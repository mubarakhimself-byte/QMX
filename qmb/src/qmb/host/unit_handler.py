"""The one run-slice handler for a hosted unit (Level 0 AD-5, R1-L0-02).

``run_slice`` drives any handler through its five hooks, so QMB's unit runner and the trading
node's runtime both drive a unit through this file. The host builds the ``HostedUnit`` from the
read surfaces this handler serves (``UnitSliceHandler.start`` takes the host's own
``construct_unit`` or resume call), and injects the execution and journal ports.

Per slice, in ``run_slice``'s order: a held position's scheduled cash events since its market's
last bar are booked (``scheduled_position_event``); a resting entry or exit fills against the
new bar (``execute_resting``); the bar becomes readable and a held position's stop, target or
liquidation level is checked against it (``update_closed_data``); then the unit steps once for
the slice's instant and its intents rest for the next bar (``mint_intents``). A fill's quantity
is the sizer receipt's rounded down to the market's lot step, or what the node's venue filled of
it; below the minimum lot the entry is skipped with its reason. The handler closes only
positions this compiled fingerprint opened. An exit acts by its kind: ``close_full`` closes the
position, ``close_partial`` closes its lot-rounded quantity and keeps the rest held, and
``amend_protection`` moves the held stop and target, tightening only.

Cash that moves with no fill (swap, financing, funding, dividends, commission) comes from the
host's cash port as ``CashEvent`` rows and changes the account the unit reads. The node passes
no cash port, because its venue books those itself.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, Protocol, TypeVar, cast

from qmf.core.chrono import Instant
from qmf.core.exact import Price
from qmf.core.fingerprint import Fingerprint
from qmf.core.identity import Instrument
from qmf.core.refusal import Ok, Result, is_refusal
from qmf.risk.unit_intent import (
    AmendProtection,
    CloseFull,
    ClosePartial,
    UnitExitIntent,
    check_amendment_tightens,
    parse_unit_intent,
)
from qml.motion import ClosedTrade
from qml.numbers import InstrumentRecord, lots
from qml.protocol.unit import (
    Account,
    CalibrationRow,
    DecisionRow,
    OwnPosition,
    QuoteBar,
    StateEvent,
    UnitStep,
)
from qml.unit.model import Side

from qmb._refuse import invalid, policy
from qmb.execution.fill import FillKind, Reached
from qmb.execution.financing import CashEvent, CashKind
from qmb.runloop.loop import RestingIntent, SliceObservation

__all__ = [
    "CashEvent",
    "CashKind",
    "CashPort",
    "ExecutionPort",
    "Fill",
    "FillKind",
    "HeldPosition",
    "JournalPort",
    "JournalRecord",
    "ListJournal",
    "Reached",
    "Skip",
    "UnitSliceHandler",
    "UnitTrade",
]

_CENT: Final[Decimal] = Decimal("0.01")
_R_PLACES: Final[Decimal] = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class HeldPosition:
    """A position the handler holds, with its live protection and what its entry fixed."""

    position: OwnPosition
    stop: Decimal
    target: Decimal | None
    decision_row_id: str
    entry_stamps: Mapping[str, Decimal]
    entry_stop: Decimal
    risk: Decimal
    """The money the whole entry quantity risked at its entry stop: the trade's 1 R."""
    realized_r: Decimal = Decimal(0)
    """The R the position's partial closes already took."""


@dataclass(frozen=True, slots=True)
class Fill:
    instant: Instant
    market_id: str
    position_id: str
    kind: FillKind
    side: Side
    price: Decimal
    quantity: Decimal
    receipt_quantity: Decimal | None
    """The sizer receipt's quantity on an entry; ``None`` on an exit."""
    residue_r: Decimal
    """The share of the receipt's risk the lot rounding left out, in R; 0 on an exit."""
    decision_row_id: str


@dataclass(frozen=True, slots=True)
class Skip:
    """An entry or partial close the host did not fill, with its reason and the R left out."""

    instant: Instant
    market_id: str
    decision_row_id: str
    reason: str
    residue_r: Decimal


@dataclass(frozen=True, slots=True)
class UnitTrade:
    """One closing fill. A partial close and the close of its rest are two trades."""

    trade_id: str
    market_id: str
    side: Side
    opened_at: Instant
    closed_at: Instant
    entry_price: Decimal
    exit_price: Decimal
    stop: Decimal
    """The entry stop, the level 1 R is measured against."""
    quantity: Decimal
    exit_kind: FillKind
    money: Decimal
    r: Decimal
    """``money`` over the whole entry's risk, so a position's trades add up to its R."""
    gap_through_stop: bool = False
    """The price jumped the stop and it filled at the first tradable price, past 1 R."""


