"""The one connect dialog's backend (design 06 section 9): the screen and the copilot connect a
storage, and later compute and deep logs, through the same routes.

A connection kind is an ordered list of steps, each `(name, who, check, do)`. A job runs the kind
on the host's job runner: it skips every step whose `check` passes, runs QMX's steps in order, and
finishes with `needs` naming a card at a step only he can do. When he has answered, the same
`POST` runs the kind again with his answer, so resuming is rerunning and no state machine is
saved (I12). What a card's answer cannot carry back (the fields he typed, rclone's pending
question) is kept in memory by place until the place row is written; a host that stops forgets
it, and the rerun asks for it again. The place row is written once, last, after the name and
target checks, through `settings_update`, which keeps every other `[engine]` key.

Every line a job shows is plain words and names the place; rclone's own text never reaches one.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Mapping, MutableMapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, NamedTuple, cast

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from qma.harness.home import DoctorLine
from qmx_broker.credentials import KeyStore
from qmx_home import Layout
from qmx_home.rclone import Rclone, RcloneRefused

from qmx_host.jobs import Job, Jobs, Progress, Stopped

if TYPE_CHECKING:
    from qmx_control.service import ControlService

type Who = Literal["his", "qmx"]
type Rows = dict[str, dict[str, object]]
"""`[engine.placement]` rows by place name."""
type Can = Literal["run", "keep"]

PLACE_NAME: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
"""A place's name is a key of `[engine.placement]`."""
JOB: Final = "connect"


@dataclass(frozen=True, slots=True)
class Card:
    """What a step only he can do shows. `fields` are a question's parsed fields only (`Name`,
    `Help`, `Examples`, `Type`); `state` is rclone's loop state the answer carries back; `key`
    is the `qmx/` name a secret goes to through the key route; `link` is a sign-in link; `job`
    is the long job (the sign-in) the card waits on."""

    name: str
    line: str
    fields: tuple[Mapping[str, object], ...] = ()
    state: str = ""
    key: str = ""
    link: str = ""
    job: str = ""

    def document(self) -> dict[str, object]:
        found: dict[str, object] = {"card": self.name, "line": self.line}
        if self.fields:
            found["fields"] = [dict(f) for f in self.fields]
        for name in ("state", "key", "link", "job"):
            if value := getattr(self, name):
                found[name] = value
        return found


@dataclass(slots=True)
class World:
    """What every step of every kind reaches: the QMX folder, its key store and rclone, the
    settings (None on the first-start card, which writes no row), the first sync, the job runner
    and what the dialog remembers by place."""

    layout: Layout
    keys: KeyStore
    rclone: Rclone
    jobs: Jobs
    control: ControlService | None = None
    first_sync: Callable[[str], str] | None = None
    remembered: MutableMapping[str, dict[str, Any]] = field(
        default_factory=dict[str, dict[str, Any]]
    )
    cancels: MutableMapping[str, threading.Event] = field(
        default_factory=dict[str, threading.Event]
    )
    """A long job's stop switch, by its job id."""


@dataclass(slots=True)
class Run:
    """One run of a kind: what was asked, the world, and what its steps found so far."""

    kind: Kind
    place: str
    answer: Mapping[str, object]
    world: World
    card: bool = False
    """On the first-start card: no row is written and the run ends with a restore `source`."""
    lines: list[str] = field(default_factory=list[str])
    facts: dict[str, Any] = field(default_factory=dict[str, Any])
    """What this run's steps found, for the steps after them."""

    @property
    def memory(self) -> dict[str, Any]:
        return self.world.remembered.setdefault(self.place, {})

    def fields(self) -> dict[str, str]:
        given = self.answer.get("fields")
        typed = cast("dict[str, object]", given) if isinstance(given, dict) else {}
        kept = cast("dict[str, str]", self.memory.setdefault("fields", {}))
        kept.update({k: v.strip() for k, v in typed.items() if isinstance(v, str) and v.strip()})
        return kept

    def say(self, line: str) -> None:
        self.lines.append(line)


class Step(NamedTuple):
    name: str
    who: Who
    check: Callable[[Run], bool]
    """True when the step's work is already in place, so the step is skipped."""
    do: Callable[[Run], Card | None]
    """QMX's work, or his card. Raises Stopped with one line for a refusal."""


