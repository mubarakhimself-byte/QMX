"""``compile_unit(document, context)``: check, load the pinned blocks, wire them, fingerprint.

The host passes everything as data: the decoded document, the bytes of each pinned block's
``block.py`` and ``entry.json``, and the instrument record of each market. The compiler reads
no file and no clock. It refuses a document with any problem and returns every problem at once:
the checker's layers A to F, the loader's, and what compiler format 1 does not run yet.

What the compiler decides, so the closure stays data plus blocks:

- A slot binding is a condition by its output. A ``Signal`` holds or not. A price ``series``
  output (the dummy's EMA) is a level the side's price must be beyond: the binding's own input
  above it on the long side, below it on the short side. An ``entry_order`` output holds.
- An exit binding's use comes from its face. A price ``level`` that reads the position's
  ``stop_price`` is the target; any other price ``level`` is the protective stop; an
  ``exit_action`` runs once per bar for each open position.
- A derived number's ``motion.source`` names the binding whose output value feeds it, on each
  side that binds the number. A number both sides bind runs one motion instance per side, so
  each side's window holds one value per bar. Its mode picks the motion block by the table below.

The compiled fingerprint is fp1 over the document's fingerprint, the lock's, the compiler
format version and the port quantum, so a recompile of the same bytes gives the same value.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from qmf.core.fingerprint import Fingerprint, fingerprint
from qmf.core.refusal import is_refusal

from qml.blocks.api import (
    PORT_QUANTUM_SIGNIFICANT_DIGITS,
    Block,
    EntryFace,
    OutputType,
    parse_entry,
)
from qml.catalogue.loader import Loaded, LockEntry, load
from qml.check.layers import check_layers
from qml.motion.engine import MIN_TRADES, SHRINK_K, SLOW_CADENCE_TRADES, SlowNumber
from qml.numbers.records import InstrumentRecord
from qml.unit.model import (
    Binding,
    CombinerKind,
    Market,
    MirrorSide,
    MotionMode,
    NumberKind,
    NumberParam,
    Role,
    ScopedBinding,
    Side,
    Slot,
    SlotsSide,
    Unit,
    ValueParam,
)
from qml.unit.parse import parse

if TYPE_CHECKING:
    from qml.protocol.unit import UnitFactory

__all__ = [
    "COMPILER_FORMAT_VERSION",
    "BoundBlock",
    "CompileContext",
    "CompileProblem",
    "CompiledUnit",
    "DerivedPlan",
    "ExitPlan",
    "ExitUse",
    "Plan",
    "SidePlan",
    "SlotPlan",
    "SlowPlan",
    "compile_unit",
]

COMPILER_FORMAT_VERSION: Final[int] = 1
"""Bumped by any compiler change that alters a decision, which makes a new fingerprint."""

COMBINERS: Final[frozenset[CombinerKind]] = frozenset(
    {CombinerKind.ALL, CombinerKind.ANY, CombinerKind.K_OF_N}
)
DERIVED_BLOCKS: Final[Mapping[MotionMode, str]] = {
    MotionMode.PERCENTILE_OF_OWN_HISTORY: "percentile-of-own-history@1",
}
SLOW_MODES: Final[frozenset[MotionMode]] = frozenset({MotionMode.SHRINK_FROM_OWN_TRADES})


@dataclass(frozen=True, slots=True)
class CompileProblem:
    """One reason the document does not compile, with its layer and a JSON pointer."""

    layer: str
    kind: str
    where: str
    message: str


@dataclass(frozen=True, slots=True)
class CompileContext:
    """What the host gathered: block sources and faces by pin, records by the unit's market id."""

    sources: Mapping[str, bytes]
    entries: Mapping[str, bytes]
    records: Mapping[str, InstrumentRecord]


