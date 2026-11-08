"""Read the risk-lab one-minute bar CSVs into typed bid or ask partitions (W9).

One file holds one side of one month: ``open, high, low, close, volume`` against a
timestamp column, prices as decimals. The importer scales each price to the int64
:data:`~qmf.data.store.engines.typed.PRICE_SCALE` the typed writer uses, sorts the rows by
time because a CSV is not guaranteed ordered, and commits them as one ``bar-m1`` series.
Bid and ask files are two series with two keys, never one series with two columns: a row
that carries only one side cannot be half of a pair.

The quality note records what the file could not give: a file that stops before the month
does leaves ``incomplete`` set with the last minute it reaches, which is the "2025 ask file
incomplete" flag the plan's card shows.

Stamps are converted once, here (LD-03, LD-16). An epoch count's unit is read from its
magnitude by the stamp check, and wall-clock text is read in the source's own zone, ``clock``
(a broker export in GMT+2 is ``Etc/GMT-2``), so the store holds UTC whatever the file wrote.
Given ``open_at``, the month is checked against its market's open time first, and an empty
open hour holds the month open (LD-01).
"""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Final, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from qmf.core import Ok, Result, is_refusal
from qmf.data.importers.quality import OpenAt, QualityReport, check_month
from qmf.data.importers.stamps import WALL, Seam, SourceClock, StampCheck, StampUnit
from qmf.data.series import BAR_KIND, CommitReceipt, SeriesKey, SeriesStore
from qmf.data.store.engines.typed import PRICE_SCALE
from qmf.data.store.refusals import invalid_input

__all__ = ["CsvBars", "CsvImport", "import_csv_month"]

RISK_LAB_SOURCE: Final[str] = "risk-lab"
NS_PER_MS: Final[int] = 1_000_000
MS_PER_MINUTE: Final[int] = 60_000
_TIME_NAMES: Final[tuple[str, ...]] = ("time", "timestamp", "datetime", "date")
_PRICE_NAMES: Final[tuple[str, ...]] = ("open", "high", "low", "close")
_VOLUME_NAMES: Final[tuple[str, ...]] = ("volume", "vol")
_ISO: Final[re.Pattern[str]] = re.compile(
    r"(?P<year>\d{4})[-.](?P<month>\d{2})[-.](?P<day>\d{2})[ T]"
    r"(?P<hour>\d{2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?"
)
_EPOCH: Final[re.Pattern[str]] = re.compile(r"\d{9,20}")
_Bar = tuple[int, int, int, int, int, float | None]
_UTC_MS: Final = SourceClock("UTC", "ms")


@dataclass(frozen=True, slots=True)
class CsvBars:
    """One risk-lab one-minute file and the series it is one side of."""

    path: Path
    subject: str
    year: int
    month: int
    variant: str = "bid"
    source: str = RISK_LAB_SOURCE
    clock: str = "UTC"
    """The zone the file's wall-clock stamps are written in."""

    def rows(self) -> Iterator[tuple[int, int, int, int, int, float | None]]:
        """The file's bars in time order, stamps in UTC epoch ms, prices scaled to int64."""
        bars, _, _ = _stamped(self.path, self.clock)
        yield from sorted(bars, key=lambda bar: bar[0])


@dataclass(frozen=True, slots=True)
class CsvImport:
    """What one month's CSV import landed, with the note its card shows."""

    key: SeriesKey
    receipt: CommitReceipt
    last_t: int | None
    missing_tail_minutes: int
    redownloadable: bool = False
    clock: SourceClock = _UTC_MS
    seams: tuple[Seam, ...] = ()
    checked: QualityReport | None = None
    """The data-quality check's report, when the import was given its market's open time."""

    @property
    def incomplete(self) -> bool:
        """True when the file stops before the month does."""
        return self.missing_tail_minutes > 0

    @property
    def quality(self) -> dict[str, object]:
        """The note a ``dataset`` card carries for this month."""
        note: dict[str, object] = {
            "rows": self.receipt.rows,
            "gaps": list(self.receipt.gaps),
            "frozen": self.receipt.frozen,
            "missing_tail_minutes": self.missing_tail_minutes,
        }
        if self.last_t is not None:
            note["last"] = _iso(self.last_t)
        if self.incomplete:
            note["incomplete"] = f"the {self.key.year:04d}-{self.key.month:02d} file is incomplete"
        if self.checked is not None:
            note["checked"] = self.checked.as_json()
        return note


