"""One live chat = one `Host` = one `ClaudeSDKClient` = one CLI process.

The only module in the repo that imports `claude_agent_sdk` (import-linted).
The SDK client runs as an asyncio task inside qmx-control; the CLI is its child.
Harvested from the daemon's `native_claude.py` (`_connect`, `events`, the init
tool-list check, the unknown-outcome rule), minus its one-tool limit and max_turns.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from qma_core.money_classify import MoneyHit, NotMoney, Proposal, ToolCall, classify
from qma_gateway.contract import ModelId, ThreadId, ToolCatalogSnapshot
from qmx_harness.api import Prompt
from qmx_harness.env import SessionEnv


@dataclass(frozen=True, slots=True)
class SubAgentSpec:
    """A row of the profile's agent catalog (UI-editable). `model` may be any model
    in the lease, on any lane: the gateway routes it. This replaces a QMX
    cross-provider delegate tool; there is one way to run a sub-agent."""

    name: str
    description: str
    prompt: str
    model: ModelId
    tools: tuple[str, ...] | None
    effort: str | None
    background: bool


@dataclass(frozen=True, slots=True)
class HostConfig:
    thread: ThreadId
    resume: str | None  # sdk session id from harness.db
    env: SessionEnv
    workspace: Path
    mode: str  # always passed explicitly; omitted can mean auto (02a trap 3)
    effort: str | None
    agents: tuple[SubAgentSpec, ...]
    append_prompt: str  # QMX rules + repo CLAUDE.md/AGENTS.md, survives compaction
    catalog: ToolCatalogSnapshot
    plugin_dir: Path  # QMX's local plugin: skills, commands, settings hooks
    mcp_servers: Mapping[str, Mapping[str, object]]  # from settings, strict


def build_options(cfg: HostConfig, qmx_server: object, hooks: Mapping[str, object], can_use_tool: object) -> object:
    """Pure mapping HostConfig -> ClaudeAgentOptions.

    tools and system_prompt presets `claude_code` (+ append); setting_sources per
    live check L12 ([] until the user tier is proven to follow CLAUDE_CONFIG_DIR);
    strict_mcp_config=True; plugins=[plugin_dir]; mcp_servers={"qmx": qmx_server, ...};
    permission_mode=cfg.mode; hooks (PreToolUse money callback); can_use_tool;
    disallowed rules for money shell patterns; enable_file_checkpointing=True;
    include_partial_messages=True; env=cfg.env.values; cwd=cfg.workspace;
    resume=cfg.resume; agents from cfg.agents.
    """
    raise NotImplementedError


def money_hook_decision(tool_name: str, tool_input: Mapping[str, object], agent_id: str | None, catalog: ToolCatalogSnapshot) -> Mapping[str, object]:
    """Pure. The PreToolUse callback body. Runs for every tool call in every mode,
    sub-agents included (input carries agent_id).

    MoneyHit -> {"permissionDecision": "deny", "permissionDecisionReason": hit.why}
    Proposal -> {"permissionDecision": "ask"}   (the operator signs, CO-2)
    NotMoney -> {}                              (fall through to native rules and mode)
    Never returns "allow": a hook allow would add nothing and a bug could widen it.
    """
    match classify(ToolCall(tool_name, tool_input, agent_id), catalog):
        case MoneyHit(act, why):
            return {"permissionDecision": "deny", "permissionDecisionReason": f"money rule: {act}: {why}"}
        case Proposal():
            return {"permissionDecision": "ask"}
        case NotMoney():
            return {}


@dataclass(frozen=True, slots=True)
class Block:
    """One of qmx-control's 14 block kinds, written with sessions_append."""

    type: str
    content: Mapping[str, object]


def project(message: object) -> list[Block]:
    """Pure. SDK message -> blocks, the mapping `stream_turn` defines today:
    text, tool, plan (task tools), agents (+ child session per parent_tool_use_id),
    permission. RateLimitEvent and ResultMessage usage are ignored here: the
    gateway is the one usage source."""
    raise NotImplementedError


class Host:
    @classmethod
    async def spawn(cls, cfg: HostConfig) -> Host:
        """connect(); on the init SystemMessage verify the tool list against
        expectations (no unknown MCP tools); store the sdk session id."""
        raise NotImplementedError

    async def turn(self, prompt: Prompt) -> AsyncIterator[Block]:
        raise NotImplementedError

    async def set_model(self, model: ModelId) -> None:
        raise NotImplementedError

    async def interrupt(self) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError
