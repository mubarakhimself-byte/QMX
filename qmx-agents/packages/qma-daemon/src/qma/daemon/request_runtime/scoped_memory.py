"""Research request facade over bounded typed durable memory.

This scope belongs to the admitted application/profile/corpus. It is not a
persistent actor identity. Actor memory uses explicit ActorMemoryScope instead.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass

from qma.core.ports.memory import MemoryCandidate, parse_memory_candidate
from qma.core.vocabulary.enums import MemoryValidationState
from qma.daemon.hooks.registry import HookRegistry
from qmf.core import is_refusal

from .durable_memory import DurableMemory, JournalMemoryProvider, MemoryLimits, MemorySource
from .graph_storage import JournalRecords
from .memory_projection import MemoryProjection
from .providers import ProviderError


@dataclass(frozen=True, slots=True)
class ResearchMemoryScope:
    principal: str
    application: str
    profile: str
    authority_binding: str
    source_id: str
    snapshot_ref: str
    locators: tuple[str, ...]

    @property
    def namespace(self) -> str:
        return (
            "research-summary:"
            + hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode("utf-8")).hexdigest()
        )


class ScopedResearchMemory:
    """Keep the existing request API; supersession now preserves typed history."""

    def __init__(
        self,
        records: JournalRecords,
        scope: ResearchMemoryScope,
        validate: Callable[[], None],
        *,
        hooks: HookRegistry | None = None,
        projection: Callable[[JournalMemoryProvider], MemoryProjection] | None = None,
        max_bytes: int = 8192,
        now_ns: Callable[[], int] = time.time_ns,
    ) -> None:
        self.scope, self.max_bytes = scope, max_bytes
        self.records, self.validate = records, validate
        self.provider = JournalMemoryProvider(
            records,
            scope.namespace,
            MemorySource(
                scope.source_id, scope.snapshot_ref, scope.locators, scope.authority_binding
            ),
            validate,
            now_ns=now_ns,
            limits=MemoryLimits(max_record_bytes=min(65536, max_bytes + 8192)),
        )
        self.projection = projection(self.provider) if projection else self.provider
        self.memory = DurableMemory(self.provider, projection=self.projection, hooks=hooks)
        self.gate = self.memory.gate

    def recall(self) -> dict[str, object] | None:
        recalled = self.projection.search(memory_type="summary")
        if is_refusal(recalled):
            raise ProviderError("memory_denied", "Research memory recall refused")
        for candidate in recalled.value:
            body = dict(candidate.content)
            # Preserve the workflow's summary field without duplicating text
            # in the invocation's byte budget or canonical record.
            body["summary"] = body.pop("text")
            if len(json.dumps(body, ensure_ascii=False).encode("utf-8")) <= self.max_bytes:
                self.projection.validate_selection((candidate,))
                return body
        if self.projection is not self.provider:
            return None
        # Read-only compatibility for previous exact-scope summaries. Once typed
        # state exists, never fall back and resurrect invalidated memory.
        with self.provider.lock:
            self.validate()
            if self.records.get("typed_memory", self.scope.namespace) is not None:
                return None
            legacy = self.records.get("memory", self.scope.namespace)
            if (
                legacy is None
                or len(json.dumps(legacy, ensure_ascii=False).encode("utf-8")) > self.max_bytes
            ):
                return None
            parsed = parse_memory_candidate(legacy)
            if is_refusal(parsed):
                raise ProviderError("storage_failure", "Invalid legacy research memory")
            candidate = parsed.value
            source = self.provider.source
            if (
                candidate.scope != self.scope.namespace
                or candidate.validation_state != MemoryValidationState.ADMITTED
                or not candidate.provenance
                or any(
                    candidate.provenance.get(key) != getattr(source, key)
                    for key in ("source_id", "snapshot_ref", "authority_binding")
                )
                or candidate.provenance.get("locators") != list(source.locators)
            ):
                raise ProviderError("memory_denied", "Legacy memory is outside current host pins")
            self.validate()
            expires = candidate.content.get("expires_at_ns")
            if expires is not None:
                if type(expires) is not int or expires <= candidate.occurrence_time:
                    raise ProviderError("storage_failure", "Invalid legacy memory expiration")
                now = self.provider.now_ns()
                if type(now) is not int:
                    raise ProviderError(
                        "memory_denied", "Host memory clock must supply integer nanoseconds"
                    )
                if now >= expires:
                    return None
            return dict(candidate.content)

    def retain(
        self,
        summary: str,
        *,
        request_id: str,
        specialist: str,
        occurrence_time: int,
        result_ref: str,
    ) -> None:
        if not summary.strip() or len(summary.encode("utf-8")) > self.max_bytes // 2:
            raise ProviderError("loop_limit", "Research summary exceeds memory byte budget")
        with self.provider.lock:
            active = self.provider.search(memory_type="summary")
            if is_refusal(active):
                raise ProviderError("memory_denied", "Research memory predecessor lookup refused")
            memory_id = f"{request_id}:summary"
            # Freeze retry identity, including predecessor. An interrupted retain
            # never recomputes supersession to point at itself or a newer job.
            history = self.provider.history(memory_id)
            if is_refusal(history):
                raise ProviderError("memory_denied", "Research memory history refused")
            prior = (
                history.value[0].supersession
                if history.value
                else (active.value[0].id if active.value else None)
            )
            candidate = MemoryCandidate(
                id=memory_id,
                scope=self.scope.namespace,
                proposer=specialist,
                occurrence_time=occurrence_time,
                supersession=prior,
                provenance={
                    "request_id": request_id,
                    "source_id": self.scope.source_id,
                    "snapshot_ref": self.scope.snapshot_ref,
                    "locators": list(self.scope.locators),
                    "authority_binding": self.scope.authority_binding,
                    "summary_sha256": hashlib.sha256(summary.encode("utf-8")).hexdigest(),
                },
                supporting_artifacts=(result_ref,),
                content={
                    "memory_type": "summary",
                    "text": summary,
                    "request_id": request_id,
                    "snapshot_ref": self.scope.snapshot_ref,
                },
            )
            self.memory.admit(candidate)
