"""Epic 73 — originating-session JobHandle cancellation and replay."""

from __future__ import annotations

from qma.core.ontology import ActorId, DeskSlug, Goal, Quant, RoleName
from qma.core.ports.execution import ExecutionEnvironmentDeclaration
from qma.core.ports.jobs import JobHandle
from qma.core.vocabulary.enums import ExecutionEnvironmentKind, JobHandleState, TaskMissionState
from qma.daemon import CompileRequest, MissionCompiler, TaskGraphDispatcher
from qma.daemon.envs import ComputeRouter, ExecutionEnvironmentRegistry
from qma.daemon.envs.jobs import JobHandleService, JobHandleStore
from qmf.core import Result, is_ok, is_refusal

_PRINCIPAL = "principal:local-operator"
_ORIGIN = "psess:home-origin"


def _owner() -> ActorId:
    result = ActorId.mint(DeskSlug.RESEARCH, "epic73")
    assert is_ok(result)
    return result.value


def _quant() -> Quant:
    actor = _owner()
    return Quant(
        actor_id=actor,
        desk=DeskSlug.RESEARCH,
        quant_slug="epic73",
        role=RoleName.RESEARCHER,
        name="Epic 73",
    )


def _job(
    *,
    origin: str | None = _ORIGIN,
    job_id: str = "job:epic-73",
    state: str = "queued",
    attempt_id: int = 2,
) -> tuple[JobHandleService, str]:
    service = JobHandleService()
    submitted = service.submit(
        owner=_owner(),
        task_id=f"task:{job_id}",
        job_id=job_id,
        logical_run_id=f"run:{job_id}",
        attempt_id=attempt_id,
        originating_product_session_ref=origin,
    )
    assert is_ok(submitted), submitted
    if state == "running":
        started = service.start(job_id)
        assert is_ok(started), started
    elif state == "done":
        assert is_ok(service.start(job_id))
        assert is_ok(service.complete(job_id, JobHandleState.DONE))
    elif state == "unknown":
        assert is_ok(service.start(job_id))
        assert is_ok(service.mark_unknown(job_id, trigger="timeout"))
    return service, job_id


def _payload(
    job_id: str = "job:epic-73",
    *,
    logical_run_id: str | None = None,
    attempt_id: int = 2,
    command_id: str = "cancel:73-1",
    expected_state: str = "queued",
    job_id_alias: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "handle_id": job_id,
        "logical_run_id": logical_run_id or f"run:{job_id}",
        "attempt_id": attempt_id,
        "command_id": command_id,
        "expected_state": expected_state,
    }
    if job_id_alias is not None:
        payload["job_id"] = job_id_alias
    return payload


def _cancel(
    service: JobHandleService,
    payload: object,
    *,
    principal_class: str = "operator",
    operator_principal: str = _PRINCIPAL,
    session_principal: str = _PRINCIPAL,
    producer_id: str = "tab:one",
    wire_id: str | int = "cancel-1",
):
    return service.cancel_from_product_session(
        payload,
        principal_class=principal_class,
        operator_principal=operator_principal,
        originating_session_principal=session_principal,
        producer_id=producer_id,
        wire_id=wire_id,
    )


class _CompletionWinsBeforeCancelCommit(JobHandleService):
    def __init__(self) -> None:
        super().__init__()
        self._raced = False

    def _commit(
        self,
        handle: JobHandle,
        *,
        event: str,
        previous: JobHandle | None = None,
    ) -> Result[JobHandle]:
        if event == "cancel_job" and not self._raced:
            self._raced = True
            completed = self.complete(handle.job_id, JobHandleState.DONE)
            assert is_ok(completed), completed
        return super()._commit(handle, event=event, previous=previous)


