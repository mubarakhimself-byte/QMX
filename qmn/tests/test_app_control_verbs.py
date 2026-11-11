"""The control verbs that act: a brake flattens through the exit path, a reduce cuts the next
entry, and only the row that says wait for a hand waits for a person (RC-16).

The section's three seams, driven at the dummy's own compile through ``construct_unit`` and
``on_instant``. Nothing here reads a chain or a reading: the unit answers, the one stop port is
the host's door to ``Runtime.risk_stop``, and the lifecycle table is folded from the same rows
the node writes.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TypeVar, cast

from qmf.core.chrono import Instant
from qmf.core.identity import AccountRole, VenueId
from qmf.core.refusal import Result, TypedRefusal
from qmf.risk.controls import Restore, StateWord, Verb
from qmf.risk.paper import ExecutionTarget
from qmf.risk.unit_intent import UNIT_INTENT_FORMAT_VERSION, UnitExitIntent
from qml.blocks.api import EntryFace, Halt, HaltAction, Scope, parse_entry
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.lifecycle import Actor, ActorKind, Event, MarketKey, Refusal, State, fold
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol.unit import (
    Account,
    DecisionRow,
    HostedUnit,
    OwnPosition,
    Proposal,
    UnitStep,
    construct_unit,
)
from qml.unit.model import Side

_QML = Path(__file__).resolve().parents[2] / "qml"
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_DUMMY = _QML / "src" / "qml" / "unit" / "templates" / "dummy-trend-pullback.json"
_RECORDS = _QML / "tests" / "fixtures" / "records"
_MARKETS: Mapping[str, str] = {"fx.eurusd": "eurusd", "metal.xauusd": "xauusd"}
_AT = Instant(1_740_952_800_000_000_000)
_LATER = Instant(1_740_952_800_900_000_000)
_T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
_T = TypeVar("_T")


def _ok(result: Result[_T]) -> _T:
    assert not isinstance(result, TypedRefusal), result
    return result.value


def _record(name: str) -> InstrumentRecord:
    return _ok(parse_record(json.loads((_RECORDS / f"{name}.json").read_text("utf-8"))))


def _document() -> dict[str, object]:
    document = cast("dict[str, object]", json.loads(_DUMMY.read_text("utf-8")))
    pins: list[dict[str, object]] = []
    for entry in sorted(_STDLIB.glob("*/*/entry.json")):
        face = parse_entry(entry.read_bytes())
        assert isinstance(face, EntryFace), face
        pins.append(
            {"entry_id": face.entry_id, "version": face.version, "fingerprint": face.fingerprint}
        )
    document["pins"] = pins
    return document


def _context() -> CompileContext:
    folders = [p.parent for p in _STDLIB.glob("*/*/block.py")]
    return CompileContext(
        sources={f"{p.parent.name}@{p.name}": (p / "block.py").read_bytes() for p in folders},
        entries={f"{p.parent.name}@{p.name}": (p / "entry.json").read_bytes() for p in folders},
        records={market: _record(name) for market, name in _MARKETS.items()},
    )


def _halt_row(verb: str, *, name: str = "flat") -> dict[str, object]:
    """The shipped session-loss halt as a row with ``verb``, so the row's own word runs."""
    return {
        "name": name,
        "block": "session-loss-limit-halt@1",
        "params": {"limit": {"value": "2"}},
        "inputs": {},
        "scope": "unit",
        "verb": verb,
    }


def _compiled(verb: str, *, restore: Restore = Restore.HAND) -> CompiledUnit:
    document = _document()
    document["halts"] = {"position": [], "unit": [_halt_row(verb)], "account": []}
    compiled = compile_unit(document, _context())
    assert isinstance(compiled, CompiledUnit), compiled
    if restore is Restore.HAND:
        return compiled
    halts = tuple(
        replace(halt, control=replace(halt.control, restore=restore)) for halt in compiled.plan.halts
    )
    return replace(compiled, plan=replace(compiled.plan, halts=halts))


class _Answering:
    """One brake instance bound to one fixed answer, so its fire needs no market."""

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


@dataclass
class _StopPort:
    """The host's door a wait-for-hand row calls, as ``Runtime.risk_stop`` would."""

    calls: list[tuple[str, str]]

    def __init__(self) -> None:
        self.calls = []

    def risk_stop(self, rule: str, reason: str) -> None:
        self.calls.append((rule, reason))


