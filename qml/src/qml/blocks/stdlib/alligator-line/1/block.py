"""alligator-line@1: one of Bill Williams' Alligator lines.

The smoothed moving average (MetaQuotes' SMMA) of the median price ``(high + low) / 2`` over
``period`` bars, drawn ``shift`` bars ahead, so at each bar it reads the average of ``shift``
bars before. The jaw is 13 and 8, the teeth 8 and 5, the lips 5 and 3. The first value comes at
update ``period + shift``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in raw]


def _bar(evidence: Mapping[str, object], *names: str) -> tuple[float, ...] | None:
    """The named fields of the bar on the ``series`` port as floats, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = bar
    found = [v for v in (fields.get(name) for name in names) if isinstance(v, Decimal)]
    return tuple(float(v) for v in found) if len(found) == len(names) else None


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
        if not isinstance(raw, list) or len(raw) != 3:
            raise ValueError("a line's state is [count, level, past]")
        count, level, past = raw
        if not isinstance(count, int) or not isinstance(level, str):
            raise ValueError("a line's state is [count, level, past]")
        self.count, self.level = count, float.fromhex(level)
        self.past = deque(_floats(past, "a line's past"), maxlen=self.shift + 1)


class _Alligator:
    __slots__ = ("_line",)

    def __init__(self, period: int, shift: int) -> None:
        self._line = _Line(period, shift)

    @property
    def warm_up_bars(self) -> int:
        return self._line.period + self._line.shift

    @property
    def state_bound(self) -> int:
        return self._line.shift + 2

    def retained(self) -> int:
        return len(self._line.past) + 1

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low")
        if found is None:
            return None
        value = self._line.step((found[0] + found[1]) / 2)
        return None if value is None else quantise(value)

    def export_state(self) -> Mapping[str, object]:
        return {"line": self._line.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._line.restore(state["line"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Alligator:
        period, shift = int(params["period"]), int(params["shift"])
        if period < 1 or shift < 0:
            raise ValueError("alligator-line@1 period must be 1+ and shift 0+")
        return _Alligator(period, shift)


BLOCK = _Block()
