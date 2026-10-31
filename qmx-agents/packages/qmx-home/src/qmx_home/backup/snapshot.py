"""One copy of the folder's `data/`, made while QMX runs (design 62 C1, Appendix D).

`make` copies in an order that never mixes moments: every SQLite store first, then the Library's
ref, edge and annotation logs, then every other file that changes, then each price month (its
data files before its `state.json`, again when the state moved meanwhile), and last the listing
of the files written once. Each step copies a moment no earlier than the step before, so no
copied ledger row, ref or price state names a file the copy lacks.

A store is copied by `VACUUM INTO` from a `mode=ro` connection, so the copy holds what was
committed and the live store is never checkpointed. A log is copied up to its last full line. A
file whose size and `mtime_ns` (and its `-wal`'s, for a store) match the previous copy is not
read again. Nothing in `LEFT_OUT` or `SECRET` is ever in a copy, and no link is followed or
copied.
"""

from __future__ import annotations

import functools
import glob
import json
import os
import platform
import re
import sqlite3
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Final, cast

from qmx_home import Label, Layout
from qmx_home.backup.repository import FORMAT, Entry, FolderRepository, Kind, Manifest
from qmx_home.files import copy_file, flush_file, long_path, open_shared, plain, sha256_of
from qmx_home.stores import STORES

