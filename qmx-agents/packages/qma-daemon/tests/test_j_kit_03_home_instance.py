"""Story 65.3 — J-KIT-03 home authoring exactly-one instance_id."""

from __future__ import annotations

import ast
import runpy
from pathlib import Path
from typing import cast

from qma.core.refusals import AmbiguousResolution, NestedGrantUnionRefused
from qma.daemon.kit_journey import (
    APP_USE_APP_INSTANCE_REQUIRED,
    AUTHORING_APP_INSTANCE_OPTIONAL,
    ENVELOPE_INSTANCE_ID_OPTIONAL,
    ENVELOPE_INSTANCE_ID_REMAINS_REQUIRED,
    GAP_0081_CHROME_FILLED,
    HOME_IS_AUTHORING_WITHOUT_INSTANCE,
    INSTANCE_ID_KIND,
    J_KIT_03,
    KIT_JOURNEY_03_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_03_INSPECT_SHA,
    KIT_JOURNEY_03_OWNER,
    SILENT_LATEST_INSTANCE,
    THIRD_PRODUCT_SESSION_PROFILE_MINTED,
    JKit03Fixture,
    claim_j_kit_03_e2e_at_inspect_sha,
    refuse_nested_grant_union,
    refuse_optional_envelope_instance_id,
    refuse_silent_latest_instance,
    refuse_third_product_session_profile,
)
from qma.daemon.sessions import ProductSessionProfile
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import Result

_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "kit_journey.py"
_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "j_kit_03_home_instance_usage.py"


