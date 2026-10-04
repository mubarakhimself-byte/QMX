"""Actual QMF archive admission, immutable correction and reopened query."""

from pathlib import Path

from qmf.core import WriterId, is_ok, is_refusal
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore
from qmf.venue.spot import SpotMarket
from qmn.venue.spot_recorded import RecordedSpotSource
from test_spot_paper_slice import market


def test_recorded_tick_archive_correction_and_reopen(tmp_path: Path) -> None:
    parsed = SpotMarket.from_ccxt_market(market(), precision_mode="TICK_SIZE")
    assert is_ok(parsed)
    writer = WriterId("local", "recorded-spot", "recorded:crypto", "fixture-epoch")
    source = RecordedSpotSource(
        SourceObservationBoundary(EvidenceStore(tmp_path)),
        writer,
        "source:synthetic-spot",
        "recorded:crypto",
        parsed.value,
    )
    payload = {
        "origin": "synthetic",
        "bid": "99.00",
        "ask": "100.00",
        "event_ns": 1000,
        "received_ns": 1001,
        "sequence": 1,
        "quantity": "0.100",
        "snapshot": True,
    }
    original = source.ingest(payload, native_id="tick:1", revision="v1", writer_sequence=0)
    assert is_ok(original), original
    duplicate = source.ingest(payload, native_id="tick:1", revision="v1", writer_sequence=0)
    assert is_ok(duplicate)
    assert duplicate.value.observation_fingerprint == original.value.observation_fingerprint
    corrected = source.ingest(
        {**payload, "ask": "101.00", "received_ns": 1002},
        native_id="tick:1",
        revision="v2",
        writer_sequence=1,
        correction_of=original.value.observation_fingerprint,
    )
    assert is_ok(corrected)
    assert corrected.value.observation_fingerprint != original.value.observation_fingerprint
    source = RecordedSpotSource(
        SourceObservationBoundary(EvidenceStore(tmp_path)),
        writer,
        "source:synthetic-spot",
        "recorded:crypto",
        parsed.value,
    )
    read = source.query(original.value.archive.fingerprint)
    assert is_ok(read) and read.value.market_data is not None
    assert read.value.market_data.provenance["raw_tick"] == payload
    assert is_refusal(
        source.boundary.read(
            original.value.archive.fingerprint, in_world="replay", for_world="live"
        )
    )
