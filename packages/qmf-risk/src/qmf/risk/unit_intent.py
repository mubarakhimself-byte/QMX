"""CT-23 contract format 3: the unit's own sized intent (Part A AD-108, Level 0 AD-18).

A unit sizes itself, so its entry carries the quantity its sizer chose. That size
travels as its own contract format, never as an extra key on format 1 or 2, because
the Book door (:mod:`qmf.risk.door`) drops unknown keys and would size the trade
instead. This module is a family beside the Book door, which it does not change: the
Book door keeps refusing format 3 and :func:`parse_unit_intent` accepts only format 3.

The wire form is a JSON-ready mapping. Exact values travel as decimal strings
(``"0.37"``, ``"1.08450"``) whose digits fix the scale, ratios as ``"n/d"``, and
instants as integer nanoseconds, so a quantity or a price round-trips to the last
digit and no binary float can reach one. The parser is strict: an unknown key is
refused, because a dropped key is exactly how a size gets lost.

By default an amendment may tighten a stop and never widen it
(:func:`check_amendment_tightens`); the risk session owns that law and may change it.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Final, Literal, TypeAlias, TypeVar, cast

from qmf.core import (
    AccountRole,
    ExactRational,
    Fingerprint,
    Instant,
    Instrument,
    Price,
    Quantity,
    Result,
    TypedRefusal,
    UnitKind,
    VenueId,
)
from qmf.core import Ok as _Ok
from qmf.risk._common import clean_str, coerce_contract_format_version, coerce_enum, invalid
from qmf.risk.door import ReasonCode, RiskMonotonicViolation, reject_risk_monotonic_violation
from qmf.risk.paper import ExecutionTarget
from qmf.risk.r_faces import Direction

__all__ = [
    "LOT",
    "NONE_DECLARED",
    "UNIT_INTENT_FORMAT_VERSION",
    "AmendProtection",
    "CloseFull",
    "ClosePartial",
    "OrderType",
    "PositionRef",
    "Protection",
    "SizerReceipt",
    "Target",
    "UnitEntryIntent",
    "UnitExitIntent",
    "UnitExitKind",
    "UnitOrder",
    "UnitRef",
    "check_amendment_tightens",
    "parse_unit_intent",
]

UNIT_INTENT_FORMAT_VERSION: Final[int] = 3
NONE_DECLARED: Final = "none_declared"
LOT: Final[str] = "lot"

NoneDeclared: TypeAlias = Literal["none_declared"]
StopLevel: TypeAlias = Price | NoneDeclared

_T = TypeVar("_T")

# Real lots, prices and the ratios built from them need far fewer digits per run. The
# bound keeps every numeral under CPython's int-string limit, so a long one is refused.
_MAX_DIGITS: Final = 64
_DECIMAL: Final = re.compile(
    rf"-?(0|[1-9][0-9]{{0,{_MAX_DIGITS - 1}}})(\.[0-9]{{1,{_MAX_DIGITS}}})?"
)
_RATIONAL: Final = re.compile(rf"(-?[0-9]{{1,{_MAX_DIGITS}}})/([1-9][0-9]{{0,{_MAX_DIGITS - 1}}})")


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class UnitExitKind(StrEnum):
    CLOSE_FULL = "close_full"
    CLOSE_PARTIAL = "close_partial"
    AMEND_PROTECTION = "amend_protection"


@dataclass(frozen=True, slots=True)
class UnitRef:
    unit_id: str
    version_ref: str
    compiled_fingerprint: Fingerprint


@dataclass(frozen=True, slots=True)
class UnitOrder:
    type: OrderType
    limit_price: Price | None = None
    stop_price: Price | None = None
    time_in_force: str | None = None
    expires_after_s: int | None = None


@dataclass(frozen=True, slots=True)
class Target:
    price: Price
    fraction: ExactRational


@dataclass(frozen=True, slots=True)
class SizerReceipt:
    """The sizer's receipt (Part A CONTRACTS §4.3): what it read and the R lost to lot rounding."""

    inputs_used: tuple[str, ...]
    rounding_residue_r: ExactRational


