"""The ccxt client through the pinned CCXT class with no network (C-16 lanes 2, 3, 4 and 6).

Runs in the qmx-agents environment, the one that locks CCXT 4.5.85::

    cd qmx-agents
    uv run --no-sync python ../qmn/probes/hyperliquid_testnet/offline.py

The real ``ccxt.hyperliquid`` class builds and signs every request. Only its HTTP call is
replaced by a stand-in testnet that answers in Hyperliquid's own shapes, so nothing leaves this
machine. The signer is a hash made here, never a wallet. Each check prints one PASS or FAIL line,
and the script exits 1 on any FAIL. The last line is the lane 2 metric, milliseconds per mapped
call, which has no fail rule.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import importlib
import io
import json
import statistics
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from qmf.core import Account, AccountRole, TypedRefusal, VenueId
from qmf.data.journal_envelope import JournalStream, JournalWorld
from qmf.data.journal_writer import JournalWriter, WriterScope
from qml.numbers import InstrumentRecord, lots, parse_record
from qml.unit.model import Side
from qmn.app.attribution import Claim, attribute
from qmn.app.feed_keeper import FeedKeeper, Quote, RecordedSource, Recording
from qmn.app.runtime import OrderPath, Placed, Unknown, Venue, ulid
from qmn.venue.ccxt_client import (
    ERRORS,
    AgentKey,
    AgentWallet,
    CcxtClient,
    Exchange,
    api_urls,
    cloid,
    cloid_tag,
    make_testnet_exchange,
)

TESTNET = "https://api.hyperliquid-testnet.xyz"
TESTNET_WS = "wss://api.hyperliquid-testnet.xyz/ws"
TAG = "a4dqobyh"
DEPLOYMENT = "dep-1"
ETH = "ETH/USDC:USDC"
ACCOUNT_ADDRESS = "0x" + "ab" * 20
SUBACCOUNT = "0x" + "cd" * 20
SIGNER = "0x" + hashlib.sha256(b"c16 offline signer, never a wallet").hexdigest()
VENUE = VenueId("hyperliquid-testnet")
ACCOUNT = Account("hl-testnet-1", VENUE, AccountRole.DEMO)
ACCOUNT_READS = frozenset(
    {"frontendOpenOrders", "historicalOrders", "userFills", "clearinghouseState"}
)
MARGIN_FIXTURE = 900
"""The fixture account's stated open-order margin (lane 6)."""


