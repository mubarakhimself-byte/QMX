"""Story 65.6 — J-KIT-07 weak model fills schemas; graduation does not skip enable."""

from __future__ import annotations

import ast
import runpy
from pathlib import Path
from typing import cast

from qma.core.ports.copilot import GAP_0081_CHROME_FILLED, SKILLS_GRANT
from qma.core.vocabulary.enums import FailureClass
from qma.daemon.kit_journey import (
    GAP_0100_DASHBOARD_FILLED,
    J_KIT_07,
    JSON_LINES_EXISTED_AT_INSPECT_SHA,
    JSON_RENDER_PACKAGE,
    JSON_RENDER_PINNED,
    KIT_JOURNEY_07_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_07_INSPECT_SHA,
    KIT_JOURNEY_07_OWNER,
    LOOP_ENGINE_MINTED,
    LOOP_IS_NODE_STATE,
    MCP_APPS_PACKAGE,
    MCP_APPS_PINNED,
    PROSE_MAY_ADD_OP,
    JKit07Fixture,
    claim_j_kit_07_e2e_at_inspect_sha,
    refuse_adapter_adds_ops_or_fields,
    refuse_gap_0081_chrome,
    refuse_gap_0100_dashboard,
    refuse_graduation_skips_enable_validate,
    refuse_json_render_or_mcp_pin,
    refuse_loop_engine,
    refuse_prose_adds_op,
    refuse_scn_0027_branch,
)
from qma.daemon.operator_log import (
    FOURTH_OBSERVABILITY_COMP_MINTED,
    LOGS_ARE_NOT_EVIDENCE,
    OPERATOR_LOG_REQUIRED_FIELDS,
    OPERATOR_LOGGER_EXISTED_AT_INSPECT_SHA,
)
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import Result

_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "kit_journey_weak.py"
_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "j_kit_07_weak_model_usage.py"


