"""The cTrader venue binding: :class:`LiveCTraderClient` behind the node runtime's venue port.

Part C AD-306 and AD-308, Level 0 AD-37. :class:`CTraderVenue` is one bound cTrader account. It
answers both seams the runtime drives: the feed keeper's :class:`~qmn.app.feed_keeper.FeedSource`
(the session, its spots and the bars it builds from them) and the order path's
:class:`~qmn.app.runtime.VenueAccount` (orders, stops, closes, the balance and the read-back).

- Every order is encoded by :meth:`LiveCTraderClient.encode_command` onto the pinned Spotware
  definitions (release 91) and goes out as one ``ProtoMessage``. Every fill comes back through
  :meth:`LiveCTraderClient.receive`, which records the frame before it is read and crosses the
  execution-price double at the symbol's digits under :data:`FILL_ROUNDING`.
- An entry is a market order with its stop as ``relativeStopLoss``, the ``entry-relative`` form
  the session verifies. The node's lots become cTrader volume through the symbol's ``lotSize``;
  a size that is not a whole step of the symbol is refused before anything is sent.
- The session's capabilities are verified on every open, from what the session itself answered
  (the account's money digits and position model, the symbol's pip position), and the verified
  protective-stop forms are the forms the order path gates on.
- A trading answer that does not arrive within :data:`ANSWER_WAIT_S` reads UNKNOWN. Nothing here
  sends an order again: the reconciler reads the account and settles it (C-12b).
- The binding is demo only. :meth:`CTraderVenue.open` refuses a live host and a live account; a
  live binding is the deliberate path of C-21.

The wire is a :class:`Wire`: :class:`FramedWire` is the TLS socket to the Open API, and a test
answers as a fake cTrader on the same definitions. No credential is printed or kept here beyond
the call that sends it.
"""

from __future__ import annotations

import contextlib
import socket
import ssl
import threading
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Final, Protocol, cast

from google.protobuf.json_format import MessageToDict, ParseDict, ParseError
from google.protobuf.message import EncodeError, Message
from qmb.host.unit_handler import FillKind
from qmf.core import (
    Account,
    AccountRole,
    Duration,
    Instant,
    Instrument,
    MonotonicReading,
    Ok,
    PriceDelta,
    Quantity,
    RefusalCategory,
    Result,
    Retryability,
    RoundingMode,
    TypedRefusal,
    World,
    is_refusal,
)
from qmf.venue.capabilities import ErrorMap
from qmf.venue.commands import (
    CloseScope,
    Command,
    CommandKind,
    OrderParameters,
    OrderType,
    SubmissionOutcome,
    TimeInForce,
)
from qmf.venue.connection import decode_framed_payload, encode_framed_payload
from qmf.venue.ctrader import decode_execution_price
from qmf.venue.encode import OrderTags
from qmf.venue.observation import MeasuredFact, ProbeCheck, ProbeVerdict
from qmf.venue.proto import SPOTWARE_PROTO_PACKAGE, CompiledProto, compile_descriptor_set
from qml.protocol.unit import OHLC, QuoteBar
from qml.unit.model import Side

from qmn.app.attribution import OrderState, ReadBack, VenueOrder, VenuePosition, tags_of
from qmn.app.feed_keeper import Bar, Dropped, FeedEvent, Heartbeat, Quote
from qmn.app.reconciler import Lost
from qmn.app.runtime import Sent, Ticket, VenueClose
from qmn.venue.conformance import protective_stop_forms_from_verification, submit_not_ready_refusal
from qmn.venue.live import LiveCTraderClient, WireKind
from qmn.venue.verify import MeasuredFactBundle, VenueFactVerifier, ctrader_static_declaration

__all__ = [
    "ANSWER_WAIT_S",
    "BAR_NS",
    "DEMO_HOST",
    "FILL_ROUNDING",
    "HEARTBEAT_NS",
    "PROTO_TAG",
    "CTraderVenue",
    "Codec",
    "Frame",
    "FramedWire",
    "Listing",
    "OpenApi",
    "SymbolFacts",
    "TestTrade",
    "Wire",
    "account_listing",
]

PROTO_TAG: Final = 91
"""The pinned Spotware release (``registry:venue_protocol_artifact``)."""
DEMO_HOST: Final = "demo.ctraderapi.com"
OPEN_API_PORT: Final = 5035
ANSWER_WAIT_S: Final = 5.0
"""`[node] ctrader_answer_s`, starting at 5 s: how long the node waits for the venue's answer to
one request before the order reads UNKNOWN."""
HEARTBEAT_NS: Final = 10_000_000_000
"""cTrader asks a client for a heartbeat every 10 s."""
BAR_NS: Final = 60_000_000_000
"""`[node] ctrader_bar_s`, starting at 60 s: the base bar the node builds from cTrader's spots,
both quote sides. A labelled setting, owner numbers talk. 60 s is the fastest stream the shipped
templates read (the scalper's 1-minute bars), so every shipped stream is a whole multiple of it
and a 15-minute unit rolls fifteen of these up. It started at 900 s, which a 1-minute unit could
not read at all. Range: one second to one day. A unit whose stream is not a whole multiple of it
is refused at the host by name. The feed's work per bar is small (OPEN row 23): one bucket per
market per minute."""
FILL_ROUNDING: Final = RoundingMode.HALF_EVEN
"""The rounding a venue execution-price double crosses at the symbol's digits."""
SPOT_SCALE: Final = 5
"""cTrader's spot prices are integers in 1/100000 of the price."""
RENEW_CHECK_NS: Final = 3_600_000_000_000
"""How often a bound session asks whether its grant is due for a refresh: hourly."""
LOOKBACK_NS: Final = 86_400_000_000_000
"""`[node] ctrader_reconcile_lookback_s`: the declared reconcile lookback the client binds."""
DEAL_WINDOW_NS: Final = 604_800_000_000_000
"""`[node] ctrader_deal_window_s`, starting at one week: how long after a send the node searches
the account's deals for its position, when no position id was journalled."""
_ERRORS: Final = frozenset({"ProtoOAErrorRes", "ProtoErrorRes"})
_TRADES: Final = frozenset({"ProtoOAExecutionEvent", "ProtoOAOrderErrorEvent"})
_FILLS: Final = frozenset({"ORDER_FILLED", "ORDER_PARTIAL_FILL"})
"""The execution types that open an entry's position: a market order cTrader filled in part
opens it at the deal's filled volume, and the rest is never chased."""
_FROM_THE_SESSION: Final = frozenset(
    {ProbeCheck.PIP_FORMULA, ProbeCheck.MONEY_EXPONENT, ProbeCheck.POSITION_MODEL}
)
"""The measured facts this session answers itself. The rest are literals in `_measured`, so their
detail must not say they were read here (chief-1: only the demo probes can measure them)."""


def _refused(code: str, reason: str, *, retry: bool = True) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.UNAVAILABLE_DEPENDENCY
        if retry
        else RefusalCategory.POLICY_REJECTION,
        retryability=Retryability.AFTER_CONDITION if retry else Retryability.NO,
        context={"code": code, "reason": reason},
        after_condition_descriptor="the cTrader session answers again" if retry else None,
    )


def _int(value: object) -> int | None:
    """An integer from a decoded message: int64 fields arrive as text."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.lstrip("-").isdigit():
        return int(value)
    return None


def _map(value: object) -> Mapping[str, object]:
    return cast("Mapping[str, object]", value) if isinstance(value, dict) else {}


def _history_said_nothing(refusal: TypedRefusal) -> bool:
    """A silent broker or a refused history request tells nothing about the position. A cut wire
    or the broker's rate limit means ask again next tick, when the true price may be there."""
    code = refusal.context.get("code")
    if code == "venue_silent":
        return True
    return refusal.retryability is Retryability.NO and code != "REQUEST_FREQUENCY_EXCEEDED"


def _rows(value: object) -> list[Mapping[str, object]]:
    return [_map(item) for item in cast("list[object]", value)] if isinstance(value, list) else []


# --- the wire and the pinned definitions -----------------------------------------------------


