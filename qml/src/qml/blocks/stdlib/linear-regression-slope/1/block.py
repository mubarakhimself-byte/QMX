"""linear-regression-slope@1: the slope per update of the least-squares line through the
last ``period`` values.

Matches TA-Lib's LINEARREG_SLOPE. The first value comes at update ``period``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in cast("list[object]", raw)]


class _LinearSlope:
    __slots__ = ("_period", "_window")

    def __init__(self, period: int) -> None:
        self._period = period
        self._window: deque[float] = deque(maxlen=period)

    @property
    def warm_up_bars(self) -> int:
        return self._period

    @property
    def state_bound(self) -> int:
        return self._period

    def retained(self) -> int:
        return len(self._window)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        self._window.append(float(price))
        if len(self._window) < self._period:
            return None
        n = self._period
        sum_x = n * (n - 1) * 0.5
        divisor = sum_x * sum_x - n * (n * (n - 1) * (2 * n - 1) / 6)
        sum_y = sum(self._window)
        sum_xy = sum(age * v for age, v in enumerate(reversed(self._window)))
        slope = (n * sum_xy - sum_x * sum_y) / divisor
        return quantise(slope)

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        values = _floats(state["window"], "linear-regression-slope@1 state's window")
        self._window = deque(values, maxlen=self._period)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _LinearSlope:
        period = int(params["period"])
        if period < 2:
            raise ValueError("linear-regression-slope@1 period must be at least 2")
        return _LinearSlope(period)


BLOCK = _Block()
