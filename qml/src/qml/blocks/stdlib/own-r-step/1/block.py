"""own-r-step@1 (labelled placeholder, owner "numbers talk"): move a number one step by its trades.

Given the unit's closed trades, each with its R after costs: once at least ``min_count`` have
closed, take their mean R. Below zero, move the number one ``step`` toward ``cautious``; above
zero, one step away from it; at zero, stay. The answer is held inside ``[min, max]``, and an answer
that leaves the number where it is answers nothing, so no move is written. ``cautious`` is ``-1``
for a number whose smaller value is the cautious one (a fraction at risk, a target multiple) and
``1`` for one whose larger value is.

The compiler hands ``min_count``, ``min``, ``max`` and ``step`` from the number's own
``min_count`` and ``range``, so one rule binds a sizing number and an exit number alike. The motion
engine decides when it runs (the cadence); this block only answers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from qml.blocks.api import Side

_TOWARD_SMALLER = Decimal(-1)
"""Starting default of the ``cautious`` setting: a smaller value is the cautious one."""


class _OwnRStep:
    __slots__ = ("_cautious", "_high", "_low", "_min_count", "_step")

    def __init__(self, params: Mapping[str, Decimal]) -> None:
        self._min_count = int(params["min_count"])
        self._low, self._high, self._step = params["min"], params["max"], params["step"]
        self._cautious = params.get("cautious", _TOWARD_SMALLER).compare(Decimal(0))

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        raw, current = evidence.get("trades"), evidence.get("current")
        if not isinstance(raw, Sequence) or not isinstance(current, Decimal):
            return None
        rs: list[Decimal] = []
        for item in raw:  # pyright: ignore[reportUnknownVariableType]
            if not isinstance(item, Mapping):
                return None
            r = item.get("r")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            if not isinstance(r, Decimal):
                return None
            rs.append(r)
        if len(rs) < self._min_count or not rs:
            return None
        mean = sum(rs, Decimal(0)) / len(rs)
        if mean == 0:
            return None
        direction = self._cautious if mean < 0 else -self._cautious
        moved = min(self._high, max(self._low, current + direction * self._step))
        return None if moved == current else moved

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _OwnRStep:
        return _OwnRStep(params)


BLOCK = _Block()
