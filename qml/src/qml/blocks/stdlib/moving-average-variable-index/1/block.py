"""moving-average-variable-index@1: Chande's VIDYA as MetaTrader draws it.

An EMA over ``ema_period`` whose factor ``2 / (ema_period + 1)`` is scaled by the absolute
Chande Momentum Oscillator (as a ratio, plain sums) over the last ``cmo_period`` changes. It
starts at the close of the first bar with a CMO, update ``cmo_period + 1``, and then moves by
``close * F * |CMO| + previous * (1 - F * |CMO|)``.
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


class _Vidya:
    __slots__ = ("_changes", "_factor", "_last", "_level", "_period")

    def __init__(self, cmo_period: int, ema_period: int) -> None:
        self._period = cmo_period
        self._factor = 2.0 / (ema_period + 1)
        self._changes: deque[float] = deque(maxlen=cmo_period)
        self._last: float | None = None
        self._level: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._period + 1

    @property
    def state_bound(self) -> int:
        return self._period + 2

    def retained(self) -> int:
        held = (self._last, self._level)
        return len(self._changes) + sum(v is not None for v in held)

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
        step = self._factor * abs(_cmo(self._changes))
        self._level = x if self._level is None else x * step + self._level * (1 - step)
        return quantise(self._level)

    def export_state(self) -> Mapping[str, object]:
        return {
            "changes": [v.hex() for v in self._changes],
            "last": None if self._last is None else self._last.hex(),
            "level": None if self._level is None else self._level.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        last, level = state.get("last"), state.get("level")
        changes = _floats(state["changes"], "moving-average-variable-index@1 changes")
        self._changes = deque(changes, maxlen=self._period)
        self._last = float.fromhex(last) if isinstance(last, str) else None
        self._level = float.fromhex(level) if isinstance(level, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Vidya:
        cmo_period, ema_period = (int(params[k]) for k in ("cmo_period", "ema_period"))
        if min(cmo_period, ema_period) < 1:
            raise ValueError(
                "moving-average-variable-index@1 cmo_period and ema_period must be at least 1"
            )
        return _Vidya(cmo_period, ema_period)


BLOCK = _Block()
