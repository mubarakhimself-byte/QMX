"""SDK messages to UI facts. One pure function, tested on recorded transcripts.

The block kinds are the 14 `SessionBlock` kinds that `qmx_agents.copilot.stream_turn` writes
today, served by the existing SSE route. New meaning goes inside `content`, never a new block
type.

Every Block passes through `redact`, so a Claude token an agent printed or read never reaches
`sessions_append`. Deltas leave here raw. A streamed token can arrive split over several deltas,
and a per-delta `redact` would hide the prefix and let the rest through, so `chat.py` feeds text
and thinking to a `TokenGate`, which holds back text that could still grow into a token. Tool
progress is a whole description per message, and `chat.py` redacts it whole.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from itertools import groupby
from operator import itemgetter
from typing import Any, Final, Literal, cast, get_args

from claude_agent_sdk import (
    AssistantMessage,
    ConversationResetMessage,
    Message,
    RateLimitEvent,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    TaskNotificationMessage,
    TaskProgressMessage,
    TaskStartedMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)
from claude_agent_sdk.types import (
    RateLimitInfo,
    ServerToolResultBlock,
    ServerToolUseBlock,
    TaskUpdatedMessage,
)
from qmx_control.service import SessionBlock

TOKEN_PATTERN: Final = re.compile(r"sk-ant-[A-Za-z0-9_-]+")
"""Any Claude credential (`sk-ant-oat`, `sk-ant-ort`, `sk-ant-api`). Broader than the relay's
token shapes on purpose: redaction only rewrites displayed text and never blocks a turn."""
REDACTED: Final = "[redacted sk-ant token]"
_PREFIX: Final = "sk-ant-"
_OPEN_TOKEN: Final = re.compile(r"sk-ant-[A-Za-z0-9_-]*\Z")
_WHOLE_TOKEN: Final = re.compile(r"sk-ant-[A-Za-z0-9_-]+\Z")
_TOKEN_END: Final = re.compile(r"[^A-Za-z0-9_-]")

PLAN_TOOLS: Final = frozenset({"TodoWrite", "TaskCreate", "TaskUpdate"})
AGENT_TOOLS: Final = frozenset({"Agent", "Task"})
INTERRUPTED: Final = frozenset({"aborted_streaming", "aborted_tools"})
"""`ResultMessage.terminal_reason` values the SDK documents as a cancelled turn. The CLI also sets
`is_error` on them (measured, 2.1.299), but the operator asked for the stop."""


def redact(text: str) -> str:
    return TOKEN_PATTERN.sub(REDACTED, text)


def redacted(value: Any) -> Any:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {key: redacted(item) for key, item in cast("dict[str, Any]", value).items()}
    if isinstance(value, list):
        return [redacted(item) for item in cast("list[Any]", value)]
    return value


type StreamKind = Literal["text", "thinking"]
type Piece = tuple[StreamKind, str]


class TokenGate:
    """One target's streamed text and thinking in, redacted pieces out. Holds back a tail that
    is, or could still become, a token across kinds and across any foreign block landing
    between two deltas, until a later delta settles it or `close` ends the target's stream. A
    token redacted across a kind change shows under the kind it started in."""

    def __init__(self) -> None:
        self._held: list[Piece] = []
        self._token: StreamKind | None = None

    def feed(self, kind: StreamKind, text: str) -> list[Piece]:
        out: list[Piece] = []
        if self._token is not None:
            end = _TOKEN_END.search(text)
            if end is None:
                return []
            out.append((self._token, REDACTED))
            self._token = None
            text = text[end.start() :]
        self._held.append((kind, text))
        out += self._release(_settled_length("".join(text for _, text in self._held)))
        return _merged(out)

    def close(self) -> list[Piece]:
        out: list[Piece] = [] if self._token is None else [(self._token, REDACTED)]
        self._token = None
        out += self._release(sum(len(text) for _, text in self._held))
        return _merged(out)

    def _release(self, cut: int) -> list[Piece]:
        text = "".join(text for _, text in self._held)
        kinds: list[StreamKind] = [kind for kind, piece in self._held for _ in piece]
        out: list[Piece] = []
        start = 0
        for token in TOKEN_PATTERN.finditer(text[:cut]):
            out += _runs(text[start : token.start()], kinds[start : token.start()])
            out.append((kinds[token.start()], REDACTED))
            start = token.end()
        out += _runs(text[start:cut], kinds[start:cut])
        if _WHOLE_TOKEN.match(text, cut):
            self._held, self._token = [], kinds[cut]
        else:
            self._held = _runs(text[cut:], kinds[cut:])
        return out


def _merged(pieces: list[Piece]) -> list[Piece]:
    return [
        (kind, "".join(text for _, text in run)) for kind, run in groupby(pieces, itemgetter(0))
    ]


def _runs(text: str, kinds: list[StreamKind]) -> list[Piece]:
    return [
        (kind, "".join(char for char, _ in run))
        for kind, run in groupby(zip(text, kinds, strict=True), itemgetter(1))
    ]


def _settled_length(text: str) -> int:
    open_token = _OPEN_TOKEN.search(text)
    if open_token:
        return open_token.start()
    for size in range(len(_PREFIX) - 1, 0, -1):
        if text.endswith(_PREFIX[:size]):
            return len(text) - size
    return len(text)


@dataclass(frozen=True)
class Here:
    """The fact belongs to the chat's own session."""


