"""Materialize bitemporal CT-10 artifacts for provider-free replay, and replay units windowed.

This adapter reads immutable QMF raw-archive artifacts through the QMF-owned
source-observation boundary. It preserves foreign prices and their declared
scales verbatim; it does not convert them into QMB execution prices.

The windowed reader (Part B AD-205, QB-01, QB-02) streams a unit's data row by row: each
market's rows become pieces as its data card's fidelity declares (quotes, trades or bars),
the bar builder folds them into the unit's bars in the venue's day, and each market keeps only
a window of the unit's derived warm-up plus its declared lookback. The run's memory is the
window's, whatever the run's length, and nothing caps the steps.

A futures market replays contract by contract (QB-05): the data card's stitching record names
the contracts and their roll instants, each contract's bars are its own prices, and the roll is
an event in the feed, never a back-adjusted price. At a roll the market's window holds the next
contract's own bars from before the roll, so the unit's warm-up never mixes two contracts.
"""

# pyarrow ships no type stubs; as in the QMF store's typed writer, the unknown-type rules are
# disabled at file scope here so the rest of this module stays strictly typed.
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import csv
import heapq
from collections import OrderedDict, deque
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
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
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.source_split import partition_source_observation
from qmf.data.splits import SegmentRole, SplitManifest
from qmf.data.store import EvidenceStore
from qml.compile import CompiledUnit
from qml.protocol import MappingReadSurface
from qml.protocol.unit import OHLC, QuoteBar

from qmb._refuse import invalid, policy
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
    "FuturesChain",
    "PinnedInstrumentPriceMetadata",
    "Print",
    "RecordedReplaySource",
    "Roll",
    "RollHook",
    "Row",
    "SliceHook",
    "Tick",
    "VenueDay",
    "futures_feed",
    "read_bar_csv",
    "read_bar_pair_csv",
    "read_bar_pair_parquet",
    "read_recorded_replay_source",
    "read_tick_parquet",
    "replay_feed",
    "replay_windowed",
    "window_size",
]

_REPLAY_SOURCE_CLASS: Final[str] = "qmb-recorded-replay-source-v1"
_NS_PER_MS: Final[int] = 1_000_000


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

    ``observations`` are the CT-10 receipts the archive boundary admitted.
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

    def fp1_identity(self) -> dict[str, object]:
        identity: dict[str, object] = {
            "class": _REPLAY_SOURCE_CLASS,
            "stream_id": self.stream_id,
            "world": self.world.value,
        }
        identity["observations"] = [item.fingerprint.value for item in self.observations]
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
    observations: tuple[SourceObservation, ...] = (),
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
        )
    )


# --- the windowed reader for units (AD-205, QB-01, QB-02) ------------------------------------

WINDOW_MEMORY_TOLERANCE: Final[Decimal] = Decimal("0.10")
"""``[qmb] window_memory_tolerance``'s starting default: a run's peak memory at 200,000 steps
stays within 10% of its peak at 10,000 steps."""


_EPOCH: Final[datetime] = datetime(1970, 1, 1, tzinfo=UTC)
_NS_PER_US: Final[int] = 1_000
_BAR_M1_SECONDS: Final[int] = 60


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
    """A bid bar and an ask bar of one stretch that opens at ``open_ms`` and lasts ``seconds``."""

    open_ms: int
    seconds: int
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
    """One bid-side bar that opens at ``open_ms`` and lasts ``seconds``."""

    open_ms: int
    seconds: int
    price: OHLC


Row = Tick | BarPair | Print | Bar
_Timed = tuple[int, int, str, QuoteBar]
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
                return Ok(_instant(ms, _flat(bid), _flat(ask)))
            case BarPair(open_ms=ms, seconds=seconds, bid=bid, ask=ask):
                return Ok(_stretch(ms, seconds, bid, ask))
            case Print(ms=ms, price=price, aggressor=Aggressor.BUY):
                return Ok(_instant(ms, _flat(price - spread), _flat(price)))
            case Print(ms=ms, price=price):
                return Ok(_instant(ms, _flat(price), _flat(price + spread)))
            case Bar(open_ms=ms, seconds=seconds, price=price):
                return Ok(_stretch(ms, seconds, price, _shifted(price, spread)))


