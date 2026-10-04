"""Actual corpus/domain services with deterministic inference, never live proof."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

import pytest
from qma.daemon import AuthoritativeJournal, PersistenceSubstrate, ProductSessionService
from qma.daemon.knowledge.plain_file import PlainFileLibrarySource
from qma.daemon.knowledge.service import KnowledgeService
from qma.daemon.request_runtime import CopilotProfile, RequestRuntime, RequestSpec
from qma.daemon.request_runtime.domain_tools import create_research_browse_binding
from qma.daemon.request_runtime.research_workflow import (
    ResearchWorkflowProvider,
    RetainedCorpus,
    SpecialistDefinition,
)
from qma.wire.invocation_envelope import ContributionRecord, InstanceRecord
from qmf.core import Result, is_ok, is_refusal
from test_product_session_grants import (  # pyright: ignore[reportPrivateUsage]
    _clock,  # pyright: ignore[reportPrivateUsage]
    _grant_kwargs,  # pyright: ignore[reportPrivateUsage]
    _mint_kwargs,  # pyright: ignore[reportPrivateUsage]
)
from test_request_runtime_tool_loop import ScriptedText


def value[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def compose(
    root: Path, corpus_root: Path, *, restore: bool = False, tools: bool = True
) -> tuple[
    PersistenceSubstrate,
    AuthoritativeJournal,
    RequestRuntime,
    ScriptedText,
    ResearchWorkflowProvider,
    list[dict[str, object]],
]:
    substrate = value(
        PersistenceSubstrate.open(root, machine="research-test", boot_epoch_id="boot")
    )
    journal = value(AuthoritativeJournal.bind(substrate, clock=_clock(boot="boot", n=2048)))
    sessions = ProductSessionService(journal=journal, sqlite=substrate.sqlite)
    if restore:
        value(sessions.restore_from_journal())
    else:
        value(sessions.mint(**_mint_kwargs()))
        value(
            sessions.host_grant(
                "psess:desk-1",
                **_grant_kwargs(
                    op_id="qml.research.browse",
                    parameter_ceiling={"allow_keys": ["snapshot_ref", "locator"]},
                ),
            )
        )
    knowledge = KnowledgeService()
    value(knowledge.bind("supplied", PlainFileLibrarySource(corpus_root, "supplied")))
    snapshot = value(knowledge.snapshot("supplied"))
    value(
        knowledge.cite(
            "supplied",
            snapshot.id,
            "visible.md",
            evidence_label="supplied",
            authored_by="test-supply",
        )
    )
    binding = create_research_browse_binding(
        knowledge,
        source_id="supplied",
        snapshot_ref=snapshot.id,
        allowed_locators=("visible.md",),
        contribution=ContributionRecord("analysis-backtest:qmb", "0.1.0", "enabled"),
        instance=InstanceRecord("inst:1", 4),
        grant_id="grant:1",
    )
    observed: list[dict[str, object]] = []
    original = binding.execute

    def observe(arguments: Mapping[str, object]) -> Mapping[str, object]:
        observed.append(dict(arguments))
        return original(arguments)

    binding = replace(binding, execute=observe)
    provider = ScriptedText(
        [json.dumps({"type": "final", "content": "Evidence supports bounded study."})] * 8
    )
    workflow = ResearchWorkflowProvider(
        provider,
        provider_id="research",
        specialist=SpecialistDefinition(
            "corpus-analyst", "1", "Analyze only the supplied evidence."
        ),
        corpus=RetainedCorpus(knowledge, "supplied", snapshot.id, ("visible.md",)),
        operation_name="research_browse",
        operation=binding,
        operation_arguments={"snapshot_ref": snapshot.id},
        profile_tools={
            "reader": frozenset({"research_browse"}) if tools else frozenset(),
            "other-reader": frozenset({"research_browse"}),
        },
        now=lambda: "2026-10-04T00:00:00Z",
    )
    runtime = RequestRuntime(
        journal=journal, product_sessions=sessions, providers={"research": workflow}
    )
    workflow.bind_runtime(runtime)
    return substrate, journal, runtime, provider, workflow, observed


def supply(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "visible.md").write_text(
        "Mean reversion needs transaction-cost controls.", encoding="utf-8"
    )
    (corpus / "hidden.md").write_text("private excluded evidence", encoding="utf-8")
    return corpus


def submit(runtime: RequestRuntime, key: str = "one", profile: str = "reader") -> str:
    return value(
        runtime.submit(
            RequestSpec(
                key,
                "operator",
                "psess:desk-1",
                0,
                CopilotProfile(
                    profile, instructions=f"Host restrictions for {profile}: no unsupported claims."
                ),
                "Assess supplied hypothesis",
                "research",
            )
        )
    ).request_id


def test_supplied_corpus_delegation_real_domain_result_and_scoped_memory(tmp_path: Path) -> None:
    substrate, journal, runtime, provider, _workflow, observed = compose(
        tmp_path / "store", supply(tmp_path)
    )
    try:
        first = value(runtime.execute(submit(runtime)))
        assert first.status == "completed", first
        assert first.result is not None
        content = json.loads(first.result.content)
        assert content["analysis"] == "Evidence supports bounded study."
        assert content["operation"]["items"][0]["locator"] == "visible.md"
        assert content["specialist"] == "corpus-analyst:1"
        delegated = json.loads(json.loads(provider.requests[0].prompt)["user_request"])
        assert (
            delegated["corpus"][0]["content"] == "Mean reversion needs transaction-cost controls."
        )
        assert "Host restrictions for reader" in provider.requests[0].instructions
        assert "Analyze only the supplied evidence" in provider.requests[0].instructions
        assert "hidden.md" not in provider.requests[0].prompt
        assert delegated["scoped_memory"] is None
        second = value(runtime.execute(submit(runtime, "two")))
        assert second.status == "completed"
        later = json.loads(json.loads(provider.requests[1].prompt)["user_request"])
        assert later["scoped_memory"]["request_id"] == first.request_id
        assert provider.requests[0].graph_thread_id != provider.requests[1].graph_thread_id
        assert (
            value(runtime.execute(submit(runtime, "three", "other-reader"))).status == "completed"
        )
        assert "Host restrictions for other-reader" in provider.requests[2].instructions
        different = json.loads(json.loads(provider.requests[2].prompt)["user_request"])
        assert different["scoped_memory"] is None
        assert len(observed) == 3
    finally:
        journal.close()
        substrate.close()


def test_restart_resumes_specialist_checkpoint_and_never_repeats_operation(tmp_path: Path) -> None:
    corpus = supply(tmp_path)
    substrate, journal, runtime, provider, _workflow, observed = compose(tmp_path / "store", corpus)
    request_id = submit(runtime)

    class LostModel(Exception):
        code = "outcome_unknown"

    provider.after = lambda count: (_ for _ in ()).throw(LostModel())
    first = value(runtime.execute(request_id))
    assert first.status == "interrupted"
    assert observed == []
    journal.close()
    substrate.close()
    substrate, journal, runtime, provider, _workflow, observed = compose(
        tmp_path / "store", corpus, restore=True
    )
    try:
        assert value(runtime.get(request_id)).status == "interrupted"
        assert is_refusal(runtime.execute(request_id))
        value(runtime.retry_interrupted(request_id))
        resumed = value(runtime.execute(request_id))
        assert resumed.status == "completed", resumed
        assert len(observed) == 1
        assert len(provider.requests) == 1
        assert resumed.result is not None
        resumed_content = resumed.result.content
        assert (
            json.loads(resumed.result.content)["operation"]["items"][0]["locator"] == "visible.md"
        )
    finally:
        journal.close()
        substrate.close()
    substrate, journal, runtime, provider, _workflow, observed = compose(
        tmp_path / "store", corpus, restore=True
    )
    try:
        cached = value(runtime.execute(request_id))
        assert cached.result is not None
        assert cached.result.content == resumed_content
        assert observed == [] and provider.requests == []
        fresh = value(runtime.execute(submit(runtime, "after-restart")))
        assert fresh.status == "completed"
        recalled = json.loads(json.loads(provider.requests[0].prompt)["user_request"])
        assert recalled["scoped_memory"]["request_id"] == request_id
    finally:
        journal.close()
        substrate.close()


def test_scope_boundary_interrupts_before_corpus_or_inference(tmp_path: Path) -> None:
    substrate, journal, runtime, provider, _, observed = compose(
        tmp_path / "store", supply(tmp_path), tools=False
    )
    try:
        request_id = submit(runtime)
        interrupted = value(runtime.execute(request_id))
        assert interrupted.status == "interrupted" and interrupted.error == "scope_interrupt"
        assert provider.requests == [] and observed == []
        value(runtime.retry_interrupted(request_id))
        assert value(runtime.execute(request_id)).error == "tool_denied"
        assert provider.requests == [] and observed == []
    finally:
        journal.close()
        substrate.close()


def test_cancellation_during_delegation_stops_domain_operation(tmp_path: Path) -> None:
    substrate, journal, runtime, provider, _, observed = compose(
        tmp_path / "store", supply(tmp_path)
    )
    try:
        request_id = submit(runtime)

        def cancel(count: int) -> None:
            runtime.cancel(request_id)

        provider.after = cancel
        cancelled = value(runtime.execute(request_id))
        assert cancelled.status == "cancelled", cancelled
        assert len(provider.requests) == 1 and observed == []
    finally:
        journal.close()
        substrate.close()


def test_memory_isolates_actor_and_application_and_obeys_host_write_hook(tmp_path: Path) -> None:
    from qma.core.plugins.hooks import HookEvent, HookResult
    from qma.core.vocabulary.enums import HookResultDecision
    from qma.daemon.hooks.registry import HookRegistry, build_hook_result
    from qma.daemon.request_runtime.graph_storage import JournalRecords
    from qma.daemon.request_runtime.scoped_memory import ResearchMemoryScope, ScopedResearchMemory

    substrate, journal, runtime, _provider, workflow, _observed = compose(
        tmp_path / "store", supply(tmp_path)
    )
    try:
        first = value(runtime.execute(submit(runtime)))
        events = value(journal.read_events())
        body = next(
            json.loads(str(e.payload["body"]))
            for e in events
            if e.event == "agent_graph.record" and e.payload.get("kind") == "memory"
        )
        assert body["provenance"]["request_id"] == first.request_id
        scope = ResearchMemoryScope(
            "operator",
            value(runtime.product_sessions.get("psess:desk-1")).app_instance_id or "home",
            "reader",
            first.context_binding,
            "supplied",
            workflow.corpus.snapshot_ref,
            ("visible.md",),
        )
        records = JournalRecords(journal)

        def validate() -> None:
            pass

        assert ScopedResearchMemory(records, scope, validate).recall() is not None
        for isolated in (
            replace(scope, principal="other-actor"),
            replace(scope, application="other-app"),
        ):
            assert ScopedResearchMemory(records, isolated, validate).recall() is None
        hooks = HookRegistry()

        def deny(payload: HookEvent) -> HookResult:
            return build_hook_result(HookResultDecision.DENY, reason="test-host-deny")

        value(
            hooks.register_handler("before_memory_write", deny, decisions={HookResultDecision.DENY})
        )
        workflow.hooks = hooks
        second = value(runtime.execute(submit(runtime, "denied-memory")))
        assert second.error == "memory_denied"
        recalled = ScopedResearchMemory(records, scope, validate).recall()
        assert recalled is not None and recalled["request_id"] == first.request_id
    finally:
        journal.close()
        substrate.close()


def test_research_resume_revalidates_expired_grants_before_disclosure(tmp_path: Path) -> None:
    from qma.daemon.request_runtime.providers import ProviderError

    substrate, journal, runtime, provider, workflow, observed = compose(
        tmp_path / "store", supply(tmp_path)
    )
    try:
        provider.after = lambda count: (_ for _ in ()).throw(
            ProviderError("outcome_unknown", "lost response")
        )
        request_id = submit(runtime)
        assert value(runtime.execute(request_id)).status == "interrupted"
        value(runtime.retry_interrupted(request_id))
        provider.after = None
        workflow.now = lambda: "2027-01-01T00:00:00Z"
        assert value(runtime.execute(request_id)).error == "context_changed"
        assert len(provider.requests) == 1 and observed == []
    finally:
        journal.close()
        substrate.close()


def test_interrupted_specialist_keeps_invocation_memory_while_shared_memory_evolves(
    tmp_path: Path,
) -> None:
    from qma.daemon.request_runtime.providers import ProviderError

    substrate, journal, runtime, provider, _, observed = compose(
        tmp_path / "store", supply(tmp_path)
    )
    try:
        provider.after = lambda count: (_ for _ in ()).throw(
            ProviderError("outcome_unknown", "lost response")
        )
        request_a = submit(runtime, "a")
        assert value(runtime.execute(request_a)).status == "interrupted"
        provider.after = None
        assert value(runtime.execute(submit(runtime, "b"))).status == "completed"
        value(runtime.retry_interrupted(request_a))
        assert value(runtime.execute(request_a)).status == "completed"
        first_input = json.loads(json.loads(provider.requests[0].prompt)["user_request"])
        resumed_input = json.loads(json.loads(provider.requests[-1].prompt)["user_request"])
        assert first_input == resumed_input and resumed_input["scoped_memory"] is None
        assert len(observed) == 2
    finally:
        journal.close()
        substrate.close()


def test_research_manifest_rejects_changed_operation_binding_on_resume(tmp_path: Path) -> None:
    from qma.daemon.request_runtime.providers import ProviderError

    substrate, journal, runtime, provider, workflow, observed = compose(
        tmp_path / "store", supply(tmp_path)
    )
    try:
        provider.after = lambda count: (_ for _ in ()).throw(
            ProviderError("outcome_unknown", "lost response")
        )
        request_id = submit(runtime)
        assert value(runtime.execute(request_id)).status == "interrupted"
        value(runtime.retry_interrupted(request_id))
        workflow.operation = replace(workflow.operation, argument_scope=(("locator", "hidden.md"),))
        provider.after = None
        assert value(runtime.execute(request_id)).error == "context_changed"
        assert len(provider.requests) == 1 and observed == []
    finally:
        journal.close()
        substrate.close()


def test_daemon_wrapper_scope_boundary_and_mixed_native_profile(tmp_path: Path) -> None:
    from qma.daemon.request_runtime.contracts import ProviderCapabilities
    from qma.daemon.request_runtime.domain_tools import bind_daemon_tool_providers
    from qmf.core import Ok

    substrate, journal, runtime, provider, workflow, _ = compose(
        tmp_path / "store", supply(tmp_path)
    )
    try:
        provider.capabilities = ProviderCapabilities("research")
        native = ScriptedText(["native worker result"])
        native.capabilities = ProviderCapabilities("native", execution_kind="agent_session")
        knowledge = KnowledgeService()
        value(knowledge.bind("supplied", PlainFileLibrarySource(tmp_path / "corpus", "supplied")))
        bound = value(
            bind_daemon_tool_providers(
                runtime,
                {"research": provider, "native": native},
                {
                    "reader": frozenset({"research_browse"}),
                    "blocked": frozenset(),
                    "native": frozenset(),
                    "ordinary": frozenset(),
                },
                {
                    "source_id": "supplied",
                    "snapshot_ref": workflow.corpus.snapshot_ref,
                    "allowed_locators": ["visible.md"],
                },
                knowledge,
                target_resolver=lambda session: Ok(
                    (workflow.operation.contribution, workflow.operation.instance)
                ),
                now=workflow.now,
                research_workflow={
                    "specialist_id": "corpus-analyst",
                    "profiles": ["reader", "blocked"],
                    "version": "1",
                    "instructions": "Analyze only the supplied evidence.",
                },
            )
        )
        runtime.providers = dict(bound)
        blocked = value(runtime.execute(submit(runtime, "blocked", "blocked")))
        assert blocked.error == "scope_interrupt" and provider.requests == []
        assert is_refusal(
            knowledge.retrieve("supplied", workflow.corpus.snapshot_ref, "visible.md")
        )
        accepted = value(
            runtime.submit(
                RequestSpec(
                    "native",
                    "operator",
                    "psess:desk-1",
                    0,
                    CopilotProfile("native"),
                    "native task",
                    "native",
                )
            )
        )
        result = value(runtime.execute(accepted.request_id))
        assert result.status == "completed" and result.result is not None
        assert result.result.content == "native worker result"
        assert native.requests[0].graph_thread_id is None
        provider.responses.insert(0, "ordinary copilot response")
        ordinary = value(runtime.execute(submit(runtime, "ordinary", "ordinary")))
        assert (
            ordinary.result is not None and ordinary.result.content == "ordinary copilot response"
        )
        assert provider.requests[-1].graph_thread_id is None
        assert "Host restrictions for ordinary" in provider.requests[-1].instructions
        researched = value(runtime.execute(submit(runtime, "configured-research")))
        assert researched.status == "completed", researched
        assert value(knowledge.retrieve("supplied", workflow.corpus.snapshot_ref, "visible.md"))
    finally:
        journal.close()
        substrate.close()


def test_research_effect_receipt_survives_outer_checkpoint_loss(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from collections.abc import Sequence
    from typing import Any

    from langchain_core.runnables import RunnableConfig
    from qma.daemon.request_runtime.graph_storage import JournalCheckpointer
    from qma.daemon.request_runtime.providers import ProviderError

    original = JournalCheckpointer.put_writes
    crashed = False

    def lose(
        self: JournalCheckpointer,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        nonlocal crashed
        if not crashed and any(channel == "operation_result" for channel, _ in writes):
            crashed = True
            raise ProviderError("outcome_unknown", "lost outer operation checkpoint")
        original(self, config, writes, task_id, task_path)

    monkeypatch.setattr(JournalCheckpointer, "put_writes", lose)
    substrate, journal, runtime, provider, _, observed = compose(
        tmp_path / "store", supply(tmp_path)
    )
    try:
        request_id = submit(runtime)
        assert value(runtime.execute(request_id)).status == "interrupted"
        assert crashed and len(observed) == 1
        value(runtime.retry_interrupted(request_id))
        assert value(runtime.execute(request_id)).status == "completed"
        assert len(observed) == 1 and len(provider.requests) == 1
    finally:
        journal.close()
        substrate.close()


def test_valid_larger_analysis_fits_coordinated_memory_budget(tmp_path: Path) -> None:
    substrate, journal, runtime, provider, _, _ = compose(tmp_path / "store", supply(tmp_path))
    try:
        provider.responses = [json.dumps({"type": "final", "content": "a" * 5000})] * 2
        assert value(runtime.execute(submit(runtime))).status == "completed"
        assert value(runtime.execute(submit(runtime, "recall-large"))).status == "completed"
        recalled = json.loads(json.loads(provider.requests[1].prompt)["user_request"])
        assert recalled["scoped_memory"]["summary"] == "a" * 5000
    finally:
        journal.close()
        substrate.close()
