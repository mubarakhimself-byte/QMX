"""Online snapshots, destination restore tests, and stopped-volume replacement."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import uuid
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import StrictModel
from qmx_apps.volume import Volume, VolumeLease


class BackupSettings(StrictModel):
    remote: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    bucket: str = Field(min_length=1)
    node: str = Field(default="laptop", pattern=r"^[a-zA-Z0-9_-]+$")
    interval_seconds: int = Field(default=86400, gt=0)
    enabled: bool = True

    def destination(self, app_id: str, snapshot_id: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", snapshot_id):
            raise AppError("invalid_snapshot", "Use the snapshot id from backup.json.")
        bucket = self.bucket.replace("\\", "/").rstrip("/")
        if not bucket or any(part in {"", ".", ".."} for part in bucket.lstrip("/").split("/")):
            raise AppError("invalid_backup_settings", "Bucket must be a safe remote path.")
        return f"{self.remote}:{bucket}/{self.node}/{app_id}/{snapshot_id}"


def _rclone(operation: str, source: str | Path, target: str | Path) -> None:
    binary = shutil.which("rclone")
    if binary is None:
        raise AppError(
            "rclone_missing", "Install rclone and configure the backup remote in Settings.", 503
        )
    result = subprocess.run(
        [binary, operation, str(source), str(target), "--checksum"],
        capture_output=True,
        check=False,
        timeout=3600,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    if result.returncode:
        # Provider diagnostics can include credentials; leave them out of API responses.
        raise AppError(
            "backup_transfer_failed", "rclone failed; check the configured remote and access.", 503
        )


def checksum(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def _files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise AppError("invalid_backup", "Backup files cannot be symlinks or junctions.")
        if path.is_file() and path.name != "backup.json":
            files.append(path)
    return files


def _verify(root: Path, *, app_id: str, snapshot_id: str) -> Document:
    try:
        manifest = json.loads((root / "backup.json").read_text(encoding="utf-8"))
        if manifest["app_id"] != app_id or manifest["snapshot_id"] != snapshot_id:
            raise ValueError("Snapshot identity differs.")
        actual = {path.relative_to(root).as_posix(): checksum(path) for path in _files(root)}
        if actual != manifest["checksums"] or "app.db" not in actual:
            raise ValueError("Snapshot checksums differ.")
        for path in root.rglob("*.db"):
            with closing(sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)) as db:
                if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise ValueError("SQLite integrity check failed.")
        return manifest
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        raise AppError(
            "invalid_backup", "Snapshot identity, checksums or SQLite integrity failed.", 409
        ) from error


def backup(volume: Volume, settings: BackupSettings) -> Document:
    if not volume.check_write("app.db").is_file():
        raise AppError("volume_missing", "Start the app once to create its data volume.", 409)
    snapshot_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:8]
    destination = settings.destination(volume.root.name, snapshot_id)
    # Fail before doing expensive snapshot work if the transfer tool is absent.
    if shutil.which("rclone") is None:
        raise AppError(
            "rclone_missing", "Install rclone and configure the backup remote in Settings.", 503
        )
    with tempfile.TemporaryDirectory(prefix="qmx-backup-") as temporary:
        root = Path(temporary) / "snapshot"
        root.mkdir()
        for source in _files(volume.root):
            relative = source.relative_to(volume.root)
            if (
                source.name.endswith(("-wal", "-shm", "-journal", ".lock"))
                or source.name == "backup.json.tmp"
                or relative.parts[:2]
                == (
                    "data",
                    "tmp",
                )
            ):
                continue
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix == ".db":
                with (
                    closing(sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True)) as src,
                    closing(sqlite3.connect(target)) as dst,
                ):
                    src.backup(dst, pages=256)
                    dst.execute("PRAGMA journal_mode=DELETE")
            else:
                shutil.copyfile(source, target)
        manifest: Document = {
            "app_id": volume.root.name,
            "snapshot_id": snapshot_id,
            "destination": destination,
            "checksums": {
                path.relative_to(root).as_posix(): checksum(path) for path in _files(root)
            },
            "restore_test": {"passed": False},
        }
        (root / "backup.json").write_text(json.dumps(manifest), encoding="utf-8")
        # Sync only this unique snapshot directory, never the bucket or older snapshots.
        _rclone("sync", root, destination)
        downloaded = Path(temporary) / "downloaded"
        _rclone("copy", destination, downloaded)
        _verify(downloaded, app_id=volume.root.name, snapshot_id=snapshot_id)
        manifest["restore_test"] = {"passed": True}
        (root / "backup.json").write_text(json.dumps(manifest), encoding="utf-8")
        _rclone("copy", root, destination)
        local = volume.check_write("backup.json.tmp")
        local.write_text(json.dumps(manifest), encoding="utf-8")
        local.replace(volume.check_write("backup.json"))
        return manifest


def restore(home: Path, app_id: str, settings: BackupSettings, snapshot_id: str) -> Document:
    volume = Volume(home, app_id)
    lease = VolumeLease(home, app_id)
    try:
        volume.root.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".restore-", dir=volume.root.parent) as temporary:
            stage = Path(temporary) / "volume"
            _rclone("copy", settings.destination(app_id, snapshot_id), stage)
            manifest = _verify(stage, app_id=app_id, snapshot_id=snapshot_id)
            for name in ("data", "blobs", "logs", "data/tmp"):
                (stage / name).mkdir(parents=True, exist_ok=True)
            old = Path(temporary) / "previous"
            if volume.root.exists():
                os.replace(volume.root, old)
            try:
                os.replace(stage, volume.root)
            except BaseException:
                if old.exists():
                    os.replace(old, volume.root)
                raise
            return manifest
    finally:
        lease.close()
