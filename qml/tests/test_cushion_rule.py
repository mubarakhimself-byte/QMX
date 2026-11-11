"""House money and its reverse: one `cushion-rule` on one cushion ledger in the fold (RC-22).

RC-22's Verify, unit block, on the shipped dummy priced at its own numbers: 100000 equity at the
default 0.005 risks 500 at the stop 0.0050 away, and one lot is 500 at that distance. The rule's
fixture is strength 1 and a reach of 200 R, the cushion that moves the size by one whole strength,
so the plan's "+100 on a base of 100" is half the reach: a realised +100 R since the day's anchor
gives 1.5, and a realised -50 R gives 0.75. The ledger is fed only by closed trades, so an open
profit never presses. A row switched off by a fact reads neutral, and the press gate holds a raise
while the unit's fold word is not ACTIVE.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from decimal import Decimal
from typing import Any, cast

import test_price_call as price
from qmf.core.chrono import Instant
from qmf.risk.controls import Cushion
from qml.blocks.api import Amount
from qml.compile import CompiledUnit
from qml.fold import Fold
from qml.motion.engine import ClosedTrade
from qml.protocol.unit import (
    HostedUnit,
    MotionSwitch,
    OwnPosition,
    Priced,
    Surface,
    TraceLevel,
    construct_unit,
)
from qml.receipt import explain_size, stored_row
from qml.unit.model import Side
from test_compile_dummy import _compiled, _document
from test_modifiers import _proposal

_START = price._START
_HOUR = 3_600 * 10**9


def _cushion(anchor: str, *, gated: bool = False) -> CompiledUnit:
    """The dummy with one `cushion-rule@1` row on a day anchor, and the press gate in front."""
    document = cast("dict[str, Any]", _document())
    gate: list[dict[str, Any]] = [
        {"name": "gate", "block": "press-gate@1", "params": {}, "inputs": {}}
    ]
    document["modifiers"] = (gate if gated else []) + [
        {
            "name": "cushion",
            "block": "cushion-rule@1",
            "params": {
                "strength": {"value": "1"},
                "reach": {"value": "200"},
                "anchor": {"value": "0" if anchor == "fixed" else "1"},
                "clock": {"value": "0"},
            },
            "inputs": {},
        }
    ]
    return _compiled(document)


def _trade(n: int, r: str) -> ClosedTrade:
    closed = Instant(_START.value_ns - (10 - n) * _HOUR)
    return ClosedTrade(
        trade_id=f"t{n:02d}",
        opened_at=closed,
        closed_at=closed,
        side=Side.LONG,
        market_id="fx.eurusd",
        world="replay",
        r_after_costs=Decimal(r),
        entry_stamps={},
    )


def _host(
    compiled: CompiledUnit,
    trades: Sequence[ClosedTrade],
    *,
    held: tuple[OwnPosition, ...] = (),
    equity: Decimal = price._EQUITY,
    risk_rows: Sequence[Mapping[str, object]] = (),
) -> HostedUnit:
    surfaces: dict[str, Surface] = {
        **price._surfaces(),
        "account": price._At(price.hosted.Account(equity)),
        "own_journal": price._At(tuple(trades)),
        "own_position:fx.eurusd": price._At(held),
    }
    unit = price._ok(
        construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id="run-cushion",
            execution_target=price._target(),
            trace_level=TraceLevel.EVERY_BAR,
            motion=MotionSwitch.OFF,
            risk_rows=risk_rows,
        )
    )
    price._ok(unit.on_instant(_START))
    return unit


def _priced(unit: HostedUnit, compiled: CompiledUnit, equity: Decimal = price._EQUITY) -> Priced:
    return unit.price(_proposal(compiled), price.hosted.Account(equity))


def _factor(priced: Priced) -> str:
    return explain_size(stored_row(priced.row)).factors[0].value


def test_a_fixed_anchor_presses_and_brakes() -> None:
    """+100 R since the day's anchor presses 500 to 750; -50 R brakes it to 375."""
    compiled = _cushion("fixed")

    won = _priced(_host(compiled, [_trade(1, "60"), _trade(2, "40")]), compiled)
    lost = _priced(_host(compiled, [_trade(1, "-50")]), compiled)

    assert (_factor(won), _factor(lost)) == ("1.5", "0.75")
    assert won.row.steps["modified"].value == Decimal("750")
    assert won.row.steps["approved"] == Amount(
        kind="quantity", value=Decimal("1.50"), basis="gross_at_stop"
    )
    assert lost.row.steps["approved"].value == Decimal("0.75")
    assert explain_size(stored_row(lost.row)).factors[0].reason == (
        "a cushion of -50 R since the day anchor, fixed, moves the size by 0.75"
    )


