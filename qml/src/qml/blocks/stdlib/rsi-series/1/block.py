"""rsi-series@1: Wilder's Relative Strength Index of the input, from 0 to 100.

Matches TA-Lib's RSI, as ``rsi-cross-back@1`` reads it: the first value comes at update
``period + 1`` from the simple means of the first ``period`` gains and losses, then each mean
is smoothed by ``1 / period``; 0 when both means are 0.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _Rsi:
    __slots__ = ("_count", "_gain", "_last", "_loss", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._count = 0
        self._last = 0.0
        self._gain = 0.0
        self._loss = 0.0

    @property
    def warm_up_bars(self) -> int:
        return self._period + 1

    @property
    def state_bound(self) -> int:
        return 3

    def retained(self) -> int:
        return 3

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        x = float(price)
        self._count += 1
        if self._count == 1:
            self._last = x
            return None
        change = x - self._last
        self._last = x
        up, down = max(change, 0.0), max(-change, 0.0)
        n = self._period
        if self._count <= n:
            self._gain += up
            self._loss += down
            return None
        if self._count == n + 1:
            self._gain = (self._gain + up) / n
            self._loss = (self._loss + down) / n
        else:
            self._gain = (self._gain * (n - 1) + up) / n
            self._loss = (self._loss * (n - 1) + down) / n
        total = self._gain + self._loss
        return quantise(0.0 if total == 0.0 else 100.0 * self._gain / total)

    def export_state(self) -> Mapping[str, object]:
        return {
            "count": self._count,
            "last": self._last.hex(),
            "gain": self._gain.hex(),
            "loss": self._loss.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        count, last, gain, loss = state["count"], state["last"], state["gain"], state["loss"]
        if not (
            isinstance(count, int)
            and isinstance(last, str)
            and isinstance(gain, str)
            and isinstance(loss, str)
        ):
            raise ValueError("rsi-series@1 state needs count, last, gain and loss")
        self._count = count
        self._last = float.fromhex(last)
        self._gain = float.fromhex(gain)
        self._loss = float.fromhex(loss)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Rsi:
        period = int(params["period"])
        if period < 1:
            raise ValueError("rsi-series@1 period must be at least 1")
        return _Rsi(period)


BLOCK = _Block()
