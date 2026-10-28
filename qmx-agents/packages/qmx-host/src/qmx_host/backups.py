"""The host makes his copies on its own (design 62 C2 and F step 14), and restores one from
Settings (C3).

Every minute the host reads `[backup]`, the storages in `[engine]` and the record in
`backups/backups.jsonl`. When This PC's copies are due (by its policy) or a storage he connected is
due and there, it runs one round as a `backup` job on its own thread, so a copy never holds a
request, and This PC's copies never take the folder's drive below the local floor. With
`[backup] on = false` it starts no round and no drill. A place he must act on has one open
inbox incident `backup:<place>`: a round it refused (no room, another QMX folder's copies, a
file that could not be read), a copy that lacks files, or a disk that has been away for seven of
its intervals. The next whole copy there resolves it. `[backup]` that cannot be read opens
`backup:settings`. The doctor row and `GET /api/backups` read the same record, which the command
line's rounds write too.

A restore from Settings is checked first (what it replaces, counted), then staged as a `restore`
job while the host serves, and finished at the next start, so no store is replaced under an open
connection. Until he carries on after it, server sync and fires stay paused. Once a month, when
no round is due, the drill restores a sample of one copy of each place in turn; a failed drill
opens `backup-drill:<place>`.

A round, a restore being staged and the drill each hold the folder's backup lock, so they run one
at a time.

Nothing is written outside the QMX folder until he connects a storage or accepts the proposed
second drive, which writes one `[engine]` place row that can keep, so the place never moves with
free space.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import sqlite3
import sys
import threading
import time as monotonic
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final, Literal, cast

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, JsonValue
from qma.harness.home import DoctorLine
from qmx_apps.errors import AppError
from qmx_apps.volume import VolumeLease
from qmx_control.models import Document
from qmx_control.service import ControlService
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.store import Reader
from qmx_engine.service.runs import status_of
from qmx_home import Label, Layout
from qmx_home.backup import restore
from qmx_home.backup.keep import when
from qmx_home.backup.plan import (
    KEEP_KEYS,
    NO_SECOND_DRIVE,
    Plan,
    PlanRefused,
    Policy,
    Proposal,
    Storage,
    parse,
    proposal,
    repository_of,
    same_drive,
    span,
)
from qmx_home.backup.repository import FolderRepository, Repository, Unreadable, free_bytes
from qmx_home.backup.restore import (
    ASIDE,
    AfterRestore,
    Drilled,
    RestoreRefused,
    _read_journal,  # pyright: ignore[reportPrivateUsage] - the staged restore's own record
    _waits,  # pyright: ignore[reportPrivateUsage] - and the line it waits with
)
from qmx_home.backup.round import (
    LOCK,
    QUICK,
    STAMP,
    Placed,
    RoundReport,
    _last,  # pyright: ignore[reportPrivateUsage] - the round's own record of a place's last copy
    carry_on,
    due,
    run_round,
    storage_key,
)
from qmx_home.backup.snapshot import RoadLease
from qmx_home.files import Busy, hold, plain
from qmx_home.versions import log_line, log_lines
from qmx_library.port import LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_host.jobs import Job, Jobs, Progress, Started, Stopped

KIND: Final = "backup"
RESTORE: Final = "restore"
DRILL: Final = "drill"
ROW: Final = "backups"
"""The doctor row's name."""
SWEEP_S: Final = 60.0
"""How often the host looks whether a place is due. The first look is one sweep after it serves,
so a start is never slowed by a copy."""
RETRY: Final = timedelta(hours=1)
"""A place that refused or was not there is tried again an hour after it was last tried."""
AWAY: Final = 7
"""Intervals with no copy before a place that is not there opens its incident."""
DRILL_INCIDENT: Final = "backup-drill:"
"""A failed drill's incident, per place. Not `backup:`, whose incidents follow the rounds."""
DOWNLOADS: Final = frozenset({"rclone"})
"""Kinds of place a drill downloads from, which a paid bucket may charge for (E-S19)."""
GOOD: Final = frozenset({"copied", "unchanged"})
SETTINGS: Final = "settings"
ENGINE: Final = cast("Any", "engine")
"""The engine's settings section, which the settings schema's Literal predates."""
PROPOSAL_S: Final = 3600.0
"""How long a measured proposal is shown before the drives are measured again."""
DEFAULT_TARGET: Final = "second-drive"
CLI_BUSY: Final = "a backup round from the command line holds this folder"
NOT_A_FOLDER: Final = (
    "this home is not a QMX folder (it has no qmx-home.toml), so QMX makes no copies of it"
)
EARLIEST: Final = datetime.min.replace(tzinfo=UTC)
ROAD_WAIT_S: Final = 60.0
"""A probe bound, not a cap: how long a round waits for a road step to let a mini app's road
lease go before it leaves that `road/` out of this copy, named; the next round tries again."""
ROAD_POLL_S: Final = 0.2
STORAGE_AT: Final = "03:00"
"""A storage's daily time until he changes it (Appendix D)."""
OFF_LINE: Final = (
    "Sync to my storage is off: QMX makes no copy anywhere, This PC included, and deletes none "
    "until you turn it on in Settings"
)

type Signature = Literal["refused", "partial", "away"]


class Refusal(Exception):
    """A backup route he must answer differently: the line says what to do, `status` is its
    HTTP status."""

    def __init__(self, line: str, status: int = 409) -> None:
        super().__init__(line)
        self.status = status


@dataclass(frozen=True, slots=True)
class Seen:
    """One round's record of one place."""

    at: datetime
    """When the round ran."""
    result: str
    line: str
    stamp: str | None
    """The copy the place holds newest after the round."""
    partial: bool


@dataclass(frozen=True, slots=True)
class Concern:
    """Why a place needs him: the incident's signature and its line."""

    signature: Signature
    line: str


