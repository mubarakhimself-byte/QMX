"""CT-13 adapter for hosted entry-reservation recovery and persistence."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

from qmf.core import Fingerprint, Instant, Ok, Result, SinkAck, WriterId, is_refusal
from qmf.data import JournalEventType, JournalReader, JournalWriter
from qmf.data.store import JournalStore

from qmn.ledger._refuse import invalid, policy
from qmn.ledger.binding_ledger import EntryReservationEvent, EntryReservationRecovery

__all__ = ["QmfEntryReservationJournal"]

_EVENT_CLASS = "qmn-entry-reservation-event"
_STREAM_EVENT_CLASS = "qmn-entry-reservation-journal"


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
        events = JournalReader(self.journal).read_checked(
            self.writer.stream_name, for_world=self.journal.world
        )
        if is_refusal(events):
            return events
        recovered: list[EntryReservationEvent] = []
        for event in events.value:
            payload = event.payload
            if event.event_type is not JournalEventType.DATA_QUALITY:
                continue
            if payload.get("class") != _STREAM_EVENT_CLASS:
                continue
            raw = payload.get("reservation")
            if not isinstance(raw, Mapping):
                return _corrupt_projection()
            parsed = EntryReservationEvent.from_mapping(cast("Mapping[str, object]", raw))
            if is_refusal(parsed):
                return parsed
            if parsed.value.binding_epoch == binding_epoch:
                recovered.append(parsed.value)
        return Ok(
            EntryReservationRecovery(
                binding_epoch=binding_epoch,
                events=tuple(recovered),
                committed_high_water=len(recovered),
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