LEFT_OUT: Final[tuple[tuple[str, str], ...]] = (
    ("library/catalog.db", "the Library's index, made again from its files"),
    ("memory/fts.db", "the recall index, made again from the Library"),
    ("memory/hindsight/pg/**", "Hindsight's database, made again from Library rows"),
    ("library/blobs/fetched/**", "cache copies fetched again from the store that made them"),
    ("library/blobs/transient/**", "checkpoints the host deletes to make room"),
    ("cache/prices/**", "prices fetched again"),
    ("queue/telemetry/**", "telemetry the host deletes to make room"),
    ("library/uploads/*.part", "uploads that did not finish"),
    ("market/.staging/**", "price commits still being written"),
    ("market/**/.state.tmp", "a price state still being written"),
    ("market/**/.incoming.parquet", "a price file still being written"),
    ("market/**/.verify-*", "a price check's scratch"),
    ("settings.tmp", "settings still being written"),
    ("chats/*/**", "a chat's launch files, made again at each launch"),
    ("apps/*/data/heartbeat-*", "a mini app's heartbeat"),
    ("apps/*/data/tmp/**", "a mini app's scratch"),
    ("**/*.lock", "a lock"),
    ("control-process.json", "the record of a running process"),
    ("router.port", "a running process's port"),
    ("node.port", "a running process's port"),
    ("**/*-wal", "SQLite's own file; the store is copied whole"),
    ("**/*-shm", "SQLite's own file; the store is copied whole"),
    ("**/*-journal", "SQLite's own file; the store is copied whole"),
    ("**/*.qmx-copying", "a copy still being written"),
)
"""Paths in `data/` never in a copy, and why. Under `library/` a writer's temporary name
`.<name>.<32 hex>` is left out too (`TEMPORARY`), while `checkout/.../.checkout.json` is copied."""
TEMPORARY: Final = re.compile(r"\..+\.[0-9a-f]{32}")
BORN_BLOB: Final = re.compile(
    r"library/blobs/([0-9a-f]{2})/([0-9a-f]{2})/((?:\1)(?:\2)[0-9a-f]{60})"
)
"""A blob born on this store, named by the sha256 of its bytes, so its hash is read from its name
and checked when a target copies it."""
SECRET: Final[tuple[str, ...]] = (
    "vault/**",
    "rclone.conf",
    "claude/.credentials.json",
    "claude/.claude.json",
    "claude-relayed/.credentials.json",
    "claude-relayed/.claude.json",
)
"""Paths in `data/` that hold a key, a token or a login, never in a copy in clear. A restore
carries them over from the data it sets aside; the sealed key copy holds the keys among them."""
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
    """Why `path` (relative to `data/`) is never in a copy, or None when it is copied."""
    if _matcher(SECRET).match(path):
        return "a key, token or login"
    if _matcher(tuple(g for g, _ in LEFT_OUT)).match(path):
        return next(why for g, why in LEFT_OUT if _matcher((g,)).match(path))
    name = path.rpartition("/")[2]
    if path.startswith("library/") and TEMPORARY.fullmatch(name):
        return "a file the Library is still writing"
    if _matcher(tuple(extra)).match(path):
        return "left out in Settings"
    return None


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
    previous: Manifest | None,
    stamp: str,
    why: str = "round",
    leave_out: Sequence[str] = (),
    keep_free: int = 0,
    progress: Callable[[str], None] | None = None,
) -> Manifest:
    """Copy `data/` into the quick undo's pool and return the copy's manifest (not yet written).
    A file written once stays in `data/` and its line says `at: live`; every other file is in
    the pool. `previous` is the newest copy, whose hashes an unchanged file keeps. Raises NoRoom
    before writing when the files to copy would leave the drive below `keep_free`, and Changing
    when a price month never held still."""
    quick = FolderRepository(layout.backups / "quick")
    told = progress or _quiet
    known = {} if previous is None else {entry.path: entry for entry in previous.entries}
    found, months = _survey(layout.data, leave_out, known)
    copying = _Copying(layout, quick, known)
    need = sum(f.size for f in found if not copying.reusable(f))
    room = quick.room()
    if room - need < keep_free:
        raise NoRoom(
            f"the quick undo in {quick.where} needs {_mb(need)} and its drive has {_mb(room)} "
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
    for step, files in zip(STEPS[:3], (stores, logs, others), strict=True):
        told(step)
        for one in files:
            copying.copy(one)
    told(STEPS[3])
    for month in sorted(months):
        copying.month(month, leave_out)
    told(STEPS[4])
    for one in _walk(layout.data, leave_out):
        if one in copying.done or not written_once(one) or _in_month(one, months):
            continue
        copying.once(one)
    head = header(layout, stamp, why)
    if copying.unread:
        head |= {"partial": True, "unread": copying.unread}
    return Manifest(head, tuple(copying.entries))


class _Copying:
    """The files of one copy as they are copied, in order."""

    def __init__(self, layout: Layout, quick: FolderRepository, known: Mapping[str, Entry]):
        self.data = layout.data
        self.quick = quick
        self.known = known
        self.entries: list[Entry] = []
        self.done: set[str] = set()
        self.unread: list[str] = []

    def reusable(self, found: _Found) -> bool:
        before = self.known.get(found.path)
        return (
            before is not None
            and before.kind == found.kind
            and before.seen == found.seen
            and (before.at == "live" or self.quick.pool_has(before.sha256))
        )

    def keep(self, entry: Entry) -> None:
        self.entries.append(entry)
        self.done.add(entry.path)

    def copy(self, found: _Found) -> None:
        if self.reusable(found):
            self.keep(self.known[found.path])
            return
        source = self.data / found.path
        writing = self.quick.temporary()
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
                    digest = self.quick.put_bytes(after)
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
        if stat is not None and before is not None and before.seen == stat:
            pooled = self.quick.pool_path(before.sha256)
            if long_path(pooled).is_file():
                return long_path(pooled).read_bytes()
        return _read(self.data / path)

    def _store(self, found: _Found, source: Path, writing: Path) -> Entry:
        uri = f"{source.resolve().as_uri()}?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=BUSY_TIMEOUT_S)) as reading:
            reading.execute("VACUUM INTO ?", (str(writing),))
        flush_file(writing)
        tables, user_version, floor = _store_facts(writing, found.path)
        digest = sha256_of(writing)
        size = writing.stat().st_size
        self.quick.adopt(writing, digest)
        return Entry(
            found.path, digest, size, "store", found.seen, "pool", tables, user_version, floor
        )

    def _file(self, found: _Found, source: Path, writing: Path, length: int | None) -> Entry:
        digest = copy_file(source, writing, length=length)
        size = long_path(writing).stat().st_size
        self.quick.adopt(writing, digest)
        return Entry(found.path, digest, size, found.kind, found.seen)


def _survey(
    data: Path, leave_out: Sequence[str], known: Mapping[str, Entry]
) -> tuple[list[_Found], set[str]]:
    """Every file that changes, with its kind and live stats, and every price month folder."""
    found: list[_Found] = []
    months: set[str] = set()
    for path in _walk(data, leave_out, months):
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


def _walk(data: Path, leave_out: Sequence[str], months: set[str] | None = None) -> Iterator[str]:
    """Every file under `data` that is not left out, as a path relative to it, never through a
    link or a junction. A price month folder (under `market/`, holding `state.json`) is added
    to `months` when given."""
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
            elif entry.is_file() and left_out(path, leave_out) is None:
                yield path


def _pruned(folder: str, leave_out: Sequence[str]) -> bool:
    """Whether everything under `folder` is left out, so it is not walked at all."""
    every = (*SECRET, *(g for g, _ in LEFT_OUT), *leave_out)
    return _matcher(tuple(g[:-3] for g in every if g.endswith("/**"))).match(folder) is not None


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
