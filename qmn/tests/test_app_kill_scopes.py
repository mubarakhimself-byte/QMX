"""A symbol and a market id name the same market, a scope the node does not hold is refused, and
every resume is journalled (C-35). Runs against the conformance venue only."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from qmf.venue.commands import CommandKind
from qmn.app.stand_down import Kind
from qmn.app.store import Json
from test_app_runtime import (
    ACCOUNT,
    Rig,
    deploy,
    deployment,
    month,
    play,
    rig,
    settle,
    value,
)

EVERY_BAR = month().bars[-1][0] + 1
"""The recorded days to the month's end, in which the dummy enters both markets."""
HOLDS = [
    "all",
    "account:demo-1",
    "deployment_id:dep-1",
    "instrument:EURUSD",
    "instrument:XAUUSD",
    "instrument:fx.eurusd",
    "instrument:metal.xauusd",
]
"""Every scope the rig's node holds, as a refusal lists them."""


def trading(tmp_path: Path) -> Rig:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    assert settle(node) == "trading"
    return node


def entries(node: Rig) -> list[str]:
    return [t.market_id for t in node.account.received if t.command.kind is CommandKind.PLACE_ORDER]


def node_rows(node: Rig, kind: str) -> list[dict[str, Json]]:
    rows = cast("list[dict[str, Json]]", value(node.node.call("journal_tail", {}))["rows"])
    return [cast("dict[str, Json]", row["body"]) for row in rows if row["kind"] == kind]


def test_the_recorded_days_enter_both_markets_with_nothing_held(tmp_path: Path) -> None:
    node = trading(tmp_path)
    play(node, EVERY_BAR)

    assert set(entries(node)) == {"fx.eurusd", "metal.xauusd"}


@pytest.mark.parametrize(
    "scope", [{"instrument": "XAUUSD"}, {"instrument": "metal.xauusd"}], ids=["symbol", "market-id"]
)
def test_a_red_at_either_name_of_a_market_blocks_its_entries_alone(
    tmp_path: Path, scope: dict[str, Json]
) -> None:
    node = trading(tmp_path)
    node.node.call("kill", {"op_id": "op-1", "level": "RED", "scope": scope})
    play(node, EVERY_BAR)

    assert set(entries(node)) == {"fx.eurusd"}


def test_a_stand_down_held_by_symbol_blocks_the_market_id_entries(tmp_path: Path) -> None:
    node = trading(tmp_path)
    node.runtime.stand_down(Kind.SPEC_CHANGE, "instrument:XAUUSD", "the lot step moved")
    play(node, EVERY_BAR)

    assert set(entries(node)) == {"fx.eurusd"}


@pytest.mark.parametrize(
    ("set_at", "resume_at"),
    [("metal.xauusd", "XAUUSD"), ("XAUUSD", "metal.xauusd")],
    ids=["set-by-id", "set-by-symbol"],
)
def test_a_resume_by_one_name_clears_what_the_other_name_set(
    tmp_path: Path, set_at: str, resume_at: str
) -> None:
    node = trading(tmp_path)
    node.node.call("kill", {"op_id": "op-2", "level": "RED", "scope": {"instrument": set_at}})
    node.node.call("pause", {"op_id": "op-3", "scope": {"instrument": set_at}})
    node.runtime.stand_down(Kind.SPEC_CHANGE, f"instrument:{set_at}", "the lot step moved")
    node.runtime.tick()
    node.now[0] += 1_000_000_000

    resumed = node.node.call("resume", {"op_id": "op-4", "scope": {"instrument": resume_at}})
    node.runtime.tick()
    state = value(node.node.call("status", {}))

    assert value(resumed) == {"state": "accepted", "open_causes": []}
    assert (state["word"], state["kill_level"], state["pauses"], state["kill_effects"]) == (
        "Trading",
        "GREEN",
        [],
        {},
    )
    assert node.runtime.stand_downs.document() == []


def test_a_resume_of_one_market_leaves_the_other_markets_kill(tmp_path: Path) -> None:
    node = trading(tmp_path)
    node.node.call(
        "kill", {"op_id": "op-5", "level": "RED", "scope": {"instrument": "metal.xauusd"}}
    )
    node.node.call("kill", {"op_id": "op-6", "level": "RED", "scope": {"instrument": "fx.eurusd"}})

    node.node.call("resume", {"op_id": "op-7", "scope": {"instrument": "EURUSD"}})

    assert value(node.node.call("status", {}))["headline"] == "Killed at XAUUSD"


