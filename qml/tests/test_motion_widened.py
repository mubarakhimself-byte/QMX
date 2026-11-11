"""RC-24: the built engine widened to risk numbers, with a bounded memory.

Three proofs, at the door both hosts use:

- The engine's memory is the window, not the journal: a canary with ``window`` 20 keeps the newest
  20 trades after 1,000, and still moves once every 20.
- A ``scaled`` number follows its fact each bar: 2 times a fact of 0.0010 is 0.0020 on the bar the
  fact reads 0.0010, and 0.0040 when it reads 0.0020.
- The shuffle control: over a seeded shuffled outcome list the shipped floor stays inside its
  range and within one step of its seed on average. This one is a control, so it holds before the
  change too; its point is that widening the engine does not make a number run away.

The shipped tests' own helpers are the shortest road to the real compiled units, so this file
borrows them rather than copying their fixtures.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import TypeVar, cast

import test_canary_motion as canary
import test_compile_dummy as dummy
from qmf.core.chrono import Instant
from qmf.core.refusal import Result, TypedRefusal
from qmf.risk.facts import Fact
from qml.compile import CompiledUnit, compile_unit
from qml.motion import ClosedTrade
from qml.protocol.unit import (
    Account,
    HostedUnit,
    MotionSwitch,
    Surface,
    UnitStep,
    construct_unit,
)
from qml.unit.model import Side

_T = TypeVar("_T")
_WEAK = Decimal("0.0003")
_STRONG = Decimal("0.0015")
_LOSS = Decimal("-1")
_WIN = Decimal("1.5")
_STEP = Decimal("0.0001")


def _ok(result: Result[_T]) -> _T:
    assert not isinstance(result, TypedRefusal), result
    return result.value


def _canary(window: int) -> CompiledUnit:
    """The shipped canary, with the engine's memory bounded to ``window`` trades."""
    document = canary._document()
    numbers = cast("dict[str, object]", document["numbers"])
    spec = cast("dict[str, object]", numbers["min_trend_strength"])
    motion = cast("dict[str, object]", spec["motion"])
    motion["window"] = window
    compiled = compile_unit(document, canary._context())
    assert isinstance(compiled, CompiledUnit), compiled
    return compiled


def _canary_host(compiled: CompiledUnit, surfaces: Mapping[str, Surface]) -> HostedUnit:
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id="run-rc24",
            execution_target=canary._target(),
            motion=MotionSwitch.ON,
        )
    )


def test_memory_is_bounded() -> None:
    unit = _canary_host(_canary(20), canary._surfaces(canary._journal(1000)))

    steps = canary._drive(unit, [canary._instant_after(n) for n in range(1, 1001)])

    moves = [row for step in steps for row in step.calibrations]
    slow = cast("Mapping[str, Mapping[str, object]]", unit.snapshot()["slow"])
    assert len(cast("Sequence[object]", slow["min_trend_strength"]["read"])) == 20
    assert len(moves) == 50, "one move every 20 closed trades, 1,000 trades in"
    assert {row.count for row in moves} == {20}, "each move read the window, not the journal"
    assert (moves[0].number, moves[0].old, moves[0].new) == (
        "min_trend_strength",
        Decimal(0),
        _STEP,
    )


def _scaled_dummy(multiple: str) -> dict[str, object]:
    """The shipped dummy with one derived number that follows a fact the account surface carries."""
    document = dummy._document()
    numbers = cast("dict[str, object]", document["numbers"])
    numbers["risk_scale"] = {
        "kind": "derived",
        "measure": "percent",
        "range": {"min": "0", "max": "0.01", "step": "0.0001"},
        "default": "0",
        "motion": {
            "mode": "scaled",
            "scaled_fact": "market.rate:EUR",
            "rule_params": {"multiple": multiple},
        },
        "authority": "motion_inside_range",
        "origin": "placeholder",  # mock-data-scan: allow (the test's own placeholder label)
        "owner": "numbers talk",
        "reason": "the test's own multiple of a fact, so a moved track reaches the bar",
    }
    return document


def _account(rate: Decimal, instant: Instant) -> Account:
    return Account(
        Decimal("10000.00"),
        "USD",
        {"EUR": Fact(rate, instant, "open", "the test's own fact")},
    )


def _fact_switches_at(change: Instant) -> Surface:
    """The account surface: the rate reads 0.0010 before ``change`` and 0.0020 after it."""

    class _AccountAt:
        def at(self, instant: Instant, /) -> Account:
            rate = Decimal("0.0010") if instant.value_ns < change.value_ns else Decimal("0.0020")
            return _account(rate, instant)

    return _AccountAt()