@dataclass(frozen=True)
class InChild:
    """The fact belongs to the child session of a native sub-agent, keyed by the Agent
    tool_use id (`parent_tool_use_id` on the message). `chat.py` owns the map from that id
    to a qmx-control child session and creates the child on first sight."""

    tool_use_id: str


type Target = Here | InChild


@dataclass(frozen=True)
class Block:
    target: Target
    block: SessionBlock


@dataclass(frozen=True)
class Delta:
    """Live only (token text, tool progress). Never stored."""

    target: Target
    kind: StreamKind | Literal["tool_progress"]
    text: str


@dataclass(frozen=True)
class TurnUsage:
    """From `ResultMessage`. Plan chats count usage here and relayed chats at the relay, so
    each profile has one usage source. Costs are list-price estimates. `model_usage` and
    `total_cost_usd` are running totals of the CLI process, and a resumed process starts from
    the session's earlier totals (measured, CLI 2.1.299)."""

    session_id: str
    model_usage: dict[str, dict[str, int | float]]
    total_cost_usd: float | None
    num_turns: int


type LimitStatus = Literal["allowed", "allowed_warning", "rejected"]
type Window = Literal[
    "five_hour",
    "seven_day",
    "seven_day_opus",
    "seven_day_sonnet",
    "seven_day_overage_included",
    "overage",
]
"""The `rateLimitType` values in Claude Code 2.1.296's `rate_limit_info` schema."""
STATUSES: Final[frozenset[str]] = frozenset(get_args(LimitStatus.__value__))
WINDOWS: Final[frozenset[str]] = frozenset(get_args(Window.__value__))


@dataclass(frozen=True)
class Reading:
    """How much of a plan window is used, as a fraction from 0 to 1."""

    window: str
    utilization: float
    resets_at: datetime | None


@dataclass(frozen=True)
class Limits:
    """From `RateLimitEvent`. Every field the SDK's `RateLimitInfo` models, plus what the CLI
    sends in `raw` that the SDK does not model."""

    window: Window | None
    status: LimitStatus
    utilization: float | None
    resets_at: datetime | None
    overage_status: LimitStatus | None
    overage_resets_at: datetime | None
    overage_disabled_reason: str | None
    using_overage: bool | None
    """True if `raw["isUsingOverage"]` or `raw["overageInUse"]` is True; None when both are
    absent."""
    overage_enabled: bool | None
    """`raw["overageEnabled"]`."""
    credits_required: bool
    """`raw["errorCode"]` is `credits_required`, or `raw` has a `credits_required` key."""
    readings: tuple[Reading, ...] = ()
    """`raw["unifiedWindows"]`: the five-hour and weekly use the CLI reports on any window's
    event."""


