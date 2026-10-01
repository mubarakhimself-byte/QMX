"""Compose a hosted decision root only from a durably checked boot seal."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from qmf.core import Ok, Result, TypedRefusal, is_refusal

from qmn.config.compiler import ResolvedNodeConfig
from qmn.host._refuse import invalid, policy
from qmn.host.boot_ceremony import (
    BootCeremonyOutcome,
    BoundSupervisorDoors,
    CompositionFingerprintInputs,
    PreflightFacts,
    WorkloadClaim,
    run_boot_ceremony,
)
from qmn.host.boot_journal import QmfBootAttemptJournalSink
from qmn.host.decision_root import HostedDecisionRoot, OrderPathTiming

__all__ = [
    "HostedRootInputs",
    "SealedHostedRuntime",
    "SealedRuntimeRequest",
    "run_sealed_hosted_runtime",
]


@dataclass(frozen=True, slots=True)
class SealedRuntimeRequest:
    """Typed boot ceremony inputs needed before a runtime root may be opened."""

    boot_epoch_id: str
    machine: str
    composition_inputs: CompositionFingerprintInputs
    writer_streams: Sequence[tuple[str, str]]
    boot_attempt_sink: QmfBootAttemptJournalSink
    config: ResolvedNodeConfig | None = None
    unit_role: str = "qmn.service"
    mode: str = "live"
    workload_claims: Sequence[WorkloadClaim] = ()
    risk_population: object = None
    shadow_consumer_wiring: Sequence[object] = ()
    preflight: PreflightFacts | None = None
    door_binder: Callable[[], Result[BoundSupervisorDoors]] | None = None
    reason: str | None = None
    mutate_runtime_state: bool = False


@dataclass(frozen=True, slots=True)
class HostedRootInputs:
    """Exact typed runtime resources consumed by ``HostedDecisionRoot.try_open``."""

    seat: object
    path: object
    order_path: object
    reservation_journal: object
    ksa_projection: object
    decision_journal: object
    timing_for: Callable[[object], Result[OrderPathTiming]]


@dataclass(frozen=True, slots=True)
class SealedHostedRuntime:
    """Boot evidence plus an optional root; readiness requires both authorities."""

    ceremony: BootCeremonyOutcome
    root: HostedDecisionRoot | None
    stand_down_reason: TypedRefusal | None = None

    @property
    def ready(self) -> bool:
        return self.ceremony.ready and self.root is not None and self.stand_down_reason is None


def run_sealed_hosted_runtime(
    request: object,
    root_inputs: object,
) -> Result[SealedHostedRuntime]:
    """Run boot, re-read its exact CT-13 seal, then open the decision root.

    Missing composition, activation, admission, KSA, journal, order, or timing
    authority is a typed stand-down. The ceremony result alone never substitutes
    for the independently checked persisted seal or an opened decision root.
    """
    if not isinstance(request, SealedRuntimeRequest):
        return invalid("request", "runtime composition requires typed boot inputs")
    if not isinstance(root_inputs, HostedRootInputs):
        return invalid("root_inputs", "hosted root composition requires its typed resource set")
    ceremony = run_boot_ceremony(
        boot_epoch_id=request.boot_epoch_id,
        machine=request.machine,
        unit_role=request.unit_role,
        mode=request.mode,
        config=request.config,
        composition_inputs=request.composition_inputs,
        writer_streams=request.writer_streams,
        workload_claims=request.workload_claims,
        risk_population=request.risk_population,
        shadow_consumer_wiring=request.shadow_consumer_wiring,
        preflight=request.preflight,
        boot_attempt_sink=request.boot_attempt_sink,
        door_binder=request.door_binder,
        reason=request.reason,
        mutate_runtime_state=request.mutate_runtime_state,
    )
    if is_refusal(ceremony):
        return ceremony
    outcome = ceremony.value
    composition_fp = outcome.composition_fp
    if (
        outcome.mode != "live"
        or not outcome.sealed
        or not outcome.ready
        or not outcome.opens_sequencer
        or composition_fp is None
    ):
        refusal = policy(
            "boot_seal", "only a successful live seal may proceed to hosted-root recovery"
        )
        return Ok(SealedHostedRuntime(ceremony=outcome, root=None, stand_down_reason=refusal))
    persisted = request.boot_attempt_sink.verify_sealed(composition_fp)
    if is_refusal(persisted):
        return Ok(SealedHostedRuntime(ceremony=outcome, root=None, stand_down_reason=persisted))
    root = HostedDecisionRoot.try_open(
        seat=root_inputs.seat,
        path=root_inputs.path,
        order_path=root_inputs.order_path,
        reservation_journal=root_inputs.reservation_journal,
        ksa_projection=root_inputs.ksa_projection,
        decision_journal=root_inputs.decision_journal,
        timing_for=root_inputs.timing_for,
    )
    if is_refusal(root):
        return Ok(SealedHostedRuntime(ceremony=outcome, root=None, stand_down_reason=root))
    return Ok(SealedHostedRuntime(ceremony=outcome, root=root.value))
