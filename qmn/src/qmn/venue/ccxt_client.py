"""The ``ccxt`` venue client: the node's orders on Hyperliquid through the pinned CCXT class.

Level 0 AD-41; Part C AD-306, AD-308 and ``EXTERNAL.md`` section 3. The client answers the node
runtime's :class:`~qmn.app.runtime.VenueAccount` seam, the one the order path sends to, by
mapping each command onto CCXT's unified calls. qmn never imports CCXT: the root workspace does
not lock it. The composition root makes the exchange from ``ccxt.hyperliquid`` 4.5.85 with
:func:`hyperliquid_config` and hands it in, typed by the calls this client makes
(:class:`Exchange`, with CCXT's own method names).

- An entry is an IOC order tagged with its :func:`cloid`. Its stop reaches the venue right after
  the fill as a reduce-only stop trigger with grouping ``positionTpsl``, which CCXT sends as a
  whole-position order of size 0, so it follows partial and later fills (the
  ``position-trigger-after-fill`` form).
- A tightened stop is placed before the stop it replaces is cancelled, so the position is never
  bare. A close is a reduce-only IOC order for the quantity the node holds.
- Every CCXT error class has one reading in :data:`ERRORS`. A class missing from the table, or
  anything else raised, reads UNKNOWN and raises the ``venue_error_unmapped`` alarm. Nothing here
  sends an order again: an UNKNOWN entry waits for the reconciler (C-12b).
- No entry goes while the account holds ``open_orders_margin`` open orders, which keeps room
  under Hyperliquid's 1,000 for stops and closes (EX-11).
- The client binds testnet only. A mainnet binding is the deliberate live path of C-21.
"""

from __future__ import annotations

import base64
import hashlib
import inspect
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Final, Protocol, TypeVar, cast
from urllib.parse import urlsplit

from qmb.host.unit_handler import FillKind
from qmf.core import (
    Account,
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
    VenueId,
)
from qmf.venue.commands import CommandKind, SubmissionOutcome
from qml.unit.model import Side

from qmn.app.attribution import OrderState, ReadBack, VenueOrder, VenuePosition
from qmn.app.runtime import Sent, Ticket, VenueClose
from qmn.order.protection import POSITION_TRIGGER_AFTER_FILL_FORM
from qmn.venue.port import VenueClientKind

__all__ = [
    "AGENT_WALLET_RENEWAL_DAYS",
    "ERRORS",
    "KEYS_SCHEMA",
    "MARKET_SLIPPAGE",
    "OPEN_ORDERS_MARGIN",
    "PINNED_CCXT_VERSION",
    "POLL_NS",
    "TESTNET_HOST",
    "AgentKey",
    "AgentWallet",
    "Buildable",
    "CcxtClient",
    "Configurable",
    "ErrorReading",
    "Exchange",
    "agent_wallets",
    "api_urls",
    "cloid",
    "cloid_tag",
    "hyperliquid_config",
    "make_testnet_exchange",
    "read_error",
    "renewal_due",
]

PINNED_CCXT_VERSION: Final = "4.5.85"
"""The CCXT the mapping was written and checked against. Any other version is refused until the
mapping is checked again (``EXTERNAL.md`` section 9)."""
OPEN_ORDERS_MARGIN: Final = 900
"""`[node] open_orders_margin`, starting at 900 of Hyperliquid's 1,000 open orders."""
AGENT_WALLET_RENEWAL_DAYS: Final = 14
"""`[node] agent_wallet_renewal_days`, starting at 14: the renewal card shows this many days
before an agent wallet expires."""
POLL_NS: Final = 1_000_000_000
"""`[node] ccxt_poll_ms`, starting at 1,000: the client reads the account at most this often to
see a stop fire or a stop land."""
MARKET_SLIPPAGE: Final = "0.05"
"""`[node] ccxt_market_slippage`, starting at CCXT's own 5%: Hyperliquid has no market order, so
CCXT sends an IOC limit this far through the reference price."""
SETTLE: Final = "USDC"
TESTNET_HOST: Final = "api.hyperliquid-testnet.xyz"
KEYS_SCHEMA: Final = "qmx.node.keys/1"
STOP_FORMS: Final[Mapping[str, str]] = {"market": POSITION_TRIGGER_AFTER_FILL_FORM}

_ADDRESS: Final = re.compile(r"0x[0-9a-fA-F]{40}")
_SIGNER: Final = re.compile(r"0x[0-9a-fA-F]{64}")
_NODE_NAME: Final = re.compile(r"q([a-z2-7]{8})-.+")
_CLOID_MARK: Final = "716d"
"""``qm``: the two bytes that open every cloid this node mints, before its tag."""
_CLOID: Final = re.compile(rf"0x{_CLOID_MARK}([0-9a-f]{{10}})([0-9a-f]{{18}})")
_CROCKFORD: Final = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_EPOCH: Final = datetime(1970, 1, 1, tzinfo=UTC)
_T = TypeVar("_T")
_E = TypeVar("_E", bound="Buildable")


