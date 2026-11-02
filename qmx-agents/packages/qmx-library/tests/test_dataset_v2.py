"""The `dataset` card at version 2: its clock, seams, stitching, rolls and calendar (B11, AD-212).

The version adds optional fields only, so a card landed at version 1 still reads as it was
written, and a version 2 card that misnames a seam is refused by the kind's schema.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qmx_engine.ledger import redact

from qmx_library import store as store_module
from qmx_library.cards import Partition, SeriesCard, card_fields, write_card
from qmx_library.kinds import Kind, kind
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")
SEAM = {
    "kind": "stamp_unit",
    "at": "2025-01-01T00:00:00.000Z",
    "at_ms": 1_735_689_600_000,
    "before": "ms",
    "after": "us",
}


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(
        tmp_path / "library", redactor=redact, wall=lambda: datetime(2026, 11, 2, tzinfo=UTC)
    ) as opened:
        yield opened


def card() -> SeriesCard:
    return SeriesCard("binance", "BTCUSDT", "trades", licence="binance-public-data")


def test_a_card_landed_at_version_1_reads_unchanged_at_version_2(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    current = kind("dataset")
    version_1 = replace(current, schema_version=1)

    def as_landed(name: str) -> Kind:
        return version_1 if name == "dataset" else kind(name)

    monkeypatch.setattr(store_module, "kind", as_landed)
    fields = card_fields(card(), (Partition(2024, 12, "a" * 64, 44_640, True),))
    landed = write_card(store, OPERATOR, card(), (Partition(2024, 12, "a" * 64, 44_640, True),))
    monkeypatch.undo()

    assert current.schema_version == 2
    assert store.can_read("dataset", 1)
    assert dict(store.get(OPERATOR, landed.object_id).fields) == fields


def test_a_version_2_card_carries_its_clock_seams_stitching_rolls_and_calendar(
    store: Store,
) -> None:
    facts = {
        "source_clock": {"zone": "UTC", "unit": "us"},
        "seams": [SEAM],
        "stitching": {"method": "contract-by-contract", "adjusted": False},
        "rolls": [{"at": "2025-03-14T00:00:00Z", "from": "ESH5", "to": "ESM5"}],
        "calendar": {"ref": "cme-equity@1", "record": "ES@1"},
    }
    fields = {**card_fields(card()), **facts}

    put = store.put(
        OPERATOR,
        Draft("dataset", card().item, card().title, fields=fields),
        on="main",
        expected_head=None,
    )
    read = store.get(OPERATOR, put.object_id).fields

    assert {name: read[name] for name in facts} == facts


def test_a_seam_of_no_known_kind_is_refused(store: Store) -> None:
    fields = {**card_fields(card()), "seams": [{**SEAM, "kind": "zone"}]}

    with pytest.raises(LibraryRefused, match=r"^schema_invalid:"):
        store.put(
            OPERATOR,
            Draft("dataset", card().item, card().title, fields=fields),
            on="main",
            expected_head=None,
        )
