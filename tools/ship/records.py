"""The plans worktree and the shared records: one branch, `plans`, checked out beside the code.

`init` makes the worktree (from the remote's `plans` when it has one, else as a new orphan branch) and
seeds `_records/`: BACKLOG.tsv, CLAIMS.tsv, REMOVED.md and PREFIXES.md (formats in FACTORY-DESIGN
11.5). Run twice, the second run changes nothing. Every records write is one commit on `plans` made
under `records.lock`; `commit` pushes it, and a push that cannot reach the remote leaves the commit
local for the next one to carry. Nothing here touches the main checkout's working tree or index.
"""

from __future__ import annotations

import contextlib
import os
import time
from pathlib import Path
from typing import Iterator

from ship.gitx import GitError, git, git_rc, remote_sha, worktrees
from ship.layout import Records, records_of
from ship.proc import pid_alive
from ship.settings import Settings

BRANCH = "plans"
BACKLOG_HEADER = "\t".join(("id", "source", "what", "where", "first_seen", "program", "touches", "door", "status",
                            "hops")) + "\n"
CLAIMS_HEADER = "\t".join(("program", "kind", "pattern", "since", "released")) + "\n"
GITIGNORE = "".join(f"{p}\n" for p in ("*/checks/", "*/runs/", "*/tmp/", "*/heartbeat/", "*/workers/*/stdout.log",
                                       "*.lock", "*.tmp"))
README = """\
# plans

Program folders (one per piece of work, from his words to merged code) and the shared records in `_records/`.
This branch never merges into the code; the ship kit writes it, one commit per records change.
"""
REMOVED = """\
# Removed, and why

Project-wide and append-only. Every deliberate deletion or change a planning or audit program agreed, with its reason and who decided. Later programs read this before they add anything: a removed thing is not rebuilt without his yes.

<!-- Rows: - **R-<program>-<n>** <what>. Why: <reason>. Replaced by: <path or "nothing, because ...">. In plain words: <one line he can read>. Decided by: him (<source>) | fable (<AUDIT.md or decision file>) | agent. Status: planned (<program>, <date>) | removed <sha> -->
"""
PREFIXES = """\
# Slice prefixes in use

Every program's slice ids start with its own prefix, because worktrees are named `slice-<id>` and branches `slice/<id>`. A planner registers a prefix here only after `git ls-remote --heads origin "slice/<prefix>-*"` and `grep -l "^| <prefix>-" {plans}/*/SLICES.md` both print nothing (`ship records prefix <prefix>` runs both).

- rc: risk build (rc-01 to rc-69), 2026-11
"""


class RecordsError(Exception):
    pass


def seed_files(plans: Path) -> dict[Path, str]:
    records = records_of(plans)
    return {
        plans / "README.md": README,
        plans / ".gitignore": GITIGNORE,
        records.backlog: BACKLOG_HEADER,
        records.claims: CLAIMS_HEADER,
        records.removed: REMOVED,
        records.prefixes: PREFIXES.replace("{plans}", plans.resolve().as_posix()),
    }


def _on_plans(repo: Path, plans: Path, t: float) -> bool | None:
    """True when `plans` is a worktree on branch plans, False when it is one on another branch, None when
    it is not a registered worktree."""
    ref = worktrees(repo, t).get(str(plans.resolve()).casefold())
    if ref is None:
        return None
    return ref == f"refs/heads/{BRANCH}"


