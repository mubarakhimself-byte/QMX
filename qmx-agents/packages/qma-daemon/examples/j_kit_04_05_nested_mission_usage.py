"""Reference usage — J-KIT-04/05 widget binds start; nested Mission is not a live merge."""

from __future__ import annotations

from qma.core.vocabulary.enums import JobHandleState
from qma.daemon.kit_journey import (
    FIFTH_COMPOSITION_MODE_MINTED,
    GAP_0081_CHROME_FILLED,
    J_KIT_04,
    J_KIT_04_05,
    J_KIT_05,
    KIT_JOURNEY_04_E2E_AT_INSPECT_SHA,
    NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA,
    WIDGET_DISPOSE_CANCELS_MISSION,
    WIDGETS_OWN_INVOKE,
    JKit0405Fixture,
    claim_j_kit_04_05_e2e_at_inspect_sha,
    refuse_fifth_composition_mode,
    refuse_nested_mission_grant_union,
    refuse_widget_contribution_without_envelope,
    refuse_widget_dispose_cancels_mission,
    refuse_widget_owned_invoke,
)
from qmf.core import is_ok, is_refusal


def main() -> None:
    assert J_KIT_04 == "J-KIT-04"
    assert J_KIT_05 == "J-KIT-05"
    assert J_KIT_04_05 == "J-KIT-04/05"
    assert KIT_JOURNEY_04_E2E_AT_INSPECT_SHA is False
    assert NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA is False
    assert WIDGETS_OWN_INVOKE is False
    assert WIDGET_DISPOSE_CANCELS_MISSION is False
    assert FIFTH_COMPOSITION_MODE_MINTED is False
    assert GAP_0081_CHROME_FILLED is False
    assert is_refusal(claim_j_kit_04_05_e2e_at_inspect_sha(True))
    assert is_ok(claim_j_kit_04_05_e2e_at_inspect_sha(False))
    assert is_refusal(refuse_widget_owned_invoke())
    assert is_refusal(refuse_widget_dispose_cancels_mission())
    assert is_refusal(refuse_widget_contribution_without_envelope())
    assert is_refusal(refuse_fifth_composition_mode("widget"))
    assert is_refusal(refuse_nested_mission_grant_union())

    fixture = JKit0405Fixture()
    user = fixture.press_widget(caller_kind="user")
    assert is_ok(user)
    assert user.value.caller_kind == "user"
    assert user.value.instance_id == "inst:1"
    assert user.value.handle.state is JobHandleState.QUEUED
    job_id = user.value.job_id
    disposed = fixture.dispose_widget()
    assert is_ok(disposed)
    live = fixture.host.handle_for(job_id)
    assert live is not None
    assert live.state is JobHandleState.QUEUED
    assert is_refusal(fixture.dispose_widget(cancel=True))
    assert is_refusal(fixture.execute_widget_contribution("widget"))
    assert is_refusal(fixture.mint_fifth_composition_mode("widget"))

    nested = fixture.start_nested()
    assert is_ok(nested)
    assert nested.value.caller_kind == "workflow"
    assert nested.value.child_job_id != nested.value.parent_job_id
    assert nested.value.grant_ids == ("grant:b",)
    assert nested.value.spliced is False
    recovered = fixture.crash_parent()
    assert is_ok(recovered)
    assert recovered.value.handle.state is JobHandleState.QUEUED
    assert "work-b" not in recovered.value.parent_node_ids
    assert is_refusal(fixture.splice_child_into_parent())
    assert is_refusal(fixture.start_nested(union_grants=True))

    authored = fixture.include_at_author()
    assert is_ok(authored)
    assert authored.value.version == "1.1.0"
    assert authored.value.runtime_merge is False
    assert is_refusal(fixture.merge_live_task_graphs())
    assert is_refusal(fixture.over_budget_call_depth())


if __name__ == "__main__":
    main()
