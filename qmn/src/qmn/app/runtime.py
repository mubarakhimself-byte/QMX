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

Protection follows the venue's rule: on cTrader the stop rides on the entry order as a distance.
If the venue does not hold it after ``PROTECT_RETRY_MAX`` tries of ``PROTECT_CONFIRM_NS`` each,
the node closes that position reduce-only and raises the protection alarm, a labelled placeholder
for the risk session (``RISK-SIZING-PLACEHOLDERS.md`` row 19).
"""

from __future__ import annotations

import hashlib
import json
import sys
import threading
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from decimal import Decimal
from enum import StrEnum
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
    WriterId,
    is_refusal,
)
from qmf.data.journal_envelope import JournalWorld, RowFacts
from qmf.data.journal_writer import AppendOutcome, JournalWriter
from qmf.risk.paper import ExecutionTarget
from qmf.risk.unit_intent import (
    AmendProtection,
    ClosePartial,
    UnitExitIntent,
    check_amendment_tightens,
    parse_unit_intent,
)
from qmf.venue.capabilities import CloseScope
from qmf.venue.commands import (
    Command,
    OrderParameters,
    OrderType,
    ProtectionAmendment,
    ProtectionSide,
    SubmissionOutcome,
    TimeInForce,
)
from qmf.venue.encode import OrderTags, order_tags
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.motion import ClosedTrade
from qml.numbers import InstrumentRecord, lots, parse_record
from qml.protocol.unit import HostedUnit, OwnPosition, QuoteBar, Surface, construct_unit
from qml.unit.model import Side

from qmn.app.feed_keeper import Bar, FeedKeeper
from qmn.app.operations import Answer, Context, Target, refused
from qmn.app.store import Json
from qmn.journal_dispatch import enact_command
from qmn.loop.accumulator import RecordingAccumulator
from qmn.loop.driver import CommandStreamLoop
from qmn.order.protection import require_venue_resident_protective_stop
from qmn.protection.effect_matrix import PLACEHOLDER_KILL_EFFECTS, KillEffect
from qmn.protection.ksa import LEVEL_RANK, KsaLevel
from qmn.venue.conformance import ConformanceDouble

__all__ = [
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
    "Venue",
    "VenueAccount",
    "deploy_preflight",
    "parse_deployment",
]

RECONCILE_TICK_S: Final = 0.2
"""`[node] reconcile_tick_ms`, starting at 200 (NODE.md section 9)."""
PROTECT_CONFIRM_NS: Final = 2_000_000_000
"""`[node] protect_confirm_ms`, starting at 2,000: how long one try waits for the venue to show
the stop. A labelled placeholder for the risk session."""
PROTECT_RETRY_MAX: Final = 3
"""`[node] protect_retry_max`, starting at 3 tries. A labelled placeholder for the risk session."""
PROTECT_POLL_S: Final = 0.05
MAX_SLICE_LATENCY_NS: Final = 500_000_000
"""`[node] max_slice_latency`, starting at 500 ms (research 31 section 3.3)."""
ACCUMULATOR_BOUND: Final = 10_000
"""`[node] accumulator_bound`, one session of bars per stream (NODE.md section 9)."""
DEPLOYMENT_SCHEMA: Final = "qmx.node.deployment/1"
ROLE: Final = "node"
_ULID_ALPHABET: Final = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_LANE_WORLD: Final[Mapping[str, JournalWorld]] = {
    "paper": JournalWorld.PAPER,
    "live": JournalWorld.LIVE,
}


# --- the deployment document ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StagedFile:
    entry_id: str
    version: int
    fingerprint: str
    path: str
    kind: str


@dataclass(frozen=True, slots=True)
class Deployment:
    """A ``qmx.node.deployment/1`` document, parsed (Part C CONTRACTS section 3)."""

    deployment_id: str
    node_tag: str
    unit_id: str
    unit_document: Mapping[str, object]
    compiled_fingerprint: str
    g_fingerprint: str
    files: tuple[StagedFile, ...]
    account_id: str
    snapshots: tuple[Mapping[str, object], ...]
    lane: str

    @property
    def world(self) -> JournalWorld:
        return _LANE_WORLD[self.lane]


def _str(document: Mapping[str, object], name: str) -> str:
    value = document.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"deployment.{name} is a non-empty string")
    return value


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
    if Path(path).is_absolute() or ".." in Path(path).parts or "\\" in path:
        raise ValueError(f"deployment.files path {path} is a relative path inside the folder")
    version = entry.get("version")
    if type(version) is not int:
        raise ValueError("deployment.files version is a whole number")
    fingerprint = _str(entry, "fingerprint")
    if not fingerprint.startswith("sha256:"):
        raise ValueError(f"the fingerprint of {path} is sha256:<hex>")
    return StagedFile(_str(entry, "entry_id"), version, fingerprint, path, _str(entry, "kind"))


def parse_deployment(document: Mapping[str, object]) -> Deployment:
    """The document's fields this node acts on; a ``ValueError`` names the first wrong one."""
    if document.get("schema_version") != DEPLOYMENT_SCHEMA:
        raise ValueError(f"deployment.schema_version is {DEPLOYMENT_SCHEMA}")
    lane = _str(document, "lane")
    if lane not in _LANE_WORLD:
        raise ValueError('deployment.lane is "paper" or "live"')
    files = document.get("files")
    snapshots = document.get("snapshots")
    if not isinstance(files, list) or not isinstance(snapshots, list):
        raise ValueError("deployment.files and deployment.snapshots are lists")
    unit = _map(document, "unit")
    return Deployment(
        deployment_id=_str(document, "deployment_id"),
        node_tag=_str(_map(document, "node"), "tag"),
        unit_id=_str(unit, "id"),
        unit_document=_map(document, "unit_document"),
        compiled_fingerprint=_str(document, "compiled_fingerprint"),
        g_fingerprint=_str(_map(document, "g_record"), "compiled_fingerprint"),
        files=tuple(_staged(item) for item in cast("list[object]", files)),
        account_id=_str(_map(document, "account"), "id"),
        snapshots=tuple(
            cast("Mapping[str, object]", item)
            for item in cast("list[object]", snapshots)
            if isinstance(item, Mapping)
        ),
        lane=lane,
    )


