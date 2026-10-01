"""Registered ExperimentSpec through QMA service into the real QMB CLI child."""

from __future__ import annotations

import importlib
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from qma.core.content import content_address
from qma.core.ontology import ActorId, DeskSlug
from qma.core.ports.execution import ExecutionEnvironmentDeclaration
from qma.core.ports.experiments import ExperimentSpec
from qma.core.ports.qmb import QMB_BACKTEST_TOOL_ID
from qma.core.vocabulary.enums import ExecutionEnvironmentKind, JobHandleState
from qma.daemon.backtest import BacktestingService, CliQmbDoorTransport
from qma.daemon.envs import ExecutionEnvironmentRegistry
from qma.daemon.envs.jobs import JobHandleService
from qma.daemon.experiments import ExperimentSpecService
from qma.daemon.taskgraph.records import DispatchLease
from qma.daemon.tools import ToolRegistry
from qmf.core import Fingerprint, Result, is_ok

ROOT = Path(__file__).resolve().parents[2]
QMB_TESTS = ROOT / "qmb" / "tests"


def _ok[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _owner() -> ActorId:
    return _ok(ActorId.mint(DeskSlug.ANALYSIS, "registered-replay-test"))


def _prepare_runtime_builder() -> Callable[
    ..., tuple[dict[str, str], dict[str, Path], Fingerprint]
]:
    if str(QMB_TESTS) not in sys.path:
        sys.path.insert(0, str(QMB_TESTS))
    module = importlib.import_module("test_operator_replay_process")
    return cast(
        "Callable[..., tuple[dict[str, str], dict[str, Path], Fingerprint]]",
        cast(Any, module).prepare_operator_replay_runtime,
    )


def test_registered_spec_runs_through_backtesting_service_and_real_qmb_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    experiments = ExperimentSpecService()
    lease = DispatchLease(
        task_id="task-qma-registered-replay",
        holder_agent_id="agent-qma-replay-test",
        mission_id="mission-qma-replay-test",
        owner=_owner(),
    )
    registered_rows: list[object] = []

    def register_spec(split_fp1: Fingerprint) -> Fingerprint:
        config_ref = _ok(content_address({"class": "qma-registered-replay-runtime-v1"}))
        spec = _ok(
            ExperimentSpec.try_create(
                data_ref=split_fp1.value,
                environment_ref="env:docker",
                seed=3,
                model_and_harness_version={"model": "local-replay-test", "harness": "qmb"},
                cost_assumptions={"spread_usd_cents": 0},
                resolved_config_ref=config_ref.value,
            )
        )
        registered = _ok(
            experiments.register(
                spec,
                dispatch_lease=lease,
                model_deployment_ref="deploy:local-replay-test",
            )
        )
        registered_rows.append(registered)
        return _ok(Fingerprint.try_create(registered.spec.spec_fp1))

    prepare_runtime = _prepare_runtime_builder()
    env, roots, request_ref = prepare_runtime(
        tmp_path / "qmb-runtime", register_experiment=register_spec
    )
    monkeypatch.setenv("QMB_REPLAY_RUNTIME_ROOT", env["QMB_REPLAY_RUNTIME_ROOT"])
    registered = registered_rows[0]
    registered_spec = cast(AnyRegisteredSpec, registered).spec
    assert registered_spec.data_ref == env["QMA_QMB_SPLIT_MANIFEST_FP1"]

    environments = ExecutionEnvironmentRegistry()
    _ok(
        environments.register_declaration(
            ExecutionEnvironmentDeclaration.isolated(
                ExecutionEnvironmentKind.DOCKER,
                provider_ref="local-process-fixture",
            )
        )
    )
    configured_cli = os.environ.get("QMB_EXECUTABLE")
    cli = Path(configured_cli) if configured_cli else Path(sys.executable).with_name("qmb")
    assert cli.is_file(), f"QMB executable is missing: {cli}"
    transport = CliQmbDoorTransport(argv0=(str(cli),))
    service = BacktestingService(
        tools=ToolRegistry(),
        jobs=JobHandleService(),
        environments=environments,
        transport=transport,
        experiments=experiments,
    )
    try:
        _ok(service.install())
        placement = _ok(
            service.invoke(
                QMB_BACKTEST_TOOL_ID,
                owner=lease.owner,
                task_id=lease.task_id,
                environment_ref="env:docker",
                experiment_spec_fp1=registered_spec.spec_fp1,
                evidence_ref=request_ref.value,
                dispatch_lease=lease,
                model_deployment_ref="deploy:local-replay-test",
            )
        )
        assert placement.invocation.payload["experiment_spec_fp1"] == registered_spec.spec_fp1
        assert placement.invocation.payload["evidence_ref"] == request_ref.value
        assert placement.invocation.payload["split_manifest_fp1"] == registered_spec.data_ref
        assert len(transport.spawned) == 1
        assert transport.spawned[0].pid > 0
        assert transport.wait(placement.handle.job_id, timeout=60.0) == 0
        completed = _ok(service.observe_outcome(placement.handle.job_id, JobHandleState.DONE))
        assert completed.state is JobHandleState.DONE

        ledger_files = tuple(roots["terminal_ledger"].rglob("ledger.jsonl"))
        assert len(ledger_files) == 1
        ledger_rows = [
            json.loads(line)
            for line in ledger_files[0].read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(ledger_rows) == 1
        assert ledger_rows[0]["ct32_fingerprint"].startswith("fp1:sha256:")
        assert ledger_rows[0]["measures"]
    finally:
        transport.close()


class AnyRegisteredSpec:
    """Test typing shim for the registered experiment record returned by QMA."""

    spec: ExperimentSpec
