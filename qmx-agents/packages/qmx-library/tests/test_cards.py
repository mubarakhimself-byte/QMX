"""One dataset card per price series, its claim on the key, and the correction mark (W9)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from qmx_engine.ledger import redact

from qmx_library.cards import (
    Correction,
    Partition,
    SeriesCard,
    card_fields,
    read_range,
    write_card,
)
from qmx_library.port import Draft, LibraryRefused, Relation
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")
START = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)
MARCH_2024 = (1_709_251_200_000_000_000, 1_711_929_600_000_000_000)
YEAR_2019 = (1_546_300_800_000_000_000, 1_577_836_800_000_000_000)


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    clock = Clock()
    with Store.open(tmp_path / "library", redactor=redact, wall=clock) as opened:
        yield opened


def ticks_card() -> SeriesCard:
    return SeriesCard(
        "dukascopy",
        "EURUSD",
        "ticks",
        licence="internal-only",
        world="live",
        redownloadable=True,
    )


def put_result(store: Store, item: str, card_id: str, series: str, span: tuple[int, int]) -> str:
    fields = {"outcome": "inconclusive", "reads": [read_range(series, *span)]}
    relations: list[Relation] = [("consumed", card_id)]
    draft = Draft("backtest-result", item, item, fields=fields, relations=relations)
    head = store.head(item, "main")
    expected = None if head is None else head[0]
    return store.put(OPERATOR, draft, on="main", expected_head=expected).object_id


def test_a_card_lists_its_partitions_and_claims_the_series_key(store: Store) -> None:
    card = ticks_card()
    january = Partition(2024, 1, "a" * 64, 100, True)
    february = Partition(2024, 2, "b" * 64, 50, False)
    first = write_card(store, OPERATOR, card, (january, february))

    assert (first.created, first.claimed, first.series) == (True, True, "dukascopy/EURUSD/ticks/-")
    fields = store.get(OPERATOR, first.object_id).fields
    assert fields["series_key"] == "dukascopy/EURUSD/ticks/-"
    assert fields["coverage"] == {
        "months": 2,
        "rows": 150,
        "frozen": 1,
        "first": "2024-01",
        "last": "2024-02",
    }
    months = fields["partitions"]
    assert isinstance(months, list)
    assert [entry["month"] for entry in months if isinstance(entry, dict)] == [
        "2024-01",
        "2024-02",
    ]
    assert fields["partition_digests"] == ["a" * 64, "b" * 64]
    assert (fields["licence"], fields["redownloadable"]) == ("internal-only", True)

    same = write_card(store, OPERATOR, card, (january, february))
    assert (same.object_id, same.claimed) == (first.object_id, False)


def test_a_second_writer_for_the_same_series_key_is_refused(store: Store) -> None:
    card = ticks_card()
    write_card(store, OPERATOR, card, (Partition(2024, 1, "a" * 64, 100, True),))
    stale = Draft("dataset", card.item, card.title, fields=card_fields(card))
    with pytest.raises(LibraryRefused, match=r"^stale_head:"):
        store.put(OPERATOR, stale, on="main", expected_head=None)


def test_a_correction_marks_only_the_reader_whose_range_overlaps(store: Store) -> None:
    card = ticks_card()
    january = Partition(2024, 1, "a" * 64, 100, True)
    first = write_card(store, OPERATOR, card, (january,))
    march = put_result(store, "res-march", first.object_id, card.series, MARCH_2024)
    older = put_result(store, "res-2019", first.object_id, card.series, YEAR_2019)
    assert store.marks(OPERATOR, march).worst is None

    march_month = Partition(2024, 3, "c" * 64, 20, True)
    write_card(store, OPERATOR, card, (january, march_month))
    assert store.marks(OPERATOR, march).worst is None
    assert store.marks(OPERATOR, older).worst is None

    corrected = Partition(2024, 3, "d" * 64, 21, True)
    write_card(
        store,
        OPERATOR,
        card,
        (january, corrected),
        (Correction(*MARCH_2024, "c" * 64, "d" * 64, "late fill", START.isoformat()),),
    )
    assert store.marks(OPERATOR, march).worst == "corrected"
    assert store.marks(OPERATOR, march).path == (march, first.object_id)
    assert store.marks(OPERATOR, older).worst is None
