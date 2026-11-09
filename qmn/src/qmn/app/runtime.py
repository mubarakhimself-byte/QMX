"""The trading node's runtime: the thread that keeps the node returning to what he asked for.

Part C AD-301, AD-308, AD-309, AD-317; Level 0 AD-5, AD-38, AD-39. Operation handlers write
``desired`` and wake this thread; it never answers a caller. On every wake and every
``RECONCILE_TICK_S`` it folds ``desired`` into the target and acts in a fixed order: the kill
switch first, then deployments, then each venue's feed and the units it drives. What it saw goes
to ``observed``, which the reads answer from.

A deployment's files were staged into ``data/deployments/<deployment_id>/in/`` by the node link
before ``deploy`` was asked, and ``deploy`` checked each one's fingerprint before it answered.
The runtime compiles the unit on a worker thread after that answer, through QML's one compiler
and block loader, and refuses to trade it when the compiled fingerprint differs from the one
its G record holds. The unit then warms up from the node's own recording of each market and
trades nothing until its warm-up is complete.

A unit is hosted through QML's ``construct_unit`` and driven through the one shared unit
handler QMB drives (``qmb/src/qmb/host/unit_handler.py``), by the node's own loop driver over
QMB's ``run_slice``. :class:`NodeUnit` wraps the handler for the node:

- each order the unit mints is sent at once through :class:`OrderPath`: local guards, the
  cross-unit hook (a placeholder that passes every order), the protection gate, the journal
  before dispatch, the venue;
- a slice that is driven again never sends an order or applies a fill a second time;
- each position is named by its entry's client order id, ``q<node tag>-<ULID>``, unique on the
  node and stable across a re-run, in the unit journal and at the venue;
- the trades the unit reads back from its own journal carry the deployment's lane as their
  world, never ``replay``;
- a stop amendment that would widen the stop is refused before it reaches the venue.

A paper deployment takes the same order path and ends at its paper account beside the binding,
which sends nothing to the venue (``paper_lane.py``). Every entry also passes the stand-down
table (``stand_down.py``); exits, broker stops and the kill switch never do.

Protection follows the venue's rule: on cTrader the stop rides on the entry order as a distance.
If the venue does not hold it after ``PROTECT_RETRY_MAX`` tries of ``PROTECT_CONFIRM_NS`` each,
the node closes that position reduce-only and raises the protection alarm, a labelled placeholder
for the risk session (``RISK-SIZING-PLACEHOLDERS.md`` row 19).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import threading
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from fractions import Fraction
from pathlib import Path
from typing import Final, Protocol, cast

from qmb.host.replay import BarWindow, window_size
from qmb.host.unit_handler import (
    Fill,
    FillKind,
    HeldPosition,
    JournalRecord,
    Reached,
    Skip,
    UnitSliceHandler,
    UnitTrade,
)
from qmb.results.journal import RunJournal
from qmb.runloop import DeclaredStream, RestingIntent, SliceObservation, StreamSet
from qmf.core import (
    Account,
    AccountRole,
    Duration,
    Instant,
    Instrument,
    MonotonicReading,
    Ok,
    Price,
    PriceDelta,
    Quantity,
    Result,
    SinkAck,
    SinkResult,
    TypedRefusal,
    VenueId,
    World,
    WriterId,
    is_refusal,
)
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.data.journal_writer import JournalWriter, WriterScope
from qmf.risk.facts import AccountFacts, Stake, account_name
from qmf.risk.journal import UNIT_FAULT, RiskEvent
from qmf.risk.paper import ExecutionTarget
from qmf.risk.unit_intent import (
    AmendProtection,
    ClosePartial,
    UnitExitIntent,
    check_amendment_tightens,
    parse_unit_intent,
)
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.feed import roll_up
from qml.motion import ClosedTrade
from qml.numbers import InstrumentRecord, lots, parse_record
from qml.protocol.unit import (
    ACCOUNT_CURRENCY,
    DecisionRow,
    FaultPhase,
    HostedUnit,
    HostPort,
    OwnPosition,
    QuoteBar,
    RatePort,
    Surface,
    construct_unit,
    rate_used,
    restore_unit,
)
from qml.protocol.unit import (
    Account as UnitAccount,
)
from qml.unit.model import Side

from qmn.app import paper_lane
from qmn.app.attribution import OrderState, ReadBack, VenueOrder, VenuePosition
from qmn.app.facts import FeedRates, LiveAccount
from qmn.app.facts import refs as rate_refs
from qmn.app.feed_keeper import Bar, FeedKeeper
from qmn.app.healing import Healer, StuckWatch
from qmn.app.operations import Answer, Context, Target, cleared_by, refused, same_market
from qmn.app.reconciler import Found, Ours, Reconciler, journal_sends
from qmn.app.stand_down import (
    REPEATED_FAULT_RESTARTS,
    REPEATED_FAULT_WINDOW_NS,
    Kind,
    StandDowns,
    Subject,
    restored,
)
from qmn.app.store import Change, Json, Outcome
from qmn.journal_dispatch import enact_command
from qmn.loop.accumulator import RecordingAccumulator
from qmn.loop.driver import CommandStreamLoop
from qmn.order.protection import require_venue_resident_protective_stop
from qmn.protection.effect_matrix import PLACEHOLDER_KILL_EFFECTS, KillEffect
from qmn.protection.ksa import LEVEL_RANK, KsaLevel
from qmn.venue import (
    CloseScope,
    Command,
    ConformanceDouble,
    OrderParameters,
    OrderTags,
    OrderType,
    ProtectionAmendment,
    ProtectionSide,
    SubmissionOutcome,
    TimeInForce,
    order_tags,
    submit_not_ready_refusal,
)

__all__ = [
    "BUDGET_SHARE",
    "CLOSE_REFUSALS_ALARM",
    "PROTECT_CONFIRM_NS",
    "PROTECT_RETRY_MAX",
    "RECONCILE_TICK_S",
    "ConformanceAccount",
    "Deployment",
    "NodeUnit",
    "OrderPath",
    "Runtime",
    "Sent",
    "Ticket",
    "Unknown",
    "Unprotected",
    "Venue",
    "VenueAccount",
    "VenueClose",
    "deploy_preflight",
    "parse_deployment",
]

RECONCILE_TICK_S: Final = 0.2
"""`[node] reconcile_tick_ms`, starting at 200 (NODE.md section 9)."""
BUDGET_SHARE: Final[Decimal] = Decimal(1)
"""`[node] budget_share`, starting at 1: the share of one account a deployment may keep at risk.
At 1 a deployment may use the whole account, so only a share above that (a bug, not a choice) is
not a budget. Labelled placeholder, owner numbers talk; a deployment document names none yet, so
every deployment starts from this one. Range: above zero, at most one."""
HOST_FACTS: Final = Path("road") / "host" / "facts.json"
"""The host's facts in the node's volume (C-05c, AD-307): the machine, the trading profile, the
holdout, and the newest clock probe."""
CLOCK_FACT_STALE_NS: Final = 180_000_000_000
"""`[node] clock_fact_stale_s`, starting at 180 s: three missed host probes, after which the
clock's offset is unproven and reads None."""
PROTECT_CONFIRM_NS: Final = 2_000_000_000
"""`[node] protect_confirm_ms`, starting at 2,000: how long one try waits for the venue to show
the stop. A labelled placeholder for the risk session."""
PROTECT_RETRY_MAX: Final = 3
"""`[node] protect_retry_max`, starting at 3 tries. A labelled placeholder for the risk session."""
CLOSE_REFUSALS_ALARM: Final = 3
"""`[node] close_refusals_alarm`, starting at 3: refused closes of one position before the node
raises the protection alarm. It keeps closing after the alarm. A labelled placeholder for the
risk session."""
PROTECT_POLL_S: Final = 0.05
MAX_SLICE_LATENCY_NS: Final = 500_000_000
"""`[node] max_slice_latency`, starting at 500 ms (research 31 section 3.3)."""
ACCUMULATOR_BOUND: Final = 10_000
"""`[node] accumulator_bound`, one session of bars per stream (NODE.md section 9)."""
DEPLOYMENT_SCHEMA: Final = "qmx.node.deployment/1"
ROLE: Final = "node"
_ULID_ALPHABET: Final = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
LANES: Final = frozenset({"paper", "live"})


# --- the deployment document ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StagedFile:
    entry_id: str
    version: int
    fingerprint: str
    path: str
    kind: str
    size: int


@dataclass(frozen=True, slots=True)
class Deployment:
    """A ``qmx.node.deployment/1`` document, parsed (Part C CONTRACTS section 3)."""

    deployment_id: str
    node_tag: str
    unit_id: str
    unit_document: Mapping[str, object]
    compiled_fingerprint: str
    logic_fingerprint: str
    """The unit version's logic half. Empty on a document written before the split."""
    risk_fingerprint: str
    """The unit version's risk half. Empty on a document written before the split."""
    g_fingerprint: str
    """The compiled fingerprint the G record names, which is the one the check ran against."""
    g_logic_fingerprint: str
    """The logic fingerprint the G record names. Empty on a document written before the split."""
    files: tuple[StagedFile, ...]
    account_id: str
    snapshots: tuple[Mapping[str, object], ...]
    lane: str
    markets: tuple[str, ...] = ()
    """The unit's markets he chose. Only these get bars, so only these ever trade."""
    starting: Mapping[str, object] = field(default_factory=dict[str, object])
    """The numbers the unit starts from, by name, as the document states them."""
    placement: Placement | None = None


def _str(document: Mapping[str, object], name: str) -> str:
    value = document.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"deployment.{name} is a non-empty string")
    return value


def _maybe_str(document: Mapping[str, object], name: str) -> str:
    """A field a document names or leaves out, ``""`` when it leaves it out."""
    if document.get(name) is None:
        return ""
    return _str(document, name)


def _map(document: Mapping[str, object], name: str) -> Mapping[str, object]:
    value = document.get(name)
    if not isinstance(value, Mapping):
        raise ValueError(f"deployment.{name} is an object")
    return cast("Mapping[str, object]", value)


def _staged(item: object) -> StagedFile:
    if not isinstance(item, Mapping):
        raise ValueError("each of deployment.files is an object")
    entry = cast("Mapping[str, object]", item)
    path = _str(entry, "path")
    if "\\" in path:
        raise ValueError(f"deployment.files path {path} is a relative path inside the folder")
    version = entry.get("version")
    if type(version) is not int:
        raise ValueError("deployment.files version is a whole number")
    fingerprint = _str(entry, "fingerprint")
    if not fingerprint.startswith("sha256:"):
        raise ValueError(f"the fingerprint of {path} is sha256:<hex>")
    size = entry.get("bytes")
    if type(size) is not int or size < 0:
        raise ValueError(f"the bytes of {path} is a whole number")
    return StagedFile(
        _str(entry, "entry_id"), version, fingerprint, path, _str(entry, "kind"), size
    )


def parse_deployment(document: Mapping[str, object]) -> Deployment:
    """The document's fields this node acts on; a ``ValueError`` names the first wrong one."""
    if document.get("schema_version") != DEPLOYMENT_SCHEMA:
        raise ValueError(f"deployment.schema_version is {DEPLOYMENT_SCHEMA}")
    lane = _str(document, "lane")
    if lane not in LANES:
        raise ValueError('deployment.lane is "paper" or "live"')
    files = document.get("files")
    snapshots = document.get("snapshots")
    if not isinstance(files, list) or not isinstance(snapshots, list):
        raise ValueError("deployment.files and deployment.snapshots are lists")
    unit = _map(document, "unit")
    g_record = _map(document, "g_record")
    return Deployment(
        deployment_id=_str(document, "deployment_id"),
        node_tag=_str(_map(document, "node"), "tag"),
        unit_id=_str(unit, "id"),
        unit_document=_map(document, "unit_document"),
        compiled_fingerprint=_str(document, "compiled_fingerprint"),
        logic_fingerprint=_maybe_str(document, "logic_fingerprint"),
        risk_fingerprint=_maybe_str(document, "risk_fingerprint"),
        g_fingerprint=_str(g_record, "compiled_fingerprint"),
        g_logic_fingerprint=_maybe_str(g_record, "logic_fingerprint"),
        files=tuple(_staged(item) for item in cast("list[object]", files)),
        account_id=_str(_map(document, "account"), "id"),
        snapshots=tuple(
            cast("Mapping[str, object]", item)
            for item in cast("list[object]", snapshots)
            if isinstance(item, Mapping)
        ),
        lane=lane,
        markets=_chosen_markets(document),
        starting=_map(_map(document, "starting"), "values"),
        placement=_placement(document.get("placement")),
    )


def _chosen_markets(document: Mapping[str, object]) -> tuple[str, ...]:
    """``deployment.markets`` as market ids of the unit. A document naming none is refused, so an
    empty list can never read as every market of the unit."""
    chosen = document.get("markets")
    if not isinstance(chosen, list) or not chosen:
        raise ValueError("deployment.markets names at least one market he chose")
    unit = _map(document, "unit_document").get("markets")
    held = {
        cast("Mapping[str, object]", market).get("market_id")
        for market in (cast("list[object]", unit) if isinstance(unit, list) else [])
        if isinstance(market, Mapping)
    }
    named: list[str] = []
    for item in cast("list[object]", chosen):
        market = (
            cast("Mapping[str, object]", item).get("market_id")
            if isinstance(item, Mapping)
            else None
        )
        if not isinstance(market, str) or market not in held:
            raise ValueError(f"deployment.markets names {market}, which the unit does not trade")
        named.append(market)
    return tuple(dict.fromkeys(named))


# --- the board feed: an optional placement read (connections C25) ----------------------------

BOARD_FEED: Final = Path("feeds") / "board.json"
"""The node's ``[feeds.board]`` under its ``data/``. Only the host's feed relay writes it."""
BOARD_SCHEMA: Final = "qmx.node.feed.board/1"
_NS: Final = 1_000_000_000


@dataclass(frozen=True, slots=True)
class Placement:
    """A deployment's placement read: of the unit's markets, those the ``tier`` board reads in
    one of the ``favours`` words of ``reading``, while that board is at most ``stale_after_ns``
    old."""

    tier: str
    reading: str
    favours: frozenset[str]
    stale_after_ns: int


def _placement(raw: object) -> Placement | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError("deployment.placement is an object")
    read = cast("Mapping[str, object]", raw)
    tier, reading, favours = read.get("tier"), read.get("reading"), read.get("favours")
    if not isinstance(tier, str) or not tier or not isinstance(reading, str) or not reading:
        raise ValueError("deployment.placement names a tier and a reading id")
    words = cast("list[object]", favours) if isinstance(favours, list) else []
    if not words or not all(isinstance(word, str) and word for word in words):
        raise ValueError("deployment.placement.favours is a list of the reading's words")
    stale = read.get("stale_after_s")
    if type(stale) is not int or stale <= 0:
        raise ValueError("deployment.placement.stale_after_s is a whole number of seconds")
    return Placement(tier, reading, frozenset(cast("list[str]", words)), stale * _NS)


@dataclass(frozen=True, slots=True)
class BoardRead:
    """What a placement read sees now. Only ``held_back`` changes trading: a market a fresh
    board reads in a word the read does not favour takes no new entry. Every other market of
    the unit trades on its own conditions, the read's fallback (Level 0 AD-2): all of them when
    the board is stale, missing, withheld or unreadable."""

    state: str
    detail: str
    as_of_ms: int | None = None
    """When the board was read by the MIS, on this machine's clock, in ms since the epoch."""
    favoured: tuple[str, ...] = ()
    held_back: Mapping[str, str] = field(default_factory=dict[str, str])
    fallback: tuple[str, ...] = ()

    def document(self) -> dict[str, object]:
        return {
            "state": self.state,
            "detail": self.detail,
            "as_of_ms": self.as_of_ms,
            "favoured": list(self.favoured),
            "held_back": dict(self.held_back),
            "fallback": list(self.fallback),
        }


@dataclass(frozen=True, slots=True)
class _TierBoard:
    age_ns: int
    """Its age when the relay wrote it, on the relay's own clock."""
    markets: Mapping[str, tuple[Mapping[str, object], Mapping[str, object]]]
    """Each market's reading words and their freshness words, by reading id."""


