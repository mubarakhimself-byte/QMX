"""The Study driver conditions only after the complete ledger-view barrier."""

from __future__ import annotations

from qmb.optimize import (
    STUDY_GENERATION_DRIVER_WRITES_EVIDENCE,
    PriorTrial,
    StudyStepper,
    coerce_study_space,
    run_study_generations,
)
from qmf.core.exact import UnitKind
from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import Ok, Result, is_ok, is_refusal


def _ok(result: Result[object]) -> object:
    assert is_ok(result), result
    return result.value


def _stepper() -> StudyStepper:
    space = _ok(
        coerce_study_space(
            [
                {
                    "name": "lookback",
                    "type": "exact integer",
                    "unit_kind": UnitKind.COUNT,
                    "bounds": {"min": 2, "max": 12},
                    "step": 2,
                    "default": 6,
                    "ui": "ui-editable",
                }
            ]
        )
    )
    study_fp = _ok(fingerprint({"study": "driver-test"}))
    return StudyStepper(
        space=space,
        seed=17,
        direction="min",
        study_fp=study_fp,
        batch_size=2,
    )


def test_generation_driver_reads_back_every_trial_before_advancing() -> None:
    ledger_view: dict[tuple[int, int], PriorTrial] = {}
    execution_order: list[tuple[int, int]] = []

    def execute(generation: int, proposal: object, label: object) -> Result[object]:
        assert label["generation_index"] == generation
        assignment = proposal.assignment
        execution_order.append((generation, proposal.ask_index))
        ledger_view[(generation, proposal.ask_index)] = _ok(
            PriorTrial.try_create(
                generation,
                proposal.ask_index,
                assignment,
                proposal.ask_index + generation + 1,
            )
        )
        return Ok(None)

    def read_trial(generation: int, ask: int) -> Result[PriorTrial]:
        return Ok(ledger_view[(generation, ask)])

    outcome = _ok(
        run_study_generations(
            _stepper(),
            generation_count=2,
            execute_trial=execute,
            read_trial=read_trial,
        )
    )
    assert execution_order == [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert len(outcome.generations) == 2
    assert outcome.stepper.generation_index == 2
    assert outcome.stepper.has_outstanding_generation is False
    assert len(outcome.completed_trials) == 4
    assert STUDY_GENERATION_DRIVER_WRITES_EVIDENCE is False


def test_generation_driver_does_not_advance_on_unread_trial() -> None:
    outcome = run_study_generations(
        _stepper(),
        generation_count=1,
        execute_trial=lambda *_: Ok(None),
        read_trial=lambda *_: Ok(None),  # type: ignore[arg-type]
    )
    assert is_refusal(outcome)
