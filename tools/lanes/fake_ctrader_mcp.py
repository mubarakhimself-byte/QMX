"""A fixture HTTP MCP server with cTrader Remote MCP's sixteen tools (C-36). It places nothing and
reaches nothing: every answer is made up here.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../tools/lanes/fake_ctrader_mcp.py --accounts <file> --port-file <file>`

`--accounts` is a JSON file read at every request. It maps each bearer value the fake accepts to
the account its session is bound to, `{"<bearer>": 41500001}`, or to `null` for a session whose
`get_balance` names no account. Any other bearer, or none, gets HTTP 401, as an expired cTrader Web
session does. The server listens on 127.0.0.1 at `--port` (0 picks a free one) and writes the port
it bound to `--port-file` once it accepts connections. The MCP endpoint is `/mcp`.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import socket
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Final

ACCOUNTS: dict[str, Path] = {}
PLACES_NOTHING: Final = {"accepted": False, "reason": "the fake cTrader MCP places nothing"}


def agents(module: str) -> Any:
    """A module of the agents venv, which the root type check cannot see."""
    return importlib.import_module(module)


def bound() -> dict[str, int | None]:
    return json.loads(ACCOUNTS["file"].read_text(encoding="utf-8"))


def bearer(header: str | None) -> str | None:
    return header.removeprefix("Bearer ") if header and header.startswith("Bearer ") else None


def get_version() -> dict[str, str]:
    return {"server": "ctrader-remote-mcp", "version": "fake-1.0.18"}


def get_balance() -> dict[str, Any]:
    request = agents("fastmcp.server.dependencies").get_http_request()
    trader = bound().get(bearer(request.headers.get("authorization")) or "")
    found: dict[str, Any] = {
        "balance": 1_000_000,
        "equity": 1_000_000,
        "freeMargin": 1_000_000,
        "moneyDigits": 2,
        "depositAssetId": 15,
        "balanceVersion": 1,
        "accountType": "Hedged",
    }
    return found if trader is None else {"traderId": trader, **found}


def get_assets() -> dict[str, Any]:
    return {"assets": [{"assetId": 15, "name": "USD"}, {"assetId": 1, "name": "EUR"}]}


def get_symbols() -> dict[str, Any]:
    return {"symbols": [{"symbolId": 1, "symbolName": "EURUSD", "digits": 5, "pipPosition": 4}]}


def get_spot_prices(symbolIds: list[int]) -> dict[str, Any]:
    return {"spots": [{"symbolId": s, "bid": 108_412, "ask": 108_414} for s in symbolIds]}


def get_trendbars(symbolId: int, period: str, count: int = 1) -> dict[str, Any]:
    bar = {
        "utcTimestampInMinutes": 29_400_000,
        "low": 108_301,
        "deltaOpen": 52,
        "deltaClose": 98,
        "deltaHigh": 140,
        "volume": 3_412,
    }
    return {"symbolId": symbolId, "period": period, "trendbars": [bar] * max(1, min(count, 5))}


def get_positions() -> dict[str, Any]:
    return {"positions": [], "orders": []}


def get_position_details(positionId: int) -> dict[str, Any]:
    return {"error": f"no position {positionId}"}


def get_pending_orders() -> dict[str, Any]:
    return {"orders": []}


def get_order_history() -> dict[str, Any]:
    return {"orders": []}


def get_deals() -> dict[str, Any]:
    return {"deals": []}


def create_order(symbolId: int, tradeSide: str, volume: int) -> dict[str, Any]:
    return PLACES_NOTHING


def amend_order(orderId: int) -> dict[str, Any]:
    return PLACES_NOTHING


def cancel_order(orderId: int) -> dict[str, Any]:
    return PLACES_NOTHING


def amend_position(positionId: int) -> dict[str, Any]:
    return PLACES_NOTHING


def close_position(positionId: int) -> dict[str, Any]:
    return PLACES_NOTHING


TOOLS: Final = (
    get_version,
    get_balance,
    get_assets,
    get_symbols,
    get_spot_prices,
    get_trendbars,
    get_positions,
    get_position_details,
    get_pending_orders,
    get_order_history,
    get_deals,
    create_order,
    amend_order,
    cancel_order,
    amend_position,
    close_position,
)

Asgi = Callable[[dict[str, Any], Any, Any], Awaitable[None]]


def gate(app: Asgi) -> Asgi:
    """HTTP 401 for any bearer the accounts file does not name."""

    async def gated(scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            headers = {
                bytes(key).decode(): bytes(value).decode() for key, value in scope["headers"]
            }
            if bearer(headers.get("authorization")) not in bound():
                await send({"type": "http.response.start", "status": 401, "headers": []})
                await send({"type": "http.response.body", "body": b"session expired"})
                return
        await app(scope, receive, send)

    return gated


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accounts", type=Path, required=True)
    parser.add_argument("--port-file", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    ACCOUNTS["file"] = args.accounts
    server = agents("fastmcp").FastMCP("ctrader-remote-mcp")
    for tool in TOOLS:
        server.tool(tool)
    uvicorn = agents("uvicorn")
    sock = socket.socket()
    sock.bind(("127.0.0.1", args.port))
    served = uvicorn.Server(uvicorn.Config(gate(server.http_app(path="/mcp")), log_level="warning"))
    task = asyncio.create_task(served.serve(sockets=[sock]))
    while not served.started:
        await asyncio.sleep(0.05)
    args.port_file.write_text(str(sock.getsockname()[1]), encoding="utf-8")
    await task


if __name__ == "__main__":
    asyncio.run(main())