@dataclass(frozen=True, slots=True)
class Standing:
    """What the backup log says about one place, oldest round first."""

    id: str
    where: str
    every: timedelta
    seen: tuple[Seen, ...]
    carried: bool
    """He carried on there after its last round."""
    on: bool = True

    @property
    def last(self) -> Seen | None:
        return self.seen[-1] if self.seen else None

    @property
    def complete(self) -> Seen | None:
        """The newest round that left the place holding a copy with every file."""
        return next(
            (s for s in reversed(self.seen) if s.result in GOOD and not s.partial and s.stamp),
            None,
        )

    def concern(self, now: datetime) -> Concern | None:
        """The incident this place should have open, or None. A round that skipped it (its disk
        was not there) decides nothing until seven intervals passed with no copy."""
        last = self.last
        if not self.on or last is None:
            return None
        if last.result == "skipped":
            good = next((s.at for s in reversed(self.seen) if s.result in GOOD), self.seen[0].at)
            if now - good >= AWAY * self.every:
                return Concern(
                    "away", f"{self.where} has had no copy for {_age(now - good)}: {last.line}"
                )
        decided = next((s for s in reversed(self.seen) if s.result != "skipped"), None)
        if decided is None or (decided.result in GOOD and not decided.partial):
            return None
        return Concern("refused" if decided.result == "refused" else "partial", decided.line)

    def ready(self, now: datetime) -> bool:
        """Whether a round may try the place now: it was never tried, its last round left a
        copy, an hour passed since a round it refused or missed, or he carried on since."""
        last = self.last
        if last is None or last.result in GOOD or self.carried:
            return True
        return now - last.at >= RETRY


def standing(
    log: Sequence[Mapping[str, object]],
    key: str,
    place_id: str,
    where: str,
    every: timedelta,
    *,
    on: bool = True,
) -> Standing:
    """One place's standing, read from the backup log."""
    seen: list[Seen] = []
    carried = False
    for line in log:
        kind = line.get("kind")
        if kind == "carry-on" and line.get("key") == key:
            carried = True
        if kind != "round":
            continue
        for place in cast("list[dict[str, object]]", line.get("places", [])):
            if place.get("key") != key:
                continue
            carried = False
            seen.append(
                Seen(
                    when(str(line["stamp"])),
                    str(place.get("result")),
                    str(place.get("line", "")),
                    cast("str | None", place.get("stamp")),
                    place.get("partial") is True,
                )
            )
    return Standing(place_id, where, every, tuple(seen), carried, on)


@dataclass(frozen=True, slots=True)
class Look:
    """The plan and the log as one sweep read them."""

    plan: Plan
    log: list[dict[str, object]]
    home_id: str
    places: list[Standing]
    """This PC first, then each folder storage in the plan's order."""


