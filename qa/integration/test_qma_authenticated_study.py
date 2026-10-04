"""Same admitted TaskAgent authors CT47, executes Study, and reopens over CT40.

The injected provider and local Alternative interpreter are explicitly synthetic,
offline fixtures. Data, requests, split, trials, journals, and witnesses are real
persisted domain artifacts. No registration or deployment receipt is fabricated.
"""

# ruff: noqa: S101
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import socket
import struct
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from operator_study_fixture_support import ok, prepare_study_inputs, write_study_binding
from qma.core.ontology import ActorId, DeskSlug, Goal, Quant, RoleName
from qma.core.operations import public_operation_descriptors
from qma.core.ports.capabilities import RoleBase
from qma.core.ports.execution import ExecutionEnvironmentDeclaration
from qma.core.ports.experiments import ExperimentSpec
from qma.core.ports.permissions import PermissionPolicy
from qma.core.ports.qmb import QMB_BACKTEST_TOOL_ID
from qma.core.vocabulary.enums import ExecutionEnvironmentKind, JobHandleState
from qma.daemon.backtest import CliQmbDoorTransport
from qma.daemon.capabilities.spawn import SpawnRequest
from qma.daemon.request_runtime.contracts import CopilotProfile
from qma.daemon.request_runtime.daemon_bridge import AgentRequestPolicy
from qma.daemon.taskgraph.compiler import CompileRequest
from qma.daemon.taskgraph.records import GraphTemplate
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from qma.wire.invocation_envelope import compute_input_hash
from qmf.core import Fingerprint, is_refusal
from test_experiment_authoring_requests import DEPLOYMENT, SyntheticAuthor
from test_pairing_listener import _pair_over_listener, _upgrade_paired_ws, _ws_write
from test_request_runtime_daemon import compose, mint, submit_params


