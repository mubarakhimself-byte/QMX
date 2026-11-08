"""`HarnessPort` (SOLUTION-DESIGN 27.2): the engine's one door to model chats, over the harness's
turn call (AD-53).

Every engine chat is a Background chat titled with its attempt's idempotency key. It is born with
exactly the built-in tools, toolsets and skills its node declares (each `()` is none, H2, AD-62),
its static prompt as the system text's last slot, the `engine` permission policy,
which answers its asks in-process, and the `engine` hook sink. All three and `compact_at` are on
the chat record, so a chat reloaded after a host restart keeps them (H19). Every prompt goes as
`InjectedText`. A turn ends when its handle's `result()` resolves: nothing polls.

A chat whose node declares a write tool is born in its attempt overlay, so `workspace` is that
overlay and the policy reads it as `policy_args["overlay"]` (AGW, AD-60). `Bash` and `PowerShell`
are deny rules on every chat whose node does not declare them, so even a CLI that offered them
could not run them (probe P-PERM, A3).

While a turn runs, its events feed `activity`, which the stuck detector reads: the tool calls so
far with their results, whether the turn still runs, and the chat's CLI process, whose children run
its tools. `queued` tells it a send that waits for a slot, so that wait is never judged idle.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, Protocol, cast

from pydantic import JsonValue
from qma.harness import (
    Background,
    ChatPermissions,
    Harness,
    InjectedText,
    LaunchRefused,
    NewChat,
    Projected,
    SessionId,
    ToolFinished,
    ToolStarted,
    TurnHandle,
    TurnResult,
)
from qma.launcher import pid_path, read_pid_record
from qmx_router.registry import KeyCheck, usable

from qmx_engine.policy import SHELLS, WRITES, engine_policy
from qmx_engine.sink import ENGINE, EngineSink, Listener

CONTEXT_FIELDS: Final = ("input_tokens", "cache_read_tokens", "cache_write_tokens")
DENIED: Final = frozenset({"rejected", "denied", "expired"})
LOST: Final = "the chat's process ended before the turn's result"

type JsonObject = dict[str, JsonValue]
type Effort = Literal["low", "medium", "high", "xhigh", "max"]


class Refusal(Exception):
    """The harness refused a launch or a send; the message is its reason."""


@dataclass(frozen=True, slots=True)
class PlanUse:
    """The plan account's use, from `Harness.usage()`."""

    five_hour: float | None
    """The last five-hour reading, a fraction from 0 to 1; None when there is none."""
    resets_at: str | None
    blocked_until: str | None
    """When a used-up (rejected) plan window resets."""
    stopped: str | None
    """The overage stop's reason while it holds."""


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    error: str | None = None


@dataclass(frozen=True, slots=True)
class Turn:
    text: str | None
    tokens: dict[str, int] = field(default_factory=dict[str, int])
    cost_usd: float | None = None
    asks_rejected: int = 0
    needs_you: str | None = None
    """Why the turn failed, when it did."""
    timed_out: bool = False
    tools: tuple[ToolCall, ...] = ()
    compactions: tuple[str, ...] = ()
    """The trigger of each compaction during the turn."""
    context: int | None = None
    """The context the turn's last model reply read: input plus cache read and cache write."""


@dataclass(frozen=True, slots=True)
class ToolStep:
    """One tool call of the running turn: `result` is None while the call is open."""

    id: str
    name: str
    arguments: JsonValue
    result: str | None = None
    error: bool = False


@dataclass(frozen=True, slots=True)
class Activity:
    blocks: int
    """Blocks the turn wrote so far."""
    steps: tuple[ToolStep, ...] = ()
    running: bool = False
    cli: int | None = None
    """The chat's CLI process id, when it runs."""

    @property
    def tool_open(self) -> bool:
        return any(step.result is None for step in self.steps)


class HarnessPort(Protocol):
    def profiles(self) -> frozenset[str]:
        """The profiles a chat can run on now: the plan and every configured provider row."""
        ...

    async def plan_use(self) -> PlanUse:
        """The plan's use, metered first when the ledger holds no five-hour reading (HG2)."""
        ...

    async def start_chat(
        self,
        *,
        title: str,
        profile: str,
        model: str,
        effort: str | None,
        workspace: Path,
        tools: tuple[str, ...] = (),
        toolsets: tuple[str, ...] = (),
        skills: tuple[str, ...] = (),
        system: str | None = None,
        compact_at: float | None = None,
    ) -> str: ...

    def surface_digest(self, chat: str) -> str | None:
        """The digest of the surface the chat's latest launch had, once it launched (AD-62)."""
        ...

    def listen(self, chat: str, listener: Listener | None) -> None:
        """Hand the chat's hook events to `listener` from now on; None stops them."""
        ...

    async def send(self, chat: str, text: str, *, priority: int = 0) -> None:
        """Returns once the prompt reached the chat or waits for a slot in the harness slot
        table, the only chat-slot counter, served by `priority` and then age (AD-58)."""
        ...

    def queued(self, chat: str) -> bool: ...

    async def wait_turn(self, chat: str, *, timeout: float | None = None) -> Turn:
        """The turn `send` opened, once it ends. `timeout` interrupts it; an engine attempt
        passes none, since the stuck detector decides when an attempt stopped moving."""
        ...

    async def interrupt(self, chat: str) -> None: ...

    async def close(self, chat: str) -> None:
        """End the chat's CLI process, keeping its record and transcript (H18). An attempt that
        works in an overlay closes its chat before the overlay goes, since on Windows a folder
        that is a live process's cwd cannot be removed."""
        ...

    def context(self, chat: str) -> int | None:
        """The context the chat's latest journaled model call read."""
        ...

    def activity(self, chat: str) -> Activity: ...

    def holds_task(self, chat: str) -> bool:
        """Whether the chat's transcript holds a prompt, so a resumed attempt need not resend
        its task (B-69)."""
        ...