@dataclass(frozen=True)
class UnreadableLimits:
    """A rate-limit event this code cannot read. The overage stop treats it as paid use."""

    reason: str


@dataclass(frozen=True)
class PlanMeter:
    """The plan's use as the CLI's `/usage` text states it: the session as `five_hour`, the
    all-models week as `seven_day`."""

    readings: tuple[Reading, ...]


type PlanFact = Limits | UnreadableLimits | PlanMeter


@dataclass(frozen=True)
class StreamEnded:
    """The target's own streamed block stopped (`content_block_stop`), or the sub-agent that
    owns the target finished (its `task_notification`). That target's token gate closes."""

    target: Target


@dataclass(frozen=True)
class TurnEnded:
    """Any `ResultMessage`. The CLI opens every turn, the operator's or an injected one such as
    a background task's notification, with an `init` and ends it with one result."""

    ok: bool
    terminal_reason: str | None
    deferred_tool_use: bool
    result: str | None = None
    """The CLI's final text for the turn, or its error text when the turn failed."""


@dataclass(frozen=True)
class Compacted:
    """`compact_boundary`. Shown as an event in the session."""

    trigger: Literal["manual", "auto"]


type Fact = Block | Delta | StreamEnded | TurnUsage | PlanFact | TurnEnded | Compacted


def project(message: Message, *, redact_tokens: bool = True) -> list[Fact]:
    """Pure and total over the SDK message union. `redact_tokens=False` exists for one live
    check only (`TestMode.redaction`). Permission asks do not come through here; `chat.py`
    writes them."""
    facts = _facts(message)
    if not redact_tokens:
        return facts
    return [_redact_fact(fact) for fact in facts]


def _redact_fact(fact: Fact) -> Fact:
    match fact:
        case Block(block=block):
            return replace(
                fact, block=SessionBlock(type=block.type, content=redacted(block.content))
            )
        case _:
            return fact


def _target(parent_tool_use_id: str | None) -> Target:
    return InChild(parent_tool_use_id) if parent_tool_use_id else Here()


def _block(target: Target, kind: str, content: dict[str, Any]) -> Block:
    return Block(target, SessionBlock.model_validate({"type": kind, "content": content}))


def _facts(message: Message) -> list[Fact]:
    match message:
        case AssistantMessage():
            return _assistant(message)
        case UserMessage():
            return _tool_results(message)
        case StreamEvent():
            return _delta(message)
        case ResultMessage():
            return _result(message)
        case RateLimitEvent(rate_limit_info=info):
            return [_limits(info)]
        case SystemMessage():
            return _system(message)
        case ConversationResetMessage():
            return []


SYNTHETIC: Final = "<synthetic>"
"""The model name on messages the CLI writes itself, such as a local command's reply."""
METER: Final = (
    ("five_hour", re.compile(r"Current session: (\d+(?:\.\d+)?)% used")),
    ("seven_day", re.compile(r"Current week \(all models\): (\d+(?:\.\d+)?)% used")),
)
"""Lines of the CLI's `/usage` reply (HP0 S10)."""


def _meter(text: str) -> list[Fact]:
    readings = tuple(
        Reading(window, float(found.group(1)) / 100, None)
        for window, pattern in METER
        if (found := pattern.search(text))
    )
    return [PlanMeter(readings)] if readings else []


