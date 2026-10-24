"""A typed price month reads into replay through the second entry point (W12, N2).

P-QMBREAD in miniature: one month of quotes replays to the same execution paths from the typed
partitions and from the same rows admitted as CT-10 receipts, and half a pair is refused.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from qmb.host.replay import (
    PinnedInstrumentPriceMetadata,
    RecordedReplaySource,
    TypedPartitionRef,
    read_recorded_replay_source,
    read_typed_replay_source,
)
from qmf.core.chrono import Instant, WriterId
from qmf.core.fingerprint import World, fingerprint
from qmf.core.identity import Instrument, VenueId
from qmf.core.refusal import Result, is_ok, is_refusal
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.series import SeriesKey, SeriesStore
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore

T = TypeVar("T")

_FIRST_NS = 1_760_000_000_000_000_000
"""The first frontier of the fixture month, on a whole minute."""
_MS = 1_000_000
_FLAT_NS = 1_000_000_000


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _minute(index: int) -> int:
    return _FIRST_NS + index * 60 * _FLAT_NS


def _quotes() -> tuple[tuple[int, int, int], ...]:
    """Six one-minute frontiers: (event_ns, bid, ask) as the source prices verbatim."""
    return tuple(
        (_minute(index), 1_095_00 + index, 1_095_20 + index) for index in range(6)
    )


def _metadata() -> PinnedInstrumentPriceMetadata:
    instrument = _ok(Instrument.try_create(_ok(VenueId.try_create("dukascopy")), "EURUSD"))
    identity: dict[str, object] = {
        "instrument": instrument.fp1_identity(),
        "metadata_version": "typed-replay-fixture-v1",
        "price_scale": 5,
        "source_policy": {"kind": "typed-partition-test"},
    }
    return _ok(
        PinnedInstrumentPriceMetadata.try_create(
            instrument=instrument,
            price_scale=5,
            metadata_identity=identity,
            metadata_fp1=_ok(fingerprint(identity)),
        )
    )


def _observation(side: str, index: int, price: int) -> SourceObservation:
    at = _ok(Instant.try_create(_minute(index)))
    return _ok(
        SourceObservation.try_create(
            event_time=at,
            known_at=at,
            source="typed-replay-fixture",
            source_native_id=f"fixture-{index}-{side}",
            revision="1",
            receive_wall_time=at,
            writer=_ok(WriterId.try_create("fixture-node", "data", "market", "boot-1")),
            sequence=index * 2 + (0 if side == "bid" else 1),
            world=World.REPLAY,
            foreign_money=_ok(ForeignMoney.try_create(price, 5)),
            market_data=_ok(
                MarketDataContext.try_create(
                    venue="dukascopy",
                    symbol="EURUSD",
                    resolution="tick",
                    side=side,
                    license_tag="local-fixture",
                    provenance={"source_kind": "typed-replay-test"},
                )
            ),
        )
    )


def _ct10_source(root: Path) -> RecordedReplaySource:
    """The same rows the old way: admitted through the CT-10 boundary, then read."""
    boundary = SourceObservationBoundary(EvidenceStore(root / "ct10-room"))
    refs = tuple(
        _ok(boundary.admit(_observation(side, index, price))).archive.fingerprint.value
        for index, (_, bid, ask) in enumerate(_quotes())
        for side, price in (("bid", bid), ("ask", ask))
    )
    return _ok(
        read_recorded_replay_source(
            store_root=root / "ct10-room",
            archive_fingerprints=refs,
            stream_id="eurusd",
            instrument_metadata=_metadata(),
        )
    )


def _ticks(root: Path) -> TypedPartitionRef:
    store = SeriesStore(root / "typed")
    key = _ok(SeriesKey.try_create("dukascopy", "EURUSD", "ticks", 2025, 10))
    receipt = _ok(
        store.commit(
            key, [(at // _MS, bid, ask, 1.0, 1.0) for at, bid, ask in _quotes()]
        )
    )
    return _ok(
        TypedPartitionRef.try_create(
            path=receipt.path,
            series=key.series,
            month=f"{key.year:04d}-{key.month:02d}",
            fingerprint=receipt.fingerprint,
        )
    )


def _bars(root: Path) -> tuple[TypedPartitionRef, TypedPartitionRef]:
    """The same minutes as bid and ask m1 bars: one tick a minute, so all four prices agree."""
    refs: list[TypedPartitionRef] = []
    for side in ("bid", "ask"):
        store = SeriesStore(root / "typed")
        key = _ok(SeriesKey.try_create("dukascopy", "EURUSD", "bar-m1", 2025, 10, side))
        receipt = _ok(
            store.commit(
                key,
                [
                    (at // _MS, price, price, price, price, 1.0)
                    for at, _bid, _ask in _quotes()
                    for price in ([_bid] if side == "bid" else [_ask])
                ],
            )
        )
        refs.append(
            _ok(
                TypedPartitionRef.try_create(
                    path=receipt.path,
                    series=key.series,
                    month=f"{key.year:04d}-{key.month:02d}",
                    fingerprint=receipt.fingerprint,
                )
            )
        )
    return refs[0], refs[1]


def _paths(source: RecordedReplaySource) -> tuple[tuple[int, int, int], ...]:
    """What the run loop crosses, as (frontier_ns, bid, ask) triples."""
    triples: list[tuple[int, int, int]] = []
    for path in source.execution_paths:
        assert path.bar_start is not None and path.bid is not None and path.ask is not None
        triples.append((path.bar_start.value_ns, path.bid.value, path.ask.value))
    return tuple(triples)


def test_a_tick_month_replays_to_the_quotes_its_ct10_receipts_give(tmp_path: Path) -> None:
    typed = _ok(
        read_typed_replay_source(
            partitions=(_ticks(tmp_path),),
            stream_id="eurusd",
            instrument_metadata=_metadata(),
        )
    )
    receipted = _ct10_source(tmp_path)

    assert _paths(typed) == _paths(receipted)
    assert _paths(typed) == (
        (_minute(0), 1_095_00, 1_095_20),
        (_minute(1), 1_095_01, 1_095_21),
        (_minute(2), 1_095_02, 1_095_22),
        (_minute(3), 1_095_03, 1_095_23),
        (_minute(4), 1_095_04, 1_095_24),
        (_minute(5), 1_095_05, 1_095_25),
    )
    assert typed.source_class == "qmb-typed-partition-replay-source-v1"
    assert typed.observations == ()
    assert len(typed.partitions) == 1
    assert typed.fp1_identity()["class"] == "qmb-typed-partition-replay-source-v1"
    assert receipted.fp1_identity()["class"] == "qmb-recorded-replay-source-v1"


def test_a_bid_and_ask_bar_pair_replays_to_the_same_quotes_as_ticks(tmp_path: Path) -> None:
    bid, ask = _bars(tmp_path)
    paired = _ok(
        read_typed_replay_source(
            partitions=(bid, ask),
            stream_id="eurusd",
            instrument_metadata=_metadata(),
        )
    )
    ticks = _ok(
        read_typed_replay_source(
            partitions=(_ticks(tmp_path),),
            stream_id="eurusd",
            instrument_metadata=_metadata(),
        )
    )

    assert _paths(paired) == _paths(ticks)
    assert [item.series for item in paired.partitions] == [
        "dukascopy/EURUSD/bar-m1/bid",
        "dukascopy/EURUSD/bar-m1/ask",
    ]


def test_a_bid_bar_without_its_ask_is_refused_never_half_a_pair(tmp_path: Path) -> None:
    bid, _ask = _bars(tmp_path)

    refused = read_typed_replay_source(
        partitions=(bid,),
        stream_id="eurusd",
        instrument_metadata=_metadata(),
    )

    assert is_refusal(refused)
    assert refused.context["field"] == "partitions"
    assert refused.context["missing"] == ("ask",)


def test_a_partition_that_does_not_hash_to_its_fingerprint_is_refused(tmp_path: Path) -> None:
    tick = _ticks(tmp_path)
    substituted = TypedPartitionRef(
        path=tick.path,
        series=tick.series,
        month=tick.month,
        fingerprint="0" * 64,
    )

    refused = read_typed_replay_source(
        partitions=(substituted,),
        stream_id="eurusd",
        instrument_metadata=_metadata(),
    )

    assert is_refusal(refused)
    assert refused.context["field"] == "fingerprint"
