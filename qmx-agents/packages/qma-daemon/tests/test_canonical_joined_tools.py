"""Offline canonical Agent ceiling plus actual ProductSession read admission."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from qma.core.barriers.capability import CapabilityRung
from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.operations import public_operation_descriptors
from qma.core.ports.capabilities import RoleBase
from qma.core.ports.permissions import PermissionPolicy
from qma.core.ports.tools import ToolKind, ToolRecord
from qma.core.vocabulary.enums import TaskMissionState
from qma.daemon.capabilities.spawn import SpawnRequest
from qma.daemon.knowledge.service import KnowledgeService
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.actor_workflow import ActorWorkflowProvider
from qma.daemon.request_runtime.canonical_join import CanonicalJoinPlan
from qma.daemon.request_runtime.contracts import CopilotProfile, ProviderRequest, RequestSpec
from qma.daemon.request_runtime.daemon_bridge import AgentRequestPolicy
from qma.daemon.request_runtime.providers import ProviderError
from qma.daemon.request_runtime.tool_loop import ToolBinding
from qma.daemon.taskgraph.records import TaskGraph, TaskRecord
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from qma.wire.invocation_envelope import PublicCallTransport, compute_input_hash
from qmf.core import is_refusal
from test_actor_workflow import app_setup, final, save_catalog, wait_finished
from test_request_runtime_configured_daemon import app_session
from test_request_runtime_daemon import receipt, rpc, submit_params, value, ws_connect
from test_request_runtime_tool_loop import ScriptedText


@pytest.mark.parametrize(
    "mode",
    [
        "allowed",
        "narrow",
        "no_permission",
        "no_tool",
        "unavailable",
        "unmapped",
        "wrong_acts",
        "wrong_schema",
        "unknown_record",
        "legacy_expanded",
        "revoked",
        "expired",
        "collision",
        "changed_alias",
        "changed_scope",
        "changed_callback",
        "changed_revision",
        "changed_grant",
        "regrant",
        "became_unavailable",
        "revoked_after_model",
        "child_escalation",
        "restart_completed",
        "restart_interrupted",
        "dispatch_decoy_callback",
        "dispatch_decoy_operation",
    ],
)
def test_joined_paired_read_respects_agent_and_current_grant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    sdk, instance, contribution, _snapshot, provider = app_setup(tmp_path, monkeypatch)
    body = json.loads((tmp_path / "actor-workflows.json").read_text())
    body["workflows"][0]["steps"].pop(1)
    body["roles"][1]["tools"] = []  # reviewer cannot inherit analyst's tool
    save_catalog(tmp_path, body)
    provider.responses.pop(2)  # reviewer receives final only
    process = value(
        DaemonProcess.compose(
            tmp_path,
            machine="tool-join-test",
            boot_epoch_id="tools",
            bind_port=0,
            plugin_load_configs=research_corpus_plugin_load_config(tmp_path / "corpus"),
        )
    )
    try:
        if mode in {"narrow", "expired"}:
            value(
                process.product_sessions.mint(
                    product_session_id="psess:configured-app",
                    profile="app-use",
                    principal="operator",
                    contribution={"qualified_id": contribution, "package_version": "0.1.0"},
                    instance_id=instance,
                    config_revision=1,
                    as_of="2026-10-03T00:00:00Z",
                )
            )
            value(
                process.product_sessions.host_grant(
                    "psess:configured-app",
                    grant_id="grant:configured-browse",
                    op_id="qml.research.browse",
                    op_version=1,
                    effect_class="read",
                    parameter_ceiling={"allow_keys": ["snapshot_ref"]},
                    expires_at="2020-01-01T00:00:00Z"
                    if mode == "expired"
                    else "2099-01-01T00:00:00Z",
                )
            )
        else:
            app_session(process, instance, contribution)
        if mode == "revoked":
            value(
                process.product_sessions.revoke_grant(
                    "psess:configured-app",
                    grant_id="grant:configured-browse",
                    principal="operator",
                    reason="test revoked",
                    revoked_at="2026-10-03T00:00:00Z",
                )
            )
        alternate = next(
            d for d in public_operation_descriptors() if d.op_id == "qmn.evidence.query"
        )
        if mode == "dispatch_decoy_operation":
            value(
                process.product_sessions.host_grant(
                    "psess:configured-app",
                    grant_id="grant:foreign-operation",
                    op_id=alternate.op_id,
                    op_version=alternate.version,
                    effect_class="read",
                    parameter_ceiling={"allow_keys": ["query"]},
                    expires_at="2099-01-01T00:00:00Z",
                )
            )
        available = [mode != "unavailable"]
        value(
            process.backtesting.tools.register_tool(
                ToolRecord(
                    "fixture:browse",
                    ToolKind.PLUGIN,
                    CapabilityRung.API_OR_STRUCTURED_TOOL,
                    schema={"required_keys": ["snapshot_ref"], "optional_keys": ["locator"]}
                    if mode != "wrong_schema"
                    else {"required_keys": ["foreign"]},
                    acts=frozenset({"qml.research.browse" if mode != "wrong_acts" else "search"}),
                    check_fn=lambda: available[0],
                )
            )
        )
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
                    RoleBase(
                        "reader",
                        tool_ids=frozenset()
                        if mode in {"no_tool", "legacy_expanded"}
                        else frozenset({"fixture:browse"}),
                        toolset_ids=("legacy-aliases",) if mode == "legacy_expanded" else (),
                    ),
                    base_toolset_tool_ids={"legacy-aliases": ("research_browse",)},
                    role_policy=PermissionPolicy(
                        "reader",
                        frozenset() if mode == "no_permission" else frozenset({"library.read"}),
                    ),
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
        process.task_dispatcher.materialize(
            TaskGraph("graph:read-join", task.mission_id, tasks=(task,))
        )
        value(process.task_dispatcher.dispatch_task(task_id=task.id, holder_agent_id=agent.id))
        value(
            process.jobs.submit(
                owner=owner, task_id=task.id, originating_product_session_ref="psess:configured-app"
            )
        )
        manifest: dict[str, object] = dict(sdk["research_browse"])
        if mode != "unmapped":
            manifest["canonical_tool_id"] = (
                "fixture:unknown" if mode == "unknown_record" else "fixture:browse"
            )
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
                    CanonicalJoinPlan("operator", "app-reader", "quant:research", owner, task.id),
                ),
            )
        )

        assert process.agent_requests is not None
        runtime = process.agent_requests.runtime
        policy = process.agent_requests.policies["app-reader"]
        actor = runtime.providers[policy.provider_id]
        assert isinstance(actor, ActorWorkflowProvider)
        reads: list[str] = []
        foreign_effects: list[object] = []
        decoy_admissions: list[Any] = []
        original_read = KnowledgeService.supersedes_chain

        def observe(self: KnowledgeService, source_id: str) -> Any:
            reads.append(source_id)
            return original_read(self, source_id)

        monkeypatch.setattr(KnowledgeService, "supersedes_chain", observe)
        original_tools = actor.tools
        original_resolver = actor.admission_tools
        assert original_resolver is not None

        def changed(binding: ToolBinding) -> ToolBinding:
            if mode == "changed_scope":
                return replace(binding, argument_scope=())
            if mode == "changed_grant":
                return replace(binding, grant_id="grant:foreign")
            if mode == "changed_callback":

                def foreign(arguments: Mapping[str, object]) -> Mapping[str, object]:
                    foreign_effects.append(arguments)
                    return {"foreign": True}

                return replace(binding, execute=foreign)
            assert binding.host_identity is not None
            return replace(binding, host_identity=replace(binding.host_identity, revision=2))

        if mode in {"changed_scope", "changed_grant", "changed_callback", "changed_revision"}:

            def substituted_tools(request: ProviderRequest) -> Mapping[str, ToolBinding]:
                return {
                    alias: changed(binding) for alias, binding in original_tools(request).items()
                }

            actor.tools = substituted_tools
        if mode == "collision":
            actor.routes = tuple(
                replace(r, tools=("research_browse", "alternate")) for r in actor.routes
            )

            def colliding_tools(spec: RequestSpec) -> Mapping[str, ToolBinding]:
                return {
                    **original_resolver(spec),
                    "alternate": original_resolver(spec)["research_browse"],
                }

            actor.admission_tools = colliding_tools
        if mode == "child_escalation":
            provider.responses[2] = json.dumps(
                {
                    "type": "tool",
                    "tool": "research_browse",
                    "arguments": {"snapshot_ref": _snapshot},
                }
            )

        def after(count: int) -> None:
            if count == 1:
                if mode in {"dispatch_decoy_callback", "dispatch_decoy_operation"}:
                    request_id = provider.requests[-1].request_id
                    row = value(runtime.get(request_id))
                    actual = original_resolver(row.spec)["research_browse"]
                    descriptor = (
                        alternate if mode == "dispatch_decoy_operation" else actual.descriptor
                    )
                    arguments = (
                        {"query": "latest"}
                        if mode == "dispatch_decoy_operation"
                        else {"snapshot_ref": _snapshot}
                    )
                    grant_id = (
                        "grant:foreign-operation"
                        if mode == "dispatch_decoy_operation"
                        else actual.grant_id
                    )
                    invocation = request_id + ":decoy"
                    envelope = {
                        "logical_invocation_id": invocation,
                        "attempt_id": 1,
                        "op_id": descriptor.op_id,
                        "op_version": descriptor.version,
                        "contribution": {
                            "qualified_id": actual.contribution.qualified_id,
                            "package_version": actual.contribution.package_version,
                        },
                        "instance_id": actual.instance.instance_id,
                        "config_revision": actual.instance.config_revision,
                        "grant_id": grant_id,
                        "effect_class": "read",
                        "idempotency_key": invocation,
                        "reconcile_policy": "query-then-decide",
                        "input_hash": value(compute_input_hash(arguments, descriptor=descriptor)),
                        "call_depth": 0,
                        "caller_kind": "agent",
                    }
                    kwargs: dict[str, Any] = {
                        "transport": PublicCallTransport.IN_PROCESS,
                        "envelope": envelope,
                        "payload": arguments,
                        "now": actor.now(),
                        "contributions": {actual.contribution.as_tuple(): actual.contribution},
                        "descriptors": {(descriptor.op_id, descriptor.version): descriptor},
                        "instances": {
                            (
                                actual.instance.instance_id,
                                actual.instance.config_revision,
                            ): actual.instance
                        },
                    }
                    if mode == "dispatch_decoy_operation":
                        # Same session's independent grant genuinely admits this
                        # operation; it still must not widen the canonical Agent.
                        control = dict(envelope)
                        control["logical_invocation_id"] = invocation + ":control"
                        control["idempotency_key"] = invocation + ":control"
                        control_kwargs: dict[str, Any] = {**kwargs, "envelope": control}
                        value(
                            process.product_sessions.dispatch_public_call(
                                "psess:configured-app", **control_kwargs
                            )
                        )
                    if mode == "dispatch_decoy_callback":
                        kwargs["execute"] = foreign_effects.append
                    denied = runtime.dispatch_tool(
                        request_id,
                        tool_name="research_browse",
                        tool_binding=actual,
                        **kwargs,
                    )
                    decoy_admissions.append(denied)
                if mode == "changed_alias":
                    actor.routes = tuple(replace(r, tools=()) for r in actor.routes)
                elif mode == "became_unavailable":
                    available[0] = False
                elif mode == "revoked_after_model":
                    value(
                        process.product_sessions.revoke_grant(
                            "psess:configured-app",
                            grant_id="grant:configured-browse",
                            principal="operator",
                            reason="revoked before callback",
                            revoked_at="2026-10-03T00:00:00Z",
                        )
                    )
                elif mode == "regrant":
                    value(
                        process.product_sessions.regrant(
                            "psess:configured-app",
                            "grant:configured-browse",
                            context_revision=1,
                            grant_id="grant:replacement",
                            parameter_ceiling={"allow_keys": ["snapshot_ref"]},
                        )
                    )
            if count == 3 and mode == "restart_interrupted":
                raise ProviderError("outcome_unknown", "lost child owner after observed read")

        provider.after = after
        accepted_modes = {
            "allowed",
            "narrow",
            "changed_alias",
            "changed_scope",
            "changed_callback",
            "changed_revision",
            "changed_grant",
            "regrant",
            "became_unavailable",
            "revoked_after_model",
            "child_escalation",
            "restart_completed",
            "restart_interrupted",
            "dispatch_decoy_callback",
            "dispatch_decoy_operation",
        }
        successful = mode in {
            "allowed",
            "restart_completed",
            "dispatch_decoy_callback",
            "dispatch_decoy_operation",
        }
        request_id = ""

        async def journey() -> None:
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
                response = await rpc(
                    reader,
                    writer,
                    "submit_agent_request",
                    submit_params(session="psess:configured-app", profile="app-reader"),
                )
                if mode not in accepted_modes:
                    assert "error" in response, response
                    assert provider.requests == []
                    assert reads == [] and foreign_effects == []
                    assert process.canonical_requests is not None
                    assert process.canonical_requests._events("accepted") == []  # pyright: ignore[reportPrivateUsage]
                    return
                request_id = str(receipt(response)["request_id"])
                await asyncio.to_thread(wait_finished, process, request_id)
                row: dict[str, Any] = receipt(
                    await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {
                            "request_id": request_id,
                            "product_session_ref": "psess:configured-app",
                        },
                    )
                )
                if mode == "restart_interrupted":
                    assert row["status"] == "interrupted", row
                else:
                    assert row["status"] == ("completed" if successful else "failed"), row
                if successful:
                    assert len(provider.requests) == 3
                    assert row["canonical_join"]["task_id"] == task.id
                    assert row["activities"][1]["result"] == "review"
                    assert len(reads) == 1
                    assert json.loads(row["content"])["outputs"]["analysis"] == "analysis"
                    assert process.canonical_requests is not None
                    pinned = process.canonical_requests._events("accepted")[0]  # pyright: ignore[reportPrivateUsage]
                    assert pinned["contract_version"] == 2
                    binding = pinned["tool_bindings"]["research_browse"]
                    assert binding["canonical_tool_id"] == "fixture:browse"
                    assert binding["adapter_revision"] == 1
                    assert binding["resource_identity"]["source_id"]
                    assert json.loads(binding["descriptor_json"])["permission_requests"] == [
                        "library.read"
                    ]
                    assert json.loads(binding["registry_json"])["acts"] == ["qml.research.browse"]
                    assert row["canonical_join"]["tool_bindings"] == pinned["tool_bindings"]
                elif mode in {
                    "changed_scope",
                    "changed_callback",
                    "changed_revision",
                    "changed_grant",
                }:
                    assert row["error"] == "tool_denied"
                    assert provider.requests == [] and reads == []
                elif mode == "narrow":
                    assert row["error"] == "tool_denied"
                    assert len(provider.requests) == 1 and reads == []
                elif mode == "child_escalation":
                    assert row["error"] == "tool_denied"
                    assert len(provider.requests) == 3 and len(reads) == 1
                elif mode == "restart_interrupted":
                    assert len(provider.requests) == 3 and len(reads) == 1
                else:
                    assert len(provider.requests) == 1 and reads == []
                assert all(is_refusal(result) for result in decoy_admissions), decoy_admissions
                assert foreign_effects == []
                assert process.task_dispatcher.dispatch_lease_for(task.id) is not None
                assert process.jobs.handle_for_task(task.id) is not None
                expected_task_state = (
                    TaskMissionState.RUNNING
                    if mode
                    in {
                        "allowed",
                        "restart_completed",
                        "child_escalation",
                        "changed_scope",
                        "changed_callback",
                        "changed_revision",
                        "changed_grant",
                        "dispatch_decoy_callback",
                        "dispatch_decoy_operation",
                    }
                    else TaskMissionState.UNKNOWN
                )
                live_task = process.task_dispatcher.task_for(task.id)
                assert live_task is not None and live_task.state is expected_task_state
            finally:
                writer.close()
                await writer.wait_closed()
                await process.aclose()

        asyncio.run(journey())
        if mode in {"restart_completed", "restart_interrupted"}:
            assert process.canonical_requests is not None
            accepted_pin = process.canonical_requests._events("accepted")[0]  # pyright: ignore[reportPrivateUsage]
            process.close()
            recovered = value(
                DaemonProcess.compose(
                    tmp_path,
                    machine="tool-join-test",
                    boot_epoch_id="restart",
                    bind_port=0,
                    plugin_load_configs=research_corpus_plugin_load_config(tmp_path / "corpus"),
                )
            )
            try:
                # Quant registration is a trusted host startup step. The original
                # execution Agent remains absent; no authority is reconstructed.
                value(
                    recovered.mailboxes.open_for_quant(
                        Quant(
                            owner, DeskSlug.RESEARCH, "read-join", RoleName.RESEARCHER, "Read join"
                        )
                    )
                )
                fresh = ScriptedText([final("must not run")])
                altered = dict(manifest)
                altered["canonical_tool_id"] = "fixture:changed-after-restart"
                value(
                    recovered.configure_agent_requests(
                        providers={fresh.capabilities.provider_id: fresh},
                        policies={
                            "app-reader": replace(
                                policy, provider_id=fresh.capabilities.provider_id
                            )
                        },
                        profile_tools={"app-reader": frozenset({"research_browse"})},
                        research_browse=altered,
                        instance_revisions={instance: 1},
                        canonical_joins=(
                            CanonicalJoinPlan(
                                "operator", "app-reader", "quant:research", owner, task.id
                            ),
                        ),
                    )
                )
                assert (
                    recovered.agent_requests is not None
                    and recovered.canonical_requests is not None
                )
                restored_runtime = recovered.agent_requests.runtime
                restored = value(restored_runtime.get(request_id))
                assert recovered.canonical_requests._events("accepted")[0] == accepted_pin  # pyright: ignore[reportPrivateUsage]
                assert is_refusal(recovered.canonical_requests.guard("execute", restored))
                assert is_refusal(restored_runtime.retry_interrupted(request_id))
                assert reads and len(reads) == 1 and fresh.requests == []
                if mode == "restart_completed":
                    assert restored.result is not None
                    assert json.loads(restored.result.content)["outputs"]["analysis"] == "analysis"
                assert recovered.task_dispatcher.dispatch_lease_for(task.id) is None
                durable = recovered.task_dispatcher.store.durable
                assert durable is not None
                graph = durable.graph_for_task(task.id)
                assert graph is not None
                durable_task = graph.task_by_id(task.id)
                assert durable_task is not None and durable_task.owner == owner
                assert durable_task.state is (
                    TaskMissionState.RUNNING
                    if mode == "restart_completed"
                    else TaskMissionState.UNKNOWN
                )
                handle = recovered.jobs.handle_for_task(task.id)
                assert handle is not None and handle.state.value == "unknown"
                assert accepted_pin["dispatch_lease"]["task_id"] == task.id

                async def replay_attempt() -> None:
                    value(await recovered.bind())
                    reader, writer, opening = await ws_connect(recovered)
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
                        denied = await rpc(
                            reader,
                            writer,
                            "resume_agent_request",
                            {
                                "request_id": request_id,
                                "product_session_ref": "psess:configured-app",
                            },
                        )
                        assert "error" in denied, denied
                        duplicate = await rpc(
                            reader,
                            writer,
                            "submit_agent_request",
                            submit_params(session="psess:configured-app", profile="app-reader"),
                        )
                        # Duplicate submission is an idempotent receipt lookup,
                        # never execution replay. A new submission still refuses.
                        assert receipt(duplicate)["request_id"] == request_id
                        new_request = await rpc(
                            reader,
                            writer,
                            "submit_agent_request",
                            submit_params(
                                key="restart-fresh",
                                session="psess:configured-app",
                                profile="app-reader",
                            ),
                        )
                        assert "error" in new_request, new_request
                        assert len(reads) == 1 and fresh.requests == []
                    finally:
                        writer.close()
                        await writer.wait_closed()
                        await recovered.aclose()

                asyncio.run(replay_attempt())
            finally:
                recovered.close()
    finally:
        process.close()
