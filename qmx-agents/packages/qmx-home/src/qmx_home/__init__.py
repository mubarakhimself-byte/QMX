"""Where his QMX folder is and how it is laid out: one resolver for every entry point (design 62
A1 to A3).

`resolve()` looks, in order, at the `--home` flag, `QMX_HOME`, the pointer file, the default
folder of A1 when it holds a label, and then each fixed drive's `QMX` folder holding a label. It
opens only a folder labelled in the tree layout (format 2) and never makes a folder unless the
caller passes the flag with `create=True`, so a test or a lane can make a throwaway folder and
nothing else can. An old flat home is refused by name until `step_to_tree` moves it into the tree.
Standard library only, so a command line can resolve its folder before it imports anything heavy.
"""

from __future__ import annotations

import ctypes
import json
import os
import re
import shutil
import sys
import tomllib
import uuid
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Final, cast

__all__ = [
    "LABEL",
    "TREE",
    "Label",
    "Layout",
    "LayoutRefused",
    "NoQmxFolder",
    "pointer_file",
    "resolve",
    "step_to_tree",
]

LABEL: Final = "qmx-home.toml"
"""The label file at the top of a QMX folder; the scan trusts only a folder holding one."""
FORMAT: Final = "qmx-home"
FLAT: Final = 1
"""Format 1: the flat home, where every package's files sit at the folder's top."""
TREE: Final = 2
"""Format 2: the tree of design 62 A3, with what packages call their home in `data/`."""
PARTS: Final = ("data", "keys", "backups", "cache", "logs")
NOT_FOUND: Final = "no QMX folder found: start QMX once, or pass --home"
FIXED_DRIVE: Final = 3
"""`DRIVE_FIXED` from `GetDriveTypeW`: a local disk, never a network, removable or RAM drive."""
JOURNAL: Final = "layout-step.json"
"""The layout step's own plan, written before its first move so a stopped step resumes the same
moves instead of guessing which `logs` folder is the old one."""

FLAT_TO_TREE: Final = (
    (".qmx/vault.key", "keys/vault.key"),
    ("vault/control-token", "keys/control-token"),
    ("memory/hindsight/hf", "cache/models/huggingface"),
    ("procs", "cache/run/procs"),
    ("state", "cache/run/state"),
    ("plugins", "cache/plugins"),
    ("environments", "cache/envs"),
)
"""Design 62 A5's rows whose readers follow the tree in this release, in the order they move.
Everything else at a flat home's top moves into `data/` under its own name, and the host's
`control.log` moves last, to `logs/host.log`, once the flat `logs/` has gone to `data/logs`."""
HOST_LOG: Final = ("control.log", "logs/host.log")


class NoQmxFolder(Exception):
    """No QMX folder could be found or made. The message is the one line a command prints."""


class LayoutRefused(Exception):
    """The layout step cannot move this folder. The message names what is in the way."""


