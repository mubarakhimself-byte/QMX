"""The `[backup]` section as one plan: the main switch, what he leaves out, This PC's policy,
each storage's policy and QMX's upkeep (design 06 sections 4 and 5, Appendix D). The screen says
"Sync to my storage".

```toml
[backup]
on = true                          # off pauses every storage and deletes nothing
leave_out = []                     # his own globs under data/
rclone_path = ""                   # per machine; empty means PATH, then the pinned release

[backup.place.pc]                  # This PC, "Copies on this PC"
on = true
save = ["recipe", "content", "result", "prices"]
every = "1h"                       # when something changed
at = "03:00"                       # local time, read when every is a day or more
keep = { hours = 48, days = 7 }

[backup.place.<place id>]          # any other storage; absent means the defaults
save = ["recipe", "content", "result", "prices"]
every = "1d"
at = "03:00"
keep = { days = 14, weeks = 8, months = 12 }
floor = "auto"

[backup.upkeep]
drill_every = "1mo"
drill_sample = 200
```

The storages are the `[engine] placement.<name>` rows whose `can` holds `keep`, each with its
policy keyed by the row's stable `id`. A folder storage (`via = "folder"`) gets copies at
`<path>/QMX-backup/<home_id>/`. A policy whose row is gone is ignored. Keys this release does not
read (an old `repository`, the mini apps' old volume keys, `[[backup.targets]]`) are kept as
written and read by nothing.
"""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import time, timedelta
from pathlib import Path, PurePath
from typing import Final, cast

from qmx_home import (
    Label,
    Layout,
    _fixed_drives,  # pyright: ignore[reportPrivateUsage] - the one drive list
)
from qmx_home.backup.repository import FolderRepository, Repository
from qmx_home.classes import SENT, Class
from qmx_home.files import GIB, floor_gb, plain

PC: Final = "pc"
"""This PC's place id: always the first storage."""
FOLDER: Final = "QMX-backup"
FREE_SHARE: Final = 10
"""A proposed second drive keeps at least a tenth of itself free after the first copy (L1)."""
NO_SECOND_DRIVE: Final = (
    "your work has no copy on another drive: connect a USB disk or another drive as a storage "
    "in Settings, Sync to my storage"
)
RETIRED: Final = frozenset(
    {
        "repository",
        "remote",
        "bucket",
        "node",
        "interval_seconds",
        "enabled",
        "quick_undo",
        "targets",
        "drill",
        "keys",
    }
)
"""Keys of `[backup]` from before this shape: kept as written, read by nothing, never refused."""
KEYS: Final = frozenset({"on", "leave_out", "rclone_path", "place", "upkeep"})
PC_KEYS: Final = frozenset({"on", "save", "every", "at", "keep"})
STORAGE_KEYS: Final = frozenset({"on", "save", "every", "at", "keep", "floor"})
KEEP_KEYS: Final = ("hours", "days", "weeks", "months")
UPKEEP: Final[Mapping[str, object]] = {
    "on": True,
    "every": "1mo",
    "repack_past": 0.05,
    "repack_per_run": "all",
    "safety": "24h",
    "check_slice": 12,
    "drill": True,
    "drill_every": "1mo",
    "drill_sample": 200,
    "before_update_wait": "10m",
}
"""QMX's own upkeep, per storage, This PC included (design 06 section 6)."""
_SPAN: Final = re.compile(r"(\d+)(s|m|min|h|d|w|mo)")
_UNIT: Final[Mapping[str, timedelta]] = {
    "s": timedelta(seconds=1),
    "m": timedelta(minutes=1),
    "min": timedelta(minutes=1),
    "h": timedelta(hours=1),
    "d": timedelta(days=1),
    "w": timedelta(weeks=1),
    "mo": timedelta(days=30),
}
_AT: Final = re.compile(r"([01]\d|2[0-3]):([0-5]\d)")
_ID: Final = re.compile(r"[A-Za-z0-9_-]{1,64}")


class PlanRefused(Exception):
    """A `[backup]` or storage row this release cannot use. The message names it and the fix."""


@dataclass(frozen=True, slots=True)
class Keep:
    """How many of the newest hours, days, weeks and months that hold a copy keep their newest
    copy."""

    hours: int = 0
    days: int = 0
    weeks: int = 0
    months: int = 0


