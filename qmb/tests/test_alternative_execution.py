"""Registered ATC execution over persisted CT-10 and CT-13 replay evidence.

The interpreter below defines a deliberately test-local exact policy vocabulary. It
does not define QMX's illustrative fixed-fraction finance semantics or connect to a
provider; the source observations and journal writes use real QMF persistence APIs.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import TypeVar, cast

import pytest
from qmb._refuse import invalid
from qmb.config.alternative import (
    ADAPTER_INTERNAL_SIMULATE,
    ALTERNATIVE_CONFIG_CLASS,
    AlternativeRunConfig,
    validate_alternative_run_config,
)
from qmb.execution import alternative_terminal as alternative_terminal_module
from qmb.execution.alternative import (
    AlternativeEvaluationRequest,
    AlternativeInterpreterRegistry,
    AlternativeMeasure,
    AlternativeMeasureDeclaration,
    AlternativePolicyEvaluation,
    ATCJournalReference,
    InternalSimulatedAction,
    PolicyInterpreterRegistration,
    execute_alternative_run,
)
from qmb.execution.alternative_terminal import (
    AlternativeTerminalArtifact,
    AlternativeTerminalStore,
)
from qmb.host.replay import RecordedReplaySource, read_recorded_replay_source
from qmb.optimize.alternative_study import (
    AlternativeParameterBinding,
    AlternativeStudyObjective,
    run_alternative_study,
)
from qmb.optimize.sampler import ProposedTrial, StudyStepper
from qmb.optimize.space import coerce_study_space
from qmf.core import (
    CalendarIdentity,
    ExactRational,
    Instant,
    Money,
    Ok,
    Result,
    UnitKind,
    World,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.core.chrono import WriterId
from qmf.data.journal import DecisionOutcome, JournalEventType
from qmf.data.journal_producer import JournalAppendReceipt, JournalReader, JournalWriter
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.seal import HoldoutSeal
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener
from qmf.registry import RegistryPersistence

T = TypeVar("T")
_NS = 1_700_000_000_000_000_000
_DECISION_NS = 1_726_747_200_000_000_000
_OBSERVED_NS = _DECISION_NS - 30_000_000_000
_MAX_AGE_NS = 30_000_000_000


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _accounting() -> dict[str, object]:
    return {
        "cash_identity": "integer-test-usd-units-v1",
        "currency": "USD",
        "fill_application": "buy-one-unit-at-recorded-ask-v1",
        "position_identity": "one-unit-eurusd-v1",
        "residual_meaning": "whole-integer-units-v1",
        "valuation": "recorded-ask-v1",
    }


def _risk() -> dict[str, object]:
    return {
        "halt": "refuse-nonpositive-ask-v1",
        "max_gross": 10_000_000,
        "override_principal": "test-host",
        "sizing": "one-unit-under-gross-cap-v1",
    }


def _config_payload(**overrides: object) -> dict[str, object]:
    command: dict[str, object] = {
        "account_id": "acct:recorded-test",
        "adapter_capability": ADAPTER_INTERNAL_SIMULATE,
        "command_owner_epoch": 18,
        "instrument": "EURUSD",
        "role": "research",
    }
    admission: dict[str, object] = {
        "checked_grant_ids": ["grant:atc-sim"],
        "decided_at_ns": _DECISION_NS,
        "evaluator_principal": "host",
        "health_evidence_ref": "health:atc-recorded-test",
        "health_revision": 4,
        "observation_freshness": {
            "max_age_ns": _MAX_AGE_NS,
            "observed_at_ns": _OBSERVED_NS,
        },
    }
    body: dict[str, object] = {
        "admission": admission,
        "command": command,
        "config_class": ALTERNATIVE_CONFIG_CLASS,
        "policy_pair": {"accounting": _accounting(), "risk": _risk()},
        "policy_pair_id": "pp:recorded-exact-v1",
        "policy_pair_version": 1,
    }
    body.update(overrides)
    return body


def _writer() -> WriterId:
    return _ok(WriterId.try_create("test-host", "qmb", "atc-recorded", "boot-1"))


def _observation(side: str, sequence: int, price: int) -> SourceObservation:
    return _ok(
        SourceObservation.try_create(
            event_time=Instant(value_ns=_NS),
            known_at=Instant(value_ns=_NS),
            source="local-ct10-atc-fixture",
            source_native_id=f"quote-{side}-1",
            revision="1",
            receive_wall_time=Instant(value_ns=_NS),
            writer=_writer(),
            sequence=sequence,
            world=World.REPLAY,
            foreign_money=_ok(ForeignMoney.try_create(price, 5)),
            market_data=_ok(
                MarketDataContext.try_create(
                    venue="fixture-venue",
                    symbol="EURUSD",
                    resolution="tick",
                    side=side,
                    license_tag="local-fixture",
                    provenance={"source_kind": "persisted-test-fixture"},
                )
            ),
        )
    )


def _split() -> tuple[SplitManifest, HoldoutSeal]:
    calendar = _ok(CalendarIdentity.try_create("atc-fixture-calendar", "v1", "2025a"))
    segments = _ok(
        SplitManifest.default_split_segments(
            tuple(Instant(value_ns=_NS + offset) for offset in (1_000, 2_000, 3_000))
        )
    )
    manifest = _ok(
        SplitManifest.try_create(
            calendar_identity=calendar,
            segments=segments,
            seal_boundary=_ok(SplitBoundary.try_create(Instant(value_ns=_NS + 3_000))),
            purge_width=0,
            embargo_width=0,
            world=World.REPLAY,
        )
    )
    return manifest, _ok(HoldoutSeal.from_manifest(manifest, 18))


def study_fixture_writer() -> WriterId:
    """Public shared-fixture access to this module's canonical writer."""
    return _writer()


