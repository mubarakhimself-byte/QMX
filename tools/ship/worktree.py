"""Slice worktrees: create or adopt, save leftovers and reset, remove only when safe.

A worktree or checkout a worker will run in gets its environment first: `ensure_worktree` and
`checkout_copy` take a `Setup` (the checks.toml `setup` of the packages the worker touches, normally
`uv sync --frozen`) and run each through the time-limited wrapper before they return, so no worker starts
in a folder whose packages are not installed. A setup that fails is recorded (`Setup.lines`, its log), never
retried here; the slice's own checks judge it again.
"""

from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path

from ship.gitx import GitError, git, git_rc, registered, remote_sha
from ship.proc import stop_processes_under
from ship.settings import Settings
from ship.wrapper import run_timed


@dataclasses.dataclass
class Setup:
    """The `setup` commands of the packages a worker touches, and where their logs go."""

    packages: tuple  # suite.Package: anything with `root`, `setup` and `label`
    runs: Path  # the wrapper's per-run temp root (the program's runs/)
    logs: Path  # setup-<label>.log are written here
    heartbeat: Path | None = None
    lines: list[str] = dataclasses.field(default_factory=list)  # PASS / FAIL / NOTRUN setup-<label> ...

    @property
    def failed(self) -> list[str]:
        return [x for x in self.lines if x.startswith("FAIL ")]


def prepare(path: Path, setup: Setup | None, settings: Settings) -> list[str]:
    """Run every package's `setup` in `path`, from the package's root, through the timed wrapper."""
    if setup is None:
        return []
    for package in setup.packages:
        if not package.setup:
            continue
        name = f"setup-{package.label}"
        if not (path / package.root).is_dir():
            setup.lines.append(f"NOTRUN {name} no folder {package.root} at this commit")
            continue
        log = setup.logs / f"{name}.log"
        done = run_timed(list(package.setup), path / package.root, log, settings.check_timeout_s, settings, setup.runs,
                         setup.heartbeat)
        setup.lines.append(f"{'PASS' if done.rc == 0 else 'FAIL'} {name} rc={done.rc} {log}")
    return setup.lines


def fetch_branch(repo: Path, remote: str, branch: str, settings: Settings) -> str | None:
    """The remote sha of `branch`, fetched so the object is local; None if the branch is not pushed."""
    sha = remote_sha(repo, remote, branch, settings.git_timeout_s)
    if sha:
        git(repo, "fetch", "-q", remote, f"+refs/heads/{branch}:refs/remotes/{remote}/{branch}",
            timeout=settings.git_timeout_s)
    return sha


def ensure_worktree(repo: Path, wt: Path, branch: str, start: str, settings: Settings,
                    setup: Setup | None = None) -> None:
    """A worktree at `wt` on `branch`. An existing one is adopted; a missing one is added at `start`. Then
    `setup` runs in it (`prepare`)."""
    if not registered(repo, wt, settings.git_timeout_s):
        wt.parent.mkdir(parents=True, exist_ok=True)
        git(repo, "worktree", "prune", timeout=settings.git_timeout_s)
        has_branch = bool(git(repo, "branch", "--list", branch, timeout=settings.git_timeout_s).strip())
        if has_branch:
            git(repo, "worktree", "add", "-q", str(wt), branch, timeout=settings.git_timeout_s)
        else:
            git(repo, "worktree", "add", "-q", "-b", branch, str(wt), start, timeout=settings.git_timeout_s)
    prepare(wt, setup, settings)


def save_and_reset(wt: Path, reset_to: str, patch: Path, settings: Settings) -> Path | None:
    """Save everything not at `reset_to` (unpushed commits, staged, unstaged, untracked) as one binary
    patch, then reset the worktree to `reset_to`. Returns the patch path, or None when nothing was there.
    Run twice, the second run finds nothing and writes nothing."""
    t = settings.git_timeout_s
    git(wt, "add", "-A", timeout=t)
    diff = git(wt, "diff", "--cached", "--binary", reset_to, timeout=t)
    saved = None
    if diff.strip():
        patch.parent.mkdir(parents=True, exist_ok=True)
        target = patch
        n = 1
        while target.exists():
            target = patch.with_name(f"{patch.stem}-{n}{patch.suffix}")
            n += 1
        target.write_text(diff, "utf-8", newline="\n")
        saved = target
    git(wt, "reset", "-q", "--hard", reset_to, timeout=t)
    git(wt, "clean", "-q", "-fd", timeout=t)
    return saved


def remove_worktree(repo: Path, wt: Path, branch: str, remote: str, settings: Settings) -> str | None:
    """Remove a worktree only when its branch head equals the remote and nothing is uncommitted.
    Never --force. Returns None on success, else why it was left."""
    t = settings.git_timeout_s
    if not registered(repo, wt, t):
        return None
    local = git(wt, "rev-parse", "HEAD", timeout=t).strip()
    pushed = remote_sha(repo, remote, branch, t)
    if local != pushed:
        return f"{wt}: local head {local[:8]} is not the remote {str(pushed)[:8]}; left in place"
    if git(wt, "status", "--porcelain", timeout=t).strip():
        return f"{wt}: uncommitted changes; left in place"
    stop_processes_under(wt)
    try:
        git(repo, "worktree", "remove", str(wt), timeout=t)
    except GitError as exc:
        return f"{wt}: git worktree remove failed: {exc}"
    return None


def checkout_copy(repo: Path, path: Path, sha: str, settings: Settings, setup: Setup | None = None) -> Path:
    """A detached check copy at `sha`, reused between runs so a package setup (a venv) survives. Then
    `setup` runs in it (`prepare`)."""
    t = settings.git_timeout_s
    if registered(repo, path, t):
        git(path, "reset", "-q", "--hard", timeout=t)
        git(path, "clean", "-q", "-fd", timeout=t)
        git(path, "checkout", "-q", "--detach", sha, timeout=t)
    else:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        git(repo, "worktree", "prune", timeout=t)
        git(repo, "worktree", "add", "-q", "--detach", str(path), sha, timeout=t)
    prepare(path, setup, settings)
    return path


def drop_copy(repo: Path, path: Path, settings: Settings) -> None:
    """Remove a detached check copy. It sits at a pushed sha and holds no work of its own, so when
    test leftovers make `git worktree remove` refuse, the folder is deleted and the entry pruned."""
    t = settings.git_timeout_s
    if registered(repo, path, t):
        stop_processes_under(path)
        if git_rc(repo, "worktree", "remove", str(path), timeout=t) == 0:
            return
    shutil.rmtree(path, ignore_errors=True)
    git(repo, "worktree", "prune", timeout=t)


def note_leftover(leftovers: Path, text: str) -> None:
    """One line in leftovers.md for something a script left in place on purpose."""
    from ship.state import now_iso

    with open(leftovers, "a", encoding="utf-8", newline="\n") as out:
        out.write(f"- {now_iso()} {text}\n")
