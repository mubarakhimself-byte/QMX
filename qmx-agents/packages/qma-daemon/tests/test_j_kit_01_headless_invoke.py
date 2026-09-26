"""Story 65.1 — J-KIT-01 headless pack with no copilot still invokes."""

from __future__ import annotations

import ast
import runpy
from pathlib import Path
from typing import cast

from qma.core.plugins import COPILOT_PROFILE_EXISTED_AT_INSPECT_SHA
from qma.core.vocabulary.enums import JobHandleState
from qma.daemon.kit_journey import (
    COPILOT_REQUIRED_TO_SHIP,
    ENABLE_AFTER_VALIDATE_IS_GRANT,
    GAP_0081_CHROME_FILLED,
    HEADLESS_HAS_COPILOT_PANEL,
    HEADLESS_HAS_NAVIGATION,
    INSTALL_IS_GRANT,
    J_KIT_01,
    KIT_JOURNEY_01_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_01_INSPECT_SHA,
    KIT_JOURNEY_01_OWNER,
    PACK_MAY_OMIT_COPILOT_PROFILE,
    PACK_SDK_INSPECT_SHA,
    SESSION_GRANT_RECORD_IS_GRANT,
    JKit01Fixture,
    claim_j_kit_01_e2e_at_inspect_sha,
    refuse_copilot_required_to_ship,
    refuse_headless_in_app_panel,
)
from qma.wire.invocation_envelope import PublicCallTransport
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import Result

_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "kit_journey.py"
_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "j_kit_01_headless_invoke_usage.py"


def _ok[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_inspect_sha_honesty_fixtures_are_not_e2e() -> None:
    assert J_KIT_01 == "J-KIT-01"
    assert KIT_JOURNEY_01_INSPECT_SHA == PACK_SDK_INSPECT_SHA == "34c148b"
    assert KIT_JOURNEY_01_E2E_AT_INSPECT_SHA is False
    assert COPILOT_PROFILE_EXISTED_AT_INSPECT_SHA is False
    assert COPILOT_REQUIRED_TO_SHIP is False
    assert PACK_MAY_OMIT_COPILOT_PROFILE is True
    assert HEADLESS_HAS_COPILOT_PANEL is False
    assert HEADLESS_HAS_NAVIGATION is False
    assert INSTALL_IS_GRANT is False
    assert ENABLE_AFTER_VALIDATE_IS_GRANT is False
    assert SESSION_GRANT_RECORD_IS_GRANT is True
    assert GAP_0081_CHROME_FILLED is False
    claimed = claim_j_kit_01_e2e_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert claimed.context["e2e_at_inspect_sha"] is False
    assert claimed.context["class_test_existence_is_e2e"] is False
    assert claimed.context["inspect_sha"] == "34c148b"
    assert _ok(claim_j_kit_01_e2e_at_inspect_sha(False)) is False
    assert is_refusal(claim_j_kit_01_e2e_at_inspect_sha("wired"))


def test_headless_pack_cli_and_wire_invoke_produce_job_handle(tmp_path: Path) -> None:
    fixture = JKit01Fixture(root=tmp_path / "j-kit-01")
    assert fixture.owner == KIT_JOURNEY_01_OWNER == "COMP-QMA-DAEMON"
    assert fixture.journey == J_KIT_01
    assert fixture.e2e_at_inspect_sha is False
    assert fixture.install_is_grant is False
    enabled = _ok(fixture.enable_headless_pack())
    assert enabled.to_state == "enabled"
    assert fixture.packs.grant_ids() == ()
    loaded = fixture.packs.loader.get("research-corpus")
    assert loaded is not None
    assert loaded.manifest.copilot_profile is None
    assert loaded.manifest.views == ()
    assert loaded.manifest.is_headless is True
    assert loaded.grant_record_ids == ()
    points = {row.point for row in loaded.published}
    assert "view" not in points
    assert "copilot" not in points
    assert "copilot_profile" not in points
    assert "tool" in points

    cli = _ok(fixture.invoke_authoring(transport=PublicCallTransport.CLI))
    assert cli.transport is PublicCallTransport.CLI
    assert cli.handle.state is JobHandleState.RUNNING
    assert cli.handle.job_id.startswith("job:")
    assert cli.is_headless is True
    assert cli.enabled is True
    assert cli.grant_ids_after_enable == ()
    assert cli.session_grant_id == "grant:j-kit-01"
    assert cli.in_app_panels == ()
    assert cli.referenced is True
    assert cli.qualified_id == "research-corpus:inspect"
    home = _ok(fixture.host.sessions.get("psess:home"))
    assert home.profile.value == "authoring"
    assert home.app_instance_id is None
    assert _ok(fixture.host.sessions.attached_tabs("psess:home")) == ()
    assert _ok(fixture.in_app_panels()) == ()

    wire = _ok(fixture.invoke_authoring(transport="wire"))
    assert wire.transport is PublicCallTransport.WIRE
    assert wire.handle.state is JobHandleState.RUNNING
    assert wire.handle.job_id != cli.handle.job_id
    assert fixture.host.jobs.handle_for(cli.handle.job_id) is not None
    assert fixture.host.jobs.handle_for(wire.handle.job_id) is not None
    body = dict(cli.to_payload())
    assert body["journey"] == J_KIT_01
    assert body["transport"] == "cli"
    assert body["in_app_panels"] == []
    in_process = fixture.invoke_authoring(transport=PublicCallTransport.IN_PROCESS)
    assert is_refusal(in_process)
    assert in_process.context["field"] == "transport"


def test_requiring_a_copilot_to_ship_fails_and_install_is_not_grant(tmp_path: Path) -> None:
    fixture = JKit01Fixture(root=tmp_path / "branch-a")
    refused = fixture.enable_headless_pack(require_copilot=True)
    assert is_refusal(refused)
    assert refused.context["branch"] == "A"
    assert refused.context["fixture_failed"] is True
    assert refused.context["copilot_required_to_ship"] is False
    assert refused.context["pack_may_omit_copilot_profile"] is True
    assert refused.context["install_is_grant"] is False
    assert fixture.packs.grant_ids() == ()
    pack = fixture.packs.pack("research-corpus")
    assert pack is not None
    assert pack.state == "validated"
    assert fixture.packs.loader.get("research-corpus") is None
    also = refuse_copilot_required_to_ship()
    assert is_refusal(also)
    assert also.context["journey"] == J_KIT_01
    invoke = fixture.invoke_authoring(transport="cli")
    assert is_refusal(invoke)
    assert invoke.context["field"] == "enable"


def test_no_in_app_panel_and_chrome_is_not_filled(tmp_path: Path) -> None:
    fixture = JKit01Fixture(root=tmp_path / "no-panel")
    _ok(fixture.enable_headless_pack())
    _ok(fixture.invoke_authoring(transport="cli"))
    panel = fixture.open_in_app_panel("panel:app")
    assert is_refusal(panel)
    assert panel.context["in_app_panel"] is False
    assert panel.context["gap_0081_chrome_filled"] is False is GAP_0081_CHROME_FILLED
    assert is_refusal(refuse_headless_in_app_panel())
    assert HEADLESS_HAS_COPILOT_PANEL is False
    assert HEADLESS_HAS_NAVIGATION is False


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
