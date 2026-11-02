"""dickey-fuller-statistic@1: the augmented Dickey-Fuller t-statistic of the last ``window``
prices, with ``lags`` lagged changes and a constant.

Each bar's change is regressed on the price before it, the ``lags`` changes before it and a
constant, as statsmodels' adfuller does with ``regression="c"`` and ``autolag=None``; the value
is the slope on the price over its standard error. The more negative, the stronger the pull back
to a mean. The regression is solved on centred columns, which gives the same slope and residuals
as the constant. The first value comes at update ``window``.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping, Sequence
from decimal import Decimal

from qml.blocks.api import Side, quantise


def _inverse(matrix: list[list[float]]) -> list[list[float]] | None:
    """Gauss-Jordan with partial pivoting; None for a singular matrix."""
    n = len(matrix)
    work = [[*row, *(1.0 if i == j else 0.0 for j in range(n))] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(work[r][col]))
        if work[pivot][col] == 0.0:
            return None
        work[col], work[pivot] = work[pivot], work[col]
        lead = work[col][col]
        work[col] = [v / lead for v in work[col]]
        for r in range(n):
            if r != col and work[r][col] != 0.0:
                factor = work[r][col]
                work[r] = [a - factor * b for a, b in zip(work[r], work[col], strict=True)]
    return [row[n:] for row in work]


def _centred(values: Sequence[float]) -> list[float]:
    mean = sum(values) / len(values)
    return [v - mean for v in values]


class _DickeyFuller:
    __slots__ = ("_lags", "_window")

    def __init__(self, window: int, lags: int) -> None:
        self._lags = lags
        self._window: deque[float] = deque(maxlen=window)

    @property
    def warm_up_bars(self) -> int:
        return self._window.maxlen or 0

    @property
    def state_bound(self) -> int:
        return self._window.maxlen or 0

    def retained(self) -> int:
        return len(self._window)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        prices = self._window
        prices.append(float(price))
        if len(prices) < (prices.maxlen or 0):
            return None
        k = self._lags
        moves = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
        rows = range(k, len(moves))
        z = _centred([moves[t] for t in rows])
        columns = [_centred([prices[t] for t in rows])]
        columns += [_centred([moves[t - j] for t in rows]) for j in range(1, k + 1)]
        p = len(columns)
        gram = [
            [sum(a * b for a, b in zip(ci, cj, strict=True)) for cj in columns] for ci in columns
        ]
        inverse = _inverse(gram)
        free = len(z) - p - 1
        if inverse is None or free < 1:
            return None
        xz = [sum(a * b for a, b in zip(c, z, strict=True)) for c in columns]
        beta = [sum(inverse[i][j] * xz[j] for j in range(p)) for i in range(p)]
        residuals = [z[t] - sum(beta[i] * columns[i][t] for i in range(p)) for t in range(len(z))]
        scale = sum(r * r for r in residuals) / free
        if scale <= 0.0 or inverse[0][0] <= 0.0:
            return None
        return quantise(beta[0] / math.sqrt(scale * inverse[0][0]))

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        raw = state["window"]
        if not isinstance(raw, list):
            raise ValueError("dickey-fuller-statistic@1 state's window is a list of hex floats")
        values = [float.fromhex(str(v)) for v in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._window = deque(values, maxlen=self._window.maxlen)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _DickeyFuller:
        window, lags = int(params["window"]), int(params["lags"])
        if lags < 0 or window < lags + 5:
            raise ValueError(
                "dickey-fuller-statistic@1 needs lags of 0 or more and window lags + 5"
            )
        return _DickeyFuller(window, lags)


BLOCK = _Block()
