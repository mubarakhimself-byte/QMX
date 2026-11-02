"""choppiness-index@1: Dreiss's choppiness index over the last ``period`` bars.

``100 log10(sum of true ranges / (highest high - lowest low)) / log10(period)``, as QuantConnect
LEAN's ChoppinessIndex computes it: the first bar's true range is its high less its low, and a
window with no range at all reads 100. Near 100 when the bars overlap, lower when they travel.
The first value comes at update ``period``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


def _bar(evidence: Mapping[str, object]) -> tuple[float, float, float] | None:
    """The bar on the ``series`` port as high, low and close, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    found = [bar.get(name) for name in ("high", "low", "close")]
    prices = [float(v) for v in found if isinstance(v, Decimal)]
    if len(prices) != len(found):
        return None
    return prices[0], prices[1], prices[2]


class _Choppiness:
    __slots__ = ("_highs", "_last", "_lows", "_ranges")

    def __init__(self, period: int) -> None:
        self._highs: deque[float] = deque(maxlen=period)
        self._lows: deque[float] = deque(maxlen=period)
        self._ranges: deque[float] = deque(maxlen=period)
        self._last: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._ranges.maxlen or 0

    @property
    def state_bound(self) -> int:
        return 3 * (self._ranges.maxlen or 0) + 1

    def retained(self) -> int:
        return len(self._highs) + len(self._lows) + len(self._ranges) + (self._last is not None)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence)
        if found is None:
            return None
        high, low, close = found
        before, self._last = self._last, close
        true_range = high - low if before is None else max(high, before) - min(low, before)
        self._highs.append(high)
        self._lows.append(low)
        self._ranges.append(true_range)
        period = self._ranges.maxlen or 0
        if len(self._ranges) < period:
            return None
        top, bottom = max(self._highs), min(self._lows)
        if top == bottom:
            return quantise(100.0)
        ratio = sum(self._ranges) / (top - bottom)
        return quantise(100.0 * math.log10(ratio) / math.log10(period))

    def export_state(self) -> Mapping[str, object]:
        return {
            "highs": [v.hex() for v in self._highs],
            "lows": [v.hex() for v in self._lows],
            "ranges": [v.hex() for v in self._ranges],
            "last": None if self._last is None else self._last.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        period = self._ranges.maxlen
        loaded: list[deque[float]] = []
        for name in ("highs", "lows", "ranges"):
            raw = state[name]
            if not isinstance(raw, list):
                raise ValueError(f"choppiness-index@1 state's {name} is a list of hex floats")
            values = [float.fromhex(str(v)) for v in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
            loaded.append(deque(values, maxlen=period))
        self._highs, self._lows, self._ranges = loaded
        last = state.get("last")
        self._last = float.fromhex(last) if isinstance(last, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Choppiness:
        period = int(params["period"])
        if period < 2:
            raise ValueError("choppiness-index@1 period must be at least 2")
        return _Choppiness(period)


BLOCK = _Block()
