"""Daily-swap financing as a scheduled rollover cash event (FEE-4, FEE-5, Story 17.5).

Sub-phase 2 applies an exact-integer ``Money`` debit or credit per open position,
per instrument, per direction — never an order fill, never per slice. The
accounting-rollover instant comes from the bound broker market-hours calendar,
never a hardcoded wall time. Triple-swap weekday, multiplier, sign convention,
and weekend/holiday handling are read from a versioned per-broker calibration
whose rate content stays deferred to GAP-0048. A missing swap table is a typed
refusal, never a silent zero. Each applied swap mints a distinct CT-13 risk-
transition journal event; cost drag decomposes fill P&L, slippage, commission,
and financing.

A unit run's carry is a ``CarrySchedule`` per market, read from its instrument record (QB-04,
LD-13). Every amount is booked as a ``CashEvent`` at venue time while a position is held:

- ``swap`` ``{long, short, triple_day}``: money per lot per night, at each venue day boundary
  closing a day the market traded, three nights on the triple day;
- ``financing`` ``{long, short, days_per_year, triple_day}``: a yearly share of the position's
  notional, booked per night at the same rollovers;
- ``funding_interval`` with the run's recorded rates: at each funding time from the venue day's
  start, a positive rate is paid by longs to shorts on the notional at the first price after it;
- ``events`` ``{kind: dividend, at, amount_per_lot, side}``: on the ex-date ``at`` the venue
  day boundary that opens the day holding it books ``amount_per_lot`` to the named side, or to
  longs and from shorts when no side is named.

A funding time with no recorded rate refuses the run, never a silent zero.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, tzinfo
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from enum import StrEnum
from fractions import Fraction
from types import MappingProxyType
from typing import Final, Protocol, cast, runtime_checkable

from qmf.core.chrono import Instant, TradingDate, WriterId
from qmf.core.exact import MONEY_STORAGE_SCALE, Money, Quantity
from qmf.core.fingerprint import Fingerprint, World, fingerprint
from qmf.core.refusal import Ok, Result, is_refusal
from qmf.data.journal import JournalEvent, JournalEventType
from qmf.risk.door import Direction
from qmf.risk.exit_record import CostComponent
from qml.protocol.unit import OwnPosition, QuoteBar
from qml.unit.model import Side

from qmb._refuse import clean_token, invalid, policy, unavailable
from qmb.execution.fidelity import FidelityIdentity, stamp_fidelity
from qmb.execution.ports import (
    COMPOSITION_VERSION,
    FINANCING_IS_ORDER_FILL,
    TAINT_OPTIMISTIC,
)

__all__ = [
    "COST_COMPONENT_FINANCING",
    "COST_DRAG_COMMISSION",
    "COST_DRAG_COMPONENTS",
    "COST_DRAG_FILL_PNL",
    "COST_DRAG_FINANCING",
    "COST_DRAG_SLIPPAGE",
    "FINANCING_ADAPTER_SCHEDULED",
    "FINANCING_CALIBRATION_KEY",
    "FINANCING_CONTENT_DEFERRED_TO",
    "FINANCING_JOURNAL_EVENT_TYPE",
    "FINANCING_JOURNAL_KIND",
    "FINANCING_JOURNAL_SUBTYPE",
    "WEEKDAYS",
    "WEEKEND_HOLIDAY_APPLY",
    "WEEKEND_HOLIDAY_HANDLING",
    "WEEKEND_HOLIDAY_SKIP",
    "CarrySchedule",
    "CashEvent",
    "CashKind",
    "CostDrag",
    "FinancingCashEvent",
    "FinancingRollover",
    "FinancingScheduler",
    "OpenPosition",
    "RolloverCalendar",
    "SwapCalibration",
    "SwapCharge",
    "SwapRate",
    "apply_financing_rollover",
    "carry_schedule",
    "charge_swap",
    "decompose_cost_drag",
    "financing_calibration_fingerprint",
    "financing_identity",
    "fingerprint_financing",
    "lookup_swap_rate",
    "mint_financing_journal_event",
    "read_funding_rates",
]

FINANCING_ADAPTER_SCHEDULED: Final[str] = "scheduled"
FINANCING_CALIBRATION_KEY: Final[str] = "financing_calibration"
FINANCING_CONTENT_DEFERRED_TO: Final[str] = "GAP-0048"
COST_COMPONENT_FINANCING: Final[str] = "financing"
COST_DRAG_FILL_PNL: Final[str] = "fill-pnl"
COST_DRAG_SLIPPAGE: Final[str] = "slippage"
COST_DRAG_COMMISSION: Final[str] = "commission"
COST_DRAG_FINANCING: Final[str] = COST_COMPONENT_FINANCING
COST_DRAG_COMPONENTS: Final[tuple[str, ...]] = (
    COST_DRAG_FILL_PNL,
    COST_DRAG_SLIPPAGE,
    COST_DRAG_COMMISSION,
    COST_DRAG_FINANCING,
)
FINANCING_JOURNAL_EVENT_TYPE: Final[str] = JournalEventType.RISK_TRANSITION.value
FINANCING_JOURNAL_KIND: Final[str] = "financing"
FINANCING_JOURNAL_SUBTYPE: Final[str] = "swap-rollover"
WEEKDAYS: Final[tuple[str, ...]] = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)
WEEKEND_HOLIDAY_SKIP: Final[str] = "skip"
WEEKEND_HOLIDAY_APPLY: Final[str] = "apply"
WEEKEND_HOLIDAY_HANDLING: Final[tuple[str, ...]] = (
    WEEKEND_HOLIDAY_SKIP,
    WEEKEND_HOLIDAY_APPLY,
)
_LEGAL_WEEKDAYS: Final[frozenset[str]] = frozenset(WEEKDAYS)
_LEGAL_HANDLING: Final[frozenset[str]] = frozenset(WEEKEND_HOLIDAY_HANDLING)


def financing_identity() -> dict[str, object]:
    """Identity-bearing financing-port fields. Package SemVer is omitted."""
    return {
        "adapter_id": FINANCING_ADAPTER_SCHEDULED,
        "applied_at": "accounting-rollover",
        "applied_per_slice": False,
        "calendar_source": "broker-market-hours-calendar",
        "calibration_key": FINANCING_CALIBRATION_KEY,
        "component_name": COST_COMPONENT_FINANCING,
        "content_deferred_to": FINANCING_CONTENT_DEFERRED_TO,
        "cost_drag": list(COST_DRAG_COMPONENTS),
        "financing_is_order_fill": FINANCING_IS_ORDER_FILL,
        "journal_event_type": FINANCING_JOURNAL_EVENT_TYPE,
        "journal_kind": FINANCING_JOURNAL_KIND,
        "journal_subtype": FINANCING_JOURNAL_SUBTYPE,
        "per_broker": True,
        "per_direction": True,
        "per_instrument": True,
        "silent_zero_on_missing_table": False,
        "subphase": "scheduled-position-events",
        "taint_field": TAINT_OPTIMISTIC,
        "weekend_holiday_handling": list(WEEKEND_HOLIDAY_HANDLING),
        "weekdays": list(WEEKDAYS),
    }


def fingerprint_financing() -> Result[Fingerprint]:
    """``fp1`` over :func:`financing_identity`."""
    return fingerprint(financing_identity())


@runtime_checkable
class RolloverCalendar(Protocol):
    """Broker market-hours calendar answering the accounting-rollover instant.

    The rollover wall time is never hardcoded here; the bound calendar supplies
    it (DEC-0135, AD-8). Weekend/holiday is a schedule fact of that calendar.
    """

    def is_rollover_instant(self, instant: Instant) -> Result[bool]:
        """Whether ``instant`` is this calendar's accounting-rollover instant."""
        ...

    def trading_date_of(self, instant: Instant) -> Result[TradingDate]:
        """Trading date of ``instant`` under this calendar's rollover rule."""
        ...

    def weekday_of(self, trading_date: TradingDate) -> Result[str]:
        """Weekday token of ``trading_date`` (monday..sunday)."""
        ...

    def is_weekend_or_holiday(self, trading_date: TradingDate) -> Result[bool]:
        """Whether ``trading_date`` is a weekend or in-scope holiday."""
        ...


