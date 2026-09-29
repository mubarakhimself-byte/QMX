"""Story 68.3 — HTTP Bearer pairing:<proof> plus WS subprotocols."""

from __future__ import annotations

from qma.wire import (
    ALLOWED_PROOF_HOMES,
    COOKIE_LOGIN_SHIPPED,
    CT40_WS_SUBPROTOCOL,
    FETCH_CREDENTIALS,
    FORBIDDEN_PROOF_HOMES,
    HANDLE_CLIENT_DISCARDED_BYTES_AT_INSPECT_SHA,
    LOCALSTORAGE_PROOF_SHIPPED,
    PAIRING_BEARER_TRANSPORT_EXISTED_AT_INSPECT_SHA,
    PAIRING_HTTP_AUTHORIZATION_PREFIX,
    PAIRING_RECORD_ID_PREFIX,
    PAIRING_WS_SUBPROTOCOL_PREFIX,
    PAIRING_WS_SUBPROTOCOLS_EXISTED_AT_INSPECT_SHA,
    WEBSOCKETS_IMPORTS_AT_INSPECT_SHA,
    AuthenticatedHttpFetch,
    authenticated_http_fetch,
    claim_cookie_login_or_localstorage_proof_shipped,
    claim_pairing_transports_existed_at_inspect_sha,
    extract_pairing_ws_proof,
    format_pairing_websocket_subprotocols,
    parse_offered_websocket_subprotocols,
    refuse_forbidden_proof_home,
    selected_websocket_subprotocol,
)
from qmf.core.refusal import RefusalCategory, is_ok, is_refusal

_PROOF = "abcDEF012-_~"
_ORIGIN = "http://127.0.0.1:5173"


def test_inspect_sha_transports_were_absent() -> None:
    assert PAIRING_BEARER_TRANSPORT_EXISTED_AT_INSPECT_SHA is False
    assert PAIRING_WS_SUBPROTOCOLS_EXISTED_AT_INSPECT_SHA is False
    assert WEBSOCKETS_IMPORTS_AT_INSPECT_SHA == 0
    assert HANDLE_CLIENT_DISCARDED_BYTES_AT_INSPECT_SHA is True
    claimed = claim_pairing_transports_existed_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert claimed.category is RefusalCategory.POLICY_REJECTION
    assert claimed.context["existed_at_inspect_sha"] is False
    assert claimed.context["inspect_sha"] == "34c148be"
    assert claimed.context["websockets_imports"] == 0
    assert claimed.context["handle_client_discarded_bytes"] is True
    assert is_ok(claim_pairing_transports_existed_at_inspect_sha(False))
    assert is_refusal(claim_pairing_transports_existed_at_inspect_sha("maybe"))


def test_cookie_login_and_localstorage_proof_not_shipped() -> None:
    assert COOKIE_LOGIN_SHIPPED is False
    assert LOCALSTORAGE_PROOF_SHIPPED is False
    assert frozenset({"cookie", "localStorage", "IndexedDB"}) == FORBIDDEN_PROOF_HOMES
    assert frozenset({"memory", "sessionStorage"}) == ALLOWED_PROOF_HOMES
    claimed = claim_cookie_login_or_localstorage_proof_shipped(True)
    assert is_refusal(claimed)
    assert claimed.context["cookie_login_shipped"] is False
    assert claimed.context["localstorage_proof_shipped"] is False
    assert is_ok(claim_cookie_login_or_localstorage_proof_shipped(False))
    assert is_ok(refuse_forbidden_proof_home("memory"))
    assert is_ok(refuse_forbidden_proof_home("sessionStorage"))
    for home in ("cookie", "localStorage", "IndexedDB", "Cookie"):
        refused = refuse_forbidden_proof_home(home)
        assert is_refusal(refused), home
        assert refused.category is RefusalCategory.POLICY_REJECTION


