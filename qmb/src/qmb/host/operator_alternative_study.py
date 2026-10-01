"""Operator-bound generation studies for the Alternative composition.

This adapter composes existing typed QMB/QMF inputs. It owns no public command,
registry kind, financial policy, or arbitrary trial callback. Study trials use the
registered Alternative interpreter and the same checked CT-10/CT-12, CT-13, and
CT-07 paths as one Alternative replay.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import cast

from qmf.core import (
    Fingerprint,
    Instant,
    Ok,
    Result,
    UnitKind,
    World,
    WriterId,
    fingerprint,
    is_refusal,
)
from qmf.core.exact import MONEY_STORAGE_SCALE, Money, RoundingMode
from qmf.data.journal_producer import JournalWriter
from qmf.data.store import JournalStore
from qmf.registry import RegistryPersistence
from qml.declaration.parameters import ParameterType

from qmb._refuse import invalid, policy, unavailable, unsupported
from qmb.config.alternative import validate_alternative_run_config
from qmb.execution.alternative import (
    AlternativeInterpreterRegistry,
    PolicyInterpreterRegistration,
    execute_alternative_run,
)
from qmb.execution.alternative_terminal import AlternativeTerminalArtifact, AlternativeTerminalStore
from qmb.host.operator_alternative import (
    OperatorAlternativeInputs,
)
from qmb.host.operator_occurrence import (
    OperatorOccurrenceIdentity,
    OperatorOccurrenceReceipt,
    record_operator_occurrence,
)
from qmb.host.qma_cli import validate_qma_backtest_context
from qmb.host.replay import RecordedReplaySource
from qmb.optimize.alternative_study import (
    AlternativeParameterBinding,
    AlternativeStudyObjective,
    run_alternative_study,
)
from qmb.optimize.resume import resume_stepper
from qmb.optimize.sampler import (
    PriorTrial,
    StudyStepper,
    generator_provenance,
    sampler_identity,
    trial_label_assignment,
    validate_trial_label,
)
from qmb.optimize.space import StudyParameterSpace, coerce_study_space
from qmb.optimize.study import StudyGenerationRun

__all__ = [
    "OPERATOR_ALTERNATIVE_STUDY_CLASS",
    "OperatorAlternativeStudyPlan",
    "OperatorAlternativeStudyResult",
    "run_operator_alternative_study",
]

OPERATOR_ALTERNATIVE_STUDY_CLASS = "qmb-operator-alternative-study-v1"
_PLAN_FORMAT_VERSION = 1


def _writer_identity(writer: WriterId) -> dict[str, str]:
    return {
        "boot_epoch_id": writer.boot_epoch_id,
        "machine": writer.machine,
        "role": writer.role,
        "stream": writer.stream,
    }


def _writer_is_canonical(writer: object) -> bool:
    if type(writer) is not WriterId:
        return False
    rebuilt = WriterId.try_create(
        writer.machine,
        writer.role,
        writer.stream,
        writer.boot_epoch_id,
    )
    return not is_refusal(rebuilt) and rebuilt.value == writer


def _space(value: object) -> Result[StudyParameterSpace]:
    # Reconstruct typed instances from their declared ParameterSpec values. This
    # deliberately bypasses StudyParameterSpace.try_create's nominal fast path.
    if type(value) is StudyParameterSpace:
        return StudyParameterSpace.try_create(tuple(value.parameters))
    return coerce_study_space(value)


def _objective(value: object) -> Result[AlternativeStudyObjective]:
    if type(value) is not AlternativeStudyObjective:
        return invalid("objective", "ATC Study objective is a typed registered measure")
    if (
        type(value.measure_identity) is not str
        or type(value.direction) is not str
        or type(value.unit_kind) is not str
        or (value.currency is not None and type(value.currency) is not str)
    ):
        return invalid("objective", "nominal objective fields have their exact declared types")
    return AlternativeStudyObjective.try_create(
        value.measure_identity,
        value.direction,
        value.unit_kind,
        value.currency,
    )


def _bindings(value: object) -> Result[tuple[AlternativeParameterBinding, ...]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        return invalid("parameter_bindings", "ATC Study declares an ordered binding sequence")
    bindings: list[AlternativeParameterBinding] = []
    for index, raw in enumerate(cast("Sequence[object]", value)):
        if type(raw) is not AlternativeParameterBinding:
            return invalid(
                "parameter_bindings",
                "each binding uses its typed QMB value",
                index=index,
            )
        if (
            type(raw.parameter_name) is not str
            or type(raw.component) is not str
            or type(raw.field_name) is not str
        ):
            return invalid(
                "parameter_bindings", "nominal binding fields are exact text", index=index
            )
        binding = AlternativeParameterBinding.try_create(
            raw.parameter_name,
            raw.component,
            raw.field_name,
        )
        if is_refusal(binding):
            return binding
        bindings.append(binding.value)
    if not bindings:
        return invalid("parameter_bindings", "ATC Study binds at least one declared field")
    if len({item.parameter_name for item in bindings}) != len(bindings):
        return invalid("parameter_bindings", "each Study parameter binds exactly once")
    if len({(item.component, item.field_name) for item in bindings}) != len(bindings):
        return invalid("parameter_bindings", "each PolicyPair field is assigned exactly once")
    return Ok(tuple(bindings))


def _base_identity(inputs: OperatorAlternativeInputs) -> Result[dict[str, object]]:
    if type(inputs) is not OperatorAlternativeInputs:
        return invalid("operator_inputs", "Study consumes trusted operator-resolved inputs")
    context = inputs.context
    checked_context = validate_qma_backtest_context(context)
    if is_refusal(checked_context):
        return checked_context
    if (
        type(context.job_id) is not str
        or type(context.attempt_id) is not int
        or type(context.mints_ct32) is not bool
        or context.mints_ct32 is not False
        or type(context.operator_descriptor_fp1) is not Fingerprint
    ):
        return invalid("qma_context", "ATC Study context is canonical and explicitly non-CT-32")
    config = validate_alternative_run_config(inputs.config)
    if is_refusal(config) or config.value.fingerprint != inputs.config.fingerprint:
        return policy("config", "ATC base config reproduces its canonical fingerprint")
    source = inputs.recorded_source
    if (
        type(source) is not RecordedReplaySource
        or source.world is not World.REPLAY
        or source.split_fp1 is None
        or source.split_role is None
        or source.split_fp1 != context.split_manifest_fp1
    ):
        return policy("split", "ATC optimization binds a materialized CT-12 split and role")
    source_fp = fingerprint(source.fp1_identity())
    if is_refusal(source_fp) or source_fp.value != source.fingerprint:
        return policy("source", "CT-10 source reproduces its checked content identity")
    registry = inputs.registry
    if type(registry) is not AlternativeInterpreterRegistry:
        return invalid("registry", "ATC Study uses a typed interpreter registry")
    canonical_registry = AlternativeInterpreterRegistry.try_create(
        tuple(registry.registrations.values())
    )
    if (
        is_refusal(canonical_registry)
        or canonical_registry.value.fingerprint != registry.fingerprint
    ):
        return policy("registry", "registered interpreter set reproduces its exact identity")
    registration = canonical_registry.value.resolve(config.value)
    if is_refusal(registration):
        return registration
    state_fp = fingerprint(inputs.initial_accounting_state)
    if is_refusal(state_fp):
        return state_fp
    if type(inputs.expected_command_owner_epoch) is not int:
        return invalid("command_owner_epoch", "Study binds an exact integer command epoch")
    if inputs.expected_command_owner_epoch != config.value.command.command_owner_epoch:
        return policy("command_owner_epoch", "Study is bound to the admitted command epoch")
    if type(inputs.runtime_descriptor_fp1) is not Fingerprint:
        return invalid("runtime_descriptor_fp1", "Study uses the verified operator descriptor fp1")
    if context.operator_descriptor_fp1 != inputs.runtime_descriptor_fp1:
        return policy("runtime_descriptor_fp1", "CT-47 and operator inputs pin one descriptor")
    if inputs.trial_label is not None:
        return invalid("trial_label", "Study owns per-trial labels; base label is absent")
    if (
        type(inputs.journal_writer) is not JournalWriter
        or type(inputs.journal_store) is not JournalStore
        or inputs.journal_writer.world is not World.REPLAY
        or inputs.journal_store.world is not World.REPLAY
        or inputs.journal_writer.stream_name != inputs.journal_writer.writer.stream
    ):
        return policy("journal", "ATC Study is pinned to one typed replay CT-13 stream")
    if (
        type(inputs.terminal_store) is not AlternativeTerminalStore
        or type(inputs.registry_persistence) is not RegistryPersistence
        or type(inputs.lineage_writer) is not WriterId
        or type(inputs.registry_writer) is not WriterId
    ):
        return invalid("persistence", "ATC Study uses its typed terminal, registry, and writers")
    if type(inputs.registry_as_of) is not Instant:
        return invalid("registry_as_of", "CT-07 as-of is a typed Instant")
    checked_as_of = Instant.try_create(inputs.registry_as_of.value_ns)
    if is_refusal(checked_as_of) or checked_as_of.value != inputs.registry_as_of:
        return invalid("registry_as_of", "CT-07 as-of is an exact instant")
    if not all(
        _writer_is_canonical(writer)
        for writer in (
            inputs.journal_writer.writer,
            inputs.lineage_writer,
            inputs.registry_writer,
            inputs.terminal_store.writer,
        )
    ):
        return invalid("writer", "ATC Study writer identities pass official QMF validation")
    if (
        not inputs.raw_store_root.is_absolute()
        or not inputs.journal_root.is_absolute()
        or not inputs.terminal_store.root.is_absolute()
    ):
        return invalid(
            "runtime_roots", "operator source, journal, and terminal roots are absolute"
        )
    try:
        raw_root = str(inputs.raw_store_root.resolve(strict=True))
        journal_root = str(inputs.journal_root.resolve(strict=True))
        terminal_root = str(inputs.terminal_store.root.resolve(strict=True))
    except OSError as exc:
        return unavailable("runtime_roots", "pinned replay roots resolve", error=str(exc))
    trial_label_fp = fingerprint(
        {
            "class": "qmb-alternative-trial-label-input-v1",
            "present": inputs.trial_label is not None,
            "label": {} if inputs.trial_label is None else inputs.trial_label,
        }
    )
    if is_refusal(trial_label_fp):
        return trial_label_fp
    computation: dict[str, object] = {
            "composition_class": "alternative",
            "composition_fp1": inputs.config.composition_fp.value,
            "policy_pair_identity": inputs.config.policy_pair.identity(),
            "resolved_config_fp1": inputs.config.fingerprint.value,
            "source_fp1": source.fingerprint.value,
            "split_fp1": source.split_fp1.value,
            "split_role": source.split_role.value,
            "registry_fp1": inputs.registry.fingerprint.value,
            "interpreter_registration_fp1": registration.value.fingerprint.value,
            "initial_accounting_state_fp1": state_fp.value.value,
            "command_owner_epoch": inputs.expected_command_owner_epoch,
            "experiment_spec_fp1": context.experiment_spec_fp1.value,
            "evidence_ref": context.evidence_ref.value,
            "split_manifest_fp1": context.split_manifest_fp1.value,
            "registry_as_of_ns": inputs.registry_as_of.value_ns,
            "registry_writer": _writer_identity(inputs.registry_writer),
            "input_trial_label_fp1": trial_label_fp.value.value,
        }
    operational: dict[str, object] = {
            "qma_occurrence": {
                "job_id": context.job_id,
                "attempt_id": context.attempt_id,
                "environment_ref": context.environment_ref,
                "occupancy_key": context.occupancy_key,
            },
            "journal_writer": _writer_identity(inputs.journal_writer.writer),
            "journal_stream": inputs.journal_writer.stream_name,
            "terminal_writer": _writer_identity(inputs.terminal_store.writer),
            "lineage_writer": _writer_identity(inputs.lineage_writer),
            "runtime_descriptor_fp1": inputs.runtime_descriptor_fp1.value,
            "raw_store_root": raw_root,
            "journal_root": journal_root,
            "terminal_root": terminal_root,
            "registry_root": str(inputs.registry_persistence.root.absolute()),
        }
    return Ok(cast("dict[str, object]", {
        "computation": computation,
        "operational": operational,
    }))


def _objective_value(
    artifact: AlternativeTerminalArtifact,
    objective: AlternativeStudyObjective,
) -> Result[Fraction]:
    raw_measures = artifact.body.get("final_measures")
    if not isinstance(raw_measures, (tuple, list)):
        return invalid("final_measures", "ATC terminal has persisted declared measures")
    matches: list[Mapping[str, object]] = []
    for raw in cast("Sequence[object]", raw_measures):
        if isinstance(raw, Mapping):
            measure_body = cast("Mapping[str, object]", raw)
            if measure_body.get("measure_identity") == objective.measure_identity:
                matches.append(measure_body)
    if len(matches) != 1:
        return policy("objective", "terminal contains one value for the declared objective")
    measure = matches[0]
    if (
        measure.get("unit_kind") != objective.unit_kind
        or measure.get("currency") != objective.currency
    ):
        return policy("objective", "terminal objective measure retains its declared unit")
    quantity = measure.get("quantity")
    if not isinstance(quantity, Mapping):
        return invalid("objective", "terminal objective carries a typed exact quantity")
    body = cast("Mapping[str, object]", quantity)
    if objective.unit_kind == UnitKind.MONEY.value:
        if body.get("class") != "money" or body.get("currency") != objective.currency:
            return policy("objective", "money measure retains exact declared currency")
        numerator, denominator = body.get("num"), body.get("den")
        if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
            return invalid("objective", "money measure is a canonical exact rational amount")
        magnitude = Fraction(numerator, denominator)
        scaled = magnitude * (10**MONEY_STORAGE_SCALE)
        if scaled.denominator != 1:
            return invalid("objective", "money measure is representable at QMF storage scale")
        canonical = Money.try_create(scaled.numerator, objective.currency, MONEY_STORAGE_SCALE)
        if is_refusal(canonical) or canonical.value.fp1_identity() != dict(body):
            return invalid("objective", "money measure is a canonical QMF Money identity")
        return Ok(magnitude)
    if body.get("class") != "exact-rational" or body.get("unit_kind") != objective.unit_kind:
        return policy("objective", "non-money measure carries its declared exact unit-kind")
    numerator, denominator = body.get("num"), body.get("den")
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        return invalid("objective", "exact objective measure has a positive rational denominator")
    return Ok(Fraction(numerator, denominator))


def _candidate_identity(
    inputs: OperatorAlternativeInputs,
    bindings: tuple[AlternativeParameterBinding, ...],
    assignment: Mapping[str, object],
    artifact: AlternativeTerminalArtifact,
) -> Result[None]:
    """Recompute each trial's candidate lineage before conditioning or returning it."""
    if set(assignment) != {binding.parameter_name for binding in bindings}:
        return policy("assignment", "trial candidate matches all declared Study parameters")
    payload = inputs.config.payload()
    raw_pair = payload.get("policy_pair")
    if not isinstance(raw_pair, Mapping):
        return invalid("policy_pair", "pinned base config carries its canonical PolicyPair")
    pair = cast("Mapping[str, object]", raw_pair)
    raw_accounting, raw_risk = pair.get("accounting"), pair.get("risk")
    if not isinstance(raw_accounting, Mapping) or not isinstance(raw_risk, Mapping):
        return invalid("policy_pair", "candidate starts from declared accounting and risk maps")
    accounting = dict(cast("Mapping[str, object]", raw_accounting))
    risk = dict(cast("Mapping[str, object]", raw_risk))
    for binding in bindings:
        value = assignment[binding.parameter_name]
        if type(value) not in {int, str}:
            return invalid("assignment", "candidate values are exact supported PolicyPair scalars")
        target = accounting if binding.component == "accounting" else risk
        if binding.field_name not in target:
            return policy("binding", "candidate destination remains in the pinned PolicyPair")
        target[binding.field_name] = value
    payload["policy_pair"] = {"accounting": accounting, "risk": risk}
    payload.pop("policy_pair_hash", None)
    payload.pop("composition_fp", None)
    candidate = validate_alternative_run_config(payload)
    if is_refusal(candidate):
        return candidate
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
    if inputs.recorded_source.split_fp1 is None or inputs.recorded_source.split_role is None:
        return policy("split", "trial lineage retains the pinned CT-12 source role")
    body = artifact.body
    recorded_registration = body.get("interpreter_registration")
    if not isinstance(recorded_registration, Mapping):
        return invalid("interpreter_registration", "terminal stores registered code identity")
    recorded_registration_fp = fingerprint(
        cast("Mapping[str, object]", recorded_registration)
    )
    expected_registration_fp = fingerprint(rebound.value.identity())
    if is_refusal(recorded_registration_fp) or is_refusal(expected_registration_fp):
        return invalid("interpreter_registration", "registered code identity is canonical")
    if (
        body.get("composition_fp1") != candidate.value.composition_fp.value
        or body.get("policy_pair_identity") != candidate.value.policy_pair.identity()
        or body.get("source_fp1") != inputs.recorded_source.fingerprint.value
        or body.get("split_fp1") != inputs.recorded_source.split_fp1.value
        or body.get("split_role") != inputs.recorded_source.split_role.value
        or recorded_registration_fp.value != expected_registration_fp.value
    ):
        return policy(
            "trial_lineage", "terminal trial matches candidate, source, split, and interpreter"
        )
    return Ok(None)


