"""market-facilitation-index@1: Bill Williams' Market Facilitation Index.

The bar's range ``high - low`` divided by its volume, missing when the volume is 0. On FX and
CFD bars the volume is a tick count, so the value is the price move per tick.
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


class _Bwmfi:
    __slots__ = ()

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "volume")
        if found is None or found[2] == 0.0:
            return None
        return quantise((found[0] - found[1]) / found[2])

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Bwmfi:
        return _Bwmfi()


BLOCK = _Block()
