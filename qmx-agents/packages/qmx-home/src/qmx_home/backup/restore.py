"""The way back to a copy (design 62 C3 and B4, guard L2, Appendix D).

`copies` lists a place's copies by date. `newer_than` counts what the folder holds that is newer
than a copy, so he sees what returning to it replaces before he confirms. `stage` rebuilds
`data/` from one copy into `backups/restoring-<stamp>/data/` and checks every file's sha256 and
every store's row counts, while QMX may still run; nothing of the folder changes. `finish` puts
the staged copy in place with QMX closed:

1. it sets the folder's `data/` aside whole into `backups/before-restore-<id>/data/`, beside a
   copy of the label, and never deletes it;
2. it moves the staged `data/` in;
3. it carries the keys, logins and app leases over from the data it set aside (`CARRIED`);
4. it writes the copy's versions into the label, keeping the folder's `home_id` unless the
   folder takes the copy's;
5. it logs the restore. That line is also the record `after_restore` reads: server sync and
   fires stay paused, and the blobs to purge again are named, until he carries on.

Each step is journalled in `backups/restore.json` once it is done, and each is safe to run again,
so a finish killed at any point is completed by the next one. `drill` restores a sample of one
copy into `cache/restore-drill/`, removes it when it ends, and never reads or writes `data/`.
"""

from __future__ import annotations

import json
import os
import random
import re
import shutil
import sqlite3
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, cast

from qmx_home import LABEL, TREE, Label, Layout, opens
from qmx_home.backup.keep import when
from qmx_home.backup.repository import (
    READS,
    STAMP,
    Entry,
    FolderRepository,
    Manifest,
    Repository,
    Unreadable,
    free_bytes,
)
from qmx_home.backup.round import LOCK, QUICK
from qmx_home.backup.snapshot import BORN_BLOB, left_out
from qmx_home.classes import PER_MACHINE, secret_paths
from qmx_home.files import PARTIAL, Busy, copy_file, hold, long_path, plain, sha256_of, write_new
from qmx_home.stores import STORES, Version
from qmx_home.versions import FLOOR_BYTES, log_line, log_lines

JOURNAL: Final = "restore.json"
RESTORE_LOCK: Final = "restore.lock"
STAGING: Final = "restoring-"
ASIDE: Final = "before-restore-"
DRILL: Final = "restore-drill"
ENGINE_LOCK: Final = "engine.lock"
HOST_RECORD: Final = "control-process.json"
TOMBSTONES: Final = "library/blobs/tombstones"
TOMBSTONE: Final = re.compile(r"library/blobs/tombstones/([0-9a-f]{64})\.json")
CARRIED: Final = (
    *(p.removeprefix("data/") for p in (*secret_paths(), *PER_MACHINE) if p.startswith("data/")),
    "locks",
)
"""What a restore carries over from the data it set aside, in this order: the folder's keys and
logins, never in a copy, the files that belong to this machine (`observers.json`), and each mini
app's lease generation in `locks/`."""
STEPS: Final = (
    "staged",
    "set-aside",
    "moved-in",
    "purges",
    *(f"carried {name}" for name in CARRIED),
    "labelled",
    "logged",
)
"""`finish`'s steps in order; the journal names the last one done. `putting-back` is the one step
outside them: a move-in that failed, putting the folder's data back."""
PUTTING_BACK: Final = "putting-back"

type How = Literal["link", "fetch"]


class RestoreRefused(Exception):
    """A restore that must not go on. The message is the one line to show, and nothing of the
    folder changed."""


class HostServes(RestoreRefused):
    """QMX runs on the folder, so the restore cannot finish now."""


@dataclass(frozen=True, slots=True)
class Copy:
    """One copy at a place, as he picks it."""

    stamp: str
    why: str
    files: int
    bytes: int
    release: str
    machine: str
    home_id: str
    folder: str
    partial: bool
    lacks: tuple[str, ...]
    """The files the copy lacks, each with why; a restore places everything else."""


@dataclass(frozen=True, slots=True)
class Newer:
    """What the folder holds that is newer than a copy: what returning to it replaces."""

    runs: int
    ref_moves: int
    chats: int
    price_months: int

    @property
    def line(self) -> str:
        counts = (
            _count(self.runs, "run started", "runs started"),
            _count(self.ref_moves, "Library save", "Library saves"),
            _count(self.chats, "chat", "chats"),
            _count(self.price_months, "price month", "price months"),
        )
        return f"since this copy the folder holds {', '.join(counts[:-1])} and {counts[-1]}"


@dataclass(frozen=True, slots=True)
class Staged:
    stamp: str
    where: str
    folder: Path
    """The staged `data/`."""
    newer: Newer
    files: int
    bytes: int
    """The bytes copied; a linked file costs none."""
    linked: int
    lacks: tuple[str, ...]
    purge: tuple[str, ...]
    """Blobs the folder purged after the copy was made: never placed, purged again after."""
    takes_home: bool
    """The folder takes the copy's `home_id`: it was new and empty, or he chose to replace."""

    @property
    def line(self) -> str:
        line = (
            f"the copy {self.stamp} from {self.where} is staged and checked, "
            f"{_count(self.files, 'file', 'files')}; {self.newer.line}, and the restore sets "
            "them aside. QMX finishes the restore when it next starts, or cancel it"
        )
        if self.lacks:
            line += f"; this copy lacks {', '.join(self.lacks)}"
        return line


@dataclass(frozen=True, slots=True)
class Finished:
    stamp: str
    where: str
    aside: Path
    """The folder the earlier `data/` was set aside in."""
    purge: tuple[str, ...]

    @property
    def line(self) -> str:
        return (
            f"QMX restored the copy {self.stamp} from {self.where}. The folder's earlier data is "
            f"set aside whole in {plain(self.aside)}. Server sync and fires stay paused until you "
            "carry on"
        )