def _instant(ms: int, bid: OHLC, ask: OHLC) -> Piece:
    return Piece(ms * _NS_PER_MS, ms * _NS_PER_MS, bid, ask)


def _stretch(open_ms: int, seconds: int, bid: OHLC, ask: OHLC) -> Piece:
    return Piece(open_ms * _NS_PER_MS, (open_ms + seconds * 1_000) * _NS_PER_MS, bid, ask)


def replay_feed(
    card: DataCard,
    rows: Iterable[Row | TypedRefusal],
    builder: BarBuilder,
    *,
    until_ns: int = 0,
) -> Iterator[QuoteBar | TypedRefusal]:
    """One market's closed bars, built row by row.

    The data reaches ``until_ns`` or the end of its last row, whichever is later. A file of
    whole bars needs no ``until_ns``: its last bar closes with its last row. Ticks and prints
    end where they start, so their last bar closes only when ``until_ns`` reaches its end,
    which is the request's end. The feed holds one forming bar, never the rows behind it. A
    refusal ends the feed.
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


def read_bar_csv(path: Path, seconds: int) -> Iterator[Bar | TypedRefusal]:
    """Stream one side's file of ``seconds`` bars, as the Dukascopy download template saves it."""
    for item in _csv_bars(path):
        yield item if isinstance(item, TypedRefusal) else Bar(item[0], seconds, item[1])


def read_bar_pair_csv(bid: Path, ask: Path, seconds: int) -> Iterator[BarPair | TypedRefusal]:
    """Stream a bid file and an ask file of ``seconds`` bars, keeping stretches both sides have."""
    return _paired(_csv_bars(bid), _csv_bars(ask), seconds)


def _parquet_batches(
    paths: Sequence[Path], columns: Sequence[str]
) -> Iterator[list[list[int]] | TypedRefusal]:
    """One side's copied months in order, a batch at a time, these whole-number columns."""
    import pyarrow.parquet as pq  # noqa: PLC0415 (only a read of the store needs the library)

    try:
        for path in paths:
            with pq.ParquetFile(path) as months:
                for batch in months.iter_batches(batch_size=50_000, columns=list(columns)):
                    yield [batch.column(name).to_pylist() for name in columns]
    except (OSError, ValueError, KeyError) as error:
        yield invalid(
            "data",
            "a market's store months are readable typed Parquet files",
            files=[str(path) for path in paths],
            error=str(error),
        )


def read_tick_parquet(
    paths: Sequence[Path], scale: int, start_ms: int, end_ms: int
) -> Iterator[Tick | TypedRefusal]:
    """Stream a market's copied tick months inside the window, as prices at the series' scale.

    This is a month's hottest loop, millions of rows, so it walks whole batches."""
    for batch in _parquet_batches(paths, ("t", "bid", "ask")):
        if isinstance(batch, TypedRefusal):
            yield batch
            return
        for ms, bid, ask in zip(*batch, strict=True):
            if start_ms <= ms < end_ms:
                yield Tick(ms, Decimal(bid).scaleb(-scale), Decimal(ask).scaleb(-scale))


def _parquet_bars(
    paths: Sequence[Path], scale: int, start_ms: int, end_ms: int
) -> Iterator[tuple[int, OHLC] | TypedRefusal]:
    for batch in _parquet_batches(paths, ("t", "open", "high", "low", "close")):
        if isinstance(batch, TypedRefusal):
            yield batch
            return
        for ms, *prices in zip(*batch, strict=True):
            if start_ms <= ms < end_ms:
                yield ms, OHLC(*(Decimal(price).scaleb(-scale) for price in prices))


def read_bar_pair_parquet(
    bid: Sequence[Path], ask: Sequence[Path], scale: int, start_ms: int, end_ms: int
) -> Iterator[BarPair | TypedRefusal]:
    """Stream a market's copied ``bar-m1`` bid and ask months inside the window."""
    return _paired(
        _parquet_bars(bid, scale, start_ms, end_ms),
        _parquet_bars(ask, scale, start_ms, end_ms),
        _BAR_M1_SECONDS,
    )


