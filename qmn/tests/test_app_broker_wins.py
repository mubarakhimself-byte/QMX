"""The broker wins over the node's memory (R20, wall check W8 and the closed half of W9).

Everything between the node and the fake is real: the runtime, the reconciler, the unit's journal
and :class:`~qmn.venue.ctrader_account.CTraderVenue` over the pinned definitions. The fake loses
what it says while the socket is cut, and holds only the fields the definitions pin.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

import test_app_binding as b
import test_app_runtime as base
from qmb.host.unit_handler import FillKind
from qmn.app.runtime import Runtime, VenueClose
from qmn.app.store import Json
from qmn.venue.ctrader_account import CTraderVenue

BAR = b.BAR
TAG = base.TAG
ENTRY_WINDOW = 60 * BAR
"""Bars enough for the dummy's next entry after its first trade ends."""


def trading(root: Path, fake: b.FakeCTrader | None = None) -> tuple[b.Bound, Runtime, int]:
    """The dummy with its first entry filled and booked; the next bar's time."""
    rig = b.bound_rig(root, broker=fake)
    b.signed_in(rig)
    b.bind(rig)
    runtime = b.deploy_dummy(rig)
    at = b.play_until_sent(rig)
    b.play_spots(rig, at, at + BAR)
    return rig, runtime, at + BAR


def venue_of(runtime: Runtime) -> CTraderVenue:
    return cast(CTraderVenue, runtime.venues[b.ACCOUNT].client)


def unit_rows(rig: b.Bound, kind: str) -> list[dict[str, Json]]:
    rows = cast(
        "list[dict[str, Json]]",
        b.value(rig.node.call("journal_tail", {"streams": ["unit"]}))["rows"],
    )
    return [cast("dict[str, Json]", row["body"]) for row in rows if row["kind"] == kind]


def closed_rows(rig: b.Bound) -> list[dict[str, Json]]:
    return [row for row in b.node_rows(rig, "order") if row["step"] == "closed"]


def entries(rig: b.Bound) -> int:
    return rig.fake.requests().count("ProtoOANewOrderReq")


def safe_to_restart(rig: b.Bound) -> Json:
    return cast("dict[str, Json]", b.value(rig.node.call("status", {}))["safe_to_restart"])["ok"]


def fire_the_stop(rig: b.Bound) -> None:
    for held in list(rig.fake.held.values()):
        rig.fake.fire_stop(held)


def restarted(rig: b.Bound, root: Path) -> b.Bound:
    again = b.bound_rig(root, grant=rig.grants.held, broker=rig.fake, at=rig.now[0])
    b.compiled(b.runtime(again))
    return again


def test_a_stop_fired_while_down_books_at_the_brokers_price(tmp_path: Path) -> None:
    rig, runtime, at = trading(tmp_path, b.FakeCTrader(b.codec(), stop_slip=Decimal("0.00010")))
    name = b.sent_entries(rig)[0]
    before = entries(rig)

    rig.fake.drop_socket()
    rig.fake.refuse_sockets = 2
    fire_the_stop(rig)
    b.play_spots(rig, at, at + 8 * BAR)
    closed = venue_of(runtime).closed(name)
    trades = unit_rows(rig, "trade")
    safe = safe_to_restart(rig)
    b.play_spots(rig, at + 8 * BAR, at + ENTRY_WINDOW)

    assert closed == VenueClose(FillKind.STOP, Decimal("1.08032"), gap=True)
    assert [(t["trade_id"], t["exit_kind"], t["exit_price"]) for t in trades] == [
        (name, "stop", "1.08032")
    ]
    assert safe is True
    assert entries(rig) - before == 2
    assert runtime.alarms == []
    runtime.stop()


def test_the_brokers_rate_limit_waits_for_the_true_price(tmp_path: Path) -> None:
    fake = b.FakeCTrader(b.codec(), stop_slip=Decimal("0.00010"), history_limits=1)
    rig, runtime, at = trading(tmp_path, fake)
    name = b.sent_entries(rig)[0]

    fake.drop_socket()
    fire_the_stop(rig)
    b.play_spots(rig, at, at + 5 * BAR)

    assert venue_of(runtime).closed(name) == VenueClose(FillKind.STOP, Decimal("1.08032"), gap=True)
    assert fake.requests().count("ProtoOADealListByPositionIdReq") == 2
    assert runtime.alarms == []
    runtime.stop()