@dataclass
class Testnet:
    """Hyperliquid's testnet as its info and exchange endpoints answer, in memory."""

    urls: list[str] = field(default_factory=list[str])
    actions: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    infos: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    next_answer: list[Any] = field(default_factory=list[Any])
    open_orders: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    history: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    fills: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    position: str = "0"
    oid: int = 100

    def answer(self, url: str, body: dict[str, Any]) -> Any:
        self.urls.append(url)
        if url.endswith("/info"):
            self.infos.append(body)
            return self.info(body)
        self.actions.append(body)
        if self.next_answer:
            queued = self.next_answer.pop(0)
            if isinstance(queued, Exception):
                raise queued
            return queued
        action = body["action"]
        if action["type"] == "cancelByCloid":
            self.open_orders = [
                o for o in self.open_orders if o["cloid"] != action["cancels"][0]["cloid"]
            ]
            return {
                "status": "ok",
                "response": {"type": "cancel", "data": {"statuses": ["success"]}},
            }
        if action["type"] == "cancel":
            gone = {c["o"] for c in action["cancels"]}
            self.open_orders = [o for o in self.open_orders if o["oid"] not in gone]
            return {
                "status": "ok",
                "response": {"type": "cancel", "data": {"statuses": ["success"]}},
            }
        order = action["orders"][0]
        self.oid += 1
        if order["t"].get("limit", {}).get("tif") == "Gtc" and Decimal(order["p"]) < 2500:
            self.open_orders.append(
                {"coin": "ETH", "side": "B", "limitPx": order["p"], "sz": order["s"],
                 "oid": self.oid, "timestamp": 1_762_000_000_000, "isTrigger": False,
                 "reduceOnly": False, "orderType": "Limit", "origSz": order["s"], "tif": "Gtc",
                 "cloid": order.get("c")}
            )  # fmt: skip
            resting = {"resting": {"oid": self.oid, "cloid": order.get("c")}}
            return {"status": "ok", "response": {"type": "order", "data": {"statuses": [resting]}}}
        if "trigger" in order["t"]:
            self.open_orders.append(
                {
                    "coin": "ETH",
                    "side": "B" if order["b"] else "A",
                    "limitPx": order["p"],
                    "sz": "0.0",
                    "oid": self.oid,
                    "timestamp": 1_762_000_000_000,
                    "isTrigger": True,
                    "triggerPx": order["t"]["trigger"]["triggerPx"],
                    "isPositionTpsl": action["grouping"] == "positionTpsl",
                    "reduceOnly": order["r"],
                    "orderType": "Stop Market",
                    "origSz": "0.0",
                    "tif": None,
                    "cloid": order.get("c"),
                }
            )
            return {
                "status": "ok",
                "response": {"type": "order", "data": {"statuses": ["waitingForTrigger"]}},
            }
        size = Decimal(order["s"])
        signed = size if order["b"] else -size
        self.position = str(Decimal(self.position) + signed)
        self.fills.append(
            {
                "coin": "ETH",
                "px": "2501.0",
                "sz": order["s"],
                "side": "B" if order["b"] else "A",
                "time": 1_762_000_000_000 + self.oid,
                "oid": self.oid,
                "tid": self.oid,
                "fee": "0.01",
                "feeToken": "USDC",
                "crossed": True,
            }
        )
        self.history.append(
            {
                "order": {
                    "coin": "ETH",
                    "side": "B" if order["b"] else "A",
                    "limitPx": order["p"],
                    "sz": "0.0",
                    "oid": self.oid,
                    "timestamp": 1_762_000_000_000 + self.oid,
                    "isTrigger": False,
                    "reduceOnly": order["r"],
                    "orderType": "Limit",
                    "origSz": order["s"],
                    "tif": "Ioc",
                    "cloid": order.get("c"),
                },
                "status": "filled",
                "statusTimestamp": 1_762_000_000_000 + self.oid,
            }
        )
        filled = {"totalSz": order["s"], "avgPx": "2501.0", "oid": self.oid}
        return {
            "status": "ok",
            "response": {"type": "order", "data": {"statuses": [{"filled": filled}]}},
        }

    def info(self, body: dict[str, Any]) -> Any:
        kind = body["type"]
        if kind == "metaAndAssetCtxs":
            return [
                {"universe": [{"name": "ETH", "szDecimals": 4, "maxLeverage": 25}]},
                [{"markPx": "2500.0", "midPx": "2500.0", "oraclePx": "2500.0", "funding": "0.0",
                  "openInterest": "1.0", "dayNtlVlm": "1.0", "prevDayPx": "2500.0"}],
            ]  # fmt: skip
        if kind == "l2Book":
            levels = [
                [{"px": "2499.5", "sz": "10.0", "n": 1}],
                [{"px": "2500.5", "sz": "10.0", "n": 1}],
            ]
            return {"coin": "ETH", "levels": levels, "time": 1_762_000_000_000}
        if kind == "userAbstraction":
            return "default"
        if kind == "spotMeta":
            return {"universe": [], "tokens": []}
        if kind == "frontendOpenOrders":
            return self.open_orders
        if kind == "historicalOrders":
            return self.history
        if kind == "userFills":
            return self.fills
        if kind == "clearinghouseState":
            held = [] if Decimal(self.position) == 0 else [
                {"position": {"coin": "ETH", "szi": self.position, "entryPx": "2501.0",
                              "leverage": {"type": "cross", "value": "10"},
                              "marginUsed": "1.0", "unrealizedPnl": "0.0",
                              "positionValue": "11.0"}, "type": "oneWay"}
            ]  # fmt: skip
            return {"assetPositions": held, "marginSummary": {"accountValue": "1000.25"},
                    "withdrawable": "1000.25", "time": "1762000000000"}  # fmt: skip
        return None


