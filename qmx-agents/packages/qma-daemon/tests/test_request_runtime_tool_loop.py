"""Real session/grant dispatch evidence for the bounded SDK-owned tool loop."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Generator, Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Protocol

import pytest
from qma.daemon import ProductSessionService
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
from qma.daemon.request_runtime.tool_loop import (
    LoopLimits,
    ToolBinding,
    ToolLoopProvider,
    configured_loop_id,
)
from qmf.core import Ok, Result, is_ok, is_refusal
from test_product_session_grants import (
    _grant_kwargs,  # pyright: ignore[reportPrivateUsage] - shared authority fixture
    _mint_kwargs,  # pyright: ignore[reportPrivateUsage] - shared authority fixture
    _open,  # pyright: ignore[reportPrivateUsage] - shared authority fixture
    _stores,  # pyright: ignore[reportPrivateUsage] - shared authority fixture
)

TOOL = json.dumps({"type": "tool", "tool": "analysis", "arguments": {"run_fp1": "run-1"}})
FINAL = json.dumps({"type": "final", "content": "Run-1: verified 7 observations"})


class ScriptedText:
    capabilities = ProviderCapabilities("text-fixture")

    def __init__(self, responses: Sequence[str]) -> None:
        self.responses = list(responses)
        self.requests: list[ProviderRequest] = []
        self.after: Callable[[int], None] | None = None

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        self.requests.append(request)
        if self.after:
            self.after(len(self.requests))
        return ProviderResult(
            self.responses.pop(0),
            thread_id="discarded-native-thread",
            turn_id=f"turn-{len(self.requests)}",
            deployment_id="fixture",
        )


class Submit(Protocol):
    def __call__(self, profile: str = "reader", key: str = "one") -> str: ...


Host = tuple[
    RequestRuntime,
    ToolLoopProvider,
    ScriptedText,
    list[dict[str, object]],
    ProductSessionService,
    Submit,
    ToolBinding,
]


def _execute(runtime: RequestRuntime, request_id: str) -> Ok[RequestRecord]:
    result = runtime.execute(request_id)
    assert is_ok(result), result
    return result


def _cancel(runtime: RequestRuntime, request_id: str) -> Ok[RequestRecord]:
    result = runtime.cancel(request_id)
    assert is_ok(result), result
    return result


def _get(runtime: RequestRuntime, request_id: str) -> Ok[RequestRecord]:
    result = runtime.get(request_id)
    assert is_ok(result), result
    return result


@pytest.fixture
def host(tmp_path: Path) -> Generator[Host]:
    substrate, journal = _open(tmp_path)
    sessions = ProductSessionService(journal=journal, sqlite=substrate.sqlite)
    assert is_ok(sessions.mint(**_mint_kwargs()))
    assert is_ok(sessions.host_grant("psess:desk-1", **_grant_kwargs()))
    contributions, descriptors, instances = _stores()
    descriptor = descriptors[("qmb.analysis.project", 1)]
    calls: list[dict[str, object]] = []

    def callback(arguments: Mapping[str, object]) -> Mapping[str, object]:
        calls.append(dict(arguments))
        return {"run_fp1": arguments["run_fp1"], "observations": 7}

    binding = ToolBinding(
        descriptor,
        next(iter(contributions.values())),
        next(iter(instances.values())),
        "grant:1",
        callback,
    )
    provider = ScriptedText([TOOL, FINAL])
    loop = ToolLoopProvider(
        provider,
        provider_id="loop",
        tools={"analysis": binding},
        profile_tools={"reader": frozenset({"analysis"}), "summary-only": frozenset()},
        now=lambda: "2026-10-03T00:00:00Z",
    )
    runtime = RequestRuntime(journal=journal, product_sessions=sessions, providers={"loop": loop})
    loop.bind_runtime(runtime)

    def submit(profile: str = "reader", key: str = "one") -> str:
        loaded = sessions.get("psess:desk-1")
        assert is_ok(loaded), loaded
        session = loaded.value
        spec = RequestSpec(
            key,
            "operator",
            "psess:desk-1",
            session.context_revision,
            CopilotProfile(profile),
            "Explain run-1",
            "loop",
        )
        result = runtime.submit(spec)
        assert is_ok(result), result
        return result.value.request_id

    try:
        yield runtime, loop, provider, calls, sessions, submit, binding
    finally:
        journal.close()
        substrate.close()


def test_real_granted_callback_then_final_turn(host: Host) -> None:
    runtime, _loop, provider, calls, _sessions, submit, _ = host
    result = _execute(runtime, submit())
    assert is_ok(result), result
    assert result.value.status == "completed", result
    assert result.value.result is not None
    assert result.value.result.content == "Run-1: verified 7 observations"
    assert calls == [{"run_fp1": "run-1"}]
    assert len(provider.requests) == 2
    second = json.loads(provider.requests[1].prompt)
    assert second["tool_observations"][0]["result"]["observations"] == 7
    assert all(request.thread_id is None for request in provider.requests)
    assert result.value.result.thread_id is None
    # Terminal execution is idempotent: it never reruns model or callback.
    assert _execute(runtime, result.value.request_id).value == result.value
    assert len(provider.requests) == 2 and len(calls) == 1


def test_same_session_narrower_host_profile_refuses_granted_tool(host: Host) -> None:
    runtime, _, provider, calls, _, submit, _ = host
    result = _execute(runtime, submit("summary-only"))
    assert result.value.status == "failed"
    assert result.value.error == "tool_denied"
    assert len(provider.requests) == 1
    assert calls == []


def test_parameter_ceiling_denies_before_callback(host: Host) -> None:
    runtime, _, provider, calls, _, submit, _ = host
    provider.responses[0] = json.dumps(
        {"type": "tool", "tool": "analysis", "arguments": {"run_fp1": "run-1", "edit_code": True}}
    )
    result = _execute(runtime, submit())
    assert result.value.error == "tool_denied"
    assert calls == [] and len(provider.requests) == 1


def test_model_cannot_override_target_grant_or_envelope(host: Host) -> None:
    runtime, _, provider, calls, _, submit, _ = host
    provider.responses[0] = json.dumps(
        {
            "type": "tool",
            "tool": "analysis",
            "arguments": {"run_fp1": "run-1"},
            "grant_id": "grant:any",
            "instance_id": "inst:other",
        }
    )
    result = _execute(runtime, submit())
    assert result.value.error == "invalid_action"
    assert calls == [] and len(provider.requests) == 1


def test_revoked_grant_during_model_call_denies_callback(host: Host) -> None:
    runtime, _, provider, calls, sessions, submit, _ = host
    request_id = submit()

    def revoke(_: int) -> None:
        revoked = sessions.revoke_grant(
            "psess:desk-1",
            grant_id="grant:1",
            principal="operator",
            reason="test",
            revoked_at="2026-10-03T00:00:00Z",
        )
        assert is_ok(revoked), revoked

    provider.after = revoke
    result = _execute(runtime, request_id)
    assert result.value.error == "tool_denied"
    assert calls == []


def test_model_and_tool_limits_prevent_extra_effect(host: Host) -> None:
    runtime, loop, provider, calls, _, submit, _ = host
    loop.limits = LoopLimits(max_model_calls=2, max_tool_calls=1)
    provider.responses[:] = [TOOL, TOOL]
    result = _execute(runtime, submit())
    assert result.value.error == "loop_limit"
    assert len(provider.requests) == 2 and len(calls) == 1


def test_unknown_tool_outcome_never_retries_automatically(host: Host) -> None:
    runtime, loop, provider, calls, _, submit, binding = host

    def lost(arguments: Mapping[str, object]) -> Mapping[str, object]:
        calls.append(dict(arguments))
        raise RuntimeError("simulated lost callback outcome")

    loop.tools["analysis"] = replace(binding, execute=lost)
    request_id = submit()
    result = _execute(runtime, request_id)
    assert result.value.status == "interrupted", result
    assert result.value.error == "outcome_unknown"
    assert is_refusal(runtime.execute(request_id))
    assert len(calls) == 1 and len(provider.requests) == 1


def test_cancel_after_model_before_tool_does_not_execute_callback(host: Host) -> None:
    runtime, _, provider, calls, _, submit, _ = host
    request_id = submit()

    def cancel_after(_: int) -> None:
        runtime.cancel(request_id)

    provider.after = cancel_after
    result = _execute(runtime, request_id)
    assert result.value.status == "cancelled"
    assert calls == [] and len(provider.requests) == 1


@pytest.mark.parametrize(
    "response",
    [
        '{"type":"final","type":"tool","content":"x"}',
        '{"type":"tool","tool":"analysis","arguments":{"run_fp1":NaN}}',
        '{"type":"tool","tool":"analysis","arguments":{"run_fp1":1e999}}',
        '```json\n{"type":"final","content":"x"}\n```',
    ],
)
def test_strict_parser_refuses_ambiguous_or_non_json_actions(host: Host, response: str) -> None:
    runtime, _, provider, calls, _, submit, _ = host
    provider.responses[0] = response
    result = _execute(runtime, submit())
    assert result.value.error == "invalid_action"
    assert calls == []


def test_explicit_retry_after_unknown_model_starts_fresh_tool_invocation(host: Host) -> None:
    runtime, _, provider, calls, _, submit, _ = host
    request_id = submit()

    class LostModel(Exception):
        code = "outcome_unknown"

    def lost_once(count: int) -> None:
        if count == 1:
            raise LostModel()

    provider.after = lost_once
    first = _execute(runtime, request_id)
    assert first.value.status == "interrupted"
    assert calls == []
    assert is_ok(runtime.retry_interrupted(request_id))
    result = _execute(runtime, request_id)
    assert result.value.status == "completed", result
    assert result.value.attempt == 2
    assert calls == [{"run_fp1": "run-1"}]
    assert len(provider.requests) == 3


def test_cancel_while_accepted_read_runs_is_responsive_and_stops_next_model(host: Host) -> None:
    runtime, loop, provider, calls, _, submit, binding = host
    started, release = threading.Event(), threading.Event()

    def slow(arguments: Mapping[str, object]) -> Mapping[str, object]:
        calls.append(dict(arguments))
        started.set()
        assert release.wait(5), "test failed to release admitted callback"
        return {"observations": 7}

    loop.tools["analysis"] = replace(binding, execute=slow)
    request_id = submit()
    outcomes: list[Result[RequestRecord]] = []
    worker = threading.Thread(target=lambda: outcomes.append(runtime.execute(request_id)))
    worker.start()
    assert started.wait(5)
    try:
        # Accepted reads finish cooperatively; cancel does not undo that read.
        assert _cancel(runtime, request_id).value.status == "cancellation_requested"
        assert _get(runtime, request_id).value.status == "cancellation_requested"
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive()
    assert is_ok(outcomes[0]), outcomes[0]
    assert outcomes[0].value.status == "cancelled"
    assert len(calls) == 1 and len(provider.requests) == 1


def test_unknown_after_cancellation_remains_interrupted(host: Host) -> None:
    runtime, loop, provider, calls, _, submit, binding = host
    request_id = submit()

    def failed_read(arguments: Mapping[str, object]) -> Mapping[str, object]:
        calls.append(dict(arguments))
        assert _cancel(runtime, request_id).value.status == "cancellation_requested"
        raise RuntimeError("read outcome lost after cancellation")

    loop.tools["analysis"] = replace(binding, execute=failed_read)
    result = _execute(runtime, request_id)
    assert result.value.status == "interrupted"
    assert result.value.error == "outcome_unknown"
    assert calls and len(provider.requests) == 1


def test_provider_config_identity_change_cannot_replay_diagnostic_as_native(host: Host) -> None:
    runtime, loop, provider, calls, sessions, submit, binding = host
    request_id = submit()
    assert _execute(runtime, request_id).value.status == "completed"
    original = _get(runtime, request_id).value
    fake_native = ScriptedText([TOOL, FINAL])
    fake_native.capabilities = ProviderCapabilities("fake-native-text")
    native_id = configured_loop_id(fake_native, {"home": "isolated-fixture", "version": "1"})
    other_home_id = configured_loop_id(
        fake_native, {"home": "other-isolated-fixture", "version": "1"}
    )
    diagnostic_id = configured_loop_id(provider, {"version": "1"})
    assert native_id not in {diagnostic_id, other_home_id}
    # Same sole-writer journal/root; a new host registry selection must preserve
    # the accepted key's provider identity rather than present cached output as live.
    alternate = ToolLoopProvider(
        fake_native,
        provider_id=native_id,
        tools={"analysis": binding},
        profile_tools={"reader": frozenset({"analysis"})},
        now=loop.now,
    )
    restored = RequestRuntime(
        journal=runtime.journal, product_sessions=sessions, providers={native_id: alternate}
    )
    alternate.bind_runtime(restored)
    conflict = restored.submit(replace(original.spec, provider_id=native_id))
    assert is_refusal(conflict)
    assert _get(restored, request_id).value.result == original.result
    assert fake_native.requests == []
    assert len(calls) == 1


def test_scope_narrowing_during_accepted_read_prevents_next_disclosure(host: Host) -> None:
    runtime, loop, provider, calls, sessions, submit, binding = host
    request_id = submit()

    def narrow(arguments: Mapping[str, object]) -> Mapping[str, object]:
        calls.append(dict(arguments))
        current = sessions.get("psess:desk-1")
        assert is_ok(current)
        # Fault injection of host context narrowing, not a model-accessible API.
        sessions._index(replace(current.value, context_revision=current.value.context_revision + 1))  # pyright: ignore[reportPrivateUsage]
        return {"restricted_observations": "must not reach another provider call"}

    loop.tools["analysis"] = replace(binding, execute=narrow)
    result = _execute(runtime, request_id)
    assert result.value.status == "failed"
    assert result.value.error == "context_changed"
    assert len(calls) == 1 and len(provider.requests) == 1


def test_grant_revocation_during_accepted_read_prevents_next_disclosure(host: Host) -> None:
    runtime, loop, provider, calls, sessions, submit, binding = host
    request_id = submit()

    def revoke(arguments: Mapping[str, object]) -> Mapping[str, object]:
        calls.append(dict(arguments))
        revoked = sessions.revoke_grant(
            "psess:desk-1",
            grant_id="grant:1",
            principal="operator",
            reason="narrow authority",
            revoked_at="2026-10-03T00:00:00Z",
        )
        assert is_ok(revoked), revoked
        return {"restricted_observations": "must not reach another provider call"}

    loop.tools["analysis"] = replace(binding, execute=revoke)
    result = _execute(runtime, request_id)
    assert result.value.status == "failed"
    assert result.value.error == "context_changed"
    assert len(calls) == 1 and len(provider.requests) == 1


def test_grant_expiry_after_accepted_read_prevents_next_disclosure(host: Host) -> None:
    runtime, loop, provider, calls, _, submit, binding = host
    request_id = submit()

    def expire(arguments: Mapping[str, object]) -> Mapping[str, object]:
        calls.append(dict(arguments))
        loop.now = lambda: "2027-01-01T00:00:00Z"
        return {"restricted_observations": "must not reach another provider call"}

    loop.tools["analysis"] = replace(binding, execute=expire)
    result = _execute(runtime, request_id)
    assert result.value.status == "failed"
    assert result.value.error == "context_changed"
    assert len(calls) == 1 and len(provider.requests) == 1