def test_the_reconcile_row_writes_the_brokers_stop_and_size(tmp_path: Path) -> None:
    rig, runtime, at = trading(tmp_path)
    name = b.sent_entries(rig)[0]
    held = next(iter(rig.fake.held.values()))

    rig.fake.drop_socket()
    held.stop = Decimal("1.07522")
    held.volume //= 2
    b.play_spots(rig, at, at + 2 * BAR)
    row = b.node_rows(rig, "reconcile")[-1]

    assert venue_of(runtime).stop_of(name) == Decimal("1.07522")
    assert row["why"] == "reconnect"
    assert row["positions"] == [
        {**b.FIRST_ENTRY_ROW, "position": name, "venue_stop": "1.07522", "quantity": "0.02"}
    ]
    runtime.stop()


def test_a_stop_moved_by_hand_is_read(tmp_path: Path) -> None:
    rig, runtime, at = trading(tmp_path)
    name = b.sent_entries(rig)[0]
    held = next(iter(rig.fake.held.values()))

    rig.fake.move_stop(held, Decimal("1.08122"))
    b.tick_quotes(rig, 2)
    moved = venue_of(runtime).stop_of(name)
    shown = cast("list[dict[str, Json]]", rig.node.call("positions", {})["value"])

    rig.fake.move_stop(held, None)
    b.tick_quotes(rig, 2)
    kept = venue_of(runtime).stop_of(name)

    rig.fake.drop_socket()
    b.play_spots(rig, at, at + 2 * BAR)
    cleared = venue_of(runtime).stop_of(name)
    row = cast("list[dict[str, Json]]", b.node_rows(rig, "reconcile")[-1]["positions"])[0]

    assert moved == Decimal("1.08122")
    assert [p["stop_at_venue"] for p in shown] == ["1.08122"]
    assert kept == Decimal("1.08122")
    assert cleared == Decimal("1.08022")
    assert rig.fake.amended == [{"stopLoss": Decimal("1.08022")}]
    assert "venue_stop" not in row
    assert runtime.alarms == []
    runtime.stop()


def test_a_stop_on_a_later_event_protects_with_no_amend(tmp_path: Path) -> None:
    rig, runtime, _ = trading(tmp_path, b.FakeCTrader(b.codec(), stop_on_later_event=True))
    name = b.sent_entries(rig)[0]

    assert venue_of(runtime).stop_of(name) == Decimal("1.08022")
    assert rig.fake.requests().count("ProtoOAAmendPositionSLTPReq") == 0
    assert b.closes(rig) == []
    assert runtime.alarms == []
    runtime.stop()


def test_a_stop_fired_while_the_process_was_down_writes_the_missing_close(tmp_path: Path) -> None:
    rig, _, at = trading(tmp_path, b.FakeCTrader(b.codec(), stop_slip=Decimal("0.00010")))
    name = b.sent_entries(rig)[0]
    rig.node.stop()
    rig.fake.drop_socket()
    fire_the_stop(rig)

    first = restarted(rig, tmp_path)
    b.tick_quotes(first, 3)
    alarms = list(b.runtime(first).alarms)
    rows = closed_rows(first)
    asked = first.fake.requests().count("ProtoOADealListByPositionIdReq")
    first.node.stop()

    again = restarted(first, tmp_path)
    b.tick_quotes(again, 3)
    second_alarms = list(b.runtime(again).alarms)
    b.play_spots(again, at, at + 2 * BAR)
    trades = unit_rows(again, "trade")
    safe = safe_to_restart(again)
    body = next(body for n, body in again.fake.received if n == "ProtoOADealListByPositionIdReq")

    assert alarms == [
        {
            "alarm": "closed_while_down",
            "position": name,
            "market_id": "fx.eurusd",
            "exit": "stop",
            "price": "1.08032",
            "guessed": False,
            "why": "the broker closed this position while the node was not running",
        }
    ]
    assert [
        (r["client_order_id"], r["price"], r["exit"], r["gap"], r["guessed"]) for r in rows
    ] == [(name, "1.08032", "stop", True, False)]
    assert body == {"ctidTraderAccountId": "4401", "positionId": "9001"}
    assert asked == 1
    assert second_alarms == []
    assert again.fake.requests().count("ProtoOADealListByPositionIdReq") == 1
    assert closed_rows(again) == rows
    assert [(t["trade_id"], t["exit_kind"], t["exit_price"]) for t in trades] == [
        (name, "stop", "1.08032")
    ]
    assert safe is True
    b.runtime(again).stop()


