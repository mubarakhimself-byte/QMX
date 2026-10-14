"""SDK messages to UI facts. One pure function, tested on recorded transcripts.

The spec is today's `qmx_agents.copilot.stream_turn` mapping (HOW "event wire"):
14 closed block kinds, written with `ControlService.sessions_append`, served by the
existing SSE route. New meaning goes inside `content`, never a new block type (UI-NOTES 2).

Every Block and Delta passes through `redact` first, so a Claude token an agent printed or
read never reaches `sessions_append`, the live channel or the UI (A1, B1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Final, Literal

if TYPE_CHECKING:
    from claude_agent_sdk import Message
    from qmx_control.service import SessionBlock


TOKEN_PATTERN: Final = r"sk-ant-[A-Za-z0-9_-]+"
"""Any Claude credential (`sk-ant-oat`, `sk-ant-ort`, `sk-ant-api`). Broader than the relay's
`TOKEN_SHAPES` on purpose: redaction only rewrites displayed text and never blocks a turn."""


def redact(text: str) -> str:
    """Pure. Replace every `TOKEN_PATTERN` match with `[redacted sk-ant token]`."""
    raise NotImplementedError


@dataclass(frozen=True)
class Here:
    """The block belongs to the chat's own session."""


@dataclass(frozen=True)
class InChild:
    """The block belongs to the child session of a native sub-agent, keyed by the Agent
    tool_use id (`parent_tool_use_id` on the message). `chat.py` owns the map from that id
    to a qmx-control child session and creates the child on first sight."""

    tool_use_id: str
    agent_type: str


type Target = Here | InChild


@dataclass(frozen=True)
class Block:
    target: Target
    block: SessionBlock


@dataclass(frozen=True)
class Delta:
    """Live-only (token text, tool progress). Never stored. Feeds `GET /api/sessions/{id}/live`."""

    target: Target
    kind: Literal["text", "thinking", "tool_progress"]
    text: str


@dataclass(frozen=True)
class TurnUsage:
    """From `ResultMessage`. For plan chats only, becomes one `model_call` journal event,
    which `RunIndex` already sums (HOW seam 5). Relayed chats are counted at the relay, so
    each profile has exactly one usage source. Costs are list-price estimates (02a section 9)."""

    session_id: str
    model_usage: dict[str, dict[str, int | float]]
    total_cost_usd: float | None
    num_turns: int


type LimitStatus = Literal["allowed", "allowed_warning", "rejected"]


@dataclass(frozen=True)
class Limits:
    """From `RateLimitEvent`. Account-level fact, merged by `usage.UsageLedger`.

    Every field the SDK's `RateLimitInfo` models is carried (SDK 0.2.163 `types.py` and
    `_internal/message_parser.py`, read 2026-10-14). The overage fields arrive on every event,
    whatever `window` is, so a `five_hour` event can say the plan is `rejected` while paid
    extra usage is `allowed`. That is the common paid case, and `UsageLedger.hard_stop` reads
    it."""

    window: Literal["five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet", "overage"]
    status: LimitStatus
    utilization: float | None
    resets_at: datetime | None
    overage_status: LimitStatus | None
    """`RateLimitInfo.overage_status`: the state of paid extra usage. None when absent."""
    overage_resets_at: datetime | None
    """`RateLimitInfo.overage_resets_at`."""
    overage_disabled_reason: str | None
    """`RateLimitInfo.overage_disabled_reason`, such as `out_of_credits` or
    `org_level_disabled`. Present when extra usage is unavailable."""
    using_overage: bool | None
    """`raw["isUsingOverage"]` or `raw["overageInUse"]`, True if either is True. The SDK does
    not model these; Claude Code 2.1.296's `rate_limit_info` schema carries both (read from the
    CLI's strings). None when both are absent."""
    overage_enabled: bool | None
    """`raw["overageEnabled"]`, same source. Feeds the "extra usage is on" doctor line."""
    credits_required: bool
    """True when `raw` carries `credits_required` (included usage exhausted, 02a section 9)."""


@dataclass(frozen=True)
class TurnEnded:
    """Our own prompt's `ResultMessage` (origin tells it apart from injected task
    notifications). Moves the chat record from "running" to "idle"."""

    ok: bool
    terminal_reason: str | None
    deferred_tool_use: bool


@dataclass(frozen=True)
class Compacted:
    """`compact_boundary`. Shown as an event in the session (UI-NOTES 3)."""

    trigger: Literal["manual", "auto"]


type Fact = Block | Delta | TurnUsage | Limits | TurnEnded | Compacted


def project(message: Message, *, redact_tokens: bool = True) -> list[Fact]:
    """Pure and total over the SDK message union. `redact_tokens=False` exists for one live
    check only (`TestMode.redaction`).

    AssistantMessage text -> Block(text); ToolUseBlock -> Block(tool, state "started");
    tool result in UserMessage -> Block(tool, state "finished" or "error");
    TodoWrite / TaskCreate / TaskUpdate input -> Block(plan); Agent tool_use -> Block(agents,
    child card) plus InChild targets for messages carrying its parent_tool_use_id;
    StreamEvent -> Delta; ResultMessage -> TurnUsage and TurnEnded; RateLimitEvent -> Limits;
    SystemMessage init -> [] (the post-connect check reads `get_server_info()` instead);
    compact_boundary -> Compacted;
    Task* messages -> Block(agents, status update). Unknown SystemMessage subtypes -> [] and
    a debug log line. Permission asks do not come through here; `chat.py` writes them.
    """
    raise NotImplementedError
