"""The unit door: hosting a compiled unit (AD-107, L0 AD-16).

``construct_unit`` and ``restore_unit`` return a ``HostedUnit``. Its ``on_instant(instant)``
reads the host's surfaces and returns a ``UnitStep``: CT-23 format 3 intents (admitted by
``accept_unit_intents``), decision rows, calibration rows and state events. ``construct_bot``,
``HostedBot`` and ``accept_intents`` are untouched and refuse a unit's sized intent (BR-A4).

The host injects these read surfaces, each an object with ``at(instant)``:

- ``bars:<stream>:<market_id>``: the latest closed ``QuoteBar`` knowable at the instant.
- ``own_position:<market_id>``: the ``OwnPosition`` open on that market, or ``None`` when flat.
- ``own_journal``: the ``ClosedTrade`` rows this run or deployment closed.
- ``account``: the ``Account`` facts the sizer reads.

On each instant, for each market whose bar is new: every block updates, exits run for the
positions this compiled fingerprint opened, then entries. A market's entries wait for its
derived warm-up (``warming``, then ``ready``). Calibrated numbers move last, from
``own_journal``, only when the unit is flat. The stream's ``close`` and its bars are the bid
side; an entry's reference price is the ask close for a long and the bid close for a short.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Final, Protocol, cast

from qmf.core.chrono import Instant
from qmf.core.fingerprint import Fingerprint, fingerprint
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qmf.risk.paper import ExecutionTarget
from qmf.risk.unit_intent import (
    UNIT_INTENT_FORMAT_VERSION,
    UnitEntryIntent,
    UnitExitIntent,
    parse_unit_intent,
)

from qml._refuse import invalid, unsupported
from qml.blocks.api import EntryOrder, Instance, OutputType, Signal, Size
from qml.compile.compiler import (
    BoundBlock,
    CompiledUnit,
    ExitUse,
    SidePlan,
    SlotPlan,
)
from qml.motion.engine import ClosedTrade, SlowState, calibrate
from qml.numbers.records import InstrumentRecord
from qml.unit.model import CombinerKind, Role, Side, ValueParam

__all__ = [
    "OHLC",
    "STATE_SCHEMA_VERSION",
    "Account",
    "CalibrationRow",
    "DecisionRow",
    "HostedUnit",
    "MotionSwitch",
    "OwnPosition",
    "QuoteBar",
    "SlotOutput",
    "StateEvent",
    "TraceLevel",
    "UnitFactory",
    "UnitIntent",
    "UnitStep",
    "accept_unit_intents",
    "construct_unit",
    "restore_unit",
]

STATE_SCHEMA_VERSION: Final[int] = 1

UnitIntent = UnitEntryIntent | UnitExitIntent


class TraceLevel(StrEnum):
    """``events``: taken, skipped and suppressed signals and near misses. ``every_bar``: also a
    ``no_signal`` row for every side on every bar."""

    EVENTS = "events"
    EVERY_BAR = "every_bar"


class MotionSwitch(StrEnum):
    """``off`` keeps every calibrated number at its starting value, so QMB can report both."""

    ON = "on"
    OFF = "off"


class Surface(Protocol):
    def at(self, instant: Instant, /) -> object: ...


@dataclass(frozen=True, slots=True)
class OHLC:
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal

    def fields(self) -> Mapping[str, Decimal]:
        return {"open": self.open, "high": self.high, "low": self.low, "close": self.close}


@dataclass(frozen=True, slots=True)
class QuoteBar:
    """One closed bar of both price sides, knowable at its close."""

    knowable_at: Instant
    bid: OHLC
    ask: OHLC


@dataclass(frozen=True, slots=True)
class OwnPosition:
    """An open position (CONTRACTS.md section 4.3), knowable at its fill."""

    position_id: str
    side: Side
    quantity: Decimal
    entry_price: Decimal
    opened_by: Fingerprint
    opened_at: Instant


@dataclass(frozen=True, slots=True)
class Account:
    equity: Decimal


@dataclass(frozen=True, slots=True)
class SlotOutput:
    slot: str
    binding: str
    output: str | None


@dataclass(frozen=True, slots=True)
class DecisionRow:
    row_id: str
    instant: Instant
    market_id: str
    side: Side
    outcome: str
    slot_trail: tuple[SlotOutput, ...]
    numbers_in_force: Mapping[str, Decimal]
    reason: str
    readings_used: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class CalibrationRow:
    row_id: str
    number: str
    old: Decimal
    new: Decimal
    rule: str
    from_trade_id: str
    to_trade_id: str
    count: int
    statistic: Mapping[str, str]
    watermark: Instant


@dataclass(frozen=True, slots=True)
class StateEvent:
    kind: str
    market_id: str
    reason: str = ""


@dataclass(frozen=True, slots=True)
class UnitStep:
    instant: Instant
    intents: tuple[UnitIntent, ...]
    decisions: tuple[DecisionRow, ...]
    calibrations: tuple[CalibrationRow, ...]
    state_events: tuple[StateEvent, ...]


def accept_unit_intents(raw: Sequence[Mapping[str, object]]) -> Result[tuple[UnitIntent, ...]]:
    """Admit format-3 wire intents only; the first refused one refuses the step."""
    accepted: list[UnitIntent] = []
    for item in raw:
        parsed = parse_unit_intent(item)
        if is_refusal(parsed):
            return parsed
        accepted.append(parsed.value)
    return Ok(tuple(accepted))


def _price(value: Decimal, record: InstrumentRecord, rounding: str = ROUND_HALF_EVEN) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-record.digits), rounding=rounding)


def _text(value: object) -> str | None:
    match value:
        case Signal(value=inner):
            return None if inner is None else str(inner)
        case Decimal():
            return str(value)
        case EntryOrder(kind=kind, at=at):
            return f"{kind} {at}"
        case Size(lots=lots, skip_reason=reason):
            return str(lots) if lots is not None else reason
        case _:
            return None


def _value(output: object) -> Decimal | None:
    if isinstance(output, Signal):
        return output.value
    return output if isinstance(output, Decimal) else None


@dataclass(slots=True)
class _Side:
    holds: bool
    trigger_held: bool
    reason: str
    trail: tuple[SlotOutput, ...]
    order: EntryOrder | None


@dataclass(slots=True)
class _Market:
    market_id: str
    record: InstrumentRecord
    instances: dict[str, Instance]
    derived: dict[Side, dict[str, Decimal]]
    """Each side's derived numbers: a number both sides bind moves once per bar per side."""
    last_bar_ns: int | None = None
    bars: int = 0
    timers: dict[str, Instance] = field(default_factory=dict[str, Instance])
    exited: set[str] = field(default_factory=set[str])
    in_force: dict[Side, dict[str, Decimal]] = field(default_factory=dict[Side, dict[str, Decimal]])
    """Each side's numbers this bar's decisions read, taken before the derived numbers update."""


