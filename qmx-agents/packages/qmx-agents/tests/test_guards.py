from __future__ import annotations

import asyncio
import json
import sys
from hashlib import sha256
from itertools import repeat
from pathlib import Path
from typing import Any

import pytest
from conftest import BoundFakeChatModel, compiled, fake, fake_models
from deepagents.backends import FilesystemBackend, StateBackend
from langchain.agents.middleware.tool_call_limit import ToolCallLimitExceededError
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from qma.core.barriers.money_path import (
    MONEY_PATH_ACT_ALIASES,
    MONEY_PATH_DENIED_ACTS,
    MoneyPathDenyError,
)
from qma.core.barriers.parent_surfaces import is_parent_surface_permitted
from qmx_ledger.journal import RunJournal, fingerprint
from test_spec import call, write_spec

from qmx_agents.guards import (
    AdmissionBackend,
    AdmissionDenied,
    AdmissionGate,
    WriteProposal,
    check_tool,
    propose_order,
)
from qmx_agents.router import ModelRouter, RouterConfig
from qmx_agents.spec import Budget, BuildContext


@tool
def lookup() -> str:
    """Return deterministic evidence."""
    return "evidence"


def records(journal: RunJournal) -> list[dict[str, Any]]:
    return [json.loads(line) for line in journal.path.read_text().splitlines()]


@pytest.mark.parametrize(
    "name",
    ["submit_order", "paper_place_order", "broker_demo_close_position", "risk.set_book_mode"],
)
def test_money_tool_names_refused(tmp_path: Path, config: RouterConfig, name: str) -> None:
    danger = lookup.model_copy(update={"name": name})
    spec = write_spec(tmp_path, "tools: [danger]")
    with pytest.raises(MoneyPathDenyError):
        compiled(spec, BuildContext(ModelRouter(config), tools={"danger": danger}))


@pytest.mark.parametrize(
    "metadata",
    [
        {"money_path": True},
        {"acts": ["resize"]},
        {"mcp": {"tool_name": "cancel_order"}},
        {"mcp": {"money_path": True}},
        {"mcp": {"tool": {"_meta": {"money_path": True}}}},
        {"mcp": {"tool": {"annotations": {"acts": ["resize"]}}}},
        {"parent_library": "qmf-risk", "parent_surface": "write"},
        {"record_family": "binding"},
    ],
)
def test_money_metadata_cannot_be_overridden(
    tmp_path: Path, config: RouterConfig, metadata: dict[str, Any]
) -> None:
    danger = lookup.model_copy(update={"metadata": metadata})
    spec = write_spec(tmp_path, "tools: [danger]")
    with pytest.raises(MoneyPathDenyError):
        compiled(spec, BuildContext(ModelRouter(config), tools={"danger": danger}))


def test_existing_money_vocabulary_and_aliases_are_retained() -> None:
    for name in [*(act.value for act in MONEY_PATH_DENIED_ACTS), *MONEY_PATH_ACT_ALIASES]:
        with pytest.raises(MoneyPathDenyError):
            check_tool(lookup.model_copy(update={"name": "paper_" + name}))
    assert is_parent_surface_permitted("qmf-registry", "dev_zone_candidate_write")
    assert not is_parent_surface_permitted("qmf-risk", "dev_zone_candidate_write")
    assert not is_parent_surface_permitted("qmf-registry", "zone_transition")


@pytest.mark.parametrize(
    "name", ["create_order", "create-order", "Create Order", "CREATE-ORDER", "paper-place order"]
)
def test_spelled_money_names_are_refused(name: str) -> None:
    with pytest.raises(MoneyPathDenyError, match=f"Money-path act refused: {name}"):
        check_tool(lookup.model_copy(update={"name": name}))


