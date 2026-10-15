from __future__ import annotations

from typing import Any

import pytest
from qma.core.barriers.descriptors import check_descriptor, description_money_act, name_money_act
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
        ("create_orders", "submit_order"),
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


BROKER_ACTS = [
    "order_update",
    "order_add",
    "open_trade",
    "trade_open",
    "position_open",
    "enter_trade",
    "update_order",
    "add_order",
    "open_position",
    "close_all",
    "cancel_all",
    "CancelAll",
    "reqGlobalCancel",
    "cancelAll",
    "close_all_now",
    "flatten_all",
    "liquidate_all",
    "exit_all",
    "panic_close",
    "market_close",
    "market_open",
    "private_edit",
    "private_cancel_all",
    "liquidate",
    "set_stop_loss",
    "set_take_profit",
    "set_trading_stop",
    "move_stop_loss",
    "amend_sltp",
    "take_profit",
    "arm_kill_switches",
    "set_book_modes",
    "placeorder",
    "cancelorder",
    "ordersend",
    "closeposition",
    "cancel_all_orders",
    "closeAllPositions",
    "positions_close_all",
    "orders_cancel_all",
    "order_send",
    "OrderSend",
    "ProtoOANewOrderReq",
    "ProtoOAClosePositionReq",
    "ProtoOAAmendPositionSLTPReq",
    "ProtoOACancelOrderReq",
    "buy_market",
    "market_buy",
    "sell_limit",
    "limit_sell",
    "BuyMarket",
    "place_orders",
    "orders_submit",
    "trade_execute",
    "execute_trades",
    "new_trade",
    "trades_close",
    "close_trades",
    "position_reduce",
    "reduce_positions",
    "liquidate_positions",
    "flatten_positions",
    "order_market_buy",
    "new_oco_order",
    "futures_create_order",
    "cancel_order_by_id",
    "universal_transfer",
    "withdraw_funds",
    "transfer_funds",
    "create_orders",
    "edit_order",
    "EditOrder",
    "change_order",
    "delete_order",
    "remove_order",
    "AddOrder",
    "update_position",
    "edit_position",
    "modify_position",
    "position_modify",
    "open_long_position",
    "open_market_position",
    "enter_position",
    "increase_position",
    "decrease_position",
    "reverse_position",
    "flip_position",
    "switch_position_mode",
    "exercise_options_position",
    "place-order",
    "place.order",
    "PLACE_ORDER",
    "Place__Order",
    "submit_order_v2",
    "placeOrderV2",
    "kill_switch_arm",
    "deposit",
    "swap_tokens",
    "convert_currency",
    "send_money",
    "pay_invoice",
    "short_sell",
    "go_long",
    "go_short",
    "open_long",
    "open_short",
    "scale_in",
    "add_to_position",
    "partial_close",
    "stop_out",
    "bracket_order",
    "oco_order",
    "market_order",
    "limit_order",
    "stop_order",
    "mcp__broker__cancel_all",
    "mcp__broker__order_update",
    "mcp__ext__placeorder",
]
"""F3 to F7 of the HP8 verify at e4efead9, then the rest of its 201-row table."""

BROKER_READS = [
    "list_orders",
    "get_orders",
    "get_open_positions",
    "positions",
    "list_positions",
    "read_bars",
    "get_quote",
    "order_history",
    "trade_history",
    "get_trades",
    "order_book",
    "get_order_status",
    "list_open_orders",
    "position_report",
    "send_message",
    "create_note",
    "new_session",
    "close_session",
    "cancel_job",
    "exit_plan",
    "execute_query",
    "sell_side_research",
    "backtest_status",
    "apps_publish",
    "kill_switch_status",
    "open_positions",
    "read_trades",
    "trade_count",
    "is_market_open",
    "get_market_close_time",
    "close_all_tabs",
    "update_market_data",
    "get_deposit_history",
    "list_transfers",
    "input",
    "output",
    "getorders",
    "orderbook",
    "mcp__broker__get_open_positions",
    "in_place",
    "mutate_in_place",
    "replace_all",
    "register_all",
    "approve_global",
    "memory_put_global",
    "attempt_money_path_write",
    "money_path_field_is_set",
    "create_short_link",
]


@pytest.mark.parametrize("name", BROKER_ACTS)
def test_a_family_noun_with_any_mutating_verb_or_a_scoped_bulk_verb_is_refused(name: str) -> None:
    assert name_money_act(name) is not None
    with pytest.raises(MoneyPathDenyError, match="Money-path act refused"):
        check_descriptor(name, {})


@pytest.mark.parametrize("name", BROKER_READS)
def test_a_read_word_or_a_name_without_an_act_passes(name: str) -> None:
    assert name_money_act(name) is None


@pytest.mark.parametrize(
    ("name", "act"),
    [
        ("order_update", "update_order"),
        ("position_open", "open_position"),
        ("enter_trade", "enter_trade"),
        ("cancel_all", "cancel_all"),
        ("reqGlobalCancel", "cancel_global"),
        ("market_open", "open_market"),
        ("set_stop_loss", "set_stop_loss"),
        ("take_profit", "protection"),
        ("arm_kill_switches", "arm_kill_switch"),
        ("set_book_modes", "set_book_mode"),
        ("placeorder", "submit_order"),
        ("ordersend", "send_order"),
        ("liquidate", "liquidate"),
        ("open_short", "open_short"),
    ],
)
def test_the_act_a_name_spells_is_named(name: str, act: str) -> None:
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


@pytest.mark.parametrize("name", ["", "__", " ", "-"])
def test_a_name_with_no_words_names_no_act(name: str) -> None:
    assert name_money_act(name) is None
    assert check_descriptor("read_bars", {"tool_name": name}) is None


@pytest.mark.parametrize(
    ("text", "act"),
    [
        ("Returns the font size.", None),
        ("Upload a file and transfer it to S3.", None),
        ("Should I buy an umbrella?", None),
        ("Get the current book mode.", None),
        ("Shows the kill switch state and the order history.", None),
        ("Lists open orders.", None),
        ("Places a market order for the symbol.", "place_order"),
        ("Cancels all open orders.", "cancel_order"),
        ("Set the book mode.", "set_book_mode"),
        ("Arms the kill switch.", "arm_kill_switch"),
        ("Moves the stop loss of a position.", "move_stop_loss"),
        ("Withdraws funds to a bank.", "withdraw_fund"),
        ("Closes the position.", "close_position"),
    ],
)
def test_a_description_names_an_act_only_by_a_verb_with_its_object(
    text: str, act: str | None
) -> None:
    assert description_money_act(text) == act
