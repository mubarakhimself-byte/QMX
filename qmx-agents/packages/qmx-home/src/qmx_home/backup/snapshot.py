"""One copy of the folder's `data/`, made while QMX runs (design 62 C1, Appendix D).

`make` copies in an order that never mixes moments: every SQLite store first, then the Library's
ref, edge and annotation logs, then every other file that changes, then each price month (its
data files before its `state.json`, again when the state moved meanwhile), and last the listing
of the files written once. Each step copies a moment no earlier than the step before, so no
copied ledger row, ref or price state names a file the copy lacks.

A store is copied by `VACUUM INTO` from a `mode=ro` connection, so the copy holds what was
committed and the live store is never checkpointed. A log is copied up to its last full line. A
file whose size and `mtime_ns` (and its `-wal`'s, for a store) match the previous copy is not
read again. A copy holds only the classes it is asked for (`qmx_home.classes`): nothing
`rebuildable`, `secret` or `scratch` is ever in one, and no link is followed or copied.
`settings.toml` is copied without any key-shaped value, each named in the header's
`keys_to_fill`. A mini app's `road/` is copied under its road lease when the host hands one.
"""

from __future__ import annotations

import functools
import glob
import json
import os
import platform
import re
import sqlite3
import tomllib
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, closing
from dataclasses import dataclass
from datetime import date, datetime
from datetime import time as clock_time
from importlib.metadata import version
from pathlib import Path
from typing import Final, cast

from qmx_home import Label, Layout
from qmx_home.backup.repository import FORMAT, Entry, FolderRepository, Kind, Manifest
from qmx_home.classes import LIBRARY, NEVER, SENT, Class, pruned, rule_of, secret_values, sent
from qmx_home.classes import without as without_keys
from qmx_home.files import copy_file, flush_file, long_path, open_shared, plain, sha256_of
from qmx_home.stores import STORES

type RoadLease = Callable[[str], AbstractContextManager[object]]
"""One mini app's road lease, held while its `road/` is copied. The host hands it to the round,
because `qmx-home` cannot import the apps' own lease."""
type Kinds = Mapping[str, tuple[str, ...]]
"""Each Library object's kind, and the kinds of the objects naming each blob, by path in `data/`."""

BORN_BLOB: Final = re.compile(
    r"library/blobs/([0-9a-f]{2})/([0-9a-f]{2})/((?:\1)(?:\2)[0-9a-f]{60})"
)
"""A blob born on this store, named by the sha256 of its bytes, so its hash is read from its name
and checked when a target copies it."""
OBJECT: Final = re.compile(r"library/objects/[0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{64}\.json")
SETTINGS: Final = "settings.toml"
WRITE_ONCE: Final[tuple[str, ...]] = (
    "library/objects/**",
    "library/blobs/??/**",
    "library/blobs/tombstones/**",
    "market/**/*.parquet",
    "migration/pre/**",
    "migration/retired/**",
)
"""Paths in `data/` never rewritten in place, listed last. Under `market/`, `open.parquet` is the
open month and changes."""
STORE_ORDER: Final = tuple(store.path for store in STORES.values() if store.kind == "sqlite")
LIBRARY_LOGS: Final = ("library/refs", "library/edges", "library/annotations")
OPEN_MONTH: Final = "open.parquet"
STATE: Final = "state.json"
MONTH_TRIES: Final = 20
"""A probe bound, not a cap: how often one price month is copied again while its state keeps
moving before the round gives up on it and the next round tries again."""
SQLITE_HEADER: Final = b"SQLite format 3\x00"
BUSY_TIMEOUT_S: Final = 30.0
STEPS: Final = ("stores", "library logs", "files", "price months", "files written once")
ROAD: Final = re.compile(r"apps/([^/]+)/road/.+")
_CASE: Final = os.name != "nt"


class NoRoom(Exception):
    """The copy would leave the drive below what QMX keeps free. Nothing was written."""


class Changing(Exception):
    """A price month kept changing while it was copied. Nothing of this copy is kept."""


@dataclass(frozen=True, slots=True)
class _Found:
    path: str
    kind: Kind
    seen: tuple[int, ...]
    size: int


