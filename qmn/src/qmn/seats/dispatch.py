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

from qmf.core import (
    Account,
    ExactRational,
    Fingerprint,
    Instant,
    Instrument,
    Ok,
    PriceDelta,
    Result,
    TypedRefusal,
    UnitKind,
    VenueId,
    fingerprint,
    is_refusal,
)
from qmf.data import JournalEvent, JournalWriter
from qmf.data.store import EvidenceStore, JournalStore
from qmf.risk.binding import BookBindingRecord
from qmf.risk.door import (
    EntryIntent,
    ExitIntent,
    ExitKind,
    ExitLogicModule,
    evaluate_exit_intent,
)
from qmf.risk.exit_policy import ExitPolicy, resolve_exit_policy_entry
from qmf.risk.paper import ExecutionTarget

from qmn.capital.ratchet import (
    BreakevenRatchetOrigin,
    dispatch_originated_breakeven_ratchet,
    originate_breakeven_ratchet,
)
from qmn.ledger.binding_ledger import BindingVirtualLedger
from qmn.ledger.native_position import (
    NativePositionAttribution,
    NativePositionEvidence,
    resolve_native_position_attribution,
    write_native_position_attribution,
)
from qmn.ledger.protection_market import resolve_checked_live_spot_prices
from qmn.ledger.protection_plan import (
    ProtectionRatchetPolicy,
    create_protection_admission_plan,
    find_protection_admission_plan,
    persist_protection_admission_plan,
    resolve_protection_ratchet_policy,
)
from qmn.ledger.protection_state import resolve_checked_native_protection_readback
from qmn.ledger.virtual import VirtualPosition, VirtualPositionStatus
from qmn.order.amend import AmendAtomicity, BookDynamicProtectionPolicy
from qmn.order.door import (
    BOT_SIZE_FIELDS,
    AuthorizedIntent,
    admit_entry_at_book_door,
    mint_place_order_from_authorized,
    reject_bot_supplied_final_size,
)
from qmn.order.identity import NativeExecutionMap, NativeExecutionMapping
from qmn.order.protection import require_venue_resident_protective_stop
from qmn.seats._refuse import invalid, policy
from qmn.seats.admission import AdmittedNodeSeat
from qmn.seats.host import GovernedSeat, drive_governed_seat
from qmn.venue import CloseScope, Command, CommandIdBinding, ProtectionAmendment, RoundingMode

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
    exit_policy: object = None
    protection_ratchet_policy: object = None
    protection_plan_writer: object = None
    protection_plan_journal: object = None
    amend_atomicity: object = None
    dynamic_protection_policy: object = None
    resolved_node_config: object = None


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
    evidence_store: object = None
    spot_events_by_position_ref: Mapping[str, tuple[JournalEvent, ...]] | None = None
    price_digits: object = None
    price_rounding: object = None


@dataclass(frozen=True, slots=True)
class SeatDispatchReceipt:
    """Proof that hosted intents crossed Book / BMS / protection / order."""

    authorized: tuple[AuthorizedIntent, ...]
    commands: tuple[Command, ...]
    hops: tuple[str, ...]
    bms_instance_id: str
    seat_id: str
    exit_attributions: tuple[NativePositionAttribution, ...] = ()
    ratchet_authorizations: tuple[RatchetCommandAuthorization, ...] = ()

    def as_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "bms_instance_id": self.bms_instance_id,
                "command_count": len(self.commands),
                "hops": list(self.hops),
                "intent_count": len(self.authorized),
                "exit_attributions": [item.identity() for item in self.exit_attributions],
                "ratchet_authorizations": [
                    item.as_mapping() for item in self.ratchet_authorizations
                ],
                "seat_id": self.seat_id,
            }
        )


