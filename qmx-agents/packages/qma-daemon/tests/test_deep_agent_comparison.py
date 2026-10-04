"""Offline full-factory comparison using actual QMA grants, journal and SDK."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import test_agent_extensions as extension_contract
import test_request_runtime_tool_loop as loop_contract
from qma.daemon.request_runtime.deep_agent import DeepAgentSelection
from qma.daemon.request_runtime.graph_storage import JournalRecords
from qma.daemon.request_runtime.providers import ProviderError
from qma.daemon.request_runtime.tool_loop import LoopLimits, ToolLoopProvider
from qmf.core import is_ok
from test_agent_extensions import BODY, PATH, READ, library
from test_request_runtime_tool_loop import FINAL, TOOL
from test_request_runtime_tool_loop import host as host_fixture

host = host_fixture
provision_clock = extension_contract.provision_clock


@pytest.fixture(params=["langchain", "deepagents"])
def comparison(host: Any, request: Any) -> Any:
    runtime, original, provider, calls, sessions, submit, binding = host
    loop = ToolLoopProvider(
        provider,
        provider_id="loop",
        tools=original.tools,
        profile_tools=original.profile_tools,
        now=original.now,
        deep_agent=DeepAgentSelection("reader", "request")
        if request.param == "deepagents"
        else None,
    )
    loop.bind_runtime(runtime)
    runtime.providers["loop"] = loop
    return runtime, loop, provider, calls, sessions, submit, binding


def run(host: Any) -> Any:
    runtime, _, _, _, _, submit, _ = host
    result = runtime.execute(submit())
    assert is_ok(result), result
    return result.value


def record(journal: Any, kind: str, key: str) -> dict[str, Any]:
    value = JournalRecords(journal).get(kind, key)
    assert value is not None
    return value


def test_same_specialist_skill_then_admitted_read(comparison: Any, tmp_path: Path) -> None:
    runtime, loop, provider, calls, _, _, _ = comparison
    loop.extensions = library(tmp_path)
    provider.responses[:] = [READ, TOOL, FINAL]
    result = run(comparison)
    assert result.status == "completed", result
    assert calls == [{"run_fp1": "run-1"}] and len(provider.requests) == 3
    assert BODY not in provider.requests[0].instructions + provider.requests[0].prompt
    assert BODY in provider.requests[1].prompt
    for request in provider.requests:
        schema = request.instructions.split("Bound SDK tool schemas: ", 1)[1]
        assert {item["name"] for item in json.loads(schema)} == {"analysis", "read_file"}
    binding = record(runtime.journal, "agent_binding", result.request_id)
    assert binding["extensions"]["files"][PATH]
    if loop.deep_agent:
        assert binding["harness"]["sdk_versions"]["deepagents"] == "0.7.21"
        assert record(runtime.journal, "deep_agent_budget", result.request_id) == {
            "models": 3,
            "summaries": 0,
            "tool_ids": ["call-1", "call-2"],
        }
    assert (
        record(runtime.journal, "effect", result.request_id + ":graph:call-2")["status"]
        == "observed"
    )


@pytest.mark.parametrize(
    "name,args",
    [
        ("task", {"description": "spawn", "subagent_type": "general-purpose"}),
        ("execute", {"command": "echo forbidden"}),
        ("write_file", {"file_path": PATH, "content": "replace"}),
        ("edit_file", {"file_path": PATH, "old_string": "x", "new_string": "y"}),
        ("ls", {"path": "/"}),
        ("read_file", {"file_path": "C:/Users/Mubarak/.codex/config.toml"}),
        ("read_file", {"file_path": "/skills/local/analysis/../private/SKILL.md"}),
        ("read_file", {"file_path": PATH, "offset": True}),
    ],
)
def test_builtins_and_filesystem_refuse_before_effect(
    comparison: Any, tmp_path: Path, name: str, args: dict[str, Any]
) -> None:
    _, loop, provider, calls, _, _, _ = comparison
    loop.extensions = library(tmp_path)
    provider.responses[:] = [json.dumps({"type": "tool", "tool": name, "arguments": args})]
    result = run(comparison)
    assert result.error == "tool_denied", result
    assert calls == [] and len(provider.requests) == 1


def test_total_iteration_budget(comparison: Any) -> None:
    _, loop, provider, calls, _, _, _ = comparison
    loop.limits = LoopLimits(max_model_calls=2, max_tool_calls=1)
    provider.responses[:] = [TOOL, TOOL]
    assert run(comparison).error == "loop_limit"
    assert len(provider.requests) == 2 and len(calls) == 1


def test_cancellation_and_unknown_receipts(comparison: Any) -> None:
    loop_contract.test_cancel_while_accepted_read_runs_is_responsive_and_stops_next_model(
        comparison
    )


def test_unknown_effect_requires_reconciliation(comparison: Any) -> None:
    loop_contract.test_unknown_tool_outcome_never_retries_automatically(comparison)


def test_unknown_effect_after_cancel(comparison: Any) -> None:
    loop_contract.test_unknown_after_cancellation_remains_interrupted(comparison)


def test_host_pair_selection_preserves_langchain(comparison: Any) -> None:
    runtime, loop, provider, _, _, submit, _ = comparison
    loop.deep_agent = DeepAgentSelection("reader", "another-role:1")
    provider.responses[:] = [FINAL]
    result = runtime.execute(submit()).value
    assert result.status == "completed"
    assert "harness" not in record(runtime.journal, "agent_binding", result.request_id)


def test_candidate_summary_counts_against_total(comparison: Any) -> None:
    runtime, loop, provider, calls, _, _, _ = comparison
    if not loop.deep_agent:
        pytest.skip("baseline has no automatic summarization")
    loop.deep_agent = replace(loop.deep_agent, summary_trigger_tokens=1)
    loop.limits = LoopLimits(max_model_calls=3, max_tool_calls=2)
    provider.responses[:] = [
        TOOL,
        json.dumps({"type": "final", "content": "Run-1 already read"}),
        FINAL,
    ]
    result = run(comparison)
    assert result.status == "completed", result
    state = record(runtime.journal, "deep_agent_budget", result.request_id)
    assert state["models"] == 3 and state["summaries"] == 1
    assert len(provider.requests) == 3 and len(calls) == 1
    assert "Run-1 already read" in provider.requests[2].prompt


def test_summary_cannot_spend_final_turn(comparison: Any) -> None:
    _, loop, provider, calls, _, _, _ = comparison
    if not loop.deep_agent:
        pytest.skip("baseline has no automatic summarization")
    loop.deep_agent = replace(loop.deep_agent, summary_trigger_tokens=1)
    loop.limits = LoopLimits(max_model_calls=2, max_tool_calls=2)
    provider.responses[:] = [TOOL, FINAL]
    result = run(comparison)
    assert result.error == "loop_limit", result
    assert len(provider.requests) == 2 and len(calls) == 1


def test_uncertain_summary_is_not_retried_automatically(comparison: Any) -> None:
    runtime, loop, provider, calls, _, _, _ = comparison
    if not loop.deep_agent:
        pytest.skip("baseline has no automatic summarization")
    loop.deep_agent = replace(loop.deep_agent, summary_trigger_tokens=1)

    def lose_summary(count: int) -> None:
        if count == 2:
            raise ProviderError("outcome_unknown", "fixture summary outcome unknown")

    provider.after = lose_summary
    result = run(comparison)
    assert result.status == "interrupted" and result.error == "outcome_unknown"
    assert len(provider.requests) == 2 and len(calls) == 1
    state = record(runtime.journal, "deep_agent_budget", result.request_id)
    assert state["models"] == 2 and state["summaries"] == 1


def test_skill_snapshot_change_refuses_resume(comparison: Any, tmp_path: Path) -> None:
    extension_contract.test_changed_snapshot_refuses_checkpoint_resume(comparison, tmp_path)


@pytest.mark.parametrize("capability", ["native_tools", "resume", "agent_session"])
def test_native_harness_ownership_refuses_before_launch(comparison: Any, capability: str) -> None:
    _, _, provider, calls, _, _, _ = comparison
    flags = (
        {"execution_kind": "agent_session"} if capability == "agent_session" else {capability: True}
    )
    provider.capabilities = replace(provider.capabilities, **flags)
    assert run(comparison).error == "unsupported"
    assert provider.requests == [] and calls == []


def test_receipt_replay_with_fresh_runtime(
    comparison: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qma.daemon.request_runtime import RequestRuntime
    from qma.daemon.request_runtime.graph_storage import JournalCheckpointer
    from qmf.core import is_refusal

    runtime, loop, provider, calls, sessions, submit, _ = comparison
    request_id = submit()
    original = JournalCheckpointer.put_writes
    lost = False

    def fault(self: Any, *args: Any, **kwargs: Any) -> None:
        nonlocal lost
        receipt = JournalRecords(runtime.journal).get("effect", request_id + ":graph:call-1")
        if not lost and receipt and receipt["status"] == "observed":
            lost = True
            raise ProviderError("outcome_unknown", "fault after receipt before checkpoint")
        original(self, *args, **kwargs)

    monkeypatch.setattr(JournalCheckpointer, "put_writes", fault)
    interrupted = runtime.execute(request_id).value
    assert interrupted.status == "interrupted" and lost and len(calls) == 1
    journal = runtime.journal
    successor = ToolLoopProvider(
        provider,
        provider_id="loop",
        tools=loop.tools,
        profile_tools=loop.profile_tools,
        now=loop.now,
        deep_agent=loop.deep_agent,
    )
    restored = RequestRuntime(
        journal=journal, product_sessions=sessions, providers={"loop": successor}
    )
    successor.bind_runtime(restored)
    assert is_refusal(restored.execute(request_id))
    assert is_ok(restored.retry_interrupted(request_id))
    result = restored.execute(request_id)
    assert is_ok(result), result
    completed = result.value
    assert completed.status == "completed", completed
    assert len(calls) == 1 and len(provider.requests) == 2
    effect = record(journal, "effect", request_id + ":graph:call-1")
    assert effect["status"] == "observed"
    if successor.deep_agent:
        assert record(journal, "deep_agent_budget", request_id)["models"] == 2
