"""CT-23 format 3, the unit's own sized intent, and the Book door left as it was.

The Book door cases C to F come from Level 0 ``blast-radius.md`` item 1: the old door
still drops an unknown key and still refuses a format-3 stamp.
"""

from __future__ import annotations

from fractions import Fraction
from typing import cast

import pytest
from qmf.core import (
    Instrument,
    Price,
    Quantity,
    RefusalCategory,
    TypedRefusal,
    VenueId,
    is_ok,
)
from qmf.risk import (
    UnitEntryIntent,
    UnitExitIntent,
    UnitExitKind,
    check_amendment_tightens,
    parse_unit_intent,
)
from qmf.risk.door import Direction, EntryIntent, ReasonCode, parse_inbound_intent
from qmf.risk.paper import ExecutionTarget

_FP_UNIT = "fp1:sha256:" + "a" * 64
_FP_OPENED = "fp1:sha256:" + "b" * 64
_EURUSD = {"venue": "ctrader", "symbol": "EURUSD"}


def _full_entry() -> dict[str, object]:
    return {
        "contract_format_version": 3,
        "intent_family": "entry",
        "unit": {
            "unit_id": "dummy-breakout",
            "version_ref": "v3",
            "compiled_fingerprint": _FP_UNIT,
        },
        "instrument": dict(_EURUSD),
        "market_id": "fx:EURUSD",
        "direction": "long",
        "reason_code": {"code": "breakout", "book_family": "unit"},
        "execution_target": {"role": "demo", "venue_id": "ctrader", "account_id": "acct-7"},
        "order": {
            "type": "stop_limit",
            "limit_price": "1.08460",
            "stop_price": "1.08450",
            "time_in_force": "gtc",
            "expires_after_s": 900,
        },
        "quantity": "1.23",
        "sizer_receipt": {
            "inputs_used": ["equity", "stop_distance", "lot_step"],
            "rounding_residue_r": "-3/250",
        },
        "protection": {
            "stop": "1.08200",
            "targets": [
                {"price": "1.08700", "fraction": "1/2"},
                {"price": "1.09000", "fraction": "1/2"},
            ],
            "time_exit_bars": 48,
        },
        "not_before": 1_700_000_000_000_000_000,
        "placeholder_labels": ["sizer"],
        "decision_row_id": "row-41",
    }


def _bare_entry() -> dict[str, object]:
    wire = _full_entry()
    wire["order"] = {"type": "market"}
    wire["protection"] = {"stop": "none_declared", "targets": []}
    wire["placeholder_labels"] = []
    return wire


def _amend(stop: str) -> dict[str, object]:
    return {
        "contract_format_version": 3,
        "intent_family": "exit",
        "kind": "amend_protection",
        "position_ref": {
            "position_id": "pos-9",
            "instrument": dict(_EURUSD),
            "opened_by": _FP_OPENED,
        },
        "reason_code": {"code": "trail", "book_family": "unit"},
        "decision_row_id": "row-52",
        "stop": stop,
        "targets": [],
    }


def _parsed(wire: dict[str, object]) -> UnitEntryIntent | UnitExitIntent:
    result = parse_unit_intent(wire)
    assert is_ok(result), result
    return result.value


def _refusal(wire: object) -> TypedRefusal:
    result = parse_unit_intent(wire)
    assert isinstance(result, TypedRefusal)
    return result


def _eurusd() -> Instrument:
    return Instrument(venue=VenueId(value="ctrader"), symbol="EURUSD")


@pytest.mark.parametrize(
    "wire", [_full_entry(), _bare_entry()], ids=["every-optional", "none-optional"]
)
def test_entry_round_trips_with_its_size_intact(wire: dict[str, object]) -> None:
    entry = _parsed(wire)
    assert isinstance(entry, UnitEntryIntent)
    assert entry.quantity == Quantity(value=123, unit="lot", scale=2)
    assert entry.to_wire() == wire
    again = _parsed(entry.to_wire())
    assert again == entry


