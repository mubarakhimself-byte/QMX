"""level-factor@1: the level, as one named sizing modifier with no ladder law (AD-11).

A modifier answers a factor inside a range it declares, with the reason the receipt prints. This
block answers the level the template names, inside the range written beside it: ``level`` at least
0 and at most ``max_level``. It computes no ladder and moves nothing by itself, so how a level
starts and how it grows is another row's content. The level is read from ``evidence`` on every
call, so a number that moves reaches the factor; ``make`` only seeds it (AD-14 step 3).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Factor, Side

_LOW = Decimal(0)
"""A factor below zero would turn the sizer's direction around, so every level starts at zero."""


def _text(value: Decimal) -> str:
    return format(value, "f")


class _LevelFactor:
    __slots__ = ("_level", "_max_level")

    def __init__(self, level: Decimal, max_level: Decimal) -> None:
        self._level = level
        self._max_level = max_level

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Factor | None:
        moved_level = evidence.get("level")
        moved_max = evidence.get("max_level")
        level = moved_level if isinstance(moved_level, Decimal) else self._level
        max_level = moved_max if isinstance(moved_max, Decimal) else self._max_level
        if max_level <= _LOW:
            return None
        return Factor(
            value=level,
            range=(_LOW, max_level),
            reason=f"the level {_text(level)} sits inside {_text(_LOW)} to {_text(max_level)}",
        )

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _LevelFactor:
        return _LevelFactor(params["level"], params["max_level"])


BLOCK = _Block()