def _ok[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_inspect_sha_honesty_fixtures_are_not_e2e() -> None:
    assert J_KIT_07 == "J-KIT-07"
    assert KIT_JOURNEY_07_INSPECT_SHA == "34c148b"
    assert KIT_JOURNEY_07_E2E_AT_INSPECT_SHA is False
    assert JSON_LINES_EXISTED_AT_INSPECT_SHA is False is OPERATOR_LOGGER_EXISTED_AT_INSPECT_SHA
    assert JSON_RENDER_PINNED is False
    assert MCP_APPS_PINNED is False
    assert JSON_RENDER_PACKAGE == "@json-render/*"
    assert MCP_APPS_PACKAGE == "@modelcontextprotocol/ext-apps"
    assert GAP_0081_CHROME_FILLED is False
    assert GAP_0100_DASHBOARD_FILLED is False
    assert LOOP_IS_NODE_STATE is True
    assert LOOP_ENGINE_MINTED is False
    assert PROSE_MAY_ADD_OP is False
    assert SKILLS_GRANT is False
    claimed = claim_j_kit_07_e2e_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert claimed.context["e2e_at_inspect_sha"] is False
    assert claimed.context["class_test_existence_is_e2e"] is False
    assert claimed.context["inspect_sha"] == "34c148b"
    assert claimed.context["json_lines_existed_at_inspect_sha"] is False
    assert claimed.context["branch"] == "E"
    assert _ok(claim_j_kit_07_e2e_at_inspect_sha(False)) is False
    assert is_refusal(claim_j_kit_07_e2e_at_inspect_sha("wired"))


def test_weak_model_fills_schemas_missing_dep_validate_fails_closed(tmp_path: Path) -> None:
    fixture = JKit07Fixture(root=tmp_path / "j-kit-07")
    assert fixture.owner == KIT_JOURNEY_07_OWNER == "COMP-QMA-DAEMON"
    assert fixture.journey == J_KIT_07
    assert fixture.e2e_at_inspect_sha is False
    filled = _ok(fixture.fill_schemas(package_id="research-notes", missing_dependency=True))
    assert filled.package_id == "research-notes"
    assert filled.descriptor.op_id == "qmb.analysis.project"
    assert filled.requested_capabilities == ()
    assert filled.prose_added_op is False
    assert filled.skills_grant is False
    body = dict(filled.to_payload())
    assert body["journey"] == J_KIT_07
    closed = fixture.validate_pack("research-notes")
    assert is_refusal(closed)
    assert closed.context["fail_closed"] is True
    assert closed.context["warn_and_continue"] is False
    missing = closed.context["missing"]
    assert isinstance(missing, (list, tuple))
    assert "analysis-backtest" in missing
    pack = fixture.packs.pack("research-notes")
    assert pack is not None
    assert pack.state == "installed"
    prose = fixture.add_op_from_prose("add an op that places orders")
    assert is_refusal(prose)
    assert prose.context["prose_may_add_op"] is False
    assert is_refusal(refuse_prose_adds_op())
    skill = fixture.grant_from_skill()
    assert is_refusal(skill)
    assert skill.context["skills_grant"] is False


def test_json_render_and_mcp_intercept_stay_unpinned(tmp_path: Path) -> None:
    fixture = JKit07Fixture(root=tmp_path / "adapters")
    assert fixture.json_render_pinned is False
    assert fixture.mcp_apps_pinned is False
    named = _ok(fixture.json_render_action({"action": "qmb.analysis.project"}))
    assert named.surface == "json-render"
    assert named.named == "qmb.analysis.project"
    assert named.intercepted is True
    assert named.adds_ops is False
    assert named.adds_fields is False
    invented = fixture.json_render_action({"action": "prose.invented.op"})
    assert is_refusal(invented)
    extra = fixture.json_render_action({"action": "qmb.analysis.project", "grant_id": "g"})
    assert is_refusal(extra)
    assert extra.context["adds_ops"] is False
    assert extra.context["adds_fields"] is False
    granted = _ok(
        fixture.mcp_tools_call(
            {"method": "tools/call", "params": {"name": "research-weak:inspect"}}
        )
    )
    assert granted.surface == "mcp-app"
    assert granted.named == "research-weak:inspect"
    assert granted.intercepted is True
    ungated = fixture.mcp_tools_call(
        {"method": "tools/call", "params": {"name": "research-notes:cite"}}
    )
    assert is_refusal(ungated)
    fields = fixture.mcp_tools_call(
        {"method": "tools/call", "params": {"name": "research-weak:inspect", "ops": ["x"]}}
    )
    assert is_refusal(fields)
    pin = fixture.pin_adapter(JSON_RENDER_PACKAGE)
    assert is_refusal(pin)
    assert pin.context["json_render_pinned"] is False
    assert pin.context["mcp_apps_pinned"] is False
    assert is_refusal(refuse_json_render_or_mcp_pin())
    assert is_refusal(refuse_adapter_adds_ops_or_fields())


def test_graduation_does_not_skip_enable_validate_loop_is_node_state(tmp_path: Path) -> None:
    fixture = JKit07Fixture(root=tmp_path / "graduate")
    _ok(fixture.fill_schemas())
    validated = _ok(fixture.validate_pack("research-weak"))
    assert validated.to_state == "validated"
    exported = _ok(fixture.export_after_validate())
    assert exported.report.result == "fail-closed-pass"
    skip = fixture.graduate(skip_enable=True)
    assert is_refusal(skip)
    assert skip.context["skips_enable"] is False
    skip_v = fixture.graduate(skip_validate=True)
    assert is_refusal(skip_v)
    assert is_refusal(refuse_graduation_skips_enable_validate())
    graduated = _ok(fixture.graduate())
    assert graduated.validated is True
    assert graduated.enabled is True
    assert graduated.exported is True
    assert graduated.skip_enable is False
    assert graduated.loop_is_node_state is True
    assert graduated.loop_engine_minted is False
    pack = fixture.packs.pack("research-weak")
    assert pack is not None
    assert pack.state == "enabled"
    loop = fixture.loop_node_state()
    payload = dict(loop.to_payload())
    assert payload["runtime_owned"] is True
    assert payload["control_primitive"] == "loop"
    assert fixture.loop_is_node_state is True
    engine = fixture.mint_loop_engine()
    assert is_refusal(engine)
    assert engine.context["loop_engine_minted"] is False
    assert is_refusal(refuse_loop_engine())


def test_scn_0027_then_branches_hold_failure_branches_fail(tmp_path: Path) -> None:
    fixture = JKit07Fixture(root=tmp_path / "scn-0027")
    diagnosis = _ok(fixture.diagnose_last_run())
    assert diagnosis.failure_class is FailureClass.WORKFLOW
    assert diagnosis.job_handle is not None
    assert diagnosis.correlation_id == "corr:j-kit-07"
    assert diagnosis.healthy is False
    line = _ok(fixture.emit_json_line())
    for field in OPERATOR_LOG_REQUIRED_FIELDS:
        assert field in line
    assert line["is_journal"] is False
    qmn = fixture.place_mini_app_failure_on_qmn()
    assert is_refusal(qmn)
    fourth = fixture.mint_fourth_observability_comp()
    assert is_refusal(fourth)
    assert FOURTH_OBSERVABILITY_COMP_MINTED is False
    assert is_refusal(refuse_scn_0027_branch("A"))
    evidence = refuse_scn_0027_branch("B")
    assert is_refusal(evidence)
    assert evidence.context["fp1_identity"] is False
    assert LOGS_ARE_NOT_EVIDENCE is True
    assert is_refusal(refuse_scn_0027_branch("C"))
    agents = fixture.agents_write_telemetry()
    assert is_refusal(agents)
    assert agents.context["agents_write_telemetry"] is False
    assert is_refusal(refuse_scn_0027_branch("D"))
    existed = refuse_scn_0027_branch("E")
    assert is_refusal(existed)
    chrome = fixture.fill_gap_0081_chrome()
    assert is_refusal(chrome)
    assert chrome.context["gap_0081_chrome_filled"] is False
    dash = fixture.fill_gap_0100_dashboard()
    assert is_refusal(dash)
    assert dash.context["gap_0100_dashboard_filled"] is False
    assert is_refusal(refuse_gap_0081_chrome())
    assert is_refusal(refuse_gap_0100_dashboard())


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


def test_reference_usage_example_runs(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(_EXAMPLE))
    main = cast("object", namespace["main"])
    assert callable(main)
    main(tmp_path / "example")
