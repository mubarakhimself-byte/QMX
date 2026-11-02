"""lbma-silver-auction-clock@1: seconds from the nearest LBMA Silver Price auction, at 12:00 London
time.

The value is the bar's close time less the nearest event time, in seconds: negative before the
event, positive after it, so a window of N minutes either side is an absolute value of at most
60 N; a close equally far from two events measures from the later one. Each bar's ``time`` is
its close in nanoseconds UTC; a bar without one is missing. Auctions run on London weekdays; UK
bank holidays are not modelled.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise

_DAY_NS = 86_400 * 10**9
_HOUR_NS = 3_600 * 10**9
_SEARCH_DAYS = 8


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


def _offset_ns(day: int) -> int:
    """Europe/London: one hour ahead of UTC from the last Sunday of March to the last Sunday of
    October (the change is at 01:00 UTC, before any event this clock names)."""
    year = _year(day)
    return _HOUR_NS if _sunday(year, 3, 0) <= day < _sunday(year, 10, 0) else 0


def _on(day: int, events: tuple[tuple[int, int], ...]) -> list[int]:
    """The UTC instants of the events on one London weekday."""
    if _weekday(day) > 4:
        return []
    return [day * _DAY_NS + minute * 60 * 10**9 - _offset_ns(day) for _, minute in events]


def _nearest(closed: int, events: list[int]) -> int:
    return min(events, key=lambda at: (abs(closed - at), -at))


class _Clock:
    __slots__ = ("_events",)

    def __init__(self, events: tuple[tuple[int, int], ...]) -> None:
        self._events = events

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        bar = evidence.get("series")
        if not isinstance(bar, Mapping):
            return None
        closed = bar.get("time")
        if not isinstance(closed, int) or isinstance(closed, bool):
            return None
        today = closed // _DAY_NS
        events = [
            at
            for day in range(today - _SEARCH_DAYS, today + _SEARCH_DAYS + 1)
            for at in _on(day, self._events)
        ]
        if not events:
            return None
        return quantise(Decimal(closed - _nearest(closed, events)) / Decimal(10**9))

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


def _events(params: Mapping[str, Decimal]) -> tuple[tuple[int, int], ...]:
    return ((0, 720),)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Clock:
        return _Clock(_events(params))


BLOCK = _Block()