def _record() -> InstrumentRecord:
    parsed = parse_record(
        {
            "venue": "hyperliquid-testnet", "symbol": "ETH", "market_id": "crypto.eth",
            "class": "perp", "currency": "USDC", "digits": 1, "tick_size": "0.1",
            "pip": {"size": "0.1", "source": "offline proof"}, "contract_size": "1",
            "value_per_point": "1", "lot_step": "0.0001", "min_lot": "0.0001", "max_lot": "1000",
            "calendar_ref": "crypto-24x7@1", "zone": "UTC", "day_boundary": "00:00",
            "data_levels": {"levels": [0, 1, 2], "volume": "tick_count"},
            "leverage": {"version": 1, "tiers": [{"up_to_lots": "1000", "leverage": "10"}]},
            "margin": {"intraday": "0.1", "overnight": "0.1"}, "record_version": 1,
            "status": "specified",
        }
    )  # fmt: skip
    if isinstance(parsed, TypedRefusal):
        raise SystemExit(f"FAIL setup: the test record is refused: {parsed.context}")
    return parsed.value


RECORD = _record()


@dataclass
class Rig:
    venue: Testnet
    exchange: Any
    client: CcxtClient
    path: OrderPath
    alarms: list[Mapping[str, object]]


def stand_in(wallet: AgentWallet, venue: Testnet) -> Any:
    """A real ``ccxt.hyperliquid`` on testnet whose HTTP call ``venue`` answers."""
    ccxt = importlib.import_module("ccxt")
    made = make_testnet_exchange(ccxt.hyperliquid, wallet)
    if isinstance(made, TypedRefusal):
        raise SystemExit(f"FAIL setup: the testnet exchange is refused: {dict(made.context)}")
    exchange = made.value
    exchange.options["fetchMarkets"] = {"types": ["swap"]}

    def fetch(url: str, method: str = "GET", headers: Any = None, body: Any = None) -> Any:
        del headers
        sent_body = cast("dict[str, Any]", json.loads(body) if body else {})
        answered = venue.answer(url, sent_body)
        text = json.dumps(answered)
        exchange.handle_errors(200, "OK", url, method, {}, text, answered, {}, body)
        return answered

    exchange.fetch = fetch
    return exchange


def rig(folder: Path, subaccount: str | None = None, sent: tuple[str, ...] = ()) -> Rig:
    ccxt = importlib.import_module("ccxt")
    wallet = AgentWallet(ACCOUNT_ADDRESS, AgentKey(SIGNER), 1_809_000_000_000, subaccount)
    venue = Testnet()
    exchange = stand_in(wallet, venue)
    now = [1_762_000_000_000_000_000]
    alarms: list[Mapping[str, object]] = []
    opened = CcxtClient.open(
        cast("Exchange", exchange),
        account=ACCOUNT,
        wallet=wallet,
        markets={"crypto.eth": ETH},
        ccxt_version=str(ccxt.__version__),
        clock_ns=lambda: now[0],
        on_alarm=alarms.append,
        sent=lambda: sent,
    )
    if isinstance(opened, TypedRefusal):
        raise SystemExit(f"FAIL setup: the client refused to open: {dict(opened.context)}")
    source = RecordedSource([])
    feed = FeedKeeper(
        "hyperliquid", "testnet", source, ("crypto.eth",), lambda: now[0], Recording(None)
    )
    source.play([Quote("crypto.eth", now[0], Decimal("2499.5"), Decimal("2500.5"), "both")])
    feed.pump()
    scope = WriterScope(JournalStream.NODE, TAG, JournalWorld.DEMO, "pc", "node", "0.1.0")
    journal = JournalWriter.open(folder, scope, clock=lambda: now[0], boot_epoch_id="b1")
    if isinstance(journal, TypedRefusal):
        raise SystemExit("FAIL setup: the journal refused to open")

    def sleep(seconds: float) -> None:
        now[0] += int(seconds * 1e9)

    path = OrderPath(
        TAG, Venue(opened.value, feed), journal.value, lambda: now[0], sleep, alarms.append
    )
    return Rig(venue, exchange, opened.value, path, alarms)


def name(seed: str) -> str:
    return f"q{TAG}-{ulid(1_762_000_000_000, seed)}"