@dataclass(frozen=True, slots=True)
class BoundBlock:
    """One binding wired to its loaded block. ``key`` is unique in the unit."""

    key: str
    name: str
    pin: str
    block: Block
    face: EntryFace
    params: Mapping[str, NumberParam | ValueParam]
    inputs: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class SlotPlan:
    name: str
    role: Role
    combiner: CombinerKind
    absent_is_false: bool
    k: int | None
    bindings: tuple[BoundBlock, ...]


@dataclass(frozen=True, slots=True)
class SidePlan:
    side: Side
    slots: tuple[SlotPlan, ...]


class ExitUse(StrEnum):
    STOP = "stop"
    TARGET = "target"
    PER_BAR = "per_bar"


@dataclass(frozen=True, slots=True)
class ExitPlan:
    binding: BoundBlock
    use: ExitUse


@dataclass(frozen=True, slots=True)
class DerivedPlan:
    """A derived number fed each bar by ``source``'s output on ``side``."""

    number: str
    side: Side
    source: str
    pin: str
    block: Block
    params: Mapping[str, Decimal]


@dataclass(frozen=True, slots=True)
class SlowPlan:
    number: SlowNumber
    block: Block
    params: Mapping[str, Decimal]


@dataclass(frozen=True, slots=True)
class Plan:
    """The compiled closure as data: what runs, in order, on each bar of each market."""

    stream: str
    markets: tuple[tuple[Market, InstrumentRecord], ...]
    sides: tuple[SidePlan, ...]
    exits: tuple[ExitPlan, ...]
    sizer: BoundBlock
    derived: tuple[DerivedPlan, ...]
    slow: tuple[SlowPlan, ...]
    defaults: Mapping[str, Decimal]


@dataclass(frozen=True, slots=True)
class CompiledUnit:
    """CONTRACTS.md section 4.1, less the footprint and parameter projection (see the PR)."""

    unit: Unit
    plan: Plan
    lock: tuple[LockEntry, ...]
    document_fingerprint: Fingerprint
    lock_fingerprint: Fingerprint
    compiled_fingerprint: Fingerprint
    compiler_format_version: int
    options: Mapping[str, int]
    warm_up: Mapping[str, int]
    state_bound: int
    placeholders: tuple[str, ...]
    trace_schema: tuple[str, ...]

    @property
    def factory(self) -> UnitFactory:
        """A factory satisfying ``BotFactory``; ``construct_bot`` on it refuses the first sized
        intent, because units are hosted through ``construct_unit`` (BR-A4)."""
        from qml.protocol.unit import UnitFactory  # noqa: PLC0415 - the door imports this module

        return UnitFactory(self)


TRACE_SCHEMA: Final[tuple[str, ...]] = (
    "row_id",
    "instant",
    "market_id",
    "side",
    "outcome",
    "slot_trail",
    "readings_used",
    "numbers_in_force",
    "reason",
)


class _Problems:
    def __init__(self) -> None:
        self.found: list[CompileProblem] = []

    def add(self, kind: str, where: str, message: str) -> None:
        self.found.append(CompileProblem("compile", kind, where, message))


def _decimal(text: str) -> Decimal | None:
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _defaults(unit: Unit) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for name, spec in unit.numbers.items():
        value = _decimal(spec.default)
        if value is not None:
            out[name] = value
    return out


def _side_slots(unit: Unit, side: Side) -> tuple[Side, Mapping[str, Slot]] | None:
    given = unit.logic.long if side is Side.LONG else unit.logic.short
    if isinstance(given, MirrorSide):
        other = unit.logic.long if given.mirror_of is Side.LONG else unit.logic.short
        return (side, other.slots) if isinstance(other, SlotsSide) else None
    if isinstance(given, SlotsSide):
        return side, given.slots
    return None


