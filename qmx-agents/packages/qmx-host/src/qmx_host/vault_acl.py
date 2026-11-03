"""The home's vault, `<home>/vault/`, readable by this user alone on every machine (C-32).

The vault holds the pairing key that signs every run pass, an unpaired home's run pass key, the
venue session tokens and, on a server, every app's declared secret. On Windows owner-only is the
folder's DACL: this user and SYSTEM, inheritance off, so a file written later inherits the same two
entries. On Linux it is 0700 on the folder and 0600 on each file.

`owner_only` makes the vault or repairs it at start and refuses a link anywhere in it. `read_key`
reads one file through one handle that never follows a link, and checks that handle, never a path
stat taken before the read.
"""

from __future__ import annotations

import errno
import os
import stat
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Final, Literal

type Outcome = Literal["made", "kept", "repaired"]
"""What start did to the vault: made it owner-only, found it so, or took other users off it."""

FOLDER_MODE: Final = 0o700
FILE_MODE: Final = 0o600
LOOSE_BITS: Final = 0o077
SYSTEM: Final = "S-1-5-18"
ADMINISTRATORS: Final = "S-1-5-32-544"
"""The owner an elevated process gives what it writes. Owning a file lets its owner rewrite the
DACL, which Administrators may do to any file anyway, so it is no wider than SYSTEM."""
NAME_SURROGATE: Final = 0x20000000
"""The reparse tag bit of a symlink, a junction and every other link to another name."""
REPARSE_POINT: Final = 0x400

LINKED: Final = "is a link, and QMX reads no key through a link"
HARD_LINKED: Final = "has another name outside the vault (a hard link)"
FOREIGN: Final = "belongs to another user"
LOOSE: Final = "is readable by others; chmod 600 it"


class VaultRefused(Exception):
    """The vault cannot be made owner-only, so the host does not start. The message is one plain
    sentence that names the path and never a file's content."""


class KeyRefused(Exception):
    """One vault file must not be read. The message finishes "The vault file <name> ..."."""


def owner_only(vault: Path) -> Outcome:
    """Make `vault` owner-only, or take every other user off it and its files. Running it again
    changes nothing. A link or hard link anywhere in it refuses the start, and so does a file
    another user owns or one whose access Windows will not change. Every refusal but the last
    comes before any write: on Windows the folder's new DACL is pushed down to what it holds, a
    hard link's other name outside the vault among them."""
    try:
        vault.mkdir(mode=FOLDER_MODE, parents=True)
        made = True
    except FileExistsError:
        made = False
    tree = list(_tree(vault))
    for path, _folder in tree:
        if not _ours(path):
            raise VaultRefused(_unfixable(path, FOREIGN))
    fixed = False
    for path, folder in tree:
        fixed = _fix(path, folder=folder) or fixed
    return "made" if made else "repaired" if fixed else "kept"


def read_key(path: Path) -> bytes | None:
    """The bytes of one vault file, or None when it is missing. Raises `KeyRefused` for a link, a
    hard link or a file another user owns, and on POSIX for a file its group or others can read.
    Any other `OSError` is the read's own."""
    return _read(path)


def _tree(vault: Path) -> Iterator[tuple[Path, bool]]:
    """Each path in the vault, the folder first and each folder before what it holds."""
    waiting = [vault]
    while waiting:
        path = waiting.pop()
        found = os.lstat(path)
        if _is_link(found):
            raise VaultRefused(
                f"{path} in your keys folder {LINKED}; remove the link, then start QMX again"
            )
        folder = stat.S_ISDIR(found.st_mode)
        if not folder and found.st_nlink != 1:
            raise VaultRefused(
                f"{path} in your keys folder {HARD_LINKED}; remove it, then start QMX again"
            )
        if not folder and not stat.S_ISREG(found.st_mode):
            raise VaultRefused(
                f"{path} in your keys folder is not a file or a folder; remove it, then start "
                "QMX again"
            )
        yield path, folder
        if folder:
            waiting.extend(sorted(path.iterdir(), reverse=True))


def _is_link(found: os.stat_result) -> bool:
    if stat.S_ISLNK(found.st_mode):
        return True
    attributes = getattr(found, "st_file_attributes", 0)
    return bool(attributes & REPARSE_POINT) and bool(
        getattr(found, "st_reparse_tag", 0) & NAME_SURROGATE
    )


