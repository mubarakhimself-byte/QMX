"""The seven logic roles run in their slots and change an entry, and none of them reaches an exit.

The section's Verify, unit block, at the unit door. Each case compiles a one-market, long-only unit
(``test_many_positions``' document, whose venue keeps positions apart and which reports no open
position, so every signal may enter) with the role's slot beside its trigger, and drives it through
``construct_unit`` and ``on_instant`` over bars whose closes, lows and highs the case states. A
signal reads ``value-above@1`` on one field of the bar against a level, a document number.

A cooldown's and a timeout's bindings read ``bars_since``, which the unit hands them: the bars since
the side last proposed an entry, and since it armed. The two blocks that read it are pinned in this
file's own bytes, the way a Library block is pinned, because the dictionary ships none yet. Their
``bars`` is bound to a document number with a labelled starting default.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import copy
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, cast

import pytest
from qmf.core.chrono import Instant
from qml.catalogue import block_fingerprint
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.protocol.unit import OHLC, QuoteBar, UnitStep
from qml.unit.model import Role
from test_compile_dummy import _drive
from test_many_positions import (
    _BAR_NS,
    _START,
    _closes,
    _context_holding,
    _holding_document,
    _host,
    _position,
    _surfaces,
)

Document = dict[str, Any]

_SINCE_BLOCK = '''"""Holds while ``bars_since`` is {test}, or nothing has been marked yet."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, Signal


class _Since:
    def __init__(self, bars: Decimal) -> None:
        self._bars = bars

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Signal:
        moved = evidence.get("bars")
        bars = moved if isinstance(moved, Decimal) else self._bars
        since = evidence.get("bars_since")
        if not isinstance(since, int):
            return Signal(state=True)
        return Signal(state={compare}, value=Decimal(since))

    def export_state(self) -> Mapping[str, object]:
        return {{}}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Since:
        del inputs, side
        return _Since(params["bars"])