@functools.cache
def _matcher(globs: tuple[str, ...]) -> re.Pattern[str]:
    """One pattern matching a path (relative, `/` between names) any of `globs` matches, as
    `PurePosixPath.full_match` would; case does not count on Windows."""
    if not globs:
        return re.compile(r"(?!)")
    parts = (glob.translate(g, recursive=True, include_hidden=True, seps="/") for g in globs)
    return re.compile("|".join(f"(?:{part})" for part in parts), 0 if _CASE else re.IGNORECASE)


def left_out(path: str, extra: Sequence[str] = ()) -> str | None:
    """Why `path` (relative to `data/`) is never in a copy, or None when its class may be: it is
    `rebuildable`, `secret` or `scratch`, or he left it out in Settings."""
    rule = rule_of(f"data/{path}")
    if rule is not None and rule.answer in NEVER:
        return rule.why
    if _matcher(tuple(extra)).match(path):
        return "left out in Settings"
    return None


def library_kinds(data: Path) -> dict[str, tuple[str, ...]]:
    """Each Library object's kind, and the kinds of the objects that name each blob, by path
    relative to `data/`, read from the objects themselves (each is written once and small)."""
    found: dict[str, list[str]] = {}
    for folder, _, names in os.walk(long_path(data / "library" / "objects")):
        for name in names:
            if not name.endswith(".json") or len(name) != 69:
                continue
            try:
                manifest = json.loads(Path(folder, name).read_bytes())
            except OSError, ValueError:
                continue
            fields = cast("dict[str, object]", manifest) if isinstance(manifest, dict) else {}
            kind = fields.get("kind")
            if not isinstance(kind, str):
                continue
            found[f"library/objects/{name[:2]}/{name[2:4]}/{name}"] = [kind]
            blobs = fields.get("blobs")
            for spec in (
                cast("dict[str, object]", blobs).values() if isinstance(blobs, dict) else ()
            ):
                held = (
                    cast("dict[str, object]", spec).get("sha256")
                    if isinstance(spec, dict)
                    else None
                )
                blob = str(held or "").removeprefix("sha256:")
                if len(blob) == 64:
                    found.setdefault(f"library/blobs/{blob[:2]}/{blob[2:4]}/{blob}", []).append(
                        kind
                    )
    return {path: tuple(kinds) for path, kinds in found.items()}


def needs_kinds(*saves: Collection[Class]) -> bool:
    """Whether some switches leave a Library class out, so objects must be told apart by kind."""
    return any(not set(save) >= LIBRARY for save in saves)


def only(copy: Manifest, save: Collection[Class], kinds: Kinds) -> Manifest:
    """The part of `copy` a place with the switches `save` keeps, its header naming the Library
    objects the switches left out."""
    chosen: tuple[Class, ...] = tuple(c for c in SENT if c in save)
    entries = tuple(e for e in copy.entries if _kept(e.path, chosen, kinds))
    head = {k: v for k, v in copy.header.items() if k != "left_out"} | {"save": list(chosen)}
    left = sorted(p for p in kinds if OBJECT.fullmatch(p) and not _kept(p, chosen, kinds))
    if left:
        head["left_out"] = [f"{path} (left out by your switches)" for path in left]
    return Manifest(head, entries)


def _kept(path: str, save: Collection[Class], kinds: Kinds) -> bool:
    return sent(f"data/{path}", save, kinds.get(path))


def written_once(path: str) -> bool:
    name = path.rpartition("/")[2]
    if path.startswith("market/") and (name == OPEN_MONTH or name.startswith(".")):
        return False
    return _matcher(WRITE_ONCE).match(path) is not None


def header(layout: Layout, stamp: str, why: str) -> dict[str, object]:
    label = Label.parse(layout.label.read_text(encoding="utf-8"))
    return {
        "format": FORMAT,
        "home_id": label.home_id,
        "stamp": stamp,
        "why": why,
        "release": version("qmx-home"),
        "machine": platform.node(),
        "folder": str(layout.root),
        "format_version": label.format_version,
        "min_reader": label.min_reader,
        "last_written_by": label.last_written_by,
        "stores": dict(label.stores),
    }