class _Wiring:
    """Binds each document binding to its loaded block and records what does not fit."""

    def __init__(
        self, unit: Unit, loaded: Loaded, faces: Mapping[str, EntryFace], problems: _Problems
    ) -> None:
        self.unit = unit
        self.loaded = loaded
        self.faces = faces
        self.problems = problems

    def bind(self, binding: Binding, key: str) -> BoundBlock | None:
        """The binding wired to its block; layer B names one whose block does not resolve."""
        pin = str(binding.block)
        block, face = self.loaded.blocks.get(pin), self.faces.get(pin)
        if block is None or face is None:
            return None
        return BoundBlock(
            key=key,
            name=binding.name,
            pin=pin,
            block=block,
            face=face,
            params=binding.params,
            inputs=binding.inputs,
        )

    def side(self, side: Side) -> SidePlan | None:
        found = _side_slots(self.unit, side)
        if found is None:
            return None
        _, slots = found
        planned: list[SlotPlan] = []
        for slot_name, slot in slots.items():
            where = f"/logic/{side.value}/slots/{slot_name}"
            if slot.combiner.kind not in COMBINERS:
                self.problems.add(
                    "combiner_not_built",
                    f"{where}/combiner/kind",
                    f"combiner {slot.combiner.kind.value} is not in compiler format "
                    f"{COMPILER_FORMAT_VERSION}",
                )
            bound = [
                one
                for binding in slot.bindings
                if (one := self.bind(binding, f"{side.value}.{binding.name}")) is not None
            ]
            planned.append(
                SlotPlan(
                    name=slot_name,
                    role=slot.role,
                    combiner=slot.combiner.kind,
                    absent_is_false=slot.combiner.when_inputs_absent.value == "treat_as_false",
                    k=slot.combiner.k,
                    bindings=tuple(bound),
                )
            )
        return SidePlan(side, tuple(planned))

    def exit(self, binding: ScopedBinding, index: int) -> ExitPlan | None:
        bound = self.bind(binding, f"exit.{binding.name}")
        if bound is None:
            return None
        output = bound.face.output
        if output.type is OutputType.EXIT_ACTION:
            return ExitPlan(bound, ExitUse.PER_BAR)
        if output.type is OutputType.LEVEL and output.measure == "price":
            reads_stop = any(port.port == "stop_price" for port in bound.face.inputs)
            return ExitPlan(bound, ExitUse.TARGET if reads_stop else ExitUse.STOP)
        self.problems.add(
            "exit_not_built",
            f"/exit_set/{index}",
            f"{bound.pin} outputs {output.type.value}, which no exit use takes",
        )
        return None


def _bound_on(side: SidePlan, number: str) -> bool:
    return any(
        isinstance(p, NumberParam) and p.number == number
        for slot in side.slots
        for b in slot.bindings
        for p in b.params.values()
    )


