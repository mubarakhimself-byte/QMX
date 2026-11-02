"""accelerator-oscillator@1: Bill Williams' Accelerator Oscillator.

The Awesome Oscillator (median price's simple mean over ``fast`` bars less over ``slow`` bars)
less its own simple mean over ``signal`` values. The first value comes at update
``max(fast, slow) + signal - 1``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


def _bar(evidence: Mapping[str, object], *names: str) -> tuple[float, ...] | None:
    """The named fields of the bar on the ``series`` port as floats, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = bar
    found = [v for v in (fields.get(name) for name in names) if isinstance(v, Decimal)]
    return tuple(float(v) for v in found) if len(found) == len(names) else None


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
        values = (float.fromhex(str(v)) for v in raw)
        self.window = deque(values, maxlen=self.period)


class _Accelerator:
    __slots__ = ("_fast", "_signal", "_slow")

    def __init__(self, fast: int, slow: int, signal: int) -> None:
        self._fast = _Sma(fast)
        self._slow = _Sma(slow)
        self._signal = _Sma(signal)

    @property
    def warm_up_bars(self) -> int:
        return max(self._fast.period, self._slow.period) + self._signal.period - 1

    @property
    def state_bound(self) -> int:
        return self._fast.period + self._slow.period + self._signal.period

    def retained(self) -> int:
        return sum(len(s.window) for s in (self._fast, self._slow, self._signal))

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low")
        if found is None:
            return None
        median = (found[0] + found[1]) / 2
        fast, slow = self._fast.step(median), self._slow.step(median)
        if fast is None or slow is None:
            return None
        awesome = fast - slow
        smoothed = self._signal.step(awesome)
        return None if smoothed is None else quantise(awesome - smoothed)

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
    ) -> _Accelerator:
        fast, slow, signal = (int(params[k]) for k in ("fast", "slow", "signal"))
        if min(fast, slow, signal) < 1:
            raise ValueError("accelerator-oscillator@1 fast, slow and signal must be at least 1")
        return _Accelerator(fast, slow, signal)


BLOCK = _Block()
