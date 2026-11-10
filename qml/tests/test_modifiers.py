"""The named modifiers on the size: two factors multiply, and one outside its range is refused.

RC-21's Verify, unit block. The unit is the shipped dummy at its own numbers, priced on one EURUSD
entry: 100000 equity at the default 0.005 risks 500 at the stop 0.0050 away, and one lot is 500 at
that distance. Two modifiers answer 0.5 and 1.5, so 500 becomes 375 and the venue is sent 0.75
lots. A third reads 3 against a range of 0 to 2, and the row names `factor_out_of_range` while
that modifier reads neutral with its fail mode.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, cast

from qmf.risk.unit_intent import UNIT_INTENT_FORMAT_VERSION
from qml.blocks.api import Amount
from qml.compile import CompiledUnit
from qml.protocol.unit import HostedUnit, Proposal
from qml.receipt import explain_size, stored_row
from qml.unit.model import Side

import test_price_call as price
from test_compile_dummy import _compiled, _document

_EQUITY = price._EQUITY
"""100000, the account the sizer reads and the fixture the section's literals assume."""
_ROW = "row-modifiers"
_START = price._START


def _with_modifiers(levels: Sequence[tuple[str, str]]) -> CompiledUnit:
    """The shipped dummy with one `level-factor@1` row per (name, level), in that order."""
    document = cast("dict[str, Any]", _document())
    document["modifiers"] = [
        {
            "name": name,
            "block": "level-factor@1",
            "params": {"level": {"value": level}, "max_level": {"value": "2"}},
            "inputs": {},
        }
        for name, level in levels
    ]
    return _compiled(document)


def _unit(levels: Sequence[tuple[str, str]]) -> tuple[CompiledUnit, HostedUnit]:
    compiled = _with_modifiers(levels)
    return compiled, price._host(compiled, price._surfaces())


def _proposal(compiled: CompiledUnit) -> Proposal:
    """One EURUSD entry at the dummy's own fraction: 500 at risk, 0.0050 from its stop.

    The wire is the one the unit itself mints at an entry, so the size reaches the admission
    door with every field it reads rather than a stub the door would refuse.
    """
    target = price._target()
    return Proposal(
        wire={
            "contract_format_version": UNIT_INTENT_FORMAT_VERSION,
            "intent_family": "entry",
            "unit": {
                "unit_id": compiled.unit.unit_id,
                "version_ref": compiled.document_fingerprint.value,
                "compiled_fingerprint": compiled.compiled_fingerprint.value,
            },
            "instrument": {"venue": "icmarkets-ctrader", "symbol": "EURUSD"},
            "market_id": "fx.eurusd",
            "direction": "long",
            "reason_code": {"code": compiled.unit.family_id, "book_family": "unit"},
            "execution_target": {
                "role": target.role.value,
                "venue_id": target.venue_id.value,
                "account_id": target.account_id,
            },
            "order": {"type": "market"},
            "protection": {
                "stop": "1.09500",
                "targets": [{"price": "1.11000", "fraction": "1/1"}],
            },
            "not_before": _START.value_ns,
            "placeholder_labels": list(compiled.placeholders),
            "decision_row_id": _ROW,
        },
        row=price.hosted.DecisionRow(
            row_id=_ROW,
            instant=_START,
            market_id="fx.eurusd",
            side=Side.LONG,
            outcome="taken",
            slot_trail=(),
            numbers_in_force={"risk_fraction": Decimal("0.005")},
            reason="all slots hold",
        ),
        market_id="fx.eurusd",
        side=Side.LONG,
        entry_price=Decimal("1.10000"),
        stop=Decimal("1.09500"),
        params={"fraction": Decimal("0.005")},
        record=price._record("eurusd"),
    )