@dataclass(frozen=True, slots=True)
class SwapRate:
    """One swap-table cell: instrument stream × direction → signed per-unit Money."""

    stream_id: str
    direction: Direction
    per_unit: Money

    def fp1_identity(self) -> dict[str, object]:
        """Canonical identity. Package SemVer never enters."""
        return {
            "class": "swap-rate",
            "direction": self.direction.value,
            "per_unit": self.per_unit.fp1_identity(),
            "stream_id": self.stream_id,
        }

    @classmethod
    def try_create(
        cls,
        stream_id: object,
        direction: object,
        per_unit: object,
    ) -> Result[SwapRate]:
        """Validate one table cell. Sign is the carry convention (credit may be +)."""
        token = clean_token(stream_id)
        if token is None:
            return invalid(
                "stream_id",
                "a swap rate names a non-empty instrument stream id",
                given=repr(stream_id),
            )
        sided = _require_direction(direction)
        if is_refusal(sided):
            return sided
        if not isinstance(per_unit, Money):
            return invalid(
                "per_unit",
                "a swap rate is exact-integer Money, never a binary float (FEE-4, CT-01)",
                given=repr(type(per_unit).__name__),
            )
        return Ok(cls(stream_id=token, direction=sided.value, per_unit=per_unit))


@dataclass(frozen=True, slots=True)
class SwapCalibration:
    """Versioned per-broker swap schedule. Rates are never invented (SC-07, DEC-0135)."""

    broker_id: str
    format_version: int
    fingerprint: Fingerprint
    rates: tuple[SwapRate, ...]
    weekend_holiday_handling: str
    triple_swap_weekday: str | None = None
    triple_swap_multiplier: int | None = None
    calendar_identity: dict[str, object] | None = None

    def fp1_identity(self) -> dict[str, object]:
        """Canonical identity. The derived fingerprint is omitted."""
        content: dict[str, object] = {
            "broker_id": self.broker_id,
            "class": "swap-calibration",
            "format_version": self.format_version,
            "per_broker": True,
            "rates": [item.fp1_identity() for item in self.rates],
            "weekend_holiday_handling": self.weekend_holiday_handling,
        }
        if self.triple_swap_weekday is not None:
            content["triple_swap_weekday"] = self.triple_swap_weekday
        if self.triple_swap_multiplier is not None:
            content["triple_swap_multiplier"] = self.triple_swap_multiplier
        if self.calendar_identity is not None:
            content["calendar_identity"] = dict(self.calendar_identity)
        return content

    @classmethod
    def try_create(
        cls,
        broker_id: object,
        *,
        rates: object,
        weekend_holiday_handling: object,
        format_version: object = 1,
        triple_swap_weekday: object = None,
        triple_swap_multiplier: object = None,
        calendar_identity: object = None,
        cited_fingerprint: object = None,
    ) -> Result[SwapCalibration]:
        """Build a fingerprinted swap table. No default numeric content is filled in."""
        broker = clean_token(broker_id)
        if broker is None:
            return invalid(
                "broker_id",
                "a swap calibration is per-broker (DEC-0135)",
                given=repr(broker_id),
            )
        if (
            not isinstance(format_version, int)
            or isinstance(format_version, bool)
            or format_version < 1
        ):
            return invalid(
                "format_version",
                "calibration format version is a positive integer",
                given=repr(format_version),
            )
        parsed_rates = _as_rates(rates)
        if is_refusal(parsed_rates):
            return parsed_rates
        handling = clean_token(weekend_holiday_handling)
        if handling not in _LEGAL_HANDLING:
            return invalid(
                "weekend_holiday_handling",
                "weekend/holiday handling is skip or apply, read from the calibration "
                "artifact, never invented (FEE-4, SC-07)",
                given=repr(weekend_holiday_handling),
                allowed=list(WEEKEND_HOLIDAY_HANDLING),
            )
        weekday = _optional_weekday(triple_swap_weekday)
        if is_refusal(weekday):
            return weekday
        multiplier = _optional_multiplier(triple_swap_multiplier)
        if is_refusal(multiplier):
            return multiplier
        if weekday.value is not None and multiplier.value is None:
            return unavailable(
                "triple_swap_multiplier",
                "a declared triple-swap weekday reads its multiplier from the "
                "calibration artifact; absence never invents a 3x (FEE-4, SC-07)",
                weekday=weekday.value,
                gap=FINANCING_CONTENT_DEFERRED_TO,
            )
        if weekday.value is None and multiplier.value is not None:
            return invalid(
                "triple_swap_weekday",
                "a triple-swap multiplier requires the weekday it applies on, from "
                "the artifact, never a hardcoded Wednesday (FEE-4, SC-07)",
            )
        calendar = _optional_calendar_identity(calendar_identity)
        if is_refusal(calendar):
            return calendar
        pending = cls(
            broker_id=broker,
            format_version=format_version,
            fingerprint=Fingerprint(value="fp1:sha256:" + ("0" * 64)),
            rates=parsed_rates.value,
            weekend_holiday_handling=handling,
            triple_swap_weekday=weekday.value,
            triple_swap_multiplier=multiplier.value,
            calendar_identity=calendar.value,
        )
        if isinstance(cited_fingerprint, Fingerprint):
            stamped = cited_fingerprint
        else:
            derived = fingerprint(pending.fp1_identity())
            if is_refusal(derived):
                return derived
            stamped = derived.value
        return Ok(
            cls(
                broker_id=pending.broker_id,
                format_version=pending.format_version,
                fingerprint=stamped,
                rates=pending.rates,
                weekend_holiday_handling=pending.weekend_holiday_handling,
                triple_swap_weekday=pending.triple_swap_weekday,
                triple_swap_multiplier=pending.triple_swap_multiplier,
                calendar_identity=pending.calendar_identity,
            )
        )


