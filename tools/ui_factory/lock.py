"""Exclusive file lock for shared factory state (Windows and POSIX)."""

from __future__ import annotations

import os
from pathlib import Path
from types import TracebackType
from typing import IO

if os.name == "nt":
    import msvcrt as _winlock

    _posixlock = None
else:
    import fcntl as _posixlock

    _winlock = None


class FileLock:
    """Exclusive lock around one metadata file.

    Used for state.json, port leases, and shared lockfile serialization.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._fh: IO[str] | None = None

    def __enter__(self) -> FileLock:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self._path.open("a+", encoding="utf-8")
        self._fh.seek(0, os.SEEK_END)
        if self._fh.tell() == 0:
            self._fh.write("0")
            self._fh.flush()
        self._fh.seek(0)
        if _winlock is not None:
            _winlock.locking(self._fh.fileno(), _winlock.LK_LOCK, 1)
        elif _posixlock is not None:
            _posixlock.flock(self._fh.fileno(), _posixlock.LOCK_EX)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._fh is None:
            return
        try:
            if _winlock is not None:
                self._fh.seek(0)
                _winlock.locking(self._fh.fileno(), _winlock.LK_UNLCK, 1)
            elif _posixlock is not None:
                _posixlock.flock(self._fh.fileno(), _posixlock.LOCK_UN)
        finally:
            self._fh.close()
            self._fh = None
