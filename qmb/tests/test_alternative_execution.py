"""Registered ATC execution over persisted CT-10 and CT-13 replay evidence.

The interpreter below defines a deliberately test-local exact policy vocabulary. It
does not define QMX's illustrative fixed-fraction finance semantics or connect to a
provider; the source observations and journal writes use real QMF persistence APIs.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from qmb._refuse import invalid
from qmb.config.alternative import (
    ADAPTER_INTERNAL_SIMULATE,
    ALTERNATIVE_CONFIG_CLASS,
    validate_alternative_run_config,
)
from qmb.execution.alternative import (
    AlternativeEvaluationRequest,
    AlternativeInterpreterRegistry,
    AlternativePolicyEvaluation,
    ATCJournalReference,
    InternalSimulatedAction,
    PolicyInterpreterRegistration,
    execute_alternative_run,
)
from qmb.host.replay import read_recorded_replay_source
from qmf.core import (
    CalendarIdentity,
    Instant,
    Ok,
    Result,
    World,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.core.chrono import WriterId
from qmf.data.journal import DecisionOutcome, JournalEventType
from qmf.data.journal_producer import JournalReader, JournalWriter
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.seal import HoldoutSeal
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener

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
        accepted = 0 < ask.verbatim <= risk["max_gross"]
        next_state = {
            "cash_units": prior_cash - ask.verbatim if accepted else prior_cash,
            "position_units": prior_position + 1 if accepted else prior_position,
        }
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
    assert "ct32" not in str(event.payload).lower()
    assert receipt.fp1_identity()["source_fp1"] == source.fingerprint.value


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
