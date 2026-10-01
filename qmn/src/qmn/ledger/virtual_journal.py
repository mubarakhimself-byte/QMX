"""Private CT-13 persistence adapter for binding virtual-ledger state."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

from qmf.core import (
    DisplayTime,
    Fingerprint,
    Instant,
    Instrument,
    Money,
    Ok,
    PriceDelta,
    Quantity,
    Result,
    SinkAck,
    VenueId,
    World,
    WriteOutcome,
    WriterId,
    fingerprint,
    is_refusal,
)
from qmf.data import (
    JournalAppendReceipt,
    JournalEvent,
    JournalEventType,
    JournalReader,
    JournalWriter,
)
from qmf.data.store import JournalStore, StoreReceipt
from qmf.data.store.rooms import RoomRole
from qmf.risk.r_faces import RFaces

from qmn.ledger._refuse import invalid, policy
from qmn.ledger.binding_ledger import LedgerRecord, LedgerRecordKind
from qmn.ledger.virtual import (
    ADMISSION_PLAN_EDGE,
    ExecutionQualityEvidence,
    PositionKind,
    VirtualPosition,
    VirtualPositionStatus,
    mint_virtual_position,
    rebase_partial_entry,
)

__all__ = ["QmfVirtualLedgerJournal", "VirtualLedgerRecovery", "VirtualLedgerRow"]

_ROW_CLASS = "qmn-binding-virtual-ledger-row"
_STREAM_CLASS = "qmn-binding-virtual-ledger-journal"


@dataclass(frozen=True, slots=True)
class VirtualLedgerRow:
    record: LedgerRecord
    position: VirtualPosition | None

    def as_mapping(self) -> Mapping[str, object]:
        body: dict[str, object] = {
            "class": _ROW_CLASS,
            "format_version": 1,
            "record": dict(self.record.storage_mapping()),
        }
        if self.position is not None:
            body["position"] = self.position.storage_mapping()
        return body


@dataclass(frozen=True, slots=True)
class VirtualLedgerRecovery:
    binding_epoch: Fingerprint
    rows: tuple[VirtualLedgerRow, ...]
    committed_high_water: int
    complete: bool


@dataclass(frozen=True, slots=True)
class QmfVirtualLedgerJournal:
    """Append and recover binding-ledger rows through the checked CT-13 journal."""

    journal: JournalStore
    writer: JournalWriter
    instant: Callable[[], Instant]

    @classmethod
    def resume(
        cls,
        journal: JournalStore,
        writer_id: WriterId,
        *,
        stream_name: str,
        instant: Callable[[], Instant],
    ) -> Result[QmfVirtualLedgerJournal]:
        resumed = JournalWriter.resume(journal, writer_id, stream_name=stream_name)
        if is_refusal(resumed):
            return resumed
        return Ok(cls(journal=journal, writer=resumed.value, instant=instant))

    def append(self, event: object, /) -> Result[SinkAck]:
        row = _parse_row(event)
        if is_refusal(row):
            return row
        at = cast(object, self.instant())
        if not isinstance(at, Instant):
            return invalid("instant", "virtual-ledger journal clock returns an Instant")
        payload: Mapping[str, object] = {
            "class": _STREAM_CLASS,
            "row": dict(row.value.as_mapping()),
        }
        persisted = self.writer.record(JournalEventType.RISK_TRANSITION, payload, instant=at)
        if is_refusal(persisted):
            return persisted
        if not _receipt_matches(
            persisted.value,
            journal=self.journal,
            writer=self.writer.writer,
            stream_name=self.writer.stream_name,
            payload=payload,
            instant=at,
            expected_sequence=self.writer.next_sequence - 1,
        ):
            return _corrupt("append receipt is not the exact physical CT-13 row")
        checked = JournalReader(self.journal).read_checked(
            self.writer.stream_name, for_world=self.journal.world
        )
        if is_refusal(checked):
            return checked
        if not any(e.fingerprint == persisted.value.event.fingerprint for e in checked.value):
            return _corrupt("row is absent from the checked CT-13 readback")
        return Ok(
            SinkAck({"complete": True, "fingerprint": persisted.value.event.fingerprint.value})
        )

    def recover(self, binding_epoch: object) -> Result[VirtualLedgerRecovery]:
        if not isinstance(binding_epoch, Fingerprint):
            return invalid("binding_epoch", "virtual-ledger recovery requires an fp1 binding")
        if self.writer.is_blocked:
            retried = self.writer.retry_blocked()
            if is_refusal(retried):
                return retried
        checked = JournalReader(self.journal).read_checked(
            self.writer.stream_name, for_world=self.journal.world
        )
        if is_refusal(checked):
            return checked
        rows: list[VirtualLedgerRow] = []
        for event in checked.value:
            if event.event_type is not JournalEventType.RISK_TRANSITION:
                return _corrupt("dedicated virtual-ledger stream contains a foreign event type")
            if (
                event.writer.machine != self.writer.writer.machine
                or event.writer.role != self.writer.writer.role
                or event.writer.stream != self.writer.writer.stream
            ):
                return _corrupt("virtual-ledger row writer is outside the configured writer unit")
            payload = event.payload
            if payload.get("class") != _STREAM_CLASS:
                return _corrupt("dedicated virtual-ledger stream contains an unrecognized row")
            raw = payload.get("row")
            parsed = _parse_row(raw)
            if is_refusal(parsed):
                return parsed
            if parsed.value.record.binding_epoch != binding_epoch:
                return _corrupt("virtual-ledger row belongs to another binding epoch")
            rows.append(parsed.value)
        if rows and rows[0].record.kind is not LedgerRecordKind.SEED:
            return _corrupt("complete virtual-ledger prefix begins with its durable seed row")
        if any(row.record.sequence != i for i, row in enumerate(rows, start=1)):
            return _corrupt("virtual-ledger logical sequence is contiguous from seed")
        return Ok(
            VirtualLedgerRecovery(
                binding_epoch=binding_epoch,
                rows=tuple(rows),
                committed_high_water=len(rows),
                complete=True,
            )
        )


def _parse_row(value: object) -> Result[VirtualLedgerRow]:
    if not isinstance(value, Mapping):
        return invalid("virtual_ledger_row", "row is a typed mapping")
    source = cast("Mapping[str, object]", value)
    if (
        source.get("class") != _ROW_CLASS
        or type(source.get("format_version")) is not int
        or source.get("format_version") != 1
    ):
        return invalid("virtual_ledger_row", "row uses private format version 1")
    record_raw = source.get("record")
    if not isinstance(record_raw, Mapping):
        return invalid("virtual_ledger_row", "row contains its ledger record")
    record = _parse_record(cast("Mapping[str, object]", record_raw))
    if is_refusal(record):
        return record
    position_raw = source.get("position")
    if position_raw is None:
        position = None
    else:
        parsed_position = _parse_position(position_raw)
        if is_refusal(parsed_position):
            return parsed_position
        position = parsed_position.value
    if record.value.position_ref != (None if position is None else position.position_ref):
        return _corrupt("position reference differs from the row's exact position state")
    return Ok(VirtualLedgerRow(record.value, position))


def _parse_record(source: Mapping[str, object]) -> Result[LedgerRecord]:
    try:
        kind = LedgerRecordKind(source.get("kind"))
    except (TypeError, ValueError):
        return invalid("ledger_record", "record kind is one of the virtual-ledger kinds")
    epoch = Fingerprint.try_create(source.get("binding_epoch"))
    at_raw: object = source.get("recorded_at")
    if not isinstance(at_raw, Mapping):
        return invalid("ledger_record", "record carries its exact Instant")
    at_mapping = cast("Mapping[str, object]", at_raw)
    at = Instant.try_create(at_mapping.get("value_ns"))
    seq, scale = source.get("sequence"), source.get("money_scale")
    if is_refusal(epoch):
        return epoch
    if is_refusal(at):
        return at
    if type(seq) is not int or seq < 1 or type(scale) is not int or scale < 0:
        return invalid("ledger_record", "record sequence and money scale are exact integers")
    cash: Money | None = None
    if "cash_delta_value" in source:
        cash_result = Money.try_create(
            source.get("cash_delta_value"),
            source.get("cash_delta_currency"),
            source.get("cash_delta_scale"),
        )
        if is_refusal(cash_result):
            return cash_result
        cash = cash_result.value
    position_ref = None
    if source.get("position_ref") is not None:
        pos = Fingerprint.try_create(source.get("position_ref"))
        if is_refusal(pos):
            return pos
        position_ref = pos.value
    command = None
    if source.get("command_identity") is not None:
        cmd = Fingerprint.try_create(source.get("command_identity"))
        if is_refusal(cmd):
            return cmd
        command = cmd.value
    note = source.get("note")
    if note is not None and not isinstance(note, str):
        return invalid("ledger_record", "optional note is text")
    native_id = source.get("fill_native_id")
    if native_id is not None and not isinstance(native_id, str):
        return invalid("ledger_record", "optional venue-native fill id is text")
    fill_identity: Fingerprint | None = None
    if source.get("fill_identity") is not None:
        parsed_fill_identity = Fingerprint.try_create(source.get("fill_identity"))
        if is_refusal(parsed_fill_identity):
            return parsed_fill_identity
        fill_identity = parsed_fill_identity.value
    if (native_id is None) != (fill_identity is None):
        return invalid("ledger_record", "fill id and fp1 identity are persisted together")
    record = LedgerRecord(
        kind,
        epoch.value,
        seq,
        at.value,
        cash,
        position_ref,
        command,
        scale,
        note,
        native_id,
        fill_identity,
    )
    if dict(record.storage_mapping()) != dict(source):
        return _corrupt("ledger record does not reproduce its exact stored representation")
    return Ok(record)


def _parse_position(value: object) -> Result[VirtualPosition]:
    if not isinstance(value, Mapping):
        return invalid("position", "persisted position is a mapping")
    source = cast("Mapping[str, object]", value)
    identity = source.get("identity")
    if not isinstance(identity, Mapping):
        return invalid("position", "persisted position carries fp1 identity")
    body = cast("Mapping[str, object]", identity)
    required = ("faces", "admission_faces", "admitted_quantity", "filled_quantity")
    if any(not isinstance(source.get(key), Mapping) for key in required):
        return invalid("position", "persisted position carries exact quantities and R faces")
    qty = _parse_quantity(cast("Mapping[str, object]", source["admitted_quantity"]))
    filled = _parse_quantity(cast("Mapping[str, object]", source["filled_quantity"]))
    faces = _parse_faces(cast("Mapping[str, object]", source["faces"]))
    admission_faces = _parse_faces(cast("Mapping[str, object]", source["admission_faces"]))
    if is_refusal(qty):
        return qty
    if is_refusal(filled):
        return filled
    if is_refusal(faces):
        return faces
    if is_refusal(admission_faces):
        return admission_faces
    position_ref_result = Fingerprint.try_create(body.get("position_ref"))
    binding_result = Fingerprint.try_create(body.get("binding_epoch"))
    admission_result = Fingerprint.try_create(body.get("admission_identity"))
    command_result = Fingerprint.try_create(body.get("command_identity"))
    if is_refusal(position_ref_result):
        return position_ref_result
    if is_refusal(binding_result):
        return binding_result
    if is_refusal(admission_result):
        return admission_result
    if is_refusal(command_result):
        return command_result
    instrument = body.get("instrument")
    bot = body.get("bot_id")
    status_raw = body.get("status")
    kind_raw = body.get("position_kind")
    if (
        not isinstance(instrument, str)
        or not isinstance(bot, str)
        or type(body.get("rebased")) is not bool
    ):
        return invalid("position", "position identity fields are typed")
    try:
        status = VirtualPositionStatus(status_raw)
        position_kind = PositionKind(kind_raw)
    except (TypeError, ValueError):
        return invalid("position", "position status and kind are closed values")
    edge = body.get("admission_plan_edge")
    if edge is not None and not isinstance(edge, str):
        return invalid("position", "optional admission-plan edge is text")
    quality = _parse_quality(source.get("execution_quality_storage"))
    if is_refusal(quality):
        return quality
    position_ref = position_ref_result.value
    binding_epoch = binding_result.value
    admission_identity = admission_result.value
    command_identity = command_result.value
    position = VirtualPosition(
        position_ref=position_ref,
        binding_epoch=binding_epoch,
        instrument=instrument,
        bot_id=bot,
        admission_identity=admission_identity,
        command_identity=command_identity,
        faces=faces.value,
        admission_faces=admission_faces.value,
        admitted_quantity=qty.value,
        filled_quantity=filled.value,
        status=status,
        rebased=cast(bool, body["rebased"]),
        position_kind=position_kind,
        admission_plan_edge=edge,
        execution_quality=quality.value,
    )
    if position.fp1_identity() != dict(body):
        return _corrupt("position state does not reproduce its stored fp1 identity")
    if position.position_kind is not PositionKind.VIRTUAL:
        return _corrupt("binding virtual ledger cannot recover a venue position")
    admitted_position = mint_virtual_position(
        binding_epoch=position.binding_epoch,
        instrument=position.instrument,
        bot_id=position.bot_id,
        admission_identity=position.admission_identity,
        command_identity=position.command_identity,
        faces=position.admission_faces,
        admitted_quantity=position.admitted_quantity,
        filled_quantity=position.filled_quantity,
    )
    if is_refusal(admitted_position):
        return admitted_position
    if admitted_position.value.position_ref != position.position_ref:
        return _corrupt("position reference does not derive from its binding/admission/command")
    if position.rebased:
        rebased = rebase_partial_entry(
            admitted_position.value,
            filled_quantity=position.filled_quantity,
            terminal=True,
        )
        if is_refusal(rebased):
            return rebased
        expected_position = rebased.value[0]
        if (
            expected_position.faces != position.faces
            or expected_position.admission_plan_edge != ADMISSION_PLAN_EDGE
            or expected_position.execution_quality != position.execution_quality
        ):
            return _corrupt("partial-entry rebase equals the exact AD-40 quantity fold")
    elif (
        position.faces != position.admission_faces
        or position.admission_plan_edge is not None
        or position.execution_quality is not None
    ):
        return _corrupt(
            "unrebased position retains its admission faces without short-fill evidence"
        )
    return Ok(position)


def _parse_quantity(source: Mapping[str, object]) -> Result[Quantity]:
    return Quantity.try_create(source.get("value"), source.get("unit"), source.get("scale"))


def _parse_faces(source: Mapping[str, object]) -> Result[RFaces]:
    distance_raw, amount_raw = (
        source.get("original_risk_distance"),
        source.get("original_risk_amount"),
    )
    if not isinstance(distance_raw, Mapping) or not isinstance(amount_raw, Mapping):
        return invalid("faces", "persisted R faces contain distance and amount")
    distance = cast("Mapping[str, object]", distance_raw)
    amount = cast("Mapping[str, object]", amount_raw)
    venue = VenueId.try_create(distance.get("venue"))
    if is_refusal(venue):
        return venue
    inst = Instrument.try_create(venue.value, distance.get("symbol"))
    if is_refusal(inst):
        return inst
    delta = PriceDelta.try_create(distance.get("value"), inst.value, distance.get("scale"))
    money = Money.try_create(amount.get("value"), amount.get("currency"), amount.get("scale"))
    if is_refusal(delta):
        return delta
    if is_refusal(money):
        return money
    return RFaces.try_create(delta.value, money.value)


def _parse_quality(value: object) -> Result[ExecutionQualityEvidence | None]:
    if value is None:
        return Ok(None)
    if not isinstance(value, Mapping):
        return invalid("execution_quality", "quality evidence is a mapping")
    source = cast("Mapping[str, object]", value)
    try:
        kind = source["kind"]
        admitted_raw = source["admitted_quantity"]
        filled_raw = source["filled_quantity"]
        shortfall_raw = source["shortfall"]
    except KeyError:
        return invalid("execution_quality", "quality evidence carries all typed fields")
    if not isinstance(kind, str) or any(
        not isinstance(item, Mapping) for item in (admitted_raw, filled_raw, shortfall_raw)
    ):
        return invalid("execution_quality", "quality evidence carries text and quantities")
    admitted = _parse_quantity(cast("Mapping[str, object]", admitted_raw))
    filled = _parse_quantity(cast("Mapping[str, object]", filled_raw))
    shortfall = _parse_quantity(cast("Mapping[str, object]", shortfall_raw))
    if is_refusal(admitted):
        return admitted
    if is_refusal(filled):
        return filled
    if is_refusal(shortfall):
        return shortfall
    return Ok(ExecutionQualityEvidence(kind, admitted.value, filled.value, shortfall.value))


def _receipt_matches(
    value: object,
    *,
    journal: JournalStore,
    writer: WriterId,
    stream_name: str,
    payload: Mapping[str, object],
    instant: Instant,
    expected_sequence: int,
) -> bool:
    if not isinstance(value, JournalAppendReceipt):
        return False
    event_value, physical_value = cast(object, value.event), cast(object, value.store_receipt)
    if not isinstance(event_value, JournalEvent) or not isinstance(physical_value, StoreReceipt):
        return False
    if type(value.edge_receipts) is not tuple or value.edge_receipts:
        return False
    event, physical = event_value, physical_value
    event_writer = cast(object, event.writer)
    event_instant = cast(object, event.instant)
    event_world = cast(object, event.world)
    event_identity = cast(object, event.fingerprint)
    event_payload = cast(object, event.payload)
    event_correlation = cast(object, event.correlation_id)
    event_display = cast(object, event.display_time)
    if (
        event.event_type is not JournalEventType.RISK_TRANSITION
        or not isinstance(event_writer, WriterId)
        or type(event.sequence) is not int
        or event.sequence != expected_sequence
        or not isinstance(event_instant, Instant)
        or not isinstance(event_world, World)
        or not isinstance(event_identity, Fingerprint)
        or not isinstance(event_payload, Mapping)
        or event.outcome is not None
        or (event_correlation is not None and not isinstance(event_correlation, str))
        or (event_display is not None and not isinstance(event_display, DisplayTime))
    ):
        return False
    event_fp = fingerprint(event.to_row())
    if is_refusal(event_fp):
        return False
    identity_fp = fingerprint(event.fp1_identity())
    if is_refusal(identity_fp) or identity_fp.value != event_identity:
        return False
    rows = journal.read_stream(stream_name, for_world=journal.world)
    if is_refusal(rows) or type(physical.sequence) is not int or physical.sequence < 0:
        return False
    index = physical.sequence
    if index >= len(rows.value):
        return False
    raw = rows.value[index]
    raw_fp = fingerprint(raw)
    return (
        event.correlation_id is None
        and event.display_time is None
        and raw == event.to_row()
        and event.payload == payload
        and event.instant == instant
        and event.writer == writer
        and event.world is journal.world
        and raw.get("fingerprint") == event.fingerprint.value
        and not is_refusal(raw_fp)
        and raw_fp.value == physical.fingerprint
        and physical.world is journal.world
        and physical.room_role is RoomRole.JOURNAL
        and physical.engine == "jsonl"
        and type(physical.format_version) is int
        and physical.format_version == 1
        and physical.outcome in (WriteOutcome.STORED, WriteOutcome.IDEMPOTENT)
        and physical.is_evidence_bearing is True
        and physical.retained_forever is True
    )


def _corrupt(reason: str):
    return policy("virtual_ledger_journal", reason)
