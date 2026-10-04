"""Typed recall projection over CT-43; the journal owns admission and retirement.

Only host-admitted recall/injection is supported. No provider write, sync,
extraction, prompt hook, discovery import or tool callback is invoked here.
"""

from __future__ import annotations

# pyright: reportUnnecessaryIsInstance=false
# Reject malformed runtime provider output and operator configuration at the boundary.
import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Protocol, cast, runtime_checkable

from qma.core.ports.memory import MemoryCandidate, MemoryProvider
from qma.daemon.plugins.loader import LoadedPlugin, PluginLoader
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection

from .contracts import RequestSpec
from .durable_memory import JournalMemoryProvider, MemoryLimits, MemoryType, encoded
from .providers import ProviderError


@runtime_checkable
class MemoryProjection(Protocol):
    """The extra context-selection capabilities, separate from CT-43 CRUD."""

    @property
    def limits(self) -> MemoryLimits: ...
    @property
    def validate(self) -> Callable[[], None]: ...
    def search(
        self,
        *,
        memory_type: MemoryType | None = None,
        query: str | None = None,
        limit: int | None = None,
    ) -> Result[tuple[MemoryCandidate, ...]]: ...
    def validate_selection(self, candidates: tuple[MemoryCandidate, ...]) -> None: ...


def _json_value(body: object) -> object:
    if is_dataclass(body) and not isinstance(body, type):
        return {f.name: _json_value(getattr(body, f.name)) for f in fields(body)}
    if isinstance(body, Mapping):
        return {
            key: _json_value(value) for key, value in cast("Mapping[str, object]", body).items()
        }
    if isinstance(body, (list, tuple)):
        return [_json_value(value) for value in cast("list[object] | tuple[object, ...]", body)]
    return body


def _digest(body: object) -> str:
    return hashlib.sha256(encoded(body)).hexdigest()


@dataclass(frozen=True)
class SelectedMemoryProvider:
    desk: str
    loaded: LoadedPlugin
    provider: MemoryProvider
    config_revision: int
    config_sha256: str
    manifest_sha256: str
    credential_refs_sha256: str

    def pin(self) -> dict[str, object]:
        return {
            "desk": self.desk,
            "plugin_id": self.loaded.manifest.id,
            "plugin_version": self.loaded.manifest.version,
            "config_revision": self.config_revision,
            "config_sha256": self.config_sha256,
            "manifest_sha256": self.manifest_sha256,
            "credential_refs_sha256": self.credential_refs_sha256,
            "admission": "journal_projection_v1",
            "policy": {"recall": True, "injection": True},
        }


class HostMemoryBindings:
    """Immutable startup selections, validated against live plugin contributions."""

    def __init__(
        self, loader: PluginLoader, selected: tuple[SelectedMemoryProvider, ...] = ()
    ) -> None:
        self.loader, self.selected = loader, selected
        self.identity = _digest([s.pin() for s in selected]) if selected else None

    def validate(self, expected: str | None) -> None:
        if expected != self.identity:
            raise ProviderError("context_changed", "Original memory provider binding unavailable")
        try:
            for s in self.selected:
                live = self.loader.get(s.loaded.manifest.id)
                if (
                    live is None
                    or live is not s.loaded
                    or live.exit_stack.closed
                    or _digest(dict(live.context.load_config)) != s.config_sha256
                    or _digest(_json_value(live.manifest)) != s.manifest_sha256
                    or _digest(_json_value(live.context.snapshot()["credential_refs"]))
                    != s.credential_refs_sha256
                    or live.context.snapshot()["singletons"].get(("MemoryProvider", s.desk))
                    is not s.provider
                ):
                    raise ProviderError("context_changed", "Memory plugin was unloaded or changed")
        except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
            raise ProviderError(
                "context_changed", "Memory plugin configuration is invalid"
            ) from exc

    def bind(self) -> Result[str | None]:
        try:
            self.validate(self.identity)
        except ProviderError:
            return policy_rejection("memory_provider", "Host memory binding is unavailable")
        return Ok(self.identity)

    def project(
        self, spec: RequestSpec, canonical: JournalMemoryProvider, *, desk: str, request_id: str
    ) -> MemoryProjection:
        self.validate(spec.memory_binding_sha256)
        selected = next((s for s in self.selected if s.desk == desk), None)
        if selected is None:
            return canonical
        return ProviderMemoryProjection(
            canonical,
            selected.provider,
            lambda: self.validate(spec.memory_binding_sha256),
            binding=self.identity or "",
            request_id=request_id,
        )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate memory configuration key")
        result[key] = value
    return result


