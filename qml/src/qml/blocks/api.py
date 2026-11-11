"""The block protocol: what a block module exports and what its entry face declares (AD-109).

A block's source is one ``block.py`` that exports ``BLOCK``. ``BLOCK.make(params, inputs,
side)`` returns an instance; the instance takes one instant's evidence at a time through
``update`` and returns its output, or ``None`` while the output is missing (warm-up values
are missing, never zero). An instance's retained observations never exceed its
``state_bound`` whatever the history length (QML-04), and ``export_state`` and
``import_state`` carry it across a restart.

The block's machine face lives beside it in ``entry.json`` and is read by ``parse_entry``.
It names every input port, the output, and each parameter with its measure, so the checker
can match a number's measure to the port it binds to (layer C).

Sides. A block whose face declares ``mirroring: supported`` reads ``side`` and acts as the
mirror image on the short side (above becomes below, a floor becomes a ceiling). A unit's
side written as ``{"mirror_of": ...}`` reuses the other side's bindings and numbers as they
are, so a side whose numbers differ (the dummy's ``rsi_low`` against ``rsi_high``) states
its slots explicitly with the same blocks.

Values that leave a block through a port are exact ``Decimal`` values quantised to
``port_quantum_significant_digits``; a block may compute in floats inside.

The risk socket (Part A AD-116, CONTRACTS.md section 4.3) is five slots:
``SizerInstance``, ``ModifierInstance``, ``ExitInstance``, ``HaltInstance`` and the host's
``CrossUnitHook``. Today's blocks in them are placeholders the risk session replaces;
``qml/tests/test_socket_contracts.py`` holds the contract every block in a slot must pass.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, InvalidOperation
from enum import StrEnum
from typing import TYPE_CHECKING, Final, Literal, Protocol, cast, runtime_checkable

from qml.unit.model import Measure, Scope, Side

if TYPE_CHECKING:
    from qmf.risk.unit_intent import UnitIntent

    from qml.protocol.unit import OwnPosition

__all__ = [
    "PASS_EVERY_ORDER",
    "PORT_QUANTUM_SIGNIFICANT_DIGITS",
    "Amount",
    "Block",
    "CrossUnitHook",
    "EntryFace",
    "EntryOrder",
    "ExitAction",
    "ExitInstance",
    "FaceProblem",
    "Factor",
    "Halt",
    "HaltAction",
    "HaltInstance",
    "Instance",
    "Mirroring",
    "ModifierInstance",
    "Output",
    "OutputType",
    "Parameter",
    "Port",
    "Refuse",
    "Settle",
    "Side",
    "Signal",
    "Size",
    "SizerInstance",
    "Skip",
    "parse_entry",
    "quantise",
]

PORT_QUANTUM_SIGNIFICANT_DIGITS: Final[int] = 12
"""Starting default of the ``port_quantum_significant_digits`` setting (CONTRACTS.md section 9)."""

ENTRY_SCHEMA: Final[str] = "qmx.entry/1"


def quantise(value: float | Decimal, digits: int = PORT_QUANTUM_SIGNIFICANT_DIGITS) -> Decimal:
    """The exact value a port carries: ``digits`` significant digits, half to even."""
    context = Context(prec=digits, rounding=ROUND_HALF_EVEN)
    if isinstance(value, Decimal):
        return context.plus(value)
    return context.create_decimal_from_float(value)


@dataclass(frozen=True, slots=True)
class Signal:
    """A context, trigger or exit output: whether it holds now, and the value it read."""

    state: bool
    value: Decimal | None = None


@dataclass(frozen=True, slots=True)
class EntryOrder:
    """How an entry is placed: ``kind`` (``market``) at ``at`` (``next_open``)."""

    kind: str
    at: str


@dataclass(frozen=True, slots=True)
class Size:
    """A sizer's answer: lots rounded to the market's lot step, or a skip with its reason."""

    lots: Decimal | None
    skip_reason: str | None = None


@dataclass(frozen=True, slots=True)
class Amount:
    """A sizer's answer in the unit it chose: money at risk, notional, or quantity.

    ``value`` is exact in that unit, and ``basis`` names what R is measured against (today
    ``gross_at_stop``). The older :class:`Size` states a quantity, so it reads as
    ``Amount(kind="quantity", ...)`` and skips the one converter.
    """

    kind: Literal["money_at_risk", "notional", "quantity"]
    value: Decimal
    basis: str


@dataclass(frozen=True, slots=True)
class Skip:
    """A sizer's refusal of one entry, with the reason the unit records."""

    reason: str


