"""Account-scoped reads and a persistent Portfolio signature queue."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import tomllib
from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager, closing
from functools import partial
from pathlib import Path
from typing import Any, cast

from qmf.core import is_refusal
from qmf.venue.proto import compile_descriptor_set

from qmx_broker.adapters import CCXTAdapter, CTraderAdapter, Document, ReadAdapter
from qmx_broker.credentials import credentials
from qmx_broker.ctrader_transport import CTraderTransport
from qmx_broker.models import Account, Broker, BrokerSettings, Connection, OrderProposal

type AdapterFactory = Callable[
    [Broker, Connection, Account], AbstractAsyncContextManager[ReadAdapter]
]


@asynccontextmanager
async def open_adapter(
    broker: Broker,
    connection: Connection,
    account: Account,
    *,
    exchanges: dict[tuple[str, str, str], CCXTAdapter] | None = None,
) -> AsyncGenerator[ReadAdapter]:
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
    if not {"clientId", "clientSecret", "accessToken"} <= secret.keys():
        raise ValueError("cTrader credentials require clientId, clientSecret and accessToken")
    if not connection.protocol_path or connection.protocol_tag is None:
        raise ValueError(
            "Set protocol_path and protocol_tag to the node's pinned FileDescriptorSet"
        )
    compiled = compile_descriptor_set(
        Path(connection.protocol_path).read_bytes(),
        package_name="openapi-proto-messages",
        release_tag=connection.protocol_tag,
    )
    if is_refusal(compiled):
        raise ValueError("Invalid cTrader protocol definitions")
    transport = await CTraderTransport.connect(compiled.value, connection.environment)
    try:
        adapter = CTraderAdapter(account, transport.request, transport.spot)
        await adapter.authenticate(connection, secret)
        yield adapter
    finally:
        await transport.close()


class BrokerService:
    def __init__(
        self,
        home: Path,
        settings: BrokerSettings | None = None,
        factory: AdapterFactory | None = None,
    ) -> None:
        self.home = home.resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self.settings = settings
        self.factory: AdapterFactory = factory or partial(open_adapter, exchanges={})
        # cTrader permits a small number of sessions; concurrent MCP reads share
        # this gate instead of opening a socket for every simultaneous request.
        self._read_lock = asyncio.Lock()
        with closing(sqlite3.connect(self.home / "portfolio.db")) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS order_proposals "
                "(id TEXT PRIMARY KEY, body TEXT NOT NULL)"
            )

    def configured_settings(self) -> BrokerSettings:
        if self.settings is not None:
            return self.settings
        path = self.home / "settings.toml"
        if not path.exists():
            return BrokerSettings()
        with path.open("rb") as file:
            return BrokerSettings.model_validate(tomllib.load(file).get("brokers", {}))

    def list_accounts(self, offset: int = 0, limit: int = 100) -> Document:
        """List configured account identities; use all three ids in subsequent calls."""
        _page(offset, limit)
        accounts = [
            {
                "broker_id": broker.id,
                "broker": broker.name,
                "adapter": broker.adapter,
                "connection_id": connection.id,
                "environment": connection.environment,
                **account.model_dump(exclude={"credential_ref"}),
            }
            for broker in self.configured_settings().brokers
            for connection in broker.connections
            for account in connection.accounts
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
        if operation == "bars" and (
            not 1 <= kwargs["limit"] <= 1000
            or not 0 <= kwargs["since"] < kwargs["until"] <= 2147483646000
        ):
            raise ValueError("Use 0 <= since < until <= 2147483646000 and limit 1..1000")
        try:
            async with self._read_lock, self.factory(broker, connection, account) as adapter:
                return await getattr(adapter, operation)(**kwargs)
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
