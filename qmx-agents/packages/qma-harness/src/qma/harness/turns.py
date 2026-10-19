"""One turn of a chat as a program sees it: a `TurnHandle` from `Harness.run_turn`.

`events()` yields what the turn does as it happens. `result()` resolves once, when the CLI's
`ResultMessage` ends the turn or the process ends first, with no polling anywhere: the chat's
reader feeds the handle the same facts it writes to the session.

A handle attaches to a turn. A prompt sent to an idle chat opens the next turn, so its handle
attaches at once. A prompt sent while a turn runs either folds into that turn (typed while a tool
ran) or waits for a turn of its own (measured, CLI 2.1.299); its handle attaches when the CLI
replays the prompt or opens the next turn, whichever comes first.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Final, Literal

from qmx_control.service import SessionBlock

from qma.harness.project import INTERRUPTED, TurnEnded

type TurnStatus = Literal["ok", "failed", "interrupted", "unknown"]
"""`unknown`: the process ended before the turn's result, so its outcome cannot be known."""


@dataclass(frozen=True)
class Queued:
    """The send waits for a free chat slot."""


@dataclass(frozen=True)
class Started:
    """The CLI opened the turn."""


@dataclass(frozen=True)
class Projected:
    """A block the turn wrote to the chat's own session, in order."""

    block: SessionBlock


@dataclass(frozen=True)
class ToolStarted:
    id: str
    name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True)
class ToolFinished:
    id: str
    name: str
    arguments: Mapping[str, Any]
    result: str
    error: bool


@dataclass(frozen=True)
class Compaction:
    trigger: str


@dataclass(frozen=True)
class WaitingOnModel:
    """True from the moment a model request is due (the turn opened or a tool result went
    back) until the first streamed token or message of the reply."""

    waiting: bool


type TurnEvent = (
    Queued | Started | Projected | ToolStarted | ToolFinished | Compaction | WaitingOnModel
)


@dataclass(frozen=True)
class TurnTokens:
    """Summed over the turn's main-thread model replies, each counted once."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    thinking_tokens: int = 0


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: Mapping[str, Any]
    result: str | None
    """None while the call never finished inside the turn."""
    error: bool = False


@dataclass(frozen=True)
class TurnResult:
    status: TurnStatus
    text: str | None
    """The CLI's final text for the turn, or its error text when the turn failed."""
    blocks: tuple[SessionBlock, ...]
    usage: TurnTokens
    tools: tuple[ToolCall, ...]
    compactions: tuple[str, ...]
    context: int | None
    """The context the turn's last model reply read: input plus cache read and cache write."""
    terminal_reason: str | None


USAGE_FIELDS: Final = {
    "input_tokens": "input_tokens",
    "output_tokens": "output_tokens",
    "cache_read_input_tokens": "cache_read_tokens",
    "cache_creation_input_tokens": "cache_write_tokens",
}


def status_of(ended: TurnEnded | None) -> TurnStatus:
    if ended is None:
        return "unknown"
    if ended.terminal_reason in INTERRUPTED:
        return "interrupted"
    return "ok" if ended.ok else "failed"


@dataclass
class TurnHandle:
    """Read side for the caller; the `on_*` methods are the chat's feed and nobody else's."""

    prompt: str
    attached: bool = False
    _events: asyncio.Queue[TurnEvent | None] = field(
        default_factory=asyncio.Queue[TurnEvent | None]
    )
    _result: asyncio.Future[TurnResult] = field(
        default_factory=lambda: asyncio.get_running_loop().create_future()
    )
    _blocks: list[SessionBlock] = field(default_factory=list[SessionBlock])
    _tools: dict[str, ToolCall] = field(default_factory=dict[str, ToolCall])
    _compactions: list[str] = field(default_factory=list[str])
    _replies: dict[str, Mapping[str, Any]] = field(default_factory=dict[str, Mapping[str, Any]])
    _waiting: bool = False

    async def events(self) -> AsyncIterator[TurnEvent]:
        """Every event of the turn, ending when the turn ends. One reader only."""
        while (event := await self._events.get()) is not None:
            yield event

    async def result(self) -> TurnResult:
        return await asyncio.shield(self._result)

    @property
    def done(self) -> bool:
        return self._result.done()

    def _emit(self, event: TurnEvent) -> None:
        if not self.done:
            self._events.put_nowait(event)

    def _wait(self, waiting: bool) -> None:
        if waiting != self._waiting:
            self._waiting = waiting
            self._emit(WaitingOnModel(waiting))

    def on_queued(self) -> None:
        self._emit(Queued())

    def on_started(self) -> None:
        self.attached = True
        self._emit(Started())
        self._wait(True)

    def on_block(self, block: SessionBlock) -> None:
        self._blocks.append(block)
        self._emit(Projected(block))
        content: dict[str, Any] = dict(block.content)
        if block.type == "text":
            self._wait(False)
        if block.type != "tool":
            return
        call = str(content.get("id", ""))
        if content.get("state") == "started":
            arguments = content.get("arguments") or {}
            started = ToolCall(call, str(content.get("name", "")), arguments, None)
            self._tools[call] = started
            self._wait(False)
            self._emit(ToolStarted(call, started.name, arguments))
            return
        known = self._tools.get(call, ToolCall(call, "", {}, None))
        finished = ToolCall(
            call,
            known.name,
            known.arguments,
            str(content.get("result", "")),
            content.get("state") == "error",
        )
        self._tools[call] = finished
        self._emit(ToolFinished(call, known.name, known.arguments, finished.result or "", finished.error))
        self._wait(True)

    def on_delta(self) -> None:
        self._wait(False)

    def on_compaction(self, trigger: str) -> None:
        self._compactions.append(trigger)
        self._emit(Compaction(trigger))

    def on_reply(self, message_id: str, usage: Mapping[str, Any]) -> None:
        """A main-thread model reply. The CLI repeats a reply's usage on each of its content
        blocks, so the last copy per message id counts."""
        self._replies[message_id] = usage
        self._wait(False)

    def finish(self, ended: TurnEnded | None, reason: str | None = None) -> None:
        """Resolve once. `reason` stands in for the terminal reason when the turn never ran,
        such as a launch refused while the send was queued."""
        if self.done:
            return
        totals = dict.fromkeys(USAGE_FIELDS.values(), 0)
        thinking = 0
        for usage in self._replies.values():
            for name, total in USAGE_FIELDS.items():
                totals[total] += int(usage.get(name) or 0)
            details = usage.get("output_tokens_details") or {}
            thinking += int(details.get("thinking_tokens") or 0)
        last = list(self._replies.values())[-1] if self._replies else None
        context = (
            None
            if last is None
            else sum(
                int(last.get(name) or 0)
                for name in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
            )
        )
        status = "failed" if ended is None and reason is not None else status_of(ended)
        self._result.set_result(
            TurnResult(
                status=status,
                text=reason if ended is None else ended.result,
                blocks=tuple(self._blocks),
                usage=TurnTokens(**totals, thinking_tokens=thinking),
                tools=tuple(self._tools.values()),
                compactions=tuple(self._compactions),
                context=context,
                terminal_reason=reason if ended is None else ended.terminal_reason,
            )
        )
        self._events.put_nowait(None)
