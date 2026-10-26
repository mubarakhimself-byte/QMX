"""Account-scoped reads and a persistent Portfolio signature queue."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping
from contextlib import AbstractAsyncContextManager, asynccontextmanager, closing
from functools import partial
from pathlib import Path
from typing import Any, Final, Protocol, cast

from qmf.core import is_refusal
from qmf.venue.proto import CompiledProto, compile_descriptor_set
from qmx_home.versions import open_sqlite

from qmx_broker.adapters import CCXTAdapter, CTraderAdapter, Document, LiveGrant, ReadAdapter
from qmx_broker.credentials import (
    CTRADER_APP,
    CTRADER_TOKENS,
    THIS_PC,
    CredentialManager,
    KeyStore,
    credentials,
)
from qmx_broker.ctrader_transport import CTraderTransport
from qmx_broker.models import Account, Broker, BrokerSettings, Connection, OrderProposal
from qmx_broker.oauth import AppCredential, Tokens

type AdapterFactory = Callable[
    [Broker, Connection, Account], AbstractAsyncContextManager[ReadAdapter]
]


class Session(Protocol):
    async def request(self, name: str, values: Document) -> Document: ...
    async def spot(self, name: str, values: Document) -> Document: ...
    async def close(self) -> None: ...


type Connect = Callable[[CompiledProto, str], Awaitable[Session]]


def compiled(connection: Connection) -> CompiledProto:
    """The cTrader messages from the connection's pinned FileDescriptorSet."""
    if not connection.protocol_path or connection.protocol_tag is None:
        raise ValueError(
            "Set protocol_path and protocol_tag to the node's pinned FileDescriptorSet"
        )
    proto = compile_descriptor_set(
        Path(connection.protocol_path).read_bytes(),
        package_name="openapi-proto-messages",
        release_tag=connection.protocol_tag,
    )
    if is_refusal(proto):
        raise ValueError("Invalid cTrader protocol definitions")
    return proto.value


async def grant_accounts(
    connection: Connection,
    app: AppCredential,
    access_token: str,
    *,
    connect: Connect = CTraderTransport.connect,
) -> Document:
    """A fresh grant's account list, read once over one session, so its home can refuse a grant
    that can trade live money before it keeps the pair (ruling 135)."""
    session = await connect(compiled(connection), connection.environment)
    try:
        await session.request(
            "ProtoOAApplicationAuthReq",
            {"clientId": app.client_id, "clientSecret": app.client_secret},
        )
        return await session.request(
            "ProtoOAGetAccountListByAccessTokenReq", {"accessToken": access_token}
        )
    finally:
        await session.close()


@asynccontextmanager
async def open_adapter(
    broker: Broker,
    connection: Connection,
    account: Account,
    *,
    exchanges: dict[tuple[str, str, str], CCXTAdapter] | None = None,
    keys: KeyStore | None = None,
    connect: Connect = CTraderTransport.connect,
) -> AsyncGenerator[ReadAdapter]:
    """One read session. A cTrader session opens only on This PC as the connection's home: the
    app half comes from the row's `qmx/read/*` entry and the access token from This PC's key
    store. A grant that can trade live money is refused by name and its pair deleted."""
    secret = credentials(account.credential_ref or connection.credential_ref)
    if broker.adapter == "ccxt":
        import ccxt  # pyright: ignore[reportMissingTypeStubs] # noqa: PLC0415 - untyped upstream

        if broker.exchange not in ccxt.exchanges:
            raise ValueError("Unknown CCXT exchange id")
        if not {"apiKey", "secret"} <= secret.keys():
            raise ValueError("CCXT credentials require apiKey and secret")
        # CCXT's limiter belongs to the instance. Reuse it for the same key pair
        # and environment; rotating vault credentials creates a fresh instance.
        identity = (
            broker.exchange,
            connection.environment,
            hashlib.sha256(json.dumps(secret, sort_keys=True).encode()).hexdigest(),
        )
        if exchanges is not None and identity in exchanges:
            yield exchanges[identity]
            return
        exchange_class: Any = getattr(ccxt, broker.exchange)
        exchange: Any = exchange_class(
            {
                **secret,
                "enableRateLimit": True,
                "timeout": 10000,
                "options": {"defaultType": "spot"},
            }
        )
        if connection.environment == "demo":
            exchange.set_sandbox_mode(True)
        adapter = CCXTAdapter(exchange)
        if exchanges is not None:
            exchanges[identity] = adapter
        yield adapter
        return
    if connection.home != THIS_PC:
        raise ValueError(
            f"{connection.id} is signed in on {connection.home}; This PC opens no session for it"
        )
    if not {"clientId", "clientSecret"} <= secret.keys():
        raise ValueError(f"{CTRADER_APP} needs clientId and clientSecret")
    proto = compiled(connection)
    store = CredentialManager() if keys is None else keys
    held = store.read(CTRADER_TOKENS)
    if held is None:
        raise ValueError("Sign in to cTrader on This PC first")
    transport = await connect(proto, connection.environment)
    try:
        adapter = CTraderAdapter(account, transport.request, transport.spot)
        try:
            await adapter.authenticate(
                connection, {**secret, "accessToken": Tokens.from_document(held).access_token}
            )
        except LiveGrant:
            store.delete(CTRADER_TOKENS)
            raise
        yield adapter
    finally:
        await transport.close()


