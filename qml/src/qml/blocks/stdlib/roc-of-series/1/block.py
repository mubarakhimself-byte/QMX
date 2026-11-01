"""roc-of-series@1: rate of change of a series over ``lookback`` updates, as a fraction.

The value is ``(x_now - x_then) / x_then`` (TA-Lib's ROCP). On the long side the signal holds
when the value is at least ``floor``; mirrored on the short side, when it is at most
``-floor``. ``floor`` may move, so this instant's value in the evidence wins over the made one.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, Signal, quantise


class _Roc:
    __slots__ = ("_floor", "_lookback", "_side", "_window")

    def __init__(self, lookback: int, floor: Decimal, side: Side) -> None:
        self._lookback = lookback
        self._floor = floor
        self._side = side
        self._window: deque[Decimal] = deque(maxlen=lookback + 1)

    @property
    def warm_up_bars(self) -> int:
        return self._lookback + 1

    @property
    def state_bound(self) -> int:
        return self._lookback + 1

    def retained(self) -> int:
        return len(self._window)

    def update(self, evidence: Mapping[str, object]) -> Signal | None:
        value = evidence.get("series")
        if not isinstance(value, Decimal):
            return None
        self._window.append(value)
        if len(self._window) <= self._lookback:
            return None
        then = self._window[0]
        if then == 0:
            return None
        rate = quantise((value - then) / then)
        moved = evidence.get("floor")
        floor = moved if isinstance(moved, Decimal) else self._floor
        holds = rate >= floor if self._side is Side.LONG else rate <= -floor
        return Signal(state=holds, value=rate)

    def export_state(self) -> Mapping[str, object]:
        return {"window": [str(v) for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        window = state["window"]
        if not isinstance(window, list):
            raise ValueError("roc-of-series@1 state needs window")
        self._window.clear()
        self._window.extend(Decimal(str(v)) for v in window)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Roc:
        lookback = int(params["lookback"])
        if lookback < 1:
            raise ValueError("roc-of-series@1 lookback must be at least 1")
        return _Roc(lookback, params["floor"], side)


BLOCK = _Block()