@dataclass(frozen=True, slots=True)
class OpenPosition:
    """One open position the rollover scheduler charges (FEE-4)."""

    stream_id: str
    direction: Direction
    quantity: Quantity

    def fp1_identity(self) -> dict[str, object]:
        """Canonical identity. Package SemVer never enters."""
        return {
            "class": "open-position",
            "direction": self.direction.value,
            "quantity": self.quantity.fp1_identity(),
            "stream_id": self.stream_id,
        }

    @classmethod
    def try_create(
        cls,
        stream_id: object,
        direction: object,
        quantity: object,
    ) -> Result[OpenPosition]:
        """Validate an open position. Quantity is a positive exact count."""
        token = clean_token(stream_id)
        if token is None:
            return invalid(
                "stream_id",
                "an open position names a non-empty instrument stream id",
                given=repr(stream_id),
            )
        sided = _require_direction(direction)
        if is_refusal(sided):
            return sided
        if not isinstance(quantity, Quantity):
            return invalid(
                "quantity",
                "an open position quantity is exact Quantity, never a binary float",
                given=repr(type(quantity).__name__),
            )
        if quantity.as_fraction() <= 0:
            return invalid(
                "quantity",
                "an open position quantity is a positive exact count",
                given=str(quantity.as_fraction()),
            )
        return Ok(cls(stream_id=token, direction=sided.value, quantity=quantity))


@dataclass(frozen=True, slots=True)
class SwapCharge:
    """Per-position swap result. ``skipped`` is weekend/holiday skip, never a missing table."""

    amount: Money | None
    day_multiplier: int
    skipped: bool

    def fp1_identity(self) -> dict[str, object]:
        """Canonical identity. Package SemVer never enters."""
        content: dict[str, object] = {
            "class": "swap-charge",
            "day_multiplier": self.day_multiplier,
            "skipped": self.skipped,
        }
        if self.amount is not None:
            content["amount"] = self.amount.fp1_identity()
        return content


@dataclass(frozen=True, slots=True)
class FinancingCashEvent:
    """One applied rollover debit/credit plus its distinct CT-13 journal event."""

    position: OpenPosition
    amount: Money
    day_multiplier: int
    trading_date: TradingDate
    journal_event: JournalEvent
    component: CostComponent
    taint: str = TAINT_OPTIMISTIC

    def fp1_identity(self) -> dict[str, object]:
        """Canonical identity. Taint is omitted (DEC-0164)."""
        return {
            "amount": self.amount.fp1_identity(),
            "class": "financing-cash-event",
            "component": self.component.fp1_identity(),
            "day_multiplier": self.day_multiplier,
            "journal_event": self.journal_event.fingerprint.value,
            "position": self.position.fp1_identity(),
            "trading_date": self.trading_date.fp1_identity(),
        }


@dataclass(frozen=True, slots=True)
class FinancingRollover:
    """The sub-phase 2 cash events at one accounting-rollover instant."""

    instant: Instant
    events: tuple[FinancingCashEvent, ...]
    skipped: tuple[OpenPosition, ...]
    taint: str = TAINT_OPTIMISTIC

    def fp1_identity(self) -> dict[str, object]:
        """Canonical identity. Taint is omitted (DEC-0164)."""
        return {
            "class": "financing-rollover",
            "events": [item.fp1_identity() for item in self.events],
            "financing_is_order_fill": FINANCING_IS_ORDER_FILL,
            "instant_ns": self.instant.value_ns,
            "skipped": [item.fp1_identity() for item in self.skipped],
        }


