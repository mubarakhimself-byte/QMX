"""Sequential parameter studies over the governed recorded-replay service.

Every trial is an ordinary QMB replay with a config fingerprint that includes the
validated study/generation/ask label. Its completed CT-32 is written through the
role=trial LedgerSink and then read back before the sampler may tell a generation.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Final, cast

from qmf.core import Fingerprint, Ok, Result, World, is_refusal
from qmf.data.journal_producer import JournalReader

from qmb._refuse import invalid, policy
from qmb.config.compiler import ASSIGNMENT_KEY, STUDY_TRIAL_LABEL_KEY, ResolvedRunConfig
from qmb.execution.binder import BoundExecution
from qmb.host.book_handler import BookAdmissionContext
from qmb.host.replay_request import ResolvedReplayRequest
from qmb.ledger.line import ROLE_TRIAL, LedgerLine
from qmb.optimize.objective import StudyCriteria, compute_winner_set
from qmb.optimize.sampler import (
    PriorTrial,
    ProposedTrial,
    StudyStepper,
    trial_label_assignment,
    validate_trial_label,
)
from qmb.optimize.study import StudyGenerationRun, run_study_generations
from qmb.orchestrator.ledger import LedgerSink, read_merge_view

__all__ = [
    "RECORDED_STUDY_ADAPTER_CLASS",
    "RecordedStudyRun",
    "ReplayTrialBindings",
    "read_recorded_study_trials",
    "run_recorded_study_generations",
    "validate_trial_binding",
]

RECORDED_STUDY_ADAPTER_CLASS: Final[str] = "qmb-recorded-study-adapter"


@dataclass(frozen=True, slots=True)
class ReplayTrialBindings:
    """Trusted per-candidate ports prepared from the proposal and its trial label."""

    request: ResolvedReplayRequest
    expected_split_fp1: Fingerprint
    request_root: Path
    raw_store_root: Path
    holdout_months: int
    config: ResolvedRunConfig
    bound_execution: BoundExecution
    admission: BookAdmissionContext
    journal_reader: JournalReader
    ledger: LedgerSink
    initial_resting: object = ()
    cancel: object = None
    limits: object = None
    probe: object = None


@dataclass(frozen=True, slots=True)
class RecordedStudyRun:
    """Generations whose economic objectives were read from durable trial lines."""

    stepper: StudyStepper
    run: StudyGenerationRun
    resumed_trials: tuple[PriorTrial, ...]

    def fp1_identity(self) -> dict[str, object]:
        return {
            "class": RECORDED_STUDY_ADAPTER_CLASS,
            "completed": [trial.fp1_identity() for trial in self.run.completed_trials],
            "resumed": [trial.fp1_identity() for trial in self.resumed_trials],
            "study_fp": self.stepper.study_fp.value,
        }


def read_recorded_study_trials(
    ledger_root: object,
    *,
    study_fp: object,
    criteria: object,
) -> Result[tuple[PriorTrial, ...]]:
    """Project exact prior trials from role=trial CT-32 ledger rows for one Study."""
    parsed_fp = _as_fingerprint(study_fp)
    if is_refusal(parsed_fp):
        return parsed_fp
    if not isinstance(criteria, StudyCriteria):
        return invalid("criteria", "the recorded study reader receives admitted StudyCriteria")
    lines = read_merge_view(ledger_root, world=World.REPLAY, role=ROLE_TRIAL)
    if is_refusal(lines):
        return lines
    selected: list[LedgerLine] = []
    labels: dict[str, dict[str, object]] = {}
    coordinates: set[tuple[int, int]] = set()
    for line in lines.value:
        if line.trial_label is None:
            continue
        label = validate_trial_label(line.trial_label)
        if is_refusal(label):
            return label
        if label.value.get("study_fp") != parsed_fp.value.value:
            continue
        if line.refusal is not None or line.ct32_fingerprint is None:
            return policy(
                "trial_line",
                "a recorded Study prior is a completed role=trial line with CT-32",
                run_id=line.run_id.value,
            )
        generation = cast(int, label.value["generation_index"])
        ask = cast(int, label.value["ask_index"])
        coordinate = (generation, ask)
        if coordinate in coordinates:
            return policy(
                "trial_label", "Study trial coordinates are unique", coordinate=coordinate
            )
        coordinates.add(coordinate)
        labels[line.run_id.value] = label.value
        selected.append(line)
    if not selected:
        return Ok(())
    winner_set = compute_winner_set(selected, criteria, world=World.REPLAY, role=ROLE_TRIAL)
    if is_refusal(winner_set):
        return winner_set
    scored = (*winner_set.value.winners, *winner_set.value.excluded)
    by_run_id = {trial.run_id.value: trial for trial in scored}
    incomplete = {trial.run_id.value: trial for trial in winner_set.value.incomplete}
    output: list[PriorTrial] = []
    for line in selected:
        label = labels[line.run_id.value]
        scored_trial = by_run_id.get(line.run_id.value)
        if scored_trial is None:
            incomplete_trial = incomplete.get(line.run_id.value)
            return policy(
                "objective",
                "a completed replay produces a defined exact objective before sampler conditioning",
                run_id=line.run_id.value,
                incomplete_reason=(
                    incomplete_trial.reason if incomplete_trial is not None else "missing-score"
                ),
            )
        parameters = trial_label_assignment(label)
        if is_refusal(parameters):
            return parameters
        trial = PriorTrial.try_create(
            label["generation_index"],
            label["ask_index"],
            parameters.value,
            Fraction(scored_trial.objective_num, scored_trial.objective_den),
        )
        if is_refusal(trial):
            return trial
        output.append(trial.value)
    output.sort(key=lambda trial: trial.sort_key)
    return Ok(tuple(output))


def run_recorded_study_generations(
    stepper: object,
    *,
    generation_count: object,
    ledger_root: object,
    criteria: object,
    prepare_trial: object,
    cancel_requested: object = None,
) -> Result[RecordedStudyRun]:
    """Resume and run sequential recorded trials, reading every objective back first.

    ``prepare_trial(generation, proposal, label)`` is a trusted host callback. It
    compiles the candidate config with ``study_trial_label=label`` and returns the
    already-resolved CT-10/12 replay request, real QMF execution ports, and the
    role=trial LedgerSink. Existing durable trials are reused only when both their
    config run id and exact persisted label match the deterministic proposal.
    """
    if not isinstance(stepper, StudyStepper):
        return invalid("stepper", "recorded replay starts from an admitted StudyStepper")
    if not isinstance(criteria, StudyCriteria):
        return invalid("criteria", "recorded replay uses admitted StudyCriteria")
    if stepper.direction != criteria.objective.direction:
        return policy("direction", "sampler and CT-32 objective direction agree")
    if not callable(prepare_trial):
        return invalid("prepare_trial", "each candidate resolves its recorded replay context")
    if cancel_requested is not None and not callable(cancel_requested):
        return invalid("cancel_requested", "cancellation is checked through a trusted callback")
    history = read_recorded_study_trials(ledger_root, study_fp=stepper.study_fp, criteria=criteria)
    if is_refusal(history):
        return history
    from qmb.optimize.resume import resume_stepper  # noqa: PLC0415

    resumed = resume_stepper(stepper, history.value)
    if is_refusal(resumed):
        return resumed
    base_stepper, _resume_plan = resumed.value
    bindings: dict[tuple[int, int], tuple[ReplayTrialBindings, dict[str, object]]] = {}

    def prepare(
        generation: int, proposal: ProposedTrial, label: Mapping[str, object]
    ) -> Result[ReplayTrialBindings]:
        prepared = cast(
            "Callable[[int, ProposedTrial, Mapping[str, object]], Result[object]]", prepare_trial
        )(generation, proposal, label)
        if is_refusal(prepared):
            return prepared
        parsed = _as_bindings(prepared.value, generation, proposal, label)
        if is_refusal(parsed):
            return parsed
        bindings[(generation, proposal.ask_index)] = (parsed.value, dict(label))
        return Ok(parsed.value)

    def execute(
        generation: int,
        proposal: ProposedTrial,
        label: Mapping[str, object],
    ) -> Result[object]:
        if cancel_requested is not None and cast(Callable[[], object], cancel_requested)():
            return policy(
                "study_cancelled",
                "the Study stops at this ask boundary; prior durable trials remain resumable",
                generation_index=generation,
                ask_index=proposal.ask_index,
            )
        prepared = prepare(generation, proposal, label)
        if is_refusal(prepared):
            return prepared
        existing = _read_trial_for_bindings(prepared.value, criteria, label)
        if is_refusal(existing):
            return existing
        if existing.value is not None:
            return Ok(existing.value)
        from qmb.host.replay_execution import execute_recorded_replay_request  # noqa: PLC0415

        executed = execute_recorded_replay_request(
            request=prepared.value.request,
            expected_request_ref=prepared.value.request.request_ref,
            request_root=prepared.value.request_root,
            raw_store_root=prepared.value.raw_store_root,
            holdout_months=prepared.value.holdout_months,
            expected_split_fp1=prepared.value.expected_split_fp1,
            config=prepared.value.config,
            bound_execution=prepared.value.bound_execution,
            admission=prepared.value.admission,
            journal_reader=prepared.value.journal_reader,
            terminal_ledger=prepared.value.ledger,
            trial_proposal=proposal,
            trial_label=label,
            trial_generation=generation,
            initial_resting=prepared.value.initial_resting,
            cancel=prepared.value.cancel,
            limits=prepared.value.limits,
            probe=prepared.value.probe,
            role=ROLE_TRIAL,
        )
        if is_refusal(executed):
            return executed
        if executed.value.terminal_line.trial_label is None:
            return policy(
                "trial_label", "the durable CT-13/32 trial line retains the exact Study label"
            )
        return Ok(executed.value.terminal_line)

    def read_trial(generation: int, ask: int) -> Result[object]:
        prepared = bindings.get((generation, ask))
        if prepared is None:
            return invalid("trial_bindings", "the proposal's resolved replay context is retained")
        loaded = _read_trial_for_bindings(prepared[0], criteria, prepared[1])
        if is_refusal(loaded):
            return loaded
        if loaded.value is None:
            return invalid(
                "trial_line", "the executed or resumed ask has durable role=trial output"
            )
        return Ok(cast(object, loaded.value))

    driven = run_study_generations(
        base_stepper,
        generation_count=generation_count,
        execute_trial=execute,
        read_trial=read_trial,
    )
    if is_refusal(driven):
        return driven
    all_history = read_recorded_study_trials(
        ledger_root, study_fp=stepper.study_fp, criteria=criteria
    )
    if is_refusal(all_history):
        return all_history
    if len(all_history.value) < len(driven.value.stepper.completed):
        return policy("trial_history", "durable read-back retains the resumed and new trials")
    return Ok(
        RecordedStudyRun(
            stepper=driven.value.stepper,
            run=driven.value,
            resumed_trials=history.value,
        )
    )


def _read_trial_for_bindings(
    bindings: ReplayTrialBindings,
    criteria: StudyCriteria,
    label: Mapping[str, object],
) -> Result[PriorTrial | None]:
    lines = read_merge_view(bindings.ledger.root, world=World.REPLAY, role=ROLE_TRIAL)
    if is_refusal(lines):
        return lines
    matches = [line for line in lines.value if line.run_id == bindings.config.fingerprint]
    if not matches:
        return Ok(None)
    if len(matches) != 1:
        return policy("trial_line", "one exact run id has one merged trial line")
    line = matches[0]
    expected = validate_trial_label(label)
    actual = validate_trial_label(line.trial_label)
    if is_refusal(expected):
        return expected
    if is_refusal(actual):
        return actual
    if dict(actual.value) != dict(expected.value) or line.refusal is not None:
        return policy("trial_label", "durable trial coordinates and assignment match the proposal")
    winners = compute_winner_set((line,), criteria, world=World.REPLAY, role=ROLE_TRIAL)
    if is_refusal(winners):
        return winners
    scored = (*winners.value.winners, *winners.value.excluded)
    if len(scored) != 1:
        return policy(
            "objective",
            "a durable trial has one defined exact objective before sampler conditioning",
            run_id=line.run_id.value,
        )
    parameters = trial_label_assignment(actual.value)
    if is_refusal(parameters):
        return parameters
    trial = PriorTrial.try_create(
        actual.value["generation_index"],
        actual.value["ask_index"],
        parameters.value,
        Fraction(scored[0].objective_num, scored[0].objective_den),
    )
    if is_refusal(trial):
        return trial
    return Ok(trial.value)


def _as_bindings(
    value: object,
    generation: int,
    proposal: ProposedTrial,
    label: Mapping[str, object],
) -> Result[ReplayTrialBindings]:
    if not isinstance(value, ReplayTrialBindings):
        return invalid(
            "trial_bindings", "a candidate resolves typed Book and CT-13 execution ports"
        )
    request: object = cast(object, value.request)
    config: object = cast(object, value.config)
    bound: object = cast(object, value.bound_execution)
    admission: object = cast(object, value.admission)
    reader: object = cast(object, value.journal_reader)
    ledger: object = cast(object, value.ledger)
    expected_split_fp1: object = cast(object, value.expected_split_fp1)
    if (
        not isinstance(request, ResolvedReplayRequest)
        or not isinstance(config, ResolvedRunConfig)
        or not isinstance(bound, BoundExecution)
        or not isinstance(admission, BookAdmissionContext)
        or not isinstance(reader, JournalReader)
        or not isinstance(ledger, LedgerSink)
        or not isinstance(expected_split_fp1, Fingerprint)
        or config.world is not World.REPLAY
    ):
        return invalid("trial_bindings", "candidate execution inputs are resolved QMB/QMF values")
    if (
        expected_split_fp1 != value.request.split_fp1
        or expected_split_fp1 != value.request.source.split_fp1
    ):
        return policy(
            "split_fp1", "candidate CT-12 data_ref matches the request and persisted source"
        )
    checked = validate_trial_binding(value.config, proposal, label, generation=generation)
    if is_refusal(checked):
        return checked
    if value.bound_execution.config != value.config:
        return policy("bound_execution", "candidate QMF execution ports bind to its exact config")
    return Ok(value)


def validate_trial_binding(
    config: object,
    proposal: object,
    label: object,
    *,
    generation: object,
) -> Result[None]:
    """Require compiled CT-33 assignment and durable label to match one exact ask."""
    if not isinstance(config, ResolvedRunConfig) or not isinstance(proposal, ProposedTrial):
        return invalid("trial_binding", "a compiled config binds one typed sampler proposal")
    parsed_generation = _non_negative_int(generation, "generation")
    if is_refusal(parsed_generation):
        return parsed_generation
    stored_label = validate_trial_label(config.keys.get(STUDY_TRIAL_LABEL_KEY))
    proposed_label = validate_trial_label(label)
    if is_refusal(stored_label):
        return stored_label
    if is_refusal(proposed_label):
        return proposed_label
    if dict(stored_label.value) != dict(proposed_label.value):
        return policy("trial_label", "the resolved run-config identity carries the exact ask label")
    assignment = trial_label_assignment(proposed_label.value)
    if is_refusal(assignment):
        return assignment
    resolved_assignment = config.keys.get(ASSIGNMENT_KEY)
    if not isinstance(resolved_assignment, Mapping):
        return invalid(
            "assignment",
            "recorded Study execution uses the exact resolved CT-33 parameter assignment",
        )
    if (
        assignment.value != proposal.assignment
        or dict(cast("Mapping[str, object]", resolved_assignment)) != proposal.assignment
        or proposed_label.value["generation_index"] != parsed_generation.value
    ):
        return policy("assignment", "compiled candidate assignment and proposal coordinates agree")
    return Ok(None)


def _non_negative_int(value: object, field: str) -> Result[int]:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return invalid(field, "a Study coordinate is a non-negative exact integer")
    return Ok(value)


def _as_fingerprint(value: object) -> Result[Fingerprint]:
    if isinstance(value, Fingerprint):
        return Ok(value)
    return Fingerprint.try_create(value)
