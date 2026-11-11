"""Foundation check 3: every stdlib block acts or refuses, as a trigger and as an exit, through the
real door over the shipped month. Never "check pass, zero signal, no reason" (UT-01, QML-08)."""
# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Final, cast

from qmf.risk.unit_intent import UnitExitIntent
from qml.check import check
from qml.compile import CompiledUnit, compile_unit
from qml.compile.compiler import BLOCKS_NOT_BUILT
from qml.protocol.unit import Account, OwnPosition, TraceLevel, construct_unit
from qml.unit.model import Side
from test_compile_dummy import (
    _context,
    _document,
    _instants,
    _ok,
    _slice,
    _surfaces,
    _target,
)

Document = dict[str, Any]

_STDLIB = Path(__file__).resolve().parents[1] / "src" / "qml" / "blocks" / "stdlib"
_MARKET = "fx.eurusd"
_REFUSED, _FIRED, _READ, _SILENT = "refused", "fired", "read", "silent"
_RIGHT_SHAPE: Final[dict[str, str]] = {"bars": "m15", "series": "m15.close"}
_OTHER_SHAPE: Final[dict[str, str]] = {"bars": "m15.close", "series": "m15"}
_DUMMYS_OWN = frozenset(
    {
        "ema",
        "fixed-fraction-at-stop",
        "market-next-open",
        "percentile-of-own-history",
        "roc-of-series",
        "rsi-cross-back",
        "swing-stop-buffer",
        "target-r-multiple",
        "time-exit-bars",
        "trend-floor-from-record",
    }
)
"""The test helper pins every stdlib block, and layer F scans each pin, so a sweep pins these."""

READ_NEVER_FIRED: Final[list[str]] = ["value-above@1"]
"""Read as a condition on the shipped month and never held. A change here is on purpose. The sweep
feeds `value-above` the close, and a EURUSD close is never above its default level of 25."""

_CONTEXT = _context()
_BARS = {_MARKET: _slice()[_MARKET]}
_INSTANTS = _instants(_BARS)


def _faces() -> dict[str, Document]:
    """Every version of every block, by its pin, so a new version cannot slip past the sweep."""
    return {
        f"{path.parent.parent.name}@{path.parent.name}": cast(
            "Document", json.loads(path.read_text("utf-8"))
        )
        for path in sorted(_STDLIB.glob("*/*/entry.json"))
    }


def _probe(face: Document, fed: dict[str, str] = _RIGHT_SHAPE) -> Document:
    """A binding of `face` at its default parameters, its ports fed as `fed` says."""
    return {
        "name": "probe",
        "block": f"{face['entry_id']}@{face['version']}",
        "params": {
            name: {"value": str(spec["default"])} for name, spec in face["parameters"].items()
        },
        "inputs": {
            port["port"]: fed[port["stream_kind"]]
            for port in face["inputs"]
            if port["stream_kind"] in fed
        },
    }


def _base(probe: str) -> Document:
    document = cast("Document", _document())
    document["pins"] = [
        pin
        for pin in document["pins"]
        if pin["entry_id"] in _DUMMYS_OWN or pin["entry_id"] == probe
    ]
    document["markets"] = [m for m in document["markets"] if m["market_id"] == _MARKET]
    return document


def _trigger_document(face: Document, fed: dict[str, str] = _RIGHT_SHAPE) -> Document:
    document = _base(face["entry_id"])
    for side in ("long", "short"):
        document["logic"][side]["slots"]["trigger"]["bindings"] = [_probe(face, fed)]
    for number in ("rsi_low", "rsi_high", "rsi_period"):
        del document["numbers"][number]
    return document


def _exit_index(face: Document) -> int | None:
    """Which of the dummy's exits `face` stands in for: its stop, its target or its time exit."""
    output = face["output"]
    if output["type"] == "exit_action":
        return 2
    if output["type"] == "level" and output.get("measure") == "price":
        return 1 if any(port["port"] == "stop_price" for port in face["inputs"]) else 0
    return None