@dataclass(frozen=True, slots=True)
class Protection:
    """``stop`` is a price, or ``none_declared``, which leaves R undefined for the trade."""

    stop: StopLevel
    targets: tuple[Target, ...] = ()
    time_exit_bars: int | None = None

    @property
    def r_defined(self) -> bool:
        return isinstance(self.stop, Price)


@dataclass(frozen=True, slots=True)
class UnitEntryIntent:
    unit: UnitRef
    instrument: Instrument
    market_id: str
    direction: Direction
    reason_code: ReasonCode
    execution_target: ExecutionTarget
    order: UnitOrder
    quantity: Quantity
    sizer_receipt: SizerReceipt
    protection: Protection
    not_before: Instant
    placeholder_labels: tuple[str, ...]
    decision_row_id: str

    @property
    def contract_format_version(self) -> int:
        return UNIT_INTENT_FORMAT_VERSION

    @property
    def intent_family(self) -> Literal["entry"]:
        return "entry"

    def to_wire(self) -> dict[str, object]:
        order: dict[str, object] = {"type": self.order.type.value}
        if self.order.limit_price is not None:
            order["limit_price"] = _price_text(self.order.limit_price)
        if self.order.stop_price is not None:
            order["stop_price"] = _price_text(self.order.stop_price)
        if self.order.time_in_force is not None:
            order["time_in_force"] = self.order.time_in_force
        if self.order.expires_after_s is not None:
            order["expires_after_s"] = self.order.expires_after_s
        protection: dict[str, object] = {
            "stop": _stop_text(self.protection.stop),
            "targets": _targets_wire(self.protection.targets),
        }
        if self.protection.time_exit_bars is not None:
            protection["time_exit_bars"] = self.protection.time_exit_bars
        return {
            "contract_format_version": UNIT_INTENT_FORMAT_VERSION,
            "intent_family": self.intent_family,
            "unit": {
                "unit_id": self.unit.unit_id,
                "version_ref": self.unit.version_ref,
                "compiled_fingerprint": self.unit.compiled_fingerprint.value,
            },
            "instrument": _instrument_wire(self.instrument),
            "market_id": self.market_id,
            "direction": self.direction.value,
            "reason_code": _reason_wire(self.reason_code),
            "execution_target": {
                "role": self.execution_target.role.value,
                "venue_id": self.execution_target.venue_id.value,
                "account_id": self.execution_target.account_id,
            },
            "order": order,
            "quantity": _quantity_text(self.quantity),
            "sizer_receipt": {
                "inputs_used": list(self.sizer_receipt.inputs_used),
                "rounding_residue_r": _rational_text(self.sizer_receipt.rounding_residue_r),
            },
            "protection": protection,
            "not_before": self.not_before.value_ns,
            "placeholder_labels": list(self.placeholder_labels),  # mock-data-scan: allow (field)
            "decision_row_id": self.decision_row_id,
        }


@dataclass(frozen=True, slots=True)
class PositionRef:
    """The position an exit acts on, and the compiled fingerprint that opened it."""

    position_id: str
    instrument: Instrument
    opened_by: Fingerprint


@dataclass(frozen=True, slots=True)
class CloseFull:
    pass


@dataclass(frozen=True, slots=True)
class ClosePartial:
    quantity: Quantity


@dataclass(frozen=True, slots=True)
class AmendProtection:
    stop: Price
    targets: tuple[Target, ...] = ()


ExitAction: TypeAlias = CloseFull | ClosePartial | AmendProtection

_KIND_OF_ACTION: Final[Mapping[type[object], UnitExitKind]] = {
    CloseFull: UnitExitKind.CLOSE_FULL,
    ClosePartial: UnitExitKind.CLOSE_PARTIAL,
    AmendProtection: UnitExitKind.AMEND_PROTECTION,
}


