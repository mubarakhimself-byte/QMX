"""The unit document ``qmx.unit/1`` as one typed model (Part A AD-102, CONTRACTS.md section 1).

These frozen dataclasses are the only definition of the document. The JSON Schema in
``qmx.unit.1.schema.json`` and the layer A parser are both derived from them, so the two
cannot drift. The model holds shape only: completeness (a market, a trigger, an exit set,
a sizer) is layer E, and identity and cross-field rules are layers B and C.

Every decimal number arrives as a decimal string and is held as an exact ``Decimal``.
A field's JSON key is its Python name unless its metadata names ``key``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from qmf.risk.controls import Verb

__all__ = [
    "AbsentInputs",
    "Authority",
    "Bar",
    "BarKind",
    "Binding",
    "Cadence",
    "CadenceAt",
    "Cautious",
    "ClaimCard",
    "Combiner",
    "CombinerKind",
    "ContextNeeds",
    "ControlBinding",
    "Direction",
    "EntryRef",
    "Fallback",
    "Guard",
    "Lineage",
    "LineageParent",
    "Marker",
    "Market",
    "Measure",
    "MirrorSide",
    "Motion",
    "MotionMode",
    "Need",
    "NumberKind",
    "NumberParam",
    "NumberSpec",
    "Origin",
    "Pin",
    "PlainPython",
    "PositionLimit",
    "Price",
    "Range",
    "Read",
    "RecipeRef",
    "Role",
    "Roll",
    "RollRule",
    "RootRef",
    "Routes",
    "Scope",
    "ScopedBinding",
    "Session",
    "Side",
    "Slot",
    "SlotsSide",
    "Source",
    "StageMove",
    "StageRow",
    "Stages",
    "Stream",
    "StreamInput",
    "SymbolRef",
    "Unit",
    "ValueParam",
    "Window",
]


class Marker(StrEnum):
    UNIT_1 = "qmx.unit/1"


class Direction(StrEnum):
    LONG = "long"
    SHORT = "short"
    BOTH = "both"


class Side(StrEnum):
    LONG = "long"
    SHORT = "short"


class Role(StrEnum):
    """AD-104's closed-and-addable slot vocabulary, socket roles last."""

    CONTEXT = "context"
    LOCATION = "location"
    SETUP = "setup"
    TRIGGER = "trigger"
    CONFIRMATION = "confirmation"
    FILTER = "filter"
    VETO = "veto"
    ENTRY_ORDER = "entry_order"
    INVALIDATION = "invalidation"
    REGIME_DETECTOR = "regime_detector"
    SIZING_MODIFIER = "sizing_modifier"
    ARMING = "arming"
    TIMEOUT = "timeout"
    COOLDOWN = "cooldown"
    RE_ENTRY = "re_entry"
    EXIT = "exit"
    SIZER = "sizer"
    HALT = "halt"


class CombinerKind(StrEnum):
    ALL = "all"
    ANY = "any"
    K_OF_N = "k_of_n"
    WEIGHTED = "weighted"
    SEQUENCE = "sequence"
    VETO = "veto"


class AbsentInputs(StrEnum):
    NO_SIGNAL = "no_signal"
    TREAT_AS_FALSE = "treat_as_false"


class Scope(StrEnum):
    POSITION = "position"
    UNIT = "unit"
    ACCOUNT = "account"


class BarKind(StrEnum):
    TIME = "time"
    TICK = "tick"
    RANGE = "range"
    VOLUME = "volume"


class StreamInput(StrEnum):
    CLOSED_BARS = "closed_bars"
    QUOTES = "quotes"
    TICKS = "ticks"


class Price(StrEnum):
    BID_ASK = "bid_ask"
    MID = "mid"
    LAST = "last"


class RollRule(StrEnum):
    CALENDAR = "calendar"
    VOLUME = "volume"
    OPEN_INTEREST = "open_interest"


class Fallback(StrEnum):
    COMPUTE_HERE = "compute_here"
    TREAT_AS_ABSENT = "treat_as_absent"
    NO_NEW_ENTRIES = "no_new_entries"


class NumberKind(StrEnum):
    FIXED = "fixed"
    CALIBRATED = "calibrated"
    DERIVED = "derived"


class Measure(StrEnum):
    """QML's measures; A3 maps each to one QMF ``UnitKind`` (CONTRACTS.md section 2.2)."""

    PRICE_DISTANCE = "price_distance"
    TICKS = "ticks"
    PIPS = "pips"
    ATR_MULTIPLE = "atr_multiple"
    PERCENT = "percent"
    RATIO = "ratio"
    PROBABILITY = "probability"
    BARS = "bars"
    COUNT = "count"
    SECONDS = "seconds"
    MONEY = "money"
    R = "r"
    LOTS = "lots"
    CATEGORY = "category"
    FLAG = "flag"


class MotionMode(StrEnum):
    FIXED = "fixed"
    SCALED = "scaled"
    PERCENTILE_OF_OWN_HISTORY = "percentile_of_own_history"
    STATE_TABLE = "state_table"
    SHRINK_FROM_OWN_TRADES = "shrink_from_own_trades"
    LEARNED = "learned"


