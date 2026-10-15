from __future__ import annotations

from typing import Any

import pytest
from qma.core.barriers.descriptors import check_descriptor, name_money_act
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


@pytest.mark.parametrize(
    ("name", "act"),
    [
        ("placeOrder", "submit_order"),
        ("PlaceOrder", "submit_order"),
        ("createOrder", "submit_order"),
        ("CreateOrder", "submit_order"),
        ("submitOrder", "submit_order"),
        ("closePosition", "close_position"),
        ("armKillSwitch", "arm_kill_switch"),
        ("place_order2", "submit_order"),
        ("placeOrder2", "submit_order"),
        ("place_order_2", "submit_order"),
        ("place2order", "submit_order"),
        ("mcp__broker__PlaceOrderV2", "submit_order"),
        ("mcp__broker__placeOrder", "submit_order"),
        ("HTTPPlaceOrder", "submit_order"),
        ("readBars", None),
        ("listPositions", None),
        ("orderHistory", None),
        ("bars2", None),
        ("PROmote", "promotion"),
        ("ReSize", "resize"),
        ("version_v2", None),
    ],
)
def test_camel_case_and_digit_spellings_read_as_their_words(name: str, act: str | None) -> None:
    assert name_money_act(name) == act


@pytest.mark.parametrize(
    ("name", "act"),
    [
        ("cancel_all_orders", "cancel_order"),
        ("close_all_positions", "close_position"),
        ("OrderSend", "send_order"),
        ("ProtoOANewOrderReq", "new_order"),
        ("ProtoOAClosePositionReq", "close_position"),
        ("ProtoOAAmendPositionSLTPReq", "amend_position"),
        ("ProtoOACancelOrderReq", "cancel_order"),
        ("buy_market", "buy"),
        ("sell_limit", "sell"),
        ("marketBuy", "buy"),
        ("withdraw_funds", "withdraw"),
        ("transfer_funds", "transfer"),
        ("place_order_now", "submit_order"),
        ("close_position_request", "close_position"),
        ("cancel_orders", "cancel_order"),
        ("orders_cancel", "cancel_order"),
        ("position_close", "close_position"),
        ("positions_close_all", "close_position"),
        ("execute_trade", "execute_trade"),
        ("trade_execute", "execute_trade"),
        ("send_order", "order"),
        ("modify_order", "order"),
        ("amend_orders", "amend_order"),
        ("new_order", "order"),
        ("create_orders", "create_order"),
        ("exit_position", "position"),
        ("exit_all_positions", "exit_position"),
        ("close_trade", "close_trade"),
        ("closeAllPositions", "close_position"),
        ("CancelAllOrders", "cancel_order"),
        ("place_market_order", "order"),
        ("MarketOrderPlace", "place_order"),
        ("submit_bracket_orders", "submit_order"),
        ("reduce_positions", "reduce_position"),
        ("mcp__broker__buy", "buy"),
        ("mcp__ext__OrderSend", "send_order"),
        ("list_orders", None),
        ("get_orders", None),
        ("orders", None),
        ("positions", None),
        ("list_positions", None),
        ("get_open_positions", None),
        ("order_history", None),
        ("order_book", None),
        ("trade_history", None),
        ("list_trades", None),
        ("get_order_status", None),
        ("cancel_job", None),
        ("create_report", None),
        ("send_message", None),
        ("apps_call", None),
        ("runs_cancel", None),
    ],
)
def test_broker_tool_names_read_as_their_acts(name: str, act: str | None) -> None:
    assert name_money_act(name) == act


@pytest.mark.parametrize(
    "name", ["cancel_all_orders", "OrderSend", "ProtoOANewOrderReq", "buy_market", "withdraw_funds"]
)
def test_broker_tool_names_are_refused(name: str) -> None:
    with pytest.raises(MoneyPathDenyError, match=f"Money-path act refused: {name}"):
        check_descriptor(name, {})
    with pytest.raises(MoneyPathDenyError, match="Money-path act refused: read_bars"):
        check_descriptor("read_bars", {"mcp": {"tool_name": name}})


@pytest.mark.parametrize("name", ["placeOrder", "CreateOrder", "place_order2", "closePosition"])
def test_camel_case_and_digit_spellings_are_refused(name: str) -> None:
    with pytest.raises(MoneyPathDenyError, match=f"Money-path act refused: {name}"):
        check_descriptor(name, {})
    with pytest.raises(MoneyPathDenyError, match="Money-path act refused: read_bars"):
        check_descriptor("read_bars", {"acts": [name]})


def test_every_denied_act_and_alias_is_refused_behind_a_role_prefix() -> None:
    for name in [*(act.value for act in MONEY_PATH_DENIED_ACTS), *MONEY_PATH_ACT_ALIASES]:
        with pytest.raises(MoneyPathDenyError):
            check_descriptor("paper_" + name, {})


@pytest.mark.parametrize(
    "name",
    ["create_order", "create-order", "Create Order", "CREATE-ORDER", "create--order"],
)
def test_create_order_is_refused_in_every_spelling(name: str) -> None:
    with pytest.raises(MoneyPathDenyError, match=f"Money-path act refused: {name}"):
        check_descriptor(name, {})
    with pytest.raises(MoneyPathDenyError, match="Money-path act refused: read_bars"):
        check_descriptor("read_bars", {"acts": [name]})
    with pytest.raises(MoneyPathDenyError, match="Money-path act refused: read_bars"):
        check_descriptor("read_bars", {"mcp": {"tool_name": name}})


@pytest.mark.parametrize("separator", ["-", " ", "--", "."])
@pytest.mark.parametrize("upper", [False, True])
def test_every_denied_act_and_alias_is_refused_in_any_spelling(separator: str, upper: bool) -> None:
    for name in [*(act.value for act in MONEY_PATH_DENIED_ACTS), *MONEY_PATH_ACT_ALIASES]:
        for prefixed in (name, "paper_" + name, "mcp__broker__" + name):
            spelled = prefixed.replace("_", separator)
            with pytest.raises(MoneyPathDenyError):
                check_descriptor(spelled.upper() if upper else spelled, {})


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
