"""Private, durable lineage for Book-declared protective ratchets.

This module records only an already-admitted plan and its explicitly declared
ratchet policy. It does not authorize venue commands; later consumers must join
this plan to the admitted position and fresh checked native evidence.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import cast

from qmf.core import (
    ExactRational,
    Fingerprint,
    Instant,
    Instrument,
    Ok,
    Price,
    PriceDelta,
    Result,
    UnitKind,
    VenueId,
    World,
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
from qmf.data.store import JournalStore, StoreReceipt
from qmf.data.store.rooms import RoomRole

from qmn.config.compiler import VALUE_STATUS_RATIFIED, ResolvedNodeConfig, ResolvedValueRow
from qmn.ledger._refuse import invalid, policy

__all__ = [
    "ProtectionAdmissionPlan",
    "ProtectionPlanReceipt",
    "ProtectionRatchetPolicy",
    "create_protection_admission_plan",
    "find_protection_admission_plan",
    "persist_protection_admission_plan",
    "read_protection_admission_plan",
    "resolve_protection_ratchet_policy",
]

_PLAN_CLASS = "qmn-book-protection-admission-plan"
_PLAN_EVENT_CLASS = "qmn-book-protection-admission-plan-event"
_PLAN_VERSION = 1


@dataclass(frozen=True, slots=True)
class ProtectionRatchetPolicy:
    """Exact Book-owned, non-default ratchet inputs from the resolved registry."""

    trigger: ExactRational
    offset: PriceDelta
    amend_min_improvement: ExactRational
    source_fp1: Fingerprint
    source_identity: Mapping[str, object]

    def fp1_identity(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "class": "qmn-book-breakeven-ratchet-policy",
                "format_version": 1,
                "trigger": _rational_record(self.trigger),
                "offset": _delta_record(self.offset),
                "amend_min_improvement": _rational_record(self.amend_min_improvement),
                "source_fp1": self.source_fp1.value,
                "source_identity": self.source_identity,
            }
        )


def resolve_protection_ratchet_policy(
    *, config: object, book_definition_fp1: object, book_instance_id: object, instrument: object
) -> Result[ProtectionRatchetPolicy]:
    """Resolve exact Book ratchet values from the full compiled node-config identity."""
    if type(config) is not ResolvedNodeConfig:
        return invalid("node_config", "ratchet values resolve from a compiled QMN node config")
    config_fp = fingerprint(config.fp1_identity())
    declared_config_fp = _fingerprint(config.fingerprint, "node_config_fp1")
    if is_refusal(config_fp):
        return config_fp
    if is_refusal(declared_config_fp):
        return declared_config_fp
    if config_fp.value != declared_config_fp.value:
        return policy("node_config", "compiled row bodies reproduce the declared full config fp1")
    definition_fp = _fingerprint(book_definition_fp1, "book_definition_fp1")
    if is_refusal(definition_fp):
        return definition_fp
    if type(book_instance_id) is not str or not book_instance_id.strip():
        return invalid("book_instance_id", "ratchet config is scoped to an exact CT-28 Book")
    resolved_instrument = _instrument(instrument)
    if is_refusal(resolved_instrument):
        return resolved_instrument
    names = (
        "breakeven_ratchet_trigger",
        "breakeven_ratchet_offset",
        "amend_min_improvement",
    )
    rows: dict[str, ResolvedValueRow] = {}
    for name in names:
        row = config.rows.get(name)
        if type(row) is not ResolvedValueRow:
            return policy(name, "ratchet registry has an exact resolved node-config row")
        if (
            row.name != name
            or row.value_status != VALUE_STATUS_RATIFIED
            or row.owner_scope != "book"
            or row.component != "COMP-QMF-RISK"
            or row.configurable is not True
            or row.value is None
        ):
            return policy(
                name,
                "ratchet registry row is ratified, Book-scoped and value-bearing for live use",
                value_status=row.value_status,
                owner_scope=row.owner_scope,
            )
        rows[name] = row
    trigger = _read_rational(rows["breakeven_ratchet_trigger"].value, names[0])
    offset = _read_delta(rows["breakeven_ratchet_offset"].value, names[1])
    minimum = _read_rational(rows["amend_min_improvement"].value, names[2])
    if is_refusal(trigger):
        return trigger
    if is_refusal(offset):
        return offset
    if is_refusal(minimum):
        return minimum
    if (
        trigger.value.unit_kind is not UnitKind.R_MULTIPLE
        or minimum.value.unit_kind is not UnitKind.R_MULTIPLE
    ):
        return policy("ratchet_units", "trigger and minimum improvement are exact R-multiples")
    if offset.value.instrument != resolved_instrument.value:
        return policy("breakeven_ratchet_offset", "offset is bound to the exact CT-03 instrument")
    source_identity = {
        "class": "qmn-resolved-book-ratchet-config",
        "format_version": 1,
        "book_definition_fp1": definition_fp.value.value,
        "book_instance_id": book_instance_id,
        "node_config_fp1": config_fp.value.value,
        "node_config_version": config.config_version,
        "resolved_rows": {name: rows[name].identity_entry() for name in names},
    }
    snapshot = _snapshot_identity(source_identity)
    if is_refusal(snapshot):
        return snapshot
    return Ok(
        ProtectionRatchetPolicy(
            trigger=trigger.value,
            offset=offset.value,
            amend_min_improvement=minimum.value,
            source_fp1=snapshot.value[1],
            source_identity=snapshot.value[0],
        )
    )


@dataclass(frozen=True, slots=True)
class ProtectionAdmissionPlan:
    """Book-minted entry reference and original risk, pinned to one command."""

    command_fp1: Fingerprint
    binding_epoch: Fingerprint
    bot_id: str
    family_id: str
    direction: str
    reference_price: Price
    original_risk_distance: PriceDelta
    policy: ProtectionRatchetPolicy

    def fp1_identity(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "class": _PLAN_CLASS,
                "format_version": _PLAN_VERSION,
                "command_fp1": self.command_fp1.value,
                "binding_epoch": self.binding_epoch.value,
                "bot_id": self.bot_id,
                "family_id": self.family_id,
                "direction": self.direction,
                "reference_price": _price_record(self.reference_price),
                "original_risk_distance": _delta_record(self.original_risk_distance),
                "policy": dict(self.policy.fp1_identity()),
            }
        )


@dataclass(frozen=True, slots=True)
class ProtectionPlanReceipt:
    """A protection plan tied to an independently checked CT-13 row."""

    plan: ProtectionAdmissionPlan
    plan_fp1: Fingerprint
    event: JournalEvent
    physical_receipt: StoreReceipt


@dataclass(frozen=True, slots=True)
class CheckedProtectionPlan:
    """A plan rehydrated from a unique checked CT-13 event after restart."""

    plan: ProtectionAdmissionPlan
    plan_fp1: Fingerprint
    event: JournalEvent


def create_protection_admission_plan(
    *,
    command_fp1: object,
    binding_epoch: object,
    bot_id: object,
    family_id: object,
    direction: object,
    reference_price: object,
    original_risk_distance: object,
    trigger: object,
    offset: object,
    amend_min_improvement: object,
    policy_source_identity: object,
) -> Result[ProtectionAdmissionPlan]:
    """Validate a complete, explicit plan without supplying policy defaults."""
    command = _fingerprint(command_fp1, "command_fp1")
    binding = _fingerprint(binding_epoch, "binding_epoch")
    policy_source = _snapshot_identity(policy_source_identity)
    if is_refusal(command):
        return command
    if is_refusal(binding):
        return binding
    if is_refusal(policy_source):
        return policy_source
    if type(bot_id) is not str or not bot_id.strip():
        return invalid("bot_id", "admission plan retains the selected Bot identity")
    if type(family_id) is not str or not family_id.strip():
        return invalid("family_id", "admission plan retains the selected strategy family")
    if direction not in {"long", "short"}:
        return invalid("direction", "admission plan retains the exact admitted position side")
    price = _validated_price(reference_price)
    risk = _validated_delta(original_risk_distance)
    resolved_offset = _validated_delta(offset)
    if is_refusal(price):
        return price
    if is_refusal(risk):
        return risk
    if is_refusal(resolved_offset):
        return resolved_offset
    if price.value.instrument != risk.value.instrument or price.value.scale != risk.value.scale:
        return policy("reference_price", "planned reference and original risk share CT-03 scale")
    if risk.value.value <= 0:
        return invalid("original_risk_distance", "admitted original risk distance is positive")
    if (
        resolved_offset.value.instrument != risk.value.instrument
        or resolved_offset.value.scale != risk.value.scale
    ):
        return policy("offset", "Book ratchet offset shares the admitted CT-03 price scale")
    trigger_value = _r_multiple(trigger, "breakeven_ratchet_trigger", positive=True)
    improvement_value = _r_multiple(amend_min_improvement, "amend_min_improvement", positive=False)
    if is_refusal(trigger_value):
        return trigger_value
    if is_refusal(improvement_value):
        return improvement_value
    ratchet = ProtectionRatchetPolicy(
        trigger=trigger_value.value,
        offset=resolved_offset.value,
        amend_min_improvement=improvement_value.value,
        source_fp1=policy_source.value[1],
        source_identity=policy_source.value[0],
    )
    return Ok(
        ProtectionAdmissionPlan(
            command_fp1=command.value,
            binding_epoch=binding.value,
            bot_id=bot_id,
            family_id=family_id,
            direction=cast(str, direction),
            reference_price=price.value,
            original_risk_distance=risk.value,
            policy=ratchet,
        )
    )


def persist_protection_admission_plan(
    plan: object,
    *,
    writer: object,
    journal: object,
    stream_name: object,
    at: object,
) -> Result[ProtectionPlanReceipt]:
    """Persist the plan as CT-13 RISK_TRANSITION and verify physical readback."""
    if type(plan) is not ProtectionAdmissionPlan:
        return invalid("plan", "plan persistence requires the exact validated private plan")
    if type(writer) is not JournalWriter or writer.world is not World.LIVE:
        return invalid("writer", "live protection plans use the exact LIVE QMF JournalWriter")
    if type(journal) is not JournalStore or journal.world is not World.LIVE:
        return invalid("journal", "live protection plans reopen the exact LIVE CT-13 store")
    if type(stream_name) is not str or stream_name != writer.stream_name or type(at) is not Instant:
        return invalid("stream_name", "plan persistence names its writer stream and instant")
    plan_fp = fingerprint(plan.fp1_identity())
    if is_refusal(plan_fp):
        return plan_fp
    payload = {
        "class": _PLAN_EVENT_CLASS,
        "format_version": _PLAN_VERSION,
        "kind": "admission-plan",
        "plan_fp1": plan_fp.value.value,
        "plan": dict(plan.fp1_identity()),
    }
    appended = writer.record(JournalEventType.RISK_TRANSITION, payload, instant=at)
    if is_refusal(appended):
        return appended
    if type(appended.value) is not JournalAppendReceipt:
        return policy("journal_receipt", "plan append ACK is a typed CT-13 receipt")
    receipt = appended.value
    event: object = receipt.event
    physical: object = receipt.store_receipt
    edges: object = receipt.edge_receipts
    if type(event) is not JournalEvent or type(physical) is not StoreReceipt:
        return policy(
            "journal_receipt", "plan append ACK contains exact event and physical receipt"
        )
    event_fp = fingerprint(event.fp1_identity())
    row_fp = fingerprint(event.to_row())
    if (
        type(edges) is not tuple
        or edges
        or event.event_type is not JournalEventType.RISK_TRANSITION
        or event.world is not World.LIVE
        or event.writer != writer.writer
        or type(event.sequence) is not int
        or event.sequence != writer.next_sequence - 1
        or event.instant != at
        or dict(event.payload) != payload
        or is_refusal(event_fp)
        or event_fp.value != event.fingerprint
        or is_refusal(row_fp)
        or physical.fingerprint != row_fp.value
        or physical.world is not World.LIVE
        or physical.room_role is not RoomRole.JOURNAL
        or physical.is_evidence_bearing is not True
        or physical.retained_forever is not True
        or type(physical.sequence) is not int
    ):
        return policy("journal_receipt", "CT-13 receipt binds the exact plan event and row")
    checked = JournalReader(journal).read_checked(stream_name, for_world=World.LIVE)
    if is_refusal(checked):
        return checked
    matches = tuple(item for item in checked.value if item.fingerprint == event.fingerprint)
    raw_rows = journal.read_stream(stream_name, for_world=World.LIVE)
    if is_refusal(raw_rows):
        return raw_rows
    physical_index = physical.sequence
    if (
        len(matches) != 1
        or matches[0].to_row() != event.to_row()
        or physical_index < 0
        or physical_index >= len(raw_rows.value)
        or not _same_canonical_row(raw_rows.value[physical_index], event.to_row())
    ):
        return policy("journal_readback", "CT-13 plan row reopens at its physical receipt index")
    return Ok(ProtectionPlanReceipt(plan, plan_fp.value, event, physical))


def read_protection_admission_plan(
    *, journal: object, stream_name: object, plan_fp1: object
) -> Result[CheckedProtectionPlan]:
    """Rehydrate one plan from its exact checked LIVE CT-13 transition."""
    if type(journal) is not JournalStore or journal.world is not World.LIVE:
        return invalid("journal", "protection plan readback uses the actual LIVE CT-13 store")
    if type(stream_name) is not str or not stream_name.strip():
        return invalid("stream_name", "protection plan readback names its CT-13 stream")
    expected_fp = _fingerprint(plan_fp1, "plan_fp1")
    if is_refusal(expected_fp):
        return expected_fp
    checked = JournalReader(journal).read_checked(stream_name, for_world=World.LIVE)
    if is_refusal(checked):
        return checked
    matches = tuple(
        event
        for event in checked.value
        if event.event_type is JournalEventType.RISK_TRANSITION
        and event.payload.get("class") == _PLAN_EVENT_CLASS
        and event.payload.get("plan_fp1") == expected_fp.value.value
    )
    if len(matches) != 1:
        return policy("plan_event", "one unique checked CT-13 event carries this plan identity")
    event = matches[0]
    event_payload = dict(event.payload)
    if set(event_payload) != {"class", "format_version", "kind", "plan_fp1", "plan"}:
        return policy("plan_event", "plan event has the exact private versioned fields")
    if (
        type(event_payload.get("format_version")) is not int
        or event_payload.get("format_version") != _PLAN_VERSION
        or event_payload.get("kind") != "admission-plan"
    ):
        return policy("plan_event", "plan event uses the exact supported private version")
    raw_plan = event_payload.get("plan")
    if not isinstance(raw_plan, Mapping):
        return policy("plan_event", "plan event carries its canonical typed identity body")
    plan_identity = cast("Mapping[str, object]", raw_plan)
    actual_fp = fingerprint(plan_identity)
    if is_refusal(actual_fp) or actual_fp.value != expected_fp.value:
        return policy("plan_event", "plan body reproduces its requested identity fingerprint")
    hydrated = _hydrate_plan(plan_identity)
    if is_refusal(hydrated):
        return hydrated
    physical_rows = journal.read_stream(stream_name, for_world=World.LIVE)
    if is_refusal(physical_rows):
        return physical_rows
    row_matches = tuple(
        row for row in physical_rows.value if _same_canonical_row(row, event.to_row())
    )
    if len(row_matches) != 1:
        return policy("plan_event", "plan event has one exact physical CT-13 row")
    return Ok(CheckedProtectionPlan(hydrated.value, expected_fp.value, event))


def find_protection_admission_plan(
    *, journal: object, stream_name: object, command_fp1: object, binding_epoch: object
) -> Result[CheckedProtectionPlan]:
    """Resolve one persisted plan by its CT-19 command and active CT-28 epoch."""
    command = _fingerprint(command_fp1, "command_fp1")
    binding = _fingerprint(binding_epoch, "binding_epoch")
    if is_refusal(command):
        return command
    if is_refusal(binding):
        return binding
    if type(journal) is not JournalStore or journal.world is not World.LIVE:
        return invalid("journal", "protection plan lookup uses the actual LIVE CT-13 store")
    if type(stream_name) is not str or not stream_name.strip():
        return invalid("stream_name", "protection plan lookup names its CT-13 stream")
    events = JournalReader(journal).read_checked(stream_name, for_world=World.LIVE)
    if is_refusal(events):
        return events
    candidates: list[Fingerprint] = []
    for event in events.value:
        if (
            event.event_type is not JournalEventType.RISK_TRANSITION
            or event.payload.get("class") != _PLAN_EVENT_CLASS
        ):
            continue
        raw_plan = event.payload.get("plan")
        if not isinstance(raw_plan, Mapping):
            continue
        body = cast("Mapping[str, object]", raw_plan)
        if (
            body.get("command_fp1") == command.value.value
            and body.get("binding_epoch") == binding.value.value
        ):
            candidate = Fingerprint.try_create(event.payload.get("plan_fp1"))
            if is_refusal(candidate):
                return candidate
            candidates.append(candidate.value)
    if len(candidates) != 1:
        return policy(
            "admission_plan",
            "one unique durable plan binds this CT-19 command and CT-28 epoch",
        )
    return read_protection_admission_plan(
        journal=journal, stream_name=stream_name, plan_fp1=candidates[0]
    )


def _fingerprint(value: object, field: str) -> Result[Fingerprint]:
    if type(value) is Fingerprint:
        return Fingerprint.try_create(value.value)
    return Fingerprint.try_create(value)


def _validated_price(value: object) -> Result[Price]:
    if type(value) is not Price:
        return invalid("reference_price", "planned reference is an exact QMF Price")
    instrument = _instrument(value.instrument)
    if is_refusal(instrument):
        return instrument
    return Price.try_create(value.value, instrument.value, value.scale)


def _validated_delta(value: object) -> Result[PriceDelta]:
    if type(value) is not PriceDelta:
        return invalid("price_delta", "risk and offset are exact QMF PriceDelta values")
    instrument = _instrument(value.instrument)
    if is_refusal(instrument):
        return instrument
    return PriceDelta.try_create(value.value, instrument.value, value.scale)


def _instrument(value: object) -> Result[Instrument]:
    if type(value) is not Instrument:
        return invalid("instrument", "plan price retains a validated CT-03 Instrument")
    if type(value.venue) is not VenueId:
        return invalid("instrument", "plan instrument retains a validated VenueId")
    venue = VenueId.try_create(value.venue.value)
    if is_refusal(venue):
        return venue
    return Instrument.try_create(venue.value, value.symbol)


def _r_multiple(value: object, field: str, *, positive: bool) -> Result[ExactRational]:
    if type(value) is not ExactRational:
        return invalid(field, "Book registry input is an ExactRational")
    checked = ExactRational.try_create(value.numerator, value.denominator, value.unit_kind)
    if is_refusal(checked):
        return checked
    if checked.value.unit_kind is not UnitKind.R_MULTIPLE:
        return invalid(field, "Book policy value is explicitly measured in R multiples")
    if (positive and checked.value.as_fraction() <= 0) or (
        not positive and checked.value.as_fraction() < 0
    ):
        return invalid(field, "Book policy value has a valid non-negative/positive magnitude")
    return checked


def _snapshot_identity(
    value: object,
) -> Result[tuple[Mapping[str, object], Fingerprint]]:
    if not isinstance(value, Mapping):
        return invalid("policy_source_identity", "Book policy source is a canonical identity map")
    source_mapping = cast("Mapping[str, object]", value)
    encoded = canonical_bytes(source_mapping)
    if is_refusal(encoded):
        return encoded
    try:
        decoded = json.loads(encoded.value.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return invalid("policy_source_identity", "Book policy source canonical bytes parse exactly")
    if not isinstance(decoded, dict):
        return invalid(
            "policy_source_identity", "Book policy source has string-keyed identity fields"
        )
    decoded_mapping = cast("dict[object, object]", decoded)
    if any(type(key) is not str for key in decoded_mapping):
        return invalid(
            "policy_source_identity", "Book policy source has string-keyed identity fields"
        )
    immutable = cast("Mapping[str, object]", _freeze_identity(decoded_mapping))
    source_fp = fingerprint(immutable)
    if is_refusal(source_fp):
        return source_fp
    return Ok((immutable, source_fp.value))


def _freeze_identity(value: object) -> object:
    if isinstance(value, dict):
        source = cast("dict[object, object]", value)
        frozen: dict[str, object] = {}
        for key, item in source.items():
            if type(key) is not str:
                raise TypeError("validated identity mapping has string keys")
            frozen[key] = _freeze_identity(item)
        return MappingProxyType(frozen)
    if isinstance(value, list):
        return tuple(_freeze_identity(item) for item in cast("list[object]", value))
    return value


def _same_canonical_row(left: object, right: object) -> bool:
    left_bytes = canonical_bytes(left)
    right_bytes = canonical_bytes(right)
    return (
        not is_refusal(left_bytes)
        and not is_refusal(right_bytes)
        and left_bytes.value == right_bytes.value
    )


def _hydrate_plan(value: Mapping[str, object]) -> Result[ProtectionAdmissionPlan]:
    if set(value) != {
        "class",
        "format_version",
        "command_fp1",
        "binding_epoch",
        "bot_id",
        "family_id",
        "direction",
        "reference_price",
        "original_risk_distance",
        "policy",
    }:
        return policy("plan_body", "persisted plan body has the exact private versioned fields")
    if (
        value.get("class") != _PLAN_CLASS
        or type(value.get("format_version")) is not int
        or value.get("format_version") != _PLAN_VERSION
    ):
        return policy("plan_body", "persisted plan body uses the exact supported version")
    price = _read_price(value.get("reference_price"), "reference_price")
    risk = _read_delta(value.get("original_risk_distance"), "original_risk_distance")
    if is_refusal(price):
        return price
    if is_refusal(risk):
        return risk
    raw_policy = value.get("policy")
    if not isinstance(raw_policy, Mapping):
        return policy("plan_policy", "persisted plan has a typed ratchet policy body")
    policy_body = cast("Mapping[str, object]", raw_policy)
    if set(policy_body) != {
        "class",
        "format_version",
        "trigger",
        "offset",
        "amend_min_improvement",
        "source_fp1",
        "source_identity",
    }:
        return policy("plan_policy", "persisted Book ratchet policy has exact identity fields")
    if (
        policy_body.get("class") != "qmn-book-breakeven-ratchet-policy"
        or type(policy_body.get("format_version")) is not int
        or policy_body.get("format_version") != 1
    ):
        return policy("plan_policy", "persisted Book ratchet policy uses its exact version")
    trigger = _read_rational(policy_body.get("trigger"), "breakeven_ratchet_trigger")
    offset = _read_delta(policy_body.get("offset"), "breakeven_ratchet_offset")
    improvement = _read_rational(policy_body.get("amend_min_improvement"), "amend_min_improvement")
    if is_refusal(trigger):
        return trigger
    if is_refusal(offset):
        return offset
    if is_refusal(improvement):
        return improvement
    source_identity = policy_body.get("source_identity")
    if not isinstance(source_identity, Mapping):
        return policy("plan_policy", "persisted policy carries its canonical source identity")
    source_fp = _fingerprint(policy_body.get("source_fp1"), "policy_source_fp1")
    if is_refusal(source_fp):
        return source_fp
    made = create_protection_admission_plan(
        command_fp1=value.get("command_fp1"),
        binding_epoch=value.get("binding_epoch"),
        bot_id=value.get("bot_id"),
        family_id=value.get("family_id"),
        direction=value.get("direction"),
        reference_price=price.value,
        original_risk_distance=risk.value,
        trigger=trigger.value,
        offset=offset.value,
        amend_min_improvement=improvement.value,
        policy_source_identity=cast("Mapping[str, object]", source_identity),
    )
    if is_refusal(made):
        return made
    if made.value.policy.source_fp1 != source_fp.value:
        return policy("plan_policy", "rehydrated exact policy source reproduces its fingerprint")
    return made


def _read_price(value: object, field: str) -> Result[Price]:
    if not isinstance(value, Mapping):
        return invalid(field, "persisted price level has a structured integer identity")
    row = cast("Mapping[str, object]", value)
    instrument = _read_instrument(row.get("instrument"), field)
    if is_refusal(instrument):
        return instrument
    if set(row) != {"value", "instrument", "scale"}:
        return invalid(field, "persisted price level has exact canonical fields")
    return Price.try_create(row.get("value"), instrument.value, row.get("scale"))


def _read_delta(value: object, field: str) -> Result[PriceDelta]:
    if not isinstance(value, Mapping):
        return invalid(field, "persisted price delta has a structured integer identity")
    row = cast("Mapping[str, object]", value)
    instrument = _read_instrument(row.get("instrument"), field)
    if is_refusal(instrument):
        return instrument
    if set(row) != {"value", "instrument", "scale"}:
        return invalid(field, "persisted price delta has exact canonical fields")
    return PriceDelta.try_create(row.get("value"), instrument.value, row.get("scale"))


def _read_instrument(value: object, field: str) -> Result[Instrument]:
    if not isinstance(value, Mapping):
        return invalid(field, "persisted CT-03 identity names venue and symbol")
    row = cast("Mapping[str, object]", value)
    if set(row) != {"venue", "symbol"}:
        return invalid(field, "persisted CT-03 identity has exact venue/symbol fields")
    venue = VenueId.try_create(row.get("venue"))
    if is_refusal(venue):
        return venue
    return Instrument.try_create(venue.value, row.get("symbol"))


def _read_rational(value: object, field: str) -> Result[ExactRational]:
    if not isinstance(value, Mapping):
        return invalid(field, "persisted Book registry ratio has an exact rational identity")
    row = cast("Mapping[str, object]", value)
    if set(row) != {"numerator", "denominator", "unit_kind"}:
        return invalid(field, "persisted exact ratio carries numerator/denominator/unit-kind")
    if type(row.get("numerator")) is not int or type(row.get("denominator")) is not int:
        return invalid(field, "persisted ratio components are exact integers")
    return ExactRational.try_create(
        row.get("numerator"), row.get("denominator"), row.get("unit_kind")
    )


def _price_record(value: Price) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "value": value.value,
            "instrument": {
                "venue": value.instrument.venue.value,
                "symbol": value.instrument.symbol,
            },
            "scale": value.scale,
        }
    )


def _rational_record(value: ExactRational) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "numerator": value.numerator,
            "denominator": value.denominator,
            "unit_kind": value.unit_kind.value,
        }
    )


def _delta_record(value: PriceDelta) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "value": value.value,
            "instrument": {
                "venue": value.instrument.venue.value,
                "symbol": value.instrument.symbol,
            },
            "scale": value.scale,
        }
    )
