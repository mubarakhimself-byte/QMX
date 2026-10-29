"""Versions: every store opens, upgrades after a copy, or refuses by name (design 62 B2 to B4,
Library AD-35).

`open_sqlite` is the gate each SQLite store's opener passes before it reads or writes the file:

1. The same version opens.
2. An older store is copied into the folder's `backups/` first (`snapshot`), then moved forward
   one step at a time, each step in its own transaction under SQLite's write lock. A step that
   fails rolls back, the store stays at its last good version, and the backup log records the
   step as an incident.
3. A newer store whose `min_reader` this release meets opens as it is, never marked down.
4. A newer store whose `min_reader` this release does not meet is refused by name and never
   written. The Library and the price data open read-only instead (`too_new`).
5. An index never refuses; its opener rebuilds it (`index_state`).

A file that is not QMX's (not SQLite, another program's `application_id`, or none of the store's
own tables) is refused by name and never written. `check_open` reads a whole folder the same way,
changes no store, and rewrites only the label's `[stores]` cache.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import time
import tomllib
from collections.abc import Mapping, Sequence
from contextlib import closing, suppress
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Final, Literal, cast

from qmx_home import LABEL, TREE, Label, Layout, restore_hint
from qmx_home.files import MIN_FLOOR, local_floor
from qmx_home.stores import APPLICATION_ID, STORES, Store, Version

FLOOR_BYTES: Final = MIN_FLOOR
"""The least free space any local copy leaves on its drive; the local floor (`local_floor`) is
never below it. A safety floor for the disk, not a limit on what he keeps."""
LOG: Final = "backups.jsonl"
"""The backup log in `backups/`: one line per pre-change copy and per failed upgrade step."""
UPGRADE_COPIES: Final = frozenset({"before-upgrade", "before-update"})
"""What a copy of the whole folder taken just before its stores upgrade says it was made for:
the local copy `serve` takes, and the sync before an update (design 06 section 7)."""
QUICK: Final = "quick"
"""This PC's copies, in `backups/`."""
SQLITE_HEADER: Final = b"SQLite format 3\x00"
BUSY_TIMEOUT_S: Final = 30.0


class StoreRefused(Exception):
    """This release must not open or upgrade a store. The message says why and what to do."""

    def __init__(self, store: str, message: str) -> None:
        super().__init__(message)
        self.store = store


class SnapshotFailed(Exception):
    """The pre-change copy could not be made. Nothing was changed and no partial copy is left."""


@dataclass(frozen=True, slots=True)
class Found:
    """What a store's file says it is."""

    version: Version
    marked: bool
    """It carries QMX's `application_id`, its `user_version` and its `min_reader` row."""


@dataclass(frozen=True, slots=True)
class Opened:
    """What `open_sqlite` found and did."""

    found: Version | None
    """The store before this open; None for a new, empty file."""
    applied: tuple[int, ...]
    """The versions the steps of this open moved it to, in order."""
    snapshot: Path | None
    """The pre-change copy taken before the first step."""
    newer: bool
    """Written by a newer release that still allows this one: opened as it is (rule 3)."""


type Action = Literal["new", "opens", "upgrades", "opens newer", "read-only", "refused", "rebuilds"]


@dataclass(frozen=True, slots=True)
class Verdict:
    store: str
    action: Action
    found: Version | None
    line: str
    """One line in plain words."""


@dataclass(frozen=True, slots=True)
class Opening:
    """`check_open`'s reading of one folder."""

    verdicts: tuple[Verdict, ...]
    label_written: bool
    """The label's `[stores]` table disagreed with a store's own file and was rewritten."""
    seconds: float

    @property
    def held_back(self) -> tuple[Verdict, ...]:
        """The stores refused or opened read-only."""
        return tuple(v for v in self.verdicts if v.action in ("refused", "read-only"))


def folder_of(path: Path) -> Layout | None:
    """The QMX folder whose `data/` holds `path`, or None when no labelled folder does (a test's
    bare home)."""
    resolved = path.resolve()
    for above in resolved.parents:
        if (above / LABEL).is_file():
            layout = Layout(above)
            return layout if resolved.is_relative_to(layout.data) else None
    return None