class Backups:
    """The host's backup service: the sweep, the jobs, the incidents, the doctor row, the view,
    a restore from Settings and the start after one, and the drill. `clock` is local time with
    its zone; `floor` the local floor on the folder's drive. `road_lease` holds a mini app's road
    lease while a round copies its `road/`."""

    def __init__(
        self,
        layout: Layout,
        control: ControlService,
        *,
        clock: Callable[[], datetime],
        floor: int,
        road_lease: RoadLease | None = None,
    ) -> None:
        self.layout = layout
        self.control = control
        self.clock = clock
        self.floor = floor
        self.road_lease = road_lease if road_lease is not None else road_lease_of(layout)
        self.jobs = Jobs()
        self.after: AfterRestore | None = None
        """The finished restore he has not carried on from: server sync and fires stay paused."""
        self._resume: Callable[[], object] | None = None
        self._asked: dict[str, bool] = {}
        self._raised: dict[str, Signature | None] = {}
        self._reconciled = False
        """Whether this process resolved the incidents of places removed while it was down."""
        self._raising = threading.Lock()
        self._starting = threading.Lock()
        """Held while a job is looked for and started, so two kinds never start side by side."""
        self._quick_bytes: int | None = None
        self._proposed: tuple[float, Proposal | None] | None = None
        self._interrupted: list[str] = []
        self._reindex: Literal["running", "failed"] | None = None
        self._reindex_line = ""
        self._hindsight = False
        self._aside_bytes: dict[str, int] = {}
        self._drill_tried: datetime | None = None
        self._drill_waits: Drilled | None = None
        """The newest drill that did not run for want of room."""

    async def run(self) -> None:
        """The sweep, every `SWEEP_S`, until the host stops."""
        while True:
            await asyncio.sleep(SWEEP_S)
            try:
                await asyncio.to_thread(self.sweep)
            except Exception as error:  # one bad sweep never ends the loop
                print(f"backups: a sweep failed: {type(error).__name__}: {error}", file=sys.stderr)

    def plan(self) -> Plan:
        return parse(
            self.control.settings_get("backup"), self.layout, self.control.settings_get(ENGINE)
        )

    def sweep(self) -> Job | None:
        """Bring the incidents in line with the log, then start a round when the quick undo, or
        a place that is there, is due, or else the drill when it is due. Returns the job it
        started."""
        if not self.layout.label.is_file():
            return None
        look = self._look()
        if look is None or not look.plan.on or self._busy() is not None:
            return None
        now = self.clock()
        pc = look.plan.pc
        quick_due = due(_last(look.log, QUICK), now, pc.interval, pc.at) and look.places[0].ready(
            now
        )
        ready = any(
            storage.policy.on
            and Path(_path(storage).anchor or "/").exists()
            and due(
                _last(look.log, storage_key(storage, look.home_id)),
                now,
                storage.policy.interval,
                storage.policy.at,
            )
            and place.ready(now)
            for storage, place in zip(look.plan.folders, look.places[1:], strict=True)
        )
        if not (quick_due or ready):
            return self._drill_if_due(look, now)
        try:
            started = self.start(None, asked=False)
        except Refusal:
            return None
        return started.job if started.new else None

    def start(self, only: str | None, *, asked: bool) -> Started:
        """A round as a `backup` job (to `only`, due or not, when named), or the round that
        already runs. Raises Refusal when the home is not a QMX folder, when `only` is not a place
        in Settings, while a restore is being staged or the drill runs, and while a round from the
        command line holds the folder."""
        if not self.layout.label.is_file():
            raise Refusal(NOT_A_FOLDER)
        if only is not None:
            self._storage(self.plan(), only)
        with self._starting:
            other = self._busy()
            if other is not None and other.kind != KIND:
                raise Refusal(self.busy_line(other))
            if other is None:
                self._unheld()
            started = self.jobs.start(KIND, lambda progress: self._round(only, progress, asked))
        if started.new:
            self._asked[started.job.id] = asked
        return started

    def busy_line(self, job: Job) -> str:
        if job.kind == RESTORE:
            return f"a restore is being staged (job {job.id}); it ends by itself, then ask again"
        if job.kind == DRILL:
            return (
                f"the monthly restore drill is checking a copy (job {job.id}); it ends by itself, "
                "then ask again"
            )
        who = "you started it" if self._asked.get(job.id) else "the schedule started it"
        return (
            f"a backup round is already running (job {job.id}, {who}); it ends by itself, "
            "then ask again"
        )

    def _busy(self) -> Job | None:
        """The round, the restore being staged or the drill that runs now."""
        for kind in (KIND, RESTORE, DRILL):
            latest = self.jobs.latest(kind)
            if latest is not None and latest.state == "running":
                return latest
        return None

    def _unheld(self) -> None:
        """Raise Refusal while a round from the command line holds the folder's backup lock."""
        try:
            with hold(self.layout.backups / LOCK, CLI_BUSY):
                pass
        except Busy:
            raise Refusal(
                "a backup round from the command line (python -m qmx_host backup) is copying "
                f"{self.layout.root}; it ends by itself, then ask again"
            ) from None

    def _round(self, only: str | None, progress: Progress, asked: bool) -> Mapping[str, object]:
        try:
            report = run_round(
                self.layout,
                self.plan(),
                now=self.clock(),
                floor=self.floor,
                only=only,
                asked=asked,
                progress=progress,
                road_lease=self.road_lease,
            )
        except (Busy, PlanRefused) as refused:
            raise Stopped(str(refused)) from None
        except Exception as error:  # a round that broke is logged like one that refused
            line = (
                f"the round stopped with an error: {type(error).__name__}: {error}; QMX tries "
                "again in an hour"
            )
            self._log_failed(only, line)
            raise Stopped(line) from None
        finally:
            self._settle()
        return report.document()

    def _log_failed(self, only: str | None, line: str) -> None:
        """A round line for a round that broke: the quick undo refused with `line`, and each place
        the round was to send to skipped, so the hourly retry and the incidents read it as they
        read a refusal."""
        now = self.clock()
        try:
            plan = self.plan()
        except PlanRefused:
            plan = Plan()
        log, home_id = log_lines(self.layout), self._home_id()
        quick = FolderRepository(self.layout.backups / QUICK)
        places = [Placed(QUICK, quick.where, "refused", line)]
        for storage in plan.folders:
            key = storage_key(storage, home_id)
            policy = storage.policy
            if storage.id == only or (
                only is None and policy.on and due(_last(log, key), now, policy.interval, policy.at)
            ):
                where = plain(storage.path)
                places.append(
                    Placed(
                        storage.id,
                        where,
                        "skipped",
                        f"no copy was made, so none went to {where}",
                        key,
                    )
                )
        stamp = now.astimezone(UTC).strftime(STAMP)
        log_line(self.layout, RoundReport(stamp, "round", tuple(places), 0.0).document())

    def _settle(self) -> None:
        """After a round: the quick undo's size, and the incidents the log now calls for."""
        self._quick_bytes = _size(self.layout.backups / QUICK)
        try:
            self._look()
        except (OSError, sqlite3.Error) as error:
            print(f"backups: incidents not updated: {error}", file=sys.stderr)

    def _look(self) -> Look | None:
        """Read the plan and the log and bring each place's incident in line with them. None
        when `[backup]` cannot be read, which is then the incident."""
        now = self.clock()
        try:
            plan = self.plan()
        except PlanRefused as refused:
            self._raise({SETTINGS: Concern("refused", str(refused))}, every_place=False)
            return None
        log, home_id = log_lines(self.layout), self._home_id()
        places = self._standings(plan, log, home_id)
        self._raise({SETTINGS: None, **{p.id: p.concern(now) for p in places}}, every_place=True)
        return Look(plan, log, home_id, places)

    def _raise(self, wanted: Mapping[str, Concern | None], *, every_place: bool) -> None:
        """Open, keep or resolve `backup:<place>` for each place named. The inbox is touched
        only when a place's signature changed since this process last looked, and once per place
        after a start, so a sweep every minute adds nothing to an incident's count. With
        `every_place`, a place no longer in Settings has its incident resolved."""
        with self._raising:
            changed = {
                place: concern
                for place, concern in wanted.items()
                if place not in self._raised
                or self._raised[place] != (concern.signature if concern else None)
            }
            gone: set[str] = set()
            if every_place:
                gone = {p for p, s in self._raised.items() if p not in wanted and s is not None}
            if not changed and not gone:
                return
            at = self.clock().astimezone(UTC).isoformat()
            with InboxTable.open(self.layout.home) as inbox:
                for place, concern in changed.items():
                    trigger = f"backup:{place}"
                    found = inbox.open_incident(trigger)
                    if concern is None:
                        if found is not None:
                            inbox.resolve_incident(trigger, at=at)
                    elif found is None or found.signature != concern.signature:
                        inbox.incident(
                            trigger, concern.signature, _title(place), concern.line, at=at
                        )
                    self._raised[place] = concern.signature if concern else None
                if every_place and not self._reconciled:
                    gone |= {p for p in _open_places(inbox) if p not in wanted}
                    self._reconciled = True
                for place in gone:
                    inbox.connection.execute(
                        "UPDATE incidents SET cause = ?, resolved_at = ?"
                        " WHERE trigger_id = ? AND resolved_at IS NULL",
                        (
                            f"the backup place {place} is no longer in Settings, so QMX no longer "
                            "copies there",
                            at,
                            f"backup:{place}",
                        ),
                    )
                    self._raised[place] = None

    def _running(self) -> Job | None:
        latest = self.jobs.latest(KIND)
        return latest if latest is not None and latest.state == "running" else None

    def view(self) -> dict[str, object]:
        """`GET /api/backups`: the plan, the proposal, each place's last round and newest whole
        copy, the quick undo's size and the round that runs; a staged restore, the pause after a
        restore with the runs it holds, and the folders earlier restores set aside."""
        running = self._running()
        found: dict[str, object] = {
            "folder": str(self.layout.root),
            "running": None if running is None else running.document(),
        }
        if not self.layout.label.is_file():
            return {**found, "refused": NOT_A_FOLDER, "places": []}
        restoring = {
            "restore": self._staged_document(),
            "after_restore": self._after_document(),
            "set_aside": self._set_aside_document(),
        }
        try:
            plan = self.plan()
        except PlanRefused as refused:
            return {
                **found,
                "refused": f"[backup] in Settings: {refused}",
                "places": [],
                **restoring,
            }
        now = self.clock()
        places = self._standings(plan, log_lines(self.layout), self._home_id())
        offered = self._proposal(plan)
        return {
            **found,
            "refused": None,
            "on": plan.on,
            "line": None if plan.folders else NO_SECOND_DRIVE,
            "proposal": None
            if offered is None
            else {"path": str(offered.path), "line": offered.line},
            "quick_undo_bytes": self._quick_size(),
            "places": [
                _place_document(place, storage, now, self.layout, plan)
                for place, storage in zip(places, (None, *plan.folders), strict=True)
            ],
            **restoring,
        }

    def _staged_document(self) -> dict[str, object]:
        """The restore being staged, or staged and waiting for the next start."""
        job = self.jobs.latest(RESTORE)
        shown = None if job is None else job.document()
        try:
            record = _read_journal(self.layout)
        except RestoreRefused as broken:
            return {"job": shown, "staged": None, "line": str(broken)}
        if record is None or record.step == "staging":
            return {"job": shown, "staged": None, "line": None}
        return {
            "job": shown,
            "staged": {
                "copy": record.copy,
                "where": record.where,
                "aside": f"backups/{ASIDE}{record.id}",
                "finishing": record.step != "staged",
            },
            "line": _waits(self.layout, record),
        }

    def _after_document(self) -> dict[str, object] | None:
        found = self.after
        if found is None:
            return None
        return {
            "copy": found.stamp,
            "where": found.where,
            "aside": found.aside,
            "interrupted": list(self._interrupted),
            "recall": self._recall_line(),
            "line": _paused_line(found, self._interrupted),
        }

    def _set_aside_document(self) -> dict[str, object]:
        """The folders earlier restores set aside, which QMX never deletes, and their total beside
        the drive's free room (E-S13)."""
        folders = sorted(
            path
            for path in self.layout.backups.glob(f"{ASIDE}*")
            if path.is_dir() and not path.is_symlink()
        )
        rows: list[dict[str, object]] = []
        for path in folders:
            if path.name not in self._aside_bytes:
                self._aside_bytes[path.name] = _size(path)
            rows.append({"folder": f"backups/{path.name}", "bytes": self._aside_bytes[path.name]})
        total = sum(self._aside_bytes[path.name] for path in folders)
        free = free_bytes(self.layout.backups)
        line = None
        if rows:
            line = (
                f"{_count(len(rows), 'folder', 'folders')} set aside by earlier restores "
                f"{'holds' if len(rows) == 1 else 'hold'} {_mb(total)} in "
                f"{plain(self.layout.backups)}, and its drive has {_mb(free)} free. QMX never "
                "deletes them; move or delete one yourself once you no longer need the work in it"
            )
        return {"folders": rows, "bytes": total, "free_bytes": free, "line": line}

    def _recall_line(self) -> str | None:
        if self._reindex == "running":
            line = "recall is partial while QMX rebuilds its memory index after the restore"
            if self._hindsight:
                line += (
                    "; Hindsight starts its database and embeds every row again, which takes a "
                    "while"
                )
            return line
        if self._reindex == "failed":
            return (
                f"recall is partial: the memory rebuild after the restore stopped "
                f"({self._reindex_line}); QMX runs it again at the next start"
            )
        return None

    def doctor_line(self) -> DoctorLine:
        """The doctor's `backups` row: the pause after a restore, recall while memory is rebuilt,
        each place's newest whole copy and what needs him, and each place's newest drill."""
        if not self.layout.label.is_file():
            return DoctorLine(ROW, False, NOT_A_FOLDER)
        try:
            plan = self.plan()
        except PlanRefused as refused:
            return DoctorLine(ROW, False, f"QMX makes no copies: [backup] in Settings: {refused}")
        now = self.clock()
        log = log_lines(self.layout)
        places = self._standings(plan, log, self._home_id())
        parts = [_doctor_part(place, now) for place in places]
        parts[0] += (
            f", {_mb(self._quick_size())} in all, {_policy_line(plan.pc)}"
            + _skipped_with_quick(log)
        )
        if not plan.folders:
            offered = self._proposal(plan)
            parts.append(NO_SECOND_DRIVE + (f"; {offered.line}" if offered else ""))
        drills, failed = self._drill_parts(plan, log, now)
        recall = self._recall_line()
        first = [
            *([] if plan.on else [OFF_LINE]),
            *([] if self.after is None else [_paused_line(self.after, self._interrupted)]),
            *([] if recall is None else [recall]),
        ]
        ok = (
            bool(plan.folders)
            and all(place.concern(now) is None for place in places)
            and not first
            and not failed
        )
        return DoctorLine(ROW, ok, "; ".join([*first, *parts, *drills]))

    def _drill_parts(
        self, plan: Plan, log: Sequence[Mapping[str, object]], now: datetime
    ) -> tuple[list[str], bool]:
        """Each place's newest drill, what a drill there costs, and whether a newest drill
        failed."""
        home_id = self._home_id()
        names = {QUICK: ("This PC's copies", "folder")} | {
            storage_key(s, home_id): (s.id, s.via) for s in plan.folders
        }
        newest: dict[str, Mapping[str, object]] = {}
        for line in log:
            if line.get("kind") == "drill" and str(line.get("key")) in names:
                newest[str(line.get("key"))] = line
        parts: list[str] = []
        for key, line in newest.items():
            name = names[key][0]
            age = _age(now - _logged_at(line))
            if line.get("passed") is True:
                parts.append(
                    f"the restore drill of {name} checked the copy {line.get('stamp')} {age} ago"
                )
            else:
                damaged = ", ".join(str(d) for d in cast("list[object]", line.get("damaged") or []))
                parts.append(
                    f"the restore drill of {name} {age} ago found the copy {line.get('stamp')} "
                    f"damaged, and it needs you: {damaged}"
                )
        if self._drill_waits is not None:
            parts.append(self._drill_waits.line)
        parts += [
            f"the monthly drill of {name} downloads a sample of one copy from there, which a "
            "paid bucket may charge for"
            for name, kind in names.values()
            if kind in DOWNLOADS
        ]
        return parts, any(line.get("passed") is not True for line in newest.values())

    def copies(self, place_id: str) -> list[dict[str, object]]:
        """Each copy one place holds, oldest first, with what made it."""
        repo = self._repository(self.plan(), place_id)
        found: list[dict[str, object]] = []
        for stamp in repo.copies():
            try:
                copy = repo.manifest(stamp)
            except Unreadable as damaged:
                found.append({"stamp": stamp, "readable": False, "line": str(damaged)})
                continue
            found.append(
                {
                    "stamp": stamp,
                    "readable": True,
                    "why": copy.header.get("why"),
                    "files": len(copy.entries),
                    "bytes": sum(entry.size for entry in copy.entries),
                    "release": copy.header.get("release"),
                    "machine": copy.header.get("machine"),
                    "partial": copy.header.get("partial") is True,
                }
            )
        return found

    def carry_on(self, place_id: str) -> str:
        """His choice to keep sending to a storage the fork guard refused. The next sweep tries
        it again at once."""
        return carry_on(self.layout, self._storage(self.plan(), place_id))

    def accept(self) -> dict[str, object]:
        """His yes to the proposed second drive: one `[engine]` place row that can keep, at its
        path. Its policy is the storage defaults until he changes one."""
        if self.plan().folders:
            raise Refusal(
                "you already connected a storage; change it in Settings, Sync to my storage"
            )
        offered = proposal(self.layout)
        if offered is None:
            raise Refusal(NO_SECOND_DRIVE)
        row: Document = {
            "id": DEFAULT_TARGET,
            "via": "folder",
            "can": ["keep"],
            "path": str(offered.path),
        }

        def added(section: Document) -> Document:
            placement = _table(section.get("placement"))
            return {**section, "placement": {**placement, DEFAULT_TARGET: row}}

        self.control.settings_update(ENGINE, added)
        self._proposed = None
        at = STORAGE_AT
        return {
            "target": row,
            "line": f"QMX copies your work to {offered.path} every day at {at}; the first copy "
            "is made at the next round, within a few minutes",
        }

    def check_restore(self, body: object) -> dict[str, object]:
        """What restoring one copy would replace, counted, for him to see before he confirms."""
        place_id, stamp = _restore_body(body, confirm=False)
        repo = self._repository(self.plan(), place_id)
        found = next((c for c in restore.copies(repo) if c.stamp == stamp), None)
        if found is None:
            raise Refusal(
                f"{repo.where} holds no whole copy {stamp}; pick one of the copies listed there",
                404,
            )
        newer = restore.newer_than(self.layout, stamp)
        line = (
            f"{newer.line}; restoring the copy {stamp} sets the folder's data aside whole in "
            f"{plain(self.layout.backups)} first, and QMX finishes the restore when it next starts"
        )
        if found.lacks:
            line += f"; this copy lacks {', '.join(found.lacks)}"
        return {
            "target": place_id,
            "copy": stamp,
            "where": repo.where,
            "why": found.why,
            "files": found.files,
            "bytes": found.bytes,
            "partial": found.partial,
            "lacks": list(found.lacks),
            "newer": {
                "runs": newer.runs,
                "ref_moves": newer.ref_moves,
                "chats": newer.chats,
                "price_months": newer.price_months,
            },
            "line": line,
        }

    def stage_restore(self, body: object) -> Job:
        """His confirmed restore of one copy, staged as a `restore` job while the host serves.
        Raises Refusal while a round, the drill or another restore runs, while a staged restore
        waits, and while a round from the command line holds the folder."""
        place_id, stamp = _restore_body(body, confirm=True)
        repo = self._repository(self.plan(), place_id)
        with self._starting:
            busy = self._busy()
            if busy is not None:
                raise Refusal(self.busy_line(busy))
            waiting = _read_journal(self.layout)
            if waiting is not None and waiting.step != "staging":
                raise Refusal(_waits(self.layout, waiting))
            self._unheld()
            started = self.jobs.start(RESTORE, lambda progress: self._stage(repo, stamp, progress))
        return started.job

    def _stage(self, repo: Repository, stamp: str, progress: Progress) -> Mapping[str, object]:
        try:
            staged = restore.stage(
                self.layout,
                repo,
                stamp,
                keep_free=self.floor,
                progress=progress,
            )
        except (RestoreRefused, Busy) as refused:
            raise Stopped(str(refused)) from None
        record = _read_journal(self.layout)
        aside = f"backups/{ASIDE}{'' if record is None else record.id}"
        return {
            "restart": True,
            "copy": stamp,
            "where": staged.where,
            "aside": aside,
            "files": staged.files,
            "bytes": staged.bytes,
            "linked": staged.linked,
            "lacks": list(staged.lacks),
            "staged": staged.line,
            "line": f"Restart QMX to finish the restore; the work it replaces is set aside in "
            f"{aside}",
        }

    def cancel_restore(self) -> str:
        """Drop the staged restore; the line to show."""
        with self._starting:
            running = self.jobs.latest(RESTORE)
            if running is not None and running.state == "running":
                raise Refusal(
                    f"a restore is being staged (job {running.id}); cancel it once its job ends"
                )
            if _read_journal(self.layout) is None:
                raise Refusal(f"no restore is staged for {self.layout.root}", 404)
            return restore.cancel(self.layout)

    def hold_after_restore(self, store: Store) -> AfterRestore | None:
        """At a start, before the engine opens: while a finished restore waits for his carry-on,
        pause fires by a merge into `[engine]`, keeping the value it replaces once for carry-on
        to give back, purge again the blobs the restore named, and read the copy's runs that read
        interrupted."""
        found = self.after = restore.after_restore(self.layout)
        if found is None:
            return None
        if not found.paused:
            earlier = _table(self.control.settings_get(ENGINE).get("autonomy")).get("paused")
            restore.paused(self.layout, earlier)
            self.after = restore.after_restore(self.layout)

        def paused(section: Document) -> Document:
            return {**section, "autonomy": {**_table(section.get("autonomy")), "paused": True}}

        self.control.settings_update(ENGINE, paused)
        for line in purge_again(store, found):
            print(f"library: {line}", file=sys.stderr)
        self._interrupted = interrupted_runs(self.layout.home)
        return self.after

    def when_carried_on(self, start: Callable[[], object]) -> None:
        """`start` now, or at his carry-on while a finished restore waits for it: the host's
        server sync, so nothing moves to or from a server before he carries on."""
        if self.after is None:
            start()
        else:
            self._resume = start

    def carry_on_restore(self) -> str:
        """His carry-on after a restore: `autonomy.paused` takes its earlier value back, server
        sync starts again, and the copy's held runs and each clocked trigger's one catch-up fire
        follow."""
        found = restore.after_restore(self.layout)
        if found is None:
            raise Refusal(
                f"no restore of {self.layout.root} waits for you to carry on; server sync and "
                "fires already run",
                404,
            )
        if found.paused:

            def given_back(section: Document) -> Document:
                autonomy = _table(section.get("autonomy"))
                autonomy.pop("paused", None)
                if found.earlier is not None:
                    autonomy["paused"] = cast("JsonValue", found.earlier)
                rest = {k: v for k, v in section.items() if k != "autonomy"}
                return {**rest, "autonomy": autonomy} if autonomy else rest

            self.control.settings_update(ENGINE, given_back)
        restore.carried_on(self.layout)
        self.after = None
        self._interrupted = []
        resume, self._resume = self._resume, None
        if resume is not None:
            resume()
        return (
            f"server sync and fires run again in {self.layout.root}; each clocked trigger fires "
            "once for the time it missed, and the runs the copy held carry on"
        )

    def reindex(self, rebuild: Callable[[], object], *, hindsight: bool) -> threading.Thread | None:
        """After a finished restore whose indexes were not rebuilt: `rebuild` on its own thread,
        logged `reindexed` only when it succeeds, so a failed one runs again at the next start."""
        if restore.pending_reindex(self.layout) is None:
            return None
        self._reindex, self._hindsight = "running", hindsight

        def work() -> None:
            try:
                rebuild()
                restore.reindexed(self.layout)
            except Exception as error:  # recall stays partial; the next start tries again
                self._reindex = "failed"
                self._reindex_line = f"{type(error).__name__}: {error}"
                print(f"memory: the rebuild after the restore failed: {error}", file=sys.stderr)
            else:
                self._reindex = None

        thread = threading.Thread(target=work, name="restore-reindex", daemon=True)
        thread.start()
        return thread

    def _drill_if_due(self, look: Look, now: datetime) -> Job | None:
        """The drill, every `[backup.drill] every`, on the place drilled longest ago (or never)
        of those that hold a whole copy; the quick undo stands in while no place he named does.
        A drill that did not start is tried again an hour later."""
        plan = look.plan
        drills = [line for line in look.log if line.get("kind") == "drill"]
        rounds = [line for line in look.log if line.get("kind") == "round"]
        since = drills[-1] if drills else (rounds[0] if rounds else None)
        if (
            not plan.upkeep.drill
            or since is None
            or now - _logged_at(since) < span(plan.upkeep.drill_every)
        ):
            return None
        if self._drill_tried is not None and now - self._drill_tried < RETRY:
            return None
        held = [
            (storage.id, repository_of(storage, self.layout), storage_key(storage, look.home_id))
            for storage, place in zip(plan.folders, look.places[1:], strict=True)
            if storage.policy.on
            and place.complete is not None
            and Path(_path(storage).anchor or "/").exists()
        ]
        if not held and look.places[0].complete is not None:
            held = [(QUICK, FolderRepository(self.layout.backups / QUICK), QUICK)]
        if not held:
            return None
        last = {str(line.get("key")): _logged_at(line) for line in drills}
        place_id, repo, _ = min(held, key=lambda place: last.get(place[2], EARLIEST))
        with self._starting:
            if self._busy() is not None:
                return None
            self._drill_tried = now
            started = self.jobs.start(
                DRILL, lambda _progress: self._drill(place_id, repo, plan.upkeep.drill_sample)
            )
        return started.job

    def _drill(self, place_id: str, repo: Repository, sample: int) -> Mapping[str, object]:
        try:
            drilled = restore.drill(
                self.layout,
                repo,
                sample=sample,
                rng=random.Random(),  # noqa: S311 - which files a drill samples, not a secret
                keep_free=self.floor,
            )
        except Busy as busy:
            raise Stopped(str(busy)) from None
        self._drill_waits = drilled if drilled.passed is None and drilled.stamp else None
        if drilled.passed is not None:
            self._drill_incident(place_id, drilled)
        return {
            "place": place_id,
            "where": drilled.where,
            "stamp": drilled.stamp,
            "passed": drilled.passed,
            "checked": drilled.checked,
            "damaged": list(drilled.damaged),
            "line": drilled.line,
        }

    def _drill_incident(self, place_id: str, drilled: Drilled) -> None:
        trigger, at = f"{DRILL_INCIDENT}{place_id}", self.clock().astimezone(UTC).isoformat()
        with InboxTable.open(self.layout.home) as inbox:
            if drilled.passed:
                if inbox.open_incident(trigger) is not None:
                    inbox.resolve_incident(trigger, at=at)
                return
            inbox.incident(
                trigger,
                "drill-failed",
                f"Backups: the restore drill of {place_id} found damage",
                f"{drilled.line}. QMX removed each damaged file there and the next round copies "
                "it again; the copies that named it lack it until then",
                at=at,
            )

    def _standings(
        self, plan: Plan, log: Sequence[Mapping[str, object]], home_id: str
    ) -> list[Standing]:
        quick = FolderRepository(self.layout.backups / QUICK)
        return [
            standing(log, QUICK, QUICK, quick.where, plan.pc.interval, on=plan.on),
            *(
                standing(
                    log,
                    storage_key(storage, home_id),
                    storage.id,
                    repository_of(storage, self.layout).where,
                    storage.policy.interval,
                    on=plan.on and storage.policy.on,
                )
                for storage in plan.folders
            ),
        ]

    def _repository(self, plan: Plan, place_id: str) -> Repository:
        if place_id == QUICK:
            return FolderRepository(self.layout.backups / QUICK)
        return repository_of(self._storage(plan, place_id), self.layout)

    def _storage(self, plan: Plan, place_id: str) -> Storage:
        found = next((s for s in plan.folders if s.id == place_id), None)
        if found is None:
            raise Refusal(f"there is no storage {place_id!r} in Settings", 404)
        return found

    def _home_id(self) -> str:
        return Label.parse(self.layout.label.read_text(encoding="utf-8")).home_id

    def _quick_size(self) -> int:
        if self._quick_bytes is None:
            self._quick_bytes = _size(self.layout.backups / QUICK)
        return self._quick_bytes

    def _proposal(self, plan: Plan) -> Proposal | None:
        if plan.folders:
            return None
        now = monotonic.monotonic()
        if self._proposed is None or now - self._proposed[0] >= PROPOSAL_S:
            self._proposed = (now, proposal(self.layout))
        return self._proposed[1]


class RunBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str | None = None


def backups_router(backups: Backups) -> APIRouter:
    """`/api/backups`: the view, a place's copies, a round asked for, its job, his carry-on, his
    yes to the proposed second drive, and a restore checked, staged, cancelled and carried on
    from. The REST app puts every route behind the bearer."""
    router = APIRouter()

    def answered[T](work: Callable[[], T]) -> T:
        try:
            return work()
        except Refusal as refused:
            raise HTTPException(refused.status, str(refused)) from None
        except PlanRefused as refused:
            raise HTTPException(409, f"[backup] in Settings: {refused}") from None
        except (RestoreRefused, Busy) as refused:
            raise HTTPException(409, str(refused)) from None

    @router.get("/api/backups")
    def view() -> dict[str, object]:
        return backups.view()

    @router.get("/api/backups/targets/{target_id}/copies")
    def copies(target_id: str) -> dict[str, object]:
        return {"copies": answered(lambda: backups.copies(target_id))}

    @router.post("/api/backups/run", status_code=202)
    def run(body: RunBody | None = None) -> JSONResponse:
        started = answered(lambda: backups.start(None if body is None else body.target, asked=True))
        if not started.new:
            raise HTTPException(409, backups.busy_line(started.job))
        return JSONResponse(started.job.document(), status_code=202)

    @router.get("/api/backups/jobs/{job_id}")
    def job(job_id: str) -> dict[str, object]:
        found = backups.jobs.get(job_id)
        if found is None:
            raise HTTPException(404, f"there is no backup job {job_id}")
        return found.document()

    @router.post("/api/backups/targets/default/accept")
    def accept() -> dict[str, object]:
        return answered(backups.accept)

    @router.post("/api/backups/targets/{target_id}/carry-on")
    def carry(target_id: str) -> dict[str, object]:
        return {"line": answered(lambda: backups.carry_on(target_id))}

    @router.post("/api/backups/restore/check")
    async def check(request: Request) -> dict[str, object]:
        body = await _json(request)
        return await asyncio.to_thread(answered, lambda: backups.check_restore(body))

    @router.post("/api/backups/restore", status_code=202)
    async def stage(request: Request) -> JSONResponse:
        body = await _json(request)
        job = await asyncio.to_thread(answered, lambda: backups.stage_restore(body))
        return JSONResponse(job.document(), status_code=202)

    @router.post("/api/backups/restore/cancel")
    def cancel() -> dict[str, object]:
        return {"line": answered(backups.cancel_restore)}

    @router.post("/api/backups/restore/carry-on")
    def carry_on_restore() -> dict[str, object]:
        return {"line": answered(backups.carry_on_restore)}

    _ = view, copies, run, job, accept, carry, check, stage, cancel, carry_on_restore
    return router


