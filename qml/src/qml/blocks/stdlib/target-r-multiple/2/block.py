"""target-r-multiple@2: a target ``multiple`` R away, with ``multiple`` read from evidence.

R is the distance from the position's entry to its stop, so the target is
``entry + multiple * (entry - stop)``; the same formula serves both sides. The multiple is read
from ``evidence`` on every call, so a number that moves reaches the target; ``make`` only seeds
it (AD-14 step 3).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Target:
    __slots__ = ("_multiple",)

    def __init__(self, multiple: Decimal) -> None:
        self._multiple = multiple

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        entry, stop = evidence.get("entry_price"), evidence.get("stop_price")
        if not isinstance(entry, Decimal) or not isinstance(stop, Decimal) or entry == stop:
            return None
        moved = evidence.get("multiple")
        multiple = moved if isinstance(moved, Decimal) else self._multiple
        return quantise(entry + multiple * (entry - stop))

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Target:
        return _Target(params["multiple"])


BLOCK = _Block()
