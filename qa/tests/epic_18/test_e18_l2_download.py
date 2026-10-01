"""Epic 18 · L2 — ``data download`` download-once acquisition (Story 18.1).

T18-1a  thin front: CT-10 evidence lands through the qmf-data boundary   (RQ1)
        + FINDING: a qmb-authored durable ledger is a second data layer   (RQ1/B-11)
T18-1b  request assembled from (venue, symbol[list], start, end, side)    (RQ2)
T18-1d  fetch flows through the QMX-authored provider-adapter port        (RQ3)
T18-1f  bid + ask preserved as distinct scaled-int streams                (RQ5) — EXPECTED FAIL
T18-1i  idempotent re-download writes no duplicate observation            (RQ8)
T18-1j  --overwrite appends a NEW CT-10 revision, retains the original    (RQ9)
T18-1k  a long import emits machine-observable progress to an injected sink (RQ10)
T18-1l  read commands reach only rooms — no provider port                 (RQ12)
T18-1m  each window records provenance + a licence tag (gate input)       (RQ11)
"""

from __future__ import annotations

import ast
import inspect
import os
import tempfile
from pathlib import Path

import qmf.data.store.engines.jsonl as jsonl_engine
from _e18 import (
    NS,
    FakeAdapter,
    RecordingProgressSink,
    download_resources,
    ok,
    provider_record,
    raw_observation_fingerprints,
    scan_raw_observations,
    store_at,
)
from qmb.data.catalog import list_data
from qmb.data.download import download, parse_download_request
from qmb.data.gap_check import gap_check
from qmb.data.ports import PROVIDER_ADAPTER_METHODS, ProviderAdapter
from qmb.data.verify import verify
from qmf.core.chrono import Instant, WriterId
from qmf.core.fingerprint import World
from qmf.core.refusal import Ok, is_ok, is_refusal
from qmf.data.ingest import IntakeKey
from qmf.data.intake_authority import IntakeAuthority
from qmf.data.store import EvidenceStore
from qmf.data.journal import JournalEventType
from qmf.data.journal_producer import JournalReader
from qmf.data.observation import SourceObservation
from qmf.data.source_boundary import SourceObservationBoundary

_DATA = Path(__file__).resolve().parents[3] / "qmb" / "src" / "qmb" / "data"


def _download_ok(dest: Path, records=None, **over):
    recs = records if records is not None else (provider_record(f"EURUSD#{NS}", NS),)
    adapter = FakeAdapter(tuple(recs))
    res = download(download_resources(dest, **over), adapter=adapter, store=store_at(dest))
    return res, adapter


class _FirstSymbolAdapter:
    """Return the scripted batch once, then empty batches for progress-only symbols."""

    source = "dukascopy"
    batch_count = 1
    rate_limit_per_second = None

    def __init__(self, records):
        self._records = tuple(records)

    def fetch(self, request, /):
        from qmf.core.refusal import Ok

        return Ok(self._records if request.symbol == "EURUSD" else ())

    def earliest_available(self, symbol, /):
        from qmf.core.refusal import Ok

        return Ok(None)

    def list_symbols(self):
        from qmf.core.refusal import Ok

        return Ok(("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF"))


# --- T18-1a  persistence routes through the CT-10 boundary (RQ1) --------------
def test_t18_1a_ct10_evidence_lands_through_qmf_data_boundary() -> None:
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        res, _ = _download_ok(dest)
        assert is_ok(res), res
        # Observed independently: the raw archive under the world namespace holds
        # the observation, i.e. the write went through the qmf-data store.
        rows = scan_raw_observations(store_at(dest))
        assert len(rows) == 1
        assert (dest / "replay" / "immutable-raw-archive").is_dir()


