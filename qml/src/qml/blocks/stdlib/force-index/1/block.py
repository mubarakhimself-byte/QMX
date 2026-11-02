"""force-index@1: Elder's Force Index, an EMA of the close's change times the bar's volume.

The raw force of a bar is ``(close - previous close) * volume``; TA-Lib's EMA, seeded with the
simple mean of its first ``period`` raw values, smooths it, so the first value comes at update
``period + 1``. On FX and CFD bars the volume is a tick count.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


class _Ema:
    __slots__ = ("acc", "alpha", "count", "period")

    def __init__(self, period: int) -> None:
        self.period = period
        self.alpha = 2.0 / (period + 1)
        self.count = 0
        self.acc = 0.0

    def step(self, x: float) -> float | None:
        self.count += 1
        if self.count < self.period:
            self.acc += x
            return None
        if self.count == self.period:
            self.acc = (self.acc + x) / self.period
        else:
            self.acc += (x - self.acc) * self.alpha
        return self.acc

    def state(self) -> list[object]:
        return [self.count, self.acc.hex()]

    def restore(self, raw: object) -> None:
        if not isinstance(raw, list) or len(cast("list[object]", raw)) != 2:
            raise ValueError("an EMA's state is [count, acc]")
        count, acc = cast("Sequence[object]", raw)
        if not isinstance(count, int) or not isinstance(acc, str):
            raise ValueError("an EMA's state is [count, acc]")
        self.count, self.acc = count, float.fromhex(acc)


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


class _Force:
    __slots__ = ("_ema", "_last")

    def __init__(self, period: int) -> None:
        self._ema = _Ema(period)
        self._last: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._ema.period + 1

    @property
    def state_bound(self) -> int:
        return 2

    def retained(self) -> int:
        return 1 if self._last is None else 2

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "close", "volume")
        if found is None:
            return None
        close, volume = found
        before, self._last = self._last, close
        if before is None:
            return None
        smoothed = self._ema.step((close - before) * volume)
        return None if smoothed is None else quantise(smoothed)

    def export_state(self) -> Mapping[str, object]:
        return {"ema": self._ema.state(), "last": None if self._last is None else self._last.hex()}

    def import_state(self, state: Mapping[str, object]) -> None:
        last = state.get("last")
        self._ema.restore(state["ema"])
        self._last = float.fromhex(last) if isinstance(last, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Force:
        period = int(params["period"])
        if period < 1:
            raise ValueError("force-index@1 period must be at least 1")
        return _Force(period)


BLOCK = _Block()