def test_cancel_job_exact_fences_and_authority() -> None:
    service, job_id = _job()
    for payload in (
        _payload(job_id, job_id_alias="job:another"),
        _payload(job_id, logical_run_id="run:another"),
        _payload(job_id, attempt_id=3),
    ):
        refused = _cancel(service, payload)
        assert is_refusal(refused)
        live = service.handle_for(job_id)
        assert live is not None and live.state is JobHandleState.QUEUED

    machine = _cancel(service, _payload(job_id), principal_class="machine")
    assert is_refusal(machine)
    wrong_operator = _cancel(
        service,
        _payload(job_id),
        operator_principal="principal:someone-else",
    )
    assert is_refusal(wrong_operator)
    wrong_session_owner = _cancel(
        service,
        _payload(job_id),
        session_principal="principal:someone-else",
    )
    assert is_refusal(wrong_session_owner)

    headless, headless_id = _job(origin=None, job_id="job:headless-73")
    unavailable = _cancel(
        headless,
        _payload(headless_id, logical_run_id=f"run:{headless_id}"),
    )
    assert is_refusal(unavailable)
    still_queued = headless.handle_for(headless_id)
    assert still_queued is not None and still_queued.state is JobHandleState.QUEUED


def test_queued_to_running_and_lost_ack_reuse_command_and_wire_pair() -> None:
    service, job_id = _job()
    started = service.start(job_id)
    assert is_ok(started)
    # expected_state records the queued observation and does not fence the race.
    accepted = _cancel(service, _payload(job_id, expected_state="queued"), wire_id=71)
    assert is_ok(accepted), accepted
    assert accepted.value.state is JobHandleState.CANCELLED

    replay = _cancel(service, _payload(job_id, expected_state="running"), wire_id=71)
    assert is_ok(replay), replay
    assert replay.value.state is JobHandleState.CANCELLED
    assert len(replay.value.later_commands) == 1
    recorded = replay.value.later_commands[0]
    assert recorded["command_id"] == "cancel:73-1"
    assert recorded["durable_command_id"] == f"{_ORIGIN}/cancel:73-1"
    assert recorded["command_hash"]
    assert recorded["job_id"] == job_id
    assert recorded["producer_id"] == "tab:one"
    assert recorded["wire_id"] == 71
    assert recorded["expected_state"] == "queued"
    duplicate = _cancel(service, _payload(job_id, expected_state="running"), wire_id=71)
    assert is_ok(duplicate)
    assert len(duplicate.value.later_commands) == 1

    changed_pair = _cancel(service, _payload(job_id), wire_id=72)
    assert is_refusal(changed_pair)


def test_successful_command_identity_rejects_retarget_and_changed_wire_id() -> None:
    service, first_id = _job()
    first = _cancel(service, _payload(first_id), wire_id="wire:first")
    assert is_ok(first), first
    assert first.value.state is JobHandleState.CANCELLED

    second = service.submit(
        owner=_owner(),
        task_id="task:second-cancel-target",
        job_id="job:second-cancel-target",
        logical_run_id="run:second-cancel-target",
        attempt_id=2,
        originating_product_session_ref=_ORIGIN,
    )
    assert is_ok(second), second
    retargeted = _cancel(
        service,
        _payload(
            second.value.job_id,
            logical_run_id=second.value.logical_run_id,
            attempt_id=second.value.attempt_id,
        ),
        wire_id="wire:first",
    )
    assert is_refusal(retargeted)
    still_queued = service.handle_for(second.value.job_id)
    assert still_queued is not None and still_queued.state is JobHandleState.QUEUED

    changed_wire = _cancel(service, _payload(first_id), wire_id="wire:changed")
    assert is_refusal(changed_wire)


def test_terminal_noop_unknown_refusal_and_nested_child_origin() -> None:
    terminal, terminal_id = _job(state="done")
    repeated = _cancel(
        terminal,
        _payload(terminal_id, logical_run_id=f"run:{terminal_id}"),
    )
    assert is_ok(repeated), repeated
    assert repeated.value.state is JobHandleState.DONE
    assert repeated.value.later_commands[0]["noop"] is True
    assert repeated.value.later_commands[0]["terminal_state"] == "done"

    unknown, unknown_id = _job(state="unknown")
    refused = _cancel(
        unknown,
        _payload(unknown_id, logical_run_id=f"run:{unknown_id}"),
    )
    assert is_refusal(refused)
    handle = unknown.handle_for(unknown_id)
    assert handle is not None and handle.state is JobHandleState.UNKNOWN

    parent, parent_id = _job(job_id="job:parent-73", origin="psess:parent")
    child = parent.submit(
        owner=_owner(),
        task_id="task:child-73",
        job_id="job:child-73",
        logical_run_id="run:child-73",
        originating_product_session_ref="psess:child",
    )
    assert is_ok(child)
    child_cancel = _cancel(
        parent,
        _payload("job:child-73", logical_run_id="run:child-73", attempt_id=1),
        session_principal=_PRINCIPAL,
    )
    assert is_ok(child_cancel), child_cancel
    parent_handle = parent.handle_for(parent_id)
    assert parent_handle is not None and parent_handle.state is JobHandleState.QUEUED
    assert child_cancel.value.originating_product_session_ref == "psess:child"