@dataclass(frozen=True, slots=True)
class AfterRestore:
    """A finished restore he has not carried on from (or not reindexed after, for
    `pending_reindex`): server sync and fires stay paused meanwhile."""

    id: str
    stamp: str
    where: str
    aside: str
    """The set-aside folder, relative to the QMX folder."""
    purge: tuple[str, ...]
    lacks: tuple[str, ...]
    paused: bool
    """`paused` recorded the pause, with the value it replaced."""
    earlier: object
    """`autonomy.paused` as it was before the pause, to give back at carry-on."""


@dataclass(frozen=True, slots=True)
class Drilled:
    where: str
    stamp: str | None
    passed: bool | None
    """None when the drill did not run: no copy, or no room."""
    checked: int
    damaged: tuple[str, ...]
    line: str


@dataclass(frozen=True, slots=True)
class _Journal:
    copy: str
    id: str
    where: str
    key: str
    newest: str
    home_id: str
    label: Mapping[str, object]
    """The copy's `format_version`, `min_reader`, `last_written_by` and `stores`."""
    purge: tuple[str, ...]
    lacks: tuple[str, ...]
    step: str


@dataclass(frozen=True, slots=True)
class _Placing:
    entry: Entry
    how: How
    source: Path | None
    """For a link: the folder's own file, which hashed to the entry's sha256."""


def copies(repository: Repository) -> tuple[Copy, ...]:
    """Every copy at `repository` whose list of files is whole, newest first."""
    found: list[Copy] = []
    for stamp in reversed(repository.copies()):
        try:
            manifest = repository.manifest(stamp)
        except Unreadable:
            continue
        head = manifest.header
        found.append(
            Copy(
                stamp,
                str(head.get("why", "")),
                len(manifest.entries),
                sum(entry.size for entry in manifest.entries),
                str(head.get("release", "")),
                str(head.get("machine", "")),
                str(head.get("home_id", "")),
                str(head.get("folder", "")),
                head.get("partial") is True,
                _lacks(manifest),
            )
        )
    return tuple(found)


def newer_than(layout: Layout, stamp: str) -> Newer:
    """Read only: the runs started, Library ref moves, chats and price months in the folder that
    are newer than the copy `stamp` names."""
    since = when(stamp)
    data = layout.data
    return Newer(
        _runs_since(data / "engine" / "engine.sqlite", since),
        _moves_since(data / "library" / "refs" / "log.jsonl", since),
        sum(_changed_since(path, since) for path in (data / "chats").glob("*.json")),
        sum(_changed_since(path, since) for path in _states(data / "market")),
    )


def stage(
    layout: Layout,
    repository: Repository,
    stamp: str,
    *,
    replace: bool = False,
    keep_free: int = FLOOR_BYTES,
    progress: Callable[..., None] | None = None,
) -> Staged:
    """Rebuild `data/` from the copy `stamp` into `backups/restoring-<stamp>/data/` and check
    it. Raises RestoreRefused, with nothing of the folder changed, for a copy this release cannot
    restore, one of another QMX folder unless `replace` or the folder's `data/` is empty, a path
    that leaves `data/`, a file gone or damaged, too little room (keeping `keep_free` free), and
    while another restore waits. Raises Busy while a backup round runs."""
    told = progress or _quiet
    if not STAMP.fullmatch(stamp):
        raise RestoreRefused(f"{stamp!r} is not the date of a copy")
    with hold(layout.backups / LOCK, _round_busy(layout)):
        waiting = _read_journal(layout)
        if waiting is not None and waiting.step != "staging":
            raise RestoreRefused(_waits(layout, waiting))
        if waiting is not None:
            _clear(layout, waiting)
        told("checking the copy")
        repository.refresh()
        try:
            manifest = repository.manifest(stamp)
        except Unreadable as torn:
            raise RestoreRefused(f"{torn}; pick another copy") from None
        label = _label(layout)
        takes_home = _check(layout, repository, manifest, label, replace)
        live = _live_folder(layout, stamp)
        placing, stones, purge = _placings(layout, repository, manifest, live)
        need = sum(p.entry.size for p in placing if p.how == "fetch")
        room = free_bytes(layout.backups)
        if room - need < keep_free:
            raise RestoreRefused(
                f"restoring the copy {stamp} needs {_mb(need)} in {plain(layout.backups)} and its "
                f"drive has {_mb(room)} free; QMX keeps {_mb(keep_free)} free there. Free some "
                "space and try again"
            )
        newer = newer_than(layout, stamp)
        stamps = repository.copies()
        record = _Journal(
            stamp,
            _now_stamp(layout),
            repository.where,
            _key(layout, repository),
            stamps[-1] if stamps else stamp,
            str(manifest.header.get("home_id")) if takes_home else label.home_id,
            _copied_label(manifest, label),
            tuple(purge),
            _lacks(manifest),
            "staging",
        )
        _journal(layout, record)
        folder = _staging(layout, stamp) / "data"
        try:
            linked, copied = _place_all(folder, repository, manifest, placing, stones, told)
            told("checking the copy's stores")
            _check_rows(folder, manifest, repository.where)
        except BaseException:
            _clear(layout, record)
            raise
        finally:
            _let_go(repository)
        _journal(layout, _at(record, "staged"))
    return Staged(
        stamp,
        repository.where,
        folder,
        newer,
        len(placing) + len(stones),
        copied,
        linked,
        record.lacks,
        record.purge,
        takes_home,
    )


