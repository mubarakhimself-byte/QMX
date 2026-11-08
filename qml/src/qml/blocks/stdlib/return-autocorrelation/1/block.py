"""return-autocorrelation@1: the autocorrelation of log returns at ``lag`` bars over the last
``window`` prices.

The sample autocorrelation as statsmodels' acf computes it: the products of each return's and
its ``lag``-earlier return's distances from the window's mean return, summed and divided by the
summed squared distances. Positive when moves follow moves, negative when they reverse. Missing
while the returns have no spread. The first value comes at update ``window``.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Autocorrelation:
    __slots__ = ("_lag", "_window")

    def __init__(self, window: int, lag: int) -> None:
        self._lag = lag
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
        if not isinstance(price, Decimal) or price <= 0:
            return None
        logs = self._window
        logs.append(math.log(price))
        if len(logs) < (logs.maxlen or 0):
            return None
        returns = [logs[i] - logs[i - 1] for i in range(1, len(logs))]
        mean = sum(returns) / len(returns)
        gaps = [r - mean for r in returns]
        total = sum(g * g for g in gaps)
        if total == 0.0:
            return None
        k = self._lag
        return quantise(sum(gaps[t] * gaps[t - k] for t in range(k, len(gaps))) / total)

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        raw = state["window"]
        if not isinstance(raw, list):
            raise ValueError("return-autocorrelation@1 state's window is a list of hex floats")
        values = [float.fromhex(str(v)) for v in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._window = deque(values, maxlen=self._window.maxlen)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Autocorrelation:
        window, lag = int(params["window"]), int(params["lag"])
        if lag < 1 or window < lag + 3:
            raise ValueError("return-autocorrelation@1 needs lag 1 or more and window lag + 3")
        return _Autocorrelation(window, lag)


BLOCK = _Block()
