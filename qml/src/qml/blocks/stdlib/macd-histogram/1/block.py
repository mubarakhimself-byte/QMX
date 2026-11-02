"""macd-histogram@1: the MACD line less its signal line (MetaTrader's OsMA).

The MACD line is ``EMA(fast) - EMA(slow)`` of the input and the signal an EMA of the line over
``signal`` values, each EMA TA-Lib's (seeded with the simple mean of its first ``period``
inputs), so the first value comes at update ``max(fast, slow) + signal - 1``.
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


class _MacdHistogram:
    __slots__ = ("_fast", "_signal", "_slow")

    def __init__(self, fast: int, slow: int, signal: int) -> None:
        self._fast = _Ema(fast)
        self._slow = _Ema(slow)
        self._signal = _Ema(signal)

    @property
    def warm_up_bars(self) -> int:
        return max(self._fast.period, self._slow.period) + self._signal.period - 1

    @property
    def state_bound(self) -> int:
        return 3

    def retained(self) -> int:
        return 3

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        fast, slow = self._fast.step(float(price)), self._slow.step(float(price))
        if fast is None or slow is None:
            return None
        line = fast - slow
        signal = self._signal.step(line)
        if signal is None:
            return None
        return quantise(line - signal)

    def export_state(self) -> Mapping[str, object]:
        return {
            "fast": self._fast.state(),
            "slow": self._slow.state(),
            "signal": self._signal.state(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        self._fast.restore(state["fast"])
        self._slow.restore(state["slow"])
        self._signal.restore(state["signal"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _MacdHistogram:
        fast, slow, signal = (int(params[k]) for k in ("fast", "slow", "signal"))
        if min(fast, slow, signal) < 1:
            raise ValueError("macd-histogram@1 fast, slow and signal must be at least 1")
        return _MacdHistogram(fast, slow, signal)


BLOCK = _Block()
