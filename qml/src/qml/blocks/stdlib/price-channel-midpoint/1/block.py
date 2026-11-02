"""price-channel-midpoint@1: the middle of the high-low channel of the last ``period`` bars,
read ``shift`` bars late.

``(highest high + lowest low) / 2``, as TA-Lib's MIDPRICE. Ichimoku's Tenkan-sen is period 9
and shift 0, its Kijun-sen 26 and 0, and its Senkou Span B 52 and 26, drawn 26 bars ahead, so
at each bar it reads the value of 26 bars before. The first value comes at update
``period + shift``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in cast("list[object]", raw)]


def _bar(evidence: Mapping[str, object], *names: str) -> tuple[float, ...] | None:
    """The named fields of the bar on the ``series`` port as floats, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = cast("Mapping[str, object]", bar)
    found = [fields.get(name) for name in names]
    if not all(isinstance(v, Decimal) for v in found):
        return None
    return tuple(float(cast("Decimal", v)) for v in found)


class _Midpoint:
    """The middle of the highest high and lowest low of the last ``period`` bars."""

    __slots__ = ("highs", "lows", "period")

    def __init__(self, period: int) -> None:
        self.period = period
        self.highs: deque[float] = deque(maxlen=period)
        self.lows: deque[float] = deque(maxlen=period)

    def step(self, high: float, low: float) -> float | None:
        self.highs.append(high)
        self.lows.append(low)
        if len(self.highs) < self.period:
            return None
        return (max(self.highs) + min(self.lows)) / 2

    def held(self) -> int:
        return len(self.highs) + len(self.lows)

    def state(self) -> list[list[str]]:
        return [[v.hex() for v in self.highs], [v.hex() for v in self.lows]]

    def restore(self, raw: object) -> None:
        if not isinstance(raw, list) or len(cast("list[object]", raw)) != 2:
            raise ValueError("a midpoint's state is [highs, lows]")
        highs, lows = cast("Sequence[object]", raw)
        self.highs = deque(_floats(highs, "its highs"), maxlen=self.period)
        self.lows = deque(_floats(lows, "its lows"), maxlen=self.period)


class _ChannelMidpoint:
    __slots__ = ("_mid", "_past", "_shift")

    def __init__(self, period: int, shift: int) -> None:
        self._mid = _Midpoint(period)
        self._shift = shift
        self._past: deque[float] = deque(maxlen=shift + 1)

    @property
    def warm_up_bars(self) -> int:
        return self._mid.period + self._shift

    @property
    def state_bound(self) -> int:
        return 2 * self._mid.period + self._shift + 1

    def retained(self) -> int:
        return self._mid.held() + len(self._past)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low")
        if found is None:
            return None
        value = self._mid.step(*found)
        if value is None:
            return None
        self._past.append(value)
        return quantise(self._past[0]) if len(self._past) == self._shift + 1 else None

    def export_state(self) -> Mapping[str, object]:
        return {"mid": self._mid.state(), "past": [v.hex() for v in self._past]}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._mid.restore(state["mid"])
        self._past = deque(_floats(state["past"], "its past"), maxlen=self._shift + 1)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _ChannelMidpoint:
        period, shift = int(params["period"]), int(params["shift"])
        if period < 1 or shift < 0:
            raise ValueError("price-channel-midpoint@1 period must be 1+ and shift 0+")
        return _ChannelMidpoint(period, shift)


BLOCK = _Block()
