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
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path, PureWindowsPath
from typing import Final, Literal, cast

from qmx_home.stores import STORES

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
TAKEN: Final = frozenset({"data", "keys", "backups", "cache"})
"""The parts a flat home may not already hold. Its own `logs/` is the exception: it moves to
`data/logs` before the tree's `logs/` is made."""
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
FLAT_MARKERS: Final = (
    "control.db",
    "runs.db",
    "claude-relayed",
    "vault/pairing-key",
    "vault/control-token",
)
"""What only QMX writes at a flat home's top: a PC host's stores and relayed Claude home (a
folder), a server setup's pairing key and control token (files). Bare folder names such as `.qmx`
or `vault` are not markers, because a user profile or a notes vault holds them too. An unlabelled
folder holding none of these, at its top or where a stopped layout step moved them, is not a QMX
folder, and nothing in it is ever moved. The step's own `layout-step.json` is not a marker on its
own: a foreign file of that name must not be able to start a move."""
MARKER_FOLDERS: Final = frozenset({"claude-relayed"})
PROFILE_FILE: Final = "NTUSER.DAT"
"""The registry hive at the top of every Windows user profile."""


type NotOpened = Literal["missing", "old", "refused"]
"""Why no folder opened: none was found (`missing`), the folder holds his old flat data (`old`),
or a folder was found and refused (`refused`), where his data may sit, so the first start must
never offer to make a second folder beside it (ruling 141)."""


class NoQmxFolder(Exception):
    """No QMX folder could be found or made. The message is the one line a command prints;
    `folder` is the folder the line is about, when there is one."""

    def __init__(self, line: str, kind: NotOpened = "refused", folder: Path | None = None) -> None:
        super().__init__(line)
        self.kind: NotOpened = kind
        self.folder = folder


class LayoutRefused(Exception):
    """The layout step cannot move this folder. The message names what is in the way."""


KNOWN_KEYS: Final = frozenset(
    {"format", "format_version", "home_id", "created_by", "last_written_by", "min_reader", "stores"}
)


@dataclass(frozen=True, slots=True)
class Label:
    """The label at the top of a QMX folder (design 62 B1).

    `min_reader` is the oldest folder format whose code may still open it; absent, it is the
    format itself. `stores` is the `[stores]` table as read: the truth for stores of plain files
    and a cache of each SQLite file's own marks. `extra` holds every top-level key this release
    does not know, so a rewrite keeps what a newer release added (B2 rule 3).
    """

    home_id: str
    format_version: int
    created_by: str
    last_written_by: str
    min_reader: int | None = None
    stores: Mapping[str, object] = field(default_factory=dict[str, object])
    extra: Mapping[str, object] = field(default_factory=dict[str, object])

    @classmethod
    def mint(cls, format_version: int = TREE) -> Label:
        release = version("qmx-home")
        files = {
            store.name: {"version": store.release.version, "min_reader": store.release.min_reader}
            for store in STORES.values()
            if store.kind == "files"
        }
        return cls(str(uuid.uuid7()), format_version, release, release, stores=files)

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
                floor = fields.get("min_reader")
                stores = fields.get("stores", {})
                return cls(
                    home_id,
                    format_version,
                    created_by,
                    last_written_by,
                    floor if isinstance(floor, int) else None,
                    cast("dict[str, object]", stores) if isinstance(stores, dict) else {},
                    {key: value for key, value in fields.items() if key not in KNOWN_KEYS},
                )
            case _:
                raise ValueError("not a qmx-home label")

    @property
    def reader_floor(self) -> int:
        """The oldest folder format whose code may open this folder."""
        return self.format_version if self.min_reader is None else self.min_reader

    def dump(self) -> str:
        lines = [
            f'format = "{FORMAT}"',
            f"format_version = {self.format_version}",
            f'home_id = "{self.home_id}"',
            f'created_by = "{self.created_by}"',
            f'last_written_by = "{self.last_written_by}"',
        ]
        if self.min_reader is not None:
            lines.append(f"min_reader = {self.min_reader}")
        lines += [f"{_toml_key(key)} = {_toml_value(value)}" for key, value in self.extra.items()]
        if self.stores:
            lines += ["", "[stores]"]
            lines += [
                f"{_toml_key(key)} = {_toml_value(value)}" for key, value in self.stores.items()
            ]
        return "\n".join(lines) + "\n"


_BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")


def _toml_string(text: str) -> str:
    """A TOML basic string: JSON's escapes are TOML's, and TOML also escapes DEL."""
    return json.dumps(text).replace("\x7f", "\\u007f")


def _toml_key(key: str) -> str:
    return key if _BARE_KEY.fullmatch(key) else _toml_string(key)


