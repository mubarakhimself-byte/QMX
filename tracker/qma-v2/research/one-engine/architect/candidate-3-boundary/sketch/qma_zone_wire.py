"""The link protocol between the operator side and the agent zone.

Pure data plus parse and encode. Both sides import this module and nothing
else from each other. The zone runtime installs only this module, the
claude-agent-sdk wheel and `qma_zone`. No QMX service code and no money code
is installed in the zone.

Trust rule: everything the zone sends is untrusted data. The operator side
parses it with `parse_event` and never takes an authorization decision from
it. Everything the operator side sends is a command the zone obeys.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, NewType

WIRE_VERSION = 1

ThreadId = NewType("ThreadId", str)
"""Minted by the operator side. The zone never invents one."""

SdkSessionId = NewType("SdkSessionId", str)
"""Minted by the CLI inside the zone. Stored operator-side for resume."""

AskId = NewType("AskId", str)
"""The CLI's tool_use_id for a built-in tool ask. Stable across link drops."""

CommandId = NewType("CommandId", str)
"""Dedupe key. The zone acknowledges each command id once and ignores repeats."""

Seq = NewType("Seq", int)
"""Per-thread event number, strictly increasing, assigned by the zone.
The operator side applies an event only if its seq is above the stored one."""

PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions", "dontAsk"]
"""`auto` is left out on purpose. Omitting the mode can start a session in
`auto`, so every ThreadSpec carries one of these explicitly."""

Effort = Literal["low", "medium", "high", "xhigh", "max"]

Quirk = Literal[
    "disable_experimental_betas",  # Meta Muse rejects unknown top-level fields
    "compact_window_200k",  # upstream caps context below the CLI's assumption
    "force_tool_search",  # ENABLE_TOOL_SEARCH=true on non-first-party hosts
]


# ---------------------------------------------------------------- model route


@dataclass(frozen=True)
class TierPins:
    """Model names the CLI uses for each alias tier. All four are always pinned
    on a door route, because a partial mapping makes some calls fail silently."""

    opus: str
    sonnet: str
    haiku: str
    fable: str


@dataclass(frozen=True)
class Direct:
    """Plan traffic. The CLI talks to Anthropic with its own login.

    The zone env carries no ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN or
    ANTHROPIC_API_KEY. No QMX process is on this network path."""


@dataclass(frozen=True)
class ViaDoor:
    """Key-provider or GPT traffic.

    The CLI points ANTHROPIC_BASE_URL at the door's model relay for
    `profile_id` and sends the zone credential as ANTHROPIC_AUTH_TOKEN. The
    upstream URL and the real provider key never enter the zone. The zone only
    knows the profile id and the tier names."""

    profile_id: str
    tiers: TierPins
    quirks: frozenset[Quirk]


ModelRoute = Direct | ViaDoor


# ---------------------------------------------------------------- thread spec


@dataclass(frozen=True)
class McpServer:
    """An operator-configured MCP server for the zone (for example Playwright).

    The name `qmx` is reserved for the door and refused by `parse_command`."""

    name: str
    command: tuple[str, ...]
    env_names: frozenset[str]  # names only; values come from the zone's own env


@dataclass(frozen=True)
class ThreadSpec:
    """Everything the zone needs to open or reopen one chat.

    The operator side builds it. `workspace` is a path the operator side has
    already shared with the zone account. `resume` is set when reopening."""

    thread: ThreadId
    route: ModelRoute
    workspace: str
    mode: PermissionMode
    model: str | None
    effort: Effort | None
    append: str
    resume: SdkSessionId | None
    background: bool
    extra_mcp: tuple[McpServer, ...]
    disabled_tools: frozenset[str]
    subagent_depth: int
    idle_reap_seconds: int


# ---------------------------------------------------------------- commands


@dataclass(frozen=True)
class Open:
    spec: ThreadSpec


@dataclass(frozen=True)
class Send:
    """One user turn. `typed_by_operator` False turns on verbatim prompts, so
    text built from tool output, news or files cannot trigger `@path` reads or
    slash commands."""

    thread: ThreadId
    text: str
    typed_by_operator: bool


@dataclass(frozen=True)
class Interrupt:
    thread: ThreadId


@dataclass(frozen=True)
class SetMode:
    thread: ThreadId
    mode: PermissionMode


@dataclass(frozen=True)
class SetModel:
    """Same-route model change. A route change is Close plus Open with resume."""

    thread: ThreadId
    model: str


@dataclass(frozen=True)
class AnswerAsk:
    """The operator's answer to a built-in tool ask.

    `remember` is never echoed to the CLI as a userSettings update. The
    operator side records the rule in its canonical settings and pushes the
    mirror, so the zone's settings.json has one writer."""

    thread: ThreadId
    ask: AskId
    allow: bool
    message: str


@dataclass(frozen=True)
class Close:
    thread: ThreadId


@dataclass(frozen=True)
class MirrorFile:
    relative_path: str  # under the zone's ~/.claude, checked against MIRRORED_PATHS
    content: bytes


@dataclass(frozen=True)
class PutUserTier:
    """Replace the mirrored part of the zone's ~/.claude with the operator's
    canonical copy. Idempotent by content hash. Zone-owned paths (projects/,
    sessions, credentials, todos) are outside MIRRORED_PATHS and never touched."""

    files: tuple[MirrorFile, ...]
    content_hash: str


@dataclass(frozen=True)
class StartLogin:
    """Run the CLI's own sign-in inside the zone. See qma_zone.runner.run_login."""


