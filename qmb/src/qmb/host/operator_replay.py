"""Operator-owned, content-addressed runtime binding for the QMB backtest door.

QMA supplies only CT-47 identifiers. This adapter finds the matching operator
binding beneath ``QMB_REPLAY_RUNTIME_ROOT`` and verifies its policy and builder
identities before allowing the builder to materialize QMB's canonical typed
inputs. Caller payloads never choose roots, Book policy, or execution ports.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import cast

from qmf.core import Fingerprint, Instant, Ok, Result, World, WriterId, fingerprint, is_refusal
from qmf.data.journal_producer import JournalReader
from qmf.data.store import EvidenceStore
from qmf.registry import RegistrationRecord, RegistryPersistence
from qmf.registry.records import CONTRACT_FORMAT_VERSION as CT06_FORMAT_VERSION
from qmf.risk.templates import (
    BMS_CONTRACT_FORMAT_VERSION,
    BOOK_KNOWN_FORMAT_VERSIONS,
)

from qmb._refuse import invalid, policy, unavailable
from qmb.config import materialize_bms_fragment, materialize_book_fragment
from qmb.config.compiler import ResolvedRunConfig
from qmb.config.fragments import ConfigFragment
from qmb.execution.binder import BoundExecution
from qmb.host.book_handler import BookAdmissionContext
from qmb.host.qma_cli import QmaBacktestContext
from qmb.host.replay_request import ResolvedReplayRequest
from qmb.orchestrator.ledger import LedgerSink
from qmb.registryread import AsOfSet, PassiveHub, RegistryReadPort

__all__ = [
    "OPERATOR_BINDING_CONFIG_KEY",
    "OPERATOR_BINDING_FORMAT_VERSION",
    "OPERATOR_BINDING_KIND",
    "OperatorReplayBinding",
    "execute_operator_replay",
    "read_operator_replay_binding",
]

OPERATOR_BINDING_KIND = "qmb-operator-replay-binding"
OPERATOR_BINDING_FORMAT_VERSION = 1
OPERATOR_BINDING_CONFIG_KEY = "qmb_operator_replay_binding_fp1"
_BINDING_FILE = "operator-binding.json"
_BINDING_FIELDS = frozenset(
    {
        "class",
        "format_version",
        "experiment_spec_fp1",
        "evidence_ref",
        "split_manifest_fp1",
        "holdout_months",
        "record_refs",
        "roots",
        "registry_as_of_ns",
        "registry_writer",
        "registry_stale_evidence_severity",
        "policy_identity",
        "policy_fp1",
        "builder_files",
        "builder_fp1",
        "entrypoint",
        "descriptor_fp1",
    }
)
_ROOT_NAMES = frozenset({"registry", "raw", "requests", "journal", "terminal_ledger"})


@dataclass(frozen=True, slots=True)
class OperatorReplayBinding:
    """Verified operator-local runtime descriptor selected by CT-47 identifiers."""

    experiment_spec_fp1: Fingerprint
    evidence_ref: Fingerprint
    split_manifest_fp1: Fingerprint
    holdout_months: int
    record_refs: Mapping[str, Fingerprint]
    roots: Mapping[str, Path]
    registry_as_of: Instant
    registry_writer: WriterId
    registry_stale_evidence_severity: str
    policy_identity: Mapping[str, object]
    policy_fp1: Fingerprint
    builder_files: Mapping[str, str]
    builder_fp1: Fingerprint
    entrypoint: str
    descriptor_fp1: Fingerprint


def read_operator_replay_binding(
    *, runtime_root: object, context: object
) -> Result[OperatorReplayBinding]:
    """Read the one operator descriptor for this registered run and request."""
    if not isinstance(context, QmaBacktestContext):
        return invalid("qma_context", "operator binding selection consumes decoded CT-47 refs")
    root = _absolute_directory(runtime_root, "runtime_root")
    if is_refusal(root):
        return root
    spec_name = context.experiment_spec_fp1.value.replace(":", "-")
    evidence_name = context.evidence_ref.value.replace(":", "-")
    descriptor_path = root.value / spec_name / evidence_name / _BINDING_FILE
    raw = _read_json(descriptor_path)
    if is_refusal(raw):
        return raw
    return _decode_binding(raw.value, context)


def execute_operator_replay(
    *, runtime_root: object, context: object
) -> Result[Mapping[str, object]]:
    """Load the pinned operator builder and call the shared governed replay service.

    Builder files are operator-authored and content-addressed by the descriptor;
    they run only inside the already-installed QMB CLI process. Their returned
    values are checked against the registered request, run-config and Book
    identity before the production service can execute.
    """
    binding = read_operator_replay_binding(runtime_root=runtime_root, context=context)
    if is_refusal(binding):
        return binding
    selected_context = cast(QmaBacktestContext, context)
    registry = _canonical_registry(binding.value)
    if is_refusal(registry):
        return registry
    with tempfile.TemporaryDirectory(prefix="qmb-operator-replay-") as raw_root:
        builder_root = Path(raw_root)
        written = _materialize_builder(binding.value.builder_files, builder_root)
        if is_refusal(written):
            return written
        module = _load_builder(
            builder_root,
            binding.value.builder_files,
            binding.value.entrypoint,
        )
        if is_refusal(module):
            return module
        entry = _entrypoint(module.value, binding.value.entrypoint)
        if is_refusal(entry):
            return entry
        built = entry.value(selected_context, binding.value, *registry.value)
        if is_refusal(built):
            return built
        inputs = _runtime_inputs(built.value, binding.value, registry.value)
        if is_refusal(inputs):
            return inputs
        from qmb.host.replay_execution import execute_recorded_replay_request  # noqa: PLC0415

        result = execute_recorded_replay_request(
            **inputs.value,
            expected_request_ref=selected_context.evidence_ref,
            request_root=binding.value.roots["requests"],
            raw_store_root=binding.value.roots["raw"],
            holdout_months=binding.value.holdout_months,
            expected_split_fp1=selected_context.split_manifest_fp1,
            role="confirmation",
        )
        if is_refusal(result):
            return result
        ct32 = result.value.performance_result.fingerprint()
        if is_refusal(ct32):
            return ct32
        terminal_stamp = fingerprint(result.value.terminal_line.fp1_identity())
        if is_refusal(terminal_stamp):
            return terminal_stamp
        return Ok(
            {
                "ct32_fp1": ct32.value.value,
                "evidence_ref": result.value.request_ref.value,
                "run_fp1": result.value.run_fp1.value,
                "terminal_line_fp1": terminal_stamp.value.value,
            }
        )


def _decode_binding(raw: object, context: QmaBacktestContext) -> Result[OperatorReplayBinding]:
    if not isinstance(raw, Mapping):
        return invalid("operator_binding", "operator binding is one JSON object")
    body = cast(Mapping[str, object], raw)
    if set(body) != set(_BINDING_FIELDS):
        return invalid(
            "operator_binding",
            "operator binding uses the exact versioned descriptor fields",
            missing=sorted(_BINDING_FIELDS.difference(body)),
            extra=sorted(set(body).difference(_BINDING_FIELDS)),
        )
    if body.get("class") != OPERATOR_BINDING_KIND or body.get("format_version") != 1:
        return invalid("operator_binding", "operator binding has the supported v1 class")
    identity = {key: value for key, value in body.items() if key != "descriptor_fp1"}
    descriptor_fp = _parse_fp(body.get("descriptor_fp1"), "descriptor_fp1")
    if is_refusal(descriptor_fp):
        return descriptor_fp
    actual_fp = fingerprint(identity)
    if is_refusal(actual_fp):
        return actual_fp
    if actual_fp.value != descriptor_fp.value:
        return policy("descriptor_fp1", "operator binding content matches its descriptor fp1")
    for field, expected in (
        ("experiment_spec_fp1", context.experiment_spec_fp1),
        ("evidence_ref", context.evidence_ref),
        ("split_manifest_fp1", context.split_manifest_fp1),
    ):
        actual = _parse_fp(body.get(field), field)
        if is_refusal(actual):
            return actual
        if actual.value != expected:
            return policy(field, "operator binding is selected by the exact trusted CT-47 ref")
    holdout_months = body.get("holdout_months")
    if (
        isinstance(holdout_months, bool)
        or not isinstance(holdout_months, int)
        or holdout_months < 1
    ):
        return invalid("holdout_months", "operator binding explicitly pins positive holdout months")
    refs_value = body.get("record_refs")
    if not isinstance(refs_value, Mapping):
        return invalid("record_refs", "binding pins CT-33, CT-22 and CT-27 records")
    refs_raw = cast(Mapping[str, object], refs_value)
    if set(refs_raw) != {"bot", "book", "bms"}:
        return invalid("record_refs", "binding pins CT-33, CT-22 and CT-27 records")
    refs: dict[str, Fingerprint] = {}
    for key, value in refs_raw.items():
        parsed = _parse_fp(value, f"record_refs.{key}")
        if is_refusal(parsed):
            return parsed
        refs[key] = parsed.value
    roots_value = body.get("roots")
    if not isinstance(roots_value, Mapping):
        return invalid("roots", "binding names the complete operator-owned QMF roots")
    roots_raw = cast(Mapping[str, object], roots_value)
    if set(roots_raw) != set(_ROOT_NAMES):
        return invalid("roots", "binding names the complete operator-owned QMF roots")
    roots: dict[str, Path] = {}
    for key, value in roots_raw.items():
        path = _absolute_directory(value, f"roots.{key}")
        if is_refusal(path):
            return path
        roots[key] = path.value
    registry_as_of_raw = body.get("registry_as_of_ns")
    if isinstance(registry_as_of_raw, bool) or not isinstance(registry_as_of_raw, int):
        return invalid("registry_as_of_ns", "binding pins its registry read instant")
    registry_as_of = Instant.try_create(registry_as_of_raw)
    if is_refusal(registry_as_of):
        return registry_as_of
    writer_raw = body.get("registry_writer")
    if not isinstance(writer_raw, Mapping):
        return invalid("registry_writer", "binding pins the registry materializer writer")
    writer_map = cast(Mapping[str, object], writer_raw)
    registry_writer = WriterId.try_create(
        writer_map.get("actor"),
        writer_map.get("role"),
        writer_map.get("stream"),
        writer_map.get("boot_epoch"),
    )
    if is_refusal(registry_writer):
        return registry_writer
    stale_severity = body.get("registry_stale_evidence_severity")
    if not isinstance(stale_severity, str) or not stale_severity.strip():
        return invalid("registry_stale_evidence_severity", "stale evidence severity is explicit")
    policy_value = body.get("policy_identity")
    if not isinstance(policy_value, Mapping):
        return invalid("policy_identity", "binding pins an explicit complete runtime policy")
    policy_raw = cast(Mapping[str, object], policy_value)
    policy_stamp = fingerprint(policy_raw)
    if is_refusal(policy_stamp):
        return policy_stamp
    expected_policy = _parse_fp(body.get("policy_fp1"), "policy_fp1")
    if is_refusal(expected_policy):
        return expected_policy
    if policy_stamp.value != expected_policy.value:
        return policy("policy_fp1", "runtime policy bytes match their pinned fingerprint")
    files_raw = body.get("builder_files")
    if not isinstance(files_raw, Mapping) or not files_raw:
        return invalid("builder_files", "binding pins a non-empty QMB runtime builder source tree")
    files: dict[str, str] = {}
    for path, source in cast(Mapping[object, object], files_raw).items():
        if not isinstance(path, str) or not _safe_source_path(path) or not isinstance(source, str):
            return invalid("builder_files", "builder paths are safe relative .py files")
        files[path] = source
    builder_stamp = fingerprint({"class": "qmb-operator-builder-source-v1", "files": files})
    if is_refusal(builder_stamp):
        return builder_stamp
    builder_fp = _parse_fp(body.get("builder_fp1"), "builder_fp1")
    if is_refusal(builder_fp):
        return builder_fp
    if builder_stamp.value != builder_fp.value:
        return policy("builder_fp1", "operator builder bytes match their pinned fingerprint")
    entrypoint = body.get("entrypoint")
    if not isinstance(entrypoint, str) or not _valid_entrypoint(entrypoint, files):
        return invalid("entrypoint", "binding selects a declared module:function entrypoint")
    return Ok(
        OperatorReplayBinding(
            experiment_spec_fp1=context.experiment_spec_fp1,
            evidence_ref=context.evidence_ref,
            split_manifest_fp1=context.split_manifest_fp1,
            holdout_months=holdout_months,
            record_refs=refs,
            roots=roots,
            registry_as_of=registry_as_of.value,
            registry_writer=registry_writer.value,
            registry_stale_evidence_severity=stale_severity,
            policy_identity=policy_raw,
            policy_fp1=expected_policy.value,
            builder_files=files,
            builder_fp1=builder_fp.value,
            entrypoint=entrypoint,
            descriptor_fp1=descriptor_fp.value,
        )
    )


def _canonical_registry(
    binding: OperatorReplayBinding,
) -> Result[tuple[RegistryReadPort, ConfigFragment, ConfigFragment]]:
    """Resolve the three pinned CT-06 records through the canonical registry port."""
    store = EvidenceStore(binding.roots["registry"])
    persistence = RegistryPersistence.open(store, World.REPLAY)
    if is_refusal(persistence):
        return persistence
    records: list[RegistrationRecord] = []
    for key, expected_kind, expected_versions in (
        ("bot", "bot-definition", frozenset({1})),
        ("book", "book-definition", BOOK_KNOWN_FORMAT_VERSIONS),
        ("bms", "bms-definition", frozenset({BMS_CONTRACT_FORMAT_VERSION})),
    ):
        loaded = persistence.value.load_record(
            binding.record_refs[key],
            for_world=World.REPLAY,
        )
        if is_refusal(loaded):
            persistence.value.close()
            return loaded
        if (
            loaded.value.kind != expected_kind
            or loaded.value.contract_format_version not in expected_versions
            or loaded.value.format_version != CT06_FORMAT_VERSION
            or loaded.value.stable_id != binding.record_refs[key]
        ):
            persistence.value.close()
            return policy(
                "record_refs",
                "operator record ref resolves to its exact registered CT record kind",
                record=key,
                expected_kind=expected_kind,
                actual_kind=loaded.value.kind,
                expected_ct06_format=CT06_FORMAT_VERSION,
                actual_ct06_format=loaded.value.format_version,
                expected_versions=sorted(expected_versions),
                actual_version=loaded.value.contract_format_version,
            )
        if (
            loaded.value.writer is None
            or loaded.value.sequence is None
            or loaded.value.created_at is None
            or loaded.value.created_at.value_ns > binding.registry_as_of.value_ns
        ):
            persistence.value.close()
            return policy(
                "registry_occurrence",
                "as-of resolution requires persisted CT-06 occurrence facts before its instant",
                record=key,
            )
        record = RegistrationRecord.try_create(
            loaded.value.kind,
            loaded.value.contract_format_version,
            [parent.value for parent in loaded.value.at_birth_parent_refs],
            loaded.value.body,
            loaded.value.writer,
            loaded.value.sequence,
            loaded.value.created_at,
        )
        if is_refusal(record):
            persistence.value.close()
            return record
        if record.value.stable_id != binding.record_refs[key]:
            persistence.value.close()
            return policy("record_refs", "reconstructed CT-06 identity matches its registry ref")
        records.append(record.value)
    persistence.value.close()
    as_of = AsOfSet.try_create(binding.registry_as_of, records=tuple(records))
    if is_refusal(as_of):
        return as_of
    hub = PassiveHub.try_create((as_of.value,))
    if is_refusal(hub):
        return hub
    port = RegistryReadPort.try_create(
        hub.value,
        stale_evidence_severity=binding.registry_stale_evidence_severity,
    )
    if is_refusal(port):
        return port
    book_fragment = materialize_book_fragment(
        port.value,
        binding.record_refs["book"],
        binding.registry_writer,
    )
    if is_refusal(book_fragment):
        return book_fragment
    bms_fragment = materialize_bms_fragment(
        port.value,
        binding.record_refs["bms"],
        binding.registry_writer,
    )
    if is_refusal(bms_fragment):
        return bms_fragment
    return Ok((port.value, book_fragment.value, bms_fragment.value))


def _runtime_inputs(
    raw: object,
    binding: OperatorReplayBinding,
    registry: tuple[RegistryReadPort, ConfigFragment, ConfigFragment],
) -> Result[Mapping[str, object]]:
    if not isinstance(raw, Mapping):
        return invalid("operator_runtime", "builder returns the typed QMB service input mapping")
    expected_keys = {
        "request",
        "config",
        "bound_execution",
        "admission",
        "journal_reader",
        "terminal_ledger",
    }
    values = cast(Mapping[str, object], raw)
    if set(values) != expected_keys:
        return invalid("operator_runtime", "builder returns the exact service input fields")
    config = values.get("config")
    request = values.get("request")
    if not isinstance(config, ResolvedRunConfig):
        return invalid("operator_runtime", "builder returns a resolved run-config")
    if not isinstance(request, ResolvedReplayRequest):
        return invalid("operator_runtime", "builder returns a resolved persisted request")
    if not isinstance(values.get("bound_execution"), BoundExecution):
        return invalid("operator_runtime", "builder returns canonical bound execution ports")
    if not isinstance(values.get("admission"), BookAdmissionContext):
        return invalid("operator_runtime", "builder returns typed Book admission policy")
    if not isinstance(values.get("journal_reader"), JournalReader):
        return invalid("operator_runtime", "builder returns the configured QMF JournalReader")
    if not isinstance(values.get("terminal_ledger"), LedgerSink):
        return invalid("operator_runtime", "builder returns the governed terminal LedgerSink")
    actual_policy = _runtime_policy_identity(
        config,
        cast(BoundExecution, values["bound_execution"]),
        cast(BookAdmissionContext, values["admission"]),
        binding.builder_fp1,
        binding.builder_files,
    )
    if is_refusal(actual_policy):
        return actual_policy
    if dict(actual_policy.value) != dict(binding.policy_identity):
        return policy(
            "policy_identity",
            "typed execution ports exactly match the operator's pinned runtime policy",
        )
    if config.keys.get(OPERATOR_BINDING_CONFIG_KEY) != binding.descriptor_fp1.value:
        return policy(
            "operator_binding_fp1",
            "resolved run identity binds the exact operator policy and builder descriptor",
        )
    if (
        config.book_fragment_fp1 != registry[1].fingerprint
        or config.bms_fragment_fp1 != registry[2].fingerprint
    ):
        return policy(
            "config_fragments",
            "compiled run-config uses the canonical CT-22 and CT-27 registry materializers",
        )
    for key, expected in (
        ("bot", binding.record_refs["bot"]),
        ("book", binding.record_refs["book"]),
        ("bms", binding.record_refs["bms"]),
    ):
        actual = {
            "bot": config.bot_fp1,
            "book": config.book_fp1,
            "bms": config.bms_fp1,
        }[key]
        if actual != expected:
            return policy(key, "compiled run-config cites the operator-pinned CT record")
    if request.request_ref != binding.evidence_ref:
        return policy("evidence_ref", "resolved request is the evidence cited by CT-47")
    if request.split_fp1 != binding.split_manifest_fp1:
        return policy("split_manifest_fp1", "resolved request matches registered CT-12 data_ref")
    return Ok(dict(values))


def _runtime_policy_identity(
    config: ResolvedRunConfig,
    execution: BoundExecution,
    admission: BookAdmissionContext,
    builder_fp1: Fingerprint,
    builder_files: Mapping[str, str],
) -> Result[Mapping[str, object]]:
    """Derive behavior identity from typed runtime values, never builder claims."""
    calendar = _typed_identity(admission.rollover_calendar, "rollover_calendar")
    if is_refusal(calendar):
        return calendar
    calendar_source = _require_pinned_implementation(
        admission.rollover_calendar, builder_files, "rollover_calendar"
    )
    if is_refusal(calendar_source):
        return calendar_source
    exit_ref = _typed_identity(admission.exit_logic_ref, "exit_logic_ref")
    if is_refusal(exit_ref):
        return exit_ref
    exit_source = _require_pinned_implementation(
        admission.exit_logic_module, builder_files, "exit_logic_module"
    )
    if is_refusal(exit_source):
        return exit_source
    value_factor = _typed_identity(admission.value_factor, "value_factor")
    if is_refusal(value_factor):
        return value_factor
    target = _typed_identity(admission.execution_target, "execution_target")
    if is_refusal(target):
        return target
    result_label = _typed_identity(admission.result_label, "result_label")
    if is_refusal(result_label):
        return result_label
    close_reasons = {
        key: value.value for key, value in admission.close_reason_by_code.items()
    }
    order_policies = {
        key: value.fp1_identity() for key, value in admission.order_policy_by_code.items()
    }
    execution_identity = execution.fp1_identity()
    execution_identity.pop("config_fp1", None)
    config_keys = dict(config.keys)
    config_keys.pop(OPERATOR_BINDING_CONFIG_KEY, None)
    return Ok(
        {
            "class": "qmb-operator-replay-policy-v1",
            "builder_fp1": builder_fp1.value,
            "config_policy": {
                "book_fp1": config.book_fp1.value,
                "bms_fp1": config.bms_fp1.value,
                "bot_fp1": config.bot_fp1.value,
                "keys": config_keys,
            },
            "execution": execution_identity,
            "book_admission": {
                "binding_fp1": admission.binding.fingerprint.value,
                "close_reasons": close_reasons,
                "exit_logic_ref": exit_ref.value,
                "exit_logic_module_source_fp1": exit_source.value,
                "money_scale": admission.money_scale,
                "opening_bot_id": admission.opening_bot_id,
                "order_policies": order_policies,
                "position_cap": admission.position_cap.fp1_identity(),
                "protective_stop_reason": admission.protective_stop_reason.fp1_identity(),
                "requested_r": admission.requested_r.fp1_identity(),
                "result_label": result_label.value,
                "rollover_calendar": calendar.value,
                "rollover_calendar_source_fp1": calendar_source.value,
                "r_unit_price": admission.r_unit_price.fp1_identity(),
                "target": target.value,
                "value_factor": value_factor.value,
                "lot_step": admission.lot_step.fp1_identity(),
            },
        }
    )


def _typed_identity(value: object, field: str) -> Result[Mapping[str, object]]:
    identity = getattr(value, "fp1_identity", None)
    if not callable(identity):
        return invalid(field, "operator runtime policy objects expose canonical fp1 identity")
    try:
        raw = identity()
    except Exception as exc:  # operator policy object boundary
        return invalid(field, "runtime policy identity evaluates successfully", error=str(exc))
    if not isinstance(raw, Mapping):
        return invalid(field, "runtime policy fp1 identity returns a mapping")
    return Ok(cast(Mapping[str, object], raw))


def _require_pinned_implementation(
    value: object, builder_files: Mapping[str, str], field: str
) -> Result[Fingerprint]:
    try:
        source = inspect.getsource(type(value))
    except (OSError, TypeError):
        return invalid(field, "operator policy implementation has readable pinned source")
    if not any(source in content for content in builder_files.values()):
        return policy(field, "behavioral policy implementation bytes are in the pinned builder")
    return fingerprint({"class": "qmb-operator-policy-source-v1", "source": source})


def _materialize_builder(files: Mapping[str, str], root: Path) -> Result[None]:
    for relative, source in files.items():
        destination = root.joinpath(*relative.split("/"))
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        except OSError as exc:
            return unavailable(
                "operator_builder",
                "operator builder source cannot be materialized",
                error=str(exc),
            )
    return Ok(None)


def _load_builder(root: Path, files: Mapping[str, str], entrypoint: str) -> Result[ModuleType]:
    module_name, _attribute = entrypoint.split(":", 1)
    relative = module_name.replace(".", "/") + ".py"
    if relative not in files:
        relative = module_name.replace(".", "/") + "/__init__.py"
    path = root / relative
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return invalid("entrypoint", "operator builder module is loadable from its pinned files")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(root))
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # operator-authored builder boundary
        return policy("operator_builder", "pinned runtime builder imports cleanly", error=str(exc))
    finally:
        sys.path.pop(0)
    return Ok(module)


def _entrypoint(
    module: ModuleType, entrypoint: str
) -> Result[Callable[..., Result[object]]]:
    _module_name, attribute = entrypoint.split(":", 1)
    value = getattr(module, attribute, None)
    if not callable(value):
        return invalid("entrypoint", "operator builder entrypoint is callable")
    return Ok(cast(Callable[..., Result[object]], value))


def _read_json(path: Path) -> Result[object]:
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            raw = stream.read(8 * 1024 * 1024 + 1)
    except FileNotFoundError:
        return unavailable("operator_binding", "no operator binding is registered for these refs")
    except OSError as exc:
        return unavailable("operator_binding", "operator descriptor cannot be read", error=str(exc))
    if len(raw) > 8 * 1024 * 1024:
        return invalid("operator_binding", "operator descriptor stays within the bounded file size")
    try:
        return Ok(json.loads(raw, object_pairs_hook=_unique_object))
    except (ValueError, UnicodeDecodeError):
        return invalid(
            "operator_binding",
            "operator descriptor is canonical JSON without duplicate keys",
        )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def _absolute_directory(value: object, field: str) -> Result[Path]:
    if not isinstance(value, str) or not value:
        return invalid(field, "operator runtime roots are explicit absolute paths")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        return invalid(field, "operator runtime roots are absolute without parent traversal")
    return Ok(path)


def _parse_fp(value: object, field: str) -> Result[Fingerprint]:
    if value is None:
        return invalid(field, "a pinned fp1 is required")
    return Fingerprint.try_create(value)


def _safe_source_path(value: str) -> bool:
    path = Path(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and path.suffix == ".py"
        and bool(path.parts)
    )


def _valid_entrypoint(value: str, files: Mapping[str, str]) -> bool:
    module_name, separator, attribute = value.partition(":")
    if not separator or not module_name or not attribute or not attribute.isidentifier():
        return False
    return (
        module_name.replace(".", "/") + ".py" in files
        or module_name.replace(".", "/") + "/__init__.py" in files
    )