def load_memory_bindings(root: Path, loader: PluginLoader) -> Result[HostMemoryBindings]:
    """Read bounded host configuration; never import/install/probe a backend."""
    path = root / "memory-providers.json"
    if not path.exists():
        return Ok(HostMemoryBindings(loader))
    try:
        if path.stat().st_size > 32768:
            raise ValueError("memory configuration exceeds byte budget")
        raw: object = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        body = cast("dict[str, object]", raw)
        if not isinstance(body, dict) or set(body) != {"version", "desks"}:
            raise ValueError("memory configuration requires version and desks only")
        if type(body["version"]) is not int or body["version"] != 1:
            raise ValueError("unknown memory configuration version")
        desks = body["desks"]
        if not isinstance(desks, dict) or len(cast("dict[str, object]", desks)) > 16:
            raise ValueError("memory desks must be a bounded mapping")
        selected: list[SelectedMemoryProvider] = []
        for desk, raw_config in sorted(cast("dict[str, object]", desks).items()):
            config = cast("dict[str, object]", raw_config)
            if not isinstance(desk, str) or not desk.strip() or desk != desk.strip():
                raise ValueError("memory desk must be an exact nonempty host key")
            if not isinstance(config, dict) or set(config) != {
                "plugin_id",
                "plugin_version",
                "config_revision",
                "admission",
                "policy",
            }:
                raise ValueError(
                    "memory selection requires explicit plugin/config/admission/policy"
                )
            if (
                type(config["config_revision"]) is not int
                or config["config_revision"] < 1
                or config["admission"] != "journal_projection_v1"
                or config["policy"] != {"recall": True, "injection": True}
                or any(
                    type(v) is not bool
                    for v in cast("dict[str, object]", config["policy"]).values()
                )
            ):
                raise ValueError("only explicitly admitted recall and injection are supported")
            if not isinstance(config["plugin_id"], str):
                raise ValueError("memory plugin id must be text")
            loaded = loader.get(config["plugin_id"])
            if loaded is None or loaded.manifest.version != config["plugin_version"]:
                raise ValueError("selected memory plugin/version is unavailable; no fallback")
            provider = loaded.context.snapshot()["singletons"].get(("MemoryProvider", desk))
            if not isinstance(provider, MemoryProvider):
                raise ValueError("selected plugin has no CT-43 singleton for the desk")
            selected.append(
                SelectedMemoryProvider(
                    desk,
                    loaded,
                    provider,
                    config["config_revision"],
                    _digest(dict(loaded.context.load_config)),
                    _digest(_json_value(loaded.manifest)),
                    _digest(_json_value(loaded.context.snapshot()["credential_refs"])),
                )
            )
        result = HostMemoryBindings(loader, tuple(selected))
        result.validate(result.identity)
        return Ok(result)
    except OSError, ValueError, TypeError, KeyError, ProviderError:
        return invalid_input("memory_providers", "Host memory provider configuration refused")


