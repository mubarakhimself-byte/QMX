"""Real paired request execution creates host-derived CT47 provenance.

The injected provider is explicitly synthetic and offline. Task and Agent are
admitted through the real graph dispatcher and frozen capability spawn API;
these tests never pre-register an ExperimentSpec or manufacture an author receipt.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

import pytest
from qma.core.ontology import ActorId, DeskSlug
from qma.core.ports.capabilities import RoleBase
from qma.core.ports.experiments import ExperimentSpec
from qma.core.ports.permissions import PermissionPolicy
from qma.core.vocabulary.enums import TaskMissionState
from qma.daemon.capabilities.spawn import SpawnRequest
from qma.daemon.experiments.service import ExperimentSpecService, RegisteredExperiment
from qma.daemon.journal.authoritative import AuthoritativeJournal, JournalAppendReceipt
from qma.daemon.ledgers.experiment import ExperimentLedger
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.contracts import (
    CopilotProfile,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    RequestSpec,
)
from qma.daemon.request_runtime.daemon_bridge import AgentRequestPolicy
from qma.daemon.request_runtime.service import RequestRuntime
from qma.daemon.taskgraph.records import DispatchLease, TaskGraph, TaskRecord
from qma.wire.grant_record import GrantRevocation
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from qmf.core import Instant, Result, is_refusal
from qmf.data.store.refusals import storage_failure
from test_pairing_listener import _pair_over_listener  # pyright: ignore[reportPrivateUsage]
from test_request_runtime_daemon import compose, mint, rpc, submit_params, value, ws_connect

DEPLOYMENT = "synthetic:offline-authoring-v1"
PROPOSAL: dict[str, object] = {
    "data_ref": "fp1:sha256:" + "a" * 64,
    "environment_ref": "env:local",
    "resolved_config_ref": "fp1:sha256:" + "b" * 64,
    "seed": 7,
    "cost_assumptions": {"spread_usd_cents": 10},
}


class SyntheticAuthor:
    capabilities = ProviderCapabilities("synthetic-author")

    def __init__(self, content: str | None = None, deployment: str | None = DEPLOYMENT) -> None:
        self.content = json.dumps(PROPOSAL) if content is None else content
        self.deployment = deployment
        self.requests: list[ProviderRequest] = []
        self.during_execution: Callable[[], object] = lambda: None

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        self.requests.append(request)
        self.during_execution()
        return ProviderResult(self.content, deployment_id=self.deployment)


def prepare(
    process: DaemonProcess,
    provider: SyntheticAuthor,
    *,
    permission: bool = True,
    task_id: str = "task:author",
    configure_runtime: bool = True,
) -> None:
    if is_refusal(process.product_sessions.get("psess:agent")):
        mint(process)
    owner = value(ActorId.mint(DeskSlug.RESEARCH, "author"))
    value(
        process.agent_capabilities.spawn(
            SpawnRequest(
                agent_id="agent:admitted-author",
                owner=owner,
                session_id="session:authoring",
                role_base=RoleBase("experiment-author"),
                role_policy=PermissionPolicy(
                    "experiment-author",
                    frozenset({"experiment.register"}) if permission else frozenset(),
                ),
            )
        )
    )
    task = TaskRecord(
        id=task_id,
        mission_id="mission:author",
        owner=owner,
        intent="author experiment",
        state=TaskMissionState.READY,
        inputs={
            "agent_session_ref": "session:authoring",
            "authoring_product_session_ref": "psess:agent",
            "authoring_profile_id": "global",
            **{
                "authoring_" + key: PROPOSAL[key]
                for key in ("data_ref", "environment_ref", "resolved_config_ref")
            },
        },
    )
    process.task_dispatcher.materialize(
        TaskGraph(
            id="graph:" + task_id,
            mission_id=task.mission_id,
            tasks=(task,),
        )
    )
    value(
        process.task_dispatcher.dispatch_task(
            task_id=task.id, holder_agent_id="agent:admitted-author"
        )
    )
    if not configure_runtime:
        return
    value(
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


async def request(process: DaemonProcess) -> dict[str, object]:
    bound = value(await process.bind())
    _, proof = await _pair_over_listener(process, bound.host, bound.port)
    reader, writer, opening = await ws_connect(process, proof=proof)
    assert b"101 Switching Protocols" in opening
    try:
        initialized = await rpc(
            reader,
            writer,
            "initialize",
            {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
        )
        assert "result" in initialized, initialized
        submitted = await rpc(
            reader,
            writer,
            "submit_agent_request",
            submit_params(prompt="Return the pinned experiment identity as JSON"),
        )
        if "error" in submitted:
            return {"submission_error": submitted["error"]}
        assert "result" in submitted, submitted
        raw_submitted = submitted["result"]
        assert isinstance(raw_submitted, dict)
        submitted_body = cast("dict[str, object]", raw_submitted)
        reference: dict[str, object] = {
            "product_session_ref": "psess:agent",
            "request_id": submitted_body["request_id"],
        }
        deadline = time.monotonic() + 8
        while True:
            response = await rpc(reader, writer, "get_agent_request", reference)
            assert "result" in response, response
            raw_body = response["result"]
            assert isinstance(raw_body, dict)
            body = cast("dict[str, object]", raw_body)
            if body["status"] in {"completed", "failed", "interrupted"}:
                return body
            assert time.monotonic() < deadline, body
            await asyncio.sleep(0.01)
    finally:
        writer.close()
        await writer.wait_closed()


def run_owned(
    process: DaemonProcess, check: Callable[[dict[str, object]], None]
) -> dict[str, object]:
    async def run() -> dict[str, object]:
        try:
            result = await request(process)
            check(result)
            return result
        finally:
            await process.aclose()

    return asyncio.run(run())


def test_actual_paired_provider_output_registers_and_receipt_survives_restart(
    tmp_path: Path,
) -> None:
    process = compose(tmp_path)
    provider = SyntheticAuthor()
    prepare(process, provider)

    def check(result: dict[str, object]) -> None:
        assert result["status"] == "completed", result
        raw_receipt = result["experiment_authoring"]
        assert isinstance(raw_receipt, dict)
        receipt = cast("dict[str, object]", raw_receipt)
        assert receipt["request_id"] == provider.requests[0].request_id
        assert len(provider.requests) == 1
        assert receipt["observed_deployment_ref"] == DEPLOYMENT
        registered = value(process.experiments.resolve(receipt["spec_fp1"]))
        assert registered.dispatch_lease == process.task_dispatcher.dispatch_lease_for(
            "task:author"
        )
        ledger = process.task_dispatcher.ledgers.get("task:author")
        assert ledger is not None
        assert registered.registering_attempt_no == ledger.attempt_no
        assert registered.spec.model_and_harness_version["model"] == DEPLOYMENT
        bridge = process.agent_requests
        assert bridge is not None
        assert (
            value(bridge.runtime.get(str(result["request_id"]))).spec.authoring_task_id
            == "task:author"
        )
        (tmp_path / "authoring-proof.json").write_text(json.dumps(result, indent=2))

    result = run_owned(process, check)
    raw_receipt = result["experiment_authoring"]
    assert isinstance(raw_receipt, dict)
    receipt = cast("dict[str, object]", raw_receipt)
    reopened = compose(tmp_path, boot="authoring-restart")
    try:
        restored = value(reopened.experiments.resolve(receipt["spec_fp1"]))
        assert restored.registering_deployment_ref == DEPLOYMENT
        assert any(
            entry.body.get("kind") == "registered_model_deployment"
            and entry.model_deployment_ref == DEPLOYMENT
            for entry in restored.ledger.entries
        )
        events = value(reopened.journal.read_events())
        assert sum(event.event == "experiment.authoring_receipt" for event in events) == 1
        assert len(provider.requests) == 1
    finally:
        reopened.close()


@pytest.mark.parametrize(
    "mode",
    [
        "permission",
        "missing-deployment",
        "unknown-field",
        "duplicate-field",
        "nested-json",
        "foreign-data",
        "cancel",
        "reassign-aba",
        "mutable-task-input",
    ],
)
def test_authoring_refuses_without_registration(tmp_path: Path, mode: str) -> None:
    provider = SyntheticAuthor()
    if mode == "missing-deployment":
        provider.deployment = None
    if mode == "unknown-field":
        provider.content = json.dumps({**PROPOSAL, "holder_agent_id": "forged"})
    if mode == "duplicate-field":
        provider.content = '{"seed":7,"seed":8}'
    if mode == "nested-json":
        provider.content = "[" * 2000 + "0" + "]" * 2000
    if mode == "foreign-data":
        provider.content = json.dumps({**PROPOSAL, "data_ref": "foreign"})
    process = compose(tmp_path)
    prepare(process, provider, permission=mode != "permission")
    if mode == "cancel":
        bridge = process.agent_requests
        assert bridge is not None
        provider.during_execution = lambda: bridge.runtime.cancel(provider.requests[0].request_id)
    if mode == "reassign-aba":

        def reassign() -> None:
            value(
                process.task_dispatcher.reassign(
                    task_id="task:author", new_holder_agent_id="agent:other"
                )
            )
            value(
                process.task_dispatcher.reassign(
                    task_id="task:author", new_holder_agent_id="agent:admitted-author"
                )
            )

        provider.during_execution = reassign
    if mode == "mutable-task-input":

        def mutate_input() -> None:
            task = process.task_dispatcher.task_for("task:author")
            assert task is not None
            cast("dict[str, object]", task.inputs)["authoring_data_ref"] = "changed-in-place"

        provider.during_execution = mutate_input

    def check(result: dict[str, object]) -> None:
        if mode == "permission":
            assert "submission_error" in result, result
        else:
            assert result["status"] == "failed", result
        assert "experiment_authoring" not in result
        events = value(process.journal.read_events())
        assert not any(event.event == "experiment.registered" for event in events)
        assert len(provider.requests) == (0 if mode == "permission" else 1)

    run_owned(process, check)


@pytest.mark.parametrize("direct_ledger", [False, True])
def test_revocation_serializes_with_authoring_registration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    direct_ledger: bool,
) -> None:
    process = compose(tmp_path)
    provider = SyntheticAuthor()
    prepare(process, provider)
    value(
        process.product_sessions.host_grant(
            "psess:agent",
            grant_id="grant:author-context",
            instance_id="inst:local",
            op_id="qmb.analysis.project",
            op_version=1,
            effect_class="read",
            parameter_ceiling={"allow_keys": ["run_fp1", "as_of"]},
            expires_at="2027-01-01T00:00:00Z",
        )
    )
    entered, finished = threading.Event(), threading.Event()
    outcomes: list[Result[GrantRevocation]] = []

    def revoke() -> None:
        entered.set()
        kwargs = {
            "grant_id": "grant:author-context",
            "principal": "operator",
            "reason": "test",
            "revoked_at": "2026-10-04T00:00:00Z",
        }
        if direct_ledger:
            outcomes.append(process.product_sessions.ledger.revoke(**kwargs))
        else:
            outcomes.append(process.product_sessions.revoke_grant("psess:agent", **kwargs))
        finished.set()

    thread = threading.Thread(target=revoke)
    register = ExperimentSpecService.register

    def register_while_revoke_waits(
        self: ExperimentSpecService,
        spec: ExperimentSpec,
        *,
        dispatch_lease: DispatchLease,
        registering_attempt_no: object,
        model_deployment_ref: object,
        continuity_kind: object = "ExperimentSpec",
    ) -> Result[RegisteredExperiment]:
        thread.start()
        assert entered.wait(2)
        assert not finished.wait(0.05), "revocation crossed the authoring effect fence"
        return register(
            self,
            spec,
            dispatch_lease=dispatch_lease,
            registering_attempt_no=registering_attempt_no,
            model_deployment_ref=model_deployment_ref,
            continuity_kind=continuity_kind,
        )

    monkeypatch.setattr(ExperimentSpecService, "register", register_while_revoke_waits)

    def check(result: dict[str, object]) -> None:
        thread.join(2)
        assert not thread.is_alive() and outcomes and not is_refusal(outcomes[0])
        # Query disclosure may be withheld once the serialized revocation wins.
        events = value(process.journal.read_events())
        assert sum(event.event == "experiment.authoring_receipt" for event in events) == 1, result
        assert len(provider.requests) == 1

    run_owned(process, check)


def test_lost_final_snapshot_restores_uncertain_effect_without_provider_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = compose(tmp_path)
    provider = SyntheticAuthor()
    prepare(process, provider)
    append = AuthoritativeJournal.append_event

    def fail_final(
        self: AuthoritativeJournal,
        event: object,
        *,
        scope_path: object = (),
        payload: Mapping[str, object] | None = None,
        occurred_at: Instant | int | None = None,
        worker_authored_timestamp: object = None,
    ) -> Result[JournalAppendReceipt]:
        if (
            event == "agent_request.snapshot"
            and payload is not None
            and payload.get("status") in {"completed", "failed"}
        ):
            return storage_failure("synthetic final snapshot unavailable")
        return append(
            self,
            event,
            scope_path=scope_path,
            payload=payload,
            occurred_at=occurred_at,
            worker_authored_timestamp=worker_authored_timestamp,
        )

    monkeypatch.setattr(AuthoritativeJournal, "append_event", fail_final)

    def check(result: dict[str, object]) -> None:
        assert result["status"] == "failed" and result["error"] == "authoring_effect_uncertain", (
            result
        )
        bridge = process.agent_requests
        assert bridge is not None
        assert is_refusal(bridge.runtime.retry_interrupted(str(result["request_id"])))
        assert len(provider.requests) == 1

    result = run_owned(process, check)
    monkeypatch.setattr(AuthoritativeJournal, "append_event", append)
    reopened = compose(tmp_path, boot="final-snapshot-recovery")
    try:
        runtime = RequestRuntime(
            journal=reopened.journal,
            product_sessions=reopened.product_sessions,
            providers={provider.capabilities.provider_id: provider},
        )
        recovered = value(runtime.get(str(result["request_id"])))
        assert recovered.status == "failed" and recovered.error == "authoring_effect_uncertain"
        assert recovered.result == ProviderResult(provider.content, deployment_id=DEPLOYMENT)
        assert is_refusal(runtime.retry_interrupted(recovered.request_id))
        assert value(runtime.execute(recovered.request_id)) == recovered
        assert len(provider.requests) == 1
    finally:
        reopened.close()


def test_optimistic_registration_cache_cannot_authorize_receipt_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = compose(tmp_path)
    provider = SyntheticAuthor()
    prepare(process, provider)

    def fail_registration(
        self: ExperimentSpecService,
        spec: ExperimentSpec,
        lease: DispatchLease,
        ledger: ExperimentLedger,
        *,
        registering_attempt_no: int,
        registering_deployment_ref: str,
    ) -> Result[None]:
        return storage_failure("synthetic registration never reached SQLite")

    monkeypatch.setattr(ExperimentSpecService, "_persist_registration", fail_registration)

    def check(result: dict[str, object]) -> None:
        assert result["status"] == "failed" and result["error"] == "authoring_effect_uncertain", (
            result
        )
        events = value(process.journal.read_events())
        observation = next(
            event.payload
            for event in events
            if event.event == "experiment.authoring_output_observed"
        )
        assert not is_refusal(process.experiments.resolve(observation["proposed_spec_fp1"]))
        assert is_refusal(process.experiments.resolve_durable(observation["proposed_spec_fp1"]))
        assert is_refusal(process.reconcile_experiment_authoring(str(result["request_id"])))
        assert not any(
            event.event == "experiment.authoring_receipt"
            for event in value(process.journal.read_events())
        )
        assert len(provider.requests) == 1

    run_owned(process, check)


def test_queued_authoring_binding_cannot_retarget_after_restart(tmp_path: Path) -> None:
    provider = SyntheticAuthor()
    first = compose(tmp_path)
    try:
        prepare(first, provider, configure_runtime=False)
        runtime = RequestRuntime(
            journal=first.journal,
            product_sessions=first.product_sessions,
            providers={provider.capabilities.provider_id: provider},
        )
        queued = value(
            runtime.submit(
                RequestSpec(
                    idempotency_key="queued-authoring",
                    principal="operator",
                    product_session_id="psess:agent",
                    context_revision=0,
                    profile=CopilotProfile("global"),
                    prompt="author",
                    provider_id=provider.capabilities.provider_id,
                    authoring_task_id="task:author",
                )
            )
        )
        assert queued.status == "queued"
    finally:
        first.close()
    restarted = compose(tmp_path, boot="retarget-authoring")
    try:
        prepare(restarted, provider, task_id="task:different")
        bridge = restarted.agent_requests
        assert bridge is not None
        restored = value(bridge.runtime.get(queued.request_id))
        assert restored.status == "failed", restored
        assert restored.spec.authoring_task_id == "task:author"
        assert not provider.requests
        assert not any(
            event.event == "experiment.registered"
            for event in value(restarted.journal.read_events())
        )
    finally:
        restarted.close()


def test_partial_registration_reconciles_receipt_without_provider_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = compose(tmp_path)
    provider = SyntheticAuthor()
    prepare(process, provider)
    append = AuthoritativeJournal.append_event
    failed = False

    def fail_receipt(
        self: AuthoritativeJournal,
        event: object,
        *,
        scope_path: object = (),
        payload: Mapping[str, object] | None = None,
        occurred_at: Instant | int | None = None,
        worker_authored_timestamp: object = None,
    ) -> Result[JournalAppendReceipt]:
        nonlocal failed
        if event == "experiment.authoring_receipt" and not failed:
            failed = True
            return storage_failure("synthetic one-time receipt failure")
        return append(
            self,
            event,
            scope_path=scope_path,
            payload=payload,
            occurred_at=occurred_at,
            worker_authored_timestamp=worker_authored_timestamp,
        )

    monkeypatch.setattr(AuthoritativeJournal, "append_event", fail_receipt)

    def check(result: dict[str, object]) -> None:
        assert result["status"] == "failed" and result["error"] == "authoring_effect_uncertain"
        assert "experiment_authoring" not in result
        bridge = process.agent_requests
        assert bridge is not None
        request_id = str(result["request_id"])
        assert is_refusal(bridge.runtime.retry_interrupted(request_id))
        repaired = value(process.reconcile_experiment_authoring(request_id))
        assert repaired["reconciled"] is True
        assert len(provider.requests) == 1
        assert value(process.reconcile_experiment_authoring(request_id)) == repaired
        assert (
            sum(
                event.event == "experiment.registered"
                for event in value(process.journal.read_events())
            )
            == 1
        )
        assert (
            sum(
                event.event == "experiment.authoring_receipt"
                for event in value(process.journal.read_events())
            )
            == 1
        )

    run_owned(process, check)