def test_proposal_only_writes_unsigned_evidence(tmp_path: Path) -> None:
    with RunJournal(tmp_path / "run.jsonl", "proposal") as journal:
        proposal_tool = propose_order(journal)
        check_tool(proposal_tool)
        reference = proposal_tool.invoke(
            {"account": "demo", "symbol": "EURUSD", "side": "buy", "quantity": 1}
        )
        assert json.loads(Path(reference).read_text()) == {
            "account": "demo",
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": "1",
        }
        assert records(journal)[0]["payload"]["status"] == "unsigned"
        assert not hasattr(proposal_tool, "venue")
        with pytest.raises(ValueError):
            proposal_tool.invoke(
                {"account": "demo", "symbol": "EURUSD", "side": "buy", "quantity": "NaN"}
            )
        imposter = lookup.model_copy(
            update={"name": "propose_order", "metadata": {"money_path": True}}
        )
        with pytest.raises(MoneyPathDenyError):
            check_tool(imposter)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_journal_records_full_fake_run(
    tmp_path: Path, config: RouterConfig, asynchronous: bool
) -> None:
    model = fake(
        call("lookup"),
        AIMessage(
            content="done",
            usage_metadata={"input_tokens": 10, "output_tokens": 2, "total_tokens": 12},
        ),
    )
    with RunJournal(tmp_path / "journal/run.jsonl", "fake") as journal:
        ctx = BuildContext(
            ModelRouter(config, fake_models(model)), tools={"lookup": lookup}, journal=journal
        )
        graph = compiled(write_spec(tmp_path, "tools: [lookup]"), ctx)
        if asynchronous:
            result = asyncio.run(
                graph.ainvoke({"messages": [{"role": "user", "content": "Lookup"}]})
            )
        else:
            result = graph.invoke({"messages": [{"role": "user", "content": "Lookup"}]})
        assert result["messages"][-1].content == "done"
        rows = records(journal)
        events = [row["event"] for row in rows]
        assert events[0] == "run_start" and events[-1] == "run_end"
        assert events.count("model_call") == 2
        assert "tool_start" in events and "tool_end" in events
        assert next(row for row in rows if row["event"] == "tool_start")["payload"][
            "arguments_hash"
        ] == fingerprint({})
        for row in rows:
            digest = row.pop("fingerprint")
            assert digest == fingerprint(row)
        assert [row["seq"] for row in rows] == list(range(1, len(rows) + 1))
        usage = [row["payload"] for row in rows if row["event"] == "model_call"][-1]
        assert usage["model"] == "cliproxy:gpt-6.1-sol"
        assert usage["usage"]["total_tokens"] == 12
        reference = next(row["payload"]["result_ref"] for row in rows if row["event"] == "tool_end")
        assert json.loads(Path(reference).read_text())["content"] == "evidence"


@pytest.mark.parametrize("decision", ["approve", "reject", "edit"])
def test_interrupt_and_decision_are_journaled(
    tmp_path: Path, config: RouterConfig, decision: str
) -> None:
    with RunJournal(tmp_path / "run.jsonl", "approval") as journal:
        model = fake(call("lookup"), "done")
        spec = write_spec(tmp_path, "tools: [lookup]\ninterrupt_on: {lookup: true}")
        graph = compiled(
            spec,
            BuildContext(
                ModelRouter(config, fake_models(model)),
                tools={"lookup": lookup},
                checkpointer=InMemorySaver(),
                journal=journal,
            ),
        )
        run_config: RunnableConfig = {"configurable": {"thread_id": "approval"}}
        result = graph.invoke(
            {"messages": [{"role": "user", "content": "Lookup"}]}, config=run_config
        )
        assert result["__interrupt__"]
        assert "model_call" in [row["event"] for row in records(journal)]
        assert "tool_start" not in [row["event"] for row in records(journal)]
        response: dict[str, Any] = {"type": decision}
        if decision == "edit":
            response["edited_action"] = {"name": "lookup", "args": {}}
        graph.invoke(Command(resume={"decisions": [response]}), config=run_config)
        events = [row["event"] for row in records(journal)]
        assert "interrupt" in events and "approval_resolved" in events
        assert ("tool_start" in events) == (decision != "reject")


def test_journal_write_errors_propagate(tmp_path: Path, config: RouterConfig) -> None:
    with RunJournal(tmp_path / "run.jsonl", "r") as journal:
        journal.path = tmp_path  # Opening a directory as an append target fails.
        model = fake("done")
        graph = compiled(
            write_spec(tmp_path),
            BuildContext(ModelRouter(config, fake_models(model)), journal=journal),
        )
        with pytest.raises(OSError):
            graph.invoke({"messages": [{"role": "user", "content": "Hello"}]})
        assert model.calls == 0


