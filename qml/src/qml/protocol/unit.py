"""The unit door: hosting a compiled unit (AD-107, L0 AD-16).

``construct_unit`` and ``restore_unit`` return a ``HostedUnit``. Its ``on_instant(instant)``
reads the host's surfaces and returns a ``UnitStep``: CT-23 format 3 intents (admitted by
``accept_unit_intents``), decision rows, calibration rows and state events. ``construct_bot``,
``HostedBot`` and ``accept_intents`` are untouched and refuse a unit's sized intent (BR-A4).

The host injects these read surfaces, each an object with ``at(instant)``:

- ``bars:<stream>:<market_id>``: the latest closed ``QuoteBar`` of that stream knowable at the
  instant.
- ``own_position:<market_id>``: every position open on that market, as a tuple of
  ``PositionFacts``, of the ``OwnPosition`` a host that tracks none of its protection answers, or
  empty when flat. A unit may hold more than one there where its ``position_limit`` says so and
  the venue keeps them apart (AD-25).
- ``own_journal``: the ``ClosedTrade`` rows this run or deployment closed.
- ``account``: the ``Account`` facts the sizer reads.

On each instant, for each market whose primary bar is new: every block updates, exits run for
every position this unit version's logic half opened, then entries. A slot reads a slower stream
at its last closed bar, so neither the step nor any block sees a bar knowable after the instant. A
market's entries wait for every stream's own warm-up (``warming``, then ``ready``). Calibrated
numbers move last, from ``own_journal``, only when the unit is flat. The primary stream's ``close``
and its bars are the bid side; an entry's reference price is the ask close for a long and the bid
close for a short.
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
from qmf.risk.controls import ENTRY_SCOPES, Restore, RiskState, Verb
from qmf.risk.facts import Fact, Stake, open_risk
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
    ExitAction,
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
from qml.fold import Fold
from qml.motion.engine import ClosedTrade, SlowState, calibrate
from qml.numbers.convert import RoundRule, to_quantity
from qml.numbers.records import InstrumentRecord
from qml.protocol.controls import CONTROL_FLATTEN, Runner, own_facts
from qml.protocol.exits import (
    ExitAnswer,
    ExitSlot,
    ExitStack,
    PositionFacts,
    answer,
    chosen,
    facts_from,
)
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
    "ControlEvent",
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
    "StopPort",
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


@dataclass(frozen=True, slots=True)
class ControlEvent:
    """One brake row's answer this step (AD-12).

    ``kind`` is ``fired`` for a live row, ``would_fire`` for a row in shadow, and ``cold`` for a
    row whose declared facts are not there yet. ``code`` is the row's own word on its risk-event
    row (the block's entry id), or ``cold``. A host writes the row; the unit only answers it.
    """

    row: str
    pin: str
    scope: str
    kind: str
    verb: Verb
    factor: Decimal | None
    code: str
    reason: str


class FaultPhase(StrEnum):
    """The phase of one step that raised. ``exit`` and ``host`` are raised by later PRs: a raising
    exit block is the exit step's, and a raise past ``_Run.step`` is the host's (AD-23, AD-13)."""

    UPDATE = "update"
    ENTRIES = "entries"
    PRICE = "price"
    MOTION = "motion"
    EXIT = "exit"
    CONTROLS = "controls"
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
    controls: tuple[ControlEvent, ...] = ()
    """Each brake row's answer this step: fired, would fire, or cold (AD-12)."""
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


class StopPort(Protocol):
    """The host's door for the one brake that waits for a person (AD-12).

    A control row whose restore is ``hand`` stops entries until his resume. The unit asks its
    host for that stop when the row fires, and the node answers by calls to
    ``Runtime.risk_stop``: one ``lifecycle`` row by ``risk_rule`` and a stand-down held at the
    unit's scopes. QMB attaches no stop port, because a replay has no person to wait for.
    """

    def risk_stop(self, rule: str, reason: str) -> None: ...


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


def bet_key(family_id: str, market_id: str) -> str:
    """The bet a position on one market expresses: this unit's family, and the open it fires at.

    WALKS 3 writes this as ``family:session``. Sessions do not compile yet (RC-33), so the market
    stands in for the open. The key names no unit, so two units of one family on one market count
    their positions as one bet, which is what the group cap reads them as (I9, AD-25).
    """
    return f"{family_id}:{market_id}"


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
    drivers: tuple[str, ...] = ()
    """The slots whose answer held this bar, in the compiled order: what drove an entry, which its
    intent carries as its driver tags (I9)."""


@dataclass(slots=True)
class _Market:
    market_id: str
    record: InstrumentRecord
    instances: dict[str, Instance]
    derived: dict[Side, dict[str, Decimal]]
    """Each side's derived numbers: a number both sides bind moves once per bar per side."""
    last_bar_ns: dict[str, int] = field(default_factory=dict[str, int])
    """Each stream's bar this market last read, by when that bar became knowable."""
    bars: dict[str, int] = field(default_factory=dict[str, int])
    """Each stream's closed bars this market has read, counted apart from the others."""
    ready: bool = False
    """Whether every stream's warm-up was met here, so ``ready`` lands once."""
    timers: dict[str, ExitStack] = field(default_factory=dict[str, ExitStack])
    """Each held position's per-bar exits, by position id (AD-13)."""
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
        risk_rows: Sequence[Mapping[str, object]] | None = None,
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
        self.stop_port: StopPort | None = None
        """The host's door to ``Runtime.risk_stop``, attached by the node after it hosts the
        unit (AD-12). A unit with none, as in a replay, asks nobody."""
        self.reduce = Decimal(1)
        """The share this step's ``reduce`` rows cut the next entry by, reset every step (AD-12)."""
        self.exit_faults: dict[str, int] = {}
        """Each held position's consecutive bars with no exit able to run (AD-13)."""
        self.close_asked: set[str] = set()
        """The positions whose host was already asked to close them, so the ask fires once."""
        self.warm_up = dict(compiled.warm_up)
        """The bars each of the unit's streams needs before entries."""
        self.warm = max(self.warm_up.values(), default=0)
        """The longest stream warm-up, which the ``warming`` event names."""
        self.slow = {
            s.number.name: SlowState(value=calibrated[s.number.name]) for s in self.plan.slow
        }
        self.slow_rules = {s.number.name: s.block.make(s.params, {}) for s in self.plan.slow}
        self.halt_instances: dict[str, Instance] = {}
        """Each brake row's one instance, by run key: a brake lives on the unit, not a market."""
        settled = self.settled()
        for halt in self.plan.halts:
            self.halt_instances[halt.control.key] = halt.binding.block.make(
                self.params(halt.binding, settled), halt.binding.inputs
            )
        self.control_runner = Runner(
            [halt.control for halt in self.plan.halts], self.halt_instances
        )
        """The unit's brakes, and the scopes a raise stands down (AD-12)."""
        self.risk = Fold(f"unit:{scope_id}")
        """What this unit's brakes say it is doing (AD-18): one fold, fed by the rows its own
        control path answers and by the journal rows a host hands on a restart."""
        self.risk_seeded = bool(risk_rows)
        """Whether a host handed rows to seed the fold. An empty sequence is a reader that found
        none, not the truth that the scope is up, so the snapshot's cache answers instead."""
        if risk_rows:
            self.risk.extend(risk_rows)
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
        state = _Market(
            market_id,
            record,
            {},
            {},
            last_bar_ns=dict.fromkeys(self.plan.streams, -1),
            bars=dict.fromkeys(self.plan.streams, 0),
        )
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
                "last_bar_ns": dict(m.last_bar_ns),
                "bars": dict(m.bars),
                "ready": m.ready,
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
            "risk": self.risk.cached(),
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
        made = self.timer(Side.LONG)
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
        self._load_risk(snapshot)
        markets = cast("Mapping[str, Mapping[str, object]]", snapshot["markets"])
        for m in self.markets:
            saved = markets[m.market_id]
            m.last_bar_ns = {
                stream: int(when)
                for stream, when in cast("Mapping[str, int]", saved["last_bar_ns"]).items()
            }
            m.bars = {
                stream: int(count)
                for stream, count in cast("Mapping[str, int]", saved["bars"]).items()
            }
            m.ready = bool(saved["ready"])
            m.derived = {
                Side(side): {k: Decimal(v) for k, v in values.items()}
                for side, values in cast(
                    "Mapping[str, Mapping[str, str]]", saved["derived"]
                ).items()
            }
            for key, state in cast("Mapping[str, Mapping[str, object]]", saved["blocks"]).items():
                m.instances[key].import_state(state)
            for pid, state in cast("Mapping[str, Mapping[str, object]]", saved["timers"]).items():
                stack = self.timer(Side.LONG)  # shape_gap refused a timers table with no exit cold
                if stack is not None:
                    stack.import_state(state)
                    m.timers[pid] = stack
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

    def _load_risk(self, snapshot: Mapping[str, object]) -> None:
        """Read the fold's cache back when the host handed no rows.

        A cache that does not read as this unit's scope is ignored: the rows are the truth, and a
        cache is a cache.
        """
        if self.risk_seeded:
            return
        cached = Fold.from_cache(snapshot.get("risk"))
        if cached.scope == self.risk.scope:
            self.risk = cached

    def timer(self, side: Side) -> ExitStack | None:
        """The per-bar exits for one position on ``side``, in the compiled order, or ``None`` for
        a unit with no time exit, which layer E warns of (UT-18)."""
        slots: list[ExitSlot] = []
        for e in self.plan.exits:
            if e.use is not ExitUse.PER_BAR:
                continue
            instance = e.binding.block.make(
                self.params(e.binding, self.plan.defaults), e.binding.inputs, side
            )
            slots.append(ExitSlot(f"exit.{e.binding.name}", e.binding.pin, instance))
        return None if not slots else ExitStack(side, slots)


class HostedUnit:
    """One compiled unit hosted for one run or deployment, driven one instant at a time."""

    def __init__(self, core: _Core) -> None:
        self._core = core

    def attach_port(self, port: HostPort) -> None:
        """Hand this unit its host's last fall-through (AD-13). The host attaches it after the
        unit is built, because the port lives on the handler that builds its surfaces."""
        self._core.port = port

    def attach_stop_port(self, port: StopPort) -> None:
        """Hand this unit the door its wait-for-hand rows call (AD-12). Only the node attaches
        one, because only the node has a person to wait for."""
        self._core.stop_port = port

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
            wanted = _amount(answer)
            if isinstance(wanted, _Skip):
                return ended(proposal.row, {}, ("sizer: refuse",), wanted.code, wanted.detail)
            factor = core.reduce
            amount = (
                wanted
                if factor == 1
                else Amount(kind=wanted.kind, value=wanted.value * factor, basis=wanted.basis)
            )
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
        steps: dict[str, Amount] = {"wanted": wanted}
        if factor != 1:
            steps["reduced"] = amount
        steps["approved"] = Amount(kind="quantity", value=converted.quantity, basis=wanted.basis)
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

    def risk_state(self, at: Instant) -> RiskState:
        """What this unit's brakes say it is doing at ``at`` (AD-18).

        One answer for every reader: the fold this unit keeps, read at the clock asked. A fact past
        its limit makes the word UNKNOWN rather than let the fold answer for what it cannot see.
        """
        return self._core.risk.state(at)


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
        self.controls_out: list[ControlEvent] = []
        self.halt_reason: str | None = None
        """Why this step's entries are refused: a brake's own words, or None."""
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
        positions: dict[str, tuple[PositionFacts, ...]] = {}
        seen: dict[str, dict[str, QuoteBar]] = {}
        fresh: dict[str, QuoteBar] = {}
        for m in self.unit.markets:
            given = self.surface(f"own_position:{m.market_id}")
            if not isinstance(given, tuple) or not all(
                isinstance(one, (OwnPosition, PositionFacts)) for one in given
            ):
                return invalid(
                    "own_position",
                    "a position surface answers a tuple of PositionFacts or OwnPositions",
                    market=m.market_id,
                )
            positions[m.market_id] = tuple(facts_from(one) for one in given)
            bars: dict[str, QuoteBar] = {}
            for stream in self.plan.streams:
                given_bar = self.surface(f"bars:{stream}:{m.market_id}")
                if given_bar is None:
                    continue
                if not isinstance(given_bar, QuoteBar):
                    return invalid(
                        "bars", "a bar surface answers a QuoteBar or None", market=m.market_id
                    )
                if given_bar.knowable_at.value_ns > self.instant.value_ns:
                    return invalid(
                        "bars",
                        "a bar knowable after the instant is a look-ahead",
                        market=m.market_id,
                    )
                bars[stream] = given_bar
                if given_bar.knowable_at.value_ns > m.last_bar_ns.get(stream, -1):
                    m.last_bar_ns[stream] = given_bar.knowable_at.value_ns
                    m.bars[stream] = m.bars.get(stream, 0) + 1
                    if stream == self.plan.stream:
                        fresh[m.market_id] = given_bar
            seen[m.market_id] = bars
        if fresh and self.unit.benched and self.unit.clean_bars >= self.unit.fault_clean_bars:
            self.unit.benched = False
        benched = self.unit.benched
        results: dict[str, dict[Side, _Side]] = {}
        for m in self.unit.markets:
            bar = fresh.get(m.market_id)
            if bar is None:
                continue
            try:
                results[m.market_id] = self.update(m, bar, seen[m.market_id])
            except _Fault as fault:
                self.fault(fault.block, FaultPhase.UPDATE)
        self.halt_reason = self.controls(journal, positions)
        for m in self.unit.markets:
            held = positions[m.market_id]
            self.kept(m, held)
            for position in held:
                self.exits(m, position, fresh.get(m.market_id))
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
                self.motion(trades, all(not held for held in positions.values()))
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
                controls=tuple(self.controls_out),
                faults=tuple(self.faults),
            )
        )

    # --- controls --------------------------------------------------------------------

    def controls(
        self, journal: object, positions: Mapping[str, tuple[PositionFacts, ...]]
    ) -> str | None:
        """Run the unit's brakes once this step, before exits and entries (AD-12).

        Each row is fed the facts it declares: the unit's own statistics from its journal, the
        money at risk on each bet the unit holds open, and the account's equity. A row that raises
        records a ``Fault`` with its ``link_fault`` code and stands its scope down. It is a plain
        ``try`` around one block call, so a raise never benches an exit and never reaches one
        (AD-9). A row that fires acts by its own verb: ``flatten`` mints one close per held
        position through the same path the exits use, ``reduce`` cuts the size of the entries this
        step prices, and ``no_new_entries`` refuses them. A ``no_new_entries`` row that waits for
        his hand also asks the host's stop port for the one automatic stop. A row whose own rule
        lets it come back writes a ``restore`` row; a row that waits for his hand answers no
        change. The words this step's entries are refused by come back, or None.
        """
        self.unit.reduce = Decimal(1)
        if not self.unit.halt_instances:
            return None
        trades = cast("Sequence[ClosedTrade]", journal if isinstance(journal, Sequence) else ())
        facts: dict[str, object] = own_facts(trades, self.instant)
        facts["own.open_risk_by_bet_key"] = self.open_risk_by_bet_key(positions)
        equity = getattr(self.surface("account"), "equity", None)
        if isinstance(equity, Decimal):
            facts["account.equity"] = equity
        run = self.unit.control_runner.run(facts)
        for raised in run.raised:
            # a raise is a fault, not a brake: it moves no risk word, and no restore row lifts one
            self.faults.append(Fault(raised.row.pin, FaultPhase.CONTROLS, raised.code))
        for fired in run.fired:
            self.controls_out.append(
                ControlEvent(
                    row=fired.row.name,
                    pin=fired.row.pin,
                    scope=fired.row.scope,
                    kind="would_fire" if fired.shadowed else "fired",
                    verb=fired.answer.verb,
                    factor=fired.answer.factor,
                    code=fired.answer.code,
                    reason=fired.answer.reason,
                )
            )
            if fired.shadowed:  # a would-have refuses nothing, so the scope stays as it is
                continue
            self._fold(fired.row.key, fired.answer.code, fired.answer.verb, fired.answer.reason)
            match fired.answer.verb:
                case Verb.FLATTEN:
                    self.flatten(fired.row.pin, fired.answer.reason, positions)
                case Verb.REDUCE:
                    if fired.answer.factor is not None:
                        self.unit.reduce *= fired.answer.factor
                case _:
                    if fired.row.restore is Restore.HAND and fired.row.scope in ENTRY_SCOPES:
                        self.stop(fired.row.pin, fired.answer.reason)
        for cold in run.cold:
            self.controls_out.append(
                ControlEvent(
                    row=cold.row.name,
                    pin=cold.row.pin,
                    scope=cold.row.scope,
                    kind="cold",
                    verb=cold.row.verb,
                    factor=None,
                    code="cold",
                    reason=f"no {', '.join(cold.missing)} yet",
                )
            )
        for row in run.restored:
            self.unit.risk.add(
                {
                    "kind": "restore",
                    "scope": self.unit.risk.scope,
                    "at": self.instant.value_ns,
                    "id": f"{self.instant.value_ns}:{row.key}:restore",
                    "code": row.code,
                }
            )
        return run.refusal_reason

    def open_risk_by_bet_key(
        self, positions: Mapping[str, tuple[PositionFacts, ...]]
    ) -> Mapping[str, Decimal] | None:
        """The money this unit holds at risk on each bet, by the bet's key (I9, WALKS 3).

        A bet's money is the same figure the account's ``open_risk`` counts: each position's loss
        if its stop fills, at the rate that converts its quote into the account's currency. Two
        positions on one bet key add into one entry, so a row that caps one bet reads one number.
        ``None`` when any position cannot be priced, because a partial sum reads as less risk
        than the unit carries. This is the unit's own view: the same key crosses units, and the
        group ledger is what adds their positions together (WALKS 3.4).
        """
        account = self.surface("account")
        stakes: dict[str, list[Stake]] = {}
        for m in self.unit.markets:
            rate = rate_used(m.record, account, self.instant) if isinstance(account, Account) else None
            for position in positions[m.market_id]:
                if not self.mine(position):
                    continue
                stakes.setdefault(bet_key(self.unit.compiled.unit.family_id, m.market_id), []).append(
                    Stake(
                        position.entry_price,
                        position.stop,
                        position.quantity,
                        m.record.value_per_point,
                        rate,
                    )
                )
        found: dict[str, Decimal] = {}
        for key, group in stakes.items():
            money = open_risk(group)
            if money is None:
                return None
            found[key] = money
        return MappingProxyType(found)

    def flatten(
        self,
        pin: str,
        reason: str,
        positions: Mapping[str, tuple[PositionFacts, ...]],
    ) -> None:
        """Close every position this unit opened, through its own exit path (AD-12).

        The close is minted by the same helper a per-bar exit uses, so it carries the unit's
        decision row and its ``control_flatten`` reason, and the exits pass this step sees the
        position already closed. Nothing refuses it: this is the unit's exit path.
        """
        why = f"{pin} flattens the position: {reason}"
        for m in self.unit.markets:
            for position in positions[m.market_id]:
                if not self.mine(position) or position.position_id in m.exited:
                    continue
                self.close_position(m, position, CONTROL_FLATTEN, why)

    def stop(self, pin: str, reason: str) -> None:
        """Ask the host for the stop a row that waits for his hand fires (AD-12)."""
        port = self.unit.stop_port
        if port is not None:
            port.risk_stop(pin, reason)

    def mine(self, position: PositionFacts) -> bool:
        """Whether this unit version opened the position (AD-3)."""
        version = self.unit.compiled
        return position.opened_by in (
            version.logic_fingerprint,
            version.compiled_fingerprint,
        )

    def close_position(self, m: _Market, position: PositionFacts, code: str, why: str) -> None:
        """Mint one full close through the unit's own exit path, and mark it closed this step."""
        m.exited.add(position.position_id)
        row = self.decision(m, position.side, "taken", (), why)
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
                "reason_code": {"code": code, "book_family": "unit"},
                "decision_row_id": row,
            }
        )

    def _fold(self, key: str, code: str, verb: Verb, reason: str) -> None:
        """Hand the fold the row this step's brake answer becomes (AD-12, AD-18).

        The row is the same shape a host's journal writes, so the unit's own answer and a restart's
        reader give the fold the same thing.
        """
        self.unit.risk.add(
            {
                "kind": "risk_event",
                "scope": self.unit.risk.scope,
                "at": self.instant.value_ns,
                "id": f"{self.instant.value_ns}:{key}:{code}",
                "code": code,
                "verb": verb.value,
                "reason": reason,
            }
        )

    # --- blocks ------------------------------------------------------------------

    def update(self, m: _Market, bar: QuoteBar, bars: Mapping[str, QuoteBar]) -> dict[Side, _Side]:
        if m.bars.get(self.plan.stream) == 1:
            self.events.append(StateEvent("warming", m.market_id, f"{self.unit.warm} bars"))
        if not m.ready and all(
            m.bars.get(stream, 0) >= self.unit.warm_up.get(stream, 0)
            for stream in self.plan.streams
        ):
            m.ready = True
            self.events.append(StateEvent("ready", m.market_id))
        m.in_force = {plan.side: self.unit.numbers(m, plan.side) for plan in self.plan.sides}
        sides = {
            plan.side: self.side(m, plan, bars, m.in_force[plan.side]) for plan in self.plan.sides
        }
        for side in (Side.LONG, Side.SHORT):
            series = bar.bid.fields() if side is Side.LONG else bar.ask.fields()
            for e in self.plan.exits:
                key = f"{side.value}.{e.binding.key}"
                if e.use is not ExitUse.STOP or key not in m.instances:
                    continue
                evidence = {"series": series} | self.unit.params(e.binding, m.in_force[side])
                _answered(e.binding.pin, m.instances[key], evidence)
        return sides

    def side(
        self,
        m: _Market,
        plan: SidePlan,
        bars: Mapping[str, QuoteBar],
        numbers: Mapping[str, Decimal],
    ) -> _Side:
        outputs: dict[str, object] = {}
        trail: list[SlotOutput] = []
        held: dict[str, tuple[bool, str]] = {}
        order: EntryOrder | None = None

        def resolve(ref: str) -> object:
            stream, _, part = ref.partition(".")
            bar = bars.get(stream)
            if bar is not None:
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
        drivers = tuple(
            s.name
            for s in plan.slots
            if s.role is not Role.ENTRY_ORDER and held[s.name][0] and s.has_conditions
        )
        return _Side(not failing, trigger, "; ".join(failing), tuple(trail), order, drivers)

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

    def exits(self, m: _Market, position: PositionFacts, bar: QuoteBar | None) -> None:
        """This market's per-bar exits on one position, on the bar of the quote that closes it.

        A position is this unit's when its key is this version's logic half, which a risk edit
        leaves alone, or this compile's own fingerprint, which a host that pins one compile
        stamps (AD-3). Either names this unit version, so another version's position is never
        closed. Every exit runs on the closing side's bar, the bid for a long and the ask for a
        short, so a short's stop feels the spread (AD-13). A raising exit block is skipped with a
        ``Fault`` and the next exit still runs; no exit able to run for ``exit_fault_bars`` bars
        asks the host's ``close_scope`` port to close the position (AD-13, AD-23 step 4). One
        action runs: the chosen one, by rank and then by the order the document wrote the exits
        in. A step where this market has no new bar leaves that count alone, so a step of the
        other market's bar never resets it. Each position has its own stack and its own count, so
        the first of two positions to be reached closes only itself.
        """
        if not self.mine(position) or position.position_id in m.exited:
            self.unit.exit_faults.pop(position.position_id, None)
            return
        if bar is None:
            return
        stack = m.timers.get(position.position_id)
        if stack is None or stack.side is not position.side:
            built = self.unit.timer(position.side)
            if built is None:
                return
            if stack is not None:  # a restore built the table before it knew the side
                built.import_state(stack.export_state())
            m.timers[position.position_id] = stack = built
        series = bar.bid.fields() if position.side is Side.LONG else bar.ask.fields()
        answers: list[ExitAnswer] = []
        raised: list[str] = []
        ran = 0
        for plan in self.plan.exits:
            if plan.use is not ExitUse.PER_BAR:
                continue
            evidence = position.evidence(
                self.instant,
                series,
                self.unit.params(plan.binding, m.in_force.get(position.side, {})),
            )
            try:
                raw = stack.instance(plan.binding.key).update(evidence)
                action = answer(plan.binding.pin, raw)
            except Exception:  # an exit's raise is this bar's Fault, never a step refusal (AD-13)
                raised.append(plan.binding.pin)
                continue
            ran += 1
            if action is not None:
                answers.append(
                    ExitAnswer(
                        plan.binding.pin,
                        plan.binding.key,
                        action,
                        self.close_words(plan.binding.pin, raw, action),
                    )
                )
        for pin in raised:
            self.fault(pin, FaultPhase.EXIT)
        if raised and not ran:
            self.no_exit_ran(position)
        else:
            self.unit.exit_faults.pop(position.position_id, None)
        winner = chosen(answers)
        if winner is None or winner.action.kind != "close_full":
            return
        self.close_position(m, position, winner.action.reason_code, winner.detail)

    def kept(self, m: _Market, held: Sequence[PositionFacts]) -> None:
        """Forget the exits of every position this market no longer holds (AD-13).

        A position closes at the venue or by this unit's own answer, and the host stops
        reporting it on a later step. Its per-bar exits went with it, and the identity is kept
        out of ``exited`` so the same id never carries a stale close into a new position.
        """
        live = {one.position_id for one in held}
        for gone in [pid for pid in m.timers if pid not in live]:
            del m.timers[gone]
            m.exited.discard(gone)

    def close_words(self, pin: str, raw: object, action: ExitAction) -> str:
        """The one sentence a close row carries. A per-bar exit that answers the old way keeps
        the shipped time exit's sentence; one that answers an ``ExitAction`` names itself."""
        if isinstance(raw, Signal):
            return f"time exit after {_text(raw)} bars"
        return f"{pin} closes the position: {action.reason_code}"

    def no_exit_ran(self, position: PositionFacts) -> None:
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
        positions: tuple[PositionFacts, ...],
    ) -> None:
        signalled = [s for s, r in sides.items() if r.holds]
        limit = self.plan.position_limit
        for side, result in sides.items():
            if not result.holds:
                if result.trigger_held:
                    self.decision(m, side, "no_signal", result.trail, f"near miss, {result.reason}")
                elif self.unit.trace is TraceLevel.EVERY_BAR:
                    self.decision(m, side, "no_signal", result.trail, result.reason)
                continue
            if self.halt_reason is not None:
                self.decision(m, side, "suppressed", result.trail, self.halt_reason)
                continue
            if any(
                m.bars.get(stream, 0) < self.unit.warm_up.get(stream, 0)
                for stream in self.plan.streams
            ):
                self.decision(m, side, "suppressed_warming", result.trail, "warming up")
            elif len(signalled) > 1:
                self.decision(m, side, "dropped_opposite", result.trail, "both sides signalled")
            elif len(positions) >= limit:
                self.decision(
                    m,
                    side,
                    "suppressed_limit",
                    result.trail,
                    f"{len(positions)} of {limit} positions are open",
                )
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
                    "bet_key": bet_key(compiled.unit.family_id, m.market_id),
                    "driver_tags": list(result.drivers),
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
        for stream in compiled.plan.streams:
            keys.add(f"bars:{stream}:{market.market_id}")
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
    risk_rows: Sequence[Mapping[str, object]] | None,
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
            risk_rows=risk_rows,
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
    risk_rows: Sequence[Mapping[str, object]] | None = (),
) -> Result[HostedUnit]:
    """Host a compiled unit. ``assignment`` holds the calibrated values the run starts from
    (the unit's defaults when ``None``); ``scope_id`` is the QMB run id or the deployment id;
    ``fault_clean_bars`` is the clean bars a faulted unit waits before its entries return;
    ``exit_fault_bars`` is the bars its exits may fail to run before ``port`` closes a position;
    ``risk_rows`` are the journal rows the host already holds, which seed the fold."""
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
        risk_rows,
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
    risk_rows: Sequence[Mapping[str, object]] | None = None,
) -> Result[HostedUnit]:
    """Resume from ``snapshot``. A snapshot of another state schema, compiled fingerprint or
    interpreter, or one whose markets, blocks, slow numbers or fields differ in shape from
    this unit's own snapshot, starts the unit cold, and its first step carries a
    ``cold_start`` event with the reason, so a restart never silently changes what the unit
    does. A block's ``export_state`` keeps the same keys for the whole run.

    ``risk_rows`` are the journal rows the host read back, which are the truth for the fold; when
    the host hands none, the snapshot's cache answers instead."""
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
        risk_rows,
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
