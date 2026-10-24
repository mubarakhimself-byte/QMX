"""Read-only CCXT spot and cTrader Open API adapters."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from decimal import Decimal
from typing import Any, Protocol, cast

from qmf.core import is_refusal
from qmf.venue.spot import SpotMarket

from qmx_broker.models import Account, Connection
from qmx_broker.registry import Declaration, PublishedLimit, declare

type Document = dict[str, Any]
type Request = Callable[[str, Document], Awaitable[Document]]

CTRADER_DECLARATION = Declaration(
    name="ctrader",
    kind="platform",
    auth="oauth2",
    credential_fields=("clientId", "clientSecret", "accessToken", "refreshToken"),
    environments=("demo", "live"),
    reads=("accounts", "balances", "positions", "quotes", "bars", "instrument_specs"),
    runs_on=("any",),
    session="host",
    limit_signals=("error code 108", "ProtoOAAccountsTokenInvalidatedEvent"),
    limit_scope="connection",
    error_map={"108": "retry", "CH_CLIENT_AUTH_FAILURE": "needs_you", "TOKEN_EXPIRED": "needs_you"},
    health_check="App auth, the account list, account auth and ProtoOAVersionReq",
    published_limits=(
        PublishedLimit(
            "connections per app",
            "one demo and one live connection per registered app",
            "Spotware Open API documentation, method note",
            "2026-10-22",
        ),
    ),
)

CCXT_DECLARATION = Declaration(
    name="ccxt",
    kind="broker",
    auth="api_key",
    credential_fields=("apiKey", "secret", "password"),
    environments=("demo", "live"),
    reads=("balances", "positions", "quotes", "bars", "instrument_specs"),
    runs_on=("any",),
    session="host",
    limit_signals=("HTTP 429 with Retry-After", "HTTP 418"),
    limit_scope="connection",
    error_map={"429": "retry", "418": "retry", "InvalidNonce": "unknown"},
    health_check="Server time, then fetch_balance",
    published_limits=(),
)

MT5_DECLARATION = Declaration(
    name="mt5",
    kind="platform",
    auth="terminal_session",
    credential_fields=("login", "password", "server"),
    environments=("demo", "live"),
    reads=("accounts", "balances", "positions", "quotes", "bars", "instrument_specs"),
    runs_on=("windows", "windows_or_wine"),
    session="host",
    limit_signals=("terminal disconnect", "request timeout"),
    limit_scope="connection",
    error_map={"10004": "retry", "10006": "needs_you", "10009": "retry"},
    health_check="initialize, terminal_info, account_info",
    published_limits=(),
)

declare(CTRADER_DECLARATION, CCXT_DECLARATION, MT5_DECLARATION)
"""The three broker-side types; DR5A declares them and DR5B gives cTrader and MT5 their homes."""


class ReadAdapter(Protocol):
    @property
    def bar_page_limit(self) -> int | None:
        """The provider's own most bars per request, or None when the provider picks the page."""
        ...

    async def account_state(self) -> Document: ...
    async def positions(self) -> list[Document]: ...
    async def quotes(self, symbol: str) -> Document: ...
    async def bars(
        self, symbol: str, timeframe: str, since: int, until: int, limit: int | None
    ) -> list[Document]:
        """One page of bars in `[since, until]`, earliest first."""
        ...

    async def symbol_info(self, symbol: str) -> Document: ...


def scaled(value: object, digits: int) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("Expected an integer wire value")
    return format(Decimal(int(value)).scaleb(-digits), "f")