@dataclass(frozen=True, slots=True)
class OperatorAlternativeStudyPlan:
    """Frozen Study declaration derived from typed current optimization values."""

    parameter_space: StudyParameterSpace
    seed: int
    direction: str
    rounding: RoundingMode
    batch_size: int
    generation_count: int
    objective: AlternativeStudyObjective
    bindings: tuple[AlternativeParameterBinding, ...]
    identity: Mapping[str, object]
    fingerprint: Fingerprint
    operational_fingerprint: Fingerprint
    base_binding_fingerprint: Fingerprint

    @classmethod
    def try_create(
        cls,
        inputs: object,
        *,
        parameter_space: object,
        seed: object,
        direction: object,
        rounding: object,
        batch_size: object,
        generation_count: object,
        objective: object,
        bindings: object,
    ) -> Result[OperatorAlternativeStudyPlan]:
        if type(inputs) is not OperatorAlternativeInputs:
            return invalid(
                "operator_inputs", "Study admission uses trusted operator-resolved inputs"
            )
        base = _base_identity(inputs)
        if is_refusal(base):
            return base
        space = _space(parameter_space)
        if is_refusal(space):
            return space
        if type(seed) is not int or seed < 0:
            return invalid("seed", "TPE seed is a nonnegative exact integer")
        if type(direction) is not str or direction not in {"min", "max"}:
            return invalid("direction", "Study objective direction is min or max")
        if type(rounding) is not RoundingMode:
            return invalid("rounding", "Study records the sampler's exact conversion mode")
        if type(batch_size) is not int or batch_size < 1:
            return invalid("batch_size", "Study batch size is a positive exact integer")
        if type(generation_count) is not int or generation_count < 1:
            return invalid(
                "generation_count", "Study generation budget is a positive exact integer"
            )
        parsed_objective = _objective(objective)
        if is_refusal(parsed_objective):
            return parsed_objective
        if parsed_objective.value.direction != direction:
            return policy("direction", "Study sampler and registered objective directions agree")
        parsed_bindings = _bindings(bindings)
        if is_refusal(parsed_bindings):
            return parsed_bindings
        binding_names = {item.parameter_name for item in parsed_bindings.value}
        if binding_names != set(space.value.parameter_names):
            return policy(
                "parameter_bindings", "every typed search parameter has one PolicyPair field"
            )
        registration = inputs.registry.resolve(inputs.config)
        if is_refusal(registration):
            return registration
        declarations = registration.value.declared_measures
        if parsed_objective.value.measure_identity not in {
            item.measure_identity for item in declarations
        }:
            return policy(
                "objective", "objective names one measure from the registered interpreter"
            )
        declaration_by_name = {item.measure_identity: item for item in declarations}
        declaration = declaration_by_name[parsed_objective.value.measure_identity]
        if (
            declaration.unit_kind != parsed_objective.value.unit_kind
            or declaration.currency != parsed_objective.value.currency
        ):
            return policy(
                "objective", "objective unit and currency match its registered declaration"
            )
        pair = inputs.config.policy_pair
        for binding in parsed_bindings.value:
            target = pair.accounting if binding.component == "accounting" else pair.risk
            if binding.field_name not in target:
                return policy(
                    "parameter_bindings", "candidate field exists in the pinned PolicyPair"
                )
        for index, parameter in enumerate(space.value.parameters):
            if parameter.type is ParameterType.EXACT_INTEGER:
                continue
            if (
                parameter.type is ParameterType.CATEGORICAL
                and parameter.bounds is not None
                and all(type(choice) in {str, int} for choice in parameter.bounds)
            ):
                continue
            return unsupported(
                "candidate_parameter_type",
                "registered ATC overrides support exact integers and string/integer categories",
                index=index,
                parameter=parameter.name,
                parameter_type=parameter.type.value,
            )
        base_computation = cast("Mapping[str, object]", base.value["computation"])
        base_operational = cast("Mapping[str, object]", base.value["operational"])
        base_stamp = fingerprint(base_computation)
        if is_refusal(base_stamp):
            return base_stamp
        space_identity = space.value.fp1_identity()
        space_fp = space.value.fingerprint()
        if is_refusal(space_fp):
            return space_fp
        objective_identity = parsed_objective.value.fp1_identity()
        binding_identities = [item.fp1_identity() for item in parsed_bindings.value]
        study_identity: dict[str, object] = {
            "class": OPERATOR_ALTERNATIVE_STUDY_CLASS,
            "format_version": _PLAN_FORMAT_VERSION,
            "base_binding_fp1": base_stamp.value.value,
            "base_binding": base_computation,
            "parameter_space": space_identity,
            "parameter_space_fp1": space_fp.value.value,
            "seed": seed,
            "direction": direction,
            "rounding": rounding.value,
            "batch_size": batch_size,
            "generation_count": generation_count,
            "objective": objective_identity,
            "parameter_bindings": binding_identities,
            "sampler_identity": sampler_identity(),
            "generator_provenance": generator_provenance(),
        }
        study_fp = fingerprint(study_identity)
        if is_refusal(study_fp):
            return study_fp
        operational_binding_fp = fingerprint(base_operational)
        if is_refusal(operational_binding_fp):
            return operational_binding_fp
        operational_identity: dict[str, object] = {
            "class": f"{OPERATOR_ALTERNATIVE_STUDY_CLASS}-invocation-v1",
            "study_fp1": study_fp.value.value,
            "operational_binding_fp1": operational_binding_fp.value.value,
            "operational_binding": base_operational,
        }
        operational_fp = fingerprint(operational_identity)
        if is_refusal(operational_fp):
            return operational_fp
        frozen_identity = MappingProxyType(operational_identity)
        return Ok(
            cls(
                parameter_space=space.value,
                seed=seed,
                direction=direction,
                rounding=rounding,
                batch_size=batch_size,
                generation_count=generation_count,
                objective=parsed_objective.value,
                bindings=parsed_bindings.value,
                identity=frozen_identity,
                fingerprint=study_fp.value,
                operational_fingerprint=operational_fp.value,
                base_binding_fingerprint=base_stamp.value,
            )
        )

    def stepper(self) -> StudyStepper:
        """Build the one internally owned sampler from the plan fingerprint."""
        return StudyStepper(
            space=self.parameter_space,
            seed=self.seed,
            direction=self.direction,
            rounding=self.rounding,
            study_fp=self.fingerprint,
            batch_size=self.batch_size,
        )


