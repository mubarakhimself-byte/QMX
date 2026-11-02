"""plus-directional-indicator@1: Wilder's +DI over ``period`` bars, from 0 to 100.

Matches TA-Lib's PLUS_DI: a bar's upward move is its high's rise when that is above 0 and above
its low's fall, and +DI is 100 times the Wilder-smoothed upward moves over the smoothed true
ranges, 0 while the true ranges are 0. The first value comes at update ``period + 1``.
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


class _Directional:
    """Wilder's directional movement as TA-Lib keeps it: the first ``period - 1`` moves and true
    ranges are summed, and each later one is folded in as ``total - total / period + new``."""

    __slots__ = ("last", "minus", "moves", "period", "plus", "ranges")

    def __init__(self, period: int) -> None:
        self.period = period
        self.moves = 0
        self.last: tuple[float, float, float] | None = None
        self.plus = 0.0
        self.minus = 0.0
        self.ranges = 0.0

    def step(self, high: float, low: float, close: float) -> bool:
        """Take one bar; True once the totals are Wilder-smoothed."""
        before, self.last = self.last, (high, low, close)
        if before is None:
            return False
        up, down = high - before[0], before[1] - low
        plus = up if up > 0.0 and up > down else 0.0
        minus = down if down > 0.0 and up < down else 0.0
        true_range = max(high, before[2]) - min(low, before[2])
        self.moves += 1
        if self.moves < self.period:
            self.plus += plus
            self.minus += minus
            self.ranges += true_range
            return False
        n = self.period
        self.plus = self.plus - self.plus / n + plus
        self.minus = self.minus - self.minus / n + minus
        self.ranges = self.ranges - self.ranges / n + true_range
        return True

    def indicators(self) -> tuple[float, float]:
        """+DI and -DI, both 0 while the true range total is 0."""
        if self.ranges == 0.0:
            return 0.0, 0.0
        return 100.0 * (self.plus / self.ranges), 100.0 * (self.minus / self.ranges)

    def state(self) -> dict[str, object]:
        return {
            "moves": self.moves,
            "last": None if self.last is None else [v.hex() for v in self.last],
            "totals": [v.hex() for v in (self.plus, self.minus, self.ranges)],
        }

    def restore(self, raw: object) -> None:
        if not isinstance(raw, Mapping):
            raise ValueError("directional movement's state is an object")
        given = raw
        moves, last = given["moves"], given.get("last")
        if not isinstance(moves, int):
            raise ValueError("directional movement's state needs moves")
        self.moves = moves
        if last is None:
            self.last = None
        else:
            high, low, close = _floats(last, "its last bar")
            self.last = (high, low, close)
        self.plus, self.minus, self.ranges = _floats(given["totals"], "its totals")


class _PlusDi:
    __slots__ = ("_dm",)

    def __init__(self, period: int) -> None:
        self._dm = _Directional(period)

    @property
    def warm_up_bars(self) -> int:
        return self._dm.period + 1

    @property
    def state_bound(self) -> int:
        return 6

    def retained(self) -> int:
        return 6

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close")
        if found is None or not self._dm.step(*found):
            return None
        return quantise(self._dm.indicators()[0])

    def export_state(self) -> Mapping[str, object]:
        return {"dm": self._dm.state()}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._dm.restore(state["dm"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _PlusDi:
        period = int(params["period"])
        if period < 1:
            raise ValueError("plus-directional-indicator@1 period must be at least 1")
        return _PlusDi(period)


BLOCK = _Block()
