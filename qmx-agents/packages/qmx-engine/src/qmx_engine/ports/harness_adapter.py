"""`HarnessPort` (SOLUTION-DESIGN 8.4): the engine's one door to model chats, over the harness's
public names only.

Every engine chat is a Background chat titled with its attempt's idempotency key, in the workflow's
workspace `workspaces/wf-<id>/`. Every prompt goes as `InjectedText`, never as operator text. A
turn ends when the chat record reads `turn == "idle"` (EP0 FINDINGS: the harness writes the turn's
`model_call` row before that, so the tokens are already in the journal). While a turn runs, every
permission ask is rejected at once with "unattended run" (ruling 57). A lost CLI or a refused
plugin also ends the turn idle, with a `needs_you` block saying why.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Literal, Protocol, cast

from pydantic import JsonValue
from qma.harness import (
    AskId,
    Background,
    ChatTableFull,
    Harness,
    InjectedText,
    LaunchRefused,
    NewChat,
    Reject,
    SessionId,
)

from qmx_engine.roles import PLAN

POLL_SECONDS: Final = 0.05
REJECTION: Final = "unattended run"
TOKEN_FIELDS: Final = {
    "input_tokens": "in",
    "output_tokens": "out",
    "cache_read_tokens": "cache_read",
    "cache_write_tokens": "cache_write",
}

type JsonObject = dict[str, JsonValue]
type Effort = Literal["low", "medium", "high", "xhigh", "max"]


class Refusal(Exception):
    """The harness refused a launch or a send; the message is its reason."""


class ChatsFull(Exception):
    """Every live chat slot was busy, so the send could not run."""


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
class Turn:
    text: str | None
    """The turn's last text block."""
    tokens: dict[str, int] = field(default_factory=dict[str, int])
    cost_usd: float | None = None
    asks_rejected: int = 0
    needs_you: str | None = None
    """Why the turn failed, when it did."""
    timed_out: bool = False


class HarnessPort(Protocol):
    def profiles(self) -> frozenset[str]:
        """The profiles a chat can run on now: the plan and every configured provider row."""
        ...

    def max_live_chats(self) -> int: ...

    async def plan_use(self) -> PlanUse:
        """The plan's use, metered first when the ledger holds no five-hour reading (HG2)."""
        ...

    async def start_chat(
        self, *, title: str, profile: str, model: str, effort: str | None, workspace: Path
    ) -> str: ...

    async def send(self, chat: str, text: str) -> None: ...

    async def wait_turn(self, chat: str, *, timeout: float) -> Turn: ...

    async def interrupt(self, chat: str) -> None: ...


class HarnessAdapter:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness
        self.marks: dict[str, tuple[int, int]] = {}
        """Each chat's last session event id and journal line count before its latest send."""

    def profiles(self) -> frozenset[str]:
        rows = self.harness.control.settings_get("providers")
        return frozenset({PLAN, *rows})

    def max_live_chats(self) -> int:
        found = self.harness.control.settings_get("budgets").get("max_live_chats", 4)
        return found if isinstance(found, int) and not isinstance(found, bool) else 4

    async def plan_use(self) -> PlanUse:
        page = await self.harness.usage()
        if not any(view.reading.window == "five_hour" for view in page.readings):
            with contextlib.suppress(LaunchRefused):
                await self.harness.meter()
            page = await self.harness.usage()
        five = next((v.reading for v in page.readings if v.reading.window == "five_hour"), None)
        rejected = sorted(
            view.limits.resets_at.isoformat()
            for view in page.windows
            if view.limits.status == "rejected" and view.limits.resets_at is not None
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
        self, *, title: str, profile: str, model: str, effort: str | None, workspace: Path
    ) -> str:
        workspace.mkdir(parents=True, exist_ok=True)
        spec = NewChat(
            title=title,
            model=model,
            effort=cast(Effort | None, effort),
            workspace=workspace,
            profile=profile,
            kind=Background(),
        )
        try:
            return str(await self.harness.start_chat(spec))
        except LaunchRefused as refused:
            raise Refusal(str(refused)) from None

    async def send(self, chat: str, text: str) -> None:
        self.marks[chat] = (self._last_event(chat), len(self._journal(chat)))
        try:
            await self.harness.send(SessionId(chat), InjectedText(text))
        except LaunchRefused as refused:
            raise Refusal(str(refused)) from None
        except ChatTableFull as full:
            raise ChatsFull(str(full)) from None

    async def wait_turn(self, chat: str, *, timeout: float) -> Turn:
        after, rows = self.marks.get(chat, (0, 0))
        answered: set[int] = set()
        deadline = time.monotonic() + timeout
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
            idle = self._turn(chat) == "idle"
            if idle or time.monotonic() > deadline:
                break
            await asyncio.sleep(POLL_SECONDS)
        if not idle:
            await self.harness.interrupt(SessionId(chat))
        blocks = self._blocks(chat, after)
        texts = [b["content"] for b in blocks if b.get("type") == "text"]
        last = texts[-1] if texts else None
        text = last.get("text") if isinstance(last, dict) else None
        needs = [b["content"] for b in blocks if b.get("type") == "needs_you"]
        reason = needs[-1].get("reason") if needs and isinstance(needs[-1], dict) else None
        tokens, cost = spent(self._journal(chat)[rows:])
        return Turn(
            text=text if isinstance(text, str) else None,
            tokens=tokens,
            cost_usd=cost,
            asks_rejected=len(answered),
            needs_you=reason if isinstance(reason, str) else None,
            timed_out=not idle,
        )

    async def interrupt(self, chat: str) -> None:
        await self.harness.interrupt(SessionId(chat))

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


def spent(lines: list[str]) -> tuple[dict[str, int], float | None]:
    """Tokens and the plan's cost estimate summed over a chat's `model_call` journal rows. A key
    row reports no cost, and some routes report no cache write (EP0 FINDINGS)."""
    tokens = dict.fromkeys(TOKEN_FIELDS.values(), 0)
    cost: float | None = None
    for line in lines:
        try:
            row: JsonValue = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict) or row.get("event") != "model_call":
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        for source, name in TOKEN_FIELDS.items():
            count = payload.get(source)
            if isinstance(count, int):
                tokens[name] += count
        metadata = payload.get("metadata")
        found = metadata.get("cost") if isinstance(metadata, dict) else None
        if isinstance(found, int | float):
            cost = (cost or 0.0) + float(found)
    return tokens, cost
