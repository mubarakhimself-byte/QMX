"""Layers B to F of the unit check, over a unit that passed layer A (AD-110).

Every check reads only the document, the pinned entries and their block sources, and the
instrument records, so an error is a fact decidable from those inputs. Heuristics are
warnings. Layer C's number rules are ``qml.numbers.check``; this module adds only what needs
the entries, the measure each bound parameter port declares.
"""

from __future__ import annotations

import ast
import difflib
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final, cast

from qmf.core.refusal import is_refusal

from qml.blocks.api import EntryFace, FaceProblem, Mirroring, OutputType, parse_entry
from qml.catalogue.loader import block_fingerprint
from qml.check.result import (
    AGENT_BANNED_ATTRIBUTES,
    AGENT_BANNED_NAMES,
    AGENT_DUNDER_ASSIGNS,
    AGENT_IMPORTS,
)
from qml.conformance.scan import scan_logic_source
from qml.numbers.check import check_numbers
from qml.numbers.records import InstrumentRecord
from qml.unit.model import (
    Binding,
    CombinerKind,
    Direction,
    Measure,
    MirrorSide,
    NumberParam,
    Origin,
    Role,
    RootRef,
    Side,
    Slot,
    SlotsSide,
    StreamInput,
    Unit,
)
from qml.unit.parse import Problem, ProblemKind

__all__ = ["TRADED_SIDES", "Found", "check_block", "check_layers"]

_PLACEHOLDER: Final = "placeholder"  # mock-data-scan: allow (the risk session's origin label)
_AGENT: Final = "agent"
_REVIEWED_ORIGINS: Final = frozenset({"qml", "port-239", _PLACEHOLDER})
_BAR_FIELDS: Final = frozenset({"", "open", "high", "low", "close"})
_BOUND_PORT_KINDS: Final = frozenset({"series", "bars"})
_STRUCTURAL_LITERALS: Final = frozenset({0, 1, -1})


@dataclass
class Found:
    """Problems of layers B to F, errors and warnings apart, in the order found."""

    errors: list[Problem] = field(default_factory=list[Problem])
    warnings: list[Problem] = field(default_factory=list[Problem])

    def error(
        self,
        layer: str,
        kind: ProblemKind,
        where: str,
        message: str,
        hint: str,
        nearest: tuple[str, ...] = (),
    ) -> None:
        self.errors.append(Problem(kind, (where,), message[:300], hint[:300], layer, nearest))

    def warning(self, layer: str, kind: ProblemKind, where: str, message: str, hint: str) -> None:
        self.warnings.append(Problem(kind, (where,), message[:300], hint[:300], layer))


def _at(parent: str, *keys: str | int) -> str:
    for key in keys:
        parent += "/" + str(key).replace("~", "~0").replace("/", "~1")
    return parent


def _nearest(wanted: str, known: Sequence[str]) -> tuple[str, ...]:
    return tuple(difflib.get_close_matches(wanted, sorted(known), n=3, cutoff=0.6))


@dataclass(frozen=True)
class _Use:
    """One binding of the unit: where it sits, which side it runs on, and the names before it."""

    where: str
    binding: Binding
    side: Side | None
    earlier: tuple[str, ...]


def _sides(unit: Unit) -> Iterator[tuple[Side, Mapping[str, Slot]]]:
    for side, given in ((Side.LONG, unit.logic.long), (Side.SHORT, unit.logic.short)):
        if isinstance(given, SlotsSide):
            yield side, given.slots


def _uses(unit: Unit) -> Iterator[_Use]:
    for side, slots in _sides(unit):
        names: list[str] = []
        for slot_name, slot in slots.items():
            for index, binding in enumerate(slot.bindings):
                where = _at("/logic", side.value, "slots", slot_name, "bindings", index)
                yield _Use(where, binding, side, tuple(names))
                names.append(binding.name)
    for index, binding in enumerate(unit.exit_set):
        yield _Use(_at("/exit_set", index), binding, None, ())
    if unit.sizer is not None:
        yield _Use("/sizer", unit.sizer, None, ())
    for index, binding in enumerate(unit.modifiers):
        yield _Use(_at("/modifiers", index), binding, None, ())
    for scope in ("position", "unit", "account"):
        for index, binding in enumerate(getattr(unit.halts, scope)):
            yield _Use(_at("/halts", scope, index), binding, None, ())


