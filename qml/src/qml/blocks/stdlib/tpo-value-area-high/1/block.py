"""tpo-value-area-high@1: the top row of the session's time-price value area.

The session's time-price opportunity profile: each bar is one time block, and it marks every row
its range traversed. A row is the price rounded to the nearest multiple of ``row_size``, named
by that multiple. ``session_start`` is the second of the UTC day a session opens, and a session
lasts a day. Each bar's ``time`` is its close in nanoseconds UTC; a bar without one is missing.
The point of control is the row with the most blocks; a tie goes to the row nearest the middle
of the session's range, then to the higher row. The value area starts at the point of control
and adds, one row at a time, whichever of the next row above and below holds more blocks (a tie
goes to the row nearer the point of control, then to the higher row) until it holds
``value_area_share`` percent of the blocks. A session whose range spans more than ``max_rows``
rows is missing.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_FLOOR, Decimal

from qml.blocks.api import Side, quantise

_DAY_NS = 86_400 * 10**9
_HALF = Decimal("0.5")


def _row(price: Decimal, size: Decimal) -> int:
    return int((price / size + _HALF).to_integral_value(rounding=ROUND_FLOOR))


class _Profile:
    __slots__ = ("_base", "_counts", "_day", "_max_rows", "_over", "_share", "_size", "_start")

    def __init__(self, start_ns: int, size: Decimal, share: Decimal, max_rows: int) -> None:
        self._start = start_ns
        self._size = size
        self._share = share
        self._max_rows = max_rows
        self._day: int | None = None
        self._base = 0
        self._counts: list[int] = []
        self._over = False

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return self._max_rows

    def retained(self) -> int:
        return len(self._counts)

    def _mark(self, low: int, high: int) -> bool:
        if not self._counts:
            self._base, self._counts = low, [0] * (high - low + 1)
        else:
            top = max(high, self._base + len(self._counts) - 1)
            bottom = min(low, self._base)
            if top - bottom + 1 > self._max_rows:
                return False
            self._counts = [0] * (self._base - bottom) + self._counts
            self._counts += [0] * (top - bottom + 1 - len(self._counts))
            self._base = bottom
        for row in range(low - self._base, high - self._base + 1):
            self._counts[row] += 1
        return True

    def _poc(self) -> int:
        counts = self._counts
        most = max(counts)
        middle = Decimal(len(counts) - 1) / 2
        ties = [i for i, n in enumerate(counts) if n == most]
        return min(ties, key=lambda i: (abs(Decimal(i) - middle), -i))

    def _value_area(self, poc: int) -> tuple[int, int]:
        counts = self._counts
        target = Decimal(sum(counts)) * self._share / 100
        down = up = poc
        held = counts[poc]
        while held < target:
            above = counts[up + 1] if up + 1 < len(counts) else None
            below = counts[down - 1] if down > 0 else None
            if above is None and below is None:
                break
            if below is None or (above is not None and above > below):
                up += 1
                held += counts[up]
            elif above is None or below > above:
                down -= 1
                held += counts[down]
            elif up + 1 - poc <= poc - (down - 1):
                up += 1
                held += counts[up]
            else:
                down -= 1
                held += counts[down]
        return down, up

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        bar = evidence.get("series")
        if not isinstance(bar, Mapping):
            return None
        closed, high, low = bar.get("time"), bar.get("high"), bar.get("low")
        if (
            not isinstance(closed, int)
            or isinstance(closed, bool)
            or not isinstance(high, Decimal)
            or not isinstance(low, Decimal)
        ):
            return None
        day = (closed - 1 - self._start) // _DAY_NS
        if day != self._day:
            self._day, self._base, self._counts, self._over = day, 0, [], False
        if self._over:
            return None
        rows = sorted((_row(low, self._size), _row(high, self._size)))
        if rows[1] - rows[0] + 1 > self._max_rows or not self._mark(rows[0], rows[1]):
            self._counts, self._over = [], True
            return None
        poc = self._poc()
        row = self._value_area(poc)[1]
        return quantise(Decimal(self._base + row) * self._size)

    def export_state(self) -> Mapping[str, object]:
        return {
            "day": self._day,
            "base": self._base,
            "counts": list(self._counts),
            "over": self._over,
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        day, base, counts = state.get("day"), state.get("base"), state.get("counts")
        self._day = day if isinstance(day, int) else None
        self._base = base if isinstance(base, int) else 0
        self._counts = [int(str(n)) for n in counts] if isinstance(counts, list) else []
        self._over = state.get("over") is True


def _params(params: Mapping[str, Decimal]) -> tuple[int, Decimal, Decimal, int]:
    seconds = int(params["session_start"])
    if not 0 <= seconds < 86_400:
        raise ValueError(
            "tpo-value-area-high@1 session_start is a second of the UTC day, 0 to 86399"
        )
    size, share = params["row_size"], params["value_area_share"]
    if size <= 0:
        raise ValueError("tpo-value-area-high@1 row_size is a price distance above 0")
    if not 0 < share <= 100:
        raise ValueError("tpo-value-area-high@1 value_area_share is a percent above 0, at most 100")
    max_rows = int(params["max_rows"])
    if max_rows < 1:
        raise ValueError("tpo-value-area-high@1 max_rows is at least 1")
    return seconds * 10**9, size, share, max_rows


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Profile:
        return _Profile(*_params(params))


BLOCK = _Block()
