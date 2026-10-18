"""The `agent` node (AD-25, AD-34, SOLUTION-DESIGN 2.3): one harness Background chat per chunk,
which reads, uses tools and answers with one JSON document validated like an `llm` node's.

The prompt states the node's brief, its skills, its tool list and its write zone, static part
first so every chunk of the node reads it from the cache (`prompts`). Every ask is rejected, so an
agent node writes nothing on the host until the sandbox packet (L6). An agent has no turn,
tool-call or run-time ceiling (AD-40): the runner's stuck detector (AD-16) reads `look` every tick
and calls `stop` when the attempt stopped moving, loops or does not converge. A stopped chat is
interrupted; a looping or flailing one then gets one summary turn and ends `stalled` with that
summary.

The warm-first gate is the runner's, at dispatch (AD-9): `hold` returns the event a chunk waits on
before it starts, so a held chunk writes no `node_started` and is never an idle attempt. The first
chunk of a node's iteration sets it when its first turn ends, so the others read its prompt cache.

Each chat starts with `compact_at` and per-chat hooks (H15, H16). PostToolUse records each tool
call as a child span as it happens, PreCompact writes the working state with `memory_note` and
records the compaction, and Stop and SubagentStop are logged. At each turn end the session's
`tool` blocks are reconciled: a call no hook reported still gets its span. The harness keeps
`compact_at` and hooks in memory only, so a refused option or a chat picked up after a restart runs
without them, and AD-34's fallback stands in: when the context passes `compact_at` plus 0.05 with
no compaction, the agent writes a summary, it is noted as memory, and the same attempt goes on in a
fresh chat seeded with it.

The chat's session id is recorded on the attempt's first heartbeat, since `node_started` is written
before the chat exists. When the engine died mid-attempt, the next attempt picks that chat up again.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Final

from pydantic import JsonValue
from qma.harness import ChatHooks, StuckCall, stuck_call

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
from qmx_engine.ports.harness_adapter import (
    ChatsFull,
    CompactRefused,
    HarnessPort,
    Refusal,
    ToolCall,
    Turn,
)
from qmx_engine.ports.memory import MemoryPort
from qmx_engine.prompts import Prompt, payload, static
from qmx_engine.roles import DEFAULT_WINDOW, Candidate

LATER_MODES: Final = frozenset({"cli_inside", "host_harness"})
MARGIN: Final = 0.05
"""How far past `compact_at` the context may get with no compaction before the fallback."""
RESUMED: Final = (
    "The engine restarted while your last turn ran. Finish the task and reply with the final JSON "
    "document only."
)
SUMMARISE: Final = (
    "Your context is nearly full and this chat will be replaced. Write down your working state: "
    "what you read, what you found, and what is left to do. Reply with that summary only."
)
STALLED: Final = "stalled"
IDLE: Final = "the agent showed no progress past its idle timeout"
STUCK_SUMMARY: Final = (
    "Stop now and call no tool. In a few sentences, say what you tried, what keeps happening, and "
    "what you would try next. Reply with that summary only."
)

type JsonObject = dict[str, JsonValue]
type Record = Callable[[EventKind, JsonObject], None]


def rules(tools: list[str], zone: str) -> list[str]:
    offer = f"Use only these tools: {', '.join(tools)}." if tools else "Use no tools."
    return [
        offer,
        "Every request to write or edit a file or to run a command is rejected in this run: read "
        f"and answer only. Your write zone is {zone}, and it stays empty for now.",
    ]


def names(parameters: JsonObject, key: str) -> list[str]:
    found = parameters.get(key)
    return [str(n) for n in found] if isinstance(found, list) else []


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
        text = static(
            brief,
            rules(names(parameters, "tools"), job.workspace or str(self.workspace)),
            schema,
            names(parameters, "skills"),
        )
        attempt = Attempt(self, job, candidate, text, schema, warming)
        self.attempts[job.idempotency_key] = attempt
        await self.admission.acquire()
        attempt.queued = False
        try:
            return await attempt.run()
        except asyncio.CancelledError:
            if attempt.chat:
                with contextlib.suppress(Exception):
                    await self.harness.interrupt(attempt.chat)
            raise
        finally:
            await self.admission.release()


class Attempt:
    """One attempt of an agent node: its chat, the tool calls the hooks and the blocks reported,
    and its compactions."""

    def __init__(
        self,
        agent: Agent,
        job: NodeJob,
        candidate: Candidate,
        text: str,
        schema: JsonObject,
        warming: asyncio.Event | None = None,
    ) -> None:
        self.agent = agent
        self.warming = warming
        self.job = job
        self.candidate = candidate
        self.static = text
        self.schema = schema
        self.compact_at = setting(agent.settings, "agent.compact_at", 0.4)
        self.window = candidate.context_window or DEFAULT_WINDOW
        self.usage = Usage()
        self.chat = ""
        self.tools: dict[str, str] = {}
        """Tool call id to name, every call recorded so far."""
        self.hooked = 0
        """Compactions the PreCompact hook recorded during the current turn."""
        self.compactions = 0
        self.compacted = False
        """The last turn compacted, so its context reading is after the compaction."""
        self.context: int | None = None
        self.fallback: str | None = None
        """Why the chat runs without `compact_at` and hooks, when it does."""
        self.queued = True
        """Waiting for an engine chat slot: a recorded wait, not an idle attempt."""
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

    def prompt(self, seed: str | None = None) -> str:
        hint = (self.job.resolved_model or {}).get("hint")
        found = payload(self.job.inputs, hint=hint if isinstance(hint, str) else None, seed=seed)
        return Prompt(self.static, found).text

    async def run(self) -> NodeResult:
        if self.job.session is not None:
            self.chat, self.fallback = self.job.session, "the chat was picked up after a restart"
            self.usage.chat = self.chat
            self.write("heartbeat", {"note": "chat resumed", "session_id": self.chat})
            text = RESUMED
        else:
            refused = await self.start()
            if refused is not None:
                return refused
            text = self.prompt()
        for _ in range(2):
            if self.over():
                found = await self.restart()
                if not isinstance(found, str):
                    return found
                text = found
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
        if self.queued or not self.chat:
            return Look(0, waiting=self.queued, in_flight=not self.queued)
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
        found = self.usage.span() | {"tool_calls": len(self.tools), "compactions": self.compactions}
        return found | ({"fallback": self.fallback} if self.fallback is not None else {})

    def ended(self, result: NodeResult) -> NodeResult:
        if isinstance(result, Failed | Waiting):
            return replace(result, span=result.span | self.span())
        return result

    async def start(self) -> NodeResult | None:
        harness, candidate = self.agent.harness, self.candidate
        title, workspace = self.job.idempotency_key, self.agent.workspace
        try:
            if self.fallback is None:
                try:
                    self.chat = await harness.start_chat(
                        title=title,
                        profile=candidate.profile,
                        model=candidate.model,
                        effort=candidate.effort,
                        workspace=workspace,
                        compact_at=self.compact_at,
                        hooks=self.hooks(),
                    )
                except CompactRefused as refused:
                    self.fallback = f"the harness refused compact_at: {redact(str(refused))}"
            if self.fallback is not None:
                self.chat = await harness.start_chat(
                    title=title,
                    profile=candidate.profile,
                    model=candidate.model,
                    effort=candidate.effort,
                    workspace=workspace,
                )
        except Refusal as refusal:
            return failed("unavailable", redact(str(refusal)), retryable=False)
        self.usage.chat = self.chat
        found: JsonObject = {"note": "chat started", "session_id": self.chat}
        self.write("heartbeat", found | ({"fallback": self.fallback} if self.fallback else {}))
        return None

    async def turn(self, text: str) -> Turn | NodeResult:
        harness = self.agent.harness
        try:
            await harness.send(self.chat, text)
        except Refusal as refusal:
            return await self.agent.admission.refused(self.candidate, redact(str(refusal)))
        except ChatsFull as full:
            return self.ended(failed("chats_full", redact(str(full)), retryable=True))
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
        self.compacted, self.hooked = bool(turn.compactions), 0
        self.context = turn.context
        return turn

    def fraction(self, context: int | None) -> float | None:
        return None if context is None else round(context / self.window, 4)

    def over(self) -> bool:
        found = self.fraction(self.context)
        return not self.compacted and found is not None and found > self.compact_at + MARGIN

    async def restart(self) -> str | NodeResult:
        """AD-34's fallback: a summary, noted as memory, seeds a fresh chat for this attempt."""
        at = self.fraction(self.context)
        found = await self.turn(SUMMARISE)
        if not isinstance(found, Turn):
            return found
        summary = (found.text or "").strip() or "The agent wrote no summary."
        self.note(summary)
        self.compactions += 1
        self.write("compacted", {"trigger": "restart", "at_fraction": at})
        self.fallback = self.fallback or "the context passed compact_at with no compaction"
        line = (
            f"{self.job.node_id}: compaction fallback, {self.fallback}; the attempt goes on in a "
            "fresh chat seeded with its summary"
        )
        self.write("log", {"level": "info", "digest": True, "line": line, "fallback": "restart"})
        refused = await self.start()
        if refused is not None:
            return refused
        self.context = None
        return self.prompt(seed=summary)

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

    def hooks(self) -> ChatHooks:
        return ChatHooks(
            post_tool_use=self.on_tool,
            pre_compact=self.on_compact,
            stop=self.on_stop,
            subagent_stop=self.on_stop,
        )

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

    async def on_tool(self, data: Mapping[str, object]) -> None:
        tool_id, duration = data.get("tool_use_id"), data.get("duration_ms")
        if not isinstance(tool_id, str) or tool_id in self.tools:
            return
        took = duration if isinstance(duration, int) else None
        self.called(ToolCall(tool_id, str(data.get("tool_name"))), took, "hook")

    async def on_compact(self, data: Mapping[str, object]) -> None:
        trigger = compaction(data.get("trigger"))
        used = sorted(set(self.tools.values()))
        self.note(
            f"Before a compaction ({trigger}) of attempt {self.job.attempt}: "
            f"{len(self.tools)} tool calls so far ({', '.join(used) or 'none'})."
        )
        self.hooked += 1
        self.compactions += 1
        at = self.fraction(self.agent.harness.context(self.chat))
        self.write("compacted", {"trigger": trigger, "at_fraction": at})

    async def on_stop(self, data: Mapping[str, object]) -> None:
        event = str(data.get("hook_event_name"))
        found: JsonObject = {"level": "debug", "hook": event, "line": f"{event} hook"}
        if isinstance(kind := data.get("agent_type"), str):
            found["agent_type"] = kind
        self.write("log", found)


def compaction(trigger: object) -> str:
    """The span's trigger: the CLI's own auto-compaction, which `compact_at` moves, is `auto`."""
    return "auto" if trigger == "auto" else "threshold"