@pytest.mark.parametrize("asynchronous", [False, True])
def test_journal_records_successful_fallback_model(
    tmp_path: Path, config: RouterConfig, asynchronous: bool
) -> None:
    config.fallbacks = ["openai:fallback"]
    router = ModelRouter(
        config, {**fake_models(fake("unused", failures=1)), "openai:fallback": fake("recovered")}
    )
    with RunJournal(tmp_path / "run.jsonl", "fallback") as journal:
        graph = compiled(write_spec(tmp_path), BuildContext(router, journal=journal))
        inputs = {"messages": [{"role": "user", "content": "Hello"}]}
        result = asyncio.run(graph.ainvoke(inputs)) if asynchronous else graph.invoke(inputs)
        assert result["messages"][-1].content == "recovered"
        model_rows = [row for row in records(journal) if row["event"] == "model_call"]
        assert model_rows[0]["payload"]["model"] == "openai:fallback"


@pytest.mark.parametrize(
    "path",
    [
        "/artifacts/output",
        "/ARTIFACTS/output",
        "/memories/global/rule",
        "/data/private",
        "/artifacts/../escape",
        "/artifacts./output",
        "/artifacts /output",
        "/artifacts:stream",
        "/ARTIFA~1/output",
    ],
)
def test_admission_refuses_direct_sync_async_and_upload_bypass(tmp_path: Path, path: str) -> None:
    inner = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend = AdmissionBackend(inner, AdmissionGate(), deny_write=["/data/**"])
    assert backend.write(path, "denied").error
    assert asyncio.run(backend.awrite(path, "denied")).error
    assert backend.edit(path, "old", "new").error
    assert backend.upload_files([(path, b"denied")])[0].error
    assert asyncio.run(backend.aupload_files([(path, b"denied")]))[0].error
    assert not list(tmp_path.iterdir())


def test_admission_verification_approval_and_compare_and_swap(tmp_path: Path) -> None:
    data = tmp_path / "volume"
    data.mkdir()
    inner = FilesystemBackend(root_dir=data, virtual_mode=True)
    with RunJournal(tmp_path / "run.jsonl", "admit") as journal:
        gate = AdmissionGate(journal)
        backend = AdmissionBackend(inner, gate)
        proposal = WriteProposal("/artifacts/output", "old", None)
        with pytest.raises(AdmissionDenied):
            gate.stage(proposal, lambda _: False)
        reference = gate.stage(proposal, lambda _: True)
        with pytest.raises(AdmissionDenied):
            gate.approve(reference, principal="agent")
        gate.approve(reference, principal="operator")
        assert backend.write(proposal.path, "tampered").error
        assert not backend.write(proposal.path, proposal.content).error
        assert backend.write(proposal.path, proposal.content).error
        edit = WriteProposal(proposal.path, "new", sha256(b"old").hexdigest())
        gate.approve(gate.stage(edit, lambda _: True), principal="operator")
        (data / "artifacts/output").write_text("changed")
        assert backend.edit(proposal.path, "changed", "new").error
        (data / "artifacts/output").write_text("old")
        assert not asyncio.run(backend.aedit(proposal.path, "old", "new")).error
        assert (data / "artifacts/output").read_text() == "new"
        assert backend.delete("/artifacts").error
        assert backend.delete("/").error
        assert [r["event"] for r in records(journal)].count("write_applied") == 2


@pytest.mark.parametrize(
    "budget,override",
    [
        (Budget(model_calls=2), None),
        (Budget(model_calls=10), Budget(model_calls=2)),
        (Budget(tool_calls=2), None),
    ],
)
def test_budget_stops_loop(
    tmp_path: Path, config: RouterConfig, budget: Budget, override: Budget | None
) -> None:
    model = BoundFakeChatModel(messages=repeat(call("lookup")))
    spec = write_spec(tmp_path, "tools: [lookup]")
    spec.budget = budget
    graph = compiled(
        spec,
        BuildContext(
            ModelRouter(config, fake_models(model)), tools={"lookup": lookup}, budget=override
        ),
    )
    if budget.tool_calls:
        with pytest.raises(ToolCallLimitExceededError):
            graph.invoke({"messages": [{"role": "user", "content": "Loop"}]})
    else:
        result = graph.invoke({"messages": [{"role": "user", "content": "Loop"}]})
        assert "limit" in result["messages"][-1].content.lower()
        assert model.calls == 2


