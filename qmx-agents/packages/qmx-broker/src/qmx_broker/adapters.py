"""Read-only CCXT (spot, perpetual and dated futures) and cTrader Open API adapters."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from decimal import Decimal
from typing import Any, Literal, Protocol, cast

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

    @property
    def is_live(self) -> bool | None:
        """Whether this session reads a live account, as the provider proved it; None before the
        proof, which no read accepts."""
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


class LiveGrant(ValueError):
    """A cTrader sign-in that can trade a live account. It belongs only on a trading server, so
    every QMX host refuses it by name (ruling 135)."""

    code = "live_trading_grant"
    message = (
        "this sign-in can trade live money; it belongs on a trading server. "
        "Sign in again with view-only access, or tick demo accounts only"
    )

    def __init__(self) -> None:
        super().__init__(f"{self.code}: {self.message}")


class EnvironmentMismatch(ValueError):
    """A read whose session proved another kind than its connection says, so its figure would
    carry the wrong label. The read fails rather than say demo over live money or the reverse.
    The message names both kinds and points at the connection, never at a switch of its kind,
    because a switch may be exactly what would read the live account."""

    code = "environment_mismatch"

    def __init__(self, connection_id: str, environment: str, is_live: bool | None) -> None:
        proved = (
            "proved neither demo nor live"
            if is_live is None
            else f"proved a {'live' if is_live else 'demo'} account"
        )
        super().__init__(
            f"{self.code}: connection {connection_id} says {environment}, but its broker session"
            f" {proved}, so nothing was read. Check this connection in Settings"
        )


def can_trade_live(listing: Document) -> bool:
    """A grant can trade live money when its scope is not view-only and it lists a live account.

    An unreported scope counts as able to trade, the way P-CTSCOPE reads it: only cTrader's own
    `SCOPE_VIEW` proves a grant cannot place an order.
    """
    trades = listing.get("permissionScope") != "SCOPE_VIEW"
    return trades and any(
        item.get("isLive") is True for item in listing.get("ctidTraderAccount", [])
    )


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
        self.is_live: bool | None = None

    async def authenticate(self, connection: Connection, secret: dict[str, str]) -> None:
        await self.request(
            "ProtoOAApplicationAuthReq",
            {"clientId": secret["clientId"], "clientSecret": secret["clientSecret"]},
        )
        accounts = await self.request(
            "ProtoOAGetAccountListByAccessTokenReq", {"accessToken": secret["accessToken"]}
        )
        if can_trade_live(accounts):
            raise LiveGrant
        listed = [
            item.get("isLive")
            for item in accounts.get("ctidTraderAccount", [])
            if str(item["ctidTraderAccountId"]) == self.account.id
        ]
        if len(listed) != 1 or not isinstance(listed[0], bool):
            raise ValueError("Account token does not authorize this account/environment")
        if listed[0] is not (connection.environment == "live"):
            raise EnvironmentMismatch(connection.id, connection.environment, listed[0])
        authorized = await self.request(
            "ProtoOAAccountAuthReq",
            {"ctidTraderAccountId": int(self.account.id), "accessToken": secret["accessToken"]},
        )
        if str(authorized.get("ctidTraderAccountId", "")) != self.account.id:
            raise ValueError("Account authentication response belongs to another account")
        self.is_live = listed[0]

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


type MarketKind = Literal["spot", "swap", "future"]
MARKET_NAMES: dict[MarketKind, str] = {
    "spot": "spot",
    "swap": "perpetual",
    "future": "dated futures",
}


def market_kind(market: Document) -> MarketKind | None:
    """The one kind CCXT classes an active market as, or None for an inactive market and for
    one whose flags disagree or that is neither spot, perpetual nor dated futures (an option)."""
    if market.get("active") is not True:
        return None
    if market.get("spot") is True and market.get("contract") is False:
        return "spot"
    kind = market.get("type")
    if (
        market.get("contract") is True
        and market.get("spot") is False
        and kind in ("swap", "future")
        and market.get(kind) is True
    ):
        return cast("MarketKind", kind)
    return None


def text(value: object) -> str | None:
    """A CCXT number as decimal text. CCXT parses the venue's decimal text into a float whose
    shortest repr gives that text back, so this reads the repr, never the binary value."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise ValueError("Expected a number from the exchange")
    return format(Decimal(str(value)), "f")