def _ok[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_inspect_sha_honesty_fixtures_are_not_e2e() -> None:
    assert J_KIT_03 == "J-KIT-03"
    assert KIT_JOURNEY_03_INSPECT_SHA == "34c148b"
    assert KIT_JOURNEY_03_E2E_AT_INSPECT_SHA is False
    assert AUTHORING_APP_INSTANCE_OPTIONAL is True
    assert APP_USE_APP_INSTANCE_REQUIRED is True
    assert HOME_IS_AUTHORING_WITHOUT_INSTANCE is True
    assert THIRD_PRODUCT_SESSION_PROFILE_MINTED is False
    assert SILENT_LATEST_INSTANCE is False
    assert ENVELOPE_INSTANCE_ID_OPTIONAL is False
    assert ENVELOPE_INSTANCE_ID_REMAINS_REQUIRED is True
    assert INSTANCE_ID_KIND == "instance_id"
    assert GAP_0081_CHROME_FILLED is False
    claimed = claim_j_kit_03_e2e_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert claimed.context["e2e_at_inspect_sha"] is False
    assert claimed.context["class_test_existence_is_e2e"] is False
    assert claimed.context["inspect_sha"] == "34c148b"
    assert claimed.context["branch"] == "D"
    assert _ok(claim_j_kit_03_e2e_at_inspect_sha(False)) is False
    assert is_refusal(claim_j_kit_03_e2e_at_inspect_sha("wired"))


def test_home_authoring_chat_without_invoke_is_legal() -> None:
    fixture = JKit03Fixture()
    assert fixture.owner == KIT_JOURNEY_03_OWNER == "COMP-QMA-DAEMON"
    assert fixture.journey == J_KIT_03
    assert fixture.e2e_at_inspect_sha is False
    home = _ok(fixture.chat_without_invoke())
    assert home.profile is ProductSessionProfile.AUTHORING
    assert home.app_instance_id is None
    assert home.context.instance_id is None
    assert home.selected_refs == ()
    payload = dict(home.to_payload())
    assert "app_instance_id" not in payload
    profiles = {item.value for item in ProductSessionProfile}
    assert profiles == {"authoring", "app-use"}
    assert fixture.third_profile_minted is False
    third = fixture.mint_third_profile("home")
    assert is_refusal(third)
    assert third.context["branch"] == "A"
    assert is_refusal(refuse_third_product_session_profile())


def test_exactly_one_instance_id_binds_envelope_and_grants() -> None:
    fixture = JKit03Fixture()
    _ok(fixture.open_home_authoring())
    report = _ok(fixture.invoke_authoring())
    assert report.selected_instance_id == "inst:B"
    assert report.envelope_instance_id == "inst:B"
    assert report.grant_instance_id == "inst:B"
    assert report.grant_id == "grant:j-kit-03-b"
    assert report.app_instance_id is None
    assert report.profile == "authoring"
    body = dict(report.to_payload())
    assert body["journey"] == J_KIT_03
    assert body["envelope_instance_id"] == "inst:B"
    assert body["grant_instance_id"] == "inst:B"
    home = _ok(fixture.host.sessions.get("psess:home"))
    assert home.app_instance_id is None
    mismatch = fixture.invoke_authoring(
        envelope_instance_id="inst:A",
        logical_invocation_id="inv:j-kit-03-mismatch",
    )
    assert is_refusal(mismatch)
    assert mismatch.context["field"] == "instance_id"


def test_zero_or_two_instance_id_refs_are_invalid_input() -> None:
    fixture = JKit03Fixture()
    zero = fixture.invoke_with_refs(())
    assert is_refusal(zero)
    assert isinstance(zero, AmbiguousResolution)
    assert zero.context["code"] == "INVALID_INPUT"
    assert zero.context["count"] == 0
    assert zero.context["resolved_to_latest"] is False
    assert zero.context["resolved_to_first"] is False
    assert zero.context["resolved_to_all"] is False
    assert zero.context["never_latest"] is True

    two = fixture.invoke_with_refs(
        [
            {"kind": "instance_id", "id": "inst:B"},
            {"kind": "instance_id", "id": "inst:A"},
        ]
    )
    assert is_refusal(two)
    assert isinstance(two, AmbiguousResolution)
    assert two.context["code"] == "INVALID_INPUT"
    assert two.context["count"] == 2
    assert two.context["resolved_to_first"] is False
    assert two.context["resolved_to_all"] is False

    latest = fixture.invoke_silent_latest()
    assert is_refusal(latest)
    assert latest.context["branch"] == "B"
    assert latest.context["resolved_to_latest"] is False
    assert latest.context["code"] == "INVALID_INPUT"
    assert is_refusal(refuse_silent_latest_instance())

    omitted = fixture.invoke_without_envelope_instance_id()
    assert is_refusal(omitted)
    assert omitted.context["branch"] == "C"
    assert omitted.context["envelope_instance_id_optional"] is False
    assert is_refusal(refuse_optional_envelope_instance_id())
    none_envelope = fixture.invoke_authoring(
        envelope_instance_id=None,
        logical_invocation_id="inv:j-kit-03-none",
    )
    assert is_refusal(none_envelope)
    assert none_envelope.context["branch"] == "C"


def test_app_use_still_requires_app_instance_id() -> None:
    fixture = JKit03Fixture()
    missing = fixture.omit_app_use_instance()
    assert is_refusal(missing)
    assert missing.context["field"] == "app_instance_id"
    bound = _ok(
        fixture.host.open_app_use(
            product_session_id="psess:app-b-ok",
            instance_id="inst:B",
        )
    )
    assert bound.profile is ProductSessionProfile.APP_USE
    assert bound.app_instance_id == "inst:B"


def test_nested_call_does_not_union_grants_or_widen_tools() -> None:
    fixture = JKit03Fixture()
    _ok(fixture.invoke_authoring())
    nested = _ok(fixture.nested_call())
    assert nested.grant_id == "grant:j-kit-03-app"
    assert nested.grant_ids == ("grant:j-kit-03-app",)
    assert "grant:j-kit-03-b" not in nested.grant_ids
    assert "grant:j-kit-03-extra" not in nested.grant_ids
    assert nested.union is False
    assert nested.widens_tools is False
    assert nested.tools == ("analysis-backtest:qmb",)
    assert "research-corpus:inspect" in nested.caller_tools
    assert "research-corpus:inspect" not in nested.tools
    body = dict(nested.to_payload())
    assert body["journey"] == J_KIT_03
    assert body["union"] is False

    unioned = fixture.nested_call(union_grants=True)
    assert is_refusal(unioned)
    assert isinstance(unioned, NestedGrantUnionRefused)
    assert unioned.context["union"] is False
    widened = fixture.nested_call(union_tools=True)
    assert is_refusal(widened)
    leaked = fixture.nested_call_leaking_home_grant()
    assert is_refusal(leaked)
    assert isinstance(leaked, NestedGrantUnionRefused)
    assert is_refusal(refuse_nested_grant_union())


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