def init(repo: Path, plans: Path, remote: str, settings: Settings) -> list[str]:
    t = settings.git_timeout_s
    lines: list[str] = []
    where = _on_plans(repo, plans, t)
    if where is False:
        raise RecordsError(f"{plans} is a worktree on another branch, not {BRANCH}")
    if where is None:
        git(repo, "worktree", "prune", timeout=t)
        if plans.exists() and any(plans.iterdir()):
            raise RecordsError(f"{plans} exists, is not empty and is not the {BRANCH} worktree; move it away first")
        plans.parent.mkdir(parents=True, exist_ok=True)
        has_local = git_rc(repo, "rev-parse", "--verify", "-q", f"refs/heads/{BRANCH}", timeout=t) == 0
        on_remote = remote_sha(repo, remote, BRANCH, t)
        if on_remote:
            git(repo, "fetch", "-q", remote, f"+refs/heads/{BRANCH}:refs/remotes/{remote}/{BRANCH}", timeout=t)
        if has_local:
            git(repo, "worktree", "add", "-q", str(plans), BRANCH, timeout=t)
            lines.append(f"WORKTREE {plans} on the local {BRANCH} branch")
        elif on_remote:
            git(repo, "worktree", "add", "-q", "--track", "-b", BRANCH, str(plans), f"{remote}/{BRANCH}", timeout=t)
            lines.append(f"WORKTREE {plans} on {remote}/{BRANCH} {on_remote[:8]}")
        else:
            git(repo, "worktree", "add", "-q", "--orphan", "-b", BRANCH, str(plans), timeout=t)
            lines.append(f"WORKTREE {plans} on a new orphan branch {BRANCH}")
    else:
        lines.append(f"WORKTREE {plans} already on {BRANCH}")
    written = []
    for path, text in seed_files(plans).items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, "utf-8", newline="\n")
            written.append(path.relative_to(plans).as_posix())
    if not written:
        lines.append("UNCHANGED every seed file is there")
        return lines
    lines.append(f"SEEDED {', '.join(written)}")
    sha = commit(plans, "records: seed the plans branch", settings, remote=remote, lines=lines)
    if sha:
        lines.append(f"COMMIT {sha[:8]}")
    return lines


def _age_s(path: Path) -> float:
    try:
        return time.time() - path.stat().st_mtime
    except OSError:
        return 1e9


@contextlib.contextmanager
def locked(records: Records) -> Iterator[Records]:
    """Hold `records.lock`. The same create-exclusive, take-over-if-dead pattern as `state.locked`."""
    records.dir.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            fd = os.open(records.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                owner = int(records.lock.read_text("utf-8").strip() or 0)
            except (OSError, ValueError):
                owner = 0
            if owner == os.getpid():
                raise RecordsError("records.lock taken twice by one process") from None
            young = _age_s(records.lock) < 10  # the creator may not have written its pid yet
            if (owner and pid_alive(owner)) or (not owner and young):
                time.sleep(0.2)
                continue
            records.lock.unlink(missing_ok=True)
    try:
        yield records
    finally:
        records.lock.unlink(missing_ok=True)


def commit(plans: Path, message: str, settings: Settings, push: bool = True, remote: str | None = None,
           lines: list[str] | None = None) -> str | None:
    """Commit everything changed in the plans worktree and push `plans`. Returns the new sha, or None
    when nothing was staged. A failed push leaves the commit local and adds an UNREACHABLE (or REFUSED)
    line to `lines`; the next commit's push carries both."""
    t = settings.git_timeout_s
    remote = remote or settings.remote
    git(plans, "add", "-A", timeout=t)
    if git_rc(plans, "diff", "--cached", "--quiet", timeout=t) == 0:
        return None
    git(plans, "commit", "-q", "-m", message, timeout=t)
    sha = git(plans, "rev-parse", "HEAD", timeout=t).strip()
    if push:
        try:
            git(plans, "push", "-q", remote, f"refs/heads/{BRANCH}:refs/heads/{BRANCH}", timeout=t)
        except GitError as exc:
            try:
                remote_sha(plans, remote, BRANCH, settings.net_timeout_s)
                word = "REFUSED"
            except GitError:
                word = "UNREACHABLE"
            if lines is not None:
                lines.append(f"{word} push of {BRANCH} {sha[:8]} left local: {exc}")
    return sha


def prefix_clashes(plans: Path, repo: Path, remote: str, prefix: str, settings: Settings) -> list[str]:
    """Every use of `prefix` already made: SLICES.md rows under the plans worktree whose id starts
    `<prefix>-`, and remote slice branches `slice/<prefix>-*`."""
    found = []
    for path in sorted(plans.glob("*/SLICES.md")):
        for row in path.read_text("utf-8", errors="replace").splitlines():
            row = row.strip()
            if not row.startswith("|"):
                continue
            first = row.strip("|").split("|")[0].strip()
            if first.startswith(f"{prefix}-"):
                found.append(f"{path.relative_to(plans).as_posix()}: {first}")
    pattern = f"{settings.slice_branch_prefix}{prefix}-*"
    out = git(repo, "ls-remote", "--heads", remote, pattern, timeout=settings.git_timeout_s)
    for line in out.splitlines():
        _, _, ref = line.partition("\t")
        if ref.strip():
            found.append(f"{remote} {ref.strip().removeprefix('refs/heads/')}")
    return found
