"""Paired partition retry journeys; availability and inference are synthetic."""

from __future__ import annotations

import asyncio
import time
from dataclasses import replace
from typing import Any

import pytest
from qma.core.ontology import ActorId
from qma.core.ports.capabilities import RoleBase
from qma.core.ports.permissions import PermissionPolicy
from qma.core.vocabulary.enums import EdgeMapping
from qma.daemon.capabilities.spawn import SpawnRequest
from qma.daemon.knowledge.service import KnowledgeService
from qma.daemon.request_runtime.graph_storage import JournalCheckpointer, JournalRecords
from qma.daemon.request_runtime.providers import ProviderError
from qma.daemon.taskgraph.join import JoinArrival, JoinPartitionStatus, JoinWatermark, WatermarkKind
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from qmf.core import is_refusal
from support.authored_graph import configure_graph, graph_host
from test_request_runtime_daemon import receipt, rpc, submit_params, value, ws_connect


@pytest.mark.parametrize(
    "defect",
    [
        "none",
        "missing_failure",
        "pending_effect",
        "wrong_partition",
        "wrong_definition",
        "wrong_join_revision",
        "foreign_owner",
        "foreign_principal",
        "foreign_lease",
        "owner_only",
        "revoked_grant",
        "expired_grant",
        "revoked_after_admission",
        "expired_after_admission",
        "released_after_admission",
        "changed_effect",
        "changed_mapping",
        "changed_cardinality",
        "changed_source_event",
        "changed_result_identity",
        "changed_watermark",
        "changed_edge",
        "changed_join_revision",
        "changed_partition_status",
        "changed_refusal",
        "unknown_effect",
        "admission_write_loss",
        "receipt_only",
        "foreign_sibling",
        "completed_mutation",
        "completed_missing_seal",
    ],
)
def test_paired_partition_retry_requires_known_refusal_and_preserves_exact_join(
    tmp_path: Any, monkeypatch: Any, defect: str
) -> None:
    sdk, instance, contribution, provider = configure_graph(tmp_path, monkeypatch, "deterministic")
    available = [True]
    process, task_id = graph_host(
        tmp_path, sdk, instance, contribution, provider, availability=lambda: available[0]
    )
    original_lease = process.task_dispatcher.dispatch_lease_for(task_id)
    assert original_lease is not None
    # Synthetic external availability changes through the real ToolRegistry.
    original_put = JournalCheckpointer.put
    stopped: list[bool] = []

    def unavailable_after_predecessor(self: Any, *args: Any, **kwargs: Any) -> Any:
        result = original_put(self, *args, **kwargs)
        checkpoint = args[1]
        if (
            defect != "missing_failure"
            and not stopped
            and "metadata" in checkpoint.get("channel_values", {}).get("outputs", {})
        ):
            stopped.append(True)
            available[0] = False
        return result

    monkeypatch.setattr(JournalCheckpointer, "put", unavailable_after_predecessor)
    original_record = JournalRecords.put

    def abrupt_loss_without_refusal(self: Any, kind: Any, key: Any, body: Any) -> Any:
        result = original_record(self, kind, key, body)
        if (
            defect == "missing_failure"
            and not stopped
            and kind == "effect"
            and body.get("status") == "observed"
        ):
            stopped.append(True)
            raise ProviderError(
                "outcome_unknown", "Synthetic observed checkpoint loss without known failure"
            )
        return result

    monkeypatch.setattr(JournalRecords, "put", abrupt_loss_without_refusal)
    reads: list[str] = []
    original_read = KnowledgeService.supersedes_chain

    def observe(self: Any, source_id: Any) -> Any:
        reads.append(source_id)
        return original_read(self, source_id)

    monkeypatch.setattr(KnowledgeService, "supersedes_chain", observe)
    request_id = ""
    plan: Any = None
    admitted_once = [False]
    params = submit_params(
        session="psess:configured-app", profile="app-reader", prompt="Inspect corpus"
    )

    async def journey(reopen: bool = False) -> None:
        nonlocal request_id, plan
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
                assert process.canonical_requests is not None
                assert "error" in await rpc(
                    reader,
                    writer,
                    "resume_agent_request",
                    {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                )
                if defect in {"pending_effect", "unknown_effect"}:
                    JournalRecords(process.journal).put(
                        "effect",
                        request_id + ":step:source",
                        {"status": "pending" if defect == "pending_effect" else "unknown"},
                    )
                if defect == "foreign_sibling":
                    durable = process.task_dispatcher.store.durable
                    graph = durable.graph_for_task(task_id)
                    value(
                        durable.open_join(
                            graph_run_id=graph.id,
                            node_id="collect",
                            edge_id="source:collect",
                            definition_revision=1,
                            join_revision=1,
                            mapping=EdgeMapping.ONE,
                            expected_cardinality=2,
                            duplicate_key_policy="refuse",
                            join_id="join:foreign-sibling",
                        )
                    )
                    for partition in ("metadata", "source"):
                        value(
                            durable.apply_join_arrival(
                                "join:foreign-sibling",
                                JoinArrival(
                                    partition,
                                    "foreign:" + partition,
                                    "2026-10-03T00:00:00Z",
                                    "2026-10-03T00:00:00Z",
                                    result_identity="foreign:" + partition,
                                ),
                            )
                        )
                original_append = process.journal.append_event
                if defect == "admission_write_loss":
                    from qmf.data.store.refusals import storage_failure

                    def lose_admission(event: str, **kwargs: Any) -> Any:
                        if event == "canonical_request.partition_retry_admitted":
                            return storage_failure("Synthetic failed admission receipt write")
                        return original_append(event=event, **kwargs)

                    monkeypatch.setattr(process.journal, "append_event", lose_admission)

                def revoke() -> None:
                    value(
                        process.product_sessions.revoke_grant(
                            "psess:configured-app",
                            grant_id="grant:configured-browse",
                            principal="operator",
                            reason="Synthetic revocation",
                            revoked_at="2026-10-03T00:00:00Z",
                        )
                    )

                def expire() -> None:
                    actor = process.agent_requests.runtime.providers[
                        value(process.agent_requests.runtime.get(request_id)).spec.provider_id
                    ]
                    actor.now = lambda: "2100-01-01T00:00:00Z"

                if defect == "revoked_grant":
                    revoke()
                elif defect == "expired_grant":
                    expire()
                admitted = (
                    process.canonical_requests.reconcile_partition_retry(
                        request_id,
                        principal="foreign" if defect == "foreign_principal" else "operator",
                        owner=ActorId("quant:research/foreign")
                        if defect == "foreign_owner"
                        else original_lease.owner,
                        dispatch_lease=replace(original_lease, holder_agent_id="agent:foreign")
                        if defect == "foreign_lease"
                        else original_lease,
                        partition_id="metadata" if defect == "wrong_partition" else "source",
                        definition_revision=2 if defect == "wrong_definition" else 1,
                        join_revision=2 if defect == "wrong_join_revision" else 1,
                    )
                    if defect != "owner_only"
                    else process.canonical_requests.reconcile_owner(
                        request_id,
                        principal="operator",
                        owner=original_lease.owner,
                        dispatch_lease=original_lease,
                    )
                )
                refused = {
                    "missing_failure",
                    "pending_effect",
                    "wrong_partition",
                    "wrong_definition",
                    "wrong_join_revision",
                    "foreign_owner",
                    "foreign_principal",
                    "foreign_lease",
                    "revoked_grant",
                    "expired_grant",
                    "unknown_effect",
                }
                if defect in refused or defect == "admission_write_loss":
                    assert is_refusal(admitted), admitted
                    if defect != "admission_write_loss":
                        assert not process.task_dispatcher.store.durable.join_states()
                elif defect != "owner_only":
                    plan = value(admitted)
                    if defect in {
                        "none",
                        "receipt_only",
                        "foreign_sibling",
                        "completed_mutation",
                        "completed_missing_seal",
                    }:
                        before = [
                            e
                            for e in value(process.journal.read_events())
                            if e.event == "canonical_request.partition_retry_admitted"
                        ]
                        value(
                            process.canonical_requests.reconcile_partition_retry(
                                request_id,
                                principal="operator",
                                owner=original_lease.owner,
                                dispatch_lease=original_lease,
                                partition_id="source",
                                definition_revision=1,
                                join_revision=1,
                            )
                        )
                        assert [
                            e
                            for e in value(process.journal.read_events())
                            if e.event == "canonical_request.partition_retry_admitted"
                        ] == before
                    if defect == "receipt_only" and not admitted_once[0]:
                        admitted_once[0] = True
                        return
                    assert plan.reinvoke_partition_ids == ("source",)
                    assert dict(plan.reused_result_identities) == {
                        "metadata": request_id + ":step:metadata"
                    }
                    if defect == "revoked_after_admission":
                        revoke()
                    elif defect == "expired_after_admission":
                        expire()
                    elif defect == "released_after_admission":
                        process.task_dispatcher.store.release_leases(task_id)
                    elif defect == "changed_effect":
                        observed = JournalRecords(process.journal).get(
                            "effect", request_id + ":step:metadata"
                        )
                        assert observed is not None
                        JournalRecords(process.journal).put(
                            "effect",
                            request_id + ":step:metadata",
                            {**observed, "result": {"synthetic": "foreign"}},
                        )
                    elif defect == "changed_refusal":
                        JournalRecords(process.journal).put("partition_refusal", request_id, {})
                    elif defect.startswith("changed_"):
                        join = plan.join
                        if defect == "changed_mapping":
                            join = replace(join, mapping=EdgeMapping.KEYED_JOIN)
                        elif defect == "changed_cardinality":
                            join = replace(join, expected_cardinality=3)
                        elif defect == "changed_watermark":
                            join = replace(
                                join,
                                watermark=JoinWatermark(
                                    WatermarkKind.TIMEOUT, "foreign", "2026-10-03T00:00:00Z"
                                ),
                            )
                        elif defect == "changed_edge":
                            join = replace(join, edge_id="foreign:edge")
                        elif defect == "changed_join_revision":
                            join = replace(join, join_revision=2)
                        else:
                            successful = join.partition("metadata")
                            changes = (
                                {"source_event_id": "foreign:event"}
                                if defect == "changed_source_event"
                                else {"result_identity": "foreign:result"}
                                if defect == "changed_result_identity"
                                else {"status": JoinPartitionStatus.PENDING}
                            )
                            join = join.with_partitions(
                                (replace(successful, **changes), join.partition("source"))
                            )
                        value(process.task_dispatcher.store.durable.persist_join(join))
                resumed = await rpc(
                    reader,
                    writer,
                    "resume_agent_request",
                    {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                )
                if defect not in {
                    "none",
                    "receipt_only",
                    "foreign_sibling",
                    "completed_mutation",
                    "completed_missing_seal",
                }:
                    assert "error" in resumed, resumed
                    assert len(reads) == 1 and not provider.requests
                    duplicate = await rpc(reader, writer, "submit_agent_request", params)
                    if defect in {"revoked_grant", "revoked_after_admission"}:
                        assert "error" in duplicate
                    else:
                        assert str(receipt(duplicate)["request_id"]) == request_id
                    if defect == "admission_write_loss":
                        monkeypatch.setattr(process.journal, "append_event", original_append)
                        value(
                            process.canonical_requests.reconcile_partition_retry(
                                request_id,
                                principal="operator",
                                owner=original_lease.owner,
                                dispatch_lease=original_lease,
                                partition_id="source",
                                definition_revision=1,
                                join_revision=1,
                            )
                        )
                        resumed = await rpc(
                            reader,
                            writer,
                            "resume_agent_request",
                            {
                                "request_id": request_id,
                                "product_session_ref": "psess:configured-app",
                            },
                        )
                    else:
                        return
                receipt(resumed)
            row: Any
            deadline = time.monotonic() + 12
            while True:
                row = receipt(
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
            assert row["attempt"] == (2 if reopen else 1)
            assert len(reads) == (2 if reopen else 1)
            assert not provider.requests
            if reopen:
                joined = row["canonical_join"]["partition_join"]
                assert {p["partition_id"]: p["result_identity"] for p in joined["partitions"]} == {
                    "metadata": request_id + ":step:metadata",
                    "source": request_id + ":step:source",
                }
                assert all(p["status"] == "done" for p in joined["partitions"])
                assert joined["definition_revision"] == 1 and joined["join_revision"] == 1
                assert row["canonical_join"]["certainty"] == "unknown"
                if defect in {"completed_mutation", "completed_missing_seal"}:
                    durable = process.task_dispatcher.store.durable
                    original_join = value(durable.get_join(plan.join.join_id))
                    observation = [
                        dict(e.payload)
                        for e in value(process.journal.read_events())
                        if e.event == "canonical_request.observed"
                        and e.payload.get("request_id") == request_id
                    ][-1]
                    if defect == "completed_mutation":
                        successful = original_join.partition("metadata")
                        value(
                            durable.persist_join(
                                original_join.with_partitions(
                                    (
                                        replace(successful, result_identity="foreign:result"),
                                        original_join.partition("source"),
                                    )
                                )
                            )
                        )
                    else:
                        # Synthetic loss of the completed disclosure seal. Durable
                        # history still must not grant execution or settle UNKNOWN.
                        unsealed = {
                            k: v for k, v in observation.items() if k != "partition_join_seal"
                        }
                        value(
                            process.journal.append_event(
                                "canonical_request.observed", payload=unsealed
                            )
                        )
                    assert "error" in await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {"request_id": request_id, "product_session_ref": "psess:configured-app"},
                    )
                    if defect == "completed_mutation":
                        value(durable.persist_join(original_join))
                    else:
                        value(
                            process.journal.append_event(
                                "canonical_request.observed", payload=observation
                            )
                        )
                    restored = receipt(
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
                    assert restored["canonical_join"] == row["canonical_join"]
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
    available[0] = True
    process, reopened_task = graph_host(
        tmp_path, sdk, instance, contribution, provider, first=False
    )
    assert reopened_task == task_id
    value(
        process.agent_capabilities.spawn(
            SpawnRequest(
                "agent:read-join",
                original_lease.owner,
                "session:read-join",
                RoleBase("reader", tool_ids=frozenset({"fixture:browse"})),
                role_policy=PermissionPolicy("reader", frozenset({"library.read"})),
            )
        )
    )
    try:
        asyncio.run(journey(True))
        if defect != "changed_effect":
            assert (
                JournalRecords(process.journal).get("effect", request_id + ":step:metadata")
                == predecessor
            )
        handle = process.jobs.handle_for_task(task_id)
        assert (
            handle is not None
            and handle.state.value == "unknown"
            and handle.attempt_id == accepted[0]["job_attempt"]
        )
        assert [
            dict(e.payload)
            for e in value(process.journal.read_events())
            if e.event == "canonical_request.accepted"
        ] == accepted
        if defect not in {
            "missing_failure",
            "pending_effect",
            "wrong_partition",
            "wrong_definition",
            "wrong_join_revision",
            "foreign_owner",
            "foreign_principal",
            "foreign_lease",
            "revoked_grant",
            "expired_grant",
            "unknown_effect",
        }:
            assert process.task_dispatcher.task_for(task_id).state.value == "unknown"
            assert (
                process.task_dispatcher.ledgers.get(task_id).attempt_no
                == accepted[0]["task_attempt"]
            )
            if defect != "released_after_admission":
                assert process.task_dispatcher.dispatch_lease_for(task_id) == original_lease
    finally:
        process.close()

    if defect == "receipt_only":
        process, _ = graph_host(tmp_path, sdk, instance, contribution, provider, first=False)
        value(
            process.agent_capabilities.spawn(
                SpawnRequest(
                    "agent:read-join",
                    original_lease.owner,
                    "session:read-join",
                    RoleBase("reader", tool_ids=frozenset({"fixture:browse"})),
                    role_policy=PermissionPolicy("reader", frozenset({"library.read"})),
                )
            )
        )
        try:
            # The saved admission receipt has no continuation authority. The
            # journey first proves resume refuses, then explicitly admits again.
            asyncio.run(journey(True))
        finally:
            process.close()