def test_two_modifiers_multiply() -> None:
    """0.5 and 1.5 on 500 at risk give 375 and 0.75 lots, and the trail prints both factors."""
    compiled, unit = _unit([("half", "0.5"), ("press", "1.5")])

    priced = unit.price(_proposal(compiled), price.hosted.Account(_EQUITY))
    trail = explain_size(stored_row(priced.row))

    assert priced.code is None
    assert priced.intent is not None
    assert priced.row.steps["wanted"] == Amount(
        kind="money_at_risk", value=Decimal("500"), basis="gross_at_stop"
    )
    assert priced.row.steps["modified"].value == Decimal("375")
    assert priced.row.steps["approved"] == Amount(
        kind="quantity", value=Decimal("0.75"), basis="gross_at_stop"
    )
    assert [(seen.name, seen.value) for seen in trail.factors] == [
        ("half", "0.5"),
        ("press", "1.5"),
    ]
    assert [seen.reason for seen in trail.factors] == [
        "the level 0.5 sits inside 0 to 2",
        "the level 1.5 sits inside 0 to 2",
    ]
    assert [seen.range for seen in trail.factors] == ["0 to 2", "0 to 2"]
    assert [(step.name, Decimal(step.value)) for step in trail.steps] == [
        ("wanted", Decimal("500")),
        ("modified", Decimal("375")),
        ("approved", Decimal("0.75")),
    ]
    assert trail.verdicts == (
        "sizer: none",
        "modifier half: none",
        "modifier press: none",
        "converter: none",
        "size_band: none",
    )


def test_a_factor_outside_its_range_is_refused_by_name() -> None:
    """3 on 0 to 2 answers `factor_out_of_range`, and that modifier reads neutral with its fail mode."""
    compiled, unit = _unit([("over", "3")])

    priced = unit.price(_proposal(compiled), price.hosted.Account(_EQUITY))
    trail = explain_size(stored_row(priced.row))

    assert priced.code == "factor_out_of_range"
    assert priced.intent is None
    assert priced.row.outcome == "skipped"
    assert priced.row.reason == "sizer: factor_out_of_range (the level 3 sits inside 0 to 2)"
    assert len(trail.factors) == 1
    seen = trail.factors[0]
    assert (seen.name, seen.value, seen.code, seen.fail_mode) == (
        "over",
        "1",
        "factor_out_of_range",
        "neutral",
    )
    assert seen.range == "0 to 2"
    assert seen.reason == "the level 3 sits inside 0 to 2"
    assert trail.verdicts == ("sizer: none", "modifier over: refuse (factor_out_of_range)")
    assert priced.row.steps.keys() == {"wanted"}


def test_a_modifier_that_answers_nothing_reads_neutral() -> None:
    """A block with no answer reads 1 with its face mode, and the size is the sizer's own."""
    compiled, unit = _unit([("silent", "1")])
    for market in unit._core.markets:  # pyright: ignore[reportPrivateUsage]
        market.instances["modifier.silent"] = _Silent()  # pyright: ignore[reportArgumentType]

    priced = unit.price(_proposal(compiled), price.hosted.Account(_EQUITY))
    trail = explain_size(stored_row(priced.row))

    assert priced.code is None
    assert priced.row.steps["approved"].value == Decimal("1.00")
    assert [(seen.value, seen.code, seen.fail_mode) for seen in trail.factors] == [
        ("1", "neutral", "neutral")
    ]
    assert trail.verdicts == (
        "sizer: none",
        "modifier silent: neutral",
        "converter: none",
        "size_band: none",
    )


class _Silent:
    """A modifier whose evidence is not there yet, as a warm-up or a cold row answers."""

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> None:
        del evidence

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


def test_a_modifier_that_raises_is_a_fault_named_by_its_block() -> None:
    """A raise in a modifier is a `unit_fault` blamed on that block, and its entries bench."""
    compiled, unit = _unit([("broken", "1")])
    for market in unit._core.markets:  # pyright: ignore[reportPrivateUsage]
        market.instances["modifier.broken"] = _Raising()  # pyright: ignore[reportArgumentType]

    priced = unit.price(_proposal(compiled), price.hosted.Account(_EQUITY))

    assert priced.code == "unit_fault"
    assert priced.intent is None
    assert [(fault.block, fault.phase.value) for fault in unit._core.pending_faults] == [
        ("level-factor@1", "price")
    ]
    assert unit._core.benched is True  # pyright: ignore[reportPrivateUsage]


class _Raising:
    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> object:
        del evidence
        raise ValueError("the block cannot read this bar")

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state
