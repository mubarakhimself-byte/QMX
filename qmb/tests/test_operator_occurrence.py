"""Durable invocation-to-terminal witnesses use checked CT-13 readback."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

from qmb.host.operator_occurrence import (
    OperatorOccurrenceIdentity,
    read_operator_occurrence,
    record_operator_occurrence,
)
from qmb.host.qma_cli import QmaBacktestContext
from qmf.core import Fingerprint, Instant, Result, World, WriterId, is_ok, is_refusal
from qmf.data.journal_producer import JournalReader, JournalWriter
from qmf.data.store import EvidenceStore

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(token: str) -> Fingerprint:
    return _ok(Fingerprint.try_create(f"fp1:sha256:{token * 64}"))


def _fixture(tmp_path: Path):
    context = QmaBacktestContext(
        job_id="job-occurrence-1",
        attempt_id=3,
        experiment_spec_fp1=_fp("a"),
        evidence_ref=_fp("b"),
        split_manifest_fp1=_fp("c"),
        environment_ref="env:recorded-replay",
        occupancy_key="run:occurrence-1",
        mints_ct32=False,
        operator_descriptor_fp1=_fp("d"),
    )
    store_root = tmp_path / "qmf"
    world_store = _ok(EvidenceStore(store_root).for_world(World.REPLAY))
    writer = _ok(WriterId.try_create("worker-1", "qmb", "operator-run", "boot-1"))
    journal_writer = JournalWriter(world_store.journal, writer, stream_name="operator-run")
    terminal_writer = _ok(WriterId.try_create("worker-1", "qmb", "terminal", "boot-1"))
    identity = _identity(context, tmp_path, writer)
    return context, world_store.journal, journal_writer, terminal_writer, identity


def _identity(
    context: QmaBacktestContext,
    root: Path,
    writer: WriterId,
    *,
    terminal_token: str = "f",
):
    return _ok(
        OperatorOccurrenceIdentity.try_create(
            context=context,
            composition_class="alternative",
            runtime_descriptor_fp1=context.operator_descriptor_fp1,
            operator_binding_fp1=_fp("e"),
            terminal_fp1=_fp(terminal_token),
            at=_ok(Instant.try_create(1_800_000_000_000_000_000)),
            domain_result_fp1=_fp("1"),
            terminal_root=root / "terminal",
            journal_root=root / "journal",
            terminal_writer=_ok(WriterId.try_create("worker-1", "qmb", "terminal", "boot-1")),
            journal_writer=writer,
            journal_stream="operator-run",
            command_owner_epoch=7,
        )
    )


def test_occurrence_is_checked_and_idempotent_after_reopen(tmp_path: Path) -> None:
    _, journal, writer, _, identity = _fixture(tmp_path)

    first = _ok(
        record_operator_occurrence(
            identity=identity,
            journal_writer=writer,
            journal_store=journal,
            at=identity.at,
        )
    )
    reopened_writer = _ok(JournalWriter.resume(journal, writer.writer, stream_name="operator-run"))
    second = _ok(
        record_operator_occurrence(
            identity=identity,
            journal_writer=reopened_writer,
            journal_store=journal,
            at=identity.at,
        )
    )
    readback = _ok(
        read_operator_occurrence(identity=identity, journal_reader=JournalReader(journal))
    )

    assert first.event.to_row() == second.event.to_row() == readback.event.to_row()
    assert first.physical_sequence == second.physical_sequence == 0
    assert reopened_writer.next_sequence == 1


def test_occurrence_refuses_relabelled_context_and_malformed_identity(tmp_path: Path) -> None:
    context, journal, writer, _, identity = _fixture(tmp_path)
    _ok(
        record_operator_occurrence(
            identity=identity,
            journal_writer=writer,
            journal_store=journal,
            at=identity.at,
        )
    )

    foreign_context = replace(context, job_id="foreign-job")
    foreign = _identity(foreign_context, tmp_path, writer.writer)
    assert is_refusal(
        read_operator_occurrence(identity=foreign, journal_reader=JournalReader(journal))
    )

    tampered = replace(identity, terminal_fp1=_fp("2"))
    assert is_refusal(
        read_operator_occurrence(identity=tampered, journal_reader=JournalReader(journal))
    )
    assert is_refusal(
        OperatorOccurrenceIdentity.try_create(
            context=replace(context, attempt_id=True),
            composition_class="alternative",
            runtime_descriptor_fp1=context.operator_descriptor_fp1,
            operator_binding_fp1=_fp("e"),
            terminal_fp1=_fp("f"),
            at=identity.at,
            terminal_root=tmp_path / "terminal",
            journal_root=tmp_path / "journal",
            journal_writer=writer.writer,
            journal_stream="operator-run",
            command_owner_epoch=7,
        )
    )


def test_nominal_occurrence_fields_refuse_before_any_append(tmp_path: Path) -> None:
    _, journal, writer, _, identity = _fixture(tmp_path)
    malformed: tuple[object, ...] = (
        replace(identity, runtime_descriptor_fp1=None),
        replace(identity, composition_class=cast("object", [])),
        replace(identity, operator_binding_fp1=cast("object", {})),
        replace(identity, context=cast("object", {"job_id": "bad"})),
        replace(identity, terminal_writer=cast("object", {"machine": "bad"})),
        replace(identity, terminal_root=cast("object", None)),
        replace(identity, at=cast("object", "not-an-instant")),
        replace(identity, command_owner_epoch=True),
    )

    for candidate in malformed:
        refused = record_operator_occurrence(
            identity=candidate,
            journal_writer=writer,
            journal_store=journal,
            at=identity.at,
        )
        assert is_refusal(refused)
        assert writer.next_sequence == 0
    assert _ok(journal.read_stream("operator-run", for_world=World.REPLAY)) == []


def test_occurrence_refuses_conflicting_same_invocation_witness(tmp_path: Path) -> None:
    context, journal, writer, _, identity = _fixture(tmp_path)
    _ok(
        record_operator_occurrence(
            identity=identity,
            journal_writer=writer,
            journal_store=journal,
            at=identity.at,
        )
    )

    conflicting = _identity(context, tmp_path, writer.writer, terminal_token="2")
    payload = {
        "class": "qmb-ct13-data-quality-v1",
        "component": "COMP-QMB",
        "contract": "CT-13",
        "event_type_wire": "data quality",
        "kind": "qmb-operator-terminal-occurrence-v1",
        "identity": conflicting.identity(),
        "identity_fp1": conflicting.fingerprint.value,
        "occurrence_key_fp1": conflicting.occurrence_key_fp1.value,
        "is_edge_claim": False,
        "fills_gaps": False,
    }
    _ok(
        writer.record_data_quality(
            payload, instant=identity.at, correlation_id=conflicting.occurrence_key_fp1.value
        )
    )
    assert is_refusal(
        read_operator_occurrence(identity=identity, journal_reader=JournalReader(journal))
    )
