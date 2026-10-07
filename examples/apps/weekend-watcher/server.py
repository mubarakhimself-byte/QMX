"""A real AgentSpec graph with a recorded fake provider; live keys are never required."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Self, cast

from fastmcp import FastMCP
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.runnables import Runnable
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import JsonValue
from qmx_agents.router import ModelRouter, RouterConfig
from qmx_agents.spec import BuildContext, build_agent, load_spec

mcp = FastMCP("Weekend watcher")


class RecordedModel(GenericFakeChatModel):
    def bind_tools(self, *args: Any, **kwargs: Any) -> Self:
        return self


@mcp.tool()
async def summarize(snapshot: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Summarise a supervisor-verified snapshot reference and emit a summary artifact."""
    payload = json.loads(Path(cast(str, snapshot["path"])).read_text(encoding="utf-8"))
    lines = [
        f"{row['exchange']}: {row['status']} ({row['observed_at']})"
        for row in payload["observations"]
    ]
    recorded = "Recorded-data fixture: " + ("; ".join(lines) or "no observations.")
    config = RouterConfig.model_validate(
        {
            "profile": "recorded",
            "profiles": {
                "recorded": dict.fromkeys(
                    ("fast", "workhorse", "coding", "reasoning_high"), "local:recorded"
                )
            },
            "providers": {},
            "max_retries": 0,
        }
    )
    router = ModelRouter(config, {"local:recorded": RecordedModel(messages=iter([recorded]))})
    spec = load_spec(Path(__file__).parent / "agents/watcher.yaml")
    graph = cast(
        "Runnable[Any, dict[str, Any]]",
        await build_agent(spec, BuildContext(router, checkpointer=InMemorySaver())),
    )
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": json.dumps(payload)}]},
        config={"configurable": {"thread_id": snapshot["sha256"]}},
    )
    return {
        "output": "summary",
        "data": {
            "summary": str(result["messages"][-1].text),
            "source_sha256": snapshot["sha256"],
            "mode": "recorded_fixture",
        },
    }


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