def test_t18_1a_ct15_authority_is_qmf_checked_ct13_evidence() -> None:
    """QMF records the full CT-10 identity behind the key in the per-world journal."""
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        res, _ = _download_ok(dest)
        assert is_ok(res), res
        evidence = store_at(dest)
        world_store = evidence.for_world("replay")
        assert is_ok(world_store), world_store
        events = JournalReader(world_store.value.journal).read_checked(
            "ct15-intake-authority", for_world="replay", expected_start=0
        )
        assert is_ok(events), events
        authority = [
            event
            for event in events.value
            if event.event_type is JournalEventType.DATA_QUALITY
            and event.payload.get("class") == "qmf-ct15-intake-key"
        ]
        rows = scan_raw_observations(evidence)
        assert len(authority) == 2 and len(rows) == 1
        intent = next(event for event in authority if event.payload.get("action") == "intent")
        complete = next(event for event in authority if event.payload.get("action") == "complete")
        assert intent.payload["observation_fingerprint"] == rows[0]["fingerprint"]
        assert intent.payload["source_native_id"] == rows[0]["source_native_id"]
        assert complete.payload["complete"] is True
        assert complete.payload["observation_fingerprint"] == rows[0]["fingerprint"]


def _authority_observation(*, receive_wall_time: int = NS + 1) -> SourceObservation:
    writer = ok(WriterId.try_create("qmb", "data", "download", "boot-ct15"))
    return ok(
        SourceObservation.try_create(
            event_time=Instant(value_ns=NS),
            known_at=Instant(value_ns=NS),
            source="fixture-provider",
            source_native_id="stable-intake-key",
            revision="r1",
            receive_wall_time=Instant(value_ns=receive_wall_time),
            writer=writer,
            sequence=0,
            world=World.REPLAY,
        )
    )


def test_t18_1a_stale_resume_handles_share_canonical_reservation_state() -> None:
    """Same-store handles serialize and refresh one key despite receive metadata changes."""
    with tempfile.TemporaryDirectory() as d:
        evidence = store_at(Path(d) / "rooms")
        world_store = ok(evidence.for_world(World.REPLAY))
        writer = ok(WriterId.try_create("qmb", "data", "download", "boot-ct15"))
        first = ok(IntakeAuthority.resume(world_store.journal, writer))
        stale_handle = ok(IntakeAuthority.resume(world_store.journal, writer))
        key = ok(IntakeKey.try_create("fixture-provider", "stable-intake-key", "r1"))
        original = _authority_observation(receive_wall_time=NS + 1)
        changed_receipt = _authority_observation(receive_wall_time=NS + 999)
        reserved = ok(first.reserve(key, original, instant=Instant(value_ns=NS + 2)))
        reused = ok(stale_handle.reserve(key, changed_receipt, instant=Instant(value_ns=NS + 3)))
        assert reserved.observation.fingerprint == original.fingerprint
        assert reused.observation.fingerprint == original.fingerprint
        assert reused.observation.receive_wall_time == original.receive_wall_time
        events = ok(
            JournalReader(world_store.journal).read_checked(
                "ct15-intake-authority", for_world=World.REPLAY, expected_start=0
            )
        )
        intents = [
            event
            for event in events
            if event.payload.get("class") == "qmf-ct15-intake-key"
            and event.payload.get("action") == "intent"
        ]
        assert len(intents) == 1


def test_t18_1a_ct15_authority_rejects_partitioned_stream_names() -> None:
    with tempfile.TemporaryDirectory() as d:
        evidence = store_at(Path(d) / "rooms")
        world_store = ok(evidence.for_world(World.REPLAY))
        writer = ok(WriterId.try_create("qmb", "data", "download", "boot-ct15"))
        for stream_name in ("one", "two"):
            result = IntakeAuthority.resume(world_store.journal, writer, stream_name=stream_name)
            assert is_refusal(result)
            assert result.category.value == "policy rejection"


