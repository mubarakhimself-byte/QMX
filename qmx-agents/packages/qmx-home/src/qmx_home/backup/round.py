"""One round: a copy of `data/` into This PC's copies, then one send of that pinned copy to each
storage that is due (design 06 sections 4 and 5).

`copy_round` runs under `backups/backups.lock`, one at a time per QMX folder. It removes what a
killed round left, makes one copy (`snapshot.make`) of every class some place keeps into
`cache/sync-staging/<stamp>/`, and writes This PC's part of it into This PC's copies (when This
PC's copies are on and due, or a storage is due) unless nothing changed. What This PC's copies
now hold leaves the staging, so the staging keeps only the copy's list and the files This PC does
not keep. Each due storage then gets `send`: its own job, under its own lock
`backups/send-<id>.lock`, so a slow storage never holds This PC's copies, the drill or another
storage. A send reads the pinned copy from the staging and This PC's copies, sends the files the
storage lacks in packs, reads the storage's newest copy again just before its manifest and writes
none when another machine wrote since, then thins the storage by its keep rule. The staging goes
when the last send from it ends (`unstage`), and a staging left by a killed round goes at the next
round that finds no send running.

With `[backup] on = false` a round copies nothing and deletes nothing. Every round and every send
is one line in `backups/backups.jsonl`, which is also the record the fork guard and `due` read:
no other state file is kept. `run_round` does all of it in one call, for the command line.
"""

from __future__ import annotations

import os
import re
import shutil
import time as clock
import uuid
from collections.abc import Callable, Collection, Mapping, Sequence
from contextlib import ExitStack, suppress
from dataclasses import dataclass, replace
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Final, Literal, cast

from qmx_home import Label, Layout
from qmx_home.backup.keep import kept, released, when
from qmx_home.backup.plan import (
    NOT_SET_UP,
    Plan,
    PlanRefused,
    Storage,
    open_storage,
    same_drive,
    span,
    storage_key,
)
from qmx_home.backup.repository import (
    ABOUT,
    Entry,
    FolderRepository,
    Manifest,
    Mismatch,
    Repository,
    StorageRefused,
    Swept,
    Unreadable,
)
from qmx_home.backup.snapshot import (
    Changing,
    NoRoom,
    RoadLease,
    library_kinds,
    make,
    needs_kinds,
)
from qmx_home.backup.snapshot import only as part_for
from qmx_home.classes import SENT, Class, class_of
from qmx_home.files import GIB, Busy, floor_of, hold, long_path, plain
from qmx_home.rclone import Rclone
from qmx_home.versions import log_line, log_lines

LOCK: Final = "backups.lock"
QUICK: Final = "quick"
STAMP: Final = "%Y%m%dT%H%M%S%fZ"
STAGING: Final = "sync-staging"
FETCH: Final = "sync-fetch"
_STAMP: Final = re.compile(r"\d{8}T\d{12}Z")
OFF: Final = (
    "Sync to my storage is off in Settings, so QMX made no copy and deleted none; turn it on to "
    "copy again"
)
PC_OFF: Final = "copies on this PC are off in Settings, so the copy went only to your storages"
CHECKS: Final = 4
"""How many times a send reads the storage's lists for its copy's files: once before it writes
the copy, and after each write."""
STORAGE_FLOOR_GB: Final = 2
"""A storage that reports its size keeps at least this much free by default, or a tenth of
itself, whichever is larger. A floor that protects his storage, not a cap."""
STORAGE_FLOOR_SHARE: Final = 10

type Result = Literal["copied", "unchanged", "refused", "skipped"]


@dataclass(frozen=True, slots=True)
class Placed:
    """What one round did at one place, with its one line for him."""

    id: str
    where: str
    result: Result
    line: str
    key: str = QUICK
    stamp: str | None = None
    """The copy the place holds newest after the round."""
    files: int = 0
    bytes: int = 0
    seconds: float = 0.0
    partial: bool = False
    """The copy lacks a file it should hold; its manifest says which."""
    other_disk: bool = False
    """The place is a storage on another disk than the QMX folder's."""
    save: tuple[Class, ...] = SENT
    """The classes the place keeps."""
    tried: bool = True
    """Whether the round tried the place, so its next due round is counted from this one; a
    place skipped because it was not due, or with the main switch off, was not tried."""
    failure: str | None = None
    """Why a storage refused, sorted: `offline`, `signin`, `full`, `missing` or `other`."""
    torn: tuple[str, ...] = ()
    """Torn copies removed at the place, each older than its newest whole copy."""
    torn_index: tuple[str, ...] = ()
    """Index files at the place found torn, skipped and written again by the sweep."""

    def document(self) -> dict[str, object]:
        found: dict[str, object] = {
            "id": self.id,
            "key": self.key,
            "where": self.where,
            "result": self.result,
            "line": self.line,
            "stamp": self.stamp,
            "files": self.files,
            "bytes": self.bytes,
            "seconds": round(self.seconds, 3),
            "partial": self.partial,
            "other_disk": self.other_disk,
            "save": list(self.save),
            "tried": self.tried,
        }
        if self.failure is not None:
            found["failure"] = self.failure
        if self.torn:
            found["torn"] = list(self.torn)
        if self.torn_index:
            found["torn_index"] = list(self.torn_index)
        return found


