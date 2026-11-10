"""``compile_unit(document, context)``: check, load the pinned blocks, wire them, fingerprint.

The host passes everything as data: the decoded document, the bytes of each pinned block's
``block.py`` and ``entry.json``, and the instrument record of each market. The compiler reads
no file and no clock. It refuses a document with any problem and returns every problem at once:
the checker's layers A to F, the loader's, and what this compiler format does not run yet. So a
unit that compiles trades as it reads, and a part with nothing behind it refuses by name.

What the compiler decides, so the closure stays data plus blocks:

- Sides follow ``direction``. A side the unit does not trade is not built.
- A slot binding is a condition by its output. An ``event`` or ``state`` output holds or not. A
  price ``series`` output (the dummy's EMA) is a level the side's price must be beyond: the
  binding's own input above it on the long side, below it on the short side, and the bar's close
  when that input is a whole bar. An ``entry_order`` output holds.
- A binding with any other output is a feeder when a later binding or a derived number reads it,
  and it refuses when nothing does. A binding that reads a surface no slot is fed refuses too.
- An exit binding's use comes from its face. A price ``level`` that reads the position's
  ``stop_price`` is the target; any other price ``level`` is the protective stop; an
  ``exit_action`` runs once per bar for each open position. A unit runs one of each use, and it
  must have the stop.
- A derived number's ``motion.source`` names the binding whose output value feeds it, on each
  side that binds the number. A number both sides bind runs one motion instance per side, so
  each side's window holds one value per bar. Its mode picks the motion block by the table below.

The compiled fingerprint is fp1 over the logic half's fingerprint, the risk half's, the lock's,
the compiler format version and the port quantum, so a recompile of the same bytes gives the
same value and a size edit moves only the risk half.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, fields, replace
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, cast

from qmf.core.fingerprint import Fingerprint, fingerprint
from qmf.core.refusal import is_refusal
from qmf.risk.controls import ControlRow

from qml.blocks.api import (
    PORT_QUANTUM_SIGNIFICANT_DIGITS,
    Block,
    EntryFace,
    Instance,
    OutputType,
    parse_entry,
)
from qml.catalogue.loader import Loaded, LockEntry, load
from qml.check.layers import TRADED_SIDES, check_layers
from qml.motion.engine import (
    MIN_TRADES,
    SHRINK_K,
    SLOW_CADENCE_TRADES,
    ScaledNumber,
    SlowNumber,
)
from qml.numbers.records import InstrumentRecord
from qml.unit.model import (
    Authority,
    BarKind,
    Binding,
    Cautious,
    Combiner,
    CombinerKind,
    ControlBinding,
    Market,
    MirrorSide,
    Motion,
    MotionMode,
    NumberKind,
    NumberParam,
    NumberSpec,
    Price,
    Role,
    Scope,
    ScopedBinding,
    Side,
    Slot,
    SlotsSide,
    StreamInput,
    Unit,
    ValueParam,
)
from qml.unit.parse import parse
from qml.unit.sections import sections

if TYPE_CHECKING:
    from qml.protocol.unit import UnitFactory

__all__ = [
    "BLOCKS_NOT_BUILT",
    "COMPILER_FORMAT_VERSION",
    "BoundBlock",
    "CompileContext",
    "CompileProblem",
    "CompiledUnit",
    "DerivedPlan",
    "ExitPlan",
    "ExitUse",
    "HaltPlan",
    "Plan",
    "SidePlan",
    "SlotPlan",
    "SlowPlan",
    "compile_unit",
]

COMPILER_FORMAT_VERSION: Final[int] = 9
"""Bumped by any compiler change that alters a decision, which makes a new fingerprint."""
_FORMAT: Final[str] = f"compiler format {COMPILER_FORMAT_VERSION}"

COMBINERS: Final[frozenset[CombinerKind]] = frozenset(
    {CombinerKind.ALL, CombinerKind.ANY, CombinerKind.K_OF_N}
)
ROLES_BUILT: Final[frozenset[Role]] = frozenset(
    {
        Role.CONTEXT,
        Role.LOCATION,
        Role.SETUP,
        Role.TRIGGER,
        Role.CONFIRMATION,
        Role.FILTER,
        Role.ENTRY_ORDER,
    }
)
_VOLUME: Final[str] = "volume, which no bar carries yet"
_CLOCK: Final[str] = "a clock it does not have: use version 2 and name its clock"
BLOCKS_NOT_BUILT: Final[Mapping[str, str]] = {
    "accumulation-distribution@1": _VOLUME,
    "chaikin-oscillator@1": _VOLUME,
    "force-index@1": _VOLUME,
    "market-facilitation-index@1": _VOLUME,
    "money-flow-index@1": _VOLUME,
    "on-balance-volume@1": _VOLUME,
    "initial-balance-high@1": _CLOCK,
    "initial-balance-low@1": _CLOCK,
    "initial-balance-range-extension@1": _CLOCK,
    "session-running-high@1": _CLOCK,
    "session-running-low@1": _CLOCK,
    "session-running-range@1": _CLOCK,
    "tpo-point-of-control@1": _CLOCK,
    "tpo-value-area-high@1": _CLOCK,
    "tpo-value-area-low@1": _CLOCK,
    "vwap-session-anchored@1": _CLOCK,
    "vwap-session-anchored@2": _VOLUME,
}
"""A binding on one of these refuses, with what it needs. A pin alone does not."""
_HOLDING_OUTPUTS: Final[frozenset[OutputType]] = frozenset(
    {OutputType.EVENT, OutputType.STATE, OutputType.ENTRY_ORDER}
)
_SIZER_ANSWERS: Final[frozenset[OutputType]] = frozenset({OutputType.AMOUNT, OutputType.QUANTITY})
"""What a sizer's face may answer: a typed amount, or the legacy lots a ``Size`` states. Any
other face in that slot would have nothing the one converter can spell (AD-10)."""
_SLOT_PORT_KINDS: Final[frozenset[str]] = frozenset({"series", "bars"})
"""The input kinds a slot binding is fed, as layer B wires them. Account, position, record and
trades facts reach a sizer, an exit or a rule through their own doors, and never a slot."""
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
    """One binding wired to its loaded block. ``key`` is unique in the unit, and ``where`` is the
    binding's JSON pointer in the document."""

    key: str
    name: str
    pin: str
    block: Block
    face: EntryFace
    params: Mapping[str, NumberParam | ValueParam]
    inputs: Mapping[str, str]
    where: str


