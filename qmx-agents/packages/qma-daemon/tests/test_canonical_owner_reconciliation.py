"""Actual paired restart recovery; all inference is explicitly synthetic."""

from __future__ import annotations

import asyncio
import time
from dataclasses import replace
from typing import Any

import pytest
from qma.core.ontology import ActorId
from qma.core.ports.capabilities import RoleBase
from qma.core.ports.permissions import PermissionPolicy
from qma.daemon.capabilities.spawn import SpawnRequest
from qma.daemon.knowledge.service import KnowledgeService
from qma.daemon.request_runtime.graph_storage import JournalRecords
from qma.daemon.request_runtime.providers import ProviderError
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from qmf.core import is_refusal
from test_authored_graphs import configure_graph, graph_host
from test_request_runtime_daemon import receipt, rpc, submit_params, value, ws_connect


@pytest.mark.parametrize(
    "composition,defect",
    [
        (composition, defect)
        for composition in ["specialist", "deterministic"]
        for defect in [
            "none",
            "foreign_owner",
            "foreign_principal",
            "missing_agent",
            "replaced_lease",
            "wider_capabilities",
            "stale_graph",
            "revoked_grant",
            "expired_grant",
            "unobserved_effect",
            "lease_lost_after_admission",
            "lease_replaced_after_admission",
            "grant_revoked_after_admission",
            "write_loss",
            "prior_child",
        ]
        if composition == "specialist" or defect != "prior_child"
    ],
)
def test_paired_restart_admits_original_owner_and_continues_one_successor(
    tmp_path: Any,
    monkeypatch: Any,
    composition: str,
    defect: str,
) -> None:
    sdk, instance, contribution, provider = configure_graph(tmp_path, monkeypatch, composition)
    process, task_id = graph_host(tmp_path, sdk, instance, contribution, provider)
    reads: list[str] = []
    original_read = KnowledgeService.supersedes_chain

    def observe(self: Any, source_id: Any) -> Any:
        reads.append(source_id)
        return original_read(self, source_id)

    monkeypatch.setattr(KnowledgeService, "supersedes_chain", observe)
    original_put = JournalRecords.put
    lost: list[bool] = []

    def lose_checkpoint(self: Any, kind: Any, key: Any, body: Any) -> Any:
        result = original_put(self, kind, key, body)
        if (
            defect != "prior_child"
            and not lost
            and kind == "effect"
            and body.get("status") == "observed"
        ):
            lost.append(True)
            if defect == "unobserved_effect":
                original_put(self, kind, key, {**body, "status": "pending"})
            raise ProviderError("outcome_unknown", "synthetic loss after observed predecessor")
        return result

    monkeypatch.setattr(JournalRecords, "put", lose_checkpoint)
    if defect == "prior_child":

        def lost_child(count: int) -> None:
            raise ProviderError("outcome_unknown", "synthetic loss after child inference started")

        provider.after = lost_child
    request_id = ""
    original_lease = process.task_dispatcher.dispatch_lease_for(task_id)
    assert original_lease is not None
    params = submit_params(
        session="psess:configured-app", profile="app-reader", prompt="Inspect corpus"
    )

    async def journey(reopen: bool = False) -> None:
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
                    receipt(await rpc(reader, writer, "submit_agent_request", params))["request_id"]
                )
            else:
                assert "error" in await rpc(
                    reader,
                    writer,
                    "resume_agent_request",
                    {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                )
                assert process.canonical_requests is not None
                supplied_lease = (
                    replace(original_lease, holder_agent_id="agent:foreign")
                    if defect == "replaced_lease"
                    else original_lease
                )

                def revoke() -> None:
                    value(
                        process.product_sessions.revoke_grant(
                            "psess:configured-app",
                            grant_id="grant:configured-browse",
                            principal="operator",
                            reason="synthetic revocation",
                            revoked_at="2026-10-03T00:00:00Z",
                        )
                    )

                if defect == "revoked_grant":
                    revoke()
                if defect == "expired_grant":
                    actor = process.agent_requests.runtime.providers[
                        value(process.agent_requests.runtime.get(request_id)).spec.provider_id
                    ]
                    actor.now = lambda: "2100-01-01T00:00:00Z"
                if defect == "stale_graph":
                    durable = process.task_dispatcher.store.durable
                    graph = durable.graph_for_task(task_id)
                    value(durable.persist(replace(graph, graph_template_ref="foreign:revision")))
                if defect == "write_loss":
                    from qmf.data.store.refusals import storage_failure

                    def lost_write(kind: str, body: dict[str, Any]) -> Any:
                        return storage_failure("synthetic admission write loss")

                    monkeypatch.setattr(process.canonical_requests, "_save", lost_write)
                restored = process.canonical_requests.reconcile_owner(
                    request_id,
                    principal="foreign" if defect == "foreign_principal" else "operator",
                    owner=ActorId("quant:research/foreign")
                    if defect == "foreign_owner"
                    else original_lease.owner,
                    dispatch_lease=supplied_lease,
                )
                if defect not in {
                    "none",
                    "lease_lost_after_admission",
                    "lease_replaced_after_admission",
                    "grant_revoked_after_admission",
                }:
                    assert is_refusal(restored), restored
                    assert "error" in await rpc(
                        reader,
                        writer,
                        "resume_agent_request",
                        {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                    )
                    assert len(reads) == 1 and len(provider.requests) == (
                        1 if defect == "prior_child" else 0
                    )
                    return
                value(restored)
                value(
                    process.canonical_requests.reconcile_owner(
                        request_id,
                        principal="operator",
                        owner=original_lease.owner,
                        dispatch_lease=original_lease,
                    )
                )
                if defect == "lease_lost_after_admission":
                    process.task_dispatcher.store.release_leases(task_id)
                    assert is_refusal(
                        process.canonical_requests.reconcile_owner(
                            request_id,
                            principal="operator",
                            owner=original_lease.owner,
                            dispatch_lease=original_lease,
                        )
                    )
                elif defect == "lease_replaced_after_admission":
                    process.task_dispatcher.store.record_lease(
                        replace(original_lease, holder_agent_id="agent:foreign")
                    )
                    assert is_refusal(
                        process.canonical_requests.reconcile_owner(
                            request_id,
                            principal="operator",
                            owner=original_lease.owner,
                            dispatch_lease=original_lease,
                        )
                    )
                elif defect == "grant_revoked_after_admission":
                    revoke()
                if defect != "none":
                    assert "error" in await rpc(
                        reader,
                        writer,
                        "resume_agent_request",
                        {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                    )
                    assert len(reads) == 1 and len(provider.requests) == (
                        1 if defect == "prior_child" else 0
                    )
                    return
                receipt(
                    await rpc(
                        reader,
                        writer,
                        "resume_agent_request",
                        {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                    )
                )
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
            assert row["status"] == ("completed" if reopen else "interrupted"), row
            assert len(reads) == (2 if reopen and composition == "deterministic" else 1)
            assert len(provider.requests) == (
                1 if (reopen and composition == "specialist") or defect == "prior_child" else 0
            )
            if reopen:
                assert row["canonical_join"]["certainty"] == "unknown"
                if composition == "specialist":
                    assert "synthetic specialist result" in row["content"]
                assert (
                    str(
                        receipt(await rpc(reader, writer, "submit_agent_request", params))[
                            "request_id"
                        ]
                    )
                    == request_id
                )
                assert "error" in await rpc(
                    reader,
                    writer,
                    "resume_agent_request",
                    {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                )
        finally:
            writer.close()
            await writer.wait_closed()
            await process.aclose()

    try:
        asyncio.run(journey())
        predecessor = JournalRecords(process.journal).get("effect", request_id + ":step:metadata")
        accepted = [
            dict(e.payload)
            for e in value(process.journal.read_events())
            if e.event == "canonical_request.accepted"
        ]
    finally:
        process.close()
    process, reopened_task = graph_host(
        tmp_path, sdk, instance, contribution, provider, first=False
    )
    assert reopened_task == task_id
    if defect != "missing_agent":
        value(
            process.agent_capabilities.spawn(
                SpawnRequest(
                    "agent:read-join",
                    original_lease.owner,
                    "session:read-join",
                    RoleBase("reader", tool_ids=frozenset({"fixture:browse"})),
                    role_policy=PermissionPolicy(
                        "reader",
                        frozenset({"library.read", "foreign.write"})
                        if defect == "wider_capabilities"
                        else frozenset({"library.read"}),
                    ),
                )
            )
        )
    try:
        asyncio.run(journey(True))
        assert (
            JournalRecords(process.journal).get("effect", request_id + ":step:metadata")
            == predecessor
        )
        assert [
            dict(e.payload)
            for e in value(process.journal.read_events())
            if e.event == "canonical_request.accepted"
        ] == accepted
        handle = process.jobs.handle_for_task(task_id)
        assert (
            handle is not None
            and handle.state.value == "unknown"
            and handle.attempt_id == accepted[0]["job_attempt"]
        )
        if defect == "none":
            ledger = process.task_dispatcher.ledgers.get(task_id)
            assert ledger is not None and ledger.attempt_no == accepted[0]["task_attempt"]
            assert process.task_dispatcher.dispatch_lease_for(task_id) == original_lease
    finally:
        process.close()
