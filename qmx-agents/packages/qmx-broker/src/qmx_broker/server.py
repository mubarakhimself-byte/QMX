"""The broker MCP door exposes seven reads and one local proposal writer."""

import os
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from qmx_broker.service import BrokerService


def create_server(service: BrokerService) -> FastMCP:
    server = FastMCP("qmx-broker")
    server.tool(annotations={"readOnlyHint": True})(service.list_accounts)
    server.tool(annotations={"readOnlyHint": True})(service.list_connections)

    async def account_state(broker_id: str, connection_id: str, account_id: str) -> dict[str, Any]:
        """Read account balances and leverage for one configured account."""
        return await service.read("account_state", broker_id, connection_id, account_id)

    async def positions(
        broker_id: str, connection_id: str, account_id: str
    ) -> list[dict[str, Any]]:
        """Read open cTrader positions or CCXT spot asset holdings."""
        return await service.read("positions", broker_id, connection_id, account_id)

    async def quotes(
        broker_id: str, connection_id: str, account_id: str, symbol: str
    ) -> dict[str, Any]:
        """Read a timestamped bid/ask quote for an account symbol."""
        return await service.read("quotes", broker_id, connection_id, account_id, symbol=symbol)

    async def symbol_info(
        broker_id: str, connection_id: str, account_id: str, symbol: str
    ) -> dict[str, Any]:
        """Read account symbol precision and limits; metadata grants no order authority."""
        return await service.read(
            "symbol_info", broker_id, connection_id, account_id, symbol=symbol
        )

    async def bars(
        broker_id: str,
        connection_id: str,
        account_id: str,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Read every bar within explicit UTC millisecond bounds, paged by the provider's own
        limit. Pass `limit` to stop after that many bars."""
        return await service.read(
            "bars",
            broker_id,
            connection_id,
            account_id,
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            until=until,
            limit=limit,
        )

    for function in (account_state, positions, quotes, symbol_info, bars):
        server.tool(annotations={"readOnlyHint": True})(function)
    server.tool(
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
        meta={"money_path": True, "proposal_only": True},
    )(service.propose_order)
    return server


def main() -> None:
    create_server(BrokerService(Path(os.environ.get("QMX_HOME", str(Path.home() / ".qmx"))))).run()