def _toml_value(value: object) -> str:
    """One TOML value on one line: tables become inline tables, so any value a label read can be
    written back."""
    match value:
        case bool():
            return "true" if value else "false"
        case int():
            return str(value)
        case float():
            return {"inf": "inf", "-inf": "-inf", "nan": "nan"}.get(repr(value), repr(value))
        case str():
            return _toml_string(value)
        case dict():
            pairs = cast("dict[str, object]", value).items()
            return "{ " + ", ".join(f"{_toml_key(k)} = {_toml_value(v)}" for k, v in pairs) + " }"
        case list():
            return "[" + ", ".join(_toml_value(item) for item in cast("list[object]", value)) + "]"
        case _:
            isoformat = getattr(value, "isoformat", None)
            return str(isoformat()) if callable(isoformat) else _toml_string(str(value))


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
        ancestor = _labelled_ancestor(root)
        if ancestor is not None:
            raise NoQmxFolder(_nested(root, ancestor), folder=root)
        if create:
            _make(root)
        if not root.is_dir():
            raise NoQmxFolder(f"no QMX folder at {root}", "missing", root)
        return _opened(root)
    named = os.environ.get("QMX_HOME")
    if named:
        root = Path(named).resolve()
        if not root.is_dir():
            raise NoQmxFolder(f"QMX_HOME names {root}, which is not a folder", folder=root)
        return _opened(root)
    pointed = _pointed()
    if pointed is not None:
        return _opened(pointed)
    fixed = _fixed_drives() if drives is None else list(drives)
    for candidate in dict.fromkeys([_default_root(fixed), *(d / "QMX" for d in fixed)]):
        if _label(candidate) is not None:
            return _opened(candidate.resolve())
    raise NoQmxFolder(NOT_FOUND, "missing")


def _opened(root: Path) -> Layout:
    label = _label(root)
    ancestor = _labelled_ancestor(root)
    if ancestor is not None:
        raise NoQmxFolder(_nested(root, ancestor), folder=root)
    if label is not None and opens(label):
        return Layout(root)
    if label is not None and label.format_version > TREE:
        raise NoQmxFolder(
            f"{root} was written by QMX {label.last_written_by} (folder format "
            f"{label.format_version}). This QMX reads folder format {TREE}, and this folder "
            f"needs a QMX that reads format {label.reader_floor} or newer. Install that QMX, or "
            f"restore the copy taken before the upgrade from {root / 'backups'}",
            folder=root,
        )
    if label is None and not any(root.iterdir()):
        raise NoQmxFolder(
            f"no QMX folder at {root}: it has no {LABEL} (pass --create to make one)",
            "missing",
            root,
        )
    refused = _refusal(root, label) if label is None or label.format_version == FLAT else None
    if refused is not None:
        raise NoQmxFolder(refused, folder=root)
    if label is None or label.format_version == FLAT:
        raise NoQmxFolder(old_flat(root), "old", root)
    raise NoQmxFolder(
        f"{root} is a QMX folder of format {label.format_version}, which this QMX does not read",
        folder=root,
    )


def old_flat(root: Path) -> str:
    """What every command says of an old flat home. On This PC that is his old data, which only
    the first start's bring-in reads, never changing it; the layout step would rearrange it in
    place, so it is not offered. A server's own setup, update and repair run the layout step by
    path."""
    return (
        f"{root} holds QMX data in the old flat layout. QMX does not open it and never changes "
        "it. On This PC, bring it into a new QMX folder with the first start: python -m qmx_host "
        f"bring-in --home <new QMX folder> --old {root}. A server's folder is moved into the "
        "tree by qmx-recover repair"
    )


def opens(label: Label) -> bool:
    """Whether this release opens a folder with this label (B2 for the folder): its own format,
    or a newer one whose `min_reader` this release still meets."""
    return label.format_version == TREE or (
        label.format_version > TREE and label.reader_floor <= TREE
    )


