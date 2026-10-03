"""Real retained corpus metadata, scope refusal, and restart pin checks."""

from __future__ import annotations

from pathlib import Path

import pytest
from qma.daemon.knowledge.plain_file import PlainFileLibrarySource
from qma.daemon.knowledge.service import KnowledgeService
from qma.daemon.request_runtime.domain_tools import create_research_browse_binding
from qma.daemon.request_runtime.providers import ProviderError
from qma.wire.invocation_envelope import ContributionRecord, InstanceRecord
from qmf.core import is_ok


def test_real_retained_snapshot_metadata_is_explicitly_scoped(tmp_path: Path) -> None:
    (tmp_path / "visible.md").write_text("hypothesis: price mean reversion", encoding="utf-8")
    (tmp_path / "hidden.md").write_text("private hypothesis", encoding="utf-8")
    knowledge = KnowledgeService()
    assert is_ok(
        knowledge.registry.bind(
            "source:research", PlainFileLibrarySource(tmp_path, "source:research")
        )
    )
    snapshot = knowledge.snapshot("source:research")
    assert is_ok(snapshot)
    kwargs = {
        "source_id": "source:research",
        "snapshot_ref": snapshot.value.id,
        "allowed_locators": ("visible.md",),
        "contribution": ContributionRecord("research:qml", "0.1.0", "enabled"),
        "instance": InstanceRecord("inst:research", 1),
        "grant_id": "grant:research",
    }
    binding = create_research_browse_binding(knowledge, **kwargs)  # pyright: ignore[reportArgumentType] - heterogeneous typed constructor fixture
    assert (
        binding.descriptor.op_id == "qml.research.browse"
        and binding.descriptor.effect_class == "read"
    )
    result = binding.execute({"snapshot_ref": snapshot.value.id})
    assert result["items"] == [
        {"locator": "visible.md", "content_fp1": snapshot.value.file_digests["visible.md"]}
    ]
    for args in (
        {"snapshot_ref": "fp1:other"},
        {"snapshot_ref": snapshot.value.id, "locator": "hidden.md"},
        {"snapshot_ref": snapshot.value.id, "locator": "../outside.md"},
    ):
        with pytest.raises(ProviderError, match="outside host scope"):
            binding.execute(args)
    (tmp_path / "visible.md").write_text("changed bytes", encoding="utf-8")
    assert binding.execute({"snapshot_ref": snapshot.value.id}) == result
    with pytest.raises(ValueError, match="unavailable or changed"):
        create_research_browse_binding(knowledge, **kwargs)  # pyright: ignore[reportArgumentType] - heterogeneous typed constructor fixture


@pytest.mark.parametrize(
    "locator", ["visible.md", "hidden.md", "wrong-snapshot", "expired-no-tools"]
)
def test_domain_browse_uses_real_session_dispatch(tmp_path: Path, locator: str) -> None:
    import json

    from qma.daemon import ProductSessionService
    from qma.daemon.request_runtime import CopilotProfile, RequestRuntime, RequestSpec
    from qma.daemon.request_runtime.domain_tools import bind_daemon_tool_providers
    from qmf.core import Ok
    from test_product_session_grants import (
        _grant_kwargs,  # pyright: ignore[reportPrivateUsage] - authority fixture
        _mint_kwargs,  # pyright: ignore[reportPrivateUsage] - authority fixture
        _open,  # pyright: ignore[reportPrivateUsage] - authority fixture
    )
    from test_request_runtime_tool_loop import ScriptedText

    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "visible.md").write_text("research evidence", encoding="utf-8")
    (corpus / "hidden.md").write_text("restricted", encoding="utf-8")
    knowledge = KnowledgeService()
    assert is_ok(
        knowledge.registry.bind(
            "source:research", PlainFileLibrarySource(corpus, "source:research")
        )
    )
    snapshot = knowledge.snapshot("source:research")
    assert is_ok(snapshot)
    substrate, journal = _open(tmp_path / "store")
    try:
        sessions = ProductSessionService(journal=journal, sqlite=substrate.sqlite)
        assert is_ok(sessions.mint(**_mint_kwargs()))
        assert is_ok(
            sessions.host_grant(
                "psess:desk-1",
                **_grant_kwargs(
                    op_id="qml.research.browse",
                    parameter_ceiling={"allow_keys": ["snapshot_ref", "locator"]},
                ),
            )
        )
        provider = ScriptedText(
            [
                json.dumps(
                    {
                        "type": "tool",
                        "tool": "research_browse",
                        "arguments": {
                            "snapshot_ref": "fp1:wrong"
                            if locator == "wrong-snapshot"
                            else snapshot.value.id,
                            "locator": "visible.md" if locator == "wrong-snapshot" else locator,
                        },
                    }
                ),
                json.dumps({"type": "final", "content": "metadata verified"}),
            ]
        )
        runtime = RequestRuntime(
            journal=journal, product_sessions=sessions, providers={"text-fixture": provider}
        )
        bound = bind_daemon_tool_providers(
            runtime,
            {"text-fixture": provider},
            {
                "reader": frozenset()
                if locator == "expired-no-tools"
                else frozenset({"research_browse"})
            },
            {
                "source_id": "source:research",
                "snapshot_ref": snapshot.value.id,
                "allowed_locators": ["visible.md"],
            },
            knowledge,
            target_resolver=lambda _session: Ok(
                (
                    ContributionRecord("analysis-backtest:qmb", "0.1.0", "enabled"),
                    InstanceRecord("inst:1", 4),
                )
            ),
            now=lambda: (
                "2027-01-01T00:00:00Z" if locator == "expired-no-tools" else "2026-10-03T00:00:00Z"
            ),
        )
        assert is_ok(bound)
        runtime.providers = dict(bound.value)
        loaded = sessions.get("psess:desk-1")
        assert is_ok(loaded)
        accepted = runtime.submit(
            RequestSpec(
                "one",
                "operator",
                "psess:desk-1",
                loaded.value.context_revision,
                CopilotProfile("reader"),
                "Browse metadata",
                "text-fixture",
            )
        )
        assert is_ok(accepted)
        executed = runtime.execute(accepted.value.request_id)
        assert is_ok(executed)
        if locator == "expired-no-tools":
            assert executed.value.status == "failed" and executed.value.error == "context_changed"
            assert len(provider.requests) == 0
        elif locator == "visible.md":
            assert executed.value.status == "completed" and len(provider.requests) == 2
            assert snapshot.value.id in provider.requests[0].instructions
            assert "visible.md" in provider.requests[0].instructions
            assert "hidden.md" not in provider.requests[0].instructions
            observations = json.loads(provider.requests[1].prompt)["tool_observations"]
            assert observations[0]["result"]["items"] == [
                {"locator": "visible.md", "content_fp1": snapshot.value.file_digests["visible.md"]}
            ]
        else:
            assert executed.value.status == "failed" and executed.value.error == "tool_denied"
            assert executed.value.result is None and len(provider.requests) == 1
    finally:
        journal.close()
        substrate.close()
