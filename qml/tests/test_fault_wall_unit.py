"""The fault wall at the unit door: a raising block costs its unit entries, never an exit.

The three seams are the section's Verify, unit block. A logic slot that raises on every bar leaves
the held position's time exit running and puts one fault row on each answer. A sizer that raises
mints no entry and stops nothing. Entries come back after `fault_clean_bars` clean bars.

Each test drives the shipped dummy trimmed to one market, so one bar is one fault row and one
entry, and its time exit is set to five bars.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import bisect
import json
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import cast

from qmf.core.chrono import Instant
from qmf.core.identity import AccountRole, VenueId
from qmf.risk.paper import ExecutionTarget
from qmf.risk.unit_intent import UnitEntryIntent, UnitExitIntent
from qml.blocks.api import Signal
from qml.compile import CompiledUnit
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol.unit import (
    FAULT_CLEAN_BARS,
    Account,
    DecisionRow,
    HostedUnit,
    OwnPosition,
    Priced,
    Proposal,
    QuoteBar,
    Surface,
    UnitStep,
    construct_unit,
)
from qml.unit.model import Side

from test_compile_dummy import _compiled, _document, _instants, _ok, _slice

_QML = Path(__file__).resolve().parents[1]
_RECORDS = _QML / "tests" / "fixtures" / "records"
_EQUITY = Decimal("100000")
_MARKET = "fx.eurusd"


def _one_market() -> CompiledUnit:
    """The shipped dummy on `fx.eurusd` alone, with its time exit at five bars."""
    document = _document()
    document["markets"] = [
        market
        for market in cast("list[dict[str, object]]", document["markets"])
        if market["market_id"] == _MARKET
    ]
    numbers = cast("dict[str, dict[str, object]]", document["numbers"])
    numbers["time_out_bars"]["default"] = "5"
    return _compiled(document)


def _bars() -> list[QuoteBar]:
    return _slice()[_MARKET]


def _record() -> InstrumentRecord:
    raw = json.loads((_RECORDS / "eurusd.json").read_text("utf-8"))
    return _ok(parse_record(raw))


def _target() -> ExecutionTarget:
    return _ok(
        ExecutionTarget.try_create(AccountRole.DEMO, VenueId("icmarkets-ctrader"), "fault-wall")
    )


class _At:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    def at(self, instant: Instant, /) -> object:
        del instant
        return self._answer


class _Latest:
    """The last bar of the series knowable at the instant, as a host serves it."""

    def __init__(self, bars: Sequence[QuoteBar]) -> None:
        self._bars = bars
        self._stamps = [bar.knowable_at.value_ns for bar in bars]

    def at(self, instant: Instant, /) -> object:
        index = bisect.bisect_right(self._stamps, instant.value_ns)
        return self._bars[index - 1] if index else None


class _Position:
    def __init__(self, held: Callable[[Instant], OwnPosition | None]) -> None:
        self._held = held

    def at(self, instant: Instant, /) -> object:
        found = self._held(instant)
        return () if found is None else (found,)


def _surfaces(
    bars: Sequence[QuoteBar],
    held: Callable[[Instant], OwnPosition | None] = lambda _i: None,
) -> dict[str, Surface]:
    return {
        "account": _At(Account(_EQUITY)),
        "own_journal": _At(()),
        f"bars:m15:{_MARKET}": _Latest(bars),
        f"own_position:{_MARKET}": _Position(held),
    }


def _host(
    compiled: CompiledUnit,
    surfaces: Mapping[str, Surface],
    *,
    fault_clean_bars: int = FAULT_CLEAN_BARS,
) -> HostedUnit:
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id="run-fault-wall",
            execution_target=_target(),
            fault_clean_bars=fault_clean_bars,
        )
    )


def _market(unit: HostedUnit):
    return unit._core.markets[0]


class _Raising:
    """A Library block with a bug: every call raises."""

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
        raise RuntimeError("the Library block's own bug")

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _Answering:
    """A slot bound to one fixed answer, so a bar's signal is known without a market."""

    def __init__(self, answer: object) -> None:
        self._answer = answer

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


def _held(compiled: CompiledUnit, opened_at: Instant) -> OwnPosition:
    return OwnPosition(
        "pos-1",
        Side.LONG,
        Decimal("0.10"),
        Decimal("1.08000"),
        compiled.logic_fingerprint,
        opened_at,
    )


