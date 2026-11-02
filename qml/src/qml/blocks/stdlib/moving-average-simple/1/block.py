"""moving-average-simple@1: the mean of the last ``period`` values.

Matches TA-Lib's SMA: the first value comes at update ``period``, then the running total gains
the new value and loses the one that left the window.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Sma:
    __slots__ = ("_period", "_total", "_window")

    def __init__(self, period: int) -> None:
        self._period = period
        self._window: deque[float] = deque(maxlen=period)
        self._total = 0.0

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
        if len(self._window) == self._period:
            self._total -= self._window[0]
        self._window.append(x)
        self._total += x
        if len(self._window) < self._period:
            return None
        return quantise(self._total / self._period)

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window], "total": self._total.hex()}

    def import_state(self, state: Mapping[str, object]) -> None:
        window, total = state["window"], state["total"]
        if not isinstance(window, list) or not isinstance(total, str):
            raise ValueError("moving-average-simple@1 state needs window and total")
        self._window = deque((float.fromhex(str(v)) for v in window), maxlen=self._period)
        self._total = float.fromhex(total)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Sma:
        period = int(params["period"])
        if period < 1:
            raise ValueError("moving-average-simple@1 period must be at least 1")
        return _Sma(period)


BLOCK = _Block()
