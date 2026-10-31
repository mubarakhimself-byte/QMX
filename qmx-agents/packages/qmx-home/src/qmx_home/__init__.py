"""Where his QMX folder is: one resolver for every entry point (design 62 A1 and A2).

`resolve()` looks, in order, at the `--home` flag, `QMX_HOME`, the pointer file, the default
folder of A1 when it holds a label, and then each fixed drive's `QMX` folder holding a label. It
never makes a folder unless the caller passes the flag with `create=True`, so a test or a lane
can make a throwaway folder and nothing else can. Standard library only, so a command line can
resolve its folder before it imports anything heavy.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import sys
import tomllib
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Final

__all__ = ["LABEL", "Label", "Layout", "NoQmxFolder", "pointer_file", "resolve"]

LABEL: Final = "qmx-home.toml"
"""The label file at the top of a QMX folder; the scan trusts only a folder holding one."""
FORMAT: Final = "qmx-home"
FLAT: Final = 1
"""Format 1: today's flat home, where every package's files sit at the folder's top."""
NOT_FOUND: Final = "no QMX folder found: start QMX once, or pass --home"
FIXED_DRIVE: Final = 3
"""`DRIVE_FIXED` from `GetDriveTypeW`: a local disk, never a network, removable or RAM drive."""


class NoQmxFolder(Exception):
    """No QMX folder could be found or made. The message is the one line a command prints."""


@dataclass(frozen=True, slots=True)
class Label:
    """The label at the top of a QMX folder (design 62 B1), without its store table yet."""

    home_id: str
    format_version: int
    created_by: str
    last_written_by: str

    @classmethod
    def mint(cls, format_version: int = FLAT) -> Label:
        release = version("qmx-home")
        return cls(str(uuid.uuid7()), format_version, release, release)

    @classmethod
    def parse(cls, text: str) -> Label:
        """The label in `text`. Raises ValueError when it is not a QMX folder's label."""
        try:
            fields = tomllib.loads(text)
        except tomllib.TOMLDecodeError as broken:
            raise ValueError(f"not TOML: {broken}") from None
        match fields:
            case {
                "format": "qmx-home",
                "format_version": int(format_version),
                "home_id": str(home_id),
                "created_by": str(created_by),
                "last_written_by": str(last_written_by),
            }:
                return cls(home_id, format_version, created_by, last_written_by)
            case _:
                raise ValueError("not a qmx-home label")

    def dump(self) -> str:
        return (
            f'format = "{FORMAT}"\n'
            f"format_version = {self.format_version}\n"
            f'home_id = "{self.home_id}"\n'
            f'created_by = "{self.created_by}"\n'
            f'last_written_by = "{self.last_written_by}"\n'
        )


@dataclass(frozen=True, slots=True)
class Layout:
    """The parts of one QMX folder (design 62 A3)."""

    root: Path

    @property
    def home(self) -> Path:
        """What every package calls its home. In the flat format 1 it is the folder itself; the
        format 2 layout step moves it to `data`."""
        return self.root

    @property
    def label(self) -> Path:
        return self.root / LABEL

    @property
    def readme(self) -> Path:
        return self.root / "README.txt"

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def keys(self) -> Path:
        return self.root / "keys"

    @property
    def backups(self) -> Path:
        return self.root / "backups"

    @property
    def cache(self) -> Path:
        return self.root / "cache"

    @property
    def logs(self) -> Path:
        return self.root / "logs"


def pointer_file() -> Path | None:
    """The per-OS file that says where the folder is, or None when the OS names no config
    folder for this user."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        return Path(appdata) / "QMX" / "home.toml" if appdata else None
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "QMX" / "home.toml"
    config = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config) / "qmx" / "home.toml"


def resolve(
    flag: Path | None = None, *, create: bool = False, drives: Sequence[Path] | None = None
) -> Layout:
    """The QMX folder, found in design 62 A2's order. Raises NoQmxFolder when there is none.

    The flag and `QMX_HOME` are taken as named and must be folders that exist; `create` makes
    the flag's folder, labelled as format 1, when it is missing or empty. A pointer naming a
    missing folder is passed over, so a lost pointer falls through to the scan. `drives` is the
    list of fixed drives to scan; the machine's own when None.
    """
    if create and flag is None:
        raise NoQmxFolder("--create needs --home <path>")
    if flag is not None:
        root = flag.resolve()
        if create:
            _make(root)
        return _existing(root, f"no QMX folder at {root}")
    named = os.environ.get("QMX_HOME")
    if named:
        root = Path(named).resolve()
        return _existing(root, f"QMX_HOME names {root}, which is not a folder")
    pointed = _pointed()
    if pointed is not None:
        return Layout(pointed)
    fixed = _fixed_drives() if drives is None else list(drives)
    for candidate in dict.fromkeys([_default_root(fixed), *(d / "QMX" for d in fixed)]):
        if _labelled(candidate):
            return Layout(candidate.resolve())
    raise NoQmxFolder(NOT_FOUND)


def _existing(root: Path, refusal: str) -> Layout:
    if not root.is_dir():
        raise NoQmxFolder(refusal)
    return Layout(root)


def _make(root: Path) -> None:
    try:
        if root.is_dir() and any(root.iterdir()):
            return
        root.mkdir(parents=True, exist_ok=True)
        (root / LABEL).write_text(Label.mint().dump(), encoding="utf-8")
    except OSError as refused:
        raise NoQmxFolder(f"cannot make a QMX folder at {root}: {refused.strerror}") from None


def _pointed() -> Path | None:
    pointer = pointer_file()
    try:
        named = tomllib.loads(pointer.read_text(encoding="utf-8"))["home"] if pointer else None
    except OSError, tomllib.TOMLDecodeError, KeyError:
        return None
    if not isinstance(named, str):
        return None
    root = Path(named)
    return root.resolve() if root.is_dir() else None


def _labelled(root: Path) -> bool:
    try:
        Label.parse((root / LABEL).read_text(encoding="utf-8"))
    except OSError, ValueError:
        return False
    return True


def _default_root(fixed: Sequence[Path]) -> Path:
    """A1's default: on Windows the fixed drive with the most free space when that is not the
    system drive, else the profile; elsewhere `~/QMX`."""
    if sys.platform != "win32" or not fixed:
        return Path.home() / "QMX"
    system = Path(os.environ.get("SYSTEMDRIVE", "C:") + "\\")
    roomiest = max(fixed, key=_free)
    return Path.home() / "QMX" if roomiest == system else roomiest / "QMX"


def _free(drive: Path) -> int:
    try:
        return shutil.disk_usage(drive).free
    except OSError:
        return -1


def _fixed_drives() -> list[Path]:
    if sys.platform != "win32":
        return []
    kernel32 = ctypes.windll.kernel32
    mask: int = kernel32.GetLogicalDrives()
    roots = [f"{chr(ord('A') + bit)}:\\" for bit in range(26) if mask >> bit & 1]
    return [Path(root) for root in roots if kernel32.GetDriveTypeW(root) == FIXED_DRIVE]
