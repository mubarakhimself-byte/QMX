"""Whether one minimum lot at this stop fits the share (FUNNEL I17, SPINE section 4).

The verdict is pure and it asks the one converter. A share in the account's currency goes in as
money at risk beside the entry, the stop, the market's record and the rate; the converter answers
either a quantity, or the named skip that stands where a quantity cannot. ``fits`` is that answer
with a quantity, ``below_min_lot`` is the one skip this module explains: the money the smallest
order risks at this stop, less the share, which is what a person has to add before the market can
be traded at all. Every other skip keeps the converter's own word, and adds no shortfall.

The verdict is pure: a caller computes it, shows it on the unit's card and re-runs it at anchors;
the shed, concentrate and borrow rules that answer it are content and live in blocks, not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Final

from qmf.risk.facts import Fact

from qml.blocks.api import Amount
from qml.numbers.convert import RoundRule, to_quantity
from qml.numbers.records import InstrumentRecord

__all__ = ["BELOW_MIN_LOT", "FITS", "Feasibility", "feasibility"]

FITS: Final = "fits"
"""The share buys at least one minimum lot at this stop."""
BELOW_MIN_LOT: Final = "below_min_lot"
"""The smallest order risks more than the share: the verdict names the money it lacks."""


@dataclass(frozen=True, slots=True)
class Feasibility:
    """One verdict: its word, the money between the share and the smallest order, and the size.

    ``word`` is ``fits``, ``below_min_lot``, or the converter's own skip word. ``shortfall`` is in
    the account's currency and is above zero only for ``below_min_lot``; ``quantity`` is set only
    when the share fits, and ``residue_r`` is the risk the rounding down left, as a fraction of R.
    """

    word: str
    shortfall: Decimal
    quantity: Decimal | None
    residue_r: Decimal

    @property
    def fits(self) -> bool:
        return self.word == FITS

    def document(self) -> dict[str, object]:
        """The verdict as plain JSON values, for a card or a check result."""
        return {
            "verdict": self.word,
            "shortfall": str(self.shortfall),
            "quantity": None if self.quantity is None else str(self.quantity),
            "residue_r": str(self.residue_r),
        }


def feasibility(
    share: Decimal,
    entry: Decimal,
    stop: Decimal | None,
    record: InstrumentRecord,
    rate: Fact | None,
    rule: RoundRule,
) -> Feasibility:
    """The verdict on ``share`` at this ``entry`` and ``stop``, through :func:`to_quantity`.

    ``share`` is money at risk in the account's currency, exactly as a sizer answers it. A share
    that is zero or negative is the converter's own answer, never a second rule here.
    """
    converted = to_quantity(
        Amount(kind="money_at_risk", value=share, basis="gross_at_stop"),
        entry,
        stop,
        record,
        rate,
        rule,
    )
    if converted.skipped == BELOW_MIN_LOT:
        return Feasibility(
            BELOW_MIN_LOT,
            _shortfall(share, entry, stop, record, rate),
            None,
            Decimal(0),
        )
    if converted.skipped is not None:
        return Feasibility(converted.skipped, Decimal(0), None, Decimal(0))
    return Feasibility(FITS, Decimal(0), converted.quantity, converted.residue_r)


def _shortfall(
    share: Decimal,
    entry: Decimal,
    stop: Decimal | None,
    record: InstrumentRecord,
    rate: Fact | None,
) -> Decimal:
    """The money the record's minimum lot risks at this stop, less ``share``, exact.

    Only reached after :func:`to_quantity` answered ``below_min_lot``, which it answers with a
    stop and a usable rate in hand. An answer without them is a broken invariant, said aloud,
    never a shortfall of zero.
    """
    if stop is None or rate is None or rate.value is None:
        raise ValueError("the converter answered below_min_lot without a stop and a rate")
    distance = abs(entry - stop)
    needed = (
        Fraction(record.min_lot)
        * Fraction(distance)
        * Fraction(record.value_per_point)
        * _exact(rate.value)
    )
    left = needed - Fraction(share)
    if left <= 0:
        return Decimal(0)
    return Decimal(left.numerator) / Decimal(left.denominator)


def _exact(value: Decimal | Fraction) -> Fraction:
    """``value`` as an exact rational, never through a binary float."""
    return value if isinstance(value, Fraction) else Fraction(*value.as_integer_ratio())
