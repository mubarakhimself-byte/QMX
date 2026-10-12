"""Story 43.8 — source-bound deterministic hooks and verifier gates (FR-Q34)."""

from __future__ import annotations

from qma.core.plugins.hooks import (
    HookEvent,
    HookImplementationKind,
    HookResult,
    HookSource,
    build_hook_result,
    parse_hook_implementation_kind,
)
from qma.core.ports.model import DeploymentRecord, ReviewPolicy, select_reviewer
from qma.core.refusals import NoEligibleReviewer
from qma.core.vocabulary.enums import HookResultDecision, ModelClass
from qma.core.vocabulary.registry import VocabularyError
from qma.daemon.hooks import (
    HookRegistry,
    ScopeSegmentView,
    assert_matcher_within_source,
    event_within_source_bound,
)
from qma.daemon.hooks.source_bounds import HookSourceBinding
from qmf.core import is_ok, is_refusal


def _mission_scope(mission_id: str = "mission-a", desk: str = "research") -> list[dict[str, str]]:
    return [
        {"kind": "desk", "id": desk},
        {"kind": "quant", "id": "lead"},
        {"kind": "mission", "id": mission_id},
    ]


def test_source_bound_applied_before_matcher() -> None:
    registry = HookRegistry()
    seen: list[str] = []

    def handler(event: HookEvent) -> HookResult:
        seen.append(event.event)
        return build_hook_result(HookResultDecision.ALLOW, reason="in_bound")

    assert is_ok(
        registry.register_handler(
            "before_tool",
            handler,
            source=HookSource.MISSION,
            source_ref="mission-a",
            matcher="search",
            implementation=HookImplementationKind.CALLABLE,
        )
    )

    outside = registry.dispatch(
        "before_tool",
        source=HookSource.MISSION,
        payload={"tool_name": "search"},
        scope_path=_mission_scope("mission-b"),
        match_value="search",
    )
    assert is_ok(outside)
    assert outside.value.decision is HookResultDecision.ALLOW
    assert outside.value.reason == "empty_handler"
    assert seen == []

    inside = registry.dispatch(
        "before_tool",
        source=HookSource.MISSION,
        payload={"tool_name": "search"},
        scope_path=_mission_scope("mission-a"),
        match_value="search",
    )
    assert is_ok(inside)
    assert inside.value.decision is HookResultDecision.ALLOW
    assert inside.value.reason == "in_bound"
    assert seen == ["before_tool"]


def test_registration_refuses_matcher_outside_source() -> None:
    registry = HookRegistry()

    def handler(_event: HookEvent) -> HookResult:
        return build_hook_result(HookResultDecision.OBSERVE)

    refused = registry.register_handler(
        "before_tool",
        handler,
        source=HookSource.MISSION,
        source_ref="mission-a",
        matcher="mission:mission-b",
    )
    assert is_refusal(refused)
    assert refused.context["field"] == "matcher"

    foreign_class = registry.register_handler(
        "before_tool",
        handler,
        source=HookSource.DESK,
        source_ref="research",
        matcher="role:analyst",
    )
    assert is_refusal(foreign_class)


def test_desk_and_role_and_plugin_bounds() -> None:
    desk_binding = HookSourceBinding(source=HookSource.DESK, source_ref="research")
    assert event_within_source_bound(
        desk_binding,
        scope_path=[ScopeSegmentView("desk", "research")],
    )
    assert not event_within_source_bound(
        desk_binding,
        scope_path=[ScopeSegmentView("desk", "trading")],
    )

    role_binding = HookSourceBinding(source=HookSource.ROLE, source_ref="analyst")
    assert event_within_source_bound(role_binding, role_id="analyst")
    assert not event_within_source_bound(role_binding, role_id="trader")

    plugin_binding = HookSourceBinding(
        source=HookSource.PLUGIN,
        source_ref="research-corpus",
        allowed_scopes=(
            (
                ScopeSegmentView("desk", "research"),
                ScopeSegmentView("quant", "lead"),
            ),
        ),
    )
    assert event_within_source_bound(
        plugin_binding,
        scope_path=_mission_scope(),
        plugin_id="research-corpus",
    )
    assert not event_within_source_bound(
        plugin_binding,
        scope_path=_mission_scope(desk="trading"),
        plugin_id="research-corpus",
    )
    empty_plugin = HookSourceBinding(source=HookSource.PLUGIN, source_ref="p")
    assert not event_within_source_bound(
        empty_plugin,
        scope_path=_mission_scope(),
        plugin_id="p",
    )


def test_same_source_matcher_claim_accepted() -> None:
    binding = HookSourceBinding(source=HookSource.MISSION, source_ref="mission-a")
    ok = assert_matcher_within_source(binding, "mission:mission-a")
    assert is_ok(ok)
    assert ok.value == "mission:mission-a"


def test_implementation_refuses_prompt_and_agent_types() -> None:
    for forbidden in ("prompt", "agent", "prompt_type", "agent_type", "prompt-type"):
        try:
            parse_hook_implementation_kind(forbidden)
            raise AssertionError(f"expected refusal for {forbidden!r}")
        except VocabularyError:
            pass
    assert parse_hook_implementation_kind("callable") is HookImplementationKind.CALLABLE
    assert parse_hook_implementation_kind("subprocess") is HookImplementationKind.SUBPROCESS

    registry = HookRegistry()

    def handler(_event: HookEvent) -> HookResult:
        return build_hook_result(HookResultDecision.ALLOW)

    refused = registry.register_handler(
        "before_tool",
        handler,
        source=HookSource.PLUGIN,
        source_ref="p1",
        implementation="prompt",
        allowed_scopes=[({"kind": "desk", "id": "research"},)],
    )
    assert is_refusal(refused)
    assert refused.context["field"] == "implementation"


def test_review_policy_author_family_not_equal_reviewer_family() -> None:
    catalog = (
        DeploymentRecord("a", ModelClass.WORKHORSE_GENERAL, "same"),
        DeploymentRecord("b", ModelClass.REASONING_HIGH, "same"),
        DeploymentRecord("c", ModelClass.CODING_HIGH, "different"),
    )
    selected = select_reviewer("same", catalog, model_class=ModelClass.CODING_HIGH)
    assert is_ok(selected)
    assert selected.value.deployment_id == "c"

    policy = ReviewPolicy(model_class=ModelClass.WORKHORSE_GENERAL)
    again = policy.select_reviewer("same", catalog)
    assert is_ok(again)
    assert again.value.model_family == "different"


def test_unassigned_family_ineligible_and_empty_catalog_no_eligible_reviewer() -> None:
    empty = select_reviewer("author", (), model_class="REASONING_HIGH")
    assert is_refusal(empty)
    assert NoEligibleReviewer.matches(empty)
    assert empty.context["model_class"] == "REASONING_HIGH"

    unassigned_only = (
        DeploymentRecord("u1", ModelClass.WORKHORSE_GENERAL, None),
        DeploymentRecord("u2", ModelClass.REASONING_HIGH, None),
    )
    refused = select_reviewer("family-a", unassigned_only)
    assert is_refusal(refused)
    assert NoEligibleReviewer.matches(refused)

    same_family = (
        DeploymentRecord("s1", ModelClass.WORKHORSE_GENERAL, "family-a"),
        DeploymentRecord("s2", ModelClass.REASONING_HIGH, None),
    )
    refused_same = select_reviewer("family-a", same_family)
    assert is_refusal(refused_same)
    assert NoEligibleReviewer.matches(refused_same)