JournalRecord = DecisionRow | CalibrationRow | StateEvent | Fill | Skip | UnitTrade | CashEvent


class JournalPort(Protocol):
    def append(self, record: JournalRecord, /) -> None: ...


@dataclass
class ListJournal:
    """A journal port that keeps every record in memory, in the order it came."""

    records: list[JournalRecord] = field(default_factory=list[JournalRecord])

    def append(self, record: JournalRecord, /) -> None:
        self.records.append(record)


class ExecutionPort(Protocol):
    """Where a fill happens. QMB's bar replay and the node's venue client each provide one."""

    def entry_price(self, market: str, side: Side, bar: QuoteBar, /) -> Decimal: ...

    def close_price(self, market: str, side: Side, bar: QuoteBar, /) -> Decimal: ...

    def protective(self, market: str, held: HeldPosition, bar: QuoteBar, /) -> Reached | None:
        """The stop, liquidation or target this bar reaches, the loss side first."""
        ...


class CashPort(Protocol):
    """The cash a replay books with no fill. The node passes none: its venue books its own."""

    def held(
        self, market: str, position: OwnPosition, since: Instant, until: Instant, bar: QuoteBar, /
    ) -> Result[tuple[CashEvent, ...]]:
        """What holding ``position`` from its market's bar at ``since`` to ``bar`` moved."""
        ...

    def filled(self, fill: Fill, /) -> tuple[CashEvent, ...]:
        """What a fill costs on top of its price, such as commission."""
        ...


class SteppingUnit(Protocol):
    def on_instant(self, instant: object, /) -> Result[UnitStep]: ...


_U = TypeVar("_U", bound=SteppingUnit)


class _At:
    def __init__(self, answer: Callable[[Instant], object]) -> None:
        self._answer = answer

    def at(self, instant: Instant, /) -> object:
        return self._answer(instant)


def _money(
    side: Side, entry: Decimal, exit_: Decimal, quantity: Decimal, record: InstrumentRecord
) -> Decimal:
    move = exit_ - entry if side is Side.LONG else entry - exit_
    return (move * quantity * record.value_per_point).quantize(_CENT, rounding=ROUND_HALF_EVEN)


def _stamps(row: DecisionRow | None) -> dict[str, Decimal]:
    """Each slot output the entry's decision row recorded as a number, by binding name."""
    stamps: dict[str, Decimal] = {}
    for out in () if row is None else row.slot_trail:
        try:
            stamps[out.binding] = Decimal(out.output or "")
        except ArithmeticError:
            continue
    return stamps


def _decimal(value: int, scale: int) -> Decimal:
    return Decimal(value).scaleb(-scale)


def _price(level: Decimal, instrument: Instrument) -> Price:
    exponent = level.as_tuple().exponent
    scale = -exponent if isinstance(exponent, int) and exponent < 0 else 0
    return Price(int(level.scaleb(scale)), instrument, scale)