# --- the agent wallet in the keys document ----------------------------------------------------


class AgentKey:
    """An agent wallet's signing key. It never prints. Only :meth:`reveal` gives it out, for the
    exchange the composition root makes."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def __repr__(self) -> str:
        return "AgentKey(<hidden>)"

    def reveal(self) -> str:
        return self._value


@dataclass(frozen=True, slots=True)
class AgentWallet:
    """One Hyperliquid agent wallet from the keys document (``CONTRACTS.md`` section 5).

    ``address`` is the account the agent trades for, as Hyperliquid's API wallets sign for their
    master account. It can trade and cannot withdraw, and it expires within 180 days.
    """

    address: str
    agent_key: AgentKey
    expires_at_ms: int
    subaccount: str | None = None


def _keys_refusal(reason: str, **extra: object) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context={"field": "hyperliquid", "reason": reason, **extra},
    )


def _expiry_ms(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    if moment.tzinfo is None:
        return None
    return (moment - _EPOCH) // timedelta(milliseconds=1)


def agent_wallets(document: Mapping[str, object]) -> Result[tuple[AgentWallet, ...]]:
    """The Hyperliquid agent wallets in a ``qmx.node.keys/1`` document, none when it has none.

    A refusal names the entry and the field, never a value from it.
    """
    if document.get("schema_version") != KEYS_SCHEMA:
        return _keys_refusal(f"the keys document is not a {KEYS_SCHEMA} document")
    entries = document.get("hyperliquid")
    if entries is None:
        return Ok(())
    if not isinstance(entries, list):
        return _keys_refusal("hyperliquid is a list of agent wallets")
    wallets: list[AgentWallet] = []
    for index, entry in enumerate(cast("list[object]", entries)):
        if not isinstance(entry, dict):
            return _keys_refusal("each agent wallet is an object", index=index)
        given = cast("Mapping[str, object]", entry)
        address, signer = given.get("address"), given.get("agent_key")
        subaccount, expires = given.get("subaccount"), _expiry_ms(given.get("expires_at"))
        if not isinstance(address, str) or _ADDRESS.fullmatch(address) is None:
            return _keys_refusal("address is the account's 0x address", index=index)
        if not isinstance(signer, str) or _SIGNER.fullmatch(signer) is None:
            return _keys_refusal("agent_key is the agent wallet's 32-byte 0x key", index=index)
        if expires is None:
            return _keys_refusal("expires_at is an ISO 8601 time with its zone", index=index)
        if subaccount is not None and (
            not isinstance(subaccount, str) or _ADDRESS.fullmatch(subaccount) is None
        ):
            return _keys_refusal("subaccount is a 0x address when given", index=index)
        wallets.append(AgentWallet(address, AgentKey(signer), expires, subaccount))
    return Ok(tuple(wallets))


def renewal_due(wallet: AgentWallet, now_ms: int, days: int = AGENT_WALLET_RENEWAL_DAYS) -> bool:
    """Whether the renewal card shows: the wallet expires within ``days``."""
    return now_ms >= wallet.expires_at_ms - days * 86_400_000


def hyperliquid_config(wallet: AgentWallet) -> dict[str, object]:
    """The ``ccxt.hyperliquid`` constructor config for ``wallet``. This is the one place the
    agent key leaves its wrapper, straight into the exchange that signs with it."""
    return {
        "walletAddress": wallet.address,
        "privateKey": wallet.agent_key.reveal(),
        "options": {"refSet": True, "builderFee": False, "approvedBuilderFee": False},
    }


# --- cloid tags --------------------------------------------------------------------------------


def cloid(name: str) -> str | None:
    """Hyperliquid's 16-byte client order id for a node order name, tag first.

    Two marker bytes, the node tag's five bytes (its eight base-32 characters), then nine bytes
    of the name's SHA-256, so the same name gets the same cloid on a re-run. ``name`` is the
    entry's client order id ``q<tag>-<ULID>``, or a step of it such as ``<id>/stop-1``. None when
    the name carries no node tag.
    """
    match = _NODE_NAME.fullmatch(name)
    if match is None:
        return None
    tag = base64.b32decode(match.group(1).upper()).hex()
    tail = hashlib.sha256(name.encode("utf-8")).digest()[:9].hex()
    return f"0x{_CLOID_MARK}{tag}{tail}"


def cloid_tag(value: str | None) -> str | None:
    """The node tag a cloid carries, or None for a cloid no node minted."""
    match = None if value is None else _CLOID.fullmatch(value.lower())
    if match is None:
        return None
    return base64.b32encode(bytes.fromhex(match.group(1))).decode("ascii").lower()


def _stand_in_name(value: str) -> str | None:
    """A ``q<tag>-<26 characters>`` name for a node's cloid this client never sent, so
    attribution reads its tag: a twin's under this node's tag, else another node's."""
    match = _CLOID.fullmatch(value.lower())
    tag = cloid_tag(value)
    if match is None or tag is None:
        return None
    number = int(match.group(2), 16)
    tail = "".join(_CROCKFORD[(number >> (5 * shift)) & 31] for shift in range(25, -1, -1))
    return f"q{tag}-{tail}"


