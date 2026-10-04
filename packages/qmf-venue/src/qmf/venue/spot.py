"""Pure, credential-free spot metadata normalization; no exchange runtime.

Original implementation informed by CCXT's precision/limits separation. This
bounded version accepts explicit TICK_SIZE decimal strings only. It does not
infer precisionMode from numeric values or claim exchange conformance.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from typing import cast

from qmf.core import Ok, RefusalCategory, Result, Retryability, TypedRefusal


def refusal(reason: str, *, code: str = "INVALID_INPUT") -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.STORAGE_FAILURE
        if code == "STORAGE_FAILURE"
        else RefusalCategory.POLICY_REJECTION
        if code in {"OWNER_BUSY", "POLICY", "RATE_LIMIT"}
        else RefusalCategory.STALE_EVIDENCE
        if code in {"STALE", "UNSYNCED", "GAP"}
        else RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context={"reason": reason, "code": code, "simulation": True},
    )


def exact(value: object, *, positive: bool = True) -> Decimal:
    """Finite bounded decimal strings; never silently stringify a binary float."""
    if not isinstance(value, str) or not value or len(value) > 64:
        raise ValueError("an exact decimal string is required")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid decimal") from exc
    if (
        not number.is_finite()
        or number < 0
        or (positive and number == 0)
        or len(number.as_tuple().digits) > 28
        or abs(number.adjusted()) > 18
    ):
        raise ValueError("decimal must be finite, nonnegative and bounded")
    return number


def mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("metadata object is required")
    return cast("Mapping[str, object]", value)


@dataclass(frozen=True, slots=True)
class SpotMarket:
    native_id: str
    symbol: str
    base: str
    quote: str
    amount_step: str
    price_step: str
    min_amount: str
    max_amount: str
    min_cost: str
    max_cost: str

    @classmethod
    def from_ccxt_market(cls, payload: object, *, precision_mode: object) -> Result[SpotMarket]:
        try:
            body = mapping(payload)
            if precision_mode != "TICK_SIZE":
                raise ValueError("this adapter requires explicit TICK_SIZE metadata")
            if body.get("spot") is not True or body.get("contract") is not False:
                raise ValueError(
                    "only explicitly classified non-contract spot markets are supported"
                )
            if body.get("active") is not True:
                raise ValueError("market must be explicitly active")
            names = [body.get(key) for key in ("id", "symbol", "base", "quote")]
            if any(not isinstance(v, str) or not v.strip() or len(v) > 128 for v in names):
                raise ValueError("market identity, symbol, base and quote must be explicit")
            native, symbol, base, quote = cast("tuple[str, str, str, str]", tuple(names))
            if base == quote or symbol != f"{base}/{quote}":
                raise ValueError("spot symbol must preserve explicit BASE/QUOTE identity")
            precision, limits = mapping(body.get("precision")), mapping(body.get("limits"))
            amount, cost = mapping(limits.get("amount")), mapping(limits.get("cost"))
            values = [
                precision.get("amount"),
                precision.get("price"),
                amount.get("min"),
                amount.get("max"),
                cost.get("min"),
                cost.get("max"),
            ]
            decimals = [exact(value) for value in values]
            if decimals[2] > decimals[3] or decimals[4] > decimals[5]:
                raise ValueError("market minimum cannot exceed maximum")
            return Ok(cls(native, symbol, base, quote, *cast("list[str]", values)))
        except (ValueError, TypeError) as exc:
            return refusal(str(exc))

    def validate_order(self, amount: object, price: object) -> Result[tuple[Decimal, Decimal]]:
        with localcontext() as context:
            context.prec = 128
            return self._validate_order(amount, price)

    def _validate_order(self, amount: object, price: object) -> Result[tuple[Decimal, Decimal]]:
        try:
            quantity, limit = exact(amount), exact(price)
            if quantity % exact(self.amount_step) or limit % exact(self.price_step):
                raise ValueError("amount/price violates declared tick precision")
            if not exact(self.min_amount) <= quantity <= exact(self.max_amount):
                raise ValueError("amount is outside declared market limits")
            if not exact(self.min_cost) <= quantity * limit <= exact(self.max_cost):
                raise ValueError("notional is outside declared market limits")
            return Ok((quantity, limit))
        except (ValueError, InvalidOperation) as exc:
            return refusal(str(exc))