class CTraderAdapter:
    bar_page_limit: int | None = None

    def __init__(self, account: Account, request: Request, spot: Request) -> None:
        self.account = account
        self.request = request
        self.spot = spot

    async def authenticate(self, connection: Connection, secret: dict[str, str]) -> None:
        await self.request(
            "ProtoOAApplicationAuthReq",
            {"clientId": secret["clientId"], "clientSecret": secret["clientSecret"]},
        )
        accounts = await self.request(
            "ProtoOAGetAccountListByAccessTokenReq", {"accessToken": secret["accessToken"]}
        )
        allowed = [
            item
            for item in accounts.get("ctidTraderAccount", [])
            if str(item["ctidTraderAccountId"]) == self.account.id
            and item.get("isLive") is (connection.environment == "live")
        ]
        if not allowed:
            raise ValueError("Account token does not authorize this account/environment")
        authorized = await self.request(
            "ProtoOAAccountAuthReq",
            {"ctidTraderAccountId": int(self.account.id), "accessToken": secret["accessToken"]},
        )
        if str(authorized.get("ctidTraderAccountId", "")) != self.account.id:
            raise ValueError("Account authentication response belongs to another account")

    async def _read(self, name: str, **values: Any) -> Document:
        result = await self.request(name, {"ctidTraderAccountId": int(self.account.id), **values})
        if str(result.get("ctidTraderAccountId", "")) != self.account.id:
            raise ValueError("cTrader response belongs to another account")
        return result

    async def symbol_info(self, symbol: str) -> Document:
        listing = await self._read("ProtoOASymbolsListReq", includeArchivedSymbols=False)
        matches = [item for item in listing.get("symbol", []) if item.get("symbolName") == symbol]
        if len(matches) != 1:
            raise ValueError("Unknown or ambiguous cTrader symbol; select an active account symbol")
        symbol_id = int(matches[0]["symbolId"])
        result = await self._read("ProtoOASymbolByIdReq", symbolId=[symbol_id])
        details = [item for item in result.get("symbol", []) if int(item["symbolId"]) == symbol_id]
        if len(details) != 1:
            raise ValueError("Missing cTrader symbol metadata")
        return {"symbol": symbol, **details[0]}

    async def account_state(self) -> Document:
        result = await self._read("ProtoOATraderReq")
        trader: Document = result["trader"]
        if str(trader["ctidTraderAccountId"]) != self.account.id:
            raise ValueError("Trader response belongs to another account")
        if "moneyDigits" not in trader:
            raise ValueError("cTrader moneyDigits is missing; refusing to guess a money scale")
        digits = int(trader["moneyDigits"])
        if not 0 <= digits <= 18:
            raise ValueError("Unsupported cTrader moneyDigits")
        return {
            "account_id": self.account.id,
            "currency": self.account.currency,
            "balance": scaled(trader["balance"], digits),
            "leverage": scaled(trader["leverageInCents"], 2)
            if "leverageInCents" in trader
            else self.account.leverage,
        }

    async def positions(self) -> list[Document]:
        result = await self._read("ProtoOAReconcileReq")
        return [
            {
                "position_id": str(item["positionId"]),
                "symbol_id": str(item["tradeData"]["symbolId"]),
                "quantity": scaled(item["tradeData"]["volume"], 2),
                "side": item["tradeData"]["tradeSide"],
                "status": item["positionStatus"],
            }
            for item in result.get("position", [])
        ]

    async def quotes(self, symbol: str) -> Document:
        info = await self.symbol_info(symbol)
        event = await self.spot(
            "ProtoOASubscribeSpotsReq",
            {
                "ctidTraderAccountId": int(self.account.id),
                "symbolId": [int(info["symbolId"])],
                "subscribeToSpotTimestamp": True,
            },
        )
        if str(event.get("ctidTraderAccountId")) != self.account.id or int(
            event.get("symbolId", 0)
        ) != int(info["symbolId"]):
            raise ValueError("Quote belongs to another account/symbol")
        if not all(key in event for key in ("bid", "ask", "timestamp")):
            raise ValueError("Wait for a complete, timestamped cTrader quote")
        return {
            "symbol": symbol,
            "bid": scaled(event["bid"], 5),
            "ask": scaled(event["ask"], 5),
            "timestamp_ms": int(event["timestamp"]),
        }

    async def bars(
        self, symbol: str, timeframe: str, since: int, until: int, limit: int | None
    ) -> list[Document]:
        periods = {
            "1m": "M1",
            "5m": "M5",
            "15m": "M15",
            "30m": "M30",
            "1h": "H1",
            "4h": "H4",
            "1d": "D1",
            "1w": "W1",
        }
        if timeframe not in periods:
            raise ValueError("Use a supported cTrader period: " + ", ".join(periods))
        info = await self.symbol_info(symbol)
        count = {} if limit is None else {"count": limit}
        result = await self._read(
            "ProtoOAGetTrendbarsReq",
            symbolId=int(info["symbolId"]),
            period=periods[timeframe],
            fromTimestamp=since,
            toTimestamp=until,
            **count,
        )
        return [
            {
                "timestamp_ms": int(item["utcTimestampInMinutes"]) * 60000,
                "open": scaled(int(item["low"]) + int(item.get("deltaOpen", 0)), 5),
                "high": scaled(int(item["low"]) + int(item.get("deltaHigh", 0)), 5),
                "low": scaled(item["low"], 5),
                "close": scaled(int(item["low"]) + int(item.get("deltaClose", 0)), 5),
                "volume": str(item["volume"]),
                "volume_unit": "ticks",
            }
            for item in result.get("trendbar", [])
            if since <= int(item["utcTimestampInMinutes"]) * 60000 <= until
        ][:limit]