def test_entry_keeps_protection_and_not_before() -> None:
    entry = _parsed(_full_entry())
    assert isinstance(entry, UnitEntryIntent)
    assert entry.protection.stop == Price(value=108200, instrument=_eurusd(), scale=5)
    assert [t.fraction.as_fraction() for t in entry.protection.targets] == [Fraction(1, 2)] * 2
    assert entry.not_before.value_ns == 1_700_000_000_000_000_000
    assert entry.sizer_receipt.rounding_residue_r.as_fraction() == Fraction(-3, 250)
    assert entry.protection.r_defined is True
    bare = _parsed(_bare_entry())
    assert isinstance(bare, UnitEntryIntent)
    assert bare.protection.r_defined is False


def test_trailing_zeros_keep_the_scale_to_the_last_digit() -> None:
    wire = _full_entry()
    wire["quantity"] = "0.10000"
    entry = _parsed(wire)
    assert isinstance(entry, UnitEntryIntent)
    assert entry.quantity == Quantity(value=10000, unit="lot", scale=5)
    assert entry.to_wire()["quantity"] == "0.10000"


@pytest.mark.parametrize("version", [1, 2, 4, True, "3"])
def test_unit_parser_refuses_every_format_but_3(version: object) -> None:
    wire = _full_entry()
    wire["contract_format_version"] = version
    refusal = _refusal(wire)
    assert refusal.category is RefusalCategory.UNSUPPORTED_CAPABILITY
    assert refusal.context["field"] == "contract_format_version"


def test_unit_parser_refuses_an_unstamped_mapping() -> None:
    wire = _full_entry()
    del wire["contract_format_version"]
    refusal = _refusal(wire)
    assert refusal.category is RefusalCategory.UNSUPPORTED_CAPABILITY
    assert refusal.context["field"] == "contract_format_version"


@pytest.mark.parametrize(
    ("path", "key", "expect_field"),
    [((), "requested_quantity", "intent"), (("protection",), "trail", "protection")],
)
def test_unknown_key_is_refused_never_dropped(
    path: tuple[str, ...], key: str, expect_field: str
) -> None:
    wire = _full_entry()
    part = wire
    for step in path:
        part = cast("dict[str, object]", part[step])
    part[key] = "1"
    refusal = _refusal(wire)
    assert refusal.category is RefusalCategory.INVALID_INPUT
    assert refusal.context["field"] == expect_field
    assert refusal.context["unknown"] == (key,)


@pytest.mark.parametrize("quantity", [0.37, 1, "0", "-1.00", "1e2"])
def test_quantity_is_an_exact_positive_decimal_string(quantity: object) -> None:
    wire = _full_entry()
    wire["quantity"] = quantity
    refusal = _refusal(wire)
    assert refusal.context["field"] == "quantity"


def test_a_4400_digit_quantity_is_refused_not_raised() -> None:
    wire = _full_entry()
    wire["quantity"] = "1" * 4400
    refusal = _refusal(wire)
    assert refusal.category is RefusalCategory.INVALID_INPUT
    assert refusal.context["field"] == "quantity"


def test_a_4400_digit_ratio_is_refused_not_raised() -> None:
    wire = _full_entry()
    cast("dict[str, object]", wire["sizer_receipt"])["rounding_residue_r"] = "1" * 4400 + "/3"
    refusal = _refusal(wire)
    assert refusal.category is RefusalCategory.INVALID_INPUT
    assert refusal.context["field"] == "sizer_receipt.rounding_residue_r"


def test_a_long_stop_above_the_order_price_is_refused() -> None:
    wire = _full_entry()
    cast("dict[str, object]", wire["protection"])["stop"] = "1.08500"
    assert _refusal(wire).context["field"] == "protection.stop"


