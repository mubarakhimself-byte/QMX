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
from typing import TYPE_CHECKING, Any, Final, Literal, cast

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
APP_PREFIX: Final = "app:"
"""A pack's toolset is `app:<id>` (AD-61). The wire form of a toolset may not carry `:`, so it
becomes `_` where the CLI's tool name is built."""
CALL_DEPTH_SETTING: Final = "apps.call_depth"
"""The host setting that bounds a ring of asks (AD-64). There is no default number: a host that
sets none lets a ring run until the stuck detector sees it."""
WIRE_NAME: Final = re.compile(r"[a-zA-Z0-9_-]+")
MAX_TOOL_NAME: Final = 64
"""The bound on `mcp__qmx__<name>`. A probe bound: the plan lane took 80 (P-NM)."""
TOOLSET_WIRE: Final = re.compile(r"[^a-zA-Z0-9_-]")
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
    pack: str = CORE_PACK
    defer: Literal["auto", "always_load"] = "auto"
    state: Literal["none", "instance"] = "none"

    @property
    def name(self) -> str:
        """The catalog's name for the row, `<toolset>_<op>`."""
        return f"{self.toolset}_{self.op}"

    @property
    def wire(self) -> str:
        """The name the CLI's tool carries, `<toolset>_<op>` with the toolset's wire form. A pack's
        toolset is `app:<id>`, so its colon is an underscore here and only here."""
        return f"{TOOLSET_WIRE.sub('_', self.toolset)}_{self.op}"

    @property
    def id(self) -> str:
        """The catalog id and engine node type. A core row is `<pack>.<wire>`; a pack's row is
        `<pack>.<op>`, because the pack is already in the name."""
        if self.pack == CORE_PACK:
            return f"{self.pack}.{self.name}"
        return f"{self.pack}.{self.op}"

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
        "ops",
        "providers",
        "agent_tool",
        "provider_rows",
        "read",
        "Read the provider profiles and their model rows: wire, window, output limit, "
        "capabilities, class and first-token timeout. Keys show as keyring references only.",
    ),
    _row(
        "ops",
        "provider_test",
        "agent_tool",
        "provider_test",
        "domain_write",
        "Test one model row by its qmx_id with a one-token request through its stored key. A "
        "row whose key is missing spends nothing and says so.",
        reversibility="irreversible_external",
    ),
    _row(
        "library",
        "mark",
        "agent_tool",
        "mark",
        "manage",
        "Quarantine a Library item, or clear its quarantine, with a reason. Everything built on "
        "it shows the mark and its path, and triggers that pin it are refused until it clears.",
        reversibility="reversible",
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
"""Rows the harness serves itself (the chat-slot table, the relay journal and `delegate`), the
provider rows and their one-token Test from `qmx_router.registry` (a chat sees them only once
its host passes those two reads),
`heartbeats`, which the host serves through the harness from its heartbeat log (AD-65), and
`library_mark`, which the host serves from the Library store as the operator once he approves
(Library AD-22: only the operator marks)."""


CONTEXT_ROWS: Final = (
    _row(
        "context",
        "add",
        "agent_tool",
        "context_add",
        "domain_write",
        "Attach a reference to this chat so the model reads the object through its handle "
        "instead of pasted text. One grammar: @pod, @unit, @bot, @run, @app, @library and "
        "@session; @file, @folder, @url and @youtube arrive with REF2 and @memory with MEM. "
        "Not for pasting a document into the prompt.",
        reversibility="reversible",
    ),
    _row(
        "context",
        "list",
        "agent_tool",
        "context_list",
        "read",
        "List this chat's attached references as the Library reads them now: status ready, "
        "pending, archived or not_cached, and 'newer version exists' when a pinned item moved.",
    ),
    _row(
        "context",
        "refresh",
        "agent_tool",
        "context_refresh",
        "domain_write",
        "Re-resolve one attached reference: a following one moves to main's head, and a pinned "
        "one keeps its version and gains the note when main moved.",
        reversibility="reversible",
    ),
    _row(
        "context",
        "drop",
        "agent_tool",
        "context_drop",
        "domain_write",
        "Take one reference off this chat's attached list. The Library object itself is not "
        "touched.",
        reversibility="reversible",
    ),
    _row(
        "context",
        "read",
        "agent_tool",
        "context_read",
        "read",
        "Read more of one attached reference than its excerpt carried: the object's text, "
        "capped at the window's hard share, optionally one a-b character range.",
    ),
)
"""The `context` toolset (AD-63). Every row is served by the process that holds the Library,
which hands the harness one read per target for each chat (`Harness.context_reads`), because
attaching writes that chat's own record. A harness with no Library serves none of these rows."""


def control_rows() -> tuple[OperationSpec, ...]:
    """Every `@operation` row on `ControlService`, in definition order."""
    from qmx_control.service import ControlService  # noqa: PLC0415

    return tuple(
        spec
        for member in vars(ControlService).values()
        if isinstance(spec := getattr(member, OPERATION, None), OperationSpec)
    )


def app_toolset(app_id: str) -> str:
    """The toolset a pack's operations are served as: `app:<id>` (AD-61)."""
    return f"{APP_PREFIX}{app_id}"


def app_rows(
    app_id: str, version: str, operations: Mapping[str, Mapping[str, object]]
) -> tuple[OperationSpec, ...]:
    """One row per `[operations.<op>]` of one app, pinned to that app's `version`. Nothing else
    the app serves is a row: an app reaches another app only through these, which is the rule
    that there is no union of permissions across apps (AD-64, DC-7)."""
    found: list[OperationSpec] = []
    for op, declared in operations.items():
        approval = declared.get("approval", "read")
        if approval not in DEFAULT_REVERSIBILITY:
            raise CatalogError(f"{app_id} {op} declares no approval this catalog serves")
        found.append(
            OperationSpec(
                toolset=app_toolset(app_id),
                op=op,
                binds="app_server",
                target=op,
                approval=cast(Approval, approval),
                description=str(declared.get("description") or ""),
                reversibility=cast(
                    Reversibility, declared.get("reversibility") or DEFAULT_REVERSIBILITY[approval]
                ),
                version=version,
                owner=app_id,
                pack=app_id,
                state=cast(
                    Literal["none", "instance"],
                    declared.get("state") or "none",
                ),
            )
        )
    check(found)
    return tuple(found)


def dispatch_refusal(row: OperationSpec, *, depth: int, ceiling: int | None) -> str | None:
    """Why an ask at `depth` may not be dispatched, or None.

    Only a pack's operation carries the chain onward: a ring of apps asking each other (A asks B,
    B asks C, C asks A) is what the host's `call_depth` bounds, and the ceiling has no default
    number. A core row ends the chain, so it is never refused for depth."""
    if depth < 0:
        return "an ask's depth is never negative"
    if row.owner == "core" or ceiling is None:
        return None
    if depth > ceiling:
        return (
            f"{row.id} is asked at depth {depth}, past the host's call_depth {ceiling}; "
            f"the ring ends here"
        )
    return None


def rows(apps: Iterable[OperationSpec] = ()) -> tuple[OperationSpec, ...]:
    """The catalog: the core rows, then every enabled app's `[operations]` rows the caller hands
    in, all checked together."""
    found = (*control_rows(), *BROKER_ROWS, *DOMAIN_ROWS, *HOST_ROWS, *CONTEXT_ROWS, *apps)
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
        if (problem := name_problem(row.wire)) is not None:
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
