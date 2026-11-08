"""ema@1: exponential moving average, seeded with the simple mean of the first ``period`` values.

Matches TA-Lib's EMA: the first value comes at the ``period``-th update, then
``ema += (x - ema) * 2 / (period + 1)``.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Ema:
    __slots__ = ("_acc", "_alpha", "_count", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._alpha = 2.0 / (period + 1)
        self._count = 0
        self._acc = 0.0

    @property
    def warm_up_bars(self) -> int:
        return self._period

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 1

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        x = float(price)
        self._count += 1
        if self._count < self._period:
            self._acc += x
            return None
        if self._count == self._period:
            self._acc = (self._acc + x) / self._period
        else:
            self._acc += (x - self._acc) * self._alpha
        return quantise(self._acc)

    def export_state(self) -> Mapping[str, object]:
        return {"count": self._count, "acc": self._acc.hex()}

    def import_state(self, state: Mapping[str, object]) -> None:
        count, acc = state["count"], state["acc"]
        if not isinstance(count, int) or not isinstance(acc, str):
            raise ValueError("ema@1 state needs count and acc")
        self._count = count
        self._acc = float.fromhex(acc)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Ema:
        period = int(params["period"])
        if period < 1:
            raise ValueError("ema@1 period must be at least 1")
        return _Ema(period)


BLOCK = _Block()