def test_a_peak_anchor_only_brakes() -> None:
    """The same trades on a running-peak anchor give 1 and 0.75: a win only raises the peak."""
    compiled = _cushion("running_peak")

    won = _priced(_host(compiled, [_trade(1, "60"), _trade(2, "40")]), compiled)
    lost = _priced(_host(compiled, [_trade(1, "-50")]), compiled)

    assert (_factor(won), _factor(lost)) == ("1", "0.75")
    assert won.row.steps["approved"].value == Decimal("1.00")
    assert lost.row.steps["approved"].value == Decimal("0.75")


def test_open_profit_never_presses() -> None:
    """An open +500 R lifts the account's equity but closes no trade, so the factor stays 1."""
    compiled = _cushion("fixed")
    open_long = OwnPosition(
        position_id="p1",
        side=Side.LONG,
        quantity=Decimal("1"),
        entry_price=Decimal("1.08000"),
        opened_by=compiled.compiled_fingerprint,
        opened_at=_START,
    )
    richer = price._EQUITY + Decimal("250000")

    priced = _priced(_host(compiled, [], held=(open_long,), equity=richer), compiled, richer)

    assert _factor(priced) == "1"
    assert explain_size(stored_row(priced.row)).factors[0].reason == (
        "a cushion of 0 R since the day anchor, fixed, moves the size by 1"
    )


def test_a_row_switched_off_by_a_fact_reads_neutral() -> None:
    """A row bound to `own.loss_streak` runs after a loss and reads `off` after a win."""
    compiled = _cushion("fixed")
    plan = compiled.plan
    switched = replace(
        compiled,
        plan=replace(plan, modifiers=(replace(plan.modifiers[0], enabled="own.loss_streak"),)),
    )

    on = _priced(_host(switched, [_trade(1, "-50")]), switched)
    off = _priced(_host(switched, [_trade(1, "100")]), switched)
    trail = explain_size(stored_row(off.row))

    assert _factor(on) == "0.75"
    assert [(seen.value, seen.code) for seen in trail.factors] == [("1", "off")]
    assert trail.verdicts[1] == "modifier cushion: off"
    assert off.row.steps["approved"].value == Decimal("1.00")


def test_the_press_gate_holds_a_raise_while_the_unit_is_not_active() -> None:
    """REDUCING by a fired row: +100 R would press to 1.5, the gate holds it at 1, a cut stands."""
    compiled = _cushion("fixed", gated=True)
    reducing: list[Mapping[str, object]] = [
        {
            "kind": "risk_event",
            "scope": "unit:run-cushion",
            "at": _START.value_ns - _HOUR,
            "id": "cut",
            "code": "session-loss-limit-halt",
            "verb": "reduce",
        }
    ]

    active = _priced(_host(compiled, [_trade(1, "100")]), compiled)
    held = _priced(_host(compiled, [_trade(1, "100")], risk_rows=reducing), compiled)
    cut = _priced(_host(compiled, [_trade(1, "-50")], risk_rows=reducing), compiled)

    held_trail = explain_size(stored_row(held.row))

    assert [seen.value for seen in explain_size(stored_row(active.row)).factors] == ["1", "1.5"]
    assert active.row.steps["approved"].value == Decimal("1.50")
    assert held_trail.factors[0].reason == "pressing waits while the unit is REDUCING"
    assert [(seen.value, seen.code) for seen in held_trail.factors] == [
        ("1", "none"),
        ("1", "held"),
    ]
    assert held.row.steps["approved"].value == Decimal("1.00")
    assert cut.row.steps["approved"].value == Decimal("0.75")


