"""QMF-backed live intake receipts retain both CT-10 and raw-body lineage."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

from qmf.core import (
    Account,
    AccountRole,
    DataDrivenClock,
    Instant,
    Instrument,
    Ok,
    Result,
    SinkAck,
    VenueId,
    World,
    WriterId,
    is_ok,
    is_refusal,
)
from qmf.data import JournalAppendReceipt, JournalEventType, JournalReader, JournalWriter
from qmf.data.observation import SourceObservation
from qmf.data.source_boundary import ObservationReceipt, SourceObservationBoundary
from qmf.data.store import EvidenceStore, StoreReceipt
from qmf.data.store.rooms import RoomRole
from qmf.venue.capabilities import ErrorMap
from qmf.venue.ctrader import RoundingMode
from qmn.data.intake import GovernedLiveIntake, LiveIntakeReceipt
from qmn.data.observation_sink import QmfLiveJournalSink, QmfLiveObservationSink
from qmn.ledger.protection_state import resolve_checked_native_protection_readback
from qmn.loop.accumulator import RecordingAccumulator, clear_first_writer_registry
from qmn.venue.live import LiveCTraderClient, WireKind

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _clock() -> DataDrivenClock:
    walls = tuple(
        _ok(Instant.try_create(1_724_000_000_000_000_000 + i * 1_000_000)) for i in range(8)
    )
    return DataDrivenClock(
        boot_epoch_id="protection-fixture-boot",
        wall_instants=walls,
        monotonic_ns=tuple(8_000_000_000 + i * 1_000_000 for i in range(8)),
    )


def test_live_client_intake_receipt_reopens_raw_ct10_and_ct13_links(tmp_path: Path) -> None:
    clear_first_writer_registry()
    venue = _ok(VenueId.try_create("venue-protection-fixture"))
    account = _ok(Account.try_create("42", venue, AccountRole.DEMO))
    writer_id = _ok(WriterId.try_create("fixture-node", "venue-adapter", "live-42", "boot-a"))
    store = EvidenceStore(tmp_path / "evidence")
    world_store = _ok(store.for_world(World.LIVE))
    writer = _ok(JournalWriter.resume(world_store.journal, writer_id, stream_name="live-42"))
    observation_sink = QmfLiveObservationSink(store=store, writer=writer)
    journal_sink = QmfLiveJournalSink(
        writer=writer,
        journal_store=world_store.journal,
        evidence_store=store,
    )
    accumulator = _ok(
        RecordingAccumulator.try_create(
            venue_id=venue,
            account=account,
            writer_id=writer_id,
            observation_sink=observation_sink,
            journal_sink=journal_sink,
            accumulator_bound=8,
        )
    )
    intake = _ok(GovernedLiveIntake.try_create(accumulator=accumulator))
    clock = _clock()
    client = _ok(
        LiveCTraderClient.try_create(
            World.LIVE,
            venue,
            clock=clock,
            error_map=_ok(ErrorMap.try_create(1, [])),
            session_epoch="session-protection-fixture",
            intake=intake,
        )
    )
    _ok(client.open_session(account))
    raw_position = {
        "positionId": 44,
        "tradeData": {"symbolId": 7},
        "stopLoss": 1.08523,
    }
    received = dict(
        _ok(
            client.receive(
                WireKind.POSITION_READBACK,
                raw_position,
                native_id="position-44",
                response_account_id=42,
                response_session_epoch="session-protection-fixture",
            )
        )
    )
    intake_receipt = received.get("intake_receipt")
    assert isinstance(intake_receipt, LiveIntakeReceipt)
    assert type(intake_receipt.observation_ack) is SinkAck
    assert type(intake_receipt.journal_ack) is SinkAck
    raw_receipt = cast(StoreReceipt, intake_receipt.observation_ack.detail["raw_store_receipt"])
    source_receipt = cast(
        ObservationReceipt, intake_receipt.observation_ack.detail["source_receipt"]
    )
    journal_receipt = cast(
        JournalAppendReceipt, intake_receipt.journal_ack.detail["journal_append_receipt"]
    )
    assert raw_receipt.room_role is RoomRole.IMMUTABLE_RAW_ARCHIVE
    assert source_receipt.archive.room_role is RoomRole.IMMUTABLE_RAW_ARCHIVE
    assert journal_receipt.event.payload["_qmn_source_join"] == {
        "class": "qmn-live-observation-source-join",
        "format_version": 1,
        "raw_archive_fp1": raw_receipt.fingerprint.value,
        "raw_encoding": "qmn-verbatim-response-json-v1",
        "source_observation_fp1": source_receipt.observation_fingerprint.value,
        "source_archive_fp1": source_receipt.archive.fingerprint.value,
        "source": intake_receipt.identity.source,
        "source_native_id": intake_receipt.identity.source_native_id,
        "revision": intake_receipt.identity.revision,
        "event_time_ns": intake_receipt.identity.event_time_ns,
        "known_at_ns": intake_receipt.identity.known_at_ns,
        "venue_id": venue.value,
        "trader_account_id": 42,
        "session_epoch": "session-protection-fixture",
        "wire_kind": "position-readback",
        "writer": {
            "machine": writer_id.machine,
            "role": writer_id.role,
            "stream": writer_id.stream,
            "boot_epoch_id": writer_id.boot_epoch_id,
        },
    }

    raw_rows = _ok(world_store.append_store.read_raw(raw_receipt.fingerprint, for_world=World.LIVE))
    assert len(raw_rows) == 1
    assert raw_rows[0]["class"] == "qmn-verbatim-response-json-v1"
    assert json.loads(cast(str, raw_rows[0]["body"])) == raw_position
    reopened_source = _ok(
        SourceObservationBoundary(store).read(
            source_receipt.archive.fingerprint,
            in_world=World.LIVE,
            for_world=World.LIVE,
        )
    )
    assert type(reopened_source) is SourceObservation
    assert reopened_source.fingerprint == source_receipt.observation_fingerprint
    reopened_events = _ok(
        JournalReader(world_store.journal).read_checked("live-42", for_world=World.LIVE)
    )
    assert any(event.fingerprint == journal_receipt.event.fingerprint for event in reopened_events)
    instrument = _ok(Instrument.try_create(venue, "EURUSD"))
    decoded = _ok(
        resolve_checked_native_protection_readback(
            journal=world_store.journal,
            journal_stream="live-42",
            evidence_store=store,
            source_event=journal_receipt.event,
            authorized_writers=(writer_id,),
            expected_position_id="44",
            expected_account_id=42,
            expected_session_epoch="session-protection-fixture",
            expected_symbol_id=7,
            instrument=instrument,
            price_digits=5,
            rounding=RoundingMode.HALF_EVEN,
        )
    )
    assert decoded.stop_loss.value == 108_523
    for malformed in (
        replace(journal_receipt.event, payload=None),
        replace(journal_receipt.event, instant=123),
    ):
        assert is_refusal(
            resolve_checked_native_protection_readback(
                journal=world_store.journal,
                journal_stream="live-42",
                evidence_store=store,
                source_event=malformed,
                authorized_writers=(writer_id,),
                expected_position_id="44",
                expected_account_id=42,
                expected_session_epoch="session-protection-fixture",
                expected_symbol_id=7,
                instrument=instrument,
                price_digits=5,
                rounding=RoundingMode.HALF_EVEN,
            )
        )
    assert is_refusal(
        resolve_checked_native_protection_readback(
            journal=world_store.journal,
            journal_stream="live-42",
            evidence_store=store,
            source_event=journal_receipt.event,
            authorized_writers=(writer_id,),
            expected_position_id="44",
            expected_account_id=43,
            expected_session_epoch="session-protection-fixture",
            expected_symbol_id=7,
            instrument=instrument,
            price_digits=5,
            rounding=RoundingMode.HALF_EVEN,
        )
    )
    sequence_before = writer.next_sequence
    checked_before = reopened_events
    for bad_account, bad_session, native_id in (
        (True, "session-protection-fixture", "position-bool-account"),
        (42, "stale-session", "position-stale-session"),
    ):
        assert is_refusal(
            client.receive(
                WireKind.POSITION_READBACK,
                raw_position,
                native_id=native_id,
                response_account_id=bad_account,
                response_session_epoch=bad_session,
            )
        )
    assert writer.next_sequence == sequence_before
    checked_after = _ok(
        JournalReader(world_store.journal).read_checked("live-42", for_world=World.LIVE)
    )
    assert len(checked_after) == len(checked_before)

    forged_source_receipt = replace(source_receipt, archive=raw_receipt)
    forged_ack = SinkAck(
        detail={
            **intake_receipt.observation_ack.detail,
            "source_receipt": forged_source_receipt,
        }
    )
    refused_ack = journal_sink.append(
        {
            "event_type": "data quality",
            "event_time_ns": intake_receipt.identity.event_time_ns,
            "known_at_ns": intake_receipt.identity.known_at_ns,
            "source": intake_receipt.identity.source,
            "source_native_id": intake_receipt.identity.source_native_id,
            "revision": intake_receipt.identity.revision,
            "_observation_ack": forged_ack,
        }
    )
    assert is_refusal(refused_ack)
    assert writer.next_sequence == sequence_before

    source_mapping = {
        "event_type": "data quality",
        "event_time_ns": intake_receipt.identity.event_time_ns,
        "known_at_ns": intake_receipt.identity.known_at_ns,
        "source": intake_receipt.identity.source,
        "source_native_id": intake_receipt.identity.source_native_id,
        "revision": intake_receipt.identity.revision,
        "_observation_ack": intake_receipt.observation_ack,
    }
    actual_record: Callable[..., Result[JournalAppendReceipt]] = cast(
        "Callable[..., Result[JournalAppendReceipt]]", writer.record
    )
    for mutation in (
        "no-event",
        "bad-payload",
        "no-store",
        "foreign-engine",
        "bool-version",
        "foreign-body",
        "mutate-input",
        "shifted-time",
    ):

        def corrupt_record(
            event_type: object,
            payload: Mapping[str, object] | None = None,
            *,
            _mutation: str = mutation,
            **kwargs: object,
        ) -> Result[JournalAppendReceipt]:
            actual_payload = payload
            actual_kwargs = dict(kwargs)
            if _mutation == "foreign-body":
                actual_payload = {**(payload or {}), "foreign_body": "unrequested"}
            if _mutation == "mutate-input":
                assert payload is not None
                cast(dict[str, object], payload)["foreign_body"] = "mutated-before-append"
            if _mutation == "shifted-time":
                requested_instant = cast(Instant, actual_kwargs["instant"])
                actual_kwargs["instant"] = _ok(Instant.try_create(requested_instant.value_ns + 1))
            appended = actual_record(event_type, actual_payload, **actual_kwargs)
            assert is_ok(appended), appended
            record = appended.value
            if _mutation == "no-event":
                return Ok(replace(record, event=None))
            if _mutation == "bad-payload":
                return Ok(replace(record, event=replace(record.event, payload=None)))
            if _mutation == "no-store":
                return Ok(replace(record, store_receipt=None))
            if _mutation == "foreign-engine":
                return Ok(
                    replace(
                        record,
                        store_receipt=replace(record.store_receipt, engine="parquet"),
                    )
                )
            return Ok(
                replace(
                    record,
                    store_receipt=replace(record.store_receipt, format_version=True),
                )
            )

        writer.record = corrupt_record
        try:
            assert is_refusal(journal_sink.append(source_mapping))
        finally:
            writer.record = actual_record

    original_join: dict[str, object] = dict(
        cast(Mapping[str, object], journal_receipt.event.payload["_qmn_source_join"])
    )
    foreign_writer: Mapping[str, object] = {
        "machine": "foreign-machine",
        "role": writer_id.role,
        "stream": writer_id.stream,
        "boot_epoch_id": writer_id.boot_epoch_id,
    }
    shifted_time = _ok(Instant.try_create(journal_receipt.event.instant.value_ns + 1))
    join_writer = cast(Mapping[str, object], original_join["writer"])
    malformed_join_controls: tuple[tuple[Mapping[str, object], Instant], ...] = (
        (foreign_writer, journal_receipt.event.instant),
        (join_writer, shifted_time),
    )
    for writer_identity, at in malformed_join_controls:
        forged_payload = dict(journal_receipt.event.payload)
        forged_join = dict(original_join)
        forged_join["writer"] = writer_identity
        forged_payload["_qmn_source_join"] = forged_join
        forged_event = _ok(
            writer.record(
                JournalEventType.DATA_QUALITY,
                forged_payload,
                instant=at,
            )
        ).event
        assert is_refusal(
            resolve_checked_native_protection_readback(
                journal=world_store.journal,
                journal_stream="live-42",
                evidence_store=store,
                source_event=forged_event,
                authorized_writers=(writer_id,),
                expected_position_id="44",
                expected_account_id=42,
                expected_session_epoch="session-protection-fixture",
                expected_symbol_id=7,
                instrument=instrument,
                price_digits=5,
                rounding=RoundingMode.HALF_EVEN,
            )
        )
    clear_first_writer_registry()
