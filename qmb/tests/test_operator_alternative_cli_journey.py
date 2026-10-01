"""Actual CLI journey for the operator-bound Alternative composition."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TypeVar, cast

from qmb.config.alternative import validate_alternative_run_config
from qmb.execution.alternative import (
    AlternativeEvaluationRequest,
    AlternativeInterpreterRegistry,
    AlternativeMeasure,
    AlternativeMeasureDeclaration,
    AlternativePolicyEvaluation,
    PolicyInterpreterRegistration,
)
from qmb.host.replay import RecordedReplaySource, read_recorded_replay_source
from qmf.core import (
    CalendarIdentity,
    ExactRational,
    Fingerprint,
    Money,
    Ok,
    Result,
    UnitKind,
    fingerprint,
    is_ok,
)
from qmf.core.chrono import Instant, WriterId
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.seal import HoldoutSeal
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest
from qmf.data.store import EvidenceStore

T = TypeVar("T")
_NS = 1_700_000_000_000_000_000


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(value: str) -> Fingerprint:
    return _ok(Fingerprint.try_create(value))


def _config_payload() -> dict[str, object]:
    return {
        "admission": {
            "checked_grant_ids": ["grant:atc-sim"],
            "decided_at_ns": 1_726_747_200_000_000_000,
            "evaluator_principal": "host",
            "health_evidence_ref": "health:atc-recorded-test",
            "health_revision": 4,
            "observation_freshness": {
                "max_age_ns": 30_000_000_000,
                "observed_at_ns": 1_726_747_170_000_000_000,
            },
        },
        "command": {
            "account_id": "acct:recorded-test",
            "adapter_capability": "internal-simulate",
            "command_owner_epoch": 18,
            "instrument": "EURUSD",
            "role": "research",
        },
        "config_class": "alternative",
        "policy_pair": {
            "accounting": {
                "cash_identity": "integer-test-usd-units-v1",
                "currency": "USD",
                "fill_application": "buy-one-unit-at-recorded-ask-v1",
                "position_identity": "one-unit-eurusd-v1",
                "residual_meaning": "whole-integer-units-v1",
                "valuation": "recorded-ask-v1",
            },
            "risk": {
                "halt": "refuse-nonpositive-ask-v1",
                "max_gross": 10_000_000,
                "override_principal": "test-host",
                "sizing": "one-unit-under-gross-cap-v1",
            },
        },
        "policy_pair_id": "pp:recorded-exact-v1",
        "policy_pair_version": 1,
    }


def _observation(side: str, sequence: int, price: int) -> SourceObservation:
    writer = _ok(WriterId.try_create("test-host", "qmb", "atc-recorded", "boot-1"))
    at = Instant(value_ns=_NS)
    return _ok(
        SourceObservation.try_create(
            event_time=at,
            known_at=at,
            source="local-ct10-atc-fixture",
            source_native_id=f"quote-{side}-1",
            revision="1",
            receive_wall_time=at,
            writer=writer,
            sequence=sequence,
            world="replay",
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


def _split():
    calendar = _ok(CalendarIdentity.try_create("atc-fixture-calendar", "v1", "2025a"))
    segments = _ok(
        SplitManifest.default_split_segments(
            tuple(Instant(value_ns=_NS + offset) for offset in (1000, 2000, 3000))
        )
    )
    manifest = _ok(
        SplitManifest.try_create(
            calendar_identity=calendar,
            segments=segments,
            seal_boundary=_ok(SplitBoundary.try_create(Instant(value_ns=_NS + 3000))),
            purge_width=0,
            embargo_width=0,
            world="replay",
        )
    )
    return manifest, _ok(HoldoutSeal.from_manifest(manifest, 18))


class _DescriptorInterpreter:
    def evaluate(
        self, request: AlternativeEvaluationRequest
    ) -> Result[AlternativePolicyEvaluation]:
        return Ok(
            _ok(
                AlternativePolicyEvaluation.try_create(
                    accounting_state=dict(request.prior_accounting_state),
                    risk_verdict="descriptor-registry-placeholder",
                    risk_accepted=True,
                    actions=(),
                    measures=(
                        _ok(
                            AlternativeMeasure.try_create(
                                "end_equity",
                                _ok(
                                    Money.try_create(
                                        request.prior_accounting_state["cash_units"],
                                        "USD",
                                        0,
                                    )
                                ),
                            )
                        ),
                        _ok(
                            AlternativeMeasure.try_create(
                                "accepted_entry",
                                _ok(ExactRational.try_create(1, 1, UnitKind.COUNT)),
                            )
                        ),
                    ),
                )
            )
        )


def _registry() -> AlternativeInterpreterRegistry:
    config = _ok(validate_alternative_run_config(_config_payload()))
    implementation = _ok(fingerprint({"class": "test-exact-interpreter", "version": 1}))
    registration = _ok(
        PolicyInterpreterRegistration.try_create(
            policy_pair_id=config.policy_pair.policy_pair_id,
            policy_pair_version=config.policy_pair.policy_pair_version,
            policy_pair_hash=config.policy_pair.policy_pair_hash,
            interpreter_id="test-exact-quote-interpreter",
            interpreter_version=1,
            interpreter_fp1=implementation,
            interpreter=_DescriptorInterpreter(),
            declared_measures=(
                _ok(
                    AlternativeMeasureDeclaration.try_create(
                        "end_equity", UnitKind.MONEY.value, "USD"
                    )
                ),
                _ok(
                    AlternativeMeasureDeclaration.try_create(
                        "accepted_entry", UnitKind.COUNT.value
                    )
                ),
            ),
        )
    )
    return _ok(AlternativeInterpreterRegistry.try_create((registration,)))


def _persisted_source(raw_root: Path) -> tuple[RecordedReplaySource, tuple[str, ...]]:
    boundary = SourceObservationBoundary(EvidenceStore(raw_root))
    archive_refs = tuple(
        _ok(boundary.admit(_observation(side, index, price))).archive.fingerprint.value
        for index, (side, price) in enumerate((("bid", 1_234_500), ("ask", 1_234_520)))
    )
    manifest, seal = _split()
    source = _ok(
        read_recorded_replay_source(
            store_root=raw_root,
            archive_fingerprints=archive_refs,
            stream_id="eurusd-recorded-atc-cli",
            split_manifest=manifest,
            split_role=SegmentRole.TRAIN,
            holdout_seal=seal,
        )
    )
    assert source.split_fp1 == manifest.fingerprint
    return source, archive_refs


def _writer(machine: str, role: str, stream: str, epoch: str) -> dict[str, str]:
    return {
        "machine": machine,
        "role": role,
        "stream": stream,
        "boot_epoch_id": epoch,
    }


def _builder_source(archive_refs: tuple[str, ...]) -> str:
    refs = archive_refs
    return f'''from collections.abc import Mapping
from pathlib import Path
from typing import cast

from qmb.config.alternative import validate_alternative_run_config
from qmb.execution.alternative import (
    AlternativeEvaluationRequest, AlternativeInterpreterRegistry, AlternativeMeasure,
    AlternativeMeasureDeclaration, AlternativePolicyEvaluation,
    PolicyInterpreterRegistration,
)
from qmb.execution.alternative_terminal import AlternativeTerminalStore
from qmb.host.operator_alternative import OperatorAlternativeInputs
from qmb.host.replay import read_recorded_replay_source
from qmb.host.qma_cli import QmaBacktestContext
from qmf.core import ExactRational, Instant, Money, Ok, Result, UnitKind, World, fingerprint
from qmf.core.refusal import is_refusal
from qmf.core.chrono import WriterId
from qmf.data.seal import HoldoutSeal
from qmf.data.splits import SegmentRole
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener
from qmf.data.journal_producer import JournalWriter
from qmf.registry import RegistryPersistence

ARCHIVE_REFS = {refs!r}
CONFIG_PAYLOAD = {_config_payload()!r}
NS = {_NS}

class RegisteredLocalReplayInterpreter:
    def evaluate(
        self, request: AlternativeEvaluationRequest
    ) -> Result[AlternativePolicyEvaluation]:
        measure = AlternativeMeasure.try_create(
            "end_equity",
            Money.try_create(request.prior_accounting_state["cash_units"], "USD", 0).value,
        )
        if is_refusal(measure):
            return measure
        accepted = AlternativeMeasure.try_create(
            "accepted_entry", ExactRational.try_create(1, 1, UnitKind.COUNT).value
        )
        if is_refusal(accepted):
            return accepted
        return Ok(AlternativePolicyEvaluation(
            accounting_state=dict(request.prior_accounting_state),
            risk_verdict="local-recorded-policy-evaluated",
            risk_accepted=True,
            actions=(),
            measures=(measure.value, accepted.value),
        ))

def _manifest():
    from qmf.core import CalendarIdentity
    from qmf.data.splits import SplitBoundary, SplitManifest
    calendar = CalendarIdentity.try_create("atc-fixture-calendar", "v1", "2025a").value
    segments = SplitManifest.default_split_segments(
        tuple(Instant(value_ns=NS + offset) for offset in (1000, 2000, 3000))
    ).value
    return SplitManifest.try_create(
        calendar_identity=calendar,
        segments=segments,
        seal_boundary=SplitBoundary.try_create(Instant(value_ns=NS + 3000)).value,
        purge_width=0,
        embargo_width=0,
        world=World.REPLAY,
    ).value

def build(context: QmaBacktestContext, binding):
    config = validate_alternative_run_config(CONFIG_PAYLOAD)
    if is_refusal(config):
        return config
    manifest = _manifest()
    roots = {{key: Path(value) for key, value in binding.identity["roots"].items()}}
    source = read_recorded_replay_source(
        store_root=roots["raw"],
        archive_fingerprints=ARCHIVE_REFS,
        stream_id="eurusd-recorded-atc-cli",
        split_manifest=manifest,
        split_role=SegmentRole.TRAIN,
        holdout_seal=HoldoutSeal.from_manifest(manifest, 18).value,
    )
    if is_refusal(source):
        return source
    implementation = fingerprint({{"class": "test-exact-interpreter", "version": 1}})
    if is_refusal(implementation):
        return implementation
    registration = PolicyInterpreterRegistration.try_create(
        policy_pair_id=config.value.policy_pair.policy_pair_id,
        policy_pair_version=config.value.policy_pair.policy_pair_version,
        policy_pair_hash=config.value.policy_pair.policy_pair_hash,
        interpreter_id="test-exact-quote-interpreter",
        interpreter_version=1,
        interpreter_fp1=implementation.value,
        interpreter=RegisteredLocalReplayInterpreter(),
        declared_measures=(
            AlternativeMeasureDeclaration.try_create(
                "end_equity", UnitKind.MONEY.value, "USD"
            ).value,
            AlternativeMeasureDeclaration.try_create(
                "accepted_entry", UnitKind.COUNT.value
            ).value,
        ),
    )
    if is_refusal(registration):
        return registration
    registry = AlternativeInterpreterRegistry.try_create((registration.value,))
    if is_refusal(registry):
        return registry
    journal_root = roots["journal"]
    journal = JournalStore(
        World.REPLAY,
        journal_dir=journal_root / context.job_id,
        open_stream=jsonl_opener(),
    )
    writer = WriterId.try_create("qmb-atc-cli", "qmb", "atc-cli-stream", "boot-1")
    if is_refusal(writer):
        return writer
    journal_writer = JournalWriter.resume(journal, writer.value)
    if is_refusal(journal_writer):
        return journal_writer
    registry_writer_data = binding.identity["registry_writer"]
    registry_writer = WriterId.try_create(
        registry_writer_data["machine"], registry_writer_data["role"],
        registry_writer_data["stream"], registry_writer_data["boot_epoch_id"],
    )
    lineage_data = binding.identity["lineage_writer"]
    lineage_writer = WriterId.try_create(
        lineage_data["machine"], lineage_data["role"],
        lineage_data["stream"], lineage_data["boot_epoch_id"],
    )
    if is_refusal(registry_writer) or is_refusal(lineage_writer):
        return registry_writer if is_refusal(registry_writer) else lineage_writer
    persistence = RegistryPersistence.open(EvidenceStore(roots["registry"]), World.REPLAY)
    if is_refusal(persistence):
        return persistence
    terminal_writer = WriterId.try_create("qmb-atc-cli", "qmb", "terminal", "boot-1")
    if is_refusal(terminal_writer):
        return terminal_writer
    terminal = AlternativeTerminalStore.try_create(
        roots["alternative_terminal"], writer=terminal_writer.value
    )
    if is_refusal(terminal):
        return terminal
    initial_state = cast(Mapping[str, object], binding.identity["initial_accounting_state"])
    return Ok(OperatorAlternativeInputs(
        context=context,
        config=config.value,
        recorded_source=source.value,
        registry=registry.value,
        initial_accounting_state=initial_state,
        expected_command_owner_epoch=binding.identity["command_owner_epoch"],
        runtime_descriptor_fp1=binding.descriptor_fp1,
        registry_as_of=Instant.try_create(binding.identity["registry_as_of_ns"]).value,
        registry_writer=registry_writer.value,
        raw_store_root=roots["raw"],
        journal_root=journal_root,
        journal_writer=journal_writer.value,
        journal_store=journal,
        terminal_store=terminal.value,
        registry_persistence=persistence.value,
        lineage_writer=lineage_writer.value,
    ))
'''


def _context_payload(
    *, spec: Fingerprint, evidence: Fingerprint, split: Fingerprint
) -> dict[str, object]:
    return {
        "job_id": "job-atc-cli-journey",
        "attempt_id": 1,
        "experiment_spec_fp1": spec.value,
        "evidence_ref": evidence.value,
        "environment_ref": "env:local-atc-cli-fixture",
        "occupancy_key": "qmb:job-atc-cli-journey",
        "world": "replay",
        "recorded": True,
        "import_edge": False,
        "owned_by": "qmb",
        "qma_re_specifies": False,
        "qmb_owned": ["artifact_contract", "intra_node_parallelism", "run_ledger"],
        "route": ["agent", "qma_backtest_tool", "backtesting_service", "qmb_door", "qmb"],
        "command": "backtest.run",
        "occupancy": "run",
        "mints_ct32": False,
        "mints_experiment_spec": False,
        "children_are_qma_jobs": False,
        "opens_daemon_sqlite": False,
        "split_manifest_fp1": split.value,
        "operator_descriptor_fp1": None,
    }


def _env(payload: Mapping[str, object], runtime_root: Path) -> dict[str, str]:
    values = {
        "QMA_QMB_DOOR": "cli",
        "QMA_QMB_DOOR_PAYLOAD": json.dumps(payload),
        "QMA_QMB_JOB_ID": str(payload["job_id"]),
        "QMA_QMB_ATTEMPT_ID": str(payload["attempt_id"]),
        "QMA_QMB_EXPERIMENT_SPEC_FP1": str(payload["experiment_spec_fp1"]),
        "QMA_QMB_EVIDENCE_REF": str(payload["evidence_ref"]),
        "QMA_QMB_SPLIT_MANIFEST_FP1": str(payload["split_manifest_fp1"]),
        "QMA_QMB_ENVIRONMENT_REF": str(payload["environment_ref"]),
        "QMA_QMB_OCCUPANCY_KEY": str(payload["occupancy_key"]),
        "QMB_REPLAY_RUNTIME_ROOT": str(runtime_root),
    }
    return values


def _write_descriptor(
    runtime_root: Path,
    payload: Mapping[str, object],
    source: RecordedReplaySource,
    archive_refs: tuple[str, ...],
    roots: Mapping[str, Path],
) -> Fingerprint:
    context_config = _ok(validate_alternative_run_config(_config_payload()))
    registry = _registry()
    registration = _ok(registry.resolve(context_config))
    writers = {
        "journal": _writer("qmb-atc-cli", "qmb", "atc-cli-stream", "boot-1"),
        "lineage": _writer("qmb-atc-cli", "qmb", "atc-lineage", "boot-1"),
        "registry": _writer("qmb-atc-cli", "qmb", "atc-registry", "boot-1"),
    }
    state = {"cash_units": 2_000_000, "position_units": 0}
    context_refs = {
        key: cast(str, payload[key])
        for key in ("experiment_spec_fp1", "evidence_ref", "split_manifest_fp1")
    }
    identity: dict[str, object] = {
        "class": "qmb-operator-alternative-binding-v1",
        "format_version": 1,
        **context_refs,
        "composition_fp1": context_config.composition_fp.value,
        "policy_pair_identity": context_config.policy_pair.identity(),
        "source_fp1": source.fingerprint.value,
        "split_fp1": cast(Fingerprint, source.split_fp1).value,
        "split_role": cast(SegmentRole, source.split_role).value,
        "registry_fp1": registry.fingerprint.value,
        "interpreter_registration_fp1": registration.fingerprint.value,
        "journal_writer": writers["journal"],
        "journal_stream": "atc-cli-stream",
        "terminal_root": str(roots["alternative_terminal"]),
        "lineage_writer": writers["lineage"],
        "roots": {key: str(value) for key, value in roots.items()},
        "registry_as_of_ns": 0,
        "registry_writer": writers["registry"],
        "initial_accounting_state": state,
        "initial_accounting_state_fp1": _ok(fingerprint(state)).value,
        "command_owner_epoch": 18,
        "trial_label": {
            "class": "qmb-alternative-trial-label-v1",
            "present": False,
            "label": {},
        },
    }
    builder_files = {"runtime_builder.py": _builder_source(archive_refs)}
    builder_fp = _ok(
        fingerprint({"class": "qmb-operator-alternative-builder-v1", "files": builder_files})
    )
    body: dict[str, object] = {
        "class": "qmb-operator-alternative-binding-v1",
        "format_version": 1,
        "composition_class": "alternative",
        **context_refs,
        "operator_binding": identity,
        "operator_binding_fp1": _ok(fingerprint(identity)).value,
        "builder_files": builder_files,
        "builder_fp1": builder_fp.value,
        "entrypoint": "runtime_builder:build",
    }
    body["descriptor_fp1"] = _ok(fingerprint(body)).value
    directory = (
        runtime_root
        / cast(str, payload["experiment_spec_fp1"]).replace(":", "-")
        / cast(str, payload["evidence_ref"]).replace(":", "-")
    )
    directory.mkdir(parents=True)
    (directory / "operator-alternative-binding.json").write_text(
        json.dumps(body), encoding="utf-8"
    )
    return _fp(body["descriptor_fp1"])


def _run_cli(env: Mapping[str, str], *flags: tuple[str, str]) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(env)
    environment.update(dict(flags))
    cli = Path(sys.executable).with_name("qmb")
    return subprocess.run(
        [str(cli), "backtest", "run"],
        capture_output=True,
        check=False,
        text=True,
        env=environment,
        timeout=60,
    )


def test_qmb_cli_runs_and_verifies_operator_bound_alternative_without_reevaluation(
    tmp_path: Path,
) -> None:
    roots = {
        "raw": tmp_path / "raw",
        "registry": tmp_path / "registry",
        "journal": tmp_path / "journal",
        "alternative_terminal": tmp_path / "alternative-terminal",
    }
    for root in roots.values():
        root.mkdir(parents=True)
    source, archive_refs = _persisted_source(roots["raw"])
    assert source.split_fp1 is not None
    spec = _ok(fingerprint({"class": "registered-local-atc-experiment-spec"}))
    evidence = _ok(
        fingerprint(
            {
                "class": "registered-local-atc-source-reference-v1",
                "source_fp1": source.fingerprint.value,
                "split_fp1": source.split_fp1.value,
            }
        )
    )
    payload = _context_payload(
        spec=spec,
        evidence=evidence,
        split=source.split_fp1,
    )
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    env = _env(payload, runtime_root)
    descriptor_fp = _write_descriptor(runtime_root, payload, source, archive_refs, roots)

    # An input with a foreign CT-12 ref is refused before any CT-13 decision.
    foreign_payload = dict(payload)
    foreign_split = _ok(fingerprint({"class": "foreign-split"})).value
    foreign_payload["split_manifest_fp1"] = foreign_split
    foreign_env = _env(foreign_payload, runtime_root)
    refused_input = _run_cli(foreign_env, ("QMA_QMB_PREFLIGHT", "1"))
    assert refused_input.returncode != 0
    assert not tuple(roots["journal"].rglob("*.jsonl"))

    preflight = _run_cli(env, ("QMA_QMB_PREFLIGHT", "1"))
    assert preflight.returncode == 0, preflight.stderr
    preflight_result = json.loads(preflight.stdout)
    assert preflight_result["composition_class"] == "alternative"
    assert preflight_result["mints_ct32"] is False
    assert preflight_result["operator_descriptor_fp1"] == descriptor_fp.value

    selected_payload = dict(payload)
    selected_payload["operator_descriptor_fp1"] = descriptor_fp.value
    selected_env = _env(selected_payload, runtime_root)
    foreign_descriptor_payload = dict(selected_payload)
    foreign_descriptor_payload["operator_descriptor_fp1"] = _ok(
        fingerprint({"class": "foreign-descriptor"})
    ).value
    refused_descriptor = _run_cli(
        _env(foreign_descriptor_payload, runtime_root)
    )
    assert refused_descriptor.returncode != 0
    assert not tuple(roots["journal"].rglob("*.jsonl"))

    execution = _run_cli(selected_env)
    assert execution.returncode == 0, execution.stderr
    result = json.loads(execution.stdout)
    assert result["class"] == "qmb-alternative-result-v1"
    assert result["composition_class"] == "alternative"
    assert "ct32_fp1" not in result
    assert result["source_fp1"] == source.fingerprint.value
    assert result["split_fp1"] == source.split_fp1.value
    journal_file = (
        roots["journal"]
        / cast(str, payload["job_id"])
        / "atc-cli-stream"
        / "000000.jsonl"
    )
    before_verify = journal_file.read_bytes()
    assert before_verify

    claim = tmp_path / "result-claim.json"
    claim.write_text(json.dumps(result), encoding="utf-8")
    verify_flags = (
        ("QMA_QMB_VERIFY", "1"),
        ("QMA_QMB_VERIFY_CLAIM_FILE", str(claim)),
    )
    forged_result = dict(result)
    forged_result["source_fp1"] = _ok(fingerprint({"class": "foreign-source"})).value
    claim.write_text(json.dumps(forged_result), encoding="utf-8")
    refused_claim = _run_cli(selected_env, *verify_flags)
    assert refused_claim.returncode != 0
    assert journal_file.read_bytes() == before_verify

    claim.write_text(json.dumps(result), encoding="utf-8")
    verified = _run_cli(selected_env, *verify_flags)
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout) == result
    assert journal_file.read_bytes() == before_verify

    durable = _run_cli(
        selected_env,
        ("QMA_QMB_VERIFY", "1"),
        ("QMA_QMB_VERIFY_DURABLE", "1"),
    )
    assert durable.returncode == 0, durable.stderr
    assert json.loads(durable.stdout) == result
    assert journal_file.read_bytes() == before_verify