def staging_folder(data: Path, deployment_id: str) -> Path:
    return data / "deployments" / deployment_id / "in"


def file_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def deploy_preflight(data: Path, document: Mapping[str, object]) -> Answer | None:
    """``deploy``'s refusals before it is kept, each naming what is wrong; None when it may go.

    A file missing from the staging folder answers ``files_missing``, which the node link's
    outbox keeps waiting on; a file whose bytes have another fingerprint answers
    ``file_mismatch``. There is no size limit. A kept deployment's ``lock.json`` lists every
    staged file by fingerprint.
    """
    try:
        deployment = parse_deployment(document)
    except ValueError as error:
        return refused("bad_argument", f"deploy: {error}")
    if deployment.lane == "live":
        return refused(
            "live_not_bound",
            "a live lane needs a live account binding, which this node does not hold",
        )
    if deployment.compiled_fingerprint != deployment.g_fingerprint:
        return refused(
            "fingerprint_mismatch",
            "the deployment's compiled fingerprint is not the one its G record tested",
            value={
                "compiled_fingerprint": deployment.compiled_fingerprint,
                "g_record": deployment.g_fingerprint,
            },
        )
    folder = staging_folder(data, deployment.deployment_id)
    missing = [item.path for item in deployment.files if not (folder / item.path).is_file()]
    if missing:
        return refused(
            "files_missing",
            f"deploy: staged file {missing[0]} is missing from {folder.name}/",
            next_step="The node link stages every file before it asks again.",
            value={"missing": cast("list[Json]", missing)},
        )
    for item in deployment.files:
        found = file_fingerprint(folder / item.path)
        if found != item.fingerprint:
            return refused(
                "file_mismatch",
                f"deploy: staged file {item.path} has fingerprint {found}, not {item.fingerprint}",
                value={"path": item.path, "expected": item.fingerprint, "found": found},
            )
    lock = [
        {"path": item.path, "fingerprint": item.fingerprint, "kind": item.kind}
        for item in deployment.files
    ]
    (folder.parent / "lock.json").write_text(json.dumps(lock, sort_keys=True), "utf-8")
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