def finish(
    layout: Layout, *, running: Callable[[Path], int | None] | None = None
) -> Finished | None:
    """Put the staged copy in place, or complete a finish that was stopped; None when no restore
    is staged. `running(data)` is the pid of a live host the folder's record names (the host's
    own `recorded_host`; a reading of the record by default). Raises HostServes while QMX runs on
    the folder, RestoreRefused when the folder cannot be moved (nothing changes, the copy stays
    staged), and Busy while another finish or a backup round runs."""
    with (
        hold(
            layout.backups / RESTORE_LOCK,
            f"QMX is starting in {layout.root}, or finishing a restore there; try again when it "
            "has",
        ),
        hold(layout.backups / LOCK, _round_busy(layout)),
    ):
        record = _read_journal(layout)
        if record is None or record.step == "staging":
            return None
        _no_host(layout, running or _recorded_host)
        if record.step == PUTTING_BACK:
            _put_back(layout, record, _aside(layout, record))
            record = _at(record, "staged")
        for step in STEPS[STEPS.index(record.step) + 1 :]:
            record = _at(_step(layout, record, step), step)
            _journal(layout, record)
        shutil.rmtree(long_path(_staging(layout, record.copy)), ignore_errors=True)
        (layout.backups / JOURNAL).unlink(missing_ok=True)
    return Finished(record.copy, record.where, _aside(layout, record), record.purge)


def cancel(layout: Layout) -> str:
    """Drop a staged restore that has not begun to finish, first putting back the folder's data
    when a finish stopped right after setting it aside. The line to show. Raises
    RestoreRefused once a finish has begun: the next start completes it."""
    with hold(layout.backups / LOCK, _round_busy(layout)):
        record = _read_journal(layout)
        if record is None:
            return f"no restore is staged for {layout.root}"
        if record.step not in ("staging", "staged"):
            raise RestoreRefused(_waits(layout, record))
        _put_back(layout, record, _aside(layout, record))
        _clear(layout, record)
    return (
        f"the restore of the copy {record.copy} from {record.where} is cancelled; nothing in "
        f"{layout.root} changed"
    )


def after_restore(layout: Layout) -> AfterRestore | None:
    """The newest restore he has not carried on from, or None."""
    return _pending(layout, "restore-carried-on")


def pending_reindex(layout: Layout) -> AfterRestore | None:
    """The newest restore whose indexes have not been rebuilt, or None."""
    return _pending(layout, "reindexed")


def paused(layout: Layout, earlier: object) -> None:
    """Record that fires were paused after the newest restore, and `autonomy.paused` as it was
    before, for carry-on to give back."""
    found = after_restore(layout)
    if found is not None and not found.paused:
        log_line(layout, {"kind": "restore-paused", "id": found.id, "earlier": earlier})


def carried_on(layout: Layout) -> None:
    """His carry-on after the newest restore: server sync and fires may start again."""
    found = after_restore(layout)
    if found is not None:
        log_line(layout, {"kind": "restore-carried-on", "id": found.id})


def reindexed(layout: Layout) -> None:
    """The indexes were rebuilt after the newest restore."""
    found = pending_reindex(layout)
    if found is not None:
        log_line(layout, {"kind": "reindexed", "id": found.id})


def drill(
    layout: Layout,
    repository: Repository,
    *,
    sample: int,
    rng: random.Random,
    keep_free: int = FLOOR_BYTES,
    lock: Path | None = None,
) -> Drilled:
    """Restore a random copy's mutable files and `sample` of its pooled files written once into
    `cache/restore-drill/`, check their hashes, each store's `quick_check` and row counts, and
    remove the folder. A pooled file whose bytes are wrong goes on the storage's bad list, so the
    next round that holds the file sends it again and the next prune drops its pack. Never reads
    or writes `data/`. Logged as a `drill` line, which the keep rule reads. Raises Busy while a
    backup round runs."""
    where = repository.where
    held = lock or layout.backups / LOCK
    busy = _round_busy(layout) if lock is None else f"QMX is working on {where}; the drill waits"
    with hold(held, busy, removed=lock is not None):
        repository.refresh()
        readable: list[Manifest] = []
        for stamp in repository.copies():
            try:
                readable.append(repository.manifest(stamp))
            except Unreadable:
                continue
        if not readable:
            return Drilled(where, None, None, 0, (), f"{where} holds no copy to drill")
        manifest = rng.choice(readable)
        pooled = [entry for entry in manifest.entries if entry.at == "pool"]
        once = [entry for entry in pooled if entry.kind == "once"]
        chosen = [e for e in pooled if e.kind != "once"] + rng.sample(once, min(sample, len(once)))
        folder = layout.cache / DRILL
        need = sum(entry.size for entry in chosen)
        room = free_bytes(layout.cache)
        if room - need < keep_free:
            line = (
                f"the drill of {where} needs {_mb(need)} in {plain(folder)} and its drive has "
                f"{_mb(room)} free; it runs when there is room"
            )
            return Drilled(where, manifest.stamp, None, 0, (), line)
        shutil.rmtree(long_path(folder), ignore_errors=True)
        long_path(folder).mkdir(parents=True)
        damaged: list[str] = []
        try:
            for number, entry in enumerate(chosen):
                trouble = _drilled(repository, entry, folder / str(number))
                if trouble is not None:
                    damaged.append(f"{entry.path} ({trouble})")
        finally:
            shutil.rmtree(long_path(folder), ignore_errors=True)
            _let_go(repository)
        passed = not damaged
        log_line(
            layout,
            {
                "kind": "drill",
                "key": _key(layout, repository),
                "stamp": manifest.stamp,
                "passed": passed,
                "checked": len(chosen),
                "damaged": damaged,
            },
        )
    line = (
        f"the drill restored {_count(len(chosen), 'file', 'files')} of the copy {manifest.stamp} "
        f"from {where}, and "
        + ("every one checked" if passed else f"{', '.join(damaged)} did not check")
    )
    return Drilled(where, manifest.stamp, passed, len(chosen), tuple(damaged), line)


