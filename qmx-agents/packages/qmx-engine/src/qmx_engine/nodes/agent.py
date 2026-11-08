"""The `agent` node (AD-25, AD-34, SOLUTION-DESIGN 2.3): one harness Background chat per chunk,
which reads, uses tools and answers with one JSON document validated like an `llm` node's.

The chat's Surface (AD-62) is built from what the node declares: its built-in `tools` (H2, B-51),
its `toolsets` and its `skills` filter, with nothing else offered. The brief and the output schema
ride the chat's system text as its last slot, so every chunk reads them from the cache and each turn
sends only its payload. Every span carries the digest of the surface the chat launched with. The
`engine` policy answers its asks and denies every undeclared tool with a reason the agent reads.
A node that declares no write tool is read-only. One that declares a write tool works in its
attempt overlay (AGW, AD-60, AD-51): the chat is born there, its file writes are allowed only
under it, and when the attempt ends `ok` only the node's declared `outputs.files` commit into the
run's `work/`; the chat's CLI is closed and the overlay deleted however the attempt ends. An
agent has no turn, tool-call or run-time ceiling (AD-40): the runner's stuck detector (AD-16)
reads `look` every tick and calls `stop` when the attempt stopped moving, loops or does not
converge. A stopped chat is interrupted; a looping or flailing one then gets one summary turn and
ends `stalled` with that summary.

The warm-first gate is the runner's, at dispatch (AD-9): `hold` returns the event a chunk waits on
before it starts, so a held chunk writes no `node_started` and is never an idle attempt. The first
chunk of a node's iteration sets it when its first turn ends, so the others read its prompt cache.
Each chat's slot comes from the harness slot table, the only chat-slot counter (AD-58).

The chat compacts in place at the resolved model's compaction point (AD-34): `agent.compact_at`
at 512k and above, 0.75 below it, because compacting a small window at 40 % throws most of it away.
Its record keeps that point across a restart (H19).
The `engine` hook sink hands the attempt its chat's hook events: PostToolUse records each tool
call as a child span as it happens, PreCompact writes the working state with `memory_note` and
records the compaction, and Stop and SubagentStop are logged. At each turn end the turn's tool
calls are reconciled, so a call no hook reported still gets its span.

The chat's session id is recorded on the attempt's first heartbeat, since `node_started` is written
before the chat exists. When the engine died mid-attempt, the next attempt picks that chat up again
and resends the whole task when the chat never got it (B-69).
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

from pydantic import JsonValue
from qma.harness import StuckCall, stuck_call

from qmx_engine.admission import Admission, setting
from qmx_engine.definition.lint import redact
from qmx_engine.ledger.events import EventKind
from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, Look, NodeJob, NodeResult, Ok, Waiting
from qmx_engine.nodes.llm import (
    BAD_OUTPUT,
    Usage,
    answer,
    candidate_of,
    ended_badly,
    node_schema,
    read_ref,
    repair,
)
from qmx_engine.nodes.script import failed
from qmx_engine.policy import WRITES
from qmx_engine.ports.harness_adapter import HarnessPort, Refusal, ToolCall, Turn
from qmx_engine.ports.memory import MemoryPort
from qmx_engine.ports.router import adopted
from qmx_engine.prompts import payload, static
from qmx_engine.roles import DEFAULT_WINDOW, Candidate
from qmx_engine.sink import HookData
from qmx_engine.workers.local import attempt_keys, declared_outputs
from qmx_engine.workers.zones import Overlay, RunZone, ZoneError

LATER_MODES: Final = frozenset({"cli_inside", "host_harness"})
RESUMED: Final = (
    "The engine restarted while your last turn ran. Finish the task and reply with the final JSON "
    "document only."
)
STALLED: Final = "stalled"
IDLE: Final = "the agent showed no progress past its idle timeout"
STUCK_SUMMARY: Final = (
    "Stop now and call no tool. In a few sentences, say what you tried, what keeps happening, and "
    "what you would try next. Reply with that summary only."
)

type JsonObject = dict[str, JsonValue]
type Record = Callable[[EventKind, JsonObject], None]


def names(parameters: JsonObject, key: str) -> list[str]:
    found = parameters.get(key)
    return [str(n) for n in found] if isinstance(found, list) else []


@dataclass(frozen=True, slots=True)
class Declared:
    """What an agent node declares for its chat's Surface; each unset field is empty."""

    tools: tuple[str, ...]
    toolsets: tuple[str, ...]
    skills: tuple[str, ...]

    @property
    def writes(self) -> bool:
        return bool(WRITES & set(self.tools))