async def rpc(
    reader: Any, writer: Any, method: str, params: dict[str, object], *, req_id: int = 1
) -> dict[str, Any]:
    """Read complete response frames with a bound suitable for real QML preflight."""
    _ws_write(writer, {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
    await writer.drain()
    while True:
        head = await asyncio.wait_for(reader.readexactly(2), timeout=90)
        length = head[1] & 0x7F
        if length == 126:
            length = struct.unpack("!H", await reader.readexactly(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", await reader.readexactly(8))[0]
        body = await asyncio.wait_for(reader.readexactly(length), timeout=90)
        if head[0] & 0x0F == 1:
            response = json.loads(body)
            if response.get("id") == req_id:
                return response


def result(response: dict[str, Any]) -> dict[str, Any]:
    assert "error" not in response, response
    return response["result"]


def snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize("mode", ["cancel", "complete", "wrong-owner"])
def test_authenticated_author_to_study_durable_public_readback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    cancel = mode == "cancel"
    inputs = prepare_study_inputs(tmp_path / "recorded")
    root = tmp_path / "daemon"
    process = compose(root)
    provider = SyntheticAuthor(
        content=json.dumps(
            {
                "data_ref": inputs.context.split_manifest_fp1.value,
                "environment_ref": "env:local",
                "resolved_config_ref": inputs.config.fingerprint.value,
                "seed": 12,
                "cost_assumptions": {"provider_usd_cents": 0},
            }
        )
    )
    owner = ok(ActorId.mint(DeskSlug.ANALYSIS, "authenticated-study"))
    quant = Quant(
        actor_id=owner,
        desk=DeskSlug.ANALYSIS,
        quant_slug="authenticated-study",
        role=RoleName.RESEARCHER,
        name="Offline Study author",
    )
    ok(process.mailboxes.open_for_quant(quant))
    mint(process)
    agent_id = "agent:admitted-study-author"
    ok(
        process.agent_capabilities.spawn(
            SpawnRequest(
                agent_id=agent_id,
                owner=owner,
                session_id="session:study-author",
                role_base=RoleBase("experiment-author"),
                role_policy=PermissionPolicy(
                    "experiment-author", frozenset({"experiment.register"})
                ),
            )
        )
    )
    # Predict the immutable identity for the declared graph inputs; only the
    # authenticated provider execution below may actually register this spec.
    candidate = ok(
        ExperimentSpec.try_create(
            **json.loads(provider.content),
            model_and_harness_version={"model": DEPLOYMENT, "harness": "qma-request-runtime-v1"},
        )
    )
    assert is_refusal(process.experiments.resolve(candidate.spec_fp1))
    loaded = process.roster.loader.get("analysis-backtest")
    assert loaded is not None
    tool = next(
        row
        for row in loaded.published
        if row.point == "tool" and row.qualified_id == QMB_BACKTEST_TOOL_ID
    )
    template = GraphTemplate(
        qualified_id="qma-test:authenticated-study",
        version="1",
        nodes=(
            {
                "id": "study",
                "kind": "task",
                "intent": "author and execute offline Study",
                "inputs": {
                    "op_id": "qmb.optimize.run",
                    "op_version": 1,
                    "instance_id": loaded.instance_id,
                    "config_revision": 2,
                    "run_fp1": candidate.spec_fp1,
                    "evidence_ref": inputs.context.evidence_ref.value,
                    "model_deployment_ref": DEPLOYMENT,
                    "agent_session_ref": "session:study-author",
                    "authoring_product_session_ref": "psess:agent",
                    "authoring_profile_id": "global",
                    "authoring_data_ref": candidate.data_ref,
                    "authoring_environment_ref": candidate.environment_ref,
                    "authoring_resolved_config_ref": candidate.resolved_config_ref,
                },
            },
        ),
    )
    ok(process.roster.templates.register(template))
    compiled = ok(
        process.roster.compiler.compile(
            CompileRequest(
                goal=Goal(text="Author and execute recorded offline Study"),
                owner=quant,
                graph_template_ref=template.qualified_id,
                graph_template_version="1",
                require_decomposition_reasoning=False,
            )
        )
    )
    task = compiled.task_graph.task_for_node("study")
    assert task is not None
    process.task_dispatcher.materialize(compiled.task_graph, mission=compiled.mission)
    dispatched = ok(
        process.task_dispatcher.dispatch_task(
            task_id=task.id,
            holder_agent_id=agent_id,
            environment_kind="qmb-operator-replay",
        )
    )
    lease = dispatched.dispatch_lease
    ledger = process.task_dispatcher.ledgers.get(task.id)
    assert ledger is not None
    (row,) = process.task_graphs.outbox_rows(compiled.task_graph.id)
    ok(
        process.configure_agent_requests(
            providers={provider.capabilities.provider_id: provider},
            policies={
                "global": AgentRequestPolicy(
                    profile=CopilotProfile("global"),
                    authority_profile="authoring",
                    provider_id=provider.capabilities.provider_id,
                    authoring_task_id=task.id,
                )
            },
        )
    )
    ok(
        process.execution_environments.register_declaration(
            ExecutionEnvironmentDeclaration.isolated(
                ExecutionEnvironmentKind.LOCAL, provider_ref="synthetic-offline-study"
            )
        )
    )
    config = {
        "research_corpus_root_path": str(root / "seed-corpus"),
        "qmb_local_environment": {"provider_ref": "synthetic-offline-study", "network": "none"},
        "qmb_bindings": {
            loaded.instance_id: {
                "owner_actor_id": owner.value,
                "environment_ref": "env:local",
                "config_revision": 2,
            }
        },
    }
    config_path = root / "operator-config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    inputs = replace(
        inputs,
        context=replace(
            inputs.context, experiment_spec_fp1=ok(Fingerprint.try_create(candidate.spec_fp1))
        ),
    )
    binding, inputs, plan = write_study_binding(tmp_path / "qmb-runtime", inputs)
    monkeypatch.setenv("QMB_REPLAY_RUNTIME_ROOT", str(tmp_path / "qmb-runtime"))
    descriptor = next(d for d in public_operation_descriptors() if d.op_id == "qmb.optimize.run")
    payload = {"run_fp1": candidate.spec_fp1, "evidence_ref": inputs.context.evidence_ref.value}
    proof: dict[str, Any] = {"provider": "synthetic offline injected fixture", "controls": []}

    async def journey() -> tuple[str, str, str, dict[str, Any]]:
        bound = ok(await process.bind())
        _, pairing_proof = await _pair_over_listener(process, bound.host, bound.port)
        reader, writer = await _upgrade_paired_ws(bound.host, bound.port, pairing_proof)
        try:
            result(
                await rpc(
                    reader,
                    writer,
                    "initialize",
                    {
                        "protocolVersion": WIRE_PROTOCOL_VERSION,
                        "capabilities": {},
                    },
                )
            )
            authored = result(
                await rpc(
                    reader,
                    writer,
                    "submit_agent_request",
                    submit_params(prompt="Return the pinned recorded experiment identity as JSON"),
                )
            )
            deadline = time.monotonic() + 20
            while True:
                author = result(
                    await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {
                            "product_session_ref": "psess:agent",
                            "request_id": authored["request_id"],
                        },
                    )
                )
                if author["status"] in {"completed", "failed", "interrupted"}:
                    break
                assert time.monotonic() < deadline
                await asyncio.sleep(0.01)
            assert author["status"] == "completed", author
            receipt = author["experiment_authoring"]
            assert receipt["spec_fp1"] == candidate.spec_fp1
            assert receipt["observed_deployment_ref"] == DEPLOYMENT
            assert receipt["request_id"] == provider.requests[0].request_id
            registered = ok(process.experiments.resolve_durable(candidate.spec_fp1))
            assert registered.dispatch_lease == lease
            assert registered.registering_attempt_no == ledger.attempt_no
            assert registered.registering_deployment_ref == DEPLOYMENT
            assert lease.holder_agent_id == agent_id
            proof["authoring"] = author
            session = result(
                await rpc(
                    reader,
                    writer,
                    "open_product_session",
                    {
                        "instance_id": loaded.instance_id,
                        "qualified_id": tool.qualified_id,
                        "package_version": tool.package_version,
                    },
                )
            )["product_session_id"]

            async def grant(revision: int) -> str:
                return result(
                    await rpc(
                        reader,
                        writer,
                        "grant_product_session",
                        {
                            "product_session_ref": session,
                            "expected_revision": revision,
                            "op_id": descriptor.op_id,
                            "op_version": 1,
                            "parameter_ceiling": {"allow_keys": list(payload)},
                            "expires_at": "2099-01-01T00:00:00Z",
                        },
                    )
                )["grant_id"]

            grant_id = await grant(0)
            envelope = {
                "logical_invocation_id": row.logical_invocation_id,
                "attempt_id": 1,
                "op_id": descriptor.op_id,
                "op_version": 1,
                "contribution": {
                    "qualified_id": tool.qualified_id,
                    "package_version": tool.package_version,
                },
                "instance_id": loaded.instance_id,
                "config_revision": 2,
                "grant_id": grant_id,
                "effect_class": descriptor.effect_class.value,
                "idempotency_key": "idem:study-author",
                "reconcile_policy": "query-then-decide",
                "input_hash": ok(compute_input_hash(payload, descriptor=descriptor)),
                "call_depth": 0,
                "caller_kind": "user",
                "caller_session_ref": session,
            }
            params = {"product_session_ref": session, "envelope": envelope, "payload": payload}
            ok(
                process.product_sessions.revoke_grant(
                    session,
                    grant_id=grant_id,
                    principal="operator",
                    reason="offline stale-grant control",
                    revoked_at="2026-10-04T00:00:00Z",
                )
            )
            rejected = await rpc(reader, writer, "start_mission", params)
            assert "error" in rejected, rejected
            proof["controls"].append({"stale_grant": rejected})
            revision = ok(process.product_sessions.get(session)).context_revision
            envelope["grant_id"] = await grant(revision)
            wrong_owner = ok(ActorId.mint(DeskSlug.ANALYSIS, "wrong-study-owner"))
            ok(
                process.mailboxes.open_for_quant(
                    Quant(
                        actor_id=wrong_owner,
                        desk=DeskSlug.ANALYSIS,
                        quant_slug="wrong-study-owner",
                        role=RoleName.RESEARCHER,
                        name="Negative control",
                    )
                )
            )
            config["qmb_bindings"][loaded.instance_id]["owner_actor_id"] = wrong_owner.value
            if mode == "wrong-owner":
                config_path.write_text(json.dumps(config), encoding="utf-8")
                rejected = await rpc(reader, writer, "start_mission", params)
                assert "error" in rejected, rejected
                assert "task_owner" in rejected["error"]["data"]["context"]["failed_checks"]
                assert not process.backtesting.transport.spawned
                assert not list(inputs.terminal_store.root.rglob("ledger.jsonl"))
                proof["controls"].append({"wrong_owner": rejected})
                return pairing_proof, session, "", {}
            config["qmb_bindings"][loaded.instance_id]["owner_actor_id"] = owner.value
            config_path.write_text(json.dumps(config), encoding="utf-8")
            assert isinstance(process.backtesting.transport, CliQmbDoorTransport)
            assert len(process.backtesting.transport.spawned) == 0
            accepted = result(await rpc(reader, writer, "start_mission", params))
            proof["accepted"] = accepted
            job_id = accepted["job_id"]
            assert len(process.backtesting.transport.spawned) == 1
            assert process.backtesting.transport.spawned[0].pid > 0
            duplicate = await rpc(reader, writer, "start_mission", params)
            assert "error" in duplicate, duplicate
            assert len(process.backtesting.transport.spawned) == 1
            proof["controls"].append({"duplicate": duplicate})
            changed = {**params, "envelope": {**envelope, "attempt_id": 4}}
            rejected = await rpc(reader, writer, "start_mission", changed)
            assert "error" in rejected, rejected
            proof["controls"].append({"changed_attempt": rejected})
            if cancel:
                cancel_handle = result(
                    await rpc(
                        reader,
                        writer,
                        "get_job",
                        {
                            "product_session_ref": session,
                            "handle_id": job_id,
                        },
                    )
                )
                cancelled = result(
                    await rpc(
                        reader,
                        writer,
                        "cancel_job",
                        {
                            "handle_id": job_id,
                            "logical_run_id": cancel_handle["logical_run_id"],
                            "attempt_id": cancel_handle["attempt_id"],
                            "expected_state": cancel_handle["state"],
                            "command_id": "cancel:offline-study",
                        },
                    )
                )
                proof["cancellation"] = cancelled
            deadline = time.monotonic() + 90
            while True:
                raw_readback = await rpc(
                    reader,
                    writer,
                    "get_job",
                    {
                        "product_session_ref": session,
                        "handle_id": job_id,
                    },
                )
                (tmp_path / "last-public-readback.json").write_text(
                    json.dumps(raw_readback, indent=2), encoding="utf-8"
                )
                readback = result(raw_readback)
                if readback["state"] in {"done", "failed", "cancelled", "unknown"}:
                    break
                assert time.monotonic() < deadline, readback
                await asyncio.sleep(0.05)
            proof["public_readback"] = readback
            if cancel:
                assert readback["state"] == JobHandleState.CANCELLED.value, readback
                assert not list(inputs.terminal_store.root.rglob("ledger.jsonl"))
                return pairing_proof, session, job_id, readback
            assert readback["state"] == JobHandleState.DONE.value, readback
            verified = readback["verified_result"]
            assert len(verified) == 7 and verified["study_fp1"] == plan.fingerprint.value
            assert len(verified["terminal_artifact_fp1s"]) == 2
            terminals = ok(
                inputs.terminal_store.read(
                    journal_store=inputs.journal_store, registry=inputs.registry_persistence
                )
            )
            assert len(terminals) == 2
            before = snapshot(tmp_path / "recorded")
            repeated = result(
                await rpc(
                    reader,
                    writer,
                    "get_job",
                    {
                        "product_session_ref": session,
                        "handle_id": job_id,
                    },
                )
            )
            assert repeated["verified_result"] == verified
            assert snapshot(tmp_path / "recorded") == before
            # Corrupt actual persisted source bytes, then restore the disposable fixture.
            archive = next(
                path
                for path in inputs.raw_store_root.rglob("*")
                if path.is_file() and "replay-requests" not in str(path)
            )
            original = archive.read_bytes()
            try:
                archive.write_bytes(b"changed source negative control")
                rejected = await rpc(
                    reader,
                    writer,
                    "get_job",
                    {
                        "product_session_ref": session,
                        "handle_id": job_id,
                    },
                )
                assert "error" in rejected, rejected
                proof["controls"].append({"changed_source": rejected})
            finally:
                archive.write_bytes(original)
            return pairing_proof, session, job_id, readback
        finally:
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    pairing_proof, session, job_id, readback = asyncio.run(journey())
    assert len(provider.requests) == 1
    if mode == "complete":
        # Start the normal module, with persisted operator configuration and no
        # injected provider. Read through its new authenticated listener process.
        with socket.socket() as reserve:
            reserve.bind(("127.0.0.1", 0))
            port = reserve.getsockname()[1]
        env = os.environ.copy()
        # Keep the installed console entrypoint from this interpreter's runtime
        # visible to the fresh module, even when the host token rewrites PATH.
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        env.update(
            QMA_DAEMON_ROOT=str(root),
            QMA_DAEMON_MACHINE="test-host",
            QMA_DAEMON_BOOT_EPOCH="study-public-restart",
            QMA_DAEMON_BIND_PORT=str(port),
        )
        with (tmp_path / "restart.log").open("w", encoding="utf-8") as log:
            child = subprocess.Popen(
                [sys.executable, "-m", "qma.daemon"],
                env=env,
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            async def reopened() -> dict[str, Any]:
                deadline = time.monotonic() + 30
                while True:
                    try:
                        reader, writer = await _upgrade_paired_ws("127.0.0.1", port, pairing_proof)
                        break
                    except OSError:
                        assert time.monotonic() < deadline, (tmp_path / "restart.log").read_text()
                        await asyncio.sleep(0.1)
                try:
                    result(
                        await rpc(
                            reader,
                            writer,
                            "initialize",
                            {
                                "protocolVersion": WIRE_PROTOCOL_VERSION,
                                "capabilities": {},
                            },
                        )
                    )
                    return result(
                        await rpc(
                            reader,
                            writer,
                            "get_job",
                            {
                                "product_session_ref": session,
                                "handle_id": job_id,
                            },
                        )
                    )
                finally:
                    writer.close()
                    await writer.wait_closed()

            before = snapshot(tmp_path / "recorded")
            try:
                restored = asyncio.run(reopened())
                assert restored["verified_result"] == readback["verified_result"]
                assert snapshot(tmp_path / "recorded") == before
                proof["fresh_module_readback"] = restored
                proof["restart_pid"] = child.pid
            finally:
                child.terminate()
                child.wait(timeout=15)
    proof.update(
        task_id=task.id,
        holder_agent_id=agent_id,
        study_descriptor=str(binding),
        study_fp1=plan.fingerprint.value,
        job_id=job_id,
        provider_call_count=len(provider.requests),
        persisted_files=snapshot(tmp_path / "recorded"),
    )
    (tmp_path / "authenticated-study-proof.json").write_text(
        json.dumps(proof, indent=2), encoding="utf-8"
    )