@dataclass(frozen=True, slots=True)
class Kind:
    id: str
    name: str
    can: tuple[Can, ...]
    rclone: bool
    steps: tuple[Step, ...]
    source: Callable[[Run], dict[str, object]] | None = None
    """On the card: the restore's `source` for the storage this kind connected."""
    refusal: Callable[[Run], str | None] | None = None
    """A refusal the route answers at once (409), before a job starts."""

    def document(self) -> dict[str, object]:
        return {"id": self.id, "name": self.name, "can": list(self.can), "rclone": self.rclone}


ROW_STEPS: Final = frozenset({"row", "first-sync"})
"""The steps the first-start card leaves out: it writes no row and starts no sync."""


def run_kind(
    kind: Kind,
    place: str,
    answer: Mapping[str, object],
    *,
    report: Progress,
    world: World,
    card: bool = False,
) -> Mapping[str, object]:
    """Run `kind` for `place` once. Ends with `needs` and its card at the first step he must do,
    or with the place and one line per step."""
    run = Run(kind, place, answer, world, card=card)
    steps = [s for s in kind.steps if not (card and s.name in ROW_STEPS)]
    for number, step in enumerate(steps):
        report(step.name, done=number, total=len(steps))
        if step.check(run):
            run.say(f"{step.name}: already done, skipped")
            continue
        try:
            needs = step.do(run)
        except RcloneRefused as refused:
            raise Stopped(f"{place}: {refused}", {"lines": run.lines}) from None
        except Stopped as stopped:
            raise Stopped(stopped.line, {"lines": run.lines}) from None
        if needs is not None:
            return {
                "place": place,
                "step": step.name,
                "needs": needs.document(),
                "lines": run.lines,
            }
    report("done", done=len(steps), total=len(steps))
    found: dict[str, object] = {"place": place, "needs": None, "lines": run.lines}
    if card and kind.source is not None:
        found["source"] = kind.source(run)
    if not card:
        world.remembered.pop(place, None)
    return found


class Connect:
    """The dialog on one QMX folder: its kinds, its jobs and what it remembers by place."""

    def __init__(self, world: World, kinds: Mapping[str, Kind]) -> None:
        self.world = world
        self.kinds = kinds
        self._starting = threading.Lock()

    def start(self, kind_id: str, place: str, answer: Mapping[str, object]) -> Job:
        kind = self.kind(kind_id)
        if not PLACE_NAME.fullmatch(place) or place == "pc":
            raise Refused(
                f"{place!r} cannot name a place: use letters, digits, - and _, and not pc, "
                "which is This PC",
                400,
            )
        if kind.refusal is not None:
            refused = kind.refusal(Run(kind, place, answer, self.world))
            if refused is not None:
                raise Refused(refused)
        with self._starting:
            started = self.world.jobs.start(
                f"{JOB}:{place}",
                lambda report: run_kind(kind, place, answer, report=report, world=self.world),
            )
        if not started.new:
            raise Refused(
                f"connecting {place} is already running (job {started.job.id}); wait for it to "
                "end, then answer its card"
            )
        return started.job

    def kind(self, kind_id: str) -> Kind:
        found = self.kinds.get(kind_id)
        if found is None:
            raise Refused(
                f"there is no kind {kind_id!r} to connect; choose one of {', '.join(self.kinds)}",
                400,
            )
        return found

    def read(self, job_id: str) -> dict[str, object]:
        job = self.world.jobs.get(job_id)
        if job is None:
            raise Refused(f"there is no connect job {job_id}", 404)
        return document(job)

    def cancel(self, job_id: str) -> str:
        """Stop the long job `job_id` names, or the one its card waits on."""
        job = self.world.jobs.get(job_id)
        if job is None:
            raise Refused(f"there is no connect job {job_id}", 404)
        needs = (job.result or {}).get("needs")
        waits = cast("dict[str, object]", needs).get("job") if isinstance(needs, dict) else None
        stop = self.world.cancels.get(str(waits)) or self.world.cancels.get(job_id)
        if stop is None:
            raise Refused(f"job {job_id} holds nothing that runs on; there is nothing to stop")
        stop.set()
        return f"job {job_id}: stopping; nothing was connected"

    def doctor_line(self) -> DoctorLine:
        """The storages' row. It never raises, because one failing row would fail the whole
        doctor read, and a headless server's keyring raises on every read."""
        try:
            aside = self.world.rclone.check_conf()
        except Exception as error:  # any key store failure is this row's answer
            return DoctorLine(
                "storages",
                False,
                f"the key store on this machine did not answer ({type(error).__name__}), so the "
                "storages' settings cannot be opened here",
            )
        if aside is None:
            return DoctorLine("storages", True, "the storages' settings on this PC open")
        return DoctorLine(
            "storages",
            False,
            f"the storages' settings on this PC could not be opened and were set aside as "
            f"{aside.name}; connect each rclone storage again",
        )


