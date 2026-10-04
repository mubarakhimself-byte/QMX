"""Persistent research summaries behind QMX's existing memory admission gate.

This bounded provider stores the latest admitted summary per host-derived scope.
It is separate from invocation context and LangGraph checkpoints. LangMem may
later propose extracted candidates through the same gate; it is not a storage
or authorization substitute and no embedding/model service is enabled here.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass

from qma.core.ports.memory import MemoryCandidate, parse_memory_candidate
from qma.core.vocabulary.enums import MemoryValidationState
from qma.daemon.hooks.registry import HookRegistry
from qma.daemon.memory.admission import MemoryAdmissionGate
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection

from .graph_storage import JournalRecords
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


class _JournalSummaryProvider:
    """One exact scope, one latest summary; unsupported mutations fail closed."""

    def __init__(self, records: JournalRecords, scope: str, validate: Callable[[], None]) -> None:
        self.records = records
        self.scope = scope
        self.validate = validate

    def propose(self, candidate: MemoryCandidate) -> Result[MemoryCandidate]:
        return Ok(candidate)

    def admit(self, candidate: MemoryCandidate) -> Result[MemoryCandidate]:
        self.validate()
        if (
            candidate.scope != self.scope
            or candidate.validation_state != MemoryValidationState.ADMITTED
        ):
            return policy_rejection(
                "memory_scope", "Only gate-admitted memory in this scope is stored"
            )
        self.records.put("memory", self.scope, dict(candidate.to_payload()))
        return Ok(candidate)

    def recall(self, scope: str, token_budget: int) -> Result[tuple[MemoryCandidate, ...]]:
        self.validate()
        if scope != self.scope:
            return policy_rejection("memory_scope", "Memory recall cannot retarget host authority")
        body = self.records.get("memory", scope)
        if body is None or token_budget <= 0:
            return Ok(())
        # Conservative UTF-8 byte bound, not a count of returned memories.
        # No tokenizer or paid embedding service is needed for a bounded summary.
        if len(json.dumps(body, ensure_ascii=False).encode("utf-8")) > token_budget:
            return Ok(())
        parsed = parse_memory_candidate(body)
        if is_refusal(parsed):
            return parsed
        if parsed.value.validation_state != MemoryValidationState.ADMITTED:
            return Ok(())
        return Ok((parsed.value,))

    def get(self, memory_id: str) -> Result[MemoryCandidate]:
        recalled = self.recall(self.scope, 65_536)
        if is_refusal(recalled):
            return recalled
        if recalled.value and recalled.value[0].id == memory_id:
            return Ok(recalled.value[0])
        return invalid_input("memory_id", "No admitted summary with this id in the host scope")

    def list(self, scope: str) -> Result[tuple[MemoryCandidate, ...]]:
        return self.recall(scope, 65_536)

    def history(self, memory_id: str) -> Result[tuple[MemoryCandidate, ...]]:
        return policy_rejection("memory_history", "Historical memory queries are not exposed here")

    def supersede(self, memory_id: str, successor: MemoryCandidate) -> Result[MemoryCandidate]:
        return policy_rejection("memory_supersede", "Explicit memory editing is not enabled here")

    def invalidate(self, memory_id: str) -> Result[MemoryCandidate]:
        return policy_rejection("memory_invalidate", "Explicit memory editing is not enabled here")

    def expire(self, memory_id: str) -> Result[MemoryCandidate]:
        return policy_rejection("memory_expire", "Explicit memory editing is not enabled here")

    def scopes(self) -> Result[tuple[str, ...]]:
        self.validate()
        return Ok((self.scope,))


class ScopedResearchMemory:
    """Job-bound access to durable cross-job summaries with source provenance."""

    def __init__(
        self,
        records: JournalRecords,
        scope: ResearchMemoryScope,
        validate: Callable[[], None],
        *,
        hooks: HookRegistry | None = None,
        max_bytes: int = 8192,
    ) -> None:
        self.scope = scope
        self.max_bytes = max_bytes
        self.gate = MemoryAdmissionGate(hooks=hooks)
        bound = self.gate.bind(
            "research", _JournalSummaryProvider(records, scope.namespace, validate)
        )
        if is_refusal(bound):
            raise ProviderError("memory_denied", "Research memory provider binding refused")

    def recall(self) -> dict[str, object] | None:
        recalled = self.gate.recall(
            "research", scope=self.scope.namespace, token_budget=self.max_bytes
        )
        if is_refusal(recalled):
            raise ProviderError("memory_denied", "Research memory recall refused")
        if not recalled.value:
            return None
        return dict(recalled.value[-1].content)

    def retain(
        self,
        summary: str,
        *,
        request_id: str,
        specialist: str,
        occurrence_time: int,
        result_ref: str,
    ) -> None:
        if len(summary.encode("utf-8")) > self.max_bytes // 2:
            raise ProviderError("loop_limit", "Research summary exceeds memory byte budget")
        candidate = MemoryCandidate(
            id=f"{request_id}:summary",
            scope=self.scope.namespace,
            proposer=specialist,
            occurrence_time=occurrence_time,
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
                "summary": summary,
                "request_id": request_id,
                "snapshot_ref": self.scope.snapshot_ref,
            },
        )
        admitted = self.gate.admit("research", candidate)
        if is_refusal(admitted):
            raise ProviderError("memory_denied", "Research summary admission refused")
