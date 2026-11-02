"""relative-vigor-signal@1: the Relative Vigor Index's signal line.

The RVI (see ``relative-vigor-index@1``) weighted 1, 2, 2, 1 over its last four values. The
first value comes at update ``period + 6``.
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


def _weighted(values: Sequence[float]) -> float:
    """The newest four values weighted 1, 2, 2, 1, as MetaQuotes smooths RVI's parts."""
    return (values[3] + 2 * values[2] + 2 * values[1] + values[0]) / 6


class _Rvi:
    """The Relative Vigor Index: the weighted close-less-open summed over ``period`` bars
    divided by the weighted high-less-low summed the same way."""

    __slots__ = ("bodies", "moves", "period", "reaches", "spans")

    def __init__(self, period: int) -> None:
        self.period = period
        self.bodies: deque[float] = deque(maxlen=4)
        self.spans: deque[float] = deque(maxlen=4)
        self.moves: deque[float] = deque(maxlen=period)
        self.reaches: deque[float] = deque(maxlen=period)

    def step(self, opened: float, high: float, low: float, close: float) -> float | None:
        self.bodies.append(close - opened)
        self.spans.append(high - low)
        if len(self.bodies) < 4:
            return None
        self.moves.append(_weighted(self.bodies))
        self.reaches.append(_weighted(self.spans))
        if len(self.moves) < self.period:
            return None
        reach = sum(self.reaches)
        return None if reach == 0.0 else sum(self.moves) / reach

    def held(self) -> int:
        return len(self.bodies) + len(self.spans) + len(self.moves) + len(self.reaches)

    def state(self) -> dict[str, object]:
        return {
            name: [v.hex() for v in values]
            for name, values in (
                ("bodies", self.bodies),
                ("spans", self.spans),
                ("moves", self.moves),
                ("reaches", self.reaches),
            )
        }

    def restore(self, raw: object) -> None:
        if not isinstance(raw, Mapping):
            raise ValueError("an RVI's state is an object")
        given = cast("Mapping[str, object]", raw)
        self.bodies = deque(_floats(given["bodies"], "its bodies"), maxlen=4)
        self.spans = deque(_floats(given["spans"], "its spans"), maxlen=4)
        self.moves = deque(_floats(given["moves"], "its moves"), maxlen=self.period)
        self.reaches = deque(_floats(given["reaches"], "its reaches"), maxlen=self.period)


class _RelativeVigorSignal:
    __slots__ = ("_recent", "_rvi")

    def __init__(self, period: int) -> None:
        self._rvi = _Rvi(period)
        self._recent: deque[float] = deque(maxlen=4)

    @property
    def warm_up_bars(self) -> int:
        return self._rvi.period + 6

    @property
    def state_bound(self) -> int:
        return 2 * self._rvi.period + 12

    def retained(self) -> int:
        return self._rvi.held() + len(self._recent)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "open", "high", "low", "close")
        if found is None:
            return None
        value = self._rvi.step(*found)
        if value is None:
            self._recent.clear()
            return None
        self._recent.append(value)
        return quantise(_weighted(self._recent)) if len(self._recent) == 4 else None

    def export_state(self) -> Mapping[str, object]:
        return {"rvi": self._rvi.state(), "recent": [v.hex() for v in self._recent]}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._rvi.restore(state["rvi"])
        self._recent = deque(_floats(state["recent"], "its recent values"), maxlen=4)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _RelativeVigorSignal:
        period = int(params["period"])
        if period < 1:
            raise ValueError("relative-vigor-signal@1 period must be at least 1")
        return _RelativeVigorSignal(period)


BLOCK = _Block()