def _motion(
    unit: Unit, sides: Sequence[SidePlan], loaded: Loaded, problems: _Problems
) -> tuple[tuple[DerivedPlan, ...], tuple[SlowPlan, ...]]:
    derived: list[DerivedPlan] = []
    slow: list[SlowPlan] = []
    for name, spec in unit.numbers.items():
        where = f"/numbers/{name}/motion"
        motion = spec.motion
        if spec.kind is NumberKind.DERIVED:
            pin = DERIVED_BLOCKS.get(motion.mode)
            block = loaded.blocks.get(pin) if pin is not None else None
            if pin is None or block is None:
                problems.add("motion_not_built", where, f"no pinned block runs {motion.mode.value}")
                continue
            params = {k: d for k, v in motion.rule_params.items() if (d := _decimal(v)) is not None}
            hosts = [s for s in sides if _bound_on(s, name)]
            sources = [
                s
                for s in hosts
                for slot in s.slots
                for b in slot.bindings
                if b.name == motion.source
            ]
            if not hosts or len(sources) != len(hosts):
                problems.add(
                    "motion_source",
                    f"{where}/source",
                    f"{motion.source} names no binding on every side that binds {name}",
                )
                continue
            derived.extend(
                DerivedPlan(name, s.side, str(motion.source), pin, block, params) for s in hosts
            )
        elif spec.kind is NumberKind.CALIBRATED:
            rule = str(motion.rule) if motion.rule is not None else ""
            block = loaded.blocks.get(rule)
            stamp = next(
                (
                    b.name
                    for s in sides
                    for slot in s.slots
                    for b in slot.bindings
                    if any(
                        isinstance(p, NumberParam) and p.number == name for p in b.params.values()
                    )
                ),
                None,
            )
            if (
                motion.mode not in SLOW_MODES
                or block is None
                or stamp is None
                or spec.range is None
            ):
                problems.add(
                    "motion_not_built",
                    where,
                    f"{name} needs a pinned rule, a range and a binding that stamps it at entry",
                )
                continue
            params = {k: d for k, v in motion.rule_params.items() if (d := _decimal(v)) is not None}
            default = _decimal(spec.default) or Decimal(0)
            params |= {
                "min_count": Decimal(
                    motion.min_count if motion.min_count is not None else MIN_TRADES
                ),
                "shrink_k": Decimal(motion.shrink_k if motion.shrink_k is not None else SHRINK_K),
                "step_limit": Decimal(motion.step_limit or 1),
                "min": spec.range.min,
                "max": spec.range.max,
                "step": spec.range.step,
                "default": default,
            }
            every = (
                motion.cadence.every_closed_trades if motion.cadence else None
            ) or SLOW_CADENCE_TRADES
            slow.append(SlowPlan(SlowNumber(name, rule, stamp, every), block, params))
    return tuple(derived), tuple(slow)