PC_KEEP: Final = Keep(hours=48, days=7)
STORAGE_KEEP: Final = Keep(days=14, weeks=8, months=12)


def span(text: str) -> timedelta:
    """A span as Settings writes it: a whole number and `s`, `m` (minutes), `h`, `d`, `w` or
    `mo` (30 days), such as `10m`, `2h`, `1d` or `1mo`. Raises ValueError for any other text."""
    found = _SPAN.fullmatch(text)
    if found is None or int(found.group(1)) == 0:
        raise ValueError(text)
    return int(found.group(1)) * _UNIT[found.group(2)]


@dataclass(frozen=True, slots=True)
class Policy:
    """When one storage gets a copy, of what, and how many it keeps."""

    on: bool = True
    save: tuple[Class, ...] = SENT
    every: str = "1d"
    at: time = time(3, 0)
    keep: Keep = STORAGE_KEEP
    floor: float | None = None
    """GB a storage that reports free space keeps free; None is `auto`."""

    @property
    def interval(self) -> timedelta:
        return span(self.every)


PC_POLICY: Final = Policy(every="1h", keep=PC_KEEP)
STORAGE_POLICY: Final = Policy()


@dataclass(frozen=True, slots=True)
class Storage:
    """A place that can keep: an `[engine]` row whose `can` holds `keep`."""

    id: str
    name: str
    via: str
    """How copies are kept there: `folder`, or `rclone` once its adapter is in."""
    path: Path | None
    policy: Policy = STORAGE_POLICY


@dataclass(frozen=True, slots=True)
class Upkeep:
    drill: bool = True
    drill_every: str = "1mo"
    drill_sample: int = 200


@dataclass(frozen=True, slots=True)
class Plan:
    on: bool = True
    """The main switch: off pauses every storage and deletes nothing."""
    leave_out: tuple[str, ...] = ()
    """Globs relative to `data/` he leaves out of every copy."""
    rclone_path: str = ""
    pc: Policy = PC_POLICY
    storages: tuple[Storage, ...] = ()
    """Every place that can keep, in `[engine]`'s order."""
    upkeep: Upkeep = field(default_factory=Upkeep)
    floor_gb: float | None = None
    """`[engine] disk.floor_gb`, which the one local floor reads."""

    @property
    def folders(self) -> tuple[Storage, ...]:
        """The storages this release copies to: folders on a drive."""
        return tuple(s for s in self.storages if s.via == "folder" and s.path is not None)


@dataclass(frozen=True, slots=True)
class Proposal:
    """The second drive QMX suggests. It is a storage only once he accepts it."""

    path: Path
    line: str


def parse(
    section: Mapping[str, object], layout: Layout, engine: Mapping[str, object] | None = None
) -> Plan:
    """The plan in `section`, the `[backup]` table as read, with the storages of `engine`, the
    `[engine]` table. Raises PlanRefused naming the first key or row it cannot use."""
    unknown = sorted(set(section) - KEYS - RETIRED)
    if unknown:
        raise PlanRefused(
            f"[backup] has {', '.join(unknown)}, which QMX does not know; use "
            f"{', '.join(sorted(KEYS))}"
        )
    on = _bool("[backup] on", section.get("on", True))
    rclone_path = section.get("rclone_path", "")
    if not isinstance(rclone_path, str):
        raise PlanRefused("[backup] rclone_path must be the path of rclone, or empty")
    places = _table("[backup.place]", section.get("place", {}))
    pc = _policy(PC, _table("[backup.place.pc]", places.get(PC, {})), PC_POLICY, PC_KEYS)
    rows = engine or {}
    storages = tuple(
        replace(
            storage,
            policy=_policy(
                storage.id,
                _table(f"[backup.place.{storage.id}]", places.get(storage.id, {})),
                STORAGE_POLICY,
                STORAGE_KEYS,
            ),
        )
        for storage in _storages(rows, layout)
    )
    return Plan(
        on,
        _leave_out(section.get("leave_out", [])),
        rclone_path,
        pc,
        storages,
        _upkeep(_table("[backup.upkeep]", section.get("upkeep", {}))),
        floor_gb(rows),
    )


