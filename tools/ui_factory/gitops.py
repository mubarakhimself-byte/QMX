"""Git helpers used by quality, merge, resume, and validation."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path


def git(
    cwd: Path, args: list[str], *, check: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def changed_files(worktree: Path, against: str) -> list[str]:
    names: set[str] = set()
    for extra in (
        ["diff", "--name-only", "--relative", against],
        ["diff", "--name-only", "--relative", "--cached"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        proc = git(worktree, extra)
        if proc.returncode != 0:
            continue
        for line in proc.stdout.splitlines():
            path = line.strip().replace("\\", "/")
            if path:
                names.add(path)
    return sorted(names)


def content_fingerprint(worktree: Path) -> str:
    digest = hashlib.sha256()
    diff = git(worktree, ["diff", "HEAD"])
    digest.update((diff.stdout or "").encode("utf-8"))
    untracked = git(worktree, ["ls-files", "--others", "--exclude-standard"])
    for rel in untracked.stdout.splitlines():
        path = worktree / rel.strip()
        digest.update(rel.encode("utf-8"))
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def observed_toolchain() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for name in ("node", "pnpm", "python"):
        exe = shutil.which(name)
        if exe is None:
            pairs.append((name, "missing"))
            continue
        proc = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        text = (proc.stdout or proc.stderr or "").strip().splitlines()
        pairs.append((name, text[0] if text else "missing"))
    return pairs


def destination_checkout(repo: Path, dest: str) -> Path | None:
    proc = git(repo, ["worktree", "list", "--porcelain"])
    current: dict[str, str] = {}
    rows: list[dict[str, str]] = []
    for line in (proc.stdout or "").splitlines():
        if line == "":
            if current:
                rows.append(current)
            current = {}
            continue
        if line.startswith("worktree "):
            current["path"] = line[len("worktree ") :]
        elif line.startswith("branch "):
            current["branch"] = line[len("branch ") :]
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD ") :]
    if current:
        rows.append(current)
    want = f"refs/heads/{dest}"
    for row in rows:
        if row.get("branch") == want:
            path = row.get("path")
            if path:
                return Path(path)
    return None


def completed_ids_from_git(worktree: Path) -> set[str]:
    proc = git(worktree, ["log", "--format=%s", "-n", "400"])
    found: set[str] = set()
    for line in proc.stdout.splitlines():
        for token in line.replace(",", " ").split():
            if token.startswith("FEAT-") or (
                token.startswith("story") is False
                and "." in token
                and token[0].isdigit()
            ):
                found.add(token.rstrip(":"))
            if token.startswith("story") and len(token) > 5:
                found.add(token)
    return found
