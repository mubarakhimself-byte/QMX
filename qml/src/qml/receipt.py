"""One row answers why this size: the trail it prints and the replay it must meet (AD-18, AD-9).

The size trail is the decision row. ``HostedUnit.price`` fills the row with every input the size
read, the sizer that answered, the steps it took and each link's verdict; a host journals it
before any order leaves; and this module reads that stored row back. One function each, over
plain mappings, for the developer, the copilot, the UI and triage alike:

- :func:`stored_row` — the row as a host journals it.
- :func:`row_hash` — the receipt's own fingerprint, over exactly the inputs and steps the size
  used, so a changed input changes the hash rather than passing quietly.
- :func:`explain_size` — the trail, one line per step, each fact with its source and its age.
- :func:`replay_decision` — re-run the sizing on the row's own stored inputs and answer the
  quantity it must reach. The sizer is a pinned block, so a row stores the amount it answered
  and everything after it replays: the one converter, its lot rounding and its residue.

Nothing here imports a host (AD-21). The record the row carries is read back by the same parser
that read it first, so a replay never guesses a value per point or a lot step.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Final, Literal, cast

from qmf.core.chrono import Instant
from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import is_refusal
from qmf.risk.facts import Fact

from qml.blocks.api import Amount
from qml.numbers.convert import RoundRule, to_quantity
from qml.numbers.records import InstrumentRecord, parse_record

if TYPE_CHECKING:  # the row's shape lives in the unit's own module, which imports this one
    from qml.protocol.unit import DecisionRow, ModifierReading

_AmountKind = Literal["money_at_risk", "notional", "quantity"]
_FailMode = Literal["open", "closed", "neutral"]
_FactState = Literal["ok", "stale", "absent", "uncalibrated"]

__all__ = [
    "FactSeen",
    "FactorSeen",
    "NumberSeen",
    "Replay",
    "Step",
    "Trail",
    "explain_size",
    "record_stored",
    "replay_decision",
    "row_hash",
    "stored_row",
]

_NANOS_PER_SECOND: Final[int] = 1_000_000_000

_RECEIPT_KEYS: Final[tuple[str, ...]] = (
    "binding",
    "inputs",
    "steps",
    "verdicts",
    "numbers_in_force",
    "logic_fp",
    "risk_fp",
    "placeholders",
)
"""The row's receipt: every input the size read, every step it took and every link that judged
it. The hash covers these and nothing else, so a later row field does not move it and a changed
input, amount or verdict always does."""

_DEFAULTS: Final[Mapping[str, object]] = {
    "binding": "",
    "inputs": {},
    "steps": {},
    "verdicts": [],
    "numbers_in_force": {},
    "logic_fp": "",
    "risk_fp": "",
    "placeholders": [],
}


@dataclass(frozen=True, slots=True)
class FactSeen:
    """One input as the row read it: its value, who supplied it, and how old it was."""

    name: str
    value: str
    source: str
    age_s: str


@dataclass(frozen=True, slots=True)
class NumberSeen:
    """One number in force at this entry: its value, and for a number a calibration row moved,
    the default it started from and that row's id (AD-14 step 4)."""

    name: str
    value: str
    default: str = ""
    calibration_row_id: str = ""

    @property
    def text(self) -> str:
        """The number as the trail prints it, naming the row that set it when one did."""
        if not self.calibration_row_id:
            return f"{self.name} {self.value}"
        return f"{self.name} {self.value} default {self.default} set by {self.calibration_row_id}"


@dataclass(frozen=True, slots=True)
class Step:
    """One position of the entry's size, side by side (FUNNEL D42): the unit it is in, its value,
    and the basis R is measured against."""

    name: str
    kind: str
    value: str
    basis: str


@dataclass(frozen=True, slots=True)
class FactorSeen:
    """One sizing modifier as the trail prints it (AD-11): its name, the factor it answered, the
    range it declared, its own reason, the code the row gave the reading, and its fail mode."""

    name: str
    value: str
    range: str
    reason: str
    code: str
    fail_mode: str


@dataclass(frozen=True, slots=True)
class Trail:
    """One entry's size trail, in the order it happened."""

    row_hash: str
    binding: str
    logic_fp: str
    risk_fp: str
    written_before_send: bool
    facts: tuple[FactSeen, ...]
    numbers: tuple[NumberSeen, ...]
    steps: tuple[Step, ...]
    verdicts: tuple[str, ...]
    residue_r: str
    placeholders: tuple[str, ...]
    factors: tuple[FactorSeen, ...]