def _proposal() -> Proposal:
    return Proposal(
        wire={},
        row=DecisionRow(
            row_id="row-sizer",
            instant=Instant(1_740_952_800_000_000_000),
            market_id=_MARKET,
            side=Side.LONG,
            outcome="taken",
            slot_trail=(),
            numbers_in_force={"risk_fraction": Decimal("0.005")},
            reason="all slots hold",
        ),
        market_id=_MARKET,
        side=Side.LONG,
        entry_price=Decimal("1.10000"),
        stop=Decimal("1.09500"),
        params={"fraction": Decimal("0.005")},
        record=_record(),
    )


def _step(unit: HostedUnit, instant: Instant) -> tuple[UnitStep, tuple[Priced, ...]]:
    """One host slice: the step, then the price of every proposal it answered."""
    step = _ok(unit.on_instant(instant))
    priced = tuple(unit.price(proposal, Account(_EQUITY)) for proposal in step.proposals)
    return step, priced


# --- a logic slot that raises on every bar ----------------------------------------------


def test_a_raising_logic_slot_leaves_exits_running() -> None:
    compiled = _one_market()
    bars = _bars()
    instants = _instants({_MARKET: bars})[:5]
    held = _held(compiled, instants[0])
    unit = _host(compiled, _surfaces(bars, lambda _i: held))
    _market(unit).instances["long.trend"] = _Raising()

    steps = [_step(unit, instant) for instant in instants]

    faults = [fault for step, _ in steps for fault in step.faults]
    assert [(fault.block, fault.phase, fault.code) for fault in faults] == [
        ("ema@1", "update", "unit_fault")
    ] * 5
    exits = [
        (intent, step.instant)
        for step, _ in steps
        for intent in step.intents
        if isinstance(intent, UnitExitIntent)
    ]
    assert len(exits) == 1
    intent, at = exits[0]
    assert at == instants[4], "the time exit fires on the fifth bar the position is held"
    assert intent.kind.value == "close_full"
    assert intent.reason_code.code == "time"
    entries = [
        entry
        for step, priced in steps
        for entry in (*step.intents, *(one.intent for one in priced))
        if isinstance(entry, UnitEntryIntent)
    ]
    assert entries == []


# --- a sizer that raises ----------------------------------------------------------------


def test_a_raising_sizer_mints_nothing_and_stops_nothing() -> None:
    compiled = _one_market()
    bars = _bars()
    instants = _instants({_MARKET: bars})[:6]
    held = _held(compiled, instants[1])
    unit = _host(
        compiled,
        _surfaces(bars, lambda instant: held if instant.value_ns >= instants[1].value_ns else None),
    )
    _market(unit).instances["sizer"] = _Raising()

    first = _step(unit, instants[0])
    priced = unit.price(_proposal(), Account(_EQUITY))
    rest = [_step(unit, instant) for instant in instants[1:]]

    assert priced.intent is None, "a raising sizer mints no entry"
    assert priced.code == "unit_fault"
    assert priced.row.outcome == "skipped"
    faults = [fault for step, _ in rest for fault in step.faults]
    assert [(fault.block, fault.phase, fault.code) for fault in faults] == [
        ("fixed-fraction-at-stop@2", "price", "unit_fault")
    ]
    exits = [
        (intent, step.instant)
        for step, _ in [first, *rest]
        for intent in step.intents
        if isinstance(intent, UnitExitIntent)
    ]
    assert len(exits) == 1, "the held position's exit still runs after the sizer raised"
    assert exits[0][1] == instants[5], "the time exit fires on the fifth bar the position is held"


# --- entries come back ------------------------------------------------------------------


def test_entries_come_back_after_clean_bars() -> None:
    compiled = _one_market()
    bars = _bars()
    instants = _instants({_MARKET: bars})[:925]
    unit = _host(compiled, _surfaces(bars), fault_clean_bars=3)
    market = _market(unit)
    real = market.instances["long.trend"]
    market.instances["long.strength"] = _Answering(Signal(state=True, value=Decimal(1)))
    market.instances["short.strength"] = _Answering(Signal(state=False, value=Decimal(1)))
    market.instances["long.rsi_cross"] = _Answering(Signal(state=True, value=Decimal(1)))

    steps: list[tuple[UnitStep, tuple[Priced, ...]]] = []
    for bar, instant in enumerate(instants, start=1):
        if bar == 921:
            market.instances["long.trend"] = _Raising()  # the fault bar
        elif bar == 922:
            market.instances["long.trend"] = real
        steps.append(_step(unit, instant))

    faults = [
        (bar, fault.phase)
        for bar, (step, _) in enumerate(steps, start=1)
        for fault in step.faults
    ]
    entries = [
        bar
        for bar, (_, priced) in enumerate(steps, start=1)
        if any(one.intent is not None for one in priced)
    ]
    assert faults == [(921, "update")]
    assert entries == [925], "entries resume on the fourth clean bar after the fault"
