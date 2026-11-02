"""half-life-of-mean-reversion@1: the bars a gap from the mean takes to halve, fitted over the
last ``window`` prices.

The least-squares slope ``beta`` of each bar's change on the price before it, with a constant,
gives ``-ln(2) / beta``, the half-life the MQL5 article on mean reversion computes. Missing
while ``beta`` is zero or above, since the series then shows no pull back. The first value
comes at update ``window``.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _HalfLife:
    __slots__ = ("_window",)

    def __init__(self, window: int) -> None:
        self._window: deque[float] = deque(maxlen=window)

    @property
    def warm_up_bars(self) -> int:
        return self._window.maxlen or 0

    @property
    def state_bound(self) -> int:
        return self._window.maxlen or 0

    def retained(self) -> int:
        return len(self._window)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        prices = self._window
        prices.append(float(price))
        if len(prices) < (prices.maxlen or 0):
            return None
        before = [prices[i] for i in range(len(prices) - 1)]
        moves = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
        x_mean, z_mean = sum(before) / len(before), sum(moves) / len(moves)
        sxx = sum((x - x_mean) ** 2 for x in before)
        sxz = sum((x - x_mean) * (z - z_mean) for x, z in zip(before, moves, strict=True))
        if sxx == 0.0 or sxz >= 0.0:
            return None
        return quantise(-math.log(2.0) / (sxz / sxx))

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        raw = state["window"]
        if not isinstance(raw, list):
            raise ValueError("half-life-of-mean-reversion@1 state's window is a list of floats")
        values = [float.fromhex(str(v)) for v in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._window = deque(values, maxlen=self._window.maxlen)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _HalfLife:
        window = int(params["window"])
        if window < 3:
            raise ValueError("half-life-of-mean-reversion@1 window must be at least 3")
        return _HalfLife(window)


BLOCK = _Block()