class _Core:
    """A hosted unit's state and the parts of its step that read it."""

    def __init__(
        self,
        compiled: CompiledUnit,
        *,
        calibrated: Mapping[str, Decimal],
        surfaces: Mapping[str, Surface],
        scope_id: str,
        execution_target: ExecutionTarget,
        trace_level: TraceLevel,
        motion: MotionSwitch,
    ) -> None:
        self.compiled = compiled
        self.plan = compiled.plan
        self.surfaces = surfaces
        self.scope_id = scope_id
        self.target = execution_target
        self.trace = trace_level
        self.motion = motion
        self.warm_up = max(compiled.warm_up.values(), default=0)
        self.slow = {
            s.number.name: SlowState(value=calibrated[s.number.name]) for s in self.plan.slow
        }
        self.slow_rules = {s.number.name: s.block.make(s.params, {}) for s in self.plan.slow}
        self.pending: list[StateEvent] = []
        self.markets = [
            self.market(market.market_id, record) for market, record in self.plan.markets
        ]

    # --- building --------------------------------------------------------------

    def settled(self) -> dict[str, Decimal]:
        return dict(self.plan.defaults) | {name: state.value for name, state in self.slow.items()}

    def numbers(self, market: _Market, side: Side) -> dict[str, Decimal]:
        return self.settled() | market.derived.get(side, {})

    def params(self, bound: BoundBlock, numbers: Mapping[str, Decimal]) -> dict[str, Decimal]:
        out: dict[str, Decimal] = {}
        for name, param in bound.params.items():
            if isinstance(param, ValueParam):
                out[name] = param.value
            elif param.number in numbers:
                out[name] = numbers[param.number]
        return out

    def market(self, market_id: str, record: InstrumentRecord) -> _Market:
        state = _Market(market_id, record, {}, {})
        numbers = self.settled()
        for side in self.plan.sides:
            for slot in side.slots:
                for b in slot.bindings:
                    state.instances[b.key] = b.block.make(
                        self.params(b, numbers), b.inputs, side.side
                    )
            for e in self.plan.exits:
                if e.use is not ExitUse.PER_BAR:
                    key = f"{side.side.value}.{e.binding.key}"
                    state.instances[key] = e.binding.block.make(
                        self.params(e.binding, numbers), e.binding.inputs, side.side
                    )
        for d in self.plan.derived:
            state.instances[f"derived.{d.side.value}.{d.number}"] = d.block.make(
                d.params, {}, d.side
            )
        state.instances["sizer"] = self.plan.sizer.block.make(
            self.params(self.plan.sizer, numbers), self.plan.sizer.inputs
        )
        return state

    # --- state -------------------------------------------------------------------

    def snapshot_state(self) -> Mapping[str, object]:
        """Every instance's state, the motion state and the fingerprint it belongs to (UT-09)."""
        markets: dict[str, object] = {}
        for m in self.markets:
            markets[m.market_id] = {
                "last_bar_ns": m.last_bar_ns,
                "bars": m.bars,
                "derived": {
                    side.value: {k: str(v) for k, v in values.items()}
                    for side, values in m.derived.items()
                },
                "blocks": {k: dict(i.export_state()) for k, i in m.instances.items()},
                "timers": {k: dict(i.export_state()) for k, i in m.timers.items()},
                "exited": sorted(m.exited),
            }
        slow = {
            name: {
                "value": str(s.value),
                "read": [[t, str(stamp), str(r)] for t, stamp, r in s.read],
                "watermark": None if s.watermark is None else list(s.watermark),
                "read_at_last_run": s.read_at_last_run,
            }
            for name, s in self.slow.items()
        }
        return {
            "state_schema_version": STATE_SCHEMA_VERSION,
            "compiled_fingerprint": self.compiled.compiled_fingerprint.value,
            "markets": markets,
            "slow": slow,
        }

    def load(self, snapshot: Mapping[str, object]) -> None:
        markets = cast("Mapping[str, Mapping[str, object]]", snapshot["markets"])
        for m in self.markets:
            saved = markets[m.market_id]
            last = saved["last_bar_ns"]
            m.last_bar_ns = last if isinstance(last, int) else None
            m.bars = cast("int", saved["bars"])
            m.derived = {
                Side(side): {k: Decimal(v) for k, v in values.items()}
                for side, values in cast(
                    "Mapping[str, Mapping[str, str]]", saved["derived"]
                ).items()
            }
            for key, state in cast("Mapping[str, Mapping[str, object]]", saved["blocks"]).items():
                m.instances[key].import_state(state)
            for pid, state in cast("Mapping[str, Mapping[str, object]]", saved["timers"]).items():
                m.timers[pid] = self.timer()
                m.timers[pid].import_state(state)
            m.exited = set(cast("list[str]", saved["exited"]))
        for name, raw in cast("Mapping[str, Mapping[str, object]]", snapshot["slow"]).items():
            mark = raw["watermark"]
            self.slow[name] = SlowState(
                value=Decimal(cast("str", raw["value"])),
                read=tuple(
                    (t, Decimal(s), Decimal(r)) for t, s, r in cast("list[list[str]]", raw["read"])
                ),
                watermark=None
                if mark is None
                else (
                    cast("int", cast("list[object]", mark)[0]),
                    cast("str", cast("list[object]", mark)[1]),
                ),
                read_at_last_run=cast("int", raw["read_at_last_run"]),
            )

    def timer(self) -> Instance:
        per_bar = next(e for e in self.plan.exits if e.use is ExitUse.PER_BAR)
        return per_bar.binding.block.make(
            self.params(per_bar.binding, self.plan.defaults), per_bar.binding.inputs
        )


