"""The ccxt venue client against a fake Hyperliquid with CCXT 4.5.85's method names (C-16).

The fake answers as CCXT's unified calls do, numbers as floats included, and records every call.
No network, no CCXT import and no real wallet: the one signer below is made from a hash at test
time. Orders go through the node's own order path (C-12a), so each test sees what the venue
would receive from the node.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qmb.host.unit_handler import FillKind
from qmf.core import Account, AccountRole, Result, TypedRefusal, VenueId, World
from qmf.data.journal_envelope import JournalStream, JournalWorld
from qmf.data.journal_writer import JournalWriter, WriterScope
from qmf.venue.commands import Command
from qml.numbers import InstrumentRecord, lots, parse_record
from qml.unit.model import Side
from qmn.app.attribution import Claim, attribute
from qmn.app.feed_keeper import FeedKeeper, Quote, RecordedSource, Recording
from qmn.app.reconciler import Reconciler, journal_sends
from qmn.app.runtime import Blocked, OrderPath, Placed, Ticket, Unknown, Venue, VenueClose, ulid
from qmn.order.protection import require_venue_resident_protective_stop
from qmn.venue import CloseScope, OrderParameters, OrderType, TimeInForce
from qmn.venue.ccxt_client import (
    ERRORS,
    AgentWallet,
    CcxtClient,
    agent_wallets,
    cloid,
    cloid_tag,
    read_error,
    renewal_due,
)
from qmn.venue.port import VenueClientKind, select_venue_client

T0 = 1_762_000_000_000_000_000
TAG = "a4dqobyh"
OTHER_TAG = "b7xkq2mn"
NAME = f"q{TAG}-{ulid(1_762_000_000_000, 'dep-1/row-1')}"
LABEL = f"qmx:{TAG}:dummy-trend-pullback"
ETH = "ETH/USDC:USDC"
VENUE = VenueId("hyperliquid-testnet")
ACCOUNT = Account("hl-testnet-1", VENUE, AccountRole.DEMO)
ADDRESS = "0x" + "ab" * 20
SIGNER = "0x" + hashlib.sha256(b"c16 test signer, never a wallet").hexdigest()
TESTNET = "https://api.hyperliquid-testnet.xyz"
CCXT_ERRORS_4_5_85 = {
    "BaseError", "ExchangeError", "AuthenticationError", "PermissionDenied",
    "AccountNotEnabled", "AccountSuspended", "ArgumentsRequired", "BadRequest", "BadSymbol",
    "OperationRejected", "NoChange", "MarginModeAlreadySet", "MarketClosed",
    "ManualInteractionNeeded", "RestrictedLocation", "InsufficientFunds", "InvalidAddress",
    "AddressPending", "InvalidOrder", "OrderNotFound", "OrderNotCached",
    "OrderImmediatelyFillable", "OrderNotFillable", "DuplicateOrderId", "ContractUnavailable",
    "NotSupported", "InvalidProxySettings", "ExchangeClosedByUser", "OperationFailed",
    "NetworkError", "DDoSProtection", "RateLimitExceeded", "ExchangeNotAvailable",
    "OnMaintenance", "InvalidNonce", "ChecksumError", "RequestTimeout", "BadResponse",
    "NullResponse", "CancelPending", "UnsubscribeError",
}  # fmt: skip
"""Every class in ``ccxt/base/errors.py`` of the pinned CCXT 4.5.85."""


class InsufficientFunds(Exception):
    pass


class RequestTimeout(Exception):
    pass


class ExchangeError(Exception):
    pass


class Teapot(Exception):
    """An error class CCXT 4.5.85 does not have."""


def _record() -> InstrumentRecord:
    document = {
        "venue": "hyperliquid-testnet",
        "symbol": "ETH",
        "market_id": "crypto.eth",
        "class": "perp",
        "currency": "USDC",
        "digits": 1,
        "tick_size": "0.1",
        "pip": {"size": "0.1", "source": "test record"},
        "contract_size": "1",
        "value_per_point": "1",
        "lot_step": "0.0001",
        "min_lot": "0.0001",
        "max_lot": "1000",
        "calendar_ref": "crypto-24x7@1",
        "zone": "UTC",
        "day_boundary": "00:00",
        "data_levels": {"levels": [0, 1, 2], "volume": "tick_count"},
        "leverage": {"version": 1, "tiers": [{"up_to_lots": "1000", "leverage": "10"}]},
        "margin": {"intraday": "0.1", "overnight": "0.1"},
        "record_version": 1,
        "status": "specified",
    }
    parsed = parse_record(document)
    assert not isinstance(parsed, TypedRefusal), parsed
    return parsed.value


RECORD = _record()


@dataclass
class FakeHyperliquid:
    """Hyperliquid as CCXT 4.5.85's unified calls answer it, in memory."""

    options: dict[str, object] = field(default_factory=lambda: {"sandboxMode": True})
    urls: dict[str, object] = field(
        default_factory=lambda: {"api": {"public": TESTNET, "private": TESTNET}}
    )
    walletAddress: str | None = ADDRESS
    fill_price: float = 2501.0
    calls: list[tuple[object, ...]] = field(default_factory=list[tuple[object, ...]])
    raises: dict[str, list[Exception]] = field(default_factory=dict[str, list[Exception]])
    open_orders: list[dict[str, object]] = field(default_factory=list[dict[str, object]])
    orders: list[dict[str, object]] = field(default_factory=list[dict[str, object]])
    trades: list[dict[str, object]] = field(default_factory=list[dict[str, object]])
    positions: list[dict[str, object]] = field(default_factory=list[dict[str, object]])
    lose_answers: int = 0
    """How many of the next filled orders fill at the venue and then lose their answer."""

    def handle_builder_fee_approval(self) -> bool:
        self.calls.append(("approve_builder_fee",))
        return True

    def _raise(self, call: str) -> None:
        queued = self.raises.get(call)
        if queued:
            raise queued.pop(0)

    def create_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: str,
        price: str | None = None,
        params: Mapping[str, object] | None = None,
    ) -> Mapping[str, object]:
        given = dict(params or {})
        self.calls.append(("create_order", symbol, type, side, amount, price, given))
        self._raise("create_order")
        oid = str(len(self.calls))
        if "stopLoss" in given:
            trigger = float(str(cast("dict[str, object]", given["stopLoss"])["triggerPrice"]))
            self.open_orders.append(
                {
                    "id": oid,
                    "clientOrderId": given["clientOrderId"],
                    "symbol": symbol,
                    "reduceOnly": True,
                    "triggerPrice": trigger,
                    "status": "open",
                    "filled": 0.0,
                }
            )
            return {"id": None, "status": "waitingForTrigger", "filled": None, "average": None}
        size = float(amount)
        if given.get("reduceOnly") is True:
            self.positions = [p for p in self.positions if p["symbol"] != symbol]
        else:
            self.positions = [
                {
                    "symbol": symbol,
                    "side": "long" if side == "buy" else "short",
                    "contracts": size,
                    "entryPrice": self.fill_price,
                }
            ]
        self.trades.append(
            {"order": oid, "symbol": symbol, "side": side, "price": self.fill_price, "amount": size}
        )
        if given.get("reduceOnly") is not True:
            self.orders.append(
                {"id": oid, "clientOrderId": given["clientOrderId"], "symbol": symbol,
                 "filled": size, "status": "closed", "timestamp": len(self.calls)}
            )  # fmt: skip
        if self.lose_answers > 0:
            self.lose_answers -= 1
            raise RequestTimeout("the answer was lost after the fill")
        return {
            "id": oid,
            "clientOrderId": given["clientOrderId"],
            "status": None,
            "filled": size,
            "average": self.fill_price,
        }

    def cancel_order(
        self, id: str, symbol: str | None = None, params: Mapping[str, object] | None = None
    ) -> Mapping[str, object]:
        given = dict(params or {})
        self.calls.append(("cancel_order", id, symbol, given))
        self._raise("cancel_order")
        self.open_orders = [
            o for o in self.open_orders if o["clientOrderId"] != given.get("clientOrderId")
        ]
        return {"id": None, "status": "canceled"}

    def fetch_open_orders(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: Mapping[str, object] | None = None,
    ) -> Sequence[Mapping[str, object]]:
        self.calls.append(("fetch_open_orders",))
        self._raise("fetch_open_orders")
        return list(self.open_orders)

    def fetch_orders(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: Mapping[str, object] | None = None,
    ) -> Sequence[Mapping[str, object]]:
        self.calls.append(("fetch_orders",))
        return list(self.orders)

    def fetch_my_trades(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: Mapping[str, object] | None = None,
    ) -> Sequence[Mapping[str, object]]:
        self.calls.append(("fetch_my_trades", symbol))
        return [t for t in self.trades if symbol is None or t["symbol"] == symbol]

    def fetch_positions(
        self, symbols: Sequence[str] | None = None, params: Mapping[str, object] | None = None
    ) -> Sequence[Mapping[str, object]]:
        self.calls.append(("fetch_positions",))
        return list(self.positions)

    def fetch_balance(self, params: Mapping[str, object] | None = None) -> Mapping[str, object]:
        self.calls.append(("fetch_balance",))
        return {"total": {"USDC": 1000.25}}

    def sent_orders(self) -> list[tuple[object, ...]]:
        return [c for c in self.calls if c[0] in {"create_order", "cancel_order"}]


