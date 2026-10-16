"""Unsigned order-proposal tools and the LangChain tool check on the core barrier."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, ConfigDict, Field, field_validator
from qma.core.barriers.descriptors import check_descriptor
from qmx_broker.models import OrderProposal
from qmx_broker.service import BrokerService
from qmx_ledger.journal import RunJournal, encoded


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
    check_descriptor(tool.name, metadata)