class Refused(Exception):
    def __init__(self, line: str, status: int = 409) -> None:
        super().__init__(line)
        self.status = status


def document(job: Job) -> dict[str, object]:
    """A connect job as a reader sees it, with the card it needs lifted to the top."""
    result = job.result or {}
    return {**job.document(), "needs": result.get("needs")}


class Asked(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    place: str
    answer: dict[str, object] = Field(default_factory=dict[str, object])
    """`{state, result}` for a question card, `{state, key}` for a secret card, `{fields}` for
    any other card."""


def connect_router(connect: Connect) -> APIRouter:
    """`/api/connect`: the kinds, a connect job started or rerun, read, and cancelled. The host's
    REST app puts every route behind the bearer."""
    router = APIRouter(prefix="/api/connect")

    def answered[T](work: Callable[[], T]) -> T:
        try:
            return work()
        except Refused as refused:
            raise HTTPException(refused.status, str(refused)) from None

    def kinds() -> dict[str, object]:
        return {"kinds": [kind.document() for kind in connect.kinds.values()]}

    def start(asked: Asked) -> JSONResponse:
        job = answered(lambda: connect.start(asked.kind, asked.place, asked.answer))
        return JSONResponse(document(job), status_code=202)

    def read(job_id: str) -> dict[str, object]:
        return answered(lambda: connect.read(job_id))

    def cancel(job_id: str) -> dict[str, object]:
        return {"line": answered(lambda: connect.cancel(job_id))}

    router.add_api_route("/kinds", kinds, methods=["GET"])
    router.add_api_route("/jobs", start, methods=["POST"], status_code=202)
    router.add_api_route("/jobs/{job_id}", read, methods=["GET"])
    router.add_api_route("/jobs/{job_id}/cancel", cancel, methods=["POST"])
    return router


def placement(control: ControlService) -> Rows:
    """`[engine.placement]` as stored, by place name."""
    engine = control.settings_get(cast("Any", "engine"))
    rows = engine.get("placement")
    if not isinstance(rows, dict):
        return {}
    return {
        name: cast("dict[str, object]", row)
        for name, row in cast("dict[str, object]", rows).items()
        if isinstance(row, dict)
    }


def write_row(
    control: ControlService,
    place: str,
    row: Mapping[str, object],
    refusal: Callable[[Rows], str | None],
) -> bool:
    """Write `row` as `[engine.placement.<place>]`, merged into the stored `[engine]`, once. The
    name and target checks run again inside the write, so a row another job wrote meanwhile is
    refused. False when the same row is already there and nothing was written."""
    wrote: list[bool] = []

    def placed(engine: dict[str, Any]) -> dict[str, Any]:
        found = engine.get("placement")
        rows = dict(cast("dict[str, Any]", found)) if isinstance(found, dict) else {}
        refused = refusal({k: v for k, v in rows.items() if isinstance(v, dict)})
        if refused is not None:
            raise Stopped(refused)
        if rows.get(place) == dict(row):
            return engine
        wrote.append(True)
        return {**engine, "placement": {**rows, place: dict(row)}}

    control.settings_update(cast("Any", "engine"), cast("Any", placed))
    return bool(wrote)


def kinds_of(*groups: tuple[Kind, ...]) -> dict[str, Kind]:
    return {kind.id: kind for group in groups for kind in group}


def same_folder(one: Path, other: Path) -> bool:
    return str(one.resolve()).casefold().rstrip("\\/") == str(other.resolve()).casefold().rstrip(
        "\\/"
    )


from qmx_host.connect_storage import STORAGE  # noqa: E402 - the kinds build on the types above

KINDS: Final[Mapping[str, Kind]] = kinds_of(STORAGE)
"""Every kind the dialog connects, by id."""