def study_fixture_split() -> tuple[SplitManifest, HoldoutSeal]:
    """Public shared-fixture access to this module's persisted split contract."""
    return _split()


STUDY_FIXTURE_EPOCH_NS = _NS


def _source(tmp_path: Path):
    boundary = SourceObservationBoundary(EvidenceStore(tmp_path / "ct10-room"))
    refs = tuple(
        _ok(boundary.admit(_observation(side, index, price))).archive.fingerprint.value
        for index, (side, price) in enumerate((("bid", 1_234_500), ("ask", 1_234_520)))
    )
    split, seal = _split()
    return _ok(
        read_recorded_replay_source(
            store_root=tmp_path / "ct10-room",
            archive_fingerprints=refs,
            stream_id="eurusd-recorded-atc",
            split_manifest=split,
            split_role=SegmentRole.TRAIN,
            holdout_seal=seal,
        )
    )


class _TestExactInterpreter:
    """An explicit test grammar using exact integer CT-10 prices and accounting."""

    def evaluate(
        self, request: AlternativeEvaluationRequest
    ) -> Result[AlternativePolicyEvaluation]:
        accounting = request.config.policy_pair.accounting
        risk = request.config.policy_pair.risk
        if (
            accounting.get("fill_application") != "buy-one-unit-at-recorded-ask-v1"
            or accounting.get("valuation") != "recorded-ask-v1"
            or risk.get("sizing") != "one-unit-under-gross-cap-v1"
            or not isinstance(risk.get("max_gross"), int)
        ):
            return invalid("test_policy", "the explicitly registered test grammar matches")
        sides = {item.market_data.side: item for item in request.observations if item.market_data}
        bid = sides["bid"].foreign_money
        ask = sides["ask"].foreign_money
        if bid is None or ask is None or ask.scale != bid.scale:
            return invalid("test_quote", "recorded bid and ask share their exact source scale")
        prior_cash = request.prior_accounting_state.get("cash_units")
        prior_position = request.prior_accounting_state.get("position_units")
        if not isinstance(prior_cash, int) or not isinstance(prior_position, int):
            return invalid("test_state", "the test accounting state contains exact integer units")
        max_gross = risk.get("max_gross")
        assert isinstance(max_gross, int)
        accepted = 0 < ask.verbatim <= max_gross
        next_state = {
            "cash_units": prior_cash - ask.verbatim if accepted else prior_cash,
            "position_units": prior_position + 1 if accepted else prior_position,
        }
        ending_equity = next_state["cash_units"] + next_state["position_units"] * ask.verbatim
        measure = AlternativeMeasure.try_create(
            "end_equity",
            _ok(Money.try_create(ending_equity, "USD", 0)),
        )
        if is_refusal(measure):
            return measure
        accepted_measure = AlternativeMeasure.try_create(
            "accepted_entry",
            _ok(ExactRational.try_create(int(accepted), 1, UnitKind.COUNT)),
        )
        if is_refusal(accepted_measure):
            return accepted_measure
        actions: tuple[InternalSimulatedAction, ...] = ()
        if accepted:
            action = InternalSimulatedAction.try_create(
                action_id=f"buy-at-{request.frontier.value_ns}",
                action_type="recorded-quote-buy-one-unit",
                body={
                    "ask_raw": ask.verbatim,
                    "price_scale": ask.scale,
                    "source_observation_fp1": sides["ask"].fingerprint.value,
                    "units": 1,
                },
            )
            if is_refusal(action):
                return action
            actions = (action.value,)
        return Ok(
            AlternativePolicyEvaluation(
                accounting_state=next_state,
                risk_verdict="within-gross-cap" if accepted else "gross-cap-refused",
                risk_accepted=accepted,
                actions=actions,
                measures=(measure.value, accepted_measure.value),
            )
        )


def _registry() -> AlternativeInterpreterRegistry:
    config = _ok(validate_alternative_run_config(_config_payload()))
    impl_fp = _ok(fingerprint({"class": "test-exact-interpreter", "version": 1}))
    registration = _ok(
        PolicyInterpreterRegistration.try_create(
            policy_pair_id=config.policy_pair.policy_pair_id,
            policy_pair_version=config.policy_pair.policy_pair_version,
            policy_pair_hash=config.policy_pair.policy_pair_hash,
            interpreter_id="test-exact-quote-interpreter",
            interpreter_version=1,
            interpreter_fp1=impl_fp,
            interpreter=_TestExactInterpreter(),
            declared_measures=(
                _ok(
                    AlternativeMeasureDeclaration.try_create(
                        "end_equity", UnitKind.MONEY.value, "USD"
                    )
                ),
                _ok(
                    AlternativeMeasureDeclaration.try_create("accepted_entry", UnitKind.COUNT.value)
                ),
            ),
        )
    )
    return _ok(AlternativeInterpreterRegistry.try_create((registration,)))


