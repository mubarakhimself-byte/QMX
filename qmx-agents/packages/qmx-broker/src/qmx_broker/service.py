"""Account-scoped reads and a persistent Portfolio signature queue."""

from __future__ import annotations

import asyncio
import errno
import hashlib
import json
import os
import sqlite3
import time
from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping
from contextlib import AbstractAsyncContextManager, asynccontextmanager, closing
from pathlib import Path
from typing import IO, Any, Final, Protocol, cast

import qmf.venue as venue_package
from qmf.core import is_refusal
from qmf.venue.proto import CompiledProto, compile_descriptor_set
from qmx_home import Layout
from qmx_home.versions import open_sqlite

from qmx_broker.adapters import (
    CCXTAdapter,
    CTraderAdapter,
    Document,
    EnvironmentMismatch,
    LiveGrant,
    ReadAdapter,
    can_trade_live,
)
from qmx_broker.credentials import (
    CTRADER_APP,
    CTRADER_TOKENS,
    THIS_PC,
    CredentialManager,
    KeyStore,
    credentials,
)
from qmx_broker.ctrader_transport import CTraderTransport
from qmx_broker.models import (
    Account,
    Broker,
    BrokerSettings,
    Connection,
    OrderProposal,
    ReadEnvelope,
)
from qmx_broker.oauth import (
    TOKEN_URL,
    AppCredential,
    Fetch,
    OAuthRefused,
    Tokens,
    refresh_tokens,
    urllib_fetch,
)
from qmx_broker.sandbox import demo_refusal

type AdapterFactory = Callable[
    [Broker, Connection, Account], AbstractAsyncContextManager[ReadAdapter]
]

PROTOCOL_SET: Final = Path(venue_package.__file__).resolve().parent / "protocol" / "openapi-91.pb"
"""Spotware's Open API FileDescriptorSet at release tag 91, under the MIT licence beside it."""
PROTOCOL_TAG: Final = 91
REFRESH_LOCK: Final = "ctrader-refresh.lock"
"""In the QMX folder's `keys/`: one process at a time refreshes the cTrader pair."""
SIGN_IN_AGAIN: Final = "sign in to cTrader on This PC again"


class ReadRefused(ValueError):
    """A read QMX could not make: a closed `code` and one plain `line` that says what to do next.
    The line never holds a token, a secret or a URL."""

    def __init__(self, code: str, line: str) -> None:
        super().__init__(line)
        self.code = code
        self.line = line


class Session(Protocol):
    async def request(self, name: str, values: Document) -> Document: ...
    async def spot(self, name: str, values: Document) -> Document: ...
    async def close(self) -> None: ...


type Connect = Callable[[CompiledProto, str], Awaitable[Session]]


def compiled(connection: Connection) -> CompiledProto:
    """The cTrader messages from the connection's pinned FileDescriptorSet, or from the set QMX
    ships when the row names no file."""
    path, tag, row = connection.protocol_path, connection.protocol_tag, connection.id
    if not path and tag in {None, PROTOCOL_TAG}:
        path, tag = str(PROTOCOL_SET), PROTOCOL_TAG
    elif not path:
        raise ReadRefused(
            "protocol_files",
            f"{row} names protocol_tag {tag} but no protocol_path; set both, or clear both to use "
            f"the set QMX ships (tag {PROTOCOL_TAG})",
        )
    elif tag is None:
        raise ReadRefused(
            "protocol_files",
            f"{row} names protocol_path but no protocol_tag; set both, or clear both to use the "
            "set QMX ships",
        )
    use_shipped = f"clear protocol_path and protocol_tag on {row} to use the set QMX ships"
    try:
        raw = Path(path).read_bytes()
    except OSError as error:
        why = "does not exist" if isinstance(error, FileNotFoundError) else "cannot be read"
        raise ReadRefused(
            "protocol_files",
            f"The cTrader protocol file {path} that {row} names {why}; {use_shipped}",
        ) from None
    proto = compile_descriptor_set(raw, package_name="openapi-proto-messages", release_tag=tag)
    if is_refusal(proto):
        raise ReadRefused(
            "protocol_files",
            f"The cTrader protocol file {path} that {row} names is not a tag {tag} set; "
            f"{use_shipped}",
        )
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