@dataclass(frozen=True, slots=True)
class Factor:
    """A modifier's answer: a multiplier inside the range it declares, with its reason.

    ``range`` is the range the block declares for its own answer, so a reader knows what the factor
    was allowed to be. A factor outside it is refused by name and the modifier reads neutral, which
    is what ``None`` already means: a modifier with no answer never raises or cuts a size by
    itself.
    """

    value: Decimal
    range: tuple[Decimal, Decimal]
    reason: str


@dataclass(frozen=True, slots=True)
class ExitAction:
    """An exit's answer: close the whole position, close part of it, or move its protection.

    ``kind`` is what the unit does with the answer. ``close_full`` closes the position,
    ``close_partial`` closes ``fraction`` of it, and ``amend_protection`` moves the stop to
    ``new_stop``, which may only tighten. ``target_position`` is reserved for the venue-resting
    target and no host runs it yet. ``reason_code`` is the word the close row and the receipt
    carry, so a close always says why it closed.
    """

    kind: Literal["close_full", "close_partial", "amend_protection", "target_position"]
    reason_code: str
    fraction: Decimal | None = None
    new_stop: Decimal | None = None


class Instance(Protocol):
    """One running block, made for one binding on one side."""

    @property
    def warm_up_bars(self) -> int:
        """Updates before the output stops being missing for a reason other than data."""
        ...

    @property
    def state_bound(self) -> int:
        """The most observations the instance ever retains."""
        ...

    def update(self, evidence: Mapping[str, object]) -> object | None:
        """Take this instant's evidence and return the output, ``None`` while missing.

        ``evidence`` holds the value of each input port by port name and, for a parameter
        bound to a number that moves, that number's current value under the parameter name.
        """
        ...

    def retained(self) -> int:
        """Observations held right now; never above ``state_bound``."""
        ...

    def export_state(self) -> Mapping[str, object]: ...

    def import_state(self, state: Mapping[str, object]) -> None: ...


@runtime_checkable
class Block(Protocol):
    """What a block module exports as ``BLOCK``."""

    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> Instance: ...


class SizerInstance(Instance, Protocol):
    """The sizer slot. The host passes ``equity``, ``entry_price`` and ``stop_price`` as exact
    ``Decimal`` values, ``record`` as the market's ``InstrumentRecord``, and the sizer's own
    parameters, each under its parameter name, so a number that moves reaches the answer.

    The answer is an ``Amount`` in the unit the sizer chose: the one converter spells the venue's
    quantity, rounding down to the lot step with the residue kept. ``Size`` still states a
    quantity in lots, and skips the converter exactly as it always did. ``Skip`` refuses one entry
    with the reason the unit records, and ``None`` means the evidence was not there yet.
    """

    def update(self, evidence: Mapping[str, object]) -> Amount | Skip | Size | None: ...


class ModifierInstance(Instance, Protocol):
    """The sizing-modifier slot (AD-11). A modifier reads the same evidence a sizer reads, plus
    the parameters its row binds, and answers a :class:`Factor` inside the range it declares, or
    ``None`` when it has no answer yet. The unit multiplies the factors in the order the document
    writes them and prints each one on the receipt, with its range, its reason and its fail mode.
    """

    def update(self, evidence: Mapping[str, object]) -> Factor | None: ...


class ExitInstance(Instance, Protocol):
    """An exit slot. A stop reads ``series`` bars and answers its price level; a target reads
    ``entry_price`` and ``stop_price`` and answers its price level; a per-bar exit reads the
    position's facts, the bar of the quote that closes it under ``series`` and that bar's close
    under ``clock``, and answers an ``ExitAction`` or a ``Signal`` that closes the position while
    it holds. Levels are exact ``Decimal`` prices."""

    def update(self, evidence: Mapping[str, object]) -> Decimal | Signal | ExitAction | None: ...


