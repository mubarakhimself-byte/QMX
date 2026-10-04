"""Bounded CT-43 journal adapter; SDK Store is a disposable search projection.

Host bindings and live validation supply authority. Model output never selects
scope, embeddings, source pins or persistent actor identity. No second writer,
automatic model call, background TTL thread or autonomous reflection is added.
"""

from __future__ import annotations

# pyright: reportUnnecessaryIsInstance=false
# These boundary checks deliberately reject incorrectly typed host configuration.
import hashlib
import json
import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from typing import TYPE_CHECKING, Any, Literal, cast
from weakref import WeakKeyDictionary

from langchain_core.embeddings import Embeddings
from langgraph.store.base import IndexConfig
from langgraph.store.memory import InMemoryStore
from qma.core.ports.memory import MemoryCandidate, MemoryProvider, parse_memory_candidate
from qma.core.vocabulary.enums import MemoryValidationState as State
from qma.daemon.hooks.registry import HookRegistry
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.memory.admission import MemoryAdmissionGate
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection

from .graph_storage import JournalRecords
from .providers import ProviderError

if TYPE_CHECKING:
    from .memory_projection import MemoryProjection

MemoryType = Literal["summary", "semantic", "episodic", "procedural"]
MEMORY_TYPES = frozenset({"summary", "semantic", "episodic", "procedural"})
_locks: WeakKeyDictionary[AuthoritativeJournal, Any] = WeakKeyDictionary()
_locks_guard = threading.Lock()


