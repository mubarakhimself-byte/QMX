"""stepped-profit-stop@1: move the stop to fixed levels above entry as the profit passes steps.

freqtrade's "stepped stoploss" example keeps the initial stop until the profit is above 20%,
then sets the stop 7% above the open price; above 25% profit, 15% above; above 40%, 25%
above. The highest step passed wins and the stop never moves back. Here the profit is read at
the bar's high for a long and its low for a short, as freqtrade's backtest reads it, and the
short side is the mirror: the stop sits ``lock`` below ``entry_price``.

Before the first step the level is missing: the unit's own initial stop holds. One instance
serves one position on its side. An update with no ``entry_price`` means no position is given:
the stop answers missing and forgets its level.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise

_STEPS = 3


class _SteppedStop:
    __slots__ = ("_side", "_steps", "_stop")

    def __init__(self, steps: tuple[tuple[Decimal, Decimal], ...], side: Side) -> None:
        self._steps = steps
        self._side = side
        self._stop: Decimal | None = None

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 0 if self._stop is None else 1

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        entry, bar = evidence.get("entry_price"), evidence.get("series")
        if not isinstance(entry, Decimal) or entry <= 0:
            self._stop = None
            return None
        long = self._side is Side.LONG
        rate = bar.get("high" if long else "low") if isinstance(bar, Mapping) else None  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if not isinstance(rate, Decimal):
            return self._stop
        profit = (rate - entry if long else entry - rate) / entry
        lock = next((lock for trigger, lock in reversed(self._steps) if profit > trigger), None)
        if lock is None:
            return self._stop
        level = quantise(entry * (1 + lock) if long else entry * (1 - lock))
        if self._stop is None or (level > self._stop if long else level < self._stop):
            self._stop = level
        return self._stop

    def export_state(self) -> Mapping[str, object]:
        return {"stop": None if self._stop is None else str(self._stop)}

    def import_state(self, state: Mapping[str, object]) -> None:
        stop = state.get("stop")
        self._stop = Decimal(stop) if isinstance(stop, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _SteppedStop:
        steps = tuple((params[f"trigger_{k}"], params[f"lock_{k}"]) for k in range(1, _STEPS + 1))
        rising = all(
            steps[k - 1][0] < steps[k][0] and steps[k - 1][1] < steps[k][1]
            for k in range(1, len(steps))
        )
        if not rising or any(lock >= trigger for trigger, lock in steps):
            raise ValueError(
                "stepped-profit-stop@1 needs rising steps, each lock below its trigger"
            )
        return _SteppedStop(steps, side)


BLOCK = _Block()
