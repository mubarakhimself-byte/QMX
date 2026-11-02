"""money-flow-index@1: the Money Flow Index, a volume-weighted RSI from 0 to 100.

Matches TA-Lib's MFI: a bar's money flow is its typical price ``(high + low + close) / 3`` times
its volume, counted as positive when the typical price rose and negative when it fell; the
value is 100 times the positive flow over ``period`` bars divided by all the flow, and 0 when
the flow is below 1. The first value comes at update ``period + 1``. On FX and CFD bars the
volume is a tick count.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in cast("list[object]", raw)]


def _bar(evidence: Mapping[str, object], *names: str) -> tuple[float, ...] | None:
    """The named fields of the bar on the ``series`` port as floats, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = cast("Mapping[str, object]", bar)
    found = [fields.get(name) for name in names]
    if not all(isinstance(v, Decimal) for v in found):
        return None
    return tuple(float(cast("Decimal", v)) for v in found)


class _Mfi:
    __slots__ = ("_flows", "_last", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._flows: deque[tuple[float, float]] = deque(maxlen=period)
        self._last: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._period + 1

    @property
    def state_bound(self) -> int:
        return 2 * self._period + 1

    def retained(self) -> int:
        return 2 * len(self._flows) + (0 if self._last is None else 1)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close", "volume")
        if found is None:
            return None
        high, low, close, volume = found
        typical = (high + low + close) / 3
        before, self._last = self._last, typical
        if before is None:
            return None
        flow = typical * volume
        up = flow if typical > before else 0.0
        down = flow if typical < before else 0.0
        self._flows.append((up, down))
        if len(self._flows) < self._period:
            return None
        positive = sum(f[0] for f in self._flows)
        total = positive + sum(f[1] for f in self._flows)
        return quantise(0.0 if total < 1.0 else 100.0 * (positive / total))

    def export_state(self) -> Mapping[str, object]:
        return {
            "flows": [[u.hex(), d.hex()] for u, d in self._flows],
            "last": None if self._last is None else self._last.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        flows, last = state["flows"], state.get("last")
        if not isinstance(flows, list):
            raise ValueError("money-flow-index@1 state needs flows")
        pairs = [_floats(f, "a flow") for f in cast("list[object]", flows)]
        self._flows = deque(((u, d) for u, d in pairs), maxlen=self._period)
        self._last = float.fromhex(last) if isinstance(last, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Mfi:
        period = int(params["period"])
        if period < 1:
            raise ValueError("money-flow-index@1 period must be at least 1")
        return _Mfi(period)


BLOCK = _Block()