class UnitSliceHandler:
    """``run_slice``'s five hooks over one hosted unit. Stream ids are the unit's market ids."""

    def __init__(
        self,
        *,
        stream: str,
        records: Mapping[str, InstrumentRecord],
        bars: Mapping[str, Mapping[int, QuoteBar]],
        opened_by: Fingerprint,
        equity: Decimal,
        execution: ExecutionPort,
        journal: JournalPort,
        seeded: Mapping[str, OwnPosition] | None = None,
        cash: CashPort | None = None,
    ) -> None:
        self._stream = stream
        self._records = records
        self._bars = bars
        self._opened_by = opened_by
        self._equity = equity
        self._execution = execution
        self._journal = journal
        self._cash_port = cash
        self._unit: SteppingUnit | None = None
        self._latest: dict[str, QuoteBar] = {}
        self._held: dict[str, HeldPosition] = {}
        self._foreign: dict[str, OwnPosition] = dict(seeded or {})
        self._closed: list[ClosedTrade] = []
        self._trades: list[UnitTrade] = []
        self._fills: list[Fill] = []
        self._cash: list[CashEvent] = []
        self._carried: dict[str, Instant] = {}
        self._stepped: tuple[int, UnitStep] | None = None
        self._entry_stamps: dict[str, dict[str, Decimal]] = {}
        self._entries = 0

    @classmethod
    def start(
        cls,
        host: Callable[[Mapping[str, _At]], Result[_U]],
        *,
        stream: str,
        records: Mapping[str, InstrumentRecord],
        bars: Mapping[str, Mapping[int, QuoteBar]],
        opened_by: Fingerprint,
        equity: Decimal,
        execution: ExecutionPort,
        journal: JournalPort,
        seeded: Mapping[str, OwnPosition] | None = None,
        cash: CashPort | None = None,
    ) -> Result[UnitSliceHandler]:
        """A handler whose unit ``host`` built from this handler's read surfaces.

        QMB passes ``construct_unit``; the node passes its resume call, so this file never
        restores a unit itself.
        """
        handler = cls(
            stream=stream,
            records=records,
            bars=bars,
            opened_by=opened_by,
            equity=equity,
            execution=execution,
            journal=journal,
            seeded=seeded,
            cash=cash,
        )
        unit = host(handler.read_surfaces())
        if is_refusal(unit):
            return unit
        handler._unit = unit.value
        return Ok(handler)

    def adopt(
        self,
        market: str,
        position: OwnPosition,
        *,
        stop: Decimal,
        entry_stop: Decimal,
        target: Decimal | None,
        decision_row_id: str,
    ) -> Result[None]:
        """Hold a position the unit opened before this handler started, as the node finds it
        at its venue after a process restart: its stop, target and exits are managed as the
        unit's own. A ``seeded`` position is another's, which the unit never closes."""
        record = self._records.get(market)
        if record is None:
            return invalid("market", "a unit adopts a position on its own markets", market=market)
        if self._position(market) is not None:
            return policy("market", "a unit holds one position per market", market=market)
        risk = _money(position.side, position.entry_price, entry_stop, position.quantity, record)
        self._held[market] = HeldPosition(
            position, stop, target, decision_row_id, {}, entry_stop, risk.copy_abs()
        )
        return Ok(None)

    def read_surfaces(self) -> dict[str, _At]:
        surfaces = {
            "account": _At(lambda _i: self._account()),
            "own_journal": _At(lambda _i: tuple(self._closed)),
        }
        for market in self._records:
            surfaces[f"bars:{self._stream}:{market}"] = _At(
                lambda _i, m=market: self._latest.get(m)
            )
            surfaces[f"own_position:{market}"] = _At(lambda _i, m=market: self._position(m))
        return surfaces

    def _account(self) -> Account:
        traded = sum((t.money for t in self._trades), Decimal(0))
        return Account(self._equity + traded + sum((c.money for c in self._cash), Decimal(0)))

    def _position(self, market: str) -> OwnPosition | None:
        held = self._held.get(market)
        return held.position if held is not None else self._foreign.get(market)

    @property
    def trades(self) -> tuple[UnitTrade, ...]:
        return tuple(self._trades)

    @property
    def fills(self) -> tuple[Fill, ...]:
        return tuple(self._fills)

    @property
    def cash_events(self) -> tuple[CashEvent, ...]:
        return tuple(self._cash)

    @property
    def open_positions(self) -> Mapping[str, OwnPosition]:
        held = {m: h.position for m, h in self._held.items()}
        return held | {m: p for m, p in self._foreign.items() if m not in held}

    def update_stream(
        self, stream_id: str, observation: SliceObservation | None, frontier: Instant
    ) -> Result[None]:
        del frontier
        if stream_id not in self._records:
            return invalid("stream_id", "a unit's streams are its market ids", stream_id=stream_id)
        if observation is not None and observation.instant.value_ns not in self._bars[stream_id]:
            return invalid(
                "observation",
                "every observation names a bar the run fed",
                stream_id=stream_id,
                instant_ns=observation.instant.value_ns,
            )
        return Ok(None)

    def scheduled_position_event(self, stream_id: str, frontier: Instant) -> Result[None]:
        bar = self._bars.get(stream_id, {}).get(frontier.value_ns)
        if bar is None:
            return Ok(None)
        since = self._carried.get(stream_id)
        self._carried[stream_id] = frontier
        held = self._held.get(stream_id)
        if self._cash_port is None or held is None or since is None:
            return Ok(None)
        booked = self._cash_port.held(stream_id, held.position, since, frontier, bar)
        if is_refusal(booked):
            return booked
        for event in booked.value:
            self._book(event)
        return Ok(None)

    def _book(self, event: CashEvent) -> None:
        self._cash.append(event)
        self._journal.append(event)

    def execute_resting(
        self,
        intent: RestingIntent,
        observation: SliceObservation | None,
        frontier: Instant,
        *,
        filled: Decimal | None = None,
    ) -> Result[bool]:
        """Fill a resting intent on the bar. ``filled`` is the quantity a venue filled of an
        entry it filled only in part, which the position then holds; QMB's replay fills whole."""
        if observation is None or not observation.closed:
            return Ok(False)
        bar = self._bars[intent.stream_id][observation.instant.value_ns]
        wire = cast("Mapping[str, object]", intent.order)
        if wire.get("intent_family") == "entry":
            self._fill_entry(intent.stream_id, wire, bar, frontier, filled)
        else:
            exited = self._fill_exit(intent.stream_id, wire, bar, frontier)
            if is_refusal(exited):
                return exited
        return Ok(True)

    def update_closed_data(
        self, stream_id: str, observation: SliceObservation, frontier: Instant
    ) -> Result[None]:
        bar = self._bars[stream_id][observation.instant.value_ns]
        self._latest[stream_id] = bar
        held = self._held.get(stream_id)
        if held is not None:
            reached = self._execution.protective(stream_id, held, bar)
            if reached is not None:
                self._close(
                    stream_id,
                    held,
                    reached.kind,
                    reached.price,
                    frontier,
                    held.decision_row_id,
                    gapped=reached.gap,
                )
        return Ok(None)

    def mint_intents(self, stream_id: str, frontier: Instant) -> Result[object]:
        step = self._step(frontier)
        if is_refusal(step):
            return step
        minted: list[RestingIntent] = []
        for intent in step.value.intents:
            wire = intent.to_wire()
            market = self._market_of(wire)
            if market != stream_id:
                continue
            made = RestingIntent.try_create(
                f"{wire['intent_family']}:{wire['decision_row_id']}", market, order=wire
            )
            if is_refusal(made):
                return made
            minted.append(made.value)
            if wire["intent_family"] == "entry":
                row_id = cast("str", wire["decision_row_id"])
                row = next((d for d in step.value.decisions if d.row_id == row_id), None)
                self._entry_stamps[row_id] = _stamps(row)
        return Ok(tuple(minted))

    def _step(self, frontier: Instant) -> Result[UnitStep]:
        if self._stepped is not None and self._stepped[0] == frontier.value_ns:
            return Ok(self._stepped[1])
        if self._unit is None:
            return invalid("unit", "the handler steps the unit its host built at start")
        step = self._unit.on_instant(frontier)
        if is_refusal(step):
            return step
        self._stepped = (frontier.value_ns, step.value)
        for record in (
            *step.value.decisions,
            *step.value.calibrations,
            *step.value.state_events,
        ):
            self._journal.append(record)
        return step

    def _market_of(self, wire: Mapping[str, object]) -> str | None:
        if wire.get("intent_family") == "entry":
            return cast("str", wire["market_id"])
        ref = cast("Mapping[str, object]", wire["position_ref"])
        return next(
            (m for m, h in self._held.items() if h.position.position_id == ref["position_id"]),
            next(
                (m for m, p in self._foreign.items() if p.position_id == ref["position_id"]),
                None,
            ),
        )

    def _fill_entry(
        self,
        market: str,
        wire: Mapping[str, object],
        bar: QuoteBar,
        frontier: Instant,
        filled: Decimal | None,
    ) -> None:
        row_id = cast("str", wire["decision_row_id"])
        stamps = self._entry_stamps.pop(row_id, {})
        record = self._records[market]
        receipt = Decimal(cast("str", wire["quantity"]))
        if self._position(market) is not None:
            self._journal.append(Skip(frontier, market, row_id, "a position is open", Decimal(0)))
            return
        sized = lots(receipt, record)
        if is_refusal(sized):
            reason = str(sized.context.get("reason"))
            self._journal.append(Skip(frontier, market, row_id, reason, Decimal(1)))
            return
        quantity = _decimal(sized.value.value, sized.value.scale) if filled is None else filled
        residue_r = ((receipt - quantity) / receipt).quantize(_R_PLACES, rounding=ROUND_HALF_EVEN)
        side = Side(cast("str", wire["direction"]))
        protection = cast("Mapping[str, object]", wire["protection"])
        targets = cast("Sequence[Mapping[str, object]]", protection.get("targets", ()))
        stop = Decimal(cast("str", protection["stop"]))
        price = self._execution.entry_price(market, side, bar)
        self._entries += 1
        position = OwnPosition(
            f"{self._opened_by.value[-12:]}-{self._entries}",
            side,
            quantity,
            price,
            self._opened_by,
            frontier,
        )
        self._held[market] = HeldPosition(
            position,
            stop,
            Decimal(cast("str", targets[0]["price"])) if targets else None,
            row_id,
            stamps,
            stop,
            _money(side, price, stop, quantity, record).copy_abs(),
        )
        fill = Fill(
            frontier,
            market,
            position.position_id,
            FillKind.ENTRY,
            side,
            price,
            quantity,
            receipt,
            residue_r,
            row_id,
        )
        self._record_fill(fill)

    def _record_fill(self, fill: Fill) -> None:
        self._fills.append(fill)
        self._journal.append(fill)
        for event in () if self._cash_port is None else self._cash_port.filled(fill):
            self._book(event)

    def _fill_exit(
        self, market: str, wire: Mapping[str, object], bar: QuoteBar, frontier: Instant
    ) -> Result[None]:
        parsed = parse_unit_intent(wire)
        if is_refusal(parsed):
            return parsed
        exit_ = parsed.value
        if not isinstance(exit_, UnitExitIntent):
            return invalid("intent_family", "an exit rests as a format-3 exit intent")
        held = self._held.get(market)
        if held is None or held.position.position_id != exit_.position_ref.position_id:
            return policy(
                "position_ref",
                "a unit closes only a position its own compiled fingerprint opened",
                position_id=exit_.position_ref.position_id,
            )
        row_id = exit_.decision_row_id
        price = self._execution.close_price(market, held.position.side, bar)
        match exit_.action:
            case CloseFull():
                self._close(market, held, FillKind.CLOSE, price, frontier, row_id)
            case ClosePartial(quantity=asked):
                sized = lots(_decimal(asked.value, asked.scale), self._records[market])
                if is_refusal(sized):
                    reason = str(sized.context.get("reason"))
                    self._journal.append(Skip(frontier, market, row_id, reason, Decimal(0)))
                    return Ok(None)
                quantity = _decimal(sized.value.value, sized.value.scale)
                if quantity > held.position.quantity:
                    return policy(
                        "quantity",
                        "a partial close closes at most the quantity the position holds",
                        asked=str(quantity),
                        held=str(held.position.quantity),
                    )
                self._close(market, held, FillKind.CLOSE, price, frontier, row_id, quantity)
            case AmendProtection(stop=stop, targets=targets):
                current = _price(held.stop, exit_.position_ref.instrument)
                tightens = check_amendment_tightens(
                    exit_, direction=held.position.side.value, current_stop=current
                )
                if is_refusal(tightens):
                    return tightens
                self._held[market] = replace(
                    held,
                    stop=_decimal(stop.value, stop.scale),
                    target=_decimal(targets[0].price.value, targets[0].price.scale)
                    if targets
                    else None,
                )
        return Ok(None)

    def _close(
        self,
        market: str,
        held: HeldPosition,
        kind: FillKind,
        price: Decimal,
        frontier: Instant,
        row_id: str,
        quantity: Decimal | None = None,
        *,
        gapped: bool = False,
    ) -> None:
        """Close ``quantity`` of the held position, or all of it; the rest stays held."""
        record = self._records[market]
        position = held.position
        closed = position.quantity if quantity is None else quantity
        money = _money(position.side, position.entry_price, price, closed, record)
        r = (
            (money / held.risk).quantize(_R_PLACES, rounding=ROUND_HALF_EVEN)
            if held.risk
            else Decimal(0)
        )
        fill = Fill(
            frontier,
            market,
            position.position_id,
            kind,
            position.side,
            price,
            closed,
            None,
            Decimal(0),
            row_id,
        )
        trade = UnitTrade(
            position.position_id,
            market,
            position.side,
            position.opened_at,
            frontier,
            position.entry_price,
            price,
            held.entry_stop,
            closed,
            kind,
            money,
            r,
            gap_through_stop=gapped and kind is FillKind.STOP,
        )
        self._record_fill(fill)
        self._trades.append(trade)
        self._journal.append(trade)
        rest = position.quantity - closed
        if rest:
            self._held[market] = replace(
                held,
                position=replace(position, quantity=rest),
                realized_r=held.realized_r + trade.r,
            )
            return
        del self._held[market]
        self._closed.append(
            ClosedTrade(
                trade_id=position.position_id,
                opened_at=position.opened_at,
                closed_at=frontier,
                side=position.side,
                market_id=market,
                world="replay",
                r_after_costs=held.realized_r + trade.r,
                entry_stamps=held.entry_stamps,
            )
        )
