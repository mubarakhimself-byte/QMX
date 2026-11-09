"""time-exit-bars@2: close after ``bars`` bars held, and answer its own reason code.

One instance serves one position, and each update is one closed bar while it is open. The bar
count is read from ``evidence`` on every update, so a number that moves reaches the exit;
``make`` only seeds it (AD-14 step 3). The answer is an ``ExitAction`` carrying the reason code
``time``, so the close row names this exit and its own word rather than the host's.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import ExitAction, Side

REASON_CODE = "time"
"""The word this exit's closes carry, beside the pin that answered them."""


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

    def update(self, evidence: Mapping[str, object]) -> ExitAction | None:
        moved = evidence.get("bars")
        bars = int(moved) if isinstance(moved, Decimal) else self._bars
        self._held += 1
        if self._held < bars:
            return None
        return ExitAction(kind="close_full", reason_code=REASON_CODE)

    def export_state(self) -> Mapping[str, object]:
        return {"held": self._held}

    def import_state(self, state: Mapping[str, object]) -> None:
        held = state["held"]
        if not isinstance(held, int):
            raise ValueError("time-exit-bars@2 state needs held")
        self._held = held


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _TimeExit:
        bars = int(params["bars"])
        if bars < 1:
            raise ValueError("time-exit-bars@2 bars must be at least 1")
        return _TimeExit(bars)


BLOCK = _Block()
