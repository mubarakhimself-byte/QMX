"""The data-quality check: a month's stamps counted against its market's open time (LD-01).

One pass over the stamps in the order the source gave them finds three things the store's
own gap rule cannot see, because only the calendar knows when the market was open:

* **missing minutes**: minutes of open time that hold no row, with each run of at least
  ``gap_minutes`` listed as a gap;
* **empty open hours**: hours wholly inside open time that hold no row. Such an hour is a
  fetch failure until a retry and a second source agree that it was empty, so the report holds
  the month open (``hold``) until every one of them is confirmed;
* **clock jumps**: a stamp earlier than the one before it, listed with the minutes it went back.

The calendar is a function of UTC epoch milliseconds, so the check reads any calendar source:
the shipped ``qmx.calendar/1`` files in the engine, or a fixture in a test.

Stdlib only.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from qmf.data.importers.stamps import iso_ms

__all__ = ["GAP_MINUTES", "Gap", "Jump", "OpenAt", "QualityReport", "check_month", "hour_ms"]

GAP_MINUTES: Final[int] = 5
"""The data-quality step's ``gap_minutes`` starting default: a run of missing open minutes
this long or longer is listed as a gap."""

MS_PER_MINUTE: Final[int] = 60_000
MS_PER_HOUR: Final[int] = 60 * MS_PER_MINUTE

OpenAt = Callable[[int], bool]
"""Whether the market is open at a UTC epoch millisecond."""


@dataclass(frozen=True, slots=True)
class Gap:
    """Open minutes in a row with no data, from ``start_ms`` up to ``end_ms``."""

    start_ms: int
    end_ms: int

    @property
    def minutes(self) -> int:
        return (self.end_ms - self.start_ms) // MS_PER_MINUTE

    def as_json(self) -> dict[str, object]:
        return {"from": iso_ms(self.start_ms), "to": iso_ms(self.end_ms), "minutes": self.minutes}


@dataclass(frozen=True, slots=True)
class Jump:
    """A stamp at ``at_ms`` that came after a later one: the source's clock went back."""

    at_ms: int
    back_ms: int

    def as_json(self) -> dict[str, object]:
        return {
            "at": iso_ms(self.at_ms),
            "back_ms": self.back_ms,
            "minutes": self.back_ms // MS_PER_MINUTE,
        }


@dataclass(frozen=True, slots=True)
class QualityReport:
    """What one month's check found."""

    missing_minutes: int
    gaps: tuple[Gap, ...]
    empty_hours: tuple[int, ...]
    confirmed: tuple[int, ...]
    jumps: tuple[Jump, ...]

    @property
    def unconfirmed(self) -> tuple[int, ...]:
        return tuple(hour for hour in self.empty_hours if hour not in self.confirmed)

    @property
    def hold(self) -> str | None:
        """Why the month stays open, or None when nothing waits for a later fetch."""
        waiting = self.unconfirmed
        if not waiting:
            return None
        hours = ", ".join(iso_ms(hour) for hour in waiting)
        return (
            f"{len(waiting)} empty hour(s) in open time wait for a retry and a second source "
            f"to agree: {hours}"
        )

    def as_json(self) -> dict[str, object]:
        return {
            "missing_minutes": self.missing_minutes,
            "gaps": [gap.as_json() for gap in self.gaps],
            "empty_open_hours": [iso_ms(hour) for hour in self.empty_hours],
            "unconfirmed_hours": [iso_ms(hour) for hour in self.unconfirmed],
            "clock_jumps": [jump.as_json() for jump in self.jumps],
            "held_open": self.hold is not None,
        }


def hour_ms(text: str) -> int | None:
    """An hour named as ``YYYY-MM-DDTHH`` (any minutes, seconds or zone suffix after it is
    ignored) as UTC epoch milliseconds, or None when the text names no hour."""
    try:
        moment = datetime.strptime(text[:13], "%Y-%m-%dT%H").replace(tzinfo=UTC)
    except ValueError:
        return None
    return int(moment.timestamp()) * 1000


def check_month(
    stamps_ms: Iterable[int],
    *,
    start_ms: int,
    end_ms: int,
    open_at: OpenAt,
    gap_minutes: int = GAP_MINUTES,
    confirmed: Iterable[int] = (),
) -> QualityReport:
    """Check one month's stamps, in source order, against open time from ``start_ms`` to
    ``end_ms``. ``confirmed`` are the hour starts a retry and a second source both found empty.
    """
    seen: set[int] = set()
    jumps: list[Jump] = []
    previous: int | None = None
    for stamp in stamps_ms:
        if previous is not None and stamp < previous:
            jumps.append(Jump(stamp, previous - stamp))
        previous = stamp
        seen.add(stamp // MS_PER_MINUTE)
    first = start_ms // MS_PER_MINUTE
    minutes = range(first, end_ms // MS_PER_MINUTE)
    absent = [open_at(minute * MS_PER_MINUTE) and minute not in seen for minute in minutes]
    gaps: list[Gap] = []
    run: int | None = None
    for offset, gone in enumerate([*absent, False]):
        if gone and run is None:
            run = offset
        elif not gone and run is not None:
            if offset - run >= gap_minutes:
                gaps.append(Gap((first + run) * MS_PER_MINUTE, (first + offset) * MS_PER_MINUTE))
            run = None
    empty = [
        (first + offset) * MS_PER_MINUTE
        for offset in range(-first % 60, len(absent) - 59, 60)
        if all(absent[offset : offset + 60])
    ]
    agreed = frozenset(confirmed)
    return QualityReport(
        missing_minutes=sum(absent),
        gaps=tuple(gaps),
        empty_hours=tuple(empty),
        confirmed=tuple(hour for hour in empty if hour in agreed),
        jumps=tuple(jumps),
    )
