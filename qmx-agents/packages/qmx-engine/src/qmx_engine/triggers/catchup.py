"""One catch-up run per trigger after downtime (ruling 54, AD-10, SOLUTION-DESIGN 4.2 step 3).

A tick fires at most one occurrence per trigger: the latest one due. An occurrence inside
`scheduler.grace` runs late. Past it the backlog collapses: the latest fires as the one catch-up,
and every earlier occurrence is recorded `skipped: downtime`. An earlier occurrence still inside
the grace window is recorded `skipped: merged`, since the fire that runs covers it. A trigger whose
`catch_up` is `record_only` records a stale backlog and fires nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

type CatchUp = Literal["merged", "record_only"]


@dataclass(frozen=True, slots=True)
class Collapsed:
    fire: datetime | None
    skipped: tuple[tuple[datetime, str], ...]
    """Each skipped occurrence and why: `downtime` or `merged`."""


def collapse(
    occurrences: list[datetime], now: datetime, grace: timedelta, catch_up: CatchUp = "merged"
) -> Collapsed:
    """`occurrences` are the due ones, oldest first."""
    if not occurrences:
        return Collapsed(None, ())
    *earlier, last = occurrences
    stale = now - last > grace
    skipped = tuple((o, "downtime" if now - o > grace else "merged") for o in earlier)
    if stale and catch_up == "record_only":
        return Collapsed(None, (*skipped, (last, "downtime")))
    return Collapsed(last, skipped)
