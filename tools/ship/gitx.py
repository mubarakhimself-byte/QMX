"""Run git and gh with no prompt, no editor, a time limit, long paths and English output."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

NO_PROMPT_ENV = {
    "GIT_TERMINAL_PROMPT": "0",
    "GCM_INTERACTIVE": "never",
    "GIT_EDITOR": "true",
    "GIT_SEQUENCE_EDITOR": "true",
    "GIT_MERGE_AUTOEDIT": "no",
    "LC_ALL": "C",
    "LANG": "C",
}


class GitError(Exception):
    pass


def env_no_prompt(base: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base is None else base)
    env.update(NO_PROMPT_ENV)
    return env


def run(argv: list[str], cwd: Path, timeout: float, input: str | None = None, check: bool = True,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        done = subprocess.run(
            argv, cwd=cwd, input=input, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, env=env or env_no_prompt(),
            stdin=None if input is not None else subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"timed out after {timeout}s: {' '.join(argv)}") from exc
    except OSError as exc:
        raise GitError(f"could not start {argv[0]}: {exc}") from exc
    if check and done.returncode != 0:
        raise GitError(f"{' '.join(argv)} exited {done.returncode}: {done.stderr.strip() or done.stdout.strip()}")
    return done


def git(cwd: Path, *args: str, timeout: float, input: str | None = None, check: bool = True) -> str:
    argv = ["git", "-c", "core.longpaths=true", "-c", "core.quotepath=false", *args]
    return run(argv, cwd, timeout, input=input, check=check).stdout


def git_rc(cwd: Path, *args: str, timeout: float) -> int:
    argv = ["git", "-c", "core.longpaths=true", "-c", "core.quotepath=false", *args]
    return run(argv, cwd, timeout, check=False).returncode


def remote_sha(repo: Path, remote: str, branch: str, timeout: float) -> str | None:
    out = git(repo, "ls-remote", remote, f"refs/heads/{branch}", timeout=timeout)
    for line in out.splitlines():
        sha, _, ref = line.partition("\t")
        if ref.strip() == f"refs/heads/{branch}":
            return sha.strip()
    return None


def changed_files(repo: Path, base: str, head: str, timeout: float) -> list[str]:
    out = git(repo, "diff", "--no-renames", "--name-only", base, head, timeout=timeout)
    return [line for line in out.splitlines() if line.strip()]


def is_ancestor(repo: Path, older: str, newer: str, timeout: float) -> bool:
    return git_rc(repo, "merge-base", "--is-ancestor", older, newer, timeout=timeout) == 0


def patch_id(repo: Path, base: str, head: str, timeout: float) -> str:
    diff = git(repo, "diff", "--no-renames", "--binary", base, head, timeout=timeout)
    if not diff.strip():
        return ""
    out = git(repo, "patch-id", "--stable", input=diff, timeout=timeout)
    return out.split()[0] if out.split() else ""


def worktrees(repo: Path, timeout: float) -> dict[str, str]:
    """Registered worktree path (resolved, case-folded) to its branch ref or 'detached'."""
    out = git(repo, "worktree", "list", "--porcelain", timeout=timeout)
    found: dict[str, str] = {}
    path = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = str(Path(line[9:]).resolve()).casefold()
            found[path] = "detached"
        elif line.startswith("branch ") and path:
            found[path] = line[7:]
    return found


def registered(repo: Path, wt: Path, timeout: float) -> bool:
    return str(wt.resolve()).casefold() in worktrees(repo, timeout)
