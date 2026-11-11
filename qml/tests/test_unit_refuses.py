"""What compiler format 2 does not run refuses with a pointer, through `check` and `compile_unit`,
and a unit trades only the sides its `direction` says."""
# pyright: reportPrivateUsage=false

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from qmf.risk.unit_intent import UnitExitIntent
from qml.check import check
from qml.compile import CompiledUnit, compile_unit
from qml.door import new
from qml.protocol.unit import OwnPosition
from qml.unit.model import Side
from qml.unit.schema import Array, Map, OneOf, Record, Shape, shape_of
from test_compile_dummy import (
    _compiled,
    _context,
    _document,
    _drive,
    _entries,
    _host,
    _instants,
    _slice,
    _surfaces,
)

Document = dict[str, Any]
Edit = Callable[[Document], None]

_CENSUS = frozenset(
    """
    Unit.schema Unit.unit_id Unit.family_id Unit.claim_card Unit.markets Unit.streams
    Unit.direction Unit.logic Unit.exit_set Unit.halts Unit.reads Unit.numbers Unit.pins
    Unit.title Unit.lineage Unit.sessions Unit.position_limit Unit.sizer Unit.context_needs
    Unit.routes Unit.baseline Unit.plain_python
    Unit.modifiers Unit.gates Unit.tolerations Unit.stages Unit.risk_locks Unit.recipe
    Unit.home_markets Unit.tags
    ClaimCard.idea ClaimCard.sources ClaimCard.written_at ClaimCard.claimed_context
    Source.source_ref Source.locator Source.dated Source.quote
    Market.market_id Market.instrument_ref Market.roll Market.settings Market.settings_record
    SymbolRef.venue SymbolRef.symbol RootRef.venue RootRef.root
    Roll.rule Roll.days_before_expiry
    Stream.name Stream.market Stream.bar Stream.price Stream.input Stream.derived_from
    Bar.kind Bar.size
    Logic.long Logic.short SlotsSide.slots MirrorSide.mirror_of
    Slot.role Slot.bindings Slot.combiner
    Binding.name Binding.block Binding.params Binding.inputs
    NumberParam.number ValueParam.value
    Combiner.kind Combiner.when_inputs_absent Combiner.k Combiner.weights Combiner.open
    Combiner.close Combiner.within_bars
    ScopedBinding.name ScopedBinding.block ScopedBinding.params ScopedBinding.inputs
    ScopedBinding.scope
    ControlBinding.name ControlBinding.block ControlBinding.params ControlBinding.inputs
    ControlBinding.scope ControlBinding.verb ControlBinding.shadow
    Halts.position Halts.unit Halts.account
    Read.reading Read.market Read.fallback Read.stale_after_s
    NumberSpec.kind NumberSpec.measure NumberSpec.default NumberSpec.motion NumberSpec.authority
    NumberSpec.origin NumberSpec.range NumberSpec.applies_to_open_positions
    NumberSpec.derivation NumberSpec.owner NumberSpec.reason NumberSpec.cautious NumberSpec.guard
    NumberSpec.never_self_tune NumberSpec.stage_values
    Guard.revert_after Guard.freeze_after
    Motion.mode Motion.source Motion.cadence Motion.min_count Motion.shrink_k Motion.step_limit
    Motion.rule Motion.rule_params
    Cadence.every_closed_trades Cadence.at
    Range.min Range.max Range.step
    Pin.entry_id Pin.version Pin.fingerprint
    Lineage.parents Lineage.rewritten_from
    LineageParent.unit_id LineageParent.version_ref LineageParent.edit_labels
    Session.name Session.calendar_ref Session.zone Session.windows
    Window.from Window.to
    PositionLimit.per_instrument
    ContextNeeds.require ContextNeeds.warn ContextNeeds.block Need.word Need.reading
    Routes.data Routes.execution
    PlainPython.block
    RecipeRef.pod_id RecipeRef.version RecipeRef.hash RecipeRef.displaced
    Stages.selector Stages.anchor Stages.hysteresis Stages.move_up Stages.move_down Stages.rows
    StageRow.sizer StageRow.modifiers StageRow.controls StageRow.numbers
    """.split()
)
"""Every field of qmx.unit/1. The PR's census table says why each stands."""

_GUIDE = Path(__file__).resolve().parents[1] / "EXTENDING.md"
_READS = [
    {
        "reading": "news@1",
        "market": "fx.eurusd",
        "fallback": "treat_as_absent",
        "stale_after_s": 60,
    }
]


