"""vwap-session-anchored@2: the volume-weighted average typical price since the session
opened.

The typical price ``(high + low + close) / 3`` of each bar of the session weighted by its
volume, missing while the session's volume is 0.

``session_start`` is the second of ``clock``'s day a session opens. ``clock`` is 0 for UTC, 1 for
London and 2 for New York. A session is named by the local date it opens on and lasts until the
next one opens, so it keeps the market's own time on both sides of a clock change.
Each bar's ``time`` is its close in nanoseconds UTC; a bar without one or
without volume is missing. The value comes from the first bar on. On FX and CFD bars the
volume is a tick count.
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


def _session(
    evidence: Mapping[str, object], start_ns: int, clock: int
) -> tuple[int, tuple[float, ...]] | None:
    """The session a bar closes in and its prices. A bar closing exactly at the session start
    belongs to the session before; ``time`` is the bar's close in nanoseconds UTC."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    closed = bar.get("time")
    found = _bar(evidence, "high", "low", "close")
    if not isinstance(closed, int) or isinstance(closed, bool) or found is None:
        return None
    return _session_day(closed, start_ns, clock), found


def _start(params: Mapping[str, Decimal], entry: str) -> tuple[int, int]:
    seconds = int(params["session_start"])
    if not 0 <= seconds < 86_400:
        raise ValueError(f"{entry} session_start is a second of its clock's day, 0 to 86399")
    return seconds * 10**9, _clock(params, entry)


class _Vwap:
    __slots__ = ("_clock", "_day", "_start", "_volume", "_weighted")

    def __init__(self, start_ns: int, clock: int) -> None:
        self._start = start_ns
        self._clock = clock
        self._day: int | None = None
        self._weighted = 0.0
        self._volume = 0.0

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 3

    def retained(self) -> int:
        return 0 if self._day is None else 3

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _session(evidence, self._start, self._clock)
        volume = _bar(evidence, "volume")
        if found is None or volume is None:
            return None
        day, (high, low, close) = found
        if day != self._day:
            self._day, self._weighted, self._volume = day, 0.0, 0.0
        self._weighted += (high + low + close) / 3 * volume[0]
        self._volume += volume[0]
        return quantise(self._weighted / self._volume) if self._volume > 0.0 else None

    def export_state(self) -> Mapping[str, object]:
        return {"day": self._day, "sums": [self._weighted.hex(), self._volume.hex()]}

    def import_state(self, state: Mapping[str, object]) -> None:
        day = state.get("day")
        self._day = day if isinstance(day, int) else None
        self._weighted, self._volume = _floats(state["sums"], "vwap-session-anchored@2 sums")


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Vwap:
        return _Vwap(*_start(params, "vwap-session-anchored@2"))


BLOCK = _Block()