def _values(bound: BoundBlock, defaults: Mapping[str, Decimal]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for name, param in bound.params.items():
        if isinstance(param, ValueParam):
            out[name] = param.value
        elif param.number in defaults:
            out[name] = defaults[param.number]
    return out


def _warm_up(plan: Plan) -> tuple[int, int]:
    """The bars a market needs before entries, and the unit's summed state bound.

    A binding is warm at the later of its recorded settle length and the bars its upstream
    needs plus its own warm-up; a derived number at its source's plus its block's.
    """
    warm: dict[str, int] = {}
    bound_total = 0
    for side in plan.sides:
        for slot in side.slots:
            for b in slot.bindings:
                instance = b.block.make(_values(b, plan.defaults), b.inputs, side.side)
                upstream = max(
                    (warm.get(f"{side.side.value}.{ref}", 0) for ref in b.inputs.values()),
                    default=0,
                )
                settle = b.face.settle.bars if b.face.settle is not None else 0
                warm[b.key] = max(settle, upstream + instance.warm_up_bars)
                bound_total += instance.state_bound
    for d in plan.derived:
        instance = d.block.make(d.params, {}, d.side)
        warm[f"derived.{d.side.value}.{d.number}"] = (
            warm.get(f"{d.side.value}.{d.source}", 0) + instance.warm_up_bars
        )
        bound_total += instance.state_bound
    for e in plan.exits:
        instance = e.binding.block.make(_values(e.binding, plan.defaults), e.binding.inputs)
        warm[e.binding.key] = instance.warm_up_bars
        bound_total += instance.state_bound
    return max(warm.values(), default=0), bound_total


def _faces(
    unit: Unit, context: CompileContext
) -> tuple[tuple[LockEntry, ...], dict[str, EntryFace]]:
    """The lock and the faces that read; layer B names every pin whose face does not."""
    lock = tuple(LockEntry(p.entry_id, p.version, p.fingerprint) for p in unit.pins)
    faces: dict[str, EntryFace] = {}
    for entry in lock:
        raw = context.entries.get(entry.pin)
        face = parse_entry(raw) if raw is not None else None
        if isinstance(face, EntryFace):
            faces[entry.pin] = face
    return lock, faces


def _markets(unit: Unit, context: CompileContext) -> tuple[tuple[Market, InstrumentRecord], ...]:
    """Each market with its record; layer D names a market whose record is missing."""
    return tuple(
        (market, record)
        for market in unit.markets
        if (record := context.records.get(market.market_id)) is not None
    )


def _shape_problems(unit: Unit, problems: _Problems) -> None:
    if len(unit.streams) != 1:
        problems.add("streams_not_built", "/streams", "compiler format 1 runs one stream")
    if unit.reads:
        problems.add("reads_not_built", "/reads", "compiler format 1 reads no readings")
    if unit.halts.position or unit.halts.unit or unit.halts.account:
        problems.add("halts_not_built", "/halts", "compiler format 1 runs no halt blocks")


def compile_unit(
    document: object, context: CompileContext
) -> CompiledUnit | tuple[CompileProblem, ...]:
    """The compiled unit, or every problem that stops it compiling."""
    parsed = parse(document)
    if parsed.unit is None:
        return tuple(
            CompileProblem(p.layer, p.kind.value, "/".join(p.where), p.message)
            for p in parsed.problems
        )
    unit = parsed.unit
    problems = _Problems()
    checked = check_layers(
        unit, entries=context.entries, sources=context.sources, records=context.records
    )
    problems.found.extend(
        CompileProblem(p.layer, p.kind.value, "/".join(p.where), p.message) for p in checked.errors
    )
    _shape_problems(unit, problems)
    lock, faces = _faces(unit, context)
    loaded = load(lock, context.sources)
    if not isinstance(loaded, Loaded):
        problems.found.extend(
            CompileProblem("compile", p.kind.value, p.pin, p.message) for p in loaded
        )
        return tuple(problems.found)
    markets = _markets(unit, context)
    wiring = _Wiring(unit, loaded, faces, problems)
    sides = tuple(s for side in (Side.LONG, Side.SHORT) if (s := wiring.side(side)) is not None)
    exits = tuple(e for i, b in enumerate(unit.exit_set) if (e := wiring.exit(b, i)) is not None)
    sizer = wiring.bind(unit.sizer, "sizer") if unit.sizer is not None else None
    derived, slow = _motion(unit, sides, loaded, problems)
    document_fp = fingerprint(document)
    if is_refusal(document_fp):
        problems.add("document_fingerprint", "", str(document_fp.context.get("reason")))
    if problems.found or sizer is None or is_refusal(document_fp):
        return tuple(problems.found)
    plan = Plan(
        stream=unit.streams[0].name,
        markets=markets,
        sides=sides,
        exits=exits,
        sizer=sizer,
        derived=derived,
        slow=slow,
        defaults=_defaults(unit),
    )
    warm_up, state_bound = _warm_up(plan)
    options = {"port_quantum_significant_digits": PORT_QUANTUM_SIGNIFICANT_DIGITS}
    compiled_fp = fingerprint(
        {
            "document": document_fp.value.value,
            "lock": loaded.lock_fingerprint.value,
            "compiler_format_version": COMPILER_FORMAT_VERSION,
            "options": options,
        }
    )
    if is_refusal(compiled_fp):  # pragma: no cover - the content is all text and integers
        raise ValueError(json.dumps(dict(compiled_fp.context), default=str))
    bound_all = [b for s in sides for slot in s.slots for b in slot.bindings]
    bound_all += [e.binding for e in exits] + [sizer]
    placeholders = tuple(
        dict.fromkeys(
            b.name
            for b in bound_all
            if b.face.origin == "placeholder"  # mock-data-scan: allow (the origin label)
        )
    )
    return CompiledUnit(
        unit=unit,
        plan=plan,
        lock=lock,
        document_fingerprint=document_fp.value,
        lock_fingerprint=loaded.lock_fingerprint,
        compiled_fingerprint=compiled_fp.value,
        compiler_format_version=COMPILER_FORMAT_VERSION,
        options=options,
        warm_up={plan.stream: warm_up},
        state_bound=state_bound,
        placeholders=placeholders,
        trace_schema=TRACE_SCHEMA,
    )
