from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from test_broker import ExchangeFixture, settings

from qmx_broker.adapters import CCXTAdapter, ReadAdapter
from qmx_broker.models import Account, Broker, Connection
from qmx_broker.service import BrokerService

START = 1700000000000
MINUTE = 60000


class PagedExchange(ExchangeFixture):
    """A spot exchange whose fetch_ohlcv honours `since` and `limit` like a real one."""

    def __init__(self, page_limit: int, bars: int) -> None:
        super().__init__()
        self.features = {"spot": {"fetchOHLCV": {"limit": page_limit}}}
        self.series = [[START + i * MINUTE, 1, 2, 0.5, 1.5, 10] for i in range(bars)]

    def fetch_ohlcv(self, symbol: str, timeframe: str, since: int, limit: int) -> list[list[Any]]:
        self.calls.append(("bars", since, limit))
        return [row for row in self.series if row[0] >= since][:limit]


def read(exchange: PagedExchange, tmp_path: Path, limit: int | None) -> list[dict[str, Any]]:
    @asynccontextmanager
    async def factory(
        broker: Broker, connection: Connection, account: Account
    ) -> AsyncGenerator[ReadAdapter]:
        yield CCXTAdapter(exchange)

    service = BrokerService(tmp_path, settings(), factory)
    return asyncio.run(
        service.read(
            "bars",
            "crypto",
            "demo",
            "101",
            symbol="BTC/USDT",
            timeframe="1m",
            since=START,
            until=START + 2000 * MINUTE,
            limit=limit,
        )
    )


def test_bars_page_by_the_providers_own_limit_and_return_every_bar(tmp_path: Path) -> None:
    exchange = PagedExchange(page_limit=720, bars=1501)
    bars = read(exchange, tmp_path, limit=None)
    assert len(bars) == 1501
    assert bars[-1]["timestamp_ms"] == 1700090000000
    assert exchange.calls == [
        ("bars", 1700000000000, 720),
        ("bars", 1700043140001, 720),
        ("bars", 1700086340001, 720),
        ("bars", 1700090000001, 720),
    ]


def test_a_caller_limit_stops_the_paging_early(tmp_path: Path) -> None:
    exchange = PagedExchange(page_limit=300, bars=1501)
    bars = read(exchange, tmp_path, limit=450)
    assert len(bars) == 450
    assert exchange.calls == [("bars", 1700000000000, 300), ("bars", 1700017940001, 150)]