def test_runtime_money_flag_rechecked(tmp_path: Path, config: RouterConfig) -> None:
    safe = lookup.model_copy()
    model = fake(call("lookup"), "done")
    graph = compiled(
        write_spec(tmp_path, "tools: [lookup]"),
        BuildContext(ModelRouter(config, fake_models(model)), tools={"lookup": safe}),
    )
    safe.metadata = {"money_path": True}
    with pytest.raises(MoneyPathDenyError):
        graph.invoke({"messages": [{"role": "user", "content": "Lookup"}]})


def test_general_purpose_delegation_inherits_guards(tmp_path: Path, config: RouterConfig) -> None:
    model = fake(
        call("task", {"description": "Find evidence", "subagent_type": "general-purpose"}),
        call("lookup"),
        call("lookup"),
        "parent done",
    )
    with RunJournal(tmp_path / "run.jsonl", "delegate") as journal:
        spec = write_spec(tmp_path, "tools: [lookup]\nbudget: {model_calls: 2}")
        graph = compiled(
            spec,
            BuildContext(
                ModelRouter(config, fake_models(model)), tools={"lookup": lookup}, journal=journal
            ),
        )
        result = graph.invoke({"messages": [{"role": "user", "content": "Delegate"}]})
        assert result["messages"][-1].content == "parent done"
        rows = records(journal)
        child = [r for r in rows if r["payload"].get("agent") == "agent/general-purpose"]
        assert len([r for r in child if r["event"] == "model_call"]) == 2
        assert all(
            r["payload"]["model"] == "cliproxy:gpt-6.1-sol"
            for r in child
            if r["event"] == "model_call"
        )
        assert child[-1]["event"] == "run_end"


def test_delegated_approval_pause_is_not_journaled_as_failure(
    tmp_path: Path, config: RouterConfig
) -> None:
    model = fake(
        call("task", {"description": "Find evidence", "subagent_type": "general-purpose"}),
        call("lookup"),
        "child done",
        "parent done",
    )
    with RunJournal(tmp_path / "run.jsonl", "delegate-approval") as journal:
        graph = compiled(
            write_spec(tmp_path, "tools: [lookup]\ninterrupt_on: {lookup: true}"),
            BuildContext(
                ModelRouter(config, fake_models(model)),
                tools={"lookup": lookup},
                journal=journal,
                checkpointer=InMemorySaver(),
            ),
        )
        run_config: RunnableConfig = {"configurable": {"thread_id": "delegated-approval"}}
        result = graph.invoke(
            {"messages": [{"role": "user", "content": "Delegate"}]}, config=run_config
        )
        assert result["__interrupt__"]
        assert not any(row["event"] == "run_end" for row in records(journal))
        result = graph.invoke(
            Command(resume={"decisions": [{"type": "approve"}]}), config=run_config
        )
        assert result["messages"][-1].content == "parent done"
        assert all(
            row["payload"]["status"] == "completed"
            for row in records(journal)
            if row["event"] == "run_end"
        )


def test_refused_evidence_is_quarantined_verbatim(tmp_path: Path) -> None:
    data = tmp_path / "volume"
    data.mkdir()
    with RunJournal(tmp_path / "run.jsonl", "quarantine") as journal:
        backend = AdmissionBackend(
            FilesystemBackend(root_dir=data, virtual_mode=True), AdmissionGate(journal)
        )
        raw = b"\xffinvalid\x00evidence"
        assert backend.upload_files([("/artifacts/bad", raw)])[0].error
        reference = records(journal)[-1]["payload"]["result_ref"]
        assert Path(reference).read_bytes() == raw
        assert not list(data.iterdir())