def enter(node: Rig, order_name: str) -> object:
    quantity = lots(Decimal("0.0044"), RECORD)
    if isinstance(quantity, TypedRefusal):
        raise SystemExit("FAIL setup: the quantity is refused")
    return node.path.entry(
        deployment_id=DEPLOYMENT,
        client_order_id=order_name,
        label=f"qmx:{TAG}:dummy-trend-pullback",
        wire={
            "order": {"type": "market"},
            "direction": "long",
            "market_id": "crypto.eth",
            "protection": {"stop": "2475.5"},
            "quantity": "0.0044",
            "decision_row_id": order_name,
        },
        record=RECORD,
        quantity=quantity.value,
        blocked_by=None,
    )


Check = tuple[str, bool, str]


def lane_mapping(folder: Path) -> list[Check]:
    node = rig(folder / "mapping")
    first = name("mapping")
    placed = enter(node, first)
    entry, stop = node.venue.actions[0]["action"], node.venue.actions[1]["action"]
    node.path.amend(
        first, "crypto.eth", Side.LONG, Decimal("2480"), Decimal("2501.0"), Decimal("2476.0"),
        RECORD,
    )  # fmt: skip
    closed = node.path.close(first, "crypto.eth", Side.LONG, Decimal("2490"), "unit")
    kinds = [a["action"]["type"] for a in node.venue.actions]
    close = node.venue.actions[4]["action"]["orders"][0]
    read = node.client.read_back()
    return [
        ("every request goes to Hyperliquid's testnet", all(u.startswith(TESTNET) for u in
         node.venue.urls), f"{len(node.venue.urls)} requests"),
        ("the entry fills and the node books its price", placed == Placed(Decimal("2501.0")),
         repr(placed)),
        ("the entry is one IOC order of 0.0044 with its cloid",
         entry["grouping"] == "na" and entry["orders"][0]["t"] == {"limit": {"tif": "Ioc"}}
         and entry["orders"][0]["s"] == "0.0044" and entry["orders"][0]["c"] == cloid(first),
         json.dumps(entry["orders"][0])),
        ("the stop is a reduce-only market trigger of size 0 over the position",
         stop["grouping"] == "positionTpsl" and stop["orders"][0]["s"] == "0"
         and stop["orders"][0]["r"] is True
         and stop["orders"][0]["t"] == {"trigger": {"isMarket": True, "triggerPx": "2476",
                                                    "tpsl": "sl"}},
         json.dumps(stop["orders"][0])),
        ("the order path sends order, order, order, cancel, order, cancel",
         kinds == ["order", "order", "order", "cancelByCloid", "order", "cancelByCloid"],
         ", ".join(kinds)),
        ("the close is reduce-only IOC and closes the position", close["r"] is True
         and close["t"] == {"limit": {"tif": "Ioc"}} and closed == Placed(Decimal("2501.0"))
         and Decimal(node.venue.position) == 0, json.dumps(close)),
        ("no builder fee and no referrer are ever sent",
         not any("builder" in a["action"] or a["action"]["type"] in {"approveBuilderFee",
                 "setReferrer"} for a in node.venue.actions), ", ".join(kinds)),
        ("reconcile reads the filled entry back by its cloid",
         not isinstance(read, TypedRefusal)
         and [(o.client_order_id, o.state.value) for o in read.value.orders][:1]
         == [(first, "filled")], repr(read)[:200]),
    ]  # fmt: skip