class HostedUnit:
    """One compiled unit hosted for one run or deployment, driven one instant at a time."""

    def __init__(self, core: _Core) -> None:
        self._core = core

    @property
    def compiled(self) -> CompiledUnit:
        return self._core.compiled

    def on_instant(self, instant: object, /) -> Result[UnitStep]:
        if not isinstance(instant, Instant):
            return invalid("instant", "the evaluation instant rides the call", given=repr(instant))
        return _Run(self._core, instant).step()

    @property
    def calibrated_values(self) -> Mapping[str, Decimal]:
        return MappingProxyType({name: s.value for name, s in self._core.slow.items()})

    def snapshot(self) -> Mapping[str, object]:
        """Every instance's state, the motion state and the fingerprint it belongs to (UT-09)."""
        return self._core.snapshot_state()


class _Run:
    """One ``on_instant`` call: reads the surfaces once, then exits, entries and motion."""

    def __init__(self, unit: _Core, instant: Instant) -> None:
        self.unit = unit
        self.plan = unit.plan
        self.instant = instant
        self.intents: list[Mapping[str, object]] = []
        self.decisions: list[DecisionRow] = []
        self.calibrations: list[CalibrationRow] = []
        self.events: list[StateEvent] = list(unit.pending)
        unit.pending.clear()
        self.ordinal = 0

    def row_id(self) -> str:
        made = fingerprint(
            {
                "scope_id": self.unit.scope_id,
                "instant": self.instant.value_ns,
                "ordinal": self.ordinal,
            }
        )
        self.ordinal += 1
        if is_refusal(made):  # pragma: no cover - text and integers always serialise
            raise ValueError(str(made.context))
        return made.value.value

    def surface(self, key: str) -> object:
        return self.unit.surfaces[key].at(self.instant)

    def step(self) -> Result[UnitStep]:
        account = self.surface("account")
        journal = self.surface("own_journal")
        positions: dict[str, OwnPosition | None] = {}
        fresh: dict[str, QuoteBar] = {}
        for m in self.unit.markets:
            position = self.surface(f"own_position:{m.market_id}")
            positions[m.market_id] = position if isinstance(position, OwnPosition) else None
            bar = self.surface(f"bars:{self.plan.stream}:{m.market_id}")
            if bar is None:
                continue
            if not isinstance(bar, QuoteBar):
                return invalid(
                    "bars", "a bar surface answers a QuoteBar or None", market=m.market_id
                )
            if bar.knowable_at.value_ns > self.instant.value_ns:
                return invalid(
                    "bars", "a bar knowable after the instant is a look-ahead", market=m.market_id
                )
            if m.last_bar_ns is None or bar.knowable_at.value_ns > m.last_bar_ns:
                fresh[m.market_id] = bar
        results: dict[str, dict[Side, _Side]] = {}
        for m in self.unit.markets:
            bar = fresh.get(m.market_id)
            if bar is not None:
                results[m.market_id] = self.update(m, bar)
        for m in self.unit.markets:
            self.exits(m, positions[m.market_id], m.market_id in fresh)
        for m in self.unit.markets:
            bar = fresh.get(m.market_id)
            if bar is not None:
                self.entries(m, bar, results[m.market_id], positions[m.market_id], account)
        if self.unit.motion is MotionSwitch.ON:
            trades = cast("Sequence[ClosedTrade]", journal if isinstance(journal, Sequence) else ())
            self.motion(trades, all(p is None for p in positions.values()))
        admitted = accept_unit_intents(self.intents)
        if is_refusal(admitted):
            return admitted
        return Ok(
            UnitStep(
                instant=self.instant,
                intents=admitted.value,
                decisions=tuple(self.decisions),
                calibrations=tuple(self.calibrations),
                state_events=tuple(self.events),
            )
        )

    # --- blocks ------------------------------------------------------------------

    def update(self, m: _Market, bar: QuoteBar) -> dict[Side, _Side]:
        m.last_bar_ns = bar.knowable_at.value_ns
        m.bars += 1
        if m.bars == 1:
            self.events.append(StateEvent("warming", m.market_id, f"{self.unit.warm_up} bars"))
        if m.bars == self.unit.warm_up:
            self.events.append(StateEvent("ready", m.market_id))
        m.in_force = {plan.side: self.unit.numbers(m, plan.side) for plan in self.plan.sides}
        sides = {
            plan.side: self.side(m, plan, bar, m.in_force[plan.side]) for plan in self.plan.sides
        }
        for side in (Side.LONG, Side.SHORT):
            for e in self.plan.exits:
                if e.use is ExitUse.STOP and f"{side.value}.{e.binding.key}" in m.instances:
                    instance = m.instances[f"{side.value}.{e.binding.key}"]
                    instance.update(
                        {"series": bar.bid.fields()} | self.unit.params(e.binding, m.in_force[side])
                    )
        return sides

    def side(
        self, m: _Market, plan: SidePlan, bar: QuoteBar, numbers: Mapping[str, Decimal]
    ) -> _Side:
        outputs: dict[str, object] = {}
        trail: list[SlotOutput] = []
        held: dict[str, tuple[bool, str]] = {}
        order: EntryOrder | None = None

        def resolve(ref: str) -> object:
            stream, _, part = ref.partition(".")
            if stream == self.plan.stream:
                return bar.bid.fields() if part == "" else bar.bid.fields()[part]
            return _value(outputs.get(ref))

        for slot in plan.slots:
            conditions: list[bool | None] = []
            for b in slot.bindings:
                evidence = {port: resolve(ref) for port, ref in b.inputs.items()}
                evidence |= self.unit.params(b, numbers)
                out = m.instances[b.key].update(evidence)
                outputs[b.name] = out
                trail.append(SlotOutput(slot.name, b.name, _text(out)))
                if isinstance(out, EntryOrder):
                    order = out
                conditions.append(self.condition(b, out, evidence, plan.side))
            held[slot.name] = self.combine(slot, conditions)
        for d in self.plan.derived:
            if d.side is plan.side:
                fed = m.instances[f"derived.{d.side.value}.{d.number}"].update(
                    {"series": _value(outputs.get(d.source))}
                )
                spec = self.unit.compiled.unit.numbers[d.number]
                if isinstance(fed, Decimal) and spec.range is not None:
                    m.derived.setdefault(d.side, {})[d.number] = min(
                        spec.range.max, max(spec.range.min, fed)
                    )
        failing = [f"{name}: {why}" for name, (ok, why) in held.items() if not ok]
        trigger = any(held[s.name][0] for s in plan.slots if s.role is Role.TRIGGER)
        return _Side(not failing, trigger, "; ".join(failing), tuple(trail), order)

    @staticmethod
    def condition(
        b: BoundBlock, out: object, evidence: Mapping[str, object], side: Side
    ) -> bool | None:
        match out:
            case Signal(state=state):
                return state
            case EntryOrder():
                return True
            case Decimal() if (
                b.face.output.type is OutputType.SERIES and b.face.output.measure == "price"
            ):
                price = next(
                    (evidence[p] for p in b.inputs if isinstance(evidence.get(p), Decimal)), None
                )
                if not isinstance(price, Decimal):
                    return None
                return price > out if side is Side.LONG else price < out
            case _:
                return None

    @staticmethod
    def combine(slot: SlotPlan, conditions: Sequence[bool | None]) -> tuple[bool, str]:
        absent = [b.name for b, c in zip(slot.bindings, conditions, strict=True) if c is None]
        if absent and not slot.absent_is_false and slot.combiner is CombinerKind.ALL:
            return False, f"absent input {', '.join(absent)}"
        true = sum(1 for c in conditions if c is True)
        match slot.combiner:
            case CombinerKind.ALL:
                ok = true == len(conditions)
            case CombinerKind.ANY:
                ok = true >= 1
            case _:
                ok = true >= (slot.k or len(conditions))
        if ok:
            return True, ""
        if absent and not slot.absent_is_false:
            return False, f"absent input {', '.join(absent)}"
        return False, "does not hold"

    # --- exits ---------------------------------------------------------------------

    def exits(self, m: _Market, position: OwnPosition | None, new_bar: bool) -> None:
        mine = (
            position is not None and position.opened_by == self.unit.compiled.compiled_fingerprint
        )
        for gone in [pid for pid in m.timers if position is None or pid != position.position_id]:
            del m.timers[gone]
            m.exited.discard(gone)
        if position is None or not mine or not new_bar or position.position_id in m.exited:
            return
        timer = m.timers.get(position.position_id)
        if timer is None:
            timer = self.unit.timer()
            m.timers[position.position_id] = timer
        out = timer.update({})
        if not (isinstance(out, Signal) and out.state):
            return
        m.exited.add(position.position_id)
        row = self.decision(m, position.side, "taken", (), f"time exit after {_text(out)} bars")
        self.intents.append(
            {
                "contract_format_version": UNIT_INTENT_FORMAT_VERSION,
                "intent_family": "exit",
                "kind": "close_full",
                "position_ref": {
                    "position_id": position.position_id,
                    "instrument": {"venue": m.record.venue, "symbol": m.record.symbol},
                    "opened_by": position.opened_by.value,
                },
                "reason_code": {"code": "time-exit", "book_family": "unit"},
                "decision_row_id": row,
            }
        )

    # --- entries ---------------------------------------------------------------------

    def decision(
        self, m: _Market, side: Side, outcome: str, trail: tuple[SlotOutput, ...], reason: str
    ) -> str:
        row_id = self.row_id()
        self.decisions.append(
            DecisionRow(
                row_id=row_id,
                instant=self.instant,
                market_id=m.market_id,
                side=side,
                outcome=outcome,
                slot_trail=trail,
                numbers_in_force=MappingProxyType(dict(m.in_force.get(side, {}))),
                reason=reason,
            )
        )
        return row_id

    def entries(
        self,
        m: _Market,
        bar: QuoteBar,
        sides: Mapping[Side, _Side],
        position: OwnPosition | None,
        account: object,
    ) -> None:
        signalled = [s for s, r in sides.items() if r.holds]
        for side, result in sides.items():
            if not result.holds:
                if result.trigger_held:
                    self.decision(m, side, "no_signal", result.trail, f"near miss, {result.reason}")
                elif self.unit.trace is TraceLevel.EVERY_BAR:
                    self.decision(m, side, "no_signal", result.trail, result.reason)
                continue
            if m.bars < self.unit.warm_up:
                self.decision(m, side, "suppressed_warming", result.trail, "warming up")
            elif len(signalled) > 1:
                self.decision(m, side, "dropped_opposite", result.trail, "both sides signalled")
            elif position is not None:
                self.decision(m, side, "suppressed_limit", result.trail, "a position is open")
            else:
                self.enter(m, bar, side, result, account)

    def enter(self, m: _Market, bar: QuoteBar, side: Side, result: _Side, account: object) -> None:
        record = m.record
        numbers = m.in_force[side]
        reference = bar.ask.close if side is Side.LONG else bar.bid.close
        stop_plan = next((e for e in self.plan.exits if e.use is ExitUse.STOP), None)
        raw_stop = (
            _value(m.instances[f"{side.value}.{stop_plan.binding.key}"].update({}))
            if stop_plan is not None
            else None
        )
        if result.order is None or result.order.kind != "market":
            self.decision(m, side, "skipped", result.trail, "no market entry order")
            return
        if raw_stop is None:
            self.decision(m, side, "skipped", result.trail, "the protective stop has no level yet")
            return
        stop = _price(raw_stop, record, ROUND_FLOOR if side is Side.LONG else ROUND_CEILING)
        if (stop >= reference) if side is Side.LONG else (stop <= reference):
            self.decision(
                m, side, "skipped", result.trail, f"the stop {stop} is not on the loss side"
            )
            return
        targets: list[dict[str, object]] = []
        for e in self.plan.exits:
            if e.use is ExitUse.TARGET:
                level = m.instances[f"{side.value}.{e.binding.key}"].update(
                    {"entry_price": reference, "stop_price": stop}
                    | self.unit.params(e.binding, numbers)
                )
                if isinstance(level, Decimal):
                    targets.append({"price": str(_price(level, record)), "fraction": "1/1"})
        if not isinstance(account, Account):
            self.decision(m, side, "skipped", result.trail, "no account facts to size from")
            return
        size = m.instances["sizer"].update(
            {
                "equity": account.equity,
                "entry_price": reference,
                "stop_price": stop,
                "record": record,
            }
            | self.unit.params(self.plan.sizer, numbers)
        )
        if not isinstance(size, Size) or size.lots is None:
            reason = size.skip_reason if isinstance(size, Size) else "the sizer answered nothing"
            self.decision(m, side, "skipped", result.trail, f"sizer: {reason}")
            return
        protection: dict[str, object] = {"stop": str(stop), "targets": targets}
        per_bar = next((e for e in self.plan.exits if e.use is ExitUse.PER_BAR), None)
        if per_bar is not None:
            bars = self.unit.params(per_bar.binding, numbers).get("bars")
            if bars is not None:
                protection["time_exit_bars"] = int(bars)
        row = self.decision(m, side, "taken", result.trail, "all slots hold")
        compiled = self.unit.compiled
        target = self.unit.target
        self.intents.append(
            {
                "contract_format_version": UNIT_INTENT_FORMAT_VERSION,
                "intent_family": "entry",
                "unit": {
                    "unit_id": compiled.unit.unit_id,
                    "version_ref": compiled.document_fingerprint.value,
                    "compiled_fingerprint": compiled.compiled_fingerprint.value,
                },
                "instrument": {"venue": record.venue, "symbol": record.symbol},
                "market_id": m.market_id,
                "direction": side.value,
                "reason_code": {"code": compiled.unit.family_id, "book_family": "unit"},
                "execution_target": {
                    "role": target.role.value,
                    "venue_id": target.venue_id.value,
                    "account_id": target.account_id,
                },
                "order": {"type": "market"},
                "quantity": f"{size.lots:f}",
                "sizer_receipt": {
                    "inputs_used": ["equity", "entry_price", "stop_price", "record"],
                    "rounding_residue_r": "0/1",
                },
                "protection": protection,
                "not_before": bar.knowable_at.value_ns,
                "placeholder_labels": list(compiled.placeholders),
                "decision_row_id": row,
            }
        )

    # --- motion ----------------------------------------------------------------------

    def motion(self, trades: Sequence[ClosedTrade], flat: bool) -> None:
        unit = self.unit
        for slow in self.plan.slow:
            name = slow.number.name
            state, move = calibrate(
                slow.number,
                unit.slow_rules[name],
                unit.slow[name],
                trades,
                instant=self.instant,
                flat=flat,
            )
            unit.slow[name] = state
            if move is None:
                continue
            self.calibrations.append(
                CalibrationRow(
                    row_id=self.row_id(),
                    number=name,
                    old=move.old,
                    new=move.new,
                    rule=slow.number.rule_pin,
                    from_trade_id=move.read_trades.from_trade_id,
                    to_trade_id=move.read_trades.to_trade_id,
                    count=move.read_trades.count,
                    statistic={"trades_read": str(move.read_trades.count)},
                    watermark=move.watermark,
                )
            )