@dataclass(frozen=True, slots=True)
class VenueClose:
    """The venue closed a position: its stop fired, or the node closed it."""

    kind: FillKind
    price: Decimal
    gap: bool = False


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


@dataclass
class _Held:
    market_id: str
    side: Side
    quantity: Decimal
    entry: Decimal
    stop: Decimal | None


@dataclass
class ConformanceAccount:
    """The conformance venue's account: a fake, never a broker, no network and no key.

    The conformance double answers every command as the venue's port does, its protection gate
    included. Beside it this keeps what a broker keeps: positions, the stop each one holds as
    the order's distance from its fill, and the broker firing that stop on the feed's bars.
    ``received`` is every ticket that reached the venue. With ``holds_stops`` false the venue
    answers but never holds a stop, which the protection escalation is tested against.
    """

    double: ConformanceDouble
    venue_account: Account
    starting_equity: Decimal
    holds_stops: bool = True
    received: list[Ticket] = field(default_factory=list[Ticket])
    _positions: dict[str, _Held] = field(default_factory=dict[str, _Held])
    _closed: dict[str, VenueClose] = field(default_factory=dict[str, VenueClose])
    _quotes: dict[str, tuple[Decimal, Decimal]] = field(
        default_factory=dict[str, tuple[Decimal, Decimal]]
    )
    _booked: Decimal = Decimal(0)

    @classmethod
    def open(
        cls, account: Account, starting_equity: Decimal, *, holds_stops: bool = True
    ) -> Result[ConformanceAccount]:
        from qmf.core import World  # noqa: PLC0415 - the double's own selector

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
        held = self._positions.pop(position)
        move = closed.price - held.entry if held.side is Side.LONG else held.entry - closed.price
        self._booked += move * held.quantity
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
            self._positions[ticket.tags.client_order_id] = _Held(
                ticket.market_id, ticket.side, ticket.quantity, price, stop
            )
            return Ok(Sent(result.outcome, price))
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
        return self.starting_equity + self._booked

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


@dataclass(frozen=True, slots=True)
class Blocked:
    reason: str


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


