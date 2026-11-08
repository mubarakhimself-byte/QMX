"""The CCXT read adapter reads perpetual and dated futures markets on the pinned CCXT.

Each test drives a real CCXT 4.5.85 exchange class whose HTTP layer answers from
`fixtures/ccxt-contracts/`, raw public answers recorded on 2026-11-01 with no key (built by
evidence/c07/owner-build-fixtures.py). A request the fixture does not hold fails the test, so
no read reaches the network and no order endpoint is ever answered.
"""

from __future__ import annotations

import asyncio
import copy
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import ccxt  # pyright: ignore[reportMissingTypeStubs] - untyped upstream
import pytest

from qmx_broker.adapters import CCXTAdapter, Document

FIXTURES = Path(__file__).parent / "fixtures" / "ccxt-contracts"
READ_AT_MS = 1793574810000
"""This machine's clock in the tests, a little after the recorded answers."""
WALLET = "0x0000000000000000000000000000000000000001"
HYPERLIQUID_INFO = "https://api.hyperliquid.xyz/info"


def body(**fields: str) -> str:
    """A request body as CCXT writes it."""
    return json.dumps(fields, separators=(",", ":"))


SYNTHETIC_ACCOUNT = {
    ("POST", HYPERLIQUID_INFO, body(type="spotClearinghouseState", user=WALLET)): {
        "balances": [
            {"coin": "USDC", "token": 0, "hold": "0.0", "total": "250.5", "entryNtl": "0.0"}
        ]
    },
    ("POST", HYPERLIQUID_INFO, body(type="clearinghouseState", user=WALLET)): {
        "assetPositions": [
            {
                "position": {
                    "coin": "BTC",
                    "entryPx": "77950.0",
                    "leverage": {"type": "cross", "value": 5},
                    "liquidationPx": "62500.5",
                    "marginUsed": "31.18",
                    "positionValue": "155.9",
                    "szi": "-0.002",
                    "unrealizedPnl": "0.04",
                },
                "type": "oneWay",
            }
        ],
        "time": 1793574800000,
    },
}
"""A made-up account in the shape of Hyperliquid's documented answers, for a zero-like wallet:
the recordings hold no account."""


def recorded(
    name: str, extra: Mapping[tuple[str, str, str], Any] | None = None, **config: Any
) -> Any:
    fixture = json.loads((FIXTURES / f"{name}.json").read_text("utf-8"))
    exchange: Any = getattr(ccxt, name)(config)
    exchange.set_markets(fixture["markets"])
    answers = {(r["method"], r["url"], r["body"]): r["response"] for r in fixture["responses"]}
    answers.update(extra or {})

    def fetch(url: str, method: str = "GET", headers: Any = None, body: Any = None) -> Any:
        del headers
        key = (method, url, body or "")
        if key not in answers:
            raise AssertionError(f"no recorded answer for {key}")
        return copy.deepcopy(answers[key])

    exchange.fetch = fetch
    exchange.milliseconds = lambda: READ_AT_MS
    return exchange


def adapter(
    name: str, extra: Mapping[tuple[str, str, str], Any] | None = None, **config: Any
) -> CCXTAdapter:
    return CCXTAdapter(recorded(name, extra, **config), clock=lambda: READ_AT_MS * 1_000_000)


