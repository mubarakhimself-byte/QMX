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

A round makes This PC's copy as one `backup` job and then starts one `send:<place>` job per due
storage from that pinned copy, so a slow storage never holds This PC's copies; a second send to a
storage while one runs is refused. A round, a restore being staged and the drill each hold the
folder's backup lock, so they run one at a time; a send, the drill of a storage and its monthly
upkeep (re-pack and check, `upkeep:<place>`) hold that storage's own lock. A storage that refused
is tried again at its next due round.

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
import tomllib
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import ExitStack, contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final, Literal, cast

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, JsonValue
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
    STORAGE_POLICY,
    Plan,
    PlanRefused,
    Policy,
    Proposal,
    Storage,
    open_storage,
    parse,
    proposal,
    rclone_root,
    same_drive,
    span,
    storage_key,
    storage_root,
)
from qmx_home.backup.repository import (
    FolderRepository,
    Packed,
    Repository,
    StorageRefused,
    Unreadable,
    free_bytes,
)
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
    _tried,  # pyright: ignore[reportPrivateUsage] - the round's own record of a place's last try
    carry_on,
    clear_scratch,
    copy_round,
    due,
    safety_of,
    send,
    send_lock,
    unstage,
)
from qmx_home.backup.snapshot import RoadLease
from qmx_home.backup.upkeep import check, repack
from qmx_home.files import Busy, hold, plain
from qmx_home.rclone import Keys, Rclone
from qmx_home.versions import log_line, log_lines
from qmx_library.port import LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_host.first_start import (
    FILL_RECORD,
    Connected,
    keep_fill_record,
    keys_left_out,
    machine_settings,
    restored_settings,
)
from qmx_host.jobs import Job, Jobs, Progress, Started, Stopped, Work
from qmx_host.keys import NAME as KEY_NAME
from qmx_host.keys import refusal as key_refusal
from qmx_host.maintenance import landed