def _journal(tmp_path: Path) -> tuple[JournalStore, JournalWriter]:
    journal = JournalStore(
        World.REPLAY,
        journal_dir=tmp_path / "ct13-room",
        open_stream=jsonl_opener(),
    )
    return journal, _ok(JournalWriter.resume(journal, _writer()))


def test_registered_exact_atc_runs_on_persisted_ct10_and_reopens_ct13(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    journal, writer = _journal(tmp_path)
    receipt = _ok(
        execute_alternative_run(
            _config_payload(),
            source,
            _registry(),
            initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
            expected_command_owner_epoch=18,
            journal_writer=writer,
            journal_store=journal,
        )
    )
    assert receipt.split_role is SegmentRole.TRAIN
    assert receipt.final_accounting_state == {"cash_units": 765_480, "position_units": 1}
    assert len(receipt.final_measures) == 2
    assert receipt.final_measures[0].measure_identity == "end_equity"
    assert receipt.final_measures[0].quantity == _ok(Money.try_create(2_000_000, "USD", 0))
    assert receipt.final_measures[1].measure_identity == "accepted_entry"
    assert receipt.final_measures[1].quantity == _ok(ExactRational.try_create(1, 1, UnitKind.COUNT))
    assert len(receipt.journal_references) == 1
    reference = receipt.journal_references[0]
    assert isinstance(reference, ATCJournalReference)
    reopened = _ok(JournalReader(journal).read_checked(writer.stream_name, for_world=World.REPLAY))
    assert len(reopened) == 1
    event = reopened[0]
    assert event.event_type is JournalEventType.DECISION
    assert event.outcome is DecisionOutcome.AUTHORIZED
    assert event.fingerprint == reference.event_fingerprint
    assert event.payload["composition_class"] == "alternative"
    assert event.payload["recorded_source_fp1"] == source.fingerprint.value
    stored_measures = cast("tuple[object, ...]", event.payload["measures"])
    assert len(stored_measures) == 2
    assert stored_measures[0] == receipt.final_measures[0].fp1_identity()
    assert "ct32" not in str(event.payload).lower()
    assert receipt.fp1_identity()["source_fp1"] == source.fingerprint.value


def test_atc_terminal_artifact_reopens_ct13_and_ct07_lineage(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    journal, writer = _journal(tmp_path)
    receipt = _ok(
        execute_alternative_run(
            _config_payload(),
            source,
            _registry(),
            initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
            expected_command_owner_epoch=18,
            journal_writer=writer,
            journal_store=journal,
        )
    )
    persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal_writer = _ok(WriterId.try_create("test-host", "qmb", "atc-terminal-lineage", "boot-1"))
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=_writer())
    )
    stored = _ok(
        terminal.append(
            receipt,
            journal_store=journal,
            registry=persistence,
            lineage_writer=terminal_writer,
        )
    )
    assert stored.body["composition_class"] == "alternative"
    assert stored.identity()["final_measures"] == [
        measure.fp1_identity() for measure in receipt.final_measures
    ]
    assert "ct32" not in str(stored.identity()).lower()

    persistence.close()
    reopened_registry = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    reopened = _ok(terminal.read(journal_store=journal, registry=reopened_registry))
    assert len(reopened) == 1
    assert reopened[0].fingerprint == stored.fingerprint
    assert reopened[0].run_receipt_fingerprint == receipt.fingerprint
    assert (
        _ok(
            terminal.append(
                receipt,
                journal_store=journal,
                registry=reopened_registry,
                lineage_writer=terminal_writer,
            )
        ).fingerprint
        == stored.fingerprint
    )


def test_atc_terminal_read_refuses_tampered_ct13_reference_and_missing_ct07_edge(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    journal, writer = _journal(tmp_path)
    receipt = _ok(
        execute_alternative_run(
            _config_payload(),
            source,
            _registry(),
            initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
            expected_command_owner_epoch=18,
            journal_writer=writer,
            journal_store=journal,
        )
    )
    persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=_writer())
    )
    no_edge = terminal.read(journal_store=journal, registry=persistence)
    assert is_ok(no_edge)
    assert no_edge.value == ()
    changed_ref = replace(
        receipt.journal_references[0],
        store_fingerprint=_ok(fingerprint({"forged": "physical-row"})),
    )
    forged_receipt = replace(receipt, journal_references=(changed_ref,))
    refused = terminal.append(
        forged_receipt,
        journal_store=journal,
        registry=persistence,
        lineage_writer=_ok(
            WriterId.try_create("test-host", "qmb", "atc-terminal-lineage", "boot-1")
        ),
    )
    assert is_refusal(refused)
    assert _ok(terminal.read(journal_store=journal, registry=persistence)) == ()


