"""The runner: the core, the worker and the ledger on one asyncio loop (AD-1, SOLUTION-DESIGN 3.3).

`Run.drive` folds the run's events, carries out the commands the core returns, and folds again.
Every event goes through the one `Ledger` writer before the next fold, so a worker's result is in
the ledger before the core sees it. The runner writes what SOLUTION-DESIGN 3.2 gives the core:
`node_scheduled`, a hold's `node_waiting`, a memo's `node_finished`, `ladder_step`, the doctor's
`doctor_verdict`, `run_paused` and `run_finished`. The worker writes `node_started` and
heartbeats, and the runner writes each attempt's ending from the result the worker returns.

Every event that ruling 77 sends to the operator raises its inbox item as it is written: a provider
failure, a system fault, or an irreversible external step of unknown outcome. While attempts run,
the runner wakes every `scheduler.tick` for the stuck detector (`watchdog`, AD-16), which reads what
each attempt shows and warns, interrupts, ends a stalled attempt, or stops a looping agent. There
is no runaway guard and no run timeout (AD-40). A ledger write error stops the engine claiming
work and raises a `black` item.

An `agent` chunk is held at dispatch behind the warm-first gate until the first chunk of its node
ends a turn (AD-9): it is scheduled but not started, so it writes no `node_started` and the stuck
detector sees it as a recorded wait. Capacity is the worker's table per resource class (AD-58);
the run's `priority`, recorded on `run_created` and passed to its subworkflows, orders its waiting
work against other runs'.

A `limits` block he wrote is recorded on `run_created`; the core holds new attempts once one is
reached and the run pauses. For `wall_seconds` the runner records the run's active time, outside
recorded waits and host sleep, on a run-level `heartbeat`. The engine dying mid-run
`crash_loop.restarts` times parks the run with one inbox item.

The recorded clock moves on with the wall clock: before an event, a `clock_tick` is written when a
second or more passed since the last one, and every event's `at` is the latest tick. The core
reads only those ticks (AD-6).

`Engine.resume` picks a run up again from the ledger. An attempt left in flight belongs to an
engine that died, since only one engine process can hold the writer: its outcome is unknown, and
`workers.effects.after_unknown` decides whether it retries, waits for an answer, or parks. An
`agent` attempt after such a death picks up its slot's last chat.

A model node that waits on a usage limit drains the run (AD-9): no new model attempt starts while
any slot waits on a limit, and other nodes go on. Once nothing runs, the run leaves a wake at the
earliest `resume_at`, which already holds `limits.slack`, writes `run_paused` and returns
`waiting`. The scheduler's ticker resumes it at that instant with `run_resumed` (`triggers`).
"""

from __future__ import annotations

import asyncio
import os
import secrets
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, Protocol, cast

from pydantic import JsonValue
from qma.harness import Pulse
from qmx_ledger.journal import fingerprint

from qmx_engine.admission import Admission, Capacity
from qmx_engine.core.commands import (
    Climb,
    Finish,
    Hold,
    Park,
    Pause,
    StartNode,
    UseMemo,
    Wait,
)
from qmx_engine.core.fold import fold, slot_of
from qmx_engine.core.ladder import CANCELLED, NO_DOCTOR, limits_line, step_data
from qmx_engine.core.partitions import RUN_SETTINGS
from qmx_engine.core.ready import next_commands
from qmx_engine.core.replay import idempotency_key, node_definition
from qmx_engine.core.state import Slot, State
from qmx_engine.definition.folder import content_hash, load
from qmx_engine.definition.model import Node, Workflow, dropped
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event, EventKind, JsonObject
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Ledger, LedgerWriteError, Reader, ledger_path
from qmx_engine.nodes.agent import Agent
from qmx_engine.nodes.base import Failed, Look, NodeJob, ending
from qmx_engine.nodes.fake_provider import PROFILE as FAKE_PROFILE
from qmx_engine.nodes.fake_provider import FakeProvider
from qmx_engine.nodes.grader import Grader
from qmx_engine.nodes.join import Join
from qmx_engine.nodes.llm import Llm, Unavailable
from qmx_engine.nodes.loop import Loop
from qmx_engine.nodes.monitor import Monitor
from qmx_engine.nodes.rule import Rule
from qmx_engine.nodes.script import HostScript, Script
from qmx_engine.nodes.subworkflow import Subworkflow
from qmx_engine.nodes.trigger import Trigger
from qmx_engine.nodes.wait import Wait as WaitNode
from qmx_engine.nodes.wait import resume_at, utc_text
from qmx_engine.ports.harness_adapter import HarnessPort
from qmx_engine.ports.inbox import InboxPort, Raise, raised_by
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.ports.memory import MemoryPort, MemoryStub
from qmx_engine.roles import EFFORTS, order, resolve
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers.rows import put_wake
from qmx_engine.watchdog import MAX_TICKS, Action, Kind, Meter, Watchdog, Watched, ledger_fault
from qmx_engine.workers.effects import AfterUnknown, after_unknown, effect_of, model_bearing
from qmx_engine.workers.local import AnyExecutor, LocalWorker, sweep
from qmx_engine.workers.zones import RunZone