# --- errors ------------------------------------------------------------------------------------

_REJECTED: Final = SubmissionOutcome.REJECTED_BY_VENUE
_UNKNOWN: Final = SubmissionOutcome.UNKNOWN

ERRORS: Final[Mapping[str, tuple[SubmissionOutcome, str]]] = {
    "BaseError": (_UNKNOWN, "unread"),
    "ExchangeError": (_UNKNOWN, "unread"),
    "AuthenticationError": (_REJECTED, "authentication"),
    "PermissionDenied": (_REJECTED, "permission-denied"),
    "AccountNotEnabled": (_REJECTED, "account-not-enabled"),
    "AccountSuspended": (_REJECTED, "account-suspended"),
    "ArgumentsRequired": (_REJECTED, "arguments-required"),
    "BadRequest": (_REJECTED, "bad-request"),
    "BadSymbol": (_REJECTED, "bad-symbol"),
    "OperationRejected": (_REJECTED, "operation-rejected"),
    "NoChange": (_REJECTED, "no-change"),
    "MarginModeAlreadySet": (_REJECTED, "margin-mode-already-set"),
    "MarketClosed": (_REJECTED, "market-closed"),
    "ManualInteractionNeeded": (_REJECTED, "manual-interaction-needed"),
    "RestrictedLocation": (_REJECTED, "restricted-location"),
    "InsufficientFunds": (_REJECTED, "insufficient-funds"),
    "InvalidAddress": (_REJECTED, "invalid-address"),
    "AddressPending": (_REJECTED, "address-pending"),
    "InvalidOrder": (_REJECTED, "invalid-order"),
    "OrderNotFound": (_REJECTED, "order-not-found"),
    "OrderNotCached": (_REJECTED, "order-not-cached"),
    "OrderImmediatelyFillable": (_REJECTED, "order-immediately-fillable"),
    "OrderNotFillable": (_REJECTED, "order-not-fillable"),
    "DuplicateOrderId": (_UNKNOWN, "duplicate-order-id"),
    "ContractUnavailable": (_REJECTED, "contract-unavailable"),
    "NotSupported": (_REJECTED, "not-supported"),
    "InvalidProxySettings": (_REJECTED, "invalid-proxy-settings"),
    "ExchangeClosedByUser": (_REJECTED, "exchange-closed-by-user"),
    "OperationFailed": (_UNKNOWN, "operation-failed"),
    "NetworkError": (_UNKNOWN, "network-error"),
    "DDoSProtection": (_REJECTED, "ddos-protection"),
    "RateLimitExceeded": (_REJECTED, "rate-limit-exceeded"),
    "ExchangeNotAvailable": (_UNKNOWN, "exchange-not-available"),
    "OnMaintenance": (_UNKNOWN, "on-maintenance"),
    "InvalidNonce": (_REJECTED, "invalid-nonce"),
    "ChecksumError": (_UNKNOWN, "checksum-error"),
    "RequestTimeout": (_UNKNOWN, "request-timeout"),
    "BadResponse": (_UNKNOWN, "bad-response"),
    "NullResponse": (_UNKNOWN, "null-response"),
    "CancelPending": (_UNKNOWN, "cancel-pending"),
    "UnsubscribeError": (_UNKNOWN, "unsubscribe-error"),
}
"""One reading per error class of CCXT 4.5.85 (``ccxt/base/errors.py``), by class name.

A rejection is an error CCXT raises before it sends, or one the venue answered with, so the venue
holds nothing from the order. UNKNOWN is any error after which the order may be at the venue: a
timeout, a lost connection, a venue down mid-answer. ``DuplicateOrderId`` is UNKNOWN because the
venue already holds an order with that cloid. ``ExchangeError`` and ``BaseError`` are a venue
message CCXT does not know, so they read UNKNOWN and raise the alarm.
"""
_ALARMED: Final = frozenset({"BaseError", "ExchangeError"})


@dataclass(frozen=True, slots=True)
class ErrorReading:
    outcome: SubmissionOutcome
    code: str
    error: str
    """The error's class name."""
    alarm: str | None
    """The alarm it raises: ``venue_error_unmapped`` for a class the table lacks,
    ``venue_error_unread`` for a venue message CCXT does not know, else None."""


def read_error(error: BaseException) -> ErrorReading:
    """The reading of one raised error, by its exact class name, so a subclass a later CCXT adds
    is unmapped until the table names it."""
    name = type(error).__name__
    row = ERRORS.get(name)
    if row is None:
        return ErrorReading(_UNKNOWN, f"unmapped:{name}", name, "venue_error_unmapped")
    outcome, code = row
    return ErrorReading(outcome, code, name, "venue_error_unread" if name in _ALARMED else None)