def _object(value: object) -> Mapping[str, object]:
    return cast("Mapping[str, object]", value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return cast("list[object]", value) if isinstance(value, list) else []


def _tier_boards(raw: object) -> dict[str, _TierBoard] | tuple[str, str]:
    """The relayed document's boards by tier, or the state and detail that stand in for them."""
    document = _object(raw)
    if document.get("schema_version") != BOARD_SCHEMA:
        return "unreadable", f"the board feed is not {BOARD_SCHEMA}"
    withheld = document.get("withheld")
    if isinstance(withheld, str):
        return "withheld", withheld
    found: dict[str, _TierBoard] = {}
    for item in _list(document.get("boards")):
        board = _object(item)
        tier, age = board.get("tier"), board.get("age_ns")
        if not isinstance(tier, str) or type(age) is not int or age < 0:
            return "unreadable", "a relayed board lacks its tier or its age"
        rows = {
            str(market.get("market_id")): (
                _object(market.get("states")),
                _object(market.get("freshness")),
            )
            for market in map(_object, _list(board.get("markets")))
        }
        found.setdefault(tier, _TierBoard(age, rows))
    return found


class BoardFeed:
    """The node's ``[feeds.board]``: the relayed board, judged on this machine's clock.

    A board's age is the age the relay stamped plus the time since the file was written, read
    from the file's own modification time. Both the write and that time belong to this
    machine, so no host clock is ever compared with the node's."""

    def __init__(self, path: Path, clock_ns: Callable[[], int]) -> None:
        self.path = path
        self.clock_ns = clock_ns
        self._seen: tuple[int, int] | None = None
        self._boards: dict[str, _TierBoard] | tuple[str, str] = {}

    def _load(self) -> tuple[int, dict[str, _TierBoard] | tuple[str, str]]:
        try:
            stat = self.path.stat()
        except OSError:
            self._seen = None
            return 0, ("missing", "no board has been relayed to this node")
        if self._seen != (stat.st_mtime_ns, stat.st_size):
            try:
                text = self.path.read_bytes()
            except OSError:
                # Caught mid-replace on Windows: it is read again on the next tick.
                return stat.st_mtime_ns, ("unreadable", "the board feed could not be read")
            try:
                raw: object = json.loads(text)
            except ValueError:
                raw = None
            self._boards = _tier_boards(raw)
            self._seen = (stat.st_mtime_ns, stat.st_size)
        return stat.st_mtime_ns, self._boards

    def read(self, placement: Placement, markets: Iterable[str]) -> BoardRead:
        written, boards = self._load()
        admitted = tuple(markets)
        if isinstance(boards, tuple):
            return BoardRead(*boards, fallback=admitted)
        board = boards.get(placement.tier)
        if board is None:
            detail = f"the board holds nothing for the {placement.tier} tier"
            return BoardRead("empty", detail, fallback=admitted)
        as_of_ms = (written - board.age_ns) // 1_000_000
        if board.age_ns + max(0, self.clock_ns() - written) > placement.stale_after_ns:
            detail = f"older than its stale_after of {placement.stale_after_ns // _NS} s"
            return BoardRead("stale", detail, as_of_ms, fallback=admitted)
        favoured: list[str] = []
        held: dict[str, str] = {}
        fallback: list[str] = []
        for market in admitted:
            states, freshness = board.markets.get(market, ({}, {}))
            word = states.get(placement.reading)
            if freshness.get(placement.reading) != "fresh" or not isinstance(word, str):
                fallback.append(market)
            elif word in placement.favours:
                favoured.append(market)
            else:
                held[market] = word
        return BoardRead("fresh", "", as_of_ms, tuple(favoured), held, tuple(fallback))


def staging_folder(data: Path, deployment_id: str) -> Path:
    return data / "deployments" / deployment_id / "in"


def snapshot_path(data: Path, deployment_id: str) -> Path:
    """The deployment's saved unit state, beside the staging folder it owns."""
    return data / "deployments" / deployment_id / "snapshot.json"


def unit_symbols(deployment: Deployment) -> dict[str, str]:
    """Each market of the unit by the symbol the unit's own document states."""
    found: dict[str, str] = {}
    raw = deployment.unit_document.get("markets")
    for item in cast("list[object]", raw) if isinstance(raw, list) else ():
        if not isinstance(item, Mapping):
            continue
        entry = cast("Mapping[str, object]", item)
        market = entry.get("market_id")
        reference = entry.get("instrument_ref")
        symbol = (
            cast("Mapping[str, object]", reference).get("symbol")
            if isinstance(reference, Mapping)
            else None
        )
        if isinstance(market, str) and isinstance(symbol, str):
            found[market] = symbol
    return found


def stream_seconds(name: str) -> int | None:
    """A QMB stream name as seconds, read as ``qmb/host/unit_runner.py`` reads it: ``m15`` 900."""
    unit, count = name[:1], name[1:]
    if not count.isdigit() or int(count) == 0:
        return None
    match unit:
        case "m":
            return int(count) * 60
        case "h":
            return int(count) * 3600
        case "d":
            return int(count) * 86_400
        case _:
            return None


def _bar_name(ns: int) -> str:
    """A feed bar size as the words a refusal says it in."""
    seconds = ns // _NS
    if ns % (60 * _NS) == 0:
        return f"{seconds // 60:g}-minute"
    return f"{seconds:g}-second"


class _Roll:
    """One unit's stream on one market, rolled up from its account feed's base bars (AD-25).

    ``seconds`` is the unit's stream and ``base_ns`` the feed's base bar. The host refuses a
    stream that is not a whole multiple of the base, so every stream bucket is a run of base
    bars. A bucket is emitted only when its first base bar starts it, and the bucket joined part
    way through is dropped by ``roll_up``.
    """

    def __init__(self, seconds: int, base_ns: int) -> None:
        self.seconds = seconds
        self.base_ns = base_ns
        self._bucket: int | None = None
        self._bars: list[QuoteBar] = []

    def add(self, base: QuoteBar) -> QuoteBar | None:
        """This base bar's closed stream bar, or None while the stream's bucket is open."""
        end = base.knowable_at.value_ns
        start = end - self.base_ns
        bucket = start - start % (self.seconds * _NS)
        if bucket != self._bucket:
            self._bucket, self._bars = bucket, []
        self._bars.append(base)
        if end < bucket + self.seconds * _NS:
            return None
        rolled = roll_up(self._bars, self.seconds)
        self._bars = []
        return rolled


def staged_path(folder: Path, path: str) -> Path | None:
    """``path`` inside the staging folder, or None when it resolves outside it: an absolute
    path, ``..``, a link out, or on Windows a rooted ``/x`` or a drive-relative ``C:x``."""
    target = (folder / path).resolve()
    return target if target.is_relative_to(folder.resolve()) else None


def deploy_preflight(data: Path, document: Mapping[str, object]) -> Answer | None:
    """``deploy``'s refusals before it is kept, each naming what is wrong; None when it may go.

    A path outside the staging folder answers ``bad_argument``. A file missing from the
    staging folder answers ``files_missing``, which the node link's outbox keeps waiting on;
    a file of another size than the document states answers ``file_mismatch``. A deployment that
    names both halves is refused as ``g_record_missing`` when its G record names another logic
    half; a document written before the split keeps the compiled-half comparison. Only stats are
    read here, so the answer stays inside the 2 s budget whatever the files weigh: there is no
    size limit. Each file's fingerprint was verified by the node link as it staged it, and the
    runtime verifies it again as it reads the file to compile (:func:`compile_staged`). A kept
    deployment's ``lock.json`` lists every staged file.
    """
    try:
        deployment = parse_deployment(document)
    except ValueError as error:
        return refused("bad_argument", f"deploy: {error}")
    if deployment.logic_fingerprint:
        if not deployment.risk_fingerprint:
            return refused(
                "bad_argument",
                "deploy: a deployment that names its logic fingerprint names its risk fingerprint",
            )
        if deployment.g_logic_fingerprint != deployment.logic_fingerprint:
            return refused(
                "g_record_missing",
                "the deployment's G record tested "
                f"{deployment.g_logic_fingerprint or 'no logic fingerprint'}, not its logic"
                f" fingerprint {deployment.logic_fingerprint}",
                next_step=(
                    "Run the behaviour check on this unit version; a passing check lets it trade."
                ),
                value={
                    "logic_fingerprint": deployment.logic_fingerprint,
                    "g_record": deployment.g_logic_fingerprint,
                },
            )
    elif deployment.compiled_fingerprint != deployment.g_fingerprint:
        return refused(
            "fingerprint_mismatch",
            "the deployment's compiled fingerprint is not the one its G record tested",
            value={
                "compiled_fingerprint": deployment.compiled_fingerprint,
                "g_record": deployment.g_fingerprint,
            },
        )
    folder = staging_folder(data, deployment.deployment_id)
    for item in deployment.files:
        if staged_path(folder, item.path) is None:
            return refused(
                "bad_argument",
                f"deploy: deployment.files path {item.path} is a relative path inside the folder",
            )
    missing = [item.path for item in deployment.files if not (folder / item.path).is_file()]
    if missing:
        return refused(
            "files_missing",
            f"deploy: staged file {missing[0]} is missing from {folder.name}/",
            next_step="The node link stages every file before it asks again.",
            value={"missing": cast("list[Json]", missing)},
        )
    for item in deployment.files:
        size = (folder / item.path).stat().st_size
        if size != item.size:
            return refused(
                "file_mismatch",
                f"deploy: staged file {item.path} holds {size} bytes, not {item.size}",
                value={"path": item.path, "expected": item.size, "found": size},
            )
    lock = [
        {"path": item.path, "fingerprint": item.fingerprint, "kind": item.kind}
        for item in deployment.files
    ]
    folder.mkdir(parents=True, exist_ok=True)
    (folder.parent / "lock.json").write_text(json.dumps(lock, sort_keys=True), "utf-8")
    return None


def _other_version(compiled: CompiledUnit, deployment: Deployment) -> str | None:
    """Why ``compiled`` is not the unit version ``deployment`` names, or None when it is (AD-3).

    A document written before the split names one fingerprint, the compiled half its G record
    tested. A split document names the logic half its G record tested and the risk half his click
    covered, so a size edit stays the same logic half on the same G record, and a logic edit is
    refused until a G run covers the new half. The compiled comparison stays for a split document
    too, because a lock or option change moves it beside neither half.
    """
    if not deployment.logic_fingerprint:
        if compiled.compiled_fingerprint.value != deployment.g_fingerprint:
            return (
                f"compiled to {compiled.compiled_fingerprint.value}, not the"
                f" {deployment.g_fingerprint} its G record tested"
            )
        return None
    if compiled.compiled_fingerprint.value != deployment.compiled_fingerprint:
        return (
            f"compiled to {compiled.compiled_fingerprint.value}, not the"
            f" {deployment.compiled_fingerprint} its document names"
        )
    if compiled.logic_fingerprint.value != deployment.logic_fingerprint:
        return (
            f"compiled to logic {compiled.logic_fingerprint.value}, not the"
            f" {deployment.logic_fingerprint} its G record tested"
        )
    if compiled.risk_fingerprint.value != deployment.risk_fingerprint:
        return (
            f"compiled to risk {compiled.risk_fingerprint.value}, not the"
            f" {deployment.risk_fingerprint} his click covered"
        )
    return None


# --- the venue side ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Ticket:
    """One command for the venue with what the node knows beside it.

    ``tags`` ride an entry (its client order id and cTrader ``label``); ``position`` names the
    venue position a close or an amendment acts on, which is its entry's client order id.
    """

    command: Command
    market_id: str
    side: Side
    reference: Decimal
    quantity: Decimal | None = None
    receipt_quantity: Decimal | None = None
    tags: OrderTags | None = None
    position: str | None = None


@dataclass(frozen=True, slots=True)
class Sent:
    outcome: SubmissionOutcome
    price: Decimal | None = None
    code: str | None = None
    quantity: Decimal | None = None
    """On an accepted entry, the quantity the venue filled, which an IOC order may leave short
    of the ticket's. None when the binding reads only the whole ticket filled."""
    position_id: str | None = None
    """On an accepted entry, the venue's id for the position it opened, when it has one apart
    from the client order id. Journalled, so a later start can ask how that position closed."""


@dataclass(frozen=True, slots=True)
class VenueClose:
    """The venue closed a position: its stop fired, or the node closed it."""

    kind: FillKind
    price: Decimal
    gap: bool = False
    guessed: bool = False
    """No deal named this close, so the price is the stop the node held."""


class VenueAccount(Protocol):
    """One account binding at a venue, as the order path sends to it."""

    @property
    def account(self) -> Account: ...

    @property
    def stop_forms(self) -> Mapping[str, str]:
        """The protective-stop form the venue proved per order type at its last verification."""
        ...

    def send(self, ticket: Ticket, /) -> Result[Sent]: ...

    def stop_of(self, position: str, /) -> Decimal | None:
        """The stop the venue holds on the position, or None."""
        ...

    def closed(self, position: str, /) -> VenueClose | None: ...

    def equity(self) -> Decimal: ...

    def read_back(self) -> Result[ReadBack]:
        """Every order and position the venue holds on the account, as reconcile reads them."""
        ...

    def nets_positions(self) -> bool:
        """Whether one position per symbol is all this venue keeps, so a second unit's cancels."""
        ...

    def bar_size_ns(self) -> int | None:
        """The bar this venue's feed builds, or None when its bars are the unit's own."""
        ...

    def add_markets(self, markets: Mapping[str, str], /) -> bool:
        """Add each market the binding does not hold; True when the session must reconnect."""
        ...

    def unauthorised(self, market: str, /) -> str | None:
        """Why this binding cannot trade ``market``, or None when it can."""
        ...


@dataclass
class _Held:
    market_id: str
    side: Side
    quantity: Decimal
    entry: Decimal
    stop: Decimal | None
    label: str | None = None


@dataclass
class ConformanceAccount:
    """The conformance venue's account: a fake, never a broker, no network and no key.

    The conformance double answers every command as the venue's port does, its protection gate
    included. Beside it this keeps what a broker keeps: positions, the stop each one holds as
    the order's distance from its fill, and the broker firing that stop on the feed's bars.
    ``received`` is every ticket that reached the venue. With ``holds_stops`` false the venue
    answers but never holds a stop, which the protection escalation is tested against. The next
    ``lose_answers`` entries are carried out and their answers lost on the way back, as when the
    network cuts after a send (TN-01).
    """

    double: ConformanceDouble
    venue_account: Account
    starting_equity: Decimal
    holds_stops: bool = True
    lose_answers: int = 0
    partial_fills: list[Decimal] = field(default_factory=list[Decimal])
    """The quantity each coming entry fills, first entry first; an entry past the list fills
    whole. The rest of a partly filled entry is never filled."""
    received: list[Ticket] = field(default_factory=list[Ticket])
    stated_balance: Decimal | None = None
    """The cash the venue states when a case moves it; None answers the starting balance."""
    balance_reads: int = 0
    """How many times the node asked for the cash again: the record the exit-path fact reads."""
    _orders: list[VenueOrder] = field(default_factory=list[VenueOrder])
    _positions: dict[str, _Held] = field(default_factory=dict[str, _Held])
    _closed: dict[str, VenueClose] = field(default_factory=dict[str, VenueClose])
    _quotes: dict[str, tuple[Decimal, Decimal]] = field(
        default_factory=dict[str, tuple[Decimal, Decimal]]
    )

    @classmethod
    def open(
        cls, account: Account, starting_equity: Decimal, *, holds_stops: bool = True
    ) -> Result[ConformanceAccount]:
        double = ConformanceDouble.try_create(World.LIVE, account.venue)
        if is_refusal(double):
            return double
        opened = double.value.open_session(account)
        if is_refusal(opened):
            return opened
        verified = double.value.verify_capabilities()
        if is_refusal(verified):
            return verified
        return Ok(cls(double.value, account, starting_equity, holds_stops))

    @property
    def account(self) -> Account:
        return self.venue_account

    @property
    def stop_forms(self) -> Mapping[str, str]:
        return self.double.protective_stop_forms

    def on_bar(self, event: Bar) -> None:
        """The venue sees a closed bar: a held stop it crossed fires at the stop, or at the
        open when the bar opened past it."""
        bar = event.bar
        for position, held in list(self._positions.items()):
            if held.market_id != event.market_id or held.stop is None:
                continue
            long = held.side is Side.LONG
            quote = bar.bid if long else bar.ask
            worse = 1 if long else -1
            if (held.stop - quote.open) * worse > 0:
                self._close(position, VenueClose(FillKind.STOP, quote.open, gap=True))
            elif (held.stop - (quote.low if long else quote.high)) * worse >= 0:
                self._close(position, VenueClose(FillKind.STOP, held.stop))
        self._quotes[event.market_id] = (bar.bid.close, bar.ask.close)

    def _close(self, position: str, closed: VenueClose) -> None:
        del self._positions[position]
        self._closed[position] = closed

    def send(self, ticket: Ticket, /) -> Result[Sent]:
        self.received.append(ticket)
        answered = self.double.submit(ticket.command)
        if is_refusal(answered):
            return answered
        result = answered.value
        if result.outcome is not SubmissionOutcome.ACCEPTED_BY_VENUE:
            return Ok(Sent(result.outcome, None, result.observation.venue_code))
        bid, ask = self._quotes.get(ticket.market_id, (ticket.reference, ticket.reference))
        params = ticket.command.order_parameters
        if params is not None and ticket.tags is not None and ticket.quantity is not None:
            long = ticket.side is Side.LONG
            price = ask if long else bid
            distance = params.protective_stop_distance
            stop = None
            if distance is not None and self.holds_stops:
                gap = Decimal(distance.value).scaleb(-distance.scale)
                stop = price - gap if long else price + gap
            name, label = ticket.tags.client_order_id, ticket.tags.label
            filled = self.partial_fills.pop(0) if self.partial_fills else ticket.quantity
            self._positions[name] = _Held(ticket.market_id, ticket.side, filled, price, stop, label)
            self._orders.append(
                VenueOrder(name, label, ticket.market_id, OrderState.FILLED, name, price)
            )
            if self.lose_answers > 0:
                self.lose_answers -= 1
                return Ok(Sent(SubmissionOutcome.UNKNOWN))
            return Ok(Sent(result.outcome, price, quantity=filled))
        position = ticket.position
        if position is None or position not in self._positions:
            return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "no-such-position"))
        held = self._positions[position]
        if ticket.command.protection_amendment is not None:
            if not self.holds_stops:
                return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "stop-not-held"))
            amended = ticket.command.protection_amendment.new_distance
            gap = Decimal(amended.value).scaleb(-amended.scale)
            held.stop = held.entry - gap if held.side is Side.LONG else held.entry + gap
            return Ok(Sent(result.outcome, held.stop))
        price = bid if held.side is Side.LONG else ask
        self._close(position, VenueClose(FillKind.CLOSE, price))
        return Ok(Sent(result.outcome, price))

    def stop_of(self, position: str, /) -> Decimal | None:
        held = self._positions.get(position)
        return None if held is None else held.stop

    def closed(self, position: str, /) -> VenueClose | None:
        return self._closed.get(position)

    def equity(self) -> Decimal:
        """The account's balance as the venue states it. The conformance venue keeps its
        starting balance; it models fills and stops, not money."""
        return self.starting_equity

    def read_balance(self) -> Result[Decimal]:
        """The cash the venue states, asked for again as the node's timed read asks it.

        The conformance venue states ``starting_equity`` unless a case moved it, and counts the
        reads, so the exit-path fact can prove a read did or did not happen on a pass.
        """
        self.balance_reads += 1
        return Ok(self.starting_equity if self.stated_balance is None else self.stated_balance)

    def read_back(self) -> Result[ReadBack]:
        positions = tuple(
            VenuePosition(
                name,
                held.label,
                held.market_id,
                held.side.value,
                held.quantity,
                held.entry,
                held.stop,
            )
            for name, held in self._positions.items()
        )
        return Ok(ReadBack(tuple(self._orders), positions))

    def nets_positions(self) -> bool:
        """The conformance double reports a netting account unless a case arms hedging, so one
        position per market is the model here as well."""
        return True

    def bar_size_ns(self) -> int | None:
        """Its bars are the ones the recording plays, not a size of its own."""
        return None

    def add_markets(self, markets: Mapping[str, str], /) -> bool:
        del markets
        return False

    def unauthorised(self, market: str, /) -> str | None:
        del market
        return None

    def opened_elsewhere(self, order: VenueOrder, position: VenuePosition | None = None) -> None:
        """An order, and the position it opened, that reached the account from somewhere other
        than this node: his own trade, another node's, or a twin's."""
        self._orders.append(order)
        if position is not None:
            self._positions[position.position] = _Held(
                position.market_id,
                Side(position.side),
                position.quantity,
                position.entry_price,
                position.stop,
                position.label,
            )

    def positions(self) -> dict[str, tuple[str, str, Decimal, Decimal | None]]:
        """Every open position: market, side, quantity and the stop the venue holds."""
        return {
            key: (held.market_id, held.side.value, held.quantity, held.stop)
            for key, held in self._positions.items()
        }