def _alternative_study_stepper() -> StudyStepper:
    space = _ok(
        coerce_study_space(
            [
                {
                    "name": "max_gross",
                    "type": "exact integer",
                    "bounds": {"min": 1_000_000, "max": 1_500_000},
                    "step": 100_000,
                    "default": 1_300_000,
                    "unit_kind": UnitKind.COUNT,
                    "ui": "ui-editable",
                }
            ]
        )
    )
    return StudyStepper(
        space=space,
        seed=17,
        direction="max",
        study_fp=_ok(fingerprint({"class": "atc-study-test", "version": 1})),
        batch_size=2,
    )


def test_alternative_study_applies_candidate_reopens_units_and_resumes_partial_generation(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    journal, study_writer = _journal(tmp_path)
    base_config = _ok(validate_alternative_run_config(_config_payload()))
    registry = _registry()
    registry_persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal_writer = _ok(WriterId.try_create("test-host", "qmb", "atc-terminal-ledger", "boot-1"))
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=terminal_writer)
    )
    lineage_writer = _ok(WriterId.try_create("test-host", "qmb", "atc-terminal-lineage", "boot-1"))
    bindings = (_ok(AlternativeParameterBinding.try_create("max_gross", "risk", "max_gross")),)
    objective = _ok(
        AlternativeStudyObjective.try_create("accepted_entry", "max", UnitKind.COUNT.value)
    )
    executed_coordinates: list[tuple[int, int]] = []

    def execute_trial(
        generation: int,
        proposal: ProposedTrial,
        label: Mapping[str, object],
        candidate_config: AlternativeRunConfig,
        candidate_registry: AlternativeInterpreterRegistry,
        replay_source: RecordedReplaySource,
        stream: JournalWriter,
    ) -> Result[object]:
        assert replay_source is source
        assignment = proposal.assignment
        ask_index = proposal.ask_index
        assert candidate_config.policy_pair.risk["max_gross"] == assignment["max_gross"]
        assert label["generation_index"] == generation
        executed_coordinates.append((generation, ask_index))
        return cast(
            "Result[object]",
            execute_alternative_run(
                candidate_config,
                replay_source,
                candidate_registry,
                initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
                expected_command_owner_epoch=18,
                journal_writer=stream,
                journal_store=journal,
                trial_label=label,
            ),
        )

    def cancelled() -> bool:
        return len(executed_coordinates) == 1

    partial = run_alternative_study(
        _alternative_study_stepper(),
        generation_count=1,
        base_config=base_config,
        registry=registry,
        source=source,
        objective=objective,
        bindings=bindings,
        terminal_store=terminal,
        journal_store=journal,
        registry_persistence=registry_persistence,
        lineage_writer=lineage_writer,
        execute_trial=execute_trial,
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        journal_writer=study_writer,
        cancelled=cancelled,
    )
    assert is_refusal(partial)
    assert len(executed_coordinates) == 1
    assert len(_ok(terminal.read(journal_store=journal, registry=registry_persistence))) == 1

    completed = _ok(
        run_alternative_study(
            _alternative_study_stepper(),
            generation_count=1,
            base_config=base_config,
            registry=registry,
            source=source,
            objective=objective,
            bindings=bindings,
            terminal_store=terminal,
            journal_store=journal,
            registry_persistence=registry_persistence,
            lineage_writer=lineage_writer,
            execute_trial=execute_trial,
            initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
            journal_writer=study_writer,
        )
    )
    assert len(completed.completed_trials) == 2
    assert len(executed_coordinates) == 2
    assert {trial.objective for trial in completed.completed_trials} == {Fraction(0), Fraction(1)}
    artifacts = _ok(terminal.read(journal_store=journal, registry=registry_persistence))
    assert len(artifacts) == 2
    assert source.split_fp1 is not None
    assert all(item.body["split_fp1"] == source.split_fp1.value for item in artifacts)
    assert all(item.body["source_fp1"] == source.fingerprint.value for item in artifacts)
    for generation, ask_index in executed_coordinates:
        events = _ok(
            JournalReader(journal).read_checked(study_writer.stream_name, for_world=World.REPLAY)
        )
        matching: list[AlternativeTerminalArtifact] = []
        for item in artifacts:
            label = cast("Mapping[str, object]", item.body["trial_label"])
            if label["generation_index"] == generation and label["ask_index"] == ask_index:
                matching.append(item)
        assert len(matching) == 1
        artifact = matching[0]
        assert events
        artifact_label_fp = _ok(fingerprint(artifact.body["trial_label"]))
        labeled_events = [event for event in events if event.payload.get("trial_label") is not None]
        assert any(
            _ok(fingerprint(event.payload["trial_label"])) == artifact_label_fp
            for event in labeled_events
        )
    assert "ct32" not in str([item.identity() for item in artifacts]).lower()


