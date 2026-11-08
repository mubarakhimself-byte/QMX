"""bulls-power@1: Elder's Bulls Power, the bar's high less the EMA of the close.

The EMA is TA-Lib's, seeded with the simple mean of its first ``period`` closes, so the first
value comes at update ``period``.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

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
        if not isinstance(raw, list) or len(raw) != 2:
            raise ValueError("an EMA's state is [count, acc]")
        count, acc = raw
        if not isinstance(count, int) or not isinstance(acc, str):
            raise ValueError("an EMA's state is [count, acc]")
        self.count, self.acc = count, float.fromhex(acc)


def _bar(evidence: Mapping[str, object], *names: str) -> tuple[float, ...] | None:
    """The named fields of the bar on the ``series`` port as floats, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = bar
    found = [v for v in (fields.get(name) for name in names) if isinstance(v, Decimal)]
    return tuple(float(v) for v in found) if len(found) == len(names) else None


class _BullsPower:
    __slots__ = ("_ema",)

    def __init__(self, period: int) -> None:
        self._ema = _Ema(period)

    @property
    def warm_up_bars(self) -> int:
        return self._ema.period

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 1

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "close")
        if found is None:
            return None
        extreme, close = found
        average = self._ema.step(close)
        if average is None:
            return None
        return quantise(extreme - average)

    def export_state(self) -> Mapping[str, object]:
        return {"ema": self._ema.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._ema.restore(state["ema"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _BullsPower:
        period = int(params["period"])
        if period < 1:
            raise ValueError("bulls-power@1 period must be at least 1")
        return _BullsPower(period)


BLOCK = _Block()