@dataclass
class Venue:
    """One account binding the node trades on: the venue's account and its feed keeper."""

    client: VenueAccount
    feed: FeedKeeper


# --- the order path ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Placed:
    price: Decimal
    partial: Decimal | None = None
    """On an entry the venue filled only part of, the quantity it filled, which the unit holds
    and every exit, stop and kill acts on. None when the whole order filled."""


@dataclass(frozen=True, slots=True)
class Blocked:
    reason: str


@dataclass(frozen=True, slots=True)
class Unprotected(Blocked):
    """The venue filled the entry and does not hold its stop: blocked for the unit, open at
    the venue, and closed by the node until the venue shows it closed."""

    price: Decimal


@dataclass(frozen=True, slots=True)
class Unknown(Blocked):
    """The venue's answer to an entry was lost: the order may or may not be at the venue. It
    stays resting for the unit until the reconciler reads the venue (TN-01)."""

    client_order_id: str


def ulid(at_ms: int, seed: str) -> str:
    """A 26-character ULID: ``at_ms`` then 80 bits of SHA-256 of ``seed``, so the same order
    on a re-run gets the same id."""
    tail = int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:10], "big")
    number = (at_ms % (1 << 48)) << 80 | tail
    return "".join(_ULID_ALPHABET[(number >> (5 * shift)) & 31] for shift in range(25, -1, -1))


def _scaled(value: Decimal) -> tuple[int, int]:
    exponent = value.normalize().as_tuple().exponent
    scale = -exponent if isinstance(exponent, int) and exponent < 0 else 0
    return int(value.scaleb(scale)), scale


def _delta(value: Decimal, instrument: Instrument) -> Result[PriceDelta]:
    number, scale = _scaled(value)
    return PriceDelta.try_create(number, instrument, scale)


def _price(value: Decimal, instrument: Instrument) -> Result[Price]:
    number, scale = _scaled(value)
    return Price.try_create(number, instrument, scale)


def _past_entry(side: Side, stop: Decimal, entry: Decimal) -> bool:
    return (stop - entry) * (1 if side is Side.LONG else -1) > 0


class _OrderJournal:
    """The node journal as the journal-before-dispatch gate's sink: one ``order`` row."""

    def __init__(self, journal: JournalWriter, clock_ns: Callable[[], int]) -> None:
        self._journal = journal
        self._clock_ns = clock_ns

    def append(self, event: object, /) -> SinkResult:
        body = dict(cast("Mapping[str, object]", event))
        written = self._journal.append(
            "order", body, RowFacts(ts_recv=self._clock_ns(), clock_ok=False)
        )
        if is_refusal(written):
            return written
        return Ok(SinkAck())


class _Dispatch:
    def __init__(self, send: Callable[[], Result[Sent]]) -> None:
        self._send = send

    def dispatch(self, payload: Mapping[str, object], /) -> Result[object]:
        del payload
        return cast("Result[object]", self._send())


@dataclass
class OrderPath:
    """Every order of one venue binding, in Level 0 AD-39's order: guards, the cross-unit hook,
    the protection gate, the journal before dispatch, the venue."""

    tag: str
    venue: Venue
    journal: JournalWriter
    clock_ns: Callable[[], int]
    sleep: Callable[[float], None]
    on_alarm: Callable[[Mapping[str, object]], None]
    session_epoch: str = "node-session-1"
    confirm_ns: int = PROTECT_CONFIRM_NS
    retry_max: int = PROTECT_RETRY_MAX
    close_refusals_alarm: int = CLOSE_REFUSALS_ALARM
    unknown: dict[str, str] = field(default_factory=dict[str, str])
    """Each entry whose outcome is unknown, by client order id, with its market: no entry on
    that market until the reconciler resolves it (TN-01). Nothing is ever resent."""
    unprotected: set[str] = field(default_factory=set[str])
    """Positions the node closes on every tick until the venue shows them closed: filled without
    holding their stop, or a unit's full exit the venue refused."""
    _ordinal: int = 0
    _sent: dict[str, Placed | Blocked] = field(default_factory=dict[str, Placed | Blocked])
    _refusals: dict[str, int] = field(default_factory=dict[str, int])

    def _next(self) -> int:
        self._ordinal += 1
        return self._ordinal

    def _journalled(self, body: dict[str, object], ticket: Ticket) -> Result[Sent]:
        sink = _OrderJournal(self.journal, self.clock_ns)
        enacted = enact_command(
            body, journal=sink, dispatcher=_Dispatch(lambda: self._send(ticket))
        )
        if is_refusal(enacted):
            return enacted
        return Ok(cast("Sent", enacted.value.dispatcher_result))

    def _send(self, ticket: Ticket) -> Result[Sent]:
        if isinstance(self.venue.client, ConformanceAccount) and not self.venue.feed.ready:
            return submit_not_ready_refusal()
        return self.venue.client.send(ticket)

    def _note(self, client_order_id: str, step: str, body: Mapping[str, object]) -> None:
        self.journal.append(
            "order",
            {"event_id": f"{client_order_id}/{step}", "client_order_id": client_order_id, **body},
            RowFacts(ts_recv=self.clock_ns(), clock_ok=False),
        )

    def entry(
        self,
        *,
        deployment_id: str,
        client_order_id: str,
        label: str,
        wire: Mapping[str, object],
        record: InstrumentRecord,
        quantity: Quantity,
        blocked_by: str | None,
    ) -> Placed | Blocked:
        """Send one entry once; a second ask for the same client order id answers the first."""
        done = self._sent.get(client_order_id)
        if done is not None:
            return done
        outcome = self._entry(
            deployment_id, client_order_id, label, wire, record, quantity, blocked_by
        )
        self._sent[client_order_id] = outcome
        return outcome

    def _entry(
        self,
        deployment_id: str,
        client_order_id: str,
        label: str,
        wire: Mapping[str, object],
        record: InstrumentRecord,
        quantity: Quantity,
        blocked_by: str | None,
    ) -> Placed | Blocked:
        if blocked_by is not None:
            return Blocked(blocked_by)
        kind = cast("Mapping[str, object]", wire["order"]).get("type")
        if kind != "market":
            return Blocked(f"the venue cannot take a {kind} entry from this node yet")
        side = Side(str(wire["direction"]))
        market = str(wire["market_id"])
        if market in self.unknown.values():
            return Blocked(
                "venue answer unknown for an earlier order, so no entry until it resolves"
            )
        protection = cast("Mapping[str, object]", wire["protection"])
        stop = Decimal(str(protection["stop"]))
        quote = self.venue.feed.quote(market)
        reference = None if quote is None else quote.ask if side is Side.LONG else quote.bid
        if reference is None:
            # "venue not ready" is the run journal's health_stop reason code.
            return Blocked(
                "venue not ready: no quote since its feed connected, so the stop distance"
                " cannot be measured yet"
            )
        distance = reference - stop if side is Side.LONG else stop - reference
        if distance <= 0:
            return Blocked("the stop is not on the loss side of the venue's price")
        instrument = Instrument(VenueId(record.venue), record.symbol)
        gap = _delta(distance, instrument)
        if is_refusal(gap):
            return Blocked(f"the node cannot prove the stop distance ({gap.category.value})")
        params = OrderParameters.try_create(
            OrderType.MARKET,
            TimeInForce.IMMEDIATE_OR_CANCEL,
            quantity,
            protective_stop_distance=gap.value,
            instrument=instrument,
            trade_side="buy" if side is Side.LONG else "sell",
        )
        if is_refusal(params):
            return Blocked(f"the node cannot prove the order ({params.category.value})")
        command = Command.place_order(
            instrument.venue,
            self.venue.client.account,
            self.session_epoch,
            self._next(),
            params.value,
        )
        if is_refusal(command):
            return Blocked(f"the node cannot prove the order ({command.category.value})")
        if self.cross_unit_hook(command.value) is not None:
            return Blocked("the cross-unit hook refused the order")
        gate = require_venue_resident_protective_stop(
            command.value, forms_per_order_type=self.venue.client.stop_forms
        )
        if is_refusal(gate):
            return Blocked("the node cannot prove the venue holds this order's stop")
        tags = order_tags(client_order_id, label)
        if is_refusal(tags):
            return Blocked(f"the node cannot prove the order's tags ({tags.context.get('reason')})")
        size = Decimal(quantity.value).scaleb(-quantity.scale)
        ticket = Ticket(
            command.value,
            market,
            side,
            reference,
            quantity=size,
            receipt_quantity=Decimal(str(wire["quantity"])),
            tags=tags.value,
        )
        body: dict[str, object] = {
            "event_id": f"{client_order_id}/send",
            "client_order_id": client_order_id,
            "deployment_id": deployment_id,
            "sent_at_ns": self.clock_ns(),
            "label": label,
            "step": "send",
            "kind": "entry",
            "decision_row_id": str(wire["decision_row_id"]),
            "market_id": market,
            "side": side.value,
            "quantity": str(size),
            "receipt_quantity": str(wire["quantity"]),
            "stop": str(stop),
            "stop_distance": str(distance),
            "stop_form": gate.value,
        }
        targets = cast("Sequence[Mapping[str, object]]", protection.get("targets") or ())
        if targets:
            body["target"] = str(targets[0]["price"])
        sent = self._journalled(body, ticket)
        if is_refusal(sent):
            if sent.context.get("blocks_entries") is True:
                return Blocked("the node journal could not be written, so the entry is blocked")
            return Blocked(f"the venue refused the order ({sent.context.get('reason')})")
        return self._answered(client_order_id, sent.value, ticket, distance)

    @staticmethod
    def cross_unit_hook(command: Command) -> str | None:
        """The cross-unit hook: a placeholder that passes every order (placeholders row 6)."""
        del command
        return None

    def _answered(
        self, client_order_id: str, sent: Sent, ticket: Ticket, distance: Decimal
    ) -> Placed | Blocked:
        match sent.outcome:
            case SubmissionOutcome.ACCEPTED_BY_VENUE if sent.price is not None:
                filled = ticket.quantity if sent.quantity is None else sent.quantity
                note: dict[str, object] = {
                    "step": "filled",
                    "price": str(sent.price),
                    "quantity": str(filled),
                }
                if sent.position_id is not None:
                    note["position_id"] = sent.position_id
                self._note(client_order_id, "filled", note)
                if self._protected(client_order_id, ticket, distance):
                    return Placed(sent.price, None if filled == ticket.quantity else filled)
                return Unprotected(
                    "the venue cannot hold this order's stop, so the node closes it", sent.price
                )
            case SubmissionOutcome.UNKNOWN:
                self.unknown[client_order_id] = ticket.market_id
                self._note(client_order_id, "unknown", {"step": "unknown"})
                return Unknown("venue answer unknown for this order", client_order_id)
            case _:
                self._note(
                    client_order_id, "rejected", {"step": "rejected", "code": sent.code or ""}
                )
                return Blocked(f"the venue refused the order ({sent.code})")

    def _protected(self, position: str, ticket: Ticket, distance: Decimal) -> bool:
        """Wait for the venue to show the stop, amending it again up to ``retry_max`` tries in
        all; past them, close the position reduce-only and raise the protection alarm."""
        for attempt in range(self.retry_max):
            if attempt:
                self._amend(position, ticket, distance, attempt)
            if self._shows_stop(position):
                return True
        self._escalate(position, ticket.market_id, ticket.side, ticket.reference, self.retry_max)
        return False

    def restore_stop(
        self,
        position: str,
        market: str,
        side: Side,
        stop: Decimal | None,
        entry: Decimal,
        record: InstrumentRecord,
    ) -> None:
        """Put back a stop the venue no longer holds, at ``stop``, up to ``retry_max`` tries. No
        level, a level past entry, or a refusal, as when the price is already past the stop, goes
        straight to the reduce-only close and the protection alarm, so a kill never waits on it."""
        tries = 0
        while stop is not None and not _past_entry(side, stop, entry) and tries < self.retry_max:
            tries += 1
            if self._move_stop(position, market, side, stop, entry, stop, record) is not None:
                break
            if self._shows_stop(position):
                return
        self._escalate(position, market, side, entry, tries)

    def _shows_stop(self, position: str) -> bool:
        deadline = self.clock_ns() + self.confirm_ns
        while True:
            if self.venue.client.stop_of(position) is not None:
                return True
            if self.clock_ns() >= deadline:
                return False
            self.sleep(PROTECT_POLL_S)

    def _escalate(
        self, position: str, market: str, side: Side, reference: Decimal, tries: int
    ) -> None:
        self.unprotected.add(position)
        done = self.close(position, market, side, reference, "protection")
        self._alarm(
            {
                "alarm": "protection_escalation",
                "position": position,
                "market_id": market,
                "tries": tries,
                "action": "closed_reduce_only" if isinstance(done, Placed) else "close_refused",
                "origin": "placeholder",
            }
        )

    def _alarm(self, alarm: Mapping[str, object]) -> None:
        self.journal.append("protection", alarm, RowFacts(ts_recv=self.clock_ns(), clock_ok=False))
        self.on_alarm(alarm)

    def _amend(self, position: str, ticket: Ticket, distance: Decimal, attempt: int) -> None:
        params = ticket.command.order_parameters
        instrument = None if params is None else params.instrument
        if instrument is None:
            return
        gap, reference = _delta(distance, instrument), _price(ticket.reference, instrument)
        if is_refusal(gap) or is_refusal(reference):
            return
        amendment = ProtectionAmendment.try_create(
            ProtectionSide.STOP, gap.value, reference.value, original_risk_distance=gap.value
        )
        if is_refusal(amendment):
            return
        command = Command.amend_protection(
            instrument.venue,
            self.venue.client.account,
            self.session_epoch,
            self._next(),
            amendment.value,
            position,
        )
        if is_refusal(command):
            return
        body: dict[str, object] = {
            "event_id": f"{position}/protect-{attempt + 1}",
            "client_order_id": position,
            "step": "amend_protection",
            "stop_distance": str(distance),
        }
        self._journalled(body, replace(ticket, command=command.value, position=position, tags=None))

    def close(
        self, position: str, market: str, side: Side, reference: Decimal, why: str
    ) -> Placed | Blocked:
        """Close one position reduce-only. A close is never blocked by a guard, and a journal
        that cannot be written does not stop it. Asking again for the same position and reason
        repeats its journal row and sends the close again; the ``close_refusals_alarm``-th
        refusal of one position raises the protection alarm."""
        done = self._close(position, market, side, reference, why)
        if isinstance(done, Placed):
            self._refusals.pop(position, None)
            self.unprotected.discard(position)
            return done
        refusals = self._refusals.get(position, 0) + 1
        self._refusals[position] = refusals
        if refusals == self.close_refusals_alarm:
            self._alarm(
                {
                    "alarm": "close_refused",
                    "position": position,
                    "market_id": market,
                    "why": why,
                    "refusals": refusals,
                    "origin": "placeholder",
                }
            )
        return done

    def _close(
        self, position: str, market: str, side: Side, reference: Decimal, why: str
    ) -> Placed | Blocked:
        command = Command.close_position(
            self.venue.client.account.venue,
            self.venue.client.account,
            self.session_epoch,
            self._next(),
            CloseScope.INSTRUMENT_WITHIN_BINDING,
            position,
        )
        if is_refusal(command):
            return Blocked(f"the close could not be built ({command.category.value})")
        quote = self.venue.feed.quote(market)
        current = None if quote is None else quote.bid if side is Side.LONG else quote.ask
        ticket = Ticket(
            command.value,
            market,
            side,
            reference if current is None else current,
            position=position,
        )
        body: dict[str, object] = {
            "event_id": f"{position}/close-{why}",
            "client_order_id": position,
            "step": "close",
            "why": why,
            "market_id": market,
        }
        sent = self._journalled(body, ticket)
        if is_refusal(sent) and sent.context.get("blocks_entries") is True:
            sent = self._send(ticket)
        if is_refusal(sent):
            return Blocked(f"the venue refused the close ({sent.context.get('reason')})")
        if (
            sent.value.outcome is SubmissionOutcome.ACCEPTED_BY_VENUE
            and sent.value.price is not None
        ):
            self._note(
                position, f"closed-{why}", {"step": "closed", "price": str(sent.value.price)}
            )
            return Placed(sent.value.price)
        return Blocked(f"the venue refused the close ({sent.value.code})")

    def amend(
        self,
        position: str,
        market: str,
        side: Side,
        new_stop: Decimal,
        entry: Decimal,
        held_stop: Decimal,
        record: InstrumentRecord,
    ) -> Placed | Blocked:
        """Move a held stop the unit tightened; the caller checked that it only tightens, and
        the amendment's own risk check refuses a wider distance again. The venue takes a distance
        on the loss side, so a stop past entry goes out only once the risk session has signed
        the distance. The answer is the stop the broker holds, and an alarm says when that is
        not the one asked for, one tick apart being the venue's rounding."""
        if _past_entry(side, new_stop, entry):
            blocked = Blocked(
                "the new stop is past entry, not on the loss side, so the node did not send it"
            )
            self._note(
                position,
                f"amend-blocked-{new_stop}",
                {"step": "amend_blocked", "stop": str(new_stop), "reason": blocked.reason},
            )
            return blocked
        refused = self._move_stop(position, market, side, new_stop, entry, held_stop, record)
        if refused is not None:
            return refused
        at_broker = self.venue.client.stop_of(position)
        if at_broker is not None and abs(at_broker - new_stop) < Decimal(1).scaleb(-record.digits):
            return Placed(at_broker)
        self._alarm(
            {
                "alarm": "stop_differs",
                "position": position,
                "market_id": market,
                "asked": str(new_stop),
                "at_broker": _text(at_broker),
                "action": "answered_the_brokers_stop",
            }
        )
        if at_broker is None:
            return Blocked("the venue cannot show the amended stop")
        return Placed(at_broker)

    def _move_stop(
        self,
        position: str,
        market: str,
        side: Side,
        new_stop: Decimal,
        entry: Decimal,
        held_stop: Decimal,
        record: InstrumentRecord,
    ) -> Blocked | None:
        """Send the stop to the venue; None when the venue accepted it."""
        instrument = Instrument(VenueId(record.venue), record.symbol)
        gap = _delta(abs(entry - new_stop), instrument)
        first = _delta(abs(entry - held_stop), instrument)
        reference = _price(entry, instrument)
        if is_refusal(gap) or is_refusal(first) or is_refusal(reference):
            return Blocked("the node cannot prove the amended stop")
        amendment = ProtectionAmendment.try_create(
            ProtectionSide.STOP, gap.value, reference.value, original_risk_distance=first.value
        )
        if is_refusal(amendment):
            return Blocked("the amendment widens the stop")
        command = Command.amend_protection(
            instrument.venue,
            self.venue.client.account,
            self.session_epoch,
            self._next(),
            amendment.value,
            position,
        )
        if is_refusal(command):
            return Blocked("the node cannot prove the amended stop")
        body: dict[str, object] = {
            "event_id": f"{position}/amend-{new_stop}",
            "client_order_id": position,
            "step": "amend_protection",
            "stop": str(new_stop),
        }
        ticket = Ticket(command.value, market, side, entry, position=position)
        sent = self._journalled(body, ticket)
        if is_refusal(sent) or sent.value.outcome is not SubmissionOutcome.ACCEPTED_BY_VENUE:
            return Blocked("the venue refused the amended stop")
        return None


