"""The `[backup]` section as one plan: the quick undo's keep rule, the places he named, what he
leaves out and the drill (design 62 C2, Appendix D).

```toml
[backup.quick_undo]
hours = 48
days = 7

[[backup.targets]]
id = "usb"
kind = "folder"
path = 'E:\\QMX-backup'
every = "day"        # hour, day or week
at = "03:00"         # local time; a PC that was off copies at its next start
keep = { daily = 14, weekly = 8, monthly = 12 }
on = true
```

A target folder's copies go to `<path>/QMX-backup/<home_id>/`, or to `<path>/<home_id>/` when the
path he named is itself a `QMX-backup` folder. The mini apps' volume keys and `repository` belong
to the volume backup and the weekly snapshot and are left alone (`APP_KEYS`). No target means only
the quick undo. The default second drive is only ever a `proposal`, never a target by itself.
"""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path, PurePath
from typing import Final, Literal, cast

from qmx_home import (
    Label,
    Layout,
    _fixed_drives,  # pyright: ignore[reportPrivateUsage] - the one drive list
)
from qmx_home.backup.repository import FolderRepository, Repository
from qmx_home.files import plain

type Every = Literal["hour", "day", "week"]
type TargetKind = Literal["folder"]

EVERY: Final[tuple[Every, ...]] = ("hour", "day", "week")
KINDS: Final[tuple[TargetKind, ...]] = ("folder",)
APP_KEYS: Final = frozenset(
    {"remote", "bucket", "node", "interval_seconds", "enabled", "repository"}
)
"""Keys of `[backup]` that are not this plan's: the mini apps' volume backup and the weekly
snapshot's repository."""
FOLDER: Final = "QMX-backup"
GIB: Final = 1 << 30
FREE_SHARE: Final = 10
"""A proposed second drive keeps at least a tenth of itself free after the first copy (L1)."""
NO_SECOND_DRIVE: Final = (
    "your work has no copy on another drive: name a USB disk or another drive as a backup place "
    "in Settings, Data and backups"
)
_ID: Final = re.compile(r"[A-Za-z0-9_-]{1,64}")
_AT: Final = re.compile(r"([01]\d|2[0-3]):([0-5]\d)")
TARGET_KEYS: Final = frozenset({"id", "kind", "path", "every", "at", "keep", "on"})


class PlanRefused(Exception):
    """A `[backup]` row this release cannot use. The message names the row and what to fix."""


@dataclass(frozen=True, slots=True)
class Keep:
    """How many of the newest hours, days, weeks and months that hold a copy keep their newest
    copy."""

    hours: int = 0
    days: int = 0
    weeks: int = 0
    months: int = 0


QUICK_KEEP: Final = Keep(hours=48, days=7)
TARGET_KEEP: Final = Keep(days=14, weeks=8, months=12)


@dataclass(frozen=True, slots=True)
class Target:
    id: str
    kind: TargetKind
    path: Path
    every: Every = "day"
    at: time = time(3, 0)
    keep: Keep = TARGET_KEEP
    on: bool = True


@dataclass(frozen=True, slots=True)
class Drill:
    every: str = "month"
    sample: int = 200


@dataclass(frozen=True, slots=True)
class Plan:
    quick_undo: Keep = QUICK_KEEP
    targets: tuple[Target, ...] = ()
    leave_out: tuple[str, ...] = ()
    """Globs relative to `data/` he leaves out of every copy."""
    drill: Drill = field(default_factory=Drill)


@dataclass(frozen=True, slots=True)
class Proposal:
    """The second drive QMX suggests. It is a target only once he accepts it."""

    path: Path
    line: str


def parse(section: Mapping[str, object], layout: Layout) -> Plan:
    """The plan in `section`, the `[backup]` table as read. Raises PlanRefused naming the first
    row it cannot use: an unknown kind, a duplicate id, a target inside the QMX folder, a bad
    `every`, `at` or keep count, or a key a row does not have."""
    quick = section.get("quick_undo", {})
    if not isinstance(quick, dict):
        raise PlanRefused("[backup.quick_undo] must be a table with hours and days")
    rows = section.get("targets", [])
    if not isinstance(rows, list):
        raise PlanRefused("[[backup.targets]] must be a list of tables, one per backup place")
    targets: list[Target] = []
    for number, row in enumerate(cast("list[object]", rows), 1):
        target = _target(number, row, layout)
        if any(seen.id == target.id for seen in targets):
            raise PlanRefused(f"backup place {number}: the id {target.id!r} is used twice")
        targets.append(target)
    return Plan(
        quick_undo=_keep(
            "[backup.quick_undo]", cast("dict[str, object]", quick), {"hours", "days"}, QUICK_KEEP
        ),
        targets=tuple(targets),
        leave_out=_leave_out(section.get("leave_out", [])),
        drill=_drill(section.get("drill", {})),
    )


