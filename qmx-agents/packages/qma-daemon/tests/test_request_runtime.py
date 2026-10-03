"""Provider-free behavioral proof for request durability and authority boundaries."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from qma.daemon import AuthoritativeJournal, PersistenceSubstrate, ProductSessionService
from qma.daemon.request_runtime import (
    CopilotProfile,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    RequestRecord,
    RequestRuntime,
    RequestSpec,
)
from qmf.core import DataDrivenClock, Instant, Result, is_ok, is_refusal

Setup = tuple[RequestRuntime, "FakeProvider", AuthoritativeJournal]


def value[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


class FakeProvider:
    def __init__(self, *, resume: bool = False, native_tools: bool = False) -> None:
        self.capabilities = ProviderCapabilities("fake", resume=resume, native_tools=native_tools)
        self.requests: list[ProviderRequest] = []
        self.started = threading.Event()
        self.release = threading.Event()
        self.block = False
        self.failure: Exception | None = None

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        self.requests.append(request)
        self.started.set()
        emit(ProviderEvent("message", {"text": "observational"}))
        if self.block:
            assert self.release.wait(5), "test did not release provider"
        if self.failure:
            raise self.failure
        return ProviderResult("answer:" + request.prompt, "thread-1", "turn-1")


def open_runtime(
    path: Path,
    *,
    provider: FakeProvider | None = None,
    boot: str = "boot-requests",
    restore_sessions: bool = False,
) -> tuple[PersistenceSubstrate, AuthoritativeJournal, RequestRuntime, FakeProvider]:
    opened = PersistenceSubstrate.open(path, machine="test-host", boot_epoch_id=boot)
    assert is_ok(opened), opened
    walls = tuple(Instant(value_ns=1_727_000_000_000_000_000 + i) for i in range(200))
    clock = DataDrivenClock(boot_epoch_id=boot, wall_instants=walls, monotonic_ns=tuple(range(200)))
    journal_result = AuthoritativeJournal.bind(opened.value, clock=clock)
    assert is_ok(journal_result), journal_result
    journal = journal_result.value
    sessions = ProductSessionService(journal=journal, sqlite=opened.value.sqlite)
    if restore_sessions:
        assert is_ok(sessions.restore_from_journal())
    else:
        minted = sessions.mint(
            product_session_id="psess:requests",
            profile="authoring",
            principal="operator",
            contribution={"package_version": "0.1.0", "qualified_id": "assistant:sdk"},
            instance_id="inst:app",
            config_revision=0,
            as_of="2026-10-03T00:00:00Z",
        )
        assert is_ok(minted), minted
    provider = provider or FakeProvider()
    runtime = RequestRuntime(
        journal=journal, product_sessions=sessions, providers={"fake": provider}
    )
    return opened.value, journal, runtime, provider


@pytest.fixture
def setup(tmp_path: Path) -> Iterator[Setup]:
    substrate, journal, runtime, provider = open_runtime(tmp_path)
    try:
        yield runtime, provider, journal
    finally:
        journal.close()
        substrate.close()


def spec(**kwargs: object) -> RequestSpec:
    row = RequestSpec(
        "key-1", "operator", "psess:requests", 0, CopilotProfile("global-default"), "hello", "fake"
    )
    return replace(row, **kwargs)


def accepted(runtime: RequestRuntime, **kwargs: object) -> RequestRecord:
    result = runtime.submit(spec(**kwargs))
    assert is_ok(result), result
    return result.value


def test_accept_execute_idempotent_and_observers_cannot_change_result(setup: Setup) -> None:
    runtime, provider, journal = setup
    row = accepted(runtime)
    assert row.status == "queued"

    def bad_observer(event: ProviderEvent) -> None:
        raise RuntimeError("UI disconnected")

    result = runtime.execute(row.request_id, observe=bad_observer)
    assert is_ok(result), result
    assert result.value.status == "completed"
    assert result.value.result is not None
    assert result.value.result.content == "answer:hello"
    assert value(runtime.submit(spec())) == result.value
    assert value(runtime.execute(row.request_id)) == result.value
    assert len(provider.requests) == 1
    events = value(journal.read_events())
    assert [event.event for event in events] == ["product_session.minted"] + [
        "agent_request.snapshot"
    ] * 3
    assert is_refusal(runtime.submit(spec(prompt="changed")))


def test_context_and_profile_fail_before_provider(setup: Setup) -> None:
    runtime, provider, _ = setup
    assert is_refusal(runtime.submit(spec(principal="attacker")))
    assert is_refusal(runtime.submit(spec(context_revision=1)))
    wrong = CopilotProfile("page-agent", "page", app_instance_id="inst:other", page_id="page-1")
    assert is_refusal(runtime.submit(spec(profile=wrong)))
    assert provider.requests == []
    with pytest.raises(ValueError):
        CopilotProfile("page-agent", "page")


def test_unversioned_context_retarget_after_acceptance_is_refused(setup: Setup) -> None:
    runtime, provider, _ = setup
    row = accepted(runtime)
    updated = runtime.product_sessions.mint(
        product_session_id="psess:requests",
        profile="authoring",
        principal="operator",
        contribution={"package_version": "0.1.0", "qualified_id": "assistant:sdk"},
        instance_id="inst:app",
        config_revision=1,
        context_revision=0,
        as_of="2026-10-03T00:00:00Z",
    )
    assert is_ok(updated), updated
    assert is_refusal(runtime.execute(row.request_id))
    assert provider.requests == []


def test_fractional_timeout_survives_restart_and_idempotency(tmp_path: Path) -> None:
    substrate, journal, runtime, _ = open_runtime(tmp_path)
    try:
        row = accepted(runtime, timeout_seconds=0.125)
    finally:
        journal.close()
        substrate.close()
    substrate2, journal2, restored, provider2 = open_runtime(
        tmp_path, boot="fractional-restart", restore_sessions=True
    )
    try:
        same = value(restored.submit(spec(timeout_seconds=0.125)))
        assert same.request_id == row.request_id
        assert is_ok(restored.execute(same.request_id))
        assert provider2.requests[0].timeout_seconds == 0.125
    finally:
        journal2.close()
        substrate2.close()


def test_profiles_start_fresh_even_when_provider_advertises_resume(setup: Setup) -> None:
    runtime, provider, _ = setup
    provider.capabilities = ProviderCapabilities("fake", resume=True)
    global_row = accepted(runtime)
    assert is_ok(runtime.execute(global_row.request_id))
    app = CopilotProfile("app-agent", "application", app_instance_id="inst:app")
    app_row = accepted(runtime, idempotency_key="key-2", profile=app)
    assert is_ok(runtime.execute(app_row.request_id))
    page = CopilotProfile("page-agent", "page", app_instance_id="inst:app", page_id="p1")
    page_row = accepted(runtime, idempotency_key="key-3", profile=page)
    assert is_ok(runtime.execute(page_row.request_id))
    global_again = accepted(runtime, idempotency_key="key-4")
    assert is_ok(runtime.execute(global_again.request_id))
    assert [r.thread_id for r in provider.requests] == [None, None, None, None]


def test_queued_cancellation_never_calls_provider(setup: Setup) -> None:
    runtime, provider, _ = setup
    row = accepted(runtime)
    assert value(runtime.cancel(row.request_id)).status == "cancelled"
    assert value(runtime.execute(row.request_id)).status == "cancelled"
    assert provider.requests == []


def test_running_cancellation_intent_does_not_erase_observed_completion(setup: Setup) -> None:
    runtime, provider, _ = setup
    provider.block = True
    row = accepted(runtime)
    outcomes: list[Result[RequestRecord]] = []
    thread = threading.Thread(target=lambda: outcomes.append(runtime.execute(row.request_id)))
    thread.start()
    assert provider.started.wait(5)
    try:
        assert is_refusal(runtime.execute(row.request_id))
        assert value(runtime.get(row.request_id)).status == "running"
        assert value(runtime.cancel(row.request_id)).status == "cancellation_requested"
    finally:
        provider.release.set()
        thread.join(5)
    assert not thread.is_alive()
    assert value(outcomes[0]).status == "completed"
    assert value(outcomes[0]).result is not None


def test_continuation_admission_requires_active_uncancelled_owner(setup: Setup) -> None:
    runtime, provider, _ = setup
    provider.block = True
    row = accepted(runtime)
    assert is_refusal(runtime.validate_active_request(row.request_id))
    thread = threading.Thread(target=lambda: runtime.execute(row.request_id))
    thread.start()
    assert provider.started.wait(5)
    try:
        assert is_ok(runtime.validate_active_request(row.request_id))
        assert is_ok(runtime.cancel(row.request_id))
        assert is_refusal(runtime.validate_active_request(row.request_id))
    finally:
        provider.release.set()
        thread.join(5)
    assert not thread.is_alive()
    assert is_refusal(runtime.validate_active_request(row.request_id))


def test_continuation_admission_refuses_unversioned_context_change(setup: Setup) -> None:
    runtime, provider, _ = setup
    provider.block = True
    row = accepted(runtime)
    thread = threading.Thread(target=lambda: runtime.execute(row.request_id))
    thread.start()
    assert provider.started.wait(5)
    try:
        assert is_ok(runtime.validate_active_request(row.request_id))
        updated = runtime.product_sessions.mint(
            product_session_id="psess:requests",
            profile="authoring",
            principal="operator",
            contribution={"package_version": "0.1.0", "qualified_id": "assistant:sdk"},
            instance_id="inst:app",
            config_revision=1,
            context_revision=0,
            as_of="2026-10-03T00:00:00Z",
        )
        assert is_ok(updated), updated
        assert is_refusal(runtime.validate_active_request(row.request_id))
    finally:
        provider.release.set()
        thread.join(5)
    assert not thread.is_alive()


def test_provider_acknowledged_cancellation_is_terminal(setup: Setup) -> None:
    runtime, provider, _ = setup

    class Cancelled(Exception):
        code = "cancelled"

    provider.failure = Cancelled()
    row = accepted(runtime)
    result = value(runtime.execute(row.request_id))
    assert result.status == "cancelled"
    assert result.result is None


def test_no_fallback_or_native_tool_bypass(setup: Setup) -> None:
    runtime, provider, _ = setup
    row = accepted(runtime, provider_id="unconfigured")
    assert is_refusal(runtime.execute(row.request_id))
    assert value(runtime.get(row.request_id)).status == "queued"
    native = accepted(runtime, idempotency_key="key-2")
    provider.capabilities = ProviderCapabilities("fake", native_tools=True)
    assert is_refusal(runtime.execute(native.request_id))
    assert provider.requests == []


def test_restart_recovers_completed_and_never_replays_running(tmp_path: Path) -> None:
    substrate, journal, runtime, _ = open_runtime(tmp_path)
    try:
        row = accepted(runtime)
        completed = value(runtime.execute(row.request_id))
        interrupted = accepted(runtime, idempotency_key="key-2")
        # Durable state at the point where the process disappears during a provider call.
        # Fault injection at the durable crash boundary, not a public caller.
        assert is_ok(runtime._persist(replace(interrupted, status="running", attempt=1)))  # pyright: ignore[reportPrivateUsage]
    finally:
        journal.close()
        substrate.close()
    substrate2, journal2, restored, provider2 = open_runtime(
        tmp_path, boot="restart", restore_sessions=True
    )
    try:
        assert value(restored.get(row.request_id)).result == completed.result
        lost = value(restored.get(interrupted.request_id))
        assert lost.status == "interrupted"
        assert lost.error == "owner_lost"
        assert is_refusal(restored.execute(lost.request_id))
        assert provider2.requests == []
        assert value(restored.retry_interrupted(lost.request_id)).status == "queued"
        retried = value(restored.execute(lost.request_id))
        assert retried.status == "completed"
        assert retried.attempt == 2
        assert len(provider2.requests) == 1
    finally:
        journal2.close()
        substrate2.close()


def test_unknown_provider_outcome_requires_explicit_retry(setup: Setup) -> None:
    runtime, provider, _ = setup

    class LostConnection(Exception):
        code = "outcome_unknown"

    provider.failure = LostConnection("must not leak credentials or process output")
    row = accepted(runtime)
    result = value(runtime.execute(row.request_id))
    assert result.status == "interrupted"
    assert result.error == "outcome_unknown"
    assert is_refusal(runtime.execute(row.request_id))
    assert is_ok(runtime.retry_interrupted(row.request_id))


def test_tools_have_no_implicit_grants(setup: Setup) -> None:
    runtime, provider, _ = setup
    provider.block = True
    row = accepted(runtime)
    thread = threading.Thread(target=lambda: runtime.execute(row.request_id))
    thread.start()
    assert provider.started.wait(5)
    try:
        assert is_refusal(
            runtime.dispatch_tool(
                row.request_id,
                envelope={},
                transport="invoke",
                payload={},
                now="2026-10-03T00:00:00Z",
            )
        )
        assert is_refusal(runtime.dispatch_tool(row.request_id, product_session_id="psess:other"))
    finally:
        provider.release.set()
        thread.join(5)
    assert not thread.is_alive()


@pytest.mark.parametrize("duration", [0, -1, float("inf"), float("nan"), True])
def test_invalid_timeout_refused(setup: Setup, duration: float | bool) -> None:
    assert is_refusal(setup[0].submit(spec(timeout_seconds=duration)))
