"""rolling-standard-deviation@1: the population standard deviation of the last ``period``
values.

Matches TA-Lib's STDDEV with one deviation: running totals of the values and of their squares
give the mean of the squares less the square of the mean, and its square root is the value, 0
when the variance is not above 0. TA-Lib also gives 0 for any variance below 1e-8; this block
does not. The first value comes at update ``period``.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in cast("list[object]", raw)]


class _StdDev:
    __slots__ = ("_period", "_squares", "_total", "_window")

    def __init__(self, period: int) -> None:
        self._period = period
        self._window: deque[float] = deque(maxlen=period)
        self._total = 0.0
        self._squares = 0.0

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
        x = float(price)
        self._window.append(x)
        self._total += x
        self._squares += x * x
        if len(self._window) < self._period:
            return None
        mean = self._total / self._period
        variance = self._squares / self._period - mean * mean
        oldest = self._window[0]
        self._total -= oldest
        self._squares -= oldest * oldest
        return quantise(math.sqrt(variance) if variance > 0.0 else 0.0)

    def export_state(self) -> Mapping[str, object]:
        return {
            "window": [v.hex() for v in self._window],
            "totals": [self._total.hex(), self._squares.hex()],
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        values = _floats(state["window"], "rolling-standard-deviation@1 state's window")
        self._window = deque(values, maxlen=self._period)
        self._total, self._squares = _floats(state["totals"], "its totals")


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _StdDev:
        period = int(params["period"])
        if period < 1:
            raise ValueError("rolling-standard-deviation@1 period must be at least 1")
        return _StdDev(period)


BLOCK = _Block()
