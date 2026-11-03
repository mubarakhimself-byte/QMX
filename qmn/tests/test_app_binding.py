"""The node binds a cTrader demo account and proves it with its self-test (C-12d).

The rig is C-12a's node on a throwaway folder with its cTrader door. cTrader is faked twice: a
token endpoint that answers the sign-in, and :class:`FakeCTrader`, a demo broker that speaks the
pinned Spotware definitions (release 91) on the wire. Everything between them is the node's own
code: the grant store, the door, :class:`~qmn.venue.ctrader_account.CTraderVenue` and
:class:`~qmn.venue.live.LiveCTraderClient`. No account and no network is reached.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from itertools import groupby
from pathlib import Path
from typing import ClassVar, cast

import pytest
import test_app_runtime as base
from qmf.core import Ok, PriceDelta, Quantity, Result, TypedRefusal
from qmf.venue.commands import (
    CloseScope,
    Command,
    OrderParameters,
    OrderType,
    SubmissionOutcome,
    TimeInForce,
)
from qml.unit.model import Side
from qmn.app import grants as grants_module
from qmn.app import server
from qmn.app.attribution import Claim, OrderState, VenueOrder, VenuePosition, attribute
from qmn.app.grants import Grants, TokenEndpoint
from qmn.app.runtime import Phase, Runtime, Ticket
from qmn.app.server import DEFINITIONS, CTraderDoor, Node, open_node
from qmn.app.store import Json, Store
from qmn.venue import order_tags
from qmn.venue.ctrader_account import Codec, CTraderVenue, Wire

KEYS = json.dumps(
    {
        "schema_version": "qmx.node.keys/1",
        "ctrader": {"client_id": "app-77", "client_secret": "app-secret-77"},
    }
)
ACCOUNT = base.ACCOUNT
CTID = 4401
DIGEST = "c" * 64
CHECKS = [
    "broker session",
    "feed freshness",
    "demo test trade with its stop placed, observed and closed",
    "kill-switch latency",
    "image digest",
]
"""``SELF_TEST_CHECKS`` as the connect dialog names them (``connect_node.py``)."""


class Tokens:
    """A fake cTrader token endpoint: every code and refresh gets the next numbered pair."""

    def __init__(self, lifetime_s: int = 2_628_000) -> None:
        self.pairs = 0
        self.lifetime_s = lifetime_s
        self.asked: list[str] = []
        self.refuse_refresh = False

    def __call__(self, method: str, url: str) -> tuple[int, bytes]:
        self.asked.append(method)
        if method == "POST" and self.refuse_refresh:
            return 400, json.dumps({"errorCode": "INVALID_REQUEST"}).encode()
        self.pairs += 1
        body = {
            "accessToken": f"fake-a{self.pairs}",
            "refreshToken": f"fake-r{self.pairs}",
            "expiresIn": self.lifetime_s,
            "tokenType": "bearer",
        }
        return 200, json.dumps(body).encode()


@dataclass
class Held:
    position_id: int
    symbol_id: int
    side: str
    volume: int
    price: Decimal
    stop: Decimal | None
    label: str
    client_order_id: str


@dataclass
class FakeCTrader:
    """A demo cTrader broker on the wire: it authorises the node's app and its access tokens,
    lists one demo account (and a live one when asked), quotes its symbols, fills market
    orders at its quote with their relative stop, fires those stops on its bars and closes on
    request. Every request it received is kept by name."""

    codec: Codec
    live_account: bool = False
    holds_stops: bool = True
    lose_answers: int = 0
    """How many coming entries fill at the broker with every answer lost."""
    tokens: set[str] = field(default_factory=lambda: {"fake-a1"})
    received: list[tuple[str, dict[str, object]]] = field(
        default_factory=list[tuple[str, dict[str, object]]]
    )
    held: dict[int, Held] = field(default_factory=dict[int, Held])
    orders: dict[int, list[dict[str, object]]] = field(
        default_factory=dict[int, list[dict[str, object]]]
    )
    """The orders on each position, opening order first."""
    quotes: dict[int, tuple[Decimal, Decimal]] = field(
        default_factory=dict[int, tuple[Decimal, Decimal]]
    )
    opened: int = 0
    _out: list[bytes] = field(default_factory=list[bytes])
    _next: int = 9000
    _open: bool = False

    SYMBOLS: ClassVar[dict[str, tuple[int, int, int, int]]] = {
        "EURUSD": (1, 5, 4, 10_000_000),
        "XAUUSD": (41, 2, 1, 10_000),
    }

    def connect(self) -> Result[Wire]:
        self.opened += 1
        self._open = True
        return Ok(self)

    # --- the wire ---

    def send(self, envelope: bytes, /) -> Result[None]:
        frame = self.codec.decode(envelope)
        assert not isinstance(frame, TypedRefusal), frame
        name, body = frame.value.name, dict(frame.value.body)
        self.received.append((name, body))
        answer = getattr(self, f"_on_{name}", None)
        if answer is not None:
            answer(frame.value.msg_id, body)
        return Ok(None)

    def receive(self, wait_s: float, /) -> Result[bytes | None]:
        return Ok(self._out.pop(0) if self._out else None)

    def close(self) -> None:
        self._open = False

    def _say(self, name: str, values: Mapping[str, object], msg_id: str = "") -> None:
        encoded = self.codec.encode(name, values, msg_id)
        assert not isinstance(encoded, TypedRefusal), encoded
        self._out.append(encoded.value)

    def _error(self, msg_id: str, code: str) -> None:
        self._say("ProtoOAErrorRes", {"errorCode": code}, msg_id)

    # --- requests ---

    def _on_ProtoOAApplicationAuthReq(self, msg_id: str, body: dict[str, object]) -> None:
        if (body.get("clientId"), body.get("clientSecret")) != ("app-77", "app-secret-77"):
            self._error(msg_id, "CH_CLIENT_AUTH_FAILURE")
            return
        self._say("ProtoOAApplicationAuthRes", {}, msg_id)

    def _on_ProtoOAGetAccountListByAccessTokenReq(
        self, msg_id: str, body: dict[str, object]
    ) -> None:
        accounts: list[dict[str, object]] = [
            {
                "ctidTraderAccountId": CTID,
                "isLive": False,
                "traderLogin": 5501,
                "brokerTitleShort": "ICM",
            }
        ]
        if self.live_account:
            accounts.append(
                {
                    "ctidTraderAccountId": 4402,
                    "isLive": True,
                    "traderLogin": 5502,
                    "brokerTitleShort": "ICM",
                }
            )
        self._say(
            "ProtoOAGetAccountListByAccessTokenRes",
            {
                "accessToken": body["accessToken"],
                "permissionScope": "SCOPE_TRADE",
                "ctidTraderAccount": accounts,
            },
            msg_id,
        )

    def _on_ProtoOAAccountAuthReq(self, msg_id: str, body: dict[str, object]) -> None:
        if body.get("accessToken") not in self.tokens:
            self._error(msg_id, "CH_ACCESS_TOKEN_INVALID")
            return
        self._say("ProtoOAAccountAuthRes", {"ctidTraderAccountId": CTID}, msg_id)

    def _on_ProtoOATraderReq(self, msg_id: str, _: dict[str, object]) -> None:
        self._say(
            "ProtoOATraderRes",
            {
                "ctidTraderAccountId": CTID,
                "trader": {
                    "ctidTraderAccountId": CTID,
                    "balance": 1_000_000,
                    "depositAssetId": 1,
                    "moneyDigits": 2,
                    "accountType": "HEDGED",
                },
            },
            msg_id,
        )

    def _on_ProtoOASymbolsListReq(self, msg_id: str, _: dict[str, object]) -> None:
        listed = [
            {"symbolId": ident, "symbolName": name, "enabled": True}
            for name, (ident, *_rest) in self.SYMBOLS.items()
        ]
        self._say("ProtoOASymbolsListRes", {"ctidTraderAccountId": CTID, "symbol": listed}, msg_id)

    def _on_ProtoOASymbolByIdReq(self, msg_id: str, body: dict[str, object]) -> None:
        wanted = {int(str(item)) for item in cast("list[object]", body.get("symbolId", []))}
        symbols = [
            {
                "symbolId": ident,
                "digits": digits,
                "pipPosition": pip,
                "lotSize": lot,
                "stepVolume": lot // 100,
                "minVolume": lot // 100,
            }
            for ident, digits, pip, lot in self.SYMBOLS.values()
            if ident in wanted
        ]
        self._say("ProtoOASymbolByIdRes", {"ctidTraderAccountId": CTID, "symbol": symbols}, msg_id)

    def _on_ProtoOASubscribeSpotsReq(self, msg_id: str, _: dict[str, object]) -> None:
        self._say("ProtoOASubscribeSpotsRes", {"ctidTraderAccountId": CTID}, msg_id)

    def _on_ProtoOAReconcileReq(self, msg_id: str, _: dict[str, object]) -> None:
        positions = [self._position(held, "POSITION_STATUS_OPEN") for held in self.held.values()]
        self._say(
            "ProtoOAReconcileRes", {"ctidTraderAccountId": CTID, "position": positions}, msg_id
        )

    def _on_ProtoOAOrderListByPositionIdReq(self, msg_id: str, body: dict[str, object]) -> None:
        listed = self.orders.get(int(str(body["positionId"])), [])
        self._say(
            "ProtoOAOrderListByPositionIdRes",
            {"ctidTraderAccountId": CTID, "order": listed, "hasMore": False},
            msg_id,
        )

    def _on_ProtoOANewOrderReq(self, msg_id: str, body: dict[str, object]) -> None:
        symbol = int(str(body["symbolId"]))
        side = str(body["tradeSide"])
        bid, ask = self.quotes[symbol]
        price = ask if side == "BUY" else bid
        relative = Decimal(int(str(body.get("relativeStopLoss", 0)))).scaleb(-5)
        stop = (
            (price - relative if side == "BUY" else price + relative)
            if self.holds_stops and relative
            else None
        )
        self._next += 1
        held = Held(
            self._next,
            symbol,
            side,
            int(str(body["volume"])),
            price,
            stop,
            str(body.get("label", "")),
            str(body.get("clientOrderId", "")),
        )
        self.held[held.position_id] = held
        self.orders[held.position_id] = [
            {
                "orderId": held.position_id,
                "tradeData": {
                    "symbolId": symbol,
                    "volume": held.volume,
                    "tradeSide": side,
                    "label": held.label,
                },
                "orderType": "MARKET",
                "orderStatus": "ORDER_STATUS_FILLED",
                "executionPrice": float(price),
                "clientOrderId": held.client_order_id,
                "positionId": held.position_id,
            }
        ]
        if self.lose_answers:
            self.lose_answers -= 1
            return
        for kind in ("ORDER_ACCEPTED", "ORDER_FILLED"):
            self._execution(kind, held, "POSITION_STATUS_OPEN", price, "MARKET", msg_id)

    def _on_ProtoOAClosePositionReq(self, msg_id: str, body: dict[str, object]) -> None:
        held = self.held.pop(int(str(body["positionId"])), None)
        if held is None:
            self._say(
                "ProtoOAOrderErrorEvent",
                {"ctidTraderAccountId": CTID, "errorCode": "POSITION_NOT_FOUND"},
                msg_id,
            )
            return
        bid, ask = self.quotes[held.symbol_id]
        price = bid if held.side == "BUY" else ask
        self._execution(
            "ORDER_FILLED", held, "POSITION_STATUS_CLOSED", price, "MARKET", msg_id, closing=True
        )

    # --- what the broker says on its own ---

    def quote(self, symbol: str, bid: Decimal, ask: Decimal, at_ms: int) -> None:
        """A spot on ``symbol``; a held stop the quote crosses fires at the stop."""
        ident = self.SYMBOLS[symbol][0]
        self.quotes[ident] = (bid, ask)
        for held in [h for h in self.held.values() if h.symbol_id == ident and h.stop is not None]:
            crossed = (
                bid <= cast(Decimal, held.stop)
                if held.side == "BUY"
                else ask >= cast(Decimal, held.stop)
            )
            if crossed:
                del self.held[held.position_id]
                self._execution(
                    "ORDER_FILLED",
                    held,
                    "POSITION_STATUS_CLOSED",
                    cast(Decimal, held.stop),
                    "STOP_LOSS_TAKE_PROFIT",
                    "",
                    closing=True,
                )
        self._say(
            "ProtoOASpotEvent",
            {
                "ctidTraderAccountId": CTID,
                "symbolId": ident,
                "bid": int(bid.scaleb(5)),
                "ask": int(ask.scaleb(5)),
                "timestamp": at_ms,
            },
        )

    def _position(self, held: Held, status: str) -> dict[str, object]:
        position: dict[str, object] = {
            "positionId": held.position_id,
            "tradeData": {
                "symbolId": held.symbol_id,
                "volume": held.volume,
                "tradeSide": held.side,
                "label": held.label,
            },
            "positionStatus": status,
            "swap": 0,
            "price": float(held.price),
        }
        if held.stop is not None:
            position["stopLoss"] = float(held.stop)
        return position

    def _execution(
        self,
        kind: str,
        held: Held,
        status: str,
        price: Decimal,
        order_type: str,
        msg_id: str,
        *,
        closing: bool = False,
    ) -> None:
        self._next += 1
        trade = {"symbolId": held.symbol_id, "volume": held.volume, "tradeSide": held.side}
        self._say(
            "ProtoOAExecutionEvent",
            {
                "ctidTraderAccountId": CTID,
                "executionType": kind,
                "position": self._position(held, status),
                "order": {
                    "orderId": self._next,
                    "tradeData": trade,
                    "orderType": order_type,
                    "orderStatus": "ORDER_STATUS_FILLED"
                    if kind == "ORDER_FILLED"
                    else "ORDER_STATUS_ACCEPTED",
                    "clientOrderId": "" if closing else held.client_order_id,
                    "closingOrder": closing,
                    "positionId": held.position_id,
                },
                "deal": {
                    "dealId": self._next,
                    "orderId": self._next,
                    "positionId": held.position_id,
                    "volume": held.volume,
                    "filledVolume": held.volume,
                    "symbolId": held.symbol_id,
                    "createTimestamp": 1_742_500_000_000,
                    "executionTimestamp": 1_742_500_000_000,
                    "executionPrice": float(price),
                    "tradeSide": held.side,
                    "dealStatus": "FILLED",
                },
            },
            msg_id,
        )

    def requests(self) -> list[str]:
        return [name for name, _ in self.received if name != "ProtoHeartbeatEvent"]


class Memory:
    """The grant store in memory."""

    def __init__(self) -> None:
        self.held: str | None = None

    @property
    def name(self) -> str:
        return "memory"

    def read(self) -> str | None:
        return self.held

    def write(self, text: str, /) -> None:
        self.held = text

    def delete(self) -> None:
        self.held = None


@dataclass
class Bound:
    node: Node
    door: CTraderDoor
    fake: FakeCTrader
    tokens: Tokens
    grants: Memory
    now: list[int]
    data: Path


def codec() -> Codec:
    loaded = Codec.load(DEFINITIONS)
    assert not isinstance(loaded, TypedRefusal), loaded
    return loaded.value


def bound_rig(
    root: Path,
    *,
    live_account: bool = False,
    profile: bool = False,
    lifetime_s: int = 2_628_000,
    grant: str | None = None,
    broker: FakeCTrader | None = None,
    at: int = base.LIVE_FROM - base.DAY,
) -> Bound:
    """A node on ``root`` with its cTrader door over the fakes, its runtime not started. A
    restart passes the same ``broker``, which still holds what it held."""
    now = [at]
    steady = [0]
    fake = broker or FakeCTrader(codec(), live_account=live_account)
    tokens = Tokens(lifetime_s)
    memory = Memory()
    memory.held = grant
    made: list[CTraderDoor] = []

    def door(store: Store, data: Path) -> CTraderDoor:
        def clock() -> int:
            return now[0]

        def steady_ns() -> int:
            steady[0] += 1_000_000
            return steady[0]

        endpoint = TokenEndpoint(fetch=tokens)
        built = CTraderDoor(
            store=store,
            data=data,
            keys=lambda: KEYS,
            grants=Grants(memory, endpoint, lambda: profile, clock),
            endpoint=endpoint,
            open_wire=lambda _host: fake.connect(),
            codec=lambda: Ok(fake.codec),
            clock_ns=clock,
            steady_ns=steady_ns,
            image_digest=lambda: DIGEST,
        )
        made.append(built)
        return built

    node = open_node(
        root / "data",
        here="fp-pc-1",
        machine="pc",
        clock_ns=lambda: now[0],
        sleep=lambda seconds: now.__setitem__(0, now[0] + int(seconds * 1e9)),
        random_bytes=lambda size: b"\x07" * size,
        door=door,
    )
    return Bound(node, made[0], fake, tokens, memory, now, root / "data")


def value(answer: dict[str, Json]) -> dict[str, Json]:
    assert answer["ok"] is True, answer
    return cast("dict[str, Json]", answer["value"])


def signed_in(rig: Bound) -> dict[str, Json]:
    begun = value(rig.node.call("sign_in_begin", {"op_id": "begin-1", "venue": "ctrader"}))
    assert str(begun["url"]).startswith(
        "https://id.ctrader.com/my/settings/openapi/grantingaccess/?"
    )
    return value(rig.node.call("sign_in_code", {"op_id": "code-1", "code": "one-time"}))


def bind(rig: Bound) -> dict[str, Json]:
    return rig.node.call(
        "bind",
        {
            "op_id": "bind-1",
            "account": {"id": ACCOUNT, "ctid": CTID, "venue": "icmarkets-ctrader"},
            "action": "add",
        },
    )


def tick_quotes(rig: Bound, ticks: int = 3, *, bid: str = "1.08000", ask: str = "1.08012") -> None:
    for _ in range(ticks):
        rig.now[0] += 1_000_000_000
        rig.fake.quote("EURUSD", Decimal(bid), Decimal(ask), rig.now[0] // 1_000_000)
        runtime(rig).tick()


def runtime(rig: Bound) -> Runtime:
    assert rig.node.runtime is not None
    return rig.node.runtime


def play_spots(rig: Bound, start: int, until: int) -> None:
    """Play the recorded bars in ``[start, until)`` as cTrader's spots, four a bar per side
    (open, high, low, close), and tick once a bar as the next one starts."""
    live = [item for item in base.month().bars if start <= item[0] < until]
    for at, group in groupby(live, key=lambda item: item[0]):
        closed = list(group)
        for offset in range(4):
            rig.now[0] = at - 900_000_000_000 + (offset + 1) * 1_000_000
            for _, market, bar in closed:
                symbol = "EURUSD" if market == "fx.eurusd" else "XAUUSD"
                bid = (bar.bid.open, bar.bid.high, bar.bid.low, bar.bid.close)[offset]
                ask = (bar.ask.open, bar.ask.high, bar.ask.low, bar.ask.close)[offset]
                rig.fake.quote(symbol, bid, ask, rig.now[0] // 1_000_000)
            if offset == 0:
                runtime(rig).tick()


def ctrader_row(rig: Bound) -> dict[str, Json]:
    venues = cast("list[dict[str, Json]]", value(rig.node.call("status", {}))["venues"])
    return next(row for row in venues if row["venue"] == "ctrader")


def test_a_fake_sign_in_binds_a_demo_account_and_the_venue_reads_ready(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path)
    before = ctrader_row(rig)["session"]

    code = signed_in(rig)
    signed = ctrader_row(rig)["session"]
    bound = value(bind(rig))
    tick_quotes(rig)
    shown = ctrader_row(rig)

    assert before == "signed_out"
    assert code == {"accounts": [{"account": "4401", "is_live": False}], "kept": True}
    assert signed == "signed_in"
    assert bound == {"world": "demo", "state": "bound"}
    assert (shown["session"], shown["reason"], shown["accounts"]) == ("ready", "ready", [ACCOUNT])
    assert rig.fake.requests()[:4] == [
        "ProtoOAApplicationAuthReq",
        "ProtoOAGetAccountListByAccessTokenReq",
        "ProtoOAApplicationAuthReq",
        "ProtoOAAccountAuthReq",
    ]
    assert "ProtoOASubscribeSpotsReq" in rig.fake.requests()
    assert json.loads(cast(str, rig.grants.held))["accounts"] == [
        {"broker": "ICM", "ctid": 4401, "is_live": False, "login": 5501}
    ]
    runtime(rig).stop()


def test_the_self_test_lands_its_five_checks_ok_on_the_passport(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path)
    signed_in(rig)
    bind(rig)
    tick_quotes(rig)

    accepted = rig.node.call("self_test", {"op_id": "test-1", "account": ACCOUNT})
    tick_quotes(rig, 1)
    passport = value(rig.node.call("passport", {}))
    checks = cast("list[dict[str, Json]]", passport["checks"])
    trade = cast("dict[str, Json]", checks[2]["value"])
    sent = [
        (name, body.get("relativeStopLoss"), body.get("volume"))
        for name, body in rig.fake.received
        if name in {"ProtoOANewOrderReq", "ProtoOAClosePositionReq"}
    ]

    assert accepted == {"ok": True, "value": {"state": "accepted"}, "op_id": "test-1"}
    assert [(c["name"], c["ok"]) for c in checks] == [(name, True) for name in CHECKS]
    assert checks[0]["value"] == "ready"
    assert checks[4]["value"] == DIGEST
    assert (trade["entry"], trade["stop"], trade["exit"]) == ("1.08012", "1.07512", "1.08000")
    assert sent == [
        ("ProtoOANewOrderReq", "500", "100000"),
        ("ProtoOAClosePositionReq", None, "100000"),
    ]
    assert rig.fake.held == {}
    assert cast("list[dict[str, Json]]", passport["grants"])[0]["venue"] == "ctrader"
    rows = [
        cast("dict[str, Json]", row["body"])
        for row in cast(
            "list[dict[str, Json]]",
            value(rig.node.call("journal_tail", {"streams": ["node"]}))["rows"],
        )
        if row["kind"] == "order"
    ]
    assert [row["step"] for row in rows] == ["send", "filled", "close", "closed"]
    runtime(rig).stop()


def test_a_retried_self_test_trades_once_and_a_reused_op_id_trades_nothing(
    tmp_path: Path,
) -> None:
    rig = bound_rig(tmp_path)
    signed_in(rig)
    bind(rig)
    tick_quotes(rig)

    first = rig.node.call("self_test", {"op_id": "test-1", "account": ACCOUNT})
    tick_quotes(rig, 1)
    retried = rig.node.call("self_test", {"op_id": "test-1", "account": ACCOUNT})
    tick_quotes(rig, 1)
    after_retry = rig.fake.requests().count("ProtoOANewOrderReq")
    rotated = rig.node.call("rotate_keys", {"op_id": "shared-1"})
    reused = rig.node.call("self_test", {"op_id": "shared-1", "account": ACCOUNT})
    tick_quotes(rig, 1)

    assert first == retried == {"ok": True, "value": {"state": "accepted"}, "op_id": "test-1"}
    assert after_retry == 1
    assert rotated["ok"] is True
    assert (reused["ok"], reused["code"]) == (False, "op_id_reused")
    assert rig.fake.requests().count("ProtoOANewOrderReq") == 1
    runtime(rig).stop()


BAR = 900_000_000_000


def deploy_dummy(rig: Bound) -> Runtime:
    """The dummy deployed on the bound account with its recorded history, compiled."""
    runtime = rig.node.runtime
    assert runtime is not None
    feed = runtime.venues[ACCOUNT].feed
    for at, market, bar in base.month().bars:
        if at < base.LIVE_FROM:
            feed.recording.keep(market, bar)
    tick_quotes(rig)
    deployed = rig.node.call(
        "deploy", {"op_id": "op-deploy-1", "deployment": base.deployment(rig.data)}
    )
    assert value(deployed)["state"] == "accepted"
    compiled(runtime)
    return runtime


def compiled(runtime: Runtime) -> None:
    deadline = 600
    while runtime.hosted.get("dep-1") is None or runtime.hosted["dep-1"].phase is Phase.COMPILING:
        runtime.tick()
        deadline -= 1
        assert deadline, "the compile did not finish"
        time.sleep(0.05)


def play_until_sent(rig: Bound) -> int:
    """Play the recorded days bar by bar until the node sends its first entry; the next bar."""
    at = base.LIVE_FROM
    while "ProtoOANewOrderReq" not in rig.fake.requests():
        assert at < base.LIVE_FROM + 2 * base.DAY, "the dummy sent no entry"
        play_spots(rig, at, at + BAR)
        at += BAR
    return at


def node_rows(rig: Bound, kind: str) -> list[dict[str, Json]]:
    rows = cast(
        "list[dict[str, Json]]",
        value(rig.node.call("journal_tail", {"streams": ["node"]}))["rows"],
    )
    return [cast("dict[str, Json]", row["body"]) for row in rows if row["kind"] == kind]


def sent_entries(rig: Bound) -> list[str]:
    return [str(body["clientOrderId"]) for n, body in rig.fake.received if n == "ProtoOANewOrderReq"]


def closes(rig: Bound) -> list[dict[str, object]]:
    return [body for name, body in rig.fake.received if name == "ProtoOAClosePositionReq"]


FIRST_ENTRY_ROW: dict[str, Json] = {
    "claim": "mine",
    "tags": ["a4dqobyh"],
    "market_id": "fx.eurusd",
    "side": "short",
    "quantity": "0.04",
}


def test_an_entry_whose_answer_is_lost_is_the_node_own_booked_taken_and_killed_flat(
    tmp_path: Path,
) -> None:
    rig = bound_rig(tmp_path)
    signed_in(rig)
    bind(rig)
    rig.fake.lose_answers = 1
    deploy_dummy(rig)
    at = play_until_sent(rig)
    name = sent_entries(rig)[0]

    play_spots(rig, at, at + BAR)
    killed = rig.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    play_spots(rig, at + BAR, at + 2 * BAR)
    reconciled = node_rows(rig, "reconcile")
    venue = cast(CTraderVenue, runtime(rig).venues[ACCOUNT].client)

    assert [str(r["step"]) for r in node_rows(rig, "order") if r["client_order_id"] == name][
        :2
    ] == ["send", "unknown"]
    assert [(r["why"], r["resolved"]) for r in reconciled][:2] == [
        ("start", []),
        ("unknown", [{"client_order_id": name, "outcome": "filled", "price": "PRICE"}]),
    ]
    assert cast("list[dict[str, Json]]", reconciled[1]["positions"]) == [
        {**FIRST_ENTRY_ROW, "position": name}
    ]
    assert value(killed) == {"level_in_force": "RED"}
    assert closes(rig) == [
        {"ctidTraderAccountId": "4401", "positionId": "9001", "volume": "400000"}
    ]
    assert sent_entries(rig) == [name]
    assert rig.fake.held == {}
    assert venue.held() == {}
    runtime(rig).stop()


def test_after_a_restart_the_node_reads_its_open_position_as_its_own_and_kills_it_flat(
    tmp_path: Path,
) -> None:
    rig = bound_rig(tmp_path)
    signed_in(rig)
    bind(rig)
    rig.fake.lose_answers = 1
    deploy_dummy(rig)
    at = play_until_sent(rig)
    name = sent_entries(rig)[0]
    rig.node.stop()

    again = bound_rig(tmp_path, grant=rig.grants.held, broker=rig.fake, at=rig.now[0])
    compiled(runtime(again))
    play_spots(again, at, at + BAR)
    killed = again.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    play_spots(again, at + BAR, at + 2 * BAR)
    reconciled = node_rows(again, "reconcile")

    assert [(r["why"], r["resolved"]) for r in reconciled][-1:] == [("start", [])]
    assert cast("list[dict[str, Json]]", reconciled[-1]["positions"]) == [
        {**FIRST_ENTRY_ROW, "position": name}
    ]
    assert value(killed) == {"level_in_force": "RED"}
    assert closes(again) == [
        {"ctidTraderAccountId": "4401", "positionId": "9001", "volume": "400000"}
    ]
    assert sent_entries(again) == [name]
    assert again.fake.held == {}
    runtime(again).stop()


def test_an_entry_answered_after_its_wait_is_the_node_own_and_closes(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path)
    signed_in(rig)
    bind(rig)
    tick_quotes(rig)
    venue = cast(CTraderVenue, runtime(rig).venues[ACCOUNT].client)
    symbol = venue.symbols["fx.eurusd"]
    gap = PriceDelta.try_create(500, symbol.instrument, symbol.digits)
    size = Quantity.try_create(1, "lot", 2)
    tags = order_tags("e" * 36, "qmx:a4dqobyh:probe")
    assert not isinstance(gap, TypedRefusal) and not isinstance(size, TypedRefusal)
    assert not isinstance(tags, TypedRefusal)
    params = OrderParameters.try_create(
        OrderType.MARKET,
        TimeInForce.IMMEDIATE_OR_CANCEL,
        size.value,
        protective_stop_distance=gap.value,
        instrument=symbol.instrument,
        trade_side="buy",
    )
    assert not isinstance(params, TypedRefusal)
    entry = Command.place_order(venue.account.venue, venue.account, "session-1", 1, params.value)
    close = Command.close_position(
        venue.account.venue,
        venue.account,
        "session-1",
        2,
        CloseScope.INSTRUMENT_WITHIN_BINDING,
        "e" * 36,
    )
    assert not isinstance(entry, TypedRefusal) and not isinstance(close, TypedRefusal)
    lots = Decimal("0.01")
    api = venue.api
    assert api is not None

    api.wait_s = 0.0
    entered = venue.send(
        Ticket(entry.value, "fx.eurusd", Side.LONG, Decimal("1.08012"), lots, lots, tags.value)
    )
    api.wait_s = 5.0
    read = venue.read_back()
    assert not isinstance(read, TypedRefusal)
    claimed = attribute(read.value, tag="a4dqobyh", sent=["e" * 36])
    closed = venue.send(
        Ticket(close.value, "fx.eurusd", Side.LONG, Decimal(0), position="e" * 36)
    )

    assert not isinstance(entered, TypedRefusal) and not isinstance(closed, TypedRefusal)
    assert entered.value.outcome is SubmissionOutcome.UNKNOWN
    assert read.value.orders == (
        VenueOrder(
            "e" * 36,
            "qmx:a4dqobyh:probe",
            "fx.eurusd",
            OrderState.FILLED,
            "e" * 36,
            Decimal("1.08012"),
        ),
    )
    assert read.value.positions == (
        VenuePosition(
            "e" * 36,
            "qmx:a4dqobyh:probe",
            "fx.eurusd",
            "long",
            Decimal("0.01"),
            Decimal("1.08012"),
            Decimal("1.07512"),
        ),
    )
    assert [attributed.claim for _, attributed in claimed.positions] == [Claim.MINE]
    assert (closed.value.outcome, closed.value.price) == (
        SubmissionOutcome.ACCEPTED_BY_VENUE,
        Decimal("1.08000"),
    )
    assert rig.fake.held == {}
    runtime(rig).stop()


def test_the_dummy_trades_through_the_ctrader_binding_with_its_stop_at_the_venue(
    tmp_path: Path,
) -> None:
    rig = bound_rig(tmp_path)
    signed_in(rig)
    bind(rig)
    runtime = deploy_dummy(rig)
    play_spots(rig, base.LIVE_FROM, base.LIVE_FROM + 2 * base.DAY)
    venue = cast(CTraderVenue, runtime.venues[ACCOUNT].client)
    orders = [body for name, body in rig.fake.received if name == "ProtoOANewOrderReq"]
    trades = [
        cast("dict[str, Json]", row["body"])
        for row in cast(
            "list[dict[str, Json]]",
            value(rig.node.call("journal_tail", {"streams": ["unit"]}))["rows"],
        )
        if row["kind"] == "trade"
    ]

    assert [(o["tradeSide"], o["volume"], o["relativeStopLoss"]) for o in orders] == [
        ("SELL", "400000", "1164"),
        ("SELL", "17200000", "29"),
    ]
    assert {str(o["label"]) for o in orders} == {"qmx:a4dqobyh:dummy-trend-pullback"}
    assert [len(str(o["clientOrderId"])) for o in orders] == [36, 36]
    assert [(t["exit_kind"], t["quantity"]) for t in trades] == [
        ("close", "0.04"),
        ("target", "1.72"),
    ]
    assert [t["trade_id"] for t in trades] == [o["clientOrderId"] for o in orders]
    assert closes(rig) == [
        {"ctidTraderAccountId": "4401", "positionId": "9001", "volume": "400000"},
        {"ctidTraderAccountId": "4401", "positionId": "9005", "volume": "17200000"},
    ]
    assert runtime.alarms == []
    assert venue.held() == {}
    runtime.stop()


def test_an_entry_without_the_node_tags_is_refused_before_anything_is_sent(
    tmp_path: Path,
) -> None:
    rig = bound_rig(tmp_path)
    signed_in(rig)
    bind(rig)
    tick_quotes(rig)
    venue = cast(CTraderVenue, runtime(rig).venues[ACCOUNT].client)
    symbol = venue.symbols["fx.eurusd"]
    gap = PriceDelta.try_create(500, symbol.instrument, symbol.digits)
    size = Quantity.try_create(1, "lot", 2)
    assert not isinstance(gap, TypedRefusal) and not isinstance(size, TypedRefusal)
    params = OrderParameters.try_create(
        OrderType.MARKET,
        TimeInForce.IMMEDIATE_OR_CANCEL,
        size.value,
        protective_stop_distance=gap.value,
        instrument=symbol.instrument,
        trade_side="buy",
    )
    assert not isinstance(params, TypedRefusal)
    command = Command.place_order(venue.account.venue, venue.account, "session-1", 1, params.value)
    assert not isinstance(command, TypedRefusal)
    before = rig.fake.requests().count("ProtoOANewOrderReq")

    sent = venue.send(
        Ticket(command.value, "fx.eurusd", Side.LONG, Decimal("1.08012"), Decimal("0.01"))
    )

    assert not isinstance(sent, TypedRefusal)
    assert (sent.value.outcome, sent.value.code) == (
        SubmissionOutcome.REJECTED_BY_VENUE,
        "not-a-node-entry",
    )
    assert rig.fake.requests().count("ProtoOANewOrderReq") == before == 0
    runtime(rig).stop()


def test_a_grant_that_can_trade_live_money_is_discarded_and_binds_nothing(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path, live_account=True)

    code = signed_in(rig)
    refused = bind(rig)

    assert code == {
        "accounts": [{"account": "4401", "is_live": False}, {"account": "4402", "is_live": True}],
        "kept": False,
        "reason": server.LIVE_GRANT_MESSAGE,
    }
    assert rig.grants.held is None
    assert (refused["ok"], refused["code"]) == (False, "not_signed_in")
    assert ACCOUNT not in runtime(rig).venues


def test_an_expired_grant_reads_expired_and_the_self_test_cannot_trade(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path, lifetime_s=60)
    signed_in(rig)
    rig.tokens.refuse_refresh = True
    rig.now[0] += 120_000_000_000

    session = ctrader_row(rig)["session"]
    bound = bind(rig)
    tick_quotes(rig)

    assert session == "expired"
    assert value(bound) == {"world": "demo", "state": "bound"}
    assert ctrader_row(rig)["session"] == "expired"
    assert "ProtoOAAccountAuthReq" not in rig.fake.requests()


def test_a_bound_session_refreshes_its_grant_and_authorises_again_with_the_new_pair(
    tmp_path: Path,
) -> None:
    rig = bound_rig(tmp_path, lifetime_s=4 * 86_400)
    signed_in(rig)
    bind(rig)
    tick_quotes(rig)
    rig.fake.tokens.add("fake-a2")
    rig.now[0] += 2 * 86_400_000_000_000

    tick_quotes(rig, 1)
    auths = [
        body.get("accessToken")
        for name, body in rig.fake.received
        if name == "ProtoOAAccountAuthReq"
    ]

    assert rig.tokens.asked == ["GET", "POST"]
    assert json.loads(cast(str, rig.grants.held))["access_token"] == "fake-a2"
    assert auths == ["fake-a1", "fake-a2"]
    assert ctrader_row(rig)["session"] == "ready"
    runtime(rig).stop()


def test_a_restart_binds_again_the_account_he_bound(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path)
    signed_in(rig)
    bind(rig)
    runtime(rig).stop()
    held = rig.grants.held

    again = bound_rig(tmp_path, grant=held)
    tick_quotes(again)

    assert sorted(runtime(again).venues) == [ACCOUNT]
    assert (
        runtime(again).venues[ACCOUNT].client.account == runtime(rig).venues[ACCOUNT].client.account
    )
    assert ctrader_row(again)["session"] == "ready"
    runtime(again).stop()


class NoCredentialManager:
    """Stands in for Credential Manager in the environment tests: making one fails the test, so
    no test can reach a real entry."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise AssertionError("a test reached for Credential Manager")


