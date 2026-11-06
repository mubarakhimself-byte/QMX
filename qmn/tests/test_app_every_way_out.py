"""Every way out acts (R21, wall checks W9 and W10).

RED and flatten close what this node opened and nothing else, a refused exit keeps going, and a
position with no stop gets it back or is closed with an alarm. Everything between the node and
the fake is real, as in :mod:`test_app_broker_wins`.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
import test_app_binding as b
import test_app_runtime as base
from qmb.runloop import RestingIntent
from qmf.core import Instant, RefusalCategory, Retryability, TypedRefusal
from qmf.venue.commands import CommandKind
from qml.unit.model import Side
from qmn.app import runtime as node_runtime
from qmn.app.attribution import OrderState, VenueOrder, VenuePosition
from qmn.app.runtime import Blocked, NodeUnit, Placed
from qmn.app.store import Json
from test_app_broker_wins import BAR, ENTRY_WINDOW, entries, restarted, trading, unit_rows
from test_protection_every_order import node_rows, refusing
from test_protection_every_order import trading as on_conformance

PAST_ENTRY = "the new stop is past entry, not on the loss side, so the node did not send it"
"""Its words hold "not on the loss side", which the run journal's list codes stop_wrong_side."""


def hand_opened(position_id: int = 7777) -> b.Held:
    """A position he opened himself in cTrader: no label, no client order id, no stop."""
    return b.Held(position_id, 1, "BUY", 100_000, Decimal("1.06000"), None, "", "")


def unit_of(rig: b.Bound) -> NodeUnit:
    unit = b.runtime(rig).hosted["dep-1"].unit
    assert unit is not None
    return unit


def flatten_rows(rig: b.Bound) -> list[dict[str, Json]]:
    return [row for row in b.node_rows(rig, "kill_level") if "level" not in row]


def protection_rows(rig: b.Bound) -> list[dict[str, Json]]:
    return b.node_rows(rig, "protection")


def stopped(rig: b.Bound) -> None:
    b.runtime(rig).stop()


def test_red_closes_a_position_no_unit_holds(tmp_path: Path) -> None:
    rig, runtime, _ = trading(tmp_path)
    rig.fake.held[7777] = hand_opened()
    runtime.stop()

    again = b.bound_rig(tmp_path, grant=rig.grants.held, broker=rig.fake, at=rig.now[0])
    b.runtime(again).compile = lambda _d, _f: "the unit did not compile: a block changed"
    b.tick_quotes(again, 4)
    phase = b.runtime(again).hosted["dep-1"].phase.value
    killed = again.node.call("kill", {"op_id": "op-red", "level": "RED", "scope": "all"})
    b.tick_quotes(again, 3)

    assert phase == "refused"
    assert b.value(killed) == {"level_in_force": "RED"}
    assert list(rig.fake.held) == [7777]
    assert [(r["scope"], r["positions_closed"]) for r in b.node_rows(again, "kill_level")] == [
        ("all", 1)
    ]
    assert [alarm["alarm"] for alarm in b.runtime(again).alarms] == ["not_ours"]
    stopped(again)


@pytest.mark.parametrize("read_refused", [False, True], ids=["read", "read-refused"])
def test_flatten_closes_and_a_restart_replays_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, read_refused: bool
) -> None:
    rig, runtime, at = trading(tmp_path)
    name = b.sent_entries(rig)[0]
    before = entries(rig)

    answer = rig.node.call("flatten", {"op_id": "op-flat", "scope": "all"})
    b.play_spots(rig, at, at + BAR)
    flat = dict(rig.fake.held)
    done = flatten_rows(rig)
    booked = [(t["trade_id"], t["exit_kind"]) for t in unit_rows(rig, "trade")]
    b.play_spots(rig, at + BAR, at + ENTRY_WINDOW)
    entered_again = entries(rig) - before
    new_positions = list(rig.fake.held)
    closes = len(b.closes(rig))
    runtime.stop()

    assert b.value(answer) == {"state": "accepted", "positions": 1}
    assert flat == {}
    assert done == [{"op_id": "op-flat", "scope": "all", "positions_closed": 1}]
    assert booked == [(name, "close")]
    assert entered_again >= 1
    assert new_positions != []

    if read_refused:

        def refuse(_folder: Path) -> TypedRefusal:
            return TypedRefusal(
                category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                retryability=Retryability.NO,
                context={"field": "journal", "reason": "the volume refused the read"},
            )

        monkeypatch.setattr(node_runtime, "read_committed", refuse)
    again = restarted(rig, tmp_path)
    b.tick_quotes(again, 2, bid="1.06000", ask="1.06012")

    assert list(rig.fake.held) == new_positions
    assert len(b.closes(again)) == closes
    monkeypatch.undo()
    b.tick_quotes(again, 2, bid="1.06000", ask="1.06012")

    assert list(rig.fake.held) == new_positions
    assert len(b.closes(again)) == closes
    assert flatten_rows(again) == done
    stopped(again)


def test_a_flatten_held_across_a_restart_with_the_session_down_waits_and_ends_flat(
    tmp_path: Path,
) -> None:
    rig, runtime, at = trading(tmp_path)
    rig.fake.drop_socket()
    rig.fake.refuse_sockets = 1000
    b.play_spots(rig, at, at + BAR)
    answer = rig.node.call("flatten", {"op_id": "op-flat", "scope": "all"})
    b.play_spots(rig, at + BAR, at + 2 * BAR)
    held_while_down = len(rig.fake.held)
    runtime.stop()

    again = b.bound_rig(tmp_path, grant=rig.grants.held, broker=rig.fake, at=rig.now[0])
    b.compiled(b.runtime(again))
    b.play_spots(again, at + 2 * BAR, at + 3 * BAR)
    rows_while_down = flatten_rows(again)
    rig.fake.refuse_sockets = 0
    b.play_spots(again, at + 3 * BAR, at + 6 * BAR)

    assert b.value(answer) == {"state": "accepted", "positions": 1}
    assert held_while_down == 1
    assert rows_while_down == []
    assert rig.fake.held == {}
    assert flatten_rows(again) == [{"op_id": "op-flat", "scope": "all", "positions_closed": 1}]
    stopped(again)


def test_a_refused_exit_keeps_going_and_books_the_trade(tmp_path: Path) -> None:
    node = on_conformance(tmp_path)
    refusing(node, [1])
    base.play(node, base.LIVE_FROM + 2 * base.DAY)
    closes = [t for t in node.account.received if t.command.kind is CommandKind.CLOSE_POSITION]

    assert len(closes) == 2
    assert node.account.positions() == {}
    assert [(t["exit_kind"], t["quantity"]) for t in base.unit_rows(node, "trade")] == [
        ("stop", "1.72"),
        ("stop", "1.08"),
        ("close", "0.75"),
    ]
    assert [t.reference for t in closes] == [Decimal("1.06856"), Decimal("1.06856")]
    node.runtime.stop()


def test_a_blocked_stop_move_leaves_the_position_open(tmp_path: Path) -> None:
    node = on_conformance(tmp_path)
    base.play(node, 1_742_508_000_000_000_000 + 900_000_000_001)
    unit = node.runtime.hosted["dep-1"].unit
    assert unit is not None and unit.handler is not None
    held = unit.handler.open_positions["fx.eurusd"]
    name = unit.venue_name(held.position_id)
    level = held.entry_price - Decimal("0.00058")
    wire: dict[str, object] = {
        "contract_format_version": 3,
        "intent_family": "exit",
        "kind": "amend_protection",
        "position_ref": {
            "position_id": held.position_id,
            "instrument": {"venue": "icmarkets-ctrader", "symbol": "EURUSD"},
            "opened_by": held.opened_by.value,
        },
        "reason_code": {"code": "trail", "book_family": "unit"},
        "decision_row_id": "row-past",
        "stop": str(level),
        "targets": [],
    }
    intent = RestingIntent.try_create("exit:row-past", "fx.eurusd", order=wire)
    assert not isinstance(intent, TypedRefusal), intent
    stop_before = node.account.stop_of(name)

    answer = unit.place(intent.value, Instant(base.LIVE_FROM))
    node.runtime.tick()
    node.runtime.tick()
    sent = [t.command.kind for t in node.account.received]

    assert answer == Blocked(PAST_ENTRY)
    assert sent == [CommandKind.PLACE_ORDER]
    assert node.account.stop_of(name) == stop_before
    assert [r["step"] for r in node_rows(node, "order")][-1] == "amend_blocked"
    node.runtime.stop()


def test_a_restart_puts_a_missing_stop_back_before_any_entry(tmp_path: Path) -> None:
    rig, runtime, _ = trading(tmp_path)
    runtime.stop()
    held = next(iter(rig.fake.held.values()))
    wanted = cast(Decimal, held.stop)
    held.stop = None
    before = len(rig.fake.received)

    again = restarted(rig, tmp_path)
    b.tick_quotes(again, 2, bid=str(held.price), ask=str(held.price + Decimal("0.00012")))
    sent = [name for name, _ in rig.fake.received[before:]]

    assert wanted == Decimal("1.08022")
    assert held.stop == Decimal("1.08022")
    assert rig.fake.amended == [{"stopLoss": Decimal("1.08022")}]
    assert "ProtoOANewOrderReq" not in sent
    assert "ProtoOAClosePositionReq" not in sent
    assert b.runtime(again).alarms == []
    stopped(again)


