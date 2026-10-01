"""Operator-bound ATC transport over real CT-10/CT-13/CT-07 persistence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any, TypeVar, cast

from qmb.config.alternative import validate_alternative_run_config
from qmb.execution.alternative import AlternativeInterpreterRegistry
from qmb.execution.alternative_terminal import AlternativeTerminalStore
from qmb.host.operator_alternative import (
    OperatorAlternativeInputs,
    run_operator_alternative,
    validate_operator_alternative_result,
)
from qmb.host.qma_cli import QmaBacktestContext
from qmf.core import Fingerprint, Instant, Result, World, WriterId, fingerprint, is_ok, is_refusal
from qmf.data.journal_producer import JournalReader
from qmf.data.store import EvidenceStore
from qmf.registry import RegistryPersistence
from test_alternative_execution import (
    _config_payload,  # pyright: ignore[reportPrivateUsage]
    _journal,  # pyright: ignore[reportPrivateUsage]
    _registry,  # pyright: ignore[reportPrivateUsage]
    _source,  # pyright: ignore[reportPrivateUsage]
    _writer,  # pyright: ignore[reportPrivateUsage]
)

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(token: str) -> Fingerprint:
    return _ok(Fingerprint.try_create(f"fp1:sha256:{token * 64}"))


def test_operator_alternative_runs_reopens_and_validates_bound_result(tmp_path: Path) -> None:
    source = _source(tmp_path)
    assert source.split_fp1 is not None
    context = QmaBacktestContext(
        job_id="job-atc-1",
        attempt_id=1,
        experiment_spec_fp1=_fp("a"),
        evidence_ref=_fp("b"),
        split_manifest_fp1=source.split_fp1,
        environment_ref="env:local-replay",
        occupancy_key="run:atc-1",
        mints_ct32=False,
        operator_descriptor_fp1=_fp("d"),
    )
    config = _ok(validate_alternative_run_config(_config_payload()))
    registry: AlternativeInterpreterRegistry = _registry()
    journal, writer = _journal(tmp_path)
    registry_persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal_writer = _ok(WriterId.try_create("test-host", "qmb", "atc-terminal", "boot-1"))
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=terminal_writer)
    )
    lineage_writer = _ok(WriterId.try_create("test-host", "qmb", "atc-lineage", "boot-1"))
    inputs = OperatorAlternativeInputs(
        context=context,
        config=config,
        recorded_source=source,
        registry=registry,
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        expected_command_owner_epoch=18,
        runtime_descriptor_fp1=_fp("d"),
        registry_as_of=_ok(Instant.try_create(0)),
        registry_writer=_writer(),
        raw_store_root=tmp_path / "ct10-room",
        journal_root=tmp_path / "ct13-room",
        journal_writer=writer,
        journal_store=journal,
        terminal_store=terminal,
        registry_persistence=registry_persistence,
        lineage_writer=lineage_writer,
    )

    for mode in (True, 1):
        mode_context = replace(context, mints_ct32=cast("bool", mode))
        refused_mode = run_operator_alternative(replace(inputs, context=mode_context))
        assert is_refusal(refused_mode)
        assert (
            _ok(JournalReader(journal).read_checked(writer.stream_name, for_world=World.REPLAY))
            == []
        )
        assert _ok(terminal.read(journal_store=journal, registry=registry_persistence)) == ()

    malformed_context_fields: tuple[tuple[str, object], ...] = (
        ("experiment_spec_fp1", None),
        ("evidence_ref", Fingerprint("invalid")),
        ("split_manifest_fp1", None),
        ("job_id", []),
        ("attempt_id", True),
        ("occupancy_key", None),
        ("operator_descriptor_fp1", Fingerprint("invalid")),
    )
    for field, value in malformed_context_fields:
        malformed_context = replace(cast(Any, context), **{field: value})
        malformed_result = run_operator_alternative(replace(inputs, context=malformed_context))
        assert is_refusal(malformed_result), (field, malformed_result)
        assert (
            _ok(JournalReader(journal).read_checked(writer.stream_name, for_world=World.REPLAY))
            == []
        )
        assert _ok(terminal.read(journal_store=journal, registry=registry_persistence)) == ()

    assert is_refusal(validate_operator_alternative_result(None, inputs=inputs))
    assert (
        _ok(JournalReader(journal).read_checked(writer.stream_name, for_world=World.REPLAY)) == []
    )
    assert _ok(terminal.read(journal_store=journal, registry=registry_persistence)) == ()

    result = _ok(run_operator_alternative(inputs))
    validated = _ok(validate_operator_alternative_result(result.payload, inputs=inputs))
    assert validated.fingerprint == result.fingerprint
    reopened = _ok(validate_operator_alternative_result(None, inputs=inputs))
    assert _ok(fingerprint(reopened.payload)) == _ok(fingerprint(result.payload))
    assert result.payload["composition_class"] == "alternative"
    assert result.payload["source_fp1"] == source.fingerprint.value
    assert result.payload["split_fp1"] == source.split_fp1.value
    assert result.payload["terminal_artifact_fp1"]
    assert result.payload["journal_refs"]
    assert "ct32_fp1" not in result.payload
    binding = result.payload["operator_binding"]
    assert isinstance(binding, Mapping)
    binding_map = cast(Mapping[str, object], binding)
    assert binding_map["runtime_descriptor_fp1"] == inputs.runtime_descriptor_fp1.value
    assert binding_map["command_owner_epoch"] == inputs.expected_command_owner_epoch
    assert binding_map["trial_label_fp1"]
    artifacts = _ok(terminal.read(journal_store=journal, registry=registry_persistence))
    assert len(artifacts) == 1
    assert artifacts[0].fingerprint.value == result.payload["terminal_artifact_fp1"]
    events = _ok(JournalReader(journal).read_checked(writer.stream_name, for_world=World.REPLAY))
    assert len(events) == 2

    repeated = _ok(run_operator_alternative(inputs))
    assert repeated.fingerprint == result.fingerprint
    assert is_ok(validate_operator_alternative_result(None, inputs=inputs))
    assert (
        len(_ok(JournalReader(journal).read_checked(writer.stream_name, for_world=World.REPLAY)))
        == 2
    )


def test_operator_alternative_refuses_foreign_split_before_ct13_effects(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    assert source.split_fp1 is not None
    context = QmaBacktestContext(
        job_id="job-atc-1",
        attempt_id=1,
        experiment_spec_fp1=_fp("a"),
        evidence_ref=_fp("b"),
        split_manifest_fp1=_fp("c"),
        environment_ref="env:local-replay",
        occupancy_key="run:atc-1",
        mints_ct32=False,
        operator_descriptor_fp1=_fp("d"),
    )
    journal, writer = _journal(tmp_path)
    persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=_writer())
    )
    inputs = OperatorAlternativeInputs(
        context=context,
        config=_ok(validate_alternative_run_config(_config_payload())),
        recorded_source=source,
        registry=_registry(),
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        expected_command_owner_epoch=18,
        runtime_descriptor_fp1=_fp("d"),
        registry_as_of=_ok(Instant.try_create(0)),
        registry_writer=_writer(),
        raw_store_root=tmp_path / "ct10-room",
        journal_root=tmp_path / "ct13-room",
        journal_writer=writer,
        journal_store=journal,
        terminal_store=terminal,
        registry_persistence=persistence,
        lineage_writer=_writer(),
    )
    refused = run_operator_alternative(inputs)
    assert is_refusal(refused)
    assert (
        _ok(JournalReader(journal).read_checked(writer.stream_name, for_world=World.REPLAY)) == []
    )
    assert _ok(terminal.read(journal_store=journal, registry=persistence)) == ()


def test_operator_result_validator_rejects_book_or_context_substitution(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    assert source.split_fp1 is not None
    context = QmaBacktestContext(
        job_id="job-atc-1",
        attempt_id=1,
        experiment_spec_fp1=_fp("a"),
        evidence_ref=_fp("b"),
        split_manifest_fp1=source.split_fp1,
        environment_ref="env:local-replay",
        occupancy_key="run:atc-1",
        mints_ct32=False,
        operator_descriptor_fp1=_fp("d"),
    )
    journal, writer = _journal(tmp_path)
    persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=_writer())
    )
    inputs = OperatorAlternativeInputs(
        context=context,
        config=_ok(validate_alternative_run_config(_config_payload())),
        recorded_source=source,
        registry=_registry(),
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        expected_command_owner_epoch=18,
        runtime_descriptor_fp1=_fp("d"),
        registry_as_of=_ok(Instant.try_create(0)),
        registry_writer=_writer(),
        raw_store_root=tmp_path / "ct10-room",
        journal_root=tmp_path / "ct13-room",
        journal_writer=writer,
        journal_store=journal,
        terminal_store=terminal,
        registry_persistence=persistence,
        lineage_writer=_writer(),
    )
    result = _ok(run_operator_alternative(inputs))
    forged = dict(result.payload)
    forged["ct32_fp1"] = (
        "fp1:sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )
    assert is_refusal(validate_operator_alternative_result(forged, inputs=inputs))
    for key in ("source_fp1", "composition_fp1", "registry_fp1"):
        substituted = dict(result.payload)
        substituted[key] = _fp("e").value
        assert is_refusal(validate_operator_alternative_result(substituted, inputs=inputs))
    foreign_pair = dict(cast(Mapping[str, object], result.payload["policy_pair_identity"]))
    foreign_pair["policy_pair_id"] = "foreign-pair"
    substituted_pair = dict(result.payload)
    substituted_pair["policy_pair_identity"] = foreign_pair
    assert is_refusal(validate_operator_alternative_result(substituted_pair, inputs=inputs))

    changed_state_inputs = replace(
        inputs,
        initial_accounting_state={"cash_units": 2_000_001, "position_units": 0},
    )
    forged_binding = dict(cast(Mapping[str, object], result.payload["operator_binding"]))
    forged_binding["initial_accounting_state_fp1"] = _ok(
        fingerprint(changed_state_inputs.initial_accounting_state)
    ).value
    forged_state = dict(result.payload)
    forged_state["operator_binding"] = forged_binding
    forged_state["operator_binding_fp1"] = _ok(fingerprint(forged_binding)).value
    assert is_refusal(validate_operator_alternative_result(forged_state, inputs=inputs))
    assert is_refusal(
        validate_operator_alternative_result(result.payload, inputs=changed_state_inputs)
    )
    foreign_context = QmaBacktestContext(
        job_id="job-atc-2",
        attempt_id=1,
        experiment_spec_fp1=context.experiment_spec_fp1,
        evidence_ref=context.evidence_ref,
        split_manifest_fp1=context.split_manifest_fp1,
        environment_ref=context.environment_ref,
        occupancy_key=context.occupancy_key,
        mints_ct32=False,
    )
    assert is_refusal(
        validate_operator_alternative_result(
            result.payload,
            inputs=replace(inputs, context=foreign_context),
        )
    )
    assert is_refusal(
        validate_operator_alternative_result(
            result.payload,
            inputs=replace(inputs, runtime_descriptor_fp1=_fp("e")),
        )
    )
