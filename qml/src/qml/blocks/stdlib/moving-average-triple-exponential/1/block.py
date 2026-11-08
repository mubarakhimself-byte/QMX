"""moving-average-triple-exponential@1: Mulloy's TEMA, ``3 * e1 - 3 * e2 + e3``.

``e1`` is the EMA of the input, ``e2`` the EMA of ``e1`` and ``e3`` the EMA of ``e2``. Matches
TA-Lib's TEMA: each EMA is seeded with the simple mean of its first ``period`` inputs, so the
first value comes at update ``3 * period - 2``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

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
        if not isinstance(raw, list) or len(raw) != 2:
            raise ValueError("an EMA's state is [count, acc]")
        count, acc = raw
        if not isinstance(count, int) or not isinstance(acc, str):
            raise ValueError("an EMA's state is [count, acc]")
        self.count, self.acc = count, float.fromhex(acc)


class _Tema:
    __slots__ = ("_emas", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._emas = (_Ema(period), _Ema(period), _Ema(period))

    @property
    def warm_up_bars(self) -> int:
        return 3 * self._period - 2

    @property
    def state_bound(self) -> int:
        return 3

    def retained(self) -> int:
        return 3

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        e1 = self._emas[0].step(float(price))
        e2 = None if e1 is None else self._emas[1].step(e1)
        e3 = None if e2 is None else self._emas[2].step(e2)
        if e1 is None or e2 is None or e3 is None:
            return None
        return quantise(3.0 * e1 - 3.0 * e2 + e3)

    def export_state(self) -> Mapping[str, object]:
        return {"emas": [e.state() for e in self._emas]}

    def import_state(self, state: Mapping[str, object]) -> None:
        emas = state["emas"]
        if not isinstance(emas, list) or len(emas) != 3:
            raise ValueError("moving-average-triple-exponential@1 state needs three emas")
        for ema, raw in zip(self._emas, emas, strict=True):
            ema.restore(raw)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Tema:
        period = int(params["period"])
        if period < 1:
            raise ValueError("moving-average-triple-exponential@1 period must be at least 1")
        return _Tema(period)


BLOCK = _Block()
