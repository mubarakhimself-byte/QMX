"""stochastic-d@1: Lane's stochastic %D, the simple mean of %K over ``d_period`` values.

%K is the raw stochastic over ``k_period`` bars slowed by a simple mean over ``slowing``
values (see ``stochastic-k@1``), as TA-Lib's STOCH draws its slow %D. The first value comes at
update ``k_period + slowing + d_period - 2``.
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


class _FastK:
    """The stochastic's raw line as TA-Lib's STOCHF draws it: ``(close - lowest low) / ((highest
    high - lowest low) / 100)`` over ``period`` bars, 0 when the range is empty."""

    __slots__ = ("highs", "lows", "period")

    def __init__(self, period: int) -> None:
        self.period = period
        self.highs: deque[float] = deque(maxlen=period)
        self.lows: deque[float] = deque(maxlen=period)

    def step(self, high: float, low: float, close: float) -> float | None:
        self.highs.append(high)
        self.lows.append(low)
        if len(self.highs) < self.period:
            return None
        lowest = min(self.lows)
        span = (max(self.highs) - lowest) / 100.0
        return (close - lowest) / span if span != 0.0 else 0.0

    def state(self) -> list[list[str]]:
        return [[v.hex() for v in self.highs], [v.hex() for v in self.lows]]

    def restore(self, raw: object) -> None:
        if not isinstance(raw, list) or len(cast("list[object]", raw)) != 2:
            raise ValueError("the raw stochastic's state is [highs, lows]")
        highs, lows = cast("Sequence[object]", raw)
        self.highs = deque(_floats(highs, "its highs"), maxlen=self.period)
        self.lows = deque(_floats(lows, "its lows"), maxlen=self.period)


class _StochasticD:
    __slots__ = ("_d", "_raw", "_slow")

    def __init__(self, k_period: int, slowing: int, d_period: int) -> None:
        self._raw = _FastK(k_period)
        self._slow = _Sma(slowing)
        self._d = _Sma(d_period)

    @property
    def warm_up_bars(self) -> int:
        return self._raw.period + self._slow.period + self._d.period - 2

    @property
    def state_bound(self) -> int:
        return 2 * self._raw.period + self._slow.period + self._d.period

    def retained(self) -> int:
        held = len(self._raw.highs) + len(self._raw.lows)
        return held + len(self._slow.window) + len(self._d.window)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close")
        if found is None:
            return None
        raw = self._raw.step(*found)
        k = None if raw is None else self._slow.step(raw)
        d = None if k is None else self._d.step(k)
        return None if d is None else quantise(d)

    def export_state(self) -> Mapping[str, object]:
        return {"raw": self._raw.state(), "slow": self._slow.state(), "d": self._d.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._raw.restore(state["raw"])
        self._slow.restore(state["slow"])
        self._d.restore(state["d"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _StochasticD:
        k_period, slowing, d_period = (int(params[k]) for k in ("k_period", "slowing", "d_period"))
        if min(k_period, slowing, d_period) < 1:
            raise ValueError("stochastic-d@1 k_period, slowing and d_period must be at least 1")
        return _StochasticD(k_period, slowing, d_period)


BLOCK = _Block()
