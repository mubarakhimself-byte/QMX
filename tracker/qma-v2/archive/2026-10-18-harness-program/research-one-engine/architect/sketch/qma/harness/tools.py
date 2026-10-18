"""The `qmx` in-process MCP server: QMX's own tools, nothing else.

"The copilot is the same API as the UI" (01 section 11.1), so the tools are the existing
control-plane and domain functions, not new code. In-process means the CLI never receives
the qmx-control bearer token (HOW seam 2).

One list. `tool_defs` below is the only place a QMX tool joins the agent surface. Every
tool declares an `Effect`; there is no default. Which tools ask, the proposal exemption
and the grant check are all derived from that one field, not listed again.

Later seam (U10, not built): `build_server` returns an in-process SDK server today. A CLI
under another OS account would get the same `ToolDef` list served as an HTTP MCP endpoint
on the relay listener behind its grant, so `Effect`, `Grants` and the money gate keep
running in the operator's process.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Final, Literal, NewType

if TYPE_CHECKING:
    from claude_agent_sdk import McpSdkServerConfig, McpServerConfig
    from qmx_broker.service import BrokerService
    from qmx_control.service import ControlService

    from qma.harness.home import QmxHome, SessionId
    from qma.harness.money import GateRules
    from qma.harness.profiles import ProfileName, Profiles


class Effect(Enum):
    """What a QMX tool does to the world. Closed. There is no member for moving money, so
    no tool can be registered as a money act: the type has no slot for it.

    READ           reads QMX or broker state. Runs without asking.
    DOMAIN_WRITE   writes QMX research state (library, backtests, notes). Asks or not per
                   `settings.toml [agents] domain_write` ("allow" | "ask"), UI-editable.
                   `delegate` is DOMAIN_WRITE: it starts a child chat whose own acts face
                   their own gates, and spend is bounded by the delegate allow-list and the
                   child's [budgets] limits. The gate denies it inside native sub-agents (R33).
    MANAGE         publish, install, schedule, change settings, destructive control-plane
                   ops. Always asks (R35).
    PROPOSE_MONEY  writes an unsigned order proposal. Always asks. Accepted on
                   `BrokerService.propose_order` only, by identity. Signing and sending
                   belong to QMN on the node, never to a tool.
    """

    READ = "read"
    DOMAIN_WRITE = "domain_write"
    MANAGE = "manage"
    PROPOSE_MONEY = "propose_money"


type DomainWritePolicy = Literal["allow", "ask"]


def asks(effect: Effect, domain_write: DomainWritePolicy) -> bool:
    """Pure. The one table: READ no; DOMAIN_WRITE per policy; MANAGE and PROPOSE_MONEY yes."""
    raise NotImplementedError


@dataclass(frozen=True)
class ToolDef:
    name: str
    description: str
    input_schema: dict[str, object]
    effect: Effect
    """Required, no default. A tool without one does not construct."""
    call: Callable[[dict[str, object]], Awaitable[dict[str, object]]]


AGENT_OPERATIONS: Final[Mapping[str, Effect]] = {}
"""Names from `qmx_control.server.OPERATIONS` the agent may call, each with its declared
effect. An explicit allow-list: `settings_put` and `backup_weekly` stay out, because an
agent that edits a provider row's base URL could send a stored key to a host it chose.
A CI test fails if an op with `destructiveHint` is declared as anything but MANAGE.
Filled during U3."""


# --- approvals bound to arguments (03 CO-6) ---

ArgsDigest = NewType("ArgsDigest", str)
"""sha256 over the tool name and the canonical JSON of its input (sorted keys, no
whitespace, UTF-8). Computed on the final input, after any operator edit."""


def args_digest(tool_name: str, tool_input: Mapping[str, object]) -> ArgsDigest:
    raise NotImplementedError


@dataclass(frozen=True)
class Grant:
    tool: str
    digest: ArgsDigest


class Grants:
    """One chat's approvals for asking QMX tools. Owned by that chat (written by its answer
    path, consumed by its tool handlers, one event loop, no lock).

    A grant is created only when the operator answers AllowOnce on that exact call, and is
    consumed by the first handler run that matches it. So an approval never outlives the
    arguments the operator saw: a replay, a changed field, an "allow" rule someone wrote
    into settings.toml [claude], or bypass mode all reach the handler with no grant and are refused.
    Grants live in memory; a qmx-control restart drops them, matching how asks expire.
    """

    def record(self, grant: Grant) -> None:
        raise NotImplementedError

    def consume(self, tool: str, digest: ArgsDigest) -> bool:
        """True once per recorded grant, then False. Idempotent on a missing grant."""
        raise NotImplementedError


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
    """Collect every QMX tool for one chat, each with its declared `Effect`.

    Sources: `qmx_tools.functions.domain_functions(ctx)` (moved out of the LangChain-bound
    `registry.py`, HOW gotcha 3; data and research reads READ, writes DOMAIN_WRITE),
    `AGENT_OPERATIONS` rows, `BrokerService.list_accounts` and the five `read` kinds
    (READ), `propose_order` (PROPOSE_MONEY), and `delegate` when not None (Child chats pass
    None). The ToolContext handed to domain functions reuses `control`, so no second
    `ControlService` writer is created (HOW "second writer").
    """
    raise NotImplementedError


def build_server(defs: list[ToolDef], *, grants: Grants, domain_write: DomainWritePolicy, enforce_grants: bool = True) -> McpSdkServerConfig:
    """`create_sdk_mcp_server(name="qmx", tools=[...])`.

    Refuses to build on: a duplicate name; a name or metadata `money.check_tool_surface`
    flags; PROPOSE_MONEY on anything but the broker's `propose_order` (identity, not name).
    Wraps every tool for which `asks(effect, domain_write)` is True so its handler first
    calls `grants.consume(name, args_digest(name, input))` and returns an error result
    naming the rule when that is False. `enforce_grants=False` exists for one live check
    only (`TestMode.grants`).
    """
    raise NotImplementedError


def gate_rules(
    defs: list[ToolDef],
    *,
    domain_write: DomainWritePolicy,
    home: QmxHome,
    keyring_names: frozenset[str],
    broker_hosts: frozenset[str],
) -> GateRules:
    """Derive `GateRules` from the same defs: proposal_tools = names with PROPOSE_MONEY;
    mandatory_asks = names where `asks(effect, domain_write)`. Tool names are prefixed
    `mcp__qmx__`. Protected, secret and personal-home paths come from `home` and the OS
    user's home, normalized once with `money.normalize_path`."""
    raise NotImplementedError


@dataclass(frozen=True)
class VettedServers:
    """External MCP servers that passed `vet_mcp_servers`, as SDK configs, plus the config
    hash each was vetted under. Only these reach `mcp_servers`; `strict_mcp_config=True`
    makes the CLI ignore every other MCP config (02a section 7)."""

    configs: Mapping[str, McpServerConfig]
    vetted_hash: Mapping[str, str]


async def vet_mcp_servers(declared: Mapping[str, McpServerConfig], *, previous: VettedServers | None) -> VettedServers:
    """Before any launch uses them: start each declared server (settings.toml [mcp_servers])
    with the Python MCP client, list its tools, and run `money.check_tool_surface` on names
    and metadata. A server that exposes a money act is refused with a `needs_you` block and
    never launched (A8, B10). Re-vetted when its config hash changes. A tool that a server
    adds later is still denied by name in the gate."""
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
process, its own relay grant, its own qmx-control child session, its own asks, verbatim
prompts), so it obeys every rule above without extra code."""
