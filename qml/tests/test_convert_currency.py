"""One converter spells the venue's quantity in the account's currency (AD-10, CHECK B5)."""

from __future__ import annotations

import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

from qmf.core.chrono import Instant
from qmf.core.refusal import Ok
from qmf.risk.facts import Fact
from qml.blocks.api import Amount
from qml.numbers import (
    ConversionRef,
    InstrumentRecord,
    RoundRule,
    parse_record,
    to_quantity,
)

_HERE = Path(__file__).resolve().parent
_RECORDS = _HERE / "fixtures" / "records"
_NOW = Instant(1_000_000_000_000)
_RULE = RoundRule(now=_NOW, rate_stale_s=Decimal("30"))
_MONEY = Amount(kind="money_at_risk", value=Decimal("500"), basis="gross_at_stop")


def _record(name: str, edits: dict[str, object] | None = None) -> InstrumentRecord:
    document = cast(
        "dict[str, Any]", json.loads((_RECORDS / f"{name}.json").read_text("utf-8"))
    )
    document.update(edits or {})
    parsed = parse_record(document)
    assert isinstance(parsed, Ok), parsed
    return parsed.value


def _exact(value: Decimal | Fraction) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(*value.as_integer_ratio())


def _fact(rate: Decimal | Fraction, age_s: int = 0) -> Fact:
    return Fact(
        value=rate,
        ts=Instant(_NOW.value_ns - age_s * 1_000_000_000),
        fail_mode="open",
        source="node:replay",
        state="ok",
    )


def test_loss_at_the_stop_equals_the_amount_on_four_markets() -> None:
    eurusd = _record("eurusd")
    xauusd = _record("xauusd")
    usdjpy = _record("usdjpy")
    eurjpy = _record(
        "usdjpy",
        {
            "symbol": "EURJPY",
            "market_id": "eurjpy",
            "conversions": {"USD": {"market_id": "usdjpy", "invert": True}},
        },
    )
    assert eurjpy.conversions == {"USD": ConversionRef(market_id="usdjpy", invert=True)}

    cases = [
        (eurusd, Decimal("1.1000"), Decimal("1.0950"), Fraction(1), Decimal("1.00")),
        (xauusd, Decimal("2000"), Decimal("1995"), Fraction(1), Decimal("1.00")),
        (usdjpy, Decimal("150.00"), Decimal("149.50"), Fraction(1, 150), Decimal("1.50")),
        (eurjpy, Decimal("160.00"), Decimal("159.50"), Fraction(1, 150), Decimal("1.50")),
    ]
    for record, entry, stop, rate, expected in cases:
        converted = to_quantity(_MONEY, entry, stop, record, _fact(rate), _RULE)

        assert converted.skipped is None, record.symbol
        quantity = converted.quantity
        assert quantity is not None, record.symbol
        assert quantity == expected, record.symbol
        risk = _exact(quantity) * _exact(abs(entry - stop)) * _exact(record.value_per_point) * rate
        assert risk == 500, record.symbol


def test_a_stale_rate_skips_by_name() -> None:
    usdjpy = _record("usdjpy")
    entry, stop = Decimal("150.00"), Decimal("149.50")

    stale = to_quantity(_MONEY, entry, stop, usdjpy, _fact(Fraction(1, 150), age_s=31), _RULE)
    assert stale.skipped == "rate_stale"
    assert stale.quantity is None

    absent = to_quantity(_MONEY, entry, stop, usdjpy, None, _RULE)
    assert absent.skipped == "rate_absent"
    assert absent.quantity is None

    fresh = to_quantity(_MONEY, entry, stop, usdjpy, _fact(Fraction(1, 150), age_s=10), _RULE)
    assert fresh.skipped is None
    assert fresh.quantity == Decimal("1.50")


def test_rounding_goes_down_and_the_residue_is_real() -> None:
    eurusd = _record("eurusd")
    rounded = Amount(kind="quantity", value=Decimal("1.237"), basis="gross_at_stop")

    converted = to_quantity(
        rounded, Decimal("1.1000"), Decimal("1.0950"), eurusd, _fact(Fraction(1)), _RULE
    )

    assert converted.skipped is None
    assert converted.quantity == Decimal("1.23")
    assert converted.residue_r == Decimal("0.007") / Decimal("1.237")
    assert converted.residue_r > 0