@dataclass(frozen=True, slots=True)
class RatchetCommandAuthorization:
    """Source lineage authorizing one already-originated breakeven command."""

    command_fp1: Fingerprint
    plan_fp1: Fingerprint
    binding_epoch: Fingerprint
    position_ref: Fingerprint
    native_position_id: str
    bot_id: str
    family_id: str
    current_stop_event_fp1: Fingerprint
    spot_event_fp1s: tuple[Fingerprint, ...]
    source_frontier_ns: int

    def as_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "binding_epoch": self.binding_epoch.value,
                "bot_id": self.bot_id,
                "command_fp1": self.command_fp1.value,
                "current_stop_event_fp1": self.current_stop_event_fp1.value,
                "family_id": self.family_id,
                "native_position_id": self.native_position_id,
                "plan_fp1": self.plan_fp1.value,
                "position_ref": self.position_ref.value,
                "source_frontier_ns": self.source_frontier_ns,
                "spot_event_fp1s": [event.value for event in self.spot_event_fp1s],
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
    ratchet_authorizations: list[RatchetCommandAuthorization] = []
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
            exited = authorize_native_exit_intent(
                item, door, seat=admitted.value, ordering_ordinal=ordinal + index
            )
            if is_refusal(exited):
                return exited
            command, attribution, ratchet_authorization = exited.value
            if command is None:
                continue
            commands.append(command)
            if attribution is not None:
                exit_attributions.append(attribution)
            if ratchet_authorization is not None:
                ratchet_authorizations.append(ratchet_authorization)
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
        plan_written = _persist_entry_protection_plan(
            command=command.value,
            authorized=frozen.value,
            seat=admitted.value,
            door=door,
        )
        if is_refusal(plan_written):
            return plan_written
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
            ratchet_authorizations=tuple(ratchet_authorizations),
        )
    )


def _persist_entry_protection_plan(
    *,
    command: Command,
    authorized: AuthorizedIntent,
    seat: AdmittedNodeSeat,
    door: BookPathContext,
) -> Result[None]:
    """Persist full-risk entry lineage when the resolved Book permits dynamic tightening."""
    if door.exit_policy is None:
        return Ok(None)
    if type(door.exit_policy) is not ExitPolicy:
        return invalid("exit_policy", "protection plan resolves a typed Book ExitPolicy")
    if ExitKind.TIGHTEN_PROTECTIVE_STOP not in door.exit_policy.permitted_exit_intent_kinds:
        return Ok(None)
    if not isinstance(door.binding_record, BookBindingRecord):
        return invalid("binding_record", "dynamic protection plan binds the exact CT-28 epoch")
    if type(door.decision_at) is not Instant:
        return invalid("decision_at", "dynamic protection plan is stamped at the admitted frontier")
    resolved_values = _resolve_book_ratchet_values(door)
    if is_refusal(resolved_values):
        return resolved_values
    if (
        door.protection_ratchet_policy is not None
        and door.protection_ratchet_policy != resolved_values.value
    ):
        return policy(
            "protection_ratchet_policy",
            "host value matches actual resolved registry rows",
        )
    if door.protection_plan_writer is None or door.protection_plan_journal is None:
        return policy(
            "protection_plan_writer",
            "dynamic protection requires its durable CT-13 plan writer before order dispatch",
        )
    candidate = seat.proof.candidate
    declaration = candidate.declaration
    family_id = declaration.strategy_family_id.value
    resolved_entry = resolve_exit_policy_entry(door.exit_policy, family_id)
    if is_refusal(resolved_entry):
        return resolved_entry
    binding_epoch = door.binding_record.fingerprint()
    command_fp = command.fingerprint()
    exit_policy_fp = fingerprint(door.exit_policy.fp1_identity())
    if is_refusal(binding_epoch):
        return binding_epoch
    if is_refusal(command_fp):
        return command_fp
    if is_refusal(exit_policy_fp):
        return exit_policy_fp
    values = resolved_values.value
    parameters = command.order_parameters
    if parameters is None or parameters.trade_side not in {"buy", "sell"}:
        return policy("position_side", "ratchet plan retains the exact CT-19 trade side")
    policy_source_identity = {
        "class": "qmn-resolved-book-ratchet-policy-source",
        "format_version": 1,
        "book_definition_fp1": door.binding_record.book_definition_fingerprint.value,
        "binding_epoch_fp1": binding_epoch.value.value,
        "exit_policy_fp1": exit_policy_fp.value.value,
        "resolved_family_entry": resolved_entry.value.fp1_identity(),
        "family_id": family_id,
        "ratchet_config_source": dict(values.source_identity),
        "registry_values": {
            "breakeven_ratchet_trigger": values.trigger.fp1_identity(),
            "breakeven_ratchet_offset": values.offset.fp1_identity(),
            "amend_min_improvement": values.amend_min_improvement.fp1_identity(),
        },
    }
    plan = create_protection_admission_plan(
        command_fp1=command_fp.value,
        binding_epoch=binding_epoch.value,
        bot_id=candidate.fingerprint.value,
        family_id=family_id,
        direction="long" if parameters.trade_side == "buy" else "short",
        reference_price=door.entry_price,
        original_risk_distance=authorized.faces.original_risk_distance,
        trigger=values.trigger,
        offset=values.offset,
        amend_min_improvement=values.amend_min_improvement,
        policy_source_identity=policy_source_identity,
    )
    if is_refusal(plan):
        return plan
    persisted = persist_protection_admission_plan(
        plan.value,
        writer=door.protection_plan_writer,
        journal=door.protection_plan_journal,
        stream_name=getattr(door.protection_plan_writer, "stream_name", None),
        at=door.decision_at,
    )
    if is_refusal(persisted):
        return persisted
    return Ok(None)