@dataclass(frozen=True, slots=True)
class OperatorAlternativeStudyResult:
    """Reopened study state and the exact durable trial terminals it represents."""

    plan_fingerprint: Fingerprint
    operational_fingerprint: Fingerprint
    generation_run: StudyGenerationRun
    terminal_artifacts: tuple[AlternativeTerminalArtifact, ...]
    occurrence_receipt: OperatorOccurrenceReceipt

    def identity(self) -> dict[str, object]:
        return {
            "class": "qmb-operator-alternative-study-result-v1",
            "format_version": 1,
            "study_fp1": self.plan_fingerprint.value,
            "operational_fp1": self.operational_fingerprint.value,
            "generation_run": self.generation_run.fp1_identity(),
            "terminal_artifact_fp1s": [item.fingerprint.value for item in self.terminal_artifacts],
            "occurrence_event_fp1": self.occurrence_receipt.event.fingerprint.value,
        }

    def fp1_identity(self) -> dict[str, object]:
        """Canonical transport identity including its checked invocation witness."""
        return self.identity()


def _study_occurrence_time(
    artifact: AlternativeTerminalArtifact,
    source: RecordedReplaySource,
) -> Result[Instant]:
    references = artifact.body.get("journal_refs")
    if isinstance(references, (tuple, list)) and references:
        last_raw = cast("Sequence[object]", references)[-1]
        if not isinstance(last_raw, Mapping):
            return policy("journal_refs", "study terminal has its final checked frontier")
        last = cast("Mapping[str, object]", last_raw)
        frontier = last.get("frontier_ns")
        if type(frontier) is not int:
            return policy("journal_refs", "study terminal has its final checked frontier")
        return Instant.try_create(frontier)
    if source.slices and source.slices[-1].observations:
        return Ok(source.slices[-1].observations[-1].instant)
    return policy("recorded_source", "study terminal has an invocation occurrence instant")


