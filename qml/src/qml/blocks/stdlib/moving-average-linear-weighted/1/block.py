"""moving-average-linear-weighted@1: the last ``period`` values weighted 1 to ``period``.

Matches TA-Lib's WMA: the newest value weighs ``period``, the oldest 1, and the sum is divided
by ``period * (period + 1) / 2``. The first value comes at update ``period``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


class _Lwma:
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
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        self._window.append(float(price))
        if len(self._window) < self._period:
            return None
        weighted = sum((i + 1) * v for i, v in enumerate(self._window))
        return quantise(weighted / (self._period * (self._period + 1) / 2))

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        window = state["window"]
        if not isinstance(window, list):
            raise ValueError("moving-average-linear-weighted@1 state needs window")
        self._window = deque(
            (float.fromhex(str(v)) for v in cast("list[object]", window)), maxlen=self._period
        )


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Lwma:
        period = int(params["period"])
        if period < 1:
            raise ValueError("moving-average-linear-weighted@1 period must be at least 1")
        return _Lwma(period)


BLOCK = _Block()
