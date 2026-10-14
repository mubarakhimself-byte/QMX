"""Domain types for the QMA v2 harness. Every public signature in qma2 speaks these.

Read this file first. The rest of the package is signatures over these shapes.

Invariants encoded here rather than in prose:
- Ids are distinct NewTypes. A ThreadId is never accepted where a TurnId is expected.
- `ThreadId` is the qmx-control session id. One id, two tables, no mapping layer.
- `ToolEffect` is closed. `MONEY_ACT` has no Allow branch anywhere (policy.evaluate is
  exhaustive over it and returns a final Deny). `MONEY_PROPOSE` is reachable only through a
  registered `ToolSpec` (tools/registry.py), never by name.
- `OperatorProof` has no public constructor. Only `OperatorAuth.verify` builds one, so a
  function that takes an `OperatorProof` cannot be called from an agent-token path.
- `EngineEvent` is a closed union; the projector in session.py matches it exhaustively.
- SDK message classes never appear here. They stop at qma2.engines.*.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, NewType

# ---------------------------------------------------------------- identities

ThreadId = NewType("ThreadId", str)  # == qmx-control `sessions.id`
SegmentId = NewType("SegmentId", str)
TurnId = NewType("TurnId", str)
CallId = NewType("CallId", str)
ApprovalId = NewType("ApprovalId", str)
AccountId = NewType("AccountId", str)

type Json = dict[str, Any]
type AgentPath = str  # "root", "root/reviewer#1", "root/reviewer#1/explore#1"


class EngineKind(StrEnum):
    CLAUDE = "claude"  # Claude Agent SDK; structure is native
    OPENAI = "openai"  # OpenAI Agents SDK; structure is QMX's rebuild


class Provider(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    META = "meta"
    GLM = "glm"
    KIMI = "kimi"
    DEEPSEEK = "deepseek"
    MINIMAX = "minimax"
    CUSTOM = "custom"


class AccountKind(StrEnum):
    CLAUDE_SUBSCRIPTION = "claude_subscription"  # exactly one; QMX holds no token
    CHATGPT_OAUTH = "chatgpt_oauth"  # Sign in with ChatGPT; token in SecretStore
    API_KEY = "api_key"  # base_url + key in SecretStore


class Principal(StrEnum):
    OPERATOR = "operator"
    AGENT = "agent"


@dataclass(frozen=True)
class OperatorProof:
    """Evidence that the caller presented a live operator session.

    Not constructible outside `qma2.approvals.OperatorAuth.verify`. Functions that mutate
    operator-only state take one of these as a parameter; the type is the authorisation.
    """

    _session_hash: str
    issued_at: datetime


# ---------------------------------------------------------------- model, effort, mode


@dataclass(frozen=True)
class ModelRef:
    provider: Provider
    model: str  # provider's id, e.g. "claude-opus-5-5", "openai/gpt-5.6", "deepseek-chat"


class Effort(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"
    MAX = "max"


class PermissionMode(StrEnum):
    """Claude Code's modes minus `auto` (classifier is out of scope)."""

    DEFAULT = "default"
    ACCEPT_EDITS = "acceptEdits"
    PLAN = "plan"
    DONT_ASK = "dontAsk"
    BYPASS = "bypassPermissions"


# ---------------------------------------------------------------- tools and policy


class ToolEffect(StrEnum):
    READ = "read"
    WRITE = "write"  # local state or files
    EXTERNAL = "external"  # network, providers, processes
    MONEY_READ = "money_read"  # balances, positions, proposals list
    MONEY_PROPOSE = "money_propose"  # writes an unsigned proposal; only via ToolSpec
    MONEY_ACT = "money_act"  # order/position/sizing/binding/promotion: never allowed


class ToolSource(StrEnum):
    BUILTIN = "builtin"  # Claude engine's own Bash/Read/Edit/...; QMX tool kit on OpenAI
    QMX = "qmx"  # registered ToolSpec (both engines)
    MCP = "mcp"  # external MCP server, classified by name rules


@dataclass(frozen=True)
class ToolCall:
    """One attempted tool invocation, engine-neutral. Built by the engine adapter."""

    tool: str  # Claude's canonical name on both engines ("Bash", "Read", "mcp__x__y")
    input: Mapping[str, Any]
    call_id: CallId
    thread_id: ThreadId
    turn_id: TurnId
    agent_path: AgentPath
    source: ToolSource
    effect: ToolEffect  # classified by ToolRegistry.classify before the gate runs
    cwd: Path


