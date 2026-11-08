"""z-score@1: how many standard deviations the latest value stands from the mean of the last
``window`` values, the latest among them.

The population standard deviation, as numpy's default. Missing while the window has no
spread. The first value comes at update ``window``.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _ZScore:
    __slots__ = ("_window",)

    def __init__(self, window: int) -> None:
        self._window: deque[float] = deque(maxlen=window)

    @property
    def warm_up_bars(self) -> int:
        return self._window.maxlen or 0

    @property
    def state_bound(self) -> int:
        return self._window.maxlen or 0

    def retained(self) -> int:
        return len(self._window)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        value = evidence.get("series")
        if not isinstance(value, Decimal):
            return None
        values = self._window
        values.append(float(value))
        if len(values) < (values.maxlen or 0):
            return None
        mean = sum(values) / len(values)
        spread = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
        if spread == 0.0:
            return None
        return quantise((values[-1] - mean) / spread)

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        raw = state["window"]
        if not isinstance(raw, list):
            raise ValueError("z-score@1 state's window is a list of hex floats")
        values = [float.fromhex(str(v)) for v in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._window = deque(values, maxlen=self._window.maxlen)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _ZScore:
        window = int(params["window"])
        if window < 2:
            raise ValueError("z-score@1 window must be at least 2")
        return _ZScore(window)


BLOCK = _Block()
