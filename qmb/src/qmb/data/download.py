"""``qmb data download`` — thin front over CT-10/CT-15 (B-11, Story 18.1).

Parses the acquisition request, selects a :class:`~qmb.data.ports.ProviderAdapter`,
fetches through CT-15, and admits CT-10 observations into the world-scoped raw
room. No second data layer: persistence is entirely qmf-data.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast

from qmf.core.chrono import WriterId
from qmf.core.fingerprint import World
from qmf.core.refusal import Ok, Result, is_refusal
from qmf.data.dukascopy import PERSONAL_USE_LICENSE, LicenseTag, parse_license_tag
from qmf.data.ingest import (
    ExternalSourceIngest,
    IntakeKey,
    IntakeOutcome,
    IntakeReceipt,
    ProviderRecord,
    SourceRequest,
)
from qmf.data.intake_authority import IntakeAuthority
from qmf.data.observation import MarketDataContext, SourceObservation
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore

from qmb._refuse import clean_token, invalid, unavailable
from qmb.data.catalog import persist_coverage_windows
from qmb.data.ports import (
    DOWNLOAD_SIDES,
    DownloadProgress,
    DownloadSide,
    ProgressSink,
    ProviderAdapter,
    ProviderFetchRequest,
)

__all__ = [
    "DownloadReceipt",
    "DownloadRequest",
    "download",
    "parse_download_request",
    "resolve_end_ns",
]


@dataclass(frozen=True, slots=True)
class DownloadRequest:
    """Parsed ``(venue, symbols, start, end, resolution, side)`` acquisition request."""

    venue: str
    symbols: tuple[str, ...]
    start_ns: int
    end_ns: int
    resolution: str
    side: DownloadSide
    destination: str
    overwrite: bool
    license_tag: LicenseTag
    world: World
    revision: str


@dataclass(frozen=True, slots=True)
class DownloadReceipt:
    """Machine-readable download outcome — counts, windows, progress samples."""

    command: str
    venue: str
    symbols: tuple[str, ...]
    start_ns: int
    end_ns: int
    resolution: str
    side: str
    destination: str
    revision: str
    license_tag: str
    produced: int
    idempotent: int
    admitted: int
    overwrite: bool
    source: str
    progress: tuple[DownloadProgress, ...]
    windows: tuple[Mapping[str, object], ...]

    def as_mapping(self) -> dict[str, object]:
        """Door-transport payload; ``command`` keeps CLI formatting stable."""
        return {
            "command": self.command,
            "venue": self.venue,
            "symbols": self.symbols,
            "start_ns": self.start_ns,
            "end_ns": self.end_ns,
            "resolution": self.resolution,
            "side": self.side,
            "destination": self.destination,
            "revision": self.revision,
            "license_tag": self.license_tag,
            "produced": self.produced,
            "idempotent": self.idempotent,
            "admitted": self.admitted,
            "overwrite": self.overwrite,
            "source": self.source,
            "progress": tuple(
                {
                    "percent": sample.percent,
                    "date_reached_ns": sample.date_reached_ns,
                    "eta_ns": sample.eta_ns,
                    "symbol": sample.symbol,
                    "produced": sample.produced,
                    "total_batches": sample.total_batches,
                    "completed_batches": sample.completed_batches,
                }
                for sample in self.progress
            ),
            "windows": self.windows,
        }


def resolve_end_ns(end: object | None, *, now: datetime | None = None) -> Result[int]:
    """Resolve ``end``; blank defaults to end-of-today UTC (exclusive next midnight).

    The default derives from the INJECTED ``now`` — a composition root's clock
    reading — never from an ambient system-clock read below the root (FR-002,
    DEC-0106). An end-less request with no injected reading is an ``invalid
    input`` refusal, so the resolved window can never silently track the real
    wall clock.
    """
    if end is None:
        if now is None:
            return invalid(
                "end",
                "an end-less download derives end-of-today from the composition "
                "root's injected clock reading; pass end, or inject now "
                "(FR-002, DEC-0106)",
            )
        tomorrow = datetime(now.year, now.month, now.day, tzinfo=timezone.utc) + timedelta(days=1)
        return Ok(int(tomorrow.timestamp() * 1_000_000_000))
    return _as_ns(end, field="end")


def parse_download_request(resources: Mapping[str, object]) -> Result[DownloadRequest]:
    """Validate door/library resources into a :class:`DownloadRequest`."""
    venue = clean_token(resources.get("venue"))
    if venue is None:
        return invalid(
            "venue",
            "download names a non-empty venue token",
            given=repr(resources.get("venue")),
        )
    symbols = _as_symbols(resources.get("symbol", resources.get("symbols")))
    if is_refusal(symbols):
        return symbols
    start = _as_ns(resources.get("start", resources.get("start_ns")), field="start")
    if is_refusal(start):
        return start
    # The clock-injection key is ``now``, carrying an aware datetime — a recorded
    # FC-14 decision (no ratified authority defines the key; DEC-0106 demands the
    # reading be injected by the composition root, never read ambiently here).
    injected_now = resources.get("now")
    end = resolve_end_ns(
        resources.get("end", resources.get("end_ns")),
        now=injected_now if isinstance(injected_now, datetime) else None,
    )
    if is_refusal(end):
        return end
    if end.value <= start.value:
        return invalid(
            "window",
            "download window is a non-empty half-open [start, end)",
            start_ns=start.value,
            end_ns=end.value,
        )
    resolution = clean_token(resources.get("resolution")) or "tick"
    side_raw = resources.get("side", DownloadSide.BOTH.value)
    side = _as_side(side_raw)
    if is_refusal(side):
        return side
    destination = clean_token(resources.get("destination"))
    if destination is None:
        return invalid(
            "destination",
            "download writes into a non-empty destination (raw-archive root)",
            given=repr(resources.get("destination")),
        )
    overwrite = bool(resources.get("overwrite", False))
    license_tag = parse_license_tag(resources.get("license_tag", PERSONAL_USE_LICENSE))
    world = _as_world(resources.get("world", World.REPLAY))
    if is_refusal(world):
        return world
    receive = resources.get("receive_wall_time")
    if overwrite:
        stamp = receive if isinstance(receive, int) and not isinstance(receive, bool) else end.value
        revision = clean_token(resources.get("revision")) or f"r-{stamp}"
    else:
        revision = clean_token(resources.get("revision")) or "r1"
    return Ok(
        DownloadRequest(
            venue=venue,
            symbols=symbols.value,
            start_ns=start.value,
            end_ns=end.value,
            resolution=resolution,
            side=side.value,
            destination=destination,
            overwrite=overwrite,
            license_tag=license_tag,
            world=world.value,
            revision=revision,
        )
    )


def download(
    resources: Mapping[str, object],
    *,
    adapter: ProviderAdapter | None = None,
    store: EvidenceStore | None = None,
    boundary: SourceObservationBoundary | None = None,
    writer: WriterId | None = None,
    progress: ProgressSink | None = None,
) -> Result[DownloadReceipt]:
    """Fetch once through the provider port and admit CT-10 into the raw room."""
    parsed = parse_download_request(resources)
    if is_refusal(parsed):
        return parsed
    request = parsed.value
    port = adapter if adapter is not None else resources.get("adapter")
    if not isinstance(port, ProviderAdapter):
        return unavailable(
            "adapter",
            "download requires an injected ProviderAdapter (Dukascopy #1); "
            "qmb never opens a provider socket itself",
            given=repr(type(port).__name__ if port is not None else None),
        )
    evidence = store
    if evidence is None:
        raw_store = resources.get("store")
        if isinstance(raw_store, EvidenceStore):
            evidence = raw_store
    gate = boundary
    if gate is None:
        raw_boundary = resources.get("boundary")
        if isinstance(raw_boundary, SourceObservationBoundary):
            gate = raw_boundary
    if gate is None:
        if evidence is None:
            evidence = EvidenceStore(Path(request.destination))
        gate = SourceObservationBoundary(evidence)

    active_writer = writer
    if active_writer is None:
        raw_writer = resources.get("writer")
        if isinstance(raw_writer, WriterId):
            active_writer = raw_writer
    if active_writer is None:
        minted = WriterId.try_create("qmb", "data", "download", "boot-1")
        if is_refusal(minted):
            return minted
        active_writer = minted.value

    sink = progress
    if sink is None:
        raw_sink = resources.get("progress")
        if isinstance(raw_sink, ProgressSink):
            sink = raw_sink

    receive = resources.get("receive_wall_time")
    if isinstance(receive, bool) or not isinstance(receive, int):
        receive = request.end_ns

    # CT-15 owns normalization. QMF's per-world CT-13 stream is the durable key
    # authority; the application-local file is never consulted for deduplication.
    if evidence is None:
        return invalid("store", "download requires the QMF EvidenceStore for CT-10 and CT-13")
    world_store = evidence.for_world(request.world)
    if is_refusal(world_store):
        return world_store
    authority = IntakeAuthority.resume(
        world_store.value.journal,
        active_writer,
        stream_name="ct15-intake-authority",
    )
    if is_refusal(authority):
        return authority
    from qmf.core import Instant  # noqa: PLC0415 — keeps QMB's main import surface small

    journal_instant = Instant.try_create(receive)
    if is_refusal(journal_instant):
        return journal_instant

    produced = 0
    idempotent = 0
    admitted = 0
    samples: list[DownloadProgress] = []
    windows: list[Mapping[str, object]] = []
    total = len(request.symbols)
    sequence = 0
    for index, symbol in enumerate(request.symbols):
        fetch_req = ProviderFetchRequest(
            source=port.source,
            symbol=symbol,
            start_ns=request.start_ns,
            end_ns=request.end_ns,
            resolution=request.resolution,
            side=request.side,
            revision=request.revision,
            license_tag=request.license_tag.value,
        )
        fetched = port.fetch(fetch_req)
        if is_refusal(fetched):
            return fetched
        window_meta: dict[str, object] = {
            "venue": request.venue,
            "symbol": symbol,
            "start_ns": request.start_ns,
            "end_ns": request.end_ns,
            "resolution": request.resolution,
            "side": request.side.value,
            "revision": request.revision,
            "license_tag": request.license_tag.value,
            "source": port.source,
            "provenance": {
                "acquisition": "download-once",
                "component": "COMP-QMB",
                "provider": port.source,
            },
        }
        inner = getattr(port, "inner", None)
        last_window = getattr(inner, "last_window", None) if inner is not None else None
        if last_window is not None:
            window_meta["license_tag"] = last_window.license_tag.value
            window_meta["provenance"] = dict(last_window.provenance)
            window_meta["partition_key"] = last_window.partition.partition_key
        stored_side = (
            DownloadSide.ASK.value if request.side is DownloadSide.ASK else DownloadSide.BID.value
        )
        market_data = MarketDataContext.try_create(
            venue=request.venue,
            symbol=symbol,
            resolution=request.resolution,
            side=stored_side,
            license_tag=window_meta["license_tag"],
            provenance=window_meta["provenance"],
        )
        if is_refusal(market_data):
            return market_data
        covered_event_ns: list[int] = []
        batch_keys: dict[IntakeKey, ProviderRecord] = {}
        for record in fetched.value:
            record_sequence = sequence
            sequence += 1
            key = IntakeKey.try_create(record.source, record.source_native_id, record.revision)
            if is_refusal(key):
                return key
            batch_prior = batch_keys.get(key.value)
            if batch_prior is not None and batch_prior == record:
                idempotent += 1
                continue
            ingest = ExternalSourceIngest(_IngestBridge(port))
            receipt = ingest.intake(
                record,
                writer=active_writer,
                sequence=record_sequence,
                world=request.world,
                receive_wall_time=receive,
            )
            if is_refusal(receipt):
                return receipt
            if receipt.value.outcome is IntakeOutcome.PRODUCED:
                observation = _observation_for_archive(
                    receipt.value,
                    request.side,
                    market_data.value,
                )
                if is_refusal(observation):
                    return observation
                reserved = authority.value.reserve(
                    key.value,
                    observation.value,
                    instant=journal_instant.value,
                )
                if is_refusal(reserved):
                    return reserved
                canonical_observation = reserved.value.observation
                if reserved.value.complete:
                    idempotent += 1
                    batch_keys[key.value] = record
                    continue
                stored = ingest.submit(canonical_observation, gate)
                if is_refusal(stored):
                    return stored
                admitted += 1
                covered_event_ns.append(canonical_observation.event_time.value_ns)
                appended = authority.value.complete(
                    key.value,
                    canonical_observation,
                    instant=journal_instant.value,
                )
                if is_refusal(appended):
                    return appended
                produced += 1
                batch_keys[key.value] = record
            else:
                idempotent += 1

        # The envelope is only a rebuildable cache.  Stamp it from observations
        # actually admitted, never from the requested window or requested sides.
        if covered_event_ns:
            persisted = persist_coverage_windows(
                evidence,
                world=request.world,
                venue=str(window_meta["venue"]),
                symbol=symbol,
                resolution=str(window_meta["resolution"]),
                side=stored_side,
                start_ns=min(covered_event_ns),
                end_ns=max(covered_event_ns) + 1,
                observation_count=len(covered_event_ns),
                license_tag=str(window_meta["license_tag"]),
                revision=str(window_meta["revision"]),
                source=str(window_meta["source"]),
                provenance=cast("Mapping[str, object]", window_meta["provenance"]),
            )
            if is_refusal(persisted):
                return persisted
        windows.append(window_meta)

        percent = int(((index + 1) * 100) // total) if total else 100
        # ETA is derived from the declared window, never a wall-clock read below
        # the composition root (DEC-0106). The half-open window [start, end) is
        # apportioned evenly across the batches; the ETA is the remaining batches
        # scaled by that per-batch span (ns). It is a data-derived remaining span
        # in ns that falls to zero as the last batch completes — monotone with the
        # completed-batch count, deterministic and clock-free.
        remaining_batches = total - (index + 1)
        per_batch_span_ns = (request.end_ns - request.start_ns) // total if total else 0
        eta_ns = remaining_batches * per_batch_span_ns
        sample = DownloadProgress(
            percent=percent,
            date_reached_ns=request.end_ns,
            eta_ns=eta_ns,
            symbol=symbol,
            produced=produced,
            total_batches=total,
            completed_batches=index + 1,
        )
        samples.append(sample)
        if sink is not None:
            sink.on_progress(sample)

    return Ok(
        DownloadReceipt(
            command="download",
            venue=request.venue,
            symbols=request.symbols,
            start_ns=request.start_ns,
            end_ns=request.end_ns,
            resolution=request.resolution,
            side=request.side.value,
            destination=request.destination,
            revision=request.revision,
            license_tag=request.license_tag.value,
            produced=produced,
            idempotent=idempotent,
            admitted=admitted,
            overwrite=request.overwrite,
            source=port.source,
            progress=tuple(samples),
            windows=tuple(windows),
        )
    )


def _observation_for_archive(
    receipt: IntakeReceipt,
    side: DownloadSide,
    market_data: MarketDataContext,
) -> Result[SourceObservation]:
    """Attach exact quote money and self-describing context to the CT-10 value."""
    observation = receipt.observation
    if observation.foreign_money is None and receipt.quote is not None:
        money = receipt.quote.ask if side is DownloadSide.ASK else receipt.quote.bid
        priced = receipt.observation_with_foreign_money(money)
        if is_refusal(priced):
            return priced
        observation = priced.value
    return SourceObservation.try_create(
        event_time=observation.event_time,
        known_at=observation.known_at,
        source=observation.source,
        source_native_id=observation.source_native_id,
        revision=observation.revision,
        receive_wall_time=observation.receive_wall_time,
        writer=observation.writer,
        sequence=observation.sequence,
        world=observation.world,
        foreign_timestamp=observation.foreign_timestamp,
        foreign_money=observation.foreign_money,
        market_data=market_data,
        receive_monotonic_diagnostic=observation.receive_monotonic_diagnostic,
        correction_of=observation.correction_of,
    )


class _IngestBridge:
    """Adapt :class:`ProviderAdapter` to CT-15 :class:`ExternalSourcePort`."""

    def __init__(self, port: ProviderAdapter) -> None:
        self._port = port

    def fetch(self, request: SourceRequest, /) -> Result[tuple[ProviderRecord, ...]]:
        bounds = dict(request.bounds)
        symbol = clean_token(bounds.get("symbol"))
        if symbol is None:
            return invalid("symbol", "ingest bridge requires bounds.symbol")
        start = bounds.get("start_ns")
        end = bounds.get("end_ns")
        if not isinstance(start, int) or isinstance(start, bool):
            return invalid("start_ns", "ingest bridge requires int start_ns")
        if not isinstance(end, int) or isinstance(end, bool):
            return invalid("end_ns", "ingest bridge requires int end_ns")
        side = _as_side(bounds.get("side", DownloadSide.BOTH.value))
        if is_refusal(side):
            return side
        return self._port.fetch(
            ProviderFetchRequest(
                source=request.source,
                symbol=symbol,
                start_ns=start,
                end_ns=end,
                resolution=clean_token(bounds.get("resolution")) or "tick",
                side=side.value,
                revision=clean_token(bounds.get("revision")) or "r1",
                license_tag=clean_token(bounds.get("license_tag")) or PERSONAL_USE_LICENSE,
                bounds=bounds,
            )
        )


def _as_symbols(value: object) -> Result[tuple[str, ...]]:
    if isinstance(value, str):
        parts = tuple(token for token in (part.strip() for part in value.split(",")) if token)
        if not parts:
            return invalid("symbol", "download names at least one non-empty symbol")
        return Ok(parts)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        items = cast("Sequence[object]", value)
        symbols: list[str] = []
        for item in items:
            token = clean_token(item)
            if token is None:
                return invalid("symbol", "each symbol is a non-empty token", given=repr(item))
            symbols.append(token)
        if not symbols:
            return invalid("symbol", "download names at least one non-empty symbol")
        return Ok(tuple(symbols))
    return invalid(
        "symbol",
        "symbol is a non-empty token or a list of tokens",
        given=repr(value),
    )


def _as_ns(value: object, *, field: str) -> Result[int]:
    if isinstance(value, bool):
        return invalid(field, f"{field} is int64 UTC-ns, never a bool", given=repr(value))
    if isinstance(value, int):
        return Ok(value)
    if isinstance(value, str) and value.strip() != "":
        token = value.strip()
        if token.isdigit() or (token.startswith("-") and token[1:].isdigit()):
            return Ok(int(token))
        try:
            if token.endswith("Z"):
                token = token[:-1] + "+00:00"
            parsed = datetime.fromisoformat(token)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return Ok(int(parsed.timestamp() * 1_000_000_000))
        except ValueError:
            return invalid(
                field,
                f"{field} is int64 UTC-ns or an ISO-8601 timestamp",
                given=repr(value),
            )
    return invalid(field, f"{field} is required: int64 UTC-ns or ISO-8601", given=repr(value))


def _as_side(value: object) -> Result[DownloadSide]:
    if isinstance(value, DownloadSide):
        return Ok(value)
    token = clean_token(value)
    if token is None:
        return invalid(
            "side",
            "side is one of bid, ask, both",
            given=repr(value),
            legal=list(DOWNLOAD_SIDES),
        )
    try:
        return Ok(DownloadSide(token))
    except ValueError:
        return invalid(
            "side",
            "side is one of bid, ask, both",
            given=token,
            legal=list(DOWNLOAD_SIDES),
        )


def _as_world(value: object) -> Result[World]:
    if isinstance(value, World):
        return Ok(value)
    token = clean_token(value)
    if token is None:
        return invalid("world", "world is live, replay, or simulated", given=repr(value))
    try:
        return Ok(World(token))
    except ValueError:
        return invalid("world", "world is live, replay, or simulated", given=token)
