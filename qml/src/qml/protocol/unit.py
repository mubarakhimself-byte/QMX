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
positions this unit version's logic half opened, then entries. A market's entries wait for its
derived warm-up (``warming``, then ``ready``). Calibrated numbers move last, from
``own_journal``, only when the unit is flat. The stream's ``close`` and its bars are the bid
side; an entry's reference price is the ask close for a long and the bid close for a short.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal
from enum import StrEnum
from fractions import Fraction
from itertools import pairwise
from types import MappingProxyType
from typing import Final, Protocol, cast

from qmf.core.chrono import Instant
from qmf.core.fingerprint import Fingerprint, fingerprint
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qmf.risk.facts import Fact
from qmf.risk.journal import UNIT_FAULT
from qmf.risk.paper import ExecutionTarget
from qmf.risk.unit_intent import (
    UNIT_INTENT_FORMAT_VERSION,
    UnitEntryIntent,
    UnitExitIntent,
    parse_unit_intent,
)

from qml._refuse import invalid, unsupported
from qml.blocks.api import (
    Amount,
    EntryOrder,
    Instance,
    OutputType,
    Signal,
    Size,
    Skip,
)
from qml.compile.compiler import (
    BoundBlock,
    CompiledUnit,
    ExitUse,
    SidePlan,
    SlotPlan,
)
from qml.environment import current_environment
from qml.motion.engine import ClosedTrade, SlowState, calibrate
from qml.numbers.convert import RoundRule, to_quantity
from qml.numbers.records import InstrumentRecord
from qml.receipt import record_stored
from qml.unit.model import CombinerKind, Role, Side, ValueParam

__all__ = [
    "ACCOUNT_CURRENCY",
    "EXIT_FAULT",
    "EXIT_FAULT_BARS",
    "FAULT_CLEAN_BARS",
    "OHLC",
    "PER_TRADE_CAP_SHARE",
    "SEAM_JUMP_SCALE",
    "SIZE_BAND",
    "SIZE_BAND_MAX_LOTS",
    "STATE_SCHEMA_VERSION",
    "Account",
    "AdmitPort",
    "CalibrationRow",
    "DecisionRow",
    "Fault",
    "FaultPhase",
    "HostPort",
    "HostedUnit",
    "MotionSwitch",
    "OwnPosition",
    "Priced",
    "PricedEntry",
    "Proposal",
    "QuoteBar",
    "RatePort",
    "SeamCheck",
    "SizeBand",
    "SlotOutput",
    "StateEvent",
    "TraceLevel",
    "UnitFactory",
    "UnitIntent",
    "UnitStep",
    "accept_unit_intents",
    "construct_unit",
    "rate_used",
    "restore_unit",
    "seam_check",
]

STATE_SCHEMA_VERSION: Final[int] = 2
"""2 records the interpreter the snapshot was taken under (UT-09, QML-25)."""
SEAM_JUMP_SCALE: Final[Decimal] = Decimal(3)
"""The setting ``seam_jump_scale``: a seam flags past this many typical warm-up bar moves."""

ACCOUNT_CURRENCY: Final[str] = "USD"
"""Starting default of the account currency sizing is counted in (AD-10 "Currency"). The paper
lane and the demo account are in USD, and every shipped record quotes USD. Labelled placeholder,
owner numbers talk: RC-07 brings each host's real account currency and the rate for a quote that
differs, and this default goes."""
SIZE_BAND_MAX_LOTS: Final[Decimal] = Decimal("100")
"""Starting default of the ``size_band_max_lots`` setting: the most lots one entry may take
(AD-10, PH E8). It catches an absurd answer such as 5,000 lots, never a size a person chose, and a
host replaces the row rather than this number. Labelled placeholder, owner numbers talk."""
PER_TRADE_CAP_SHARE: Final[Decimal] = Decimal("1")
"""Starting default of the ``per_trade_cap_share`` setting: the largest share of equity one entry
may put at risk. At 1 an entry may risk the whole account, so only an answer above that (a bug,
not a choice) is refused. Labelled placeholder, owner numbers talk."""
FAULT_CLEAN_BARS: Final[int] = 8
"""Starting default of the ``fault_clean_bars`` setting: the clean bars a unit needs after a fault
before its entries come back (AD-23). Eight bars is about two hours on the 15-minute stream the
shipped templates run, long enough for the fault's card to be seen and short enough that a fixed
block returns the same session. Labelled placeholder, range one to 96 bars, owner numbers talk."""
EXIT_FAULT: Final[str] = "exit_fault"
"""The reason a position is closed when its unit's own exits cannot run for ``exit_fault_bars``
bars (AD-13, AD-23 step 4). It is the ``close_scope`` port's word, and the host's close row
carries it."""
EXIT_FAULT_BARS: Final[int] = 3
"""Starting default of the ``exit_fault_bars`` setting: the bars a held position's exits may fail to
run before the host's ``close_scope`` port closes it (AD-13, AD-23 step 4). The venue's stop rests
through the gap, so three bars is long enough for a transient fault to clear and short enough that
a position never sits with no exit able to run for an hour on the 15-minute stream the shipped
templates run. Labelled placeholder, range one to 96 bars, owner numbers talk."""

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


