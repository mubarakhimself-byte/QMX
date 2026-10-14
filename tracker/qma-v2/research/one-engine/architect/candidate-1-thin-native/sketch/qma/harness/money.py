"""The money rule: agents may read money data and can never move money.

Thin native does not try to win a pattern-matching contest against Bash. Money safety
here never depends on an approval, a prompt or a setting the agent could reach. It rests
on five layers, strongest first:

1. Broker credentials on this machine cannot trade (`MoneyPosture.STRUCTURAL`). The token
   QMX reads from the keyring is minted read-only at the broker (cTrader Open API
   `accounts` scope, exchange read-only API keys). A Bash or Python call that reads the
   keyring and talks to the broker directly still cannot place an order. The trading
   token lives only on the trading node. Until the operator does that one-time step the
   posture is SPEED_BUMP, which he accepted for now (R21), and `doctor` says so.
2. No money-act tool exists. `check_tool_surface` refuses to build the `qmx` server if any
   tool name or metadata names a denied act, except the proposal writer by identity.
   `BrokerService` has `read()` and `propose_order()` only, and `propose_order()` writes
   an unsigned row; signing happens in QMN on the node.
3. External MCP servers are checked when the session reports its tools (init message).
   A server that exposes a money-act tool is switched off with `toggle_mcp_server`.
4. A PreToolUse callback (`pre_tool_use`) denies, in every mode including bypass and
   inside sub-agents: money-act tool names from any server, writes to QMX state paths,
   and Bash or PowerShell text that names a `qmx/` keyring entry, a configured broker
   host or the QMX home. Deny from a hook beats every mode (02a section 4).
5. Deny rules passed in code (`deny_rules`) for the same protected paths, so the CLI
   drops those calls even if the hook process misbehaves.

The deny-list itself is `qma.core.barriers.money_path` (pure, AD-16). This module adds no
second copy of it (the drift HOW gotcha 11 warns about).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from claude_agent_sdk.types import HookCallback


@dataclass(frozen=True)
class GateRules:
    """Everything the gate needs, fixed at launch. Built by `tools.py` and `home.py`."""

    proposal_tools: frozenset[str]
    """Exact tool names allowed by identity although their names end in `order`
    (`mcp__qmx__propose_order`). The only exemption from the name check."""
    mandatory_asks: frozenset[str]
    """Tool names that always ask: `propose_order`, every destructive QMX op, publish,
    install, schedule and manage (R35). Derived from tool metadata in `tools.py`."""
    protected_paths: tuple[Path, ...]
    """The QMX home: claude_dir (settings, rules, login), chats_dir, control.db,
    portfolio.db, settings.toml, the plugin folder."""
    broker_hosts: frozenset[str]
    """Hostnames from settings.toml [brokers], plus the cTrader Open API hosts."""


@dataclass(frozen=True)
class Pass:
    """No opinion. The CLI's own rules, mode and `can_use_tool` decide."""


@dataclass(frozen=True)
class Ask:
    reason: str


@dataclass(frozen=True)
class Deny:
    reason: str


type Verdict = Pass | Ask | Deny
"""There is no Allow. A hook allow does not skip deny and ask rules anyway (02a section 4),
and the gate must never be the reason a call runs."""


def gate(tool_name: str, tool_input: Mapping[str, object], rules: GateRules) -> Verdict:
    """Pure. Total over every tool name, built-in or MCP, main agent or sub-agent.

    Order: proposal identity -> Ask; money-act token in the name (via
    `qma.core.barriers.money_path.match_money_path_act` over name segments) -> Deny;
    Write/Edit/NotebookEdit into `protected_paths` -> Deny; Bash/PowerShell text naming
    `qmx/`, a broker host or a protected path -> Deny; WebFetch to a broker host -> Deny;
    name in `mandatory_asks` -> Ask; else Pass.
    """
    raise NotImplementedError


def pre_tool_use(rules: GateRules) -> HookCallback:
    """Adapter from `gate` to the SDK hook output shape.

    Deny -> {"hookSpecificOutput": {"hookEventName": "PreToolUse",
             "permissionDecision": "deny", "permissionDecisionReason": reason}}
    Ask  -> same with "ask". Pass -> {}.
    Any exception inside `gate` returns deny (fail closed).
    """
    raise NotImplementedError


def deny_rules(rules: GateRules) -> list[str]:
    """Claude Code rule strings for `disallowed_tools`: `Edit(//<path>/**)`,
    `Write(//<path>/**)`, `NotebookEdit(//<path>/**)` for each protected path."""
    raise NotImplementedError


class MoneySurfaceError(RuntimeError):
    """A tool surface names a money act. The session does not start."""


def check_tool_surface(names: Iterable[str], metadata: Mapping[str, Mapping[str, object]], exempt: frozenset[str]) -> None:
    """Build-time and init-time check. Calls the LangChain-free `check_descriptor`, which
    deletion step 0 moves from `qmx_agents.guards.money_path` to
    `qma.core.barriers.descriptors` (next to the deny-list it reads), so the mini-app
    supervisor and the harness share one copy (HOW deletable table: Split)."""
    raise NotImplementedError


def money_servers(init_tools: Iterable[str], exempt: frozenset[str]) -> frozenset[str]:
    """From the init message's tool list, the MCP server names that expose a money act.
    `chat.py` switches each off with `toggle_mcp_server(name, False)` before the first
    prompt and writes a `needs_you` block naming it."""
    raise NotImplementedError


class MoneyPosture(StrEnum):
    STRUCTURAL = "structural"
    """Every broker credential readable on this machine was proven unable to trade."""
    SPEED_BUMP = "speed_bump"
    """At least one credential is unproven. Layers 2 to 5 still hold. Bash plus a
    trading-capable keyring entry is the open path."""


def money_posture(scope_probe_results: Mapping[str, bool]) -> MoneyPosture:
    """Derived, never stored by hand. Input: per broker account, whether check M1 saw the
    broker refuse an order request for scope on that account's local credential."""
    raise NotImplementedError
