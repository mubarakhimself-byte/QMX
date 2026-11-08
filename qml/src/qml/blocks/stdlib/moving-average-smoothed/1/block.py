"""moving-average-smoothed@1: MetaQuotes' smoothed moving average (SMMA).

The first value, at update ``period``, is the simple mean of the first ``period`` values; each
later value is ``(previous * (period - 1) + value) / period``.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Smma:
    __slots__ = ("_count", "_level", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._count = 0
        self._level = 0.0

    @property
    def warm_up_bars(self) -> int:
        return self._period

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 1

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        x = float(price)
        n = self._period
        self._count += 1
        if self._count < n:
            self._level += x
            return None
        if self._count == n:
            self._level = (self._level + x) / n
        else:
            self._level = (self._level * (n - 1) + x) / n
        return quantise(self._level)

    def export_state(self) -> Mapping[str, object]:
        return {"count": self._count, "level": self._level.hex()}

    def import_state(self, state: Mapping[str, object]) -> None:
        count, level = state["count"], state["level"]
        if not isinstance(count, int) or not isinstance(level, str):
            raise ValueError("moving-average-smoothed@1 state needs count and level")
        self._count = count
        self._level = float.fromhex(level)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Smma:
        period = int(params["period"])
        if period < 1:
            raise ValueError("moving-average-smoothed@1 period must be at least 1")
        return _Smma(period)


BLOCK = _Block()
