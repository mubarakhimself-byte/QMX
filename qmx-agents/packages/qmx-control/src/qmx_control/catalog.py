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
type Binds = Literal[
    "control_op",
    "domain_fn",
    "broker",
    "app_server",
    "agent_tool",
    "delegate",
    "primary_op",
    "lab_op",
]
"""`primary_op` is `qmx_control.primary`: the primary store's own operations, served at the host's
user door and on no model's surface (migration step 8, "When the server is lost"). `lab_op` is
`qmx_control.lab`: the Lab's own operations, served the same way for its screens (Lab AD-19)."""
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
    "router",
    "lab",
    "unit",
    "blocks",
    "instrument",
    "readings",
)
CORE_PACK: Final = "qmx"
APP_PREFIX: Final = "app:"
"""A pack's toolset is `app:<id>` (AD-61). The wire form of a toolset may not carry `:`, so it
becomes `_` where the CLI's tool name is built."""
OBSERVER_TOOLSETS: Final[frozenset[str]] = frozenset({"ops"})
"""The toolset an observer token lists (engine AD-69, HARNESS-REQUESTS H61): the `ops` rows, reads
only. The rule is a toolset and an approval, not a path list, so a `broker_read` row and a Library
content row are refused by construction rather than by a list that drifts."""
OBSERVER_WRITES: Final[frozenset[str]] = frozenset({"ops_note"})
"""The one write an observer may make: the diagnosis note, on the observer's own ref. Every other
`domain_write`, `manage` and `propose_money` row is refused, so an outside agent still only looks
and leaves one note (AD-69)."""
OBSERVER_PATHS: Final[tuple[str, ...]] = ("/api/doctor",)
"""The one route an observer reads that is no catalog row: the harness's doctor page."""
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
    _row(
        "broker_read",
        "account_state",
        "broker",
        "account_state",
        "read",
        "Read one account's balances and leverage. The answer's `environment` says demo or live: a"
        " demo balance is not real money, so say demo beside any demo figure you report.",
    ),
    _row(
        "broker_read",
        "positions",
        "broker",
        "positions",
        "read",
        "Read one account's open positions or spot holdings. The answer's `environment` says demo"
        " or live: demo positions hold no real money, so say demo beside them.",
    ),
    _row(
        "broker_read",
        "quotes",
        "broker",
        "quotes",
        "read",
        "Read a timestamped bid/ask quote for an account symbol. The answer's `environment` says"
        " demo or live: a demo server's prices can differ from live ones.",
    ),
    _row(
        "broker_read",
        "symbol_info",
        "broker",
        "symbol_info",
        "read",
        "Read an account symbol's precision and limits; they grant no order authority. The"
        " answer's `environment` says demo or live.",
    ),
    _row(
        "broker_read",
        "bars",
        "broker",
        "bars",
        "read",
        "Read every bar of an account symbol within explicit UTC millisecond bounds; pass `limit`"
        " to stop early. The answer's `environment` says demo or live: a demo server's bars can"
        " differ from live ones.",
    ),
    _row("node", "propose_order", "broker", "propose_order", "propose_money"),
)
"""`qmx_broker.server` tools by name. Every account read's answer is stamped demo or live, and its
description says so, because a demo figure is never real money. `propose_order` writes an unsigned
proposal and always asks; nothing in the catalog places, amends or cancels an order."""