def _sides(document: Document) -> dict[str, int]:
    bars = _slice()
    steps = _drive(_host(_compiled(document), _surfaces(bars)), _instants(bars))
    directions = [intent.direction.value for _, intent in _entries(steps)]
    return {side: directions.count(side) for side in ("long", "short")}


def test_a_long_only_dummy_enters_long_only() -> None:
    long_only = cast("Document", new(_document(), {"/direction": "long"}))
    short_only = cast("Document", new(_document(), {"/direction": "short"}))

    assert _sides(_document()) == {"long": 2, "short": 23}
    assert _sides(long_only) == {"long": 2, "short": 0}
    assert _sides(short_only) == {"long": 0, "short": 23}

    del long_only["logic"]["short"]
    bound_on_no_stated_side = compile_unit(long_only, _context())
    assert isinstance(bound_on_no_stated_side, tuple)
    assert {(p.kind, p.where) for p in bound_on_no_stated_side} == {
        ("motion_source", "/numbers/rsi_high/motion/source")
    }


def _put(path: str, value: object) -> Edit:
    def edit(document: Document) -> None:
        node: Any = document
        steps = path.split("/")
        for step in steps[:-1]:
            node = node[int(step)] if step.isdigit() else node[step]
        node[steps[-1]] = copy.deepcopy(value)

    return edit


def _defaults(block: str) -> Document:
    parameters = json.loads(_context().entries[block])["parameters"]
    return {name: {"value": str(spec["default"])} for name, spec in parameters.items()}


def _exit_at(index: int, block: str, inputs: Document | None = None) -> Edit:
    """`block` at its default parameters in place of `exit_set[index]`, whose number goes with it,
    or beside the three."""

    def edit(document: Document) -> None:
        binding = {
            "name": "probe",
            "scope": "position",
            "block": block,
            "params": _defaults(block),
            "inputs": inputs or {},
        }
        for replaced in document["exit_set"][index : index + 1]:
            for param in replaced["params"].values():
                del document["numbers"][param["number"]]
        document["exit_set"][index : index + 1] = [binding]

    return edit


def _gate(block: str) -> Edit:
    """`block` at its default parameters beside the long side's two context bindings."""

    def edit(document: Document) -> None:
        document["logic"]["long"]["slots"]["context"]["bindings"].append(
            {
                "name": "probe",
                "block": block,
                "params": _defaults(block),
                "inputs": {"series": "m15"},
            }
        )

    return edit


def _no_stop(document: Document) -> None:
    del document["exit_set"][0]
    del document["numbers"]["stop_buffer"]


def _mirrored(document: Document) -> None:
    document["logic"]["short"] = {"mirror_of": "long"}
    del document["numbers"]["rsi_high"]


