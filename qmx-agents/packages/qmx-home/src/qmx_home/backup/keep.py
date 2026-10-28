"""Which copies a place keeps (design 62 C2, Appendix D's keep rules). Pure.

The counts are of the newest hours, days, weeks and months that hold a copy, never windows back
from the clock, so a PC away for a year or a clock that jumped ahead never empties a place. The
newest copy and the newest copy that passed a drill are always kept.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import UTC, datetime

from qmx_home.backup.plan import Keep


def when(stamp: str) -> datetime:
    """The moment a copy's stamp (`20261027T030000123456Z`) names."""
    return datetime.strptime(stamp, "%Y%m%dT%H%M%S%fZ").replace(tzinfo=UTC)


def kept(
    copies: Sequence[str],
    keep: Keep,
    *,
    drilled: str | None = None,
    held: Collection[str] = (),
) -> frozenset[str]:
    """The stamps of `copies` to keep: the newest copy of each of the newest `keep.hours` hours
    that hold one, and likewise for days, weeks and months, with the newest copy, `drilled` (the
    newest that passed a drill) and `held` (copies kept for their own reason) always kept."""
    newest_first = sorted(copies, reverse=True)
    kept_now: set[str] = set(newest_first[:1])
    for count, bucket in (
        (keep.hours, _hour),
        (keep.days, _day),
        (keep.weeks, _week),
        (keep.months, _month),
    ):
        seen: set[tuple[int, ...]] = set()
        for stamp in newest_first:
            if len(seen) >= count:
                break
            key = bucket(when(stamp))
            if key not in seen:
                seen.add(key)
                kept_now.add(stamp)
    present = set(newest_first)
    kept_now.update(stamp for stamp in (drilled, *held) if stamp in present)
    return frozenset(kept_now)


def released(made: datetime, elsewhere: Sequence[datetime]) -> bool:
    """Whether a copy held until a whole copy made after it reached a storage on another disk
    may go: `elsewhere` are the moments such copies were made (design 06 section 5)."""
    return any(moment > made for moment in elsewhere)


def _hour(moment: datetime) -> tuple[int, ...]:
    return (moment.year, moment.month, moment.day, moment.hour)


def _day(moment: datetime) -> tuple[int, ...]:
    return (moment.year, moment.month, moment.day)


def _week(moment: datetime) -> tuple[int, ...]:
    found = moment.isocalendar()
    return (found.year, found.week)


def _month(moment: datetime) -> tuple[int, ...]:
    return (moment.year, moment.month)
