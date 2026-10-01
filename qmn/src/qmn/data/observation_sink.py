"""QMN live observation sinks with checked CT-10/raw and CT-13 receipts.

The source observation and the verbatim provider mapping are separate artifacts:
CT-10 owns bitemporal source identity, while the immutable raw archive keeps the
provider mapping unchanged. A later CT-13 witness binds both physical receipts.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from qmf.core import (
    DisplayTime,
    Fingerprint,
    Instant,
    Ok,
    Result,
    SinkAck,
    World,
    WriteOutcome,
    WriterId,
    canonical_bytes,
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
from qmf.data.observation import SourceObservation
from qmf.data.source_boundary import ObservationReceipt, SourceObservationBoundary
from qmf.data.store import EvidenceStore, JournalStore, StoreReceipt
from qmf.data.store.rooms import RoomRole

from qmn.data._refuse import invalid, policy

__all__ = ["QmfLiveJournalSink", "QmfLiveObservationSink"]

_RECEIPT_CLASS = "qmn-live-observation-write-v1"
_JOIN_CLASS = "qmn-live-observation-source-join"
_JOIN_VERSION = 1


@dataclass(frozen=True, slots=True)
class QmfLiveObservationSink:
    """Persist unchanged raw mappings plus their official CT-10 identity."""

    store: EvidenceStore
    writer: JournalWriter

    def emit(self, observation: object, /) -> Result[SinkAck]:
        if type(self.store) is not EvidenceStore or type(self.writer) is not JournalWriter:
            return invalid("sink", "live observation sink uses QMF EvidenceStore and JournalWriter")
        world_store = self.store.for_world(World.LIVE)
        if is_refusal(world_store):
            return world_store
        if self.writer.world is not World.LIVE:
            return policy("world", "live intake writes in the actual LIVE evidence namespace")
        if not isinstance(observation, Mapping):
            return invalid("observation", "live intake is a typed observation mapping")
        row = cast("Mapping[str, object]", observation)
        raw = row.get("raw_payload")
        if not isinstance(raw, Mapping):
            return invalid("raw_payload", "the unchanged provider response is retained verbatim")
        identity = _identity(row)
        if is_refusal(identity):
            return identity
        if (
            type(identity.value.get("venue_id")) is not str
            or not cast(str, identity.value["venue_id"]).strip()
            or type(identity.value.get("session_epoch")) is not str
            or not cast(str, identity.value["session_epoch"]).strip()
            or (
                identity.value.get("wire_kind") == "position-readback"
                and (
                    type(identity.value.get("trader_account_id")) is not int
                    or cast(int, identity.value["trader_account_id"]) < 1
                    or identity.value.get("session_epoch")
                    != identity.value.get("active_session_epoch")
                )
            )
        ):
            return invalid(
                "native_context",
                "live intake binds venue/session and readback account from response context",
            )
        raw_store = world_store.value.append_store
        typed_raw = cast("Mapping[str, object]", raw)
        body = _json_body(typed_raw)
        if is_refusal(body):
            return body
        raw_row: dict[str, object] = {
            "class": "qmn-verbatim-response-json-v1",
            "format_version": 1,
            "body": body.value,
        }
        raw_written = raw_store.append_raw([raw_row])
        if is_refusal(raw_written):
            return raw_written
        raw_receipt = raw_written.value
        raw_fp = fingerprint([raw_row])
        if is_refusal(raw_fp):
            return raw_fp
        if (
            type(raw_receipt) is not StoreReceipt
            or raw_receipt.fingerprint != raw_fp.value
            or raw_receipt.world is not World.LIVE
            or raw_receipt.room_role is not RoomRole.IMMUTABLE_RAW_ARCHIVE
            or raw_receipt.is_evidence_bearing is not True
            or raw_receipt.retained_forever is not True
            or raw_receipt.engine != "parquet"
            or type(raw_receipt.outcome) is not WriteOutcome
            or raw_receipt.sequence is not None
        ):
            return policy("raw_receipt", "raw response has the exact retained LIVE archive receipt")
        raw_readback = raw_store.read_raw(raw_receipt.fingerprint, for_world=World.LIVE)
        if is_refusal(raw_readback):
            return raw_readback
        if (
            len(raw_readback.value) != 1
            or raw_readback.value[0] != raw_row
            or _decode_json_body(raw_readback.value[0].get("body")) != typed_raw
        ):
            return policy("raw_readback", "raw provider mapping reopens byte-identically")

        source_observation = SourceObservation.try_create(
            event_time=identity.value["event_time"],
            known_at=identity.value["known_at"],
            source=identity.value["source"],
            source_native_id=identity.value["source_native_id"],
            revision=identity.value["revision"],
            receive_wall_time=identity.value["known_at"],
            writer=self.writer.writer,
            sequence=self.writer.next_sequence,
            world=World.LIVE,
        )
        if is_refusal(source_observation):
            return source_observation
        boundary = SourceObservationBoundary(self.store)
        source_receipt = boundary.admit(source_observation.value)
        if is_refusal(source_receipt):
            return source_receipt
        if type(source_receipt.value) is not ObservationReceipt:
            return policy("source_receipt", "CT-10 admits an exact typed ObservationReceipt")
        source_archive = source_receipt.value.archive
        if (
            type(source_archive) is not StoreReceipt
            or source_archive.world is not World.LIVE
            or source_archive.room_role is not RoomRole.IMMUTABLE_RAW_ARCHIVE
            or source_archive.is_evidence_bearing is not True
            or source_archive.retained_forever is not True
            or type(source_archive.outcome) is not WriteOutcome
        ):
            return policy("source_receipt", "CT-10 identity has its exact retained LIVE archive")
        reopened_source = boundary.read(
            source_receipt.value.archive.fingerprint,
            in_world=World.LIVE,
            for_world=World.LIVE,
        )
        if is_refusal(reopened_source):
            return reopened_source
        if reopened_source.value != source_observation.value:
            return policy("source_readback", "CT-10 observation reopens with exact identity")
        return Ok(
            SinkAck(
                detail={
                    "class": _RECEIPT_CLASS,
                    "format_version": 1,
                    "raw_store_receipt": raw_receipt,
                    "source_observation": source_observation.value,
                    "source_receipt": source_receipt.value,
                    "venue_id": identity.value["venue_id"],
                    "trader_account_id": identity.value["trader_account_id"],
                    "session_epoch": identity.value["session_epoch"],
                    "wire_kind": identity.value["wire_kind"],
                }
            )
        )


@dataclass(frozen=True, slots=True)
class QmfLiveJournalSink:
    """Append and reopen a CT-13 event carrying the CT-10/raw join witness."""

    writer: JournalWriter
    journal_store: object
    evidence_store: EvidenceStore

    def append(self, event: object, /) -> Result[SinkAck]:
        if type(self.writer) is not JournalWriter or self.writer.world is not World.LIVE:
            return invalid("writer", "live intake journals through the exact LIVE QMF writer")
        if not isinstance(event, Mapping):
            return invalid("event", "live journal event is a mapping")
        row = cast("Mapping[str, object]", event)
        observation_ack = row.get("_observation_ack")
        if type(observation_ack) is not SinkAck:
            return invalid("observation_ack", "CT-13 join consumes the exact raw/CT-10 ack")
        detail = observation_ack.detail
        if (
            detail.get("class") != _RECEIPT_CLASS
            or detail.get("format_version") != 1
            or type(detail.get("raw_store_receipt")) is not StoreReceipt
            or type(detail.get("source_receipt")) is not ObservationReceipt
            or type(detail.get("source_observation")) is not SourceObservation
        ):
            return policy("observation_ack", "CT-13 join requires verified CT-10 and raw receipts")
        raw_receipt = cast(StoreReceipt, detail["raw_store_receipt"])
        source_receipt = cast(ObservationReceipt, detail["source_receipt"])
        source_observation = cast(SourceObservation, detail["source_observation"])
        venue_id = detail.get("venue_id")
        trader_account_id = detail.get("trader_account_id")
        session_epoch = detail.get("session_epoch")
        identity = _journal_identity(row)
        if is_refusal(identity):
            return identity
        if (
            source_observation.fingerprint != source_receipt.observation_fingerprint
            or type(source_receipt.archive) is not StoreReceipt
            or source_receipt.archive.room_role is not RoomRole.IMMUTABLE_RAW_ARCHIVE
            or source_receipt.archive.world is not World.LIVE
            or raw_receipt.room_role is not RoomRole.IMMUTABLE_RAW_ARCHIVE
            or raw_receipt.world is not World.LIVE
            or source_observation.world is not World.LIVE
            or source_observation.writer != self.writer.writer
            or source_observation.sequence != self.writer.next_sequence
            or type(venue_id) is not str
            or not venue_id.strip()
            or (
                detail.get("wire_kind") == "position-readback"
                and (type(trader_account_id) is not int or trader_account_id < 1)
            )
            or type(session_epoch) is not str
            or not session_epoch.strip()
            or any(identity.value[k] != getattr(source_observation, attr) for k, attr in (
                ("event_time", "event_time"), ("known_at", "known_at"),
                ("source", "source"), ("source_native_id", "source_native_id"),
                ("revision", "revision"),
            ))
        ):
            return policy("source_join", "raw and CT-10 receipts bind this exact live observation")
        journal_type = _event_type(row.get("event_type"))
        if is_refusal(journal_type):
            return journal_type
        instant = identity.value["known_at"]
        if type(instant) is not Instant:
            return invalid("known_at", "CT-13 event is stamped at exact receive wall time")
        payload = {key: value for key, value in row.items() if key != "_observation_ack"}
        payload["_qmn_source_join"] = {
            "class": _JOIN_CLASS,
            "format_version": _JOIN_VERSION,
            "raw_archive_fp1": raw_receipt.fingerprint.value,
            "raw_encoding": "qmn-verbatim-response-json-v1",
            "source_observation_fp1": source_observation.fingerprint.value,
            "source_archive_fp1": source_receipt.archive.fingerprint.value,
            "source": source_observation.source,
            "source_native_id": source_observation.source_native_id,
            "revision": source_observation.revision,
            "event_time_ns": source_observation.event_time.value_ns,
            "known_at_ns": source_observation.known_at.value_ns,
            "venue_id": venue_id,
            "trader_account_id": trader_account_id,
            "session_epoch": session_epoch,
            "wire_kind": detail.get("wire_kind"),
            "writer": _writer_identity(source_observation.writer),
        }
        requested_payload_bytes = canonical_bytes(payload)
        if is_refusal(requested_payload_bytes):
            return requested_payload_bytes
        requested_payload_fp = fingerprint(payload)
        if is_refusal(requested_payload_fp):
            return requested_payload_fp
        appended = self.writer.record(journal_type.value, payload, instant=instant)
        if is_refusal(appended):
            return appended
        if type(appended.value) is not JournalAppendReceipt:
            return policy("journal_receipt", "CT-13 append returns exact durable receipt")
        receipt = appended.value
        event_value: object = receipt.event
        physical_value: object = receipt.store_receipt
        edge_value: object = receipt.edge_receipts
        if type(event_value) is not JournalEvent or type(physical_value) is not StoreReceipt:
            return policy(
                "journal_receipt", "CT-13 receipt contains exact typed event and store row"
            )
        event_payload: object = getattr(cast(object, event_value), "payload", None)
        if (
            type(edge_value) is not tuple
            or edge_value
            or type(event_value.event_type) is not JournalEventType
            or type(event_value.world) is not World
            or type(event_value.writer) is not WriterId
            or type(event_value.sequence) is not int
            or event_value.sequence < 0
            or type(event_value.instant) is not Instant
            or not isinstance(event_payload, Mapping)
            or type(event_value.fingerprint) is not Fingerprint
            or event_value.outcome is not None
            or (
                event_value.correlation_id is not None
                and type(event_value.correlation_id) is not str
            )
            or (
                event_value.display_time is not None
                and type(event_value.display_time) is not DisplayTime
            )
            or type(physical_value.world) is not World
            or type(physical_value.room_role) is not RoomRole
            or type(physical_value.fingerprint) is not Fingerprint
            or type(physical_value.sequence) is not int
            or physical_value.sequence < 0
            or type(physical_value.outcome) is not WriteOutcome
            or physical_value.outcome not in {WriteOutcome.STORED, WriteOutcome.IDEMPOTENT}
            or type(physical_value.engine) is not str
            or physical_value.engine != "jsonl"
            or type(physical_value.format_version) is not int
            or physical_value.format_version != 1
            or physical_value.is_evidence_bearing is not True
            or physical_value.retained_forever is not True
        ):
            return policy(
                "journal_receipt", "CT-13 event and physical receipt have exact field types"
            )
        event_fp = fingerprint(receipt.event.fp1_identity())
        row_fp = fingerprint(receipt.event.to_row())
        returned_payload_bytes = canonical_bytes(receipt.event.payload)
        returned_payload_fp = fingerprint(receipt.event.payload)
        failed_receipt_fields = tuple(
            name
            for name, okay in (
                ("event_type", type(receipt.event) is JournalEvent),
                ("event_kind", receipt.event.event_type is journal_type.value),
                ("event_world", receipt.event.world is World.LIVE),
                ("writer", receipt.event.writer == self.writer.writer),
                ("sequence", receipt.event.sequence == self.writer.next_sequence - 1),
                ("instant", receipt.event.instant == instant),
                (
                    "requested_payload",
                    not is_refusal(returned_payload_bytes)
                    and returned_payload_bytes.value == requested_payload_bytes.value
                    and not is_refusal(returned_payload_fp)
                    and returned_payload_fp.value == requested_payload_fp.value,
                ),
                ("outcome", receipt.event.outcome is None),
                (
                    "event_fp",
                    not is_refusal(event_fp) and event_fp.value == receipt.event.fingerprint,
                ),
                (
                    "row_fp",
                    not is_refusal(row_fp)
                    and row_fp.value == receipt.store_receipt.fingerprint,
                ),
                ("store_world", receipt.store_receipt.world is World.LIVE),
                ("store_role", receipt.store_receipt.room_role is RoomRole.JOURNAL),
                ("store_engine", receipt.store_receipt.engine == "jsonl"),
                (
                    "store_format",
                    type(receipt.store_receipt.format_version) is int
                    and receipt.store_receipt.format_version == 1,
                ),
                ("evidence", receipt.store_receipt.is_evidence_bearing is True),
                ("retained", receipt.store_receipt.retained_forever is True),
                ("physical_sequence", type(receipt.store_receipt.sequence) is int),
                (
                    "store_outcome",
                    type(receipt.store_receipt.outcome) is WriteOutcome
                    and receipt.store_receipt.outcome
                    in {WriteOutcome.STORED, WriteOutcome.IDEMPOTENT},
                ),
                ("store_fp_type", type(receipt.store_receipt.fingerprint) is Fingerprint),
                ("edges", not receipt.edge_receipts),
            )
            if not okay
        )
        if failed_receipt_fields:
            return policy(
                "journal_receipt",
                "CT-13 receipt binds exact durable event and row",
                failed_fields=failed_receipt_fields,
                actual_event_type=repr(receipt.event.event_type),
                expected_event_type=repr(journal_type.value),
            )
        if (
            type(self.journal_store) is not JournalStore
            or type(self.evidence_store) is not EvidenceStore
            or self.journal_store.world is not World.LIVE
        ):
            return invalid("journal_store", "checked CT-13 reader shares the exact journal store")
        world_store = self.evidence_store.for_world(World.LIVE)
        if is_refusal(world_store):
            return world_store
        raw_rows = world_store.value.append_store.read_raw(
            raw_receipt.fingerprint, for_world=World.LIVE
        )
        if is_refusal(raw_rows):
            return raw_rows
        if (
            len(raw_rows.value) != 1
            or raw_rows.value[0].get("class") != "qmn-verbatim-response-json-v1"
            or raw_rows.value[0].get("format_version") != 1
            or not isinstance(_decode_json_body(raw_rows.value[0].get("body")), Mapping)
        ):
            return policy("raw_readback", "cited raw response reopens as a checked mapping")
        raw_rows_fp = fingerprint(raw_rows.value)
        if is_refusal(raw_rows_fp) or raw_rows_fp.value != raw_receipt.fingerprint:
            return policy("raw_readback", "reopened raw bytes reproduce the archive fingerprint")
        source_reopen = SourceObservationBoundary(self.evidence_store).read(
            source_receipt.archive.fingerprint,
            in_world=World.LIVE,
            for_world=World.LIVE,
        )
        if is_refusal(source_reopen):
            return source_reopen
        if source_reopen.value != source_observation:
            return policy("source_readback", "cited CT-10 archive reopens exact identity")
        reader = JournalReader(self.journal_store)
        checked = reader.read_checked(self.writer.stream_name, for_world=World.LIVE)
        if is_refusal(checked):
            return checked
        matches = tuple(
            item for item in checked.value if item.fingerprint == receipt.event.fingerprint
        )
        if len(matches) != 1 or matches[0].to_row() != receipt.event.to_row():
            return policy("journal_readback", "CT-13 event reopens through the checked reader")
        journal_rows = self.journal_store.read_stream(
            self.writer.stream_name, for_world=World.LIVE
        )
        if is_refusal(journal_rows):
            return journal_rows
        physical_index = receipt.store_receipt.sequence
        if (
            type(physical_index) is not int
            or physical_index < 0
            or physical_index >= len(journal_rows.value)
            or journal_rows.value[physical_index] != receipt.event.to_row()
        ):
            return policy("journal_readback", "CT-13 physical row matches its exact append receipt")
        return Ok(SinkAck(detail={"journal_append_receipt": receipt}))


def _identity(row: Mapping[str, object]) -> Result[dict[str, object]]:
    obs = row.get("observation")
    if not isinstance(obs, Mapping):
        return invalid("observation", "recorded source identity is inside InboundObservation")
    typed_obs = cast("Mapping[str, object]", obs)
    payload = typed_obs.get("payload")
    if not isinstance(payload, Mapping):
        return invalid("payload", "inbound observation carries its original source mapping")
    source_row = cast("Mapping[str, object]", payload)
    event = Instant.try_create(source_row.get("event_time_ns"))
    known = Instant.try_create(source_row.get("known_at_ns"))
    if is_refusal(event):
        return event
    if is_refusal(known):
        return known
    fields = {
        "event_time": event.value,
        "known_at": known.value,
        "source": source_row.get("source"),
        "source_native_id": source_row.get("source_native_id"),
        "revision": source_row.get("revision"),
        "venue_id": source_row.get("venue_id"),
        "trader_account_id": source_row.get("response_account_id"),
        "session_epoch": (
            source_row.get("response_session_epoch")
            if source_row.get("response_session_epoch") is not None
            else source_row.get("session_epoch")
        ),
        "active_session_epoch": source_row.get("session_epoch"),
        "wire_kind": source_row.get("wire_kind"),
    }
    if any(type(fields[key]) is not str or not cast(str, fields[key]).strip() for key in (
        "source", "source_native_id", "revision"
    )):
        return invalid(
            "source_identity", "source/native/revision identifiers are non-empty strings"
        )
    return Ok(fields)


def _journal_identity(row: Mapping[str, object]) -> Result[dict[str, object]]:
    event = Instant.try_create(row.get("event_time_ns"))
    known = Instant.try_create(row.get("known_at_ns"))
    if is_refusal(event):
        return event
    if is_refusal(known):
        return known
    fields = {
        "event_time": event.value,
        "known_at": known.value,
        "source": row.get("source"),
        "source_native_id": row.get("source_native_id"),
        "revision": row.get("revision"),
    }
    if any(
        type(fields[key]) is not str or not cast(str, fields[key]).strip()
        for key in ("source", "source_native_id", "revision")
    ):
        return invalid(
            "source_identity", "source/native/revision identifiers are non-empty strings"
        )
    return Ok(fields)


def _event_type(value: object) -> Result[JournalEventType]:
    if type(value) is not str:
        return invalid("event_type", "CT-13 event type is a closed string token")
    try:
        return Ok(JournalEventType(value))
    except ValueError:
        return invalid("event_type", "CT-13 event type belongs to its closed vocabulary")


def _writer_identity(writer: WriterId) -> dict[str, str]:
    return {
        "machine": writer.machine,
        "role": writer.role,
        "stream": writer.stream,
        "boot_epoch_id": writer.boot_epoch_id,
    }


def _json_body(value: Mapping[str, object]) -> Result[str]:
    """Serialize a decoded provider mapping without interpreting numeric values."""
    if not _json_value(value):
        return invalid(
            "raw_payload",
            "verbatim mapping rows contain only finite JSON-native values and string keys",
        )
    try:
        return Ok(
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    except (TypeError, ValueError):
        return invalid("raw_payload", "provider mapping has a deterministic JSON representation")


def _decode_json_body(value: object) -> object:
    if type(value) is not str:
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _json_value(value: object) -> bool:
    if value is None or type(value) in {str, int, bool}:
        return True
    if type(value) is float:
        return math.isfinite(value)
    if isinstance(value, Mapping):
        typed = cast("Mapping[object, object]", value)
        return all(type(key) is str and _json_value(child) for key, child in typed.items())
    if type(value) in {list, tuple}:
        return all(_json_value(child) for child in cast("list[object] | tuple[object, ...]", value))
    return False
