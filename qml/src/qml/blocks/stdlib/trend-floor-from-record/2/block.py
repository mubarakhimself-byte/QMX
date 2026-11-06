"""trend-floor-from-record@2: the slow rule that moves the dummy's ``min_trend_strength``.

Given the unit's closed trades, each with the trend strength stamped at entry and its R after
costs: once at least ``min_count`` have closed, bucket them by the size of their strength into
``buckets`` equal buckets over the number's range, so a short, whose stamp is negative, reads as
its long mirror does (``@1`` clamped it into the lowest bucket); find the lowest bucket edge
above which every bucket that holds a trade has a mean R of at least zero; shrink that edge
toward the number's default by
n / (n + ``shrink_k``); and move the number at most ``step_limit`` steps toward it, inside its
range. The motion engine decides when it runs (the cadence); this block only answers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from fractions import Fraction
from math import floor

from qml.blocks.api import Side


class _TrendFloor:
    __slots__ = (
        "_buckets",
        "_default",
        "_high",
        "_k",
        "_low",
        "_min_count",
        "_step",
        "_step_limit",
    )

    def __init__(self, params: Mapping[str, Decimal]) -> None:
        self._buckets = int(params["buckets"])
        self._min_count = int(params["min_count"])
        self._k = int(params["shrink_k"])
        self._step_limit = int(params["step_limit"])
        self._low, self._high, self._step = params["min"], params["max"], params["step"]
        self._default = params["default"]

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def _edge(self, trades: Sequence[tuple[Decimal, Decimal]]) -> Fraction:
        low, width = (
            Fraction(self._low),
            (Fraction(self._high) - Fraction(self._low)) / self._buckets,
        )
        sums: dict[int, Fraction] = {}
        for strength, r in trades:
            index = min(self._buckets - 1, max(0, floor((abs(Fraction(strength)) - low) / width)))
            sums[index] = sums.get(index, Fraction(0)) + Fraction(r)
        lowest = self._buckets
        for edge in range(self._buckets - 1, -1, -1):
            if sums.get(edge, Fraction(0)) < 0:
                break
            lowest = edge
        return low + width * lowest

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        raw, current = evidence.get("trades"), evidence.get("current")
        if not isinstance(raw, Sequence) or not isinstance(current, Decimal):
            return None
        trades: list[tuple[Decimal, Decimal]] = []
        for item in raw:  # pyright: ignore[reportUnknownVariableType]
            if not isinstance(item, Mapping):
                return None
            strength, r = item.get("strength"), item.get("r")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            if not isinstance(strength, Decimal) or not isinstance(r, Decimal):
                return None
            trades.append((strength, r))
        n = len(trades)
        if n < self._min_count:
            return None
        default = Fraction(self._default)
        target = default + (self._edge(trades) - default) * Fraction(n, n + self._k)
        gap = target - Fraction(current)
        steps = min(self._step_limit, floor(abs(gap) / Fraction(self._step)))
        moved = current + (steps if gap > 0 else -steps) * self._step
        return min(self._high, max(self._low, moved))

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _TrendFloor:
        return _TrendFloor(params)


BLOCK = _Block()
