"""Host admission joins bounded requests to existing authority, offline only."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.ports.capabilities import RoleBase
from qma.core.vocabulary.enums import JobHandleState, TaskMissionState
from qma.daemon.capabilities.spawn import SpawnRequest
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.actor_workflow import ActorWorkflowProvider
from qma.daemon.request_runtime.canonical_join import CanonicalJoinPlan, CanonicalRequestJoin
from qma.daemon.request_runtime.contracts import CopilotProfile, RequestRecord, RequestSpec
from qma.daemon.request_runtime.daemon_bridge import AgentRequestPolicy
from qma.daemon.request_runtime.graph_storage import JournalRecords
from qma.daemon.request_runtime.providers import ProviderError
from qma.daemon.taskgraph.records import TaskGraph, TaskRecord
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from qmf.core import Result, is_refusal
from qmf.data.store.refusals import storage_failure
from test_actor_workflow import accepted, catalog, final, wait_status
from test_request_runtime_daemon import (
    compose,
    connection,
    dispatch,
    mint,
    receipt,
    rpc,
    submit_params,
    value,
    ws_connect,
)
from test_request_runtime_tool_loop import ScriptedText


@pytest.fixture
def joined_host(tmp_path: Path) -> Iterator[tuple[DaemonProcess, ScriptedText]]:
    catalog(tmp_path)
    process = compose(tmp_path)
    try:
        mint(process)
        owner = value(ActorId.mint(DeskSlug.RESEARCH, "joined"))
        value(
            process.mailboxes.open_for_quant(
                Quant(owner, DeskSlug.RESEARCH, "joined", RoleName.RESEARCHER, "Joined")
            )
        )
        agent = value(
            process.agent_capabilities.spawn(
                SpawnRequest("agent:joined", owner, "session:joined", RoleBase("bounded-worker"))
            )
        )
        task = TaskRecord(
            "task:joined",
            "mission:joined",
            owner,
            "bounded request",
            state=TaskMissionState.READY,
            inputs={
                "agent_session_ref": agent.session_id,
                "request_product_session_ref": "psess:agent",
                "request_profile_id": "global",
            },
        )
        process.task_dispatcher.materialize(
            TaskGraph("graph:joined", task.mission_id, tasks=(task,))
        )
        value(process.task_dispatcher.dispatch_task(task_id=task.id, holder_agent_id=agent.id))
        value(
            process.jobs.submit(
                owner=owner, task_id=task.id, originating_product_session_ref="psess:agent"
            )
        )
        provider = ScriptedText([final("analysis"), final("review")])
        value(
            process.configure_agent_requests(
                providers={provider.capabilities.provider_id: provider},
                policies={
                    "global": AgentRequestPolicy(
                        CopilotProfile("global"), "authoring", provider.capabilities.provider_id
                    )
                },
                canonical_joins=(
                    CanonicalJoinPlan("operator", "global", "quant:research", owner, task.id),
                ),
            )
        )
        yield process, provider
    finally:
        process.close()


def test_host_admitted_request_has_canonical_owner_without_rewriting_behavior(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host
    conn = connection(process)
    request_id = accepted(process, conn)
    result = wait_status(process, conn, request_id, "completed")
    join = result["canonical_join"]
    assert join["canonical_owner"] == "quant:research/joined"
    assert join["behavioral_actor_id"] == "quant:research"
    assert join["execution_agent_id"] == "agent:joined"
    assert join["task_id"] == "task:joined"
    assert join["job_id"] == "job:task:joined"
    assert join["canonical_state"] == "running"
    assert join["certainty"] == "observed"
    assert len(provider.requests) == 2
    assert process.canonical_requests is not None
    value(process.canonical_requests.bind_task("global", "task:joined"))


def test_unqualified_toolset_alias_cannot_bypass_joined_permission_ceiling(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host
    assert process.agent_requests is not None
    runtime = process.agent_requests.runtime
    task = process.task_dispatcher.task_for("task:joined")
    assert task is not None
    agent = value(
        process.agent_capabilities.spawn(
            SpawnRequest(
                "agent:alias-toolset",
                task.owner,
                "session:joined",
                RoleBase("bounded-worker", toolset_ids=("legacy-aliases",)),
                base_toolset_tool_ids={"legacy-aliases": ("research_browse",)},
            )
        )
    )
    assert agent.effective_tool_ids == frozenset({"research_browse"})
    assert not agent.effective_permissions
    value(process.task_dispatcher.reassign(task_id=task.id, new_holder_agent_id=agent.id))
    policy = process.agent_requests.policies["global"]
    actor = runtime.providers[policy.provider_id]
    assert isinstance(actor, ActorWorkflowProvider)
    # A trusted route resolver can supply a tool-equipped route; the join must
    # enforce its own authority fence even for legacy toolset expansion.
    actor.routes = tuple(replace(route, tools=("research_browse",)) for route in actor.routes)
    admitted = runtime.submit(
        RequestSpec(
            "alias-ceiling",
            "operator",
            "psess:agent",
            0,
            policy.profile,
            "read metadata",
            policy.provider_id,
        )
    )
    assert is_refusal(admitted), admitted
    assert provider.requests == []


def test_second_request_cannot_claim_same_canonical_task_attempt(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host
    conn = connection(process)
    first = accepted(process, conn)
    wait_status(process, conn, first, "completed")
    refused = dispatch(
        process, conn, "submit_agent_request", submit_params(key="second", prompt="another job")
    )
    assert "error" in refused
    assert accepted(process, conn) == first
    assert len(provider.requests) == 2
    assert len(process.jobs.store.all()) == 1


def test_two_canonical_tasks_retain_behavioral_memory_and_fresh_child_threads(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host
    conn = connection(process)
    first = accepted(process, conn)
    wait_status(process, conn, first, "completed")
    task = process.task_dispatcher.task_for("task:joined")
    assert task is not None
    second = replace(
        task,
        id="task:second",
        mission_id="mission:second",
        state=TaskMissionState.READY,
        ledger=None,
    )
    process.task_dispatcher.materialize(
        TaskGraph("graph:second", second.mission_id, tasks=(second,))
    )
    value(process.task_dispatcher.dispatch_task(task_id=second.id, holder_agent_id="agent:joined"))
    value(
        process.jobs.submit(
            owner=second.owner, task_id=second.id, originating_product_session_ref="psess:agent"
        )
    )
    assert process.canonical_requests is not None
    value(process.canonical_requests.bind_task("global", second.id))
    provider.responses.extend([final("analysis-two"), final("review-two")])
    next_id = accepted(process, conn, key="second")
    result = wait_status(process, conn, next_id, "completed", timeout_seconds=30)
    assert result["canonical_join"]["task_id"] == "task:second"
    assert first != next_id
    assert "analysis" in provider.requests[2].prompt
    assert len({r.graph_thread_id for r in provider.requests}) == 4
    assert len(process.jobs.store.all()) == 2


def test_unknown_child_retains_canonical_lease_and_refuses_retry_before_and_after_resolution(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host

    def lose_second(count: int) -> None:
        if count == 2:
            raise ProviderError("outcome_unknown", "synthetic child owner loss")

    provider.after = lose_second
    conn = connection(process)
    request_id = accepted(process, conn)
    result = wait_status(process, conn, request_id, "interrupted")
    assert result["canonical_join"]["certainty"] == "unknown"
    handle = process.jobs.handle_for_task("task:joined")
    assert handle is not None and handle.state is JobHandleState.UNKNOWN
    assert process.task_dispatcher.dispatch_lease_for("task:joined") is not None
    assert process.agent_requests is not None
    assert is_refusal(process.agent_requests.runtime.retry_interrupted(request_id))
    value(
        process.jobs.resolve_unknown(
            handle.job_id, principal="operator", recorded=True, to_state="cancelled"
        )
    )
    assert is_refusal(process.agent_requests.runtime.retry_interrupted(request_id))
    assert len(provider.requests) == 2


def test_mapping_retirement_stops_new_model_dispatch_and_withholds_results(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host
    assert process.canonical_requests is not None
    join = process.canonical_requests
    provider.after = lambda _: value(join.retire("global"))
    conn = connection(process)
    request_id = accepted(process, conn)
    assert process.agent_requests is not None
    import time

    deadline = time.monotonic() + 20
    while value(process.agent_requests.runtime.get(request_id)).status in {
        "queued",
        "running",
        "cancellation_requested",
    }:
        assert time.monotonic() < deadline
        import threading

        threading.Event().wait(0.01)
    result = dispatch(
        process,
        conn,
        "get_agent_request",
        {"request_id": request_id, "product_session_ref": "psess:agent"},
    )
    assert receipt(result)["content_withheld"] is True
    assert "content" not in receipt(result) and "activities" not in receipt(result)
    assert len(provider.requests) == 1
    assert "error" in dispatch(process, conn, "submit_agent_request", submit_params(key="new"))


def test_joined_request_cannot_execute_after_restart_without_original_agent_authority(
    joined_host: tuple[DaemonProcess, ScriptedText], tmp_path: Path
) -> None:
    process, provider = joined_host
    provider.after = lambda _: (_ for _ in ()).throw(
        ProviderError("outcome_unknown", "synthetic owner loss")
    )
    conn = connection(process)
    request_id = accepted(process, conn)
    wait_status(process, conn, request_id, "interrupted")
    process.close()
    recovered = compose(tmp_path, boot="joined-restart")
    try:
        fresh_provider = ScriptedText([final("must not dispatch")])
        value(
            recovered.configure_agent_requests(
                providers={fresh_provider.capabilities.provider_id: fresh_provider},
                policies={
                    "global": AgentRequestPolicy(
                        CopilotProfile("global"),
                        "authoring",
                        fresh_provider.capabilities.provider_id,
                    )
                },
            )
        )
        assert recovered.agent_requests is not None
        assert is_refusal(recovered.agent_requests.runtime.retry_interrupted(request_id))
        handle = recovered.jobs.handle_for_task("task:joined")
        assert handle is not None and handle.state is JobHandleState.UNKNOWN
        # The dispatcher and frozen spawn registry are volatile; the durable
        # graph retains uncertainty and must not reconstruct caller authority.
        durable = recovered.task_dispatcher.store.durable
        assert durable is not None
        graph = durable.graph_for_task("task:joined")
        assert graph is not None
        task = graph.task_by_id("task:joined")
        assert task is not None and task.state is TaskMissionState.UNKNOWN
        assert recovered.task_dispatcher.dispatch_lease_for("task:joined") is None
        assert fresh_provider.requests == []
    finally:
        recovered.close()


def test_behavioral_mapping_cannot_move_to_another_existing_quant(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host
    assert process.agent_requests is not None
    owner = value(ActorId.mint(DeskSlug.RESEARCH, "other"))
    value(
        process.mailboxes.open_for_quant(
            Quant(owner, DeskSlug.RESEARCH, "other", RoleName.RESEARCHER, "Other"),
        )
    )
    with pytest.raises(ValueError, match="mapping admission refused"):
        CanonicalRequestJoin(
            runtime=process.agent_requests.runtime,
            plans=(
                CanonicalJoinPlan("operator", "global", "quant:research", owner, "task:joined", 2),
            ),
            dispatcher=process.task_dispatcher,
            agents=process.agent_capabilities,
            mailboxes=process.mailboxes,
            jobs=process.jobs,
        )
    assert not provider.requests
    conn = connection(process)
    request_id = accepted(process, conn)
    result = wait_status(process, conn, request_id, "completed", timeout_seconds=30)
    assert result["canonical_join"]["canonical_owner"] == "quant:research/joined"


def test_clean_restart_preserves_completed_request_and_uncertain_canonical_owner(
    joined_host: tuple[DaemonProcess, ScriptedText],
    tmp_path: Path,
) -> None:
    process, provider = joined_host
    conn = connection(process)
    request_id = accepted(process, conn)
    wait_status(process, conn, request_id, "completed", timeout_seconds=30)
    process.close()
    recovered = compose(tmp_path, boot="completed-join-restart")
    try:
        handle = recovered.jobs.handle_for_task("task:joined")
        assert handle is not None and handle.state is JobHandleState.UNKNOWN
        assert is_refusal(recovered.jobs.cancel(handle.job_id))
        assert len(provider.requests) == 2
    finally:
        recovered.close()


def test_unknown_observation_write_failure_never_readmits_joined_request(
    joined_host: tuple[DaemonProcess, ScriptedText],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process, provider = joined_host
    assert process.canonical_requests is not None and process.agent_requests is not None
    join, runtime = process.canonical_requests, process.agent_requests.runtime
    save = join._save  # pyright: ignore[reportPrivateUsage] - write boundary fault fixture

    def lose_observation(kind: str, body: dict[str, Any]) -> Result[None]:
        return (
            storage_failure("offline observation write loss")
            if kind == "observed"
            else save(kind, body)
        )

    monkeypatch.setattr(join, "_save", lose_observation)
    provider.after = lambda _: (_ for _ in ()).throw(
        ProviderError("outcome_unknown", "offline lost child"),
    )
    conn = connection(process)
    request_id = accepted(process, conn)
    wait_status(process, conn, request_id, "interrupted", timeout_seconds=30)
    handle = process.jobs.handle_for_task("task:joined")
    assert handle is not None and handle.state is JobHandleState.UNKNOWN
    assert is_refusal(runtime.retry_interrupted(request_id))
    assert len(provider.requests) == 1


def test_retired_mapping_still_allows_owned_bounded_stop(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host
    assert process.canonical_requests is not None and process.agent_requests is not None
    started, released = threading.Event(), threading.Event()

    def block(count: int) -> None:
        if count == 1:
            started.set()
            assert released.wait(20)

    provider.after = block
    request_id = accepted(process, connection(process))
    assert started.wait(10)
    try:
        value(process.canonical_requests.retire("global"))
        assert (
            value(process.agent_requests.runtime.cancel(request_id)).status
            == "cancellation_requested"
        )
        assert process.task_dispatcher.dispatch_lease_for("task:joined") is not None
    finally:
        released.set()


def test_paired_socket_cancel_observes_child_stop_before_releasing_canonical_lease(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host
    started, released = threading.Event(), threading.Event()

    def block_first(count: int) -> None:
        if count == 1:
            started.set()
            assert released.wait(20), "offline child fixture was not released"

    provider.after = block_first

    async def run() -> None:
        value(await process.bind())
        reader, writer, opening = await ws_connect(process)
        try:
            assert b"101 Switching Protocols" in opening
            assert "result" in await rpc(
                reader,
                writer,
                "initialize",
                {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
            )
            response = await rpc(reader, writer, "submit_agent_request", submit_params())
            request_id = cast("str", receipt(response)["request_id"])
            assert await asyncio.to_thread(started.wait, 10)
            handle = process.jobs.handle_for_task("task:joined")
            assert handle is not None
            assert is_refusal(process.jobs.cancel(handle.job_id))
            intent = await rpc(
                reader,
                writer,
                "cancel_agent_request",
                {"request_id": request_id, "product_session_ref": "psess:agent"},
            )
            assert receipt(intent)["status"] == "cancellation_requested"
            assert is_refusal(process.jobs.cancel(handle.job_id))
            assert process.task_dispatcher.dispatch_lease_for("task:joined") is not None
            released.set()
            deadline = time.monotonic() + 30
            while True:
                response = await rpc(
                    reader,
                    writer,
                    "get_agent_request",
                    {"request_id": request_id, "product_session_ref": "psess:agent"},
                )
                if receipt(response)["status"] == "cancelled":
                    break
                assert time.monotonic() < deadline
                await asyncio.sleep(0.01)
            cancelled = value(process.jobs.cancel(handle.job_id))
            assert cancelled.state is JobHandleState.CANCELLED
            assert process.task_dispatcher.dispatch_lease_for("task:joined") is None
            assert value(process.jobs.cancel(handle.job_id)).state is JobHandleState.CANCELLED
            assert len(provider.requests) == 1
            old_task = process.task_dispatcher.task_for("task:joined")
            assert old_task is not None
            fresh_task = replace(
                old_task,
                id="task:socket-second",
                mission_id="mission:socket-second",
                state=TaskMissionState.READY,
                ledger=None,
            )
            process.task_dispatcher.materialize(
                TaskGraph(
                    "graph:socket-second",
                    fresh_task.mission_id,
                    tasks=(fresh_task,),
                )
            )
            value(
                process.task_dispatcher.dispatch_task(
                    task_id=fresh_task.id,
                    holder_agent_id="agent:joined",
                )
            )
            value(
                process.jobs.submit(
                    owner=fresh_task.owner,
                    task_id=fresh_task.id,
                    originating_product_session_ref="psess:agent",
                )
            )
            assert process.canonical_requests is not None
            value(process.canonical_requests.bind_task("global", fresh_task.id))
            provider.responses.extend([final("fresh analysis"), final("fresh review")])
            response = await rpc(
                reader,
                writer,
                "submit_agent_request",
                submit_params(key="socket-second"),
            )
            second_id = cast("str", receipt(response)["request_id"])
            deadline = time.monotonic() + 30
            while True:
                response = await rpc(
                    reader,
                    writer,
                    "get_agent_request",
                    {"request_id": second_id, "product_session_ref": "psess:agent"},
                )
                if receipt(response)["status"] == "completed":
                    break
                assert time.monotonic() < deadline
                await asyncio.sleep(0.01)
            assert len(process.jobs.store.all()) == 2
            assert len({r.graph_thread_id for r in provider.requests}) == 3
            assert second_id != request_id
        finally:
            released.set()
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    asyncio.run(run())


def test_pending_effect_is_not_reclassified_by_known_provider_failure(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host
    assert process.agent_requests is not None

    def pending_effect(count: int) -> None:
        if count == 1:
            request_id = provider.requests[-1].request_id
            JournalRecords(process.journal).put(
                "effect",
                request_id + ":synthetic-egress",
                {"status": "pending", "input_hash": "offline", "tool": "egress"},
            )
            raise ProviderError("tool_denied", "offline failure after intent")

    provider.after = pending_effect
    conn = connection(process)
    request_id = accepted(process, conn)
    result = wait_status(process, conn, request_id, "failed", timeout_seconds=30)
    assert result["canonical_join"]["certainty"] == "unknown"
    handle = process.jobs.handle_for_task("task:joined")
    assert handle is not None and handle.state is JobHandleState.UNKNOWN
    assert process.task_dispatcher.dispatch_lease_for("task:joined") is not None
    assert is_refusal(process.jobs.cancel(handle.job_id))


def test_reassignment_cannot_admit_replacement_before_prior_owner_reconciles(
    joined_host: tuple[DaemonProcess, ScriptedText],
) -> None:
    process, provider = joined_host
    started, released = threading.Event(), threading.Event()

    def hold(count: int) -> None:
        if count == 1:
            started.set()
            assert released.wait(20)

    provider.after = hold
    conn = connection(process)
    request_id = accepted(process, conn)
    assert started.wait(10)
    try:
        task = process.task_dispatcher.task_for("task:joined")
        assert task is not None
        value(
            process.agent_capabilities.spawn(
                SpawnRequest(
                    "agent:replacement",
                    task.owner,
                    "session:joined",
                    RoleBase("bounded-worker"),
                )
            )
        )
        value(
            process.task_dispatcher.reassign(
                task_id="task:joined",
                new_holder_agent_id="agent:replacement",
            )
        )
        ledger = process.task_dispatcher.ledgers.get("task:joined")
        assert ledger is not None and ledger.attempt_no == 1
        assert "error" in dispatch(
            process,
            conn,
            "submit_agent_request",
            submit_params(key="replacement"),
        )
    finally:
        released.set()
    wait_status(process, conn, request_id, "failed", timeout_seconds=30)
    handle = process.jobs.handle_for_task("task:joined")
    assert handle is not None and handle.state is JobHandleState.UNKNOWN
    assert process.task_dispatcher.dispatch_lease_for("task:joined") is not None
    assert len(provider.requests) == 1


@pytest.mark.parametrize("corrupt_observation", [False, True])
def test_final_snapshot_loss_recovers_owned_observation_without_repeat_inference(
    joined_host: tuple[DaemonProcess, ScriptedText],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    corrupt_observation: bool,
) -> None:
    process, provider = joined_host
    assert process.agent_requests is not None
    runtime = process.agent_requests.runtime
    persist = runtime._persist  # pyright: ignore[reportPrivateUsage] - crash boundary fixture

    def lose_final(row: RequestRecord) -> Result[RequestRecord]:
        return (
            storage_failure("offline lost final snapshot")
            if row.status == "completed"
            else persist(row)
        )

    monkeypatch.setattr(runtime, "_persist", lose_final)
    conn = connection(process)
    request_id = accepted(process, conn)
    deadline = time.monotonic() + 30
    while True:
        handle = process.jobs.handle_for_task("task:joined")
        if handle is not None and handle.state is JobHandleState.UNKNOWN:
            break
        assert time.monotonic() < deadline
        threading.Event().wait(0.01)
    assert len(provider.requests) == 2
    mint(process, "psess:foreign")
    assert "error" in dispatch(
        process,
        conn,
        "get_agent_request",
        {"request_id": request_id, "product_session_ref": "psess:foreign"},
    )
    if corrupt_observation:
        value(
            process.journal.append_event(
                "canonical_request.observed",
                payload={
                    "request_id": request_id,
                    "request_attempt": 1,
                    "request_status": "interrupted",
                    "result_sha256": "0" * 64,
                    "result_json": json.dumps({"content": "incorrect bytes"}),
                },
            )
        )
    process.close()
    recovered = compose(tmp_path, boot="lost-result-restart")
    try:
        fresh = ScriptedText([final("must not run")])
        configured = recovered.configure_agent_requests(
            providers={fresh.capabilities.provider_id: fresh},
            policies={
                "global": AgentRequestPolicy(
                    CopilotProfile("global"),
                    "authoring",
                    fresh.capabilities.provider_id,
                )
            },
        )
        if corrupt_observation:
            assert is_refusal(configured)
            assert not fresh.requests
            return
        value(configured)
        assert recovered.agent_requests is not None
        restored = value(recovered.agent_requests.runtime.get(request_id))
        assert restored.status == "interrupted" and restored.result is not None
        assert "review" in restored.result.content
        assert is_refusal(recovered.agent_requests.runtime.retry_interrupted(request_id))
        response = dispatch(
            recovered,
            connection(recovered),
            "get_agent_request",
            {"request_id": request_id, "product_session_ref": "psess:agent"},
        )
        assert receipt(response)["content_withheld"] is True
        assert "content" not in receipt(response)
        assert not fresh.requests
    finally:
        recovered.close()
