"""heikin-ashi-open@1: the Heikin-Ashi candle's open.

The mean of the previous Heikin-Ashi open and close; on the first bar, the mean of its own open
and close. The first bar's seed fades as each later open halves the distance to the candles.
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


class _HeikinAshi:
    """Heikin-Ashi's open and close: the close is the bar's mean of open, high, low and close;
    the open is the mean of the previous Heikin-Ashi open and close, and on the first bar the
    mean of its own open and close."""

    __slots__ = ("close", "open")

    def __init__(self) -> None:
        self.open: float | None = None
        self.close = 0.0

    def step(self, opened: float, high: float, low: float, close: float) -> tuple[float, float]:
        ha_close = (opened + high + low + close) / 4
        ha_open = (opened + close) / 2 if self.open is None else (self.open + self.close) / 2
        self.open, self.close = ha_open, ha_close
        return ha_open, ha_close

    def state(self) -> list[str] | None:
        return None if self.open is None else [self.open.hex(), self.close.hex()]

    def restore(self, raw: object) -> None:
        if raw is None:
            self.open = None
            return
        self.open, self.close = _floats(raw, "Heikin-Ashi's state")


class _HeikinAshiOpen:
    __slots__ = ("_ha",)

    def __init__(self) -> None:
        self._ha = _HeikinAshi()

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 2

    def retained(self) -> int:
        return 0 if self._ha.open is None else 2

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "open", "high", "low", "close")
        if found is None:
            return None
        return quantise(self._ha.step(*found)[0])

    def export_state(self) -> Mapping[str, object]:
        return {"ha": self._ha.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._ha.restore(state.get("ha"))


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _HeikinAshiOpen:
        return _HeikinAshiOpen()


BLOCK = _Block()
