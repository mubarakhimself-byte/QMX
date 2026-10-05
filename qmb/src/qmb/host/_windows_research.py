"""Native NTFS handle adapter; imported only on Windows by research_store.

All component opens and publication are relative to held directory handles.
No path-following fallback, additional store, credentials or privileges.
"""

from __future__ import annotations

import ctypes as c
import msvcrt
import os
from contextlib import contextmanager
from pathlib import Path


class UnsafePath(ValueError):
    """A path/filesystem cannot meet the host's no-follow contract."""


class _UnicodeString(c.Structure):
    _fields_ = [("Length", c.c_ushort), ("MaximumLength", c.c_ushort), ("Buffer", c.c_void_p)]


class _ObjectAttributes(c.Structure):
    _fields_ = [
        ("Length", c.c_ulong),
        ("RootDirectory", c.c_void_p),
        ("ObjectName", c.POINTER(_UnicodeString)),
        ("Attributes", c.c_ulong),
        ("SecurityDescriptor", c.c_void_p),
        ("SecurityQualityOfService", c.c_void_p),
    ]


class _IoStatus(c.Structure):
    _fields_ = [("Status", c.c_void_p), ("Information", c.c_size_t)]


class _FileInfo(c.Structure):
    _fields_ = [
        ("Attributes", c.c_ulong),
        ("Creation", c.c_ulong * 2),
        ("Access", c.c_ulong * 2),
        ("Write", c.c_ulong * 2),
        ("Volume", c.c_ulong),
        ("SizeHigh", c.c_ulong),
        ("SizeLow", c.c_ulong),
        ("Links", c.c_ulong),
        ("IndexHigh", c.c_ulong),
        ("IndexLow", c.c_ulong),
    ]


class _RenameInfo(c.Structure):
    _fields_ = [
        ("ReplaceIfExists", c.c_ulong),
        ("RootDirectory", c.c_void_p),
        ("FileNameLength", c.c_ulong),
        ("FileName", c.c_wchar * 1),
    ]


_nt = c.WinDLL("ntdll")
_kernel = c.WinDLL("kernel32", use_last_error=True)
_create = _nt.NtCreateFile
_create.restype = c.c_long
_create.argtypes = (
    c.POINTER(c.c_void_p),
    c.c_ulong,
    c.POINTER(_ObjectAttributes),
    c.POINTER(_IoStatus),
    c.c_void_p,
    c.c_ulong,
    c.c_ulong,
    c.c_ulong,
    c.c_ulong,
    c.c_void_p,
    c.c_ulong,
)
_error = _nt.RtlNtStatusToDosError
_error.argtypes = (c.c_long,)
_error.restype = c.c_ulong
_nt_set_info = _nt.NtSetInformationFile
_nt_set_info.argtypes = (c.c_void_p, c.POINTER(_IoStatus), c.c_void_p, c.c_ulong, c.c_int)
_nt_set_info.restype = c.c_long
_close = _kernel.CloseHandle
_close.argtypes = (c.c_void_p,)
_close.restype = c.c_int
_get_info = _kernel.GetFileInformationByHandle
_get_info.argtypes = (c.c_void_p, c.POINTER(_FileInfo))
_get_info.restype = c.c_int
_set_info = _kernel.SetFileInformationByHandle
_set_info.argtypes = (c.c_void_p, c.c_int, c.c_void_p, c.c_ulong)
_set_info.restype = c.c_int
_volume_info = _kernel.GetVolumeInformationByHandleW
_volume_info.argtypes = (
    c.c_void_p,
    c.c_wchar_p,
    c.c_ulong,
    c.c_void_p,
    c.c_void_p,
    c.c_void_p,
    c.c_wchar_p,
    c.c_ulong,
)
_volume_info.restype = c.c_int
_drive_type = _kernel.GetDriveTypeW
_drive_type.argtypes = (c.c_wchar_p,)
_drive_type.restype = c.c_uint


