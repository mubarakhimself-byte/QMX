"""Provider-free replay materialization over normal CT-10 QMF persistence APIs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeVar, cast

import pytest
from qmb.host.replay import PinnedInstrumentPriceMetadata, read_recorded_replay_source
from qmf.core.chrono import Instant, WriterId
from qmf.core.exact import Price
from qmf.core.fingerprint import World, fingerprint
from qmf.core.identity import Instrument, VenueId
from qmf.core.refusal import Result, is_ok, is_refusal
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.source_boundary import SourceObservationBoundary
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
    next_frame = cast(
        "Mapping[str, object]", _ok(source.read_surfaces["eurusd"].at(_instant()))
    )
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