def encoded(body: object) -> bytes:
    return json.dumps(
        body, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _positive(value: int, name: str, ceiling: int) -> None:
    if type(value) is not int or not 0 < value <= ceiling:
        raise ValueError(f"{name} must be a positive bounded integer")


@dataclass(frozen=True, slots=True)
class MemorySource:
    source_id: str
    snapshot_ref: str
    locators: tuple[str, ...]
    authority_binding: str

    def __post_init__(self) -> None:
        if any(
            not isinstance(x, str) or not x.strip()
            for x in (self.source_id, self.snapshot_ref, self.authority_binding)
        ):
            raise ValueError("memory requires explicit source and authority pins")
        if (
            not isinstance(self.locators, tuple)
            or not 0 < len(self.locators) <= 64
            or len(set(self.locators)) != len(self.locators)
            or any(not isinstance(x, str) or not x.strip() for x in self.locators)
        ):
            raise ValueError("memory requires bounded unique source locators")


@dataclass(frozen=True, slots=True)
class ActorMemoryScope:
    """Explicit durable actor identity, independent of invocation/thread/app IDs."""

    principal: str
    actor_id: str
    collection: str
    source: MemorySource

    def __post_init__(self) -> None:
        if any(
            not isinstance(x, str) or not x.strip()
            for x in (self.principal, self.actor_id, self.collection)
        ):
            raise ValueError("actor memory requires an explicit host actor identity")

    @property
    def namespace(self) -> str:
        return "actor-memory:" + hashlib.sha256(encoded(asdict(self))).hexdigest()


@dataclass(frozen=True, slots=True)
class MemoryLimits:
    max_records: int = 64
    max_revisions: int = 256
    max_record_bytes: int = 32768
    max_scope_bytes: int = 524288

    def __post_init__(self) -> None:
        for name, ceiling in (
            ("max_records", 128),
            ("max_revisions", 512),
            ("max_record_bytes", 65536),
            ("max_scope_bytes", 1048576),
        ):
            _positive(getattr(self, name), name, ceiling)


DEFAULT_LIMITS = MemoryLimits()


class JournalMemoryProvider:
    """Small exact-scope port adapter using atomic bounded journal snapshots.

    Each write appends a whole scope state in one existing journal event. That
    keeps supersession and its successor atomic. History includes terminal
    states; ordinary get/list/recall/search expose only admitted, unexpired heads.
    Tombstones preserve audit history; invalidation is not erasure of journal bytes.
    """

    def __init__(
        self,
        records: JournalRecords,
        scope: str,
        source: MemorySource,
        validate: Callable[[], None],
        *,
        now_ns: Callable[[], int],
        limits: MemoryLimits = DEFAULT_LIMITS,
        embeddings: Embeddings | None = None,
        embedding_dims: int | None = None,
    ) -> None:
        if not isinstance(scope, str) or not scope.strip():
            raise ValueError("memory requires exact host scope")
        if embeddings is not None:
            if not isinstance(embeddings, Embeddings):
                raise ValueError("embedding backend must be an explicit injected Embeddings object")
            _positive(embedding_dims, "embedding_dims", 65536)  # type: ignore[arg-type]
        elif embedding_dims is not None:
            raise ValueError("dimensions require an explicit embedding backend")
        self.records, self.scope, self.source = records, scope, source
        self.validate, self.now_ns, self.limits = validate, now_ns, limits
        self.embeddings, self.embedding_dims = embeddings, embedding_dims
        with _locks_guard:
            self.lock = _locks.setdefault(records.journal, threading.RLock())

    def _state(self) -> dict[str, Any]:
        self.validate()
        body = self.records.get("typed_memory", self.scope)
        if body is None:
            return {"version": 1, "scope": self.scope, "revisions": []}
        if (
            body.get("version") != 1
            or body.get("scope") != self.scope
            or not isinstance(body.get("revisions"), list)
            or len(body["revisions"]) > self.limits.max_revisions
            or len(encoded(body)) > self.limits.max_scope_bytes
        ):
            raise ProviderError("storage_failure", "Invalid bounded memory state")
        for payload in body["revisions"]:
            parsed = parse_memory_candidate(payload)
            if is_refusal(parsed) or self._check(parsed.value, admitted=False) is not None:
                raise ProviderError("storage_failure", "Invalid memory record or source pin")
        if len(self._heads(body)) > self.limits.max_records:
            raise ProviderError("storage_failure", "Stored memory exceeds current host record cap")
        return body

    def _check(self, candidate: MemoryCandidate, *, admitted: bool = True) -> Any:
        if (
            candidate.scope != self.scope
            or not candidate.provenance
            or not candidate.proposer.strip()
            or not candidate.id.strip()
            or type(candidate.occurrence_time) is not int
            or not candidate.supporting_artifacts
            or any(not x.strip() for x in candidate.supporting_artifacts)
        ):
            return policy_rejection("memory_scope", "Memory requires exact scope and provenance")
        if admitted and (
            candidate.validation_state != State.ADMITTED or candidate.admission_confidence is None
        ):
            return policy_rejection("memory_admission", "Memory must pass the admission gate")
        p = candidate.provenance
        if any(
            p.get(key) != getattr(self.source, key)
            for key in ("source_id", "snapshot_ref", "authority_binding")
        ):
            return policy_rejection("memory_source", "Memory source is outside host pins")
        locators = p.get("locators")
        if (
            not isinstance(locators, (list, tuple))
            or not locators
            or any(
                not isinstance(x, str) or x not in self.source.locators
                for x in cast("list[object] | tuple[object, ...]", locators)
            )
        ):
            return policy_rejection("memory_source", "Memory locator is outside host pins")
        if candidate.content.get("memory_type") not in MEMORY_TYPES:
            return invalid_input("memory_type", "Memory requires a supported explicit type")
        text = candidate.content.get("text")
        if not isinstance(text, str) or not text.strip():
            return invalid_input("memory_text", "Memory text must be nonempty")
        expires = candidate.content.get("expires_at_ns")
        if expires is not None and (
            type(expires) is not int or expires <= candidate.occurrence_time
        ):
            return invalid_input("memory_expiration", "Expiration must follow occurrence time")
        try:
            if len(encoded(dict(candidate.to_payload()))) > self.limits.max_record_bytes:
                return invalid_input("memory_budget", "Memory record exceeds byte budget")
        except ValueError, TypeError, UnicodeError:
            return invalid_input("memory_payload", "Memory must be finite UTF-8 JSON")
        return None

    @staticmethod
    def _heads(body: dict[str, Any]) -> dict[str, MemoryCandidate]:
        heads: dict[str, MemoryCandidate] = {}
        for payload in body["revisions"]:
            result = parse_memory_candidate(payload)
            if is_refusal(result):
                raise ProviderError("storage_failure", "Invalid memory revision")
            heads[result.value.id] = result.value
        return heads

    def _active(self, candidate: MemoryCandidate) -> bool:
        now = self.now_ns()
        if type(now) is not int:
            raise ProviderError(
                "memory_denied", "Host memory clock must supply integer nanoseconds"
            )
        expires = candidate.content.get("expires_at_ns")
        return candidate.validation_state == State.ADMITTED and (
            expires is None or (isinstance(expires, int) and now < expires)
        )

    def _put(self, body: dict[str, Any], revisions: tuple[MemoryCandidate, ...]) -> Result[None]:
        for candidate in revisions:
            refusal = self._check(candidate, admitted=False)
            if refusal is not None:
                return refusal
        updated = {
            **body,
            "revisions": [*body["revisions"], *(dict(c.to_payload()) for c in revisions)],
        }
        if (
            len(updated["revisions"]) > self.limits.max_revisions
            or len(self._heads(updated)) > self.limits.max_records
            or len(encoded(updated)) > self.limits.max_scope_bytes
        ):
            return policy_rejection("memory_capacity", "Bounded memory capacity exhausted")
        self.validate()
        self.records.put("typed_memory", self.scope, updated)
        return Ok(None)

    def propose(self, candidate: MemoryCandidate) -> Result[MemoryCandidate]:
        self.validate()
        refusal = self._check(candidate)
        return refusal if refusal is not None else Ok(candidate)

    def admit(self, candidate: MemoryCandidate) -> Result[MemoryCandidate]:
        with self.lock:
            body = self._state()
            refusal = self._check(candidate)
            if refusal is not None:
                return refusal
            heads = self._heads(body)
            existing = heads.get(candidate.id)
            if existing is not None:
                # Retry cannot resurrect a tombstone or overwrite immutable content.
                if dict(existing.to_payload()) == dict(candidate.to_payload()):
                    self.validate()
                    return Ok(existing)
                return policy_rejection(
                    "memory_conflict", "Memory id is immutable and already used"
                )
            revisions = (candidate,)
            if candidate.supersession is not None:
                prior = heads.get(candidate.supersession)
                if prior is None or not self._active(prior):
                    return policy_rejection(
                        "memory_supersession", "Predecessor must be active in this scope"
                    )
                revisions = (
                    replace(
                        prior,
                        validation_state=State.SUPERSEDED,
                        validation_history=(*prior.validation_history, "superseded"),
                    ),
                    candidate,
                )
            if not self._active(candidate):
                return policy_rejection("memory_expiration", "Cannot admit already expired memory")
            saved = self._put(body, revisions)
            return saved if is_refusal(saved) else Ok(candidate)

    def search(
        self,
        *,
        memory_type: MemoryType | None = None,
        query: str | None = None,
        limit: int | None = None,
    ) -> Result[tuple[MemoryCandidate, ...]]:
        if limit is None:
            limit = self.limits.max_records
        _positive(limit, "limit", self.limits.max_records)
        if memory_type is not None and memory_type not in MEMORY_TYPES:
            return invalid_input("memory_type", "Unknown memory type")
        if query is not None and (
            not isinstance(query, str) or not query.strip() or len(query.encode("utf-8")) > 4096
        ):
            return invalid_input("memory_query", "Query must be nonempty bounded UTF-8")
        with self.lock:
            body = self._state()
            if query is not None and self.embeddings is None:
                return policy_rejection(
                    "memory_search", "Semantic search requires an explicit embedding backend"
                )
            active = {c.id: c for c in self._heads(body).values() if self._active(c)}
            # Fresh projection includes only currently authorized active canonical
            # bytes; no tombstones or other scopes enter a supplied embedder.
            self.validate()
            index: IndexConfig | None = None
            if query is not None:
                if self.embedding_dims is None or self.embeddings is None:
                    raise ProviderError("memory_denied", "Embedding backend is not configured")
                index = {"dims": self.embedding_dims, "embed": self.embeddings, "fields": ["text"]}
            store = InMemoryStore(index=index)
            namespace = ("qma-memory", self.scope)
            ordered = sorted(active.values(), key=lambda c: (-c.occurrence_time, c.id))
            for c in ordered:
                self.validate()
                # An injected backend may advance the clock or retire another
                # record. Recheck canonical state before each document leaves.
                current = self._heads(self._state()).get(c.id)
                if current != c or not self._active(c):
                    continue
                store.put(
                    namespace,
                    c.id,
                    {"memory_type": c.content["memory_type"], "text": c.content["text"]},
                )
            self.validate()
            results = store.search(
                namespace,
                query=query,
                filter={"memory_type": memory_type} if memory_type else None,
                limit=limit,
            )
            self.validate()
            current_heads = self._heads(self._state())
            return Ok(
                tuple(
                    active[item.key]
                    for item in results
                    if item.namespace == namespace
                    and item.key in active
                    and current_heads.get(item.key) == active[item.key]
                    and self._active(active[item.key])
                )
            )

    def recall(self, scope: str, token_budget: int) -> Result[tuple[MemoryCandidate, ...]]:
        self.validate()
        if scope != self.scope:
            return policy_rejection("memory_scope", "Recall cannot retarget host authority")
        if type(token_budget) is not int or token_budget < 0:
            return invalid_input("token_budget", "Token budget must be nonnegative integer")
        recalled = self.search(limit=self.limits.max_records)
        if is_refusal(recalled):
            return recalled
        chosen: list[MemoryCandidate] = []
        remaining = token_budget
        for c in recalled.value:
            # UTF-8 bytes conservatively bound byte-level tokenization.
            size = len(encoded(dict(c.to_payload())))
            if size <= remaining:
                chosen.append(c)
                remaining -= size
        self.validate_selection(tuple(chosen))
        return Ok(tuple(chosen))

    def get(self, memory_id: str) -> Result[MemoryCandidate]:
        with self.lock:
            candidate = self._heads(self._state()).get(memory_id)
            self.validate()
            if candidate is None or not self._active(candidate):
                return invalid_input("memory_id", "No active memory with this id in host scope")
            return Ok(candidate)

    def list(self, scope: str) -> Result[tuple[MemoryCandidate, ...]]:
        return self.recall(scope, self.limits.max_scope_bytes)

    def history(self, memory_id: str) -> Result[tuple[MemoryCandidate, ...]]:
        with self.lock:
            body = self._state()
            history: list[MemoryCandidate] = []
            for payload in body["revisions"]:
                if payload["id"] != memory_id:
                    continue
                parsed = parse_memory_candidate(payload)
                if is_refusal(parsed):
                    raise ProviderError("storage_failure", "Invalid memory history")
                history.append(parsed.value)
            self.validate()
            return Ok(tuple(history))

    def supersede(self, memory_id: str, successor: MemoryCandidate) -> Result[MemoryCandidate]:
        self.validate()
        if successor.supersession != memory_id:
            return policy_rejection(
                "memory_supersession", "Gate-admitted successor must name predecessor"
            )
        return self.admit(successor)

    def _terminal(self, memory_id: str, state: State) -> Result[MemoryCandidate]:
        with self.lock:
            body = self._state()
            prior = self._heads(body).get(memory_id)
            if prior is None:
                return invalid_input("memory_id", "No memory with this id in host scope")
            if prior.validation_state == state:
                self.validate()
                return Ok(prior)
            if prior.validation_state != State.ADMITTED:
                return policy_rejection(
                    "memory_state", "Terminal memory cannot change or resurrect"
                )
            candidate = replace(
                prior,
                validation_state=state,
                validation_history=(*prior.validation_history, state.value),
            )
            saved = self._put(body, (candidate,))
            return saved if is_refusal(saved) else Ok(candidate)

    def invalidate(self, memory_id: str) -> Result[MemoryCandidate]:
        return self._terminal(memory_id, State.INVALIDATED)

    def expire(self, memory_id: str) -> Result[MemoryCandidate]:
        return self._terminal(memory_id, State.EXPIRED)

    def scopes(self) -> Result[tuple[str, ...]]:
        self.validate()
        return Ok((self.scope,))

    def validate_selection(self, candidates: tuple[MemoryCandidate, ...]) -> None:
        """Revalidate a rendered selection after potentially slow host callbacks."""
        with self.lock:
            current = self._heads(self._state())
            if any(current.get(c.id) != c or not self._active(c) for c in candidates):
                raise ProviderError("context_changed", "Memory changed during context assembly")
            self.validate()


class DurableMemory:
    """Host-only admission facade. Skills and extraction cannot choose its binding."""

    def __init__(
        self,
        provider: MemoryProvider,
        *,
        projection: MemoryProjection | None = None,
        desk: str = "research",
        hooks: HookRegistry | None = None,
    ) -> None:
        from .memory_projection import MemoryProjection  # noqa: PLC0415

        if projection is None:
            if not isinstance(provider, MemoryProjection):
                raise ValueError("Memory context requires an explicit typed projection")
            projection = provider
        self.provider, self.desk = provider, desk
        self.projection = projection
        self.gate = MemoryAdmissionGate(hooks=hooks)
        result = self.gate.bind(desk, provider)
        if is_refusal(result):
            raise ProviderError("memory_denied", "Memory provider binding refused")

    def admit(self, candidate: MemoryCandidate) -> MemoryCandidate:
        result = self.gate.admit(self.desk, candidate)
        if is_refusal(result):
            raise ProviderError("memory_denied", "Memory candidate admission refused")
        admitted_candidate = result.value.candidate
        if admitted_candidate is None:
            raise ProviderError("memory_denied", "Memory admission produced no candidate")
        return admitted_candidate

    def context(
        self,
        *,
        max_bytes: int,
        max_tokens: int,
        memory_type: MemoryType | None = None,
        query: str | None = None,
        count_tokens: Callable[[str], int] | None = None,
    ) -> str:
        """Render a bounded subset. Omission never edits canonical records."""
        _positive(max_bytes, "max_bytes", 1048576)
        _positive(max_tokens, "max_tokens", 1048576)
        results = self.projection.search(
            memory_type=memory_type, query=query, limit=self.projection.limits.max_records
        )
        if is_refusal(results):
            raise ProviderError("memory_denied", "Memory search refused")
        chosen: list[dict[str, object]] = []
        rendered = ""
        for candidate in results.value:
            entry = {
                "id": candidate.id,
                "memory_type": candidate.content["memory_type"],
                "text": candidate.content["text"],
                "provenance": dict(candidate.provenance),
                "supporting_artifacts": list(candidate.supporting_artifacts),
            }
            attempt = encoded({"memories": [*chosen, entry]}).decode("utf-8")
            tokens = count_tokens(attempt) if count_tokens else len(attempt.encode("utf-8"))
            if type(tokens) is not int or tokens < 0:
                raise ProviderError("memory_denied", "Host tokenizer returned an invalid count")
            if len(attempt.encode("utf-8")) <= max_bytes and tokens <= max_tokens:
                chosen.append(entry)
                rendered = attempt
        self.projection.validate()
        # Tokenization can take time or invoke trusted host code. Refuse stale
        # disclosure if a selected canonical head expired or changed meanwhile.
        selected_ids = {str(entry["id"]) for entry in chosen}
        self.projection.validate_selection(tuple(c for c in results.value if c.id in selected_ids))
        return rendered
