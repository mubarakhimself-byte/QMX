"""ichimoku-senkou-a@1: Ichimoku's Senkou Span A, read ``shift`` bars late.

The mean of the Tenkan-sen (the high-low channel's middle over ``tenkan`` bars) and the
Kijun-sen (the same over ``kijun`` bars), drawn ``shift`` bars ahead, so at each bar it reads
the value of ``shift`` bars before. The first value comes at update
``max(tenkan, kijun) + shift``.
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


class _SenkouA:
    __slots__ = ("_kijun", "_past", "_shift", "_tenkan")

    def __init__(self, tenkan: int, kijun: int, shift: int) -> None:
        self._tenkan = _Midpoint(tenkan)
        self._kijun = _Midpoint(kijun)
        self._shift = shift
        self._past: deque[float] = deque(maxlen=shift + 1)

    @property
    def warm_up_bars(self) -> int:
        return max(self._tenkan.period, self._kijun.period) + self._shift

    @property
    def state_bound(self) -> int:
        return 2 * (self._tenkan.period + self._kijun.period) + self._shift + 1

    def retained(self) -> int:
        return self._tenkan.held() + self._kijun.held() + len(self._past)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low")
        if found is None:
            return None
        tenkan, kijun = self._tenkan.step(*found), self._kijun.step(*found)
        if tenkan is None or kijun is None:
            return None
        self._past.append((tenkan + kijun) / 2)
        return quantise(self._past[0]) if len(self._past) == self._shift + 1 else None

    def export_state(self) -> Mapping[str, object]:
        return {
            "tenkan": self._tenkan.state(),
            "kijun": self._kijun.state(),
            "past": [v.hex() for v in self._past],
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        self._tenkan.restore(state["tenkan"])
        self._kijun.restore(state["kijun"])
        self._past = deque(_floats(state["past"], "its past"), maxlen=self._shift + 1)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _SenkouA:
        tenkan, kijun, shift = (int(params[k]) for k in ("tenkan", "kijun", "shift"))
        if min(tenkan, kijun) < 1 or shift < 0:
            raise ValueError("ichimoku-senkou-a@1 periods must be 1+ and shift 0+")
        return _SenkouA(tenkan, kijun, shift)


BLOCK = _Block()
