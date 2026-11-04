"""The node's status word and reasons name everything that holds it (C-35).

Runs against the conformance venue only.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from qmn.app.store import Json
from test_app_runtime import ACCOUNT, Rig, deploy, deployment, rig, settle, value


def trading(tmp_path: Path) -> Rig:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    assert settle(node) == "trading"
    return node


def status(node: Rig) -> dict[str, Json]:
    node.runtime.tick()
    return value(node.node.call("status", {}))


def said(state: dict[str, Json]) -> tuple[Json, Json, Json]:
    return state["word"], state["headline"], state["kill_level"]


def test_a_node_with_nothing_held_still_reads_trading(tmp_path: Path) -> None:
    state = status(trading(tmp_path))

    assert said(state) == ("Trading", "Trading, 1 unit", "GREEN")
    assert state["reasons"] == []


def test_a_risk_stop_on_one_market_reads_in_the_word_and_the_reasons(tmp_path: Path) -> None:
    node = trading(tmp_path)
    assert node.runtime.risk_stop("dep-1", "metal.xauusd", "daily_loss", "2R lost") is not None

    state = status(node)

    assert said(state) == ("Stopped by a risk rule", "Paused, risk stop on XAUUSD", "GREEN")
    assert state["reasons"] == [
        "Stopped by a risk rule on XAUUSD: daily_loss: 2R lost. It waits for your resume."
    ]


def test_a_kill_at_any_scope_reads_in_the_word_the_level_and_the_reasons(tmp_path: Path) -> None:
    node = trading(tmp_path)
    killed = node.node.call(
        "kill", {"op_id": "op-1", "level": "RED", "scope": {"instrument": "XAUUSD"}}
    )

    state = status(node)
    units = cast("list[dict[str, Json]]", value(node.node.call("status", {}))["reasons"])
    row = cast("list[dict[str, Json]]", node.node.call("units", {})["value"])[0]

    assert value(killed) == {"level_in_force": "RED"}
    assert said(state) == ("Paused", "Killed at XAUUSD", "RED")
    assert units == ["The kill switch is at RED for XAUUSD."]
    assert row["kill_level"] == "RED"


def test_a_kill_named_by_market_id_reads_the_symbol_he_knows(tmp_path: Path) -> None:
    node = trading(tmp_path)
    node.node.call(
        "kill", {"op_id": "op-2", "level": "YELLOW", "scope": {"instrument": "fx.eurusd"}}
    )

    assert said(status(node)) == ("Paused", "Killed at EURUSD", "YELLOW")


def test_a_kill_at_an_account_or_a_deployment_reads_where_it_holds(tmp_path: Path) -> None:
    node = trading(tmp_path)
    node.node.call("kill", {"op_id": "op-3", "level": "ORANGE", "scope": {"account": ACCOUNT}})
    node.node.call(
        "kill", {"op_id": "op-4", "level": "YELLOW", "scope": {"deployment_id": "dep-1"}}
    )

    state = status(node)

    assert said(state) == ("Paused", "Killed at account demo-1, deployment dep-1", "ORANGE")
    assert state["reasons"] == [
        "The kill switch is at ORANGE for account demo-1.",
        "The kill switch is at YELLOW for deployment dep-1.",
    ]


def test_a_pause_at_one_market_reads_paused_at_that_market(tmp_path: Path) -> None:
    node = trading(tmp_path)
    node.node.call("pause", {"op_id": "op-5", "scope": {"instrument": "EURUSD"}})

    state = status(node)

    assert said(state) == ("Paused", "Paused at EURUSD", "GREEN")
    assert state["pauses"] == ["instrument:EURUSD"]


def stale_feed(node: Rig, market: str) -> None:
    """The stand-down watch reads a binding whose feed on ``market`` last quoted 130 s ago."""
    quote = SimpleNamespace(receive_time=node.now[0] - 130_000_000_000)
    feed = SimpleNamespace(ready=True, reason="", markets=(market,), quote=lambda _market: quote)
    node.runtime.stand_downs.watch_feed(ACCOUNT, cast("Any", feed))


def test_a_stand_down_that_clears_itself_reads_too_when_the_node_trades_that_market(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    stale_feed(node, "metal.xauusd")

    state = status(node)

    assert said(state) == ("Stopped by a health check", "Stopped by a health check", "GREEN")
    assert state["reasons"] == [
        "Stopped by a health check on XAUUSD: last quote 130 s ago. It clears by itself."
    ]


def test_a_stand_down_on_a_market_no_deployment_trades_leaves_the_word_alone(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    stale_feed(node, "self.test")

    assert said(status(node)) == ("Trading", "Trading, 1 unit", "GREEN")
