"""momentum-ratio@1: MetaTrader's Momentum, the value as a percent of the value ``period``
updates ago.

Matches TA-Lib's ROCR100: ``100 * value / value period updates ago``, 100 meaning no change.
The first value comes at update ``period + 1``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in raw]


class _Momentum:
    __slots__ = ("_period", "_window")

    def __init__(self, period: int) -> None:
        self._period = period
        self._window: deque[float] = deque(maxlen=period + 1)

    @property
    def warm_up_bars(self) -> int:
        return self._period + 1

    @property
    def state_bound(self) -> int:
        return self._period + 1

    def retained(self) -> int:
        return len(self._window)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        self._window.append(float(price))
        if len(self._window) < self._period + 1:
            return None
        then = self._window[0]
        if then == 0.0:
            return None
        return quantise(100.0 * self._window[-1] / then)

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        values = _floats(state["window"], "momentum-ratio@1 state's window")
        self._window = deque(values, maxlen=self._period + 1)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Momentum:
        period = int(params["period"])
        if period < 1:
            raise ValueError("momentum-ratio@1 period must be at least 1")
        return _Momentum(period)


BLOCK = _Block()
