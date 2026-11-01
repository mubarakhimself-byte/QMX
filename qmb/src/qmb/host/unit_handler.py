"""The one run-slice handler for a hosted unit (Level 0 AD-5, R1-L0-02).

``run_slice`` drives any handler through its five hooks, so QMB's unit runner and the trading
node's runtime both drive a unit through this file. The host builds the ``HostedUnit`` from the
read surfaces this handler serves (``UnitSliceHandler.start`` takes the host's own
``construct_unit`` or resume call), and injects the execution and journal ports.

Per slice, in ``run_slice``'s order: a resting entry or close fills against the new bar
(``execute_resting``); the bar becomes readable and a held position's stop or target is checked
against it (``update_closed_data``); then the unit steps once for the slice's instant and its
intents rest for the next bar (``mint_intents``). A fill's quantity is the sizer receipt's
rounded down to the market's lot step; below the minimum lot the entry is skipped with its
reason. The handler closes only positions this compiled fingerprint opened.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum
from typing import Final, Protocol, TypeVar, cast

from qmf.core.chrono import Instant
from qmf.core.fingerprint import Fingerprint
from qmf.core.refusal import Ok, Result, is_refusal
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
from qmb.runloop.loop import RestingIntent, SliceObservation

__all__ = [
    "ExecutionPort",
    "Fill",
    "FillKind",
    "HeldPosition",
    "JournalPort",
    "JournalRecord",
    "ListJournal",
    "NextOpenExecution",
    "Skip",
    "UnitSliceHandler",
    "UnitTrade",
]

_CENT: Final[Decimal] = Decimal("0.01")
_R_PLACES: Final[Decimal] = Decimal("0.0001")


class FillKind(StrEnum):
    ENTRY = "entry"
    STOP = "stop"
    TARGET = "target"
    CLOSE = "close"


@dataclass(frozen=True, slots=True)
class HeldPosition:
    """A position the handler holds, with the protection its entry intent carried."""

    position: OwnPosition
    stop: Decimal
    target: Decimal | None
    decision_row_id: str
    entry_stamps: Mapping[str, Decimal]


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
    """An entry the host did not fill, with its reason and the lots rounding left out."""

    instant: Instant
    market_id: str
    decision_row_id: str
    reason: str
    residue_r: Decimal


@dataclass(frozen=True, slots=True)
class UnitTrade:
    trade_id: str
    market_id: str
    side: Side
    opened_at: Instant
    closed_at: Instant
    entry_price: Decimal
    exit_price: Decimal
    stop: Decimal
    quantity: Decimal
    exit_kind: FillKind
    money: Decimal
    r: Decimal


JournalRecord = DecisionRow | CalibrationRow | StateEvent | Fill | Skip | UnitTrade


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

    def entry_price(self, side: Side, bar: QuoteBar, /) -> Decimal: ...

    def close_price(self, side: Side, bar: QuoteBar, /) -> Decimal: ...

    def protective(self, held: HeldPosition, bar: QuoteBar, /) -> tuple[FillKind, Decimal] | None:
        """The stop or target this bar reaches, the stop first when it reaches both."""
        ...


@dataclass(frozen=True, slots=True)
class NextOpenExecution:
    """Bars fidelity: an order fills at the next bar's open on its side of the quote."""

    def entry_price(self, side: Side, bar: QuoteBar, /) -> Decimal:
        return bar.ask.open if side is Side.LONG else bar.bid.open

    def close_price(self, side: Side, bar: QuoteBar, /) -> Decimal:
        return bar.bid.open if side is Side.LONG else bar.ask.open

    def protective(self, held: HeldPosition, bar: QuoteBar, /) -> tuple[FillKind, Decimal] | None:
        if held.position.side is Side.LONG:
            if bar.bid.low <= held.stop:
                return FillKind.STOP, held.stop
            if held.target is not None and bar.bid.high >= held.target:
                return FillKind.TARGET, held.target
            return None
        if bar.ask.high >= held.stop:
            return FillKind.STOP, held.stop
        if held.target is not None and bar.ask.low <= held.target:
            return FillKind.TARGET, held.target
        return None


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
    ) -> None:
        self._stream = stream
        self._records = records
        self._bars = bars
        self._opened_by = opened_by
        self._equity = equity
        self._execution = execution
        self._journal = journal
        self._unit: SteppingUnit | None = None
        self._latest: dict[str, QuoteBar] = {}
        self._held: dict[str, HeldPosition] = {}
        self._foreign: dict[str, OwnPosition] = dict(seeded or {})
        self._closed: list[ClosedTrade] = []
        self._trades: list[UnitTrade] = []
        self._fills: list[Fill] = []
        self._stepped: tuple[int, UnitStep] | None = None
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
        )
        unit = host(handler.read_surfaces())
        if is_refusal(unit):
            return unit
        handler._unit = unit.value
        return Ok(handler)

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
        return Account(self._equity + sum((t.money for t in self._trades), Decimal(0)))

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
        del stream_id, frontier
        return Ok(None)

    def execute_resting(
        self, intent: RestingIntent, observation: SliceObservation | None, frontier: Instant
    ) -> Result[bool]:
        if observation is None or not observation.closed:
            return Ok(False)
        bar = self._bars[intent.stream_id][observation.instant.value_ns]
        wire = cast("Mapping[str, object]", intent.order)
        if wire.get("intent_family") == "entry":
            self._fill_entry(intent.stream_id, wire, bar, frontier)
        else:
            closed = self._fill_close(intent.stream_id, wire, bar, frontier)
            if is_refusal(closed):
                return closed
        return Ok(True)

    def update_closed_data(
        self, stream_id: str, observation: SliceObservation, frontier: Instant
    ) -> Result[None]:
        bar = self._bars[stream_id][observation.instant.value_ns]
        self._latest[stream_id] = bar
        held = self._held.get(stream_id)
        if held is not None:
            reached = self._execution.protective(held, bar)
            if reached is not None:
                self._close(stream_id, held, reached[0], reached[1], frontier, held.decision_row_id)
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

    def _decision(self, row_id: str) -> DecisionRow | None:
        if self._stepped is None:
            return None
        return next((d for d in self._stepped[1].decisions if d.row_id == row_id), None)

    def _fill_entry(
        self, market: str, wire: Mapping[str, object], bar: QuoteBar, frontier: Instant
    ) -> None:
        row_id = cast("str", wire["decision_row_id"])
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
        quantity = Decimal(sized.value.value).scaleb(-sized.value.scale)
        residue_r = ((receipt - quantity) / receipt).quantize(_R_PLACES, rounding=ROUND_HALF_EVEN)
        side = Side(cast("str", wire["direction"]))
        protection = cast("Mapping[str, object]", wire["protection"])
        targets = cast("Sequence[Mapping[str, object]]", protection.get("targets", ()))
        price = self._execution.entry_price(side, bar)
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
            Decimal(cast("str", protection["stop"])),
            Decimal(cast("str", targets[0]["price"])) if targets else None,
            row_id,
            _stamps(self._decision(row_id)),
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
        self._fills.append(fill)
        self._journal.append(fill)

    def _fill_close(
        self, market: str, wire: Mapping[str, object], bar: QuoteBar, frontier: Instant
    ) -> Result[None]:
        ref = cast("Mapping[str, object]", wire["position_ref"])
        held = self._held.get(market)
        if held is None or held.position.position_id != ref["position_id"]:
            return policy(
                "position_ref",
                "a unit closes only a position its own compiled fingerprint opened",
                position_id=str(ref["position_id"]),
            )
        price = self._execution.close_price(held.position.side, bar)
        self._close(
            market, held, FillKind.CLOSE, price, frontier, cast("str", wire["decision_row_id"])
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
    ) -> None:
        record = self._records[market]
        position = held.position
        del self._held[market]
        money = _money(position.side, position.entry_price, price, position.quantity, record)
        risk = _money(
            position.side, position.entry_price, held.stop, position.quantity, record
        ).copy_abs()
        r = (money / risk).quantize(_R_PLACES, rounding=ROUND_HALF_EVEN) if risk else Decimal(0)
        fill = Fill(
            frontier,
            market,
            position.position_id,
            kind,
            position.side,
            price,
            position.quantity,
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
            held.stop,
            position.quantity,
            kind,
            money,
            r,
        )
        self._fills.append(fill)
        self._trades.append(trade)
        self._journal.append(fill)
        self._journal.append(trade)
        self._closed.append(
            ClosedTrade(
                trade_id=position.position_id,
                opened_at=position.opened_at,
                closed_at=frontier,
                side=position.side,
                market_id=market,
                world="replay",
                r_after_costs=r,
                entry_stamps=held.entry_stamps,
            )
        )