def _record_study_occurrence(
    inputs: OperatorAlternativeInputs,
    plan: OperatorAlternativeStudyPlan,
    generation_run: StudyGenerationRun,
    artifacts: tuple[AlternativeTerminalArtifact, ...],
) -> Result[OperatorOccurrenceReceipt]:
    if not artifacts:
        return policy("study_history", "complete Study history includes checked terminal artifacts")
    trial_fingerprints: list[str] = []
    for trial in generation_run.completed_trials:
        trial_fp = fingerprint(cast("Mapping[str, object]", trial.fp1_identity()))
        if is_refusal(trial_fp):
            return trial_fp
        trial_fingerprints.append(trial_fp.value.value)
    history_identity: dict[str, object] = {
        "class": "qmb-operator-alternative-study-history-v1",
        "study_fp1": plan.fingerprint.value,
        "completed_trial_fp1s": trial_fingerprints,
        "terminal_artifact_fp1s": [artifact.fingerprint.value for artifact in artifacts],
    }
    history_fp = fingerprint(history_identity)
    if is_refusal(history_fp):
        return history_fp
    at = _study_occurrence_time(artifacts[-1], inputs.recorded_source)
    if is_refusal(at):
        return at
    identity = OperatorOccurrenceIdentity.try_create(
        context=inputs.context,
        composition_class="alternative",
        runtime_descriptor_fp1=inputs.runtime_descriptor_fp1,
        operator_binding_fp1=plan.operational_fingerprint,
        terminal_fp1=artifacts[-1].fingerprint,
        domain_result_fp1=history_fp.value,
        at=at.value,
        terminal_root=inputs.terminal_store.root,
        journal_root=inputs.journal_root,
        terminal_writer=inputs.terminal_store.writer,
        journal_writer=inputs.journal_writer.writer,
        journal_stream=inputs.journal_writer.stream_name,
        command_owner_epoch=inputs.expected_command_owner_epoch,
    )
    if is_refusal(identity):
        return identity
    return record_operator_occurrence(
        identity=identity.value,
        journal_writer=inputs.journal_writer,
        journal_store=inputs.journal_store,
        at=at.value,
    )