def _at(record: _Journal, step: str) -> _Journal:
    return replace(record, step=step)


def _check(
    layout: Layout, repository: Repository, manifest: Manifest, label: Label, replace_home: bool
) -> bool:
    """Refuse a copy this release must not restore here; whether the folder takes its
    `home_id`."""
    head, where, stamp = manifest.header, repository.where, manifest.stamp
    if head.get("format") not in READS:
        raise RestoreRefused(
            f"the copy {stamp} in {where} was made by a QMX whose copy format "
            f"({head.get('format')}) this QMX does not read; install that QMX to restore it, or "
            "pick another copy"
        )
    _check_label(head, where, stamp)
    for entry in manifest.entries:
        store = next((s for s in STORES.values() if s.path == entry.path), None)
        if store is None or store.kind != "sqlite" or entry.version is None:
            continue
        ours = store.release.version
        floor = entry.version if entry.min_reader is None else entry.min_reader
        if entry.version > ours and floor > ours:
            raise RestoreRefused(
                f"the copy {stamp} in {where} holds the {store.words} at version "
                f"{entry.version}, which needs a QMX that reads version {floor} or newer; this "
                f"QMX reads version {ours}. Install that QMX to restore this copy, or pick an "
                "older one"
            )
    seen: set[str] = set()
    for entry in manifest.entries:
        name = os.path.normcase(entry.path)
        if not _inside_data(entry.path) or name in seen:
            raise RestoreRefused(
                f"the copy {stamp} in {where} names {entry.path!r}, which is not a file QMX "
                "copies from data/; its list of files was changed by hand, so QMX does not "
                "restore it. Pick another copy"
            )
        seen.add(name)
    home_id = str(head.get("home_id"))
    if home_id == label.home_id:
        return _empty(layout.data)
    if not replace_home and not _empty(layout.data):
        raise RestoreRefused(
            f"the copy {stamp} in {where} is of another QMX folder ({head.get('folder')} on "
            f"{head.get('machine')}), not of {layout.root}. Choose replace to restore it here: "
            "this folder's data is set aside whole first"
        )
    return True


def _check_label(head: Mapping[str, object], where: str, stamp: str) -> None:
    """Refuse a copy whose label this release cannot read or must not open: its folder format,
    and each plain-file store's version, which only the label holds."""
    version, floor = head.get("format_version"), head.get("min_reader")
    by, stores = head.get("last_written_by"), head.get("stores")
    if not (
        _whole(version)
        and (floor is None or _whole(floor))
        and isinstance(by, str)
        and isinstance(stores, dict)
    ):
        raise RestoreRefused(
            f"the copy {stamp} in {where} carries a label this QMX cannot read; install the QMX "
            "that made it to restore it, or pick another copy"
        )
    copied = Label("", cast("int", version), by, by, cast("int | None", floor))
    if not opens(copied):
        reads = (
            f"needs a QMX that reads folder format {copied.reader_floor} or newer"
            if copied.format_version > TREE
            else "this QMX does not read"
        )
        raise RestoreRefused(
            f"the copy {stamp} in {where} was written by QMX {by} as folder format "
            f"{copied.format_version}, which {reads}; this QMX reads folder format {TREE}. "
            "Install that QMX to restore this copy, or pick another one"
        )
    for name, value in cast("dict[str, object]", stores).items():
        store = STORES.get(name)
        if store is None or store.kind != "files":
            continue
        found = _version_of(value)
        if found is None:
            raise RestoreRefused(
                f"the copy {stamp} in {where} says what version of the {store.words} it holds "
                "in a way this QMX cannot read; install the QMX that made it to restore it, or "
                "pick another copy"
            )
        ours = store.release.version
        if found.version > ours and found.min_reader > ours:
            raise RestoreRefused(
                f"the copy {stamp} in {where} holds the {store.words} at version "
                f"{found.version}, which needs a QMX that reads version {found.min_reader} or "
                f"newer; this QMX reads version {ours}. Install that QMX to restore this copy, or "
                "pick an older one"
            )