if TYPE_CHECKING:
    from qmx_engine.ports.settings import SettingsPort

TICK: Final = timedelta(seconds=1)
LADDER_SETTINGS: Final = ("retry.max_tries", "retry.backoff")
NOTICED: Final = frozenset({"node_failed", "gate_opened"})
SCRIPTS: Final = frozenset({"script", "grader", "monitor"})

type Mode = Literal["live", "test"]
type Status = Literal["passed", "failed", "waiting", "interrupted", "stopped"]
type Classification = Literal["transient", "bad_input", "bad_output", "logic", "unavailable"]


@dataclass(frozen=True, slots=True)
class Outcome:
    run_id: str
    status: Status
    reason: str | None = None
    outputs: JsonObject = field(default_factory=dict[str, JsonValue])
    outputs_hash: str | None = None


class Refused(Exception):
    """The run cannot start or resume; the message says why."""


@dataclass(frozen=True, slots=True)
class Consult:
    """What the doctor reads: the failed attempt and every event of its slot so far."""

    run_id: str
    node_definition: JsonObject
    slot: Slot
    attempt: int
    events: tuple[Event, ...]
    mode: Mode = "test"


@dataclass(frozen=True, slots=True)
class Verdict:
    classification: Classification
    hint: str | None = None


class Doctor(Protocol):
    """The ladder's doctor step (AD-16): a cheap `llm` node on the `doctor` role from EP10, which
    classifies a failure and never edits a definition."""

    async def classify(self, consult: Consult) -> Verdict: ...


def recorded_settings(
    settings: Mapping[str, object], workflow: Workflow, mode: Mode = "test"
) -> JsonObject:
    """The settings a run records for its core: chunk sizing, retry defaults, and the candidates
    of the roles its nodes use, in the order a run in `mode` tries them, so the ladder's model rung
    walks the list dispatch resolves from."""
    found: JsonObject = {}
    for key in (*RUN_SETTINGS, *LADDER_SETTINGS):
        value = settings.get(key)
        if isinstance(value, tuple):
            found[key] = [v for v in cast(tuple[object, ...], value) if isinstance(v, int | str)]
        elif isinstance(value, int | float | str):
            found[key] = value
    for role in sorted({node.role for node in workflow.nodes if node.role is not None}):
        found[f"roles.{role}"] = [c.name for c in order(settings, role, mode)]
    return found


def recorded_limits(workflow: Workflow) -> JsonObject:
    """The limits he wrote, keyed as the core reads them: the run's by name, a node's as
    `<node id>.<name>`. Empty unless he wrote one; QMX has no default (AD-40)."""
    found: JsonObject = {}
    if workflow.settings.limits is not None:
        found |= workflow.settings.limits.model_dump(exclude_none=True)
    for node in workflow.nodes:
        if node.limits is not None:
            mine = node.limits.model_dump(exclude_none=True)
            found |= {f"{node.id}.{name}": value for name, value in mine.items()}
    return found


def new_run_id(now: datetime) -> str:
    return f"run-{now:%Y%m%dT%H%M%S}-{secrets.token_hex(3)}"


def workspace(home: Path, workflow_id: str) -> Path:
    return home / "workspaces" / f"wf-{workflow_id}"


def slot_keys(slot: Slot, attempt: int, **data: JsonValue) -> JsonObject:
    return {
        "node_id": slot.node_id,
        "iteration": slot.iteration,
        "partition": slot.partition,
        "attempt": attempt,
        **data,
    }


