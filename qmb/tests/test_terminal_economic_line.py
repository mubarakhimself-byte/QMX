"""The governed terminal row carries the replay's actual CT-32 measures."""

from __future__ import annotations

from dataclasses import replace
from typing import TypeVar

from qmb.config import ResolvedRunConfig
from qmb.ledger.line import WORKBENCH_LANE_GOVERNED, mint_completed_line
from qmb.results.ct32 import mint_run_performance_result
from qmb.results.measures import ClosedTrade, EquityPoint, TradeSide
from qmb.runloop import STREAM_SET_KEY, SliceObservation, run
from qmf.core.chrono import Instant
from qmf.core.exact import Money
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
