"""Core domain types for the QMX harness.

Pure data. No I/O, no SDK imports, no qmx_* imports. Every other qma2 module and
qmx_control speak these types; wire and storage formats are parsed into them at the
edge (host/link.py, store.py) and never leak out.

Invariants encoded here (rather than checked at runtime):
- An engine is never chosen on its own. It is derived from the account kind
  (`Route`), so "Claude engine on an OpenRouter key" cannot be expressed.
- `ClaudeSubscription` has no credential field. QMX cannot store a Claude token
  because there is nowhere to put one (H1 fact 4).
- `Mode` has no `auto` member, so the SDK default of `auto` can never be passed.
- A policy `Decision` (pure) and a wire `Verdict` (after an approval is opened) are
  different types, so a host can never see `NeedsOperator` and invent its own prompt.
- `Answer` needs an `OperatorProof`; only qmx_control's operator auth can mint one
  (see `qma2.operator`, import-linted).
- A model or engine switch needs a `SwitchQuote`, so the cost warning cannot be skipped.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal, NewType

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]

# --------------------------------------------------------------------------- ids

ThreadId = NewType("ThreadId", str)
"""Equal to the qmx-control session id. One thread = one UI session, for days."""
SegmentId = NewType("SegmentId", str)
TurnId = NewType("TurnId", str)
ApprovalId = NewType("ApprovalId", str)
AccountId = NewType("AccountId", str)
ItemId = NewType("ItemId", str)


@dataclass(frozen=True, slots=True)
class AgentPath:
    """Who inside a thread made a call: "root", "root/reviewer#2", ...

    Depth is derived, never stored, so the depth cap (policy) and the UI tree read
    one value.
    """

    parts: tuple[str, ...] = ("root",)

    def child(self, name: str, ordinal: int) -> AgentPath:
        raise NotImplementedError

    @property
    def depth(self) -> int:
        """root = 0. Claude and QMX both refuse depth > 3 (configurable)."""
        raise NotImplementedError

    def __str__(self) -> str:
        return "/".join(self.parts)


# ------------------------------------------------------------------- vocabulary


class Engine(StrEnum):
    CLAUDE = "claude"
    OPENAI = "openai"


class Wire(StrEnum):
    RESPONSES = "responses"
    CHAT_COMPLETIONS = "chat_completions"


class Mode(StrEnum):
    """Claude Code permission modes. `auto` is deliberately absent (classifier is later)."""

    DEFAULT = "default"
    ACCEPT_EDITS = "acceptEdits"
    PLAN = "plan"
    DONT_ASK = "dontAsk"
    BYPASS = "bypassPermissions"


class Effort(StrEnum):
    """Claude's five levels are the UI vocabulary; adapters map them per provider."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"
    MAX = "max"


class Origin(StrEnum):
    """Who started the thread. Anything other than OPERATOR is background work and
    obeys the router's spare-window cap."""

    OPERATOR = "operator"
    AGENT = "agent"
    TRIGGER = "trigger"


# --------------------------------------------------------------------- accounts


@dataclass(frozen=True, slots=True)
class HostSecretRef:
    """A keyring label whose value may be injected into ONE engine host's env.

    Provider API keys and the ChatGPT access token are HostSecretRefs.
    """

    label: str  # "qmx/<provider>/<name>"


@dataclass(frozen=True, slots=True)
class OperatorSecretRef:
    """A keyring label that never leaves the qmx-control process.

    Broker credentials, the control token, the operator session key. `secrets.host_env`
    only accepts HostSecretRef, so these cannot reach an agent's environment by any
    code path that type-checks.
    """

    label: str


@dataclass(frozen=True, slots=True)
class ClaudeSubscription:
    """The one Claude Max account. Its 'credential' is the operator's own /login inside
    `config_dir` (QMX's CLAUDE_CONFIG_DIR). There is intentionally no secret field.
    A partial unique index in harness.db allows at most one row of this kind."""

    id: AccountId
    label: str
    config_dir: Path


@dataclass(frozen=True, slots=True)
class ChatGPTAccount:
    """Sign in with ChatGPT (PKCE). Calls go to api.openai.com/v1/responses only,
    store=false, stream=true (H1 fact 17). QMX stores and refreshes the token."""

    id: AccountId
    label: str
    access_ref: HostSecretRef
    refresh_ref: OperatorSecretRef