_SESSION = {
    "name": "london",
    "calendar_ref": "fx-24x5@1",
    "zone": "Europe/London",
    "windows": [{"from": "08:00", "to": "16:00"}],
}
_BARS = {"series": "m15"}
_UNBOUND = {
    "kind": "fixed",
    "measure": "ratio",
    "range": {"min": "0", "max": "9", "step": "1"},
    "default": "2",
    "motion": {"mode": "fixed"},
    "authority": "motion_inside_range",
    "origin": "source_stated",
    "reason": "a spare number nothing binds, so the format refuses it by name",
}
_PARTS: dict[str, tuple[Edit, str, str]] = {
    "sessions": (_put("sessions", [_SESSION]), "sessions_not_built", "/sessions"),
    "settings": (
        _put("markets/0/settings", {"ema_period": "20"}),
        "settings_not_built",
        "/markets/0/settings",
    ),
    "settings record": (
        _put("markets/0/settings_record", "eurusd-settings@1"),
        "settings_not_built",
        "/markets/0/settings_record",
    ),
    "a number on open positions": (
        _put("numbers/stop_buffer/applies_to_open_positions", True),
        "open_positions_not_built",
        "/numbers/stop_buffer/applies_to_open_positions",
    ),
    "limit on a netting venue": (
        _put("position_limit", {"per_instrument": 3}),
        "position_limit_nets",
        "/position_limit",
    ),
    "price": (_put("streams/0/price", "mid"), "price_not_built", "/streams/0/price"),
    "input quotes": (_put("streams/0/input", "quotes"), "input_not_built", "/streams/0/input"),
    "bar kind tick": (
        _put("streams/0/bar", {"kind": "tick", "size": "100"}),
        "bar_not_built",
        "/streams/0/bar",
    ),
    "bar size against the stream's name": (
        _put("streams/0/bar/size", "3600"),
        "bar_not_built",
        "/streams/0/bar",
    ),
    "sole cadence at": (
        _put("numbers/min_trend_strength/motion/cadence", {"at": "market_day_close"}),
        "cadence_not_built",
        "/numbers/min_trend_strength/motion/cadence",
    ),
    "a stream naming one of two markets": (
        _put("streams/0/market", "fx.eurusd"),
        "market_not_built",
        "/streams/0/market",
    ),
    "a market's roll": (
        _put("markets/0/roll", {"rule": "calendar"}),
        "roll_not_built",
        "/markets/0/roll",
    ),
    "context needs": (
        _put("context_needs", {"block": [{"word": "fomc"}]}),
        "context_not_built",
        "/context_needs",
    ),
    "routes": (_put("routes", {"execution": "paper"}), "routes_not_built", "/routes"),
    "plain python": (
        _put("plain_python", {"block": "ema@1"}),
        "plain_python_not_built",
        "/plain_python",
    ),
    "a halt filed under another scope": (
        _put(
            "halts",
            {
                "position": [],
                "unit": [
                    {
                        "name": "probe",
                        "scope": "position",
                        "block": "equity-drawdown-halt@1",
                        "params": {"max_drawdown": {"value": "0.05"}, "trailing": {"value": "0"}},
                        "inputs": {},
                    }
                ],
                "account": [],
            },
        ),
        "halt_scope",
        "/halts/unit/0/scope",
    ),
    "an exit's scope": (
        _put("exit_set/0/scope", "account"),
        "exit_not_built",
        "/exit_set/0/scope",
    ),
    "a stop reading one field of its bars": (
        _put("exit_set/0/inputs/series", "m15.high"),
        "inputs_not_built",
        "/exit_set/0/inputs/series",
    ),
    "a target's own entry price": (
        _put("exit_set/1/inputs", {"entry_price": "m15.close"}),
        "inputs_not_built",
        "/exit_set/1/inputs/entry_price",
    ),
    "a sizer's own equity": (
        _put("sizer/inputs", {"equity": "m15.close"}),
        "inputs_not_built",
        "/sizer/inputs/equity",
    ),
    "k on an all combiner": (
        _put("logic/long/slots/context/combiner/k", 1),
        "combiner_not_built",
        "/logic/long/slots/context/combiner/k",
    ),
    "weights on an all combiner": (
        _put("logic/long/slots/context/combiner/weights", {"trend": "1", "strength": "2"}),
        "combiner_not_built",
        "/logic/long/slots/context/combiner/weights",
    ),
    "open on an all combiner": (
        _put("logic/long/slots/context/combiner/open", "0.5"),
        "combiner_not_built",
        "/logic/long/slots/context/combiner/open",
    ),
    "close on an all combiner": (
        _put("logic/long/slots/context/combiner/close", "0.5"),
        "combiner_not_built",
        "/logic/long/slots/context/combiner/close",
    ),
    "within_bars on an all combiner": (
        _put("logic/long/slots/context/combiner/within_bars", 3),
        "combiner_not_built",
        "/logic/long/slots/context/combiner/within_bars",
    ),
    "a fixed number nothing binds": (
        _put("numbers/max_spread", _UNBOUND),
        "number_not_read",
        "/numbers/max_spread",
    ),
    "a fixed number's source": (
        _put("numbers/ema_period/motion/source", "trend"),
        "motion_not_built",
        "/numbers/ema_period/motion/source",
    ),
    "a fixed number's rule params": (
        _put("numbers/ema_period/motion/rule_params", {"step": "1"}),
        "motion_not_built",
        "/numbers/ema_period/motion/rule_params",
    ),
    "a derived number's cadence": (
        _put("numbers/rsi_low/motion/cadence", {"every_closed_trades": 5}),
        "motion_not_built",
        "/numbers/rsi_low/motion/cadence",
    ),
    "a derived number's min_count": (
        _put("numbers/rsi_low/motion/min_count", 5),
        "motion_not_built",
        "/numbers/rsi_low/motion/min_count",
    ),
    "a derived number's shrink_k": (
        _put("numbers/rsi_low/motion/shrink_k", 5),
        "motion_not_built",
        "/numbers/rsi_low/motion/shrink_k",
    ),
    "a derived number's step_limit": (
        _put("numbers/rsi_low/motion/step_limit", 5),
        "motion_not_built",
        "/numbers/rsi_low/motion/step_limit",
    ),
    "a derived number's rule": (
        _put("numbers/rsi_low/motion/rule", "trend-floor-from-record@1"),
        "motion_not_built",
        "/numbers/rsi_low/motion/rule",
    ),
    "a rule param the rule does not declare": (
        _put("numbers/rsi_low/motion/rule_params/floor", "30"),
        "motion_not_built",
        "/numbers/rsi_low/motion/rule_params/floor",
    ),
    "a rule param the motion's own field sets": (
        _put("numbers/min_trend_strength/motion/rule_params/min_count", "3"),
        "motion_not_built",
        "/numbers/min_trend_strength/motion/rule_params/min_count",
    ),
    "a calibrated number moved from anything but its record": (
        _put("numbers/min_trend_strength/motion/source", "trend"),
        "motion_not_built",
        "/numbers/min_trend_strength/motion/source",
    ),
    "role veto": (
        _put("logic/long/slots/context/role", "veto"),
        "role_not_built",
        "/logic/long/slots/context/role",
    ),
    "two stops": (_exit_at(3, "swing-stop-buffer@1", _BARS), "exit_not_built", "/exit_set/3"),
    "two targets": (_exit_at(3, "target-r-multiple@1"), "exit_not_built", "/exit_set/3"),
    "unrealised-profit-cap": (
        _exit_at(2, "unrealised-profit-cap@1", _BARS),
        "exit_not_built",
        "/exit_set/2",
    ),
    "roi-table-exit": (_exit_at(2, "roi-table-exit@1", _BARS), "exit_not_built", "/exit_set/2"),
    "peak-holdings-giveback-exit": (
        _exit_at(2, "peak-holdings-giveback-exit@1", _BARS),
        "exit_not_built",
        "/exit_set/2",
    ),
    "offset-gated-trailing-stop": (
        _exit_at(0, "offset-gated-trailing-stop@1", _BARS),
        "exit_not_built",
        "/exit_set/0",
    ),
    "stepped-profit-stop": (
        _exit_at(0, "stepped-profit-stop@1", _BARS),
        "exit_not_built",
        "/exit_set/0",
    ),
    "profit-fraction-trailing-stop": (
        _exit_at(0, "profit-fraction-trailing-stop@1", _BARS),
        "exit_not_built",
        "/exit_set/0",
    ),
    "an indicator level as the stop": (
        _exit_at(0, "parabolic-sar@1", _BARS),
        "exit_not_built",
        "/exit_set/0",
    ),
    "no stop": (_no_stop, "stop_not_built", "/exit_set"),
    "a volume block": (
        _gate("money-flow-index@1"),
        "block_not_built",
        "/logic/long/slots/context/bindings/2/block",
    ),
    "a session block": (
        _gate("session-running-high@1"),
        "block_not_built",
        "/logic/long/slots/context/bindings/2/block",
    ),
    "period 0": (
        _put("logic/long/slots/context/bindings/0/params/period", {"value": "0"}),
        "bad_params",
        "/logic/long/slots/context/bindings/0",
    ),
    "a rule with a setting missing": (
        _put("numbers/min_trend_strength/motion/rule_params", {}),
        "bad_params",
        "/numbers/min_trend_strength/motion",
    ),
    "a mirror of side-neutral blocks": (_mirrored, "bad_mirror", "/logic/short/mirror_of"),
}


