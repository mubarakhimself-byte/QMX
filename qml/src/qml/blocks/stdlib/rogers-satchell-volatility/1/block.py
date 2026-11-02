"""rogers-satchell-volatility@1: Rogers and Satchell's volatility from the open, high, low and
close of the last ``window`` bars.

The square root of the mean of ``ln(high / close) ln(high / open) + ln(low / close) ln(low /
open)``, which stays unbiased when the price drifts. Per bar and not annualised; missing for a
bar with a price of zero or below. The first value comes at update ``window``.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


def _bar(evidence: Mapping[str, object]) -> tuple[float, float, float, float] | None:
    """The bar on the ``series`` port as open, high, low and close, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = cast("Mapping[str, object]", bar)
    found = [fields.get(name) for name in ("open", "high", "low", "close")]
    prices = [float(v) for v in found if isinstance(v, Decimal) and v > 0]
    if len(prices) != len(found):
        return None
    return prices[0], prices[1], prices[2], prices[3]


def _term(o: float, h: float, lo: float, c: float) -> float:
    return math.log(h / c) * math.log(h / o) + math.log(lo / c) * math.log(lo / o)


class _RangeVolatility:
    __slots__ = ("_terms",)

    def __init__(self, window: int) -> None:
        self._terms: deque[float] = deque(maxlen=window)

    @property
    def warm_up_bars(self) -> int:
        return self._terms.maxlen or 0

    @property
    def state_bound(self) -> int:
        return self._terms.maxlen or 0

    def retained(self) -> int:
        return len(self._terms)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence)
        if found is None:
            return None
        terms = self._terms
        terms.append(_term(*found))
        if len(terms) < (terms.maxlen or 0):
            return None
        variance = sum(terms) / len(terms)
        return quantise(math.sqrt(variance)) if variance >= 0.0 else None

    def export_state(self) -> Mapping[str, object]:
        return {"terms": [v.hex() for v in self._terms]}

    def import_state(self, state: Mapping[str, object]) -> None:
        raw = state["terms"]
        if not isinstance(raw, list):
            raise ValueError("rogers-satchell-volatility@1 state's terms is a list of hex floats")
        values = [float.fromhex(str(v)) for v in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._terms = deque(values, maxlen=self._terms.maxlen)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _RangeVolatility:
        window = int(params["window"])
        if window < 1:
            raise ValueError("rogers-satchell-volatility@1 window must be at least 1")
        return _RangeVolatility(window)


BLOCK = _Block()