def _required_keys(compiled: CompiledUnit) -> frozenset[str]:
    keys = {"account", "own_journal"}
    for market, _ in compiled.plan.markets:
        keys.add(f"bars:{compiled.plan.stream}:{market.market_id}")
        keys.add(f"own_position:{market.market_id}")
    return frozenset(keys)


def _starting(
    compiled: CompiledUnit, assignment: Mapping[str, Decimal] | None
) -> Result[dict[str, Decimal]]:
    start = {s.number.name: compiled.plan.defaults[s.number.name] for s in compiled.plan.slow}
    for name, value in (assignment or {}).items():
        spec = compiled.unit.numbers.get(name)
        if name not in start or spec is None or spec.range is None:
            return invalid(
                "assignment", "an assignment names the unit's calibrated numbers", name=name
            )
        if not spec.range.min <= value <= spec.range.max:
            return invalid("assignment", "a starting value lies inside its range", name=name)
        start[name] = value
    return Ok(start)


def _core(
    compiled: CompiledUnit,
    read_surfaces: Mapping[str, Surface],
    scope_id: str,
    execution_target: ExecutionTarget,
    assignment: Mapping[str, Decimal] | None,
    trace_level: TraceLevel,
    motion: MotionSwitch,
) -> Result[_Core]:
    needed = _required_keys(compiled)
    missing, extra = sorted(needed - set(read_surfaces)), sorted(set(read_surfaces) - needed)
    if missing or extra:
        return invalid(
            "read_surfaces",
            "a hosted unit takes exactly its own surfaces",
            missing=tuple(missing),
            extra=tuple(extra),
        )
    if not scope_id.strip():
        return invalid("scope_id", "a hosted unit needs the run or deployment id")
    start = _starting(compiled, assignment)
    if is_refusal(start):
        return start
    return Ok(
        _Core(
            compiled,
            calibrated=start.value,
            surfaces=MappingProxyType(dict(read_surfaces)),
            scope_id=scope_id,
            execution_target=execution_target,
            trace_level=trace_level,
            motion=motion,
        )
    )


