"""percentage-price-oscillator@1: the MACD line as a percent of the slow EMA.

``100 * (EMA(fast) - EMA(slow)) / EMA(slow)``, each EMA TA-Lib's (seeded with the simple mean of
its first ``period`` inputs), so the first value comes at update ``max(fast, slow)``. TA-Lib's
own PPO starts its fast average later and differs until the seeds wash out.
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


class _Ppo:
    __slots__ = ("_fast", "_slow")

    def __init__(self, fast: int, slow: int) -> None:
        self._fast = _Ema(fast)
        self._slow = _Ema(slow)

    @property
    def warm_up_bars(self) -> int:
        return max(self._fast.period, self._slow.period)

    @property
    def state_bound(self) -> int:
        return 2

    def retained(self) -> int:
        return 2

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        fast, slow = self._fast.step(float(price)), self._slow.step(float(price))
        if fast is None or slow is None or slow == 0.0:
            return None
        return quantise((fast - slow) / slow * 100)

    def export_state(self) -> Mapping[str, object]:
        return {"fast": self._fast.state(), "slow": self._slow.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._fast.restore(state["fast"])
        self._slow.restore(state["slow"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Ppo:
        fast, slow = (int(params[k]) for k in ("fast", "slow"))
        if min(fast, slow) < 1:
            raise ValueError("percentage-price-oscillator@1 fast and slow must be at least 1")
        return _Ppo(fast, slow)


BLOCK = _Block()
