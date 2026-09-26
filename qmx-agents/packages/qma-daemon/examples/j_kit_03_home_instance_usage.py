"""Reference usage — J-KIT-03 home authoring exactly-one instance_id."""

from __future__ import annotations

from qma.daemon.kit_journey import (
    ENVELOPE_INSTANCE_ID_OPTIONAL,
    GAP_0081_CHROME_FILLED,
    J_KIT_03,
    KIT_JOURNEY_03_E2E_AT_INSPECT_SHA,
    SILENT_LATEST_INSTANCE,
    THIRD_PRODUCT_SESSION_PROFILE_MINTED,
    JKit03Fixture,
    claim_j_kit_03_e2e_at_inspect_sha,
    refuse_nested_grant_union,
    refuse_optional_envelope_instance_id,
    refuse_silent_latest_instance,
    refuse_third_product_session_profile,
)
from qmf.core import is_ok, is_refusal


def main() -> None:
    assert J_KIT_03 == "J-KIT-03"
    assert KIT_JOURNEY_03_E2E_AT_INSPECT_SHA is False
    assert THIRD_PRODUCT_SESSION_PROFILE_MINTED is False
    assert SILENT_LATEST_INSTANCE is False
    assert ENVELOPE_INSTANCE_ID_OPTIONAL is False
    assert GAP_0081_CHROME_FILLED is False
    assert is_refusal(claim_j_kit_03_e2e_at_inspect_sha(True))
    assert is_ok(claim_j_kit_03_e2e_at_inspect_sha(False))
    assert is_refusal(refuse_third_product_session_profile())
    assert is_refusal(refuse_silent_latest_instance())
    assert is_refusal(refuse_optional_envelope_instance_id())
    assert is_refusal(refuse_nested_grant_union())

    fixture = JKit03Fixture()
    home = fixture.chat_without_invoke()
    assert is_ok(home)
    assert home.value.app_instance_id is None
    assert home.value.profile.value == "authoring"
    assert is_refusal(fixture.mint_third_profile())
    assert is_refusal(fixture.omit_app_use_instance())

    invoked = fixture.invoke_authoring()
    assert is_ok(invoked)
    assert invoked.value.envelope_instance_id == "inst:B"
    assert invoked.value.grant_instance_id == "inst:B"
    assert invoked.value.app_instance_id is None
    assert is_refusal(fixture.invoke_with_refs(()))
    assert is_refusal(
        fixture.invoke_with_refs(
            [
                {"kind": "instance_id", "id": "inst:B"},
                {"kind": "instance_id", "id": "inst:A"},
            ]
        )
    )
    assert is_refusal(fixture.invoke_silent_latest())
    assert is_refusal(fixture.invoke_without_envelope_instance_id())

    nested = fixture.nested_call()
    assert is_ok(nested)
    assert nested.value.grant_ids == ("grant:j-kit-03-app",)
    assert "grant:j-kit-03-b" not in nested.value.grant_ids
    assert nested.value.union is False
    assert "research-corpus:inspect" not in nested.value.tools
    assert is_refusal(fixture.nested_call(union_grants=True))
    assert is_refusal(fixture.nested_call_leaking_home_grant())


if __name__ == "__main__":
    main()