def _secret(reference: str) -> dict[str, str]:
    try:
        return credentials(reference)
    except ValueError as error:
        raise ReadRefused("credential_unusable", str(error)) from None


@asynccontextmanager
async def open_adapter(
    broker: Broker,
    connection: Connection,
    account: Account,
    *,
    exchanges: dict[tuple[str, str, str], CCXTAdapter] | None = None,
    keys: KeyStore | None = None,
    connect: Connect = CTraderTransport.connect,
    folder: Path | None = None,
    token_url: str = TOKEN_URL,
    fetch: Fetch = urllib_fetch,
    clock: Callable[[], float] = time.time,
) -> AsyncGenerator[ReadAdapter]:
    """One read session. A cTrader session opens only on This PC as the connection's home: the
    app half comes from the row's `qmx/read/*` entry and the pair from This PC's key store. A
    pair whose expiry has passed is first refreshed at `token_url`, under the lock in `folder`
    (the QMX folder). A grant that can trade live money is refused by name and its pair deleted,
    and a refreshed one is never kept. A refusal is a `ReadRefused`, a `LiveGrant` or an
    `EnvironmentMismatch`."""
    reference = account.credential_ref or connection.credential_ref
    if broker.adapter == "ccxt":
        import ccxt  # pyright: ignore[reportMissingTypeStubs] # noqa: PLC0415 - untyped upstream

        if broker.exchange not in ccxt.exchanges:
            raise ReadRefused(
                "unknown_exchange",
                f"CCXT knows no exchange {broker.exchange}; check {broker.name} in Settings",
            )
        if connection.environment == "demo" and (no_demo := demo_refusal(broker.exchange)):
            raise ReadRefused("no_demo_mode", no_demo)
        secret = _secret(reference)
        if not {"apiKey", "secret"} <= secret.keys():
            raise ReadRefused("credential_unusable", f"{reference} needs apiKey and secret")
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
        raise ReadRefused(
            "signed_in_elsewhere",
            f"{connection.id} is signed in on {connection.home}, so This PC opens no session for "
            f"it; read it from {connection.home}, or sign in to cTrader on This PC",
        )
    secret = _secret(reference)
    if not {"clientId", "clientSecret"} <= secret.keys():
        raise ReadRefused("credential_unusable", f"{CTRADER_APP} needs clientId and clientSecret")
    proto = compiled(connection)
    store = CredentialManager() if keys is None else keys
    raw, held = _held_pair(store)
    if held.due(clock()):
        if folder is None:
            raise ReadRefused("sign_in_ended", f"The cTrader sign-in has expired; {SIGN_IN_AGAIN}")
        async with _one_refresher(folder):
            app = AppCredential(secret["clientId"], secret["clientSecret"])
            raw, held = await _renewed(
                store,
                app,
                connection,
                token_url=token_url,
                fetch=fetch,
                clock=clock,
                connect=connect,
            )
    transport = await connect(proto, connection.environment)
    try:
        adapter = CTraderAdapter(account, transport.request, transport.spot)
        try:
            await adapter.authenticate(connection, {**secret, "accessToken": held.access_token})
        except LiveGrant:
            store.delete(CTRADER_TOKENS)
            raise
        except EnvironmentMismatch:
            raise
        except ValueError:
            if store.read(CTRADER_TOKENS) != raw:
                raise ReadRefused(
                    "sign_in_renewed",
                    "Another QMX process renewed the cTrader sign-in during this read; try again",
                ) from None
            raise ReadRefused(
                "key_refused",
                f"cTrader refused the app key or the sign-in for account {account.id}; check the "
                f"app id and secret in Settings, or {SIGN_IN_AGAIN}",
            ) from None
        yield adapter
    finally:
        await transport.close()