def lane_unknown(folder: Path) -> list[Check]:
    ccxt = importlib.import_module("ccxt")
    errors = importlib.import_module("ccxt.base.errors")
    defined = {
        name
        for name, value in vars(errors).items()
        if isinstance(value, type)
        and issubclass(value, Exception)
        and value.__module__ == errors.__name__
    }
    unmapped = rig(folder / "unmapped")
    unmapped.venue.next_answer.append(LookupError("an error no CCXT class names"))
    first = name("unmapped")
    lost = enter(unmapped, first)
    again = enter(unmapped, name("unmapped-2"))
    unread = rig(folder / "unread")
    unread.venue.next_answer.append(
        {"status": "ok", "response": {"type": "order", "data": {"statuses": [
            {"error": "Words this CCXT has never seen."}]}}}
    )  # fmt: skip
    unread_answer = enter(unread, name("unread"))
    timeout = rig(folder / "timeout")
    timeout.venue.next_answer.append(ccxt.RequestTimeout("slow testnet"))
    timed = enter(timeout, name("timeout"))
    margin = rig(folder / "funds")
    margin.venue.next_answer.append(
        {"status": "ok", "response": {"type": "order", "data": {"statuses": [
            {"error": "Insufficient margin to place order. asset=0"}]}}}
    )  # fmt: skip
    refused = enter(margin, name("funds"))
    return [
        ("the table reads every error class this CCXT defines, and no other",
         set(ERRORS) == defined, f"missing {sorted(defined - set(ERRORS))}, extra "
         f"{sorted(set(ERRORS) - defined)}"),
        ("an unmapped error reads UNKNOWN", lost == Unknown("venue answer unknown for this order",
         first), repr(lost)),
        ("the stream goes UNKNOWN: no entry on the market until it resolves",
         unmapped.path.unknown == {first: "crypto.eth"} and len(unmapped.venue.actions) == 1,
         repr(again)),
        ("the unmapped error raises the alarm",
         [a["alarm"] for a in unmapped.alarms] == ["venue_error_unmapped"],
         json.dumps([dict(a) for a in unmapped.alarms])),
        ("a venue message CCXT does not know reads UNKNOWN with the alarm",
         isinstance(unread_answer, Unknown)
         and [a["error"] for a in unread.alarms] == ["ExchangeError"],
         json.dumps([dict(a) for a in unread.alarms])),
        ("a timeout reads UNKNOWN and is not sent again",
         isinstance(timed, Unknown) and len(timeout.venue.actions) == 1, repr(timed)),
        ("Hyperliquid's margin refusal reads rejected", repr(refused).endswith(
         "(insufficient-funds)')") and margin.path.unknown == {}, repr(refused)),
    ]  # fmt: skip


def lane_cloid(folder: Path) -> list[Check]:
    node = rig(folder / "cloid", subaccount=SUBACCOUNT)
    first = name("cloid")
    enter(node, first)
    node.path.amend(
        first, "crypto.eth", Side.LONG, Decimal("2480"), Decimal("2501.0"), Decimal("2476.0"),
        RECORD,
    )  # fmt: skip
    node.path.close(first, "crypto.eth", Side.LONG, Decimal("2490"), "unit")
    tags: list[str | None] = []
    for sent in node.venue.actions:
        action = sent["action"]
        carried = action["orders"] if action["type"] == "order" else action["cancels"]
        tags += [cloid_tag(o.get("c") or o.get("cloid")) for o in carried]
    groupings = [a["action"].get("grouping") for a in node.venue.actions]
    return [
        ("every order and cancel carries the node's cloid", tags == [TAG] * len(tags)
         and len(tags) == 6, ", ".join(str(t) for t in tags)),
        ("each entry is followed by its position-trigger stop", groupings[:2] == ["na",
         "positionTpsl"] and groupings[2] == "positionTpsl", ", ".join(map(str, groupings))),
        ("a subaccount's orders carry its vault address", all(a.get("vaultAddress")
         == SUBACCOUNT[2:] for a in node.venue.actions), str(node.venue.actions[0].get(
         "vaultAddress"))),
        ("a subaccount's account reads ask for its own address", all(i["user"] == SUBACCOUNT
         for i in node.venue.infos if i["type"] in ACCOUNT_READS), str({(i["type"],
         i.get("user")) for i in node.venue.infos})),
    ]  # fmt: skip


def lane_margin(folder: Path) -> list[Check]:
    full = rig(folder / "full")
    full.venue.open_orders = [{"coin": "ETH", "side": "A", "limitPx": "3000.0", "sz": "0.01",
                               "oid": i, "timestamp": 1, "origSz": "0.01", "cloid": None}
                              for i in range(MARGIN_FIXTURE)]  # fmt: skip
    room = rig(folder / "room")
    room.venue.open_orders = full.venue.open_orders[:-1]
    refused, placed = enter(full, name("full")), enter(room, name("room"))
    return [
        (f"the fixture account at its stated margin of {MARGIN_FIXTURE} takes no entry",
         repr(refused).endswith("(open-orders-margin)')") and full.venue.actions == [],
         repr(refused)),
        (f"one order under the margin ({MARGIN_FIXTURE - 1}) the entry goes",
         isinstance(placed, Placed), repr(placed)),
    ]  # fmt: skip


