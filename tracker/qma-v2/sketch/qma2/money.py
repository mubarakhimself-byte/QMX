"""The money rule: agents may read money, never move it.

Ported from QA/guards/money_path.py without langchain_core or qmx_broker imports.
This module is the single source of the money vocabulary: qmx_apps.supervisor
re-points its import here, and qmx_agents.guards.money_path becomes a re-export shim
until the old package is deleted.

It answers one question for every tool call on both engines, before hooks, modes,
rules or approvals are consulted:

    classify(call, catalog, surface) -> NotMoney | Proposal | MoneyAct

A `MoneyAct` is denied by `policy.evaluate` with DenySource.MONEY and never becomes an
approval, so no operator answer, agent answer, hook, rule or mode can unlock it.

What this is and is not (design.md, tension 1):
- REAL for the tool-call surface: every QMX tool, every MCP tool, every sub-agent call,
  on both engines, passes here (Claude via the in-code PreToolUse callback that every
  call reaches; OpenAI via QMX's own tool wrappers, the only tools that engine gets).
- SPEED BUMP for arbitrary code: `Bash(python -c "import keyring ...")` is caught only by
  the surface patterns below. A same-user process can read the OS keyring. The real
  guarantee against code is credential absence (broker creds on the trading node) or
  the optional `os_account` agent backend (unit U10).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from qma2.model import JsonValue, OperatorSecretRef, ToolCall


class MoneyAct(StrEnum):
    """Copied verbatim from MoneyPathAct + MoneyPathDeniedAct (one enum, same values)."""

    ORDER = "order"
    POSITION = "position"
    PROTECTION = "protection"
    SIZING = "sizing"
    BINDING = "binding"
    MODE = "mode"
    CONTROL = "control"
    ZONE_TRANSITION = "zone_transition"
    PROMOTION = "promotion"
    SUBMIT_ORDER = "submit_order"
    # ... the remaining MoneyPathDeniedAct members, unchanged


# ---------------------------------------------------------------- the exemption


@dataclass(frozen=True, slots=True)
class OrderProposal:
    """What an agent may produce: an unsigned proposal for the operator's Portfolio."""

    broker_id: str
    connection_id: str
    account_id: str
    symbol: str
    side: str  # "buy" | "sell"
    quantity: str  # decimal text, never float (copied validator)
    order_type: str = "market"
    limit_price: str = ""


@dataclass(frozen=True, slots=True)
class ProposalToolSpec:
    """The ONE tool allowed to carry money vocabulary. Exempt by identity, never by name.

    Instances exist only in `PROPOSAL_TOOLS` below. The Gate exempts a call only when
    (a) its source is ToolSource.QMX (the reserved `qmx` namespace that config refuses
    to any MCP server), and (b) `catalog.spec(call.name)` *is* one of these objects.
    A broker MCP server's own `propose_order` therefore stays refused (source=MCP).
    """

    name: str  # "propose_order"
    description: str
    input_schema: Mapping[str, JsonValue]


PROPOSAL_TOOLS: Final[tuple[ProposalToolSpec, ...]] = (
    # ProposalToolSpec(name="propose_order", description="Queue an unsigned order for the
    #   operator's Portfolio signature. Never sends an order.", input_schema=...),
)


# --------------------------------------------------------------- money surface


@dataclass(frozen=True, slots=True)
class MoneySurface:
    """Where money credentials and money state live, for the code-path speed bump.

    Derived, not hand-kept: credential labels come from the `brokers` settings section's
    `credential_ref`s plus the control token and operator key; state paths come from the
    broker/portfolio locations under QMX home. Rebuilt whenever settings change.
    """

    credential_labels: frozenset[OperatorSecretRef]
    credential_paths: frozenset[Path]  # incl. QMX's CLAUDE_CONFIG_DIR/.credentials.json
    state_paths: frozenset[Path]  # readable, never writable by agents

    @staticmethod
    def derive(qmx_home: Path, broker_refs: frozenset[OperatorSecretRef]) -> MoneySurface:
        raise NotImplementedError


# -------------------------------------------------------------------- classify


@dataclass(frozen=True, slots=True)
class NotMoney:
    pass


@dataclass(frozen=True, slots=True)
class Proposal:
    spec: ProposalToolSpec


@dataclass(frozen=True, slots=True)
class MoneyHit:
    act: str
    why: str  # "tool name token 'order'", "Bash reads keyring label qmx/ctrader/...", ...


type MoneyClass = NotMoney | Proposal | MoneyHit


class MoneyPathDenyError(ValueError):
    """Kept for qmx_apps (mini-app descriptor checks at install time)."""


def check_descriptor(name: str, metadata: Mapping[str, JsonValue]) -> None:
    """Verbatim port of money_path.check_descriptor (raises MoneyPathDenyError).
    qmx_apps.supervisor re-points here; `classify` reuses it for MCP and QMX tools."""
    raise NotImplementedError


class ToolCatalog:
    """What the control side knows about every tool it hands to a host: name -> spec and
    descriptor metadata (MCP annotations, `money_path` meta, parent surfaces).
    Built once per segment from ResolvedConfig + PROPOSAL_TOOLS + control ops."""

    def spec(self, name: str) -> ProposalToolSpec | None:
        raise NotImplementedError

    def descriptor(self, name: str) -> Mapping[str, JsonValue]:
        raise NotImplementedError


def classify(call: ToolCall, catalog: ToolCatalog, surface: MoneySurface) -> MoneyClass:
    """Pure. Runs on the original input and again on any hook- or operator-edited input.

    # TODO pseudocode
    # 1. if call.source is QMX and catalog.spec(call.name) in PROPOSAL_TOOLS (identity):
    #        return Proposal(spec)
    # 2. descriptor = catalog.descriptor(call.name)
    #    port check_descriptor(): money_path meta, parent surfaces, record_family,
    #    act/acts/name tokens, split on _ . : / and every suffix -> MoneyHit
    # 3. shell tools (Bash, PowerShell): for each sub-command of shell_split(command):
    #        keyring/credential CLIs (cmdkey, keyring, security find-*-password, secret-tool,
    #        Get-StoredCredential) naming a surface label  -> MoneyHit
    #        any path argument under surface.credential_paths -> MoneyHit
    #        write-ish command touching surface.state_paths  -> MoneyHit
    # 4. file tools: Read/Grep/Glob under credential_paths -> MoneyHit;
    #    Write/Edit/apply_patch under credential_paths or state_paths -> MoneyHit
    # 5. else NotMoney
    """
    raise NotImplementedError
