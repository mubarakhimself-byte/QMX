"""market-next-open@1: enter with a market order at the next bar's open."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import EntryOrder, Side

_ORDER = EntryOrder(kind="market", at="next_open")


class _NextOpen:
    __slots__ = ()

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> EntryOrder:
        return _ORDER

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _NextOpen:
        return _NextOpen()


BLOCK = _Block()
