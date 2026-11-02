"""hurst-exponent@1: the Hurst exponent of the last ``window`` prices, read from how the spread
of lagged differences grows with the lag.

Matches QuantConnect LEAN's HurstExponent: for each lag from 2 to ``max_lag`` it takes the
population standard deviation of the differences between prices that lag apart inside the window,
and returns the least-squares slope of its logarithm on the lag's logarithm. A zero standard
deviation counts as a logarithm of zero, as LEAN does. The first value comes at update
``window``. Running sums per lag are rebuilt from the window once every ``window`` updates, so
rounding never piles up.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in raw]


class _Hurst:
    __slots__ = ("_lags", "_since", "_squares", "_sums", "_window", "_x", "_x2")

    def __init__(self, window: int, max_lag: int) -> None:
        self._lags = list(range(2, max_lag + 1))
        self._window: deque[float] = deque(maxlen=window)
        self._sums = [0.0] * len(self._lags)
        self._squares = [0.0] * len(self._lags)
        self._since = 0
        logs = [math.log(lag) for lag in self._lags]
        self._x = sum(logs)
        self._x2 = sum(v * v for v in logs)

    @property
    def warm_up_bars(self) -> int:
        return self._window.maxlen or 0

    @property
    def state_bound(self) -> int:
        return self._window.maxlen or 0

    def retained(self) -> int:
        return len(self._window)

    def _rebuild(self) -> None:
        prices = list(self._window)
        for i, lag in enumerate(self._lags):
            diffs = [prices[j + lag] - prices[j] for j in range(len(prices) - lag)]
            self._sums[i] = sum(diffs, 0.0)
            self._squares[i] = sum((d * d for d in diffs), 0.0)
        self._since = 0

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        new = float(price)
        prices = self._window
        full = len(prices) == prices.maxlen
        for i, lag in enumerate(self._lags):
            if len(prices) >= lag:
                added = new - prices[len(prices) - lag]
                self._sums[i] += added
                self._squares[i] += added * added
            if full:
                dropped = prices[lag] - prices[0]
                self._sums[i] -= dropped
                self._squares[i] -= dropped * dropped
        prices.append(new)
        self._since += 1
        if self._since >= (prices.maxlen or 0):
            self._rebuild()
        if len(prices) < (prices.maxlen or 0):
            return None
        sum_y = sum_xy = 0.0
        for i, lag in enumerate(self._lags):
            count = len(prices) - lag
            mean = self._sums[i] / count
            variance = self._squares[i] / count - mean * mean
            log_tau = math.log(math.sqrt(variance)) if variance > 0.0 else 0.0
            sum_y += log_tau
            sum_xy += math.log(lag) * log_tau
        n = len(self._lags)
        return quantise((n * sum_xy - self._x * sum_y) / (n * self._x2 - self._x * self._x))

    def export_state(self) -> Mapping[str, object]:
        return {
            "window": [v.hex() for v in self._window],
            "sums": [v.hex() for v in self._sums],
            "squares": [v.hex() for v in self._squares],
            "since": self._since,
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        since = state["since"]
        if not isinstance(since, int):
            raise ValueError("hurst-exponent@1 state needs since")
        self._window = deque(_floats(state["window"], "window"), maxlen=self._window.maxlen)
        self._sums = _floats(state["sums"], "hurst-exponent@1 state's sums")
        self._squares = _floats(state["squares"], "hurst-exponent@1 state's squares")
        self._since = since


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Hurst:
        window, max_lag = int(params["window"]), int(params["max_lag"])
        if max_lag < 3 or window <= max_lag:
            raise ValueError("hurst-exponent@1 needs max_lag of at least 3 and below window")
        return _Hurst(window, max_lag)


BLOCK = _Block()