@dataclass(frozen=True, slots=True)
class UnitExitIntent:
    """An exit whose ``action`` fixes its kind, so a kind can never carry another kind's fields."""

    action: ExitAction
    position_ref: PositionRef
    reason_code: ReasonCode
    decision_row_id: str

    @property
    def contract_format_version(self) -> int:
        return UNIT_INTENT_FORMAT_VERSION

    @property
    def intent_family(self) -> Literal["exit"]:
        return "exit"

    @property
    def kind(self) -> UnitExitKind:
        return _KIND_OF_ACTION[type(self.action)]

    def to_wire(self) -> dict[str, object]:
        wire: dict[str, object] = {
            "contract_format_version": UNIT_INTENT_FORMAT_VERSION,
            "intent_family": self.intent_family,
            "kind": self.kind.value,
            "position_ref": {
                "position_id": self.position_ref.position_id,
                "instrument": _instrument_wire(self.position_ref.instrument),
                "opened_by": self.position_ref.opened_by.value,
            },
            "reason_code": _reason_wire(self.reason_code),
            "decision_row_id": self.decision_row_id,
        }
        match self.action:
            case ClosePartial(quantity=quantity):
                wire["quantity"] = _quantity_text(quantity)
            case AmendProtection(stop=stop, targets=targets):
                wire["stop"] = _price_text(stop)
                wire["targets"] = _targets_wire(targets)
            case CloseFull():
                pass
        return wire


UnitIntent: TypeAlias = UnitEntryIntent | UnitExitIntent


# --- the parser ----------------------------------------------------------------


class _Refused(Exception):
    """Carries a refusal out of the nested readers; never escapes :func:`parse_unit_intent`."""

    def __init__(self, refusal: TypedRefusal) -> None:
        super().__init__(refusal)
        self.refusal = refusal


def _refuse(field: str, reason: str, **extra: object) -> _Refused:
    return _Refused(invalid(field, reason, **extra))


def _unwrap(result: Result[_T]) -> _T:
    if isinstance(result, TypedRefusal):
        raise _Refused(result)
    return result.value


class _Fields:
    """One wire mapping read strictly: every key must be read, an unread key is refused."""

    def __init__(self, raw: object, path: str) -> None:
        if not isinstance(raw, Mapping):
            raise _refuse(path, "a unit intent part is a mapping", given=type(raw).__name__)
        self._mapping = cast("Mapping[str, object]", raw)
        self._path = path
        self._read: set[str] = set()

    def at(self, key: str) -> str:
        return f"{self._path}.{key}" if self._path else key

    def has(self, key: str) -> bool:
        return key in self._mapping

    def required(self, key: str) -> object:
        self._read.add(key)
        if key not in self._mapping:
            raise _refuse(self.at(key), "a required field of CT-23 format 3 is missing")
        return self._mapping[key]

    def optional(self, key: str) -> object | None:
        self._read.add(key)
        if key not in self._mapping:
            return None
        value = self._mapping[key]
        if value is None:
            raise _refuse(self.at(key), "an optional field is left out, never sent as null")
        return value

    def text(self, key: str) -> str:
        return _text(self.required(key), self.at(key))

    def finish(self) -> None:
        unknown = sorted(str(key) for key in self._mapping if key not in self._read)
        if unknown:
            raise _refuse(
                self._path or "intent",
                "CT-23 format 3 refuses unknown keys, so a field can never be dropped silently",
                unknown=unknown,
            )


