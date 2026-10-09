"""Code runs use an isolated checkout and one explicit push refspec."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from qmx_remote.models import CodeSource, RemoteError


def git(root: Path, *args: str) -> str:
    executable = shutil.which("git")
    if executable is None:
        raise RemoteError("Install Git on the remote worker.")
    result = subprocess.run(
        [executable, "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    if result.returncode:
        raise RemoteError("Run Git operation failed; check repository access on the target.")
    return result.stdout.strip()


def checkout(root: Path, source: CodeSource, run_id: str) -> Path:
    if (root / ".git").is_dir():
        if (
            git(root, "remote", "get-url", "origin") != source.repository
            or git(root, "branch", "--show-current") != "runs/" + run_id
        ):
            raise RemoteError("Existing code checkout belongs to a different run.")
        git(root, "merge-base", "--is-ancestor", source.revision, "HEAD")
        return root
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise RemoteError("Code checkout directory must be empty for a new run.")
    git(root, "clone", "--no-checkout", "--", source.repository, ".")
    git(root, "switch", "--detach", source.revision)
    git(root, "switch", "--create", "runs/" + run_id)
    return root


def publish(root: Path, run_id: str) -> None:
    branch = "runs/" + run_id
    if git(root, "branch", "--show-current") != branch:
        raise RemoteError("Code run changed branches; refusing to publish.")
    if git(root, "status", "--porcelain"):
        git(root, "add", "--all")
        git(
            root,
            "-c",
            "user.name=QMX Remote",
            "-c",
            "user.email=remote@qmx.local",
            "commit",
            "-m",
            "Remote run " + run_id,
        )
    git(root, "push", "origin", "HEAD:refs/heads/" + branch)