def _wallet(expires_at: str = "2027-04-30T00:00:00+00:00") -> AgentWallet:
    document = {
        "schema_version": "qmx.node.keys/1",
        "hyperliquid": [{"address": ADDRESS, "agent_key": SIGNER, "expires_at": expires_at}],
    }
    parsed = agent_wallets(document)
    assert not isinstance(parsed, TypedRefusal), parsed
    return parsed.value[0]


@dataclass
class Rig:
    exchange: FakeHyperliquid
    client: CcxtClient
    path: OrderPath
    now: list[int]
    alarms: list[Mapping[str, object]]
    journal: Path
    writer: JournalWriter


def rig(tmp_path: Path, exchange: FakeHyperliquid | None = None, sent: Sequence[str] = ()) -> Rig:
    venue = exchange or FakeHyperliquid()
    now = [T0]
    alarms: list[Mapping[str, object]] = []
    opened = CcxtClient.open(
        venue,
        account=ACCOUNT,
        wallet=_wallet(),
        markets={"crypto.eth": ETH},
        ccxt_version="4.5.85",
        clock_ns=lambda: now[0],
        on_alarm=alarms.append,
        sent=lambda: sent,
    )
    assert not isinstance(opened, TypedRefusal), opened
    source = RecordedSource([])
    feed = FeedKeeper(
        "hyperliquid", "testnet", source, ("crypto.eth",), lambda: now[0], Recording(None)
    )
    source.play([Quote("crypto.eth", T0, Decimal("2499.5"), Decimal("2500.5"), "both")])
    feed.pump()
    scope = WriterScope(JournalStream.NODE, TAG, JournalWorld.DEMO, "pc", "node", "0.1.0")
    journal = JournalWriter.open(tmp_path, scope, clock=lambda: now[0], boot_epoch_id="b1")
    assert not isinstance(journal, TypedRefusal), journal

    def sleep(seconds: float) -> None:
        now[0] += int(seconds * 1e9)

    path = OrderPath(
        TAG, Venue(opened.value, feed), journal.value, lambda: now[0], sleep, alarms.append
    )
    return Rig(venue, opened.value, path, now, alarms, tmp_path, journal.value)