# --- one hosted unit ------------------------------------------------------------------------


class _Execution:
    """The shared handler's execution port on the node: prices come from the venue."""

    def __init__(self, unit: NodeUnit) -> None:
        self._unit = unit
        self.price: Decimal | None = None

    def entry_price(self, market: str, side: Side, bar: QuoteBar, /) -> Decimal:
        del market, side, bar
        return cast("Decimal", self.price)

    def close_price(self, market: str, side: Side, bar: QuoteBar, /) -> Decimal:
        del market, side, bar
        return cast("Decimal", self.price)

    def protective(self, market: str, held: HeldPosition, bar: QuoteBar, /) -> Reached | None:
        return self._unit.protective(market, held, bar)


class _Journal:
    """The unit journal as the node writes it: each position under its venue name."""

    def __init__(self, unit: NodeUnit, journal: RunJournal) -> None:
        self._unit = unit
        self._journal = journal

    def append(self, record: JournalRecord, /) -> None:
        match record:
            case Fill():
                if record.kind is FillKind.ENTRY:
                    named = self._unit.names[record.decision_row_id]
                    at_venue = self._unit.at_venue.get(named, named)
                    self._unit.venue_ids[record.position_id] = at_venue
                record = replace(record, position_id=self._unit.venue_name(record.position_id))
            case UnitTrade():
                record = replace(record, trade_id=self._unit.venue_name(record.trade_id))
            case DecisionRow():
                facts = self._unit.account_inputs()
                if facts:
                    record = replace(record, inputs={**record.inputs, **facts})
            case _:
                pass
        self._journal.append(record)


class _OwnJournal:
    """The unit's own closed trades, stamped with the deployment's lane and venue names."""

    def __init__(self, unit: NodeUnit, inner: Surface) -> None:
        self._unit = unit
        self._inner = inner

    def at(self, instant: Instant, /) -> object:
        trades = cast("Iterable[ClosedTrade]", self._inner.at(instant))
        return tuple(
            replace(t, world=self._unit.lane, trade_id=self._unit.venue_name(t.trade_id))
            for t in trades
        )


class _ScopeClose:
    """A unit's last fall-through: the node closes every position of the deployment whose own
    exits could not run for ``exit_fault_bars`` bars, with the reason it gives (AD-13)."""

    def __init__(self, runtime: Runtime, deployment_id: str) -> None:
        self._runtime = runtime
        self._deployment_id = deployment_id

    def close_scope(self, unit: object, why: str) -> None:
        del unit
        self._runtime.close_scope(self._deployment_id, why)