def road_lease_of(layout: Layout, *, wait: float = ROAD_WAIT_S) -> RoadLease:
    """The hook a round copies a mini app's `road/` under: its road lease
    (`VolumeLease(data / "road-locks", app_id)`), taken as soon as a road step lets it go."""

    @contextmanager
    def held(app_id: str) -> Generator[object]:
        deadline = monotonic.monotonic() + wait
        while True:
            try:
                lease = VolumeLease(layout.data / "road-locks", app_id)
            except AppError:
                if monotonic.monotonic() >= deadline:
                    raise
                monotonic.sleep(ROAD_POLL_S)
            else:
                break
        try:
            yield lease
        finally:
            lease.close()

    return held


def purge_again(store: Store, restored: AfterRestore) -> list[str]:
    """Purge again each blob a restore named, so no replica keeps it (E-S17); the line for each
    that could not be. On a writer through `purge`. The restore placed each blob's tombstone
    already, so `purge` meets other tombstone bytes there (`collision`): the blob is purged, and
    only the purge ref the copy lacks is recorded, which replicas apply when they mirror it. On a
    replica through `apply_purge`, which does nothing once the tombstone is there; the primary's
    ref reaches it after he carries on."""
    reason = f"purged again after the restore of the copy {restored.stamp}"
    at = datetime.now(UTC).isoformat()
    failed: list[str] = []
    for blob in restored.purge:
        try:
            if store.role != "writer":
                store.apply_purge(blob, reason=reason, at=at)
                continue
            try:
                store.purge(Principal("operator"), blob, reason)
            except LibraryRefused as refused:
                if refused.code != "collision":
                    raise
                hexdigest = blob.removeprefix("sha256:")
                item, ref = f"purge:{hexdigest}", f"refs/purges/{hexdigest}"
                if store.head(item, ref) is None:
                    store.mirror(item, ref, "purged", expected_head=None, who="operator")
        except LibraryRefused as refused:
            failed.append(f"{blob} was not purged again after the restore: {refused}")
    return failed


