"""Weekly, vault-free snapshots of small stores to a private Git repository."""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

from qmx_control.models import ControlError, Document

MAX_BYTES = 95_000_000
LIBRARY = Path("library")
"""The one Library store `<home>/library/` (MIGRATION step 6)."""
LIBRARY_EVIDENCE = frozenset({"objects", "refs", "edges", "annotations", "kinds"})
"""The store's objects, its three logs, its annotations and the kind schemas. `catalog.db` and
`writer.lock` stay out because both are derived from those files, and `blobs/` is excluded like
every other blob folder, so the snapshot stays a small-store backup that rebuilds the index on
restore."""
DATABASES = {
    "memory.db",
    "runs.db",
    "experiments.db",
    "experiment.db",
    "app.db",
    "apps.db",
}


def evidence(relative: Path) -> bool:
    """Whether a home path is one of the Library store's evidence files."""
    return (
        relative.is_relative_to(LIBRARY)
        and len(relative.parts) > 2
        and relative.parts[1] in LIBRARY_EVIDENCE
    )


def _git(directory: Path, *args: str) -> str:
    executable = shutil.which("git")
    if executable is None:
        raise ControlError("git_missing", "Install git to run the backup job.")
    result = subprocess.run(
        [executable, "-C", str(directory), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if result.returncode:
        raise ControlError("backup_git_failed", "Git backup command failed.", 409)
    return result.stdout.strip()


def weekly_backup(home: Path, repository: str, *, dry_run: bool = False) -> Document:
    home = home.resolve()
    state = home / "weekly-backup.json"
    now = datetime.now(UTC)
    if not dry_run and state.exists():
        previous = json.loads(state.read_text(encoding="utf-8"))
        if now - datetime.fromisoformat(previous["completed"]) < timedelta(days=7):
            return {"status": "not_due", "completed": previous["completed"]}
    if dry_run:
        remote = Path(repository).resolve()
        if (
            not remote.is_dir()
            or not (remote / "HEAD").is_file()
            or _git(remote, "rev-parse", "--is-bare-repository") != "true"
        ):
            raise ControlError(
                "invalid_backup_repo", "Dry runs require a local bare Git repository."
            )
        destination = str(remote)
    else:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ControlError(
                "invalid_backup_repo", "Set backup.repository to owner/private-repo."
            )
        gh = shutil.which("gh")
        if gh is None:
            raise ControlError(
                "gh_missing", "Install and authenticate gh for private GitHub backups."
            )
        result = subprocess.run(
            [gh, "api", "--hostname", "github.com", f"repos/{repository}", "--jq", ".private"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode or result.stdout.strip() != "true":
            raise ControlError(
                "private_repo_required", "Backup requires a verified private GitHub repo."
            )
        destination = f"https://github.com/{repository}.git"
    lock = home / "weekly-backup.lock"
    try:
        owner = lock.open("x")
    except FileExistsError as error:
        raise ControlError("backup_busy", "Another backup owns the snapshot job.", 409) from error
    included: list[str] = []
    excluded: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="qmx-weekly-") as temporary:
            checkout = Path(temporary) / "repo"
            _git(Path(temporary), "clone", "--quiet", "--", destination, str(checkout))
            snapshot = checkout / "snapshot"
            if snapshot.exists():
                # Only clear our snapshot in this disposable checkout.
                if snapshot.resolve().parent != checkout.resolve() or snapshot.is_symlink():
                    raise ControlError(
                        "invalid_backup_repo", "Unsafe snapshot path in backup repo."
                    )
                shutil.rmtree(snapshot)
            snapshot.mkdir()
            candidates = sorted(path for path in home.rglob("*") if path.is_file())
            for path in candidates:
                relative = path.relative_to(home)
                parts = relative.parts
                definition = parts[0] in {"definitions", "agents", "workflows"}
                allowed = (
                    path.name in DATABASES
                    or relative == Path("settings.toml")
                    or evidence(relative)
                    or (definition and path.suffix.lower() in {".toml", ".json", ".yaml", ".yml"})
                )
                if (
                    not allowed
                    or path.is_symlink()
                    or not path.resolve().is_relative_to(home)
                    or any(
                        part in {"artifacts", "blobs", "data", ".venv", ".git"} for part in parts
                    )
                ):
                    excluded.append(relative.as_posix())
                    continue
                if path.stat().st_size > MAX_BYTES:
                    excluded.append(relative.as_posix())
                    if not dry_run:
                        raise ControlError(
                            "backup_too_large", f"Backup file exceeds 95 MB: {relative}."
                        )
                    continue
                target = snapshot / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == ".db":
                    uri = path.resolve().as_uri() + "?mode=ro"
                    with (
                        closing(sqlite3.connect(uri, uri=True)) as source,
                        closing(sqlite3.connect(target)) as output,
                    ):
                        source.backup(output)
                        if output.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                            raise ControlError(
                                "backup_corrupt", f"Snapshot restore failed: {relative}."
                            )
                else:
                    shutil.copyfile(path, target)
                if target.stat().st_size > MAX_BYTES:
                    raise ControlError("backup_too_large", f"Snapshot exceeds 95 MB: {relative}.")
                included.append(relative.as_posix())
            _git(checkout, "add", "--force", "--all", "--", "snapshot")
            if _git(checkout, "status", "--porcelain"):
                _git(
                    checkout,
                    "-c",
                    "user.name=QMX backup",
                    "-c",
                    "user.email=qmx-backup@localhost",
                    "-c",
                    "commit.gpgsign=false",
                    "commit",
                    "-m",
                    "Weekly small-store snapshot",
                )
                # A dry run exercises the complete job against a local bare repo only.
                _git(checkout, "push", "origin", "HEAD")
            commit = _git(checkout, "rev-parse", "HEAD")
        result_data: Document = {
            "status": "dry_run" if dry_run else "completed",
            "commit": commit,
            "included": list(included),
            "excluded": list(excluded),
            "completed": now.isoformat(),
        }
        if not dry_run:
            pending = state.with_suffix(".tmp")
            pending.write_text(json.dumps(result_data), encoding="utf-8")
            pending.replace(state)
        return result_data
    finally:
        owner.close()
        lock.unlink()
