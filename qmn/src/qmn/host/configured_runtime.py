"""Operator-pinned configured-runtime preflight for the supervised QMN process.

This loader reads only deployment references and configuration.  It does not
mint activation authority, open provider connections, or make a roster eligible.
Missing or mismatched pinned protocol artifacts are ordinary typed stand-down
conditions.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import stat
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from qmf.core import Fingerprint, Ok, Result, VenueId, World, fingerprint, is_refusal
from qmf.core.chrono import Instant, WriterId
from qmf.data.journal_producer import JournalReader
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener
from qmf.registry import LoadedRecord, RegistryPersistence
from qmf.risk.binding import (
    BindingLineageEdgeKind,
    BmsInstanceId,
    BookBindingRecord,
    BookInstanceId,
    CapabilityCheckResult,
    ContinuesPerformanceEdge,
    PairingRecord,
    PositionModel,
    SignedLedgerEdge,
    StateCarry,
)
from qmf.risk.templates import BmsDefinition, BookDefinition
from qml.declaration import BotDefinition, mint_bot_definition

from qmn.config.compiler import ResolvedNodeConfig, compile_node_config
from qmn.config.roster import RosterRuntimeComposition, compose_roster_runtime
from qmn.host._refuse import clean_token, invalid, policy, unavailable
from qmn.host.registered_templates import decode_bms_definition, decode_book_definition
from qmn.promotion.journal import ActivationReconstruction, reconstruct_activation
from qmn.seats.state import OPERATOR_PRINCIPAL, GovernedSeatState
from qmn.venue.proto_runtime import compile_pinned_descriptor

if os.name == "nt":
    from qmn.host._windows_deployment import read_deployment

__all__ = [
    "CONFIGURED_REGISTRY_REFERENCE_KINDS",
    "CONFIGURED_RUNTIME_FORMAT_VERSION",
    "ConfiguredRuntimeAssessment",
    "assess_configured_runtime",
    "configured_registry_as_of_fingerprint",
    "main",
    "resolve_registered_binding",
]

CONFIGURED_RUNTIME_FORMAT_VERSION: Final[int] = 1
CONFIGURED_RUNTIME_FORMAT_V2: Final[int] = 2
_MAX_DEPLOYMENT_BYTES: Final[int] = 1 << 20
_O_NOFOLLOW: Final[int] = cast("int", getattr(os, "O_NOFOLLOW", 0))
_O_DIRECTORY: Final[int] = cast("int", getattr(os, "O_DIRECTORY", 0))
_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "format_version",
        "machine",
        "registry_root",
        "registry_as_of_fp1",
        "config_layers",
        "roster",
        "proto",
        "required_references",
    }
)
_TOP_LEVEL_KEYS_V2: Final[frozenset[str]] = _TOP_LEVEL_KEYS | {"host_resource_profile"}
_LAYER_KEYS: Final[frozenset[str]] = frozenset(
    {"roster", "bms", "book", "node_defaults", "roster_identity", "config_version"}
)
_ROSTER_KEYS: Final[frozenset[str]] = frozenset(
    {"account_bindings", "sensing_only", "protective_reserve_capacity"}
)
_PROTO_KEYS: Final[frozenset[str]] = frozenset(
    {"package_name", "release_tag", "descriptor_digest", "descriptor_path"}
)
_ACTIVATION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "journal_root",
        "stream_name",
        "event_fp1",
        "sequence",
        "writer",
        "world",
        "binding_id",
        "binding_epoch_fp1",
        "seat_id",
    }
)
CONFIGURED_REGISTRY_REFERENCE_KINDS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "ct28_fp1": "book-binding",
        "ct22_fp1": "book-definition",
        "ct27_fp1": "bms-definition",
        "ct33_fp1": "bot-definition",
    }
)


@dataclass(frozen=True, slots=True)
class ConfiguredRuntimeAssessment:
    """Validated operator configuration and the current fail-closed verdict."""

    machine: str
    registry_as_of: Fingerprint
    node_config: ResolvedNodeConfig
    roster: RosterRuntimeComposition
    registered_records: Mapping[str, LoadedRecord]
    book_definition: BookDefinition
    bms_definition: BmsDefinition
    bot_definition: BotDefinition
    binding_fingerprint: Fingerprint
    binding_record: BookBindingRecord
    activation_evidence_ref: str
    activation: ActivationReconstruction
    descriptor_digest: str
    stand_down_reason: str | None
    activation_authorized: bool = False
    provider_ready: bool = False
    host_resource_profile: Mapping[str, object] | None = None

    @property
    def stand_down(self) -> bool:
        return self.stand_down_reason is not None


def configured_registry_as_of_fingerprint(records: object) -> Result[Fingerprint]:
    """Fingerprint the exact four registration references in a deployment file."""
    if not isinstance(records, Mapping):
        return invalid("registered_records", "registered records are keyed by configured CT")
    body = cast("Mapping[str, object]", records)
    if set(body) != set(CONFIGURED_REGISTRY_REFERENCE_KINDS):
        return invalid(
            "registered_records",
            "the pinned set has exact CT-28, CT-22, CT-27 and CT-33 references",
        )
    identities: dict[str, str] = {}
    for name in sorted(CONFIGURED_REGISTRY_REFERENCE_KINDS):
        record = body[name]
        if not isinstance(record, LoadedRecord):
            return invalid("registered_records", "each reference resolves to a LoadedRecord")
        if record.kind != CONFIGURED_REGISTRY_REFERENCE_KINDS[name]:
            return policy(
                name,
                "the fingerprint-addressed record kind matches the exact configured CT",
                expected_kind=CONFIGURED_REGISTRY_REFERENCE_KINDS[name],
                actual_kind=record.kind,
            )
        identities[name] = record.persisted_fingerprint.value
    return fingerprint({"class": "qmn-configured-registry-as-of-v1", "records": identities})


def assess_configured_runtime(
    deployment_path: object,
    *,
    qmx_root: object,
) -> Result[ConfiguredRuntimeAssessment]:
    """Load, type-check and preflight one operator-pinned deployment document.

    Successful assessment only means its local declarations were parsed and
    compiled.  A missing protocol artifact returns an assessment that explicitly
    remains stand-down; an artifact on disk is compiled and digest checked, but
    this function never performs admission, activation or provider readiness.
    """
    path = _absolute_path(deployment_path, "deployment_path")
    if is_refusal(path):
        return path
    root = _absolute_path(qmx_root, "qmx_root")
    if is_refusal(root):
        return root
    try:
        input_root = root.value.absolute()
        input_path = path.value.absolute()
        relative_path = input_path.relative_to(input_root)
        resolved_root = input_root.resolve(strict=True)
        raw_bytes = _read_deployment_no_follow(input_root, relative_path)
    except (OSError, ValueError):
        return unavailable(
            "deployment_file",
            "the operator-pinned deployment file is readable beneath QMX_ROOT",
        )
    try:
        payload = json.loads(raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return invalid("deployment_file", "the configured deployment is valid UTF-8 JSON")
    if not isinstance(payload, Mapping):
        return invalid("deployment_file", "the configured deployment is a JSON object")
    body = cast("Mapping[str, object]", payload)
    version = body.get("format_version")
    if version is None:
        expected_keys = _TOP_LEVEL_KEYS
    elif type(version) is int and version in {
        CONFIGURED_RUNTIME_FORMAT_VERSION,
        CONFIGURED_RUNTIME_FORMAT_V2,
    }:
        expected_keys = _TOP_LEVEL_KEYS if version == 1 else _TOP_LEVEL_KEYS_V2
    else:
        return invalid("format_version", "configured-runtime format version is 1 or 2")
    keys = frozenset(body.keys())
    if keys != expected_keys:
        return invalid(
            "deployment_file",
            "the deployment has exactly the versioned configured-runtime fields",
            missing=sorted(expected_keys - keys),
            unknown=sorted(keys - expected_keys),
        )
    if version is None:
        return invalid("format_version", "configured-runtime format version is 1 or 2")
    host_profile: Mapping[str, object] | None = None
    if version == CONFIGURED_RUNTIME_FORMAT_V2:
        profile_pin = body.get("host_resource_profile")
        if not isinstance(profile_pin, Mapping):
            return invalid(
                "host_resource_profile",
                "version 2 pins an application-layer host resource profile",
            )
        pin = cast("Mapping[str, object]", profile_pin)
        if frozenset(pin) != frozenset({"descriptor_path", "descriptor_fp1"}):
            return invalid(
                "host_resource_profile",
                "profile pin contains only descriptor_path and descriptor_fp1",
            )
        profile_path = pin.get("descriptor_path")
        profile_fp = Fingerprint.try_create(pin.get("descriptor_fp1"))
        if is_refusal(profile_fp):
            return profile_fp
        if not isinstance(profile_path, str) or not Path(profile_path).is_absolute():
            return invalid(
                "host_resource_profile.descriptor_path",
                "profile descriptor path is absolute and operator pinned",
            )
        try:
            relative_profile = Path(profile_path).relative_to(root.value)
            profile_bytes = _read_deployment_no_follow(input_root, relative_profile)
        except (OSError, ValueError):
            return unavailable(
                "host_resource_profile",
                "profile descriptor is a regular no-follow file beneath QMX_ROOT",
            )
        try:
            raw_profile = json.loads(profile_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return invalid("host_resource_profile", "profile descriptor is UTF-8 JSON")
        if not isinstance(raw_profile, Mapping):
            return invalid("host_resource_profile", "profile descriptor is an object")
        profile_body = cast("Mapping[str, object]", raw_profile)
        actual_profile_fp = fingerprint(profile_body)
        if is_refusal(actual_profile_fp):
            return actual_profile_fp
        if actual_profile_fp.value != profile_fp.value:
            return policy(
                "host_resource_profile.descriptor_fp1",
                "profile descriptor bytes match the separately pinned fp1",
                failure_id="configured_runtime.host_profile_identity_mismatch",
            )
        frozen_profile = _freeze_json_mapping(profile_body, "host_resource_profile")
        if is_refusal(frozen_profile):
            return frozen_profile
        host_profile = frozen_profile.value

    machine = clean_token(body.get("machine"))
    if machine is None:
        return invalid("machine", "machine is the exact operator-pinned machine identity")
    as_of = Fingerprint.try_create(body.get("registry_as_of_fp1"))
    if is_refusal(as_of):
        return as_of
    if not isinstance(body.get("registry_root"), str):
        return invalid("registry_root", "registry_root is an operator-pinned path reference")
    registry_root = Path(cast("str", body["registry_root"]))
    if not registry_root.is_absolute():
        return invalid("registry_root", "registry_root is an absolute evidence-root reference")
    if not registry_root.is_dir():
        return unavailable(
            "registry_root",
            "the pinned registry evidence root is present and readable",
        )

    layers = _mapping(body.get("config_layers"), "config_layers", _LAYER_KEYS)
    if is_refusal(layers):
        return layers
    config_version = layers.value.get("config_version", 1)
    if type(config_version) is not int:
        return invalid("config_version", "config_version is a positive integer")
    compiled = compile_node_config(
        roster=layers.value.get("roster"),
        bms=layers.value.get("bms"),
        book=layers.value.get("book"),
        node_defaults=layers.value.get("node_defaults"),
        roster_identity=layers.value.get("roster_identity"),
        config_version=config_version,
    )
    if is_refusal(compiled):
        return compiled

    roster_decl = _mapping(body.get("roster"), "roster", _ROSTER_KEYS)
    if is_refusal(roster_decl):
        return roster_decl
    roster = compose_roster_runtime(
        account_bindings=roster_decl.value.get("account_bindings"),
        sensing_only=roster_decl.value.get("sensing_only"),
        protective_reserve_capacity=roster_decl.value.get("protective_reserve_capacity"),
    )
    if is_refusal(roster):
        return roster

    references = body.get("required_references")
    if not isinstance(references, Mapping):
        return invalid(
            "required_references",
            "deployment references name exact CT-28/22/27/33 and checked activation evidence",
        )
    reference_body = cast("Mapping[str, object]", references)
    expected_reference_keys = set(CONFIGURED_REGISTRY_REFERENCE_KINDS) | {"activation_evidence"}
    if set(reference_body) != expected_reference_keys:
        return invalid(
            "required_references",
            "required references contain exact CT-28/22/27/33 records and activation boundary",
            missing=sorted(expected_reference_keys - set(reference_body)),
            unknown=sorted(set(reference_body) - expected_reference_keys),
        )
    activation_ref = _mapping(
        reference_body.get("activation_evidence"), "activation_evidence", _ACTIVATION_KEYS
    )
    if is_refusal(activation_ref):
        return activation_ref
    if frozenset(activation_ref.value) != _ACTIVATION_KEYS:
        return invalid("activation_evidence", "activation pins the exact CT13/24 boundary fields")
    loaded = _load_registered_records(registry_root, reference_body)
    if is_refusal(loaded):
        return loaded
    actual_as_of = configured_registry_as_of_fingerprint(loaded.value)
    if is_refusal(actual_as_of):
        return actual_as_of
    if as_of.value != actual_as_of.value:
        return policy(
            "registry_as_of_fp1",
            "the operator pin exactly matches the loaded CT-28/22/27/33 registrations",
            failure_id="configured_runtime.registry_as_of_mismatch",
            expected=actual_as_of.value.value,
            offered=as_of.value.value,
        )
    artifacts = _decode_registered_artifacts(loaded.value)
    if is_refusal(artifacts):
        return artifacts
    activation = _load_activation_evidence(
        activation_ref.value,
        qmx_root=resolved_root,
        expected_binding=artifacts.value[4],
    )
    if is_refusal(activation):
        return activation
    for key in reference_body:
        if clean_token(key) is None:
            return invalid(
                "required_references",
                "each reference key is a nonblank token",
            )

    proto = _mapping(body.get("proto"), "proto", _PROTO_KEYS)
    if is_refusal(proto):
        return proto
    package_name = clean_token(proto.value.get("package_name"))
    digest = clean_token(proto.value.get("descriptor_digest"))
    release_tag = proto.value.get("release_tag")
    descriptor_path = proto.value.get("descriptor_path")
    if package_name is None or digest is None:
        return invalid("proto", "the protocol package and descriptor digest are pinned")
    if type(release_tag) is not int or release_tag <= 0:
        return invalid("proto.release_tag", "the protocol release tag is a positive integer")
    if not isinstance(descriptor_path, str) or not descriptor_path:
        return unavailable(
            "proto_descriptor",
            "pinned protocol descriptor bytes are absent; configured runtime remains stand-down",
            failure_id="configured_runtime.proto_missing",
        )
    descriptor = Path(descriptor_path)
    if not descriptor.is_absolute():
        return invalid("proto.descriptor_path", "protocol descriptor path is absolute")
    try:
        descriptor_bytes = descriptor.read_bytes()
    except OSError:
        return unavailable(
            "proto_descriptor",
            "pinned protocol descriptor bytes are absent; configured runtime remains stand-down",
            failure_id="configured_runtime.proto_missing",
        )
    compiled_proto = compile_pinned_descriptor(
        descriptor_bytes,
        package_name=package_name,
        release_tag=release_tag,
        expected_digest=digest,
    )
    if is_refusal(compiled_proto):
        return compiled_proto

    # Local config + descriptor validity cannot substitute for CT-28 admission,
    # an activation boundary or the rest of the sealed host composition.
    return Ok(
        ConfiguredRuntimeAssessment(
            machine=machine,
            registry_as_of=as_of.value,
            node_config=compiled.value,
            roster=roster.value,
            registered_records=loaded.value,
            book_definition=artifacts.value[0],
            bms_definition=artifacts.value[1],
            bot_definition=artifacts.value[2],
            binding_fingerprint=artifacts.value[3],
            binding_record=artifacts.value[4],
            activation_evidence_ref=activation.value[0],
            activation=activation.value[1],
            descriptor_digest=digest,
            stand_down_reason=(
                "configured deployment declarations validated; authoritative registered "
                "seat resolution, activation, and boot ceremony have not been admitted"
            ),
            host_resource_profile=host_profile,
        )
    )


def _load_registered_records(
    registry_root: Path,
    references: Mapping[str, object],
) -> Result[Mapping[str, LoadedRecord]]:
    persistence = RegistryPersistence.open(EvidenceStore(registry_root), World.LIVE)
    if is_refusal(persistence):
        return persistence
    loaded: dict[str, LoadedRecord] = {}
    try:
        for name, expected_kind in CONFIGURED_REGISTRY_REFERENCE_KINDS.items():
            ref = Fingerprint.try_create(references.get(name))
            if is_refusal(ref):
                return ref
            record = persistence.value.load_record(ref.value, for_world=World.LIVE)
            if is_refusal(record):
                return record
            if record.value.kind != expected_kind:
                return policy(
                    name,
                    "the fingerprint-addressed record kind matches its CT reference",
                    expected_kind=expected_kind,
                    actual_kind=record.value.kind,
                    failure_id="configured_runtime.record_kind_mismatch",
                )
            loaded[name] = record.value
    finally:
        persistence.value.close()
    return Ok(MappingProxyType(loaded))


def _load_activation_evidence(
    reference: Mapping[str, object],
    *,
    qmx_root: Path,
    expected_binding: BookBindingRecord,
) -> Result[tuple[str, ActivationReconstruction]]:
    """Hydrate one exact committed CT-24 transition from its checked CT-13 event."""
    if reference.get("world") != World.LIVE.value:
        return policy("activation_evidence.world", "activation evidence is from the live world")
    stream_name = clean_token(reference.get("stream_name"))
    binding_id = clean_token(reference.get("binding_id"))
    seat_id = clean_token(reference.get("seat_id"))
    if stream_name is None or binding_id is None or seat_id is None:
        return invalid("activation_evidence", "stream, seat and binding ids are nonblank")
    if binding_id != expected_binding.book_instance_id.value:
        return policy(
            "activation_evidence.binding_id",
            "the activation names this exact CT-28 Book instance",
            failure_id="configured_runtime.activation_binding_mismatch",
        )
    expected_epoch = Fingerprint.try_create(reference.get("binding_epoch_fp1"))
    if is_refusal(expected_epoch):
        return expected_epoch
    actual_epoch = expected_binding.fingerprint()
    if is_refusal(actual_epoch):
        return actual_epoch
    if expected_epoch.value != actual_epoch.value:
        return policy(
            "activation_evidence.binding_epoch_fp1",
            "activation evidence pins the exact typed CT-28 binding epoch",
            failure_id="configured_runtime.activation_binding_mismatch",
        )
    writer_raw = reference.get("writer")
    if not isinstance(writer_raw, Mapping):
        return invalid("activation_evidence.writer", "the exact QMF WriterId family is pinned")
    writer_body = cast("Mapping[str, object]", writer_raw)
    if frozenset(writer_body) != frozenset(
        {
            "machine",
            "role",
            "stream",
            "boot_epoch_id",
        }
    ):
        return invalid("activation_evidence.writer", "the exact QMF WriterId family is pinned")
    writer_values = writer_body
    writer = WriterId.try_create(
        writer_values.get("machine"),
        writer_values.get("role"),
        writer_values.get("stream"),
        writer_values.get("boot_epoch_id"),
    )
    if is_refusal(writer):
        return writer
    sequence = reference.get("sequence")
    if type(sequence) is not int or sequence < 0:
        return invalid("activation_evidence.sequence", "event sequence is a nonnegative integer")
    event_fp = Fingerprint.try_create(reference.get("event_fp1"))
    if is_refusal(event_fp):
        return event_fp
    root = _path_beneath_root(reference.get("journal_root"), qmx_root, "activation_journal_root")
    if is_refusal(root):
        return root
    opened = JournalStore(World.LIVE, journal_dir=root.value, open_stream=jsonl_opener())
    reader = JournalReader(opened)
    try:
        events = reader.read_checked(stream_name, for_world=World.LIVE)
    finally:
        opened.close()
    if is_refusal(events):
        return events
    matched = tuple(event for event in events.value if event.fingerprint == event_fp.value)
    if len(matched) != 1:
        return unavailable(
            "activation_event",
            "the pinned CT-13 event fingerprint resolves exactly once in the checked stream",
            failure_id="configured_runtime.activation_event_missing",
        )
    event = matched[0]
    if (
        event.world is not World.LIVE
        or event.event_type.value != "risk transition"
        or event.writer != writer.value
        or event.sequence != sequence
    ):
        return policy(
            "activation_event",
            "event world, CT-13 type, writer family and logical sequence match the operator pin",
            failure_id="configured_runtime.activation_event_mismatch",
        )
    rebuilt = reconstruct_activation(
        {"event_type": event.event_type.value, "payload": event.payload}, None
    )
    if is_refusal(rebuilt):
        return rebuilt
    transition = rebuilt.value.transition
    if (
        transition.binding_id != binding_id
        or transition.seat_id != seat_id
        or transition.operator_signature != OPERATOR_PRINCIPAL
        or transition.phase.value != "successful"
        or transition.requested_state is not GovernedSeatState.ACTIVE
        or transition.enforced_state is not GovernedSeatState.ACTIVE
        or transition.transition_instant.value_ns > event.instant.value_ns
        or (
            transition.effective_at is not None
            and transition.effective_at.value_ns > event.instant.value_ns
        )
    ):
        return policy(
            "activation_transition",
            "CT-24 transition is operator-signed successful activation for this seat and binding",
            failure_id="configured_runtime.activation_transition_mismatch",
        )
    return Ok((event_fp.value.value, rebuilt.value))


def _path_beneath_root(value: object, root: Path, field: str) -> Result[Path]:
    if not isinstance(value, str) or not Path(value).is_absolute():
        return invalid(field, "evidence path is an absolute operator-pinned path")
    try:
        path = Path(value).resolve(strict=True)
        path.relative_to(root)
        if not path.is_dir():
            return invalid(field, "journal root is a directory beneath QMX_ROOT")
    except (OSError, ValueError):
        return unavailable(field, "evidence directory exists beneath QMX_ROOT")
    return Ok(path)


def _decode_registered_artifacts(
    records: Mapping[str, LoadedRecord],
) -> Result[tuple[BookDefinition, BmsDefinition, BotDefinition, Fingerprint, BookBindingRecord]]:
    book_record = records["ct22_fp1"]
    book = decode_book_definition(book_record.contract_format_version, book_record.body)
    if is_refusal(book):
        return book
    book_fp = book.value.fingerprint()
    if is_refusal(book_fp):
        return book_fp

    bms_record = records["ct27_fp1"]
    bms = decode_bms_definition(bms_record.contract_format_version, bms_record.body)
    if is_refusal(bms):
        return bms
    bms_fp = bms.value.fingerprint()
    if is_refusal(bms_fp):
        return bms_fp

    bot_record = records["ct33_fp1"]
    bot = mint_bot_definition(
        bot_record.body,
        format_version=bot_record.contract_format_version,
        at_birth_parent_refs=bot_record.at_birth_parent_refs,
    )
    if is_refusal(bot):
        return bot

    typed_binding = resolve_registered_binding(
        records["ct28_fp1"].body,
        expected_book_fp=book_fp.value,
        expected_bms_fp=bms_fp.value,
    )
    if is_refusal(typed_binding):
        return typed_binding
    binding_fp = typed_binding.value.fingerprint()
    if is_refusal(binding_fp):
        return binding_fp
    return Ok((book.value, bms.value, bot.value, binding_fp.value, typed_binding.value))


def resolve_registered_binding(
    value: object,
    *,
    expected_book_fp: object,
    expected_bms_fp: object,
) -> Result[BookBindingRecord]:
    """Decode a persisted CT-28 identity into its canonical QMF binding type."""
    if not isinstance(value, Mapping):
        return invalid("ct28_fp1", "the registered CT-28 body is a mapping")
    body = cast("Mapping[str, object]", value)
    book_fp = (
        Ok(expected_book_fp)
        if isinstance(expected_book_fp, Fingerprint)
        else Fingerprint.try_create(expected_book_fp)
    )
    bms_fp = (
        Ok(expected_bms_fp)
        if isinstance(expected_bms_fp, Fingerprint)
        else Fingerprint.try_create(expected_bms_fp)
    )
    if is_refusal(book_fp):
        return book_fp
    if is_refusal(bms_fp):
        return bms_fp
    venue = VenueId.try_create(body.get("venue_id"))
    if is_refusal(venue):
        return venue
    account = clean_token(body.get("account_id"))
    world = body.get("world")
    if account is None or world != World.LIVE.value:
        return policy(
            "ct28_fp1",
            "the persisted binding names a nonblank account and live world",
            failure_id="configured_runtime.binding_mismatch",
        )
    if body.get("class") != "book-binding-record":
        return policy(
            "ct28_fp1",
            "the persisted record carries the canonical BookBindingRecord class",
            failure_id="configured_runtime.binding_mismatch",
        )
    if (
        body.get("book_definition_fingerprint") != book_fp.value.value
        or body.get("bms_definition_fingerprint") != bms_fp.value.value
    ):
        return policy(
            "ct28_fp1",
            "the binding cites the exactly decoded CT-22 and CT-27 versions",
            failure_id="configured_runtime.binding_mismatch",
        )
    book_instance = BookInstanceId.try_create(body.get("book_instance_id"))
    if is_refusal(book_instance):
        return book_instance
    bms_instance = BmsInstanceId.derive(bms_fp.value, account, venue.value, World.LIVE)
    if is_refusal(bms_instance):
        return bms_instance
    if body.get("bms_instance_id") != bms_instance.value.value:
        return policy(
            "ct28_fp1.bms_instance_id",
            "the BMS instance id is derived from exact BMS, account, venue and world",
            failure_id="configured_runtime.binding_mismatch",
        )
    raw_state = body.get("state_carry")
    if not isinstance(raw_state, Mapping):
        return invalid("ct28_fp1.state_carry", "the binding carries typed StateCarry identity")
    state_body = cast("Mapping[str, object]", raw_state)
    if state_body.get("class") != "state-carry":
        return invalid("ct28_fp1.state_carry", "the binding carries typed StateCarry identity")
    state_carry = StateCarry.try_create(state_body.get("per_counter"))
    if is_refusal(state_carry):
        return state_carry
    capability = _decode_capability_result(body.get("capability_check_result"))
    if is_refusal(capability):
        return capability
    optional_edges = _decode_binding_edges(body)
    if is_refusal(optional_edges):
        return optional_edges
    created = BookBindingRecord.try_create(
        book_instance.value,
        bms_instance.value,
        venue.value,
        account,
        World.LIVE,
        book_fp.value,
        bms_fp.value,
        state_carry.value,
        capability.value,
        carries_ledger_edge=optional_edges.value[0],
        continues_performance_edge=optional_edges.value[1],
        pairing_record=optional_edges.value[2],
        supersedes=optional_edges.value[3],
    )
    if is_refusal(created):
        return created
    canonical = created.value.fp1_identity()
    offered_fp = fingerprint(dict(body))
    if is_refusal(offered_fp):
        return offered_fp
    canonical_fp = fingerprint(canonical)
    if is_refusal(canonical_fp):
        return canonical_fp
    if offered_fp.value != canonical_fp.value:
        return policy(
            "ct28_fp1",
            "the registry CT-28 body contains only canonical typed binding identity fields",
            failure_id="configured_runtime.binding_mismatch",
        )
    return created


def _decode_capability_result(value: object) -> Result[CapabilityCheckResult]:
    if not isinstance(value, Mapping):
        return invalid("capability_check_result", "CT-28 capability evidence is a mapping")
    body = cast("Mapping[str, object]", value)
    if body.get("class") != "capability-check-result":
        return invalid(
            "capability_check_result", "CT-28 cites the canonical capability-check result"
        )
    try:
        position_model = PositionModel(body.get("position_model"))
    except (TypeError, ValueError):
        return invalid("capability_check_result.position_model", "position model is recognized")
    settlement = clean_token(body.get("settlement_currency"))
    capabilities = _string_set(body.get("satisfied_capabilities"), "satisfied_capabilities")
    baselines = _string_set(body.get("satisfied_sensor_baselines"), "satisfied_sensor_baselines")
    if is_refusal(capabilities):
        return capabilities
    if is_refusal(baselines):
        return baselines
    signature = body.get("shared_flatten_signature")
    if signature is not None and clean_token(signature) is None:
        return invalid("shared_flatten_signature", "signature is absent or a nonblank string")
    live_rung = body.get("live_path_rung_baseline_present")
    rank = body.get("rank_table_non_contradicted")
    if settlement is None or type(live_rung) is not bool or type(rank) is not bool:
        return invalid(
            "capability_check_result",
            "settlement and both bind-time check results have their exact types",
        )
    if body.get("format_version") != 1:
        return invalid("capability_check_result.format_version", "format version is 1")
    return Ok(
        CapabilityCheckResult(
            position_model=position_model,
            settlement_currency=settlement,
            satisfied_capabilities=capabilities.value,
            shared_flatten_signature=cast("str | None", signature),
            satisfied_sensor_baselines=baselines.value,
            live_path_rung_baseline_present=live_rung,
            rank_table_non_contradicted=rank,
        )
    )


def _decode_binding_edges(
    body: Mapping[str, object],
) -> Result[
    tuple[
        SignedLedgerEdge | None,
        ContinuesPerformanceEdge | None,
        PairingRecord | None,
        Fingerprint | None,
    ]
]:
    carries: SignedLedgerEdge | None = None
    continues: ContinuesPerformanceEdge | None = None
    pairing: PairingRecord | None = None
    supersedes: Fingerprint | None = None
    if "carries_ledger_edge" in body:
        edge = body["carries_ledger_edge"]
        if not isinstance(edge, Mapping):
            return invalid("carries_ledger_edge", "lineage edge is a mapping")
        edge_body = cast("Mapping[str, object]", edge)
        instant_raw = edge_body.get("signed_at")
        if (
            edge_body.get("class") != "binding-lineage-edge"
            or edge_body.get("kind") != BindingLineageEdgeKind.CARRIES_LEDGER.value
            or not isinstance(instant_raw, Mapping)
            or edge_body.get("format_version") != 1
        ):
            return invalid("carries_ledger_edge", "edge carries canonical signed-edge identity")
        instant_body = cast("Mapping[str, object]", instant_raw)
        if (
            instant_body.get("class") != "instant"
            or type(instant_body.get("value_ns")) is not int
            or instant_body.get("format_version") != 1
        ):
            return invalid("carries_ledger_edge.signed_at", "signed_at is a canonical Instant")
        instant = Instant.try_create(instant_body.get("value_ns"))
        if is_refusal(instant):
            return instant
        previous = Fingerprint.try_create(edge_body.get("from_binding_fingerprint"))
        if is_refusal(previous):
            return previous
        parsed = SignedLedgerEdge.try_create(
            edge_body.get("signer_identity"), instant.value, previous.value
        )
        if is_refusal(parsed):
            return parsed
        carries = parsed.value
    if "continues_performance_edge" in body:
        edge = body["continues_performance_edge"]
        if not isinstance(edge, Mapping):
            return invalid("continues_performance_edge", "lineage edge is a mapping")
        edge_body = cast("Mapping[str, object]", edge)
        if (
            edge_body.get("class") != "binding-lineage-edge"
            or edge_body.get("kind") != BindingLineageEdgeKind.CONTINUES_PERFORMANCE.value
            or edge_body.get("format_version") != 1
        ):
            return invalid(
                "continues_performance_edge", "edge carries canonical continuation identity"
            )
        previous = Fingerprint.try_create(edge_body.get("from_binding_fingerprint"))
        if is_refusal(previous):
            return previous
        parsed = ContinuesPerformanceEdge.try_create(previous.value)
        if is_refusal(parsed):
            return parsed
        continues = parsed.value
    if "pairing_record" in body:
        pair = body["pairing_record"]
        if not isinstance(pair, Mapping):
            return invalid("pairing_record", "pairing evidence is a mapping")
        pair_body = cast("Mapping[str, object]", pair)
        if (
            pair_body.get("class") != "binding-pairing-record"
            or pair_body.get("format_version") != 1
        ):
            return invalid("pairing_record", "pairing evidence has canonical identity")
        live = _bms_id(pair_body.get("live_bms_instance_id"))
        paired = _bms_id(pair_body.get("paired_bms_instance_id"))
        if is_refusal(live):
            return live
        if is_refusal(paired):
            return paired
        parsed_pair = PairingRecord.try_create(
            live.value, paired.value, pair_body.get("paired_account_id")
        )
        if is_refusal(parsed_pair):
            return parsed_pair
        pairing = parsed_pair.value
    if "supersedes" in body:
        prior = Fingerprint.try_create(body["supersedes"])
        if is_refusal(prior):
            return prior
        supersedes = prior.value
    return Ok((carries, continues, pairing, supersedes))


def _bms_id(value: object) -> Result[BmsInstanceId]:
    token = clean_token(value)
    if token is None:
        return invalid("bms_instance_id", "BMS instance reference is nonblank")
    return Ok(BmsInstanceId(token))


def _string_set(value: object, field: str) -> Result[frozenset[str]]:
    if not isinstance(value, (list, tuple)):
        return invalid(field, "identity set is a sequence of tokens")
    items = cast("list[object] | tuple[object, ...]", value)
    output: set[str] = set()
    for item in items:
        token = clean_token(item)
        if token is None:
            return invalid(field, "identity set contains only nonblank tokens")
        output.add(token)
    if len(output) != len(items):
        return invalid(field, "identity set contains no duplicate tokens")
    return Ok(frozenset(output))


def _absolute_path(value: object, field: str) -> Result[Path]:
    if not isinstance(value, (str, Path)):
        return invalid(field, f"{field} is an absolute filesystem path")
    path = Path(value)
    if not path.is_absolute():
        return invalid(field, f"{field} is an absolute filesystem path")
    return Ok(path)


def _read_deployment_no_follow(root: Path, relative_path: Path) -> bytes:
    """Read a bounded deployment file through a no-follow descriptor chain."""
    if (
        not relative_path.parts
        or relative_path.is_absolute()
        or any(part in {"", ".", ".."} for part in relative_path.parts)
    ):
        raise ValueError("deployment path is not a normalized relative path")
    if os.name == "nt":
        return read_deployment(root, relative_path, limit=_MAX_DEPLOYMENT_BYTES)
    if _O_NOFOLLOW == 0 or _O_DIRECTORY == 0 or os.open not in os.supports_dir_fd:
        raise OSError("descriptor-relative no-follow reads are unavailable")
    directory_fd = os.open("/", os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW)
    leaf_fd: int | None = None
    try:
        for part in root.parts[1:]:
            next_fd = _open_directory_component(part, directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        for part in relative_path.parts[:-1]:
            next_fd = _open_directory_component(part, directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        leaf_fd = os.open(
            relative_path.parts[-1],
            os.O_RDONLY | _O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
            dir_fd=directory_fd,
        )
        info = os.fstat(leaf_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_DEPLOYMENT_BYTES:
            raise OSError("deployment file is not a regular file under 1 MiB")
        data = bytearray()
        while len(data) <= _MAX_DEPLOYMENT_BYTES:
            chunk = os.read(leaf_fd, min(65536, _MAX_DEPLOYMENT_BYTES + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if len(data) > _MAX_DEPLOYMENT_BYTES:
            raise OSError("deployment file exceeds 1 MiB")
        return bytes(data)
    finally:
        try:
            if leaf_fd is not None:
                os.close(leaf_fd)
        finally:
            os.close(directory_fd)


def _open_directory_component(name: str, parent_fd: int) -> int:
    fd = os.open(
        name,
        os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW,
        dir_fd=parent_fd,
    )
    try:
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("deployment path component is not a directory")
    except BaseException:
        os.close(fd)
        raise
    return fd


def _mapping(
    value: object,
    field: str,
    allowed: frozenset[str],
) -> Result[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return invalid(field, f"{field} is an object with pinned fields")
    body = cast("Mapping[str, object]", value)
    unknown = set(body) - allowed
    if unknown:
        return invalid(field, f"{field} has no unknown fields", unknown=sorted(unknown))
    return Ok(MappingProxyType(dict(body)))


def _freeze_json_mapping(value: object, field: str) -> Result[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return invalid(field, "profile descriptor is a JSON object")
    frozen = _freeze_json_value(cast("Mapping[object, object]", value), field)
    if is_refusal(frozen):
        return frozen
    return Ok(cast("Mapping[str, object]", frozen.value))


def _freeze_json_value(value: object, field: str) -> Result[object]:
    if value is None or type(value) in {str, int, bool}:
        return Ok(value)
    if type(value) is float:
        return (
            Ok(value)
            if math.isfinite(value)
            else invalid(field, "profile numbers are finite JSON values")
        )
    if isinstance(value, Mapping):
        frozen: dict[str, object] = {}
        for key, item in cast("Mapping[object, object]", value).items():
            if type(key) is not str:
                return invalid(field, "profile object keys are strings")
            child = _freeze_json_value(item, field)
            if is_refusal(child):
                return child
            frozen[key] = child.value
        return Ok(MappingProxyType(frozen))
    if isinstance(value, list):
        values: list[object] = []
        for item in cast("list[object]", value):
            child = _freeze_json_value(item, field)
            if is_refusal(child):
                return child
            values.append(child.value)
        return Ok(tuple(values))
    return invalid(field, "profile descriptor contains only JSON values")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the same filesystem/registry preflight used by supervised startup.

    This DevOps diagnostic reports preflight only. A valid document is not
    activation, admission, provider readiness, or permission to connect.
    """
    parser = argparse.ArgumentParser(description="QMN configured-runtime preflight only")
    parser.add_argument("--deployment", required=True)
    parser.add_argument("--qmx-root", required=True)
    args = parser.parse_args(argv)
    assessed = assess_configured_runtime(args.deployment, qmx_root=args.qmx_root)
    if is_refusal(assessed):
        print(
            json.dumps(
                {
                    "status": "refused",
                    "reason": dict(assessed.context),
                    "provider_calls": 0,
                    "activation_performed": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    value = assessed.value
    print(
        json.dumps(
            {
                "activation_authorized": value.activation_authorized,
                "descriptor_digest": value.descriptor_digest,
                "machine": value.machine,
                "provider_calls": 0,
                "provider_ready": value.provider_ready,
                "stand_down": value.stand_down,
                "stand_down_reason": value.stand_down_reason,
                "status": "preflight_valid_not_activated",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