def interrupted_runs(home: Path) -> list[str]:
    """The runs in the folder's ledger that read `interrupted`: an attempt was in flight when the
    copy was made. They resume once fires run again."""
    try:
        with Reader.open(home) as reader:
            started = [
                str(row[0])
                for row in reader.connection.execute(
                    "SELECT run_id FROM events WHERE kind = 'run_created' ORDER BY at, run_id"
                )
            ]
            return [
                run
                for run in started
                if status_of(reader.events(run), frozenset[str]()).status == "interrupted"
            ]
    except FileNotFoundError:
        return []
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"backups: the runs the copy held were not read: {error}", file=sys.stderr)
        return []


async def _json(request: Request) -> object:
    """The body as JSON, read raw so a bad one answers 400 with its line, never 422."""
    try:
        return json.loads(await request.body() or b"null")
    except ValueError:
        return None


def _restore_body(body: object, *, confirm: bool) -> tuple[str, str]:
    """The place and the copy a restore route names. Raises Refusal (400) for any other body,
    and for a restore not confirmed."""
    allowed = {"target", "copy", "confirmed"} if confirm else {"target", "copy"}
    fields = cast("dict[str, object]", body) if isinstance(body, dict) else None
    if (
        fields is None
        or not isinstance(fields.get("target"), str)
        or not isinstance(fields.get("copy"), str)
        or set(fields) - allowed
    ):
        raise Refusal(
            "send the backup place and the copy's date as {target, copy"
            + (", confirmed}" if confirm else "}"),
            400,
        )
    if confirm and fields.get("confirmed") is not True:
        raise Refusal(
            "a restore replaces this folder's data, so it needs confirmed: true, sent once you "
            "have seen what it replaces (POST /api/backups/restore/check)",
            400,
        )
    return str(fields["target"]), str(fields["copy"])