def _realised(at_ns: int, ident: str, r: str) -> dict[str, object]:
    return {"kind": "realised", "scope": "unit:late", "at": at_ns, "id": ident, "r": r}


def test_a_trade_that_reaches_the_ledger_late_is_counted() -> None:
    """A +2 R win at 02:00 is folded, then a -3 R loss at 01:00 arrives: the day reads -1 R."""
    day = 20_149 * 24 * _HOUR
    clock = Instant(day + 3 * _HOUR)
    win, loss = _realised(day + 2 * _HOUR, "b", "2"), _realised(day + _HOUR, "a", "-3")
    late = Fold("unit:late")
    late.extend([win])
    late.extend([loss, win])
    restarted = Fold.from_cache(json.loads(json.dumps(late.cached())))
    restarted.extend([loss, win])
    same_instant = Fold("unit:late")
    same_instant.extend([_realised(day + _HOUR, "t9", "2")])
    same_instant.extend([_realised(day + _HOUR, "t10", "-3"), _realised(day + _HOUR, "t9", "2")])

    assert late.cushions(clock)["day"] == Cushion(realised=Decimal(-1), peak=Decimal(0))
    assert restarted.cushions(clock)["day"] == Cushion(realised=Decimal(-1), peak=Decimal(0))
    assert same_instant.cushions(clock)["day"].realised == Decimal(-1)


class _Journal:
    """The unit's own journal surface, which a host appends to between steps."""

    def __init__(self) -> None:
        self.trades: tuple[ClosedTrade, ...] = ()

    def at(self, instant: Instant, /) -> object:
        del instant
        return self.trades


def test_a_late_loss_moves_the_factor() -> None:
    """The unit folds a +2 R win, then the journal gains an earlier -3 R loss: 0.995, not 1.01."""
    compiled = _cushion("fixed")
    journal = _Journal()
    journal.trades = (_trade(2, "2"),)
    unit = price._ok(
        construct_unit(
            compiled,
            read_surfaces={
                **price._surfaces(),
                "account": price._At(price.hosted.Account(price._EQUITY)),
                "own_journal": journal,
                "own_position:fx.eurusd": price._At(()),
            },
            scope_id="run-cushion",
            execution_target=price._target(),
            trace_level=TraceLevel.EVERY_BAR,
            motion=MotionSwitch.OFF,
        )
    )
    price._ok(unit.on_instant(_START))
    journal.trades = (_trade(1, "-3"), _trade(2, "2"))
    price._ok(unit.on_instant(_START))

    factor = explain_size(stored_row(_priced(unit, compiled).row)).factors[0]

    assert (factor.value, factor.reason) == (
        "0.995",
        "a cushion of -1 R since the day anchor, fixed, moves the size by 0.995",
    )


def test_a_gate_switched_off_by_a_missing_fact_holds_a_raise() -> None:
    """REDUCING, the gate bound to an absent fact: +100 R holds at 1.00, never presses to 1.50."""
    compiled = _cushion("fixed", gated=True)
    plan = compiled.plan
    gate = replace(plan.modifiers[0], enabled="group.raise_ok")
    switched = replace(compiled, plan=replace(plan, modifiers=(gate, plan.modifiers[1])))
    reducing: list[Mapping[str, object]] = [
        {
            "kind": "risk_event",
            "scope": "unit:run-cushion",
            "at": _START.value_ns - _HOUR,
            "id": "cut",
            "code": "session-loss-limit-halt",
            "verb": "reduce",
        }
    ]

    held = _priced(_host(switched, [_trade(1, "100")], risk_rows=reducing), switched)

    assert [(seen.value, seen.code) for seen in explain_size(stored_row(held.row)).factors] == [
        ("1", "off"),
        ("1", "held"),
    ]
    assert held.row.steps["approved"].value == Decimal("1.00")


def test_a_ledger_overflow_never_ends_the_step() -> None:
    """Two trades of 9E+999999 R overflow the day's total: that row is skipped, the step runs."""
    compiled = _cushion("fixed")

    unit = _host(compiled, [_trade(1, "9E+999999"), _trade(2, "9E+999999")])

    assert unit._core.risk.cushions(_START)["day"].realised == Decimal("9E+999999")
