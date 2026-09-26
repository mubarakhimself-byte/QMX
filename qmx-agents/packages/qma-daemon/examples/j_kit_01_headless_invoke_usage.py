"""Reference usage — J-KIT-01 headless pack with no copilot still invokes."""

from __future__ import annotations

from pathlib import Path

from qma.core.vocabulary.enums import JobHandleState
from qma.daemon.kit_journey import (
    COPILOT_REQUIRED_TO_SHIP,
    GAP_0081_CHROME_FILLED,
    INSTALL_IS_GRANT,
    J_KIT_01,
    KIT_JOURNEY_01_E2E_AT_INSPECT_SHA,
    JKit01Fixture,
    claim_j_kit_01_e2e_at_inspect_sha,
    refuse_copilot_required_to_ship,
)
from qma.wire.invocation_envelope import PublicCallTransport
from qmf.core import is_ok, is_refusal


def main(root: Path) -> None:
    assert J_KIT_01 == "J-KIT-01"
    assert KIT_JOURNEY_01_E2E_AT_INSPECT_SHA is False
    assert COPILOT_REQUIRED_TO_SHIP is False
    assert INSTALL_IS_GRANT is False
    assert GAP_0081_CHROME_FILLED is False
    assert is_refusal(claim_j_kit_01_e2e_at_inspect_sha(True))
    assert is_ok(claim_j_kit_01_e2e_at_inspect_sha(False))
    assert is_refusal(refuse_copilot_required_to_ship())

    fixture = JKit01Fixture(root=root)
    enabled = fixture.enable_headless_pack()
    assert is_ok(enabled)
    assert enabled.value.to_state == "enabled"
    assert fixture.packs.grant_ids() == ()
    loaded = fixture.packs.loader.get("research-corpus")
    assert loaded is not None
    assert loaded.manifest.is_headless is True
    assert loaded.manifest.copilot_profile is None
    assert loaded.manifest.views == ()

    cli = fixture.invoke_authoring(transport=PublicCallTransport.CLI)
    assert is_ok(cli)
    assert cli.value.handle.state is JobHandleState.RUNNING
    assert cli.value.in_app_panels == ()
    assert cli.value.referenced is True
    wire = fixture.invoke_authoring(transport="wire")
    assert is_ok(wire)
    assert wire.value.transport is PublicCallTransport.WIRE
    assert is_refusal(fixture.open_in_app_panel("panel:app"))

    blocked = JKit01Fixture(root=root / "branch-a")
    required = blocked.enable_headless_pack(require_copilot=True)
    assert is_refusal(required)
    assert required.context["branch"] == "A"
    assert blocked.packs.grant_ids() == ()


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        main(Path(tmp))