@pytest.mark.parametrize("part", sorted(_PARTS))
def test_each_part_format_2_does_not_run_refuses_with_a_pointer(part: str) -> None:
    edit, kind, where = _PARTS[part]
    document = cast("Document", _document())
    edit(document)

    problems = compile_unit(document, _context())
    checked = check(document, _context())

    assert isinstance(problems, tuple), "it compiled"
    assert {(p.kind, p.where) for p in problems} == {(kind, where)}
    assert checked.verdict.value == "fail"
    assert {pointer for p in checked.errors for pointer in p.where} == {where}


def test_an_hourly_bar_needs_the_hourly_name_because_the_name_is_what_replays() -> None:
    labelled_m15 = new(_document(), {"/streams/0/bar/size": "3600"})
    named_h1 = cast("Document", json.loads(json.dumps(labelled_m15).replace('"m15', '"h1')))

    problems = compile_unit(labelled_m15, _context())

    assert isinstance(problems, tuple), "it compiled"
    assert [p.message for p in problems] == [
        "m15 replays as 900 second bars, and this stream says 3600"
    ]
    assert _compiled(named_h1).plan.stream == "h1"


def test_a_stream_naming_the_only_market_trades_as_written() -> None:
    document = cast("Document", _document())
    del document["markets"][1]
    _put("streams/0/market", "fx.eurusd")(document)

    assert [market.market_id for market, _ in _compiled(document).plan.markets] == ["fx.eurusd"]


