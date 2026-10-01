"""Checked LIVE quote prices used only by the Book breakeven-ratchet path."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from qmf.core import (
    Fingerprint,
    Instant,
    Instrument,
    Ok,
    Price,
    Result,
    World,
    WriterId,
    canonical_bytes,
    fingerprint,
    is_refusal,
)
from qmf.data import JournalEvent, JournalEventType, JournalReader
from qmf.data.observation import SourceObservation
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore, JournalStore
from qmf.venue.ctrader import decode_market_data_price

from qmn.ledger._refuse import invalid, policy

__all__ = ["CheckedSpotPrices", "resolve_checked_live_spot_prices"]

_JOIN_CLASS = "qmn-live-observation-source-join"
_RAW_CLASS = "qmn-verbatim-response-json-v1"


@dataclass(frozen=True, slots=True)
class CheckedSpotPrices:
    """Bid/ask decoded from one independently reopened spot observation."""

    event: JournalEvent
    bid: Price
    ask: Price


def resolve_checked_live_spot_prices(
    *,
    journal: object,
    journal_stream: object,
    evidence_store: object,
    source_event: object,
    authorized_writers: object,
    instrument: object,
    expected_venue_id: object,
    expected_account_id: object,
    expected_session_epoch: object,
    not_before: object,
    decision_at: object,
) -> Result[CheckedSpotPrices]:
    """Reopen CT-13→CT-10/raw joins and decode exact recorded bid/ask values."""
    if type(journal) is not JournalStore or journal.world is not World.LIVE:
        return invalid("journal", "ratchet prices reopen from the exact LIVE CT-13 store")
    if type(evidence_store) is not EvidenceStore:
        return invalid("evidence_store", "ratchet prices reopen their QMF evidence archive")
    if type(journal_stream) is not str or not journal_stream.strip():
        return invalid("journal_stream", "ratchet prices name their checked CT-13 stream")
    if type(source_event) is not JournalEvent:
        return invalid("source_event", "ratchet price source is an exact CT-13 event")
    payload_value: object = getattr(cast(object, source_event), "payload", None)
    if (
        source_event.event_type is not JournalEventType.DATA_QUALITY
        or source_event.world is not World.LIVE
        or type(source_event.writer) is not WriterId
        or type(source_event.sequence) is not int
        or source_event.sequence < 0
        or type(source_event.instant) is not Instant
        or type(source_event.fingerprint) is not Fingerprint
        or source_event.outcome is not None
        or not isinstance(payload_value, Mapping)
    ):
        return invalid("source_event", "spot source carries exact LIVE CT-13 fields")
    if (
        type(instrument) is not Instrument
        or type(expected_venue_id) is not str
        or not expected_venue_id.strip()
        or type(expected_account_id) is not int
        or expected_account_id < 1
        or type(expected_session_epoch) is not str
        or not expected_session_epoch.strip()
        or type(not_before) is not Instant
        or type(decision_at) is not Instant
        or not (not_before.value_ns <= source_event.instant.value_ns <= decision_at.value_ns)
    ):
        return invalid("market_context", "spot price pins the exact venue/account/session/frontier")
    if not isinstance(authorized_writers, (tuple, list, set, frozenset)):
        return invalid("authorized_writers", "spot source authority is an explicit writer set")
    writers = cast(
        "tuple[object, ...] | list[object] | set[object] | frozenset[object]",
        authorized_writers,
    )
    if not writers or any(type(writer) is not WriterId for writer in writers):
        return invalid("authorized_writers", "spot source authority contains exact WriterIds")
    if source_event.writer not in writers:
        return policy("source_writer", "spot CT-13 row comes from an authorized venue writer")
    event_identity = fingerprint(source_event.fp1_identity())
    if is_refusal(event_identity) or event_identity.value != source_event.fingerprint:
        return policy("source_event", "spot event reproduces its checked CT-13 identity")
    checked = JournalReader(journal).read_checked(journal_stream, for_world=World.LIVE)
    if is_refusal(checked):
        return checked
    matches = tuple(
        event for event in checked.value if event.fingerprint == source_event.fingerprint
    )
    if len(matches) != 1 or matches[0].to_row() != source_event.to_row():
        return policy("source_event", "spot event independently reopens through checked CT-13")
    physical = journal.read_stream(journal_stream, for_world=World.LIVE)
    if is_refusal(physical):
        return physical
    expected_row = canonical_bytes(source_event.to_row())
    if is_refusal(expected_row):
        return expected_row
    physical_matches = 0
    for row in physical.value:
        actual_row = canonical_bytes(row)
        if is_refusal(actual_row):
            return actual_row
        physical_matches += actual_row.value == expected_row.value
    if physical_matches != 1:
        return policy("source_event", "spot event has one exact physical CT-13 row")

    join_value = source_event.payload.get("_qmn_source_join")
    if not isinstance(join_value, Mapping):
        return policy("source_join", "spot event carries its private CT-10/raw join")
    join = cast("Mapping[str, object]", join_value)
    if (
        join.get("class") != _JOIN_CLASS
        or type(join.get("format_version")) is not int
        or join.get("format_version") != 1
        or join.get("raw_encoding") != _RAW_CLASS
        or join.get("wire_kind") != "spot"
        or join.get("venue_id") != expected_venue_id
        or join.get("trader_account_id") != expected_account_id
        or type(join.get("session_epoch")) is not str
        or join.get("session_epoch") != expected_session_epoch
    ):
        return policy("source_join", "spot join binds exact LIVE venue/account/session identity")
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
    if len(raw_rows.value) != 1 or raw_rows.value[0].get("class") != _RAW_CLASS:
        return policy("raw_archive", "spot response reopens as one retained raw artifact")
    raw_body = raw_rows.value[0].get("body")
    if type(raw_body) is not str:
        return policy("raw_archive", "spot response is retained as canonical JSON text")
    try:
        decoded_body = json.loads(raw_body)
    except (TypeError, ValueError):
        return policy("raw_archive", "spot response JSON reopens without transformation")
    if not isinstance(decoded_body, Mapping):
        return policy("raw_archive", "spot response body is a mapping")
    raw_fp_check = fingerprint(raw_rows.value)
    if is_refusal(raw_fp_check) or raw_fp_check.value != raw_fp.value:
        return policy("raw_archive", "spot body reproduces its immutable archive identity")
    observation = SourceObservationBoundary(evidence_store).read(
        source_fp.value, in_world=World.LIVE, for_world=World.LIVE
    )
    if is_refusal(observation):
        return observation
    source = observation.value
    expected_writer = {
        "machine": source_event.writer.machine,
        "role": source_event.writer.role,
        "stream": source_event.writer.stream,
        "boot_epoch_id": source_event.writer.boot_epoch_id,
    }
    join_writer = join.get("writer")
    if (
        type(source) is not SourceObservation
        or source.fingerprint != observation_fp.value
        or source.world is not World.LIVE
        or source.writer != source_event.writer
        or source.sequence != source_event.sequence
        or source.known_at != source_event.instant
        or source.source != join.get("source")
        or source.source_native_id != join.get("source_native_id")
        or source.revision != join.get("revision")
        or source.event_time.value_ns != join.get("event_time_ns")
        or source.known_at.value_ns != join.get("known_at_ns")
        or source.known_at.value_ns > decision_at.value_ns
        or not isinstance(join_writer, Mapping)
        or dict(cast("Mapping[str, object]", join_writer)) != expected_writer
    ):
        return policy("source_observation", "spot CT-10 identity matches its exact CT-13 row")
    market_body = cast("Mapping[str, object]", decoded_body)
    bid = decode_market_data_price(market_body.get("bid"), instrument)
    ask = decode_market_data_price(market_body.get("ask"), instrument)
    if is_refusal(bid):
        return bid
    if is_refusal(ask):
        return ask
    if bid.value.value > ask.value.value:
        return policy("quote", "recorded spot quote has a non-crossed bid/ask")
    return Ok(CheckedSpotPrices(source_event, bid.value, ask.value))
