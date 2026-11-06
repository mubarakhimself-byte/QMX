"""value-above@1: whether a value is above ``level``, or below it when ``below`` is 1.

The comparison a slot needs to gate on a value that holds nothing by itself, such as ADX above 25
or RSI below 30. Both comparisons are strict. ``level`` may move, so this instant's value in the
evidence wins over the made one. A value is above a level or not whichever way a unit trades, so
both sides read the same rule. A missing value answers nothing.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, Signal


class _ValueAbove:
    __slots__ = ("_below", "_level")

    def __init__(self, level: Decimal, below: bool) -> None:
        self._level = level
        self._below = below

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Signal | None:
        value = evidence.get("series")
        if not isinstance(value, Decimal):
            return None
        moved = evidence.get("level")
        level = moved if isinstance(moved, Decimal) else self._level
        return Signal(state=value < level if self._below else value > level, value=value)

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _ValueAbove:
        below = params.get("below", Decimal(0))
        if below not in (0, 1):
            raise ValueError("value-above@1 below is 0 for above, 1 for below")
        return _ValueAbove(params["level"], below == 1)


BLOCK = _Block()
