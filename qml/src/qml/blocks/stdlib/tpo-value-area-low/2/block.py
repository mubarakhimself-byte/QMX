"""tpo-value-area-low@2: the bottom row of the session's time-price value area.

The session's time-price opportunity profile: each bar is one time block, and it marks every row
its range traversed. A row is the price rounded to the nearest multiple of ``row_size``, named
by that multiple.
``session_start`` is the second of ``clock``'s day a session opens. ``clock`` is 0 for UTC, 1 for
London and 2 for New York. A session is named by the local date it opens on and lasts until the
next one opens, so it keeps the market's own time on both sides of a clock change.
Each bar's ``time`` is its close in nanoseconds UTC; a bar without one is missing.
The point of control is the row with the most blocks; a tie goes to the row nearest the middle
of the session's range, then to the higher row. The value area starts at the point of control
and adds, one row at a time, whichever of the next row above and below holds more blocks (a tie
goes to the row nearer the point of control, then to the higher row) until it holds
``value_area_share`` percent of the blocks. A session whose range spans more than ``max_rows``
rows is missing.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_FLOOR, Decimal

from qml.blocks.api import Side, quantise

_DAY_NS = 86_400 * 10**9
_HALF = Decimal("0.5")

_HOUR_NS = 3_600 * 10**9
_RULES = {1: (0, (3, 0, 1), (10, 0, 1)), 2: (-5, (3, 2, 7), (11, 1, 6))}
"""Each clock's winter hours from UTC, then its move to summer and its move back, each as the
month, the nth Sunday (0 for the last) and the UTC hour. 1 is London and 2 is New York, and 0, UTC,
never moves."""


def _days(year: int, month: int, day: int) -> int:
    """Days from 1970-01-01 to a civil date (H. Hinnant's days_from_civil)."""
    year -= month <= 2
    era = (year if year >= 0 else year - 399) // 400
    yoe = year - era * 400
    doy = (153 * (month + (-3 if month > 2 else 9)) + 2) // 5 + day - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146_097 + doe - 719_468


def _year(days: int) -> int:
    """The civil year of a day count (H. Hinnant's civil_from_days)."""
    z = days + 719_468
    era = (z if z >= 0 else z - 146_096) // 146_097
    doe = z - era * 146_097
    yoe = (doe - doe // 1_460 + doe // 36_524 - doe // 146_096) // 365
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    month = (5 * doy + 2) // 153
    return yoe + era * 400 + (month >= 10)


def _weekday(days: int) -> int:
    """0 for Monday to 6 for Sunday; 1970-01-01 was a Thursday."""
    return (days + 3) % 7


def _sunday(year: int, month: int, nth: int) -> int:
    """The nth Sunday of a month, or the last one when ``nth`` is 0."""
    if nth == 0:
        first_next = _days(year + (month == 12), month % 12 + 1, 1)
        return first_next - 1 - (_weekday(first_next - 1) + 1) % 7
    first = _days(year, month, 1)
    return first + (6 - _weekday(first)) % 7 + 7 * (nth - 1)


def _open_ns(day: int, start_ns: int, clock: int) -> int:
    """The instant the session of local date ``day`` opens. A second a clock change repeats opens at
    its first pass, and a second it skips opens at the instant it would have on winter time."""
    wall = day * _DAY_NS + start_ns
    if clock not in _RULES:
        return wall
    winter, (to_month, to_nth, to_hour), (back_month, back_nth, back_hour) = _RULES[clock]
    year = _year(day)
    into = _sunday(year, to_month, to_nth) * _DAY_NS + to_hour * _HOUR_NS
    back = _sunday(year, back_month, back_nth) * _DAY_NS + back_hour * _HOUR_NS
    summer = wall - (winter + 1) * _HOUR_NS
    return summer if into <= summer < back else wall - winter * _HOUR_NS


def _session_day(closed: int, start_ns: int, clock: int) -> int:
    """The local date of the session a bar closes in, walked back from the instant, so it only ever
    rises across a clock change. A bar closing exactly at a session's open belongs to the one
    before."""
    day = (closed - 1) // _DAY_NS + 1
    while _open_ns(day, start_ns, clock) >= closed:
        day -= 1
    return day


def _clock(params: Mapping[str, Decimal], entry: str) -> int:
    clock = params["clock"]
    if clock not in (0, *_RULES):
        raise ValueError(f"{entry} clock is 0 for UTC, 1 for London, 2 for New York")
    return int(clock)


def _row(price: Decimal, size: Decimal) -> int:
    return int((price / size + _HALF).to_integral_value(rounding=ROUND_FLOOR))


class _Profile:
    __slots__ = (
        "_base",
        "_clock",
        "_counts",
        "_day",
        "_max_rows",
        "_over",
        "_share",
        "_size",
        "_start",
    )

    def __init__(
        self, start_ns: int, size: Decimal, share: Decimal, max_rows: int, clock: int
    ) -> None:
        self._start = start_ns
        self._clock = clock
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
        day = _session_day(closed, self._start, self._clock)
        if day != self._day:
            self._day, self._base, self._counts, self._over = day, 0, [], False
        if self._over:
            return None
        rows = sorted((_row(low, self._size), _row(high, self._size)))
        if rows[1] - rows[0] + 1 > self._max_rows or not self._mark(rows[0], rows[1]):
            self._counts, self._over = [], True
            return None
        poc = self._poc()
        row = self._value_area(poc)[0]
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


def _params(params: Mapping[str, Decimal]) -> tuple[int, Decimal, Decimal, int, int]:
    seconds = int(params["session_start"])
    if not 0 <= seconds < 86_400:
        raise ValueError(
            "tpo-value-area-low@2 session_start is a second of its clock's day, 0 to 86399"
        )
    size, share = params["row_size"], params["value_area_share"]
    if size <= 0:
        raise ValueError("tpo-value-area-low@2 row_size is a price distance above 0")
    if not 0 < share <= 100:
        raise ValueError("tpo-value-area-low@2 value_area_share is a percent above 0, at most 100")
    max_rows = int(params["max_rows"])
    if max_rows < 1:
        raise ValueError("tpo-value-area-low@2 max_rows is at least 1")
    return seconds * 10**9, size, share, max_rows, _clock(params, "tpo-value-area-low@2")


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Profile:
        return _Profile(*_params(params))


BLOCK = _Block()