def _execute_trial_callback(
    inputs: OperatorAlternativeInputs,
) -> Callable[..., Result[object]]:
    def execute_trial(
        _generation: int,
        _proposal: object,
        label: Mapping[str, object],
        config: object,
        registry: object,
        source: object,
        writer: object,
    ) -> Result[object]:
        if not isinstance(config, type(inputs.config)):
            return invalid("candidate_config", "ATC trial receives a typed AlternativeRunConfig")
        if type(registry) is not AlternativeInterpreterRegistry:
            return invalid("candidate_registry", "ATC trial resolves a typed interpreter registry")
        if (
            type(source) is not RecordedReplaySource
            or source.fingerprint != inputs.recorded_source.fingerprint
        ):
            return policy("source", "every candidate uses the exact pinned CT-10/CT-12 source")
        if type(writer) is not JournalWriter:
            return invalid("journal_writer", "every candidate uses the exact bound CT-13 writer")
        if (
            writer.writer != inputs.journal_writer.writer
            or writer.stream_name != inputs.journal_writer.stream_name
        ):
            return policy(
                "journal_writer", "candidate execution remains on the pinned CT-13 stream"
            )
        receipt = execute_alternative_run(
            config,
            source,
            registry,
            initial_accounting_state=inputs.initial_accounting_state,
            expected_command_owner_epoch=inputs.expected_command_owner_epoch,
            journal_writer=writer,
            journal_store=inputs.journal_store,
            trial_label=label,
        )
        if is_refusal(receipt):
            return receipt
        return Ok(receipt.value)

    return execute_trial


