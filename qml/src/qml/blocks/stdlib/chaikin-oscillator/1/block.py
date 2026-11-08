"""chaikin-oscillator@1: Chaikin's oscillator, a fast EMA less a slow EMA of the A/D line.

Matches TA-Lib's ADOSC: both averages start at the first bar's A/D value and move by
``2 / (period + 1)`` every bar, and the first value comes at update ``max(fast, slow)``. On FX
and CFD bars the volume is a tick count.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in raw]


def _bar(evidence: Mapping[str, object], *names: str) -> tuple[float, ...] | None:
    """The named fields of the bar on the ``series`` port as floats, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = bar
    found = [v for v in (fields.get(name) for name in names) if isinstance(v, Decimal)]
    return tuple(float(v) for v in found) if len(found) == len(names) else None


def _ad_step(high: float, low: float, close: float, volume: float) -> float:
    """A bar's accumulation: its close location value times its volume, 0 for an empty range."""
    span = high - low
    return ((close - low) - (high - close)) / span * volume if span > 0.0 else 0.0


class _Chaikin:
    __slots__ = ("_ad", "_count", "_fast", "_fast_k", "_slow", "_slow_k", "_warm")

    def __init__(self, fast: int, slow: int) -> None:
        self._fast_k = 2.0 / (fast + 1)
        self._slow_k = 2.0 / (slow + 1)
        self._warm = max(fast, slow)
        self._count = 0
        self._ad = 0.0
        self._fast = 0.0
        self._slow = 0.0

    @property
    def warm_up_bars(self) -> int:
        return self._warm

    @property
    def state_bound(self) -> int:
        return 3

    def retained(self) -> int:
        return 3

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close", "volume")
        if found is None:
            return None
        self._ad += _ad_step(*found)
        self._count += 1
        if self._count == 1:
            self._fast = self._slow = self._ad
        else:
            self._fast = self._fast_k * self._ad + (1 - self._fast_k) * self._fast
            self._slow = self._slow_k * self._ad + (1 - self._slow_k) * self._slow
        if self._count < self._warm:
            return None
        return quantise(self._fast - self._slow)

    def export_state(self) -> Mapping[str, object]:
        return {
            "count": self._count,
            "values": [self._ad.hex(), self._fast.hex(), self._slow.hex()],
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        count = state["count"]
        if not isinstance(count, int):
            raise ValueError("chaikin-oscillator@1 state needs count")
        self._count = count
        self._ad, self._fast, self._slow = _floats(state["values"], "its values")


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Chaikin:
        fast, slow = (int(params[k]) for k in ("fast", "slow"))
        if min(fast, slow) < 1:
            raise ValueError("chaikin-oscillator@1 fast and slow must be at least 1")
        return _Chaikin(fast, slow)


BLOCK = _Block()
