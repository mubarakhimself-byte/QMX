"""rsi-cross-back@1: Wilder's RSI, and the event of it crossing back over ``level``.

RSI matches TA-Lib's RSI: the first value comes at update ``period + 1`` from the simple means
of the first ``period`` gains and losses, then each mean is smoothed by ``1 / period``. On the
long side the event fires when RSI was below ``level`` and is now at or above it; mirrored on
the short side, when it was above and is now at or below. ``level`` may move each instant.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, Signal, quantise


class _Rsi:
    __slots__ = ("_count", "_gain", "_last", "_level", "_loss", "_period", "_previous", "_side")

    def __init__(self, period: int, level: Decimal, side: Side) -> None:
        self._period = period
        self._level = level
        self._side = side
        self._count = 0
        self._last = 0.0
        self._gain = 0.0
        self._loss = 0.0
        self._previous: Decimal | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._period + 1

    @property
    def state_bound(self) -> int:
        return 4

    def retained(self) -> int:
        return 4 if self._previous is not None else 3

    def _rsi(self) -> Decimal:
        total = self._gain + self._loss
        return quantise(0.0 if total == 0.0 else 100.0 * self._gain / total)

    def update(self, evidence: Mapping[str, object]) -> Signal | None:
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
        rsi = self._rsi()
        moved = evidence.get("level")
        level = moved if isinstance(moved, Decimal) else self._level
        before, self._previous = self._previous, rsi
        if before is None:
            return Signal(state=False, value=rsi)
        crossed = before < level <= rsi if self._side is Side.LONG else before > level >= rsi
        return Signal(state=crossed, value=rsi)

    def export_state(self) -> Mapping[str, object]:
        return {
            "count": self._count,
            "last": self._last.hex(),
            "gain": self._gain.hex(),
            "loss": self._loss.hex(),
            "previous": None if self._previous is None else str(self._previous),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        count, last, gain, loss = state["count"], state["last"], state["gain"], state["loss"]
        previous = state.get("previous")
        if not (
            isinstance(count, int)
            and isinstance(last, str)
            and isinstance(gain, str)
            and isinstance(loss, str)
        ):
            raise ValueError("rsi-cross-back@1 state needs count, last, gain and loss")
        self._count = count
        self._last = float.fromhex(last)
        self._gain = float.fromhex(gain)
        self._loss = float.fromhex(loss)
        self._previous = Decimal(previous) if isinstance(previous, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Rsi:
        period = int(params["period"])
        if period < 1:
            raise ValueError("rsi-cross-back@1 period must be at least 1")
        return _Rsi(period, params["level"], side)


BLOCK = _Block()