@dataclass(frozen=True, slots=True)
class ApiKeyAccount:
    """Any OpenAI-compatible provider by base URL + key: OpenRouter, Meta Muse, GLM,
    Kimi, DeepSeek, MiniMax. Never Anthropic or OpenAI API keys for Claude/GPT
    (operator: no API for Claude or GPT) -- enforced by `accounts.put_api_key`."""

    id: AccountId
    provider: str
    label: str
    base_url: str
    wire: Wire
    key_ref: HostSecretRef
    models: tuple[str, ...]


type Account = ClaudeSubscription | ChatGPTAccount | ApiKeyAccount


# ----------------------------------------------------------------------- routes


@dataclass(frozen=True, slots=True)
class ClaudeRoute:
    account: ClaudeSubscription
    model: str
    effort: Effort


@dataclass(frozen=True, slots=True)
class OpenAIRoute:
    account: ChatGPTAccount | ApiKeyAccount
    model: str
    effort: Effort

    @property
    def wire(self) -> Wire:
        """ChatGPT is always Responses; API-key accounts carry their wire."""
        raise NotImplementedError


type Route = ClaudeRoute | OpenAIRoute


def engine_of(route: Route) -> Engine:
    """The only place an engine is decided. Derived, never stored separately."""
    raise NotImplementedError


# ------------------------------------------------------------- threads, segments


class Lineage(StrEnum):
    """Why a segment (one engine session inside a thread) began."""

    START = "start"
    FORK = "fork"  # new thread forked from another thread's segment
    SWITCH = "switch"  # operator switched model/engine with a quote
    REROUTE = "reroute"  # router moved a background thread at a turn boundary


@dataclass(frozen=True, slots=True)
class ThreadSpec:
    """What a caller supplies to start a thread. Everything else is derived."""

    title: str
    cwd: Path
    profile: str = "default"
    origin: Origin = Origin.OPERATOR
    model: str | None = None  # None = profile default, routed
    parent: ThreadId | None = None  # a thread spawned by an agent (not a sub-agent)


@dataclass(frozen=True, slots=True)
class Segment:
    """A period of a thread with one fixed route. A thread is an ordered list of
    segments; only the last is live.

    A same-engine switch (model or effort) starts a new segment that continues the same
    SDK session (`sdk_session_id` carried over). An engine change starts a new SDK
    session seeded from `items`. So usage and cache history attribute cleanly per route.
    Claude resumes by `sdk_session_id`; OpenAI resumes from `items`."""

    id: SegmentId
    thread: ThreadId
    ordinal: int
    route: Route
    sdk_session_id: str | None
    lineage: Lineage
    started_at: datetime
    ended_at: datetime | None


@dataclass(frozen=True, slots=True)
class Idle:
    host_alive: bool


@dataclass(frozen=True, slots=True)
class Running:
    turn: TurnId
    waiting_on: tuple[ApprovalId, ...] = ()


@dataclass(frozen=True, slots=True)
class LockedOut:
    """The account's window is exhausted. The thread persists and resumes at `until`
    (or the operator switches it with a quote)."""

    until: datetime
    account: AccountId


@dataclass(frozen=True, slots=True)
class Failed:
    reason: str  # "host_exited", "auth_required", ...


@dataclass(frozen=True, slots=True)
class Archived:
    pass


type ThreadStatus = Idle | Running | LockedOut | Failed | Archived


@dataclass(frozen=True, slots=True)
class ThreadView:
    """Read model returned to callers. Built from harness.db + actor state."""

    id: ThreadId
    cwd: Path
    profile: str
    origin: Origin
    mode: Mode
    status: ThreadStatus
    segment: Segment
    turns: int


@dataclass(frozen=True, slots=True)
class TurnInput:
    """`client_turn_id` makes `send` idempotent: the same id twice returns the first
    turn instead of starting a second one."""

    text: str
    client_turn_id: str
    attachments: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class TurnAccepted:
    thread: ThreadId
    turn: TurnId
    duplicate: bool


# ------------------------------------------------------------------ tool calls


