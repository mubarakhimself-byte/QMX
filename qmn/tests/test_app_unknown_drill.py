"""The network-cut drill (case TN-01, Part C slice C-12b): an answer lost after a send.

The conformance venue carries out the dummy's first entry and the answer never comes back, then
the session drops. The node marks the order UNKNOWN, sends nothing again, reads the venue's
orders and positions when the session is back, and goes on with exactly one position. On the
other path the order never reached the venue, and the node drops the entry instead of resending.
Runs against the conformance venue only.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

from qmf.core import Ok, Result
from qmf.venue.commands import CommandKind
from qmn.app.runtime import Sent, Ticket
from qmn.venue import SubmissionOutcome
from test_app_runtime import LIVE_FROM, Rig, play, unit_rows
from test_protection_every_order import FIRST_SEND, node_rows, trading

DAY = 86_400_000_000_000


def cut_and_reconnect(node: Rig) -> None:
    """The session drops on the next read, and the tick after opens it again."""
    node.source.drop()
    node.runtime.tick()
    node.runtime.tick()


def steps(node: Rig, client_order_id: str) -> list[str]:
    return [
        str(r["step"]) for r in node_rows(node, "order") if r["client_order_id"] == client_order_id
    ]


def test_a_lost_answer_is_unknown_never_resent_and_leaves_one_position(tmp_path: Path) -> None:
    node = trading(tmp_path)
    node.account.lose_answers = 1
    play(node, FIRST_SEND + 1)
    first = node.account.received[0].tags
    assert first is not None
    name = first.client_order_id
    held_while_unknown = dict(node.account.positions())
    cut_and_reconnect(node)
    held_after_reconnect = dict(node.account.positions())
    play(node, LIVE_FROM + 2 * DAY, start=FIRST_SEND + 1)
    entries = [t for t in node.account.received if t.command.kind is CommandKind.PLACE_ORDER]
    reconciled = node_rows(node, "reconcile")

    assert steps(node, name)[:2] == ["send", "unknown"]
    assert [t.tags.client_order_id for t in entries if t.tags is not None].count(name) == 1
    assert held_while_unknown == held_after_reconnect
    assert held_after_reconnect == {
        name: ("fx.eurusd", "short", Decimal("1.61"), Decimal("1.06889"))
    }
    assert node.feed.reconnects == 1
    assert [(r["why"], r["session"], r["resolved"]) for r in reconciled] == [
        ("start", 0, []),
        ("reconnect", 1, [{"client_order_id": name, "outcome": "filled", "price": "1.06858"}]),
    ]
    assert cast("list[object]", reconciled[1]["positions"]) == [
        {
            "position": name,
            "claim": "mine",
            "tags": ["a4dqobyh"],
            "market_id": "fx.eurusd",
            "side": "short",
            "quantity": "1.61",
            "fill_price": "1.06858",
            "venue_stop": "1.06889",
            "unit_stop": "1.06889",
            "stop_distance": "0.00031",
            "node_price": "1.06858",
            "slippage": "0.00000",
        }
    ]
    names = [t.tags.client_order_id for t in entries if t.tags is not None]
    trades = unit_rows(node, "trade")
    assert [t.quantity for t in entries] == [Decimal("1.61"), Decimal("1.03"), Decimal("0.72")]
    assert [(t["trade_id"], t["exit_kind"], t["quantity"]) for t in trades] == [
        (name, "stop", "1.61"),
        (names[1], "stop", "1.03"),
        (names[2], "close", "0.72"),
    ]


def test_an_order_that_never_reached_the_venue_is_dropped_and_never_resent(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    sending = node.account.send
    lost = [1]

    def send(ticket: Ticket) -> Result[Sent]:
        if ticket.tags is not None and lost[0] > 0:
            lost[0] -= 1
            node.account.received.append(ticket)
            return Ok(Sent(SubmissionOutcome.UNKNOWN))
        return sending(ticket)

    node.account.send = send  # type: ignore[method-assign]
    play(node, FIRST_SEND + 1)
    first = node.account.received[0].tags
    assert first is not None
    name = first.client_order_id
    cut_and_reconnect(node)
    held_after_reconnect = dict(node.account.positions())
    play(node, LIVE_FROM + 2 * DAY, start=FIRST_SEND + 1)
    entries = [t for t in node.account.received if t.command.kind is CommandKind.PLACE_ORDER]
    guards = unit_rows(node, "guard")

    assert held_after_reconnect == {}
    assert [t.tags.client_order_id for t in entries if t.tags is not None].count(name) == 1
    assert [r["resolved"] for r in node_rows(node, "reconcile")] == [
        [],
        [{"client_order_id": name, "outcome": "absent"}],
    ]
    assert (
        "health_stop",
        "venue answer unknown, and the venue never took the order: not sent again",
    ) in {(g["reason"], g["detail"]) for g in guards}


def test_each_reconnect_runs_one_reconcile_before_entries_go_again(tmp_path: Path) -> None:
    node = trading(tmp_path)
    play(node, FIRST_SEND)
    for _ in range(3):
        cut_and_reconnect(node)
    play(node, FIRST_SEND + 1, start=FIRST_SEND)

    assert [(r["why"], r["session"]) for r in node_rows(node, "reconcile")] == [
        ("start", 0),
        ("reconnect", 1),
        ("reconnect", 2),
        ("reconnect", 3),
    ]
    assert [t.quantity for t in node.account.received] == [Decimal("1.61")]