KIND: Final = "backup"
RESTORE: Final = "restore"
DRILL: Final = "drill"
SEND: Final = "send:"
"""A send to one storage, one job per storage: `send:<place id>`."""
UPKEEP: Final = "upkeep:"
"""QMX's monthly upkeep of one storage, This PC included: `upkeep:<place id>`."""
ROW: Final = "backups"
"""The doctor row's name."""
SWEEP_S: Final = 60.0
"""How often the host looks whether a place is due. The first look is one sweep after it serves,
so a start is never slowed by a copy."""
RETRY: Final = timedelta(hours=1)
"""A drill that did not start is tried again an hour later."""
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
OFF_LINE: Final = (
    "Sync to my storage is off: QMX makes no copy anywhere, This PC included, and deletes none "
    "until you turn it on in Settings"
)
NO_COPY_LINE: Final = (
    "your work has no copy anywhere: copies on this PC are off and no storage gets one; turn "
    "This PC's copies on or connect a storage in Settings, Sync to my storage"
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
        keys: Keys | None = None,
        store: Store | None = None,
    ) -> None:
        self.layout = layout
        self.store = store
        """The Library each host job lands its `maintenance-result` in; none lands without it."""
        self.control = control
        self.clock = clock
        self.floor = floor
        self.road_lease = road_lease if road_lease is not None else road_lease_of(layout)
        self.keys = keys
        """The key store an rclone storage's runner reads; Credential Manager when None, made
        only once a storage needs it."""
        self.jobs = Jobs()
        self._runner: Rclone | None = None
        self._pins: dict[str, set[str]] = {}
        """Each pinned copy's stamp and the storages whose sends still read it."""
        self._pinning = threading.Lock()
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
        with suppress(Busy, PlanRefused, OSError, ValueError):
            if layout.label.is_file():
                with hold(layout.backups / LOCK, CLI_BUSY):
                    clear_scratch(layout, self.plan())

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
        quick_due = pc.on and due(_tried(look.log, QUICK), now, pc.interval, pc.at)
        ready = any(
            storage.policy.on
            and (storage.path is None or Path(storage.path.anchor or "/").exists())
            and not self._sending(storage.id)
            and due(
                _tried(look.log, storage_key(storage, look.home_id)),
                now,
                storage.policy.interval,
                storage.policy.at,
            )
            for storage in look.plan.sending
        )
        if not (quick_due or ready):
            return self._drill_if_due(look, now) or self._upkeep_if_due(look, now)
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
            storage = self._storage(self.plan(), only)
            if self._sending(only):
                raise Refusal(
                    f"QMX is already sending a copy to {storage.shown} (job "
                    f"{self._send_job(only)}); it ends by itself, then ask again"
                )
        with self._starting:
            other = self._busy()
            if other is not None and other.kind != KIND:
                raise Refusal(self.busy_line(other))
            if other is None:
                self._unheld()
            started = self.jobs.start(
                KIND, self._landing("sync", lambda progress: self._round(only, progress, asked))
            )
        if started.new:
            self._asked[started.job.id] = asked
        return started

    def busy_line(self, job: Job) -> str:
        if job.kind.startswith(SEND):
            return (
                f"QMX is already sending a copy to {job.kind.removeprefix(SEND)} (job {job.id}); "
                "it ends by itself, then ask again"
            )
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
        """This PC's copy, then one send job per due storage from that pinned copy. The result
        names each send's job."""
        sends: dict[str, str] = {}
        try:
            plan = self.plan()
            with self._pinning:
                held = set(self._pins)
            report, pinned = copy_round(
                self.layout,
                plan,
                now=self.clock(),
                floor=self.floor,
                only=only,
                asked=asked,
                progress=progress,
                road_lease=self.road_lease,
                held=held,
            )
            self._torn(plan, next(p for p in report.places if p.key == QUICK))
            if pinned is not None:
                sends = self._send_all(plan, pinned.stamp, pinned.due)
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
        return {**report.document(), "sends": sends}

    def _send_all(self, plan: Plan, stamp: str, due: Sequence[str]) -> dict[str, str]:
        """Start one send job per storage in `due` from the pinned copy `stamp`; a storage whose
        send still runs waits for its next due round. The staging goes once the last ends."""
        started: dict[str, str] = {}
        with self._pinning:
            self._pins[stamp] = {""}
        for place_id in due:
            with self._pinning:
                self._pins[stamp].add(place_id)

            def work(progress: Progress, place_id: str = place_id) -> Mapping[str, object]:
                return self._send(plan, place_id, stamp, progress)

            job = self.jobs.start(f"{SEND}{place_id}", self._landing("sync", work))
            if job.new:
                started[place_id] = job.job.id
            else:
                self._unpin(stamp, place_id)
        self._unpin(stamp, "")
        return started

    def _send(
        self, plan: Plan, place_id: str, stamp: str, progress: Progress
    ) -> Mapping[str, object]:
        try:
            report = send(
                self.layout,
                plan,
                place_id,
                stamp,
                progress=progress,
                rclone=self.rclone(plan),
                floor=self.floor,
            )
        except (Busy, PlanRefused) as refused:
            raise Stopped(str(refused)) from None
        finally:
            self._unpin(stamp, place_id)
            self._settle()
        self._torn(plan, report.places[0])
        return report.document()

    def _landing(self, job: str, work: Work) -> Work:
        """`work` that lands one `maintenance-result` artifact when it ends, however it ends."""

        def landing(progress: Progress) -> Mapping[str, object]:
            state, line = "stopped", ""
            try:
                found = work(progress)
            except Stopped as stopped:
                line = stopped.line
                raise
            except Exception as error:
                line = f"{type(error).__name__}: {error}"
                raise
            else:
                state = "finished"
                line = str(found.get("line") or "; ".join(_lines_of(found)))
                return found
            finally:
                if self.store is not None:
                    landed(self.store, job, state, line)

        return landing

    def _unpin(self, stamp: str, place_id: str) -> None:
        with self._pinning:
            left = self._pins.get(stamp)
            if left is None:
                return
            left.discard(place_id)
            if left:
                return
            del self._pins[stamp]
        unstage(self.layout, stamp)

    def _sending(self, place_id: str) -> bool:
        latest = self.jobs.latest(f"{SEND}{place_id}")
        return latest is not None and latest.state == "running"

    def _send_job(self, place_id: str) -> str:
        latest = self.jobs.latest(f"{SEND}{place_id}")
        return "" if latest is None else latest.id

    def rclone(self, plan: Plan) -> Rclone | None:
        """The one rclone runner on this folder, made when a storage needs it."""
        if not any(s.via == "rclone" for s in plan.storages):
            return None
        if self._runner is None or self._runner.path != plan.rclone_path:
            keys = self.keys
            if keys is None:
                from qmx_broker.credentials import CredentialManager  # noqa: PLC0415

                keys = CredentialManager()
            self._runner = Rclone(self.layout, keys=keys, path=plan.rclone_path)
        return self._runner

    def _torn(self, plan: Plan, placed: Placed) -> None:
        """The upkeep incident for what a round's clean and sweep found torn at one place."""
        line = _torn_line(placed)
        if line:
            self._note(plan, placed.id, "torn", line)

    def _note(self, plan: Plan, place_id: str, signature: str, line: str) -> None:
        """An upkeep incident at one storage, `upkeep:<place>`, named as he reads the storage;
        the next clean upkeep there resolves it."""
        at = self.clock().astimezone(UTC).isoformat()
        shown = "This PC's copies" if place_id == QUICK else self._storage(plan, place_id).shown
        with InboxTable.open(self.layout.home) as inbox:
            inbox.incident(
                f"{UPKEEP}{place_id}",
                signature,
                f"Backups: QMX's upkeep of {shown} found something",
                line,
                at=at,
            )

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
        for storage in plan.sending:
            key = storage_key(storage, home_id)
            policy = storage.policy
            if storage.id == only or (
                only is None
                and policy.on
                and due(_tried(log, key), now, policy.interval, policy.at)
            ):
                where = storage.shown
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

    def _upkeep_if_due(self, look: Look, now: datetime) -> Job | None:
        """QMX's monthly upkeep of the place upkept longest ago (or never) of those due: This PC
        and each storage, each `[backup.upkeep] every` since its last upkeep, or since its first
        copy. One upkeep at a time, so a re-pack never reads a storage beside another."""
        plan = look.plan
        if not plan.upkeep.on:
            return None
        if any(
            job.kind.startswith(UPKEEP) and job.state == "running"
            for job in (self.jobs.latest(f"{UPKEEP}{p.id}") for p in look.places)
            if job is not None
        ):
            return None
        every = span(plan.upkeep.every)
        last: dict[str, datetime] = {}
        first: dict[str, datetime] = {}
        for line in look.log:
            key = str(line.get("key"))
            if line.get("kind") == "upkeep":
                last[key] = _logged_at(line)
            if line.get("kind") == "round":
                for place in cast("list[dict[str, object]]", line.get("places", [])):
                    if place.get("result") == "copied":
                        first.setdefault(str(place.get("key")), when(str(line["stamp"])))
        keys = {QUICK: QUICK} | {
            s.id: storage_key(s, look.home_id) for s in plan.sending if s.policy.on
        }
        due_now = [
            (last.get(key, EARLIEST), place_id)
            for place_id, key in keys.items()
            if key in first
            and now - last.get(key, first[key]) >= every
            and not self._sending(place_id)
        ]
        if not due_now:
            return None
        _, place_id = min(due_now)
        started = self.jobs.start(
            f"{UPKEEP}{place_id}",
            self._landing("upkeep", lambda progress: self._upkeep(place_id, progress)),
        )
        return started.job

    def _upkeep(self, place_id: str, progress: Progress) -> Mapping[str, object]:
        """One place's re-pack and check, under its lock, logged as an `upkeep` line."""
        plan = self.plan()
        repo = self._repository(plan, place_id)
        if not isinstance(repo, Packed):
            raise Stopped(f"{repo.where} needs no upkeep from QMX")
        lock = self.layout.backups / LOCK if place_id == QUICK else send_lock(self.layout, place_id)
        upkeep = plan.upkeep
        now = self.clock()
        try:
            with hold(lock, f"QMX is working on {repo.where}; its upkeep waits", removed=True):
                progress(f"tidying {repo.where}")
                packed = repack(
                    repo,
                    past=upkeep.repack_past,
                    per_run=upkeep.repack_per_run,
                    safety=safety_of(plan),
                    step=lambda step: progress(f"tidying {repo.where}: {step}"),
                )
                progress(f"reading back a twelfth of what {repo.where} stores")
                checked = check(
                    repo,
                    slice=upkeep.check_slice,
                    month=now.year * 12 + now.month,
                    work=self.layout.cache / "sync-fetch",
                )
        except Busy as busy:
            raise Stopped(str(busy)) from None
        except StorageRefused as refused:
            raise Stopped(f"{refused}; QMX tries the upkeep again next month") from None
        line = (
            f"the upkeep of {repo.where} freed {_mb(packed.freed)}; {packed.unused:.0%} of what it "
            f"stores is used by no kept copy; {checked.line}"
        )
        if packed.torn:
            line += (
                f"; QMX wrote {_count(len(packed.torn), 'list', 'lists')} of where files are kept "
                "again from the stored files themselves, as "
                f"{'it was' if len(packed.torn) == 1 else 'they were'} not whole"
            )
        if packed.blocked:
            line = f"{line}; {packed.blocked}"
        found = [*checked.damaged, *packed.torn]
        log_line(
            self.layout,
            {
                "kind": "upkeep",
                "key": repo.key,
                "id": place_id,
                "at": now.astimezone(UTC).isoformat(),
                "deleted": packed.deleted,
                "written": packed.written,
                "unused": round(packed.unused, 4),
                "checked": checked.packs,
                "damaged": list(checked.damaged),
                "torn": [*packed.torn, *checked.torn],
                "line": line,
            },
        )
        trigger = f"{UPKEEP}{place_id}"
        if found or checked.torn:
            self._note(plan, place_id, "damaged" if checked.damaged else "torn", line)
        else:
            with InboxTable.open(self.layout.home) as inbox:
                if inbox.open_incident(trigger) is not None:
                    inbox.resolve_incident(trigger, at=now.astimezone(UTC).isoformat())
        return {"place": place_id, "where": repo.where, "line": line}

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
            "line": None if plan.sending else NO_SECOND_DRIVE,
            "proposal": None
            if offered is None
            else {"path": str(offered.path), "line": offered.line},
            "quick_undo_bytes": self._quick_size(),
            "places": [
                _place_document(place, storage, now, self.layout, plan)
                for place, storage in zip(places, (None, *plan.sending), strict=True)
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
        if not plan.sending:
            offered = self._proposal(plan)
            parts.append(NO_SECOND_DRIVE + (f"; {offered.line}" if offered else ""))
        parts += [
            f"{s.name} is not set up as a storage this QMX can copy to (via {s.via!r}); connect "
            "it again in Settings, Sync to my storage"
            for s in plan.not_set_up
        ]
        nowhere = plan.on and not plan.pc.on and not any(s.policy.on for s in plan.sending)
        drills, failed = self._drill_parts(plan, log, now)
        recall = self._recall_line()
        first = [
            *([] if plan.on else [OFF_LINE]),
            *([NO_COPY_LINE] if nowhere else []),
            *([] if self.after is None else [_paused_line(self.after, self._interrupted)]),
            *([] if recall is None else [recall]),
        ]
        ok = (
            bool(plan.sending)
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
            storage_key(s, home_id): (s.id, s.via) for s in plan.sending
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
        plan = self.plan()
        try:
            return carry_on(self.layout, self._storage(plan, place_id), rclone=self.rclone(plan))
        except StorageRefused as refused:
            raise Refusal(str(refused)) from None

    def accept(self) -> dict[str, object]:
        """His yes to the proposed second drive: one `[engine]` place row that can keep, at its
        path. Its policy is the storage defaults until he changes one."""
        if self.plan().sending:
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
        at = STORAGE_POLICY.at.strftime("%H:%M")
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
            started = self.jobs.start(
                RESTORE, lambda progress: self._stage(place_id, repo, stamp, progress)
            )
        return started.job

    def _stage(
        self, place_id: str, repo: Repository, stamp: str, progress: Progress
    ) -> Mapping[str, object]:
        try:
            with ExitStack() as held:
                if place_id != QUICK:
                    busy = f"QMX is working on {repo.where}; ask again once it ends"
                    held.enter_context(hold(send_lock(self.layout, place_id), busy, removed=True))
                staged = restore.stage(
                    self.layout,
                    repo,
                    stamp,
                    keep_free=self.floor,
                    progress=progress,
                )
        except StorageRefused as refused:
            raise Stopped(f"{refused}; the restore did not start") from None
        except (RestoreRefused, Busy) as refused:
            raise Stopped(str(refused)) from None
        keep_fill_record(self.layout, stamp, keys_left_out(repo, stamp))
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
            line = restore.cancel(self.layout)
            (self.layout.backups / FILL_RECORD).unlink(missing_ok=True)
            return line

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
        self._settle_restored(found)
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

    def _settle_restored(self, found: AfterRestore) -> None:
        """At his carry-on after a restore from Settings: this machine's keys come back from the
        settings the restore set aside, and the storage it restored from keeps its row under the
        copy's row id, as the card does after its restore."""
        aside = self.layout.root / found.aside
        machine = machine_settings(aside)
        key = next(
            (
                str(line.get("key"))
                for line in reversed(log_lines(self.layout))
                if line.get("kind") == "restored" and line.get("id") == found.id
            ),
            "",
        )
        storage = None
        try:
            earlier = parse({}, self.layout, _table(machine.get("engine")))
        except PlanRefused:
            earlier = Plan()
        home_id = self._home_id()
        rows = _table(_table(machine.get("engine")).get("placement"))
        for one in earlier.sending:
            row = rows.get(one.name)
            if storage_key(one, home_id) == key and isinstance(row, dict):
                storage = Connected(one.name, cast("dict[str, object]", row))
        path = self.layout.home / "settings.toml"
        stored = tomllib.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        settings, _ = restored_settings(stored, machine, storage)
        for section in sorted({*settings, *stored}):
            if settings.get(section) != stored.get(section):
                value = cast("Document", settings.get(section, {}))
                self.control.settings_update(cast("Any", section), lambda _c, v=value: v)

    def keys_to_fill(self) -> dict[str, object]:
        """`GET /api/backups/keys-to-fill`: the key names the restored settings refer to that
        this machine's key store lacks, and the `settings.toml` paths the restored copy left out
        that are not filled yet. Names and paths only, never a value."""
        record = _fill_record(self.layout)
        store = self._keys()
        path = self.layout.home / "settings.toml"
        try:
            settings = tomllib.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        except ValueError:
            settings = {}
        names = sorted(n for n in _referred(settings) if store.read(n) is None)
        filled = set(cast("list[str]", record.get("filled", [])))
        paths = [p for p in cast("list[str]", record.get("settings", [])) if p not in filled]
        return {"copy": record.get("copy"), "keys": names, "settings": paths}

    def fill(self, path: str, value: str) -> None:
        """One `settings.toml` value the restored copy left out, written back at its path.
        Raises Refusal for a path the list does not name."""
        listed = cast("list[str]", self.keys_to_fill()["settings"])
        if path not in listed:
            raise Refusal(
                f"{path!r} is not a settings.toml key this restore left out; fill one of "
                "GET /api/backups/keys-to-fill, or change other settings in Settings"
            )
        self.control.fill_setting(path, value)
        record = _fill_record(self.layout)
        keep_fill_record(
            self.layout,
            str(record.get("copy", "")),
            cast("list[str]", record.get("settings", [])),
            filled=[*cast("list[str]", record.get("filled", [])), path],
        )

    def _keys(self) -> Keys:
        if self.keys is not None:
            return self.keys
        from qmx_broker.credentials import CredentialManager  # noqa: PLC0415

        return CredentialManager()

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
            (storage.id, self._repository(plan, storage.id), storage_key(storage, look.home_id))
            for storage, place in zip(plan.sending, look.places[1:], strict=True)
            if storage.policy.on
            and place.complete is not None
            and (storage.path is None or Path(storage.path.anchor or "/").exists())
            and not self._sending(storage.id)
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
                DRILL,
                self._landing(
                    "drill", lambda _progress: self._drill(place_id, repo, plan.upkeep.drill_sample)
                ),
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
                lock=None if place_id == QUICK else send_lock(self.layout, place_id),
            )
        except Busy as busy:
            raise Stopped(str(busy)) from None
        except StorageRefused as refused:
            raise Stopped(f"{refused}; the drill runs again next month") from None
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
                f"{drilled.line}. QMX put each damaged file on that storage's list of damaged "
                "files and the next round sends it again; the copies that named it lack it until "
                "then",
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
                    _where(storage, home_id),
                    storage.policy.interval,
                    on=plan.on and storage.policy.on,
                )
                for storage in plan.sending
            ),
        ]

    def _repository(self, plan: Plan, place_id: str) -> Repository:
        if place_id == QUICK:
            return FolderRepository(self.layout.backups / QUICK, key=QUICK)
        storage = self._storage(plan, place_id)
        return open_storage(storage, self.layout, rclone=self.rclone(plan), keep_free=self.floor)

    def _storage(self, plan: Plan, place_id: str) -> Storage:
        found = next((s for s in plan.storages if s.id == place_id), None)
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
        if plan.sending:
            return None
        now = monotonic.monotonic()
        if self._proposed is None or now - self._proposed[0] >= PROPOSAL_S:
            self._proposed = (now, proposal(self.layout))
        return self._proposed[1]


class RunBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str | None = None


class FillBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(min_length=1)
    value: str = Field(min_length=1)


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

    @router.get("/api/backups/keys-to-fill")
    def keys_to_fill() -> dict[str, object]:
        return backups.keys_to_fill()

    @router.put("/api/backups/keys-to-fill", status_code=204)
    def fill(body: FillBody) -> Response:
        answered(lambda: backups.fill(body.path, body.value))
        return Response(status_code=204)

    _ = view, copies, run, job, accept, carry, check, stage, cancel, carry_on_restore
    _ = keys_to_fill, fill
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


def _lines_of(found: Mapping[str, object]) -> list[str]:
    places = found.get("places")
    if not isinstance(places, list):
        return []
    return [
        str(cast("dict[str, object]", p).get("line"))
        for p in cast("list[object]", places)
        if isinstance(p, dict)
    ]


def _fill_record(layout: Layout) -> dict[str, object]:
    try:
        found = json.loads((layout.backups / FILL_RECORD).read_text(encoding="utf-8"))
    except OSError, ValueError:
        return {}
    return cast("dict[str, object]", found) if isinstance(found, dict) else {}


def _referred(settings: object) -> set[str]:
    """Every `qmx/` key name a value of `settings` refers to, such as a row's `credential_ref`,
    less the names QMX makes and keeps itself."""
    if isinstance(settings, dict):
        return {n for v in cast("dict[str, object]", settings).values() for n in _referred(v)}
    if isinstance(settings, list):
        return {n for v in cast("list[object]", settings) for n in _referred(v)}
    if isinstance(settings, str) and KEY_NAME.fullmatch(settings) and key_refusal(settings) is None:
        return {settings}
    return set()


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