def _unfixable(path: Path, why: str) -> str:
    return (
        f"your keys folder holds {path}, which {why}, so QMX cannot make it readable by you "
        "alone; give it back to your user, then start QMX again"
    )


if sys.platform != "win32":

    def _ours(path: Path) -> bool:
        return os.lstat(path).st_uid == os.geteuid()

    def _fix(path: Path, *, folder: bool) -> bool:
        found = os.lstat(path)
        if not found.st_mode & LOOSE_BITS:
            return False
        os.chmod(path, FOLDER_MODE if folder else FILE_MODE)
        return True

    def _read(path: Path) -> bytes | None:
        flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC
        try:
            handle = os.open(path, flags)
        except FileNotFoundError:
            return None
        except OSError as error:
            if error.errno == errno.ELOOP:
                raise KeyRefused(LINKED) from None
            raise
        with os.fdopen(handle, "rb") as file:
            found = os.fstat(handle)
            if stat.S_ISDIR(found.st_mode):
                raise IsADirectoryError(errno.EISDIR, "a folder")
            if not stat.S_ISREG(found.st_mode):
                raise OSError(errno.EINVAL, "not a file")
            if found.st_uid != os.geteuid():
                raise KeyRefused(FOREIGN)
            if found.st_mode & LOOSE_BITS:
                raise KeyRefused(LOOSE)
            if found.st_nlink != 1:
                raise KeyRefused(HARD_LINKED)
            return file.read()

else:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    _advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    _kernel = ctypes.WinDLL("kernel32", use_last_error=True)

    _FILE_OBJECT: Final = 1
    _OWNER: Final = 0x1
    _DACL: Final = 0x4
    _PROTECTED_DACL: Final = 0x80000000
    _DACL_PROTECTED: Final = 0x1000
    _ALLOWED: Final = 0
    _DENIED: Final = 1
    _INHERIT_DOWN: Final = 0x1 | 0x2
    """OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE: what the vault holds gets the same entries."""
    _INHERITED: Final = 0x10
    _FILE_ALL_ACCESS: Final = 0x1F01FF
    _ACL_REVISION: Final = 2
    _ACL_SIZE: Final = 2
    _GENERIC_READ: Final = 0x80000000
    _SHARE_ALL: Final = 0x1 | 0x2 | 0x4
    _OPEN_EXISTING: Final = 3
    _OPEN_REPARSE_POINT: Final = 0x00200000
    _BACKUP_SEMANTICS: Final = 0x02000000
    """Lets the handle open a folder or a junction, so the reader refuses a junction by its tag."""
    _DIRECTORY: Final = 0x10
    """A plain folder answers PermissionError, the error Windows gave before the handle could open
    one, which `test_server_secrets.py` pins."""
    _TAG_INFO: Final = 9
    _MISSING: Final = frozenset({2, 3})
    _INVALID: Final = wintypes.HANDLE(-1).value
    _TOKEN_QUERY: Final = 0x8
    _TOKEN_USER: Final = 1

    class _AclSize(ctypes.Structure):
        _fields_ = (
            ("count", wintypes.DWORD),
            ("used", wintypes.DWORD),
            ("free", wintypes.DWORD),
        )

    class _TagInfo(ctypes.Structure):
        _fields_ = (("attributes", wintypes.DWORD), ("tag", wintypes.DWORD))

    _P = ctypes.c_void_p
    _PP = ctypes.POINTER(ctypes.c_void_p)
    for _name, _args, _result in (
        (
            "GetNamedSecurityInfoW",
            (wintypes.LPCWSTR, ctypes.c_int, wintypes.DWORD, _PP, _PP, _PP, _PP, _PP),
            wintypes.DWORD,
        ),
        (
            "GetSecurityInfo",
            (wintypes.HANDLE, ctypes.c_int, wintypes.DWORD, _PP, _PP, _PP, _PP, _PP),
            wintypes.DWORD,
        ),
        (
            "SetNamedSecurityInfoW",
            (wintypes.LPWSTR, ctypes.c_int, wintypes.DWORD, _P, _P, _P, _P),
            wintypes.DWORD,
        ),
        (
            "GetSecurityDescriptorControl",
            (_P, ctypes.POINTER(wintypes.WORD), ctypes.POINTER(wintypes.DWORD)),
            wintypes.BOOL,
        ),
        ("GetAclInformation", (_P, _P, wintypes.DWORD, ctypes.c_int), wintypes.BOOL),
        ("GetAce", (_P, wintypes.DWORD, _PP), wintypes.BOOL),
        ("ConvertSidToStringSidW", (_P, ctypes.POINTER(wintypes.LPWSTR)), wintypes.BOOL),
        ("ConvertStringSidToSidW", (wintypes.LPCWSTR, _PP), wintypes.BOOL),
        ("InitializeAcl", (_P, wintypes.DWORD, wintypes.DWORD), wintypes.BOOL),
        (
            "AddAccessAllowedAceEx",
            (_P, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, _P),
            wintypes.BOOL,
        ),
        ("GetLengthSid", (_P,), wintypes.DWORD),
        (
            "OpenProcessToken",
            (wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)),
            wintypes.BOOL,
        ),
        (
            "GetTokenInformation",
            (wintypes.HANDLE, ctypes.c_int, _P, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)),
            wintypes.BOOL,
        ),
    ):
        getattr(_advapi, _name).argtypes = _args
        getattr(_advapi, _name).restype = _result
    for _name, _args, _result in (
        (
            "CreateFileW",
            (
                wintypes.LPCWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
                _P,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.HANDLE,
            ),
            wintypes.HANDLE,
        ),
        (
            "GetFileInformationByHandleEx",
            (wintypes.HANDLE, ctypes.c_int, _P, wintypes.DWORD),
            wintypes.BOOL,
        ),
        ("CloseHandle", (wintypes.HANDLE,), wintypes.BOOL),
        ("GetCurrentProcess", (), wintypes.HANDLE),
        ("LocalFree", (_P,), _P),
    ):
        getattr(_kernel, _name).argtypes = _args
        getattr(_kernel, _name).restype = _result

    def _check(done: object) -> None:
        if not done:
            raise ctypes.WinError(ctypes.get_last_error())

    def _sid_text(sid: int | None) -> str:
        text = wintypes.LPWSTR()
        _check(_advapi.ConvertSidToStringSidW(sid, ctypes.byref(text)))
        try:
            return text.value or ""
        finally:
            _kernel.LocalFree(ctypes.cast(text, ctypes.c_void_p))

    def _me() -> str:
        token = wintypes.HANDLE()
        _check(
            _advapi.OpenProcessToken(_kernel.GetCurrentProcess(), _TOKEN_QUERY, ctypes.byref(token))
        )
        try:
            size = wintypes.DWORD()
            _advapi.GetTokenInformation(token, _TOKEN_USER, None, 0, ctypes.byref(size))
            buffer = ctypes.create_string_buffer(size.value)
            _check(
                _advapi.GetTokenInformation(token, _TOKEN_USER, buffer, size, ctypes.byref(size))
            )
            return _sid_text(ctypes.c_void_p.from_buffer(buffer).value)
        finally:
            _kernel.CloseHandle(token)

    type _Entry = tuple[int, int, int, str]
    """One DACL entry: its kind, its inherit flags without the inherited bit, its mask, its SID."""

    def _entries(dacl: int | None) -> list[_Entry] | None:
        """Each entry of the DACL, sorted, or None for a missing DACL, which lets everyone in, or
        for an entry whose kind names no plain SID."""
        if not dacl:
            return None
        size = _AclSize()
        _check(_advapi.GetAclInformation(dacl, ctypes.byref(size), ctypes.sizeof(size), _ACL_SIZE))
        found: list[_Entry] = []
        for index in range(size.count):
            ace = ctypes.c_void_p()
            _check(_advapi.GetAce(dacl, index, ctypes.byref(ace)))
            start = ace.value or 0
            kind = ctypes.c_ubyte.from_address(start).value
            if kind not in {_ALLOWED, _DENIED}:
                return None
            flags = ctypes.c_ubyte.from_address(start + 1).value & ~_INHERITED
            mask = wintypes.DWORD.from_address(start + 4).value
            found.append((kind, flags, mask, _sid_text(start + 8)))
        return sorted(found)

    def _p() -> ctypes.c_void_p:
        return ctypes.c_void_p()

    def _ours(path: Path) -> bool:
        return _owner_of(path) in {_me(), SYSTEM, ADMINISTRATORS}

    def _owner_of(path: Path) -> str:
        owner, descriptor = _p(), _p()
        failed = _advapi.GetNamedSecurityInfoW(
            str(path),
            _FILE_OBJECT,
            _OWNER,
            ctypes.byref(owner),
            None,
            None,
            None,
            ctypes.byref(descriptor),
        )
        if failed:
            raise VaultRefused(_unfixable(path, f"Windows would not show its owner ({failed})"))
        try:
            return _sid_text(owner.value)
        finally:
            _kernel.LocalFree(descriptor)

    def _fix(path: Path, *, folder: bool) -> bool:
        me = _me()
        dacl, descriptor = _p(), _p()
        failed = _advapi.GetNamedSecurityInfoW(
            str(path),
            _FILE_OBJECT,
            _DACL,
            None,
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(descriptor),
        )
        if failed:
            raise VaultRefused(_unfixable(path, f"Windows would not show its access ({failed})"))
        try:
            control, revision = wintypes.WORD(), wintypes.DWORD()
            _check(
                _advapi.GetSecurityDescriptorControl(
                    descriptor, ctypes.byref(control), ctypes.byref(revision)
                )
            )
            found = _entries(dacl.value)
            protected = bool(control.value & _DACL_PROTECTED)
        finally:
            _kernel.LocalFree(descriptor)
        flags = _INHERIT_DOWN if folder else 0
        wanted = sorted((_ALLOWED, flags, _FILE_ALL_ACCESS, sid) for sid in (me, SYSTEM))
        if found == wanted and (protected or not folder):
            return False
        _set(path, me, folder=folder)
        return True

    def _set(path: Path, me: str, *, folder: bool) -> None:
        sids = [_sid(me), _sid(SYSTEM)]
        try:
            size = 8 + sum(8 + _advapi.GetLengthSid(sid) for sid in sids)
            acl = ctypes.create_string_buffer(size)
            _check(_advapi.InitializeAcl(acl, size, _ACL_REVISION))
            for sid in sids:
                _check(
                    _advapi.AddAccessAllowedAceEx(
                        acl, _ACL_REVISION, _INHERIT_DOWN if folder else 0, _FILE_ALL_ACCESS, sid
                    )
                )
            failed = _advapi.SetNamedSecurityInfoW(
                str(path),
                _FILE_OBJECT,
                _DACL | _PROTECTED_DACL,
                None,
                None,
                ctypes.addressof(acl),
                None,
            )
        finally:
            for sid in sids:
                _kernel.LocalFree(sid)
        if failed:
            raise VaultRefused(_unfixable(path, f"Windows would not change its access ({failed})"))

    def _sid(text: str) -> int:
        sid = ctypes.c_void_p()
        _check(_advapi.ConvertStringSidToSidW(text, ctypes.byref(sid)))
        return sid.value or 0

    def _read(path: Path) -> bytes | None:
        handle = _kernel.CreateFileW(
            str(path),
            _GENERIC_READ,
            _SHARE_ALL,
            None,
            _OPEN_EXISTING,
            _OPEN_REPARSE_POINT | _BACKUP_SEMANTICS,
            None,
        )
        if handle == _INVALID or handle is None:
            error = ctypes.get_last_error()
            if error in _MISSING:
                return None
            raise ctypes.WinError(error)
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY)
        try:
            tag = _TagInfo()
            _check(
                _kernel.GetFileInformationByHandleEx(
                    handle, _TAG_INFO, ctypes.byref(tag), ctypes.sizeof(tag)
                )
            )
            if tag.attributes & REPARSE_POINT and tag.tag & NAME_SURROGATE:
                raise KeyRefused(LINKED)
            if tag.attributes & _DIRECTORY:
                raise PermissionError(errno.EACCES, "a folder")
            if os.fstat(fd).st_nlink != 1:
                raise KeyRefused(HARD_LINKED)
            owner, descriptor = _p(), _p()
            failed = _advapi.GetSecurityInfo(
                handle,
                _FILE_OBJECT,
                _OWNER,
                ctypes.byref(owner),
                None,
                None,
                None,
                ctypes.byref(descriptor),
            )
            if failed:
                raise ctypes.WinError(failed)
            try:
                who = _sid_text(owner.value)
            finally:
                _kernel.LocalFree(descriptor)
            if who not in {_me(), SYSTEM, ADMINISTRATORS}:
                raise KeyRefused(FOREIGN)
            with os.fdopen(fd, "rb", closefd=False) as file:
                return file.read()
        finally:
            os.close(fd)