class CadenceAt(StrEnum):
    MARKET_DAY_CLOSE = "market_day_close"
    SESSION_CLOSE = "session_close"


class StageMove(StrEnum):
    """How a stage moves, by its own rule or by his card (AD-7)."""

    RULE = "rule"
    CARD = "card"


class Authority(StrEnum):
    OFF = "off"
    MOTION_INSIDE_RANGE = "motion_inside_range"
    AT_ANCHOR = "at_anchor"


class Cautious(StrEnum):
    """The direction a move may take a number: toward less risk, toward more, or neither."""

    DOWN = "down"
    UP = "up"
    HOLD = "hold"


class Origin(StrEnum):
    SOURCE_STATED = "source_stated"
    PUBLISHED_CONVENTION = "published_convention"
    STRATS_STANDARDIZED = "strats_standardized"
    INFERRED = "inferred"
    BUILDER_CHOSEN = "builder_chosen"
    UNRESOLVED = "unresolved"
    FOUND_BY_REPLAY = "found_by_replay"
    PLACEHOLDER = "placeholder"  # mock-data-scan: allow (the risk session's label, AD-116)


@dataclass(frozen=True)
class EntryRef:
    """``entry_id@version``: a dictionary entry at one version."""

    entry_id: str
    version: int

    def __str__(self) -> str:
        return f"{self.entry_id}@{self.version}"


@dataclass(frozen=True)
class Source:
    source_ref: str
    locator: str
    dated: str
    quote: str | None = None


@dataclass(frozen=True)
class ClaimCard:
    idea: str
    sources: tuple[Source, ...]
    written_at: str
    claimed_context: str | None = None


@dataclass(frozen=True)
class LineageParent:
    unit_id: str
    version_ref: str
    edit_labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class Lineage:
    parents: tuple[LineageParent, ...] = ()
    rewritten_from: str | None = None


@dataclass(frozen=True)
class SymbolRef:
    venue: str
    symbol: str


@dataclass(frozen=True)
class RootRef:
    """A future's root; the contract months come from the instrument records (R1-C-10)."""

    venue: str
    root: str


@dataclass(frozen=True)
class Roll:
    rule: RollRule
    days_before_expiry: int | None = field(default=None, metadata={"minimum": 0})


@dataclass(frozen=True)
class Market:
    market_id: str
    instrument_ref: SymbolRef | RootRef
    roll: Roll | None = None
    settings: Mapping[str, Decimal] = field(default_factory=dict[str, Decimal])
    settings_record: str | None = None


@dataclass(frozen=True)
class Bar:
    kind: BarKind
    size: Decimal


@dataclass(frozen=True)
class Stream:
    name: str
    market: str
    bar: Bar
    price: Price
    input: StreamInput = StreamInput.CLOSED_BARS
    derived_from: str | None = None


_CLOCK = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"


@dataclass(frozen=True)
class Window:
    start: str = field(metadata={"key": "from", "pattern": _CLOCK})
    end: str = field(metadata={"key": "to", "pattern": _CLOCK})


@dataclass(frozen=True)
class Session:
    name: str
    calendar_ref: str
    zone: str
    windows: tuple[Window, ...]


@dataclass(frozen=True)
class PositionLimit:
    per_instrument: int = field(default=1, metadata={"minimum": 1})


@dataclass(frozen=True)
class NumberParam:
    number: str


@dataclass(frozen=True)
class ValueParam:
    value: Decimal


@dataclass(frozen=True)
class Binding:
    name: str
    block: EntryRef
    params: Mapping[str, NumberParam | ValueParam]
    inputs: Mapping[str, str]


@dataclass(frozen=True)
class ScopedBinding(Binding):
    """An exit or halt binding, which names the scope it acts on."""

    scope: Scope


@dataclass(frozen=True)
class Combiner:
    kind: CombinerKind
    when_inputs_absent: AbsentInputs
    k: int | None = field(default=None, metadata={"minimum": 1})
    weights: Mapping[str, Decimal] = field(default_factory=dict[str, Decimal])
    open: Decimal | None = None
    close: Decimal | None = None
    within_bars: int | None = field(default=None, metadata={"minimum": 1})


@dataclass(frozen=True)
class Slot:
    role: Role
    bindings: tuple[Binding, ...]
    combiner: Combiner


@dataclass(frozen=True)
class SlotsSide:
    slots: Mapping[str, Slot]


@dataclass(frozen=True)
class MirrorSide:
    mirror_of: Side


@dataclass(frozen=True)
class Logic:
    long: SlotsSide | MirrorSide | None = None
    short: SlotsSide | MirrorSide | None = None


@dataclass(frozen=True)
class ControlBinding(ScopedBinding):
    """A brake's row (AD-12): a scoped binding, the verb it runs when it fires, and whether it is
    only in shadow. The rest of a control row is compiled from the block's face (``reads``) or
    defaulted (``on_fire``, ``restore``, ``until_n``, ``enabled``), so the document states only
    what a person chose."""

    verb: Verb = Verb.NO_NEW_ENTRIES
    shadow: bool = False


