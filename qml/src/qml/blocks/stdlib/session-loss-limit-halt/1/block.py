"""session-loss-limit-halt@1: flatten and stop the unit for the session once it has lost ``limit`` R.

TradingView's ``strategy.risk.max_intraday_loss`` closes the open position and stops trading
until the end of the session once the day's losses reach its threshold. Here the loss is the
unit's own session result in R from its journal, ``session_loss_r`` (negative is a loss), and
the halt holds while that result is at or below ``-limit``. The host resets the session result
at each session start, which releases the halt.

An update with no ``session_loss_r`` halts nothing.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Halt, HaltAction, Scope, Side


class _SessionLoss:
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
        result = evidence.get("session_loss_r")
        if not isinstance(result, Decimal) or result > -self._limit:
            return None
        reason = f"lost {-result}R this session, at or past the {self._limit}R limit"
        return Halt(HaltAction.FLATTEN, Scope.UNIT, reason)

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _SessionLoss:
        limit = params["limit"]
        if limit <= 0:
            raise ValueError("session-loss-limit-halt@1 limit must be above 0")
        return _SessionLoss(limit)


BLOCK = _Block()