def _open(
    name: str,
    parent: int | None,
    *,
    directory: bool,
    create: bool = False,
    writable: bool = False,
    share: int = 1,
) -> int:
    encoded = name.encode("utf-16-le")
    if len(encoded) > 65_532:
        raise UnsafePath("research path component is too long")
    buffer = c.create_unicode_buffer(name)
    string = _UnicodeString(len(encoded), len(encoded) + 2, c.cast(buffer, c.c_void_p))
    attributes = _ObjectAttributes(
        c.sizeof(_ObjectAttributes), parent, c.pointer(string), 0x40, None, None
    )  # OBJ_CASE_INSENSITIVE
    handle, status = c.c_void_p(), _IoStatus()
    # Directory handles are anchors, never data-I/O handles. READ_ATTRIBUTES
    # suffices for reparse/type verification and avoids unnecessary SYNCHRONIZE
    # rights on read-only ancestors. File descriptors require synchronous I/O.
    # FILE_LIST_DIRECTORY makes directory anchors participate in sharing checks.
    # Attribute-only opens can permit a root move before the first leaf is open.
    # Share directory writes for NTFS's internal target open during publication;
    # never share deletion, so held ancestors cannot move. No directory data I/O
    # is performed, and SYNCHRONIZE is not needed. Leaves keep their own modes.
    options = 0x200000 | (1 if directory else 0x60)
    access = 0x81 if directory else 0x80100000
    native_share = share | 2 if directory else share
    if directory and create:
        options |= 2  # NTFS directory-creation metadata is write-through too.
    if writable:
        access |= 0x40010000  # GENERIC_WRITE | DELETE for handle-only rename/cleanup
        options |= 2  # FILE_WRITE_THROUGH: includes NTFS rename metadata flushing
    disposition = (3 if directory else 2) if create else 1  # OPEN_IF / CREATE / OPEN
    result = _create(
        c.byref(handle),
        access,
        c.byref(attributes),
        c.byref(status),
        None,
        0,
        native_share,
        disposition,
        options,
        None,
        0,
    )
    if result < 0:
        raise c.WinError(_error(result))
    if handle.value is None:
        raise OSError("native research open returned no handle")
    try:
        info = _info(handle.value)
        if info.Attributes & 0x400 or bool(info.Attributes & 0x10) != directory:
            raise UnsafePath(
                "research components must be ordinary directories/files, not reparse points"
            )
    except BaseException:
        _close(handle)
        raise
    return handle.value


def _info(handle: int) -> _FileInfo:
    info = _FileInfo()
    if not _get_info(handle, c.byref(info)):
        raise c.WinError(c.get_last_error())
    return info


@contextmanager
def _root(root: Path, *, create: bool):
    # Do not normalize away traversal through a reparse component or accept DOS devices/ADS.
    if not root.is_absolute() or len(root.drive) != 2 or root.drive[1] != ":":
        raise UnsafePath("Windows research_root requires an absolute local drive path")
    if any(p in {".", ".."} or p.endswith((".", " ")) or ":" in p for p in root.parts[1:]):
        raise UnsafePath("ambiguous research-root path component")
    if _drive_type(root.anchor) != 3:  # fixed local drive; not network/device/removable
        raise UnsafePath("Windows research_root requires a fixed local NTFS volume")
    handles: list[int] = []
    try:
        handles.append(_open("\\??\\" + root.anchor, None, directory=True))
        filesystem = c.create_unicode_buffer(32)
        if not _volume_info(handles[0], None, 0, None, None, None, filesystem, 32):
            raise c.WinError(c.get_last_error())
        if filesystem.value != "NTFS":
            raise UnsafePath("Windows research_root requires NTFS write-through publication")
        for part in root.parts[1:]:
            # FILE_OPEN_IF can require creation rights even for an existing ancestor.
            # Do not request mutation of read-only ancestors outside research_root.
            try:
                child = _open(part, handles[-1], directory=True)
            except FileNotFoundError:
                if not create:
                    raise
                child = _open(part, handles[-1], directory=True, create=True)
            handles.append(child)
        yield handles[-1]
    finally:
        for handle in reversed(handles):
            _close(handle)


def _fd(handle: int, *, writable: bool = False) -> int:
    try:
        return msvcrt.open_osfhandle(handle, os.O_BINARY | (os.O_RDWR if writable else os.O_RDONLY))
    except BaseException:
        _close(handle)
        raise