def test_authenticated_http_fetch_is_bearer_plus_origin_credentials_omit() -> None:
    built = authenticated_http_fetch(origin=_ORIGIN, proof=_PROOF)
    assert is_ok(built)
    fetch = built.value
    assert isinstance(fetch, AuthenticatedHttpFetch)
    assert fetch.credentials == FETCH_CREDENTIALS == "omit"
    assert fetch.query is None
    assert fetch.headers["Origin"] == _ORIGIN
    assert fetch.headers["Authorization"] == f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{_PROOF}"
    assert "pairing:<id>" not in fetch.headers["Authorization"]

    record_id = f"{PAIRING_RECORD_ID_PREFIX}{'ab' * 16}"
    as_id = authenticated_http_fetch(origin=_ORIGIN, proof=record_id)
    assert is_refusal(as_id)
    assert "never pairing:<id>" in str(as_id.context["reason"])

    cred = authenticated_http_fetch(origin=_ORIGIN, proof="cred://models/openai")
    assert is_refusal(cred)
    assert "cred://" in str(cred.context["reason"])

    in_query = authenticated_http_fetch(
        origin=_ORIGIN,
        proof=_PROOF,
        query={"pairing_proof": _PROOF},
    )
    assert is_refusal(in_query)

    missing_origin = authenticated_http_fetch(origin="", proof=_PROOF)
    assert is_refusal(missing_origin)


def test_websocket_constructor_offers_ct40_and_pair_proof() -> None:
    offered = format_pairing_websocket_subprotocols(_PROOF)
    assert is_ok(offered)
    assert offered.value == (CT40_WS_SUBPROTOCOL, f"{PAIRING_WS_SUBPROTOCOL_PREFIX}{_PROOF}")
    assert selected_websocket_subprotocol() == CT40_WS_SUBPROTOCOL

    parsed = parse_offered_websocket_subprotocols(list(offered.value))
    assert is_ok(parsed)
    extracted = extract_pairing_ws_proof(parsed.value)
    assert is_ok(extracted)
    assert extracted.value == _PROOF

    header = parse_offered_websocket_subprotocols(
        f"{CT40_WS_SUBPROTOCOL}, {PAIRING_WS_SUBPROTOCOL_PREFIX}{_PROOF}"
    )
    assert is_ok(header)
    assert is_ok(extract_pairing_ws_proof(header.value))


def test_websocket_refuses_missing_malformed_and_pairing_id() -> None:
    missing = extract_pairing_ws_proof([])
    assert is_refusal(missing)
    only_ct40 = extract_pairing_ws_proof([CT40_WS_SUBPROTOCOL])
    assert is_refusal(only_ct40)
    only_pair = extract_pairing_ws_proof([f"{PAIRING_WS_SUBPROTOCOL_PREFIX}{_PROOF}"])
    assert is_refusal(only_pair)

    record_id = f"{PAIRING_RECORD_ID_PREFIX}{'cd' * 16}"
    as_pair_id = extract_pairing_ws_proof(
        [CT40_WS_SUBPROTOCOL, f"{PAIRING_WS_SUBPROTOCOL_PREFIX}{record_id}"]
    )
    assert is_refusal(as_pair_id)
    assert "pairing:<id>" in str(as_pair_id.context["reason"])

    literal = extract_pairing_ws_proof([CT40_WS_SUBPROTOCOL, f"pairing:{record_id}"])
    assert is_refusal(literal)

    formatted_id = format_pairing_websocket_subprotocols(record_id)
    assert is_refusal(formatted_id)

    malformed = extract_pairing_ws_proof([CT40_WS_SUBPROTOCOL, "qmx.pair."])
    assert is_refusal(malformed)
    spaced = extract_pairing_ws_proof([CT40_WS_SUBPROTOCOL, "qmx.pair.abc def"])
    assert is_refusal(spaced)


def test_authenticated_http_fetch_never_sets_cookie() -> None:
    built = authenticated_http_fetch(origin=_ORIGIN, proof=_PROOF)
    assert is_ok(built)
    headers = {key.casefold(): value for key, value in built.value.headers.items()}
    assert "cookie" not in headers
    assert "set-cookie" not in headers
    assert built.value.credentials == "omit"


def test_whatwg_websocket_constructor_list_is_ct40_then_pair_proof() -> None:
    pairing_proof = _PROOF
    offered = format_pairing_websocket_subprotocols(pairing_proof)
    assert is_ok(offered)
    assert offered.value == ("qmx.ct40.v1", "qmx.pair." + pairing_proof)
    cred = format_pairing_websocket_subprotocols("cred://models/openai")
    assert is_refusal(cred)