# --- the exchange -------------------------------------------------------------------------------


class Configurable(Protocol):
    """What the testnet setup reads and sets on any ``ccxt.hyperliquid``, ``ccxt.pro``'s
    included."""

    options: dict[str, object]
    urls: dict[str, object]


class Buildable(Configurable, Protocol):
    """A ``ccxt.hyperliquid`` as :func:`make_testnet_exchange` builds it."""

    def set_sandbox_mode(self, enabled: bool, /) -> None: ...


class Exchange(Configurable, Protocol):
    """The calls this client makes on a ``ccxt.hyperliquid`` instance, by CCXT's names. Every
    call passes its arguments by position, CCXT's order."""

    walletAddress: str | None

    def create_order(
        self,
        symbol: str,
        kind: str,
        side: str,
        amount: str,
        price: str | None,
        params: Mapping[str, object],
        /,
    ) -> Mapping[str, object]: ...

    def cancel_order(
        self, order_id: str, symbol: str | None, params: Mapping[str, object], /
    ) -> Mapping[str, object]: ...

    def fetch_open_orders(
        self,
        symbol: str | None,
        since: int | None,
        limit: int | None,
        params: Mapping[str, object],
        /,
    ) -> Sequence[Mapping[str, object]]: ...

    def fetch_orders(
        self,
        symbol: str | None,
        since: int | None,
        limit: int | None,
        params: Mapping[str, object],
        /,
    ) -> Sequence[Mapping[str, object]]: ...

    def fetch_my_trades(
        self,
        symbol: str | None,
        since: int | None,
        limit: int | None,
        params: Mapping[str, object],
        /,
    ) -> Sequence[Mapping[str, object]]: ...

    def fetch_positions(
        self, symbols: Sequence[str] | None, params: Mapping[str, object], /
    ) -> Sequence[Mapping[str, object]]: ...

    def fetch_balance(self, params: Mapping[str, object], /) -> Mapping[str, object]: ...


def _no_builder_fee() -> bool:
    """Stands in for CCXT's builder-fee approval, which would sign and send an approval for
    CCXT's own builder address on the first order."""
    return True


async def _no_builder_fee_async() -> bool:
    """:func:`_no_builder_fee` for ``ccxt.pro``, whose first order awaits the approval."""
    return True


def api_urls(exchange: Configurable) -> tuple[str, ...]:
    """Every endpoint in the exchange's ``urls["api"]``, nested ones (``ccxt.pro``'s ``ws``)
    included."""
    found: list[str] = []
    pending: list[object] = [exchange.urls.get("api")]
    while pending:
        value = pending.pop()
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, dict):
            pending.extend(cast("dict[str, object]", value).values())
    return tuple(sorted(found))


def _off_testnet(exchange: Configurable) -> TypedRefusal | None:
    """The refusal for an exchange with any endpoint off Hyperliquid's testnet, or None."""
    urls = api_urls(exchange)
    if urls and all(urlsplit(url).hostname == TESTNET_HOST for url in urls):
        return None
    return _refused("endpoints", "an endpoint is not Hyperliquid's testnet", endpoints=list(urls))


def _quiet(exchange: Configurable) -> None:
    """Turn off what CCXT 4.5.85 sends on the first order: a ``setReferrer`` action, and an
    ``approveBuilderFee`` for CCXT's own builder, which then rides on every order."""
    exchange.options["refSet"] = True
    exchange.options["approvedBuilderFee"] = False
    approve: object = getattr(exchange, "handle_builder_fee_approval", None)
    stand_in = _no_builder_fee_async if inspect.iscoroutinefunction(approve) else _no_builder_fee
    setattr(exchange, "handle_builder_fee_approval", stand_in)  # noqa: B010 - CCXT's own method


def make_testnet_exchange(
    make: Callable[[dict[str, object]], _E], wallet: AgentWallet
) -> Result[_E]:
    """``make`` (``ccxt.hyperliquid`` or ``ccxt.pro.hyperliquid``) on testnet for ``wallet``,
    with no referrer and no builder fee. Refused when an endpoint is not testnet's. Every exchange
    a composition root makes goes through here."""
    exchange = make(hyperliquid_config(wallet))
    exchange.set_sandbox_mode(True)
    refused = _off_testnet(exchange)
    if refused is not None:
        return refused
    _quiet(exchange)
    return Ok(exchange)


def _number(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _text(value: Decimal) -> str:
    return format(value, "f")


@dataclass
class _Held:
    """A position the node holds on one coin, as this client placed or adopted it."""

    market_id: str
    symbol: str
    side: Side
    quantity: Decimal
    entry: Decimal
    stop: Decimal | None = None
    stop_cloid: str | None = None
    steps: int = 0

    def step(self, name: str, what: str) -> str | None:
        self.steps += 1
        return cloid(f"{name}/{what}-{self.steps}")


def _refused(field_name: str, reason: str, **extra: object) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.UNSUPPORTED_CAPABILITY,
        retryability=Retryability.NO,
        context={"field": field_name, "reason": reason, **extra},
    )