def make(
    layout: Layout,
    *,
    into: FolderRepository,
    have: FolderRepository | None = None,
    previous: Manifest | None,
    stamp: str,
    why: str = "round",
    leave_out: Sequence[str] = (),
    save: Collection[Class] = SENT,
    kinds: Kinds | None = None,
    keep_free: int = 0,
    progress: Callable[[str], None] | None = None,
    road_lease: RoadLease | None = None,
) -> Manifest:
    """Copy the classes `save` of `data/` into the loose pool of `into` (the round's staging)
    and return the copy's manifest (not yet written). A new file written once stays in `data/`
    and its line says `at: live`, for This PC's copies to link and each send to read there; every
    other new file is in `into`. `previous` is the newest of This PC's copies `have`, whose
    hashes an unchanged file keeps while `have` still holds its bytes. `kinds` tells Library
    objects apart when `save` leaves a Library class out (`library_kinds`). Raises NoRoom before
    writing when the files to copy would leave the drive below `keep_free`, and Changing when a
    price month never held still."""
    told = progress or _quiet
    known = {} if previous is None else {entry.path: entry for entry in previous.entries}
    chosen: tuple[Class, ...] = tuple(c for c in SENT if c in save)
    by_kind: Kinds = kinds if kinds is not None else {}

    def kept(path: str) -> bool:
        return _kept(path, chosen, by_kind)

    found, months = _survey(layout.data, leave_out, known, kept)
    months = {month for month in months if kept(f"{month}/{STATE}")}
    copying = _Copying(layout, into, have, known)
    need = sum(f.size for f in found if not copying.reusable(f))
    room = into.room() or 0
    if room - need < keep_free:
        raise NoRoom(
            f"the copy in {into.where} needs {_mb(need)} and its drive has {_mb(room)} "
            f"free; QMX keeps at least {_mb(keep_free)} free there so QMX itself never runs "
            "out of room. Free some space; the next round tries again"
        )
    stores = sorted(
        (f for f in found if f.kind == "store"),
        key=lambda f: (
            STORE_ORDER.index(f.path) if f.path in STORE_ORDER else len(STORE_ORDER),
            f.path,
        ),
    )
    logs = [f for f in found if f.kind != "store" and f.path.startswith(LIBRARY_LOGS)]
    others = [f for f in found if f.kind != "store" and not f.path.startswith(LIBRARY_LOGS)]
    roads: dict[str, list[_Found]] = {}
    for one in others:
        road = ROAD.fullmatch(one.path)
        if road is not None:
            roads.setdefault(road.group(1), []).append(one)
    others = [f for f in others if ROAD.fullmatch(f.path) is None]
    for step, files in zip(STEPS[:3], (stores, logs, others), strict=True):
        told(step)
        for one in files:
            copying.copy(one)
    for app, files in sorted(roads.items()):
        copying.road(app, files, road_lease)
    told(STEPS[3])
    for month in sorted(months):
        copying.month(month, leave_out)
    told(STEPS[4])
    for one in _walk(layout.data, leave_out, kept=kept):
        if one in copying.done or not written_once(one) or _in_month(one, months):
            continue
        copying.once(one)
    head = header(layout, stamp, why) | {"save": list(chosen), "keys_to_fill": copying.keys}
    left = sorted(p for p in by_kind if OBJECT.fullmatch(p) and not kept(p))
    if left:
        head["left_out"] = [f"{path} (left out by your switches)" for path in left]
    if copying.unread:
        head |= {"partial": True, "unread": copying.unread}
    return Manifest(head, tuple(copying.entries))


def _scanned(path: Path) -> tuple[list[str], bytes | str | None]:
    """`settings.toml`'s key paths that hold a secret, and what its copy holds: None for the file
    as it is (no secret in it), the bytes without them, or the line saying why it is left out."""
    raw = _read(path)
    if raw is None:
        return [], None
    try:
        values = tomllib.loads(raw.decode("utf-8"))
    except UnicodeDecodeError, tomllib.TOMLDecodeError:
        return [], (
            "it is not TOML QMX can read, so its keys could not be left out; fix it in Settings"
        )
    keys = sorted(secret_values(values))
    if not keys:
        return [], None
    return keys, _dumps(without_keys(values, keys)).encode("utf-8")


