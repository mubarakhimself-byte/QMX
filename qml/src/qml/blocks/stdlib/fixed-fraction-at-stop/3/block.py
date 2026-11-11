"""fixed-fraction-at-stop@3: risk ``fraction`` of equity at the stop with the cost of a fill in the
denominator, as money at risk.

The money at risk is ``equity * fraction * d / (d + c)``, ``d`` the distance from entry to stop and
``c`` the market's cost per fill in price (AD-15). So the loss at the stop plus that cost is the
fraction of equity, and the one converter spells the venue's quantity from this amount. ``c`` is
the host's ``market.cost_cell`` fact, so a cost read only ever shrinks a size. A cost the host did
not supply, one that is not a finite number, or one below zero reads as the record's stated cost
stressed, never as zero: a negative cell is drift or a bad fill price, not a fill that paid
nothing. The fraction is read from ``evidence`` on every call, so a number that
moves reaches the size; ``make`` only seeds it (AD-14 step 3).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from fractions import Fraction

from qml.blocks.api import Amount, Side, Skip
from qml.numbers.records import InstrumentRecord, stressed_cost


def _cost(evidence: Mapping[str, object], record: InstrumentRecord) -> Decimal:
    """The cost per fill this size charges: the cell's value, or the stressed stated cost."""
    value = getattr(evidence.get("cost_cell"), "value", None)
    if isinstance(value, Fraction):
        value = Decimal(value.numerator) / Decimal(value.denominator)
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
        return stressed_cost(record)
    return value


class _FixedFraction:
    __slots__ = ("_fraction",)

    def __init__(self, fraction: Decimal) -> None:
        self._fraction = fraction

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Amount | Skip | None:
        equity = evidence.get("equity")
        entry, stop = evidence.get("entry_price"), evidence.get("stop_price")
        record = evidence.get("record")
        if not isinstance(equity, Decimal) or not isinstance(record, InstrumentRecord):
            return None
        if not isinstance(entry, Decimal) or not isinstance(stop, Decimal):
            return None
        moved = evidence.get("fraction")
        fraction = moved if isinstance(moved, Decimal) else self._fraction
        if equity <= 0:
            return Skip(reason="the account holds nothing, so there is nothing to risk")
        if fraction <= 0:
            return Skip(reason="the fraction is zero, so nothing is risked")
        distance = abs(entry - stop)
        if not distance:
            return Skip(reason="the stop is at the entry, so a size has no risk to divide")
        share = distance / (distance + _cost(evidence, record))
        return Amount(kind="money_at_risk", value=equity * fraction * share, basis="gross_at_stop")

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _FixedFraction:
        return _FixedFraction(params["fraction"])


BLOCK = _Block()