@dataclass(frozen=True, slots=True)
class Label:
    """The label at the top of a QMX folder (design 62 B1), without its store table yet."""

    home_id: str
    format_version: int
    created_by: str
    last_written_by: str

    @classmethod
    def mint(cls, format_version: int = TREE) -> Label:
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
    """The parts of one QMX folder (design 62 A3). `root` is the folder itself."""

    root: Path

    @classmethod
    def from_home(cls, home: Path) -> Layout:
        """The folder whose `data/` is `home`. Every package keeps the home it was given, so this
        is how one finds the folder's other parts from it."""
        return cls(home.parent)

    @property
    def home(self) -> Path:
        """What every package calls its home: the folder's `data/`."""
        return self.data

    @property
    def label(self) -> Path:
        return self.root / LABEL

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

    The flag, `QMX_HOME` and the pointer must name a folder labelled in the tree layout; an
    unlabelled or format 1 folder is refused with the layout step's command. `create` makes the
    flag's folder, labelled and with its five parts, when it is missing or empty. A pointer naming
    a missing folder is passed over, so a lost pointer falls through to the scan; a pointer that
    cannot be read is refused by name. `drives` is the list of fixed drives to scan; the
    machine's own when None.
    """
    if create and flag is None:
        raise NoQmxFolder("--create needs --home <path>")
    if flag is not None:
        root = flag.resolve()
        if create:
            _make(root)
        if not root.is_dir():
            raise NoQmxFolder(f"no QMX folder at {root}")
        return _opened(root)
    named = os.environ.get("QMX_HOME")
    if named:
        root = Path(named).resolve()
        if not root.is_dir():
            raise NoQmxFolder(f"QMX_HOME names {root}, which is not a folder")
        return _opened(root)
    pointed = _pointed()
    if pointed is not None:
        return _opened(pointed)
    fixed = _fixed_drives() if drives is None else list(drives)
    for candidate in dict.fromkeys([_default_root(fixed), *(d / "QMX" for d in fixed)]):
        if _label(candidate) is not None:
            return _opened(candidate.resolve())
    raise NoQmxFolder(NOT_FOUND)


def _opened(root: Path) -> Layout:
    label = _label(root)
    if label is not None and label.format_version == TREE:
        return Layout(root)
    if label is None and not any(root.iterdir()):
        raise NoQmxFolder(f"no QMX folder at {root}: it has no {LABEL} (pass --create to make one)")
    if label is None or label.format_version == FLAT:
        raise NoQmxFolder(
            f"{root} is a QMX home in the old flat layout: move it into the folder tree with "
            f"python -m qmx_home layout {root}"
        )
    raise NoQmxFolder(
        f"{root} is a QMX folder of format {label.format_version}, which this QMX does not read"
    )


def _make(root: Path) -> None:
    try:
        if root.is_dir() and any(root.iterdir()):
            return
        for part in PARTS:
            (root / part).mkdir(parents=True, exist_ok=True)
        _write_label(root, Label.mint())
    except OSError as refused:
        raise NoQmxFolder(f"cannot make a QMX folder at {root}: {refused.strerror}") from None


def _write_label(root: Path, label: Label) -> None:
    staged = root / f"{LABEL}.new"
    staged.write_text(label.dump(), encoding="utf-8")
    staged.replace(root / LABEL)


def _pointed() -> Path | None:
    pointer = pointer_file()
    if pointer is None:
        return None
    try:
        text = pointer.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as unreadable:
        raise NoQmxFolder(_unreadable(pointer, unreadable)) from None
    named = _pointer_home(text)
    if named is None:
        raise NoQmxFolder(_unreadable(pointer, ValueError("it names no home")))
    root = Path(named)
    return root.resolve() if root.is_dir() else None


_HOME_LINE = re.compile(r"""^\s*home\s*=\s*(["'])(.*)\1\s*(?:#.*)?$""", re.MULTILINE)
_CONTROL = re.compile(r"[\x00-\x1f]")


def _pointer_home(text: str) -> str | None:
    """The pointer's `home`. A Windows path written in double quotes is not valid TOML (`\\Q`) or
    turns into control characters (`\\t`), so such a line is read as the path it spells."""
    try:
        named = tomllib.loads(text).get("home")
    except tomllib.TOMLDecodeError:
        named = None
    if isinstance(named, str) and named and not _CONTROL.search(named):
        return named
    found = _HOME_LINE.search(text)
    return found.group(2) if found and found.group(2) else None


def _unreadable(pointer: Path, why: Exception) -> str:
    return f"the pointer {pointer} cannot be read ({why}): write it again as UTF-8, or pass --home"


def _label(root: Path) -> Label | None:
    try:
        return Label.parse((root / LABEL).read_text(encoding="utf-8"))
    except OSError, ValueError:
        return None


def step_to_tree(root: Path) -> list[tuple[str, str]]:
    """Move a flat format 1 home into the tree (design 62 A3 and A5, guard 4) and label it format
    2. Every move is a rename inside the folder, so nothing is copied and nothing is taken away.
    Returns the moves made, as paths relative to `root`; a folder already in the tree returns none.

    Run it with QMX closed. A move the OS refuses (a file still open) stops the step; running it
    again finishes the same plan from where it stopped, because the plan is written to
    `layout-step.json` before the first move.
    """
    root = root.resolve()
    if not root.is_dir():
        raise LayoutRefused(f"no folder at {root}")
    label = _label(root)
    if label is not None and label.format_version == TREE:
        return []
    if label is not None and label.format_version != FLAT:
        raise LayoutRefused(f"{root} is a QMX folder of format {label.format_version}")
    journal = root / JOURNAL
    plan = _read_plan(journal) if journal.is_file() else _plan(root)
    if not journal.is_file():
        journal.write_text(json.dumps(plan, indent=1), encoding="utf-8")
    moved = [(source, target) for source, target in plan if _move(root, source, target)]
    _remove_if_empty(root / ".qmx")
    for part in PARTS:
        (root / part).mkdir(exist_ok=True)
    stepped = Label.mint() if label is None else label
    release = version("qmx-home")
    _write_label(root, Label(stepped.home_id, TREE, stepped.created_by, release))
    journal.unlink()
    return moved


def _remove_if_empty(folder: Path) -> None:
    """Remove `folder` only when it is empty: the step takes no file away."""
    with suppress(OSError):
        folder.rmdir()


def _plan(root: Path) -> list[tuple[str, str]]:
    top = {entry.name for entry in root.iterdir()} - {LABEL, JOURNAL}
    taken = sorted(top & {"data", "keys", "backups", "cache"})
    if taken:
        raise LayoutRefused(
            f"{root} already holds {', '.join(taken)}, which the tree uses; move it aside first"
        )
    plan = [(src, dst) for src, dst in FLAT_TO_TREE if (root / src).exists()]
    special = {src for src, _ in plan if "/" not in src} | {HOST_LOG[0]}
    rest = sorted(top - special)
    if ".qmx" in rest and {entry.name for entry in (root / ".qmx").iterdir()} <= {"vault.key"}:
        rest.remove(".qmx")
    plan += [(name, f"data/{name}") for name in rest]
    if (root / HOST_LOG[0]).exists():
        plan.append(HOST_LOG)
    return plan


def _read_plan(journal: Path) -> list[tuple[str, str]]:
    found: object = json.loads(journal.read_text(encoding="utf-8"))
    rows = cast("list[object]", found) if isinstance(found, list) else []
    plan: list[tuple[str, str]] = []
    for row in rows:
        pair = cast("list[object]", row) if isinstance(row, list) else []
        if len(pair) != 2 or not all(isinstance(part, str) for part in pair):
            raise LayoutRefused(f"{journal} is not a layout plan")
        plan.append((str(pair[0]), str(pair[1])))
    if not plan:
        raise LayoutRefused(f"{journal} is not a layout plan")
    return plan


def _move(root: Path, source: str, target: str) -> bool:
    """Rename `source` to `target`. False when an earlier run already moved it."""
    src, dst = root / source, root / target
    if not src.exists():
        if dst.exists():
            return False
        raise LayoutRefused(f"{source} is missing and was never moved to {target}")
    if dst.exists():
        raise LayoutRefused(f"both {source} and {target} exist; move one aside first")
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        src.rename(dst)
    except OSError as refused:
        raise LayoutRefused(
            f"cannot move {source} to {target}: {refused.strerror}; close QMX and run it again"
        ) from None
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