def _where(storage: Storage, home_id: str) -> str:
    """Where a storage's copies are, as he reads it, without reaching the storage."""
    if storage.via == "folder" and storage.path is not None:
        return plain(storage_root(storage.path, home_id))
    if storage.via == "rclone" and storage.remote is not None:
        return f"{storage.name} ({rclone_root(storage.root, home_id)})"
    return storage.name


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
    rounds = [
        line
        for line in log
        if line.get("kind") == "round"
        and cast("list[dict[str, object]]", line.get("places", []))[:1]
        and cast("list[dict[str, object]]", line.get("places", []))[0].get("key") == QUICK
    ]
    if not rounds:
        return ""
    places = cast("list[dict[str, object]]", rounds[-1].get("places", []))
    if places[0].get("result") != "refused":
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


def _torn_line(placed: Placed) -> str:
    """What a round's clean and sweep found torn at one place, for him; empty when nothing."""
    found: list[str] = []
    if placed.torn:
        one = len(placed.torn) == 1
        found.append(
            f"QMX removed {_count(len(placed.torn), 'copy list', 'copy lists')} at {placed.where} "
            f"that {'was' if one else 'were'} never whole ({', '.join(placed.torn)}); "
            f"{'it was' if one else 'each was'} older than the newest whole copy there, so no "
            "copy was lost"
        )
    if placed.torn_index:
        one = len(placed.torn_index) == 1
        found.append(
            f"QMX found {_count(len(placed.torn_index), 'list', 'lists')} of where files are "
            f"kept at {placed.where} that {'was' if one else 'were'} not whole, and wrote "
            f"{'it' if one else 'them'} again from the stored files themselves, so no copy was "
            "lost"
        )
    return ". ".join(found)


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