def parse_unit_intent(raw: object) -> Result[UnitIntent]:
    """Parse a format-3 wire mapping into a :class:`UnitEntryIntent` or :class:`UnitExitIntent`.

    Formats 1 and 2 (the Book door's), an unstamped mapping, and any other version are an
    ``unsupported capability`` refusal. Every other fault is ``invalid input``.
    """
    try:
        fields = _Fields(raw, "")
        _require_format_3(fields.optional("contract_format_version"))
        family = fields.required("intent_family")
        if family == "entry":
            intent: UnitIntent = _read_entry(fields)
        elif family == "exit":
            intent = _read_exit(fields)
        else:
            raise _refuse(
                "intent_family",
                "a format-3 intent is an entry or an exit",
                given=repr(family),
                allowed=["entry", "exit"],
            )
        fields.finish()
    except _Refused as refused:
        return refused.refusal
    return _Ok(intent)


def _require_format_3(version: object) -> None:
    resolved = coerce_contract_format_version(
        version,
        known=frozenset({UNIT_INTENT_FORMAT_VERSION}),
        reader_format_version=UNIT_INTENT_FORMAT_VERSION,
    )
    if isinstance(resolved, TypedRefusal):
        raise _Refused(resolved)


def _read_entry(fields: _Fields) -> UnitEntryIntent:
    instrument = _read_instrument(fields.required("instrument"), fields.at("instrument"))
    direction = _read_direction(fields.required("direction"), fields.at("direction"))
    order = _read_order(fields.required("order"), fields.at("order"), instrument)
    protection = _read_protection(
        fields.required("protection"), fields.at("protection"), instrument
    )
    _check_sides(direction, order, protection)
    return UnitEntryIntent(
        unit=_read_unit_ref(fields.required("unit"), fields.at("unit")),
        instrument=instrument,
        market_id=fields.text("market_id"),
        direction=direction,
        reason_code=_read_reason(fields.required("reason_code"), fields.at("reason_code")),
        execution_target=_read_execution_target(
            fields.required("execution_target"), fields.at("execution_target")
        ),
        order=order,
        quantity=_read_lots(fields.required("quantity"), fields.at("quantity")),
        sizer_receipt=_read_receipt(fields.required("sizer_receipt"), fields.at("sizer_receipt")),
        protection=protection,
        not_before=_read_instant(fields.required("not_before"), fields.at("not_before")),
        placeholder_labels=_read_labels(
            fields.required("placeholder_labels"),  # mock-data-scan: allow (receipt field)
            fields.at("placeholder_labels"),  # mock-data-scan: allow (receipt field)
        ),
        decision_row_id=fields.text("decision_row_id"),
    )


def _read_exit(fields: _Fields) -> UnitExitIntent:
    kind_value = fields.required("kind")
    kind = coerce_enum(UnitExitKind, kind_value)
    if kind is None:
        raise _refuse(
            "kind",
            "a format-3 exit is close_full, close_partial or amend_protection",
            given=repr(kind_value),
            allowed=[member.value for member in UnitExitKind],
        )
    position_ref = _read_position_ref(fields.required("position_ref"), fields.at("position_ref"))
    action: ExitAction
    match kind:
        case UnitExitKind.CLOSE_FULL:
            action = CloseFull()
        case UnitExitKind.CLOSE_PARTIAL:
            action = ClosePartial(quantity=_read_lots(fields.required("quantity"), "quantity"))
        case UnitExitKind.AMEND_PROTECTION:
            instrument = position_ref.instrument
            action = AmendProtection(
                stop=_read_price(fields.required("stop"), "stop", instrument),
                targets=_read_targets(fields.required("targets"), "targets", instrument),
            )
    return UnitExitIntent(
        action=action,
        position_ref=position_ref,
        reason_code=_read_reason(fields.required("reason_code"), fields.at("reason_code")),
        decision_row_id=fields.text("decision_row_id"),
    )


def _read_unit_ref(raw: object, path: str) -> UnitRef:
    fields = _Fields(raw, path)
    unit = UnitRef(
        unit_id=fields.text("unit_id"),
        version_ref=fields.text("version_ref"),
        compiled_fingerprint=_read_fingerprint(
            fields.required("compiled_fingerprint"), fields.at("compiled_fingerprint")
        ),
    )
    fields.finish()
    return unit


