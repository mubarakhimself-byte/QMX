"""bar-range-pressure@1: where a bar closed inside its range, from -1 at the low to 1 at the high:
((close - low) - (high - close)) / (high - low), the money flow multiplier of the Accumulation
Distribution Line. A bar whose high equals its low reads 0, as TA-Lib's AD counts it. It needs
only the bar's prices, so it reads on every bar a unit is given.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Pressure:
    __slots__ = ()

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        bar = evidence.get("series")
        if not isinstance(bar, Mapping):
            return None
        high, low, close = bar.get("high"), bar.get("low"), bar.get("close")
        if not (
            isinstance(high, Decimal) and isinstance(low, Decimal) and isinstance(close, Decimal)
        ):
            return None
        if high == low:
            return quantise(Decimal(0))
        return quantise(((close - low) - (high - close)) / (high - low))

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Pressure:
        return _Pressure()


BLOCK = _Block()
