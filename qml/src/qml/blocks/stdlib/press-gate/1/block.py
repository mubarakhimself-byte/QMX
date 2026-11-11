"""press-gate@1: the gate in front of every raise on the size (AD-11).

A gate is a sizing modifier whose face measures a ``flag``: it answers 1 when a raise may stand and
0 when it waits, and the unit never multiplies a size by it. Every row behind a closed gate that
answers above 1 is held at 1, so a raise waits and a cut stands.

This gate opens while the unit's fold word is ``ACTIVE``, which the unit hands every modifier as
``risk_word``. A unit that a brake is reducing, that is coming back from a restore, or whose fold
cannot see a fact it needs, does not press. ``group.raise_ok`` joins it when group facts exist.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Factor, Side

_OPEN = "ACTIVE"
_RANGE = (Decimal(0), Decimal(1))


class _PressGate:
    __slots__ = ()

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Factor | None:
        word = evidence.get("risk_word")
        if not isinstance(word, str):
            return None
        if word == _OPEN:
            return Factor(Decimal(1), _RANGE, f"pressing is open while the unit is {word}")
        return Factor(Decimal(0), _RANGE, f"pressing waits while the unit is {word}")

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _PressGate:
        return _PressGate()


BLOCK = _Block()