@dataclass(frozen=True, slots=True)
class CostDrag:
    """Four separately attributable cost-drag lines (FEE-5)."""

    fill_pnl: Money
    slippage: Money
    commission: Money
    financing: Money

    def fp1_identity(self) -> dict[str, object]:
        """Canonical identity. Package SemVer never enters."""
        return {
            "class": "cost-drag",
            "commission": self.commission.fp1_identity(),
            "fill_pnl": self.fill_pnl.fp1_identity(),
            "financing": self.financing.fp1_identity(),
            "slippage": self.slippage.fp1_identity(),
        }

    def components(self) -> Result[tuple[CostComponent, ...]]:
        """Named cost components. Fill P&L is never folded with financing."""
        return _cost_drag_components(self)

    def total(self) -> Result[Money]:
        """Sum of the four lines. Same-currency only; no silent conversion."""
        first = self.fill_pnl.add(self.slippage)
        if is_refusal(first):
            return first
        second = first.value.add(self.commission)
        if is_refusal(second):
            return second
        return second.value.add(self.financing)


def lookup_swap_rate(
    calibration: SwapCalibration,
    stream_id: object,
    direction: object,
) -> Result[Money]:
    """Per-unit daily swap for instrument × direction. Missing cell refuses, never zeros."""
    token = clean_token(stream_id)
    if token is None:
        return invalid(
            "stream_id",
            "swap lookup names a non-empty instrument stream id",
            given=repr(stream_id),
        )
    sided = _require_direction(direction)
    if is_refusal(sided):
        return sided
    for rate in calibration.rates:
        if rate.stream_id == token and rate.direction is sided.value:
            return Ok(rate.per_unit)
    return unavailable(
        "swap_table",
        "an open multi-day position whose instrument has no bound swap table is a "
        "typed refusal, never a silent zero swap (FEE-4, B-6, SC-07)",
        stream_id=token,
        direction=sided.value.value,
        broker_id=calibration.broker_id,
        gap=FINANCING_CONTENT_DEFERRED_TO,
    )


def charge_swap(
    position: OpenPosition,
    calibration: SwapCalibration,
    *,
    weekday: object,
    closed: object,
) -> Result[SwapCharge]:
    """Exact-integer debit/credit for one position at one rollover.

    Triple-swap weekday and weekend/holiday handling come from the artifact.
    A closed day with ``skip`` is an explicit no-charge, not a missing table.
    """
    if not isinstance(closed, bool):
        return invalid(
            "closed",
            "weekend/holiday is a bool schedule fact from the bound calendar",
            given=repr(type(closed).__name__),
        )
    day = clean_token(weekday)
    if day not in _LEGAL_WEEKDAYS:
        return invalid(
            "weekday",
            "weekday is monday..sunday from the bound calendar, never invented",
            given=repr(weekday),
            allowed=list(WEEKDAYS),
        )
    if closed:
        if calibration.weekend_holiday_handling == WEEKEND_HOLIDAY_SKIP:
            return Ok(SwapCharge(amount=None, day_multiplier=0, skipped=True))
        if calibration.weekend_holiday_handling != WEEKEND_HOLIDAY_APPLY:
            return unavailable(
                "weekend_holiday_handling",
                "weekend/holiday handling is read from the calibration artifact (FEE-4, SC-07)",
                given=calibration.weekend_holiday_handling,
                gap=FINANCING_CONTENT_DEFERRED_TO,
            )
    multiplier = 1
    if calibration.triple_swap_weekday is not None and day == calibration.triple_swap_weekday:
        if calibration.triple_swap_multiplier is None:
            return unavailable(
                "triple_swap_multiplier",
                "triple-swap multiplier is read from the calibration artifact; "
                "absence never invents a 3x (FEE-4, SC-07)",
                gap=FINANCING_CONTENT_DEFERRED_TO,
            )
        multiplier = calibration.triple_swap_multiplier
    unit = lookup_swap_rate(calibration, position.stream_id, position.direction)
    if is_refusal(unit):
        return unit
    amount = _scale_money(
        unit.value,
        position.quantity.as_fraction() * multiplier,
    )
    if is_refusal(amount):
        return amount
    return Ok(SwapCharge(amount=amount.value, day_multiplier=multiplier, skipped=False))


def mint_financing_journal_event(
    *,
    position: OpenPosition,
    amount: Money,
    day_multiplier: int,
    instant: Instant,
    writer: WriterId,
    world: World,
    sequence: int,
) -> Result[JournalEvent]:
    """Distinct CT-13 risk-transition event, never a fill event (FEE-5, B-4)."""
    return JournalEvent.try_create(
        event_type=FINANCING_JOURNAL_EVENT_TYPE,
        writer=writer,
        sequence=sequence,
        instant=instant,
        world=world,
        payload={
            "amount": amount.fp1_identity(),
            "day_multiplier": day_multiplier,
            "direction": position.direction.value,
            "financing_is_order_fill": FINANCING_IS_ORDER_FILL,
            "kind": FINANCING_JOURNAL_KIND,
            "quantity": position.quantity.fp1_identity(),
            "stream_id": position.stream_id,
            "subtype": FINANCING_JOURNAL_SUBTYPE,
        },
    )


