"""parabolic-sar@1: Wilder's parabolic stop and reverse.

Matches TA-Lib's SAR. The second bar picks the first side: short when its low fell further
than its high rose, long otherwise, with the stop at the first bar's low (long) or high
(short). Each bar the stop moves toward the extreme point by the acceleration factor, which
starts at ``step`` and grows by ``step`` at each new extreme up to ``maximum``; it never
enters the last two bars' range; a bar through the stop flips the side and restarts it at the
extreme point. The first value comes at update 2.
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


class _Sar:
    __slots__ = ("_af", "_ep", "_high", "_long", "_low", "_maximum", "_sar", "_seen", "_step")

    def __init__(self, step: float, maximum: float) -> None:
        self._step = min(step, maximum)
        self._maximum = maximum
        self._af = self._step
        self._seen = 0
        self._long = True
        self._sar = 0.0
        self._ep = 0.0
        self._high = 0.0
        self._low = 0.0

    @property
    def warm_up_bars(self) -> int:
        return 2

    @property
    def state_bound(self) -> int:
        return 6

    def retained(self) -> int:
        return 6

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low")
        if found is None:
            return None
        high, low = found
        if self._seen == 0:
            self._high, self._low, self._seen = high, low, 1
            return None
        if self._seen == 1:
            rise, fall = high - self._high, self._low - low
            self._long = not (fall > 0.0 and rise < fall)
            if self._long:
                self._ep, self._sar = high, self._low
            else:
                self._ep, self._sar = low, self._high
            self._high, self._low, self._seen = high, low, 2
        return quantise(self._move(high, low))

    def _move(self, high: float, low: float) -> float:
        prev_high, prev_low = self._high, self._low
        self._high, self._low = high, low
        if self._long:
            if low <= self._sar:
                self._long = False
                self._sar = max(self._ep, prev_high, high)
                out = self._sar
                self._af, self._ep = self._step, low
                self._sar = max(self._sar + self._af * (self._ep - self._sar), prev_high, high)
                return out
            out = self._sar
            if high > self._ep:
                self._ep = high
                self._af = min(self._af + self._step, self._maximum)
            self._sar = min(self._sar + self._af * (self._ep - self._sar), prev_low, low)
            return out
        if high >= self._sar:
            self._long = True
            self._sar = min(self._ep, prev_low, low)
            out = self._sar
            self._af, self._ep = self._step, high
            self._sar = min(self._sar + self._af * (self._ep - self._sar), prev_low, low)
            return out
        out = self._sar
        if low < self._ep:
            self._ep = low
            self._af = min(self._af + self._step, self._maximum)
        self._sar = max(self._sar + self._af * (self._ep - self._sar), prev_high, high)
        return out

    def export_state(self) -> Mapping[str, object]:
        return {
            "seen": self._seen,
            "long": self._long,
            "values": [v.hex() for v in (self._af, self._ep, self._sar, self._high, self._low)],
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        seen, long = state["seen"], state["long"]
        if not isinstance(seen, int) or not isinstance(long, bool):
            raise ValueError("parabolic-sar@1 state needs seen and long")
        self._seen, self._long = seen, long
        values = _floats(state["values"], "parabolic-sar@1 state's values")
        self._af, self._ep, self._sar, self._high, self._low = values


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Sar:
        return _Sar(float(params["step"]), float(params["maximum"]))


BLOCK = _Block()
