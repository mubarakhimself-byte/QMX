"""percentile-of-own-history@1: a number derived as a percentile of a series' last window.

Once ``window_bars`` values are held, the value is the ``percentile`` (0 to 100) of them with
linear interpolation between closest ranks (numpy's default method).
"""

from __future__ import annotations

from bisect import bisect_left, insort
from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Percentile:
    __slots__ = ("_fraction", "_order", "_size", "_window")

    def __init__(self, percentile: Decimal, size: int) -> None:
        self._fraction = percentile / 100
        self._size = size
        self._window: deque[Decimal] = deque()
        self._order: list[Decimal] = []

    @property
    def warm_up_bars(self) -> int:
        return self._size

    @property
    def state_bound(self) -> int:
        return self._size

    def retained(self) -> int:
        return len(self._window)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        value = evidence.get("series")
        if not isinstance(value, Decimal):
            return None
        self._window.append(value)
        insort(self._order, value)
        if len(self._window) > self._size:
            gone = self._window.popleft()
            del self._order[bisect_left(self._order, gone)]
        if len(self._window) < self._size:
            return None
        rank = self._fraction * (self._size - 1)
        low = int(rank)
        weight = rank - low
        below = self._order[low]
        if weight == 0:
            return quantise(below)
        return quantise(below + (self._order[low + 1] - below) * weight)

    def export_state(self) -> Mapping[str, object]:
        return {"window": [str(v) for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        window = state["window"]
        if not isinstance(window, list):
            raise ValueError("percentile-of-own-history@1 state needs window")
        values = [Decimal(str(v)) for v in window]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._window = deque(values)
        self._order = sorted(values)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Percentile:
        percentile, size = params["percentile"], int(params["window_bars"])
        if not 0 <= percentile <= 100 or size < 1:
            raise ValueError("percentile-of-own-history@1 needs a percentile 0 to 100 and a window")
        return _Percentile(percentile, size)


BLOCK = _Block()