class Wire(Protocol):
    """One Open API connection: whole ``ProtoMessage`` envelopes each way."""

    def send(self, envelope: bytes, /) -> Result[None]: ...

    def receive(self, wait_s: float, /) -> Result[bytes | None]:
        """The next envelope, or None when none arrived within ``wait_s``."""
        ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class Frame:
    """One decoded message: its name, the request it answers, and its fields."""

    name: str
    msg_id: str
    body: Mapping[str, object]


class Codec:
    """The pinned Spotware definitions: encode a request by name, decode any answer."""

    def __init__(self, proto: CompiledProto) -> None:
        self.proto = proto
        self._names: dict[int, str] = {}
        for name in proto.message_names():
            if name == "ProtoMessage":
                continue
            made = proto.message_class(name)
            if is_refusal(made):
                continue
            payload_type = getattr(made.value(), "payloadType", None)
            if isinstance(payload_type, int) and payload_type:
                self._names.setdefault(payload_type, name)

    @classmethod
    def load(cls, path: Path) -> Result[Codec]:
        try:
            raw = path.read_bytes()
        except OSError as error:
            return _refused(
                "definitions_missing", f"{path.name}: {type(error).__name__}", retry=False
            )
        compiled = compile_descriptor_set(
            raw, package_name=SPOTWARE_PROTO_PACKAGE, release_tag=PROTO_TAG
        )
        if is_refusal(compiled):
            return compiled
        return Ok(cls(compiled.value))

    def _make(self, name: str) -> Result[Message]:
        made = self.proto.message_class(name)
        if is_refusal(made):
            return made
        return Ok(made.value())

    def encode(self, name: str, values: Mapping[str, object], msg_id: str) -> Result[bytes]:
        inner = self._make(name)
        envelope = self._make("ProtoMessage")
        if is_refusal(inner):
            return inner
        if is_refusal(envelope):
            return envelope
        try:
            message = ParseDict(dict(values), inner.value)
            outer = envelope.value
            outer.payloadType = getattr(message, "payloadType")  # pyright: ignore[reportAttributeAccessIssue]  # noqa: B009
            outer.payload = message.SerializeToString()  # pyright: ignore[reportAttributeAccessIssue]
            outer.clientMsgId = msg_id  # pyright: ignore[reportAttributeAccessIssue]
            return Ok(outer.SerializeToString())
        except (ParseError, EncodeError) as error:
            return _refused("unencodable", f"{name}: {type(error).__name__}", retry=False)

    def decode(self, envelope: bytes) -> Result[Frame]:
        outer = self._make("ProtoMessage")
        if is_refusal(outer):
            return outer
        try:
            outer.value.ParseFromString(envelope)
        except Exception:  # the venue's bytes are the boundary
            return _refused("unreadable_frame", "a frame is not a ProtoMessage", retry=False)
        found = cast("dict[str, object]", MessageToDict(outer.value))
        payload_type = _int(found.get("payloadType")) or 0
        msg_id = str(found.get("clientMsgId") or "")
        name = self._names.get(payload_type)
        if name is None:
            return Ok(Frame(f"unknown:{payload_type}", msg_id, {}))
        inner = self._make(name)
        if is_refusal(inner):
            return inner
        try:
            inner.value.ParseFromString(getattr(outer.value, "payload", b""))
        except Exception:  # the venue's bytes are the boundary
            return _refused("unreadable_frame", f"{name} did not decode", retry=False)
        body = cast(
            "dict[str, object]", MessageToDict(inner.value, preserving_proto_field_name=True)
        )
        return Ok(Frame(name, msg_id, body))


class FramedWire:
    """The TLS socket to cTrader's Open API, a plain blocking socket driven by the one thread
    that owns the binding; the node keeps its one event loop (DEC-0243). Bytes are kept until a
    frame has arrived whole, so a wait that ends early never cuts one."""

    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock
        self._buffer = bytearray()

    @classmethod
    def open(
        cls, host: str, *, port: int = OPEN_API_PORT, tls: bool = True, timeout_s: float = 10.0
    ) -> Result[Wire]:
        """``tls`` is off only for a fake cTrader on this machine (``server.endpoints``)."""
        try:
            raw = socket.create_connection((host, port), timeout=timeout_s)
            if not tls:
                return Ok(cls(raw))
            try:
                return Ok(cls(ssl.create_default_context().wrap_socket(raw, server_hostname=host)))
            except OSError:
                raw.close()
                raise
        except OSError as error:
            return _refused("venue_unreachable", f"{host}:{port} {type(error).__name__}")

    def send(self, envelope: bytes, /) -> Result[None]:
        framed = encode_framed_payload(envelope)
        if is_refusal(framed):
            return framed
        try:
            self._sock.settimeout(ANSWER_WAIT_S)
            self._sock.sendall(framed.value)
        except OSError as error:
            return _refused("venue_write_failed", type(error).__name__)
        return Ok(None)

    def receive(self, wait_s: float, /) -> Result[bytes | None]:
        while True:
            whole = self._whole()
            if whole is not None:
                return whole
            try:
                self._sock.settimeout(max(wait_s, 0.001))
                chunk = self._sock.recv(65536)
            except TimeoutError:
                return Ok(None)
            except OSError as error:
                return _refused("venue_read_failed", type(error).__name__)
            if not chunk:
                return _refused("venue_closed", "cTrader closed the connection")
            self._buffer += chunk

    def _whole(self) -> Result[bytes | None] | None:
        if len(self._buffer) < 4:
            return None
        end = 4 + int.from_bytes(self._buffer[:4], "big")
        if len(self._buffer) < end:
            return None
        frame = bytes(self._buffer[:end])
        del self._buffer[:end]
        decoded = decode_framed_payload(frame)
        if is_refusal(decoded):
            return decoded
        return Ok(decoded.value)

    def close(self) -> None:
        with contextlib.suppress(OSError):
            self._sock.close()


@dataclass
class OpenApi:
    """One conversation over a wire: requests answered by their ``clientMsgId``, and every
    other message kept for the binding to read."""

    codec: Codec
    wire: Wire
    steady_ns: Callable[[], int]
    wait_s: float = ANSWER_WAIT_S
    pending: list[Frame] = field(default_factory=list[Frame])
    _sequence: int = 0

    def next_id(self) -> str:
        self._sequence += 1
        return f"qmx-{self._sequence}"

    def ask(self, name: str, values: Mapping[str, object]) -> Result[Frame]:
        """Send ``name`` and wait for its answer; an error answer is a refusal by its code."""
        msg_id = self.next_id()
        encoded = self.codec.encode(name, values, msg_id)
        if is_refusal(encoded):
            return encoded
        sent = self.wire.send(encoded.value)
        if is_refusal(sent):
            return sent
        answer = name.removesuffix("Req") + "Res"
        found = self.wait(lambda frame: frame.msg_id == msg_id and frame.name in {answer, *_ERRORS})
        if is_refusal(found):
            return found
        if found.value is None:
            return _refused("venue_silent", f"no {answer} within {self.wait_s:g} s")
        if found.value.name in _ERRORS:
            return _refused(_error_word(found.value.body), f"{name} refused", retry=False)
        return Ok(found.value)

    def push(self, envelope: bytes) -> Result[None]:
        return self.wire.send(envelope)

    def wait(self, match: Callable[[Frame], bool]) -> Result[Frame | None]:
        """Read until a frame matches, keeping every other one; None past ``wait_s``."""
        for index, frame in enumerate(self.pending):
            if match(frame):
                return Ok(self.pending.pop(index))
        deadline = self.steady_ns() + int(self.wait_s * 1e9)
        while True:
            left = (deadline - self.steady_ns()) / 1e9
            if left <= 0:
                return Ok(None)
            got = self._next(left)
            if is_refusal(got):
                return got
            if got.value is None:
                return Ok(None)
            if match(got.value):
                return Ok(got.value)
            self.pending.append(got.value)

    def drain(self) -> Result[list[Frame]]:
        """Every message that has arrived, without waiting."""
        while True:
            got = self._next(0.0)
            if is_refusal(got):
                return got
            if got.value is None:
                break
            self.pending.append(got.value)
        taken, self.pending = self.pending, []
        return Ok(taken)

    def _next(self, wait_s: float) -> Result[Frame | None]:
        raw = self.wire.receive(wait_s)
        if is_refusal(raw):
            return raw
        if raw.value is None:
            return Ok(None)
        frame = self.codec.decode(raw.value)
        if is_refusal(frame):
            return frame
        return Ok(frame.value)