def test_alternative_study_refuses_objective_unit_mismatch_before_trial(tmp_path: Path) -> None:
    source = _source(tmp_path)
    journal, study_writer = _journal(tmp_path)
    base_config = _ok(validate_alternative_run_config(_config_payload()))
    registry = _registry()
    registry_persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=_writer())
    )

    def must_not_execute(*_args: object) -> Result[object]:
        pytest.fail("unit mismatch must refuse before execution")

    result = run_alternative_study(
        _alternative_study_stepper(),
        generation_count=1,
        base_config=base_config,
        registry=registry,
        source=source,
        objective=_ok(
            AlternativeStudyObjective.try_create(
                "accepted_entry", "max", UnitKind.DIMENSIONLESS_RATIO.value
            )
        ),
        bindings=(_ok(AlternativeParameterBinding.try_create("max_gross", "risk", "max_gross")),),
        terminal_store=terminal,
        journal_store=journal,
        registry_persistence=registry_persistence,
        lineage_writer=_writer(),
        execute_trial=must_not_execute,
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        journal_writer=study_writer,
    )
    assert is_refusal(result)
    assert _ok(terminal.read(journal_store=journal, registry=registry_persistence)) == ()


def test_terminal_failure_reservation_prevents_evaluator_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source(tmp_path)
    journal, study_writer = _journal(tmp_path)
    config = _ok(validate_alternative_run_config(_config_payload()))
    registry = _registry()
    registry_persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=_writer())
    )
    lineage_writer = _ok(WriterId.try_create("test-host", "qmb", "lineage", "boot-1"))
    bindings = (_ok(AlternativeParameterBinding.try_create("max_gross", "risk", "max_gross")),)
    objective = _ok(AlternativeStudyObjective.try_create("accepted_entry", "max", "count"))
    calls: list[tuple[int, int]] = []

    def execute_trial(
        generation: int,
        proposal: ProposedTrial,
        label: Mapping[str, object],
        candidate: AlternativeRunConfig,
        candidate_registry: AlternativeInterpreterRegistry,
        replay_source: RecordedReplaySource,
        stream: JournalWriter,
    ) -> Result[object]:
        calls.append((generation, proposal.ask_index))
        return cast(
            "Result[object]",
            execute_alternative_run(
                candidate,
                replay_source,
                candidate_registry,
                initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
                expected_command_owner_epoch=18,
                journal_writer=stream,
                journal_store=journal,
                trial_label=label,
            ),
        )

    kwargs: dict[str, object] = {
        "generation_count": 1,
        "base_config": config,
        "registry": registry,
        "source": source,
        "objective": objective,
        "bindings": bindings,
        "terminal_store": terminal,
        "journal_store": journal,
        "registry_persistence": registry_persistence,
        "lineage_writer": lineage_writer,
        "execute_trial": execute_trial,
        "initial_accounting_state": {"cash_units": 2_000_000, "position_units": 0},
        "journal_writer": study_writer,
    }
    original_append = AlternativeTerminalStore.append

    def fail_terminal(*_args: object, **_kwargs: object) -> Result[object]:
        return invalid("injected", "terminal persistence failed after actual CT-13 effects")

    monkeypatch.setattr(AlternativeTerminalStore, "append", fail_terminal)
    first = run_alternative_study(_alternative_study_stepper(), **kwargs)
    assert is_refusal(first)
    assert calls == [(0, 0)]
    assert len(
        _ok(JournalReader(journal).read_checked(study_writer.stream_name, for_world=World.REPLAY))
    ) == 1

    monkeypatch.setattr(AlternativeTerminalStore, "append", original_append)
    restarted_id = _ok(
        WriterId.try_create("test-host", "qmb", study_writer.stream_name, "boot-2")
    )
    restarted_writer = _ok(JournalWriter.resume(journal, restarted_id))
    kwargs["journal_writer"] = restarted_writer
    _ok(run_alternative_study(_alternative_study_stepper(), **kwargs))
    assert calls == [(0, 0), (0, 1)]
    assert len(_ok(terminal.pending_trials())) == 0
    recovered_artifacts = _ok(terminal.read(journal_store=journal, registry=registry_persistence))
    assert len(recovered_artifacts) == 2
    assert cast("Mapping[str, object]", recovered_artifacts[0].body["journal_writer"])[
        "boot_epoch_id"
    ] == "boot-1"
    assert cast("Mapping[str, object]", recovered_artifacts[1].body["journal_writer"])[
        "boot_epoch_id"
    ] == "boot-2"
    events = _ok(
        JournalReader(journal).read_checked(
            restarted_writer.stream_name, for_world=World.REPLAY
        )
    )
    reopened = _ok(terminal.read(journal_store=journal, registry=registry_persistence))
    first_label_fp = _ok(fingerprint(reopened[0].body["trial_label"]))
    assert sum(
        _ok(fingerprint(event.payload.get("trial_label"))) == first_label_fp for event in events
    ) == 1


