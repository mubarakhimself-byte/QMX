"""A brake is a control row the unit runs: it binds at its limit, its raise never reaches an exit,
and a row in shadow never refuses.

The three seams are the section's Verify, unit block. Each drives the shipped dummy through
``construct_unit`` and ``on_instant``; the journal is the unit's own closed trades, so the session
statistics are QML's and the same in either host.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import bisect
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from typing import cast

import pytest
from qmf.core.chrono import Instant
from qmf.risk.controls import Verb
from qmf.risk.unit_intent import UnitEntryIntent, UnitExitIntent
from qml.blocks.api import Signal
from qml.compile import CompiledUnit, compile_unit
from qml.motion import ClosedTrade
from qml.protocol.unit import (
    Account,
    HostedUnit,
    OwnPosition,
    Priced,
    QuoteBar,
    Surface,
    UnitStep,
    construct_unit,
)
from qml.unit.model import Side

from test_compile_dummy import _compiled, _context, _document, _instants, _ok, _slice, _target

_MARKET = "fx.eurusd"


def _one_market() -> dict[str, object]:
    """The shipped dummy on `fx.eurusd` alone, with its time exit at five bars."""
    document = _document()
    document["markets"] = [
        market
        for market in cast("list[dict[str, object]]", document["markets"])
        if market["market_id"] == _MARKET
    ]
    numbers = cast("dict[str, dict[str, object]]", document["numbers"])
    numbers["time_out_bars"]["default"] = "5"
    return document


def _with_halt(document: dict[str, object], row: dict[str, object], scope: str = "unit") -> None:
    document["halts"] = {"position": [], "unit": [], "account": []}
    cast("dict[str, list[dict[str, object]]]", document["halts"])[scope] = [row]


def _session_loss(limit: str = "2", *, shadow: bool = False) -> dict[str, object]:
    """The shipped ``session-loss-limit-halt`` at ``limit`` R."""
    row: dict[str, object] = {
        "name": "session_loss",
        "block": "session-loss-limit-halt@1",
        "params": {"limit": {"value": limit}},
        "inputs": {},
        "scope": "unit",
    }
    if shadow:
        row["shadow"] = True
    return row


def _losing_day(*, shadow: bool = False) -> dict[str, object]:
    """The shipped ``losing-days-halt`` at one day, which holds while the last day lost."""
    row: dict[str, object] = {
        "name": "losing_day",
        "block": "losing-days-halt@1",
        "params": {"days": {"value": "1"}},
        "inputs": {},
        "scope": "unit",
    }
    if shadow:
        row["shadow"] = True
    return row


def _trade(n: int, r: str, closed_at: Instant) -> ClosedTrade:
    return ClosedTrade(
        trade_id=f"t{n:02d}",
        opened_at=closed_at,
        closed_at=closed_at,
        side=Side.LONG,
        market_id=_MARKET,
        world="replay",
        r_after_costs=Decimal(r),
        entry_stamps={},
    )


class _Answering:
    """A block instance bound to one fixed answer, so a bar's signal needs no market."""

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


class _Raising:
    """A control row with a bug: every call raises."""

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
        raise RuntimeError("the brake's own bug")

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _At:
    def __init__(self, answer: Callable[[Instant], object]) -> None:
        self._answer = answer

    def at(self, instant: Instant, /) -> object:
        return self._answer(instant)


class _Latest:
    def __init__(self, bars: Sequence[QuoteBar]) -> None:
        self._bars = bars
        self._stamps = [bar.knowable_at.value_ns for bar in bars]

    def at(self, instant: Instant, /) -> object:
        index = bisect.bisect_right(self._stamps, instant.value_ns)
        return self._bars[index - 1] if index else None


def _surfaces(
    bars: Sequence[QuoteBar],
    journal: Sequence[ClosedTrade] = (),
    held: Callable[[Instant], OwnPosition | None] = lambda _i: None,
) -> dict[str, Surface]:
    return {
        "account": _At(lambda _i: Account(Decimal("10000.00"))),
        "own_journal": _At(
            lambda instant: tuple(t for t in journal if t.closed_at.value_ns <= instant.value_ns)
        ),
        f"bars:m15:{_MARKET}": _Latest(bars),
        f"own_position:{_MARKET}": _At(held),
    }


def _host(compiled: CompiledUnit, surfaces: Mapping[str, Surface]) -> HostedUnit:
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id="run-control-rows",
            execution_target=_target(),
        )
    )


def _step(unit: HostedUnit, instant: Instant) -> UnitStep:
    return _ok(unit.on_instant(instant))


# --- one brake, at its own limit -----------------------------------------------------


def test_session_loss_halt_binds_at_its_limit() -> None:
    bars = _slice()[_MARKET]
    instants = _instants({_MARKET: bars})
    at = instants[2]
    two_losses = [_trade(1, "-1", instants[0]), _trade(2, "-1", instants[1])]
    one_loss = two_losses[:1]
    over = _host(_compiled(_one_market_with(_session_loss("2"))), _surfaces(bars, two_losses))
    under = _host(_compiled(_one_market_with(_session_loss("2"))), _surfaces(bars, one_loss))

    fired = _step(over, at)
    quiet = _step(under, at)

    assert [(event.kind, event.verb, event.code) for event in fired.controls] == [
        ("fired", Verb.NO_NEW_ENTRIES, "session-loss-limit-halt")
    ]
    assert fired.controls[0].reason == "lost 2R this session, at or past the 2R limit"
    assert quiet.controls == (), "one loss of 1R is above a 2R limit"


