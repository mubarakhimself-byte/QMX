"""on-balance-volume@1: Granville's On Balance Volume.

Matches TA-Lib's OBV: it starts at the first bar's volume, then adds a bar's volume when the
close rose and takes it away when the close fell. It sums from the first bar it is given, so
two runs that start on different bars differ by a constant. On FX and CFD bars the volume is a
tick count.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


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


class _Obv:
    __slots__ = ("_last", "_obv")

    def __init__(self) -> None:
        self._last: float | None = None
        self._obv = 0.0

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 2

    def retained(self) -> int:
        return 0 if self._last is None else 2

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "close", "volume")
        if found is None:
            return None
        close, volume = found
        before, self._last = self._last, close
        if before is None:
            self._obv = volume
        elif close > before:
            self._obv += volume
        elif close < before:
            self._obv -= volume
        return quantise(self._obv)

    def export_state(self) -> Mapping[str, object]:
        return {"last": None if self._last is None else self._last.hex(), "obv": self._obv.hex()}

    def import_state(self, state: Mapping[str, object]) -> None:
        last, obv = state.get("last"), state["obv"]
        if not isinstance(obv, str):
            raise ValueError("on-balance-volume@1 state needs obv")
        self._last = float.fromhex(last) if isinstance(last, str) else None
        self._obv = float.fromhex(obv)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Obv:
        return _Obv()


BLOCK = _Block()