class NodeUnit:
    """One deployment's unit on this node: the shared handler, wrapped with the order path.

    The five ``run_slice`` hooks delegate to the shared handler. Each minted intent is sent to
    the venue as soon as it is minted, the way a live order goes; its fill is booked on the
    next bar, when the handler fills a resting intent, at the price the venue answered. An
    intent already handled answers as done, so a slice the driver re-drives sends nothing and
    fills nothing twice.
    """

    def __init__(
        self,
        deployment: Deployment,
        compiled: CompiledUnit,
        records: Mapping[str, InstrumentRecord],
        orders: OrderPath,
        journal: RunJournal,
        guard: Callable[[str], str | None],
        assignment: Mapping[str, Decimal] | None = None,
        rates: RatePort | None = None,
        port: object | None = None,
    ) -> None:
        self.deployment = deployment
        self.assignment = assignment
        self.traded = deployment.markets
        self.compiled = compiled
        self.stream = compiled.plan.stream
        self.stream_seconds = stream_seconds(self.stream)
        self.base_ns: int | None = None
        """The account feed's base bar, or None when the feed's bars are the unit's own."""
        self.records = records
        self.orders = orders
        self.journal = journal
        self.port = port
        """This unit's last fall-through: the runtime closes the positions its own exits cannot
        run for (AD-13, AD-23 step 4)."""
        self.lane = deployment.lane
        self.journal_world = JournalWorld.PAPER
        self.guard = guard
        self.rates = rates
        self.windows = {
            (self.stream, market): BarWindow(window_size(compiled)) for market in records
        }
        self.rolling: dict[str, _Roll] = {}
        """One roll per traded market, made when the feed's base bar arrives."""
        self.warm_needed = window_size(compiled)
        self.warm_seen = 0
        self.warming = True
        self.venue_ids: dict[str, str] = {}
        self.names: dict[str, str] = {}
        self.at_venue: dict[str, str] = {}
        """Each entry the reconcile found under another venue name than its client order id,
        such as a cTrader position id, with that name, which its closes and stop reads use."""
        self.placed: dict[str, tuple[str, Side, Decimal]] = {}
        """Each entry the venue filled, by its venue name (its client order id unless
        ``at_venue`` names another): market, side and fill price, its stop held or not."""
        self._orders: dict[str, Placed | Blocked] = {}
        self._unknown: dict[str, tuple[str, str, Side, Decimal]] = {}
        """Each entry whose outcome is unknown, by client order id: its intent, market, side and
        the quantity sent."""
        self._done: set[str] = set()
        self._execution = _Execution(self)
        self._port = _Journal(self, journal)
        self.handler: UnitSliceHandler | None = None
        self.hosted_unit: HostedUnit | None = None
        self.target: ExecutionTarget | None = None
        self.account: Callable[[], Mapping[str, object]] | None = None
        """The account's facts and basis as the node last read them, for the rows this unit
        writes. The runtime sets it at the host; a unit hosted without one stamps no account
        fact."""
        self.kept_values: dict[str, Decimal] = {}
        """The slow numbers the deployment's saved snapshot already holds, so a write happens
        only when one of them moves."""

    def account_inputs(self) -> Mapping[str, object]:
        """The account's facts and basis beside the size trail, so a row says what the account
        read.

        The sizer's own ``equity`` input is left exactly as the sizer read it, so a replayed row
        still reaches its quantity; the live account facts ride beside it under ``account.*``.
        """
        return {} if self.account is None else self.account()

    def stream_id(self, market: str) -> str:
        """The stream id that names this unit's stream and ``market`` (AD-25)."""
        return f"{self.stream}:{market}"

    def roll(self, market: str, base: QuoteBar) -> tuple[QuoteBar, ...]:
        """The stream bars ``market``'s base bar closes; none while its bucket is open.

        A feed whose bars are the unit's own, or a stream this node cannot name in seconds, passes
        the bar through: the parent's behaviour, kept for a venue that builds the unit's bars.
        """
        if self.base_ns is None or self.stream_seconds is None:
            return (base,)
        state = self.rolling.get(market)
        if state is None:
            state = self.rolling[market] = _Roll(self.stream_seconds, self.base_ns)
        rolled = state.add(base)
        return () if rolled is None else (rolled,)

    def start(
        self,
        equity: Decimal,
        target: ExecutionTarget,
        snapshot: Mapping[str, object] | None = None,
    ) -> Result[None]:
        """Host the unit: fresh through ``construct_unit``, or from ``snapshot`` through
        ``restore_unit``, which resumes it warm or starts it cold with the reason (A10)."""

        def host(surfaces: Mapping[str, Surface]) -> Result[HostedUnit]:
            own = _OwnJournal(self, surfaces["own_journal"])
            read = {**surfaces, "own_journal": own}
            scope = self.deployment.deployment_id
            built = (
                construct_unit(
                    self.compiled,
                    read_surfaces=read,
                    scope_id=scope,
                    execution_target=target,
                    assignment=self.assignment,
                )
                if snapshot is None
                else restore_unit(
                    snapshot,
                    self.compiled,
                    read_surfaces=read,
                    scope_id=scope,
                    execution_target=target,
                    assignment=self.assignment,
                )
            )
            if not is_refusal(built):
                self.hosted_unit = built.value
            return built

        self.target = target

        started = UnitSliceHandler.start(
            host,
            stream=self.compiled.plan.stream,
            records=self.records,
            bars={market: self.windows[(self.stream, market)] for market in self.records},
            opened_by=self.compiled.logic_fingerprint,
            equity=equity,
            execution=self._execution,
            journal=self._port,
            rates=self.rates,
            port=cast("HostPort | None", self.port),
        )
        if is_refusal(started):
            return started
        self.handler = started.value
        return Ok(None)

    @property
    def settled(self) -> bool:
        """Whether nothing of this unit is open or in flight at the venue, so it can be hosted
        again from its snapshot without losing a position the handler holds."""
        held = self.handler is not None and bool(self.handler.open_positions)
        return not (held or self._unknown or self.venue_open())

    def restore(self) -> Result[None]:
        """Host the unit again from its own snapshot (a heal of the runtime)."""
        if self.hosted_unit is None or self.target is None:
            return Ok(None)
        snapshot = self.hosted_unit.snapshot()
        return self.start(self.orders.venue.client.equity(), self.target, snapshot)

    def adopt(self, found: Iterable[Ours]) -> None:
        """Hold each position this deployment sent that the reconcile read open at the venue
        and this unit does not hold, as a process restart finds them: the unit manages its
        stop, its target and its exits as its own. A position that closed while the node was
        down is held too, so the handler books its trade on the next bar. A position is
        adopted once."""
        handler = self.handler
        client = self.orders.venue.client
        for ours in found:
            venue, send = ours.position, ours.send
            name, market = venue.position, venue.market_id
            if (
                handler is None
                or send.get("deployment_id") != self.deployment.deployment_id
                or market not in self.traded
                or name in self.placed
                or (client.closed(name) is not None and not ours.closed_while_down)
            ):
                continue
            side = Side(venue.side)
            entry_stop = Decimal(str(send["stop"]))
            position = OwnPosition(
                name,
                side,
                venue.quantity,
                venue.entry_price,
                self.compiled.logic_fingerprint,
                Instant(cast("int", send["sent_at_ns"])),
            )
            adopted = handler.adopt(
                market,
                position,
                stop=entry_stop if venue.stop is None else venue.stop,
                entry_stop=entry_stop,
                target=Decimal(str(send["target"])) if "target" in send else None,
                decision_row_id=str(send["decision_row_id"]),
            )
            if not is_refusal(adopted):
                self.placed[name] = (market, side, venue.entry_price)

    # --- names ---

    def client_order_id(self, decision_row_id: str, at: Instant) -> str:
        """``q<node tag>-<ULID>``: the ULID's time is the bar the unit decided on and its rest
        comes from the deployment and the decision row, so a re-run names the same order."""
        named = self.names.get(decision_row_id)
        if named is None:
            seed = f"{self.deployment.deployment_id}/{decision_row_id}"
            named = f"q{self.orders.tag}-{ulid(at.value_ns // 1_000_000, seed)}"
            self.names[decision_row_id] = named
        return named

    def venue_name(self, position_id: str) -> str:
        return self.venue_ids.get(position_id, position_id)

    @property
    def label(self) -> str:
        return f"qmx:{self.orders.tag}:{self.deployment.unit_id}"

    def instrument_scopes(self, market: str) -> tuple[str, str]:
        """Both scope keys that name ``market``: its market id, as the node shows it, and its
        record's symbol."""
        return f"instrument:{market}", f"instrument:{self.records[market].symbol}"

    @property
    def handled(self) -> UnitSliceHandler:
        return cast("UnitSliceHandler", self.handler)

    # --- the five hooks ---

    def update_stream(
        self, stream_id: str, observation: SliceObservation | None, frontier: Instant
    ) -> Result[None]:
        return self.handled.update_stream(stream_id, observation, frontier)

    def scheduled_position_event(self, stream_id: str, frontier: Instant) -> Result[None]:
        return self.handled.scheduled_position_event(stream_id, frontier)

    def execute_resting(
        self, intent: RestingIntent, observation: SliceObservation | None, frontier: Instant
    ) -> Result[bool]:
        if observation is None or not observation.closed:
            return Ok(False)
        if intent.intent_id in self._done:
            return Ok(True)
        placed = self._orders.get(intent.intent_id)
        wire = cast("Mapping[str, object]", intent.order)
        if isinstance(placed, Unknown):
            return Ok(False)
        if not isinstance(placed, Placed):
            reason = "warming up" if placed is None else placed.reason
            market = self.handled.market_of(intent.stream_id)
            if wire.get("intent_family") == "entry" and market is not None:
                self._port.append(
                    Skip(frontier, market, str(wire["decision_row_id"]), reason, Decimal(1))
                )
            self._done.add(intent.intent_id)
            return Ok(True)
        self._execution.price = placed.price
        done = self.handled.execute_resting(intent, observation, frontier, filled=placed.partial)
        self._execution.price = None
        if not is_refusal(done):
            self._done.add(intent.intent_id)
        return done

    def update_closed_data(
        self, stream_id: str, observation: SliceObservation, frontier: Instant
    ) -> Result[None]:
        return self.handled.update_closed_data(stream_id, observation, frontier)

    def mint_intents(self, stream_id: str, frontier: Instant) -> Result[object]:
        minted = self.handled.mint_intents(stream_id, frontier)
        if is_refusal(minted):
            return minted
        for intent in cast("tuple[RestingIntent, ...]", minted.value):
            if intent.intent_id not in self._orders and not self.warming:
                self._orders[intent.intent_id] = self.place(intent, frontier)
        return minted

    # --- the order path for one minted intent ---

    def place(self, intent: RestingIntent, at: Instant) -> Placed | Blocked:
        """Send one minted intent through the order path: an entry with its guards and its
        stop, an exit or a stop amendment for a position this unit holds."""
        wire = cast("Mapping[str, object]", intent.order)
        if wire.get("intent_family") == "entry":
            market = str(wire["market_id"])
            record = self.records[market]
            sized = lots(Decimal(str(wire["quantity"])), record)
            if is_refusal(sized):
                return Blocked(str(sized.context.get("reason")))
            row = str(wire["decision_row_id"])
            named = self.client_order_id(row, at)
            placed = self.orders.entry(
                deployment_id=self.deployment.deployment_id,
                client_order_id=named,
                label=self.label,
                wire=wire,
                record=record,
                quantity=sized.value,
                blocked_by=self.guard(market),
            )
            if isinstance(placed, Placed | Unprotected):
                self.placed[named] = (market, Side(str(wire["direction"])), placed.price)
            if isinstance(placed, Unknown):
                size = Decimal(sized.value.value).scaleb(-sized.value.scale)
                side = Side(str(wire["direction"]))
                self._unknown[named] = (intent.intent_id, market, side, size)
            return placed
        market = self.handled.market_of(intent.stream_id)
        if market is None:
            return Blocked("the intent names a stream this unit does not read")
        return self._exit(market, wire)

    def resolve(self, client_order_id: str, found: Found | None, *, protected: bool) -> bool:
        """Settle an entry whose outcome was unknown, from what the reconciler read at the
        venue: filled into ``found``'s position, which the unit holds under the venue's name and
        at the venue's quantity from the next closed bar, or never taken. A fill whose stop the
        venue does not hold is closed by the node, as any unprotected one."""
        pending = self._unknown.pop(client_order_id, None)
        if pending is None:
            return False
        intent_id, market, side, sent = pending
        self.orders.unknown.pop(client_order_id, None)
        if found is None:
            self._orders[intent_id] = Blocked(
                "venue answer unknown, and the venue never took the order: not sent again"
            )
            return True
        if found.position != client_order_id:
            self.at_venue[client_order_id] = found.position
        self.placed[found.position] = (market, side, found.price)
        if protected:
            filled = found.quantity
            partial = None if filled is None or filled == sent else filled
            self._orders[intent_id] = Placed(found.price, partial)
        else:
            self.orders.unprotected.add(found.position)
            self._orders[intent_id] = Unprotected(
                "the venue does not hold this order's stop", found.price
            )
        return True

    def _exit(self, market: str, wire: Mapping[str, object]) -> Placed | Blocked:
        parsed = parse_unit_intent(wire)
        if is_refusal(parsed) or not isinstance(parsed.value, UnitExitIntent):
            return Blocked("the venue cannot take this exit")
        exit_ = parsed.value
        held = self.handled.open_positions.get(market)
        if held is None or held.position_id != exit_.position_ref.position_id:
            return Blocked("the venue cannot close a position this unit did not open")
        position = self.venue_name(held.position_id)
        match exit_.action:
            case ClosePartial():
                return Blocked("the venue cannot close part of a position")
            case AmendProtection(stop=stop):
                new_stop = Decimal(stop.value).scaleb(-stop.scale)
                return self._amend(exit_, market, position, held, new_stop)
            case _:
                done = self.orders.close(position, market, held.side, held.entry_price, "unit")
                if not isinstance(done, Placed):
                    self.orders.unprotected.add(position)
                return done

    def _amend(
        self,
        exit_: UnitExitIntent,
        market: str,
        position: str,
        held: OwnPosition,
        new_stop: Decimal,
    ) -> Placed | Blocked:
        """A stop amendment goes to the venue only when it tightens the stop the venue holds."""
        current = self.orders.venue.client.stop_of(position)
        if current is None:
            return Blocked("the venue cannot amend a stop it does not hold")
        level = _price(current, exit_.position_ref.instrument)
        if is_refusal(level):
            return Blocked("the node cannot prove the held stop")
        tightens = check_amendment_tightens(
            exit_, direction=held.side.value, current_stop=level.value
        )
        if is_refusal(tightens):
            return Blocked("the amendment widens the stop, so the node refused it")
        return self.orders.amend(
            position, market, held.side, new_stop, held.entry_price, current, self.records[market]
        )

    def protective(self, market: str, held: HeldPosition, bar: QuoteBar) -> Reached | None:
        """What the venue did to a held position on this bar: its stop fired or the node
        closed it; else the target, which the node closes at the venue."""
        position = self.venue_name(held.position.position_id)
        closed = self.orders.venue.client.closed(position)
        if closed is not None:
            return Reached(closed.kind, closed.price, closed.gap)
        target = held.target
        if target is None:
            return None
        long = held.position.side is Side.LONG
        quote = bar.bid if long else bar.ask
        if ((quote.high if long else quote.low) - target) * (1 if long else -1) < 0:
            return None
        done = self.orders.close(position, market, held.position.side, target, "target")
        return Reached(FillKind.TARGET, done.price) if isinstance(done, Placed) else None

    def venue_open(self) -> dict[str, tuple[str, Side, Decimal]]:
        """This unit's positions still open at the venue, by client order id, whether or not
        the handler has booked their fill yet."""
        client = self.orders.venue.client
        return {name: held for name, held in self.placed.items() if client.closed(name) is None}

    # --- what he sees ---

    def positions(self) -> list[dict[str, object]]:
        if self.handler is None:
            return []
        shown: list[dict[str, object]] = []
        for market, position in self.handler.open_positions.items():
            name = self.venue_name(position.position_id)
            shown.append(
                {
                    "deployment_id": self.deployment.deployment_id,
                    "unit_id": self.deployment.unit_id,
                    "market_id": market,
                    "position": name,
                    "side": position.side.value,
                    "quantity": str(position.quantity),
                    "entry_price": str(position.entry_price),
                    "stop_at_venue": _text(self.orders.venue.client.stop_of(name)),
                }
            )
        return shown