def run_operator_alternative_study(
    inputs: object,
    plan: object,
    *,
    cancelled: object = None,
) -> Result[OperatorAlternativeStudyResult]:
    """Run/reopen an operator-bound ATC Study with internally fixed execution ports."""
    if type(inputs) is not OperatorAlternativeInputs:
        return invalid("operator_inputs", "ATC Study uses trusted resolved operator inputs")
    if type(plan) is not OperatorAlternativeStudyPlan:
        return invalid("study_plan", "ATC Study uses a typed, fingerprinted Study plan")
    fresh = OperatorAlternativeStudyPlan.try_create(
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
    if is_refusal(fresh):
        return fresh
    declared_identity_fp = fingerprint(plan.identity)
    if is_refusal(declared_identity_fp):
        return declared_identity_fp
    if (
        fresh.value.fingerprint != plan.fingerprint
        or fresh.value.operational_fingerprint != plan.operational_fingerprint
        or declared_identity_fp.value != plan.operational_fingerprint
    ):
        return policy("study_plan", "plan identity reproduces from the current trusted inputs")
    opened = inputs.terminal_store.read(
        journal_store=inputs.journal_store,
        registry=inputs.registry_persistence,
    )
    if is_refusal(opened):
        return opened
    history: list[PriorTrial] = []
    artifacts: list[AlternativeTerminalArtifact] = []
    seen: set[tuple[int, int]] = set()
    for artifact in opened.value:
        raw_label = artifact.body.get("trial_label")
        if raw_label is None:
            continue
        label = validate_trial_label(raw_label)
        if is_refusal(label):
            return label
        if label.value["study_fp"] != plan.fingerprint.value:
            continue
        generation = label.value["generation_index"]
        ask_index = label.value["ask_index"]
        if type(generation) is not int or type(ask_index) is not int:
            return invalid("trial_label", "reopened study coordinates are exact integers")
        coordinate = (generation, ask_index)
        if coordinate in seen:
            return policy("trial_label", "one reopened artifact exists per Study ask")
        seen.add(coordinate)
        assignment = trial_label_assignment(label.value)
        if is_refusal(assignment):
            return assignment
        lineage = _candidate_identity(inputs, plan.bindings, assignment.value, artifact)
        if is_refusal(lineage):
            return lineage
        objective = _objective_value(artifact, plan.objective)
        if is_refusal(objective):
            return objective
        prior = PriorTrial.try_create(generation, ask_index, assignment.value, objective.value)
        if is_refusal(prior):
            return prior
        history.append(prior.value)
        artifacts.append(artifact)
    resumed = resume_stepper(plan.stepper(), history)
    if is_refusal(resumed):
        return resumed
    resume_plan = resumed.value[1]
    if resume_plan.completed_generations > plan.generation_count:
        return policy("generation_count", "durable history does not exceed the frozen Study budget")
    additional_generations = plan.generation_count - resume_plan.completed_generations
    if additional_generations:
        completed = run_alternative_study(
            plan.stepper(),
            generation_count=additional_generations,
            base_config=inputs.config,
            registry=inputs.registry,
            source=inputs.recorded_source,
            objective=plan.objective,
            bindings=plan.bindings,
            terminal_store=inputs.terminal_store,
            journal_store=inputs.journal_store,
            registry_persistence=inputs.registry_persistence,
            lineage_writer=inputs.lineage_writer,
            execute_trial=_execute_trial_callback(inputs),
            initial_accounting_state=inputs.initial_accounting_state,
            journal_writer=inputs.journal_writer,
            cancelled=cancelled,
        )
        if is_refusal(completed):
            return completed

    reopened = inputs.terminal_store.read(
        journal_store=inputs.journal_store,
        registry=inputs.registry_persistence,
    )
    if is_refusal(reopened):
        return reopened
    history_after: list[PriorTrial] = []
    artifacts_after: list[AlternativeTerminalArtifact] = []
    artifacts_by_coordinate: dict[tuple[int, int], AlternativeTerminalArtifact] = {}
    coordinates_after: set[tuple[int, int]] = set()
    for artifact in reopened.value:
        raw_label = artifact.body.get("trial_label")
        if raw_label is None:
            continue
        label = validate_trial_label(raw_label)
        if is_refusal(label):
            return label
        if label.value["study_fp"] != plan.fingerprint.value:
            continue
        generation = label.value["generation_index"]
        ask_index = label.value["ask_index"]
        if type(generation) is not int or type(ask_index) is not int:
            return invalid("trial_label", "reopened study coordinates are exact integers")
        coordinate = (generation, ask_index)
        if coordinate in coordinates_after:
            return policy("trial_label", "one durable terminal remains for every Study ask")
        coordinates_after.add(coordinate)
        assignment = trial_label_assignment(label.value)
        if is_refusal(assignment):
            return assignment
        lineage = _candidate_identity(inputs, plan.bindings, assignment.value, artifact)
        if is_refusal(lineage):
            return lineage
        objective = _objective_value(artifact, plan.objective)
        if is_refusal(objective):
            return objective
        prior = PriorTrial.try_create(
            generation,
            ask_index,
            assignment.value,
            objective.value,
        )
        if is_refusal(prior):
            return prior
        if dict(prior.value.parameters) != assignment.value:
            return policy(
                "assignment", "persisted candidate mapping matches its validated trial label"
            )
        history_after.append(prior.value)
        artifacts_after.append(artifact)
        artifacts_by_coordinate[coordinate] = artifact
    final_resume = resume_stepper(plan.stepper(), history_after)
    if is_refusal(final_resume):
        return final_resume
    final_plan = final_resume.value[1]
    if final_plan.completed_generations != plan.generation_count:
        return unavailable(
            "study_barrier",
            "all generations in the fixed ATC Study budget have checked terminal readback",
            completed_generations=final_plan.completed_generations,
            expected_generations=plan.generation_count,
        )
    grouped: list[list[PriorTrial]] = [[] for _ in range(plan.generation_count)]
    for trial in history_after:
        if trial.generation_index >= len(grouped):
            return policy("generation_index", "no persisted trial exceeds the Study budget")
        grouped[trial.generation_index].append(trial)
    if any(len(generation) != plan.batch_size for generation in grouped):
        return unavailable(
            "study_barrier",
            "each completed generation has its full declared batch of durable trials",
        )
    generation_run = StudyGenerationRun(
        stepper=final_resume.value[0],
        generations=tuple(
            tuple(sorted(items, key=lambda item: item.ask_index)) for items in grouped
        ),
    )
    ordered_artifacts = tuple(
        artifacts_by_coordinate[(generation, ask_index)]
        for generation in range(plan.generation_count)
        for ask_index in range(plan.batch_size)
    )
    occurrence = _record_study_occurrence(inputs, plan, generation_run, ordered_artifacts)
    if is_refusal(occurrence):
        return occurrence
    return Ok(
        OperatorAlternativeStudyResult(
            plan_fingerprint=plan.fingerprint,
            operational_fingerprint=plan.operational_fingerprint,
            generation_run=generation_run,
            terminal_artifacts=ordered_artifacts,
            occurrence_receipt=occurrence.value,
        )
    )
