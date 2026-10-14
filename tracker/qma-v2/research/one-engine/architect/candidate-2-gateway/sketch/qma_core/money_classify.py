"""The one money classifier. Pure, LangChain-free, no I/O.

Lives in `qma.core.barriers` next to `money_path.py`, the deny-list source of truth
(HOW "Keep" row). It absorbs a LangChain-free `check_descriptor` (HOW Gotcha 1 and
11), so `qmx_agents.guards.money_path` has no reason left to exist and both old
copies collapse into one.

Called from three places, all with the same function:
- build time: `qmx_harness` refuses to start if any registry tool descriptor hits;
- the gateway wire gate (`qma_gateway.tap`): model-proposed tool_use, every lane;
- the CLI-side PreToolUse callback (`qmx_harness.engine`): final input, every mode.
`qmx_apps.supervisor` retargets its `check_descriptor` import here.

What it proves and what it does not:
- REAL for tool calls: QMX tools, MCP tools, built-ins, from any agent and any
  provider.
- A SPEED BUMP for code that Bash runs as the operator's OS user. A same-user
  process can read the OS keyring. Shell patterns (keyring CLIs naming qmx/*
  labels, broker hosts, credential paths) are caught; obfuscated code is not.
  The structural guarantee stays where it is today: `BrokerService` has `read` and
  `propose_order` only, and `propose_order` opens no broker connection.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ToolCall:
    name: str  # "Bash", "mcp__qmx__positions", "mcp__broker__place_order", ...
    input: Mapping[str, object]
    agent: str | None


@dataclass(frozen=True, slots=True)
class NotMoney:
    pass


@dataclass(frozen=True, slots=True)
class Proposal:
    """`mcp__qmx__propose_order`, matched by exact name inside the reserved `qmx`
    server, whose registry entry is the proposal writer by identity. A broker MCP
    server's own `propose_order` is a MoneyHit. The harness always asks the
    operator before a Proposal runs."""

    tool: str


@dataclass(frozen=True, slots=True)
class MoneyHit:
    act: str  # a MoneyPathDeniedAct value, e.g. "submit_order"
    why: str  # "tool name token 'order'", "Bash reads keyring label qmx/ctrader/live", ...


type MoneyVerdict = NotMoney | Proposal | MoneyHit


class Catalog(Protocol):
    """Satisfied by `qma_gateway.contract.ToolCatalogSnapshot`."""

    descriptors: Mapping[str, Mapping[str, object]]
    proposal_tools: frozenset[str]
    credential_labels: frozenset[str]
    protected_paths: frozenset[str]


def check_descriptor(name: str, metadata: Mapping[str, object]) -> MoneyHit | None:
    """LangChain-free port of `qmx_agents.guards.money_path.check_descriptor`:
    money_path meta, parent surfaces, act tokens, name split on _ . : / with every
    suffix tested against `qma.core.barriers.money_path`."""
    raise NotImplementedError


def classify(call: ToolCall, catalog: Catalog) -> MoneyVerdict:
    """Pure. Same answer at the wire and in the hook for the same (name, input).

    # TODO pseudocode
    # 1. call.name in catalog.proposal_tools -> Proposal
    # 2. hit = check_descriptor(call.name, catalog.descriptors.get(call.name, {}))
    #    -> MoneyHit
    # 3. Bash / PowerShell: split compound commands; keyring CLIs (cmdkey, keyring,
    #    security find-*-password, secret-tool, Get-StoredCredential) naming a qmx/*
    #    label, broker hosts, credential paths, writes under money state paths
    #    -> MoneyHit
    # 4. Read / Grep / Glob under credential paths; Write / Edit / NotebookEdit under
    #    credential or money state paths (incl. QMX's CLAUDE_CONFIG_DIR settings.json
    #    and .credentials.json, CO-8) -> MoneyHit
    # 5. else NotMoney
    """
    raise NotImplementedError