@dataclass(frozen=True, slots=True)
class SlotPlan:
    """``feeders`` names the bindings that only feed a later binding or a derived number, so they
    are no conditions. A slot left with no conditions holds, whatever its combiner."""

    name: str
    role: Role
    combiner: CombinerKind
    absent_is_false: bool
    k: int | None
    bindings: tuple[BoundBlock, ...]
    where: str
    feeders: frozenset[str] = frozenset()

    @property
    def has_conditions(self) -> bool:
        return len(self.bindings) > len(self.feeders)


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
class HaltPlan:
    """One brake: its block wired to its parameters, and the control row the unit runs."""

    binding: BoundBlock
    control: ControlRow


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
    halts: tuple[HaltPlan, ...]
    sizer: BoundBlock
    derived: tuple[DerivedPlan, ...]
    slow: tuple[SlowPlan, ...]
    scaled: tuple[ScaledNumber, ...]
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
    logic_fingerprint: Fingerprint
    risk_fingerprint: Fingerprint
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
        problem = CompileProblem("compile", kind, where, message)
        if problem not in self.found:  # a mirrored side repeats the side it mirrors
            self.found.append(problem)


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
    """The slots ``side`` runs, with the side they are written on."""
    given = unit.logic.long if side is Side.LONG else unit.logic.short
    if isinstance(given, MirrorSide):
        other = unit.logic.long if given.mirror_of is Side.LONG else unit.logic.short
        return (given.mirror_of, other.slots) if isinstance(other, SlotsSide) else None
    if isinstance(given, SlotsSide):
        return side, given.slots
    return None


def _holds_a_slot(face: EntryFace) -> bool:
    """Whether the runtime reads ``face``'s output as a condition."""
    output = face.output
    return output.type in _HOLDING_OUTPUTS or (
        output.type is OutputType.SERIES and output.measure == "price"
    )


def _exit_use(face: EntryFace) -> ExitUse | None:
    output = face.output
    if output.type is OutputType.EXIT_ACTION:
        return ExitUse.PER_BAR
    if output.type is OutputType.LEVEL and output.measure == "price":
        reads_stop = any(port.port == "stop_price" for port in face.inputs)
        return ExitUse.TARGET if reads_stop else ExitUse.STOP
    return None


def _exit_gap(face: EntryFace, use: ExitUse | None) -> str | None:
    """Why this format cannot run ``face`` as an exit, by its shape and never by its name, so an
    agent's block of the same shape refuses too. A per-bar exit's ports are the position and the
    bar the host hands it, and it names none of its own; a stop is read with nothing at entry."""
    if use is None:
        return f"{face.pin} outputs {face.output.type.value}, which no exit use takes"
    if face.component_type != "exit":
        return f"{face.pin} is a {face.component_type} block, so nothing reads its level at entry"
    if use is ExitUse.PER_BAR and face.inputs:
        return (
            f"{face.pin} is not built yet: it names inputs of its own, and this format runs a "
            "per-bar exit whose ports are the position and the bar it is handed. Which inputs a "
            "per-bar exit may name is the risk session's"
        )
    reads_position = any(port.stream_kind == "position" for port in face.inputs)
    if use is ExitUse.STOP and reads_position:
        return (
            f"{face.pin} is not built yet: it reads the position, and a stop is read before the "
            "entry it protects"
        )
    return None


def _exit_inputs_unread(bound: BoundBlock) -> dict[str, str]:
    """The ports of an exit whose written reference runs nothing: the host feeds its bars port
    whole bars and its position ports the position, whatever the document says."""
    whole_bars = {port.port for port in bound.face.inputs if port.stream_kind == "bars"}
    return {port: ref for port, ref in bound.inputs.items() if port not in whole_bars or "." in ref}


def _combiner_extras(combiner: Combiner) -> tuple[str, ...]:
    """The combiner's written fields that ``_Run.combine`` does not read."""
    written = {
        "k": combiner.k is not None and combiner.kind is not CombinerKind.K_OF_N,
        "weights": bool(combiner.weights),
        "open": combiner.open is not None,
        "close": combiner.close is not None,
        "within_bars": combiner.within_bars is not None,
    }
    return tuple(name for name, is_written in written.items() if is_written)