class ToolSource(StrEnum):
    BUILTIN = "builtin"  # Claude built-in, or QMX's own rebuild of it on OpenAI
    QMX = "qmx"  # reserved `qmx` namespace: QMX control ops and the proposal tool
    MCP = "mcp"  # any configured MCP server (never named "qmx": config refuses it)


@dataclass(frozen=True, slots=True)
class ToolCall:
    """One tool call as the policy sees it, identical for both engines.

    `name` uses Claude's vocabulary on both engines (Bash, Read, Edit, Agent,
    mcp__server__tool) so rules and hook matchers are written once.
    """

    tool_use_id: str
    name: str
    input: Mapping[str, JsonValue]
    source: ToolSource
    agent_path: AgentPath
    engine: Engine

    def with_input(self, updated: Mapping[str, JsonValue]) -> ToolCall:
        raise NotImplementedError


class DenySource(StrEnum):
    MONEY = "money"  # the always-on money rule; nothing can override it
    HOOK = "hook"
    RULE = "rule"
    MODE = "mode"
    LIMIT = "limit"  # depth / concurrency caps
    OPERATOR = "operator"


class ApprovalKind(StrEnum):
    TOOL = "tool"
    QUESTION = "question"  # AskUserQuestion / AskUser
    PLAN = "plan"  # ExitPlanMode


@dataclass(frozen=True, slots=True)
class Allow:
    input: Mapping[str, JsonValue]
    context: tuple[str, ...] = ()  # hook additionalContext, delivered to the model


@dataclass(frozen=True, slots=True)
class Deny:
    reason: str
    source: DenySource
    stop_turn: bool = False


@dataclass(frozen=True, slots=True)
class NeedsOperator:
    """Pure result of `policy.decide`: the operator must answer. Never crosses the wire;
    the thread actor turns it into an Approval row and sends `Pending`."""

    kind: ApprovalKind
    reason: str
    suggested_rule: str | None  # e.g. "Bash(npm run lint *)", offered for ALLOW_ALWAYS


@dataclass(frozen=True, slots=True)
class Pending:
    approval: ApprovalId


type Decision = Allow | Deny | NeedsOperator
type Verdict = Allow | Deny | Pending


# ------------------------------------------------------------------- approvals


class Choice(StrEnum):
    ALLOW_ONCE = "allow_once"
    ALLOW_THREAD = "allow_thread"  # remembered for this thread (rules table, scope=thread)
    ALLOW_ALWAYS = "allow_always"  # writes a rule (scope=project or user)
    DENY = "deny"
    DENY_AND_STOP = "deny_and_stop"  # also interrupts the turn (Codex Abort)


@dataclass(frozen=True, slots=True)
class OperatorProof:
    """Evidence that the operator principal made this request.

    Minted only by `qma2.operator.mint` (import-linted: only qmx_control.server may
    import it). This is a type-level fence against builder shortcuts; the security
    boundary itself is the route principal check in qmx_control.
    """

    session_hash: str
    _sealed: object = field(repr=False)


@dataclass(frozen=True, slots=True)
class Answer:
    choice: Choice
    message: str | None = None  # shown to the model on deny
    edited_input: Mapping[str, JsonValue] | None = None  # full replacement; re-checked by money rule
    rule_text: str | None = None  # override for ALLOW_ALWAYS; defaults to suggested_rule
    answers: Mapping[str, JsonValue] | None = None  # for QUESTION approvals


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    RESOLVED = "resolved"
    EXPIRED = "expired"  # host died or turn ended before an answer


@dataclass(frozen=True, slots=True)
class ApprovalView:
    id: ApprovalId
    thread: ThreadId
    turn: TurnId
    agent_path: AgentPath
    kind: ApprovalKind
    call: ToolCall
    reason: str
    suggested_rule: str | None
    status: ApprovalStatus
    answer: Answer | None
    created_at: datetime


# ------------------------------------------------------------- model switching


class SwitchCostKind(StrEnum):
    NONE = "none"  # e.g. effort change on a 5.5-family model with cache kept
    CACHE_REBUILD = "cache_rebuild"  # same engine, new model (or effort split)
    ENGINE_CHANGE = "engine_change"  # new segment on the other engine, seeded


