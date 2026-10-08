"""Closed money path rules retained from the existing barrier."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Final, Literal, cast

from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, ConfigDict, Field, field_validator
from qmx_broker.models import OrderProposal
from qmx_broker.service import BrokerService

from qmx_agents.guards.journal import RunJournal, encoded
from qmx_agents.guards.parent_surfaces import is_parent_surface_permitted


class MoneyPathAct(StrEnum):
    ORDER = "order"
    POSITION = "position"
    PROTECTION = "protection"
    SIZING = "sizing"
    BINDING = "binding"
    MODE = "mode"
    CONTROL = "control"
    ZONE_TRANSITION = "zone_transition"
    PROMOTION = "promotion"


class MoneyPathDeniedAct(StrEnum):
    SUBMIT_ORDER = "submit_order"
    AMEND_ORDER = "amend_order"
    CANCEL_ORDER = "cancel_order"
    REPLACE_ORDER = "replace_order"
    OPEN_POSITION = "open_position"
    CLOSE_POSITION = "close_position"
    REDUCE_POSITION = "reduce_position"
    HEDGE_POSITION = "hedge_position"
    SET_PROTECTION = "set_protection"
    AMEND_PROTECTION = "amend_protection"
    SIZE = "size"
    RESIZE = "resize"
    MINT_SIZING_DECISION = "mint_sizing_decision"
    CREATE_BINDING = "create_binding"
    AMEND_BINDING = "amend_binding"
    ACTIVATE_BINDING = "activate_binding"
    STAND_DOWN_BINDING = "stand_down_binding"
    DELETE_BINDING = "delete_binding"
    SET_BOOK_MODE = "set_book_mode"
    SET_SEAT_STATE = "set_seat_state"
    SET_BOOK_PARAMETER = "set_book_parameter"
    SET_BMS_PARAMETER = "set_bms_parameter"
    SET_PRIORITY_RANK = "set_priority_rank"
    SET_CAPITAL_FLOOR = "set_capital_floor"
    ARM_KILL_SWITCH = "arm_kill_switch"
    DISARM_KILL_SWITCH = "disarm_kill_switch"
    CHANGE_KILL_SWITCH = "change_kill_switch"
    CHANGE_CONTROL_ACTION = "change_control_action"


MONEY_PATH_DENY_LIST: Final[frozenset[MoneyPathAct]] = frozenset(MoneyPathAct)


MONEY_PATH_DENIED_ACTS: Final[frozenset[MoneyPathDeniedAct]] = frozenset(MoneyPathDeniedAct)


_ROLE_PREFIXES: Final[tuple[str, ...]] = (
    "paper_only_",
    "live_only_",
    "demo_only_",
    "paper_",
    "live_",
    "demo_",
)


_ALIAS_PAIRS: Final[tuple[tuple[str, str], ...]] = (
    ("place_order", MoneyPathDeniedAct.SUBMIT_ORDER.value),
    ("place_an_order", MoneyPathDeniedAct.SUBMIT_ORDER.value),
    ("submit_an_order", MoneyPathDeniedAct.SUBMIT_ORDER.value),
    ("order_submit", MoneyPathDeniedAct.SUBMIT_ORDER.value),
    ("amend_an_order", MoneyPathDeniedAct.AMEND_ORDER.value),
    ("order_amend", MoneyPathDeniedAct.AMEND_ORDER.value),
    ("cancel_an_order", MoneyPathDeniedAct.CANCEL_ORDER.value),
    ("order_cancel", MoneyPathDeniedAct.CANCEL_ORDER.value),
    ("replace_an_order", MoneyPathDeniedAct.REPLACE_ORDER.value),
    ("order_replace", MoneyPathDeniedAct.REPLACE_ORDER.value),
    ("open_a_position", MoneyPathDeniedAct.OPEN_POSITION.value),
    ("close_a_position", MoneyPathDeniedAct.CLOSE_POSITION.value),
    ("reduce_a_position", MoneyPathDeniedAct.REDUCE_POSITION.value),
    ("hedge_a_position", MoneyPathDeniedAct.HEDGE_POSITION.value),
    ("set_a_protection", MoneyPathDeniedAct.SET_PROTECTION.value),
    ("amend_a_protection", MoneyPathDeniedAct.AMEND_PROTECTION.value),
    ("re_size", MoneyPathDeniedAct.RESIZE.value),
    ("re_size_sizing", MoneyPathDeniedAct.RESIZE.value),
    ("mint_a_sizing_decision", MoneyPathDeniedAct.MINT_SIZING_DECISION.value),
    ("sizing_decision", MoneyPathDeniedAct.MINT_SIZING_DECISION.value),
    ("create_a_binding", MoneyPathDeniedAct.CREATE_BINDING.value),
    ("quant_to_book_binding", MoneyPathDeniedAct.CREATE_BINDING.value),
    ("bot_to_book_binding", MoneyPathDeniedAct.CREATE_BINDING.value),
    ("stand_down", MoneyPathDeniedAct.STAND_DOWN_BINDING.value),
    ("book_mode", MoneyPathDeniedAct.SET_BOOK_MODE.value),
    ("seat_state", MoneyPathDeniedAct.SET_SEAT_STATE.value),
    ("book_parameter", MoneyPathDeniedAct.SET_BOOK_PARAMETER.value),
    ("bms_parameter", MoneyPathDeniedAct.SET_BMS_PARAMETER.value),
    ("priority_rank", MoneyPathDeniedAct.SET_PRIORITY_RANK.value),
    ("capital_floor", MoneyPathDeniedAct.SET_CAPITAL_FLOOR.value),
    ("kill_switch", MoneyPathDeniedAct.CHANGE_KILL_SWITCH.value),
    ("node_control_action", MoneyPathDeniedAct.CHANGE_CONTROL_ACTION.value),
    ("control_action", MoneyPathDeniedAct.CHANGE_CONTROL_ACTION.value),
    ("transition_zone", MoneyPathAct.ZONE_TRANSITION.value),
    ("transition_a_registry_artifact", MoneyPathAct.ZONE_TRANSITION.value),
    ("promote", MoneyPathAct.PROMOTION.value),
)


MONEY_PATH_ACT_ALIASES: Final[Mapping[str, str]] = MappingProxyType(dict(_ALIAS_PAIRS))


class MoneyPathDenyError(ValueError):
    """Money-state authority cannot be granted to an agent."""


def _normalize_act_token(value: str) -> str:
    token = value.strip().casefold().replace("-", "_").replace("/", "_")
    token = "_".join(token.split())
    while "__" in token:
        token = token.replace("__", "_")
    token = token.strip("_")
    for prefix in _ROLE_PREFIXES:
        if token.startswith(prefix) and len(token) > len(prefix):
            token = token[len(prefix) :]
            break
    return token


def match_money_path_act(act: MoneyPathAct | MoneyPathDeniedAct | str) -> str | None:
    if isinstance(act, MoneyPathAct):
        return act.value
    if isinstance(act, MoneyPathDeniedAct):
        return act.value
    if not act.strip():
        return None
    token = _normalize_act_token(act)
    if not token:
        return None
    aliased = MONEY_PATH_ACT_ALIASES.get(token, token)
    try:
        return MoneyPathAct(aliased).value
    except ValueError:
        pass
    try:
        return MoneyPathDeniedAct(aliased).value
    except ValueError:
        return None


def is_money_path_act_denied(act: MoneyPathAct | MoneyPathDeniedAct | str) -> bool:
    return match_money_path_act(act) is not None


class OrderProposalInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    account: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    side: Literal["buy", "sell"]
    quantity: Decimal = Field(gt=0)

    @field_validator("quantity", mode="before")
    @classmethod
    def exact_quantity(cls, value: object) -> object:
        if isinstance(value, (float, bool)):
            raise ValueError("Quantity must use decimal text, never a binary float")
        return value


class OrderProposalTool(BaseTool):
    """A local proposal writer, with no venue dependency or execution authority."""

    name: str = "propose_order"
    description: str = "Save an unsigned order proposal for the operator; never send an order."
    args_schema: ArgsSchema | None = OrderProposalInput
    journal: RunJournal = Field(exclude=True)
    metadata: dict[str, Any] | None = Field(default_factory=lambda: {"money_path": True})

    def _run(self, account: str, symbol: str, side: str, quantity: Decimal) -> str:
        if not account.strip() or not symbol.strip() or side not in {"buy", "sell"}:
            raise ValueError("Provide an account, symbol and buy/sell side")
        if not quantity.is_finite() or quantity <= 0:
            raise ValueError("Quantity must be finite and positive")
        payload = {"account": account, "symbol": symbol, "side": side, "quantity": str(quantity)}
        reference = self.journal.store_result(encoded(payload))
        self.journal.append("order_proposed", {"result_ref": reference, "status": "unsigned"})
        return reference


def propose_order(journal: RunJournal) -> OrderProposalTool:
    return OrderProposalTool(journal=journal)


class BrokerOrderProposalTool(BaseTool):
    """Trusted local Portfolio writer, substituted for the broker MCP proposal."""

    name: str = "propose_order"
    description: str = "Queue an unsigned broker order for Portfolio review; never execute."
    args_schema: ArgsSchema | None = OrderProposal
    service: BrokerService = Field(exclude=True)
    metadata: dict[str, Any] | None = Field(default_factory=lambda: {"money_path": True})

    def _run(
        self,
        broker_id: str,
        connection_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: str,
        order_type: str = "market",
        limit_price: str = "",
    ) -> str:
        proposal = OrderProposal.model_validate(
            {
                "broker_id": broker_id,
                "connection_id": connection_id,
                "account_id": account_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "limit_price": limit_price,
            }
        )
        return encoded(self.service.propose_order(proposal)).decode("utf-8")


def check_tool(tool: BaseTool) -> None:
    if type(tool) in {OrderProposalTool, BrokerOrderProposalTool} and tool.name == "propose_order":
        return
    metadata = tool.metadata or {}
    if metadata.get("money_path"):
        raise MoneyPathDenyError(f"Money-path tool refused: {tool.name}")
    tokens: list[str] = [tool.name]
    # MCP names can be server-prefixed; check every suffix and original metadata.
    for separator in ("_", ".", ":", "/"):
        parts = tool.name.split(separator)
        tokens.extend(separator.join(parts[index:]) for index in range(1, len(parts)))
    sources: list[dict[str, Any]] = [metadata]
    while sources:
        source = sources.pop()
        for key in ("mcp", "tool", "annotations", "_meta"):
            nested = source.get(key)
            if isinstance(nested, dict):
                sources.append(cast("dict[str, Any]", nested))
        if "parent_library" in source and not is_parent_surface_permitted(
            str(source["parent_library"]), str(source.get("parent_surface", ""))
        ):
            raise MoneyPathDenyError(f"Parent surface refused: {tool.name}")
        if source.get("record_family") is not None:
            raise MoneyPathDenyError(f"Parent record mutation refused: {tool.name}")
        if source.get("money_path"):
            raise MoneyPathDenyError(f"Money-path tool refused: {tool.name}")
        for key in ("act", "acts", "name", "tool_name"):
            value = source.get(key)
            if isinstance(value, str):
                tokens.append(value)
            elif isinstance(value, (list, tuple, set)):
                tokens.extend(str(item) for item in cast("list[Any]", value))
    if any(is_money_path_act_denied(token) for token in tokens):
        raise MoneyPathDenyError(f"Money-path act refused: {tool.name}")
