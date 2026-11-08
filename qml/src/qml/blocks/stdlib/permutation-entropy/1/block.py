"""permutation-entropy@1: Bandt and Pompe's permutation entropy of the last ``window`` prices.

Each run of ``order`` consecutive prices has an ordinal pattern, the order its values rank in;
a tie keeps the earlier value first. The value is the Shannon entropy of how often each pattern
occurs in the window, divided by ``ln(order!)`` so it runs from 0 (one pattern only) to 1 (every
pattern equally often). The first value comes at update ``window``.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping, Sequence
from decimal import Decimal

from qml.blocks.api import Side, quantise


def _pattern(values: Sequence[float]) -> tuple[int, ...]:
    return tuple(sorted(range(len(values)), key=lambda i: values[i]))


class _PermutationEntropy:
    __slots__ = ("_counts", "_order", "_patterns", "_window")

    def __init__(self, window: int, order: int) -> None:
        self._order = order
        self._window: deque[float] = deque(maxlen=window)
        self._patterns: deque[tuple[int, ...]] = deque(maxlen=window - order + 1)
        self._counts: dict[tuple[int, ...], int] = {}

    @property
    def warm_up_bars(self) -> int:
        return self._window.maxlen or 0

    @property
    def state_bound(self) -> int:
        return 2 * (self._window.maxlen or 0)

    def retained(self) -> int:
        return len(self._window) + len(self._patterns)

    def _take(self, value: float) -> None:
        self._window.append(value)
        if len(self._window) < self._order:
            return
        patterns, counts = self._patterns, self._counts
        if len(patterns) == patterns.maxlen:
            gone = patterns[0]
            counts[gone] -= 1
            if counts[gone] == 0:
                del counts[gone]
        new = _pattern(list(self._window)[-self._order :])
        patterns.append(new)
        counts[new] = counts.get(new, 0) + 1

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        self._take(float(price))
        if len(self._window) < (self._window.maxlen or 0):
            return None
        total = len(self._patterns)
        shares = [self._counts[key] / total for key in sorted(self._counts)]
        h = -sum(share * math.log(share) for share in shares)
        return quantise(h / math.log(math.factorial(self._order)))

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        raw = state["window"]
        if not isinstance(raw, list):
            raise ValueError("permutation-entropy@1 state's window is a list of hex floats")
        values = [float.fromhex(str(v)) for v in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._window = deque(maxlen=self._window.maxlen)
        self._patterns = deque(maxlen=self._patterns.maxlen)
        self._counts = {}
        for value in values:
            self._take(value)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _PermutationEntropy:
        window, order = int(params["window"]), int(params["order"])
        if order < 2 or window < order + 1:
            raise ValueError("permutation-entropy@1 needs order 2 or more and window above it")
        return _PermutationEntropy(window, order)


BLOCK = _Block()
