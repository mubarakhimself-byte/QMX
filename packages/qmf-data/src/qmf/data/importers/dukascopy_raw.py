"""Read the old raw Dukascopy ``bi5`` hour files into one typed ticks partition (W9).

The old download left one LZMA-compressed file per market hour. The PC's copy and the server's
raw-backup copy are partitioned the way the old ingestion wrote them,
``venue=FOREX/platform=CTRADER/instrument=EURUSD/resolution=tick/date=YYYY-MM-DD/raw/HHh_ticks.bi5``,
and the provider's own tree shape, ``<symbol>/<YYYY>/<MM>/<DD>/<HH>h_ticks.bi5``, reads too.
The root may be the directory above ``instrument=`` or the instrument directory itself. Each
file is decoded through :func:`qmf.data.dukascopy.decode_bi5_ticks` — the one decoder in the
package, so the importer never grows a second reading of the format — and the ticks stream into
the typed writer in a child process. The parent holds no rows, which is what makes a month
importable without holding it.

The source is read only. Bids and asks stay as the provider's scaled integers; both sides of one
tick are one row, so ticks are one series.

A bi5 file states each tick as milliseconds from its UTC hour, so the source clock is UTC in
milliseconds by the format itself. Given ``open_at``, the written month is checked against its
market's open time before the commit, reading the time column back in batches, and an empty
open hour keeps the month open (LD-01).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Final

from qmf.core import Ok, Result, is_refusal
from qmf.data.dukascopy import DEFAULT_PRICE_SCALE, PERSONAL_USE_LICENSE, decode_bi5_ticks
from qmf.data.importers.quality import OpenAt, QualityReport, check_month, partition_stamps
from qmf.data.importers.stamps import SourceClock
from qmf.data.series import INCOMING_NAME, TICKS_KIND, CommitReceipt, SeriesKey, SeriesStore
from qmf.data.store.engines import SeriesFile, StoreEngineError
from qmf.data.store.engines.typed import TypedWriter, write_in_child
from qmf.data.store.refusals import invalid_input, translate_engine_failure

__all__ = ["DUKASCOPY_SOURCE", "RawTicks", "RawTicksImport", "import_raw_month", "raw_tick_rows"]

DUKASCOPY_SOURCE: Final[str] = "dukascopy"
NS_PER_MS: Final[int] = 1_000_000
NS_PER_SECOND: Final[int] = 1_000_000_000
_HOUR_FILE: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(
        r"(?:^|/)instrument=(?P<symbol>[^/]+)/resolution=tick/"
        r"date=(?P<date>\d{4}-\d{2}-\d{2})/raw/(?P<hour>\d{2})h_ticks\.bi5$"
    ),
    re.compile(
        r"^resolution=tick/date=(?P<date>\d{4}-\d{2}-\d{2})/raw/(?P<hour>\d{2})h_ticks\.bi5$"
    ),
    re.compile(
        r"(?:^|/)(?P<symbol>[^/]+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/"
        r"(?P<hour>\d{2})h_ticks\.bi5$"
    ),
    re.compile(r"^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<hour>\d{2})h_ticks\.bi5$"),
)


@dataclass(frozen=True, slots=True)
class RawTicks:
    """One month of the old raw hour files: where they are, and which series they are."""

    root: Path
    subject: str
    year: int
    month: int
    price_scale: int = DEFAULT_PRICE_SCALE

    def hours(self) -> tuple[tuple[int, Path], ...]:
        """Every hour file of the month as ``(hour start ns, path)``, in time order."""
        found: list[tuple[int, Path]] = []
        if not self.root.is_dir():
            return ()
        for path in self.root.rglob("*h_ticks.bi5"):
            relative = str(path.relative_to(self.root)).replace("\\", "/")
            for pattern in _HOUR_FILE:
                match = pattern.search(relative)
                if match is None:
                    continue
                symbol = match.groupdict().get("symbol")
                if symbol is not None and symbol != self.subject:
                    break
                year, month, day = _date_parts(match)
                if (year, month) != (self.year, self.month):
                    break
                hour = datetime(year, month, day, int(match["hour"]), tzinfo=UTC)
                found.append((int(hour.timestamp()) * NS_PER_SECOND, path))
                break
        return tuple(sorted(found))


def _date_parts(match: re.Match[str]) -> tuple[int, int, int]:
    """The day a matched hour file belongs to, from its date partition or from its path."""
    date = match.groupdict().get("date")
    if date is not None:
        year, month, day = (int(part) for part in date.split("-"))
        return year, month, day
    return int(match["year"]), int(match["month"]), int(match["day"])


@dataclass(frozen=True, slots=True)
class RawTicksImport:
    """What one month's import landed: its key, its receipt, and its quality note."""

    key: SeriesKey
    receipt: CommitReceipt
    hours: int
    licence: str = PERSONAL_USE_LICENSE
    redownloadable: bool = True
    checked: QualityReport | None = None
    """The data-quality check's report, when the import was given its market's open time."""

    @property
    def clock(self) -> SourceClock:
        return SourceClock("UTC", "ms")

    @property
    def quality(self) -> dict[str, object]:
        """The note a ``dataset`` card carries for this month."""
        note: dict[str, object] = {
            "hours": self.hours,
            "rows": self.receipt.rows,
            "gaps": list(self.receipt.gaps),
            "frozen": self.receipt.frozen,
        }
        if self.checked is not None:
            note["checked"] = self.checked.as_json()
        return note


