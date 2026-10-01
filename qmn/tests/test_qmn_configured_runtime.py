"""Configured supervisor preflight never manufactures runtime authority."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest
from google.protobuf import descriptor_pb2
from qmf.core import (
    CalendarIdentity,
    ExactRational,
    Instant,
    Money,
    Ok,
    SinkAck,
    SinkResult,
    UnitKind,
    VenueId,
    World,
    WriterId,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.data.journal_producer import JournalReader, JournalWriter
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener
from qmf.registry import LoadedRecord, RegistrationRecord, RegistryPersistence
from qmf.risk.binding import (
    BmsInstanceId,
    BookBindingRecord,
    BookInstanceId,
    CapabilityCheckResult,
    PositionModel,
    StateCarry,
)
from qmf.risk.control_rank import ControlActionKind
from qmf.risk.grammar import AdmissionImpact, TemplateSection, TemplateVariable, UiEditability
from qmf.risk.templates import BmsDefinition, BookDefinition
from qmf.venue.proto import descriptor_set_digest
from qml.declaration import mint_bot_definition, mint_confluence
from qml.footprint import ProducerBinding, mint_footprint
from qml.logic import mint_logic_identity
from qmn.host.configured_runtime import (
    CONFIGURED_REGISTRY_REFERENCE_KINDS,
    assess_configured_runtime,
    configured_registry_as_of_fingerprint,
    resolve_registered_binding,
)
from qmn.promotion import ActivationBindingTransition, ActivationPhase, persist_activation
from qmn.seats.state import OPERATOR_PRINCIPAL, GovernedSeatState


def _references(
    root: Path, *, nonempty_templates: bool = False
) -> tuple[dict[str, str], str, BookBindingRecord]:
    registry = root / "registry"
    registry.mkdir(exist_ok=True)
    opened = RegistryPersistence.open(EvidenceStore(registry), World.LIVE)
    assert is_ok(opened)
    refs: dict[str, str] = {}
    writer = WriterId.try_create("fixture-machine", "composition", "registry", "fixture-boot")
    instant = Instant.try_create(1_700_000_000_000_000_000)
    assert is_ok(writer) and is_ok(instant)
    book_sections: dict[str, TemplateSection] = {}
    bms_sections: dict[str, TemplateSection] = {}
    if nonempty_templates:
        declared_floor = Money.try_create(100, "USD", 2)
        assert is_ok(declared_floor)
        floor = TemplateVariable.try_create(
            "loss_floor",
            UnitKind.MONEY,
            declared_floor.value,
            UiEditability.UNEDITABLE,
            AdmissionImpact.RESIGN,
        )
        assert is_ok(floor)
        book_section = TemplateSection.try_create("money_rules", {"loss_floor": floor.value})
        assert is_ok(book_section)
        book_sections["money_rules"] = book_section.value
        rank_variables: dict[str, TemplateVariable] = {}
        for rank, action in enumerate(ControlActionKind):
            declared_rank = ExactRational.try_create(rank, 1, UnitKind.COUNT)
            assert is_ok(declared_rank)
            variable = TemplateVariable.try_create(
                action.value,
                UnitKind.COUNT,
                declared_rank.value,
                UiEditability.UNEDITABLE,
                AdmissionImpact.RELINT,
            )
            assert is_ok(variable)
            rank_variables[action.value] = variable.value
        rank_section = TemplateSection.try_create("control_rank_table", rank_variables)
        assert is_ok(rank_section)
        bms_sections["control_rank_table"] = rank_section.value
    book = BookDefinition.try_create(1, "USD", book_sections)
    bms = BmsDefinition.try_create(1, bms_sections)
    assert is_ok(book) and is_ok(bms)
    book_fp = book.value.fingerprint()
    bms_fp = bms.value.fingerprint()
    assert is_ok(book_fp) and is_ok(bms_fp)
    venue_id = VenueId.try_create("fixture-venue")
    book_instance_id = BookInstanceId.try_create("fixture-book-instance")
    assert is_ok(venue_id) and is_ok(book_instance_id)
    bms_instance_id = BmsInstanceId.derive(
        bms_fp.value, "fixture-account", venue_id.value, World.LIVE
    )
    state_carry = StateCarry.try_create(
        dict.fromkeys(("ledger", "cycle", "budget", "bench_counter", "exposure"), "reset")
    )
    capability = CapabilityCheckResult(
        position_model=PositionModel.HEDGING,
        settlement_currency="USD",
        satisfied_capabilities=frozenset(),
        shared_flatten_signature=None,
        satisfied_sensor_baselines=frozenset(),
        live_path_rung_baseline_present=True,
        rank_table_non_contradicted=True,
    )
    assert is_ok(venue_id)
    assert is_ok(book_instance_id)
    assert is_ok(bms_instance_id)
    assert is_ok(state_carry)
    typed_binding = BookBindingRecord.try_create(
        book_instance_id.value,
        bms_instance_id.value,
        venue_id.value,
        "fixture-account",
        World.LIVE,
        book_fp.value,
        bms_fp.value,
        state_carry.value,
        capability,
    )
    assert is_ok(typed_binding)
    producer_fp = fingerprint({"class": "loader-fixture-producer"})
    assert is_ok(producer_fp)
    producer = ProducerBinding.try_create(producer_fp.value)
    assert is_ok(producer)
    confluence = mint_confluence([{"role": "level", "producer_binding": producer.value}])
    assert is_ok(confluence)
    calendar = CalendarIdentity.try_create("fixture-calendar", "1", "2025.2")
    assert is_ok(calendar)
    footprint = mint_footprint(
        [
            {
                "instrument_role": "primary",
                "bar_specs": [{"kind": "time-interval", "seconds": 60}],
                "stream_role": "trading",
            }
        ],
        [calendar.value],
        [producer.value],
    )
    logic = mint_logic_identity(
        "fixture-bot",
        "1.0.0",
        {
            "bot.py": "def on_instant(self, evidence):\n    return ()\n",
            "factory.py": (
                "from qml.protocol import FunctionFactory\n"
                "factory = FunctionFactory(logic=lambda evidence: ())\n"
            ),
        },
    )
    assert is_ok(footprint) and is_ok(logic)
    bot = mint_bot_definition(
        strategy_family_id="fixture-family",
        confluence_set=[confluence.value],
        parameter_space=[],
        footprint=footprint.value,
        permitted_exit_intents=[],
        logic_reference=logic.value,
    )
    assert is_ok(bot)
    record_bodies: dict[str, dict[str, object]] = {
        "book-definition": {
            "accounting_currency": book.value.accounting_currency,
            "sections": {
                name: section.fp1_identity() for name, section in book.value.sections.items()
            },
        },
        "bms-definition": {
            "sections": {
                name: section.fp1_identity() for name, section in bms.value.sections.items()
            }
        },
        "bot-definition": bot.value.body(),
        "book-binding": typed_binding.value.fp1_identity(),
    }
    for sequence, kind in enumerate(CONFIGURED_REGISTRY_REFERENCE_KINDS.values()):
        record = RegistrationRecord.try_create(
            kind,
            1,
            (),
            record_bodies[kind],
            writer.value,
            sequence,
            instant.value,
        )
        assert is_ok(record)
        stored = opened.value.persist_record(record.value)
        assert is_ok(stored)
        refs[kind] = record.value.stable_id.value
    opened.value.close()
    loaded_store = RegistryPersistence.open(EvidenceStore(registry), World.LIVE)
    assert is_ok(loaded_store)
    loaded: dict[str, LoadedRecord] = {}
    key_by_kind = {value: key for key, value in CONFIGURED_REGISTRY_REFERENCE_KINDS.items()}
    for kind, key in refs.items():
        row = loaded_store.value.load_record(key, for_world=World.LIVE)
        assert is_ok(row)
        loaded[key_by_kind[kind]] = row.value
    loaded_store.value.close()
    as_of = configured_registry_as_of_fingerprint(loaded)
    assert is_ok(as_of)
    return refs, as_of.value.value, typed_binding.value


def _activation_evidence(root: Path, binding: BookBindingRecord) -> dict[str, object]:
    writer = WriterId.try_create(
        "fixture-machine", "operator", "activation", "fixture-activation-boot"
    )
    instant = Instant.try_create(1_700_000_000_000_000_100)
    assert is_ok(writer) and is_ok(instant)
    transition = ActivationBindingTransition.try_create(
        phase=ActivationPhase.SUCCESSFUL,
        seat_id="fixture-seat",
        binding_id=binding.book_instance_id.value,
        requested_state=GovernedSeatState.ACTIVE,
        enforced_state=GovernedSeatState.ACTIVE,
        operator_signature=OPERATOR_PRINCIPAL,
        transition_instant=instant.value,
        effective_at=instant.value,
    )
    assert is_ok(transition)
    journal_root = root / "activation-journal"
    journal = JournalStore(World.LIVE, journal_dir=journal_root, open_stream=jsonl_opener())
    journal_writer = JournalWriter(journal, writer.value, stream_name="activation")
    recorded = persist_activation(
        journal=_QmfActivationJournalSink(journal_writer),
        transition=transition.value,
        correlation_id="activation-fixture",
    )
    assert is_ok(recorded)
    reopened = JournalReader(journal).read_checked("activation", for_world=World.LIVE)
    assert is_ok(reopened) and len(reopened.value) == 1
    event = reopened.value[0]
    event_fp = event.fingerprint.value
    binding_fp = binding.fingerprint()
    assert is_ok(binding_fp)
    journal.close()
    return {
        "journal_root": str(journal_root),
        "stream_name": "activation",
        "event_fp1": event_fp,
        "sequence": event.sequence,
        "writer": {
            "machine": writer.value.machine,
            "role": writer.value.role,
            "stream": writer.value.stream,
            "boot_epoch_id": writer.value.boot_epoch_id,
        },
        "world": World.LIVE.value,
        "binding_id": binding.book_instance_id.value,
        "binding_epoch_fp1": binding_fp.value.value,
        "seat_id": "fixture-seat",
    }


class _QmfActivationJournalSink:
    """Test-only JournalSink adapter that persists QMN activation rows through QMF."""

    def __init__(self, writer: JournalWriter) -> None:
        self._writer = writer

    def append(self, event: Mapping[str, object], /) -> SinkResult:
        raw_payload = event.get("payload")
        if not isinstance(raw_payload, Mapping):
            raise AssertionError("activation journal row has a payload")
        payload = cast("Mapping[str, object]", raw_payload)
        raw_transition = payload.get("transition_record")
        if not isinstance(raw_transition, Mapping):
            raise AssertionError("activation event retains its CT-24 identity")
        transition = cast("Mapping[str, object]", raw_transition)
        raw_instant = transition.get("transition_instant")
        if not isinstance(raw_instant, Mapping):
            raise AssertionError("CT-24 transition carries its instant")
        instant = cast("Mapping[str, object]", raw_instant)
        result = self._writer.record(
            event.get("event_type"),
            payload,
            instant=instant.get("value_ns"),
            correlation_id=event.get("correlation_id"),
        )
        if not is_ok(result):
            return result
        return Ok(SinkAck())


def _deployment(
    root: Path,
    descriptor_path: Path | None,
    digest: str,
    *,
    nonempty_templates: bool = False,
) -> Path:
    refs, as_of, binding = _references(root, nonempty_templates=nonempty_templates)
    activation_evidence = _activation_evidence(root, binding)
    payload = {
        "format_version": 1,
        "machine": "fixture-machine",
        "registry_root": str(root / "registry"),
        "registry_as_of_fp1": as_of,
        "config_layers": {"roster_identity": {"roster_fp1": "fixture-roster"}},
        "roster": {
            "account_bindings": [],
            "sensing_only": [
                {
                    "venue_id": "fixture-venue",
                    "environment": "demo",
                    "account_id": "fixture-account",
                    "credential_reference": "secret://fixture",
                    "opaque_metric_id": "fixture-metric",
                    "world": "replay",
                }
            ],
            "protective_reserve_capacity": 1,
        },
        "proto": {
            "package_name": "openapi-proto-messages",
            "release_tag": 91,
            "descriptor_digest": digest,
            "descriptor_path": None if descriptor_path is None else str(descriptor_path),
        },
        "required_references": {
            "ct28_fp1": refs["book-binding"],
            "ct22_fp1": refs["book-definition"],
            "ct27_fp1": refs["bms-definition"],
            "ct33_fp1": refs["bot-definition"],
            "activation_evidence": activation_evidence,
        },
    }
    path = root / "deployment.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


fixture_deployment = _deployment


def test_missing_pinned_protocol_bytes_refuse_as_typed_stand_down(tmp_path: Path) -> None:
    path = _deployment(tmp_path, None, "sha256:" + "b" * 64)

    refused = assess_configured_runtime(path, qmx_root=tmp_path)

    assert is_refusal(refused)
    assert refused.context.get("failure_id") == "configured_runtime.proto_missing"


def test_valid_local_pins_remain_stand_down_without_admission(tmp_path: Path) -> None:
    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "fixture.proto"
    proto.package = "fixture"
    proto.syntax = "proto3"
    raw = descriptor_set.SerializeToString()
    digest = descriptor_set_digest(raw)
    assert is_ok(digest)
    descriptor_path = tmp_path / "pinned-proto.pb"
    descriptor_path.write_bytes(raw)
    path = _deployment(tmp_path, descriptor_path, digest.value)

    assessed = assess_configured_runtime(path, qmx_root=tmp_path)

    assert is_ok(assessed)
    assert assessed.value.stand_down
    assert assessed.value.stand_down_reason is not None
    assert assessed.value.activation_authorized is False
    assert assessed.value.provider_ready is False
    assert assessed.value.activation.phase is ActivationPhase.SUCCESSFUL
    assert (
        assessed.value.activation.transition.binding_id
        == assessed.value.binding_record.book_instance_id.value
    )
    binding_fp = assessed.value.binding_record.fingerprint()
    assert is_ok(binding_fp)
    assert binding_fp.value == assessed.value.binding_fingerprint


def test_nonempty_registered_book_and_bms_reload_as_typed_assessment(
    tmp_path: Path,
) -> None:
    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "fixture-nonempty.proto"
    proto.package = "fixture_nonempty"
    proto.syntax = "proto3"
    raw = descriptor_set.SerializeToString()
    digest = descriptor_set_digest(raw)
    assert is_ok(digest)
    descriptor_path = tmp_path / "pinned-proto.pb"
    descriptor_path.write_bytes(raw)
    path = _deployment(
        tmp_path,
        descriptor_path,
        digest.value,
        nonempty_templates=True,
    )

    assessed = assess_configured_runtime(path, qmx_root=tmp_path)

    assert is_ok(assessed), assessed
    assert "money_rules" in assessed.value.book_definition.sections
    assert "control_rank_table" in assessed.value.bms_definition.sections
    assert assessed.value.stand_down
    assert assessed.value.activation_authorized is False
    assert assessed.value.provider_ready is False


def test_registered_binding_decoder_refuses_stale_tuple_and_incomplete_carry(
    tmp_path: Path,
) -> None:
    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "fixture.proto"
    proto.package = "fixture"
    proto.syntax = "proto3"
    raw = descriptor_set.SerializeToString()
    digest = descriptor_set_digest(raw)
    assert is_ok(digest)
    descriptor_path = tmp_path / "pinned-proto.pb"
    descriptor_path.write_bytes(raw)
    path = _deployment(tmp_path, descriptor_path, digest.value)
    assessed = assess_configured_runtime(path, qmx_root=tmp_path)
    assert is_ok(assessed)
    binding = assessed.value.binding_record.fp1_identity()
    book_fp = assessed.value.binding_record.book_definition_fingerprint
    bms_fp = assessed.value.binding_record.bms_definition_fingerprint

    stale = dict(binding)
    stale["bms_instance_id"] = "fp1:sha256:" + "0" * 64
    assert is_refusal(
        resolve_registered_binding(stale, expected_book_fp=book_fp, expected_bms_fp=bms_fp)
    )

    incomplete = dict(binding)
    state = dict(cast("dict[str, object]", binding["state_carry"]))
    per_counter = dict(cast("dict[str, object]", state["per_counter"]))
    per_counter.pop("exposure")
    state["per_counter"] = per_counter
    incomplete["state_carry"] = state
    assert is_refusal(
        resolve_registered_binding(incomplete, expected_book_fp=book_fp, expected_bms_fp=bms_fp)
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("world", World.REPLAY.value),
        ("sequence", 1),
        ("stream_name", "other-stream"),
        ("binding_epoch_fp1", "fp1:sha256:" + "0" * 64),
    ],
)
def test_activation_resolver_refuses_changed_ct13_boundaries(
    tmp_path: Path, field: str, replacement: object
) -> None:
    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "fixture.proto"
    proto.package = "fixture"
    proto.syntax = "proto3"
    raw = descriptor_set.SerializeToString()
    digest = descriptor_set_digest(raw)
    assert is_ok(digest)
    descriptor_path = tmp_path / "pinned-proto.pb"
    descriptor_path.write_bytes(raw)
    path = _deployment(tmp_path, descriptor_path, digest.value)
    payload = json.loads(path.read_text(encoding="utf-8"))
    activation = payload["required_references"]["activation_evidence"]
    activation[field] = replacement
    path.write_text(json.dumps(payload), encoding="utf-8")

    refused = assess_configured_runtime(path, qmx_root=tmp_path)

    assert is_refusal(refused)


def test_deployment_file_outside_operator_root_is_refused(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-deployment.json"
    outside.write_text("{}", encoding="utf-8")

    refused = assess_configured_runtime(outside, qmx_root=tmp_path)

    assert is_refusal(refused)