def test_incomplete_trial_intent_stays_blocked_and_preintent_failure_has_no_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source(tmp_path)
    journal, study_writer = _journal(tmp_path)
    config = _ok(validate_alternative_run_config(_config_payload()))
    registry = _registry()
    registry_persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=_writer())
    )
    calls: list[int] = []

    def interrupted(
        generation: int,
        proposal: ProposedTrial,
        _label: Mapping[str, object],
        _candidate: AlternativeRunConfig,
        _candidate_registry: AlternativeInterpreterRegistry,
        _source: RecordedReplaySource,
        _writer: JournalWriter,
    ) -> Result[object]:
        calls.append(proposal.ask_index)
        return invalid("injected", "worker stopped before any CT-13 decision")

    kwargs: dict[str, object] = {
        "generation_count": 1,
        "base_config": config,
        "registry": registry,
        "source": source,
        "objective": _ok(AlternativeStudyObjective.try_create("accepted_entry", "max", "count")),
        "bindings": (
            _ok(AlternativeParameterBinding.try_create("max_gross", "risk", "max_gross")),
        ),
        "terminal_store": terminal,
        "journal_store": journal,
        "registry_persistence": registry_persistence,
        "lineage_writer": _writer(),
        "execute_trial": interrupted,
        "initial_accounting_state": {"cash_units": 2_000_000, "position_units": 0},
        "journal_writer": study_writer,
    }
    original_reserve = AlternativeTerminalStore.reserve_trial

    def fail_before_intent(*_args: object, **_kwargs: object) -> Result[None]:
        return invalid("injected", "intent persistence failed before evaluator invocation")

    monkeypatch.setattr(AlternativeTerminalStore, "reserve_trial", fail_before_intent)
    assert is_refusal(run_alternative_study(_alternative_study_stepper(), **kwargs))
    assert calls == []
    assert _ok(terminal.pending_trials()) == {}
    assert (
        _ok(
            JournalReader(journal).read_checked(
                study_writer.stream_name, for_world=World.REPLAY
            )
        )
        == []
    )

    monkeypatch.setattr(AlternativeTerminalStore, "reserve_trial", original_reserve)
    assert is_refusal(run_alternative_study(_alternative_study_stepper(), **kwargs))
    assert calls == [0]
    assert len(_ok(terminal.pending_trials())) == 1
    assert (
        _ok(
            JournalReader(journal).read_checked(
                study_writer.stream_name, for_world=World.REPLAY
            )
        )
        == []
    )

    def must_not_retry(*_args: object) -> Result[object]:
        pytest.fail("an unresolved post-intent trial must not replay its evaluator")

    kwargs["execute_trial"] = must_not_retry
    assert is_refusal(run_alternative_study(_alternative_study_stepper(), **kwargs))
    assert calls == [0]
    assert len(_ok(terminal.pending_trials())) == 1


def test_terminal_row_written_before_error_is_read_back_without_reexecution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source(tmp_path)
    journal, study_writer = _journal(tmp_path)
    config = _ok(validate_alternative_run_config(_config_payload()))
    registry = _registry()
    registry_persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=_writer())
    )
    calls: list[int] = []

    def execute_trial(
        generation: int,
        proposal: ProposedTrial,
        label: Mapping[str, object],
        candidate: AlternativeRunConfig,
        candidate_registry: AlternativeInterpreterRegistry,
        replay_source: RecordedReplaySource,
        writer: JournalWriter,
    ) -> Result[object]:
        calls.append(proposal.ask_index)
        return cast(
            "Result[object]",
            execute_alternative_run(
                candidate,
                replay_source,
                candidate_registry,
                initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
                expected_command_owner_epoch=18,
                journal_writer=writer,
                journal_store=journal,
                trial_label=label,
            ),
        )

    kwargs: dict[str, object] = {
        "generation_count": 1,
        "base_config": config,
        "registry": registry,
        "source": source,
        "objective": _ok(AlternativeStudyObjective.try_create("accepted_entry", "max", "count")),
        "bindings": (
            _ok(AlternativeParameterBinding.try_create("max_gross", "risk", "max_gross")),
        ),
        "terminal_store": terminal,
        "journal_store": journal,
        "registry_persistence": registry_persistence,
        "lineage_writer": _writer(),
        "execute_trial": execute_trial,
        "initial_accounting_state": {"cash_units": 2_000_000, "position_units": 0},
        "journal_writer": study_writer,
    }
    original_append = AlternativeTerminalStore.append
    injected = False

    def append_then_refuse(
        self: AlternativeTerminalStore, *args: object, **kwargs_: object
    ) -> Result[object]:
        nonlocal injected
        result = original_append(self, *args, **kwargs_)
        if not injected:
            injected = True
            return invalid("injected", "terminal JSONL and CT-07 edge were written before lost ACK")
        return cast("Result[object]", result)

    monkeypatch.setattr(AlternativeTerminalStore, "append", append_then_refuse)
    assert is_refusal(run_alternative_study(_alternative_study_stepper(), **kwargs))
    assert calls == [0]
    assert len(_ok(terminal.read(journal_store=journal, registry=registry_persistence))) == 1

    monkeypatch.setattr(AlternativeTerminalStore, "append", original_append)
    restarted_writer = _ok(JournalWriter.resume(journal, study_writer.writer))
    kwargs["journal_writer"] = restarted_writer
    completed = _ok(run_alternative_study(_alternative_study_stepper(), **kwargs))
    assert calls == [0, 1]
    assert len(completed.completed_trials) == 2
    events = _ok(
        JournalReader(journal).read_checked(
            restarted_writer.stream_name, for_world=World.REPLAY
        )
    )
    assert len(events) == 2
    assert len(_ok(terminal.read(journal_store=journal, registry=registry_persistence))) == 2