class _Copying:
    """The files of one copy as they are copied, in order."""

    def __init__(
        self,
        layout: Layout,
        into: FolderRepository,
        have: FolderRepository | None,
        known: Mapping[str, Entry],
    ):
        self.data = layout.data
        self.into = into
        self.have = have
        self.known = known
        self.keys: list[str] = []
        """The `settings.toml` key paths left out of this copy."""
        self.entries: list[Entry] = []
        self.done: set[str] = set()
        self.unread: list[str] = []

    def road(self, app: str, files: Sequence[_Found], lease: RoadLease | None) -> None:
        """One mini app's `road/`, copied while its road lease is held, so its journal and blobs
        are copied at one serialized point."""
        if lease is None:
            for one in files:
                self.copy(one)
            return
        try:
            with lease(app):
                for one in files:
                    self.copy(one)
        except Exception as busy:  # the lease is the apps' own; any refusal leaves the road out
            self.unread += [f"{one.path} (its road lease was held: {busy})" for one in files]

    def reusable(self, found: _Found) -> bool:
        before = self.known.get(found.path)
        return (
            before is not None
            and before.kind == found.kind
            and before.seen == found.seen
            and (
                before.at == "live" or (self.have is not None and self.have.pool_has(before.sha256))
            )
        )

    def keep(self, entry: Entry) -> None:
        self.entries.append(entry)
        self.done.add(entry.path)

    def copy(self, found: _Found) -> None:
        if found.path == SETTINGS:
            # Scanned every time: a copy made before this release holds the file whole, keys in.
            self.keys, held = _scanned(self.data / SETTINGS)
            if isinstance(held, str):
                self.unread.append(f"{SETTINGS} ({held})")
                return
            if held is not None:
                digest = self.into.put_bytes(held)
                self.keep(Entry(found.path, digest, len(held), found.kind, found.seen))
                return
        if self.reusable(found):
            self.keep(self.known[found.path])
            return
        source = self.data / found.path
        writing = self.into.temporary()
        try:
            match found.kind:
                case "store":
                    entry = self._store(found, source, writing)
                case "log":
                    entry = self._file(found, source, writing, _last_line_end(source))
                case _:
                    entry = self._file(found, source, writing, None)
        except FileNotFoundError:
            long_path(writing).unlink(missing_ok=True)
            return
        except (OSError, sqlite3.Error) as failed:
            long_path(writing).unlink(missing_ok=True)
            self.unread.append(f"{found.path} ({_why(failed)})")
            return
        self.keep(entry)

    def once(self, path: str) -> None:
        source = self.data / path
        try:
            stat = long_path(source).stat()
        except FileNotFoundError:
            return
        found = _Found(path, "once", (stat.st_size, stat.st_mtime_ns), 0)
        if self.reusable(found):
            self.keep(self.known[path])
            return
        named = BORN_BLOB.fullmatch(path)
        if named is not None:
            self.keep(Entry(path, named.group(3), stat.st_size, "once", found.seen, at="live"))
            return
        try:
            digest = sha256_of(source)
        except FileNotFoundError:
            return
        except OSError as failed:
            self.unread.append(f"{path} ({_why(failed)})")
            return
        self.keep(Entry(path, digest, stat.st_size, "once", found.seen, at="live"))

    def month(self, folder: str, leave_out: Sequence[str]) -> None:
        """One price month: its data files, then its state, again until the state held still
        across the copy and names a file the copy holds. A state unchanged since the previous
        copy is read from the pool, not from `data/`."""
        state = f"{folder}/{STATE}"
        for _ in range(MONTH_TRIES):
            first = _stat(self.data / state)
            before = self._state(state, first)
            names: list[str] = []
            for name in _month_files(self.data / folder):
                path = f"{folder}/{name}"
                if left_out(path, leave_out) is not None:
                    continue
                if written_once(path):
                    self.once(path)
                else:
                    stat = _stat(self.data / path)
                    if stat is not None:
                        self.copy(_Found(path, "file", stat, stat[0]))
                if path in self.done:
                    names.append(name)
            last = _stat(self.data / state)
            after = self._state(state, last)
            if before == after and first == last and _named(after) in (None, *names):
                if after is not None and first is not None:
                    digest = self.into.put_bytes(after)
                    self.keep(Entry(state, digest, len(after), "file", first))
                return
            self.done.difference_update(f"{folder}/{name}" for name in names)
            self.entries = [e for e in self.entries if e.path.rpartition("/")[0] != folder]
        raise Changing(
            f"the price month {folder} kept changing while it was copied; the next round tries "
            "again"
        )

    def _state(self, path: str, stat: tuple[int, int] | None) -> bytes | None:
        before = self.known.get(path)
        if stat is not None and before is not None and before.seen == stat and self.have:
            pooled = self.have.read_pool(before.sha256)
            if pooled is not None:
                return pooled
        return _read(self.data / path)

    def _store(self, found: _Found, source: Path, writing: Path) -> Entry:
        uri = f"{source.resolve().as_uri()}?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=BUSY_TIMEOUT_S)) as reading:
            reading.execute("VACUUM INTO ?", (str(writing),))
        flush_file(writing)
        tables, user_version, floor = _store_facts(writing, found.path)
        digest = sha256_of(writing)
        size = writing.stat().st_size
        self.into.adopt(writing, digest)
        return Entry(
            found.path, digest, size, "store", found.seen, "pool", tables, user_version, floor
        )

    def _file(self, found: _Found, source: Path, writing: Path, length: int | None) -> Entry:
        digest = copy_file(source, writing, length=length)
        size = long_path(writing).stat().st_size
        self.into.adopt(writing, digest)
        return Entry(found.path, digest, size, found.kind, found.seen)