def _read_position_ref(raw: object, path: str) -> PositionRef:
    fields = _Fields(raw, path)
    ref = PositionRef(
        position_id=fields.text("position_id"),
        instrument=_read_instrument(fields.required("instrument"), fields.at("instrument")),
        opened_by=_read_fingerprint(fields.required("opened_by"), fields.at("opened_by")),
    )
    fields.finish()
    return ref


def _read_instrument(raw: object, path: str) -> Instrument:
    fields = _Fields(raw, path)
    venue = _unwrap(VenueId.try_create(fields.text("venue")))
    instrument = _unwrap(Instrument.try_create(venue, fields.text("symbol")))
    fields.finish()
    return instrument


def _read_reason(raw: object, path: str) -> ReasonCode:
    fields = _Fields(raw, path)
    reason = _unwrap(ReasonCode.try_create(fields.text("code"), fields.text("book_family")))
    fields.finish()
    return reason


def _read_execution_target(raw: object, path: str) -> ExecutionTarget:
    fields = _Fields(raw, path)
    role = coerce_enum(AccountRole, fields.required("role"))
    if role is None:
        raise _refuse(
            fields.at("role"),
            "an execution target carries an account role",
            allowed=[member.value for member in AccountRole],
        )
    venue = _unwrap(VenueId.try_create(fields.text("venue_id")))
    target = _unwrap(ExecutionTarget.try_create(role, venue, fields.text("account_id")))
    fields.finish()
    return target


def _read_order(raw: object, path: str, instrument: Instrument) -> UnitOrder:
    fields = _Fields(raw, path)
    type_value = fields.required("type")
    order_type = coerce_enum(OrderType, type_value)
    if order_type is None:
        raise _refuse(
            fields.at("type"),
            "an order type is market, limit, stop or stop_limit",
            given=repr(type_value),
            allowed=[member.value for member in OrderType],
        )
    needs_limit = order_type in {OrderType.LIMIT, OrderType.STOP_LIMIT}
    needs_stop = order_type in {OrderType.STOP, OrderType.STOP_LIMIT}
    for key, needed in (("limit_price", needs_limit), ("stop_price", needs_stop)):
        if fields.has(key) != needed:
            raise _refuse(
                fields.at(key),
                f"a {order_type.value} order {'needs' if needed else 'never carries'} {key}",
            )
    limit_raw = fields.optional("limit_price")
    stop_raw = fields.optional("stop_price")
    tif_raw = fields.optional("time_in_force")
    expires_raw = fields.optional("expires_after_s")
    order = UnitOrder(
        type=order_type,
        limit_price=None
        if limit_raw is None
        else _read_price(limit_raw, fields.at("limit_price"), instrument),
        stop_price=None
        if stop_raw is None
        else _read_price(stop_raw, fields.at("stop_price"), instrument),
        time_in_force=None if tif_raw is None else _text(tif_raw, fields.at("time_in_force")),
        expires_after_s=None
        if expires_raw is None
        else _positive_int(expires_raw, fields.at("expires_after_s")),
    )
    fields.finish()
    return order


def _read_protection(raw: object, path: str, instrument: Instrument) -> Protection:
    fields = _Fields(raw, path)
    stop_raw = fields.required("stop")
    stop: StopLevel = (
        NONE_DECLARED
        if stop_raw == NONE_DECLARED
        else _read_price(stop_raw, fields.at("stop"), instrument)
    )
    bars_raw = fields.optional("time_exit_bars")
    protection = Protection(
        stop=stop,
        targets=_read_targets(fields.required("targets"), fields.at("targets"), instrument),
        time_exit_bars=None
        if bars_raw is None
        else _positive_int(bars_raw, fields.at("time_exit_bars")),
    )
    fields.finish()
    return protection


