"""A partly filled entry books the size the venue filled (C-12e, LOOSE-ENDS B2).

An IOC market entry can fill short of its order. The unit then holds what filled, and every
exit, stop and kill acts on that size; the rest is never chased. Proved on the conformance
venue, on the fake cTrader broker (which answers ``ORDER_PARTIAL_FILL`` with the deal's filled
volume) and on the fake Hyperliquid behind CCXT. Nothing reaches a broker.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import cast

import test_app_binding as binding
import test_ccxt_client as hyperliquid
from qmf.venue.commands import CommandKind
from qml.unit.model import Side
from qmn.app.runtime import Placed
from qmn.app.store import Json
from test_app_runtime import LIVE_FROM, Rig, play, unit_rows, value
from test_protection_every_order import FIRST_SEND, node_rows, trading

BAR = 900_000_000_000
DAY = 86_400_000_000_000
FILLED = Decimal("1.00")
"""What the conformance venue fills of the dummy's first entry, a 1.61 lot order."""


def first_entry(node: Rig) -> str:
    tags = node.account.received[0].tags
    assert tags is not None
    return tags.client_order_id


def trades(node: Rig) -> list[tuple[object, object, object]]:
    return [(t["trade_id"], t["exit_kind"], t["quantity"]) for t in unit_rows(node, "trade")]