def _survey(
    data: Path,
    leave_out: Sequence[str],
    known: Mapping[str, Entry],
    kept: Callable[[str], bool],
) -> tuple[list[_Found], set[str]]:
    """Every file that changes, with its kind and live stats, and every price month folder."""
    found: list[_Found] = []
    months: set[str] = set()
    for path in _walk(data, leave_out, months, kept):
        if written_once(path) or _in_month(path, months):
            continue
        source = data / path
        stat = _stat(source)
        if stat is None:
            continue
        before = known.get(path)
        kind: Kind = (
            before.kind
            if before is not None and before.kind != "once"
            else "log"
            if path.endswith(".jsonl")
            else "store"
            if _is_sqlite(source)
            else "file"
        )
        if kind == "store":
            wal = _stat(source.with_name(f"{source.name}-wal"))
            seen = (*stat, *(wal if wal is not None and wal[0] > 0 else (0, 0)))
            found.append(_Found(path, kind, seen, stat[0] + seen[2]))
        else:
            found.append(_Found(path, kind, stat, stat[0]))
    return found, months


def _walk(
    data: Path,
    leave_out: Sequence[str],
    months: set[str] | None = None,
    kept: Callable[[str], bool] | None = None,
) -> Iterator[str]:
    """Every file under `data` that is not left out and that `kept` keeps, as a path relative to
    it, never through a link or a junction. A price month folder (under `market/`, holding
    `state.json`) is added to `months` when given."""
    pending = [""]
    while pending:
        folder = pending.pop()
        try:
            entries = sorted(os.scandir(long_path(data / folder)), key=lambda e: e.name)
        except FileNotFoundError:
            continue
        names = {entry.name for entry in entries}
        if months is not None and folder.startswith("market/") and STATE in names:
            months.add(folder)
        for entry in entries:
            path = f"{folder}/{entry.name}" if folder else entry.name
            if entry.is_symlink() or entry.is_junction():
                continue
            if entry.is_dir():
                if not _pruned(path, leave_out):
                    pending.append(path)
            elif (
                entry.is_file()
                and left_out(path, leave_out) is None
                and (kept is None or kept(path))
            ):
                yield path


def _pruned(folder: str, leave_out: Sequence[str]) -> bool:
    """Whether everything under `folder` is left out, so it is not walked at all."""
    if pruned(f"data/{folder}"):
        return True
    return _matcher(tuple(g[:-3] for g in leave_out if g.endswith("/**"))).match(folder) is not None


def _in_month(path: str, months: Collection[str]) -> bool:
    return path.rpartition("/")[0] in months


def _month_files(folder: Path) -> list[str]:
    try:
        return sorted(
            entry.name
            for entry in os.scandir(long_path(folder))
            if entry.is_file(follow_symlinks=False) and entry.name != STATE
        )
    except FileNotFoundError:
        return []


def _named(state: bytes | None) -> str | None:
    """The data file a month's state names: its frozen file, or the open month."""
    if state is None:
        return None
    try:
        found = cast("dict[str, object]", json.loads(state))
        return f"{found['fingerprint']}.parquet" if found.get("frozen") else OPEN_MONTH
    except ValueError, KeyError, TypeError, AttributeError:
        return None