@pytest.mark.parametrize(
    ("name", "symbol", "funding", "interest"),
    [
        (
            "hyperliquid",
            "BTC/USDC:USDC",
            {
                "rate": "0.0000125",
                "interval": "1h",
                "pays_at_ms": 1793577600000,
                "mark_price": "78118.0",
                "index_price": "78141.3",
                "venue_time_ms": None,
            },
            {"amount": "39810.71082", "value": None, "venue_time_ms": None},
        ),
        (
            "binance",
            "BTC/USDT:USDT",
            {
                "rate": "0.0001",
                "interval": None,
                "pays_at_ms": 1793577600000,
                "mark_price": "78109.47776812",
                "index_price": "78135.71478261",
                "venue_time_ms": 1793574796000,
            },
            {"amount": "95712.885", "value": None, "venue_time_ms": 1793574791641},
        ),
        (
            "bybit",
            "BTC/USDT:USDT",
            {
                "rate": "0.0001",
                "interval": "8h",
                "pays_at_ms": 1793577600000,
                "mark_price": "78110.8",
                "index_price": "78144.16",
                "venue_time_ms": 1793574804042,
            },
            {"amount": "68202.978", "value": None, "venue_time_ms": 1793574000000},
        ),
    ],
)
def test_a_perps_funding_and_open_interest_read_with_their_timestamps(
    name: str, symbol: str, funding: Document, interest: Document
) -> None:
    """Hyperliquid stamps neither answer, so only this machine's read time dates them."""
    read = adapter(name)
    stamps = {"symbol": symbol, "read_at_ms": READ_AT_MS}
    assert asyncio.run(read.funding(symbol)) == {**stamps, **funding}
    assert asyncio.run(read.open_interest(symbol)) == {**stamps, **interest}


def test_a_dated_future_reads_open_interest_and_only_perpetuals_read_funding() -> None:
    read = adapter("binance")
    assert asyncio.run(read.open_interest("BTC/USDT:USDT-261225")) == {
        "symbol": "BTC/USDT:USDT-261225",
        "amount": "581.834",
        "value": None,
        "venue_time_ms": 1793574787247,
        "read_at_ms": READ_AT_MS,
    }
    for symbol in ("BTC/USDT:USDT-261225", "BTC/USDT"):
        with pytest.raises(ValueError, match=r"^Select an explicitly active perpetual symbol$"):
            asyncio.run(read.funding(symbol))
    with pytest.raises(ValueError, match=r"perpetual or dated futures symbol$"):
        asyncio.run(read.open_interest("BTC/USDT"))


def test_a_perps_book_and_contract_facts_read() -> None:
    read = adapter("binance")
    book = asyncio.run(read.book("BTC/USDT:USDT", 5))
    assert (book["instrument"], book["kind"], book["read_at_ms"]) == (
        "BTC/USDT:USDT",
        "snapshot",
        READ_AT_MS,
    )
    assert book["levels"][:2] + book["levels"][5:6] == [
        {"side": "bid", "price": "78108.5", "size": "4.219"},
        {"side": "bid", "price": "78108.4", "size": "0.043"},
        {"side": "ask", "price": "78108.6", "size": "6.131"},
    ]
    assert len(book["levels"]) == 10
    info = asyncio.run(read.symbol_info("BTC/USDT:USDT-261225"))
    assert (info["market_type"], info["contract"]) == (
        "future",
        {"settle": "USDT", "contract_size": "1.0", "linear": True, "expiry_ms": 1798185600000},
    )


def test_open_perp_positions_read_on_their_own_beside_spot_holdings() -> None:
    """The exchange is set up as `open_adapter` sets every CCXT session up, spot by default.
    The spot read is answered without the perps account, so it never asks for it."""
    spot_only = {key: answer for key, answer in SYNTHETIC_ACCOUNT.items() if "spot" in key[2]}
    config: dict[str, Any] = {"walletAddress": WALLET, "options": {"defaultType": "spot"}}
    assert asyncio.run(adapter("hyperliquid", spot_only, **config).positions()) == [
        {"asset": "USDC", "quantity": "250.5", "market_type": "spot"}
    ]
    read = adapter("hyperliquid", SYNTHETIC_ACCOUNT, **config)
    assert asyncio.run(read.contract_positions()) == [
        {
            "symbol": "BTC/USDC:USDC",
            "market_type": "swap",
            "side": "short",
            "quantity": "0.002",
            "contract_size": "1.0",
            "entry_price": "77950.0",
            "notional": "155.9",
            "unrealized_pnl": "0.04",
            "liquidation_price": "62500.5",
            "leverage": "5.0",
            "margin_mode": "cross",
            "venue_time_ms": None,
        },
    ]