def _paused_line(found: AfterRestore, interrupted: Sequence[str]) -> str:
    line = (
        f"server sync and fires are paused after the restore of the copy {found.stamp} from "
        f"{found.where}; look over what it restored, then carry on in Settings, Data and backups"
    )
    if interrupted:
        line += (
            f"; {_count(len(interrupted), 'run', 'runs')} the copy held "
            f"{'resumes' if len(interrupted) == 1 else 'resume'} then: {', '.join(interrupted)}"
        )
    return line


def _table(value: object) -> dict[str, JsonValue]:
    return dict(cast("dict[str, JsonValue]", value)) if isinstance(value, dict) else {}


def _path(storage: Storage) -> Path:
    return cast("Path", storage.path)


def _policy_line(policy: Policy) -> str:
    """This PC's policy, as the doctor row says it."""
    if not policy.on:
        return "copies on this PC are off"
    counts = [
        f"{getattr(policy.keep, key)} {key}" for key in KEEP_KEYS if getattr(policy.keep, key)
    ]
    return f"a copy every {policy.every} when something changed, kept {', '.join(counts)}"


def _logged_at(line: Mapping[str, object]) -> datetime:
    """When a backup log line was written."""
    try:
        return datetime.fromisoformat(str(line.get("at")))
    except ValueError:
        return EARLIEST


