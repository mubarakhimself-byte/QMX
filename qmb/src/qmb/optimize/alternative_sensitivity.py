"""Read-time B-8 sensitivity analysis over durable Alternative Study trials.

The adapter resolves only CT-13/CT-07-backed Alternative terminal artifacts and
feeds their exact registered objective/assignment values to the shared pure
sensitivity fold. It creates no LedgerLine, CT-32 result, winner threshold, or
execution effect.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import cast

from qmf.core import Fingerprint, Money, Ok, Result, UnitKind, World, fingerprint, is_refusal
from qmf.core.chrono import WriterId
from qmf.core.exact import MONEY_STORAGE_SCALE

from qmb._refuse import invalid, policy
from qmb.config.alternative import validate_alternative_run_config
from qmb.execution.alternative import PolicyInterpreterRegistration
from qmb.execution.alternative_terminal import AlternativeTerminalArtifact
from qmb.host.operator_alternative import OperatorAlternativeInputs
from qmb.host.operator_alternative_study import OperatorAlternativeStudyPlan
from qmb.optimize.resume import resume_stepper
from qmb.optimize.sampler import PriorTrial, trial_label_assignment, validate_trial_label
from qmb.optimize.sensitivity import (
    SENSITIVITY_REPORT_CLASS,
    SensitivityReport,
    SensitivitySample,
    build_sensitivity_report_from_samples,
)

__all__ = [
    "AlternativeSensitivityAnalysis",
    "build_operator_alternative_sensitivity",
]


@dataclass(frozen=True, slots=True)
class AlternativeSensitivityAnalysis:
    """Sensitivity report bound to its complete ATC plan and terminal history."""

    plan_fingerprint: Fingerprint
    terminal_artifact_fingerprints: tuple[Fingerprint, ...]
    report: SensitivityReport
    fingerprint: Fingerprint

    def fp1_identity(self) -> dict[str, object]:
        return {
            "class": "qmb-alternative-sensitivity-analysis-v1",
            "format_version": 1,
            "plan_fp1": self.plan_fingerprint.value,
            "report": self.report.fp1_identity(),
            "report_class": SENSITIVITY_REPORT_CLASS,
            "terminal_artifact_fp1s": [item.value for item in self.terminal_artifact_fingerprints],
        }


def _writer_identity(writer: WriterId) -> dict[str, object]:
    return {
        "boot_epoch_id": writer.boot_epoch_id,
        "machine": writer.machine,
        "role": writer.role,
        "stream": writer.stream,
    }


def _validate_candidate(
    inputs: OperatorAlternativeInputs,
    plan: OperatorAlternativeStudyPlan,
    artifact: AlternativeTerminalArtifact,
    assignment: Mapping[str, object],
) -> Result[None]:
    if set(assignment) != {binding.parameter_name for binding in plan.bindings}:
        return policy("assignment", "trial assignment covers the complete declared parameter set")
    payload = inputs.config.payload()
    pair_value = payload.get("policy_pair")
    if not isinstance(pair_value, Mapping):
        return invalid("policy_pair", "ATC base configuration carries its typed policy pair")
    pair = cast("Mapping[str, object]", pair_value)
    accounting_value, risk_value = pair.get("accounting"), pair.get("risk")
    if not isinstance(accounting_value, Mapping) or not isinstance(risk_value, Mapping):
        return invalid("policy_pair", "candidate starts with typed accounting and risk sections")
    accounting = dict(cast("Mapping[str, object]", accounting_value))
    risk = dict(cast("Mapping[str, object]", risk_value))
    for binding in plan.bindings:
        value = assignment.get(binding.parameter_name)
        if type(value) not in {int, str}:
            return invalid("assignment", "candidate has an exact supported scalar value")
        destination = accounting if binding.component == "accounting" else risk
        if binding.field_name not in destination:
            return policy("binding", "candidate target remains in the admitted PolicyPair")
        destination[binding.field_name] = value
    payload["policy_pair"] = {"accounting": accounting, "risk": risk}
    payload.pop("policy_pair_hash", None)
    payload.pop("composition_fp", None)
    candidate = validate_alternative_run_config(payload)
    if is_refusal(candidate):
        return candidate
    if inputs.recorded_source.split_fp1 is None or inputs.recorded_source.split_role is None:
        return policy("split", "ATC sensitivity is tied to the pinned CT-12 role")
    registration = inputs.registry.resolve(inputs.config)
    if is_refusal(registration):
        return registration
    rebound = PolicyInterpreterRegistration.try_create(
        policy_pair_id=candidate.value.policy_pair.policy_pair_id,
        policy_pair_version=candidate.value.policy_pair.policy_pair_version,
        policy_pair_hash=candidate.value.policy_pair.policy_pair_hash,
        interpreter_id=registration.value.interpreter_id,
        interpreter_version=registration.value.interpreter_version,
        interpreter_fp1=registration.value.interpreter_fp1,
        interpreter=registration.value.interpreter,
        declared_measures=registration.value.declared_measures,
    )
    if is_refusal(rebound):
        return rebound
    recorded_registration = artifact.body.get("interpreter_registration")
    if not isinstance(recorded_registration, Mapping):
        return invalid("interpreter_registration", "durable ATC trial carries its registered code")
    recorded_fp = fingerprint(cast("Mapping[str, object]", recorded_registration))
    expected_fp = fingerprint(rebound.value.identity())
    if is_refusal(recorded_fp) or is_refusal(expected_fp):
        return invalid("interpreter_registration", "trial interpreter identity is canonical")
    if (
        artifact.body.get("composition_fp1") != candidate.value.composition_fp.value
        or artifact.body.get("policy_pair_identity") != candidate.value.policy_pair.identity()
        or artifact.body.get("source_fp1") != inputs.recorded_source.fingerprint.value
        or artifact.body.get("split_fp1") != inputs.recorded_source.split_fp1.value
        or artifact.body.get("split_role") != inputs.recorded_source.split_role.value
        or recorded_fp.value != expected_fp.value
    ):
        return policy(
            "trial_lineage", "terminal source, split, PolicyPair, and interpreter match the plan"
        )
    if artifact.body.get("journal_writer") != _writer_identity(inputs.journal_writer.writer):
        return policy("journal_writer", "trial terminal uses the plan's pinned evidence writer")
    if artifact.body.get("journal_stream") != inputs.journal_writer.stream_name:
        return policy("journal_stream", "trial terminal uses the plan's pinned evidence stream")
    return Ok(None)


def _objective_fraction(
    artifact: AlternativeTerminalArtifact, plan: OperatorAlternativeStudyPlan
) -> Result[Fraction]:
    measures = artifact.body.get("final_measures")
    if not isinstance(measures, (tuple, list)):
        return invalid("final_measures", "trial terminal contains persisted exact measures")
    matches: list[Mapping[str, object]] = []
    for raw in cast("tuple[object, ...] | list[object]", measures):
        if isinstance(raw, Mapping):
            body = cast("Mapping[str, object]", raw)
            if body.get("measure_identity") == plan.objective.measure_identity:
                matches.append(body)
    if len(matches) != 1:
        return policy("objective", "each terminal has one declared objective value")
    measure = matches[0]
    if (
        measure.get("unit_kind") != plan.objective.unit_kind
        or measure.get("currency") != plan.objective.currency
    ):
        return policy("objective", "persisted objective retains the declared exact units")
    quantity_value = measure.get("quantity")
    if not isinstance(quantity_value, Mapping):
        return invalid("objective", "persisted objective is an exact quantity identity")
    quantity = cast("Mapping[str, object]", quantity_value)
    numerator, denominator = quantity.get("num"), quantity.get("den")
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        return invalid("objective", "objective magnitude is a canonical exact rational")
    magnitude = Fraction(numerator, denominator)
    if plan.objective.unit_kind == UnitKind.MONEY.value:
        if quantity.get("class") != "money" or quantity.get("currency") != plan.objective.currency:
            return policy("objective", "Money objective retains its pinned currency")
        scaled = magnitude * (10**MONEY_STORAGE_SCALE)
        if scaled.denominator != 1:
            return invalid("objective", "Money objective is representable at QMF storage scale")
        canonical = Money.try_create(scaled.numerator, plan.objective.currency, MONEY_STORAGE_SCALE)
        if is_refusal(canonical) or canonical.value.fp1_identity() != dict(quantity):
            return invalid("objective", "Money objective has a canonical QMF identity")
    elif (
        quantity.get("class") != "exact-rational"
        or quantity.get("unit_kind") != plan.objective.unit_kind
    ):
        return policy("objective", "rational objective retains its declared unit-kind")
    return Ok(magnitude)


def build_operator_alternative_sensitivity(
    inputs: object,
    plan: object,
    *,
    neighbourhood_size: object = None,
) -> Result[AlternativeSensitivityAnalysis]:
    """Reopen complete ATC trial history and analyze its exact objective landscape."""
    if type(inputs) is not OperatorAlternativeInputs:
        return invalid("operator_inputs", "ATC sensitivity uses trusted resolved operator inputs")
    if type(plan) is not OperatorAlternativeStudyPlan:
        return invalid("study_plan", "ATC sensitivity uses the admitted typed Study plan")
    rebuilt = OperatorAlternativeStudyPlan.try_create(
        inputs,
        parameter_space=plan.parameter_space,
        seed=plan.seed,
        direction=plan.direction,
        rounding=plan.rounding,
        batch_size=plan.batch_size,
        generation_count=plan.generation_count,
        objective=plan.objective,
        bindings=plan.bindings,
    )
    if is_refusal(rebuilt):
        return rebuilt
    stamped_plan_identity = fingerprint(plan.identity)
    if is_refusal(stamped_plan_identity):
        return stamped_plan_identity
    if (
        rebuilt.value.fingerprint != plan.fingerprint
        or rebuilt.value.operational_fingerprint != plan.operational_fingerprint
        or stamped_plan_identity.value != plan.operational_fingerprint
    ):
        return policy("study_plan", "sensitivity plan reproduces from current trusted inputs")
    opened = inputs.terminal_store.read(
        journal_store=inputs.journal_store,
        registry=inputs.registry_persistence,
    )
    if is_refusal(opened):
        return opened
    samples: list[SensitivitySample] = []
    priors: list[PriorTrial] = []
    fingerprints: list[Fingerprint] = []
    coordinates: set[tuple[int, int]] = set()
    for artifact in opened.value:
        raw_label = artifact.body.get("trial_label")
        if raw_label is None:
            continue
        label = validate_trial_label(raw_label)
        if is_refusal(label):
            return label
        if label.value["study_fp"] != plan.fingerprint.value:
            continue
        generation, ask = label.value["generation_index"], label.value["ask_index"]
        if type(generation) is not int or type(ask) is not int:
            return invalid("trial_label", "study generation and ask coordinates are exact integers")
        coordinate = (generation, ask)
        if coordinate in coordinates:
            return policy("trial_label", "one durable terminal exists per study ask")
        coordinates.add(coordinate)
        assignment = trial_label_assignment(label.value)
        if is_refusal(assignment):
            return assignment
        candidate = _validate_candidate(inputs, plan, artifact, assignment.value)
        if is_refusal(candidate):
            return candidate
        magnitude = _objective_fraction(artifact, plan)
        if is_refusal(magnitude):
            return magnitude
        prior = PriorTrial.try_create(generation, ask, assignment.value, magnitude.value)
        if is_refusal(prior):
            return prior
        priors.append(prior.value)
        sample = SensitivitySample.try_create(
            trial_id=artifact.fingerprint.value,
            world=World.REPLAY,
            role="trial",
            objective=magnitude.value,
            unit_kind=plan.objective.unit_kind,
            currency=plan.objective.currency,
            assignment=assignment.value,
            taint="optimistic",
        )
        if is_refusal(sample):
            return sample
        samples.append(sample.value)
        fingerprints.append(artifact.fingerprint)
    resumed = resume_stepper(plan.stepper(), priors)
    if is_refusal(resumed):
        return resumed
    if resumed.value[1].completed_generations != plan.generation_count:
        return policy("study_barrier", "sensitivity requires every declared generation complete")
    if len(samples) != plan.generation_count * plan.batch_size:
        return policy("study_history", "sensitivity requires every declared trial exactly once")
    report = build_sensitivity_report_from_samples(
        samples,
        objective=plan.objective.measure_identity,
        world=World.REPLAY,
        direction=plan.direction,
        role="trial",
        neighbourhood_size=neighbourhood_size,
    )
    if is_refusal(report):
        return report
    identity = {
        "class": "qmb-alternative-sensitivity-analysis-v1",
        "format_version": 1,
        "plan_fp1": plan.fingerprint.value,
        "report": report.value.fp1_identity(),
        "report_class": SENSITIVITY_REPORT_CLASS,
        "terminal_artifact_fp1s": [item.value for item in fingerprints],
    }
    stamped = fingerprint(identity)
    if is_refusal(stamped):
        return stamped
    return Ok(
        AlternativeSensitivityAnalysis(
            plan_fingerprint=plan.fingerprint,
            terminal_artifact_fingerprints=tuple(fingerprints),
            report=report.value,
            fingerprint=stamped.value,
        )
    )