def _assistant(message: AssistantMessage) -> list[Fact]:
    target = _target(message.parent_tool_use_id)
    facts: list[Fact] = []
    for part in message.content:
        match part:
            case TextBlock(text=text) if text:
                facts.append(_block(target, "text", {"text": text}))
                if message.model == SYNTHETIC:
                    facts += _meter(text)
            case ToolUseBlock() | ServerToolUseBlock():
                facts += _tool_use(target, part.id, part.name, part.input)
            case ServerToolResultBlock(tool_use_id=tool_use_id, content=content):
                facts.append(
                    _block(
                        target,
                        "tool",
                        {"id": tool_use_id, "state": "finished", "result": json.dumps(content)},
                    )
                )
            case _:
                pass
    if message.error:
        facts.append(_block(target, "needs_you", {"reason": f"model error: {message.error}"}))
    return facts


def _tool_use(target: Target, tool_id: str, name: str, arguments: dict[str, Any]) -> list[Fact]:
    facts: list[Fact] = [
        _block(
            target,
            "tool",
            {"id": tool_id, "name": name, "arguments": arguments, "state": "started"},
        )
    ]
    if name in PLAN_TOOLS:
        facts.append(_block(target, "plan", {"tool": name, **arguments}))
    if name in AGENT_TOOLS:
        facts.append(
            _block(
                target,
                "agents",
                {
                    "tool_use_id": tool_id,
                    "name": arguments.get("subagent_type", "general-purpose"),
                    "description": arguments.get("description", ""),
                    "state": "working",
                },
            )
        )
    return facts


def _result_text(content: str | list[dict[str, Any]] | None) -> str:
    if content is None or isinstance(content, str):
        return content or ""
    return "\n".join(
        str(item.get("text", "")) if item.get("type") == "text" else f"[{item.get('type')}]"
        for item in content
    )


def _tool_results(message: UserMessage) -> list[Fact]:
    if isinstance(message.content, str):
        return []
    target = _target(message.parent_tool_use_id)
    return [
        _block(
            target,
            "tool",
            {
                "id": part.tool_use_id,
                "state": "error" if part.is_error else "finished",
                "result": _result_text(part.content),
            },
        )
        for part in message.content
        if isinstance(part, ToolResultBlock)
    ]


def _delta(message: StreamEvent) -> list[Fact]:
    event = message.event
    target = _target(message.parent_tool_use_id)
    if event.get("type") == "content_block_stop":
        return [StreamEnded(target)]
    if event.get("type") != "content_block_delta":
        return []
    delta = cast("dict[str, Any]", event.get("delta", {}))
    match delta.get("type"):
        case "text_delta":
            return [Delta(target, "text", str(delta.get("text", "")))]
        case "thinking_delta":
            return [Delta(target, "thinking", str(delta.get("thinking", "")))]
        case _:
            return []


def _result(message: ResultMessage) -> list[Fact]:
    facts: list[Fact] = [
        TurnUsage(
            session_id=message.session_id,
            model_usage=cast("dict[str, dict[str, int | float]]", message.model_usage or {}),
            total_cost_usd=message.total_cost_usd,
            num_turns=message.num_turns,
        )
    ]
    if message.is_error and message.terminal_reason not in INTERRUPTED:
        reason = message.result or "; ".join(message.errors or []) or message.subtype
        facts.append(_block(Here(), "needs_you", {"reason": f"the turn failed: {reason}"}))
    facts.append(
        TurnEnded(
            ok=not message.is_error,
            terminal_reason=message.terminal_reason,
            deferred_tool_use=message.deferred_tool_use is not None,
            result=message.result,
        )
    )
    return facts


class _Unreadable(Exception):
    pass