def defaults(section: Mapping[str, object], engine: Mapping[str, object]) -> dict[str, object]:
    """`[backup]` with every default filled in, a policy for This PC and for each storage of
    `engine` included: what the screen reads. Nothing stores this view."""
    places = _loose(section.get("place"))
    filled: dict[str, object] = {
        **section,
        "on": section.get("on", True),
        "leave_out": section.get("leave_out", []),
        "rclone_path": section.get("rclone_path", ""),
        "upkeep": {**UPKEEP, **_loose(section.get("upkeep"))},
    }
    shown: dict[str, object] = {PC: {**_document(PC_POLICY, pc=True), **_loose(places.get(PC))}}
    for place_id in _keeping_ids(engine):
        shown[place_id] = {**_document(STORAGE_POLICY, pc=False), **_loose(places.get(place_id))}
    for place_id, policy in places.items():
        shown.setdefault(place_id, policy)
    filled["place"] = shown
    return filled


def orphans_dropped(
    section: Mapping[str, object], engine: Mapping[str, object]
) -> dict[str, object]:
    """`[backup]` less each storage policy whose `[engine]` row is gone."""
    places = section.get("place")
    if not isinstance(places, dict):
        return dict(section)
    alive = {PC, *_keeping_ids(engine)}
    kept = {k: v for k, v in cast("dict[str, object]", places).items() if k in alive}
    if kept:
        return {**section, "place": kept}
    return {k: v for k, v in section.items() if k != "place"}


def _keeping_ids(engine: Mapping[str, object]) -> list[str]:
    return [place_id for _, place_id, row in _rows(engine) if "keep" in can_of(row)]


def _rows(engine: Mapping[str, object]) -> list[tuple[str, str, Mapping[str, object]]]:
    """Each `[engine] placement.<name>` row as (name, stable id, fields), in its order."""
    placement = engine.get("placement")
    if not isinstance(placement, dict):
        return []
    found: list[tuple[str, str, Mapping[str, object]]] = []
    for name, row in cast("dict[str, object]", placement).items():
        if name == PC or not isinstance(row, dict):
            continue
        fields = cast("dict[str, object]", row)
        ident = fields.get("id")
        found.append((name, ident if isinstance(ident, str) and ident else name, fields))
    return found


def can_of(row: Mapping[str, object]) -> tuple[str, ...]:
    """What a place row can do; a row that says nothing can run, as every row before it did."""
    can = row.get("can", ["run"])
    if isinstance(can, str):
        return (can,)
    if isinstance(can, list | tuple):
        return tuple(str(one) for one in cast("Sequence[object]", can))
    return ("run",)


def _storages(engine: Mapping[str, object], layout: Layout) -> list[Storage]:
    storages: list[Storage] = []
    for name, ident, row in _rows(engine):
        if "keep" not in can_of(row):
            continue
        named = f"the storage {name!r}"
        if ident == PC or not _ID.fullmatch(ident):
            raise PlanRefused(f"{named} needs an id of letters, digits, - and _, other than pc")
        via = row.get("via", "folder")
        if not isinstance(via, str):
            raise PlanRefused(f"{named}: via must be folder or rclone")
        path: Path | None = None
        if via == "folder":
            given = row.get("path")
            if not isinstance(given, str) or not given.strip() or not PurePath(given).is_absolute():
                raise PlanRefused(f"{named} needs a full folder path, such as E:\\")
            path = Path(given)
            if _inside(path, layout.root):
                raise PlanRefused(
                    f"{named}: {given} is inside the QMX folder {layout.root}, so a copy there is "
                    "lost with the folder; pick a folder on another drive"
                )
        storages.append(Storage(ident, name, via, path))
    return storages


