"""`value-above@1` and the slot rule it needs: a value that only feeds is no condition, a slot left
with none holds, and a binding that can neither hold nor feed refuses with a pointer."""

from __future__ import annotations

import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from qml.blocks.api import Signal
from qml.catalogue.loader import Loaded, LockEntry, block_fingerprint, load
from qml.check import check
from qml.compile import CompiledUnit, compile_unit
from qml.protocol.unit import TraceLevel, construct_unit
from test_compile_dummy import (
    _context,
    _document,
    _drive,
    _entries,
    _host,
    _instants,
    _ok,
    _slice,
    _surfaces,
    _target,
    adx_above,
)

Document = dict[str, Any]

_FOLDER = (
    Path(__file__).resolve().parents[1] / "src" / "qml" / "blocks" / "stdlib" / "value-above" / "1"
)
_ADX = {
    "name": "adx",
    "block": "adx@1",
    "params": {"period": {"value": "14"}},
    "inputs": {"series": "m15"},
}


def _make(level: str, below: str = "0") -> Any:
    source = (_FOLDER / "block.py").read_bytes()
    lock = [LockEntry("value-above", 1, block_fingerprint(source).value)]
    loaded = load(lock, {"value-above@1": source})
    assert isinstance(loaded, Loaded), loaded
    return loaded.blocks["value-above@1"].make(
        {"level": Decimal(level), "below": Decimal(below)}, {"series": "x"}
    )


@pytest.mark.parametrize(
    ("value", "level", "below", "holds"),
    [
        ("25.01", "25", "0", True),
        ("25", "25", "0", False),
        ("24.99", "25", "0", False),
        ("24.99", "25", "1", True),
        ("25", "25", "1", False),
        ("25.01", "25", "1", False),
        ("-3", "-5", "0", True),
        ("-7", "-5", "1", True),
    ],
)
def test_it_compares_a_value_with_its_level(
    value: str, level: str, below: str, holds: bool
) -> None:
    answer = _make(level, below).update({"series": Decimal(value)})

    assert answer == Signal(state=holds, value=Decimal(value))


def test_it_reads_a_level_that_moves_and_answers_nothing_for_a_missing_value() -> None:
    above = _make("25")

    assert above.update({"series": Decimal(30), "level": Decimal(35)}) == Signal(
        state=False, value=Decimal(30)
    )
    assert above.update({"series": None}) is None


def test_its_below_setting_takes_only_0_or_1() -> None:
    with pytest.raises(ValueError, match=r"below is 0 for above, 1 for below"):
        _make("25", "2")


def test_its_entry_pins_its_source() -> None:
    entry = json.loads((_FOLDER / "entry.json").read_text("utf-8"))

    assert entry["fingerprint"] == block_fingerprint((_FOLDER / "block.py").read_bytes()).value
    assert (entry["output"]["type"], entry["mirroring"]) == ("event", "supported")
    assert [(p["port"], p["stream_kind"]) for p in entry["inputs"]] == [("series", "series")]
    assert {name: spec["measure"] for name, spec in entry["parameters"].items()} == {
        "level": "ratio",
        "below": "category",
    }


def _slots(document: Document) -> list[dict[str, Any]]:
    return [document["logic"][side]["slots"] for side in ("long", "short")]


def _feeder_alone_in(slot: str, kind: str, k: int | None = None) -> Document:
    """ADX alone in a slot of its own, read by `value-above` in the context slot after it."""
    document = cast("Document", adx_above("1"))
    combiner: Document = {"kind": kind, "when_inputs_absent": "no_signal"}
    if k is not None:
        combiner["k"] = k
    for slots in _slots(document):
        context = slots["context"]["bindings"]
        context[:] = [b for b in context if b["name"] != "adx"]
        rest = dict(slots)
        slots.clear()
        slots[slot] = {"role": "context", "combiner": combiner, "bindings": [dict(_ADX)]}
        slots.update(rest)
    return document


@pytest.mark.parametrize(("kind", "k"), [("all", None), ("any", None), ("k_of_n", 1)])
def test_a_slot_left_with_no_conditions_holds_under_every_combiner(
    kind: str, k: int | None
) -> None:
    bars = _slice()
    built = compile_unit(_feeder_alone_in("gauge", kind, k), _context())
    assert isinstance(built, CompiledUnit), built

    steps = _drive(_host(built, _surfaces(bars)), _instants(bars))

    assert len(_entries(steps)) == 25


def test_a_trigger_slot_of_only_feeders_writes_no_near_miss_row() -> None:
    document = _feeder_alone_in("gauge", "all")
    for slots in _slots(document):
        slots["gauge"]["role"] = "trigger"
        slots["trigger"]["role"] = "confirmation"
        numbers = document["numbers"]
    numbers["adx_level"]["default"] = "99"
    bars = _slice()
    built = compile_unit(document, _context())
    assert isinstance(built, CompiledUnit), built
    unit = _ok(
        construct_unit(
            built,
            read_surfaces=_surfaces(bars),
            scope_id="near",
            execution_target=_target(),
            trace_level=TraceLevel.EVENTS,
        )
    )

    rows = [row for s in _drive(unit, _instants(bars)) for row in s.decisions]

    assert [row.reason for row in rows if row.reason.startswith("near miss")] == []


def test_a_real_trigger_that_held_on_a_failing_side_still_writes_its_near_miss_row() -> None:
    document = cast("Document", adx_above("99"))
    bars = _slice()
    built = compile_unit(document, _context())
    assert isinstance(built, CompiledUnit), built

    rows = [
        row for s in _drive(_host(built, _surfaces(bars)), _instants(bars)) for row in s.decisions
    ]
    misses = {row.reason for row in rows if row.reason.startswith("near miss")}

    assert len(rows) > 0
    assert "near miss, context: does not hold" in misses