def _read_targets(raw: object, path: str, instrument: Instrument) -> tuple[Target, ...]:
    items = _list(raw, path)
    targets: list[Target] = []
    for index, item in enumerate(items):
        fields = _Fields(item, f"{path}[{index}]")
        fraction = _read_rational(
            fields.required("fraction"), fields.at("fraction"), UnitKind.DIMENSIONLESS_RATIO
        )
        if not 0 < fraction.as_fraction() <= 1:
            raise _refuse(
                fields.at("fraction"), "a target closes a fraction in (0, 1] of the position"
            )
        targets.append(
            Target(
                price=_read_price(fields.required("price"), fields.at("price"), instrument),
                fraction=fraction,
            )
        )
        fields.finish()
    if sum((target.fraction.as_fraction() for target in targets), Fraction(0)) > 1:
        raise _refuse(path, "the target fractions together close at most the whole position")
    return tuple(targets)


def _read_receipt(raw: object, path: str) -> SizerReceipt:
    fields = _Fields(raw, path)
    receipt = SizerReceipt(
        inputs_used=_read_labels(fields.required("inputs_used"), fields.at("inputs_used")),
        rounding_residue_r=_read_rational(
            fields.required("rounding_residue_r"),
            fields.at("rounding_residue_r"),
            UnitKind.R_MULTIPLE,
        ),
    )
    fields.finish()
    return receipt


def _read_labels(raw: object, path: str) -> tuple[str, ...]:
    labels = tuple(_text(item, f"{path}[{index}]") for index, item in enumerate(_list(raw, path)))
    if len(set(labels)) != len(labels):
        raise _refuse(path, "a label is listed once")
    return labels


def _read_direction(raw: object, path: str) -> Direction:
    direction = coerce_enum(Direction, raw)
    if direction is None:
        raise _refuse(
            path,
            "a direction is long or short",
            given=repr(raw),
            allowed=[m.value for m in Direction],
        )
    return direction


def _read_instant(raw: object, path: str) -> Instant:
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise _refuse(path, "an instant travels as integer nanoseconds", given=repr(raw))
    return _unwrap(Instant.try_create(raw))


def _read_fingerprint(raw: object, path: str) -> Fingerprint:
    return _unwrap(Fingerprint.try_create(_text(raw, path)))


def _read_lots(raw: object, path: str) -> Quantity:
    value, scale = _decimal(raw, path)
    if value <= 0:
        raise _refuse(path, "a quantity in lots is above zero")
    return _unwrap(Quantity.try_create(value, LOT, scale))


def _read_price(raw: object, path: str, instrument: Instrument) -> Price:
    value, scale = _decimal(raw, path)
    return _unwrap(Price.try_create(value, instrument, scale))


def _read_rational(raw: object, path: str, unit_kind: UnitKind) -> ExactRational:
    match = _RATIONAL.fullmatch(raw) if isinstance(raw, str) else None
    if match is None:
        raise _refuse(path, "a ratio travels as the text 'n/d'", given=repr(raw))
    return _unwrap(ExactRational.try_create(int(match[1]), int(match[2]), unit_kind))


def _decimal(raw: object, path: str) -> tuple[int, int]:
    """Read an exact decimal string as ``(scaled integer, scale)``; a float never gets here."""
    if not isinstance(raw, str) or _DECIMAL.fullmatch(raw) is None:
        raise _refuse(
            path,
            "an exact value travels as a decimal string such as '0.37', never a number",
            given=repr(raw),
        )
    whole, _, fraction = raw.partition(".")
    value = int(whole + fraction)
    if value == 0 and raw.startswith("-"):
        raise _refuse(path, "zero carries no sign", given=raw)
    return value, len(fraction)


def _text(raw: object, path: str) -> str:
    token = clean_str(raw)
    if token is None:
        raise _refuse(path, "a non-empty text value is required", given=repr(raw))
    return token


def _list(raw: object, path: str) -> Sequence[object]:
    if not isinstance(raw, list):
        raise _refuse(path, "a list is required", given=type(raw).__name__)
    return cast("list[object]", raw)


