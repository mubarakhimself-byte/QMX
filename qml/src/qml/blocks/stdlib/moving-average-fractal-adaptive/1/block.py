"""moving-average-fractal-adaptive@1: Ehlers' FrAMA as MetaTrader's help states it.

Over the last ``2 * period`` bars, ``N1`` is the high-low range of the newest ``period`` bars
over ``period``, ``N2`` the same for the ``period`` bars before them and ``N3`` the range of all
``2 * period`` bars over ``2 * period``. The fractal dimension ``D = (log(N1 + N2) - log(N3)) /
log(2)`` gives the factor ``A = exp(-4.6 * (D - 1))``, 1 when a range is 0, and FrAMA moves by
``A * close + (1 - A) * previous``. It starts at the close of the first full window, update
``2 * period``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

import math
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


class _Frama:
    __slots__ = ("_highs", "_level", "_lows", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._highs: deque[float] = deque(maxlen=2 * period)
        self._lows: deque[float] = deque(maxlen=2 * period)
        self._level: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return 2 * self._period

    @property
    def state_bound(self) -> int:
        return 4 * self._period + 1

    def retained(self) -> int:
        return len(self._highs) + len(self._lows) + (0 if self._level is None else 1)

    def _factor(self) -> float:
        n = self._period
        highs, lows = list(self._highs), list(self._lows)
        older = (max(highs[:n]) - min(lows[:n])) / n
        newer = (max(highs[n:]) - min(lows[n:])) / n
        whole = (max(highs) - min(lows)) / (2 * n)
        if newer + older <= 0.0 or whole <= 0.0:
            return 1.0
        dimension = (math.log(newer + older) - math.log(whole)) / math.log(2)
        return math.exp(-4.6 * (dimension - 1))

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close")
        if found is None:
            return None
        high, low, close = found
        self._highs.append(high)
        self._lows.append(low)
        if len(self._highs) < 2 * self._period:
            return None
        if self._level is None:
            self._level = close
        else:
            factor = self._factor()
            self._level = factor * close + (1 - factor) * self._level
        return quantise(self._level)

    def export_state(self) -> Mapping[str, object]:
        return {
            "highs": [v.hex() for v in self._highs],
            "lows": [v.hex() for v in self._lows],
            "level": None if self._level is None else self._level.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        level = state.get("level")
        size = 2 * self._period
        self._highs = deque(_floats(state["highs"], "its highs"), maxlen=size)
        self._lows = deque(_floats(state["lows"], "its lows"), maxlen=size)
        self._level = float.fromhex(level) if isinstance(level, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Frama:
        period = int(params["period"])
        if period < 1:
            raise ValueError("moving-average-fractal-adaptive@1 period must be at least 1")
        return _Frama(period)


BLOCK = _Block()
