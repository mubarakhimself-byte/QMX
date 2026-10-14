"""QMX's rebuild of Claude Code's tool set for the OpenAI engine (H5, BASELINE 2.3).

Names and argument shapes copy Claude's, so permission rules and hook matchers are
written once. Every tool is a FunctionTool whose on_invoke goes through `gated`, so the
QMX Gate sees every call on this engine (and sub-agents' calls, with their agent_path).

Set: Read, Write, Edit, Glob, Grep, Bash (POSIX) / PowerShell (Windows), WebFetch,
WebSearch (QMX backend), TodoWrite, AskUser, Skill, Agent, apply_patch (GPT models only),
`mcp__<server>__<tool>` for each configured MCP tool (QMX connects the servers itself and
wraps their tools, instead of handing MCPServer objects to the SDK), and
`mcp__qmx__<op>` for QMX ops and the proposal tool (executed on the control side).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qma2.host.link import Link
from qma2.model import AgentPath, JsonValue, Mode, ToolSource
from qma2.wire import Spawn

type Handler = Callable[[Mapping[str, JsonValue], "ToolContext"], Awaitable[str]]


@dataclass(frozen=True, slots=True)
class ToolContext:
    cwd: Path
    agent_path: AgentPath
    mode: Mode
    env: Mapping[str, str]  # secrets.tool_env: no provider key, no QMX_*


@dataclass(frozen=True, slots=True)
class QmxTool:
    """Defined once; the FunctionTool is generated from it."""

    name: str
    description: str
    schema: Mapping[str, JsonValue]  # strict: additionalProperties false
    source: ToolSource
    read_only: bool  # parallel-safe
    handler: Handler
    max_result_tokens: int = 25_000  # Claude Code's cap; overflow saved, head+tail returned


def gated(tool: QmxTool, link: Link) -> Any:
    """Wrap a QmxTool as an agents.FunctionTool.

    # TODO pseudocode
    # async def on_invoke(ctx, args_json):
    #     call = ToolCall(id, tool.name, parse(args_json), tool.source, ctx.agent_path, OPENAI)
    #     verdict = await link.decide(call)          # gate, then wait for the operator if Pending
    #     if Deny: return f"Denied: {reason}"        # the model reads it, like Claude
    #     out = await link.hook(PostToolUse(...)) after running tool.handler(verdict.input)
    #     on exception: link.hook(PostToolUseFailure) and return a one-line error
    #     return cap(result) + "\n".join(verdict.context + out.context)
    """
    raise NotImplementedError


def build(spawn: Spawn, link: Link, agent_path: AgentPath = AgentPath()) -> Sequence[Any]:
    """Tool list for one agent (root or sub-agent), filtered by its definition's tools /
    disallowedTools. Sorted by name: a stable order keeps the prompt cache warm."""
    raise NotImplementedError


class ProcessTable:
    """Every Bash/PowerShell process tree this host started, so interrupt and shutdown
    leave no orphans (H3). Job Object per command on Windows, process group on POSIX.
    Commands get cwd pinned, a timeout, an output cap and secrets.tool_env."""

    async def run(self, command: str, ctx: ToolContext, timeout_s: float) -> tuple[int, str]:
        raise NotImplementedError

    async def kill_all(self) -> None:
        raise NotImplementedError


class AgentTool:
    """Claude's `Agent` tool on the OpenAI engine (H13). Its own call is gated first, so
    depth and concurrency caps are enforced by policy.decide like every other rule.
    Builds a nested agents.Agent from the AgentDef (prompt, tools, model, effort) whose
    tools are `build(..., agent_path=child)`, runs it, returns only the final text.
    background=true runs as a task in this host's registry; SendMessage / wait / list /
    interrupt tools copy Codex V2. Approvals from children carry their agent_path, so the
    operator sees which agent is asking."""

    async def __call__(self, args: Mapping[str, JsonValue], ctx: ToolContext) -> str:
        raise NotImplementedError


class WebSearchBackend:
    """QMX-provided search for routes without hosted search (ChatGPT route, Chat
    Completions providers). Backend choice is an open question (BASELINE open item 5)."""

    async def search(self, query: str, *, max_results: int) -> Sequence[Mapping[str, JsonValue]]:
        raise NotImplementedError
