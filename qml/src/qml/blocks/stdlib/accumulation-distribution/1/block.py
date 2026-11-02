"""accumulation-distribution@1: Chaikin's Accumulation/Distribution line.

Matches TA-Lib's AD: each bar adds ``((close - low) - (high - close)) / (high - low) * volume``,
nothing when the range is empty. It sums from the first bar it is given. On FX and CFD bars the
volume is a tick count.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


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


class _Ad:
    __slots__ = ("_ad",)

    def __init__(self) -> None:
        self._ad = 0.0

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 1

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close", "volume")
        if found is None:
            return None
        self._ad += _ad_step(*found)
        return quantise(self._ad)

    def export_state(self) -> Mapping[str, object]:
        return {"ad": self._ad.hex()}

    def import_state(self, state: Mapping[str, object]) -> None:
        ad = state["ad"]
        if not isinstance(ad, str):
            raise ValueError("accumulation-distribution@1 state needs ad")
        self._ad = float.fromhex(ad)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Ad:
        return _Ad()


BLOCK = _Block()
