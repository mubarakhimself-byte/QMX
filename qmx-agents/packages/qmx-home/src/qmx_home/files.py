"""File helpers every part of QMX that copies his data shares: paths past Windows' 260
characters, a copy that hashes what it writes, and an OS lock one process holds at a time.

The bring-in, the first-start card and the backup all use these, so a long path, a copy cut short
and a busy lock behave the same everywhere. Standard library only.
"""

from __future__ import annotations

import functools
import hashlib
import os
import struct
from collections.abc import Callable, Mapping
from contextlib import suppress
from pathlib import Path
from typing import IO, Final, cast

CHUNK: Final = 1 << 20
THROUGH_BELOW: Final = 8 << 20
"""A new file smaller than this is written through the disk cache; a larger one is flushed once
at the end. Measured on his D: drive: 2 KB files take 0.9 ms written through against 3.4 ms
flushed, and 512 MB is written at 41 MB/s through against 82 MB/s flushed once."""
PARTIAL: Final = ".qmx-copying"
"""Added to a copy's name while it is written; a copy cut short keeps it, so only names ending in
it are ever cleared."""


GIB: Final = 1 << 30
MIN_FLOOR: Final = GIB
"""The local floor is never below this, whatever the drive's size."""
FLOOR_SHARE: Final = 20
"""With no `disk.floor_gb`, the local floor is a twentieth of the drive's free space."""


class Busy(Exception):
    """An OS lock is held by another process or handle. The message is the one line to show."""


def floor_gb(settings: Mapping[str, object]) -> float | None:
    """`disk.floor_gb` in the `[engine]` section, as read from `settings.toml` (a `disk` table)
    or as the engine's dotted keys; None when unset or not a positive number."""
    disk = settings.get("disk")
    raised = (
        cast("Mapping[str, object]", disk).get("floor_gb")
        if isinstance(disk, Mapping)
        else settings.get("disk.floor_gb")
    )
    if isinstance(raised, int | float) and not isinstance(raised, bool) and raised > 0:
        return float(raised)
    return None


def floor_of(raised: float | None, free: int) -> int:
    """The room a local write leaves on its drive: the larger of 1 GiB and `raised` GB, or a
    twentieth of `free` when `raised` is None. It protects his drive and is not a cap."""
    return max(MIN_FLOOR, int(raised * GIB) if raised is not None else free // FLOOR_SHARE)


def local_floor(settings: Mapping[str, object], free: int) -> int:
    """The one local floor for every local write (design 06 section 4), from `[engine]`'s
    `disk.floor_gb` and the drive's `free` bytes."""
    return floor_of(floor_gb(settings), free)


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
    sharing, so a writer that deletes the file while it is read (the price store freezing a
    month, the host making room) is not refused because of the reader. Windows still refuses a
    rename onto a file held open this way: the Library retries, other writers do not. Elsewhere
    a plain open."""
    path = long_path(path)
    if os.name != "nt":
        return path.open("rb")
    return _windows_file(path, _GENERIC_READ, _SHARE_ALL, _OPEN_EXISTING, _NORMAL, "rb")


def create_new(path: Path, *, through: bool = True) -> IO[bytes]:
    """The new file `path` (refused when it exists), opened so its bytes are on the disk once
    `settle` returns. With `through`, on Windows, every write goes through the disk cache, which
    costs far less than a flush for a small file; otherwise `settle` flushes it once, which
    writes a large file at the disk's full speed. Pass `settle` the same `through`."""
    path = long_path(path)
    if os.name != "nt" or not through:
        return path.open("xb")
    flags = _NORMAL | _WRITE_THROUGH
    return _windows_file(path, _GENERIC_WRITE, 0, _CREATE_NEW, flags, "wb")


def settle(writing: IO[bytes], *, through: bool = True) -> None:
    """Make what was written to a `create_new` file durable before it is closed or renamed."""
    writing.flush()
    if os.name != "nt" or not through:
        os.fsync(writing.fileno())


def write_new(path: Path, data: bytes) -> None:
    """`data` in the new file `path`, on the disk when this returns."""
    with create_new(path) as writing:
        writing.write(data)
        settle(writing)


def flush_file(path: Path) -> None:
    """Flush a file another writer made (SQLite's `VACUUM INTO`) to the disk."""
    with long_path(path).open("r+b") as writing:
        os.fsync(writing.fileno())


_GENERIC_READ: Final = 0x8000_0000
_GENERIC_WRITE: Final = 0x4000_0000
_SHARE_ALL: Final = 0x7
_CREATE_NEW: Final = 1
_OPEN_EXISTING: Final = 3
_NORMAL: Final = 0x80
_WRITE_THROUGH: Final = 0x8000_0000
_INVALID: Final = (1 << (8 * struct.calcsize("P"))) - 1
"""`INVALID_HANDLE_VALUE`, as an unsigned handle."""


def _windows_file(
    path: Path, access: int, share: int, disposition: int, flags: int, mode: str
) -> IO[bytes]:
    import msvcrt  # noqa: PLC0415

    handle = _create_file()(str(path), access, share, None, disposition, flags, None)
    if handle is None or handle == _INVALID:
        import ctypes  # noqa: PLC0415

        error = ctypes.get_last_error()
        raise OSError(None, ctypes.FormatError(error).strip(), str(path), error)
    access_mode = os.O_RDONLY if mode == "rb" else os.O_WRONLY
    try:
        descriptor = msvcrt.open_osfhandle(handle, access_mode | os.O_BINARY)
    except BaseException:
        _close_handle()(handle)
        raise
    return cast("IO[bytes]", os.fdopen(descriptor, mode))


@functools.cache
def _create_file() -> Callable[..., int | None]:
    """kernel32's `CreateFileW`, typed once."""
    import ctypes  # noqa: PLC0415
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
    return cast("Callable[..., int | None]", create)


@functools.cache
def _close_handle() -> Callable[[int], int]:
    import ctypes  # noqa: PLC0415

    return cast("Callable[[int], int]", ctypes.WinDLL("kernel32").CloseHandle)


def copy_file(source: Path, target: Path, *, length: int | None = None) -> str:
    """Copy `source` to the new file `target` byte for byte, keeping its times, and return the
    sha256 of what was written, which is on the disk when this returns. `target` must not exist,
    so a copy never lands on a file already there. `length` copies only the first that many
    bytes (a log up to its last full line)."""
    digest = hashlib.sha256()
    left = length
    with open_shared(source) as reading:
        found = os.fstat(reading.fileno())
        through = (found.st_size if length is None else length) < THROUGH_BELOW
        with create_new(target, through=through) as writing:
            while left is None or left > 0:
                chunk = reading.read(CHUNK if left is None else min(CHUNK, left))
                if not chunk:
                    break
                digest.update(chunk)
                writing.write(chunk)
                if left is not None:
                    left -= len(chunk)
            settle(writing, through=through)
    os.utime(long_path(target), ns=(found.st_atime_ns, found.st_mtime_ns))
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