@dataclass(frozen=True, slots=True)
class RoundReport:
    stamp: str
    why: str
    places: tuple[Placed, ...]
    seconds: float

    @property
    def result(self) -> Result:
        """`refused` when a place refused, `copied` when a place got a copy, else `unchanged`."""
        results = {place.result for place in self.places}
        for result in ("refused", "copied"):
            if result in results:
                return cast("Result", result)
        return "unchanged"

    @property
    def lines(self) -> tuple[str, ...]:
        return tuple(place.line for place in self.places)

    def document(self) -> dict[str, object]:
        return {
            "kind": "round",
            "stamp": self.stamp,
            "why": self.why,
            "result": self.result,
            "seconds": round(self.seconds, 3),
            "bytes": sum(place.bytes for place in self.places),
            "places": [place.document() for place in self.places],
        }


@dataclass(frozen=True, slots=True)
class Pinned:
    """The copy a round made, which each due storage's send reads: by its stamp, from the
    staging and This PC's copies."""

    stamp: str
    due: tuple[str, ...]
    """The storages to send it to, by place id."""


def due(last: datetime | None, now: datetime, every: timedelta, at: time) -> bool:
    """Whether a place tried last at `last` is due at `now`. Under a day: `every` after the
    last try. A day or more: at the first `at` (local time, in `now`'s zone) once `every` less a
    day has passed since the last try. A PC that was off is due at its next start."""
    if last is None:
        return True
    last = last.astimezone(now.tzinfo)
    if every < timedelta(days=1):
        return now - last >= every
    after = last + every - timedelta(days=1)
    slot = datetime.combine(after.date(), at, tzinfo=now.tzinfo)
    if slot <= after:
        slot += timedelta(days=1)
    return now >= slot


def run_round(
    layout: Layout,
    plan: Plan,
    *,
    now: datetime,
    floor: int,
    only: str | None = None,
    asked: bool = False,
    progress: Callable[[str], None] | None = None,
    road_lease: RoadLease | None = None,
    rclone: Rclone | None = None,
) -> RoundReport:
    """One round at `now`, every send in turn: This PC's copies when due or `asked` (he asked
    for the round), and every storage that is due (or only the storage `only`, due or not).
    `floor` is the local floor, which no write on this PC's drives crosses. `road_lease` holds a
    mini app's road lease while its `road/` is copied; `rclone` runs every rclone storage. Raises
    Busy while another round holds the lock, and PlanRefused when `only` names no storage."""
    started = clock.monotonic()
    report, pinned = copy_round(
        layout,
        plan,
        now=now,
        floor=floor,
        only=only,
        asked=asked,
        progress=progress,
        road_lease=road_lease,
    )
    if pinned is None:
        return report
    sent: list[Placed] = []
    told = progress or _quiet
    try:
        for place_id in pinned.due:
            try:
                sent += send(
                    layout,
                    plan,
                    place_id,
                    pinned.stamp,
                    progress=_steps(told),
                    rclone=rclone,
                    floor=floor,
                ).places
            except Busy as busy:
                sent.append(_busy_place(layout, plan, place_id, str(busy)))
    finally:
        unstage(layout, pinned.stamp)
    pc = [p for p in report.places if p.key == QUICK]
    rest = [p for p in report.places if p.key != QUICK]
    places = (*pc, *sent, *rest)
    return RoundReport(report.stamp, report.why, places, clock.monotonic() - started)


def quick(
    layout: Layout,
    why: str,
    *,
    floor: int,
    leave_out: Sequence[str] = (),
    now: datetime | None = None,
    road_lease: RoadLease | None = None,
) -> RoundReport:
    """One copy of every sent class into This PC's copies at once, tagged `why`, written even
    when nothing changed (a copy taken before an upgrade). It thins nothing: the next round thins
    by his own keep rule. Raises Busy while a round holds the lock."""
    report, pinned = copy_round(
        layout,
        Plan(leave_out=tuple(leave_out)),
        now=now or datetime.now(UTC),
        floor=floor,
        why=why,
        force=True,
        road_lease=road_lease,
    )
    if pinned is not None:
        unstage(layout, pinned.stamp)
    return report


def carry_on(layout: Layout, storage: Storage, *, rclone: Rclone | None = None) -> str:
    """His choice to keep sending to a storage the fork guard refused: the storage's newest copy
    is taken as this folder's own from now on. The line to show."""
    repo = open_storage(storage, layout, rclone=rclone)
    stamps = repo.copies()
    log_line(
        layout,
        {
            "kind": "carry-on",
            "id": storage.id,
            "key": repo.key,
            "stamp": stamps[-1] if stamps else None,
        },
    )
    return f"QMX carries on sending this folder's copies to {repo.where}"


def staging_of(layout: Layout, stamp: str) -> FolderRepository:
    """Where a round's copy waits for its sends."""
    return FolderRepository(layout.cache / STAGING / stamp)


def unstage(layout: Layout, stamp: str) -> None:
    """Remove a round's staging, once its last send ended."""
    shutil.rmtree(long_path(layout.cache / STAGING / stamp), ignore_errors=True)