def _whole(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _version_of(value: object) -> Version | None:
    """A plain-file store's entry in a label's `[stores]`, as the label's own reader reads it."""
    match value:
        case {"version": int(at), "min_reader": int(floor)}:
            return Version(at, floor)
        case {"version": int(at)}:
            return Version(at, at)
        case _:
            return None


def _inside_data(path: str) -> bool:
    """Whether a manifest's path names a file QMX copies, inside `data/`: relative, `/` between
    names, no `..`, drive, backslash or stream, no name Windows would trim to another, and none
    QMX leaves out of a copy (a key above all)."""
    if not path or path.startswith("/") or "\\" in path or ":" in path:
        return False
    parts = path.split("/")
    if any(part in ("", ".", "..") or part != part.rstrip(". ") for part in parts):
        return False
    return left_out(path) is None


def _placings(
    layout: Layout, repository: Repository, manifest: Manifest, live: Path
) -> tuple[list[_Placing], list[tuple[str, Path]], list[str]]:
    """How each file of the copy is placed, the tombstones to place from the folder, and the
    blobs to purge again. A blob tombstoned in the copy or in the folder is never placed. A file
    written once that the folder still holds, with the copy's bytes, is linked from it."""
    paths = {entry.path for entry in manifest.entries}
    placing: list[_Placing] = []
    stones: list[tuple[str, Path]] = []
    purge: list[str] = []
    for entry in manifest.entries:
        blob = BORN_BLOB.fullmatch(entry.path)
        if blob is not None:
            stone = f"{TOMBSTONES}/{blob.group(3)}.json"
            if stone in paths:
                continue
            held = next(
                (f / stone for f in (layout.data, live) if long_path(f / stone).is_file()), None
            )
            if held is not None:
                if stone not in {s for s, _ in stones}:
                    stones.append((stone, held))
                    purge.append(f"sha256:{blob.group(3)}")
                continue
        if entry.at == "live":
            source = live / entry.path
            if not _holds(source, entry):
                raise RestoreRefused(
                    f"the quick-undo copy {manifest.stamp} needs {entry.path} as it was, and "
                    f"{plain(source)} is gone or changed since. Restore a copy from your second "
                    "drive instead"
                )
            placing.append(_Placing(entry, "link", source))
        elif entry.kind == "once" and _holds(layout.data / entry.path, entry):
            placing.append(_Placing(entry, "link", layout.data / entry.path))
        else:
            placing.append(_Placing(entry, "fetch", None))
    copied = [f"sha256:{m.group(1)}" for p in paths if (m := TOMBSTONE.fullmatch(p))]
    return placing, stones, list(dict.fromkeys([*sorted(copied), *purge]))


def _holds(path: Path, entry: Entry) -> bool:
    try:
        return long_path(path).stat().st_size == entry.size and sha256_of(path) == entry.sha256
    except OSError:
        return False


def _place_all(
    folder: Path,
    repository: Repository,
    manifest: Manifest,
    placing: Sequence[_Placing],
    stones: Sequence[tuple[str, Path]],
    told: Callable[..., None] | None = None,
) -> tuple[int, int]:
    """Place every file into the staged `folder`; the files linked and the bytes copied. The
    files fetched from the storage come first, counted in bytes, then the rest, counted in
    files."""
    linked = copied = 0
    made: set[Path] = set()
    told = told or _quiet
    fetched = [one for one in placing if one.source is None]
    rest = [one for one in placing if one.source is not None]
    fetching = f"fetching your copy from {repository.where}"
    total = sum(one.entry.size for one in fetched)
    told(fetching, done=0, total=total)
    for number, one in enumerate([*fetched, *rest]):
        if number == len(fetched):
            told("placing the copy's files", done=0, total=len(rest))
        elif number > len(fetched):
            told("placing the copy's files", done=number - len(fetched), total=len(rest))
        target = folder / one.entry.path
        if target.parent not in made:
            long_path(target.parent).mkdir(parents=True, exist_ok=True)
            made.add(target.parent)
        if one.source is not None and _link(one.source, target):
            linked += 1
            continue
        try:
            got = (
                copy_file(one.source, target)
                if one.source is not None
                else repository.fetch(one.entry.sha256, target)
            )
        except FileNotFoundError:
            raise RestoreRefused(
                f"the copy {manifest.stamp} in {repository.where} lacks {one.entry.path}: its "
                "file is missing there. Pick another copy; the next round copies the file again "
                "if the folder still holds it"
            ) from None
        if got != one.entry.sha256:
            raise RestoreRefused(
                f"{one.entry.path} in the copy {manifest.stamp} at {repository.where} does not "
                "hold the bytes the copy names: it is damaged there. Pick another copy"
            )
        copied += one.entry.size
        told(fetching, done=copied, total=total)
    if rest:
        told("placing the copy's files", done=len(rest), total=len(rest))
    for stone, source in stones:
        target = folder / stone
        long_path(target.parent).mkdir(parents=True, exist_ok=True)
        if not _link(source, target):
            copy_file(source, target)
    return linked, copied


def _link(source: Path, target: Path) -> bool:
    """A hard link; False where the drive refuses one, so the caller copies instead."""
    try:
        os.link(long_path(source), long_path(target))
    except OSError:
        return False
    return True


def _check_rows(folder: Path, manifest: Manifest, where: str) -> None:
    for entry in manifest.entries:
        if entry.kind == "store" and _rows(folder / entry.path) != dict(entry.tables):
            raise RestoreRefused(
                f"the {entry.path} the copy {manifest.stamp} at {where} holds does not count "
                "the rows its copy names. Pick another copy"
            )


def _rows(path: Path) -> dict[str, int]:
    with closing(sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)) as reading:
        names = [
            str(row[0])
            for row in reading.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        return {
            name: int(reading.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0])  # noqa: S608
            for name in sorted(names)
        }


def _step(layout: Layout, record: _Journal, step: str) -> _Journal:
    """Do one step of a finish, safe to run again; the journal record it leaves."""
    data, aside = layout.data, _aside(layout, record)
    if step == "set-aside":
        _set_aside(layout, aside)
    elif step == "moved-in":
        _move_in(layout, record, aside)
    elif step == "purges":
        return _purge_again(layout, record, aside)
    elif step.startswith("carried "):
        _carry(aside / "data" / step.removeprefix("carried "), data / step.removeprefix("carried "))
    elif step == "labelled":
        _relabel(layout, record)
    elif step == "logged" and not any(
        line.get("kind") == "restored" and line.get("id") == record.id for line in log_lines(layout)
    ):
        log_line(
            layout,
            {
                "kind": "restored",
                "id": record.id,
                "key": record.key,
                "stamp": record.newest,
                "copy": record.copy,
                "where": record.where,
                "aside": aside.relative_to(layout.root).as_posix(),
                "sync_paused": True,
                "fires_paused": True,
                "purge": list(record.purge),
                "lacks": list(record.lacks),
            },
        )
    return record


