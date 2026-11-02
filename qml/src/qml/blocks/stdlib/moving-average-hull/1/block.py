"""moving-average-hull@1: Hull's moving average.

``LWMA(2 * LWMA(period // 2) - LWMA(period), isqrt(period))``, each LWMA weighting its newest
value most, as TA-Lib's WMA does. The first value comes at update
``period + isqrt(period) - 1``.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


def _lwma(window: deque[float]) -> float:
    n = len(window)
    return sum((i + 1) * v for i, v in enumerate(window)) / (n * (n + 1) / 2)


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in cast("list[object]", raw)]


class _Hull:
    __slots__ = ("_half", "_period", "_raw", "_root", "_window")

    def __init__(self, period: int) -> None:
        self._period = period
        self._half = period // 2
        self._root = math.isqrt(period)
        self._window: deque[float] = deque(maxlen=period)
        self._raw: deque[float] = deque(maxlen=self._root)

    @property
    def warm_up_bars(self) -> int:
        return self._period + self._root - 1

    @property
    def state_bound(self) -> int:
        return self._period + self._root

    def retained(self) -> int:
        return len(self._window) + len(self._raw)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        self._window.append(float(price))
        if len(self._window) < self._period:
            return None
        recent = deque(list(self._window)[-self._half :])
        self._raw.append(2.0 * _lwma(recent) - _lwma(self._window))
        if len(self._raw) < self._root:
            return None
        return quantise(_lwma(self._raw))

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window], "raw": [v.hex() for v in self._raw]}

    def import_state(self, state: Mapping[str, object]) -> None:
        window = _floats(state["window"], "moving-average-hull@1 state's window")
        self._window = deque(window, maxlen=self._period)
        self._raw = deque(_floats(state["raw"], "its raw values"), maxlen=self._root)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Hull:
        period = int(params["period"])
        if period < 2:
            raise ValueError("moving-average-hull@1 period must be at least 2")
        return _Hull(period)


BLOCK = _Block()