def clear_scratch(layout: Layout, plan: Plan, *, keep: Collection[str] = ()) -> None:
    """Remove what killed rounds and sends left in `cache/sync-staging/` and `cache/sync-fetch/`,
    the stamps `keep` names left as they are; nothing while any storage's send runs."""
    with ExitStack() as locks:
        try:
            for storage in plan.sending:
                locks.enter_context(
                    hold(send_lock(layout, storage.id), "a send runs", removed=True)
                )
        except Busy:
            return
        for folder in (layout.cache / STAGING, layout.cache / FETCH):
            if not long_path(folder).is_dir():
                continue
            for entry in os.scandir(long_path(folder)):
                if entry.name not in keep:
                    shutil.rmtree(entry.path, ignore_errors=True)


def send_lock(layout: Layout, place_id: str) -> Path:
    """The lock one storage's jobs hold, so one QMX job at a time touches its copies."""
    return layout.backups / f"send-{place_id}.lock"


def copy_round(
    layout: Layout,
    plan: Plan,
    *,
    now: datetime,
    floor: int,
    why: str = "round",
    force: bool = False,
    only: str | None = None,
    asked: bool = False,
    progress: Callable[[str], None] | None = None,
    road_lease: RoadLease | None = None,
    held: Collection[str] = (),
) -> tuple[RoundReport, Pinned | None]:
    """This PC's part of a round: the copy made, This PC's copies written, and the copy pinned
    for each due storage's send. `held` names the stamps sends still read, which the round's
    thinning keeps. The report is logged; the pinned copy is None when no storage is due."""
    started = clock.monotonic()
    told = progress or _quiet
    busy = f"a backup round is already running for {layout.root}; it ends by itself"
    with hold(layout.backups / LOCK, busy):
        quick_repo = FolderRepository(layout.backups / QUICK, key=QUICK)
        torn = quick_repo.clean().torn
        clear_scratch(layout, plan, keep=held)
        log = log_lines(layout)
        home_id = _label(layout).home_id
        if only is not None and not any(s.id == only for s in plan.storages):
            raise PlanRefused(f"there is no storage {only!r} in Settings")
        unknown = tuple(
            Placed(
                s.id,
                s.shown,
                "skipped",
                NOT_SET_UP.format(name=s.name, via=s.via),
                storage_key(s, home_id),
                tried=False,
            )
            for s in plan.not_set_up
            if only is None or s.id == only
        )
        if not plan.on and not force:
            places = (
                Placed(QUICK, quick_repo.where, "skipped", OFF, tried=False),
                *(
                    Placed(s.id, s.shown, "skipped", OFF, storage_key(s, home_id), tried=False)
                    for s in plan.sending
                ),
            )
            stamp = _stamp(now, (quick_repo,), log)
            return _logged(layout, RoundReport(stamp, why, _at_pc(places, torn), 0.0)), None
        chosen = [
            storage
            for storage in plan.sending
            if (storage.id == only)
            or (
                only is None
                and storage.policy.on
                and due(
                    _tried(log, storage_key(storage, home_id)),
                    now,
                    storage.policy.interval,
                    storage.policy.at,
                )
            )
        ]
        pc_on = plan.pc.on or force
        pc_due = pc_on and (
            force
            or asked
            or only is not None
            or bool(chosen)
            or due(_tried(log, QUICK), now, plan.pc.interval, plan.pc.at)
        )
        stamp = _stamp(now, (quick_repo,), log)
        if not pc_due and not chosen:
            line = (
                "copies on this PC are off in Settings, and no storage is due"
                if not pc_on
                else f"This PC's copies are made every {plan.pc.every}; the newest in "
                f"{quick_repo.where} is not that old yet"
            )
            places = (Placed(QUICK, quick_repo.where, "skipped", line, tried=False), *unknown)
            return _logged(layout, RoundReport(stamp, why, _at_pc(places, torn), 0.0)), None
        previous = _newest(quick_repo) if pc_on else None
        saves = [*([plan.pc.save] if pc_due else []), *(s.policy.save for s in chosen)]
        union: tuple[Class, ...] = tuple(c for c in SENT if any(c in save for save in saves))
        kinds = library_kinds(layout.data) if needs_kinds(*saves) else {}
        staging = staging_of(layout, stamp)
        try:
            copy = make(
                layout,
                into=staging,
                have=quick_repo if pc_on else None,
                previous=previous,
                stamp=stamp,
                why=why,
                leave_out=plan.leave_out,
                save=union,
                kinds=kinds,
                keep_free=floor,
                progress=told,
                road_lease=road_lease,
            )
        except (NoRoom, Changing) as refused:
            unstage(layout, stamp)
            places = (
                Placed(QUICK, quick_repo.where, "refused", str(refused)),
                *(
                    Placed(
                        s.id,
                        s.shown,
                        "skipped",
                        f"no copy was made, so none went to {s.shown}",
                        storage_key(s, home_id),
                    )
                    for s in chosen
                ),
                *unknown,
            )
            return _logged(
                layout, RoundReport(stamp, why, _at_pc(places, torn), clock.monotonic() - started)
            ), None
        staging.put_copy(copy)
        if pc_due:
            placed = _quick_place(
                layout,
                quick_repo,
                staging,
                part_for(copy, plan.pc.save, kinds),
                previous,
                force,
                started,
            )
            _leave_staging(staging, quick_repo)
        else:
            placed = Placed(QUICK, quick_repo.where, "skipped", PC_OFF, tried=False)
        if not force and placed.result == "copied":
            placed = _thin_quick(quick_repo, plan, log, placed, {*held, stamp})
            _thin_pre_change(layout, log, [placed])
        places = _at_pc((placed, *unknown), torn)
        report = RoundReport(stamp, why, places, clock.monotonic() - started)
        _logged(layout, report)
    if not chosen:
        unstage(layout, stamp)
        return report, None
    return report, Pinned(stamp, tuple(s.id for s in chosen))