class Engine:
    """One engine on one QMX home: the ledger writer, the worker, and the runs it drives."""

    def __init__(
        self,
        home: Path,
        ledger: Ledger,
        *,
        settings: Mapping[str, object] | SettingsPort = DEFAULTS,
        worker: LocalWorker | None = None,
        wall: Callable[[], datetime] = lambda: datetime.now(UTC),
        executors: Mapping[str, AnyExecutor] | None = None,
        doctor: Doctor | None = None,
        inbox: InboxPort | None = None,
        watch_every: float | None = None,
        harness: HarnessPort | None = None,
        memory: MemoryPort | None = None,
    ) -> None:
        """`settings` given as a port are read at use, so a run starts on the settings of that
        moment (B-42). `executors` replace the built-in executor of a kind. Without a `doctor`,
        the ladder's doctor step is recorded as skipped. Without a `harness`, model nodes fail
        `unavailable`. Without `memory`, agent notes go to the memory stub over the home's
        Library."""
        self.home = home
        self.ledger = ledger
        self._settings = settings
        settings = self.settings
        self.worker = worker or LocalWorker(Capacity.of(settings))
        self.wall = wall
        self.executors = executors or {}
        self.doctor = doctor
        self.harness = harness
        self.admission = Admission(harness, settings) if harness is not None else None
        self._inbox = inbox
        self._memory = memory
        tick = settings.get("scheduler.tick")
        self.watch_every = watch_every or (float(tick) if isinstance(tick, int | float) else 60.0)
        self.claiming = True
        """False once a ledger write failed: the scheduler claims no more fires."""
        self.children: set[asyncio.Future[Outcome]] = set()
        self.live: dict[str, Run] = {}
        """The runs this engine drives now, by run id."""

    @property
    def settings(self) -> Mapping[str, object]:
        found = self._settings
        return found if isinstance(found, Mapping) else found.values()

    @property
    def inbox(self) -> InboxPort:
        if self._inbox is None:
            self._inbox = InboxTable.open(self.home)
        return self._inbox

    @property
    def memory(self) -> MemoryPort:
        if self._memory is None:
            self._memory = MemoryStub(LibraryFake.open(self.home))
        return self._memory

    def banned_values(self) -> tuple[str, ...]:
        """The home and the plan login; no script's environment may point at or under them."""
        home = self.home.resolve()
        found = [str(home), str(home / "claude"), os.environ.get("CLAUDE_CONFIG_DIR", "")]
        return tuple(value for value in found if value)

    async def start(
        self,
        root: Path,
        workflow: Workflow,
        *,
        mode: Mode,
        inputs: JsonValue,
        run_id: str | None = None,
        parent_run_id: str | None = None,
        call_depth: int = 0,
        fake: bool = False,
        priority: int = 0,
        pins: JsonObject | None = None,
    ) -> Outcome:
        """`fake` is the per-run switch that answers model nodes with the fake provider.
        `priority` orders the run's waiting work against other runs', higher first (AD-58).
        `pins` are a trigger's `{"roles": {role: row}, "effort": ...}`, which override role
        resolution for this run and are recorded on `run_created` (B-60)."""
        if not self.claiming:
            raise Refused("the engine stopped claiming work after a ledger write error")
        run_id = run_id or new_run_id(self.wall())
        if ledger_path(self.home).exists():
            with Reader.open(self.home) as reader:
                if reader.events(run_id):
                    raise Refused(f"run {run_id} already exists")
        run = Run(
            self,
            root,
            workflow,
            run_id,
            mode=mode,
            call_depth=call_depth,
            fake=fake,
            priority=priority,
            parent_run_id=parent_run_id,
            pins=pins or {},
        )
        run.create(inputs)
        return await run.drive()

    async def resume(
        self, run_id: str, *, reason: str = "operator", woke: str | None = None
    ) -> Outcome:
        """`reason` is what `run_resumed` records when nothing was left in flight. The ticker
        passes `wake` with the instant `woke` it woke the run at; a run a usage limit paused then
        records `limit`."""
        with Reader.open(self.home) as reader:
            events = reader.events(run_id)
        if not events or events[0].kind != "run_created":
            raise Refused(f"no run {run_id} in this home")
        created = events[0].data
        root = Path(str(created.get("folder")))
        found = checked(root)
        if isinstance(found, list):
            codes = " ".join(sorted({p.code for p in found}))
            raise Refused(f"the run's folder no longer runs: {codes}")
        mode: Mode = "live" if created.get("mode") == "live" else "test"
        depth = created.get("call_depth")
        priority = created.get("priority")
        parent = created.get("parent_run_id")
        pins = created.get("pins")
        run = Run(
            self,
            root,
            found[1],
            run_id,
            mode=mode,
            call_depth=depth if isinstance(depth, int) else 0,
            fake=created.get("fake") is True,
            priority=priority if isinstance(priority, int) else 0,
            parent_run_id=parent if isinstance(parent, str) else None,
            pins=pins if isinstance(pins, dict) else {},
        )
        run.events = events
        run.woke = woke
        run.recover(woken_by(events) if reason == "wake" else reason)
        return await run.drive()

    def cancel(self, run_id: str, reason: str = "operator") -> list[str]:
        """Stop a run this engine drives and every live run under it (AD-5, B-66): each records
        `run_cancelled` and its attempts are cancelled. Returns the run ids it stopped."""
        found = [run for run in self.live.values() if run_id in self.lineage(run)]
        for run in found:
            run.stop(reason)
        return [run.run_id for run in found]

    def lineage(self, run: Run) -> set[str]:
        """The run's id and those of its live ancestors."""
        found = {run.run_id}
        parent = run.parent_run_id
        while parent is not None and parent not in found:
            found.add(parent)
            above = self.live.get(parent)
            parent = above.parent_run_id if above is not None else None
        return found

    def spawn(self, outcome: Awaitable[Outcome]) -> None:
        task = asyncio.ensure_future(outcome)
        self.children.add(task)
        task.add_done_callback(self.children.discard)

    async def settle(self) -> None:
        """Wait for every child run a parent did not wait for."""
        while self.children:
            await asyncio.gather(*self.children)


