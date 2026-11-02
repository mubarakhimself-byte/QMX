"""close-to-close-volatility@1: the sample standard deviation of the last ``window`` log returns
from close to close, per bar and not annualised.

The first value comes at update ``window + 1``.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _CloseToClose:
    __slots__ = ("_logs",)

    def __init__(self, window: int) -> None:
        self._logs: deque[float] = deque(maxlen=window + 1)

    @property
    def warm_up_bars(self) -> int:
        return self._logs.maxlen or 0

    @property
    def state_bound(self) -> int:
        return self._logs.maxlen or 0

    def retained(self) -> int:
        return len(self._logs)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal) or price <= 0:
            return None
        logs = self._logs
        logs.append(math.log(price))
        if len(logs) < (logs.maxlen or 0):
            return None
        returns = [logs[i] - logs[i - 1] for i in range(1, len(logs))]
        mean = sum(returns) / len(returns)
        return quantise(math.sqrt(sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)))

    def export_state(self) -> Mapping[str, object]:
        return {"logs": [v.hex() for v in self._logs]}

    def import_state(self, state: Mapping[str, object]) -> None:
        raw = state["logs"]
        if not isinstance(raw, list):
            raise ValueError("close-to-close-volatility@1 state's logs is a list of hex floats")
        values = [float.fromhex(str(v)) for v in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._logs = deque(values, maxlen=self._logs.maxlen)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _CloseToClose:
        window = int(params["window"])
        if window < 2:
            raise ValueError("close-to-close-volatility@1 window must be at least 2")
        return _CloseToClose(window)


BLOCK = _Block()