def test_a_stop_it_cannot_put_back_closes_with_an_alarm(tmp_path: Path) -> None:
    rig, runtime, _ = trading(tmp_path)
    name = b.sent_entries(rig)[0]
    runtime.stop()
    held = next(iter(rig.fake.held.values()))
    past = cast(Decimal, held.stop) + Decimal("0.001")
    held.stop = None

    again = b.bound_rig(tmp_path, grant=rig.grants.held, broker=rig.fake, at=rig.now[0])
    rig.fake.quote("EURUSD", past, past + Decimal("0.00012"), again.now[0] // 1_000_000)
    b.compiled(b.runtime(again))
    b.tick_quotes(again, 3, bid=str(past), ask=str(past + Decimal("0.00012")))

    assert rig.fake.held == {}
    assert rig.fake.amended == []
    assert b.sent_entries(again) == [name]
    assert protection_rows(again) == [
        {
            "alarm": "protection_escalation",
            "position": name,
            "market_id": "fx.eurusd",
            "tries": 1,
            "action": "closed_reduce_only",
            "origin": "placeholder",
        }
    ]
    stopped(again)


def test_a_stop_lost_across_a_reconnect_is_put_back(tmp_path: Path) -> None:
    rig, runtime, at = trading(tmp_path)
    name = b.sent_entries(rig)[0]
    held = next(iter(rig.fake.held.values()))

    rig.fake.drop_socket()
    held.stop = None
    b.play_spots(rig, at, at + 2 * BAR)

    assert held.stop == Decimal("1.08022")
    assert rig.fake.amended == [{"stopLoss": Decimal("1.08022")}]
    assert list(cast("dict[int, b.Held]", rig.fake.held)) == [held.position_id]
    assert unit_of(rig).orders.venue.client.stop_of(name) == Decimal("1.08022")
    assert runtime.alarms == []
    runtime.stop()


class LandsElsewhere(b.FakeCTrader):
    """A broker that holds an accepted stop at another level than the one it was sent."""

    landing: Decimal | None = None

    def _on_ProtoOAAmendPositionSLTPReq(self, msg_id: str, body: dict[str, object]) -> None:
        landed = body if self.landing is None else {**body, "stopLoss": float(self.landing)}
        super()._on_ProtoOAAmendPositionSLTPReq(msg_id, landed)


def test_amend_answers_the_brokers_stop_and_a_past_entry_stop_is_blocked_with_its_row(
    tmp_path: Path,
) -> None:
    fake = LandsElsewhere(b.codec())
    rig, runtime, _ = trading(tmp_path / "ctrader", fake)
    name = b.sent_entries(rig)[0]
    unit = unit_of(rig)
    market, side, entry = unit.venue_open()[name]
    start = cast(Decimal, unit.orders.venue.client.stop_of(name))
    b.tick_quotes(rig, 1, bid="1.06700", ask="1.06712")
    record = unit.records[market]

    rounded = unit.orders.amend(name, market, side, Decimal("1.069164"), entry, start, record)
    quiet = list(runtime.alarms)
    fake.landing = Decimal("1.06900")
    moved = unit.orders.amend(name, market, side, Decimal("1.06880"), entry, start, record)

    assert (side, entry, start) == (Side.SHORT, Decimal("1.06858"), Decimal("1.08022"))
    assert rounded == Placed(Decimal("1.06916"))
    assert quiet == []
    assert moved == Placed(Decimal("1.06900"))
    assert protection_rows(rig) == [
        {
            "alarm": "stop_differs",
            "position": name,
            "market_id": "fx.eurusd",
            "asked": "1.06880",
            "at_broker": "1.06900",
            "action": "answered_the_brokers_stop",
        }
    ]
    runtime.stop()

    node = on_conformance(tmp_path / "conformance")
    label = "qmx:a4dqobyh:dummy-trend-pullback"
    position = VenuePosition(
        "long-1", label, "fx.eurusd", "long", Decimal("1"), Decimal("1.1000"), Decimal("1.0900")
    )
    order = VenueOrder("long-1", label, "fx.eurusd", OrderState.FILLED, "long-1", Decimal("1.1000"))
    node.account.opened_elsewhere(order, position)
    placed = node.runtime.hosted["dep-1"].unit
    assert placed is not None

    blocked = placed.orders.amend(
        "long-1",
        "fx.eurusd",
        Side.LONG,
        Decimal("1.1020"),
        Decimal("1.1000"),
        Decimal("1.0900"),
        placed.records["fx.eurusd"],
    )

    assert blocked == Blocked(PAST_ENTRY)
    assert node.account.stop_of("long-1") == Decimal("1.0900")
    assert node.account.received == []
    assert [
        (r["step"], r["stop"], r["reason"])
        for r in node_rows(node, "order")
        if r["client_order_id"] == "long-1"
    ] == [("amend_blocked", "1.1020", PAST_ENTRY)]
    node.runtime.stop()
