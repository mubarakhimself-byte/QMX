"""Real journal/SDK/admission behavior with synthetic data, no live providers."""

from __future__ import annotations

import json
from collections.abc import Generator
from dataclasses import replace
from pathlib import Path
from threading import Barrier, Thread
from typing import Any

import pytest
from langchain_core.embeddings import Embeddings
from qma.core.plugins.hooks import HookEvent, HookResult
from qma.core.ports.memory import MemoryCandidate
from qma.core.vocabulary.enums import HookResultDecision
from qma.core.vocabulary.enums import MemoryValidationState as State
from qma.daemon import AuthoritativeJournal, PersistenceSubstrate
from qma.daemon.hooks.registry import HookRegistry, build_hook_result
from qma.daemon.request_runtime.durable_memory import (
    ActorMemoryScope,
    DurableMemory,
    JournalMemoryProvider,
    MemoryLimits,
    MemorySource,
)
from qma.daemon.request_runtime.graph_storage import JournalRecords
from qma.daemon.request_runtime.providers import ProviderError
from qma.daemon.request_runtime.scoped_memory import ResearchMemoryScope, ScopedResearchMemory
from qmf.core import Result, is_ok, is_refusal
from test_product_session_grants import _clock  # pyright: ignore[reportPrivateUsage]


