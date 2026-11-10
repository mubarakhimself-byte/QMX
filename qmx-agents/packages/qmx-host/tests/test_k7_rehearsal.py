"""K9 7: the walk from zero reaches paper, and the practice venue says what it is (RC-19).

Two seams, the two the section names. The first runs K7, whose venue is the fake broker because
the Library's account kind cannot hold a practice account; the second binds the practice venue to
a real node and reads every row of both its journals and both its cards.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import k7_rehearsal
import pytest
import test_feed_relay as relay
from k7_rehearsal import DAY, LIVE_FROM
from qmf.core import is_refusal
from qmn.app.feed_keeper import FeedKeeper
from qmn.app.practice import ACCOUNT, PRACTICE, SHIPPED_VENUE, Month, stated, venue
from qmn.app.runtime import Phase, Runtime
from qmn.app.server import Node, open_node

STEPS = [
    "practice_start",
    "unit_new",
    "check",
    "backtest",
    "click",
    "stage",
    "warm_up",
    "first_signal",
    "row",
    "fill",
]
"""The walk's steps, in the order SPINE section 6 gives them."""


def test_k9_7_canary_reaches_a_filled_paper_entry(tmp_path: Path) -> None:
    found = k7_rehearsal.run(tmp_path / "QMX")

    assert [step.name for step in found.steps] == STEPS
    assert found.decision is not None
    assert len(found.fills) == 1
    fill = found.fills[0]
    steps = cast("Mapping[str, Mapping[str, object]]", found.decision["steps"])
    assert found.decision["written_before_send"] is True
    assert steps["approved"]["kind"] == "quantity"
    assert Decimal(str(steps["approved"]["value"])) == Decimal(str(fill["quantity"]))
    assert "not one of ['demo', 'live']" in found.shortfall
    """The practice account row is the Library's to widen; K7 keeps its refusal as evidence."""


def test_practice_says_it_is_practice(tmp_path: Path) -> None:
    """Every row of both journals says the practice world and kind, and so do the two cards.

    The node stream carries this binding's order rows. The unit stream carries every row of the
    deployment's own journal, which the venue must label as it labels the orders.
    """
    node, runtime, now = _practice_node(tmp_path)
    document = relay.deployment(_data(tmp_path), None)
    document["lane"] = "paper"
    document["account"] = {"id": ACCOUNT, "version": 1, "fingerprint": None}
    answer = node.call("deploy", {"op_id": "op-practice-1", "deployment": document})
    assert answer["ok"] is True, answer
    _settle(runtime, "dep-1")
    _play(node, runtime, now)
    orders = [row for row in _rows(node, "node") if row["kind"] == "order"]
    unit_rows = _rows(node, "unit")
    card = next(
        row
        for row in cast("list[Mapping[str, object]]", _value(node, "status")["venues"])
        if row.get("venue_kind") == PRACTICE
    )
    unit_card = cast("list[Mapping[str, object]]", _value(node, "units"))[0]

    assert len(orders) >= 2, orders
    assert {(row["world"], cast("dict[str, object]", row["body"])["world"]) for row in orders} == {
        ("paper", "paper")
    }
    assert {cast("dict[str, object]", row["body"])["venue_kind"] for row in orders} == {"practice"}
    assert unit_rows, "the practice unit wrote no journal rows"
    assert {
        (row["world"], cast("dict[str, object]", row["body"]).get("world")) for row in unit_rows
    } == {("paper", "paper")}
    assert {cast("dict[str, object]", row["body"]).get("venue_kind") for row in unit_rows} == {
        "practice"
    }
    assert (card["venue"], card["world"], card["venue_kind"]) == (
        SHIPPED_VENUE,
        "paper",
        "practice",
    )
    assert (unit_card["world"], unit_card["venue_kind"]) == ("paper", "practice")
    assert stated(object()) == {}
    """A broker's rows and cards state nothing, so no other binding reads differently."""
    runtime.stop()


def _data(root: Path) -> Path:
    return root / "QMX" / "apps" / "trading-node" / "data"


def _practice_node(root: Path) -> tuple[Node, Runtime, list[int]]:
    """A node whose one binding is the practice venue, on a throwaway folder."""
    now = [LIVE_FROM - DAY]
    made: list[FeedKeeper] = []

    def venues() -> Mapping[str, Any]:
        bound = venue(clock_ns=lambda: now[0], started_ns=LIVE_FROM - DAY)
        assert not is_refusal(bound), bound
        made.append(bound.value.feed)
        return {ACCOUNT: bound.value}

    node = open_node(
        _data(root),
        here="fp-pc-1",
        machine="pc",
        clock_ns=lambda: now[0],
        sleep=lambda seconds: now.__setitem__(0, now[0] + int(seconds * 1e9)),
        random_bytes=lambda size: b"\x07" * size,
        venues=lambda _journal, _epoch: venues(),
    )
    runtime = cast("Runtime", node.runtime)
    feed = made[0]
    feed.pump()
    assert feed.ready, feed.reason
    return node, runtime, now


def _settle(runtime: Runtime, deployment: str) -> None:
    deadline = time.monotonic() + 120
    while True:
        runtime.tick()
        hosted = runtime.hosted.get(deployment)
        if hosted is not None and hosted.phase is Phase.TRADING:
            return
        assert time.monotonic() < deadline, f"{deployment} never traded: {hosted}"
        time.sleep(0.02)


def _play(node: Node, runtime: Runtime, now: list[int]) -> None:
    """Play the shipped month's bars after the venue's history until one order row lands."""
    for at, _market, _bar in Month.ship().bars:
        if at <= LIVE_FROM:
            continue
        now[0] = at
        runtime.tick()
        if any(row["kind"] == "order" for row in _rows(node, "node")):
            return
    raise AssertionError("the practice venue wrote no order row")


def _rows(node: Node, stream: str) -> list[Mapping[str, object]]:
    answer = node.call("journal_tail", {"streams": [stream]})
    assert answer["ok"] is True, answer
    return cast("list[Mapping[str, object]]", cast("dict[str, object]", answer["value"])["rows"])


def _value(node: Node, operation: str) -> Mapping[str, object]:
    answer = node.call(operation, {})
    assert answer["ok"] is True, answer
    return cast("Mapping[str, object]", answer["value"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