class RatePort(Protocol):
    """Where a host supplies ``market.rate:<quote>`` for the instant it prices at (AD-10, AD-15).

    ``currency`` is the account currency every rate converts into. QMB reads the fact from the
    conversion market's replay bars and the node from its feed's last closed bar; this seam is
    what lets either host put the fact in front of the one converter.
    """

    @property
    def currency(self) -> str: ...

    def rate(self, record: InstrumentRecord, instant: Instant) -> Fact | None: ...


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
    currency: str = ACCOUNT_CURRENCY
    rates: Mapping[str, Fact] = MappingProxyType({})
    """``market.rate:<quote>`` by the quote currency each converts from, its value the exact
    rational (AD-10 "Currency"). A host supplies one per quote its unit reads; the account's own
    currency takes the ``Fact(1)`` fast path and never looks here."""


@dataclass(frozen=True, slots=True)
class SlotOutput:
    slot: str
    binding: str
    output: str | None


@dataclass(frozen=True, slots=True)
class DecisionRow:
    """One decision, with every input the size read, so one row answers "why this size?".

    ``price`` fills the trail on the row it prices: the sizer that answered, the facts it read
    with their sources and ages, the steps from the sizer's amount to the venue's quantity, each
    link's verdict, and the two fingerprints the row was made under. A host journals the row
    before any order leaves (AD-9's "One row"), and ``qml/receipt.py`` reads it back.
    """

    row_id: str
    instant: Instant
    market_id: str
    side: Side
    outcome: str
    slot_trail: tuple[SlotOutput, ...]
    numbers_in_force: Mapping[str, Decimal]
    reason: str
    readings_used: tuple[object, ...] = ()
    binding: str = ""
    """The sizer binding that answered the amount, ``block@version``. A row replays alone, so it
    names the block it came from even when the amount, not the block, is what replays."""
    inputs: Mapping[str, object] = MappingProxyType({})
    """Every input the size read, in the row's own stored form: each a ``Fact`` with its value,
    read time, source and state, and ``record``, the instrument record's own facts in the form
    ``parse_record`` reads back."""
    steps: Mapping[str, Amount] = MappingProxyType({})
    """The positions of the size side by side (FUNNEL D42): ``wanted`` is the sizer's answer,
    ``approved`` the quantity the one converter and the admit row allowed. ``filled`` is not
    here, because the row is journalled before any order leaves and only the ``fill`` row knows
    what the venue took."""
    verdicts: tuple[str, ...] = ()
    """Each link's verdict in the order it ran, in AD-9's words: ``none`` when it passed,
    ``refuse`` (or the code it refused by) when it stopped the entry."""
    logic_fp: str = ""
    risk_fp: str = ""
    placeholders: tuple[str, ...] = ()
    written_before_send: bool = False
    """True on a row a host's journal wrote before the send it names. A unit mints false: it
    writes nothing, and a flag the unit set could not be true."""


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


class FaultPhase(StrEnum):
    """The phase of one step that raised. ``exit`` and ``host`` are raised by later PRs: a raising
    exit block is the exit step's, and a raise past ``_Run.step`` is the host's (AD-23, AD-13)."""

    UPDATE = "update"
    ENTRIES = "entries"
    PRICE = "price"
    MOTION = "motion"
    EXIT = "exit"
    HOST = "host"


@dataclass(frozen=True, slots=True)
class Fault:
    """One block's raise, as a row on the answer (AD-23).

    ``block`` is the raising binding's pin, so a card and a journal row name the block its owner
    fixes. ``code`` is the risk-event code this row becomes; every fault the unit raises today is a
    ``unit_fault``, and a later chain link's fault carries its own code.
    """

    block: str
    phase: FaultPhase
    code: str = UNIT_FAULT


@dataclass(frozen=True, slots=True)
class UnitStep:
    instant: Instant
    intents: tuple[UnitIntent, ...]
    decisions: tuple[DecisionRow, ...]
    calibrations: tuple[CalibrationRow, ...]
    state_events: tuple[StateEvent, ...]
    proposals: tuple[Proposal, ...] = ()
    """The entries whose slots held, with no size yet: the host prices each one in pass two."""
    faults: tuple[Fault, ...] = ()
    """Each block that raised, with the phase it raised in. That unit's entries stop until
    ``fault_clean_bars`` clean bars have passed; its exits keep running."""


@dataclass(frozen=True, slots=True)
class Proposal:
    """One entry whose slots held, before any size: every wire field but the quantity and the
    receipt, the row it will land, and the evidence its sizer reads (AD-1, AD-10).

    It carries no account fact, so a host can park it and price it later on fresh facts.
    """

    wire: Mapping[str, object]
    row: DecisionRow
    market_id: str
    side: Side
    entry_price: Decimal
    stop: Decimal
    params: Mapping[str, Decimal]
    record: InstrumentRecord


@dataclass(frozen=True, slots=True)
class PricedEntry:
    """One entry's size after the converter: the number the admit row judges."""

    amount: Amount
    quantity: Decimal
    residue_r: Decimal
    money_at_risk: Decimal | None
    equity: Decimal


class AdmitPort(Protocol):
    """The host's entry seam after pricing: ``None`` passes the entry, a code refuses it."""

    def admit(self, proposal: Proposal, entry: PricedEntry) -> str | None: ...


class HostPort(Protocol):
    """The host's last fall-through when a held position's own exits cannot run (AD-13, AD-23
    step 4).

    The unit answers the fault and, after ``exit_fault_bars`` bars with no exit able to run, asks
    its host to close the position. The node closes it through its own scope close; QMB closes it
    at the next bar's open. ``qml`` imports no host, so the host injects this port.
    """

    def close_scope(self, unit: object, why: str) -> None: ...


