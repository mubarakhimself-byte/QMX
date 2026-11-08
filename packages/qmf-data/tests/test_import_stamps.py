"""Imports check stamps, state their clock, and hold a month with an empty open hour (B11).

A file's time unit is read from the magnitude of its stamps and converted once to UTC epoch
milliseconds (LD-03), wall-clock text is read in the source's own zone (LD-16), a change of
unit or cadence is a seam on the card (LD-04), and an hour wholly inside open time with no row
keeps the month open until a retry and a second source agree that it was empty (LD-01).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qmf.core import is_ok, is_refusal
from qmf.data.importers import CsvBars, import_csv_month
from qmf.data.importers.quality import check_month
from qmf.data.importers.stamps import ClockLedger, StampCheck, StampUnit
from qmf.data.series import SeriesStore

JANUARY_2025 = 1_735_689_600_000
"""2025-01-01T00:00:00Z in epoch ms."""
JANUARY_2024 = 1_704_067_200_000
MINUTE_MS = 60_000
HOUR_MS = 3_600_000
NOW = datetime(2026, 10, 23, tzinfo=UTC)


def csv_file(path: Path, stamps: list[str]) -> Path:
    lines = ["time,open,high,low,close,volume"]
    lines += [f"{stamp},1.10400,1.10420,1.10390,1.10410,1" for stamp in stamps]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_a_microsecond_file_after_a_millisecond_month_lands_with_its_seam(tmp_path: Path) -> None:
    stamps = [str((JANUARY_2025 + i * MINUTE_MS) * 1000) for i in range(3)]
    source = csv_file(tmp_path / "btcusdt-2025-01.csv", stamps)
    series = SeriesStore(tmp_path / "series", wall=lambda: NOW)

    imported = import_csv_month(
        series, CsvBars(source, "BTCUSDT", 2025, 1, "trade"), after=StampUnit.MILLIS
    )

    assert is_ok(imported)
    assert imported.value.clock.as_json() == {"zone": "UTC", "unit": "us"}
    assert [seam.as_json() for seam in imported.value.seams] == [
        {
            "kind": "stamp_unit",
            "at": "2025-01-01T00:00:00.000Z",
            "at_ms": 1_735_689_600_000,
            "before": "ms",
            "after": "us",
        }
    ]
    read = series.read(imported.value.key)
    assert is_ok(read)
    assert [row["t"] for row in read.value.rows] == [
        1_735_689_600_000,
        1_735_689_660_000,
        1_735_689_720_000,
    ]


def test_a_broker_export_in_gmt_plus_two_lands_in_utc_and_its_card_says_so(
    tmp_path: Path,
) -> None:
    source = csv_file(tmp_path / "eurusd-2024-01.csv", ["2024-01-02 02:00:00"])
    series = SeriesStore(tmp_path / "series", wall=lambda: NOW)

    imported = import_csv_month(series, CsvBars(source, "EURUSD", 2024, 1, clock="Etc/GMT-2"))

    assert is_ok(imported)
    assert imported.value.last_t == 1_704_153_600_000
    assert imported.value.clock.as_json() == {"zone": "Etc/GMT-2", "unit": "wall"}


def test_a_file_whose_ends_disagree_on_their_unit_is_refused(tmp_path: Path) -> None:
    first = str(JANUARY_2025)
    last = str((JANUARY_2025 + MINUTE_MS) * 1000)
    source = csv_file(tmp_path / "mixed.csv", [first, last])

    imported = import_csv_month(
        SeriesStore(tmp_path / "series", wall=lambda: NOW),
        CsvBars(source, "BTCUSDT", 2025, 1, "trade"),
    )

    assert is_refusal(imported)
    assert "disagree on their unit" in str(imported.context["reason"])


def test_a_cadence_change_between_files_is_a_seam_and_the_ledger_carries_it_on(
    tmp_path: Path,
) -> None:
    check = StampCheck(cadenced=True)
    one = [(JANUARY_2025 + i * 1000, 1.0, 2.0) for i in range(5)]
    two = [(JANUARY_2025 + 86_400_000 + i * 250, 1.0, 2.0) for i in range(5)]

    assert is_ok(check.file("day-1", one))
    assert is_ok(check.file("day-2", two))
    ledger = ClockLedger(tmp_path)
    ledger.record("binance/BTCUSDT/book/depth", 2025, 1, check)

    assert [seam.as_json() for seam in check.seams] == [
        {
            "kind": "cadence",
            "at": "2025-01-02T00:00:00.000Z",
            "at_ms": 1_735_776_000_000,
            "before": "1000ms",
            "after": "250ms",
        }
    ]
    assert ledger.before("binance/BTCUSDT/book/depth", 2025, 2) == (StampUnit.MILLIS, 250)
    assert ledger.before("binance/BTCUSDT/book/depth", 2025, 1) == (None, None)


def one_open_day(at_ms: int) -> bool:
    """A fixture calendar: open on 2024-01-02 only."""
    return JANUARY_2024 + 86_400_000 <= at_ms < JANUARY_2024 + 2 * 86_400_000


def day_without_its_tenth_hour(tmp_path: Path) -> Path:
    start = JANUARY_2024 + 86_400_000
    minutes = [start + i * MINUTE_MS for i in range(1440) if not 600 <= i < 660]
    return csv_file(tmp_path / "eurusd-bid-2024-01.csv", [str(stamp) for stamp in minutes])


def test_an_empty_open_hour_keeps_the_month_unfrozen_through_a_retry(tmp_path: Path) -> None:
    source = day_without_its_tenth_hour(tmp_path)
    series = SeriesStore(tmp_path / "series", wall=lambda: NOW)
    bars = CsvBars(source, "EURUSD", 2024, 1)

    first = import_csv_month(series, bars, open_at=one_open_day)
    retry = import_csv_month(series, bars, open_at=one_open_day)

    assert is_ok(first) and is_ok(retry)
    assert (first.value.receipt.frozen, retry.value.receipt.frozen) == (False, False)
    assert retry.value.receipt.attempts == 2
    assert retry.value.quality["checked"] == {
        "missing_minutes": 60,
        "gaps": [
            {"from": "2024-01-02T10:00:00.000Z", "to": "2024-01-02T11:00:00.000Z", "minutes": 60}
        ],
        "empty_open_hours": ["2024-01-02T10:00:00.000Z"],
        "unconfirmed_hours": ["2024-01-02T10:00:00.000Z"],
        "clock_jumps": [],
        "held_open": True,
    }


def test_the_same_retry_freezes_once_a_second_source_confirms_the_hour(tmp_path: Path) -> None:
    source = day_without_its_tenth_hour(tmp_path)
    series = SeriesStore(tmp_path / "series", wall=lambda: NOW)
    bars = CsvBars(source, "EURUSD", 2024, 1)
    agreed = [JANUARY_2024 + 86_400_000 + 10 * HOUR_MS]

    import_csv_month(series, bars, open_at=one_open_day, confirmed=agreed)
    retry = import_csv_month(series, bars, open_at=one_open_day, confirmed=agreed)

    assert is_ok(retry)
    assert retry.value.receipt.frozen is True
    assert retry.value.quality["checked"]["held_open"] is False  # type: ignore[index]


def test_a_clock_that_goes_back_is_listed_with_its_minutes() -> None:
    start = JANUARY_2024 + 86_400_000
    stamps = [start, start + 90 * MINUTE_MS, start + 30 * MINUTE_MS, start + 31 * MINUTE_MS]

    report = check_month(stamps, start_ms=start, end_ms=start + 2 * HOUR_MS, open_at=lambda _: True)

    assert [jump.as_json() for jump in report.jumps] == [
        {"at": "2024-01-02T00:30:00.000Z", "back_ms": 3_600_000, "minutes": 60}
    ]
    assert report.missing_minutes == 116
