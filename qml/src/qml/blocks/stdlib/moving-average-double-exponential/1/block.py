"""moving-average-double-exponential@1: Mulloy's DEMA, ``2 * EMA - EMA(EMA)``.

Matches TA-Lib's DEMA: each EMA is seeded with the simple mean of its first ``period`` inputs
and then moves by ``2 / (period + 1)``, so the first value comes at update ``2 * period - 1``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


class _Ema:
    __slots__ = ("acc", "alpha", "count", "period")

    def __init__(self, period: int) -> None:
        self.period = period
        self.alpha = 2.0 / (period + 1)
        self.count = 0
        self.acc = 0.0

    def step(self, x: float) -> float | None:
        self.count += 1
        if self.count < self.period:
            self.acc += x
            return None
        if self.count == self.period:
            self.acc = (self.acc + x) / self.period
        else:
            self.acc += (x - self.acc) * self.alpha
        return self.acc

    def state(self) -> list[object]:
        return [self.count, self.acc.hex()]

    def restore(self, raw: object) -> None:
        if not isinstance(raw, list) or len(cast("list[object]", raw)) != 2:
            raise ValueError("an EMA's state is [count, acc]")
        count, acc = cast("Sequence[object]", raw)
        if not isinstance(count, int) or not isinstance(acc, str):
            raise ValueError("an EMA's state is [count, acc]")
        self.count, self.acc = count, float.fromhex(acc)


class _Dema:
    __slots__ = ("_inner", "_outer", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._inner = _Ema(period)
        self._outer = _Ema(period)

    @property
    def warm_up_bars(self) -> int:
        return 2 * self._period - 1

    @property
    def state_bound(self) -> int:
        return 2

    def retained(self) -> int:
        return 2

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        first = self._inner.step(float(price))
        if first is None:
            return None
        second = self._outer.step(first)
        if second is None:
            return None
        return quantise(2.0 * first - second)

    def export_state(self) -> Mapping[str, object]:
        return {"inner": self._inner.state(), "outer": self._outer.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._inner.restore(state["inner"])
        self._outer.restore(state["outer"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Dema:
        period = int(params["period"])
        if period < 1:
            raise ValueError("moving-average-double-exponential@1 period must be at least 1")
        return _Dema(period)


BLOCK = _Block()
