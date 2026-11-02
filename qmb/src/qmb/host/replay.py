"""Materialize bitemporal CT-10 artifacts for provider-free replay, and replay units windowed.

This adapter reads immutable QMF raw-archive artifacts through the QMF-owned
source-observation boundary. It preserves foreign prices and their declared
scales verbatim; it does not convert them into QMB execution prices.

The windowed reader (Part B AD-205, QB-01, QB-02) streams a unit's data row by row: each
market's rows become pieces as its data card's fidelity declares (quotes, trades or bars),
the bar builder folds them into the unit's bars in the venue's day, and each market keeps only
a window of the unit's derived warm-up plus its declared lookback. The run's memory is the
window's, whatever the run's length, and nothing caps the steps.
"""

# pyarrow ships no type stubs; as in the QMF store's typed writer, the unknown-type rules are
# disabled at file scope here so the rest of this module stays strictly typed.
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import csv
import heapq
import re
import tempfile
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from itertools import groupby
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from qmf.core.chrono import Instant
from qmf.core.exact import Price
from qmf.core.fingerprint import Fingerprint, World, fingerprint
from qmf.core.identity import Instrument
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qmf.data.observation import SourceObservation
from qmf.data.seal import HoldoutSeal
from qmf.data.series import SeriesKey, SeriesStore, rule_for
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.source_split import partition_source_observation
from qmf.data.splits import SegmentRole, SplitManifest
from qmf.data.store import EvidenceStore
from qml.compile import CompiledUnit
from qml.protocol import MappingReadSurface
from qml.protocol.unit import OHLC, QuoteBar

from qmb._refuse import invalid, policy
from qmb.data import policy as data_policy
from qmb.execution.ports import SlicePath
from qmb.host.unit_handler import UnitSliceHandler
from qmb.runloop.bars import BarBuilder, Piece
from qmb.runloop.loop import (
    DeclaredStream,
    EventSlice,
    RestingIntent,
    SliceObservation,
    StreamSet,
    run_slice,
)

__all__ = [
    "WINDOW_MEMORY_TOLERANCE",
    "Aggressor",
    "Bar",
    "BarPair",
    "BarWindow",
    "DataCard",
    "Fidelity",
    "PinnedInstrumentPriceMetadata",
    "Print",
    "RecordedReplaySource",
    "Tick",
    "TypedPartitionRef",
    "VenueDay",
    "read_bar_csv",
    "read_bar_pair_csv",
    "read_recorded_replay_source",
    "read_typed_replay_source",
    "replay_feed",
    "replay_windowed",
    "window_size",
]

_REPLAY_SOURCE_CLASS: Final[str] = "qmb-recorded-replay-source-v1"
_TYPED_SOURCE_CLASS: Final[str] = "qmb-typed-partition-replay-source-v1"
_TICKS_KIND: Final[str] = "ticks"
_BAR_KIND: Final[str] = "bar-m1"
_NS_PER_MS: Final[int] = 1_000_000
_SOURCE_PRICE_SCALE: Final[int] = 5
"""The typed writer's own scale: a price integer divided by 100_000 is the price (W9)."""
_MONTH: Final[re.Pattern[str]] = re.compile(r"^(\d{4})-(\d{2})$")