# --- layer B: references -------------------------------------------------------------


def _pins(
    unit: Unit,
    entries: Mapping[str, bytes],
    sources: Mapping[str, bytes],
    found: Found,
) -> dict[str, EntryFace]:
    faces: dict[str, EntryFace] = {}
    seen: set[str] = set()
    for index, pin in enumerate(unit.pins):
        where = _at("/pins", index)
        ref = f"{pin.entry_id}@{pin.version}"
        if ref in seen:
            found.error(
                "B", ProblemKind.DUPLICATE_NAME, where, f"{ref} is pinned twice", "pin it once"
            )
            continue
        seen.add(ref)
        raw = entries.get(ref)
        if raw is None:
            found.error(
                "B",
                ProblemKind.PIN_UNRESOLVED,
                where,
                f"no entry {ref} was found",
                "pin an entry that exists at that version",
                _nearest(ref, list(entries)),
            )
            continue
        face = parse_entry(raw)
        if isinstance(face, FaceProblem):
            found.error(
                "B",
                ProblemKind.ENTRY_FACE,
                where,
                f"{ref}'s entry does not read: {face.where} {face.message}",
                "fix the entry's machine face",
            )
            continue
        if face.pin != ref:
            found.error(
                "B",
                ProblemKind.ENTRY_FACE,
                where,
                f"the entry given for {ref} is {face.pin}",
                "gather the entry the pin names",
            )
            continue
        if face.fingerprint != pin.fingerprint:
            found.error(
                "B",
                ProblemKind.PIN_FINGERPRINT,
                _at(where, "fingerprint"),
                f"{ref}'s entry names {face.fingerprint}, the pin {pin.fingerprint}",
                "pin the fingerprint the entry names, or pin the version you tested",
            )
        source = sources.get(ref)
        if source is None:
            found.error(
                "B",
                ProblemKind.BLOCK_SOURCE_MISSING,
                where,
                f"{ref} has no block source, so nothing can run it",
                "a slot binds a block with code; write the block first",
            )
        elif block_fingerprint(source).value != pin.fingerprint:
            found.error(
                "B",
                ProblemKind.PIN_FINGERPRINT,
                _at(where, "fingerprint"),
                f"{ref}'s block source does not have the pinned fingerprint",
                "pin the block's current fingerprint as a successor version",
            )
        faces[ref] = face
    return faces


def _binding(
    unit: Unit, use: _Use, faces: Mapping[str, EntryFace], streams: frozenset[str], found: Found
) -> EntryFace | None:
    pin = str(use.binding.block)
    face = faces.get(pin)
    if face is None:
        if pin not in {f"{p.entry_id}@{p.version}" for p in unit.pins}:
            found.error(
                "B",
                ProblemKind.BLOCK_NOT_PINNED,
                _at(use.where, "block"),
                f"{pin} is not in the unit's pins",
                "pin the block's entry, or bind a pinned one",
                _nearest(pin, list(faces)),
            )
        return None
    for name in face.parameters:
        if name not in use.binding.params:
            found.error(
                "B",
                ProblemKind.PARAMETER_MISSING,
                _at(use.where, "params"),
                f"{pin} needs its parameter {name}",
                f"bind {name} to a number or a value",
            )
    for name, param in use.binding.params.items():
        where = _at(use.where, "params", name)
        if name not in face.parameters:
            found.error(
                "B",
                ProblemKind.UNKNOWN_PARAMETER,
                where,
                f"{pin} has no parameter {name}",
                f"its parameters are {', '.join(sorted(face.parameters)) or 'none'}",
                _nearest(name, list(face.parameters)),
            )
            continue
        if not isinstance(param, NumberParam):
            continue
        spec = unit.numbers.get(param.number)
        if spec is None:
            found.error(
                "B",
                ProblemKind.UNDECLARED_NUMBER,
                where,
                f"{param.number} is not declared under numbers",
                "declare it under numbers, or bind a declared one",
                _nearest(param.number, list(unit.numbers)),
            )
            continue
        wanted = face.parameter_measure(name)
        if wanted is not None and spec.measure is not wanted:
            found.error(
                "C",
                ProblemKind.MEASURE_MISMATCH,
                where,
                f"{pin}'s {name} takes {wanted.value}, and {param.number} is {spec.measure.value}",
                f"bind a {wanted.value} number, or convert through the instrument record",
            )
    ports = {port.port: port for port in face.inputs}
    for port, ref in use.binding.inputs.items():
        where = _at(use.where, "inputs", port)
        if port not in ports:
            found.error(
                "B",
                ProblemKind.UNKNOWN_PORT,
                where,
                f"{pin} has no input port {port}",
                f"its ports are {', '.join(sorted(ports)) or 'none'}",
                _nearest(port, list(ports)),
            )
        stream, _, part = ref.partition(".")
        if stream in streams and part in _BAR_FIELDS:
            continue
        if ref not in use.earlier:
            takes_a_bar = port in ports and ports[port].stream_kind == "bars"
            found.error(
                "B",
                ProblemKind.UNKNOWN_INPUT,
                where,
                f"{ref} is neither a stream field nor an earlier binding",
                "feed the whole bar by its stream's name, such as m15"
                if takes_a_bar
                else "feed one value such as m15.close, or a binding written before this one",
                _nearest(ref, list(streams if takes_a_bar else use.earlier)),
            )
    for port in face.inputs:
        if port.stream_kind in _BOUND_PORT_KINDS and port.port not in use.binding.inputs:
            found.error(
                "B",
                ProblemKind.INPUT_MISSING,
                _at(use.where, "inputs"),
                f"{pin} reads its {port.stream_kind} port {port.port}, and nothing feeds it",
                f"set inputs.{port.port}",
            )
    return face


