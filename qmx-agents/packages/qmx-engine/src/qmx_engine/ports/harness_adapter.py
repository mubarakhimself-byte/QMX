"""`HarnessPort` (SOLUTION-DESIGN 8.4): the engine's one door to model chats, over the harness's
public names only.

Every engine chat is a Background chat titled with its attempt's idempotency key, in the workflow's
workspace `workspaces/wf-<id>/`. Every prompt goes as `InjectedText`, never as operator text. A
turn ends when the chat record reads `turn == "idle"` (EP0 FINDINGS: the harness writes the turn's
`model_call` row before that, so the tokens are already in the journal). While a turn runs, every
permission ask is rejected at once with "unattended run" (ruling 57). A lost CLI or a refused
plugin also ends the turn idle, with a `needs_you` block saying why.

An agent chat also passes `compact_at` and per-chat `ChatHooks` (H15, H16). The harness refuses
both when it builds the `NewChat`, before any launch, and that refusal is `CompactRefused`, so the
caller can fall back. A turn reports the tool calls and compactions its session blocks show, which
the caller reconciles against what the hooks reported.

`activity` is what the stuck detector reads while a turn runs: the tool calls the session blocks
show since the latest send, with their arguments and results, whether the turn still runs, and the
chat's CLI process, whose children run its tools. `queued` tells it a send that waits for a slot
in the harness slot table, so that wait is never judged idle.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, Protocol, cast

from pydantic import JsonValue
from qma.harness import (
    AskId,
    Background,
    ChatHooks,
    Harness,
    InjectedText,
    LaunchRefused,
    NewChat,
    Reject,
    SessionId,
)
from qma.launcher import pid_path, read_pid_record

from qmx_engine.roles import PLAN

POLL_SECONDS: Final = 0.05
REJECTION: Final = "unattended run"
TOKEN_FIELDS: Final = {
    "input_tokens": "in",
    "output_tokens": "out",
    "cache_read_tokens": "cache_read",
    "cache_write_tokens": "cache_write",
}
CONTEXT_FIELDS: Final = ("input_tokens", "cache_read_tokens", "cache_write_tokens")

type JsonObject = dict[str, JsonValue]
type Effort = Literal["low", "medium", "high", "xhigh", "max"]


class Refusal(Exception):
    """The harness refused a launch or a send; the message is its reason."""


class CompactRefused(Refusal):
    """The harness refused the chat's `compact_at` or `hooks`; nothing was launched."""


@dataclass(frozen=True, slots=True)
class PlanUse:
    """The plan account's use, from `Harness.usage()`."""

    five_hour: float | None
    """The last five-hour reading, a fraction from 0 to 1; None when there is none."""
    resets_at: str | None
    """When the five-hour window resets."""
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
    """The turn's last text block."""
    tokens: dict[str, int] = field(default_factory=dict[str, int])
    cost_usd: float | None = None
    asks_rejected: int = 0
    needs_you: str | None = None
    """Why the turn failed, when it did."""
    timed_out: bool = False
    idle: bool = False
    """The turn was interrupted because no block arrived for the idle limit."""
    tools: tuple[ToolCall, ...] = ()
    compactions: tuple[str, ...] = ()
    """The trigger of each compaction the session recorded during the turn."""
    context: int | None = None
    """The context the turn's last model call read: input plus cache read and cache write."""


@dataclass(frozen=True, slots=True)
class ToolStep:
    """One tool call the session shows: `result` is None while the call is open."""

    id: str
    name: str
    arguments: JsonValue
    result: str | None = None
    error: bool = False


