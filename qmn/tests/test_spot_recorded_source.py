"""Actual QMF archive admission, immutable correction and reopened query."""

from pathlib import Path

from qmf.core import WriterId, is_ok, is_refusal
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore
from qmf.venue.spot import SpotMarket
from qmn.venue.spot_recorded import RecordedSpotSource
from test_spot_paper_slice import market, open_account


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
    account = open_account(tmp_path / "paper")
    assert is_ok(account)
    try:
        assert is_ok(source.replay_into(account.value, original.value.archive.fingerprint))
        assert account.value.query()["feed_status"] == "READY"
    finally:
        account.value.close()
    assert is_refusal(
        source.boundary.read(
            original.value.archive.fingerprint, in_world="replay", for_world="live"
        )
    )


def test_replay_rejects_raw_tick_that_disagrees_with_ct10_time(tmp_path: Path) -> None:
    from qmf.data.observation import MarketDataContext, SourceObservation

    account = open_account(tmp_path / "paper")
    assert is_ok(account)
    writer = WriterId("local", "recorded-spot", "recorded:crypto", "fixture-epoch")
    source = RecordedSpotSource(
        SourceObservationBoundary(EvidenceStore(tmp_path / "archive")),
        writer,
        "source:synthetic-spot",
        "recorded:crypto",
        account.value.market,
    )
    context = MarketDataContext.try_create(
        venue="recorded:crypto",
        symbol="BTC/USDT",
        resolution="tick",
        side="bid",
        license_tag="synthetic-infrastructure-only",
        provenance={
            "origin": "synthetic",
            "adapter_version": 1,
            "amount_step": "0.001",
            "price_step": "0.01",
            "market": "BTC/USDT",
            "raw_tick": {
                "origin": "synthetic",
                "bid": "99.00",
                "ask": "100.00",
                "sequence": 1,
                "event_ns": 2000,
                "received_ns": 2000,
                "quantity": "0.100",
                "snapshot": True,
            },
        },
    )
    assert is_ok(context)
    observation = SourceObservation.try_create(
        event_time=1000,
        known_at=1000,
        source=source.source_id,
        source_native_id="bad-time",
        revision="v1",
        receive_wall_time=1000,
        writer=writer,
        sequence=0,
        world="replay",
        market_data=context.value,
    )
    assert is_ok(observation)
    receipt = source.boundary.admit(observation.value)
    assert is_ok(receipt)
    try:
        assert is_refusal(source.replay_into(account.value, receipt.value.archive.fingerprint))
        assert account.value.query()["feed_status"] == "UNSYNCED"
    finally:
        account.value.close()