def value[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


SOURCE = MemorySource("synthetic-source", "snapshot:one", ("visible.md",), "grant-revision:one")
SCOPE = ActorMemoryScope("owner", "quant:persistent-researcher", "facts", SOURCE)


class Host:
    def __init__(self) -> None:
        self.active = True
        self.now = 100
        self.checks = 0

    def validate(self) -> None:
        self.checks += 1
        if not self.active:
            raise ProviderError("context_changed", "Current host grant was revoked")


def open_journal(root: Path) -> tuple[PersistenceSubstrate, AuthoritativeJournal]:
    substrate = value(PersistenceSubstrate.open(root, machine="memory-test", boot_epoch_id="boot"))
    return substrate, value(AuthoritativeJournal.bind(substrate, clock=_clock(boot="boot", n=4096)))


Bound = tuple[DurableMemory, JournalMemoryProvider, Host, AuthoritativeJournal]


@pytest.fixture
def bound(tmp_path: Path) -> Generator[Bound]:
    substrate, journal = open_journal(tmp_path / "store")
    host = Host()
    provider = JournalMemoryProvider(
        JournalRecords(journal), SCOPE.namespace, SOURCE, host.validate, now_ns=lambda: host.now
    )
    memory = DurableMemory(provider)
    yield memory, provider, host, journal
    journal.close()
    substrate.close()


def candidate(
    memory_id: str = "fact:one", text: str = "Synthetic alpha fact", **kwargs: Any
) -> MemoryCandidate:
    content = {"memory_type": "semantic", "text": text}
    content.update(kwargs.pop("content", {}))
    return MemoryCandidate(
        id=memory_id,
        scope=SCOPE.namespace,
        proposer="agent:one",
        occurrence_time=10,
        provenance={
            "source_id": SOURCE.source_id,
            "snapshot_ref": SOURCE.snapshot_ref,
            "locators": list(SOURCE.locators),
            "authority_binding": SOURCE.authority_binding,
            "request_id": "request:synthetic",
        },
        supporting_artifacts=("artifact:synthetic",),
        content=content,
        **kwargs,
    )


def test_typed_records_sdk_filter_and_full_provenance(bound: Bound) -> None:
    memory, provider, _, _ = bound
    semantic = memory.admit(candidate())
    memory.admit(
        candidate("episode", "A synthetic run succeeded", content={"memory_type": "episodic"})
    )
    assert semantic.admission_confidence is not None and semantic.validation_state == State.ADMITTED
    assert [c.id for c in value(provider.search(memory_type="semantic"))] == [semantic.id]
    context = json.loads(memory.context(max_bytes=8192, max_tokens=8192, memory_type="semantic"))
    assert context["memories"][0]["provenance"]["locators"] == ["visible.md"]
    assert context["memories"][0]["supporting_artifacts"] == ["artifact:synthetic"]


@pytest.mark.parametrize(
    "change",
    [
        {"scope": "other-scope"},
        {"provenance": {}},
        {"supporting_artifacts": ()},
        {"provenance": {"source_id": "hidden-source"}},
        {"content": {"memory_type": "unknown", "text": "bad"}},
        {"content": {"memory_type": "semantic", "text": " "}},
    ],
)
def test_scope_provenance_and_type_denials_do_not_persist(
    bound: Bound, change: dict[str, Any]
) -> None:
    memory, provider, _, journal = bound
    before = len(value(journal.read_events()))
    with pytest.raises(ProviderError, match="admission refused"):
        memory.admit(replace(candidate(), **change))
    assert len(value(journal.read_events())) == before
    assert value(provider.list(SCOPE.namespace)) == ()


@pytest.mark.parametrize(
    "field,bad",
    [
        ("snapshot_ref", "snapshot:other"),
        ("locators", ["hidden.md"]),
        ("authority_binding", "old-grant"),
    ],
)
def test_candidate_cannot_widen_pinned_source(bound: Bound, field: str, bad: Any) -> None:
    memory, _, _, _ = bound
    c = candidate()
    with pytest.raises(ProviderError):
        memory.admit(replace(c, provenance={**c.provenance, field: bad}))


def test_supersession_atomic_history_and_no_resurrection(bound: Bound) -> None:
    memory, provider, _, journal = bound
    first = memory.admit(candidate())
    before = len(value(journal.read_events()))
    second = memory.admit(candidate("fact:two", "Synthetic corrected fact", supersession=first.id))
    assert len(value(journal.read_events())) == before + 1
    assert [c.validation_state for c in value(provider.history(first.id))] == [
        State.ADMITTED,
        State.SUPERSEDED,
    ]
    assert is_refusal(provider.get(first.id))
    assert [c.id for c in value(provider.list(SCOPE.namespace))] == [second.id]
    assert is_refusal(provider.admit(first))
    assert value(provider.history(second.id))[0].supersession == first.id


def test_invalidate_and_expiration_are_durable_terminal_states(bound: Bound) -> None:
    memory, provider, host, _ = bound
    memory.admit(candidate())
    memory.admit(candidate("ttl", content={"expires_at_ns": 150}))
    value(provider.invalidate("fact:one"))
    assert is_refusal(provider.get("fact:one"))
    host.now = 150
    assert value(provider.list(SCOPE.namespace)) == ()
    value(provider.expire("ttl"))
    assert value(provider.history("ttl"))[-1].validation_state == State.EXPIRED
    assert memory.context(max_bytes=8192, max_tokens=8192) == ""
    assert is_refusal(provider.admit(value(provider.history("fact:one"))[0]))


def test_replayed_admission_and_terminal_operation_append_nothing(bound: Bound) -> None:
    memory, provider, _, journal = bound
    memory.admit(candidate())
    count = len(value(journal.read_events()))
    memory.admit(candidate())
    assert len(value(journal.read_events())) == count
    value(provider.invalidate("fact:one"))
    count = len(value(journal.read_events()))
    value(provider.invalidate("fact:one"))
    assert len(value(journal.read_events())) == count
    with pytest.raises(ProviderError):
        memory.admit(candidate(text="Changed same id"))


def test_actor_owner_collection_and_source_binding_isolation(bound: Bound) -> None:
    memory, provider, host, _ = bound
    memory.admit(candidate())
    for other in (
        replace(SCOPE, principal="other"),
        replace(SCOPE, actor_id="quant:other"),
        replace(SCOPE, collection="other"),
        replace(SCOPE, source=replace(SOURCE, authority_binding="revision:two")),
    ):
        p = JournalMemoryProvider(
            provider.records, other.namespace, other.source, host.validate, now_ns=lambda: host.now
        )
        assert value(p.list(other.namespace)) == ()
        assert value(p.history("fact:one")) == ()
        assert is_refusal(p.get("fact:one"))
    assert is_refusal(provider.recall("other-scope", 8192))


def test_stale_grant_blocks_all_reads_and_mutations(bound: Bound) -> None:
    memory, provider, host, journal = bound
    memory.admit(candidate())
    count = len(value(journal.read_events()))
    host.active = False
    for operation in (
        lambda: provider.get("fact:one"),
        lambda: provider.history("fact:one"),
        lambda: provider.list(provider.scope),
        provider.scopes,
        lambda: provider.invalidate("fact:one"),
        lambda: memory.context(max_bytes=8192, max_tokens=8192),
        lambda: memory.admit(candidate("two")),
    ):
        with pytest.raises(ProviderError, match="revoked"):
            operation()
    assert len(value(journal.read_events())) == count


def test_context_byte_token_bounds_leave_canonical_memory_intact(bound: Bound) -> None:
    memory, provider, _, journal = bound
    memory.admit(candidate(text="Synthetic fact with unicode 🐈 " * 30))
    memory.admit(candidate("small", "short"))
    before = len(value(journal.read_events()))
    assert memory.context(max_bytes=10, max_tokens=8192) == ""
    assert memory.context(max_bytes=8192, max_tokens=10) == ""
    bounded = memory.context(max_bytes=550, max_tokens=8192)
    assert len(bounded.encode("utf-8")) <= 550
    assert [m["id"] for m in json.loads(bounded)["memories"]] == ["small"]
    assert len(value(provider.list(provider.scope))) == 2
    assert len(value(journal.read_events())) == before
    exact = memory.context(max_bytes=8192, max_tokens=100, count_tokens=lambda text: 5)
    assert len(json.loads(exact)["memories"]) == 2


class LocalEmbeddings(Embeddings):
    def __init__(self, host: Host | None = None) -> None:
        self.documents: list[str] = []
        self.queries: list[str] = []
        self.host = host

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.documents.extend(texts)
        if self.host:
            self.host.active = False
        return [[1.0, 0.0] if "alpha" in text else [0.0, 1.0] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return [1.0, 0.0]


def test_explicit_sdk_semantic_search_indexes_only_active_allowed_bytes(bound: Bound) -> None:
    memory, provider, host, _ = bound
    memory.admit(candidate())
    memory.admit(candidate("beta", "Synthetic beta fact"))
    memory.admit(candidate("deleted", "DO NOT EMBED deleted"))
    memory.admit(candidate("expired", "DO NOT EMBED expired", content={"expires_at_ns": 150}))
    value(provider.invalidate("deleted"))
    host.now = 200
    assert is_refusal(provider.search(query="alpha"))
    embedding = LocalEmbeddings()
    p = JournalMemoryProvider(
        provider.records,
        provider.scope,
        SOURCE,
        host.validate,
        now_ns=lambda: host.now,
        embeddings=embedding,
        embedding_dims=2,
    )
    assert value(p.search(query="alpha", limit=1))[0].id == "fact:one"
    assert len(embedding.documents) == 2 and all(
        "DO NOT EMBED" not in text for text in embedding.documents
    )
    assert embedding.queries == ["alpha"]


def test_revocation_during_embedding_prevents_query_and_disclosure(bound: Bound) -> None:
    memory, provider, host, _ = bound
    memory.admit(candidate())
    embedding = LocalEmbeddings(host)
    p = JournalMemoryProvider(
        provider.records,
        provider.scope,
        SOURCE,
        host.validate,
        now_ns=lambda: host.now,
        embeddings=embedding,
        embedding_dims=2,
    )
    with pytest.raises(ProviderError, match="revoked"):
        p.search(query="alpha")
    assert len(embedding.documents) == 1 and embedding.queries == []


def test_capacity_failure_cannot_partially_supersede(bound: Bound) -> None:
    _, provider, host, _ = bound
    p = JournalMemoryProvider(
        provider.records,
        provider.scope,
        SOURCE,
        host.validate,
        now_ns=lambda: host.now,
        limits=MemoryLimits(max_revisions=2),
    )
    m = DurableMemory(p)
    m.admit(candidate())
    with pytest.raises(ProviderError):
        m.admit(candidate("two", supersession="fact:one"))
    assert value(p.get("fact:one")).validation_state == State.ADMITTED
    assert value(p.history("two")) == ()


def test_two_provider_instances_cannot_supersede_same_head_concurrently(bound: Bound) -> None:
    memory, provider, host, _ = bound
    memory.admit(candidate())
    second = DurableMemory(
        JournalMemoryProvider(
            provider.records, provider.scope, SOURCE, host.validate, now_ns=lambda: host.now
        )
    )
    barrier = Barrier(2)
    outcomes: list[str] = []

    def write(m: DurableMemory, memory_id: str) -> None:
        barrier.wait()
        try:
            m.admit(candidate(memory_id, supersession="fact:one"))
            outcomes.append("admitted")
        except ProviderError:
            outcomes.append("refused")

    threads = [
        Thread(target=write, args=(memory, "two")),
        Thread(target=write, args=(second, "three")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert sorted(outcomes) == ["admitted", "refused"]
    assert len(value(provider.list(provider.scope))) == 1


def test_disk_reopen_rebuilds_history_tombstones_and_identical_context(tmp_path: Path) -> None:
    root = tmp_path / "restart"
    host = Host()
    substrate, journal = open_journal(root)
    p = JournalMemoryProvider(
        JournalRecords(journal), SCOPE.namespace, SOURCE, host.validate, now_ns=lambda: host.now
    )
    m = DurableMemory(p)
    m.admit(candidate())
    m.admit(candidate("two", "replacement", supersession="fact:one"))
    m.admit(candidate("deleted", "old"))
    value(p.invalidate("deleted"))
    before = m.context(max_bytes=8192, max_tokens=8192)
    journal.close()
    substrate.close()
    substrate, journal = open_journal(root)
    try:
        p = JournalMemoryProvider(
            JournalRecords(journal), SCOPE.namespace, SOURCE, host.validate, now_ns=lambda: host.now
        )
        m = DurableMemory(p)
        assert m.context(max_bytes=8192, max_tokens=8192) == before
        assert [c.validation_state for c in value(p.history("fact:one"))] == [
            State.ADMITTED,
            State.SUPERSEDED,
        ]
        assert is_refusal(p.get("deleted"))
        count = len(value(journal.read_events()))
        m.admit(candidate("two", "replacement", supersession="fact:one"))
        assert len(value(journal.read_events())) == count
    finally:
        journal.close()
        substrate.close()


def test_existing_write_hook_denial_leaves_predecessor_current(bound: Bound) -> None:
    memory, provider, _, _ = bound
    memory.admit(candidate())
    hooks = HookRegistry()

    def deny(payload: HookEvent) -> HookResult:
        return build_hook_result(HookResultDecision.DENY, reason="host-deny")

    value(hooks.register_handler("before_memory_write", deny, decisions={HookResultDecision.DENY}))
    with pytest.raises(ProviderError):
        DurableMemory(provider, hooks=hooks).admit(candidate("two", supersession="fact:one"))
    assert value(provider.get("fact:one")).validation_state == State.ADMITTED


def test_research_facade_retry_history_and_no_legacy_resurrection(bound: Bound) -> None:
    _, provider, host, _ = bound
    scope = ResearchMemoryScope(
        "owner",
        "app:one",
        "reader",
        SOURCE.authority_binding,
        SOURCE.source_id,
        SOURCE.snapshot_ref,
        SOURCE.locators,
    )
    memory = ScopedResearchMemory(provider.records, scope, host.validate, now_ns=lambda: host.now)
    memory.retain(
        "first",
        request_id="one",
        specialist="analyst:1",
        occurrence_time=10,
        result_ref="result:one",
    )
    memory.retain(
        "second",
        request_id="two",
        specialist="analyst:1",
        occurrence_time=20,
        result_ref="result:two",
    )
    memory.retain(
        "second",
        request_id="two",
        specialist="analyst:1",
        occurrence_time=20,
        result_ref="result:two",
    )
    recalled = memory.recall()
    assert recalled is not None and recalled["request_id"] == "two"
    assert value(memory.provider.history("one:summary"))[-1].validation_state == State.SUPERSEDED
    value(memory.provider.invalidate("two:summary"))
    assert memory.recall() is None


def test_embedding_revalidation_stops_second_document_after_revoke(bound: Bound) -> None:
    memory, provider, host, _ = bound
    memory.admit(candidate())
    memory.admit(candidate("two", "second synthetic fact"))
    embedding = LocalEmbeddings(host)
    p = JournalMemoryProvider(
        provider.records,
        provider.scope,
        SOURCE,
        host.validate,
        now_ns=lambda: host.now,
        embeddings=embedding,
        embedding_dims=2,
    )
    with pytest.raises(ProviderError, match="revoked"):
        p.search(query="alpha")
    assert len(embedding.documents) == 1 and embedding.queries == []


def test_expiration_during_sdk_search_is_not_disclosed(bound: Bound) -> None:
    memory, provider, host, _ = bound
    memory.admit(candidate(content={"expires_at_ns": 150}))

    class ClockAdvancingEmbeddings(LocalEmbeddings):
        def embed_query(self, text: str) -> list[float]:
            host.now = 200
            return super().embed_query(text)

    p = JournalMemoryProvider(
        provider.records,
        provider.scope,
        SOURCE,
        host.validate,
        now_ns=lambda: host.now,
        embeddings=ClockAdvancingEmbeddings(),
        embedding_dims=2,
    )
    assert value(p.search(query="alpha")) == ()
    assert is_refusal(p.get("fact:one"))


def test_expiration_during_token_count_refuses_context_disclosure(bound: Bound) -> None:
    memory, provider, host, _ = bound
    memory.admit(candidate(content={"expires_at_ns": 150}))

    def count(text: str) -> int:
        host.now = 200
        return 1

    with pytest.raises(ProviderError, match="changed during context"):
        memory.context(max_bytes=8192, max_tokens=8192, count_tokens=count)
    assert is_refusal(provider.get("fact:one"))


def test_small_host_record_cap_has_valid_default_search(bound: Bound) -> None:
    _, provider, host, _ = bound
    p = JournalMemoryProvider(
        provider.records,
        provider.scope,
        SOURCE,
        host.validate,
        now_ns=lambda: host.now,
        limits=MemoryLimits(max_records=3),
    )
    assert value(p.search()) == ()


def test_reduced_host_cap_refuses_old_state_before_embedding(bound: Bound) -> None:
    memory, provider, host, _ = bound
    memory.admit(candidate())
    memory.admit(candidate("two", "second fact"))
    embedding = LocalEmbeddings()
    p = JournalMemoryProvider(
        provider.records,
        provider.scope,
        SOURCE,
        host.validate,
        now_ns=lambda: host.now,
        limits=MemoryLimits(max_records=1),
        embeddings=embedding,
        embedding_dims=2,
    )
    with pytest.raises(ProviderError, match="current host record cap"):
        p.search(query="alpha")
    assert embedding.documents == [] and embedding.queries == []


def test_durable_write_ack_loss_replays_without_duplicate_or_partial_supersession(
    bound: Bound, monkeypatch: pytest.MonkeyPatch
) -> None:
    memory, provider, _, journal = bound
    memory.admit(candidate())
    write = provider.records.put

    def lost_ack(kind: str, key: str, body: dict[str, Any]) -> None:
        write(kind, key, body)
        raise ProviderError(
            "storage_failure", "Synthetic acknowledgement loss after journal append"
        )

    monkeypatch.setattr(provider.records, "put", lost_ack)
    with pytest.raises(ProviderError, match="acknowledgement loss"):
        memory.admit(candidate("two", "replacement", supersession="fact:one"))
    monkeypatch.setattr(provider.records, "put", write)
    assert value(provider.history("fact:one"))[-1].validation_state == State.SUPERSEDED
    assert value(provider.get("two")).validation_state == State.ADMITTED
    count = len(value(journal.read_events()))
    memory.admit(candidate("two", "replacement", supersession="fact:one"))
    assert len(value(journal.read_events())) == count


def test_legacy_exact_scope_summary_is_read_only_and_cannot_resurrect(bound: Bound) -> None:
    _, provider, host, journal = bound
    scope = ResearchMemoryScope(
        "owner",
        "app:one",
        "reader",
        SOURCE.authority_binding,
        SOURCE.source_id,
        SOURCE.snapshot_ref,
        SOURCE.locators,
    )
    old = replace(
        candidate(),
        scope=scope.namespace,
        content={"summary": "legacy", "request_id": "legacy", "snapshot_ref": SOURCE.snapshot_ref},
    )
    old = old.with_admission(0.5)
    provider.records.put("memory", scope.namespace, dict(old.to_payload()))
    m = ScopedResearchMemory(provider.records, scope, host.validate, now_ns=lambda: host.now)
    count = len(value(journal.read_events()))
    recalled = m.recall()
    assert recalled is not None and recalled["summary"] == "legacy"
    assert len(value(journal.read_events())) == count
    m.retain(
        "updated",
        request_id="new",
        specialist="agent:one",
        occurrence_time=20,
        result_ref="artifact:new",
    )
    value(m.provider.invalidate("new:summary"))
    assert m.recall() is None


def test_legacy_summary_with_wrong_source_pin_refuses(bound: Bound) -> None:
    _, provider, host, _ = bound
    scope = ResearchMemoryScope(
        "owner",
        "app:one",
        "reader",
        SOURCE.authority_binding,
        SOURCE.source_id,
        SOURCE.snapshot_ref,
        SOURCE.locators,
    )
    c = replace(
        candidate(),
        scope=scope.namespace,
        provenance={**candidate().provenance, "snapshot_ref": "hidden-snapshot"},
        content={"summary": "hidden bytes"},
    ).with_admission(0.5)
    provider.records.put("memory", scope.namespace, dict(c.to_payload()))
    m = ScopedResearchMemory(provider.records, scope, host.validate, now_ns=lambda: host.now)
    with pytest.raises(ProviderError, match="outside current host pins"):
        m.recall()