def apply_financing_rollover(
    port: object,
    positions: object,
    *,
    frontier: object,
    calendar: object,
    writer: object,
    world: object = World.REPLAY,
    start_sequence: object = 0,
    stream_id: object = None,
) -> Result[FinancingRollover]:
    """Sub-phase 2: apply swap at the accounting-rollover instant, not per slice.

    The rollover instant is answered by ``calendar`` — never hardcoded. Missing
    calibration or a missing swap-table cell is a typed refusal, never zero.
    """
    if not isinstance(frontier, Instant):
        return invalid(
            "frontier",
            "financing applies at an Instant frontier, never a wall-clock string",
            given=repr(type(frontier).__name__),
        )
    if not isinstance(calendar, RolloverCalendar):
        return invalid(
            "calendar",
            "the accounting-rollover instant comes from the bound broker "
            "market-hours calendar, never a hardcoded wall time (AD-8, DEC-0135)",
            given=repr(type(calendar).__name__),
        )
    if not isinstance(writer, WriterId):
        return invalid(
            "writer",
            "a CT-13 financing event is written under an AD-8 WriterId",
            given=repr(type(writer).__name__),
        )
    if not isinstance(world, World):
        return invalid(
            "world",
            "a CT-13 financing event is instantiated per world",
            given=repr(world),
        )
    if (
        isinstance(start_sequence, bool)
        or not isinstance(start_sequence, int)
        or start_sequence < 0
    ):
        return invalid(
            "start_sequence",
            "journal sequence is a non-negative integer",
            given=repr(start_sequence),
        )
    parsed = _as_positions(positions)
    if is_refusal(parsed):
        return parsed
    cohort = parsed.value
    if stream_id is not None:
        token = clean_token(stream_id)
        if token is None:
            return invalid(
                "stream_id",
                "a stream filter is a non-empty instrument stream id",
                given=repr(stream_id),
            )
        cohort = tuple(item for item in cohort if item.stream_id == token)
    at_rollover = calendar.is_rollover_instant(frontier)
    if is_refusal(at_rollover):
        return at_rollover
    if not at_rollover.value:
        return Ok(
            FinancingRollover(instant=frontier, events=(), skipped=()),
        )
    calibration = _calibration_of(port)
    if is_refusal(calibration):
        return calibration
    trading = calendar.trading_date_of(frontier)
    if is_refusal(trading):
        return trading
    weekday = calendar.weekday_of(trading.value)
    if is_refusal(weekday):
        return weekday
    closed = calendar.is_weekend_or_holiday(trading.value)
    if is_refusal(closed):
        return closed
    events: list[FinancingCashEvent] = []
    skipped: list[OpenPosition] = []
    sequence = start_sequence
    for position in cohort:
        charged = charge_swap(
            position,
            calibration.value,
            weekday=weekday.value,
            closed=closed.value,
        )
        if is_refusal(charged):
            return charged
        if charged.value.skipped or charged.value.amount is None:
            skipped.append(position)
            continue
        journaled = mint_financing_journal_event(
            position=position,
            amount=charged.value.amount,
            day_multiplier=charged.value.day_multiplier,
            instant=frontier,
            writer=writer,
            world=world,
            sequence=sequence,
        )
        if is_refusal(journaled):
            return journaled
        component = CostComponent.try_create(
            COST_COMPONENT_FINANCING,
            charged.value.amount,
            FINANCING_ADAPTER_SCHEDULED,
        )
        if is_refusal(component):
            return component
        events.append(
            FinancingCashEvent(
                position=position,
                amount=charged.value.amount,
                day_multiplier=charged.value.day_multiplier,
                trading_date=trading.value,
                journal_event=journaled.value,
                component=component.value,
            )
        )
        sequence += 1
    return Ok(
        FinancingRollover(
            instant=frontier,
            events=tuple(events),
            skipped=tuple(skipped),
        )
    )


def decompose_cost_drag(
    *,
    fill_pnl: object,
    slippage: object,
    commission: object,
    financing: object,
) -> Result[CostDrag]:
    """Four separately attributable lines. None is folded into fill P&L (FEE-5)."""
    pnl = _require_money(fill_pnl, COST_DRAG_FILL_PNL)
    if is_refusal(pnl):
        return pnl
    slip = _require_money(slippage, COST_DRAG_SLIPPAGE)
    if is_refusal(slip):
        return slip
    fee = _require_money(commission, COST_DRAG_COMMISSION)
    if is_refusal(fee):
        return fee
    carry = _require_money(financing, COST_DRAG_FINANCING)
    if is_refusal(carry):
        return carry
    currency = pnl.value.currency
    for field, amount in (
        (COST_DRAG_SLIPPAGE, slip.value),
        (COST_DRAG_COMMISSION, fee.value),
        (COST_DRAG_FINANCING, carry.value),
    ):
        if amount.currency != currency:
            return invalid(
                field,
                "cost-drag lines share one currency; no silent conversion (FEE-1)",
                given=amount.currency,
                currency=currency,
            )
    return Ok(
        CostDrag(
            fill_pnl=pnl.value,
            slippage=slip.value,
            commission=fee.value,
            financing=carry.value,
        )
    )


def financing_calibration_fingerprint(value: object) -> Result[Fingerprint]:
    """Coerce a config citation or artifact to the calibration fingerprint."""
    if isinstance(value, SwapCalibration):
        return Ok(value.fingerprint)
    if isinstance(value, Fingerprint):
        return Ok(value)
    token = clean_token(value)
    if token is None:
        return invalid(
            FINANCING_CALIBRATION_KEY,
            "a financing calibration citation is an fp1 fingerprint or the "
            "calibration artifact (DEC-0135, B-10)",
            given=repr(type(value).__name__),
        )
    parsed = Fingerprint.try_create(token)
    if is_refusal(parsed):
        return invalid(
            FINANCING_CALIBRATION_KEY,
            "a financing calibration citation is an fp1 fingerprint or the "
            "calibration artifact (DEC-0135, B-10)",
            given=token,
        )
    return parsed


