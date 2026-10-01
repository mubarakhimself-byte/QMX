"""Story 65.4 — J-KIT-04/05 widget binds start; nested Mission is not a live merge."""

from __future__ import annotations

import ast
import runpy
from pathlib import Path
from typing import cast

from qma.core.refusals import NestedGrantUnionRefused
from qma.core.vocabulary.enums import CallerKind, JobHandleState
from qma.daemon.kit_journey import (
    FIFTH_COMPOSITION_MODE_MINTED,
    GAP_0081_CHROME_FILLED,
    INCLUDE_AT_AUTHOR_IMPLEMENTED,
    J_KIT_04,
    J_KIT_04_05,
    J_KIT_05,
    KIT_JOURNEY_04_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_04_INSPECT_SHA,
    KIT_JOURNEY_04_OWNER,
    KIT_JOURNEY_05_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_05_INSPECT_SHA,
    NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA,
    PARENT_AD10_COMPOSITION_MODES,
    WIDGET_DISPOSE_CANCELS_MISSION,
    WIDGET_START_CALLER_KINDS,
    WIDGET_START_IMPLEMENTED,
    WIDGET_START_VERB,
    WIDGETS_OWN_INVOKE,
    JKit0405Fixture,
    claim_j_kit_04_05_e2e_at_inspect_sha,
    claim_nested_mission_occupancy_at_inspect_sha,
    refuse_fifth_composition_mode,
    refuse_nested_mission_grant_union,
    refuse_widget_contribution_without_envelope,
    refuse_widget_dispose_cancels_mission,
    refuse_widget_owned_invoke,
)
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import Result

_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "kit_journey_nested.py"
_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "j_kit_04_05_nested_mission_usage.py"


