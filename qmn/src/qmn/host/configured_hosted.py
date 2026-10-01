"""Supervisor handoff from checked deployment assessment to hosted root."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from qmf.core import Fingerprint, Ok, Result, World, fingerprint, is_refusal
from qmf.core.chrono import WriterId
from qmf.data.store import JournalStore

from qmn.config.compiler import ResolvedNodeConfig
from qmn.host._refuse import invalid, policy, unavailable
from qmn.host.boot_ceremony import (
    BootAttemptRecord,
    CompositionFingerprintInputs,
    PreflightFacts,
    WorkloadClaim,
)
from qmn.host.boot_journal import QmfBootAttemptJournalSink
from qmn.host.configured_runtime import ConfiguredRuntimeAssessment
from qmn.host.sealed_runtime import (
    HostedRootInputs,
    SealedHostedRuntime,
    SealedRuntimeRequest,
    run_sealed_hosted_runtime,
)
from qmn.promotion.journal import ActivationPhase
from qmn.seats.dispatch import BookPathContext
from qmn.seats.state import GovernedSeatState

__all__ = [
    "ConfiguredHostedResources",
    "invoke_configured_hosted_runtime",
    "persist_configured_standdown",
    "validate_assessed_path_config",
]


@dataclass(frozen=True, slots=True)
class ConfiguredHostedResources:
    """Explicit host-owned inputs absent from the deployment declaration.

    Implementations construct these only after resolving admitted seat proof,
    KSA folds, Book path, reservation journal and order/decision ports from the
    checked operator configuration and current durable evidence.
    """

    composition_inputs: CompositionFingerprintInputs
    writer_streams: Sequence[tuple[str, str]]
    root_inputs: HostedRootInputs
    workload_claims: Sequence[WorkloadClaim] = ()
    risk_population: object = None
    shadow_consumer_wiring: Sequence[object] = ()
    preflight: PreflightFacts | None = None


def invoke_configured_hosted_runtime(
    assessment: object,
    *,
    journal_store: object,
    boot_epoch_id: object,
    instant: object,
    resources: object,
) -> Result[SealedHostedRuntime]:
    """Compose the runtime only from an active checked assessment and typed ports."""
    if not isinstance(assessment, ConfiguredRuntimeAssessment):
        return invalid("assessment", "supervisor consumes the checked configured-runtime result")
    if not isinstance(journal_store, JournalStore) or journal_store.world is not World.LIVE:
        return invalid("journal_store", "supervisor lifecycle evidence uses its live QMF journal")
    if not isinstance(boot_epoch_id, str) or not boot_epoch_id.strip():
        return invalid("boot_epoch_id", "supervisor invocation has its fresh process epoch")
    if not callable(instant):
        return invalid("instant", "CT-13 stage writes use the injected VPS wall clock")
    if not isinstance(resources, ConfiguredHostedResources):
        return unavailable(
            "hosted_resources",
            "admitted seat, KSA, Book, reservation and OrderPath ports are not available",
            failure_id="configured_runtime.hosted_resources_missing",
        )
    activation = assessment.activation
    if (
        activation.enforced_state is not GovernedSeatState.ACTIVE
        or activation.requested_state is not GovernedSeatState.ACTIVE
        or activation.phase is not ActivationPhase.SUCCESSFUL
        or activation.principal != "operator"
    ):
        return policy(
            "activation",
            "only the exact successful operator CT-24 activation can reach hosted composition",
            failure_id="configured_runtime.activation_not_active",
        )
    if resources.composition_inputs.config_fp != assessment.node_config.fingerprint:
        return policy("composition_inputs", "seal identity uses the assessed node config")
    if resources.composition_inputs.registry_as_of_fp != assessment.registry_as_of:
        return policy("composition_inputs", "seal identity cites the checked registry snapshot")
    path = resources.root_inputs.path
    if not isinstance(path, BookPathContext):
        return invalid("book_path", "resource provider carries typed BookPathContext")
    path_config = validate_assessed_path_config(path, assessment.node_config)
    if is_refusal(path_config):
        return path_config
    if path.binding_record != assessment.binding_record:
        return policy("binding_record", "hosted Book path carries the assessed CT-28 record")
    writer = WriterId.try_create(assessment.machine, "supervisor", "boot-lifecycle", boot_epoch_id)
    if is_refusal(writer):
        return writer
    sink = QmfBootAttemptJournalSink.resume(
        journal_store,
        writer.value,
        instant=instant,
    )
    if is_refusal(sink):
        return sink
    request = SealedRuntimeRequest(
        boot_epoch_id=boot_epoch_id,
        machine=assessment.machine,
        composition_inputs=resources.composition_inputs,
        writer_streams=resources.writer_streams,
        boot_attempt_sink=sink.value,
        config=assessment.node_config,
        workload_claims=resources.workload_claims,
        risk_population=resources.risk_population,
        shadow_consumer_wiring=resources.shadow_consumer_wiring,
        preflight=resources.preflight,
    )
    return run_sealed_hosted_runtime(request, resources.root_inputs)


def validate_assessed_path_config(path: object, expected: ResolvedNodeConfig) -> Result[None]:
    """Bind the Book ratchet inputs to the exact node config checked at preflight."""
    actual: object = getattr(path, "resolved_node_config", None)
    if type(actual) is not ResolvedNodeConfig:
        return policy(
            "node_config",
            "the Book path carries the exact assessed resolved node configuration",
        )
    if type(actual.fingerprint) is not Fingerprint or type(expected.fingerprint) is not Fingerprint:
        return policy("node_config", "resolved config carries exact fingerprint identities")
    actual_fp = fingerprint(actual.fp1_identity())
    expected_fp = fingerprint(expected.fp1_identity())
    declared_actual = Fingerprint.try_create(actual.fingerprint.value)
    declared_expected = Fingerprint.try_create(expected.fingerprint.value)
    if is_refusal(actual_fp):
        return actual_fp
    if is_refusal(expected_fp):
        return expected_fp
    if is_refusal(declared_actual):
        return declared_actual
    if is_refusal(declared_expected):
        return declared_expected
    if (
        actual_fp.value != declared_actual.value
        or expected_fp.value != declared_expected.value
        or actual_fp.value != expected_fp.value
    ):
        return policy(
            "node_config",
            "the Book path's full value-bearing row identity matches operator assessment",
        )
    return Ok(None)


def persist_configured_standdown(
    *,
    journal_store: object,
    machine: object,
    boot_epoch_id: object,
    instant: object,
    reason: object,
    failure_id: object = "configured_runtime.hosted_resources_missing",
) -> Result[BootAttemptRecord]:
    """Record resource/preflight stand-down in the same durable lifecycle stream."""
    if not isinstance(journal_store, JournalStore) or journal_store.world is not World.LIVE:
        return invalid("journal_store", "stand-down evidence uses the live QMF journal")
    if not callable(instant):
        return invalid("instant", "stand-down stages use an injected wall clock")
    if not isinstance(reason, str) or not reason.strip():
        return invalid("reason", "stand-down records its concrete missing condition")
    if not isinstance(failure_id, str) or not failure_id.strip():
        return invalid("failure_id", "stand-down uses a stable failure identifier")
    writer = WriterId.try_create(machine, "supervisor", "boot-lifecycle", boot_epoch_id)
    if is_refusal(writer):
        return writer
    sink = QmfBootAttemptJournalSink.resume(journal_store, writer.value, instant=instant)
    if is_refusal(sink):
        return sink
    first = BootAttemptRecord(
        boot_epoch_id=writer.value.boot_epoch_id,
        unit_role="qmn.service",
        stage="doors_bound",
        writer=writer.value,
        sequence=0,
        reason=reason.strip(),
    )
    persisted = sink.value.append(first)
    if is_refusal(persisted):
        return persisted
    attempt = BootAttemptRecord(
        boot_epoch_id=writer.value.boot_epoch_id,
        unit_role="qmn.service",
        stage="boot_attempt_written",
        writer=writer.value,
        sequence=0,
        reason=reason.strip(),
    )
    amended = sink.value.amend(attempt)
    if is_refusal(amended):
        return amended
    stand_down = BootAttemptRecord(
        boot_epoch_id=writer.value.boot_epoch_id,
        unit_role="qmn.service",
        stage="preflight",
        writer=writer.value,
        sequence=0,
        reason=reason.strip(),
        failure_id=failure_id.strip(),
    )
    return sink.value.amend(stand_down)
