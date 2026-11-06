"""Numbers carry a measure and convert only through a market's record (Part A slice A3, QML-05)."""

from __future__ import annotations

import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

import pytest
from qmf.core.exact import ExactRational, Money, PriceDelta, Quantity, UnitKind
from qmf.core.refusal import Ok, RefusalCategory, TypedRefusal
from qml.numbers import (
    InstrumentRecord,
    atr_multiple,
    check_numbers,
    distance,
    from_atr,
    instrument,
    lots,
    parse_record,
    value_factor,
)
from qml.unit import parse
from qml.unit.model import Measure, Unit

_HERE = Path(__file__).resolve().parent
_DUMMY = _HERE.parent / "src" / "qml" / "unit" / "templates" / "dummy-trend-pullback.json"


def _record_document(name: str) -> dict[str, Any]:
    text = (_HERE / "fixtures" / "records" / f"{name}.json").read_text("utf-8")
    return cast(dict[str, Any], json.loads(text))


def _record(name: str) -> InstrumentRecord:
    parsed = parse_record(_record_document(name))
    assert isinstance(parsed, Ok), parsed
    return parsed.value


EURUSD, USDJPY, XAUUSD = _record("eurusd"), _record("usdjpy"), _record("xauusd")
RECORDS = {"fx.eurusd": EURUSD, "metal.xauusd": XAUUSD}


_DROP = object()


def _unit(*edits: tuple[str, object]) -> Unit:
    document = cast(dict[str, Any], json.loads(_DUMMY.read_text("utf-8")))
    for path, value in edits:
        *parents, last = path.split("/")
        target: Any = document
        for part in parents:
            target = target[int(part) if part.isdigit() else part]
        if value is _DROP:
            del target[last]
        else:
            target[last] = value
    parsed = parse(document)
    assert parsed.problems == (), parsed.problems
    assert parsed.unit is not None
    return parsed.unit


def _errors(unit: Unit) -> set[tuple[str, str]]:
    return {(p.kind.value, p.where[0]) for p in check_numbers(unit, RECORDS).errors}


def test_broken_document_1_a_stop_buffer_in_pips_on_gold_is_one_error_naming_the_record() -> None:
    result = check_numbers(_unit(("numbers/stop_buffer/measure", "pips")), RECORDS)

    assert [(p.kind.value, p.where) for p in result.errors] == [
        ("no_pip", ("/numbers/stop_buffer/measure",))
    ]
    assert "icmarkets-ctrader:XAUUSD@1" in result.errors[0].message


def test_broken_document_3_an_ema_period_above_its_range_is_one_error_at_its_default() -> None:
    result = check_numbers(_unit(("numbers/ema_period/default", "400")), RECORDS)

    assert [(p.kind.value, p.where) for p in result.errors] == [
        ("outside_range", ("/numbers/ema_period/default",))
    ]


def test_a_percent_written_as_a_whole_percent_is_refused_with_the_fraction_rule() -> None:
    unit = _unit(
        ("numbers/risk_fraction/range", {"min": "0.01", "max": "5", "step": "0.01"}),
        ("numbers/risk_fraction/default", "0.5"),
    )

    result = check_numbers(unit, RECORDS)

    assert [(p.kind.value, p.where[0]) for p in result.errors] == [
        ("outside_measure", "/numbers/risk_fraction/range/max")
    ]
    assert '"0.005"' in result.errors[0].hint


_MOTION = {"mode": "shrink_from_own_trades", "min_count": 20, "step_limit": 1}
BROKEN = [
    (
        "a fixed number that moves",
        [("numbers/ema_period/motion", {"mode": "scaled"})],
        {("motion_not_allowed", "/numbers/ema_period/motion/mode")},
    ),
    (
        "a calibrated number with no cadence and no shrink",
        [("numbers/min_trend_strength/motion", _MOTION)],
        {
            ("motion_incomplete", "/numbers/min_trend_strength/motion/cadence"),
            ("motion_incomplete", "/numbers/min_trend_strength/motion/shrink_k"),
        },
    ),
    (
        "a step that does not divide the range",
        [("numbers/target_r/range", {"min": "0.5", "max": "10", "step": "0.3"})],
        {("bad_range", "/numbers/target_r/range/step")},
    ),
    (
        "a numeric number with no range",
        [("numbers/time_out_bars/range", _DROP)],
        {("range_missing", "/numbers/time_out_bars/range")},
    ),
    (
        "half a bar",
        [("numbers/time_out_bars/default", "47.5")],
        {("not_in_measure", "/numbers/time_out_bars/default")},
    ),
    (
        "a flag with a range and a non-flag default",
        [("numbers/target_r/measure", "flag"), ("numbers/target_r/default", "yes")],
        {
            ("range_not_allowed", "/numbers/target_r/range"),
            ("not_in_measure", "/numbers/target_r/default"),
        },
    ),
    (
        "market settings for an unknown number and outside a range",
        [("markets/0/settings", {"ema_periodd": "50", "ema_period": "10"})],
        {
            ("undeclared_number", "/markets/0/settings/ema_periodd"),
            ("outside_range", "/markets/0/settings/ema_period"),
        },
    ),
]