def _policy(
    place_id: str, table: Mapping[str, object], default: Policy, allowed: frozenset[str]
) -> Policy:
    named = f"[backup.place.{place_id}]"
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise PlanRefused(f"{named} has {', '.join(unknown)}; use {', '.join(sorted(allowed))}")
    save = table.get("save", list(default.save))
    if not isinstance(save, list) or any(one not in SENT for one in cast("list[object]", save)):
        raise PlanRefused(f"{named}: save lists classes from {', '.join(SENT)}")
    every = table.get("every", default.every)
    if not isinstance(every, str) or not _valid_span(every) or span(every) < timedelta(hours=1):
        raise PlanRefused(f"{named}: every is a span of an hour or more, such as 1h, 1d or 1w")
    at = table.get("at", default.at.strftime("%H:%M"))
    found = _AT.fullmatch(at) if isinstance(at, str) else None
    if found is None:
        raise PlanRefused(f"{named}: at must be a time such as 03:00, not {at!r}")
    floor = table.get("floor", "auto")
    if floor != "auto" and (
        not isinstance(floor, int | float) or isinstance(floor, bool) or floor < 0
    ):
        raise PlanRefused(f"{named}: floor is auto or a number of GB to keep free")
    return Policy(
        _bool(f"{named} on", table.get("on", default.on)),
        tuple(c for c in SENT if c in cast("list[str]", save)),
        every,
        time(int(found.group(1)), int(found.group(2))),
        _keep(named, _table(f"{named} keep", table.get("keep", {})), default.keep),
        None if floor == "auto" else float(cast("float", floor)),
    )


def _upkeep(table: Mapping[str, object]) -> Upkeep:
    unknown = sorted(set(table) - set(UPKEEP))
    if unknown:
        raise PlanRefused(
            f"[backup.upkeep] has {', '.join(unknown)}; use {', '.join(sorted(UPKEEP))}"
        )
    values = {**UPKEEP, **table}
    for key in ("every", "safety", "drill_every", "before_update_wait"):
        value = values[key]
        if not isinstance(value, str) or not _valid_span(value):
            raise PlanRefused(f"[backup.upkeep] {key} is a span such as 24h or 1mo")
    sample = values["drill_sample"]
    if not isinstance(sample, int) or isinstance(sample, bool) or sample < 0:
        raise PlanRefused("[backup.upkeep] drill_sample must be a whole number of files")
    return Upkeep(
        _bool("[backup.upkeep] drill", values["drill"]),
        cast("str", values["drill_every"]),
        sample,
    )


def _keep(named: str, table: Mapping[str, object], default: Keep) -> Keep:
    unknown = sorted(set(table) - set(KEEP_KEYS))
    if unknown:
        raise PlanRefused(f"{named}: keep has {', '.join(unknown)}; use {', '.join(KEEP_KEYS)}")
    counts = {key: int(getattr(default, key)) for key in KEEP_KEYS}
    for key, value in table.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise PlanRefused(f"{named}: {key} must be a whole number of copies, not {value!r}")
        counts[key] = value
    return Keep(**counts)


def _document(policy: Policy, *, pc: bool) -> dict[str, object]:
    shown: dict[str, object] = {
        "on": policy.on,
        "save": list(policy.save),
        "every": policy.every,
        "at": policy.at.strftime("%H:%M"),
        "keep": {key: getattr(policy.keep, key) for key in KEEP_KEYS if getattr(policy.keep, key)},
    }
    if not pc:
        shown["floor"] = "auto"
    return shown


def _valid_span(text: str) -> bool:
    try:
        span(text)
    except ValueError:
        return False
    return True


