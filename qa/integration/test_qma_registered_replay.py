"""Registered ExperimentSpec through QMA service into the real QMB CLI child."""

# Integration assertions describe cross-process contracts rather than production branches.
# ruff: noqa: S101

from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, cast

import pytest
from qma.core.content import content_address
from qma.core.ontology import ActorId, DeskSlug, Goal, Quant, RoleName
from qma.core.operations import public_operation_descriptors
from qma.core.ports.execution import ExecutionEnvironmentDeclaration
from qma.core.ports.experiments import ExperimentSpec
from qma.core.ports.qmb import QMB_BACKTEST_TOOL_ID
from qma.core.vocabulary.enums import ExecutionEnvironmentKind, JobHandleState
from qma.daemon.backtest import BacktestingService, CliQmbDoorTransport
from qma.daemon.envs import ExecutionEnvironmentRegistry
from qma.daemon.envs.jobs import JobHandleService
from qma.daemon.experiments import ExperimentSpecService
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.daemon.taskgraph.compiler import CompileRequest
from qma.daemon.taskgraph.records import DispatchLease
from qma.daemon.tools import ToolRegistry
from qma.wire.invocation_envelope import compute_input_hash
from qma.wire.vocabulary import WireCommand, WireQuery
from qmf.core import Fingerprint, Result, is_ok

ROOT = Path(__file__).resolve().parents[2]
QMB_TESTS = ROOT / "qmb" / "tests"


T = TypeVar("T")


def _ok(result: Result[T]) -> T:
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


