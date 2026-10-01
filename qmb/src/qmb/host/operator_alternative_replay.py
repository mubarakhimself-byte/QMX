"""Resolve the operator-pinned ATC runtime for the existing QMA backtest CLI."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import cast

from qmf.core import Fingerprint, Instant, Ok, Result, WriterId, fingerprint, is_ok, is_refusal

from qmb._refuse import invalid, policy, unavailable
from qmb.host.operator_alternative import (
    OperatorAlternativeInputs,
    run_operator_alternative,
    validate_operator_alternative_result,
)
from qmb.host.qma_cli import QmaBacktestContext, validate_qma_backtest_context

__all__ = [
    "execute_operator_alternative_replay",
    "operator_alternative_binding_present",
    "read_operator_alternative_binding",
    "verify_operator_alternative_result",
]

_BINDING_FILENAME = "operator-alternative-binding.json"
_BINDING_CLASS = "qmb-operator-alternative-binding-v1"
_BINDING_FIELDS = frozenset(
    {
        "class",
        "format_version",
        "composition_class",
        "experiment_spec_fp1",
        "evidence_ref",
        "split_manifest_fp1",
        "operator_binding",
        "operator_binding_fp1",
        "builder_files",
        "builder_fp1",
        "entrypoint",
        "descriptor_fp1",
    }
)
_BINDING_BODY_FIELDS = frozenset(
    {
        "class",
        "format_version",
        "experiment_spec_fp1",
        "evidence_ref",
        "split_manifest_fp1",
        "composition_fp1",
        "policy_pair_identity",
        "source_fp1",
        "split_fp1",
        "split_role",
        "registry_fp1",
        "interpreter_registration_fp1",
        "journal_writer",
        "journal_stream",
        "terminal_root",
        "lineage_writer",
        "roots",
        "registry_as_of_ns",
        "registry_writer",
        "initial_accounting_state",
        "initial_accounting_state_fp1",
        "command_owner_epoch",
        "trial_label",
    }
)
_ROOT_NAMES = frozenset({"raw", "registry", "journal", "alternative_terminal"})


@dataclass(frozen=True, slots=True)
class OperatorAlternativeBinding:
    """Strict operator-selected ATC descriptor, selected only by CT-47 refs."""

    context: QmaBacktestContext
    identity: Mapping[str, object]
    builder_files: Mapping[str, str]
    builder_fp1: Fingerprint
    entrypoint: str
    descriptor_fp1: Fingerprint


def read_operator_alternative_binding(
    *, runtime_root: object, context: object
) -> Result[OperatorAlternativeBinding]:
    """Read a content-addressed Alternative descriptor under operator-owned root."""
    checked_context = validate_qma_backtest_context(context)
    if is_refusal(checked_context):
        return checked_context
    context = checked_context.value
    if context.mints_ct32 is not False:
        return policy(
            "mints_ct32",
            "Alternative execution requires its declared non-CT-32 result mode",
        )
    root = _absolute_directory(runtime_root, "runtime_root")
    if is_refusal(root):
        return root
    directory = (
        root.value
        / context.experiment_spec_fp1.value.replace(":", "-")
        / context.evidence_ref.value.replace(":", "-")
    )
    descriptor = _read_object(directory / _BINDING_FILENAME)
    if is_refusal(descriptor):
        return descriptor
    body = cast(Mapping[str, object], descriptor.value)
    if frozenset(body) != _BINDING_FIELDS:
        return invalid(
            "operator_binding",
            "ATC descriptor contains the exact versioned field set",
            missing=sorted(_BINDING_FIELDS.difference(body)),
            extra=sorted(set(body).difference(_BINDING_FIELDS)),
        )
    if body.get("class") != _BINDING_CLASS or type(body.get("format_version")) is not int:
        return invalid("operator_binding", "ATC descriptor uses its registered class and version")
    if body.get("format_version") != 1 or body.get("composition_class") != "alternative":
        return policy("composition_class", "operator descriptor selects the ATC composition")
    for key, expected in (
        ("experiment_spec_fp1", context.experiment_spec_fp1.value),
        ("evidence_ref", context.evidence_ref.value),
        ("split_manifest_fp1", context.split_manifest_fp1.value),
    ):
        if body.get(key) != expected:
            return policy(key, "ATC descriptor is bound to the selected registered QMA refs")
    identity = body.get("operator_binding")
    if not isinstance(identity, Mapping):
        return invalid("operator_binding", "ATC descriptor pins one operator identity object")
    identity_body = cast(Mapping[str, object], identity)
    if frozenset(identity_body) != _BINDING_BODY_FIELDS:
        return invalid(
            "operator_binding",
            "ATC operator identity contains the exact semantic and root fields",
            missing=sorted(_BINDING_BODY_FIELDS.difference(identity_body)),
            extra=sorted(set(identity_body).difference(_BINDING_BODY_FIELDS)),
        )
    binding_fp = _parse_fingerprint(body.get("operator_binding_fp1"), "operator_binding_fp1")
    if is_refusal(binding_fp):
        return binding_fp
    actual_binding_fp = fingerprint(identity_body)
    if is_refusal(actual_binding_fp) or actual_binding_fp.value != binding_fp.value:
        return policy("operator_binding_fp1", "ATC binding identity reproduces its fingerprint")
    for key, expected in (
        ("experiment_spec_fp1", context.experiment_spec_fp1.value),
        ("evidence_ref", context.evidence_ref.value),
        ("split_manifest_fp1", context.split_manifest_fp1.value),
    ):
        if identity_body.get(key) != expected:
            return policy(key, "nested ATC identity matches the selected QMA refs")
    roots = _decode_roots(identity_body.get("roots"))
    if is_refusal(roots):
        return roots
    registry_as_of_ns = identity_body.get("registry_as_of_ns")
    if type(registry_as_of_ns) is not int:
        return invalid("registry_as_of_ns", "registry as-of is an exact integer nanosecond instant")
    registry_as_of = Instant.try_create(registry_as_of_ns)
    if is_refusal(registry_as_of):
        return registry_as_of
    if _writer_from_body(identity_body.get("registry_writer")) is None:
        return invalid("registry_writer", "ATC descriptor pins a canonical registry WriterId")
    if identity_body.get("terminal_root") != str(roots.value["alternative_terminal"]):
        return policy("terminal_root", "terminal root matches the pinned ATC root set")
    initial_state = identity_body.get("initial_accounting_state")
    if not isinstance(initial_state, Mapping):
        return invalid("initial_accounting_state", "ATC descriptor pins an accounting state object")
    initial_state_fp = fingerprint(cast(Mapping[str, object], initial_state))
    state_fp_ref = _parse_fingerprint(
        identity_body.get("initial_accounting_state_fp1"), "initial_accounting_state_fp1"
    )
    if is_refusal(state_fp_ref):
        return state_fp_ref
    if is_refusal(initial_state_fp) or initial_state_fp.value != state_fp_ref.value:
        return policy("initial_accounting_state_fp1", "accounting seed matches its descriptor fp1")
    owner_epoch = identity_body.get("command_owner_epoch")
    if isinstance(owner_epoch, bool) or not isinstance(owner_epoch, int) or owner_epoch < 0:
        return invalid("command_owner_epoch", "ATC descriptor pins a nonnegative exact owner epoch")
    trial_label = _decode_trial_label(identity_body.get("trial_label"))
    if is_refusal(trial_label):
        return trial_label
    for field in (
        "composition_fp1",
        "source_fp1",
        "split_fp1",
        "registry_fp1",
        "interpreter_registration_fp1",
    ):
        parsed = _parse_fingerprint(identity_body.get(field), field)
        if is_refusal(parsed):
            return parsed
    journal_writer = _writer_from_body(identity_body.get("journal_writer"))
    lineage_writer = _writer_from_body(identity_body.get("lineage_writer"))
    if journal_writer is None or lineage_writer is None:
        return invalid("writer", "ATC descriptor pins CT-13 and CT-07 WriterIds")
    if identity_body.get("journal_stream") != journal_writer.stream:
        return policy("journal_stream", "CT-13 stream matches the pinned WriterId")
    descriptor_stamp = fingerprint(
        {key: body[key] for key in _BINDING_FIELDS if key != "descriptor_fp1"}
    )
    descriptor_fp = _parse_fingerprint(body.get("descriptor_fp1"), "descriptor_fp1")
    if is_refusal(descriptor_fp):
        return descriptor_fp
    if is_refusal(descriptor_stamp) or descriptor_stamp.value != descriptor_fp.value:
        return policy("descriptor_fp1", "ATC descriptor bytes match the pinned fingerprint")
    if (
        context.operator_descriptor_fp1 is not None
        and context.operator_descriptor_fp1 != descriptor_fp.value
    ):
        return policy(
            "operator_descriptor_fp1",
            "the QMA placement pins this exact trusted Alternative runtime descriptor",
        )
    builder_raw = body.get("builder_files")
    if not isinstance(builder_raw, Mapping) or not builder_raw:
        return invalid("builder_files", "ATC descriptor pins non-empty builder source bytes")
    builder: dict[str, str] = {}
    for raw_path, raw_source in cast(Mapping[object, object], builder_raw).items():
        if not isinstance(raw_path, str) or not _safe_module_path(raw_path):
            return invalid("builder_files", "ATC builder paths are safe Python source paths")
        if not isinstance(raw_source, str):
            return invalid("builder_files", "ATC builder contents are UTF-8 text")
        builder[raw_path] = raw_source
    builder_stamp = fingerprint({"class": "qmb-operator-alternative-builder-v1", "files": builder})
    builder_fp = _parse_fingerprint(body.get("builder_fp1"), "builder_fp1")
    if is_refusal(builder_fp):
        return builder_fp
    if is_refusal(builder_stamp) or builder_stamp.value != builder_fp.value:
        return policy("builder_fp1", "ATC builder source matches its pinned fingerprint")
    entrypoint = body.get("entrypoint")
    if not isinstance(entrypoint, str) or not _valid_entrypoint(entrypoint, builder):
        return invalid("entrypoint", "ATC builder selects a declared module:function")
    return Ok(
        OperatorAlternativeBinding(
            context=context,
            identity=identity_body,
            builder_files=builder,
            builder_fp1=builder_fp.value,
            entrypoint=entrypoint,
            descriptor_fp1=descriptor_fp.value,
        )
    )


def operator_alternative_binding_present(*, runtime_root: object, context: object) -> Result[bool]:
    """Select the Alternative branch only when its operator descriptor exists.

    Existence selects the composition; descriptor parsing happens afterward and
    must succeed. A malformed Alternative descriptor therefore cannot silently
    fall through to the Book runtime.
    """
    checked_context = validate_qma_backtest_context(context)
    if is_refusal(checked_context):
        return checked_context
    context = checked_context.value
    root = _absolute_directory(runtime_root, "runtime_root")
    if is_refusal(root):
        return root
    directory = (
        root.value
        / context.experiment_spec_fp1.value.replace(":", "-")
        / context.evidence_ref.value.replace(":", "-")
    )
    try:
        alternative_exists = os.path.lexists(directory / _BINDING_FILENAME)
        book_exists = os.path.lexists(directory / "operator-binding.json")
    except OSError as exc:
        return unavailable(
            "operator_binding", "composition descriptor can be inspected", error=str(exc)
        )
    if alternative_exists and book_exists:
        return policy(
            "composition_class",
            "one operator descriptor selects exactly one execution composition",
        )
    return Ok(alternative_exists)


def execute_operator_alternative_replay(
    *, runtime_root: object, context: object
) -> Result[Mapping[str, object]]:
    """Materialize typed operator ports, run ATC, and return its reopened result."""
    binding = read_operator_alternative_binding(runtime_root=runtime_root, context=context)
    if is_refusal(binding):
        return binding
    if not isinstance(context, QmaBacktestContext) or context.operator_descriptor_fp1 is None:
        return invalid("operator_descriptor_fp1", "execution is pinned to a completed preflight")
    with tempfile.TemporaryDirectory(prefix="qmb-operator-alternative-") as raw:
        builder_root = Path(raw)
        materialized = _materialize(binding.value.builder_files, builder_root)
        if is_refusal(materialized):
            return materialized
        module = _load_builder(builder_root, binding.value.entrypoint)
        if is_refusal(module):
            return module
        try:
            entry = _resolve_entrypoint(module.value, binding.value.entrypoint)
            if is_refusal(entry):
                return entry
            try:
                built = entry.value(binding.value.context, binding.value)
            except Exception as exc:
                return policy("operator_builder", "pinned ATC builder executes", error=str(exc))
            if is_refusal(built):
                return built
            if not is_ok(built):
                return invalid("operator_runtime", "ATC builder returns a typed Result")
            inputs = _validate_runtime_inputs(built.value, binding.value)
            if is_refusal(inputs):
                return inputs
            result = run_operator_alternative(inputs.value)
            if is_refusal(result):
                return result
            validated = validate_operator_alternative_result(
                result.value.payload,
                inputs=inputs.value,
            )
            if is_refusal(validated):
                return validated
            return Ok(result.value.payload)
        finally:
            _remove_builder_modules(builder_root)


def verify_operator_alternative_result(
    *, runtime_root: object, context: object, claimed_result: object | None
) -> Result[Mapping[str, object]]:
    """Reopen the pinned ATC terminal and validate a prior child response."""
    binding = read_operator_alternative_binding(runtime_root=runtime_root, context=context)
    if is_refusal(binding):
        return binding
    if not isinstance(context, QmaBacktestContext) or context.operator_descriptor_fp1 is None:
        return invalid("operator_descriptor_fp1", "verification uses the completed preflight pin")
    if claimed_result is not None and not isinstance(claimed_result, Mapping):
        return invalid("claimed_result", "ATC verification consumes the prior result object")
    with tempfile.TemporaryDirectory(prefix="qmb-operator-alternative-verify-") as raw:
        builder_root = Path(raw)
        materialized = _materialize(binding.value.builder_files, builder_root)
        if is_refusal(materialized):
            return materialized
        module = _load_builder(builder_root, binding.value.entrypoint)
        if is_refusal(module):
            return module
        try:
            entry = _resolve_entrypoint(module.value, binding.value.entrypoint)
            if is_refusal(entry):
                return entry
            try:
                built = entry.value(binding.value.context, binding.value)
            except Exception as exc:
                return policy(
                    "operator_builder", "pinned ATC inputs can be resolved", error=str(exc)
                )
            if is_refusal(built):
                return built
            if not is_ok(built):
                return invalid("operator_runtime", "ATC builder returns a typed Result")
            inputs = _validate_runtime_inputs(built.value, binding.value)
            if is_refusal(inputs):
                return inputs
            validated = validate_operator_alternative_result(
                None if claimed_result is None else cast(Mapping[str, object], claimed_result),
                inputs=inputs.value,
            )
            if is_refusal(validated):
                return validated
            return Ok(validated.value.payload)
        finally:
            _remove_builder_modules(builder_root)


def _validate_runtime_inputs(
    raw: object, binding: OperatorAlternativeBinding
) -> Result[OperatorAlternativeInputs]:
    if not isinstance(raw, OperatorAlternativeInputs):
        return invalid("operator_runtime", "ATC builder returns typed OperatorAlternativeInputs")
    if raw.context != binding.context:
        return policy("qma_context", "ATC runtime ports match the selected QMA placement")
    identity = binding.identity
    config = raw.config
    if config.composition_fp.value != identity.get("composition_fp1"):
        return policy("composition_fp1", "ATC config matches the descriptor composition")
    pair = identity.get("policy_pair_identity")
    if not isinstance(pair, Mapping) or not _same_canonical(
        config.policy_pair.identity(), cast(Mapping[str, object], pair)
    ):
        return policy("policy_pair_identity", "ATC config matches the exact descriptor Pair")
    if raw.recorded_source.fingerprint.value != identity.get("source_fp1"):
        return policy("source_fp1", "CT-10 source matches the descriptor")
    if raw.recorded_source.split_fp1 is None:
        return policy("split_fp1", "CT-10 source has its registered CT-12 split")
    if raw.recorded_source.split_fp1.value != identity.get("split_fp1"):
        return policy("split_fp1", "CT-12 split matches the descriptor")
    if (
        raw.recorded_source.split_role is None
        or raw.recorded_source.split_role.value != identity.get("split_role")
    ):
        return policy("split_role", "CT-12 role matches the descriptor")
    if raw.registry.fingerprint.value != identity.get("registry_fp1"):
        return policy("registry_fp1", "interpreter registry matches the descriptor")
    resolved = raw.registry.resolve(config)
    if is_refusal(resolved):
        return resolved
    if resolved.value.fingerprint.value != identity.get("interpreter_registration_fp1"):
        return policy("interpreter_registration_fp1", "selected interpreter matches the descriptor")
    journal_writer = _writer_from_body(identity.get("journal_writer"))
    lineage_writer = _writer_from_body(identity.get("lineage_writer"))
    if journal_writer is None or raw.journal_writer.writer != journal_writer:
        return policy("journal_writer", "CT-13 writer matches the descriptor")
    if raw.journal_writer.stream_name != identity.get("journal_stream"):
        return policy("journal_stream", "CT-13 stream matches the descriptor")
    try:
        expected_terminal_root = Path(str(identity.get("terminal_root"))).resolve(strict=True)
        actual_terminal_root = raw.terminal_store.root.resolve(strict=True)
    except OSError as exc:
        return unavailable("terminal_root", "pinned ATC terminal root is readable", error=str(exc))
    if actual_terminal_root != expected_terminal_root:
        return policy("terminal_root", "ATC terminal store uses its operator-pinned root")
    if lineage_writer is None or raw.lineage_writer != lineage_writer:
        return policy("lineage_writer", "CT-07 writer matches the descriptor")
    if raw.expected_command_owner_epoch != identity.get("command_owner_epoch"):
        return policy("command_owner_epoch", "ATC command epoch matches the descriptor")
    initial_fp = fingerprint(raw.initial_accounting_state)
    if is_refusal(initial_fp) or initial_fp.value.value != identity.get(
        "initial_accounting_state_fp1"
    ):
        return policy("initial_accounting_state", "initial accounting state matches the descriptor")
    seed = identity.get("initial_accounting_state")
    if not isinstance(seed, Mapping) or not _same_canonical(
        raw.initial_accounting_state, cast(Mapping[str, object], seed)
    ):
        return policy("initial_accounting_state", "accounting seed bytes match the descriptor")
    trial_label = _decode_trial_label(identity.get("trial_label"))
    if is_refusal(trial_label):
        return trial_label
    if not _same_canonical(raw.trial_label or {}, trial_label.value):
        return policy("trial_label", "operator descriptor pins the exact study label or null")
    if raw.runtime_descriptor_fp1 != binding.descriptor_fp1:
        return policy("descriptor_fp1", "typed ATC runtime binds the selected descriptor fp1")
    roots_result = _decode_roots(identity.get("roots"))
    if is_refusal(roots_result):
        return roots_result
    roots = roots_result.value
    registry_root = raw.registry_persistence.root
    if registry_root.resolve() != roots["registry"]:
        return policy("registry_root", "CT-07 persistence uses the operator-pinned registry root")
    if raw.journal_root.resolve() != roots["journal"]:
        return policy("journal_root", "CT-13 persistence uses the operator-pinned journal root")
    if raw.raw_store_root.resolve() != roots["raw"]:
        return policy("raw_store_root", "CT-10 resolver uses the operator-pinned raw-data root")
    if raw.registry_persistence.world.value != "replay":
        return policy("registry_world", "registry persistence is bound to replay world")
    if raw.registry_as_of.value_ns != identity.get("registry_as_of_ns"):
        return policy("registry_as_of_ns", "registry read uses the pinned as-of instant")
    expected_registry_writer = _writer_from_body(identity.get("registry_writer"))
    if raw.registry_writer != expected_registry_writer:
        return policy("registry_writer", "registry read uses the pinned WriterId")
    return Ok(raw)


def _read_object(path: Path) -> Result[object]:
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            raw = stream.read(8 * 1024 * 1024 + 1)
    except FileNotFoundError:
        return unavailable("operator_binding", "no ATC binding exists for these CT-47 refs")
    except OSError as exc:
        return unavailable("operator_binding", "ATC descriptor cannot be opened", error=str(exc))
    if len(raw) > 8 * 1024 * 1024:
        return invalid("operator_binding", "ATC descriptor stays within the bounded file size")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_pairs)
    except (UnicodeError, ValueError, TypeError):
        return invalid("operator_binding", "ATC descriptor is strict JSON without duplicate keys")
    if not isinstance(value, Mapping):
        return invalid("operator_binding", "ATC descriptor is one JSON object")
    return Ok(cast(Mapping[str, object], value))


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _absolute_directory(value: object, field: str) -> Result[Path]:
    if not isinstance(value, str) or not value.strip():
        return invalid(field, "operator runtime root is an explicit absolute path")
    path = Path(value)
    if not path.is_absolute():
        return invalid(field, "operator runtime root is absolute")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        return unavailable(field, "operator runtime root exists", error=str(exc))
    if not resolved.is_dir():
        return invalid(field, "operator runtime root is a directory")
    return Ok(resolved)


def _decode_roots(value: object) -> Result[Mapping[str, Path]]:
    if not isinstance(value, Mapping):
        return invalid("roots", "ATC descriptor pins its operator-owned QMF roots")
    raw = cast(Mapping[object, object], value)
    if frozenset(raw) != _ROOT_NAMES:
        return invalid("roots", "ATC descriptor names the exact supported roots")
    decoded: dict[str, Path] = {}
    for key, candidate in raw.items():
        if not isinstance(key, str):
            return invalid("roots", "ATC root names are text")
        parsed = _absolute_directory(candidate, f"roots.{key}")
        if is_refusal(parsed):
            return parsed
        decoded[key] = parsed.value
    if len(set(decoded.values())) != len(decoded):
        return policy("roots", "ATC registry, raw, journal and terminal roots are distinct")
    return Ok(decoded)


def _decode_trial_label(value: object) -> Result[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return invalid("trial_label", "ATC trial label uses a canonical presence wrapper")
    body = cast(Mapping[str, object], value)
    if frozenset(body) != frozenset({"class", "present", "label"}):
        return invalid("trial_label", "ATC trial label wrapper has exact fields")
    if body.get("class") != "qmb-alternative-trial-label-v1":
        return invalid("trial_label", "ATC trial label uses its registered wrapper class")
    present = body.get("present")
    label = body.get("label")
    if type(present) is not bool or not isinstance(label, Mapping):
        return invalid("trial_label", "ATC trial label presence and mapping are typed")
    if not present and label:
        return policy("trial_label", "an absent trial label carries an empty mapping")
    if present and not label:
        return policy("trial_label", "a present trial label is nonempty")
    return Ok(cast(Mapping[str, object], label))


def _parse_fingerprint(value: object, field: str) -> Result[Fingerprint]:
    parsed = Fingerprint.try_create(value)
    if is_refusal(parsed):
        return invalid(field, "operator descriptor contains a canonical fp1")
    return parsed


def _writer_from_body(value: object) -> WriterId | None:
    if not isinstance(value, Mapping):
        return None
    body = cast(Mapping[str, object], value)
    parsed = WriterId.try_create(
        body.get("machine"),
        body.get("role"),
        body.get("stream"),
        body.get("boot_epoch_id"),
    )
    return None if is_refusal(parsed) else parsed.value


def _same_canonical(left: object, right: object) -> bool:
    left_fp = fingerprint(left)
    right_fp = fingerprint(right)
    return not is_refusal(left_fp) and not is_refusal(right_fp) and left_fp.value == right_fp.value


def _safe_module_path(value: str) -> bool:
    path = Path(value)
    return (
        value.endswith(".py")
        and not path.is_absolute()
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _valid_entrypoint(value: str, files: Mapping[str, str]) -> bool:
    if value.count(":") != 1:
        return False
    module, attribute = value.split(":", 1)
    if (
        not module
        or not attribute
        or not all(part.isidentifier() for part in (*module.split("."), attribute))
    ):
        return False
    relative = module.replace(".", "/") + ".py"
    return relative in files or module.replace(".", "/") + "/__init__.py" in files


def _materialize(files: Mapping[str, str], root: Path) -> Result[None]:
    for relative, source in files.items():
        target = root.joinpath(*relative.split("/"))
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8")
        except OSError as exc:
            return unavailable("operator_builder", "ATC source tree materializes", error=str(exc))
    return Ok(None)


def _load_builder(root: Path, entrypoint: str) -> Result[ModuleType]:
    module_name, _ = entrypoint.split(":", 1)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        parts = module_name.split(".")
        for index in range(1, len(parts)):
            package_name = ".".join(parts[:index])
            if package_name in sys.modules:
                loaded = sys.modules[package_name]
                loaded_path = getattr(loaded, "__file__", None)
                if not isinstance(loaded_path, str) or not Path(loaded_path).is_relative_to(root):
                    return policy(
                        "operator_builder", "builder package has no stale imported module"
                    )
                continue
            package_path = root.joinpath(*parts[:index]) / "__init__.py"
            if not package_path.is_file():
                return invalid("entrypoint", "dotted ATC modules have pinned package initializers")
            package_spec = importlib.util.spec_from_file_location(
                package_name,
                package_path,
                submodule_search_locations=[str(package_path.parent)],
            )
            if package_spec is None or package_spec.loader is None:
                return invalid("entrypoint", "ATC package initializer loads from pinned source")
            package = importlib.util.module_from_spec(package_spec)
            sys.modules[package_name] = package
            package_spec.loader.exec_module(package)
        module_path = root.joinpath(*parts)
        file_path = module_path.with_suffix(".py")
        if not file_path.is_file():
            file_path = module_path / "__init__.py"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return invalid("entrypoint", "ATC builder module loads from its pinned source tree")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except Exception as exc:
        _remove_builder_modules(root)
        return policy("operator_builder", "pinned ATC builder imports cleanly", error=str(exc))
    finally:
        sys.path[:] = [path for path in sys.path if path != str(root)]
    return Ok(module)


def _resolve_entrypoint(
    module: ModuleType, entrypoint: str
) -> Result[Callable[[QmaBacktestContext, OperatorAlternativeBinding], Result[object]]]:
    _module_name, attribute = entrypoint.split(":", 1)
    value = getattr(module, attribute, None)
    if not callable(value):
        return invalid("entrypoint", "ATC builder entrypoint is callable")
    return Ok(
        cast(Callable[[QmaBacktestContext, OperatorAlternativeBinding], Result[object]], value)
    )


def _remove_builder_modules(root: Path) -> None:
    for name, module in tuple(sys.modules.items()):
        module_file = getattr(module, "__file__", None)
        if isinstance(module_file, str) and Path(module_file).is_relative_to(root):
            sys.modules.pop(name, None)
    sys.path[:] = [path for path in sys.path if Path(path or ".").resolve() != root]