def _at_pc(places: tuple[Placed, ...], torn: tuple[str, ...]) -> tuple[Placed, ...]:
    """The round's places with This PC's torn copies, which its `clean` removed, on its line."""
    return tuple(replace(p, torn=torn) if p.key == QUICK and torn else p for p in places)


def send(
    layout: Layout,
    plan: Plan,
    place_id: str,
    stamp: str,
    *,
    progress: Callable[..., None] | None = None,
    rclone: Rclone | None = None,
    floor: int = 0,
    why: str = "round",
) -> RoundReport:
    """Send the pinned copy `stamp` to one storage, under that storage's lock, and log it as its
    own round line. Raises Busy while another job holds the storage, and PlanRefused when
    `place_id` names no storage."""
    started = clock.monotonic()
    storage = next((s for s in plan.storages if s.id == place_id), None)
    if storage is None:
        raise PlanRefused(f"there is no storage {place_id!r} in Settings")
    busy = f"QMX is already working on {storage.shown}; it ends by itself"
    home_id = _label(layout).home_id
    with hold(send_lock(layout, place_id), busy, removed=True):
        log = log_lines(layout)
        if not storage.opens:
            line = NOT_SET_UP.format(name=storage.name, via=storage.via)
            placed = Placed(
                storage.id,
                storage.shown,
                "skipped",
                line,
                storage_key(storage, home_id),
                tried=False,
            )
        else:
            placed = _send(layout, plan, storage, stamp, log, rclone, floor, progress or _quiet)
            _thin_pre_change(layout, log, [placed])
    return _logged(layout, RoundReport(stamp, why, (placed,), clock.monotonic() - started))


def _busy_place(layout: Layout, plan: Plan, place_id: str, line: str) -> Placed:
    storage = next(s for s in plan.storages if s.id == place_id)
    home_id = _label(layout).home_id
    return Placed(
        storage.id, storage.shown, "skipped", line, storage_key(storage, home_id), tried=False
    )


def _quick_place(
    layout: Layout,
    repo: FolderRepository,
    staging: FolderRepository,
    copy: Manifest,
    previous: Manifest | None,
    force: bool,
    started: float,
) -> Placed:
    """This PC's copy: each changed file packed from the staging, each file written once kept as
    a hard link, or by its place in `data/` where the drive refuses one."""
    if not force and previous is not None and previous.files == copy.files:
        line = f"nothing changed since the last copy; This PC's copies in {repo.where} hold it"
        return Placed(
            QUICK, repo.where, "unchanged", line, stamp=previous.stamp, partial=_partial(previous)
        )
    entries: list[Entry] = []
    unlinked = 0
    for entry in copy.entries:
        if entry.at == "live":
            if repo.pool_has(entry.sha256) or repo.link(entry.sha256, layout.data / entry.path):
                entries.append(replace(entry, at="pool"))
            else:
                entries.append(entry)
                unlinked += 1
            continue
        if not repo.pool_has(entry.sha256) and staging.loose(entry.sha256):
            repo.put_pool(entry.sha256, staging.pool_path(entry.sha256), path=entry.path)
        entries.append(entry)
    held = Manifest(copy.header, tuple(entries))
    repo.put_copy(held)
    old: frozenset[tuple[str, str]] = frozenset() if previous is None else previous.files
    new = [e for e in held.entries if (e.path, e.sha256) not in old]
    size = sum(e.size for e in new)
    line = (
        f"copied {_count(len(new), 'changed file')} ({_mb(size)}) into This PC's copies in "
        f"{repo.where}"
    ) + _lacks(cast("list[str]", copy.header.get("unread", [])))
    if unlinked:
        line += (
            f"; its drive refuses hard links, so {_count(unlinked, 'file')} written once "
            "stay only where they are in data/, and a file removed there cannot come back from "
            "This PC's copies"
        )
    return Placed(
        QUICK,
        repo.where,
        "copied",
        line,
        stamp=held.stamp,
        files=len(new),
        bytes=size,
        seconds=clock.monotonic() - started,
        partial=_partial(held),
    )


def _leave_staging(staging: FolderRepository, quick_repo: FolderRepository) -> None:
    """Remove from the staging each file This PC's copies now hold, so a send reads it there."""
    for path in staging._loose_files():  # pyright: ignore[reportPrivateUsage] - its own pool
        if quick_repo.pool_has(path.name):
            path.unlink(missing_ok=True)