def _names(unit: Unit, found: Found) -> None:
    seen: set[str] = set()
    for index, market in enumerate(unit.markets):
        if market.market_id in seen:
            found.error(
                "B",
                ProblemKind.DUPLICATE_NAME,
                _at("/markets", index, "market_id"),
                f"the market {market.market_id} is listed twice",
                "list each market once",
            )
        seen.add(market.market_id)
    for side, slots in _sides(unit):
        _unique(
            [
                (_at("/logic", side.value, "slots", s, "bindings", i, "name"), b.name)
                for s, slot in slots.items()
                for i, b in enumerate(slot.bindings)
            ],
            found,
        )
    _unique([(_at("/exit_set", i, "name"), b.name) for i, b in enumerate(unit.exit_set)], found)


def _unique(named: Sequence[tuple[str, str]], found: Found) -> None:
    seen: set[str] = set()
    for where, name in named:
        if name in seen:
            found.error(
                "B",
                ProblemKind.DUPLICATE_NAME,
                where,
                f"two bindings here are named {name}",
                "give each binding its own name",
            )
        seen.add(name)


def _shape_refs(unit: Unit, faces: Mapping[str, EntryFace], found: Found) -> None:
    markets = {m.market_id for m in unit.markets}
    streams = {s.name for s in unit.streams}
    for index, stream in enumerate(unit.streams):
        if stream.market != "*" and stream.market not in markets:
            found.error(
                "B",
                ProblemKind.UNKNOWN_MARKET,
                _at("/streams", index, "market"),
                f"{stream.market} is not one of the unit's markets",
                'name a market_id, or "*" for every market',
                _nearest(stream.market, list(markets)),
            )
        if stream.derived_from is not None and stream.derived_from not in streams - {stream.name}:
            found.error(
                "B",
                ProblemKind.UNKNOWN_STREAM,
                _at("/streams", index, "derived_from"),
                f"{stream.derived_from} is not another stream of the unit",
                "derive from a stream the unit declares",
            )
    for index, read in enumerate(unit.reads):
        if str(read.reading) not in faces:
            found.error(
                "B",
                ProblemKind.BLOCK_NOT_PINNED,
                _at("/reads", index, "reading"),
                f"{read.reading} is not in the unit's pins",
                "a unit reads readings it pins, never another unit",
                _nearest(str(read.reading), list(faces)),
            )
        if read.market not in markets:
            found.error(
                "B",
                ProblemKind.UNKNOWN_MARKET,
                _at("/reads", index, "market"),
                f"{read.market} is not one of the unit's markets",
                "read for a market the unit trades",
            )
    for name, spec in unit.numbers.items():
        rule = spec.motion.rule
        if rule is not None and str(rule) not in faces:
            found.error(
                "B",
                ProblemKind.BLOCK_NOT_PINNED,
                _at("/numbers", name, "motion", "rule"),
                f"{rule} is not in the unit's pins",
                "pin the motion rule's entry",
                _nearest(str(rule), list(faces)),
            )
    for side, given in (("long", unit.logic.long), ("short", unit.logic.short)):
        if isinstance(given, MirrorSide):
            other = unit.logic.long if given.mirror_of is Side.LONG else unit.logic.short
            if given.mirror_of.value == side or not isinstance(other, SlotsSide):
                found.error(
                    "B",
                    ProblemKind.BAD_MIRROR,
                    _at("/logic", side, "mirror_of"),
                    f"the {side} side mirrors {given.mirror_of.value}, which states no slots",
                    "mirror the other side, and write that side's slots",
                )
                continue
            for slot in other.slots.values():
                for binding in slot.bindings:
                    face = faces.get(str(binding.block))
                    if face is not None and face.mirroring is not Mirroring.SUPPORTED:
                        found.error(
                            "B",
                            ProblemKind.BAD_MIRROR,
                            _at("/logic", side, "mirror_of"),
                            f"the {side} side mirrors {binding.block}, which has no mirror image",
                            "state both sides",
                        )
    for side, slots in _sides(unit):
        for slot_name, slot in slots.items():
            _combiner(slot, _at("/logic", side.value, "slots", slot_name, "combiner"), found)


