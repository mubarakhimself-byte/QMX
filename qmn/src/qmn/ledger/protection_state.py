"""Checked private joins for native protection readbacks (no new CT contract)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast

from qmf.core import (
    Fingerprint,
    Instant,
    Instrument,
    Ok,
    Result,
    VenueId,
    World,
    WriterId,
    fingerprint,
    is_refusal,
)
from qmf.data import JournalEvent, JournalEventType, JournalReader
from qmf.data.observation import SourceObservation
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore, JournalStore

from qmn.ledger._refuse import invalid, policy
from qmn.venue.protection_readback import (
    NativeProtectionReadback,
    decode_native_protection_readback,
)

__all__ = ["resolve_checked_native_protection_readback"]

_JOIN_CLASS = "qmn-live-observation-source-join"
_JOIN_VERSION = 1
_RAW_CLASS = "qmn-verbatim-response-json-v1"


def resolve_checked_native_protection_readback(
    *,
    journal: object,
    journal_stream: object,
    evidence_store: object,
    source_event: object,
    authorized_writers: object,
    expected_position_id: object,
    expected_account_id: object,
    expected_session_epoch: object,
    expected_symbol_id: object,
    instrument: object,
    price_digits: object,
    rounding: object,
) -> Result[NativeProtectionReadback]:
    """Reopen checked CT-13 → CT-10/raw artifacts before decoding native stopLoss."""
    if type(journal) is not JournalStore or journal.world is not World.LIVE:
        return invalid("journal", "protection readback cites the actual LIVE CT-13 store")
    if type(evidence_store) is not EvidenceStore:
        return invalid("evidence_store", "protection readback reopens QMF evidence artifacts")
    if type(journal_stream) is not str or not journal_stream.strip():
        return invalid("journal_stream", "protection readback names its checked CT-13 stream")
    if type(source_event) is not JournalEvent:
        return invalid("source_event", "protection readback is an exact typed CT-13 event")
    # Nominal dataclasses can be forged with ordinary replacement; reject malformed
    # fields before calling fp1_identity()/to_row(), which assume constructor validity.
    payload_value: object = getattr(cast(object, source_event), "payload", None)
    if (
        type(source_event.event_type) is not JournalEventType
        or type(source_event.world) is not World
        or type(source_event.writer) is not WriterId
        or type(source_event.sequence) is not int
        or source_event.sequence < 0
        or type(source_event.instant) is not Instant
        or not isinstance(payload_value, Mapping)
        or type(source_event.fingerprint) is not Fingerprint
        or source_event.outcome is not None
    ):
        return invalid("source_event", "CT-13 event carries exact canonical field types")
    if (
        type(expected_account_id) is not int
        or expected_account_id < 1
        or type(expected_session_epoch) is not str
        or not expected_session_epoch.strip()
        or type(expected_symbol_id) is not int
        or expected_symbol_id < 1
    ):
        return invalid("native_context", "expected account/session/symbol authority is typed")
    if (
        source_event.event_type is not JournalEventType.DATA_QUALITY
        or source_event.world is not World.LIVE
        or type(source_event.writer) is not WriterId
    ):
        return policy("source_event", "position readback is LIVE data-quality evidence")
    if not isinstance(authorized_writers, (tuple, list, set, frozenset)):
        return invalid("authorized_writers", "source authority is an explicit writer-id set")
    writers = cast(
        "tuple[object, ...] | list[object] | set[object] | frozenset[object]",
        authorized_writers,
    )
    if not writers or any(type(writer) is not WriterId for writer in writers):
        return invalid("authorized_writers", "source authority contains exact WriterIds")
    if source_event.writer not in writers:
        return policy("source_writer", "CT-13 readback comes from an explicitly authorized writer")
    event_fp = fingerprint(source_event.fp1_identity())
    if is_refusal(event_fp) or event_fp.value != source_event.fingerprint:
        return policy("source_event", "CT-13 event identity reproduces its checked fingerprint")
    checked = JournalReader(journal).read_checked(journal_stream, for_world=World.LIVE)
    if is_refusal(checked):
        return checked
    matches = tuple(
        event for event in checked.value if event.fingerprint == source_event.fingerprint
    )
    if len(matches) != 1 or matches[0].to_row() != source_event.to_row():
        return policy("source_event", "exact CT-13 readback event reopens through checked reader")
    raw_journal_rows = journal.read_stream(journal_stream, for_world=World.LIVE)
    if is_refusal(raw_journal_rows):
        return raw_journal_rows
    matching_rows = tuple(row for row in raw_journal_rows.value if row == source_event.to_row())
    if len(matching_rows) != 1:
        return policy("source_event", "checked CT-13 event has one exact physical row")

    join_value = source_event.payload.get("_qmn_source_join")
    if not isinstance(join_value, Mapping):
        return policy("source_join", "checked CT-13 row cites its private CT-10/raw join")
    join = cast("Mapping[str, object]", join_value)
    required = {
        "class",
        "format_version",
        "raw_archive_fp1",
        "raw_encoding",
        "source_observation_fp1",
        "source_archive_fp1",
        "source",
        "source_native_id",
        "revision",
        "event_time_ns",
        "known_at_ns",
        "venue_id",
        "trader_account_id",
        "session_epoch",
        "wire_kind",
        "writer",
    }
    if frozenset(join) != frozenset(required) or (
        join.get("class") != _JOIN_CLASS
        or type(join.get("format_version")) is not int
        or join.get("format_version") != _JOIN_VERSION
        or join.get("raw_encoding") != "qmn-verbatim-response-json-v1"
        or join.get("wire_kind") != "position-readback"
    ):
        return policy("source_join", "private source join has the exact supported version")
    if type(instrument) is not Instrument or type(instrument.venue) is not VenueId:
        return invalid("instrument", "CT-03 instrument identity is fully typed")
    venue = VenueId.try_create(instrument.venue.value)
    if is_refusal(venue):
        return venue
    resolved_instrument = Instrument.try_create(venue.value, instrument.symbol)
    if is_refusal(resolved_instrument):
        return resolved_instrument
    if (
        type(join.get("trader_account_id")) is not int
        or join.get("trader_account_id") != expected_account_id
        or type(join.get("session_epoch")) is not str
        or join.get("session_epoch") != expected_session_epoch
        or resolved_instrument.value.venue.value != join.get("venue_id")
    ):
        return policy("native_context", "join account/session/venue match current native authority")
    raw_fp = Fingerprint.try_create(join.get("raw_archive_fp1"))
    source_fp = Fingerprint.try_create(join.get("source_archive_fp1"))
    observation_fp = Fingerprint.try_create(join.get("source_observation_fp1"))
    if is_refusal(raw_fp):
        return raw_fp
    if is_refusal(source_fp):
        return source_fp
    if is_refusal(observation_fp):
        return observation_fp
    world_store = evidence_store.for_world(World.LIVE)
    if is_refusal(world_store):
        return world_store
    raw_rows = world_store.value.append_store.read_raw(
        raw_fp.value, for_world=World.LIVE, at=source_event.instant
    )
    if is_refusal(raw_rows):
        return raw_rows
    if len(raw_rows.value) != 1:
        return policy("raw_archive", "cited native response reopens as one immutable raw artifact")
    row = raw_rows.value[0]
    if row.get("class") != _RAW_CLASS or row.get("format_version") != 1:
        return policy("raw_archive", "cited raw artifact uses the exact private response encoding")
    body_value = row.get("body")
    if type(body_value) is not str:
        return policy("raw_archive", "private raw response body is a canonical JSON text value")
    try:
        body = json.loads(body_value)
    except (TypeError, ValueError):
        return policy("raw_archive", "private raw response body parses without transformation")
    if not isinstance(body, Mapping):
        return policy("raw_archive", "private raw response body is a mapping")
    raw_fingerprint = fingerprint(raw_rows.value)
    if is_refusal(raw_fingerprint) or raw_fingerprint.value != raw_fp.value:
        return policy("raw_archive", "reopened response bytes reproduce the cited archive fp1")

    source_observation = SourceObservationBoundary(evidence_store).read(
        source_fp.value,
        in_world=World.LIVE,
        for_world=World.LIVE,
    )
    if is_refusal(source_observation):
        return source_observation
    observation = source_observation.value
    join_writer = join.get("writer")
    expected_writer = {
        "machine": source_event.writer.machine,
        "role": source_event.writer.role,
        "stream": source_event.writer.stream,
        "boot_epoch_id": source_event.writer.boot_epoch_id,
    }
    if not isinstance(join_writer, Mapping):
        return policy("source_observation", "CT-13 join cites the typed source writer identity")
    resolved_join_writer = cast("Mapping[str, object]", join_writer)
    if (
        type(observation) is not SourceObservation
        or observation.fingerprint != observation_fp.value
        or observation.world is not World.LIVE
        or observation.sequence != source_event.sequence
        or source_event.instant != observation.known_at
        or observation.source != join.get("source")
        or observation.source_native_id != join.get("source_native_id")
        or observation.revision != join.get("revision")
        or observation.event_time.value_ns != join.get("event_time_ns")
        or observation.known_at.value_ns != join.get("known_at_ns")
        or observation.writer != source_event.writer
        or dict(resolved_join_writer) != expected_writer
    ):
        return policy(
            "source_observation",
            "reopened CT-10 identity and CT-13 writer/sequence/frontier exactly match the join",
        )
    position = _position_body(cast("Mapping[object, object]", body), expected_position_id)
    if is_refusal(position):
        return position
    return decode_native_protection_readback(
        position.value,
        expected_position_id=expected_position_id,
        expected_account_id=expected_account_id,
        response_account_id=join.get("trader_account_id"),
        expected_session_epoch=expected_session_epoch,
        response_session_epoch=join.get("session_epoch"),
        expected_symbol_id=expected_symbol_id,
        instrument=resolved_instrument.value,
        price_digits=price_digits,
        rounding=rounding,
        source_event_fp1=source_event.fingerprint,
    )


def _position_body(
    body: Mapping[object, object], expected_position_id: object
) -> Result[Mapping[str, object]]:
    if body.get("positionId") is not None:
        return Ok(cast("Mapping[str, object]", body))
    return policy(
        "position",
        "recorded response does not carry a direct ProtoOAPosition row for this resolver",
        expected_position_id=repr(expected_position_id),
    )
