"""offset-gated-trailing-stop@1: trail a fixed share below the best rate, once in profit by an offset.

freqtrade's ``trailing_stop_positive`` with ``trailing_only_offset_is_reached = True`` keeps the
configured stop until the rate reaches the entry plus ``trailing_stop_positive_offset``, then
trails ``trailing_stop_positive`` below the highest rate seen, never lowering the stop. Here the
best rate is the bar's high since the position was given (the low, mirrored, for a short); once
it is at least ``entry_price * (1 + offset)`` the stop is ``best * (1 - distance)`` for a long
and ``best * (1 + distance)`` for a short.

Before the offset is reached the level is missing: the unit's own initial stop holds. One
instance serves one position on its side. An update with no ``entry_price`` means no position
is given: the stop answers missing and forgets its best rate.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _GatedTrail:
    __slots__ = ("_best", "_distance", "_offset", "_side")

    def __init__(self, offset: Decimal, distance: Decimal, side: Side) -> None:
        self._offset, self._distance = offset, distance
        self._side = side
        self._best: Decimal | None = None

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 0 if self._best is None else 1

    def _stop(self, entry: Decimal) -> Decimal | None:
        best = self._best
        if best is None:
            return None
        if self._side is Side.LONG:
            armed = best >= entry * (1 + self._offset)
            return quantise(best * (1 - self._distance)) if armed else None
        armed = best <= entry * (1 - self._offset)
        return quantise(best * (1 + self._distance)) if armed else None

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        entry, bar = evidence.get("entry_price"), evidence.get("series")
        if not isinstance(entry, Decimal) or entry <= 0:
            self._best = None
            return None
        long = self._side is Side.LONG
        rate = bar.get("high" if long else "low") if isinstance(bar, Mapping) else None  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if isinstance(rate, Decimal) and (
            self._best is None or (rate > self._best if long else rate < self._best)
        ):
            self._best = rate
        return self._stop(entry)

    def export_state(self) -> Mapping[str, object]:
        return {"best": None if self._best is None else str(self._best)}

    def import_state(self, state: Mapping[str, object]) -> None:
        best = state.get("best")
        self._best = Decimal(best) if isinstance(best, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _GatedTrail:
        offset, distance = params["offset"], params["distance"]
        if not 0 < distance < 1 or offset < 0:
            raise ValueError("offset-gated-trailing-stop@1 needs 0 < distance < 1, offset >= 0")
        return _GatedTrail(offset, distance, side)


BLOCK = _Block()