def _place_document(
    place: Standing, storage: Storage | None, now: datetime, layout: Layout, plan: Plan
) -> dict[str, object]:
    last, complete, concern = place.last, place.complete, place.concern(now)
    policy = plan.pc if storage is None else storage.policy
    return {
        "id": place.id,
        "where": place.where,
        "every": policy.every,
        "keep": {key: getattr(policy.keep, key) for key in KEEP_KEYS},
        "save": list(policy.save),
        "path": None if storage is None else str(storage.path),
        "at": None if storage is None else policy.at.strftime("%H:%M"),
        "on": place.on,
        "same_drive": storage is not None and same_drive(storage, layout),
        "last": None
        if last is None
        else {
            "at": last.at.isoformat(),
            "result": last.result,
            "line": last.line,
            "stamp": last.stamp,
            "partial": last.partial,
        },
        "newest_complete": None if complete is None else complete.stamp,
        "concern": None if concern is None else concern.line,
    }


def _doctor_part(place: Standing, now: datetime) -> str:
    name = "This PC's copies" if place.id == QUICK else f"{place.id} ({place.where})"
    complete = place.complete
    part = (
        f"{name}: no whole copy yet"
        if complete is None or complete.stamp is None
        else f"{name}: newest whole copy from {_age(now - when(complete.stamp))} ago"
    )
    concern = place.concern(now)
    return part if concern is None else f"{part}, and it needs you: {concern.line}"


def _skipped_with_quick(log: Sequence[Mapping[str, object]]) -> str:
    """When the newest round's quick undo was refused, the places it then skipped."""
    rounds = [line for line in log if line.get("kind") == "round"]
    if not rounds:
        return ""
    places = cast("list[dict[str, object]]", rounds[-1].get("places", []))
    if not places or places[0].get("key") != QUICK or places[0].get("result") != "refused":
        return ""
    skipped = [str(p.get("where")) for p in places[1:] if p.get("result") == "skipped"]
    if not skipped:
        return ""
    return f"; the last round made no copy, so none went to {', '.join(skipped)} either"


def _open_places(inbox: InboxTable) -> set[str]:
    """The places with an open `backup:<place>` incident. The inbox table has no reader of
    incidents by prefix, so this reads its `incidents` rows."""
    rows = inbox.connection.execute(
        "SELECT trigger_id FROM incidents WHERE trigger_id LIKE 'backup:%' AND resolved_at IS NULL"
    ).fetchall()
    return {str(row[0]).removeprefix("backup:") for row in rows}


def _title(place: str) -> str:
    if place == SETTINGS:
        return "Backups: the [backup] settings need you"
    if place == QUICK:
        return "Backups: This PC's copies need you"
    return f"Backups: the backup place {place} needs you"


def _size(folder: Path) -> int:
    total = 0
    for root, _folders, files in os.walk(folder):
        for name in files:
            with suppress(OSError):
                total += os.stat(os.path.join(root, name)).st_size
    return total


def _age(span: timedelta) -> str:
    minutes = max(int(span.total_seconds() // 60), 0)
    for size, word in ((24 * 60, "day"), (60, "hour"), (1, "minute")):
        if minutes >= size:
            count = minutes // size
            return f"{count} {word}" if count == 1 else f"{count} {word}s"
    return "less than a minute"


def _count(count: int, one: str, many: str) -> str:
    return f"{count:,} {one if count == 1 else many}"


def _mb(count: int) -> str:
    return f"{count / (1 << 20):,.1f} MB"
