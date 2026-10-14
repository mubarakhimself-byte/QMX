"""The `qmx` in-process MCP server: QMX's own tools, nothing else.

"The copilot is the same API as the UI" (01 section 11.1), so the tools are the existing
control-plane and domain functions, not new code. In-process means the CLI never receives
the qmx-control bearer token (HOW seam 2).

One list. `tool_defs` below is the only place a QMX tool joins the agent surface. The
mandatory-ask set and the proposal exemption are derived from its output (`gate_rules`),
not listed again.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal

if TYPE_CHECKING:
    from claude_agent_sdk import McpSdkServerConfig
    from qmx_broker.service import BrokerService
    from qmx_control.service import ControlService

    from qma.harness.home import SessionId
    from qma.harness.money import GateRules
    from qma.harness.profiles import ProfileName, Profiles


type Effect = Literal["read", "write", "propose"]


@dataclass(frozen=True)
class ToolDef:
    name: str
    description: str
    input_schema: dict[str, object]
    effect: Effect
    asks: bool
    """True for every write the operator must approve (destructive ops, publish, install,
    schedule, manage) and for `propose_order`."""
    call: Callable[[dict[str, object]], Awaitable[dict[str, object]]]


AGENT_OPERATIONS: Final[frozenset[str]] = frozenset()
"""Names from `qmx_control.server.OPERATIONS` the agent may call. An explicit allow-list:
`settings_put` and `backup_weekly` stay out, because an agent that edits a provider row's
base URL could send a stored key to a host it chose. Filled during U3."""


type Delegate = Callable[[SessionId, "ProfileName", str], Awaitable[str]]
"""Runs a child chat to completion and returns its final text. Provided by `Harness`."""


def tool_defs(
    *,
    control: ControlService,
    broker: BrokerService,
    session_id: SessionId,
    profiles: Profiles,
    delegate: Delegate | None,
) -> list[ToolDef]:
    """Collect every QMX tool for one chat.

    Sources: `qmx_tools.functions.domain_functions(ctx)` (moved out of the LangChain-bound
    `registry.py`, HOW gotcha 3), `AGENT_OPERATIONS` rows (their `destructiveHint` sets
    `asks`), `BrokerService.list_accounts` and the five `read` kinds, `propose_order`
    (effect "propose", asks), and `delegate` when not None (Child chats pass None).
    The ToolContext handed to domain functions reuses `control`, so no second
    `ControlService` writer is created (HOW "second writer").
    """
    raise NotImplementedError


def build_server(defs: list[ToolDef]) -> McpSdkServerConfig:
    """`create_sdk_mcp_server(name="qmx", tools=[...])`. Runs `money.check_tool_surface`
    over the names first and refuses to build on any match."""
    raise NotImplementedError


def gate_rules(defs: list[ToolDef], *, protected: tuple, broker_hosts: frozenset[str]) -> GateRules:
    """Derive `GateRules` from the same defs: proposal_tools = names with effect "propose";
    mandatory_asks = names with `asks`. Tool names are prefixed `mcp__qmx__`."""
    raise NotImplementedError


DELEGATE_SCHEMA: Final[dict[str, object]] = {
    "type": "object",
    "properties": {
        "profile": {"type": "string", "description": "A provider profile from the allow-list"},
        "prompt": {"type": "string"},
    },
    "required": ["profile", "prompt"],
}
"""`mcp__qmx__delegate`: the one QMX tool that adds capability the SDK lacks. Native
sub-agents cannot change provider (AgentDefinition has no env, 02a section 5), and the
operator wants GPT and key models for helpers. The child is a full chat (its own CLI
process, its own qmx-control child session, its own asks), so it obeys every rule above
without extra code."""