def _exit_document(face: Document) -> Document:
    document = _base(face["entry_id"])
    binding = _probe(face) | {"scope": "position"}
    index = _exit_index(face)
    if index is None:
        document["exit_set"].append(binding)
    else:
        for param in document["exit_set"][index]["params"].values():
            del document["numbers"][param["number"]]
        document["exit_set"][index] = binding
    return document


def _compiled(document: Document) -> CompiledUnit | None:
    """The compiled unit, or None when check names a pointer for why it refuses."""
    result = check(document, _CONTEXT)
    if result.verdict.value == "fail":
        assert all(p.where and all(p.where) for p in result.errors), result.errors
        return None
    built = compile_unit(document, _CONTEXT)
    assert isinstance(built, CompiledUnit), built
    return built


def _surfaces_for(position: OwnPosition | None = None) -> dict[str, Any]:
    surfaces = _surfaces(_BARS, positions=lambda _m, _i: position)
    return {key: at for key, at in surfaces.items() if "metal.xauusd" not in key}


def _as_trigger(face: Document) -> str:
    return _driven(_trigger_document(face))


def _through_a_comparator(face: Document) -> str:
    """A block whose value is no price holds a slot only through `value-above`, as an agent binds it."""
    document = _trigger_document(face)
    pins = cast("Document", _document())["pins"]
    document["pins"] += [p for p in pins if p["entry_id"] == "value-above"]
    comparator = {
        "name": "above",
        "block": "value-above@1",
        "params": {"level": {"value": "0"}, "below": {"value": "0"}},
        "inputs": {"series": "probe"},
    }
    for side in ("long", "short"):
        document["logic"][side]["slots"]["trigger"]["bindings"].append(comparator)
    return _driven(document)


def _driven(document: Document) -> str:
    compiled = _compiled(document)
    if compiled is None:
        return _REFUSED
    unit = _ok(
        construct_unit(
            compiled,
            read_surfaces=_surfaces_for(),
            scope_id="sweep",
            execution_target=_target(),
            trace_level=TraceLevel.EVERY_BAR,
        )
    )
    read = False
    for instant in _INSTANTS:
        for row in _ok(unit.on_instant(instant)).decisions:
            if "trigger:" not in row.reason:
                return _FIRED
            read = read or "trigger: does not hold" in row.reason
    return _READ if read else _SILENT


def _as_exit(face: Document) -> str:
    compiled = _compiled(_exit_document(face))
    if compiled is None:
        return _REFUSED
    index = _exit_index(face)
    position = (
        OwnPosition(
            "pos-1",
            Side.LONG,
            Decimal("0.10"),
            Decimal("1.08000"),
            compiled.compiled_fingerprint,
            _INSTANTS[0],
        )
        if index == 2
        else None
    )
    unit = _ok(
        construct_unit(
            compiled,
            read_surfaces=_surfaces_for(position),
            scope_id="sweep",
            execution_target=_target(),
        )
    )
    for instant in _INSTANTS:
        step = _ok(unit.on_instant(instant))
        intents = [
            *step.intents,
            *(
                one.intent
                for one in (
                    unit.price(proposal, Account(Decimal("10000.00")))
                    for proposal in step.proposals
                )
                if one.intent is not None
            ),
        ]
        for intent in intents:
            if isinstance(intent, UnitExitIntent):
                return _FIRED
            if index == 0 or intent.protection.targets:
                return _FIRED
    return _SILENT


