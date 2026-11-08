"""AD-32 private evidence wrapper preserves checked lineage and incompleteness."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

from google.protobuf import descriptor_pb2
from qmf.core import (
    Account,
    AccountRole,
    Duration,
    ExactRational,
    Instant,
    Instrument,
    Money,
    Result,
    UnitKind,
    VenueId,
    World,
    canonical_bytes,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.data.store import EvidenceStore
from qmf.risk.control_rank import ControlActionKind
from qmf.risk.grammar import AdmissionImpact, TemplateSection, TemplateVariable, UiEditability
from qmf.risk.templates import BMS_CONTRACT_FORMAT_VERSION, BmsDefinition
from qmf.venue.proto import descriptor_set_digest
from qmn.host.admission_evidence import (
    AdmissionEvidenceRef,
    derive_bms_control_rank_table,
    persist_admission_evidence,
    read_admission_evidence,
)
from qmn.host.configured_runtime import assess_configured_runtime
from qmn.host.shakedown import (
    ShakedownPlan,
    ShakedownSignaturePage,
    assemble_shakedown_signature_page,
    run_demo_shakedown,
)
from qmf.readings.signal_snapshot import sqs_baseline_key
from qmn.protection.windows import AnchorSide, require_resolved_window_settings
from qmn.venue import Command
from test_qmn_configured_runtime import fixture_deployment

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _demo_page(venue: VenueId) -> ShakedownSignaturePage:
    instant = _ok(Instant.try_create(1_700_000_000_000_000_000))
    duration = _ok(Duration.try_create(60_000_000_000))
    windows = _ok(
        require_resolved_window_settings(
            news_blackout_before=duration,
            news_blackout_after=duration,
            daily_dead_zone_width=duration,
            session_handover_buffer_width=duration,
            session_handover_buffer_anchor=AnchorSide.PRE_CLOSE,
            news_calendar_max_staleness=duration,
        )
    )
    account = _ok(Account.try_create("fixture-account", venue, AccountRole.DEMO))
    command = _ok(Command.cancel_order(venue, account, "demo-session", 1, "order-1"))
    instrument = _ok(Instrument.try_create(venue, "EURUSD"))
    plan = _ok(
        ShakedownPlan.try_create(
            binding_identity="fixture-binding",
            shakedown_role=AccountRole.DEMO,
            live_path_rung_baseline_present=True,
            sensor_baselines_present=True,
            window_settings=windows,
            ledger_binding_epoch=_ok(fingerprint({"class": "demo-epoch"})),
            ledger_seed=_ok(Money.try_create(50_000, "USD", 2)),
            ledger_recorded_at=instant,
            kill_line_capital_floor=_ok(Money.try_create(10_000, "USD", 2)),
            kill_line_equity=_ok(Money.try_create(40_000, "USD", 2)),
            kill_line_evaluated_at=instant,
            sqs_venue=venue,
            sqs_environment="demo",
            sqs_instrument=instrument,
            callback_deadline=_ok(Duration.try_create(5_000_000)),
            memory_ceiling_bytes=8_388_608,
            dry_run_command=command,
            protective_stop_forms={"market": "entry-relative"},
        )
    )
    evidence = _ok(run_demo_shakedown(plan))
    return _ok(
        assemble_shakedown_signature_page(
            layer1_checks_run=("registration-lint",),
            shakedown=replace(
                evidence,
                sqs_baseline=_ok(sqs_baseline_key(venue, "demo", instrument)),
            ),
        )
    )


def test_bms_rank_adapter_uses_all_and_only_declared_exact_count_rows() -> None:
    variables: dict[str, TemplateVariable] = {}
    for rank, action in enumerate(ControlActionKind):
        value = _ok(ExactRational.try_create(rank, 1, UnitKind.COUNT))
        variable = _ok(
            TemplateVariable.try_create(
                action.value,
                UnitKind.COUNT,
                value,
                UiEditability.UNEDITABLE,
                AdmissionImpact.RELINT,
            )
        )
        variables[action.value] = variable
    section = _ok(TemplateSection.try_create("control_rank_table", variables))
    bms = _ok(
        BmsDefinition.try_create(
            BMS_CONTRACT_FORMAT_VERSION,
            {"control_rank_table": section},
        )
    )

    table = _ok(derive_bms_control_rank_table(bms))

    assert set(table.ranks_by_kind()) == set(ControlActionKind)
    assert table.ranks_by_kind()[ControlActionKind.SUSPEND_NEW] == 0
    missing = _ok(BmsDefinition.try_create(BMS_CONTRACT_FORMAT_VERSION, {}))
    assert is_refusal(derive_bms_control_rank_table(missing))


def test_private_ad32_wrapper_persists_real_registry_lineage_as_incomplete(
    tmp_path: Path,
) -> None:
    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "admission-fixture.proto"
    proto.package = "admission_fixture"
    proto.syntax = "proto3"
    descriptor_bytes = descriptor_set.SerializeToString()
    digest = _ok(descriptor_set_digest(descriptor_bytes))
    descriptor_path = tmp_path / "pinned-proto.pb"
    descriptor_path.write_bytes(descriptor_bytes)
    deployment = fixture_deployment(tmp_path, descriptor_path, digest)
    assessment = _ok(assess_configured_runtime(deployment, qmx_root=tmp_path))

    venue = _ok(VenueId.try_create("fixture-venue"))
    page = _demo_page(venue)
    store_root = tmp_path / "admission-evidence"
    written = _ok(persist_admission_evidence(EvidenceStore(store_root), assessment, page))
    reopened = _ok(read_admission_evidence(EvidenceStore(store_root), written))

    records_raw = reopened["registered_records"]
    assert isinstance(records_raw, Mapping)
    records = cast(Mapping[str, object], records_raw)
    missing_raw = reopened["missing_evidence"]
    assert isinstance(missing_raw, list)
    missing = cast(list[object], missing_raw)
    assert reopened["status"] == "incomplete"
    assert set(records) == {"ct22_fp1", "ct27_fp1", "ct28_fp1", "ct33_fp1"}
    assert reopened["binding_fp1"] == assessment.binding_fingerprint.value
    assert "ct28_fresh_ct18_capability_check" in missing
    assert "derived_live_sqs_baselines_for_book_sensors" in missing
    assert "ct27_complete_control_rank_table" in missing
    assert reopened["page_fp1"]
    assert assessment.activation_authorized is False
    assert assessment.provider_ready is False


def test_lineage_rejects_page_from_another_venue(tmp_path: Path) -> None:
    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "admission-fixture.proto"
    proto.package = "admission_fixture"
    proto.syntax = "proto3"
    digest = _ok(descriptor_set_digest(descriptor_set.SerializeToString()))
    descriptor_path = tmp_path / "pinned-proto.pb"
    descriptor_path.write_bytes(descriptor_set.SerializeToString())
    deployment = fixture_deployment(tmp_path, descriptor_path, digest)
    assessment = _ok(assess_configured_runtime(deployment, qmx_root=tmp_path))

    foreign_venue = _ok(VenueId.try_create("foreign-venue"))
    page = _demo_page(foreign_venue)

    refused = persist_admission_evidence(EvidenceStore(tmp_path / "store"), assessment, page)

    assert is_refusal(refused)


def test_reader_rejects_rehashed_boolean_envelope_version(tmp_path: Path) -> None:
    store, reference = _persist_fixture_evidence(tmp_path)

    forged = _append_rehashed_envelope(
        store, reference, lambda body: body.__setitem__("format_version", True)
    )

    refused = read_admission_evidence(EvidenceStore(tmp_path / "store"), forged)

    assert is_refusal(refused)


def test_reader_recomputes_nested_page_identity_after_outer_rehash(tmp_path: Path) -> None:
    store, reference = _persist_fixture_evidence(tmp_path)

    forged = _append_rehashed_envelope(
        store,
        reference,
        lambda body: body.__setitem__(
            "page_fp1", _ok(fingerprint({"class": "foreign-page"})).value
        ),
    )

    refused = read_admission_evidence(EvidenceStore(tmp_path / "store"), forged)

    assert is_refusal(refused)


def _persist_fixture_evidence(
    tmp_path: Path,
    *,
    nonempty_templates: bool = False,
) -> tuple[EvidenceStore, AdmissionEvidenceRef]:
    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "admission-fixture.proto"
    proto.package = "admission_fixture"
    proto.syntax = "proto3"
    descriptor_bytes = descriptor_set.SerializeToString()
    digest = _ok(descriptor_set_digest(descriptor_bytes))
    descriptor_path = tmp_path / "pinned-proto.pb"
    descriptor_path.write_bytes(descriptor_bytes)
    deployment = fixture_deployment(
        tmp_path,
        descriptor_path,
        digest,
        nonempty_templates=nonempty_templates,
    )
    assessment = _ok(assess_configured_runtime(deployment, qmx_root=tmp_path))
    page = _demo_page(_ok(VenueId.try_create("fixture-venue")))
    store = EvidenceStore(tmp_path / "store")
    reference = _ok(persist_admission_evidence(store, assessment, page))
    return store, reference


def _append_rehashed_envelope(
    store: EvidenceStore,
    reference: AdmissionEvidenceRef,
    mutate: Callable[[dict[str, object]], None],
) -> AdmissionEvidenceRef:
    world_store = _ok(store.for_world(World.LIVE))
    rows = _ok(world_store.append_store.read_raw(reference.archive_fp1, for_world=World.LIVE))
    assert len(rows) == 1
    row = dict(cast(Mapping[str, object], rows[0]))
    parsed: object = json.loads(cast(str, row["body_json"]))
    assert isinstance(parsed, dict)
    body = cast(dict[str, object], parsed)
    mutate(body)
    body_bytes = _ok(canonical_bytes(body))
    body_fp = _ok(fingerprint(body))
    row["body_json"] = body_bytes.decode("utf-8")
    row["artifact_fp1"] = body_fp.value
    written = _ok(world_store.append_store.append_raw([row]))
    return AdmissionEvidenceRef(body_fp, written.fingerprint)


def test_nonempty_ct22_ct27_records_survive_ad32_physical_reopen(tmp_path: Path) -> None:
    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "admission-nonempty.proto"
    proto.package = "admission_nonempty"
    proto.syntax = "proto3"
    raw = descriptor_set.SerializeToString()
    digest = _ok(descriptor_set_digest(raw))
    descriptor_path = tmp_path / "pinned-proto.pb"
    descriptor_path.write_bytes(raw)
    deployment = fixture_deployment(
        tmp_path,
        descriptor_path,
        digest,
        nonempty_templates=True,
    )
    assessment = _ok(assess_configured_runtime(deployment, qmx_root=tmp_path))
    page = _demo_page(_ok(VenueId.try_create("fixture-venue")))
    store = EvidenceStore(tmp_path / "admission-evidence")

    written = _ok(persist_admission_evidence(store, assessment, page))
    reopened = _ok(read_admission_evidence(EvidenceStore(tmp_path / "admission-evidence"), written))

    assert reopened["status"] == "incomplete"
    rank = reopened["bms_control_rank_table"]
    assert isinstance(rank, Mapping)
    assert rank["status"] == "derived"
    assert assessment.book_definition.sections
    assert assessment.bms_definition.sections
    assert assessment.activation_authorized is False
    assert assessment.provider_ready is False


def test_reader_refuses_correctly_rehashed_malformed_ct27_section_identity(
    tmp_path: Path,
) -> None:
    store, reference = _persist_fixture_evidence(tmp_path, nonempty_templates=True)

    def make_nested_section_malformed(body: dict[str, object]) -> None:
        raw_records = body.get("registered_records")
        assert isinstance(raw_records, dict)
        records = cast(dict[str, object], raw_records)
        raw_record = records["ct27_fp1"]
        assert isinstance(raw_record, dict)
        record = cast(dict[str, object], raw_record)
        raw_record_body = record.get("body")
        assert isinstance(raw_record_body, dict)
        registered_body = cast(dict[str, object], raw_record_body)
        raw_sections = registered_body.get("sections")
        assert isinstance(raw_sections, dict)
        sections = cast(dict[str, object], raw_sections)
        raw_section = sections["control_rank_table"]
        assert isinstance(raw_section, dict)
        cast(dict[str, object], raw_section)["format_version"] = True
        stable_identity = {
            "class": "registration-record",
            "kind": record["kind"],
            "contract_format_version": record["contract_format_version"],
            "at_birth_parent_refs": record["at_birth_parent_refs"],
            "body": registered_body,
            "format_version": record["format_version"],
        }
        record["stable_id"] = _ok(fingerprint(stable_identity)).value
        identities = {
            name: cast(dict[str, object], item)["stable_id"] for name, item in records.items()
        }
        body["registry_as_of_fp1"] = _ok(
            fingerprint({"class": "qmn-configured-registry-as-of-v1", "records": identities})
        ).value

    forged = _append_rehashed_envelope(store, reference, make_nested_section_malformed)

    assert is_refusal(read_admission_evidence(EvidenceStore(tmp_path / "store"), forged))