def _purge_again(layout: Layout, record: _Journal, aside: Path) -> _Journal:
    """Take out of the moved-in data every blob the set-aside data holds a tombstone for, place
    that tombstone and name the blob for a new purge: a blob he purged after the copy was
    staged never comes back."""
    stones = aside / "data" / TOMBSTONES
    named = [
        entry
        for entry in (os.scandir(long_path(stones)) if long_path(stones).is_dir() else ())
        if TOMBSTONE.fullmatch(f"{TOMBSTONES}/{entry.name}")
    ]
    found = sorted(entry.name for entry in named if entry.is_file(follow_symlinks=False))
    logged = {
        line.get("path")
        for line in log_lines(layout)
        if line.get("kind") == "restore-skipped" and line.get("id") == record.id
    }
    for entry in named:
        path = f"{TOMBSTONES}/{entry.name}"
        if not entry.is_file(follow_symlinks=False) and path not in logged:
            log_line(
                layout,
                {
                    "kind": "restore-skipped",
                    "id": record.id,
                    "path": path,
                    "line": f"{path} in the set-aside data is not a tombstone file, so the "
                    "restore left it there and purged nothing for it",
                },
            )
    purge = list(record.purge)
    for name in found:
        hexdigest = name.removesuffix(".json")
        blob = layout.data / "library" / "blobs" / hexdigest[:2] / hexdigest[2:4] / hexdigest
        long_path(blob).unlink(missing_ok=True)
        if not long_path(layout.data / TOMBSTONES / name).is_file():
            _copy_over(stones / name, layout.data / TOMBSTONES / name)
        if f"sha256:{hexdigest}" not in purge:
            purge.append(f"sha256:{hexdigest}")
    return replace(record, purge=tuple(purge))


def _set_aside(layout: Layout, aside: Path) -> None:
    data = layout.data
    if long_path(aside / "data").is_dir():
        if long_path(data).exists():
            raise RestoreRefused(_both(data, aside / "data"))
        return
    made = not long_path(aside).exists()
    long_path(aside).mkdir(parents=True, exist_ok=True)
    if long_path(layout.label).is_file():
        _put(aside / LABEL, long_path(layout.label).read_bytes())
    try:
        if long_path(data).exists():
            os.replace(long_path(data), long_path(aside / "data"))
        else:
            long_path(aside / "data").mkdir()
    except OSError as failed:
        if made:
            shutil.rmtree(long_path(aside), ignore_errors=True)
        raise RestoreRefused(_held_open(data, failed)) from None


def _move_in(layout: Layout, record: _Journal, aside: Path) -> None:
    data, staged = layout.data, _staging(layout, record.copy) / "data"
    if not long_path(staged).exists() and long_path(data).exists():
        return
    try:
        os.replace(long_path(staged), long_path(data))
    except OSError as failed:
        _journal(layout, _at(record, PUTTING_BACK))
        _put_back(layout, record, aside)
        raise RestoreRefused(_held_open(staged, failed)) from None


def _put_back(layout: Layout, record: _Journal, aside: Path) -> None:
    """Undo a set-aside whose move-in failed: the folder's data back in `data/`, the copy still
    staged. Safe to run again, so a finish stopped part way completes it."""
    data = layout.data
    if long_path(aside / "data").exists():
        if long_path(data).exists():
            raise RestoreRefused(_both(data, aside / "data"))
        try:
            os.replace(long_path(aside / "data"), long_path(data))
        except OSError as failed:
            raise RestoreRefused(
                f"QMX could not move the folder's earlier data back from {plain(aside / 'data')} "
                f"({failed.strerror or type(failed).__name__}); it waits whole there. Close any "
                "program using it; QMX puts it back when it next starts"
            ) from None
    if not long_path(aside / "data").exists():
        shutil.rmtree(long_path(aside), ignore_errors=True)
    _journal(layout, _at(record, "staged"))


def _both(data: Path, earlier: Path) -> str:
    return (
        f"both {plain(data)} and {plain(earlier)} exist, so QMX cannot tell which to keep and "
        f"changed nothing. {plain(earlier)} holds the folder's data from before the restore; if "
        f"{plain(data)} holds nothing you need, move it out of the QMX folder and start QMX again"
    )


def _carry(source: Path, target: Path) -> None:
    """Copy `source` (a file, or every file under a folder) over `target`, replacing what is
    there; the set-aside data keeps its own."""
    if long_path(source).is_file():
        _copy_over(source, target)
        return
    if not long_path(source).is_dir():
        return
    for folder, _, names in os.walk(long_path(source)):
        for name in names:
            inner = Path(folder, name).relative_to(long_path(source))
            if not os.path.islink(os.path.join(folder, name)):
                _copy_over(source / inner, target / inner)


def _copy_over(source: Path, target: Path) -> None:
    long_path(target.parent).mkdir(parents=True, exist_ok=True)
    writing = target.with_name(f"{target.name}{PARTIAL}")
    long_path(writing).unlink(missing_ok=True)
    copy_file(source, writing)
    os.replace(long_path(writing), long_path(target))


def _relabel(layout: Layout, record: _Journal) -> None:
    label = _label(layout)
    copied = record.label
    floor = copied.get("min_reader")
    stores = copied.get("stores")
    written = Label(
        record.home_id,
        int(cast("int", copied.get("format_version", label.format_version))),
        label.created_by,
        str(copied.get("last_written_by", label.last_written_by)),
        floor if isinstance(floor, int) else None,
        cast("dict[str, object]", stores) if isinstance(stores, dict) else dict(label.stores),
        label.extra,
    )
    _put(layout.label, written.dump().encode())


