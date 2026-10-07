"""Actual daemon request journeys, injected providers, no external calls."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from qma.daemon.knowledge.service import KnowledgeService
from qma.daemon.request_runtime.actor_profiles import load_actor_catalog
from qma.daemon.request_runtime.graph_storage import JournalCheckpointer, JournalRecords
from qma.daemon.request_runtime.providers import ProviderCancelled, ProviderError
from qma.wire.agent_request import AgentRequestReference, parse_cancel_agent_request
from qma.wire.initialize import WIRE_PROTOCOL_VERSION, WireConnection
from qmf.core import is_refusal
from test_agent_extensions import BODY, READ
from test_agent_extensions_daemon import configure_file, offline, write
from test_request_runtime_configured_daemon import (
    app_session,
    compose_configured,
    discover,
    sdk_config,
)
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
from test_request_runtime_tool_loop import host as host_fixture

host = host_fixture

# Deep Agents builds its graph on the first turn; allow loaded parallel workers.
ACTOR_COMPLETION_TIMEOUT_SECONDS = 60


def test_named_child_wire_roundtrip() -> None:
    reference = AgentRequestReference("req:one", "psess:agent", "req:one:child:analysis")
    assert value(parse_cancel_agent_request(reference.to_payload())) == reference
    assert is_refusal(parse_cancel_agent_request(reference.to_payload() | {"grant": "new"}))


def test_legacy_child_thread_keeps_original_effect_namespace(
    host: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime, loop, _provider, calls, _sessions, submit, _ = host
    original = loop.execute

    def child(request: Any, emit: Any, cancellation: Any) -> Any:
        return original(
            replace(request, graph_thread_id=request.request_id + ":legacy-child"),
            emit,
            cancellation,
        )

    monkeypatch.setattr(loop, "execute", child)
    request_id = submit()
    original_writes = JournalCheckpointer.put_writes
    lost = False

    def lose_tool_checkpoint(self: Any, *args: Any, **kwargs: Any) -> None:
        nonlocal lost
        effect = JournalRecords(runtime.journal).get("effect", request_id + ":graph:call-1")
        if not lost and effect is not None and effect["status"] == "observed":
            lost = True
            raise ProviderError("outcome_unknown", "fixture loss after effect, before graph write")
        original_writes(self, *args, **kwargs)

    monkeypatch.setattr(JournalCheckpointer, "put_writes", lose_tool_checkpoint)
    interrupted = value(runtime.execute(request_id))
    assert interrupted.status == "interrupted" and lost and len(calls) == 1
    value(runtime.retry_interrupted(request_id))
    row = value(runtime.execute(request_id))
    assert row.status == "completed" and len(calls) == 1
    effect = JournalRecords(runtime.journal).get("effect", request_id + ":graph:call-1")
    assert effect is not None and effect["status"] == "observed"
    pin = JournalRecords(runtime.journal).get("agent_binding", request_id + ":legacy-child")
    assert pin is not None and "effect_namespace" not in pin


def catalog(root: Path) -> dict[str, Any]:
    body: dict[str, Any] = {
        "limits": {"max_children": 2, "max_depth": 1, "max_model_calls": 4},
        "roles": [
            {
                "id": "analyst",
                "version": "1",
                "instructions": "ANALYST_SENTINEL: analyze the supplied request",
                "tools": [],
                "max_model_calls": 2,
                "max_tool_calls": 1,
            },
            {
                "id": "reviewer",
                "version": "1",
                "instructions": "REVIEWER_SENTINEL: critically review the analysis",
                "tools": [],
                "max_model_calls": 2,
                "max_tool_calls": 1,
            },
        ],
        "workflows": [
            {
                "id": "assessment",
                "version": "1",
                "steps": [
                    {"id": "normalize", "kind": "normalize"},
                    {"id": "analysis", "kind": "agent", "role": "analyst:1"},
                    {"id": "review", "kind": "agent", "role": "reviewer:1"},
                    {"id": "collect", "kind": "collect"},
                ],
            }
        ],
        "routes": [
            {
                "profile_id": "global",
                "actor_id": "quant:research",
                "workflow": "assessment:1",
                "tools": [],
            }
        ],
    }
    save_catalog(root, body)
    return body


def save_catalog(root: Path, body: dict[str, Any]) -> None:
    (root / "actor-workflows.json").write_text(json.dumps(body), encoding="utf-8")


def setup(root: Path, monkeypatch: pytest.MonkeyPatch, responses: list[str]) -> ScriptedText:
    sdk = configure_file(root)
    sdk["agent_extensions"]["profiles"]["global"]["workflows"] = ["analyst:1"]
    write(root, sdk)
    catalog(root)
    scripted = ScriptedText(responses)
    offline(monkeypatch, scripted)
    return scripted


def final(text: str) -> str:
    return json.dumps({"type": "final", "content": text})


def accepted(process: Any, conn: Any, key: str = "one") -> str:
    return str(
        receipt(
            dispatch(
                process,
                conn,
                "submit_agent_request",
                submit_params(key=key, prompt="  assess   hypothesis  "),
            )
        )["request_id"]
    )


def children(process: Any, conn: Any, request_id: str) -> list[dict[str, Any]]:
    return cast(
        "list[dict[str, Any]]",
        receipt(
            dispatch(
                process,
                conn,
                "get_agent_request",
                {"request_id": request_id, "product_session_ref": "psess:agent"},
            )
        )["activities"],
    )


def wait_finished(
    process: Any, request_id: str, timeout_seconds: float = ACTOR_COMPLETION_TIMEOUT_SECONDS
) -> None:
    # Status reads replay the journal and compete with the worker's writes.
    # Wait on its completion condition, then assert the result through the real door.
    bridge = process.agent_requests
    assert bridge is not None
    with bridge._condition:
        assert bridge._condition.wait_for(
            lambda: request_id not in bridge._jobs, timeout=timeout_seconds
        ), f"request {request_id} did not finish"


def wait_status(
    process: Any,
    conn: Any,
    request_id: str,
    status: str,
    *,
    timeout_seconds: float = ACTOR_COMPLETION_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    wait_finished(process, request_id, timeout_seconds)
    row = receipt(
        dispatch(
            process,
            conn,
            "get_agent_request",
            {"request_id": request_id, "product_session_ref": "psess:agent"},
        )
    )
    assert row["status"] == status, row
    return row


def test_two_specialists_two_jobs_actor_memory_and_thread_isolation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripted = setup(
        tmp_path,
        monkeypatch,
        [
            READ,
            final("analysis-one"),
            final("review-one"),
            final("analysis-two"),
            final("review-two"),
        ],
    )
    process = compose(tmp_path)
    try:
        mint(process)
        assert "error" in dispatch(
            process, WireConnection(), "submit_agent_request", submit_params()
        )
        conn = connection(process)
        first = accepted(process, conn)
        first_result = wait_status(process, conn, first, "completed")
        second = accepted(process, conn, "two")
        second_result = wait_status(process, conn, second, "completed")
        assert (
            json.loads(first_result["content"])["actor_id"]
            == json.loads(second_result["content"])["actor_id"]
            == "quant:research"
        )
        assert json.loads(first_result["content"])["outputs"] == {
            "analysis": "analysis-one",
            "review": "review-one",
        }
        assert len(scripted.requests) == 5
        assert BODY in scripted.requests[1].prompt
        assert "ANALYST_SENTINEL" in scripted.requests[0].instructions
        assert "REVIEWER_SENTINEL" in scripted.requests[2].instructions
        assert "read_file" not in scripted.requests[2].instructions
        assert "analysis-one" in scripted.requests[2].prompt
        assert "analysis-one" in scripted.requests[3].prompt  # durable typed actor memory
        assert len({r.graph_thread_id for r in scripted.requests}) == 4
        rows = children(process, conn, first)
        assert [r["status"] for r in rows] == ["completed", "completed"]
        assert all(
            r["actor_id"] == "quant:research" and r["execution_agent"] != r["actor_id"]
            for r in rows
        )
        assert rows[0]["result"] == "analysis-one"
        replay = accepted(process, conn)
        assert replay == first and len(scripted.requests) == 5
    finally:
        process.close()


def test_disk_restart_explicit_resume_does_not_repeat_completed_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripted = setup(
        tmp_path,
        monkeypatch,
        [final("retained analysis"), final("resumed review")],
    )
    scripted.after = lambda count: (
        (_ for _ in ()).throw(ProviderError("outcome_unknown", "lost fixture turn"))
        if count == 2
        else None
    )
    first = compose(tmp_path, boot="actor-one")
    try:
        mint(first)
        conn = connection(first)
        request_id = accepted(first, conn)
        wait_status(first, conn, request_id, "interrupted")
        assert [c["status"] for c in children(first, conn, request_id)] == [
            "completed",
            "interrupted",
        ]
    finally:
        first.close()
    scripted.after = None
    second = compose(tmp_path, boot="actor-two")
    try:
        conn = connection(second)
        receipt(
            dispatch(
                second,
                conn,
                "resume_agent_request",
                {"request_id": request_id, "product_session_ref": "psess:agent"},
            )
        )
        result = wait_status(second, conn, request_id, "completed")
        assert json.loads(result["content"])["outputs"]["analysis"] == "retained analysis"
        assert len(scripted.requests) == 3
        assert "REVIEWER_SENTINEL" in scripted.requests[-1].instructions
        assert JournalRecords(second.journal).get("quant", "quant:research") == {
            "actor_id": "quant:research",
            "principal": "operator",
        }
        scripted.responses.extend([final("fresh analysis"), final("fresh review")])
        fresh_id = accepted(second, conn, "fresh-after-restart")
        fresh = wait_status(second, conn, fresh_id, "completed")
        assert json.loads(fresh["content"])["actor_id"] == "quant:research"
        assert "retained analysis" in scripted.requests[3].prompt
        assert len(scripted.requests) == 5
        assert scripted.requests[3].graph_thread_id != scripted.requests[0].graph_thread_id
    finally:
        second.close()


@pytest.mark.parametrize("mutation", ["child_tools", "depth", "children", "models"])
def test_child_cannot_widen_host_ceiling_or_budget(tmp_path: Path, mutation: str) -> None:
    body = catalog(tmp_path)
    if mutation == "child_tools":
        body["roles"][0]["tools"] = ["research_browse"]
    elif mutation == "depth":
        body["limits"]["max_depth"] = 2
    elif mutation == "children":
        body["limits"]["max_children"] = 1
    else:
        body["limits"]["max_model_calls"] = 1
    save_catalog(tmp_path, body)
    with pytest.raises(ValueError):
        load_actor_catalog(tmp_path)


def test_same_version_mutation_refuses_restart_before_provider_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripted = setup(tmp_path, monkeypatch, [final("a"), final("b")])
    process = compose(tmp_path)
    process.close()
    body = json.loads((tmp_path / "actor-workflows.json").read_text())
    body["roles"][0]["instructions"] = "mutated same version"
    save_catalog(tmp_path, body)
    with pytest.raises(AssertionError):
        compose(tmp_path, boot="changed")
    assert scripted.requests == []


def test_named_child_cancel_stops_dependent_work_and_never_fakes_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripted = setup(tmp_path, monkeypatch, [final("a"), final("b")])
    started, release = threading.Event(), threading.Event()
    original = scripted.execute

    def blocked(request: Any, emit: Any, cancellation: threading.Event) -> Any:
        started.set()
        assert release.wait(3)
        if cancellation.is_set():
            raise ProviderCancelled()
        return original(request, emit, cancellation)

    monkeypatch.setattr(scripted, "execute", blocked)
    process = compose(tmp_path)
    try:
        mint(process)
        conn = connection(process)
        request_id = accepted(process, conn)
        assert started.wait(3)
        active = children(process, conn, request_id)
        assert [r["status"] for r in active] == ["running", "queued"]
        assert "error" in dispatch(
            process,
            conn,
            "cancel_agent_request",
            {
                "request_id": request_id,
                "product_session_ref": "psess:agent",
                "activity_id": "req:foreign:child:x",
            },
        )
        row = receipt(
            dispatch(
                process,
                conn,
                "cancel_agent_request",
                {
                    "request_id": request_id,
                    "product_session_ref": "psess:agent",
                    "activity_id": active[0]["activity_id"],
                },
            )
        )
        assert row["status"] == "cancellation_requested"
        release.set()
        wait_status(process, conn, request_id, "cancelled")
        assert [r["status"] for r in children(process, conn, request_id)] == [
            "cancelled",
            "cancelled",
        ]
        assert scripted.requests == []
    finally:
        release.set()
        process.close()


def app_setup(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], str, str, str, ScriptedText]:
    instance, contribution, snapshot = discover(root)
    sdk = sdk_config("http://127.0.0.1:9876/v1/chat/completions", instance, snapshot)
    body = catalog(root)
    body["routes"][0].update(profile_id="app-reader", tools=["research_browse"])
    for role in body["roles"]:
        role["tools"] = ["research_browse"]
    body["workflows"][0]["steps"].insert(
        1,
        {
            "id": "metadata",
            "kind": "read",
            "tool": "research_browse",
            "arguments": {"snapshot_ref": snapshot},
        },
    )
    save_catalog(root, body)
    tool = json.dumps(
        {
            "type": "tool",
            "tool": "research_browse",
            "arguments": {"snapshot_ref": snapshot, "locator": "README.md"},
        }
    )
    scripted = ScriptedText([tool, final("analysis"), tool, final("review")])
    offline(monkeypatch, scripted)
    return sdk, instance, contribution, snapshot, scripted


def app_wait(process: Any, request_id: str, status: str) -> Any:
    deadline = time.monotonic() + 10
    runtime = process.agent_requests.runtime
    while True:
        row = value(runtime.get(request_id))
        if row.status == status:
            return row
        if (
            row.status in {"failed", "cancelled", "completed", "interrupted"}
            or time.monotonic() >= deadline
        ):
            pytest.fail(repr(row))
        threading.Event().wait(0.01)


def test_actual_paired_socket_two_child_tool_effects_are_distinct_and_restart_does_not_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sdk, instance, contribution, _snapshot, scripted = app_setup(tmp_path, monkeypatch)
    reads: list[str] = []
    original = KnowledgeService.supersedes_chain

    def observe(self: KnowledgeService, source_id: str) -> Any:
        reads.append(source_id)
        return original(self, source_id)

    monkeypatch.setattr(KnowledgeService, "supersedes_chain", observe)
    scripted.after = lambda count: (
        (_ for _ in ()).throw(ProviderError("outcome_unknown", "lost final review"))
        if count == 4
        else None
    )
    process = compose_configured(tmp_path, sdk, "tools-one")
    request_id = ""

    async def journey() -> None:
        nonlocal request_id
        app_session(process, instance, contribution)
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
            started = receipt(
                await rpc(
                    reader,
                    writer,
                    "submit_agent_request",
                    submit_params(
                        session="psess:configured-app", profile="app-reader", key="socket-tools"
                    ),
                )
            )
            request_id = str(started["request_id"])
            deadline = time.monotonic() + 10
            while True:
                row = receipt(
                    await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                    )
                )
                if row["status"] == "interrupted":
                    break
                assert time.monotonic() < deadline, repr(row)
                await asyncio.sleep(0.01)
            activities = cast("list[dict[str, Any]]", row["activities"])
            assert [r["status"] for r in activities] == ["completed", "interrupted"]
            assert len(reads) == 3  # deterministic metadata + each child's call-1
            events = value(process.journal.read_events())
            effects = {
                e.payload["key"]
                for e in events
                if e.event == "agent_graph.record" and e.payload.get("kind") == "effect"
            }
            assert len(effects) == 3
        finally:
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    asyncio.run(journey())
    scripted.after = None
    scripted.responses.append(final("resumed review"))
    second = compose_configured(tmp_path, sdk, "tools-two")
    try:
        conn = connection(second)
        receipt(
            dispatch(
                second,
                conn,
                "resume_agent_request",
                {"request_id": request_id, "product_session_ref": "psess:configured-app"},
            )
        )
        row = app_wait(second, request_id, "completed")
        assert row.result is not None
        assert (
            json.loads(row.result.content)["outputs"]["metadata"]["items"][0]["locator"]
            == "README.md"
        )
        assert len(reads) == 3 and len(scripted.requests) == 5
    finally:
        second.close()


def test_narrow_parameter_grant_denies_child_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sdk, instance, contribution, _snapshot, scripted = app_setup(tmp_path, monkeypatch)
    # Remove deterministic read so the first attempted effect is the child's.
    body = json.loads((tmp_path / "actor-workflows.json").read_text())
    body["workflows"][0]["steps"].pop(1)
    save_catalog(tmp_path, body)
    process = compose_configured(tmp_path, sdk, "narrow")
    try:
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
                expires_at="2099-01-01T00:00:00Z",
            )
        )
        conn = connection(process)
        started = receipt(
            dispatch(
                process,
                conn,
                "submit_agent_request",
                submit_params(session="psess:configured-app", profile="app-reader"),
            )
        )
        row = app_wait(process, str(started["request_id"]), "failed")
        assert row.error == "tool_denied" and len(scripted.requests) == 1
        activity = JournalRecords(process.journal).get(
            "actor_activity", row.request_id + ":child:analysis"
        )
        assert activity is not None and activity["status"] == "failed"
    finally:
        process.close()


def test_queued_job_survives_restart_and_catalog_change_cannot_retarget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripted = setup(tmp_path, monkeypatch, [final("a"), final("b"), final("c"), final("d")])
    process = compose(tmp_path, boot="queue-one")
    try:
        mint(process)
        bridge = process.agent_requests
        assert bridge is not None
        runtime = bridge.runtime
        policy = bridge.policies["global"]
        from qma.daemon.request_runtime.contracts import RequestSpec

        queued = value(
            runtime.submit(
                RequestSpec(
                    "queued",
                    "operator",
                    "psess:agent",
                    0,
                    policy.profile,
                    "queued work",
                    policy.provider_id,
                )
            )
        )
        queued_id = queued.request_id
        assert queued.status == "queued" and scripted.requests == []
        assert [r["status"] for r in children(process, connection(process), queued_id)] == [
            "queued",
            "queued",
        ]
    finally:
        process.close()
    second = compose(tmp_path, boot="queue-two")
    try:
        conn = connection(second)
        row = wait_status(second, conn, queued_id, "completed")
        assert row["attempt"] == 1 and len(scripted.requests) == 2
    finally:
        second.close()


def test_revoked_grant_stops_child_and_withholds_activity_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sdk, instance, contribution, _snapshot, scripted = app_setup(tmp_path, monkeypatch)
    body = json.loads((tmp_path / "actor-workflows.json").read_text())
    body["workflows"][0]["steps"].pop(1)
    save_catalog(tmp_path, body)
    process = compose_configured(tmp_path, sdk, "revoked")
    try:
        app_session(process, instance, contribution)

        def revoke(_: int) -> None:
            value(
                process.product_sessions.revoke_grant(
                    "psess:configured-app",
                    grant_id="grant:configured-browse",
                    principal="operator",
                    reason="fixture",
                    revoked_at="2026-10-04T00:00:00Z",
                )
            )

        scripted.after = revoke
        conn = connection(process)
        started = receipt(
            dispatch(
                process,
                conn,
                "submit_agent_request",
                submit_params(session="psess:configured-app", profile="app-reader"),
            )
        )
        row = app_wait(process, str(started["request_id"]), "failed")
        assert row.error == "tool_denied" and len(scripted.requests) == 1
        disclosed = receipt(
            dispatch(
                process,
                conn,
                "get_agent_request",
                {"request_id": row.request_id, "product_session_ref": "psess:configured-app"},
            )
        )
        assert (
            disclosed["content_withheld"] is True
            and "activities" not in disclosed
            and "content" not in disclosed
        )
    finally:
        process.close()


def test_catalog_upgrade_refuses_queued_job_retarget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripted = setup(tmp_path, monkeypatch, [final("a"), final("b")])
    process = compose(tmp_path, boot="pin-one")
    try:
        mint(process)
        bridge = process.agent_requests
        assert bridge is not None
        runtime = bridge.runtime
        policy = bridge.policies["global"]
        from qma.daemon.request_runtime.contracts import RequestSpec

        queued_id = value(
            runtime.submit(
                RequestSpec(
                    "pinned",
                    "operator",
                    "psess:agent",
                    0,
                    policy.profile,
                    "queued work",
                    policy.provider_id,
                )
            )
        ).request_id
    finally:
        process.close()
    body = json.loads((tmp_path / "actor-workflows.json").read_text())
    body["roles"][0]["version"] = "2"
    body["workflows"][0]["version"] = "2"
    body["workflows"][0]["steps"][1]["role"] = "analyst:2"
    body["routes"][0]["workflow"] = "assessment:2"
    save_catalog(tmp_path, body)
    second = compose(tmp_path, boot="pin-two")
    try:
        conn = connection(second)
        row = receipt(
            dispatch(
                second,
                conn,
                "get_agent_request",
                {"request_id": queued_id, "product_session_ref": "psess:agent"},
            )
        )
        assert row["status"] == "failed" and row["content_withheld"] is True
        assert scripted.requests == []
    finally:
        second.close()


def test_deterministic_only_job_executes_domain_read_without_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sdk, instance, contribution, _snapshot, scripted = app_setup(tmp_path, monkeypatch)
    body = json.loads((tmp_path / "actor-workflows.json").read_text())
    body["workflows"][0]["steps"] = [
        s for s in body["workflows"][0]["steps"] if s["kind"] != "agent"
    ]
    save_catalog(tmp_path, body)
    process = compose_configured(tmp_path, sdk, "deterministic")
    try:
        app_session(process, instance, contribution)
        conn = connection(process)
        started = receipt(
            dispatch(
                process,
                conn,
                "submit_agent_request",
                submit_params(session="psess:configured-app", profile="app-reader"),
            )
        )
        row = app_wait(process, str(started["request_id"]), "completed")
        assert row.result is not None
        assert (
            json.loads(row.result.content)["outputs"]["metadata"]["items"][0]["locator"]
            == "README.md"
        )
        assert scripted.requests == []
    finally:
        process.close()


def test_native_tool_provider_is_refused_before_actor_launch(tmp_path: Path) -> None:
    from qma.daemon.request_runtime.contracts import CopilotProfile, ProviderCapabilities
    from qma.daemon.request_runtime.daemon_bridge import AgentRequestPolicy

    catalog(tmp_path)
    provider = ScriptedText([final("unused")])
    provider.capabilities = ProviderCapabilities("native", native_tools=True)
    process = compose(tmp_path)
    try:
        result = process.configure_agent_requests(
            providers={"native": provider},
            policies={
                "global": AgentRequestPolicy(CopilotProfile("global"), "authoring", "native")
            },
        )
        assert is_refusal(result) and provider.requests == []
    finally:
        process.close()
