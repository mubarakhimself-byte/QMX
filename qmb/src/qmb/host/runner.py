"""QMB composition-root Layer-2 sandbox runner (QL-8, AR-68).

V1 enforcement of no-clock / no-I-O / no-network is exactly three mechanisms:

* static AST/import scanning (Layer-2 failure **before** any process is spawned)
* capability starvation (hosts inject read surfaces only; no Book, clock, or
  venue command surface)
* host process isolation via stdlib ``subprocess`` (B-5's posture)

Hardened OS-level confinement (restricted tokens / job objects on Windows,
seccomp-class on Linux) is a named deferred dependency of the node/platform
sitting — V1 does not wait on it. A dynamically-evasive malicious bot is out of
V1's threat model; bots are operator- or operator's-agent-authored (DEC-0178).

The runner owns only spawning and isolation. Observations feed
:func:`qml.conformance.evaluate_layer2`; host identity never enters the verdict.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Final, TextIO, cast

from qmf.core.fingerprint import Fingerprint
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
    is_refusal,
)
from qml._refuse import invalid, policy, unavailable
from qml.conformance.layer2 import (
    Layer2Observations,
    Layer2Verdict,
    collect_layer2_observations,
    evaluate_layer2,
)
from qml.conformance.scan import ScanReport, scan_logic_source
from qml.conformance.slice import generate_golden_slice
from qml.declaration.bot import BotDefinition, mint_bot_definition
from qml.logic import normalize_source_manifest
from qml.protocol import FunctionFactory
from qml.protocol.state import BotStateScope

__all__ = [
    "FACTORY_KIND_SILENT",
    "FACTORY_KIND_SOURCE",
    "V1_DEFERRED_OS_CONFINEMENT",
    "V1_ENFORCEMENT_MECHANISMS",
    "V1_OUT_OF_SCOPE",
    "FactorySpec",
    "run_sandbox",
    "v1_enforcement_identity",
    "worker_main",
]

FACTORY_KIND_SILENT: Final[str] = "silent"
FACTORY_KIND_SOURCE: Final[str] = "source"

V1_ENFORCEMENT_MECHANISMS: Final[tuple[str, ...]] = (
    "static_ast_import_scan",
    "capability_starvation",
    "host_process_isolation",
)
V1_DEFERRED_OS_CONFINEMENT: Final[tuple[str, ...]] = (
    "windows_restricted_tokens",
    "windows_job_objects",
    "linux_seccomp",
)
V1_OUT_OF_SCOPE: Final[tuple[str, ...]] = ("dynamically_evasive_malicious_bot",)

_SEED_NAME: Final[str] = "seed"
_LAYER: Final[int] = 2
_WORKER_MODULE: Final[str] = "qmb.host.worker"
_BOOK_KEYS: Final[frozenset[str]] = frozenset({"book", "book_module", "Book", "book_present"})
_SANDBOX_CLASS: Final[str] = "qmb-host-sandbox-v1"


def v1_enforcement_identity() -> dict[str, object]:
    """Named V1 scope. Package SemVer and host identity never enter a verdict."""
    return {
        "class": _SANDBOX_CLASS,
        "mechanisms": list(V1_ENFORCEMENT_MECHANISMS),
        "deferred_os_confinement": list(V1_DEFERRED_OS_CONFINEMENT),
        "out_of_scope": list(V1_OUT_OF_SCOPE),
        "verdict_function": "qml.conformance.evaluate_layer2",
        "process_management": "stdlib.subprocess",
    }


@dataclass(frozen=True, slots=True)
class FactorySpec:
    """How the isolated child reconstructs the bot factory.

    ``silent`` emits zero intents. ``source`` is operator-authored Python that
    binds ``factory``. Live callables cannot cross the process boundary.
    """

    kind: str
    source: str = ""
    entrypoint: str | None = None


def run_sandbox(
    *,
    declaration: object,
    source_tree: object,
    factory_spec: object = None,
    assignment: object = None,
    state_scope: object,
    state_bound: object,
    timeout_seconds: object = None,
) -> Result[Layer2Verdict]:
    """Spawn an isolated bot process and feed observations to the pure verdict.

    A static AST/import scan that detects clock, filesystem, or network use is a
    Layer-2 failure **before** any process is spawned. The runner never computes
    the verdict and never injects a Book.
    """
    timeout = _coerce_timeout(timeout_seconds)
    if is_refusal(timeout):
        return timeout
    bot = _admit_declaration(declaration)
    if is_refusal(bot):
        return _journal(bot)
    definition = bot.value
    tree = normalize_source_manifest(source_tree)
    if is_refusal(tree):
        return _journal(tree)
    files = dict(tree.value)
    scan = scan_logic_source(files, declared_seed=_has_declared_seed(definition))
    if is_refusal(scan):
        return _journal(scan)
    if scan.value.findings:
        return _verdict_from_scan_findings(definition, scan.value)
    if factory_spec is None:
        # The selected artifact is the declared, fingerprinted source tree.
        # Never substitute a silent fixture when production omitted a loader.
        candidates = [
            (path, source)
            for path, source in files.items()
            if path.rsplit("/", 1)[-1] == "factory.py"
        ]
        if len(candidates) != 1:
            return policy(
                "factory_spec",
                "conformance must load one factory.py from the manifest-bound logic source",
                candidates=tuple(path for path, _ in candidates),
                layer=_LAYER,
            )
        spec = Ok(
            FactorySpec(
                kind=FACTORY_KIND_SOURCE,
                source=candidates[0][1],
                entrypoint=_module_entrypoint(candidates[0][0]),
            )
        )
    else:
        spec = coerce_factory_spec(factory_spec)
        if is_refusal(spec):
            return spec
        if spec.value.kind == FACTORY_KIND_SILENT:
            return policy(
                "factory_spec",
                "an explicit silent fixture cannot mint a production Layer-2 verdict",
                layer=_LAYER,
            )
        if spec.value.kind == FACTORY_KIND_SOURCE:
            # CT-33 pins source bytes but does not currently pin a callable
            # selector. Therefore only the unique conventional factory.py:factory
            # is admissible until the selector is added to LogicIdentity.
            conventional = [p for p in files if p.rsplit("/", 1)[-1] == "factory.py"]
            expected = _module_entrypoint(conventional[0]) if len(conventional) == 1 else None
            if expected is None or (
                spec.value.entrypoint is not None and spec.value.entrypoint != expected
            ):
                return policy(
                    "factory_spec",
                    "source manifest selects its unique conventional factory.py:factory entrypoint",
                    layer=_LAYER,
                )
            path = _entrypoint_path(files, expected)
            if path is None or files[path] != spec.value.source:
                return policy(
                    "factory_spec",
                    "factory entrypoint resolves to matching source bytes in the logic manifest",
                    entrypoint=expected,
                    layer=_LAYER,
                )
            spec = Ok(FactorySpec(spec.value.kind, spec.value.source, expected))
    payload = _encode_payload(
        definition=definition,
        source_tree=files,
        factory_spec=spec.value,
        assignment=assignment,
        state_scope=state_scope,
        state_bound=state_bound,
    )
    if is_refusal(payload):
        return payload
    envelope = _spawn_isolated(payload.value, timeout_seconds=timeout.value)
    if is_refusal(envelope):
        return envelope
    return _verdict_from_envelope(envelope.value)


def coerce_factory_spec(value: object) -> Result[FactorySpec]:
    """Admit a reconstructable factory spec. A Book key is a Layer-2 failure."""
    if value is None:
        return invalid(
            "factory_spec",
            "silent is a test fixture; production conformance names manifest-bound source",
            layer=_LAYER,
        )
    if isinstance(value, FactorySpec):
        blocked = _refuse_book(value.source) if value.source else None
        if blocked is not None:
            return blocked
        return _validate_spec(value.kind, value.source, value.entrypoint)
    if isinstance(value, str):
        return _validate_spec(FACTORY_KIND_SOURCE, value)
    if not isinstance(value, Mapping):
        return invalid(
            "factory_spec",
            "a sandbox factory spec is silent, a source string, or a mapping",
            given=type(value).__name__,
            layer=_LAYER,
        )
    mapping = cast("Mapping[str, object]", value)
    blocked = _refuse_book_keys(mapping)
    if blocked is not None:
        return blocked
    kind = mapping.get("kind", FACTORY_KIND_SOURCE)
    if not isinstance(kind, str):
        return invalid(
            "factory_spec",
            "factory_spec.kind is silent or source",
            given=repr(kind),
            layer=_LAYER,
        )
    source = mapping.get("source", mapping.get("factory_source", ""))
    if source is None:
        source = ""
    if not isinstance(source, str):
        return invalid(
            "factory_spec",
            "factory source is a string of operator-authored Python binding factory",
            given=type(source).__name__,
            layer=_LAYER,
        )
    entrypoint = mapping.get("entrypoint")
    if entrypoint is not None and not isinstance(entrypoint, str):
        return invalid("factory_spec", "factory entrypoint is module:attribute", layer=_LAYER)
    parsed = _validate_spec(kind, source, entrypoint)
    if is_refusal(parsed) or entrypoint is None:
        return parsed
    if ":" not in entrypoint:
        return invalid(
            "factory_spec", "factory entrypoint is module:attribute", given=entrypoint, layer=_LAYER
        )
    module, attribute = entrypoint.split(":", 1)
    if (
        not module
        or not attribute.isidentifier()
        or any(not part.isidentifier() for part in module.split("."))
    ):
        return invalid(
            "factory_spec", "factory entrypoint is module:attribute", given=entrypoint, layer=_LAYER
        )
    return parsed


def load_factory(spec: FactorySpec, *, source_tree: object = None) -> Result[object]:
    """Reconstruct the factory in this process. Used by the isolated child."""
    if spec.kind == FACTORY_KIND_SILENT:
        return Ok(FunctionFactory(logic=_silent_logic))
    try:
        if source_tree is None:
            module = _load_source_factory_module(spec.source)
        else:
            normalized = normalize_source_manifest(source_tree)
            if is_refusal(normalized):
                return normalized
            path = _entrypoint_path(normalized.value, spec.entrypoint)
            if path is None or normalized.value[path] != spec.source:
                return policy(
                    "factory_spec",
                    "a source factory resolves to matching bytes at its manifest entrypoint",
                    entrypoint=spec.entrypoint,
                    layer=_LAYER,
                )
            with _manifest_factory(normalized.value, path, spec) as factory:
                return Ok(factory)
    except SyntaxError as exc:
        return invalid(
            "factory_spec",
            "factory source must parse as Python",
            lineno=exc.lineno,
            layer=_LAYER,
        )
    except Exception as exc:
        return invalid(
            "factory_spec",
            "factory source failed to execute in the isolated process",
            given=type(exc).__name__,
            layer=_LAYER,
        )
    attribute = "factory"
    if spec.entrypoint is not None and ":" in spec.entrypoint:
        attribute = spec.entrypoint.split(":", 1)[1]
    factory = getattr(module, attribute, None)
    if factory is None:
        return invalid(
            "factory_spec",
            "factory source must bind the name factory",
            layer=_LAYER,
        )
    return Ok(factory)


@contextmanager
def _manifest_module(source_tree: Mapping[str, str], entry_path: str):
    """Load a manifest module while its complete source tree remains available."""
    module_path = entry_path[:-3] if entry_path.endswith(".py") else entry_path
    parts = module_path.split("/")
    if parts[-1] == "__init__":
        parts.pop()
    module_name = ".".join(parts)
    if not module_name or any(not part.isidentifier() for part in parts):
        raise ImportError("manifest factory path is not a Python module path")
    with tempfile.TemporaryDirectory(prefix="qml_logic_manifest_") as root:
        root_path = Path(root)
        for relative, body in source_tree.items():
            target = root_path.joinpath(*relative.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8", newline="\n")
        sys.path.insert(0, root)
        try:
            importlib.invalidate_caches()
            module = importlib.import_module(module_name)
            yield module
        finally:
            sys.path.remove(root)
            for name, loaded in tuple(sys.modules.items()):
                loaded_path = getattr(loaded, "__file__", None)
                if isinstance(loaded_path, str) and Path(loaded_path).is_relative_to(root_path):
                    sys.modules.pop(name, None)


def _module_entrypoint(path: str) -> str:
    module = path[:-3] if path.endswith(".py") else path
    parts = module.split("/")
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) + ":factory"


def _entrypoint_path(source_tree: Mapping[str, str], entrypoint: str | None) -> str | None:
    if not isinstance(entrypoint, str) or ":" not in entrypoint:
        return None
    module, attribute = entrypoint.split(":", 1)
    if not attribute.isidentifier() or any(not part.isidentifier() for part in module.split(".")):
        return None
    base = module.replace(".", "/")
    matches = [path for path in (base + ".py", base + "/__init__.py") if path in source_tree]
    return matches[0] if len(matches) == 1 else None


@contextmanager
def _manifest_factory(source_tree: Mapping[str, str], entry_path: str, spec: FactorySpec):
    if spec.entrypoint is None:
        raise ImportError("manifest factory entrypoint is required")
    attribute = spec.entrypoint.split(":", 1)[1]
    with _manifest_module(source_tree, entry_path) as module:
        factory = getattr(module, attribute, None)
        if factory is None:
            raise ImportError("manifest factory entrypoint attribute is missing")
        yield factory


def _load_source_factory_module(source: str) -> ModuleType:
    """Import operator-authored factory source from a generated module file."""
    module_name = f"_qml_host_factory_{uuid.uuid4().hex}"  # ambient-scan: allow
    with tempfile.TemporaryDirectory(prefix="qml_host_factory_", ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "factory.py")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(source)
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError("factory source could not be loaded as a module")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(module_name, None)
        return module


def worker_main(stdin: TextIO | None = None, stdout: TextIO | None = None) -> int:
    """Child entry: collect observations, never evaluate the verdict."""
    inbound = (stdin or sys.stdin).read()
    outbound = stdout or sys.stdout
    try:
        raw: object = json.loads(inbound)
    except json.JSONDecodeError as exc:
        json.dump(
            _refusal_envelope(
                invalid(
                    "sandbox_payload",
                    "the isolated worker payload must be JSON",
                    given=str(exc),
                    layer=_LAYER,
                )
            ),
            outbound,
        )
        return 0
    observed = _worker_collect(raw)
    if is_refusal(observed):
        json.dump(_refusal_envelope(observed), outbound)
        return 0
    json.dump(
        {
            "ok": True,
            "observations": observed.value.fp1_identity(),
            "worker_pid": os.getpid(),
        },
        outbound,
    )
    return 0


def _worker_collect(raw: object) -> Result[Layer2Observations]:
    if not isinstance(raw, Mapping):
        return invalid(
            "sandbox_payload",
            "the isolated worker payload is a mapping",
            given=type(raw).__name__,
            layer=_LAYER,
        )
    mapping = cast("Mapping[str, object]", raw)
    blocked = _refuse_book_keys(mapping)
    if blocked is not None:
        return blocked
    spec = coerce_factory_spec(mapping.get("factory_spec"))
    if is_refusal(spec):
        return spec
    if spec.value.kind == FACTORY_KIND_SILENT:
        return policy(
            "factory_spec",
            "an explicit silent fixture cannot mint a production Layer-2 verdict",
            layer=_LAYER,
        )
    source = normalize_source_manifest(mapping.get("source_tree"))
    if is_refusal(source):
        return _journal(source)
    conventional = [item for item in source.value if item.rsplit("/", 1)[-1] == "factory.py"]
    expected_entrypoint = _module_entrypoint(conventional[0]) if len(conventional) == 1 else None
    if expected_entrypoint is None or spec.value.entrypoint != expected_entrypoint:
        return policy(
            "factory_spec",
            "the isolated worker selects the unique conventional factory.py:factory entrypoint",
            layer=_LAYER,
        )
    path = _entrypoint_path(source.value, spec.value.entrypoint)
    if path is None or source.value[path] != spec.value.source:
        return policy(
            "factory_spec",
            "the isolated conformance factory must match its declared source-manifest entrypoint",
            entrypoint=spec.value.entrypoint,
            layer=_LAYER,
        )
    try:
        with _manifest_factory(source.value, path, spec.value) as factory:
            return collect_layer2_observations(
                declaration=mapping.get("declaration"),
                factory=factory,
                source_tree=source.value,
                assignment=mapping.get("assignment"),
                state_scope=mapping.get("state_scope"),
                state_bound=mapping.get("state_bound"),
            )
    except Exception as exc:
        return unavailable(
            "factory_spec",
            "factory source failed to load from its manifest entrypoint",
            given=type(exc).__name__,
            layer=_LAYER,
        )


def _spawn_isolated(
    payload: Mapping[str, object], *, timeout_seconds: float | None
) -> Result[Mapping[str, object]]:
    try:
        completed = subprocess.run(
            [sys.executable, "-B", "-m", _WORKER_MODULE],
            input=json.dumps(_jsonable(dict(payload)), ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_seconds,
            env=_child_env(),
            start_new_session=True,
        )
    except subprocess.TimeoutExpired:
        return unavailable(
            "sandbox_process",
            "the isolated conformance process exceeded the host-supplied timeout",
            layer=_LAYER,
        )
    except OSError as exc:
        return unavailable(
            "sandbox_process",
            "stdlib process management could not spawn the isolated worker",
            given=type(exc).__name__,
            layer=_LAYER,
        )
    if completed.returncode != 0:
        return unavailable(
            "sandbox_process",
            "the isolated conformance process exited without observations",
            returncode=completed.returncode,
            stderr=completed.stderr[-2000:] if completed.stderr else "",
            layer=_LAYER,
        )
    try:
        parsed: object = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return unavailable(
            "sandbox_process",
            "the isolated conformance process did not return a JSON envelope",
            stdout=completed.stdout[-2000:] if completed.stdout else "",
            layer=_LAYER,
        )
    if not isinstance(parsed, dict):
        return unavailable(
            "sandbox_process",
            "the isolated conformance envelope is a mapping",
            given=type(parsed).__name__,
            layer=_LAYER,
        )
    return Ok(cast("dict[str, object]", parsed))


def _verdict_from_envelope(envelope: Mapping[str, object]) -> Result[Layer2Verdict]:
    ok = envelope.get("ok")
    if ok is True:
        return evaluate_layer2(envelope.get("observations"))
    if ok is False:
        return _typed_refusal_from_envelope(envelope)
    return unavailable(
        "sandbox_process",
        "the isolated conformance envelope must set ok true or false",
        layer=_LAYER,
    )


def _typed_refusal_from_envelope(envelope: Mapping[str, object]) -> Result[Layer2Verdict]:
    category = envelope.get("category")
    retryability = envelope.get("retryability", Retryability.NO.value)
    context = envelope.get("context", {})
    if not isinstance(category, str) or not isinstance(retryability, str):
        return unavailable(
            "sandbox_process",
            "a worker refusal envelope names category and retryability",
            layer=_LAYER,
        )
    if not isinstance(context, Mapping):
        return unavailable(
            "sandbox_process",
            "a worker refusal envelope carries a mapping context",
            layer=_LAYER,
        )
    try:
        parsed_category = RefusalCategory(category)
        parsed_retry = Retryability(retryability)
    except ValueError:
        return unavailable(
            "sandbox_process",
            "a worker refusal envelope uses CT-04 category and retryability tokens",
            layer=_LAYER,
        )
    descriptor = envelope.get("after_condition_descriptor")
    if descriptor is not None and not isinstance(descriptor, str):
        descriptor = None
    return TypedRefusal(
        category=parsed_category,
        retryability=parsed_retry,
        context=dict(cast("Mapping[str, object]", context)),
        after_condition_descriptor=descriptor,
    )


def _verdict_from_scan_findings(
    definition: BotDefinition, scan: ScanReport
) -> Result[Layer2Verdict]:
    decl_fp = definition.fingerprint_content()
    if is_refusal(decl_fp):
        return _journal(decl_fp)
    slice_ = generate_golden_slice(definition.footprint)
    if is_refusal(slice_):
        return _journal(slice_)
    slice_fp = slice_.value.fingerprint_content()
    if is_refusal(slice_fp):
        return _journal(slice_fp)
    return evaluate_layer2(
        Layer2Observations(
            loaded_in_isolation=True,
            book_present=False,
            scan=scan,
            golden_slice_fingerprint=slice_fp.value,
            declaration_fingerprint=decl_fp.value,
            first_run=(),
            second_run=(),
            emitted_kinds=(),
            permitted_exit_intents=definition.permitted_exit_intents,
            state_bound_holds=True,
            restore_equivalent=True,
        )
    )


def _encode_payload(
    *,
    definition: BotDefinition,
    source_tree: Mapping[str, str],
    factory_spec: FactorySpec,
    assignment: object,
    state_scope: object,
    state_bound: object,
) -> Result[dict[str, object]]:
    scope = _scope_payload(state_scope)
    if is_refusal(scope):
        return scope
    assigned: object = dict(definition.canonical_assignment()) if assignment is None else assignment
    payload: dict[str, object] = {
        "declaration": definition.identity_payload(),
        "source_tree": dict(source_tree),
        "factory_spec": {
            "kind": factory_spec.kind,
            "source": factory_spec.source,
            "entrypoint": factory_spec.entrypoint,
        },
        "assignment": assigned,
        "state_scope": scope.value,
        "state_bound": state_bound,
        "book_present": False,
        "read_surfaces_only": True,
    }
    blocked = _refuse_book_keys(payload)
    if blocked is not None:
        return blocked
    return Ok(payload)


def _scope_payload(state_scope: object) -> Result[Mapping[str, object]]:
    if isinstance(state_scope, BotStateScope):
        return Ok(state_scope.to_mapping())
    if isinstance(state_scope, Mapping):
        return Ok(cast("Mapping[str, object]", state_scope))
    return invalid(
        "state_scope",
        "a sandbox run injects a bot-state scope mapping; the OS is never read ambiently",
        given=type(state_scope).__name__,
        layer=_LAYER,
    )


def _validate_spec(kind: str, source: str, entrypoint: str | None = None) -> Result[FactorySpec]:
    if kind == FACTORY_KIND_SILENT:
        return Ok(FactorySpec(kind=FACTORY_KIND_SILENT))
    if kind != FACTORY_KIND_SOURCE:
        return invalid(
            "factory_spec",
            "factory_spec.kind is silent or source; a live callable cannot cross "
            "the process boundary",
            given=kind,
            layer=_LAYER,
        )
    if source.strip() == "":
        return invalid(
            "factory_spec",
            "source factory spec carries operator-authored Python that binds factory",
            layer=_LAYER,
        )
    blocked = _refuse_book(source)
    if blocked is not None:
        return blocked
    return Ok(FactorySpec(kind=FACTORY_KIND_SOURCE, source=source, entrypoint=entrypoint))


def _refuse_book_keys(mapping: Mapping[str, object]) -> TypedRefusal | None:
    overlap = _BOOK_KEYS.intersection(mapping)
    if not overlap:
        return None
    if mapping.get("book_present") is False and overlap == frozenset({"book_present"}):
        return None
    return policy(
        "no_book_present",
        "Layer 2 runs with no Book present or needed; hosts inject read surfaces only",
        layer=_LAYER,
        forbidden=tuple(sorted(overlap)),
    )


def _refuse_book(source: str) -> TypedRefusal | None:
    lowered = source.lower()
    if "book_module" in lowered or "inject_book" in lowered:
        return policy(
            "no_book_present",
            "Layer 2 runs with no Book present or needed; hosts inject read surfaces only",
            layer=_LAYER,
        )
    return None


def _admit_declaration(declaration: object) -> Result[BotDefinition]:
    if isinstance(declaration, BotDefinition):
        return Ok(declaration)
    return mint_bot_definition(declaration)


def _has_declared_seed(bot: BotDefinition) -> bool:
    for spec in bot.parameter_space:
        name = spec.name
        if name == _SEED_NAME or name.endswith("_seed"):
            return True
    return False


def _silent_logic(evidence: object) -> tuple[()]:
    del evidence
    return ()


def _coerce_timeout(value: object) -> Result[float | None]:
    if value is None:
        return Ok(None)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return invalid(
            "timeout_seconds",
            "a host-supplied sandbox timeout is a positive number of seconds",
            given=repr(value),
            layer=_LAYER,
        )
    if value <= 0:
        return invalid(
            "timeout_seconds",
            "a host-supplied sandbox timeout is a positive number of seconds",
            given=repr(value),
            layer=_LAYER,
        )
    return Ok(float(value))


def _child_env() -> dict[str, str]:
    env = dict(os.environ)
    extra = [item for item in sys.path if item]
    existing = env.get("PYTHONPATH", "")
    merged = extra + ([existing] if existing else [])
    env["PYTHONPATH"] = os.pathsep.join(merged)
    env["PYTHONNOUSERSITE"] = "1"
    return env


def _jsonable(value: object) -> object:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, Fingerprint):
        return value.value
    if isinstance(value, Enum):
        return value.value
    identity = getattr(value, "fp1_identity", None)
    if callable(identity):
        return _jsonable(identity())
    if isinstance(value, Mapping):
        mapping = cast("Mapping[object, object]", value)
        return {str(key): _jsonable(item) for key, item in mapping.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        items = cast("Sequence[object]", value)
        return [_jsonable(item) for item in items]
    return str(value)


def _refusal_envelope(refusal: TypedRefusal) -> dict[str, object]:
    envelope: dict[str, object] = {
        "ok": False,
        "category": refusal.category.value,
        "retryability": refusal.retryability.value,
        "context": _jsonable(dict(refusal.context)),
        "worker_pid": os.getpid(),
    }
    if refusal.after_condition_descriptor is not None:
        envelope["after_condition_descriptor"] = refusal.after_condition_descriptor
    return envelope


def _journal(refusal: TypedRefusal) -> TypedRefusal:
    extra: dict[str, object] = dict(refusal.context)
    extra["journal"] = True
    extra.setdefault("layer", _LAYER)
    return TypedRefusal(
        category=refusal.category,
        retryability=refusal.retryability,
        context=extra,
        after_condition_descriptor=refusal.after_condition_descriptor,
    )
