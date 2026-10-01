"""Materialize bitemporal CT-10 artifacts for provider-free replay.

This adapter reads immutable QMF raw-archive artifacts through the QMF-owned
source-observation boundary. It preserves foreign prices and their declared
scales verbatim; it does not convert them into QMB execution prices.
"""

from __future__ import annotations

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
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.source_split import partition_source_observation
from qmf.data.splits import SegmentRole, SplitManifest
from qmf.data.store import EvidenceStore
from qml.protocol import MappingReadSurface

from qmb._refuse import invalid, policy
from qmb.execution.ports import SlicePath
from qmb.runloop.loop import EventSlice, SliceObservation

__all__ = [
    "PinnedInstrumentPriceMetadata",
    "RecordedReplaySource",
    "read_recorded_replay_source",
]

_REPLAY_SOURCE_CLASS: Final[str] = "qmb-recorded-replay-source-v1"


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
    """Validated CT-10 evidence arranged as replay slices and QML read surfaces."""

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

    def fp1_identity(self) -> dict[str, object]:
        identity: dict[str, object] = {
            "class": _REPLAY_SOURCE_CLASS,
            "observations": [item.fingerprint.value for item in self.observations],
            "stream_id": self.stream_id,
            "world": self.world.value,
        }
        if self.price_metadata_fp1 is not None:
            identity["price_metadata_fp1"] = self.price_metadata_fp1.value
        if self.split_fp1 is not None and self.split_role is not None:
            identity["split_fp1"] = self.split_fp1.value
            identity["split_role"] = self.split_role.value
        return identity


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

    slices: list[EventSlice] = []
    frames: dict[int, object] = {}
    cumulative: list[object] = []
    execution_paths: list[SlicePath] = []
    previous_frontier: int | None = None
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
        knowable_ns = max(event_ns, bid.known_at.value_ns, ask.known_at.value_ns)
        if previous_frontier is not None and knowable_ns <= previous_frontier:
            return invalid(
                "known_at",
                "replay frontiers are strictly increasing and one stream emits once per frontier",
                frontier_ns=knowable_ns,
            )
        knowable = Instant.try_create(knowable_ns)
        event = Instant.try_create(event_ns)
        if is_refusal(knowable) or is_refusal(event):
            return invalid(
                "instant", "CT-10 replay instants are valid QMF Instants", instant_ns=event_ns
            )
        quote_value: Mapping[str, object] = MappingProxyType(
            {
                "ask": {
                    "amount": ask.foreign_money.verbatim,
                    "scale": ask.foreign_money.scale,
                    "source_fp1": ask.fingerprint.value,
                },
                "bid": {
                    "amount": bid.foreign_money.verbatim,
                    "scale": bid.foreign_money.scale,
                    "source_fp1": bid.fingerprint.value,
                },
                "event_time_ns": event_ns,
                "license_tag": bid_context.license_tag,
                "resolution": bid_context.resolution,
                "symbol": bid_context.symbol,
                "venue": bid_context.venue,
            }
        )
        if instrument_metadata is not None:
            metadata = instrument_metadata
            if (
                bid_context.venue != metadata.instrument.venue.value
                or bid_context.symbol != metadata.instrument.symbol
                or bid.foreign_money.scale != metadata.price_scale
                or ask.foreign_money.scale != metadata.price_scale
            ):
                return policy(
                    "instrument_metadata",
                    "CT-10 quote coordinates and source scales match pinned CT-03 metadata",
                    instant_ns=event_ns,
                )
            bid_price = Price.try_create(
                bid.foreign_money.verbatim, metadata.instrument, metadata.price_scale
            )
            ask_price = Price.try_create(
                ask.foreign_money.verbatim, metadata.instrument, metadata.price_scale
            )
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
    stamped = fingerprint(identity)
    if is_refusal(stamped):
        return stamped
    return Ok(
        RecordedReplaySource(
            world=World.REPLAY,
            stream_id=stream_id,
            observations=tuple(observations),
            slices=tuple(slices),
            read_surfaces=MappingProxyType({stream_id: built_surface.value}),
            execution_paths=tuple(execution_paths),
            price_metadata_fp1=(
                None if instrument_metadata is None else instrument_metadata.fingerprint
            ),
            split_fp1=(
                None
                if not isinstance(split_manifest, SplitManifest)
                else split_manifest.fingerprint
            ),
            split_role=(None if not isinstance(split_role, SegmentRole) else split_role),
            fingerprint=stamped.value,
        )
    )
