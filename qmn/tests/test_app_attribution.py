"""Each position and order on an account is the node's, a twin's, another node's or nobody's
(Part C slice C-12b, Level 0 AD-8 and AD-38).

The rig is C-12a's: a node on a throwaway folder bound to one conformance account, a fake that
never reaches a broker. A record from elsewhere is put on the account before the node starts,
as his own trade or another node's would be.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

from qmf.venue.commands import CommandKind
from qmn.app.attribution import (
    Claim,
    OrderState,
    ReadBack,
    VenueOrder,
    VenuePosition,
    attribute,
)
from test_app_runtime import LIVE_FROM, Rig, deploy, deployment, play, rig, settle, unit_rows, value
from test_protection_every_order import node_rows

DAY = 86_400_000_000_000
MINE = "qa4dqobyh-01JQ00000000000000000000MN"
TWIN = "qa4dqobyh-01JQ00000000000000000000TW"
OTHER = "qbbbbbbbb-01JQ00000000000000000000FR"
LABEL = "qmx:a4dqobyh:dummy-trend-pullback"


def test_each_record_is_claimed_by_its_label_tag_and_client_order_id() -> None:
    def order(coid: str | None, label: str | None, position: str | None) -> VenueOrder:
        return VenueOrder(coid, label, "fx.eurusd", OrderState.FILLED, position, Decimal("1.08"))

    def position(name: str, label: str | None) -> VenuePosition:
        return VenuePosition(
            name, label, "fx.eurusd", "short", Decimal("1"), Decimal("1.08"), Decimal("1.09")
        )

    read = ReadBack(
        orders=(
            order(MINE, LABEL, "p-mine"),
            order(TWIN, LABEL, "p-twin"),
            order(OTHER, "qmx:bbbbbbbb:other-unit", "p-foreign"),
            order(None, None, "p-manual"),
            order(MINE.replace("MN", "MX"), "qmx:bbbbbbbb:other-unit", None),
        ),
        positions=(
            position("p-mine", LABEL),
            position("p-twin", LABEL),
            position("p-foreign", "qmx:bbbbbbbb:other-unit"),
            position("p-manual", None),
            position("p-label-only", LABEL),
            position("p-odd-label", "qmx:short:x"),
        ),
    )

    found = attribute(read, tag="a4dqobyh", sent={MINE, MINE.replace("MN", "MX")})

    assert [(p.position, a.claim.value, a.tags) for p, a in found.positions] == [
        ("p-mine", "mine", ("a4dqobyh",)),
        ("p-twin", "twin", ("a4dqobyh",)),
        ("p-foreign", "foreign", ("bbbbbbbb",)),
        ("p-manual", "untagged", ()),
        ("p-label-only", "twin", ("a4dqobyh",)),
        ("p-odd-label", "untagged", ()),
    ]
    assert [(o.client_order_id, a.claim.value) for o, a in found.orders] == [
        (MINE, "mine"),
        (TWIN, "twin"),
        (OTHER, "foreign"),
        (None, "untagged"),
        (MINE.replace("MN", "MX"), "twin"),
    ]
    assert found.stand_down is Claim.TWIN


def trading_day(node: Rig) -> None:
    deploy(node, deployment(node.data))
    assert settle(node) == "trading"
    play(node, LIVE_FROM + 2 * DAY)


def reconcile_rows(node: Rig) -> list[dict[str, object]]:
    return node_rows(node, "reconcile")


def test_a_twin_tagged_order_stands_the_account_down_with_the_twin_alarm(tmp_path: Path) -> None:
    node = rig(tmp_path)
    node.account.opened_elsewhere(VenueOrder(TWIN, LABEL, "fx.eurusd", OrderState.OPEN))

    trading_day(node)
    status = value(node.node.call("status", {}))
    guards = unit_rows(node, "guard")

    assert node.account.received == []
    assert status["alarms"] == [
        {
            "alarm": "twin",
            "account": "demo-1",
            "records": [TWIN],
            "tags": ["a4dqobyh"],
            "action": "no_new_entries",
        }
    ]
    assert {(g["reason"], g["detail"]) for g in guards} == {
        (
            "health_stop",
            "the node cannot prove the account is its own: a twin with its tag trades it",
        )
    }
    assert reconcile_rows(node)[0] == {
        "account": "demo-1",
        "why": "start",
        "session": 0,
        "positions": [],
        "orders": [
            {"client_order_id": TWIN, "claim": "twin", "state": "open", "tags": ["a4dqobyh"]}
        ],
        "resolved": [],
        "stand_down": "twin",
    }


def test_an_untagged_position_is_protected_flagged_and_never_adopted(tmp_path: Path) -> None:
    node = rig(tmp_path)
    manual = VenuePosition(
        "manual-1", None, "fx.eurusd", "long", Decimal("0.50"), Decimal("1.08000"), None
    )
    node.account.opened_elsewhere(
        VenueOrder(None, None, "fx.eurusd", OrderState.FILLED, "manual-1", Decimal("1.08000")),
        manual,
    )

    trading_day(node)
    node.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    node.runtime.tick()
    node.runtime.tick()
    status = value(node.node.call("status", {}))
    positions = value(node.node.call("positions", {}))
    entries = [t for t in node.account.received if t.command.kind is CommandKind.PLACE_ORDER]

    assert [t.quantity for t in entries] == [Decimal("1.61"), Decimal("1.03"), Decimal("0.72")]
    assert all(t.position != "manual-1" for t in node.account.received)
    assert node.account.positions() == {"manual-1": ("fx.eurusd", "long", Decimal("0.50"), None)}
    assert positions == [
        {
            "account": "demo-1",
            "position": "manual-1",
            "market_id": "fx.eurusd",
            "side": "long",
            "quantity": "0.50",
            "entry_price": "1.08000",
            "stop_at_venue": None,
            "claim": "untagged",
            "shown": "not ours, never touched, no stop at the broker",
        }
    ]
    assert cast("list[object]", status["alarms"])[0] == {
        "alarm": "not_ours",
        "account": "demo-1",
        "position": "manual-1",
        "market_id": "fx.eurusd",
        "shown": "not ours, never touched",
    }
    assert [r.get("stand_down") for r in reconcile_rows(node)] == [None]


def test_a_position_another_node_tagged_is_left_alone_and_reported(tmp_path: Path) -> None:
    node = rig(tmp_path)
    label = "qmx:bbbbbbbb:other-unit"
    node.account.opened_elsewhere(
        VenueOrder(OTHER, label, "metal.xauusd", OrderState.FILLED, OTHER, Decimal("3010.50")),
        VenuePosition(
            OTHER, label, "metal.xauusd", "short", Decimal("0.10"), Decimal("3010.50"), None
        ),
    )

    trading_day(node)
    status = value(node.node.call("status", {}))
    positions = cast("list[dict[str, object]]", value(node.node.call("positions", {})))

    assert node.account.received == []
    assert node.account.positions() == {OTHER: ("metal.xauusd", "short", Decimal("0.10"), None)}
    assert status["alarms"] == [
        {
            "alarm": "foreign_claimant",
            "account": "demo-1",
            "records": [OTHER],
            "tags": ["bbbbbbbb"],
            "action": "no_new_entries",
        }
    ]
    assert [(p["position"], p["claim"], p["shown"]) for p in positions] == [
        (OTHER, "foreign", "not ours, never touched, no stop at the broker")
    ]
