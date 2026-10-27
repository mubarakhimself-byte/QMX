"""File helpers every part of QMX that copies his data shares: paths past Windows' 260
characters, a copy that hashes what it writes, and an OS lock one process holds at a time.

The bring-in, the first-start card and the backup all use these, so a long path, a copy cut short
and a busy lock behave the same everywhere. Standard library only.
"""

from __future__ import annotations

import hashlib
import os
from contextlib import suppress
from pathlib import Path
from typing import IO, Final, cast

CHUNK: Final = 1 << 20
PARTIAL: Final = ".qmx-copying"
"""Added to a copy's name while it is written; a copy cut short keeps it, so only names ending in
it are ever cleared."""


class Busy(Exception):
    """An OS lock is held by another process or handle. The message is the one line to show."""


def long_path(path: Path) -> Path:
    """`path` as Windows opens it past 260 characters: absolute, with `\\\\?\\` before it (and
    `\\\\?\\UNC\\` before a network path). Unchanged on other systems."""
    if os.name != "nt" or str(path).startswith("\\\\?\\"):
        return path
    full = os.path.abspath(path)
    if full.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + full[2:])
    return Path("\\\\?\\" + full)


def plain(name: object) -> str:
    """A path as he reads it: without the prefix `long_path` adds."""
    text = os.fsdecode(name) if isinstance(name, str | bytes) else str(name)
    if text.startswith("\\\\?\\UNC\\"):
        return "\\\\" + text.removeprefix("\\\\?\\UNC\\")
    return text.removeprefix("\\\\?\\")


def open_shared(path: Path) -> IO[bytes]:
    """`path` opened for reading the way a live folder must be read: on Windows with delete
    sharing, so a writer that replaces the file while it is read (the Library, the price store,
    the settings) is never refused because of the reader. Elsewhere a plain open."""
    path = long_path(path)
    if os.name != "nt":
        return path.open("rb")
    import ctypes  # noqa: PLC0415
    import msvcrt  # noqa: PLC0415
    from ctypes import wintypes  # noqa: PLC0415

    create = ctypes.WinDLL("kernel32", use_last_error=True).CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    generic_read, share_all, open_existing, normal = 0x80000000, 0x7, 3, 0x80
    handle = create(str(path), generic_read, share_all, None, open_existing, normal, None)
    if handle in (None, wintypes.HANDLE(-1).value):
        error = ctypes.get_last_error()
        raise OSError(None, ctypes.FormatError(error).strip(), str(path), error)
    descriptor = msvcrt.open_osfhandle(cast("int", handle), os.O_RDONLY | os.O_BINARY)
    return os.fdopen(descriptor, "rb")


def copy_file(source: Path, target: Path, *, length: int | None = None) -> str:
    """Copy `source` to the new file `target` byte for byte, keeping its times, and return the
    sha256 of what was written. `target` must not exist, so a copy never lands on a file already
    there. `length` copies only the first that many bytes (a log up to its last full line)."""
    target = long_path(target)
    digest = hashlib.sha256()
    left = length
    with open_shared(source) as reading, target.open("xb") as writing:
        while left is None or left > 0:
            chunk = reading.read(CHUNK if left is None else min(CHUNK, left))
            if not chunk:
                break
            digest.update(chunk)
            writing.write(chunk)
            if left is not None:
                left -= len(chunk)
        writing.flush()
        os.fsync(writing.fileno())
        found = os.fstat(reading.fileno())
    os.utime(target, ns=(found.st_atime_ns, found.st_mtime_ns))
    return digest.hexdigest()


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open_shared(path) as reading:
        while chunk := reading.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


class Held:
    """An OS lock on a file, held until `release` or the end of a `with` block, from any thread.
    The OS lets go when the process ends, so a stopped process never leaves it held."""

    def __init__(self, path: Path, handle: IO[bytes], *, removed: bool, made: bool) -> None:
        self._path = path
        self._handle: IO[bytes] | None = handle
        self._removed = removed
        self._made = made

    def __enter__(self) -> Held:
        return self

    def __exit__(self, *_: object) -> None:
        self.release()

    def release(self) -> None:
        """Let go, once; a second call does nothing."""
        handle, self._handle = self._handle, None
        if handle is None:
            return
        if self._removed and os.name != "nt":
            self._path.unlink(missing_ok=True)
        handle.close()
        if self._removed and os.name == "nt":
            with suppress(OSError):
                self._path.unlink(missing_ok=True)
        if self._removed and self._made:
            with suppress(OSError):
                self._path.parent.rmdir()


def hold(path: Path, busy: str, *, removed: bool = False) -> Held:
    """Take an OS lock on `path`; raises `Busy` with `busy` while another process or handle
    holds it. `removed` takes the file (and its folder, when this made it) away on release, so
    nothing but the pointer stays beside the pointer (ruling 143). A holder checks that its file
    is still the one at `path`, because a file removed under a waiting process is not a lock."""
    made = not path.parent.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    return Held(path, _locked(path, busy), removed=removed, made=made)


def _locked(path: Path, busy: str) -> IO[bytes]:
    while True:
        handle = path.open("a+b")
        try:
            _lock(handle)
        except OSError:
            handle.close()
            raise Busy(busy) from None
        try:
            same = os.path.samestat(os.fstat(handle.fileno()), os.stat(path))
        except OSError:
            same = False
        if same:
            return handle
        handle.close()


def _lock(handle: IO[bytes]) -> None:
    if os.name == "nt":
        import msvcrt  # noqa: PLC0415

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl  # noqa: PLC0415

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