@dataclass(frozen=True, slots=True)
class SizeBand:
    """The one row that catches an absurd size after the converter (AD-10, PH E8): a ceiling on
    the quantity and a ceiling on the money one entry risks. A host that wants other vetoes passes
    its own row; this one is what every host gets until the node chain lands."""

    max_lots: Decimal = SIZE_BAND_MAX_LOTS
    max_money_at_risk_share: Decimal = PER_TRADE_CAP_SHARE

    def admit(self, proposal: Proposal, entry: PricedEntry) -> str | None:
        del proposal
        if (
            entry.money_at_risk is not None
            and entry.equity > 0
            and entry.money_at_risk > entry.equity * self.max_money_at_risk_share
        ):
            return "per_trade_cap"
        if entry.quantity > self.max_lots:
            return "size_band"
        return None


SIZE_BAND: Final[SizeBand] = SizeBand()
"""The size band every host gets until a host passes its own admit row."""


@dataclass(frozen=True, slots=True)
class Priced:
    """What ``price`` answers for one proposal: the sized entry intent, or the code it skipped by.
    The row comes back either way, so the caller writes it before any order leaves."""

    row: DecisionRow
    intent: UnitIntent | None
    code: str | None


@dataclass(frozen=True, slots=True)
class _Skip:
    """A sizer's answer that cannot be sized, as the code it records and the words beside it."""

    code: str
    detail: str = ""


_SIZER_PORTS: Final[tuple[str, ...]] = ("equity", "entry_price", "stop_price", "record")
"""The evidence a sizer's face declares and the host passes, in the order the receipt names it."""


def _amount(answer: object) -> Amount | _Skip:
    """Every sizer answer as the amount the converter reads, or the skip it is. A ``Size`` states
    lots, so it reads as a quantity amount and skips the arithmetic (AD-10)."""
    match answer:
        case Amount():
            return answer
        case Size(lots=lots, skip_reason=reason):
            if lots is None:
                return _Skip("sizer_skip", reason or "the sizer answered nothing")
            return Amount(kind="quantity", value=lots, basis="gross_at_stop")
        case Skip(reason=reason):
            return _Skip("sizer_skip", reason)
        case _:
            return _Skip("sizer_silent", "the sizer answered nothing")


def _skip_text(code: str, detail: str) -> str:
    """The row's words. Every sized skip keeps the ``sizer: `` head the journal maps to its
    closed ``sizer_skip`` code, and the specific code stays readable beside it."""
    if code == "sizer_silent":
        return "the sizer answered nothing"
    return f"sizer: {code}" + (f" ({detail})" if detail and detail != code else "")


def _priced_skip(row: DecisionRow, code: str, detail: str) -> Priced:
    return Priced(replace(row, outcome="skipped", reason=_skip_text(code, detail)), None, code)


def _sizing_inputs(proposal: Proposal, facts: Account) -> dict[str, object]:
    """Every input the size reads, each as a fact with the instant it was read at, so the row
    carries its own evidence and a replay never looks one up."""
    instant = proposal.row.instant
    inputs: dict[str, object] = {
        "equity": Fact(
            facts.equity, instant, "open", "the account's equity at the pricing instant"
        ),
        "entry_price": Fact(
            proposal.entry_price, instant, "open", "the entry bar's close on the side's own quote"
        ),
        "stop_price": Fact(proposal.stop, instant, "open", "the stop exit's level"),
        "record": record_stored(proposal.record),
    }
    rate = _rate(proposal.record, facts, instant)
    if rate is not None:
        inputs[f"market.rate:{proposal.record.currency}"] = rate
    return inputs


def _rate(record: InstrumentRecord, facts: Account, now: Instant) -> Fact | None:
    """The rate into the account's currency: one when the record quotes that currency, and
    otherwise the fact the host supplied for that quote. A quote with no fact is what the
    converter names ``rate_absent``, and one past its age is ``rate_stale``."""
    if record.currency == facts.currency:
        return Fact(Decimal(1), now, "open", "the account is in the record's quote currency")
    return facts.rates.get(record.currency)


def rate_used(record: InstrumentRecord, facts: Account, now: Instant) -> Fact | None:
    """The rate ``HostedUnit.price`` sizes an entry at, for the host that stamps its row."""
    return _rate(record, facts, now)


def _residue_text(residue: Decimal) -> str:
    """The converter's residue as the wire's rational, ``n/d``."""
    exact = Fraction(residue)
    return f"{exact.numerator}/{exact.denominator}"


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
    """``value`` on the record's tick, written to its digits."""
    ticks = (value / record.tick_size).quantize(Decimal(1), rounding=rounding)
    return (ticks * record.tick_size).quantize(Decimal(1).scaleb(-record.digits))


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


