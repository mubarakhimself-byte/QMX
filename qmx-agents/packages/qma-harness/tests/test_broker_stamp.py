"""A broker read's demo-or-live stamp survives the harness's tool text, paging and spill (MD2)."""

from __future__ import annotations

import asyncio
import dataclasses
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from qmx_broker.models import Account, Broker, BrokerSettings, Connection
from qmx_broker.server import create_server
from qmx_broker.service import BrokerService
from qmx_control.catalog import rows
from qmx_control.models import LibraryInput

from qma.harness.tools import wrap

STAMP = {"environment": "demo", "is_live": False, "connection_id": "main", "account_id": "spot"}
START = 1700000000000
SETTINGS = BrokerSettings(
    connections=[
        Broker(
            id="crypto",
            name="Crypto",
            adapter="ccxt",
            exchange="binance",
            connections=[
                Connection(
                    id="main",
                    credential_ref="qmx/crypto",
                    accounts=[Account(id="spot", currency="USDT")],
                )
            ],
        )
    ]
)


class DemoAdapter:
    bar_page_limit = None
    is_live = False

    async def account_state(self) -> dict[str, Any]:
        return {"balances": {"total": {"USDT": 100}}, "timestamp_ms": START, "market_type": "spot"}

    async def positions(self) -> list[dict[str, Any]]:
        return [
            {"asset": asset, "quantity": "1", "market_type": "spot"} for asset in ("BTC", "ETH")
        ]

    async def bars(
        self, symbol: str, timeframe: str, since: int, until: int, limit: int | None
    ) -> list[dict[str, Any]]:
        series = (START + minute * 60000 for minute in range(400))
        return [
            {"timestamp_ms": at, "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 10}
            for at in series
            if since <= at <= until
        ]


def call(
    tmp_path: Path, name: str, arguments: dict[str, Any], *, cursor: bool = False
) -> tuple[str, list[LibraryInput]]:
    """The text a chat sees for one broker tool call, and anything it spilled to the Library."""

    @asynccontextmanager
    async def factory(
        broker: Broker, connection: Connection, account: Account
    ) -> AsyncGenerator[DemoAdapter]:
        yield DemoAdapter()

    saved: list[LibraryInput] = []

    def save(item: LibraryInput) -> dict[str, Any]:
        saved.append(item)
        return {"id": "artifact-1"}

    async def run() -> str:
        service = BrokerService(tmp_path, SETTINGS, factory)  # pyright: ignore[reportArgumentType] - a fake adapter
        tools = {tool.name: tool for tool in await create_server(service).list_tools()}
        [row] = [row for row in rows() if row.name == f"broker_read_{name}"]
        tool = wrap(dataclasses.replace(row, cursor=cursor), tools[row.target], save)
        answer = await tool.call(
            {"broker_id": "crypto", "connection_id": "main", "account_id": "spot", **arguments}
        )
        return answer["content"][0]["text"]

    return asyncio.run(run()), saved


def test_an_account_state_answer_says_demo_beside_the_balance(tmp_path: Path) -> None:
    text, saved = call(tmp_path, "account_state", {})
    assert json.loads(text) == {
        **STAMP,
        "result": {
            "balances": {"total": {"USDT": 100}},
            "timestamp_ms": START,
            "market_type": "spot",
        },
    }
    assert saved == []


def test_a_paged_list_answer_keeps_the_stamp_on_its_page(tmp_path: Path) -> None:
    text, _ = call(tmp_path, "positions", {}, cursor=True)
    assert json.loads(text) == {
        **STAMP,
        "items": [
            {"asset": "BTC", "quantity": "1", "market_type": "spot"},
            {"asset": "ETH", "quantity": "1", "market_type": "spot"},
        ],
        "next_offset": None,
    }


def test_a_long_bars_answer_spills_with_the_stamp_on_its_pointer(tmp_path: Path) -> None:
    window = {"symbol": "BTC/USDT", "timeframe": "1m", "since": START, "until": START + 399 * 60000}
    text, saved = call(tmp_path, "bars", window)
    pointer = json.loads(text)
    whole = json.loads(str(cast("dict[str, Any]", saved[0].content)["text"]))

    assert {key: pointer[key] for key in (*STAMP, "spilled", "artifact_id")} == {
        **STAMP,
        "spilled": True,
        "artifact_id": "artifact-1",
    }
    assert pointer["head"].startswith('{"environment":"demo","is_live":false')
    assert ({key: whole[key] for key in STAMP}, len(whole["result"])) == (STAMP, 400)