def _store_facts(copy: Path, path: str) -> tuple[dict[str, int], int, int | None]:
    """A copied store's row count per table, its `user_version` and its `min_reader` row."""
    meta = next((s.meta for s in STORES.values() if s.path == path), None)
    with closing(sqlite3.connect(copy)) as reading:
        names = [
            str(row[0])
            for row in reading.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        tables = {
            name: int(reading.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0])  # noqa: S608
            for name in sorted(names)
        }
        user_version = int(reading.execute("PRAGMA user_version").fetchone()[0])
        floor: int | None = None
        for table in dict.fromkeys((meta or "qmx_meta", "qmx_meta", "meta")):
            if table in names:
                row = reading.execute(
                    f"SELECT value FROM {table} WHERE key = 'min_reader'"  # noqa: S608
                ).fetchone()
                floor = int(row[0]) if row else None
                break
    return tables, user_version, floor


def _last_line_end(path: Path) -> int:
    """The length of `path` up to and with its last newline."""
    with open_shared(path) as reading:
        end = reading.seek(0, os.SEEK_END)
        while end > 0:
            start = max(0, end - (1 << 16))
            reading.seek(start)
            chunk = reading.read(end - start)
            at = chunk.rfind(b"\n")
            if at >= 0:
                return start + at + 1
            end = start
    return 0


def _is_sqlite(path: Path) -> bool:
    try:
        with open_shared(path) as reading:
            return reading.read(len(SQLITE_HEADER)) == SQLITE_HEADER
    except OSError:
        return False


def _stat(path: Path) -> tuple[int, int] | None:
    try:
        found = long_path(path).stat()
    except FileNotFoundError:
        return None
    return found.st_size, found.st_mtime_ns


def _read(path: Path) -> bytes | None:
    try:
        with open_shared(path) as reading:
            return reading.read()
    except FileNotFoundError:
        return None


def _quiet(_step: str) -> None:
    return None


def _mb(count: int) -> str:
    return f"{max(count, 0) / (1 << 20):,.0f} MB"


def _why(error: BaseException) -> str:
    named = getattr(error, "sqlite_errorname", None)
    if isinstance(named, str):
        return named
    if isinstance(error, OSError) and error.strerror:
        return f"{error.strerror}: {plain(error.filename)}" if error.filename else error.strerror
    return type(error).__name__


_BARE: Final = re.compile(r"[A-Za-z0-9_-]+")


def _dumps(values: Mapping[str, object]) -> str:
    """`values` (as `tomllib` reads them) written as TOML again, for the copy of a
    `settings.toml` whose keys were left out. Comments and layout are not kept."""
    lines: list[str] = []
    _section(lines, values, (), array=False)
    return "\n".join(lines).strip("\n") + "\n"


def _section(
    lines: list[str], table: Mapping[str, object], at: tuple[str, ...], *, array: bool
) -> None:
    flat = [(k, v) for k, v in table.items() if not _is_table(v) and not _is_tables(v)]
    if array:
        lines += ["", f"[[{_dotted(at)}]]"]
    elif at and (flat or not any(_is_table(v) or _is_tables(v) for v in table.values())):
        lines += ["", f"[{_dotted(at)}]"]
    lines += [f"{_key(k)} = {_value(v)}" for k, v in flat]
    for key, value in table.items():
        if _is_table(value):
            _section(lines, cast("Mapping[str, object]", value), (*at, key), array=False)
        elif _is_tables(value):
            for item in cast("list[Mapping[str, object]]", value):
                _section(lines, item, (*at, key), array=True)


def _is_table(value: object) -> bool:
    return isinstance(value, Mapping)


def _is_tables(value: object) -> bool:
    if not isinstance(value, list):
        return False
    items = cast("list[object]", value)
    return bool(items) and all(isinstance(item, Mapping) for item in items)


def _dotted(at: Sequence[str]) -> str:
    return ".".join(_key(part) for part in at)


def _key(key: str) -> str:
    return key if _BARE.fullmatch(key) else _string(key)


def _string(text: str) -> str:
    return json.dumps(text, ensure_ascii=False).replace("\x7f", "\\u007f")


def _value(value: object) -> str:
    match value:
        case bool():
            return "true" if value else "false"
        case int():
            return str(value)
        case float():
            text = repr(value)
            return {"inf": "inf", "-inf": "-inf", "nan": "nan"}.get(text, text)
        case str():
            return _string(value)
        case datetime() | date() | clock_time():
            return value.isoformat()
        case Mapping():
            items = cast("Mapping[str, object]", value).items()
            return "{" + ", ".join(f"{_key(k)} = {_value(v)}" for k, v in items) + "}"
        case list():
            return "[" + ", ".join(_value(v) for v in cast("list[object]", value)) + "]"
        case _:
            return _string(str(value))