def _copied_label(manifest: Manifest, label: Label) -> dict[str, object]:
    head = manifest.header
    return {
        "format_version": head.get("format_version", label.format_version),
        "min_reader": head.get("min_reader", label.min_reader),
        "last_written_by": head.get("last_written_by", label.last_written_by),
        "stores": head.get("stores", dict(label.stores)),
    }


def _no_host(layout: Layout, running: Callable[[Path], int | None]) -> None:
    """Refuse while a host serves the folder: its record names a live process, or it holds
    `data/engine.lock`. The lock is let go at once, before any rename."""
    data = layout.data
    if not long_path(data).is_dir():
        return
    pid = running(data)
    lock = data / ENGINE_LOCK
    held = pid is not None
    if not held and lock.is_file():
        try:
            hold(lock, "").release()
        except Busy:
            held = True
    if held:
        who = "" if pid is None else f" (PID {pid})"
        raise HostServes(
            f"QMX is running on {layout.root}{who}; close it, then start QMX again to finish "
            "the restore"
        )


def _recorded_host(data: Path) -> int | None:
    """The pid the host's record in `data` names when that process still runs and started when
    the record says; None otherwise, and wherever the start time cannot be read."""
    try:
        record = json.loads((data / HOST_RECORD).read_text(encoding="utf-8"))
        pid, created = record["pid"], float(record["created"])
    except OSError, ValueError, KeyError, TypeError:
        return None
    if not isinstance(pid, int):
        return None
    started = _started(pid)
    return pid if started is not None and abs(started - created) < 0.01 else None


def _started(pid: int) -> float | None:
    """When the live process `pid` started, in seconds since the epoch, as psutil counts it."""
    if os.name == "nt":
        return _windows_started(pid)
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        boot = next(
            int(line.split()[1])
            for line in Path("/proc/stat").read_text(encoding="ascii").splitlines()
            if line.startswith("btime ")
        )
        ticks = int(stat.rpartition(")")[2].split()[19])
    except OSError, ValueError, IndexError, StopIteration:
        return None
    return boot + ticks / os.sysconf("SC_CLK_TCK")


def _windows_started(pid: int) -> float | None:
    import ctypes  # noqa: PLC0415
    from ctypes import wintypes  # noqa: PLC0415

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 259:
            return None
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel32.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
            return None
        ticks = times[0].dwHighDateTime << 32 | times[0].dwLowDateTime
        return ticks / 1e7 - 11_644_473_600
    finally:
        kernel32.CloseHandle(handle)


def _held_open(folder: Path, failed: OSError) -> str:
    return (
        f"QMX could not move {plain(folder)} ({failed.strerror or type(failed).__name__}): a "
        "program still has a file in it open. Close every QMX window and any program using that "
        "folder (a postgres left by Hindsight, an editor, a file browser), then start QMX again; "
        "nothing changed and the copy stays staged"
    )


def _pending(layout: Layout, cleared_by: str) -> AfterRestore | None:
    found: dict[str, object] | None = None
    done: set[object] = set()
    earlier: dict[object, object] = {}
    for line in log_lines(layout):
        kind = line.get("kind")
        if kind == "restored":
            found = line
        elif kind == cleared_by:
            done.add(line.get("id"))
        elif kind == "restore-paused":
            earlier[line.get("id")] = line.get("earlier")
    if found is None or found.get("id") in done:
        return None
    ident = found.get("id")
    return AfterRestore(
        str(ident),
        str(found.get("copy")),
        str(found.get("where")),
        str(found.get("aside")),
        tuple(str(b) for b in cast("list[object]", found.get("purge") or [])),
        tuple(str(f) for f in cast("list[object]", found.get("lacks") or [])),
        ident in earlier,
        earlier.get(ident),
    )


def _live_folder(layout: Layout, stamp: str) -> Path:
    """Where a quick-undo copy's files written once are: the data the first restore after the
    copy set aside, which is the data the copy was taken of, or else `data/`."""
    made = when(stamp)
    for line in log_lines(layout):
        if line.get("kind") != "restored":
            continue
        try:
            at = datetime.fromisoformat(str(line.get("at")))
        except ValueError:
            continue
        if at > made:
            return layout.root / str(line.get("aside")) / "data"
    return layout.data


def _drilled(repository: Repository, entry: Entry, target: Path) -> str | None:
    """What is wrong with one pooled file, restored to `target`, or None."""
    try:
        got = repository.fetch(entry.sha256, target)
    except FileNotFoundError:
        return f"missing from {repository.where}; the next round copies it again"
    if got != entry.sha256:
        repository.mark_bad(entry.sha256)
        return (
            f"damaged in {repository.where}, so QMX put it on the list of damaged files there; "
            "the next round sends it again"
        )
    if entry.kind != "store":
        return None
    try:
        with closing(sqlite3.connect(f"{target.resolve().as_uri()}?mode=ro", uri=True)) as db:
            check = db.execute("PRAGMA quick_check").fetchall()
        if check != [("ok",)]:
            return f"its SQLite check failed: {check[0][0]}"
        if _rows(target) != dict(entry.tables):
            return "its row counts differ from its copy's"
    except sqlite3.Error as broken:
        return f"it cannot be read as SQLite ({broken})"
    return None


def _runs_since(path: Path, since: datetime) -> int:
    if not path.is_file():
        return 0
    # With no -wal the file holds every commit; immutable reads it without leaving SQLite's
    # -wal and -shm beside a store no QMX has open.
    opened = "mode=ro" if path.with_name(f"{path.name}-wal").is_file() else "immutable=1"
    try:
        with closing(sqlite3.connect(f"{path.resolve().as_uri()}?{opened}", uri=True)) as db:
            moments = db.execute("SELECT at FROM events WHERE kind = 'run_created'").fetchall()
    except sqlite3.Error:
        return 0
    return sum(_after(str(at), since) for (at,) in moments)