def raw_tick_rows(
    files: Sequence[tuple[int, Path]],
) -> Iterator[tuple[int, int, int, float, float]]:
    """Stream one month's ticks: int64 epoch ms, int64 bid, int64 ask, the volumes.

    Runs in the writer's child process, so this is a module-level function on purpose. A
    payload the decoder refuses stops the stream with the file named, never a silently short
    month.
    """
    for hour_start_ns, path in files:
        payload = path.read_bytes()
        decoded = decode_bi5_ticks(payload, hour_start_ns=hour_start_ns)
        if is_refusal(decoded):
            reason = decoded.context.get("reason", "the payload is not a bi5 tick file")
            raise ValueError(f"{path.name}: {reason}")
        for tick in decoded.value:
            yield (
                tick.event_time_ns // NS_PER_MS,
                tick.bid_verbatim,
                tick.ask_verbatim,
                tick.bid_volume,
                tick.ask_volume,
            )


def import_raw_month(
    store: SeriesStore,
    raw: RawTicks,
    *,
    correction: str | None = None,
    writer: Callable[..., SeriesFile] | None = None,
    open_at: OpenAt | None = None,
    confirmed: Iterable[int] = (),
) -> Result[RawTicksImport]:
    """Import one month of raw ticks through the store's commit, in a child by default.

    Given ``open_at``, an empty open hour not in ``confirmed`` keeps the month open.
    """
    built = SeriesKey.try_create(DUKASCOPY_SOURCE, raw.subject, TICKS_KIND, raw.year, raw.month)
    if is_refusal(built):
        return built
    key = built.value
    files = raw.hours()
    if not files:
        return invalid_input(
            "root",
            "no hour files of this month are under the source root",
            root=str(raw.root),
            subject=raw.subject,
            month=f"{raw.year:04d}-{raw.month:02d}",
        )
    folder = store.folder(key)
    folder.mkdir(parents=True, exist_ok=True)
    temp = folder / INCOMING_NAME
    write = writer if writer is not None else write_in_child
    try:
        written = write(
            temp,
            key.text,
            key.rule.columns,
            partial(raw_tick_rows, files),
            hole_bounds=key.rule.hole_bounds,
        )
    except ValueError as exc:
        temp.unlink(missing_ok=True)
        return invalid_input("payload", f"a raw hour file did not decode: {exc}", key=key.text)
    except StoreEngineError as exc:
        temp.unlink(missing_ok=True)
        return translate_engine_failure(exc)
    checked = (
        None
        if open_at is None
        else check_month(
            partition_stamps(written.path),
            start_ms=key.start_ns // NS_PER_MS,
            end_ms=key.end_ns // NS_PER_MS,
            open_at=open_at,
            confirmed=confirmed,
        )
    )
    receipt = store.commit_file(
        key, written, correction=correction, hold=None if checked is None else checked.hold
    )
    if is_refusal(receipt):
        return receipt
    return Ok(RawTicksImport(key=key, receipt=receipt.value, hours=len(files), checked=checked))


def import_raw_month_in_process(
    store: SeriesStore,
    raw: RawTicks,
    *,
    correction: str | None = None,
    open_at: OpenAt | None = None,
    confirmed: Iterable[int] = (),
) -> Result[RawTicksImport]:
    """The same import without a child process: the tests and a handful of hours use this."""
    return import_raw_month(
        store,
        raw,
        correction=correction,
        writer=_writer_in_process,
        open_at=open_at,
        confirmed=confirmed,
    )


def _writer_in_process(
    target: Path,
    key: str,
    columns: Sequence[str],
    rows: Callable[[], Iterator[Sequence[object]]],
    *,
    hole_bounds: tuple[int, int] | None = None,
) -> SeriesFile:
    return TypedWriter(target, key, columns, hole_bounds=hole_bounds).add(rows()).finish()