@dataclass(frozen=True, slots=True)
class SwitchTarget:
    model: str
    effort: Effort | None = None
    account: AccountId | None = None  # None = router picks among accounts serving `model`


@dataclass(frozen=True, slots=True)
class SwitchQuote:
    """Returned by `Harness.quote_switch`, required by `Harness.switch`.

    `cache_epoch` pins the quote to the cache state it priced. If a turn ran since,
    the epoch moved and `switch` refuses with `QuoteStale`, so the warning the operator
    saw is always the warning that applies.
    """

    thread: ThreadId
    to: Route
    cost: SwitchCostKind
    est_uncached_tokens: int
    cache_epoch: int
    expires_at: datetime


# -------------------------------------------------------------- usage, limits


class CostSource(StrEnum):
    REPORTED = "reported"  # Claude total_cost_usd / model_usage (API-equivalent estimate)
    PRICED = "priced"  # QMX price table
    UNPRICED = "unpriced"


@dataclass(frozen=True, slots=True)
class UsageRow:
    """One ledger row. `dedupe_key` makes recording idempotent
    (Claude: turn_id + model; OpenAI: response id)."""

    dedupe_key: str
    at: datetime
    thread: ThreadId
    turn: TurnId | None
    agent_path: AgentPath
    account: AccountId
    model: str
    uncached_input: int
    cache_read: int
    cache_write: int
    output: int
    reasoning: int
    cost_usd: float | None
    cost_source: CostSource


type Window = Literal["five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet", "primary", "secondary"]


@dataclass(frozen=True, slots=True)
class LimitSnapshot:
    """Latest known state of one plan window. Claude emits these only on change
    (H1 fact 10), so the latest row per (account, window) is the truth."""

    account: AccountId
    window: Window
    utilization: float | None  # 0..1
    status: Literal["allowed", "allowed_warning", "rejected"]
    resets_at: datetime | None
    observed_at: datetime
    source: Literal["claude_rate_limit_event", "claude_get_usage", "x_codex_headers"]


@dataclass(frozen=True, slots=True)
class UsageReport:
    windows: tuple[LimitSnapshot, ...]
    by_model: Mapping[str, UsageRow]  # summed rows keyed by model
    by_thread: Mapping[ThreadId, UsageRow]
    cache_hit_ratio: float
    money_guarantee: Literal["tool_level_same_user", "os_account"]
    """Shown on the usage/status page so the operator always sees which money
    guarantee is in force (see design.md, tension 1)."""


# ------------------------------------------------------------------ UI protocol

type BlockKind = Literal[
    "user", "text", "plan", "agents", "tool", "changed", "artifact", "table",
    "entity", "question", "permission", "panel", "handoff", "needs_you",
]
"""Single source for today's 14 block kinds. qmx_control.service.SessionBlock imports
this alias instead of keeping its own Literal (control -> qma2 is the allowed edge)."""


@dataclass(frozen=True, slots=True)
class Block:
    kind: BlockKind
    content: Mapping[str, JsonValue]  # always carries "v": 1


type EventKind = Literal[
    "turn.started", "turn.finished",
    "message.delta", "message.done",
    "reasoning.done", "plan.updated",
    "tool.started", "tool.progress", "tool.finished",
    "approval.requested", "approval.resolved",
    "subagent.started", "subagent.finished",
    "file.changed", "compacted",
    "usage.delta", "usage.recorded", "limits.updated",
    "thread.status", "error",
]


@dataclass(frozen=True, slots=True)
class Event:
    """Research 32 B3.1 envelope. `durable` events become blocks (via `to_block`) or
    topic events; live ones (deltas, progress) go only to `Harness.live`."""

    kind: EventKind
    thread: ThreadId
    turn: TurnId | None
    agent_path: AgentPath
    item: ItemId | None
    engine: Engine | None
    data: Mapping[str, JsonValue]
    durable: bool


def to_block(event: Event) -> Block | None:
    """Pure projection, ported from QA/copilot.py stream_turn rules:
    message.done -> text; tool.started/finished -> two `tool` blocks (append-only);
    plan.updated -> plan; approval.* -> permission (with approval_id);
    subagent.* -> agents; file.changed -> changed; compacted -> text{kind:"compaction"};
    error -> text{level:"error"}. Live kinds return None.
    """
    raise NotImplementedError