def _text(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


# --- the runtime ----------------------------------------------------------------------------


class Phase(StrEnum):
    COMPILING = "compiling"
    WARMING = "warming up"
    TRADING = "trading"
    WAITING = "waiting"
    REFUSED = "refused"
    STOPPED = "stopped"


@dataclass
class _Hosted:
    deployment: Deployment
    phase: Phase
    detail: str = ""
    unit: NodeUnit | None = None
    loop: CommandStreamLoop | None = None
    compiling: Future[CompiledUnit | str] | None = None
    venue: Venue | None = None
    held_compile: CompiledUnit | None = None
    """The compiled unit, kept while its account's session is not up or not bound yet."""
    fault_roots: set[str] = field(default_factory=set[str])
    """Each root-cause key this deployment already filed a ``risk_event`` row, and so a card, for
    (AD-23). The same broken piece raising every tick lands one card, not one per tick."""


class _Sink:
    def emit(self, observation: object, /) -> SinkResult:
        del observation
        return Ok(SinkAck())

    def append(self, event: object, /) -> SinkResult:
        del event
        return Ok(SinkAck())


@dataclass
class _LoopClock:
    boot_epoch_id: str
    clock_ns: Callable[[], int]
    steady_ns: Callable[[], int]

    def wall_now(self) -> Result[Instant]:
        return Instant.try_create(self.clock_ns())

    def monotonic_now(self) -> Result[MonotonicReading]:
        return MonotonicReading.try_create(self.steady_ns(), self.boot_epoch_id)


Compile = Callable[[Deployment, Path], "CompiledUnit | str"]


def compile_staged(deployment: Deployment, folder: Path) -> CompiledUnit | str:
    """Read each staged file once and verify those bytes' fingerprint, then compile the
    deployment's unit from them through QML's one compiler, which checks every pin's
    fingerprint; answers the compiled unit or why it does not trade."""
    sources: dict[str, bytes] = {}
    entries: dict[str, bytes] = {}
    for item in deployment.files:
        path = staged_path(folder, item.path)
        if path is None:
            return f"staged file {item.path} is outside {folder.name}/"
        data = path.read_bytes()
        found = f"sha256:{hashlib.sha256(data).hexdigest()}"
        if found != item.fingerprint:
            return f"staged file {item.path} has fingerprint {found}, not {item.fingerprint}"
        pin = f"{item.entry_id}@{item.version}"
        if item.kind == "block":
            sources[pin] = data
        elif item.kind == "entry":
            entries[pin] = data
    records = deployment_records(deployment)
    if isinstance(records, str):
        return records
    compiled = compile_unit(
        deployment.unit_document,
        CompileContext(sources=sources, entries=entries, records=records),
    )
    if isinstance(compiled, CompiledUnit):
        return compiled
    why = compiled[0].message if compiled else "no problem named"
    return f"the unit did not compile: {why}"


def deployment_records(deployment: Deployment) -> dict[str, InstrumentRecord] | str:
    """Each of the unit's markets' instrument record, from the deployment's snapshots."""
    by_symbol: dict[tuple[str, str], InstrumentRecord] = {}
    for snapshot in deployment.snapshots:
        parsed = parse_record(snapshot)
        if not is_refusal(parsed):
            by_symbol[(parsed.value.venue, parsed.value.symbol)] = parsed.value
    found: dict[str, InstrumentRecord] = {}
    markets = deployment.unit_document.get("markets")
    for market in cast(
        "Sequence[Mapping[str, object]]", markets if isinstance(markets, list) else ()
    ):
        ref = cast("Mapping[str, object]", market.get("instrument_ref", {}))
        record = by_symbol.get((str(ref.get("venue")), str(ref.get("symbol"))))
        if record is None:
            return f"the deployment holds no record snapshot for {market.get('market_id')}"
        found[str(market["market_id"])] = record
    return found


def starting_assignment(deployment: Deployment, compiled: CompiledUnit) -> dict[str, Decimal] | str:
    """The calibrated numbers the deployment starts from, or why one does not read as a number.
    Every other number the document lists is fixed in the compiled plan its G record tested."""
    found: dict[str, Decimal] = {}
    for slow in compiled.plan.slow:
        given = deployment.starting.get(slow.number.name)
        if given is None:
            continue
        try:
            found[slow.number.name] = Decimal(str(given))
        except InvalidOperation:
            return f"the starting value of {slow.number.name} is not a number: {given}"
    return found


def journalled_resumes(root: Path) -> set[str]:
    """The op id of each resume the node journal already holds a row for, so a restart lands no
    second row and still lands the row of a resume it missed. A folder the volume refuses reads
    as holding none: a repeated row is better than a resume nobody can see."""
    found: set[str] = set()
    for folder in stream_folders(root):
        if not folder.name.startswith(f"{JournalStream.NODE.source}.kill_level."):
            continue
        lines = read_committed(folder)
        if is_refusal(lines):
            continue
        for line in lines.value:
            if isinstance(line, JournalLine):
                body = cast("Mapping[str, object]", line.record.get("body", {}))
                if isinstance(body.get("op_id"), str):
                    found.add(str(body["op_id"]))
    return found


def journalled_flattens(root: Path) -> Result[set[str]]:
    """The op id of each flatten the node journal holds as done, so a restart never replays an
    old flatten on new positions. A folder the volume refuses answers the refusal: reading it as
    holding none would close positions he opened since, so the op waits for a read that works."""
    found: set[str] = set()
    for folder in stream_folders(root):
        if not folder.name.startswith(f"{JournalStream.NODE.source}.kill_level."):
            continue
        lines = read_committed(folder)
        if is_refusal(lines):
            return lines
        for line in lines.value:
            if isinstance(line, JournalLine):
                body = cast("Mapping[str, object]", line.record.get("body", {}))
                if isinstance(body.get("op_id"), str):
                    found.add(str(body["op_id"]))
    return Ok(found)


@dataclass(frozen=True, slots=True)
class _Open:
    """One position of this node open at the venue, whether a unit holds it or not."""

    name: str
    market: str
    side: Side
    entry: Decimal
    path: OrderPath
    scopes: frozenset[str]
    """Every scope key that names it."""


class Runtime:
    """The node's runtime thread over its store, its journal and its venue bindings."""

    def __init__(
        self,
        context: Context,
        journal: JournalWriter,
        venues: Mapping[str, Venue],
        *,
        machine: str,
        build: str,
        clock_ns: Callable[[], int],
        steady_ns: Callable[[], int],
        sleep: Callable[[float], None],
        boot_epoch_id: str,
        compile: Compile = compile_staged,
        tick_s: float = RECONCILE_TICK_S,
    ) -> None:
        self.context = context
        self.journal = journal
        self.venues = dict(venues)
        self.machine = machine
        self.build = build
        self.clock_ns = clock_ns
        self.steady_ns = steady_ns
        self.sleep = sleep
        self.boot_epoch_id = boot_epoch_id
        self.compile = compile
        self.tick_s = tick_s
        self.hosted: dict[str, _Hosted] = {}
        self.alarms: list[Mapping[str, object]] = []
        self.applied: dict[str, KsaLevel] = {}
        self._accounts: dict[str, LiveAccount] = {}
        self._facts: dict[str, AccountFacts] = {}
        """Each account's facts as the last refresh read them, by account id."""
        self._resumes_seen = journalled_resumes(context.journal_root)
        self._flattened: set[str] | None = None
        """Every flatten op journalled done; None until the journal could be read."""
        self._flat_closed: dict[str, int] = {}
        self._paths: dict[str, OrderPath] = {}
        self._compiler = ThreadPoolExecutor(max_workers=1, thread_name_prefix="node-compile")
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._shown: dict[str, str] = {}
        self._target = Target()
        self.board = BoardFeed(context.data / BOARD_FEED, clock_ns)
        self.paused_by_black = False
        self.reconciler = Reconciler(
            journal, context.journal_root, context.standing().tag, clock_ns, self.alarms.append
        )
        # Imported here: alarms reads this module's deployment records at import time.
        from qmn.app.alarms import market_hours  # noqa: PLC0415

        self.stand_downs = StandDowns(
            journal,
            journal_root=context.journal_root,
            machine=machine,
            build=build,
            boot_epoch_id=boot_epoch_id,
            clock_ns=clock_ns,
            free_bytes=lambda: shutil.disk_usage(context.data).free,
            on_alarm=self.alarms.append,
            clock_offset_ns=lambda: clock_offset(context.data.parent / HOST_FACTS, clock_ns()),
            market_open=market_hours(context.store),
        )
        self._paper_journal: JournalWriter | None = None
        waiting = restored(context.journal_root)
        if is_refusal(waiting):
            self.stand_down(
                Kind.REPEATED_FAULT,
                "all",
                "the node could not read its journals at start, so it cannot prove which"
                " stand-downs it held",
            )
        else:
            self.stand_downs.adopt(waiting.value)
        self.healer = Healer(
            context.store,
            journal,
            clock_ns=clock_ns,
            boot_epoch_id=boot_epoch_id,
            max_restarts=REPEATED_FAULT_RESTARTS,
            window_ns=REPEATED_FAULT_WINDOW_NS,
        )
        counted = self.healer.fold.evaluate(now_ns=clock_ns())
        if counted.threshold_breached:
            last = self.healer.fold.stamps[-1].reason
            self._repeated_fault_down(counted.counted_boots, str(last))
        self.watch = StuckWatch(
            steady_ns=steady_ns,
            alive=self._alive,
            before_exit=self.healer.exit_record,
        )
        self._recovering = False

    # --- the thread, under the inner supervisor ---

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="node-runtime", daemon=True)
        self._thread.start()
        watching = threading.Thread(
            target=self.watch.run, args=(self._stop,), name="node-watchdog", daemon=True
        )
        watching.start()

    def _alive(self) -> bool:
        thread = self._thread
        return self._stop.is_set() or thread is None or thread.is_alive()

    def wake(self) -> None:
        self._wake.set()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
        self._compiler.shutdown(wait=False, cancel_futures=True)
        self.stand_downs.close()
        if self._paper_journal is not None:
            self._paper_journal.close()

    def _run(self) -> None:
        while not self._stop.is_set():
            self.step()
            self._wake.wait(self.tick_s)
            self._wake.clear()

    def step(self) -> None:
        """One pass of the runtime thread under the inner supervisor: a tick, or, after the
        tick raised, a heal. A heal waits its back-off and starts the runtime again over the
        same hosted units, which hold the node's record of what is open at the venue."""
        self._wake.clear()
        self.watch.began = self.steady_ns()
        try:
            if self._recovering:
                self._recover()
            self.tick()
        except Exception as error:
            self.watch.began = None
            self._heal(repr(error))
            return
        self.watch.began = None
        if self.healer.healing is not None and self._back():
            self.healer.healed()
            self._observe()

    def _heal(self, why: str) -> None:
        print(json.dumps({"event": "runtime_error", "error": why}), file=sys.stderr)
        fault = self.healer.fault(why)
        if fault.breached:
            self._repeated_fault_down(fault.restarts, why)
        try:
            self._observe()
        except Exception as error:  # the store may be what failed; the heal goes on
            print(json.dumps({"event": "observe_failed", "error": repr(error)}), file=sys.stderr)
        self._wait(fault.wait_s)
        self._recovering = True

    def _repeated_fault_down(self, restarts: int, why: str) -> None:
        """Past the crash-loop threshold the node stands down alive until his resume."""
        minutes = REPEATED_FAULT_WINDOW_NS // 60_000_000_000
        cause = f"{restarts} restarts in {minutes} minutes"
        if self.stand_down(Kind.REPEATED_FAULT, "all", cause):
            self.alarms.append(
                {
                    "alarm": "repeated_fault",
                    "restarts": restarts,
                    "action": "no_new_entries",
                    "why": f"{cause}, the last: {why}",
                }
            )

    def _wait(self, seconds: float) -> None:
        """The back-off before a heal, slept a tick at a time so his kill, any other wake and
        a stop end it early."""
        left = round(seconds * 1000)
        tick = max(1, round(self.tick_s * 1000))
        while left > 0 and not (self._wake.is_set() or self._stop.is_set()):
            step = min(tick, left)
            self.sleep(step / 1000)
            left -= step

    def _recover(self) -> None:
        """Start the runtime again: every account reconciles before its next entry, and each
        unit with nothing open or in flight is hosted again from its own snapshot. The kill
        level, the pauses and every stand-down are carried as they were."""
        self._recovering = False
        self.healer.restarted()
        self.reconciler = Reconciler(
            self.journal,
            self.context.journal_root,
            self.context.standing().tag,
            self.clock_ns,
            self.alarms.append,
            healed=True,
        )
        for hosted in self.hosted.values():
            unit = hosted.unit
            if unit is not None and unit.settled:
                restarted = unit.restore()
                if is_refusal(restarted):
                    hosted.phase = Phase.STOPPED
                    hosted.detail = f"the unit would not start again ({restarted.category.value})"

    def _back(self) -> bool:
        """Trading again after a heal: every ready account reconciled, every unit compiled
        and warmed up."""
        for account, venue in self.venues.items():
            if venue.feed.ready and self.reconciler.due(account, venue.feed.reconnects, {}):
                return False
        return all(h.phase not in (Phase.COMPILING, Phase.WARMING) for h in self.hosted.values())

    def safe_to_restart(self) -> dict[str, Json]:
        """Whether a restart now loses nothing (Part C AD-315), with each reason it would."""
        reasons: list[Json] = []
        if self.healer.healing is not None:
            reasons.append("the node is healing")
        units = [hosted.unit for hosted in self.hosted.values() if hosted.unit is not None]
        paths = {id(path): path for path in self._paths.values()}
        paths.update((id(unit.orders), unit.orders) for unit in units)
        for path in paths.values():
            reasons.extend(
                f"order {name} is in flight: the venue's answer is unknown"
                for name in sorted(path.unknown)
            )
        for unit in units:
            client = unit.orders.venue.client
            reasons.extend(
                f"position {name} has no stop at the venue"
                if client.stop_of(name) is None
                else f"position {name} is open at the venue"
                for name in sorted(unit.venue_open())
            )
        for account, venue in self.venues.items():
            if venue.feed.ready and self.reconciler.due(account, venue.feed.reconnects, {}):
                reasons.append(f"account {account} is not reconciled")
            reasons.extend(
                f"position {orphan.position.position} of ours is open and no unit holds it"
                for orphan in self._orphans(account, venue)
            )
        reasons.extend(
            f"{held.row.word.value} at {held.scope} is held in memory only: no journal took it"
            for held in self.stand_downs.in_memory_only()
        )
        return {"ok": not reasons, "reasons": reasons}

    # --- one reconcile pass ---

    def tick(self) -> None:
        standing = self.context.standing()
        accepted = self.context.store.accepted()
        target = Target.fold(accepted)
        self._target = target
        if standing.mismatch:
            for hosted in self.hosted.values():
                hosted.phase, hosted.detail = Phase.WAITING, "the node's identity is unconfirmed"
            self._observe()
            return
        tried = self._kill(target)
        self._flatten(target, accepted, tried)
        self._protect(tried)
        self._journal_resumes(accepted)
        self._deployments(target)
        faulted = self._repeated_fault()
        self.stand_downs.resumes(accepted)
        if faulted and not self._repeated_fault():
            self.healer.reset()
        self.stand_downs.settle()
        self.stand_downs.watch_node()
        for account, venue in self.venues.items():
            bars = venue.feed.pump()
            self.stand_downs.watch_feed(account, venue.feed)
            self._reconcile(account, venue)
            if bars:
                self._drive(venue, bars)
        self._refresh_accounts()
        self._observe()

    # --- the account's facts: a timed re-read, and the surface it leaves ---------------------

    def _account_source(self, account: str, venue: Venue) -> LiveAccount:
        """The account's fact surface, built once per binding.

        The currency is the labelled default until a real account is bound: cTrader states its
        deposit asset by id, and nothing on this node turns that id into a name (G-DEMO reads it
        from the demo account). The binding is asked for at every refresh, so the client under
        the venue is the one read, never a copy taken here. The basis names the conformance
        double when that is the client, so a row written on the fake never says the venue.
        """
        source = self._accounts.get(account)
        if source is None:
            supplied_by = (
                "the fake conformance double"
                if isinstance(venue.client, ConformanceAccount)
                else "the venue"
            )
            source = LiveAccount(
                lambda venue=venue: venue.client,
                currency=ACCOUNT_CURRENCY,
                budget_share=BUDGET_SHARE,
                supplied_by=supplied_by,
            )
            self._accounts[account] = source
        return source

    def _refresh_accounts(self) -> None:
        """The one place the timed balance re-read runs: after the pass that drove every unit.

        A row written inside that pass reads what this left, so no exit and no row write can start
        a venue round trip. The account's facts are re-stated only when the read's timer is due, so
        the stops they carry are asked of the unit's own binding at the read's cadence, not on
        every tick.
        """
        now = Instant(self.clock_ns())
        for account, venue in self.venues.items():
            source = self._account_source(account, venue)
            if source.refresh(now) or account not in self._facts:
                self._facts[account] = source.read(
                    now,
                    stakes=self._stakes(account, now),
                    realised_since=self._realised(account, now),
                )

    def account_facts(self, account: str) -> AccountFacts | None:
        """The account's facts as the last refresh left them, or None before the first read."""
        return self._facts.get(account)

    def _account_inputs(self, account: str) -> Mapping[str, object]:
        """The account's facts by their names and its basis, for a decision row the units of
        ``account`` write."""
        facts = self._facts.get(account)
        if facts is None:
            return {}
        return {**facts.facts(), account_name("basis"): facts.basis}

    def _stakes(self, account: str, instant: Instant) -> tuple[Stake, ...]:
        """Every position a unit on ``account`` holds, at the money it loses if its stop fills.

        The stop is the one the unit's own binding carries: the venue's for a live lane, the paper
        lane's own for a paper one. A stake with no stop is kept, so open risk reads absent rather
        than short.
        """
        stakes: list[Stake] = []
        for hosted in self.hosted.values():
            unit = hosted.unit
            if unit is None or hosted.deployment.account_id != account:
                continue
            sized = _unit_account(unit, instant)
            handler = unit.handler
            held: Mapping[str, OwnPosition] = {} if handler is None else handler.open_positions
            for market, position in held.items():
                record = unit.records.get(market)
                if record is None or sized is None:
                    continue
                stop = unit.orders.venue.client.stop_of(unit.venue_name(position.position_id))
                stakes.append(
                    Stake(
                        position.entry_price,
                        stop,
                        position.quantity,
                        record.value_per_point,
                        rate_used(record, sized, instant),
                    )
                )
        return tuple(stakes)

    def _realised(self, account: str, instant: Instant) -> Decimal | None:
        """The money the units on ``account`` have closed since this node hosted them.

        Each closed trade's quote figure at the rate the row stamped, as the handler's own equity
        sum converts it; a trade with no rate takes the current fact for its quote, and a quote
        this node cannot price makes the figure absent rather than short. A restart re-anchors
        it: these are the trades the handler holds, and the unit's journal keeps the record.
        """
        total = Fraction(0)
        for hosted in self.hosted.values():
            unit = hosted.unit
            if unit is None or hosted.deployment.account_id != account or unit.handler is None:
                continue
            sized = _unit_account(unit, instant)
            for trade in unit.handler.trades:
                rate = trade.rate
                if rate is None:
                    record = unit.records.get(trade.market_id)
                    fact = (
                        None
                        if record is None or sized is None
                        else rate_used(record, sized, instant)
                    )
                    if fact is None or fact.value is None:
                        return None
                    rate = Fraction(fact.value)
                total += Fraction(trade.money) * rate
        return Decimal(total.numerator) / Decimal(total.denominator)

    def _reconcile(self, account: str, venue: Venue) -> None:
        """Reconcile once per venue session and after an UNKNOWN, before any bar is driven."""
        path = self._paths.get(account)
        unknown = {} if path is None else path.unknown
        units = [
            hosted.unit
            for hosted in self.hosted.values()
            if hosted.unit is not None and hosted.deployment.account_id == account
        ]
        if venue.feed.ready and self.reconciler.due(account, venue.feed.reconnects, unknown):
            kept = frozenset(
                hosted.deployment.deployment_id
                for hosted in self.hosted.values()
                if hosted.deployment.account_id == account
            )
            self.reconciler.run(account, venue.feed.reconnects, venue.client, unknown, units, kept)
        for unit in units:
            unit.adopt(self.reconciler.mine(account))
        if venue.feed.ready and not self.reconciler.due(account, venue.feed.reconnects, unknown):
            self._restore_stops(account, units)

    def _restore_stops(self, account: str, units: Sequence[NodeUnit]) -> None:
        """Put back each stop the venue no longer holds on a position a unit holds, or close it
        with the alarm, before any bar is driven. It walks every tick and not only at adoption:
        ``adopt`` runs from a snapshot and skips a name it holds, a unit may compile after the
        reconcile, and a stop can go during a dropped connection. The level is the entry's send
        row, the one ``adopt`` gives the handler."""
        for unit in units:
            client = unit.orders.venue.client
            missing = {
                name: held
                for name, held in unit.venue_open().items()
                if name not in unit.orders.unprotected and client.stop_of(name) is None
            }
            if not missing:
                continue
            read = journal_sends(self.context.journal_root)
            sends = {} if is_refusal(read) else dict(read.value)
            sends.update((o.position.position, o.send) for o in self.reconciler.mine(account))
            for name, (market, side, entry) in missing.items():
                stop = sends.get(name, {}).get("stop")
                unit.orders.restore_stop(
                    name,
                    market,
                    side,
                    None if stop is None else Decimal(str(stop)),
                    entry,
                    unit.records[market],
                )

    def _orphans(self, account: str, venue: Venue) -> list[Ours]:
        """The node's own positions the reconcile read open on ``account`` that no hosted unit
        holds and the venue has not closed since."""
        held = {
            name for hosted in self.hosted.values() if hosted.unit for name in hosted.unit.placed
        }
        return sorted(
            (
                ours
                for ours in self.reconciler.mine(account)
                if ours.position.position not in held
                and venue.client.closed(ours.position.position) is None
            ),
            key=lambda ours: ours.position.position,
        )

    def _mine(self) -> list[_Open]:
        """Every position of this node open at the venue. A unit's own list holds what opened
        since the last reconcile, and paper; the orphans add what no unit holds. Only the
        reconcile's ``Claim.MINE`` positions ever join, so a position not ours is never here."""
        found = [
            _Open(
                name,
                market,
                side,
                entry,
                unit.orders,
                frozenset(
                    {
                        "all",
                        f"deployment_id:{hosted.deployment.deployment_id}",
                        f"account:{hosted.deployment.account_id}",
                        *unit.instrument_scopes(market),
                    }
                ),
            )
            for hosted in self.hosted.values()
            if (unit := hosted.unit) is not None
            for name, (market, side, entry) in unit.venue_open().items()
        ]
        for account, venue in self.venues.items():
            for orphan in self._orphans(account, venue):
                position = orphan.position
                found.append(
                    _Open(
                        position.position,
                        position.market_id,
                        Side(position.side),
                        position.entry_price,
                        cast("OrderPath", self._path(account)),
                        frozenset(
                            {
                                "all",
                                f"deployment_id:{orphan.send.get('deployment_id')}",
                                f"account:{account}",
                                *same_market(
                                    self._target.deployments, f"instrument:{position.market_id}"
                                ),
                            }
                        ),
                    )
                )
        return found

    def close_scope(self, deployment_id: str, why: str) -> int:
        """The last fall-through for one deployment: close every position at its scope whose
        unit's own exits could not run, with the reason it gives (AD-13, AD-23 step 4)."""
        return self._close_scope(f"deployment_id:{deployment_id}", why, set())

    def _close_scope(self, scope: str, why: str, tried: set[str], *, every: bool = False) -> int:
        """Close every position of this node at ``scope``, or all of them with ``every``;
        answers how many the venue closed now. A position already tried this tick waits."""
        closed = 0
        for held in self._mine():
            if held.name in tried or not (every or scope in held.scopes):
                continue
            tried.add(held.name)
            done = held.path.close(held.name, held.market, held.side, held.entry, why)
            closed += isinstance(done, Placed)
        return closed

    def _path(self, account: str) -> OrderPath | None:
        venue = self.venues.get(account)
        if venue is None:
            return None
        if account not in self._paths:
            self._paths[account] = OrderPath(
                tag=self.context.standing().tag,
                venue=venue,
                journal=self.journal,
                clock_ns=self.clock_ns,
                sleep=self.sleep,
                on_alarm=self.alarms.append,
                session_epoch=f"{self.boot_epoch_id}-{account}",
            )
        return self._paths[account]

    # --- the kill switch: escalate-only, his resume brings it down ---

    def level_for(self, hosted: _Hosted, market: str | None = None) -> tuple[KsaLevel, str]:
        deployment = hosted.deployment
        scopes = [
            "all",
            f"deployment_id:{deployment.deployment_id}",
            f"account:{deployment.account_id}",
        ]
        if market is not None and hosted.unit is not None:
            scopes.extend(hosted.unit.instrument_scopes(market))
        held = [(self._target.kills.get(scope, KsaLevel.GREEN), scope) for scope in scopes]
        return max(held, key=lambda pair: LEVEL_RANK[pair[0]])

    def _kill(self, target: Target) -> set[str]:
        """Apply every kill level in force; answers the positions a close was sent for.

        A level that rises is journalled once. While a scope holds a level that closes
        positions, its closes are sent again on every tick for each covered position still
        open at the venue, so one refused close is never the last."""
        for scope in list(self.applied):
            if target.kills.get(scope, KsaLevel.GREEN) is KsaLevel.GREEN:
                del self.applied[scope]
        self.paused_by_black = any(level is KsaLevel.BLACK for level in target.kills.values())
        tried: set[str] = set()
        for scope, level in target.kills.items():
            rises = LEVEL_RANK[level] > LEVEL_RANK[self.applied.get(scope, KsaLevel.GREEN)]
            if rises:
                self.applied[scope] = level
            held = self.applied.get(scope)
            if held is None:
                continue
            effect = PLACEHOLDER_KILL_EFFECTS[held]
            closed = self._enact(scope, effect, tried)
            if not rises:
                continue
            body: dict[str, object] = {
                "scope": scope,
                **effect.document(),
                "positions_closed": closed,
                # The node sends market entries only, so no entry order of its rests to cancel.
                "resting_entries_cancelled": 0,
            }
            self.journal.append(
                "kill_level", body, RowFacts(ts_recv=self.clock_ns(), clock_ok=False)
            )
        return tried

    def _journal_resumes(self, accepted: Sequence[Change]) -> None:
        """One ``kill_level`` row per resume he sent, beside the rises, naming the kills it
        cleared. It is keyed by its op id and read back at start, so it lands once across a
        restart, and a row the journal refuses is tried again on the next tick."""
        for index, change in enumerate(accepted):
            if (
                change.kind != "resume"
                or change.outcome is not Outcome.ACCEPTED
                or change.op_id in self._resumes_seen
            ):
                continue
            scope = str(change.args["scope"])
            before = Target.fold(accepted[:index])
            named = same_market(before.deployments, scope)
            body: dict[str, object] = {
                "scope": scope,
                **PLACEHOLDER_KILL_EFFECTS[KsaLevel.GREEN].document(),
                "positions_closed": 0,
                "resting_entries_cancelled": 0,
                "op_id": change.op_id,
                "cleared": sorted(cleared_by(before.kills, scope, named)),
            }
            written = self.journal.append(
                "kill_level", body, RowFacts(ts_recv=self.clock_ns(), clock_ok=False)
            )
            if not is_refusal(written):
                self._resumes_seen.add(change.op_id)

    def _enact(self, scope: str, effect: KillEffect, tried: set[str]) -> int:
        if not (effect.close_positions or effect.close_all_and_pause):
            return 0
        why = f"kill-{effect.level.value.lower()}"
        return self._close_scope(scope, why, tried, every=effect.close_all_and_pause)

    def _flatten(self, target: Target, accepted: Sequence[Change], tried: set[str]) -> None:
        """Close each flatten's scope until it reads flat, then write the op's done row: a
        ``kill_level`` row with no ``level``, which reads as neither a kill nor a clear. The row
        is read back at start, so a restart never replays it on new positions, and a journal
        that cannot be read holds every op unacted."""
        if self._flattened is None:
            read = journalled_flattens(self.context.journal_root)
            if is_refusal(read):
                return
            self._flattened = read.value
        for op_id, scope in target.flattens.items():
            if op_id in self._flattened:
                continue
            closed = self._flat_closed.get(op_id, 0) + self._close_scope(scope, "flatten", tried)
            self._flat_closed[op_id] = closed
            if not self._reads_flat(scope, accepted):
                continue
            written = self.journal.append(
                "kill_level",
                {"op_id": op_id, "scope": scope, "positions_closed": closed},
                RowFacts(ts_recv=self.clock_ns(), clock_ok=False),
            )
            if not is_refusal(written):
                self._flattened.add(op_id)

    def _reads_flat(self, scope: str, accepted: Sequence[Change]) -> bool:
        """Whether the broker is proved to hold nothing of this node at ``scope``: every account
        he kept bound that the scope may reach is bound now, its session is up and reconciled,
        and no entry's answer is unknown. An empty view proves nothing, because a restart sees
        no position until its first reconcile."""
        kept = {
            str(change.args["account"]): change.args["action"]
            for change in accepted
            if change.kind == "bind"
        }
        accounts = {name for name, action in kept.items() if action == "add"} | set(self.venues)
        for account in accounts:
            if scope.startswith("account:") and scope != f"account:{account}":
                continue
            venue = self.venues.get(account)
            path = self._paths.get(account)
            unknown = {} if path is None else path.unknown
            if (
                venue is None
                or unknown
                or not venue.feed.ready
                or self.reconciler.due(account, venue.feed.reconnects, unknown)
            ):
                return False
        return not any(scope in held.scopes for held in self._mine())

    def _protect(self, tried: set[str]) -> None:
        """Close again each position the venue filled without holding its stop, until the
        venue shows it closed; a position a kill close was sent for this tick waits."""
        for hosted in self.hosted.values():
            unit = hosted.unit
            if unit is None:
                continue
            for position, (market, side, price) in unit.venue_open().items():
                if position in unit.orders.unprotected and position not in tried:
                    unit.orders.close(position, market, side, price, "protection")

    def guard(self, hosted: _Hosted) -> Callable[[str], str | None]:
        """Why an entry on ``market`` may not go now, or None (Level 0 AD-39 step 2)."""

        def check(market: str) -> str | None:
            level, scope = self.level_for(hosted, market)
            if LEVEL_RANK[level] >= LEVEL_RANK[KsaLevel.YELLOW]:
                return f"the kill switch is at {level.value} for {scope}"
            if self.paused_by_black:
                return "the kill switch is at BLACK, so the node is paused"
            for scope_key in (
                "all",
                f"deployment_id:{hosted.deployment.deployment_id}",
                f"account:{hosted.deployment.account_id}",
                *(hosted.unit.instrument_scopes(market) if hosted.unit else ()),
            ):
                if self._target.paused.get(scope_key):
                    return f"paused at {scope_key}"
            if hosted.deployment.deployment_id in self._target.withdrawn:
                return "the deployment is withdrawn, so it takes no new entry"
            if hosted.unit is not None and hosted.unit.journal.write_failure is not None:
                return "the node journal could not be written"
            placed = self.board_read(hosted)
            if placed is not None and market in placed.held_back:
                placement = cast("Placement", hosted.deployment.placement)
                word = placed.held_back[market]
                return f"the board does not favour {market} now ({placement.reading} is {word})"
            venue = hosted.venue
            if venue is None or not venue.feed.ready:
                reason = "no session" if venue is None else venue.feed.reason
                return f"venue not ready: {reason}"
            held_by_reconcile = self.reconciler.holds(
                hosted.deployment.account_id, venue.feed.reconnects
            )
            if held_by_reconcile is not None:
                return held_by_reconcile
            for orphan in self._orphans(hosted.deployment.account_id, venue):
                if orphan.position.market_id == market:
                    return (
                        f"a position of ours that no unit holds is open on {market}:"
                        f" {orphan.position.position}"
                    )
            held = self.stand_downs.blocking(
                (
                    "all",
                    f"account:{hosted.deployment.account_id}",
                    f"instrument:{market}",
                    *(hosted.unit.instrument_scopes(market) if hosted.unit else ()),
                    f"unit:{hosted.deployment.deployment_id}:{market}",
                )
            )
            return None if held is None else f"{held.row.blocks} ({held.cause})"

        return check

    def board_read(self, hosted: _Hosted) -> BoardRead | None:
        """What the deployment's placement read sees now over the unit's markets, or None when
        it has no placement read."""
        placement = hosted.deployment.placement
        if placement is None or hosted.unit is None:
            return None
        return self.board.read(placement, hosted.unit.traded)

    # --- stand-downs that wait for him ---

    def _repeated_fault(self) -> bool:
        return any(held.kind is Kind.REPEATED_FAULT for held in self.stand_downs.held.values())

    def stand_down(self, kind: Kind, scope: str, cause: str) -> bool:
        """Hold a stand-down that waits for him (a repeated fault, a spec change) at ``scope``;
        True when it was not already held. His resume reaches it by either name of its market."""
        deployments = Target.fold(self.context.store.accepted()).deployments
        return self.stand_downs.hold(kind, scope, cause, covers=same_market(deployments, scope))

    def risk_stop(self, deployment_id: str, market_id: str, rule: str, reason: str) -> str | None:
        """A risk rule stops a hosted unit on one market (standing order 7): one ``lifecycle``
        event by ``risk_rule``, and no entry there until his resume. Answers its event id, or
        None when the deployment is not trading or the row could not be written; the stop holds
        in the second case, with an alarm."""
        hosted = self.hosted.get(deployment_id)
        unit = None if hosted is None else hosted.unit
        if hosted is None or unit is None or market_id not in unit.traded:
            return None
        deployment = hosted.deployment
        subject = Subject(
            deployment_id,
            deployment.unit_id,
            unit.compiled.document_fingerprint.value,
            unit.compiled.compiled_fingerprint.value,
            market_id,
            deployment.lane,
            unit.journal_world,
        )
        covers = (
            f"deployment_id:{deployment_id}",
            f"account:{deployment.account_id}",
            *unit.instrument_scopes(market_id),
        )
        return self.stand_downs.risk_stop(subject, rule, reason, covers=covers)

    # --- deployments: compile after the answer, then warm up, then trade ---

    def _deployments(self, target: Target) -> None:
        for deployment_id, change in target.deployments.items():
            if deployment_id in self.hosted:
                continue
            document = cast("Mapping[str, object]", change.args.get("document") or {})
            try:
                deployment = parse_deployment(document)
            except ValueError as error:
                self.hosted[deployment_id] = _Hosted(
                    _placeholder(deployment_id), Phase.REFUSED, str(error)
                )
                continue
            folder = staging_folder(self.context.data, deployment_id)
            hosted = _Hosted(deployment, Phase.COMPILING, "compiling after the answer")
            hosted.compiling = self._compiler.submit(self.compile, deployment, folder)
            self.hosted[deployment_id] = hosted
        for hosted in self.hosted.values():
            compiling = hosted.compiling
            if hosted.phase is Phase.COMPILING and compiling is not None and compiling.done():
                self._host(hosted, compiling.result())
            elif hosted.phase is Phase.WAITING and hosted.held_compile is not None:
                self._host(hosted, hosted.held_compile)
            withdrawn = hosted.deployment.deployment_id in target.withdrawn
            if withdrawn and hosted.unit is not None and not hosted.unit.venue_open():
                hosted.phase, hosted.detail = Phase.STOPPED, "withdrawn and flat"

    def _host(self, hosted: _Hosted, compiled: CompiledUnit | str) -> None:
        deployment = hosted.deployment
        hosted.compiling = None
        if isinstance(compiled, str):
            hosted.phase, hosted.detail = Phase.REFUSED, compiled
            return
        wrong = _other_version(compiled, deployment)
        if wrong is not None:
            hosted.phase, hosted.detail = Phase.REFUSED, wrong
            return
        venue = self.venues.get(deployment.account_id)
        if venue is None:
            hosted.phase = Phase.WAITING
            hosted.detail = f"no venue binding holds account {deployment.account_id}"
            hosted.held_compile = compiled
            return
        live = deployment.lane == "live"
        if live and venue.client.account.role is not AccountRole.DEMO:
            hosted.phase = Phase.REFUSED
            hosted.detail = "a live lane trades only on a demo binding until a live one is bound"
            return
        seconds, account_bar = stream_seconds(compiled.plan.stream), venue.client.bar_size_ns()
        if seconds is not None and account_bar is not None and (seconds * _NS) % account_bar:
            hosted.phase = Phase.REFUSED
            hosted.detail = (
                f"the unit reads {compiled.plan.stream} bars and this account's feed builds"
                f" {_bar_name(account_bar)} bars that do not divide it"
            )
            return
        if self._widen(venue, deployment):
            hosted.phase, hosted.detail = Phase.WAITING, "waiting for its account's session"
            hosted.held_compile = compiled
            return
        if not venue.feed.ready:
            hosted.phase, hosted.detail = Phase.WAITING, "waiting for its account's session"
            hosted.held_compile = compiled
            return
        untradeable = next(
            (
                why
                for market in deployment.markets
                if (why := venue.client.unauthorised(market)) is not None
            ),
            None,
        )
        if untradeable is not None:
            hosted.phase, hosted.detail = Phase.REFUSED, untradeable
            return
        netted = self._netted(venue, deployment)
        if netted is not None:
            hosted.phase, hosted.detail = Phase.REFUSED, netted
            return
        hosted.held_compile = None
        path = self._path(deployment.account_id) if live else self._paper_path(hosted, venue)
        if path is None:
            hosted.phase, hosted.detail = Phase.REFUSED, "the paper lane's journal would not open"
            return
        records = deployment_records(deployment)
        if isinstance(records, str):
            hosted.phase, hosted.detail = Phase.REFUSED, records
            return
        world = JournalWorld.DEMO if live else JournalWorld.PAPER
        journal = RunJournal.open_live(
            self.context.journal_root,
            compiled,
            scope_id=deployment.deployment_id,
            world=world,
            machine=self.machine,
            role=ROLE,
            build=self.build,
            boot_epoch_id=self.boot_epoch_id,
            account=deployment.account_id,
        )
        if is_refusal(journal):
            hosted.phase, hosted.detail = Phase.REFUSED, "the unit journal would not open"
            return
        assignment = starting_assignment(deployment, compiled)
        if isinstance(assignment, str):
            hosted.phase, hosted.detail = Phase.REFUSED, assignment
            return
        hosted.venue = venue
        unit = NodeUnit(
            deployment,
            compiled,
            records,
            path,
            journal.value,
            self.guard(hosted),
            assignment,
            FeedRates(venue.feed.recording, rate_refs(records, ACCOUNT_CURRENCY), ACCOUNT_CURRENCY),
            port=_ScopeClose(self, deployment.deployment_id),
        )
        unit.base_ns = account_bar
        unit.journal_world = world
        unit.account = lambda account=deployment.account_id: self._account_inputs(account)
        account = venue.client.account
        target = ExecutionTarget.try_create(account.role, account.venue, account.account_id)
        if is_refusal(target):
            hosted.phase, hosted.detail = Phase.REFUSED, "the account is not a trading target"
            return
        started = unit.start(venue.client.equity(), target.value, self._saved_snapshot(deployment))
        if is_refusal(started):
            hosted.phase = Phase.REFUSED
            hosted.detail = f"the unit would not start: {_why(started)}"
            return
        if unit.hosted_unit is not None:
            unit.kept_values = dict(unit.hosted_unit.calibrated_values)
        loop = self._loop(unit, account)
        if is_refusal(loop):
            hosted.phase, hosted.detail = Phase.REFUSED, "the loop driver refused the unit"
            return
        hosted.unit, hosted.loop = unit, loop.value
        if not live:
            rebuilt = paper_lane.restored(self.context.journal_root, deployment.deployment_id)
            if is_refusal(rebuilt):
                hosted.phase = Phase.REFUSED
                hosted.detail = "the paper lane's journal could not be read"
                return
            cast("paper_lane.PaperAccount", unit.orders.venue.client).adopt(rebuilt.value)
            unit.adopt(rebuilt.value)
        hosted.phase = Phase.WARMING
        recorded = [
            Bar(market, bar) for market in unit.traded for bar in self._recent(unit, venue, market)
        ]
        self._drive_one(hosted, recorded)
        self._settle_warm(hosted)

    def _widen(self, venue: Venue, deployment: Deployment) -> bool:
        """Add each market the deployment chose, and each conversion market its records name,
        that the binding does not hold; then drop the session once so it reconnects and
        subscribes them. True when it must come back first.

        A conversion market is subscribed so its bars reach this node's recording, which is where
        a unit's rate fact is read from; the unit is never driven on it, because ``_drive_one``
        keeps to its own traded markets. The reconnect is the path R20 and R21 already reset:
        books rebuild, quotes go with the old session, and the reconcile runs once on the new
        one. A running unit on that account misses one bar's record, which the plan accepts.
        """
        symbols = unit_symbols(deployment)
        wanted = {market: symbols[market] for market in deployment.markets if market in symbols}
        records = deployment_records(deployment)
        if not isinstance(records, str):
            for ref in rate_refs(records, ACCOUNT_CURRENCY).values():
                if ref.market_id in symbols:
                    wanted.setdefault(ref.market_id, symbols[ref.market_id])
        if not venue.client.add_markets(wanted):
            return False
        venue.feed.widen(wanted)
        venue.feed.drop("a deployment added a market")
        return True

    def _netted(self, venue: Venue, deployment: Deployment) -> str | None:
        """Why a second live unit on a netting account may not trade a market this one holds:
        its position would cancel the first at the venue, and neither unit would know."""
        if deployment.lane != "live" or not venue.client.nets_positions():
            return None
        for hosted in self.hosted.values():
            other = hosted.deployment
            unit = hosted.unit
            if (
                other.deployment_id != deployment.deployment_id
                and other.account_id == deployment.account_id
                and other.lane == "live"
                and unit is not None
                and (hosted.phase is not Phase.STOPPED or unit.venue_open())
            ):
                shared = sorted(set(unit.traded) & set(deployment.markets))
                if shared:
                    return f"another unit already trades {shared[0]} on this netting account"
        return None

    def _saved_snapshot(self, deployment: Deployment) -> Mapping[str, object] | None:
        """The unit state the deployment's folder holds, or None when there is none to read. A
        file that does not parse starts the unit fresh: no reason to refuse the deployment."""
        try:
            found = json.loads(
                snapshot_path(self.context.data, deployment.deployment_id).read_text("utf-8")
            )
        except (OSError, ValueError):
            return None
        return cast("Mapping[str, object]", found) if isinstance(found, Mapping) else None

    def _write_snapshot(self, hosted: _Hosted) -> None:
        """Save the unit's own state when one of its slow numbers moved, written whole and
        replaced, so a stop halfway leaves the last good one. The next start hands it back to
        ``unit.start``, which resumes the unit or writes the ``cold_start`` reason."""
        unit = hosted.unit
        if unit is None or unit.hosted_unit is None:
            return
        values = dict(unit.hosted_unit.calibrated_values)
        if values == unit.kept_values:
            return
        path = snapshot_path(self.context.data, hosted.deployment.deployment_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(unit.hosted_unit.snapshot(), sort_keys=True), "utf-8")
        os.replace(temporary, path)
        unit.kept_values = values

    def _paper_path(self, hosted: _Hosted, venue: Venue) -> OrderPath | None:
        """A paper deployment's own order path: every step a live order takes, ending at its
        paper account beside the binding instead of the venue. Its order rows go to the node
        journal's ``paper`` partition."""
        if self._paper_journal is None:
            scope = WriterScope(
                JournalStream.NODE,
                self.context.standing().tag,
                JournalWorld.PAPER,
                self.machine,
                ROLE,
                self.build,
            )
            opened = JournalWriter.open(
                self.context.journal_root,
                scope,
                clock=self.clock_ns,
                boot_epoch_id=self.boot_epoch_id,
            )
            if is_refusal(opened):
                return None
            self._paper_journal = opened.value
        paper = paper_lane.PaperAccount(venue.client)
        venue.feed.listen(paper.on_bar)
        return OrderPath(
            tag=self.context.standing().tag,
            venue=Venue(paper, venue.feed),
            journal=self._paper_journal,
            clock_ns=self.clock_ns,
            sleep=self.sleep,
            on_alarm=self.alarms.append,
            session_epoch=f"{self.boot_epoch_id}-paper-{hosted.deployment.deployment_id}",
        )

    def _loop(self, unit: NodeUnit, account: Account) -> Result[CommandStreamLoop]:
        writer = WriterId.try_create(
            self.machine, ROLE, f"{account.venue.value}:{account.account_id}", self.boot_epoch_id
        )
        if is_refusal(writer):
            return writer
        accumulator = RecordingAccumulator.try_create(
            venue_id=account.venue,
            account=account,
            writer_id=writer.value,
            observation_sink=_Sink(),
            journal_sink=_Sink(),
            accumulator_bound=ACCUMULATOR_BOUND,
            writer_name=f"node-feed:{account.venue.value}",
        )
        if is_refusal(accumulator):
            return accumulator
        streams = StreamSet.try_create(
            [DeclaredStream(unit.stream_id(market), market) for market in unit.traded]
        )
        if is_refusal(streams):
            return streams
        latency = Duration.try_create(MAX_SLICE_LATENCY_NS)
        if is_refusal(latency):
            return latency
        return CommandStreamLoop.try_create(
            accumulator=accumulator.value,
            stream_set=streams.value,
            clock=_LoopClock(self.boot_epoch_id, self.clock_ns, self.steady_ns),
            max_slice_latency=latency.value,
            handler=unit,
        )

    def _settle_warm(self, hosted: _Hosted) -> None:
        unit = hosted.unit
        if unit is None:
            return
        if unit.warm_seen >= unit.warm_needed:
            unit.warming = False
            hosted.phase, hosted.detail = Phase.TRADING, ""
        else:
            hosted.detail = f"warming up {unit.warm_seen} of {unit.warm_needed}"

    # --- driving units on closed bars ---

    def _recent(self, unit: NodeUnit, venue: Venue, market: str) -> tuple[QuoteBar, ...]:
        """The feed bars to replay for warm-up: the unit's own stream's ``warm_needed`` buckets.

        A unit whose stream is ``factor`` base bars long needs ``factor`` bars per warm-up bar,
        and the recording may start part way through a bucket, which ``roll_up`` drops. So the
        read stops one base bar short of ``warm_needed + 1`` whole buckets: a mid-stream start
        still yields ``warm_needed`` whole buckets, and never a bucket past the one that
        completes warm-up. A unit driven past that bucket would mint from the replay.
        """
        if unit.base_ns is None or unit.stream_seconds is None:
            return venue.feed.recording.recent(market, unit.warm_needed)
        factor = unit.stream_seconds * _NS // unit.base_ns
        return venue.feed.recording.recent(market, (unit.warm_needed + 1) * factor - 1)

    def _drive(self, venue: Venue, bars: Sequence[Bar]) -> None:
        for hosted in self.hosted.values():
            if hosted.venue is venue and hosted.phase in (Phase.WARMING, Phase.TRADING):
                try:
                    self._drive_one(hosted, bars)
                except Exception as error:  # one unit's raise costs that unit, not the next one
                    self._unit_fault(hosted, FaultPhase.HOST, type(error).__name__, repr(error))
                    continue
                if hosted.phase is Phase.WARMING:
                    self._settle_warm(hosted)

    def _unit_fault(self, hosted: _Hosted, phase: FaultPhase, root: str, why: str) -> None:
        """One raise or refusal past a unit's own step is that unit's fault (AD-23 step 2): its
        entries stop, one ``risk_event`` row is filed per root-cause key, its phase stays
        ``TRADING``, and the driver steps it again on the next bar."""
        unit = hosted.unit
        if unit is not None:
            if unit.hosted_unit is not None:
                unit.hosted_unit.bench()
            key = f"{phase.value}:{root}"
            if key not in hosted.fault_roots:
                hosted.fault_roots.add(key)
                unit.journal.append(RiskEvent(UNIT_FAULT, key))
        hosted.detail = f"a fault: {why}"

    def _drive_one(self, hosted: _Hosted, bars: Sequence[Bar]) -> None:
        unit, loop = hosted.unit, hosted.loop
        if unit is None or loop is None:
            return
        by_at: dict[int, list[Bar]] = {}
        for event in bars:
            if event.market_id in unit.traded:
                by_at.setdefault(event.bar.knowable_at.value_ns, []).append(event)
        for at in sorted(by_at):
            closes: dict[int, list[str]] = {}
            for event in by_at[at]:
                for closed in unit.roll(event.market_id, event.bar):
                    unit.windows[(unit.stream, event.market_id)].push(closed)
                    closes.setdefault(closed.knowable_at.value_ns, []).append(event.market_id)
            for ns in sorted(closes):
                for market in closes[ns]:
                    pushed = loop.accumulator.push(
                        observation_id=f"{unit.stream_id(market)}:{ns}",
                        stream_id=unit.stream_id(market),
                        receive_wall=Instant(ns),
                        payload={"kind": "market-bar", "market_id": market},
                        kind="market-bar",
                        closed=True,
                    )
                    if is_refusal(pushed):
                        hosted.phase, hosted.detail = Phase.STOPPED, _why(pushed)
                        return
                unit.journal.at(Instant(ns))
                driven = loop.close_frontier()
                if is_refusal(driven):
                    self._unit_fault(
                        hosted,
                        FaultPhase.HOST,
                        str(driven.context.get("field") or "close_frontier"),
                        _why(driven),
                    )
                    return
                if unit.warming:
                    unit.warm_seen += 1
                    if unit.warm_seen >= unit.warm_needed:
                        unit.warming = False
        self._write_snapshot(hosted)

    # --- what he sees ---

    def _unit_level(self, hosted: _Hosted) -> KsaLevel:
        """The highest kill level over the unit: its deployment, its account, each market."""
        markets = (None,) if hosted.unit is None else (None, *hosted.unit.traded)
        levels = [self.level_for(hosted, market)[0] for market in markets]
        return max(levels, key=LEVEL_RANK.__getitem__)

    def _observe(self) -> None:
        deployments: dict[str, object] = {}
        units: list[object] = []
        positions: list[object] = []
        boards: dict[str, object] = {}
        journal_problem: str | None = None
        for deployment_id, hosted in self.hosted.items():
            deployments[deployment_id] = {"state": hosted.phase.value, "detail": hosted.detail}
            unit = hosted.unit
            placed = self.board_read(hosted)
            if placed is not None:
                boards[deployment_id] = placed.document()
            units.append(
                {
                    **({} if placed is None else {"board": boards[deployment_id]}),
                    "deployment_id": deployment_id,
                    "unit_id": hosted.deployment.unit_id,
                    "state": hosted.phase.value,
                    "detail": hosted.detail,
                    "warm": None
                    if unit is None
                    else {
                        "seen": min(unit.warm_seen, unit.warm_needed),
                        "needed": unit.warm_needed,
                    },
                    "kill_level": self._unit_level(hosted).value,
                }
            )
            if unit is not None:
                positions.extend(unit.positions())
                refused = unit.journal.write_failure
                if refused is not None:
                    journal_problem = (
                        f"a row of deployment {deployment_id} was refused"
                        f" ({refused.category.value})"
                    )
        positions.extend(self.reconciler.shown())
        kill = {
            scope: PLACEHOLDER_KILL_EFFECTS[level].document()
            for scope, level in self.applied.items()
        }
        venues = [venue.feed.document() for venue in self.venues.values()]
        for key, value in (
            ("runtime.deployments", deployments),
            ("runtime.units", units),
            ("runtime.positions", positions),
            (
                "runtime.mine",
                [{"position": held.name, "scopes": sorted(held.scopes)} for held in self._mine()],
            ),
            ("runtime.board", boards),
            ("runtime.kill", kill),
            ("runtime.venues", venues),
            (
                "runtime.accounts",
                {account: facts.document() for account, facts in self._facts.items()},
            ),
            ("runtime.alarms", list(self.alarms)),
            ("runtime.stand_downs", self.stand_downs.document()),
            ("runtime.safe_to_restart", self.safe_to_restart()),
            # Only a problem is written, so a clean tick never wipes the one the node's start saw.
            *(() if journal_problem is None else (("journal_problem", journal_problem),)),
        ):
            text = json.dumps(value, sort_keys=True, default=str)
            if self._shown.get(key) != text:
                self.context.store.observe(key, json.loads(text), self.clock_ns())
                self._shown[key] = text


