"""unrealised-profit-cap@1: close once the open profit ratio passes a cap.

QuantConnect LEAN's ``MaximumUnrealizedProfitPercentPerSecurity`` liquidates a holding whose
unrealised profit percent is above its cap. Here the open profit ratio is read at the bar's
close against the position's ``entry_price``, mirrored on the short side, and the exit holds
while it is above ``cap``; its value is the open profit ratio.

An update with no ``entry_price`` means no position is given, and the exit answers missing.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, Signal, quantise


class _ProfitCap:
    __slots__ = ("_cap", "_side")

    def __init__(self, cap: Decimal, side: Side) -> None:
        self._cap = cap
        self._side = side

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Signal | None:
        entry, bar = evidence.get("entry_price"), evidence.get("series")
        close = bar.get("close") if isinstance(bar, Mapping) else None  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if not isinstance(entry, Decimal) or entry <= 0 or not isinstance(close, Decimal):
            return None
        move = close - entry if self._side is Side.LONG else entry - close
        profit = move / entry
        return Signal(state=profit > self._cap, value=quantise(profit))

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _ProfitCap:
        cap = params["cap"]
        if cap <= 0:
            raise ValueError("unrealised-profit-cap@1 cap must be above 0")
        return _ProfitCap(cap, side)


BLOCK = _Block()