@dataclass
class Running:
    """One chat's turn in flight: its handle, what its events showed so far, and the journal's
    length before the send, so the turn's cost is the rows after it."""

    handle: TurnHandle
    rows: int
    blocks: int = 0
    steps: dict[str, ToolStep] = field(default_factory=dict[str, ToolStep])
    reader: asyncio.Task[None] | None = None

    async def read(self) -> None:
        async for event in self.handle.events():
            match event:
                case Projected():
                    self.blocks += 1
                case ToolStarted(id=tool_id, name=name, arguments=arguments):
                    self.steps[tool_id] = ToolStep(tool_id, name, cast(JsonValue, arguments))
                case ToolFinished(id=tool_id, name=name, arguments=arguments, result=result):
                    self.steps[tool_id] = ToolStep(
                        tool_id, name, cast(JsonValue, arguments), result, event.error
                    )
                case _:
                    pass


class HarnessAdapter:
    def __init__(self, harness: Harness, *, stored: KeyCheck | None = None) -> None:
        """Registers the `engine` sink and policy on `harness`, so build the adapter before any
        engine chat launches or reloads. `stored` says whether a key row's keyring entry exists,
        the router's `key_stored` when None."""
        self.harness = harness
        self.stored = stored
        self.sink = EngineSink()
        harness.register_sink(ENGINE, self.sink)
        harness.register_policy(ENGINE, engine_policy)
        self.running: dict[str, Running] = {}
        """Each chat's turn in flight, dropped when `wait_turn` returns it."""

    def profiles(self) -> frozenset[str]:
        """The plan and the `[providers]` rows a run may use. A row that does not parse, or a key
        row whose keyring entry is missing, is left out, so role resolution moves to the next
        candidate instead of a provider that would refuse."""
        rows = self.harness.control.settings_get("providers")
        return frozenset(usable(rows, stored=self.stored))

    async def plan_use(self) -> PlanUse:
        page = await self.harness.usage()
        if not any(view.reading.window == "five_hour" for view in page.readings):
            with contextlib.suppress(LaunchRefused):
                await self.harness.meter()
            page = await self.harness.usage()
        five = next((v.reading for v in page.readings if v.reading.window == "five_hour"), None)
        now = datetime.now(UTC)
        rejected = sorted(
            view.limits.resets_at.isoformat()
            for view in page.windows
            if view.limits.status == "rejected"
            and view.limits.resets_at is not None
            and view.limits.resets_at > now
        )
        return PlanUse(
            five_hour=None if five is None else five.utilization,
            resets_at=None
            if five is None or five.resets_at is None
            else five.resets_at.isoformat(),
            blocked_until=rejected[-1] if rejected else None,
            stopped=page.hard_stop,
        )

    async def start_chat(
        self,
        *,
        title: str,
        profile: str,
        model: str,
        effort: str | None,
        workspace: Path,
        tools: tuple[str, ...] = (),
        toolsets: tuple[str, ...] = (),
        skills: tuple[str, ...] = (),
        system: str | None = None,
        compact_at: float | None = None,
    ) -> str:
        workspace.mkdir(parents=True, exist_ok=True)
        try:
            spec = NewChat(
                title=title,
                model=model,
                effort=cast(Effort | None, effort),
                workspace=workspace,
                profile=profile,
                kind=Background(),
                compact_at=compact_at,
                tools=tools,
                toolsets=toolsets,
                skills=skills,
                append_system_prompt=system,
                hook_sink=ENGINE,
                permissions=ChatPermissions(policy=ENGINE, deny=undeclared_shells(tools)),
                policy_args=policy_args(tools, workspace),
            )
            return str(await self.harness.start_chat(spec))
        except LaunchRefused as refused:
            raise Refusal(str(refused)) from None

    def surface_digest(self, chat: str) -> str | None:
        return self.harness.surface_digest(SessionId(chat))

    def listen(self, chat: str, listener: Listener | None) -> None:
        self.sink.listen(chat, listener)

    async def send(self, chat: str, text: str, *, priority: int = 0) -> None:
        rows = len(self._journal(chat))
        try:
            handle = await self.harness.run_turn(
                SessionId(chat), InjectedText(text), priority=priority
            )
        except LaunchRefused as refused:
            raise Refusal(str(refused)) from None
        running = self.running[chat] = Running(handle, rows)
        running.reader = asyncio.create_task(running.read())

    def queued(self, chat: str) -> bool:
        return SessionId(chat) in self.harness.slot_table().waiting

    async def wait_turn(self, chat: str, *, timeout: float | None = None) -> Turn:
        running = self.running[chat]
        timed_out = False
        try:
            result = await asyncio.wait_for(running.handle.result(), timeout)
        except TimeoutError:
            timed_out = True
            await self.harness.interrupt(SessionId(chat))
            result = await running.handle.result()
        finally:
            if running.reader is not None:
                running.reader.cancel()
            if self.running.get(chat) is running:
                del self.running[chat]
        cost = spent(self._journal(chat)[running.rows :])
        return turn_of(result, cost, timed_out=timed_out)

    async def interrupt(self, chat: str) -> None:
        await self.harness.interrupt(SessionId(chat))

    async def close(self, chat: str) -> None:
        await self.harness.close_chat(SessionId(chat))

    def context(self, chat: str) -> int | None:
        calls = model_calls(self._journal(chat))
        if not calls:
            return None
        return sum(n for name in CONTEXT_FIELDS if isinstance(n := calls[-1].get(name), int))

    def activity(self, chat: str) -> Activity:
        running = self.running.get(chat)
        if running is None:
            return Activity(0)
        record = read_pid_record(pid_path(self.harness.home.procs_dir, chat))
        return Activity(
            running.blocks,
            tuple(running.steps.values()),
            not running.handle.done,
            None if record is None else record.cli_pid,
        )

    def holds_task(self, chat: str) -> bool:
        projects = self.harness.home.plan_dir / "projects"
        for path in projects.glob(f"*/{chat}.jsonl"):
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                with contextlib.suppress(ValueError):
                    row: JsonValue = json.loads(line)
                    if isinstance(row, dict) and row.get("type") == "user":
                        return True
        return False

    def _journal(self, chat: str) -> list[str]:
        path = self.harness.home.root / "runs" / chat / "journal.jsonl"
        try:
            return path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []


