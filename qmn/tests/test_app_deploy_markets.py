"""A deployment trades only the markets he chose and starts from its starting numbers (C-29).

Runs against the conformance venue only.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qmf.venue.commands import CommandKind
from qmn.app.store import Json
from test_app_runtime import MARKETS, Rig, deploy, deployment, month, play, rig, settle, value

EVERY_BAR = month().bars[-1][0] + 1
"""The recorded days to the month's end, in which the dummy enters both markets."""


def on(market: str | None, data: Path, deployment_id: str = "dep-1") -> dict[str, Json]:
    document = deployment(data, deployment_id)
    document["markets"] = [] if market is None else [market_row(market)]
    return document


def market_row(market: str) -> Json:
    return {"market_id": market, "instrument": {"id": MARKETS[market], "version": 1}}


def entries(node: Rig) -> list[tuple[str, str]]:
    return [
        (t.market_id, str(t.quantity))
        for t in node.account.received
        if t.command.kind is CommandKind.PLACE_ORDER
    ]


def test_a_two_market_unit_deployed_on_one_market_opens_on_that_market_only(tmp_path: Path) -> None:
    node = rig(tmp_path)
    deploy(node, on("metal.xauusd", node.data))
    assert settle(node) == "trading"

    play(node, EVERY_BAR)

    assert entries(node) == [("metal.xauusd", "0.09"), ("metal.xauusd", "0.12")]


def test_a_second_deployment_of_the_version_trades_its_own_market_beside_the_first(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    deploy(node, on("metal.xauusd", node.data, "dep-gold"), "op-gold")
    assert settle(node, "dep-gold") == "trading"
    deploy(node, on("fx.eurusd", node.data, "dep-euro"), "op-euro")
    assert settle(node, "dep-euro") == "trading"

    play(node, EVERY_BAR)

    by_market = {market for market, _ in entries(node)}
    gold = [row for row in entries(node) if row[0] == "metal.xauusd"]
    sends = cast(
        "list[dict[str, Json]]",
        value(node.node.call("journal_tail", {"streams": ["node"]}))["rows"],
    )
    owners = {
        cast("dict[str, Json]", row["body"])["market_id"]: cast("dict[str, Json]", row["body"])[
            "deployment_id"
        ]
        for row in sends
        if row["kind"] == "order" and cast("dict[str, Json]", row["body"])["step"] == "send"
    }

    assert by_market == {"fx.eurusd", "metal.xauusd"}
    assert gold == [("metal.xauusd", "0.09"), ("metal.xauusd", "0.12")]
    assert owners == {"metal.xauusd": "dep-gold", "fx.eurusd": "dep-euro"}


def test_a_kill_at_a_market_the_unit_holds_and_he_did_not_choose_is_refused(tmp_path: Path) -> None:
    node = rig(tmp_path)
    deploy(node, on("metal.xauusd", node.data))

    answer = node.node.call(
        "kill", {"op_id": "op-kill", "level": "RED", "scope": {"instrument": "EURUSD"}}
    )

    assert answer["code"] == "unknown_scope"


@pytest.mark.parametrize(
    ("markets", "why"),
    [
        ([], "deployment.markets names at least one market he chose"),
        (
            [{"market_id": "fx.gbpusd", "instrument": {"id": "gbpusd", "version": 1}}],
            "deployment.markets names fx.gbpusd, which the unit does not trade",
        ),
    ],
    ids=["none", "not-the-units"],
)
def test_a_deployment_that_chooses_no_market_of_its_unit_is_refused_before_it_is_kept(
    tmp_path: Path, markets: list[Json], why: str
) -> None:
    node = rig(tmp_path)
    document = deployment(node.data)
    document["markets"] = markets

    answer = deploy(node, document)

    assert answer == {
        "ok": False,
        "code": "bad_argument",
        "message": f"deploy: {why}",
        "op_id": "op-deploy-1",
    }
    assert value(node.node.call("deployments", {})) == []


def test_the_unit_starts_from_the_deployments_calibrated_numbers(tmp_path: Path) -> None:
    node = rig(tmp_path)
    document = on("fx.eurusd", node.data)
    document["starting"] = {
        "source": "paper_lane",
        "values": {"min_trend_strength": "0.0015", "ema_period": "100", "rsi_low": "25"},
        "watermark": 1_762_100_000_000_000_000,
    }
    deploy(node, document)
    assert settle(node) == "trading"

    unit = node.runtime.hosted["dep-1"].unit
    assert unit is not None and unit.hosted_unit is not None

    assert dict(unit.hosted_unit.calibrated_values) == {"min_trend_strength": Decimal("0.0015")}


def test_a_starting_number_outside_its_range_refuses_the_deployment_with_its_reason(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    document = on("fx.eurusd", node.data)
    document["starting"] = {"source": "paper_lane", "values": {"min_trend_strength": "0.5"}}
    deploy(node, document)

    assert settle(node) == "refused"
    rows = cast("list[dict[str, Json]]", value(node.node.call("units", {})))
    assert rows[0]["detail"] == (
        "the unit would not start: invalid input: a starting value lies inside its range"
    )