def _make(root: Path) -> None:
    try:
        if root.is_dir() and any(root.iterdir()):
            return
        for part in PARTS:
            (root / part).mkdir(parents=True, exist_ok=True)
        _write_label(root, Label.mint())
    except OSError as refused:
        raise NoQmxFolder(
            f"cannot make a QMX folder at {root}: {refused.strerror}", folder=root
        ) from None


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
    An empty folder is labelled with its five parts. Refused untouched, whatever they hold: a
    folder inside a labelled QMX folder, a drive's root, the user's profile, a folder holding
    `NTUSER.DAT` or a labelled QMX folder, and an unlabelled folder holding none of
    `FLAT_MARKERS`. A resumed plan may only hold moves `_plan` itself writes.

    Run it with QMX closed. A move the OS refuses (a file still open) stops the step; running it
    again finishes the same plan from where it stopped, because the plan is written to
    `layout-step.json` before the first move.
    """
    root = root.resolve()
    if not root.is_dir():
        raise LayoutRefused(f"no folder at {root}")
    label = _label(root)
    journal = root / JOURNAL
    ancestor = _labelled_ancestor(root)
    if ancestor is not None:
        raise LayoutRefused(f"{_nested(root, ancestor)}; nothing in it was moved")
    if label is not None and opens(label):
        journal.unlink(missing_ok=True)
        return []
    if label is not None and label.format_version != FLAT:
        raise LayoutRefused(f"{root} is a QMX folder of format {label.format_version}")
    refused = _refusal(root, label)
    if refused is not None:
        raise LayoutRefused(f"{refused}; nothing in it was moved")
    plan = _read_plan(root, journal) if journal.is_file() else _plan(root)
    if not journal.is_file():
        journal.write_text(json.dumps(plan, indent=1), encoding="utf-8")
    _copy_before_layout(root)
    moved = [(source, target) for source, target in plan if _move(root, source, target)]
    _remove_if_empty(root / ".qmx")
    for part in PARTS:
        (root / part).mkdir(exist_ok=True)
    stepped = Label.mint() if label is None else label
    release = version("qmx-home")
    _write_label(root, Label(stepped.home_id, TREE, stepped.created_by, release))
    journal.unlink()
    return moved


def _copy_before_layout(root: Path) -> None:
    """The pre-change copy of the layout step (B3, guard 4): the flat home's SQLite stores, its
    settings and the step's plan, into `backups/` before the first move. A stopped step whose
    copy the backup log records as complete is not copied again; a copy cut short is made again
    beside it. A home with no store has nothing to copy."""
    from qmx_home.versions import (  # noqa: PLC0415 (versions imports this module)
        SnapshotFailed,
        completed_copies,
        snapshot,
    )

    if completed_copies(Layout(root), "layout"):
        return
    stores = [root / store.path for store in STORES.values() if store.kind == "sqlite"]
    if not any(store.is_file() for store in stores):
        return
    try:
        files = [*stores, root / "settings.toml", root / JOURNAL]
        snapshot(Layout(root), "layout", FLAT, TREE, files, closed=True)
    except SnapshotFailed as failed:
        raise LayoutRefused(
            f"the copy taken before the move could not be made: {failed}; nothing was moved"
        ) from None


def _refusal(root: Path, label: Label | None) -> str | None:
    """Why the layout step must leave `root` alone, or None when it is a whole flat QMX home or
    a folder with nothing to move. `resolve` and `step_to_tree` both ask this one gate, so the
    resolver never sends him to a step that would move a folder the gate refuses."""
    kept_out = _kept_out(root)
    if kept_out is not None:
        return kept_out
    if label is None and not _nothing_to_move(root) and not _flat_home(root):
        return _not_qmx(root)
    held = next((entry for entry in root.iterdir() if entry.is_dir() and _qmx_folder(entry)), None)
    if held is not None:
        return (
            f"{root} holds the QMX folder {held}, which the layout step would move; move it "
            f"out of {root} first"
        )
    return None


def _qmx_folder(folder: Path) -> bool:
    """Whether `folder` is a QMX folder for the nesting checks: it holds a label file, whatever
    its content, or the plan of a layout step that stopped before writing the label."""
    return (folder / LABEL).is_file() or (folder / JOURNAL).is_file()


def _labelled_ancestor(root: Path) -> Path | None:
    """The nearest QMX folder above `root`: `root` is then a part of it (its `data/`,
    `cache/run`, a backup), never a home of its own."""
    return next((above for above in root.parents if _qmx_folder(above)), None)


def _nested(root: Path, ancestor: Path) -> str:
    if not (ancestor / LABEL).is_file():
        return (
            f"{root} is inside the QMX folder {ancestor}, whose layout step stopped; run "
            f"python -m qmx_home layout {ancestor} again"
        )
    return f"{root} is inside the QMX folder {ancestor}; pass {ancestor}"


def _flat_home(root: Path) -> bool:
    """Whether `root` holds a flat home's own files, at its top or where a stopped layout step
    moved them (`data/`, or `keys/` for the control token)."""
    for marker in FLAT_MARKERS:
        moved = [target for source, target in FLAT_TO_TREE if source == marker]
        for place in (root / marker, root / "data" / marker, *(root / m for m in moved)):
            if place.is_dir() if marker in MARKER_FOLDERS else place.is_file():
                return True
    return False


def _nothing_to_move(root: Path) -> bool:
    """Whether `root` holds at most the tree's empty parts and this module's own files: a fresh
    folder, or one whose labelling stopped before the label was written."""
    ours = {*PARTS, JOURNAL, f"{LABEL}.new"}
    for entry in root.iterdir():
        if entry.name not in ours:
            return False
        if entry.name in PARTS and (not entry.is_dir() or any(entry.iterdir())):
            return False
    return True


def _profile() -> Path | None:
    """The user's profile folder, or None when the OS names none."""
    try:
        return Path.home().resolve()
    except RuntimeError, KeyError, OSError:
        return None


