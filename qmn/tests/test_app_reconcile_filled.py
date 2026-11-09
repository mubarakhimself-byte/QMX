"""An entry whose answer was lost is found by its label (C-12e, LOOSE-ENDS B3).

cTrader's reconcile lists pending orders, not filled ones, so a filled entry may show only as
its position, which carries the unit's label. The reconciler reads such an order as filled into
the one open position with its label, market and side that no other order opened, under the
venue's own name, and the kill closes it. It reads the order absent only when no such position
is open, and two of them keep it UNKNOWN with an alarm. Conformance venue and the fake cTrader
broker only.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import cast

import test_app_binding as binding
from qmf.core import Ok, Result, is_refusal
from qmf.venue.commands import CommandKind
from qmn.app.attribution import OrderState, ReadBack, VenueOrder, VenuePosition
from qmn.app.runtime import Sent, Ticket
from qmn.venue import SubmissionOutcome
from test_app_runtime import LIVE_FROM, Rig, play, value
from test_protection_every_order import FIRST_SEND, node_rows, trading

BAR = 900_000_000_000
DAY = 86_400_000_000_000
LABEL = "qmx:a4dqobyh:dummy-trend-pullback"


def pending_only(node: Rig) -> None:
    """The conformance venue's read-back lists open orders only, as cTrader's reconcile does."""
    reading = node.account.read_back

    def read_back() -> Result[ReadBack]:
        read = reading()
        if is_refusal(read):
            return read
        orders = tuple(o for o in read.value.orders if o.state is OrderState.OPEN)
        return Ok(ReadBack(orders, read.value.positions))

    node.account.read_back = read_back  # type: ignore[method-assign]


def first_entry(node: Rig) -> str:
    tags = node.account.received[0].tags
    assert tags is not None
    return tags.client_order_id


def entries(node: Rig) -> list[str]:
    return [t.tags.client_order_id for t in node.account.received if t.tags is not None]


def test_a_filled_entry_the_read_back_does_not_list_is_found_by_its_label_and_killed(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    node.account.lose_answers = 1
    pending_only(node)
    play(node, FIRST_SEND + 2 * BAR + 1)
    name = first_entry(node)
    killed = node.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    play(node, FIRST_SEND + 4 * BAR + 1, start=FIRST_SEND + 2 * BAR + 1)
    reconciled = node_rows(node, "reconcile")
    closes = [t for t in node.account.received if t.command.kind is CommandKind.CLOSE_POSITION]

    assert [(r["why"], r["resolved"]) for r in reconciled][:2] == [
        ("start", []),
        ("unknown", [{"client_order_id": name, "outcome": "filled", "price": "1.06858"}]),
    ]
    positions = cast("list[dict[str, object]]", reconciled[1]["positions"])
    assert [(p["position"], p["claim"], p["quantity"]) for p in positions] == [
        (name, "mine", "1.61")
    ]
    assert value(killed) == {"level_in_force": "RED"}
    assert [(t.position, t.market_id) for t in closes] == [(name, "fx.eurusd")]
    assert node.account.positions() == {}
    assert node.runtime.alarms == []
    assert entries(node) == [name]


@dataclass
class HistoryOutOfReach(binding.FakeCTrader):
    """The fake demo broker once a position's orders are past its order-list reach: the list
    by position id answers no order, so the position shows only with its label."""

    def _on_ProtoOAOrderListByPositionIdReq(self, msg_id: str, body: dict[str, object]) -> None:
        self._say(
            "ProtoOAOrderListByPositionIdRes",
            {"ctidTraderAccountId": binding.CTID, "order": [], "hasMore": False},
            msg_id,
        )


def test_a_ctrader_position_found_by_label_keeps_its_position_id_and_the_kill_closes_it(
    tmp_path: Path,
) -> None:
    broker = HistoryOutOfReach(binding.codec())
    rig = binding.bound_rig(tmp_path, broker=broker)
    binding.signed_in(rig)
    binding.bind(rig)
    broker.lose_answers = 1
    binding.deploy_dummy(rig)
    at = binding.play_until_sent(rig)
    name = binding.sent_entries(rig)[0]
    binding.play_spots(rig, at, at + BAR)
    killed = rig.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    binding.play_spots(rig, at + BAR, at + 2 * BAR)
    reconciled = binding.node_rows(rig, "reconcile")

    assert [(r["why"], r["resolved"]) for r in reconciled][:2] == [
        ("start", []),
        (
            "unknown",
            [
                {
                    "client_order_id": name,
                    "outcome": "filled",
                    "price": "1.06858",
                    "position": "9001",
                }
            ],
        ),
    ]
    assert reconciled[1]["positions"] == [{**binding.FIRST_ENTRY_ROW, "position": "9001"}]
    assert value(killed) == {"level_in_force": "RED"}
    assert binding.closes(rig) == [
        {"ctidTraderAccountId": "4401", "positionId": "9001", "volume": "400000"}
    ]
    assert binding.sent_entries(rig) == [name]
    assert broker.held == {}
    assert binding.runtime(rig).alarms == []
    binding.runtime(rig).stop()


def test_a_ctrader_position_found_by_label_still_reads_as_the_node_own_after_a_reconnect(
    tmp_path: Path,
) -> None:
    broker = HistoryOutOfReach(binding.codec())
    rig = binding.bound_rig(tmp_path, broker=broker)
    binding.signed_in(rig)
    binding.bind(rig)
    broker.lose_answers = 1
    binding.deploy_dummy(rig)
    at = binding.play_until_sent(rig)
    binding.play_spots(rig, at, at + BAR)
    feed = next(iter(binding.runtime(rig).venues.values())).feed
    feed._drop("the session closed")  # pyright: ignore[reportPrivateUsage]
    binding.play_spots(rig, at + BAR, at + 3 * BAR)
    reconciled = binding.node_rows(rig, "reconcile")

    assert feed.reconnects == 1
    assert [(r["why"], r.get("stand_down")) for r in reconciled] == [
        ("start", None),
        ("unknown", None),
        ("reconnect", None),
    ]
    assert reconciled[2]["positions"] == [{**binding.FIRST_ENTRY_ROW, "position": "9001"}]
    assert binding.runtime(rig).alarms == []
    binding.runtime(rig).stop()


def test_two_positions_with_the_order_label_keep_it_unknown_with_an_alarm_and_send_nothing(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    node.account.lose_answers = 1
    pending_only(node)
    play(node, FIRST_SEND + 1)
    name = first_entry(node)
    node.account.opened_elsewhere(
        VenueOrder(None, LABEL, "fx.eurusd", OrderState.FILLED, "pos-77", Decimal("1.06860")),
        VenuePosition(
            "pos-77",
            LABEL,
            "fx.eurusd",
            "short",
            Decimal("1.72"),
            Decimal("1.06860"),
            Decimal("1.06900"),
        ),
    )
    play(node, LIVE_FROM + 2 * DAY, start=FIRST_SEND + 1)
    reconciled = node_rows(node, "reconcile")

    assert [r["resolved"] for r in reconciled][:2] == [[], []]
    assert {
        "alarm": "label_twice",
        "client_order_id": name,
        "positions": [name, "pos-77"],
        "action": "no_new_entries",
        "why": "more than one open position carries the label of an order whose answer was"
        " lost, so the node cannot tell which one it opened",
    } in node.runtime.alarms
    assert entries(node) == [name]


def test_an_entry_with_no_labelled_position_reads_absent_and_its_market_trades_again(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    pending_only(node)
    sending = node.account.send
    lost = [1]

    def send(ticket: Ticket) -> Result[Sent]:
        if ticket.tags is not None and lost[0] > 0:
            lost[0] -= 1
            node.account.received.append(ticket)
            return Ok(Sent(SubmissionOutcome.UNKNOWN))
        return sending(ticket)

    node.account.send = send  # type: ignore[method-assign]
    play(node, LIVE_FROM + 2 * DAY)
    name = first_entry(node)
    later = [t.market_id for t in node.account.received[1:] if t.tags is not None]

    assert [r["resolved"] for r in node_rows(node, "reconcile")][:2] == [
        [],
        [{"client_order_id": name, "outcome": "absent"}],
    ]
    assert entries(node).count(name) == 1
    assert later == ["fx.eurusd", "fx.eurusd"]
