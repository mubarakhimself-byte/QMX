"""time-exit-bars@1 (placeholder, owner the risk session): close after ``bars`` bars held.

One instance serves one position, and each update is one closed bar while it is open.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, Signal


class _TimeExit:
    __slots__ = ("_bars", "_held")

    def __init__(self, bars: int) -> None:
        self._bars = bars
        self._held = 0

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 1

    def update(self, evidence: Mapping[str, object]) -> Signal:
        self._held += 1
        return Signal(state=self._held >= self._bars, value=Decimal(self._held))

    def export_state(self) -> Mapping[str, object]:
        return {"held": self._held}

    def import_state(self, state: Mapping[str, object]) -> None:
        held = state["held"]
        if not isinstance(held, int):
            raise ValueError("time-exit-bars@1 state needs held")
        self._held = held


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _TimeExit:
        bars = int(params["bars"])
        if bars < 1:
            raise ValueError("time-exit-bars@1 bars must be at least 1")
        return _TimeExit(bars)


BLOCK = _Block()
