"""fractal-low-level@1: the low of the last confirmed Williams down fractal.

A down fractal is a bar whose low is below the lows of the two bars before it and the two
after it, so it is known two bars late. The value is missing until the first one confirms.
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


def _bar(evidence: Mapping[str, object], *names: str) -> tuple[float, ...] | None:
    """The named fields of the bar on the ``series`` port as floats, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = bar
    found = [v for v in (fields.get(name) for name in names) if isinstance(v, Decimal)]
    return tuple(float(v) for v in found) if len(found) == len(names) else None


class _FractalLow:
    __slots__ = ("_last", "_window")

    def __init__(self) -> None:
        self._window: deque[float] = deque(maxlen=5)
        self._last: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return 5

    @property
    def state_bound(self) -> int:
        return 6

    def retained(self) -> int:
        return len(self._window) + (0 if self._last is None else 1)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "low")
        if found is None:
            return None
        self._window.append(found[0])
        if len(self._window) == 5:
            middle = self._window[2]
            sides = (self._window[0], self._window[1], self._window[3], self._window[4])
            if all(middle < side for side in sides):
                self._last = middle
        return None if self._last is None else quantise(self._last)

    def export_state(self) -> Mapping[str, object]:
        return {
            "window": [v.hex() for v in self._window],
            "last": None if self._last is None else self._last.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        last = state.get("last")
        self._window = deque(_floats(state["window"], "fractal-low-level@1 window"), maxlen=5)
        self._last = float.fromhex(last) if isinstance(last, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _FractalLow:
        return _FractalLow()


BLOCK = _Block()