def _send(
    layout: Layout,
    plan: Plan,
    storage: Storage,
    stamp: str,
    log: Sequence[Mapping[str, object]],
    rclone: Rclone | None,
    floor: int,
    told: Callable[..., None],
) -> Placed:
    """Send one pinned copy to one storage. A file whose bytes do not match its hash is left out
    of the storage's copy by name, and the copy is marked partial; the rest is sent. The send is
    logged as soon as its manifest is up, so a send killed later never makes this folder's own
    copy look like another folder's."""
    started = clock.monotonic()
    key = storage_key(storage, _label(layout).home_id)
    apart = not same_drive(storage, layout)
    unopened = ""
    try:
        repo = open_storage(storage, layout, rclone=rclone, keep_free=floor)
    except PlanRefused as refused:
        repo, unopened = None, str(refused)
    where = storage.shown if repo is None else repo.where

    def placed(
        result: Result,
        line: str,
        *,
        stamp: str | None = None,
        files: int = 0,
        size: int = 0,
        partial: bool = False,
        failure: str | None = None,
        torn: tuple[str, ...] = (),
        torn_index: tuple[str, ...] = (),
    ) -> Placed:
        return Placed(
            storage.id,
            where,
            result,
            line,
            key,
            stamp,
            files,
            size,
            clock.monotonic() - started,
            partial,
            apart,
            storage.policy.save,
            failure=failure,
            torn=torn,
            torn_index=torn_index,
        )

    if storage.path is not None and not Path(storage.path.anchor or "/").exists():
        return placed(
            "skipped",
            f"{plain(storage.path)} is not there (is its drive plugged in?); the copy waits for it",
        )
    if repo is None:
        return placed("skipped", unopened)
    scratch = layout.cache / FETCH / f"send-{storage.id}-{uuid.uuid4().hex[:8]}"
    try:
        return _sent(layout, plan, storage, stamp, log, repo, scratch, told, placed)
    except StorageRefused as refused:
        result: Result = "skipped" if refused.failure in ("offline", "missing") else "refused"
        lines = {
            "offline": f"{where} was not reached; check the connection. This PC's copies go on, "
            "and QMX tries it again at its next due round",
            "missing": f"{where} was not reached; connect it again in Settings, Sync to my storage",
            "signin": f"sign in to {where} again in Settings, Sync to my storage; This PC's "
            "copies go on",
        }
        line = lines.get(refused.failure, f"{refused}; QMX tries again at its next due round")
        return placed(result, line, failure=refused.failure)
    except OSError as failed:
        return placed(
            "refused", f"the copy to {where} stopped: {_why(failed)}; the next round tries again"
        )
    finally:
        _let_go(repo, scratch)


type _Place = Callable[..., Placed]


def _sent(
    layout: Layout,
    plan: Plan,
    storage: Storage,
    stamp: str,
    log: Sequence[Mapping[str, object]],
    repo: Repository,
    scratch: Path,
    told: Callable[..., None],
    placed: _Place,
) -> Placed:
    where, key = repo.where, repo.key
    quick_repo = FolderRepository(layout.backups / QUICK, key=QUICK)
    staging = staging_of(layout, stamp)
    pinned = _pinned(staging, quick_repo, stamp)
    if pinned is None:
        return placed(
            "skipped",
            f"the copy {stamp} this send was to read is gone from this PC; the next round "
            f"sends {where} a new one",
        )
    kinds = library_kinds(layout.data) if needs_kinds(storage.policy.save) else {}
    copy = part_for(pinned, storage.policy.save, kinds)
    refusal = _guard(log, key, repo)
    if refusal is not None:
        return placed("refused", refusal)
    cleaned = repo.clean()
    seen = repo.copies()[-1:]
    newest = _newest(repo)
    if (
        newest is not None
        and _intended(newest) == copy.files
        and all(repo.pool_has(entry.sha256) for entry in newest.entries)
    ):
        if repo.about() is None:
            repo.set_about(_about(layout, newest))
        return placed(
            "unchanged",
            f"nothing changed since the last copy to {where}",
            stamp=newest.stamp,
            partial=_partial(newest),
            torn=cleaned.torn,
        )
    unique = {entry.sha256: entry for entry in copy.entries}
    missing = [e for e in unique.values() if not repo.pool_has(e.sha256)]
    full = _full(repo, plan, sum(e.size for e in missing) + len(copy.dump()), copy, storage)
    if full is not None:
        return placed("refused", full, failure="full", torn=cleaned.torn)
    total = sum(e.size for e in missing)
    written, done, damaged = 0, 0, set[str]()
    told(f"sending the copy to {where}", done=0, total=total)
    for entry in missing:
        try:
            written += _put(repo, entry, staging, quick_repo, layout, scratch)
        except Mismatch:
            damaged.add(entry.sha256)
        done += entry.size
        told(f"sending the copy to {where}", done=done, total=total)
    repo.seal()
    if repo.copies()[-1:] != seen:
        return placed(
            "refused",
            f"another QMX folder with this one's id wrote a copy to {where} while this one was "
            "sending, so this copy was not written. Carry on to keep sending this folder's "
            "copies there, or pick another storage",
        )
    skipped = [e for e in copy.entries if e.sha256 in damaged]
    held = _without(copy, skipped)
    repo.set_about(_about(layout, held))
    again = _checked_copy(repo, held, staging, quick_repo, layout, scratch)
    if again is None:
        return placed(
            "refused",
            f"the copy to {where} stopped: files it names left {where} while it was sent, and "
            "this PC could not send them again; the next round tries again",
        )
    written += again
    log_line(layout, {"kind": "sent", "id": storage.id, "key": key, "stamp": held.stamp})
    try:
        swept = _thin(repo, storage, plan, log, key)
    except (OSError, StorageRefused) as failed:
        why = _why(failed) if isinstance(failed, OSError) else str(failed)
        swept = Swept(
            0, f"tidying {where} after the copy stopped ({why}); the next round tries again"
        )
    sent = len(missing) - len(damaged)
    line = f"copied {_count(sent, 'file')} ({_mb(written)}) to {where}"
    if same_drive(storage, layout):
        line += "; it is on the same drive as the QMX folder, so it does not survive that disk"
    if swept.blocked:
        line += f"; {swept.blocked}"
    line += _lacks(
        [
            *cast("list[str]", copy.header.get("unread", [])),
            *(f"{e.path} ({DAMAGED})" for e in skipped),
        ]
    )
    return placed(
        "copied",
        line,
        stamp=held.stamp,
        files=sent,
        size=written,
        partial=_partial(held),
        torn=cleaned.torn,
        torn_index=swept.torn,
    )