@dataclass(frozen=True, slots=True)
class FinancingScheduler:
    """Scheduled position-level cash event, never an order fill (B-6, FEE-4).

    Bound from a financing-schedule reference plus an optional swap calibration.
    Applying a swap without that artifact is a typed refusal, never a silent zero.
    """

    schedule_ref: str
    adapter_id: str = FINANCING_ADAPTER_SCHEDULED
    composition_version: int = COMPOSITION_VERSION
    taint: str = TAINT_OPTIMISTIC
    calibration: SwapCalibration | None = None

    def fidelity(self) -> Result[FidelityIdentity]:
        """Stamp adapter-id + composition-version + schedule/calibration ref + taint."""
        ref = self.schedule_ref
        if self.calibration is not None:
            ref = self.calibration.fingerprint.value
        return stamp_fidelity(
            f"financing.{self.adapter_id}",
            composition_version=self.composition_version,
            calibration_ref=ref,
        )

    def schedule(self, *, stream_id: str, direction: object) -> Result[Money]:
        """Per-unit daily swap from the bound table. Absence never silently zeros."""
        if self.calibration is None:
            return unavailable(
                "financing_schedule",
                "swap/financing calibration content is deferred to GAP-0048; absence "
                "never silently zeros (B-6, FEE-4, SC-07)",
                schedule_ref=self.schedule_ref,
                gap=FINANCING_CONTENT_DEFERRED_TO,
                financing_is_order_fill=FINANCING_IS_ORDER_FILL,
            )
        return lookup_swap_rate(self.calibration, stream_id, direction)

    def apply_at_rollover(
        self,
        positions: object,
        *,
        frontier: object,
        calendar: object,
        writer: object,
        world: object = World.REPLAY,
        start_sequence: object = 0,
        stream_id: object = None,
    ) -> Result[FinancingRollover]:
        """Sub-phase 2 cash event at the calendar's accounting-rollover instant."""
        return apply_financing_rollover(
            self,
            positions,
            frontier=frontier,
            calendar=calendar,
            writer=writer,
            world=world,
            start_sequence=start_sequence,
            stream_id=stream_id,
        )


def _calibration_of(port: object) -> Result[SwapCalibration]:
    calibration = getattr(port, "calibration", None)
    if isinstance(calibration, SwapCalibration):
        return Ok(calibration)
    return unavailable(
        "financing_schedule",
        "swap/financing calibration content is deferred to GAP-0048; absence "
        "never silently zeros (B-6, FEE-4, SC-07)",
        gap=FINANCING_CONTENT_DEFERRED_TO,
        financing_is_order_fill=FINANCING_IS_ORDER_FILL,
        given=repr(type(port).__name__),
    )


def _cost_drag_components(drag: CostDrag) -> Result[tuple[CostComponent, ...]]:
    lines: list[CostComponent] = []
    for name, amount in (
        (COST_DRAG_FILL_PNL, drag.fill_pnl),
        (COST_DRAG_SLIPPAGE, drag.slippage),
        (COST_DRAG_COMMISSION, drag.commission),
        (COST_DRAG_FINANCING, drag.financing),
    ):
        component = CostComponent.try_create(name, amount, FINANCING_ADAPTER_SCHEDULED)
        if is_refusal(component):
            return component
        lines.append(component.value)
    return Ok(tuple(lines))


def _scale_money(unit: Money, factor: Fraction) -> Result[Money]:
    amount = unit.as_fraction() * factor
    scaled = amount * (10**unit.scale)
    if scaled.denominator == 1:
        return Money.try_create(scaled.numerator, unit.currency, unit.scale)
    for candidate in range(unit.scale + 1, MONEY_STORAGE_SCALE + 1):
        finer = amount * (10**candidate)
        if finer.denominator == 1:
            return Money.try_create(finer.numerator, unit.currency, candidate)
    return invalid(
        "financing",
        "financing is not exactly representable as scaled-integer Money; "
        "no silent rounding (CT-01, FR-001)",
        amount=str(amount),
        scale=unit.scale,
    )


def _as_rates(value: object) -> Result[tuple[SwapRate, ...]]:
    if isinstance(value, SwapRate):
        items = (value,)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        items = tuple(cast("Sequence[object]", value))
    else:
        return invalid(
            "rates",
            "a swap table is a sequence of SwapRate cells, never a binary float",
            given=repr(type(value).__name__),
        )
    parsed: list[SwapRate] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if not isinstance(item, SwapRate):
            return invalid(
                "rates",
                "each swap-table cell is a SwapRate (instrument x direction)",
                given=repr(type(item).__name__),
            )
        key = (item.stream_id, item.direction.value)
        if key in seen:
            return invalid(
                "rates",
                "a swap table has one cell per instrument stream and direction",
                stream_id=item.stream_id,
                direction=item.direction.value,
            )
        seen.add(key)
        parsed.append(item)
    return Ok(tuple(parsed))


def _as_positions(value: object) -> Result[tuple[OpenPosition, ...]]:
    if value is None:
        return Ok(())
    if isinstance(value, OpenPosition):
        return Ok((value,))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        parsed: list[OpenPosition] = []
        for item in cast("Sequence[object]", value):
            if not isinstance(item, OpenPosition):
                return invalid(
                    "positions",
                    "financing applies to OpenPosition values, never an order fill",
                    given=repr(type(item).__name__),
                )
            parsed.append(item)
        return Ok(tuple(parsed))
    return invalid(
        "positions",
        "financing applies to a sequence of OpenPosition values",
        given=repr(type(value).__name__),
    )


def _require_direction(value: object) -> Result[Direction]:
    if isinstance(value, Direction):
        return Ok(value)
    token = clean_token(value)
    if token is None:
        return invalid(
            "direction",
            "swap direction is long or short (FEE-4)",
            given=repr(value),
        )
    try:
        return Ok(Direction(token))
    except ValueError:
        return invalid(
            "direction",
            "swap direction is long or short (FEE-4)",
            given=token,
            allowed=[Direction.LONG.value, Direction.SHORT.value],
        )


