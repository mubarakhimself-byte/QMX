"""Story 68.2 — unauthenticated HTTP is start, confirm, and OPTIONS only."""

from __future__ import annotations

from pathlib import Path

import pytest
from qma.core.barriers.credential_allowlist import (
    ALLOWED_CREDENTIAL_REF_PREFIXES,
    CredentialAllowlistError,
    assert_allowlist_not_widenable,
)
from qma.daemon.host_control.channel import CT40_BIND_PORT, HOST_CONTROL_IS_CT40
from qma.daemon.http_pair import (
    ACCEPT_HEADER_OR_COOKIE,
    AM_01_NAME,
    BROKER_ALLOWLIST_WIDENED,
    COOKIE_IS_OPERATOR_PROOF,
    CORS_EXISTED_AT_INSPECT_SHA,
    DEC_0304_SUPERSEDED_BY,
    DEC_0323_SUPERSEDED_BY,
    HOST_CONTROL_IS_AM01_HTTP,
    LISTENER_POSTURE_TYPES_EXISTED_AT_INSPECT_SHA,
    OPTIONS_IS_CT40_INITIALIZE,
    OPTIONS_IS_UNAUTHENTICATED_WS_BIND,
    OPTIONS_NEVER_ISSUES_PAIRING_PROOF,
    OPTIONS_NEVER_RETURNS_ARTIFACT_BYTES,
    OPTIONS_NEVER_UPGRADES_WEBSOCKET,
    PAIRING_HTTP_EXISTED_AT_INSPECT_SHA,
    PAIRING_HTTP_OPENS_AUTHENTICATED_WIRE,
    SET_COOKIE_ON_PAIR_HTTP_IS_SPEC_MISS,
    UNAUTHENTICATED_BIND_SENTENCE_HELD,
    Am01UnauthenticatedHttp,
    PairHttpRequest,
    admit_unauthenticated_http,
    assert_no_set_cookie,
    authenticate_machine_or_worker,
    claim_cors_existed_at_inspect_sha,
    claim_listener_posture_types_absent_at_inspect_sha,
    claim_pair_http_existed_at_inspect_sha,
    claim_unauthenticated_bind_sentence_dropped,
    cors_options_response,
    is_host_control_http,
    operator_proof_from_headers,
    require_pair_renew_bearer,
)
from qma.daemon.pairing import PAIRING_HTTP_EXISTED_AT_INSPECT_SHA as PAIRING_CLAIM
from qma.wire.auth import PAIRING_HTTP_AUTHORIZATION_PREFIX
from qma.wire.initialize import InitializeParams, WireConnection
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import RefusalCategory

_ORIGIN = "http://127.0.0.1:5173"
_PROOF = "abcDEF012-_~"
_PROCESS_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "process.py"


def _request(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    query: str | None = None,
    body: bytes = b"",
    port: int = CT40_BIND_PORT,
) -> PairHttpRequest:
    built = PairHttpRequest.try_create(
        method=method,
        path=path,
        headers=headers,
        query=query,
        body=body,
        port=port,
    )
    assert is_ok(built), built
    return built.value


def test_honesty_and_held_sentence() -> None:
    assert PAIRING_HTTP_EXISTED_AT_INSPECT_SHA is False
    assert PAIRING_CLAIM is False
    assert CORS_EXISTED_AT_INSPECT_SHA is False
    assert LISTENER_POSTURE_TYPES_EXISTED_AT_INSPECT_SHA is True
    assert UNAUTHENTICATED_BIND_SENTENCE_HELD is True
    assert DEC_0304_SUPERSEDED_BY is None
    assert DEC_0323_SUPERSEDED_BY is None
    assert AM_01_NAME == "AM-01"
    assert is_refusal(claim_pair_http_existed_at_inspect_sha(True))
    assert is_ok(claim_pair_http_existed_at_inspect_sha(False))
    assert is_refusal(claim_cors_existed_at_inspect_sha(True))
    assert is_ok(claim_cors_existed_at_inspect_sha(False))
    assert is_refusal(claim_listener_posture_types_absent_at_inspect_sha(True))
    assert is_ok(claim_listener_posture_types_absent_at_inspect_sha(False))
    assert is_refusal(claim_unauthenticated_bind_sentence_dropped(True))
    assert is_ok(claim_unauthenticated_bind_sentence_dropped(False))


