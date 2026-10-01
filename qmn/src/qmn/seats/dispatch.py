"""Hosted-callback intents cross Book / BMS / protection / order, never CT-19.

Story 26.15 / FR-072: a seated callback may emit CT-23 intents only. Those
intents enter the Book door (requested_r Book-resolved, bot never sizes),
bind through the BMS instance named at admission, take the venue-resident
protective-stop gate, and mint CT-19 ``place_order`` from the authorized
intent. The callback cannot construct CT-19, cannot read clock/Book/venue/
signal-snapshot objects, and cannot skip a hop.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from qmf.core import Fingerprint, Instant, Ok, Result, TypedRefusal, is_refusal
from qmf.risk.binding import BookBindingRecord
from qmf.risk.door import EntryIntent, ExitIntent, ExitKind
from qmf.risk.paper import ExecutionTarget

from qmn.ledger.binding_ledger import BindingVirtualLedger
from qmn.ledger.native_position import (
    NativePositionAttribution,
    NativePositionEvidence,
    resolve_native_position_attribution,
    write_native_position_attribution,
)
from qmn.ledger.virtual import VirtualPosition, VirtualPositionStatus
from qmn.order.door import (
    BOT_SIZE_FIELDS,
    AuthorizedIntent,
    admit_entry_at_book_door,
    mint_place_order_from_authorized,
    reject_bot_supplied_final_size,
)
from qmn.order.identity import NativeExecutionMap
from qmn.order.protection import require_venue_resident_protective_stop
from qmn.seats._refuse import invalid, policy
from qmn.seats.admission import AdmittedNodeSeat
from qmn.seats.host import GovernedSeat, drive_governed_seat
from qmn.venue import CloseScope, Command, CommandIdBinding

__all__ = [
    "INTENT_PATH_HOPS",
    "BookPathContext",
    "NativeExitAuthority",
    "SeatDispatchReceipt",
    "authorize_native_exit_intent",
    "dispatch_hosted_intents",
    "dispatch_seat_intents",
    "refuse_bot_constructed_ct19",
]

INTENT_PATH_HOPS: Final[tuple[str, ...]] = ("book", "bms", "protection", "order")


@dataclass(frozen=True, slots=True)
class BookPathContext:
    """Inputs every hosted intent must cross — Book door, BMS, protection, order."""

    entry_price: object
    exit_logic_ref: object
    module: object
    book_resolved_requested_r: object
    r_unit_price: object
    value_factor: object
    money_scale: object
    account: object
    venue_id: object
    session_epoch: object
    ordering_ordinal: object
    bms_instance_id: str
    protective_stop_forms: object
    position_ledger: object
    native_execution_map: object
    decision_at: object
    binding_record: object
    native_exit_authority: object = None


@dataclass(frozen=True, slots=True)
class NativeExitAuthority:
    """Host-owned, checked-evidence inputs for resolving one native close subject."""

    journal: object
    authorized_writers: object
    command_binding_journal: object
    evidence_by_position_ref: Mapping[str, NativePositionEvidence]
    binding_by_position_ref: Mapping[str, CommandIdBinding]
    target: object
    composition_fp: object
    position_model: object
    binding_id: object
    projection_writer: object
    netting_partition: object = None
    subject_present_at_submission: object = None
    subject_observations: object = None


@dataclass(frozen=True, slots=True)
class SeatDispatchReceipt:
    """Proof that hosted intents crossed Book / BMS / protection / order."""

    authorized: tuple[AuthorizedIntent, ...]
    commands: tuple[Command, ...]
    hops: tuple[str, ...]
    bms_instance_id: str
    seat_id: str
    exit_attributions: tuple[NativePositionAttribution, ...] = ()

    def as_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "bms_instance_id": self.bms_instance_id,
                "command_count": len(self.commands),
                "hops": list(self.hops),
                "intent_count": len(self.authorized),
                "exit_attributions": [item.identity() for item in self.exit_attributions],
                "seat_id": self.seat_id,
            }
        )


def refuse_bot_constructed_ct19(payload: object = None, **extra: object) -> TypedRefusal:
    """A hosted callback cannot mint CT-19; the Book door mints after freeze."""
    given = type(payload).__name__ if payload is not None else "ct-19"
    return policy(
        "ct19",
        "a hosted callback cannot construct CT-19; place_order mints only from "
        "a Book-authorized intent after the BMS/protection/order path (FR-072)",
        given=given,
        **extra,
    )


def dispatch_hosted_intents(
    seat: object,
    intents: object,
    *,
    path: object,
) -> Result[SeatDispatchReceipt]:
    """Admit hosted CT-23 intents through Book / BMS / protection / order."""
    admitted = _as_admitted_seat(seat)
    if is_refusal(admitted):
        return admitted
    context = _as_path(path)
    if is_refusal(context):
        return context
    door = context.value
    if not isinstance(door.position_ledger, BindingVirtualLedger):
        return invalid(
            "position_ledger",
            "hosted order admission requires its binding-scoped virtual position ledger",
            given=type(door.position_ledger).__name__,
        )
    if not door.position_ledger.reservation_admission_ready:
        return policy(
            "reservation_journal",
            "hosted entries wait for complete reservation recovery and a clean durable journal",
        )
    if not isinstance(door.native_execution_map, NativeExecutionMap):
        return invalid(
            "native_execution_map",
            "hosted order admission requires its immutable registry-pinned native "
            "account/symbol map",
            given=type(door.native_execution_map).__name__,
        )
    if not isinstance(door.binding_record, BookBindingRecord):
        return invalid(
            "binding_record",
            "hosted order admission resolves epoch from a typed CT-28 BookBindingRecord",
            given=type(door.binding_record).__name__,
        )
    expected_epoch = door.binding_record.fingerprint()
    if is_refusal(expected_epoch):
        return expected_epoch
    if (
        admitted.value.binding_ref != expected_epoch.value.value
        or admitted.value.proof.bms_instance_id != door.binding_record.bms_instance_id.value
        or door.binding_record.venue_id != door.venue_id
        or door.binding_record.account_id != getattr(door.account, "account_id", None)
        or door.position_ledger.binding_epoch != expected_epoch.value
    ):
        return policy(
            "binding_epoch",
            "seat, Book/BMS context, and position ledger resolve to the exact CT-28 binding epoch",
            admitted_binding_ref=admitted.value.binding_ref,
        )
    if door.native_execution_map.binding_epoch != expected_epoch.value:
        return policy(
            "native_execution_map",
            "the native account/symbol map is explicitly pinned to the exact admitted "
            "binding epoch",
        )
    if not isinstance(door.decision_at, Instant):
        return invalid("decision_at", "order admission requires the current decision frontier")
    if any(
        record.recorded_at.value_ns > door.decision_at.value_ns
        for record in door.position_ledger.records
    ):
        return policy(
            "decision_frontier",
            "the decision cannot precede a binding ledger record already folded into risk",
            decision_at=door.decision_at.value_ns,
        )
    if door.bms_instance_id != admitted.value.proof.bms_instance_id:
        return policy(
            "bms_instance_id",
            "hosted intents bind the BMS instance named at seat admission; "
            "the callback cannot skip or substitute the BMS hop",
            admitted=admitted.value.proof.bms_instance_id,
            given=door.bms_instance_id,
        )
    items = _as_intent_sequence(intents)
    if is_refusal(items):
        return items
    authorized: list[AuthorizedIntent] = []
    commands: list[Command] = []
    exit_attributions: list[NativePositionAttribution] = []
    entry_reservations: list[tuple[str, Fingerprint]] = []
    pending_in_batch: set[str] = set()
    ordinal = door.ordering_ordinal
    if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 0:
        return invalid(
            "ordering_ordinal",
            "the order-path hop carries a non-negative command ordinal",
            given=repr(ordinal),
        )
    for index, item in enumerate(items.value):
        blocked = _refuse_sizing_or_ct19(item)
        if is_refusal(blocked):
            return blocked
        if isinstance(item, ExitIntent):
            exited = authorize_native_exit_intent(item, door, ordering_ordinal=ordinal + index)
            if is_refusal(exited):
                return exited
            commands.append(exited.value[0])
            exit_attributions.append(exited.value[1])
            continue
        if not isinstance(item, EntryIntent):
            return policy(
                "intents",
                "a hosted callback emits CT-23 intents; only an entry intent "
                "crosses the Book door onto the order path",
                index=index,
                given=type(item).__name__,
            )
        instrument_key = item.instrument.symbol
        if (
            door.position_ledger.has_open_virtual(instrument_key)
            or door.position_ledger.has_pending_entry(instrument_key)
            or instrument_key in pending_in_batch
        ):
            return policy(
                "has_open_virtual_position",
                "a binding/instrument virtual position or pending entry blocks scale-in",
                instrument=instrument_key,
            )
        frozen = admit_entry_at_book_door(
            intent=item,
            entry_price=door.entry_price,
            exit_logic_ref=door.exit_logic_ref,
            module=door.module,
            book_resolved_requested_r=door.book_resolved_requested_r,
            r_unit_price=door.r_unit_price,
            value_factor=door.value_factor,
            money_scale=door.money_scale,
            has_open_virtual_position=False,
        )
        if is_refusal(frozen):
            return frozen
        command = mint_place_order_from_authorized(
            frozen.value,
            venue_id=door.venue_id,
            account=door.account,
            session_epoch=door.session_epoch,
            ordering_ordinal=ordinal + index,
            native_execution_map=door.native_execution_map,
        )
        if is_refusal(command):
            return command
        protected = require_venue_resident_protective_stop(
            command.value,
            forms_per_order_type=door.protective_stop_forms,
        )
        if is_refusal(protected):
            return protected
        authorized.append(frozen.value)
        commands.append(command.value)
        pending_in_batch.add(instrument_key)
        command_identity = command.value.fingerprint()
        if is_refusal(command_identity):
            return command_identity
        entry_reservations.append((item.instrument.symbol, command_identity.value))
    if entry_reservations:
        reserved = door.position_ledger.reserve_entries(tuple(entry_reservations))
        if is_refusal(reserved):
            return reserved
    return Ok(
        SeatDispatchReceipt(
            authorized=tuple(authorized),
            commands=tuple(commands),
            hops=INTENT_PATH_HOPS,
            bms_instance_id=door.bms_instance_id,
            seat_id=admitted.value.seat_id,
            exit_attributions=tuple(exit_attributions),
        )
    )


def authorize_native_exit_intent(
    intent: ExitIntent, door: BookPathContext, *, ordering_ordinal: int
) -> Result[tuple[Command, NativePositionAttribution]]:
    """Resolve and persist the native subject before minting a full-close command."""
    if intent.kind is not ExitKind.CLOSE_FULL:
        return policy(
            "exit_intent",
            "tighten-protective-stop needs the separately admitted protection path; "
            "it cannot be converted to a market close",
        )
    authority = door.native_exit_authority
    if type(authority) is not NativeExitAuthority:
        return policy(
            "native_exit_authority",
            "a hosted close requires host-pinned CT-13 fill/readback and durable "
            "CT-19 binding authority",
        )
    ledger = door.position_ledger
    if type(ledger) is not BindingVirtualLedger:
        return invalid("position_ledger", "native exit resolves through a binding virtual ledger")
    position = ledger.position_by_ref(intent.virtual_position_ref)
    if not isinstance(position, VirtualPosition):
        return policy("virtual_position", "exit intent targets an existing virtual position")
    if position.status is not VirtualPositionStatus.OPEN:
        return policy("virtual_position", "exit intent targets an open virtual position")
    ref = intent.virtual_position_ref.value
    evidence = authority.evidence_by_position_ref.get(ref)
    command_binding = authority.binding_by_position_ref.get(ref)
    if (
        type(evidence) is not NativePositionEvidence
        or type(command_binding) is not CommandIdBinding
    ):
        return policy(
            "native_evidence", "the virtual position has exact host-pinned native evidence"
        )
    if type(authority.target) is not ExecutionTarget:
        return invalid("target", "native exit authority carries an exact execution target")
    native_map = door.native_execution_map
    if type(native_map) is not NativeExecutionMap:
        return invalid(
            "native_execution_map", "native exit resolves through an immutable native map"
        )
    mappings = tuple(
        mapping
        for mapping in native_map.mappings
        if mapping.target == authority.target and mapping.instrument.symbol == position.instrument
    )
    if len(mappings) != 1:
        return policy(
            "native_execution_map", "the position resolves one exact target/instrument row"
        )
    resolved = resolve_native_position_attribution(
        journal=authority.journal,
        authorized_writers=authority.authorized_writers,
        evidence=evidence,
        command_binding=command_binding,
        command_binding_journal=authority.command_binding_journal,
        ledger=door.position_ledger,
        position_ref=intent.virtual_position_ref,
        target=authority.target,
        instrument=mappings[0].instrument,
        native_map=native_map,
        binding_epoch=ledger.binding_epoch,
        composition_fp=authority.composition_fp,
        position_model=authority.position_model,
        binding_id=authority.binding_id,
        netting_partition=authority.netting_partition,
    )
    if is_refusal(resolved):
        return resolved
    command = Command.close_position(
        door.venue_id,
        door.account,
        door.session_epoch,
        ordering_ordinal,
        CloseScope.ACCOUNT_BINDING,
        resolved.value.native_position_id,
    )
    if is_refusal(command):
        return command
    persisted = write_native_position_attribution(
        journal=authority.journal,
        writer=authority.projection_writer,
        instant=door.decision_at,
        attribution=resolved.value,
    )
    if is_refusal(persisted):
        return persisted
    return Ok((command.value, resolved.value))


def dispatch_seat_intents(
    seat: object,
    instant: object,
    *,
    path: object,
    stream: object,
    cancel: object,
    probe: object,
    transition_instant: object = None,
) -> Result[SeatDispatchReceipt]:
    """Drive one hosted callback and send its intents through the money path."""
    admitted = _as_admitted_seat(seat)
    if is_refusal(admitted):
        return admitted
    if not isinstance(instant, Instant):
        return invalid(
            "instant",
            "the evaluation instant rides the callback; bots never read a clock",
            given=repr(instant),
        )
    intents = drive_governed_seat(
        admitted.value.seat,
        instant,
        stream=stream,
        cancel=cancel,
        probe=probe,
        transition_instant=transition_instant,
    )
    if is_refusal(intents):
        return intents
    return dispatch_hosted_intents(admitted.value, intents.value, path=path)


def _as_admitted_seat(value: object) -> Result[AdmittedNodeSeat]:
    if isinstance(value, AdmittedNodeSeat):
        return Ok(value)
    if isinstance(value, GovernedSeat):
        return policy(
            "seat",
            "hosted intents reach the Book/BMS/protection/order path only from "
            "a seat admitted through propose_node_seat; a raw QL-7 construct "
            "is not a money-path grant (E12-F05)",
            given="GovernedSeat",
        )
    return invalid(
        "seat",
        "the money path drives an AdmittedNodeSeat",
        given=type(value).__name__,
    )


def _as_path(value: object) -> Result[BookPathContext]:
    if isinstance(value, BookPathContext):
        if not value.bms_instance_id.strip():
            return invalid(
                "bms_instance_id",
                "the BMS hop is a non-empty instance id named at seat admission",
            )
        return Ok(value)
    return invalid(
        "path",
        "hosted intents cross a BookPathContext; the callback cannot skip "
        "Book, BMS, protection, or order",
        given=type(value).__name__,
        hops=list(INTENT_PATH_HOPS),
    )


def _as_intent_sequence(value: object) -> Result[tuple[object, ...]]:
    if value is None:
        return Ok(())
    if isinstance(value, (Command, EntryIntent, ExitIntent)):
        return Ok((value,))
    if isinstance(value, Mapping):
        return Ok((cast("object", value),))
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        return invalid(
            "intents",
            "a hosted callback returns zero-or-more CT-23 intents",
            given=type(value).__name__,
        )
    return Ok(tuple(cast("Sequence[object]", value)))


def _refuse_sizing_or_ct19(item: object) -> Result[None]:
    if isinstance(item, Command):
        return refuse_bot_constructed_ct19(item)
    if isinstance(item, Mapping):
        mapping = cast("Mapping[str, object]", item)
        sized = reject_bot_supplied_final_size(mapping)
        if is_refusal(sized):
            return sized
        if "place_order" in mapping or "venue_command" in mapping:
            return refuse_bot_constructed_ct19(mapping)
        extra = BOT_SIZE_FIELDS.intersection(mapping)
        if extra:
            return invalid(
                "size",
                "the bot never supplies final size; quantity is Book-derived",
                fields=tuple(sorted(extra)),
            )
    return Ok(None)