def _moves_since(path: Path, since: datetime) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    count = 0
    for line in text.splitlines():
        try:
            move: object = json.loads(line)
        except ValueError:
            continue
        if isinstance(move, dict) and _after(str(cast("dict[str, object]", move).get("at")), since):
            count += 1
    return count


def _after(moment: str, since: datetime) -> bool:
    try:
        at = datetime.fromisoformat(moment)
    except ValueError:
        return False
    return (at if at.tzinfo else at.replace(tzinfo=UTC)) > since


def _changed_since(path: Path, since: datetime) -> bool:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, UTC) > since
    except OSError:
        return False


def _states(market: Path) -> list[Path]:
    return [
        Path(folder, "state.json") for folder, _, names in os.walk(market) if "state.json" in names
    ]


def _empty(data: Path) -> bool:
    """Whether `data/` holds no file: a folder just made."""
    return not any(names for _, _, names in os.walk(long_path(data)))


def _lacks(manifest: Manifest) -> tuple[str, ...]:
    head = manifest.header
    unread = [str(line) for line in cast("list[object]", head.get("unread") or [])]
    skipped = [
        f"{pair[0]} (its bytes were damaged when it was copied)"
        for pair in cast("list[list[str]]", head.get("skipped") or [])
    ]
    switched = [str(line) for line in cast("list[object]", head.get("left_out") or [])]
    return (*unread, *skipped, *switched)


def _key(layout: Layout, repository: Repository) -> str:
    """The place's key in the backup log, as a round writes it."""
    if isinstance(repository, FolderRepository) and os.path.normcase(
        os.path.abspath(repository.root)
    ) == os.path.normcase(os.path.abspath(layout.backups / "quick")):
        return QUICK
    return repository.key


def _let_go(repository: Repository) -> None:
    """Remove the pack a storage fetched last, so none stays on this PC."""
    let_go = getattr(repository, "let_go", None)
    if callable(let_go):
        let_go()


def _label(layout: Layout) -> Label:
    try:
        return Label.parse(long_path(layout.label).read_text(encoding="utf-8"))
    except (OSError, ValueError) as broken:
        raise RestoreRefused(
            f"the label {plain(layout.label)} cannot be read ({broken}); make the folder with "
            "QMX first, then restore into it"
        ) from None


def _staging(layout: Layout, stamp: str) -> Path:
    return layout.backups / f"{STAGING}{stamp}"


def _aside(layout: Layout, record: _Journal) -> Path:
    return layout.backups / f"{ASIDE}{record.id}"


def _now_stamp(layout: Layout) -> str:
    """A fresh id for a restore, named after the moment and never one set aside before."""
    moment = datetime.now(UTC)
    while True:
        stamp = moment.strftime("%Y%m%dT%H%M%S%fZ")
        if not (layout.backups / f"{ASIDE}{stamp}").exists():
            return stamp
        moment = moment.replace(microsecond=(moment.microsecond + 1) % 1_000_000)


def _journal(layout: Layout, record: _Journal) -> None:
    """Write the journal durably; a finish reads it to know the last step done."""
    document = {**asdict(record), "purge": list(record.purge), "lacks": list(record.lacks)}
    _put(layout.backups / JOURNAL, json.dumps(document, sort_keys=True).encode())


def _read_journal(layout: Layout) -> _Journal | None:
    path = layout.backups / JOURNAL
    try:
        raw = cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))
        record = _Journal(
            str(raw["copy"]),
            str(raw["id"]),
            str(raw["where"]),
            str(raw["key"]),
            str(raw["newest"]),
            str(raw["home_id"]),
            cast("dict[str, object]", raw["label"]),
            tuple(str(b) for b in cast("list[object]", raw["purge"])),
            tuple(str(f) for f in cast("list[object]", raw["lacks"])),
            str(raw["step"]),
        )
    except FileNotFoundError:
        return None
    except (OSError, ValueError, KeyError, TypeError) as broken:
        raise RestoreRefused(
            f"the restore journal {plain(path)} cannot be read ({broken}); nothing more is "
            "changed until it can"
        ) from None
    if record.step not in ("staging", PUTTING_BACK, *STEPS) or not STAMP.fullmatch(record.copy):
        raise RestoreRefused(f"the restore journal {plain(path)} names a step QMX does not make")
    return record


def _clear(layout: Layout, record: _Journal) -> None:
    shutil.rmtree(long_path(_staging(layout, record.copy)), ignore_errors=True)
    (layout.backups / JOURNAL).unlink(missing_ok=True)


def _waits(layout: Layout, record: _Journal) -> str:
    if record.step == "staged":
        return (
            f"a restore of the copy {record.copy} from {record.where} is staged and waits; QMX "
            f"finishes it when {layout.root} next starts, or cancel it first"
        )
    return (
        f"a restore of the copy {record.copy} into {layout.root} is half done; start QMX to "
        "finish it"
    )


def _round_busy(layout: Layout) -> str:
    return f"a backup round is running for {layout.root}; try again when it ends"


def _put(path: Path, data: bytes) -> None:
    """`data` in `path`, on the disk and in place whole when this returns."""
    writing = path.with_name(f"{path.name}{PARTIAL}")
    long_path(writing).unlink(missing_ok=True)
    write_new(writing, data)
    os.replace(long_path(writing), long_path(path))


def _count(count: int, one: str, many: str) -> str:
    return f"{count:,} {one if count == 1 else many}"


def _mb(count: int) -> str:
    return f"{max(count, 0) / (1 << 20):,.0f} MB"


def _quiet(_line: str, **_counts: int) -> None:
    return None
