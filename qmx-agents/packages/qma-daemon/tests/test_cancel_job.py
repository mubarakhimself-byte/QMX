"""Epic 73 — originating-session JobHandle cancellation and replay."""

from __future__ import annotations

from qma.core.ontology import ActorId, DeskSlug
from qma.core.vocabulary.enums import JobHandleState
from qma.daemon.envs.jobs import JobHandleService
from qmf.core import is_ok, is_refusal

_PRINCIPAL = "principal:local-operator"
_ORIGIN = "psess:home-origin"


def _owner() -> ActorId:
    result = ActorId.mint(DeskSlug.RESEARCH, "epic73")
    assert is_ok(result)
    return result.value


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
    assert recorded["producer_id"] == "tab:one"
    assert recorded["wire_id"] == 71
    assert recorded["expected_state"] == "running"
    duplicate = _cancel(service, _payload(job_id, expected_state="running"), wire_id=71)
    assert is_ok(duplicate)
    assert len(duplicate.value.later_commands) == 1

    changed_pair = _cancel(service, _payload(job_id), wire_id=72)
    assert is_refusal(changed_pair)


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
