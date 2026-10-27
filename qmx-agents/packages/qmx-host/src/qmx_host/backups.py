"""The host makes his copies on its own (design 62 C2 and F step 14).

Every minute the host reads `[backup]` and the record in `backups/backups.jsonl`. When the quick
undo is due (hourly) or a place he named is due and there, it runs one round as a `backup` job on
its own thread, so a copy never holds a request, and the quick undo never takes the folder's drive
below the host's floor. A place he must act on has one open inbox incident `backup:<place>`: a
round it refused (no room, another QMX folder's copies, a file that could not be read), a copy
that lacks files, or a disk that has been away for seven of its intervals. The next whole copy
there resolves it. `[backup]` that cannot be read opens `backup:settings`. The doctor row and
`GET /api/backups` read the same record, which the command line's rounds write too.

Nothing is written outside the QMX folder until he names a place or accepts the proposed second
drive, which writes one `[[backup.targets]]` row, so the place never moves with free space.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
import sys
import threading
import time as monotonic
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final, Literal, cast

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from qma.harness.home import DoctorLine
from qmx_control.models import Document
from qmx_control.service import ControlService
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_home import Label, Layout
from qmx_home.backup.keep import when
from qmx_home.backup.plan import (
    NO_SECOND_DRIVE,
    Every,
    Plan,
    PlanRefused,
    Proposal,
    Target,
    parse,
    proposal,
    repository_of,
    same_drive,
)
from qmx_home.backup.repository import FolderRepository, Repository, Unreadable
from qmx_home.backup.round import (
    QUICK,
    SealedKeys,
    _last,  # pyright: ignore[reportPrivateUsage] - the round's own record of a place's last copy
    _target_key,  # pyright: ignore[reportPrivateUsage] - and the key it logs a place under
    carry_on,
    due,
    run_round,
)
from qmx_home.files import Busy
from qmx_home.versions import log_lines

from qmx_host.jobs import Job, Jobs, Progress, Started, Stopped

KIND: Final = "backup"
ROW: Final = "backups"
"""The doctor row's name."""
SWEEP_S: Final = 60.0
"""How often the host looks whether a place is due. The first look is one sweep after it serves,
so a start is never slowed by a copy."""
RETRY: Final = timedelta(hours=1)
"""A place that refused or was not there is tried again an hour after it was last tried."""
AWAY: Final = 7
"""Intervals with no copy before a place that is not there opens its incident."""
INTERVAL: Final[Mapping[Every, timedelta]] = {
    "hour": timedelta(hours=1),
    "day": timedelta(days=1),
    "week": timedelta(weeks=1),
}
GOOD: Final = frozenset({"copied", "unchanged"})
SETTINGS: Final = "settings"
PROPOSAL_S: Final = 3600.0
"""How long a measured proposal is shown before the drives are measured again."""
DEFAULT_TARGET: Final = "second-drive"
NOT_A_FOLDER: Final = (
    "this home is not a QMX folder (it has no qmx-home.toml), so QMX makes no copies of it"
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
    every: Every
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
            if now - good >= AWAY * INTERVAL[self.every]:
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
    every: Every,
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
    """The quick undo first, then each target in the plan's order."""


class Backups:
    """The host's backup service: the sweep, the jobs, the incidents, the doctor row and the
    view. `clock` is local time with its zone; `floor` the room the host keeps on the folder's
    drive. `sealed_keys` makes the sealed key copy (B7)."""

    def __init__(
        self,
        layout: Layout,
        control: ControlService,
        *,
        clock: Callable[[], datetime],
        floor: int,
        sealed_keys: SealedKeys | None = None,
    ) -> None:
        self.layout = layout
        self.control = control
        self.clock = clock
        self.floor = floor
        self.sealed_keys = sealed_keys
        self.jobs = Jobs()
        self._asked: dict[str, bool] = {}
        self._raised: dict[str, Signature | None] = {}
        self._raising = threading.Lock()
        self._quick_bytes: int | None = None
        self._proposed: tuple[float, Proposal | None] | None = None

    async def run(self) -> None:
        """The sweep, every `SWEEP_S`, until the host stops."""
        while True:
            await asyncio.sleep(SWEEP_S)
            try:
                await asyncio.to_thread(self.sweep)
            except Exception as error:  # one bad sweep never ends the loop
                print(f"backups: a sweep failed: {type(error).__name__}: {error}", file=sys.stderr)

    def plan(self) -> Plan:
        return parse(self.control.settings_get("backup"), self.layout)

    def sweep(self) -> Job | None:
        """Bring the incidents in line with the log, then start a round when the quick undo, or
        a place that is there, is due. Returns the job it started."""
        if not self.layout.label.is_file():
            return None
        look = self._look()
        if look is None or self._running() is not None:
            return None
        now = self.clock()
        quick_due = due(_last(look.log, QUICK), now, "hour", now.time()) and look.places[0].ready(
            now
        )
        ready = any(
            target.on
            and Path(target.path.anchor or "/").exists()
            and due(
                _last(look.log, _target_key(target, look.home_id)), now, target.every, target.at
            )
            and place.ready(now)
            for target, place in zip(look.plan.targets, look.places[1:], strict=True)
        )
        if not (quick_due or ready):
            return None
        started = self.start(None, asked=False)
        return started.job if started.new else None

    def start(self, only: str | None, *, asked: bool) -> Started:
        """A round as a `backup` job (to `only`, due or not, when named), or the round that
        already runs. Raises Refusal when `only` is not a place in Settings."""
        if only is not None:
            self._target(self.plan(), only)
        started = self.jobs.start(KIND, lambda progress: self._round(only, progress))
        if started.new:
            self._asked[started.job.id] = asked
        return started

    def busy_line(self, job: Job) -> str:
        who = "you started it" if self._asked.get(job.id) else "the schedule started it"
        return (
            f"a backup round is already running (job {job.id}, {who}); it ends by itself, "
            "then ask again"
        )

    def _round(self, only: str | None, progress: Progress) -> Mapping[str, object]:
        try:
            report = run_round(
                self.layout,
                self.plan(),
                now=self.clock(),
                floor=self.floor,
                only=only,
                sealed_keys=self.sealed_keys,
                progress=progress,
            )
        except (Busy, PlanRefused) as refused:
            raise Stopped(str(refused)) from None
        finally:
            self._settle()
        return report.document()

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
            gone = (
                [p for p, s in self._raised.items() if p not in wanted and s is not None]
                if every_place
                else []
            )
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
                for place in gone:
                    inbox.resolve_incident(f"backup:{place}", at=at)
                    self._raised[place] = None

    def _running(self) -> Job | None:
        latest = self.jobs.latest(KIND)
        return latest if latest is not None and latest.state == "running" else None

    def view(self) -> dict[str, object]:
        """`GET /api/backups`: the plan, the proposal, each place's last round and newest whole
        copy, the quick undo's size and the round that runs."""
        running = self._running()
        found: dict[str, object] = {
            "folder": str(self.layout.root),
            "running": None if running is None else running.document(),
        }
        if not self.layout.label.is_file():
            return {**found, "refused": NOT_A_FOLDER, "places": []}
        try:
            plan = self.plan()
        except PlanRefused as refused:
            return {**found, "refused": f"[backup] in Settings: {refused}", "places": []}
        now = self.clock()
        places = self._standings(plan, log_lines(self.layout), self._home_id())
        offered = self._proposal(plan)
        return {
            **found,
            "refused": None,
            "line": None if plan.targets else NO_SECOND_DRIVE,
            "proposal": None
            if offered is None
            else {"path": str(offered.path), "line": offered.line},
            "quick_undo_bytes": self._quick_size(),
            "places": [
                _place_document(place, target, now, self.layout)
                for place, target in zip(places, (None, *plan.targets), strict=True)
            ],
        }

    def doctor_line(self) -> DoctorLine:
        """The doctor's `backups` row: each place's newest whole copy and what needs him."""
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
        parts[0] += f", {_mb(self._quick_size())} in all" + _skipped_with_quick(log)
        if not plan.targets:
            offered = self._proposal(plan)
            parts.append(NO_SECOND_DRIVE + (f"; {offered.line}" if offered else ""))
        ok = bool(plan.targets) and all(place.concern(now) is None for place in places)
        return DoctorLine(ROW, ok, "; ".join(parts))

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

    def carry_on(self, target_id: str) -> str:
        """His choice to keep sending to a place the fork guard refused. The next sweep tries it
        again at once."""
        return carry_on(self.layout, self._target(self.plan(), target_id))

    def accept(self) -> dict[str, object]:
        """His yes to the proposed second drive: one `[[backup.targets]]` row at its path."""
        if self.plan().targets:
            raise Refusal(
                "you already named a backup place; change it in Settings, Data and backups"
            )
        offered = proposal(self.layout)
        if offered is None:
            raise Refusal(NO_SECOND_DRIVE)
        target = Target(DEFAULT_TARGET, "folder", offered.path)
        row: Document = {
            "id": target.id,
            "kind": target.kind,
            "path": str(target.path),
            "every": target.every,
            "at": target.at.strftime("%H:%M"),
            "keep": {
                "daily": target.keep.days,
                "weekly": target.keep.weeks,
                "monthly": target.keep.months,
            },
            "on": target.on,
        }

        def added(section: Document) -> Document:
            rows = section.get("targets", [])
            return {**section, "targets": [*(rows if isinstance(rows, list) else []), row]}

        self.control.settings_update("backup", added)
        self._proposed = None
        return {
            "target": row,
            "line": f"QMX copies your work to {offered.path} every day at {row['at']}; the "
            "first copy is made at the next round, within a few minutes",
        }

    def _standings(
        self, plan: Plan, log: Sequence[Mapping[str, object]], home_id: str
    ) -> list[Standing]:
        quick = FolderRepository(self.layout.backups / QUICK)
        return [
            standing(log, QUICK, QUICK, quick.where, "hour"),
            *(
                standing(
                    log,
                    _target_key(target, home_id),
                    target.id,
                    repository_of(target, self.layout).where,
                    target.every,
                    on=target.on,
                )
                for target in plan.targets
            ),
        ]

    def _repository(self, plan: Plan, place_id: str) -> Repository:
        if place_id == QUICK:
            return FolderRepository(self.layout.backups / QUICK)
        return repository_of(self._target(plan, place_id), self.layout)

    def _target(self, plan: Plan, target_id: str) -> Target:
        found = next((t for t in plan.targets if t.id == target_id), None)
        if found is None:
            raise Refusal(f"there is no backup place {target_id!r} in Settings", 404)
        return found

    def _home_id(self) -> str:
        return Label.parse(self.layout.label.read_text(encoding="utf-8")).home_id

    def _quick_size(self) -> int:
        if self._quick_bytes is None:
            self._quick_bytes = _size(self.layout.backups / QUICK)
        return self._quick_bytes

    def _proposal(self, plan: Plan) -> Proposal | None:
        if plan.targets:
            return None
        now = monotonic.monotonic()
        if self._proposed is None or now - self._proposed[0] >= PROPOSAL_S:
            self._proposed = (now, proposal(self.layout))
        return self._proposed[1]


class RunBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str | None = None


def backups_router(backups: Backups) -> APIRouter:
    """`/api/backups`: the view, a place's copies, a round asked for, its job, his carry-on and
    his yes to the proposed second drive. The REST app puts every route behind the bearer."""
    router = APIRouter()

    def answered[T](work: Callable[[], T]) -> T:
        try:
            return work()
        except Refusal as refused:
            raise HTTPException(refused.status, str(refused)) from None
        except PlanRefused as refused:
            raise HTTPException(409, f"[backup] in Settings: {refused}") from None

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

    _ = view, copies, run, job, accept, carry
    return router


def _place_document(
    place: Standing, target: Target | None, now: datetime, layout: Layout
) -> dict[str, object]:
    last, complete, concern = place.last, place.complete, place.concern(now)
    return {
        "id": place.id,
        "where": place.where,
        "every": place.every,
        "path": None if target is None else str(target.path),
        "at": None if target is None else target.at.strftime("%H:%M"),
        "on": place.on,
        "same_drive": target is not None and same_drive(target, layout),
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
    name = "the quick undo" if place.id == QUICK else f"{place.id} ({place.where})"
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


def _title(place: str) -> str:
    if place == SETTINGS:
        return "Backups: the [backup] settings need you"
    if place == QUICK:
        return "Backups: the quick undo needs you"
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


def _mb(count: int) -> str:
    return f"{count / (1 << 20):,.1f} MB"
