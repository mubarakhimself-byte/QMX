"""cusum-change-point@1: Page's two-sided tabular CUSUM on each bar's log return, standardised
by the ``window`` returns before it.

Each return becomes ``z``, its distance from the mean of the previous ``window`` returns in their
sample standard deviations. ``moment`` 1 watches the mean of returns (``x = z``), ``moment`` 2
their variance (``x = z * z - 1``). As in the NIST handbook's tabular form, ``high`` and ``low``
add ``x - drift`` and ``-x - drift`` and never go below zero. The output holds when either
exceeds ``threshold``, and carries the larger side signed: ``high`` positive, ``low``
negative. Both start again from zero after it holds. Missing while the window before the return
has no spread. The first value comes at update ``window + 2``.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, Signal, quantise


class _Cusum:
    __slots__ = ("_drift", "_high", "_last", "_low", "_moment", "_returns", "_threshold")

    def __init__(self, window: int, drift: float, threshold: float, moment: int) -> None:
        self._drift, self._threshold, self._moment = drift, threshold, moment
        self._returns: deque[float] = deque(maxlen=window)
        self._last: float | None = None
        self._high = self._low = 0.0

    @property
    def warm_up_bars(self) -> int:
        return (self._returns.maxlen or 0) + 2

    @property
    def state_bound(self) -> int:
        return (self._returns.maxlen or 0) + 1

    def retained(self) -> int:
        return len(self._returns) + (self._last is not None)

    def update(self, evidence: Mapping[str, object]) -> Signal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal) or price <= 0:
            return None
        new = math.log(price)
        before, self._last = self._last, new
        if before is None:
            return None
        move, history = new - before, self._returns
        if len(history) < (history.maxlen or 0):
            history.append(move)
            return None
        mean = sum(history) / len(history)
        spread = math.sqrt(sum((r - mean) ** 2 for r in history) / (len(history) - 1))
        history.append(move)
        if spread == 0.0:
            return None
        z = (move - mean) / spread
        x = z if self._moment == 1 else z * z - 1.0
        self._high = max(0.0, self._high + x - self._drift)
        self._low = max(0.0, self._low - x - self._drift)
        value = self._high if self._high >= self._low else -self._low
        holds = self._high > self._threshold or self._low > self._threshold
        if holds:
            self._high = self._low = 0.0
        return Signal(state=holds, value=quantise(value))

    def export_state(self) -> Mapping[str, object]:
        return {
            "returns": [v.hex() for v in self._returns],
            "last": None if self._last is None else self._last.hex(),
            "high": self._high.hex(),
            "low": self._low.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        raw, last, high, low = state["returns"], state.get("last"), state["high"], state["low"]
        if not isinstance(raw, list) or not isinstance(high, str) or not isinstance(low, str):
            raise ValueError("cusum-change-point@1 state needs returns, high and low")
        values = [float.fromhex(str(v)) for v in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._returns = deque(values, maxlen=self._returns.maxlen)
        self._last = float.fromhex(last) if isinstance(last, str) else None
        self._high, self._low = float.fromhex(high), float.fromhex(low)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Cusum:
        window, moment = int(params["window"]), int(params["moment"])
        drift, threshold = float(params["drift"]), float(params["threshold"])
        if window < 2 or moment not in {1, 2} or drift < 0 or threshold <= 0:
            raise ValueError("cusum-change-point@1 needs window 2+, moment 1 or 2, threshold > 0")
        return _Cusum(window, drift, threshold, moment)


BLOCK = _Block()
