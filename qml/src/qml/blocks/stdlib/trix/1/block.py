"""trix@1: Hutson's TRIX, the one-bar rate of change of a triple-smoothed EMA, in percent.

``e3`` is the EMA of the EMA of the EMA of the input. Matches TA-Lib's TRIX: each EMA is seeded
with the simple mean of its first ``period`` inputs, and the value is
``100 * (e3 - previous e3) / previous e3``, so the first value comes at update
``3 * period - 1``.
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


class _Trix:
    __slots__ = ("_emas", "_last", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._emas = (_Ema(period), _Ema(period), _Ema(period))
        self._last: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return 3 * self._period - 1

    @property
    def state_bound(self) -> int:
        return 4

    def retained(self) -> int:
        return 3 if self._last is None else 4

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        e1 = self._emas[0].step(float(price))
        e2 = None if e1 is None else self._emas[1].step(e1)
        e3 = None if e2 is None else self._emas[2].step(e2)
        if e3 is None:
            return None
        before, self._last = self._last, e3
        if before is None or before == 0.0:
            return None
        return quantise(100.0 * (e3 - before) / before)

    def export_state(self) -> Mapping[str, object]:
        return {
            "emas": [e.state() for e in self._emas],
            "last": None if self._last is None else self._last.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        emas, last = state["emas"], state.get("last")
        if not isinstance(emas, list) or len(emas) != 3:
            raise ValueError("trix@1 state needs three emas")
        for ema, raw in zip(self._emas, emas, strict=True):
            ema.restore(raw)
        self._last = float.fromhex(last) if isinstance(last, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Trix:
        period = int(params["period"])
        if period < 1:
            raise ValueError("trix@1 period must be at least 1")
        return _Trix(period)


BLOCK = _Block()