def test_detach_never_cancels_originating_handle() -> None:
    service, job_id = _job(state="running")
    detached = service.on_client_detach(job_id, event="wire.detach")
    assert is_ok(detached)
    assert detached.value.state is JobHandleState.RUNNING
    assert detached.value.originating_product_session_ref == _ORIGIN
    assert detached.value.later_commands == ()


def test_cancel_noop_on_dispatched_terminal_handle_skips_task_remap() -> None:
    owner = _quant()
    compiled = MissionCompiler(known_quant_actor_ids={owner.actor_id.value}).compile(
        CompileRequest(goal=Goal(text="terminal cancellation no-op"), owner=owner)
    )
    assert is_ok(compiled), compiled
    environments = ExecutionEnvironmentRegistry()
    assert is_ok(
        environments.register_declaration(
            ExecutionEnvironmentDeclaration.isolated(
                ExecutionEnvironmentKind.DOCKER,
                provider_ref="local-docker",
            )
        )
    )
    router = ComputeRouter(environments=environments)
    dispatcher = TaskGraphDispatcher(environments=environments, router=router)
    dispatcher.materialize(compiled.value.task_graph, mission=compiled.value.mission)
    task_id = compiled.value.task_graph.tasks[0].id
    assert is_ok(dispatcher.dispatch_task(task_id=task_id, holder_agent_id="agent:epic73"))
    service = JobHandleService(dispatcher=dispatcher, router=router)
    submitted = service.submit(
        owner=owner.actor_id,
        task_id=task_id,
        job_id="job:dispatched-terminal-noop",
        originating_product_session_ref=_ORIGIN,
    )
    assert is_ok(submitted), submitted
    assert is_ok(service.start(submitted.value.job_id))
    done = service.complete(submitted.value.job_id, JobHandleState.DONE)
    assert is_ok(done), done

    no_op = _cancel(
        service,
        _payload(
            submitted.value.job_id,
            logical_run_id=submitted.value.logical_run_id,
            attempt_id=submitted.value.attempt_id,
        ),
    )
    assert is_ok(no_op), no_op
    assert no_op.value.state is JobHandleState.DONE
    located = dispatcher.store.find_task(task_id)
    assert located is not None and located[1].state is TaskMissionState.DONE


def test_completion_winning_between_cancel_read_and_commit_is_preserved() -> None:
    service = _CompletionWinsBeforeCancelCommit()
    submitted = service.submit(
        owner=_owner(),
        task_id="task:terminal-race",
        job_id="job:terminal-race",
        logical_run_id="run:terminal-race",
        originating_product_session_ref=_ORIGIN,
    )
    assert is_ok(submitted), submitted
    assert is_ok(service.start(submitted.value.job_id))

    raced = _cancel(
        service,
        _payload(
            submitted.value.job_id,
            logical_run_id=submitted.value.logical_run_id,
            attempt_id=submitted.value.attempt_id,
        ),
    )
    assert is_ok(raced), raced
    assert raced.value.state is JobHandleState.DONE
    assert len(raced.value.later_commands) == 1
    assert raced.value.later_commands[0]["noop"] is True
    assert raced.value.later_commands[0]["terminal_state"] == "done"


def test_restore_reports_origin_immutability_conflict_as_refusal() -> None:
    handle = JobHandle.try_create(
        job_id="job:restore-origin-conflict",
        owner=_owner(),
        state=JobHandleState.QUEUED,
        task_id="task:restore-origin-conflict",
        originating_product_session_ref=_ORIGIN,
    )
    assert is_ok(handle), handle
    payload = dict(handle.value.to_payload())
    conflicting_payload = dict(payload)
    conflicting_payload["originating_product_session_ref"] = "psess:other-origin"
    restored = JobHandleStore().restore([payload, conflicting_payload])
    assert is_refusal(restored)