def _resolve_book_ratchet_values(door: BookPathContext) -> Result[ProtectionRatchetPolicy]:
    if type(door.binding_record) is not BookBindingRecord:
        return invalid("binding_record", "ratchet config resolves under the exact CT-28 Book")
    instrument = getattr(door.entry_price, "instrument", None)
    return resolve_protection_ratchet_policy(
        config=door.resolved_node_config,
        book_definition_fp1=door.binding_record.book_definition_fingerprint,
        book_instance_id=door.binding_record.book_instance_id.value,
        instrument=instrument,
    )


def authorize_native_exit_intent(
    intent: ExitIntent,
    door: BookPathContext,
    *,
    seat: object,
    ordering_ordinal: int,
    persist_projection: bool = True,
) -> Result[
    tuple[
        Command | None,
        NativePositionAttribution | None,
        RatchetCommandAuthorization | None,
    ]
]:
    """Resolve a native close subject; optionally persist its CT-13 projection."""
    if type(persist_projection) is not bool:
        return invalid("persist_projection", "projection mode is an exact bool")
    if type(seat) is not AdmittedNodeSeat:
        return invalid("seat", "native close is dispatched only for a fully admitted node seat")
    evaluated = evaluate_exit_intent(intent)
    if is_refusal(evaluated):
        return evaluated
    if intent.kind not in {ExitKind.CLOSE_FULL, ExitKind.TIGHTEN_PROTECTIVE_STOP}:
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
    binding_record = door.binding_record
    if type(binding_record) is not BookBindingRecord:
        return invalid("binding_record", "native close requires the active CT-28 Book binding")
    epoch = binding_record.fingerprint()
    if is_refusal(epoch):
        return epoch
    candidate = seat.proof.candidate
    declaration = candidate.declaration
    family_id = declaration.strategy_family_id.value
    account = door.account
    if type(account) is not Account:
        return invalid("account", "native close uses the exact bound Book account")
    if (
        seat.binding_ref != epoch.value.value
        or seat.proof.bms_instance_id != binding_record.bms_instance_id.value
        or door.bms_instance_id != seat.proof.bms_instance_id
        or binding_record.venue_id != door.venue_id
        or binding_record.account_id != account.account_id
        or ledger.binding_epoch != epoch.value
        or position.binding_epoch != epoch.value
        or position.bot_id != candidate.fingerprint.value
        or intent.reason_code.book_family != family_id
    ):
        return policy(
            "book_exit_identity",
            "CT-28, BMS, open virtual position, selected Bot, family and declared exit kind agree",
        )
    if intent.kind.value not in declaration.permitted_exit_intents:
        return policy(
            "exit_intent",
            "the selected Bot declaration permits this exact hosted exit kind",
            exit_kind=intent.kind.value,
        )
    policy_record = door.exit_policy
    if type(policy_record) is not ExitPolicy:
        return invalid("exit_policy", "native close requires the Book's typed ExitPolicy")
    if intent.kind not in policy_record.permitted_exit_intent_kinds:
        return policy("exit_policy", "the Book ExitPolicy permits this exact exit kind")
    resolved_policy = resolve_exit_policy_entry(policy_record, family_id)
    if is_refusal(resolved_policy):
        return resolved_policy
    if (
        type(door.exit_logic_ref) is not type(resolved_policy.value.entry)
        or door.exit_logic_ref != resolved_policy.value.entry
        or not isinstance(door.module, ExitLogicModule)
    ):
        return policy(
            "exit_logic_ref",
            "the Book executes the selected family ExitPolicy entry through its typed module",
        )
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
    if type(door.decision_at) is not Instant:
        return invalid("decision_at", "native exit requires the current typed decision frontier")
    if (
        authority.target.venue_id != door.venue_id
        or authority.target.account_id != account.account_id
        or authority.target.role != account.role
        or command_binding.account_id != authority.target.account_id
        or command_binding.session_epoch != door.session_epoch
    ):
        return policy(
            "native_exit_identity",
            "native target, Book account, venue, role and opening session match exactly",
        )
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
    if resolved.value.source_frontier_ns > door.decision_at.value_ns:
        return policy(
            "native_exit_frontier",
            "native close decision is not earlier than checked opening fill and readback evidence",
            source_frontier_ns=resolved.value.source_frontier_ns,
            decision_at_ns=door.decision_at.value_ns,
        )
    if intent.kind is ExitKind.TIGHTEN_PROTECTIVE_STOP:
        tightened = _authorize_native_ratchet(
            intent=intent,
            door=door,
            seat=seat,
            position=position,
            mapping=mappings[0],
            evidence=evidence,
            attribution=resolved.value,
            persist_projection=persist_projection,
            ordering_ordinal=ordering_ordinal,
        )
        return tightened
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
    if persist_projection:
        persisted = write_native_position_attribution(
            journal=authority.journal,
            writer=authority.projection_writer,
            instant=door.decision_at,
            attribution=resolved.value,
        )
        if is_refusal(persisted):
            return persisted
    return Ok((command.value, resolved.value, None))


