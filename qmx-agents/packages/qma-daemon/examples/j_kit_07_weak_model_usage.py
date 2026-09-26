"""Reference usage — J-KIT-07 weak model fills schemas; graduation does not skip enable."""

from __future__ import annotations

from pathlib import Path

from qma.core.vocabulary.enums import FailureClass
from qma.daemon.kit_journey import (
    J_KIT_07,
    JSON_LINES_EXISTED_AT_INSPECT_SHA,
    JSON_RENDER_PINNED,
    KIT_JOURNEY_07_E2E_AT_INSPECT_SHA,
    MCP_APPS_PINNED,
    JKit07Fixture,
    claim_j_kit_07_e2e_at_inspect_sha,
    refuse_graduation_skips_enable_validate,
    refuse_prose_adds_op,
    refuse_scn_0027_branch,
)
from qmf.core import is_ok, is_refusal


def main(root: Path) -> None:
    assert J_KIT_07 == "J-KIT-07"
    assert KIT_JOURNEY_07_E2E_AT_INSPECT_SHA is False
    assert JSON_LINES_EXISTED_AT_INSPECT_SHA is False
    assert JSON_RENDER_PINNED is False
    assert MCP_APPS_PINNED is False
    assert is_refusal(claim_j_kit_07_e2e_at_inspect_sha(True))
    assert is_ok(claim_j_kit_07_e2e_at_inspect_sha(False))
    assert is_refusal(refuse_prose_adds_op())
    assert is_refusal(refuse_graduation_skips_enable_validate())
    assert is_refusal(refuse_scn_0027_branch("A"))

    missing = JKit07Fixture(root=root / "missing")
    filled = missing.fill_schemas(package_id="research-notes", missing_dependency=True)
    assert is_ok(filled)
    closed = missing.validate_pack("research-notes")
    assert is_refusal(closed)
    assert closed.context["fail_closed"] is True
    assert is_refusal(missing.add_op_from_prose())
    assert is_refusal(missing.grant_from_skill())

    ok = JKit07Fixture(root=root / "ok")
    assert is_ok(ok.fill_schemas())
    assert is_ok(ok.validate_pack("research-weak"))
    assert is_ok(ok.export_after_validate())
    assert is_refusal(ok.graduate(skip_enable=True))
    graduated = ok.graduate()
    assert is_ok(graduated)
    assert graduated.value.enabled is True
    assert graduated.value.loop_is_node_state is True
    assert is_ok(ok.json_render_action({"action": "qmb.analysis.project"}))
    assert is_ok(
        ok.mcp_tools_call({"method": "tools/call", "params": {"name": "research-weak:inspect"}})
    )
    assert is_refusal(ok.pin_adapter("@json-render/*"))
    diagnosis = ok.diagnose_last_run()
    assert is_ok(diagnosis)
    assert diagnosis.value.failure_class is FailureClass.WORKFLOW
    assert is_ok(ok.emit_json_line())
    assert is_refusal(ok.place_mini_app_failure_on_qmn())
    assert is_refusal(ok.agents_write_telemetry())
    assert is_refusal(ok.fill_gap_0081_chrome())
    assert is_refusal(ok.fill_gap_0100_dashboard())
    assert is_refusal(ok.mint_loop_engine())


if __name__ == "__main__":
    main(Path("_j_kit_07_example"))
