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
"""

from __future__ import annotations

import csv
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Final

from qmf.core import Ok, Result, is_refusal
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


@dataclass(frozen=True, slots=True)
class CsvBars:
    """One risk-lab one-minute file and the series it is one side of."""

    path: Path
    subject: str
    year: int
    month: int
    variant: str = "bid"
    source: str = RISK_LAB_SOURCE

    def rows(self) -> Iterator[tuple[int, int, int, int, int, float | None]]:
        """The file's bars in time order, prices scaled to int64, volume nullable."""
        bars = sorted(_parsed(self.path), key=lambda bar: bar[0])
        yield from bars


@dataclass(frozen=True, slots=True)
class CsvImport:
    """What one month's CSV import landed, with the note its card shows."""

    key: SeriesKey
    receipt: CommitReceipt
    last_t: int | None
    missing_tail_minutes: int
    redownloadable: bool = False

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
        return note


def _iso(t_ms: int) -> str:
    return datetime.fromtimestamp(t_ms // 1000, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _named(fields: dict[str, str], names: Sequence[str]) -> str | None:
    for name in names:
        for key, value in fields.items():
            if key.strip().lower() == name:
                return value
    return None


def _timestamp(text: str) -> int:
    """A CSV timestamp as int64 epoch milliseconds (UTC)."""
    stripped = text.strip()
    if re.fullmatch(r"\d{10}", stripped):
        return int(stripped) * 1000
    if re.fullmatch(r"\d{13}", stripped):
        return int(stripped)
    match = _ISO.search(stripped)
    if match is None:
        raise ValueError(f"{stripped!r} is not a one-minute timestamp")
    second = int(match["second"] or 0)
    moment = datetime(
        int(match["year"]),
        int(match["month"]),
        int(match["day"]),
        int(match["hour"]),
        int(match["minute"]),
        second,
        tzinfo=UTC,
    )
    return int(moment.timestamp()) * 1000


def _price(text: str) -> int:
    try:
        scaled = Decimal(text.strip()) * PRICE_SCALE
    except InvalidOperation as exc:
        raise ValueError(f"{text!r} is not a price") from exc
    return int(scaled.to_integral_value(rounding=ROUND_HALF_UP))


def _parsed(path: Path) -> list[tuple[int, int, int, int, int, float | None]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        names = list(reader.fieldnames or [])
        if not names:
            raise ValueError(f"{path.name} has no header row")
        bars: list[tuple[int, int, int, int, int, float | None]] = []
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
            bars.append((_timestamp(stamp), open_, high, low, close, volume))
    return bars


def import_csv_month(
    store: SeriesStore,
    bars: CsvBars,
    *,
    correction: str | None = None,
    provider_checksum: str | None = None,
) -> Result[CsvImport]:
    """Import one side of one month as one ``bar-m1`` series, through the store's commit."""
    built = SeriesKey.try_create(
        bars.source, bars.subject, BAR_KIND, bars.year, bars.month, bars.variant
    )
    if is_refusal(built):
        return built
    key = built.value
    try:
        rows = list(bars.rows())
    except (OSError, ValueError) as exc:
        return invalid_input("path", f"the CSV did not read: {exc}", path=str(bars.path))
    if not rows:
        return invalid_input(
            "path", "the CSV holds no usable bar", path=str(bars.path), key=key.text
        )
    receipt = store.commit(key, rows, correction=correction, provider_checksum=provider_checksum)
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
        )
    )
