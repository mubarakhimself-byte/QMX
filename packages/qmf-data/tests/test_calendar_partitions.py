"""The calendar's bitemporal partitions: a revision in an open month is an append (W14).

The month is open while its own month has not ended, so the store writes it again under the
open name and the rows only ever grow. A revision is a second row under the same provider-native
id, never a rewrite of the first, which is what lets a downstream reader see what was known when.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qmf.core import is_ok
from qmf.data.calendar_feed import CalendarEvent, calendar_key, land_calendar
from qmf.data.series import SeriesStore

MONTH = (2026, 10)
NOW = datetime(2026, 10, 15, tzinfo=UTC)
OCT_02 = int(datetime(2026, 10, 2, 9, 0, tzinfo=UTC).timestamp() * 1_000_000_000)
OCT_09 = int(datetime(2026, 10, 9, 9, 0, tzinfo=UTC).timestamp() * 1_000_000_000)
OCT_30 = int(datetime(2026, 10, 30, 12, 30, tzinfo=UTC).timestamp() * 1_000_000_000)


def event(
    native: str,
    revision: str,
    *,
    at: int,
    known_at: int,
    impact: str = "High",
    currency: str = "USD",
    title: str = "Non-Farm Payrolls",
) -> CalendarEvent:
    return CalendarEvent(
        source="news-calendar",
        source_native_id=native,
        revision=revision,
        event_time_ns=at,
        known_at_ns=known_at,
        impact_label=impact,
        currency=currency,
        title=title,
    )


def test_a_revision_in_an_open_month_is_an_append(tmp_path: Path) -> None:
    store = SeriesStore(tmp_path / "series", wall=lambda: NOW)
    built = calendar_key(*MONTH)
    assert is_ok(built)
    key = built.value
    first = land_calendar(store, key, [event("us-nfp", "r1", at=OCT_02, known_at=OCT_02)])
    second = land_calendar(
        store,
        key,
        [
            event("us-nfp", "r1", at=OCT_02, known_at=OCT_02),
            event("us-nfp", "r2", at=OCT_30, known_at=OCT_09),
        ],
    )

    assert is_ok(first) and first.value is not None
    assert is_ok(second) and second.value is not None
    assert (first.value.rows, first.value.frozen) == (1, False)
    assert (second.value.rows, second.value.frozen) == (2, False)
    read = store.read(key)
    assert is_ok(read)
    assert [(row["source_native_id"], row["revision"]) for row in read.value.rows] == [
        ("us-nfp", "r1"),
        ("us-nfp", "r2"),
    ]
    assert read.value.rows[1]["impact"] == "High"


def test_the_same_rows_again_write_one_file(tmp_path: Path) -> None:
    store = SeriesStore(tmp_path / "series", wall=lambda: NOW)
    built = calendar_key(*MONTH)
    assert is_ok(built)
    key = built.value
    one = event("us-nfp", "r1", at=OCT_02, known_at=OCT_02)
    first = land_calendar(store, key, [one])
    again = land_calendar(store, key, [one])

    assert is_ok(first) and first.value is not None
    assert is_ok(again) and again.value is not None
    assert again.value.fingerprint == first.value.fingerprint
    assert sorted(path.name for path in store.folder(key).glob("*.parquet")) == ["open.parquet"]