def test_a_partly_filled_entry_is_held_and_stopped_out_at_the_filled_size(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    node.account.partial_fills = [FILLED]
    play(node, FIRST_SEND + BAR + 1)
    name = first_entry(node)
    booked = dict(node.account.positions())
    shown = cast("list[dict[str, Json]]", value(node.node.call("positions", {})))
    play(node, LIVE_FROM + 2 * DAY, start=FIRST_SEND + BAR + 1)
    fills = [f for f in unit_rows(node, "fill") if f["position_id"] == name]

    assert node.account.received[0].quantity == Decimal("1.61")
    assert booked == {name: ("fx.eurusd", "short", FILLED, Decimal("1.06889"))}
    assert [(row["position"], row["quantity"]) for row in shown] == [(name, "1.00")]
    filled = [r for r in node_rows(node, "order") if r["step"] == "filled"]
    assert [(r["client_order_id"], r["quantity"]) for r in filled][:1] == [(name, "1.00")]
    assert [(f["kind"], f["quantity"], f.get("receipt_quantity")) for f in fills] == [
        ("entry", "1.00", "1.61"),
        ("stop", "1.00", None),
    ]
    assert trades(node)[0] == (name, "stop", "1.00")


def test_a_kill_after_a_partial_fill_closes_the_filled_size_and_leaves_nothing_open(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    node.account.partial_fills = [FILLED]
    play(node, FIRST_SEND + BAR + 1)
    name = first_entry(node)
    killed = node.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    play(node, FIRST_SEND + 3 * BAR + 1, start=FIRST_SEND + BAR + 1)
    closes = [t for t in node.account.received if t.command.kind is CommandKind.CLOSE_POSITION]

    assert value(killed) == {"level_in_force": "RED"}
    assert [(t.position, t.market_id) for t in closes] == [(name, "fx.eurusd")]
    assert node.account.positions() == {}
    assert trades(node) == [(name, "close", "1.00")]


def test_a_partial_fill_whose_answer_was_lost_books_the_size_the_venue_holds(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    node.account.lose_answers = 1
    node.account.partial_fills = [FILLED]
    play(node, FIRST_SEND + 2 * BAR + 1)
    name = first_entry(node)
    held = dict(node.account.positions())
    play(node, LIVE_FROM + 2 * DAY, start=FIRST_SEND + 2 * BAR + 1)
    resolved = [r["resolved"] for r in node_rows(node, "reconcile")]

    assert held == {name: ("fx.eurusd", "short", FILLED, Decimal("1.06889"))}
    assert resolved[:2] == [
        [],
        [
            {
                "client_order_id": name,
                "outcome": "filled",
                "price": "1.06858",
                "quantity": "1.00",
            }
        ],
    ]
    assert trades(node)[0] == (name, "stop", "1.00")
    assert [t.tags.client_order_id for t in node.account.received if t.tags].count(name) == 1


@dataclass
class PartlyFillingCTrader(binding.FakeCTrader):
    """The fake demo broker, filling each coming entry at the next volume of ``fills`` only:
    it answers ``ORDER_PARTIAL_FILL`` with the deal's filled volume and cancels the rest."""

    fills: list[int] = field(default_factory=list[int])
    _asked: int = 0

    def _on_ProtoOANewOrderReq(self, msg_id: str, body: dict[str, object]) -> None:
        self._asked = int(str(body["volume"]))
        filled = self.fills.pop(0) if self.fills else self._asked
        super()._on_ProtoOANewOrderReq(msg_id, {**body, "volume": str(filled)})

    def _say(self, name: str, values: dict[str, object] | object, msg_id: str = "") -> None:
        body = cast("dict[str, object]", values)
        order = cast("dict[str, object]", body.get("order") or {})
        deal = cast("dict[str, object]", body.get("deal") or {})
        if (
            name == "ProtoOAExecutionEvent"
            and body.get("executionType") == "ORDER_FILLED"
            and order.get("closingOrder") is False
            and deal.get("filledVolume") != self._asked
        ):
            body = {
                **body,
                "executionType": "ORDER_PARTIAL_FILL",
                "deal": {**deal, "volume": self._asked},
            }
        super()._say(name, body, msg_id)


def test_a_ctrader_partial_fill_is_held_and_killed_at_the_deal_filled_volume(
    tmp_path: Path,
) -> None:
    broker = PartlyFillingCTrader(binding.codec(), fills=[300_000])
    rig = binding.bound_rig(tmp_path, broker=broker)
    binding.signed_in(rig)
    binding.bind(rig)
    binding.deploy_dummy(rig)
    at = binding.play_until_sent(rig)
    name = binding.sent_entries(rig)[0]
    binding.play_spots(rig, at, at + BAR)
    killed = rig.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    binding.play_spots(rig, at + BAR, at + 2 * BAR)
    filled = [r for r in binding.node_rows(rig, "order") if r["step"] == "filled"]
    rows = binding.value(rig.node.call("journal_tail", {"streams": ["unit"]}))["rows"]
    trades = [
        (body["trade_id"], body["quantity"])
        for row in cast("list[dict[str, Json]]", rows)
        if row["kind"] == "trade"
        for body in [cast("dict[str, Json]", row["body"])]
    ]
    asked = [b["volume"] for n, b in broker.received if n == "ProtoOANewOrderReq"]

    assert asked[0] == "400000"
    assert [(r["client_order_id"], r["quantity"]) for r in filled] == [(name, "0.03")]
    assert value(killed) == {"level_in_force": "RED"}
    assert binding.closes(rig) == [
        {"ctidTraderAccountId": "4401", "positionId": "9001", "volume": "300000"}
    ]
    assert trades == [(name, "0.03")]
    assert broker.held == {}
    binding.runtime(rig).stop()


@dataclass
class TwoDealCTrader(binding.FakeCTrader):
    """The fake demo broker, filling each entry in two deals: ``ORDER_PARTIAL_FILL`` for
    300000, then ``ORDER_FILLED`` for the rest, the position growing to the order's volume."""

    def _on_ProtoOANewOrderReq(self, msg_id: str, body: dict[str, object]) -> None:
        lose, self.lose_answers = self.lose_answers, 1
        super()._on_ProtoOANewOrderReq(msg_id, body)
        self.lose_answers = lose
        held = self.held[self._next]
        full = held.volume
        held.volume = 300_000
        self._execution("ORDER_ACCEPTED", held, "POSITION_STATUS_OPEN", held.price, "MARKET", msg_id)
        self._deal("ORDER_PARTIAL_FILL", held, 300_000, msg_id)
        held.volume = full
        self._deal("ORDER_FILLED", held, full - 300_000, msg_id)

    def _deal(self, kind: str, held: binding.Held, volume: int, msg_id: str) -> None:
        self._execution(kind, held, "POSITION_STATUS_OPEN", held.price, "MARKET", msg_id)
        frame = self.codec.decode(self._out.pop())
        body = dict(frame.value.body)  # type: ignore[union-attr]
        body["deal"] = {**body["deal"], "filledVolume": volume}  # type: ignore[dict-item]
        self._say("ProtoOAExecutionEvent", body, msg_id)


def test_a_ctrader_entry_filled_in_two_deals_is_killed_at_the_whole_position_volume(
    tmp_path: Path,
) -> None:
    broker = TwoDealCTrader(binding.codec())
    rig = binding.bound_rig(tmp_path, broker=broker)
    binding.signed_in(rig)
    binding.bind(rig)
    binding.deploy_dummy(rig)
    at = binding.play_until_sent(rig)
    binding.play_spots(rig, at, at + BAR)
    held = {position: h.volume for position, h in broker.held.items()}
    killed = rig.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    binding.play_spots(rig, at + BAR, at + 2 * BAR)

    assert held == {9001: 400_000}
    assert value(killed) == {"level_in_force": "RED"}
    assert binding.closes(rig) == [
        {"ctidTraderAccountId": "4401", "positionId": "9001", "volume": "400000"}
    ]
    assert broker.held == {}
    binding.runtime(rig).stop()


@dataclass
class PartlyFillingHyperliquid(hyperliquid.FakeHyperliquid):
    """The fake Hyperliquid, filling an entry's IOC order at ``fill`` only."""

    fill: str = "0.006"
    asked: list[str] = field(default_factory=list[str])
    """The amount of each entry the node asked for."""

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
        entry = "stopLoss" not in given and given.get("reduceOnly") is not True
        if entry:
            self.asked.append(amount)
        return super().create_order(
            symbol, type, side, self.fill if entry else amount, price, params
        )


def test_a_ccxt_ioc_entry_filled_in_part_is_held_stopped_and_closed_at_its_fill(
    tmp_path: Path,
) -> None:
    exchange = PartlyFillingHyperliquid()
    node = hyperliquid.rig(tmp_path, exchange)
    placed = hyperliquid.enter(node)
    closed = node.path.close(hyperliquid.NAME, "crypto.eth", Side.LONG, Decimal("2501.0"), "unit")
    orders = [call for call in exchange.calls if call[0] == "create_order"]

    assert exchange.asked == ["0.0100"]
    assert placed == Placed(Decimal("2501.0"), Decimal("0.006"))
    assert [
        (call[3], call[4], "stopLoss" in cast("dict[str, object]", call[6])) for call in orders[1:]
    ] == [
        ("buy", "0.006", True),
        ("sell", "0.006", False),
    ]
    assert closed == Placed(Decimal("2501.0"))