class _At:
    def __init__(self, answer: Callable[[Instant], object]) -> None:
        self._answer = answer

    def at(self, instant: Instant, /) -> object:
        return self._answer(instant)


def _one(position: OwnPosition | None) -> tuple[OwnPosition, ...]:
    """The unit door answers every position on a market, so a fixture holding one answers one."""
    return () if position is None else (position,)


def _surfaces(held: Mapping[str, OwnPosition] | None = None) -> dict[str, _At]:
    positions: Mapping[str, OwnPosition] = {} if held is None else held
    surfaces = {
        "account": _At(lambda _i: Account(Decimal("100000"))),
        "own_journal": _At(lambda _i: ()),
    }
    for market in _MARKETS:
        surfaces[f"bars:m15:{market}"] = _At(lambda _i: None)
        surfaces[f"own_position:{market}"] = _At(lambda _i, m=market: _one(positions.get(m)))
    return surfaces


def _target() -> ExecutionTarget:
    return _ok(
        ExecutionTarget.try_create(AccountRole.DEMO, VenueId("icmarkets-ctrader"), "acct-a5")
    )


def _host(compiled: CompiledUnit, surfaces: Mapping[str, _At]) -> HostedUnit:
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id="run-control-verbs",
            execution_target=_target(),
        )
    )


def _step(unit: HostedUnit, instant: Instant = _AT) -> UnitStep:
    return _ok(unit.on_instant(instant))


def _event(
    sequence: int,
    start: State,
    end: State,
    kind: ActorKind,
    principal: str,
    *,
    clears: str | None = None,
    market: str = "fx.eurusd",
) -> Event:
    return Event(
        event_id=f"e{sequence}",
        unit_id="dummy-trend-pullback",
        version_ref="v1",
        compiled_fingerprint="fp1:abc",
        market_id=market,
        from_state=start,
        to_state=end,
        by=Actor(kind, principal),
        reason="the fixture",
        evidence_ref=None,
        at=_T0.replace(minute=sequence),
        writer="this-pc",
        sequence=sequence,
        clears=clears,
    )


