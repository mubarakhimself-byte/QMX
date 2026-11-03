"""Read bars from this machine's market store, ask one model for the day's bias, keep it in app.db.

Live, the daily job reads the `market` series' M1 bars from the read-only market root the host
hands the app (`QMX_MARKET_ROOT`), rolls them up to `timeframe`, then sends that snapshot and
`agents/analyst.md` to the OpenAI-compatible chat endpoint at `model_url` with `QMX_MODEL_KEY`,
asking for one JSON answer. Under the road's `tests` and `sandbox` stages it reads a recorded
snapshot and a recorded answer and makes no network call.

Settings are the image's `config.json`, overlaid by the instance's own `data/config.json`. The
image is immutable once installed, so an instance is pointed at its market and model from its
volume. `market` is the store's series key, `source/symbol/bar-m1/variant` (`-` for no variant).
"""

from __future__ import annotations

import html
import json
import os
import re
import sqlite3
from collections.abc import Awaitable, Callable, Sequence
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, cast

import httpx
from fastmcp import FastMCP
from fastmcp.apps import AppConfig
from pydantic import BaseModel, ConfigDict, Field
from qmf.core import is_refusal
from qmf.data.series import SeriesKey, SeriesStore

ROOT = Path(__file__).parent
SERIES_KEY = re.compile(r"[A-Za-z0-9_.+-]{1,64}/[A-Za-z0-9_.+-]{1,64}/bar-m1/[A-Za-z0-9_.+-]{1,64}")
"""A bar series in the store, `source/symbol/bar-m1/variant`, the store's own token rule."""
MONTH = re.compile(r"\d{4}-\d{2}")
TIMEFRAME = re.compile(r"([1-9][0-9]*)([mhd])")
UNIT_SECONDS = {"m": 60, "h": 3_600, "d": 86_400}
MINUTE_MS = 60_000
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
        overlay: object = json.loads(own.read_text(encoding="utf-8"))
        if not isinstance(overlay, dict):
            raise ValueError("data/config.json holds one JSON object of settings.")
        found.update(cast(dict[str, Any], overlay))
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
        content = response.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("The model answered with no text content.")
        return content

    return ask


async def recorded_model(system: str, user: str) -> str:
    return RECORDED_ANSWER


def period_ms(timeframe: str) -> int:
    found = TIMEFRAME.fullmatch(timeframe)
    if found is None:
        raise ValueError("A timeframe is minutes, hours or days, such as 15m, 4h or 1d.")
    return int(found[1]) * UNIT_SECONDS[found[2]] * 1_000


def months(store: SeriesStore, market: str) -> list[SeriesKey]:
    """Each month the store holds of `market`, oldest first."""
    source, symbol, kind, variant = market.split("/")
    variant = "" if variant == "-" else variant
    keys: list[SeriesKey] = []
    folder = store.root / source / symbol / kind / (variant or "-")
    for state in sorted(folder.glob("*/state.json")) if folder.is_dir() else ():
        name = state.parent.name
        if not MONTH.fullmatch(name):
            continue
        made = SeriesKey.try_create(source, symbol, kind, int(name[:4]), int(name[5:]), variant)
        if is_refusal(made):
            raise ValueError(f"Set market to the store's bar series: {made}")
        keys.append(made.value)
    return keys


def rolled(minutes: Sequence[tuple[int, int]], period: int) -> list[tuple[int, int]]:
    """Each closed bar of `period` ms as its start and its last minute's close, oldest first. The
    newest bar is dropped until its last minute has closed."""
    bars: list[tuple[int, int, int]] = []
    for t, close in minutes:
        bucket = t // period
        if bars and bars[-1][0] == bucket:
            bars[-1] = (bucket, t, close)
        else:
            bars.append((bucket, t, close))
    if bars and bars[-1][1] < (bars[-1][0] + 1) * period - MINUTE_MS:
        bars.pop()
    return [(bucket * period, close) for bucket, _, close in bars]


def read_market(config: dict[str, Any], market_root: Path) -> dict[str, Any]:
    """The last `bars` closed bars of the `market` series, rolled up from its M1 bars."""
    market = config["market"]
    if (
        not isinstance(market, str)
        or not SERIES_KEY.fullmatch(market)
        or {".", ".."} & set(market.split("/"))
    ):
        raise ValueError("Set market to the store's bar series, source/symbol/bar-m1/variant.")
    period = period_ms(str(config["timeframe"]))
    wanted, digits = int(config["bars"]), int(config["digits"])
    store = SeriesStore(market_root / "series")
    minutes: list[tuple[int, int]] = []
    bars: list[tuple[int, int]] = []
    for key in reversed(months(store, market)):
        read = store.read(key)
        if is_refusal(read):
            raise ValueError(f"The market store could not read {key.text}: {read}")
        minutes[:0] = [(int(row["t"]), int(row["close"])) for row in read.value.rows]
        bars = rolled(minutes, period)
        if len(bars) > wanted:
            break
    if not bars:
        raise ValueError(f"The market store holds no closed {config['timeframe']} bar of {market}.")
    shown = [
        {
            "t": datetime.fromtimestamp(start // 1_000, UTC).strftime("%Y-%m-%dT%H:%MZ"),
            "close": str(Decimal(close).scaleb(-digits)),
        }
        for start, close in bars[-wanted:]
    ]
    return {"as_of": shown[-1]["t"], "bars": shown, "source": market}


async def refresh(
    volume: Path,
    model: Model | None = None,
    market_root: Path | None = None,
) -> dict[str, Any]:
    config = settings(volume)
    recorded = os.environ.get("QMX_STAGE") in RECORDED_STAGES
    if market_root is None and not recorded:
        if "QMX_MARKET_ROOT" not in os.environ:
            raise ValueError("The host gave this app no market root to read its bars from.")
        market_root = Path(os.environ["QMX_MARKET_ROOT"])
    snapshot = dict(RECORDED_SNAPSHOT) if market_root is None else read_market(config, market_root)
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
