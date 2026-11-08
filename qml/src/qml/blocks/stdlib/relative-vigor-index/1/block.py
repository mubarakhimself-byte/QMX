"""relative-vigor-index@1: the Relative Vigor Index of MetaTrader.

Each bar's close less open and high less low are weighted 1, 2, 2, 1 over the last four bars;
the value is the first summed over ``period`` bars divided by the second summed the same way,
missing when that sum is 0. The first value comes at update ``period + 3``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
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
        given = raw
        self.bodies = deque(_floats(given["bodies"], "its bodies"), maxlen=4)
        self.spans = deque(_floats(given["spans"], "its spans"), maxlen=4)
        self.moves = deque(_floats(given["moves"], "its moves"), maxlen=self.period)
        self.reaches = deque(_floats(given["reaches"], "its reaches"), maxlen=self.period)


class _RelativeVigor:
    __slots__ = ("_rvi",)

    def __init__(self, period: int) -> None:
        self._rvi = _Rvi(period)

    @property
    def warm_up_bars(self) -> int:
        return self._rvi.period + 3

    @property
    def state_bound(self) -> int:
        return 2 * self._rvi.period + 8

    def retained(self) -> int:
        return self._rvi.held()

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "open", "high", "low", "close")
        if found is None:
            return None
        value = self._rvi.step(*found)
        return None if value is None else quantise(value)

    def export_state(self) -> Mapping[str, object]:
        return {"rvi": self._rvi.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._rvi.restore(state["rvi"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _RelativeVigor:
        period = int(params["period"])
        if period < 1:
            raise ValueError("relative-vigor-index@1 period must be at least 1")
        return _RelativeVigor(period)


BLOCK = _Block()
