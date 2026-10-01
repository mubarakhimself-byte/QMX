"""The Study adapter reads real replay economics from its durable trial ledger."""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import TypeVar, cast

from qmb.execution.adapters import SLIPPAGE_ADAPTER_ZERO
from qmb.ledger.line import ROLE_TRIAL
from qmb.optimize import (
    StudyCriteria,
    StudyParameterSpace,
    StudyStepper,
    coerce_study_criteria,
    coerce_study_space,
    read_recorded_study_trials,
    run_recorded_study_generations,
)
from qmb.optimize.sampler import trial_label_assignment
from qmb.orchestrator.ledger import read_merge_view
from qmf.core.exact import UnitKind
from qmf.core.fingerprint import World, fingerprint
from qmf.core.refusal import Result, is_ok, is_refusal
from replay_fixture_support import make_recorded_replay_fixture, make_trial_ledger

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _stepper() -> StudyStepper:
    space: StudyParameterSpace = _ok(
        coerce_study_space(
            [
                {
                    "name": "lookback",
                    "type": "exact integer",
                    "unit_kind": UnitKind.COUNT,
                    "bounds": {"min": 1, "max": 12},
                    "step": 1,
                    "default": 4,
                    "ui": "ui-editable",
                },
                {
                    "name": "sma_period",
                    "type": "exact integer",
                    "unit_kind": UnitKind.COUNT,
                    "bounds": {"min": 1, "max": 12},
                    "step": 1,
                    "default": 4,
                    "ui": "ui-editable",
                },
            ]
        )
    )
    return StudyStepper(
        space=space,
        seed=4242,
        direction="max",
        study_fp=_ok(fingerprint({"study": "persisted-replay-adapter"})),
        batch_size=1,
    )


def _criteria() -> StudyCriteria:
    return _ok(
        coerce_study_criteria(
            {"objective": {"measure": "net_profit", "direction": "max"}}
        )
    )


def test_two_generations_run_on_persisted_ct10_and_reopen_trial_economics(
    tmp_path: Path,
) -> None:
    fixture = make_recorded_replay_fixture(tmp_path, slippage_adapter=SLIPPAGE_ADAPTER_ZERO)
    ledger = make_trial_ledger(tmp_path / "study-ledger")
    criteria = _criteria()

    def prepare(generation: int, proposal: object, label: Mapping[str, object]):
        from qmb.optimize.sampler import ProposedTrial

        assert isinstance(proposal, ProposedTrial)
        return fixture.prepare_trial(tmp_path, ledger, generation, proposal, dict(label))

    first = _ok(
        run_recorded_study_generations(
            _stepper(),
            generation_count=1,
            ledger_root=ledger.root,
            criteria=criteria,
            prepare_trial=prepare,
        )
    )
    assert len(first.run.completed_trials) == 1
    assert first.run.completed_trials[0].objective == Fraction(-106)

    # A cancelled resumed ask leaves the first complete durable generation intact.
    cancelled = run_recorded_study_generations(
        _stepper(),
        generation_count=1,
        ledger_root=ledger.root,
        criteria=criteria,
        prepare_trial=prepare,
        cancel_requested=lambda: True,
    )
    assert is_refusal(cancelled)
    assert len(_ok(read_recorded_study_trials(
        ledger.root, study_fp=_stepper().study_fp, criteria=criteria
    ))) == 1

    second = _ok(
        run_recorded_study_generations(
            _stepper(),
            generation_count=1,
            ledger_root=ledger.root,
            criteria=criteria,
            prepare_trial=prepare,
        )
    )
    assert len(second.resumed_trials) == 1
    durable = _ok(
        read_recorded_study_trials(
            ledger.root, study_fp=_stepper().study_fp, criteria=criteria
        )
    )
    assert len(durable) == 2
    assert [trial.generation_index for trial in durable] == [0, 1]
    lines = _ok(read_merge_view(ledger.root, world=World.REPLAY, role=ROLE_TRIAL))
    assert len(lines) == 2
    assert len({line.run_id for line in lines}) == 2
    labels = [cast(Mapping[str, object], line.trial_label) for line in lines]
    assignments = [_ok(trial_label_assignment(label)) for label in labels]
    assert assignments[0] != assignments[1]
    assert all(line.trial_label is not None for line in lines)
    assert all(
        cast(Mapping[str, object], line.trial_label)["role"] == ROLE_TRIAL
        and cast(Mapping[str, object], line.trial_label)["format_version"] == 2
        for line in lines
    )
    for line in lines:
        measures = {
            measure["measure_identity"]: measure
            for measure in line.measures
        }
        net = cast(Mapping[str, object], measures["net_profit"]["quantity"])
        trades = cast(Mapping[str, object], measures["total_trades"]["quantity"])
        assert net["currency"] == "USD" and net["num"] == -106
        assert trades["num"] == 1


def test_one_basis_point_quote_slippage_is_vetoed_without_print_evidence(
    tmp_path: Path,
) -> None:
    fixture = make_recorded_replay_fixture(tmp_path)
    ledger = make_trial_ledger(tmp_path / "constant-percent-control")
    criteria = _criteria()

    def prepare(generation: int, proposal: object, label: Mapping[str, object]):
        from qmb.optimize.sampler import ProposedTrial

        assert isinstance(proposal, ProposedTrial)
        return fixture.prepare_trial(tmp_path, ledger, generation, proposal, dict(label))

    run = _ok(
        run_recorded_study_generations(
            _stepper(),
            generation_count=1,
            ledger_root=ledger.root,
            criteria=criteria,
            prepare_trial=prepare,
        )
    )
    assert run.run.completed_trials[0].objective == Fraction(0)
    lines = _ok(read_merge_view(ledger.root, world=World.REPLAY, role=ROLE_TRIAL))
    assert len(lines) == 1
    measures = {measure["measure_identity"]: measure for measure in lines[0].measures}
    net = cast(Mapping[str, object], measures["net_profit"]["quantity"])
    trades = cast(Mapping[str, object], measures["total_trades"]["quantity"])
    assert net["num"] == 0
    assert trades["num"] == 0