def _paired(
    bids: Iterator[tuple[int, OHLC] | TypedRefusal],
    asks: Iterator[tuple[int, OHLC] | TypedRefusal],
    seconds: int,
) -> Iterator[BarPair | TypedRefusal]:
    """Half a pair is never a quote, so a stretch only one side holds is skipped."""
    left, right = next(bids, None), next(asks, None)
    while left is not None and right is not None:
        if isinstance(left, TypedRefusal) or isinstance(right, TypedRefusal):
            yield cast("TypedRefusal", left if isinstance(left, TypedRefusal) else right)
            return
        if left[0] == right[0]:
            yield BarPair(left[0], seconds, left[1], right[1])
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

    def reset(self, bars: Iterable[QuoteBar]) -> None:
        """Hold ``bars`` alone, as a roll does with the next contract's own bars."""
        self._bars.clear()
        for bar in bars:
            self.push(bar)

    def __getitem__(self, key: int) -> QuoteBar:
        return self._bars[key]

    def __iter__(self) -> Iterator[int]:
        return iter(self._bars)

    def __len__(self) -> int:
        return len(self._bars)


def window_size(compiled: CompiledUnit, lookback: int = 0) -> int:
    """The unit's derived warm-up on its stream plus its declared lookback, one bar at least."""
    return max(1, compiled.warm_up.get(compiled.plan.stream, 0) + lookback)


SliceHook = Callable[[Instant, Sequence[str]], None]
"""Told each slice's instant and the markets whose bar closed there, before the slice runs."""

RollHook = Callable[[str, "Roll"], None]
"""Told each market's roll, once, at the roll's instant and before any slice there runs."""