def _require_money(value: object, field: str) -> Result[Money]:
    if isinstance(value, Money):
        return Ok(value)
    return invalid(
        field,
        "cost drag is exact-integer Money, never a binary float (FEE-5, CT-01)",
        given=repr(type(value).__name__),
    )


def _optional_weekday(value: object) -> Result[str | None]:
    if value is None:
        return Ok(None)
    token = clean_token(value)
    if token not in _LEGAL_WEEKDAYS:
        return invalid(
            "triple_swap_weekday",
            "triple-swap weekday is monday..sunday from the artifact, never "
            "a hardcoded Wednesday (FEE-4, SC-07)",
            given=repr(value),
            allowed=list(WEEKDAYS),
        )
    return Ok(token)


def _optional_multiplier(value: object) -> Result[int | None]:
    if value is None:
        return Ok(None)
    if isinstance(value, bool) or not isinstance(value, int):
        return invalid(
            "triple_swap_multiplier",
            "triple-swap multiplier is a positive integer from the artifact, "
            "never invented (FEE-4, SC-07)",
            given=repr(type(value).__name__),
        )
    if value < 1:
        return invalid(
            "triple_swap_multiplier",
            "triple-swap multiplier is a positive integer from the artifact",
            given=value,
        )
    return Ok(value)


def _optional_calendar_identity(value: object) -> Result[dict[str, object] | None]:
    if value is None:
        return Ok(None)
    identity = getattr(value, "fp1_identity", None)
    if callable(identity):
        content = identity()
        if isinstance(content, dict):
            return Ok(dict(cast("Mapping[str, object]", content)))
        return invalid(
            "calendar_identity",
            "calendar identity on a swap calibration is the rule-set fingerprint "
            "content, never a hardcoded rollover wall time",
            given=repr(type(content).__name__),
        )
    if isinstance(value, dict):
        return Ok(dict(cast("Mapping[str, object]", value)))
    return invalid(
        "calendar_identity",
        "calendar identity on a swap calibration is the rule-set identity, never "
        "a hardcoded rollover wall time (AD-8)",
        given=repr(type(value).__name__),
    )


# --- a unit run's carry from its instrument record (QB-04, LD-13) -------------

_CENT: Final[Decimal] = Decimal("0.01")
_EPOCH: Final[datetime] = datetime(1970, 1, 1, tzinfo=UTC)
_NS_PER_US: Final[int] = 1_000
_INTERVAL: Final[re.Pattern[str]] = re.compile(r"PT([1-9][0-9]*)([HM])")
_UNIT_NS: Final[Mapping[str, int]] = MappingProxyType({"H": 3_600_000_000_000, "M": 60_000_000_000})


class CashKind(StrEnum):
    SWAP = "swap"
    FINANCING = "financing"
    FUNDING = "funding"
    DIVIDEND = "dividend"
    COMMISSION = "commission"


@dataclass(frozen=True, slots=True)
class CashEvent:
    """Money a held position or a fill moves with no price change: signed, in cents."""

    instant: Instant
    """When the venue books it: the rollover, the funding time, the ex-date, the fill."""
    market_id: str
    position_id: str
    kind: CashKind
    money: Decimal
    detail: str


class VenueClock(Protocol):
    """The instrument record's venue day: its zone and the span of the day holding an instant."""

    @property
    def zone(self) -> tzinfo: ...

    def span(self, ns: int) -> tuple[int, int]: ...


@dataclass(frozen=True, slots=True)
class _Nightly:
    kind: CashKind
    long: Decimal
    short: Decimal
    triple_day: int | None
    days_per_year: Decimal | None
    """None for a swap in money per lot; the day count of a yearly share of notional otherwise."""


@dataclass(frozen=True, slots=True)
class _Dividend:
    at_ns: int
    side: Side | None
    amount_per_lot: Decimal