@dataclass(frozen=True, slots=True)
class Activity:
    blocks: int
    """Blocks the session wrote since the latest send."""
    steps: tuple[ToolStep, ...] = ()
    running: bool = False
    """The turn has not ended."""
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
        compact_at: float | None = None,
        hooks: ChatHooks | None = None,
    ) -> str: ...

    async def send(self, chat: str, text: str, *, priority: int = 0) -> None:
        """Returns once the prompt is sent. A send waits in the harness slot table, the only
        chat-slot counter, served by `priority` and then age (AD-58)."""
        ...

    def queued(self, chat: str) -> bool:
        """Whether the chat's send waits for a slot: a recorded wait, never an idle attempt."""
        ...

    async def wait_turn(
        self, chat: str, *, timeout: float | None = None, idle: float | None = None
    ) -> Turn:
        """The turn once it ends. `timeout` and `idle` interrupt it; an engine attempt passes
        neither, since the stuck detector decides when an attempt stopped moving."""
        ...

    async def interrupt(self, chat: str) -> None: ...

    def context(self, chat: str) -> int | None:
        """The context the chat's latest model call read, as `Turn.context`."""
        ...

    def activity(self, chat: str) -> Activity:
        """What the chat shows since the latest send, while its turn runs."""
        ...


class HarnessAdapter:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness
        self.marks: dict[str, tuple[int, int]] = {}
        """Each chat's last session event id and journal line count before its latest send."""

    def profiles(self) -> frozenset[str]:
        rows = self.harness.control.settings_get("providers")
        return frozenset({PLAN, *rows})

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
        compact_at: float | None = None,
        hooks: ChatHooks | None = None,
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
                hooks=hooks,
            )
        except LaunchRefused as refused:
            raise CompactRefused(str(refused)) from None
        try:
            return str(await self.harness.start_chat(spec))
        except LaunchRefused as refused:
            raise Refusal(str(refused)) from None

    async def send(self, chat: str, text: str, *, priority: int = 0) -> None:
        self.marks[chat] = (self._last_event(chat), len(self._journal(chat)))
        try:
            await self.harness.send(SessionId(chat), InjectedText(text), priority=priority)
        except LaunchRefused as refused:
            raise Refusal(str(refused)) from None

    def queued(self, chat: str) -> bool:
        return SessionId(chat) in self.harness.slot_table().waiting

    async def wait_turn(
        self, chat: str, *, timeout: float | None = None, idle: float | None = None
    ) -> Turn:
        after, rows = self.marks.get(chat, (0, 0))
        answered: set[int] = set()
        deadline = None if timeout is None else time.monotonic() + timeout
        seen, quiet_since = 0, time.monotonic()
        while True:
            blocks = self._blocks(chat, after)
            for block in blocks:
                content = block.get("content")
                if (
                    block.get("type") == "permission"
                    and isinstance(content, dict)
                    and content.get("state") == "asking"
                    and isinstance(seq := block.get("seq"), int)
                    and seq not in answered
                ):
                    self.harness.answer(AskId(SessionId(chat), seq), Reject(REJECTION))
                    answered.add(seq)
            now = time.monotonic()
            if len(blocks) > seen:
                seen, quiet_since = len(blocks), now
            idled = idle is not None and now - quiet_since > idle
            done = self._turn(chat) == "idle"
            if done or (deadline is not None and now > deadline) or idled:
                break
            await asyncio.sleep(POLL_SECONDS)
        if not done:
            await self.harness.interrupt(SessionId(chat))
        blocks = self._blocks(chat, after)
        contents = [(b.get("type"), b.get("content")) for b in blocks]
        texts = [c for kind, c in contents if kind == "text" and isinstance(c, dict)]
        text = texts[-1].get("text") if texts else None
        needs = [c for kind, c in contents if kind == "needs_you" and isinstance(c, dict)]
        reason = needs[-1].get("reason") if needs else None
        journal = self._journal(chat)[rows:]
        tokens, cost = spent(journal)
        return Turn(
            text=text if isinstance(text, str) else None,
            tokens=tokens,
            cost_usd=cost,
            asks_rejected=len(answered),
            needs_you=reason if isinstance(reason, str) else None,
            timed_out=not done,
            idle=not done and idled,
            tools=tool_calls(blocks),
            compactions=tuple(
                str(c.get("trigger"))
                for kind, c in contents
                if kind == "changed" and isinstance(c, dict) and c.get("kind") == "compacted"
            ),
            context=context_of(journal),
        )

    async def interrupt(self, chat: str) -> None:
        await self.harness.interrupt(SessionId(chat))

    def context(self, chat: str) -> int | None:
        return context_of(self._journal(chat))

    def activity(self, chat: str) -> Activity:
        after, _ = self.marks.get(chat, (0, 0))
        blocks = self._blocks(chat, after)
        record = read_pid_record(pid_path(self.harness.home.procs_dir, chat))
        return Activity(
            len(blocks),
            tool_steps(blocks),
            self._turn(chat) != "idle",
            None if record is None else record.cli_pid,
        )

    def _turn(self, chat: str) -> str | None:
        path = self.harness.home.chats_dir / f"{chat}.json"
        try:
            found = json.loads(path.read_text(encoding="utf-8")).get("turn")
        except OSError, ValueError:
            return None
        return found if isinstance(found, str) else None

    def _blocks(self, chat: str, after: int) -> list[JsonObject]:
        found: list[JsonObject] = []
        while True:
            page = self.harness.control.events("sessions", after, chat, 1000)
            for event in page:
                data = event.get("data")
                if isinstance(data, dict) and data.get("type") == "block":
                    block = data.get("block")
                    if isinstance(block, dict):
                        found.append(block)
            if len(page) < 1000:
                return found
            last = page[-1].get("id")
            after = last if isinstance(last, int) else after + len(page)

    def _last_event(self, chat: str) -> int:
        last, after = 0, 0
        while True:
            page = self.harness.control.events("sessions", after, chat, 1000)
            if page:
                found = page[-1].get("id")
                last = after = found if isinstance(found, int) else last
            if len(page) < 1000:
                return last

    def _journal(self, chat: str) -> list[str]:
        path = self.harness.home.root / "runs" / chat / "journal.jsonl"
        try:
            return path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []


def tool_calls(blocks: list[JsonObject]) -> tuple[ToolCall, ...]:
    """Each tool call the `tool` blocks show, in the order it started. A started block names the
    call; a later block with the same id says whether it ended in an error."""
    names: dict[str, str] = {}
    errors: dict[str, str] = {}
    for block in blocks:
        content = block.get("content")
        if block.get("type") != "tool" or not isinstance(content, dict):
            continue
        tool_id, name, state = content.get("id"), content.get("name"), content.get("state")
        if not isinstance(tool_id, str):
            continue
        if state == "started" and isinstance(name, str):
            names.setdefault(tool_id, name)
        elif state == "error":
            errors[tool_id] = str(content.get("result", ""))[:200]
    return tuple(ToolCall(i, n, errors.get(i)) for i, n in names.items())


def tool_steps(blocks: list[JsonObject]) -> tuple[ToolStep, ...]:
    """Each tool call the `tool` blocks show, in the order it started, with its result once a
    later block with the same id ended it."""
    started: dict[str, ToolStep] = {}
    for block in blocks:
        content = block.get("content")
        if block.get("type") != "tool" or not isinstance(content, dict):
            continue
        tool_id, state = content.get("id"), content.get("state")
        if not isinstance(tool_id, str):
            continue
        name = content.get("name")
        if state == "started" and isinstance(name, str):
            started.setdefault(tool_id, ToolStep(tool_id, name, content.get("arguments")))
        elif state in ("finished", "error") and tool_id in started:
            result = content.get("result")
            text = result if isinstance(result, str) else json.dumps(result)
            started[tool_id] = replace(started[tool_id], result=text, error=state == "error")
    return tuple(started.values())


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


def context_of(lines: list[str]) -> int | None:
    calls = model_calls(lines)
    if not calls:
        return None
    return sum(n for name in CONTEXT_FIELDS if isinstance(n := calls[-1].get(name), int))


def spent(lines: list[str]) -> tuple[dict[str, int], float | None]:
    """Tokens and the plan's cost estimate summed over a chat's `model_call` journal rows. A key
    row reports no cost, and some routes report no cache write (EP0 FINDINGS)."""
    tokens = dict.fromkeys(TOKEN_FIELDS.values(), 0)
    cost: float | None = None
    for payload in model_calls(lines):
        for source, name in TOKEN_FIELDS.items():
            count = payload.get(source)
            if isinstance(count, int):
                tokens[name] += count
        metadata = payload.get("metadata")
        found = metadata.get("cost") if isinstance(metadata, dict) else None
        if isinstance(found, int | float):
            cost = (cost or 0.0) + float(found)
    return tokens, cost
