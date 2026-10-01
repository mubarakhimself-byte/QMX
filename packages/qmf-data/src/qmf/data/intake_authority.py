"""Durable CT-15 key authority backed by the world's CT-13 journal.

The authority writes an exact normalized CT-10 observation as an intent before
raw-room admission, then acknowledges completion after that admission succeeds.
On restart, an intent without completion replays the retained observation
verbatim, so a lost append acknowledgement cannot mint a second observation.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from threading import RLock
from typing import Final, Protocol, cast

from qmf.core import Instant, Ok, Result, WriteOutcome, WriterId, fingerprint, is_refusal
from qmf.data.ingest import IntakeKey
from qmf.data.journal import JournalEvent, JournalEventType
from qmf.data.journal_producer import JournalAppendReceipt, JournalReader, JournalWriter
from qmf.data.observation import SourceObservation
from qmf.data.store import JournalStore
from qmf.data.store.receipts import StoreReceipt
from qmf.data.store.refusals import invalid_input, policy_rejection
from qmf.data.store.rooms import RoomRole

__all__ = ["IntakeAuthority", "IntakeReservation"]

_EVENT_CLASS: Final[str] = "qmf-ct15-intake-key"
_RECOVERY_CLASS: Final[str] = "qmf-ct15-recovery-barrier"
_INTENT: Final[str] = "intent"
_COMPLETE: Final[str] = "complete"
_AUTHORITY_STREAM: Final[str] = "ct15-intake-authority"
_COORDINATORS_LOCK = RLock()
_COORDINATORS: dict[
    tuple[int, int, str],
    tuple[
        JournalStore, WriterId, JournalWriter, dict[IntakeKey, tuple[str, IntakeReservation]], RLock
    ],
] = {}


class _ProcessLock:
    """Advisory transaction lock shared by CT-15 handles across processes."""

    def __init__(self, path: Path) -> None:
        self._fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
        if not stat.S_ISREG(os.fstat(self._fd).st_mode):
            os.close(self._fd)
            raise OSError("CT-15 lock path is not a regular file")
        try:
            fcntl = cast(_Fcntl, import_module("fcntl"))
            fcntl.flock(self._fd, fcntl.LOCK_EX)
        except BaseException:
            os.close(self._fd)
            raise

    def close(self) -> None:
        fcntl = cast(_Fcntl, import_module("fcntl"))
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        os.close(self._fd)

    def __enter__(self) -> _ProcessLock:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class _Fcntl(Protocol):
    LOCK_EX: int
    LOCK_UN: int

    def flock(self, fd: int, operation: int) -> None: ...


def _process_lock(journal: JournalStore) -> _ProcessLock:
    lock_path = journal.coordination_lock_path("ct15-intake-authority")
    if is_refusal(lock_path):
        raise OSError("invalid CT-15 room lock path")
    base = lock_path.value.parent
    base.mkdir(parents=True, exist_ok=True)
    return _ProcessLock(lock_path.value)


@dataclass(frozen=True, slots=True)
class IntakeReservation:
    """The canonical observation retained for a key and whether CT-10 is complete."""

    observation: SourceObservation
    complete: bool


@dataclass(slots=True)
class IntakeAuthority:
    """QMF-owned durable mapping from a CT-15 key to a canonical CT-10 identity."""

    writer: JournalWriter
    _journal: JournalStore
    _keys: dict[IntakeKey, tuple[str, IntakeReservation]] = field(default_factory=lambda: {})
    _lock: RLock = field(default_factory=RLock)

    @classmethod
    def resume(
        cls,
        journal: JournalStore,
        writer_id: WriterId,
        *,
        stream_name: str = "ct15-intake-authority",
    ) -> Result[IntakeAuthority]:
        """Validate, durably barrier, and resume the one canonical CT-15 authority stream."""
        if stream_name != _AUTHORITY_STREAM:
            return policy_rejection(
                "stream_name",
                "CT-15 canonical-key uniqueness uses the fixed authority stream",
                expected=_AUTHORITY_STREAM,
                given=stream_name,
            )
        coordinator_key = (id(journal), os.getpid(), _AUTHORITY_STREAM)
        with _COORDINATORS_LOCK:
            existing = _COORDINATORS.get(coordinator_key)
            if existing is not None:
                shared_journal, _shared_writer_id, _shared_writer, shared_keys, shared_lock = (
                    existing
                )
                if shared_journal is not journal:
                    return policy_rejection(
                        "journal",
                        "a cached CT-15 coordinator belongs to the exact journal object",
                    )
                try:
                    with _process_lock(journal):
                        events = JournalReader(journal).read_checked(
                            _AUTHORITY_STREAM, for_world=journal.world, expected_start=0
                        )
                        if is_refusal(events):
                            return events
                        keys = _rebuild_keys(events.value, journal.world)
                        if is_refusal(keys):
                            return keys
                        resumed = JournalWriter.resume(
                            journal, writer_id, stream_name=_AUTHORITY_STREAM
                        )
                        if is_refusal(resumed):
                            return resumed
                        synced = resumed.value.synchronize_prefix()
                        if is_refusal(synced):
                            return synced
                        barrier = _persist_recovery_barrier(journal, resumed.value, events.value)
                        if is_refusal(barrier):
                            return barrier
                        shared_keys.clear()
                        shared_keys.update(keys.value)
                        shared = (journal, writer_id, resumed.value, shared_keys, shared_lock)
                        _COORDINATORS[coordinator_key] = shared
                        return Ok(cls(resumed.value, journal, shared_keys, shared_lock))
                except OSError as exc:
                    return invalid_input(
                        "ct15_process_lock",
                        "the CT-15 cross-process transaction lock is available",
                        given=str(exc),
                    )
            try:
                with _process_lock(journal):
                    events = JournalReader(journal).read_checked(
                        _AUTHORITY_STREAM, for_world=journal.world, expected_start=0
                    )
                    if is_refusal(events):
                        return events
                    keys = _rebuild_keys(events.value, journal.world)
                    if is_refusal(keys):
                        return keys
                    resumed = JournalWriter.resume(
                        journal, writer_id, stream_name=_AUTHORITY_STREAM
                    )
                    if is_refusal(resumed):
                        return resumed
                    synced = resumed.value.synchronize_prefix()
                    if is_refusal(synced):
                        return synced
                    barrier = _persist_recovery_barrier(journal, resumed.value, events.value)
                    if is_refusal(barrier):
                        return barrier
                    shared = (journal, writer_id, resumed.value, keys.value, RLock())
                    _COORDINATORS[coordinator_key] = shared
                    return Ok(
                        cls(
                            writer=resumed.value,
                            _journal=journal,
                            _keys=keys.value,
                            _lock=shared[4],
                        )
                    )
            except OSError as exc:
                return invalid_input(
                    "ct15_process_lock",
                    "the CT-15 cross-process transaction lock is available",
                    given=str(exc),
                )

    def reserve(
        self,
        key: IntakeKey,
        observation: SourceObservation,
        *,
        instant: Instant,
    ) -> Result[IntakeReservation]:
        try:
            with self._lock, _process_lock(self._journal):
                refreshed = self._refresh_process_state(instant)
                if is_refusal(refreshed):
                    return refreshed
                return self._reserve_under_lock(key, observation, instant=instant)
        except OSError as exc:
            return invalid_input(
                "ct15_process_lock",
                "the CT-15 cross-process transaction lock is available",
                given=str(exc),
            )

    def _reserve_under_lock(
        self,
        key: IntakeKey,
        observation: SourceObservation,
        *,
        instant: Instant,
    ) -> Result[IntakeReservation]:
        """Durably reserve an exact CT-10 row or return the earlier canonical row.

        Provider-fact identity excludes only receipt metadata (writer, sequence,
        receive-wall-time). A later retry with the same provider facts therefore
        reuses the original CT-10 value, while changed source facts under the same
        CT-15 key are refused.
        """
        with self._lock:
            valid = _validate_key_observation(key, observation, self.writer.world)
            if is_refusal(valid):
                return valid
            fact_fp = _fact_fingerprint(observation)
            if is_refusal(fact_fp):
                return fact_fp
            refreshed = self._refresh_and_barrier(instant)
            if is_refusal(refreshed):
                return refreshed
            prior = self._keys.get(key)
            if prior is not None:
                if prior[0] != fact_fp.value:
                    return _changed_fact(key, prior[0], fact_fp.value)
                return Ok(prior[1])

            persisted = self.writer.record_data_quality(
                _intent_payload(key, observation, fact_fp.value), instant=instant
            )
            if is_refusal(persisted):
                return persisted
            if not _complete_journal_ack(
                cast(object, persisted.value),
                self._journal,
                self.writer,
                expected_payload=_intent_payload(key, observation, fact_fp.value),
            ):
                return policy_rejection(
                    "journal_ack", "CT-15 intent has a complete durable CT-13 acknowledgment"
                )
            synchronized = self.writer.synchronize_prefix()
            if is_refusal(synchronized):
                return synchronized
            reservation = IntakeReservation(observation, complete=False)
            self._keys[key] = (fact_fp.value, reservation)
            return Ok(reservation)

    def complete(
        self,
        key: IntakeKey,
        observation: SourceObservation,
        *,
        instant: Instant,
    ) -> Result[None]:
        """Persist explicit completion after CT-10 admission and its acknowledgement."""
        try:
            with self._lock, _process_lock(self._journal):
                refreshed = self._refresh_process_state(instant)
                if is_refusal(refreshed):
                    return refreshed
                return self._complete_under_lock(key, observation, instant=instant)
        except OSError as exc:
            return invalid_input(
                "ct15_process_lock",
                "the CT-15 cross-process transaction lock is available",
                given=str(exc),
            )

    def _complete_under_lock(
        self,
        key: IntakeKey,
        observation: SourceObservation,
        *,
        instant: Instant,
    ) -> Result[None]:
        with self._lock:
            valid = _validate_key_observation(key, observation, self.writer.world)
            if is_refusal(valid):
                return valid
            fact_fp = _fact_fingerprint(observation)
            if is_refusal(fact_fp):
                return fact_fp
            refreshed = self._refresh_and_barrier(instant)
            if is_refusal(refreshed):
                return refreshed
            prior = self._keys.get(key)
            if prior is None or prior[0] != fact_fp.value:
                return _inconsistent_key(key)
            if prior[1].observation.fingerprint != observation.fingerprint:
                return policy_rejection(
                    "intake_identity",
                    "completion must acknowledge the exact CT-10 observation retained "
                    "by its intent",
                    source=key.source,
                    source_native_id=key.source_native_id,
                    revision=key.revision,
                )
            if prior[1].complete:
                return Ok(None)
            payload = {
                "class": _EVENT_CLASS,
                "action": _COMPLETE,
                "complete": True,
                "source": key.source,
                "source_native_id": key.source_native_id,
                "revision": key.revision,
                "fact_fingerprint": fact_fp.value,
                "observation_fingerprint": observation.fingerprint.value,
            }
            persisted = self.writer.record_data_quality(payload, instant=instant)
            if is_refusal(persisted):
                return persisted
            if not _complete_journal_ack(
                cast(object, persisted.value), self._journal, self.writer, expected_payload=payload
            ):
                return policy_rejection(
                    "journal_ack", "CT-15 completion has a complete durable CT-13 acknowledgment"
                )
            synchronized = self.writer.synchronize_prefix()
            if is_refusal(synchronized):
                return synchronized
            self._keys[key] = (
                fact_fp.value,
                IntakeReservation(observation, complete=True),
            )
            return Ok(None)

    def _refresh_and_barrier(self, instant: Instant) -> Result[None]:
        # The public operation holds the process lock and runs _refresh_process_state
        # before entering the key mutation path, so no second barrier is needed here.
        return Ok(None)

    def _refresh_process_state(self, instant: Instant) -> Result[None]:
        """Refresh sequence and indexes while holding the room-wide transaction lock."""
        synchronized = self.writer.synchronize_prefix()
        if is_refusal(synchronized):
            return synchronized
        events = JournalReader(self._journal).read_checked(
            _AUTHORITY_STREAM, for_world=self._journal.world, expected_start=0
        )
        if is_refusal(events):
            return events
        if self.writer.is_blocked:
            blocked = self.writer.blocked_event
            if blocked is None:
                return policy_rejection(
                    "ct15_blocked_event", "a blocked writer retains its exact event"
                )
            same_sequence = next(
                (
                    event
                    for event in events.value
                    if event.writer == blocked.writer and event.sequence == blocked.sequence
                ),
                None,
            )
            if same_sequence is not None and same_sequence.fingerprint != blocked.fingerprint:
                return policy_rejection(
                    "ct15_sequence_conflict",
                    "a blocked CT-15 event cannot reuse a sequence consumed by a different event",
                    sequence=blocked.sequence,
                )
            if same_sequence is None and any(
                event.writer == blocked.writer and event.sequence > blocked.sequence
                for event in events.value
            ):
                return policy_rejection(
                    "ct15_sequence_conflict",
                    "a previously blocked CT-15 event cannot be appended after later sequences",
                    sequence=blocked.sequence,
                )
            recovered = self.writer.retry_blocked()
            if is_refusal(recovered):
                return recovered
        events = JournalReader(self._journal).read_checked(
            _AUTHORITY_STREAM, for_world=self._journal.world, expected_start=0
        )
        if is_refusal(events):
            return events
        rebuilt = _rebuild_keys(events.value, self._journal.world)
        if is_refusal(rebuilt):
            return rebuilt
        resumed = JournalWriter.resume(
            self._journal, self.writer.writer, stream_name=_AUTHORITY_STREAM
        )
        if is_refusal(resumed):
            return resumed
        self.writer = resumed.value
        synced = resumed.value.synchronize_prefix()
        if is_refusal(synced):
            return synced
        self._keys.clear()
        self._keys.update(rebuilt.value)
        return _persist_recovery_barrier(self._journal, self.writer, events.value, instant=instant)


def _rebuild_keys(
    events: list[JournalEvent], world: object
) -> Result[dict[IntakeKey, tuple[str, IntakeReservation]]]:
    keys: dict[IntakeKey, tuple[str, IntakeReservation]] = {}
    for event in events:
        if event.event_type is not JournalEventType.DATA_QUALITY:
            continue
        payload = event.payload
        if payload.get("class") == _RECOVERY_CLASS:
            if payload != {
                "class": _RECOVERY_CLASS,
                "durable_prefix": True,
            }:
                return policy_rejection(
                    "ct15_recovery_barrier",
                    "a CT-15 recovery barrier explicitly covers the durable prefix",
                )
            continue
        if payload.get("class") != _EVENT_CLASS:
            continue
        parsed = _parse_event(payload, world)
        if is_refusal(parsed):
            return parsed
        action, key, fact_fp, observation_fp, observation = parsed.value
        current = keys.get(key)
        if action == _INTENT:
            if observation is None:
                return _inconsistent_key(key)
            if current is not None:
                if (
                    current[0] != fact_fp
                    or current[1].observation.fingerprint != observation.fingerprint
                ):
                    return _inconsistent_key(key)
                continue
            keys[key] = (fact_fp, IntakeReservation(observation, complete=False))
        else:
            if current is None or current[0] != fact_fp:
                return _inconsistent_key(key)
            if current[1].observation.fingerprint.value != observation_fp:
                return _inconsistent_key(key)
            keys[key] = (fact_fp, IntakeReservation(current[1].observation, complete=True))
    return Ok(keys)


def _persist_recovery_barrier(
    journal: JournalStore,
    writer: JournalWriter,
    events: list[JournalEvent],
    *,
    instant: Instant | None = None,
) -> Result[None]:
    """Fsync a new barrier before any previously visible intent is reusable."""
    barrier_instant = instant
    if barrier_instant is None:
        barrier_instant = Instant(
            value_ns=max((event.instant.value_ns for event in events), default=0)
        )
    payload = {
        "class": _RECOVERY_CLASS,
        "durable_prefix": True,
    }
    appended = writer.record_data_quality(payload, instant=barrier_instant)
    if is_refusal(appended):
        return appended
    if not _complete_journal_ack(
        cast(object, appended.value),
        journal,
        writer,
        expected_payload=payload,
        expected_instant=barrier_instant,
    ):
        return policy_rejection(
            "ct15_recovery_barrier",
            "the CT-13 recovery barrier is durably acknowledged and reopened",
        )
    synchronized = writer.synchronize_prefix()
    if is_refusal(synchronized):
        return synchronized
    return Ok(None)


def _complete_journal_ack(
    receipt: object,
    journal: JournalStore,
    writer: JournalWriter,
    *,
    expected_payload: Mapping[str, object],
    expected_instant: Instant | None = None,
) -> bool:
    if not isinstance(receipt, JournalAppendReceipt):
        return False
    event_value: object = cast(object, receipt.event)
    store_receipt_value: object = cast(object, receipt.store_receipt)
    if not isinstance(event_value, JournalEvent) or not isinstance(
        store_receipt_value, StoreReceipt
    ):
        return False
    event = event_value
    store_receipt = store_receipt_value
    if receipt.edge_receipts:
        return False
    if (
        event.event_type is not JournalEventType.DATA_QUALITY
        or event.writer != writer.writer
        or event.world is not journal.world
        or event.sequence != writer.next_sequence - 1
        or (expected_instant is not None and event.instant != expected_instant)
        or _thaw(event.payload) != _thaw(expected_payload)
    ):
        return False
    event_fp = fingerprint(event.fp1_identity())
    if is_refusal(event_fp) or event_fp.value != event.fingerprint:
        return False
    sequence_value: object = cast(object, store_receipt.sequence)
    format_value: object = cast(object, store_receipt.format_version)
    if (
        store_receipt.world is not journal.world
        or store_receipt.room_role is not RoomRole.JOURNAL
        or store_receipt.engine != "jsonl"
        or store_receipt.outcome not in (WriteOutcome.STORED, WriteOutcome.IDEMPOTENT)
        or store_receipt.is_evidence_bearing is not True
        or store_receipt.retained_forever is not True
        or isinstance(sequence_value, bool)
        or not isinstance(sequence_value, int)
        or sequence_value < 0
        or isinstance(format_value, bool)
        or not isinstance(format_value, int)
        or format_value != 1
    ):
        return False
    raw = journal.read_stream(writer.stream_name, for_world=journal.world)
    if is_refusal(raw) or sequence_value >= len(raw.value):
        return False
    row = raw.value[sequence_value]
    row_fp = fingerprint(row)
    persisted = JournalEvent.from_row(row)
    if (
        is_refusal(row_fp)
        or row_fp.value != store_receipt.fingerprint
        or is_refusal(persisted)
        or persisted.value.fingerprint != event.fingerprint
    ):
        return False
    checked = JournalReader(journal).read_checked(
        writer.stream_name, for_world=journal.world, expected_start=0
    )
    return not is_refusal(checked) and any(
        candidate.writer == event.writer
        and candidate.sequence == event.sequence
        and candidate.fingerprint == event.fingerprint
        for candidate in checked.value
    )


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        entries = cast("Mapping[object, object]", value)
        return {key: _thaw(item) for key, item in entries.items()}
    if isinstance(value, (tuple, list)):
        items = cast("list[object] | tuple[object, ...]", value)
        return [_thaw(item) for item in items]
    return value


def _intent_payload(
    key: IntakeKey, observation: SourceObservation, fact_fingerprint: str
) -> dict[str, object]:
    return {
        "class": _EVENT_CLASS,
        "action": _INTENT,
        "source": key.source,
        "source_native_id": key.source_native_id,
        "revision": key.revision,
        "fact_fingerprint": fact_fingerprint,
        "observation_fingerprint": observation.fingerprint.value,
        "observation": observation.to_row(),
    }


def _parse_event(
    payload: Mapping[str, object], world: object
) -> Result[tuple[str, IntakeKey, str, str, SourceObservation | None]]:
    action = payload.get("action")
    if action not in (_INTENT, _COMPLETE):
        return policy_rejection(
            "ct15_intake_authority", "a CT-15 authority event has a declared intent/complete action"
        )
    key = IntakeKey.try_create(
        payload.get("source"), payload.get("source_native_id"), payload.get("revision")
    )
    fact_fp = payload.get("fact_fingerprint")
    observation_fp = payload.get("observation_fingerprint")
    if is_refusal(key) or not isinstance(fact_fp, str) or not isinstance(observation_fp, str):
        return policy_rejection(
            "ct15_intake_authority", "a CT-15 authority event carries a valid key and fingerprints"
        )
    if action == _INTENT:
        observation = SourceObservation.from_row(payload.get("observation"))
        if is_refusal(observation):
            return observation
    else:
        if payload.get("complete") is not True or "observation" in payload:
            return policy_rejection(
                "ct15_intake_authority",
                "a completion event carries explicit complete=true and references its prior intent",
            )
        observation = Ok(None)
    if observation.value is not None:
        if observation.value.fingerprint.value != observation_fp:
            return policy_rejection(
                "ct15_intake_authority", "the durable CT-10 observation fingerprint does not verify"
            )
        valid = _validate_key_observation(key.value, observation.value, world)
        if is_refusal(valid):
            return valid
        actual_fact_fp = _fact_fingerprint(observation.value)
        if is_refusal(actual_fact_fp):
            return actual_fact_fp
        if actual_fact_fp.value != fact_fp:
            return policy_rejection(
                "ct15_intake_authority", "the durable provider-fact fingerprint does not verify"
            )
    return Ok((cast(str, action), key.value, fact_fp, observation_fp, observation.value))


def _validate_key_observation(
    key: IntakeKey, observation: SourceObservation, world: object
) -> Result[None]:
    if (key.source, key.source_native_id, key.revision) != (
        observation.source,
        observation.source_native_id,
        observation.revision,
    ):
        return invalid_input(
            "intake_identity",
            "the CT-15 key must match source, native id, and revision on the CT-10 observation",
        )
    if observation.world is not world:
        return policy_rejection(
            "world", "a CT-15 key authority is scoped to one world's CT-13 room"
        )
    return Ok(None)


def _fact_fingerprint(observation: SourceObservation) -> Result[str]:
    identity = observation.fp1_identity()
    identity.pop("receive_wall_time", None)
    identity.pop("writer", None)
    identity.pop("sequence", None)
    built = fingerprint(identity)
    if is_refusal(built):
        return built
    return Ok(built.value.value)


def _changed_fact(key: IntakeKey, prior: str, presented: str):
    return policy_rejection(
        "intake_identity",
        "the same CT-15 key was presented with different provider facts; issue a new revision",
        source=key.source,
        source_native_id=key.source_native_id,
        revision=key.revision,
        accepted_fact_fingerprint=prior,
        presented_fact_fingerprint=presented,
    )


def _inconsistent_key(key: IntakeKey):
    return policy_rejection(
        "ct15_intake_authority",
        "the checked CT-13 stream contains an inconsistent intent/completion for one CT-15 key",
        source=key.source,
        source_native_id=key.source_native_id,
        revision=key.revision,
    )