# --- a raise, and the exit it must never reach ---------------------------------------


def test_a_raising_row_stops_no_exit() -> None:
    compiled = _compiled(_one_market_with(_session_loss()))
    bars = _slice()[_MARKET]
    instants = _instants({_MARKET: bars})[:5]
    held = OwnPosition(
        "pos-1",
        Side.LONG,
        Decimal("0.10"),
        Decimal("1.08000"),
        compiled.compiled_fingerprint,
        instants[0],
    )
    unit = _host(
        compiled,
        _surfaces(
            bars,
            (),
            lambda instant: held if instant.value_ns >= instants[0].value_ns else None,
        ),
    )
    unit._core.halt_instances["unit.session_loss"] = _Raising()  # the row's block has a bug

    steps = [_step(unit, instant) for instant in instants]

    faults = [
        (fault.block, fault.phase.value, fault.code) for step in steps for fault in step.faults
    ]
    assert faults == [("session-loss-limit-halt@1", "controls", "link_fault")], (
        "one raise, then that row's scope stands down"
    )
    exits = [
        (intent, step.instant)
        for step in steps
        for intent in step.intents
        if isinstance(intent, UnitExitIntent)
    ]
    assert len(exits) == 1, "the held position's time exit still fires"
    intent, at = exits[0]
    assert (intent.kind.value, at) == ("close_full", instants[4])


# --- a row in shadow -----------------------------------------------------------------


def _one_market_with(row: dict[str, object]) -> dict[str, object]:
    document = _one_market()
    _with_halt(document, row)
    return document


def _signals(unit: HostedUnit) -> None:
    """Every long slot holds and every short slot does not, so one entry per eligible bar."""
    market = unit._core.markets[0]
    market.instances["long.trend"] = _Answering(Signal(state=True, value=Decimal(1)))
    market.instances["long.strength"] = _Answering(Signal(state=True, value=Decimal(1)))
    market.instances["long.rsi_cross"] = _Answering(Signal(state=True, value=Decimal(1)))
    market.instances["short.trend"] = _Answering(Signal(state=False, value=Decimal(0)))
    market.instances["short.strength"] = _Answering(Signal(state=False, value=Decimal(0)))
    market.instances["short.rsi_cross"] = _Answering(Signal(state=False, value=Decimal(0)))


def _drive(
    unit: HostedUnit, instants: Sequence[Instant]
) -> list[tuple[UnitStep, tuple[Priced, ...]]]:
    account = Account(Decimal("10000.00"))
    out: list[tuple[UnitStep, tuple[Priced, ...]]] = []
    for instant in instants:
        step = _step(unit, instant)
        out.append((step, tuple(unit.price(proposal, account) for proposal in step.proposals)))
    return out


def test_a_row_in_shadow_never_refuses() -> None:
    bars = _slice()[_MARKET]
    instants = _instants({_MARKET: bars})[:950]
    losses = [_trade(1, "-1", instants[0])]
    shadowed = _host(_compiled(_one_market_with(_losing_day(shadow=True))), _surfaces(bars, losses))
    live = _host(_compiled(_one_market_with(_losing_day())), _surfaces(bars, losses))
    for unit in (shadowed, live):
        _signals(unit)

    shadow_steps = _drive(shadowed, instants)
    live_steps = _drive(live, instants)

    assert {(event.kind, event.verb) for step, _ in shadow_steps for event in step.controls} == {
        ("would_fire", Verb.NO_NEW_ENTRIES)
    }
    entries = [
        intent
        for step, priced in shadow_steps
        for intent in (*step.intents, *(one.intent for one in priced))
        if isinstance(intent, UnitEntryIntent)
    ]
    assert entries, "a row in shadow leaves the entry placed"
    assert not [
        row for step, _ in shadow_steps for row in step.decisions if row.outcome == "suppressed"
    ]

    assert {(event.kind, event.verb) for step, _ in live_steps for event in step.controls} == {
        ("fired", Verb.NO_NEW_ENTRIES)
    }
    refused = [
        row for step, _ in live_steps for row in step.decisions if row.outcome == "suppressed"
    ]
    assert refused, "the same row, live, refuses the entry"
    assert all("halt slot" in row.reason for row in refused)
    assert not [
        intent
        for step, priced in live_steps
        for intent in (*step.intents, *(one.intent for one in priced))
        if isinstance(intent, UnitEntryIntent)
    ]


# --- a row whose own scope disagrees with the list it sits in ------------------------


@pytest.mark.parametrize(("listed", "declared"), [("unit", "position"), ("position", "unit")])
def test_a_halt_row_filed_under_another_scope_is_refused(listed: str, declared: str) -> None:
    """A row says its scope twice. The list decides where it runs, so the row's own field can
    only agree or refuse; a row the compiler silently re-scopes would brake the wrong thing."""
    row = _session_loss()
    row["scope"] = declared
    document = _one_market()
    _with_halt(document, row, listed)

    problems = compile_unit(document, _context())

    assert isinstance(problems, tuple), "a row whose scope field disagrees with its list compiled"
    assert [(p.kind, p.where) for p in problems] == [("halt_scope", f"/halts/{listed}/0/scope")]
