from __future__ import annotations

from typing import Any

import pytest
from qma.core.barriers.descriptors import check_descriptor
from qma.core.barriers.money_path import (
    MONEY_PATH_ACT_ALIASES,
    MONEY_PATH_DENIED_ACTS,
    MoneyPathDenyError,
)


@pytest.mark.parametrize(
    "name",
    [
        "place_order",
        "create_order",
        "submit_order",
        "paper_place_order",
        "mcp__broker__place_order",
        "broker_demo_close_position",
        "risk.set_book_mode",
        "node:arm_kill_switch",
        "qmx/resize",
    ],
)
def test_money_tool_names_are_refused(name: str) -> None:
    with pytest.raises(MoneyPathDenyError, match=f"Money-path act refused: {name}"):
        check_descriptor(name, {})


def test_every_denied_act_and_alias_is_refused_behind_a_role_prefix() -> None:
    for name in [*(act.value for act in MONEY_PATH_DENIED_ACTS), *MONEY_PATH_ACT_ALIASES]:
        with pytest.raises(MoneyPathDenyError):
            check_descriptor("paper_" + name, {})


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        ({"money_path": True}, "Money-path tool refused"),
        ({"acts": ["resize"]}, "Money-path act refused"),
        ({"mcp": {"tool_name": "cancel_order"}}, "Money-path act refused"),
        ({"mcp": {"money_path": True}}, "Money-path tool refused"),
        ({"mcp": {"tool": {"_meta": {"money_path": True}}}}, "Money-path tool refused"),
        ({"mcp": {"tool": {"annotations": {"acts": ["resize"]}}}}, "Money-path act refused"),
        ({"parent_library": "qmf-risk", "parent_surface": "write"}, "Parent surface refused"),
        ({"record_family": "binding"}, "Parent record mutation refused"),
    ],
)
def test_money_metadata_is_refused_under_a_read_name(
    metadata: dict[str, Any], message: str
) -> None:
    with pytest.raises(MoneyPathDenyError, match=f"{message}: read_bars"):
        check_descriptor("read_bars", metadata)


def test_propose_order_is_refused_without_the_callers_writer_type_exemption() -> None:
    with pytest.raises(MoneyPathDenyError, match="Money-path tool refused: propose_order"):
        check_descriptor("propose_order", {"money_path": True})
    with pytest.raises(MoneyPathDenyError, match="Money-path act refused: propose_order"):
        check_descriptor("propose_order", {})


@pytest.mark.parametrize(
    ("name", "metadata"),
    [
        ("read_bars", {}),
        ("get_quote", {"annotations": {"readOnlyHint": True}}),
        ("list_positions", {"mcp": {"tool_name": "list_positions"}}),
        (
            "save_candidate",
            {"parent_library": "qmf-registry", "parent_surface": "dev_zone_candidate_write"},
        ),
    ],
)
def test_read_tools_pass(name: str, metadata: dict[str, Any]) -> None:
    assert check_descriptor(name, metadata) is None