class Agent:
    def __init__(
        self,
        root: Path,
        harness: HarnessPort,
        admission: Admission,
        workspace: Path,
        *,
        record: Record,
        memory: MemoryPort,
        settings: Mapping[str, object],
    ) -> None:
        self.root = root.resolve()
        self.harness = harness
        self.admission = admission
        self.workspace = workspace
        self.record = record
        self.memory = memory
        self.settings = settings
        self.warm: dict[tuple[str, int], asyncio.Event] = {}
        """Set once the first chunk of a node's iteration has ended a turn. Chunks sent together
        would each write the prompt cache and none would read it (measured on the plan), so the
        other chunks wait for the first."""
        self.firsts: dict[str, asyncio.Event] = {}
        """The event each first chunk sets, by its attempt's idempotency key."""
        self.attempts: dict[str, Attempt] = {}

    def hold(self, job: NodeJob) -> asyncio.Event | None:
        """The event this chunk waits on before it is started, or None when it may start now."""
        key = (job.node_id, job.iteration)
        if key not in self.warm:
            self.warm[key] = self.firsts[job.idempotency_key] = asyncio.Event()
            return None
        found = self.warm[key]
        return None if found.is_set() else found

    def look(self, key: str) -> Look:
        attempt = self.attempts.get(key)
        return Look(0, waiting=True) if attempt is None else attempt.look()

    async def stop(self, key: str, why: str) -> None:
        attempt = self.attempts.get(key)
        if attempt is not None:
            await attempt.halt(why)

    async def run(self, job: NodeJob) -> NodeResult:
        warming = self.firsts.pop(job.idempotency_key, None)
        try:
            return await self.attempt(job, warming)
        finally:
            if warming is not None:
                warming.set()
            self.attempts.pop(job.idempotency_key, None)

    async def attempt(self, job: NodeJob, warming: asyncio.Event | None) -> NodeResult:
        found = job.node_definition.get("parameters")
        parameters: JsonObject = found if isinstance(found, dict) else {}
        mode = parameters.get("agent_mode", "runner_outside")
        if mode in LATER_MODES:
            message = f"agent_mode {mode} needs relay run passes (harness request H11)"
            return failed("mode_not_available", message, retryable=False)
        candidate = candidate_of(job.resolved_model)
        if isinstance(candidate, str):
            return failed("unavailable", candidate, retryable=False)
        brief = read_ref(self.root, parameters, "brief_ref")
        schema = node_schema(self.root, parameters, "output_schema_ref")
        if brief is None or schema is None:
            message = "an agent node needs a readable brief_ref and a JSON output_schema_ref"
            return failed("bad_definition", message, retryable=False)
        held = await self.admission.check(candidate)
        if held is not None:
            return held
        node = job.node_definition
        declared = Declared(
            tuple(names(parameters, "tools")),
            tuple(names(node, "toolsets")),
            tuple(names(node, "skills")),
        )
        zone = RunZone(Path(job.workspace)) if declared.writes and job.workspace else None
        if declared.writes and zone is None:
            message = "an agent node that declares a write tool needs its run's zone"
            return failed("bad_definition", message, retryable=False)
        try:
            overlay = zone.open(job) if zone is not None else None
        except ZoneError as error:
            return Failed(error.code, error.message, signature(error.code, error.message), False)
        attempt = Attempt(
            self, job, candidate, static(brief, [], schema), schema, declared, warming, overlay
        )
        self.attempts[job.idempotency_key] = attempt
        try:
            try:
                result = await attempt.run()
            except asyncio.CancelledError:
                if attempt.chat:
                    with contextlib.suppress(Exception):
                        await self.harness.interrupt(attempt.chat)
                raise
            finally:
                if attempt.chat:
                    self.harness.listen(attempt.chat, None)
                    if overlay is not None:
                        await self.harness.close(attempt.chat)
            if zone is not None and overlay is not None and isinstance(result, Ok):
                result = self.commit(zone, job, overlay, result)
            return result
        finally:
            if zone is not None and overlay is not None:
                zone.discard(overlay.path)

    def commit(self, zone: RunZone, job: NodeJob, overlay: Overlay, result: Ok) -> NodeResult:
        """Only the declared `outputs.files` leave the overlay, as for a script step (AD-51); an
        agent returns no artifacts. Runs without awaiting, so no other commit interleaves."""
        try:
            done = zone.commit(job, overlay, declared_outputs(job).files, (), attempt_keys(job))
        except ZoneError as error:
            return Failed(error.code, error.message, signature(error.code, error.message), False)
        if done.sha256 or done.deleted:
            self.record("zone_committed", done.data())
        zone.finish(done)
        return result


LARGE_WINDOW: Final = 512_000
"""From this window up a chat compacts at `agent.compact_at`, and below it at 0.75 (AD-34)."""
SMALL_POINT: Final = 0.75


