"""Conversions between measures, each only through an instrument record (AD-103, L0 AD-9).

Every result is an exact QMF value. A conversion the record cannot support is a typed refusal
that names the record and the missing fact, never a guess.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from math import floor

from qmf.core.exact import ExactRational, PriceDelta, Quantity, UnitKind, ValueFactor
from qmf.core.identity import Instrument, VenueId
from qmf.core.refusal import Ok, Result

from qml._refuse import invalid, unavailable
from qml.numbers.records import InstrumentRecord, places
from qml.unit.model import Measure

__all__ = ["atr_multiple", "distance", "from_atr", "instrument", "lots", "value_factor"]


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


def lots(amount: Decimal, record: InstrumentRecord) -> Result[Quantity]:
    """A size in lots rounded down to the record's lot step, refused outside its lot limits."""
    step = Fraction(record.lot_step)
    steps = floor(Fraction(amount) / step)
    scale = places(record.lot_step)
    units = steps * int(step * 10**scale)
    size = Decimal(f"{units}E-{scale}")
    if steps * step < Fraction(record.min_lot):
        return invalid(
            "lots",
            f"{amount} lots rounds down to {size}, below {record.name}'s minimum lot "
            f"of {record.min_lot}",
            record=record.name,
        )
    if record.max_lot is not None and steps * step > Fraction(record.max_lot):
        return invalid(
            "lots",
            f"{amount} lots is above {record.name}'s largest order of {record.max_lot}",
            record=record.name,
        )
    return Ok(Quantity(units, "lot", scale))


def value_factor(record: InstrumentRecord) -> ValueFactor:
    """Money per price unit per lot in the record's currency, for ``PriceDelta.to_money``."""
    exact = Fraction(record.value_per_point)
    return ValueFactor(exact.numerator, exact.denominator, instrument(record), record.currency)
