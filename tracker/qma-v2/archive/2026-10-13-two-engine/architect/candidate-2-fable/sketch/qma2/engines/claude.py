"""ClaudeEngine: the Claude Agent SDK with Claude Code's full structure, under QMX's gate.

What changes versus the old native recipe (native_claude.py), and why:
- `tools` not stripped; `disallowed_tools=[]`; skills/agents/plugins from QMX's config home.
  The lockdown existed for a missing worker boundary; the sealed-secret tier plus managed
  rules replace it (design.md tension 1).
- `permission_mode` is always passed explicitly (never `auto`, H1 fact 1).
- `can_use_tool` is wired to the Gate, with the required streaming-input mode and the
  PreToolUse hook (H1 fact 1 workaround). No allow rules in settings, so nothing shadows it.
- Sub-agent output and background tasks are accepted and mapped to `agent_path`.
- `ResultMessage.usage`, `model_usage`, `total_cost_usd` and `RateLimitEvent` are read.
- The env is scrubbed and allow-listed, not merely refused (Gotcha 6), via `Launcher`.
- Version pins are "≥ reviewed" not "==": `claude-agent-sdk>=0.2.165` (Windows wheel with a
  bundled CLI; the two-week rule is the operator's call, noted in design.md).

Kept from the recipe: preflight check names only; `claude auth status` must say claude.ai;
QMX never reads credential files; `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`; no token
anywhere (H1 fact 4).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Any

from qma2.engines.base import Engine, EngineSession, SegmentContext
from qma2.types import (
    Account,
    ApprovalAnswer,
    Effort,
    EngineEvent,
    EngineKind,
    ModelRef,
    ProbeResult,
    Segment,
    Turn,
    TurnInput,
)

CLAUDE_ENV_INJECT: Mapping[str, str] = {
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
    "ENABLE_CLAUDEAI_MCP_SERVERS": "false",
    # CLAUDE_CONFIG_DIR added per account; auto memory stays on but inside that dir (H1 fact 3)
}


class ClaudeEngine(Engine):
    kind = EngineKind.CLAUDE

    async def probe(self, account: Account, home_env: Mapping[str, str]) -> ProbeResult:
        raise NotImplementedError

    async def open(self, segment: Segment, ctx: SegmentContext) -> EngineSession:
        """Build ClaudeAgentOptions:
        # TODO:
        #   cwd, resume=segment.engine_session_id, model, effort (UNVERIFIED mid-session effort
        #   API; set at open), system_prompt={"type":"preset","preset":"claude_code",
        #   "append": qmx_rules_text(ctx)}  with exclude_dynamic_sections=True,
        #   permission_mode=ctx.config.mode, can_use_tool=self._can_use_tool(ctx.gate),
        #   hooks={PreToolUse:[gate hook], PostToolUse, PostToolUseFailure, UserPromptSubmit,
        #          Stop, SubagentStart, SubagentStop, PreCompact, PermissionRequest,
        #          Notification → HookRunner}, setting_sources=[] (QMX supplies everything
        #   explicitly), agents=load_agent_defs(ctx.config.agents_dirs), skills=list(...),
        #   plugins=[], mcp_servers={"qmx": ctx.registry.to_claude_mcp(...), **ctx.config.mcp_servers},
        #   include_partial_messages=True (TextDelta for the console), max_turns from settings,
        #   env=ctx.env | CLAUDE_ENV_INJECT | {CLAUDE_CONFIG_DIR: account.claude_home},
        #   cli_path=launcher.wrap_command(...) so the CLI joins ctx.tree.
        #   Streaming input mode (the can_use_tool workaround): connect(), then query per turn.
        # Fire HookRunner SessionStart here (not a Python callback event, H1 fact 2)."""
        raise NotImplementedError


class ClaudeSession(EngineSession):
    def __init__(self, client: Any, ctx: SegmentContext, segment: Segment) -> None:
        raise NotImplementedError

    def run(self, turn: Turn) -> AsyncIterator[EngineEvent]:
        """Translate `receive_response()` (research 32 B4.1):
        SystemMessage init → SessionBound(session_id)
        stream_event text delta → TextDelta
        AssistantMessage TextBlock → TextDone (merge by message id); ToolUseBlock → ToolStarted
        UserMessage tool_result → ToolFinished (denied when the gate denied)
        parent_tool_use_id / task_* subtypes → SubagentStarted/Finished with agent_path
        compact_boundary → Compacted
        RateLimitEvent → LimitUpdated (cache last per window)
        ResultMessage → UsageRecorded per model in model_usage (dedupe_key =
          f"claude:{session_id}:{turn.id}:{model}"), then TurnFinished(stop_reason from subtype:
          success→done, error_max_turns→max_turns, aborted_*→interrupted, else error)."""
        raise NotImplementedError

    async def steer(self, input: TurnInput) -> None:
        """Mid-turn `client.query(text)` in streaming-input mode. UNVERIFIED whether it folds
        into the running turn; the live check in U7 decides, else it queues as the next turn."""
        raise NotImplementedError

    async def interrupt(self) -> None:
        """client.interrupt(), retried while "interrupt pending"; bounded; then tree.kill()."""
        raise NotImplementedError

    async def switch(self, model: ModelRef | None, effort: Effort | None) -> None:
        """client.set_model(model). Effort: UNVERIFIED API; fallback = reopen the client on
        the same session id with the new option (resume keeps context)."""
        raise NotImplementedError

    async def compact(self, focus: str) -> None:
        """Send `/compact {focus}` as the prompt (H1 fact 6)."""
        raise NotImplementedError

    async def resume_from(self, engine_state: bytes, answer: ApprovalAnswer) -> AsyncIterator[EngineEvent]:
        raise NotImplementedError  # NotResumable

    async def close(self) -> None:
        raise NotImplementedError


def load_agent_defs(dirs: Any) -> dict[str, Any]:
    """Parse `*.md` frontmatter into `AgentDefinition`s. Shared with the OpenAI Agent tool
    through a frontmatter-only parser in qma2.config (no SDK types there)."""
    raise NotImplementedError


def qmx_rules_text(ctx: SegmentContext) -> str:
    """The `append` block: money boundary in plain words, placement rules, QMX tool guidance.
    Byte-stable per segment so the cache holds."""
    raise NotImplementedError