def _bool(named: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise PlanRefused(f"{named} must be true or false")
    return value


def _table(named: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise PlanRefused(f"{named} must be a table")
    return cast("dict[str, object]", value)


def _loose(value: object) -> dict[str, object]:
    return dict(cast("dict[str, object]", value)) if isinstance(value, dict) else {}


def _leave_out(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(g, str) for g in cast("list[object]", value)
    ):
        raise PlanRefused(
            "[backup] leave_out must be a list of paths inside data/, such as exports/**"
        )
    globs = tuple(cast("list[str]", value))
    for glob in globs:
        if not glob or PurePath(glob).is_absolute() or ".." in PurePath(glob).parts or "\\" in glob:
            raise PlanRefused(f"[backup] leave_out: {glob!r} is not a path inside data/")
    return globs


def storage_root(path: Path, home_id: str) -> Path:
    """Where one folder's copies go in a folder storage."""
    return path / home_id if path.name.casefold() == FOLDER.casefold() else path / FOLDER / home_id


def repository_of(storage: Storage, layout: Layout) -> Repository:
    """The folder a folder storage names, for this QMX folder."""
    return FolderRepository(storage_root(cast("Path", storage.path), _home_id(layout)))


def source_of(document: Mapping[str, object]) -> Repository:
    """The place a card's `source` names: `{"kind": "folder", "path": ..., "home_id": ...}`.
    `path` is the folder he named or a folder's own place in it; without `home_id` the place
    must hold exactly one QMX folder's copies. Raises PlanRefused naming what is missing."""
    kind, path = document.get("kind"), document.get("path")
    if kind != "folder":
        raise PlanRefused(f"a backup source of kind {kind!r} is not one QMX knows; use folder")
    if not isinstance(path, str) or not PurePath(path).is_absolute():
        raise PlanRefused("a backup source needs the full path of the folder that holds copies")
    root = Path(path)
    if (root / "snapshots").is_dir():
        return FolderRepository(root)
    home_id = document.get("home_id")
    holder = root if root.name.casefold() == FOLDER.casefold() else root / FOLDER
    if isinstance(home_id, str) and _ID.fullmatch(home_id):
        return FolderRepository(holder / home_id)
    homes = (
        sorted(p.name for p in holder.iterdir() if (p / "snapshots").is_dir())
        if holder.is_dir()
        else []
    )
    if len(homes) == 1:
        return FolderRepository(holder / homes[0])
    if not homes:
        raise PlanRefused(f"{plain(root)} holds no QMX copies")
    raise PlanRefused(
        f"{plain(holder)} holds copies of {len(homes)} QMX folders ({', '.join(homes)}); pick one"
    )


def same_drive(storage: Storage, layout: Layout) -> bool:
    """Whether a folder storage sits on the QMX folder's own drive, where it does not survive the
    disk."""
    return storage.path is not None and _drive(storage.path) == _drive(layout.root)


def proposal(
    layout: Layout,
    drives: Sequence[Path] | None = None,
    free: Callable[[Path], tuple[int, int]] | None = None,
) -> Proposal | None:
    """The second drive he may accept: the fixed drive with the most free room that is not the
    folder's own, as `<drive>:\\QMX-backup`, when the first copy leaves it at least the larger of
    1 GiB and a tenth of the drive free (L1). None when no drive fits; `NO_SECOND_DRIVE` is then
    the line to show. `free(drive)` is the drive's total and free bytes."""
    usage = free or _usage
    own = _drive(layout.root)
    candidates: list[tuple[int, int, Path]] = []
    for drive in _fixed_drives() if drives is None else drives:
        if _drive(drive) == own:
            continue
        try:
            total, room = usage(drive)
        except OSError:
            continue
        candidates.append((room, total, drive))
    if not candidates:
        return None
    room, total, drive = max(candidates, key=lambda found: found[0])
    need = _data_bytes(layout.data)
    if room - need < max(GIB, total // FREE_SHARE):
        return None
    path = Path(drive) / FOLDER
    return Proposal(
        path,
        f"QMX proposes {plain(path)} on another drive for a daily copy of your work; accept it in "
        "Settings, Sync to my storage, or connect a USB disk instead",
    )


def _usage(drive: Path) -> tuple[int, int]:
    found = shutil.disk_usage(drive)
    return found.total, found.free


def _data_bytes(data: Path) -> int:
    total = 0
    pending = [str(data)]
    while pending:
        try:
            entries = list(os.scandir(pending.pop()))
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink() or entry.is_junction():
                continue
            if entry.is_dir():
                pending.append(entry.path)
            elif entry.is_file():
                total += entry.stat().st_size
    return total


def _home_id(layout: Layout) -> str:
    return Label.parse(layout.label.read_text(encoding="utf-8")).home_id


def _drive(path: Path) -> str:
    """The drive letter on Windows; elsewhere the device of the nearest folder that exists."""
    full = os.path.abspath(path)
    letter = os.path.splitdrive(full)[0]
    if letter:
        return os.path.normcase(letter)
    existing = next((p for p in (Path(full), *Path(full).parents) if p.exists()), Path("/"))
    return str(existing.stat().st_dev)


def _inside(path: Path, folder: Path) -> bool:
    """Whether `path` is `folder` or inside it, links and junctions followed on both sides."""
    inner = os.path.normcase(os.path.realpath(path))
    outer = os.path.normcase(os.path.realpath(folder))
    return inner == outer or inner.startswith(outer.rstrip("\\/") + os.sep)