class HaltAction(StrEnum):
    """What a halt would do at its scope: stop new entries, reduce the next size, or flatten."""

    NO_NEW_ENTRIES = "no_new_entries"
    REDUCE = "reduce"
    FLATTEN = "flatten"


@dataclass(frozen=True, slots=True)
class Halt:
    """A halt that holds: what it does, at which scope, and why.

    ``factor`` is the share a ``reduce`` halt cuts the next entry by, as ``0.5`` for half. A
    halt of any other action leaves it out, and the row's own verb decides what runs.
    """

    action: HaltAction
    scope: Scope
    reason: str
    factor: Decimal | None = None


class HaltInstance(Instance, Protocol):
    """A halt slot, read from unit and account statistics and his limits. ``None`` is the
    contract's ``none``: nothing is halted. The unit runs its row in the control runner, which
    refuses entries at the row's scope and never reaches an exit."""

    def update(self, evidence: Mapping[str, object]) -> Halt | None: ...


@dataclass(frozen=True, slots=True)
class Refuse:
    """The cross-unit hook's refusal of one order, with its reason."""

    reason: str


class CrossUnitHook(Protocol):
    """What the host calls before every order, across every unit on the account. ``None``
    passes the order. No host calls it yet."""

    def before_order(
        self,
        intent: UnitIntent,
        open_positions: Sequence[OwnPosition],
        dispersion: Decimal | None,
    ) -> Refuse | None: ...


class _PassEveryOrder:
    def before_order(
        self,
        intent: UnitIntent,
        open_positions: Sequence[OwnPosition],
        dispersion: Decimal | None,
    ) -> Refuse | None:
        return None


PASS_EVERY_ORDER: Final[CrossUnitHook] = _PassEveryOrder()
"""The cross-unit hook's placeholder, owned by the risk session: every order passes."""


class OutputType(StrEnum):
    EVENT = "event"
    LEVEL = "level"
    SERIES = "series"
    STATE = "state"
    PROBABILITY = "probability"
    QUANTITY = "quantity"
    AMOUNT = "amount"
    FACTOR = "factor"
    EXIT_ACTION = "exit_action"
    CALENDAR_STATE = "calendar_state"
    ENTRY_ORDER = "entry_order"


class Mirroring(StrEnum):
    SUPPORTED = "supported"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class Port:
    """An input port. ``stream_kind`` says where the value comes from: a ``series`` or
    ``bars`` binding input, or ``position``, ``account``, ``record`` and ``trades`` facts the
    host supplies. ``measure`` is a QML measure, or ``price`` for a price level of the market."""

    port: str
    stream_kind: str
    measure: str | None
    data_level: int | None


@dataclass(frozen=True, slots=True)
class Output:
    type: OutputType
    measure: str | None


@dataclass(frozen=True, slots=True)
class Parameter:
    """A parameter port; a binding feeds it a number whose measure must equal this one."""

    name: str
    measure: Measure


@dataclass(frozen=True, slots=True)
class Settle:
    """The recursive-settle length found at ``params`` within ``tolerance`` (QML-03). ``scales_by``
    names the parameter the length grows with, so ``bars / params[scales_by]`` is its bars per
    period; a block with no such parameter leaves it None and settles at ``bars`` whatever it is
    given."""

    params: Mapping[str, Decimal]
    bars: int
    tolerance: Decimal
    scales_by: str | None = None

    def bars_at(self, params: Mapping[str, Decimal]) -> int:
        """The settle length at a binding's ``params``, rounded up to a whole bar."""
        value = None if self.scales_by is None else params.get(self.scales_by)
        if self.scales_by is None or value is None:
            return self.bars
        return math.ceil(Decimal(self.bars) * value / self.params[self.scales_by])


@dataclass(frozen=True, slots=True)
class EntryFace:
    """The machine face of one block entry, read from its ``entry.json``."""

    entry_id: str
    version: int
    component_type: str
    origin: str
    inputs: tuple[Port, ...]
    output: Output
    parameters: Mapping[str, Parameter]
    mirroring: Mirroring
    fingerprint: str
    settle: Settle | None
    owner: str | None

    @property
    def pin(self) -> str:
        return f"{self.entry_id}@{self.version}"

    def parameter_measure(self, name: str) -> Measure | None:
        found = self.parameters.get(name)
        return found.measure if found is not None else None


