"""When a `cron` or `interval` trigger falls due.

Five-field cron runs in the trigger's IANA zone through `cronsim` 2.7 (pinned in the engine's
`pyproject.toml`), which keeps cron's own DST rules: a time the spring change skips runs once at
the first valid minute after it, and a time the autumn change repeats runs once, on its first
pass. An interval counts whole steps from the trigger's creation. Every instant leaves here in
UTC, and `stamp` writes one fixed-width text, so stored times compare as text.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from itertools import islice
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from cronsim import CronSim, CronSimError

MAX_MISSED = 1000
"""How many missed occurrences one tick lists; past that only the latest is added."""


class BadSchedule(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Cron:
    expr: str
    zone: str

    def __post_init__(self) -> None:
        if len(self.expr.split()) != 5:
            raise BadSchedule("a cron trigger needs five fields")
        try:
            CronSim(self.expr, datetime.now(ZoneInfo(self.zone)))
        except (CronSimError, ZoneInfoNotFoundError, ValueError) as error:
            raise BadSchedule(f"not a cron in an IANA zone: {error}") from None


@dataclass(frozen=True, slots=True)
class Interval:
    seconds: int
    anchor: datetime

    def __post_init__(self) -> None:
        if self.seconds < 1:
            raise BadSchedule("an interval trigger needs at least one second")


type Clocked = Cron | Interval


def stamp(when: datetime) -> str:
    return when.astimezone(UTC).isoformat(timespec="microseconds")


def instant(text: str) -> datetime:
    return datetime.fromisoformat(text).astimezone(UTC)


def after(schedule: Clocked, when: datetime) -> Iterator[datetime]:
    """Every occurrence strictly after `when`, in UTC."""
    match schedule:
        case Cron(expr, zone):
            for found in CronSim(expr, when.astimezone(ZoneInfo(zone))):
                yield found.astimezone(UTC)
        case Interval(seconds, anchor):
            step = timedelta(seconds=seconds)
            k = max((when - anchor) // step + 1, 1)
            while True:
                yield anchor + k * step
                k += 1


def latest(schedule: Clocked, now: datetime) -> datetime:
    """The newest occurrence at or before `now`. Cron occurrences fall on whole minutes."""
    floor = now.replace(microsecond=0) + timedelta(seconds=1)
    match schedule:
        case Cron(expr, zone):
            found = next(CronSim(expr, floor.astimezone(ZoneInfo(zone)), reverse=True))
            return found.astimezone(UTC)
        case Interval(seconds, anchor):
            return anchor + ((now - anchor) // timedelta(seconds=seconds)) * timedelta(
                seconds=seconds
            )


def missed(schedule: Clocked, first: datetime, now: datetime) -> list[datetime]:
    """`first` and every later occurrence up to `now`, oldest first. After a long downtime only
    the oldest `MAX_MISSED` are listed, then the latest."""
    if first > now:
        return []
    listed = [first, *islice(_until(after(schedule, first), now), MAX_MISSED - 1)]
    last = latest(schedule, now)
    return listed if last <= listed[-1] else [*listed, last]


def _until(occurrences: Iterator[datetime], now: datetime) -> Iterator[datetime]:
    for occurrence in occurrences:
        if occurrence > now:
            return
        yield occurrence
