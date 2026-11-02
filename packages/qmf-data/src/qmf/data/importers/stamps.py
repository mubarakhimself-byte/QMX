"""The stamp check at import: each file's time unit, the source's clock, and its seams (W9).

A source states time as an epoch count in seconds, milliseconds, microseconds or nanoseconds,
or as wall-clock text in its own zone. The store keeps UTC epoch milliseconds, so the
conversion happens once, here (LD-16). Each file's unit is read from the magnitude of its
first and last stamps (LD-03): a file whose two ends disagree is refused, because a unit that
changes inside one file has no place to put its seam. A file whose unit differs from the file
before it is a ``stamp_unit`` seam at its first stamp, and for a kind with a cadence (bars, book
snapshots) a file whose usual spacing differs from the one before it is a ``cadence`` seam
(LD-04). The card carries the clock and the seams, so a result that crosses one can name it.

Stdlib + qmf-core.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from itertools import pairwise
from pathlib import Path
from typing import Final, cast

from qmf.core import Ok, Result
from qmf.data.store.refusals import invalid_input

__all__ = [
    "STORE_UNIT",
    "WALL",
    "ClockLedger",
    "Seam",
    "SeamKind",
    "SourceClock",
    "StampCheck",
    "StampUnit",
    "iso_ms",
    "unit_of",
]


class StampUnit(StrEnum):
    """An epoch count's unit, as its magnitude says it."""

    SECONDS = "s"
    MILLIS = "ms"
    MICROS = "us"
    NANOS = "ns"


STORE_UNIT: Final = StampUnit.MILLIS
"""What the store keeps: UTC epoch milliseconds."""

WALL: Final[str] = "wall"
"""A source that writes wall-clock text in its own zone, not an epoch count."""

_BANDS: Final[tuple[tuple[int, int, StampUnit], ...]] = (
    (10**8, 10**11, StampUnit.SECONDS),
    (10**11, 10**14, StampUnit.MILLIS),
    (10**14, 10**17, StampUnit.MICROS),
    (10**17, 10**20, StampUnit.NANOS),
)
"""Each unit's band. From 1973 to 5138 the four bands do not overlap."""

_PER_MS: Final[dict[StampUnit, tuple[int, int]]] = {
    StampUnit.SECONDS: (1000, 1),
    StampUnit.MILLIS: (1, 1),
    StampUnit.MICROS: (1, 1000),
    StampUnit.NANOS: (1, 1_000_000),
}


def unit_of(stamp: int) -> StampUnit | None:
    """The unit an epoch count's magnitude says, or None when it is no plausible epoch."""
    for low, high, unit in _BANDS:
        if low <= stamp < high:
            return unit
    return None


def _to_ms(stamp: int, unit: StampUnit) -> int:
    times, per = _PER_MS[unit]
    return stamp * times // per


