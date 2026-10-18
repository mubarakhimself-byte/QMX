"""The runner: the core, the worker and the ledger on one asyncio loop (AD-1, SOLUTION-DESIGN 3.3).

`Run.drive` folds the run's events, carries out the commands the core returns, and folds again.
Every event goes through the one `Ledger` writer before the next fold, so a worker's result is in
the ledger before the core sees it. The runner writes what SOLUTION-DESIGN 3.2 gives the core:
`node_scheduled`, a hold's `node_waiting`, a memo's `node_finished`, `ladder_step`, the doctor's
`doctor_verdict`, `run_paused` and `run_finished`. The worker writes `node_started` and
heartbeats, and the runner writes each attempt's ending from the result the worker returns.

Every event that ruling 77 sends to the operator raises its inbox item as it is written: a provider
failure, a system fault, or an irreversible external step of unknown outcome. While attempts run,
the runner wakes every `scheduler.tick` for the watchdog, which cancels a stalled attempt. A ledger
write error stops the engine claiming work and raises a `black` item.

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
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final, Literal, Protocol, cast

from pydantic import JsonValue
from qmx_ledger.journal import fingerprint

from qmx_engine.admission import Admission
from qmx_engine.core.commands import (
    Climb,
    Degrade,
    Finish,
    Hold,
    Park,
    Pause,
    StartNode,
    UseMemo,
    Wait,
)
from qmx_engine.core.fold import fold, slot_of
from qmx_engine.core.ladder import NO_DOCTOR, runaway_line, step_data
from qmx_engine.core.partitions import RUN_SETTINGS
from qmx_engine.core.ready import next_commands
from qmx_engine.core.replay import idempotency_key, node_definition
from qmx_engine.core.state import Slot, State
from qmx_engine.definition.folder import content_hash, load
from qmx_engine.definition.model import Node, Workflow
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event, EventKind, JsonObject
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Ledger, LedgerWriteError, Reader, ledger_path
from qmx_engine.nodes.agent import Agent
from qmx_engine.nodes.base import Failed, NodeJob, ending
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
from qmx_engine.nodes.wait import resume_at
from qmx_engine.ports.harness_adapter import HarnessPort
from qmx_engine.ports.inbox import InboxPort, raised_by
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.ports.memory import MemoryPort, MemoryStub
from qmx_engine.roles import order, resolve
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers.rows import put_wake
from qmx_engine.watchdog import Open, ledger_fault, stalled
from qmx_engine.workers.effects import AfterUnknown, after_unknown, effect_of, model_bearing
from qmx_engine.workers.local import AnyExecutor, LocalWorker

TICK: Final = timedelta(seconds=1)
LADDER_SETTINGS: Final = ("retry.max_tries", "retry.backoff")
NOTICED: Final = frozenset({"node_failed", "gate_opened"})

type Mode = Literal["live", "test"]
type Status = Literal["passed", "failed", "waiting", "interrupted"]
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


def runaway_guard(
    settings: Mapping[str, object], workflow: Workflow, created: datetime
) -> JsonObject:
    """The run's guard: the workflow's own limits over the engine defaults, with the wall time as
    a `deadline` instant the core compares against its clock."""
    own = workflow.settings.runaway

    def pick(name: str, key: str) -> object:
        mine = getattr(own, name) if own is not None else None
        return mine if mine is not None else settings.get(key)

    wall = pick("wall_seconds", "runaway.wall_seconds")
    guard: dict[str, object] = {
        "tokens": pick("tokens", "runaway.tokens"),
        "agents": pick("agents", "runaway.agents"),
        "tool_calls": pick("tool_calls", "runaway.tool_calls"),
        "wall_seconds": wall,
        "deadline": None,
        "on_runaway": pick("on_runaway", "on_runaway"),
    }
    if isinstance(wall, int):
        guard["deadline"] = (created + timedelta(seconds=wall)).astimezone(UTC).isoformat()
    return {key: value for key, value in guard.items() if isinstance(value, int | str)}


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
        settings: Mapping[str, object] = DEFAULTS,
        worker: LocalWorker | None = None,
        wall: Callable[[], datetime] = lambda: datetime.now(UTC),
        executors: Mapping[str, AnyExecutor] | None = None,
        doctor: Doctor | None = None,
        inbox: InboxPort | None = None,
        watch_every: float | None = None,
        harness: HarnessPort | None = None,
        memory: MemoryPort | None = None,
    ) -> None:
        """`executors` replace the built-in executor of a kind. Without a `doctor`, the ladder's
        doctor step is recorded as skipped. Without a `harness`, model nodes fail `unavailable`.
        Without `memory`, agent notes go to the memory stub over the home's Library."""
        self.home = home
        self.ledger = ledger
        self.settings = settings
        concurrency = settings.get("placement.pc.concurrency")
        self.worker = worker or LocalWorker(
            concurrency=concurrency if isinstance(concurrency, int) else 1
        )
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
        """Where the plan login lives; no script's environment may point there."""
        found = [str(self.home.resolve() / "claude"), os.environ.get("CLAUDE_CONFIG_DIR", "")]
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
    ) -> Outcome:
        """`fake` is the per-run switch that answers model nodes with the fake provider."""
        if not self.claiming:
            raise Refused("the engine stopped claiming work after a ledger write error")
        run_id = run_id or new_run_id(self.wall())
        if ledger_path(self.home).exists():
            with Reader.open(self.home) as reader:
                if reader.events(run_id):
                    raise Refused(f"run {run_id} already exists")
        run = Run(self, root, workflow, run_id, mode=mode, call_depth=call_depth, fake=fake)
        run.create(inputs, parent_run_id)
        return await run.drive()

    async def resume(
        self, run_id: str, *, reason: str = "operator", woke: str | None = None
    ) -> Outcome:
        """`reason` is what `run_resumed` records when nothing was left in flight: `limit` when
        the ticker wakes a paused run at the reset `woke`."""
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
        run = Run(
            self,
            root,
            found[1],
            run_id,
            mode=mode,
            call_depth=depth if isinstance(depth, int) else 0,
            fake=created.get("fake") is True,
        )
        run.events = events
        run.woke = woke
        run.recover(reason)
        return await run.drive()

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
    ) -> None:
        self.engine = engine
        self.fake = fake
        self.root = root.resolve()
        self.definition = workflow
        self.run_id = run_id
        self.mode: Mode = mode
        self.call_depth = call_depth
        self.events: list[Event] = []
        self.now = ""
        self.ticked: datetime | None = None
        self.inflight: dict[asyncio.Task[None], StartNode] = {}
        self.seen: dict[str, datetime] = {}
        """Idempotency key of an attempt to when it last wrote an event, for the watchdog."""
        self.woke: str | None = None
        """The reset the ticker last woke this run at."""
        self.zone = workspace(engine.home, workflow.id) / "runs" / run_id
        self.executors = self.build_executors()

    def build_executors(self) -> dict[str, AnyExecutor]:
        settings = self.engine.settings
        timeout = settings.get("timeout.script.run")
        max_depth = settings.get("subworkflow.max_depth")
        host = HostScript(
            self.root,
            float(timeout) if isinstance(timeout, int | float) else 600.0,
            self.engine.banned_values(),
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
            settings=engine.settings,
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
        found = resolve(order(self.engine.settings, node.role, self.mode), profiles, ladder)
        if isinstance(found, str):
            return asks | {"role": node.role, "unresolved": found}
        return asks | found.started(node.role) | {"context_window": found.context_window}

    def write(self, kind: EventKind, data: JsonObject) -> None:
        tried = self.tried(slot_of(data)) if kind in NOTICED else ()
        self.events.append(self.engine.ledger.append(self.run_id, kind, data, at=self.now))
        item = raised_by(self.run_id, kind, data, tried)
        if item is not None:
            self.engine.inbox.raise_item(item, at=self.now)

    def tried(self, slot: Slot) -> tuple[str, ...]:
        """The slot's ladder steps since its last park."""
        steps: list[str] = []
        for event in self.events:
            if event.kind == "ladder_step" and slot_of(event.data) == slot:
                step = str(event.data.get("step"))
                steps = [] if step == "park" else [*steps, step]
        return tuple(steps)

    def append(self, kind: EventKind, data: JsonObject) -> None:
        """Write one event at the recorded clock, ticking it on first when it is a second behind."""
        wall = self.engine.wall()
        if self.ticked is None or wall - self.ticked >= TICK:
            self.ticked, self.now = wall, wall.isoformat()
            self.write("clock_tick", {"now": self.now})
        attempt = data.get("attempt")
        if isinstance(attempt, int) and "node_id" in data:
            self.seen[idempotency_key(self.run_id, slot_of(data), attempt)] = wall
        self.write(kind, data)

    def create(self, inputs: JsonValue, parent_run_id: str | None) -> None:
        self.ticked = self.engine.wall()
        self.now = self.ticked.isoformat()
        self.write(
            "run_created",
            {
                "mode": self.mode,
                "fake": self.fake,
                "settings": recorded_settings(self.engine.settings, self.definition, self.mode),
                "runaway": runaway_guard(self.engine.settings, self.definition, self.ticked),
                "workflow_id": self.definition.id,
                "folder": str(self.root),
                "content_hash": content_hash(load(self.root)),
                "parent_run_id": parent_run_id,
                "call_depth": self.call_depth,
            },
        )
        self.write("run_input", {"inputs": inputs})
        self.write("clock_tick", {"now": self.now})

    def state(self) -> State:
        return fold(self.definition, self.events)

    async def drive(self) -> Outcome:
        try:
            return await self.steps()
        except LedgerWriteError as error:
            return await self.fault(error)

    async def steps(self) -> Outcome:
        while True:
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
                    case Degrade():
                        self.append("log", runaway_line(command.detail, "degrade"))
                        moved = True
                    case Finish() | Park() | Pause() | Wait():
                        ended = command
            if moved:
                continue
            if self.inflight:
                done, _ = await asyncio.wait(
                    self.inflight,
                    timeout=self.engine.watch_every,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if not done:
                    self.watch()
                for task in done:
                    del self.inflight[task]
                    task.result()
                continue
            return self.end(ended, state)

    def wakes(self, paused: Pause) -> bool:
        """Whether a limit pause leaves a wake: always, unless it names the reset the run was
        just woken at and that reset is past, so a stale reset cannot spin the run."""
        if paused.reason != "limit" or paused.resume_at is None:
            return False
        reset = datetime.fromisoformat(paused.resume_at)
        woke = datetime.fromisoformat(self.woke) if self.woke is not None else None
        return reset > self.engine.wall() or reset != woke

    def watch(self) -> None:
        """Cancel every attempt the watchdog finds stalled; each then fails `stalled`."""
        opens: list[Open] = []
        for command in self.inflight.values():
            node = self.node(command.node_id)
            idle = node.timeout.idle_seconds if node.timeout is not None else None
            kind = REGISTRY.kind(node.type)
            if idle is None and kind is not None and kind.name == "agent":
                found = self.engine.settings.get("timeout.agent.idle")
                idle = found if isinstance(found, int) else None
            last = self.seen.get(command.idempotency_key, self.engine.wall())
            opens.append(Open(command.idempotency_key, last, idle))
        for key in stalled(opens, self.engine.wall()):
            self.engine.worker.cancel(key, stalled=True)

    async def fault(self, error: LedgerWriteError) -> Outcome:
        """The ledger cannot be written: stop claiming, stop this run's attempts, and raise the
        item the operator must see. The run is folded on the next resume."""
        self.engine.claiming = False
        for task in self.inflight:
            task.cancel()
        await asyncio.gather(*self.inflight, return_exceptions=True)
        self.inflight.clear()
        at = self.now or self.engine.wall().isoformat()
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
        self.seen[command.idempotency_key] = self.engine.wall()
        node = next(n for n in self.definition.nodes if n.id == command.node_id)
        slot = Slot(command.node_id, command.iteration, command.partition)
        own = node.timeout
        timeouts: JsonObject | None = None
        if own is not None:
            limits = (("run_seconds", own.run_seconds), ("idle_seconds", own.idle_seconds))
            timeouts = {key: value for key, value in limits if value is not None} or None
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
            workspace=str(self.zone),
            timeouts=timeouts,
            resolved_model=self.resolved(node, command.ladder),
            pinned_outputs=pinned_outputs(pinned) if pinned is not None else None,
            session=session,
        )
        task = asyncio.create_task(self.attempt(job))
        self.inflight[task] = command

    async def attempt(self, job: NodeJob) -> None:
        kind = REGISTRY.kind(str(job.node_definition.get("type")))
        executor = self.executors[kind.name if kind is not None else ""]
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
                    self.append("log", runaway_line(command.detail, "pause"))
                if self.wakes(command):
                    self.engine.ledger.write(put_wake(self.run_id, str(command.resume_at)))
                paused: JsonObject = {"reason": command.reason, "resume_at": command.resume_at}
                self.append("run_paused", paused)
                return Outcome(self.run_id, "waiting", command.reason)
            case Wait():
                return Outcome(self.run_id, "waiting", f"waiting on {' '.join(command.node_ids)}")
            case None:
                status: Status = "passed" if state.ended == "passed" else "failed"
                return Outcome(self.run_id, status, f"the run already ended {state.ended}")

    def recover(self, reason: str = "operator") -> None:
        """Fold what a dead engine left in flight, then open a new pass. A slot whose step may have
        reached the outside world waits on its gate, and the fold keeps it waiting over the pass."""
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

    def unknown(self, slot: Slot, attempt: int, code: str, message: str) -> AfterUnknown:
        """Record an attempt whose outcome is unknown: a crash, a timeout or a cancel. A step that
        may rerun ends failed; any other waits on a gate that shows its idempotency key."""
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
            self.append(
                "node_failed", slot_keys(slot, attempt) | failure(code, message, True, "unknown")
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