def _target(number: int, row: object, layout: Layout) -> Target:
    if not isinstance(row, dict):
        raise PlanRefused(f"backup place {number} is not a table")
    fields = cast("dict[str, object]", row)
    named = f"backup place {number}"
    unknown = sorted(set(fields) - TARGET_KEYS)
    if unknown:
        raise PlanRefused(f"{named} has {', '.join(unknown)}, which a backup place does not have")
    ident = fields.get("id")
    if not isinstance(ident, str) or not _ID.fullmatch(ident):
        raise PlanRefused(f"{named} needs an id of letters, digits, - and _")
    named = f"backup place {ident!r}"
    kind = fields.get("kind", "folder")
    if kind not in KINDS:
        raise PlanRefused(f"{named}: the kind {kind!r} is not one QMX knows; use folder")
    path = fields.get("path")
    if not isinstance(path, str) or not path.strip() or not PurePath(path).is_absolute():
        raise PlanRefused(f"{named} needs a full folder path, such as E:\\QMX-backup")
    where = Path(path)
    if _inside(where, layout.root):
        raise PlanRefused(
            f"{named}: {path} is inside the QMX folder {layout.root}, so a copy there is lost "
            "with the folder; name a folder on another drive"
        )
    every = fields.get("every", "day")
    if every not in EVERY:
        raise PlanRefused(f"{named}: every must be hour, day or week, not {every!r}")
    at = fields.get("at", "03:00")
    found = _AT.fullmatch(at) if isinstance(at, str) else None
    if found is None:
        raise PlanRefused(f"{named}: at must be a time such as 03:00, not {at!r}")
    on = fields.get("on", True)
    if not isinstance(on, bool):
        raise PlanRefused(f"{named}: on must be true or false")
    keep = fields.get("keep", {})
    if not isinstance(keep, dict):
        raise PlanRefused(f"{named}: keep must be a table such as {{ daily = 14 }}")
    return Target(
        ident,
        kind,
        where,
        every,
        time(int(found.group(1)), int(found.group(2))),
        _keep(named, cast("dict[str, object]", keep), {"daily", "weekly", "monthly"}, TARGET_KEEP),
        on,
    )


_KEEP_FIELDS: Final = {
    "hours": "hours",
    "days": "days",
    "daily": "days",
    "weekly": "weeks",
    "monthly": "months",
}


def _keep(named: str, table: Mapping[str, object], allowed: set[str], default: Keep) -> Keep:
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise PlanRefused(
            f"{named}: keep has {', '.join(unknown)}; use {', '.join(sorted(allowed))}"
        )
    counts = {
        "hours": default.hours,
        "days": default.days,
        "weeks": default.weeks,
        "months": default.months,
    }
    for key, value in table.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise PlanRefused(f"{named}: {key} must be a whole number of copies, not {value!r}")
        counts[_KEEP_FIELDS[key]] = value
    return Keep(**counts)


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


def _drill(value: object) -> Drill:
    if not isinstance(value, dict):
        raise PlanRefused("[backup.drill] must be a table with every and sample")
    table = cast("dict[str, object]", value)
    every, sample = table.get("every", "month"), table.get("sample", 200)
    if every not in ("week", "month"):
        raise PlanRefused(f"[backup.drill] every must be week or month, not {every!r}")
    if not isinstance(sample, int) or isinstance(sample, bool) or sample < 0:
        raise PlanRefused(f"[backup.drill] sample must be a whole number of files, not {sample!r}")
    return Drill(str(every), sample)


def target_root(path: Path, home_id: str) -> Path:
    """Where one folder's copies go in the place he named."""
    return path / home_id if path.name.casefold() == FOLDER.casefold() else path / FOLDER / home_id


def repository_of(target: Target, layout: Layout) -> Repository:
    """The place a target row names, for this folder."""
    return FolderRepository(target_root(target.path, _home_id(layout)))


def source_of(document: Mapping[str, object]) -> Repository:
    """The place a card's `source` names: `{"kind": "folder", "path": ..., "home_id": ...}`.
    `path` is the folder he named or a folder's own place in it; without `home_id` the place
    must hold exactly one QMX folder's copies. Raises PlanRefused naming what is missing."""
    kind, path = document.get("kind"), document.get("path")
    if kind not in KINDS:
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


def same_drive(target: Target, layout: Layout) -> bool:
    """Whether a target sits on the QMX folder's own drive, where it does not survive the disk."""
    return _drive(target.path) == _drive(layout.root)


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
        "Settings, Data and backups, or name a USB disk instead",
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
