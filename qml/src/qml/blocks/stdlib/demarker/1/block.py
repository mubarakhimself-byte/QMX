"""demarker@1: DeMark's DeMarker, from 0 to 1.

Each bar the high's rise over the previous high (0 when it did not rise) and the low's fall
under the previous low (0 when it did not fall); the value is the simple mean of the rises over
``period`` bars divided by that mean plus the mean of the falls, and missing when both are 0.
The first value comes at update ``period + 1``.
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


class _DeMarker:
    __slots__ = ("_falls", "_last", "_rises")

    def __init__(self, period: int) -> None:
        self._rises = _Sma(period)
        self._falls = _Sma(period)
        self._last: tuple[float, float] | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._rises.period + 1

    @property
    def state_bound(self) -> int:
        return 2 * self._rises.period + 2

    def retained(self) -> int:
        held = 0 if self._last is None else 2
        return len(self._rises.window) + len(self._falls.window) + held

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low")
        if found is None:
            return None
        high, low = found
        before, self._last = self._last, (high, low)
        if before is None:
            return None
        rise = self._rises.step(max(high - before[0], 0.0))
        fall = self._falls.step(max(before[1] - low, 0.0))
        if rise is None or fall is None or rise + fall == 0.0:
            return None
        return quantise(rise / (rise + fall))

    def export_state(self) -> Mapping[str, object]:
        return {
            "rises": self._rises.state(),
            "falls": self._falls.state(),
            "last": None if self._last is None else [v.hex() for v in self._last],
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        self._rises.restore(state["rises"])
        self._falls.restore(state["falls"])
        last = state.get("last")
        if last is None:
            self._last = None
        else:
            high, low = _floats(last, "demarker@1 state's last")
            self._last = (high, low)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _DeMarker:
        period = int(params["period"])
        if period < 1:
            raise ValueError("demarker@1 period must be at least 1")
        return _DeMarker(period)


BLOCK = _Block()
