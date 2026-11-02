"""adx@1: Wilder's Average Directional Index over ``period`` bars, from 0 to 100.

Matches TA-Lib's ADX: each bar's DX is ``100 * |+DI - -DI| / (+DI + -DI)`` (skipped while the
sum is 0); the first ADX is the mean of the first ``period`` DX values and each later one is
``(previous * (period - 1) + DX) / period``. The first value comes at update ``2 * period``.
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


class _Adx:
    __slots__ = ("_adx", "_dm", "_smoothed")

    def __init__(self, period: int) -> None:
        self._dm = _Directional(period)
        self._smoothed = 0
        self._adx = 0.0

    @property
    def warm_up_bars(self) -> int:
        return 2 * self._dm.period

    @property
    def state_bound(self) -> int:
        return 8

    def retained(self) -> int:
        return 8

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _bar(evidence, "high", "low", "close")
        if found is None or not self._dm.step(*found):
            return None
        n = self._dm.period
        self._smoothed += 1
        dx: float | None = None
        if self._dm.ranges != 0.0:
            plus, minus = self._dm.indicators()
            total = minus + plus
            if total != 0.0:
                dx = 100.0 * (abs(minus - plus) / total)
        if self._smoothed < n:
            self._adx += 0.0 if dx is None else dx
            return None
        if self._smoothed == n:
            self._adx = (self._adx + (0.0 if dx is None else dx)) / n
        elif dx is not None:
            self._adx = (self._adx * (n - 1) + dx) / n
        return quantise(self._adx)

    def export_state(self) -> Mapping[str, object]:
        return {"dm": self._dm.state(), "smoothed": self._smoothed, "adx": self._adx.hex()}

    def import_state(self, state: Mapping[str, object]) -> None:
        smoothed, adx = state["smoothed"], state["adx"]
        if not isinstance(smoothed, int) or not isinstance(adx, str):
            raise ValueError("adx@1 state needs smoothed and adx")
        self._dm.restore(state["dm"])
        self._smoothed, self._adx = smoothed, float.fromhex(adx)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Adx:
        period = int(params["period"])
        if period < 1:
            raise ValueError("adx@1 period must be at least 1")
        return _Adx(period)


BLOCK = _Block()