def enter(node: Rig, name: str = NAME, side: Side = Side.LONG, stop: str = "2475.5") -> object:
    quantity = lots(Decimal("0.01"), RECORD)
    assert not isinstance(quantity, TypedRefusal), quantity
    return node.path.entry(
        client_order_id=name,
        label=LABEL,
        wire={
            "order": {"type": "market"},
            "direction": side.value,
            "market_id": "crypto.eth",
            "protection": {"stop": stop},
            "quantity": "0.01",
            "decision_row_id": "row-1",
        },
        record=RECORD,
        quantity=quantity.value,
        blocked_by=None,
    )


def test_an_entry_goes_ioc_with_its_cloid_then_its_stop_as_a_whole_position_trigger(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    placed = enter(node)
    sends = journal_sends(node.journal)
    assert not isinstance(sends, TypedRefusal), sends

    assert placed == Placed(Decimal("2501.0"))
    assert node.exchange.sent_orders() == [
        (
            "create_order", ETH, "market", "buy", "0.0100", "2500.5",
            {"clientOrderId": "0x716d0707070707ca00e19289fa04f0ca", "timeInForce": "Ioc",
             "slippage": "0.05"},
        ),
        (
            "create_order", ETH, "market", "buy", "0.01", "2476.0",
            {"clientOrderId": "0x716d070707070755e2a6e838c0e2306a",
             "stopLoss": {"triggerPrice": "2476.0", "type": "market"},
             "grouping": "positionTpsl"},
        ),
    ]  # fmt: skip
    assert node.client.stop_of(NAME) == Decimal("2476.0")
    assert sends.value[NAME]["stop_form"] == "position-trigger-after-fill"
    assert node.alarms == []


def test_every_order_the_node_sends_carries_its_cloid_and_the_stop_stays_on(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    enter(node)
    tightened = node.path.amend(
        NAME,
        "crypto.eth",
        Side.LONG,
        Decimal("2480.0"),
        Decimal("2501.0"),
        Decimal("2476.0"),
        RECORD,
    )
    closed = node.path.close(NAME, "crypto.eth", Side.LONG, Decimal("2490"), "unit")
    sent = node.exchange.sent_orders()
    tags = [cloid_tag(str(cast("dict[str, object]", c[-1])["clientOrderId"])) for c in sent]
    stop_1, stop_2 = "0x716d070707070755e2a6e838c0e2306a", "0x716d0707070707f036ea5e4faee7346b"

    assert tightened == Placed(Decimal("2480.0"))
    assert closed == Placed(Decimal("2501.0"))
    assert tags == [TAG] * 6
    assert sent[2:] == [
        (
            "create_order", ETH, "market", "buy", "0.01", "2480.0",
            {"clientOrderId": stop_2, "stopLoss": {"triggerPrice": "2480.0", "type": "market"},
             "grouping": "positionTpsl"},
        ),
        ("cancel_order", stop_1, ETH, {"clientOrderId": stop_1}),
        (
            "create_order", ETH, "market", "sell", "0.01", "2490",
            {"clientOrderId": "0x716d0707070707eb84404b5048d254d0", "reduceOnly": True,
             "timeInForce": "Ioc", "slippage": "0.05"},
        ),
        ("cancel_order", stop_2, ETH, {"clientOrderId": stop_2}),
    ]  # fmt: skip
    assert node.client.closed(NAME) == VenueClose(FillKind.CLOSE, Decimal("2501.0"))
    assert node.exchange.open_orders == []


def test_an_error_ccxt_does_not_have_is_unknown_with_an_alarm_and_never_sent_again(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    node.exchange.raises["create_order"] = [Teapot("418")]
    first = enter(node)
    again = enter(node, name=f"q{TAG}-{ulid(1_762_000_060_000, 'dep-1/row-2')}")

    assert first == Unknown("venue answer unknown for this order", NAME)
    assert again == Blocked(
        "venue answer unknown for an earlier order, so no entry until it resolves"
    )
    assert node.path.unknown == {NAME: "crypto.eth"}
    assert len(node.exchange.sent_orders()) == 1
    assert node.alarms == [
        {
            "alarm": "venue_error_unmapped",
            "venue": "hyperliquid-testnet",
            "account": "hl-testnet-1",
            "call": "create_order",
            "error": "Teapot",
        }
    ]


@pytest.mark.parametrize(
    ("raised", "answer", "alarms"),
    [
        (InsufficientFunds("margin"), Blocked("the venue refused the order (insufficient-funds)"),
         []),
        (RequestTimeout("slow"), Unknown("venue answer unknown for this order", NAME), []),
        (ExchangeError("new words"), Unknown("venue answer unknown for this order", NAME),
         ["venue_error_unread"]),
    ],
)  # fmt: skip
def test_each_ccxt_error_reads_as_its_table_row(
    tmp_path: Path, raised: Exception, answer: object, alarms: list[str]
) -> None:
    node = rig(tmp_path)
    node.exchange.raises["create_order"] = [raised]

    assert enter(node) == answer
    assert [a["alarm"] for a in node.alarms] == alarms


def test_the_table_reads_every_error_class_of_the_pinned_ccxt() -> None:
    assert set(ERRORS) == CCXT_ERRORS_4_5_85
    assert read_error(RequestTimeout()).code == "request-timeout"
    assert read_error(Teapot()).code == "unmapped:Teapot"


def test_no_entry_goes_while_the_account_holds_the_open_order_margin(tmp_path: Path) -> None:
    full = FakeHyperliquid(open_orders=[{"id": str(i), "status": "open"} for i in range(900)])
    room = FakeHyperliquid(open_orders=[{"id": str(i), "status": "open"} for i in range(899)])

    assert enter(rig(tmp_path / "full", full)) == Blocked(
        "the venue refused the order (open-orders-margin)"
    )
    assert full.sent_orders() == []
    assert enter(rig(tmp_path / "room", room)) == Placed(Decimal("2501.0"))


@dataclass
class Units:
    """The node's hosted units as reconcile resolves them."""

    resolved: list[tuple[str, Decimal | None, bool]] = field(
        default_factory=list[tuple[str, Decimal | None, bool]]
    )

    def resolve(self, client_order_id: str, price: Decimal | None, *, protected: bool) -> bool:
        self.resolved.append((client_order_id, price, protected))
        return True


def test_an_entry_whose_answer_was_lost_is_reconciled_and_its_protection_close_goes_flat(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    node.exchange.lose_answers = 1
    lost = enter(node)
    units = Units()
    reconciler = Reconciler(node.writer, tmp_path, TAG, lambda: node.now[0], node.alarms.append)
    reconciler.run("hl-testnet-1", 1, node.client, node.path.unknown, [units])
    closed = node.path.close(NAME, "crypto.eth", Side.LONG, Decimal("2490"), "protection")

    assert lost == Unknown("venue answer unknown for this order", NAME)
    assert units.resolved == [(NAME, Decimal("2501.0"), False)]
    assert [a["alarm"] for a in node.alarms] == ["protection_escalation"]
    assert closed == Placed(Decimal("2501.0"))
    assert node.exchange.sent_orders()[1:] == [
        (
            "create_order", ETH, "market", "sell", "0.01", "2490",
            {"clientOrderId": "0x716d070707070783d2558f065e537e83", "reduceOnly": True,
             "timeInForce": "Ioc", "slippage": "0.05"},
        ),
    ]  # fmt: skip
    assert node.exchange.positions == []


def test_a_stop_that_fired_at_the_venue_reads_closed_once_per_poll(tmp_path: Path) -> None:
    node = rig(tmp_path)
    enter(node)
    node.exchange.positions = []
    node.exchange.open_orders = []
    node.exchange.trades.append(
        {"order": "9", "symbol": ETH, "side": "sell", "price": 2470.0, "amount": 0.01}
    )
    node.now[0] += 2_000_000_000
    first = node.client.closed(NAME)
    polls = node.exchange.calls.count(("fetch_positions",))

    assert first == VenueClose(FillKind.STOP, Decimal("2470.0"), gap=True)
    assert node.client.closed(NAME) == first
    assert polls == 1
    assert node.exchange.calls.count(("fetch_positions",)) == 1


def test_a_restarted_client_reads_its_own_foreign_and_untagged_records(tmp_path: Path) -> None:
    foreign = f"q{OTHER_TAG}-{ulid(1_762_000_000_000, 'another node')}"
    venue = FakeHyperliquid(
        orders=[
            {"id": "11", "clientOrderId": cloid(NAME), "symbol": ETH, "filled": 0.01,
             "status": "closed", "timestamp": 1},
            {"id": "21", "clientOrderId": cloid(foreign), "symbol": "BTC/USDC:USDC",
             "filled": 0.001, "status": "closed", "timestamp": 2},
            {"id": "31", "clientOrderId": None, "symbol": "SOL/USDC:USDC", "filled": 1.0,
             "status": "closed", "timestamp": 3},
        ],
        open_orders=[
            {"id": "12", "clientOrderId": cloid(f"{NAME}/stop-1"), "symbol": ETH,
             "reduceOnly": True, "triggerPrice": 2476.0, "status": "open", "filled": 0.0},
            {"id": "22", "clientOrderId": cloid(f"{foreign}/stop-1"), "symbol": ETH,
             "reduceOnly": True, "triggerPrice": 2600.0, "status": "open", "filled": 0.0},
        ],
        trades=[
            {"order": "11", "symbol": ETH, "side": "buy", "price": 2501.0, "amount": 0.01},
            {"order": "21", "symbol": "BTC/USDC:USDC", "side": "buy", "price": 60000.0,
             "amount": 0.001},
            {"order": "31", "symbol": "SOL/USDC:USDC", "side": "sell", "price": 150.0,
             "amount": 1.0},
        ],
        positions=[
            {"symbol": ETH, "side": "long", "contracts": 0.01, "entryPrice": 2501.0},
            {"symbol": "BTC/USDC:USDC", "side": "long", "contracts": 0.001,
             "entryPrice": 60000.0},
            {"symbol": "SOL/USDC:USDC", "side": "short", "contracts": 1.0, "entryPrice": 150.0},
        ],
    )  # fmt: skip
    node = rig(tmp_path, venue, sent=[NAME])
    read = node.client.read_back()
    assert not isinstance(read, TypedRefusal), read
    found = attribute(read.value, tag=TAG, sent=[NAME])
    close = Command.close_position(
        VENUE, ACCOUNT, "s1", 1, CloseScope.INSTRUMENT_WITHIN_BINDING, NAME
    )
    assert not isinstance(close, TypedRefusal), close
    after = node.client.send(
        Ticket(close.value, "crypto.eth", Side.LONG, Decimal("2490"), position=NAME)
    )

    assert [
        (p.position, p.market_id, p.side, p.quantity, p.stop, a.claim, a.tags)
        for p, a in found.positions
    ] == [
        (NAME, "crypto.eth", "long", Decimal("0.01"), Decimal("2476.0"), Claim.MINE, (TAG,)),
        ("qb7xkq2mn-000000000001RHPRJG34N2N6JG", "BTC/USDC:USDC", "long", Decimal("0.001"), None,
         Claim.FOREIGN, (OTHER_TAG,)),
        ("SOL/USDC:USDC", "SOL/USDC:USDC", "short", Decimal("1.0"), None, Claim.UNTAGGED, ()),
    ]  # fmt: skip
    assert [(o.client_order_id, o.state.value, o.price) for o in read.value.orders] == [
        (NAME, "filled", Decimal("2501.0")),
        ("qb7xkq2mn-000000000001RHPRJG34N2N6JG", "filled", Decimal("60000.0")),
        (None, "filled", Decimal("150.0")),
    ]
    assert found.stand_down is Claim.FOREIGN
    assert not isinstance(after, TypedRefusal), after
    assert (after.value.outcome.value, after.value.price) == (
        "accepted-by-venue",
        Decimal("2501.0"),
    )
    assert node.exchange.sent_orders()[0][3:5] == ("sell", "0.01")


def test_the_agent_wallet_reads_from_the_keys_document_and_never_prints() -> None:
    wallet = _wallet("2026-12-01T00:00:00+00:00")
    bad = agent_wallets(
        {
            "schema_version": "qmx.node.keys/1",
            "hyperliquid": [{"address": ADDRESS, "agent_key": SIGNER[:-2], "expires_at": "x"}],
        }
    )
    fifteen_days_before = 1_796_083_200_000 - 15 * 86_400_000

    assert (wallet.address, wallet.expires_at_ms, wallet.subaccount) == (
        ADDRESS,
        1_796_083_200_000,
        None,
    )
    assert wallet.agent_key.reveal() == SIGNER
    assert SIGNER not in repr(wallet)
    assert isinstance(bad, TypedRefusal)
    assert dict(bad.context) == {
        "field": "hyperliquid",
        "reason": "agent_key is the agent wallet's 32-byte 0x key",
        "index": 0,
    }
    assert SIGNER[:-2] not in json.dumps(dict(bad.context))
    assert agent_wallets({"schema_version": "qmx.node.keys/1"}) == agent_wallets(
        {"schema_version": "qmx.node.keys/1", "hyperliquid": []}
    )
    assert renewal_due(wallet, fifteen_days_before) is False
    assert renewal_due(wallet, fifteen_days_before + 86_400_000) is True


def _refused_field(make: Callable[[], object]) -> object:
    answer = make()
    assert isinstance(answer, TypedRefusal), answer
    return answer.context["field"]


def test_the_client_binds_the_pinned_ccxt_on_testnet_for_its_own_signer_only() -> None:
    def opened(
        venue: FakeHyperliquid, version: str = "4.5.85", now: int = T0
    ) -> Result[CcxtClient]:
        return CcxtClient.open(
            venue,
            account=ACCOUNT,
            wallet=_wallet(),
            markets={"crypto.eth": ETH},
            ccxt_version=version,
            clock_ns=lambda: now,
            on_alarm=lambda _alarm: None,
            sent=lambda: (),
        )

    venue = FakeHyperliquid()
    bound = opened(venue)
    assert not isinstance(bound, TypedRefusal)

    assert _refused_field(lambda: opened(FakeHyperliquid(), "4.5.86")) == "ccxt_version"
    assert _refused_field(lambda: opened(FakeHyperliquid(options={}))) == "sandbox_mode"
    mainnet = FakeHyperliquid(options={"sandboxMode": False})
    assert _refused_field(lambda: opened(mainnet)) == "sandbox_mode"
    flagged = FakeHyperliquid(
        urls={"api": {"public": TESTNET, "private": "https://api.hyperliquid.xyz"}}
    )
    assert _refused_field(lambda: opened(flagged)) == "endpoints"
    other = FakeHyperliquid(walletAddress="0x" + "cd" * 20)
    assert _refused_field(lambda: opened(other)) == "wallet_address"
    late = 1_809_043_200_000_000_000
    assert _refused_field(lambda: opened(FakeHyperliquid(), now=late)) == "expires_at"
    assert venue.options == {"sandboxMode": True, "refSet": True, "approvedBuilderFee": False}
    assert venue.handle_builder_fee_approval() is True
    assert venue.calls == []
    assert bound.value.equity() == Decimal("1000.25")


def test_live_selection_opens_to_ccxt_and_replay_refuses_it() -> None:
    live = select_venue_client(World.LIVE, VENUE, "ccxt")
    replay = select_venue_client(World.REPLAY, VENUE, VenueClientKind.CCXT)

    assert not isinstance(live, TypedRefusal)
    assert live.value.kind is VenueClientKind.CCXT
    assert isinstance(replay, TypedRefusal)
    assert replay.context["given"] == "ccxt"


def test_the_gate_proves_the_position_trigger_form_from_the_entry_stop_distance(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    quantity = lots(Decimal("0.01"), RECORD)
    assert not isinstance(quantity, TypedRefusal)
    bare = OrderParameters.try_create(
        OrderType.MARKET, TimeInForce.IMMEDIATE_OR_CANCEL, quantity.value
    )
    assert not isinstance(bare, TypedRefusal), bare
    command = Command.place_order(VENUE, ACCOUNT, "s1", 1, bare.value)
    assert not isinstance(command, TypedRefusal), command
    refused = require_venue_resident_protective_stop(
        command.value, forms_per_order_type=node.client.stop_forms
    )

    assert node.client.stop_forms == {"market": "position-trigger-after-fill"}
    assert isinstance(refused, TypedRefusal)
    assert refused.context["field"] == "protective_stop_distance"
    assert refused.context["required_form"] == "position-trigger-after-fill"
    assert cloid(NAME) == "0x716d0707070707ca00e19289fa04f0ca"
    assert cloid_tag(cloid(NAME)) == TAG
    assert cloid_tag("0x" + "12" * 16) is None
    assert cloid("not a node order") is None
    assert node.client.kind is VenueClientKind.CCXT