@dataclass
class CcxtClient:
    """One Hyperliquid account binding, as the node's order path sends to it.

    Build it with :meth:`open`. ``markets`` maps each node market id to its CCXT symbol. ``sent``
    answers every client order id the node journal holds a send for, so a cloid read back after a
    restart is named by the order it came from.
    """

    exchange: Exchange
    venue_account: Account
    markets: Mapping[str, str]
    clock_ns: Callable[[], int]
    on_alarm: Callable[[Mapping[str, object]], None]
    sent: Callable[[], Iterable[str]]
    subaccount: str | None = None
    open_orders_margin: int = OPEN_ORDERS_MARGIN
    poll_ns: int = POLL_NS
    _held: dict[str, _Held] = field(default_factory=dict[str, _Held])
    _closed: dict[str, VenueClose] = field(default_factory=dict[str, VenueClose])
    _names: dict[str, str] = field(default_factory=dict[str, str])
    _polled_ns: int | None = None

    @classmethod
    def open(
        cls,
        exchange: Exchange,
        *,
        account: Account,
        wallet: AgentWallet,
        markets: Mapping[str, str],
        ccxt_version: str,
        clock_ns: Callable[[], int],
        on_alarm: Callable[[Mapping[str, object]], None],
        sent: Callable[[], Iterable[str]],
    ) -> Result[CcxtClient]:
        """Bind ``exchange`` for ``wallet``, refused on another CCXT version, on mainnet, for
        another signer or for an expired wallet.

        ``sent`` has no default: after a restart the journal is the only record of which
        positions on the account the node opened, so every composition root wires it."""
        if ccxt_version != PINNED_CCXT_VERSION:
            return _refused(
                "ccxt_version",
                "the venue mapping is checked against the pinned CCXT only; check it again "
                "before binding another version",
                given=ccxt_version,
                pinned=PINNED_CCXT_VERSION,
            )
        if exchange.options.get("sandboxMode") is not True:
            return _refused(
                "sandbox_mode",
                "this client binds Hyperliquid's testnet only; a mainnet binding is the "
                "deliberate live path",
            )
        off_testnet = _off_testnet(exchange)
        if off_testnet is not None:
            return off_testnet
        signer = exchange.walletAddress
        if signer is None or signer.lower() != wallet.address.lower():
            return _refused("wallet_address", "the exchange does not sign for this agent wallet")
        if clock_ns() // 1_000_000 >= wallet.expires_at_ms:
            return _refused("expires_at", "the agent wallet has expired; approve a new one")
        _quiet(exchange)
        return Ok(cls(exchange, account, markets, clock_ns, on_alarm, sent, wallet.subaccount))

    # --- what the order path reads ---

    @property
    def kind(self) -> VenueClientKind:
        return VenueClientKind.CCXT

    @property
    def venue_id(self) -> VenueId:
        return self.venue_account.venue

    @property
    def account(self) -> Account:
        return self.venue_account

    @property
    def stop_forms(self) -> Mapping[str, str]:
        return STOP_FORMS

    def stop_of(self, position: str, /) -> Decimal | None:
        held = self._held.get(position)
        if held is not None and held.stop is None:
            self._poll()
        return None if held is None else held.stop

    def closed(self, position: str, /) -> VenueClose | None:
        if position in self._held:
            self._poll()
        return self._closed.get(position)

    def equity(self) -> Decimal:
        """The account's USDC total as the venue states it; zero when it cannot be read."""
        balance = self._call("fetch_balance", lambda: self.exchange.fetch_balance(self._reads))
        if isinstance(balance, ErrorReading):
            return Decimal(0)
        total = balance.get("total")
        found = (
            _number(cast("Mapping[str, object]", total).get(SETTLE))
            if isinstance(total, dict)
            else None
        )
        return Decimal(0) if found is None else found

    # --- sending ---

    def send(self, ticket: Ticket, /) -> Result[Sent]:
        match ticket.command.kind:
            case CommandKind.PLACE_ORDER:
                return Ok(self._entry(ticket))
            case CommandKind.AMEND_PROTECTION:
                return Ok(self._amend(ticket))
            case CommandKind.CLOSE_POSITION:
                held = self._held.get(ticket.position or "")
                if held is None or ticket.position is None:
                    return Ok(Sent(_REJECTED, None, "no-such-position"))
                return Ok(self._close(ticket.position, held, ticket.reference))
            case CommandKind.CLOSE_ALL:
                return Ok(self._close_all(ticket.reference))
            case CommandKind.CANCEL_ORDER:
                return Ok(self._cancel(ticket))

    def _entry(self, ticket: Ticket) -> Sent:
        params, tags, quantity = ticket.command.order_parameters, ticket.tags, ticket.quantity
        if params is None or tags is None or quantity is None:
            return Sent(_REJECTED, None, "not-an-entry")
        distance = params.protective_stop_distance
        symbol = self.markets.get(ticket.market_id)
        tag = cloid(tags.client_order_id)
        if distance is None:
            return Sent(_REJECTED, None, "no-stop-distance")
        if symbol is None:
            return Sent(_REJECTED, None, "unknown-market")
        if tag is None:
            return Sent(_REJECTED, None, "untagged-order")
        resting = self._call(
            "fetch_open_orders",
            lambda: self.exchange.fetch_open_orders(None, None, None, self._reads),
        )
        if isinstance(resting, ErrorReading):
            return Sent(_REJECTED, None, f"open-orders-unread:{resting.code}")
        if len(resting) >= self.open_orders_margin:
            return Sent(_REJECTED, None, "open-orders-margin")
        name = tags.client_order_id
        self._names[tag] = name
        long = ticket.side is Side.LONG
        order = self._call(
            "create_order",
            lambda: self.exchange.create_order(
                symbol,
                "market",
                "buy" if long else "sell",
                _text(quantity),
                _text(ticket.reference),
                {
                    "clientOrderId": tag,
                    "timeInForce": "Ioc",
                    "slippage": MARKET_SLIPPAGE,
                    **self._writes,
                },
            ),
        )
        if isinstance(order, ErrorReading):
            return Sent(order.outcome, None, order.code)
        filled = self._filled("create_order", order)
        if filled is None:
            return Sent(_UNKNOWN, None, "answer-unread")
        size, price = filled
        if size == 0:
            return Sent(_REJECTED, None, "not-filled")
        gap = Decimal(distance.value).scaleb(-distance.scale)
        held = _Held(ticket.market_id, symbol, ticket.side, size, price)
        self._held[name] = held
        self._place_stop(name, held, price - gap if long else price + gap)
        return Sent(SubmissionOutcome.ACCEPTED_BY_VENUE, price, quantity=size)

    def _place_stop(self, name: str, held: _Held, stop: Decimal) -> ErrorReading | None:
        """A reduce-only stop trigger over the whole position, then the stop it replaces
        cancelled. A refused or unknown placement leaves the held stop as it was."""
        tag = held.step(name, "stop")
        placed = self._call(
            "create_order",
            lambda: self.exchange.create_order(
                held.symbol,
                "market",
                "buy" if held.side is Side.LONG else "sell",
                _text(held.quantity),
                _text(stop),
                {
                    "clientOrderId": tag,
                    "stopLoss": {"triggerPrice": _text(stop), "type": "market"},
                    "grouping": "positionTpsl",
                    **self._writes,
                },
            ),
        )
        if isinstance(placed, ErrorReading):
            return placed
        replaced = held.stop_cloid
        held.stop, held.stop_cloid = stop, tag
        if replaced is not None:
            self._cancel_cloid(held.symbol, replaced)
        return None

    def _amend(self, ticket: Ticket) -> Sent:
        amendment, name = ticket.command.protection_amendment, ticket.position
        held = None if name is None else self._held.get(name)
        if amendment is None or name is None or held is None:
            return Sent(_REJECTED, None, "no-such-position")
        gap = Decimal(amendment.new_distance.value).scaleb(-amendment.new_distance.scale)
        stop = held.entry - gap if held.side is Side.LONG else held.entry + gap
        refused = self._place_stop(name, held, stop)
        if refused is not None:
            return Sent(refused.outcome, None, refused.code)
        return Sent(SubmissionOutcome.ACCEPTED_BY_VENUE, stop)

    def _close(self, name: str, held: _Held, reference: Decimal) -> Sent:
        """A reduce-only IOC order for what the node holds. Done only once nothing is left; a
        part filled is taken off the held quantity, and the next close sends the rest."""
        tag = held.step(name, "close")
        order = self._call(
            "create_order",
            lambda: self.exchange.create_order(
                held.symbol,
                "market",
                "sell" if held.side is Side.LONG else "buy",
                _text(held.quantity),
                _text(reference),
                {
                    "clientOrderId": tag,
                    "reduceOnly": True,
                    "timeInForce": "Ioc",
                    "slippage": MARKET_SLIPPAGE,
                    **self._writes,
                },
            ),
        )
        if isinstance(order, ErrorReading):
            return Sent(order.outcome, None, order.code)
        filled = self._filled("create_order", order)
        if filled is None:
            return Sent(_UNKNOWN, None, "answer-unread")
        size, price = filled
        if size < held.quantity:
            held.quantity -= size
            return Sent(_REJECTED, None, "not-filled" if size == 0 else "partly-closed")
        del self._held[name]
        self._closed[name] = VenueClose(FillKind.CLOSE, price)
        if held.stop_cloid is not None:
            self._cancel_cloid(held.symbol, held.stop_cloid)
        return Sent(SubmissionOutcome.ACCEPTED_BY_VENUE, price)

    def _close_all(self, reference: Decimal) -> Sent:
        answers = [self._close(name, held, reference) for name, held in list(self._held.items())]
        refused = next(
            (a for a in answers if a.outcome is not SubmissionOutcome.ACCEPTED_BY_VENUE), None
        )
        return refused or Sent(SubmissionOutcome.ACCEPTED_BY_VENUE, reference)

    def _cancel(self, ticket: Ticket) -> Sent:
        subject = ticket.command.subject_reference
        symbol = self.markets.get(ticket.market_id)
        tag = None if subject is None else cloid(subject)
        if symbol is None or tag is None:
            return Sent(_REJECTED, None, "no-such-order")
        refused = self._cancel_cloid(symbol, tag)
        if refused is not None:
            return Sent(refused.outcome, None, refused.code)
        return Sent(SubmissionOutcome.ACCEPTED_BY_VENUE, None)

    def _cancel_cloid(self, symbol: str, tag: str) -> ErrorReading | None:
        cancelled = self._call(
            "cancel_order",
            lambda: self.exchange.cancel_order(tag, symbol, {"clientOrderId": tag, **self._writes}),
        )
        return cancelled if isinstance(cancelled, ErrorReading) else None

    # --- reading the account ---

    def read_back(self) -> Result[ReadBack]:
        """Every entry and position on the account, as reconcile reads them.

        Positions net per coin, so each is named by the latest filled entry on its coin that
        carries a node cloid, and read through that order; a coin with none is named by its
        symbol and reads untagged. Stop triggers and reduce-only orders are the node's protection
        and closes: they set a position's stop and are not listed. A position's stop is a trigger
        carrying the same tag as the position, so a take-profit or another node's stop on the
        coin is never read as it.

        A position this client did not record as held is adopted when its entry is one this
        client sent or the node journal holds, so the node can close it: an entry whose answer
        was lost fills at the venue with nothing held here.
        """
        reads = self._reads
        calls: dict[str, Callable[[], Sequence[Mapping[str, object]]]] = {
            "fetch_open_orders": lambda: self.exchange.fetch_open_orders(None, None, None, reads),
            "fetch_orders": lambda: self.exchange.fetch_orders(None, None, None, reads),
            "fetch_my_trades": lambda: self.exchange.fetch_my_trades(None, None, None, reads),
            "fetch_positions": lambda: self.exchange.fetch_positions(None, reads),
        }
        got: dict[str, Sequence[Mapping[str, object]]] = {}
        for call, run in calls.items():
            answer = self._call(call, run)
            if isinstance(answer, ErrorReading):
                return _refused("read_back", f"the venue did not answer {call}", code=answer.code)
            got[call] = answer
        self._names.update({tag: name for name in self.sent() if (tag := cloid(name)) is not None})
        prices = _fill_prices(got["fetch_my_trades"])
        orders = {str(o.get("id")): o for o in got["fetch_orders"]}
        orders.update({str(o.get("id")): o for o in got["fetch_open_orders"]})
        entries = sorted(
            (o for o in orders.values() if not _protective(o)),
            key=lambda o: _number(o.get("timestamp")) or Decimal(0),
        )
        stops = {
            (str(o.get("symbol")), _order_tag(o)): _number(o.get("triggerPrice"))
            for o in got["fetch_open_orders"]
            if _protective(o) and o.get("triggerPrice") is not None
        }
        read: list[tuple[str, str | None, OrderState, Decimal | None, str]] = []
        opened: dict[str, str] = {}
        for order in entries:
            symbol, name = str(order.get("symbol")), self._name_of(order.get("clientOrderId"))
            state, price = _state(order, prices)
            read.append((symbol, name, state, price, self._market_of(symbol)))
            if state is OrderState.FILLED and name is not None:
                opened[symbol] = name
        positions: list[VenuePosition] = []
        for position in got["fetch_positions"]:
            symbol, size = str(position.get("symbol")), _number(position.get("contracts"))
            entry, side = _number(position.get("entryPrice")), position.get("side")
            if size is None or size == 0 or entry is None or side not in ("long", "short"):
                continue
            name = opened.get(symbol, symbol)
            stop, market = stops.get((symbol, _name_tag(name))), self._market_of(symbol)
            positions.append(VenuePosition(name, None, market, str(side), size, entry, stop))
            if name in self._names.values() and name not in self._held:
                self._held[name] = _Held(market, symbol, Side(str(side)), size, entry, stop)
        listed = tuple(
            VenueOrder(
                name, None, market, state, name if opened.get(symbol) == name else None, price
            )
            for symbol, name, state, price, market in read
        )
        return Ok(ReadBack(listed, tuple(positions)))

    def _poll(self) -> None:
        """Read positions and open orders at most every ``poll_ns``: a position gone from the
        venue was closed there, by its stop when it held one; a stop trigger seen is held."""
        now = self.clock_ns()
        if self._polled_ns is not None and now - self._polled_ns < self.poll_ns:
            return
        self._polled_ns = now
        reads = self._reads
        positions = self._call(
            "fetch_positions", lambda: self.exchange.fetch_positions(None, reads)
        )
        resting = self._call(
            "fetch_open_orders",
            lambda: self.exchange.fetch_open_orders(None, None, None, reads),
        )
        if isinstance(positions, ErrorReading) or isinstance(resting, ErrorReading):
            return
        open_symbols = {
            str(p.get("symbol")) for p in positions if (_number(p.get("contracts")) or 0) != 0
        }
        for name, held in list(self._held.items()):
            if held.symbol in open_symbols:
                held.stop = next(
                    (
                        _number(o.get("triggerPrice"))
                        for o in resting
                        if o.get("triggerPrice") is not None
                        and o.get("symbol") == held.symbol
                        and _order_tag(o) == _name_tag(name)
                    ),
                    None,
                )
                continue
            price = self._last_close_price(held)
            if price is None:
                continue
            long = held.side is Side.LONG
            kind = FillKind.STOP if held.stop is not None else FillKind.CLOSE
            gap = held.stop is not None and (price < held.stop if long else price > held.stop)
            del self._held[name]
            self._closed[name] = VenueClose(kind, price, gap)

    def _last_close_price(self, held: _Held) -> Decimal | None:
        trades = self._call(
            "fetch_my_trades",
            lambda: self.exchange.fetch_my_trades(held.symbol, None, None, self._reads),
        )
        if isinstance(trades, ErrorReading):
            return None
        opening = "buy" if held.side is Side.LONG else "sell"
        sides = [t.get("side") for t in trades]
        after = len(sides) - sides[::-1].index(opening) if opening in sides else 0
        closing = [t for t in trades[after:] if t.get("side") != opening]
        return None if not closing else _number(closing[-1].get("price"))

    # --- helpers ---

    @property
    def _reads(self) -> dict[str, object]:
        return {} if self.subaccount is None else {"subAccountAddress": self.subaccount}

    @property
    def _writes(self) -> dict[str, object]:
        return {} if self.subaccount is None else {"vaultAddress": self.subaccount}

    def _name_of(self, value: object) -> str | None:
        if not isinstance(value, str):
            return None
        return self._names.get(value.lower()) or _stand_in_name(value)

    def _market_of(self, symbol: str) -> str:
        return next((m for m, s in self.markets.items() if s == symbol), symbol)

    def _filled(self, call: str, order: Mapping[str, object]) -> tuple[Decimal, Decimal] | None:
        size, price = _number(order.get("filled")), _number(order.get("average"))
        if size == 0:
            return Decimal(0), Decimal(0)
        if size is None or price is None:
            self._alarm(call, "venue_answer_unread", "an order answer with no fill size or price")
            return None
        return size, price

    def _call(self, call: str, run: Callable[[], _T]) -> _T | ErrorReading:
        try:
            return run()
        except Exception as error:  # every raise is read, the unmapped ones as UNKNOWN
            reading = read_error(error)
            if reading.alarm is not None:
                self._alarm(call, reading.alarm, reading.error)
            return reading

    def _alarm(self, call: str, alarm: str, error: str) -> None:
        self.on_alarm(
            {
                "alarm": alarm,
                "venue": self.venue_account.venue.value,
                "account": self.venue_account.account_id,
                "call": call,
                "error": error,
            }
        )


