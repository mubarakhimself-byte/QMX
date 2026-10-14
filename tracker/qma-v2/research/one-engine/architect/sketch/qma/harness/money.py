"""The money rule: agents may read money data and can never move money.

Thin native does not try to win a pattern-matching contest against Bash. Money safety
here never depends on an approval, a prompt or a setting the agent could reach. It rests
on six layers, strongest first:

1. Credential scope, when proven (`MoneyPosture.STRUCTURAL`). IF every broker credential
   that agent Bash can reach on this machine is unable to trade at the broker, then a Bash
   or Python call that reads the keyring and talks to the broker directly still cannot
   place an order. That is measured, never assumed: check S27 (M1) records per credential
   whether the broker refused an order request for scope, and `run_exposure_probe` records
   which credentials agent Bash can reach at all. The cTrader scope names used in the
   design come from the runner's own knowledge of the Open API, not from the grounding,
   so S27 is what settles them. In month one the trading node shares this PC (R25), so a
   trading-capable credential is reachable and the posture is SPEED_BUMP, which the
   operator accepted on 10-13 (R21).
2. No money-act tool exists. `tools.Effect` has no money-act member, and
   `check_tool_surface` refuses to build the `qmx` server if any tool name or metadata
   names a denied act. `PROPOSE_MONEY` is accepted on `BrokerService.propose_order` only,
   by identity. `propose_order()` writes an unsigned row; signing happens in QMN on the node.
3. Approvals bound to arguments. Every asking QMX tool runs only if its handler consumes a
   `tools.Grant` for the digest of its exact input. A remembered rule, an edited
   settings.json, bypass mode or a replay reaches the handler with no grant (03 CO-6).
4. External MCP servers are checked when the session reports its tools (init message).
   A server that exposes a money-act tool is switched off with `toggle_mcp_server`.
5. A PreToolUse callback (`pre_tool_use`) denies, in every mode including bypass and
   inside sub-agents: money-act tool names from any server, writes to QMX state paths,
   and Bash or PowerShell text that names a `qmx/` keyring entry, a configured broker
   host or the QMX home. Deny from a hook beats every mode (02a section 4). The Bash
   rules are a tripwire, not a proof.
6. Deny rules passed in code (`deny_rules`) for the same protected paths, so the CLI
   drops those calls even if the hook process misbehaves.

The deny-list itself is `qma.core.barriers.money_path` (pure, AD-16). This module adds no
second copy of it (the drift HOW gotcha 11 warns about).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from claude_agent_sdk.types import HookCallback


@dataclass(frozen=True)
class GateRules:
    """Everything the gate needs, fixed at launch. Built by `tools.py` and `home.py`."""

    proposal_tools: frozenset[str]
    """Exact tool names allowed by identity although their names end in `order`
    (`mcp__qmx__propose_order`). The only exemption from the name check."""
    mandatory_asks: frozenset[str]
    """Tool names that always ask: every QMX tool whose `Effect` asks (MANAGE,
    PROPOSE_MONEY, and DOMAIN_WRITE when the UI sets it to ask; R35). Derived from
    `tools.tool_defs`, never listed by hand."""
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
    """Build-time and init-time check, on top of the `Effect` type (HOW gotcha 11 says names
    alone are not enough, so both run). Calls the LangChain-free `check_descriptor`, which
    deletion step 0 moves from `qmx_agents.guards.money_path` to
    `qma.core.barriers.descriptors` (next to the deny-list it reads), so the mini-app
    supervisor and the harness share one copy (HOW deletable table: Split)."""
    raise NotImplementedError


def money_servers(init_tools: Iterable[str], exempt: frozenset[str]) -> frozenset[str]:
    """From the init message's tool list, the MCP server names that expose a money act.
    `chat.py` switches each off with `toggle_mcp_server(name, False)` before the first
    prompt and writes a `needs_you` block naming it."""
    raise NotImplementedError


# --- measured posture ---


@dataclass(frozen=True)
class ExposureTarget:
    kind: Literal["keyring_entry", "read_path", "write_path", "loopback"]
    value: str
    """A `qmx/*` keyring name, a path, or `127.0.0.1:<port>`."""


@dataclass(frozen=True)
class ExposureFinding:
    target: ExposureTarget
    reachable: bool
    detail: str
    """Plain words for the usage page. Never a secret value."""


@dataclass(frozen=True)
class ExposureReport:
    at: datetime
    cli_version: str
    findings: tuple[ExposureFinding, ...]


def exposure_targets(home_root: Path, keyring_refs: Iterable[str], control_port: int) -> tuple[ExposureTarget, ...]:
    """Pure. Every `qmx/*` entry named in settings.toml plus `qmx/chatgpt` and
    `qmx/control-token`; QMX home files (settings.toml, control.db, portfolio.db for read;
    claude/settings.json for write); his `~/.claude` (read and write rights); the
    qmx-control port without a bearer."""
    raise NotImplementedError


async def run_exposure_probe(env: Mapping[str, str], targets: tuple[ExposureTarget, ...]) -> ExposureReport:
    """Inside-out: what an agent's Bash could reach. Runs `python -I` as a subprocess with
    exactly `env` (the plan `launch_env`) under the same OS user the agent CLI runs as, so
    it has the agent's rights, not QMA's.

    Keyring entries: `get_password` and record only whether a value came back; the value
    is dropped inside the subprocess. Paths: access rights only (`os.access` plus a
    create-and-delete for write targets in QMX's own folders). It never opens a
    `.credentials.json` or a Keychain Claude item, his or QMX's, so QMA never reads the plan
    token while measuring. Loopback: connect and send one request with no bearer.
    """
    raise NotImplementedError


class MoneyPosture(StrEnum):
    STRUCTURAL = "structural"
    """Every broker credential agent Bash can reach was proven unable to trade."""
    SPEED_BUMP = "speed_bump"
    """At least one reachable credential is unproven or can trade. Layers 2 to 6 still
    hold. Bash plus a trading-capable keyring entry is the open path."""


def money_posture(exposure: ExposureReport, scope_proofs: Mapping[str, bool], broker_refs: frozenset[str]) -> MoneyPosture:
    """Pure and derived, never typed in. STRUCTURAL only when every broker credential in
    `broker_refs` that `exposure` found reachable has `scope_proofs[ref] is True` (S27 saw
    the broker refuse an order for scope). Anything missing or unproven is SPEED_BUMP.
    Shown on the usage page with the reachable entries named."""
    raise NotImplementedError