def test_a_resolved_unknown_finds_its_close_over_the_sends_window(tmp_path: Path) -> None:
    rig = b.bound_rig(tmp_path)
    b.signed_in(rig)
    b.bind(rig)
    rig.fake.lose_answers = 1
    b.deploy_dummy(rig)
    at = b.play_until_sent(rig)
    b.play_spots(rig, at, at + BAR)
    name = b.sent_entries(rig)[0]
    rig.node.stop()
    rig.fake.drop_socket()
    fire_the_stop(rig)

    again = restarted(rig, tmp_path)
    b.play_spots(again, at + BAR, at + 5 * BAR)
    filled = [r for r in b.node_rows(again, "order") if r["step"] == "filled"]
    trades = unit_rows(again, "trade")

    assert filled == []
    assert "ProtoOADealListReq" in again.fake.requests()
    assert [(a["alarm"], a["price"], a["guessed"]) for a in b.runtime(again).alarms] == [
        ("closed_while_down", "1.08022", False)
    ]
    assert [(t["trade_id"], t["exit_kind"], t["exit_price"]) for t in trades] == [
        (name, "stop", "1.08022")
    ]
    b.runtime(again).stop()


def test_old_stop_outs_and_a_paper_send_stay_quiet_at_a_restart(tmp_path: Path) -> None:
    rig, runtime, at = trading(tmp_path)
    paper = base.deployment(rig.data, "dep-2")
    paper["lane"] = "paper"
    assert b.value(rig.node.call("deploy", {"op_id": "op-paper", "deployment": paper}))
    while runtime.hosted.get("dep-2") is None or runtime.hosted["dep-2"].unit is None:
        runtime.tick()

    live = set(b.sent_entries(rig))
    played = at
    while len([t for t in unit_rows(rig, "trade") if t["trade_id"] in live]) < 2:
        assert played < at + 2 * base.DAY, "the dummy did not stop out twice"
        fire_the_stop(rig)
        b.play_spots(rig, played, played + BAR)
        played += BAR
        live = set(b.sent_entries(rig))
    papers = [
        row
        for row in b.node_rows(rig, "order")
        if row["step"] == "send" and row["deployment_id"] == "dep-2"
    ]
    held_at_restart = len(rig.fake.held)
    rows = len(b.node_rows(rig, "order"))
    rig.node.stop()

    again = restarted(rig, tmp_path)
    b.tick_quotes(again, 3)
    asked = {
        "ProtoOADealListByPositionIdReq": again.fake.requests().count(
            "ProtoOADealListByPositionIdReq"
        ),
        "ProtoOADealListReq": again.fake.requests().count("ProtoOADealListReq"),
    }

    assert len(papers) >= 1
    assert [t["exit_kind"] for t in unit_rows(again, "trade")] == ["stop", "stop"]
    assert held_at_restart == 0
    assert b.runtime(again).alarms == []
    assert asked == {"ProtoOADealListByPositionIdReq": 0, "ProtoOADealListReq": 0}
    assert closed_rows(again) == []
    assert len(b.node_rows(again, "order")) == rows
    b.runtime(again).stop()


class HoldsNoStop(b.FakeCTrader):
    def _on_ProtoOAAmendPositionSLTPReq(self, msg_id: str, body: dict[str, object]) -> None:
        del body
        self._order_error(msg_id, "TRADING_BAD_STOPS")


