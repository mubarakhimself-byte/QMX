"""Read qmx-data, summarise with an agent, and persist the panel's state in app.db."""

from __future__ import annotations

import html
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Literal, Self, cast

from fastmcp import Client, FastMCP
from fastmcp.apps import AppConfig
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.runnables import Runnable
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, ConfigDict, Field
from qmx_agents.router import ModelRouter, RouterConfig
from qmx_agents.spec import BuildContext, build_agent, load_spec

ROOT = Path(__file__).parent
VIEW = "ui://macro-daily-bias/view.html"


class Bias(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bias: Literal["bullish", "bearish", "neutral"]
    rationale: str = Field(min_length=1, max_length=4000)


class RecordedModel(GenericFakeChatModel):
    def bind_tools(self, *args: Any, **kwargs: Any) -> Self:
        return self


def latest(volume: Path) -> dict[str, Any] | None:
    with closing(sqlite3.connect(volume / "app.db")) as db, db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(
            "CREATE TABLE IF NOT EXISTS biases (seq INTEGER PRIMARY KEY, data TEXT NOT NULL)"
        )
        row = db.execute("SELECT data FROM biases ORDER BY seq DESC LIMIT 1").fetchone()
    return json.loads(row[0]) if row else None


async def refresh(
    volume: Path,
    data_target: Any = None,
    model: BaseChatModel | None = None,
) -> dict[str, Any]:
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    recorded = os.environ.get("QMX_STAGE") in {"tests", "sandbox"}
    if data_target is None:
        if recorded:
            data_target = FastMCP("Recorded qmx-data fixture")

            @data_target.tool
            def read_bars(symbol: str, timeframe: str, limit: int) -> dict[str, Any]:
                """Return the explicitly recorded test fixture."""
                return {"as_of": "2026-10-07", "bars": [{"close": "1.10"}], "source": "recorded"}

            _ = read_bars
        else:
            if not config["data_url"]:
                raise ValueError("Configure data_url before the live daily job.")
            data_target = Client(config["data_url"], auth=os.environ["QMX_DATA_TOKEN"])
    client = (
        cast("Client[Any]", data_target) if isinstance(data_target, Client) else Client(data_target)
    )
    async with client:
        response = await client.call_tool(
            "read_bars", {"symbol": config["symbol"], "timeframe": config["timeframe"], "limit": 50}
        )
        if response.is_error or not response.structured_content:
            raise ValueError("qmx-data did not return a valid snapshot.")
        snapshot = response.structured_content
    source = "recorded" if recorded else "qmx-data"
    if model is None:
        if recorded:
            model = RecordedModel(
                messages=iter(
                    [
                        json.dumps(
                            {
                                "bias": "neutral",
                                "rationale": "Recorded fixture has no macro driver coverage.",
                            }
                        )
                    ]
                )
            )
        else:
            if not config["model"] or not config["model_url"]:
                raise ValueError("Configure the app's model and model_url before live execution.")
            model = init_chat_model(
                str(config["model"]),
                base_url=str(config["model_url"]),
                api_key=os.environ["QMX_MODEL_KEY"],
            )
    router = ModelRouter(
        RouterConfig.model_validate(
            {
                "profile": "app",
                "profiles": {
                    "app": dict.fromkeys(
                        ("fast", "workhorse", "coding", "reasoning_high"), "local:configured"
                    )
                },
                "providers": {},
                "max_retries": 0,
            }
        ),
        {"local:configured": model},
    )
    graph = await build_agent(
        load_spec(ROOT / "agents/analyst.yaml"),
        BuildContext(router, checkpointer=InMemorySaver(), general_purpose_subagent=False),
    )
    result = await cast("Runnable[Any, dict[str, Any]]", graph).ainvoke(
        {"messages": [("user", json.dumps(snapshot))]},
        config={"configurable": {"thread_id": "daily"}},
    )
    answer = Bias.model_validate_json(result["messages"][-1].text)
    # The source's observation date is preserved; the model cannot invent freshness.
    payload = {
        **answer.model_dump(),
        "as_of": str(snapshot.get("as_of", "unknown")),
        "source": source,
    }
    latest(volume)
    with closing(sqlite3.connect(volume / "app.db")) as db, db:
        db.execute("INSERT INTO biases(data) VALUES(?)", (json.dumps(payload),))
    return payload


def create_server(volume: Path) -> FastMCP:
    server = FastMCP("Macro daily bias")

    @server.tool(annotations={"readOnlyHint": True}, app=AppConfig(resource_uri=VIEW))
    def bias() -> dict[str, Any]:
        """Read the latest persisted bias; a host saves it as an artifact."""
        value = latest(volume)
        return {"output": "bias", "data": value} if value else {"status": "awaiting_data"}

    @server.resource(VIEW, mime_type="text/html;profile=mcp-app")
    def view() -> str:
        """Re-read the app's database on every panel open."""
        value = latest(volume)
        content = "No daily bias yet. Configure data and model providers, then run the daily job."
        if value:
            content = " ".join(
                html.escape(str(value[key])) for key in ("bias", "rationale", "as_of", "source")
            )
        return (ROOT / "ui/view.html").read_text(encoding="utf-8").replace("{{content}}", content)

    _ = bias, view
    return server