def _freeze_evidence(value: object) -> object:
    """Freeze nested CT-10-derived evidence before exposing it to selected logic."""
    if isinstance(value, Mapping):
        mapping = cast("Mapping[object, object]", value)
        return MappingProxyType({key: _freeze_evidence(item) for key, item in mapping.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_evidence(item) for item in cast("Sequence[object]", value))
    return value


@dataclass(frozen=True, slots=True)
class RecordedReplaySource:
    """Validated replay evidence arranged as replay slices and QML read surfaces.

    One type serves both readers: ``observations`` are the CT-10 receipts the archive
    boundary admitted, and ``partitions`` are the typed price files the market-data door
    materialised. A source carries one or the other, never a mix, and ``source_class`` says
    which, so its fingerprint names the release it was read from.
    """

    world: World
    stream_id: str
    observations: tuple[SourceObservation, ...]
    slices: tuple[EventSlice, ...]
    read_surfaces: Mapping[str, MappingReadSurface]
    execution_paths: tuple[SlicePath, ...]
    price_metadata_fp1: Fingerprint | None
    split_fp1: Fingerprint | None
    split_role: SegmentRole | None
    fingerprint: Fingerprint
    source_class: str = _REPLAY_SOURCE_CLASS
    partitions: tuple[TypedPartitionRef, ...] = ()

    def fp1_identity(self) -> dict[str, object]:
        identity: dict[str, object] = {
            "class": self.source_class,
            "stream_id": self.stream_id,
            "world": self.world.value,
        }
        if self.partitions:
            identity["partitions"] = [item.fp1_identity() for item in self.partitions]
        else:
            identity["observations"] = [item.fingerprint.value for item in self.observations]
        if self.price_metadata_fp1 is not None:
            identity["price_metadata_fp1"] = self.price_metadata_fp1.value
        if self.split_fp1 is not None and self.split_role is not None:
            identity["split_fp1"] = self.split_fp1.value
            identity["split_role"] = self.split_role.value
        return identity


@dataclass(frozen=True, slots=True)
class TypedPartitionRef:
    """One typed price partition the market-data door materialised for a replay read.

    ``series`` is the door's address without its month (``source/subject/kind/variant``,
    ``-`` for no variant) and ``month`` is ``YYYY-MM``. ``fingerprint`` is the streamed one
    the store recorded, and the reader re-derives it from the file's rows before it replays
    anything, so a copied or substituted file cannot pass as that partition.
    """

    path: Path
    series: str
    month: str
    fingerprint: str

    @classmethod
    def try_create(
        cls, *, path: object, series: object, month: object, fingerprint: object
    ) -> Result[TypedPartitionRef]:
        if not isinstance(path, (str, Path)) or not str(path).strip():
            return invalid("path", "a typed partition names the file the door materialised")
        if not isinstance(series, str):
            return invalid("series", "a typed partition names its series", given=repr(series))
        parts = series.split("/")
        if len(parts) != 4 or any(part.strip() == "" for part in parts[:3]):
            return invalid(
                "series",
                "a series is source/subject/kind/variant, with '-' for no variant",
                given=series,
            )
        if not isinstance(month, str) or _MONTH.fullmatch(month) is None:
            return invalid("month", "a typed partition names its month as YYYY-MM", given=month)
        if not isinstance(fingerprint, str):
            return invalid(
                "fingerprint", "a typed partition names its fingerprint", given=repr(fingerprint)
            )
        return Ok(cls(Path(path), series, month, fingerprint))

    @property
    def source(self) -> str:
        return self.series.split("/")[0]

    @property
    def subject(self) -> str:
        return self.series.split("/")[1]

    @property
    def kind(self) -> str:
        return self.series.split("/")[2]

    @property
    def variant(self) -> str:
        variant = self.series.split("/")[3]
        return "" if variant == "-" else variant

    @property
    def year(self) -> int:
        return int(self.month[:4])

    @property
    def month_number(self) -> int:
        return int(self.month[5:])

    def fp1_identity(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "month": self.month,
            "series": self.series,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class PinnedInstrumentPriceMetadata:
    """Explicit CT-03 instrument and source-price scale used for exact Price values.

    The opaque fingerprint is over the supplied metadata identity. This adapter does
    not infer a price scale from CT-10 foreign money or from a symbol spelling.
    """

    instrument: Instrument
    price_scale: int
    metadata_identity: Mapping[str, object]
    fingerprint: Fingerprint

    @classmethod
    def try_create(
        cls,
        *,
        instrument: object,
        price_scale: object,
        metadata_identity: object,
        metadata_fp1: object,
    ) -> Result[PinnedInstrumentPriceMetadata]:
        if not isinstance(instrument, Instrument):
            return invalid("instrument", "price metadata is pinned to a CT-03 Instrument")
        if isinstance(price_scale, bool) or not isinstance(price_scale, int) or price_scale < 0:
            return invalid("price_scale", "price scale is a declared non-negative integer")
        if not isinstance(metadata_identity, Mapping):
            return invalid(
                "metadata_identity", "pinned metadata carries canonical identity content"
            )
        stamped = fingerprint(cast("Mapping[str, object]", metadata_identity))
        if is_refusal(stamped):
            return stamped
        ref = (
            Ok(metadata_fp1)
            if isinstance(metadata_fp1, Fingerprint)
            else Fingerprint.try_create(metadata_fp1)
        )
        if is_refusal(ref):
            return ref
        if stamped.value != ref.value:
            return policy(
                "metadata_fp1", "price scale and instrument match the pinned metadata identity"
            )
        body = cast("Mapping[str, object]", metadata_identity)
        if (
            body.get("instrument") != instrument.fp1_identity()
            or body.get("price_scale") != price_scale
        ):
            return policy(
                "metadata_identity",
                "the pinned metadata identity declares this exact instrument and price scale",
            )
        frozen_identity = _freeze_evidence(cast("Mapping[str, object]", metadata_identity))
        if not isinstance(frozen_identity, Mapping):
            return invalid("metadata_identity", "pinned metadata identity freezes as a mapping")
        return Ok(
            cls(instrument, price_scale, cast("Mapping[str, object]", frozen_identity), ref.value)
        )


def read_recorded_replay_source(
    *,
    store_root: object,
    archive_fingerprints: object,
    stream_id: object,
    instrument_metadata: object = None,
    split_manifest: object = None,
    split_role: object = None,
    holdout_seal: object = None,
    world: object = World.REPLAY,
) -> Result[RecordedReplaySource]:
    """Read explicit CT-10 archive receipts and materialize bitemporal replay input.

    ``archive_fingerprints`` are the raw-archive receipt fingerprints returned by
    ``SourceObservationBoundary.admit``. The reader resolves each through the
    QMF-owned boundary, verifies world and observation identities, then builds
    quote pairs only from matching bid/ask observations. Corrections are
    refused until the governed correction-resolution fold is available.
    """
    if isinstance(world, str):
        try:
            world = World(world)
        except ValueError:
            return invalid("world", "recorded replay data is read from a QMF world")
    if world is not World.REPLAY:
        return policy("world", "QMB replay source materialization requires world=replay")
    if not isinstance(store_root, (str, Path)) or not str(store_root).strip():
        return invalid("store_root", "a recorded replay source names a QMF EvidenceStore root")
    if not isinstance(stream_id, str) or not stream_id.strip():
        return invalid("stream_id", "a replay source names its declared run stream")
    if instrument_metadata is not None and not isinstance(
        instrument_metadata, PinnedInstrumentPriceMetadata
    ):
        return invalid(
            "instrument_metadata",
            "execution prices require explicit fingerprint-verified instrument metadata",
        )
    if split_manifest is not None or split_role is not None or holdout_seal is not None:
        if not isinstance(split_manifest, SplitManifest):
            return invalid("split_manifest", "governed replay uses the registered CT-12 manifest")
        if not isinstance(split_role, SegmentRole):
            return invalid("split_role", "governed replay names one CT-12 segment role")
        if not isinstance(holdout_seal, HoldoutSeal):
            return invalid(
                "holdout_seal", "governed replay wires the configured CT-12 holdout seal"
            )
        if split_manifest.world is not World.REPLAY:
            return policy("world", "CT-12 split world matches replay materialization")
        if (
            holdout_seal.world is not World.REPLAY
            or holdout_seal.calendar_identity != split_manifest.calendar_identity
            or holdout_seal.seal_boundary != split_manifest.seal_boundary
        ):
            return policy(
                "holdout_seal",
                "the configured holdout seal carries this CT-12 manifest's calendar, "
                "boundary, and world",
            )
    elif world is World.REPLAY:
        # Lower-level source inspection remains available to explicitly ungoverned
        # callers; the production request loader always supplies all CT-12 pins.
        pass
    if isinstance(archive_fingerprints, (str, bytes)) or not isinstance(
        archive_fingerprints, Sequence
    ):
        return invalid("archive_fingerprints", "a replay source cites archive receipt fingerprints")

    configured_seal = holdout_seal if isinstance(holdout_seal, HoldoutSeal) else None
    reader = SourceObservationBoundary(EvidenceStore(Path(store_root), seal=configured_seal))
    observations: list[SourceObservation] = []
    seen: set[str] = set()
    for index, ref in enumerate(cast("Sequence[object]", archive_fingerprints)):
        key = Fingerprint.try_create(ref)
        if is_refusal(key):
            return key
        if key.value.value in seen:
            return invalid(
                "archive_fingerprints", "a replay source cites each artifact once", index=index
            )
        seen.add(key.value.value)
        observed = reader.read(key.value, in_world=World.REPLAY, for_world=World.REPLAY)
        if is_refusal(observed):
            return observed
        item = observed.value
        if item.world is not World.REPLAY:
            return policy(
                "world", "a QMB replay source contains only replay observations", index=index
            )
        if isinstance(split_manifest, SplitManifest):
            selected_role = cast("SegmentRole", split_role)
            partition = partition_source_observation(split_manifest, item)
            if is_refusal(partition):
                return partition
            if partition.value is not selected_role:
                return policy(
                    "split_role",
                    "every pinned CT-10 source receipt belongs to the requested CT-12 role",
                    expected=selected_role.value,
                    actual=partition.value.value,
                    observation=item.fingerprint.value,
                )
        if item.correction_of is not None:
            return policy(
                "correction_of",
                "CT-10 corrections need their resolution fold before replay",
                index=index,
                correction_of=item.correction_of.value,
            )
        if item.market_data is None or item.foreign_money is None:
            return invalid(
                "market_data",
                "a replay quote carries CT-10 market-data coordinates and verbatim foreign money",
                index=index,
            )
        observations.append(item)

    if not observations:
        return invalid("archive_fingerprints", "a recorded replay source is non-empty")
    observations.sort(
        key=lambda item: (
            item.event_time.value_ns,
            item.known_at.value_ns,
            item.writer.stream,
            item.sequence,
            item.fingerprint.value,
        )
    )
    groups: dict[int, dict[str, SourceObservation]] = {}
    for item in observations:
        context = item.market_data
        if context is None:
            return invalid("market_data", "a replay observation carries market coordinates")
        row = groups.setdefault(item.event_time.value_ns, {})
        if context.side in row:
            return invalid(
                "market_data.side",
                "one quote frontier contains at most one observation per side",
                instant_ns=item.event_time.value_ns,
                side=context.side,
            )
        row[context.side] = item

    frontiers: list[_QuoteFrontier] = []
    for event_ns, quote in sorted(groups.items()):
        if set(quote) != {"bid", "ask"}:
            return invalid(
                "market_data.side",
                "each replay quote frontier requires recorded bid and ask observations",
                instant_ns=event_ns,
                present_sides=sorted(quote),
            )
        bid = quote["bid"]
        ask = quote["ask"]
        bid_context = bid.market_data
        ask_context = ask.market_data
        if bid_context is None or ask_context is None:
            return invalid("market_data", "a replay quote side carries market coordinates")
        if (
            bid_context.venue != ask_context.venue
            or bid_context.symbol != ask_context.symbol
            or bid_context.resolution != ask_context.resolution
            or bid_context.license_tag != ask_context.license_tag
            or bid.foreign_money is None
            or ask.foreign_money is None
            or bid.foreign_money.scale != ask.foreign_money.scale
        ):
            return invalid(
                "market_data",
                "bid/ask share coordinates, usage right, and exact source scale",
                instant_ns=event_ns,
            )
        frontiers.append(
            _QuoteFrontier(
                event_ns=event_ns,
                knowable_ns=max(event_ns, bid.known_at.value_ns, ask.known_at.value_ns),
                bid=bid.foreign_money.verbatim,
                ask=ask.foreign_money.verbatim,
                scale=bid.foreign_money.scale,
                license_tag=bid_context.license_tag,
                resolution=bid_context.resolution,
                symbol=bid_context.symbol,
                venue=bid_context.venue,
                bid_source_fp1=bid.fingerprint.value,
                ask_source_fp1=ask.fingerprint.value,
            )
        )

    identity: dict[str, object] = {
        "class": _REPLAY_SOURCE_CLASS,
        "observations": [item.fingerprint.value for item in observations],
        "stream_id": stream_id,
        "world": World.REPLAY.value,
    }
    if isinstance(split_manifest, SplitManifest):
        identity["split_fp1"] = split_manifest.fingerprint.value
        identity["split_role"] = cast("SegmentRole", split_role).value
    if instrument_metadata is not None:
        identity["price_metadata_fp1"] = instrument_metadata.fingerprint.value
    return _materialise_quotes(
        stream_id=stream_id,
        frontiers=tuple(frontiers),
        instrument_metadata=instrument_metadata,
        identity=identity,
        split_manifest=split_manifest if isinstance(split_manifest, SplitManifest) else None,
        split_role=split_role if isinstance(split_role, SegmentRole) else None,
        source_class=_REPLAY_SOURCE_CLASS,
        observations=tuple(observations),
    )


@dataclass(frozen=True, slots=True)
class _QuoteFrontier:
    """One bid/ask frontier either reader built, in the exact form the run loop consumes.

    Both readers reduce to this, so the slices, the read surfaces and the execution paths are
    built once and a tick receipt and a typed partition reach the run loop in the same shape.
    """

    event_ns: int
    knowable_ns: int
    bid: int
    ask: int
    scale: int
    license_tag: str
    resolution: str
    symbol: str
    venue: str
    bid_source_fp1: str
    ask_source_fp1: str


def _materialise_quotes(
    *,
    stream_id: str,
    frontiers: Sequence[_QuoteFrontier],
    instrument_metadata: PinnedInstrumentPriceMetadata | None,
    identity: dict[str, object],
    split_manifest: SplitManifest | None,
    split_role: SegmentRole | None,
    source_class: str,
    observations: tuple[SourceObservation, ...] = (),
    partitions: tuple[TypedPartitionRef, ...] = (),
) -> Result[RecordedReplaySource]:
    """Turn quote frontiers into slices, cumulative read surfaces and exact execution paths."""
    slices: list[EventSlice] = []
    frames: dict[int, object] = {}
    cumulative: list[object] = []
    execution_paths: list[SlicePath] = []
    previous_frontier: int | None = None
    for frontier in frontiers:
        knowable_ns = frontier.knowable_ns
        if previous_frontier is not None and knowable_ns <= previous_frontier:
            return invalid(
                "known_at",
                "replay frontiers are strictly increasing and one stream emits once per frontier",
                frontier_ns=knowable_ns,
            )
        knowable = Instant.try_create(knowable_ns)
        event = Instant.try_create(frontier.event_ns)
        if is_refusal(knowable) or is_refusal(event):
            return invalid(
                "instant",
                "replay instants are valid QMF Instants",
                instant_ns=frontier.event_ns,
            )
        quote_value: Mapping[str, object] = MappingProxyType(
            {
                "ask": {
                    "amount": frontier.ask,
                    "scale": frontier.scale,
                    "source_fp1": frontier.ask_source_fp1,
                },
                "bid": {
                    "amount": frontier.bid,
                    "scale": frontier.scale,
                    "source_fp1": frontier.bid_source_fp1,
                },
                "event_time_ns": frontier.event_ns,
                "license_tag": frontier.license_tag,
                "resolution": frontier.resolution,
                "symbol": frontier.symbol,
                "venue": frontier.venue,
            }
        )
        if instrument_metadata is not None:
            metadata = instrument_metadata
            if (
                frontier.venue != metadata.instrument.venue.value
                or frontier.symbol != metadata.instrument.symbol
                or frontier.scale != metadata.price_scale
            ):
                return policy(
                    "instrument_metadata",
                    "quote coordinates and source scales match pinned CT-03 metadata",
                    instant_ns=frontier.event_ns,
                )
            bid_price = Price.try_create(frontier.bid, metadata.instrument, metadata.price_scale)
            ask_price = Price.try_create(frontier.ask, metadata.instrument, metadata.price_scale)
            if is_refusal(bid_price):
                return bid_price
            if is_refusal(ask_price):
                return ask_price
            path = SlicePath.try_create(
                stream_id,
                (),
                bid=bid_price.value,
                ask=ask_price.value,
                bar_start=event.value,
                bar_end=knowable.value,
            )
            if is_refusal(path):
                return path
            execution_paths.append(path.value)
        cumulative.append(
            _freeze_evidence(
                {
                    "presence": "present",
                    "knowable_at": knowable.value,
                    "value": dict(quote_value),
                }
            )
        )
        surface_payload = _freeze_evidence(
            {
                "kind": "series",
                "samples": list(cumulative),
            }
        )
        frames[knowable_ns] = surface_payload
        previous_frontier = knowable_ns
        observation = SliceObservation.try_create(stream_id, knowable.value, True)
        if is_refusal(observation):
            return observation
        slice_ = EventSlice.try_create((observation.value,))
        if is_refusal(slice_):
            return slice_
        slices.append(slice_.value)

    built_surface = MappingReadSurface.try_create(frames)
    if is_refusal(built_surface):
        return built_surface
    stamped = fingerprint(identity)
    if is_refusal(stamped):
        return stamped
    return Ok(
        RecordedReplaySource(
            world=World.REPLAY,
            stream_id=stream_id,
            observations=observations,
            slices=tuple(slices),
            read_surfaces=MappingProxyType({stream_id: built_surface.value}),
            execution_paths=tuple(execution_paths),
            price_metadata_fp1=(
                None if instrument_metadata is None else instrument_metadata.fingerprint
            ),
            split_fp1=(None if split_manifest is None else split_manifest.fingerprint),
            split_role=split_role,
            fingerprint=stamped.value,
            source_class=source_class,
            partitions=partitions,
        )
    )


def read_typed_replay_source(
    *,
    partitions: object,
    stream_id: object,
    instrument_metadata: object = None,
    split_manifest: object = None,
    split_role: object = None,
    holdout_seal: object = None,
    world: object = World.REPLAY,
) -> Result[RecordedReplaySource]:
    """Read typed price partitions and materialize bitemporal replay input (W12, N2).

    ``partitions`` are the typed files the market-data door's ``materialise`` copied for this
    read, each with its series, its month and the fingerprint the store recorded. The reader
    verifies the world, each file's streamed fingerprint, the holdout seal and the split role
    as ``read_recorded_replay_source`` does for CT-10 receipts, then builds quote pairs from
    tick rows (both sides in one row) or from a bid and an ask bar series of the same month.
    Half a pair is refused: a bid series without its ask is never replayed as a one-sided
    quote.
    """
    checked_world = data_policy.check_typed_world(world)
    if is_refusal(checked_world):
        return checked_world
    if not isinstance(stream_id, str) or not stream_id.strip():
        return invalid("stream_id", "a replay source names its declared run stream")
    if instrument_metadata is not None and not isinstance(
        instrument_metadata, PinnedInstrumentPriceMetadata
    ):
        return invalid(
            "instrument_metadata",
            "typed replay prices require explicit fingerprint-verified instrument metadata",
        )
    pinned_split: tuple[SplitManifest, SegmentRole] | None = None
    pinned_seal: HoldoutSeal | None = None
    if split_manifest is not None or split_role is not None or holdout_seal is not None:
        if not isinstance(split_manifest, SplitManifest):
            return invalid("split_manifest", "governed replay uses the registered CT-12 manifest")
        if not isinstance(split_role, SegmentRole):
            return invalid("split_role", "governed replay names one CT-12 segment role")
        if not isinstance(holdout_seal, HoldoutSeal):
            return invalid(
                "holdout_seal", "governed replay wires the configured CT-12 holdout seal"
            )
        if split_manifest.world is not World.REPLAY:
            return policy("world", "CT-12 split world matches replay materialization")
        if (
            holdout_seal.world is not World.REPLAY
            or holdout_seal.calendar_identity != split_manifest.calendar_identity
            or holdout_seal.seal_boundary != split_manifest.seal_boundary
        ):
            return policy(
                "holdout_seal",
                "the configured holdout seal carries this CT-12 manifest's calendar, "
                "boundary, and world",
            )
        pinned_split = (split_manifest, split_role)
        pinned_seal = holdout_seal
    if isinstance(partitions, (str, bytes)) or not isinstance(partitions, Sequence):
        return invalid(
            "partitions", "a typed replay read cites the partitions the door materialised"
        )
    refs: list[TypedPartitionRef] = []
    for index, item in enumerate(cast("Sequence[object]", partitions)):
        if not isinstance(item, TypedPartitionRef):
            return invalid(
                "partitions",
                "a typed replay read cites materialised partition references",
                index=index,
            )
        refs.append(item)
    paired = _typed_pair(refs)
    if is_refusal(paired):
        return paired
    kind, ordered = paired.value
    metadata = instrument_metadata
    if metadata is not None and (
        ordered[0].subject != metadata.instrument.symbol
        or metadata.price_scale != _SOURCE_PRICE_SCALE
    ):
        return policy(
            "instrument_metadata",
            "the typed series is about the pinned CT-03 instrument at its declared scale",
            series=ordered[0].series,
            price_scale=metadata.price_scale,
        )
    month = ordered[0].month
    rows: dict[str, list[tuple[object, ...]]] = {}
    for ref in ordered:
        read = _verified_rows(ref, _columns_of(ref))
        if is_refusal(read):
            return read
        rows[ref.variant or kind] = read.value
    built = _typed_frontiers(kind, ordered, rows, metadata=metadata, month=month)
    if is_refusal(built):
        return built
    frontiers = built.value
    for frontier in frontiers:
        if pinned_seal is not None:
            sealed = data_policy.check_typed_sealed(
                seal=pinned_seal, month=month, instant_ns=frontier.event_ns
            )
            if is_refusal(sealed):
                return sealed
        if pinned_split is not None:
            manifest, role = pinned_split
            claimed = data_policy.check_typed_instant(
                manifest=manifest, role=role, month=month, instant_ns=frontier.event_ns
            )
            if is_refusal(claimed):
                return claimed
    identity: dict[str, object] = {
        "class": _TYPED_SOURCE_CLASS,
        "partitions": [ref.fp1_identity() for ref in ordered],
        "stream_id": stream_id,
        "world": World.REPLAY.value,
    }
    if pinned_split is not None:
        identity["split_fp1"] = pinned_split[0].fingerprint.value
        identity["split_role"] = pinned_split[1].value
    if metadata is not None:
        identity["price_metadata_fp1"] = metadata.fingerprint.value
    return _materialise_quotes(
        stream_id=stream_id,
        frontiers=frontiers,
        instrument_metadata=metadata,
        identity=identity,
        split_manifest=None if pinned_split is None else pinned_split[0],
        split_role=None if pinned_split is None else pinned_split[1],
        source_class=_TYPED_SOURCE_CLASS,
        partitions=tuple(ordered),
    )


def _typed_pair(
    refs: Sequence[TypedPartitionRef],
) -> Result[tuple[str, tuple[TypedPartitionRef, ...]]]:
    """Order a typed read as one tick series, or one month's bid and ask bar pair."""
    if not refs:
        return invalid("partitions", "a typed replay read cites at least one partition")
    kinds = sorted({ref.kind for ref in refs})
    if len(kinds) != 1:
        return invalid("partitions", "a typed replay read pairs one kind at a time", kinds=kinds)
    kind = kinds[0]
    if kind == _TICKS_KIND:
        if len(refs) != 1:
            return invalid(
                "partitions",
                "a tick month is one partition, because a tick row carries both sides",
                series=[ref.series for ref in refs],
            )
        return Ok((_TICKS_KIND, (refs[0],)))
    if kind != _BAR_KIND:
        return invalid(
            "partitions",
            "a typed replay read takes ticks or the bid and ask bar-m1 series of one month",
            kind=kind,
        )
    if len({(ref.source, ref.subject, ref.month) for ref in refs}) != 1:
        return invalid(
            "partitions",
            "a bar pair is one instrument's bid and ask series of one month",
            series=[ref.series for ref in refs],
        )
    variants = {ref.variant for ref in refs}
    if len(refs) != 2 or variants != {"bid", "ask"}:
        return invalid(
            "partitions",
            "a bar replay reads the bid series and the ask series together; half a pair is "
            "never used as a quote",
            present=sorted(variants),
            missing=sorted({"bid", "ask"} - variants),
        )
    by_variant = {ref.variant: ref for ref in refs}
    return Ok((_BAR_KIND, (by_variant["bid"], by_variant["ask"])))


def _columns_of(ref: TypedPartitionRef) -> tuple[str, ...]:
    """The typed columns the store wrote for this series' kind."""
    return rule_for(ref.source, ref.kind).columns


def _verified_rows(
    ref: TypedPartitionRef, columns: Sequence[str]
) -> Result[list[tuple[object, ...]]]:
    """Read a materialised partition and re-derive the fingerprint its rows hash to.

    The fingerprint is the store writer's own streamed hash over the pinned logical encoding, so
    the rows are written once more through the store's public commit into a scratch root, and the
    fingerprint that comes back is compared with the one claimed for the partition. A file whose
    rows do not hash to its claim is refused before a single quote is built, so a substituted or
    truncated copy cannot pass as that partition.
    """
    try:
        import pyarrow.parquet as pq  # noqa: PLC0415 (only a read needs the library)
    except ImportError as exc:  # pragma: no cover - qmf-data ships pyarrow
        return invalid("partitions", "reading a typed partition needs pyarrow", error=str(exc))
    key = SeriesKey.try_create(
        ref.source, ref.subject, ref.kind, ref.year, ref.month_number, ref.variant
    )
    if is_refusal(key):
        return key
    collected: list[tuple[object, ...]] = []
    computed = ""
    with tempfile.TemporaryDirectory(prefix="qmb-typed-", ignore_cleanup_errors=True) as scratch:
        try:
            for batch in pq.ParquetFile(ref.path).iter_batches(batch_size=50_000):
                collected.extend(tuple(row[name] for name in columns) for row in batch.to_pylist())
        except (OSError, ValueError, KeyError) as exc:
            return invalid(
                "partitions",
                "a typed partition is a readable typed Parquet file",
                series=ref.series,
                month=ref.month,
                error=str(exc),
            )
        written = SeriesStore(Path(scratch)).commit(key.value, collected)
        if is_refusal(written):
            return written
        computed = written.value.fingerprint
    checked = data_policy.check_typed_fingerprint(
        series=ref.series, month=ref.month, claimed=ref.fingerprint, computed=computed
    )
    if is_refusal(checked):
        return checked
    return Ok(collected)


def _typed_frontiers(
    kind: str,
    ordered: Sequence[TypedPartitionRef],
    rows: Mapping[str, Sequence[tuple[object, ...]]],
    *,
    metadata: PinnedInstrumentPriceMetadata | None,
    month: str,
) -> Result[tuple[_QuoteFrontier, ...]]:
    """Build quote frontiers from tick rows, or from a bid and an ask bar series."""
    first = ordered[0]
    symbol = first.subject if metadata is None else metadata.instrument.symbol
    venue = first.source if metadata is None else metadata.instrument.venue.value
    license_tag = first.source
    if kind == _TICKS_KIND:
        built: list[_QuoteFrontier] = []
        for row in rows[first.variant or _TICKS_KIND]:
            event_ns = int(cast("int", row[0])) * _NS_PER_MS
            built.append(
                _QuoteFrontier(
                    event_ns=event_ns,
                    knowable_ns=event_ns,
                    bid=int(cast("int", row[1])),
                    ask=int(cast("int", row[2])),
                    scale=_SOURCE_PRICE_SCALE,
                    license_tag=license_tag,
                    resolution="tick",
                    symbol=symbol,
                    venue=venue,
                    bid_source_fp1=first.fingerprint,
                    ask_source_fp1=first.fingerprint,
                )
            )
        return Ok(tuple(built))
    bid_ref, ask_ref = ordered[0], ordered[1]
    bid_rows = rows["bid"]
    ask_rows = rows["ask"]
    if len(bid_rows) != len(ask_rows):
        return policy(
            "partitions",
            "the bid and ask bars of a month cover the same minutes",
            month=month,
            bid_rows=len(bid_rows),
            ask_rows=len(ask_rows),
        )
    paired: list[_QuoteFrontier] = []
    for bid_row, ask_row in zip(bid_rows, ask_rows, strict=True):
        bid_t = int(cast("int", bid_row[0]))
        ask_t = int(cast("int", ask_row[0]))
        if bid_t != ask_t:
            return policy(
                "partitions",
                "the bid and ask bars of a month cover the same minutes",
                month=month,
                bid_t=bid_t,
                ask_t=ask_t,
            )
        event_ns = bid_t * _NS_PER_MS
        # One m1 bar is one quote at its minute, priced at the bar's close, the last price the
        # minute traded and so the price a taker could have met at its end.
        paired.append(
            _QuoteFrontier(
                event_ns=event_ns,
                knowable_ns=event_ns,
                bid=int(cast("int", bid_row[4])),
                ask=int(cast("int", ask_row[4])),
                scale=_SOURCE_PRICE_SCALE,
                license_tag=license_tag,
                resolution=_BAR_KIND,
                symbol=symbol,
                venue=venue,
                bid_source_fp1=bid_ref.fingerprint,
                ask_source_fp1=ask_ref.fingerprint,
            )
        )
    return Ok(tuple(paired))


# --- the windowed reader for units (AD-205, QB-01, QB-02) ------------------------------------

WINDOW_MEMORY_TOLERANCE: Final[Decimal] = Decimal("0.10")
"""``[qmb] window_memory_tolerance``'s starting default: a run's peak memory at 200,000 steps
stays within 10% of its peak at 10,000 steps."""


_EPOCH: Final[datetime] = datetime(1970, 1, 1, tzinfo=UTC)
_NS_PER_US: Final[int] = 1_000


def _ns_of(moment: datetime) -> int:
    return (moment - _EPOCH) // timedelta(microseconds=1) * _NS_PER_US


@dataclass(frozen=True, slots=True)
class VenueDay:
    """The venue's trading day: each one starts at ``boundary`` wall time in ``zone``.

    It comes from the instrument record's ``zone`` and ``day_boundary`` (17:00 New York at most
    FX CFD brokers), so a daily bar closes where the venue's day does and moves with its
    daylight saving, never at UTC midnight.
    """

    zone: ZoneInfo
    boundary: time

    @classmethod
    def try_create(cls, zone: object, boundary: object) -> Result[VenueDay]:
        if not isinstance(boundary, str):
            return invalid("day_boundary", "a day boundary is wall time HH:MM", given=boundary)
        try:
            wall = time.fromisoformat(boundary)
        except ValueError:
            return invalid("day_boundary", "a day boundary is wall time HH:MM", given=boundary)
        if not isinstance(zone, str):
            return invalid("zone", "a venue zone is an IANA zone name", given=zone)
        try:
            return Ok(cls(ZoneInfo(zone), wall))
        except (ZoneInfoNotFoundError, ValueError):
            return invalid(
                "zone", "the venue zone is not in this machine's time zone data", zone=zone
            )

    def span(self, ns: int) -> tuple[int, int]:
        """The start and the end, in UTC ns, of the venue day that holds ``ns``."""
        date = (_EPOCH + timedelta(microseconds=ns // _NS_PER_US)).astimezone(self.zone).date()
        start = datetime.combine(date, self.boundary, self.zone)
        if _ns_of(start) > ns:
            start = datetime.combine(date - timedelta(days=1), self.boundary, self.zone)
        end = datetime.combine(start.date() + timedelta(days=1), self.boundary, self.zone)
        return _ns_of(start), _ns_of(end)


class Fidelity(StrEnum):
    """What a data card says QMB replays. Part A's data levels: bars 1, quotes 2, trades 4."""

    QUOTES = "quotes"
    TRADES = "trades"
    BARS = "bars"


class Aggressor(StrEnum):
    """The side that crossed the spread on a print: a buyer meets the ask, a seller the bid."""

    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class Tick:
    """A quote: both sides at one millisecond."""

    ms: int
    bid: Decimal
    ask: Decimal


@dataclass(frozen=True, slots=True)
class BarPair:
    """A bid bar and an ask bar of one stretch that opens at ``open_ms``."""

    open_ms: int
    bid: OHLC
    ask: OHLC


@dataclass(frozen=True, slots=True)
class Print:
    """A trade print with the side that crossed the spread."""

    ms: int
    price: Decimal
    aggressor: Aggressor


@dataclass(frozen=True, slots=True)
class Bar:
    """One bid-side bar that opens at ``open_ms``."""

    open_ms: int
    price: OHLC


Row = Tick | BarPair | Print | Bar
_Timed = tuple[int, str, QuoteBar]
_ROWS: Final[Mapping[Fidelity, tuple[type, ...]]] = MappingProxyType(
    {Fidelity.QUOTES: (Tick, BarPair), Fidelity.TRADES: (Print,), Fidelity.BARS: (Bar,)}
)


def _flat(price: Decimal) -> OHLC:
    return OHLC(price, price, price, price)


def _shifted(bar: OHLC, by: Decimal) -> OHLC:
    return OHLC(bar.open + by, bar.high + by, bar.low + by, bar.close + by)


@dataclass(frozen=True, slots=True)
class DataCard:
    """How one market's rows replay (QB-02).

    Quotes carry both sides. Trades and bars carry one price, so the card declares the spread,
    ask minus bid: a buyer's print is the ask and a seller's the bid, and a bar is the bid side.
    """

    fidelity: Fidelity
    spread: Decimal | None = None

    @classmethod
    def try_create(cls, fidelity: object, spread: object = None) -> Result[DataCard]:
        try:
            declared = Fidelity(str(fidelity))
        except ValueError:
            return invalid("fidelity", "a data card replays quotes, trades or bars", given=fidelity)
        if declared is Fidelity.QUOTES:
            if spread is not None:
                return invalid("spread", "quotes carry their own spread, so a card declares none")
            return Ok(cls(declared))
        if not isinstance(spread, Decimal) or not spread.is_finite() or spread < 0:
            return invalid(
                "spread",
                "trades and bars replay with a declared spread of zero or more",
                fidelity=declared.value,
            )
        return Ok(cls(declared, spread))

    def piece(self, row: Row) -> Result[Piece]:
        if not isinstance(row, _ROWS[self.fidelity]):
            return invalid(
                "rows",
                "a row is the kind of data its card declares",
                fidelity=self.fidelity.value,
                row=type(row).__name__,
            )
        spread = self.spread or Decimal(0)
        match row:
            case Tick(ms=ms, bid=bid, ask=ask):
                return Ok(Piece(ms * _NS_PER_MS, _flat(bid), _flat(ask)))
            case BarPair(open_ms=ms, bid=bid, ask=ask):
                return Ok(Piece(ms * _NS_PER_MS, bid, ask))
            case Print(ms=ms, price=price, aggressor=Aggressor.BUY):
                return Ok(Piece(ms * _NS_PER_MS, _flat(price - spread), _flat(price)))
            case Print(ms=ms, price=price):
                return Ok(Piece(ms * _NS_PER_MS, _flat(price), _flat(price + spread)))
            case Bar(open_ms=ms, price=price):
                return Ok(Piece(ms * _NS_PER_MS, price, _shifted(price, spread)))


def replay_feed(
    card: DataCard,
    rows: Iterable[Row | TypedRefusal],
    builder: BarBuilder,
    *,
    until_ns: int,
) -> Iterator[QuoteBar | TypedRefusal]:
    """One market's closed bars, built row by row; the data reaches ``until_ns``.

    The feed holds one forming bar, never the rows behind it. A refusal ends the feed.
    """
    for row in rows:
        if isinstance(row, TypedRefusal):
            yield row
            return
        piece = card.piece(row)
        if is_refusal(piece):
            yield piece
            return
        closed = builder.push(piece.value)
        if is_refusal(closed):
            yield closed
            return
        if closed.value is not None:
            yield closed.value
    last = builder.close(until_ns)
    if last is not None:
        yield last


def _csv_bars(path: Path) -> Iterator[tuple[int, OHLC] | TypedRefusal]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                yield (
                    int(row["timestamp"]),
                    OHLC(
                        Decimal(row["open"]),
                        Decimal(row["high"]),
                        Decimal(row["low"]),
                        Decimal(row["close"]),
                    ),
                )
    except (OSError, KeyError, ValueError, InvalidOperation) as error:
        yield invalid(
            "bars",
            "a bar file is rows of timestamp, open, high, low, close",
            file=str(path),
            error=str(error),
        )


def read_bar_csv(path: Path) -> Iterator[Bar | TypedRefusal]:
    """Stream one side's bar file, as the Dukascopy download template saves it."""
    for item in _csv_bars(path):
        yield item if isinstance(item, TypedRefusal) else Bar(*item)


def read_bar_pair_csv(bid: Path, ask: Path) -> Iterator[BarPair | TypedRefusal]:
    """Stream a bid file and an ask file together, keeping the stretches both sides have.

    Half a pair is never a quote, so a minute only one file holds is skipped.
    """
    bids, asks = _csv_bars(bid), _csv_bars(ask)
    left, right = next(bids, None), next(asks, None)
    while left is not None and right is not None:
        if isinstance(left, TypedRefusal) or isinstance(right, TypedRefusal):
            yield cast("TypedRefusal", left if isinstance(left, TypedRefusal) else right)
            return
        if left[0] == right[0]:
            yield BarPair(left[0], left[1], right[1])
            left, right = next(bids, None), next(asks, None)
        elif left[0] < right[0]:
            left = next(bids, None)
        else:
            right = next(asks, None)


class BarWindow(Mapping[int, QuoteBar]):
    """One market's last ``size`` closed bars by the instant each became knowable."""

    def __init__(self, size: int) -> None:
        self._size = size
        self._bars: OrderedDict[int, QuoteBar] = OrderedDict()

    def push(self, bar: QuoteBar) -> None:
        self._bars[bar.knowable_at.value_ns] = bar
        if len(self._bars) > self._size:
            self._bars.popitem(last=False)

    def __getitem__(self, key: int) -> QuoteBar:
        return self._bars[key]

    def __iter__(self) -> Iterator[int]:
        return iter(self._bars)

    def __len__(self) -> int:
        return len(self._bars)


def window_size(compiled: CompiledUnit, lookback: int = 0) -> int:
    """The unit's derived warm-up on its stream plus its declared lookback, one bar at least."""
    return max(1, compiled.warm_up.get(compiled.plan.stream, 0) + lookback)


def replay_windowed(
    handler: UnitSliceHandler,
    feeds: Mapping[str, Iterable[QuoteBar | TypedRefusal]],
    windows: Mapping[str, BarWindow],
) -> Result[int]:
    """Drive ``handler`` one bar instant at a time over every market's feed; answer the steps.

    ``windows`` are the bars the handler was started with, so each bar enters its market's
    window just before the slice that observes it.
    """
    streams = StreamSet.try_create([DeclaredStream(market, market) for market in feeds])
    if is_refusal(streams):
        return streams
    failed: list[TypedRefusal] = []

    def timed(market: str, feed: Iterable[QuoteBar | TypedRefusal]) -> Iterator[_Timed]:
        for item in feed:
            if isinstance(item, TypedRefusal):
                failed.append(item)
                return
            yield item.knowable_at.value_ns, market, item

    merged = heapq.merge(*(timed(m, f) for m, f in feeds.items()), key=lambda t: (t[0], t[1]))
    frontier: Instant | None = None
    resting: tuple[RestingIntent, ...] = ()
    steps = 0
    for ns, group in groupby(merged, key=lambda t: t[0]):
        observed: list[SliceObservation] = []
        for _, market, bar in group:
            windows[market].push(bar)
            observed.append(SliceObservation(market, Instant(ns)))
        if failed:
            return failed[0]
        outcome = run_slice(
            observed,
            stream_set=streams.value,
            current_frontier=frontier,
            handler=handler,
            resting=resting,
        )
        if is_refusal(outcome):
            return outcome
        frontier, resting = outcome.value.frontier, outcome.value.resting
        steps += 1
    if failed:
        return failed[0]
    return Ok(steps)
