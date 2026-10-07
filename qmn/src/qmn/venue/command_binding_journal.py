"""CT-13-backed readback for durable CT-19 venue-id bindings."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
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
from qmf.core.chrono import Instant
from qmf.data import JournalAppendReceipt, JournalEvent, JournalEventType, JournalWriter
from qmf.data.journal_producer import JournalReader
from qmf.data.store import JournalStore, StoreReceipt
from qmf.data.store.rooms import RoomRole
from qmf.venue import CommandIdBinding

from qmn.venue._refuse import invalid, policy

__all__ = [
    "COMMAND_ID_BINDING_RECORD_CLASS",
    "COMMAND_ID_BINDING_RECORD_VERSION",
    "QmfCommandIdBindingJournal",
]

COMMAND_ID_BINDING_RECORD_CLASS = "qmn-command-id-binding"
COMMAND_ID_BINDING_RECORD_VERSION = 1
_STREAM = "command-id-bindings"
_SUBTYPE = "qmn-command-id-binding"


@dataclass(slots=True)
class QmfCommandIdBindingJournal:
    """RecordSink adapter that reopens command binds from checked live CT-13."""

    journal: JournalStore
    writer: JournalWriter
    instant: Callable[[], Result[Instant]]
    authorized_writers: frozenset[WriterId]

    @classmethod
    def resume(
        cls,
        journal: object,
        writer: object,
        *,
        instant: object,
        authorized_writers: object,
    ) -> Result[QmfCommandIdBindingJournal]:
        if type(journal) is not JournalStore or journal.world is not World.LIVE:
            return invalid("journal", "CT-19 binding records persist to live QMF CT-13")
        if type(writer) is not WriterId or writer.stream != _STREAM:
            return invalid("writer", "command binds use the dedicated CT-13 writer stream")
        if not callable(instant):
            return invalid("instant", "command binding records use an injected wall clock")
        if not isinstance(authorized_writers, (Sequence, set, frozenset)) or isinstance(
            authorized_writers, (str, bytes)
        ):
            return invalid("authorized_writers", "command binding recovery names writer authority")
        members = tuple(cast("Sequence[object]", authorized_writers))
        if (
            not members
            or any(type(item) is not WriterId for item in members)
            or writer not in members
            or any(cast(WriterId, item).stream != _STREAM for item in members)
        ):
            return invalid(
                "authorized_writers", "binding stream authority contains its exact writers"
            )
        resumed = JournalWriter.resume(journal, writer, stream_name=_STREAM)
        if is_refusal(resumed):
            return resumed
        result = cls(
            journal=journal,
            writer=resumed.value,
            instant=cast("Callable[[], Result[Instant]]", instant),
            authorized_writers=frozenset(cast(WriterId, item) for item in members),
        )
        recovered = result._read_bindings()
        if is_refusal(recovered):
            return recovered
        return Ok(result)

    def write(self, value: object, /) -> Result[CommandIdBinding]:
        """Persist one CT-19 binding before handoff; identical recovered rows are idempotent."""
        binding = _validated_binding(value)
        if is_refusal(binding):
            return binding
        current = self.binding_for(binding.value.venue_client_id)
        if is_refusal(current):
            return current
        if current.value is not None:
            if current.value == binding.value:
                return Ok(binding.value)
            return policy("command_id_binding", "client id cannot be rebound to different content")
        at = self.instant()
        if is_refusal(at):
            return at
        if type(at.value) is not Instant:
            return invalid("instant", "command binding wall stamp is a typed Instant")
        payload = _binding_payload(binding.value)
        appended = self.writer.record_control_action(_SUBTYPE, instant=at.value, payload=payload)
        if is_refusal(appended):
            return appended
        checked = _validate_physical_append(
            appended.value,
            journal=self.journal,
            stream_name=_STREAM,
            writer=self.writer,
            instant=at.value,
            payload=payload,
        )
        if is_refusal(checked):
            return checked
        reopened = self.binding_for(binding.value.venue_client_id)
        if is_refusal(reopened):
            return reopened
        if reopened.value != binding.value:
            return policy("command_id_binding", "CT-19 binding reopens as exact checked evidence")
        return Ok(binding.value)

    def binding_for(self, venue_client_id: object) -> Result[CommandIdBinding | None]:
        if type(venue_client_id) is not str or not venue_client_id.strip():
            return invalid("venue_client_id", "lookup names a non-empty exact client id")
        rows = self._read_bindings()
        if is_refusal(rows):
            return rows
        matches = tuple(row for row in rows.value if row.venue_client_id == venue_client_id)
        if len(matches) > 1:
            return policy("command_id_binding", "one venue client id has one checked CT-19 bind")
        return Ok(matches[0] if matches else None)

    def _read_bindings(self) -> Result[tuple[CommandIdBinding, ...]]:
        rows = JournalReader(self.journal).read_checked(_STREAM, for_world=World.LIVE)
        if is_refusal(rows):
            return rows
        bindings: list[CommandIdBinding] = []
        clients: set[str] = set()
        for event in rows.value:
            if (
                event.writer not in self.authorized_writers
                or event.event_type is not JournalEventType.CONTROL_ACTION
                or event.world is not World.LIVE
                or type(event.sequence) is not int
            ):
                return policy("command_id_binding", "binding stream contains authorized live rows")
            if event.payload.get("control_action_subtype") != _SUBTYPE:
                return policy("command_id_binding", "dedicated binding stream carries binding rows")
            decoded = _decode_binding_payload(event.payload)
            if is_refusal(decoded):
                return decoded
            binding = decoded.value
            if binding.venue_client_id in clients:
                return policy("command_id_binding", "client id has one durable binding row")
            clients.add(binding.venue_client_id)
            bindings.append(binding)
        return Ok(tuple(bindings))


def _binding_payload(binding: CommandIdBinding) -> dict[str, object]:
    return {
        "binding_record_class": COMMAND_ID_BINDING_RECORD_CLASS,
        "binding_record_version": COMMAND_ID_BINDING_RECORD_VERSION,
        "command_id_binding": binding.fp1_identity(),
    }


def _validated_binding(value: object) -> Result[CommandIdBinding]:
    if type(value) is not CommandIdBinding:
        return invalid("command_id_binding", "RecordSink accepts exact CT-19 binding values")
    if (
        type(value.venue_client_id) is not str
        or not value.venue_client_id.strip()
        or type(value.account_id) is not str
        or not value.account_id.strip()
        or type(value.session_epoch) is not str
        or not value.session_epoch.strip()
        or type(value.command_fp1) is not Fingerprint
    ):
        return invalid(
            "command_id_binding", "binding carries exact client, command, account, epoch"
        )
    parsed = Fingerprint.try_create(value.command_fp1.value)
    if is_refusal(parsed):
        return parsed
    return Ok(
        CommandIdBinding(value.venue_client_id, parsed.value, value.account_id, value.session_epoch)
    )


def _decode_binding_payload(payload: Mapping[str, object]) -> Result[CommandIdBinding]:
    if (
        payload.get("binding_record_class") != COMMAND_ID_BINDING_RECORD_CLASS
        or type(payload.get("binding_record_version")) is not int
        or payload.get("binding_record_version") != COMMAND_ID_BINDING_RECORD_VERSION
    ):
        return invalid("command_id_binding", "row carries the exact versioned binding envelope")
    raw = payload.get("command_id_binding")
    if not isinstance(raw, Mapping):
        return invalid("command_id_binding", "row contains exact CT-19 identity fields")
    body = cast("Mapping[str, object]", raw)
    if set(body) != {
        "class",
        "command_fp1",
        "account_id",
        "venue_client_id",
        "session_epoch",
        "format_version",
    }:
        return invalid("command_id_binding", "row contains exact CT-19 identity fields")
    if (
        body.get("class") != "command-id-binding"
        or type(body.get("format_version")) is not int
        or body.get("format_version") != 1
        or type(body.get("venue_client_id")) is not str
        or type(body.get("account_id")) is not str
        or type(body.get("session_epoch")) is not str
    ):
        return invalid("command_id_binding", "row carries exact CT-19 identity scalar types")
    command_fp = Fingerprint.try_create(body.get("command_fp1"))
    if is_refusal(command_fp):
        return command_fp
    candidate = CommandIdBinding(
        venue_client_id=cast(str, body.get("venue_client_id")),
        command_fp1=command_fp.value,
        account_id=cast(str, body.get("account_id")),
        session_epoch=cast(str, body.get("session_epoch")),
    )
    return _validated_binding(candidate)


def _validate_physical_append(
    value: object,
    *,
    journal: JournalStore,
    stream_name: str,
    writer: JournalWriter,
    instant: Instant,
    payload: Mapping[str, object],
) -> Result[JournalEvent]:
    if type(value) is not JournalAppendReceipt:
        return policy("journal_receipt", "append ACK is an exact typed CT-13 receipt")
    event: object = cast(object, value.event)
    physical: object = cast(object, value.store_receipt)
    edges: object = cast(object, value.edge_receipts)
    if type(event) is not JournalEvent or type(physical) is not StoreReceipt:
        return policy("journal_receipt", "append ACK carries exact event and store receipt")
    expected_payload = dict(payload)
    expected_payload["control_action_subtype"] = _SUBTYPE
    if (
        type(edges) is not tuple
        or edges
        or event.event_type is not JournalEventType.CONTROL_ACTION
        or type(event.writer) is not WriterId
        or event.writer != writer.writer
        or type(event.sequence) is not int
        or event.sequence != writer.next_sequence - 1
        or type(event.instant) is not Instant
        or event.instant != instant
        or event.world is not World.LIVE
        or type(event.fingerprint) is not Fingerprint
        or event.outcome is not None
        or not _same_bytes(event.payload, expected_payload)
        or physical.world is not World.LIVE
        or physical.room_role is not RoomRole.JOURNAL
        or physical.engine != "jsonl"
        or physical.is_evidence_bearing is not True
        or physical.retained_forever is not True
        or type(physical.format_version) is not int
        or physical.format_version != 1
        or physical.engine_major is not None
        or physical.sequence is None
        or type(physical.sequence) is not int
        or physical.sequence < 0
        or physical.rebuild_calendar_identity is not None
        or physical.rebuild_tzdata_version is not None
        or type(physical.fingerprint) is not Fingerprint
        or type(physical.outcome) is not WriteOutcome
        or physical.outcome not in {WriteOutcome.STORED, WriteOutcome.IDEMPOTENT}
    ):
        return policy("journal_receipt", "append receipt binds exact live event and physical row")
    event_fp = fingerprint(event.fp1_identity())
    row_fp = fingerprint(event.to_row())
    if (
        is_refusal(event_fp)
        or event_fp.value != event.fingerprint
        or is_refusal(row_fp)
        or row_fp.value != physical.fingerprint
    ):
        return policy("journal_receipt", "event and physical row fingerprints recompute exactly")
    checked = JournalReader(journal).read_checked(stream_name, for_world=World.LIVE)
    raw = journal.read_stream(stream_name, for_world=World.LIVE)
    if is_refusal(checked):
        return checked
    if is_refusal(raw):
        return raw
    found = tuple(item for item in checked.value if item.fingerprint == event.fingerprint)
    index = physical.sequence
    if (
        len(found) != 1
        or not _same_bytes(found[0].to_row(), event.to_row())
        or index >= len(raw.value)
        or not _same_bytes(raw.value[index], event.to_row())
    ):
        return policy("journal_readback", "event and physical row independently reopen exactly")
    return Ok(event)


def _same_bytes(left: object, right: object) -> bool:
    left_result = canonical_bytes(left)
    right_result = canonical_bytes(right)
    return (
        not is_refusal(left_result)
        and not is_refusal(right_result)
        and left_result.value == right_result.value
    )
