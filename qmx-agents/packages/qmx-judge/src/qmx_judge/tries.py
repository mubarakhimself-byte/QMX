"""The try ledger: one append-only `try` item per counted try (Level 0 AD-25, Part B AD-207).

A run writes two items, never one item edited: the `opened` try when the lander opens it and a
`landed` or `failed` try when it closes, linking back to the first. Each is written once by one
writer, so concurrent runs share no record, and family counts are a query over `try` items.

Effective tries are computed at read (`effective_tries`): the daily R streams of the family's
runs are clustered, a correlation above the threshold joining two streams into one cluster, and a
try with no stream (a failed or killed run, a zero-trade run, a spec edit) counts as one by itself.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Final, Literal

__all__ = [
    "TRY_KIND",
    "Counted",
    "DailyR",
    "Try",
    "TryKind",
    "TryState",
    "correlation",
    "daily_r",
    "effective_tries",
    "spec_edit_item",
    "try_item",
]

TRY_KIND: Final = "try"

type TryKind = Literal["run", "check", "spec_edit", "shortlist", "paper_pick", "whatif_rerun"]
type TryState = Literal["opened", "landed", "failed", "recorded"]
type DailyR = Mapping[str, float]
"""One stream's R summed by UTC close day (`YYYY-MM-DD`). Statistics only: never a money value."""

_NS_PER_S: Final = 1_000_000_000


def try_item(run_id: str, state: TryState) -> str:
    """The Library item of a run's opening or closing try, named by its run id so a retry
    finds it instead of writing a second one."""
    return f"try-{run_id}-{'opened' if state == 'opened' else 'closed'}"


def spec_edit_item(spec_object: str) -> str:
    """The item of the `spec_edit` try a study spec's new version lands, named by that version,
    so saving the same version again finds it."""
    return f"try-spec_edit-{spec_object}"


@dataclass(frozen=True, slots=True)
class Try:
    kind: TryKind
    state: TryState
    run_id: str
    family: str
    unit: str
    principal: str
    at: str
    study: str | None = None
    market: str | None = None
    tester: Mapping[str, str] | None = None
    place: str | None = None
    links: tuple[str, ...] = ()

    def fields(self) -> dict[str, object]:
        """The item's fields, as the `try` kind file declares them."""
        found: dict[str, object] = {
            "kind": self.kind,
            "state": self.state,
            "run_id": self.run_id,
            "family": self.family,
            "unit": self.unit,
            "principal": self.principal,
            "at": self.at,
            "links": list(self.links),
        }
        optional = {
            "study": self.study,
            "market": self.market,
            "tester": None if self.tester is None else dict(self.tester),
            "place": self.place,
        }
        found.update({name: value for name, value in optional.items() if value is not None})
        return found


@dataclass(frozen=True, slots=True)
class Counted:
    """One counted try as the clustering reads it: its label and its daily R stream, or None
    when it has none (a failed run, a zero-trade run, a spec edit, a shortlisted market)."""

    label: str
    stream: DailyR | None


def daily_r(trades: Iterable[tuple[int, Decimal]]) -> dict[str, float]:
    """`(closed_at_ns, r)` pairs summed by UTC close day."""
    days: dict[str, Decimal] = {}
    for closed_at, r in trades:
        day = datetime.fromtimestamp(closed_at // _NS_PER_S, UTC).date().isoformat()
        days[day] = days.get(day, Decimal(0)) + r
    return {day: float(total) for day, total in sorted(days.items())}


def correlation(left: DailyR, right: DailyR) -> float:
    """Pearson correlation over the union of both streams' days, a day with no trade being 0 R.
    A stream with no spread correlates with nothing (0)."""
    days = sorted(left.keys() | right.keys())
    xs = [left.get(day, 0.0) for day in days]
    ys = [right.get(day, 0.0) for day in days]
    n = len(days)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def effective_tries(tries: Sequence[Counted], threshold: float) -> int:
    """How many independent tries `tries` are: streams whose correlation is above `threshold`
    join one cluster (single linkage, the crude stand-in for ONC research 24 measured), and a
    try without a stream counts as one."""
    streams = [t.stream for t in tries if t.stream]
    alone = len(tries) - len(streams)
    seen = [False] * len(streams)
    clusters = 0
    for start in range(len(streams)):
        if seen[start]:
            continue
        clusters += 1
        seen[start] = True
        stack = [start]
        while stack:
            here = streams[stack.pop()]
            for other in range(len(streams)):
                if not seen[other] and correlation(here, streams[other]) > threshold:
                    seen[other] = True
                    stack.append(other)
    return clusters + alone
