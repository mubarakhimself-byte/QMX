"""Read bars from a QMX data server, ask one model for the day's bias, and keep it in app.db.

Live, the daily job calls `read_bars` on the MCP server at `data_url` with the control token, then
sends that snapshot and `agents/analyst.md` to the OpenAI-compatible chat endpoint at `model_url`
with `QMX_MODEL_KEY`, asking for one JSON answer. Under the road's `tests` and `sandbox` stages it
reads a recorded snapshot and a recorded answer and makes no network call.

Settings are the image's `config.json`, overlaid by the instance's own `data/config.json`. The
image is immutable once installed, so an instance is pointed at its services from its volume.
"""

from __future__ import annotations

import html
import json
import os
import sqlite3
from collections.abc import Awaitable, Callable
from contextlib import closing
from pathlib import Path
from typing import Any, Literal, cast

import httpx
from fastmcp import Client, FastMCP
from fastmcp.apps import AppConfig
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).parent
VIEW = "ui://macro-daily-bias/view.html"
RECORDED_STAGES = frozenset({"tests", "sandbox"})
RECORDED_SNAPSHOT: dict[str, Any] = {
    "as_of": "2026-10-07",
    "bars": [{"close": "1.10"}],
    "source": "recorded",
}
RECORDED_ANSWER = json.dumps(
    {"bias": "neutral", "rationale": "Recorded fixture has no macro driver coverage."}
)
MODEL_TIMEOUT_SECONDS = 120.0
"""How long the daily job waits for the model's one answer."""

type Model = Callable[[str, str], Awaitable[str]]
"""One model answer: the system prompt and the user message in, the answer's text out."""


class Bias(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bias: Literal["bullish", "bearish", "neutral"]
    rationale: str = Field(min_length=1, max_length=4000)


def settings(volume: Path) -> dict[str, Any]:
    """The image's settings, with the instance's own `data/config.json` over them."""
    found = cast(dict[str, Any], json.loads((ROOT / "config.json").read_text(encoding="utf-8")))
    own = volume / "data" / "config.json"
    if own.is_file():
        found.update(cast(dict[str, Any], json.loads(own.read_text(encoding="utf-8"))))
    return found


def latest(volume: Path) -> dict[str, Any] | None:
    with closing(sqlite3.connect(volume / "app.db")) as db, db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(
            "CREATE TABLE IF NOT EXISTS biases (seq INTEGER PRIMARY KEY, data TEXT NOT NULL)"
        )
        row = db.execute("SELECT data FROM biases ORDER BY seq DESC LIMIT 1").fetchone()
    return json.loads(row[0]) if row else None


def chat_model(config: dict[str, Any]) -> Model:
    """The configured model behind an OpenAI-compatible `chat/completions` endpoint."""
    if not config["model"] or not config["model_url"]:
        raise ValueError("Configure the app's model and model_url before live execution.")
    url = str(config["model_url"]).rstrip("/") + "/chat/completions"

    async def ask(system: str, user: str) -> str:
        async with httpx.AsyncClient(timeout=MODEL_TIMEOUT_SECONDS) as http:
            response = await http.post(
                url,
                headers={"Authorization": f"Bearer {os.environ['QMX_MODEL_KEY']}"},
                json={
                    "model": str(config["model"]),
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "response_format": {"type": "json_object"},
                },
            )
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"])

    return ask


async def recorded_model(system: str, user: str) -> str:
    return RECORDED_ANSWER


async def read_snapshot(config: dict[str, Any], data_target: Any) -> dict[str, Any]:
    client = (
        cast("Client[Any]", data_target) if isinstance(data_target, Client) else Client(data_target)
    )
    async with client:
        response = await client.call_tool(
            "read_bars", {"symbol": config["symbol"], "timeframe": config["timeframe"], "limit": 50}
        )
    if response.is_error or not response.structured_content:
        raise ValueError("The data server did not return a valid snapshot.")
    return dict(response.structured_content)


async def refresh(
    volume: Path,
    data_target: Any = None,
    model: Model | None = None,
) -> dict[str, Any]:
    config = settings(volume)
    recorded = os.environ.get("QMX_STAGE") in RECORDED_STAGES
    if data_target is not None:
        snapshot = await read_snapshot(config, data_target)
    elif recorded:
        snapshot = dict(RECORDED_SNAPSHOT)
    else:
        if not config["data_url"]:
            raise ValueError("Configure data_url before the live daily job.")
        snapshot = await read_snapshot(
            config, Client(config["data_url"], auth=os.environ["QMX_DATA_TOKEN"])
        )
    if model is None:
        model = recorded_model if recorded else chat_model(config)
    system = (ROOT / "agents/analyst.md").read_text(encoding="utf-8")
    answer = Bias.model_validate_json(await model(system, json.dumps(snapshot)))
    # The source's observation date is kept; the model cannot invent freshness.
    payload = {
        **answer.model_dump(),
        "as_of": str(snapshot.get("as_of", "unknown")),
        "source": "recorded" if recorded else "qmx-data",
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