def _price_of(given: object) -> Decimal | None:
    """The price in a binding's input: the value, or a whole bar's close."""
    value = (
        cast("Mapping[str, object]", given).get("close") if isinstance(given, Mapping) else given
    )
    return value if isinstance(value, Decimal) else None


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
        fault_clean_bars: int,
        exit_fault_bars: int = EXIT_FAULT_BARS,
        port: HostPort | None = None,
    ) -> None:
        self.compiled = compiled
        self.plan = compiled.plan
        self.surfaces = surfaces
        self.scope_id = scope_id
        self.target = execution_target
        self.trace = trace_level
        self.motion = motion
        self.fault_clean_bars = fault_clean_bars
        self.exit_fault_bars = exit_fault_bars
        self.port = port
        """The host's last fall-through, attached by the host after the unit is built (AD-13)."""
        self.exit_faults: dict[str, int] = {}
        """Each held position's consecutive bars with no exit able to run (AD-13)."""
        self.close_asked: set[str] = set()
        """The positions whose host was already asked to close them, so the ask fires once."""
        self.warm_up = max(compiled.warm_up.values(), default=0)
        self.slow = {
            s.number.name: SlowState(value=calibrated[s.number.name]) for s in self.plan.slow
        }
        self.slow_rules = {s.number.name: s.block.make(s.params, {}) for s in self.plan.slow}
        self.pending: list[StateEvent] = []
        self.pending_faults: list[Fault] = []
        """A fault made outside a step, waiting for the next answer to carry it."""
        self.benched = False
        """Entries are off after a fault until ``fault_clean_bars`` clean bars have passed."""
        self.clean_bars = 0
        """Bars with no fault since the one that benched the unit."""
        self.markets = [
            self.market(market.market_id, record) for market, record in self.plan.markets
        ]

    def bench(self) -> None:
        """A fault benches the unit's entries and starts the clean count again (AD-23)."""
        self.benched = True
        self.clean_bars = 0

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
            "environment": {"python": current_environment().python},
            "markets": markets,
            "slow": slow,
        }

    def shape_gap(self, snapshot: Mapping[str, object]) -> str | None:
        """Where ``snapshot`` departs from this unit's state shape, or ``None`` when it holds
        every market, block, slow number and field this unit's own snapshot would."""
        fresh = self.snapshot_state()
        for key in ("markets", "slow"):
            if key not in snapshot:
                return f"it lacks {key}"
            if gap := _gap(fresh[key], snapshot[key], (key,)):
                return gap
        derived = {
            side.side.value: {d.number for d in self.plan.derived if d.side is side.side}
            for side in self.plan.sides
        }
        made = self.timer()
        timer = made.export_state() if made is not None else None
        markets = cast("Mapping[str, Mapping[str, object]]", snapshot["markets"])
        for m in self.markets:
            saved = markets[m.market_id]
            where = ("markets", m.market_id)
            sides = saved["derived"]
            if not isinstance(sides, Mapping):
                return f"{_where((*where, 'derived'))} is not a table"
            for side, numbers in cast("Mapping[str, object]", sides).items():
                if side not in derived:
                    return f"{_where((*where, 'derived'))} has unknown {side}"
                if gap := _keys(derived[side], numbers, (*where, "derived", side), exact=False):
                    return gap
            timers = saved["timers"]
            if not isinstance(timers, Mapping):
                return f"{_where((*where, 'timers'))} is not a table"
            for pid, state in cast("Mapping[str, object]", timers).items():
                if timer is None:
                    return f"{_where((*where, 'timers'))} has unknown {pid}"
                if gap := _gap(timer, state, (*where, "timers", pid)):
                    return gap
        return None

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
                timer = self.timer()
                if timer is not None:  # shape_gap sent a snapshot with timers and no exit cold
                    timer.import_state(state)
                    m.timers[pid] = timer
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

    def timer(self) -> Instance | None:
        """The per-bar exit for one position, or ``None`` for a unit with no time exit, which
        layer E warns of (UT-18)."""
        per_bar = next((e for e in self.plan.exits if e.use is ExitUse.PER_BAR), None)
        if per_bar is None:
            return None
        return per_bar.binding.block.make(
            self.params(per_bar.binding, self.plan.defaults), per_bar.binding.inputs
        )

    @property
    def exit_pin(self) -> str:
        """The per-bar exit's pin, the root-cause key its fault is filed under (AD-13)."""
        per_bar = next((e for e in self.plan.exits if e.use is ExitUse.PER_BAR), None)
        return "per-bar-exit" if per_bar is None else per_bar.binding.pin


