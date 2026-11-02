"""awesome-oscillator@1: Bill Williams' Awesome Oscillator.

The simple mean of the bar's median price ``(high + low) / 2`` over ``fast`` bars less its
simple mean over ``slow`` bars. The first value comes at update ``max(fast, slow)``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


def _bar(evidence: Mapping[str, object], *names: str) -> tuple[float, ...] | None:
    """The named fields of the bar on the ``series`` port as floats, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = cast("Mapping[str, object]", bar)
    found = [fields.get(name) for name in names]
    if not all(isinstance(v, Decimal) for v in found):
        return None
    return tuple(float(cast("Decimal", v)) for v in found)


class _Sma:
    __slots__ = ("period", "window")

    def __init__(self, period: int) -> None:
        self.period = period
        self.window: deque[float] = deque(maxlen=period)

    def step(self, x: float) -> float | None:
        self.window.append(x)
        if len(self.window) < self.period:
            return None
        return sum(self.window) / self.period

    def state(self) -> list[str]:
        return [v.hex() for v in self.window]

    def restore(self, raw: object) -> None:
        if not isinstance(raw, list):
            raise ValueError("an SMA's state is its window")
        values = (float.fromhex(str(v)) for v in cast("list[object]", raw))
        self.window = deque(values, maxlen=self.period)


class _Awesome:
    __slots__ = ("_fast", "_slow")

    def __init__(self, fast: int, slow: int) -> None:
        self._fast = _Sma(fast)
        self._slow = _Sma(slow)

    @property
    def warm_up_bars(self) -> int:
        return max(self._fast.period, self._slow.period)

    @property
    def state_bound(self) -> int:
        return self._fast.period + self._slow.period

    def retained(self) -> int:
        return len(self._fast.window) + len(self._slow.window)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low")
        if found is None:
            return None
        median = (found[0] + found[1]) / 2
        fast, slow = self._fast.step(median), self._slow.step(median)
        if fast is None or slow is None:
            return None
        return quantise(fast - slow)

    def export_state(self) -> Mapping[str, object]:
        return {"fast": self._fast.state(), "slow": self._slow.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._fast.restore(state["fast"])
        self._slow.restore(state["slow"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Awesome:
        fast, slow = (int(params[k]) for k in ("fast", "slow"))
        if min(fast, slow) < 1:
            raise ValueError("awesome-oscillator@1 fast and slow must be at least 1")
        return _Awesome(fast, slow)


BLOCK = _Block()
