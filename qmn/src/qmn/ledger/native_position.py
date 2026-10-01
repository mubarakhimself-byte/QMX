"""Checked native-position attribution for risk-reducing CT-19 commands.

This QMN projection joins recorded native evidence to a virtual position through
its durable command binding. It never derives venue identity from correlation,
quantity, account-only or instrument-only coincidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from qmf.core import (
    Account,
    Fingerprint,
    Instrument,
    Ok,
    Result,
    VenueId,
    World,
    WriteOutcome,
    canonical_bytes,
    fingerprint,
    is_refusal,
)
from qmf.core.chrono import DisplayTime, Instant, WriterId
from qmf.data import JournalAppendReceipt, JournalEvent, JournalEventType, JournalWriter
from qmf.data.journal_producer import JournalReader
from qmf.data.store import JournalStore, StoreReceipt
from qmf.data.store.rooms import RoomRole
from qmf.risk.binding import PositionModel
from qmf.risk.paper import ExecutionTarget

from qmn.ledger._refuse import invalid, policy
from qmn.ledger.attribution import (
    AttributionPartition,
    PositionModelKind,
    prove_attribution_partition,
)
from qmn.ledger.binding_ledger import BindingVirtualLedger
from qmn.ledger.virtual import VirtualPosition, VirtualPositionStatus
from qmn.order.identity import NativeExecutionMap
from qmn.venue import CommandIdBinding, QmfCommandIdBindingJournal

__all__ = [
    "NATIVE_POSITION_ATTRIBUTION_CLASS",
    "NATIVE_POSITION_ATTRIBUTION_VERSION",
    "NativePositionAttribution",
    "NativePositionEvidence",
    "resolve_native_position_attribution",
    "write_native_position_attribution",
]

NATIVE_POSITION_ATTRIBUTION_CLASS = "qmn-native-position-attribution"
NATIVE_POSITION_ATTRIBUTION_VERSION = 1


@dataclass(frozen=True, slots=True)
class NativePositionEvidence:
    """Exact checked CT-13 fill and readback events used by the native join."""

    fill_event: JournalEvent
    readback_event: JournalEvent
    fill_stream: str
    readback_stream: str


@dataclass(frozen=True, slots=True)
class NativePositionAttribution:
    """Immutable native subject joined to one binding-scoped open virtual position."""

    venue_id: VenueId
    account: Account
    binding_epoch: Fingerprint
    virtual_position_ref: Fingerprint
    native_position_id: str
    native_account_id: int
    native_symbol_id: int
    position_model: PositionModel
    opening_command_fp1: Fingerprint
    opening_venue_client_id: str
    opening_order_id: str
    opening_deal_id: str
    fill_event_fp1: Fingerprint
    readback_event_fp1: Fingerprint
    native_map_fp1: Fingerprint
    composition_fp1: Fingerprint
    source_frontier_ns: int

    def identity(self) -> dict[str, object]:
        return {
            "account_id": self.account.account_id,
            "account_role": self.account.role.value,
            "binding_epoch_fp1": self.binding_epoch.value,
            "class": NATIVE_POSITION_ATTRIBUTION_CLASS,
            "composition_fp1": self.composition_fp1.value,
            "fill_event_fp1": self.fill_event_fp1.value,
            "format_version": NATIVE_POSITION_ATTRIBUTION_VERSION,
            "native_account_id": self.native_account_id,
            "native_map_fp1": self.native_map_fp1.value,
            "native_position_id": self.native_position_id,
            "native_symbol_id": self.native_symbol_id,
            "opening_command_fp1": self.opening_command_fp1.value,
            "opening_deal_id": self.opening_deal_id,
            "opening_order_id": self.opening_order_id,
            "opening_venue_client_id": self.opening_venue_client_id,
            "position_model": self.position_model.value,
            "readback_event_fp1": self.readback_event_fp1.value,
            "source_frontier_ns": self.source_frontier_ns,
            "venue_id": self.venue_id.value,
            "virtual_position_ref": self.virtual_position_ref.value,
        }


def resolve_native_position_attribution(
    *,
    journal: object,
    authorized_writers: object,
    evidence: object,
    command_binding: object,
    command_binding_journal: object,
    ledger: object,
    position_ref: object,
    target: object,
    instrument: object,
    native_map: object,
    binding_epoch: object,
    composition_fp: object,
    position_model: object,
    binding_id: object,
    netting_partition: object = None,
) -> Result[NativePositionAttribution]:
    """Resolve only when every native, virtual, mapping and journal edge agrees."""
    if not isinstance(journal, JournalStore) or journal.world is not World.LIVE:
        return invalid("journal", "native exit attribution reads checked live CT-13 evidence")
    if type(evidence) is not NativePositionEvidence:
        return invalid("evidence", "native attribution requires checked fill and readback refs")
    if type(command_binding) is not CommandIdBinding:
        return invalid(
            "command_binding", "opening command identity came from its durable CT-19 bind"
        )
    if (
        type(command_binding.command_fp1) is not Fingerprint
        or type(command_binding.venue_client_id) is not str
        or not command_binding.venue_client_id.strip()
        or type(command_binding.account_id) is not str
        or not command_binding.account_id.strip()
        or type(command_binding.session_epoch) is not str
        or not command_binding.session_epoch.strip()
    ):
        return invalid("command_binding", "CT-19 binding fields are exact typed identities")
    if type(command_binding_journal) is not QmfCommandIdBindingJournal:
        return invalid(
            "command_binding_journal", "native attribution requires checked CT-13 bind readback"
        )
    durable_binding = command_binding_journal.binding_for(command_binding.venue_client_id)
    if is_refusal(durable_binding):
        return durable_binding
    if durable_binding.value != command_binding:
        return policy("command_binding", "opening command bind independently reopens from CT-13")
    if type(ledger) is not BindingVirtualLedger:
        return invalid("ledger", "native subject resolves through the binding virtual ledger")
    if type(position_ref) is not Fingerprint:
        return invalid("position_ref", "exit subject names an exact virtual position fingerprint")
    position_ref_parsed = Fingerprint.try_create(position_ref.value)
    if is_refusal(position_ref_parsed):
        return position_ref_parsed
    if type(target) is not ExecutionTarget:
        return invalid("target", "native identity resolves for a typed execution target")
    target_result = ExecutionTarget.try_create(target.role, target.venue_id, target.account_id)
    if is_refusal(target_result):
        return target_result
    target = target_result.value
    if type(instrument) is not Instrument:
        return invalid("instrument", "native identity resolves for an exact instrument")
    instrument_result = Instrument.try_create(instrument.venue, instrument.symbol)
    if is_refusal(instrument_result):
        return instrument_result
    instrument = instrument_result.value
    if type(native_map) is not NativeExecutionMap:
        return invalid("native_map", "native ids come from the pinned immutable CT-18 map")
    if (
        type(native_map.registry_as_of_fingerprint) is not Fingerprint
        or type(native_map.fingerprint) is not Fingerprint
        or (
            native_map.binding_epoch is not None
            and type(native_map.binding_epoch) is not Fingerprint
        )
    ):
        return invalid("native_map", "native map identity fields are exact fingerprints")
    registry_fp = Fingerprint.try_create(native_map.registry_as_of_fingerprint.value)
    map_fp = Fingerprint.try_create(native_map.fingerprint.value)
    if is_refusal(registry_fp):
        return registry_fp
    if is_refusal(map_fp):
        return map_fp
    map_epoch: Fingerprint | None = None
    if native_map.binding_epoch is not None:
        parsed_epoch = Fingerprint.try_create(native_map.binding_epoch.value)
        if is_refusal(parsed_epoch):
            return parsed_epoch
        map_epoch = parsed_epoch.value
    rebuilt_map = NativeExecutionMap.try_create(
        native_map.mappings,
        registry_as_of_fingerprint=registry_fp.value,
        binding_epoch=map_epoch,
    )
    if is_refusal(rebuilt_map) or rebuilt_map.value.fingerprint != map_fp.value:
        return policy("native_map", "native map rows match their recomputed pinned identity")
    native_map = rebuilt_map.value
    if type(binding_epoch) is not Fingerprint or native_map.binding_epoch != binding_epoch:
        return policy("binding_epoch", "native map and virtual subject share the exact CT-28 epoch")
    epoch_parsed = Fingerprint.try_create(binding_epoch.value)
    if is_refusal(epoch_parsed):
        return epoch_parsed
    if type(composition_fp) is not Fingerprint:
        return invalid("composition_fp", "projection cites the sealed composition fingerprint")
    composition_parsed = Fingerprint.try_create(composition_fp.value)
    if is_refusal(composition_parsed):
        return composition_parsed
    if target.venue_id != instrument.venue:
        return policy("instrument", "target, instrument and pinned native venue agree")
    if type(position_model) is not PositionModel:
        return invalid("position_model", "account position model is read from the CT-18 profile")
    mapping = native_map.resolve(target, instrument)
    if is_refusal(mapping):
        return mapping

    authorized = _authorized_writer_ids(authorized_writers)
    if is_refusal(authorized):
        return authorized
    fill_event = _checked_source_event(
        journal, evidence.fill_stream, evidence.fill_event, authorized.value
    )
    if is_refusal(fill_event):
        return fill_event
    readback_event = _checked_source_event(
        journal, evidence.readback_stream, evidence.readback_event, authorized.value
    )
    if is_refusal(readback_event):
        return readback_event
    if fill_event.value.event_type is not JournalEventType.FILL:
        return policy("fill_event", "opening source is the checked CT-13 fill event")
    if readback_event.value.event_type is not JournalEventType.DATA_QUALITY:
        return policy("readback_event", "position readback is checked CT-13 data-quality evidence")
    if readback_event.value.instant.value_ns < fill_event.value.instant.value_ns:
        return policy("readback_event", "position readback is not older than its opening fill")
    fill_payload = _raw_payload(fill_event.value)
    if is_refusal(fill_payload):
        return fill_payload
    readback_payload = _raw_payload(readback_event.value)
    if is_refusal(readback_payload):
        return readback_payload
    native = _native_opening_ids(fill_payload.value)
    if is_refusal(native):
        return native
    position_id, native_account, native_symbol, client_id, order_id, deal_id, session_epoch = (
        native.value
    )
    rows = _position_rows(readback_payload.value)
    if is_refusal(rows):
        return rows
    matches = tuple(
        row for row in rows.value if _native_id_token(row.get("positionId")) == position_id
    )
    if len(matches) != 1:
        return policy("native_position_id", "readback resolves exactly one native position row")
    row = matches[0]
    if (
        type(row.get("accountId")) is not int
        or type(row.get("symbolId")) is not int
        or row.get("accountId") != native_account
        or row.get("symbolId") != native_symbol
        or _native_id_token(row.get("clientOrderId")) != client_id
        or _native_id_token(row.get("orderId")) != order_id
        or _native_id_token(row.get("dealId")) != deal_id
    ):
        return policy(
            "native_lineage", "position readback repeats exact account, symbol and opening lineage"
        )
    if (
        mapping.value.native_account_id != native_account
        or mapping.value.native_symbol_id != native_symbol
        or command_binding.venue_client_id != client_id
        or command_binding.account_id != target.account_id
        or command_binding.session_epoch != session_epoch
    ):
        return policy("native_lineage", "native ids join the pinned map and durable command bind")
    position = ledger.position_by_ref(position_ref)
    if (
        not isinstance(position, VirtualPosition)
        or position.status is not VirtualPositionStatus.OPEN
    ):
        return policy("virtual_position", "native subject resolves to one open virtual position")
    if (
        ledger.binding_epoch != binding_epoch
        or position.position_ref != position_ref
        or position.binding_epoch != binding_epoch
        or position.command_identity != command_binding.command_fp1
        or position.instrument != instrument.symbol
    ):
        return policy("virtual_position", "opening command owns the exact open virtual position")
    try:
        model = PositionModelKind(position_model.value)
    except ValueError:
        return invalid("position_model", "measured CT-18 model is netting or hedging")
    if model is PositionModelKind.NETTING:
        partition = netting_partition
        if type(partition) is not AttributionPartition:
            return policy("netting_attribution", "netting exits require the proved CT-28 partition")
        reproved = prove_attribution_partition(
            account_key=partition.account_key,
            position_model=partition.position_model,
            declarations=partition.declarations,
        )
        if is_refusal(reproved):
            return reproved
        binding_token = binding_id if isinstance(binding_id, str) else ""
        declaration = tuple(
            item for item in partition.declarations if item.binding_id == binding_token
        )
        if (
            reproved.value != partition
            or
            partition.position_model is not PositionModelKind.NETTING
            or partition.account_key != f"{target.venue_id.value}::{target.account_id}"
            or len(declaration) != 1
            or declaration[0].attribution_instruments is None
            or instrument.symbol not in declaration[0].attribution_instruments
        ):
            return policy(
                "netting_attribution",
                "proved netting partition assigns this instrument to exactly this binding",
            )
    frontier = max(fill_event.value.instant.value_ns, readback_event.value.instant.value_ns)
    account = Account.try_create(target.account_id, target.venue_id, target.role)
    if is_refusal(account):
        return account
    return Ok(
        NativePositionAttribution(
            venue_id=target.venue_id,
            account=account.value,
            binding_epoch=binding_epoch,
            virtual_position_ref=position_ref,
            native_position_id=position_id,
            native_account_id=native_account,
            native_symbol_id=native_symbol,
            position_model=position_model,
            opening_command_fp1=command_binding.command_fp1,
            opening_venue_client_id=client_id,
            opening_order_id=order_id,
            opening_deal_id=deal_id,
            fill_event_fp1=fill_event.value.fingerprint,
            readback_event_fp1=readback_event.value.fingerprint,
            native_map_fp1=native_map.fingerprint,
            composition_fp1=composition_fp,
            source_frontier_ns=frontier,
        )
    )


def write_native_position_attribution(
    *,
    journal: object,
    writer: object,
    instant: object,
    attribution: object,
) -> Result[JournalEvent]:
    """Persist a resolved projection as existing CT-13 data-quality evidence."""
    if type(journal) is not JournalStore or journal.world is not World.LIVE:
        return invalid("journal", "native position attribution persists to live CT-13")
    if type(writer) is not JournalWriter or writer.world is not World.LIVE:
        return invalid("writer", "native attribution uses its reserved live CT-13 writer")
    if type(instant) is not Instant:
        return invalid("instant", "native attribution uses an exact wall-clock Instant")
    if type(attribution) is not NativePositionAttribution:
        return invalid("attribution", "persisted native projection is fully resolved and typed")
    identity = attribution.identity()
    written = writer.record(
        JournalEventType.DATA_QUALITY,
        {
            "class": NATIVE_POSITION_ATTRIBUTION_CLASS,
            "format_version": NATIVE_POSITION_ATTRIBUTION_VERSION,
            "attribution": identity,
        },
        instant=instant,
    )
    if is_refusal(written):
        return written
    receipt_value: object = cast(object, written.value)
    if type(receipt_value) is not JournalAppendReceipt:
        return policy("journal_receipt", "append ACK is an exact typed CT-13 receipt")
    receipt = receipt_value
    event_value: object = cast(object, receipt.event)
    physical_value: object = cast(object, receipt.store_receipt)
    edges_value: object = cast(object, receipt.edge_receipts)
    if type(event_value) is not JournalEvent or type(physical_value) is not StoreReceipt:
        return policy("journal_receipt", "append receipt has exact event and physical store types")
    event = event_value
    physical = physical_value
    if (
        type(edges_value) is not tuple
        or edges_value
        or event.event_type is not JournalEventType.DATA_QUALITY
        or type(event.writer) is not WriterId
        or event.writer != writer.writer
        or type(event.sequence) is not int
        or event.sequence != writer.next_sequence - 1
        or type(event.instant) is not Instant
        or event.instant != instant
        or type(event.world) is not World
        or event.world is not World.LIVE
        or (event.correlation_id is not None and type(event.correlation_id) is not str)
        or (event.display_time is not None and type(event.display_time) is not DisplayTime)
        or type(event.fingerprint) is not Fingerprint
        or event.outcome is not None
        or not _same_row_bytes(
            event.payload,
            {
                "class": NATIVE_POSITION_ATTRIBUTION_CLASS,
                "format_version": NATIVE_POSITION_ATTRIBUTION_VERSION,
                "attribution": identity,
            },
        )
        or type(physical.world) is not World
        or physical.world is not World.LIVE
        or type(physical.room_role) is not RoomRole
        or physical.room_role is not RoomRole.JOURNAL
        or type(physical.engine) is not str
        or physical.engine != "jsonl"
        or physical.is_evidence_bearing is not True
        or physical.retained_forever is not True
        or type(physical.sequence) is not int
        or physical.sequence < 0
        or type(physical.format_version) is not int
        or physical.format_version != 1
        or physical.engine_major is not None
        or physical.rebuild_calendar_identity is not None
        or physical.rebuild_tzdata_version is not None
        or type(physical.outcome) is not WriteOutcome
        or type(physical.fingerprint) is not Fingerprint
        or physical.outcome not in {WriteOutcome.STORED, WriteOutcome.IDEMPOTENT}
    ):
        return policy("journal_receipt", "receipt binds exact CT-13 event and physical append")
    event_fp = fingerprint(event.fp1_identity())
    row_fp = fingerprint(event.to_row())
    if (
        is_refusal(event_fp)
        or event_fp.value != event.fingerprint
        or is_refusal(row_fp)
        or row_fp.value != physical.fingerprint
    ):
        return policy("journal_receipt", "event and stored row carry their exact fingerprints")
    checked = JournalReader(journal).read_checked(writer.stream_name, for_world=World.LIVE)
    if is_refusal(checked):
        return checked
    found = tuple(row for row in checked.value if row.fingerprint == event.fingerprint)
    raw_rows = journal.read_stream(writer.stream_name, for_world=World.LIVE)
    if is_refusal(raw_rows):
        return raw_rows
    index = physical.sequence
    if (
        len(found) != 1
        or not _same_event_bytes(found[0], event)
        or index >= len(raw_rows.value)
        or not _same_row_bytes(raw_rows.value[index], event.to_row())
    ):
        return policy("journal_readback", "exact projection row and physical index reopen checked")
    return Ok(event)


def _authorized_writer_ids(value: object) -> Result[frozenset[WriterId]]:
    if not isinstance(value, (set, frozenset, tuple, list)):
        return invalid("authorized_writers", "source authority is an explicit writer-id set")
    items = cast("Sequence[object]", value)
    if not items or any(not isinstance(item, WriterId) for item in items):
        return invalid("authorized_writers", "source authority contains exact WriterIds")
    return Ok(frozenset(cast("WriterId", item) for item in items))


def _checked_source_event(
    journal: JournalStore,
    stream: str,
    source: JournalEvent,
    authorized: frozenset[WriterId],
) -> Result[JournalEvent]:
    if type(source) is not JournalEvent:
        return invalid("source_event", "native evidence reference is an exact JournalEvent")
    stream_value: object = cast(object, stream)
    if (
        type(stream_value) is not str
        or not stream_value.strip()
        or source.writer not in authorized
    ):
        return policy(
            "source_writer", "native source event is from an explicitly authorized writer"
        )
    checked = JournalReader(journal).read_checked(stream, for_world=World.LIVE)
    if is_refusal(checked):
        return checked
    matches = tuple(row for row in checked.value if row.fingerprint == source.fingerprint)
    if len(matches) != 1 or not _same_event_bytes(matches[0], source):
        return policy("source_event", "source reference is the exact checked CT-13 row")
    return Ok(source)


def _same_event_bytes(left: JournalEvent, right: JournalEvent) -> bool:
    left_row = canonical_bytes(left.to_row())
    right_row = canonical_bytes(right.to_row())
    return (
        not is_refusal(left_row)
        and not is_refusal(right_row)
        and left_row.value == right_row.value
    )


def _same_row_bytes(left: object, right: Mapping[str, object]) -> bool:
    left_row = canonical_bytes(left)
    right_row = canonical_bytes(dict(right))
    return (
        not is_refusal(left_row)
        and not is_refusal(right_row)
        and left_row.value == right_row.value
    )


def _raw_payload(event: JournalEvent) -> Result[Mapping[str, object]]:
    raw = event.payload.get("raw_payload")
    if not isinstance(raw, Mapping):
        return invalid("raw_payload", "CT-20 source row retains its verbatim native payload")
    return Ok(cast("Mapping[str, object]", raw))


def _native_opening_ids(
    payload: Mapping[str, object],
) -> Result[tuple[str, int, int, str, str, str, str]]:
    position_id = payload.get("positionId")
    account_id = payload.get("accountId")
    symbol_id = payload.get("symbolId")
    client_id = _native_id_token(payload.get("clientOrderId"))
    order_id = _native_id_token(payload.get("orderId"))
    deal_id = _native_id_token(payload.get("dealId"))
    session_epoch = payload.get("sessionEpoch")
    if (
        (
            type(position_id) is int and position_id < 1
        )
        or (type(position_id) is str and not position_id.strip())
        or type(position_id) not in {str, int}
        or type(account_id) is not int
        or account_id < 1
        or type(symbol_id) is not int
        or symbol_id < 1
        or any(value is None for value in (client_id, order_id, deal_id))
        or type(session_epoch) is not str
        or not session_epoch.strip()
    ):
        return invalid(
            "native_lineage",
            "opening fill carries explicit native PID/account/symbol/order/deal/client ids",
        )
    return Ok(
        (
            str(position_id),
            account_id,
            symbol_id,
            cast("str", client_id),
            cast("str", order_id),
            cast("str", deal_id),
            session_epoch,
        )
    )


def _native_id_token(value: object) -> str | None:
    if type(value) is str and value.strip():
        return value
    if type(value) is int and value >= 1:
        return str(value)
    return None


def _position_rows(payload: Mapping[str, object]) -> Result[tuple[Mapping[str, object], ...]]:
    raw_rows = payload.get("positions")
    if not isinstance(raw_rows, Sequence) or isinstance(raw_rows, (str, bytes)):
        return invalid("positions", "position readback contains its exact row collection")
    rows: list[Mapping[str, object]] = []
    for item in cast("Sequence[object]", raw_rows):
        if not isinstance(item, Mapping):
            return invalid("positions", "each native position readback row is a mapping")
        rows.append(cast("Mapping[str, object]", item))
    return Ok(tuple(rows))