def _error_word(body: Mapping[str, object]) -> str:
    """cTrader's own error word; its description is never kept, since it may echo a value."""
    word = str(body.get("errorCode") or "venue_refused")
    return word if word.replace("_", "").isalnum() and len(word) <= 40 else "venue_refused"


# --- what a grant can reach -------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Listing:
    """The accounts an access token reaches and the scope it was granted."""

    scope: str
    accounts: tuple[tuple[int, bool, int | None, str], ...]
    """``(ctidTraderAccountId, isLive, traderLogin, brokerTitleShort)`` each."""


def account_listing(
    api: OpenApi, client_id: str, client_secret: str, access_token: str
) -> Result[Listing]:
    """Authorise the node's app on the session, then list what the access token reaches."""
    authorised = api.ask(
        "ProtoOAApplicationAuthReq", {"clientId": client_id, "clientSecret": client_secret}
    )
    if is_refusal(authorised):
        return authorised
    listed = api.ask("ProtoOAGetAccountListByAccessTokenReq", {"accessToken": access_token})
    if is_refusal(listed):
        return listed
    body = listed.value.body
    accounts: list[tuple[int, bool, int | None, str]] = []
    for row in _rows(body.get("ctidTraderAccount")):
        ctid = _int(row.get("ctidTraderAccountId"))
        if ctid is not None:
            accounts.append(
                (
                    ctid,
                    row.get("isLive") is True,
                    _int(row.get("traderLogin")),
                    str(row.get("brokerTitleShort") or ""),
                )
            )
    return Ok(Listing(str(body.get("permissionScope") or "SCOPE_TRADE"), tuple(accounts)))


# --- one bound account ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SymbolFacts:
    """One market's cTrader symbol as the session answered it."""

    market_id: str
    name: str
    symbol_id: int
    digits: int
    pip_position: int
    lot_size: int
    """Cents of the base unit in one lot."""
    step_volume: int
    min_volume: int
    instrument: Instrument


@dataclass(frozen=True, slots=True)
class TestTrade:
    """What the self-test's demo trade proved."""

    ok: bool
    detail: str
    stop: Decimal | None = None
    entry: Decimal | None = None
    exit: Decimal | None = None
    close_ms: int | None = None


@dataclass
class _Open:
    position_id: int
    market_id: str
    side: Side
    volume: int
    lots: Decimal
    entry: Decimal
    stop: Decimal | None
    label: str | None
    closing: bool = False

    def read_back(self, name: str) -> VenuePosition:
        return VenuePosition(
            name, self.label, self.market_id, self.side.value, self.lots, self.entry, self.stop
        )


@dataclass(frozen=True, slots=True)
class _Gone:
    """A position the broker no longer lists, until its close is known."""

    name: str
    held: _Open
    """Its ``position_id`` is 0 when no id was journalled."""
    sent_ns: int | None = None
    """When its entry was sent, the start of the deal search when it has no id."""


def _close_read(held: _Open, price: Decimal, order_type: object) -> VenueClose:
    """What a close was, from its price and its order's type."""
    stopped = order_type == "STOP_LOSS_TAKE_PROFIT" and not held.closing
    gap = (
        held.stop is not None
        and stopped
        and (price < held.stop if held.side is Side.LONG else price > held.stop)
    )
    return VenueClose(FillKind.STOP if stopped else FillKind.CLOSE, price, gap)


@dataclass(frozen=True, slots=True)
class _Entry:
    """An entry sent whose fill or refusal has not been read yet."""

    market_id: str
    side: Side
    volume: int
    lots: Decimal
    label: str


@dataclass
class _Building:
    start_ns: int
    bid: list[Decimal]
    ask: list[Decimal]
    whole: bool
    """False for the bucket a session joined part way through: it is never sent as a bar."""


class _NodeClock:
    """The node's own clock as the live client's :class:`~qmf.core.Clock` seam."""

    def __init__(
        self, clock_ns: Callable[[], int], steady_ns: Callable[[], int], epoch: str
    ) -> None:
        self.boot_epoch_id = epoch
        self._clock_ns, self._steady_ns = clock_ns, steady_ns

    def wall_now(self) -> Result[Instant]:
        return Instant.try_create(self._clock_ns())

    def monotonic_now(self) -> Result[MonotonicReading]:
        return MonotonicReading.try_create(self._steady_ns(), self.boot_epoch_id)