def _decided(steps: Sequence[UnitStep], number: str) -> list[tuple[int, Decimal]]:
    """Every decision row's value for ``number``: the numbers a bar's decision was made with."""
    return [
        (step.instant.value_ns, row.numbers_in_force[number])
        for step in steps
        for row in step.decisions
        if number in row.numbers_in_force
    ]


def test_a_scaled_number_follows_its_fact() -> None:
    bars = dummy._slice()
    instants = dummy._instants(bars)
    change = instants[len(instants) // 2]
    defined = compile_unit(_scaled_dummy("2"), dummy._context())
    assert isinstance(defined, CompiledUnit), defined
    surfaces = cast("dict[str, Surface]", dummy._surfaces(bars)) | {
        "account": _fact_switches_at(change)
    }
    unit = _canary_host(defined, surfaces)

    rows = _decided(dummy._drive(unit, instants), "risk_scale")

    before = next(value for when, value in rows if when < change.value_ns)
    after = next(value for when, value in rows if when >= change.value_ns)
    assert (before, after) == (Decimal("0.0020"), Decimal("0.0040"))


def _calibrated_sizer_canary() -> CompiledUnit:
    """The canary with ``risk_fraction``, the sizer's own number, moved by the shipped rule.

    Its only binding is the sizer's, so before this PR the compiler found no stamp and refused it
    ``motion_not_built``; the stamp a risk number carries is its own value, ``number:<name>``.
    """
    document = canary._document()
    numbers = cast("dict[str, object]", document["numbers"])
    spec = cast("dict[str, object]", numbers["risk_fraction"])
    spec["kind"] = "calibrated"
    spec["motion"] = {
        "mode": "shrink_from_own_trades",
        "source": "own_record",
        "cadence": {"every_closed_trades": 20},
        "min_count": 20,
        "shrink_k": 100,
        "step_limit": 1,
        "rule": "trend-floor-from-record@2",
        "rule_params": {"buckets": "5"},
    }
    compiled = compile_unit(document, canary._context())
    assert isinstance(compiled, CompiledUnit), compiled
    return compiled


def _risk_trade(n: int) -> ClosedTrade:
    """One closed trade that carries the risk number's own value at entry, as RC-25 will write it."""
    return ClosedTrade(
        trade_id=f"r{n:02d}",
        opened_at=Instant(canary._START + n * 900_000_000_000),
        closed_at=Instant(canary._START + (n + 1) * 900_000_000_000),
        side=Side.LONG,
        market_id="fx.eurusd",
        world="replay",
        gross_r=Decimal("1.5"),
        net_r=Decimal("1.5"),
        entry_stamps={"number:risk_fraction": Decimal("0.005")},
    )


def test_a_sizer_number_moves_on_its_own_stamp() -> None:
    compiled = _calibrated_sizer_canary()
    assert {slow.number.name: slow.number.stamp for slow in compiled.plan.slow} == {
        "min_trend_strength": "strength",
        "risk_fraction": "number:risk_fraction",
    }

    unit = _canary_host(compiled, canary._surfaces([_risk_trade(n) for n in range(1, 21)]))
    steps = canary._drive(unit, [canary._instant_after(n) for n in range(1, 21)])

    moves = [(row.number, row.old, row.new, row.count) for step in steps for row in step.calibrations]
    assert moves == [("risk_fraction", Decimal("0.005"), Decimal("0.0049"), 20)]
    assert unit.calibrated_values["risk_fraction"] == Decimal("0.0049")


def _shuffled(count: int, seed: int) -> list[tuple[Decimal, Decimal]]:
    strengths = [_WEAK if n % 3 == 0 else _STRONG for n in range(1, count + 1)]
    outcomes = [_LOSS if n % 3 == 0 else _WIN for n in range(1, count + 1)]
    random.Random(seed).shuffle(outcomes)
    return list(zip(strengths, outcomes, strict=True))


def test_shuffle_control() -> None:
    pairs = _shuffled(400, 7)
    trades: list[ClosedTrade] = [
        canary._trade(n, str(strength), str(outcome))
        for n, (strength, outcome) in enumerate(pairs, 1)
    ]
    compiled = compile_unit(canary._document(), canary._context())
    assert isinstance(compiled, CompiledUnit), compiled
    unit = _canary_host(compiled, canary._surfaces(trades))

    steps = canary._drive(unit, [canary._instant_after(n) for n in range(1, 401)])

    moves = [row for step in steps for row in step.calibrations]
    assert len(moves) == 20
    assert all(Decimal("0") <= row.new <= Decimal("0.0030") for row in moves)
    assert all(abs(row.new - row.old) <= _STEP for row in moves)
    seed = Decimal("0")
    mean = sum((abs(row.new - seed) for row in moves), Decimal(0)) / len(moves)
    assert mean <= _STEP, f"the shuffled list moved the number {mean} from its seed on average"
