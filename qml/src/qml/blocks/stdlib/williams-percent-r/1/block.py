"""williams-percent-r@1: where the close sits in the range of the last ``period`` bars.

Matches TA-Lib's WILLR: ``-100 * (highest high - close) / (highest high - lowest low)``, from 0
at the top of the range to -100 at the bottom, and 0 when the range is empty. The first value
comes at update ``period``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Wpr:
    __slots__ = ("_highs", "_lows", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._highs: deque[float] = deque(maxlen=period)
        self._lows: deque[float] = deque(maxlen=period)

    @property
    def warm_up_bars(self) -> int:
        return self._period

    @property
    def state_bound(self) -> int:
        return 2 * self._period

    def retained(self) -> int:
        return len(self._highs) + len(self._lows)

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
        self._highs.append(float(high))
        self._lows.append(float(low))
        if len(self._highs) < self._period:
            return None
        top, bottom = max(self._highs), min(self._lows)
        if top == bottom:
            return quantise(0.0)
        return quantise(-100.0 * (top - float(close)) / (top - bottom))

    def export_state(self) -> Mapping[str, object]:
        return {"highs": [v.hex() for v in self._highs], "lows": [v.hex() for v in self._lows]}

    def import_state(self, state: Mapping[str, object]) -> None:
        highs, lows = state["highs"], state["lows"]
        if not isinstance(highs, list) or not isinstance(lows, list):
            raise ValueError("williams-percent-r@1 state needs highs and lows")
        self._highs = deque((float.fromhex(str(v)) for v in highs), maxlen=self._period)
        self._lows = deque((float.fromhex(str(v)) for v in lows), maxlen=self._period)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Wpr:
        period = int(params["period"])
        if period < 1:
            raise ValueError("williams-percent-r@1 period must be at least 1")
        return _Wpr(period)


BLOCK = _Block()