BLOCK = _Block()
'''
_BLOCKS = {
    "bars-since-at-least@1": _SINCE_BLOCK.format(test="at least bars", compare="since >= bars"),
    "bars-since-under@1": _SINCE_BLOCK.format(test="under bars", compare="since < bars"),
}


def _face(pin: str, source: str) -> bytes:
    entry_id, _, version = pin.partition("@")
    return json.dumps(
        {
            "schema": "qmx.entry/1",
            "entry_id": entry_id,
            "version": int(version),
            "component_type": "filter",
            "origin": "library",
            "inputs": [],
            "output": {"type": "state", "measure": None},
            "parameters": {"bars": {"measure": "bars", "default": "3", "origin": "placeholder"}},
            "mirroring": "not_applicable",
            "fingerprint": block_fingerprint(source.encode()).value,
        }
    ).encode()


def _context() -> CompileContext:
    base = _context_holding()
    return CompileContext(
        sources={**base.sources, **{pin: src.encode() for pin, src in _BLOCKS.items()}},
        entries={**base.entries, **{pin: _face(pin, src) for pin, src in _BLOCKS.items()}},
        records=base.records,
        nets_positions=False,
    )


def _number(measure: str, default: str, reason: str) -> dict[str, object]:
    step = "1" if measure == "bars" else "0.0001"
    return {
        "kind": "fixed",
        "measure": measure,
        "range": {"min": "0" if measure != "bars" else "1", "max": "100", "step": step},
        "default": default,
        "motion": {"mode": "fixed"},
        "authority": "motion_inside_range",
        "origin": "placeholder",
        "owner": "numbers talk",
        "reason": reason,
    }


def _above(name: str, field: str, level: str, *, below: bool = False) -> dict[str, object]:
    """A binding that holds when the bar's ``field`` is above the number ``level``, or below."""
    params = {"level": {"number": level}, "below": {"value": "1" if below else "0"}}
    return {"name": name, "block": "value-above@1", "params": params, "inputs": {"series": field}}


def _since(name: str, block: str, number: str) -> dict[str, object]:
    return {"name": name, "block": block, "params": {"bars": {"number": number}}, "inputs": {}}


def _slot(role: str, *bindings: dict[str, object]) -> dict[str, object]:
    return {
        "role": role,
        "combiner": {"kind": "all", "when_inputs_absent": "no_signal"},
        "bindings": list(bindings),
    }


_EVERY_BAR = {"name": "next_open", "block": "market-next-open@1", "params": {}, "inputs": {}}
_LEVELS = {
    "high_close": _number("ratio", "1.0975", "the close a signal clears, a starting level"),
    "dip_low": _number("ratio", "1.0950", "the low that arms a pullback, a starting level"),
    "spike_high": _number("ratio", "1.0990", "the high that breaks a setup, a starting level"),
    "reclaim_close": _number("ratio", "1.0985", "the close a re-entry needs, a starting level"),
}
_COOLDOWN_BARS = _number("bars", "3", "bars to wait after an entry, a starting count")
_TIMEOUT_BARS = _number("bars", "2", "bars an armed setup stays live, a starting count")


def _unit(
    trigger: dict[str, object],
    slots: Mapping[str, dict[str, object]],
    numbers: Mapping[str, dict[str, object]] | None = None,
) -> CompiledUnit:
    """The holding document with ``trigger``, then ``slots`` in their order, then the order."""
    document = _holding_document(limit=1)
    logic = cast("Document", document["logic"])["long"]["slots"]
    logic.clear()
    logic["trigger"] = _slot("trigger", trigger)
    logic.update(copy.deepcopy(dict(slots)))
    logic["entry_order"] = _slot("entry_order", {**_EVERY_BAR, "name": "at_open"})
    document_numbers = cast("Document", document["numbers"])
    document_numbers.update(copy.deepcopy(_LEVELS))
    document_numbers.update(copy.deepcopy(dict(numbers or {})))
    read = json.dumps(document["logic"])
    for name in list(_LEVELS):
        if f'"{name}"' not in read:
            del document_numbers[name]
    pins = cast("list[dict[str, object]]", document["pins"])
    for pin, source in _BLOCKS.items():
        entry_id, _, version = pin.partition("@")
        pins.append(
            {
                "entry_id": entry_id,
                "version": int(version),
                "fingerprint": block_fingerprint(source.encode()).value,
            }
        )
    compiled = compile_unit(document, _context())
    assert isinstance(compiled, CompiledUnit), compiled
    return compiled


@dataclass(frozen=True)
class _Bar:
    close: str = "1.0960"
    low: str | None = None
    high: str | None = None


def _bars(given: Sequence[_Bar]) -> list[QuoteBar]:
    out: list[QuoteBar] = []
    for index, one in enumerate(given):
        close = Decimal(one.close)
        low = Decimal(one.low) if one.low is not None else close - Decimal("0.0002")
        high = Decimal(one.high) if one.high is not None else close + Decimal("0.0002")
        bid = OHLC(close, high, low, close)
        spread = Decimal("0.0001")
        ask = OHLC(close + spread, high + spread, low + spread, close + spread)
        out.append(QuoteBar(Instant(_START + index * _BAR_NS), bid, ask))
    return out


def _run(compiled: CompiledUnit, given: Sequence[_Bar]) -> list[UnitStep]:
    bars = _bars(given)
    return _drive(_host(compiled, _surfaces(bars, [])), [bar.knowable_at for bar in bars])


def _what(steps: Sequence[UnitStep]) -> list[str]:
    """Each bar's entry decision: ``taken``, a refusal's reason, or ``-`` for no row."""
    out: list[str] = []
    for step in steps:
        rows = [(row.outcome, row.reason) for row in step.decisions]
        rows += [(p.row.outcome, p.row.reason) for p in step.proposals]
        taken = [outcome for outcome, _ in rows if outcome == "taken"]
        out.append("taken" if taken else "; ".join(reason for _, reason in rows) or "-")
    return out


_HIGH, _LOW = _Bar("1.0980"), _Bar("1.0960")
_DIP = _Bar("1.0960", low="1.0945")
_SPIKE = _Bar("1.0980", high="1.0995")
_RECLAIM = _Bar("1.0990")


@dataclass(frozen=True)
class _Case:
    trigger: dict[str, object]
    slots: dict[str, dict[str, object]]
    bars: tuple[_Bar, ...]
    expected: tuple[str, ...]
    numbers: dict[str, dict[str, object]] | None = None


_SIGNAL = _above("up", "m15.close", "high_close")
_ARMING = {"arming": _slot("arming", _above("dip", "m15.low", "dip_low", below=True))}
_CASES: dict[Role, _Case] = {
    Role.COOLDOWN: _Case(
        _SIGNAL,
        {"cooldown": _slot("cooldown", _since("rest", "bars-since-at-least@1", "cooldown_bars"))},
        (_HIGH, _LOW, _HIGH, _LOW, _HIGH),
        ("taken", "-", "near miss, cooldown: does not hold", "-", "taken"),
        {"cooldown_bars": _COOLDOWN_BARS},
    ),
    Role.VETO: _Case(
        _EVERY_BAR,
        {"veto": _slot("veto", _above("too_high", "m15.close", "high_close"))},
        (_LOW, _HIGH, _LOW),
        ("taken", "near miss, veto: vetoed by too_high", "taken"),
    ),
    Role.REGIME_DETECTOR: _Case(
        _EVERY_BAR,
        {"regime": _slot("regime_detector", _above("trending", "m15.close", "high_close"))},
        (_LOW, _HIGH),
        ("near miss, regime: does not hold", "taken"),
    ),
    Role.ARMING: _Case(
        _SIGNAL,
        _ARMING,
        (_DIP, _HIGH, _HIGH),
        ("-", "taken", "near miss, arming: not armed"),
    ),
    Role.INVALIDATION: _Case(
        _SIGNAL,
        {
            **_ARMING,
            "invalidation": _slot("invalidation", _above("spike", "m15.high", "spike_high")),
        },
        (_DIP, _SPIKE, _HIGH),
        (
            "-",
            "near miss, arming: not armed; invalidation: invalidated by spike",
            "near miss, arming: not armed",
        ),
    ),
    Role.TIMEOUT: _Case(
        _SIGNAL,
        {
            **_ARMING,
            "timeout": _slot("timeout", _since("live", "bars-since-under@1", "timeout_bars")),
        },
        (_DIP, _LOW, _HIGH),
        ("-", "-", "near miss, arming: not armed; timeout: does not hold"),
        {"timeout_bars": _TIMEOUT_BARS},
    ),
    Role.RE_ENTRY: _Case(
        _EVERY_BAR,
        {"re_entry": _slot("re_entry", _above("reclaim", "m15.close", "reclaim_close"))},
        (_LOW, _LOW, _RECLAIM),
        ("taken", "near miss, re_entry: does not hold", "taken"),
    ),
}


@pytest.mark.parametrize("role", sorted(_CASES), ids=str)
def test_each_role_changes_a_decision(role: Role) -> None:
    """Cooldown 3 bars: an entry on bar 0 refuses the signal on bar 2 and lets the one on bar 4
    through. A veto refuses with its binding's name, a regime that does not hold refuses, an arm
    lasts until its entry, an invalidation and a timeout of 2 bars each clear the arm, and a re-entry
    is read only once the side has entered."""
    case = _CASES[role]

    steps = _run(_unit(case.trigger, case.slots, case.numbers), case.bars)

    assert tuple(_what(steps)) == case.expected


def test_a_longer_timeout_keeps_the_arm() -> None:
    """The timeout's bars is a number: at 3 the same bars enter on bar 2."""
    case = _CASES[Role.TIMEOUT]
    longer = {"timeout_bars": _number("bars", "3", "a longer arm, for this test")}

    steps = _run(_unit(case.trigger, case.slots, longer), case.bars)

    assert _what(steps) == ["-", "-", "taken"]


def _socket_slot(role: str) -> Callable[[Document], None]:
    def edit(document: Document) -> None:
        document["logic"]["long"]["slots"]["context"]["role"] = role

    return edit


def test_the_census_counts_no_refused_role() -> None:
    """Every logic role compiles in a slot. A socket role there names the section it runs in."""
    refused = []
    for role in Role:
        document = _holding_document(limit=1)
        slots = cast("Document", document["logic"])["long"]["slots"]
        slots["context"] = _slot(role.value, _EVERY_BAR | {"name": "probe"})
        if role is Role.TIMEOUT:
            slots["arming"] = _slot("arming", _EVERY_BAR | {"name": "arm"})
        answer = compile_unit(document, _context())
        if isinstance(answer, tuple):
            refused.append((role.value, sorted({(p.kind, p.where) for p in answer})))

    where = "/logic/long/slots/context/role"
    assert refused == [
        ("sizing_modifier", [("role_has_a_section", where)]),
        ("exit", [("role_has_a_section", where)]),
        ("sizer", [("role_has_a_section", where)]),
        ("halt", [("role_has_a_section", where)]),
    ]


def test_a_timeout_with_nothing_to_time_refuses() -> None:
    document = _holding_document(limit=1)
    slots = cast("Document", document["logic"])["long"]["slots"]
    slots["context"] = _slot("timeout", _EVERY_BAR | {"name": "probe"})

    answer = compile_unit(document, _context())

    assert isinstance(answer, tuple), "it compiled"
    assert [(p.kind, p.where) for p in answer] == [
        ("timeout_not_armed", "/logic/long/slots/context/role")
    ]


def test_no_role_blocks_an_exit() -> None:
    """Every role refusing at once, and a held long whose stop 1.0955 the bar's low 1.0945 reaches:
    the stop exit closes it and no entry is proposed."""
    slots = {
        "veto": _slot("veto", _above("always", "m15.close", "dip_low")),
        **_ARMING,
        "invalidation": _slot("invalidation", _above("always_too", "m15.close", "dip_low")),
        "regime": _slot("regime_detector", _above("never", "m15.close", "spike_high")),
        "cooldown": _slot("cooldown", _since("rest", "bars-since-at-least@1", "cooldown_bars")),
        "re_entry": _slot("re_entry", _above("reclaim", "m15.close", "reclaim_close")),
        "timeout": _slot("timeout", _since("live", "bars-since-under@1", "timeout_bars")),
    }
    compiled = _unit(
        _EVERY_BAR, slots, {"cooldown_bars": _COOLDOWN_BARS, "timeout_bars": _TIMEOUT_BARS}
    )
    held = _position("own-1", "1.0955", "1.0970", compiled)
    bars = _bars([_DIP])

    (step,) = _drive(_host(compiled, _surfaces(bars, [held])), [bars[0].knowable_at])

    assert [
        (one.position_ref.position_id, one.kind.value, one.reason_code.code)
        for one in _closes(step)
    ] == [("own-1", "close_full", "stop-hit")]
    assert step.proposals == ()
