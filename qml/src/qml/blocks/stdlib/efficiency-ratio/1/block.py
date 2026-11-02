"""efficiency-ratio@1: Kaufman's efficiency ratio over the last ``period`` price changes.

The net change over ``period`` bars, as an absolute value, divided by the sum of the absolute
bar-to-bar changes. 1 when every bar moved the same way, near 0 when the moves cancel. Missing
while the window holds no movement, since the ratio is then 0 over 0. The first value comes at
update ``period + 1``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _EfficiencyRatio:
    __slots__ = ("_window",)

    def __init__(self, period: int) -> None:
        self._window: deque[float] = deque(maxlen=period + 1)

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
        path = sum(abs(prices[i] - prices[i - 1]) for i in range(1, len(prices)))
        if path == 0.0:
            return None
        return quantise(abs(prices[-1] - prices[0]) / path)

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        raw = state["window"]
        if not isinstance(raw, list):
            raise ValueError("efficiency-ratio@1 state's window is a list of hex floats")
        values = [float.fromhex(str(v)) for v in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._window = deque(values, maxlen=self._window.maxlen)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _EfficiencyRatio:
        period = int(params["period"])
        if period < 1:
            raise ValueError("efficiency-ratio@1 period must be at least 1")
        return _EfficiencyRatio(period)


BLOCK = _Block()
