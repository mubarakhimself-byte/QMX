"""Conversions between measures, each only through an instrument record (AD-103, L0 AD-9).

Every result is an exact QMF value. A conversion the record cannot support is a typed refusal
that names the record and the missing fact, never a guess.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from math import floor
from typing import Final

from qmf.core.chrono import Instant
from qmf.core.exact import ExactRational, PriceDelta, Quantity, UnitKind, ValueFactor
from qmf.core.identity import Instrument, VenueId
from qmf.core.refusal import Ok, Result
from qmf.risk.facts import Fact

from qml._refuse import invalid, unavailable
from qml.blocks.api import Amount
from qml.numbers.records import InstrumentRecord, places
from qml.unit.model import Measure

__all__ = [
    "RATE_STALE_S",
    "Converted",
    "RoundRule",
    "atr_multiple",
    "distance",
    "from_atr",
    "instrument",
    "lots",
    "to_quantity",
    "value_factor",
]

RATE_STALE_S: Final[Decimal] = Decimal("60")
"""Starting default of the ``rate_stale_s`` setting (OPEN row 25): a market rate read longer ago
than this is stale, and the entry it would size skips. Labelled placeholder, owner numbers talk."""

_NANOS_PER_SECOND: Final[int] = 1_000_000_000


def instrument(record: InstrumentRecord) -> Instrument:
    return Instrument(VenueId(record.venue), record.symbol)


def distance(amount: Decimal, measure: Measure, record: InstrumentRecord) -> Result[PriceDelta]:
    """A price distance from an amount in ``price_distance``, ``ticks`` or ``pips``.

    The result sits on the record's tick grid at its digits. Pips need the record's pip;
    a record that defines none refuses, so 20 pips never means 20 of something else.
    """
    match measure:
        case Measure.PRICE_DISTANCE:
            exact = Fraction(amount)
        case Measure.TICKS:
            if amount != amount.to_integral_value():
                return invalid("amount", f"{amount} ticks is not a whole number of ticks")
            exact = Fraction(amount) * Fraction(record.tick_size)
        case Measure.PIPS:
            if record.pip is None:
                return unavailable(
                    "pip",
                    f"the record {record.name} defines no pip, so a distance in pips "
                    "has no meaning on this market",
                    record=record.name,
                )
            exact = Fraction(amount) * Fraction(record.pip.size)
        case _:
            return invalid("measure", f"{measure.value} is not a price distance measure")
    if exact < 0:
        return invalid("amount", "a distance is zero or more")
    if (exact / Fraction(record.tick_size)).denominator != 1:
        return invalid(
            "amount",
            f"{amount} {measure.value} is not a whole number of {record.name}'s "
            f"ticks of {record.tick_size}",
            record=record.name,
        )
    scaled = exact * 10**record.digits
    return Ok(PriceDelta(scaled.numerator, instrument(record), record.digits))


def atr_multiple(delta: PriceDelta, atr: PriceDelta) -> Result[ExactRational]:
    """A distance as a multiple of the ATR on the same instrument at the same instant."""
    if atr.instrument != delta.instrument:
        return invalid("atr", "the ATR belongs to a different instrument")
    if atr.value <= 0:
        return invalid("atr", "an ATR is above zero")
    ratio = delta.as_fraction() / atr.as_fraction()
    return ExactRational.try_create(
        ratio.numerator, ratio.denominator, UnitKind.DIMENSIONLESS_RATIO
    )


def from_atr(multiple: Decimal, atr: PriceDelta) -> Result[PriceDelta]:
    """The price distance of ``multiple`` ATRs, exact, at the scale the product needs."""
    if multiple < 0:
        return invalid("multiple", "an ATR multiple is zero or more")
    if atr.value <= 0:
        return invalid("atr", "an ATR is above zero")
    scale = atr.scale + places(multiple)
    scaled = Fraction(multiple) * atr.as_fraction() * 10**scale
    return Ok(PriceDelta(scaled.numerator, atr.instrument, scale))


@dataclass(frozen=True, slots=True)
class RoundRule:
    """The two rules the converter applies beside the record: the clock and the rate's age."""

    now: Instant
    rate_stale_s: Decimal = RATE_STALE_S


