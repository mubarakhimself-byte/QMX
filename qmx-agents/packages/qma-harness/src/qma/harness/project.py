"""SDK messages to UI facts. One pure function, tested on recorded transcripts.

The block kinds are the 14 `SessionBlock` kinds that `qmx_agents.copilot.stream_turn` writes
today, served by the existing SSE route. New meaning goes inside `content`, never a new block
type.

Every Block passes through `redact`, so a Claude token an agent printed or read never reaches
`sessions_append`. Deltas leave here raw: a streamed token can arrive split over several deltas,
and a per-delta `redact` would hide the prefix and let the rest through. `chat.py` feeds them to
a `TokenGate`, the only redactor on the live channel, which holds back text that could still
grow into a token.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any, Final, Literal, cast

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

PLAN_TOOLS: Final = frozenset({"TodoWrite", "TaskCreate", "TaskUpdate"})
AGENT_TOOLS: Final = frozenset({"Agent", "Task"})


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


class TokenGate:
    """Streamed text in, redacted text out. Holds back a tail that is, or could still become,
    a token, until the next piece settles it or `flush` ends the stream."""

    def __init__(self) -> None:
        self._held = ""

    def feed(self, text: str) -> str:
        pending = self._held + text
        cut = _settled_length(pending)
        self._held = pending[cut:]
        return redact(pending[:cut])

    def flush(self) -> str:
        held, self._held = self._held, ""
        return redact(held)


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
    kind: Literal["text", "thinking", "tool_progress"]
    text: str


@dataclass(frozen=True)
class TurnUsage:
    """From `ResultMessage`. Plan chats count usage here and relayed chats at the relay, so
    each profile has one usage source. Costs are list-price estimates."""

    session_id: str
    model_usage: dict[str, dict[str, int | float]]
    total_cost_usd: float | None
    num_turns: int


type LimitStatus = Literal["allowed", "allowed_warning", "rejected"]
type Window = Literal["five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet", "overage"]


@dataclass(frozen=True)
class Limits:
    """From `RateLimitEvent`. Every field the SDK's `RateLimitInfo` models, plus three the CLI
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


@dataclass(frozen=True)
class TurnEnded:
    """The `ResultMessage` of the operator's own prompt. Results of injected turns, such as a
    background task's notification, carry a non-human origin and end no turn."""

    ok: bool
    terminal_reason: str | None
    deferred_tool_use: bool


@dataclass(frozen=True)
class Compacted:
    """`compact_boundary`. Shown as an event in the session."""

    trigger: Literal["manual", "auto"]


type Fact = Block | Delta | TurnUsage | Limits | TurnEnded | Compacted


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


def _assistant(message: AssistantMessage) -> list[Fact]:
    target = _target(message.parent_tool_use_id)
    facts: list[Fact] = []
    for part in message.content:
        match part:
            case TextBlock(text=text) if text:
                facts.append(_block(target, "text", {"text": text}))
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
    if event.get("type") != "content_block_delta":
        return []
    delta = cast("dict[str, Any]", event.get("delta", {}))
    target = _target(message.parent_tool_use_id)
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
    if message.is_error:
        reason = message.result or "; ".join(message.errors or []) or message.subtype
        facts.append(_block(Here(), "needs_you", {"reason": f"the turn failed: {reason}"}))
    origin = message.origin or {}
    if origin.get("kind", "human") == "human":
        facts.append(
            TurnEnded(
                ok=not message.is_error,
                terminal_reason=message.terminal_reason,
                deferred_tool_use=message.deferred_tool_use is not None,
            )
        )
    return facts


def _moment(stamp: int | None) -> datetime | None:
    return None if stamp is None else datetime.fromtimestamp(stamp, UTC)


def _limits(info: RateLimitInfo) -> Limits:
    raw = info.raw
    flags = [raw[key] for key in ("isUsingOverage", "overageInUse") if key in raw]
    enabled = raw.get("overageEnabled")
    return Limits(
        window=info.rate_limit_type,
        status=info.status,
        utilization=info.utilization,
        resets_at=_moment(info.resets_at),
        overage_status=info.overage_status,
        overage_resets_at=_moment(info.overage_resets_at),
        overage_disabled_reason=info.overage_disabled_reason,
        using_overage=any(flag is True for flag in flags) if flags else None,
        overage_enabled=enabled if isinstance(enabled, bool) else None,
        credits_required="credits_required" in raw,
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
        case TaskNotificationMessage():
            return [
                _block(
                    Here(),
                    "agents",
                    {
                        "task_id": message.task_id,
                        "tool_use_id": message.tool_use_id,
                        "state": message.status,
                        "summary": message.summary,
                    },
                )
            ]
        case TaskUpdatedMessage(status=status) if status:
            return [_block(Here(), "agents", {"task_id": message.task_id, "state": status})]
        case _ if message.subtype == "compact_boundary":
            metadata = cast("dict[str, Any]", message.data.get("compact_metadata", {}))
            return [Compacted("manual" if metadata.get("trigger") == "manual" else "auto")]
        case _:
            return []