@pytest.mark.parametrize(("name", "edits", "expected"), BROKEN, ids=[b[0] for b in BROKEN])
def test_layer_c_names_every_number_problem_with_its_pointer(
    name: str, edits: list[tuple[str, object]], expected: set[tuple[str, str]]
) -> None:
    assert _errors(_unit(*edits)) == expected, name


def test_a_pips_number_with_no_record_for_a_market_names_that_market() -> None:
    unit = _unit(("numbers/stop_buffer/measure", "pips"))

    result = check_numbers(unit, {"fx.eurusd": EURUSD})

    assert [(p.kind.value, p.where[0]) for p in result.errors] == [
        ("no_record", "/numbers/stop_buffer/measure")
    ]
    assert "metal.xauusd" in result.errors[0].message


def test_a_20_pip_stop_converts_on_eurusd_and_is_refused_on_xauusd() -> None:
    euro = distance(Decimal("20"), Measure.PIPS, EURUSD)
    gold = distance(Decimal("20"), Measure.PIPS, XAUUSD)

    assert euro == Ok(PriceDelta(200, instrument(EURUSD), 5))
    assert isinstance(gold, TypedRefusal)
    assert gold.category is RefusalCategory.UNAVAILABLE_DEPENDENCY
    assert gold.context["field"] == "pip"
    assert gold.context["record"] == "icmarkets-ctrader:XAUUSD@1"


def test_one_distance_through_three_records_is_equal_in_atr_multiples() -> None:
    atrs = {
        "EURUSD": (EURUSD, Decimal("100")),
        "USDJPY": (USDJPY, Decimal("150")),
        "XAUUSD": (XAUUSD, Decimal("300")),
    }
    ticks_per_stop: dict[str, int] = {}
    multiples: dict[str, object] = {}
    for symbol, (record, atr_ticks) in atrs.items():
        atr = distance(atr_ticks, Measure.TICKS, record)
        assert isinstance(atr, Ok)
        stop = from_atr(Decimal("1.5"), atr.value)
        assert isinstance(stop, Ok)
        ticks_per_stop[symbol] = int(stop.value.as_fraction() / Fraction(record.tick_size))
        on_grid = distance(Decimal(ticks_per_stop[symbol]), Measure.TICKS, record)
        assert isinstance(on_grid, Ok)
        multiples[symbol] = atr_multiple(on_grid.value, atr.value)

    assert ticks_per_stop == {"EURUSD": 150, "USDJPY": 225, "XAUUSD": 450}
    three_halves = Ok(ExactRational(3, 2, UnitKind.DIMENSIONLESS_RATIO))
    assert multiples == {"EURUSD": three_halves, "USDJPY": three_halves, "XAUUSD": three_halves}


def test_a_distance_off_the_tick_grid_is_refused() -> None:
    refused = distance(Decimal("0.000015"), Measure.PRICE_DISTANCE, EURUSD)

    assert isinstance(refused, TypedRefusal)
    assert refused.context["field"] == "amount"


def test_lots_round_down_to_the_step_and_refuse_below_the_minimum() -> None:
    assert lots(Decimal("0.537"), EURUSD) == Ok(Quantity(53, "lot", 2))
    below = lots(Decimal("0.009"), EURUSD)
    assert isinstance(below, TypedRefusal)
    assert "minimum lot of 0.01" in str(below.context["reason"])


def test_lots_round_down_exactly_past_28_digits() -> None:
    sized = lots(Decimal("12345678901234567890123456789.01"), XAUUSD)

    assert sized == Ok(Quantity(1234567890123456789012345678901, "lot", 2))


def test_a_range_past_28_digits_is_checked_exactly() -> None:
    wide = {"min": "0", "max": "100000000000000000000", "step": "0.0000000001"}
    off = {"min": "0", "max": "100000000000000000000.00000000005", "step": "0.0000000001"}

    assert _errors(_unit(("numbers/target_r/range", wide))) == set()
    assert _errors(_unit(("numbers/target_r/range", off))) == {
        ("bad_range", "/numbers/target_r/range/step")
    }


def test_twenty_pips_on_one_eurusd_lot_is_200_dollars() -> None:
    stop = distance(Decimal("20"), Measure.PIPS, EURUSD)
    assert isinstance(stop, Ok)

    money = stop.value.to_money(value_factor(EURUSD), Quantity(100, "lot", 2), scale=2)

    assert money == Ok(Money(20000, "USD", 2))


def test_a_record_missing_keys_is_refused_naming_every_one() -> None:
    document = _record_document("xauusd")
    del document["tick_size"]
    document["class"] = "metals"

    refused = parse_record(document)

    assert isinstance(refused, TypedRefusal)
    assert refused.context["problems"] == (
        "/class: expected one of fx, metal, index_cfd, commodity_cfd, stock_cfd, future, perp, "
        "spot_crypto, stock",
        "/tick_size: the required key is missing",
    )

