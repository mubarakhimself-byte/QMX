"""Characterize supported Study ingress and refusal of the earlier partial descriptor.

The checkpoint's backtest request is retained as a refusal control. Complete
recorded Study inputs use the existing optimize door; no runtime alias is added.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TypeVar

import pytest
from click.testing import CliRunner
from operator_study_fixture_support import (  # pyright: ignore[reportMissingTypeStubs]
    prepare_study_inputs,
    write_study_binding,
)
from qmb.doors.cli import main
from qmb.host.qma_cli import QmaBacktestContext
from qmb.optimize import (
    AlternativeParameterBinding,
    AlternativeStudyObjective,
    StudyStepper,
    coerce_study_space,
)
from qmf.core import Fingerprint, UnitKind, fingerprint, is_ok
from qmf.core.refusal import Result

T = TypeVar("T")


@pytest.fixture(autouse=True)
def _forbid_study_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_execution(*args: object, **kwargs: object) -> object:
        raise AssertionError("preflight must not execute or verify a Study")

    monkeypatch.setattr(
        "qmb.host.operator_study_replay.run_operator_alternative_study", unexpected_execution
    )
    monkeypatch.setattr(
        "qmb.host.operator_study_replay.verify_operator_alternative_study", unexpected_execution
    )


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(char: str) -> Fingerprint:
    return _ok(Fingerprint.try_create(f"fp1:sha256:{char * 64}"))


def _study_descriptor_identity() -> dict[str, object]:
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
    objective = _ok(
        AlternativeStudyObjective.try_create("accepted_entry", "max", UnitKind.COUNT.value)
    )
    binding = _ok(AlternativeParameterBinding.try_create("max_gross", "risk", "max_gross"))
    identity: dict[str, object] = {
        "class": "qmb-operator-alternative-study-v1",
        "format_version": 1,
        "parameter_space": space.fp1_identity(),
        "seed": 17,
        "direction": "max",
        "batch_size": 2,
        "generation_count": 1,
        "objective": objective.fp1_identity(),
        "parameter_bindings": [binding.fp1_identity()],
    }
    study_fp = _ok(fingerprint(identity))
    stepper = StudyStepper(
        space=space,
        seed=17,
        direction="max",
        study_fp=study_fp,
        batch_size=2,
    )
    return {**identity, "study_fp1": stepper.study_fp.value}


def _qma_payload() -> dict[str, object]:
    return {
        "job_id": "job-atc-study-ingress",
        "attempt_id": 1,
        "experiment_spec_fp1": _fp("a").value,
        "evidence_ref": _fp("b").value,
        "environment_ref": "env:local-recorded-study-fixture",
        "occupancy_key": "run:atc-study-fixture",
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
        "split_manifest_fp1": _fp("c").value,
        "operator_descriptor_fp1": None,
    }


def _write_legacy_study_binding(runtime_root: Path, payload: dict[str, object]) -> None:
    """Keep the old checkpoint descriptor, including its incomplete runtime binding."""
    descriptor_dir = (
        runtime_root
        / str(payload["experiment_spec_fp1"]).replace(":", "-")
        / str(payload["evidence_ref"]).replace(":", "-")
    )
    descriptor_dir.mkdir(parents=True)
    body: dict[str, object] = {
        "class": "qmb-operator-alternative-study-binding-v1",
        "format_version": 1,
        "composition_class": "alternative",
        "experiment_spec_fp1": payload["experiment_spec_fp1"],
        "evidence_ref": payload["evidence_ref"],
        "split_manifest_fp1": payload["split_manifest_fp1"],
        "study": _study_descriptor_identity(),
        "operator_binding": {
            "policy_pair_fp1": _fp("d").value,
            "source_fp1": _fp("e").value,
            "split_fp1": payload["split_manifest_fp1"],
            "registry_fp1": _fp("f").value,
            "interpreter_registration_fp1": _fp("1").value,
        },
    }
    body["descriptor_fp1"] = _ok(fingerprint(body)).value
    (descriptor_dir / "operator-alternative-study-binding.json").write_text(
        json.dumps(body, sort_keys=True), encoding="utf-8"
    )


def _environment(payload: dict[str, object], runtime_root: Path) -> dict[str, str]:
    return {
        "QMA_QMB_DOOR": "cli",
        "QMA_QMB_DOOR_PAYLOAD": json.dumps(payload),
        "QMA_QMB_JOB_ID": str(payload["job_id"]),
        "QMA_QMB_ATTEMPT_ID": str(payload["attempt_id"]),
        "QMA_QMB_EXPERIMENT_SPEC_FP1": str(payload["experiment_spec_fp1"]),
        "QMA_QMB_EVIDENCE_REF": str(payload["evidence_ref"]),
        "QMA_QMB_SPLIT_MANIFEST_FP1": str(payload["split_manifest_fp1"]),
        "QMA_QMB_ENVIRONMENT_REF": str(payload["environment_ref"]),
        "QMA_QMB_OCCUPANCY_KEY": str(payload["occupancy_key"]),
        "QMA_QMB_PREFLIGHT": "1",
        "QMB_REPLAY_RUNTIME_ROOT": str(runtime_root),
    }


def _payload_for(context: QmaBacktestContext) -> dict[str, object]:
    payload = _qma_payload()
    payload.update(
        job_id=context.job_id,
        attempt_id=context.attempt_id,
        experiment_spec_fp1=context.experiment_spec_fp1.value,
        evidence_ref=context.evidence_ref.value,
        split_manifest_fp1=context.split_manifest_fp1.value,
        environment_ref=context.environment_ref,
        occupancy_key=context.occupancy_key,
        command=context.command,
    )
    return payload


def _files(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_backtest_preflight_refuses_checkpoint_study_descriptor(tmp_path: Path) -> None:
    """Study is an optimize invocation, never an implicit backtest alias."""
    payload = _qma_payload()
    runtime = tmp_path / "operator-runtime"
    _write_legacy_study_binding(runtime, payload)
    before = _files(tmp_path)
    result = CliRunner().invoke(main, ["backtest", "run"], env=_environment(payload, runtime))
    assert result.exit_code == 1, result.output
    refusal = json.loads(result.stderr)
    assert refusal["category"] == "policy rejection"
    assert refusal["context"]["field"] == "command"
    assert (
        refusal["context"]["reason"]
        == "optimize selects Study; backtest selects Book or Alternative"
    )
    assert _files(tmp_path) == before


def test_optimize_preflight_refuses_checkpoint_partial_descriptor(tmp_path: Path) -> None:
    """Changing the command does not confer complete operator-binding authority."""
    payload = _qma_payload()
    payload["command"] = "optimize.run"
    runtime = tmp_path / "operator-runtime"
    _write_legacy_study_binding(runtime, payload)
    before = _files(tmp_path)
    result = CliRunner().invoke(main, ["optimize", "run"], env=_environment(payload, runtime))
    assert result.exit_code == 1, result.output
    refusal = json.loads(result.stderr)
    assert refusal["context"]["field"] == "operator_binding"
    assert refusal["context"]["reason"] == "Study descriptor has exactly its versioned fields"
    assert _files(tmp_path) == before


def test_optimize_preflight_selects_complete_operator_study_descriptor(tmp_path: Path) -> None:
    inputs = prepare_study_inputs(tmp_path / "recorded")
    runtime = tmp_path / "operator-runtime"
    path, inputs, plan = write_study_binding(runtime, inputs)
    payload = _payload_for(inputs.context)
    body = json.loads(path.read_text())
    before = _files(tmp_path)
    result = CliRunner().invoke(main, ["optimize", "run"], env=_environment(payload, runtime))
    assert result.exit_code == 0, result.output
    preflight = json.loads(result.stdout)
    assert preflight["class"] == "qmb-runtime-preflight-v1"
    assert preflight["composition_class"] == "alternative-study"
    assert preflight["mints_ct32"] is False
    assert preflight["operator_descriptor_fp1"] == body["descriptor_fp1"]
    assert preflight["study_fp1"] == plan.fingerprint.value
    assert preflight["generation_count"] == plan.generation_count
    assert preflight["batch_size"] == plan.batch_size
    assert not inputs.terminal_store.path.exists()
    assert _files(tmp_path) == before


def test_backtest_preflight_refuses_complete_study_descriptor(tmp_path: Path) -> None:
    """Even complete recorded Study inputs cannot cross the command boundary."""
    inputs = prepare_study_inputs(tmp_path / "recorded")
    runtime = tmp_path / "operator-runtime"
    _, inputs, _ = write_study_binding(runtime, inputs)
    payload = _payload_for(inputs.context)
    payload["command"] = "backtest.run"
    before = _files(tmp_path)
    result = CliRunner().invoke(main, ["backtest", "run"], env=_environment(payload, runtime))
    assert result.exit_code == 1, result.output
    refusal = json.loads(result.stderr)
    assert refusal["category"] == "policy rejection"
    assert refusal["context"]["field"] == "command"
    assert not inputs.terminal_store.path.exists()
    assert _files(tmp_path) == before