@dataclass(frozen=True, slots=True)
class CarrySchedule:
    """What holding one market costs or pays with no fill, read from its instrument record."""

    market_id: str
    day: VenueClock
    value_per_point: Decimal
    bar_ns: int
    nightly: tuple[_Nightly, ...]
    dividends: tuple[_Dividend, ...]
    funding_ns: int | None
    rates: Mapping[int, Decimal]

    def held(
        self, position: OwnPosition, since: Instant, until: Instant, bar: QuoteBar
    ) -> Result[tuple[CashEvent, ...]]:
        """The cash ``position`` moved from the bar opening at ``since`` to the one at ``until``.

        Bars are stamped at their close, so the position was held from the open of the bar at
        ``since`` to the open of ``bar``, the first price this slice trades at.
        """
        after, upto = since.value_ns - self.bar_ns, until.value_ns - self.bar_ns
        mark = (bar.bid.open + bar.ask.open) / 2
        notional = mark * position.quantity * self.value_per_point
        long = position.side is Side.LONG
        events: list[CashEvent] = []
        rollover = self.day.span(after)[1]
        if rollover <= upto:
            weekday = (_EPOCH + timedelta(microseconds=rollover // _NS_PER_US)).astimezone(
                self.day.zone
            )
            for night in self.nightly:
                nights = 3 if night.triple_day == weekday.weekday() else 1
                rate = night.long if long else night.short
                money = (
                    rate * position.quantity * nights
                    if night.days_per_year is None
                    else rate * nights / night.days_per_year * notional
                )
                detail = f"{nights} night{'s' if nights > 1 else ''} at {rate}"
                events.append(self._event(rollover, position, night.kind, money, detail))
        for dividend in self.dividends:
            if after < dividend.at_ns <= upto and dividend.side in (None, position.side):
                sign = 1 if dividend.side is not None or long else -1
                money = sign * dividend.amount_per_lot * position.quantity
                detail = f"{dividend.amount_per_lot} per lot"
                events.append(
                    self._event(dividend.at_ns, position, CashKind.DIVIDEND, money, detail)
                )
        for at in self._funding_times(after, upto):
            rate = self.rates.get(at)
            if rate is None:
                return policy(
                    "funding",
                    "the run holds no recorded funding rate for a funding time a position was "
                    "held through, so its funding is unknown",
                    market_id=self.market_id,
                    at_ns=at,
                )
            money = (-rate if long else rate) * notional
            detail = f"rate {rate} on {notional}"
            events.append(self._event(at, position, CashKind.FUNDING, money, detail))
        return Ok(tuple(sorted(events, key=lambda event: event.instant.value_ns)))

    def _funding_times(self, after: int, upto: int) -> list[int]:
        if self.funding_ns is None:
            return []
        times: list[int] = []
        start = self.day.span(after)[0]
        while start <= upto:
            end = self.day.span(start)[1]
            times += [t for t in range(start, end, self.funding_ns) if after < t <= upto]
            start = end
        return times

    def _event(
        self, at: int, position: OwnPosition, kind: CashKind, money: Decimal, detail: str
    ) -> CashEvent:
        return CashEvent(
            Instant(at),
            self.market_id,
            position.position_id,
            kind,
            money.quantize(_CENT, rounding=ROUND_HALF_EVEN),
            detail,
        )


def _signed(value: object) -> Decimal | None:
    if not isinstance(value, str):
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _weekday(value: object) -> int | None:
    return WEEKDAYS.index(value) if isinstance(value, str) and value in WEEKDAYS else None


def _nightly(kind: CashKind, terms: object, *, yearly: bool) -> Result[_Nightly | None]:
    if terms is None:
        return Ok(None)
    given = cast("Mapping[str, object]", terms) if isinstance(terms, Mapping) else {}
    long, short = _signed(given.get("long")), _signed(given.get("short"))
    per_year = _signed(given.get("days_per_year")) if yearly else None
    triple = given.get("triple_day")
    if (
        long is None
        or short is None
        or (yearly and (per_year is None or per_year <= 0))
        or (triple is not None and _weekday(triple) is None)
    ):
        wants = "long, short and days_per_year" if yearly else "long and short"
        return invalid(
            kind.value,
            f"{kind.value} terms are {wants} as decimal text and an optional triple_day weekday",
            given=repr(terms),
        )
    return Ok(_Nightly(kind, long, short, _weekday(triple), per_year))


def _ex_instant(at: object, day: VenueClock) -> int | None:
    if not isinstance(at, str):
        return None
    try:
        if len(at) == len("2026-12-18"):
            midnight = datetime.combine(date.fromisoformat(at), datetime.min.time(), day.zone)
            ns = (midnight - _EPOCH) // timedelta(microseconds=1) * _NS_PER_US
            return day.span(ns)[0]
        stamped = datetime.fromisoformat(at)
    except ValueError:
        return None
    if stamped.tzinfo is None:
        return None
    return (stamped - _EPOCH) // timedelta(microseconds=1) * _NS_PER_US


def _dividends(events: object, day: VenueClock) -> Result[tuple[_Dividend, ...]]:
    found: list[_Dividend] = []
    rows = cast("Sequence[object]", events) if isinstance(events, list) else ()
    for row in rows:
        event = cast("Mapping[str, object]", row) if isinstance(row, Mapping) else {}
        if event.get("kind") != "dividend":
            continue
        at, amount, side = (
            _ex_instant(event.get("at"), day),
            _signed(event.get("amount_per_lot")),
            event.get("side"),
        )
        if at is None or amount is None or side not in (None, "long", "short"):
            return invalid(
                "events",
                "a dividend is {kind, at: an ex-date or a zoned instant, amount_per_lot, side}",
                given=repr(row),
            )
        found.append(_Dividend(at, None if side is None else Side(side), amount))
    return Ok(tuple(found))


def read_funding_rates(rows: Sequence[str]) -> Result[Mapping[int, Decimal]]:
    """``timestamp,rate`` lines (epoch milliseconds, decimal text) into rates by UTC ns."""
    rates: dict[int, Decimal] = {}
    for line in rows[1:]:
        stamp, _, text = line.strip().partition(",")
        rate = _signed(text)
        if not stamp.isdigit() or rate is None:
            return invalid("funding", "a funding row is timestamp,rate", given=line)
        rates[int(stamp) * 1_000_000] = rate
    return Ok(rates)


def carry_schedule(
    market_id: str,
    terms: Mapping[str, object],
    *,
    value_per_point: Decimal,
    day: VenueClock,
    bar_ns: int,
    rates: Mapping[int, Decimal] | None,
) -> Result[CarrySchedule]:
    """The carry an instrument record's terms schedule; a perp needs its recorded rates."""
    nightly: list[_Nightly] = []
    for kind, key, yearly in (
        (CashKind.SWAP, "swap", False),
        (CashKind.FINANCING, "financing", True),
    ):
        parsed = _nightly(kind, terms.get(key), yearly=yearly)
        if is_refusal(parsed):
            return parsed
        if parsed.value is not None:
            nightly.append(parsed.value)
    dividends = _dividends(terms.get("events"), day)
    if is_refusal(dividends):
        return dividends
    interval = terms.get("funding_interval")
    funding_ns: int | None = None
    if interval is not None:
        matched = _INTERVAL.fullmatch(str(interval))
        if matched is None:
            return invalid("funding_interval", "a funding interval is PT<n>H or PT<n>M")
        funding_ns = int(matched[1]) * _UNIT_NS[matched[2]]
        if rates is None:
            return invalid(
                "funding",
                "a market that pays funding needs its recorded rates in the run folder",
                market_id=market_id,
            )
    return Ok(
        CarrySchedule(
            market_id,
            day,
            value_per_point,
            bar_ns,
            tuple(nightly),
            dividends.value,
            funding_ns,
            rates or {},
        )
    )
