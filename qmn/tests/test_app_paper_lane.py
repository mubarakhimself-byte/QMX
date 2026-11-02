"""A paper deployment sends no order and journals its trades with world ``paper`` (AD-39).

The rig is C-12a's: a node on a throwaway folder with one binding on the conformance venue, a
fake that never reaches a broker. The dummy is deployed on the paper lane and fed the same
recorded days its live lane trades in C-12a's tests.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
import test_app_runtime
from qmb.host.unit_handler import FillKind
from qmf.core import Account, AccountRole, VenueId
from qmf.venue.commands import CommandKind
from qmn.app.paper_lane import PaperAccount
from qmn.app.runtime import NodeUnit
from qmn.app.store import Json
from test_app_runtime import DAY, LIVE_FROM, deploy, deployment, play, rig, settle, value
from test_app_stand_down import CASES, Case, Probes, at, played


def rows(node_call: dict[str, Json], kind: str) -> list[dict[str, object]]:
    found = cast("list[dict[str, object]]", value(node_call)["rows"])
    return [row for row in found if row["kind"] == kind]


def test_a_paper_deployment_sends_no_order_and_journals_its_trades_with_world_paper(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    document = deployment(node.data)
    document["lane"] = "paper"
    deploy(node, document)
    phase = settle(node)
    play(node, LIVE_FROM + 2 * DAY)
    unit = cast("NodeUnit", node.runtime.hosted["dep-1"].unit)
    paper = cast("PaperAccount", unit.orders.venue.client)
    trades = rows(node.node.call("journal_tail", {"streams": ["unit"]}), "trade")
    orders = rows(node.node.call("journal_tail", {"streams": ["node"]}), "order")

    assert phase == "trading"
    assert value(node.node.call("status", {}))["headline"] == "Trading, 1 unit"
    assert node.account.received == []
    assert [(t.command.kind, t.market_id, t.side.value, t.quantity) for t in paper.simulated] == [
        (CommandKind.PLACE_ORDER, "fx.eurusd", "short", Decimal("1.72")),
        (CommandKind.PLACE_ORDER, "fx.eurusd", "short", Decimal("1.08")),
        (CommandKind.PLACE_ORDER, "fx.eurusd", "short", Decimal("0.75")),
        (CommandKind.CLOSE_POSITION, "fx.eurusd", "short", None),
    ]
    assert [
        (row["world"], body["exit_kind"], body["quantity"])
        for row in trades
        for body in [cast("dict[str, object]", row["body"])]
    ] == [("paper", "stop", "1.72"), ("paper", "stop", "1.08"), ("paper", "close", "0.75")]
    assert {row["world"] for row in orders} == {"paper"}
    assert [
        cast("dict[str, object]", row["body"])["step"]
        for row in orders
        if cast("dict[str, object]", row["body"])["step"] in {"send", "close"}
    ] == ["send", "send", "send", "close"]
    node.runtime.stop()


@pytest.mark.parametrize(
    "role",
    [
        AccountRole.LIVE,
        AccountRole.PAPER_VALIDATION,
        AccountRole.PAPER_BENCHED,
        AccountRole.PROP_FIRM,
    ],
)
def test_a_live_lane_on_any_binding_but_demo_is_refused_and_sends_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role: AccountRole
) -> None:
    def bound(account_id: str, venue: VenueId, given: AccountRole) -> Account:
        del given
        return Account(account_id, venue, role)

    monkeypatch.setattr(test_app_runtime, "Account", bound)
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    phase = settle(node)
    play(node, LIVE_FROM + 2 * DAY)

    assert node.account.account.role is role
    assert phase == "refused"
    assert node.runtime.hosted["dep-1"].detail == (
        "a live lane trades only on a demo binding until a live one is bound"
    )
    assert node.account.received == []
    node.runtime.stop()


@pytest.mark.parametrize("case", CASES, ids=[case.kind.value for case in CASES])
def test_a_red_kill_closes_a_paper_position_under_every_stand_down_and_sends_nothing(
    tmp_path: Path, case: Case
) -> None:
    node = rig(tmp_path)
    probes = Probes()
    node.runtime.stand_downs.clock_offset_ns = lambda: probes.offset
    node.runtime.stand_downs.free_bytes = lambda: probes.free
    document = deployment(node.data)
    document["lane"] = "paper"
    deploy(node, document)
    settle(node)
    played(node, probes, at(530))
    case.enter(node, probes)
    played(node, probes, at(560))
    unit = cast("NodeUnit", node.runtime.hosted["dep-1"].unit)
    paper = cast("PaperAccount", unit.orders.venue.client)
    before = len(paper.simulated)
    killed = node.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    node.runtime.tick()
    closes = paper.simulated[before:]
    closed = [paper.closed(cast("str", ticket.position)) for ticket in closes]

    assert killed["ok"] is True
    assert [(t.command.kind, t.market_id, t.side.value) for t in closes] == [
        (CommandKind.CLOSE_POSITION, "fx.eurusd", "short")
    ]
    assert [None if c is None else c.kind for c in closed] == [FillKind.CLOSE]
    assert node.account.received == []
    node.runtime.stop()
