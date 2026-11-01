"""fixed-fraction-at-stop@1 (placeholder, owner the risk session): risk ``fraction`` of equity.

Lots are ``equity * fraction / (|entry - stop| * value_per_point)``, rounded down to the
market's lot step by ``qml.numbers.lots``; below the minimum lot the entry is skipped with
the reason. The division rounds toward floor, so it never rounds up across a lot step.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_FLOOR, Context, Decimal

from qmf.core.refusal import is_refusal
from qml.blocks.api import Side, Size
from qml.numbers import InstrumentRecord, lots

_DIVIDE = Context(prec=40, rounding=ROUND_FLOOR)


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

    def update(self, evidence: Mapping[str, object]) -> Size | None:
        equity = evidence.get("equity")
        entry, stop = evidence.get("entry_price"), evidence.get("stop_price")
        record = evidence.get("record")
        if not (
            isinstance(equity, Decimal)
            and isinstance(entry, Decimal)
            and isinstance(stop, Decimal)
            and isinstance(record, InstrumentRecord)
        ):
            return None
        if entry == stop:
            return Size(
                lots=None, skip_reason="the stop is at the entry, so the risk per lot is zero"
            )
        loss_per_lot = abs(entry - stop) * record.value_per_point
        wanted = _DIVIDE.divide(equity * self._fraction, loss_per_lot)
        sized = lots(wanted, record)
        if is_refusal(sized):
            reason = sized.context.get("reason")
            return Size(lots=None, skip_reason=str(reason))
        quantity = sized.value
        return Size(lots=Decimal(quantity.value).scaleb(-quantity.scale))

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