def test_every_stdlib_block_acts_or_refuses() -> None:
    faces = _faces()

    triggers = {name: _as_trigger(face) for name, face in faces.items()}
    exits = {name: _as_exit(face) for name, face in faces.items()}

    silent = sorted(name for name, found in triggers.items() if found == _SILENT)
    silent += sorted(f"{name} as an exit" for name, found in exits.items() if found == _SILENT)
    assert silent == []
    assert [name for name, found in triggers.items() if found == _READ] == READ_NEVER_FIRED
    assert sorted(name for name, found in exits.items() if found != _REFUSED) == [
        "swing-stop-buffer@1",
        "swing-stop-buffer@2",
        "target-r-multiple@1",
        "target-r-multiple@2",
        "time-exit-bars@1",
        "time-exit-bars@2",
    ]
    assert len(faces) == 130
    assert {pin: triggers[pin] for pin in _HOLDS_ON_ITS_CLOCK} == dict.fromkeys(
        _HOLDS_ON_ITS_CLOCK, _FIRED
    )
    assert {pin: _through_a_comparator(faces[pin]) for pin in _MEASURES_ON_ITS_CLOCK} == {
        pin: _FIRED for pin in _MEASURES_ON_ITS_CLOCK
    }
    assert triggers["vwap-session-anchored@2"] == _REFUSED


def _refuses_the_feed(document: Document) -> bool:
    problems = compile_unit(document, _CONTEXT)
    return isinstance(problems, tuple) and any(
        p.kind == "binding_not_read" and "Feed it" in p.message for p in problems
    )


def test_every_block_fed_the_other_shape_refuses_and_none_fed_the_right_shape_does() -> None:
    """Check pass and no trades again if a whole bar reached a value port, or a value a bar port.
    A block on other facts, an exit or a block not built refuses for that reason first."""
    fed = [
        face
        for name, face in _faces().items()
        if {port["stream_kind"] for port in face["inputs"]} in ({"series"}, {"bars"})
        and face["output"]["type"] != "exit_action"
        and name not in BLOCKS_NOT_BUILT
    ]

    wrong = [f["entry_id"] for f in fed if _refuses_the_feed(_trigger_document(f, _OTHER_SHAPE))]
    right = [f["entry_id"] for f in fed if _refuses_the_feed(_trigger_document(f))]

    assert wrong == [f["entry_id"] for f in fed]
    assert right == []
    assert len(wrong) == 91
    assert set(_SESSION_BLOCKS) - {"vwap-session-anchored"} <= set(wrong)


_SESSION_BLOCKS: Final[tuple[str, ...]] = (
    "initial-balance-high",
    "initial-balance-low",
    "initial-balance-range-extension",
    "session-running-high",
    "session-running-low",
    "session-running-range",
    "tpo-point-of-control",
    "tpo-value-area-high",
    "tpo-value-area-low",
    "vwap-session-anchored",
)
_MEASURES_ON_ITS_CLOCK: Final[tuple[str, ...]] = (
    "initial-balance-range-extension@2",
    "session-running-range@2",
)
_HOLDS_ON_ITS_CLOCK: Final[tuple[str, ...]] = tuple(
    pin
    for pin in (f"{name}@2" for name in _SESSION_BLOCKS)
    if pin not in (*_MEASURES_ON_ITS_CLOCK, "vwap-session-anchored@2")
)
_VOLUME_BLOCKS: Final[tuple[str, ...]] = (
    "accumulation-distribution@1",
    "chaikin-oscillator@1",
    "force-index@1",
    "market-facilitation-index@1",
    "money-flow-index@1",
    "on-balance-volume@1",
    "vwap-session-anchored@2",
)


def test_a_session_block_with_no_clock_and_a_volume_block_still_refuse() -> None:
    """A session block on a fixed UTC second is an hour wrong most of the year, so every `@1` stays
    refused with the way forward in its words (call 4). Volume waits for its own repair (call 5)."""
    faces = _faces()

    for pin in (*(f"{name}@1" for name in _SESSION_BLOCKS), *_VOLUME_BLOCKS):
        problems = compile_unit(_trigger_document(faces[pin]), _CONTEXT)

        assert isinstance(problems, tuple), pin
        assert ("block_not_built", "/logic/long/slots/trigger/bindings/0/block") in {
            (p.kind, p.where) for p in problems
        }, pin
    told = compile_unit(_trigger_document(faces["session-running-high@1"]), _CONTEXT)
    assert isinstance(told, tuple)
    assert [p.message for p in told if p.kind == "block_not_built"] == [
        "session-running-high@1 needs a clock it does not have: use version 2 and name its clock"
    ] * 2
