"""session-fill-limit-halt@1: flatten and stop the unit for the session after too many fills.

TradingView's ``strategy.risk.max_intraday_filled_orders`` sets the most filled orders per
trading day; when the strategy fills more, it cancels pending orders, closes the open position
and halts trading until the session ends. Here the count is the unit's own ``session_fills``
from its journal, and the halt holds while it is above ``fills``. The host resets the count at
each session start, which releases the halt.

An update with no ``session_fills`` halts nothing.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Halt, HaltAction, Scope, Side


class _SessionFills:
    __slots__ = ("_fills",)

    def __init__(self, fills: int) -> None:
        self._fills = fills

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Halt | None:
        filled = evidence.get("session_fills")
        if isinstance(filled, bool) or not isinstance(filled, int | Decimal):
            return None
        if filled <= self._fills:
            return None
        reason = f"{filled} fills this session, above the limit of {self._fills}"
        return Halt(HaltAction.FLATTEN, Scope.UNIT, reason)

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _SessionFills:
        fills = int(params["fills"])
        if fills < 1:
            raise ValueError("session-fill-limit-halt@1 fills must be at least 1")
        return _SessionFills(fills)


BLOCK = _Block()
