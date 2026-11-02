"""ultimate-oscillator@1: Williams' Ultimate Oscillator, from 0 to 100.

Matches TA-Lib's ULTOSC: a bar's buying pressure is its close less the lower of its low and the
previous close, and its true range runs from that low to the higher of its high and the
previous close. Over the ``short``, ``medium`` and ``long`` windows the pressure sums are
divided by the range sums and weighted 4, 2 and 1, and the value is 100 times their sum over 7,
a window whose range sum is 0 adding nothing. The first value comes at update ``long + 1``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in cast("list[object]", raw)]


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


class _Ultimate:
    __slots__ = ("_last", "_parts", "_windows")

    def __init__(self, short: int, medium: int, long: int) -> None:
        self._windows = sorted((short, medium, long))
        self._parts: deque[tuple[float, float]] = deque(maxlen=self._windows[-1])
        self._last: float | None = None

    @property
    def warm_up_bars(self) -> int:
        return self._windows[-1] + 1

    @property
    def state_bound(self) -> int:
        return 2 * self._windows[-1] + 1

    def retained(self) -> int:
        return 2 * len(self._parts) + (0 if self._last is None else 1)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close")
        if found is None:
            return None
        high, low, close = found
        before, self._last = self._last, close
        if before is None:
            return None
        true_low = min(low, before)
        self._parts.append((close - true_low, max(high, before) - true_low))
        if len(self._parts) < self._windows[-1]:
            return None
        parts = list(self._parts)
        total = 0.0
        for weight, window in zip((4.0, 2.0, 1.0), self._windows, strict=True):
            pressure = sum(p[0] for p in parts[-window:])
            reach = sum(p[1] for p in parts[-window:])
            if reach != 0.0:
                total += weight * (pressure / reach)
        return quantise(100.0 * (total / 7.0))

    def export_state(self) -> Mapping[str, object]:
        return {
            "parts": [[a.hex(), b.hex()] for a, b in self._parts],
            "last": None if self._last is None else self._last.hex(),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        parts, last = state["parts"], state.get("last")
        if not isinstance(parts, list):
            raise ValueError("ultimate-oscillator@1 state needs parts")
        pairs = [_floats(p, "a part") for p in cast("list[object]", parts)]
        self._parts = deque(((a, b) for a, b in pairs), maxlen=self._windows[-1])
        self._last = float.fromhex(last) if isinstance(last, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Ultimate:
        short, medium, long = (int(params[k]) for k in ("short", "medium", "long"))
        if min(short, medium, long) < 1:
            raise ValueError("ultimate-oscillator@1 short, medium and long must be at least 1")
        return _Ultimate(short, medium, long)


BLOCK = _Block()