_HALT_FACTS: Final[Mapping[str, str]] = MappingProxyType({"account": "account", "trades": "own"})
"""The fact namespaces a control row may read, by the port kind its block declares."""


class _Wiring:
    """Binds each document binding to its loaded block and records what does not fit."""

    def __init__(
        self, unit: Unit, loaded: Loaded, faces: Mapping[str, EntryFace], problems: _Problems
    ) -> None:
        self.unit = unit
        self.loaded = loaded
        self.faces = faces
        self.problems = problems

    def bind(self, binding: Binding, key: str, where: str) -> BoundBlock | None:
        """The binding wired to its block; layer B names one whose block does not resolve."""
        pin = str(binding.block)
        block, face = self.loaded.blocks.get(pin), self.faces.get(pin)
        if block is None or face is None:
            return None
        needs = BLOCKS_NOT_BUILT.get(pin)
        if needs is not None:
            self.problems.add("block_not_built", f"{where}/block", f"{pin} needs {needs}")
        return BoundBlock(
            key=key,
            name=binding.name,
            pin=pin,
            block=block,
            face=face,
            params=binding.params,
            inputs=binding.inputs,
            where=where,
        )

    def side(self, side: Side) -> SidePlan | None:
        found = _side_slots(self.unit, side)
        if found is None:
            return None
        written_on, slots = found
        planned: list[SlotPlan] = []
        for slot_name, slot in slots.items():
            where = f"/logic/{written_on.value}/slots/{slot_name}"
            if slot.combiner.kind not in COMBINERS:
                self.problems.add(
                    "combiner_not_built",
                    f"{where}/combiner/kind",
                    f"combiner {slot.combiner.kind.value} is not in {_FORMAT}",
                )
            for extra in _combiner_extras(slot.combiner):
                self.problems.add(
                    "combiner_not_built",
                    f"{where}/combiner/{extra}",
                    f"{_FORMAT} reads no {extra} on a {slot.combiner.kind.value} combiner, so this "
                    "slot would hold or not without it",
                )
            if slot.role not in ROLES_BUILT:
                self.problems.add(
                    "role_not_built",
                    f"{where}/role",
                    f"{_FORMAT} runs no slot of role {slot.role.value}",
                )
            bound: list[BoundBlock] = []
            for index, binding in enumerate(slot.bindings):
                one = self.bind(
                    binding, f"{side.value}.{binding.name}", f"{where}/bindings/{index}"
                )
                if one is not None:
                    bound.append(one)
            planned.append(
                SlotPlan(
                    name=slot_name,
                    role=slot.role,
                    combiner=slot.combiner.kind,
                    absent_is_false=slot.combiner.when_inputs_absent.value == "treat_as_false",
                    k=slot.combiner.k,
                    bindings=tuple(bound),
                    where=where,
                )
            )
        return SidePlan(side, tuple(planned))

    def exits(self) -> tuple[ExitPlan, ...]:
        """The exits this format runs, in the order the document writes them: one stop, one
        target, and any number of per-bar exits. The per-bar exits are the stack one bar's
        decision comes from, so their order is the order they answer in. A refused stop still
        counts as stated, so its own refusal is the one he reads."""
        planned: list[ExitPlan] = []
        stated: set[ExitUse] = set()
        unresolved = False
        for index, binding in enumerate(self.unit.exit_set):
            where = f"/exit_set/{index}"
            if binding.scope is not Scope.POSITION:
                self.problems.add(
                    "exit_not_built",
                    f"{where}/scope",
                    f"{_FORMAT} runs an exit per position, not on the {binding.scope.value}",
                )
            bound = self.bind(binding, f"exit.{binding.name}", where)
            if bound is None:
                unresolved = True
                continue
            for port, ref in _exit_inputs_unread(bound).items():
                self.problems.add(
                    "inputs_not_built",
                    f"{where}/inputs/{port}",
                    f"{_FORMAT} hands an exit whole bars and its position, so it never reads {ref}",
                )
            use = _exit_use(bound.face)
            gap = _exit_gap(bound.face, use)
            if gap is not None:
                self.problems.add("exit_not_built", where, gap)
            elif use in stated and use is not ExitUse.PER_BAR:
                self.problems.add(
                    "exit_not_built", where, f"{_FORMAT} runs one {use} exit, and this is another"
                )
            elif use is not None:
                planned.append(ExitPlan(bound, use))
            if use is not None:
                stated.add(use)
        if ExitUse.STOP not in stated and not unresolved:
            self.problems.add(
                "stop_not_built",
                "/exit_set",
                f"{_FORMAT} runs a unit with one price stop. Whether a unit may have none is the "
                "risk session's",
            )
        return tuple(planned)

    def halts(self) -> tuple[HaltPlan, ...]:
        """The brake rows this format runs, in scope order and document order.

        A row's ``reads`` are named from its block's declared ports, so a row never states a fact
        its block does not read. The five shipped halts read account and trades facts, which the
        unit supplies from its account surface and its own journal. A block that is not a halt,
        or that declares a port the runner cannot feed, is refused by name here rather than
        answering nothing forever. The list a row sits in decides where it runs, so a row whose
        own ``scope`` disagrees with that list is refused rather than re-scoped in silence.
        """
        planned: list[HaltPlan] = []
        for scope in (Scope.POSITION, Scope.UNIT, Scope.ACCOUNT):
            seen: set[str] = set()
            for index, binding in enumerate(getattr(self.unit.halts, scope.value)):
                where = f"/halts/{scope.value}/{index}"
                if binding.scope is not scope:
                    self.problems.add(
                        "halt_scope",
                        f"{where}/scope",
                        f"{_FORMAT} runs a row in the {scope.value} list, and this row's scope "
                        f"says {binding.scope.value}",
                    )
                    continue
                if binding.name in seen:
                    self.problems.add(
                        "duplicate_name", f"{where}/name", "two halt rows at one scope share a name"
                    )
                seen.add(binding.name)
                bound = self.bind(binding, f"halt.{scope.value}.{binding.name}", where)
                if bound is None:
                    continue
                if bound.face.component_type != "halt":
                    self.problems.add(
                        "halt_not_built",
                        where,
                        f"{_FORMAT} runs a halt row as a brake, and {bound.pin} answers a "
                        f"{bound.face.component_type}",
                    )
                planned.append(
                    HaltPlan(
                        binding=bound,
                        control=ControlRow(
                            name=binding.name,
                            pin=bound.pin,
                            code=bound.face.entry_id,
                            scope=scope.value,
                            reads=self._halt_reads(bound, where),
                            verb=binding.verb,
                            shadow=binding.shadow,
                        ),
                    )
                )
        return tuple(planned)

    def _halt_reads(self, bound: BoundBlock, where: str) -> tuple[str, ...]:
        """The facts one row reads, named from its block's declared ports."""
        reads: list[str] = []
        for port in bound.face.inputs:
            namespace = _HALT_FACTS.get(port.stream_kind)
            if namespace is None:
                self.problems.add(
                    "halt_not_built",
                    where,
                    f"{_FORMAT} feeds a halt row account and own-journal facts, and {bound.pin} "
                    f"reads a {port.stream_kind} port",
                )
                continue
            reads.append(f"{namespace}.{port.port}")
        return tuple(reads)