def iso_ms(t_ms: int) -> str:
    """A UTC epoch millisecond as the ISO text a card shows."""
    moment = datetime.fromtimestamp(t_ms // 1000, tz=UTC)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t_ms % 1000:03d}Z"


class SeamKind(StrEnum):
    STAMP_UNIT = "stamp_unit"
    CADENCE = "cadence"


@dataclass(frozen=True, slots=True)
class Seam:
    """Where a source changed shape: from ``at_ms`` on, ``after`` holds instead of ``before``."""

    kind: SeamKind
    at_ms: int
    before: str
    after: str

    def as_json(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "at": iso_ms(self.at_ms),
            "at_ms": self.at_ms,
            "before": self.before,
            "after": self.after,
        }


@dataclass(frozen=True, slots=True)
class SourceClock:
    """The zone a source stamps in and the unit of its first stamp; the seams say what changed."""

    zone: str
    unit: str

    def as_json(self) -> dict[str, object]:
        return {"zone": self.zone, "unit": self.unit}


def _cadence(stamps: Sequence[int]) -> int | None:
    """The spacing between consecutive stamps that occurs most often, in ms."""
    steps = Counter(b - a for a, b in pairwise(stamps) if b > a)
    if not steps:
        return None
    return min(steps.items(), key=lambda item: (-item[1], item[0]))[0]


class StampCheck:
    """The files of one import in time order, each checked and converted to UTC milliseconds.

    ``zone`` is the source's clock as its documentation states it. An epoch count is UTC by
    definition, so the zone is recorded for the card and moves nothing. ``cadenced`` asks for
    cadence seams, which only a kind sampled on a cadence has.
    """

    def __init__(
        self,
        *,
        zone: str = "UTC",
        cadenced: bool = False,
        after: StampUnit | None = None,
        after_cadence_ms: int | None = None,
    ) -> None:
        self._zone = zone
        self._cadenced = cadenced
        self._first: StampUnit | None = None
        self._unit: StampUnit | None = after
        self._spacing: int | None = after_cadence_ms
        self._seams: list[Seam] = []

    @property
    def clock(self) -> SourceClock:
        return SourceClock(self._zone, (self._first or STORE_UNIT).value)

    @property
    def seams(self) -> tuple[Seam, ...]:
        return tuple(self._seams)

    @property
    def last(self) -> tuple[StampUnit | None, int | None]:
        """The unit and the cadence of the last file read, which the next import starts from."""
        return self._unit, self._spacing

    def file(
        self, name: str, rows: Sequence[tuple[object, ...]]
    ) -> Result[list[tuple[object, ...]]]:
        """One file's rows with their first cell, the stamp, in UTC epoch milliseconds."""
        if not rows:
            return Ok([])
        first, last = rows[0][0], rows[-1][0]
        if not isinstance(first, int) or not isinstance(last, int):
            return invalid_input("t", "a file's stamps are epoch counts", file=name)
        unit, closing = unit_of(first), unit_of(last)
        if unit is None or closing is None:
            return invalid_input(
                "t", "a stamp is no plausible epoch count", file=name, first=first, last=last
            )
        if unit is not closing:
            return invalid_input(
                "t",
                "a file's first and last stamps disagree on their unit",
                file=name,
                first=unit.value,
                last=closing.value,
            )
        converted: list[tuple[object, ...]] = []
        stamps: list[int] = []
        for row in rows:
            stamp = row[0]
            if not isinstance(stamp, int):
                return invalid_input("t", "a file's stamps are epoch counts", file=name)
            stamps.append(_to_ms(stamp, unit))
            converted.append((stamps[-1], *row[1:]))
        start = stamps[0]
        self._first = self._first or unit
        if self._unit is not None and unit is not self._unit:
            self._seams.append(Seam(SeamKind.STAMP_UNIT, start, self._unit.value, unit.value))
        self._unit = unit
        if self._cadenced:
            spacing = _cadence(stamps)
            if spacing is not None:
                if self._spacing is not None and spacing != self._spacing:
                    self._seams.append(
                        Seam(SeamKind.CADENCE, start, f"{self._spacing}ms", f"{spacing}ms")
                    )
                self._spacing = spacing
        return Ok(converted)


class ClockLedger:
    """The unit and cadence each landed month of a series ended in, beside a store's claims.

    A month is one download run, so a seam at a month boundary (Binance's spot files moved to
    microseconds on 1 January 2025) is only seen against the month before. The ledger is one
    small file per series under ``<root>/.clocks``; a month landed again replaces its entry.
    """

    def __init__(self, root: Path) -> None:
        self._folder = root / ".clocks"

    def _path(self, series: str) -> Path:
        return self._folder / f"{series.replace('/', '_')}.json"

    def _months(self, series: str) -> dict[str, dict[str, object]]:
        path = self._path(series)
        if not path.is_file():
            return {}
        return cast("dict[str, dict[str, object]]", json.loads(path.read_text("utf-8")))

    def before(self, series: str, year: int, month: int) -> tuple[StampUnit | None, int | None]:
        """What the latest month before ``year``-``month`` ended in, or nothing when none."""
        earlier = sorted(m for m in self._months(series) if m < f"{year:04d}-{month:02d}")
        if not earlier:
            return None, None
        found = self._months(series)[earlier[-1]]
        cadence = found.get("cadence_ms")
        return StampUnit(str(found["unit"])), cadence if isinstance(cadence, int) else None

    def record(self, series: str, year: int, month: int, check: StampCheck) -> None:
        unit, cadence = check.last
        if unit is None:
            return
        months = self._months(series)
        months[f"{year:04d}-{month:02d}"] = {"unit": unit.value, "cadence_ms": cadence}
        self._folder.mkdir(parents=True, exist_ok=True)
        staged = self._path(series).with_suffix(".tmp")
        staged.write_text(json.dumps(months, sort_keys=True), encoding="utf-8")
        staged.replace(self._path(series))