class CTraderVenue:
    """One bound cTrader demo account: the feed keeper's source and the order path's account.

    Every method holds one lock, so the runtime thread and a self-test never share the socket.
    """

    def __init__(
        self,
        *,
        account: Account,
        ctid: int,
        host: str,
        markets: Mapping[str, str],
        codec: Codec,
        open_wire: Callable[[str], Result[Wire]],
        credentials: Callable[[], tuple[str, str, str] | None],
        clock_ns: Callable[[], int],
        steady_ns: Callable[[], int],
        session_epoch: str,
        bar_ns: int = BAR_NS,
    ) -> None:
        self.venue_account = account
        self.ctid = ctid
        self.host = host
        self.markets = dict(markets)
        """Each market id the feed keeper asks for, with its cTrader symbol name."""
        self.codec = codec
        self.open_wire = open_wire
        self.credentials = credentials
        """The app id, app secret and access token, read fresh at every session open."""
        self.clock_ns = clock_ns
        self.steady_ns = steady_ns
        self.session_epoch = session_epoch
        self.bar_ns = bar_ns
        self.api: OpenApi | None = None
        self.symbols: dict[str, SymbolFacts] = {}
        self.unlisted: dict[str, str] = {}
        """Each market this session cannot trade, by the symbol the account does not list. The
        session keeps the markets it can trade instead of refusing all for one of these."""
        self.balance: Decimal = Decimal(0)
        self.money_digits = 2
        self.position_model = "hedging"
        self.ready = False
        self.reason = "not opened yet"
        self.client: LiveCTraderClient | None = None
        self._forms: Mapping[str, str] = {}
        self._lock = threading.RLock()
        self._open: dict[str, _Open] = {}
        """Each open position by its entry's client order id, the name the runtime closes."""
        self._unanswered: dict[str, _Entry] = {}
        self._closed: dict[str, VenueClose] = {}
        self._doubts: list[Mapping[str, object]] = []
        self._orders: list[VenueOrder] = []
        self._events: list[FeedEvent] = []
        self._building: dict[str, _Building] = {}
        self._last_heartbeat = 0
        self._renew_at = 0
        self.renew: Callable[[], str | None] = lambda: None
        """A new access token when the grant was refreshed since the last ask, else None."""
        self.jobs: list[Callable[[], None]] = []
        """Work that must run on the thread that drives the session, such as a self-test."""

    @classmethod
    def refusal(cls, *, host: str, is_live: bool, role: AccountRole) -> TypedRefusal | None:
        """Why this binding may not open: a live host or a live account is C-21's path."""
        if host != DEMO_HOST:
            return _refused(
                "live_host", f"the node binds cTrader's demo host only, not {host}", retry=False
            )
        if is_live or role is not AccountRole.DEMO:
            return _refused(
                "live_account",
                "the practice node binds demo accounts only; a live binding is the deliberate"
                " live path",
                retry=False,
            )
        return None

    # --- the venue account the order path sends to --------------------------------------

    @property
    def account(self) -> Account:
        return self.venue_account

    @property
    def stop_forms(self) -> Mapping[str, str]:
        return self._forms

    def send(self, ticket: Ticket, /) -> Result[Sent]:
        with self._lock:
            if not self.ready or self.api is None or self.client is None:
                return submit_not_ready_refusal()
            kind = ticket.command.kind
            if kind is CommandKind.PLACE_ORDER:
                return self._enter(ticket, self.api, self.client)
            held = None if ticket.position is None else self._open.get(ticket.position)
            if ticket.position is None or held is None:
                return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "no-such-position"))
            if kind is CommandKind.CLOSE_POSITION:
                return self._close(ticket, ticket.position, held, self.api, self.client)
            if kind is CommandKind.AMEND_PROTECTION:
                return self._amend(ticket, held, self.api, self.client)
            return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "unsupported-command"))

    def stop_of(self, position: str, /) -> Decimal | None:
        with self._lock:
            self._pump()
            held = self._open.get(position)
            return None if held is None else held.stop

    def closed(self, position: str, /) -> VenueClose | None:
        with self._lock:
            self._pump()
            return self._closed.get(position)

    def equity(self) -> Decimal:
        return self.balance

    def read_balance(self) -> Result[Decimal]:
        """Ask cTrader for the account's cash again: the node's timed account read (AD-15).

        The same ``ProtoOATraderReq`` the session opened with and the same parse, so a re-read can
        never read the cash under other money digits than the first one. A session that is not
        open answers a refusal and leaves the last balance in place, which the fact's own age then
        marks stale; nothing here sends an order.
        """
        with self._lock:
            if self.api is None or not self._pump():
                return submit_not_ready_refusal()
            answer = self.api.ask("ProtoOATraderReq", {"ctidTraderAccountId": self.ctid})
            if is_refusal(answer):
                return answer
            return Ok(self._took(_map(answer.value.body.get("trader"))))

    def _took(self, found: Mapping[str, object]) -> Decimal:
        """The cash and money digits a trader answer states, for the open and every re-read."""
        digits = _int(found.get("moneyDigits"))
        if digits is None:
            # Open API answers without moneyDigits are in cents.
            digits = 2
        self.money_digits = digits
        self.balance = Decimal(_int(found.get("balance")) or 0).scaleb(-digits)
        return self.balance

    def read_back(self) -> Result[ReadBack]:
        """The account's open positions and orders as cTrader reconciles them, each position
        named by its entry's client order id. Fills that already arrived are read first. The
        broker wins: each held position takes its stop and volume from the broker's row, and
        one the broker no longer lists closes (:meth:`_settle`)."""
        with self._lock:
            if self.api is None or not self._pump():
                return submit_not_ready_refusal()
            api = self.api
            listed = self._listed(api)
            if is_refusal(listed):
                return listed
            rows = self._settle(api, self._take_rows(listed.value), listed.value)
            if is_refusal(rows):
                return rows
            positions: list[VenuePosition] = []
            for row in rows.value:
                read = self._reconciled(api, row)
                if is_refusal(read):
                    return read
                positions.append(read.value)
            return Ok(ReadBack(tuple(self._orders), tuple(positions)))

    def find_closes(self, lost: Sequence[Lost], /) -> Result[Mapping[str, VenueClose]]:
        """How each entry closed while the node was down: what an earlier start journalled, else
        the broker's history. A position the broker lists after all answers a refusal, so the
        next tick's reconcile reads it fresh."""
        with self._lock:
            if self.api is None:
                return submit_not_ready_refusal()
            gone: list[_Gone] = []
            for item in lost:
                position = item.ours.position
                name = position.position
                if item.told is not None:
                    self._closed[name] = VenueClose(
                        FillKind(str(item.told["exit"])),
                        Decimal(str(item.told["price"])),
                        item.told.get("gap") is True,
                        item.told.get("guessed") is True,
                    )
                elif name not in self._closed:
                    held = _Open(
                        _int(item.position_id) or 0,
                        position.market_id,
                        Side(position.side),
                        0,
                        position.quantity,
                        position.entry_price,
                        position.stop,
                        position.label,
                    )
                    sent = _int(item.ours.send.get("sent_at_ns"))
                    gone.append(_Gone(name, held, sent))
            settled = self._settle(self.api, gone, [])
            if is_refusal(settled):
                return settled
            names = [item.ours.position.position for item in lost]
            if any(name not in self._closed for name in names):
                return _refused("listed_after_all", "the broker lists a position it left out")
            return Ok({name: self._closed[name] for name in names})

    def take_doubts(self) -> Sequence[Mapping[str, object]]:
        with self._lock:
            taken, self._doubts = self._doubts, []
            return taken

    def _listed(self, api: OpenApi) -> Result[list[Mapping[str, object]]]:
        """The positions the broker lists now. Frames kept while waiting arrived before the
        answer, so a close among them is read here and never reaches the history path."""
        answered = api.ask("ProtoOAReconcileReq", {"ctidTraderAccountId": self.ctid})
        if is_refusal(answered):
            return answered
        kept, api.pending = api.pending, []
        for frame in kept:
            self._absorb(frame)
        return Ok(_rows(answered.value.body.get("position")))

    def _take_rows(self, rows: Sequence[Mapping[str, object]]) -> list[_Gone]:
        """Each held position takes its stop and volume from its row, and a row with no stop
        clears the stop. Answers the held positions with no row."""
        by_id = {_int(row.get("positionId")): row for row in rows}
        gone: list[_Gone] = []
        for name, held in self._open.items():
            row = by_id.get(held.position_id)
            if row is None:
                gone.append(_Gone(name, held))
                continue
            held.stop = self._execution_price(row.get("stopLoss"), held.market_id)
            self._take_volume(held, row)
        return gone

    def _take_volume(self, held: _Open, position: Mapping[str, object]) -> None:
        volume = _int(_map(position.get("tradeData")).get("volume"))
        if volume is not None:
            held.volume = volume
            held.lots = Decimal(volume) / Decimal(self.symbols[held.market_id].lot_size)

    def _settle(
        self, api: OpenApi, gone: Sequence[_Gone], rows: Sequence[Mapping[str, object]]
    ) -> Result[Sequence[Mapping[str, object]]]:
        """Close each position the broker no longer lists, at its closing deal. With no deal,
        ask the broker once more, because a missing report is not flat. One still not listed
        closes at the stop it held, with an alarm that says the price is a guess, so no position
        stays held because history was silent. One silent answer ends the asking, since each
        waits :data:`ANSWER_WAIT_S` and a tick past 30 s stops the node. Answers the rows read
        last."""
        unread: list[_Gone] = []
        silent = False
        for one in gone:
            closing: Result[VenueClose | None] = Ok(None) if silent else self._closing(api, one)
            if is_refusal(closing):
                if not _history_said_nothing(closing):
                    return closing
                silent = closing.context.get("code") == "venue_silent"
                unread.append(one)
            elif closing.value is None:
                unread.append(one)
            else:
                self._open.pop(one.name, None)
                self._closed[one.name] = closing.value
        if not unread:
            return Ok(rows)
        again = self._listed(api)
        if is_refusal(again):
            return again
        for one in unread:
            if not any(self._lists(row, one.held) for row in again.value):
                self._guess(one)
        self._take_rows(again.value)
        return Ok(again.value)

    def _lists(self, row: Mapping[str, object], held: _Open) -> bool:
        if held.position_id:
            return _int(row.get("positionId")) == held.position_id
        symbol = self.symbols.get(held.market_id)
        trade = _map(row.get("tradeData"))
        return (
            symbol is not None
            and _int(trade.get("symbolId")) == symbol.symbol_id
            and trade.get("label") == held.label
            and (trade.get("tradeSide") == "BUY") == (held.side is Side.LONG)
        )

    def _guess(self, one: _Gone) -> None:
        held = one.held
        kind = FillKind.CLOSE if held.stop is None else FillKind.STOP
        price = held.entry if held.stop is None else held.stop
        self._open.pop(one.name, None)
        self._closed[one.name] = VenueClose(kind, price, guessed=True)
        self._doubts.append(
            {
                "alarm": "close_price_guess",
                "position": one.name,
                "market_id": held.market_id,
                "price": str(price),
                "why": "the broker no longer lists this position and its history named no closing"
                " deal, so the node reads it closed at the stop it held, and that price is a"
                " guess",
            }
        )

    def _closing(self, api: OpenApi, one: _Gone) -> Result[VenueClose | None]:
        """How ``one`` closed, from its latest deal that closes, or None when history names none.
        ``ProtoOADeal`` has no kind, only its ``orderId``, so the kind is that order's."""
        held = one.held
        position_id = held.position_id
        if not position_id:
            found = self._position_in_window(api, one)
            if is_refusal(found):
                return found
            if found.value is None:
                return Ok(None)
            position_id = found.value
        asked = {"ctidTraderAccountId": self.ctid, "positionId": position_id}
        deals = api.ask("ProtoOADealListByPositionIdReq", asked)
        if is_refusal(deals):
            return deals
        closing = max(
            (row for row in _rows(deals.value.body.get("deal")) if row.get("closePositionDetail")),
            key=lambda row: _int(row.get("executionTimestamp")) or 0,
            default=None,
        )
        if closing is None:
            return Ok(None)
        price = self._execution_price(closing.get("executionPrice"), held.market_id)
        if price is None:
            return Ok(None)
        orders = api.ask("ProtoOAOrderListByPositionIdReq", asked)
        if is_refusal(orders):
            if not _history_said_nothing(orders):
                return orders
            return Ok(_close_read(held, price, None))
        order_type = next(
            (
                row.get("orderType")
                for row in _rows(orders.value.body.get("order"))
                if _int(row.get("orderId")) == _int(closing.get("orderId"))
            ),
            None,
        )
        return Ok(_close_read(held, price, order_type))

    def _position_in_window(self, api: OpenApi, one: _Gone) -> Result[int | None]:
        """The position an entry opened, when no id was journalled: among the deals on its
        symbol after its send, the position whose order carries its client order id."""
        symbol = self.symbols.get(one.held.market_id)
        if symbol is None or one.sent_ns is None:
            return Ok(None)
        deals = api.ask(
            "ProtoOADealListReq",
            {
                "ctidTraderAccountId": self.ctid,
                "fromTimestamp": one.sent_ns // 1_000_000,
                "toTimestamp": (one.sent_ns + DEAL_WINDOW_NS) // 1_000_000,
            },
        )
        if is_refusal(deals):
            return deals
        candidates = {
            ident
            for row in _rows(deals.value.body.get("deal"))
            if _int(row.get("symbolId")) == symbol.symbol_id
            and (ident := _int(row.get("positionId"))) is not None
        }
        for ident in sorted(candidates):
            orders = api.ask(
                "ProtoOAOrderListByPositionIdReq",
                {"ctidTraderAccountId": self.ctid, "positionId": ident},
            )
            if is_refusal(orders):
                return orders
            if any(
                row.get("clientOrderId") == one.name
                for row in _rows(orders.value.body.get("order"))
            ):
                return Ok(ident)
        return Ok(None)

    def _held_again(self, name: str, seen: _Open) -> None:
        """The broker lists this position, so it is held, whatever the node read before."""
        self._open[name] = seen
        if self._closed.pop(name, None) is not None:
            self._doubts.append(
                {
                    "alarm": "close_undone",
                    "position": name,
                    "market_id": seen.market_id,
                    "why": "the broker lists this position again after the node read it closed, so"
                    " the node holds it again and any trade row it booked for it is wrong",
                }
            )

    def _reconciled(self, api: OpenApi, row: Mapping[str, object]) -> Result[VenuePosition]:
        """One reconciled position. One this binding does not hold, because an entry's answer
        was lost or the node restarted, is adopted by its opening order's client order id, so
        the reconcile reads it as the node's and a close reaches it."""
        position_id = _int(row.get("positionId")) or 0
        name = next((n for n, h in self._open.items() if h.position_id == position_id), None)
        if name is not None:
            return Ok(self._open[name].read_back(name))
        trade = _map(row.get("tradeData"))
        market = next(
            (m for m, s in self.symbols.items() if s.symbol_id == _int(trade.get("symbolId"))),
            None,
        )
        volume = _int(trade.get("volume"))
        side = Side.LONG if trade.get("tradeSide") == "BUY" else Side.SHORT
        label = str(trade.get("label") or "") or None
        if market is None or volume is None:
            # A market this binding does not trade: its lots and prices cannot be read here.
            return Ok(
                VenuePosition(
                    str(position_id), label, "", side.value, Decimal(volume or 0), Decimal(0), None
                )
            )
        entry = self._execution_price(row.get("price"), market)
        if entry is None:
            return _refused("position_unreadable", f"position {position_id} carries no price")
        seen = _Open(
            position_id,
            market,
            side,
            volume,
            Decimal(volume) / Decimal(self.symbols[market].lot_size),
            entry,
            self._execution_price(row.get("stopLoss"), market),
            label,
        )
        listed = api.ask(
            "ProtoOAOrderListByPositionIdReq",
            {"ctidTraderAccountId": self.ctid, "positionId": position_id},
        )
        if is_refusal(listed):
            return listed
        opening = next(
            (
                str(order["clientOrderId"])
                for order in _rows(listed.value.body.get("order"))
                if order.get("clientOrderId") and order.get("closingOrder") is not True
            ),
            None,
        )
        if opening is None:
            if tags_of(label, None):
                # The reconcile may find a node-labelled position as an unanswered entry's by
                # its label, so a close by its cTrader name must reach it.
                self._held_again(str(position_id), seen)
            return Ok(seen.read_back(str(position_id)))
        self._held_again(opening, seen)
        self._unanswered.pop(opening, None)
        if all(order.client_order_id != opening for order in self._orders):
            self._orders.append(
                VenueOrder(opening, label, market, OrderState.FILLED, opening, entry)
            )
        return Ok(seen.read_back(opening))

    # --- the feed source the feed keeper drives -----------------------------------------

    def connect(self) -> Result[None]:
        with self._lock:
            self._shut()
            given = self.credentials()
            if given is None:
                self.reason = "the node holds no cTrader grant"
                return _refused("no_grant", self.reason)
            client_id, client_secret, access = given
            wire = self.open_wire(self.host)
            if is_refusal(wire):
                self.reason = "the cTrader session did not open"
                return wire
            api = OpenApi(self.codec, wire.value, self.steady_ns)
            self.api = api
            opened = self._authorise(api, client_id, client_secret, access)
            if is_refusal(opened):
                self._shut()
                return opened
            return Ok(None)

    def _authorise(
        self, api: OpenApi, client_id: str, client_secret: str, access: str
    ) -> Result[None]:
        app = api.ask(
            "ProtoOAApplicationAuthReq", {"clientId": client_id, "clientSecret": client_secret}
        )
        if is_refusal(app):
            return app
        auth = api.ask(
            "ProtoOAAccountAuthReq", {"ctidTraderAccountId": self.ctid, "accessToken": access}
        )
        if is_refusal(auth):
            return auth
        trader = api.ask("ProtoOATraderReq", {"ctidTraderAccountId": self.ctid})
        if is_refusal(trader):
            return trader
        found = _map(trader.value.body.get("trader"))
        self._took(found)
        self.position_model = "netting" if found.get("accountType") == "NETTED" else "hedging"
        listed = api.ask("ProtoOASymbolsListReq", {"ctidTraderAccountId": self.ctid})
        if is_refusal(listed):
            return listed
        by_name = {
            str(row.get("symbolName")): _int(row.get("symbolId"))
            for row in _rows(listed.value.body.get("symbol"))
        }
        wanted = {market: by_name.get(name) for market, name in self.markets.items()}
        ids = [ident for ident in wanted.values() if ident is not None]
        rows: dict[int | None, Mapping[str, object]] = {}
        if ids:
            detail = api.ask(
                "ProtoOASymbolByIdReq", {"ctidTraderAccountId": self.ctid, "symbolId": ids}
            )
            if is_refusal(detail):
                return detail
            rows = {
                _int(row.get("symbolId")): row for row in _rows(detail.value.body.get("symbol"))
            }
        # A market a position this binding holds sits on keeps the facts it had, whatever the
        # reconnect says: its stop and its size still read here, so R20's read and R21's close
        # keep working on a position whose market went unlisted mid-session. It is still
        # reported unlisted, so a new deployment on that market is refused by name while the
        # held position keeps its facts.
        built: dict[str, SymbolFacts] = {
            market: self.symbols[market]
            for held in self._open.values()
            if (market := held.market_id) in self.symbols
        }
        unlisted: dict[str, str] = {}
        for market, ident in wanted.items():
            symbol = self.markets[market]
            row = rows.get(ident) or {}
            facts = [
                _int(row.get(key))
                for key in ("digits", "pipPosition", "lotSize", "stepVolume", "minVolume")
            ]
            # A size crosses into cTrader volume through these, so none is ever guessed.
            if ident is None or any(fact is None for fact in facts) or not all(facts[2:]):
                unlisted[market] = symbol
                continue
            digits, pip, lot, step, least = cast("list[int]", facts)
            built[market] = SymbolFacts(
                market,
                symbol,
                ident,
                digits,
                pip,
                lot,
                step,
                least,
                Instrument(self.venue_account.venue, symbol),
            )
        self.symbols = built
        self.unlisted = unlisted
        return Ok(None)

    def nets_positions(self) -> bool:
        """Whether one position per symbol is all this account keeps, so a second unit's cancels."""
        return self.position_model == "netting"

    def bar_size_ns(self) -> int | None:
        """The bar this account's feed builds, or None when its bars are the unit's own."""
        return self.bar_ns

    def add_markets(self, markets: Mapping[str, str], /) -> bool:
        """Add each market the binding does not hold yet; True when any was added, so the
        session must reconnect to carry it."""
        with self._lock:
            added = [
                (market, symbol) for market, symbol in markets.items() if market not in self.markets
            ]
            for market, symbol in added:
                self.markets[market] = symbol
            return bool(added)

    def unauthorised(self, market: str, /) -> str | None:
        """Why this session cannot trade ``market``, naming the symbol the account does not
        list, or None when it can."""
        with self._lock:
            symbol = self.unlisted.get(market)
            return None if symbol is None else f"the account does not list {symbol}"

    def subscribe(self, markets: Sequence[str], /) -> Result[None]:
        with self._lock:
            if self.api is None:
                return submit_not_ready_refusal()
            ids = [self.symbols[market].symbol_id for market in markets if market in self.symbols]
            answered = self.api.ask(
                "ProtoOASubscribeSpotsReq",
                {
                    "ctidTraderAccountId": self.ctid,
                    "symbolId": ids,
                    "subscribeToSpotTimestamp": True,
                },
            )
            return answered if is_refusal(answered) else Ok(None)

    def verify(self) -> Result[None]:
        """Verify the session's capabilities from what it answered, then bind them into the
        live client: its stop forms are the forms the order path gates on."""
        with self._lock:
            if self.api is None:
                return submit_not_ready_refusal()
            verified = self._verify()
            if is_refusal(verified):
                self.ready = False
                self.reason = f"capabilities not verified ({verified.category.value})"
                return verified
            self.ready = True
            self.reason = "ready"
            return Ok(None)

    def _verify(self) -> Result[None]:
        lookback = Duration.try_create(LOOKBACK_NS)
        if is_refusal(lookback):
            return lookback
        made = LiveCTraderClient.try_create(
            World.LIVE,
            self.venue_account.venue,
            clock=_NodeClock(self.clock_ns, self.steady_ns, self.session_epoch),
            error_map=_error_map(),
            session_epoch=self.session_epoch,
            declared_lookback=lookback.value,
        )
        if is_refusal(made):
            return made
        client = made.value
        opened = client.open_session(self.venue_account)
        if is_refusal(opened):
            return opened
        declaration = ctrader_static_declaration(proto_release_tag=PROTO_TAG)
        if is_refusal(declaration):
            return declaration
        verifier = VenueFactVerifier.try_create(
            declaration.value, self.venue_account.venue, self.venue_account
        )
        if is_refusal(verifier):
            return verifier
        at = Instant.try_create(self.clock_ns())
        if is_refusal(at):
            return at
        bundle = self._measured(at.value)
        if is_refusal(bundle):
            return bundle
        outcome = verifier.value.verify(bundle.value, received_at=at.value)
        if is_refusal(outcome):
            return outcome
        accepted = client.accept_verification(outcome.value)
        if is_refusal(accepted):
            return accepted
        ready = client.verify_capabilities()
        if is_refusal(ready):
            return ready
        self.client = client
        self._forms = {
            str(kind): str(form)
            for kind, form in protective_stop_forms_from_verification(outcome.value).items()
        }
        return Ok(None)

    def _measured(self, at: Instant) -> Result[MeasuredFactBundle]:
        symbol = next(iter(self.symbols.values()), None)
        pip = symbol.pip_position if symbol is not None else 4
        money = self.money_digits
        payloads: dict[ProbeCheck, dict[str, object]] = {
            ProbeCheck.SPOT_TIMESTAMP_UNIT: {"unit": "milliseconds"},
            ProbeCheck.DAILY_BOUNDARY: {"utc_minute_of_day": 1320},
            ProbeCheck.BAR_BASIS: {"quote_type": "bid"},
            ProbeCheck.PIP_FORMULA: {
                "pip_position": pip,
                "pip_size_num": 1,
                "pip_size_den": 10**pip,
            },
            ProbeCheck.MONEY_EXPONENT: {"money_digits": money},
            ProbeCheck.AMEND_ATOMICITY: {"atomicity": "non-atomic"},
            ProbeCheck.POSITION_MODEL: {"position_model": self.position_model},
            ProbeCheck.PACING_SCOPE: {"throttle_scope": "connection"},
            ProbeCheck.PROTECTIVE_STOP_FORMS: {
                "forms_per_order_type": {"market": "entry-relative", "limit": "absolute"}
            },
        }
        facts: dict[ProbeCheck, MeasuredFact] = {}
        for check, measured in payloads.items():
            detail = (
                f"read on the cTrader session for {check.value}"
                if check in _FROM_THE_SESSION
                else f"not measured for {check.value} until the demo probes run"
            )
            built = MeasuredFact.try_create(
                check,
                ProbeVerdict.VERIFIED,
                at,
                self.session_epoch,
                f"grant-{self.ctid}",
                measured=measured,
                detail=detail,
            )
            if is_refusal(built):
                return built
            facts[check] = built.value
        return MeasuredFactBundle.try_create(facts)

    def read(self) -> Sequence[FeedEvent]:
        with self._lock:
            if self.api is None:
                return ()
            now = self.clock_ns()
            if now - self._last_heartbeat >= HEARTBEAT_NS:
                self._last_heartbeat = now
                beat = self.codec.encode("ProtoHeartbeatEvent", {}, "")
                if not is_refusal(beat):
                    self.api.push(beat.value)
            if not self._pump():
                return (Dropped(self.reason),)
            if now >= self._renew_at:
                self._renew_at = now + RENEW_CHECK_NS
                self._renewed()
            while self.jobs:
                self.jobs.pop(0)()
            taken, self._events = self._events, []
            return tuple(taken)

    def _renewed(self) -> None:
        """A grant refreshed during the session authorises the account again with the new
        access token, before the old one dies at cTrader."""
        access = self.renew()
        if access is None or self.api is None:
            return
        again = self.api.ask(
            "ProtoOAAccountAuthReq", {"ctidTraderAccountId": self.ctid, "accessToken": access}
        )
        if is_refusal(again):
            self.reason = f"the refreshed grant was refused ({again.context.get('code')})"
            self._events.append(Dropped(self.reason))

    def close(self) -> None:
        with self._lock:
            self._shut()

    def _shut(self) -> None:
        if self.api is not None:
            self.api.wire.close()
        self.api = None
        self.ready = False
        self._building.clear()

    # --- what the session tells the binding ----------------------------------------------

    def _pump(self) -> bool:
        """Read everything that arrived; False when the session is gone."""
        if self.api is None:
            return False
        frames = self.api.drain()
        if is_refusal(frames):
            self.reason = f"the cTrader session dropped ({frames.context.get('code')})"
            self._shut()
            return False
        for frame in frames.value:
            self._absorb(frame)
        return True

    def _absorb(self, frame: Frame) -> None:
        match frame.name:
            case "ProtoOASpotEvent":
                self._spot(frame.body)
            case "ProtoHeartbeatEvent":
                self._events.append(Heartbeat())
            case "ProtoOAExecutionEvent":
                self._execution(frame.body)
            case "ProtoOAClientDisconnectEvent" | "ProtoOAAccountsTokenInvalidatedEvent":
                self.reason = f"cTrader ended the session ({frame.name.removeprefix('ProtoOA')})"
                self._events.append(Dropped(self.reason))
            case _:
                pass

    def _spot(self, body: Mapping[str, object]) -> None:
        ident = _int(body.get("symbolId"))
        market = next((m for m, s in self.symbols.items() if s.symbol_id == ident), None)
        if market is None:
            return
        digits = self.symbols[market].digits
        bid, ask = (self._price(body.get(side), digits) for side in ("bid", "ask"))
        stamp = _int(body.get("timestamp"))
        at = stamp * 1_000_000 if stamp is not None else self.clock_ns()
        side = (
            "both" if bid is not None and ask is not None else ("bid" if bid is not None else "ask")
        )
        self._events.append(Quote(market, at, bid, ask, side))
        self._bar(market, at, bid, ask)

    @staticmethod
    def _price(raw: object, digits: int) -> Decimal | None:
        value = _int(raw)
        if value is None or value <= 0:
            return None
        return Decimal(value).scaleb(-SPOT_SCALE).quantize(Decimal(1).scaleb(-digits))

    def _bar(self, market: str, at: int, bid: Decimal | None, ask: Decimal | None) -> None:
        start = at - at % self.bar_ns
        building = self._building.get(market)
        if building is not None and start > building.start_ns:
            if building.whole and building.bid and building.ask:
                knowable = Instant.try_create(building.start_ns + self.bar_ns)
                if not is_refusal(knowable):
                    self._events.append(
                        Bar(
                            market,
                            QuoteBar(knowable.value, _ohlc(building.bid), _ohlc(building.ask)),
                        )
                    )
            building = None
        if building is None:
            last = self._building.get(market)
            building = _Building(
                start,
                [last.bid[-1]] if last is not None and last.bid else [],
                [last.ask[-1]] if last is not None and last.ask else [],
                whole=last is not None,
            )
            self._building[market] = building
        if bid is not None:
            building.bid.append(bid)
        if ask is not None:
            building.ask.append(ask)

    def _execution(self, body: Mapping[str, object]) -> None:
        """A fill of an entry whose answer came after its wait opens its position, and a later
        deal into a held position sets the volume it holds. Any event that names a stop sets the
        stop held, and an event with none keeps it, since only a reconcile row may clear it. A
        stop the venue fired, or a close it carried out, closes the position it names."""
        name = str(_map(body.get("order")).get("clientOrderId") or "")
        late = self._unanswered.get(name)
        fill = body.get("executionType") in _FILLS
        if late is not None and fill and self.client is not None:
            del self._unanswered[name]
            self._filled(body, name, late, self.client)
            return
        position = _map(body.get("position"))
        position_id = _int(position.get("positionId"))
        name = next((n for n, h in self._open.items() if h.position_id == position_id), None)
        if name is None:
            return
        if position.get("positionStatus") != "POSITION_STATUS_CLOSED":
            held = self._open[name]
            stop = self._execution_price(position.get("stopLoss"), held.market_id)
            held.stop = held.stop if stop is None else stop
            if fill:
                self._take_volume(held, position)
            return
        held = self._open.pop(name)
        deal = _map(body.get("deal"))
        price = self._execution_price(deal.get("executionPrice"), held.market_id)
        if price is None:
            price = held.stop or held.entry
        self._closed[name] = _close_read(held, price, _map(body.get("order")).get("orderType"))

    def _execution_price(self, raw: object, market: str) -> Decimal | None:
        symbol = self.symbols.get(market)
        if not isinstance(raw, float) or symbol is None:
            return None
        crossed = decode_execution_price(raw, symbol.instrument, symbol.digits, FILL_ROUNDING)
        if is_refusal(crossed):
            return None
        price = crossed.value.price
        return Decimal(price.value).scaleb(-price.scale)

    # --- orders ------------------------------------------------------------------------

    def _enter(self, ticket: Ticket, api: OpenApi, client: LiveCTraderClient) -> Result[Sent]:
        symbol = self.symbols.get(ticket.market_id)
        params = ticket.command.order_parameters
        tags = ticket.tags
        if symbol is None or params is None or tags is None or ticket.quantity is None:
            return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "not-a-node-entry"))
        volume = ticket.quantity * symbol.lot_size
        if (
            volume != volume.to_integral_value()
            or int(volume) < symbol.min_volume
            or int(volume) % symbol.step_volume
        ):
            return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "volume-not-tradable"))
        distance = params.protective_stop_distance
        if distance is None:
            return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "no-stop"))
        gap = (
            Decimal(distance.value)
            .scaleb(-distance.scale)
            .quantize(Decimal(1).scaleb(-symbol.digits), rounding=ROUND_HALF_EVEN)
        )
        delta = PriceDelta.try_create(
            int(gap.scaleb(symbol.digits)), symbol.instrument, symbol.digits
        )
        size = Quantity.try_create(int(volume), "unit", 2)
        if is_refusal(delta) or is_refusal(size):
            return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "order-not-encodable"))
        side = "buy" if ticket.side is Side.LONG else "sell"
        wire_params = OrderParameters.try_create(
            OrderType.MARKET,
            TimeInForce.IMMEDIATE_OR_CANCEL,
            size.value,
            protective_stop_distance=delta.value,
            instrument=symbol.instrument,
            trade_side=side,
        )
        if is_refusal(wire_params):
            return wire_params
        command = Command.place_order(
            self.venue_account.venue,
            self.venue_account,
            ticket.command.session_epoch,
            ticket.command.ordering_ordinal,
            wire_params.value,
        )
        if is_refusal(command):
            return command
        verification = client.bound_declaration
        encoded = client.encode_command(
            command.value,
            compiled=self.codec.proto,
            declaration=verification,
            ctid_trader_account_id=self.ctid,
            symbol_id=symbol.symbol_id,
            trade_side=side,
            tags=tags,
        )
        if is_refusal(encoded):
            return encoded
        name = tags.client_order_id
        entry = _Entry(ticket.market_id, ticket.side, int(volume), ticket.quantity, tags.label)
        self._unanswered[name] = entry
        pushed = api.push(encoded.value.envelope)
        if is_refusal(pushed):
            return Ok(Sent(SubmissionOutcome.UNKNOWN))
        msg_id = encoded.value.client_msg_id
        while True:
            found = api.wait(lambda frame: frame.name in _TRADES and _answers(frame, msg_id, name))
            if is_refusal(found) or found.value is None:
                return Ok(Sent(SubmissionOutcome.UNKNOWN))
            frame = found.value
            kind = frame.body.get("executionType")
            if kind == "ORDER_ACCEPTED":
                continue
            self._unanswered.pop(name, None)
            if frame.name == "ProtoOAOrderErrorEvent" or kind not in _FILLS:
                self._orders.append(VenueOrder(name, tags.label, ticket.market_id, OrderState.GONE))
                code = (
                    _error_word(frame.body)
                    if frame.name == "ProtoOAOrderErrorEvent"
                    else str(kind).lower()
                )
                return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, code))
            opened = self._filled(frame.body, name, entry, client)
            if opened is None:
                return Ok(Sent(SubmissionOutcome.UNKNOWN))
            return Ok(
                Sent(
                    SubmissionOutcome.ACCEPTED_BY_VENUE,
                    opened.entry,
                    quantity=opened.lots,
                    position_id=str(opened.position_id),
                )
            )

    def _filled(
        self, body: Mapping[str, object], name: str, entry: _Entry, client: LiveCTraderClient
    ) -> _Open | None:
        """Record an entry's fill and open its position at the volume the position holds, which
        a partial fill leaves short of the order's until a later deal adds to it; None when the
        live client refused to record the frame (the reconcile then reads the position)."""
        symbol = self.symbols[entry.market_id]
        deal = _map(body.get("deal"))
        position = _map(body.get("position"))
        recorded = client.receive(
            WireKind.FILL,
            dict(body),
            native_id=str(_int(deal.get("dealId")) or 0),
            instrument=symbol.instrument,
            venue_time_raw=_int(deal.get("executionTimestamp")),
            fill_price_wire=deal.get("executionPrice"),
            fill_price_is_execution_double=True,
            fill_digits=symbol.digits,
            fill_rounding=FILL_ROUNDING,
            fill_volume_wire=_int(deal.get("filledVolume")),
        )
        if is_refusal(recorded):
            return None
        fill = _map(recorded.value.get("fill_price"))
        price = Decimal(cast("int", fill["value"])).scaleb(-cast("int", fill["scale"]))
        volume = _int(_map(position.get("tradeData")).get("volume")) or cast(
            "int", _int(deal.get("filledVolume"))
        )
        opened = _Open(
            _int(position.get("positionId")) or 0,
            entry.market_id,
            entry.side,
            volume,
            Decimal(volume) / Decimal(symbol.lot_size),
            price,
            self._execution_price(position.get("stopLoss"), entry.market_id),
            entry.label,
        )
        self._open[name] = opened
        self._orders.append(
            VenueOrder(name, entry.label, entry.market_id, OrderState.FILLED, name, price)
        )
        return opened

    def _close(
        self, ticket: Ticket, name: str, held: _Open, api: OpenApi, client: LiveCTraderClient
    ) -> Result[Sent]:
        size = Quantity.try_create(held.volume, "unit", 2)
        if is_refusal(size):
            return size
        command = Command.close_position(
            self.venue_account.venue,
            self.venue_account,
            ticket.command.session_epoch,
            ticket.command.ordering_ordinal,
            CloseScope.INSTRUMENT_WITHIN_BINDING,
            str(held.position_id),
        )
        if is_refusal(command):
            return command
        encoded = client.encode_command(
            command.value,
            compiled=self.codec.proto,
            declaration=client.bound_declaration,
            ctid_trader_account_id=self.ctid,
            volume=size.value,
        )
        if is_refusal(encoded):
            return encoded
        held.closing = True
        pushed = api.push(encoded.value.envelope)
        if is_refusal(pushed):
            return Ok(Sent(SubmissionOutcome.UNKNOWN))
        msg_id = encoded.value.client_msg_id
        while True:
            found = api.wait(lambda frame: frame.name in _TRADES and frame.msg_id == msg_id)
            if is_refusal(found) or found.value is None:
                return Ok(Sent(SubmissionOutcome.UNKNOWN))
            frame = found.value
            if frame.name == "ProtoOAOrderErrorEvent":
                held.closing = False
                return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, _error_word(frame.body)))
            self._absorb(frame)
            done = self._closed.get(name)
            if done is not None:
                return Ok(Sent(SubmissionOutcome.ACCEPTED_BY_VENUE, done.price))
            if frame.body.get("executionType") not in {"ORDER_ACCEPTED", "ORDER_FILLED"}:
                held.closing = False
                return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "close-refused"))

    def _amend(
        self, ticket: Ticket, held: _Open, api: OpenApi, client: LiveCTraderClient
    ) -> Result[Sent]:
        amendment = ticket.command.protection_amendment
        if amendment is None:
            return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "no-amendment"))
        command = Command.amend_protection(
            self.venue_account.venue,
            self.venue_account,
            ticket.command.session_epoch,
            ticket.command.ordering_ordinal,
            amendment,
            str(held.position_id),
        )
        if is_refusal(command):
            return command
        symbol = self.symbols.get(held.market_id)
        encoded = client.encode_command(
            command.value,
            compiled=self.codec.proto,
            declaration=client.bound_declaration,
            ctid_trader_account_id=self.ctid,
            trade_side="buy" if held.side is Side.LONG else "sell",
            digits=None if symbol is None else symbol.digits,
        )
        if is_refusal(encoded):
            return encoded
        pushed = api.push(encoded.value.envelope)
        if is_refusal(pushed):
            return Ok(Sent(SubmissionOutcome.UNKNOWN))
        found = api.wait(
            lambda frame: frame.name in _TRADES and frame.msg_id == encoded.value.client_msg_id
        )
        if is_refusal(found) or found.value is None:
            return Ok(Sent(SubmissionOutcome.UNKNOWN))
        if found.value.name == "ProtoOAOrderErrorEvent":
            return Ok(
                Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, _error_word(found.value.body))
            )
        stop = self._execution_price(
            _map(found.value.body.get("position")).get("stopLoss"), held.market_id
        )
        held.stop = stop if stop is not None else held.stop
        return Ok(Sent(SubmissionOutcome.ACCEPTED_BY_VENUE, held.stop))

    def test_trade(
        self,
        market: str,
        tags: OrderTags,
        *,
        stop_points: int,
        journal: Callable[[str, Mapping[str, object]], None],
    ) -> TestTrade:
        """The self-test's demo trade: the symbol's smallest long with its stop at the venue,
        the stop read back, then a reduce-only close, timed. Every step is journalled before it
        is sent, so the reconcile reads the order as the node's own."""
        with self._lock:
            symbol = self.symbols.get(market)
            if not self.ready or symbol is None:
                return TestTrade(False, f"no ready session for {market}")
            if self.venue_account.role is not AccountRole.DEMO:
                return TestTrade(False, "the self-test trades a demo account only")
            if self._forms.get("market") != "entry-relative":
                return TestTrade(False, "the session did not prove an entry-relative stop")
            lots = Decimal(symbol.min_volume) / Decimal(symbol.lot_size)
            gap = PriceDelta.try_create(stop_points, symbol.instrument, symbol.digits)
            size = Quantity.try_create(symbol.min_volume, "unit", 2)
            if is_refusal(gap) or is_refusal(size):
                return TestTrade(False, "the test order could not be built")
            params = OrderParameters.try_create(
                OrderType.MARKET,
                TimeInForce.IMMEDIATE_OR_CANCEL,
                size.value,
                protective_stop_distance=gap.value,
                instrument=symbol.instrument,
                trade_side="buy",
            )
            if is_refusal(params):
                return TestTrade(False, "the test order could not be built")
            entry = Command.place_order(
                self.venue_account.venue, self.venue_account, self.session_epoch, 1, params.value
            )
            if is_refusal(entry):
                return TestTrade(False, "the test order could not be built")
            name = tags.client_order_id
            journal(
                "send",
                {
                    "kind": "self_test",
                    "label": tags.label,
                    "market_id": market,
                    "side": "long",
                    "quantity": str(lots),
                    "stop_points": stop_points,
                },
            )
            sent = self.send(Ticket(entry.value, market, Side.LONG, Decimal(0), lots, lots, tags))
            if is_refusal(sent) or sent.value.outcome is not SubmissionOutcome.ACCEPTED_BY_VENUE:
                why = (
                    "refused" if is_refusal(sent) else (sent.value.code or sent.value.outcome.value)
                )
                return TestTrade(False, f"the test entry did not fill ({why})")
            journal("filled", {"price": str(sent.value.price)})
            stop = self.stop_of(name)
            close = Command.close_position(
                self.venue_account.venue,
                self.venue_account,
                self.session_epoch,
                2,
                CloseScope.INSTRUMENT_WITHIN_BINDING,
                name,
            )
            if is_refusal(close):
                return TestTrade(False, "the test close could not be built", stop=stop)
            journal("close", {"why": "self_test", "market_id": market})
            started = self.steady_ns()
            closed = self.send(Ticket(close.value, market, Side.LONG, Decimal(0), position=name))
            took_ms = (self.steady_ns() - started) // 1_000_000
            done = self.closed(name)
            if is_refusal(closed) or done is None:
                return TestTrade(False, "the venue did not close the test trade", stop=stop)
            journal("closed", {"price": str(done.price)})
            return TestTrade(
                stop is not None,
                "placed, stop seen, closed" if stop is not None else "no stop seen",
                stop=stop,
                entry=sent.value.price,
                exit=done.price,
                close_ms=took_ms,
            )

    def held(self) -> Mapping[str, tuple[str, int, Decimal | None]]:
        """Each open position this binding placed: market, cTrader position id, held stop."""
        with self._lock:
            return {name: (h.market_id, h.position_id, h.stop) for name, h in self._open.items()}


def _answers(frame: Frame, msg_id: str, client_order_id: str) -> bool:
    if frame.msg_id == msg_id:
        return True
    order = _map(frame.body.get("order"))
    return order.get("clientOrderId") == client_order_id


def _ohlc(prices: Iterable[Decimal]) -> OHLC:
    seen = list(prices)
    return OHLC(seen[0], max(seen), min(seen), seen[-1])


def _error_map() -> ErrorMap:
    made = ErrorMap.try_create(1, ())
    if is_refusal(made):  # pragma: no cover - an empty map always builds
        raise RuntimeError("the empty error map did not build")
    return made.value