class Run:
    def __init__(
        self,
        engine: Engine,
        root: Path,
        workflow: Workflow,
        run_id: str,
        *,
        mode: Mode,
        call_depth: int,
        fake: bool = False,
        priority: int = 0,
        parent_run_id: str | None = None,
        pins: JsonObject | None = None,
    ) -> None:
        self.engine = engine
        self.fake = fake
        self.priority = priority
        self.parent_run_id = parent_run_id
        self.pins: JsonObject = pins or {}
        self.settings = pinned(engine.settings, self.pins)
        """The settings this pass runs on, read once as it opens (B-42)."""
        self.root = root.resolve()
        self.definition = workflow
        self.run_id = run_id
        self.mode: Mode = mode
        self.call_depth = call_depth
        self.events: list[Event] = []
        self.now = ""
        self.ticked: datetime | None = None
        self.inflight: dict[asyncio.Task[None], StartNode] = {}
        self.progress: dict[str, int] = {}
        """Idempotency key of an attempt to how many events it wrote, heartbeats left out."""
        self.started: set[str] = set()
        """Attempts that wrote `node_started`; one held at dispatch or queued for a slot has not."""
        self.stopping: set[str] = set()
        self.noticed: dict[Slot, Raise] = {}
        """A failure's inbox item, held until the ladder's step on that failure is written."""
        self.watchdog = Watchdog(self.settings, engine.watch_every)
        self.meter = Meter()
        self.watched: datetime | None = None
        self.marked: datetime | None = None
        self.active = 0.0
        """The run's active seconds, for a `wall_seconds` limit."""
        self.woke: str | None = None
        """The reset the ticker last woke this run at."""
        self.zone = RunZone.of(engine.home, run_id)
        self.executors = self.build_executors()

    def build_executors(self) -> dict[str, AnyExecutor]:
        max_depth = self.settings.get("subworkflow.max_depth")
        manifest = self.zone.prepare_code(self.root)
        host = self.host = HostScript(
            self.zone.code, None, self.engine.banned_values(), fake=self.fake, manifest=manifest
        )

        def launch(
            root: Path, workflow: Workflow, inputs: JsonValue, run_id: str
        ) -> Awaitable[Outcome]:
            return self.engine.start(
                root,
                workflow,
                mode=self.mode,
                inputs=inputs,
                run_id=run_id,
                parent_run_id=self.run_id,
                call_depth=self.call_depth + 1,
                fake=self.fake,
                priority=self.priority,
                pins=self.pins,
            )

        built: dict[str, AnyExecutor] = {
            "trigger": Trigger(),
            "rule": Rule(),
            "loop": Loop(),
            "join": Join(),
            "wait": WaitNode(),
            "script": Script(host),
            "grader": Grader(host),
            "monitor": Monitor(host, workspace(self.engine.home, self.definition.id) / "monitors"),
            "subworkflow": Subworkflow(
                self.root,
                depth=self.call_depth,
                max_depth=max_depth if isinstance(max_depth, int) else 0,
                launch=launch,
                spawn=self.engine.spawn,
            ),
            "llm": self.llm_executor(),
            "agent": self.agent_executor(),
        }
        return built | dict(self.engine.executors)

    def agent_executor(self) -> AnyExecutor:
        engine = self.engine
        if engine.harness is None or engine.admission is None:
            return Unavailable()
        return Agent(
            self.root,
            engine.harness,
            engine.admission,
            workspace(engine.home, self.definition.id),
            record=self.append,
            memory=engine.memory,
            settings=self.settings,
        )

    def llm_executor(self) -> AnyExecutor:
        engine = self.engine
        if self.fake:
            return FakeProvider(self.root)
        if engine.harness is None or engine.admission is None:
            return Unavailable()
        return Llm(
            self.root,
            engine.harness,
            engine.admission,
            workspace(engine.home, self.definition.id),
        )

    def resolved(self, node: Node, ladder: JsonObject | None) -> JsonObject | None:
        """The candidate a model attempt runs on, chosen at dispatch from the role's list (AD-13),
        with what the ladder asks; None for a node that names no role."""
        if node.role is None:
            return ladder
        asks: JsonObject = dict(ladder or {})
        if self.fake:
            return asks | {"role": node.role, "profile": FAKE_PROFILE, "model": FAKE_PROFILE}
        harness = self.engine.harness
        profiles = harness.profiles() if harness is not None else frozenset[str]()
        found = resolve(order(self.settings, node.role, self.mode), profiles, ladder)
        if isinstance(found, str):
            return asks | {"role": node.role, "unresolved": found}
        effort = self.pins.get("effort")
        if isinstance(effort, str) and effort in EFFORTS:
            found = replace(found, effort=effort)
        return asks | found.started(node.role) | {"context_window": found.context_window}

    def write(self, kind: EventKind, data: JsonObject) -> None:
        """Write one event and raise the item it raises. A failure's item waits for the ladder's
        step on it, so the item shows what was tried for that failure too (L-47)."""
        slot = slot_of(data)
        before = self.tried(slot) if kind in NOTICED or kind == "ladder_step" else ()
        self.events.append(self.engine.ledger.append(self.run_id, kind, data, at=self.now))
        if kind == "ladder_step" and (failed := self.noticed.pop(slot, None)) is not None:
            tried = (*before, str(data.get("step")))
            self.engine.inbox.raise_item(replace(failed, tried=tried), at=self.now)
        item = raised_by(self.run_id, kind, data, before)
        if item is None:
            return
        if kind == "node_failed":
            self.noticed[slot] = item
        else:
            self.engine.inbox.raise_item(item, at=self.now)

    def flush(self) -> None:
        """Raise every failure's item still waiting for a ladder step."""
        for slot, item in self.noticed.items():
            self.engine.inbox.raise_item(replace(item, tried=self.tried(slot)), at=self.now)
        self.noticed.clear()

    def tried(self, slot: Slot) -> tuple[str, ...]:
        """The slot's ladder steps since its last park."""
        steps: list[str] = []
        for event in self.events:
            if event.kind == "ladder_step" and slot_of(event.data) == slot:
                step = str(event.data.get("step"))
                steps = [] if step == "park" else [*steps, step]
        return tuple(steps)

    def append(self, kind: EventKind, data: JsonObject, *, progress: bool = True) -> None:
        """Write one event at the recorded clock, ticking it on first when it is a second behind.
        `progress` is False for the stuck detector's own lines, which are no attempt's progress."""
        wall = self.engine.wall()
        if self.ticked is None or wall - self.ticked >= TICK:
            self.ticked, self.now = wall, utc_text(wall)
            self.write("clock_tick", {"now": self.now})
        attempt = data.get("attempt")
        if progress and isinstance(attempt, int) and "node_id" in data and kind != "heartbeat":
            key = idempotency_key(self.run_id, slot_of(data), attempt)
            self.progress[key] = self.progress.get(key, 0) + 1
            if kind == "node_started":
                self.started.add(key)
        self.write(kind, data)

    def create(self, inputs: JsonValue) -> None:
        self.ticked = self.engine.wall()
        self.now = utc_text(self.ticked)
        self.write(
            "run_created",
            {
                "mode": self.mode,
                "fake": self.fake,
                "settings": recorded_settings(self.settings, self.definition, self.mode),
                "limits": recorded_limits(self.definition),
                "workflow_id": self.definition.id,
                "folder": str(self.root),
                "content_hash": content_hash(load(self.root)),
                "parent_run_id": self.parent_run_id,
                "call_depth": self.call_depth,
                "priority": self.priority,
                "pins": self.pins,
            },
        )
        self.write("run_input", {"inputs": inputs})
        self.write("clock_tick", {"now": self.now})
        gone = dropped(self.definition)
        if gone:
            line = f"ignored {', '.join(gone)}: QMX sets no usage limit of its own"
            ignored = list[JsonValue](gone)
            self.write("log", {"level": "info", "digest": True, "line": line, "ignored": ignored})

    def state(self) -> State:
        return fold(self.definition, self.events)

    async def drive(self) -> Outcome:
        self.engine.live[self.run_id] = self
        try:
            return await self.steps()
        except LedgerWriteError as error:
            return await self.fault(error)
        finally:
            self.engine.live.pop(self.run_id, None)

    def stop(self, reason: str) -> None:
        """Record `run_cancelled` and cancel every attempt; the drive then ends `stopped`."""
        if self.state().ended is None:
            self.append("run_cancelled", {"reason": reason})
        for task in self.inflight:
            task.cancel()

    def stopped(self) -> bool:
        return self.state().ended == "stopped"

    async def steps(self) -> Outcome:
        self.active = float(self.state().active_seconds)
        while True:
            self.mark_active()
            state = self.state()
            commands = next_commands(state)
            ended: Finish | Park | Pause | Wait | None = None
            moved = False
            limits = drain(state)
            for command in commands:
                match command:
                    case StartNode() if limits and model_bearing(command.node_definition):
                        ended = Pause("limit", earliest(limits))
                    case StartNode():
                        self.launch(command)
                        moved = True
                    case Hold():
                        self.hold(command)
                        moved = True
                    case UseMemo():
                        self.settle_from_memo(command)
                        moved = True
                    case Climb():
                        await self.climb(command)
                        moved = True
                    case Finish() | Park() | Pause() | Wait():
                        ended = command
            if moved:
                continue
            if self.inflight:
                try:
                    done, _ = await asyncio.wait(
                        self.inflight,
                        timeout=self.engine.watch_every,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                except asyncio.CancelledError:
                    if not self.stopped():
                        raise
                    for task in self.inflight:
                        task.cancel()
                    await asyncio.gather(*self.inflight, return_exceptions=True)
                    return self.end(None, self.state())
                self.mark_active()
                now = self.engine.wall()
                if self.watched is None or (now - self.watched).total_seconds() >= (
                    self.engine.watch_every
                ):
                    await self.watch(now)
                for task in done:
                    del self.inflight[task]
                    if not (task.cancelled() and self.stopped()):
                        task.result()
                continue
            return self.end(ended, state)

    def wakes(self, held: Pause | Wait) -> bool:
        """Whether a hold with a `resume_at` leaves a wake (AD-10): a usage limit, a time `wait` or
        a retry backoff always does, unless it names the instant the run was just woken at and that
        instant is past, so a stale reset cannot spin the run. A `limits` pause waits for him."""
        if held.resume_at is None or (isinstance(held, Pause) and held.reason != "limit"):
            return False
        reset = datetime.fromisoformat(held.resume_at)
        woke = datetime.fromisoformat(self.woke) if self.woke is not None else None
        return reset > self.engine.wall() or reset != woke

    def look(self, kind: str, key: str) -> Look:
        """What one attempt in flight shows the stuck detector."""
        executor = self.executors.get(kind)
        if key not in self.started or kind == "subworkflow":
            return Look(0, waiting=True)
        if isinstance(executor, Agent | Llm):
            return executor.look(key)
        if isinstance(executor, Script | Grader | Monitor):
            return self.host.look(key)
        return Look(self.progress.get(key, 0))

    async def watch(self, now: datetime) -> None:
        """One tick of the stuck detector over every attempt in flight."""
        self.watched = now
        watched: list[Watched] = []
        commands: dict[str, StartNode] = {}
        for command in self.inflight.values():
            key = command.idempotency_key
            node = self.node(command.node_id)
            found = REGISTRY.kind(node.type)
            name = found.name if found is not None else ""
            look = self.look(name, key)
            busy = look.pid is not None and self.meter.busy(
                key, look.pid, children_only=look.children_only
            )
            pulse = Pulse(look.progress, look.in_flight, look.waiting, look.tool_open, busy)
            kind: Kind = "agent" if name == "agent" else "script" if name in SCRIPTS else "other"
            own = node.timeout
            watched.append(
                Watched(
                    key,
                    kind,
                    pulse,
                    look.calls,
                    own.idle_seconds if own is not None else None,
                    own.in_tool_seconds if own is not None else None,
                )
            )
            commands[key] = command
        self.meter.forget(commands)
        for action in self.watchdog.tick(now, watched):
            await self.act(action, commands[action.key])

    async def act(self, action: Action, command: StartNode) -> None:
        key = action.key
        slot = Slot(command.node_id, command.iteration, command.partition)
        agent = self.executors.get("agent")
        match action.act:
            case "warn":
                line = (
                    f"{command.node_id}: no progress for {action.quiet_seconds:.0f} s; "
                    "it is interrupted at its idle timeout"
                )
                data = slot_keys(slot, command.attempt, level="warn", line=line)
                self.append("log", data, progress=False)
            case "interrupt" if isinstance(agent, Agent):
                await agent.stop(key, "idle")
            case "stalled":
                self.engine.worker.cancel(key, stalled=True)
            case "loop" | "no_convergence":
                if key not in self.stopping:
                    self.stopping.add(key)
                    line = f"{command.node_id}: the stuck detector found {action.act}; it stops"
                    data = slot_keys(slot, command.attempt, level="info", digest=True, line=line)
                    self.append("log", data, progress=False)
                if isinstance(agent, Agent):
                    await agent.stop(key, action.act)
            case _:
                pass

    def mark_active(self) -> None:
        """Count the run's active time for a `wall_seconds` limit: wall time while an attempt
        runs outside a recorded wait, a gap past `MAX_TICKS` ticks (host sleep) counted as that
        many ticks only, and recorded on a run-level `heartbeat` when it moves a second."""
        now = self.engine.wall()
        last, self.marked = self.marked, now
        limits = self.definition.settings.limits
        if last is None or limits is None or limits.wall_seconds is None:
            return
        if not any(c.idempotency_key in self.started for c in self.inflight.values()):
            return
        before = int(self.active)
        gap = min((now - last).total_seconds(), MAX_TICKS * self.engine.watch_every)
        self.active += max(gap, 0.0)
        if int(self.active) > before:
            self.append("heartbeat", {"active_seconds": int(self.active)})

    async def fault(self, error: LedgerWriteError) -> Outcome:
        """The ledger cannot be written: stop claiming, stop this run's attempts, and raise the
        item the operator must see. The run is folded on the next resume."""
        self.engine.claiming = False
        for task in self.inflight:
            task.cancel()
        await asyncio.gather(*self.inflight, return_exceptions=True)
        self.inflight.clear()
        at = self.now or utc_text(self.engine.wall())
        self.engine.inbox.raise_item(ledger_fault(self.run_id, error), at=at)
        return Outcome(self.run_id, "interrupted", str(error))

    def node(self, node_id: str) -> Node:
        return next(n for n in self.definition.nodes if n.id == node_id)

    async def climb(self, command: Climb) -> None:
        slot = Slot(command.node_id, command.iteration, command.partition)
        at = None
        if command.step == "retry":
            at = resume_at(Hold(*slot, command.seconds or 0), self.now)
        data = step_data(command, at)
        doctor = self.engine.doctor
        if command.step == "doctor" and doctor is None:
            data |= {"skipped": True, "reason": NO_DOCTOR}
        self.append("ladder_step", data)
        if command.step != "doctor" or doctor is None:
            return
        node = self.node(command.node_id)
        events = tuple(e for e in self.events if "node_id" in e.data and slot_of(e.data) == slot)
        consult = Consult(
            self.run_id, node_definition(node), slot, command.attempt, events, self.mode
        )
        try:
            verdict = await doctor.classify(consult)
        except Exception:  # a broken doctor must not stop the run
            verdict = Verdict("unavailable")
        found: JsonObject = {"classification": verdict.classification, "hint": verdict.hint}
        self.append("doctor_verdict", slot_keys(slot, command.attempt) | found)

    def launch(self, command: StartNode) -> None:
        self.append(
            "node_scheduled",
            slot_keys(
                Slot(command.node_id, command.iteration, command.partition),
                command.attempt,
                memo_key=command.memo_key,
                plan=command.plan,
                **({"ladder": command.ladder} if command.ladder is not None else {}),
            ),
        )
        node = next(n for n in self.definition.nodes if n.id == command.node_id)
        slot = Slot(command.node_id, command.iteration, command.partition)
        own = node.timeout
        timeouts: JsonObject | None = None
        if own is not None:
            timeouts = own.model_dump(exclude_none=True) or None
        kind = REGISTRY.kind(node.type)
        agent = kind is not None and kind.name == "agent"
        session = resumed_chat(self.events, slot, command.attempt) if agent else None
        pins = self.definition.pin_data or {}
        pinned = pins.get(node.name) if self.mode == "test" else None
        job = NodeJob(
            run_id=command.run_id,
            node_id=command.node_id,
            iteration=command.iteration,
            partition=command.partition,
            attempt=command.attempt,
            memo_key=command.memo_key,
            idempotency_key=command.idempotency_key,
            node_definition=command.node_definition,
            inputs=command.inputs,
            now=command.now,
            mode=self.mode,
            workspace=str(self.zone.root),
            timeouts=timeouts,
            resolved_model=self.resolved(node, command.ladder),
            pinned_outputs=pinned_outputs(pinned) if pinned is not None else None,
            session=session,
            priority=self.priority,
        )
        executor = self.executors.get(kind.name if kind is not None else "")
        gate = executor.hold(job) if isinstance(executor, Agent) else None
        task = asyncio.create_task(self.attempt(job, gate))
        self.inflight[task] = command

    async def attempt(self, job: NodeJob, gate: asyncio.Event | None = None) -> None:
        kind = REGISTRY.kind(str(job.node_definition.get("type")))
        executor = self.executors[kind.name if kind is not None else ""]
        if gate is not None:
            await gate.wait()
        result = await self.engine.worker.run(job, executor, self.append)
        slot = Slot(job.node_id, job.iteration, job.partition)
        if isinstance(result, Failed) and result.effect_state == "unknown":
            self.unknown(slot, job.attempt, result.code, result.message)
            return
        keys = slot_keys(slot, job.attempt)
        for name, data in ending(result):
            self.append(cast(EventKind, name), keys | data)

    def settle_from_memo(self, command: UseMemo) -> None:
        slot = Slot(command.node_id, command.iteration, command.partition)
        self.append(
            "node_finished",
            slot_keys(slot, 0, memo=True, memo_key=command.memo_key, outputs=command.outputs),
        )

    def hold(self, command: Hold) -> None:
        self.append(
            "node_waiting",
            {
                "node_id": command.node_id,
                "iteration": command.iteration,
                "partition": command.partition,
                "reason": "wait",
                "resume_at": resume_at(command, self.now),
                "event": command.event,
            },
        )

    def end(self, command: Finish | Park | Pause | Wait | None, state: State) -> Outcome:
        outcome = self.ended(command, state)
        self.flush()
        return outcome

    def ended(self, command: Finish | Park | Pause | Wait | None, state: State) -> Outcome:
        match command:
            case Finish():
                digest = fingerprint(command.outputs)
                self.append("run_finished", {"status": "passed", "outputs_hash": digest})
                return Outcome(self.run_id, "passed", None, command.outputs, digest)
            case Park():
                self.append("ladder_step", step_data(command))
                return Outcome(self.run_id, "failed", command.reason)
            case Pause():
                if command.detail is not None:
                    self.append("log", limits_line(command.detail))
                if self.wakes(command):
                    self.engine.ledger.write(put_wake(self.run_id, str(command.resume_at)))
                paused: JsonObject = {"reason": command.reason, "resume_at": command.resume_at}
                self.append("run_paused", paused)
                return Outcome(self.run_id, "waiting", command.reason)
            case Wait():
                if self.wakes(command):
                    self.engine.ledger.write(put_wake(self.run_id, str(command.resume_at)))
                return Outcome(self.run_id, "waiting", f"waiting on {' '.join(command.node_ids)}")
            case None if state.ended == "stopped":
                return Outcome(self.run_id, "stopped", "the run was cancelled")
            case None:
                status: Status = "passed" if state.ended == "passed" else "failed"
                return Outcome(self.run_id, status, f"the run already ended {state.ended}")

    def recover(self, reason: str = "operator") -> None:
        """Fold what a dead engine left in flight, then open a new pass. A slot whose step may have
        reached the outside world waits on its gate, and the fold keeps it waiting over the pass.
        First the run's zone: scripts that escaped the Job object are stopped, a complete staged
        commit rolls forward and an overlay the dead engine left is deleted (AD-51)."""
        sweep(self.zone)
        recorded = [e.data for e in self.events if e.kind == "zone_committed"]
        for commit in self.zone.recover():
            if (commit.sha256 or commit.deleted) and commit.data() not in recorded:
                self.append("zone_committed", commit.data())
            self.zone.finish(commit)
        state = self.state()
        if state.ended in ("passed", "stopped"):
            return
        interrupted = False
        for slot, run in state.nodes.items():
            if run.phase == "scheduled":
                message = "the engine stopped before the attempt started"
                failed = failure("interrupted", message, True, "before")
                self.append("node_failed", slot_keys(slot, run.attempt) | failed)
            elif run.phase == "started":
                message = "the engine stopped mid-attempt; the outcome is unknown"
                self.unknown(slot, run.attempt, "interrupted", message)
            else:
                continue
            interrupted = True
        self.append("run_resumed", {"reason": "interrupted" if interrupted else reason})
        restarts = self.state().restarts
        allowed = self.settings.get("crash_loop.restarts")
        if interrupted and isinstance(allowed, int) and restarts >= allowed:
            why = f"crash loop: the engine stopped mid-run {restarts} times"
            self.append("ladder_step", {"step": "park", "reason": why, "crash_loop": restarts})

    def unknown(self, slot: Slot, attempt: int, code: str, message: str) -> AfterUnknown:
        """Record an attempt whose outcome is unknown: a crash, a timeout or a cancel. A step that
        may rerun ends failed; any other waits on a gate that shows its idempotency key. A
        cancelled step that may rerun ends failed and is not retried, since the cancel was a stop
        (B-37)."""
        node = next(n for n in self.definition.nodes if n.id == slot.node_id)
        definition = node_definition(node)
        earlier = sum(
            1
            for e in self.events
            if e.kind == "node_failed"
            and e.data.get("effect_state") == "unknown"
            and (e.data.get("node_id"), e.data.get("iteration"), e.data.get("partition"))
            == (slot.node_id, slot.iteration, slot.partition)
        )
        verdict = after_unknown(definition, earlier)
        key = idempotency_key(self.run_id, slot, attempt)
        if verdict == "retry":
            retryable = code != CANCELLED
            self.append(
                "node_failed",
                slot_keys(slot, attempt) | failure(code, message, retryable, "unknown"),
            )
            if model_bearing(definition):
                line = f"{node.name}: a model call of unknown outcome ({key}) is retried once"
                self.append(
                    "log",
                    slot_keys(
                        slot, attempt, level="info", digest=True, line=line, idempotency_key=key
                    ),
                )
            return verdict
        self.append(
            "gate_opened",
            slot_keys(
                slot,
                attempt,
                category="irreversible_external",
                effect=effect_of(definition),
                idempotency_key=key,
                ask=f"{node.name} may have reached the outside world ({code}). "
                f"Retry with key {key}?",
                options=["retry (may duplicate)", "stop"],
            ),
        )
        self.append(
            "node_waiting",
            slot_keys(
                slot,
                attempt,
                reason="gate",
                resume_at=None,
                code=code,
                effect_state="unknown",
                idempotency_key=key,
                signature=signature(code, message),
            ),
        )
        return verdict


def drain(state: State) -> list[str | None]:
    """The `resume_at` of every slot waiting on a usage limit in this pass; any one drains the
    run."""
    return [
        run.resume_at
        for run in state.nodes.values()
        if run.phase == "waiting" and run.reason == "limit"
    ]


def earliest(times: list[str | None]) -> str | None:
    known = [t for t in times if t is not None]
    return min(known, key=datetime.fromisoformat) if known else None


def woken_by(events: list[Event]) -> str:
    """Why a wake resumes the run: the reason of its pause in this pass, else `wake`."""
    for event in reversed(events):
        if event.kind == "run_resumed":
            break
        if event.kind == "run_paused":
            return str(event.data.get("reason"))
    return "wake"


def pinned(settings: Mapping[str, object], pins: JsonObject) -> Mapping[str, object]:
    """The settings with a trigger's role pins over the roles they name (B-60)."""
    roles = pins.get("roles")
    if not isinstance(roles, dict) or not roles:
        return settings
    found = dict(settings)
    for role, row in roles.items():
        rows = [row] if isinstance(row, str) else row if isinstance(row, list) else []
        kept = tuple(r for r in rows if isinstance(r, str))
        if kept:
            found[f"roles.{role}"] = kept
    return found


def resumed_chat(events: list[Event], slot: Slot, attempt: int) -> str | None:
    """The chat the slot's previous attempt left when the engine died mid-attempt, else None."""
    chat: str | None = None
    died = False
    for event in events:
        if "node_id" not in event.data or slot_of(event.data) != slot:
            continue
        if event.data.get("attempt") != attempt - 1:
            continue
        found = event.data.get("session_id")
        if event.kind == "heartbeat" and isinstance(found, str):
            chat = found
        elif event.kind == "node_failed":
            died = event.data.get("code") == "interrupted"
    return chat if died else None


def pinned_outputs(pinned: Mapping[str, list[JsonValue]]) -> JsonObject:
    """A node's `pinData` as outputs by port: one pinned item is the port's value, more are a
    list."""
    return {port: items[0] if len(items) == 1 else list(items) for port, items in pinned.items()}


def failure(code: str, message: str, retryable: bool, effect_state: str) -> JsonObject:
    return {
        "code": code,
        "message": message,
        "signature": signature(code, message),
        "retryable": retryable,
        "effect_state": effect_state,
    }
