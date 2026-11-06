"""initial-balance-low@2: the low of the session's initial balance, once it is complete.

The initial balance is the high and low of the bars that close within the first ``ib_seconds``
of the session.
``session_start`` is the second of ``clock``'s day a session opens. ``clock`` is 0 for UTC, 1 for
London and 2 for New York. A session is named by the local date it opens on and lasts until the
next one opens, so it keeps the market's own time on both sides of a clock change.
Each bar's ``time`` is its close in nanoseconds UTC; a bar without one is missing.
The value is missing until the initial balance is complete, which is at the first bar that
closes at or after its end, and for the whole session when no bar closed inside it.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise

_DAY_NS = 86_400 * 10**9

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


class _Balance:
    __slots__ = ("_clock", "_day", "_done", "_extreme", "_high", "_ib", "_low", "_side", "_start")

    def __init__(self, start_ns: int, ib_ns: int, side: int, clock: int) -> None:
        self._start = start_ns
        self._clock = clock
        self._ib = ib_ns
        self._side = side
        self._day: int | None = None
        self._high: Decimal | None = None
        self._low: Decimal | None = None
        self._extreme: Decimal | None = None
        self._done = False

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 3

    def retained(self) -> int:
        return 0 if self._day is None else 3

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
            self._day, self._high, self._low, self._extreme, self._done = (
                day,
                None,
                None,
                None,
                False,
            )
        into = closed - _open_ns(day, self._start, self._clock)
        if not self._done and into <= self._ib:
            self._high = high if self._high is None else max(self._high, high)
            self._low = low if self._low is None else min(self._low, low)
            self._done = into == self._ib
        else:
            self._done = True
            if self._side > 0:
                self._extreme = high if self._extreme is None else max(self._extreme, high)
            else:
                self._extreme = low if self._extreme is None else min(self._extreme, low)
        if not self._done or self._high is None or self._low is None:
            return None
        return quantise(self._low)

    def export_state(self) -> Mapping[str, object]:
        return {
            "day": self._day,
            "done": self._done,
            "range": [None if v is None else str(v) for v in (self._high, self._low)],
            "extreme": None if self._extreme is None else str(self._extreme),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        day, held, extreme = state.get("day"), state.get("range"), state.get("extreme")
        self._day = day if isinstance(day, int) else None
        self._done = state.get("done") is True
        pair = held if isinstance(held, list) else [None, None]
        self._high, self._low = (None if v is None else Decimal(str(v)) for v in pair)
        self._extreme = None if extreme is None else Decimal(str(extreme))


def _params(params: Mapping[str, Decimal]) -> tuple[int, int, int, int]:
    seconds = int(params["session_start"])
    if not 0 <= seconds < 86_400:
        raise ValueError(
            "initial-balance-low@2 session_start is a second of its clock's day, 0 to 86399"
        )
    ib = int(params["ib_seconds"])
    if not 0 < ib < 86_400:
        raise ValueError("initial-balance-low@2 ib_seconds is above 0 and below a day")
    side = int(params.get("side", Decimal(1)))
    if side not in (1, -1):
        raise ValueError("initial-balance-low@2 side is 1 for above the balance or -1 for below")
    return seconds * 10**9, ib * 10**9, side, _clock(params, "initial-balance-low@2")


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Balance:
        return _Balance(*_params(params))


BLOCK = _Block()
