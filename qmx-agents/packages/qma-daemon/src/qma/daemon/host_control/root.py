"""Product ``QMA_DAEMON_ROOT`` (Story 67.1; DEC-0510 A14).

Inspect cwd-relative ``qma-daemon-data`` is not the product root.
Story 67.4: recover-control is gated on OS ownership of this root.
"""

from __future__ import annotations

import ctypes
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final

__all__ = [
    "INSPECT_CWD_RELATIVE_ROOT",
    "caller_owns_daemon_root",
    "product_daemon_root",
    "resolve_daemon_root",
]


INSPECT_CWD_RELATIVE_ROOT: Final[str] = "qma-daemon-data"


def product_daemon_root(
    *,
    system: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | str | None = None,
) -> Path:
    """OS product data root for the local workstation daemon.

    Windows ``%LOCALAPPDATA%\\QMX\\qma-daemon``;
    Linux ``${XDG_STATE_HOME:-$HOME/.local/state}/qmx/qma-daemon``;
    macOS ``~/Library/Application Support/QMX/qma-daemon``.
    """
    env = os.environ if environ is None else environ
    plat = sys.platform if system is None else system
    if plat.startswith("win"):
        local = env.get("LOCALAPPDATA")
        if not local:
            base = Path.home() if home is None else Path(home)
            local = str(base / "AppData" / "Local")
        return Path(local) / "QMX" / "qma-daemon"
    if plat == "darwin":
        base = Path(env["HOME"]) if "HOME" in env else (Path.home() if home is None else Path(home))
        return base / "Library" / "Application Support" / "QMX" / "qma-daemon"
    xdg = env.get("XDG_STATE_HOME")
    if xdg:
        return Path(xdg) / "qmx" / "qma-daemon"
    base = Path(env["HOME"]) if "HOME" in env else (Path.home() if home is None else Path(home))
    return base / ".local" / "state" / "qmx" / "qma-daemon"


def resolve_daemon_root(
    environ: Mapping[str, str] | None = None,
    *,
    system: str | None = None,
    home: Path | str | None = None,
) -> Path:
    """Honor ``QMA_DAEMON_ROOT`` when set; otherwise the product root.

    Never falls back to cwd-relative ``qma-daemon-data``.
    """
    env = os.environ if environ is None else environ
    raw = env.get("QMA_DAEMON_ROOT")
    if isinstance(raw, str) and raw.strip() != "":
        return Path(raw)
    return product_daemon_root(system=system, environ=env, home=home)


def caller_owns_daemon_root(root: Path) -> bool:
    """True when the calling OS user owns ``QMA_DAEMON_ROOT`` (C1 / T-H-04)."""
    try:
        if not root.exists():
            return False
        if os.name != "nt":
            return int(root.stat().st_uid) == int(os.getuid())
        return _windows_caller_owns(root)
    except OSError:
        return False


def _windows_caller_owns(root: Path) -> bool:
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    owner_info = 0x00000001
    token_query = 0x0008
    token_user = 1

    class _SidAndAttributes(ctypes.Structure):
        _fields_ = (("Sid", ctypes.c_void_p), ("Attributes", ctypes.c_uint32))

    class _TokenUser(ctypes.Structure):
        _fields_ = (("User", _SidAndAttributes),)

    needed = ctypes.c_uint32(0)
    get_sd = advapi32.GetFileSecurityW
    get_sd.restype = ctypes.c_int
    get_sd.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    get_sd(str(root), owner_info, None, 0, ctypes.byref(needed))
    if needed.value == 0:
        return False
    sd = ctypes.create_string_buffer(needed.value)
    if not get_sd(str(root), owner_info, sd, needed, ctypes.byref(needed)):
        return False
    owner = ctypes.c_void_p()
    defaulted = ctypes.c_int(0)
    get_owner = advapi32.GetSecurityDescriptorOwner
    get_owner.restype = ctypes.c_int
    get_owner.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_int),
    ]
    if not get_owner(sd, ctypes.byref(owner), ctypes.byref(defaulted)):
        return False
    if not owner.value:
        return False
    token = ctypes.c_void_p()
    open_token = advapi32.OpenProcessToken
    open_token.restype = ctypes.c_int
    open_token.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)]
    if not open_token(kernel32.GetCurrentProcess(), token_query, ctypes.byref(token)):
        return False
    try:
        size = ctypes.c_uint32(0)
        get_info = advapi32.GetTokenInformation
        get_info.restype = ctypes.c_int
        get_info.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
        ]
        get_info(token, token_user, None, 0, ctypes.byref(size))
        if size.value == 0:
            return False
        buf = ctypes.create_string_buffer(size.value)
        if not get_info(token, token_user, buf, size, ctypes.byref(size)):
            return False
        user = _TokenUser.from_buffer(buf)
        equal = advapi32.EqualSid
        equal.restype = ctypes.c_int
        equal.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        return bool(equal(owner, user.User.Sid))
    finally:
        kernel32.CloseHandle(token)
