"""Private CT-13 witnesses binding a delegated QMA invocation to one QMB terminal.

The witness is not a new public contract or result artifact. It is an immutable
data-quality row in the operator-selected replay journal, written only after the
domain terminal has been reopened and validated.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Literal, cast

from qmf.core import (
    Fingerprint,
    Instant,
    Ok,
    RefusalCategory,
    Result,
    World,
    WriterId,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.data.journal import JournalEvent, JournalEventType
from qmf.data.journal_producer import JournalAppendReceipt, JournalReader, JournalWriter
from qmf.data.store import JournalStore, RoomRole, StoreReceipt

from qmb._refuse import invalid, policy, unavailable
from qmb.host.qma_cli import QmaBacktestContext

__all__ = [
    "OPERATOR_OCCURRENCE_KIND",
    "OperatorOccurrenceIdentity",
    "OperatorOccurrenceReceipt",
    "read_operator_occurrence",
    "record_operator_occurrence",
]

OPERATOR_OCCURRENCE_KIND = "qmb-operator-terminal-occurrence-v1"
_OCCURRENCE_MISSING_REASON = "no durable invocation-to-terminal witness exists yet"
_EMPTY_MAPPING: Mapping[str, object] = {}
_MAPPING_PROXY_TYPE = type(MappingProxyType(_EMPTY_MAPPING))


def _writer_body(writer: WriterId | None) -> dict[str, object] | None:
    if writer is None:
        return None
    return {
        "boot_epoch_id": writer.boot_epoch_id,
        "machine": writer.machine,
        "role": writer.role,
        "stream": writer.stream,
    }


@dataclass(frozen=True, slots=True)
class OperatorOccurrenceIdentity:
    """Exact delegated context and checked terminal identity for one QMB operation."""

    composition_class: Literal["book", "alternative"]
    context: Mapping[str, object]
    runtime_descriptor_fp1: Fingerprint
    operator_binding_fp1: Fingerprint
    terminal_fp1: Fingerprint
    domain_result_fp1: Fingerprint | None
    at: Instant
    terminal_root: str
    journal_root: str
    terminal_writer: WriterId | None
    journal_writer: WriterId | None
    journal_stream: str | None
    command_owner_epoch: int | None
    binding_epoch_fp1: Fingerprint | None
    fingerprint: Fingerprint
    occurrence_key_fp1: Fingerprint

    def identity(self) -> dict[str, object]:
        """Return the frozen identity content for the checked CT-13 witness."""
        body: dict[str, object] = {
            "class": OPERATOR_OCCURRENCE_KIND,
            "composition_class": self.composition_class,
            "context": dict(self.context),
            "runtime_descriptor_fp1": self.runtime_descriptor_fp1.value,
            "operator_binding_fp1": self.operator_binding_fp1.value,
            "terminal_fp1": self.terminal_fp1.value,
            "at_ns": self.at.value_ns,
            "terminal_root": self.terminal_root,
            "journal_root": self.journal_root,
        }
        if self.domain_result_fp1 is not None:
            body["domain_result_fp1"] = self.domain_result_fp1.value
        if self.terminal_writer is not None:
            body["terminal_writer"] = _writer_body(self.terminal_writer)
        if self.journal_writer is not None:
            body["journal_writer"] = _writer_body(self.journal_writer)
            body["journal_stream"] = self.journal_stream
        if self.command_owner_epoch is not None:
            body["command_owner_epoch"] = self.command_owner_epoch
        if self.binding_epoch_fp1 is not None:
            body["binding_epoch_fp1"] = self.binding_epoch_fp1.value
        return body

    @classmethod
    def try_create(
        cls,
        *,
        context: object,
        composition_class: object,
        runtime_descriptor_fp1: object,
        operator_binding_fp1: object,
        terminal_fp1: object,
        at: object,
        domain_result_fp1: object = None,
        terminal_root: object,
        journal_root: object,
        terminal_writer: object = None,
        journal_writer: object = None,
        journal_stream: object = None,
        command_owner_epoch: object = None,
        binding_epoch_fp1: object = None,
    ) -> Result[OperatorOccurrenceIdentity]:
        if type(context) is not QmaBacktestContext or not _valid_context(context):
            return invalid("qma_context", "operator occurrence uses decoded QMA context")
        if not isinstance(composition_class, str) or composition_class not in {
            "book",
            "alternative",
        }:
            return invalid(
                "composition_class", "operator occurrence identifies Book or Alternative"
            )
        expected_mode = composition_class == "book"
        if type(context.mints_ct32) is not bool or context.mints_ct32 is not expected_mode:
            return policy("mints_ct32", "QMA result mode matches the selected composition")
        if (
            type(context.job_id) is not str
            or not context.job_id.strip()
            or type(context.attempt_id) is not int
            or context.attempt_id < 1
            or type(context.environment_ref) is not str
            or not context.environment_ref.strip()
            or type(context.occupancy_key) is not str
            or not context.occupancy_key.strip()
            or type(context.experiment_spec_fp1) is not Fingerprint
            or type(context.evidence_ref) is not Fingerprint
            or type(context.split_manifest_fp1) is not Fingerprint
            or not all(
                _valid_fingerprint(item)
                for item in (
                    context.experiment_spec_fp1,
                    context.evidence_ref,
                    context.split_manifest_fp1,
                )
            )
        ):
            return invalid(
                "qma_context", "delegated job, attempt, environment, and occupancy are typed"
            )
        descriptor = _fingerprint(runtime_descriptor_fp1, "runtime_descriptor_fp1")
        binding = _fingerprint(operator_binding_fp1, "operator_binding_fp1")
        terminal = _fingerprint(terminal_fp1, "terminal_fp1")
        if is_refusal(descriptor):
            return descriptor
        if is_refusal(binding):
            return binding
        if is_refusal(terminal):
            return terminal
        if type(at) is not Instant or not _valid_instant(at):
            return invalid("at", "occurrence time is a valid typed Instant")
        if (
            context.operator_descriptor_fp1 is None
            or context.operator_descriptor_fp1 != descriptor.value
        ):
            return policy(
                "runtime_descriptor_fp1", "QMA context pins the selected runtime descriptor"
            )
        domain_result: Fingerprint | None = None
        if domain_result_fp1 is not None:
            parsed_result = _fingerprint(domain_result_fp1, "domain_result_fp1")
            if is_refusal(parsed_result):
                return parsed_result
            domain_result = parsed_result.value
        if not isinstance(terminal_root, Path) or not terminal_root.is_absolute():
            return invalid("terminal_root", "operator occurrence is rooted at an absolute path")
        if not isinstance(journal_root, Path) or not journal_root.is_absolute():
            return invalid("journal_root", "CT-13 occurrence is rooted at an absolute path")
        terminal_real = str(terminal_root.resolve())
        journal_real = str(journal_root.resolve())
        if terminal_writer is not None and not _valid_writer(terminal_writer):
            return invalid("terminal_writer", "terminal writer is a typed WriterId or absent")
        if journal_writer is not None and not _valid_writer(journal_writer):
            return invalid("journal_writer", "journal writer is a typed WriterId or absent")
        if journal_stream is not None and (
            not isinstance(journal_stream, str) or not journal_stream.strip()
        ):
            return invalid("journal_stream", "journal stream is a non-empty token or absent")
        if (journal_writer is None) != (journal_stream is None):
            return invalid("journal_writer", "journal writer and stream are pinned together")
        if journal_writer is not None and cast(WriterId, journal_writer).stream != journal_stream:
            return policy("journal_stream", "journal stream belongs to its pinned WriterId")
        if command_owner_epoch is not None and (
            type(command_owner_epoch) is not int or command_owner_epoch < 0
        ):
            return invalid("command_owner_epoch", "owner epoch is a nonnegative exact integer")
        binding_epoch: Fingerprint | None = None
        if binding_epoch_fp1 is not None:
            parsed_epoch = _fingerprint(binding_epoch_fp1, "binding_epoch_fp1")
            if is_refusal(parsed_epoch):
                return parsed_epoch
            binding_epoch = parsed_epoch.value
        if command_owner_epoch is None and binding_epoch is None:
            return invalid("epoch", "operator occurrence pins a command or binding epoch")
        context_body = _context_body(context)
        identity: dict[str, object] = {
            "class": OPERATOR_OCCURRENCE_KIND,
            "composition_class": composition_class,
            "context": context_body,
            "runtime_descriptor_fp1": descriptor.value.value,
            "operator_binding_fp1": binding.value.value,
            "terminal_fp1": terminal.value.value,
            "at_ns": at.value_ns,
            "terminal_root": terminal_real,
            "journal_root": journal_real,
        }
        if domain_result is not None:
            identity["domain_result_fp1"] = domain_result.value
        if terminal_writer is not None:
            identity["terminal_writer"] = _writer_body(cast(WriterId, terminal_writer))
        if journal_writer is not None:
            identity["journal_writer"] = _writer_body(cast(WriterId, journal_writer))
            identity["journal_stream"] = cast(str, journal_stream)
        if command_owner_epoch is not None:
            identity["command_owner_epoch"] = command_owner_epoch
        if binding_epoch is not None:
            identity["binding_epoch_fp1"] = binding_epoch.value
        stamped = fingerprint(identity)
        key_fp = fingerprint(
            {
                "class": "qmb-operator-occurrence-key-v1",
                "composition_class": composition_class,
                "job_id": context.job_id,
                "attempt_id": context.attempt_id,
                "experiment_spec_fp1": context.experiment_spec_fp1.value,
                "evidence_ref": context.evidence_ref.value,
                "runtime_descriptor_fp1": descriptor.value.value,
            }
        )
        if is_refusal(stamped):
            return stamped
        if is_refusal(key_fp):
            return key_fp
        return Ok(
            cls(
                cast(Literal["book", "alternative"], composition_class),
                MappingProxyType(context_body),
                descriptor.value,
                binding.value,
                terminal.value,
                domain_result,
                at,
                terminal_real,
                journal_real,
                cast(WriterId | None, terminal_writer),
                cast(WriterId | None, journal_writer),
                journal_stream,
                command_owner_epoch,
                binding_epoch,
                stamped.value,
                key_fp.value,
            )
        )


@dataclass(frozen=True, slots=True)
class OperatorOccurrenceReceipt:
    """Exact checked CT-13 event plus physical JSONL position."""

    identity: OperatorOccurrenceIdentity
    event: JournalEvent
    physical_sequence: int
    store_fingerprint: Fingerprint


def record_operator_occurrence(
    *,
    identity: OperatorOccurrenceIdentity,
    journal_writer: JournalWriter,
    journal_store: JournalStore,
    at: Instant,
) -> Result[OperatorOccurrenceReceipt]:
    """Append the immutable invocation-to-terminal witness and check physical readback."""
    if type(identity) is not OperatorOccurrenceIdentity or not _identity_is_valid(identity):
        return invalid("occurrence", "operator occurrence uses its typed identity")
    if (
        type(journal_writer) is not JournalWriter
        or type(journal_store) is not JournalStore
        or journal_store.world is not World.REPLAY
        or journal_writer.world is not World.REPLAY
        or type(at) is not Instant
        or at != identity.at
    ):
        return invalid(
            "journal", "operator occurrence uses a replay CT-13 writer, room, and instant"
        )
    if (
        journal_writer.writer != identity.journal_writer
        or journal_writer.stream_name != identity.journal_stream
    ):
        return policy("journal_writer", "CT-13 writer matches the bound occurrence identity")
    existing = read_operator_occurrence(
        identity=identity,
        journal_reader=JournalReader(journal_store),
        missing_ok=True,
    )
    if is_ok(existing):
        return existing
    if (
        existing.category is not RefusalCategory.UNAVAILABLE_DEPENDENCY
        or existing.context.get("field") != "operator_occurrence"
        or existing.context.get("reason") != _OCCURRENCE_MISSING_REASON
    ):
        return existing
    expected_sequence = journal_writer.next_sequence
    payload = _witness_payload(identity)
    appended = journal_writer.record_data_quality(
        payload,
        instant=at,
        correlation_id=identity.occurrence_key_fp1.value,
    )
    if is_refusal(appended):
        return appended
    if type(appended.value) is not JournalAppendReceipt:
        return policy("occurrence_receipt", "CT-13 append returns the typed receipt")
    receipt = appended.value
    if type(receipt.event) is not JournalEvent or type(receipt.store_receipt) is not StoreReceipt:
        return policy("occurrence_receipt", "CT-13 receipt contains typed event and store receipt")
    event = receipt.event
    store = receipt.store_receipt
    if (
        type(event.event_type) is not JournalEventType
        or event.event_type is not JournalEventType.DATA_QUALITY
        or type(event.writer) is not WriterId
        or type(event.instant) is not Instant
        or event.world is not World.REPLAY
        or type(event.sequence) is not int
        or event.sequence != expected_sequence
        or type(event.fingerprint) is not Fingerprint
        or not isinstance(cast(object, event.payload), Mapping)
        or event.outcome is not None
        or type(receipt.edge_receipts) is not tuple
        or receipt.edge_receipts
    ):
        return policy("occurrence_receipt", "CT-13 event fields validate before identity access")
    if (
        type(store.fingerprint) is not Fingerprint
        or type(store.world) is not World
        or type(store.room_role) is not RoomRole
        or type(store.engine) is not str
        or type(store.sequence) is not int
        or store.sequence < 0
        or type(store.is_evidence_bearing) is not bool
        or type(store.retained_forever) is not bool
        or type(store.format_version) is not int
        or store.engine != "jsonl"
        or store.world is not World.REPLAY
        or store.room_role is not RoomRole.JOURNAL
        or store.is_evidence_bearing is not True
        or store.retained_forever is not True
        or store.format_version != 1
    ):
        return policy("occurrence_receipt", "CT-13 store receipt is the retained replay journal")
    event_fp = fingerprint(event.fp1_identity())
    if is_refusal(event_fp):
        return event_fp
    if (
        event_fp.value != event.fingerprint
        or event.writer != journal_writer.writer
        or event.instant != at
        or not _same(event.payload, payload)
    ):
        return policy("occurrence_receipt", "CT-13 receipt matches the exact occurrence witness")
    rows = journal_store.read_stream(journal_writer.stream_name, for_world=World.REPLAY)
    if is_refusal(rows):
        return rows
    if store.sequence >= len(rows.value):
        return policy("occurrence_receipt", "physical receipt indexes its durable journal row")
    raw = rows.value[store.sequence]
    raw_fp = fingerprint(raw)
    if is_refusal(raw_fp) or raw_fp.value != store.fingerprint:
        return policy("occurrence_receipt", "store fingerprint matches the physical journal row")
    raw_event = JournalEvent.from_row(raw)
    if is_refusal(raw_event) or raw_event.value.to_row() != event.to_row():
        return policy("occurrence_receipt", "physical journal row is the exact typed witness")
    checked = read_operator_occurrence(
        identity=identity,
        journal_reader=JournalReader(journal_store),
    )
    if is_refusal(checked):
        return checked
    if checked.value.event.to_row() != event.to_row():
        return policy("occurrence_readback", "one exact occurrence event reads back")
    return checked


def read_operator_occurrence(
    *,
    identity: OperatorOccurrenceIdentity,
    journal_reader: JournalReader,
    missing_ok: bool = False,
) -> Result[OperatorOccurrenceReceipt]:
    """Resolve exactly one durable witness for the complete expected occurrence."""
    if (
        type(identity) is not OperatorOccurrenceIdentity
        or not _identity_is_valid(identity)
        or type(journal_reader) is not JournalReader
    ):
        return invalid("occurrence", "readback uses typed occurrence identity and JournalReader")
    if (
        journal_reader.journal.world is not World.REPLAY
        or identity.journal_writer is None
        or identity.journal_stream is None
    ):
        return invalid("journal", "occurrence readback pins a replay CT-13 writer and stream")
    checked = journal_reader.read_checked(identity.journal_stream, for_world=World.REPLAY)
    if is_refusal(checked):
        return checked
    candidates = tuple(
        event for event in checked.value if _could_be_same_occurrence(event, identity)
    )
    if not candidates:
        if missing_ok:
            return unavailable(
                "operator_occurrence",
                _OCCURRENCE_MISSING_REASON,
            )
        return unavailable(
            "operator_occurrence",
            "the delegated invocation has one durable terminal witness",
        )
    if len(candidates) != 1:
        return policy(
            "operator_occurrence",
            "one invocation key has exactly one durable terminal witness",
            matches=len(candidates),
        )
    event = candidates[0]
    payload = _witness_payload(identity)
    if (
        type(event) is not JournalEvent
        or event.event_type is not JournalEventType.DATA_QUALITY
        or event.writer != identity.journal_writer
        or event.world is not World.REPLAY
        or event.instant != identity.at
        or event.outcome is not None
        or not _same(event.payload, payload)
        or event.correlation_id != identity.occurrence_key_fp1.value
    ):
        return policy(
            "operator_occurrence", "stored witness exactly matches trusted occurrence inputs"
        )
    raw_rows = journal_reader.journal.read_stream(identity.journal_stream, for_world=World.REPLAY)
    if is_refusal(raw_rows):
        return raw_rows
    physical_matches: list[tuple[int, Mapping[str, object], Fingerprint]] = []
    for index, raw in enumerate(raw_rows.value):
        raw_event = JournalEvent.from_row(raw)
        if is_refusal(raw_event):
            return raw_event
        if (
            raw_event.value.fingerprint == event.fingerprint
            and raw_event.value.writer == event.writer
        ):
            raw_fp = fingerprint(raw)
            if is_refusal(raw_fp):
                return raw_fp
            physical_matches.append((index, raw, raw_fp.value))
    if len(physical_matches) != 1:
        return policy("operator_occurrence", "witness resolves to one physical journal row")
    physical_sequence, raw_row, store_fp = physical_matches[0]
    if raw_row != event.to_row():
        return policy("operator_occurrence", "physical row matches the checked event exactly")
    stamped = fingerprint(event.fp1_identity())
    if is_refusal(stamped) or stamped.value != event.fingerprint:
        return policy("operator_occurrence", "witness event fingerprint matches its typed body")
    return Ok(OperatorOccurrenceReceipt(identity, event, physical_sequence, store_fp))


def _witness_payload(identity: OperatorOccurrenceIdentity) -> dict[str, object]:
    return {
        "class": "qmb-ct13-data-quality-v1",
        "component": "COMP-QMB",
        "contract": "CT-13",
        "event_type_wire": JournalEventType.DATA_QUALITY.value,
        "kind": OPERATOR_OCCURRENCE_KIND,
        "identity": identity.identity(),
        "identity_fp1": identity.fingerprint.value,
        "occurrence_key_fp1": identity.occurrence_key_fp1.value,
        "is_edge_claim": False,
        "fills_gaps": False,
    }


def _context_body(context: QmaBacktestContext) -> dict[str, object]:
    return {
        "job_id": context.job_id,
        "attempt_id": context.attempt_id,
        "experiment_spec_fp1": context.experiment_spec_fp1.value,
        "evidence_ref": context.evidence_ref.value,
        "split_manifest_fp1": context.split_manifest_fp1.value,
        "environment_ref": context.environment_ref,
        "occupancy_key": context.occupancy_key,
        "mints_ct32": context.mints_ct32,
        "operator_descriptor_fp1": (
            None
            if context.operator_descriptor_fp1 is None
            else context.operator_descriptor_fp1.value
        ),
    }


def _fingerprint(value: object, field: str) -> Result[Fingerprint]:
    parsed = Fingerprint.try_create(value.value if isinstance(value, Fingerprint) else value)
    if is_refusal(parsed):
        return invalid(field, "operator occurrence references carry a valid fp1")
    return parsed


def _same(left: object, right: object) -> bool:
    left_fp = fingerprint(left)
    right_fp = fingerprint(right)
    return not is_refusal(left_fp) and not is_refusal(right_fp) and left_fp.value == right_fp.value


def _valid_writer(value: object) -> bool:
    if type(value) is not WriterId:
        return False
    parsed = WriterId.try_create(value.machine, value.role, value.stream, value.boot_epoch_id)
    return not is_refusal(parsed) and parsed.value == value


def _valid_instant(value: Instant) -> bool:
    parsed = Instant.try_create(value.value_ns)
    return not is_refusal(parsed) and parsed.value == value


def _valid_context(context: object) -> bool:
    if type(context) is not QmaBacktestContext:
        return False
    return (
        type(context.job_id) is str
        and bool(context.job_id.strip())
        and type(context.attempt_id) is int
        and context.attempt_id > 0
        and _valid_fingerprint(context.experiment_spec_fp1)
        and _valid_fingerprint(context.evidence_ref)
        and _valid_fingerprint(context.split_manifest_fp1)
        and type(context.environment_ref) is str
        and bool(context.environment_ref.strip())
        and type(context.occupancy_key) is str
        and bool(context.occupancy_key.strip())
        and type(context.mints_ct32) is bool
        and (
            context.operator_descriptor_fp1 is None
            or _valid_fingerprint(context.operator_descriptor_fp1)
        )
    )


def _could_be_same_occurrence(event: JournalEvent, identity: OperatorOccurrenceIdentity) -> bool:
    payload_object: object = cast(object, event.payload)
    if (
        type(event) is not JournalEvent
        or event.event_type is not JournalEventType.DATA_QUALITY
        or not isinstance(payload_object, Mapping)
    ):
        return False
    payload = cast(Mapping[str, object], payload_object)
    if payload.get("kind") != OPERATOR_OCCURRENCE_KIND:
        return False
    if payload.get("occurrence_key_fp1") == identity.occurrence_key_fp1.value:
        return True
    body_object = payload.get("identity")
    if not isinstance(body_object, Mapping):
        return True
    body = cast(Mapping[str, object], body_object)
    context_object = body.get("context")
    if not isinstance(context_object, Mapping):
        return True
    context = cast(Mapping[str, object], context_object)
    core_fields = ("job_id", "attempt_id", "experiment_spec_fp1", "evidence_ref")
    if (
        any(field not in context for field in core_fields)
        or type(context.get("job_id")) is not str
        or type(context.get("attempt_id")) is not int
        or type(context.get("experiment_spec_fp1")) is not str
        or type(context.get("evidence_ref")) is not str
    ):
        return True
    return all(
        context.get(field) == identity.context.get(field)
        for field in ("job_id", "attempt_id", "experiment_spec_fp1", "evidence_ref")
    )


def _valid_fingerprint(value: object) -> bool:
    if type(value) is not Fingerprint:
        return False
    parsed = Fingerprint.try_create(value.value)
    return not is_refusal(parsed) and parsed.value == value


def _valid_context_body(identity: OperatorOccurrenceIdentity) -> bool:
    context = identity.context
    expected_keys = {
        "job_id",
        "attempt_id",
        "experiment_spec_fp1",
        "evidence_ref",
        "split_manifest_fp1",
        "environment_ref",
        "occupancy_key",
        "mints_ct32",
        "operator_descriptor_fp1",
    }
    context_value: object = cast(object, context)
    if type(context_value) is not _MAPPING_PROXY_TYPE:
        return False
    context = cast(Mapping[str, object], context_value)
    if set(context.keys()) != expected_keys:
        return False
    mode = identity.composition_class == "book"
    return (
        identity.composition_class in {"book", "alternative"}
        and type(context.get("job_id")) is str
        and bool(cast(str, context.get("job_id")).strip())
        and type(context.get("attempt_id")) is int
        and cast(int, context.get("attempt_id")) > 0
        and all(
            _valid_fingerprint_value(context.get(key))
            for key in ("experiment_spec_fp1", "evidence_ref", "split_manifest_fp1")
        )
        and type(context.get("environment_ref")) is str
        and bool(cast(str, context.get("environment_ref")).strip())
        and type(context.get("occupancy_key")) is str
        and bool(cast(str, context.get("occupancy_key")).strip())
        and type(context.get("mints_ct32")) is bool
        and context.get("mints_ct32") is mode
        and type(context.get("operator_descriptor_fp1")) is str
        and context.get("operator_descriptor_fp1") == identity.runtime_descriptor_fp1.value
        and _valid_fingerprint_value(context.get("operator_descriptor_fp1"))
    )


def _valid_fingerprint_value(value: object) -> bool:
    parsed = Fingerprint.try_create(value)
    return not is_refusal(parsed) and parsed.value.value == value


def _identity_is_valid(identity: OperatorOccurrenceIdentity) -> bool:
    if (
        type(identity.composition_class) is not str
        or identity.composition_class not in {"book", "alternative"}
        or not _valid_fingerprint(identity.runtime_descriptor_fp1)
        or not _valid_fingerprint(identity.operator_binding_fp1)
        or not _valid_fingerprint(identity.terminal_fp1)
        or (
            identity.domain_result_fp1 is not None
            and not _valid_fingerprint(identity.domain_result_fp1)
        )
        or type(identity.at) is not Instant
        or not _valid_instant(identity.at)
        or type(identity.terminal_root) is not str
        or not Path(identity.terminal_root).is_absolute()
        or type(identity.journal_root) is not str
        or not Path(identity.journal_root).is_absolute()
        or (identity.terminal_writer is not None and not _valid_writer(identity.terminal_writer))
        or (identity.journal_writer is not None and not _valid_writer(identity.journal_writer))
        or (identity.journal_stream is not None and type(identity.journal_stream) is not str)
        or (identity.journal_writer is None) != (identity.journal_stream is None)
        or (
            identity.journal_writer is not None
            and identity.journal_writer.stream != identity.journal_stream
        )
        or (
            identity.command_owner_epoch is not None
            and (type(identity.command_owner_epoch) is not int or identity.command_owner_epoch < 0)
        )
        or (
            identity.binding_epoch_fp1 is not None
            and not _valid_fingerprint(identity.binding_epoch_fp1)
        )
        or (identity.command_owner_epoch is None and identity.binding_epoch_fp1 is None)
        or not _valid_fingerprint(identity.fingerprint)
        or not _valid_fingerprint(identity.occurrence_key_fp1)
    ):
        return False
    if not _valid_context_body(identity):
        return False
    body_fp = fingerprint(identity.identity())
    key_fp = fingerprint(
        {
            "class": "qmb-operator-occurrence-key-v1",
            "composition_class": identity.composition_class,
            "job_id": identity.context["job_id"],
            "attempt_id": identity.context["attempt_id"],
            "experiment_spec_fp1": identity.context["experiment_spec_fp1"],
            "evidence_ref": identity.context["evidence_ref"],
            "runtime_descriptor_fp1": identity.runtime_descriptor_fp1.value,
        }
    )
    return (
        not is_refusal(body_fp)
        and body_fp.value == identity.fingerprint
        and not is_refusal(key_fp)
        and key_fp.value == identity.occurrence_key_fp1
    )
