"""atr-simple@1: MetaTrader's average true range, the simple mean of the last ``period``
true ranges.

The true range is the higher of the bar's high and the previous close less the lower of its low
and the previous close. The first value comes at update ``period + 1``. Wilder's smoothed form
is ``atr-wilder@1``.
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


class _AtrSimple:
    __slots__ = ("_last", "_mean")

    def __init__(self, period: int) -> None:
        self._mean = _Sma(period)
        self._last: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._mean.period + 1

    @property
    def state_bound(self) -> int:
        return self._mean.period + 1

    def retained(self) -> int:
        return len(self._mean.window) + (0 if self._last is None else 1)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close")
        if found is None:
            return None
        high, low, close = found
        before, self._last = self._last, close
        if before is None:
            return None
        mean = self._mean.step(max(high, before) - min(low, before))
        return None if mean is None else quantise(mean)

    def export_state(self) -> Mapping[str, object]:
        return {
            "mean": self._mean.state(),
            "last": None if self._last is None else self._last.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        last = state.get("last")
        self._mean.restore(state["mean"])
        self._last = float.fromhex(last) if isinstance(last, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _AtrSimple:
        period = int(params["period"])
        if period < 1:
            raise ValueError("atr-simple@1 period must be at least 1")
        return _AtrSimple(period)


BLOCK = _Block()