def _positive_int(raw: object, path: str) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int) or raw <= 0:
        raise _refuse(path, "a whole number above zero is required", given=repr(raw))
    return raw


def _check_sides(direction: Direction, order: UnitOrder, protection: Protection) -> None:
    """The stop sits on the loss side of every order price and every target on the profit side."""
    sign = 1 if direction is Direction.LONG else -1
    order_prices = [
        price.as_fraction() for price in (order.limit_price, order.stop_price) if price is not None
    ]
    targets = [target.price.as_fraction() for target in protection.targets]
    stop = protection.stop
    if isinstance(stop, Price):
        stop_level = stop.as_fraction()
        if any(sign * (level - stop_level) <= 0 for level in order_prices + targets):
            raise _refuse(
                "protection.stop",
                f"a {direction.value} stop sits on the loss side of every order price and target",
            )
    for target in targets:
        if any(sign * (target - level) <= 0 for level in order_prices):
            raise _refuse(
                "protection.targets",
                f"a {direction.value} target sits beyond every order price on the profit side",
            )


# --- the amendment law -----------------------------------------------------------


def check_amendment_tightens(
    exit_intent: object, *, direction: object, current_stop: object
) -> Result[None]:
    """Refuse an ``amend_protection`` that widens the position's stop.

    A long's stop may only rise and a short's only fall; a position with no declared
    stop takes any stop. Widening is a ``widen-stop`` risk-monotonic policy rejection.
    """
    if not isinstance(exit_intent, UnitExitIntent) or not isinstance(
        exit_intent.action, AmendProtection
    ):
        return invalid("exit_intent", "the amendment law reads an amend_protection exit")
    resolved = coerce_enum(Direction, direction)
    if resolved is None:
        return invalid(
            "direction", "the position's direction is long or short", given=repr(direction)
        )
    if current_stop == NONE_DECLARED:
        return _Ok(None)
    if (
        not isinstance(current_stop, Price)
        or current_stop.instrument != exit_intent.position_ref.instrument
    ):
        return invalid(
            "current_stop",
            "the current stop is a price on the position's instrument, or none_declared",
            given=repr(current_stop),
        )
    proposed = exit_intent.action.stop.as_fraction()
    current = current_stop.as_fraction()
    widens = proposed < current if resolved is Direction.LONG else proposed > current
    if widens:
        return reject_risk_monotonic_violation(
            RiskMonotonicViolation.WIDEN_STOP,
            detail=(
                f"an amendment may tighten a stop and never widen it; the {resolved.value} "
                f"stop moves from {_price_text(current_stop)} to "
                f"{_price_text(exit_intent.action.stop)}"
            ),
        )
    return _Ok(None)


# --- wire writers ------------------------------------------------------------------


def _decimal_text(value: int, scale: int) -> str:
    digits = str(abs(value)).rjust(scale + 1, "0")
    sign = "-" if value < 0 else ""
    if scale == 0:
        return sign + digits
    return f"{sign}{digits[:-scale]}.{digits[-scale:]}"


def _price_text(price: Price) -> str:
    return _decimal_text(price.value, price.scale)


def _quantity_text(quantity: Quantity) -> str:
    return _decimal_text(quantity.value, quantity.scale)


def _stop_text(stop: StopLevel) -> str:
    return _price_text(stop) if isinstance(stop, Price) else NONE_DECLARED


def _rational_text(value: ExactRational) -> str:
    return f"{value.numerator}/{value.denominator}"


def _targets_wire(targets: tuple[Target, ...]) -> list[dict[str, object]]:
    return [
        {"price": _price_text(target.price), "fraction": _rational_text(target.fraction)}
        for target in targets
    ]


def _instrument_wire(instrument: Instrument) -> dict[str, object]:
    return {"venue": instrument.venue.value, "symbol": instrument.symbol}


def _reason_wire(reason: ReasonCode) -> dict[str, object]:
    return {"code": reason.code, "book_family": reason.book_family}