def _with_binding(document: Document, slot: str, binding: Document) -> Document:
    document["logic"]["long"]["slots"][slot]["bindings"].append(binding)
    return document


def _lone(block: str, params: Document | None = None, inputs: Document | None = None) -> Edit:
    def edit(document: Document) -> Document:
        return _with_binding(
            document,
            "context",
            {
                "name": "probe",
                "block": block,
                "params": params or {},
                "inputs": {"series": "m15"} if inputs is None else inputs,
            },
        )

    return edit


Edit = Callable[[Document], Document]
_NOT_READ = "/logic/long/slots/context/bindings/2"


@pytest.mark.parametrize(
    ("edit", "says"),
    [
        pytest.param(
            _lone("adx@1", {"period": {"value": "14"}}),
            "Bind value-above@1",
            id="a value nothing reads",
        ),
        pytest.param(
            _lone("lbma-gold-auction-clock@1", {"auction": {"value": "0"}}),
            "Bind value-above@1",
            id="a clock nothing reads",
        ),
        pytest.param(
            _lone("parabolic-sar@1", {"step": {"value": "0.02"}, "maximum": {"value": "0.2"}}),
            "Bind value-above@1",
            id="a price level nothing reads",
        ),
        pytest.param(
            _lone("time-exit-bars@1", {"bars": {"value": "48"}}, {}),
            "Bind value-above@1",
            id="an exit in a slot",
        ),
        pytest.param(
            _lone("account-daily-loss-halt@1", {"limit": {"value": "0.05"}}, {}),
            "reads its account port equity",
            id="a halt on account facts",
        ),
        pytest.param(
            _lone("losing-days-halt@1", {"days": {"value": "3"}}, {}),
            "reads its trades port",
            id="a halt on the unit's trades",
        ),
    ],
)
def test_a_binding_that_can_neither_hold_nor_feed_refuses_with_a_pointer(
    edit: Edit, says: str
) -> None:
    document = edit(cast("Document", _document()))

    problems = compile_unit(document, _context())
    checked = check(document, _context())

    assert isinstance(problems, tuple), "it compiled"
    assert [(p.kind, p.where) for p in problems] == [("binding_not_read", _NOT_READ)]
    assert says in problems[0].message
    assert [e.where for e in checked.errors] == [(_NOT_READ,)]
    assert checked.errors[0].message.startswith("binding_not_read: ")


def test_a_halt_a_later_binding_reads_still_refuses_because_it_never_feeds_a_value() -> None:
    document = _lone("account-daily-loss-halt@1", {"limit": {"value": "0.05"}}, {})(
        cast("Document", _document())
    )
    _with_binding(
        document,
        "context",
        {
            "name": "strong",
            "block": "value-above@1",
            "params": {"level": {"value": "1"}, "below": {"value": "0"}},
            "inputs": {"series": "probe"},
        },
    )

    problems = compile_unit(document, _context())

    assert isinstance(problems, tuple), "it compiled"
    assert [(p.kind, p.where) for p in problems] == [("binding_not_read", _NOT_READ)]


def test_a_value_only_a_derived_number_reads_feeds_and_does_not_refuse() -> None:
    document = _with_binding(cast("Document", _document()), "context", dict(_ADX))
    document["numbers"]["rsi_low"]["motion"]["source"] = "adx"

    built = compile_unit(document, _context())

    assert isinstance(built, CompiledUnit), built
    long_side = next(s for s in built.plan.sides if s.side.value == "long")
    assert [slot.feeders for slot in long_side.slots if slot.name == "context"] == [
        frozenset({"adx"})
    ]


def test_k_above_the_conditions_a_slot_is_left_with_refuses() -> None:
    document = cast("Document", adx_above("1"))
    for slots in _slots(document):
        slots["context"]["combiner"] = {"kind": "k_of_n", "k": 4, "when_inputs_absent": "no_signal"}

    problems = compile_unit(document, _context())

    assert isinstance(problems, tuple), "it compiled"
    assert [(p.kind, p.where) for p in problems] == [
        ("binding_not_read", "/logic/long/slots/context/combiner/k"),
        ("binding_not_read", "/logic/short/slots/context/combiner/k"),
    ]


def test_a_clock_block_reads_the_bars_time_and_gates_through_value_above() -> None:
    """Within an hour of the London gold auctions, as a unit that stands aside elsewhere writes it:
    the block reads seconds from the nearest auction, and `value-above` compares them."""
    document = cast("Document", _document())
    for slots in _slots(document):
        slots["context"]["bindings"] += [
            {
                "name": "clock",
                "block": "lbma-gold-auction-clock@1",
                "params": {"auction": {"value": "0"}},
                "inputs": {"series": "m15"},
            },
            {
                "name": "after_it",
                "block": "value-above@1",
                "params": {"level": {"value": "0"}, "below": {"value": "0"}},
                "inputs": {"series": "clock"},
            },
        ]
    bars = _slice()
    built = compile_unit(document, _context())
    assert isinstance(built, CompiledUnit), built

    steps = _drive(_host(built, _surfaces(bars)), _instants(bars))
    entered = _entries(steps)

    assert 0 < len(entered) < 25
    held = {
        o.output is not None
        for s in steps
        for row in s.decisions
        for o in row.slot_trail
        if o.binding == "clock"
    }
    assert held == {True}
