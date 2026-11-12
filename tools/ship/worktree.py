"""Slice worktrees: create or adopt, save leftovers and reset, remove only when safe."""

from __future__ import annotations

from pathlib import Path

from ship.gitx import GitError, git, registered, remote_sha
from ship.proc import stop_processes_under
from ship.settings import Settings


def fetch_branch(repo: Path, remote: str, branch: str, settings: Settings) -> str | None:
    """The remote sha of `branch`, fetched so the object is local; None if the branch is not pushed."""
    sha = remote_sha(repo, remote, branch, settings.git_timeout_s)
    if sha:
        git(repo, "fetch", "-q", remote, f"+refs/heads/{branch}:refs/remotes/{remote}/{branch}",
            timeout=settings.git_timeout_s)
    return sha


def ensure_worktree(repo: Path, wt: Path, branch: str, start: str, settings: Settings) -> None:
    """A worktree at `wt` on `branch`. An existing one is adopted; a missing one is added at `start`."""
    if registered(repo, wt, settings.git_timeout_s):
        return
    wt.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "prune", timeout=settings.git_timeout_s)
    has_branch = bool(git(repo, "branch", "--list", branch, timeout=settings.git_timeout_s).strip())
    if has_branch:
        git(repo, "worktree", "add", "-q", str(wt), branch, timeout=settings.git_timeout_s)
    else:
        git(repo, "worktree", "add", "-q", "-b", branch, str(wt), start, timeout=settings.git_timeout_s)


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


def note_leftover(leftovers: Path, text: str) -> None:
    """One line in leftovers.md for something a script left in place on purpose."""
    from ship.state import now_iso

    with open(leftovers, "a", encoding="utf-8", newline="\n") as out:
        out.write(f"- {now_iso()} {text}\n")