def test_terminal_chain_uses_physical_row_after_fresh_writer_boot(tmp_path: Path) -> None:
    source = _source(tmp_path)
    journal, _ = _journal(tmp_path)
    registry_persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=_writer())
    )
    lineage_writer = _ok(WriterId.try_create("test-host", "qmb", "lineage", "boot-1"))
    config = _ok(validate_alternative_run_config(_config_payload()))
    for boot in ("boot-1", "boot-2"):
        writer_id = _ok(WriterId.try_create("test-host", "qmb", "atc-recorded", boot))
        writer = _ok(JournalWriter.resume(journal, writer_id))
        receipt = _ok(
            execute_alternative_run(
                config,
                source,
                _registry(),
                initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
                expected_command_owner_epoch=18,
                journal_writer=writer,
                journal_store=journal,
            )
        )
        _ok(
            terminal.append(
                receipt,
                journal_store=journal,
                registry=registry_persistence,
                lineage_writer=lineage_writer,
            )
        )
    artifacts = _ok(terminal.read(journal_store=journal, registry=registry_persistence))
    assert len(artifacts) == 2
    refs = cast("Sequence[object]", artifacts[1].body["journal_refs"])
    second_ref = cast("Mapping[str, object]", refs[0])
    assert second_ref["sequence"] == 0
    assert second_ref["store_sequence"] == 1


def test_terminal_recovers_edge_written_before_terminal_jsonl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source(tmp_path)
    journal, writer = _journal(tmp_path)
    config = _ok(validate_alternative_run_config(_config_payload()))
    registry = _registry()
    registry_persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "registry-room"), World.REPLAY)
    )
    terminal = _ok(
        AlternativeTerminalStore.try_create(tmp_path / "alternative-ledger", writer=_writer())
    )
    lineage_writer = _ok(WriterId.try_create("test-host", "qmb", "lineage", "boot-1"))
    receipt = _ok(
        execute_alternative_run(
            config,
            source,
            registry,
            initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
            expected_command_owner_epoch=18,
            journal_writer=writer,
            journal_store=journal,
        )
    )
    original_write = alternative_terminal_module.append_bytes_no_follow
    interrupted = False

    def fail_terminal_jsonl(
        path: Path, data: bytes, *, contain_within: Path, field: str = "path"
    ) -> Result[None]:
        nonlocal interrupted
        if b'"class":"qmb-alternative-terminal-row-v1"' in data and not interrupted:
            interrupted = True
            return invalid("injected", "CT-07 edge was durable before terminal-row write")
        return original_write(path, data, contain_within=contain_within, field=field)

    monkeypatch.setattr(alternative_terminal_module, "append_bytes_no_follow", fail_terminal_jsonl)
    assert is_refusal(
        terminal.append(
            receipt,
            journal_store=journal,
            registry=registry_persistence,
            lineage_writer=lineage_writer,
        )
    )
    assert interrupted
    assert _ok(terminal.read(journal_store=journal, registry=registry_persistence)) == ()
    edges = _ok(
        registry_persistence.read_edges(
            alternative_terminal_module.ALTERNATIVE_TERMINAL_EDGE_STREAM,
            for_world=World.REPLAY,
        )
    )
    assert len(edges) == 1

    monkeypatch.setattr(alternative_terminal_module, "append_bytes_no_follow", original_write)
    artifact = _ok(
        terminal.append(
            receipt,
            journal_store=journal,
            registry=registry_persistence,
            lineage_writer=lineage_writer,
        )
    )
    assert len(_ok(terminal.read(journal_store=journal, registry=registry_persistence))) == 1
    assert len(
        _ok(
            registry_persistence.read_edges(
                alternative_terminal_module.ALTERNATIVE_TERMINAL_EDGE_STREAM,
                for_world=World.REPLAY,
            )
        )
    ) == 1
    assert artifact.run_receipt_fingerprint == receipt.fingerprint


def test_atc_requires_exact_interpreter_key_before_writing(tmp_path: Path) -> None:
    source = _source(tmp_path)
    journal, writer = _journal(tmp_path)
    result = execute_alternative_run(
        _config_payload(),
        source,
        _ok(AlternativeInterpreterRegistry.try_create(())),
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        expected_command_owner_epoch=18,
        journal_writer=writer,
        journal_store=journal,
    )
    assert is_refusal(result)
    assert result.category.value == "unavailable dependency"
    assert (
        _ok(JournalReader(journal).read_checked(writer.stream_name, for_world=World.REPLAY)) == []
    )


def test_atc_study_label_is_validated_before_any_ct13_write(tmp_path: Path) -> None:
    source = _source(tmp_path)
    journal, writer = _journal(tmp_path)
    refused = execute_alternative_run(
        _config_payload(),
        source,
        _registry(),
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        expected_command_owner_epoch=18,
        journal_writer=writer,
        journal_store=journal,
        trial_label={"study_fp": "not-a-v2-trial-label"},
    )
    assert is_refusal(refused)
    assert writer.next_sequence == 0


