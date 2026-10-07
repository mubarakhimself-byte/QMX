"""Per-app durable files and a host-held lease for the single writer process."""

from __future__ import annotations

import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from typing import BinaryIO

from qmx_apps.errors import AppError
from qmx_apps.manifest import RESERVED


class Volume:
    def __init__(self, home: Path, app_id: str) -> None:
        if (
            app_id in RESERVED
            or not app_id
            or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in app_id)
        ):
            raise AppError("invalid_id", "Use a safe app id.")
        base = home.resolve() / "apps"
        candidate = base / app_id
        if (
            base.is_symlink()
            or base.is_junction()
            or candidate.is_symlink()
            or candidate.is_junction()
        ):
            raise AppError("invalid_volume", "Volumes cannot be symlinks or junctions.")
        self.root = candidate.resolve()
        if not self.root.is_relative_to((home.resolve() / "apps").resolve()):
            raise AppError("invalid_volume", "Volume escapes the app root.")

    def check_write(self, path: str | Path) -> Path:
        candidate = (self.root / path).resolve()
        if not candidate.is_relative_to(self.root):
            raise AppError("write_denied", "App writes must stay inside its volume.")
        return candidate

    def create(self, *, agents: bool) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for name in ("data", "blobs", "logs", "data/tmp"):
            self.check_write(name).mkdir(parents=True, exist_ok=True)
        for name in ("app.db", *(("memory.db",) if agents else ())):
            with closing(sqlite3.connect(self.check_write(name))) as db:
                db.execute("PRAGMA journal_mode=WAL")


class VolumeLease:
    def __init__(self, home: Path, app_id: str) -> None:
        directory = home.resolve() / "locks"
        directory.mkdir(parents=True, exist_ok=True)
        self.file: BinaryIO = (directory / f"{app_id}.lock").open("a+b")
        self.file.seek(0, os.SEEK_END)
        if self.file.tell() == 0:
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt  # noqa: PLC0415

                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl  # noqa: PLC0415

                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self.file.close()
            raise AppError("volume_busy", "Another instance owns this app volume.", 409) from error

    def close(self) -> None:
        self.file.close()