def _pinned(staging: FolderRepository, quick_repo: FolderRepository, stamp: str) -> Manifest | None:
    for repo in (staging, quick_repo):
        if stamp in repo.copies():
            try:
                return repo.manifest(stamp)
            except Unreadable:
                continue
    return None


def _checked_copy(
    repo: Repository,
    held: Manifest,
    staging: FolderRepository,
    quick_repo: FolderRepository,
    layout: Layout,
    scratch: Path,
) -> int | None:
    """Write `held` as a copy, then read the storage's lists again and send again each file it
    names that no named pack holds now: a prune can let a file's pack go and delete it while a
    send runs, however slow the send. The copy is taken down while a file is sent again, so it
    never stays naming a file that is gone. The bytes sent again; None, with the copy taken
    down, when a file cannot be sent again or the copy is still not whole after `CHECKS`."""
    written = 0
    files = {entry.sha256: entry for entry in held.entries}
    for attempt in range(CHECKS):
        repo.refresh()
        lost = [entry for sha, entry in files.items() if not repo.pool_has(sha)]
        if attempt > 0 and not lost:
            return written
        if attempt > 0:
            repo.drop(held.stamp)
        if attempt == CHECKS - 1:
            return None
        try:
            for entry in lost:
                written += _put(repo, entry, staging, quick_repo, layout, scratch)
        except Mismatch:
            return None
        repo.put_copy(held)
    return None


def _put(
    repo: Repository,
    entry: Entry,
    staging: FolderRepository,
    quick_repo: FolderRepository,
    layout: Layout,
    scratch: Path,
) -> int:
    """Send one file: from the staging, from This PC's copies, or from `data/` for a file written
    once that is kept only there."""
    if entry.at == "live" and not quick_repo.pool_has(entry.sha256):
        return repo.put_pool(entry.sha256, layout.data / entry.path, path=entry.path)
    if staging.loose(entry.sha256):
        return repo.put_pool(entry.sha256, staging.pool_path(entry.sha256), path=entry.path)
    if quick_repo.loose(entry.sha256):
        return repo.put_pool(entry.sha256, quick_repo.pool_path(entry.sha256), path=entry.path)
    long_path(scratch).mkdir(parents=True, exist_ok=True)
    target = scratch / uuid.uuid4().hex
    try:
        got = quick_repo.fetch(entry.sha256, target)
        if got != entry.sha256:
            raise Mismatch(f"{entry.path} is damaged in This PC's copies")
        return repo.put_pool(entry.sha256, target, path=entry.path)
    except FileNotFoundError:
        raise Mismatch(f"{entry.path} is gone from This PC's copies") from None
    finally:
        long_path(target).unlink(missing_ok=True)


def _let_go(repo: Repository | None, scratch: Path) -> None:
    abandon = getattr(repo, "abandon", None)
    if callable(abandon):
        abandon()
    let_go = getattr(repo, "let_go", None)
    if callable(let_go):
        with suppress(OSError):
            let_go()
    work = getattr(repo, "work", None)
    if isinstance(work, Path):
        shutil.rmtree(long_path(work), ignore_errors=True)
    shutil.rmtree(long_path(scratch), ignore_errors=True)


