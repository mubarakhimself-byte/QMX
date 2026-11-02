"""gator-oscillator@1: Bill Williams' Gator, the distance between two Alligator lines.

Each line is the smoothed moving average (MetaQuotes' SMMA) of the median price over its period,
read its shift bars late, and the value is the absolute difference of the two. The jaw and the
teeth (13 and 8 against 8 and 5) give the upper histogram, the teeth and the lips (8 and 5
against 5 and 3) the lower one, which MetaTrader draws below zero. The first value comes at
update ``max(slow_period + slow_shift, fast_period + fast_shift)``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in cast("list[object]", raw)]


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


class _Line:
    """A smoothed moving average of the median price, read ``shift`` bars late."""

    __slots__ = ("count", "level", "past", "period", "shift")

    def __init__(self, period: int, shift: int) -> None:
        self.period = period
        self.shift = shift
        self.count = 0
        self.level = 0.0
        self.past: deque[float] = deque(maxlen=shift + 1)

    def step(self, x: float) -> float | None:
        n = self.period
        self.count += 1
        if self.count < n:
            self.level += x
            return None
        if self.count == n:
            self.level = (self.level + x) / n
        else:
            self.level = (self.level * (n - 1) + x) / n
        self.past.append(self.level)
        return self.past[0] if len(self.past) == self.shift + 1 else None

    def state(self) -> list[object]:
        return [self.count, self.level.hex(), [v.hex() for v in self.past]]

    def restore(self, raw: object) -> None:
        if not isinstance(raw, list) or len(cast("list[object]", raw)) != 3:
            raise ValueError("a line's state is [count, level, past]")
        count, level, past = cast("Sequence[object]", raw)
        if not isinstance(count, int) or not isinstance(level, str):
            raise ValueError("a line's state is [count, level, past]")
        self.count, self.level = count, float.fromhex(level)
        self.past = deque(_floats(past, "a line's past"), maxlen=self.shift + 1)


class _Gator:
    __slots__ = ("_fast", "_slow")

    def __init__(self, slow: _Line, fast: _Line) -> None:
        self._slow = slow
        self._fast = fast

    @property
    def warm_up_bars(self) -> int:
        return max(line.period + line.shift for line in (self._slow, self._fast))

    @property
    def state_bound(self) -> int:
        return self._slow.shift + self._fast.shift + 4

    def retained(self) -> int:
        return len(self._slow.past) + len(self._fast.past) + 2

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low")
        if found is None:
            return None
        median = (found[0] + found[1]) / 2
        slow, fast = self._slow.step(median), self._fast.step(median)
        if slow is None or fast is None:
            return None
        return quantise(abs(slow - fast))

    def export_state(self) -> Mapping[str, object]:
        return {"slow": self._slow.state(), "fast": self._fast.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._slow.restore(state["slow"])
        self._fast.restore(state["fast"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Gator:
        slow_period, slow_shift, fast_period, fast_shift = (
            int(params[k]) for k in ("slow_period", "slow_shift", "fast_period", "fast_shift")
        )
        if min(slow_period, fast_period) < 1 or min(slow_shift, fast_shift) < 0:
            raise ValueError("gator-oscillator@1 periods must be 1+ and shifts 0+")
        return _Gator(_Line(slow_period, slow_shift), _Line(fast_period, fast_shift))


BLOCK = _Block()