def _combiner(slot: Slot, where: str, found: Found) -> None:
    combiner = slot.combiner
    names = {b.name for b in slot.bindings}
    if combiner.kind is CombinerKind.K_OF_N and (
        combiner.k is None or combiner.k > len(slot.bindings)
    ):
        found.error(
            "B",
            ProblemKind.BAD_COMBINER,
            _at(where, "k"),
            f"k_of_n needs a k from 1 to {len(slot.bindings)}, the slot's binding count",
            "set k",
        )
    if combiner.kind is CombinerKind.WEIGHTED and set(combiner.weights) != names:
        found.error(
            "B",
            ProblemKind.BAD_COMBINER,
            _at(where, "weights"),
            "a weighted combiner weighs exactly the slot's bindings",
            f"give weights for {', '.join(sorted(names))}",
        )


# --- layer C: what qml.numbers.check cannot see ------------------------------------------

_TWO_PLACES: Final = Decimal("0.01")
_WHOLE_PERCENT_STEP: Final = Decimal("0.01")
_WHOLE_PERCENT_MAX: Final = Decimal("0.1")


def _percent_looks_whole(unit: Unit, found: Found) -> None:
    """Warn on a percent number written as if 1 meant one percent.

    The rule: the default, the range and the step all have at most two decimal places, the
    step is at least 0.01 and the max at least 0.1. Such a number moves in whole percentage
    points up to 10% or more, which reads like whole percents typed as fractions. A value
    with a third decimal place (0.005 for half a percent) never warns.
    """
    for name, spec in unit.numbers.items():
        span = spec.range
        if spec.measure is not Measure.PERCENT or span is None:
            continue
        try:
            default = Decimal(spec.default)
        except ArithmeticError:
            continue
        values = (default, span.min, span.max, span.step)
        if (
            all(v == v.quantize(_TWO_PLACES) for v in values)
            and span.step >= _WHOLE_PERCENT_STEP
            and span.max >= _WHOLE_PERCENT_MAX
        ):
            found.warning(
                "C",
                ProblemKind.PERCENT_LOOKS_WHOLE,
                _at("/numbers", name),
                f"{name} is stored as a fraction, so its default {spec.default} means "
                f"{default * 100}% and its range reaches {span.max * 100}%",
                'if you meant whole percents, divide by 100: one percent is "0.01"',
            )


def _cadence_at(unit: Unit, found: Found) -> None:
    """Warn on an ``at`` beside ``every_closed_trades``: the count runs and the ``at`` does not. A
    lone ``at`` is the compiler's refusal, because the number would move on the default count and
    the ``at`` would not run."""
    for name, spec in unit.numbers.items():
        cadence = spec.motion.cadence
        if cadence is None or cadence.at is None or cadence.every_closed_trades is None:
            continue
        found.warning(
            "C",
            ProblemKind.CADENCE_NOT_BUILT,
            _at("/numbers", name, "motion", "cadence", "at"),
            f"{name} moves every {cadence.every_closed_trades} closed trades, and its "
            f"{cadence.at.value} does not run yet",
            "drop the at, or read the number as moving on the count alone",
        )


# --- layer D: data levels and calendars ------------------------------------------------