@dataclass(frozen=True)
class ProbeTarget:
    kind: Literal["read_path", "write_path", "keyring_entry", "connect"]
    value: str  # a path, a keyring service name, or host:port


@dataclass(frozen=True)
class Probe:
    targets: tuple[ProbeTarget, ...]


@dataclass(frozen=True)
class Transcript:
    """Stream one thread's JSONL (and its helpers' JSONL) for export or backup."""

    thread: ThreadId


@dataclass(frozen=True)
class Shutdown:
    """Exit non-zero. The OS service manager restarts the zone."""


CommandBody = (
    Open | Send | Interrupt | SetMode | SetModel | AnswerAsk | Close
    | PutUserTier | StartLogin | Probe | Transcript | Shutdown
)

MIRRORED_PATHS: tuple[str, ...] = (
    "settings.json",
    "CLAUDE.md",
    "skills/",
    "agents/",
    "commands/",
    "hooks/",
)
"""The one list of zone paths the operator side owns. Everything else under
the zone's ~/.claude belongs to the CLI."""


@dataclass(frozen=True)
class Command:
    id: CommandId
    body: CommandBody


# ---------------------------------------------------------------- events


@dataclass(frozen=True)
class TextBlock:
    text: str
    partial: bool


@dataclass(frozen=True)
class ToolBlock:
    tool_use_id: str
    name: str
    state: Literal["started", "finished", "failed"]
    input_summary: str
    output_summary: str | None
    agent_id: str | None  # set when a helper made the call


@dataclass(frozen=True)
class PlanBlock:
    todos: tuple[tuple[str, Literal["pending", "in_progress", "completed"]], ...]


@dataclass(frozen=True)
class AgentsBlock:
    agent_id: str
    agent_type: str
    state: Literal["started", "finished"]


Block = TextBlock | ToolBlock | PlanBlock | AgentsBlock
"""Only the kinds the zone can produce. `permission` blocks are written by the
operator side, from Ask events and from door approvals."""


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_estimate_usd: float  # client-side list-price estimate, never billing
    by_model: tuple[tuple[str, int, int], ...]


@dataclass(frozen=True)
class Completed:
    pass


@dataclass(frozen=True)
class Errored:
    subtype: str
    api_status: int | None


@dataclass(frozen=True)
class Interrupted:
    pass


Outcome = Completed | Errored | Interrupted


@dataclass(frozen=True)
class ThreadReport:
    thread: ThreadId
    sdk_session: SdkSessionId | None
    live: bool
    last_seq: Seq


@dataclass(frozen=True)
class Ask:
    thread: ThreadId
    ask: AskId
    tool: str
    input_summary: str
    agent_id: str | None


@dataclass(frozen=True)
class Hello:
    """First event after every (re)connect. The operator side reconciles its
    thread index against it before sending anything else."""

    wire_version: int
    zone_version: str
    cli_version: str
    threads: tuple[ThreadReport, ...]
    pending_asks: tuple[Ask, ...]
    user_tier_hash: str | None


@dataclass(frozen=True)
class Opened:
    thread: ThreadId
    sdk_session: SdkSessionId
    tools: tuple[str, ...]  # from the init message, for the vanilla-parity check


@dataclass(frozen=True)
class BlockEvent:
    thread: ThreadId
    seq: Seq
    block: Block


@dataclass(frozen=True)
class TurnEnded:
    thread: ThreadId
    seq: Seq
    outcome: Outcome
    usage: Usage


@dataclass(frozen=True)
class RateLimit:
    """Copied from the SDK's RateLimitEvent. Fires on status changes only."""

    window: Literal["five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet", "overage"]
    status: Literal["allowed", "allowed_warning", "rejected"]
    utilization: float
    resets_at: datetime | None


@dataclass(frozen=True)
class LoginUrl:
    """The authorize URL the CLI printed. A URL with a PKCE challenge, not a
    credential. The operator's browser opens it."""

    url: str


@dataclass(frozen=True)
class LoginDone:
    """From `claude auth status`. Never carries a token."""

    signed_in: bool
    method: str  # for example "claude.ai"
    plan: str | None


@dataclass(frozen=True)
class ProbeFinding:
    target: ProbeTarget
    reachable: bool
    detail: str


@dataclass(frozen=True)
class ProbeResult:
    findings: tuple[ProbeFinding, ...]


@dataclass(frozen=True)
class TranscriptChunk:
    thread: ThreadId
    path: str  # relative name inside the export bundle
    data: bytes
    last: bool


@dataclass(frozen=True)
class Closed:
    thread: ThreadId
    reason: Literal["requested", "idle_reaped", "crashed"]


EventBody = (
    Hello | Opened | BlockEvent | Ask | TurnEnded | RateLimit
    | LoginUrl | LoginDone | ProbeResult | TranscriptChunk | Closed
)


@dataclass(frozen=True)
class Event:
    acks: tuple[CommandId, ...]
    body: EventBody


# ---------------------------------------------------------------- codec


def parse_command(raw: bytes) -> Command:
    """Zone-side boundary. Refuses an unknown wire version, an McpServer named
    `qmx`, and a MirrorFile path outside MIRRORED_PATHS."""
    raise NotImplementedError


def parse_event(raw: bytes) -> Event:
    """Operator-side boundary. Caps text sizes and refuses unknown kinds.
    A parse failure drops the link, it never guesses."""
    raise NotImplementedError


def encode(message: Command | Event) -> bytes:
    raise NotImplementedError
