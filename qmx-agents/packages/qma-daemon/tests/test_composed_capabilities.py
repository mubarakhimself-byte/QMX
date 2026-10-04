"""Composed authority journeys: real paired sockets, synthetic inference and CT43."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, cast

import pytest
import test_canonical_joined_tools as joined_tools
from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.vocabulary.enums import JobHandleState, TaskMissionState
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.canonical_join import CanonicalJoinPlan
from qma.daemon.request_runtime.contracts import CopilotProfile
from qma.daemon.request_runtime.daemon_bridge import AgentRequestPolicy
from qma.daemon.request_runtime.graph_storage import JournalRecords
from qma.daemon.request_runtime.providers import ProviderCancelled, ProviderError
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from qmf.core import is_refusal
from test_actor_workflow import final, setup
from test_canonical_request_join import joined_host
from test_deep_agent_actor import select
from test_memory_provider_seam import FakeMemory, install_fake, retained, selection
from test_request_runtime_daemon import (
    compose,
    mint,
    receipt,
    rpc,
    submit_params,
    value,
    ws_connect,
)
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
def test_selected_harness_joined_callback_and_memory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    # Reuse the full socket/effect/Task assertions with all three capabilities active.
    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)
    select(monkeypatch, "app-reader")
    joined_tools.test_joined_paired_read_respects_agent_and_current_grant(
        tmp_path, monkeypatch, mode
    )
    if mode in {
        "allowed",
        "restart_completed",
        "dispatch_decoy_callback",
        "dispatch_decoy_operation",
    }:
        assert len(fake.calls) == 2
        assert all(scope.startswith("actor-memory:") for scope, _ in fake.calls)
    elif mode in {
        "narrow",
        "revoked_after_model",
        "became_unavailable",
        "regrant",
        "changed_alias",
    }:
        assert len(fake.calls) == 1


async def open_pair(process: DaemonProcess) -> tuple[Any, Any]:
    value(await process.bind())
    reader, writer, opening = await ws_connect(process)
    assert b"101 Switching Protocols" in opening
    receipt(
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
    return reader, writer


async def poll(reader: Any, writer: Any, request_id: str, statuses: set[str]) -> dict[str, Any]:
    deadline = time.monotonic() + 30
    while True:
        row = receipt(
            await rpc(
                reader,
                writer,
                "get_agent_request",
                {
                    "request_id": request_id,
                    "product_session_ref": "psess:agent",
                },
            )
        )
        if row["status"] in statuses:
            return row
        assert time.monotonic() < deadline, row
        await asyncio.sleep(0.01)


def test_selected_harness_provider_continuity_through_paired_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripted = setup(
        tmp_path,
        monkeypatch,
        [
            final("first-analysis"),
            final("first-review"),
            final("second-analysis"),
            final("second-review"),
        ],
    )
    select(monkeypatch, "global")
    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)

    async def journey(first: bool) -> None:
        process = compose(tmp_path, boot="composed-first" if first else "composed-restart")
        writer = None
        try:
            if first:
                mint(process)
            reader, writer = await open_pair(process)
            accepted = receipt(
                await rpc(
                    reader,
                    writer,
                    "submit_agent_request",
                    submit_params(key="first" if first else "second"),
                )
            )
            request_id = str(accepted["request_id"])
            row = await poll(reader, writer, request_id, {"completed", "failed", "interrupted"})
            assert row["status"] == "completed", row
            assert process.agent_requests is not None
            record = value(process.agent_requests.runtime.get(request_id))
            assert record.spec.memory_binding_sha256
            pin = JournalRecords(process.journal).get(
                "agent_binding", request_id + ":child:analysis:thread"
            )
            assert pin is not None and pin["harness"]["revision"] == "qmx:bounded-specialist-v1"
            reviewer = JournalRecords(process.journal).get(
                "agent_binding", request_id + ":child:review:thread"
            )
            assert reviewer is not None and "harness" not in reviewer
            fake.candidates = retained(process)
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
            await process.aclose()

    asyncio.run(journey(True))
    asyncio.run(journey(False))
    assert len(fake.calls) == 4 and fake.calls[:2] == fake.calls[2:]
    assert len(scripted.requests) == 4
    for request in scripted.requests[2:]:
        prompt = json.loads(json.loads(request.prompt)["user_request"])
        assert "first-" in prompt["actor_memory"]


def test_selected_harness_named_child_cancel_through_paired_socket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripted = setup(tmp_path, monkeypatch, [final("must not finish"), final("must not start")])
    select(monkeypatch, "global")
    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)
    started, release = threading.Event(), threading.Event()

    def blocked(request: Any, emit: Any, cancellation: threading.Event) -> Any:
        started.set()
        assert release.wait(15)
        assert cancellation.is_set()
        raise ProviderCancelled()

    monkeypatch.setattr(scripted, "execute", blocked)

    async def journey() -> None:
        process = compose(tmp_path, boot="composed-child-cancel")
        writer = None
        try:
            mint(process)
            reader, writer = await open_pair(process)
            accepted = receipt(await rpc(reader, writer, "submit_agent_request", submit_params()))
            request_id = str(accepted["request_id"])
            assert await asyncio.to_thread(started.wait, 10)
            active = await poll(reader, writer, request_id, {"running"})
            assert [a["status"] for a in active["activities"]] == ["running", "queued"]
            foreign = await rpc(
                reader,
                writer,
                "cancel_agent_request",
                {
                    "request_id": request_id,
                    "product_session_ref": "psess:agent",
                    "activity_id": "req:foreign:child:analysis",
                },
            )
            assert "error" in foreign
            cancel = receipt(
                await rpc(
                    reader,
                    writer,
                    "cancel_agent_request",
                    {
                        "request_id": request_id,
                        "product_session_ref": "psess:agent",
                        "activity_id": active["activities"][0]["activity_id"],
                    },
                )
            )
            assert cancel["status"] == "cancellation_requested"
            release.set()
            row = await poll(reader, writer, request_id, {"cancelled"})
            assert [a["status"] for a in row["activities"]] == ["cancelled", "cancelled"]
            assert all("result" not in a for a in row["activities"])
            assert len(fake.calls) == 1 and scripted.requests == []
        finally:
            release.set()
            if writer is not None:
                writer.close()
                await writer.wait_closed()
            await process.aclose()

    asyncio.run(journey())


@pytest.mark.parametrize("loss", ["cancelled", "denied"])
def test_unobserved_memory_recall_keeps_joined_canonical_outcome_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, loss: str
) -> None:
    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)
    select(monkeypatch, "global")

    def lose() -> None:
        if loss == "cancelled":
            raise ProviderCancelled()
        raise ProviderError("memory_denied", "fixture recall lost after intent")

    fake.after = lose
    fixture = cast(
        "Callable[[Path], Generator[tuple[DaemonProcess, ScriptedText]]]",
        cast("Any", joined_host).__wrapped__,
    )(tmp_path)
    process, scripted = next(fixture)
    request_id = ""

    async def journey() -> None:
        nonlocal request_id
        reader, writer = await open_pair(process)
        try:
            accepted = receipt(await rpc(reader, writer, "submit_agent_request", submit_params()))
            request_id = str(accepted["request_id"])
            row = await poll(reader, writer, request_id, {"cancelled", "failed", "interrupted"})
            assert row["status"] == ("cancelled" if loss == "cancelled" else "failed")
            assert process.agent_requests is not None and process.canonical_requests is not None
            record = value(process.agent_requests.runtime.get(request_id))
            assert record.spec.memory_binding_sha256
            handle = process.jobs.handle_for_task("task:joined")
            assert handle is not None
            # A memory recall intent is an unobserved host effect just like a tool intent.
            assert handle.state is JobHandleState.UNKNOWN
            task = process.task_dispatcher.task_for("task:joined")
            assert task is not None and task.state is TaskMissionState.UNKNOWN
            assert process.task_dispatcher.dispatch_lease_for(task.id) is not None
            assert is_refusal(process.canonical_requests.allow_canonical_cancel(handle))
            assert is_refusal(process.agent_requests.runtime.retry_interrupted(request_id))
            assert len(fake.calls) == 1 and scripted.requests == []
        finally:
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    try:
        asyncio.run(journey())
    finally:
        fixture.close()
    recovered = compose(tmp_path, boot="memory-uncertain-reopen")
    try:
        owner = ActorId("quant:research/joined")
        value(
            recovered.mailboxes.open_for_quant(
                Quant(owner, DeskSlug.RESEARCH, "joined", RoleName.RESEARCHER, "Joined")
            )
        )
        fresh = ScriptedText([final("must not replay")])
        value(
            recovered.configure_agent_requests(
                providers={fresh.capabilities.provider_id: fresh},
                policies={
                    "global": AgentRequestPolicy(
                        CopilotProfile("global"), "authoring", fresh.capabilities.provider_id
                    )
                },
                canonical_joins=(
                    CanonicalJoinPlan("operator", "global", "quant:research", owner, "task:joined"),
                ),
            )
        )
        assert recovered.agent_requests is not None and recovered.canonical_requests is not None
        handle = recovered.jobs.handle_for_task("task:joined")
        assert handle is not None and handle.state is JobHandleState.UNKNOWN
        assert is_refusal(recovered.canonical_requests.allow_canonical_cancel(handle))
        assert is_refusal(recovered.agent_requests.runtime.retry_interrupted(request_id))

        async def refused_replay() -> None:
            reader, writer = await open_pair(recovered)
            try:
                resumed = await rpc(
                    reader,
                    writer,
                    "resume_agent_request",
                    {
                        "request_id": request_id,
                        "product_session_ref": "psess:agent",
                    },
                )
                assert "error" in resumed, resumed
                fresh_submission = await rpc(
                    reader, writer, "submit_agent_request", submit_params(key="fresh-replay")
                )
                assert "error" in fresh_submission, fresh_submission
                duplicate = receipt(
                    await rpc(reader, writer, "submit_agent_request", submit_params())
                )
                assert duplicate["request_id"] == request_id
                assert len(fake.calls) == 1 and fresh.requests == []
            finally:
                writer.close()
                await writer.wait_closed()
                await recovered.aclose()

        asyncio.run(refused_replay())
        assert len(fake.calls) == 1 and fresh.requests == []
    finally:
        recovered.close()