def _iso(t_ms: int) -> str:
    return datetime.fromtimestamp(t_ms // 1000, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _named(fields: dict[str, str], names: Sequence[str]) -> str | None:
    for name in names:
        for key, value in fields.items():
            if key.strip().lower() == name:
                return value
    return None


def _wall_ms(text: str, zone: ZoneInfo) -> int:
    """Wall-clock text written in ``zone`` as UTC epoch milliseconds."""
    match = _ISO.search(text)
    if match is None:
        raise ValueError(f"{text!r} is not a one-minute timestamp")
    moment = datetime(
        int(match["year"]),
        int(match["month"]),
        int(match["day"]),
        int(match["hour"]),
        int(match["minute"]),
        int(match["second"] or 0),
        tzinfo=zone,
    )
    return int(moment.timestamp()) * 1000


def _price(text: str) -> int:
    try:
        scaled = Decimal(text.strip()) * PRICE_SCALE
    except InvalidOperation as exc:
        raise ValueError(f"{text!r} is not a price") from exc
    return int(scaled.to_integral_value(rounding=ROUND_HALF_UP))


def _parsed(path: Path) -> list[tuple[str, int, int, int, int, float | None]]:
    """The file's bars in file order, each stamp as its text."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        names = list(reader.fieldnames or [])
        if not names:
            raise ValueError(f"{path.name} has no header row")
        bars: list[tuple[str, int, int, int, int, float | None]] = []
        for fields in reader:
            stamp = _named(fields, _TIME_NAMES)
            if stamp is None or stamp.strip() == "":
                continue
            prices = [(_named(fields, (name,)) or "").strip() for name in _PRICE_NAMES]
            if any(price == "" for price in prices):
                continue
            open_, high, low, close = (_price(price) for price in prices)
            volume_text = _named(fields, _VOLUME_NAMES)
            volume = (
                None if volume_text is None or volume_text.strip() == "" else float(volume_text)
            )
            bars.append((stamp.strip(), open_, high, low, close, volume))
    return bars


def _stamped(
    path: Path, clock: str, after: StampUnit | None = None
) -> tuple[list[_Bar], SourceClock, tuple[Seam, ...]]:
    """The file's bars with UTC epoch ms stamps, the source's clock, and its seam, if any."""
    parsed = _parsed(path)
    epoch = sum(1 for row in parsed if _EPOCH.fullmatch(row[0]))
    if epoch == 0:
        try:
            zone = ZoneInfo(clock)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"the clock {clock!r} is not a time zone this machine knows") from exc
        bars = [(_wall_ms(row[0], zone), *row[1:]) for row in parsed]
        return bars, SourceClock(clock, WALL), ()
    if epoch != len(parsed):
        raise ValueError(f"{path.name} mixes epoch counts and wall-clock text")
    check = StampCheck(zone=clock, after=after)
    converted = check.file(path.name, [(int(row[0]), *row[1:]) for row in parsed])
    if is_refusal(converted):
        raise ValueError(str(converted.context.get("reason", "the stamps did not check")))
    return cast("list[_Bar]", converted.value), check.clock, check.seams


def import_csv_month(
    store: SeriesStore,
    bars: CsvBars,
    *,
    correction: str | None = None,
    provider_checksum: str | None = None,
    after: StampUnit | None = None,
    open_at: OpenAt | None = None,
    confirmed: Iterable[int] = (),
) -> Result[CsvImport]:
    """Import one side of one month as one ``bar-m1`` series, through the store's commit.

    ``after`` is the unit the series' previous month was stamped in, so a change at the month
    boundary is a seam. Given ``open_at``, the month is checked against open time first, and an
    empty open hour not in ``confirmed`` keeps the month open.
    """
    built = SeriesKey.try_create(
        bars.source, bars.subject, BAR_KIND, bars.year, bars.month, bars.variant
    )
    if is_refusal(built):
        return built
    key = built.value
    try:
        stamped, clock, seams = _stamped(bars.path, bars.clock, after)
    except (OSError, ValueError) as exc:
        return invalid_input("path", f"the CSV did not read: {exc}", path=str(bars.path))
    if not stamped:
        return invalid_input(
            "path", "the CSV holds no usable bar", path=str(bars.path), key=key.text
        )
    checked = (
        None
        if open_at is None
        else check_month(
            (row[0] for row in stamped),
            start_ms=key.start_ns // NS_PER_MS,
            end_ms=key.end_ns // NS_PER_MS,
            open_at=open_at,
            confirmed=confirmed,
        )
    )
    rows = sorted(stamped, key=lambda bar: bar[0])
    receipt = store.commit(
        key,
        rows,
        correction=correction,
        provider_checksum=provider_checksum,
        hold=None if checked is None else checked.hold,
    )
    if is_refusal(receipt):
        return receipt
    last_t = rows[-1][0]
    tail = (key.end_ns // NS_PER_MS - last_t) // MS_PER_MINUTE - 1
    return Ok(
        CsvImport(
            key=key,
            receipt=receipt.value,
            last_t=last_t,
            missing_tail_minutes=max(0, tail),
            clock=clock,
            seams=seams,
            checked=checked,
        )
    )