def test_t18_1a_ct15_visible_uncertain_intent_needs_durable_recovery_barrier(
    monkeypatch,
) -> None:
    """Visible CT-13 bytes cannot authorize reuse until a later fsync succeeds."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "rooms"
        evidence = EvidenceStore(root, rotation_bytes=1)
        world_store = ok(evidence.for_world(World.REPLAY))
        writer = ok(WriterId.try_create("qmb", "data", "download", "boot-ct15"))
        authority = ok(IntakeAuthority.resume(world_store.journal, writer))
        key = ok(IntakeKey.try_create("fixture-provider", "stable-intake-key", "r1"))
        original = _authority_observation()
        original_fsync = jsonl_engine.os.fsync
        failed_intent_sync = False

        def fail_intent_fsync(fd: int) -> None:
            nonlocal failed_intent_sync
            target = Path(os.readlink(f"/proc/self/fd/{fd}"))
            if target.name == "000002.jsonl" and not failed_intent_sync:
                failed_intent_sync = True
                raise OSError("injected CT-13 fsync failure")
            original_fsync(fd)

        monkeypatch.setattr(jsonl_engine.os, "fsync", fail_intent_fsync)
        refused_intent = authority.reserve(key, original, instant=Instant(value_ns=NS + 2))
        assert is_refusal(refused_intent)
        assert failed_intent_sync is True
        visible = ok(
            JournalReader(world_store.journal).read_checked(
                "ct15-intake-authority", for_world=World.REPLAY, expected_start=0
            )
        )
        assert any(event.payload.get("action") == "intent" for event in visible)
        world_store.journal.close()

        def fail_all_fsync(_fd: int) -> None:
            raise OSError("injected persistent CT-13 fsync failure")

        monkeypatch.setattr(jsonl_engine.os, "fsync", fail_all_fsync)
        reopening = store_at(root)
        reopening_world = ok(reopening.for_world(World.REPLAY))
        failed_recovery = IntakeAuthority.resume(reopening_world.journal, writer)
        assert is_refusal(failed_recovery)
        reopening_world.journal.close()

        monkeypatch.setattr(jsonl_engine.os, "fsync", original_fsync)
        synced_chunks: list[str] = []

        def record_sync(fd: int) -> None:
            synced_chunks.append(Path(os.readlink(f"/proc/self/fd/{fd}")).name)
            original_fsync(fd)

        monkeypatch.setattr(jsonl_engine.os, "fsync", record_sync)
        recovered_store = store_at(root)
        recovered_world = ok(recovered_store.for_world(World.REPLAY))
        recovered = ok(IntakeAuthority.resume(recovered_world.journal, writer))
        assert "000002.jsonl" in synced_chunks
        reservation = ok(recovered.reserve(key, original, instant=Instant(value_ns=NS + 3)))
        assert reservation.observation.fingerprint == original.fingerprint
        assert reservation.complete is False


def test_t18_1a_download_does_not_complete_on_unknown_ct10_ack(monkeypatch) -> None:
    """Ok(None) from CT-10 is not proof that the raw row was retained."""
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        evidence = store_at(dest)
        world_store = ok(evidence.for_world(World.REPLAY))
        boundary = SourceObservationBoundary(evidence)
        monkeypatch.setattr(boundary, "admit", lambda _observation: Ok(None))
        result = download(
            download_resources(dest),
            adapter=FakeAdapter((provider_record("EURUSD#ack", NS),)),
            store=evidence,
            boundary=boundary,
        )
        assert is_refusal(result)
        assert scan_raw_observations(evidence) == ()
        events = ok(
            JournalReader(world_store.journal).read_checked(
                "ct15-intake-authority", for_world=World.REPLAY, expected_start=0
            )
        )
        actions = [
            event.payload.get("action")
            for event in events
            if event.payload.get("class") == "qmf-ct15-intake-key"
        ]
        assert actions == ["intent"]


# --- T18-1b  request assembly + explicit reproducible end (RQ2) ---------------
def test_t18_1b_request_assembled_from_fields() -> None:
    parsed = parse_download_request(
        {
            "venue": "dukascopy",
            "symbol": "EURUSD, GBPUSD",
            "start_ns": NS,
            "end_ns": NS + 500,
            "resolution": "tick",
            "side": "both",
            "destination": "rooms",
        }
    )
    assert is_ok(parsed), parsed
    req = parsed.value
    assert req.venue == "dukascopy"
    assert req.symbols == ("EURUSD", "GBPUSD")
    assert req.start_ns == NS
    assert req.end_ns == NS + 500  # explicit end honoured verbatim → reproducible
    assert req.side.value == "both"


def test_t18_1b_symbol_list_form_accepted() -> None:
    parsed = parse_download_request(
        {
            "venue": "dukascopy",
            "symbol": ["EURUSD", "GBPUSD", "USDJPY"],
            "start_ns": NS,
            "end_ns": NS + 1,
            "destination": "rooms",
        }
    )
    assert is_ok(parsed), parsed
    assert parsed.value.symbols == ("EURUSD", "GBPUSD", "USDJPY")


# --- T18-1d  fetch flows through the QMX-authored port (RQ3) -------------------
def test_t18_1d_port_surface_and_fetch_is_called() -> None:
    assert PROVIDER_ADAPTER_METHODS == (
        "fetch",
        "earliest_available",
        "list_symbols",
        "batch_count",
        "rate_limit_per_second",
    )
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        res, adapter = _download_ok(dest)
        assert is_ok(res), res
        # The provider fetch actually flowed through the injected port.
        assert len(adapter.fetch_calls) == 1
        req = adapter.fetch_calls[0]
        assert req.symbol == "EURUSD" and req.side.value == "both"


def test_t18_1d_dukascopy_adapter_one_is_a_provider_adapter() -> None:
    from qmb.data.dukascopy import DukascopyProviderAdapter
    from qmf.core import VenueId
    from qmf.core.identity import Instrument

    class _NullTransport:
        def fetch_hour(self, key, /):
            from qmf.core.refusal import Ok

            return Ok(b"")

    v = ok(VenueId.try_create("dukascopy"))
    adapter = DukascopyProviderAdapter(
        _NullTransport(), instruments={"EURUSD": ok(Instrument.try_create(v, "EURUSD"))}
    )
    assert isinstance(adapter, ProviderAdapter)
    assert adapter.source == "dukascopy"
    # The port surface is real, not just a declared constant: every named method /
    # property is present on the QMX adapter #1.
    for name in PROVIDER_ADAPTER_METHODS:
        assert hasattr(adapter, name), f"Dukascopy adapter missing port member {name}"
    assert callable(adapter.fetch) and callable(adapter.list_symbols)
    assert callable(adapter.earliest_available)
    assert isinstance(adapter.batch_count, int)


# --- T18-1f  bid + ask preserved as distinct streams (RQ5, AR-46) -------------
def test_t18_1f_bid_and_ask_preserved_in_ct10_evidence_FINDING() -> None:
    """AR-46 / 18.1 AC3: bid and ask land as distinct scaled-integer streams,
    written as CT-10 observations and retained forever.

    EXPECTED FAIL — the CT-15 intake builds a TickQuote from bid/ask, but
    ``download`` submits only the bare ``SourceObservation`` (``foreign_money``
    absent) and DISCARDS the quote. No bid/ask price is ever persisted to the raw
    archive, so a governed reader recovers timestamps with no prices.
    """
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        rec = provider_record("EURUSD#1", NS, bid=110_000, ask=110_020)
        res = download(download_resources(dest), adapter=FakeAdapter((rec,)), store=store_at(dest))
        assert is_ok(res), res
        rows = scan_raw_observations(store_at(dest))
        assert rows, "no observation persisted at all"
        recovered = {"foreign_money" in row or "bid" in row or "ask" in row for row in rows}
        assert recovered == {True}, (
            "persisted CT-10 evidence carries neither bid/ask nor foreign_money — the "
            "download-once tick prices are dropped (RQ5/RQ6/RQ7); persisted keys were "
            f"{sorted(rows[0].keys())}"
        )


# --- T18-1i  idempotent re-download (RQ8) -------------------------------------
def test_t18_1i_rerun_writes_no_duplicate() -> None:
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        recs = tuple(provider_record(f"EURUSD#{NS + i}", NS + i) for i in range(3))
        r1 = download(download_resources(dest), adapter=FakeAdapter(recs), store=store_at(dest))
        assert is_ok(r1), r1
        fps1 = raw_observation_fingerprints(store_at(dest))
        r2 = download(download_resources(dest), adapter=FakeAdapter(recs), store=store_at(dest))
        assert is_ok(r2), r2
        fps2 = raw_observation_fingerprints(store_at(dest))
        assert fps1 == fps2 and len(fps1) == 3


def test_t18_1i_restart_rejects_changed_fact_for_same_key() -> None:
    """Reopened QMF rooms refuse a source key whose canonical CT-10 fact changed."""
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        original = provider_record("EURUSD#same", NS, bid=110_000, ask=110_020)
        first = download(
            download_resources(dest), adapter=FakeAdapter((original,)), store=store_at(dest)
        )
        assert is_ok(first), first
        changed = provider_record("EURUSD#same", NS, bid=110_001, ask=110_021)
        second = download(
            download_resources(dest), adapter=FakeAdapter((changed,)), store=store_at(dest)
        )
        assert is_refusal(second), second
        refused = second
        assert refused.category.value == "policy rejection"
        assert "different provider facts" in str(refused.context)
        assert len(raw_observation_fingerprints(store_at(dest))) == 1


def test_t18_1i_same_facts_reuse_canonical_row_across_boot_metadata() -> None:
    """Receive time and writer boot metadata do not mint another CT-10 row."""
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        record = provider_record("EURUSD#stable", NS)
        first = download(
            download_resources(dest, receive_wall_time=NS + 21),
            adapter=FakeAdapter((record,)),
            store=store_at(dest),
        )
        assert is_ok(first), first
        later_writer = ok(WriterId.try_create("qmb", "data", "download", "boot-2"))
        second = download(
            download_resources(dest, receive_wall_time=NS + 99, writer=later_writer),
            adapter=FakeAdapter((record,)),
            store=store_at(dest),
        )
        assert is_ok(second), second
        assert second.value.idempotent == 1
        assert len(raw_observation_fingerprints(store_at(dest))) == 1


def test_t18_1i_uncertain_ct10_ack_recovers_through_qmf_authority(monkeypatch) -> None:
    """A raw append whose acknowledgement is lost is retried idempotently after reopen."""
    from qmf.core import RefusalCategory, Retryability, TypedRefusal
    from qmf.data.source_boundary import SourceObservationBoundary

    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        evidence = store_at(dest)
        boundary = SourceObservationBoundary(evidence)
        actual_admit = boundary.admit
        fail_once = True

        def admit_then_lose_ack(observation):
            nonlocal fail_once
            result = actual_admit(observation)
            if fail_once and is_ok(result):
                fail_once = False
                return TypedRefusal(
                    category=RefusalCategory.STORAGE_FAILURE,
                    retryability=Retryability.YES,
                    context={"field": "ct10", "reason": "simulated lost acknowledgement"},
                )
            return result

        monkeypatch.setattr(boundary, "admit", admit_then_lose_ack)
        record = provider_record("EURUSD#uncertain", NS)
        first = download(
            download_resources(dest),
            adapter=FakeAdapter((record,)),
            store=evidence,
            boundary=boundary,
        )
        assert is_refusal(first)
        assert len(raw_observation_fingerprints(evidence)) == 1

        reopened = store_at(dest)
        retry_writer = ok(WriterId.try_create("qmb", "data", "download", "boot-2"))
        second = download(
            download_resources(dest, receive_wall_time=NS + 99, writer=retry_writer),
            adapter=FakeAdapter((record,)),
            store=reopened,
        )
        assert is_ok(second), second
        assert len(raw_observation_fingerprints(reopened)) == 1
        world_store = ok(reopened.for_world("replay"))
        events = ok(
            JournalReader(world_store.journal).read_checked(
                "ct15-intake-authority", for_world="replay", expected_start=0
            )
        )
        assert (
            sum(
                event.event_type is JournalEventType.DATA_QUALITY
                and event.payload.get("class") == "qmf-ct15-intake-key"
                for event in events
            )
            == 2
        )
        assert {event.payload.get("action") for event in events} >= {"intent", "complete"}


# --- T18-1j  --overwrite appends a new revision, retains the original (RQ9) ----
def test_t18_1j_overwrite_appends_new_revision() -> None:
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        r1 = download(
            download_resources(dest, revision="r1"),
            adapter=FakeAdapter((provider_record("EURUSD#1", NS, revision="r1"),)),
            store=store_at(dest),
        )
        assert is_ok(r1), r1
        fps1 = raw_observation_fingerprints(store_at(dest))
        r2 = download(
            download_resources(dest, overwrite=True, revision="r2"),
            adapter=FakeAdapter((provider_record("EURUSD#1", NS, revision="r2"),)),
            store=store_at(dest),
        )
        assert is_ok(r2), r2
        fps2 = raw_observation_fingerprints(store_at(dest))
        # A new revision is a distinct artifact; the original is retained (append,
        # never overwrite the only copy).
        assert fps1 <= fps2 and len(fps2) == 2, (fps1, fps2)


# --- T18-1k  machine-observable progress to an injected sink (RQ10) -----------
def test_t18_1k_progress_emitted_to_injected_sink() -> None:
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        sink = RecordingProgressSink()
        res = download(
            download_resources(dest, symbol="EURUSD, GBPUSD"),
            adapter=_FirstSymbolAdapter((provider_record("EURUSD#1", NS),)),
            store=store_at(dest),
            progress=sink,
        )
        assert is_ok(res), res
        assert sink.samples, "no progress emitted to the injected sink"
        last = sink.samples[-1]
        assert last.percent == 100
        assert isinstance(last.date_reached_ns, int)
        assert last.completed_batches == last.total_batches


# --- FC-29 / T18-1k'  every sample reports percent, date-reached AND ETA (RQ10, AC5) ---
def test_t18_1k_progress_samples_carry_monotonic_eta() -> None:
    """18.1 AC5 / RQ10: a progress sample reports percent, date-reached AND an ETA
    — a non-None ``eta_ns`` on EVERY sample, not just the terminal one — and the
    ETA falls as batches advance.

    A multi-symbol download emits one sample per symbol (one batch each) over a
    window wide enough that the per-batch ETA span is non-zero. Every symbol
    advances the completed-batch count by exactly one, so no two samples share a
    completed count: the stream is STRICTLY decreasing and equality is never
    expected here.
    """
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        sink = RecordingProgressSink()
        symbols = "EURUSD, GBPUSD, USDJPY, AUDUSD, USDCHF"
        res = download(
            download_resources(dest, symbol=symbols, start_ns=NS, end_ns=NS + 1_000),
            adapter=_FirstSymbolAdapter((provider_record("EURUSD#1", NS),)),
            store=store_at(dest),
            progress=sink,
        )
        assert is_ok(res), res
        assert len(sink.samples) == 5, sink.samples
        # AC5: an ETA is present on EVERY emitted sample, never hard-coded None.
        missing = [s for s in sink.samples if s.eta_ns is None]
        assert not missing, (
            "a progress sample carried eta_ns=None; AC5 requires percent, "
            f"date-reached AND ETA on every sample: {[s.eta_ns for s in sink.samples]}"
        )
        etas = [int(s.eta_ns) for s in sink.samples]
        # Batches strictly advance one-per-sample, so the ETA strictly decreases.
        assert all(earlier > later for earlier, later in zip(etas, etas[1:])), (
            f"ETA is not strictly decreasing across the sample stream: {etas}"
        )
        # No batches remain at completion, so the final ETA is exactly zero.
        assert etas[-1] == 0, etas


# --- T18-1l  read commands reach only rooms, no provider port (RQ12) -----------
def test_t18_1l_read_commands_hold_no_provider_port() -> None:
    # The read entrypoints take no provider adapter in their signature.
    for fn in (list_data, verify, gap_check):
        params = set(inspect.signature(fn).parameters)
        assert "adapter" not in params, f"{fn.__name__} exposes a provider adapter seam"
    # And no read module imports the ProviderAdapter port at all.
    offenders: list[str] = []
    for name in ("catalog.py", "verify.py", "gap_check.py"):
        tree = ast.parse((_DATA / name).read_text(encoding="utf-8"), filename=name)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "qmb.data.ports":
                imported = {a.name for a in node.names}
                if "ProviderAdapter" in imported:
                    offenders.append(f"{name}: imports ProviderAdapter")
    assert offenders == [], offenders


# --- T18-1m  provenance + licence tag recorded per window (RQ11) --------------
def test_t18_1m_window_records_provenance_and_license_tag() -> None:
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "rooms"
        res = download(
            download_resources(dest, license_tag="internal-only"),
            adapter=FakeAdapter((provider_record("EURUSD#1", NS),)),
            store=store_at(dest),
        )
        assert is_ok(res), res
        listed = list_data({"destination": str(dest), "world": "replay"})
        assert is_ok(listed), listed
        entries = listed.value.entries
        assert entries, "no catalog coverage recorded for the ingested window"
        for entry in entries:
            assert entry.license_tag == "internal-only", entry.as_mapping()
            assert entry.provenance is not None and dict(entry.provenance), entry.as_mapping()

        # R-011: the usage right rides the evidence-bearing CT-10 observation,
        # rather than existing only on a QMB-authored coverage envelope.
        observations = scan_raw_observations(store_at(dest))
        assert len(observations) == 1
        market_data = observations[0].get("market_data")
        assert isinstance(market_data, dict)
        assert market_data["license_tag"] == "internal-only"
        assert market_data["side"] == "bid"
        assert isinstance(market_data["provenance"], dict)