class ProviderMemoryProjection:
    """Ranked suggestions are disclosed only as matching current journal heads.

    The server supplies the complete scope. Provider content cannot create,
    update or resurrect memory. Receipts contain only accepted journal refs.
    A lost callback result requires explicit reconciliation, never silent replay.
    """

    def __init__(
        self,
        canonical: JournalMemoryProvider,
        provider: MemoryProvider,
        validate_binding: Callable[[], None],
        *,
        binding: str,
        request_id: str,
    ) -> None:
        self.canonical, self.provider = canonical, provider
        self.validate_binding, self.binding = validate_binding, binding
        self.limits = canonical.limits
        self.effect_key = request_id + ":memory-recall:" + canonical.scope

    def validate(self) -> None:
        self.validate_binding()
        self.canonical.validate()

    def validate_selection(self, candidates: tuple[MemoryCandidate, ...]) -> None:
        self.validate()
        self.canonical.validate_selection(candidates)
        self.validate()

    def search(
        self,
        *,
        memory_type: MemoryType | None = None,
        query: str | None = None,
        limit: int | None = None,
    ) -> Result[tuple[MemoryCandidate, ...]]:
        self.validate()
        if query is not None:
            return policy_rejection("memory_query", "CT-43 projection has no query operation")
        cap = self.limits.max_records if limit is None else limit
        if type(cap) is not int or not 0 < cap <= self.limits.max_records:
            return invalid_input("memory_limit", "Projection count must be bounded")
        if memory_type is not None and memory_type not in {
            "summary",
            "semantic",
            "episodic",
            "procedural",
        }:
            return invalid_input("memory_type", "Unknown memory type")
        with self.canonical.lock:
            records = self.canonical.records
            receipt = records.get("memory_projection_effect", self.effect_key)
            if receipt is None:
                intent = {
                    "status": "intent",
                    "scope": self.canonical.scope,
                    "binding": self.binding,
                    "effect_class": "read",
                }
                self.validate()
                records.put("memory_projection_effect", self.effect_key, intent)
                recalled = self.provider.recall(self.canonical.scope, self.limits.max_scope_bytes)
                self.validate()
                if is_refusal(recalled):
                    raise ProviderError("memory_denied", "Selected memory provider refused recall")
                if (
                    not isinstance(recalled, Ok)
                    or not isinstance(recalled.value, tuple)
                    or len(recalled.value) > self.limits.max_records
                ):
                    raise ProviderError("memory_denied", "Provider projection exceeds record cap")
                refs: list[dict[str, str]] = []
                seen: set[str] = set()
                total = 0
                for proposed in recalled.value:
                    if not isinstance(proposed, MemoryCandidate):
                        raise ProviderError("memory_denied", "Provider returned invalid candidate")
                    try:
                        payload = encoded(dict(proposed.to_payload()))
                    except (ValueError, TypeError, UnicodeError) as exc:
                        raise ProviderError(
                            "memory_denied", "Invalid provider memory bytes"
                        ) from exc
                    total += len(payload)
                    if (
                        len(payload) > self.limits.max_record_bytes
                        or total > self.limits.max_scope_bytes
                    ):
                        raise ProviderError("memory_denied", "Provider projection exceeds byte cap")
                    current = self.canonical.get(proposed.id)
                    if (
                        proposed.scope != self.canonical.scope
                        or is_refusal(current)
                        or current.value != proposed
                        or proposed.id in seen
                    ):
                        continue
                    seen.add(proposed.id)
                    refs.append({"id": proposed.id, "sha256": _digest(dict(proposed.to_payload()))})
                self.validate()
                receipt = {**intent, "status": "observed", "selection": refs}
                records.put("memory_projection_effect", self.effect_key, receipt)
            if (
                receipt.get("status") != "observed"
                or receipt.get("binding") != self.binding
                or receipt.get("scope") != self.canonical.scope
            ):
                raise ProviderError(
                    "outcome_unknown", "Memory recall receipt requires reconciliation"
                )
            raw_refs: object = receipt.get("selection")
            if (
                not isinstance(raw_refs, list)
                or len(cast("list[object]", raw_refs)) > self.limits.max_records
            ):
                raise ProviderError("storage_failure", "Invalid memory recall receipt")
            receipt_refs = cast("list[Mapping[str, str]]", raw_refs)
            if any(
                not isinstance(ref, dict)
                or set(ref) != {"id", "sha256"}
                or not isinstance(ref["id"], str)
                or not ref["id"]
                or not isinstance(ref["sha256"], str)
                or len(ref["sha256"]) != 64
                for ref in receipt_refs
            ):
                raise ProviderError("storage_failure", "Invalid memory recall reference")
            chosen: list[MemoryCandidate] = []
            for ref in receipt_refs:
                current = self.canonical.get(ref["id"])
                if (
                    not is_refusal(current)
                    and _digest(dict(current.value.to_payload())) == ref["sha256"]
                    and (memory_type is None or current.value.content["memory_type"] == memory_type)
                ):
                    chosen.append(current.value)
            selected = tuple(chosen[:cap])
            self.validate_selection(selected)
            return Ok(selected)
