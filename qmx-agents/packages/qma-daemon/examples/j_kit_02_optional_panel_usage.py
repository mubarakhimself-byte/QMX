"""Reference usage — J-KIT-02 optional panel cannot apply; dispose does not cancel."""

from __future__ import annotations

from qma.core.vocabulary.enums import FailureClass, JobHandleState
from qma.daemon.kit_journey import (
    APP_USE_MAY_APPLY,
    GAP_0081_CHROME_FILLED,
    J_KIT_02,
    KIT_JOURNEY_02_E2E_AT_INSPECT_SHA,
    PANEL_DISPOSE_CANCELS_JOB_HANDLE,
    RECONNECT_REPLAYS_UNACKED_INTENT,
    STORY_58_4_IS_APPLY_ORACLE,
    JKit02Fixture,
    claim_j_kit_02_e2e_at_inspect_sha,
    refuse_panel_applies_change_request,
    refuse_tab_close_cancels_job_handle,
)
from qmf.core import is_ok, is_refusal


def main() -> None:
    assert J_KIT_02 == "J-KIT-02"
    assert KIT_JOURNEY_02_E2E_AT_INSPECT_SHA is False
    assert APP_USE_MAY_APPLY is False
    assert PANEL_DISPOSE_CANCELS_JOB_HANDLE is False
    assert RECONNECT_REPLAYS_UNACKED_INTENT is False
    assert STORY_58_4_IS_APPLY_ORACLE is True
    assert GAP_0081_CHROME_FILLED is False
    assert is_refusal(claim_j_kit_02_e2e_at_inspect_sha(True))
    assert is_ok(claim_j_kit_02_e2e_at_inspect_sha(False))
    assert is_refusal(refuse_panel_applies_change_request())
    assert is_refusal(refuse_tab_close_cancels_job_handle())

    fixture = JKit02Fixture()
    opened = fixture.open_instance_a_with_panel()
    assert is_ok(opened)
    assert opened.value.app_instance_id == "inst:A"
    assert is_ok(fixture.fail_last_run())
    why = fixture.ask_why_last_run_failed()
    assert is_ok(why)
    assert why.value.diagnosis.failure_class is FailureClass.WORKFLOW
    assert why.value.diagnosis.job_handle is not None
    assert why.value.can_edit_pack is False
    assert is_refusal(fixture.edit_pack())

    minted = fixture.mint_change_request()
    assert is_ok(minted)
    assert is_refusal(fixture.apply_from_panel())
    applied = fixture.apply_authoring_plus_operator()
    assert is_ok(applied)
    assert applied.value.outcome == "applied"
    still = fixture.v1_snapshot()
    assert is_ok(still)
    assert still.value.version == "1.0.0"

    running = fixture.start_running_work()
    assert is_ok(running)
    assert running.value.state is JobHandleState.RUNNING
    closed = fixture.dispose_panel()
    assert is_ok(closed)
    live = fixture.host.jobs.handle_for(running.value.job_id)
    assert live is not None
    assert live.state is JobHandleState.RUNNING
    assert is_ok(fixture.close_future_ui_tab())
    snapshot = fixture.reconnect()
    assert is_ok(snapshot)
    assert snapshot.value.replays_unacked_intent is False
    assert is_refusal(fixture.reconnect_replaying_unacked())


if __name__ == "__main__":
    main()