def _held_pair(store: KeyStore) -> tuple[str, Tokens]:
    """The stored pair as written, so a later read can tell whether another writer replaced it,
    and as tokens."""
    raw = store.read(CTRADER_TOKENS)
    if raw is None:
        raise ReadRefused(
            "not_signed_in", "Sign in to cTrader on This PC first; This PC holds no cTrader sign-in"
        )
    return raw, Tokens.from_document(raw)


def _written_meanwhile(store: KeyStore, raw: str) -> tuple[str, Tokens] | None:
    """The pair a sign-in wrote while a refresh ran, which wins over the refresh; the PC sign-in
    writes without the refresh lock, and Credential Manager has no compare-and-set."""
    if store.read(CTRADER_TOKENS) == raw:
        return None
    return _held_pair(store)


async def _renewed(
    store: KeyStore,
    app: AppCredential,
    connection: Connection,
    *,
    token_url: str,
    fetch: Fetch,
    clock: Callable[[], float],
    connect: Connect,
) -> tuple[str, Tokens]:
    """The pair this read uses, renewed in the sign-in's own order: list the new grant's
    accounts, refuse a grant that can trade live money (ruling 135), and only then keep it. A
    pair another reader renewed while this one waited for the lock, or a sign-in wrote while
    this refresh ran, is used as it is. No line holds the token endpoint's own text."""
    raw, held = _held_pair(store)
    if not held.due(clock()):
        return raw, held
    try:
        fresh = await asyncio.to_thread(
            refresh_tokens, app, held.refresh_token, token_url=token_url, fetch=fetch, now=clock()
        )
    except OAuthRefused as refused:
        newer = _written_meanwhile(store, raw)
        if newer is not None:
            return newer
        if refused.code in {"token_endpoint_unreachable", "bad_token_answer"}:
            raise ConnectionError(refused.code) from None
        if refused.code == "unreadable_token_answer":
            raise ReadRefused(
                "token_answer_unreadable",
                "cTrader's token endpoint gave an answer QMX could not read, so the sign-in is "
                "kept; try again, and check [ctrader] token_url in Settings if it repeats",
            ) from None
        if refused.code == "token_url_invalid":
            raise ReadRefused(
                "token_url_invalid",
                "The [ctrader] token_url in Settings is not a web address; fix it, or clear it "
                "to use cTrader's own",
            ) from None
        store.delete(CTRADER_TOKENS)
        raise ReadRefused(
            "sign_in_ended",
            f"The cTrader sign-in has ended: cTrader would not renew it; {SIGN_IN_AGAIN}",
        ) from None
    newer = _written_meanwhile(store, raw)
    if newer is not None:
        return newer
    try:
        listing = await grant_accounts(connection, app, fresh.access_token, connect=connect)
    except Exception as error:  # the check crosses the network; an unchecked pair is never kept
        raise ReadRefused(
            "refresh_unchecked",
            "QMX renewed the cTrader sign-in but could not check its accounts "
            f"({type(error).__name__}), so it kept nothing; {SIGN_IN_AGAIN}",
        ) from None
    if can_trade_live(listing):
        if store.read(CTRADER_TOKENS) == raw:
            store.delete(CTRADER_TOKENS)
        raise LiveGrant
    newer = _written_meanwhile(store, raw)
    if newer is not None:
        return newer
    kept = fresh.document()
    try:
        store.replace(CTRADER_TOKENS, kept)
        stored = store.read(CTRADER_TOKENS)
    except Exception:  # Credential Manager's own failure; the read never uses a pair it lacks
        stored = None
    if stored != kept:
        raise ReadRefused(
            "refresh_not_kept",
            "QMX renewed the cTrader sign-in but could not keep the new pair in Credential "
            f"Manager; {SIGN_IN_AGAIN}",
        )
    return kept, fresh


