"""HookRunner: Claude's hook wire format, run by QMX on both engines.

Claude engine: QMX does NOT write hooks into the Claude settings file. It runs this runner
from in-code SDK callbacks (PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit,
Stop, SubagentStart/Stop, PreCompact, PermissionRequest, Notification; H1 fact 2) so the one
runner is the one place hook policy lives. Events Python callbacks cannot see (SessionStart,
SessionEnd, PostCompact) are fired by the engine adapter at the moments it owns.
OpenAI engine: fired from the gate wrapper, the prompt builder and the compactor.

Wire contract (cc:hooks): JSON on stdin; exit 0 + JSON stdout; exit 2 blocks with stderr as
the reason; other codes are non-blocking errors. Handler kinds: `command`, `http`. (`prompt`,
`agent`, `mcp_tool` handlers are later.)

Hook "allow" never overrides a deny or ask rule (cc:permissions:589). PreToolUse order of
strength: deny > defer > ask > allow (H1 fact 2).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from qma2.config import HookEntry
from qma2.types import Json, ToolCall

type HookEvent = Literal[
    "SessionStart", "SessionEnd", "UserPromptSubmit", "PreToolUse", "PermissionRequest",
    "PostToolUse", "PostToolUseFailure", "Stop", "SubagentStart", "SubagentStop",
    "PreCompact", "PostCompact", "Notification",
]


@dataclass(frozen=True)
class HookOutcome:
    """Parsed union of every hook's output for one event."""

    blocked: bool
    reason: str = ""
    permission: Literal["allow", "deny", "ask", "defer"] | None = None
    updated_input: Mapping[str, object] | None = None
    additional_context: str = ""
    system_message: str = ""
    stop_turn: bool = False  # `continue: false`


class HookRunner:
    def __init__(self, config: Mapping[HookEvent, Sequence[HookEntry]], cwd: Path, env: Mapping[str, str]) -> None:
        """`env` is the scrubbed child env; hooks never see provider keys."""
        raise NotImplementedError

    async def fire(self, event: HookEvent, payload: Json, *, call: ToolCall | None = None) -> HookOutcome:
        """Run every matching handler; merge per Claude's strength order; log one line per hook
        to the thread's trace (hooks.log in the export)."""
        raise NotImplementedError


def pre_tool_payload(call: ToolCall, session_id: str) -> Json:
    """Pure: Claude's PreToolUse stdin JSON (`tool_name`, `tool_input`, `session_id`, `cwd`)."""
    raise NotImplementedError