@dataclass(frozen=True)
class Halts:
    position: tuple[ControlBinding, ...] = ()
    unit: tuple[ControlBinding, ...] = ()
    account: tuple[ControlBinding, ...] = ()


@dataclass(frozen=True)
class Read:
    reading: EntryRef
    market: str
    fallback: Fallback
    stale_after_s: int = field(metadata={"minimum": 0})


@dataclass(frozen=True)
class Range:
    min: Decimal
    max: Decimal
    step: Decimal


@dataclass(frozen=True)
class Guard:
    """What a number does after its moves trip: return to the last value, then stop moving.

    ``revert_after`` counts the trips that take the number back to the value it held before the
    first move of the run. ``freeze_after`` counts the trips that stop it moving at all until a
    person writes a new version. Both are counts of trips, so neither is ever zero.
    """

    revert_after: int = field(metadata={"minimum": 1})
    freeze_after: int = field(metadata={"minimum": 1})


@dataclass(frozen=True)
class Cadence:
    every_closed_trades: int | None = field(default=None, metadata={"minimum": 1})
    at: CadenceAt | None = None


@dataclass(frozen=True)
class Motion:
    mode: MotionMode
    source: str | None = None
    cadence: Cadence | None = None
    min_count: int | None = field(default=None, metadata={"minimum": 0})
    shrink_k: int | None = field(default=None, metadata={"minimum": 0})
    step_limit: int | None = field(default=None, metadata={"minimum": 1})
    rule: EntryRef | None = None
    rule_params: Mapping[str, str] = field(default_factory=dict[str, str])


@dataclass(frozen=True)
class NumberSpec:
    """One number of the unit (AD-103). ``default`` is a decimal string, or a category or
    flag value; which one depends on ``measure`` and is checked at layer C.

    The four answers AD-14 asks of every number sit here: ``derivation`` says where the value
    comes from (a rule block's pin, or a fact's name), ``authority`` and ``never_self_tune`` say
    who may move it, ``owner`` names who argues it, and ``reason`` says why it holds this value
    rather than another. A number that states none of them is an old document and reads: layer C
    then names the reason it lacks.
    """

    kind: NumberKind
    measure: Measure
    default: str
    motion: Motion
    authority: Authority
    origin: Origin
    derivation: str | None = None
    owner: str = ""
    reason: str = ""
    cautious: Cautious = Cautious.HOLD
    guard: Guard | None = None
    never_self_tune: bool = False
    stage_values: Mapping[str, str] = field(default_factory=dict[str, str])
    range: Range | None = None
    applies_to_open_positions: bool = False


@dataclass(frozen=True)
class Need:
    word: str
    reading: EntryRef | None = None


@dataclass(frozen=True)
class ContextNeeds:
    require: tuple[Need, ...] = ()
    warn: tuple[Need, ...] = ()
    block: tuple[Need, ...] = ()


@dataclass(frozen=True)
class Routes:
    data: Mapping[str, str] = field(default_factory=dict[str, str])
    execution: str | None = None


@dataclass(frozen=True)
class Pin:
    entry_id: str
    version: int = field(metadata={"minimum": 1})
    fingerprint: str


@dataclass(frozen=True)
class PlainPython:
    block: EntryRef


@dataclass(frozen=True)
class RecipeRef:
    """The pod stamp a document carries: what filled its risk half, and what that displaced."""

    pod_id: str
    version: int = field(metadata={"minimum": 1})
    hash: str
    displaced: tuple[str, ...] = ()


@dataclass(frozen=True)
class StageRow:
    """What one stage puts in force: a sizer, modifiers, control rows and number values."""

    sizer: Binding | None = None
    modifiers: tuple[Binding, ...] = ()
    controls: tuple[ScopedBinding, ...] = ()
    numbers: Mapping[str, Decimal] = field(default_factory=dict[str, Decimal])


@dataclass(frozen=True)
class Stages:
    """A risk half's stages (AD-7): the selector, its anchor, and the rows in force."""

    selector: str
    anchor: CadenceAt
    hysteresis: Decimal
    move_up: StageMove
    move_down: StageMove
    rows: Mapping[str, StageRow]


@dataclass(frozen=True)
class Unit:
    schema: Marker
    unit_id: str
    family_id: str
    claim_card: ClaimCard
    markets: tuple[Market, ...]
    streams: tuple[Stream, ...]
    direction: Direction
    logic: Logic
    exit_set: tuple[ScopedBinding, ...]
    halts: Halts
    reads: tuple[Read, ...]
    numbers: Mapping[str, NumberSpec]
    pins: tuple[Pin, ...]
    title: str | None = None
    lineage: Lineage | None = None
    sessions: tuple[Session, ...] = ()
    position_limit: PositionLimit | None = None
    sizer: Binding | None = None
    context_needs: ContextNeeds | None = None
    routes: Routes | None = None
    baseline: str | None = None
    plain_python: PlainPython | None = None
    modifiers: tuple[Binding, ...] = ()
    gates: tuple[Binding, ...] = ()
    tolerations: tuple[str, ...] = ()
    stages: Stages | None = None
    risk_locks: tuple[str, ...] = ()
    recipe: RecipeRef | None = None
    home_markets: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
