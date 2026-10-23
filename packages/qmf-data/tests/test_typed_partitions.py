"""Typed price partitions: the streamed fingerprint, the key and the freeze rules (W9)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qmf.core import RefusalCategory, is_ok, is_refusal
from qmf.data.importers import CsvBars, import_csv_month
from qmf.data.series import SeriesKey, SeriesStore
from qmf.data.store.engines.typed import TICK_COLUMNS, TypedWriter

JANUARY_2024 = 1_704_067_200_000  # 2024-01-01T00:00:00Z in epoch ms
HOUR_MS = 3_600_000
DAY_MS = 86_400_000
NOW = datetime(2026, 10, 23, tzinfo=UTC)


def store(tmp_path: Path) -> SeriesStore:
    return SeriesStore(tmp_path / "series", wall=lambda: NOW)


def key(
    source: str = "dukascopy",
    kind: str = "ticks",
    month: int = 1,
    variant: str = "",
    year: int = 2024,
) -> SeriesKey:
    built = SeriesKey.try_create(source, "EURUSD", kind, year, month, variant)
    assert is_ok(built)
    return built.value


def ticks(start_ms: int, count: int) -> list[tuple[int, int, int, float, float]]:
    return [
        (start_ms + index * 1000, 108_000 + index, 108_012 + index, 0.5, 0.25)
        for index in range(count)
    ]


def parquet_files(folder: Path) -> list[str]:
    return sorted(path.name for path in folder.glob("*.parquet"))


def test_two_writes_of_the_same_rows_give_the_same_fingerprint_and_one_file(
    tmp_path: Path,
) -> None:
    rows = ticks(JANUARY_2024 + 9 * HOUR_MS, 5)
    series_key = key()
    first = TypedWriter(tmp_path / "a.parquet", series_key.text, TICK_COLUMNS).add(rows).finish()
    second = TypedWriter(tmp_path / "b.parquet", series_key.text, TICK_COLUMNS).add(rows).finish()
    assert first.fingerprint == second.fingerprint

    series = store(tmp_path)
    committed = series.commit(series_key, rows)
    again = series.commit(series_key, rows)
    assert is_ok(committed) and is_ok(again)
    assert committed.value.fingerprint == first.fingerprint
    assert (again.value.idempotent, again.value.fingerprint) == (True, first.fingerprint)
    assert parquet_files(series.folder(series_key)) == [f"{first.fingerprint}.parquet"]

    read = series.read(series_key)
    assert is_ok(read)
    assert [row["t"] for row in read.value.rows] == [row[0] for row in rows]


def test_bid_m1_and_ask_m1_get_different_keys_and_two_files(tmp_path: Path) -> None:
    series = store(tmp_path)
    bid = key(source="risk-lab", kind="bar-m1", variant="bid")
    ask = key(source="risk-lab", kind="bar-m1", variant="ask")
    assert bid.text != ask.text
    assert (bid.series, ask.series) == ("risk-lab/EURUSD/bar-m1/bid", "risk-lab/EURUSD/bar-m1/ask")

    bars = [(JANUARY_2024 + 60_000, 108_000, 108_010, 107_990, 108_005, 12.0)]
    assert is_ok(series.commit(bid, bars))
    assert is_ok(series.commit(ask, bars))
    assert len(parquet_files(series.folder(bid))) == 1
    assert len(parquet_files(series.folder(ask))) == 1
    assert series.folder(bid) != series.folder(ask)


def test_a_different_file_for_a_frozen_key_is_refused_without_the_correction_mark(
    tmp_path: Path,
) -> None:
    series = store(tmp_path)
    frozen = key()
    assert is_ok(series.commit(frozen, ticks(JANUARY_2024 + 9 * HOUR_MS, 5)))
    state = series.state(frozen)
    assert state is not None and state.frozen is True

    late = ticks(JANUARY_2024 + 9 * HOUR_MS + DAY_MS, 1)
    refused = series.commit(frozen, late)
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["key"] == "dukascopy/EURUSD/ticks/-/2024-01"
    assert parquet_files(series.folder(frozen)) == [f"{state.fingerprint}.parquet"]

    fixed = series.commit(frozen, late, correction="late fill for January")
    assert is_ok(fixed)
    assert (fixed.value.correction, fixed.value.frozen) == (True, True)
    after = series.state(frozen)
    assert after is not None
    assert [(item.old, item.new) for item in after.corrections] == [
        (state.fingerprint, fixed.value.fingerprint)
    ]
    assert after.corrections[0].reason == "late fill for January"


def test_a_ticks_month_with_a_gap_freezes_after_one_re_fetch_returns_it(
    tmp_path: Path,
) -> None:
    series = store(tmp_path)
    gapped = key(month=2)
    start = JANUARY_2024 + 30 * DAY_MS + 9 * HOUR_MS
    rows = [
        (start, 1, 2, 0.1, 0.1),
        (start + 2 * HOUR_MS, 3, 4, 0.1, 0.1),
    ]
    first = series.commit(gapped, rows)
    assert is_ok(first)
    assert (first.value.frozen, first.value.attempts) == (False, 1)
    assert first.value.gaps == ("2024-01-31T09:00:00.000Z/2024-01-31T11:00:00.000Z",)

    again = series.commit(gapped, rows)
    assert is_ok(again)
    assert (again.value.frozen, again.value.attempts) == (True, 2)
    assert again.value.gaps == first.value.gaps
    assert parquet_files(series.folder(gapped)) == [f"{again.value.fingerprint}.parquet"]


def test_a_fill_after_the_freeze_lands_as_a_correction_listing_both_fingerprints(
    tmp_path: Path,
) -> None:
    series = store(tmp_path)
    fills = key(source="risk-lab", kind="fill", month=3, variant="")
    bars = [(1_709_251_200_000 + 60_000, 108_000, 108_010, 107_990, 108_005, None)]
    first = series.commit(fills, bars)
    assert is_ok(first)
    assert first.value.frozen is True
    old = series.state(fills)
    assert old is not None and old.frozen is True

    late = [(1_709_251_200_000 + 120_000, 108_010, 108_020, 108_000, 108_015, 3.0)]
    fixed = series.commit(fills, late, correction="broker fill arrived after settlement")
    assert is_ok(fixed)
    after = series.state(fills)
    assert after is not None
    assert [(item.old, item.new) for item in after.corrections] == [
        (old.fingerprint, fixed.value.fingerprint)
    ]
    assert after.corrections[0].reason == "broker fill arrived after settlement"


def test_the_csv_importer_lands_one_side_of_a_month_with_its_quality_note(tmp_path: Path) -> None:
    source = tmp_path / "eurusd-bid-2024-01.csv"
    source.write_text(
        "time,open,high,low,close,volume\n"
        "2024-01-01 00:00:00,1.10400,1.10420,1.10390,1.10410,12.5\n"
        "2024-01-01 00:01:00,1.10410,1.10430,1.10400,1.10425,10.0\n",
        encoding="utf-8",
    )
    series = store(tmp_path)
    built = CsvBars(source, "EURUSD", 2024, 1, "bid")
    imported = import_csv_month(series, built)
    assert is_ok(imported)
    assert imported.value.key.text == "risk-lab/EURUSD/bar-m1/bid/2024-01"
    assert imported.value.receipt.rows == 2
    assert imported.value.last_t == 1_704_067_260_000
    assert imported.value.quality["incomplete"] == "the 2024-01 file is incomplete"
    read = series.read(imported.value.key)
    assert is_ok(read)
    assert [row["open"] for row in read.value.rows] == [110_400, 110_410]
