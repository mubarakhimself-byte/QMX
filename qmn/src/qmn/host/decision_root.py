"""Configured Book decision root joining MIS, CT-28, reservations and OrderPath."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import cast

from qmf.core import (
    Account,
    Fingerprint,
    Instant,
    JournalSink,
    MonotonicReading,
    Ok,
    Result,
    SinkAck,
    VenueId,
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
from qmf.risk.binding import BookBindingRecord
from qmf.risk.door import EntryIntent

from qmn.host._refuse import invalid, policy
from qmn.ledger import BindingVirtualLedger, QmfEntryReservationJournal
from qmn.mis.signal_snapshot import (
    GovernedConsumer,
    ProducerReadiness,
    SignalSnapshot,
    consume_signal_snapshot,
)
from qmn.order.identity import NativeExecutionMap
from qmn.order.path import OrderPath, OrderPathSubmission, OrderPathTerminalResolution
from qmn.protection.ksa import (
    KsaEnforcementScope,
    KsaLevel,
    effective_ksa_level,
)
from qmn.protection.ksa_journal import KsaJournalProjection
from qmn.seats.admission import AdmittedNodeSeat
from qmn.seats.dispatch import BookPathContext, SeatDispatchReceipt, dispatch_hosted_intents
from qmn.seats.host import drive_governed_seat

__all__ = [
    "DECISION_TRANSCRIPT_CLASS",
    "HostedDecisionRoot",
    "HostedDecisionTranscript",
    "OrderPathTiming",
    "QmfHostedDecisionJournal",
]

DECISION_TRANSCRIPT_CLASS = "qmn-hosted-decision-transcript"


@dataclass(frozen=True, slots=True)
class OrderPathTiming:
    """Injected wall and monotonic stamps for one actual OrderPath submission."""

    enqueued_at: MonotonicReading
    now_mono: MonotonicReading
    handed_off_at: Instant

    def valid(self) -> bool:
        return self.enqueued_at.boot_epoch_id == self.now_mono.boot_epoch_id


@dataclass(frozen=True, slots=True)
class HostedDecisionTranscript:
    """Evidence emitted only after both governed consumers and OrderPath ran."""

    snapshot_fingerprint: Fingerprint
    snapshot_frontier: Instant
    decision_at: Instant
    binding_epoch: Fingerprint
    seat_candidate: Fingerprint
    global_ksa_level: KsaLevel
    stream_ksa_level: KsaLevel
    effective_ksa_level: KsaLevel
    ksa_epoch_fingerprints: tuple[Fingerprint, ...]
    ksa_event_fingerprints: tuple[Fingerprint, ...]
    dispatch: SeatDispatchReceipt
    command_fingerprints: tuple[Fingerprint, ...]
    submissions: tuple[OrderPathSubmission | OrderPathTerminalResolution, ...]
    executed_stages: tuple[str, ...]

    def as_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "binding_epoch": self.binding_epoch.value,
                "class": DECISION_TRANSCRIPT_CLASS,
                "decision_at_ns": self.decision_at.value_ns,
                "executed_stages": list(self.executed_stages),
                "effective_ksa_level": self.effective_ksa_level.value,
                "ksa_epoch_fingerprints": [fp.value for fp in self.ksa_epoch_fingerprints],
                "ksa_event_fingerprints": [fp.value for fp in self.ksa_event_fingerprints],
                "global_ksa_level": self.global_ksa_level.value,
                "order_results": [
                    {
                        "command_fp1": command_fp.value,
                        "kind": (
                            "terminal-without-handoff"
                            if isinstance(item, OrderPathTerminalResolution)
                            else "submitted"
                        ),
                        "outcome": (
                            None
                            if isinstance(item, OrderPathTerminalResolution)
                            else item.result.outcome.value
                        ),
                    }
                    for command_fp, item in zip(
                        self.command_fingerprints, self.submissions, strict=False
                    )
                ],
                "commands": [fp.value for fp in self.command_fingerprints],
                "seat_candidate_fp1": self.seat_candidate.value,
                "snapshot_fingerprint": self.snapshot_fingerprint.value,
                "snapshot_frontier_ns": self.snapshot_frontier.value_ns,
                "stream_ksa_level": self.stream_ksa_level.value,
            }
        )


@dataclass(frozen=True, slots=True)
class QmfHostedDecisionJournal:
    """Map node decision transcript mappings onto the QMF CT-13 writer."""

    writer: JournalWriter
    journal_store: JournalStore
    instant: Callable[[], Instant]

    @classmethod
    def resume(
        cls,
        journal: object,
        writer_id: object,
        *,
        stream_name: str,
        instant: Callable[[], Instant],
    ) -> Result[QmfHostedDecisionJournal]:
        if not isinstance(journal, JournalStore) or not isinstance(writer_id, WriterId):
            return invalid("decision_journal", "QMF journal and WriterId are typed")
        writer = JournalWriter.resume(journal, writer_id, stream_name=stream_name)
        if is_refusal(writer):
            return writer
        return Ok(cls(writer=writer.value, journal_store=journal, instant=instant))

    def append(self, event: object, /) -> Result[SinkAck]:
        if not isinstance(event, Mapping):
            return invalid("decision_transcript", "the QMF decision journal takes a mapping")
        body = cast("Mapping[str, object]", event)
        if body.get("class") == DECISION_TRANSCRIPT_CLASS:
            event_type = JournalEventType.DATA_QUALITY
        elif body.get("kind") == "command" and body.get("phase") == "before-dispatch":
            event_type = JournalEventType.ORDER
        else:
            return invalid(
                "decision_transcript",
                "the QMF root journal accepts decision transcripts and pre-dispatch order events",
            )
        appended_at = cast(object, self.instant())
        if not isinstance(appended_at, Instant):
            return invalid("decision_journal", "the journal stamp is an exact Instant")
        appended = self.writer.record(
            event_type,
            dict(body),
            instant=appended_at,
        )
        if is_refusal(appended):
            return appended
        if type(appended.value) is not JournalAppendReceipt:
            return policy("decision_journal", "QMF confirms a typed durable journal append")
        event_value: object = cast(object, appended.value.event)
        physical_value: object = cast(object, appended.value.store_receipt)
        if not isinstance(event_value, JournalEvent) or not isinstance(
            physical_value, StoreReceipt
        ):
            return policy("decision_journal", "QMF receipt contains typed event and store records")
        event = event_value
        physical = physical_value
        row_fingerprint = fingerprint(event.to_row())
        if is_refusal(row_fingerprint):
            return row_fingerprint
        stored_payload_fp = fingerprint(event.payload)
        expected_payload_fp = fingerprint(body)
        if is_refusal(stored_payload_fp):
            return stored_payload_fp
        if is_refusal(expected_payload_fp):
            return expected_payload_fp
        if (
            event.event_type is not event_type
            or event.instant != appended_at
            or event.sequence != self.writer.next_sequence - 1
            or stored_payload_fp.value != expected_payload_fp.value
            or event.writer != self.writer.writer
            or event.world is not self.journal_store.world
            or physical.fingerprint != row_fingerprint.value
            or physical.sequence != event.sequence
            or physical.world is not self.journal_store.world
            or physical.room_role is not RoomRole.JOURNAL
            or physical.engine != "jsonl"
            or physical.format_version != 1
            or physical.outcome not in (WriteOutcome.STORED, WriteOutcome.IDEMPOTENT)
            or not physical.is_evidence_bearing
            or not physical.retained_forever
        ):
            return policy(
                "decision_journal", "the append receipt identifies the exact CT-13 journal event"
            )
        checked = JournalReader(self.journal_store).read_checked(
            self.writer.stream_name, for_world=self.journal_store.world
        )
        if is_refusal(checked):
            return checked
        if not any(row.fingerprint == event.fingerprint for row in checked.value):
            return policy("decision_journal", "the complete decision event reads back from CT-13")
        return Ok(
            SinkAck(
                {
                    "complete": True,
                    "fingerprint": event.fingerprint.value,
                }
            )
        )


@dataclass(frozen=True, slots=True)
class HostedDecisionRoot:
    """Open only after exact CT-28 reservation recovery and ordinal recovery."""

    seat: AdmittedNodeSeat
    path: BookPathContext
    order_path: OrderPath
    reservation_journal: QmfEntryReservationJournal
    ksa_projection: KsaJournalProjection
    decision_journal: JournalSink[object]
    timing_for: Callable[[object], Result[OrderPathTiming]]

    @classmethod
    def try_open(
        cls,
        *,
        seat: object,
        path: object,
        order_path: object,
        reservation_journal: object,
        ksa_projection: object,
        decision_journal: object,
        timing_for: object,
    ) -> Result[HostedDecisionRoot]:
        if not isinstance(seat, AdmittedNodeSeat):
            return invalid("seat", "the Book decision root requires an admitted node seat")
        if not isinstance(path, BookPathContext):
            return invalid("path", "the Book decision root requires a configured BookPathContext")
        if not isinstance(order_path, OrderPath) or not order_path.sequencer_open:
            return policy(
                "order_path",
                "OrderPath is configured and its command ordinal high-water is recovered",
            )
        if not isinstance(reservation_journal, QmfEntryReservationJournal):
            return invalid(
                "reservation_journal",
                "the configured root requires the checked QMF CT-13 reservation adapter",
            )
        if not isinstance(decision_journal, QmfHostedDecisionJournal):
            return invalid(
                "decision_journal",
                "the configured root persists decision transcripts through a JournalSink",
            )
        if not isinstance(ksa_projection, KsaJournalProjection):
            return invalid("ksa_projection", "the root reads KSA folds from checked CT-13")
        if ksa_projection.journal is not decision_journal.journal_store:
            return policy("ksa_projection", "KSA and hosted decisions use the same CT-13 store")
        if reservation_journal.journal is not decision_journal.journal_store:
            return policy(
                "reservation_journal", "reservations and decisions use the same CT-13 store"
            )
        if not callable(timing_for):
            return invalid("timing_for", "OrderPath timing is injected per command")
        if not isinstance(path.binding_record, BookBindingRecord):
            return invalid("binding_record", "BookPathContext carries an exact CT-28 record")
        if not isinstance(path.position_ledger, BindingVirtualLedger):
            return invalid("position_ledger", "BookPathContext carries a binding virtual ledger")
        if not isinstance(path.native_execution_map, NativeExecutionMap):
            return invalid(
                "native_execution_map", "BookPathContext carries its immutable native map"
            )
        if not path.position_ledger.uses_reservation_journal(reservation_journal):
            return policy(
                "reservation_journal",
                "the ledger uses this exact QMF reservation adapter",
            )
        if order_path.position_ledger is not path.position_ledger:
            return policy("position_ledger", "OrderPath and BookPathContext share one ledger")
        if order_path.command_journal is not decision_journal:
            return policy(
                "decision_journal",
                "the same QMF CT-13 writer journals the transcript and order dispatch intent",
            )
        if not isinstance(path.account, Account) or not isinstance(path.venue_id, VenueId):
            return invalid("execution_target", "BookPathContext carries typed account and venue")
        stream_scope = KsaEnforcementScope.stream(path.venue_id, path.account.account_id)
        if is_refusal(stream_scope):
            return stream_scope
        if (
            ksa_projection.global_epoch.scope.kind != "global"
            or not ksa_projection.stream_epoch.scope.matches(stream_scope.value)
        ):
            return policy("ksa_scope", "pinned KSA epochs cover global and exact Book scope")
        epoch = path.binding_record.fingerprint()
        if is_refusal(epoch):
            return epoch
        rebuilt_native_map = NativeExecutionMap.try_create(
            path.native_execution_map.mappings,
            registry_as_of_fingerprint=path.native_execution_map.registry_as_of_fingerprint,
            binding_epoch=epoch.value,
        )
        if is_refusal(rebuilt_native_map):
            return rebuilt_native_map
        if rebuilt_native_map.value.fingerprint != path.native_execution_map.fingerprint:
            return policy(
                "native_execution_map",
                "native mappings reproduce the pinned immutable map fingerprint",
            )
        if (
            seat.binding_ref != epoch.value.value
            or path.position_ledger.binding_epoch != epoch.value
            or path.native_execution_map.binding_epoch != epoch.value
            or seat.proof.bms_instance_id != path.binding_record.bms_instance_id.value
            or path.bms_instance_id != seat.proof.bms_instance_id
            or path.binding_record.venue_id != path.venue_id
            or path.binding_record.account_id != path.account.account_id
        ):
            return policy(
                "binding_epoch",
                "seat, Book, native map, and position ledger share the CT-28 fingerprint",
            )
        recovered = reservation_journal.recover(epoch.value)
        if is_refusal(recovered):
            return recovered
        restored = path.position_ledger.recover_entry_reservations(recovered.value)
        if is_refusal(restored):
            return restored
        return Ok(
            cls(
                seat=seat,
                path=path,
                order_path=order_path,
                reservation_journal=reservation_journal,
                ksa_projection=ksa_projection,
                decision_journal=cast("JournalSink[object]", decision_journal),
                timing_for=cast("Callable[[object], Result[OrderPathTiming]]", timing_for),
            )
        )

    def run_slice(
        self,
        *,
        snapshot: object,
        decision_at: object,
        stream: object,
        cancel: object,
        probe: object,
        transition_instant: object = None,
    ) -> Result[HostedDecisionTranscript]:
        if not isinstance(snapshot, SignalSnapshot):
            return invalid("snapshot", "the Book and KSA consume a typed MIS SignalSnapshot")
        if not isinstance(decision_at, Instant):
            return invalid("decision_at", "the configured root receives its recorded Instant")
        account = cast("Account", self.path.account)
        expected_environment = account.role.value
        if snapshot.environment != expected_environment:
            return policy(
                "snapshot_environment",
                "MIS snapshot and SQS baseline environment match the exact Book account role",
                expected=expected_environment,
                given=snapshot.environment,
            )
        book_snapshot = consume_signal_snapshot(
            snapshot,
            consumer=GovernedConsumer.BOOK_DOOR,
            decision_at=decision_at,
        )
        if is_refusal(book_snapshot):
            return book_snapshot
        ksa_snapshot = consume_signal_snapshot(
            snapshot,
            consumer=GovernedConsumer.KSA,
            decision_at=decision_at,
        )
        if is_refusal(ksa_snapshot):
            return ksa_snapshot
        expected_scope = KsaEnforcementScope.stream(
            cast("VenueId", self.path.venue_id), cast("Account", self.path.account).account_id
        )
        if is_refusal(expected_scope):
            return expected_scope
        folded = self.ksa_projection.levels(expected_stream_scope=expected_scope.value)
        if is_refusal(folded):
            return folded
        global_ksa_level = folded.value.global_level
        stream_ksa_level = folded.value.stream_level
        effective_level = effective_ksa_level(
            global_level=global_ksa_level,
            stream_level=stream_ksa_level,
        )
        if is_refusal(effective_level):
            return effective_level
        if effective_level.value is not KsaLevel.GREEN:
            return policy(
                "ksa_level",
                "non-GREEN KSA state blocks new hosted entry admission",
                level=effective_level.value.value,
            )
        snapshot_fingerprint = snapshot.fingerprint()
        if is_refusal(snapshot_fingerprint):
            return snapshot_fingerprint
        if not (book_snapshot.value is snapshot and ksa_snapshot.value is snapshot):
            return policy("signal_snapshot", "Book and KSA consumed the exact same MIS snapshot")
        path = replace(self.path, decision_at=decision_at)
        intents = drive_governed_seat(
            self.seat.seat,
            decision_at,
            stream=stream,
            cancel=cancel,
            probe=probe,
            transition_instant=transition_instant,
        )
        if is_refusal(intents):
            return intents
        if any(not isinstance(intent, EntryIntent) for intent in intents.value):
            return policy(
                "intents",
                "this Book decision composition dispatches only governed EntryIntent values",
            )
        for intent in intents.value:
            if not isinstance(intent, EntryIntent):
                return invalid("intent", "hosted entry callback returned a typed EntryIntent")
            reading = snapshot.sqs_for(intent.instrument)
            if (
                reading is None
                or reading.readiness is not ProducerReadiness.OK
                or reading.hard_block
                or reading.score is None
                or reading.baseline_key.venue != self.path.venue_id
                or reading.baseline_key.environment != expected_environment
                or reading.baseline_key.instrument != intent.instrument
            ):
                return policy(
                    "sqs",
                    "hosted entry requires the same frontier's ready, non-blocked SQS reading",
                    instrument=intent.instrument.symbol,
                )
        first_ordinal: int | None = None
        for _intent in intents.value:
            ordinal = self.order_path.mint_ordinal()
            if is_refusal(ordinal):
                return ordinal
            if first_ordinal is None:
                first_ordinal = ordinal.value
        if first_ordinal is not None:
            path = replace(path, ordering_ordinal=first_ordinal)
        receipt = dispatch_hosted_intents(self.seat, intents.value, path=path)
        if is_refusal(receipt):
            return receipt
        epoch = cast("BookBindingRecord", self.path.binding_record).fingerprint()
        if is_refusal(epoch):
            return epoch
        snapshot_fp = snapshot_fingerprint.value
        candidate_fp = self.seat.proof.candidate.fingerprint
        stages = (
            "mis_snapshot_consumed_by_book",
            "mis_snapshot_consumed_by_ksa",
            "governed_seat_callback_completed",
            "dispatch_hosted_intents_completed",
        )
        command_fingerprints: list[Fingerprint] = []
        for command in receipt.value.commands:
            command_fp = command.fingerprint()
            if is_refusal(command_fp):
                return command_fp
            command_fingerprints.append(command_fp.value)
        provisional = HostedDecisionTranscript(
            snapshot_fingerprint=snapshot_fp,
            snapshot_frontier=snapshot.frontier_instant,
            decision_at=decision_at,
            binding_epoch=epoch.value,
            seat_candidate=candidate_fp,
            global_ksa_level=global_ksa_level,
            stream_ksa_level=stream_ksa_level,
            effective_ksa_level=effective_level.value,
            ksa_epoch_fingerprints=folded.value.epoch_fingerprints,
            ksa_event_fingerprints=folded.value.event_fingerprints,
            dispatch=receipt.value,
            command_fingerprints=tuple(command_fingerprints),
            submissions=(),
            executed_stages=stages,
        )
        persisted = self.decision_journal.append(provisional.as_mapping())
        if is_refusal(persisted):
            return persisted
        if persisted.value.detail.get("complete") is not True:
            return policy(
                "decision_journal",
                "the decision journal explicitly confirms a complete durable transcript",
            )
        submissions: list[OrderPathSubmission | OrderPathTerminalResolution] = []
        for command in receipt.value.commands:
            timing = self.timing_for(command)
            if is_refusal(timing):
                return timing
            if not timing.value.valid():
                return invalid(
                    "order_path_timing", "each command has typed wall and monotonic stamps"
                )
            result = self.order_path.submit_authorized(
                command,
                enqueued_at=timing.value.enqueued_at,
                now_mono=timing.value.now_mono,
                handed_off_at=timing.value.handed_off_at,
            )
            if is_refusal(result):
                return result
            submissions.append(result.value)
        completed = HostedDecisionTranscript(
            snapshot_fingerprint=snapshot_fp,
            snapshot_frontier=snapshot.frontier_instant,
            decision_at=decision_at,
            binding_epoch=epoch.value,
            seat_candidate=candidate_fp,
            global_ksa_level=global_ksa_level,
            stream_ksa_level=stream_ksa_level,
            effective_ksa_level=effective_level.value,
            ksa_epoch_fingerprints=folded.value.epoch_fingerprints,
            ksa_event_fingerprints=folded.value.event_fingerprints,
            dispatch=receipt.value,
            command_fingerprints=provisional.command_fingerprints,
            submissions=tuple(submissions),
            executed_stages=(*stages, "ct19_order_path_resolved"),
        )
        persisted_result = self.decision_journal.append(completed.as_mapping())
        if is_refusal(persisted_result):
            return persisted_result
        if persisted_result.value.detail.get("complete") is not True:
            return policy(
                "decision_journal",
                "the decision journal explicitly confirms a complete result transcript",
            )
        return Ok(completed)
