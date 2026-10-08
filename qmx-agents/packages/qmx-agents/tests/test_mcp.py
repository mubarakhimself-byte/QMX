from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from conftest import compiled, fake, fake_models
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool, ToolException, tool
from langgraph.graph import (  # pyright: ignore[reportMissingTypeStubs]
    END,
    START,
    MessagesState,
    StateGraph,
)
from test_spec import call, write_spec

from qmx_agents.router import ModelRouter, RouterConfig, RunContext
from qmx_agents.spec import BuildContext, build_agent, mcp_configuration


def test_firecrawl_defaults_and_settings_overlay(
    tmp_path: Path, config: RouterConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    accesses: list[str] = []

    def vault(provider: str) -> str:
        accesses.append(provider)
        return "test-vault-token"

    monkeypatch.setattr("qmx_agents.spec.credential", vault)
    spec = write_spec(tmp_path, "mcp_servers: [firecrawl]", name="researcher")
    ctx = BuildContext(ModelRouter(config), qmx_home=tmp_path)
    assert mcp_configuration(spec, ctx) == {}
    assert not accesses
    (tmp_path / "settings.toml").write_text(
        "[mcp_servers.firecrawl]\nenabled = true\n", encoding="utf-8"
    )
    spec.mcp_servers = []
    servers = mcp_configuration(spec, ctx)
    assert servers == {
        "firecrawl": {"url": "https://mcp.firecrawl.dev/v2/mcp", "auth": "test-vault-token"}
    }
    assert accesses == ["firecrawl"]
    assert spec.mcp_servers == [] and config.mcp_servers == {}
    assert "test-vault-token" not in (tmp_path / "settings.toml").read_text()
    config.mcp_servers["firecrawl"] = {"enabled": True, "url": "https://host/?key=leak"}
    with pytest.raises(ValueError, match="HTTPS URL"):
        mcp_configuration(spec, ctx)


@pytest.mark.parametrize("persist", [False, True])
@pytest.mark.parametrize("fails", [False, True])
def test_enabled_firecrawl_reaches_researcher_subagent(
    tmp_path: Path,
    config: RouterConfig,
    monkeypatch: pytest.MonkeyPatch,
    persist: bool,
    fails: bool,
) -> None:
    captured: list[dict[str, Any]] = []

    @tool
    def firecrawl_scrape(url: str) -> str:
        """Read a recorded research page."""
        if fails:
            raise ToolException("recorded fetch failure")
        return "recorded research"

    firecrawl_scrape.handle_tool_error = True

    class Adapter:
        def __init__(self, options: dict[str, Any]) -> None:
            captured.append(options)

        async def __aenter__(self) -> Adapter:
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

        async def list_tools(self) -> list[BaseTool]:
            return [firecrawl_scrape]

    monkeypatch.setattr("langchain.mcp.MCPAdapter", Adapter)

    def vault(provider: str) -> str:
        return "vault-token"

    monkeypatch.setattr("qmx_agents.spec.credential", vault)
    config.mcp_servers["firecrawl"] = {"enabled": True}
    write_spec(tmp_path, name="researcher")
    parent = write_spec(tmp_path, "subagents: [{ref: researcher.yaml}]")
    model = fake(
        call("task", {"description": "Research", "subagent_type": "researcher"}),
        call("firecrawl_scrape", {"url": "https://recorded.test"}),
        "research complete",
        "done",
    )
    ctx = BuildContext(
        ModelRouter(config, fake_models(model)),
        general_purpose_subagent=False,
        qmx_home=tmp_path / "home" if persist else None,
        run=RunContext(
            session_id="research-session", workflow_id="research-flow", task_id="scrape"
        ),
    )

    async def run() -> dict[str, Any]:
        try:
            graph = cast("Runnable[Any, dict[str, Any]]", await build_agent(parent, ctx))
            return await graph.ainvoke({"messages": [{"role": "user", "content": "Research"}]})
        finally:
            await ctx.close_memory()

    result = asyncio.run(run())
    assert result["messages"][-1].content == "done"
    assert any("firecrawl_scrape" in names for names in model.bound_names)
    assert len(captured) == 1
    assert captured[0]["mcpServers"]["firecrawl"]["auth"] == "vault-token"
    if persist:
        from qmx_control.service import ControlService

        catalog = ControlService(tmp_path / "home").library_search("")
        assert len(catalog) == (0 if fails else 1)
        if not fails:
            assert catalog[0]["source"] == "https://recorded.test"
            assert catalog[0]["fetched_date"] is not None
            assert catalog[0]["content"] == "recorded research"


def test_mcp_selection_and_call_after_discovery_exits(tmp_path: Path, config: RouterConfig) -> None:
    server = tmp_path / "server.py"
    server.write_text(
        "from fastmcp import FastMCP\n"
        'mcp = FastMCP("quotes")\n'
        "@mcp.tool\n"
        "def double(value: int) -> int:\n"
        '    """Double an integer."""\n'
        "    return value * 2\n"
        "mcp.run()\n",
        encoding="utf-8",
    )
    config.mcp_servers = {
        "quotes": {"command": sys.executable, "args": [str(server)]},
        "unselected": {"command": "must-not-be-launched"},
    }
    model = fake(call("double", {"value": 21}), "done")
    spec = write_spec(tmp_path, "mcp_servers: [quotes]")

    async def run() -> dict[str, Any]:
        graph = cast(
            "Runnable[Any, dict[str, Any]]",
            await build_agent(spec, BuildContext(ModelRouter(config, fake_models(model)))),
        )
        return await graph.ainvoke({"messages": [{"role": "user", "content": "Double 21"}]})

    result = asyncio.run(run())
    assert result["messages"][-2].text == "42"
    assert result["messages"][-2].artifact == {"structured_content": {"result": 42}}
    assert "double" in model.bound_names[0]
    assert not any(name.startswith("unselected_") for name in model.bound_names[0])


def test_workflow_delegation(tmp_path: Path, config: RouterConfig) -> None:
    def step(state: MessagesState) -> dict[str, Any]:
        return {"messages": [AIMessage(content="workflow result")]}

    workflow = StateGraph(MessagesState)
    workflow.add_node("step", step)  # pyright: ignore[reportUnknownMemberType] - upstream overload
    workflow.add_edge(START, "step")
    workflow.add_edge("step", END)
    model = fake(call("task", {"description": "Run pipeline", "subagent_type": "pipeline"}), "done")
    ctx = BuildContext(
        ModelRouter(config, fake_models(model)),
        RunContext(),
        workflows={"workflows/pipeline": workflow.compile()},  # pyright: ignore[reportUnknownMemberType]
    )
    graph = compiled(write_spec(tmp_path, "subagents: [{workflow: workflows/pipeline}]"), ctx)
    result = graph.invoke({"messages": [{"role": "user", "content": "Run workflow"}]})
    assert result["messages"][-2].content == "workflow result"