def test_an_entry_the_node_closed_for_protection_stays_quiet_at_a_restart(tmp_path: Path) -> None:
    rig, runtime, _ = trading(tmp_path, HoldsNoStop(b.codec(), holds_stops=False))
    name = b.sent_entries(rig)[0]
    rows = [r["event_id"] for r in closed_rows(rig)]
    raised = [a["alarm"] for a in runtime.alarms]
    rig.node.stop()

    again = restarted(rig, tmp_path)
    b.tick_quotes(again, 3)

    assert rows[:1] == [f"{name}/closed-protection"]
    assert raised[0] == "protection_escalation"
    assert b.runtime(again).alarms == []
    assert "ProtoOADealListByPositionIdReq" not in again.fake.requests()
    b.runtime(again).stop()


def test_history_silent_closes_at_the_held_stop_with_a_guess_alarm(tmp_path: Path) -> None:
    rig, runtime, at = trading(
        tmp_path, b.FakeCTrader(b.codec(), stop_slip=Decimal("0.00010"), history_silent=True)
    )
    name = b.sent_entries(rig)[0]
    held = next(iter(rig.fake.held.values()))
    guess = {
        "alarm": "close_price_guess",
        "position": name,
        "market_id": "fx.eurusd",
        "price": "1.08022",
        "why": "the broker no longer lists this position and its history named no closing deal,"
        " so the node reads it closed at the stop it held, and that price is a guess",
    }

    rig.fake.drop_socket()
    fire_the_stop(rig)
    sent = len(rig.fake.requests())
    b.play_spots(rig, at, at + 5 * BAR)
    asked = [
        r
        for r in rig.fake.requests()[sent:]
        if r in {"ProtoOAReconcileReq", "ProtoOADealListByPositionIdReq"}
    ]
    closed = venue_of(runtime).closed(name)
    alarms = list(runtime.alarms)
    trades = unit_rows(rig, "trade")

    rig.fake.drop_socket()
    rig.fake.held[held.position_id] = held
    b.play_spots(rig, at + 5 * BAR, at + 7 * BAR)
    listed_closed = venue_of(runtime).closed(name)

    assert alarms == [guess]
    assert asked == ["ProtoOAReconcileReq", "ProtoOADealListByPositionIdReq", "ProtoOAReconcileReq"]
    assert closed == VenueClose(FillKind.STOP, Decimal("1.08022"), guessed=True)
    assert [t["exit_price"] for t in trades] == ["1.08022"]
    assert listed_closed is None
    assert venue_of(runtime).held()[name][1] == held.position_id
    assert runtime.alarms == [
        guess,
        {
            "alarm": "close_undone",
            "position": name,
            "market_id": "fx.eurusd",
            "why": "the broker lists this position again after the node read it closed, so the"
            " node holds it again and any trade row it booked for it is wrong",
        },
    ]
    runtime.stop()


def test_a_send_with_no_stop_is_skipped_not_a_keyerror(tmp_path: Path) -> None:
    fake = b.FakeCTrader(b.codec(), close_error="INVALID_REQUEST")
    rig = b.bound_rig(tmp_path, broker=fake)
    b.signed_in(rig)
    b.bind(rig)
    b.tick_quotes(rig)
    rig.node.call("self_test", {"op_id": "test-1", "account": b.ACCOUNT})
    b.tick_quotes(rig, 1)
    name = str(
        next(body["clientOrderId"] for n, body in fake.received if n == "ProtoOANewOrderReq")
    )

    fake.drop_socket()
    for _ in range(3):
        b.tick_quotes(rig, 1)
    row = cast("list[dict[str, Json]]", b.node_rows(rig, "reconcile")[-1]["positions"])

    assert list(fake.held)
    assert row == [
        {
            "position": name,
            "claim": "mine",
            "tags": [TAG],
            "market_id": "fx.eurusd",
            "side": "long",
            "quantity": "0.01",
            "fill_price": "1.08012",
            "venue_stop": "1.07512",
        }
    ]
    assert b.runtime(rig).healer.healing is None
    b.runtime(rig).stop()
