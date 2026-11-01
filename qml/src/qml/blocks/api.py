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
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, InvalidOperation
from enum import StrEnum
from typing import Final, Protocol, cast, runtime_checkable

from qml.unit.model import Measure, Side

__all__ = [
    "PORT_QUANTUM_SIGNIFICANT_DIGITS",
    "Block",
    "EntryFace",
    "EntryOrder",
    "FaceProblem",
    "Instance",
    "Mirroring",
    "Output",
    "OutputType",
    "Parameter",
    "Port",
    "Settle",
    "Side",
    "Signal",
    "Size",
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


class OutputType(StrEnum):
    EVENT = "event"
    LEVEL = "level"
    SERIES = "series"
    STATE = "state"
    PROBABILITY = "probability"
    QUANTITY = "quantity"
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
    """The recursive-settle length found at ``params`` within ``tolerance`` (QML-03)."""

    params: Mapping[str, Decimal]
    bars: int
    tolerance: Decimal


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
    return Settle(params=params, bars=bars, tolerance=Decimal(_text(raw, "tolerance")))


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
