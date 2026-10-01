"""Durable CT-13 adapter for the boot ceremony's stage sink.

The boot ceremony retains its one logical attempt and sequence. This adapter stores
that attempt's successive stages as a checked control-action chain on a dedicated
boot-lifecycle stream; the QMF event sequence remains the physical journal sequence.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

from qmf.core import Fingerprint, Ok, Result, World, WriterId, is_refusal
from qmf.core.chrono import Instant
from qmf.data import JournalEvent, JournalWriter
from qmf.data.journal_producer import JournalReader
from qmf.data.store import JournalStore

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
            )
        )

    def append(self, record: BootAttemptRecord, /) -> Result[BootAttemptRecord]:
        """Durably write the initial doors-bound attempt before later boot work."""
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
            return written
        event = written.value.event
        if event.world is not World.LIVE:
            return invalid("journal_receipt", "append receipt retains the exact live CT-13 event")
        if event.writer != self.writer.writer or event.sequence != self.writer.next_sequence - 1:
            return policy(
                "journal_receipt", "append receipt matches writer and logical journal sequence"
            )
        checked = JournalReader(self.journal_store).read_checked(_BOOT_STREAM, for_world=World.LIVE)
        if is_refusal(checked):
            return checked
        matches = tuple(item for item in checked.value if item.fingerprint == event.fingerprint)
        if len(matches) != 1 or matches[0] != event:
            return unavailable(
                "journal_readback", "boot stage is independently visible in checked CT-13"
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
