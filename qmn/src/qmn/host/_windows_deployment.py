"""Read-only, handle-relative deployment reader on native Windows.

Each name is opened relative to a held directory, with reparse processing
disabled. Handles deny write/delete sharing until the bounded read and identity
checks finish. Native errors propagate; there is no path-following fallback.
"""

from __future__ import annotations

import ctypes as c
from contextlib import ExitStack
from pathlib import Path
from typing import cast


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
    # The first field is a union of NTSTATUS and a pointer, hence pointer-sized.
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


class _FileIdInfo(c.Structure):
    _fields_ = [("VolumeSerialNumber", c.c_ulonglong), ("FileId", c.c_ubyte * 16)]


class _NativeReader:
    def __init__(self) -> None:
        native = c.WinDLL("ntdll")
        kernel = c.WinDLL("kernel32", use_last_error=True)
        self.open_file = native.NtOpenFile
        self.open_file.argtypes = [
            c.POINTER(c.c_void_p),
            c.c_ulong,
            c.POINTER(_ObjectAttributes),
            c.POINTER(_IoStatus),
            c.c_ulong,
            c.c_ulong,
        ]
        self.open_file.restype = c.c_long
        self.error = native.RtlNtStatusToDosError
        self.error.argtypes = [c.c_long]
        self.error.restype = c.c_ulong
        self.close_handle = kernel.CloseHandle
        self.close_handle.argtypes = [c.c_void_p]
        self.close_handle.restype = c.c_int
        self.get_info = kernel.GetFileInformationByHandle
        self.get_info.argtypes = [c.c_void_p, c.POINTER(_FileInfo)]
        self.get_info.restype = c.c_int
        self.get_info_ex = kernel.GetFileInformationByHandleEx
        self.get_info_ex.argtypes = [c.c_void_p, c.c_int, c.c_void_p, c.c_ulong]
        self.get_info_ex.restype = c.c_int
        self.file_type = kernel.GetFileType
        self.file_type.argtypes = [c.c_void_p]
        self.file_type.restype = c.c_ulong
        self.drive_type = kernel.GetDriveTypeW
        self.drive_type.argtypes = [c.c_wchar_p]
        self.drive_type.restype = c.c_uint
        self.read_file = kernel.ReadFile
        self.read_file.argtypes = [
            c.c_void_p,
            c.c_void_p,
            c.c_ulong,
            c.POINTER(c.c_ulong),
            c.c_void_p,
        ]
        self.read_file.restype = c.c_int

    def close(self, handle: int) -> None:
        if not self.close_handle(handle):
            raise c.WinError(c.get_last_error())

    def snapshot(self, handle: int, *, directory: bool) -> tuple[bytes, int, int, int]:
        info, identity = _FileInfo(), _FileIdInfo()
        if not self.get_info(handle, c.byref(info)):
            raise c.WinError(c.get_last_error())
        if info.Attributes & 0x400 or bool(info.Attributes & 0x10) != directory:
            raise OSError(
                "deployment components must be ordinary files/directories, not reparse points"
            )
        if self.file_type(handle) != 1:  # FILE_TYPE_DISK
            raise OSError("deployment components must be disk files/directories")
        if not self.get_info_ex(handle, 18, c.byref(identity), c.sizeof(identity)):  # FileIdInfo
            raise c.WinError(c.get_last_error())
        size = int(info.SizeHigh) << 32 | int(info.SizeLow)
        write = int(info.Write[1]) << 32 | int(info.Write[0])
        return bytes(identity), size, write, int(info.Attributes)

    def open(self, name: str, parent: int | None, *, directory: bool) -> int:
        encoded = name.encode("utf-16-le")
        if len(encoded) > 65_532:
            raise ValueError("deployment component is too long")
        buffer = c.create_unicode_buffer(name)
        string = _UnicodeString(len(encoded), len(encoded) + 2, c.cast(buffer, c.c_void_p))
        attributes = _ObjectAttributes(
            c.sizeof(_ObjectAttributes), parent, c.pointer(string), 0x40, None, None
        )  # OBJ_CASE_INSENSITIVE; names below the anchor are single components.
        handle, status = c.c_void_p(), _IoStatus()
        access = 0x100080 if directory else 0x80100000  # sync/attributes or generic read
        options = 0x20 | 0x200000 | (1 if directory else 0x40)
        # SYNCHRONOUS_IO_NONALERT | OPEN_REPARSE_POINT | DIRECTORY/NON_DIRECTORY_FILE
        result = cast(
            "int",
            self.open_file(
                c.byref(handle), access, c.byref(attributes), c.byref(status), 1, options
            ),
        )  # FILE_SHARE_READ only: replacements and ordinary writes are excluded.
        if result < 0:
            raise c.WinError(cast("int", self.error(result)))
        if handle.value is None:
            raise OSError("native deployment open returned no handle")
        try:
            self.snapshot(handle.value, directory=directory)
        except BaseException:
            self.close(handle.value)
            raise
        return handle.value

    def read(self, handle: int, limit: int) -> bytes:
        before = self.snapshot(handle, directory=False)
        if before[1] > limit:
            raise OSError("deployment file exceeds 1 MiB")
        data = bytearray()
        while len(data) <= limit:
            size = min(65_536, limit + 1 - len(data))
            buffer, count = c.create_string_buffer(size), c.c_ulong()
            if not self.read_file(handle, buffer, size, c.byref(count), None):
                raise c.WinError(c.get_last_error())
            if count.value == 0:
                break
            data.extend(buffer.raw[: count.value])
        if len(data) > limit or len(data) != before[1]:
            raise OSError("deployment file exceeds the bound or changed during read")
        if self.snapshot(handle, directory=False) != before:
            raise OSError("deployment file identity or metadata changed during read")
        return bytes(data)


