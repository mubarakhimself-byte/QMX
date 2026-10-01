"""Book-side replay admission, exact position sizing and CT-29 close journaling.

The handler is an application-layer replay composition root. It consumes CT-23
proposals, resolves size through the declared R-unit/value-factor inputs, executes
the bound fill/slippage/cost ports, and records a CT-29 close before returning it.
It never creates venue positions or maps an opaque reason code by guesswork.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
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
from qmf.data.journal import DecisionOutcome, JournalEvent, JournalEventType
from qmf.data.journal_producer import JournalAppendReceipt, JournalReader, JournalWriter
from qmf.data.store import RoomRole, StoreReceipt, WriteOutcome
from qmf.risk.door import (
    AdmittedEntry,
    EntryIntent,
    ExitIntent,
    ExitKind,
    ExitLogicModule,
    ExitLogicRef,
    ReasonCode,
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
from qmb.execution.fill import (
    FillOrder,
    OrderType,
    entry_reference_price,
    split_path_at,
)
from qmb.execution.financing import (
    FinancingCashEvent,
    OpenPosition,
    RolloverCalendar,
    apply_financing_rollover,
)
from qmb.execution.ports import CostedFill, Fill, NoFill, PartialFill, SlicePath
from qmb.execution.risk import admit_open
from qmb.results.measures import TradeSide
from qmb.runloop.loop import (
    ExecutionDisposition,
    RestingIntent,
    RestingTerminalCause,
    RestingTerminalDisposition,
    SliceObservation,
)

__all__ = [
    "BOOK_CLOSE_RECORD_REF_KEY",
    "BOOK_POSITION_CLASS",
    "BookAdmissionContext",
    "BookExecutionReceipt",
    "BookExecutionSliceHandler",
    "BookOrderPolicy",
    "EntryTerminalReason",
    "ReplayEntryFill",
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
    journal_reader: JournalReader
    rollover_calendar: RolloverCalendar
    protective_stop_reason: ReasonCode

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
        journal_reader: object,
        rollover_calendar: object,
        protective_stop_reason: object,
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
        if not isinstance(journal_reader, JournalReader):
            return invalid(
                "journal_reader", "CT-13 memory advances require physical JournalReader readback"
            )
        if not isinstance(rollover_calendar, RolloverCalendar):
            return invalid(
                "rollover_calendar",
                "Book financing uses the explicit bound broker accounting-rollover calendar",
            )
        if not isinstance(protective_stop_reason, ReasonCode):
            return invalid(
                "protective_stop_reason",
                "the Book pins a typed reason for its declared-loss stop close",
            )
        stop_key = _reason_policy_key("exit", protective_stop_reason)
        if stop_key not in reason_map or stop_key not in order_map:
            return invalid(
                "protective_stop_policy",
                "the configured stop reason has explicit close-reason and order policies",
            )
        if order_map[stop_key].order_type is not OrderType.STOP:
            return invalid(
                "protective_stop_policy",
                "the declared-loss reason is governed by an explicit STOP order policy",
            )
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
                journal_reader=journal_reader,
                rollover_calendar=rollover_calendar,
                protective_stop_reason=protective_stop_reason,
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
    protective_stop: Price
    entry_terminal_reason: EntryTerminalReason
    quantity: Quantity
    faces: RFaces
    entry_fill_ref: Fingerprint
    entry_costs: tuple[CostComponent, ...]
    closed: bool = False
    entry_fills: tuple[ReplayEntryFill, ...] = ()
    declared_plan_quantity: Quantity | None = None
    declared_plan_risk_amount: Money | None = None
    risk_rebased: bool = False
    risk_rebase_lineage: Fingerprint | None = None
    financing_costs: tuple[CostComponent, ...] = ()
    financing_rollovers: tuple[Fingerprint, ...] = ()

    @property
    def entry_fill_refs(self) -> tuple[Fingerprint, ...]:
        return tuple(fill.fill_ref for fill in self.entry_fills) or (self.entry_fill_ref,)

    def fp1_identity(self) -> dict[str, object]:
        """The canonical QMB replay-position identity, excluding later close state."""
        identity: dict[str, object] = {
            "admission_identity": self.admission_identity.value,
            "binding_epoch": self.binding_epoch.value,
            "class": BOOK_POSITION_CLASS,
            "command_identity": self.command_identity.value,
            "entry_fill_ref": self.entry_fill_ref.value,
            "entry_costs": [component.fp1_identity() for component in self.entry_costs],
            "entry_price": self.entry_price.fp1_identity(),
            "protective_stop": self.protective_stop.fp1_identity(),
            "entry_terminal_reason": self.entry_terminal_reason.value,
            "faces": self.faces.fp1_identity(),
            "instrument": self.instrument,
            "direction": self.direction.value,
            "opened_at": self.opened_at.fp1_identity(),
            "opening_bot_id": self.opening_bot_id,
            "position_ref": self.position_ref.value,
            "quantity": self.quantity.fp1_identity(),
        }
        if self.entry_fills:
            identity["entry_fills"] = [fill.fp1_identity() for fill in self.entry_fills]
        if self.declared_plan_quantity is not None:
            identity["declared_plan_quantity"] = self.declared_plan_quantity.fp1_identity()
        if self.declared_plan_risk_amount is not None:
            identity["declared_plan_risk_amount"] = self.declared_plan_risk_amount.fp1_identity()
        if self.risk_rebased:
            identity["risk_rebased"] = True
        if self.risk_rebase_lineage is not None:
            identity["risk_rebase_lineage"] = self.risk_rebase_lineage.value
        return identity


class EntryTerminalReason(StrEnum):
    """Typed lifecycle boundary that seals an admitted replay entry."""

    REPLAY_COMPLETE = "replay_complete"
    CANCELLED = "cancelled"
    PROTECTIVE_STOP = "protective_stop"


@dataclass(frozen=True, slots=True)
class ReplayEntryFill:
    """One actual costed entry fill, retained for exact multi-fill economics."""

    fill_ref: Fingerprint
    quantity: Quantity
    price: Price
    costs: tuple[CostComponent, ...]
    instant: Instant

    def fp1_identity(self) -> dict[str, object]:
        return {
            "class": "qmb-replay-entry-fill",
            "costs": [cost.fp1_identity() for cost in self.costs],
            "fill_ref": self.fill_ref.value,
            "instant": self.instant.fp1_identity(),
            "price": self.price.fp1_identity(),
            "quantity": self.quantity.fp1_identity(),
        }


@dataclass(frozen=True, slots=True)
class _PendingEntry:
    ticket: Fingerprint
    intent_ref: Fingerprint
    intent: EntryIntent
    admission: AdmittedEntry
    admission_identity: Fingerprint
    planned_quantity: Quantity
    planned_faces: RFaces
    resting_intent_id: str
    fills: tuple[ReplayEntryFill, ...] = ()
    financing_costs: tuple[CostComponent, ...] = ()
    financing_rollovers: tuple[Fingerprint, ...] = ()


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
    entry_ticket: Fingerprint | None = None


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
                {
                    "closed": position.closed,
                    "financing_costs": [item.fp1_identity() for item in position.financing_costs],
                    "financing_rollovers": [item.value for item in position.financing_rollovers],
                    "position": position.fp1_identity(),
                }
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
    pending_entry_refs: dict[str, list[str]] = {}
    pending_entry_fills: dict[str, list[ReplayEntryFill]] = {}
    pending_financing: dict[str, tuple[list[CostComponent], list[Fingerprint]]] = {}
    transitions: set[tuple[str, str]] = set()
    for event in events.value:
        if (
            event.writer.machine != writer.machine
            or event.writer.role != writer.role
            or event.writer.stream != writer.stream
        ):
            return policy(
                "writer",
                "replay-position evidence belongs to the declared writer-scoped stream",
            )
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
        if event.payload.get("kind") == "financing":
            raw_position = event.payload.get("virtual_position_ref")
            raw_financing = event.payload.get("financing_event")
            if not isinstance(raw_position, str) or not isinstance(raw_financing, Mapping):
                return invalid("financing_event", "financing witness carries position and body")
            position = positions.get(raw_position)
            financing_body = cast(Mapping[object, object], raw_financing)
            component = _parse_cost(financing_body.get("component"))
            amount = _parse_money(financing_body.get("amount"))
            raw_trading_date = financing_body.get("trading_date")
            if not isinstance(raw_trading_date, Mapping):
                return invalid("trading_date", "financing witness carries its calendar date")
            rollover_ref = fingerprint(dict(cast(Mapping[object, object], raw_trading_date)))
            if is_refusal(rollover_ref):
                return rollover_ref
            if is_refusal(component):
                return component
            if is_refusal(amount):
                return amount
            if component.value.amount != amount.value:
                return policy("financing_event", "cost component amount matches cash amount")
            cost = _book_financing_cost(component.value, amount.value)
            if is_refusal(cost):
                return cost
            if position is not None:
                if position.closed:
                    return invalid("financing_event", "cash event names one prior open position")
                if rollover_ref.value in position.financing_rollovers:
                    return invalid(
                        "financing_event", "one position is charged once per trading date"
                    )
                positions[raw_position] = replace(
                    position,
                    financing_costs=(*position.financing_costs, cost.value),
                    financing_rollovers=(*position.financing_rollovers, rollover_ref.value),
                )
            else:
                pending_ticket_matches: list[str] = []
                for ticket, fills in pending_entry_fills.items():
                    if not fills:
                        continue
                    ticket_fp = Fingerprint.try_create(ticket)
                    if is_refusal(ticket_fp):
                        return ticket_fp
                    stable_ref = _replay_position_ref(ticket_fp.value, binding_epoch)
                    if is_refusal(stable_ref):
                        return stable_ref
                    if stable_ref.value.value == raw_position:
                        pending_ticket_matches.append(ticket)
                pending_tickets = tuple(pending_ticket_matches)
                if len(pending_tickets) != 1:
                    return invalid(
                        "financing_event", "cash event identifies one witnessed partial entry"
                    )
                costs, dates = pending_financing.setdefault(raw_position, ([], []))
                if rollover_ref.value in dates:
                    return invalid(
                        "financing_event", "one partial position is charged once per date"
                    )
                costs.append(cost.value)
                dates.append(rollover_ref.value)
            continue
        raw_entry_ref = event.payload.get("replay_entry_fill_ref")
        if raw_entry_ref is not None:
            raw_ticket = event.payload.get("replay_entry_ticket")
            raw_fill = event.payload.get("replay_entry_fill")
            raw_virtual_ref = event.payload.get("virtual_position_ref")
            if not isinstance(raw_ticket, str) or not isinstance(raw_fill, Mapping):
                return invalid("replay_entry_fill", "partial-fill witness carries ticket and body")
            ticket = _parse_fingerprint(raw_ticket, "replay_entry_ticket")
            restored_fill = _restore_replay_entry_fill(cast(Mapping[object, object], raw_fill))
            if is_refusal(ticket):
                return ticket
            if is_refusal(restored_fill):
                return restored_fill
            if restored_fill.value.fill_ref.value != raw_entry_ref:
                return policy("replay_entry_fill_ref", "partial fill ref matches its typed body")
            expected_position_ref = _replay_position_ref(ticket.value, binding_epoch)
            if is_refusal(expected_position_ref):
                return expected_position_ref
            if raw_virtual_ref != expected_position_ref.value.value:
                return policy(
                    "virtual_position_ref",
                    "partial fill is bound to its stable admission-derived position identity",
                )
            refs = pending_entry_refs.setdefault(ticket.value.value, [])
            if restored_fill.value.fill_ref.value in refs:
                return invalid("replay_entry_fill_ref", "one partial fill witness is recorded once")
            refs.append(restored_fill.value.fill_ref.value)
            pending_entry_fills.setdefault(ticket.value.value, []).append(restored_fill.value)
            continue
        raw_position_ref = event.payload.get("replay_position_ref")
        if raw_position_ref is not None:
            raw_body = event.payload.get("replay_position")
            raw_state_fp = event.payload.get("replay_position_fingerprint")
            if not isinstance(raw_body, Mapping):
                return invalid(
                    "replay_position", "open witness carries a canonical position mapping"
                )
            state_identity = cast(
                dict[object, object], _canonical_plain(cast(Mapping[object, object], raw_body))
            )
            state_identity.pop("position_ref", None)
            state_fp = fingerprint(state_identity)
            if is_refusal(state_fp):
                return state_fp
            if raw_state_fp != state_fp.value.value:
                return policy(
                    "replay_position_fingerprint",
                    "open witness preserves the exact terminal position state under its stable ref",
                    expected=raw_state_fp,
                    actual=state_fp.value.value,
                )
            parsed_position = _restore_replay_position(cast(Mapping[object, object], raw_body))
            if is_refusal(parsed_position):
                return parsed_position
            position = parsed_position.value
            if position.position_ref.value != raw_position_ref:
                return policy("replay_position_ref", "open event ref equals position body identity")
            if (
                position.binding_epoch != binding_epoch
                or position.opened_at.value_ns > event.instant.value_ns
            ):
                return policy(
                    "replay_position",
                    "open identity epoch matches and terminal witness follows its first fill",
                )
            raw_ticket = event.payload.get("replay_entry_ticket")
            if raw_ticket is not None:
                ticket = _parse_fingerprint(raw_ticket, "replay_entry_ticket")
                if is_refusal(ticket):
                    return ticket
                prior_refs = pending_entry_refs.pop(ticket.value.value, [])
                prior_fills = pending_entry_fills.pop(ticket.value.value, [])
                if prior_refs and tuple(prior_refs) != tuple(
                    fill.value for fill in position.entry_fill_refs
                ):
                    return policy(
                        "replay_entry_fill_refs",
                        "terminal position seals exactly its witnessed partial fills",
                    )
                if prior_fills and tuple(prior_fills) != position.entry_fills:
                    return policy(
                        "replay_entry_fills",
                        "terminal position preserves the exact witnessed actual fills",
                    )
            deferred_costs, deferred_dates = pending_financing.pop(
                position.position_ref.value, ([], [])
            )
            if deferred_costs:
                position = replace(
                    position,
                    financing_costs=(*position.financing_costs, *deferred_costs),
                    financing_rollovers=(*position.financing_rollovers, *deferred_dates),
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
    if pending_entry_refs or pending_financing:
        return policy(
            "entry_terminal",
            "partial exposure without its typed admission request remains fail-closed on recovery",
            tickets=sorted(pending_entry_refs),
        )
    restored = tuple(positions.values())
    high_water = events.value[-1].sequence if events.value else 0
    identity = {
        "binding_epoch": binding_epoch.value,
        "class": "qmb-replay-position-recovery",
        "high_water": high_water,
        "positions": [
            {
                "closed": position.closed,
                "financing_costs": [item.fp1_identity() for item in position.financing_costs],
                "financing_rollovers": [item.value for item in position.financing_rollovers],
                "position": position.fp1_identity(),
            }
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
        protective_stop = _parse_price(body.get("protective_stop"))
        entry_terminal_reason = EntryTerminalReason(body.get("entry_terminal_reason"))
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
        raw_entry_fills = body.get("entry_fills", ())
        if not isinstance(raw_entry_fills, (tuple, list)):
            return invalid("entry_fills", "position entry fills are a typed sequence")
        entry_fills: list[ReplayEntryFill] = []
        for raw_fill in cast(tuple[object, ...] | list[object], raw_entry_fills):
            parsed_fill = _restore_replay_entry_fill(raw_fill)
            if is_refusal(parsed_fill):
                return parsed_fill
            entry_fills.append(parsed_fill.value)
        declared_plan_quantity_raw = body.get("declared_plan_quantity")
        declared_plan_amount_raw = body.get("declared_plan_risk_amount")
        declared_plan_quantity: Quantity | None = None
        if declared_plan_quantity_raw is not None:
            parsed_plan_quantity = _parse_quantity(declared_plan_quantity_raw)
            if is_refusal(parsed_plan_quantity):
                return parsed_plan_quantity
            declared_plan_quantity = parsed_plan_quantity.value
        declared_plan_amount: Money | None = None
        if declared_plan_amount_raw is not None:
            parsed_plan_amount = _parse_money(declared_plan_amount_raw)
            if is_refusal(parsed_plan_amount):
                return parsed_plan_amount
            declared_plan_amount = parsed_plan_amount.value
        risk_rebased = body.get("risk_rebased", False)
        if not isinstance(risk_rebased, bool):
            return invalid("risk_rebased", "rebase marker is boolean")
        raw_lineage = body.get("risk_rebase_lineage")
        lineage_ref: Fingerprint | None = None
        if raw_lineage is not None:
            parsed_lineage = _parse_fingerprint(raw_lineage, "risk_rebase_lineage")
            if is_refusal(parsed_lineage):
                return parsed_lineage
            lineage_ref = parsed_lineage.value
        if is_refusal(entry_price):
            return entry_price
        if is_refusal(protective_stop):
            return protective_stop
        if is_refusal(quantity):
            return quantity
        if is_refusal(faces):
            return faces
        if is_refusal(opened_at):
            return opened_at
        if declared_plan_quantity is None or declared_plan_amount is None:
            return invalid(
                "entry_plan",
                "a persisted QMB replay position records its admitted quantity and R amount",
            )
        if risk_rebased != (lineage_ref is not None):
            return policy(
                "risk_rebase_lineage", "a rebased position carries exactly one lineage ref"
            )
        is_partial = quantity.value.as_fraction() < declared_plan_quantity.as_fraction()
        if quantity.value.as_fraction() > declared_plan_quantity.as_fraction():
            return policy("entry_quantity", "recovered actual quantity never exceeds its plan")
        if risk_rebased != is_partial:
            return policy(
                "risk_rebased", "exactly a partial terminal entry carries a one-time risk rebase"
            )
        if risk_rebased:
            expected_amount = _scale_money(
                declared_plan_amount,
                quantity.value.as_fraction(),
                declared_plan_quantity.as_fraction(),
            )
            if is_refusal(expected_amount):
                return expected_amount
            if not _same_money_amount(faces.value.original_risk_amount, expected_amount.value):
                return policy(
                    "risk_rebase",
                    "recovered RFaces equal the exact proportional amount for actual quantity",
                    actual=faces.value.original_risk_amount.fp1_identity(),
                    expected=expected_amount.value.fp1_identity(),
                )
            expected_lineage = fingerprint(
                {
                    "class": "qmb-entry-risk-rebase-lineage",
                    "from_amount": declared_plan_amount.fp1_identity(),
                    "from_quantity": declared_plan_quantity.fp1_identity(),
                    "to_amount": faces.value.original_risk_amount.fp1_identity(),
                    "to_quantity": quantity.value.fp1_identity(),
                    "terminal_reason": entry_terminal_reason.value,
                    "ticket": command_ref.value.value,
                }
            )
            if is_refusal(expected_lineage):
                return expected_lineage
            if expected_lineage.value != lineage_ref:
                return policy(
                    "risk_rebase_lineage",
                    "recovered rebase lineage binds exact plan, actual quantity, reason and ticket",
                )
        elif not _same_money_amount(faces.value.original_risk_amount, declared_plan_amount):
            return policy("risk_rebase", "full-size position retains its planned R amount")
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
            protective_stop=protective_stop.value,
            entry_terminal_reason=entry_terminal_reason,
            quantity=quantity.value,
            faces=faces.value,
            entry_fill_ref=fill_ref.value,
            entry_costs=tuple(costs),
            entry_fills=tuple(entry_fills),
            declared_plan_quantity=declared_plan_quantity,
            declared_plan_risk_amount=declared_plan_amount,
            risk_rebased=risk_rebased,
            risk_rebase_lineage=lineage_ref,
        )
    except (TypeError, ValueError):
        return invalid("replay_position", "position identity fields are well-formed typed values")
    expected = _replay_position_ref(position.command_identity, position.binding_epoch)
    if is_refusal(expected):
        return expected
    if expected.value != position.position_ref:
        return policy("position_ref", "recovered stable command-derived position ref matches")
    identity = position.fp1_identity()
    without_ref = {key: value for key, value in identity.items() if key != "position_ref"}
    expected_body = fingerprint(without_ref)
    if is_refusal(expected_body):
        return expected_body
    recorded_body = dict(cast(Mapping[object, object], raw))
    recorded_body.pop("position_ref", None)
    recorded_identity = fingerprint(recorded_body)
    if is_refusal(recorded_identity):
        return recorded_identity
    if recorded_identity.value != expected_body.value:
        return policy("replay_position", "recovered fields reproduce the canonical identity")
    if body.get("direction") != position.direction.value:
        return policy("replay_position", "recorded direction matches restored typed direction")
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


def _restore_replay_entry_fill(raw: object) -> Result[ReplayEntryFill]:
    if not isinstance(raw, Mapping):
        return invalid("entry_fill", "entry fill carries a canonical mapping")
    body = cast(Mapping[object, object], raw)
    if body.get("class") != "qmb-replay-entry-fill":
        return invalid("entry_fill", "entry fill uses the pinned QMB replay class")
    fill_ref = _parse_fingerprint(body.get("fill_ref"), "fill_ref")
    quantity = _parse_quantity(body.get("quantity"))
    price = _parse_price(body.get("price"))
    instant = _parse_instant(body.get("instant"))
    raw_costs = body.get("costs")
    if not isinstance(raw_costs, (tuple, list)):
        return invalid("entry_fill", "entry fill costs are a sequence")
    costs: list[CostComponent] = []
    for raw_cost in cast(tuple[object, ...] | list[object], raw_costs):
        cost = _parse_cost(raw_cost)
        if is_refusal(cost):
            return cost
        costs.append(cost.value)
    if is_refusal(fill_ref):
        return fill_ref
    if is_refusal(quantity):
        return quantity
    if is_refusal(price):
        return price
    if is_refusal(instant):
        return instant
    entry_fill = ReplayEntryFill(
        fill_ref=fill_ref.value,
        quantity=quantity.value,
        price=price.value,
        costs=tuple(costs),
        instant=instant.value,
    )
    body_fp = fingerprint(dict(body))
    expected_fp = fingerprint(entry_fill.fp1_identity())
    if is_refusal(body_fp):
        return body_fp
    if is_refusal(expected_fp):
        return expected_fp
    if body_fp.value != expected_fp.value:
        return policy("entry_fill", "restored entry fill reproduces its full identity")
    return Ok(entry_fill)


def _fraction_scale(value: Fraction) -> int:
    """Smallest decimal scale that exactly stores a finite decimal fraction."""
    for scale in range(19):
        if (value * (10**scale)).denominator == 1:
            return scale
    return 19


def _sum_quantities(values: tuple[Quantity, ...]) -> Result[Quantity]:
    if not values:
        return invalid("quantity", "at least one exact quantity is present")
    unit = values[0].unit
    if any(value.unit != unit for value in values):
        return invalid("quantity", "summed fill quantities share one unit")
    total = sum((value.as_fraction() for value in values), Fraction(0))
    scale = _fraction_scale(total)
    scaled = total * (10**scale)
    if scaled.denominator != 1:
        return invalid("quantity", "cumulative fill quantity is exactly representable")
    return Quantity.try_create(scaled.numerator, unit, scale)


def _same_quantity(left: Quantity, right: Quantity) -> bool:
    """Compare amount and unit, ignoring only equivalent storage scale."""
    return (
        type(left) is Quantity
        and type(right) is Quantity
        and left.unit == right.unit
        and left.as_fraction() == right.as_fraction()
    )


def _scale_money(amount: Money, numerator: Fraction, denominator: Fraction) -> Result[Money]:
    if denominator <= 0:
        return invalid("quantity", "planned quantity is positive")
    result = amount.as_fraction() * numerator / denominator
    scale = _fraction_scale(result)
    scaled = result * (10**scale)
    if scaled.denominator != 1:
        return invalid("original_risk_amount", "rebased R amount is exactly representable")
    return Money.try_create(scaled.numerator, amount.currency, scale)


def _same_money_amount(left: Money, right: Money) -> bool:
    return left.currency == right.currency and left.as_fraction() == right.as_fraction()


def _gross_exit_pnl(
    position: ReplayPosition,
    exit_price: Price,
    value_factor: ValueFactor,
    money_scale: int,
) -> Result[Money]:
    entry_fills = position.entry_fills or (
        ReplayEntryFill(
            fill_ref=position.entry_fill_ref,
            quantity=position.quantity,
            price=position.entry_price,
            costs=position.entry_costs,
            instant=position.opened_at,
        ),
    )
    total: Money | None = None
    for entry in entry_fills:
        delta = (
            exit_price.subtract(entry.price)
            if position.direction is Direction.LONG
            else entry.price.subtract(exit_price)
        )
        if is_refusal(delta):
            return delta
        part = delta.value.to_money(value_factor, entry.quantity, scale=money_scale)
        if is_refusal(part):
            return part
        if total is None:
            total = part.value
        else:
            added = total.add(part.value)
            if is_refusal(added):
                return added
            total = added.value
    if total is None:
        return invalid("entry_fill", "gross PnL requires actual opening fill evidence")
    return Ok(total)


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


def _book_financing_cost(
    cash_component: CostComponent, cash_amount: Money
) -> Result[CostComponent]:
    """Convert signed financing cash flow to CT-29's subtractive cost convention."""
    if cash_component.amount != cash_amount:
        return policy(
            "financing_component",
            "the QMF financing component exactly witnesses signed cash flow",
        )
    inverse_cash = Money.try_create(
        -cash_amount.value,
        cash_amount.currency,
        cash_amount.scale,
    )
    if is_refusal(inverse_cash):
        return inverse_cash
    return CostComponent.try_create(
        cash_component.name,
        inverse_cash.value,
        cash_component.source,
    )


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
    _pending_entries: dict[str, _PendingEntry] = field(default_factory=dict[str, _PendingEntry])
    _pending_by_intent: dict[str, str] = field(default_factory=dict[str, str])
    _finalized_resting_intent_ids: set[str] = field(default_factory=set[str])
    _terminalizing_resting_ids: dict[str, str] = field(default_factory=dict[str, str])
    _resting_terminal_proofs: dict[str, RestingTerminalDisposition] = field(
        default_factory=dict[str, RestingTerminalDisposition]
    )
    _resting_terminal_events: dict[str, JournalEvent] = field(
        default_factory=dict[str, JournalEvent]
    )
    _stream_update_seen: bool = False
    _current_observation: SliceObservation | None = None
    _last_processed_frontier: Instant | None = None
    _journal_uncertain: bool = False

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

    @property
    def pending_entry_tickets(self) -> tuple[Fingerprint, ...]:
        """Tickets whose admitted entry has fills awaiting an explicit terminal fold."""
        return tuple(entry.ticket for entry in self._pending_entries.values() if entry.fills)

    @property
    def finalized_resting_intent_ids(self) -> tuple[str, ...]:
        """Resting entry tokens terminalized by the successful end-of-input fold."""
        return tuple(sorted(self._finalized_resting_intent_ids))

    @property
    def last_processed_frontier(self) -> Instant | None:
        """Last validated runloop frontier delivered to this stream's update hook."""
        return self._last_processed_frontier

    def verify_resting_terminal(
        self, intent: RestingIntent, terminal: RestingTerminalDisposition
    ) -> Result[None]:
        """Verify stop-driven token retirement against its durable CT-13 close row."""
        expected = self._resting_terminal_proofs.get(intent.intent_id)
        event = self._resting_terminal_events.get(intent.intent_id)
        if (
            expected is None
            or event is None
            or terminal != expected
            or terminal.intent_id != intent.intent_id
            or terminal.cause is not RestingTerminalCause.PROTECTIVE_STOP
            or event.fingerprint != terminal.evidence_fp
            or event.writer != self.admission.journal_writer.writer
            or event.event_type is not JournalEventType.RISK_TRANSITION
            or event.payload.get("binding_epoch") != self.admission.binding.fingerprint.value
            or not isinstance(event.payload.get(BOOK_CLOSE_RECORD_REF_KEY), str)
        ):
            return policy(
                "terminal_witness",
                "retired resting token matches its Book-created protective-stop close witness",
            )
        rows = self.admission.journal_reader.read_checked(
            self.admission.journal_writer.stream_name,
            for_world=World.REPLAY,
        )
        if is_refusal(rows):
            return rows
        matches = tuple(
            item
            for item in rows.value
            if item.writer == event.writer
            and item.sequence == event.sequence
            and item.fingerprint == terminal.evidence_fp
        )
        if len(matches) != 1 or matches[0] != event:
            return invalid(
                "terminal_witness",
                "terminal-only outcome has one exact CT-13 readback close event",
            )
        recovered = read_replay_positions(
            journal_reader=self.admission.journal_reader,
            stream_name=self.admission.journal_writer.stream_name,
            writer=self.admission.journal_writer.writer,
            binding_epoch=self.admission.binding.fingerprint,
            result_label=self.admission.result_label,
        )
        if is_refusal(recovered):
            return recovered
        position_ref = event.payload.get("virtual_position_ref")
        if not isinstance(position_ref, str) or not any(
            position.position_ref.value == position_ref and position.closed
            for position in recovered.value.positions
        ):
            return policy(
                "terminal_position",
                "terminal stop witness resolves to the durably closed Book position",
            )
        return Ok(None)

    def _record_transition(
        self, payload: Mapping[str, object], *, instant: Instant
    ) -> Result[JournalAppendReceipt]:
        """Append one CT-13 transition and prove its exact physical readback."""
        if self._journal_uncertain:
            return policy(
                "journal_uncertain",
                "no later Book state advances until uncertain CT-13 state is reopened",
            )
        writer = self.admission.journal_writer
        sequence = writer.next_sequence
        appended = writer.record(
            JournalEventType.RISK_TRANSITION,
            payload,
            instant=instant,
        )
        if is_refusal(appended):
            return appended
        append_value: object = getattr(appended, "value", None)
        if not isinstance(append_value, JournalAppendReceipt):
            self._journal_uncertain = True
            return invalid(
                "journal_receipt",
                "CT-13 append returns a complete physical JournalAppendReceipt",
            )
        receipt = append_value
        event_value: object = getattr(receipt, "event", None)
        stored_value: object = getattr(receipt, "store_receipt", None)
        edge_receipts: object = getattr(receipt, "edge_receipts", None)
        if not isinstance(event_value, JournalEvent) or not isinstance(stored_value, StoreReceipt):
            self._journal_uncertain = True
            return invalid(
                "journal_receipt",
                "physical receipt carries typed JournalEvent and StoreReceipt values",
            )
        event = event_value
        stored = stored_value
        untrusted_event: object = event
        raw_writer = getattr(untrusted_event, "writer", None)
        raw_sequence = getattr(untrusted_event, "sequence", None)
        raw_instant = getattr(untrusted_event, "instant", None)
        raw_world = getattr(untrusted_event, "world", None)
        raw_event_type = getattr(untrusted_event, "event_type", None)
        raw_payload = getattr(untrusted_event, "payload", None)
        raw_fingerprint = getattr(untrusted_event, "fingerprint", None)
        raw_outcome = getattr(untrusted_event, "outcome", None)
        raw_correlation_id = getattr(untrusted_event, "correlation_id", None)
        if (
            not isinstance(raw_writer, WriterId)
            or raw_writer != writer.writer
            or type(raw_sequence) is not int
            or raw_sequence != sequence
            or not isinstance(raw_instant, Instant)
            or raw_instant != instant
            or raw_world is not World.REPLAY
            or not isinstance(raw_event_type, JournalEventType)
            or raw_event_type is not JournalEventType.RISK_TRANSITION
            or not isinstance(raw_payload, Mapping)
            or not isinstance(raw_fingerprint, Fingerprint)
            or (raw_outcome is not None and not isinstance(raw_outcome, DecisionOutcome))
            or (raw_correlation_id is not None and not isinstance(raw_correlation_id, str))
        ):
            self._journal_uncertain = True
            return invalid(
                "journal_event",
                "CT-13 append receipt event has well-typed identity fields before fingerprinting",
            )
        event_fp = fingerprint(event.fp1_identity())
        raw_row_fp = fingerprint(event.to_row())
        if is_refusal(event_fp):
            self._journal_uncertain = True
            return event_fp
        if is_refusal(raw_row_fp):
            self._journal_uncertain = True
            return raw_row_fp
        expected_payload_fp = fingerprint(dict(payload))
        actual_payload_fp = fingerprint(dict(event.payload))
        if is_refusal(expected_payload_fp):
            return expected_payload_fp
        if is_refusal(actual_payload_fp):
            self._journal_uncertain = True
            return actual_payload_fp
        if (
            event.writer != writer.writer
            or event.sequence != sequence
            or event.instant != instant
            or event.world is not World.REPLAY
            or event.event_type is not JournalEventType.RISK_TRANSITION
            or actual_payload_fp.value != expected_payload_fp.value
            or event.fingerprint != event_fp.value
            or stored.world is not World.REPLAY
            or stored.room_role is not RoomRole.JOURNAL
            or stored.engine != "jsonl"
            or type(stored.format_version) is not int
            or stored.format_version != 1
            or stored.fingerprint != raw_row_fp.value
            or stored.outcome not in {WriteOutcome.STORED, WriteOutcome.IDEMPOTENT}
            or stored.is_evidence_bearing is not True
            or stored.retained_forever is not True
            or not isinstance(edge_receipts, tuple)
            or edge_receipts
        ):
            self._journal_uncertain = True
            return invalid(
                "journal_receipt",
                "CT-13 receipt exactly witnesses the typed event and durable journal-room write",
            )
        readback = self.admission.journal_reader.read_checked(
            writer.stream_name,
            for_world=World.REPLAY,
        )
        if is_refusal(readback):
            self._journal_uncertain = True
            return readback
        matches = tuple(
            (physical_index, item)
            for physical_index, item in enumerate(readback.value)
            if item.writer == writer.writer and item.sequence == sequence
        )
        if (
            len(matches) != 1
            or matches[0][1] != event
            or type(stored.sequence) is not int
            or stored.sequence != matches[0][0]
        ):
            self._journal_uncertain = True
            return invalid(
                "journal_readback",
                "physical CT-13 readback contains this exact event once at its sequence",
                details={
                    "matches": len(matches),
                    "event_equal": bool(matches and matches[0][1] == event),
                    "stored_sequence": stored.sequence,
                    "physical_sequence": matches[0][0] if matches else None,
                },
            )
        return Ok(receipt)

    def finalize_pending_entries(self, *, at: Instant) -> Result[tuple[ReplayPosition, ...]]:
        """Seal all filled entries only at a successful end-of-input boundary."""
        return self._terminalize_pending_entries(at=at, reason=EntryTerminalReason.REPLAY_COMPLETE)

    def cancel_pending_entries(self, *, at: Instant) -> Result[tuple[ReplayPosition, ...]]:
        """Seal known cancelled entries at their exact cancellation boundary."""
        return self._terminalize_pending_entries(at=at, reason=EntryTerminalReason.CANCELLED)

    def _terminalize_pending_entries(
        self, *, at: Instant, reason: EntryTerminalReason
    ) -> Result[tuple[ReplayPosition, ...]]:
        finalized: list[ReplayPosition] = []
        unfilled = [ticket for ticket, entry in self._pending_entries.items() if not entry.fills]
        for ticket in unfilled:
            entry = self._pending_entries.pop(ticket)
            self._pending_by_intent.pop(entry.intent_ref.value, None)
            self._finalized_resting_intent_ids.add(entry.resting_intent_id)
        for ticket in self.pending_entry_tickets:
            position = self.finalize_entry(ticket, at=at, terminal_reason=reason)
            if is_refusal(position):
                return position
            finalized.append(position.value)
        if self.pending_entry_tickets:
            return policy("entry_terminal", "every filled replay entry reaches one terminal fold")
        return Ok(tuple(finalized))

    def finalize_entry(
        self,
        ticket: Fingerprint,
        *,
        at: Instant,
        terminal_reason: EntryTerminalReason,
    ) -> Result[ReplayPosition]:
        """Seal one order at its typed terminal state and perform AD-40's sole rebase."""
        pending = self._pending_entries.get(ticket.value)
        if pending is None:
            return invalid("entry_ticket", "terminalization names a live admitted-entry ticket")
        if not pending.fills:
            return invalid("entry_fill", "an entry without actual fills cannot mint a position")
        if at.value_ns < pending.fills[-1].instant.value_ns:
            return policy(
                "entry_terminal",
                "the terminal witness cannot precede the last actual entry fill",
            )
        total_quantity = _sum_quantities(tuple(fill.quantity for fill in pending.fills))
        if is_refusal(total_quantity):
            return total_quantity
        if total_quantity.value.as_fraction() > pending.planned_quantity.as_fraction():
            return policy("entry_quantity", "actual cumulative fills never exceed admitted plan")
        partial = not _same_quantity(total_quantity.value, pending.planned_quantity)
        lineage_ref: Fingerprint | None = None
        if partial:
            risk_amount = _scale_money(
                pending.planned_faces.original_risk_amount,
                total_quantity.value.as_fraction(),
                pending.planned_quantity.as_fraction(),
            )
            if is_refusal(risk_amount):
                return risk_amount
            faces = RFaces.try_create(
                pending.planned_faces.original_risk_distance, risk_amount.value
            )
            if is_refusal(faces):
                return faces
            lineage = fingerprint(
                {
                    "class": "qmb-entry-risk-rebase-lineage",
                    "from_amount": pending.planned_faces.original_risk_amount.fp1_identity(),
                    "from_quantity": pending.planned_quantity.fp1_identity(),
                    "to_amount": risk_amount.value.fp1_identity(),
                    "to_quantity": total_quantity.value.fp1_identity(),
                    "terminal_reason": terminal_reason.value,
                    "ticket": ticket.value,
                }
            )
            if is_refusal(lineage):
                return lineage
            lineage_ref = lineage.value
            risk_rebased = True
        else:
            faces = Ok(pending.planned_faces)
            risk_rebased = False
        aggregate_costs = _aggregate_cost_components(
            tuple(cost for fill in pending.fills for cost in fill.costs)
        )
        if is_refusal(aggregate_costs):
            return aggregate_costs
        first_fill = pending.fills[0]
        if risk_rebased and lineage_ref is None:
            return invalid("risk_rebase_lineage", "partial admission carries a lineage fingerprint")
        position_ref = _replay_position_ref(ticket, self.admission.binding.fingerprint)
        if is_refusal(position_ref):
            return position_ref
        position = ReplayPosition(
            position_ref=position_ref.value,
            binding_epoch=self.admission.binding.fingerprint,
            admission_identity=pending.admission_identity,
            command_identity=ticket,
            opening_bot_id=self.admission.opening_bot_id,
            instrument=pending.intent.instrument.symbol,
            direction=pending.intent.direction,
            opened_at=first_fill.instant,
            entry_price=first_fill.price,
            protective_stop=pending.admission.declared_full_loss_price,
            entry_terminal_reason=terminal_reason,
            quantity=total_quantity.value,
            faces=faces.value,
            entry_fill_ref=first_fill.fill_ref,
            entry_costs=aggregate_costs.value,
            entry_fills=pending.fills,
            declared_plan_quantity=pending.planned_quantity,
            declared_plan_risk_amount=pending.planned_faces.original_risk_amount,
            risk_rebased=risk_rebased,
            risk_rebase_lineage=lineage_ref,
            financing_costs=pending.financing_costs,
            financing_rollovers=pending.financing_rollovers,
        )
        witness = self._append_position_event(position, at, entry_ticket=ticket)
        if is_refusal(witness):
            return witness
        self._positions[position_ref.value.value] = position
        self._finalized_resting_intent_ids.add(pending.resting_intent_id)
        self._pending_entries.pop(ticket.value)
        self._pending_by_intent.pop(pending.intent_ref.value, None)
        return Ok(position)

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

    def update_stream(
        self,
        stream_id: str,
        observation: SliceObservation | None,
        frontier: Instant,
    ) -> Result[None]:
        """The caller supplies already materialized observations and recorded paths."""
        if stream_id != self.stream_id:
            return Ok(None)
        if observation is not None and observation.stream_id != stream_id:
            return policy("observation", "stream update belongs to its declared stream")
        if observation is not None and observation.instant.value_ns > frontier.value_ns:
            return policy("frontier", "observation time does not follow its processed frontier")
        previous = self._last_processed_frontier
        if previous is not None and frontier.value_ns < previous.value_ns:
            return policy("frontier", "processed stream frontiers never move backwards")
        self._stream_update_seen = True
        self._current_observation = observation
        self._last_processed_frontier = frontier
        return Ok(None)

    def update_closed_data(
        self,
        stream_id: str,
        observation: SliceObservation,
        frontier: Instant,
    ) -> Result[None]:
        """No secondary indicator state is owned here; the selected Bot consumes its protocol."""
        del frontier
        if stream_id != self.stream_id or observation.stream_id != stream_id:
            return policy("observation", "closed-data update matches the selected Bot stream")
        if not observation.closed:
            return policy("observation", "QML receives only a closed materialized observation")
        return Ok(None)

    def scheduled_position_event(self, stream_id: str, frontier: Instant) -> Result[None]:
        """Apply and durably record only calendar-authorized financing rollovers."""
        if stream_id != self.stream_id:
            return Ok(None)
        pending_exposures = tuple(entry for entry in self._pending_entries.values() if entry.fills)
        if not self._positions and not pending_exposures:
            return Ok(None)
        if self._stream_update_seen and self._current_observation is None:
            return Ok(None)
        stop_path = self._paths_by_frontier.get(frontier.value_ns, self._path)
        if stop_path is None:
            return invalid(
                "protective_stop_path",
                "open positions require their exact recorded quote path at each frontier",
                instant_ns=frontier.value_ns,
            )
        exposures = tuple(
            (position.direction, position.protective_stop) for position in self._positions.values()
        ) + tuple(
            (entry.intent.direction, entry.admission.declared_full_loss_price)
            for entry in pending_exposures
        )
        for direction, protective_stop in exposures:
            quote = stop_path.bid if direction is Direction.LONG else stop_path.ask
            if quote is None:
                quote_name = "bid" if direction is Direction.LONG else "ask"
                return invalid(
                    quote_name,
                    f"{direction.value} protective stops cross only recorded {quote_name} quotes",
                )
            if quote.instrument != protective_stop.instrument:
                return policy(
                    "protective_stop_quote",
                    "recorded quote side and admitted stop name the same instrument",
                )
        open_positions: list[OpenPosition] = []
        rollover = self.admission.rollover_calendar.is_rollover_instant(frontier)
        if is_refusal(rollover):
            return rollover
        rollover_ref: Fingerprint | None = None
        if rollover.value:
            trading_date = self.admission.rollover_calendar.trading_date_of(frontier)
            if is_refusal(trading_date):
                return trading_date
            date_fp = fingerprint(trading_date.value.fp1_identity())
            if is_refusal(date_fp):
                return date_fp
            rollover_ref = date_fp.value
        eligible = tuple(
            position
            for position in self._positions.values()
            if rollover_ref is None or rollover_ref not in position.financing_rollovers
        )
        for position in eligible:
            opened = OpenPosition.try_create(self.stream_id, position.direction, position.quantity)
            if is_refusal(opened):
                return opened
            open_positions.append(opened.value)
        pending_eligible = tuple(
            entry
            for entry in pending_exposures
            if rollover_ref is None or rollover_ref not in entry.financing_rollovers
        )
        for entry in pending_eligible:
            actual_quantity = _sum_quantities(tuple(fill.quantity for fill in entry.fills))
            if is_refusal(actual_quantity):
                return actual_quantity
            opened = OpenPosition.try_create(
                self.stream_id, entry.intent.direction, actual_quantity.value
            )
            if is_refusal(opened):
                return opened
            open_positions.append(opened.value)
        events: tuple[FinancingCashEvent, ...] = ()
        if open_positions:
            applied = apply_financing_rollover(
                self.bound_execution.ports.financing,
                tuple(open_positions),
                frontier=frontier,
                calendar=self.admission.rollover_calendar,
                writer=self.admission.journal_writer.writer,
                world=World.REPLAY,
                start_sequence=self.admission.journal_writer.next_sequence,
                stream_id=self.stream_id,
            )
            if is_refusal(applied):
                return applied
            events = applied.value.events
        for cash in events:
            if rollover_ref is None:
                return policy(
                    "financing_rollover",
                    "a cash event is emitted only for its fingerprinted calendar date",
                )
            candidates = [
                position
                for position in self._positions.values()
                if position.direction is cash.position.direction
                and _same_quantity(position.quantity, cash.position.quantity)
            ]
            pending_candidates: list[tuple[_PendingEntry, Quantity]] = []
            for entry in pending_eligible:
                quantity = _sum_quantities(tuple(fill.quantity for fill in entry.fills))
                if is_refusal(quantity):
                    return quantity
                if (
                    entry.intent.direction is cash.position.direction
                    and _same_quantity(quantity.value, cash.position.quantity)
                ):
                    pending_candidates.append((entry, quantity.value))
            if len(candidates) + len(pending_candidates) != 1:
                return policy(
                    "financing_attribution",
                    "cash event maps to one full or actual partial QMB position",
                )
            position_candidate = candidates[0] if candidates else None
            pending_candidate = pending_candidates[0][0] if pending_candidates else None
            if position_candidate is not None:
                virtual_position_ref = position_candidate.position_ref.value
            else:
                if pending_candidate is None:
                    return invalid("financing_attribution", "cash event has one typed position")
                stable_ref = _replay_position_ref(
                    pending_candidate.ticket, self.admission.binding.fingerprint
                )
                if is_refusal(stable_ref):
                    return stable_ref
                virtual_position_ref = stable_ref.value.value
            cost = _book_financing_cost(cash.component, cash.amount)
            if is_refusal(cost):
                return cost
            journaled = self._record_transition(
                {
                    "binding_epoch": self.admission.binding.fingerprint.value,
                    "financing_event": cash.fp1_identity(),
                    "kind": "financing",
                    "virtual_position_ref": virtual_position_ref,
                },
                instant=frontier,
            )
            if is_refusal(journaled):
                return journaled
            if position_candidate is not None:
                self._positions[position_candidate.position_ref.value] = replace(
                    position_candidate,
                    financing_costs=(*position_candidate.financing_costs, cost.value),
                    financing_rollovers=(*position_candidate.financing_rollovers, rollover_ref),
                )
            else:
                if pending_candidate is None:
                    return invalid("financing_attribution", "cash event has one typed position")
                self._pending_entries[pending_candidate.ticket.value] = replace(
                    pending_candidate,
                    financing_costs=(*pending_candidate.financing_costs, cost.value),
                    financing_rollovers=(*pending_candidate.financing_rollovers, rollover_ref),
                )
        stopped = self._evaluate_protective_stops(frontier)
        if is_refusal(stopped):
            return stopped
        for pending in pending_exposures:
            current = self._pending_entries.get(pending.ticket.value)
            if current is None or not current.fills:
                continue
            quote = stop_path.bid if current.intent.direction is Direction.LONG else stop_path.ask
            if quote is None:
                return invalid(
                    "protective_stop_quote",
                    "partial exposure uses its direction's recorded quote side",
                )
            stop = current.admission.declared_full_loss_price
            triggered = (
                quote.as_fraction() <= stop.as_fraction()
                if current.intent.direction is Direction.LONG
                else quote.as_fraction() >= stop.as_fraction()
            )
            if not triggered:
                continue
            # The residual order is terminal at the recorded stop crossing. Rebase only
            # to actual accumulated fills, then close that witnessed exposure normally.
            terminal = self.finalize_entry(
                current.ticket,
                at=frontier,
                terminal_reason=EntryTerminalReason.PROTECTIVE_STOP,
            )
            if is_refusal(terminal):
                return terminal
            self._terminalizing_resting_ids[terminal.value.position_ref.value] = (
                current.resting_intent_id
            )
        stopped = self._evaluate_protective_stops(frontier)
        if is_refusal(stopped):
            return stopped
        return Ok(None)

    def _evaluate_protective_stops(self, frontier: Instant) -> Result[None]:
        path = self._paths_by_frontier.get(frontier.value_ns, self._path)
        if path is None:
            return invalid(
                "protective_stop_path",
                "open positions require their exact recorded quote path at each frontier",
                instant_ns=frontier.value_ns,
            )
        reason_code = self.admission.protective_stop_reason
        reason_key = _reason_policy_key("exit", reason_code)
        stop_order_policy = self.admission.order_policy_by_code.get(reason_key)
        if stop_order_policy is None:
            return invalid("protective_stop_policy", "declared stop has an explicit Book order")
        for position in tuple(self._positions.values()):
            stop = position.protective_stop
            quote = path.bid if position.direction is Direction.LONG else path.ask
            if quote is None:
                quote_name = "bid" if position.direction is Direction.LONG else "ask"
                return invalid(
                    quote_name,
                    f"{position.direction.value} protective stops cross only recorded "
                    f"{quote_name} quotes",
                )
            if quote.instrument != stop.instrument:
                return policy(
                    "protective_stop_quote",
                    "recorded quote side and admitted stop name the same instrument",
                )
            triggered = (
                quote.as_fraction() <= stop.as_fraction()
                if position.direction is Direction.LONG
                else quote.as_fraction() >= stop.as_fraction()
            )
            if not triggered:
                continue
            if stop_order_policy.stop_price is not None and stop_order_policy.stop_price != stop:
                return policy(
                    "protective_stop_policy",
                    "configured stop price, when present, equals the admitted immutable loss price",
                )
            effective_stop_policy = replace(stop_order_policy, stop_price=stop)
            exit_intent = ExitIntent.try_create(
                ExitKind.CLOSE_FULL,
                reason_code,
                position.position_ref,
            )
            if is_refusal(exit_intent):
                return exit_intent
            resting = RestingIntent.try_create(
                f"protective-stop:{position.position_ref.value}",
                self.stream_id,
                order=effective_stop_policy,
                proposal=exit_intent.value,
            )
            if is_refusal(resting):
                return resting
            closed = self._close(
                exit_intent.value,
                path,
                frontier,
                resting.value,
                order_policy_override=effective_stop_policy,
            )
            if is_refusal(closed):
                return closed
            self._receipts.append(closed.value)
            resting_intent_id = self._terminalizing_resting_ids.pop(
                position.position_ref.value, None
            )
            if resting_intent_id is not None:
                journal_receipt = closed.value.journal_receipt
                if journal_receipt is None:
                    return invalid(
                        "terminal_witness", "protective stop close carries a verified CT-13 receipt"
                    )
                terminal = RestingTerminalDisposition(
                    intent_id=resting_intent_id,
                    cause=RestingTerminalCause.PROTECTIVE_STOP,
                    evidence_fp=journal_receipt.event.fingerprint,
                )
                self._resting_terminal_proofs[resting_intent_id] = terminal
                self._resting_terminal_events[resting_intent_id] = journal_receipt.event
            if isinstance(closed.value.fill, NoFill):
                return policy(
                    "protective_stop_fill",
                    "a crossed protective stop must produce an actual close fill",
                    no_fill_reason=closed.value.fill.reason,
                )
            filled_price = _fill_price(closed.value.fill.fill)
            if is_refusal(filled_price):
                return filled_price
            split = split_path_at(path, filled_price.value)
            if is_refusal(split):
                return split
            if frontier.value_ns in self._paths_by_frontier:
                paths_by_frontier = dict(self._paths_by_frontier)
                paths_by_frontier[frontier.value_ns] = split.value
                self._paths_by_frontier = MappingProxyType(paths_by_frontier)
            else:
                self._path = split.value
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
    ) -> Result[bool | ExecutionDisposition | RestingTerminalDisposition]:
        """Execute one CT-23 proposal; only actual full fills change position state."""
        if intent.stream_id != self.stream_id:
            return Ok(False)
        terminal = self._resting_terminal_proofs.get(intent.intent_id)
        if terminal is not None:
            return Ok(terminal)
        if isinstance(intent.proposal, EntryIntent) and intent.intent_id in (
            self._finalized_resting_intent_ids
        ):
            return invalid(
                "terminal_witness",
                "a finalized entry token has no terminal disposition without its close witness",
            )
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
            return Ok(
                ExecutionDisposition(False, False) if isinstance(proposal, EntryIntent) else False
            )
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
        if isinstance(proposal, EntryIntent):
            return Ok(ExecutionDisposition(True, receipt.value.position is not None))
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
        entry_price = entry_reference_price(path, intent)
        if is_refusal(entry_price):
            return entry_price
        intent_fp = fingerprint(intent.fp1_identity())
        if is_refusal(intent_fp):
            return intent_fp
        known_ticket = self._pending_by_intent.get(intent_fp.value.value)
        pending = self._pending_entries.get(known_ticket) if known_ticket is not None else None
        if pending is None and any(
            existing.intent.instrument == intent.instrument
            for existing in self._pending_entries.values()
        ):
            return policy(
                "pending_entry",
                "a distinct entry cannot top up or compete with an actual partial exposure",
            )
        if pending is None:
            admitted = _admit(context, intent, entry_price.value)
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
                entry_price.value,
                admitted.value.declared_full_loss_price,
                intent.direction,
                quantity.value,
                context.value_factor,
                money_scale=context.money_scale,
            )
            if is_refusal(faces):
                return faces
            target = r_to_money(
                context.requested_r, context.r_unit_price, scale=context.money_scale
            )
            if is_refusal(target):
                return target
            if faces.value.original_risk_amount != target.value:
                return policy(
                    "position_quantity",
                    "planned CT-23 RFaces equal the Book R budget before slippage",
                )
            admission_identity = fingerprint(admitted.value.fp1_identity())
            if is_refusal(admission_identity):
                return admission_identity
            ticket = fingerprint(
                {
                    "admission_identity": admission_identity.value.value,
                    "binding_epoch": context.binding.fingerprint.value,
                    "class": "qmb-replay-entry-ticket",
                    "intent_identity": intent_fp.value.value,
                }
            )
            if is_refusal(ticket):
                return ticket
            pending = _PendingEntry(
                ticket=ticket.value,
                intent_ref=intent_fp.value,
                intent=intent,
                admission=admitted.value,
                admission_identity=admission_identity.value,
                planned_quantity=quantity.value,
                planned_faces=faces.value,
                resting_intent_id=resting.intent_id,
            )
            self._pending_entries[ticket.value.value] = pending
            self._pending_by_intent[intent_fp.value.value] = ticket.value.value
        elif pending.resting_intent_id != resting.intent_id:
            return policy(
                "entry_ticket",
                "a pending admitted entry resumes only through its original resting intent",
            )
        filled_fraction = sum((fill.quantity.as_fraction() for fill in pending.fills), Fraction(0))
        remaining = pending.planned_quantity.as_fraction() - filled_fraction
        if remaining <= 0:
            return policy("entry_quantity", "pending entry has remaining admitted quantity")
        remaining_quantity = Quantity.try_create(
            remaining.numerator,
            pending.planned_quantity.unit,
            _fraction_scale(remaining),
        )
        if is_refusal(remaining_quantity):
            return remaining_quantity
        reason_key = _policy_key("entry", intent)
        order_policy = context.order_policy_by_code.get(reason_key)
        if order_policy is None:
            return invalid(
                "order_policy", "Book has no explicit order rule for this CT-23 entry reason code"
            )
        order = order_policy.materialize(
            side=intent.direction,
            quantity=remaining_quantity.value,
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
            quantity=remaining_quantity.value,
            context=context,
            order=order.value,
            entry_price=entry_price.value,
        )
        if is_refusal(fill):
            return fill
        if isinstance(fill.value, NoFill):
            return Ok(
                BookExecutionReceipt(intent=intent, fill=fill.value, entry_ticket=pending.ticket)
            )
        actual_entry_price = _fill_price(fill.value.fill)
        if is_refusal(actual_entry_price):
            return actual_entry_price
        fill_identity = fingerprint(fill.value.fp1_identity())
        if is_refusal(fill_identity):
            return fill_identity
        entry_fill = ReplayEntryFill(
            fill_ref=fill_identity.value,
            quantity=fill.value.fill.quantity,
            price=actual_entry_price.value,
            costs=fill.value.costs,
            instant=at,
        )
        next_pending = replace(pending, fills=(*pending.fills, entry_fill))
        total = _sum_quantities(tuple(item.quantity for item in next_pending.fills))
        if is_refusal(total):
            return total
        if total.value.as_fraction() > pending.planned_quantity.as_fraction():
            return policy("entry_quantity", "actual cumulative fill stays within the admitted plan")
        if isinstance(fill.value.fill, PartialFill):
            stable_ref = _replay_position_ref(pending.ticket, context.binding.fingerprint)
            if is_refusal(stable_ref):
                return stable_ref
            persisted = self._record_transition(
                {
                    "binding_epoch": context.binding.fingerprint.value,
                    "replay_entry_fill": entry_fill.fp1_identity(),
                    "replay_entry_fill_ref": entry_fill.fill_ref.value,
                    "replay_entry_ticket": pending.ticket.value,
                    "virtual_position_ref": stable_ref.value.value,
                },
                instant=at,
            )
            if is_refusal(persisted):
                return persisted
            self._pending_entries[pending.ticket.value] = next_pending
            return Ok(
                BookExecutionReceipt(
                    intent=intent,
                    fill=fill.value,
                    journal_receipt=persisted.value,
                    entry_ticket=pending.ticket,
                )
            )
        if not _same_quantity(fill.value.fill.quantity, remaining_quantity.value):
            return policy("fill_quantity", "a full replay fill equals the exact remaining quantity")
        if pending.fills:
            stable_ref = _replay_position_ref(pending.ticket, context.binding.fingerprint)
            if is_refusal(stable_ref):
                return stable_ref
            persisted = self._record_transition(
                {
                    "binding_epoch": context.binding.fingerprint.value,
                    "replay_entry_fill": entry_fill.fp1_identity(),
                    "replay_entry_fill_ref": entry_fill.fill_ref.value,
                    "replay_entry_ticket": pending.ticket.value,
                    "virtual_position_ref": stable_ref.value.value,
                },
                instant=at,
            )
            if is_refusal(persisted):
                return persisted
        previous_pending = self._pending_entries[pending.ticket.value]
        self._pending_entries[pending.ticket.value] = next_pending
        position = self.finalize_entry(
            pending.ticket, at=at, terminal_reason=EntryTerminalReason.REPLAY_COMPLETE
        )
        if is_refusal(position):
            self._pending_entries[pending.ticket.value] = previous_pending
            return position
        return Ok(
            BookExecutionReceipt(
                intent=intent,
                fill=fill.value,
                position=position.value,
                entry_ticket=pending.ticket,
            )
        )

    def _close(
        self,
        intent: ExitIntent,
        path: SlicePath,
        at: Instant,
        resting: RestingIntent,
        *,
        order_policy_override: BookOrderPolicy | None = None,
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
        order_policy = order_policy_override or context.order_policy_by_code.get(reason_key)
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
        if not _same_quantity(actual_fill.quantity, position.quantity):
            return policy("quantity", "close fill quantity equals the complete virtual position")
        price = _fill_price(actual_fill)
        if is_refusal(price):
            return price
        gross = _gross_exit_pnl(position, price.value, context.value_factor, context.money_scale)
        if is_refusal(gross):
            return gross
        fill_ref = fingerprint(evaluated.value.fp1_identity())
        if is_refusal(fill_ref):
            return fill_ref
        costed_result = _aggregate_cost_components(
            (*position.entry_costs, *position.financing_costs, *evaluated.value.costs)
        )
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
        entry_fill_refs = tuple(fill.fill_ref for fill in position.entry_fills) or (
            position.entry_fill_ref,
        )
        record = mint_exit_record(
            virtual_position_ref=position.position_ref,
            opening_bot_id=position.opening_bot_id,
            original_risk_distance=position.faces.original_risk_distance,
            original_risk_amount=position.faces.original_risk_amount,
            fill_references=(*entry_fill_refs, fill_ref.value),
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
        journaled = self._record_transition(
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
            protective_stop=position.protective_stop,
            entry_terminal_reason=position.entry_terminal_reason,
            quantity=position.quantity,
            faces=position.faces,
            entry_fill_ref=position.entry_fill_ref,
            entry_costs=position.entry_costs,
            closed=True,
            entry_fills=position.entry_fills,
            declared_plan_quantity=position.declared_plan_quantity,
            declared_plan_risk_amount=position.declared_plan_risk_amount,
            risk_rebased=position.risk_rebased,
            risk_rebase_lineage=position.risk_rebase_lineage,
            financing_costs=position.financing_costs,
            financing_rollovers=position.financing_rollovers,
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
        self,
        position: ReplayPosition,
        at: Instant,
        *,
        entry_ticket: Fingerprint | None = None,
    ) -> Result[JournalAppendReceipt]:
        """Write the opening virtual-position witness before later close interpretation."""
        # The caller adds this position to memory only after the witness append succeeds.
        state_fp = _position_state_fingerprint(position)
        if is_refusal(state_fp):
            return state_fp
        payload: dict[str, object] = {
            "binding_epoch": position.binding_epoch.value,
            "replay_position": position.fp1_identity(),
            "replay_position_fingerprint": state_fp.value.value,
            "replay_position_ref": position.position_ref.value,
        }
        if entry_ticket is not None:
            payload["replay_entry_ticket"] = entry_ticket.value
        return self._record_transition(
            payload,
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
    return _reason_policy_key(intent_kind, intent.reason_code)


def _replay_position_ref(
    command_identity: Fingerprint, binding_epoch: Fingerprint
) -> Result[Fingerprint]:
    """Stable virtual-position identity, independent of terminal quantity rebasing."""
    return fingerprint(
        {
            "binding_epoch": binding_epoch.value,
            "class": "qmb-replay-position-ref",
            "command_identity": command_identity.value,
        }
    )


def _position_state_fingerprint(position: ReplayPosition) -> Result[Fingerprint]:
    """Bind mutable terminal fields to the stable command-derived position reference."""
    identity = position.fp1_identity()
    identity.pop("position_ref", None)
    stamped = fingerprint(identity)
    return stamped


def _canonical_plain(value: object) -> object:
    """Normalize frozen journal mappings and tuples to the original fp1 JSON shape."""
    if isinstance(value, Mapping):
        mapped: Mapping[object, object] = cast(Mapping[object, object], value)
        normalized: dict[object, object] = {}
        for key, child in mapped.items():
            normalized[key] = _canonical_plain(child)
        return normalized
    if isinstance(value, (tuple, list)):
        values = cast(Sequence[object], value)
        return [_canonical_plain(child) for child in values]
    return value


def _reason_policy_key(intent_kind: str, reason_code: ReasonCode) -> str:
    return f"{intent_kind}:{reason_code.book_family}:{reason_code.code}"