def test_three_path_carve_out_admits_start_confirm_and_options() -> None:
    start = admit_unauthenticated_http(_request("POST", "/pair/start", headers={"Origin": _ORIGIN}))
    assert is_ok(start)
    assert start.value.carve_out is Am01UnauthenticatedHttp.POST_PAIR_START
    assert start.value.issues_pairing_proof is False
    assert start.value.opens_authenticated_wire is False
    assert start.value.is_ct40_initialize is False

    confirm = admit_unauthenticated_http(
        _request("POST", "/pair/confirm", headers={"Origin": _ORIGIN})
    )
    assert is_ok(confirm)
    assert confirm.value.carve_out is Am01UnauthenticatedHttp.POST_PAIR_CONFIRM
    assert confirm.value.issues_pairing_proof is False

    for path in (
        "/pair/start",
        "/pair/confirm",
        "/pair/renew",
        "/artifacts/stage",
        "/q/list_mailbox",
        "/q/get_pack_ui_request",
        "/q/get_editor_draft_head",
        "/artifacts/fp1:sha256:abcd",
    ):
        options = admit_unauthenticated_http(_request("OPTIONS", path, headers={"Origin": _ORIGIN}))
        assert is_ok(options), path
        assert options.value.carve_out is Am01UnauthenticatedHttp.CORS_OPTIONS
        assert options.value.issues_pairing_proof is False
        assert options.value.upgrades_websocket is False
        assert options.value.returns_artifact_bytes is False
        assert options.value.opens_authenticated_wire is False
        assert options.value.is_ct40_initialize is False


def test_options_never_issues_upgrades_or_returns_bytes() -> None:
    assert OPTIONS_NEVER_ISSUES_PAIRING_PROOF is True
    assert OPTIONS_NEVER_UPGRADES_WEBSOCKET is True
    assert OPTIONS_NEVER_RETURNS_ARTIFACT_BYTES is True
    assert OPTIONS_IS_CT40_INITIALIZE is False
    assert OPTIONS_IS_UNAUTHENTICATED_WS_BIND is False
    assert SET_COOKIE_ON_PAIR_HTTP_IS_SPEC_MISS is True

    response = cors_options_response(
        _request(
            "OPTIONS",
            "/pair/start",
            headers={
                "Origin": _ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Upgrade": "websocket",
                "Connection": "Upgrade",
            },
        )
    )
    assert is_ok(response)
    assert response.value.status == 204
    assert response.value.body == b""
    assert "pairing_proof" not in response.value.body.decode("ascii")
    headers = {key.casefold(): value for key, value in response.value.headers.items()}
    assert "set-cookie" not in headers
    assert "upgrade" not in headers
    assert headers["access-control-allow-origin"] == _ORIGIN
    assert headers["access-control-allow-origin"] != "*"
    assert "authorization" in headers["access-control-allow-headers"].casefold()
    assert is_ok(assert_no_set_cookie(response.value.headers))

    unnamed = cors_options_response(_request("OPTIONS", "/initialize"))
    assert is_refusal(unnamed)


def test_renew_without_bearer_is_refused_as_unauthenticated() -> None:
    refused = admit_unauthenticated_http(
        _request("POST", "/pair/renew", headers={"Origin": _ORIGIN})
    )
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "authorization"
    assert "unauthenticated" in str(refused.context["reason"])
    assert "AM-01" in str(refused.context["named_amendment"])

    cookie_only = admit_unauthenticated_http(
        _request(
            "POST",
            "/pair/renew",
            headers={"Origin": _ORIGIN, "Cookie": "pairing_proof=abc"},
        )
    )
    assert is_refusal(cookie_only)
    assert cookie_only.context["field"] == "cookie"

    header = f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{_PROOF}"
    with_bearer = admit_unauthenticated_http(
        _request(
            "POST",
            "/pair/renew",
            headers={"Origin": _ORIGIN, "Authorization": header},
        )
    )
    assert is_refusal(with_bearer)
    assert with_bearer.context["renew_is_am01_unauthenticated"] is False
    assert with_bearer.context["opens_authenticated_wire"] is False

    parsed = require_pair_renew_bearer(
        _request(
            "POST",
            "/pair/renew",
            headers={"Origin": _ORIGIN, "Authorization": header},
        )
    )
    assert is_ok(parsed)
    assert parsed.value == _PROOF
    missing = require_pair_renew_bearer(
        _request("POST", "/pair/renew", headers={"Origin": _ORIGIN})
    )
    assert is_refusal(missing)


