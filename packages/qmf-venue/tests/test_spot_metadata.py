"""Explicit spot classification and precision-mode boundaries."""

from typing import Any

import pytest
from qmf.core import is_ok, is_refusal
from qmf.venue.spot import SpotMarket


def metadata() -> dict[str, Any]:
    return {
        "id": "BTCUSDT",
        "symbol": "BTC/USDT",
        "base": "BTC",
        "quote": "USDT",
        "spot": True,
        "contract": False,
        "active": True,
        "precision": {"amount": "0.00000001", "price": "0.00000001"},
        "limits": {
            "amount": {"min": "0.00000001", "max": "10"},
            "cost": {"min": "10", "max": "1000000"},
        },
    }


@pytest.mark.parametrize(
    "change",
    [
        {"spot": False},
        {"contract": True},
        {"active": False},
        {"symbol": "BTC/USDT:USDT"},
        {"base": "USDT"},
        {"precision": {"amount": 1e-8, "price": "0.01"}},
    ],
)
def test_metadata_never_infers_missing_or_derivative_capabilities(
    change: dict[str, object],
) -> None:
    assert is_refusal(
        SpotMarket.from_ccxt_market({**metadata(), **change}, precision_mode="TICK_SIZE")
    )


@pytest.mark.parametrize("mode", [None, "DECIMAL_PLACES", "SIGNIFICANT_DIGITS", 4])
def test_other_precision_modes_need_a_separate_declared_adapter(mode: object) -> None:
    assert is_refusal(SpotMarket.from_ccxt_market(metadata(), precision_mode=mode))


def test_exact_arithmetic_is_independent_of_callers_decimal_context() -> None:
    from decimal import localcontext

    parsed = SpotMarket.from_ccxt_market(metadata(), precision_mode="TICK_SIZE")
    assert is_ok(parsed)
    with localcontext() as context:
        context.prec = 3
        assert is_ok(parsed.value.validate_order("0.12345678", "12345.12345678"))
