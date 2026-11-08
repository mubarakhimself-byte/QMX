"""account-daily-loss-halt@1: flatten the account for the day once it has lost ``limit`` of its
day-start equity.

The MQL5 article "Implementing a Daily Loss Limit and Drawdown Circuit Breaker" sums the day's
realised and floating result from the broker's server midnight, compares it with a daily loss
limit, and on a breach closes every position, cancels every pending order and halts. Here the
day's result is ``equity / day_start_equity - 1``, where ``equity`` holds the floating result
and the host sets ``day_start_equity`` at its day boundary, and the halt holds while that
result is at or below ``-limit``. A new day's ``day_start_equity`` releases it.

An update with no ``equity`` or ``day_start_equity`` halts nothing.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Halt, HaltAction, Scope, Side, quantise


class _DailyLoss:
    __slots__ = ("_limit",)

    def __init__(self, limit: Decimal) -> None:
        self._limit = limit

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Halt | None:
        equity, start = evidence.get("equity"), evidence.get("day_start_equity")
        if not isinstance(equity, Decimal) or not isinstance(start, Decimal) or start <= 0:
            return None
        result = equity / start - 1
        if result > -self._limit:
            return None
        reason = (
            f"the account is down {quantise(-result)} today, at or past the {self._limit} limit"
        )
        return Halt(HaltAction.FLATTEN, Scope.ACCOUNT, reason)

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _DailyLoss:
        limit = params["limit"]
        if not 0 < limit < 1:
            raise ValueError("account-daily-loss-halt@1 limit must be between 0 and 1")
        return _DailyLoss(limit)


BLOCK = _Block()