@dataclass(frozen=True, slots=True)
class Replay:
    """What the row's own inputs give when the sizing runs again: the venue's quantity, the
    share of R the lot rounding left out, and the row it was replayed from."""

    quantity: Decimal | None
    residue_r: Decimal
    code: str | None
    row_hash: str


def _number(value: Decimal | Fraction | str) -> str:
    """``value`` as text a replay reads back exactly: a decimal in plain digits, a rate as
    ``n/d``. Never a binary float (``tools/money_path_scan.py``)."""
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


def record_stored(record: InstrumentRecord) -> Mapping[str, object]:
    """The instrument record's own facts, in the form :func:`qml.numbers.parse_record` reads
    back, so the row that carries them replays alone. A key the parser does not read is left
    out; an absent optional value is omitted rather than written as a null (CT-05)."""
    body: dict[str, object] = {
        "market_id": record.market_id,
        "venue": record.venue,
        "symbol": record.symbol,
        "class": record.instrument_class.value,
        "currency": record.currency,
        "digits": record.digits,
        "tick_size": _number(record.tick_size),
        "contract_size": _number(record.contract_size),
        "value_per_point": _number(record.value_per_point),
        "lot_step": _number(record.lot_step),
        "min_lot": _number(record.min_lot),
        "calendar_ref": record.calendar_ref,
        "zone": record.zone,
        "day_boundary": record.day_boundary,
        "data_levels": dict(record.data_levels),
        "leverage": dict(record.leverage),
        "margin": dict(record.margin),
        "record_version": record.record_version,
        "conversions": {
            account: {"market_id": ref.market_id, "invert": ref.invert}
            for account, ref in record.conversions.items()
        },
    }
    if record.pip is not None:
        body["pip"] = {"size": _number(record.pip.size), "source": record.pip.source}
    optional: tuple[tuple[str, object], ...] = (
        ("max_lot", record.max_lot),
        ("expiry", record.expiry),
        ("last_trade", record.last_trade),
        ("root", record.root),
        ("rolls_to", record.rolls_to),
        ("funding_interval", record.funding_interval),
    )
    for name, value in optional:
        if value is not None:
            body[name] = _number(value) if isinstance(value, Decimal) else value
    return body


def _fact_stored(fact: Fact) -> Mapping[str, object]:
    """One fact as the row stores it. An absent value or read time is omitted, never a null."""
    body: dict[str, object] = {
        "source": fact.source,
        "state": fact.state,
        "fail_mode": fact.fail_mode,
    }
    if fact.value is not None:
        body["value"] = _number(fact.value)
    if fact.ts is not None:
        body["ts"] = fact.ts.value_ns
    return body


def _amount_stored(amount: Amount) -> Mapping[str, object]:
    return {"kind": amount.kind, "value": _number(amount.value), "basis": amount.basis}


def _modifier_stored(reading: ModifierReading) -> Mapping[str, object]:
    """One sizing modifier's answer as the row stores it (AD-11): its name and block, the factor it
    answered, the range it declared, its reason, its code and its fail mode. An absent range is
    omitted rather than written as a null (CT-05)."""
    body: dict[str, object] = {
        "name": reading.name,
        "pin": reading.pin,
        "value": _number(reading.value),
        "reason": reading.reason,
        "code": reading.code,
        "fail_mode": reading.fail_mode,
    }
    if reading.range is not None:
        body["range"] = [_number(reading.range[0]), _number(reading.range[1])]
    return body


def stored_row(row: DecisionRow) -> Mapping[str, object]:
    """One decision row as a host journals it: the numbers, the facts it read, the three
    positions of its size, each link's verdict, the sizing modifiers and the two fingerprints it
    was made under. The host adds its own reason code and the readings its blocks produced. A row
    with no sizing modifiers carries no ``modifiers`` key, and one whose numbers are all at their
    start carries no ``numbers_moved`` key, so its body is the one it carried before either
    existed. Neither key is in the receipt's hash: they name where a value came from, and the
    value itself is in ``numbers_in_force``."""
    body: dict[str, object] = {
        "row_id": row.row_id,
        "instant": row.instant.value_ns,
        "market_id": row.market_id,
        "side": row.side.value,
        "outcome": row.outcome,
        "numbers_in_force": {name: _number(value) for name, value in row.numbers_in_force.items()},
        "binding": row.binding,
        "inputs": {
            name: _fact_stored(value) if isinstance(value, Fact) else value
            for name, value in row.inputs.items()
        },
        "steps": {name: _amount_stored(amount) for name, amount in row.steps.items()},
        "verdicts": list(row.verdicts),
        "logic_fp": row.logic_fp,
        "risk_fp": row.risk_fp,
        "placeholders": list(row.placeholders),
        "written_before_send": row.written_before_send,
    }
    if row.modifiers:
        body["modifiers"] = [_modifier_stored(reading) for reading in row.modifiers]
    if row.numbers_moved:
        body["numbers_moved"] = {
            name: {
                "default": _number(moved.default),
                "calibration_row_id": moved.calibration_row_id,
            }
            for name, moved in row.numbers_moved.items()
        }
    return body