class _OrderJournal:
    """The node journal as the journal-before-dispatch gate's sink: one ``order`` row."""

    def __init__(self, journal: JournalWriter, clock_ns: Callable[[], int]) -> None:
        self._journal = journal
        self._clock_ns = clock_ns
        self.repeated = False

    def append(self, event: object, /) -> SinkResult:
        body = dict(cast("Mapping[str, object]", event))
        written = self._journal.append(
            "order", body, RowFacts(ts_recv=self._clock_ns(), clock_ok=False)
        )
        if is_refusal(written):
            return written
        self.repeated = written.value.outcome is AppendOutcome.REPEAT
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
    unknown: bool = False
    """An earlier order's outcome is unknown: no entry until it resolves (TN-01, C-12b)."""
    _ordinal: int = 0
    _sent: dict[str, Placed | Blocked] = field(default_factory=dict[str, Placed | Blocked])

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
        outcome = self._entry(client_order_id, label, wire, record, quantity, blocked_by)
        self._sent[client_order_id] = outcome
        return outcome

    def _entry(
        self,
        client_order_id: str,
        label: str,
        wire: Mapping[str, object],
        record: InstrumentRecord,
        quantity: Quantity,
        blocked_by: str | None,
    ) -> Placed | Blocked:
        if blocked_by is not None:
            return Blocked(blocked_by)
        if self.unknown:
            return Blocked(
                "venue answer unknown for an earlier order, so no entry until it resolves"
            )
        side = Side(str(wire["direction"]))
        market = str(wire["market_id"])
        stop = Decimal(str(cast("Mapping[str, object]", wire["protection"])["stop"]))
        quote = self.venue.feed.quote(market)
        reference = (
            (quote.ask if side is Side.LONG else quote.bid) if quote is not None else None
        ) or stop
        distance = reference - stop if side is Side.LONG else stop - reference
        if distance <= 0:
            return Blocked("the stop widens the stop past the price: it is not on the loss side")
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
                self._note(client_order_id, "filled", {"step": "filled", "price": str(sent.price)})
                if self._protected(client_order_id, ticket, distance):
                    return Placed(sent.price)
                return Blocked("the venue cannot hold this order's stop, so the node closed it")
            case SubmissionOutcome.UNKNOWN:
                self.unknown = True
                self._note(client_order_id, "unknown", {"step": "unknown"})
                return Blocked("venue answer unknown for this order")
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
            deadline = self.clock_ns() + self.confirm_ns
            while True:
                if self.venue.client.stop_of(position) is not None:
                    return True
                if self.clock_ns() >= deadline:
                    break
                self.sleep(PROTECT_POLL_S)
        self.close(position, ticket.market_id, ticket.side, ticket.reference, "protection")
        alarm: dict[str, object] = {
            "alarm": "protection_escalation",
            "position": position,
            "market_id": ticket.market_id,
            "tries": self.retry_max,
            "action": "closed_reduce_only",
            "origin": "placeholder",
        }
        self.journal.append("protection", alarm, RowFacts(ts_recv=self.clock_ns(), clock_ok=False))
        self.on_alarm(alarm)
        return False

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
        that cannot be written does not stop it."""
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
        ticket = Ticket(command.value, market, side, reference, position=position)
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
        the amendment's own risk check refuses a wider distance again."""
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
        return Placed(new_stop)


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
                    self._unit.venue_ids[record.position_id] = named
                record = replace(record, position_id=self._unit.venue_name(record.position_id))
            case UnitTrade():
                record = replace(record, trade_id=self._unit.venue_name(record.trade_id))
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
    ) -> None:
        self.deployment = deployment
        self.compiled = compiled
        self.records = records
        self.orders = orders
        self.journal = journal
        self.lane = deployment.lane
        self.guard = guard
        self.windows = {market: BarWindow(window_size(compiled)) for market in records}
        self.warm_needed = window_size(compiled)
        self.warm_seen = 0
        self.warming = True
        self.venue_ids: dict[str, str] = {}
        self.names: dict[str, str] = {}
        self.placed: dict[str, tuple[str, Side, Decimal]] = {}
        """Each entry the venue filled, by client order id: market, side and fill price."""
        self._orders: dict[str, Placed | Blocked] = {}
        self._done: set[str] = set()
        self._execution = _Execution(self)
        self._port = _Journal(self, journal)
        self.handler: UnitSliceHandler | None = None

    def start(self, equity: Decimal, target: ExecutionTarget) -> Result[None]:
        def host(surfaces: Mapping[str, Surface]) -> Result[HostedUnit]:
            own = _OwnJournal(self, surfaces["own_journal"])
            return construct_unit(
                self.compiled,
                read_surfaces={**surfaces, "own_journal": own},
                scope_id=self.deployment.deployment_id,
                execution_target=target,
            )

        started = UnitSliceHandler.start(
            host,
            stream=self.compiled.plan.stream,
            records=self.records,
            bars=self.windows,
            opened_by=self.compiled.compiled_fingerprint,
            equity=equity,
            execution=self._execution,
            journal=self._port,
        )
        if is_refusal(started):
            return started
        self.handler = started.value
        return Ok(None)

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
        if not isinstance(placed, Placed):
            reason = "warming up" if placed is None else placed.reason
            if wire.get("intent_family") == "entry":
                self._port.append(
                    Skip(
                        frontier, intent.stream_id, str(wire["decision_row_id"]), reason, Decimal(1)
                    )
                )
            self._done.add(intent.intent_id)
            return Ok(True)
        self._execution.price = placed.price
        done = self.handled.execute_resting(intent, observation, frontier)
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
                self._orders[intent.intent_id] = self._send(intent, frontier)
        return minted

    # --- the order path for one minted intent ---

    def _send(self, intent: RestingIntent, at: Instant) -> Placed | Blocked:
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
                client_order_id=named,
                label=self.label,
                wire=wire,
                record=record,
                quantity=sized.value,
                blocked_by=self.guard(market),
            )
            if isinstance(placed, Placed):
                self.placed[named] = (market, Side(str(wire["direction"])), placed.price)
            return placed
        return self._exit(intent.stream_id, wire)

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
                return self._amend(exit_, position, held, Decimal(stop.value).scaleb(-stop.scale))
            case _:
                return self.orders.close(position, market, held.side, held.entry_price, "unit")

    def _amend(
        self, exit_: UnitExitIntent, position: str, held: OwnPosition, new_stop: Decimal
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
        market = next(m for m, p in self.handled.open_positions.items() if p is held)
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
    bars_driven: int = 0


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
    monotonic_ns: Callable[[], int]

    def wall_now(self) -> Result[Instant]:
        return Instant.try_create(self.clock_ns())

    def monotonic_now(self) -> Result[MonotonicReading]:
        return MonotonicReading.try_create(self.monotonic_ns(), self.boot_epoch_id)


Compile = Callable[[Deployment, Path], "CompiledUnit | str"]


def compile_staged(deployment: Deployment, folder: Path) -> CompiledUnit | str:
    """Compile the deployment's unit from its staged blocks through QML's one compiler, which
    checks every pin's fingerprint; answers the compiled unit or why it did not compile."""
    sources: dict[str, bytes] = {}
    entries: dict[str, bytes] = {}
    for item in deployment.files:
        pin = f"{item.entry_id}@{item.version}"
        data = (folder / item.path).read_bytes()
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
    return compiled[0].message if compiled else "the unit does not compile"


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
        monotonic_ns: Callable[[], int],
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
        self.monotonic_ns = monotonic_ns
        self.sleep = sleep
        self.boot_epoch_id = boot_epoch_id
        self.compile = compile
        self.tick_s = tick_s
        self.hosted: dict[str, _Hosted] = {}
        self.alarms: list[Mapping[str, object]] = []
        self.applied: dict[str, KsaLevel] = {}
        self._paths: dict[str, OrderPath] = {}
        self._compiler = ThreadPoolExecutor(max_workers=1, thread_name_prefix="node-compile")
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._shown: dict[str, str] = {}
        self._target = Target()
        self.paused_by_black = False

    # --- the thread ---

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="node-runtime", daemon=True)
        self._thread.start()

    def wake(self) -> None:
        self._wake.set()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
        self._compiler.shutdown(wait=False, cancel_futures=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception as error:  # the runtime keeps going; the error is observed
                print(json.dumps({"event": "runtime_error", "error": repr(error)}), file=sys.stderr)
                self.context.store.observe("runtime.error", repr(error), self.clock_ns())
            self._wake.wait(self.tick_s)
            self._wake.clear()

    # --- one reconcile pass ---

    def tick(self) -> None:
        standing = self.context.standing()
        target = Target.fold(self.context.store.accepted())
        self._target = target
        if standing.mismatch:
            for hosted in self.hosted.values():
                hosted.phase, hosted.detail = Phase.WAITING, "the node's identity is unconfirmed"
            self._observe()
            return
        self._kill(target)
        self._deployments(target)
        for venue in self.venues.values():
            bars = venue.feed.pump()
            if bars:
                self._drive(venue, bars)
        self._observe()

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
            scopes.append(f"instrument:{hosted.unit.records[market].symbol}")
        held = [(self._target.kills.get(scope, KsaLevel.GREEN), scope) for scope in scopes]
        return max(held, key=lambda pair: LEVEL_RANK[pair[0]])

    def _kill(self, target: Target) -> None:
        for scope in list(self.applied):
            if target.kills.get(scope, KsaLevel.GREEN) is KsaLevel.GREEN:
                del self.applied[scope]
        self.paused_by_black = any(level is KsaLevel.BLACK for level in target.kills.values())
        for scope, level in target.kills.items():
            if LEVEL_RANK[level] <= LEVEL_RANK[self.applied.get(scope, KsaLevel.GREEN)]:
                continue
            self.applied[scope] = level
            effect = PLACEHOLDER_KILL_EFFECTS[level]
            closed = self._enact(scope, effect)
            body: dict[str, object] = {
                "scope": scope,
                **effect.document(),
                "positions_closed": closed,
                "resting_entries_cancelled": 0,
            }
            self.journal.append(
                "kill_level", body, RowFacts(ts_recv=self.clock_ns(), clock_ok=False)
            )

    def _enact(self, scope: str, effect: KillEffect) -> int:
        if not (effect.close_positions or effect.close_all_and_pause):
            return 0
        closed = 0
        for hosted in self.hosted.values():
            unit = hosted.unit
            if unit is None:
                continue
            for position, (market, side, price) in unit.venue_open().items():
                symbol = f"instrument:{unit.records[market].symbol}"
                covers = (
                    effect.close_all_and_pause
                    or scope == "all"
                    or scope
                    in (
                        f"deployment_id:{hosted.deployment.deployment_id}",
                        f"account:{hosted.deployment.account_id}",
                        symbol,
                    )
                )
                if not covers:
                    continue
                done = unit.orders.close(
                    position, market, side, price, f"kill-{effect.level.value.lower()}"
                )
                closed += isinstance(done, Placed)
        return closed

    def guard(self, hosted: _Hosted) -> Callable[[str], str | None]:
        """Why an entry on ``market`` may not go now, or None (Level 0 AD-39 step 2)."""

        def check(market: str) -> str | None:
            level, scope = self.level_for(hosted, market)
            if LEVEL_RANK[level] >= LEVEL_RANK[KsaLevel.YELLOW]:
                return f"the kill switch is at {level.value} for {scope}"
            if self.paused_by_black:
                return "the kill switch is at BLACK, so the node is paused"
            symbol = f"instrument:{hosted.unit.records[market].symbol}" if hosted.unit else ""
            for scope_key in (
                "all",
                f"deployment_id:{hosted.deployment.deployment_id}",
                f"account:{hosted.deployment.account_id}",
                symbol,
            ):
                if self._target.paused.get(scope_key):
                    return f"paused at {scope_key}"
            if hosted.deployment.deployment_id in self._target.withdrawn:
                return "the deployment is withdrawn, so it takes no new entry"
            venue = hosted.venue
            if venue is None or not venue.feed.ready:
                reason = "no session" if venue is None else venue.feed.reason
                return f"venue not ready: {reason}"
            return None

        return check

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
            withdrawn = hosted.deployment.deployment_id in target.withdrawn
            if withdrawn and hosted.unit is not None and not hosted.unit.positions():
                hosted.phase, hosted.detail = Phase.STOPPED, "withdrawn and flat"

    def _host(self, hosted: _Hosted, compiled: CompiledUnit | str) -> None:
        deployment = hosted.deployment
        hosted.compiling = None
        if isinstance(compiled, str):
            hosted.phase, hosted.detail = Phase.REFUSED, f"the unit did not compile: {compiled}"
            return
        if compiled.compiled_fingerprint.value != deployment.g_fingerprint:
            hosted.phase = Phase.REFUSED
            hosted.detail = (
                f"compiled to {compiled.compiled_fingerprint.value}, not the"
                f" {deployment.g_fingerprint} its G record tested"
            )
            return
        venue = self.venues.get(deployment.account_id)
        path = self._path(deployment.account_id)
        if venue is None or path is None:
            hosted.phase = Phase.WAITING
            hosted.detail = f"no venue binding holds account {deployment.account_id}"
            return
        records = deployment_records(deployment)
        if isinstance(records, str):
            hosted.phase, hosted.detail = Phase.REFUSED, records
            return
        journal = RunJournal.open_live(
            self.context.journal_root,
            compiled,
            scope_id=deployment.deployment_id,
            world=deployment.world,
            machine=self.machine,
            role=ROLE,
            build=self.build,
            boot_epoch_id=self.boot_epoch_id,
        )
        if is_refusal(journal):
            hosted.phase, hosted.detail = Phase.REFUSED, "the unit journal would not open"
            return
        hosted.venue = venue
        unit = NodeUnit(deployment, compiled, records, path, journal.value, self.guard(hosted))
        account = venue.client.account
        target = ExecutionTarget.try_create(account.role, account.venue, account.account_id)
        if is_refusal(target):
            hosted.phase, hosted.detail = Phase.REFUSED, "the account is not a trading target"
            return
        started = unit.start(venue.client.equity(), target.value)
        if is_refusal(started):
            hosted.phase, hosted.detail = (
                Phase.REFUSED,
                f"the unit would not start ({started.category.value})",
            )
            return
        loop = self._loop(unit, account)
        if is_refusal(loop):
            hosted.phase, hosted.detail = Phase.REFUSED, "the loop driver refused the unit"
            return
        hosted.unit, hosted.loop = unit, loop.value
        hosted.phase = Phase.WARMING
        recorded = [
            Bar(market, bar)
            for market in records
            for bar in venue.feed.recording.recent(market, unit.warm_needed)
        ]
        self._drive_one(hosted, recorded)
        self._settle_warm(hosted)

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
        streams = StreamSet.try_create([DeclaredStream(market, market) for market in unit.records])
        if is_refusal(streams):
            return streams
        latency = Duration.try_create(MAX_SLICE_LATENCY_NS)
        if is_refusal(latency):
            return latency
        return CommandStreamLoop.try_create(
            accumulator=accumulator.value,
            stream_set=streams.value,
            clock=_LoopClock(self.boot_epoch_id, self.clock_ns, self.monotonic_ns),
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

    def _drive(self, venue: Venue, bars: Sequence[Bar]) -> None:
        for hosted in self.hosted.values():
            if hosted.venue is venue and hosted.phase in (Phase.WARMING, Phase.TRADING):
                self._drive_one(hosted, bars)
                if hosted.phase is Phase.WARMING:
                    self._settle_warm(hosted)

    def _drive_one(self, hosted: _Hosted, bars: Sequence[Bar]) -> None:
        unit, loop = hosted.unit, hosted.loop
        if unit is None or loop is None:
            return
        by_ns: dict[int, list[Bar]] = {}
        for event in bars:
            if event.market_id in unit.records:
                by_ns.setdefault(event.bar.knowable_at.value_ns, []).append(event)
        for ns in sorted(by_ns):
            for event in by_ns[ns]:
                unit.windows[event.market_id].push(event.bar)
                pushed = loop.accumulator.push(
                    observation_id=f"{event.market_id}:{ns}",
                    stream_id=event.market_id,
                    receive_wall=Instant(ns),
                    payload={"kind": "market-bar", "market_id": event.market_id},
                    kind="market-bar",
                    closed=True,
                )
                if is_refusal(pushed):
                    hosted.phase, hosted.detail = Phase.STOPPED, _why(pushed)
                    return
            unit.journal.at(Instant(ns))
            driven = loop.close_frontier()
            if is_refusal(driven):
                hosted.phase, hosted.detail = Phase.STOPPED, _why(driven)
                return
            hosted.bars_driven += 1
            if unit.warming:
                unit.warm_seen += 1
                if unit.warm_seen >= unit.warm_needed:
                    unit.warming = False

    # --- what he sees ---

    def _observe(self) -> None:
        deployments: dict[str, object] = {}
        units: list[object] = []
        positions: list[object] = []
        for deployment_id, hosted in self.hosted.items():
            deployments[deployment_id] = {"state": hosted.phase.value, "detail": hosted.detail}
            unit = hosted.unit
            units.append(
                {
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
                    "kill_level": self.level_for(hosted)[0].value,
                }
            )
            if unit is not None:
                positions.extend(unit.positions())
        kill = {
            scope: PLACEHOLDER_KILL_EFFECTS[level].document()
            for scope, level in self.applied.items()
        }
        venues = [venue.feed.document() for venue in self.venues.values()]
        for key, value in (
            ("runtime.deployments", deployments),
            ("runtime.units", units),
            ("runtime.positions", positions),
            ("runtime.kill", kill),
            ("runtime.venues", venues),
            ("runtime.alarms", list(self.alarms)),
        ):
            text = json.dumps(value, sort_keys=True, default=str)
            if self._shown.get(key) != text:
                self.context.store.observe(key, json.loads(text), self.clock_ns())
                self._shown[key] = text


def _why(refusal: TypedRefusal) -> str:
    return f"{refusal.category.value}: {refusal.context.get('reason', '')}"


def _placeholder(deployment_id: str) -> Deployment:
    return Deployment(deployment_id, "", "", {}, "", "", (), "", (), "paper")
