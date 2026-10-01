"""Pure sample contract for the non-CT32 Alternative sensitivity fold."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from qmb.host.operator_alternative_study import run_operator_alternative_study
from qmb.optimize.alternative_sensitivity import build_operator_alternative_sensitivity
from qmb.optimize.sensitivity import (
    SensitivitySample,
    build_sensitivity_report_from_samples,
)
from qmf.core import UnitKind, World, is_ok, is_refusal
from qmf.data.journal_producer import JournalReader
from test_operator_alternative_study import (  # pyright: ignore[reportPrivateUsage]
    _inputs as _persisted_study_inputs,  # pyright: ignore[reportPrivateUsage]
)
from test_operator_alternative_study import (
    _plan as _persisted_study_plan,  # pyright: ignore[reportPrivateUsage]
)


def _sample(
    trial: str,
    value: int,
    objective: int,
    *,
    world: World = World.REPLAY,
    currency: str | None = None,
    unit_kind: str = UnitKind.COUNT.value,
    taint: str = "optimistic",
) -> SensitivitySample:
    sample = SensitivitySample.try_create(
        trial_id=trial,
        world=world,
        role="trial",
        objective=Fraction(objective),
        unit_kind=unit_kind,
        currency=currency,
        assignment={"candidate_size": value},
        taint=taint,
    )
    assert is_ok(sample), sample
    return sample.value


def test_generic_exact_samples_use_the_same_report_contract_without_ledger_lines() -> None:
    samples = (
        _sample("trial-a", 1, 2),
        _sample("trial-b", 2, 4),
        _sample("trial-c", 3, 6),
    )
    report = build_sensitivity_report_from_samples(
        samples,
        objective="registered-count-objective",
        world=World.REPLAY,
        direction="max",
        role="trial",
    )
    assert is_ok(report)
    assert report.value.analysed_count == 3
    assert report.value.distribution is not None
    assert report.value.distribution.mean == Fraction(4)
    assert report.value.distribution.unit_kind == UnitKind.COUNT.value
    assert [point.value for point in report.value.parameter_slices[0].bins] == [1, 2, 3]
    assert not report.value.makes_edge_claim
    assert not report.value.makes_search_quality_verdict
    assert not report.value.invents_threshold
    assert "ct32" not in str(report.value.fp1_identity()).lower()


def test_generic_exact_samples_refuse_world_unit_taint_and_identity_mixture() -> None:
    replay = _sample("trial-replay", 1, 10)
    live = _sample("trial-live", 2, 20, world=World.LIVE)
    mixed_worlds = build_sensitivity_report_from_samples(
        (replay, live),
        objective="registered-count-objective",
        direction="max",
    )
    assert is_refusal(mixed_worlds)

    usd = _sample("trial-usd", 1, 100, unit_kind=UnitKind.MONEY.value, currency="USD")
    eur = _sample("trial-eur", 2, 100, unit_kind=UnitKind.MONEY.value, currency="EUR")
    mixed_currencies = build_sensitivity_report_from_samples(
        (usd, eur), objective="registered-money-objective", direction="max"
    )
    assert is_refusal(mixed_currencies)

    bad_taint = SensitivitySample.try_create(
        trial_id="trial-taint",
        world=World.REPLAY,
        role="trial",
        objective=1,
        unit_kind=UnitKind.COUNT.value,
        currency=None,
        assignment={"candidate_size": 1},
        taint="unlabelled",
    )
    assert is_refusal(bad_taint)
    duplicate = build_sensitivity_report_from_samples(
        (replay, replay),
        objective="registered-count-objective",
        direction="max",
    )
    assert is_refusal(duplicate)


def test_operator_adapter_reads_actual_completed_atc_terminal_history(
    tmp_path: Path,
) -> None:
    inputs, persistence = _persisted_study_inputs(tmp_path)
    plan = _persisted_study_plan(inputs)
    incomplete = build_operator_alternative_sensitivity(inputs, plan)
    assert is_refusal(incomplete)
    no_effects = JournalReader(inputs.journal_store).read_checked(
        inputs.journal_writer.stream_name, for_world=World.REPLAY
    )
    assert is_ok(no_effects)
    assert no_effects.value == []

    executed = run_operator_alternative_study(inputs, plan)
    assert is_ok(executed), executed
    analysis = build_operator_alternative_sensitivity(inputs, plan)
    assert is_ok(analysis), analysis
    repeated = build_operator_alternative_sensitivity(inputs, plan)
    assert is_ok(repeated), repeated
    assert analysis.value.fingerprint == repeated.value.fingerprint
    assert analysis.value.plan_fingerprint == plan.fingerprint
    assert analysis.value.report.analysed_count == plan.generation_count * plan.batch_size
    assert analysis.value.terminal_artifact_fingerprints == tuple(
        artifact.fingerprint for artifact in executed.value.terminal_artifacts
    )
    assert analysis.value.report.distribution is not None
    assert analysis.value.report.distribution.unit_kind == UnitKind.COUNT.value
    assert "ct32" not in str(analysis.value.fp1_identity()).lower()

    reopened = inputs.terminal_store.read(
        journal_store=inputs.journal_store,
        registry=persistence,
    )
    assert is_ok(reopened)
    assert len(reopened.value) == plan.generation_count * plan.batch_size