class CCXTAdapter:
    """Reads only: spot, perpetual and dated futures markets, and never an order call (Level 0
    blast-radius item 8)."""

    def __init__(self, exchange: Any, clock: Callable[[], int] = time.time_ns) -> None:
        self.exchange = exchange
        self.clock = clock

    @property
    def is_live(self) -> bool:
        """False when `set_sandbox_mode(True)` took: CCXT's base sets `isSandboxModeEnabled` when it
        swaps in the test endpoints, and Bitget's override sets only `options["sandboxMode"]`
        (demo trading by header). In ccxt 4.5.85 no exchange proves demo a third way."""
        options: object = getattr(self.exchange, "options", None)
        sandboxed = getattr(self.exchange, "isSandboxModeEnabled", False) is True or (
            isinstance(options, dict)
            and cast("dict[str, object]", options).get("sandboxMode") is True
        )
        return not sandboxed

    @property
    def bar_page_limit(self) -> int | None:
        try:
            limit: object = self.exchange.features["spot"]["fetchOHLCV"]["limit"]
        except AttributeError, KeyError, TypeError:
            return None
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            return None
        return limit

    async def _market(self, symbol: str, *kinds: MarketKind) -> Document:
        """The market `symbol` names when CCXT classes it, active, as one of `kinds` (any kind
        when none is named)."""
        markets = cast("dict[str, Document]", await asyncio.to_thread(self.exchange.load_markets))
        market = markets.get(symbol)
        allowed = kinds or tuple(MARKET_NAMES)
        if market is None or market_kind(market) not in allowed:
            names = [MARKET_NAMES[kind] for kind in allowed]
            named = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]
            raise ValueError(f"Select an explicitly active {named} symbol")
        return market

    async def symbol_info(self, symbol: str) -> Document:
        import ccxt  # pyright: ignore[reportMissingTypeStubs] # noqa: PLC0415 - untyped upstream

        market = await self._market(symbol)
        market_type = market_kind(market)
        result: Document = {
            key: market.get(key) for key in ("id", "symbol", "base", "quote", "precision", "limits")
        }
        result["market_type"] = market_type
        if market_type != "spot":
            result["contract"] = {
                "settle": market.get("settle"),
                "contract_size": text(market.get("contractSize")),
                "linear": market.get("linear"),
                "expiry_ms": market.get("expiry"),
            }
        elif self.exchange.precisionMode == ccxt.TICK_SIZE:
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

    async def contract_positions(self) -> list[Document]:
        """Open perpetual and dated futures positions. A read apart from `positions`, so a spot
        account's read never depends on the exchange's contract endpoints (Coinbase, for one,
        refuses `fetch_positions` without a portfolio). `quantity` counts contracts, and
        `contract_size` converts them to the base."""
        has: object = getattr(self.exchange, "has", None)
        if (
            not isinstance(has, dict)
            or cast("dict[str, object]", has).get("fetchPositions") is not True
        ):
            raise ValueError("This exchange reads no contract positions through CCXT")
        found = cast("list[Document]", await asyncio.to_thread(self.exchange.fetch_positions))
        markets = cast("dict[str, Document]", self.exchange.markets)
        rows: list[Document] = []
        for position in found:
            if not position.get("contracts"):
                continue
            market = markets.get(str(position.get("symbol")), {})
            size = position.get("contractSize") or market.get("contractSize")
            rows.append(
                {
                    "symbol": position.get("symbol"),
                    "market_type": market.get("type"),
                    "side": position.get("side"),
                    "quantity": text(position.get("contracts")),
                    "contract_size": text(size),
                    "entry_price": text(position.get("entryPrice")),
                    "notional": text(position.get("notional")),
                    "unrealized_pnl": text(position.get("unrealizedPnl")),
                    "liquidation_price": text(position.get("liquidationPrice")),
                    "leverage": text(position.get("leverage")),
                    "margin_mode": position.get("marginMode"),
                    "venue_time_ms": position.get("timestamp"),
                }
            )
        return rows

    async def funding(self, symbol: str) -> Document:
        """A perpetual's current funding rate and when it is paid. `venue_time_ms` is the venue's
        own stamp, None when it sends none (Hyperliquid); `read_at_ms` is this machine's clock
        when the answer arrived."""
        await self._market(symbol, "swap")
        rate = cast(Document, await asyncio.to_thread(self.exchange.fetch_funding_rate, symbol))
        return {
            "symbol": symbol,
            "rate": text(rate.get("fundingRate")),
            "interval": rate.get("interval"),
            "pays_at_ms": rate.get("fundingTimestamp"),
            "mark_price": text(rate.get("markPrice")),
            "index_price": text(rate.get("indexPrice")),
            "venue_time_ms": rate.get("timestamp"),
            "read_at_ms": self.clock() // 1_000_000,
        }

    async def open_interest(self, symbol: str) -> Document:
        """A perpetual's or dated future's open interest, `amount` in contracts as the venue
        counts them, with the venue's stamp (None when it sends none) and `read_at_ms`."""
        await self._market(symbol, "swap", "future")
        interest = cast(
            Document, await asyncio.to_thread(self.exchange.fetch_open_interest, symbol)
        )
        return {
            "symbol": symbol,
            "amount": text(interest.get("openInterestAmount")),
            "value": text(interest.get("openInterestValue")),
            "venue_time_ms": interest.get("timestamp"),
            "read_at_ms": self.clock() // 1_000_000,
        }

    async def book(self, symbol: str, depth: int | None) -> Document:
        """The top `depth` levels a side (the venue's default when None), bids then asks, named
        as the data route's `book` event names them."""
        await self._market(symbol)
        book = cast(
            Document, await asyncio.to_thread(self.exchange.fetch_order_book, symbol, depth)
        )
        return {
            "instrument": symbol,
            "levels": [
                {"side": side, "price": text(level[0]), "size": text(level[1])}
                for side, key in (("bid", "bids"), ("ask", "asks"))
                for level in book[key]
            ],
            "kind": "snapshot",
            "venue_time_ms": book.get("timestamp"),
            "read_at_ms": self.clock() // 1_000_000,
        }

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
