"""Book-side replay admission, exact position sizing and CT-29 close journaling.

The handler is an application-layer replay composition root. It consumes CT-23
proposals, resolves size through the declared R-unit/value-factor inputs, executes
the bound fill/slippage/cost ports, and records a CT-29 close before returning it.
It never creates venue positions or maps an opaque reason code by guesswork.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from fractions import Fraction
from types import MappingProxyType
from typing import Final, cast

from qmf.core import (
    ExactRational,
    Fingerprint,
    Instant,
    Instrument,
    Money,
    Ok,
    Price,
    PriceDelta,
    Quantity,
    Result,
    ValueFactor,
    VenueId,
    World,
    WriterId,
    fingerprint,
    is_refusal,
)
from qmf.data.journal import JournalEventType
from qmf.data.journal_producer import JournalAppendReceipt, JournalReader, JournalWriter
from qmf.risk.door import (
    EntryIntent,
    ExitIntent,
    ExitKind,
    ExitLogicModule,
    ExitLogicRef,
    check_no_reopen,
)
from qmf.risk.exit_record import (
    CloseOutcome,
    CloseReason,
    ClosingAuthority,
    CostComponent,
    ExitRecord,
    ExitResultLabel,
    mint_exit_record,
)
from qmf.risk.paper import ExecutionTarget
from qmf.risk.r_faces import Direction, RFaces, admit_entry_r_faces, r_to_money
from qml.protocol import HostedBot

from qmb._refuse import clean_token, invalid, policy
from qmb.config.replay import ReplayBinding
from qmb.execution.binder import BoundExecution
from qmb.execution.fill import FillOrder, OrderType, path_ohlc, split_path_at
from qmb.execution.ports import CostedFill, Fill, NoFill, PartialFill, SlicePath
from qmb.execution.risk import admit_open
from qmb.results.measures import TradeSide
from qmb.runloop.loop import RestingIntent, SliceObservation

__all__ = [
    "BOOK_CLOSE_RECORD_REF_KEY",
    "BOOK_POSITION_CLASS",
    "BookAdmissionContext",
    "BookExecutionReceipt",
    "BookExecutionSliceHandler",
    "BookOrderPolicy",
    "ReplayPosition",
    "ReplayPositionRecovery",
    "derive_replay_quantity",
    "read_replay_positions",
]

BOOK_POSITION_CLASS: Final[str] = "qmb-replay-position"
BOOK_CLOSE_RECORD_REF_KEY: Final[str] = "exit_record_ref"
_CLOSE_BODY_KEY: Final[str] = "exit_record"


@dataclass(frozen=True, slots=True)
class BookAdmissionContext:
    """Every Book decision needed to size and journal one replay position.

    `requested_r` and `r_unit_price` are Book-resolved values. Quantity is derived
    from them, the CT-23 admitted full-loss distance, and `value_factor`; callers
    cannot inject a bot quantity. `close_reason_by_code` is an explicit Book policy
    maps are keyed by `entry:<family>:<code>` or `exit:<family>:<code>` and have no fallback.
    """

    binding: ReplayBinding
    exit_logic_ref: ExitLogicRef
    exit_logic_module: ExitLogicModule
    requested_r: ExactRational
    r_unit_price: ExactRational
    value_factor: ValueFactor
    money_scale: int
    lot_step: Quantity
    position_cap: Quantity
    execution_target: ExecutionTarget
    result_label: ExitResultLabel
    opening_bot_id: str
    close_reason_by_code: Mapping[str, CloseReason]
    order_policy_by_code: Mapping[str, BookOrderPolicy]
    journal_writer: JournalWriter

    @classmethod
    def try_create(
        cls,
        *,
        binding: object,
        exit_logic_ref: object,
        exit_logic_module: object,
        requested_r: object,
        r_unit_price: object,
        value_factor: object,
        money_scale: object,
        lot_step: object,
        position_cap: object,
        execution_target: object,
        result_label: object,
        opening_bot_id: object,
        close_reason_by_code: object,
        order_policy_by_code: object,
        journal_writer: object,
    ) -> Result[BookAdmissionContext]:
        """Validate the complete Book policy and persistence inputs."""
        if not isinstance(binding, ReplayBinding):
            return invalid("binding", "Book replay execution requires its minted ReplayBinding")
        if not isinstance(exit_logic_ref, ExitLogicRef):
            return invalid("exit_logic_ref", "Book policy supplies a typed ExitLogicRef")
        if not isinstance(exit_logic_module, ExitLogicModule):
            return invalid("exit_logic_module", "Book policy supplies its typed ExitLogicModule")
        if (
            not isinstance(requested_r, ExactRational)
            or requested_r.unit_kind.value != "r-multiple"
        ):
            return invalid("requested_r", "position size uses the Book-resolved r-multiple")
        if (
            not isinstance(r_unit_price, ExactRational)
            or r_unit_price.unit_kind.value != "rate(money-per-r)"
        ):
            return invalid("r_unit_price", "sizing requires the Book's exact money-per-R rate")
        if not isinstance(value_factor, ValueFactor):
            return invalid("value_factor", "position size requires instrument metadata ValueFactor")
        if isinstance(money_scale, bool) or not isinstance(money_scale, int) or money_scale < 0:
            return invalid("money_scale", "the Book declares an exact non-negative money scale")
        if not isinstance(lot_step, Quantity) or lot_step.as_fraction() <= 0:
            return invalid("lot_step", "position size requires a positive exact lot step")
        if not isinstance(position_cap, Quantity) or position_cap.unit != lot_step.unit:
            return invalid("position_cap", "the Book's positive cap shares the lot-step unit")
        if position_cap.as_fraction() <= 0:
            return invalid("position_cap", "the Book's position cap is positive")
        if not isinstance(execution_target, ExecutionTarget):
            return invalid("execution_target", "Book replay carries one explicit target")
        if not isinstance(result_label, ExitResultLabel):
            return invalid("result_label", "Book replay carries one explicit result label")
        if result_label.world is not World.REPLAY:
            return policy("result_label", "QMB Book execution is replay-only")
        if result_label.account_role is not execution_target.role:
            return policy("result_label", "result role and execution target role must agree")
        if binding.record.venue_id != execution_target.venue_id:
            return policy("execution_target", "execution target venue matches replay binding")
        if binding.record.account_id != execution_target.account_id:
            return policy("execution_target", "execution target account matches replay binding")
        if binding.record.world is not World.REPLAY:
            return policy("binding", "QMB Book handler cannot execute outside replay")
        if not isinstance(opening_bot_id, str) or not opening_bot_id.strip():
            return invalid("opening_bot_id", "whole-trade attribution names the opening Bot")
        if not isinstance(close_reason_by_code, Mapping) or not close_reason_by_code:
            return invalid("close_reason_by_code", "Book policy supplies explicit close reasons")
        reason_map: dict[str, CloseReason] = {}
        typed_reasons = cast(Mapping[object, object], close_reason_by_code)
        for key, reason in typed_reasons.items():
            if not isinstance(key, str) or not key.strip() or not isinstance(reason, CloseReason):
                return invalid("close_reason_by_code", "every reason mapping is typed and named")
            reason_map[key] = reason
        if not isinstance(order_policy_by_code, Mapping) or not order_policy_by_code:
            return invalid("order_policy_by_code", "Book policy declares typed order rules")
        order_map: dict[str, BookOrderPolicy] = {}
        typed_orders = cast(Mapping[object, object], order_policy_by_code)
        for key, order_rule in typed_orders.items():
            if (
                not isinstance(key, str)
                or not key.strip()
                or not isinstance(order_rule, BookOrderPolicy)
            ):
                return invalid("order_policy_by_code", "every order rule is typed and named")
            order_map[key] = order_rule
        if not isinstance(journal_writer, JournalWriter):
            return invalid("journal_writer", "CT-13 close evidence uses a JournalWriter")
        if journal_writer.world is not World.REPLAY:
            return policy("journal_writer", "CT-13 close stream must be in world=replay")
        if journal_writer.writer.stream != journal_writer.stream_name:
            return policy("journal_writer", "CT-13 writer identity must own its stream")
        return Ok(
            cls(
                binding=binding,
                exit_logic_ref=exit_logic_ref,
                exit_logic_module=exit_logic_module,
                requested_r=requested_r,
                r_unit_price=r_unit_price,
                value_factor=value_factor,
                money_scale=money_scale,
                lot_step=lot_step,
                position_cap=position_cap,
                execution_target=execution_target,
                result_label=result_label,
                opening_bot_id=opening_bot_id.strip(),
                close_reason_by_code=MappingProxyType(reason_map),
                order_policy_by_code=MappingProxyType(order_map),
                journal_writer=journal_writer,
            )
        )


@dataclass(frozen=True, slots=True)
class ReplayPosition:
    """One Book-owned replay position with admission, command and R-face identity."""

    position_ref: Fingerprint
    binding_epoch: Fingerprint
    admission_identity: Fingerprint
    command_identity: Fingerprint
    opening_bot_id: str
    instrument: str
    direction: Direction
    opened_at: Instant
    entry_price: Price
    quantity: Quantity
    faces: RFaces
    entry_fill_ref: Fingerprint
    entry_costs: tuple[CostComponent, ...]
    closed: bool = False

    def fp1_identity(self) -> dict[str, object]:
        """The canonical QMB replay-position identity, excluding later close state."""
        return {
            "admission_identity": self.admission_identity.value,
            "binding_epoch": self.binding_epoch.value,
            "class": BOOK_POSITION_CLASS,
            "command_identity": self.command_identity.value,
            "entry_fill_ref": self.entry_fill_ref.value,
            "entry_costs": [component.fp1_identity() for component in self.entry_costs],
            "entry_price": self.entry_price.fp1_identity(),
            "faces": self.faces.fp1_identity(),
            "instrument": self.instrument,
            "direction": self.direction.value,
            "opened_at": self.opened_at.fp1_identity(),
            "opening_bot_id": self.opening_bot_id,
            "position_ref": self.position_ref.value,
            "quantity": self.quantity.fp1_identity(),
        }


@dataclass(frozen=True, slots=True)
class BookOrderPolicy:
    """Pinned order-shape policy resolved by Book, never by QML/default."""

    order_type: OrderType
    limit_price: Price | None = None
    stop_price: Price | None = None
    trail_distance: PriceDelta | None = None
    trail_extreme: Price | None = None
    liquidity: Quantity | None = None
    fee_reference: str | None = None

    def fp1_identity(self) -> dict[str, object]:
        identity: dict[str, object] = {
            "class": "book-order-policy",
            "order_type": self.order_type.value,
        }
        for key, value in (
            ("limit_price", self.limit_price),
            ("stop_price", self.stop_price),
            ("trail_extreme", self.trail_extreme),
        ):
            if value is not None:
                identity[key] = value.fp1_identity()
        if self.trail_distance is not None:
            identity["trail_distance"] = self.trail_distance.fp1_identity()
        if self.liquidity is not None:
            identity["liquidity"] = self.liquidity.fp1_identity()
        if self.fee_reference is not None:
            identity["fee_reference"] = self.fee_reference
        return identity

    def materialize(
        self,
        *,
        side: Direction,
        quantity: Quantity,
        is_close: bool,
        lot_step: Quantity,
        position_quantity: Quantity | None,
        intent_id: str,
    ) -> Result[FillOrder]:
        """Create an exact order after Book admission has resolved the quantity."""
        return FillOrder.try_create(
            self.order_type,
            side,
            quantity,
            limit_price=self.limit_price,
            stop_price=self.stop_price,
            trail_distance=self.trail_distance,
            trail_extreme=self.trail_extreme,
            reduce_only=is_close,
            position_quantity=position_quantity,
            lot_step=lot_step,
            liquidity=self.liquidity,
            fee_reference=self.fee_reference,
            intent_id=intent_id,
        )


@dataclass(frozen=True, slots=True)
class BookExecutionReceipt:
    """The actual port outcome and any newly durable CT-29 close."""

    intent: EntryIntent | ExitIntent
    fill: CostedFill | NoFill
    position: ReplayPosition | None = None
    exit_record: ExitRecord | None = None
    journal_receipt: JournalAppendReceipt | None = None


@dataclass(frozen=True, slots=True)
class ReplayPositionRecovery:
    """A validated open/close fold over one CT-13 replay stream."""

    stream_name: str
    writer: WriterId
    binding_epoch: Fingerprint
    positions: tuple[ReplayPosition, ...]
    exit_records: tuple[ExitRecord, ...]
    high_water: int
    fingerprint: Fingerprint

    @property
    def record_resolver(self) -> Mapping[str, ExitRecord]:
        """Typed CT-29 records hydrated only from validated CT-13 close bodies."""
        resolved: dict[str, ExitRecord] = {}
        for record in self.exit_records:
            stamped = record.fingerprint()
            if not is_refusal(stamped):
                resolved[stamped.value.value] = record
        return MappingProxyType(resolved)

    @property
    def position_sides(self) -> Mapping[str, TradeSide]:
        """Original opening direction for every restored position, including closed."""
        return MappingProxyType(
            {
                position.position_ref.value: (
                    TradeSide.LONG if position.direction is Direction.LONG else TradeSide.SHORT
                )
                for position in self.positions
            }
        )

    def fp1_identity(self) -> dict[str, object]:
        """Identity of the validated stream fold, independent of runtime objects."""
        return {
            "binding_epoch": self.binding_epoch.value,
            "class": "qmb-replay-position-recovery",
            "high_water": self.high_water,
            "positions": [
                {"closed": position.closed, "position": position.fp1_identity()}
                for position in self.positions
            ],
            "stream_name": self.stream_name,
            "writer": _writer_identity(self.writer),
        }


def read_replay_positions(
    *,
    journal_reader: JournalReader,
    stream_name: str,
    writer: WriterId,
    binding_epoch: Fingerprint,
    result_label: ExitResultLabel,
    record_resolver: Mapping[str, ExitRecord] | None = None,
) -> Result[ReplayPositionRecovery]:
    """Restore QMB replay positions from validated CT-13 opens and CT-29 closes.

    The event stream is authoritative. Every open body must hash to its declared
    position ref; every close must resolve to a typed, fingerprint-matching CT-29
    record. A missing record, wrong writer/epoch/label, duplicate transition, or
    close without a prior witnessed open refuses recovery.
    """
    if not stream_name.strip():
        return invalid("stream", "recovery requires the exact CT-13 stream and WriterId")
    events = journal_reader.read_checked(stream_name, for_world=World.REPLAY)
    if is_refusal(events):
        return events
    positions: dict[str, ReplayPosition] = {}
    exit_records: dict[str, ExitRecord] = {}
    transitions: set[tuple[str, str]] = set()
    for event in events.value:
        if event.writer != writer:
            return policy("writer", "all replay-position evidence belongs to its declared writer")
        if event.event_type is not JournalEventType.RISK_TRANSITION:
            continue
        if event.payload.get("binding_epoch") != binding_epoch.value:
            # Unrelated risk transitions may coexist in a QMB CT-13 stream.
            if (
                "replay_position_ref" not in event.payload
                and BOOK_CLOSE_RECORD_REF_KEY not in event.payload
            ):
                continue
            return policy("binding_epoch", "replay-position transition matches recovery epoch")
        raw_position_ref = event.payload.get("replay_position_ref")
        if raw_position_ref is not None:
            raw_body = event.payload.get("replay_position")
            parsed_position = _restore_replay_position(raw_body)
            if is_refusal(parsed_position):
                return parsed_position
            position = parsed_position.value
            if position.position_ref.value != raw_position_ref:
                return policy("replay_position_ref", "open event ref equals position body identity")
            if position.binding_epoch != binding_epoch or position.opened_at != event.instant:
                return policy(
                    "replay_position",
                    "open identity epoch and Instant match its CT-13 witness",
                )
            key = position.position_ref.value
            transition = (key, "open")
            if transition in transitions or key in positions:
                return invalid(
                    "replay_position", "a replay position has one immutable open witness"
                )
            transitions.add(transition)
            positions[key] = position
            continue
        raw_close_ref = event.payload.get(BOOK_CLOSE_RECORD_REF_KEY)
        if raw_close_ref is None:
            continue
        if not isinstance(raw_close_ref, str):
            return invalid("exit_record_ref", "close transition names a fingerprint string")
        close_fp = Fingerprint.try_create(raw_close_ref)
        if is_refusal(close_fp):
            return close_fp
        raw_record_body = event.payload.get(_CLOSE_BODY_KEY)
        if not isinstance(raw_record_body, Mapping):
            return invalid("exit_record", "CT-13 close embeds the canonical CT-29 identity")
        resolved_record: ExitRecord | None = (record_resolver or {}).get(close_fp.value.value)
        if resolved_record is None:
            hydrated = _restore_exit_record(cast(Mapping[object, object], raw_record_body))
            if is_refusal(hydrated):
                return hydrated
            resolved_record = hydrated.value
        record = resolved_record
        actual_fp = record.fingerprint()
        if is_refusal(actual_fp):
            return actual_fp
        if actual_fp.value != close_fp.value:
            return policy("exit_record_ref", "resolved CT-29 record matches its CT-13 ref")
        raw_record_fp = fingerprint(dict(cast(Mapping[object, object], raw_record_body)))
        if is_refusal(raw_record_fp):
            return raw_record_fp
        expected_record_fp = fingerprint(record.fp1_identity())
        if is_refusal(expected_record_fp):
            return expected_record_fp
        if (
            record.binding_epoch != binding_epoch
            or record.result_label != result_label
            or record.recorded_at != event.instant
            or raw_record_fp.value != expected_record_fp.value
        ):
            return policy("exit_record", "CT-13 close body matches typed CT-29 record facts")
        raw_closed_ref = event.payload.get("virtual_position_ref")
        if (
            not isinstance(raw_closed_ref, str)
            or raw_closed_ref != record.virtual_position_ref.value
        ):
            return policy("virtual_position_ref", "close links its CT-29 virtual position")
        opened = positions.get(raw_closed_ref)
        if opened is None or opened.closed:
            return invalid("virtual_position_ref", "close resolves to one prior open witness")
        close_transition = (raw_closed_ref, "close")
        if close_transition in transitions:
            return invalid("virtual_position_ref", "one immutable CT-29 close exists per position")
        transitions.add(close_transition)
        exit_records[close_fp.value.value] = record
        positions[raw_closed_ref] = _closed_position(opened)
    restored = tuple(positions.values())
    high_water = events.value[-1].sequence if events.value else 0
    identity = {
        "binding_epoch": binding_epoch.value,
        "class": "qmb-replay-position-recovery",
        "high_water": high_water,
        "positions": [
            {"closed": position.closed, "position": position.fp1_identity()}
            for position in restored
        ],
        "stream_name": stream_name,
        "writer": _writer_identity(writer),
    }
    stamped = fingerprint(identity)
    if is_refusal(stamped):
        return stamped
    return Ok(
        ReplayPositionRecovery(
            stream_name=stream_name,
            writer=writer,
            binding_epoch=binding_epoch,
            positions=restored,
            exit_records=tuple(exit_records.values()),
            high_water=high_water,
            fingerprint=stamped.value,
        )
    )


def _restore_replay_position(raw: object) -> Result[ReplayPosition]:
    if not isinstance(raw, Mapping):
        return invalid("replay_position", "open witness carries a canonical position mapping")
    body = cast(Mapping[object, object], raw)
    try:
        if body.get("class") != BOOK_POSITION_CLASS:
            return invalid("replay_position", "position class is the pinned QMB replay class")
        position_ref = _parse_fingerprint(body.get("position_ref"), "position_ref")
        if is_refusal(position_ref):
            return position_ref
        epoch = _parse_fingerprint(body.get("binding_epoch"), "binding_epoch")
        if is_refusal(epoch):
            return epoch
        admission_ref = _parse_fingerprint(body.get("admission_identity"), "admission_identity")
        if is_refusal(admission_ref):
            return admission_ref
        command_ref = _parse_fingerprint(body.get("command_identity"), "command_identity")
        if is_refusal(command_ref):
            return command_ref
        fill_ref = _parse_fingerprint(body.get("entry_fill_ref"), "entry_fill_ref")
        if is_refusal(fill_ref):
            return fill_ref
        direction = Direction(body.get("direction"))
        instrument = body.get("instrument")
        opening_bot_id = body.get("opening_bot_id")
        if not isinstance(instrument, str) or not isinstance(opening_bot_id, str):
            return invalid("replay_position", "position instrument and opening Bot are strings")
        entry_price = _parse_price(body.get("entry_price"))
        quantity = _parse_quantity(body.get("quantity"))
        faces = _parse_faces(body.get("faces"))
        opened_at = _parse_instant(body.get("opened_at"))
        raw_costs = body.get("entry_costs")
        if not isinstance(raw_costs, (tuple, list)):
            return invalid("entry_costs", "position identity carries a cost-component list")
        costs: list[CostComponent] = []
        for raw_cost in cast(list[object] | tuple[object, ...], raw_costs):
            cost = _parse_cost(raw_cost)
            if is_refusal(cost):
                return cost
            costs.append(cost.value)
        if is_refusal(entry_price):
            return entry_price
        if is_refusal(quantity):
            return quantity
        if is_refusal(faces):
            return faces
        if is_refusal(opened_at):
            return opened_at
        position = ReplayPosition(
            position_ref=position_ref.value,
            binding_epoch=epoch.value,
            admission_identity=admission_ref.value,
            command_identity=command_ref.value,
            opening_bot_id=opening_bot_id,
            instrument=instrument,
            direction=direction,
            opened_at=opened_at.value,
            entry_price=entry_price.value,
            quantity=quantity.value,
            faces=faces.value,
            entry_fill_ref=fill_ref.value,
            entry_costs=tuple(costs),
        )
    except (TypeError, ValueError):
        return invalid("replay_position", "position identity fields are well-formed typed values")
    identity = position.fp1_identity()
    without_ref = {key: value for key, value in identity.items() if key != "position_ref"}
    expected = fingerprint(without_ref)
    if is_refusal(expected):
        return expected
    if expected.value != position.position_ref:
        return policy("position_ref", "recovered position identity hashes to its declared ref")
    recorded_body = dict(cast(Mapping[object, object], raw))
    recorded_body.pop("position_ref", None)
    recorded_identity = fingerprint(recorded_body)
    if is_refusal(recorded_identity):
        return recorded_identity
    if recorded_identity.value != expected.value:
        return policy("replay_position", "recovered fields reproduce the canonical identity")
    return Ok(position)


def _parse_fingerprint(raw: object, field_name: str) -> Result[Fingerprint]:
    if not isinstance(raw, str):
        return invalid(field_name, "identity fingerprint field is a string")
    return Fingerprint.try_create(raw)


def _writer_identity(writer: WriterId) -> dict[str, str]:
    return {
        "boot_epoch_id": writer.boot_epoch_id,
        "machine": writer.machine,
        "role": writer.role,
        "stream": writer.stream,
    }


def _empty_paths() -> Mapping[int, SlicePath]:
    return MappingProxyType({})


def _parse_instrument(raw: object) -> Result[Instrument]:
    if not isinstance(raw, Mapping):
        return invalid("instrument", "identity instrument is a mapping")
    value = cast(Mapping[object, object], raw)
    venue, symbol = value.get("venue"), value.get("symbol")
    if not isinstance(venue, str) or not isinstance(symbol, str):
        return invalid("instrument", "identity venue and symbol are strings")
    return Ok(Instrument(VenueId(venue), symbol))


def _scaled_parts(raw: object, field_name: str) -> Result[tuple[int, int]]:
    if not isinstance(raw, Mapping):
        return invalid(field_name, "exact value identity is a mapping")
    value = cast(Mapping[object, object], raw)
    numerator, denominator, scale = value.get("num"), value.get("den"), value.get("storage_scale")
    if (
        isinstance(numerator, bool)
        or not isinstance(numerator, int)
        or isinstance(denominator, bool)
        or not isinstance(denominator, int)
        or denominator <= 0
        or isinstance(scale, bool)
        or not isinstance(scale, int)
        or scale < 0
    ):
        return invalid(field_name, "exact value has integer numerator/denominator/storage scale")
    scaled = Fraction(numerator, denominator) * (10**scale)
    if scaled.denominator != 1:
        return invalid(field_name, "identity magnitude is representable at its declared scale")
    return Ok((scaled.numerator, scale))


def _parse_price(raw: object) -> Result[Price]:
    if not isinstance(raw, Mapping):
        return invalid("entry_price", "entry price identity is a mapping")
    value = cast(Mapping[object, object], raw)
    instrument = _parse_instrument(value.get("instrument"))
    parts = _scaled_parts(value, "entry_price")
    if is_refusal(instrument):
        return instrument
    if is_refusal(parts):
        return parts
    return Price.try_create(parts.value[0], instrument.value, parts.value[1])


def _parse_quantity(raw: object) -> Result[Quantity]:
    if not isinstance(raw, Mapping):
        return invalid("quantity", "position quantity identity is a mapping")
    value = cast(Mapping[object, object], raw)
    unit = value.get("unit")
    if not isinstance(unit, str):
        return invalid("quantity", "position quantity carries an opaque unit")
    parts = _scaled_parts(value, "quantity")
    if is_refusal(parts):
        return parts
    return Quantity.try_create(parts.value[0], unit, parts.value[1])


def _parse_money(raw: object) -> Result[Money]:
    if not isinstance(raw, Mapping):
        return invalid("money", "money identity is a mapping")
    value = cast(Mapping[object, object], raw)
    currency = value.get("currency")
    if not isinstance(currency, str):
        return invalid("money", "money identity names its currency")
    parts = _scaled_parts(value, "money")
    if is_refusal(parts):
        return parts
    return Money.try_create(parts.value[0], currency, parts.value[1])


def _parse_faces(raw: object) -> Result[RFaces]:
    if not isinstance(raw, Mapping):
        return invalid("faces", "R-face identity is a mapping")
    value = cast(Mapping[object, object], raw)
    distance_raw = value.get("original_risk_distance")
    amount_raw = value.get("original_risk_amount")
    if not isinstance(distance_raw, Mapping):
        return invalid("faces", "R-faces carry the frozen distance identity")
    distance_map = cast(Mapping[object, object], distance_raw)
    instrument = _parse_instrument(distance_map.get("instrument"))
    parts = _scaled_parts(distance_map, "original_risk_distance")
    amount = _parse_money(amount_raw)
    if is_refusal(instrument):
        return instrument
    if is_refusal(parts):
        return parts
    if is_refusal(amount):
        return amount
    distance = PriceDelta.try_create(parts.value[0], instrument.value, parts.value[1])
    if is_refusal(distance):
        return distance
    return RFaces.try_create(distance.value, amount.value)


def _parse_instant(raw: object) -> Result[Instant]:
    if not isinstance(raw, Mapping):
        return invalid("opened_at", "open Instant identity is a mapping")
    value = cast(Mapping[object, object], raw)
    ns = value.get("value_ns")
    return Instant.try_create(ns)


def _parse_cost(raw: object) -> Result[CostComponent]:
    if not isinstance(raw, Mapping):
        return invalid("entry_cost", "cost identity is a mapping")
    value = cast(Mapping[object, object], raw)
    amount = _parse_money(value.get("amount"))
    if is_refusal(amount):
        return amount
    return CostComponent.try_create(value.get("name"), amount.value, value.get("source"))


def _restore_exit_record(raw: object) -> Result[ExitRecord]:
    """Hydrate a typed CT-29 only from its complete canonical identity body."""
    if not isinstance(raw, Mapping):
        return invalid("exit_record", "CT-13 close body is a canonical CT-29 mapping")
    body = cast(Mapping[object, object], raw)
    if body.get("class") != "exit-record" or body.get("format_version") != 1:
        return invalid("exit_record", "CT-13 close body uses the pinned CT-29 format")
    distance_raw = body.get("original_risk_distance")
    if not isinstance(distance_raw, Mapping):
        return invalid("original_risk_distance", "CT-29 carries its frozen price distance")
    distance_map = cast(Mapping[object, object], distance_raw)
    instrument = _parse_instrument(distance_map.get("instrument"))
    distance_parts = _scaled_parts(distance_map, "original_risk_distance")
    amount = _parse_money(body.get("original_risk_amount"))
    realized = _parse_money(body.get("realized_pnl"))
    position_ref = _parse_fingerprint(body.get("virtual_position_ref"), "virtual_position_ref")
    epoch = _parse_fingerprint(body.get("binding_epoch"), "binding_epoch")
    instant = _parse_instant(body.get("recorded_at"))
    label_raw = body.get("result_label")
    if not isinstance(label_raw, Mapping):
        return invalid("result_label", "CT-29 carries typed result-label parts")
    label_map = cast(Mapping[object, object], label_raw)
    label = ExitResultLabel.try_create(label_map.get("account_role"), label_map.get("world"))
    if is_refusal(instrument):
        return instrument
    if is_refusal(distance_parts):
        return distance_parts
    if is_refusal(amount):
        return amount
    if is_refusal(realized):
        return realized
    if is_refusal(position_ref):
        return position_ref
    if is_refusal(epoch):
        return epoch
    if is_refusal(instant):
        return instant
    if is_refusal(label):
        return label
    distance = PriceDelta.try_create(
        distance_parts.value[0], instrument.value, distance_parts.value[1]
    )
    if is_refusal(distance):
        return distance
    raw_fills = body.get("fill_references")
    raw_costs = body.get("cost_components")
    if not isinstance(raw_fills, (list, tuple)) or not isinstance(raw_costs, (list, tuple)):
        return invalid("exit_record", "CT-29 fill references and costs are explicit sequences")
    fills: list[Fingerprint] = []
    typed_fills = cast(list[object] | tuple[object, ...], raw_fills)
    typed_costs = cast(list[object] | tuple[object, ...], raw_costs)
    for raw_fill in typed_fills:
        fill = _parse_fingerprint(raw_fill, "fill_references")
        if is_refusal(fill):
            return fill
        fills.append(fill.value)
    costs: list[CostComponent] = []
    for raw_cost in typed_costs:
        cost = _parse_cost(raw_cost)
        if is_refusal(cost):
            return cost
        costs.append(cost.value)
    raw_bot = body.get("opening_bot_id")
    if not isinstance(raw_bot, str):
        return invalid("opening_bot_id", "CT-29 retains the opening Bot identity")
    arbitration = body.get("arbitration_record_ref")
    venue_observation = body.get("venue_observation_ref")
    if arbitration is not None:
        arbitration = _parse_fingerprint(arbitration, "arbitration_record_ref")
        if is_refusal(arbitration):
            return arbitration
    if venue_observation is not None:
        venue_observation = _parse_fingerprint(venue_observation, "venue_observation_ref")
        if is_refusal(venue_observation):
            return venue_observation
    record = mint_exit_record(
        virtual_position_ref=position_ref.value,
        opening_bot_id=raw_bot,
        original_risk_distance=distance.value,
        original_risk_amount=amount.value,
        fill_references=tuple(fills),
        realized_pnl=realized.value,
        cost_components=tuple(costs),
        close_reason=body.get("close_reason"),
        mechanism=body.get("mechanism"),
        outcome=body.get("outcome"),
        closing_authority=body.get("closing_authority"),
        close_reason_mapping_version=body.get("close_reason_mapping_version"),
        result_label=label.value,
        loss_predicate_format_version=body.get("loss_predicate_format_version"),
        binding_epoch=epoch.value,
        recorded_at=instant.value,
        arbitration_record_ref=arbitration.value if arbitration is not None else None,
        venue_observation_ref=venue_observation.value if venue_observation is not None else None,
    )
    if is_refusal(record):
        return record
    hydrated_fp = fingerprint(record.value.fp1_identity())
    body_fp = fingerprint(dict(body))
    if is_refusal(hydrated_fp):
        return hydrated_fp
    if is_refusal(body_fp):
        return body_fp
    if hydrated_fp.value != body_fp.value:
        return policy("exit_record", "hydrated CT-29 reproduces the exact canonical body")
    return record


def _closed_position(position: ReplayPosition) -> ReplayPosition:
    return replace(position, closed=True)


def _aggregate_cost_components(
    components: tuple[CostComponent, ...],
) -> Result[tuple[CostComponent, ...]]:
    """Aggregate repeated close-lifecycle cost names without losing exact totals."""
    grouped: dict[str, CostComponent] = {}
    for component in components:
        previous = grouped.get(component.name)
        if previous is None:
            grouped[component.name] = component
            continue
        if previous.source != component.source:
            return policy(
                "cost_components",
                "repeated CT-29 cost names share their declared source for exact aggregation",
                name=component.name,
            )
        total = previous.amount.add(component.amount)
        if is_refusal(total):
            return total
        merged = CostComponent.try_create(component.name, total.value, component.source)
        if is_refusal(merged):
            return merged
        grouped[component.name] = merged.value
    return Ok(tuple(grouped.values()))


@dataclass(slots=True)
class BookExecutionSliceHandler:
    """QMB replay `SliceHandler` for a selected QL-7 bot and one Book policy."""

    hosted: HostedBot
    stream_id: str
    bound_execution: BoundExecution
    admission: BookAdmissionContext
    _path: SlicePath | None = None
    _paths_by_frontier: Mapping[int, SlicePath] = field(default_factory=_empty_paths)
    _positions: dict[str, ReplayPosition] = field(default_factory=dict[str, ReplayPosition])
    _closed: set[str] = field(default_factory=set[str])
    _receipts: list[BookExecutionReceipt] = field(default_factory=list[BookExecutionReceipt])

    @classmethod
    def try_create(
        cls,
        *,
        hosted: object,
        stream_id: object,
        bound_execution: object,
        admission: object,
        recovery: object,
    ) -> Result[BookExecutionSliceHandler]:
        """Bind a selected hosted bot to one declared Book execution policy."""
        token = clean_token(stream_id)
        if not isinstance(hosted, HostedBot):
            return invalid("hosted", "Book replay handler consumes the selected QL-7 HostedBot")
        if token is None:
            return invalid("stream_id", "the Book handler binds one declared stream")
        if not isinstance(bound_execution, BoundExecution):
            return invalid("bound_execution", "the handler consumes pinned BoundExecution ports")
        if not isinstance(admission, BookAdmissionContext):
            return invalid("admission", "every Book admission field is explicit and typed")
        if not isinstance(recovery, ReplayPositionRecovery):
            return invalid(
                "recovery",
                "startup requires a typed, validated CT-13 replay-position recovery result",
            )
        if bound_execution.config.replay_binding != admission.binding:
            return policy("binding", "BoundExecution and Book policy share the replay binding")
        if recovery.binding_epoch != admission.binding.fingerprint:
            return policy("recovery", "recovered positions belong to this replay binding epoch")
        if (
            recovery.stream_name != admission.journal_writer.stream_name
            or recovery.writer != admission.journal_writer.writer
        ):
            return policy("recovery", "recovery and CT-13 writer identify the same stream")
        recovered_fp = fingerprint(recovery.fp1_identity())
        if is_refusal(recovered_fp):
            return recovered_fp
        if recovered_fp.value != recovery.fingerprint:
            return policy("recovery", "position fold matches its recovery fingerprint")
        handler = cls(hosted, token, bound_execution, admission)
        for position in recovery.positions:
            key = position.position_ref.value
            if position.closed:
                handler._closed.add(key)
            else:
                if position.instrument in {item.instrument for item in handler._positions.values()}:
                    return policy(
                        "recovery", "recovered positions do not double-open an instrument"
                    )
                handler._positions[key] = position
        return Ok(handler)

    @property
    def positions(self) -> tuple[ReplayPosition, ...]:
        """Current open replay positions."""
        return tuple(self._positions.values())

    @property
    def receipts(self) -> tuple[BookExecutionReceipt, ...]:
        """Fill and close receipts observed by this handler."""
        return tuple(self._receipts)

    def bind_path(self, path: object) -> Result[None]:
        """Bind the source-materialized path for the next loop sub-phase."""
        if not isinstance(path, SlicePath) or path.stream_id != self.stream_id:
            return invalid("path", "the path is a typed source-bound SlicePath for this stream")
        self._path = path
        self._paths_by_frontier = MappingProxyType({})
        return Ok(None)

    def bind_paths(self, paths: object) -> Result[None]:
        """Bind source paths by exact slice Instant; no positional/fallback pairing."""
        if isinstance(paths, (str, bytes)) or not isinstance(paths, (tuple, list)) or not paths:
            return invalid(
                "paths", "source execution paths are non-empty (Instant, SlicePath) pairs"
            )
        keyed: dict[int, SlicePath] = {}
        typed_paths = cast(tuple[object, ...] | list[object], paths)
        for item in typed_paths:
            if not isinstance(item, tuple):
                return invalid("paths", "each source path entry is an (Instant, SlicePath) pair")
            pair = cast(tuple[object, ...], item)
            if len(pair) != 2:
                return invalid("paths", "each source path entry is an (Instant, SlicePath) pair")
            instant, path = pair[0], pair[1]
            if not isinstance(instant, Instant) or not isinstance(path, SlicePath):
                return invalid(
                    "paths", "each source path entry carries typed Instant and SlicePath"
                )
            if path.stream_id != self.stream_id:
                return policy("paths", "every materialized path belongs to the handler stream")
            if instant.value_ns in keyed:
                return invalid("paths", "one source path is bound to each slice Instant")
            keyed[instant.value_ns] = path
        self._path = None
        self._paths_by_frontier = MappingProxyType(keyed)
        return Ok(None)

    def mint_intents(self, stream_id: str, frontier: Instant) -> Result[tuple[RestingIntent, ...]]:
        """Drive the selected QL-7 callback and preserve typed CT-23 proposals."""
        if stream_id != self.stream_id:
            return Ok(())
        proposals = self.hosted.on_instant(frontier)
        if is_refusal(proposals):
            return proposals
        tokens: list[RestingIntent] = []
        for index, proposal in enumerate(proposals.value):
            reason_key = _policy_key(
                "entry" if isinstance(proposal, EntryIntent) else "exit", proposal
            )
            order_policy = self.admission.order_policy_by_code.get(reason_key)
            if order_policy is None:
                return invalid(
                    "order_policy",
                    "Book has no explicit order rule for this CT-23 reason code",
                    reason_code=reason_key,
                )
            stamped = fingerprint(proposal.fp1_identity())
            if is_refusal(stamped):
                return stamped
            token = RestingIntent.try_create(
                f"{stamped.value.value}:{index}",
                stream_id,
                order=order_policy,
                proposal=proposal,
            )
            if is_refusal(token):
                return token
            tokens.append(token.value)
        return Ok(tuple(tokens))

    def execute_resting(
        self,
        intent: RestingIntent,
        observation: SliceObservation | None,
        frontier: Instant,
    ) -> Result[bool]:
        """Execute one CT-23 proposal; only actual full fills change position state."""
        if intent.stream_id != self.stream_id:
            return Ok(False)
        if observation is not None and (
            observation.stream_id != self.stream_id or not observation.closed
        ):
            return policy("observation", "Book orders execute only on this stream's closed slice")
        instant = observation.instant if observation is not None else frontier
        path = self._paths_by_frontier.get(instant.value_ns, self._path)
        if path is None:
            return invalid(
                "path",
                "an exact source path must be bound to the current replay slice before fill",
                instant_ns=instant.value_ns,
            )
        proposal = intent.proposal
        if isinstance(proposal, EntryIntent):
            receipt = self._open(proposal, path, frontier, intent)
        elif isinstance(proposal, ExitIntent):
            receipt = self._close(proposal, path, frontier, intent)
        else:
            return invalid("proposal", "resting Book execution carries a typed CT-23 proposal")
        if is_refusal(receipt):
            return receipt
        self._receipts.append(receipt.value)
        if isinstance(receipt.value.fill, NoFill):
            return Ok(False)
        price = _fill_price(receipt.value.fill.fill)
        if is_refusal(price):
            return price
        split = split_path_at(path, price.value)
        if is_refusal(split):
            return split
        if instant.value_ns in self._paths_by_frontier:
            paths_by_frontier = dict(self._paths_by_frontier)
            paths_by_frontier[instant.value_ns] = split.value
            self._paths_by_frontier = MappingProxyType(paths_by_frontier)
        else:
            self._path = split.value
        return Ok(True)

    def _open(
        self, intent: EntryIntent, path: SlicePath, at: Instant, resting: RestingIntent
    ) -> Result[BookExecutionReceipt]:
        context = self.admission
        if intent.execution_target != context.execution_target:
            return policy(
                "execution_target", "the bot proposal target matches its pinned Book target"
            )
        if any(
            position.instrument == intent.instrument.symbol for position in self._positions.values()
        ):
            return policy(
                "has_open_position", "Book V1 refuses a second open position on the instrument"
            )
        if intent.instrument != context.value_factor.instrument:
            return policy("instrument", "the Book ValueFactor is pinned to this intent instrument")
        path_prices = path_ohlc(path)
        if is_refusal(path_prices):
            return path_prices
        entry_price = path_prices.value[0]
        admitted = _admit(context, intent, entry_price)
        if is_refusal(admitted):
            return admitted
        quantity = derive_replay_quantity(
            admitted.value.original_risk_distance,
            context.requested_r,
            context.r_unit_price,
            context.value_factor,
            context.money_scale,
            context.lot_step,
            context.position_cap,
        )
        if is_refusal(quantity):
            return quantity
        faces = admit_entry_r_faces(
            entry_price,
            admitted.value.declared_full_loss_price,
            intent.direction,
            quantity.value,
            context.value_factor,
            money_scale=context.money_scale,
        )
        if is_refusal(faces):
            return faces
        target = r_to_money(context.requested_r, context.r_unit_price, scale=context.money_scale)
        if is_refusal(target):
            return target
        if faces.value.original_risk_amount != target.value:
            return policy(
                "position_quantity",
                "planned CT-23 RFaces equal the Book R budget before slippage",
            )
        reason_key = _policy_key("entry", intent)
        order_policy = context.order_policy_by_code.get(reason_key)
        if order_policy is None:
            return invalid(
                "order_policy", "Book has no explicit order rule for this CT-23 entry reason code"
            )
        order = order_policy.materialize(
            side=intent.direction,
            quantity=quantity.value,
            is_close=False,
            lot_step=context.lot_step,
            position_quantity=None,
            intent_id=resting.intent_id,
        )
        if is_refusal(order):
            return order
        fill = contextual_execute(
            self.bound_execution,
            intent=intent,
            path=path,
            quantity=quantity.value,
            context=context,
            order=order.value,
            entry_price=entry_price,
        )
        if is_refusal(fill):
            return fill
        if isinstance(fill.value, NoFill):
            return Ok(BookExecutionReceipt(intent=intent, fill=fill.value))
        if isinstance(fill.value.fill, PartialFill):
            return invalid(
                "partial_entry",
                "partial-entry reservation persistence is being completed; no position is minted",
            )
        if fill.value.fill.quantity != quantity.value:
            return policy("fill_quantity", "a full replay fill equals the admitted exact quantity")
        actual_entry_price = _fill_price(fill.value.fill)
        if is_refusal(actual_entry_price):
            return actual_entry_price
        fill_identity = fingerprint(fill.value.fp1_identity())
        if is_refusal(fill_identity):
            return fill_identity
        admission_identity = fingerprint(admitted.value.fp1_identity())
        if is_refusal(admission_identity):
            return admission_identity
        command_identity = fingerprint(
            {
                "admission_identity": admission_identity.value.value,
                "binding_epoch": context.binding.fingerprint.value,
                "class": "qmb-replay-command",
                "fill_identity": fill_identity.value.value,
                "intent_identity": intent.fp1_identity(),
                "resting_identity": resting.fp1_identity(),
            }
        )
        if is_refusal(command_identity):
            return command_identity
        pos_identity: dict[str, object] = {
            "admission_identity": admission_identity.value.value,
            "binding_epoch": context.binding.fingerprint.value,
            "class": BOOK_POSITION_CLASS,
            "command_identity": command_identity.value.value,
            "direction": intent.direction.value,
            "entry_costs": [component.fp1_identity() for component in fill.value.costs],
            "entry_fill_ref": fill_identity.value.value,
            "entry_price": actual_entry_price.value.fp1_identity(),
            "faces": faces.value.fp1_identity(),
            "instrument": intent.instrument.symbol,
            "opened_at": at.fp1_identity(),
            "opening_bot_id": context.opening_bot_id,
            "quantity": quantity.value.fp1_identity(),
        }
        position_ref = fingerprint(pos_identity)
        if is_refusal(position_ref):
            return position_ref
        position = ReplayPosition(
            position_ref=position_ref.value,
            binding_epoch=context.binding.fingerprint,
            admission_identity=admission_identity.value,
            command_identity=command_identity.value,
            opening_bot_id=context.opening_bot_id,
            instrument=intent.instrument.symbol,
            direction=intent.direction,
            opened_at=at,
            entry_price=actual_entry_price.value,
            quantity=fill.value.fill.quantity,
            faces=faces.value,
            entry_fill_ref=fill_identity.value,
            entry_costs=fill.value.costs,
        )
        witness = self._append_position_event(position, at)
        if is_refusal(witness):
            return witness
        self._positions[position_ref.value.value] = position
        return Ok(BookExecutionReceipt(intent=intent, fill=fill.value, position=position))

    def _close(
        self, intent: ExitIntent, path: SlicePath, at: Instant, resting: RestingIntent
    ) -> Result[BookExecutionReceipt]:
        context = self.admission
        key = intent.virtual_position_ref.value
        if key in self._closed:
            checked = check_no_reopen(position_is_closed=True)
            return (
                checked if is_refusal(checked) else invalid("position", "closed ref cannot reopen")
            )
        position = self._positions.get(key)
        if position is None:
            return invalid("virtual_position_ref", "exit resolves to an open Book replay position")
        if intent.kind is not ExitKind.CLOSE_FULL:
            return invalid("exit_kind", "QMB replay close journaling requires full-close intent")
        reason_key = _policy_key("exit", intent)
        reason = context.close_reason_by_code.get(reason_key)
        order_policy = context.order_policy_by_code.get(reason_key)
        if reason is None:
            return invalid(
                "close_reason",
                "opaque CT-23 exit reason needs explicit Book CloseReason mapping",
            )
        if order_policy is None:
            return invalid(
                "order_policy",
                "Book has no explicit close order rule for this CT-23 exit reason code",
            )
        close_side = Direction.SHORT if position.direction is Direction.LONG else Direction.LONG
        order = order_policy.materialize(
            side=close_side,
            quantity=position.quantity,
            is_close=True,
            lot_step=context.lot_step,
            position_quantity=position.quantity,
            intent_id=resting.intent_id,
        )
        if is_refusal(order):
            return order
        evaluated = self.bound_execution.execute(
            intent=intent,
            path=path,
            requested_quantity=position.quantity,
            position_cap=context.position_cap,
            lot_step=context.lot_step,
            order=order.value,
        )
        if is_refusal(evaluated):
            return evaluated
        if isinstance(evaluated.value, NoFill):
            return Ok(BookExecutionReceipt(intent=intent, fill=evaluated.value, position=position))
        if isinstance(evaluated.value.fill, PartialFill):
            return invalid(
                "partial_close",
                "partial-close state is not yet supported; CT-29 is not minted",
            )
        actual_fill = evaluated.value.fill
        if actual_fill.quantity != position.quantity:
            return policy("quantity", "close fill quantity equals the complete virtual position")
        price = _fill_price(actual_fill)
        if is_refusal(price):
            return price
        signed_delta = (
            price.value.subtract(position.entry_price)
            if position.direction is Direction.LONG
            else position.entry_price.subtract(price.value)
        )
        if is_refusal(signed_delta):
            return signed_delta
        gross = signed_delta.value.to_money(
            context.value_factor, position.quantity, scale=context.money_scale
        )
        if is_refusal(gross):
            return gross
        fill_ref = fingerprint(evaluated.value.fp1_identity())
        if is_refusal(fill_ref):
            return fill_ref
        costed_result = _aggregate_cost_components((*position.entry_costs, *evaluated.value.costs))
        if is_refusal(costed_result):
            return costed_result
        costed = costed_result.value
        net = gross.value
        for component in costed:
            netted = net.subtract(component.amount)
            if is_refusal(netted):
                return netted
            net = netted.value
        outcome = (
            CloseOutcome.GAIN
            if net.value > 0
            else CloseOutcome.LOSS
            if net.value < 0
            else CloseOutcome.BREAKEVEN
        )
        close_command = fingerprint(
            {
                "binding_epoch": context.binding.fingerprint.value,
                "class": "qmb-replay-close-command",
                "exit_intent": intent.fp1_identity(),
                "fill_identity": fill_ref.value.value,
                "position_ref": position.position_ref.value,
                "resting_identity": resting.fp1_identity(),
            }
        )
        if is_refusal(close_command):
            return close_command
        record = mint_exit_record(
            virtual_position_ref=position.position_ref,
            opening_bot_id=position.opening_bot_id,
            original_risk_distance=position.faces.original_risk_distance,
            original_risk_amount=position.faces.original_risk_amount,
            fill_references=(position.entry_fill_ref, fill_ref.value),
            realized_pnl=gross.value,
            cost_components=tuple(costed),
            close_reason=reason,
            mechanism=reason,
            outcome=outcome,
            closing_authority=ClosingAuthority.BOOK_POLICY,
            close_reason_mapping_version=1,
            result_label=context.result_label,
            loss_predicate_format_version=1,
            binding_epoch=context.binding.fingerprint,
            recorded_at=at,
            arbitration_record_ref=close_command.value,
        )
        if is_refusal(record):
            return record
        fp = record.value.fingerprint()
        if is_refusal(fp):
            return fp
        journaled = context.journal_writer.record(
            JournalEventType.RISK_TRANSITION,
            {
                "binding_epoch": context.binding.fingerprint.value,
                _CLOSE_BODY_KEY: record.value.fp1_identity(),
                BOOK_CLOSE_RECORD_REF_KEY: fp.value.value,
                "virtual_position_ref": position.position_ref.value,
            },
            instant=at,
        )
        if is_refusal(journaled):
            return journaled
        self._positions.pop(key)
        self._closed.add(key)
        closed = ReplayPosition(
            position_ref=position.position_ref,
            binding_epoch=position.binding_epoch,
            admission_identity=position.admission_identity,
            command_identity=position.command_identity,
            opening_bot_id=position.opening_bot_id,
            instrument=position.instrument,
            direction=position.direction,
            opened_at=position.opened_at,
            entry_price=position.entry_price,
            quantity=position.quantity,
            faces=position.faces,
            entry_fill_ref=position.entry_fill_ref,
            entry_costs=position.entry_costs,
            closed=True,
        )
        return Ok(
            BookExecutionReceipt(
                intent=intent,
                fill=evaluated.value,
                position=closed,
                exit_record=record.value,
                journal_receipt=journaled.value,
            )
        )

    def _append_position_event(
        self, position: ReplayPosition, at: Instant
    ) -> Result[JournalAppendReceipt]:
        """Write the opening virtual-position witness before later close interpretation."""
        # The caller adds this position to memory only after the witness append succeeds.
        return self.admission.journal_writer.record(
            JournalEventType.RISK_TRANSITION,
            {
                "binding_epoch": position.binding_epoch.value,
                "replay_position": position.fp1_identity(),
                "replay_position_ref": position.position_ref.value,
            },
            instant=at,
        )


def _admit(context: BookAdmissionContext, intent: EntryIntent, entry_price: Price):
    return admit_open(
        context.binding,
        intent=intent,
        entry_price=entry_price,
        exit_logic_ref=context.exit_logic_ref,
        module=context.exit_logic_module,
        book_resolved_requested_r=context.requested_r,
        has_open_position=False,
    )


def derive_replay_quantity(
    distance: object,
    requested_r: ExactRational,
    r_unit_price: ExactRational,
    value_factor: ValueFactor,
    money_scale: int,
    lot_step: Quantity,
    position_cap: Quantity,
) -> Result[Quantity]:
    """Derive exact Book position size; never round a lot-step remainder."""
    if not isinstance(distance, PriceDelta):
        return invalid("original_risk_distance", "CT-23 admission supplies PriceDelta")
    target = r_to_money(requested_r, r_unit_price, scale=money_scale)
    if is_refusal(target):
        return target
    one = Quantity.try_create(1, lot_step.unit, 0)
    if is_refusal(one):
        return one
    unit_risk = distance.to_money(value_factor, one.value, scale=money_scale)
    if is_refusal(unit_risk):
        return unit_risk
    if unit_risk.value.as_fraction() <= 0:
        return invalid("value_factor", "one lot-step unit carries positive full-loss risk")
    wanted = target.value.as_fraction() / unit_risk.value.as_fraction()
    step_units = wanted / lot_step.as_fraction()
    if step_units.denominator != 1:
        return invalid(
            "lot_step",
            "Book risk amount must map exactly to an integer multiple of its declared lot step",
            wanted=str(wanted),
            lot_step=str(lot_step.as_fraction()),
        )
    if wanted > position_cap.as_fraction():
        return policy("position_cap", "exact risk-derived quantity exceeds the Book cap")
    scaled = wanted * (10**lot_step.scale)
    if scaled.denominator != 1:
        return invalid(
            "lot_step", "risk-derived size is not exactly representable at lot-step scale"
        )
    return Quantity.try_create(scaled.numerator, lot_step.unit, lot_step.scale)


def contextual_execute(
    bound: BoundExecution,
    *,
    intent: EntryIntent,
    path: SlicePath,
    quantity: Quantity,
    context: BookAdmissionContext,
    order: object,
    entry_price: Price,
) -> Result[CostedFill | NoFill]:
    """Invoke the existing bound execution path with only the exact derived size."""
    return bound.execute(
        intent=intent,
        path=path,
        requested_quantity=quantity,
        position_cap=context.position_cap,
        lot_step=context.lot_step,
        entry_price=entry_price,
        exit_logic_ref=context.exit_logic_ref,
        module=context.exit_logic_module,
        book_resolved_requested_r=context.requested_r,
        order=order,
    )


def _fill_price(fill: Fill | PartialFill) -> Result[Price]:
    return Ok(fill.post_slip_price or fill.pre_slip_price)


def _policy_key(intent_kind: str, intent: EntryIntent | ExitIntent) -> str:
    """Book order policy is pinned by intent class plus its Book-owned reason."""
    return f"{intent_kind}:{intent.reason_code.book_family}:{intent.reason_code.code}"
