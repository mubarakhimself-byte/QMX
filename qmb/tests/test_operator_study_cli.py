"""Real delegated optimize door with complete pinned recorded inputs and restart witnesses."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from operator_study_fixture_support import (  # pyright: ignore[reportMissingTypeStubs]
    ok,
    prepare_study_inputs,
    write_study_binding,
)
from qma.core.ontology import ActorId, DeskSlug
from qma.core.ports.execution import ExecutionEnvironmentDeclaration
from qma.core.ports.experiments import ExperimentSpec
from qma.core.ports.qmb import QMB_BACKTEST_TOOL_ID, QmbDoorInvocation
from qma.core.vocabulary.enums import ExecutionEnvironmentKind, JobHandleState
from qma.daemon.backtest import BacktestingService, CliQmbDoorTransport
from qma.daemon.envs import ExecutionEnvironmentRegistry
from qma.daemon.envs.jobs import JobHandleService
from qma.daemon.experiments import ExperimentSpecService
from qma.daemon.taskgraph.records import DispatchLease
from qma.daemon.tools import ToolRegistry
from qmb.host.operator_study_replay import invoke_operator_study, select_operator_composition
from qmf.core import Fingerprint, is_refusal


def _file_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_incomplete_study_verification_cannot_finish_trials_or_create_witness(
    tmp_path: Path,
) -> None:
    inputs = prepare_study_inputs(tmp_path / "recorded")
    runtime = tmp_path / "runtime"
    _, inputs, _ = write_study_binding(runtime, inputs)
    interrupted = invoke_operator_study(
        runtime_root=runtime,
        context=inputs.context,
        mode="execute",
        cancelled=inputs.terminal_store.path.exists,
    )
    assert is_refusal(interrupted), interrupted
    assert (
        len(
            ok(
                inputs.terminal_store.read(
                    journal_store=inputs.journal_store, registry=inputs.registry_persistence
                )
            )
        )
        == 1
    )
    before = _file_hashes(tmp_path)
    refused = invoke_operator_study(runtime_root=runtime, context=inputs.context, mode="verify")
    assert is_refusal(refused), refused
    assert _file_hashes(tmp_path) == before
    completed = ok(
        invoke_operator_study(runtime_root=runtime, context=inputs.context, mode="execute")
    )
    assert len(cast(list[object], completed["terminal_artifact_fp1s"])) == 2
    before = _file_hashes(tmp_path)
    reopened = ok(
        invoke_operator_study(runtime_root=runtime, context=inputs.context, mode="verify")
    )
    assert reopened == completed and _file_hashes(tmp_path) == before
    refused = invoke_operator_study(
        runtime_root=runtime,
        context=replace(inputs.context, attempt_id=inputs.context.attempt_id + 1),
        mode="verify",
    )
    assert is_refusal(refused), refused
    assert _file_hashes(tmp_path) == before


def test_registered_study_production_transport_persists_seven_field_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = prepare_study_inputs(tmp_path / "recorded")
    owner = ok(ActorId.mint(DeskSlug.ANALYSIS, "study-transport-fixture"))
    lease = DispatchLease(
        task_id="task-study",
        holder_agent_id="explicit-offline-fixture",
        mission_id="mission-study",
        owner=owner,
    )
    experiments = ExperimentSpecService()
    spec = ok(
        ExperimentSpec.try_create(
            data_ref=inputs.context.split_manifest_fp1.value,
            environment_ref="env:local",
            seed=12,
            model_and_harness_version={
                "model": "synthetic-offline-fixture",
                "harness": "transport-control",
            },
            cost_assumptions={"provider_usd_cents": 0},
            resolved_config_ref=inputs.config.fingerprint.value,
        )
    )
    ok(
        experiments.register(
            spec,
            dispatch_lease=lease,
            registering_attempt_no=0,
            model_deployment_ref="synthetic:transport-fixture",
        )
    )
    inputs = replace(
        inputs,
        context=replace(
            inputs.context, experiment_spec_fp1=ok(Fingerprint.try_create(spec.spec_fp1))
        ),
    )
    runtime = tmp_path / "runtime"
    path, inputs, plan = write_study_binding(runtime, inputs)
    monkeypatch.setenv("QMB_REPLAY_RUNTIME_ROOT", str(runtime))
    transport = CliQmbDoorTransport()
    environments = ExecutionEnvironmentRegistry()
    ok(
        environments.register_declaration(
            ExecutionEnvironmentDeclaration.isolated(
                ExecutionEnvironmentKind.LOCAL, provider_ref="offline-fixture"
            )
        )
    )
    service = BacktestingService(
        tools=ToolRegistry(),
        jobs=JobHandleService(),
        environments=environments,
        transport=transport,
        experiments=experiments,
        artifact_root=tmp_path / "qma-artifacts",
    )
    prepared = ok(
        service.preflight_registered_run(
            owner=owner,
            task_id=lease.task_id,
            environment_ref="env:local",
            experiment_spec_fp1=spec.spec_fp1,
            evidence_ref=inputs.context.evidence_ref.value,
            command="optimize.run",
        )
    )
    assert prepared is not None and prepared["study_fp1"] == plan.fingerprint.value
    assert is_refusal(
        invoke_operator_study(runtime_root=runtime, context=inputs.context, mode="verify")
    )
    assert not inputs.terminal_store.path.exists()
    placement = ok(
        service.invoke(
            QMB_BACKTEST_TOOL_ID,
            owner=owner,
            task_id=lease.task_id,
            environment_ref="env:local",
            experiment_spec_fp1=spec.spec_fp1,
            evidence_ref=inputs.context.evidence_ref.value,
            command="optimize.run",
            dispatch_lease=lease,
            model_deployment_ref="synthetic:transport-fixture",
        )
    )
    completed = ok(service.wait_and_observe(placement.handle.job_id, timeout=60))
    assert completed.state is JobHandleState.DONE, service.observer_failure_for(completed.job_id)
    readback = ok(
        service.read_completed_result(completed.job_id, owner=owner, environment_ref="env:local")
    )
    result = cast(Mapping[str, object], readback["result"])
    assert len(result) == 7
    assert len(cast(list[object], result["terminal_artifact_fp1s"])) == 2
    assert result["study_fp1"] == plan.fingerprint.value
    # A new actual module process uses only verify mode and this exact invocation.
    env = os.environ.copy()
    env["QMA_QMB_VERIFY"] = "1"
    env["QMA_QMB_VERIFY_DURABLE"] = "1"
    from qma.daemon.backtest.cli import (
        _door_env,  # pyright: ignore[reportPrivateUsage] - exact production envelope
    )

    env.update(
        _door_env(
            cast(QmbDoorInvocation, readback["invocation"]),
            receipt_path=None,
            cancel_path=None,
            ledger_path=None,
            hang=False,
        )
    )
    env["QMA_QMB_VERIFY"] = "1"
    env["QMA_QMB_VERIFY_DURABLE"] = "1"
    check = subprocess.run(
        [sys.executable, "-c", "from qmb.doors.cli import main; main()", "optimize", "run"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    assert json.loads(check.stdout) == result
    assert (
        len(
            ok(
                inputs.terminal_store.read(
                    journal_store=inputs.journal_store, registry=inputs.registry_persistence
                )
            )
        )
        == 2
    )
    # Conflicting presence and changed descriptor cannot change the prepared branch.
    (path.parent / "operator-binding.json").write_text("{}")
    assert is_refusal(select_operator_composition(runtime_root=runtime, context=inputs.context))


@pytest.mark.parametrize(
    "mutation",
    ["missing-field", "unknown-objective", "wrong-unit", "changed-builder", "study-fingerprint"],
)
def test_study_descriptor_refuses_before_any_trial(tmp_path: Path, mutation: str) -> None:
    inputs = prepare_study_inputs(tmp_path / "recorded")
    path, inputs, _ = write_study_binding(tmp_path / "runtime", inputs)
    body = json.loads(path.read_text())
    if mutation == "missing-field":
        del body["alternative_binding"]["operator_binding"]["roots"]
    elif mutation == "unknown-objective":
        body["study"]["objective"]["measure_identity"] = "unregistered"
    elif mutation == "wrong-unit":
        body["study"]["objective"]["unit_kind"] = "ratio"
    elif mutation == "changed-builder":
        body["alternative_binding"]["builder_files"]["builder.py"] += "\n# changed source\n"
    else:
        body["study_fp1"] = "fp1:sha256:" + "0" * 64
    from qmf.core import fingerprint

    body["descriptor_fp1"] = ok(
        fingerprint({k: v for k, v in body.items() if k != "descriptor_fp1"})
    ).value
    path.write_text(json.dumps(body))
    # Supply the new outer pin so the test reaches nested/content validation.
    context = replace(
        inputs.context, operator_descriptor_fp1=ok(Fingerprint.try_create(body["descriptor_fp1"]))
    )
    rejected = invoke_operator_study(
        runtime_root=tmp_path / "runtime", context=context, mode="execute"
    )
    assert is_refusal(rejected), rejected
    assert not inputs.terminal_store.path.exists()
