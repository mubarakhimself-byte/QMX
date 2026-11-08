"""equity-drawdown-halt@1: flatten the account and stop trading once equity falls ``max_drawdown``.

QuantConnect LEAN's ``MaximumDrawdownPercentPortfolio`` liquidates when the portfolio value has
fallen more than ``maximumDrawdownPercent`` from its starting value, or from its last high when
``isTrailing`` is true; a new high in trailing mode does not check. TradingView's
``strategy.risk.max_drawdown`` closes the position and stops all further trading once the
drawdown reaches its amount. Here the base is the first ``equity`` given, or its highest when
``trailing`` is 1, and the halt holds from the first update where ``equity / base - 1`` is
below ``-max_drawdown``. It then keeps holding, as TradingView's does, where LEAN restarts from
the next value; releasing it is his call.

An update with no ``equity`` halts nothing and leaves the base as it is.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Halt, HaltAction, Scope, Side, quantise


class _EquityDrawdown:
    __slots__ = ("_base", "_breached", "_most", "_trailing")

    def __init__(self, most: Decimal, trailing: bool) -> None:
        self._most = most
        self._trailing = trailing
        self._base: Decimal | None = None
        self._breached: str | None = None

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 2

    def retained(self) -> int:
        return (self._base is not None) + (self._breached is not None)

    def update(self, evidence: Mapping[str, object]) -> Halt | None:
        if self._breached is not None:
            return Halt(HaltAction.FLATTEN, Scope.ACCOUNT, self._breached)
        equity = evidence.get("equity")
        if not isinstance(equity, Decimal) or equity <= 0:
            return None
        if self._base is None or (self._trailing and equity > self._base):
            self._base = equity
            return None
        drawdown = equity / self._base - 1
        if drawdown >= -self._most:
            return None
        self._breached = (
            f"equity {equity} is {quantise(-drawdown)} below its base {self._base}, "
            f"past the {self._most} drawdown limit"
        )
        return Halt(HaltAction.FLATTEN, Scope.ACCOUNT, self._breached)

    def export_state(self) -> Mapping[str, object]:
        return {"base": None if self._base is None else str(self._base), "breached": self._breached}

    def import_state(self, state: Mapping[str, object]) -> None:
        base, breached = state.get("base"), state.get("breached")
        self._base = Decimal(base) if isinstance(base, str) else None
        self._breached = breached if isinstance(breached, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _EquityDrawdown:
        most, trailing = params["max_drawdown"], params["trailing"]
        if not 0 < most < 1 or trailing not in (0, 1):
            raise ValueError("equity-drawdown-halt@1 needs 0 < max_drawdown < 1, trailing 0 or 1")
        return _EquityDrawdown(most, trailing == 1)


BLOCK = _Block()
