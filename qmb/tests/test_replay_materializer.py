"""Provider-free replay materialization over normal CT-10 QMF persistence APIs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeVar, cast

import pytest
from qmb.host.replay import PinnedInstrumentPriceMetadata, read_recorded_replay_source
from qmb.host.replay_request import persist_replay_request, resolve_replay_request
from qmf.core.chrono import CalendarIdentity, Instant, WriterId
from qmf.core.exact import Price
from qmf.core.fingerprint import World, fingerprint
from qmf.core.identity import Instrument, VenueId
from qmf.core.refusal import Result, is_ok, is_refusal
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.seal import HoldoutSeal
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest
from qmf.data.store import EvidenceStore

T = TypeVar("T")
_NS = 1_700_000_000_000_000_000


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _instant(ns: int = _NS) -> Instant:
    return _ok(Instant.try_create(ns))


def _observation(side: str, sequence: int, price: int) -> SourceObservation:
    return _ok(
        SourceObservation.try_create(
            event_time=_instant(),
            known_at=_instant(),
            source="local-recorded-fixture",
            source_native_id=f"fixture-{side}",
            revision="1",
            receive_wall_time=_instant(),
            writer=_ok(WriterId.try_create("fixture-node", "data", "market", "boot-1")),
            sequence=sequence,
            world=World.REPLAY,
            foreign_money=_ok(ForeignMoney.try_create(price, 5)),
            market_data=_ok(
                MarketDataContext.try_create(
                    venue="fixture-venue",
                    symbol="EURUSD",
                    resolution="tick",
                    side=side,
                    license_tag="local-fixture",
                    provenance={"source_kind": "recorded-local-test"},
                )
            ),
        )
    )


def _split() -> tuple[SplitManifest, HoldoutSeal]:
    calendar = _ok(CalendarIdentity.try_create("fixture-calendar", "v1", "2025a"))
    segments = _ok(
        SplitManifest.default_split_segments(
            (
                _instant(_NS + 1_000),
                _instant(_NS + 2_000),
                _instant(_NS + 3_000),
            )
        )
    )
    manifest = _ok(
        SplitManifest.try_create(
            calendar_identity=calendar,
            segments=segments,
            seal_boundary=_ok(SplitBoundary.try_create(_instant(_NS + 3_000))),
            purge_width=0,
            embargo_width=0,
            world=World.REPLAY,
        )
    )
    return manifest, _ok(HoldoutSeal.from_manifest(manifest, 12))


def test_replay_source_reads_persisted_ct10_bid_ask_and_builds_asof_surface(
    tmp_path: Path,
) -> None:
    boundary = SourceObservationBoundary(EvidenceStore(tmp_path / "qmf-room"))
    refs = tuple(
        _ok(boundary.admit(_observation(side, index, price))).archive.fingerprint.value
        for index, (side, price) in enumerate((("bid", 1_234_500), ("ask", 1_234_520)))
    )

    source = _ok(
        read_recorded_replay_source(
            store_root=tmp_path / "qmf-room",
            archive_fingerprints=refs,
            stream_id="eurusd",
        )
    )

    assert source.world is World.REPLAY
    assert len(source.observations) == 2
    assert len(source.slices) == 1
    frame = cast("Mapping[str, object]", _ok(source.read_surfaces["eurusd"].at(_instant())))
    assert frame["kind"] == "series"
    samples = cast("Sequence[object]", frame["samples"])
    quote_sample = cast("Mapping[str, object]", samples[0])
    quote = cast("Mapping[str, object]", quote_sample["value"])
    bid = cast("Mapping[str, object]", quote["bid"])
    ask = cast("Mapping[str, object]", quote["ask"])
    assert bid == {
        "amount": 1_234_500,
        "scale": 5,
        "source_fp1": source.observations[0].fingerprint.value,
    }
    assert ask["amount"] == 1_234_520
    assert quote["license_tag"] == "local-fixture"
    assert source.fingerprint.value.startswith("fp1:sha256:")
    with pytest.raises(TypeError):
        cast("dict[str, object]", quote["bid"])["amount"] = 1
    next_frame = cast("Mapping[str, object]", _ok(source.read_surfaces["eurusd"].at(_instant())))
    next_sample = cast("Sequence[object]", next_frame["samples"])[0]
    next_quote = cast("Mapping[str, object]", cast("Mapping[str, object]", next_sample)["value"])
    assert cast("Mapping[str, object]", next_quote["bid"])["amount"] == 1_234_500
    aliased = _ok(
        read_recorded_replay_source(
            store_root=tmp_path / "qmf-room",
            archive_fingerprints=refs,
            stream_id="different-stream",
        )
    )
    assert aliased.fingerprint != source.fingerprint


def test_replay_source_refuses_missing_quote_side(tmp_path: Path) -> None:
    boundary = SourceObservationBoundary(EvidenceStore(tmp_path / "qmf-room"))
    ref = _ok(boundary.admit(_observation("bid", 0, 1_234_500))).archive.fingerprint.value
    refused = read_recorded_replay_source(
        store_root=tmp_path / "qmf-room",
        archive_fingerprints=(ref,),
        stream_id="eurusd",
    )
    assert is_refusal(refused)
    assert refused.context["field"] == "market_data.side"


def test_replay_prices_require_and_use_pinned_instrument_metadata(tmp_path: Path) -> None:
    boundary = SourceObservationBoundary(EvidenceStore(tmp_path / "qmf-room"))
    refs = tuple(
        _ok(boundary.admit(_observation(side, index, price))).archive.fingerprint.value
        for index, (side, price) in enumerate((("bid", 1_234_500), ("ask", 1_234_520)))
    )
    instrument = _ok(Instrument.try_create(_ok(VenueId.try_create("fixture-venue")), "EURUSD"))
    metadata_identity = {"instrument": instrument.fp1_identity(), "price_scale": 5}
    metadata_fp1 = _ok(fingerprint(metadata_identity))
    metadata = _ok(
        PinnedInstrumentPriceMetadata.try_create(
            instrument=instrument,
            price_scale=5,
            metadata_identity=metadata_identity,
            metadata_fp1=metadata_fp1,
        )
    )
    source = _ok(
        read_recorded_replay_source(
            store_root=tmp_path / "qmf-room",
            archive_fingerprints=refs,
            stream_id="eurusd",
            instrument_metadata=metadata,
        )
    )
    assert len(source.execution_paths) == 1
    path = source.execution_paths[0]
    assert path.bid == _ok(Price.try_create(1_234_500, instrument, 5))
    assert path.ask == _ok(Price.try_create(1_234_520, instrument, 5))
    assert source.price_metadata_fp1 == metadata_fp1

    wrong = read_recorded_replay_source(
        store_root=tmp_path / "qmf-room",
        archive_fingerprints=refs,
        stream_id="eurusd",
        instrument_metadata=_ok(
            PinnedInstrumentPriceMetadata.try_create(
                instrument=instrument,
                price_scale=4,
                metadata_identity={"instrument": instrument.fp1_identity(), "price_scale": 4},
                metadata_fp1=_ok(
                    fingerprint({"instrument": instrument.fp1_identity(), "price_scale": 4})
                ),
            )
        ),
    )
    assert is_refusal(wrong)
    assert wrong.context["field"] == "instrument_metadata"


def test_replay_source_binds_ct12_role_and_refuses_holdout_reads(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "qmf-room")
    boundary = SourceObservationBoundary(store)
    refs = tuple(
        _ok(boundary.admit(_observation(side, index, price))).archive.fingerprint.value
        for index, (side, price) in enumerate((("bid", 1_234_500), ("ask", 1_234_520)))
    )
    manifest, seal = _split()
    accepted = _ok(
        read_recorded_replay_source(
            store_root=tmp_path / "qmf-room",
            archive_fingerprints=refs,
            stream_id="eurusd",
            split_manifest=manifest,
            split_role=SegmentRole.TRAIN,
            holdout_seal=seal,
        )
    )
    assert accepted.split_fp1 == manifest.fingerprint
    assert accepted.split_role is SegmentRole.TRAIN
    assert accepted.fp1_identity()["split_fp1"] == manifest.fingerprint.value

    rejected = read_recorded_replay_source(
        store_root=tmp_path / "qmf-room",
        archive_fingerprints=refs,
        stream_id="eurusd",
        split_manifest=manifest,
        split_role=SegmentRole.VALIDATION,
        holdout_seal=seal,
    )
    assert is_refusal(rejected)
    assert rejected.context["field"] == "split_role"

    late_boundary = SourceObservationBoundary(EvidenceStore(tmp_path / "sealed-room", seal=seal))
    late_refs = tuple(
        _ok(
            late_boundary.admit(
                _observation_at(
                    side,
                    index,
                    price,
                    event_ns=_NS + 3_000,
                    known_ns=_NS + 3_000,
                )
            )
        ).archive.fingerprint.value
        for index, (side, price) in enumerate((("bid", 1_234_500), ("ask", 1_234_520)))
    )
    sealed = read_recorded_replay_source(
        store_root=tmp_path / "sealed-room",
        archive_fingerprints=late_refs,
        stream_id="eurusd",
        split_manifest=manifest,
        split_role=SegmentRole.SEALED_TEST,
        holdout_seal=seal,
    )
    assert is_refusal(sealed)
    assert sealed.context["field"] == "seal"


def test_replay_request_requires_a_validated_envelope_and_existing_content_ref(
    tmp_path: Path,
) -> None:
    rejected_write = persist_replay_request(request_root=tmp_path / "requests", request={})
    assert is_refusal(rejected_write)
    request_ref = _ok(fingerprint({"class": "missing-replay-request"}))
    manifest, _ = _split()
    missing = resolve_replay_request(
        request_root=tmp_path / "requests",
        request_ref=request_ref,
        split=manifest,
        expected_split_fp1=manifest.fingerprint,
        raw_store_root=tmp_path / "qmf-room",
        holdout_months=12,
    )
    assert is_refusal(missing)
    assert missing.context["field"] == "request_ref"


def _observation_at(
    side: str, sequence: int, price: int, *, event_ns: int, known_ns: int
) -> SourceObservation:
    item = _observation(side, sequence, price)
    return _ok(
        SourceObservation.try_create(
            event_time=_instant(event_ns),
            known_at=_instant(known_ns),
            source="local-recorded-fixture",
            source_native_id=f"fixture-{side}-{sequence}",
            revision="1",
            receive_wall_time=_instant(known_ns),
            writer=item.writer,
            sequence=sequence,
            world=World.REPLAY,
            foreign_money=item.foreign_money,
            market_data=item.market_data,
        )
    )
