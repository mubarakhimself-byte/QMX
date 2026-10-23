"""Materialize bitemporal CT-10 artifacts for provider-free replay.

This adapter reads immutable QMF raw-archive artifacts through the QMF-owned
source-observation boundary. It preserves foreign prices and their declared
scales verbatim; it does not convert them into QMB execution prices.
"""

from __future__ import annotations

import re
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from qmf.core.chrono import Instant
from qmf.core.exact import Price
from qmf.core.fingerprint import Fingerprint, World, fingerprint
from qmf.core.identity import Instrument
from qmf.core.refusal import Ok, Result, is_refusal
from qmf.data.observation import SourceObservation
from qmf.data.seal import HoldoutSeal
from qmf.data.series import rule_for
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.source_split import partition_source_observation
from qmf.data.splits import SegmentRole, SplitManifest
from qmf.data.store import EvidenceStore
from qmf.data.store.engines import StoreEngineError
from qmf.data.store.engines.typed import TypedWriter
from qml.protocol import MappingReadSurface

from qmb._refuse import invalid, policy
from qmb.data import policy as data_policy
from qmb.execution.ports import SlicePath
from qmb.runloop.loop import EventSlice, SliceObservation

__all__ = [
    "PinnedInstrumentPriceMetadata",
    "RecordedReplaySource",
    "TypedPartitionRef",
    "read_recorded_replay_source",
    "read_typed_replay_source",
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
    metadata = cast("PinnedInstrumentPriceMetadata | None", instrument_metadata)
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
        return invalid(
            "partitions", "a typed replay read pairs one kind at a time", kinds=kinds
        )
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

    The fingerprint is the writer's own streamed hash over the pinned logical encoding, so the
    rows pass through the same writer again (`TypedWriter`) instead of through a second copy of
    the encoding. A file whose rows do not hash to its claimed fingerprint is refused before a
    single quote is built, so a substituted or truncated copy cannot pass as that partition.
    """
    try:
        import pyarrow.parquet as pq  # noqa: PLC0415 (only a read needs the library)
    except ImportError as exc:  # pragma: no cover - qmf-data ships pyarrow
        return invalid("partitions", "reading a typed partition needs pyarrow", error=str(exc))
    key = f"{ref.series}/{ref.month}"
    collected: list[tuple[object, ...]] = []
    computed = ""
    with tempfile.TemporaryDirectory(
        prefix="qmb-typed-", ignore_cleanup_errors=True
    ) as scratch:
        target = Path(scratch) / "verify.parquet"
        try:
            writer = TypedWriter(target, key, columns)
            for batch in pq.ParquetFile(ref.path).iter_batches(batch_size=50_000):
                batch_rows = [
                    tuple(row[name] for name in columns) for row in batch.to_pylist()
                ]
                writer.add(batch_rows)
                collected.extend(batch_rows)
            computed = writer.finish().fingerprint
        except (OSError, ValueError, KeyError, StoreEngineError) as exc:
            return invalid(
                "partitions",
                "a typed partition is a readable typed Parquet file",
                series=ref.series,
                month=ref.month,
                error=str(exc),
            )
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
