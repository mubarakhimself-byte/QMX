"""Authored backend compositions with scripted inference only."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from copy import deepcopy
from dataclasses import replace
from itertools import pairwise
from pathlib import Path
from typing import Any

import pytest
from qma.core.barriers.capability import CapabilityRung
from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.ports.capabilities import RoleBase
from qma.core.ports.permissions import PermissionPolicy
from qma.core.ports.tools import ToolKind, ToolRecord
from qma.core.vocabulary.enums import NodeKind, TaskMissionState
from qma.daemon.capabilities.spawn import SpawnRequest
from qma.daemon.knowledge.service import KnowledgeService
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.actor_profiles import load_actor_catalog
from qma.daemon.request_runtime.authored_graphs import (
    compile_authored_graph,
    compile_graph_proposal,
    validate_graph_proposal,
)
from qma.daemon.request_runtime.canonical_join import CanonicalJoinPlan
from qma.daemon.request_runtime.contracts import CopilotProfile
from qma.daemon.request_runtime.daemon_bridge import AgentRequestPolicy
from qma.daemon.request_runtime.graph_storage import JournalRecords
from qma.daemon.request_runtime.providers import ProviderError
from qma.daemon.taskgraph.dispatcher import TaskGraphDispatcher
from qma.daemon.taskgraph.records import TaskRecord
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from test_actor_workflow import app_setup, catalog, final, save_catalog
from test_canonical_request_join import joined_host as joined_host_fixture
from test_request_runtime_configured_daemon import app_session
from test_request_runtime_daemon import receipt, rpc, submit_params, value, ws_connect


def authored(body: dict[str, Any]) -> dict[str, Any]:
    flow = body["workflows"][0]
    flow["steps"] = [s for s in flow["steps"] if s["id"] != "review"]
    flow["id"] = "fixture:assessment"
    body["routes"][0]["workflow"] = "fixture:assessment:1"
    flow["graph"] = {
        "author": "operator",
        "operations": {
            s["id"]: {"op_id": "qml.research.browse", "version": 1}
            for s in flow["steps"]
            if s["kind"] == "read"
        },
        "edges": [
            {
                "from": a["id"],
                "to": b["id"],
                "mapping": "one",
                "from_port": "data",
                "to_port": "data",
            }
            for a, b in pairwise(flow["steps"])
        ],
    }
    return flow


def test_host_loads_pinned_authored_template(tmp_path: Path) -> None:
    body = catalog(tmp_path)
    authored(body)
    save_catalog(tmp_path, body)
    loaded = load_actor_catalog(tmp_path)
    assert loaded is not None
    flow = loaded.workflows[0]
    assert flow.graph_sha256
    assert flow.template().qualified_id == "fixture:assessment"


def graph_host(
    root: Any,
    sdk: Any,
    instance: Any,
    contribution: Any,
    provider: Any,
    first: Any = True,
    joined: bool = True,
) -> Any:
    process = value(
        DaemonProcess.compose(
            root,
            machine="tool-join-test",
            boot_epoch_id="tools",
            bind_port=0,
            plugin_load_configs=research_corpus_plugin_load_config(root / "corpus"),
        )
    )
    value(
        process.backtesting.tools.register_tool(
            ToolRecord(
                "fixture:browse",
                ToolKind.PLUGIN,
                CapabilityRung.API_OR_STRUCTURED_TOOL,
                schema={"required_keys": ["snapshot_ref"], "optional_keys": ["locator"]},
                acts=frozenset({"qml.research.browse"}),
                check_fn=lambda: True,
            )
        )
    )
    if first:
        app_session(process, instance, contribution)
        owner = value(ActorId.mint(DeskSlug.RESEARCH, "read-join"))
        value(
            process.mailboxes.open_for_quant(
                Quant(owner, DeskSlug.RESEARCH, "read-join", RoleName.RESEARCHER, "Read join")
            )
        )
        agent = value(
            process.agent_capabilities.spawn(
                SpawnRequest(
                    "agent:read-join",
                    owner,
                    "session:read-join",
                    RoleBase("reader", tool_ids=frozenset({"fixture:browse"})),
                    role_policy=PermissionPolicy("reader", frozenset({"library.read"})),
                )
            )
        )
        task = TaskRecord(
            "task:read-join",
            "mission:read-join",
            owner,
            "read metadata",
            state=TaskMissionState.READY,
            inputs={
                "agent_session_ref": agent.session_id,
                "request_product_session_ref": "psess:configured-app",
                "request_profile_id": "app-reader",
            },
        )
        loaded = load_actor_catalog(root)
        assert loaded is not None
        compiled = value(
            compile_authored_graph(
                loaded.workflows[0],
                owner=Quant(
                    owner, DeskSlug.RESEARCH, "read-join", RoleName.RESEARCHER, "Read join"
                ),
                goal="Inspect retained corpus",
                logical_run_id="fixture-run",
            )
        )
        anchor = replace(
            compiled.task_graph.tasks[0], inputs=task.inputs, state=TaskMissionState.READY
        )
        process.task_dispatcher.materialize(
            replace(compiled.task_graph, tasks=(anchor, *compiled.task_graph.tasks[1:]))
        )
        task = anchor
        value(process.task_dispatcher.dispatch_task(task_id=task.id, holder_agent_id=agent.id))
        value(
            process.jobs.submit(
                owner=owner, task_id=task.id, originating_product_session_ref="psess:configured-app"
            )
        )
    if not first:
        restored_owner = value(ActorId.mint(DeskSlug.RESEARCH, "read-join"))
        value(
            process.mailboxes.open_for_quant(
                Quant(
                    restored_owner, DeskSlug.RESEARCH, "read-join", RoleName.RESEARCHER, "Read join"
                )
            )
        )
    loaded = load_actor_catalog(root)
    assert loaded is not None
    owner = value(ActorId.mint(DeskSlug.RESEARCH, "read-join"))
    quant = process.mailboxes.quant_for(owner)
    assert quant is not None
    compiled = value(
        compile_authored_graph(
            loaded.workflows[0],
            owner=quant,
            goal="Inspect retained corpus",
            logical_run_id="fixture-run",
        )
    )
    task_id = compiled.task_graph.tasks[0].id
    manifest: dict[str, object] = dict(sdk["research_browse"])
    manifest["canonical_tool_id"] = "fixture:browse"
    value(
        process.configure_agent_requests(
            providers={provider.capabilities.provider_id: provider},
            policies={
                "app-reader": AgentRequestPolicy(
                    CopilotProfile("app-reader", "application", app_instance_id=instance),
                    "app-use",
                    provider.capabilities.provider_id,
                )
            },
            profile_tools={"app-reader": frozenset({"research_browse"})},
            research_browse=manifest,
            instance_revisions={instance: 1},
            canonical_joins=(
                CanonicalJoinPlan(
                    "operator",
                    "app-reader",
                    "quant:research",
                    value(ActorId.mint(DeskSlug.RESEARCH, "read-join")),
                    task_id,
                ),
            )
            if joined
            else (),
        )
    )

    return process, task_id


def configure_graph(root: Any, monkeypatch: Any, composition: Any) -> Any:
    sdk, instance, contribution, snapshot, provider = app_setup(root, monkeypatch)
    body = json.loads((root / "actor-workflows.json").read_text())
    steps = [
        {
            "id": "metadata",
            "kind": "read",
            "tool": "research_browse",
            "arguments": {"snapshot_ref": snapshot},
        }
    ]
    if composition == "specialist":
        body["roles"][0]["tools"] = []
        steps.append({"id": "analysis", "kind": "agent", "role": "analyst:1"})
    else:
        steps.append(
            {
                "id": "source",
                "kind": "read",
                "tool": "research_browse",
                "arguments": {"snapshot_ref": snapshot, "locator": "README.md"},
            }
        )
    steps.append({"id": "collect", "kind": "collect"})
    body["workflows"][0]["steps"] = steps
    authored(body)
    save_catalog(root, body)
    provider.responses[:] = [final("synthetic specialist result")]
    return sdk, instance, contribution, provider


@pytest.mark.parametrize("composition", ["specialist", "deterministic"])
@pytest.mark.parametrize("fault", ["none", "checkpoint", "unknown"])
@pytest.mark.parametrize("joined", [True, False])
def test_paired_authored_composition_and_disk_reopen(
    tmp_path: Any, monkeypatch: Any, composition: Any, fault: Any, joined: bool
) -> None:
    sdk, instance, contribution, provider = configure_graph(tmp_path, monkeypatch, composition)
    from test_memory_provider_seam import FakeMemory, install_fake, selection

    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)
    process, task_id = graph_host(tmp_path, sdk, instance, contribution, provider, joined=joined)
    reads: list[str] = []
    original_read = KnowledgeService.supersedes_chain

    def observe(self: Any, source_id: Any) -> Any:
        reads.append(source_id)
        return original_read(self, source_id)

    monkeypatch.setattr(KnowledgeService, "supersedes_chain", observe)
    original_put = JournalRecords.put
    lost: list[bool] = []

    def lose_checkpoint(self: Any, kind: Any, key: Any, body: Any) -> Any:
        if fault != "none" and not lost and kind == "effect" and body.get("status") == "observed":
            lost.append(True)
            if fault == "checkpoint":
                original_put(self, kind, key, body)
            raise ProviderError("outcome_unknown", "synthetic predecessor receipt/checkpoint loss")
        return original_put(self, kind, key, body)

    monkeypatch.setattr(JournalRecords, "put", lose_checkpoint)
    request_id = ""

    async def journey(reopen: Any = False) -> Any:
        nonlocal request_id
        value(await process.bind())
        reader, writer, opening = await ws_connect(process)
        try:
            assert b"101 Switching Protocols" in opening
            receipt(
                await rpc(
                    reader,
                    writer,
                    "initialize",
                    {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
                )
            )
            if not reopen:
                request_id = str(
                    receipt(
                        await rpc(
                            reader,
                            writer,
                            "submit_agent_request",
                            submit_params(
                                session="psess:configured-app",
                                profile="app-reader",
                                prompt="Inspect corpus",
                            ),
                        )
                    )["request_id"]
                )
            elif fault != "none":
                denied = await rpc(
                    reader,
                    writer,
                    "resume_agent_request",
                    {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                )
                if joined:
                    assert "error" in denied, denied
                else:
                    receipt(denied)
            deadline = time.monotonic() + 30
            while True:
                row: Any = receipt(
                    await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                    )
                )
                if row["status"] in {"completed", "failed", "interrupted"}:
                    break
                assert time.monotonic() < deadline, row
                await asyncio.sleep(0.01)
            if fault != "none" and (not reopen or joined or fault == "unknown"):
                assert row["status"] == "interrupted", row
                assert len(reads) == 1
            else:
                assert row["status"] == "completed", row
                outputs = json.loads(row["content"])["outputs"]
                assert outputs["metadata"]
                if composition == "specialist":
                    assert outputs["collect"] == {"analysis": "synthetic specialist result"}
                    assert len(provider.requests) == 1
                else:
                    assert outputs["collect"] == {"source": outputs["source"]}
                    assert provider.requests == []
                if joined:
                    assert row["canonical_join"]["task_id"] == task_id
                else:
                    assert "canonical_join" not in row
                assert len(reads) == (1 if composition == "specialist" else 2)
        finally:
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    try:
        asyncio.run(journey())
    finally:
        process.close()
    process, reopened_task = graph_host(
        tmp_path, sdk, instance, contribution, provider, first=False, joined=joined
    )
    assert reopened_task == task_id
    try:
        asyncio.run(journey(True))
        binding = JournalRecords(process.journal).get("actor_job", request_id)
        assert binding is not None
        assert binding["authored_graph"]["author"] == "operator"
        assert process.task_dispatcher.dispatch_lease_for(task_id) is None
        if joined:
            assert process.jobs.handle_for_task(task_id).state.value == "unknown"
    finally:
        process.close()


@pytest.mark.parametrize("defect", ["cycle", "join", "digest", "wider", "operation"])
def test_host_refuses_invalid_authored_definition(tmp_path: Any, defect: Any) -> None:
    body = catalog(tmp_path)
    flow = authored(body)
    if defect == "cycle":
        flow["graph"]["edges"].append(
            {
                "from": "collect",
                "to": "normalize",
                "mapping": "one",
                "from_port": "data",
                "to_port": "data",
            }
        )
    elif defect == "join":
        flow["graph"]["edges"].append(
            {
                "from": "normalize",
                "to": "collect",
                "mapping": "one",
                "from_port": "data",
                "to_port": "data",
            }
        )
    elif defect == "digest":
        flow["graph"]["sha256"] = "0" * 64
    elif defect == "wider":
        body["roles"][0]["tools"] = ["arbitrary_code"]
    else:
        flow["steps"][0] = {
            "id": "normalize",
            "kind": "read",
            "tool": "uninstalled:operation:99",
            "arguments": {},
        }
    save_catalog(tmp_path, body)
    with pytest.raises(ValueError):
        load_actor_catalog(tmp_path)


@pytest.mark.parametrize("defect", ["none", "digest", "tools", "route"])
def test_proposal_is_validated_data_and_never_authority(tmp_path: Any, defect: Any) -> None:
    body = catalog(tmp_path)
    authored(body)
    save_catalog(tmp_path, body)
    loaded = load_actor_catalog(tmp_path)
    assert loaded is not None
    flow = loaded.workflows[0]
    proposed: dict[str, Any] = {
        "workflow": flow.key,
        "graph_sha256": flow.graph_sha256,
        "goal": "Inspect corpus",
    }
    if defect == "digest":
        proposed["graph_sha256"] = "0" * 64
    elif defect == "tools":
        proposed["tools"] = ["arbitrary_code"]
    elif defect == "route":
        proposed["workflow"] = "foreign:graph:1"
    if defect == "none":
        proposal = validate_graph_proposal(
            json.dumps(proposed), prompt="Inspect corpus", catalog=loaded, profile_id="global"
        )
        assert proposal.workflow == "fixture:assessment:1"
        assert proposal.goal == "Inspect corpus"
        assert not hasattr(proposal, "permissions")
    else:
        with pytest.raises(ValueError):
            validate_graph_proposal(
                json.dumps(proposed), prompt="Inspect corpus", catalog=loaded, profile_id="global"
            )


joined_host = joined_host_fixture


def test_prompt_led_paired_agent_proposes_validated_graph_job(
    tmp_path: Any, joined_host: Any
) -> None:
    process, provider = joined_host
    target = tmp_path / "proposal"
    target.mkdir()
    body = catalog(target)
    authored(body)
    save_catalog(target, body)
    loaded = load_actor_catalog(target)
    assert loaded is not None
    flow = loaded.workflows[0]
    proposal_json = json.dumps(
        {
            "workflow": flow.key,
            "graph_sha256": flow.graph_sha256,
            "goal": "Review a retained hypothesis",
        }
    )
    provider.responses[:] = [final(proposal_json), final("proposal review")]

    async def journey() -> Any:
        value(await process.bind())
        reader, writer, opening = await ws_connect(process)
        try:
            assert b"101 Switching Protocols" in opening
            receipt(
                await rpc(
                    reader,
                    writer,
                    "initialize",
                    {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
                )
            )
            request_id = str(
                receipt(
                    await rpc(
                        reader,
                        writer,
                        "submit_agent_request",
                        submit_params(prompt="Propose a pinned workflow to review a hypothesis"),
                    )
                )["request_id"]
            )
            deadline = time.monotonic() + 30
            while True:
                row: Any = receipt(
                    await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {"request_id": request_id, "product_session_ref": "psess:agent"},
                    )
                )
                if row["status"] == "completed":
                    break
                assert (
                    row["status"] not in {"failed", "interrupted"} and time.monotonic() < deadline
                ), row
                await asyncio.sleep(0.01)
            output = json.loads(row["content"])["outputs"]["analysis"]
            proposal = validate_graph_proposal(
                output,
                prompt="Propose a pinned workflow to review a hypothesis",
                catalog=loaded,
                profile_id="global",
            )
            assert proposal.goal == "Review a retained hypothesis"
            assert proposal.workflow == "fixture:assessment:1"
            assert len(provider.requests) == 2  # planning and review, no proposed execution
            # Explicit host compile is a separate operation; this result has no
            # lease and has not been dispatched by the model output.
            quant = process.mailboxes.quant_for(value(ActorId.mint(DeskSlug.RESEARCH, "joined")))
            assert quant is not None
            compiled = value(
                compile_graph_proposal(
                    proposal, catalog=loaded, owner=quant, logical_run_id="host-proposal-run"
                )
            )
            assert len(compiled.task_graph.tasks) == 1
            assert compiled.task_graph.graph_template_ref == "fixture:assessment"
            assert process.task_dispatcher.task_for(compiled.task_graph.tasks[0].id) is None
        finally:
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    asyncio.run(journey())


@pytest.mark.parametrize("defect", ["version", "cancel"])
@pytest.mark.parametrize("joined", [True, False])
def test_paired_authored_operation_version_and_cancel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str, joined: bool
) -> None:
    sdk, instance, contribution, provider = configure_graph(tmp_path, monkeypatch, "specialist")
    if defect == "version":
        body = json.loads((tmp_path / "actor-workflows.json").read_text())
        body["workflows"][0]["graph"]["operations"]["metadata"]["version"] = 99
        save_catalog(tmp_path, body)
    process, task_id = graph_host(tmp_path, sdk, instance, contribution, provider, joined=joined)
    entered = threading.Event()
    original_execute = provider.execute

    def blocked(request: Any, emit: Any, cancellation: Any) -> Any:
        entered.set()
        while not cancellation.wait(0.01):
            pass
        return original_execute(request, emit, cancellation)

    if defect == "cancel":
        monkeypatch.setattr(provider, "execute", blocked)

    async def journey() -> None:
        value(await process.bind())
        reader, writer, opening = await ws_connect(process)
        try:
            assert b"101 Switching Protocols" in opening
            receipt(
                await rpc(
                    reader,
                    writer,
                    "initialize",
                    {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
                )
            )
            response = await rpc(
                reader,
                writer,
                "submit_agent_request",
                submit_params(session="psess:configured-app", profile="app-reader"),
            )
            if defect == "version":
                assert "error" in response, response
                assert provider.requests == []
                return
            request_id = str(receipt(response)["request_id"])
            deadline = time.monotonic() + 30
            while not entered.is_set():
                assert time.monotonic() < deadline
                await asyncio.sleep(0.01)
            receipt(
                await rpc(
                    reader,
                    writer,
                    "cancel_agent_request",
                    {
                        "request_id": request_id,
                        "product_session_ref": "psess:configured-app",
                        "activity_id": request_id + ":child:analysis",
                    },
                )
            )
            while True:
                row: Any = receipt(
                    await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                    )
                )
                if row["status"] == "cancelled":
                    break
                assert time.monotonic() < deadline, row
                await asyncio.sleep(0.01)
            assert row["activities"][0]["status"] == "cancelled"
            assert process.task_dispatcher.dispatch_lease_for(task_id) is not None
            effect = JournalRecords(process.journal).get("effect", request_id + ":step:metadata")
            assert effect is not None and effect["status"] == "observed"
        finally:
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    try:
        asyncio.run(journey())
    finally:
        process.close()


def test_legacy_catalog_identity_matches_immutable_reviewed_base(tmp_path: Path) -> None:
    catalog(tmp_path)
    loaded = load_actor_catalog(tmp_path)
    assert loaded is not None
    assert loaded.identity == "468bc3ee613d11da94e2e87ced4fa493cb251697a8cbc8edfc85553c83943942"


@pytest.mark.parametrize("mutation", ["duplicate-node", "wrong-task-anchor"])
def test_paired_rejects_noncompiled_graph(tmp_path: Any, monkeypatch: Any, mutation: Any) -> None:
    sdk, instance, contribution, provider = configure_graph(tmp_path, monkeypatch, "specialist")
    original = TaskGraphDispatcher.materialize

    def corrupt(self: Any, graph: Any, **kwargs: Any) -> Any:
        if mutation == "duplicate-node":
            graph = replace(graph, nodes=(*graph.nodes, graph.nodes[0]))
        else:
            task = replace(
                graph.tasks[0], node_id="metadata", node_kind=NodeKind.ARTIFACT_DEPENDENCY
            )
            graph = replace(graph, tasks=(task,))
        return original(self, graph, **kwargs)

    monkeypatch.setattr(TaskGraphDispatcher, "materialize", corrupt)
    process, task_id = graph_host(tmp_path, sdk, instance, contribution, provider, joined=True)

    async def journey() -> None:
        value(await process.bind())
        reader, writer, opening = await ws_connect(process)
        try:
            receipt(
                await rpc(
                    reader,
                    writer,
                    "initialize",
                    {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
                )
            )
            response = await rpc(
                reader,
                writer,
                "submit_agent_request",
                submit_params(session="psess:configured-app", profile="app-reader"),
            )
            assert "error" in response, "noncompiled authored graph was admitted"
        finally:
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    try:
        asyncio.run(journey())
    finally:
        process.close()


def test_mixed_host_rejects_stale_unjoined_operation_before_acceptance(
    tmp_path: Any, monkeypatch: Any
) -> None:
    sdk, instance, contribution, provider = configure_graph(tmp_path, monkeypatch, "specialist")
    body = json.loads((tmp_path / "actor-workflows.json").read_text())
    stale = deepcopy(body["workflows"][0])
    stale["id"] = "fixture:stale-assessment"
    stale["graph"]["operations"]["metadata"]["version"] = 99
    body["workflows"].append(stale)
    route = deepcopy(body["routes"][0])
    route["profile_id"] = "other-reader"
    route["workflow"] = "fixture:stale-assessment:1"
    body["routes"].append(route)
    save_catalog(tmp_path, body)
    original = DaemonProcess.configure_agent_requests

    def configure(self: Any, **kwargs: Any) -> Any:
        policies = dict(kwargs["policies"])
        source = policies["app-reader"]
        policies["other-reader"] = replace(
            source, profile=replace(source.profile, profile_id="other-reader")
        )
        kwargs["policies"] = policies
        tools = dict(kwargs["profile_tools"])
        tools["other-reader"] = tools["app-reader"]
        kwargs["profile_tools"] = tools
        return original(self, **kwargs)

    monkeypatch.setattr(DaemonProcess, "configure_agent_requests", configure)
    process, task_id = graph_host(tmp_path, sdk, instance, contribution, provider, joined=True)

    async def journey() -> None:
        value(await process.bind())
        reader, writer, opening = await ws_connect(process)
        try:
            receipt(
                await rpc(
                    reader,
                    writer,
                    "initialize",
                    {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
                )
            )
            response = await rpc(
                reader,
                writer,
                "submit_agent_request",
                submit_params(session="psess:configured-app", profile="other-reader"),
            )
            assert "error" in response, (
                "stale authored operation was accepted before execution in a mixed host"
            )
        finally:
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    try:
        asyncio.run(journey())
    finally:
        process.close()