def _choice(value: object, allowed: frozenset[str], name: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise _Unreadable(f"{name} is {value!r}")
    return value


def _moment(value: object, name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise _Unreadable(f"{name} is {value!r}")
    try:
        return datetime.fromtimestamp(value, UTC)
    except OverflowError, OSError, ValueError:
        raise _Unreadable(f"{name} is {value!r}") from None


def _fraction(value: object, name: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool) or not math.isfinite(value):
        raise _Unreadable(f"{name} is {value!r}")
    return float(value)


def _flag(raw: Mapping[str, object], key: str) -> bool | None:
    value = raw.get(key)
    if value is None or isinstance(value, bool):
        return value
    raise _Unreadable(f"{key} is {value!r}")


def _readings(value: object) -> tuple[Reading, ...]:
    if value is None:
        return ()
    if not isinstance(value, dict):
        raise _Unreadable(f"unifiedWindows is {value!r}")
    readings: list[Reading] = []
    for window, entry in cast("dict[object, object]", value).items():
        if not isinstance(window, str) or not isinstance(entry, dict):
            raise _Unreadable(f"unifiedWindows has {window!r}: {entry!r}")
        fields = cast("dict[str, object]", entry)
        used = _fraction(fields.get("utilization"), f"unifiedWindows.{window}.utilization")
        if used is not None:
            resets = _moment(fields.get("resetsAt"), f"unifiedWindows.{window}.resetsAt")
            readings.append(Reading(window, used, resets))
    return tuple(readings)


def _limits(info: RateLimitInfo) -> Limits | UnreadableLimits:
    """Any field outside the pinned CLI's schema makes the whole event unreadable, so a shape
    this code does not know never reads as "no overage"."""
    try:
        return _read_limits(info)
    except _Unreadable as error:
        return UnreadableLimits(f"a rate-limit event could not be read: {error}")


def _read_limits(info: RateLimitInfo) -> Limits:
    raw = cast("Mapping[str, object]", info.raw)
    flags = [
        flag for key in ("isUsingOverage", "overageInUse") if (flag := _flag(raw, key)) is not None
    ]
    code = raw.get("errorCode")
    if code is not None and code != "credits_required":
        raise _Unreadable(f"errorCode is {code!r}")
    window = info.rate_limit_type
    overage = info.overage_status
    reason: object = info.overage_disabled_reason
    if reason is not None and not isinstance(reason, str):
        raise _Unreadable(f"overageDisabledReason is {reason!r}")
    return Limits(
        window=None
        if window is None
        else cast("Window", _choice(window, WINDOWS, "rateLimitType")),
        status=cast("LimitStatus", _choice(info.status, STATUSES, "status")),
        utilization=_fraction(info.utilization, "utilization"),
        resets_at=_moment(info.resets_at, "resetsAt"),
        overage_status=None
        if overage is None
        else cast("LimitStatus", _choice(overage, STATUSES, "overageStatus")),
        overage_resets_at=_moment(info.overage_resets_at, "overageResetsAt"),
        overage_disabled_reason=reason,
        using_overage=any(flags) if flags else None,
        overage_enabled=_flag(raw, "overageEnabled"),
        credits_required=code == "credits_required" or "credits_required" in raw,
        readings=_readings(raw.get("unifiedWindows")),
    )


def _system(message: SystemMessage) -> list[Fact]:
    match message:
        case TaskStartedMessage():
            return [
                _block(
                    Here(),
                    "agents",
                    {
                        "task_id": message.task_id,
                        "tool_use_id": message.tool_use_id,
                        "description": message.description,
                        "state": "working",
                    },
                )
            ]
        case TaskProgressMessage():
            return [
                Delta(
                    _target(message.tool_use_id),
                    "tool_progress",
                    f"{message.description}: {message.last_tool_name or 'working'}",
                )
            ]
        case TaskNotificationMessage(tool_use_id=tool_use_id):
            card = _block(
                Here(),
                "agents",
                {
                    "task_id": message.task_id,
                    "tool_use_id": tool_use_id,
                    "state": message.status,
                    "summary": message.summary,
                },
            )
            return [card, StreamEnded(InChild(tool_use_id))] if tool_use_id else [card]
        case TaskUpdatedMessage(status=status) if status:
            return [_block(Here(), "agents", {"task_id": message.task_id, "state": status})]
        case _ if message.subtype == "compact_boundary":
            metadata = cast("dict[str, Any]", message.data.get("compact_metadata", {}))
            return [Compacted("manual" if metadata.get("trigger") == "manual" else "auto")]
        case _:
            return []