PORTFOLIO_SCHEMA: Final = (
    "CREATE TABLE IF NOT EXISTS order_proposals (id TEXT PRIMARY KEY, body TEXT NOT NULL)",
)
"""`portfolio.db` at version 1 (design 62 B1)."""


class BrokerService:
    def __init__(
        self,
        home: Path,
        settings: BrokerSettings | None = None,
        factory: AdapterFactory | None = None,
        *,
        brokers: Callable[[], Mapping[str, object]] | None = None,
    ) -> None:
        self.home = home.resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self.settings = settings
        self.brokers = brokers
        self.factory: AdapterFactory = factory or partial(open_adapter, exchanges={})
        # cTrader permits a small number of sessions; concurrent MCP reads share
        # this gate instead of opening a socket for every simultaneous request.
        self._read_lock = asyncio.Lock()
        with closing(sqlite3.connect(self.home / "portfolio.db", isolation_level=None)) as db:
            open_sqlite(db, "portfolio", (PORTFOLIO_SCHEMA,))
            for statement in PORTFOLIO_SCHEMA:
                db.execute(statement)

    def configured_settings(self) -> BrokerSettings:
        """`settings` when given, else the `connections` section from the reader the composition
        injects, which is `ControlService.settings_get` (AD-52); the reader also serves the old
        `brokers` section, which it has already read into `connections`. With neither, no
        accounts."""
        if self.settings is not None:
            return self.settings
        if self.brokers is None:
            return BrokerSettings()
        return BrokerSettings.model_validate(self.brokers())

    def list_connections(self, offset: int = 0, limit: int = 100) -> Document:
        """Read-only rows over enabled accounts: one row per connection, with its scope and home.

        The row carries no secret and no read operation: only the identity fields, the enabled
        accounts and the connection's declared home. Every tool over these rows is read-only.
        """
        _page(offset, limit)
        rows = [
            {
                "provider_id": broker.id,
                "provider": broker.name,
                "kind": broker.kind,
                "adapter": broker.adapter,
                "exchange": broker.exchange,
                "connection_id": connection.id,
                "environment": connection.environment,
                "scope": connection.scope,
                "home": connection.home,
                "accounts": [
                    account.model_dump(exclude={"credential_ref"})
                    for account in connection.accounts
                    if account.enabled
                ],
                "enabled_accounts": sum(1 for account in connection.accounts if account.enabled),
            }
            for broker in self.configured_settings().providers
            for connection in broker.connections
        ]
        return {"connections": rows[offset : offset + limit], "total": len(rows)}

    def list_accounts(self, offset: int = 0, limit: int = 100) -> Document:
        """List configured account identities; use all three ids in subsequent calls."""
        _page(offset, limit)
        accounts = [
            {
                "broker_id": broker.id,
                "broker": broker.name,
                "kind": broker.kind,
                "adapter": broker.adapter,
                "connection_id": connection.id,
                "environment": connection.environment,
                "scope": connection.scope,
                "home": connection.home,
                **account.model_dump(exclude={"credential_ref"}),
            }
            for broker in self.configured_settings().providers
            for connection in broker.connections
            for account in connection.accounts
            if account.enabled
        ]
        return {"accounts": accounts[offset : offset + limit], "total": len(accounts)}

    async def read(
        self, operation: str, broker_id: str, connection_id: str, account_id: str, **kwargs: Any
    ) -> Any:
        broker, connection, account = self.configured_settings().resolve(
            broker_id, connection_id, account_id
        )
        if "read" not in account.permissions:
            raise ValueError("Enable read permission for this account in node settings")
        if operation not in {"account_state", "positions", "quotes", "bars", "symbol_info"}:
            raise ValueError("Unknown read operation")
        # 2147483646000 is a millisecond timestamp (January 2038), not a capacity number.
        if operation == "bars" and (
            (kwargs["limit"] is not None and kwargs["limit"] < 1)
            or not 0 <= kwargs["since"] < kwargs["until"] <= 2147483646000
        ):
            raise ValueError(
                "Use 0 <= since < until <= 2147483646000, and limit >= 1 or no limit for every bar"
            )
        try:
            async with self._read_lock, self.factory(broker, connection, account) as adapter:
                if operation == "bars":
                    return await read_bars(adapter, **kwargs)
                return await getattr(adapter, operation)(**kwargs)
        except LiveGrant:
            raise
        except Exception:
            raise ValueError(
                "Broker read failed; check credentials, network and node protocol settings"
            ) from None

    def propose_order(self, proposal: OrderProposal) -> Document:
        """Persist an unsigned proposal; this method never opens a broker connection."""
        proposal = OrderProposal.model_validate(proposal)
        _, connection, account = self.configured_settings().resolve(
            proposal.broker_id, proposal.connection_id, proposal.account_id
        )
        if "propose" not in account.permissions:
            raise ValueError("Enable propose permission for this account in node settings")
        body = proposal.model_dump(mode="json")
        body["environment"] = connection.environment
        encoded = json.dumps(body, sort_keys=True, separators=(",", ":"))
        proposal_id = hashlib.sha256(encoded.encode()).hexdigest()
        with closing(sqlite3.connect(self.home / "portfolio.db", timeout=5)) as db, db:
            db.execute(
                "INSERT OR IGNORE INTO order_proposals VALUES (?, ?)", (proposal_id, encoded)
            )
        return {
            "proposal_id": proposal_id,
            "status": "awaiting_operator_signature",
            "executed": False,
        }

    def proposals(self, offset: int = 0, limit: int = 100) -> list[Document]:
        """Read the unsigned Portfolio queue; signing and execution belong to QMN."""
        return read_proposals(self.home, offset, limit)


