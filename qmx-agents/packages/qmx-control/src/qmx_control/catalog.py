"""The operation catalog (engine AD-61): every capability QMX exposes is one `OperationSpec` row.

The REST route, the model-facing tool and the engine node type all derive from the row. Control
operations declare their row with `@operation` on the `ControlService` method; broker, domain,
host and delegate rows are listed here, each bound by `binds` and `target` to the callable that
serves it. A row with `agent=False` is a REST or stdio door only and never reaches a model.

Wire names are `<toolset>_<op>`. `mcp__qmx__<name>` stays within `MAX_TOOL_NAME`, checked by
`check`. Probe P-NM measured 80 characters on the plan; 64 holds until another provider is probed.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal

from qmx_control.models import LibraryInput

if TYPE_CHECKING:
    from qmx_control.models import Document

type Approval = Literal["read", "domain_write", "manage", "propose_money"]
"""The harness `Effect` by value: READ runs, DOMAIN_WRITE follows `[agents] domain_write`,
MANAGE and PROPOSE_MONEY always ask."""
type Reversibility = Literal[
    "none", "reversible", "compensable", "irreversible", "irreversible_external"
]
type Binds = Literal["control_op", "domain_fn", "broker", "app_server", "agent_tool", "delegate"]
type Caller = Literal["model", "code"]
type Verb = Literal["GET", "POST", "PUT"]

CORE_TOOLSETS: Final = (
    "library",
    "workflows",
    "data",
    "backtest",
    "research",
    "node",
    "broker_read",
    "apps_admin",
    "memory",
    "context",
    "delegate",
    "settings_read",
    "ops",
)
CORE_PACK: Final = "qmx"
WIRE_NAME: Final = re.compile(r"[a-zA-Z0-9_-]+")
MAX_TOOL_NAME: Final = 64
"""The bound on `mcp__qmx__<name>`. A probe bound: the plan lane took 80 (P-NM)."""
INLINE_LIMIT: Final = 20_000
"""Characters an answer may carry before it spills to the Library (Claude's default)."""
SPILL_EDGE: Final = 2_000
"""Characters of a spilled answer's head and of its tail returned inline (Claude's default)."""

DEFAULT_REVERSIBILITY: Final[Mapping[Approval, Reversibility]] = MappingProxyType(
    {
        "read": "none",
        "domain_write": "compensable",
        "manage": "irreversible",
        "propose_money": "compensable",
    }
)


@dataclass(frozen=True)
class Rest:
    verb: Verb
    path: str


@dataclass(frozen=True)
class OperationSpec:
    toolset: str
    op: str
    binds: Binds
    target: str
    """The name of the method or function that serves the row."""
    approval: Approval
    description: str
    """First line: when to use it. Empty takes the bound callable's own description."""
    reversibility: Reversibility
    agent: bool = True
    left_out: str = ""
    """Why an `agent=False` row stays off every model's surface."""
    rest: Rest | None = None
    cursor: bool = False
    """The operation lists with `offset` and `limit`; a tool answer carries `next_offset`."""
    max_chars: int = INLINE_LIMIT
    forced: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    """Arguments a tool call always runs with, left out of the schema the model sees."""
    version: str = "1.0.0"
    owner: str = "core"
    defer: Literal["auto", "always_load"] = "auto"
    state: Literal["none", "instance"] = "none"

    @property
    def name(self) -> str:
        """The wire name, `<toolset>_<op>`."""
        return f"{self.toolset}_{self.op}"

    @property
    def id(self) -> str:
        """The catalog id and engine node type, `<pack>.<toolset>_<op>`."""
        return f"{CORE_PACK}.{self.name}"

    @property
    def callers(self) -> tuple[Caller, ...]:
        """Code never calls an operation that always asks."""
        if self.approval in ("manage", "propose_money"):
            return ("model",)
        return ("model", "code")


OPERATION: Final = "__qmx_operation__"


def operation[F: Callable[..., Any]](
    toolset: str,
    op: str,
    approval: Approval,
    *,
    rest: tuple[Verb, str] | None = None,
    agent: bool = True,
    left_out: str = "",
    reversibility: Reversibility | None = None,
    cursor: bool = False,
    forced: Mapping[str, object] | None = None,
) -> Callable[[F], F]:
    """Declare a `ControlService` method's row beside it. Its docstring's first line is the
    description."""

    def mark(method: F) -> F:
        doc = (method.__doc__ or "").strip()
        spec = OperationSpec(
            toolset=toolset,
            op=op,
            binds="control_op",
            target=method.__name__,
            approval=approval,
            description=doc.splitlines()[0] if doc else "",
            reversibility=reversibility or DEFAULT_REVERSIBILITY[approval],
            agent=agent,
            left_out=left_out,
            rest=None if rest is None else Rest(*rest),
            cursor=cursor,
            forced=MappingProxyType(dict(forced or {})),
        )
        setattr(method, OPERATION, spec)
        return method

    return mark


def _row(
    toolset: str,
    op: str,
    binds: Binds,
    target: str,
    approval: Approval,
    description: str = "",
    *,
    agent: bool = True,
    left_out: str = "",
    reversibility: Reversibility | None = None,
) -> OperationSpec:
    return OperationSpec(
        toolset=toolset,
        op=op,
        binds=binds,
        target=target,
        approval=approval,
        description=description,
        reversibility=reversibility or DEFAULT_REVERSIBILITY[approval],
        agent=agent,
        left_out=left_out,
    )


BROKER_ROWS: Final = (
    _row("broker_read", "accounts", "broker", "list_accounts", "read"),
    _row("broker_read", "account_state", "broker", "account_state", "read"),
    _row("broker_read", "positions", "broker", "positions", "read"),
    _row("broker_read", "quotes", "broker", "quotes", "read"),
    _row("broker_read", "symbol_info", "broker", "symbol_info", "read"),
    _row("broker_read", "bars", "broker", "bars", "read"),
    _row("node", "propose_order", "broker", "propose_order", "propose_money"),
)
"""`qmx_broker.server` tools by name. `propose_order` writes an unsigned proposal and always
asks; nothing in the catalog places, amends or cancels an order."""

DOMAIN_ROWS: Final = (
    _row("data", "instruments", "domain_fn", "list_instruments", "read"),
    _row("data", "bars", "domain_fn", "read_bars", "read"),
    _row("data", "features", "domain_fn", "read_features", "read"),
    _row("data", "calendar", "domain_fn", "calendar", "read"),
    _row("backtest", "run", "domain_fn", "run_backtest", "domain_write"),
    _row("backtest", "status", "domain_fn", "backtest_status", "read"),
    _row("backtest", "results", "domain_fn", "backtest_results", "read"),
    _row("backtest", "compare", "domain_fn", "compare_runs", "read"),
    _row("research", "qml_run", "domain_fn", "qml_run", "read"),
    _row("node", "state", "domain_fn", "node_state", "read"),
)
"""`qmx_tools.functions.domain_functions` by name. Its `library_search`, `library_save` and
`propose_order` stay stdio doors only: the library rows and the broker's `propose_order` serve
the same stores."""

HOST_ROWS: Final = (
    _row(
        "ops",
        "capacity",
        "agent_tool",
        "slot_table",
        "read",
        "Read the chat-slot table: how many chats may run, which hold a slot and which wait.",
    ),
    _row(
        "ops",
        "journal",
        "agent_tool",
        "journal",
        "read",
        "Read a chat's request journal: one row per model request with its usage and status.",
    ),
    _row(
        "ops",
        "heartbeats",
        "agent_tool",
        "heartbeats",
        "read",
        "Read what is running here and how loaded it is: the newest heartbeat per host and app "
        "(CPU, memory, capacity in use and waiting per class, the pause flag, the version) and "
        "the host's last ten rows.",
    ),
    _row(
        "delegate",
        "run",
        "delegate",
        "delegate",
        "domain_write",
        "Run a helper chat on another provider profile and return its final answer. The "
        "helper starts fresh: put the whole task in the prompt. It cannot start helpers.",
    ),
)
"""Rows the harness serves itself (the chat-slot table, the relay journal and `delegate`) and
`heartbeats`, which the host serves through the harness from its heartbeat log (AD-65)."""


def control_rows() -> tuple[OperationSpec, ...]:
    """Every `@operation` row on `ControlService`, in definition order."""
    from qmx_control.service import ControlService  # noqa: PLC0415

    return tuple(
        spec
        for member in vars(ControlService).values()
        if isinstance(spec := getattr(member, OPERATION, None), OperationSpec)
    )


def rows() -> tuple[OperationSpec, ...]:
    """The core catalog, checked."""
    found = (*control_rows(), *BROKER_ROWS, *DOMAIN_ROWS, *HOST_ROWS)
    check(found)
    return found


class CatalogError(ValueError):
    """Rows that cannot be served; the message names each problem."""


def name_problem(name: str) -> str | None:
    """Why a wire name cannot be registered, or None."""
    if not WIRE_NAME.fullmatch(name):
        return f"{name!r} must match ^[a-zA-Z0-9_-]+$"
    if len(f"mcp__qmx__{name}") > MAX_TOOL_NAME:
        return f"mcp__qmx__{name} is longer than {MAX_TOOL_NAME} characters"
    return None


def check(found: Iterable[OperationSpec]) -> None:
    """Refuse duplicate names, bad or long wire names, a core row outside the core toolsets, a
    left-out row with no reason, and `propose_money` anywhere but the broker's `propose_order`."""
    problems: list[str] = []
    seen: set[str] = set()
    for row in found:
        if row.name in seen:
            problems.append(f"{row.name} is declared twice")
        seen.add(row.name)
        if (problem := name_problem(row.name)) is not None:
            problems.append(problem)
        if row.owner == "core" and row.toolset not in CORE_TOOLSETS:
            problems.append(f"{row.name} names no core toolset ({row.toolset})")
        if not row.agent and not row.left_out:
            problems.append(f"{row.name} is left off the agent surface without a reason")
        if row.approval == "propose_money" and (row.binds, row.target) != (
            "broker",
            "propose_order",
        ):
            problems.append(f"{row.name} is not the broker's propose_order and cannot ask money")
    if problems:
        raise CatalogError("; ".join(problems))


def rest_routes(found: Iterable[OperationSpec]) -> list[tuple[OperationSpec, Rest]]:
    """Each row with a REST door, with its verb and path. A literal path segment sorts before a
    `{parameter}` at the same place, so `/api/apps/registry` is matched before `/api/apps/{id}`."""
    routes = [(row, row.rest) for row in found if row.rest is not None]
    return sorted(
        routes, key=lambda route: [part.startswith("{") for part in route[1].path.split("/")]
    )


def node_types(found: Iterable[OperationSpec]) -> Mapping[str, Reversibility]:
    """Engine node types `<pack>.<toolset>_<op>` with their reversibility, for every row code
    may call."""
    return MappingProxyType({row.id: row.reversibility for row in found if "code" in row.callers})


def spill(
    text: str,
    row: OperationSpec,
    save: Callable[[LibraryInput], Document],
    keep: Mapping[str, object] = MappingProxyType({}),
) -> str:
    """`text` when it fits `row.max_chars`; else the whole answer saved as a Library artifact
    (the control `library.db` until the Library store lands) and its head, tail and id, with
    `keep` (a list's cursor) beside them."""
    if len(text) <= row.max_chars:
        return text
    saved = save(
        LibraryInput(
            title=f"{row.name} answer",
            kind="artifact",
            content={"operation": row.id, "text": text},
            tags=["tool-answer", row.name],
        )
    )
    return json.dumps(
        {
            "spilled": True,
            "artifact_id": saved["id"],
            "chars": len(text),
            "head": text[:SPILL_EDGE],
            "tail": text[-SPILL_EDGE:],
            "next_step": f"call library_get with artifact_id {saved['id']} for the whole answer",
            **keep,
        }
    )