def test_an_empty_context_needs_or_routes_says_nothing_and_compiles() -> None:
    document = cast("Document", _document())
    document["context_needs"] = {"require": [], "warn": [], "block": []}
    document["routes"] = {"data": {}}

    assert isinstance(compile_unit(document, _context()), CompiledUnit)


def _schema_fields(shape: Shape) -> set[str]:
    match shape:
        case Array(item=inner) | Map(value=inner):
            return _schema_fields(inner)
        case OneOf(choices=choices):
            return {name for choice in choices for name in _schema_fields(choice)}
        case Record(model=model, fields=fields):
            own = {f"{model.__name__}.{field.key}" for field in fields}
            return own.union(*(_schema_fields(field.shape) for field in fields))
        case _:
            return set()


def _guide_refusals() -> dict[str, str]:
    """The generated guide's field table: each field, and the code format 4 refuses it with."""
    rows: dict[str, str] = {}
    for line in _GUIDE.read_text("utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0].startswith("`"):
            rows[cells[0].strip("`")] = "" if cells[2] == "-" else cells[2].strip("`")
    return rows


def _unlisted(fields: set[str]) -> set[str]:
    return fields - _CENSUS


def test_every_unit_field_is_run_refused_or_labelled() -> None:
    """Every schema field is in the census and the guide, `reads` refuses with its code and
    pointer, and a field the census does not hold is named, not waved through."""
    fields = _schema_fields(shape_of())
    assert fields == _CENSUS, (
        "a unit schema field is not in this list. Make the compiled unit read it, refuse it in "
        "qml/compile/compiler.py, or keep it only if it labels, then name it here"
    )

    assert _GUIDE.is_file(), "qml/EXTENDING.md is generated; run tools/qml/extending.py"
    guide = _guide_refusals()
    assert set(guide) == _CENSUS, (
        "qml/EXTENDING.md and the census disagree about the unit's fields; regenerate the "
        "guide with tools/qml/extending.py"
    )
    assert guide["Unit.reads"] == "reads_not_built"

    document = cast("Document", _document())
    _put("reads", _READS)(document)
    problems = compile_unit(document, _context())
    assert isinstance(problems, tuple), "the reads document compiled"
    assert [(p.kind, p.where) for p in problems if p.kind == "reads_not_built"] == [
        ("reads_not_built", "/reads")
    ]

    assert _unlisted(fields) == set()
    assert _unlisted(fields | {"Unit.probe"}) == {"Unit.probe"}


def test_a_mirror_of_a_side_neutral_block_says_state_both_sides() -> None:
    document = cast("Document", _document())
    _mirrored(document)

    checked = check(document, _context())

    assert {(p.kind.value, p.hint) for p in checked.errors} == {("bad_mirror", "state both sides")}


def test_two_refusals_are_listed_at_once() -> None:
    document = cast("Document", _document())
    _put("sessions", [_SESSION])(document)
    _gate("vwap-session-anchored@1")(document)

    checked = check(document, _context())

    assert {pointer for p in checked.errors for pointer in p.where} == {
        "/sessions",
        "/logic/long/slots/context/bindings/2/block",
    }


def test_a_unit_with_no_time_exit_steps_and_holds_its_position() -> None:
    document = cast("Document", _document())
    del document["exit_set"][2]
    del document["numbers"]["time_out_bars"]
    bars = _slice()
    instants = _instants(bars)[:100]
    compiled = _compiled(document)
    position = OwnPosition(
        "pos-1",
        Side.LONG,
        Decimal("0.10"),
        Decimal("1.08000"),
        compiled.compiled_fingerprint,
        instants[0],
    )

    steps = _drive(
        _host(
            compiled,
            _surfaces(bars, positions=lambda m, _i: position if m == "fx.eurusd" else None),
        ),
        instants,
    )

    assert len(steps) == 100
    assert [i for s in steps for i in s.intents if isinstance(i, UnitExitIntent)] == []
    assert "no_time_exit" in {p.kind.value for p in check(document, _context()).warnings}