def _binds(binding: Binding | ControlBinding | ScopedBinding, number: str) -> bool:
    """Whether one binding reads ``number`` as a parameter."""
    return any(
        isinstance(p, NumberParam) and p.number == number for p in binding.params.values()
    )


def _bound_on(side: SidePlan, number: str) -> bool:
    return any(_binds(b, number) for slot in side.slots for b in slot.bindings)


def _risk_bindings(unit: Unit) -> tuple[Binding | ControlBinding | ScopedBinding, ...]:
    """The bindings outside the logic slots: the sizer, the exits and the control rows (AD-14)."""
    controls = (*unit.halts.position, *unit.halts.unit, *unit.halts.account)
    return (*([unit.sizer] if unit.sizer is not None else ()), *unit.exit_set, *controls)


def _stamp_for(unit: Unit, number: str) -> str | None:
    """The entry stamp the rule reads for ``number``: a stated side's binding name, or
    ``number:<name>`` for a sizer, exit or control number (AD-14's first step).

    A logic number keeps the stamp its slot binding already writes (``strength`` for the trend
    floor); a risk number has no slot, so its stamp is its own value in force at entry.
    """
    for side in Side:
        found = _side_slots(unit, side)
        if found is None:
            continue
        for slot in found[1].values():
            for binding in slot.bindings:
                if _binds(binding, number):
                    return binding.name
    return f"number:{number}" if any(_binds(b, number) for b in _risk_bindings(unit)) else None


def _only_on_a_dropped_side(unit: Unit, number: str) -> bool:
    """Whether ``number`` is bound on a stated side ``direction`` does not trade, and on no other,
    so nothing runs it. A number bound on no stated side is not this, and still refuses. A number
    a sizer, exit or control row reads runs whatever the side says, so it is not this either."""
    if any(_binds(b, number) for b in _risk_bindings(unit)):
        return False
    binding_sides = {
        side
        for side in Side
        if (found := _side_slots(unit, side)) is not None
        and any(_binds(b, number) for slot in found[1].values() for b in slot.bindings)
    }
    return bool(binding_sides) and not binding_sides.intersection(TRADED_SIDES[unit.direction])


def _bound_numbers(unit: Unit) -> set[str]:
    """Every number a binding on a stated side, an exit, the sizer or a control row reads."""
    bindings: list[Binding | ControlBinding | ScopedBinding] = [
        binding
        for side in Side
        if (found := _side_slots(unit, side)) is not None
        for slot in found[1].values()
        for binding in slot.bindings
    ]
    bindings += list(_risk_bindings(unit))
    return {
        param.number
        for binding in bindings
        for param in binding.params.values()
        if isinstance(param, NumberParam)
    }


def _unread_rule_params(
    given: Mapping[str, str],
    face: EntryFace | None,
    set_here: Mapping[str, Decimal],
    where: str,
    problems: _Problems,
) -> None:
    """A rule param the block does not declare, or one the compiler sets itself, runs nothing."""
    if face is None:
        return
    for key in sorted(given.keys() - (face.parameters.keys() - set_here.keys())):
        problems.add(
            "motion_not_built", f"{where}/rule_params/{key}", f"{face.pin} never reads {key} here"
        )