def replay_windowed(
    handler: UnitSliceHandler,
    feeds: Mapping[str, Iterable[QuoteBar | Roll | TypedRefusal]],
    windows: Mapping[str, BarWindow],
    *,
    on_slice: SliceHook | None = None,
    on_roll: RollHook | None = None,
) -> Result[int]:
    """Drive ``handler`` one bar instant at a time over every market's feed; answer the steps.

    ``windows`` are the bars the handler was started with, so each bar enters its market's
    window just before the slice that observes it. A slice lists its markets in the order of
    ``feeds``. A futures feed's roll swaps its market's window for the next contract's own bars
    before the slice at the roll's instant. A unit cannot yet see a roll and act on it with its
    exits, so a roll reached while the unit holds or waits to fill on that market refuses the
    run rather than carry a position from one contract into the next.
    """
    streams = StreamSet.try_create([DeclaredStream(market, market) for market in feeds])
    if is_refusal(streams):
        return streams
    failed: list[TypedRefusal] = []

    def timed(
        order: int, market: str, feed: Iterable[QuoteBar | Roll | TypedRefusal]
    ) -> Iterator[tuple[int, int, str, QuoteBar | Roll]]:
        for item in feed:
            if isinstance(item, TypedRefusal):
                failed.append(item)
                return
            at = item.at_ns if isinstance(item, Roll) else item.knowable_at.value_ns
            yield at, order, market, item

    merged = heapq.merge(
        *(timed(i, m, f) for i, (m, f) in enumerate(feeds.items())), key=lambda t: (t[0], t[1])
    )
    frontier: Instant | None = None
    resting: tuple[RestingIntent, ...] = ()
    steps = 0
    for ns, group in groupby(merged, key=lambda t: t[0]):
        markets: list[str] = []
        for _, _, market, item in group:
            if isinstance(item, Roll):
                held = market in handler.open_positions or any(
                    r.stream_id == market for r in resting
                )
                if held:
                    return policy(
                        "roll",
                        "a futures roll was reached with a position or a resting order on the "
                        "market; QMB never carries one from one contract into the next",
                        market=market,
                        contract=item.contract,
                        next_contract=item.next_contract,
                        at_ns=item.at_ns,
                    )
                windows[market].reset(item.warm)
                if on_roll is not None:
                    on_roll(market, item)
                continue
            windows[market].push(item)
            markets.append(market)
        if failed:
            return failed[0]
        if not markets:
            continue
        if on_slice is not None:
            on_slice(Instant(ns), markets)
        outcome = run_slice(
            [SliceObservation(market, Instant(ns)) for market in markets],
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


# --- futures, contract by contract (QB-05) ---------------------------------------------------

CONTRACT_BY_CONTRACT: Final[str] = "contract-by-contract"


@dataclass(frozen=True, slots=True)
class Roll:
    """A futures market moved from ``contract`` to ``next_contract`` at ``at_ns``.

    It is an event and moves no price: ``warm`` is the next contract's own last bars before the
    roll, which become the market's window.
    """

    at_ns: int
    contract: str
    next_contract: str
    warm: tuple[QuoteBar, ...] = ()

    def as_record(self) -> dict[str, object]:
        return {
            "event_kind": "roll",
            "at_ns": self.at_ns,
            "contract": self.contract,
            "next_contract": self.next_contract,
        }


def _utc_ns(text: object) -> int | None:
    if not isinstance(text, str):
        return None
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        return None
    return _ns_of(moment)


@dataclass(frozen=True, slots=True)
class FuturesChain:
    """The contracts a futures series replays, in order, and the instant each one rolls."""

    contracts: tuple[str, ...]
    rolls_ns: tuple[int, ...]

    @classmethod
    def try_create(cls, card: Mapping[str, object]) -> Result[FuturesChain]:
        """Read a ``dataset`` card's ``stitching`` and ``rolls`` (version 2).

        Only a contract-by-contract card replays. A card that says its prices were adjusted is
        refused by name, because a back-adjusted price is a price no contract ever traded at.
        """
        stitching = card.get("stitching")
        if not isinstance(stitching, Mapping):
            return invalid("stitching", "a futures card states how its contracts are stitched")
        shape = cast("Mapping[str, object]", stitching)
        if shape.get("method") != CONTRACT_BY_CONTRACT or shape.get("adjusted") is not False:
            return policy(
                "stitching",
                "QMB replays futures contract by contract and never a back-adjusted price",
                method=shape.get("method"),
                adjusted=shape.get("adjusted"),
            )
        rolls = card.get("rolls")
        if not isinstance(rolls, list) or not rolls:
            return invalid("rolls", "a futures card lists at least one roll")
        contracts: list[str] = []
        instants: list[int] = []
        for index, raw in enumerate(cast("list[object]", rolls)):
            if not isinstance(raw, Mapping):
                return invalid("rolls", "a roll is {at, from, to}", index=index)
            roll = cast("Mapping[str, object]", raw)
            at, old, new = _utc_ns(roll.get("at")), roll.get("from"), roll.get("to")
            if at is None or not isinstance(old, str) or not isinstance(new, str) or not old:
                return invalid(
                    "rolls", "a roll names its UTC instant and both contracts", index=index
                )
            if contracts and (old != contracts[-1] or at <= instants[-1]):
                return invalid(
                    "rolls",
                    "each roll starts from the contract the last one rolled to, later in time",
                    index=index,
                )
            contracts += [new] if contracts else [old, new]
            instants.append(at)
        return Ok(cls(tuple(contracts), tuple(instants)))


def futures_feed(
    chain: FuturesChain,
    card: DataCard,
    rows: Mapping[str, Callable[[], Iterable[Row | TypedRefusal]]],
    builder: Callable[[], BarBuilder],
    *,
    window: int,
    until_ns: int = 0,
) -> Iterator[QuoteBar | Roll | TypedRefusal]:
    """One futures market's bars, each contract's own, with a roll between two contracts.

    ``rows`` opens each contract's own rows. A contract's bars that become knowable before its
    roll in are kept, the last ``window`` of them, as the window it rolls in with, and its bars
    from its roll out on are never read. The last contract runs to ``until_ns``.
    """
    for index, contract in enumerate(chain.contracts):
        opens = rows.get(contract)
        if opens is None:
            yield invalid("rows", "every contract on the card has its rows", contract=contract)
            return
        roll_in = chain.rolls_ns[index - 1] if index else None
        roll_out = chain.rolls_ns[index] if index < len(chain.rolls_ns) else None
        warm: deque[QuoteBar] = deque(maxlen=max(1, window))
        pending = roll_in is not None
        feed = replay_feed(card, opens(), builder(), until_ns=until_ns if roll_out is None else 0)
        for bar in feed:
            if isinstance(bar, TypedRefusal):
                yield bar
                return
            at = bar.knowable_at.value_ns
            if roll_out is not None and at >= roll_out:
                break
            if roll_in is not None and pending and at < roll_in:
                warm.append(bar)
                continue
            if roll_in is not None and pending:
                yield Roll(roll_in, chain.contracts[index - 1], contract, tuple(warm))
                pending = False
            yield bar
        if roll_in is not None and pending:
            yield Roll(roll_in, chain.contracts[index - 1], contract, tuple(warm))
