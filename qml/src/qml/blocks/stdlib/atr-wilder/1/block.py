"""atr-wilder@1: Wilder's average true range over ``period`` bars.

Matches TA-Lib's ATR: the first value, at update ``period + 1``, is the simple mean of the first
``period`` true ranges, and each later value is ``(previous * (period - 1) + true range) /
period``. MetaTrader's ATR draws a simple mean of the true range instead.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


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


class _Atr:
    __slots__ = ("_atr", "_count", "_last", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._count = 0
        self._atr = 0.0
        self._last: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._period + 1

    @property
    def state_bound(self) -> int:
        return 2

    def retained(self) -> int:
        return 2

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close")
        if found is None:
            return None
        high, low, close = found
        before, self._last = self._last, close
        if before is None:
            return None
        true_range = max(high, before) - min(low, before)
        n = self._period
        self._count += 1
        if self._count < n:
            self._atr += true_range
            return None
        if self._count == n:
            self._atr = (self._atr + true_range) / n
        else:
            self._atr = (self._atr * (n - 1) + true_range) / n
        return quantise(self._atr)

    def export_state(self) -> Mapping[str, object]:
        return {
            "count": self._count,
            "atr": self._atr.hex(),
            "last": None if self._last is None else self._last.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        count, atr, last = state["count"], state["atr"], state.get("last")
        if not isinstance(count, int) or not isinstance(atr, str):
            raise ValueError("atr-wilder@1 state needs count and atr")
        self._count = count
        self._atr = float.fromhex(atr)
        self._last = float.fromhex(last) if isinstance(last, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Atr:
        period = int(params["period"])
        if period < 1:
            raise ValueError("atr-wilder@1 period must be at least 1")
        return _Atr(period)


BLOCK = _Block()
