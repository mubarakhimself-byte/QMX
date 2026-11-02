"""momersion@1: Harris's Momersion, the share of momentum steps among the last ``period`` steps.

A step is the product of a bar's change and the change before it: positive when the move goes
on, negative when it turns back. The value is ``100 * momentum / (momentum + reversion)``, as
QuantConnect LEAN's Momersion with no minimum period. Where LEAN prints 50 because half the
steps or more are zero, or before it is ready, this block leaves the value missing. The first
value comes at update ``period + 3``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Momersion:
    __slots__ = ("_count", "_prices", "_steps")

    def __init__(self, period: int) -> None:
        self._steps: deque[float] = deque(maxlen=period)
        self._prices: deque[float] = deque(maxlen=2)
        self._count = 0

    @property
    def warm_up_bars(self) -> int:
        return (self._steps.maxlen or 0) + 3

    @property
    def state_bound(self) -> int:
        return (self._steps.maxlen or 0) + 2

    def retained(self) -> int:
        return len(self._steps) + len(self._prices)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        new, prices = float(price), self._prices
        if len(prices) == prices.maxlen:
            self._steps.append((new - prices[1]) * (prices[1] - prices[0]))
            self._count = min(self._count + 1, (self._steps.maxlen or 0) + 1)
        prices.append(new)
        steps = self._steps
        if self._count <= (steps.maxlen or 0):
            return None
        if sum(1 for s in steps if s == 0.0) >= 0.5 * len(steps):
            return None
        up, down = sum(1 for s in steps if s > 0.0), sum(1 for s in steps if s < 0.0)
        return quantise(Decimal(100 * up) / Decimal(up + down))

    def export_state(self) -> Mapping[str, object]:
        return {
            "steps": [v.hex() for v in self._steps],
            "prices": [v.hex() for v in self._prices],
            "count": self._count,
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        steps, prices, count = state["steps"], state["prices"], state["count"]
        if (
            not isinstance(steps, list)
            or not isinstance(prices, list)
            or not isinstance(count, int)
        ):
            raise ValueError("momersion@1 state needs steps, prices and count")
        loaded = [float.fromhex(str(v)) for v in steps]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        last = [float.fromhex(str(v)) for v in prices]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._steps = deque(loaded, maxlen=self._steps.maxlen)
        self._prices = deque(last, maxlen=2)
        self._count = count


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Momersion:
        period = int(params["period"])
        if period < 4:
            raise ValueError("momersion@1 period must be at least 4")
        return _Momersion(period)


BLOCK = _Block()