def _authorize_native_ratchet(
    *,
    intent: ExitIntent,
    door: BookPathContext,
    seat: AdmittedNodeSeat,
    position: VirtualPosition,
    mapping: object,
    evidence: NativePositionEvidence,
    attribution: NativePositionAttribution,
    persist_projection: bool,
    ordering_ordinal: int,
) -> Result[
    tuple[
        Command | None,
        NativePositionAttribution | None,
        RatchetCommandAuthorization | None,
    ]
]:
    """Originate one admitted Book ratchet from durable plan and checked price sources."""
    authority = door.native_exit_authority
    if not isinstance(authority, NativeExitAuthority):
        return invalid("native_exit_authority", "ratchet sources carry typed native authority")
    binding_record = cast(BookBindingRecord, door.binding_record)
    venue_id = cast(VenueId, door.venue_id)
    account = cast(Account, door.account)
    plan_journal = cast(JournalStore, door.protection_plan_journal)
    plan_writer = door.protection_plan_writer
    if type(plan_writer) is not JournalWriter:
        return policy("protection_plan_writer", "ratchet reopens the plan from its exact stream")
    if (
        intent.tighten is None
        or type(authority.evidence_store) is not EvidenceStore
        or not isinstance(authority.spot_events_by_position_ref, Mapping)
        or type(authority.price_digits) is not int
        or isinstance(authority.price_digits, bool)
        or not isinstance(authority.price_rounding, RoundingMode)
        or type(door.protection_plan_journal) is not type(authority.journal)
        or type(door.protection_plan_journal) is not JournalStore
        or type(door.decision_at) is not Instant
    ):
        return policy(
            "protection_evidence",
            "ratchet requires durable Book plan, joined current stop and checked LIVE quote "
            "sources",
        )
    epoch = binding_record.fingerprint()
    if is_refusal(epoch):
        return epoch
    plan = find_protection_admission_plan(
        journal=plan_journal,
        stream_name=plan_writer.stream_name,
        command_fp1=position.command_identity,
        binding_epoch=epoch.value,
    )
    if is_refusal(plan):
        return plan
    candidate = seat.proof.candidate
    family = candidate.declaration.strategy_family_id.value
    exit_policy = cast(ExitPolicy, door.exit_policy)
    resolved_entry = resolve_exit_policy_entry(exit_policy, family)
    if is_refusal(resolved_entry):
        return resolved_entry
    exit_policy_fp = fingerprint(exit_policy.fp1_identity())
    if is_refusal(exit_policy_fp):
        return exit_policy_fp
    resolved_values = _resolve_book_ratchet_values(door)
    if is_refusal(resolved_values):
        return resolved_values
    registry_values = resolved_values.value
    expected_source: dict[str, object] = {
        "class": "qmn-resolved-book-ratchet-policy-source",
        "format_version": 1,
        "book_definition_fp1": binding_record.book_definition_fingerprint.value,
        "binding_epoch_fp1": epoch.value.value,
        "exit_policy_fp1": exit_policy_fp.value.value,
        "resolved_family_entry": resolved_entry.value.fp1_identity(),
        "family_id": family,
        "ratchet_config_source": dict(registry_values.source_identity),
        "registry_values": {
            "breakeven_ratchet_trigger": registry_values.trigger.fp1_identity(),
            "breakeven_ratchet_offset": registry_values.offset.fp1_identity(),
            "amend_min_improvement": registry_values.amend_min_improvement.fp1_identity(),
        },
    }
    if (
        plan.value.plan.command_fp1 != position.command_identity
        or plan.value.plan.binding_epoch != epoch.value
        or plan.value.plan.bot_id != candidate.fingerprint.value
        or plan.value.plan.family_id != family
        or plan.value.plan.policy.source_identity != expected_source
        or plan.value.plan.direction not in {"long", "short"}
        or plan.value.event.instant.value_ns > attribution.source_frontier_ns
    ):
        return policy(
            "protection_plan",
            "persisted Book plan matches the exact position, Bot, family, epoch and "
            "registered policy",
        )
    binding = authority.binding_by_position_ref.get(intent.virtual_position_ref.value)
    native_mapping = cast(NativeExecutionMapping, mapping)
    instrument = native_mapping.instrument
    symbol_id = native_mapping.native_symbol_id
    if type(binding) is not CommandIdBinding or type(instrument) is not Instrument:
        return policy("protection_context", "ratchet reuses the checked native position binding")
    current_stop = resolve_checked_native_protection_readback(
        journal=authority.journal,
        journal_stream=evidence.readback_stream,
        evidence_store=authority.evidence_store,
        source_event=evidence.readback_event,
        authorized_writers=authority.authorized_writers,
        expected_position_id=attribution.native_position_id,
        expected_account_id=attribution.native_account_id,
        expected_session_epoch=binding.session_epoch,
        expected_symbol_id=symbol_id,
        instrument=instrument,
        price_digits=authority.price_digits,
        rounding=authority.price_rounding,
    )
    if is_refusal(current_stop):
        return current_stop
    stop_distance = (
        plan.value.plan.reference_price.subtract(current_stop.value.stop_loss)
        if plan.value.plan.direction == "long"
        else current_stop.value.stop_loss.subtract(plan.value.plan.reference_price)
    )
    if is_refusal(stop_distance):
        return stop_distance
    spot_events = authority.spot_events_by_position_ref.get(
        intent.virtual_position_ref.value
    )
    if type(spot_events) is not tuple or not spot_events:
        return policy("spot_events", "ratchet reads recorded live spot frontiers after admission")
    best_excursion = ExactRational.try_create(0, 1, UnitKind.R_MULTIPLE)
    if is_refusal(best_excursion):
        return best_excursion
    latest_source_ns = attribution.source_frontier_ns
    for spot_event in spot_events:
        prices = resolve_checked_live_spot_prices(
            journal=authority.journal,
            journal_stream=evidence.readback_stream,
            evidence_store=authority.evidence_store,
            source_event=spot_event,
            authorized_writers=authority.authorized_writers,
            instrument=instrument,
            expected_venue_id=venue_id.value,
            expected_account_id=attribution.native_account_id,
            expected_session_epoch=binding.session_epoch,
            not_before=plan.value.event.instant,
            decision_at=door.decision_at,
        )
        if is_refusal(prices):
            return prices
        if spot_event.instant.value_ns < attribution.source_frontier_ns:
            continue
        quote = prices.value.bid if plan.value.plan.direction == "long" else prices.value.ask
        favorable = (
            quote.subtract(plan.value.plan.reference_price)
            if plan.value.plan.direction == "long"
            else plan.value.plan.reference_price.subtract(quote)
        )
        if is_refusal(favorable):
            return favorable
        if favorable.value.as_fraction() > 0:
            ratio = favorable.value.as_fraction() / (
                plan.value.plan.original_risk_distance.as_fraction()
            )
            candidate_r = ExactRational.try_create(
                ratio.numerator, ratio.denominator, UnitKind.R_MULTIPLE
            )
            if is_refusal(candidate_r):
                return candidate_r
            if candidate_r.value.as_fraction() > best_excursion.value.as_fraction():
                best_excursion = candidate_r
        latest_source_ns = max(latest_source_ns, spot_event.instant.value_ns)
    if latest_source_ns > door.decision_at.value_ns:
        return policy("spot_frontier", "ratchet source prices are not later than decision time")
    if intent.tighten.bound.instrument != instrument or (
        intent.tighten.bound.scale != plan.value.plan.reference_price.scale
    ):
        return policy("tighten_bound", "intent bound shares the admitted instrument and scale")
    moved = stop_distance.value.as_fraction() - registry_values.offset.as_fraction()
    if moved > intent.tighten.bound.as_fraction():
        return policy("tighten_bound", "Book-originated stop move stays within the intent bound")
    proposal = originate_breakeven_ratchet(
        original_risk_distance=plan.value.plan.original_risk_distance,
        current_stop_distance=stop_distance.value,
        favorable_excursion=best_excursion.value,
        reference_price=plan.value.plan.reference_price,
        trigger=plan.value.plan.policy.trigger,
        offset=plan.value.plan.policy.offset,
        amend_min_improvement=plan.value.plan.policy.amend_min_improvement,
    )
    if is_refusal(proposal):
        return proposal
    if proposal.value.origin is BreakevenRatchetOrigin.NOT_YET:
        return Ok((None, None, None))
    if (
        type(door.amend_atomicity) is not AmendAtomicity
        or door.dynamic_protection_policy
        is not BookDynamicProtectionPolicy.SINGLE_SIDED_BREAKEVEN_RATCHET
    ):
        return policy("amend_policy", "ratchet amendment has the exact measured Book/order policy")
    amendment = proposal.value.amendment
    if amendment is None:
        return policy("amendment", "originated ratchet includes its exact stop amendment")
    signed_offset = PriceDelta.try_create(
        -registry_values.offset.value
        if plan.value.plan.direction == "long"
        else registry_values.offset.value,
        registry_values.offset.instrument,
        registry_values.offset.scale,
    )
    if is_refusal(signed_offset):
        return signed_offset
    signed_amendment = ProtectionAmendment.try_create(
        amendment.protection_side,
        signed_offset.value,
        amendment.reference_price,
        original_risk_distance=amendment.original_risk_distance,
    )
    if is_refusal(signed_amendment):
        return signed_amendment
    command = Command.amend_protection(
        venue_id,
        account,
        door.session_epoch,
        ordering_ordinal,
        signed_amendment.value,
        attribution.native_position_id,
    )
    if is_refusal(command):
        return command
    admitted = dispatch_originated_breakeven_ratchet(
        command.value,
        atomicity=door.amend_atomicity,
        breakeven_offset=signed_offset.value,
    )
    if is_refusal(admitted):
        return admitted
    command_fp = command.value.fingerprint()
    if is_refusal(command_fp):
        return command_fp
    if persist_projection:
        persisted = write_native_position_attribution(
            journal=authority.journal,
            writer=authority.projection_writer,
            instant=door.decision_at,
            attribution=attribution,
        )
        if is_refusal(persisted):
            return persisted
    authorization = RatchetCommandAuthorization(
        command_fp1=command_fp.value,
        plan_fp1=plan.value.plan_fp1,
        binding_epoch=epoch.value,
        position_ref=intent.virtual_position_ref,
        native_position_id=attribution.native_position_id,
        bot_id=plan.value.plan.bot_id,
        family_id=plan.value.plan.family_id,
        current_stop_event_fp1=evidence.readback_event.fingerprint,
        spot_event_fp1s=tuple(event.fingerprint for event in spot_events),
        source_frontier_ns=latest_source_ns,
    )
    return Ok((command.value, attribution, authorization))


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