def _full(repo: Repository, plan: Plan, need: int, copy: Manifest, storage: Storage) -> str | None:
    """The refusal of a storage at its floor, before anything is written: the floor he set, or
    the larger of 2 GB and a tenth of the storage, and on a folder the local floor too. A kind
    that reports no free space has none."""
    room = repo.room()
    if room is None:
        return None
    total = repo.total()
    if storage.policy.floor is not None:
        keep_free = int(storage.policy.floor * GIB)
    else:
        keep_free = max(STORAGE_FLOOR_GB * GIB, (total or 0) // STORAGE_FLOOR_SHARE)
    if storage.via == "folder":
        keep_free = max(keep_free, floor_of(plan.floor_gb, room))
    if room - need >= keep_free:
        return None
    sizes: dict[str, int] = {}
    for entry in copy.entries:
        named = class_of(f"data/{entry.path}")
        sizes[named] = sizes.get(named, 0) + entry.size
    biggest = max(sizes, key=lambda c: sizes[c], default="content")
    return (
        f"{repo.where} needs {_mb(need)} for this copy and has {_mb(room)} free; QMX keeps at "
        f"least {_whole_mb(keep_free)} free there, so nothing was written. The biggest part of "
        f"what it keeps is {_CLASS_WORDS.get(biggest, biggest)} ({_mb(sizes.get(biggest, 0))}): "
        "free some space there, stop sending that to it in Settings, or connect another storage"
    )


_CLASS_WORDS: Final[Mapping[str, str]] = {
    "recipe": "your recipes",
    "content": "your content",
    "result": "your run results",
    "prices": "your prices",
}

DAMAGED: Final = (
    "it does not hold the bytes its name says: it changed while it was copied, or it is damaged"
)


def _without(copy: Manifest, skipped: Sequence[Entry]) -> Manifest:
    """The copy a storage holds: every file in its pool, less the files it could not take,
    which its header names, so the copy reads as partial and a later round knows what it meant
    to hold."""
    if not skipped:
        return copy.pooled()
    gone = {entry.path for entry in skipped}
    pooled = copy.pooled(partial=True, skipped=[[entry.path, entry.sha256] for entry in skipped])
    return Manifest(pooled.header, tuple(e for e in pooled.entries if e.path not in gone))


def _intended(manifest: Manifest) -> frozenset[tuple[str, str]]:
    """The files a copy meant to hold: those it holds and those its header says it lacks."""
    skipped = cast("list[list[str]]", manifest.header.get("skipped", []))
    return manifest.files | {(path, sha) for path, sha in skipped}


def _partial(manifest: Manifest) -> bool:
    return manifest.header.get("partial") is True


def _lacks(missing: Sequence[str]) -> str:
    if not missing:
        return ""
    return f"; this copy lacks {_count(len(missing), 'file')}: {', '.join(missing)}"


def _about(layout: Layout, copy: Manifest) -> dict[str, str]:
    """`backup.toml`: which folder sends here, and its newest copy."""
    return {
        "home_id": _label(layout).home_id,
        "folder": str(layout.root),
        "last_copy": copy.stamp,
        "written_by": str(copy.header.get("release", "")),
    }


def _guard(log: Sequence[Mapping[str, object]], key: str, repo: Repository) -> str | None:
    """Why a round must not send to this place (E-S7): another QMX folder with this one's id
    sent there since this one last did, or a place copied to before lost its `backup.toml`,
    which is another disk on the same letter or a storage emptied. His carry-on clears either."""
    events = _events(log, key)
    stamps = repo.copies()
    newest = stamps[-1] if stamps else None
    carried = bool(events) and events[-1] == ("carry-on", newest)
    if any(kind == "sent" for kind, _ in events) and repo.about() is None and not carried:
        return (
            f"{repo.where} is not the place QMX copied to before: its {ABOUT} is missing, so this "
            "may be another disk on the same drive letter. Plug in the disk QMX copied to, or "
            "carry on to copy there anyway"
        )
    ours = events[-1][1] if events else None
    if newest is not None and newest != ours:
        try:
            head = repo.manifest(newest).header
            made = f"{head.get('machine')} ({head.get('folder')})"
        except Unreadable:
            made = "another QMX folder"
        return (
            f"{repo.where} holds a copy another QMX folder made since this one last sent there: "
            f"the newest, {newest}, is from {made}. Carry on to keep sending this folder's copies "
            "there, or pick another storage"
        )
    return None


def _events(log: Sequence[Mapping[str, object]], key: str) -> list[tuple[str, str | None]]:
    """What this folder did at one place, oldest first: copies it sent (each logged as its
    manifest went up, and again in its round's line) or found unchanged, restores from it, and
    his carry-ons."""
    found: list[tuple[str, str | None]] = []
    for line in log:
        kind = line.get("kind")
        if kind == "round":
            for place in cast("list[dict[str, object]]", line.get("places", [])):
                if place.get("key") == key and place.get("result") in ("copied", "unchanged"):
                    found.append(("sent", cast("str | None", place.get("stamp"))))
        elif kind in ("sent", "carry-on", "restored") and line.get("key") == key:
            found.append((str(kind), cast("str | None", line.get("stamp"))))
    return found


def _tried(log: Sequence[Mapping[str, object]], key: str) -> datetime | None:
    """When a round last tried the place, whatever it answered: its next due round counts from
    then, so a storage that refused or was not there is tried again at its next due round. His
    carry-on since makes it due at once."""
    for line in reversed(log):
        if line.get("kind") == "carry-on" and line.get("key") == key:
            return None
        if line.get("kind") != "round":
            continue
        for place in cast("list[dict[str, object]]", line.get("places", [])):
            if place.get("key") == key and place.get("tried", place.get("result") != "skipped"):
                return when(str(line["stamp"]))
    return None


def _drilled(log: Sequence[Mapping[str, object]], key: str) -> str | None:
    """The newest copy at a place that passed a drill."""
    for line in reversed(log):
        if line.get("kind") == "drill" and line.get("key") == key and line.get("passed") is True:
            return cast("str | None", line.get("stamp"))
    return None


def safety_of(plan: Plan) -> timedelta:
    return span(plan.upkeep.safety)


def _thin(
    repo: Repository,
    storage: Storage,
    plan: Plan,
    log: Sequence[Mapping[str, object]],
    key: str,
) -> Swept:
    """Drop the copies the keep rule lets go, then sweep."""
    readable, whole = _readable(repo)
    keep = kept(list(readable), storage.policy.keep, drilled=_drilled(log, key), held=whole)
    for stamp in readable:
        if stamp not in keep:
            repo.drop(stamp)
    return repo.sweep(safety=safety_of(plan), now=datetime.now(UTC))


def _readable(repo: Repository) -> tuple[dict[str, Manifest], set[str]]:
    """The copies whose manifest is whole, oldest first, and the newest of them that is not
    partial. A copy whose manifest is not whole is never dropped, and neither is the newest
    complete copy, so copies that lack a file never thin away the last one that has them all."""
    readable: dict[str, Manifest] = {}
    for stamp in repo.copies():
        try:
            readable[stamp] = repo.manifest(stamp)
        except Unreadable:
            continue
    complete = [stamp for stamp, manifest in readable.items() if not _partial(manifest)]
    return readable, set(complete[-1:])


def _thin_quick(
    repo: FolderRepository,
    plan: Plan,
    log: Sequence[Mapping[str, object]],
    placed: Placed,
    pinned: Collection[str],
) -> Placed:
    elsewhere = _copies_elsewhere(log, [placed])
    readable, held = _readable(repo)
    held |= set(pinned)
    for stamp, manifest in readable.items():
        if manifest.header.get("why") == "before-upgrade" and not released(when(stamp), elsewhere):
            held.add(stamp)
    keep = kept(list(readable), plan.pc.keep, drilled=_drilled(log, QUICK), held=held)
    for stamp in readable:
        if stamp not in keep:
            repo.drop(stamp)
    swept = repo.sweep(safety=safety_of(plan), now=datetime.now(UTC))
    line = placed.line if swept.blocked is None else f"{placed.line}; {swept.blocked}"
    return replace(placed, line=line, torn_index=swept.torn)


def _thin_pre_change(
    layout: Layout, log: Sequence[Mapping[str, object]], placed: Sequence[Placed]
) -> None:
    """Remove each store's pre-change copy (LF3's `backups/pre-*`) once a whole copy made after
    it reached a storage on another disk."""
    elsewhere = _copies_elsewhere(log, placed)
    for line in log:
        if line.get("kind") != "pre-change":
            continue
        folder = layout.root / str(line.get("path", ""))
        if (
            folder.parent != layout.backups
            or not folder.name.startswith("pre-")
            or not folder.is_dir()
        ):
            continue
        made = datetime.fromisoformat(str(line["at"]))
        if released(made, elsewhere):
            shutil.rmtree(folder)


def _copies_elsewhere(
    log: Sequence[Mapping[str, object]], placed: Sequence[Placed]
) -> list[datetime]:
    """When each whole copy that reached a storage on another disk was made: one that lacks no
    file and holds every sent class. A log line older than `save` held them all."""
    rows = [
        place
        for line in log
        if line.get("kind") == "round"
        for place in cast("list[dict[str, object]]", line.get("places", []))
    ]
    rows += [p.document() for p in placed]
    return [
        when(str(row["stamp"]))
        for row in rows
        if row.get("id") != QUICK
        and row.get("result") == "copied"
        and row.get("other_disk") is True
        and row.get("partial") is not True
        and set(cast("list[str]", row.get("save", SENT))) >= set(SENT)
        and row.get("stamp")
    ]


def _newest(repo: Repository) -> Manifest | None:
    """The newest copy whose manifest is whole."""
    for stamp in reversed(repo.copies()):
        try:
            return repo.manifest(stamp)
        except Unreadable:
            continue
    return None


def _stamp(now: datetime, repos: Sequence[Repository], log: Sequence[Mapping[str, object]]) -> str:
    """The copy's stamp: `now` in UTC, after the newest copy in This PC's copies and after the
    last stamp in the backup log, which names every copy this folder sent anywhere, so a clock
    moved back never makes this folder's own copy look like another folder's."""
    stamp = now.astimezone(UTC).strftime(STAMP)
    seen = [s for repo in repos for s in repo.copies()[-1:]]
    seen += [str(line["stamp"]) for line in log if _STAMP.fullmatch(str(line.get("stamp", "")))]
    latest = max(seen, default=None)
    if latest is not None and stamp <= latest:
        stamp = (when(latest) + timedelta(microseconds=1)).strftime(STAMP)
    return stamp


def _label(layout: Layout) -> Label:
    return Label.parse(layout.label.read_text(encoding="utf-8"))


def _quiet(_line: str, **_counts: int) -> None:
    return None


def _steps(told: Callable[[str], None]) -> Callable[..., None]:
    """A progress that hears only the steps, for a caller that counts nothing."""

    def heard(step: str, **_counts: int) -> None:
        told(step)

    return heard


def _logged(layout: Layout, report: RoundReport) -> RoundReport:
    log_line(layout, report.document())
    return report


def _count(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def _mb(count: int) -> str:
    return f"{max(count, 0) / (1 << 20):,.1f} MB"


def _whole_mb(count: int) -> str:
    """As every floor refusal names the floor."""
    return f"{max(count, 0) / (1 << 20):,.0f} MB"


def _why(error: OSError) -> str:
    return f"{error.strerror or type(error).__name__}" + (
        f" ({plain(error.filename)})" if error.filename else ""
    )