@dataclass(frozen=True, slots=True)
class Converted:
    """The venue's quantity in lots, the fraction of R rounding down left, or a skip name."""

    quantity: Decimal | None
    residue_r: Decimal
    skipped: str | None = None


def _skipped(name: str) -> Converted:
    return Converted(quantity=None, residue_r=Decimal(0), skipped=name)


def _exact(value: Decimal | Fraction) -> Fraction:
    """``value`` as an exact rational, never through a binary float."""
    return value if isinstance(value, Fraction) else Fraction(*value.as_integer_ratio())


def _spell(amount: Fraction, record: InstrumentRecord) -> tuple[Decimal, Fraction]:
    """The largest whole number of lot steps at or below ``amount``, and its exact value."""
    step = Fraction(record.lot_step)
    steps = floor(amount / step)
    scale = places(record.lot_step)
    units = steps * int(step * 10**scale)
    return Decimal(f"{units}E-{scale}"), steps * step


def lots(amount: Decimal, record: InstrumentRecord) -> Result[Quantity]:
    """A size in lots rounded down to the record's lot step, refused outside its lot limits."""
    size, spelled = _spell(Fraction(amount), record)
    scale = places(record.lot_step)
    if spelled < Fraction(record.min_lot):
        return invalid(
            "lots",
            f"{amount} lots rounds down to {size}, below {record.name}'s minimum lot "
            f"of {record.min_lot}",
            record=record.name,
        )
    if record.max_lot is not None and spelled > Fraction(record.max_lot):
        return invalid(
            "lots",
            f"{amount} lots is above {record.name}'s largest order of {record.max_lot}",
            record=record.name,
        )
    return Ok(Quantity(int(spelled * 10**scale), "lot", scale))


def _rate_value(rate: Fact | None, rule: RoundRule) -> Converted | Fraction:
    """The exact rate into the account's currency, or the named skip that stands in its place."""
    if rate is None or rate.value is None or rate.state == "absent":
        return _skipped("rate_absent")
    if rate.state == "stale" or rate.is_stale(rule.now, rule.rate_stale_s):
        return _skipped("rate_stale")
    return _exact(rate.value)


def to_quantity(
    amount: Amount,
    entry: Decimal,
    stop_or_basis: Decimal | None,
    record: InstrumentRecord,
    rate: Fact | None,
    rule: RoundRule,
) -> Converted:
    """One sizer's amount spelled as the venue's quantity in the account's currency.

    ``rate`` is account currency per one unit of the record's quote currency, read as the
    ``market.rate:<quote>`` fact. The quantity rounds down to the record's lot step, and the
    risk that rounding leaves behind comes back in ``residue_r`` as a fraction of R. A missing,
    stale or unsupported input is a named skip, never a guess and never a raise.
    """
    if amount.kind == "quantity":
        wanted = _exact(amount.value)
    elif amount.kind in ("money_at_risk", "notional"):
        checked = _rate_value(rate, rule)
        if isinstance(checked, Converted):
            return checked
        if amount.kind == "notional":
            wanted = _exact(amount.value) / (_exact(entry) * _exact(record.contract_size) * checked)
        elif amount.basis == "tail_budget":
            return _skipped("tail_budget")
        elif stop_or_basis is None:
            return _skipped("stop_absent")
        else:
            distance = abs(entry - stop_or_basis)
            if distance == 0:
                return _skipped("stop_at_entry")
            wanted = _exact(amount.value) / (
                _exact(distance) * _exact(record.value_per_point) * checked
            )
    else:
        return _skipped("kind_unknown")
    size, spelled = _spell(wanted, record)
    if spelled < Fraction(record.min_lot):
        return _skipped("below_min_lot")
    if record.max_lot is not None and spelled > Fraction(record.max_lot):
        return _skipped("above_max_lot")
    residue = (wanted - spelled) / wanted if wanted else Fraction(0)
    return Converted(
        quantity=size,
        residue_r=Decimal(residue.numerator) / Decimal(residue.denominator),
        skipped=None,
    )


def value_factor(record: InstrumentRecord) -> ValueFactor:
    """Money per price unit per lot in the record's currency, for ``PriceDelta.to_money``."""
    exact = Fraction(record.value_per_point)
    return ValueFactor(exact.numerator, exact.denominator, instrument(record), record.currency)
