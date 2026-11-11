"""The named modifiers on the size: two factors multiply, and one outside its range is refused.

RC-21's Verify, unit block. The unit is the shipped dummy at its own numbers, priced on one EURUSD
entry: 100000 equity at the default 0.005 risks 500 at the stop 0.0050 away, and one lot is 500 at
that distance. Two modifiers answer 0.5 and 1.5, so 500 becomes 375 and the venue is sent 0.75
lots. A third reads 3 against a range of 0 to 2, and the row names `factor_out_of_range` while
that modifier reads neutral with its fail mode.

The last three tests answer a shape `Factor` states: a float factor, a factor with no range, and a
NaN factor, which is type-correct and still unusable. Each is refused by name with the block on the
fault, benches the unit, and the position held on the other market still runs its exit on that bar.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, cast

from qmf.core.chrono import Instant
from qmf.risk.unit_intent import UNIT_INTENT_FORMAT_VERSION, UnitExitIntent
from qml.blocks.api import Amount, Factor
from qml.compile import CompiledUnit
from qml.protocol.unit import HostedUnit, Proposal, QuoteBar, Surface
from qml.receipt import explain_size, stored_row
from qml.unit.model import Side

import test_price_call as price
from test_compile_dummy import _compiled, _document, _instants, _ok, _slice
from test_fault_wall_unit import _Latest

_EQUITY = price._EQUITY
"""100000, the account the sizer reads and the fixture the section's literals assume."""
_ROW = "row-modifiers"
_START = price._START


def _with_modifiers(levels: Sequence[tuple[str, str]], time_out: str | None = None) -> CompiledUnit:
    """The shipped dummy with one `level-factor@1` row per (name, level), in that order."""
    document = cast("dict[str, Any]", _document())
    if time_out is not None:
        numbers = cast("dict[str, dict[str, Any]]", document["numbers"])
        numbers["time_out_bars"]["default"] = time_out
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


def _holding(
    compiled: CompiledUnit, bars: Mapping[str, Sequence[QuoteBar]], opened_at: Instant
) -> HostedUnit:
    """The dummy hosted on both markets, with a position held on EURUSD from the first bar."""
    held = price.hosted.OwnPosition(
        "pos-1",
        Side.LONG,
        Decimal("0.10"),
        Decimal("1.10000"),
        compiled.logic_fingerprint,
        opened_at,
    )
    surfaces: dict[str, Surface] = {
        "account": price._At(price.hosted.Account(_EQUITY)),
        "own_journal": price._At(()),
    }
    for market, series in bars.items():
        surfaces[f"bars:m15:{market}"] = _Latest(series)
        surfaces[f"own_position:{market}"] = price._At((held,) if market == "fx.eurusd" else ())
    return price._host(compiled, surfaces)


def _held_unit(answer: object) -> tuple[HostedUnit, list[Instant]]:
    """The dummy with one `odd` modifier row, answered by `answer`, and a position held on EURUSD."""
    compiled = _with_modifiers([("odd", "1")], time_out="5")
    bars = _slice()
    instants = _instants(bars)
    unit = _holding(compiled, bars, instants[0])
    for market in unit._core.markets:  # pyright: ignore[reportPrivateUsage]
        market.instances["modifier.odd"] = answer  # pyright: ignore[reportArgumentType]
    return unit, instants


class _Malformed:
    """A Library modifier that answers a `Factor` the core cannot read.

    `Factor` declares a decimal value and a two-decimal range, and nothing validates either, so
    these are the two answers the review found a `TypeError` for.
    """

    def __init__(self, value: object, bounds: object) -> None:
        self._answer = Factor(
            cast("Any", value), cast("Any", bounds), "a factor the core cannot read"
        )

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
        return self._answer

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


def test_a_float_factor_keeps_the_held_exit_and_names_the_block() -> None:
    """A float factor is refused by name, and the exit on that bar still runs."""
    unit, instants = _held_unit(_Malformed(0.5, (Decimal("0"), Decimal("2"))))

    steps = [_ok(unit.on_instant(instant)) for instant in instants[:5]]
    exits = [
        (intent.kind.value, intent.reason_code.code)
        for step in steps
        for intent in step.intents
        if isinstance(intent, UnitExitIntent)
    ]
    assert exits == [("close_full", "time")], "the held position's exit closes on that bar"
    priced = unit.price(price._proposal("0.005"), price.hosted.Account(_EQUITY))

    assert priced.code == "unit_fault"
    assert priced.intent is None
    assert unit._core.benched is True, "a fault benches the unit's entries"
    assert priced.row.reason == "sizer: unit_fault (the modifier odd answered no usable factor)"
    assert [(fault.block, fault.phase.value) for fault in unit._core.pending_faults] == [
        ("level-factor@1", "price")
    ]


def test_a_factor_with_no_range_keeps_the_held_exit_and_names_the_block() -> None:
    """A factor with no range is refused by name, and the exit on that bar still runs."""
    unit, instants = _held_unit(_Malformed(Decimal("0.5"), None))

    steps = [_ok(unit.on_instant(instant)) for instant in instants[:5]]
    exits = [
        (intent.kind.value, intent.reason_code.code)
        for step in steps
        for intent in step.intents
        if isinstance(intent, UnitExitIntent)
    ]
    assert exits == [("close_full", "time")], "the held position's exit closes on that bar"
    priced = unit.price(price._proposal("0.005"), price.hosted.Account(_EQUITY))

    assert priced.code == "unit_fault"
    assert priced.intent is None
    assert unit._core.benched is True, "a fault benches the unit's entries"
    assert priced.row.reason == "sizer: unit_fault (the modifier odd answered no usable factor)"
    assert [(fault.block, fault.phase.value) for fault in unit._core.pending_faults] == [
        ("level-factor@1", "price")
    ]


class _NaN(_Malformed):
    """A `Factor` whose factor is NaN, built with no cast because `Decimal` is its stated type."""

    def __init__(self) -> None:
        self._answer = Factor(
            Decimal("NaN"), (Decimal("0"), Decimal("2")), "the factor is not a number"
        )


def test_a_nan_factor_keeps_the_held_exit_and_names_the_block() -> None:
    """A NaN factor is refused by name, and the exit on that bar still runs."""
    unit, instants = _held_unit(_NaN())

    steps = [_ok(unit.on_instant(instant)) for instant in instants[:5]]
    exits = [
        (intent.kind.value, intent.reason_code.code)
        for step in steps
        for intent in step.intents
        if isinstance(intent, UnitExitIntent)
    ]
    assert exits == [("close_full", "time")], "the held position's exit closes on that bar"
    assert unit._core.benched is False, "no fault on the held bars has benched the unit yet"
    priced = unit.price(price._proposal("0.005"), price.hosted.Account(_EQUITY))

    assert priced.code == "unit_fault"
    assert priced.intent is None
    assert unit._core.benched is True, "a fault benches the unit's entries"
    assert priced.row.reason == "sizer: unit_fault (the modifier odd answered no usable factor)"
    assert [(fault.block, fault.phase.value) for fault in unit._core.pending_faults] == [
        ("level-factor@1", "price")
    ]