def _ok[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_inspect_sha_honesty_fixtures_are_not_e2e() -> None:
    assert J_KIT_04 == "J-KIT-04"
    assert J_KIT_05 == "J-KIT-05"
    assert J_KIT_04_05 == "J-KIT-04/05"
    assert KIT_JOURNEY_04_INSPECT_SHA == KIT_JOURNEY_05_INSPECT_SHA == "34c148b"
    assert KIT_JOURNEY_04_E2E_AT_INSPECT_SHA is False
    assert KIT_JOURNEY_05_E2E_AT_INSPECT_SHA is False
    assert NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA is False
    assert WIDGET_START_IMPLEMENTED is True
    assert WIDGETS_OWN_INVOKE is False
    assert WIDGET_DISPOSE_CANCELS_MISSION is False
    assert FIFTH_COMPOSITION_MODE_MINTED is False
    assert INCLUDE_AT_AUTHOR_IMPLEMENTED is True
    assert GAP_0081_CHROME_FILLED is False
    assert WIDGET_START_VERB == "start"
    assert frozenset({CallerKind.USER, CallerKind.AGENT}) == WIDGET_START_CALLER_KINDS
    assert len(PARENT_AD10_COMPOSITION_MODES) == 4
    assert "widget" not in PARENT_AD10_COMPOSITION_MODES
    claimed = claim_j_kit_04_05_e2e_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert claimed.context["e2e_at_inspect_sha"] is False
    assert claimed.context["class_test_existence_is_e2e"] is False
    assert claimed.context["inspect_sha"] == "34c148b"
    assert claimed.context["branch"] == "D"
    assert claimed.context["nested_mission_occupancy_existed_at_inspect_sha"] is False
    assert _ok(claim_j_kit_04_05_e2e_at_inspect_sha(False)) is False
    assert is_refusal(claim_j_kit_04_05_e2e_at_inspect_sha("wired"))
    assert is_refusal(claim_nested_mission_occupancy_at_inspect_sha(True))
    assert _ok(claim_nested_mission_occupancy_at_inspect_sha(False)) is False


def test_widget_binds_start_user_or_agent_dispose_does_not_cancel() -> None:
    fixture = JKit0405Fixture()
    assert fixture.owner == KIT_JOURNEY_04_OWNER == "COMP-QMA-DAEMON"
    assert fixture.journey == J_KIT_04_05
    assert fixture.journeys == (J_KIT_04, J_KIT_05)
    assert fixture.e2e_at_inspect_sha is False
    assert fixture.widgets_own_invoke is False
    assert fixture.widget_dispose_cancels_mission is False
    assert fixture.fifth_composition_mode_minted is False
    binding = _ok(fixture.bind_widget_start())
    assert binding.bound_verb == "start"
    assert binding.owns_invoke is False
    assert binding.composition_mode in PARENT_AD10_COMPOSITION_MODES
    owned = fixture.bind_widget_start(owns_invoke=True)
    assert is_refusal(owned)
    assert owned.context["owns_invoke"] is False
    assert is_refusal(refuse_widget_owned_invoke())

    user = _ok(fixture.press_widget(caller_kind="user"))
    assert user.caller_kind == "user"
    assert user.instance_id == "inst:1"
    assert user.bound_verb == "start"
    assert user.owns_invoke is False
    assert user.handle.state is JobHandleState.QUEUED
    body = dict(user.to_payload())
    assert body["journey"] == J_KIT_04
    assert body["journeys"] == [J_KIT_04, J_KIT_05]
    assert body["cancelled_on_dispose"] is False

    agent_host = JKit0405Fixture()
    agent = _ok(agent_host.press_widget(caller_kind="agent"))
    assert agent.caller_kind == "agent"
    assert agent.instance_id == "inst:1"

    workflow = JKit0405Fixture().press_widget(caller_kind="workflow")
    assert is_refusal(workflow)
    assert workflow.context["field"] == "caller_kind"
    missing = JKit0405Fixture().press_widget(envelope=None)
    assert is_refusal(missing)
    assert missing.context["envelope_present"] is False
    blank = JKit0405Fixture().press_widget(instance_id="")
    assert is_refusal(blank)

    job_id = user.job_id
    disposed = _ok(fixture.dispose_widget())
    assert disposed.owns_invoke is False
    assert disposed.cancelled_on_dispose is False
    assert disposed.handle.state is JobHandleState.QUEUED
    assert disposed.handle.state is not JobHandleState.CANCELLED
    live = fixture.host.handle_for(job_id)
    assert live is not None
    assert live.state is JobHandleState.QUEUED
    cancelled_dispose = fixture.dispose_widget(cancel=True)
    assert is_refusal(cancelled_dispose)
    still = fixture.host.handle_for(job_id)
    assert still is not None
    assert still.state is JobHandleState.QUEUED
    assert is_refusal(refuse_widget_dispose_cancels_mission())

    fifth = fixture.mint_fifth_composition_mode("widget")
    assert is_refusal(fifth)
    assert fifth.context["fifth_composition_mode_minted"] is False
    assert is_refusal(refuse_fifth_composition_mode("widget"))
    chrome = fixture.fill_gap_0081_chrome()
    assert is_refusal(chrome)
    assert chrome.context["gap_0081_chrome_filled"] is False


def test_widget_contribution_without_envelope_is_refused() -> None:
    fixture = JKit0405Fixture()
    _ok(fixture.bind_widget_start())
    for point in ("widget", "ui_widget", "ui_view"):
        refused = fixture.execute_widget_contribution(point)
        assert is_refusal(refused)
        assert refused.context["envelope_present"] is False
        assert refused.context["owns_invoke"] is False
    with_envelope = fixture.execute_widget_contribution(
        "widget",
        envelope={"logical_invocation_id": "inv:bare"},
    )
    assert is_refusal(with_envelope)
    assert with_envelope.context["owns_invoke"] is False
    assert with_envelope.context["envelope_present"] is True
    assert is_refusal(refuse_widget_contribution_without_envelope())


def test_nested_mission_has_own_job_handle_crash_does_not_splice() -> None:
    fixture = JKit0405Fixture()
    nested = _ok(fixture.start_nested())
    assert nested.caller_kind == "workflow"
    assert nested.child_job_id != nested.parent_job_id
    assert nested.child_graph_id != nested.parent_graph_id
    assert nested.child_mission_id != nested.parent_mission_id
    assert nested.handle.state is JobHandleState.QUEUED
    assert nested.grant_ids == ("grant:b",)
    assert "grant:a" not in nested.grant_ids
    assert nested.union is False
    assert nested.spliced is False
    assert nested.child_node_ids == ("work-b",)
    assert nested.parent_node_ids == ("start-b",)
    assert "work-b" not in nested.parent_node_ids
    body = dict(nested.to_payload())
    assert body["journey"] == J_KIT_05
    assert body["spliced"] is False

    queried = _ok(fixture.query_nested_state())
    assert queried.child_job_id == nested.child_job_id
    assert queried.handle.state is JobHandleState.QUEUED

    recovered = _ok(fixture.crash_parent())
    assert recovered.spliced is False
    assert "work-b" not in recovered.parent_node_ids
    assert recovered.child_node_ids == ("work-b",)
    assert recovered.handle.state is JobHandleState.QUEUED
    assert fixture.host.is_live(nested.child_graph_id) is True
    spliced = fixture.splice_child_into_parent()
    assert is_refusal(spliced)
    assert spliced.context["spliced"] is False


def test_nested_invoke_does_not_union_grants_cancel_follows_child() -> None:
    fixture = JKit0405Fixture()
    nested = _ok(fixture.start_nested())
    assert nested.grant_ids == ("grant:b",)
    unioned = fixture.start_nested(union_grants=True)
    assert is_refusal(unioned)
    assert isinstance(unioned, NestedGrantUnionRefused)
    assert unioned.context["union"] is False
    assert unioned.context["branch"] == "C"
    leaked = JKit0405Fixture().start_nested(grant_id="grant:a")
    assert is_refusal(leaked)
    assert isinstance(leaked, NestedGrantUnionRefused)
    assert is_refusal(refuse_nested_mission_grant_union())

    cancelled = _ok(fixture.cancel_nested())
    assert cancelled.handle.state is JobHandleState.CANCELLED
    parent_live = fixture.host.jobs.handle_for(nested.parent_job_id)
    assert parent_live is not None
    assert parent_live.state is JobHandleState.QUEUED


def test_include_at_author_new_version_live_merge_refused() -> None:
    fixture = JKit0405Fixture()
    authored = _ok(fixture.include_at_author())
    assert authored.qualified_id == "research-corpus:a"
    assert authored.version == "1.1.0"
    assert authored.parent_version == "1.0.0"
    assert authored.runtime_merge is False
    assert "work-b" in authored.node_ids
    assert "start-b" not in authored.node_ids
    body = dict(authored.to_payload())
    assert body["journey"] == J_KIT_05
    assert body["runtime_merge"] is False
    kept = fixture.host.templates.get_versioned("research-corpus:a", "1.0.0")
    assert kept is not None
    assert {node["id"] for node in kept.nodes} == {"start-b"}

    merged = fixture.merge_live_task_graphs()
    assert is_refusal(merged)
    assert merged.context["code"] == "INVALID_INPUT"
    assert merged.context["merged"] is False
    assert merged.context["substituted"] is False
    assert merged.context["substituted_instance"] is False
    assert merged.context["substituted_version"] is False
    assert merged.context["substituted_account"] is False

    over = fixture.over_budget_call_depth()
    assert is_refusal(over)
    assert over.context["field"] == "call_depth"
    assert over.context["code"] == "INVALID_INPUT"
    assert over.context["call_depth"] == 2
    assert over.context["ceiling"] == 1
    assert over.context["gap_0108"] is False


def test_module_never_imports_qmb() -> None:
    source = _SRC.read_text(encoding="utf-8")
    assert "import qmb" not in source
    assert "from qmb" not in source
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    assert not any(name == "qmb" or name.startswith("qmb.") for name in imports)


def test_reference_usage_example_runs() -> None:
    namespace = runpy.run_path(str(_EXAMPLE))
    main = cast("object", namespace["main"])
    assert callable(main)
    main()