def row_hash(row: Mapping[str, object]) -> str:
    """The receipt's fingerprint. Two rows with the same inputs, steps and verdicts hash the
    same; a row whose input moved does not."""
    printed = fingerprint({key: row.get(key, _DEFAULTS[key]) for key in _RECEIPT_KEYS})
    if is_refusal(printed):  # pragma: no cover - text, integers and lists always serialise
        raise ValueError(str(printed.context))
    return printed.value.value


def _map(value: object) -> Mapping[str, object]:
    return cast("Mapping[str, object]", value) if isinstance(value, Mapping) else {}


def _age(row_instant: int, reading: object) -> str:
    """How old the input was when the row was written, in seconds, exact: a whole second reads as
    its digits and a part of one as a rational, never as a binary float."""
    found = _map(reading).get("ts")
    if not isinstance(found, int):
        return ""
    seconds = Fraction(row_instant - found, _NANOS_PER_SECOND)
    return str(seconds.numerator) if seconds.denominator == 1 else _number(seconds)


def _source(name: str, body: Mapping[str, object]) -> str:
    """Who supplied one stored input. A fact carries its own source; the record names its own
    version, which is what a reader needs to know which value per point spelled the size."""
    given = body.get("source")
    if isinstance(given, str) and given:
        return given
    return "the instrument record" if name == "record" else ""


def _value(name: str, body: Mapping[str, object]) -> str:
    """One stored input's value as the trail prints it. The record prints as its own name: it is
    a version in force, not a reading with an age."""
    if name == "record":
        return f"{body.get('venue')}:{body.get('symbol')}@{body.get('record_version')}"
    value = body.get("value")
    return "" if value is None else str(value)


def _seen(name: str, reading: object, row_instant: int) -> FactSeen:
    body = _map(reading)
    return FactSeen(
        name=name,
        value=_value(name, body),
        source=_source(name, body),
        age_s="" if name == "record" else _age(row_instant, reading),
    )


_STEP_ORDER: Final[tuple[str, ...]] = ("wanted", "modified", "reduced", "approved", "filled")
"""The size's own order. A stored body's keys are canonicalised alphabetically on the way in
(CT-05), so the trail reads the order from here and never from the mapping."""


def _ordered(steps: Mapping[str, object]) -> list[tuple[str, object]]:
    """The steps in the order the size took them, then any the reader does not know."""
    known = [(name, steps[name]) for name in _STEP_ORDER if name in steps]
    return known + [(name, step) for name, step in steps.items() if name not in _STEP_ORDER]


def _range_text(value: object) -> str:
    """A stored modifier's declared range as the trail prints it, or nothing when it had none."""
    if not isinstance(value, list) or len(cast("list[object]", value)) != 2:
        return ""
    low, high = cast("list[object]", value)
    return f"{low} to {high}"


def _factor_seen(reading: object) -> FactorSeen:
    """One stored modifier as the trail prints it."""
    body = _map(reading)
    return FactorSeen(
        name=str(body.get("name", "")),
        value=str(body.get("value", "")),
        range=_range_text(body.get("range")),
        reason=str(body.get("reason", "")),
        code=str(body.get("code", "")),
        fail_mode=str(body.get("fail_mode", "")),
    )


def _number_seen(name: str, value: object, moved: object) -> NumberSeen:
    """One stored number as the trail prints it, with the row that moved it when one did."""
    body = _map(moved)
    return NumberSeen(
        name=name,
        value=str(value),
        default=str(body.get("default", "")),
        calibration_row_id=str(body.get("calibration_row_id", "")),
    )


