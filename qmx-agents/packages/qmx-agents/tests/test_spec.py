from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from conftest import compiled, fake, fake_models
from deepagents import GeneralPurposeSubagentProfile, HarnessProfile, register_harness_profile
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from pydantic import ValidationError
from qmx_tools import DomainContext

from qmx_agents.router import ModelRouter, RouterConfig, RunContext
from qmx_agents.spec import AgentSpec, BuildContext, build_agent, load_spec


def write_spec(tmp_path: Path, extra: str = "", name: str = "agent") -> AgentSpec:
    (tmp_path / "prompt.md").write_text("Only use your assigned tools.", encoding="utf-8")
    path = tmp_path / f"{name}.yaml"
    path.write_text(
        f"name: {name}\nmodel: tier:workhorse\nsystem_prompt: prompt.md\n{extra}",
        encoding="utf-8",
    )
    return load_spec(path)


def call(name: str, args: dict[str, Any] | None = None) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args or {}, "id": name}])


def test_default_domain_registry_is_used_by_build_agent(
    tmp_path: Path, config: RouterConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QMX_TOOLS_ROOT", str(tmp_path / "volume"))
    spec = write_spec(tmp_path, "tools: [qmx-research.library_save]\n")
    model = fake(
        call(
            "qmx_research_library_save",
            {"artifact": {"name": "report", "kind": "note", "content": "recorded"}},
        ),
        "saved",
    )
    graph = compiled(spec, BuildContext(router=ModelRouter(config, models=fake_models(model))))
    result = graph.invoke({"messages": [{"role": "user", "content": "Save this report"}]})
    assert result["messages"][-1].content == "saved"
    artifacts = DomainContext(root=tmp_path / "volume")
    catalog = artifacts.library.search("")
    assert len(catalog) == 1
    assert catalog[0]["title"] == "report" and catalog[0]["kind"] == "note"
    ref = catalog[0]["ref"]
    assert isinstance(ref, str)
    saved = artifacts.artifact(ref)
    assert (saved.name, saved.kind, saved.content) == ("report", "note", "recorded")


def test_valid_spec_resolves_paths_and_all_fields(tmp_path: Path) -> None:
    spec = write_spec(
        tmp_path,
        "tools: [lookup]\nmcp_servers: [docs]\nskills: [/skills/]\n"
        "memory: {scope: workflow}\nsubagents: [{ref: child.yaml}, {workflow: workflows/sweep}]\n"
        "background_tasks: [overnight.yaml]\ninterrupt_on: {lookup: true}\n"
        "permissions: {write: ['/artifacts/**'], deny_write: ['/data/**']}\n"
        "budget: {model_calls: 200, tool_calls: 400}\n",
    )
    assert spec.system_prompt == tmp_path / "prompt.md"
    assert spec.subagents[0].ref == tmp_path / "child.yaml"
    assert spec.background_tasks == [tmp_path / "overnight.yaml"]
    assert spec.memory.scope == "workflow"
    assert spec.budget.model_calls == 200
    assert [rule.mode for rule in spec.permissions.rules()] == ["deny", "allow", "deny"]


@pytest.mark.parametrize(
    "extra",
    [
        "unexpected: true",
        "memory: {scope: unknown}",
        "budget: {tool_calls: 0}",
        "subagents: [{}]",
        "subagents: [{ref: x, workflow: y}]",
        "async_subagents: [legacy.yaml]",
    ],
)
def test_invalid_spec(tmp_path: Path, extra: str) -> None:
    with pytest.raises(ValidationError):
        write_spec(tmp_path, extra)


def test_missing_prompt(tmp_path: Path) -> None:
    path = tmp_path / "agent.yaml"
    path.write_text("name: agent\nmodel: tier:fast\nsystem_prompt: missing.md", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        load_spec(path)


def test_tool_filtering_and_unknown_tool_never_runs(tmp_path: Path, config: RouterConfig) -> None:
    used: list[str] = []

    @tool
    def allowed() -> str:
        """An assigned tool."""
        used.append("allowed")
        return "ok"

    @tool
    def other() -> str:
        """An unassigned tool."""
        used.append("other")
        return "bad"

    model = fake(call("other"), call("allowed"), "done")
    ctx = BuildContext(
        ModelRouter(config, fake_models(model)), tools={"allowed": allowed, "other": other}
    )
    graph = compiled(write_spec(tmp_path, "tools: [allowed]"), ctx)
    result = graph.invoke({"messages": [{"role": "user", "content": "Use tools"}]})
    assert result["messages"][-1].content == "done"
    assert used == ["allowed"]
    assert "other" not in model.bound_names[0]
    assert "allowed" in model.bound_names[0]


def test_subagent_owns_tools_and_model_with_runtime_context(
    tmp_path: Path, config: RouterConfig
) -> None:
    used: list[str] = []

    @tool
    def parent_tool() -> str:
        """Parent only."""
        used.append("parent")
        return "parent"

    @tool
    def child_tool() -> str:
        """Child only."""
        used.append("child")
        return "child"

    child = write_spec(tmp_path, "tools: [child_tool]", name="child")
    (tmp_path / "child.yaml").write_text(
        "name: child\nmodel: tier:fast\nsystem_prompt: prompt.md\ntools: [child_tool]",
        encoding="utf-8",
    )
    assert child.name == "child"
    parent = write_spec(tmp_path, "tools: [parent_tool]\nsubagents: [{ref: child.yaml}]")
    parent_model = fake(
        call("task", {"description": "Do the child job", "subagent_type": "child"}), "done"
    )
    child_model = fake(call("child_tool"), "child done")
    ctx = BuildContext(
        ModelRouter(
            config, {"cliproxy:gpt-6.1-sol": parent_model, "cliproxy:gpt-6-luna": child_model}
        ),
        tools={"parent_tool": parent_tool, "child_tool": child_tool},
    )
    graph = compiled(parent, ctx)
    runtime = RunContext()
    graph.invoke({"messages": [{"role": "user", "content": "Delegate"}]}, context=runtime)
    assert used == ["child"]
    assert "parent_tool" not in child_model.bound_names[0]
    assert "child_tool" not in parent_model.bound_names[0]
    assert runtime.effective_models == {
        "agent": "cliproxy:gpt-6.1-sol",
        "child": "cliproxy:gpt-6-luna",
    }


def test_interrupt_then_approve(tmp_path: Path, config: RouterConfig) -> None:
    used: list[str] = []

    @tool
    def publish() -> str:
        """Publish after approval."""
        used.append("published")
        return "ok"

    model = fake(call("publish"), "done")
    ctx = BuildContext(
        ModelRouter(config, fake_models(model)),
        tools={"publish": publish},
        checkpointer=InMemorySaver(),
    )
    spec = write_spec(tmp_path, "tools: [publish]\ninterrupt_on: {publish: true}")
    graph = compiled(spec, ctx)
    run_config: RunnableConfig = {"configurable": {"thread_id": "approval"}}
    result = graph.invoke({"messages": [{"role": "user", "content": "Publish"}]}, config=run_config)
    assert result["__interrupt__"]
    assert used == []
    result = graph.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config=run_config)
    assert used == ["published"]
    assert result["messages"][-1].content == "done"


def test_interrupt_requires_checkpoint(tmp_path: Path, config: RouterConfig) -> None:
    spec = write_spec(tmp_path, "interrupt_on: {publish: true}")
    with pytest.raises(ValueError, match="checkpointer"):
        asyncio.run(build_agent(spec, BuildContext(ModelRouter(config))))


def test_harness_exclusions_and_no_general_purpose(tmp_path: Path, config: RouterConfig) -> None:
    name = "qmx:restricted-test"
    config.harness_profiles[name] = {"general_purpose_subagent": {"enabled": False}}
    register_harness_profile(
        name,
        HarnessProfile(
            excluded_tools=frozenset({"execute", "write_file", "edit_file", "delete"}),
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ),
    )
    model = fake("done", name=name)
    ctx = BuildContext(ModelRouter(config, fake_models(model)))
    graph = compiled(write_spec(tmp_path), ctx)
    graph.invoke({"messages": [{"role": "user", "content": "Hello"}]})
    assert {"execute", "write_file", "edit_file", "delete", "task"}.isdisjoint(model.bound_names[0])


def test_permission_write_allowlist_enforced(tmp_path: Path, config: RouterConfig) -> None:
    model = fake(call("write_file", {"file_path": "/data/private", "content": "denied"}), "done")
    spec = write_spec(tmp_path, "permissions: {write: ['/artifacts/**'], deny_write: ['/data/**']}")
    graph = compiled(spec, BuildContext(ModelRouter(config, fake_models(model))))
    result = graph.invoke({"messages": [{"role": "user", "content": "Write data"}]})
    assert "permission" in str(result["messages"][-2].content).lower()
    assert "/data/private" not in result.get("files", {})


def test_cyclic_subagent_rejected(tmp_path: Path, config: RouterConfig) -> None:
    spec = write_spec(tmp_path, "subagents: [{ref: agent.yaml}]")
    with pytest.raises(ValueError, match="Cyclic"):
        asyncio.run(build_agent(spec, BuildContext(ModelRouter(config))))


def test_background_tasks_fail_explicitly_until_control_exists(
    tmp_path: Path, config: RouterConfig
) -> None:
    spec = write_spec(tmp_path, "background_tasks: [overnight.yaml]")
    with pytest.raises(NotImplementedError, match="qmx-control"):
        asyncio.run(build_agent(spec, BuildContext(ModelRouter(config))))