def test_an_older_resume_by_one_name_does_not_lift_a_newer_pause_by_the_other(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    node.node.call(
        "pause",
        {
            "op_id": "op-14",
            "scope": {"instrument": "fx.eurusd"},
            "issued_at": "2025-03-19T19:30:00+00:00",
        },
    )
    node.node.call(
        "resume",
        {
            "op_id": "op-15",
            "scope": {"instrument": "EURUSD"},
            "issued_at": "2025-03-19T19:00:00+00:00",
        },
    )

    assert value(node.node.call("status", {}))["pauses"] == ["instrument:fx.eurusd"]


@pytest.mark.parametrize(
    ("change", "arguments", "named"),
    [
        ("kill", {"level": "RED", "scope": {"account": "other-9"}}, "account other-9"),
        ("pause", {"scope": {"account": "other-9"}}, "account other-9"),
        ("resume", {"scope": {"deployment_id": "dep-9"}}, "deployment_id dep-9"),
        ("flatten", {"scope": {"account": "other-9"}}, "account other-9"),
        ("kill", {"level": "RED", "scope": {"instrument": "fx.gbpusd"}}, "instrument fx.gbpusd"),
    ],
    ids=["kill", "pause", "resume", "flatten", "instrument"],
)
def test_a_scope_the_node_does_not_hold_is_refused_and_changes_nothing(
    tmp_path: Path, change: str, arguments: dict[str, Json], named: str
) -> None:
    node = trading(tmp_path)
    before = len(node.node.context.store.accepted())

    answer = node.node.call(change, {"op_id": "op-1", **arguments})
    node.runtime.tick()
    state = value(node.node.call("status", {}))

    assert answer == {
        "ok": False,
        "code": "unknown_scope",
        "message": f"{change}: this node holds no {named}; it holds {', '.join(HOLDS)}",
        "value": cast("Json", HOLDS),
    }
    assert len(node.node.context.store.accepted()) == before
    assert (state["word"], state["kill_level"], state["kill_effects"]) == ("Trading", "GREEN", {})
    assert node_rows(node, "kill_level") == []


def test_a_node_with_no_deployment_holds_only_all(tmp_path: Path) -> None:
    node = rig(tmp_path)

    answer = node.node.call(
        "kill", {"op_id": "op-8", "level": "RED", "scope": {"account": ACCOUNT}}
    )
    whole = node.node.call("kill", {"op_id": "op-9", "level": "RED", "scope": "all"})

    assert answer["code"] == "unknown_scope"
    assert answer["value"] == ["all"]
    assert value(whole) == {"level_in_force": "RED"}


def test_a_resume_journals_one_row_beside_the_rise(tmp_path: Path) -> None:
    node = trading(tmp_path)
    node.node.call("kill", {"op_id": "op-10", "level": "RED", "scope": {"instrument": "XAUUSD"}})
    node.node.call("kill", {"op_id": "op-11", "level": "YELLOW", "scope": {"account": ACCOUNT}})
    node.runtime.tick()

    node.node.call("resume", {"op_id": "op-resume", "scope": "all"})
    node.runtime.tick()
    node.runtime.tick()
    rows = node_rows(node, "kill_level")

    assert [(r["scope"], r["level"]) for r in rows] == [
        ("instrument:XAUUSD", "RED"),
        ("account:demo-1", "YELLOW"),
        ("all", "GREEN"),
    ]
    assert (rows[-1]["op_id"], rows[-1]["cleared"]) == (
        "op-resume",
        ["account:demo-1", "instrument:XAUUSD"],
    )


def test_a_resume_with_nothing_held_still_journals_its_one_row(tmp_path: Path) -> None:
    node = trading(tmp_path)

    node.node.call("resume", {"op_id": "op-resume", "scope": {"account": ACCOUNT}})
    node.runtime.tick()

    rows = node_rows(node, "kill_level")
    assert [(r["scope"], r["level"], r["cleared"]) for r in rows] == [
        ("account:demo-1", "GREEN", [])
    ]


def test_a_restart_lands_no_second_row_for_a_resume_and_lands_one_it_missed(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    node.node.call("kill", {"op_id": "op-12", "level": "YELLOW", "scope": "all"})
    node.runtime.tick()
    node.node.call("resume", {"op_id": "op-seen", "scope": "all"})
    node.runtime.tick()
    node.node.call("kill", {"op_id": "op-13", "level": "YELLOW", "scope": "all"})
    node.runtime.tick()
    node.node.call("resume", {"op_id": "op-missed", "scope": "all"})
    node.node.stop()

    back = rig(tmp_path)
    back.runtime.tick()
    back.runtime.tick()

    resumes = [r["op_id"] for r in node_rows(back, "kill_level") if r["level"] == "GREEN"]
    assert resumes == ["op-seen", "op-missed"]