def _scaled(
    name: str,
    spec: NumberSpec,
    where: str,
    problems: _Problems,
) -> ScaledNumber | None:
    """A ``scaled`` number's row: the fact it follows, its multiple, and its range.

    ``rule_params`` carries one key, ``multiple``, because there is no rule block here: the fact
    times the multiple is the whole arithmetic. A key the compiler does not read is refused by
    name, so a document cannot state a mechanism nothing runs.
    """
    motion = spec.motion
    for key in sorted(motion.rule_params.keys() - {"multiple"}):
        problems.add(
            "motion_not_built",
            f"{where}/rule_params/{key}",
            f"a scaled number reads only its multiple, never {key}",
        )
    multiple = _decimal(motion.rule_params.get("multiple", "1"))
    if motion.scaled_fact is None or multiple is None or spec.range is None:
        problems.add(
            "motion_not_built",
            where,
            f"{name} needs a scaled_fact, a numeric multiple and a range to hold it inside",
        )
        return None
    return ScaledNumber(name, motion.scaled_fact, multiple, spec.range.min, spec.range.max)


def _motion(
    unit: Unit,
    sides: Sequence[SidePlan],
    loaded: Loaded,
    faces: Mapping[str, EntryFace],
    problems: _Problems,
) -> tuple[tuple[DerivedPlan, ...], tuple[SlowPlan, ...], tuple[ScaledNumber, ...]]:
    derived: list[DerivedPlan] = []
    slow: list[SlowPlan] = []
    scaled: list[ScaledNumber] = []
    bound = _bound_numbers(unit)
    for name, spec in unit.numbers.items():
        where = f"/numbers/{name}/motion"
        motion = spec.motion
        if _only_on_a_dropped_side(unit, name):
            continue
        if spec.kind is NumberKind.FIXED and name not in bound:
            problems.add(
                "number_not_read",
                f"/numbers/{name}",
                f"no binding reads {name}, so writing it changes nothing",
            )
        if spec.kind is NumberKind.DERIVED and motion.mode is MotionMode.SCALED:
            row = _scaled(name, spec, where, problems)
            if row is not None:
                scaled.append(row)
        elif spec.kind is NumberKind.DERIVED:
            pin = DERIVED_BLOCKS.get(motion.mode)
            block = loaded.blocks.get(pin) if pin is not None else None
            if pin is None or block is None:
                problems.add("motion_not_built", where, f"no pinned block runs {motion.mode.value}")
                continue
            _unread_rule_params(motion.rule_params, faces.get(pin), {}, where, problems)
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
            stamp = _stamp_for(unit, name)
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
            set_here = {
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
            _unread_rule_params(motion.rule_params, faces.get(rule), set_here, where, problems)
            params |= set_here
            every = (
                motion.cadence.every_closed_trades if motion.cadence else None
            ) or SLOW_CADENCE_TRADES
            min_trades = (
                motion.min_count if motion.min_count is not None else MIN_TRADES
            )  # the same number the rule is told, now the engine's own floor as well
            slow.append(
                SlowPlan(
                    SlowNumber(name, rule, stamp, every, min_trades, motion.window),
                    block,
                    params,
                )
            )
    return tuple(derived), tuple(slow), tuple(scaled)


def _wrong_feed(b: BoundBlock, streams: AbstractSet[str]) -> str | None:
    """Why a port of ``b`` would never answer. ``resolve`` hands a whole bar for a stream's bare
    name and one value or nothing for any other ref, and each port reads only one of those."""
    for port in b.face.inputs:
        ref = b.inputs.get(port.port)
        if ref is None:
            continue
        stream, _, part = ref.partition(".")
        whole_bar = stream in streams and not part
        if whole_bar and port.stream_kind == "series":
            return (
                f"{b.pin}'s {port.port} port takes one value, and {ref} is a whole bar. "
                f"Feed it {stream}.close or a binding that gives a value"
            )
        if not whole_bar and port.stream_kind == "bars":
            return (
                f"{b.pin}'s {port.port} port takes a whole bar, and {ref} is not one. "
                f"Feed it {' or '.join(sorted(streams))}"
            )
    return None


def _not_read(b: BoundBlock, read: AbstractSet[str], streams: AbstractSet[str]) -> str | None:
    """Why ``b`` can neither hold nor feed, by the shape of its face and never by its name, so an
    agent's block of the same shape refuses too. A block not built yet answers only for that."""
    if b.pin in BLOCKS_NOT_BUILT:
        return None
    if b.face.output.type is OutputType.EXIT_ACTION:
        return f"{b.pin} is an exit, and a slot never acts on one. Put it in /exit_set"
    unfed = next((p for p in b.face.inputs if p.stream_kind not in _SLOT_PORT_KINDS), None)
    if unfed is not None:
        return (
            f"{b.pin} reads its {unfed.stream_kind} port {unfed.port}, which no slot is fed, so it "
            "can neither hold nor feed here"
        )
    wrong_feed = _wrong_feed(b, streams)
    if wrong_feed is not None:
        return wrong_feed
    if _holds_a_slot(b.face) or b.name in read:
        return None
    return (
        f"{b.pin} outputs a {b.face.output.type.value} that cannot hold a slot, and nothing reads "
        f"it. Bind value-above@1 with inputs.series {b.name} to compare it with a level"
    )


def _with_feeders(
    side: SidePlan,
    derived: Sequence[DerivedPlan],
    streams: AbstractSet[str],
    problems: _Problems,
) -> SidePlan:
    """``side`` with its feeders marked. A binding that can neither hold nor feed refuses."""
    read = {d.source for d in derived if d.side is side.side}
    feeders: set[str] = set()
    for b in reversed([b for slot in side.slots for b in slot.bindings]):
        why = _not_read(b, read, streams)
        if why is not None:
            problems.add("binding_not_read", b.where, why)
        elif not _holds_a_slot(b.face):
            feeders.add(b.name)
        read.update(b.inputs.values())
    marked: list[SlotPlan] = []
    for slot in side.slots:
        mine = frozenset(b.name for b in slot.bindings if b.name in feeders)
        conditions = len(slot.bindings) - len(mine)
        if (
            conditions
            and mine
            and slot.combiner is CombinerKind.K_OF_N
            and (slot.k or 0) > conditions
        ):
            problems.add(
                "combiner_not_built",
                f"{slot.where}/combiner/k",
                f"k_of_n needs a k of at most {conditions}, the conditions this slot holds, "
                "because a binding that only feeds is no condition",
            )
        marked.append(replace(slot, feeders=mine))
    return replace(side, slots=tuple(marked))


def _values(bound: BoundBlock, defaults: Mapping[str, Decimal]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for name, param in bound.params.items():
        if isinstance(param, ValueParam):
            out[name] = param.value
        elif param.number in defaults:
            out[name] = defaults[param.number]
    return out


def _built(
    block: Block,
    params: Mapping[str, Decimal],
    inputs: Mapping[str, str],
    side: Side,
    label: str,
    where: str,
    problems: _Problems,
) -> Instance | None:
    """The one guard over a block's constructor: a value it cannot run is a problem at ``where``,
    never a raise out of ``check`` or ``construct_unit``."""
    try:
        return block.make(params, inputs, side)
    except (ValueError, KeyError, OverflowError) as bad:
        problems.add("bad_params", where, f"{label} cannot run these values: {bad}")
        return None


def _warm_up(plan: Plan, problems: _Problems) -> tuple[int, int]:
    """The bars a market needs before entries, and the unit's summed state bound. It builds every
    instance once, so a value no block can run is named at compile.

    A binding is warm at the later of its recorded settle length, at this binding's parameters, and
    the bars its upstream needs plus its own warm-up; a derived number at its source's plus its
    block's.
    """
    warm: dict[str, int] = {}
    bound_total = 0

    def make(b: BoundBlock, side: Side) -> Instance | None:
        return _built(b.block, _values(b, plan.defaults), b.inputs, side, b.pin, b.where, problems)

    for side in plan.sides:
        for slot in side.slots:
            for b in slot.bindings:
                instance = make(b, side.side)
                if instance is None:
                    continue
                upstream = max(
                    (warm.get(f"{side.side.value}.{ref}", 0) for ref in b.inputs.values()),
                    default=0,
                )
                recorded = b.face.settle
                settle = recorded.bars_at(_values(b, plan.defaults)) if recorded is not None else 0
                warm[b.key] = max(settle, upstream + instance.warm_up_bars)
                bound_total += instance.state_bound
    for d in plan.derived:
        instance = _built(
            d.block, d.params, {}, d.side, d.pin, f"/numbers/{d.number}/motion", problems
        )
        if instance is None:
            continue
        warm[f"derived.{d.side.value}.{d.number}"] = (
            warm.get(f"{d.side.value}.{d.source}", 0) + instance.warm_up_bars
        )
        bound_total += instance.state_bound
    for e in plan.exits:
        instance = make(e.binding, Side.LONG)
        if instance is None:
            continue
        warm[e.binding.key] = instance.warm_up_bars
        bound_total += instance.state_bound
    for h in plan.halts:
        # A brake's own warm-up never gates the unit's entries: the row goes cold and says so.
        instance = make(h.binding, Side.LONG)
        if instance is not None:
            bound_total += instance.state_bound
    make(plan.sizer, Side.LONG)
    for s in plan.slow:
        _built(
            s.block,
            s.params,
            {},
            Side.LONG,
            s.number.rule_pin,
            f"/numbers/{s.number.name}/motion",
            problems,
        )
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


_NAMED_STREAM: Final = re.compile(r"([mhd])(\d{1,9})")
_SECONDS_PER: Final[Mapping[str, int]] = {"m": 60, "h": 3600, "d": 86_400}


def _named_seconds(stream: str) -> int | None:
    """The bar length QMB replays for this stream name, by the rule of its ``_bar_seconds``, which
    QML may not import. A name is free text, so the digits are capped here: ``check`` must not
    raise on one. QMB refuses a name this cannot read."""
    named = _NAMED_STREAM.fullmatch(stream)
    return (_SECONDS_PER[named[1]] * int(named[2]) or None) if named else None


_MOTION_READ: Final[Mapping[NumberKind, frozenset[str]]] = {
    NumberKind.FIXED: frozenset(),
    NumberKind.DERIVED: frozenset({"source", "rule_params"}),
    NumberKind.CALIBRATED: frozenset(
        {"cadence", "min_count", "shrink_k", "step_limit", "window", "rule", "rule_params"}
    ),
}
"""The motion fields the compiled unit runs for each kind of number, beside ``mode``."""
_OWN_RECORD: Final[str] = "own_record"
"""The one ``source`` true of a calibrated number, which moves from the unit's own closed trades."""


def _motion_read(spec: NumberSpec) -> frozenset[str]:
    """The motion fields this format runs for one number, by its kind and its mode."""
    if spec.kind is NumberKind.DERIVED and spec.motion.mode is MotionMode.SCALED:
        return frozenset({"scaled_fact", "rule_params"})
    return _MOTION_READ[spec.kind]


def _motion_unread(spec: NumberSpec) -> tuple[str, ...]:
    motion = spec.motion
    read = _motion_read(spec)
    unread = [
        item.name
        for item in fields(Motion)
        if item.name != "mode"
        and item.name not in read
        and getattr(motion, item.name) not in (None, {})
    ]
    if spec.kind is NumberKind.CALIBRATED and motion.source == _OWN_RECORD:
        unread.remove("source")
    return tuple(unread)


def _shape_problems(unit: Unit, problems: _Problems) -> None:
    """The fields of the document this format runs nothing behind."""
    if len(unit.streams) != 1:
        problems.add("streams_not_built", "/streams", f"{_FORMAT} runs one stream")
    if unit.reads:
        problems.add("reads_not_built", "/reads", f"{_FORMAT} reads no readings")
    if unit.sessions:
        problems.add(
            "sessions_not_built",
            "/sessions",
            f"{_FORMAT} runs no session window, so this unit would trade outside it",
        )
    needs = unit.context_needs
    if needs is not None and (needs.require or needs.warn or needs.block):
        problems.add(
            "context_not_built",
            "/context_needs",
            f"{_FORMAT} reads no context, so this unit would trade whatever the context is",
        )
    routes = unit.routes
    if routes is not None and (routes.data or routes.execution is not None):
        problems.add(
            "routes_not_built",
            "/routes",
            f"{_FORMAT} takes no route from a unit, so this one would run on the host's own",
        )
    if unit.plain_python is not None:
        problems.add(
            "plain_python_not_built",
            "/plain_python",
            f"{_FORMAT} runs the unit's slots, so {unit.plain_python.block} would never run",
        )
    if unit.modifiers:
        problems.add(
            "modifiers_not_built",
            "/modifiers",
            f"{_FORMAT} runs one unmodified size, so these would never apply",
        )
    if unit.gates:
        problems.add(
            "gates_not_built",
            "/gates",
            f"{_FORMAT} runs no gate slot, so this unit would enter whatever the gate says",
        )
    if unit.tolerations:
        problems.add(
            "tolerations_not_built",
            "/tolerations",
            f"{_FORMAT} reads no sticker, so nothing would ever need tolerating",
        )
    if unit.stages is not None:
        problems.add(
            "stages_not_built",
            "/stages",
            f"{_FORMAT} runs one set of rows, not stages",
        )
    if unit.risk_locks:
        problems.add(
            "risk_locks_not_built",
            "/risk_locks",
            f"{_FORMAT} runs no pod, so a lock would hold nothing",
        )
    if unit.recipe is not None:
        problems.add(
            "recipe_not_built",
            "/recipe",
            f"{_FORMAT} runs no pod, so this recipe would never be stamped in",
        )
    if unit.home_markets:
        problems.add(
            "home_markets_not_built",
            "/home_markets",
            f"{_FORMAT} runs every market in /markets, not only these",
        )
    if unit.tags:
        problems.add(
            "tags_not_built",
            "/tags",
            f"{_FORMAT} groups nothing, so a tag would select nothing",
        )
    if unit.sizer is not None:
        for port, ref in unit.sizer.inputs.items():
            problems.add(
                "inputs_not_built",
                f"/sizer/inputs/{port}",
                f"{_FORMAT} hands a sizer its equity, prices and record, so it never reads {ref}",
            )
    for index, market in enumerate(unit.markets):
        if market.roll is not None:
            problems.add(
                "roll_not_built",
                f"/markets/{index}/roll",
                f"{_FORMAT} reads no roll rule, so {market.market_id} would not roll by it",
            )
        if market.settings:
            problems.add(
                "settings_not_built",
                f"/markets/{index}/settings",
                f"{_FORMAT} runs no setting for one market, so {market.market_id} would read the "
                "unit's own numbers",
            )
        if market.settings_record is not None:
            problems.add(
                "settings_not_built",
                f"/markets/{index}/settings_record",
                f"{_FORMAT} reads no settings record, so {market.market_id} would read the unit's "
                "own numbers",
            )
    if unit.position_limit is not None and unit.position_limit.per_instrument != 1:
        problems.add(
            "limit_not_built", "/position_limit", f"{_FORMAT} holds one position per market"
        )
    for index, stream in enumerate(unit.streams):
        if stream.market != "*" and {stream.market} != {m.market_id for m in unit.markets}:
            problems.add(
                "market_not_built",
                f"/streams/{index}/market",
                f"{_FORMAT} runs the one stream on every market in /markets, not on "
                f"{stream.market} alone",
            )
        if stream.price is not Price.BID_ASK:
            problems.add(
                "price_not_built",
                f"/streams/{index}/price",
                f"{_FORMAT} runs bid and ask bars, not {stream.price.value}",
            )
        if stream.input is not StreamInput.CLOSED_BARS:
            problems.add(
                "input_not_built",
                f"/streams/{index}/input",
                f"{_FORMAT} runs closed bars, not {stream.input.value}",
            )
        if stream.bar.kind is not BarKind.TIME:
            problems.add(
                "bar_not_built",
                f"/streams/{index}/bar",
                f"{_FORMAT} runs time bars, not {stream.bar.kind.value}",
            )
        elif (seconds := _named_seconds(stream.name)) is not None and stream.bar.size != seconds:
            problems.add(
                "bar_not_built",
                f"/streams/{index}/bar",
                f"{stream.name} replays as {seconds} second bars, and this stream says "
                f"{stream.bar.size}",
            )
    for name, spec in unit.numbers.items():
        if spec.applies_to_open_positions:
            problems.add(
                "open_positions_not_built",
                f"/numbers/{name}/applies_to_open_positions",
                f"{_FORMAT} moves no open position by a number, so {name} would not reach one",
            )
        for field in _motion_unread(spec):
            problems.add(
                "motion_not_built",
                f"/numbers/{name}/motion/{field}",
                f"{_FORMAT} reads no {field} on a {spec.kind.value} number",
            )
        cadence = spec.motion.cadence
        if cadence is not None and cadence.at is not None and cadence.every_closed_trades is None:
            problems.add(
                "cadence_not_built",
                f"/numbers/{name}/motion/cadence",
                f"{_FORMAT} moves a number every so many closed trades, not at {cadence.at.value}",
            )
        _number_fields(name, spec, problems)


def _number_fields(name: str, spec: NumberSpec, problems: _Problems) -> None:
    """The number's own declarations this format runs nothing behind.

    Each names a mechanism the compiled unit does not have, so accepting it in silence would
    promise a behaviour nobody runs. ``owner``, ``reason`` and ``origin`` stay out: they label the
    value and decide nothing.
    """
    where = f"/numbers/{name}"
    if spec.derivation is not None:
        problems.add(
            "derivation_not_built",
            f"{where}/derivation",
            f"{_FORMAT} runs no derivation, so {name}'s value would come from no rule it reads",
        )
    if spec.guard is not None:
        problems.add(
            "guard_not_built",
            f"{where}/guard",
            f"{_FORMAT} reverts and freezes no number, so {name} would keep moving after a trip",
        )
    if spec.cautious is not Cautious.HOLD:
        problems.add(
            "cautious_not_built",
            f"{where}/cautious",
            f"{_FORMAT} moves a number by its rule and never asks which way is cautious, so "
            f"{name}'s {spec.cautious.value} would decide nothing",
        )
    if spec.never_self_tune:
        problems.add(
            "never_self_tune_not_built",
            f"{where}/never_self_tune",
            f"{_FORMAT} tunes a number by its own motion rule and reads no never_self_tune",
        )
    if spec.stage_values:
        problems.add(
            "stage_values_not_built",
            f"{where}/stage_values",
            f"{_FORMAT} runs one set of number values, not a value per stage",
        )
    if spec.authority is Authority.AT_ANCHOR:
        problems.add(
            "authority_not_built",
            f"{where}/authority",
            f"{_FORMAT} moves no number at an anchor, so {name} would move on its count alone",
        )
    elif spec.authority is Authority.OFF and spec.motion.mode is not MotionMode.FIXED:
        problems.add(
            "authority_not_built",
            f"{where}/authority",
            f"{_FORMAT} moves {name} by its {spec.motion.mode.value} rule, and no authority "
            "holds a value its own rule moves",
        )


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
    sides = tuple(
        s for side in TRADED_SIDES[unit.direction] if (s := wiring.side(side)) is not None
    )
    exits = wiring.exits()
    halts = wiring.halts()
    sizer = wiring.bind(unit.sizer, "sizer", "/sizer") if unit.sizer is not None else None
    if sizer is not None and sizer.face.output.type not in _SIZER_ANSWERS:
        problems.add(
            "sizer_not_built",
            "/sizer/block",
            f"{sizer.face.pin} answers {sizer.face.output.type.value}, and a sizer answers an "
            "amount or a quantity, which one converter spells as the venue's lots",
        )
    derived, slow, scaled = _motion(unit, sides, loaded, faces, problems)
    streams = frozenset(s.name for s in unit.streams)
    sides = tuple(_with_feeders(s, derived, streams, problems) for s in sides)
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
        halts=halts,
        sizer=sizer,
        derived=derived,
        slow=slow,
        scaled=scaled,
        defaults=_defaults(unit),
    )
    warm_up, state_bound = _warm_up(plan, problems)
    if problems.found:
        return tuple(problems.found)
    options = {"port_quantum_significant_digits": PORT_QUANTUM_SIGNIFICANT_DIGITS}
    logic, risk = sections(cast("Mapping[str, object]", document), COMPILER_FORMAT_VERSION)
    compiled_fp = fingerprint(
        {
            "logic": logic.fingerprint.value,
            "risk": risk.fingerprint.value,
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
        logic_fingerprint=logic.fingerprint,
        risk_fingerprint=risk.fingerprint,
        compiler_format_version=COMPILER_FORMAT_VERSION,
        options=options,
        warm_up={plan.stream: warm_up},
        state_bound=state_bound,
        placeholders=placeholders,
        trace_schema=TRACE_SCHEMA,
    )