def test_other_http_and_websocket_still_authenticate() -> None:
    for method, path in (
        ("PUT", "/artifacts/stage"),
        ("GET", "/q/list_mailbox"),
        ("GET", "/artifacts/fp1:sha256:abcd"),
        ("GET", "/pair/start"),
        ("POST", "/initialize"),
    ):
        refused = admit_unauthenticated_http(_request(method, path))
        assert is_refusal(refused), f"{method} {path}"
        assert refused.context["field"] == "authentication"

    ws = admit_unauthenticated_http(
        _request(
            "GET",
            "/",
            headers={"Connection": "Upgrade", "Upgrade": "websocket"},
        )
    )
    assert is_refusal(ws)
    assert ws.context["field"] == "upgrade"


def test_cookie_is_not_operator_proof_and_set_cookie_is_spec_miss() -> None:
    assert COOKIE_IS_OPERATOR_PROOF is False
    assert ACCEPT_HEADER_OR_COOKIE is False
    cookie = operator_proof_from_headers({"Cookie": f"pairing={_PROOF}"})
    assert is_refusal(cookie)
    assert cookie.context["cookie_is_proof"] is False
    assert cookie.context["accept_header_or_cookie"] is False

    header = f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{_PROOF}"
    both = operator_proof_from_headers({"Authorization": header, "Cookie": f"pairing={_PROOF}"})
    assert is_ok(both)
    assert both.value == _PROOF

    refused_cookie = assert_no_set_cookie({"Set-Cookie": "pairing=x"})
    assert is_refusal(refused_cookie)
    with pytest.raises(ValueError, match="Set-Cookie"):
        from qma.daemon.http_pair import PairHttpResponse

        PairHttpResponse(status=200, headers={"Set-Cookie": "x"}, body=b"")


def test_pairing_http_does_not_open_authenticated_wire() -> None:
    assert PAIRING_HTTP_OPENS_AUTHENTICATED_WIRE is False
    admitted = admit_unauthenticated_http(_request("POST", "/pair/start"))
    assert is_ok(admitted)
    assert admitted.value.opens_authenticated_wire is False

    conn = WireConnection()
    params = InitializeParams.try_create(protocol_version="1.0.0")
    assert is_ok(params)
    assert is_refusal(conn.complete_initialize(params.value, assign_producer_id="p"))
    assert conn.authenticated is False
    assert conn.initialized is False


def test_machine_worker_still_need_credential_ref_allowlist_unwidened() -> None:
    assert BROKER_ALLOWLIST_WIDENED is False
    assert_allowlist_not_widenable()
    with pytest.raises(CredentialAllowlistError):
        assert_allowlist_not_widenable(ALLOWED_CREDENTIAL_REF_PREFIXES | {"cred://operator/"})
    with pytest.raises(CredentialAllowlistError):
        assert_allowlist_not_widenable(ALLOWED_CREDENTIAL_REF_PREFIXES | {"cred://pairing/"})

    machine = authenticate_machine_or_worker("cred://models/openai")
    assert is_ok(machine)
    assert str(machine.value.credential_ref) == "cred://models/openai"
    assert machine.value.principal_class.value == "machine"

    page = authenticate_machine_or_worker("cred://operator/ui")
    assert is_refusal(page)
    venue = authenticate_machine_or_worker("cred://venue/ctrader")
    assert is_refusal(venue)


def test_host_control_is_not_am01_http_and_stays_off_8765() -> None:
    assert HOST_CONTROL_IS_AM01_HTTP is False
    assert HOST_CONTROL_IS_CT40 is False
    assert is_host_control_http("/host/status", port=CT40_BIND_PORT) is True
    refused = admit_unauthenticated_http(_request("POST", "/host/pair"))
    assert is_refusal(refused)
    assert refused.context["field"] == "host_control"
    source = _PROCESS_SRC.read_text(encoding="utf-8")
    assert "http.server" not in source
