"""Story 68.1 — pairing bearer identity and AM-11 value-class secret scan."""

from __future__ import annotations

from qma.wire import (
    FORBIDDEN_SECRET_SURFACE_KEYS,
    PAIRING_BEARER_SCHEME,
    PAIRING_HTTP_AUTHORIZATION_PREFIX,
    PAIRING_RECORD_ID_PREFIX,
    PAIRING_SESSION_ID_FIELD,
    PAIRING_WS_SUBPROTOCOL_PREFIX,
    assert_no_secret_on_wire_surface,
    authenticate_before_protocol,
    authenticate_pairing_record,
    format_pairing_authorization,
    is_pairing_record_id,
    is_rfc6455_token,
    looks_like_bearer_proof,
    parse_pairing_bearer_authorization,
    refuse_pairing_proof_in_query,
)
from qmf.core.refusal import RefusalCategory, is_ok, is_refusal


def test_forbidden_keys_include_pairing_bearer_names() -> None:
    assert "pairing_proof" in FORBIDDEN_SECRET_SURFACE_KEYS
    assert "authorization" in FORBIDDEN_SECRET_SURFACE_KEYS
    assert "token" in FORBIDDEN_SECRET_SURFACE_KEYS
    assert PAIRING_BEARER_SCHEME == "pairing"
    assert PAIRING_HTTP_AUTHORIZATION_PREFIX == "Bearer pairing:"
    assert PAIRING_WS_SUBPROTOCOL_PREFIX == "qmx.pair."
    assert PAIRING_SESSION_ID_FIELD == "pairing_session_id"


def test_parse_bearer_pairing_proof_never_id() -> None:
    proof = "abcDEF012-_~"
    assert is_rfc6455_token(proof)
    header = format_pairing_authorization(proof)
    assert is_ok(header)
    parsed = parse_pairing_bearer_authorization(header.value)
    assert is_ok(parsed)
    assert parsed.value == proof

    record_id = f"{PAIRING_RECORD_ID_PREFIX}{'ab' * 16}"
    assert is_pairing_record_id(record_id)
    refused = parse_pairing_bearer_authorization(f"Bearer pairing:{record_id}")
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert "never pairing:<id>" in str(refused.context["reason"])

    as_id = format_pairing_authorization(record_id)
    assert is_refusal(as_id)


def test_query_string_never_carries_proof() -> None:
    assert is_ok(refuse_pairing_proof_in_query(None))
    assert is_ok(refuse_pairing_proof_in_query({}))
    refused = refuse_pairing_proof_in_query({"pairing_proof": "abc"})
    assert is_refusal(refused)
    refused_q = refuse_pairing_proof_in_query("?pairing_proof=abc")
    assert is_refusal(refused_q)
    refused_auth = refuse_pairing_proof_in_query({"q": "Bearer pairing:abcDEF"})
    assert is_refusal(refused_auth)


def test_value_class_scan_refuses_bearer_proofs_not_only_token_keys() -> None:
    proof = "abcDEF012-_~"
    leaked = {"note": f"Bearer pairing:{proof}", "ok": True}
    refused = assert_no_secret_on_wire_surface(leaked)
    assert is_refusal(refused)
    assert refused.context["field"] == "secret_on_wire"

    subprotocol = {"protocol": f"{PAIRING_WS_SUBPROTOCOL_PREFIX}{proof}"}
    assert is_refusal(assert_no_secret_on_wire_surface(subprotocol))

    named = {"pairing_proof": proof, "pairing_record_id": f"{PAIRING_RECORD_ID_PREFIX}aa"}
    assert is_refusal(assert_no_secret_on_wire_surface(named))

    known = assert_no_secret_on_wire_surface({"payload": {"x": proof}}, known_proofs={proof})
    assert is_refusal(known)

    record_id = f"{PAIRING_RECORD_ID_PREFIX}{'cd' * 16}"
    allowed = {"pairing_record_id": record_id, "status": "bound"}
    assert is_ok(assert_no_secret_on_wire_surface(allowed))

    minted_session_id = {"pairing_session_id": "nope"}
    refused_sid = assert_no_secret_on_wire_surface(minted_session_id)
    assert is_refusal(refused_sid)


def test_once_returned_confirm_body_may_carry_pairing_proof() -> None:
    proof = "abcDEF012-_~"
    record_id = f"{PAIRING_RECORD_ID_PREFIX}{'ee' * 16}"
    body = {
        "pairing_record_id": record_id,
        "pairing_proof": proof,
        "expires_at": 1,
    }
    assert is_ok(assert_no_secret_on_wire_surface(body, allow_once_returned_pairing_proof=True))
    assert is_refusal(assert_no_secret_on_wire_surface(body))


def test_pairing_session_has_record_id_never_credential_ref() -> None:
    record_id = f"{PAIRING_RECORD_ID_PREFIX}{'ff' * 16}"
    session = authenticate_pairing_record(record_id)
    assert is_ok(session)
    assert session.value.credential_ref is None
    assert session.value.pairing_record_id == record_id
    assert session.value.principal_class.value == "operator"
    diagnostic = session.value.to_diagnostic()
    assert diagnostic["pairing_record_id"] == record_id
    assert "credential_ref" not in diagnostic
    assert "pairing_proof" not in diagnostic
    assert is_ok(assert_no_secret_on_wire_surface(diagnostic))

    machine = authenticate_pairing_record(record_id, principal_class="machine")
    assert is_refusal(machine)

    broker = authenticate_before_protocol("cred://models/openai", principal_class="machine")
    assert is_ok(broker)
    assert broker.value.pairing_record_id is None
    assert str(broker.value.credential_ref) == "cred://models/openai"


def test_looks_like_bearer_proof_value_class() -> None:
    assert looks_like_bearer_proof("Bearer pairing:abc") is True
    assert looks_like_bearer_proof("qmx.pair.abc") is True
    assert looks_like_bearer_proof("pairing:abc") is True
    assert looks_like_bearer_proof(f"{PAIRING_RECORD_ID_PREFIX}ab") is False
    assert looks_like_bearer_proof("not-a-proof", known_proofs={"secret-proof"}) is False
    assert looks_like_bearer_proof("secret-proof", known_proofs={"secret-proof"}) is True
