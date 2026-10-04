"""Exact host scopes and retirement across disk reopen; no service or model calls."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from qma.core.vocabulary.enums import MemoryValidationState as State
from qma.daemon.request_runtime.durable_memory import (
    ActorMemoryScope,
    DurableMemory,
    JournalMemoryProvider,
)
from qma.daemon.request_runtime.graph_storage import JournalRecords
from qma.daemon.request_runtime.providers import ProviderError
from qma.daemon.request_runtime.scoped_memory import ResearchMemoryScope, ScopedResearchMemory
from qmf.core import is_refusal
from test_durable_memory import SOURCE, Host, candidate, open_journal, value


@pytest.mark.parametrize(
    "field",
    [
        "principal",
        "actor_id",
        "collection",
        "source_id",
        "snapshot_ref",
        "locators",
        "authority_binding",
    ],
)
def test_complete_actor_scope_withholds_foreign_read_write_after_restart(
    tmp_path: Path, field: str
) -> None:
    root = tmp_path / "actor-scope"
    host = Host()
    scope = ActorMemoryScope("owner", "quant:persistent-researcher", "facts", SOURCE)
    substrate, journal = open_journal(root)
    try:
        provider = JournalMemoryProvider(
            JournalRecords(journal), scope.namespace, SOURCE, host.validate, now_ns=lambda: host.now
        )
        admitted = DurableMemory(provider).admit(candidate())
    finally:
        journal.close()
        substrate.close()

    substrate, journal = open_journal(root)
    try:
        records = JournalRecords(journal)
        provider = JournalMemoryProvider(
            records, scope.namespace, SOURCE, host.validate, now_ns=lambda: host.now
        )
        assert value(provider.get(admitted.id)) == admitted
        if field in {"principal", "actor_id", "collection"}:
            other = replace(scope, **{field: "other"})
        else:
            replacement = ("hidden.md",) if field == "locators" else "other"
            other = replace(scope, source=replace(SOURCE, **{field: replacement}))
        foreign = JournalMemoryProvider(
            records, other.namespace, other.source, host.validate, now_ns=lambda: host.now
        )
        before = len(value(journal.read_events()))
        assert value(foreign.list(other.namespace)) == ()
        assert value(foreign.history(admitted.id)) == ()
        assert is_refusal(foreign.get(admitted.id))
        assert is_refusal(foreign.recall(scope.namespace, 8192))
        assert is_refusal(foreign.invalidate(admitted.id))
        assert is_refusal(foreign.expire(admitted.id))
        assert is_refusal(foreign.admit(admitted))
        assert is_refusal(foreign.supersede(admitted.id, admitted))
        assert value(foreign.scopes()) == (other.namespace,)
        assert len(value(journal.read_events())) == before
        assert value(provider.get(admitted.id)) == admitted
    finally:
        journal.close()
        substrate.close()


@pytest.mark.parametrize(
    "field",
    [
        "principal",
        "application",
        "profile",
        "authority_binding",
        "source_id",
        "snapshot_ref",
        "locators",
    ],
)
def test_complete_research_scope_retains_exact_job_memory_and_withholds_other_scope(
    tmp_path: Path, field: str
) -> None:
    root = tmp_path / "research-scope"
    host = Host()
    scope = ResearchMemoryScope(
        "owner",
        "app:one",
        "reader",
        SOURCE.authority_binding,
        SOURCE.source_id,
        SOURCE.snapshot_ref,
        SOURCE.locators,
    )
    substrate, journal = open_journal(root)
    try:
        memory = ScopedResearchMemory(
            JournalRecords(journal), scope, host.validate, now_ns=lambda: host.now
        )
        memory.retain(
            "first job",
            request_id="one",
            specialist="analyst:1",
            occurrence_time=10,
            result_ref="journal://result/one",
        )
    finally:
        journal.close()
        substrate.close()
    substrate, journal = open_journal(root)
    try:
        records = JournalRecords(journal)
        memory = ScopedResearchMemory(records, scope, host.validate, now_ns=lambda: host.now)
        recalled = memory.recall()
        assert recalled is not None and recalled["summary"] == "first job"
        other = replace(scope, **{field: ("hidden.md",) if field == "locators" else "other"})
        foreign = ScopedResearchMemory(records, other, host.validate, now_ns=lambda: host.now)
        before = len(value(journal.read_events()))
        assert foreign.recall() is None
        assert value(foreign.provider.history("one:summary")) == ()
        assert is_refusal(foreign.provider.get("one:summary"))
        assert is_refusal(foreign.provider.recall(scope.namespace, 8192))
        assert len(value(journal.read_events())) == before
        memory.retain(
            "second job",
            request_id="two",
            specialist="analyst:1",
            occurrence_time=20,
            result_ref="journal://result/two",
        )
        assert (
            value(memory.provider.history("one:summary"))[-1].validation_state == State.SUPERSEDED
        )
        recalled = memory.recall()
        assert recalled is not None and recalled["summary"] == "second job"
        assert foreign.recall() is None
    finally:
        journal.close()
        substrate.close()


def test_all_retirement_forms_rebuild_only_active_heads_after_restart(tmp_path: Path) -> None:
    root = tmp_path / "retirement"
    host = Host()
    scope = ActorMemoryScope("owner", "quant:persistent-researcher", "facts", SOURCE)
    substrate, journal = open_journal(root)
    try:
        provider = JournalMemoryProvider(
            JournalRecords(journal), scope.namespace, SOURCE, host.validate, now_ns=lambda: host.now
        )
        memory = DurableMemory(provider)
        original = memory.admit(candidate())
        successor = memory.admit(candidate("replacement", "new", supersession=original.id))
        invalidated = memory.admit(candidate("invalid", "retire"))
        expired = memory.admit(candidate("expired", "explicit"))
        deadline = memory.admit(candidate("deadline", "ttl", content={"expires_at_ns": 150}))
        value(provider.invalidate(invalidated.id))
        value(provider.expire(expired.id))
        before = memory.context(max_bytes=8192, max_tokens=8192)
    finally:
        journal.close()
        substrate.close()
    host.now = 150
    substrate, journal = open_journal(root)
    try:
        provider = JournalMemoryProvider(
            JournalRecords(journal), scope.namespace, SOURCE, host.validate, now_ns=lambda: host.now
        )
        memory = DurableMemory(provider)
        count = len(value(journal.read_events()))
        for record in (original, invalidated, expired, deadline):
            assert is_refusal(provider.get(record.id))
        for record in (original, invalidated, expired):
            assert is_refusal(provider.admit(record))
        assert is_refusal(
            provider.admit(candidate("late", supersession=deadline.id).with_admission(0.5))
        )
        assert [c.id for c in value(provider.search())] == [successor.id]
        assert value(provider.recall(scope.namespace, 8192)) == (successor,)
        after = memory.context(max_bytes=8192, max_tokens=8192)
        assert '"deadline"' in before and '"deadline"' not in after
        assert memory.context(max_bytes=8192, max_tokens=8192) == after
        assert value(provider.history(original.id))[-1].validation_state == State.SUPERSEDED
        assert value(provider.history(invalidated.id))[-1].validation_state == State.INVALIDATED
        assert value(provider.history(expired.id))[-1].validation_state == State.EXPIRED
        assert value(provider.history(deadline.id))[-1].validation_state == State.ADMITTED
        assert len(value(journal.read_events())) == count
        host.active = False
        with pytest.raises(ProviderError, match="revoked"):
            memory.context(max_bytes=8192, max_tokens=8192)
        assert len(value(journal.read_events())) == count
    finally:
        journal.close()
        substrate.close()


@pytest.mark.parametrize("expires", [True, "150", 10, 0])
def test_malformed_legacy_deadline_refuses_without_rewriting(
    tmp_path: Path, expires: object
) -> None:
    host = Host()
    scope = ResearchMemoryScope(
        "owner",
        "app:one",
        "reader",
        SOURCE.authority_binding,
        SOURCE.source_id,
        SOURCE.snapshot_ref,
        SOURCE.locators,
    )
    substrate, journal = open_journal(tmp_path / "legacy-invalid")
    try:
        records = JournalRecords(journal)
        old = replace(
            candidate(),
            scope=scope.namespace,
            content={"summary": "must withhold", "expires_at_ns": expires},
        ).with_admission(0.5)
        records.put("memory", scope.namespace, dict(old.to_payload()))
        before = len(value(journal.read_events()))
        memory = ScopedResearchMemory(records, scope, host.validate, now_ns=lambda: host.now)
        with pytest.raises(ProviderError, match="Invalid legacy memory expiration"):
            memory.recall()
        assert len(value(journal.read_events())) == before
    finally:
        journal.close()
        substrate.close()


def test_legacy_deadline_refuses_boolean_host_clock(tmp_path: Path) -> None:
    scope = ResearchMemoryScope(
        "owner",
        "app:one",
        "reader",
        SOURCE.authority_binding,
        SOURCE.source_id,
        SOURCE.snapshot_ref,
        SOURCE.locators,
    )
    substrate, journal = open_journal(tmp_path / "legacy-clock")
    try:
        records = JournalRecords(journal)
        old = replace(
            candidate(),
            scope=scope.namespace,
            content={"summary": "must withhold", "expires_at_ns": 150},
        ).with_admission(0.5)
        records.put("memory", scope.namespace, dict(old.to_payload()))
        memory = ScopedResearchMemory(records, scope, lambda: None, now_ns=lambda: True)
        before = len(value(journal.read_events()))
        with pytest.raises(ProviderError, match="integer nanoseconds"):
            memory.recall()
        assert len(value(journal.read_events())) == before
    finally:
        journal.close()
        substrate.close()