@dataclass(frozen=True)
class Allow:
    updated_input: Mapping[str, Any] | None = None
    reason: str = ""


@dataclass(frozen=True)
class Deny:
    reason: str
    final: bool = False  # True = managed tier; no approval can override it


@dataclass(frozen=True)
class Ask:
    request: ApprovalRequest


type Verdict = Allow | Deny  # what an engine receives
type RuleVerdict = Allow | Deny | Ask  # what pure policy returns


@dataclass(frozen=True)
class ApprovalRequest:
    kind: Literal["tool", "question", "confirm"]
    prompt: str
    call: ToolCall | None = None  # kind == "tool"
    options: tuple[str, ...] = ()  # kind == "question"
    schema: Json | None = None  # structured answers (AskUserQuestion)


class Answer(StrEnum):
    ALLOW_ONCE = "allow_once"
    ALLOW_SESSION = "allow_session"  # remembered in the actor until the thread ends
    ALLOW_ALWAYS = "allow_always"  # writes a rule to the project-local settings layer
    DENY_ONCE = "deny_once"
    DENY_ALWAYS = "deny_always"
    CANCEL_TURN = "cancel_turn"


@dataclass(frozen=True)
class ApprovalAnswer:
    answer: Answer
    message: str = ""
    edited_input: Mapping[str, Any] | None = None  # full replacement of the tool input
    text: str | None = None  # kind == "question"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    ANSWERED = "answered"
    EXPIRED = "expired"  # engine died before the answer arrived


@dataclass(frozen=True)
class Approval:
    id: ApprovalId
    thread_id: ThreadId
    turn_id: TurnId
    agent_path: AgentPath
    request: ApprovalRequest
    status: ApprovalStatus
    created_at: datetime
    answer: ApprovalAnswer | None = None
    answered_at: datetime | None = None


# ---------------------------------------------------------------- threads, segments, turns


class ThreadStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"  # an approval or question is pending
    FAILED = "failed"


@dataclass(frozen=True)
class Thread:
    """The operator-visible conversation. Lives for days. `id` is the control session id."""

    id: ThreadId
    title: str
    cwd: Path
    status: ThreadStatus
    current_segment: SegmentId
    created_at: datetime
    parent_id: ThreadId | None = None  # sub-agent child threads
    background: bool = False  # may only use spare Claude window (Account.background_cap_pct)
    archived: bool = False


class SegmentEnd(StrEnum):
    SWITCHED = "switched"  # model/effort/engine switch started a new segment
    COMPACTED = "compacted"  # cross-engine or forced re-seed
    FAILED = "failed"


@dataclass(frozen=True)
class Segment:
    """One engine session inside a thread. A new segment starts when the engine or account
    changes; a model or effort change on the same engine stays in the segment.

    `engine_session_id` is the engine's own resume token (Claude session uuid, QMX SQLite
    session id on OpenAI). None until the engine reports it (`SessionBound`).
    """

    id: SegmentId
    thread_id: ThreadId
    engine: EngineKind
    account_id: AccountId
    model: ModelRef
    effort: Effort
    mode: PermissionMode
    started_at: datetime
    engine_session_id: str | None = None
    seed_from_block_seq: int | None = None  # history rendered from blocks up to here
    ended_at: datetime | None = None
    end_reason: SegmentEnd | None = None


@dataclass(frozen=True)
class TurnInput:
    text: str
    attachments: tuple[Path, ...] = ()


class TurnStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    INTERRUPTED = "interrupted"
    FAILED = "failed"


type StopReason = Literal["done", "interrupted", "max_turns", "error", "needs_input"]


@dataclass(frozen=True)
class Turn:
    id: TurnId
    thread_id: ThreadId
    segment_id: SegmentId
    seq: int
    input: TurnInput
    status: TurnStatus
    client_key: str  # idempotency: (thread_id, client_key) is unique
    started_at: datetime | None = None
    ended_at: datetime | None = None
    stop_reason: StopReason | None = None


# ---------------------------------------------------------------- accounts, usage, limits


@dataclass(frozen=True)
class Account:
    id: AccountId
    provider: Provider
    kind: AccountKind
    label: str
    engine: EngineKind
    models: tuple[str, ...]
    enabled: bool = True
    credential_ref: str | None = None  # SecretStore key; None for CLAUDE_SUBSCRIPTION
    claude_home: Path | None = None  # CLAUDE_CONFIG_DIR; CLAUDE_SUBSCRIPTION only
    base_url: str | None = None  # API_KEY only
    background_cap_pct: int = 50  # background threads refused above this utilisation