def test_atc_refuses_stale_admission_and_old_command_owner_before_effects(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    journal, writer = _journal(tmp_path)
    stale_admission = {
        "checked_grant_ids": ["grant:atc-sim"],
        "decided_at_ns": _DECISION_NS,
        "evaluator_principal": "host",
        "health_evidence_ref": "health:atc-recorded-test",
        "health_revision": 4,
        "observation_freshness": {
            "max_age_ns": 1,
            "observed_at_ns": _OBSERVED_NS,
        },
    }
    refused_stale = execute_alternative_run(
        _config_payload(admission=stale_admission),
        source,
        _registry(),
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        expected_command_owner_epoch=18,
        journal_writer=writer,
        journal_store=journal,
    )
    assert is_refusal(refused_stale)
    assert refused_stale.category.value == "stale evidence"
    assert writer.next_sequence == 0
    refused_epoch = execute_alternative_run(
        _config_payload(),
        source,
        _registry(),
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        expected_command_owner_epoch=19,
        journal_writer=writer,
        journal_store=journal,
    )
    assert is_refusal(refused_epoch)
    assert writer.next_sequence == 0


@pytest.mark.parametrize("ack", [None, "ack"])
def test_atc_refuses_untyped_append_acknowledgments_without_attribute_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ack: object
) -> None:
    source = _source(tmp_path)
    journal, writer = _journal(tmp_path)

    def untyped_ack(
        event_type: object,
        payload: Mapping[str, object] | None = None,
        *,
        instant: object,
        outcome: object | None = None,
        correlation_id: object | None = None,
        display_time: object | None = None,
    ) -> Result[JournalAppendReceipt]:
        del event_type, payload, instant, outcome, correlation_id, display_time
        return Ok(cast(JournalAppendReceipt, ack))

    monkeypatch.setattr(writer, "record", untyped_ack)
    result = execute_alternative_run(
        _config_payload(),
        source,
        _registry(),
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        expected_command_owner_epoch=18,
        journal_writer=writer,
        journal_store=journal,
    )
    assert is_refusal(result)
    assert writer.next_sequence == 0
    assert (
        _ok(JournalReader(journal).read_checked(writer.stream_name, for_world=World.REPLAY)) == []
    )


@pytest.mark.parametrize("corrupt_metadata", [False, True])
def test_atc_refuses_false_physical_receipt_for_a_real_append(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corrupt_metadata: bool
) -> None:
    source = _source(tmp_path)
    journal, writer = _journal(tmp_path)
    original_record = writer.record

    def false_receipt(
        event_type: object,
        payload: Mapping[str, object] | None = None,
        *,
        instant: object,
        outcome: object | None = None,
        correlation_id: object | None = None,
        display_time: object | None = None,
    ) -> Result[JournalAppendReceipt]:
        actual = original_record(
            event_type,
            payload,
            instant=instant,
            outcome=outcome,
            correlation_id=correlation_id,
            display_time=display_time,
        )
        assert is_ok(actual)
        changes: dict[str, object] = {"fingerprint": _ok(fingerprint({"unrelated": "artifact"}))}
        if corrupt_metadata:
            changes.update(
                world=World.LIVE,
                sequence=999,
                is_evidence_bearing=False,
                retained_forever=False,
            )
        false_store = replace(actual.value.store_receipt, **changes)
        return Ok(replace(actual.value, store_receipt=false_store))

    monkeypatch.setattr(writer, "record", false_receipt)
    result = execute_alternative_run(
        _config_payload(),
        source,
        _registry(),
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        expected_command_owner_epoch=18,
        journal_writer=writer,
        journal_store=journal,
    )
    assert is_refusal(result)
    assert writer.next_sequence == 1  # The append happened; its false acknowledgment was rejected.
    reopened = _ok(JournalReader(journal).read_checked(writer.stream_name, for_world=World.REPLAY))
    assert len(reopened) == 1
    assert reopened[0].event_type is JournalEventType.DECISION


@pytest.mark.parametrize(
    ("field", "value"),
    [("event_type", "decision"), ("world", "replay"), ("outcome", "authorized")],
)
def test_atc_refuses_malformed_typed_event_acknowledgment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    source = _source(tmp_path)
    journal, writer = _journal(tmp_path)
    original_record = writer.record

    def malformed_event(
        event_type: object,
        payload: Mapping[str, object] | None = None,
        *,
        instant: object,
        outcome: object | None = None,
        correlation_id: object | None = None,
        display_time: object | None = None,
    ) -> Result[JournalAppendReceipt]:
        actual = original_record(
            event_type,
            payload,
            instant=instant,
            outcome=outcome,
            correlation_id=correlation_id,
            display_time=display_time,
        )
        assert is_ok(actual)
        event = replace(actual.value.event, **{field: value})
        return Ok(replace(actual.value, event=event))

    monkeypatch.setattr(writer, "record", malformed_event)
    result = execute_alternative_run(
        _config_payload(),
        source,
        _registry(),
        initial_accounting_state={"cash_units": 2_000_000, "position_units": 0},
        expected_command_owner_epoch=18,
        journal_writer=writer,
        journal_store=journal,
    )
    assert is_refusal(result)
    assert writer.next_sequence == 1
