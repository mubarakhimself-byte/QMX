"""Claude engine adapter. The only module that imports claude_agent_sdk.

Native everything (built-in tools, sub-agents, skills via the materialised plugin,
compaction, caching, auto memory in QMX's claude-home) with QMX's policy and hooks
spliced in through in-code callbacks. Replaces the old lockdown recipe (tools=[]):
the full Claude Code tool set is on, and every call still reaches the QMX Gate.

Why every call reaches the Gate: Claude evaluates hooks first, then deny/ask/mode/allow
rules, then can_use_tool (H1 fact 1). QMX passes no rules and no settings sources, so
the in-code PreToolUse callback sees every tool call (built-ins, MCP, the `qmx` server,
and sub-agent calls, which carry agent_id) and returns QMX's verdict:
  Allow  -> permissionDecision "allow" (+ updatedInput, additionalContext)
  Deny   -> permissionDecision "deny" with the reason
  Pending-> permissionDecision "ask"; the SDK then calls can_use_tool, which awaits the
            operator's answer over the link with no timeout (hook callbacks have one).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from qma2.host.link import Link
from qma2.model import ApprovalId, Mode
from qma2.wire import Compact, Interrupt, Reconfigure, Rotate, Spawn, Steer, Turn


class ClaudeAdapter:
    """One ClaudeSDKClient for the life of the host (streaming input mode, which the
    Python can_use_tool needs). Resume across host restarts by sdk_session_id."""

    _link: Link
    _client: Any  # ClaudeSDKClient
    _pending_by_tool_use: dict[str, ApprovalId]

    @classmethod
    async def start(cls, spawn: Spawn, link: Link) -> ClaudeAdapter:
        """# TODO pseudocode
        # options = ClaudeAgentOptions(
        #   cwd=spawn.cwd, model=route.model, effort=route.effort,
        #   permission_mode=mirror(spawn.mode),     # model-visible mode (plan reminder);
        #                                           # QMX's Gate stays authoritative; never unset
        #   resume=spawn.resume_sdk_session, fork_session=spawn.fork,
        #   system_prompt={"type":"preset","preset":"claude_code","append":QMX_APPEND,
        #                  "exclude_dynamic_sections": True},   # option spelling: probe in U1
        #   setting_sources=[],                    # QMX loads every layer itself
        #   plugins=[{"type":"local","path":spawn.claude_plugin_dir}],   # skills + agents, no hooks
        #   agents={n: to_agent_definition(a) for n, a in spawn.agents.items()},
        #   mcp_servers={**to_sdk_mcp(spawn.mcp), "qmx": qmx_server(spawn.qmx_tools, link)},
        #   hooks={PreToolUse: [pre_tool_use], PostToolUse: [post_tool_use],
        #          PostToolUseFailure: [...], UserPromptSubmit: [...]? (control already ran it),
        #          Stop: [stop], SubagentStart: [...], SubagentStop: [...], PreCompact: [...]},
        #   can_use_tool=can_use_tool,
        #   include_partial_messages=True,         # message.delta for the live channel
        #   env={},                                # host env is already the allow-list
        #   max_turns=None)
        # client = ClaudeSDKClient(options); await client.connect()
        """
        raise NotImplementedError

    async def turn(self, message: Turn) -> None:
        """# TODO pseudocode
        # prompt = (context_prefix if first turn of segment) + extra_context + input.text
        # await client.query(prompt)
        # async for m in client.receive_response(): translate(m)
        # translate (research 32 B4.1):
        #   SystemMessage init          -> link.started(session_id, tools)
        #   StreamEvent text delta       -> emit message.delta (live)
        #   AssistantMessage TextBlock   -> emit message.done (merge by message id)
        #   AssistantMessage ToolUseBlock-> emit tool.started
        #   UserMessage ToolResultBlock  -> emit tool.finished
        #   parent_tool_use_id set       -> same event under the sub-agent's agent_path
        #   task_* system messages       -> subagent.started / finished
        #   compact_boundary             -> emit compacted; control fires PostCompact
        #   RateLimitEvent               -> link.limits(...)   (cache-on-change semantics)
        #   ResultMessage                -> link.usage(model_usage rows, dedupe turn+model);
        #                                   link.turn_ended(completed|interrupted|failed);
        #                                   status "rejected" limit -> locked_out
        """
        raise NotImplementedError

    async def steer(self, message: Steer) -> None:
        """client.query(text) while streaming: queued input folds into the running turn
        (UNVERIFIED in Python; U6 live check decides, fallback = interrupt + new query)."""
        raise NotImplementedError

    async def interrupt(self, message: Interrupt) -> None:
        """client.interrupt(), retried while 'interrupt pending' (copied recipe)."""
        raise NotImplementedError

    async def reconfigure(self, message: Reconfigure) -> None:
        """model -> client.set_model(); mode -> client.set_permission_mode();
        effort -> no Python setter (H1 fact 6): disconnect and reconnect with
        resume=session_id and the new effort, between turns only."""
        raise NotImplementedError

    async def compact(self, message: Compact) -> None:
        """Send '/compact <focus>' as the prompt (H1 fact 6)."""
        raise NotImplementedError

    async def rotate(self, message: Rotate) -> None:
        raise NotImplementedError  # never used: Claude has no QMX-held credential

    async def close(self) -> None:
        raise NotImplementedError

    # --- callbacks ---------------------------------------------------------

    async def _pre_tool_use(self, payload: Mapping[str, Any], tool_use_id: str | None, context: Any) -> Mapping[str, Any]:
        """# TODO pseudocode
        # call = ToolCall(tool_use_id, payload.tool_name, payload.tool_input,
        #                 source=source_of(name), agent_path=path_of(payload.agent_id), engine=CLAUDE)
        # v = await link.gate(call)
        # Allow  -> {"hookSpecificOutput": {"permissionDecision": "allow",
        #             "updatedInput": v.input, "additionalContext": "\n".join(v.context)}}
        # Deny   -> {"hookSpecificOutput": {"permissionDecision": "deny", "permissionDecisionReason": v.reason}}
        # Pending-> remember tool_use_id -> approval; {"permissionDecision": "ask"}
        """
        raise NotImplementedError

    async def _can_use_tool(self, name: str, tool_input: Mapping[str, Any], context: Any) -> Any:
        """Reached only after PreToolUse said "ask". Correlate to the approval by
        tool_use_id when the context carries it, else by (name, input digest) FIFO
        (probe in U2). Await the operator; return PermissionResultAllow(updated_input=...)
        or PermissionResultDeny(message=..., interrupt=stop_turn). AskUserQuestion answers
        come back as updated_input, per cc:agent-sdk/user-input."""
        raise NotImplementedError


def mirror(mode: Mode) -> str:
    """QMX Mode -> SDK permission_mode string. Always explicit (H1 fact 3)."""
    raise NotImplementedError
