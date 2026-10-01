"""Operator-bound ATC study journeys using persisted local replay fixtures."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

import pytest
from qmb._refuse import invalid
from qmb.config.alternative import ADAPTER_INTERNAL_SIMULATE, validate_alternative_run_config
from qmb.execution.alternative import (
    AlternativeEvaluationRequest,
    AlternativeInterpreterRegistry,
    AlternativeMeasure,
    AlternativeMeasureDeclaration,
    AlternativePolicyEvaluation,
    PolicyInterpreterRegistration,
)
from qmb.execution.alternative_terminal import AlternativeTerminalStore
from qmb.host.operator_alternative import OperatorAlternativeInputs
from qmb.host.operator_alternative_study import (
    OperatorAlternativeStudyPlan,
    run_operator_alternative_study,
)
from qmb.host.qma_cli import QmaBacktestContext
from qmb.host.replay import RecordedReplaySource, read_recorded_replay_source
from qmb.optimize.alternative_study import AlternativeParameterBinding, AlternativeStudyObjective
from qmb.optimize.space import coerce_study_space
from qmf.core import (
    CalendarIdentity,
    ExactRational,
    Fingerprint,
    Instant,
    Result,
    UnitKind,
    World,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.core.chrono import WriterId
from qmf.core.exact import RoundingMode
from qmf.data.journal_producer import JournalReader, JournalWriter
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.seal import HoldoutSeal
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener
from qmf.registry import RegistryPersistence

T = TypeVar("T")
_NS = 1_700_000_000_000_000_000


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(label: str) -> Fingerprint:
    return _ok(fingerprint({"class": "operator-alternative-study-test", "label": label}))


def _writer(stream: str, boot: str = "boot-1") -> WriterId:
    return _ok(WriterId.try_create("study-fixture", "qmb", stream, boot))


def _config_payload() -> dict[str, object]:
    return {
        "admission": {
            "checked_grant_ids": ["grant:local-atc"],
            "decided_at_ns": 1_726_747_200_000_000_000,
            "evaluator_principal": "host",
            "health_evidence_ref": "health:local-test",
            "health_revision": 1,
            "observation_freshness": {
                "max_age_ns": 30_000_000_000,
                "observed_at_ns": 1_726_747_170_000_000_000,
            },
        },
        "command": {
            "account_id": "acct:local-atc-study",
            "adapter_capability": ADAPTER_INTERNAL_SIMULATE,
            "command_owner_epoch": 7,
            "instrument": "EURUSD",
            "role": "research",
        },
        "config_class": "alternative",
        "policy_pair": {
            "accounting": {
                "cash_identity": "integer-local-test-v1",
                "currency": "USD",
                "fill_application": "buy-one-unit-at-recorded-ask-v1",
                "position_identity": "one-unit-eurusd-v1",
                "residual_meaning": "whole-integer-units-v1",
                "valuation": "recorded-ask-v1",
            },
            "risk": {
                "halt": "refuse-nonpositive-ask-v1",
                "max_gross": 10,
                "override_principal": "local-test-host",
                "sizing": "one-unit-under-gross-cap-v1",
            },
        },
        "policy_pair_id": "pp:local-study-test",
        "policy_pair_version": 1,
    }


class _LocalStudyInterpreter:
    """Exact local test policy; it has no provider or financial execution effects."""

    calls: int

    def __init__(self) -> None:
        self.calls = 0

    def evaluate(
        self, request: AlternativeEvaluationRequest
    ) -> Result[AlternativePolicyEvaluation]:
        self.calls += 1
        measure = AlternativeMeasure.try_create(
            "observed_frontier_count", _ok(ExactRational.try_create(1, 1, UnitKind.COUNT))
        )
        if is_refusal(measure):
            return measure
        return AlternativePolicyEvaluation.try_create(
            accounting_state=dict(request.prior_accounting_state),
            risk_verdict="local-recorded-policy-accepted",
            risk_accepted=True,
            actions=(),
            measures=(measure.value,),
        )


def _registry() -> AlternativeInterpreterRegistry:
    config = _ok(validate_alternative_run_config(_config_payload()))
    interpreter = _LocalStudyInterpreter()
    registration = _ok(
        PolicyInterpreterRegistration.try_create(
            policy_pair_id=config.policy_pair.policy_pair_id,
            policy_pair_version=config.policy_pair.policy_pair_version,
            policy_pair_hash=config.policy_pair.policy_pair_hash,
            interpreter_id="local-study-interpreter",
            interpreter_version=1,
            interpreter_fp1=_fp("local-interpreter-source"),
            interpreter=interpreter,
            declared_measures=(
                _ok(AlternativeMeasureDeclaration.try_create(
                    "observed_frontier_count", UnitKind.COUNT.value
                )),
            ),
        )
    )
    return _ok(AlternativeInterpreterRegistry.try_create((registration,)))


def _source(tmp_path: Path) -> RecordedReplaySource:
    writer = _writer("ct10-fixture")
    boundary = SourceObservationBoundary(EvidenceStore(tmp_path / "ct10-room"))
    references: list[str] = []
    for index, (side, price) in enumerate((
        ("bid", 1_250_000),
        ("ask", 1_250_020),
    )):
        offset = 500
        at = Instant(value_ns=_NS + offset)
        observation = _ok(
            SourceObservation.try_create(
                event_time=at,
                known_at=at,
                source="local-recorded-study-fixture",
                source_native_id=f"sample-{index}",
                revision="1",
                receive_wall_time=at,
                writer=writer,
                sequence=index,
                world=World.REPLAY,
                foreign_money=_ok(ForeignMoney.try_create(price, 5)),
                market_data=_ok(MarketDataContext.try_create(
                    venue="recorded-local-fixture",
                    symbol="EURUSD",
                    resolution="tick",
                    side=side,
                    license_tag="local-fixture",
                    provenance={"source_kind": "persisted-local-test"},
                )),
            )
        )
        references.append(_ok(boundary.admit(observation)).archive.fingerprint.value)
    calendar = _ok(CalendarIdentity.try_create("study-fixture-calendar", "v1", "2025a"))
    segments = _ok(
        SplitManifest.default_split_segments(
            tuple(Instant(value_ns=_NS + offset) for offset in (1_000, 2_000, 3_000))
        )
    )
    split = _ok(SplitManifest.try_create(
        calendar_identity=calendar,
        segments=segments,
        seal_boundary=_ok(SplitBoundary.try_create(Instant(value_ns=_NS + 3_000))),
        purge_width=0,
        embargo_width=0,
        world=World.REPLAY,
    ))
    seal = _ok(HoldoutSeal.from_manifest(split, 7))
    return _ok(read_recorded_replay_source(
        store_root=tmp_path / "ct10-room",
        archive_fingerprints=tuple(references),
        stream_id="local-study-recorded-source",
        split_manifest=split,
        split_role=SegmentRole.TRAIN,
        holdout_seal=seal,
    ))


def _inputs(tmp_path: Path) -> tuple[OperatorAlternativeInputs, RegistryPersistence]:
    source = _source(tmp_path)
    split_fp = source.split_fp1
    assert split_fp is not None
    journal_root = tmp_path / "ct13-room"
    journal_root.mkdir()
    journal = JournalStore(World.REPLAY, journal_dir=journal_root, open_stream=jsonl_opener())
    journal_writer = _ok(JournalWriter.resume(journal, _writer("study-decisions")))
    registry_persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal_writer = _writer("study-terminal")
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "study-terminal", writer=terminal_writer)
    )
    descriptor = _fp("operator-descriptor")
    context = QmaBacktestContext(
        job_id="qma-local-study-job",
        attempt_id=1,
        experiment_spec_fp1=_fp("ct47-experiment-spec"),
        evidence_ref=_fp("ct12-split-evidence"),
        split_manifest_fp1=split_fp,
        environment_ref="local-replay-fixture",
        occupancy_key="local-study-occupancy",
        mints_ct32=False,
        operator_descriptor_fp1=descriptor,
    )
    inputs = OperatorAlternativeInputs(
        context=context,
        config=_ok(validate_alternative_run_config(_config_payload())),
        recorded_source=source,
        registry=_registry(),
        initial_accounting_state={"cash_units": 100, "position_units": 0},
        expected_command_owner_epoch=7,
        runtime_descriptor_fp1=descriptor,
        registry_as_of=Instant(value_ns=_NS + 3_000),
        registry_writer=_writer("study-registry"),
        raw_store_root=tmp_path / "ct10-room",
        journal_root=journal_root,
        journal_writer=journal_writer,
        journal_store=journal,
        terminal_store=terminal,
        registry_persistence=registry_persistence,
        lineage_writer=_writer("study-lineage"),
    )
    return inputs, registry_persistence


def _plan(inputs: OperatorAlternativeInputs) -> OperatorAlternativeStudyPlan:
    space = _ok(coerce_study_space(({
        "name": "max_gross",
        "type": "exact integer",
        "bounds": {"min": 5, "max": 10},
        "step": 1,
        "default": 10,
        "unit_kind": UnitKind.COUNT,
        "ui": "ui-editable",
    },)))
    return _ok(OperatorAlternativeStudyPlan.try_create(
        inputs,
        parameter_space=space,
        seed=12,
        direction="max",
        rounding=RoundingMode.HALF_EVEN,
        batch_size=2,
        generation_count=1,
        objective=_ok(AlternativeStudyObjective.try_create(
            "observed_frontier_count", "max", UnitKind.COUNT.value
        )),
        bindings=(_ok(AlternativeParameterBinding.try_create(
            "max_gross", "risk", "max_gross"
        )),),
    ))


def test_operator_study_runs_registered_policy_and_reopens_fixed_generation_budget(
    tmp_path: Path,
) -> None:
    inputs, persistence = _inputs(tmp_path)
    plan = _plan(inputs)

    completed = _ok(run_operator_alternative_study(inputs, plan))

    assert completed.plan_fingerprint == plan.fingerprint
    assert len(completed.generation_run.generations) == 1
    assert len(completed.generation_run.generations[0]) == 2
    assert len(completed.terminal_artifacts) == 2
    assert all(
        artifact.body["composition_class"] == "alternative"
        for artifact in completed.terminal_artifacts
    )
    assert all(
        "ct32" not in str(artifact.identity()).lower()
        for artifact in completed.terminal_artifacts
    )

    rows_before = len(_ok(JournalReader(inputs.journal_store).read_checked(
        inputs.journal_writer.stream_name, for_world=World.REPLAY
    )))
    resumed = _ok(run_operator_alternative_study(inputs, plan))
    rows_after = len(_ok(JournalReader(inputs.journal_store).read_checked(
        inputs.journal_writer.stream_name, for_world=World.REPLAY
    )))
    assert rows_after == rows_before
    assert tuple(item.fingerprint for item in resumed.terminal_artifacts) == tuple(
        item.fingerprint for item in completed.terminal_artifacts
    )
    reopened = _ok(inputs.terminal_store.read(
        journal_store=inputs.journal_store, registry=persistence
    ))
    assert len(reopened) == 2



def test_operator_study_rejects_placeholder_source_and_mutated_plan_before_effects(
    tmp_path: Path,
) -> None:
    inputs, _ = _inputs(tmp_path)
    plan = _plan(inputs)
    before = _ok(JournalReader(inputs.journal_store).read_checked(
        inputs.journal_writer.stream_name, for_world=World.REPLAY
    ))
    placeholder = replace(inputs, raw_store_root=tmp_path / "unmaterialized-source")
    refused_placeholder = run_operator_alternative_study(placeholder, plan)
    assert is_refusal(refused_placeholder)
    assert not (tmp_path / "unmaterialized-source").exists()

    changed_plan = replace(plan, generation_count=True)
    refused_plan = run_operator_alternative_study(inputs, changed_plan)
    assert is_refusal(refused_plan)
    changed_seed_state = replace(
        inputs,
        initial_accounting_state={"cash_units": 101, "position_units": 0},
    )
    refused_seed_state = run_operator_alternative_study(changed_seed_state, plan)
    assert is_refusal(refused_seed_state)
    malformed_objective = replace(plan.objective, unit_kind=True)
    refused_objective = run_operator_alternative_study(
        inputs, replace(plan, objective=malformed_objective)
    )
    assert is_refusal(refused_objective)
    after = _ok(JournalReader(inputs.journal_store).read_checked(
        inputs.journal_writer.stream_name, for_world=World.REPLAY
    ))
    assert after == before == []


def test_operator_study_resumes_partial_generation_without_replaying_terminal_trial(
    tmp_path: Path,
) -> None:
    inputs, persistence = _inputs(tmp_path)
    plan = _plan(inputs)
    registration = next(iter(inputs.registry.registrations.values()))
    interpreter = cast("_LocalStudyInterpreter", registration.interpreter)

    def stop_after_first_terminal() -> bool:
        return interpreter.calls > 0

    interrupted = run_operator_alternative_study(
        inputs, plan, cancelled=stop_after_first_terminal
    )
    assert is_refusal(interrupted)
    first_readback = _ok(inputs.terminal_store.read(
        journal_store=inputs.journal_store, registry=persistence
    ))
    assert len(first_readback) == 1
    assert interpreter.calls == 1

    completed = _ok(run_operator_alternative_study(inputs, plan))
    assert len(completed.terminal_artifacts) == 2
    assert interpreter.calls == 2


def test_operator_study_computational_identity_reuses_history_across_qma_attempts(
    tmp_path: Path,
) -> None:
    inputs, _ = _inputs(tmp_path)
    plan = _plan(inputs)
    first = _ok(run_operator_alternative_study(inputs, plan))
    registration = next(iter(inputs.registry.registrations.values()))
    interpreter = cast("_LocalStudyInterpreter", registration.interpreter)
    calls_after_first = interpreter.calls

    next_context = replace(
        inputs.context,
        job_id="qma-next-study-job",
        attempt_id=2,
        environment_ref="another-local-replay-fixture",
        occupancy_key="next-local-study-occupancy",
    )
    next_inputs = replace(inputs, context=next_context)
    next_plan = _plan(next_inputs)
    assert next_plan.fingerprint == plan.fingerprint
    assert next_plan.operational_fingerprint != plan.operational_fingerprint

    resumed = _ok(run_operator_alternative_study(next_inputs, next_plan))
    assert interpreter.calls == calls_after_first
    assert resumed.plan_fingerprint == first.plan_fingerprint
    assert resumed.operational_fingerprint == next_plan.operational_fingerprint
    assert resumed.occurrence_receipt.identity != first.occurrence_receipt.identity
    assert tuple(item.fingerprint for item in resumed.terminal_artifacts) == tuple(
        item.fingerprint for item in first.terminal_artifacts
    )
    checked = _ok(JournalReader(inputs.journal_store).read_checked(
        inputs.journal_writer.stream_name, for_world=World.REPLAY
    ))
    occurrence_events = [
        event for event in checked
        if event.payload.get("kind") == "qmb-operator-terminal-occurrence-v1"
    ]
    assert len(occurrence_events) == 2


def test_operator_study_recovers_reserved_before_start_after_restart(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, _ = _inputs(tmp_path)
    plan = _plan(inputs)
    registration = next(iter(inputs.registry.registrations.values()))
    interpreter = cast("_LocalStudyInterpreter", registration.interpreter)
    original_start = AlternativeTerminalStore.start_trial
    fail_once = True

    def stop_before_start(self: AlternativeTerminalStore, **kwargs: object) -> Result[None]:
        nonlocal fail_once
        if fail_once:
            fail_once = False
            return invalid("injected", "stop after reservation before evaluator start")
        return original_start(self, **kwargs)

    monkeypatch.setattr(AlternativeTerminalStore, "start_trial", stop_before_start)
    first = run_operator_alternative_study(inputs, plan)
    assert is_refusal(first)
    assert interpreter.calls == 0
    pending = _ok(inputs.terminal_store.pending_trials())
    assert len(pending) == 1
    assert next(iter(pending.values()))["_started"] is False

    monkeypatch.setattr(AlternativeTerminalStore, "start_trial", original_start)
    recovered = _ok(run_operator_alternative_study(inputs, plan))
    assert len(recovered.terminal_artifacts) == 2
    assert interpreter.calls == 2


def test_operator_study_blocks_started_trial_without_complete_effect_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, _ = _inputs(tmp_path)
    plan = _plan(inputs)
    registration = next(iter(inputs.registry.registrations.values()))
    interpreter = cast("_LocalStudyInterpreter", registration.interpreter)
    original_start = AlternativeTerminalStore.start_trial

    def lose_start_ack(self: AlternativeTerminalStore, **kwargs: object) -> Result[None]:
        written = original_start(self, **kwargs)
        if is_refusal(written):
            return written
        return invalid("injected", "start marker persisted but its acknowledgement was lost")

    monkeypatch.setattr(AlternativeTerminalStore, "start_trial", lose_start_ack)
    first = run_operator_alternative_study(inputs, plan)
    assert is_refusal(first)
    assert interpreter.calls == 0
    pending = _ok(inputs.terminal_store.pending_trials())
    assert len(pending) == 1
    assert next(iter(pending.values()))["_started"] is True

    monkeypatch.setattr(AlternativeTerminalStore, "start_trial", original_start)
    restart = run_operator_alternative_study(inputs, plan)
    assert is_refusal(restart)
    assert interpreter.calls == 0
    assert len(_ok(inputs.terminal_store.pending_trials())) == 1


def test_operator_study_terminal_readback_recovers_lost_append_ack_without_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, _ = _inputs(tmp_path)
    plan = _plan(inputs)
    registration = next(iter(inputs.registry.registrations.values()))
    interpreter = cast("_LocalStudyInterpreter", registration.interpreter)
    original_append = AlternativeTerminalStore.append
    lose_ack = True

    def append_then_lose_ack(
        self: AlternativeTerminalStore,
        *args: object,
        **kwargs: object,
    ) -> Result[object]:
        nonlocal lose_ack
        written = original_append(self, *args, **kwargs)
        if is_refusal(written):
            return written
        if lose_ack:
            lose_ack = False
            return invalid("injected", "terminal and CT-07 evidence were written before lost ACK")
        return cast("Result[object]", written)

    monkeypatch.setattr(AlternativeTerminalStore, "append", append_then_lose_ack)
    first = run_operator_alternative_study(inputs, plan)
    assert is_refusal(first)
    assert interpreter.calls == 1
    first_artifacts = _ok(inputs.terminal_store.read(
        journal_store=inputs.journal_store,
        registry=inputs.registry_persistence,
    ))
    assert len(first_artifacts) == 1

    monkeypatch.setattr(AlternativeTerminalStore, "append", original_append)
    resumed = _ok(run_operator_alternative_study(inputs, plan))
    assert len(resumed.terminal_artifacts) == 2
    assert interpreter.calls == 2
