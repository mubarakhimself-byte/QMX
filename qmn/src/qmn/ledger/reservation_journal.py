"""CT-13 adapter for hosted entry-reservation recovery and persistence."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import cast

from qmf.core import Fingerprint, Instant, Ok, Result, SinkAck, WriterId, fingerprint, is_refusal
from qmf.data import (
    JournalAppendReceipt,
    JournalEvent,
    JournalEventType,
    JournalReader,
    JournalWriter,
)
from qmf.data.store import JournalStore
from qmf.data.store.rooms import RoomRole

from qmn.ledger._refuse import invalid, policy
from qmn.ledger.binding_ledger import EntryReservationEvent, EntryReservationRecovery

__all__ = ["QmfEntryReservationJournal"]

_EVENT_CLASS = "qmn-entry-reservation-event"
_STREAM_EVENT_CLASS = "qmn-entry-reservation-journal"
_RECOVERY_BARRIER_CLASS = "qmn-entry-reservation-recovery"


@dataclass(frozen=True, slots=True)
class QmfEntryReservationJournal:
    """Persist reservation transitions in the QMF checked journal stream.

    The writer is resumed by the composition root for the current boot epoch.
    Recovery reads and validates the entire CT-13 stream before projecting this
    adapter's namespaced data-quality events. A read refusal never becomes an
    empty projection.
    """

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
    ) -> Result[QmfEntryReservationJournal]:
        resumed = JournalWriter.resume(journal, writer_id, stream_name=stream_name)
        if is_refusal(resumed):
            return resumed
        return Ok(cls(journal=journal, writer=resumed.value, instant=instant))

    def append(self, event: object, /) -> Result[SinkAck]:
        if (
            not isinstance(event, Mapping)
            or cast("Mapping[str, object]", event).get("class") != _EVENT_CLASS
        ):
            return _invalid_event()
        typed = EntryReservationEvent.from_mapping(cast("Mapping[str, object]", event))
        if is_refusal(typed):
            return typed
        persisted = self.writer.record(
            JournalEventType.DATA_QUALITY,
            {
                "class": _STREAM_EVENT_CLASS,
                "reservation": dict(typed.value.as_mapping()),
            },
            instant=self.instant(),
        )
        if is_refusal(persisted):
            return persisted
        expected_payload = {
            "class": _STREAM_EVENT_CLASS,
            "reservation": dict(typed.value.as_mapping()),
        }
        if not _receipt_matches(
            persisted.value,
            journal=self.journal,
            writer=self.writer.writer,
            event_type=JournalEventType.DATA_QUALITY,
            payload=expected_payload,
        ):
            return _corrupt_projection()
        if type(persisted.value) is not JournalAppendReceipt:
            return _corrupt_projection()
        event_row = persisted.value.event
        checked = JournalReader(self.journal).read_checked(
            self.writer.stream_name, for_world=self.journal.world
        )
        if is_refusal(checked):
            return checked
        if not any(row.fingerprint == event_row.fingerprint for row in checked.value):
            return _corrupt_projection()
        return Ok(
            SinkAck(
                {
                    "complete": True,
                    "fingerprint": persisted.value.event.fingerprint.value,
                }
            )
        )

    def recover(self, binding_epoch: object) -> Result[EntryReservationRecovery]:
        if not isinstance(binding_epoch, Fingerprint):
            return _invalid_epoch()
        if self.writer.is_blocked:
            retried = self.writer.retry_blocked()
            if is_refusal(retried):
                return retried
        events = JournalReader(self.journal).read_checked(
            self.writer.stream_name, for_world=self.journal.world
        )
        if is_refusal(events):
            return events
        initial = _project_reservations(events.value, self.writer.writer, binding_epoch)
        if is_refusal(initial):
            return initial
        barrier = self.writer.record(
            JournalEventType.DATA_QUALITY,
            {
                "class": _RECOVERY_BARRIER_CLASS,
                "stream_class": _STREAM_EVENT_CLASS,
                "binding_epoch": binding_epoch.value,
                "reconciled_reservation_count": sum(
                    1
                    for event in events.value
                    if event.event_type is JournalEventType.DATA_QUALITY
                    and event.payload.get("class") == _STREAM_EVENT_CLASS
                ),
            },
            instant=self.instant(),
        )
        if is_refusal(barrier):
            return barrier
        barrier_payload = {
            "class": _RECOVERY_BARRIER_CLASS,
            "stream_class": _STREAM_EVENT_CLASS,
            "binding_epoch": binding_epoch.value,
            "reconciled_reservation_count": len(initial.value),
        }
        if not _receipt_matches(
            barrier.value,
            journal=self.journal,
            writer=self.writer.writer,
            event_type=JournalEventType.DATA_QUALITY,
            payload=barrier_payload,
        ):
            return _corrupt_projection()
        if type(barrier.value) is not JournalAppendReceipt:
            return _corrupt_projection()
        events = JournalReader(self.journal).read_checked(
            self.writer.stream_name, for_world=self.journal.world
        )
        if is_refusal(events):
            return events
        if not any(row.fingerprint == barrier.value.event.fingerprint for row in events.value):
            return _corrupt_projection()
        recovered = _project_reservations(events.value, self.writer.writer, binding_epoch)
        if is_refusal(recovered):
            return recovered
        return Ok(
            EntryReservationRecovery(
                binding_epoch=binding_epoch,
                events=tuple(recovered.value),
                committed_high_water=len(recovered.value),
                complete=True,
            )
        )


def _invalid_event():
    return invalid("reservation_event", "the QMF adapter appends typed QMN reservation events")


def _corrupt_projection():
    return policy(
        "reservation_journal",
        "a namespaced reservation event must contain a valid typed reservation payload",
    )


def _invalid_epoch():
    return invalid("binding_epoch", "QMF reservation recovery requires a CT-28 fingerprint")


def _project_reservations(
    events: Iterable[JournalEvent], trusted_writer: WriterId, binding_epoch: Fingerprint
) -> Result[list[EntryReservationEvent]]:
    """Validate trusted reservation stream provenance before projecting its prefix."""
    recovered: list[EntryReservationEvent] = []
    for event in events:
        if event.event_type is not JournalEventType.DATA_QUALITY:
            continue
        payload = event.payload
        event_class = payload.get("class")
        if event_class not in {_STREAM_EVENT_CLASS, _RECOVERY_BARRIER_CLASS}:
            continue
        if (
            event.writer.machine != trusted_writer.machine
            or event.writer.role != trusted_writer.role
            or event.writer.stream != trusted_writer.stream
        ):
            return policy(
                "reservation_writer",
                "persisted reservation transitions come from the configured host risk writer",
            )
        if event_class == _RECOVERY_BARRIER_CLASS:
            if payload.get("stream_class") != _STREAM_EVENT_CLASS:
                return _corrupt_projection()
            continue
        raw = payload.get("reservation")
        if not isinstance(raw, Mapping):
            return _corrupt_projection()
        parsed = EntryReservationEvent.from_mapping(cast("Mapping[str, object]", raw))
        if is_refusal(parsed):
            return parsed
        if parsed.value.binding_epoch == binding_epoch:
            recovered.append(parsed.value)
    return Ok(recovered)


def _receipt_matches(
    value: object,
    *,
    journal: JournalStore,
    writer: WriterId,
    event_type: JournalEventType,
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(value, JournalAppendReceipt):
        return False
    event = value.event
    physical = value.store_receipt
    row_fingerprint = fingerprint(event.to_row())
    if is_refusal(row_fingerprint):
        return False
    return (
        event.event_type is event_type
        and event.payload == payload
        and event.writer == writer
        and event.world is journal.world
        and physical.fingerprint == row_fingerprint.value
        and physical.world is journal.world
        and physical.room_role is RoomRole.JOURNAL
        and physical.is_evidence_bearing
        and physical.retained_forever
    )