def construct_unit(
    compiled: CompiledUnit,
    *,
    read_surfaces: Mapping[str, Surface],
    scope_id: str,
    execution_target: ExecutionTarget,
    assignment: Mapping[str, Decimal] | None = None,
    trace_level: TraceLevel = TraceLevel.EVENTS,
    motion: MotionSwitch = MotionSwitch.ON,
) -> Result[HostedUnit]:
    """Host a compiled unit. ``assignment`` holds the calibrated values the run starts from
    (the unit's defaults when ``None``); ``scope_id`` is the QMB run id or the deployment id."""
    core = _core(
        compiled, read_surfaces, scope_id, execution_target, assignment, trace_level, motion
    )
    if is_refusal(core):
        return core
    return Ok(HostedUnit(core.value))


def restore_unit(
    snapshot: Mapping[str, object],
    compiled: CompiledUnit,
    *,
    read_surfaces: Mapping[str, Surface],
    scope_id: str,
    execution_target: ExecutionTarget,
    assignment: Mapping[str, Decimal] | None = None,
    trace_level: TraceLevel = TraceLevel.EVENTS,
    motion: MotionSwitch = MotionSwitch.ON,
) -> Result[HostedUnit]:
    """Resume from ``snapshot``. A snapshot of another compiled fingerprint or state schema
    starts the unit cold, and its first step carries a ``cold_start`` event with the reason."""
    built = _core(
        compiled, read_surfaces, scope_id, execution_target, assignment, trace_level, motion
    )
    if is_refusal(built):
        return built
    core = built.value
    found = snapshot.get("state_schema_version")
    if found != STATE_SCHEMA_VERSION:
        reason = f"state schema {found!r}, this door reads {STATE_SCHEMA_VERSION}"
    elif snapshot.get("compiled_fingerprint") != compiled.compiled_fingerprint.value:
        reason = "the snapshot belongs to another compiled fingerprint"
    else:
        core.load(snapshot)
        return Ok(HostedUnit(core))
    core.pending.extend(StateEvent("cold_start", m.market_id, reason) for m in core.markets)
    return Ok(HostedUnit(core))