def clock_offset(facts: Path, now_ns: int) -> int | None:
    """The offset the host last proved, in nanoseconds, from the facts in the node's volume.

    None when no probe answered, the file cannot be read, or the reading is older than
    `CLOCK_FACT_STALE_NS`: an old reading is not acted on, so a host that stops probing leaves the
    clock unproven rather than holding a stale offset."""
    try:
        document: object = json.loads(facts.read_text("utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(document, Mapping):
        return None
    clock = cast("Mapping[str, object]", document).get("clock")
    if not isinstance(clock, Mapping):
        return None
    named = cast("Mapping[str, object]", clock)
    offset, probed = named.get("offset_ms"), named.get("probed_at")
    if not isinstance(offset, int) or isinstance(offset, bool) or not isinstance(probed, str):
        return None
    try:
        at = datetime.fromisoformat(probed)
    except ValueError:
        return None
    if at.tzinfo is None:
        return None
    if now_ns - int(at.timestamp() * 1e9) > CLOCK_FACT_STALE_NS:
        return None
    return offset * 1_000_000


def _why(refusal: TypedRefusal) -> str:
    return f"{refusal.category.value}: {refusal.context.get('reason', '')}"


def _unit_account(unit: NodeUnit, instant: Instant) -> UnitAccount | None:
    """The account facts the unit sizes against, as its handler answers them for this instant."""
    handler = unit.handler
    if handler is None:
        return None
    return cast("UnitAccount", handler.read_surfaces()["account"].at(instant))


def _placeholder(deployment_id: str) -> Deployment:
    return Deployment(deployment_id, "", "", {}, "", "", "", "", "", (), "", (), "paper")
