"""moving-average-kaufman-adaptive@1: Kaufman's adaptive moving average (MetaTrader's AMA).

Matches TA-Lib's KAMA. The efficiency ratio over the last ``period`` changes is the net change
over the sum of absolute changes, 1 when the sum is 0 or not above the net change. The smoothing
constant is ``(ratio * (2 / (fast + 1) - 2 / (slow + 1)) + 2 / (slow + 1)) ** 2``. The average
starts at the value before the first full window and the first value comes at update
``period + 1``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


class _Kama:
    __slots__ = ("_fastest", "_kama", "_period", "_slowest", "_window")

    def __init__(self, period: int, fast: int, slow: int) -> None:
        self._period = period
        self._fastest = 2.0 / (fast + 1)
        self._slowest = 2.0 / (slow + 1)
        self._window: deque[float] = deque(maxlen=period + 1)
        self._kama: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._period + 1

    @property
    def state_bound(self) -> int:
        return self._period + 2

    def retained(self) -> int:
        return len(self._window) + (0 if self._kama is None else 1)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        x = float(price)
        self._window.append(x)
        if len(self._window) <= self._period:
            return None
        values = list(self._window)
        if self._kama is None:
            self._kama = values[-2]
        path = sum(abs(values[i + 1] - values[i]) for i in range(self._period))
        net = values[-1] - values[0]
        ratio = 1.0 if path <= net or path == 0.0 else abs(net / path)
        constant = ratio * (self._fastest - self._slowest) + self._slowest
        self._kama += (x - self._kama) * constant * constant
        return quantise(self._kama)

    def export_state(self) -> Mapping[str, object]:
        return {
            "window": [v.hex() for v in self._window],
            "kama": None if self._kama is None else self._kama.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        window, kama = state["window"], state.get("kama")
        if not isinstance(window, list):
            raise ValueError("moving-average-kaufman-adaptive@1 state needs window")
        values = (float.fromhex(str(v)) for v in cast("list[object]", window))
        self._window = deque(values, maxlen=self._period + 1)
        self._kama = float.fromhex(kama) if isinstance(kama, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Kama:
        period, fast, slow = (int(params[k]) for k in ("period", "fast", "slow"))
        if min(period, fast, slow) < 1:
            raise ValueError("moving-average-kaufman-adaptive@1 period, fast and slow must be 1+")
        return _Kama(period, fast, slow)


BLOCK = _Block()