def _levels(record: InstrumentRecord) -> frozenset[int] | None:
    raw = record.data_levels.get("levels")
    if not isinstance(raw, list):
        return None
    given = cast("list[object]", raw)
    levels = [level for level in given if isinstance(level, int) and not isinstance(level, bool)]
    return frozenset(levels) if len(levels) == len(given) else None


def _data(
    unit: Unit,
    bound: Sequence[tuple[_Use, EntryFace]],
    records: Mapping[str, InstrumentRecord],
    found: Found,
) -> None:
    offered: dict[str, frozenset[int]] = {}
    for index, market in enumerate(unit.markets):
        record = records.get(market.market_id)
        if record is None:
            found.error(
                "D",
                ProblemKind.NO_RECORD,
                _at("/markets", index),
                f"no instrument record was given for {market.market_id}",
                "check against the market's instrument record",
            )
            continue
        levels = _levels(record)
        if levels is None:
            found.warning(
                "D",
                ProblemKind.DATA_LEVELS_UNKNOWN,
                _at("/markets", index),
                f"the record {record.name} lists no data levels, so layer D could not compare",
                "the record's data_levels.levels is a list of level numbers",
            )
            continue
        offered[market.market_id] = levels
    given = [records[m.market_id] for m in unit.markets if m.market_id in records]
    if len(given) == len(unit.markets):
        held = sorted({record.calendar_ref for record in given})
        for s_index, session in enumerate(unit.sessions):
            if session.calendar_ref not in held:
                found.error(
                    "D",
                    ProblemKind.CALENDAR_NOT_HELD,
                    _at("/sessions", s_index, "calendar_ref"),
                    f"{session.calendar_ref} is not a calendar any market's record holds "
                    f"({', '.join(held)})",
                    "name the calendar of a market the unit trades",
                )
    for use, face in bound:
        for port in face.inputs:
            if port.data_level is None:
                continue
            for market_id, levels in offered.items():
                if port.data_level not in levels:
                    found.error(
                        "D",
                        ProblemKind.DATA_LEVEL_MISSING,
                        _at(use.where, "block"),
                        f"{face.pin} reads data level {port.data_level} on {port.port}, "
                        f"which {market_id} does not offer",
                        "bind a block this market's data can feed, or drop the market",
                    )
    for index, stream in enumerate(unit.streams):
        if stream.input is StreamInput.CLOSED_BARS:
            continue
        for market_id, levels in offered.items():
            if 2 not in levels and stream.market in ("*", market_id):
                found.error(
                    "D",
                    ProblemKind.DATA_LEVEL_MISSING,
                    _at("/streams", index, "input"),
                    f"{stream.input.value} need quote ticks (level 2), which {market_id} "
                    "does not offer",
                    "read closed bars, or drop the market",
                )


# --- layer E: completeness ---------------------------------------------------------------

TRADED_SIDES: Final[Mapping[Direction, tuple[Side, ...]]] = {
    Direction.LONG: (Side.LONG,),
    Direction.SHORT: (Side.SHORT,),
    Direction.BOTH: (Side.LONG, Side.SHORT),
}
"""The sides a unit's ``direction`` trades. Layer E wants them stated and the compiler builds only
them."""


def _side_slots(unit: Unit, side: Side) -> Mapping[str, Slot] | None:
    given = unit.logic.long if side is Side.LONG else unit.logic.short
    if isinstance(given, MirrorSide):
        given = unit.logic.long if given.mirror_of is Side.LONG else unit.logic.short
    return given.slots if isinstance(given, SlotsSide) else None


