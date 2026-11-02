"""bar-true-range@1: Wilder's true range of a bar.

Matches TA-Lib's TRANGE: the larger of the bar's high and the previous close less the smaller
of its low and the previous close. The first bar has no previous close, so the first value
comes at update 2.
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


class _TrueRange:
    __slots__ = ("_last",)

    def __init__(self) -> None:
        self._last: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return 2

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 0 if self._last is None else 1

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close")
        if found is None:
            return None
        high, low, close = found
        before, self._last = self._last, close
        if before is None:
            return None
        return quantise(max(high, before) - min(low, before))

    def export_state(self) -> Mapping[str, object]:
        return {"last": None if self._last is None else self._last.hex()}

    def import_state(self, state: Mapping[str, object]) -> None:
        last = state.get("last")
        self._last = float.fromhex(last) if isinstance(last, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _TrueRange:
        return _TrueRange()


BLOCK = _Block()
