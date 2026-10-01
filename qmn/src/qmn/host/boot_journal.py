"""Durable CT-13 adapter for the boot ceremony's stage sink.

The boot ceremony retains its one logical attempt and sequence. This adapter stores
that attempt's successive stages as a checked control-action chain on a dedicated
boot-lifecycle stream; the QMF event sequence remains the physical journal sequence.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

from qmf.core import (
    Fingerprint,
    Ok,
    Result,
    World,
    WriteOutcome,
    WriterId,
    canonical_bytes,
    fingerprint,
    is_refusal,
)
from qmf.core.chrono import DisplayTime, Instant
from qmf.data import JournalAppendReceipt, JournalEvent, JournalEventType, JournalWriter
from qmf.data.journal_producer import JournalReader
from qmf.data.store import JournalStore, StoreReceipt
from qmf.data.store.rooms import RoomRole

from qmn.host._refuse import invalid, policy, unavailable
from qmn.host.boot_ceremony import (
    BOOT_STAGES,
    BootAttemptRecord,
    supervisor_writer_is_reserved,
)

__all__ = ["BOOT_ATTEMPT_RECORD_VERSION", "QmfBootAttemptJournalSink"]

BOOT_ATTEMPT_RECORD_VERSION = 1
_BOOT_ATTEMPT_SUBTYPE = "qmn-boot-attempt"
_BOOT_AMEND_SUBTYPE = "qmn-boot-attempt-stage"
_BOOT_STREAM = "boot-lifecycle"


@dataclass(slots=True)
class QmfBootAttemptJournalSink:
    """Persist and recover the single boot attempt owned by one supervisor writer."""

    writer: JournalWriter
    journal_store: JournalStore
    instant: Callable[[], Result[Instant]]
    _latest: BootAttemptRecord | None = None
    _latest_event: JournalEvent | None = None
    _uncertain: bool = False

    @classmethod
    def resume(
        cls,
        journal: object,
        writer: object,
        *,
        instant: object,
    ) -> Result[QmfBootAttemptJournalSink]:
        if not isinstance(journal, JournalStore) or journal.world is not World.LIVE:
            return invalid("journal", "boot lifecycle is persisted through a live QMF JournalStore")
        if not isinstance(writer, WriterId) or not supervisor_writer_is_reserved(writer):
            return invalid("writer", "boot lifecycle uses the reserved supervisor WriterId")
        if writer.stream != _BOOT_STREAM:
            return invalid("writer.stream", "boot lifecycle uses its dedicated stream")
        if not callable(instant):
            return invalid("instant", "each lifecycle stage uses the injected wall clock")
        writer_result = JournalWriter.resume(journal, writer, stream_name=_BOOT_STREAM)
        if is_refusal(writer_result):
            return writer_result
        reader = JournalReader(journal)
        events = reader.read_checked(_BOOT_STREAM, for_world=World.LIVE)
        if is_refusal(events):
            return events
        state = _recover_attempt(events.value, writer)
        if is_refusal(state):
            return state
        return Ok(
            cls(
                writer=writer_result.value,
                journal_store=journal,
                instant=cast("Callable[[], Result[Instant]]", instant),
                _latest=state.value[0],
                _latest_event=state.value[1],
                _uncertain=False,
            )
        )

    def append(self, record: BootAttemptRecord, /) -> Result[BootAttemptRecord]:
        """Durably write the initial doors-bound attempt before later boot work."""
        if self._uncertain:
            return unavailable("boot_journal", "reopen checked CT-13 after uncertain append ACK")
        if self._latest is not None:
            return policy("boot_attempt", "one supervisor epoch records its attempt once")
        if (
            record.writer != self.writer.writer
            or record.boot_epoch_id != self.writer.writer.boot_epoch_id
            or record.sequence != 0
            or record.stage != "doors_bound"
        ):
            return invalid("boot_attempt", "initial boot record matches reserved writer and stage")
        return self._persist(record, initial=True)

    def amend(self, record: BootAttemptRecord, /) -> Result[BootAttemptRecord]:
        """Append a same-attempt stage amendment with a pointer to its prior CT-13 row."""
        if self._uncertain:
            return unavailable("boot_journal", "reopen checked CT-13 after uncertain append ACK")
        previous = self._latest
        if previous is None or self._latest_event is None:
            return invalid("boot_attempt", "stage amend follows a durable initial attempt")
        if (
            record.writer != previous.writer
            or record.boot_epoch_id != previous.boot_epoch_id
            or record.sequence != previous.sequence
        ):
            return policy(
                "boot_attempt", "stage amend retains the original writer, epoch and sequence"
            )
        old_stage = _stage_index(previous.stage)
        new_stage = _stage_index(record.stage)
        if old_stage is None or new_stage is None or new_stage < old_stage:
            return policy("stage", "boot stages advance monotonically through the declared order")
        return self._persist(record, initial=False)

    def verify_sealed(self, composition_fp: Fingerprint) -> Result[BootAttemptRecord]:
        """Reopen checked CT-13 evidence and prove this epoch sealed this composition."""
        events = JournalReader(self.journal_store).read_checked(_BOOT_STREAM, for_world=World.LIVE)
        if is_refusal(events):
            return events
        recovered = _recover_attempt(events.value, self.writer.writer)
        if is_refusal(recovered):
            return recovered
        record, event = recovered.value
        if record is None or event is None:
            return unavailable("boot_seal", "checked CT-13 contains this supervisor boot attempt")
        if (
            record.stage != "seal"
            or record.composition_fp != composition_fp
            or record.writer != self.writer.writer
            or record.boot_epoch_id != self.writer.writer.boot_epoch_id
        ):
            return policy(
                "boot_seal", "checked CT-13 seals the exact composition under this boot epoch"
            )
        return Ok(record)

    def _persist(self, record: BootAttemptRecord, *, initial: bool) -> Result[BootAttemptRecord]:
        at = self.instant()
        if is_refusal(at):
            return at
        payload: dict[str, object] = {
            "attempt_record_version": BOOT_ATTEMPT_RECORD_VERSION,
            "attempt": dict(record.as_status()),
        }
        if not initial:
            if self._latest_event is None:
                return invalid(
                    "previous_event", "stage amend follows checked prior journal evidence"
                )
            payload["previous_event_fp1"] = self._latest_event.fingerprint.value
        written = self.writer.record_control_action(
            _BOOT_ATTEMPT_SUBTYPE if initial else _BOOT_AMEND_SUBTYPE,
            instant=at.value,
            payload=payload,
        )
        if is_refusal(written):
            self._uncertain = True
            return written
        written_value: object = cast(object, written.value)
        if type(written_value) is not JournalAppendReceipt:
            self._uncertain = True
            return invalid("journal_receipt", "append acknowledgement is a typed QMF receipt")
        receipt = written_value
        event_value: object = cast(object, receipt.event)
        store_value: object = cast(object, receipt.store_receipt)
        edges_value: object = cast(object, receipt.edge_receipts)
        if type(event_value) is not JournalEvent or type(store_value) is not StoreReceipt:
            self._uncertain = True
            return policy(
                "journal_receipt", "typed receipt contains event and physical store receipt"
            )
        event = event_value
        event_writer: object = cast(object, event.writer)
        event_instant: object = cast(object, event.instant)
        event_world: object = cast(object, event.world)
        event_identity: object = cast(object, event.fingerprint)
        event_type: object = cast(object, event.event_type)
        event_payload: object = cast(object, event.payload)
        store_world: object = cast(object, store_value.world)
        store_role: object = cast(object, store_value.room_role)
        store_outcome: object = cast(object, store_value.outcome)
        expected_payload = dict(payload)
        expected_payload["control_action_subtype"] = (
            _BOOT_ATTEMPT_SUBTYPE if initial else _BOOT_AMEND_SUBTYPE
        )
        store_receipt = store_value
        if (
            type(event_type) is not JournalEventType
            or event_type is not JournalEventType.CONTROL_ACTION
            or type(event_writer) is not WriterId
            or type(event.sequence) is not int
            or type(event_instant) is not Instant
            or type(event_world) is not World
            or event_world is not World.LIVE
            or type(event_identity) is not Fingerprint
            or not isinstance(event_payload, Mapping)
            or (event.correlation_id is not None and type(event.correlation_id) is not str)
            or (event.display_time is not None and type(event.display_time) is not DisplayTime)
            or not _same_mapping_bytes(
                cast("Mapping[str, object]", event_payload), expected_payload
            )
            or event_writer != self.writer.writer
            or event.sequence != self.writer.next_sequence - 1
            or event_instant != at.value
            or event.outcome is not None
            or type(edges_value) is not tuple
            or edges_value != ()
            or type(store_world) is not World
            or store_world is not World.LIVE
            or type(store_role) is not RoomRole
            or store_role is not RoomRole.JOURNAL
            or type(store_receipt.engine) is not str
            or store_receipt.engine != "jsonl"
            or store_receipt.is_evidence_bearing is not True
            or store_receipt.retained_forever is not True
            or type(store_receipt.format_version) is not int
            or store_receipt.format_version != 1
            or store_receipt.engine_major is not None
            or store_receipt.rebuild_calendar_identity is not None
            or store_receipt.rebuild_tzdata_version is not None
            or type(store_receipt.sequence) is not int
            or store_receipt.sequence < 0
            or type(store_outcome) is not WriteOutcome
            or type(store_receipt.fingerprint) is not Fingerprint
            or store_outcome not in {WriteOutcome.STORED, WriteOutcome.IDEMPOTENT}
        ):
            self._uncertain = True
            return policy(
                "journal_receipt", "receipt binds exact live event and physical JSONL append"
            )
        recomputed = fingerprint(event.fp1_identity())
        if is_refusal(recomputed) or recomputed.value != event_identity:
            self._uncertain = True
            return policy("journal_receipt", "receipt event carries its recomputed fp1 identity")
        checked = JournalReader(self.journal_store).read_checked(_BOOT_STREAM, for_world=World.LIVE)
        if is_refusal(checked):
            self._uncertain = True
            return checked
        matches = tuple(item for item in checked.value if item.fingerprint == event.fingerprint)
        if len(matches) != 1 or not _same_event_bytes(matches[0], event):
            self._uncertain = True
            return unavailable(
                "journal_readback", "boot stage is independently visible in checked CT-13"
            )
        row_identity = fingerprint(event.to_row())
        raw_rows = self.journal_store.read_stream(_BOOT_STREAM, for_world=World.LIVE)
        if is_refusal(row_identity) or is_refusal(raw_rows):
            self._uncertain = True
            return unavailable("journal_readback", "physical CT-13 row is readable after append")
        physical_index = store_receipt.sequence
        if (
            row_identity.value != store_receipt.fingerprint
            or physical_index >= len(raw_rows.value)
            or not _same_mapping_bytes(raw_rows.value[physical_index], event.to_row())
        ):
            self._uncertain = True
            return policy(
                "journal_receipt", "physical receipt index and fingerprint identify exact row bytes"
            )
        self._latest = record
        self._latest_event = event
        return Ok(record)


def _recover_attempt(
    events: list[JournalEvent], writer: WriterId
) -> Result[tuple[BootAttemptRecord | None, JournalEvent | None]]:
    own = tuple(event for event in events if event.writer == writer)
    latest: BootAttemptRecord | None = None
    latest_event: JournalEvent | None = None
    for event in own:
        if event.event_type.value != "control action":
            return policy(
                "boot_journal", "dedicated lifecycle stream carries control-action events"
            )
        payload = event.payload
        subtype = payload.get("control_action_subtype")
        version = payload.get("attempt_record_version")
        raw_attempt = payload.get("attempt")
        if version != BOOT_ATTEMPT_RECORD_VERSION or not isinstance(raw_attempt, Mapping):
            return invalid("boot_journal", "persisted stage row has its versioned attempt envelope")
        record = _decode_attempt(cast("Mapping[str, object]", raw_attempt))
        if is_refusal(record):
            return record
        if record.value.writer != writer or record.value.boot_epoch_id != writer.boot_epoch_id:
            return policy("boot_attempt", "recovered record matches exact supervisor writer epoch")
        if latest is None:
            if subtype != _BOOT_ATTEMPT_SUBTYPE or record.value.stage != "doors_bound":
                return policy("boot_attempt", "recovery starts with one initial doors-bound row")
        else:
            prior = payload.get("previous_event_fp1")
            if latest_event is None:
                return invalid("previous_event_fp1", "amendment has a checked predecessor")
            if subtype != _BOOT_AMEND_SUBTYPE or prior != latest_event.fingerprint.value:
                return policy("previous_event_fp1", "each amendment links to its exact predecessor")
            old_stage = _stage_index(latest.stage)
            new_stage = _stage_index(record.value.stage)
            if old_stage is None or new_stage is None or new_stage < old_stage:
                return policy("stage", "recovered boot stages advance monotonically")
        latest = record.value
        latest_event = event
    return Ok((latest, latest_event))


def _decode_attempt(value: Mapping[str, object]) -> Result[BootAttemptRecord]:
    required = {"boot_epoch_id", "unit_role", "stage", "sequence", "writer"}
    optional = {"reason", "composition_fp", "failure_id"}
    if required - set(value) or set(value) - required - optional:
        return invalid("attempt", "attempt record has its exact status fields")
    raw_writer = value.get("writer")
    if not isinstance(raw_writer, Mapping):
        return invalid("writer", "attempt carries a typed WriterId mapping")
    writer_body = cast("Mapping[str, object]", raw_writer)
    writer = WriterId.try_create(
        writer_body.get("machine"),
        writer_body.get("role"),
        writer_body.get("stream"),
        writer_body.get("boot_epoch_id"),
    )
    if is_refusal(writer):
        return writer
    epoch = value.get("boot_epoch_id")
    role = value.get("unit_role")
    stage = value.get("stage")
    sequence = value.get("sequence")
    if (
        not isinstance(epoch, str)
        or not isinstance(role, str)
        or not isinstance(stage, str)
        or type(sequence) is not int
    ):
        return invalid("attempt", "attempt identity contains exact scalar types")
    reason = value.get("reason")
    failure_id = value.get("failure_id")
    if reason is not None and not isinstance(reason, str):
        return invalid("reason", "reason is absent or a string")
    if failure_id is not None and not isinstance(failure_id, str):
        return invalid("failure_id", "failure id is absent or a string")
    composition_fp: Fingerprint | None = None
    if "composition_fp" in value:
        parsed = Fingerprint.try_create(value.get("composition_fp"))
        if is_refusal(parsed):
            return parsed
        composition_fp = parsed.value
    if _stage_index(stage) is None:
        return invalid("stage", "stage uses the declared boot ceremony vocabulary")
    return Ok(
        BootAttemptRecord(
            boot_epoch_id=epoch,
            unit_role=role,
            stage=stage,
            writer=writer.value,
            sequence=sequence,
            reason=reason,
            composition_fp=composition_fp,
            failure_id=failure_id,
        )
    )


def _stage_index(value: str) -> int | None:
    try:
        return BOOT_STAGES.index(value)
    except ValueError:
        return None


def _same_event_bytes(left: JournalEvent, right: JournalEvent) -> bool:
    """Compare the complete checked row, including fields excluded from fp1."""
    left_row = canonical_bytes(left.to_row())
    right_row = canonical_bytes(right.to_row())
    return (
        not is_refusal(left_row)
        and not is_refusal(right_row)
        and left_row.value == right_row.value
    )


def _same_mapping_bytes(left: object, right: Mapping[str, object]) -> bool:
    left_row = canonical_bytes(left)
    right_row = canonical_bytes(dict(right))
    return (
        not is_refusal(left_row)
        and not is_refusal(right_row)
        and left_row.value == right_row.value
    )
