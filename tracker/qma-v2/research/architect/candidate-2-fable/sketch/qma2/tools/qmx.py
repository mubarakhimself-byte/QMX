"""QMX domain tools exposed to both engines through the registry. Money is read-only plus
proposals; nothing here can act on money (the effect enum makes that unrepresentable)."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from qma2.tools.registry import CallContext, ProposalSink, ToolSpec


class ProposeOrderInput(BaseModel):
    """Copied from money_path.OrderProposalInput: decimal text, never binary floats."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    account: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    side: Literal["buy", "sell"]
    quantity: Decimal = Field(gt=0)
    note: str = ""

    @field_validator("quantity", mode="before")
    @classmethod
    def exact_quantity(cls, value: object) -> object:
        if isinstance(value, (float, bool)):
            raise ValueError("Quantity must use decimal text, never a binary float")
        return value


class ProposalsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    offset: int = 0
    limit: int = 50


async def propose_order(inp: ProposeOrderInput, ctx: CallContext, sink: ProposalSink) -> str:
    """Writes an UNSIGNED proposal and returns its reference. The engine sees text; the
    operator sees it in Portfolio; signing needs an OperatorProof on a route that is not a tool."""
    raise NotImplementedError


async def portfolio_proposals(inp: ProposalsInput, ctx: CallContext) -> str:
    """MONEY_READ: list proposals and their signed/unsigned state."""
    raise NotImplementedError


def qmx_specs(sink: ProposalSink) -> list[ToolSpec]:
    """`money_proposal_spec(sink)` for propose_order (the only MONEY_PROPOSE), plus reads."""
    raise NotImplementedError