@dataclass(frozen=True, slots=True)
class FaceProblem:
    where: str
    message: str


def _text(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise _Bad(key, "a non-empty string")
    return value


class _Bad(Exception):
    def __init__(self, where: str, wanted: str) -> None:
        super().__init__(where, wanted)
        self.where = where
        self.wanted = wanted


def _object(value: object, where: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _Bad(where, "an object")
    return cast("Mapping[str, object]", value)


def _port(value: object, where: str) -> Port:
    raw = _object(value, where)
    measure = raw.get("measure")
    level = raw.get("data_level")
    if measure is not None and not isinstance(measure, str):
        raise _Bad(f"{where}/measure", "a measure name or null")
    if level is not None and (not isinstance(level, int) or isinstance(level, bool)):
        raise _Bad(f"{where}/data_level", "a whole number or null")
    return Port(
        port=_text(raw, "port"),
        stream_kind=_text(raw, "stream_kind"),
        measure=measure,
        data_level=level,
    )


def _settle(value: object) -> Settle | None:
    if value is None:
        return None
    raw = _object(value, "settle_bars")
    bars = raw.get("bars")
    if not isinstance(bars, int) or isinstance(bars, bool) or bars < 1:
        raise _Bad("settle_bars/bars", "a whole number of at least 1")
    params = {
        k: Decimal(str(v)) for k, v in _object(raw.get("params"), "settle_bars/params").items()
    }
    scales_by = raw.get("scales_by")
    if scales_by is not None and (
        not isinstance(scales_by, str) or params.get(scales_by, Decimal(0)) <= 0
    ):
        raise _Bad("settle_bars/scales_by", "one of its params, above 0")
    return Settle(
        params=params,
        bars=bars,
        tolerance=Decimal(_text(raw, "tolerance")),
        scales_by=scales_by,
    )


def parse_entry(data: bytes) -> EntryFace | FaceProblem:
    """Read one ``entry.json``; the first shape problem comes back as a ``FaceProblem``."""
    try:
        raw = _object(json.loads(data.decode("utf-8")), "")
        if raw.get("schema") != ENTRY_SCHEMA:
            raise _Bad("schema", f'"{ENTRY_SCHEMA}"')
        version = raw.get("version")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise _Bad("version", "a whole number of at least 1")
        raw_inputs = raw.get("inputs")
        if not isinstance(raw_inputs, list):
            raise _Bad("inputs", "a list")
        inputs = tuple(
            _port(item, f"inputs/{i}") for i, item in enumerate(cast("list[object]", raw_inputs))
        )
        raw_output = _object(raw.get("output"), "output")
        out_measure = raw_output.get("measure")
        if out_measure is not None and not isinstance(out_measure, str):
            raise _Bad("output/measure", "a measure name or null")
        output = Output(type=OutputType(_text(raw_output, "type")), measure=out_measure)
        parameters: dict[str, Parameter] = {}
        for name, spec in _object(raw.get("parameters"), "parameters").items():
            measure = _text(_object(spec, f"parameters/{name}"), "measure")
            parameters[name] = Parameter(name=name, measure=Measure(measure))
        owner = raw.get("owner")
        return EntryFace(
            entry_id=_text(raw, "entry_id"),
            version=version,
            component_type=_text(raw, "component_type"),
            origin=_text(raw, "origin"),
            inputs=inputs,
            output=output,
            parameters=parameters,
            mirroring=Mirroring(_text(raw, "mirroring")),
            fingerprint=_text(raw, "fingerprint"),
            settle=_settle(raw.get("settle_bars")),
            owner=owner if isinstance(owner, str) else None,
        )
    except _Bad as bad:
        return FaceProblem(where=f"/{bad.where}", message=f"expected {bad.wanted}")
    except (UnicodeDecodeError, ValueError, InvalidOperation) as error:
        return FaceProblem(where="/", message=str(error))