def undeclared_shells(tools: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(SHELLS - set(tools)))


def policy_args(tools: tuple[str, ...], workspace: Path) -> JsonObject:
    found: JsonObject = {"tools": list(tools)}
    if WRITES & set(tools):
        found["overlay"] = str(workspace.resolve())
    return found


def turn_of(result: TurnResult, cost: float | None, *, timed_out: bool = False) -> Turn:
    usage = result.usage
    asks = [dict(b.content) for b in result.blocks if b.type == "permission" and "ask" in b.content]
    needs = [str(b.content.get("reason")) for b in result.blocks if b.type == "needs_you"]
    match result.status:
        case _ if timed_out:
            reason = None
        case "ok":
            reason = needs[-1] if needs else None
        case "unknown":
            reason = needs[-1] if needs else LOST
        case "failed":
            reason = result.text or result.terminal_reason or "the turn failed"
        case "interrupted":
            reason = f"the turn was interrupted ({result.terminal_reason})"
    return Turn(
        text=result.text if result.status == "ok" else None,
        tokens={
            "in": usage.input_tokens,
            "out": usage.output_tokens,
            "cache_read": usage.cache_read_tokens,
            "cache_write": usage.cache_write_tokens,
        },
        cost_usd=cost,
        asks_rejected=sum(1 for ask in asks if ask.get("state") in DENIED),
        needs_you=reason,
        timed_out=timed_out,
        tools=tuple(
            ToolCall(c.id, c.name, (c.result or "")[:200] if c.error else None)
            for c in result.tools
        ),
        compactions=result.compactions,
        context=result.context,
    )


def model_calls(lines: list[str]) -> list[JsonObject]:
    found: list[JsonObject] = []
    for line in lines:
        try:
            row: JsonValue = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("event") == "model_call":
            payload = row.get("payload")
            if isinstance(payload, dict):
                found.append(payload)
    return found


def spent(lines: list[str]) -> float | None:
    """The plan's cost estimate summed over a chat's `model_call` journal rows. A key row reports
    no cost (EP0 FINDINGS)."""
    cost: float | None = None
    for payload in model_calls(lines):
        metadata = payload.get("metadata")
        found = metadata.get("cost") if isinstance(metadata, dict) else None
        if isinstance(found, int | float):
            cost = (cost or 0.0) + float(found)
    return cost
