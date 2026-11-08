"""bollinger-band@1: Bollinger's band, the simple mean of the last ``period`` values plus
``deviations`` population standard deviations.

``deviations`` 2 gives the upper band, -2 the lower and 0 the middle line, as TA-Lib's BBANDS
draws them. The first value comes at update ``period``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in raw]


class _Band:
    __slots__ = ("_deviations", "_period", "_window")

    def __init__(self, period: int, deviations: float) -> None:
        self._period = period
        self._window: deque[float] = deque(maxlen=period)
        self._deviations = deviations

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
        mean = sum(self._window) / self._period
        variance = sum(v * v for v in self._window) / self._period - mean * mean
        spread = math.sqrt(variance) if variance > 0.0 else 0.0
        return quantise(mean + self._deviations * spread)

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        values = _floats(state["window"], "bollinger-band@1 state's window")
        self._window = deque(values, maxlen=self._period)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Band:
        period = int(params["period"])
        if period < 1:
            raise ValueError("bollinger-band@1 period must be at least 1")
        return _Band(period, float(params["deviations"]))


BLOCK = _Block()