def _complete(unit: Unit, bound: Sequence[tuple[_Use, EntryFace]], found: Found) -> None:
    if not unit.markets:
        found.error(
            "E", ProblemKind.NO_MARKET, "/markets", "the unit trades no market", "add a market"
        )
    needed = TRADED_SIDES[unit.direction]
    for side in (Side.LONG, Side.SHORT):
        given = unit.logic.long if side is Side.LONG else unit.logic.short
        where = _at("/logic", side.value)
        if side not in needed:
            if given is not None:
                found.warning(
                    "E",
                    ProblemKind.SIDE_UNUSED,
                    where,
                    f"the unit trades {unit.direction.value}, so its {side.value} side never runs",
                    "remove the side, or set direction to both",
                )
            continue
        if given is None:
            found.error(
                "E",
                ProblemKind.SIDE_MISSING,
                where,
                f"the unit trades {unit.direction.value} and states no {side.value} side",
                f'write the {side.value} slots, or {{"mirror_of": ...}} the other side',
            )
            continue
        slots = _side_slots(unit, side)
        if slots is not None and not any(
            s.role is Role.TRIGGER and s.bindings for s in slots.values()
        ):
            found.error(
                "E",
                ProblemKind.NO_TRIGGER,
                where,
                f"the {side.value} side has no trigger, so it never enters",
                "add a trigger slot with a binding",
            )
    if not unit.exit_set:
        found.error(
            "E", ProblemKind.NO_EXIT, "/exit_set", "the unit has no exit", "add an exit set"
        )
    if unit.sizer is None:
        found.error(
            "E",
            ProblemKind.SIZER_MISSING,
            "/sizer",
            "a unit that enters needs a sizer",
            "bind a sizer block",
        )
    if not unit.claim_card.sources:
        found.error(
            "E",
            ProblemKind.NO_SOURCE,
            "/claim_card/sources",
            "the claim card cites no source",
            "cite where the idea comes from",
        )
    for index, market in enumerate(unit.markets):
        if isinstance(market.instrument_ref, RootRef) and market.roll is None:
            found.error(
                "E",
                ProblemKind.NO_ROLL,
                _at("/markets", index, "roll"),
                f"{market.market_id} is a future with no roll rule, so a contract would expire",
                "set roll with its rule",
            )
    for use, face in bound:
        if face.origin == _PLACEHOLDER:
            found.warning(
                "E",
                ProblemKind.PLACEHOLDER,
                use.where,
                f"this binds a {_PLACEHOLDER} block that {face.owner or 'its owner'} replaces",
                "trade it on demo only until the real block lands",
            )
    for name, spec in unit.numbers.items():
        if spec.origin is Origin.PLACEHOLDER:
            found.warning(
                "E",
                ProblemKind.PLACEHOLDER,
                _at("/numbers", name, "origin"),
                f"this number's value is a {_PLACEHOLDER}",
                "replace it with a value from a source",
            )
    if not (unit.halts.position or unit.halts.unit or unit.halts.account):
        found.warning(
            "E",
            ProblemKind.NO_HALTS,
            "/halts",
            "the unit names no brakes",
            "add a halt, or rely on the account's own",
        )
    timed = any(
        face.output.type is OutputType.EXIT_ACTION and face.output.measure in ("bars", "seconds")
        for use, face in bound
        if use.where.startswith("/exit_set")
    )
    if unit.exit_set and not timed:
        found.warning(
            "E",
            ProblemKind.NO_TIME_EXIT,
            "/exit_set",
            "no exit is bounded in time, so a position may stay open indefinitely",
            "add a time exit",
        )


# --- layer F: code safety ----------------------------------------------------------------


def _chain(node: ast.AST) -> tuple[str, ...]:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return tuple(reversed(parts))


