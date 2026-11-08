"""library-sizer-answers-a-float@1: the Library control whose sizer answer is a bare float.

It is saved in the component shape the Library uses, an ``entry.json`` beside a ``block.py``,
so the socket contract proves it enrols Library blocks and judges them with the message it
gives a stdlib block. The sizer slot refuses a float, so this control must fail the contract.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side


class _AnswersAFloat:
    __slots__ = ()

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> object:
        return 0.25

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _AnswersAFloat:
        return _AnswersAFloat()


BLOCK = _Block()