class HostedUnit:
    """One compiled unit hosted for one run or deployment, driven one instant at a time."""

    def __init__(self, core: _Core) -> None:
        self._core = core

    def attach_port(self, port: HostPort) -> None:
        """Hand this unit its host's last fall-through (AD-13). The host attaches it after the
        unit is built, because the port lives on the handler that builds its surfaces."""
        self._core.port = port

    def bench(self) -> None:
        """Stop this unit's entries until its clean bars pass: the host's own fault wall
        (AD-23)."""
        self._core.bench()

    @property
    def compiled(self) -> CompiledUnit:
        return self._core.compiled

    def on_instant(self, instant: object, /) -> Result[UnitStep]:
        if not isinstance(instant, Instant):
            return invalid("instant", "the evaluation instant rides the call", given=repr(instant))
        return _Run(self._core, instant).step()

    def price(self, proposal: Proposal, facts: Account, admit: AdmitPort = SIZE_BAND) -> Priced:
        """Spell one entry's size on the facts the host read for it (AD-1, AD-10).

        The one call that sizes an entry: the sizer answers an amount from this evidence, the one
        converter spells the venue's quantity and the residue from the record and the rate, and
        the admit row catches an absurd size after it. The row comes back either way, so the
        caller writes it before any order leaves, carrying the whole trail: the sizer that
        answered, every fact it read with its source and age, the steps it took and each link's
        verdict. No account fact is read here by the exits.
        """
        core = self._core
        compiled = core.compiled
        inputs = _sizing_inputs(proposal, facts)

        def receipt(
            row: DecisionRow, steps: Mapping[str, Amount], verdicts: tuple[str, ...]
        ) -> DecisionRow:
            """The row with its size trail on it, whatever the sizing answered."""
            return replace(
                row,
                binding=compiled.plan.sizer.pin,
                inputs=inputs,
                steps=steps,
                verdicts=verdicts,
                logic_fp=compiled.logic_fingerprint.value,
                risk_fp=compiled.risk_fingerprint.value,
                placeholders=compiled.placeholders,
            )

        def ended(
            row: DecisionRow,
            steps: Mapping[str, Amount],
            verdicts: tuple[str, ...],
            code: str,
            detail: str,
        ) -> Priced:
            """A skip whose trail ends at the link that refused it."""
            return _priced_skip(receipt(row, steps, verdicts), code, detail)

        market = next((m for m in core.markets if m.market_id == proposal.market_id), None)
        if market is None:
            return ended(
                proposal.row,
                {},
                ("sizer: refuse",),
                "sizer_skip",
                "the proposal names no market this unit runs",
            )
        try:
            answer = market.instances["sizer"].update(
                {
                    "equity": facts.equity,
                    "entry_price": proposal.entry_price,
                    "stop_price": proposal.stop,
                    "record": proposal.record,
                }
                | dict(proposal.params)
            )
            amount = _amount(answer)
            if isinstance(amount, _Skip):
                return ended(proposal.row, {}, ("sizer: refuse",), amount.code, amount.detail)
            converted = to_quantity(
                amount,
                proposal.entry_price,
                proposal.stop,
                proposal.record,
                _rate(proposal.record, facts, proposal.row.instant),
                RoundRule(now=proposal.row.instant),
            )
        except Exception:  # the fault wall: a sizer or converter raise is a skip, never a crash
            core.pending_faults.append(Fault(compiled.plan.sizer.pin, FaultPhase.PRICE))
            core.bench()
            return ended(proposal.row, {}, ("sizer: refuse",), UNIT_FAULT, "the sizer raised")
        if converted.skipped is not None or converted.quantity is None:
            return ended(
                proposal.row,
                {"wanted": amount},
                ("sizer: none", "converter: refuse"),
                converted.skipped or "kind_unknown",
                "",
            )
        steps: dict[str, Amount] = {
            "wanted": amount,
            "approved": Amount(kind="quantity", value=converted.quantity, basis=amount.basis),
        }
        entry = PricedEntry(
            amount=amount,
            quantity=converted.quantity,
            residue_r=converted.residue_r,
            money_at_risk=amount.value if amount.kind == "money_at_risk" else None,
            equity=facts.equity,
        )
        code = admit.admit(proposal, entry)
        if code is not None:
            return ended(
                proposal.row,
                steps,
                ("sizer: none", "converter: none", f"size_band: refuse ({code})"),
                code,
                "",
            )
        wire = dict(proposal.wire) | {
            "quantity": f"{converted.quantity:f}",
            "sizer_receipt": {
                "inputs_used": list(_SIZER_PORTS),
                "rounding_residue_r": _residue_text(converted.residue_r),
            },
        }
        admitted = accept_unit_intents((wire,))
        if is_refusal(admitted):
            reason = admitted.context.get("reason")
            return ended(
                proposal.row,
                steps,
                ("sizer: none", "converter: none", "size_band: none", "intent: refuse"),
                "sizer_skip",
                str(reason) if reason else "",
            )
        row = receipt(proposal.row, steps, ("sizer: none", "converter: none", "size_band: none"))
        return Priced(row, admitted.value[0], None)

    @property
    def calibrated_values(self) -> Mapping[str, Decimal]:
        return MappingProxyType({name: s.value for name, s in self._core.slow.items()})

    def snapshot(self) -> Mapping[str, object]:
        """Every instance's state, the motion state and the fingerprint it belongs to (UT-09)."""
        return self._core.snapshot_state()


class _Fault(Exception):
    """A block's own exception, carried to its phase's wall with the block named."""

    def __init__(self, block: str) -> None:
        super().__init__(block)
        self.block = block


def _answered(block: str, instance: Instance, evidence: Mapping[str, object]) -> object:
    """One block call. A raise becomes this bar's ``Fault``, named by the block's pin, and the
    phase it raised in keeps running (AD-23). No threads: a plain ``try``."""
    try:
        return instance.update(evidence)
    except Exception as bad:  # a block's raise is a Fault, never a step refusal (AD-23)
        raise _Fault(block) from bad