DOMAIN_ROWS: Final = (
    _row("data", "instruments", "domain_fn", "list_instruments", "read"),
    _row("data", "bars", "domain_fn", "read_bars", "read"),
    _row("data", "features", "domain_fn", "read_features", "read"),
    _row("data", "calendar", "domain_fn", "calendar", "read"),
    _row(
        "backtest",
        "run",
        "domain_fn",
        "backtest_run",
        "domain_write",
        "Backtest a unit on QMB, the first tester app, over a window, and land its one "
        "`backtest-result` in his Library: trades in money and R, with who ran it. The core "
        "counts the try and runs the unit's behaviour check first when it has none. Answers the "
        "run id, and the result id when the run finished within `[qmb] agent_wait_s`.",
    ),
    _row(
        "backtest",
        "status",
        "domain_fn",
        "backtest_status",
        "read",
        "Read a run's state from its try rows (running, landed, failed), its tester and its "
        "result id.",
    ),
    _row(
        "backtest",
        "results",
        "domain_fn",
        "backtest_results",
        "read",
        "Read a landed `backtest-result` by its result id: status, measures in money and R, "
        "labels, and a page of trades.",
    ),
    _row(
        "backtest",
        "compare",
        "domain_fn",
        "backtest_compare",
        "read",
        "Compare two landed `backtest-result`s by result id: measures that differ, and trades "
        "found in one only or differing.",
    ),
    _row(
        "backtest",
        "judge_run",
        "domain_fn",
        "backtest_judge_run",
        "domain_write",
        "Judge landed `backtest-result`s by result id with the core's referee, under a study "
        "spec (or the results' own, or a quick one). Every market is judged by one rule, shrunk "
        "toward the unit's whole result, and deflated by the family's effective tries. Lands the "
        "verdict and its cards and answers it in plain words with the tries behind it. Scripts "
        "decide; it never publishes or promotes a unit.",
    ),
    _row("research", "qml_run", "domain_fn", "qml_run", "read"),
    _row(
        "research",
        "journal_query",
        "domain_fn",
        "journal_query",
        "read",
        "Read a journal (unit, market or node) over a required time window, filtered by"
        " envelope fields such as unit_id, market_id, kind or world. Reading history is read"
        " with readings_query. The `trades_with_context`"
        " view puts each decision and trade beside its market's minute, spread included, which"
        " answers why a unit did or did not trade; `digest` counts per unit, market and day. Past"
        " the data it says where the data stops. Reads only.",
    ),
    _row(
        "research",
        "notes_write",
        "domain_fn",
        "notes_write",
        "domain_write",
        "Write an analysis as a Library note, with a receipt for every number and the journal"
        " rows or items it is about. The only thing an agent writes from journals: never a trade,"
        " a journal row, a unit move or an order.",
    ),
    _row(
        "node",
        "state",
        "domain_fn",
        "node_state",
        "read",
        "Read the trading node's state: its lifecycle, its units' counts and its last broker"
        " contact. Reads only; when no trading node is set up yet the answer says so.",
    ),
    _row(
        "node",
        "units",
        "domain_fn",
        "node_units",
        "read",
        "Read the trading node's units: each deployment's state. Pass `deployment_id` for one."
        " Reads only.",
    ),
    _row(
        "node",
        "positions",
        "domain_fn",
        "node_positions",
        "read",
        "Read the trading node's open positions with their owner tags and protection. Pass"
        " `account` for one account. Reads only.",
    ),
    _row(
        "node",
        "journal_tail",
        "domain_fn",
        "node_journal_tail",
        "read",
        "Read the trading node's journal rows after `after_sequence`, and the next sequence to"
        " ask from. Pass `streams` to narrow. Reads only.",
    ),
    _row(
        "node",
        "passport",
        "domain_fn",
        "node_passport",
        "read",
        "Read the trading node's passport: its identity, versions, clock and venue round trips."
        " Reads only.",
    ),
    _row(
        "unit",
        "new",
        "domain_fn",
        "unit_new",
        "domain_write",
        "Start a new trading unit from a template, the dummy trend pullback by default, with"
        " `overrides` set by JSON pointer. It saves the document as a new unit draft in his"
        " Library and returns its `item`; nothing is published, tested or traded.",
    ),
    _row(
        "unit",
        "check",
        "domain_fn",
        "unit_check",
        "domain_write",
        "Check a unit document at layers A to F and get every problem at once, each with where"
        " it is and a hint. Pass `item` to save the document as that unit's draft first, and"
        " `previous_problem_set` to learn `no_progress`. Fix every error and check again.",
    ),
    _row(
        "unit",
        "explain",
        "domain_fn",
        "unit_explain",
        "read",
        "Explain a unit in plain lines: what it trades, its slots and blocks, its exits, sizer"
        " and numbers, and its check counts. Pass a `document` or a unit draft's `item`.",
    ),
    _row(
        "blocks",
        "find",
        "domain_fn",
        "blocks_find",
        "read",
        "Search the dictionary before you write a block: one line per entry with its pin, type,"
        " output, data level and status, best match first. Narrow by `role`, `data_level` or"
        " `market_class`.",
    ),
    _row(
        "blocks",
        "get",
        "domain_fn",
        "blocks_get",
        "read",
        "Read one dictionary entry in full: its trader words, machine spec, code and status."
        " The newest version unless you name one.",
    ),
    _row(
        "blocks",
        "check",
        "domain_fn",
        "blocks_check",
        "read",
        "Check a new entry and its block source before saving it: every problem at once, the"
        " status it would earn, what the next status lacks, and the fingerprint of the source.",
    ),
    _row(
        "blocks",
        "match",
        "domain_fn",
        "blocks_match",
        "read",
        "Match each sentence of a source to the dictionary entry it states. A sentence no entry"
        " covers comes back as an append request; never invent an entry for it silently.",
    ),
    _row(
        "instrument",
        "get",
        "domain_fn",
        "instrument_get",
        "read",
        "Read the facts of one instrument record (contract size, pip, digits, lots, calendar,"
        " funding, leverage, data levels, status) as they stood at an instant, `at`, now by"
        " default. Name it by `venue` and `symbol`, or by `market_id` when one venue holds it;"
        " `version` reads one version. Answers the record with its id, version and fingerprint.",
    ),
    _row(
        "readings",
        "query",
        "domain_fn",
        "readings_query",
        "read",
        "Read what a reading (an MIS or node market state such as the volatility state) said"
        " over a required time window, the open month included, narrowed by markets, tier,"
        " source and version. Each row carries its value or word, its health and when it was"
        " computed. Continue with `cursor`; `data_ends_at` says where the recorded data stops."
        " The only way to read reading history. Reads only.",
    ),
)
"""`qmx_tools.functions.domain_functions` by name. Its `library_search`, `library_save` and
`propose_order` stay stdio doors only: the library rows and the broker's `propose_order` serve
the same stores. The `unit` rows write unit drafts and nothing else: no row here publishes,
promotes, deploys or sends an order (Part A AD-117)."""

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
        "Start a helper chat on another provider profile and return its handle at once, so you "
        "keep working while it runs. The helper starts fresh: put the whole task in `task`. Its "
        "answer arrives as a report between your turns; `delegate_list` shows it, "
        "`delegate_steer` adds a note to it and `delegate_stop` ends it.",
        reversibility="reversible",
    ),
    _row(
        "delegate",
        "list",
        "delegate",
        "delegate_list",
        "read",
        "List this chat's helpers and where each one is: queued, running, done, failed, stalled "
        "or unknown, with its elapsed time and where it last moved. Read it before steering or "
        "stopping one.",
    ),
    _row(
        "delegate",
        "steer",
        "delegate",
        "delegate_steer",
        "domain_write",
        "Add a note to a running helper's next checkpoint, to correct where it is going without "
        "starting again. The helper's report says whether the note arrived.",
        reversibility="reversible",
    ),
    _row(
        "delegate",
        "stop",
        "delegate",
        "delegate_stop",
        "domain_write",
        "End one helper now and say why. Its work stops and its report says stopped. Use it for "
        "a helper that is no longer worth running.",
        reversibility="compensable",
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


MEMORY_ROWS: Final = (
    _row(
        "memory",
        "recall",
        "agent_tool",
        "memory_recall",
        "read",
        "Recall what was learnt before: the rows that answer a question, each with its tag and "
        "the Library objects it cites. Read this before rebuilding something or repeating a dead "
        "end. A row outside its validity window is not returned unless you ask as of a date.",
    ),
    _row(
        "memory",
        "note",
        "agent_tool",
        "memory_note",
        "domain_write",
        "Write one memory row so a later chat or run finds it: a lesson, a dead end, a procedure "
        "or a preference, with the objects it is about in `refs`. Use it for what is worth "
        "keeping, not for narration.",
        reversibility="reversible",
    ),
    _row(
        "memory",
        "check",
        "agent_tool",
        "memory_check",
        "read",
        "Check an intent key before building: whether it was already built (and what to link), "
        "and whether it is a known dead end. Exact, no model, no spend.",
    ),
    _row(
        "memory",
        "forget",
        "agent_tool",
        "memory_forget",
        "manage",
        "Forget rows for good: each row's Library item is archived and the row leaves every "
        "index, so neither a recall nor a rebuild brings it back. Give the row ids recall "
        "returned. This is the operator's act on his own memory.",
        reversibility="irreversible",
    ),
    _row(
        "memory",
        "rebuild",
        "agent_tool",
        "memory_rebuild",
        "manage",
        "Re-index the memory rows from the Library, for one scope or every scope. What the "
        "index lost comes back; what was forgotten stays forgotten.",
        reversibility="reversible",
    ),
)
"""The `memory` toolset (AD-18, AD-27). The host serves these rows from the engine it installed
(`HO/host.py`), so a harness with no memory engine serves none of them. `forget` archives, which
is why it asks: memory is the operator's record, not a chat's scratch space."""


ROUTER_ROWS: Final = (
    _row(
        "router",
        "accounts",
        "agent_tool",
        "accounts",
        "read",
        "Read the account pool: each account's provider, state, live leases, last reading and "
        "the models it is cooling for. No key is ever shown; a secret is a keyring name.",
    ),
    _row(
        "router",
        "llm_complete",
        "agent_tool",
        "llm_complete",
        "domain_write",
        "Ask one model for one answer through the router with no CLI process: a role or a model "
        "id, the messages, and an optional JSON schema the answer must hold to. A plan row is "
        "refused, because only the CLI holds that sign-in.",
        reversibility="reversible",
    ),
)
"""The account pool and the one-shot model call (AD-56, AD-12, AD-19). `llm_complete(role)` is
what a mini app or a workflow asks for a model call: the router leases an account, normalises,
classifies and journals the request, and no key ever reaches the app."""


INSTANCE_ROWS: Final = (
    OperationSpec(
        toolset="apps_admin",
        op="move",
        binds="app_server",
        target="move",
        approval="manage",
        description=(
            "Move one app instance to another machine: snapshot its volume, restore it there, "
            "flip its home and hand the volume lease over, so its next run happens on the "
            "machine it moved to."
        ),
        reversibility="irreversible",
        state="instance",
    ),
)
"""The move (AD-64). It is served against the app's own volume by the apps supervisor's
`snapshot_instance` and `restore_instance`, which is why it binds to the app server and not to a
control method: the snapshot, the restore, the home flip and the lease handover are one act on one
volume. A caller reaches it as `apps_admin_move`, `MANAGE` because a move takes the instance away
from the machine that had it."""


PRIMARY_ROWS: Final = (
    _row(
        "library",
        "move",
        "primary_op",
        "press",
        "manage",
        "Move the Library to the server: say so, pause saves, push until the PC and the server "
        "agree, then wait for his click. Nothing moves until he presses the card.",
        agent=False,
        left_out="it moves the one record of which store is primary, so only his click asks it",
        reversibility="compensable",
    ),
    _row(
        "library",
        "server_lost",
        "primary_op",
        "server_lost",
        "manage",
        "Run the procedure for a server that is gone: promote the PC, list the refs that may be "
        "behind, name what has one copy only, then rebuild and re-pair when he is ready.",
        agent=False,
        left_out="it promotes the PC, which raises the epoch; an agent never promotes a store",
        reversibility="compensable",
    ),
)
"""The primary store's two operations (migration step 8 and "When the server is lost"; DATA-PLAN
DR2D). Both are the operator's, so neither is on any model's surface: `qmx_control.primary` serves
them at the host's user door, which is the same `user` the inbox answers as."""


LAB_ROWS: Final = (
    _row(
        "lab",
        "levels",
        "lab_op",
        "levels",
        "read",
        "List the Lab's four levels and the templates each offers: the published ones tagged for "
        "the level first, then the pack's own. A level is a filter, not a kind.",
        agent=False,
        left_out="its screens ask it; the copilot's Lab pack is a later slice (Lab AD-14)",
    ),
    _row(
        "lab",
        "new",
        "lab_op",
        "new",
        "domain_write",
        "Create a project as a collection and install its template at one level: quick idea, "
        "experiment, study or campaign. The template is published and tagged with the level, and "
        "the new project gets an empty workspace annotation.",
        agent=False,
        left_out="opening a project is the operator's act on his own Lab (Lab AD-19)",
        reversibility="compensable",
    ),
    _row(
        "lab",
        "open",
        "lab_op",
        "open",
        "read",
        "Open one project: its members as cards, its workspace state, its problems (marks and "
        "merge conflicts) and its timeline (the item's moves in the ref log).",
        agent=False,
        left_out="its screens ask it; the copilot's Lab pack is a later slice (Lab AD-14)",
    ),
    _row(
        "lab",
        "workspace",
        "lab_op",
        "workspace",
        "domain_write",
        "Save the workspace state onto the project: which member is open, the pins, the layout "
        "and the open tabs. It is an annotation, so reopening the Lab restores it and no version "
        "is minted.",
        agent=False,
        left_out="the layout is his screen's state, and no model arranges his workspace",
        reversibility="reversible",
    ),
    _row(
        "lab",
        "panel",
        "lab_op",
        "panel",
        "read",
        "Read one dataset card's data panel: its months and quality off the card and one month's "
        "sample through the market-data door. A sealed month is refused in the door's own words.",
        agent=False,
        left_out="agents read price data through the data tools, not the Lab's panel (Lib AD-28)",
    ),
    _row(
        "lab",
        "training",
        "lab_op",
        "training",
        "domain_write",
        "Place a training run on the PC: check the live free disk against the partitions it must "
        "fetch, refuse with both sizes when they do not fit, then materialise exactly those "
        "partitions and answer the lineage the model will record.",
        agent=False,
        left_out="a training run is a placement the Lab holds a GPU slot for, not a tool call",
        reversibility="reversible",
    ),
    _row(
        "lab",
        "model",
        "lab_op",
        "model",
        "domain_write",
        "Land the model a training run made: its data fingerprints, code version, seed, framework "
        "and hardware, its weights blob, and its edges consumed to the card and derived-from its "
        "code.",
        agent=False,
        left_out="the run that trained it lands it; nothing else writes a model item",
        reversibility="compensable",
    ),
)
"""The Lab backend's operations (Lab AD-19, AD-20; DATA-PLAN DR13). `qmx_control.lab` serves them at
the host's user door for the Lab's screens, which are the UI session's; pods are not among them."""


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
        approval = str(declared.get("approval", "read"))
        if approval not in DEFAULT_REVERSIBILITY:
            raise CatalogError(f"{app_id} {op} declares no approval this catalog serves")
        served = cast(Approval, approval)
        found.append(
            OperationSpec(
                toolset=app_toolset(app_id),
                op=op,
                binds="app_server",
                target=op,
                approval=served,
                description=str(declared.get("description") or ""),
                reversibility=cast(
                    Reversibility, declared.get("reversibility") or DEFAULT_REVERSIBILITY[served]
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
    found = (
        *control_rows(),
        *BROKER_ROWS,
        *DOMAIN_ROWS,
        *HOST_ROWS,
        *CONTEXT_ROWS,
        *MEMORY_ROWS,
        *ROUTER_ROWS,
        *INSTANCE_ROWS,
        *PRIMARY_ROWS,
        *LAB_ROWS,
        *apps,
    )
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
    `keep` (a list's cursor, a broker read's demo-or-live stamp) beside them."""
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