def _order_tag(order: Mapping[str, object]) -> str | None:
    value = order.get("clientOrderId")
    return cloid_tag(value) if isinstance(value, str) else None


def _name_tag(name: str) -> str | None:
    """The node tag a position name carries, None for a position named by its symbol."""
    return cloid_tag(cloid(name))


def _protective(order: Mapping[str, object]) -> bool:
    return order.get("reduceOnly") is True or order.get("triggerPrice") is not None


def _fill_prices(trades: Sequence[Mapping[str, object]]) -> dict[str, Decimal]:
    """Each order's average fill price from its trades, by order id."""
    sums: dict[str, tuple[Decimal, Decimal]] = {}
    for trade in trades:
        order, price, size = (
            trade.get("order"),
            _number(trade.get("price")),
            _number(trade.get("amount")),
        )
        if order is None or price is None or size is None or size == 0:
            continue
        paid, filled = sums.get(str(order), (Decimal(0), Decimal(0)))
        sums[str(order)] = (paid + price * size, filled + size)
    return {order: paid / filled for order, (paid, filled) in sums.items()}


def _state(
    order: Mapping[str, object], prices: Mapping[str, Decimal]
) -> tuple[OrderState, Decimal | None]:
    """An order's state as reconcile reads it. A filled order whose trades are not yet listed
    reads open, so an UNKNOWN stays unknown until its price can be read."""
    filled = _number(order.get("filled")) or Decimal(0)
    if filled > 0:
        price = prices.get(str(order.get("id")))
        return (OrderState.OPEN, None) if price is None else (OrderState.FILLED, price)
    if order.get("status") == "open":
        return OrderState.OPEN, None
    return OrderState.GONE, None
