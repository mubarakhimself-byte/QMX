"""The door: the only way from the agent zone into the operator side.

One loopback ASGI app on its own port (default 8767), separate from the
operator API on 8766, with its own auth gate. Three routes:

  /zone/link             WebSocket. The zone runner's control channel. Handed to Harness.
  /zone/mcp              MCP over HTTP. The `qmx` tools. Every call is decided here.
  /zone/model/{profile}  Anthropic Messages relay for key providers and GPT. See relay.py.

Every request must carry the zone credential as a bearer. The gate compares
it in constant time against the copy in the operator keyring and never logs
the Authorization header, so a misrouted plan token would be dropped unread.

Invariants:
- The catalog is an explicit allow-list built at startup. It contains no op
  that answers approvals, starts operator turns, edits door policy, reads the
  operator token, or manages the zone.
- `DoorCatalog.build` runs the LangChain-free `check_descriptor` over every
  op name and metadata and refuses to start on a money-act match.
- Op args are parsed with the op's schema here. Handlers receive typed args.
- Results pass through `Redactor`, which removes every secret value the
  operator side read during the call.
- `X-QMX-Thread` is attribution, not identity. All zone sessions share the
  zone's rights, so a forged thread header gains nothing.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from qma_harness.model import (
    ApprovalId,
    DoorApproval,
    DoorDecision,
    DoorPolicy,
    Effect,
)
from qma_zone_wire import ThreadId

Handler = Callable[[Any], Awaitable[Any]]


@dataclass(frozen=True)
class DoorOp:
    """One `mcp__qmx__<name>` tool. Effect is required; there is no default."""

    name: str
    effect: Effect
    description: str
    input_schema: dict[str, Any]
    read_only_hint: bool
    handler: Handler


@dataclass(frozen=True)
class DoorCatalog:
    ops: dict[str, DoorOp]

    @staticmethod
    def build(ops: list[DoorOp]) -> "DoorCatalog":
        """Refuse duplicates, refuse any op whose name or metadata
        `check_descriptor` flags as a money act, refuse PROPOSE_MONEY on any op
        but the local proposal writer (by identity, not by name)."""
        raise NotImplementedError


def qmx_catalog(control: Any, broker: Any, domain: Any) -> list[DoorOp]:
    """The explicit list. Sources:
    - qmx_tools domain_functions (data, backtest, research, node): READ or DOMAIN_WRITE.
    - ControlService ops named in OPERATIONS that an agent may use, with
      destructiveHint ops as MANAGE.
    - BrokerService.list_accounts and the five reads: READ.
    - BrokerService.propose_order, the local writer: PROPOSE_MONEY.
    - ask_helper: start a helper thread on an allow-listed profile (MANAGE when
      the profile is a ChatGptPlan or KeyProvider with spend, else READ).
    """
    raise NotImplementedError


def args_digest(op: str, args: dict[str, Any]) -> str:
    """Pure. Canonical JSON (sorted keys, no floats re-rendered) then SHA-256."""
    raise NotImplementedError


def decide(op: DoorOp, digest: str, approvals: tuple[DoorApproval, ...],
           policy: DoorPolicy) -> DoorDecision:
    """Pure.

    READ -> Execute.
    DOMAIN_WRITE -> Execute if policy.domain_write == "allow", else as MANAGE.
    MANAGE, PROPOSE_MONEY -> Execute only if a Granted approval for (op, digest)
    exists (the door then marks it Consumed); else AwaitOperator with a new id,
    or Refuse if a matching approval was Denied.
    """
    raise NotImplementedError


class Redactor:
    """Collects secret values fetched from the keyring during one door call and
    replaces them in the result with `<redacted:qmx/...>`."""

    def note(self, ref: str, value: str) -> None:
        raise NotImplementedError

    def scrub(self, result: Any) -> Any:
        raise NotImplementedError


class Door:
    def __init__(self, catalog: DoorCatalog, policy: DoorPolicy, harness: Any,
                 relay: Any, zone_credential_ref: str) -> None:
        raise NotImplementedError

    def app(self) -> Any:
        """The ASGI app. Bound to 127.0.0.1 only."""
        raise NotImplementedError

    async def call(self, thread: ThreadId, op: str, raw_args: dict[str, Any]) -> Any:
        """Parse args, decide, and on AwaitOperator write a `permission` block
        into the thread and wait up to policy.approval_wait_seconds for the
        operator. Executes operator-side with operator rights. Returns the
        redacted result, or a refusal text that names the rule."""
        raise NotImplementedError

    async def wait_for(self, approval: ApprovalId, seconds: int) -> DoorApproval:
        raise NotImplementedError