async def request_on(
    listener_helpers: Any,
    writer: Any,
    reader: Any,
    req_id: int,
    method: str,
    params: dict[str, object],
) -> dict[str, object]:
    listener_helpers._ws_write(
        writer, {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    )
    return await listener_helpers._ws_read_json(reader)


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
        _ok(
            experiments.append_evidence(
                spec_fp1=registered.spec.spec_fp1,
                dispatch_lease=lease,
                model_deployment_ref="deploy:local-replay-test",
                body={"note": "local registered deployment provenance"},
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
    registered_spec = cast(Any, registered).spec
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


def test_authenticated_ct40_run_grant_reaches_real_registered_qmb_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    daemon_root = tmp_path / "daemon"
    seed = tmp_path / "seed"
    seed.mkdir()
    composed = _ok(
        DaemonProcess.compose(
            daemon_root,
            machine="ct40-replay-test",
            boot_epoch_id="ct40-replay-test-boot",
            bind_port=0,
            plugin_load_configs=research_corpus_plugin_load_config(seed),
        )
    )
    process = composed
    actor = _owner()
    quant = Quant(
        actor_id=actor,
        desk=DeskSlug.ANALYSIS,
        quant_slug="registered-replay-test",
        role=RoleName.RESEARCHER,
        name="Registered replay test",
    )
    _ok(process._mailboxes.open_for_quant(quant))
    compiled = _ok(
        process.roster.compiler.compile(
            CompileRequest(goal=Goal(text="run a recorded QMB replay"), owner=quant)
        )
    )
    graph = process.task_dispatcher.materialize(compiled.task_graph, mission=compiled.mission)
    task_id = graph.tasks[0].id
    accepted = _ok(
        process.task_dispatcher.dispatch_task(
            task_id=task_id,
            holder_agent_id="agent-qma-replay-test",
            environment_kind="qmb-operator-replay",
        )
    )
    # QMB receives the actual registered Task dispatch lease; QMA does not
    # claim a compute-environment lease for QMB's separately owned runner.
    assert accepted.dispatch_lease.task_id == task_id
    assert accepted.environment_lease is None
    lease = accepted.dispatch_lease
    _ok(
        process.execution_environments.register_declaration(
            ExecutionEnvironmentDeclaration.isolated(
                ExecutionEnvironmentKind.LOCAL,
                provider_ref="local-ct40-recorded-replay",
            )
        )
    )
    loaded = process.roster.loader.get("analysis-backtest")
    assert loaded is not None
    tool = next(
        row
        for row in loaded.published
        if row.point == "tool" and row.qualified_id == QMB_BACKTEST_TOOL_ID
    )
    (daemon_root / "operator-config.json").write_text(
        json.dumps(
            {
                "qmb_bindings": {
                    loaded.instance_id: {
                        "owner_actor_id": actor.value,
                        "environment_ref": "env:local",
                        "config_revision": 2,
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    registered_rows: list[object] = []

    def register_spec(split_fp1: Fingerprint) -> Fingerprint:
        config_ref = _ok(content_address({"class": "qma-ct40-replay-runtime-v1"}))
        spec = _ok(
            ExperimentSpec.try_create(
                data_ref=split_fp1.value,
                environment_ref="env:local",
                seed=3,
                model_and_harness_version={"model": "local-replay-test", "harness": "qmb"},
                cost_assumptions={"spread_usd_cents": 0},
                resolved_config_ref=config_ref.value,
            )
        )
        registered = _ok(
            process.experiments.register(
                spec,
                dispatch_lease=lease,
                model_deployment_ref="deploy:local-replay-test",
            )
        )
        _ok(
            process.experiments.append_evidence(
                spec_fp1=registered.spec.spec_fp1,
                dispatch_lease=lease,
                model_deployment_ref="deploy:local-replay-test",
                body={"note": "recorded local replay model deployment"},
            )
        )
        registered_rows.append(registered)
        return _ok(Fingerprint.try_create(registered.spec.spec_fp1))

    runtime_env, roots, request_ref = _prepare_runtime_builder()(
        tmp_path / "qmb-runtime", register_experiment=register_spec
    )
    monkeypatch.setenv("QMB_REPLAY_RUNTIME_ROOT", runtime_env["QMB_REPLAY_RUNTIME_ROOT"])
    executable = os.environ.get("QMB_EXECUTABLE")
    if executable:
        monkeypatch.setenv("PATH", f"{Path(executable).parent}{os.pathsep}{os.environ['PATH']}")
    registered_spec = cast(Any, registered_rows[0]).spec

    descriptor = next(
        row
        for row in public_operation_descriptors()
        if row.op_id == "qmb.backtest.run" and row.version == 1
    )
    payload = {
        "run_fp1": registered_spec.spec_fp1,
        "evidence_ref": request_ref.value,
    }
    input_hash = _ok(compute_input_hash(payload, descriptor=descriptor))
    listener_tests = (
        Path(__file__).resolve().parents[2] / "qmx-agents" / "packages" / "qma-daemon" / "tests"
    )
    if str(listener_tests) not in sys.path:
        sys.path.insert(0, str(listener_tests))
    listener_helpers = importlib.import_module("test_pairing_listener")

    async def run_over_authenticated_listener() -> tuple[str, str, str]:
        bound = _ok(await process.bind())
        _pairing_id, pairing_proof = await listener_helpers._pair_over_listener(
            process, bound.host, bound.port
        )
        reader, writer = await listener_helpers._upgrade_paired_ws(
            bound.host, bound.port, pairing_proof
        )

        async def request(req_id: int, method: str, params: dict[str, object]) -> dict[str, object]:
            listener_helpers._ws_write(
                writer,
                {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params},
            )
            return await listener_helpers._ws_read_json(reader)

        try:
            initialized = await listener_helpers._initialize_ws(writer, reader, capabilities={})
            assert "error" not in initialized, initialized
            opened = await request(
                2,
                WireCommand.OPEN_PRODUCT_SESSION.value,
                {
                    "instance_id": loaded.instance_id,
                    "qualified_id": tool.qualified_id,
                    "package_version": tool.package_version,
                },
            )
            assert "error" not in opened, opened
            open_result = cast(dict[str, object], opened["result"])
            session_ref = cast(str, open_result["product_session_id"])
            granted = await request(
                3,
                WireCommand.GRANT_PRODUCT_SESSION.value,
                {
                    "product_session_ref": session_ref,
                    "expected_revision": 0,
                    "op_id": descriptor.op_id,
                    "op_version": descriptor.version,
                    "parameter_ceiling": {"allow_keys": ["run_fp1", "evidence_ref"]},
                    "expires_at": "2099-01-01T00:00:00Z",
                },
            )
            assert "error" not in granted, granted
            grant_result = cast(dict[str, object], granted["result"])
            envelope = {
                "logical_invocation_id": task_id,
                "attempt_id": 1,
                "op_id": descriptor.op_id,
                "op_version": descriptor.version,
                "contribution": {
                    "qualified_id": tool.qualified_id,
                    "package_version": tool.package_version,
                },
                "instance_id": loaded.instance_id,
                "config_revision": 2,
                "grant_id": grant_result["grant_id"],
                "effect_class": descriptor.effect_class.value,
                "idempotency_key": "idem:qma-ct40-registered-replay",
                "reconcile_policy": "query-then-decide",
                "input_hash": input_hash,
                "call_depth": 0,
                "caller_kind": "user",
                "caller_session_ref": session_ref,
            }
            invoked = await request(
                4,
                WireCommand.START_MISSION.value,
                {
                    "product_session_ref": session_ref,
                    "envelope": envelope,
                    "payload": payload,
                },
            )
            assert "error" not in invoked, invoked
            invoke_result = cast(dict[str, object], invoked["result"])
            job_id = cast(str, invoke_result["job_id"])
            assert process.jobs.handle_for(job_id) is not None
            assert process.backtesting.occupying_job("env:local") == job_id
            assert isinstance(process.backtesting.transport, CliQmbDoorTransport)
            exit_code = process.backtesting.transport.wait(job_id, timeout=60.0)
            assert exit_code == 0
            terminal_result: dict[str, object] = {}
            for _ in range(100):
                terminal = await request(
                    5,
                    WireQuery.GET_JOB.value,
                    {"product_session_ref": session_ref, "handle_id": job_id},
                )
                assert "error" not in terminal, terminal
                terminal_result = cast(dict[str, object], terminal["result"])
                if terminal_result["state"] in {
                    JobHandleState.DONE.value,
                    JobHandleState.FAILED.value,
                }:
                    break
                await asyncio.sleep(0.01)
            assert terminal_result["state"] == JobHandleState.DONE.value

            # Revoking the retained dispatch authority prevents a second child
            # even though the ProductSession grant still names the same operation.
            process.task_dispatcher.store.release_leases(task_id)
            replayed_envelope = dict(envelope)
            replayed_envelope["attempt_id"] = 2
            replayed_envelope["idempotency_key"] = "idem:qma-ct40-released-lease"
            refused_replay = await request(
                10,
                WireCommand.START_MISSION.value,
                {
                    "product_session_ref": session_ref,
                    "envelope": replayed_envelope,
                    "payload": payload,
                },
            )
            assert "error" in refused_replay, refused_replay
            assert process.jobs.handle_for(job_id) is not None
            assert len(cast(CliQmbDoorTransport, process.backtesting.transport).spawned) == 1

            reconnect_reader, reconnect_writer = await listener_helpers._upgrade_paired_ws(
                bound.host, bound.port, pairing_proof
            )
            try:
                reinitialized = await listener_helpers._initialize_ws(
                    reconnect_writer, reconnect_reader, capabilities={}
                )
                assert "error" not in reinitialized, reinitialized
                recovered_session = await request_on(
                    listener_helpers,
                    reconnect_writer,
                    reconnect_reader,
                    6,
                    WireQuery.GET_PRODUCT_SESSION.value,
                    {"product_session_ref": session_ref},
                )
                assert "error" not in recovered_session, recovered_session
                session_payload = cast(dict[str, object], recovered_session["result"])
                assert session_payload["product_session_id"] == session_ref
                assert len(cast(list[object], session_payload["grant_records"])) == 1
                recovered_job = await request_on(
                    listener_helpers,
                    reconnect_writer,
                    reconnect_reader,
                    7,
                    WireQuery.GET_JOB.value,
                    {"product_session_ref": session_ref, "handle_id": job_id},
                )
                assert "error" not in recovered_job, recovered_job
                assert (
                    cast(dict[str, object], recovered_job["result"])["state"]
                    == JobHandleState.DONE.value
                )
            finally:
                reconnect_writer.close()
                await reconnect_writer.wait_closed()

            rows = [
                json.loads(line)
                for path in roots["terminal_ledger"].rglob("ledger.jsonl")
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            assert len(rows) == 1
            assert rows[0]["ct32_fingerprint"].startswith("fp1:sha256:")
            assert rows[0]["measures"]
            return session_ref, job_id, pairing_proof
        finally:
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    try:
        session_ref, job_id, pairing_proof = asyncio.run(run_over_authenticated_listener())
        process.close()
        process = _ok(
            DaemonProcess.compose(
                daemon_root,
                machine="ct40-replay-test",
                boot_epoch_id="ct40-replay-test-restarted",
                bind_port=0,
                plugin_load_configs=research_corpus_plugin_load_config(seed),
            )
        )

        async def read_after_restart() -> None:
            bound_after_restart = _ok(await process.bind())
            reader, writer = await listener_helpers._upgrade_paired_ws(
                bound_after_restart.host, bound_after_restart.port, pairing_proof
            )
            try:
                initialized = await listener_helpers._initialize_ws(writer, reader, capabilities={})
                assert "error" not in initialized, initialized
                recovered_session = await request_on(
                    listener_helpers,
                    writer,
                    reader,
                    8,
                    WireQuery.GET_PRODUCT_SESSION.value,
                    {"product_session_ref": session_ref},
                )
                assert "error" not in recovered_session, recovered_session
                recovered_job = await request_on(
                    listener_helpers,
                    writer,
                    reader,
                    9,
                    WireQuery.GET_JOB.value,
                    {"product_session_ref": session_ref, "handle_id": job_id},
                )
                assert "error" not in recovered_job, recovered_job
                assert (
                    cast(dict[str, object], recovered_job["result"])["state"]
                    == JobHandleState.DONE.value
                )
            finally:
                writer.close()
                await writer.wait_closed()
                await process.aclose()

        asyncio.run(read_after_restart())
    finally:
        process.close()


def test_coordinated_lease_and_deployment_refusal_happen_before_spawn(tmp_path: Path) -> None:
    lease = DispatchLease(
        task_id="task-qma-authority-preflight",
        holder_agent_id="agent-qma-replay-test",
        mission_id="mission-qma-replay-test",
        owner=_owner(),
    )
    experiments = ExperimentSpecService()
    registered_rows: list[object] = []

    def register_spec(split_fp1: Fingerprint) -> Fingerprint:
        config_ref = _ok(content_address({"class": "qma-authority-preflight-runtime-v1"}))
        spec = _ok(
            ExperimentSpec.try_create(
                data_ref=split_fp1.value,
                environment_ref="env:docker",
                seed=4,
                model_and_harness_version={"model": "local-replay-test", "harness": "qmb"},
                cost_assumptions={"spread_usd_cents": 0},
                resolved_config_ref=config_ref.value,
            )
        )
        registered = _ok(
            experiments.register(
                spec,
                dispatch_lease=lease,
                model_deployment_ref="deploy:preflight",
            )
        )
        _ok(
            experiments.append_evidence(
                spec_fp1=registered.spec.spec_fp1,
                dispatch_lease=lease,
                model_deployment_ref="deploy:preflight",
                body={"note": "registered deployment provenance"},
            )
        )
        registered_rows.append(registered)
        return _ok(Fingerprint.try_create(registered.spec.spec_fp1))

    _env, _roots, request_ref = _prepare_runtime_builder()(
        tmp_path / "qmb-runtime", register_experiment=register_spec
    )
    registered_spec = cast(Any, registered_rows[0]).spec
    environments = ExecutionEnvironmentRegistry()
    _ok(
        environments.register_declaration(
            ExecutionEnvironmentDeclaration.isolated(
                ExecutionEnvironmentKind.DOCKER, provider_ref="local-preflight"
            )
        )
    )
    transport = CliQmbDoorTransport(argv0=(str(Path(sys.executable).with_name("qmb")),))
    service = BacktestingService(
        tools=ToolRegistry(),
        jobs=JobHandleService(),
        environments=environments,
        transport=transport,
        experiments=experiments,
    )
    try:
        _ok(service.install())
        wrong_lease = DispatchLease(
            task_id="task-foreign-authority",
            holder_agent_id=lease.holder_agent_id,
            mission_id=lease.mission_id,
            owner=lease.owner,
        )
        for task_id, attempt_lease, deployment in (
            ("task-foreign-authority", wrong_lease, "deploy:preflight"),
            ("task-qma-authority-preflight", lease, "deploy:stale"),
        ):
            refused = service.invoke(
                QMB_BACKTEST_TOOL_ID,
                owner=lease.owner,
                task_id=task_id,
                environment_ref="env:docker",
                experiment_spec_fp1=registered_spec.spec_fp1,
                evidence_ref=request_ref.value,
                dispatch_lease=attempt_lease,
                model_deployment_ref=deployment,
            )
            assert not is_ok(refused), refused
            assert service.jobs.handle_for(f"qmb:env:docker:{task_id}") is None
        assert transport.spawned == ()
        resolved = _ok(experiments.resolve(registered_spec.spec_fp1))
        assert len(resolved.ledger.entries) == 1
    finally:
        transport.close()