async def read_bars(
    adapter: ReadAdapter, symbol: str, timeframe: str, since: int, until: int, limit: int | None
) -> list[Document]:
    """Every bar in `[since, until]`, or the first `limit`, paged by the provider's own limit."""
    page = adapter.bar_page_limit
    rows: list[Document] = []
    cursor = since
    while cursor <= until and (limit is None or len(rows) < limit):
        wanted = page if limit is None else min(page or limit, limit - len(rows))
        batch = [
            row
            for row in await adapter.bars(symbol, timeframe, cursor, until, wanted)
            if cursor <= int(row["timestamp_ms"]) <= until
        ]
        if not batch:
            break
        rows.extend(batch)
        cursor = max(int(row["timestamp_ms"]) for row in batch) + 1
    return rows[:limit]


def _page(offset: int, limit: int) -> None:
    if offset < 0 or not 1 <= limit <= 1000:
        raise ValueError("Use offset >= 0 and limit 1..1000")


def read_proposals(home: Path, offset: int = 0, limit: int = 100) -> list[Document]:
    """The control door opens the broker-owned queue strictly read-only."""
    _page(offset, limit)
    path = home.resolve() / "portfolio.db"
    if not path.exists():
        return []
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        rows = db.execute(
            "SELECT id, body FROM order_proposals ORDER BY rowid LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [
        {
            "proposal_id": row[0],
            "proposal": cast(Document, json.loads(row[1])),
            "status": "awaiting_operator_signature",
            "executed": False,
        }
        for row in rows
    ]
