"""cci@1: Lambert's Commodity Channel Index over ``period`` bars.

Matches TA-Lib's CCI: the typical price ``(high + low + close) / 3`` against its simple mean
over ``period`` bars, divided by 0.015 times the mean absolute deviation; 0 when the deviation
is 0. The first value comes at update ``period``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise

_LAMBERT: float = 0.015


class _Cci:
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
        bar = evidence.get("series")
        if not isinstance(bar, Mapping):
            return None
        fields = bar
        high, low, close = fields.get("high"), fields.get("low"), fields.get("close")
        if not (
            isinstance(high, Decimal) and isinstance(low, Decimal) and isinstance(close, Decimal)
        ):
            return None
        typical = (float(high) + float(low) + float(close)) / 3
        self._window.append(typical)
        if len(self._window) < self._period:
            return None
        mean = sum(self._window) / self._period
        deviation = sum(abs(v - mean) for v in self._window) / self._period
        if deviation == 0.0:
            return quantise(0.0)
        return quantise((typical - mean) / (_LAMBERT * deviation))

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        window = state["window"]
        if not isinstance(window, list):
            raise ValueError("cci@1 state needs window")
        self._window = deque((float.fromhex(str(v)) for v in window), maxlen=self._period)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Cci:
        period = int(params["period"])
        if period < 2:
            raise ValueError("cci@1 period must be at least 2")
        return _Cci(period)


BLOCK = _Block()
