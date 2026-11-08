"""chande-momentum-oscillator@1: Chande's Momentum Oscillator, from -100 to 100.

100 times the sum of the rises less the sum of the falls of the last ``period`` changes, over
their total, 0 when nothing moved. These are plain sums, as Chande and MetaTrader's VIDYA use
them; TA-Lib's CMO smooths them as Wilder does. The first value comes at update ``period + 1``.
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


def _cmo(changes: deque[float]) -> float:
    """Chande's ratio of the summed rises less the summed falls over their total, 0 when flat."""
    up = sum(x for x in changes if x > 0.0)
    down = sum(-x for x in changes if x < 0.0)
    return 0.0 if up + down == 0.0 else (up - down) / (up + down)


class _Cmo:
    __slots__ = ("_changes", "_last", "_period")

    def __init__(self, period: int) -> None:
        self._period = period
        self._changes: deque[float] = deque(maxlen=period)
        self._last: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._period + 1

    @property
    def state_bound(self) -> int:
        return self._period + 1

    def retained(self) -> int:
        return len(self._changes) + (0 if self._last is None else 1)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        x = float(price)
        before, self._last = self._last, x
        if before is None:
            return None
        self._changes.append(x - before)
        if len(self._changes) < self._period:
            return None
        return quantise(100 * _cmo(self._changes))

    def export_state(self) -> Mapping[str, object]:
        return {
            "changes": [v.hex() for v in self._changes],
            "last": None if self._last is None else self._last.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        last = state.get("last")
        changes = _floats(state["changes"], "chande-momentum-oscillator@1 changes")
        self._changes = deque(changes, maxlen=self._period)
        self._last = float.fromhex(last) if isinstance(last, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Cmo:
        period = int(params["period"])
        if period < 1:
            raise ValueError("chande-momentum-oscillator@1 period must be at least 1")
        return _Cmo(period)


BLOCK = _Block()
