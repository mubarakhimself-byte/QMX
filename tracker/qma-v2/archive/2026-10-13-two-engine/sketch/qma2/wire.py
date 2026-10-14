"""The link between qmx-control and one engine host: JSON lines over the host's stdio.

The host is a child process of qmx-control (`python -m qma2.host`). Its stdin/stdout are
the link; nothing else in the host may write to fd 1 (host/__main__ rebinds sys.stdout to
stderr before importing any SDK). The pipe is the host's only capability: it holds no
bearer token, no operator credential, and its tool subprocesses do not inherit the pipe.

Two directions, each a closed union, parsed with pydantic/msgspec at the edge in
host/link.py and harness.py; nothing outside those two files sees raw JSON.

    control -> host   Down:  Spawn (once) | Turn | Steer | Interrupt | Reconfigure
                             | Compact | Reply | Shutdown
    host -> control   Up:    Emit(Event-ish) | Ask(request) | Persist(items) | Bye

Every `Ask` carries a request id and gets exactly one `Reply`. `Ask` requests:
    Gate(call)            -> Verdict        (Allow | Deny | Pending)
    Await(approval)       -> Allow | Deny   (blocks until answered or expired)
    Hook(event)           -> HookOutcome    (UserPromptSubmit, PostToolUse, Stop, ...)
    LoadItems(segment)    -> items          (OpenAI resume)
    CallOp(name, args)    -> result         (QMX ops exposed to agents as qmx tools)
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from qma2.config import AgentDef, McpServerDef
from qma2.hooks import HookEvent, HookOutcome
from qma2.model import (
    AgentPath,
    ApprovalId,
    Effort,
    EventKind,
    ItemId,
    JsonValue,
    Mode,
    Route,
    SegmentId,
    ThreadId,
    ToolCall,
    TurnId,
    TurnInput,
    UsageRow,
    LimitSnapshot,
    Allow,
    Deny,
    Pending,
)

# ------------------------------------------------------------------ down (control -> host)


@dataclass(frozen=True, slots=True)
class Spawn:
    """Everything the host needs, sent once. The host never reads config files itself."""

    thread: ThreadId
    segment: SegmentId
    route: Route
    cwd: Path
    mode: Mode
    resume_sdk_session: str | None  # Claude resume id; None for OpenAI (items via LoadItems)
    fork: bool
    context_prefix: str  # ProjectContext.text, prepended to the segment's first user message
    agents: Mapping[str, AgentDef]
    claude_plugin_dir: Path | None
    mcp: Mapping[str, McpServerDef]
    qmx_tools: Sequence[Mapping[str, JsonValue]]  # name/description/schema of ToolSource.QMX tools
    trace_dir: Path


@dataclass(frozen=True, slots=True)
class Turn:
    turn: TurnId
    input: TurnInput
    extra_context: tuple[str, ...]  # UserPromptSubmit additionalContext, SessionStart context


@dataclass(frozen=True, slots=True)
class Steer:
    turn: TurnId
    text: str


@dataclass(frozen=True, slots=True)
class Interrupt:
    turn: TurnId


@dataclass(frozen=True, slots=True)
class Reconfigure:
    """Same-engine change applied from the next request: model, effort or mode.
    Engine changes never use this; they end the segment (new host, new segment)."""

    model: str | None
    effort: Effort | None
    mode: Mode | None


@dataclass(frozen=True, slots=True)
class Compact:
    focus: str | None


@dataclass(frozen=True, slots=True)
class Reply:
    request: int
    ok: bool
    value: JsonValue  # rendered Verdict / HookOutcome / items / op result


@dataclass(frozen=True, slots=True)
class Rotate:
    """A refreshed ChatGPT access token for a long-lived host. The only Down message that
    carries a secret; the host keeps it in memory and never puts it in a tool's env."""

    value: str


@dataclass(frozen=True, slots=True)
class Shutdown:
    reason: str


type Down = Spawn | Turn | Steer | Interrupt | Reconfigure | Compact | Reply | Rotate | Shutdown

# -------------------------------------------------------------------- up (host -> control)


@dataclass(frozen=True, slots=True)
class Emit:
    """An engine fact, already normalised by the adapter. The thread actor wraps it into
    a model.Event (adds thread, assigns item ids) and records/projects it."""

    kind: EventKind
    turn: TurnId | None
    agent_path: AgentPath
    source_key: str | None  # engine message/item id: idempotent item append
    data: Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True)
class Started:
    """Claude init (sdk session id, advertised tools) or OpenAI ready."""

    sdk_session_id: str | None
    tools: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TurnEnded:
    turn: TurnId
    status: str  # completed | interrupted | failed | locked_out
    detail: str | None


@dataclass(frozen=True, slots=True)
class Usage:
    rows: tuple[UsageRow, ...]


@dataclass(frozen=True, slots=True)
class Limits:
    snapshots: tuple[LimitSnapshot, ...]


@dataclass(frozen=True, slots=True)
class Gate:
    call: ToolCall


@dataclass(frozen=True, slots=True)
class Await:
    approval: ApprovalId


@dataclass(frozen=True, slots=True)
class Hook:
    event: HookEvent


@dataclass(frozen=True, slots=True)
class LoadItems:
    segment: SegmentId


@dataclass(frozen=True, slots=True)
class CallOp:
    """Run a ToolSource.QMX tool (control op or the proposal tool) on the control side.
    Accepted only for a `tool_use_id` that just received an Allow from `Gate`, consumed
    once, so a host cannot reach a QMX op without passing the policy point."""

    tool_use_id: str
    name: str
    args: Mapping[str, JsonValue]
    agent_path: AgentPath


type AskBody = Gate | Await | Hook | LoadItems | CallOp
type AskResult = Allow | Deny | Pending | HookOutcome | Sequence[Mapping[str, JsonValue]] | JsonValue


@dataclass(frozen=True, slots=True)
class Ask:
    request: int
    body: AskBody


@dataclass(frozen=True, slots=True)
class Bye:
    reason: str


type Up = Emit | Started | TurnEnded | Usage | Limits | Ask | Bye


def encode(message: Down | Up) -> bytes:
    """One JSON object per line, tagged by type name. Secrets reach a host only through
    its env at spawn (secrets.host_env) and `Rotate`. `Emit` payloads pass through
    secrets.redact before encoding, so a key that leaks into a tool result does not
    travel on into blocks, items, logs or traces."""
    raise NotImplementedError


def decode_up(line: bytes) -> Up:
    raise NotImplementedError


def decode_down(line: bytes) -> Down:
    raise NotImplementedError


__all__ = ["Ask", "AskBody", "AskResult", "Down", "Up", "decode_down", "decode_up", "encode"]
