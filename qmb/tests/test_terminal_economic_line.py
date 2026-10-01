"""The governed terminal row carries the replay's actual CT-32 measures."""

from __future__ import annotations

from dataclasses import replace
from typing import TypeVar

from qmb.config import ASSIGNMENT_KEY, ResolvedRunConfig
from qmb.ledger.line import ROLE_TRIAL, WORKBENCH_LANE_GOVERNED, LedgerLine, mint_completed_line
from qmb.optimize import (
    StudyParameterSpace,
    coerce_study_space,
    propose_generation,
    trial_label,
    trial_label_assignment,
    validate_trial_binding,
)
from qmb.results.ct32 import mint_run_performance_result
from qmb.results.measures import ClosedTrade, EquityPoint, TradeSide
from qmb.runloop import STREAM_SET_KEY, SliceObservation, run
from qmf.core.chrono import Instant
from qmf.core.exact import Money, UnitKind
from qmf.core.fingerprint import World, fingerprint
from qmf.core.refusal import Result, is_ok, is_refusal

T = TypeVar("T")
_NS = 1_700_000_000_000_000_000


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _config() -> ResolvedRunConfig:
    stamp = _ok(fingerprint({"fixture": "terminal-economic-line"}))
    config = ResolvedRunConfig(
        format_version=1,
        book_fp1=stamp,
        bms_fp1=stamp,
        bot_fp1=stamp,
        book_fragment_fp1=stamp,
        bms_fragment_fp1=stamp,
        keys={STREAM_SET_KEY: ("eurusd",)},
        clock="replay",
        data_provenance="recorded",
        world=World.REPLAY,
        fingerprint=stamp,
        binding_fp1=stamp,
    )
    return replace(config, fingerprint=_ok(fingerprint(config.fp1_identity())))


def test_completed_line_preserves_the_supplied_realized_ct32_measures() -> None:
    config = _config()
    start = _ok(Instant.try_create(_NS))
    outcome = _ok(
        run(
            config=config,
            slices=((_ok(SliceObservation.try_create("eurusd", start, True)),),),
        )
    )
    end = outcome.evidence_range.end
    capital = _ok(Money.try_create(1_000_000, "USD", 2))
    net = _ok(Money.try_create(-750, "USD", 2))
    fees = _ok(Money.try_create(150, "USD", 2))
    trade = _ok(ClosedTrade.try_create(net, fees, TradeSide.LONG, end))
    ending = _ok(capital.add(net))
    equity = (
        _ok(EquityPoint.try_create(start, capital)),
        _ok(EquityPoint.try_create(end, ending)),
    )
    artifact = _ok(
        mint_run_performance_result(
            config,
            evidence_range=outcome.evidence_range,
            stream_order=("eurusd",),
            slice_count=1,
            filled_count=1,
            resting_count=0,
            data_points_processed=1,
            outcome_identity=outcome.fp1_identity(),
            trades=(trade,),
            equity_curve=equity,
            starting_capital=capital,
            journal_events=(),
        )
    )
    artifact_fp = _ok(artifact.fingerprint())
    line = _ok(
        mint_completed_line(
            config,
            outcome_identity=outcome.fp1_identity(),
            ct32_fingerprint=artifact_fp,
            performance_result=artifact,
            workbench_lane=WORKBENCH_LANE_GOVERNED,
        )
    )
    assert line.ct32_fingerprint == artifact_fp
    assert line.measures == tuple(item.fp1_identity() for item in artifact.measure_set)

    reconstructed = mint_completed_line(
        config,
        outcome_identity=outcome.fp1_identity(),
        ct32_fingerprint=artifact_fp,
        workbench_lane=WORKBENCH_LANE_GOVERNED,
    )
    assert is_refusal(reconstructed)


def test_malformed_nested_ct32_values_return_refusal_without_raising() -> None:
    config = _config()
    start = _ok(Instant.try_create(_NS))
    outcome = _ok(
        run(
            config=config,
            slices=((_ok(SliceObservation.try_create("eurusd", start, True)),),),
        )
    )
    capital = _ok(Money.try_create(1_000_000, "USD", 2))
    artifact = _ok(
        mint_run_performance_result(
            config,
            evidence_range=outcome.evidence_range,
            stream_order=("eurusd",),
            slice_count=1,
            filled_count=0,
            resting_count=0,
            data_points_processed=1,
            outcome_identity=outcome.fp1_identity(),
            trades=(),
            equity_curve=(_ok(EquityPoint.try_create(start, capital)),),
            starting_capital=capital,
            journal_events=(),
        )
    )
    artifact_fp = _ok(artifact.fingerprint())
    for field in ("result_label", "period", "population"):
        malformed = replace(artifact, **{field: None})
        result = mint_completed_line(
            config,
            outcome_identity=outcome.fp1_identity(),
            ct32_fingerprint=artifact_fp,
            performance_result=malformed,
            workbench_lane=WORKBENCH_LANE_GOVERNED,
        )
        assert is_refusal(result), field


def test_trial_ct32_line_persists_and_reopens_exact_study_label() -> None:
    study_fp = _ok(fingerprint({"study": "terminal-line-label"}))
    space: StudyParameterSpace = _ok(
        coerce_study_space(
            [
                {
                    "name": "lookback",
                    "type": "exact integer",
                    "unit_kind": UnitKind.COUNT,
                    "bounds": {"min": 1, "max": 3},
                    "step": 1,
                    "default": 2,
                    "ui": "ui-editable",
                }
            ]
        )
    )
    batch = _ok(propose_generation(space, 8, [], 0, direction="max", batch_size=1))
    label = _ok(trial_label(study_fp, 8, 0, batch.proposals[0]))
    config = _config()
    assignment = _ok(trial_label_assignment(label))
    keys = {
        **config.keys,
        ASSIGNMENT_KEY: assignment,
        "qmb_study_trial_label": label,
    }
    config = replace(config, keys=keys)
    config = replace(config, fingerprint=_ok(fingerprint(config.fp1_identity())))
    assert is_ok(validate_trial_binding(config, batch.proposals[0], label, generation=0))
    mismatched_config = replace(config, keys={**config.keys, ASSIGNMENT_KEY: {"lookback": 99}})
    assert is_refusal(
        validate_trial_binding(mismatched_config, batch.proposals[0], label, generation=0)
    )

    start = _ok(Instant.try_create(_NS))
    outcome = _ok(
        run(
            config=config,
            slices=((_ok(SliceObservation.try_create("eurusd", start, True)),),),
        )
    )
    capital = _ok(Money.try_create(1_000_000, "USD", 2))
    artifact = _ok(
        mint_run_performance_result(
            config,
            evidence_range=outcome.evidence_range,
            stream_order=("eurusd",),
            slice_count=1,
            filled_count=0,
            resting_count=0,
            data_points_processed=1,
            outcome_identity=outcome.fp1_identity(),
            trades=(),
            equity_curve=(_ok(EquityPoint.try_create(start, capital)),),
            starting_capital=capital,
            journal_events=(),
        )
    )
    artifact_fp = _ok(artifact.fingerprint())
    line = _ok(
        mint_completed_line(
            config,
            outcome_identity=outcome.fp1_identity(),
            ct32_fingerprint=artifact_fp,
            performance_result=artifact,
            role=ROLE_TRIAL,
            workbench_lane=WORKBENCH_LANE_GOVERNED,
        )
    )
    assert line.trial_label == label
    reopened = _ok(LedgerLine.from_mapping(line.fp1_identity()))
    assert reopened.fp1_identity() == line.fp1_identity()
    assert reopened.trial_label == label
