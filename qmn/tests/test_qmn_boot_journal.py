"""Durable CT-13 boot-attempt amendments retain one logical attempt."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest
import test_qmn_seat_tunnel as seat_fixture
from qmf.core import (
    MonotonicReading,
    Ok,
    Result,
    World,
    WriterId,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.core.chrono import Instant
from qmf.data import JournalWriter
from qmf.data.journal_producer import JournalReader
from qmf.data.store import JournalStore, jsonl_opener
from qmn.host._refuse import unavailable
from qmn.host.boot_ceremony import BootAttemptRecord, CompositionFingerprintInputs
from qmn.host.boot_journal import QmfBootAttemptJournalSink
from qmn.host.configured_hosted import persist_configured_standdown
from qmn.host.decision_root import OrderPathTiming, QmfHostedDecisionJournal
from qmn.host.sealed_runtime import (
    HostedRootInputs,
    SealedRuntimeRequest,
    run_sealed_hosted_runtime,
)
from qmn.ledger import QmfEntryReservationJournal
from qmn.order import (
    CommandIdentityBinder,
    CommandOrdinalStore,
    ConnectionCommandPacer,
    OrderPath,
)
from qmn.protection.ksa import KsaEnforcementScope, mint_level_epoch
from qmn.protection.ksa_journal import KSA_EPOCH_CLASS, KsaJournalProjection


def _writer() -> WriterId:
    result = WriterId.try_create("fixture-machine", "supervisor", "boot-lifecycle", "boot-1")
    assert is_ok(result)
    return result.value


def _instant() -> Ok[Instant]:
    result = Instant.try_create(1_700_000_000_000_000_100)
    assert is_ok(result)
    return Ok(result.value)


def _record(writer: WriterId, stage: str, sequence: int = 0) -> BootAttemptRecord:
    return BootAttemptRecord(
        boot_epoch_id=writer.boot_epoch_id,
        unit_role="qmn.service",
        stage=stage,
        writer=writer,
        sequence=sequence,
    )


def _actual_hosted_root_inputs(tmp_path: Path) -> HostedRootInputs:
    """Use the characterized seat/root fixture with durable QMF journal ports."""
    world_result = seat_fixture.fixture_ok(
        seat_fixture.fixture_evidence_store(tmp_path / "runtime-evidence").for_world(World.LIVE)
    )
    reservation_writer = seat_fixture.fixture_ok(
        WriterId.try_create("node-test", "risk", "entry-reservations", "boot-1")
    )
    reservation = seat_fixture.fixture_ok(
        QmfEntryReservationJournal.resume(
            world_result.journal,
            reservation_writer,
            stream_name="entry-reservations",
            instant=seat_fixture.fixture_instant,
        )
    )
    binding = seat_fixture.fixture_book_binding_record()
    binding_epoch = seat_fixture.fixture_ok(binding.fingerprint())
    recovered = seat_fixture.fixture_ok(reservation.recover(binding_epoch))
    path = seat_fixture.fixture_path(
        binding_record=binding,
        reservation_recovery=recovered,
        reservation_journal=reservation,
    )
    decision_writer = seat_fixture.fixture_ok(
        WriterId.try_create("node-test", "supervisor", "hosted-decisions", "boot-1")
    )
    decision = seat_fixture.fixture_ok(
        QmfHostedDecisionJournal.resume(
            world_result.journal,
            decision_writer,
            stream_name="hosted-decisions",
            instant=seat_fixture.fixture_instant,
        )
    )
    global_scope = KsaEnforcementScope.global_scope()
    stream_scope = seat_fixture.fixture_ok(
        KsaEnforcementScope.stream(
            seat_fixture.fixture_venue(), seat_fixture.fixture_account().account_id
        )
    )
    global_epoch = seat_fixture.fixture_ok(
        mint_level_epoch(
            epoch_id="global-epoch-1",
            scope=global_scope,
            opened_at=seat_fixture.fixture_instant(),
        )
    )
    stream_epoch = seat_fixture.fixture_ok(
        mint_level_epoch(
            epoch_id="stream-epoch-1",
            scope=stream_scope,
            opened_at=seat_fixture.fixture_instant(),
        )
    )
    ksa_writer_id = seat_fixture.fixture_ok(
        WriterId.try_create("node-test", "risk", "ksa-state", "boot-1")
    )
    ksa_writer = seat_fixture.fixture_ok(
        JournalWriter.resume(world_result.journal, ksa_writer_id, stream_name="ksa-state")
    )
    for epoch in (global_epoch, stream_epoch):
        seat_fixture.fixture_ok(
            ksa_writer.record_control_action(
                "ksa-level-epoch",
                instant=seat_fixture.fixture_instant(),
                payload={
                    "class": KSA_EPOCH_CLASS,
                    "epoch_fp1": seat_fixture.fixture_ok(fingerprint(epoch.fp1_identity())).value,
                    "epoch_id": epoch.epoch_id,
                    "scope": epoch.scope.token(),
                },
            )
        )
    projection = seat_fixture.fixture_ok(
        KsaJournalProjection.try_create(
            reader=JournalReader(world_result.journal),
            world=World.LIVE,
            stream_name="ksa-state",
            global_epoch=global_epoch,
            stream_epoch=stream_epoch,
            authorized_writers=frozenset({ksa_writer_id}),
        )
    )
    record_sink = seat_fixture.fixture_configured_root_record_sink()
    ordinal_store = seat_fixture.fixture_ok(
        CommandOrdinalStore.try_create(
            seat_fixture.fixture_venue(), seat_fixture.fixture_account(), record_sink
        )
    )
    seat_fixture.fixture_ok(ordinal_store.recover(0))
    binder = seat_fixture.fixture_ok(
        CommandIdentityBinder.try_create(record_sink, injective_total=False)
    )
    pacer = seat_fixture.fixture_ok(
        ConnectionCommandPacer.try_create(
            local_queue_bound=seat_fixture.fixture_duration(5_000_000_000),
            protective_reserve_capacity=2,
            general_capacity=1,
        )
    )
    client = seat_fixture.fixture_ok(
        seat_fixture.fixture_conformance_double.try_create(World.LIVE, seat_fixture.fixture_venue())
    )
    seat_fixture.fixture_ok(client.open_session(seat_fixture.fixture_account()))
    seat_fixture.fixture_ok(client.verify_capabilities())

    def timing_for(_command: object) -> Result[OrderPathTiming]:
        return Ok(
            OrderPathTiming(
                enqueued_at=seat_fixture.fixture_ok(MonotonicReading.try_create(100, "boot-1")),
                now_mono=seat_fixture.fixture_ok(MonotonicReading.try_create(200, "boot-1")),
                handed_off_at=seat_fixture.fixture_instant(),
            )
        )

    order_path = seat_fixture.fixture_ok(
        OrderPath.try_create(
            ordinal_store=ordinal_store,
            binder=binder,
            pacer=pacer,
            client=client,
            forms_per_order_type={"market": seat_fixture.fixture_entry_relative_form},
            submission_deadline_duration=seat_fixture.fixture_duration(5_000_000_000),
            command_journal=decision,
            position_ledger=path.position_ledger,
        )
    )
    seat_fixture.fixture_ok(order_path.open_sequencer())
    return HostedRootInputs(
        seat=seat_fixture.fixture_ok(seat_fixture.fixture_propose()),
        path=path,
        order_path=order_path,
        reservation_journal=reservation,
        ksa_projection=projection,
        decision_journal=decision,
        timing_for=timing_for,
    )


def test_boot_attempt_stages_durably_reopen_under_same_writer_epoch(tmp_path: Path) -> None:
    journal = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    writer = _writer()
    sink_result = QmfBootAttemptJournalSink.resume(journal, writer, instant=_instant)
    assert is_ok(sink_result)
    sink = sink_result.value

    assert is_ok(sink.append(_record(writer, "doors_bound")))
    assert is_ok(sink.amend(_record(writer, "boot_attempt_written")))
    journal.close()

    reopened = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    resumed = QmfBootAttemptJournalSink.resume(reopened, writer, instant=_instant)
    assert is_ok(resumed)
    assert is_ok(resumed.value.amend(_record(writer, "preflight")))
    events = JournalReader(reopened).read_checked("boot-lifecycle", for_world=World.LIVE)
    assert is_ok(events)
    assert [event.sequence for event in events.value] == [0, 1, 2]
    assert [event.payload["control_action_subtype"] for event in events.value] == [
        "qmn-boot-attempt",
        "qmn-boot-attempt-stage",
        "qmn-boot-attempt-stage",
    ]
    assert events.value[2].payload["previous_event_fp1"] == events.value[1].fingerprint.value
    reopened.close()


def test_boot_attempt_rejects_wrong_writer_and_stage_without_append(tmp_path: Path) -> None:
    journal = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    wrong = WriterId.try_create("fixture-machine", "operator", "boot-lifecycle", "boot-1")
    assert is_ok(wrong)
    refused = QmfBootAttemptJournalSink.resume(journal, wrong.value, instant=_instant)
    assert is_refusal(refused)

    writer = _writer()
    sink = QmfBootAttemptJournalSink.resume(journal, writer, instant=_instant)
    assert is_ok(sink)
    bad_stage = sink.value.append(_record(writer, "preflight"))
    assert is_refusal(bad_stage)
    assert sink.value.writer.next_sequence == 0
    journal.close()


def test_seal_must_be_reopened_before_missing_root_resources_stand_down(tmp_path: Path) -> None:
    journal = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    writer = _writer()
    sink = QmfBootAttemptJournalSink.resume(journal, writer, instant=_instant)
    assert is_ok(sink)
    inputs_fp = fingerprint({"fixture": "boot-composition"})
    assert is_ok(inputs_fp)
    request = SealedRuntimeRequest(
        boot_epoch_id="boot-1",
        machine="fixture-machine",
        composition_inputs=CompositionFingerprintInputs(
            config_fp=inputs_fp.value,
            distribution_identities={
                "qmf": "fixture",
                "qmb": "fixture",
                "qml": "fixture",
                "qmn": "fixture",
            },
            registry_as_of_fp=inputs_fp.value,
            calendar_code_identities={
                "market_hours_calendar": "fixture",
                "day_boundary_calendar": "fixture",
                "news_calendar": "fixture",
            },
            os_cpu_class="fixture-linux",
        ),
        writer_streams=(),
        boot_attempt_sink=sink.value,
    )
    result = run_sealed_hosted_runtime(
        request,
        HostedRootInputs(
            seat=None,
            path=None,
            order_path=None,
            reservation_journal=None,
            ksa_projection=None,
            decision_journal=None,
            timing_for=lambda _command: unavailable(
                "timing", "test refuses before timing is consumed"
            ),
        ),
    )
    assert is_ok(result)
    assert result.value.ceremony.stage_reached == "seal"
    assert result.value.ceremony.sealed
    assert result.value.root is None
    assert result.value.stand_down_reason is not None
    assert not result.value.ready
    composition_fp = result.value.ceremony.composition_fp
    assert composition_fp is not None
    verified = sink.value.verify_sealed(composition_fp)
    assert is_ok(verified)
    journal.close()


def test_durable_boot_seal_opens_the_characterized_hosted_root(tmp_path: Path) -> None:
    journal = JournalStore(World.LIVE, journal_dir=tmp_path / "boot", open_stream=jsonl_opener())
    writer = _writer()
    sink = QmfBootAttemptJournalSink.resume(journal, writer, instant=_instant)
    assert is_ok(sink)
    inputs_fp = fingerprint({"fixture": "boot-root-composition"})
    assert is_ok(inputs_fp)
    request = SealedRuntimeRequest(
        boot_epoch_id="boot-1",
        machine="fixture-machine",
        composition_inputs=CompositionFingerprintInputs(
            config_fp=inputs_fp.value,
            distribution_identities={
                "qmf": "fixture",
                "qmb": "fixture",
                "qml": "fixture",
                "qmn": "fixture",
            },
            registry_as_of_fp=inputs_fp.value,
            calendar_code_identities={
                "market_hours_calendar": "fixture",
                "day_boundary_calendar": "fixture",
                "news_calendar": "fixture",
            },
            os_cpu_class="fixture-linux",
        ),
        writer_streams=(),
        boot_attempt_sink=sink.value,
    )
    composed = run_sealed_hosted_runtime(request, _actual_hosted_root_inputs(tmp_path))
    assert is_ok(composed)
    assert composed.value.ceremony.stage_reached == "seal"
    assert composed.value.root is not None
    assert composed.value.ready
    journal.close()


def test_missing_supervisor_resources_are_durably_recorded_as_stand_down(
    tmp_path: Path,
) -> None:
    journal = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    recorded = persist_configured_standdown(
        journal_store=journal,
        machine="fixture-machine",
        boot_epoch_id="boot-1",
        instant=_instant,
        reason="fixture resource provider is absent",
    )
    assert is_ok(recorded)
    assert recorded.value.stage == "preflight"
    assert recorded.value.failure_id == "configured_runtime.hosted_resources_missing"
    events = JournalReader(journal).read_checked("boot-lifecycle", for_world=World.LIVE)
    assert is_ok(events)
    assert len(events.value) == 3
    attempt = cast(Mapping[str, object], events.value[-1].payload["attempt"])
    assert attempt["stage"] == "preflight"
    assert attempt["failure_id"] == ("configured_runtime.hosted_resources_missing")
    journal.close()


def test_failed_stand_down_journal_write_is_not_reported_as_persisted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())

    def fail_record(_self: object, _subtype: object, *, instant: object, payload: object) -> object:
        del instant
        del payload
        return unavailable("journal_append", "injected CT-13 append refusal")

    monkeypatch.setattr(JournalWriter, "record_control_action", fail_record)
    refused = persist_configured_standdown(
        journal_store=journal,
        machine="fixture-machine",
        boot_epoch_id="boot-1",
        instant=_instant,
        reason="fixture journal is closed",
    )
    assert is_refusal(refused)
    journal.close()