class _Run:
    """One ``on_instant`` call: reads the surfaces once, then exits, entries and motion."""

    def __init__(self, unit: _Core, instant: Instant) -> None:
        self.unit = unit
        self.plan = unit.plan
        self.instant = instant
        self.intents: list[Mapping[str, object]] = []
        self.proposals: list[Proposal] = []
        self.decisions: list[DecisionRow] = []
        self.calibrations: list[CalibrationRow] = []
        self.events: list[StateEvent] = list(unit.pending)
        unit.pending.clear()
        self.faults: list[Fault] = list(unit.pending_faults)
        unit.pending_faults.clear()
        self.raised = False
        self.ordinal = 0

    def fault(self, block: str, phase: FaultPhase) -> None:
        """Record this bar's fault, and bench the unit's entries from here (AD-23)."""
        self.faults.append(Fault(block, phase))
        self.raised = True
        self.unit.bench()

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
        if fresh and self.unit.benched and self.unit.clean_bars >= self.unit.fault_clean_bars:
            self.unit.benched = False
        benched = self.unit.benched
        results: dict[str, dict[Side, _Side]] = {}
        for m in self.unit.markets:
            bar = fresh.get(m.market_id)
            if bar is None:
                continue
            try:
                results[m.market_id] = self.update(m, bar)
            except _Fault as fault:
                self.fault(fault.block, FaultPhase.UPDATE)
        for m in self.unit.markets:
            self.exits(m, positions[m.market_id], m.market_id in fresh)
        for m in self.unit.markets:
            bar = fresh.get(m.market_id)
            sides = results.get(m.market_id)
            if benched or bar is None or sides is None:
                continue
            try:
                self.entries(m, bar, sides, positions[m.market_id])
            except _Fault as fault:
                self.fault(fault.block, FaultPhase.ENTRIES)
        if self.unit.motion is MotionSwitch.ON:
            trades = cast("Sequence[ClosedTrade]", journal if isinstance(journal, Sequence) else ())
            try:
                self.motion(trades, all(p is None for p in positions.values()))
            except _Fault as fault:
                self.fault(fault.block, FaultPhase.MOTION)
        if fresh and self.unit.benched and not self.raised:
            self.unit.clean_bars += 1
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
                proposals=tuple(self.proposals),
                faults=tuple(self.faults),
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
                key = f"{side.value}.{e.binding.key}"
                if e.use is not ExitUse.STOP or key not in m.instances:
                    continue
                evidence = {"series": bar.bid.fields()} | self.unit.params(
                    e.binding, m.in_force[side]
                )
                _answered(e.binding.pin, m.instances[key], evidence)
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
                if part == "":
                    return {**bar.bid.fields(), "time": bar.knowable_at.value_ns}
                return bar.bid.fields()[part]
            return _value(outputs.get(ref))

        for slot in plan.slots:
            conditions: list[bool | None] = []
            for b in slot.bindings:
                evidence = {port: resolve(ref) for port, ref in b.inputs.items()}
                evidence |= self.unit.params(b, numbers)
                out = _answered(b.pin, m.instances[b.key], evidence)
                outputs[b.name] = out
                trail.append(SlotOutput(slot.name, b.name, _text(out)))
                if isinstance(out, EntryOrder):
                    order = out
                conditions.append(self.condition(b, out, evidence, plan.side))
            held[slot.name] = self.combine(slot, conditions)
        for d in self.plan.derived:
            if d.side is plan.side:
                fed = _answered(
                    d.pin,
                    m.instances[f"derived.{d.side.value}.{d.number}"],
                    {"series": _value(outputs.get(d.source))},
                )
                spec = self.unit.compiled.unit.numbers[d.number]
                if isinstance(fed, Decimal) and spec.range is not None:
                    m.derived.setdefault(d.side, {})[d.number] = min(
                        spec.range.max, max(spec.range.min, fed)
                    )
        failing = [f"{name}: {why}" for name, (ok, why) in held.items() if not ok]
        trigger = any(
            held[s.name][0] for s in plan.slots if s.role is Role.TRIGGER and s.has_conditions
        )
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
                inputs = (_price_of(evidence.get(p)) for p in b.inputs)
                price = next((p for p in inputs if p is not None), None)
                if price is None:
                    return None
                return price > out if side is Side.LONG else price < out
            case _:
                return None

    @staticmethod
    def combine(slot: SlotPlan, conditions: Sequence[bool | None]) -> tuple[bool, str]:
        kept = [
            (b, c)
            for b, c in zip(slot.bindings, conditions, strict=True)
            if b.name not in slot.feeders
        ]
        if not kept:
            return True, ""
        absent = [b.name for b, c in kept if c is None]
        if absent and not slot.absent_is_false and slot.combiner is CombinerKind.ALL:
            return False, f"absent input {', '.join(absent)}"
        true = sum(1 for _, c in kept if c is True)
        match slot.combiner:
            case CombinerKind.ALL:
                ok = true == len(kept)
            case CombinerKind.ANY:
                ok = true >= 1
            case _:
                ok = true >= (slot.k or len(kept))
        if ok:
            return True, ""
        if absent and not slot.absent_is_false:
            return False, f"absent input {', '.join(absent)}"
        return False, "does not hold"

    # --- exits ---------------------------------------------------------------------

    def exits(self, m: _Market, position: OwnPosition | None, new_bar: bool) -> None:
        """This market's per-bar exits on ``position``.

        A position is this unit's when its key is this version's logic half, which a risk edit
        leaves alone, or this compile's own fingerprint, which a host that pins one compile
        stamps (AD-3). Either names this unit version, so another version's position is never
        closed. A raising exit block is skipped with a ``Fault`` and the next exit still runs; no
        exit able to run for ``exit_fault_bars`` bars asks the host's ``close_scope`` port to
        close the position (AD-13, AD-23 step 4). A step where this market has no new bar leaves
        that count alone, so a step of the other market's bar never resets it.
        """
        version = self.unit.compiled
        mine = position is not None and position.opened_by in (
            version.logic_fingerprint,
            version.compiled_fingerprint,
        )
        for gone in [pid for pid in m.timers if position is None or pid != position.position_id]:
            del m.timers[gone]
            m.exited.discard(gone)
        if position is None or not new_bar:
            return
        if not mine or position.position_id in m.exited:
            self.unit.exit_faults.pop(position.position_id, None)
            return
        timer = m.timers.get(position.position_id)
        if timer is None:
            timer = self.unit.timer()
            if timer is None:
                return
            m.timers[position.position_id] = timer
        try:
            out = timer.update({})
        except Exception:  # an exit's raise is this bar's Fault, never a step refusal (AD-13)
            self.fault(self.unit.exit_pin, FaultPhase.EXIT)
            self.no_exit_ran(position)
            return
        self.unit.exit_faults.pop(position.position_id, None)
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

    def no_exit_ran(self, position: OwnPosition) -> None:
        """One held position's exits could not run this bar. After ``exit_fault_bars`` in a row
        the host's ``close_scope`` port closes it, once (AD-13, AD-23 step 4)."""
        if position.position_id in self.unit.close_asked:
            return
        bars = self.unit.exit_faults.get(position.position_id, 0) + 1
        self.unit.exit_faults[position.position_id] = bars
        if bars < self.unit.exit_fault_bars:
            return
        self.unit.close_asked.add(position.position_id)
        port = self.unit.port
        if port is not None:
            port.close_scope(self.unit, EXIT_FAULT)

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
                self.enter(m, bar, side, result)

    def enter(self, m: _Market, bar: QuoteBar, side: Side, result: _Side) -> None:
        """The entry's slots held: collect what sizing it needs and no size.

        The size is made by ``HostedUnit.price`` on the host's read of the account facts, so an
        exit never waits on one and this pass reads no account fact (AD-1).
        """
        record = m.record
        numbers = m.in_force[side]
        reference = bar.ask.close if side is Side.LONG else bar.bid.close
        stop_plan = next((e for e in self.plan.exits if e.use is ExitUse.STOP), None)
        raw_stop = (
            _value(
                _answered(
                    stop_plan.binding.pin,
                    m.instances[f"{side.value}.{stop_plan.binding.key}"],
                    {},
                )
            )
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
                level = _answered(
                    e.binding.pin,
                    m.instances[f"{side.value}.{e.binding.key}"],
                    {"entry_price": reference, "stop_price": stop}
                    | self.unit.params(e.binding, numbers),
                )
                if isinstance(level, Decimal):
                    targets.append({"price": str(_price(level, record)), "fraction": "1/1"})
        protection: dict[str, object] = {"stop": str(stop), "targets": targets}
        per_bar = next((e for e in self.plan.exits if e.use is ExitUse.PER_BAR), None)
        if per_bar is not None:
            bars = self.unit.params(per_bar.binding, numbers).get("bars")
            if bars is not None:
                protection["time_exit_bars"] = int(bars)
        row = self.row_id()
        compiled = self.unit.compiled
        target = self.unit.target
        self.proposals.append(
            Proposal(
                wire={
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
                    "protection": protection,
                    "not_before": bar.knowable_at.value_ns,
                    "placeholder_labels": list(  # mock-data-scan: allow (field)
                        compiled.placeholders
                    ),
                    "decision_row_id": row,
                },
                row=DecisionRow(
                    row_id=row,
                    instant=self.instant,
                    market_id=m.market_id,
                    side=side,
                    outcome="taken",
                    slot_trail=result.trail,
                    numbers_in_force=MappingProxyType(dict(m.in_force.get(side, {}))),
                    reason="all slots hold",
                ),
                market_id=m.market_id,
                side=side,
                entry_price=reference,
                stop=stop,
                params=self.unit.params(self.plan.sizer, numbers),
                record=record,
            )
        )

    # --- motion ----------------------------------------------------------------------

    def motion(self, trades: Sequence[ClosedTrade], flat: bool) -> None:
        unit = self.unit
        for slow in self.plan.slow:
            name = slow.number.name
            try:
                state, move = calibrate(
                    slow.number,
                    unit.slow_rules[name],
                    unit.slow[name],
                    trades,
                    instant=self.instant,
                    flat=flat,
                )
            except Exception as bad:  # the fault wall: a rule's raise is a Fault (AD-23)
                raise _Fault(slow.number.rule_pin) from bad
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
                    statistic={
                        "trades_read": str(move.read_trades.count),
                        "mean_r": str(move.mean_r),
                        "mean_stamp": str(move.mean_stamp),
                    },
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
    fault_clean_bars: int,
    exit_fault_bars: int,
    port: HostPort | None,
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
    if fault_clean_bars < 0:
        return invalid(
            "fault_clean_bars",
            "the clean bars before entries return are zero or more",
            given=repr(fault_clean_bars),
        )
    if exit_fault_bars < 1:
        return invalid(
            "exit_fault_bars",
            "the bars before the close-scope fall-through are one or more",
            given=repr(exit_fault_bars),
        )
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
            fault_clean_bars=fault_clean_bars,
            exit_fault_bars=exit_fault_bars,
            port=port,
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
    fault_clean_bars: int = FAULT_CLEAN_BARS,
    exit_fault_bars: int = EXIT_FAULT_BARS,
    port: HostPort | None = None,
) -> Result[HostedUnit]:
    """Host a compiled unit. ``assignment`` holds the calibrated values the run starts from
    (the unit's defaults when ``None``); ``scope_id`` is the QMB run id or the deployment id;
    ``fault_clean_bars`` is the clean bars a faulted unit waits before its entries return;
    ``exit_fault_bars`` is the bars its exits may fail to run before ``port`` closes a position."""
    core = _core(
        compiled,
        read_surfaces,
        scope_id,
        execution_target,
        assignment,
        trace_level,
        motion,
        fault_clean_bars,
        exit_fault_bars,
        port,
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
    fault_clean_bars: int = FAULT_CLEAN_BARS,
    exit_fault_bars: int = EXIT_FAULT_BARS,
    port: HostPort | None = None,
) -> Result[HostedUnit]:
    """Resume from ``snapshot``. A snapshot of another state schema, compiled fingerprint or
    interpreter, or one whose markets, blocks, slow numbers or fields differ in shape from
    this unit's own snapshot, starts the unit cold, and its first step carries a
    ``cold_start`` event with the reason, so a restart never silently changes what the unit
    does. A block's ``export_state`` keeps the same keys for the whole run."""
    built = _core(
        compiled,
        read_surfaces,
        scope_id,
        execution_target,
        assignment,
        trace_level,
        motion,
        fault_clean_bars,
        exit_fault_bars,
        port,
    )
    if is_refusal(built):
        return built
    core = built.value
    reason = _cold_reason(snapshot, core)
    if reason is None:
        core.load(snapshot)
    else:
        core.pending.extend(StateEvent("cold_start", m.market_id, reason) for m in core.markets)
    return Ok(HostedUnit(core))


