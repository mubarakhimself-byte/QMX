"""envelope-band@1: MetaTrader's Envelopes, the simple mean of the last ``period`` values
moved by the fraction ``deviation``.

``deviation`` 0.001 gives the upper band 0.1% above the mean and -0.001 the lower band. The
first value comes at update ``period``.
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


class _Envelope:
    __slots__ = ("_deviation", "_period", "_window")

    def __init__(self, period: int, deviation: float) -> None:
        self._period = period
        self._window: deque[float] = deque(maxlen=period)
        self._deviation = deviation

    @property
    def warm_up_bars(self) -> int:
        return self._period

    @property
    def state_bound(self) -> int:
        return self._period

    def retained(self) -> int:
        return len(self._window)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        self._window.append(float(price))
        if len(self._window) < self._period:
            return None
        mean = sum(self._window) / self._period
        return quantise(mean * (1 + self._deviation))

    def export_state(self) -> Mapping[str, object]:
        return {"window": [v.hex() for v in self._window]}

    def import_state(self, state: Mapping[str, object]) -> None:
        values = _floats(state["window"], "envelope-band@1 state's window")
        self._window = deque(values, maxlen=self._period)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Envelope:
        period = int(params["period"])
        if period < 1:
            raise ValueError("envelope-band@1 period must be at least 1")
        return _Envelope(period, float(params["deviation"]))


BLOCK = _Block()
