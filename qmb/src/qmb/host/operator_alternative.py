"""Trusted operator adapter for the Alternative Trading Composition door.

This module accepts only values already materialized by the QMB operator binding.
It executes the registered PolicyPair interpreter, writes the CT-13 decision
chain and CT-07 terminal lineage, then reopens the terminal JSONL before it
returns a transport payload. The Alternative result is deliberately independent
of the Book/CT-32 performance contract.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast

from qmf.core import Fingerprint, Instant, Ok, Result, World, WriterId, fingerprint, is_refusal
from qmf.data.journal_producer import JournalReader, JournalWriter
from qmf.data.store import JournalStore
from qmf.registry import RegistryPersistence

from qmb._refuse import invalid, policy
from qmb.config.alternative import AlternativeRunConfig, validate_alternative_run_config
from qmb.execution.alternative import (
    AlternativeInterpreterRegistry,
    AlternativeRunReceipt,
    execute_alternative_run,
)
from qmb.execution.alternative_terminal import (
    AlternativeTerminalArtifact,
    AlternativeTerminalStore,
)
from qmb.host.operator_occurrence import (
    OperatorOccurrenceIdentity,
    read_operator_occurrence,
    record_operator_occurrence,
)
from qmb.host.qma_cli import QmaBacktestContext, validate_qma_backtest_context
from qmb.host.replay import RecordedReplaySource
from qmb.optimize.sampler import validate_trial_label

__all__ = [
    "OPERATOR_ALTERNATIVE_RESULT_CLASS",
    "OperatorAlternativeInputs",
    "OperatorAlternativeResult",
    "run_operator_alternative",
    "validate_operator_alternative_result",
]

OPERATOR_ALTERNATIVE_RESULT_CLASS = "qmb-alternative-result-v1"


def _writer_body(writer: WriterId) -> dict[str, object]:
    return {
        "boot_epoch_id": writer.boot_epoch_id,
        "machine": writer.machine,
        "role": writer.role,
        "stream": writer.stream,
    }


@dataclass(frozen=True, slots=True)
class OperatorAlternativeInputs:
    """Resolved values supplied by the trusted operator runtime binding.

    Paths and persistence ports are operator-selected. The QMA envelope carries
    only registered CT-47 identifiers and is never allowed to choose these roots.
    """

    context: QmaBacktestContext
    config: AlternativeRunConfig
    recorded_source: RecordedReplaySource
    registry: AlternativeInterpreterRegistry
    initial_accounting_state: Mapping[str, object]
    expected_command_owner_epoch: int
    runtime_descriptor_fp1: Fingerprint
    registry_as_of: Instant
    registry_writer: WriterId
    raw_store_root: Path
    journal_root: Path
    journal_writer: JournalWriter
    journal_store: JournalStore
    terminal_store: AlternativeTerminalStore
    registry_persistence: RegistryPersistence
    lineage_writer: WriterId
    trial_label: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class OperatorAlternativeResult:
    """Verified terminal result suitable for the isolated QMB/QMN transport."""

    payload: Mapping[str, object]
    fingerprint: Fingerprint

    def identity(self) -> dict[str, object]:
        return dict(self.payload)


def run_operator_alternative(
    inputs: object,
) -> Result[OperatorAlternativeResult]:
    """Run one operator-resolved Alternative composition and verify its terminal.

    The function does not accept a builder callback, arbitrary evaluator, Book
    objects, or a caller-selected terminal root. Policy execution is delegated to
    the registered interpreter through ``execute_alternative_run``.
    """
    if not isinstance(inputs, OperatorAlternativeInputs):
        return invalid("operator_inputs", "ATC operator execution consumes typed resolved inputs")
    checked = _validate_inputs(inputs)
    if is_refusal(checked):
        return checked

    existing = _matching_terminal_artifacts(inputs)
    if is_refusal(existing):
        return existing
    if existing.value:
        if len(existing.value) != 1:
            return policy("terminal_artifact", "one matching prior terminal is resumable")
        return validate_operator_alternative_result(None, inputs=inputs)

    receipt = execute_alternative_run(
        inputs.config,
        inputs.recorded_source,
        inputs.registry,
        initial_accounting_state=inputs.initial_accounting_state,
        expected_command_owner_epoch=inputs.expected_command_owner_epoch,
        journal_writer=inputs.journal_writer,
        journal_store=inputs.journal_store,
        trial_label=inputs.trial_label,
    )
    if is_refusal(receipt):
        return receipt

    appended = inputs.terminal_store.append(
        receipt.value,
        journal_store=inputs.journal_store,
        registry=inputs.registry_persistence,
        lineage_writer=inputs.lineage_writer,
        trial_label=inputs.trial_label,
    )
    if is_refusal(appended):
        return appended

    reopened = inputs.terminal_store.read(
        journal_store=inputs.journal_store,
        registry=inputs.registry_persistence,
    )
    if is_refusal(reopened):
        return reopened
    matches = tuple(
        artifact
        for artifact in reopened.value
        if artifact.run_receipt_fingerprint == receipt.value.fingerprint
    )
    if len(matches) != 1 or matches[0].fingerprint != appended.value.fingerprint:
        return policy(
            "terminal_readback",
            "the exact ATC terminal artifact is present once after durable readback",
        )
    artifact = matches[0]
    verified = _verify_artifact(inputs, receipt.value, artifact)
    if is_refusal(verified):
        return verified

    binding_identity = _binding_identity(inputs, receipt.value, artifact)
    binding_fp = fingerprint(binding_identity)
    if is_refusal(binding_fp):
        return binding_fp
    occurrence = _occurrence_identity(inputs, artifact, binding_fp.value)
    if is_refusal(occurrence):
        return occurrence
    recorded_occurrence = record_operator_occurrence(
        identity=occurrence.value,
        journal_writer=inputs.journal_writer,
        journal_store=inputs.journal_store,
        at=occurrence.value.at,
    )
    if is_refusal(recorded_occurrence):
        return recorded_occurrence
    body: dict[str, object] = {
        "class": OPERATOR_ALTERNATIVE_RESULT_CLASS,
        "format_version": 1,
        "job_id": inputs.context.job_id,
        "attempt_id": inputs.context.attempt_id,
        "experiment_spec_fp1": inputs.context.experiment_spec_fp1.value,
        "evidence_ref": inputs.context.evidence_ref.value,
        "split_manifest_fp1": inputs.context.split_manifest_fp1.value,
        "operator_binding_fp1": binding_fp.value.value,
        "operator_binding": binding_identity,
        "composition_class": "alternative",
        "composition_fp1": receipt.value.config.composition_fp.value,
        "policy_pair_identity": receipt.value.config.policy_pair.identity(),
        "source_fp1": receipt.value.source_fingerprint.value,
        "split_fp1": receipt.value.split_fingerprint.value,
        "split_role": receipt.value.split_role.value,
        "registry_fp1": receipt.value.registry_fingerprint.value,
        "interpreter_registration_fp1": receipt.value.interpreter_registration.fingerprint.value,
        "run_receipt_fp1": receipt.value.fingerprint.value,
        "terminal_artifact_fp1": artifact.fingerprint.value,
        "journal_writer": _writer_body(receipt.value.journal_writer),
        "journal_stream": receipt.value.journal_stream,
        "journal_refs": [item.identity() for item in receipt.value.journal_references],
        "final_measures": [item.fp1_identity() for item in receipt.value.final_measures],
        "final_accounting_state_fp1": receipt.value.final_accounting_state_fingerprint.value,
    }
    stamped = fingerprint(body)
    if is_refusal(stamped):
        return stamped
    result = OperatorAlternativeResult(MappingProxyType(body), stamped.value)
    return validate_operator_alternative_result(result.payload, inputs=inputs)


def validate_operator_alternative_result(
    value: object,
    *,
    inputs: object,
) -> Result[OperatorAlternativeResult]:
    """Validate transport fields against trusted inputs and reopened terminal storage.

    ``inputs`` must be the same operator-resolved object used for execution; a
    result cannot make its own descriptor, terminal root, or policy identity
    trusted by hashing those values inside the child payload.
    """
    if not isinstance(inputs, OperatorAlternativeInputs):
        return invalid("operator_inputs", "result validation uses the resolved operator binding")
    checked_inputs = _validate_inputs(inputs)
    if is_refusal(checked_inputs):
        return checked_inputs
    if value is None:
        materialized = _materialize_reopened_result(inputs)
        if is_refusal(materialized):
            return materialized
        value = materialized.value
    if not isinstance(value, Mapping):
        return invalid("alternative_result", "ATC child result is one mapping")
    body = cast(Mapping[str, object], value)
    required = {
        "class",
        "format_version",
        "job_id",
        "attempt_id",
        "experiment_spec_fp1",
        "evidence_ref",
        "split_manifest_fp1",
        "operator_binding_fp1",
        "operator_binding",
        "composition_class",
        "composition_fp1",
        "policy_pair_identity",
        "source_fp1",
        "split_fp1",
        "split_role",
        "registry_fp1",
        "interpreter_registration_fp1",
        "run_receipt_fp1",
        "terminal_artifact_fp1",
        "journal_writer",
        "journal_stream",
        "journal_refs",
        "final_measures",
        "final_accounting_state_fp1",
    }
    if set(body) != required:
        return invalid(
            "alternative_result",
            "ATC child result contains the exact v1 fields",
            missing=sorted(required.difference(body)),
            extra=sorted(set(body).difference(required)),
        )
    if body.get("class") != OPERATOR_ALTERNATIVE_RESULT_CLASS:
        return invalid("alternative_result", "ATC child result has its registered class")
    if type(body.get("format_version")) is not int or body.get("format_version") != 1:
        return invalid("alternative_result", "ATC child result uses format version 1")
    if body.get("composition_class") != "alternative":
        return policy("composition_class", "result identifies the Alternative composition")
    for key, expected in (
        ("job_id", inputs.context.job_id),
        ("attempt_id", inputs.context.attempt_id),
        ("experiment_spec_fp1", inputs.context.experiment_spec_fp1.value),
        ("evidence_ref", inputs.context.evidence_ref.value),
        ("split_manifest_fp1", inputs.context.split_manifest_fp1.value),
    ):
        actual = body.get(key)
        if type(actual) is not type(expected) or actual != expected:
            return policy(key, "ATC result matches the exact delegated QMA identifiers")
    forbidden = {"ct32_fp1", "book_fp1", "bms_fp1", "bot_fp1", "requested_r", "r_multiple"}
    if forbidden.intersection(body):
        return policy("composition_class", "ATC result contains no Book or CT-32/R fields")
    binding = body.get("operator_binding")
    if not isinstance(binding, Mapping):
        return invalid("operator_binding", "result echoes its operator-resolved binding identity")
    terminal = inputs.terminal_store.read(
        journal_store=inputs.journal_store,
        registry=inputs.registry_persistence,
    )
    if is_refusal(terminal):
        return terminal
    terminal_fp = body.get("terminal_artifact_fp1")
    matched = tuple(item for item in terminal.value if item.fingerprint.value == terminal_fp)
    if len(matched) != 1:
        return policy("terminal_artifact", "result names one actual reopened terminal artifact")
    artifact = matched[0]
    registration = inputs.registry.resolve(inputs.config)
    if is_refusal(registration):
        return registration
    expected_trial = _validated_trial_label(inputs.trial_label)
    if is_refusal(expected_trial):
        return expected_trial
    split_role = inputs.recorded_source.split_role
    if split_role is None:
        return policy("split_role", "trusted replay source includes its exact CT-12 role")
    expected_initial_state_fp = _terminal_accounting_state_fp1(inputs.initial_accounting_state)
    if is_refusal(expected_initial_state_fp):
        return expected_initial_state_fp
    expected_artifact_values: tuple[tuple[str, object], ...] = (
        ("composition_fp1", inputs.config.composition_fp.value),
        ("policy_pair_identity", inputs.config.policy_pair.identity()),
        ("source_fp1", inputs.recorded_source.fingerprint.value),
        ("split_fp1", inputs.context.split_manifest_fp1.value),
        ("split_role", split_role.value),
        ("registry_fp1", inputs.registry.fingerprint.value),
        ("interpreter_registration_fp1", registration.value.fingerprint.value),
        ("initial_accounting_state_fp1", expected_initial_state_fp.value.value),
        ("journal_writer", _writer_body(inputs.journal_writer.writer)),
        ("journal_stream", inputs.journal_writer.stream_name),
        ("lineage_writer", _writer_body(inputs.lineage_writer)),
    )
    for key, expected in expected_artifact_values:
        if not _same_canonical(artifact.body.get(key), expected):
            return policy(
                key,
                "reopened terminal binds the trusted source, policy, state, and writers",
            )
    if expected_trial.value is None:
        if "trial_label" in artifact.body:
            return policy("trial_label", "terminal presence matches the trusted trial label")
    elif not _same_canonical(artifact.body.get("trial_label"), expected_trial.value):
        return policy("trial_label", "terminal label matches the trusted trial label")

    events = JournalReader(inputs.journal_store).read_checked(
        inputs.journal_writer.stream_name,
        for_world=World.REPLAY,
    )
    if is_refusal(events):
        return events
    refs = artifact.body.get("journal_refs")
    if not isinstance(refs, (tuple, list)):
        return policy("journal_refs", "reopened terminal carries its checked CT-13 references")
    for ref_value in cast("Sequence[object]", refs):
        if not isinstance(ref_value, Mapping):
            return policy("journal_refs", "reopened terminal references are typed mappings")
        ref = cast("Mapping[str, object]", ref_value)
        sequence = ref.get("sequence")
        event_fp = ref.get("event_fp1")
        if type(sequence) is not int or not isinstance(event_fp, str):
            return policy("journal_refs", "terminal references carry typed sequence and fp1")
        matching = tuple(
            event
            for event in events.value
            if event.writer == inputs.journal_writer.writer
            and event.sequence == sequence
            and event.fingerprint.value == event_fp
        )
        if len(matching) != 1 or matching[0].payload.get("command_owner_epoch") != (
            inputs.expected_command_owner_epoch
        ):
            return policy(
                "command_owner_epoch",
                "durable CT-13 decision chain belongs to the trusted command epoch",
            )

    expected_result_values: tuple[tuple[str, object], ...] = (
        ("composition_fp1", artifact.body.get("composition_fp1")),
        ("policy_pair_identity", artifact.body.get("policy_pair_identity")),
        ("source_fp1", artifact.body.get("source_fp1")),
        ("split_fp1", artifact.body.get("split_fp1")),
        ("split_role", artifact.body.get("split_role")),
        ("registry_fp1", artifact.body.get("registry_fp1")),
        (
            "interpreter_registration_fp1",
            artifact.body.get("interpreter_registration_fp1"),
        ),
        ("journal_writer", artifact.body.get("journal_writer")),
        ("journal_stream", artifact.body.get("journal_stream")),
        ("journal_refs", artifact.body.get("journal_refs")),
        ("final_measures", artifact.body.get("final_measures")),
        ("final_accounting_state_fp1", artifact.body.get("final_accounting_state_fp1")),
    )
    if any(
        not _same_canonical(body.get(key), expected) for key, expected in expected_result_values
    ):
        return policy(
            "alternative_result",
            "all duplicated execution identity fields match the reopened terminal",
        )
    if artifact.run_receipt_fingerprint.value != body.get("run_receipt_fp1"):
        return policy("terminal_artifact", "result fields reproduce the durable terminal body")
    expected_binding = _binding_identity_from_inputs(inputs, artifact)
    if is_refusal(expected_binding):
        return expected_binding
    if not _same_canonical(cast(Mapping[str, object], binding), expected_binding.value):
        return policy("operator_binding", "result binding equals the resolved operator inputs")
    stamped_binding = fingerprint(cast(Mapping[str, object], binding))
    if is_refusal(stamped_binding) or stamped_binding.value.value != body.get(
        "operator_binding_fp1"
    ):
        return policy("operator_binding_fp1", "operator binding fp1 matches its canonical body")
    occurrence = _occurrence_identity(inputs, artifact, stamped_binding.value)
    if is_refusal(occurrence):
        return occurrence
    occurrence_readback = read_operator_occurrence(
        identity=occurrence.value,
        journal_reader=JournalReader(inputs.journal_store),
    )
    if is_refusal(occurrence_readback):
        return occurrence_readback
    stamped = fingerprint(dict(body))
    if is_refusal(stamped):
        return stamped
    return Ok(OperatorAlternativeResult(MappingProxyType(dict(body)), stamped.value))


def _validate_inputs(inputs: OperatorAlternativeInputs) -> Result[None]:
    validated_context = validate_qma_backtest_context(inputs.context)
    if is_refusal(validated_context):
        return validated_context
    context = validated_context.value
    if type(context.mints_ct32) is not bool:
        return invalid("mints_ct32", "the composition discriminator is a strict boolean")
    if context.mints_ct32 is not False:
        return policy(
            "mints_ct32",
            "Alternative execution requires the trusted QMA descriptor to select non-CT-32 mode",
        )
    config = validate_alternative_run_config(inputs.config)
    if is_refusal(config):
        return config
    if config.value.fingerprint != inputs.config.fingerprint:
        return policy("config", "resolved ATC config matches its canonical fingerprint")
    source = inputs.recorded_source
    if type(source) is not RecordedReplaySource or source.world is not World.REPLAY:
        return invalid("recorded_source", "ATC requires a materialized replay-world CT-10 source")
    source_fp = fingerprint(source.fp1_identity())
    if is_refusal(source_fp) or source_fp.value != source.fingerprint:
        return policy("recorded_source", "CT-10 source reproduces its exact content identity")
    if source.split_fp1 != inputs.context.split_manifest_fp1 or source.split_role is None:
        return policy("split_manifest_fp1", "CT-10 source is bound to the delegated CT-12 split")
    registry = inputs.registry
    if type(registry) is not AlternativeInterpreterRegistry:
        return invalid("registry", "ATC uses the canonical registered interpreter set")
    canonical_registry = AlternativeInterpreterRegistry.try_create(
        tuple(registry.registrations.values())
    )
    if is_refusal(canonical_registry):
        return canonical_registry
    if canonical_registry.value.fingerprint != registry.fingerprint:
        return policy("registry", "interpreter registry fp1 matches its registered policies")
    registration = canonical_registry.value.resolve(config.value)
    if is_refusal(registration):
        return registration
    if (
        type(inputs.expected_command_owner_epoch) is not int
        or inputs.expected_command_owner_epoch != config.value.command.command_owner_epoch
    ):
        return policy("command_owner_epoch", "host epoch equals the admitted ATC command epoch")
    if type(inputs.runtime_descriptor_fp1) is not Fingerprint:
        return invalid(
            "runtime_descriptor_fp1", "ATC uses the verified operator descriptor fingerprint"
        )
    descriptor_fp = Fingerprint.try_create(inputs.runtime_descriptor_fp1.value)
    if (
        is_refusal(descriptor_fp)
        or descriptor_fp.value != inputs.runtime_descriptor_fp1
        or context.operator_descriptor_fp1 != descriptor_fp.value
    ):
        return policy(
            "runtime_descriptor_fp1",
            "decoded QMA context and operator inputs pin the same valid descriptor",
        )
    if type(inputs.registry_as_of) is not Instant or type(inputs.registry_writer) is not WriterId:
        return invalid("registry_binding", "ATC pins typed registry as-of and writer identity")
    if (
        not isinstance(
            inputs.raw_store_root,
            Path,  # pyright: ignore[reportUnnecessaryIsInstance]
        )
        or not inputs.raw_store_root.is_absolute()
        or not isinstance(
            inputs.journal_root,
            Path,  # pyright: ignore[reportUnnecessaryIsInstance]
        )
        or not inputs.journal_root.is_absolute()
    ):
        return invalid("runtime_roots", "ATC source and journal roots are absolute operator paths")
    if (
        type(inputs.journal_writer) is not JournalWriter
        or type(inputs.journal_store) is not JournalStore
    ):
        return invalid("journal", "ATC receives the operator-bound CT-13 writer and room")
    if (
        inputs.journal_writer.world is not World.REPLAY
        or inputs.journal_store.world is not World.REPLAY
        or inputs.journal_writer.writer.stream != inputs.journal_writer.stream_name
    ):
        return policy("journal", "ATC decision writer and room are replay-world and stream-bound")
    if type(inputs.terminal_store) is not AlternativeTerminalStore:
        return invalid("terminal_store", "ATC receives its operator-bound durable terminal store")
    if type(inputs.registry_persistence) is not RegistryPersistence:
        return invalid(
            "registry_persistence", "ATC terminal lineage uses canonical CT-07 persistence"
        )
    if type(inputs.lineage_writer) is not WriterId:
        return invalid("lineage_writer", "ATC terminal Pair edge uses the operator WriterId")
    if not isinstance(inputs.initial_accounting_state, Mapping):  # pyright: ignore[reportUnnecessaryIsInstance]
        return invalid("initial_accounting_state", "ATC starts from explicit persisted state")
    state_fp = fingerprint(inputs.initial_accounting_state)
    if is_refusal(state_fp):
        return state_fp
    if inputs.trial_label is not None and not isinstance(
        inputs.trial_label,
        Mapping,  # pyright: ignore[reportUnnecessaryIsInstance]
    ):
        return invalid("trial_label", "ATC study trial labels are validated mappings")
    trial_fp = fingerprint(
        {
            "class": "qmb-alternative-trial-label-v1",
            "present": inputs.trial_label is not None,
            "label": {} if inputs.trial_label is None else inputs.trial_label,
        }
    )
    if is_refusal(trial_fp):
        return trial_fp
    return Ok(None)


def _materialize_reopened_result(
    inputs: OperatorAlternativeInputs,
) -> Result[Mapping[str, object]]:
    """Build a result envelope only from one trusted-input-matching durable terminal."""
    matches = _matching_terminal_artifacts(inputs)
    if is_refusal(matches):
        return matches
    if len(matches.value) != 1:
        return policy(
            "terminal_artifact",
            "verify-only recovery finds exactly one terminal matching the trusted runtime inputs",
            matches=len(matches.value),
        )
    artifact = matches.value[0]
    binding = _binding_identity_from_inputs(inputs, artifact)
    if is_refusal(binding):
        return binding
    binding_fp = fingerprint(binding.value)
    if is_refusal(binding_fp):
        return binding_fp
    body: dict[str, object] = {
        "class": OPERATOR_ALTERNATIVE_RESULT_CLASS,
        "format_version": 1,
        "job_id": inputs.context.job_id,
        "attempt_id": inputs.context.attempt_id,
        "experiment_spec_fp1": inputs.context.experiment_spec_fp1.value,
        "evidence_ref": inputs.context.evidence_ref.value,
        "split_manifest_fp1": inputs.context.split_manifest_fp1.value,
        "operator_binding_fp1": binding_fp.value.value,
        "operator_binding": dict(binding.value),
        "composition_class": "alternative",
        "composition_fp1": artifact.body.get("composition_fp1"),
        "policy_pair_identity": artifact.body.get("policy_pair_identity"),
        "source_fp1": artifact.body.get("source_fp1"),
        "split_fp1": artifact.body.get("split_fp1"),
        "split_role": artifact.body.get("split_role"),
        "registry_fp1": artifact.body.get("registry_fp1"),
        "interpreter_registration_fp1": artifact.body.get("interpreter_registration_fp1"),
        "run_receipt_fp1": artifact.body.get("run_receipt_fp1"),
        "terminal_artifact_fp1": artifact.fingerprint.value,
        "journal_writer": artifact.body.get("journal_writer"),
        "journal_stream": artifact.body.get("journal_stream"),
        "journal_refs": artifact.body.get("journal_refs"),
        "final_measures": artifact.body.get("final_measures"),
        "final_accounting_state_fp1": artifact.body.get("final_accounting_state_fp1"),
    }
    return Ok(MappingProxyType(body))


def _matching_terminal_artifacts(
    inputs: OperatorAlternativeInputs,
) -> Result[tuple[AlternativeTerminalArtifact, ...]]:
    terminal = inputs.terminal_store.read(
        journal_store=inputs.journal_store,
        registry=inputs.registry_persistence,
    )
    if is_refusal(terminal):
        return terminal
    registration = inputs.registry.resolve(inputs.config)
    if is_refusal(registration):
        return registration
    split_fp = inputs.recorded_source.split_fp1
    split_role = inputs.recorded_source.split_role
    if split_fp is None or split_role is None:
        return policy("split", "trusted replay source includes its CT-12 split")
    initial_state_fp = _terminal_accounting_state_fp1(inputs.initial_accounting_state)
    if is_refusal(initial_state_fp):
        return initial_state_fp
    trial = _validated_trial_label(inputs.trial_label)
    if is_refusal(trial):
        return trial
    matches: list[AlternativeTerminalArtifact] = []
    for artifact in terminal.value:
        expected: tuple[tuple[str, object], ...] = (
            ("composition_class", "alternative"),
            ("composition_fp1", inputs.config.composition_fp.value),
            ("policy_pair_identity", inputs.config.policy_pair.identity()),
            ("source_fp1", inputs.recorded_source.fingerprint.value),
            ("split_fp1", split_fp.value),
            ("split_role", split_role.value),
            ("registry_fp1", inputs.registry.fingerprint.value),
            ("interpreter_registration_fp1", registration.value.fingerprint.value),
            ("initial_accounting_state_fp1", initial_state_fp.value.value),
            ("journal_writer", _writer_body(inputs.journal_writer.writer)),
            ("journal_stream", inputs.journal_writer.stream_name),
            ("lineage_writer", _writer_body(inputs.lineage_writer)),
        )
        if any(
            not _same_canonical(artifact.body.get(key), expected_value)
            for key, expected_value in expected
        ):
            continue
        if trial.value is None:
            if "trial_label" in artifact.body:
                continue
        elif not _same_canonical(artifact.body.get("trial_label"), trial.value):
            continue
        matches.append(artifact)
    return Ok(tuple(matches))


def _occurrence_identity(
    inputs: OperatorAlternativeInputs,
    artifact: AlternativeTerminalArtifact,
    operator_binding_fp1: Fingerprint,
) -> Result[OperatorOccurrenceIdentity]:
    refs = artifact.body.get("journal_refs")
    if isinstance(refs, (tuple, list)) and refs:
        last_value: object = cast(Sequence[object], refs)[-1]
        if not isinstance(last_value, Mapping):
            return policy("journal_refs", "terminal occurrence has a typed final CT-13 frontier")
        last = cast(Mapping[str, object], last_value)
        frontier = last.get("frontier_ns")
        if type(frontier) is not int:
            return policy("journal_refs", "terminal occurrence has a typed final CT-13 frontier")
        at = Instant.try_create(frontier)
        if is_refusal(at):
            return at
        occurrence_at = at.value
    else:
        if not inputs.recorded_source.slices:
            return policy("recorded_source", "empty-source terminal has a pinned occurrence time")
        observations = inputs.recorded_source.slices[-1].observations
        if not observations:
            return policy("recorded_source", "terminal source slice has a pinned occurrence time")
        occurrence_at = observations[-1].instant
    return OperatorOccurrenceIdentity.try_create(
        context=inputs.context,
        composition_class="alternative",
        runtime_descriptor_fp1=inputs.runtime_descriptor_fp1,
        operator_binding_fp1=operator_binding_fp1,
        terminal_fp1=artifact.fingerprint,
        domain_result_fp1=artifact.run_receipt_fingerprint,
        at=occurrence_at,
        terminal_root=inputs.terminal_store.root,
        journal_root=inputs.journal_root,
        terminal_writer=inputs.terminal_store.writer,
        journal_writer=inputs.journal_writer.writer,
        journal_stream=inputs.journal_writer.stream_name,
        command_owner_epoch=inputs.expected_command_owner_epoch,
    )


def _verify_artifact(
    inputs: OperatorAlternativeInputs,
    receipt: AlternativeRunReceipt,
    artifact: AlternativeTerminalArtifact,
) -> Result[None]:
    if artifact.run_receipt_fingerprint != receipt.fingerprint:
        return policy("terminal_artifact", "terminal artifact cites the exact CT-13 run receipt")
    expected = {
        "composition_fp1": receipt.config.composition_fp.value,
        "source_fp1": receipt.source_fingerprint.value,
        "split_fp1": inputs.context.split_manifest_fp1.value,
        "registry_fp1": receipt.registry_fingerprint.value,
        "final_accounting_state_fp1": receipt.final_accounting_state_fingerprint.value,
    }
    for key, value in expected.items():
        if artifact.body.get(key) != value:
            return policy(key, "reopened ATC terminal preserves resolved execution identity")
    pair = artifact.body.get("policy_pair_identity")
    if not isinstance(pair, Mapping) or not _same_canonical(
        cast(Mapping[str, object], pair), receipt.config.policy_pair.identity()
    ):
        return policy("policy_pair_identity", "terminal result preserves exact PolicyPair identity")
    return Ok(None)


def _binding_identity(
    inputs: OperatorAlternativeInputs,
    receipt: AlternativeRunReceipt,
    artifact: AlternativeTerminalArtifact,
) -> Mapping[str, object]:
    body: dict[str, object] = {
        "class": "qmb-operator-alternative-binding-v1",
        "format_version": 1,
        "experiment_spec_fp1": inputs.context.experiment_spec_fp1.value,
        "evidence_ref": inputs.context.evidence_ref.value,
        "split_manifest_fp1": inputs.context.split_manifest_fp1.value,
        "runtime_descriptor_fp1": inputs.runtime_descriptor_fp1.value,
        "initial_accounting_state_fp1": _accounting_state_fp1(inputs.initial_accounting_state),
        "command_owner_epoch": inputs.expected_command_owner_epoch,
        "trial_label_fp1": _trial_label_fp1(inputs.trial_label),
        "registry_as_of_ns": inputs.registry_as_of.value_ns,
        "registry_writer": _writer_body(inputs.registry_writer),
        "composition_fp1": receipt.config.composition_fp.value,
        "policy_pair_identity": receipt.config.policy_pair.identity(),
        "source_fp1": receipt.source_fingerprint.value,
        "split_fp1": receipt.split_fingerprint.value,
        "split_role": receipt.split_role.value,
        "registry_fp1": receipt.registry_fingerprint.value,
        "interpreter_registration_fp1": receipt.interpreter_registration.fingerprint.value,
        "journal_writer": _writer_body(receipt.journal_writer),
        "journal_stream": receipt.journal_stream,
        "terminal_root": str(inputs.terminal_store.root.resolve()),
        "terminal_artifact_fp1": artifact.fingerprint.value,
        "lineage_writer": _writer_body(inputs.lineage_writer),
    }
    return MappingProxyType(body)


def _binding_identity_from_inputs(
    inputs: OperatorAlternativeInputs,
    artifact: AlternativeTerminalArtifact,
) -> Result[Mapping[str, object]]:
    """Reconstruct the expected binding from inputs, not the echoed payload."""
    split_fp = inputs.recorded_source.split_fp1
    split_role = inputs.recorded_source.split_role
    if split_fp is None or split_role is None:
        return policy("split", "operator binding requires the exact materialized CT-12 split")
    registration = inputs.registry.resolve(inputs.config)
    if is_refusal(registration):
        return registration
    body: dict[str, object] = {
        "class": "qmb-operator-alternative-binding-v1",
        "format_version": 1,
        "experiment_spec_fp1": inputs.context.experiment_spec_fp1.value,
        "evidence_ref": inputs.context.evidence_ref.value,
        "split_manifest_fp1": inputs.context.split_manifest_fp1.value,
        "runtime_descriptor_fp1": inputs.runtime_descriptor_fp1.value,
        "initial_accounting_state_fp1": _accounting_state_fp1(inputs.initial_accounting_state),
        "command_owner_epoch": inputs.expected_command_owner_epoch,
        "trial_label_fp1": _trial_label_fp1(inputs.trial_label),
        "registry_as_of_ns": inputs.registry_as_of.value_ns,
        "registry_writer": _writer_body(inputs.registry_writer),
        "composition_fp1": inputs.config.composition_fp.value,
        "policy_pair_identity": inputs.config.policy_pair.identity(),
        "source_fp1": inputs.recorded_source.fingerprint.value,
        "split_fp1": split_fp.value,
        "split_role": split_role.value,
        "registry_fp1": inputs.registry.fingerprint.value,
        "interpreter_registration_fp1": registration.value.fingerprint.value,
        "journal_writer": _writer_body(inputs.journal_writer.writer),
        "journal_stream": inputs.journal_writer.stream_name,
        "terminal_root": str(inputs.terminal_store.root.resolve()),
        "terminal_artifact_fp1": artifact.fingerprint.value,
        "lineage_writer": _writer_body(inputs.lineage_writer),
    }
    return Ok(MappingProxyType(body))


def _same_canonical(left: object, right: object) -> bool:
    left_fp = fingerprint(left)
    right_fp = fingerprint(right)
    return not is_refusal(left_fp) and not is_refusal(right_fp) and left_fp.value == right_fp.value


def _accounting_state_fp1(state: Mapping[str, object]) -> str:
    stamped = fingerprint(state)
    return "" if is_refusal(stamped) else stamped.value.value


def _terminal_accounting_state_fp1(state: Mapping[str, object]) -> Result[Fingerprint]:
    """Fingerprint a trusted seed using the same typed state identity as CT-13."""
    return fingerprint({"class": "qmb-atc-accounting-state-v1", "state": dict(state)})


def _validated_trial_label(
    label: Mapping[str, object] | None,
) -> Result[Mapping[str, object] | None]:
    if label is None:
        return Ok(None)
    checked = validate_trial_label(label)
    if is_refusal(checked):
        return checked
    return Ok(checked.value)


def _trial_label_fp1(label: Mapping[str, object] | None) -> str:
    stamped = fingerprint(
        {
            "class": "qmb-alternative-trial-label-v1",
            "present": label is not None,
            "label": {} if label is None else label,
        }
    )
    return "" if is_refusal(stamped) else stamped.value.value
