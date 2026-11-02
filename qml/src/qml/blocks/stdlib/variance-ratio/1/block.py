"""variance-ratio@1: Lo and MacKinlay's variance ratio of the last ``window`` prices at a
``horizon`` of bars.

The variance of overlapping ``horizon``-bar log returns over ``horizon`` times the variance of
one-bar log returns, both with the mean drift taken out and both de-biased, as arch's
VarianceRatio computes it with ``trend="c"`` and ``debiased=True``. About 1 for a random walk,
above 1 when moves persist, below 1 when they revert. The first value comes at update
``window``. Running sums are rebuilt from the window once every ``window`` updates.
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


class _VarianceRatio:
    __slots__ = ("_q", "_since", "_sums", "_window")

    def __init__(self, window: int, horizon: int) -> None:
        self._q = horizon
        self._window: deque[float] = deque(maxlen=window)
        self._sums = [0.0, 0.0, 0.0]
        """Sum of squared one-bar returns, sum and sum of squares of horizon returns."""
        self._since = 0

    @property
    def warm_up_bars(self) -> int:
        return self._window.maxlen or 0

    @property
    def state_bound(self) -> int:
        return self._window.maxlen or 0

    def retained(self) -> int:
        return len(self._window)

    def _rebuild(self) -> None:
        y, q = list(self._window), self._q
        ones = [y[i] - y[i - 1] for i in range(1, len(y))]
        longs = [y[i] - y[i - q] for i in range(q, len(y))]
        self._sums = [sum(r * r for r in ones), sum(longs), sum(x * x for x in longs)]
        self._since = 0

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal) or price <= 0:
            return None
        new, y, q, sums = math.log(price), self._window, self._q, self._sums
        if len(y) == y.maxlen:
            one, long = y[1] - y[0], y[q] - y[0]
            sums[0] -= one * one
            sums[1] -= long
            sums[2] -= long * long
        if y:
            one = new - y[-1]
            sums[0] += one * one
        if len(y) >= q:
            long = new - y[len(y) - q]
            sums[1] += long
            sums[2] += long * long
        y.append(new)
        self._since += 1
        if self._since >= (y.maxlen or 0):
            self._rebuild()
        if len(y) < (y.maxlen or 0):
            return None
        nq = len(y) - 1
        mu = (y[-1] - y[0]) / nq
        one_bar = (self._sums[0] - nq * mu * mu) / (nq - 1)
        spread = self._sums[2] - 2 * q * mu * self._sums[1] + (nq - q + 1) * q * q * mu * mu
        m = q * (nq - q + 1) * (1 - q / nq)
        if one_bar <= 0.0:
            return None
        return quantise((spread / m) / one_bar)

    def export_state(self) -> Mapping[str, object]:
        return {
            "window": [v.hex() for v in self._window],
            "sums": [v.hex() for v in self._sums],
            "since": self._since,
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        since = state["since"]
        if not isinstance(since, int):
            raise ValueError("variance-ratio@1 state needs since")
        self._window = deque(_floats(state["window"], "window"), maxlen=self._window.maxlen)
        self._sums = _floats(state["sums"], "variance-ratio@1 state's sums")
        self._since = since


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _VarianceRatio:
        window, horizon = int(params["window"]), int(params["horizon"])
        if horizon < 2 or window <= 2 * horizon:
            raise ValueError("variance-ratio@1 needs a horizon of at least 2 and window above 2q")
        return _VarianceRatio(window, horizon)


BLOCK = _Block()