def _validate_component(name: str) -> None:
    reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    reserved.update(f"{prefix}{number}" for prefix in ("COM", "LPT") for number in "123456789¹²³")
    if (
        name in {"", ".", ".."}
        or name.endswith((".", " "))
        or any(character in name for character in ":\\/\0")
        or name.split(".", 1)[0].upper() in reserved
    ):
        raise ValueError("ambiguous Windows deployment path component")


def read_deployment(root: Path, relative_path: Path, *, limit: int) -> bytes:
    """Open only existing, ordinary local files; never request write authority."""
    if not relative_path.parts or relative_path.is_absolute():
        raise ValueError("deployment path requires a normalized relative file name")
    if type(limit) is not int or not 0 <= limit <= 1 << 20:
        raise ValueError("deployment read bound must be an integer at most 1 MiB")
    if not root.is_absolute() or len(root.drive) != 2 or root.drive[1] != ":":
        raise ValueError("Windows deployment root requires an absolute local drive path")
    for part in (*root.parts[1:], *relative_path.parts):
        _validate_component(part)
    native = _NativeReader()
    if native.drive_type(root.anchor) != 3:  # DRIVE_FIXED; reject UNC/device/removable roots.
        raise OSError("Windows deployment root requires a fixed local volume")
    with ExitStack() as stack:
        parent = native.open("\\??\\" + root.anchor, None, directory=True)
        stack.callback(native.close, parent)
        directories: list[tuple[int, bytes]] = [
            (parent, native.snapshot(parent, directory=True)[0])
        ]
        for part in (*root.parts[1:], *relative_path.parts[:-1]):
            parent = native.open(part, parent, directory=True)
            stack.callback(native.close, parent)
            directories.append((parent, native.snapshot(parent, directory=True)[0]))
        leaf = native.open(relative_path.parts[-1], parent, directory=False)
        stack.callback(native.close, leaf)
        data = native.read(leaf, limit)
        for handle, identity in directories:
            if native.snapshot(handle, directory=True)[0] != identity:
                raise OSError("deployment directory identity changed during read")
        return data