def explain_size(row: Mapping[str, object], fill: Mapping[str, object] | None = None) -> Trail:
    """One entry's size trail: every fact with its source and age, the numbers in force with the
    default and calibration row of each one a row moved, the base amount and its basis, each link's
    verdict, the converter's residue, and the fill with its gap when the caller has the fill row
    (the row is written before any order leaves, so the third position of the size lands in the
    ``fill`` row and not on this one)."""
    instant = int(cast("int", row.get("instant", 0)))
    steps = tuple(
        Step(
            name,
            str(_map(step).get("kind", "")),
            str(_map(step).get("value", "")),
            str(_map(step).get("basis", "")),
        )
        for name, step in _ordered(_map(row.get("steps")))
    )
    if fill is not None:
        steps += (Step("filled", "quantity", str(fill.get("quantity", "")), "the venue's fill"),)
    return Trail(
        row_hash=row_hash(row),
        binding=str(row.get("binding", "")),
        logic_fp=str(row.get("logic_fp", "")),
        risk_fp=str(row.get("risk_fp", "")),
        written_before_send=row.get("written_before_send") is True,
        facts=tuple(_seen(name, fact, instant) for name, fact in _map(row.get("inputs")).items()),
        numbers=tuple(
            _number_seen(name, value, _map(row.get("numbers_moved")).get(name))
            for name, value in _map(row.get("numbers_in_force")).items()
        ),
        steps=steps,
        verdicts=tuple(str(word) for word in cast("list[object]", row.get("verdicts", []))),
        residue_r=_number(replay_decision(row).residue_r),
        placeholders=tuple(
            str(label) for label in cast("list[object]", row.get("placeholders", []))
        ),
        factors=tuple(
            _factor_seen(reading) for reading in cast("list[object]", row.get("modifiers", []))
        ),
    )


def _value_of(reading: object) -> Decimal | None:
    value = _map(reading).get("value")
    return None if value is None else Decimal(str(value))


_SIZED_STEPS: Final[tuple[str, ...]] = ("wanted", "modified", "reduced")
"""The steps that state an amount before the converter, in the order the size took them. The last
one present is the amount the converter spelled, so a replay uses it and a modifier or a brake that
cut the size is replayed as it was, not as the sizer first answered it."""


def _last_sized(steps: Mapping[str, object]) -> Mapping[str, object]:
    """The last amount step the row stores: the sizer's, or the one a modifier or brake made."""
    found: Mapping[str, object] = {}
    for name in _SIZED_STEPS:
        step = steps.get(name)
        if isinstance(step, Mapping):
            found = cast("Mapping[str, object]", step)
    return found


def _one_of(value: object, allowed: tuple[str, ...], default: str) -> str:
    """``value`` when it is one of ``allowed``, else ``default``: a stored row is read, never
    trusted, and a word outside the closed list reads as the fail-safe one."""
    return value if isinstance(value, str) and value in allowed else default


def _rate_of(facts: Mapping[str, object], currency: str) -> Fact | None:
    """The rate fact the row stored for the record's quote, read back with its age."""
    body = _map(facts.get(f"market.rate:{currency}"))
    value = body.get("value")
    if value is None:
        return None
    stamp = body.get("ts")
    return Fact(
        Fraction(str(value)),
        None if not isinstance(stamp, int) else Instant(stamp),
        cast("_FailMode", _one_of(body.get("fail_mode"), ("open", "closed", "neutral"), "closed")),
        str(body.get("source", "")),
        cast(
            "_FactState",
            _one_of(body.get("state"), ("ok", "stale", "absent", "uncalibrated"), "ok"),
        ),
    )


def replay_decision(row: Mapping[str, object]) -> Replay:
    """Re-run the sizing on the row's own stored inputs and answer the quantity it reaches.

    The sizer and each sizing modifier are pinned blocks, so a row stores the amount each chain
    link produced; everything after the last one runs again here, through the same converter the
    price call used, over the record, the entry, the stop and the rate the row also stored. A row
    missing an input answers the code naming what it lacks instead of a size."""
    digest = row_hash(row)
    wanted = _last_sized(_map(row.get("steps")))
    kind = wanted.get("kind")
    value = wanted.get("value")
    if kind is None or value is None:
        return Replay(None, Decimal(0), "amount_absent", digest)
    parsed = parse_record(_map(row.get("inputs")).get("record"))
    if is_refusal(parsed):
        return Replay(None, Decimal(0), "record_unreadable", digest)
    facts = _map(row.get("inputs"))
    entry = _value_of(facts.get("entry_price"))
    stop = _value_of(facts.get("stop_price"))
    if entry is None or stop is None:
        return Replay(None, Decimal(0), "prices_absent", digest)
    amount = Amount(
        kind=cast(
            "_AmountKind",
            _one_of(kind, ("money_at_risk", "notional", "quantity"), "quantity"),
        ),
        value=Decimal(str(value)),
        basis=str(wanted.get("basis", "")),
    )
    converted = to_quantity(
        amount,
        entry,
        stop,
        parsed.value,
        _rate_of(facts, parsed.value.currency),
        RoundRule(now=Instant(int(cast("int", row.get("instant", 0))))),
    )
    return Replay(converted.quantity, converted.residue_r, converted.skipped, digest)