def _cold_reason(snapshot: Mapping[str, object], core: _Core) -> str | None:
    """Why ``snapshot`` cannot resume the fresh ``core`` here, or ``None`` when it can."""
    found = snapshot.get("state_schema_version")
    if found != STATE_SCHEMA_VERSION:
        return f"state schema {found!r}, this door reads {STATE_SCHEMA_VERSION}"
    if snapshot.get("compiled_fingerprint") != core.compiled.compiled_fingerprint.value:
        return "the snapshot belongs to another compiled fingerprint"
    env = snapshot.get("environment")
    saved = cast("Mapping[str, object]", env).get("python") if isinstance(env, Mapping) else None
    running = current_environment().python
    if saved is None:
        return f"the snapshot does not record its interpreter, this is Python {running}"
    if saved != running:
        return f"the snapshot was taken under Python {saved}, this is Python {running}"
    if gap := core.shape_gap(snapshot):
        return f"the snapshot does not hold this unit's state ({gap})"
    return None


_OPEN = frozenset({"derived", "timers"})
"""A market's tables whose keys grow as it runs; ``_Core.shape_gap`` checks them itself."""


def _where(path: tuple[str, ...]) -> str:
    return ".".join(path)


def _keys(
    want: Iterable[str], got: object, path: tuple[str, ...], *, exact: bool = True
) -> str | None:
    if not isinstance(got, Mapping):
        return f"{_where(path)} is not a table"
    found = set(cast("Mapping[str, object]", got))
    missing = sorted(set(want) - found) if exact else []
    if missing:
        return f"{_where(path)} lacks {', '.join(missing)}"
    extra = sorted(found - set(want))
    if extra:
        return f"{_where(path)} has unknown {', '.join(extra)}"
    return None


