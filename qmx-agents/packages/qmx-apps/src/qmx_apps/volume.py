"""Per-app durable files and a host-held lease for the single writer process.

The lease is two things at once. Locally it is a byte lock on `locks/<app>.lock`, which makes one
process the writer on one machine. Across machines it is the `Lease` record written after that
byte, which numbers every handover: a machine that lost the lease by one generation is refused
instead of taking the volume back (AD-64, probe P-APP).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, cast

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import RESERVED

LOCK_BYTE = 1
"""The lock holds the first byte; the lease record starts after it."""


@dataclass(frozen=True, slots=True)
class Lease:
    """Which machine may write one app's volume, and which generation of the handover it holds.
    `released` says whether the holder let go: a handover leaves the next generation free for the
    machine it names, so the machine can take the volume without a second round trip."""

    app_id: str
    generation: int
    holder: str
    released: bool
    at: str

    @classmethod
    def parse(cls, value: Lease | Document | None) -> Lease | None:
        if value is None or isinstance(value, Lease):
            return value
        app_id, generation = value.get("app_id"), value.get("generation")
        holder = value.get("holder", "")
        at = value.get("at", "")
        if not isinstance(app_id, str) or not isinstance(generation, int):
            raise AppError("invalid_lease", "A lease names an app and a generation.", 409)
        return cls(
            app_id,
            generation,
            holder if isinstance(holder, str) else "",
            value.get("released") is True,
            at if isinstance(at, str) else "",
        )

    def document(self) -> Document:
        return {
            "app_id": self.app_id,
            "generation": self.generation,
            "holder": self.holder,
            "released": self.released,
            "at": self.at,
        }


def read_lease(home: Path, app_id: str) -> Lease:
    """The lease this machine's store holds for `app_id`, without taking the lock. A volume no
    machine has ever held reads as generation zero, released. The record is read from after the
    lock byte, because a machine holding the lock makes that byte unreadable."""
    path = home.resolve() / "locks" / f"{app_id}.lock"
    if not path.is_file():
        return Lease(app_id, 0, "", True, "")
    with path.open("rb") as file:
        file.seek(LOCK_BYTE)
        raw = file.read()
    if not raw.strip():
        return Lease(app_id, 0, "", True, "")
    return _read(raw, app_id)


def _read(raw: bytes, app_id: str) -> Lease:
    try:
        record = cast(dict[str, object], json.loads(raw))
        generation = record["generation"]
        if not isinstance(generation, int):
            raise ValueError("generation is a number")
        return Lease(
            app_id,
            generation,
            str(record.get("holder") or ""),
            record.get("released") is True,
            str(record.get("at") or ""),
        )
    except (ValueError, KeyError, TypeError) as error:
        raise AppError(
            "lease_corrupt",
            f"locks/{app_id}.lock holds no lease; delete it if no instance is running.",
            409,
        ) from error


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
                db.execute("PRAGMA busy_timeout=5000")


class VolumeLease:
    def __init__(
        self,
        home: Path,
        app_id: str,
        *,
        holder: str = "",
        expect: Lease | Document | None = None,
    ) -> None:
        """Take the volume's writer lease for `holder`. `expect` is the lease a handover named:
        taking the volume with a different generation than the store records is refused, because
        another machine has held it since. A `holder` that is not the recorded one is refused
        while the record is unreleased, which is how two machines are kept off one volume."""
        directory = home.resolve() / "locks"
        directory.mkdir(parents=True, exist_ok=True)
        self.app_id = app_id
        self.holder = holder
        self.file: BinaryIO = (directory / f"{app_id}.lock").open("a+b")
        try:
            self._lock()
            current = self._read()
            wanted = Lease.parse(expect)
            generation = max(current.generation, 1)
            if wanted is not None:
                if wanted.app_id != app_id:
                    raise AppError("lease_mismatch", f"That lease is for {wanted.app_id}.", 409)
                if current.generation > wanted.generation:
                    raise AppError(
                        "lease_stale",
                        f"{app_id} is at lease generation {current.generation}, "
                        f"past the handover at {wanted.generation}",
                        409,
                    )
                generation = wanted.generation
            if holder and current.holder:
                if not current.released and current.holder != holder:
                    raise AppError(
                        "volume_busy",
                        f"{app_id} is held by {current.holder} at generation {current.generation}.",
                        409,
                    )
                if current.released and current.holder != holder:
                    raise AppError(
                        "lease_handed_over",
                        f"{app_id} was handed to {current.holder} at generation "
                        f"{current.generation}.",
                        409,
                    )
            self._write(Lease(app_id, generation, holder, False, _now()))
        except BaseException:
            self.file.close()
            raise

    def _lock(self) -> None:
        self.file.seek(0, os.SEEK_END)
        if self.file.tell() == 0:
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt  # noqa: PLC0415

                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, LOCK_BYTE)
            else:
                import fcntl  # noqa: PLC0415

                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise AppError("volume_busy", "Another instance owns this app volume.", 409) from error

    def _read(self) -> Lease:
        self.file.seek(LOCK_BYTE)
        raw = self.file.read()
        if not raw.strip():
            return Lease(self.app_id, 0, "", True, "")
        return _read(raw, self.app_id)

    def _write(self, record: Lease) -> None:
        self.file.seek(LOCK_BYTE)
        self.file.truncate(LOCK_BYTE)
        self.file.write(json.dumps(record.document()).encode())
        self.file.flush()

    @property
    def record(self) -> Lease:
        return self._read()

    def handover(self, holder: str) -> Lease:
        """Release the lease to `holder` at the next generation, and answer the lease that
        machine takes the volume with. The old machine's next attempt is refused as stale."""
        current = self._read()
        handed = Lease(self.app_id, max(current.generation, 1) + 1, holder, True, _now())
        self._write(handed)
        return handed

    def close(self) -> None:
        self.file.close()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def checksum(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def _files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise AppError("invalid_volume", "Volume files cannot be symlinks or junctions.")
        if path.is_file() and path.name != "backup.json":
            files.append(path)
    return files


def snapshot(volume: Volume, root: Path) -> None:
    """Copy a volume's files to `root`, its databases consistently while they are written, for
    a handover and the road check's isolated proof."""
    root.mkdir(parents=True, exist_ok=True)
    for source in _files(volume.root):
        relative = source.relative_to(volume.root)
        if (
            source.name.endswith(("-wal", "-shm", "-journal", ".lock"))
            or source.name == "backup.json.tmp"
            or (relative.parent == Path("data") and source.name.startswith("heartbeat-"))
            or relative.parts[:2] == ("data", "tmp")
            or relative.parts[0] == "road"
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
