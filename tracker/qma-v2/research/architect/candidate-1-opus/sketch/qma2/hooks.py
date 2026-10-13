"""The QMX hook runner: Claude's wire format, run by QMX, on both engines.

Hooks never run inside an engine. On the Claude engine, QMX passes no settings hooks
(setting_sources=[] and a hook-free materialised plugin) and instead registers in-code
callbacks in the host that forward each event over the link; this runner executes the
configured hooks in the qmx-control process and returns one merged HookOutcome. On the
OpenAI engine the host's tool wrappers and loop forward the same events. So one hook
script behaves the same everywhere, and the Python SDK's TS-only events
(SessionStart, SessionEnd, PostCompact) fire from QMX's own vantage point: the thread
actor opens/closes sessions and sees `compacted` events.

Contract (cc:hooks, copied by Codex): stdin JSON in; exit 0 -> stdout JSON parsed;
exit 2 -> block with stderr as reason; other codes -> non-blocking error.
Full Claude semantics are the target, including PreToolUse `ask` and `updatedInput`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

from qma2.model import AgentPath, JsonValue, Mode, ThreadId, ToolCall


class HookEventName(StrEnum):
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    PRE_TOOL_USE = "PreToolUse"
    PERMISSION_REQUEST = "PermissionRequest"
    POST_TOOL_USE = "PostToolUse"
    POST_TOOL_USE_FAILURE = "PostToolUseFailure"
    STOP = "Stop"
    SUBAGENT_START = "SubagentStart"
    SUBAGENT_STOP = "SubagentStop"
    PRE_COMPACT = "PreCompact"
    POST_COMPACT = "PostCompact"
    INTERRUPT = "Interrupt"  # Codex extension


# Event payloads. Each renders to Claude's stdin JSON in `wire_payload`.


@dataclass(frozen=True, slots=True)
class SessionStart:
    thread: ThreadId
    source: Literal["startup", "resume", "compact", "switch"]


@dataclass(frozen=True, slots=True)
class SessionEnd:
    thread: ThreadId
    reason: str


@dataclass(frozen=True, slots=True)
class UserPromptSubmit:
    thread: ThreadId
    prompt: str


@dataclass(frozen=True, slots=True)
class PreToolUse:
    call: ToolCall
    thread: ThreadId
    mode: Mode


@dataclass(frozen=True, slots=True)
class PermissionRequest:
    call: ToolCall
    thread: ThreadId


@dataclass(frozen=True, slots=True)
class PostToolUse:
    call: ToolCall
    thread: ThreadId
    result: str
    failed: bool


@dataclass(frozen=True, slots=True)
class Stop:
    thread: ThreadId
    agent_path: AgentPath
    last_message: str


@dataclass(frozen=True, slots=True)
class SubagentStart:
    thread: ThreadId
    agent_path: AgentPath
    agent_type: str


@dataclass(frozen=True, slots=True)
class SubagentStop:
    thread: ThreadId
    agent_path: AgentPath


@dataclass(frozen=True, slots=True)
class Compact:
    thread: ThreadId
    phase: Literal["pre", "post"]
    trigger: Literal["manual", "auto"]
    focus: str | None


type HookEvent = (
    SessionStart | SessionEnd | UserPromptSubmit | PreToolUse | PermissionRequest
    | PostToolUse | Stop | SubagentStart | SubagentStop | Compact
)


@dataclass(frozen=True, slots=True)
class HookOutcome:
    """Merged result of every matching handler. Deny beats ask beats allow."""

    decision: Literal["allow", "ask", "deny"] | None = None
    reason: str | None = None
    updated_input: Mapping[str, JsonValue] | None = None
    context: tuple[str, ...] = ()  # additionalContext, in handler order
    block: bool = False  # Stop / UserPromptSubmit / PostToolUse `decision: block`
    stop_turn: bool = False  # `continue: false`
    system_message: str | None = None  # shown to the operator, not the model


@dataclass(frozen=True, slots=True)
class HookHandler:
    """Baseline handler type is `command`. `http`, `prompt`, `agent` are later."""

    event: HookEventName
    matcher: str | None  # tool-name pattern for tool events
    command: str
    timeout_s: float
    source: Path  # settings file / plugin hooks.json / skill or agent frontmatter


class HookRunner:
    """Built from ResolvedConfig.hooks. Stateless apart from that list."""

    def __init__(self, handlers: Sequence[HookHandler], cwd: Path, env: Mapping[str, str]) -> None:
        """`env` is the scrubbed tool env (secrets.tool_env), never the control env."""
        raise NotImplementedError

    async def run(self, event: HookEvent) -> HookOutcome:
        """Run matching handlers in parallel (as Claude does), merge, return.

        # TODO pseudocode
        # payload = wire_payload(event)                 # Claude stdin JSON shape
        # results = await gather(*(spawn(h, payload) for h in matching(event)))
        # for each: exit 2 -> deny/block with stderr; exit 0 -> parse JSON (invalid -> error)
        # merge: any deny -> deny; else any ask -> ask; else any allow -> allow;
        #        updated_input: last writer in declaration order wins (Claude doc'd);
        #        context: concatenate.
        # every run is reported as Event(kind="tool.progress"-free) hook trace, not a block
        """
        raise NotImplementedError


def wire_payload(event: HookEvent) -> Mapping[str, JsonValue]:
    """Render Claude's documented stdin JSON (hook_event_name, session_id, cwd,
    tool_name, tool_input, ...). session_id is the ThreadId so scripts see one id per
    conversation regardless of engine segments."""
    raise NotImplementedError