def lane_reconcile(folder: Path) -> list[Check]:
    first = name("before-restart")
    before = rig(folder / "before")
    enter(before, first)
    after = rig(folder / "after", sent=(first,))
    after.venue.open_orders = before.venue.open_orders
    after.venue.history, after.venue.fills = before.venue.history, before.venue.fills
    after.venue.position = before.venue.position
    read = after.client.read_back()
    if isinstance(read, TypedRefusal):
        return [("a fresh client reads the account back", False, repr(read))]
    found = attribute(read.value, tag=TAG, sent=[first])
    rows = [(p.position, p.stop, a.claim) for p, a in found.positions]
    return [
        (
            "a fresh client names the position by its entry and reads its stop",
            rows == [(first, Decimal("2476"), Claim.MINE)],
            repr(rows),
        ),
    ]


def lane_probe(folder: Path) -> list[Check]:
    """A dry run of the testnet probe's own code on the stand-in testnet: the child's marks, the
    fresh process's marks and the cleanup. The fill-event mark needs Hyperliquid's websocket,
    so it is not checked here."""
    probe: Any = importlib.import_module("run")
    venue = Testnet()
    wallet = AgentWallet(ACCOUNT_ADDRESS, AgentKey(SIGNER), 1_809_000_000_000)

    def testnet_exchange(_wallet: AgentWallet, *, streaming: bool = False) -> Any:
        del streaming
        return stand_in(wallet, venue)

    real = probe.testnet_exchange
    probe.testnet_exchange = testnet_exchange
    printed = io.StringIO()

    async def no_stream(_wallet: AgentWallet, _size: Decimal) -> tuple[bool, str]:
        return True, "not run offline"

    (folder / "probe-child").mkdir()
    (folder / "probe-fresh").mkdir()
    try:
        with contextlib.redirect_stdout(printed):
            probe.child(wallet, folder / "probe-child", hold_s=0)
            lines = printed.getvalue().splitlines()
            sent = [line.removeprefix("SENT ") for line in lines if line.startswith("SENT ")]
            later = probe.after_kill(wallet, sent, folder / "probe-fresh", watch=no_stream)
    finally:
        probe.testnet_exchange = real
    marks = [line for line in printed.getvalue().splitlines() if line[:4] in {"PASS", "FAIL"}]
    checked = [m for i, m in enumerate(marks) if i != 6]
    return [
        ("the probe's own marks pass on the stand-in testnet, the stream mark aside",
         len(marks) == 8 and all(m.startswith("PASS") for m in checked) and all(later)
         and Decimal(venue.position) == 0 and venue.open_orders == [], " | ".join(marks)),
        ("the probe never trades past testnet", all(u.startswith(TESTNET) for u in venue.urls),
         f"{len(venue.urls)} requests"),
    ]  # fmt: skip