@pytest.fixture
def environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setattr(grants_module, "CredentialManager", NoCredentialManager)

    def memory(data: Path, tag: str) -> Memory:
        del data, tag
        return Memory()

    monkeypatch.setattr(server, "grant_store_for", memory)
    volume = tmp_path / "volume"
    (volume / "data").mkdir(parents=True)
    (volume / "road" / "host").mkdir(parents=True)
    (volume / "road" / "host" / "facts.json").write_text(
        json.dumps({"placement": "pc", "trading_profile": False}), "utf-8"
    )
    saved = {
        name: os.environ.get(name)
        for name in ("QMX_DATA_DIR", "QMX_VOLUME", "QMX_STAGE", "NODE_KEYS")
    }
    os.environ.update(
        {"QMX_DATA_DIR": str(volume / "data"), "QMX_VOLUME": str(volume), "NODE_KEYS": KEYS}
    )
    yield volume
    for name, held in saved.items():
        if held is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = held


def test_under_the_shadow_stage_the_node_reads_no_grant_and_binds_nothing(
    environment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    read: list[str] = []

    def no_store(data: Path, tag: str) -> Memory:
        read.append(tag)
        return Memory()

    monkeypatch.setattr(server, "grant_store_for", no_store)
    os.environ["QMX_STAGE"] = "shadow"
    node = server.from_environment()
    try:
        answers = [
            node.call("sign_in_begin", {"op_id": "s", "venue": "ctrader"}),
            node.call(
                "bind",
                {
                    "op_id": "b",
                    "account": {"id": ACCOUNT, "ctid": CTID, "venue": "icmarkets-ctrader"},
                    "action": "add",
                },
            ),
            node.call("self_test", {"op_id": "t", "account": ACCOUNT}),
        ]
        sessions = [
            row["session"]
            for row in cast("list[dict[str, Json]]", value(node.call("status", {}))["venues"])
        ]
        venues = dict(node.runtime.venues) if node.runtime is not None else None
    finally:
        node.stop()

    assert [(a["ok"], a["code"]) for a in answers] == [(False, "not_set_up")] * 3
    assert sessions == ["not_set_up", "not_set_up"]
    assert venues == {}
    assert read == []


def test_at_the_live_stage_the_node_opens_its_door_with_its_own_grant_store(
    environment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    read: list[str] = []

    def memory_store(data: Path, tag: str) -> Memory:
        read.append(tag)
        return Memory()

    monkeypatch.setattr(server, "grant_store_for", memory_store)
    os.environ["QMX_STAGE"] = "live"
    node = server.from_environment()
    try:
        begun = node.call(
            "sign_in_begin",
            {
                "op_id": "s",
                "venue": "ctrader",
                "redirect": "http://127.0.0.1:47613/ctrader/callback",
            },
        )
        refused = node.call(
            "bind",
            {
                "op_id": "b",
                "account": {"id": ACCOUNT, "ctid": CTID, "venue": "icmarkets-ctrader"},
                "action": "add",
            },
        )
        session = ctrader_session(node)
    finally:
        node.stop()

    assert str(value(begun)["url"]) == (
        "https://id.ctrader.com/my/settings/openapi/grantingaccess/?client_id=app-77"
        "&redirect_uri=http%3A%2F%2F127.0.0.1%3A47613%2Fctrader%2Fcallback&scope=trading&product=web"
    )
    assert (refused["ok"], refused["code"]) == (False, "not_signed_in")
    assert session == "signed_out"
    assert len(read) == 1 and len(read[0]) == 8


def ctrader_session(node: Node) -> Json:
    venues = cast("list[dict[str, Json]]", value(node.call("status", {}))["venues"])
    return next(row["session"] for row in venues if row["venue"] == "ctrader")