def compact_at(settings: Mapping[str, object], window: int) -> float:
    """The point a chat of this window compacts at: `agent.compact_at` (Claude's default 0.40) at
    512k and above, 0.75 below, because a small window compacted at 40 % loses most of it. Below
    512k the point moves only when a registry answered the window; without one the setting
    stands."""
    point = setting(settings, "agent.compact_at", 0.4)
    if window >= LARGE_WINDOW or adopted() is None:
        return point
    return SMALL_POINT


class Attempt:
    """One attempt of an agent node: its chat, the tool calls the hooks and the turns reported,
    and its compactions."""

    def __init__(
        self,
        agent: Agent,
        job: NodeJob,
        candidate: Candidate,
        system: str,
        schema: JsonObject,
        declared: Declared,
        warming: asyncio.Event | None = None,
        overlay: Overlay | None = None,
    ) -> None:
        self.agent = agent
        self.warming = warming
        self.overlay = overlay
        """The attempt's overlay when its node declares a write tool; the chat is born in it."""
        self.job = job
        self.candidate = candidate
        self.system = system
        self.schema = schema
        self.declared = declared
        self.compact_at = compact_at(agent.settings, candidate.context_window or DEFAULT_WINDOW)
        self.window = candidate.context_window or DEFAULT_WINDOW
        self.usage = Usage()
        self.chat = ""
        self.tools: dict[str, str] = {}
        """Tool call id to name, every call recorded so far."""
        self.hooked = 0
        """Compactions the PreCompact hook recorded during the current turn."""
        self.compactions = 0
        self.halted: str | None = None
        """Why the stuck detector stopped the attempt, once it did."""
        self.calls: dict[str, StuckCall] = {}
        """Each finished tool call of the current turn, as the stuck detector compares it."""
        self.judged = False
        """Whether `calls` belong to a turn the detector may judge: off from a halt until the next
        send, so a stop is not repeated over the calls that caused it."""
        zone = job.workspace or str(agent.workspace)
        self.masks = (zone, str(agent.workspace))

    def write(self, kind: EventKind, data: JsonObject) -> None:
        keys: JsonObject = {
            "node_id": self.job.node_id,
            "iteration": self.job.iteration,
            "partition": self.job.partition,
            "attempt": self.job.attempt,
        }
        self.agent.record(kind, keys | data)

    def prompt(self) -> str:
        hint = (self.job.resolved_model or {}).get("hint")
        return payload(self.job.inputs, hint=hint if isinstance(hint, str) else None)

    async def run(self) -> NodeResult:
        harness = self.agent.harness
        if self.job.session is not None:
            self.chat = self.usage.chat = self.job.session
            harness.listen(self.chat, self.on_hook)
            got = harness.holds_task(self.chat)
            note = "chat resumed" if got else "chat resumed; its task never arrived and is resent"
            self.write("heartbeat", {"note": note, "session_id": self.chat})
            text = RESUMED if got else self.prompt()
        else:
            refused = await self.start()
            if refused is not None:
                return refused
            text = self.prompt()
        for _ in range(2):
            turn = await self.turn(text)
            if not isinstance(turn, Turn):
                return turn
            if self.halted is not None:
                return await self.stalled(self.halted)
            bad = ended_badly(turn, self.usage)
            if bad is not None:
                return self.ended(bad)
            document, problem = answer(turn.text, self.schema)
            if problem is None:
                return Ok({"main": document}, span=self.span() | {"repaired": self.usage.turns > 1})
            text = repair(problem)
        return self.ended(failed("bad_output", BAD_OUTPUT, retryable=True))

    def look(self) -> Look:
        if not self.chat:
            return Look(0, in_flight=True)
        if self.agent.harness.queued(self.chat):
            return Look(0, waiting=True)
        activity = self.agent.harness.activity(self.chat)
        for step in activity.steps:
            if step.result is not None and step.id not in self.calls:
                self.calls[step.id] = stuck_call(
                    step.name, step.arguments, step.result, error=step.error, masks=self.masks
                )
        return Look(
            hash((self.usage.turns, activity.blocks, self.compactions)),
            in_flight=activity.running and not activity.tool_open,
            tool_open=activity.tool_open,
            pid=activity.cli,
            children_only=True,
            calls=tuple(self.calls.values()) if self.judged else None,
        )

    async def halt(self, why: str) -> None:
        """Interrupt the chat. Called again while the summary turn runs, it ends that turn too,
        so a chat that loops through its summary turn still stops."""
        self.halted = self.halted or why
        self.judged = False
        if self.chat:
            await self.agent.harness.interrupt(self.chat)

    async def stalled(self, why: str) -> NodeResult:
        """The stuck detector stopped this attempt. A loop or a fixer that does not converge
        gets one summary turn, which becomes the failure's output."""
        if why == "idle":
            result = failed(STALLED, IDLE, retryable=True, effect_state="unknown")
            return self.ended(replace(result, span={"stalled": why}))
        turn = await self.turn(STUCK_SUMMARY)
        summary = (turn.text or "").strip() if isinstance(turn, Turn) else ""
        summary = redact(summary) or "The agent wrote no summary."
        result = Failed(STALLED, f"{why}: {summary}", signature(STALLED, why), retryable=False)
        return self.ended(replace(result, span={"stalled": why, "output": summary}))

    def span(self) -> JsonObject:
        digest = self.agent.harness.surface_digest(self.chat) if self.chat else None
        return self.usage.span() | {
            "tool_calls": len(self.tools),
            "compactions": self.compactions,
            "surface_digest": digest,
        }

    def ended(self, result: NodeResult) -> NodeResult:
        if isinstance(result, Failed | Waiting):
            return replace(result, span=result.span | self.span())
        return result

    async def start(self) -> NodeResult | None:
        harness, candidate = self.agent.harness, self.candidate
        try:
            self.chat = await harness.start_chat(
                title=self.job.idempotency_key,
                profile=candidate.profile,
                model=candidate.model,
                effort=candidate.effort,
                workspace=self.agent.workspace if self.overlay is None else self.overlay.path,
                tools=self.declared.tools,
                toolsets=self.declared.toolsets,
                skills=self.declared.skills,
                system=self.system,
                compact_at=self.compact_at,
            )
        except Refusal as refusal:
            return failed("unavailable", redact(str(refusal)), retryable=False)
        harness.listen(self.chat, self.on_hook)
        self.usage.chat = self.chat
        self.write("heartbeat", {"note": "chat started", "session_id": self.chat})
        return None

    async def turn(self, text: str) -> Turn | NodeResult:
        harness = self.agent.harness
        try:
            await harness.send(self.chat, text, priority=self.job.priority)
        except Refusal as refusal:
            return await self.agent.admission.refused(self.candidate, redact(str(refusal)))
        self.calls, self.judged = {}, True
        turn = await harness.wait_turn(self.chat)
        if self.warming is not None:
            self.warming.set()
        self.usage.add(turn)
        for call in turn.tools:
            if call.id not in self.tools:
                self.called(call, None, "reconcile")
        for trigger in turn.compactions[self.hooked :]:
            self.compactions += 1
            self.write("compacted", {"trigger": compaction(trigger), "at_fraction": None})
        self.hooked = 0
        return turn

    def note(self, content: str) -> None:
        job = self.job
        row: JsonObject = {
            "tag": "procedure",
            "when_to_use": f"resuming node {job.node_id} partition {job.partition} of {job.run_id}",
            "content": content,
            "keywords": [job.node_id, "working-state"],
            "confidence": 1.0,
            "refs": [],
        }
        row_id = self.agent.memory.note(job.run_id, row)
        self.write("memory_written", {"scope": "run", "rows_added": 1, "row_id": row_id})

    def called(self, call: ToolCall, duration_ms: int | None, source: str) -> None:
        self.tools[call.id] = call.name
        found: JsonObject = {
            "id": call.id,
            "name": call.name,
            "duration_ms": duration_ms,
            "error": call.error,
            "placement": "host",
            "source": source,
        }
        self.write("tool_called", {"tool": found})

    async def on_hook(self, data: HookData) -> None:
        match data.get("hook_event_name"):
            case "PostToolUse":
                self.on_tool(data)
            case "PreCompact":
                self.on_compact(data)
            case "Stop" | "SubagentStop" as event:
                hook = str(event)
                found: JsonObject = {"level": "debug", "hook": hook, "line": f"{hook} hook"}
                if isinstance(kind := data.get("agent_type"), str):
                    found["agent_type"] = kind
                self.write("log", found)
            case _:
                pass

    def on_tool(self, data: HookData) -> None:
        tool_id, duration = data.get("tool_use_id"), data.get("duration_ms")
        if not isinstance(tool_id, str) or tool_id in self.tools:
            return
        took = duration if isinstance(duration, int) else None
        self.called(ToolCall(tool_id, str(data.get("tool_name"))), took, "hook")

    def on_compact(self, data: HookData) -> None:
        trigger = compaction(data.get("trigger"))
        used = sorted(set(self.tools.values()))
        self.note(
            f"Before a compaction ({trigger}) of attempt {self.job.attempt}: "
            f"{len(self.tools)} tool calls so far ({', '.join(used) or 'none'})."
        )
        self.hooked += 1
        self.compactions += 1
        context = self.agent.harness.context(self.chat)
        at = None if context is None else round(context / self.window, 4)
        self.write("compacted", {"trigger": trigger, "at_fraction": at})


def compaction(trigger: object) -> str:
    """The span's trigger: the CLI's own auto-compaction, which `compact_at` moves, is `auto`."""
    return "auto" if trigger == "auto" else "threshold"
