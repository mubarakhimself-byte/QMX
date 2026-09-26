"""Story 65.2 — J-KIT-02 optional panel cannot apply; dispose does not cancel."""

from __future__ import annotations

import ast
import runpy
from pathlib import Path
from typing import cast

from qma.core.ports.copilot import APP_USE_MAY_APPLY
from qma.core.vocabulary.enums import FailureClass, JobHandleState
from qma.daemon.kit_journey import (
    GAP_0081_CHROME_FILLED,
    J_KIT_02,
    KIT_JOURNEY_02_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_02_INSPECT_SHA,
    KIT_JOURNEY_02_OWNER,
    PANEL_DISPOSE_CANCELS_JOB_HANDLE,
    RECONNECT_REPLAYS_UNACKED_INTENT,
    STORY_58_4_IS_APPLY_ORACLE,
    JKit02Fixture,
    claim_j_kit_02_e2e_at_inspect_sha,
    refuse_panel_applies_change_request,
    refuse_tab_close_cancels_job_handle,
)
from qma.daemon.sessions import ProductSessionProfile
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import Result

_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "kit_journey.py"
_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "j_kit_02_optional_panel_usage.py"


def _ok[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_inspect_sha_honesty_fixtures_are_not_e2e() -> None:
    assert J_KIT_02 == "J-KIT-02"
    assert KIT_JOURNEY_02_INSPECT_SHA == "34c148b"
    assert KIT_JOURNEY_02_E2E_AT_INSPECT_SHA is False
    assert APP_USE_MAY_APPLY is False
    assert PANEL_DISPOSE_CANCELS_JOB_HANDLE is False
    assert RECONNECT_REPLAYS_UNACKED_INTENT is False
    assert STORY_58_4_IS_APPLY_ORACLE is True
    assert GAP_0081_CHROME_FILLED is False
    claimed = claim_j_kit_02_e2e_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert claimed.context["e2e_at_inspect_sha"] is False
    assert claimed.context["class_test_existence_is_e2e"] is False
    assert claimed.context["inspect_sha"] == "34c148b"
    assert _ok(claim_j_kit_02_e2e_at_inspect_sha(False)) is False
    assert is_refusal(claim_j_kit_02_e2e_at_inspect_sha("wired"))


def test_panel_ask_why_returns_failure_class_and_job_handle() -> None:
    fixture = JKit02Fixture()
    assert fixture.owner == KIT_JOURNEY_02_OWNER == "COMP-QMA-DAEMON"
    assert fixture.journey == J_KIT_02
    assert fixture.e2e_at_inspect_sha is False
    assert fixture.app_use_may_apply is False
    session = _ok(fixture.open_instance_a_with_panel())
    assert session.profile is ProductSessionProfile.APP_USE
    assert session.app_instance_id == "inst:A"
    assert _ok(fixture.in_app_panels()) == ("panel:a",)

    failed = _ok(fixture.fail_last_run())
    assert failed.state is JobHandleState.FAILED
    report = _ok(fixture.ask_why_last_run_failed())
    assert report.diagnosis.failure_class is FailureClass.WORKFLOW
    assert report.diagnosis.job_handle is not None
    assert report.diagnosis.job_handle.job_id == failed.job_id
    assert report.diagnosis.job_handle.attempt_id == 2
    assert report.can_edit_pack is False
    assert report.applies is False
    body = dict(report.to_payload())
    assert body["journey"] == J_KIT_02
    assert body["failure_class"] == "workflow"
    assert body["job_id"] == failed.job_id
    assert body["can_edit_pack"] is False

    null_handle = _ok(fixture.ask_why_without_job())
    assert null_handle.diagnosis.job_handle is None
    assert null_handle.diagnosis.failure_class is FailureClass.DEPENDENCY
    assert dict(null_handle.to_payload())["job_id"] is None

    edited = fixture.edit_pack()
    assert is_refusal(edited)
    assert edited.context["writes_package_source"] is False
    assert edited.context["profile"] == "app-use"


def test_app_use_mints_change_request_and_must_not_apply() -> None:
    fixture = JKit02Fixture()
    _ok(fixture.open_instance_a_with_panel())
    before = dict(_ok(fixture.v1_snapshot()).to_payload())
    minted = _ok(fixture.mint_change_request())
    assert minted.from_session == "psess:app-a"
    assert minted.source_instance_id == "inst:A"
    after_mint = dict(_ok(fixture.v1_snapshot()).to_payload())
    assert after_mint == before

    panel_apply = fixture.apply_from_panel()
    assert is_refusal(panel_apply)
    assert panel_apply.context["branch"] == "B"
    assert panel_apply.context["applies"] is False
    assert panel_apply.context["story_58_4_is_apply_oracle"] is True
    also = refuse_panel_applies_change_request()
    assert is_refusal(also)
    assert also.context["journey"] == J_KIT_02

    applied = _ok(fixture.apply_authoring_plus_operator())
    assert applied.outcome == "applied"
    assert applied.operator_principal == "operator"
    assert applied.authoring_principal == "authoring"
    still = dict(_ok(fixture.v1_snapshot()).to_payload())
    assert still == before
    assert still["instance_id"] == "inst:A"
    assert still["version"] == "1.0.0"


def test_dispose_does_not_cancel_and_reconnect_does_not_replay() -> None:
    fixture = JKit02Fixture()
    _ok(fixture.open_instance_a_with_panel())
    running = _ok(fixture.start_running_work())
    assert running.state is JobHandleState.RUNNING

    closed = _ok(fixture.dispose_panel())
    assert closed.product_session_id == "psess:app-a"
    live = fixture.host.jobs.handle_for(running.job_id)
    assert live is not None
    assert live.state is JobHandleState.RUNNING
    assert _ok(fixture.in_app_panels()) == ()

    future = _ok(fixture.close_future_ui_tab())
    assert future.product_session_id == "psess:app-a"
    still = fixture.host.jobs.handle_for(running.job_id)
    assert still is not None
    assert still.state is JobHandleState.RUNNING

    snapshot = _ok(fixture.reconnect())
    assert snapshot.replays_unacked_intent is False is RECONNECT_REPLAYS_UNACKED_INTENT
    assert snapshot.is_query is True
    replay = fixture.reconnect_replaying_unacked()
    assert is_refusal(replay)
    assert replay.context["replays_unacked_intent"] is False

    cancelled = fixture.dispose_panel(cancel_job=True)
    assert is_refusal(cancelled)
    assert cancelled.context["branch"] == "C"
    assert cancelled.context["cancels"] is False
    assert is_refusal(refuse_tab_close_cancels_job_handle())
    reread = fixture.host.jobs.handle_for(running.job_id)
    assert reread is not None
    assert reread.state is JobHandleState.RUNNING


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