type LimitWindow = Literal[
    "five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet",
    "primary", "secondary",  # ChatGPT route (x-codex-* headers)
    "daily", "weekly", "monthly", "credits",  # OpenRouter /key
]


@dataclass(frozen=True)
class LimitSnapshot:
    account_id: AccountId
    window: LimitWindow
    used_pct: float
    taken_at: datetime
    source: str  # "claude_rate_limit_event" | "codex_headers" | "openrouter_key" | ...
    resets_at: datetime | None = None
    status: Literal["allowed", "allowed_warning", "rejected"] = "allowed"


@dataclass(frozen=True)
class UsageRow:
    """One row per model call. Token kinds are disjoint (research 05 normalisation)."""

    dedupe_key: str  # engine-specific stable key; insert-or-ignore
    at: datetime
    account_id: AccountId
    provider: Provider
    model: str
    thread_id: ThreadId
    turn_id: TurnId
    agent_path: AgentPath
    uncached_input: int
    cache_read: int
    cache_write: int
    output: int
    reasoning: int = 0
    reported_cost_usd: float | None = None
    is_compaction: bool = False


@dataclass(frozen=True)
class UsageSummary:
    since: datetime
    until: datetime
    by_account: tuple[AccountUsage, ...]
    limits: tuple[LimitSnapshot, ...]  # latest per (account, window)


@dataclass(frozen=True)
class AccountUsage:
    account_id: AccountId
    label: str
    uncached_input: int
    cache_read: int
    cache_write: int
    output: int
    reasoning: int
    cost_usd_estimate: float | None
    turns: int


# ---------------------------------------------------------------- engine events (closed)


@dataclass(frozen=True)
class SessionBound:
    engine_session_id: str


@dataclass(frozen=True)
class TextDelta:
    item_id: str
    text: str


@dataclass(frozen=True)
class TextDone:
    item_id: str
    text: str
    role: Literal["assistant", "reasoning", "compaction", "error"] = "assistant"
    agent_path: AgentPath = "root"


@dataclass(frozen=True)
class ToolStarted:
    call: ToolCall


@dataclass(frozen=True)
class ToolFinished:
    call_id: CallId
    agent_path: AgentPath
    status: Literal["completed", "failed", "denied"]
    result_preview: str  # <= 500 chars, redacted
    files_changed: tuple[Path, ...] = ()


@dataclass(frozen=True)
class PlanUpdated:
    steps: tuple[tuple[str, Literal["pending", "in_progress", "done"]], ...]
    agent_path: AgentPath = "root"


@dataclass(frozen=True)
class SubagentStarted:
    agent_path: AgentPath
    name: str
    model: ModelRef | None
    background: bool


@dataclass(frozen=True)
class SubagentFinished:
    agent_path: AgentPath
    outcome: Literal["complete", "failed", "needs_you"]
    summary: str


@dataclass(frozen=True)
class Compacted:
    trigger: Literal["auto", "manual"]
    summary_preview: str
    agent_path: AgentPath = "root"


@dataclass(frozen=True)
class UsageRecorded:
    row: UsageRow


@dataclass(frozen=True)
class LimitUpdated:
    snapshot: LimitSnapshot


@dataclass(frozen=True)
class TurnFinished:
    stop_reason: StopReason
    error: str | None = None


type EngineEvent = (
    SessionBound
    | TextDelta
    | TextDone
    | ToolStarted
    | ToolFinished
    | PlanUpdated
    | SubagentStarted
    | SubagentFinished
    | Compacted
    | UsageRecorded
    | LimitUpdated
    | TurnFinished
)


# ---------------------------------------------------------------- switch preview


@dataclass(frozen=True)
class SwitchPreview:
    """Returned when a switch would break the prompt cache and `confirm` was False."""

    from_model: ModelRef
    to_model: ModelRef
    from_effort: Effort
    to_effort: Effort
    cache_breaks: bool
    new_segment: bool  # engine or account changes
    message: str  # plain words for the pop-up


@dataclass(frozen=True)
class ExportBundle:
    path: Path  # zip: blocks.jsonl, engine transcript, usage.jsonl, traces/, hooks.log
    thread_id: ThreadId
    bytes: int


@dataclass(frozen=True)
class ProbeResult:
    """Outcome of `Engine.probe(account)`; the first unit's live check reads this."""

    ok: bool
    detail: str
    checks: Mapping[str, bool] = field(default_factory=dict)