def open_sqlite(
    connection: sqlite3.Connection, name: str, steps: Sequence[Sequence[str]]
) -> Opened:
    """Bring one SQLite store to this release (B2) before its opener uses it. `connection` must be
    in autocommit mode (`isolation_level=None`). `steps[n]` moves the store from version n to
    n + 1, and there are exactly as many steps as this release's version of the store.

    The file is judged through a `mode=ro` connection of its own before `connection` reads it, so
    a store refused as too new or not QMX's is never checkpointed by the opener's connection when
    it closes (its pending `-wal` stays as it is). Only then is it switched to WAL (every QMX
    store runs in WAL; switching after a step that drops a table leaves SQLite unable to
    checkpoint on that connection). A store whose file held none of this store's tables is made
    at this release in one go; it has nothing to copy. An unmarked file of today's version is
    marked in place. Raises StoreRefused for a store too new, a file that is not QMX's, an upgrade
    whose copy cannot be made, and a step that fails.
    """
    store = STORES[name]
    if len(steps) != store.release.version:
        raise ValueError(f"{name} has {len(steps)} steps for version {store.release.version}")
    path = _file_of(connection)
    if path is not None and path.is_file() and path.stat().st_size > 0:
        with closing(_reader(path)) as reading:
            found = _judge(store, _found(reading, store, path), path)
    else:
        found = _judge(store, _found(connection, store, path), path)
    connection.execute("PRAGMA journal_mode = WAL").fetchall()
    if found is not None and found.version.version > store.release.version:
        return Opened(found.version, (), None, newer=True)
    if found is not None and found.marked and found.version.version == store.release.version:
        return Opened(found.version, (), None, newer=False)
    applied, copy = _forward(connection, store, path, steps, fresh=found is None)
    return Opened(None if found is None else found.version, tuple(applied), copy, newer=False)


def check_sqlite(connection: sqlite3.Connection, name: str) -> Version | None:
    """What a SQLite store's file holds, for a reader that never writes it. Raises StoreRefused
    for a store too new or a file that is not QMX's; None for a new, empty file."""
    store = STORES[name]
    path = _file_of(connection)
    found = _judge(store, _found(connection, store, path), path)
    return None if found is None else found.version


def too_new(path: Path, name: str) -> str | None:
    """Why a store of plain files must not be written: the refusal, or None when this release
    may write it. `path` is the store's folder or a file inside the QMX folder's `data/`; the
    label's `[stores]` entry is its version. Outside a labelled folder there is no label and the
    store is this release's."""
    store = STORES[name]
    layout = folder_of(path)
    if layout is None:
        return None
    label = _label_of(layout)
    if label is None or name not in label.stores:
        return None
    found = _entry(label.stores[name])
    if found is None:
        return _unreadable_entry(store, layout)
    if not _closed(store, found):
        return None
    return _too_new(store, found, layout)


type IndexState = Literal["current", "rebuild", "foreign"]