def _proposal(compiled: CompiledUnit) -> Proposal:
    """One EURUSD long at the dummy's 0.0050 stop distance, for the one price call."""
    record = _record("eurusd")
    stop = Decimal("1.09500")
    target = _target()
    return Proposal(
        wire={
            "contract_format_version": UNIT_INTENT_FORMAT_VERSION,
            "intent_family": "entry",
            "unit": {
                "unit_id": compiled.unit.unit_id,
                "version_ref": compiled.document_fingerprint.value,
                "compiled_fingerprint": compiled.compiled_fingerprint.value,
            },
            "instrument": {"venue": record.venue, "symbol": record.symbol},
            "market_id": "fx.eurusd",
            "direction": Side.LONG.value,
            "reason_code": {"code": compiled.unit.family_id, "book_family": "unit"},
            "execution_target": {
                "role": target.role.value,
                "venue_id": target.venue_id.value,
                "account_id": target.account_id,
            },
            "order": {"type": "market"},
            "protection": {"stop": str(stop), "targets": [], "time_exit_bars": 1},
            "not_before": _AT.value_ns,
            "placeholder_labels": list(compiled.placeholders),
            "decision_row_id": "row-eurusd",
        },
        row=DecisionRow(
            row_id="row-eurusd",
            instant=_AT,
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
        stop=stop,
        params={"fraction": Decimal("0.005")},
        record=record,
    )


def test_flatten_closes_through_the_exit_path() -> None:
    """A row with verb flatten on two held positions gives two exit intents with reason
    control_flatten in the same step."""
    compiled = _compiled("flatten")
    held = {
        market: OwnPosition(
            f"pos-{market.split('.')[1]}",
            Side.LONG if market == "fx.eurusd" else Side.SHORT,
            Decimal("0.10"),
            Decimal("1.10000") if market == "fx.eurusd" else Decimal("2650.00"),
            compiled.compiled_fingerprint,
            _AT,
        )
        for market in _MARKETS
    }
    unit = _host(compiled, _surfaces(held))
    unit._core.halt_instances["unit.flat"] = _Answering(
        Halt(HaltAction.FLATTEN, Scope.UNIT, "the fixture says flatten")
    )

    step = _step(unit)

    closes = [intent for intent in step.intents if isinstance(intent, UnitExitIntent)]
    assert [
        (close.position_ref.position_id, close.kind.value, close.reason_code.code)
        for close in closes
    ] == [
        ("pos-eurusd", "close_full", "control_flatten"),
        ("pos-xauusd", "close_full", "control_flatten"),
    ]
    assert len(step.decisions) == 2, "both closes land in the same step"


def test_reduce_factor_halves_the_next_entry() -> None:
    """Verb reduce(0.5) at 500 money at risk on EURUSD with stop distance 0.0050 gives 0.50
    lots."""
    compiled = _compiled("reduce")
    unit = _host(compiled, _surfaces())
    unit._core.halt_instances["unit.flat"] = _Answering(
        Halt(HaltAction.REDUCE, Scope.UNIT, "the fixture halves the size", Decimal("0.5"))
    )

    fired = _step(unit)
    priced = unit.price(_proposal(compiled), Account(Decimal("100000")))

    assert [(event.kind, event.verb, event.factor) for event in fired.controls] == [
        ("fired", Verb.REDUCE, Decimal("0.5"))
    ]
    assert priced.row.steps["wanted"].value == Decimal("500")
    assert priced.row.steps["reduced"].value == Decimal("250")
    assert priced.intent is not None
    assert priced.intent.to_wire()["quantity"] == "0.50"


def test_only_a_hand_lifts_a_hand_row() -> None:
    """After a hand row fires, a restore rule answers no change, and resume by his route clears
    it."""
    compiled = _compiled("no_new_entries")
    unit = _host(compiled, _surfaces())
    port = _StopPort()
    unit.attach_stop_port(port)
    unit._core.halt_instances["unit.flat"] = _Answering(
        Halt(HaltAction.NO_NEW_ENTRIES, Scope.UNIT, "the fixture says stop")
    )

    fired = _step(unit)
    unit._core.halt_instances["unit.flat"] = _Answering(None)
    quiet = _step(unit, _LATER)

    assert [(event.kind, event.verb) for event in fired.controls] == [
        ("fired", Verb.NO_NEW_ENTRIES)
    ]
    assert port.calls == [("session-loss-limit-halt@1", "the fixture says stop")], (
        "the hand row asks its host for the one automatic stop"
    )
    assert quiet.controls == ()
    assert unit.risk_state(_AT).word is StateWord.BENCHED, "a restore rule answers no change"

    ruled = _host(_compiled("no_new_entries", restore=Restore.RULE), _surfaces())
    ruled._core.halt_instances["unit.flat"] = _Answering(
        Halt(HaltAction.NO_NEW_ENTRIES, Scope.UNIT, "the fixture says stop")
    )
    _step(ruled)
    ruled._core.halt_instances["unit.flat"] = _Answering(None)
    _step(ruled, _LATER)

    assert ruled.risk_state(_AT).word is StateWord.RESTORE, "a rule's own row restores itself"

    key = MarketKey("dummy-trend-pullback", "v1", "fx.eurusd")
    traded = [
        _event(1, State.DRAFT, State.TESTED, ActorKind.JUDGE, "run:judge-7"),
        _event(2, State.TESTED, State.PAPER, ActorKind.HIS_CLICK, "operator"),
        _event(3, State.PAPER, State.STOPPED, ActorKind.RISK_RULE, "node:vps-1"),
    ]
    stop = traded[-1].event_id
    restored = fold(
        [*traded, _event(4, State.STOPPED, State.PAPER, ActorKind.RISK_RULE, "node:vps-1", clears=stop)]
    )
    live = fold(
        [*traded, _event(5, State.STOPPED, State.LIVE, ActorKind.RISK_RULE, "node:vps-1", clears=stop)]
    )
    resumed = fold(
        [*traded, _event(6, State.STOPPED, State.PAPER, ActorKind.HIS_CLICK, "operator", clears=stop)]
    )

    assert restored.rejected == ()
    assert restored.state(key) is State.PAPER, "a restore rule may send a member to paper"
    assert [refused.refusal for refused in live.rejected] == [Refusal.NOT_OPERATOR], (
        "a restore rule never sends a member to live"
    )
    assert (resumed.state(key), resumed.rejected) == (State.PAPER, ())