@dataclass(frozen=True, slots=True)
class _Hosting:
    read_surfaces: Mapping[str, Surface]
    scope_id: str
    execution_target: ExecutionTarget


@dataclass(frozen=True, slots=True)
class UnitFactory:
    """The compiled unit as a structural ``BotFactory``.

    A unit belongs on ``construct_unit``. Driven through ``construct_bot``, the callback hands
    the unit's format-3 intents to ``accept_intents``, which refuses the first sized one; a
    factory not given ``hosting`` refuses at construct.
    """

    compiled: CompiledUnit
    bound: _Hosting | None = None

    def hosting(
        self,
        read_surfaces: Mapping[str, Surface],
        *,
        scope_id: str,
        execution_target: ExecutionTarget,
    ) -> UnitFactory:
        return UnitFactory(self.compiled, _Hosting(read_surfaces, scope_id, execution_target))

    def construct(
        self,
        *,
        declaration: object,
        assignment: Mapping[str, object],
        read_surfaces: Mapping[str, object],
    ) -> Result[_UnitCallback]:
        del declaration, assignment, read_surfaces
        if self.bound is None:
            return unsupported(
                "factory", "a unit is hosted through qml.protocol.unit.construct_unit"
            )
        hosted = construct_unit(
            self.compiled,
            read_surfaces=self.bound.read_surfaces,
            scope_id=self.bound.scope_id,
            execution_target=self.bound.execution_target,
        )
        if is_refusal(hosted):
            return hosted
        return Ok(_UnitCallback(hosted.value))


@dataclass(frozen=True, slots=True)
class _UnitCallback:
    hosted: HostedUnit

    def on_instant(self, evidence: object, /) -> object:
        instant = getattr(evidence, "evaluation_instant", None)
        step = self.hosted.on_instant(instant)
        if isinstance(step, TypedRefusal):
            return step
        return [intent.to_wire() for intent in step.value.intents]