def _dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def _widened(tree: ast.AST) -> Iterator[tuple[int, str]]:
    """Deny by default: an import outside ``AGENT_IMPORTS``, any dunder read, any banned name.

    Spelling out ``exec`` and ``eval`` cannot hold, since ``getattr``, ``builtins``, ``vars``,
    a frame's globals and a dunder walk each reach them under another name. So every road
    to a namespace or to builtins is closed instead.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in AGENT_IMPORTS:
                    yield node.lineno, f"import {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            if module not in AGENT_IMPORTS:
                yield node.lineno, f"from {module} import"
        elif isinstance(node, ast.Name):
            assigns = isinstance(node.ctx, ast.Store) and node.id in AGENT_DUNDER_ASSIGNS
            if node.id in AGENT_BANNED_NAMES or (_dunder(node.id) and not assigns):
                yield node.lineno, f"uses {node.id}"
        elif isinstance(node, ast.Attribute):
            if node.attr in AGENT_BANNED_ATTRIBUTES or _dunder(node.attr):
                yield node.lineno, f"uses {'.'.join(_chain(node))}"
        elif isinstance(node, ast.MatchClass):
            for attr in node.kwd_attrs:
                if _dunder(attr) or attr in AGENT_BANNED_ATTRIBUTES:
                    yield node.lineno, f"matches on {attr}"


def _literals(tree: ast.AST) -> Iterator[tuple[int, object]]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for operand in (node.left, *node.comparators):
                value = operand
                if isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.USub):
                    value = value.operand
                if (
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, int | float)
                    and not isinstance(value.value, bool)
                    and value.value not in _STRUCTURAL_LITERALS
                ):
                    yield node.lineno, value.value


def check_block(pin: str, origin: str, source: bytes, where: str = "") -> Found:
    """Layer F over one block's source: the kept scan, then the rules for agent code.

    The kept scan's clock, I/O and network findings are errors for every block. Unseeded
    random and the deny-by-default rules of ``_widened`` are errors when an agent wrote the
    block, and warnings for human plain Python. Numeric literals in comparisons warn for agent
    and human blocks only, because QML's own blocks are reviewed and golden-tested; 0, 1 and
    -1 never warn.
    """
    found = Found()
    text = source.decode("utf-8", errors="replace")
    agent = origin == _AGENT
    scanned = scan_logic_source({"block.py": text}, declared_seed=False)
    if is_refusal(scanned):
        found.error(
            "F",
            ProblemKind.BLOCK_SYNTAX,
            where,
            f"{pin}'s source does not parse as Python",
            "fix the syntax error",
        )
        return found
    for finding in scanned.value.findings:
        message = f"{pin} line {finding.lineno}: {finding.detail} ({finding.capability})"
        hint = "a block reads only its evidence; it never reads a clock, a file or the network"
        if finding.capability != "undeclared_randomness":
            found.error("F", ProblemKind.UNSAFE_CODE, where, message, hint)
        elif agent:
            found.error("F", ProblemKind.UNSAFE_CODE, where, message, "seed any randomness")
        else:
            found.warning("F", ProblemKind.UNSAFE_CODE, where, message, "seed any randomness")
    tree = ast.parse(text)
    for lineno, detail in _widened(tree):
        message = f"{pin} line {lineno}: {detail}"
        hint = (
            "a block computes from its evidence, imports only "
            f"{', '.join(sorted(AGENT_IMPORTS))}, and never reaches builtins, a namespace "
            "or a dunder"
        )
        if agent:
            found.error("F", ProblemKind.UNSAFE_CODE, where, message, hint)
        else:
            found.warning("F", ProblemKind.UNSAFE_CODE, where, message, hint)
    if origin not in _REVIEWED_ORIGINS:
        for lineno, value in _literals(tree):
            found.warning(
                "F",
                ProblemKind.LITERAL_IN_COMPARISON,
                where,
                f"{pin} line {lineno} compares against the literal {value}",
                "make the threshold a parameter bound to a number",
            )
    return found


def _code(
    unit: Unit, faces: Mapping[str, EntryFace], sources: Mapping[str, bytes], found: Found
) -> None:
    for index, pin in enumerate(unit.pins):
        ref = f"{pin.entry_id}@{pin.version}"
        face, source = faces.get(ref), sources.get(ref)
        if face is None or source is None:
            continue
        one = check_block(ref, face.origin, source, _at("/pins", index))
        found.errors.extend(one.errors)
        found.warnings.extend(one.warnings)


# --- all of them ---------------------------------------------------------------------------


def check_layers(
    unit: Unit,
    *,
    entries: Mapping[str, bytes],
    sources: Mapping[str, bytes],
    records: Mapping[str, InstrumentRecord],
) -> Found:
    """Every problem of layers B to F in ``unit``, in layer order."""
    found = Found()
    faces = _pins(unit, entries, sources, found)
    streams = frozenset(s.name for s in unit.streams)
    bound: list[tuple[_Use, EntryFace]] = []
    for use in _uses(unit):
        face = _binding(unit, use, faces, streams, found)
        if face is not None:
            bound.append((use, face))
    _names(unit, found)
    _shape_refs(unit, faces, found)
    numbers = check_numbers(unit, records)
    found.errors.extend(numbers.errors)
    found.warnings.extend(numbers.warnings)
    _percent_looks_whole(unit, found)
    _cadence_at(unit, found)
    _data(unit, bound, records, found)
    _complete(unit, bound, found)
    _code(unit, faces, sources, found)
    order = {layer: i for i, layer in enumerate("ABCDEF")}
    found.errors.sort(key=lambda p: order.get(p.layer, len(order)))
    found.warnings.sort(key=lambda p: order.get(p.layer, len(order)))
    return found
