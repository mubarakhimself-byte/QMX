"""Deterministic graph recovery through the admitted request seam."""

import json
from collections.abc import Sequence
from typing import Any, cast

import pytest
from langchain_core.runnables import RunnableConfig
from qma.daemon.request_runtime.graph_storage import JournalCheckpointer
from qmf.core import is_ok
from test_request_runtime_tool_loop import Host
from test_request_runtime_tool_loop import host as host_fixture

host = host_fixture


def test_checkpoint_resume_does_not_repeat_observed_domain_operation(host: Host) -> None:
    runtime, _, provider, calls, _, submit, _ = host
    request_id = submit()

    class LostModel(Exception):
        code = "outcome_unknown"

    def lose_final(count: int) -> None:
        if count == 2:
            raise LostModel()

    provider.after = lose_final
    first = runtime.execute(request_id)
    assert is_ok(first) and first.value.status == "interrupted"
    assert calls == [{"run_fp1": "run-1"}]
    assert is_ok(runtime.retry_interrupted(request_id))
    provider.after = None
    resumed = runtime.execute(request_id)
    assert is_ok(resumed) and resumed.value.status == "completed"
    assert resumed.value.result is not None
    assert resumed.value.result.content == "Run-1: verified 7 observations"
    assert calls == [{"run_fp1": "run-1"}]
    assert json.loads(provider.requests[-1].prompt)["tool_observations"][0]["result"] == {
        "run_fp1": "run-1",
        "observations": 7,
    }


def test_effect_receipt_closes_checkpoint_crash_window(
    host: Host, monkeypatch: pytest.MonkeyPatch
) -> None:
    from langchain_core.messages import ToolMessage
    from qma.daemon.request_runtime.providers import ProviderError

    runtime, _, provider, calls, _, submit, _ = host
    original = JournalCheckpointer.put_writes
    crashed = False

    def lose_tool_checkpoint(
        self: JournalCheckpointer,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        nonlocal crashed
        if not crashed and any(
            channel == "messages"
            and isinstance(value, list)
            and any(isinstance(item, ToolMessage) for item in cast("list[Any]", value))
            for channel, value in writes
        ):
            crashed = True
            raise ProviderError("outcome_unknown", "simulated checkpoint write loss")
        return original(self, config, writes, task_id, task_path)

    monkeypatch.setattr(JournalCheckpointer, "put_writes", lose_tool_checkpoint)
    request_id = submit()
    first = runtime.execute(request_id)
    assert is_ok(first) and first.value.status == "interrupted", first
    assert crashed and len(calls) == 1
    assert is_ok(runtime.retry_interrupted(request_id))
    resumed = runtime.execute(request_id)
    assert is_ok(resumed) and resumed.value.status == "completed", resumed
    assert len(calls) == 1 and len(provider.requests) == 2


def test_native_agent_session_cannot_be_wrapped_as_chat_model(host: Host) -> None:
    from qma.daemon.request_runtime import ProviderCapabilities

    runtime, _, provider, calls, _, submit, _ = host
    provider.capabilities = ProviderCapabilities("native-worker", execution_kind="agent_session")
    result = runtime.execute(submit())
    assert is_ok(result) and result.value.error == "unsupported"
    assert provider.requests == [] and calls == []


def test_changed_tool_binding_cannot_resume_prior_checkpoint(host: Host) -> None:
    from dataclasses import replace

    from qma.daemon.request_runtime.providers import ProviderError

    runtime, loop, provider, calls, _, submit, binding = host
    provider.after = lambda count: (_ for _ in ()).throw(
        ProviderError("outcome_unknown", "lost first response")
    )
    request_id = submit()
    assert is_ok(runtime.execute(request_id))
    assert is_ok(runtime.retry_interrupted(request_id))
    loop.tools["analysis"] = replace(binding, argument_scope=(("run_fp1", "other"),))
    provider.after = None
    resumed = runtime.execute(request_id)
    assert is_ok(resumed) and resumed.value.error == "context_changed"
    assert len(provider.requests) == 1 and calls == []


def test_environment_tracing_is_disabled_inside_inference(
    host: Host, monkeypatch: pytest.MonkeyPatch
) -> None:
    from langsmith.client import Client
    from langsmith.run_helpers import get_tracing_context

    runtime, _, provider, _, _, submit, _ = host
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")

    def refuse_transport(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("unexpected LangSmith transport")

    monkeypatch.setattr(Client, "request_with_retries", refuse_transport)

    def verify_context(count: int) -> None:
        assert get_tracing_context()["enabled"] is False

    provider.after = verify_context
    outcome = runtime.execute(submit())
    assert is_ok(outcome) and outcome.value.status == "completed"
