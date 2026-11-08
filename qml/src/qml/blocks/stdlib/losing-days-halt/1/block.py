"""losing-days-halt@1: flatten and stop the unit after ``days`` losing days in a row.

TradingView's ``strategy.risk.max_cons_loss_days`` cancels pending orders, closes the open
position and stops all further trading once the strategy has had a set number of consecutive
losing days. Here the count is the unit's own ``losing_day_streak`` from its journal, and the
halt holds while it is at least ``days``.

An update with no ``losing_day_streak`` halts nothing.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Halt, HaltAction, Scope, Side


class _LosingDays:
    __slots__ = ("_days",)

    def __init__(self, days: int) -> None:
        self._days = days

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Halt | None:
        streak = evidence.get("losing_day_streak")
        if isinstance(streak, bool) or not isinstance(streak, int | Decimal):
            return None
        if streak < self._days:
            return None
        reason = f"{streak} losing days in a row, at or past the limit of {self._days}"
        return Halt(HaltAction.FLATTEN, Scope.UNIT, reason)

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _LosingDays:
        days = int(params["days"])
        if days < 1:
            raise ValueError("losing-days-halt@1 days must be at least 1")
        return _LosingDays(days)


BLOCK = _Block()