def lane_stream(folder: Path) -> list[Check]:
    """Mark 7 as the probe runs it: ``watch_fill`` builds its ``ccxt.pro`` exchange through the
    probe's own ``testnet_exchange``. Only the exchange's HTTP call and its websocket are answered
    here: the subscription is recorded, and the venue's fill is pushed back as Hyperliquid's
    ``userFills`` message."""
    del folder
    probe: Any = importlib.import_module("run")
    pro = importlib.import_module("ccxt.pro")
    venue = Testnet()
    wallet = AgentWallet(ACCOUNT_ADDRESS, AgentKey(SIGNER), 1_809_000_000_000)
    real = probe.testnet_exchange
    built: list[Any] = []
    subscribed: list[tuple[str, dict[str, Any]]] = []

    def answered_here(given: AgentWallet, *, streaming: bool = False) -> Any:
        exchange = real(given, streaming=streaming)
        exchange.options["fetchMarkets"] = {"types": ["swap"]}
        socket_url = exchange.urls["api"]["ws"]["public"]
        socket = exchange.client(socket_url)

        def connect(_session: Any, _backoff_delay: float = 0) -> Any:
            if not socket.connected.done():
                socket.connected.resolve(socket_url)
            return socket.connected

        async def send(message: dict[str, Any]) -> None:
            subscribed.append((socket_url, message))

        async def fetch(
            url: str, method: str = "GET", headers: Any = None, body: Any = None
        ) -> Any:
            del headers
            sent_body = cast("dict[str, Any]", json.loads(body) if body else {})
            fills = len(venue.fills)
            answer = venue.answer(url, sent_body)
            exchange.handle_errors(200, "OK", url, method, {}, json.dumps(answer), answer, {}, body)
            if len(venue.fills) > fills and subscribed:
                fill = {**venue.fills[-1], "hash": "0x" + "00" * 32, "startPosition": "0.0",
                        "dir": "Close Long", "closedPnl": "0.0", "cloid": None}  # fmt: skip
                exchange.handle_message(
                    socket,
                    {"channel": "userFills",
                     "data": {"isSnapshot": False, "user": ACCOUNT_ADDRESS, "fills": [fill]}},
                )  # fmt: skip
            return answer

        socket.connect = connect
        socket.send = send
        exchange.fetch = fetch
        built.append(exchange)
        return exchange

    probe.testnet_exchange = answered_here
    try:
        ok, detail = asyncio.run(probe.watch_fill(wallet, Decimal("0.0044")))
    finally:
        probe.testnet_exchange = real
    kinds = [a["action"]["type"] for a in venue.actions]
    stream = built[0] if built else None

    def mainnet_socket(config: dict[str, object]) -> Any:
        exchange = pro.hyperliquid(config)
        exchange.urls["test"]["ws"]["public"] = "wss://api.hyperliquid.xyz/ws"
        return exchange

    refused = make_testnet_exchange(mainnet_socket, wallet)
    return [
        ("mark 7 builds a ccxt.pro exchange and reads the fill from its stream",
         ok and stream is not None and type(stream).__module__.startswith("ccxt.pro"), detail),
        ("every endpoint of the stream exchange is testnet's, its websocket included",
         stream is not None and set(api_urls(stream)) == {TESTNET, TESTNET_WS}
         and all(u.startswith(TESTNET) for u in venue.urls)
         and [u for u, _ in subscribed] == [TESTNET_WS], f"{venue.urls} {subscribed}"),
        ("the stream exchange sends its one order with no builder fee and no referrer",
         kinds == ["order"] and not any("builder" in a["action"] for a in venue.actions),
         json.dumps(venue.actions)[:400]),
        ("a stream exchange with a mainnet websocket is refused before it is used",
         isinstance(refused, TypedRefusal) and refused.context["field"] == "endpoints",
         repr(refused)[:300]),
    ]  # fmt: skip


def perf(folder: Path, *, paced: bool, rounds: int = 20) -> str:
    node = rig(folder / f"perf-{paced}")
    node.exchange.enableRateLimit = paced
    timings: list[float] = []
    for index in range(rounds):
        order = name(f"perf-{index}")
        started = time.perf_counter()  # ambient-scan: allow - the lane's measurement harness
        enter(node, order)
        node.path.close(order, "crypto.eth", Side.LONG, Decimal("2490"), "perf")
        took = time.perf_counter() - started  # ambient-scan: allow - the lane's measurement
        timings.append(took * 1000 / 4)
    pacing = "CCXT's own rate limiter on" if paced else "CCXT's rate limiter off"
    return (
        f"METRIC ms per mapped call, {pacing}: median {statistics.median(timings):.2f}, min "
        f"{min(timings):.2f}, max {max(timings):.2f} over {rounds} rounds of entry, stop, close "
        f"and cancel (4 signed actions and 1 open-order read each, signing included)"
    )


LANES: Mapping[str, Callable[[Path], list[Check]]] = {
    "mapping": lane_mapping,
    "unknown": lane_unknown,
    "cloid": lane_cloid,
    "margin": lane_margin,
    "reconcile": lane_reconcile,
    "probe": lane_probe,
    "stream": lane_stream,
}


def main(argv: list[str]) -> int:
    chosen = argv or list(LANES)
    failed = 0
    with tempfile.TemporaryDirectory(prefix="c16-offline-") as scratch:
        folder = Path(scratch)
        for lane in chosen:
            for check, ok, detail in LANES[lane](folder):
                failed += not ok
                print(
                    f"{'PASS' if ok else 'FAIL'} {lane}: {check}" + ("" if ok else f" ({detail})")
                )
        if not argv or "mapping" in argv:
            print(perf(folder, paced=False))
            print(perf(folder, paced=True))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
