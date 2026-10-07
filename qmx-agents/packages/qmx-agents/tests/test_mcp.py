from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, cast

from conftest import compiled, fake, fake_models
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable
from langgraph.graph import (  # pyright: ignore[reportMissingTypeStubs]
    END,
    START,
    MessagesState,
    StateGraph,
)
from test_spec import call, write_spec

from qmx_agents.router import ModelRouter, RouterConfig, RunContext
from qmx_agents.spec import BuildContext, build_agent


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
