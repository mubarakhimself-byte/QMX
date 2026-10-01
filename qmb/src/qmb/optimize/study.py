"""Bounded generation-barrier driver for QMB studies.

The driver owns only proposal order and the generation barrier. A trial executor
must perform the QMB replay operation and its evidence writes; the driver then
reads that trial back from the caller's QMB ledger view before it can condition
the next generation. It creates no measures, result lines, or scheduler.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final, cast

from qmf.core.refusal import Ok, Result, is_refusal

from qmb._refuse import invalid
from qmb.optimize.sampler import PriorTrial, ProposedTrial, StudyStepper

__all__ = [
    "STUDY_GENERATION_DRIVER_CLASS",
    "STUDY_GENERATION_DRIVER_WRITES_EVIDENCE",
    "StudyGenerationRun",
    "run_study_generations",
]

STUDY_GENERATION_DRIVER_CLASS: Final[str] = "qmb-study-generation-run"
STUDY_GENERATION_DRIVER_WRITES_EVIDENCE: Final[bool] = False


@dataclass(frozen=True, slots=True)
class StudyGenerationRun:
    """Completed bounded generations, each read back from the QMB ledger view."""

    stepper: StudyStepper
    generations: tuple[tuple[PriorTrial, ...], ...]

    @property
    def completed_trials(self) -> tuple[PriorTrial, ...]:
        """All read-back trials in canonical generation and ask order."""
        return tuple(trial for generation in self.generations for trial in generation)

    def fp1_identity(self) -> dict[str, object]:
        """Identity of the barrier result; it is not a winner or promotion verdict."""
        return {
            "class": STUDY_GENERATION_DRIVER_CLASS,
            "completed_generations": [
                [trial.fp1_identity() for trial in generation] for generation in self.generations
            ],
            "generation_count": len(self.generations),
            "study_fp": self.stepper.study_fp.value,
            "writes_evidence": STUDY_GENERATION_DRIVER_WRITES_EVIDENCE,
        }


def run_study_generations(
    stepper: object,
    *,
    generation_count: object,
    execute_trial: object,
    read_trial: object,
) -> Result[StudyGenerationRun]:
    """Execute a fixed number of sequential generations with ledger read-back.

    ``execute_trial(generation_index, proposal, label)`` performs one replay and
    its ordinary QMB evidence writes. After success, ``read_trial(generation,
    ask)`` must return the completed ``PriorTrial`` reconstructed from the QMB
    ledger view. The driver's ``tell`` is reachable only after every ask in the
    generation is present and agrees with the proposal. This port is intentionally
    sequential; bounded process fan-out remains the orchestrator's responsibility.
    """
    if not isinstance(stepper, StudyStepper):
        return invalid(
            "stepper",
            "a Study generation run starts from an admitted StudyStepper",
            given=repr(type(stepper).__name__),
        )
    if stepper.has_outstanding_generation:
        return invalid("stepper", "a Study generation run starts at a closed barrier")
    if isinstance(generation_count, bool) or not isinstance(generation_count, int):
        return invalid("generation_count", "generation_count is a positive integer")
    if generation_count < 1:
        return invalid("generation_count", "generation_count is a positive integer")
    if not callable(execute_trial):
        return invalid("execute_trial", "each proposal is sent to a replay evaluator")
    if not callable(read_trial):
        return invalid("read_trial", "completed trials are read from a QMB ledger view")
    execute = cast(
        "Callable[[int, ProposedTrial, Mapping[str, object]], Result[object]]",
        execute_trial,
    )
    read = cast("Callable[[int, int], Result[object]]", read_trial)

    current = stepper
    generations: list[tuple[PriorTrial, ...]] = []
    for _ in range(generation_count):
        asked = current.ask()
        if is_refusal(asked):
            return asked
        outstanding, batch = asked.value
        labels = outstanding.trial_labels()
        if is_refusal(labels):
            return labels
        if len(labels.value) != batch.size or any(
            label.get("generation_index") != current.generation_index for label in labels.value
        ):
            return invalid("trial_labels", "every proposed ask has exactly one ledger label")

        read_back: list[PriorTrial] = []
        for proposal, label in zip(batch.proposals, labels.value, strict=True):
            executed = execute(current.generation_index, proposal, label)
            if is_refusal(executed):
                return executed
            loaded = read(current.generation_index, proposal.ask_index)
            if is_refusal(loaded):
                return loaded
            if not isinstance(loaded.value, PriorTrial):
                return invalid(
                    "read_trial",
                    "the ledger view reconstructs each completed proposal as PriorTrial",
                    generation_index=current.generation_index,
                    ask_index=proposal.ask_index,
                )
            trial = loaded.value
            if (
                trial.generation_index != current.generation_index
                or trial.ask_index != proposal.ask_index
                or dict(trial.parameters) != proposal.assignment
            ):
                return invalid(
                    "read_trial",
                    "ledger read-back coordinates and exact assignment match the proposal",
                    generation_index=current.generation_index,
                    ask_index=proposal.ask_index,
                )
            read_back.append(trial)
        told = outstanding.tell(read_back)
        if is_refusal(told):
            return told
        generations.append(tuple(read_back))
        current = told.value
    return Ok(StudyGenerationRun(stepper=current, generations=tuple(generations)))