class CCXTAdapter:
    def __init__(self, exchange: Any) -> None:
        self.exchange = exchange

    @property
    def bar_page_limit(self) -> int | None:
        try:
            limit: object = self.exchange.features["spot"]["fetchOHLCV"]["limit"]
        except AttributeError, KeyError, TypeError:
            return None
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            return None
        return limit

    async def _market(self, symbol: str) -> Document:
        markets = cast("dict[str, Document]", await asyncio.to_thread(self.exchange.load_markets))
        market = markets.get(symbol)
        if (
            not market
            or market.get("spot") is not True
            or market.get("contract") is not False
            or market.get("active") is not True
        ):
            raise ValueError("Select an explicitly active, non-contract spot symbol")
        return market

    async def symbol_info(self, symbol: str) -> Document:
        import ccxt  # pyright: ignore[reportMissingTypeStubs] # noqa: PLC0415 - untyped upstream

        market = await self._market(symbol)
        result: Document = {
            key: market.get(key) for key in ("id", "symbol", "base", "quote", "precision", "limits")
        }
        if self.exchange.precisionMode == ccxt.TICK_SIZE:
            # CCXT metadata uses floats. These are display-only round-trip decimal
            # representations, never order authority or a precision upgrade.
            normalized = {
                **market,
                "precision": {key: str(value) for key, value in market["precision"].items()},
                "limits": {
                    kind: {
                        key: str(value) if value is not None else None
                        for key, value in limits.items()
                    }
                    for kind, limits in market["limits"].items()
                },
            }
            parsed = SpotMarket.from_ccxt_market(normalized, precision_mode="TICK_SIZE")
            if not is_refusal(parsed):
                result["spot_market"] = asdict(parsed.value)
        return result

    async def account_state(self) -> Document:
        balance = cast(Document, await asyncio.to_thread(self.exchange.fetch_balance))
        return {
            "balances": {key: balance.get(key, {}) for key in ("free", "used", "total")},
            "timestamp_ms": balance.get("timestamp"),
            "market_type": "spot",
        }

    async def positions(self) -> list[Document]:
        state = await self.account_state()
        return [
            {"asset": asset, "quantity": str(quantity), "market_type": "spot"}
            for asset, quantity in state["balances"]["total"].items()
            if quantity is not None and Decimal(str(quantity)) != 0
        ]

    async def quotes(self, symbol: str) -> Document:
        await self._market(symbol)
        ticker = cast(Document, await asyncio.to_thread(self.exchange.fetch_ticker, symbol))
        if ticker.get("symbol") != symbol or any(
            ticker.get(key) is None for key in ("bid", "ask", "timestamp")
        ):
            raise ValueError("Exchange did not return a complete, timestamped bid/ask quote")
        return {key: ticker.get(key) for key in ("symbol", "bid", "ask", "timestamp")}

    async def bars(
        self, symbol: str, timeframe: str, since: int, until: int, limit: int | None
    ) -> list[Document]:
        await self._market(symbol)
        rows = cast(
            "list[list[Any]]",
            await asyncio.to_thread(self.exchange.fetch_ohlcv, symbol, timeframe, since, limit),
        )
        return [
            cast(
                Document,
                dict(
                    zip(
                        ("timestamp_ms", "open", "high", "low", "close", "volume"), row, strict=True
                    )
                ),
            )
            for row in rows
            if since <= int(row[0]) <= until
        ][:limit]
