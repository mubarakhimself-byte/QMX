"""profit-fraction-trailing-stop@1: once in profit by ``offset``, trail a share of the profit.

freqtrade's "trailing stoploss with positive offset" example keeps the initial stop until the
profit reaches 4%, then trails the stop below the current rate by half the current profit,
held between 2.5% and 5%, and never lowers it. In backtesting freqtrade reads the current rate
and profit at the candle's high (its low for a short), so here the rate is the bar's high for a
long and its low for a short, and the profit is ``(rate - entry_price) / entry_price``,
mirrored. Once armed the stop is ``rate * (1 - distance)`` for a long and
``rate * (1 + distance)`` for a short, with ``distance = share * profit`` clamped to
``min_distance`` and ``max_distance``, and it only ever moves in the trade's favour.

Before the offset is reached the level is missing: the unit's own initial stop holds. One
instance serves one position at a time on its side, and the entry price names the position: an
entry price other than the one held starts a new position with no level. An update with no
``entry_price`` means no position is given: the stop answers missing and forgets its level.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _FractionTrail:
    __slots__ = ("_ceiling", "_entry", "_floor", "_offset", "_share", "_side", "_stop")

    def __init__(
        self, offset: Decimal, share: Decimal, floor: Decimal, ceiling: Decimal, side: Side
    ) -> None:
        self._offset, self._share = offset, share
        self._floor, self._ceiling = floor, ceiling
        self._side = side
        self._entry: Decimal | None = None
        self._stop: Decimal | None = None

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 2

    def retained(self) -> int:
        return sum(held is not None for held in (self._entry, self._stop))

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        entry, bar = evidence.get("entry_price"), evidence.get("series")
        if not isinstance(entry, Decimal) or entry <= 0:
            self._entry = self._stop = None
            return None
        if entry != self._entry:
            self._entry, self._stop = entry, None
        long = self._side is Side.LONG
        rate = bar.get("high" if long else "low") if isinstance(bar, Mapping) else None  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if not isinstance(rate, Decimal):
            return self._stop
        profit = (rate - entry if long else entry - rate) / entry
        if profit < self._offset:
            return self._stop
        distance = min(self._ceiling, max(self._floor, self._share * profit))
        level = quantise(rate * (1 - distance) if long else rate * (1 + distance))
        if self._stop is None or (level > self._stop if long else level < self._stop):
            self._stop = level
        return self._stop

    def export_state(self) -> Mapping[str, object]:
        held = {"entry": self._entry, "stop": self._stop}
        return {k: None if v is None else str(v) for k, v in held.items()}

    def import_state(self, state: Mapping[str, object]) -> None:
        entry, stop = state.get("entry"), state.get("stop")
        self._entry = Decimal(entry) if isinstance(entry, str) else None
        self._stop = Decimal(stop) if isinstance(stop, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _FractionTrail:
        floor, ceiling = params["min_distance"], params["max_distance"]
        if not 0 < floor <= ceiling < 1:
            raise ValueError("profit-fraction-trailing-stop@1 needs 0 < min_distance <= max < 1")
        return _FractionTrail(params["offset"], params["share"], floor, ceiling, side)


BLOCK = _Block()