def _read(fd: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while chunk := os.read(fd, 65_536):
        chunks.append(chunk)
    return b"".join(chunks)


def _read_at(root: int, name: str) -> bytes:
    fd = _fd(_open(name, root, directory=False))
    try:
        return _read(fd)
    finally:
        os.close(fd)


def read_blob(root: Path, name: str) -> bytes:
    _validate_leaf(name)
    with _root(root, create=False) as directory:
        return _read_at(directory, name)


def _validate_leaf(name: str) -> None:
    if (
        not name
        or name in {".", ".."}
        or name.endswith((".", " "))
        or any(character in name for character in ("/", "\\", ":", "\0"))
    ):
        raise UnsafePath("research blob names are single unambiguous path components")


def _rename(handle: int, root: int, name: str) -> None:
    encoded = name.encode("utf-16-le")
    size = c.sizeof(_RenameInfo) + len(encoded) + 2
    buffer = c.create_string_buffer(max(size, c.sizeof(_RenameInfo)))
    info = _RenameInfo.from_buffer(buffer)
    info.ReplaceIfExists = 0
    info.RootDirectory = root
    info.FileNameLength = len(encoded)
    c.memmove(c.addressof(buffer) + _RenameInfo.FileName.offset, encoded, len(encoded))
    status = _IoStatus()
    # The Win32 wrapper rejects a non-null RootDirectory on some Windows builds.
    # Native FileRenameInformation retains the documented handle-relative target.
    result = _nt_set_info(handle, c.byref(status), buffer, size, 10)
    if result < 0:
        raise c.WinError(_error(result))


def _delete_temp(handle: int) -> None:
    # FileDispositionInfo: delete the held object, never unlink a path that could be swapped.
    delete = c.c_ubyte(1)
    if not _set_info(handle, 4, c.byref(delete), 1):
        raise c.WinError(c.get_last_error())


def _flush_existing(root: int, name: str, payload: bytes) -> bool:
    """Validate and flush one held existing blob before acknowledging a retry.

    Deny external writes/deletes for the entire comparison and flush. A racing
    publisher still holding its writable handle causes a sharing refusal; the
    caller may retry after that publisher completes. Never claim durability from
    a read alone, including after a previous post-publication flush failure.
    """
    try:
        handle = _open(name, root, directory=False, writable=True)
    except FileNotFoundError:
        return False
    fd = _fd(handle, writable=True)
    try:
        if _read(fd) != payload:
            raise UnsafePath("an existing content-addressed blob cannot be overwritten")
        os.fsync(fd)
        return True
    finally:
        os.close(fd)


def write_blob(root: Path, name: str, payload: bytes) -> None:
    _validate_leaf(name)
    with _root(root, create=True) as directory:
        if _flush_existing(directory, name, payload):
            return
        # Exclusive, handle-relative creation owns the staging object; randomness
        # is unnecessary. Bound collision retries like the POSIX host adapter,
        # preserving every pre-existing leaf and failing closed on exhaustion.
        for attempt in range(32):
            temporary = f".{name}.write-{attempt}"
            try:
                handle = _open(temporary, directory, directory=False, create=True, writable=True)
            except FileExistsError:
                continue
            break
        else:
            raise UnsafePath("no exclusive temporary filename was available for the research blob")
        try:
            fd = msvcrt.open_osfhandle(handle, os.O_BINARY | os.O_RDWR)
        except BaseException:
            try:
                _delete_temp(handle)
            finally:
                _close(handle)
            raise
        published = False
        try:
            offset = 0
            while offset < len(payload):
                count = os.write(fd, memoryview(payload)[offset:])
                if count == 0:
                    raise OSError("zero-length research write")
                offset += count
            os.fsync(fd)
            try:
                _rename(handle, directory, name)
            except FileExistsError as exc:
                if not _flush_existing(directory, name, payload):
                    raise UnsafePath("concurrent blob disappeared before verification") from exc
                return
            published = True
            os.fsync(fd)
            check = _fd(_open(name, directory, directory=False, share=7))
            try:
                named, held = _info(msvcrt.get_osfhandle(check)), _info(handle)
                if (named.Volume, named.IndexHigh, named.IndexLow) != (
                    held.Volume,
                    held.IndexHigh,
                    held.IndexLow,
                ) or _read(check) != payload:
                    raise UnsafePath(
                        "published research bytes/identity differ from admitted temporary file"
                    )
            finally:
                os.close(check)
        finally:
            try:
                if not published:
                    _delete_temp(handle)
            finally:
                os.close(fd)
