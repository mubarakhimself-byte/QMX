"""aroon-up@1: Chande's Aroon Up, how recent the highest high of the last ``period + 1``
bars is, from 100 (this bar) to 0 (``period`` bars ago).

Matches TA-Lib's AROON, which counts the newest of tied highs. The first value comes at update
``period + 1``.
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


def _latest_extreme(values: Sequence[float], higher: bool) -> int:
    """The index of the newest highest (or lowest) value, as TA-Lib's AROON breaks ties."""
    best = 0
    for i, v in enumerate(values):
        if (v >= values[best]) if higher else (v <= values[best]):
            best = i
    return best


class _Aroon:
    __slots__ = ("highs", "lows", "period")

    def __init__(self, period: int) -> None:
        self.period = period
        self.highs: deque[float] = deque(maxlen=period + 1)
        self.lows: deque[float] = deque(maxlen=period + 1)

    def step(self, high: float, low: float) -> tuple[int, int] | None:
        """The positions of the newest highest high and lowest low in the window, 0 the oldest."""
        self.highs.append(high)
        self.lows.append(low)
        if len(self.highs) <= self.period:
            return None
        return _latest_extreme(self.highs, True), _latest_extreme(self.lows, False)

    def state(self) -> list[list[str]]:
        return [[v.hex() for v in self.highs], [v.hex() for v in self.lows]]

    def restore(self, raw: object) -> None:
        if not isinstance(raw, list) or len(cast("list[object]", raw)) != 2:
            raise ValueError("aroon's state is [highs, lows]")
        highs, lows = cast("Sequence[object]", raw)
        self.highs = deque(_floats(highs, "its highs"), maxlen=self.period + 1)
        self.lows = deque(_floats(lows, "its lows"), maxlen=self.period + 1)


class _AroonUp:
    __slots__ = ("_aroon",)

    def __init__(self, period: int) -> None:
        self._aroon = _Aroon(period)

    @property
    def warm_up_bars(self) -> int:
        return self._aroon.period + 1

    @property
    def state_bound(self) -> int:
        return 2 * self._aroon.period + 2

    def retained(self) -> int:
        return len(self._aroon.highs) + len(self._aroon.lows)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low")
        if found is None:
            return None
        places = self._aroon.step(*found)
        if places is None:
            return None
        high_at, _low_at = places
        n = self._aroon.period
        factor = 100.0 / n
        return quantise(factor * (n - (n - high_at)))

    def export_state(self) -> Mapping[str, object]:
        return {"aroon": self._aroon.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._aroon.restore(state["aroon"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _AroonUp:
        period = int(params["period"])
        if period < 1:
            raise ValueError("aroon-up@1 period must be at least 1")
        return _AroonUp(period)


BLOCK = _Block()