def _kept_out(root: Path) -> str | None:
    """Why `root` is never moved into the tree, marker or not: the refusal, or None."""
    if root.parent == root:
        why = "a drive's root"
    elif root == _profile():
        why = "your user profile"
    elif (root / PROFILE_FILE).exists():
        why = f"a user profile (it holds {PROFILE_FILE})"
    else:
        return None
    return f"{root} is not a QMX folder: it is {why}; pass the folder QMX made"


def _not_qmx(root: Path) -> str:
    return (
        f"{root} is not a QMX folder: it has no {LABEL} and none of a QMX home's own files; "
        "pass the folder QMX made, or --create with an empty one"
    )


def _remove_if_empty(folder: Path) -> None:
    """Remove `folder` only when it is empty: the step takes no file away."""
    with suppress(OSError):
        folder.rmdir()


def _own_backups(folder: Path) -> bool:
    """Whether `folder` holds nothing but the layout step's own copies and their log: what a
    step that stopped, or whose copy was refused, leaves in a flat home's `backups/`."""
    return folder.is_dir() and all(
        (entry.name == "backups.jsonl" and entry.is_file())
        or (entry.name.startswith("pre-layout-") and entry.is_dir())
        for entry in folder.iterdir()
    )


def _plan(root: Path) -> list[tuple[str, str]]:
    top = {entry.name for entry in root.iterdir()} - {LABEL, JOURNAL}
    if _own_backups(root / "backups"):
        top.discard("backups")
    taken = sorted(top & TAKEN)
    if taken:
        raise LayoutRefused(
            f"{root} already holds {', '.join(taken)}, which the tree uses; move it aside first"
        )
    plan = [(src, dst) for src, dst in FLAT_TO_TREE if (root / src).exists()]
    special = {src for src, _ in plan if "/" not in src} | {HOST_LOG[0]}
    rest = sorted(top - special)
    nested = root / ".qmx"
    if ".qmx" in rest and nested.is_dir() and {e.name for e in nested.iterdir()} <= {"vault.key"}:
        rest.remove(".qmx")
    plan += [(name, f"data/{name}") for name in rest]
    if (root / HOST_LOG[0]).exists():
        plan.append(HOST_LOG)
    return plan


def _read_plan(root: Path, journal: Path) -> list[tuple[str, str]]:
    try:
        found: object = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, ValueError) as broken:
        raise LayoutRefused(
            f"{journal} cannot be read as a layout plan ({broken}); nothing has moved yet, so "
            "removing that file and running the step again is safe"
        ) from None
    if not isinstance(found, list):
        raise LayoutRefused(f"{journal} is not a layout plan")
    plan: list[tuple[str, str]] = []
    for row in cast("list[object]", found):
        pair = cast("list[object]", row) if isinstance(row, list) else []
        if len(pair) != 2 or not all(isinstance(part, str) for part in pair):
            raise LayoutRefused(f"{journal} is not a layout plan")
        source, target = str(pair[0]), str(pair[1])
        if not _plannable(source, target):
            raise LayoutRefused(
                f"{journal} names {source!r} to {target!r}, which is not a move the layout step "
                f"makes inside {root}; nothing was moved"
            )
        plan.append((source, target))
    return plan


def _plannable(source: str, target: str) -> bool:
    """Whether a plan row is one `_plan` itself could write: an A5 row, the host log, or one
    top-level name into `data/`. So a resumed plan stays inside the folder: no absolute path, no
    drive, no `..`, no backslash, and never a part of the tree or the label."""
    if (source, target) in FLAT_TO_TREE or (source, target) == HOST_LOG:
        return True
    return target == f"data/{source}" and _top_name(source)


def _top_name(name: str) -> bool:
    """Whether `name` is one entry at the folder's top that is none of the tree's parts, the
    label or the plan, compared the way the OS compares names: on Windows case does not count
    and a trailing dot or space is dropped, so `Keys` and `keys.` would name `keys/`."""
    windows = os.name == "nt"
    fold = str.casefold if windows else str
    if windows and name != name.rstrip(". "):
        return False
    if not name or fold(name) in {fold(n) for n in (".", "..", *TAKEN, LABEL, JOURNAL)}:
        return False
    return not any(mark in name for mark in ("/", "\\", ":")) and not PureWindowsPath(name).anchor


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