def test_admission_through_agent_interrupt_and_backend(
    tmp_path: Path, config: RouterConfig
) -> None:
    volume = tmp_path / "volume"
    volume.mkdir()
    model = fake(
        call("write_file", {"file_path": "/artifacts/output", "content": "checked"}), "done"
    )
    with RunJournal(tmp_path / "run.jsonl", "admission-run") as journal:
        gate = AdmissionGate(journal)
        proposal = WriteProposal("/artifacts/output", "checked", None)
        proposal_id = gate.stage(proposal, lambda p: p.content == "checked")
        spec = write_spec(tmp_path, "interrupt_on: {write_file: true}")
        ctx = BuildContext(
            ModelRouter(config, fake_models(model)),
            journal=journal,
            admission=gate,
            backend=FilesystemBackend(root_dir=volume, virtual_mode=True),
            checkpointer=InMemorySaver(),
        )
        graph = compiled(spec, ctx)
        run_config: RunnableConfig = {"configurable": {"thread_id": "admission"}}
        result = graph.invoke(
            {"messages": [{"role": "user", "content": "Write checked evidence"}]}, config=run_config
        )
        assert result["__interrupt__"]
        assert not list(volume.iterdir())
        gate.approve(proposal_id, principal="operator")
        result = graph.invoke(
            Command(resume={"decisions": [{"type": "approve"}]}), config=run_config
        )
        assert result["messages"][-1].content == "done"
        assert (volume / "artifacts/output").read_text() == "checked"
        events = [r["event"] for r in records(journal)]
        assert events.index("before_write") < events.index("write_applied")


def test_resolved_mcp_money_tool_is_rejected(tmp_path: Path, config: RouterConfig) -> None:
    server = tmp_path / "server.py"
    server.write_text(
        'from fastmcp import FastMCP\nmcp = FastMCP("broker")\n@mcp.tool\n'
        'def paper_submit_order() -> str:\n    """Must never execute."""\n'
        '    raise RuntimeError("venue reached")\n'
        "mcp.run()\n",
        encoding="utf-8",
    )
    config.mcp_servers = {"broker": {"command": sys.executable, "args": [str(server)]}}
    spec = write_spec(tmp_path, "mcp_servers: [broker]")
    with pytest.raises(MoneyPathDenyError):
        compiled(spec, BuildContext(ModelRouter(config)))


def test_directory_delete_cannot_bypass_descendant_policy(tmp_path: Path) -> None:
    (tmp_path / "scratch/private").mkdir(parents=True)
    (tmp_path / "scratch/private/secret").write_text("keep")
    (tmp_path / "scratch/public").write_text("temporary")
    backend = AdmissionBackend(
        FilesystemBackend(root_dir=tmp_path, virtual_mode=True),
        AdmissionGate(),
        deny_write=["/scratch/private/**"],
    )
    assert backend.delete("/scratch").error
    assert (tmp_path / "scratch/private/secret").read_text() == "keep"
    assert not backend.delete("/scratch/public").error


@pytest.mark.parametrize(
    "secret",
    ["/scratch/foo/private/secret", "/scratch/foo/.private", "/scratch/foo/private/.secret"],
)
def test_state_file_with_descendants_cannot_bypass_delete_policy(
    tmp_path: Path, config: RouterConfig, secret: str
) -> None:
    @tool
    def cleanup() -> str:
        """Remove a temporary state file."""
        backend = AdmissionBackend(StateBackend(), AdmissionGate(), deny_write=[secret])
        result = backend.delete("/scratch/foo")
        return result.error or "deleted"

    graph = compiled(
        write_spec(tmp_path, "tools: [cleanup]"),
        BuildContext(
            ModelRouter(config, fake_models(fake(call("cleanup"), "done"))),
            tools={"cleanup": cleanup},
        ),
    )
    file = {"content": "keep", "created_at": "2026-10-07", "modified_at": "2026-10-07"}
    files = {"/scratch/foo": file, secret: file}
    result = graph.invoke({"messages": [{"role": "user", "content": "Clean up"}], "files": files})
    assert result["files"] == files
    assert "Admission denied" in result["messages"][-2].content


def test_default_guarded_state_backend_preserves_file_writes(
    tmp_path: Path, config: RouterConfig
) -> None:
    graph = compiled(
        write_spec(tmp_path),
        BuildContext(
            ModelRouter(
                config,
                fake_models(
                    fake(
                        call("write_file", {"file_path": "/scratch/evidence", "content": "saved"}),
                        call("read_file", {"file_path": "/scratch/evidence"}),
                        "done",
                    )
                ),
            )
        ),
    )
    result = graph.invoke({"messages": [{"role": "user", "content": "Save evidence"}]})
    assert result["files"]["/scratch/evidence"]["content"] == "saved"
    assert "saved" in result["messages"][-2].content
