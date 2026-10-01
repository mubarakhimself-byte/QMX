"""Characterize the missing operator-bound ATC Study CLI ingress.

The test's private descriptor shape composes existing typed Study constructors;
it does not add a public operation, QMA payload field, or financial grammar.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from click.testing import CliRunner
from qmb.doors.cli import main
from qmb.optimize import (
    AlternativeParameterBinding,
    AlternativeStudyObjective,
    StudyStepper,
    coerce_study_space,
)
from qmf.core import Fingerprint, UnitKind, fingerprint, is_ok
from qmf.core.refusal import Result

T = TypeVar("T")


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


def test_backtest_preflight_selects_operator_bound_alternative_study_descriptor(
    tmp_path: Path,
) -> None:
    """Expected to fail until existing backtest.run resolves this private Study mode."""
    payload = _qma_payload()
    runtime_root = tmp_path / "operator-runtime"
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
    environment = {
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

    result = CliRunner().invoke(main, ["backtest", "run"], env=environment)
    assert result.exit_code == 0, result.output
    preflight = json.loads(result.stdout)
    assert preflight["class"] == "qmb-runtime-preflight-v1"
    assert preflight["composition_class"] == "alternative"
    assert preflight["mints_ct32"] is False
    assert preflight["operator_descriptor_fp1"] == body["descriptor_fp1"]