@asynccontextmanager
async def _one_refresher(folder: Path) -> AsyncGenerator[None]:
    """The QMX folder's one cTrader refresher across processes: an OS lock on
    `keys/ctrader-refresh.lock` that readers take in turn."""
    lock = Layout(folder).keys / REFRESH_LOCK
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+b") as handle:
        await asyncio.to_thread(_take, handle)
        try:
            yield
        finally:
            _give(handle)


def _take(handle: IO[bytes]) -> None:
    if os.name == "nt":
        import msvcrt  # noqa: PLC0415

        while True:
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EDEADLK}:
                    raise
                time.sleep(0.05)
            else:
                return
    else:
        import fcntl  # noqa: PLC0415

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)


def _give(handle: IO[bytes]) -> None:
    if os.name == "nt":
        import msvcrt  # noqa: PLC0415

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl  # noqa: PLC0415

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


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
        ctrader: Callable[[], Mapping[str, object]] | None = None,
    ) -> None:
        self.home = home.resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self.settings = settings
        self.brokers = brokers
        self.ctrader = ctrader
        self._exchanges: dict[tuple[str, str, str], CCXTAdapter] = {}
        self.factory: AdapterFactory = factory or self._open
        # cTrader permits a small number of sessions; concurrent MCP reads share
        # this gate instead of opening a socket for every simultaneous request.
        self._read_lock = asyncio.Lock()
        with closing(sqlite3.connect(self.home / "portfolio.db", isolation_level=None)) as db:
            open_sqlite(db, "portfolio", (PORTFOLIO_SCHEMA,))
            for statement in PORTFOLIO_SCHEMA:
                db.execute(statement)

    def _open(
        self, broker: Broker, connection: Connection, account: Account
    ) -> AbstractAsyncContextManager[ReadAdapter]:
        """A session that refreshes under this QMX folder's lock, at the `[ctrader] token_url`
        the injected reader names, or cTrader's own when it names none."""
        named = self.ctrader().get("token_url") if self.ctrader is not None else None
        return open_adapter(
            broker,
            connection,
            account,
            exchanges=self._exchanges,
            folder=Layout.from_home(self.home).root,
            token_url=str(named or TOKEN_URL),
        )

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
    ) -> ReadEnvelope:
        """One read, stamped from the connection it resolved here and the `is_live` the session
        proved; a stamp that would disagree with the proof fails the read by name."""
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
                is_live = adapter.is_live
                if is_live is None or is_live is not (connection.environment == "live"):
                    raise EnvironmentMismatch(connection.id, connection.environment, is_live)
                if operation == "bars":
                    result = await read_bars(adapter, **kwargs)
                else:
                    result = await getattr(adapter, operation)(**kwargs)
        except LiveGrant, EnvironmentMismatch, ReadRefused:
            raise
        except Exception as error:
            raise _unnamed(broker, account, error) from None
        return {
            "environment": connection.environment,
            "is_live": is_live,
            "connection_id": connection.id,
            "account_id": account.id,
            "result": result,
        }

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


def _unnamed(broker: Broker, account: Account, error: Exception) -> ReadRefused:
    """The plain line for a read that failed with no named refusal, chosen by the failure's
    type; its class name is only a detail."""
    network = (
        f"QMX could not reach {broker.name} to read account {account.id}; check the network and "
        "try again"
    )
    if isinstance(error, OSError | EOFError):
        return ReadRefused("network", network)
    if broker.adapter == "ccxt":
        import ccxt  # pyright: ignore[reportMissingTypeStubs] # noqa: PLC0415 - untyped upstream

        if isinstance(error, ccxt.NetworkError):
            return ReadRefused("network", network)
        if isinstance(error, ccxt.AuthenticationError):
            return ReadRefused(
                "key_refused",
                f"{broker.name} refused the key for account {account.id}; check its API key in "
                "Settings",
            )
    return ReadRefused(
        "read_failed",
        f"QMX could not read account {account.id} at {broker.name}: an unexpected "
        f"{type(error).__name__}; try again",
    )


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
