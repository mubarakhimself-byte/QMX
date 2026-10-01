"""Generation-barrier optimization over durable ATC terminal artifacts.

This driver conditions only on terminal artifacts reopened through the QMB
alternative ledger, their checked CT-13 chains, and CT-07 PolicyPair occurrence
edges. Candidate values are applied to explicitly bound PolicyPair fields; Book,
BMS, bot, CT-32 and Book-R contracts do not enter this path.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import cast

from qmf.core import (
    Ok,
    Result,
    UnitKind,
    World,
    fingerprint,
    is_refusal,
)
from qmf.core.chrono import WriterId
from qmf.core.exact import MONEY_STORAGE_SCALE, Money
from qmf.data.store import JournalStore
from qmf.registry import RegistryPersistence

from qmb._refuse import invalid, policy, unavailable
from qmb.config.alternative import (
    AlternativeRunConfig,
    validate_alternative_run_config,
)
from qmb.execution.alternative import (
    AlternativeInterpreterRegistry,
    AlternativeRunReceipt,
    PolicyInterpreterRegistration,
)
from qmb.execution.alternative_terminal import AlternativeTerminalArtifact, AlternativeTerminalStore
from qmb.host.replay import RecordedReplaySource
from qmb.optimize.resume import resume_stepper
from qmb.optimize.sampler import (
    PriorTrial,
    ProposedTrial,
    StudyStepper,
    trial_label_assignment,
    validate_trial_label,
)
from qmb.optimize.study import StudyGenerationRun, run_study_generations

__all__ = [
    "AlternativeParameterBinding",
    "AlternativeStudyObjective",
    "run_alternative_study",
]

_ExecuteTrial = Callable[
    [
        int,
        ProposedTrial,
        Mapping[str, object],
        AlternativeRunConfig,
        AlternativeInterpreterRegistry,
        RecordedReplaySource,
    ],
    Result[object],
]


@dataclass(frozen=True, slots=True)
class AlternativeParameterBinding:
    """One sampled parameter mapped to one declared PolicyPair field."""

    parameter_name: str
    component: str
    field_name: str

    @classmethod
    def try_create(
        cls, parameter_name: object, component: object, field_name: object
    ) -> Result[AlternativeParameterBinding]:
        if not isinstance(parameter_name, str) or not parameter_name.strip():
            return invalid("parameter_name", "candidate bindings name a Study parameter")
        if component not in {"accounting", "risk"}:
            return invalid("component", "candidate bindings target accounting or risk")
        if not isinstance(field_name, str) or not field_name.strip():
            return invalid("field_name", "candidate bindings name a declared PolicyPair field")
        return Ok(cls(parameter_name.strip(), cast(str, component), field_name.strip()))

    def fp1_identity(self) -> dict[str, object]:
        return {
            "class": "qmb-atc-study-parameter-binding-v1",
            "component": self.component,
            "field_name": self.field_name,
            "parameter_name": self.parameter_name,
        }


@dataclass(frozen=True, slots=True)
class AlternativeStudyObjective:
    """One exact registered ATC measure and its explicit unit/currency and direction."""

    measure_identity: str
    direction: str
    unit_kind: str
    currency: str | None = None

    @classmethod
    def try_create(
        cls,
        measure_identity: object,
        direction: object,
        unit_kind: object,
        currency: object = None,
    ) -> Result[AlternativeStudyObjective]:
        if not isinstance(measure_identity, str) or not measure_identity.strip():
            return invalid("measure_identity", "an ATC objective names a declared measure")
        if direction not in {"min", "max"}:
            return invalid("direction", "an ATC objective declares min or max")
        if not isinstance(unit_kind, str) or unit_kind not in {item.value for item in UnitKind}:
            return invalid("unit_kind", "an ATC objective declares an exact CT-01 unit-kind")
        if unit_kind == UnitKind.MONEY.value:
            if not isinstance(currency, str) or not currency.strip():
                return invalid("currency", "a money-valued objective declares its currency")
            parsed_currency: str | None = currency.strip()
        else:
            if currency is not None:
                return invalid("currency", "a non-money objective carries no currency")
            parsed_currency = None
        return Ok(cls(measure_identity.strip(), cast(str, direction), unit_kind, parsed_currency))

    def fp1_identity(self) -> dict[str, object]:
        body: dict[str, object] = {
            "class": "qmb-atc-study-objective-v1",
            "direction": self.direction,
            "measure_identity": self.measure_identity,
            "unit_kind": self.unit_kind,
        }
        if self.currency is not None:
            body["currency"] = self.currency
        return body


@dataclass(frozen=True, slots=True)
class _Context:
    base_config: AlternativeRunConfig
    registration: PolicyInterpreterRegistration
    source: RecordedReplaySource
    objective: AlternativeStudyObjective
    bindings: tuple[AlternativeParameterBinding, ...]


def _candidate_config(
    base: AlternativeRunConfig,
    assignment: Mapping[str, object],
    bindings: tuple[AlternativeParameterBinding, ...],
) -> Result[AlternativeRunConfig]:
    expected_names = {binding.parameter_name for binding in bindings}
    if set(assignment) != expected_names:
        return invalid("assignment", "proposal exactly covers the declared ATC bindings")
    payload = base.payload()
    pair_value = payload.get("policy_pair")
    if not isinstance(pair_value, Mapping):
        return invalid("policy_pair", "candidate config starts from its typed PolicyPair")
    pair = cast("Mapping[str, object]", pair_value)
    accounting_value, risk_value = pair.get("accounting"), pair.get("risk")
    if not isinstance(accounting_value, Mapping) or not isinstance(risk_value, Mapping):
        return invalid("policy_pair", "candidate config has accounting and risk sections")
    accounting = dict(cast("Mapping[str, object]", accounting_value))
    risk = dict(cast("Mapping[str, object]", risk_value))
    for binding in bindings:
        target = accounting if binding.component == "accounting" else risk
        if binding.field_name not in target:
            return invalid("binding", "candidate field exists in the pinned PolicyPair")
        candidate_value = assignment[binding.parameter_name]
        if isinstance(candidate_value, bool) or not isinstance(candidate_value, (str, int)):
            return unavailable(
                "candidate_value",
                "PolicyPair fields currently admit exact integer or token candidates only",
                parameter=binding.parameter_name,
            )
        target[binding.field_name] = candidate_value
    payload["policy_pair"] = {"accounting": accounting, "risk": risk}
    payload.pop("policy_pair_hash", None)
    payload.pop("composition_fp", None)
    return validate_alternative_run_config(payload)


def _candidate_registry(
    config: AlternativeRunConfig, registration: PolicyInterpreterRegistration
) -> Result[AlternativeInterpreterRegistry]:
    rebound = PolicyInterpreterRegistration.try_create(
        policy_pair_id=config.policy_pair.policy_pair_id,
        policy_pair_version=config.policy_pair.policy_pair_version,
        policy_pair_hash=config.policy_pair.policy_pair_hash,
        interpreter_id=registration.interpreter_id,
        interpreter_version=registration.interpreter_version,
        interpreter_fp1=registration.interpreter_fp1,
        interpreter=registration.interpreter,
        declared_measures=registration.declared_measures,
    )
    if is_refusal(rebound):
        return rebound
    return AlternativeInterpreterRegistry.try_create((rebound.value,))


def _validate_bindings(
    stepper: StudyStepper,
    registration: PolicyInterpreterRegistration,
    objective: AlternativeStudyObjective,
    bindings_value: object,
) -> Result[tuple[AlternativeParameterBinding, ...]]:
    if isinstance(bindings_value, (str, bytes)) or not isinstance(bindings_value, Sequence):
        return invalid("bindings", "ATC optimization has an explicit ordered field mapping")
    bindings: list[AlternativeParameterBinding] = []
    for index, item in enumerate(cast("Sequence[object]", bindings_value)):
        if not isinstance(item, AlternativeParameterBinding):
            return invalid("bindings", "each ATC candidate field mapping is typed", index=index)
        checked = AlternativeParameterBinding.try_create(
            item.parameter_name, item.component, item.field_name
        )
        if is_refusal(checked):
            return checked
        bindings.append(checked.value)
    if not bindings:
        return invalid("bindings", "ATC optimization overrides at least one declared field")
    if len({item.parameter_name for item in bindings}) != len(bindings):
        return invalid("bindings", "each Study parameter has one PolicyPair destination")
    if len({(item.component, item.field_name) for item in bindings}) != len(bindings):
        return invalid("bindings", "each PolicyPair field has one Study parameter")
    if {item.parameter_name for item in bindings} != set(stepper.space.parameter_names):
        return invalid("bindings", "candidate bindings cover the declared Study search space")
    declarations = {item.measure_identity: item for item in registration.declared_measures}
    declared = declarations.get(objective.measure_identity)
    if (
        declared is None
        or declared.unit_kind != objective.unit_kind
        or declared.currency != objective.currency
    ):
        return policy(
            "objective",
            "ATC objective matches a measure declared by the exact registered interpreter",
        )
    if stepper.direction != objective.direction:
        return policy("direction", "Study sampler and ATC objective directions agree")
    return Ok(tuple(bindings))


def _objective_value(
    artifact: AlternativeTerminalArtifact,
    objective: AlternativeStudyObjective,
) -> Result[Fraction]:
    measures = artifact.body.get("final_measures")
    if not isinstance(measures, (tuple, list)):
        return invalid("final_measures", "objective is read from persisted terminal measures")
    matches: list[Mapping[str, object]] = []
    for raw in cast("Sequence[object]", measures):
        if (
            isinstance(raw, Mapping)
            and cast("Mapping[str, object]", raw).get("measure_identity")
            == objective.measure_identity
        ):
            matches.append(cast("Mapping[str, object]", raw))
    if len(matches) != 1:
        return policy(
            "objective", "terminal artifact contains exactly one declared objective measure"
        )
    measure = matches[0]
    if (
        measure.get("unit_kind") != objective.unit_kind
        or measure.get("currency") != objective.currency
    ):
        return policy("objective", "terminal measure unit-kind and currency match the objective")
    quantity = measure.get("quantity")
    if not isinstance(quantity, Mapping):
        return invalid("objective", "objective measure carries an exact quantity identity")
    body = cast("Mapping[str, object]", quantity)
    if objective.unit_kind == UnitKind.MONEY.value:
        if body.get("class") != "money" or body.get("currency") != objective.currency:
            return policy("objective", "money objective carries the declared currency")
        numerator, denominator = body.get("num"), body.get("den")
        if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
            return invalid("objective", "money objective uses an exact rational amount")
        magnitude = Fraction(numerator, denominator)
        scaled = magnitude * 10**MONEY_STORAGE_SCALE
        if scaled.denominator != 1:
            return invalid("objective", "money objective is representable at QMF storage scale")
        verified = Money.try_create(
            scaled.numerator,
            objective.currency,
            MONEY_STORAGE_SCALE,
        )
        if is_refusal(verified) or verified.value.fp1_identity() != dict(body):
            return invalid("objective", "persisted money objective is a canonical QMF Money")
        return Ok(magnitude)
    if body.get("class") != "exact-rational" or body.get("unit_kind") != objective.unit_kind:
        return policy("objective", "rational objective carries the declared CT-01 unit-kind")
    numerator, denominator = body.get("num"), body.get("den")
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        return invalid("objective", "rational objective has exact numerator and denominator")
    return Ok(Fraction(numerator, denominator))


def _artifact_label(artifact: AlternativeTerminalArtifact) -> Result[dict[str, object]]:
    label = artifact.body.get("trial_label")
    if label is None:
        return invalid("trial_label", "optimization terminal artifacts carry their trial label")
    return validate_trial_label(label)


def _find_artifact(
    artifacts: tuple[AlternativeTerminalArtifact, ...],
    *,
    generation: int,
    ask_index: int,
    study_fp: str,
) -> Result[AlternativeTerminalArtifact]:
    matches: list[AlternativeTerminalArtifact] = []
    for artifact in artifacts:
        if artifact.body.get("trial_label") is None:
            continue
        label = _artifact_label(artifact)
        if is_refusal(label):
            return label
        if (
            label.value["generation_index"] == generation
            and label.value["ask_index"] == ask_index
            and label.value["study_fp"] == study_fp
        ):
            matches.append(artifact)
    if len(matches) != 1:
        return policy("trial_readback", "one durable ATC terminal artifact matches the proposal")
    return Ok(matches[0])


def _prior_trial(
    artifact: AlternativeTerminalArtifact,
    *,
    expected_generation: int,
    expected_ask: int,
    study_fp: str,
    objective: AlternativeStudyObjective,
) -> Result[PriorTrial]:
    label = _artifact_label(artifact)
    if is_refusal(label):
        return label
    if (
        label.value["generation_index"] != expected_generation
        or label.value["ask_index"] != expected_ask
        or label.value["study_fp"] != study_fp
    ):
        return policy("trial_label", "terminal trial label matches the resumed Study proposal")
    assignment = trial_label_assignment(label.value)
    if is_refusal(assignment):
        return assignment
    value = _objective_value(artifact, objective)
    if is_refusal(value):
        return value
    return PriorTrial.try_create(expected_generation, expected_ask, assignment.value, value.value)


def _validate_artifact_context(
    artifact: AlternativeTerminalArtifact,
    *,
    context: _Context,
    study_fp: str,
) -> Result[dict[str, object]]:
    label = _artifact_label(artifact)
    if is_refusal(label):
        return label
    if label.value["study_fp"] != study_fp:
        return invalid("trial_label", "ATC terminal belongs to the current optimization Study")
    assignment = trial_label_assignment(label.value)
    if is_refusal(assignment):
        return assignment
    expected_config = _candidate_config(context.base_config, assignment.value, context.bindings)
    if is_refusal(expected_config):
        return expected_config
    body = artifact.body
    if (
        body.get("composition_fp1") != expected_config.value.composition_fp.value
        or body.get("policy_pair_identity") != expected_config.value.policy_pair.identity()
        or body.get("source_fp1") != context.source.fingerprint.value
        or context.source.split_fp1 is None
        or context.source.split_role is None
        or body.get("split_fp1") != context.source.split_fp1.value
        or body.get("split_role") != context.source.split_role.value
    ):
        return policy(
            "candidate_lineage",
            "ATC terminal pins its exact candidate PolicyPair, source, and split lineage",
        )
    registration_body = body.get("interpreter_registration")
    if not isinstance(registration_body, Mapping):
        return invalid("interpreter_registration", "terminal artifact carries registration lineage")
    expected_registry = _candidate_registry(expected_config.value, context.registration)
    if is_refusal(expected_registry):
        return expected_registry
    expected = expected_registry.value.resolve(expected_config.value)
    if is_refusal(expected):
        return expected
    recorded_fp = fingerprint(cast("Mapping[str, object]", registration_body))
    expected_fp = fingerprint(expected.value.identity())
    if is_refusal(recorded_fp) or is_refusal(expected_fp) or recorded_fp.value != expected_fp.value:
        return policy(
            "interpreter_registration", "trial uses the registered code and declared outputs"
        )
    return assignment


def _is_cancelled(cancelled: object) -> Result[bool]:
    if cancelled is None:
        return Ok(False)
    try:
        value = cast("Callable[[], object]", cancelled)()
    except Exception as exc:
        return unavailable(
            "cancelled", "ATC cancellation check completed", exception=type(exc).__name__
        )
    if not isinstance(value, bool):
        return invalid("cancelled", "ATC cancellation callback returns an explicit bool")
    return Ok(value)


def run_alternative_study(
    stepper: object,
    *,
    generation_count: object,
    base_config: object,
    registry: object,
    source: object,
    objective: object,
    bindings: object,
    terminal_store: object,
    journal_store: object,
    registry_persistence: object,
    lineage_writer: object,
    execute_trial: object,
    cancelled: object = None,
) -> Result[StudyGenerationRun]:
    """Run bounded ATC generations with exact candidate binding and durable readback.

    ``execute_trial`` receives ``(generation, proposal, label, candidate_config,
    candidate_registry, source)`` and must return the actual ``AlternativeRunReceipt``.
    Existing terminal labels are read before execution, so a restarted driver never
    reruns a trial already durably completed. Cancellation leaves any partial
    generation in the terminal ledger; a later invocation reconstructs it.
    """
    if not isinstance(stepper, StudyStepper):
        return invalid("stepper", "ATC study starts from a typed StudyStepper")
    if not isinstance(base_config, AlternativeRunConfig):
        return invalid("base_config", "ATC candidate binding starts from AlternativeRunConfig")
    if not isinstance(registry, AlternativeInterpreterRegistry):
        return invalid("registry", "ATC study resolves a typed interpreter registry")
    if (
        not isinstance(source, RecordedReplaySource)
        or source.world is not World.REPLAY
        or source.split_fp1 is None
        or source.split_role is None
    ):
        return invalid("source", "ATC trials consume a validated replay RecordedReplaySource")
    if not isinstance(objective, AlternativeStudyObjective):
        return invalid("objective", "ATC study uses an explicit unit-kind objective")
    if not isinstance(terminal_store, AlternativeTerminalStore):
        return invalid("terminal_store", "ATC study persists terminal artifacts in its QMB store")
    if not isinstance(journal_store, JournalStore) or journal_store.world is not World.REPLAY:
        return invalid("journal_store", "ATC study reopens typed replay CT-13")
    if not isinstance(registry_persistence, RegistryPersistence):
        return invalid("registry_persistence", "ATC study verifies persisted CT-07 edges")
    if registry_persistence.world is not World.REPLAY:
        return invalid("registry_persistence", "ATC study uses replay-world CT-07 lineage")
    if not isinstance(lineage_writer, WriterId):
        return invalid("lineage_writer", "ATC terminal lineage uses a declared WriterId")
    if not callable(execute_trial):
        return invalid(
            "execute_trial", "ATC study delegates each candidate to the registered evaluator"
        )
    if cancelled is not None and not callable(cancelled):
        return invalid("cancelled", "ATC cancellation is a typed polling callback")
    registration = registry.resolve(base_config)
    if is_refusal(registration):
        return registration
    checked_bindings = _validate_bindings(stepper, registration.value, objective, bindings)
    if is_refusal(checked_bindings):
        return checked_bindings
    context = _Context(
        base_config,
        registration.value,
        source,
        objective,
        checked_bindings.value,
    )
    opened = terminal_store.read(journal_store=journal_store, registry=registry_persistence)
    if is_refusal(opened):
        return opened
    study_fp = stepper.study_fp.value
    history: list[PriorTrial] = []
    seen_coordinates: set[tuple[int, int]] = set()
    for artifact in opened.value:
        if artifact.body.get("trial_label") is None:
            continue
        label = _artifact_label(artifact)
        if is_refusal(label):
            return label
        if label.value["study_fp"] != study_fp:
            continue
        assignment = _validate_artifact_context(artifact, context=context, study_fp=study_fp)
        if is_refusal(assignment):
            return assignment
        generation = cast(int, label.value["generation_index"])
        ask_index = cast(int, label.value["ask_index"])
        if (generation, ask_index) in seen_coordinates:
            return policy("trial_label", "an ATC Study has one terminal per generation ask")
        seen_coordinates.add((generation, ask_index))
        prior = _prior_trial(
            artifact,
            expected_generation=generation,
            expected_ask=ask_index,
            study_fp=study_fp,
            objective=objective,
        )
        if is_refusal(prior):
            return prior
        history.append(prior.value)
    resumed = resume_stepper(stepper, history)
    if is_refusal(resumed):
        return resumed
    resumed_stepper = resumed.value[0]

    def execute(
        generation: int,
        proposal: ProposedTrial,
        label: Mapping[str, object],
    ) -> Result[object]:
        cancelled_result = _is_cancelled(cancelled)
        if is_refusal(cancelled_result):
            return cancelled_result
        if cancelled_result.value:
            return unavailable("cancelled", "ATC generation stopped at an explicit cancellation")
        current = terminal_store.read(journal_store=journal_store, registry=registry_persistence)
        if is_refusal(current):
            return current
        prior_artifact = _find_artifact(
            current.value,
            generation=generation,
            ask_index=proposal.ask_index,
            study_fp=study_fp,
        )
        if not is_refusal(prior_artifact):
            return cast(
                "Result[object]",
                _validate_artifact_context(
                    prior_artifact.value,
                    context=context,
                    study_fp=study_fp,
                ),
            )
        candidate = _candidate_config(base_config, proposal.assignment, context.bindings)
        if is_refusal(candidate):
            return candidate
        candidate_registry = _candidate_registry(candidate.value, registration.value)
        if is_refusal(candidate_registry):
            return candidate_registry
        reserved = terminal_store.reserve_trial(
            trial_label=label,
            candidate_fp=candidate.value.fingerprint,
            source_fp=source.fingerprint,
            split_fp=source.split_fp1,
        )
        if is_refusal(reserved):
            return reserved
        try:
            executed = cast(_ExecuteTrial, execute_trial)(
                generation,
                proposal,
                label,
                candidate.value,
                candidate_registry.value,
                source,
            )
        except Exception as exc:
            return unavailable(
                "execute_trial", "ATC candidate evaluator completed", exception=type(exc).__name__
            )
        if is_refusal(executed):
            return executed
        if not isinstance(executed.value, AlternativeRunReceipt):
            return invalid(
                "execute_trial", "candidate evaluator returns an actual AlternativeRunReceipt"
            )
        receipt = executed.value
        if (
            receipt.config.fingerprint != candidate.value.fingerprint
            or receipt.source_fingerprint != source.fingerprint
            or source.split_fp1 is None
            or receipt.split_fingerprint != source.split_fp1
            or receipt.split_role is not source.split_role
        ):
            return policy(
                "candidate_receipt",
                "executed candidate matches the proposal and pinned replay source",
            )
        return cast(
            "Result[object]",
            terminal_store.append(
                receipt,
                journal_store=journal_store,
                registry=registry_persistence,
                lineage_writer=lineage_writer,
                trial_label=label,
            ),
        )

    def read_trial(generation: int, ask_index: int) -> Result[object]:
        current = terminal_store.read(journal_store=journal_store, registry=registry_persistence)
        if is_refusal(current):
            return current
        artifact = _find_artifact(
            current.value,
            generation=generation,
            ask_index=ask_index,
            study_fp=study_fp,
        )
        if is_refusal(artifact):
            return artifact
        assignment = _validate_artifact_context(artifact.value, context=context, study_fp=study_fp)
        if is_refusal(assignment):
            return assignment
        return cast(
            "Result[object]",
            _prior_trial(
                artifact.value,
                expected_generation=generation,
                expected_ask=ask_index,
                study_fp=study_fp,
                objective=objective,
            ),
        )

    return run_study_generations(
        resumed_stepper,
        generation_count=generation_count,
        execute_trial=execute,
        read_trial=read_trial,
    )