def index_state(connection: sqlite3.Connection, name: str) -> IndexState:
    """What an index file is (rule 5), read only: `current` (this release's, or new and empty, or
    written before indexes carried versions), `rebuild` (QMX's, of another version: drop it and
    build it again from the store's own files), or `foreign` (not SQLite, or another program's:
    move it aside, never delete it, then build a new one)."""
    store = STORES[name]
    try:
        app = _pragma(connection, "application_id")
        user = _pragma(connection, "user_version")
        tables = {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    except sqlite3.DatabaseError as broken:
        match getattr(broken, "sqlite_errorname", ""):
            case "SQLITE_NOTADB":
                return "foreign"
            case "SQLITE_CORRUPT":
                return "rebuild"
            case _:
                raise
    if app == APPLICATION_ID:
        return "current" if user == store.release.version else "rebuild"
    if app != 0 or (tables and (user != 0 or not tables & set(store.tables))):
        return "foreign"
    return "current" if not tables or store.release.version == 1 else "rebuild"


def index_file_state(path: Path, name: str) -> IndexState:
    """`index_state` of the index file at `path`, read through a `mode=ro` connection, so a file
    that is not QMX's is never checkpointed before it is moved aside. A missing or empty file is
    `current`: it is made new."""
    if not path.is_file() or path.stat().st_size == 0:
        return "current"
    with closing(_reader(path)) as reading:
        return index_state(reading, name)


def mark_index(connection: sqlite3.Connection, name: str) -> None:
    """Mark an index as this release's, writing only when it is not marked yet."""
    store = STORES[name]
    if _pragma(connection, "application_id") != APPLICATION_ID:
        connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
    if _pragma(connection, "user_version") != store.release.version:
        connection.execute(f"PRAGMA user_version = {store.release.version}")


def snapshot(
    layout: Layout,
    what: str,
    before: int | str,
    after: int | str,
    files: Sequence[Path],
    *,
    closed: bool = False,
) -> Path:
    """The pre-change copy (B3): every file of `files` that exists, under its own path below
    `backups/pre-<what>-<before>-<after>-<stamp>/`. A SQLite file is copied whole by `VACUUM INTO`
    through a reading connection, so a live store is copied as committed; anything else by a file
    copy. `closed` says no process has the stores open (the layout step): then every file is
    copied byte for byte, a SQLite file with its `-wal`, so no connection makes or removes a file
    beside a store about to move. Refuses before it starts when the copy would leave its drive
    below the local floor (`local_floor` of `[engine]`), and removes a copy that fails part way
    (a full disk included). Writes nothing outside `backups/`, and logs the copy's bytes and
    seconds in `backups/backups.jsonl`.

    One copy per upgrade (design 06 section 7): when this start already copied the whole folder
    for its upgrade (`upgrade_copied`) and that copy holds every file, no pre-change copy is made,
    the release is logged, and that copy's own folder among This PC's copies is returned."""
    started = time.monotonic()
    named = [*files, *(f.with_name(f"{f.name}-wal") for f in files)] if closed else files
    present = [file for file in named if file.is_file()]
    outside = [file for file in present if not file.resolve().is_relative_to(layout.root)]
    if outside:
        raise SnapshotFailed(f"{outside[0]} is outside the QMX folder {layout.root}")
    covering = None if closed else _upgrade_copy(layout, present)
    if covering is not None:
        log_line(
            layout,
            {
                "kind": "pre-change-released",
                "what": what,
                "from": before,
                "to": after,
                "copy": covering,
            },
        )
        return layout.backups / QUICK / "snapshots" / covering
    needed = sum(_bytes(file) for file in present)
    try:
        free = shutil.disk_usage(layout.root).free
    except OSError as refused:
        raise SnapshotFailed(f"cannot use {layout.root}: {refused.strerror}") from None
    floor = local_floor(_engine_settings(layout), free)
    if free - needed < floor:
        raise SnapshotFailed(
            f"the copy needs {_mb(needed)} and the drive holding {layout.root} has {_mb(free)} "
            f"free; QMX keeps at least {_mb(floor)} free there. Free some space and start "
            "QMX again"
        )
    made_backups = not layout.backups.exists()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    target = layout.backups / f"pre-{what}-{before}-{after}-{stamp}"
    try:
        layout.backups.mkdir(exist_ok=True)
        target.mkdir()
        for file in present:
            copy = target / file.resolve().relative_to(layout.root)
            copy.parent.mkdir(parents=True, exist_ok=True)
            if not closed and _is_sqlite(file):
                with closing(sqlite3.connect(file, timeout=BUSY_TIMEOUT_S)) as reading:
                    reading.execute("VACUUM INTO ?", (str(copy),))
            else:
                shutil.copy2(file, copy)
    except (OSError, sqlite3.Error) as failed:
        shutil.rmtree(target, ignore_errors=True)
        if made_backups:
            with suppress(OSError):
                layout.backups.rmdir()
        raise SnapshotFailed(f"the copy into {target} failed ({_why(failed)})") from None
    log_line(
        layout,
        {
            "kind": "pre-change",
            "what": what,
            "from": before,
            "to": after,
            "path": target.relative_to(layout.root).as_posix(),
            "files": [file.resolve().relative_to(layout.root).as_posix() for file in present],
            "bytes": needed,
            "seconds": round(time.monotonic() - started, 3),
        },
    )
    return target


_UPGRADE_MOMENT: Final[dict[str, str]] = {}
"""This start's copy of each folder taken for its upgrade, by the folder: from the sync before an
update until the host serves. Only this process's start counts as the same moment."""


def _moment_key(layout: Layout) -> str:
    return os.path.normcase(os.path.abspath(layout.root.resolve()))


def upgrade_copied(layout: Layout, stamp: str) -> None:
    """This PC's copies hold `stamp`, the whole folder copied for the upgrade this start makes."""
    _UPGRADE_MOMENT[_moment_key(layout)] = stamp


def upgrade_moment_ended(layout: Layout) -> None:
    """The start's upgrades are done: a store that upgrades from now on copies itself first."""
    _UPGRADE_MOMENT.pop(_moment_key(layout), None)


def _upgrade_copy(layout: Layout, files: Sequence[Path]) -> str | None:
    """This start's upgrade copy of the folder, when it holds each of `files`; None otherwise."""
    from qmx_home.backup.repository import FolderRepository, Unreadable  # noqa: PLC0415

    stamp = _UPGRADE_MOMENT.get(_moment_key(layout))
    if stamp is None:
        return None
    try:
        held = {e.path for e in FolderRepository(layout.backups / QUICK).manifest(stamp).entries}
        inside = {file.resolve().relative_to(layout.data.resolve()).as_posix() for file in files}
    except ValueError, OSError, Unreadable:
        return None
    return stamp if inside <= held else None


def completed_copies(layout: Layout, what: str) -> list[Path]:
    """The pre-change copies of `what` the backup log records as complete. The log line is
    written after the last file is copied, so a copy cut short by a kill or a power cut is not
    among them."""
    found: list[Path] = []
    for entry in log_lines(layout):
        path = layout.root / str(entry.get("path", ""))
        if (
            entry.get("kind") == "pre-change"
            and entry.get("what") == what
            and path.parent == layout.backups
            and path.is_dir()
        ):
            found.append(path)
    return found


def check_open(layout: Layout) -> Opening:
    """Read every store of the folder against this release by B2, changing none of them: no copy
    is taken and no step runs, because each store's opener does that when it opens. The label's
    `[stores]` table is rewritten when a SQLite file says otherwise (the file wins) or a store of
    plain files has no entry yet; entries this release does not know are kept."""
    started = time.monotonic()
    label = _label_of(layout)
    stores: dict[str, object] = dict(label.stores) if label is not None else {}
    verdicts: list[Verdict] = []
    for store in STORES.values():
        verdict, entry = _verdict(layout, label, store)
        verdicts.append(verdict)
        if entry is not None:
            merged = _merged(stores.get(store.name), entry)
            if merged is not None:
                stores[store.name] = merged
    written = label is not None and _rewrite_label(layout, label, stores, verdicts)
    return Opening(tuple(verdicts), written, time.monotonic() - started)


def _verdict(layout: Layout, label: Label | None, store: Store) -> tuple[Verdict, Version | None]:
    """One store's verdict, and the label entry it should have (None: leave the entry alone)."""
    match store.kind:
        case "files":
            if label is None or store.name not in label.stores:
                return _compare(layout, store, store.release), store.release
            entry = _entry(label.stores[store.name])
            if entry is None:
                action: Action = "read-only" if store.read_only else "refused"
                return Verdict(store.name, action, None, _unreadable_entry(store, layout)), None
            return _compare(layout, store, entry), None
        case "index":
            path = layout.data / store.path
            if not path.is_file():
                return Verdict(
                    store.name, "new", None, f"{store.words}: made when first opened"
                ), None
            try:
                with closing(_reader(path)) as reading:
                    state = index_state(reading, store.name)
            except sqlite3.Error:
                state = "rebuild"
            if state == "current":
                return Verdict(store.name, "opens", store.release, f"{store.words}: opens"), None
            aside = "moved aside, then " if state == "foreign" else ""
            line = f"{store.words}: {aside}rebuilt from the Library's own files when it next opens"
            return Verdict(store.name, "rebuilds", None, line), None
        case "sqlite":
            path = layout.data / store.path
            if not path.is_file():
                line = f"{store.words}: made at version {store.release.version} when first opened"
                return Verdict(store.name, "new", None, line), None
            try:
                with closing(_reader(path)) as reading:
                    found = _found(reading, store, path)
            except StoreRefused as refused:
                return Verdict(store.name, "refused", None, str(refused)), None
            except sqlite3.Error as busy:
                line = f"{store.words}: could not be read just now ({_why(busy)})"
                return Verdict(store.name, "refused", None, line), None
            if found is None:
                line = f"{store.words}: made at version {store.release.version} when first opened"
                return Verdict(store.name, "new", None, line), None
            return _compare(layout, store, found.version), found.version


def _compare(layout: Layout, store: Store, found: Version) -> Verdict:
    words, ours = store.words, store.release.version
    if found.version == ours:
        return Verdict(store.name, "opens", found, f"{words}: version {ours}, opens")
    if found.version < ours:
        line = (
            f"{words}: version {found.version}, upgraded to {ours} when it next opens, after a "
            "copy into backups/"
        )
        return Verdict(store.name, "upgrades", found, line)
    if not _closed(store, found):
        line = (
            f"{words}: version {found.version} from a newer QMX that still allows this one; opens"
        )
        return Verdict(store.name, "opens newer", found, line)
    action: Action = "read-only" if store.read_only else "refused"
    return Verdict(store.name, action, found, _too_new(store, found, layout))


def _merged(existing: object, found: Version) -> dict[str, object] | None:
    """The label entry with the file's version and `min_reader` written in, every other field it
    holds kept; None leaves an entry this release cannot read as it is."""
    if existing is None:
        return {"version": found.version, "min_reader": found.min_reader}
    if not isinstance(existing, dict):
        return None
    return {
        **cast("dict[str, object]", existing),
        "version": found.version,
        "min_reader": found.min_reader,
    }


def _unreadable_entry(store: Store, layout: Layout) -> str:
    after = f" The {store.words} opens read-only until then." if store.read_only else ""
    return (
        f"This QMX folder's label {layout.label} says what version the {store.words} is in a "
        "way this QMX cannot read, so it may be newer than this QMX. Install the QMX that last "
        f"wrote this folder, or {restore_hint(layout.root)}.{after}"
    )


def _closed(store: Store, found: Version) -> bool:
    return found.version > store.release.version and found.min_reader > store.release.version


def _rewrite_label(
    layout: Layout, label: Label, stores: dict[str, object], verdicts: Sequence[Verdict]
) -> bool:
    if label.format_version != TREE:
        return False
    newer = any(
        (v.found is not None and v.found.version > STORES[v.store].release.version)
        or (v.found is None and v.action in ("refused", "read-only"))
        for v in verdicts
    )
    by = label.last_written_by if newer else version("qmx-home")
    if stores == dict(label.stores) and by == label.last_written_by:
        return False
    text = replace(label, stores=stores, last_written_by=by).dump()
    staged = layout.root / f"{LABEL}.{os.getpid()}.new"
    for _ in range(5):
        try:
            staged.write_text(text, encoding="utf-8")
            staged.replace(layout.label)
        except PermissionError:
            time.sleep(0.05)
            continue
        except OSError:
            break
        return True
    with suppress(OSError):
        staged.unlink()
    return False


def _forward(
    connection: sqlite3.Connection,
    store: Store,
    path: Path | None,
    steps: Sequence[Sequence[str]],
    *,
    fresh: bool,
) -> tuple[list[int], Path | None]:
    """Run the steps the file lacks, each under the write lock and in its own transaction. The
    version is read again under the lock, so a second process opening at the same time finds the
    store already moved and runs nothing."""
    applied: list[int] = []
    copy: Path | None = None
    while True:
        connection.execute("BEGIN IMMEDIATE")
        target = 0
        try:
            now = _judge(store, _found(connection, store, path), path)
            if now is not None and now.version.version >= store.release.version:
                if now.version.version == store.release.version and not now.marked:
                    _mark(connection, store, store.release.version)
                connection.execute("COMMIT")
                return applied, copy
            target = 1 if now is None else now.version.version + 1
            if now is not None and not fresh and copy is None:
                copy = _copy_first(store, path, now.version.version)
            for statement in steps[target - 1]:
                connection.execute(statement)
            _mark(connection, store, target)
            connection.execute("COMMIT")
        except StoreRefused:
            _rollback(connection)
            raise
        except Exception as error:
            _rollback(connection)
            if not target:
                raise
            raise _step_failed(store, path, target, error, copy) from error
        except BaseException:
            _rollback(connection)
            raise
        applied.append(target)


def _copy_first(store: Store, path: Path | None, before: int) -> Path:
    layout = None if path is None else folder_of(path)
    if layout is None or path is None:
        raise StoreRefused(
            store.name,
            f"The {store.words} at {path} is version {before} and this QMX upgrades it to "
            f"{store.release.version}, but it is not inside a QMX folder, so the copy QMX takes "
            "before an upgrade has nowhere to go. Nothing changed. Open it from its QMX folder.",
        )
    try:
        return snapshot(layout, store.name, before, store.release.version, [path])
    except SnapshotFailed as failed:
        raise StoreRefused(
            store.name,
            f"The {store.words} needs an upgrade from version {before} to "
            f"{store.release.version}, and the copy QMX takes first could not be made: {failed}. "
            "Nothing changed.",
        ) from None


def _step_failed(
    store: Store, path: Path | None, target: int, error: Exception, copy: Path | None
) -> StoreRefused:
    why = _why(error)
    layout = None if path is None else folder_of(path)
    if layout is not None:
        with suppress(OSError):
            log_line(
                layout,
                {
                    "kind": "upgrade-failed",
                    "store": store.name,
                    "step": target,
                    "stays_at": target - 1,
                    "error": why,
                    "copy": None if copy is None else copy.relative_to(layout.root).as_posix(),
                },
            )
    kept = "" if copy is None else f", and the copy taken first is in {copy}"
    return StoreRefused(
        store.name,
        f"The {store.words} could not be upgraded: step {target} (version {target - 1} to "
        f"{target}) failed ({why}). It stays at version {target - 1}, as it was{kept}.",
    )


def _mark(connection: sqlite3.Connection, store: Store, at: int) -> None:
    """Write the store's marks inside the caller's transaction."""
    floor = (
        store.release.min_reader
        if at == store.release.version
        else min(at, store.release.min_reader)
    )
    connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
    connection.execute(f"PRAGMA user_version = {at}")
    connection.execute(
        f"CREATE TABLE IF NOT EXISTS {store.meta}"
        " (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID"
    )
    rows = [("min_reader", str(floor))]
    if store.version_key:
        rows.append((store.version_key, str(at)))
    connection.executemany(
        f"INSERT INTO {store.meta} (key, value) VALUES (?, ?)"  # noqa: S608
        " ON CONFLICT (key) DO UPDATE SET value = excluded.value",
        rows,
    )


def _found(connection: sqlite3.Connection, store: Store, path: Path | None) -> Found | None:
    """What the file is, read only. None for a file holding no table at all."""
    try:
        app = _pragma(connection, "application_id")
        user = _pragma(connection, "user_version")
        tables = {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        floor = _meta_int(connection, store.meta, "min_reader", tables)
        legacy = _meta_int(connection, store.meta, store.version_key, tables)
    except sqlite3.DatabaseError as broken:
        match getattr(broken, "sqlite_errorname", ""):
            case "SQLITE_NOTADB":
                raise _not_ours(store, path, "it is not a SQLite database") from None
            case "SQLITE_CORRUPT":
                raise StoreRefused(
                    store.name,
                    f"The {store.words} at {path} is damaged and cannot be read. QMX leaves it as "
                    "it is; restore it from a copy in backups/.",
                ) from None
            case _:
                raise
    except ValueError:
        raise _not_ours(store, path, "its version marks cannot be read") from None
    own = bool(tables & set(store.tables))
    if app not in (0, APPLICATION_ID):
        raise _not_ours(store, path, f"it belongs to another program (application id {app:#x})")
    if app == 0:
        if not tables:
            return None
        if user != 0:
            raise _not_ours(store, path, "it carries another program's version mark")
        if legacy is None and not own:
            raise _not_ours(store, path, f"it holds none of a QMX {store.words}'s tables")
        at = 1 if legacy is None else legacy
        return Found(Version(at, at if floor is None else floor), marked=False)
    at = max(user, legacy or 0)
    if at <= store.release.version and tables and not own:
        raise _not_ours(store, path, f"it holds none of a QMX {store.words}'s tables")
    return Found(Version(at, at if floor is None else floor), marked=floor is not None)


def _judge(store: Store, found: Found | None, path: Path | None) -> Found | None:
    if found is not None and _closed(store, found.version):
        layout = None if path is None else folder_of(path)
        raise StoreRefused(store.name, _too_new(store, found.version, layout))
    return found


def _too_new(store: Store, found: Version, layout: Layout | None) -> str:
    label = None if layout is None else _label_of(layout)
    by = "" if label is None else f" by QMX {label.last_written_by}"
    after = f" The {store.words} opens read-only until then." if store.read_only else ""
    return (
        f"This QMX folder's {store.words} was written{by} as {store.words} version "
        f"{found.version}. This QMX reads {store.words} version {store.release.version}, and this "
        f"one needs a QMX that reads version {found.min_reader} or newer. Install that QMX, or "
        f"{restore_hint(None if layout is None else layout.root)}.{after}"
    )


def _not_ours(store: Store, path: Path | None, why: str) -> StoreRefused:
    return StoreRefused(
        store.name,
        f"{path} is not a QMX {store.words}: {why}. QMX leaves it as it is; move it aside and "
        "start QMX again to make a new one.",
    )


def _entry(value: object) -> Version | None:
    match value:
        case {"version": int(at), "min_reader": int(floor)}:
            return Version(at, floor)
        case {"version": int(at)}:
            return Version(at, at)
        case _:
            return None


def _label_of(layout: Layout) -> Label | None:
    try:
        return Label.parse(layout.label.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return None


def _pragma(connection: sqlite3.Connection, name: str) -> int:
    """Read to the end, so no statement stays open to hold the file's read lock."""
    rows = connection.execute(f"PRAGMA {name}").fetchall()
    return int(rows[0][0]) if rows else 0


def _meta_int(connection: sqlite3.Connection, table: str, key: str, tables: set[str]) -> int | None:
    if not key or table not in tables:
        return None
    rows = connection.execute(f"SELECT value FROM {table} WHERE key = ?", (key,)).fetchall()  # noqa: S608
    return int(rows[0][0]) if rows else None


def _file_of(connection: sqlite3.Connection) -> Path | None:
    for _, name, file in connection.execute("PRAGMA database_list").fetchall():
        if name == "main" and file:
            return Path(str(file))
    return None


def _reader(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=BUSY_TIMEOUT_S)


def _rollback(connection: sqlite3.Connection) -> None:
    if connection.in_transaction:
        connection.execute("ROLLBACK")


def _is_sqlite(path: Path) -> bool:
    with path.open("rb") as handle:
        return handle.read(len(SQLITE_HEADER)) == SQLITE_HEADER


def _bytes(path: Path) -> int:
    wal = path.with_name(f"{path.name}-wal")
    return path.stat().st_size + (wal.stat().st_size if wal.is_file() else 0)


def _mb(count: int) -> str:
    return f"{max(count, 0) / (1 << 20):,.0f} MB"


def _why(error: BaseException) -> str:
    named = getattr(error, "sqlite_errorname", None)
    if isinstance(named, str):
        return named
    if isinstance(error, OSError) and error.strerror:
        return error.strerror
    return type(error).__name__


def log_line(layout: Layout, record: Mapping[str, object]) -> None:
    """Add one line to the backup log, stamped with the time, durable before this returns."""
    line = json.dumps({"at": datetime.now(UTC).isoformat(), **record}, sort_keys=True)
    with (layout.backups / LOG).open("a", encoding="utf-8") as log:
        log.write(line + "\n")
        log.flush()
        os.fsync(log.fileno())


def log_lines(layout: Layout) -> list[dict[str, object]]:
    """Every whole line of the backup log, oldest first; none when there is no log. A line that
    is not a JSON object, as a power cut leaves the last one, is skipped."""
    try:
        text = (layout.backups / LOG).read_text(encoding="utf-8")
    except OSError:
        return []
    records: list[dict[str, object]] = []
    for line in text.splitlines():
        try:
            record: object = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            records.append(cast("dict[str, object]", record))
    return records


def _engine_settings(layout: Layout) -> Mapping[str, object]:
    """`[engine]` as `settings.toml` holds it, or nothing when it cannot be read."""
    try:
        read = tomllib.loads((layout.data / "settings.toml").read_text(encoding="utf-8"))
    except OSError, ValueError:
        return {}
    engine = read.get("engine")
    return cast("Mapping[str, object]", engine) if isinstance(engine, dict) else {}