@pytest.mark.parametrize(
    ("extra", "kind"),
    [({}, UnitExitKind.CLOSE_FULL), ({"quantity": "0.50"}, UnitExitKind.CLOSE_PARTIAL)],
)
def test_close_exits_round_trip(extra: dict[str, object], kind: UnitExitKind) -> None:
    wire = _amend("1.08300")
    del wire["stop"], wire["targets"]
    wire["kind"] = kind.value
    wire.update(extra)
    intent = _parsed(wire)
    assert isinstance(intent, UnitExitIntent)
    assert intent.kind is kind
    assert intent.to_wire() == wire


def test_a_close_full_carrying_a_quantity_is_refused() -> None:
    wire = _amend("1.08300")
    del wire["stop"], wire["targets"]
    wire["kind"] = "close_full"
    wire["quantity"] = "0.50"
    assert _refusal(wire).context["unknown"] == ("quantity",)


def _stop(text: str) -> Price:
    whole, _, fraction = text.partition(".")
    return Price(value=int(whole + fraction), instrument=_eurusd(), scale=len(fraction))


@pytest.mark.parametrize(
    ("direction", "current", "proposed"),
    [(Direction.LONG, "1.08200", "1.08199"), (Direction.SHORT, "1.08200", "1.08201")],
)
def test_an_amendment_that_widens_the_stop_by_one_tick_is_refused(
    direction: Direction, current: str, proposed: str
) -> None:
    amend = _parsed(_amend(proposed))
    assert _parsed(_amend(proposed)).to_wire() == _amend(proposed)
    result = check_amendment_tightens(amend, direction=direction, current_stop=_stop(current))
    assert isinstance(result, TypedRefusal)
    assert result.category is RefusalCategory.POLICY_REJECTION
    assert result.context["violation"] == "widen-stop"
    assert "may tighten a stop and never widen it" in str(result.context["reason"])


@pytest.mark.parametrize(
    ("direction", "current"),
    [(Direction.LONG, "1.08100"), (Direction.SHORT, "1.08300"), (Direction.LONG, "none_declared")],
)
def test_an_amendment_that_tightens_or_adds_a_stop_passes(
    direction: Direction, current: str
) -> None:
    amend = _parsed(_amend("1.08200"))
    current_stop: object = current if current == "none_declared" else _stop(current)
    assert is_ok(check_amendment_tightens(amend, direction=direction, current_stop=current_stop))


# --- the Book door, untouched (Level 0 blast-radius item 1) --------------------------


def _book_entry() -> EntryIntent:
    target = ExecutionTarget.try_create("live", VenueId(value="ctrader"), "acct-1")
    assert is_ok(target)
    result = EntryIntent.try_create(
        _eurusd(),
        Direction.LONG,
        ReasonCode(code="momentum-break", book_family="scalper-v1"),
        target.value,
    )
    assert is_ok(result)
    return result.value


def test_case_c_book_door_still_drops_an_unknown_size_key() -> None:
    result = parse_inbound_intent(
        {"intent_family": "entry", "entry": _book_entry(), "requested_quantity": "1.23"}
    )
    assert is_ok(result)
    assert result.value.entry == _book_entry()


def test_case_d_book_door_still_refuses_a_format_3_stamp() -> None:
    result = parse_inbound_intent(
        {"contract_format_version": 3, "intent_family": "entry", "entry": _book_entry()}
    )
    assert isinstance(result, TypedRefusal)
    assert result.category is RefusalCategory.UNSUPPORTED_CAPABILITY
    assert result.context["field"] == "contract_format_version"


def test_case_e_book_door_at_format_2_still_drops_an_unknown_size_key() -> None:
    result = parse_inbound_intent(
        {
            "contract_format_version": 2,
            "intent_family": "entry",
            "entry": _book_entry(),
            "requested_quantity": "1.23",
        }
    )
    assert is_ok(result)
    assert result.value.entry == _book_entry()


def test_case_f_book_door_refuses_a_unit_intent_wire_mapping() -> None:
    result = parse_inbound_intent(_full_entry())
    assert isinstance(result, TypedRefusal)
    assert result.category is RefusalCategory.UNSUPPORTED_CAPABILITY
    assert result.context["field"] == "contract_format_version"