def _gap(want: object, got: object, path: tuple[str, ...]) -> str | None:
    """The first table or list in ``want`` that ``got`` lacks, misses a key of, or adds to."""
    if isinstance(want, Mapping):
        table = cast("Mapping[str, object]", want)
        if gap := _keys(table, got, path):
            return gap
        found = cast("Mapping[str, object]", got)
        for key, value in table.items():
            if path[0] == "markets" and len(path) == 2 and key in _OPEN:
                continue
            if gap := _gap(value, found[key], (*path, key)):
                return gap
        return None
    if isinstance(want, list) and not isinstance(got, list):
        return f"{_where(path)} is not a list"
    return None


@dataclass(frozen=True, slots=True)
class SeamCheck:
    """``jump`` is the seam's gap in typical warm-up bar moves; ``flag`` is ``jump > scale``."""

    flag: bool
    jump: Decimal


def seam_check(
    warmup_tail: Sequence[QuoteBar], live_head: QuoteBar, scale: Decimal = SEAM_JUMP_SCALE
) -> Result[SeamCheck]:
    """Compare where the warm-up ended with where live data starts (UT-11).

    The gap is the live head's bid open less the tail's last bid close, measured in the
    median absolute close-to-close move of the tail. The host journals a flag as
    ``seam_flag {stream, jump}``.
    """
    closes = [bar.bid.close for bar in warmup_tail]
    moves = sorted(abs(b - a) for a, b in pairwise(closes))
    if not moves:
        return invalid("warmup_tail", "a seam is measured against at least two warm-up bars")
    middle = len(moves) // 2
    typical = moves[middle] if len(moves) % 2 else (moves[middle - 1] + moves[middle]) / 2
    if typical == 0:
        return invalid("warmup_tail", "the warm-up tail never moved, so it cannot scale a gap")
    jump = abs(live_head.bid.open - closes[-1]) / typical
    return Ok(SeamCheck(flag=jump > scale, jump=jump))


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
        if step.value.proposals:
            # A unit's entry is priced by its own host (`HostedUnit.price`); the bot door has no
            # price call and no account facts, so it refuses at the ladder rather than drop it.
            return unsupported(
                "contract_format_version",
                "a unit is hosted through qml.protocol.unit.construct_unit, so its entry is "
                "priced and sent there; the bot door refuses a unit's entry",
            )
        return [intent.to_wire() for intent in step.value.intents]
