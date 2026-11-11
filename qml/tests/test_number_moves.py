"""RC-25: a sizing number really moves, the next entry uses it, and the receipt says who moved it.

The shipped dummy binds ``risk_fraction`` to its sizer, ``fixed-fraction-at-stop@2``. Here that
number is calibrated by ``own-r-step@1`` with ``min_count`` 20, a cadence of 20 closed trades and
its range's step of 0.0001. Twenty closed trades at -0.5 R each carry the stamps the hosts write,
made from a decision row by ``DecisionRow.entry_stamps``, so the engine reads them as the
fraction's own trades. The unit is driven through ``HostedUnit``, the evaluator both hosts call.

The fixture's own stop distance varies by bar, so the priced entry is the unit's own proposal with
its entry and stop set to the section's literals: EURUSD at 1.10000 with a 0.0050 stop, at an
equity of 100000. The fraction the sizer reads comes from the unit, not from the test.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal
from typing import cast

from qmf.core.chrono import Instant
from qml.compile import CompiledUnit
from qml.motion import ClosedTrade
from qml.protocol import unit as hosted
from qml.protocol.unit import Account, CalibrationRow, HostedUnit, Proposal
from qml.receipt import explain_size, stored_row
from qml.unit.model import Side

from test_compile_dummy import (
    _START,
    _compiled,
    _document,
    _host,
    _instants,
    _ok,
    _slice,
    _surfaces,
)

_EURUSD = "fx.eurusd"
_EQUITY = Decimal("100000")
_LOSS = Decimal("-0.5")
_QUARTER_HOUR = 900_000_000_000


def _moving_fraction() -> CompiledUnit:
    """The dummy with ``risk_fraction`` moved by ``own-r-step@1``, cautious toward smaller."""
    document = _document()
    numbers = cast("dict[str, dict[str, object]]", document["numbers"])
    spec = numbers["risk_fraction"]
    spec["kind"] = "calibrated"
    spec["motion"] = {
        "mode": "shrink_from_own_trades",
        "source": "own_record",
        "cadence": {"every_closed_trades": 20},
        "min_count": 20,
        "shrink_k": 100,
        "step_limit": 1,
        "rule": "own-r-step@1",
        "rule_params": {"cautious": "-1"},
    }
    return _compiled(document)


def _stamps_at_entry() -> dict[str, Decimal]:
    """What a host stamps on a trade the dummy opened at the starting fraction."""
    row = hosted.DecisionRow(
        row_id="row-entry",
        instant=Instant(_START),
        market_id=_EURUSD,
        side=Side.LONG,
        outcome="taken",
        slot_trail=(hosted.SlotOutput("trend", "strength", "0.0015"),),
        numbers_in_force={"risk_fraction": Decimal("0.005")},
        reason="all slots hold",
    )
    return dict(row.entry_stamps())


def _losses(count: int) -> list[ClosedTrade]:
    stamps = _stamps_at_entry()
    return [
        ClosedTrade(
            trade_id=f"t{n:02d}",
            opened_at=Instant(_START + n * _QUARTER_HOUR),
            closed_at=Instant(_START + (n + 1) * _QUARTER_HOUR),
            side=Side.LONG,
            market_id=_EURUSD,
            world="replay",
            r_after_costs=_LOSS,
            entry_stamps=stamps,
        )
        for n in range(1, count + 1)
    ]


def _run() -> tuple[HostedUnit, list[CalibrationRow], list[Proposal]]:
    """The moving dummy over the synthetic month: every calibration row, and every proposal made
    after the last of them."""
    bars = _slice()
    unit = _host(_moving_fraction(), _surfaces(bars, _losses(20)))
    moves: list[CalibrationRow] = []
    after: list[Proposal] = []
    for instant in _instants(bars):
        made = _ok(unit.on_instant(instant))
        if moves:
            after.extend(made.proposals)
        moves.extend(made.calibrations)
    return unit, moves, after


def _first_eurusd(proposals: Sequence[Proposal]) -> Proposal:
    return next(one for one in proposals if one.market_id == _EURUSD)


def _priced_after_the_move() -> tuple[hosted.Priced, CalibrationRow]:
    unit, moves, after = _run()
    proposal = replace(
        _first_eurusd(after),
        side=Side.LONG,
        entry_price=Decimal("1.10000"),
        stop=Decimal("1.09500"),
    )
    return unit.price(proposal, Account(_EQUITY)), moves[0]


def test_fraction_moves_and_the_next_entry_uses_it() -> None:
    unit, moves, after = _run()

    assert [(row.number, row.old, row.new, row.count) for row in moves] == [
        ("risk_fraction", Decimal("0.005"), Decimal("0.0049"), 20)
    ]
    assert moves[0].rule == "own-r-step@1"
    assert moves[0].statistic["mean_r"] == "-0.5"
    assert unit.calibrated_values["risk_fraction"] == Decimal("0.0049")
    proposal = _first_eurusd(after)
    assert proposal.row.numbers_in_force["risk_fraction"] == Decimal("0.0049")
    assert proposal.params["fraction"] == Decimal("0.0049")

    priced, _ = _priced_after_the_move()

    assert priced.code is None, priced.row.reason
    assert priced.intent is not None
    assert priced.intent.to_wire()["quantity"] == "0.98"


def test_explain_size_names_the_row() -> None:
    priced, move = _priced_after_the_move()

    trail = explain_size(stored_row(priced.row))

    moved = next(seen for seen in trail.numbers if seen.name == "risk_fraction")
    assert (moved.value, moved.default, moved.calibration_row_id) == (
        "0.0049",
        "0.005",
        move.row_id,
    )
    assert moved.text == f"risk_fraction 0.0049 default 0.005 set by {move.row_id}"
    still = next(seen for seen in trail.numbers if seen.name == "target_r")
    assert still.text == "target_r 2"
