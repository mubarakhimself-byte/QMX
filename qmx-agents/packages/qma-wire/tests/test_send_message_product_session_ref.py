"""Story 69.1 — send_message payload may name product_session_ref."""

from __future__ import annotations

from qma.core.ports.mailbox import (
    MAILBOX_INSPECT_SHA,
    PRODUCT_SESSION_REF_EXISTED_AT_INSPECT_SHA,
    claim_envelope_types_absent_at_inspect_sha,
    claim_product_session_ref_existed_at_inspect_sha,
)
from qma.wire import (
    SEND_MESSAGE_COMMAND,
    parse_send_message_payload,
    validate_family_payload,
)
from qmf.core.refusal import is_ok, is_refusal


def test_send_message_payload_may_name_product_session_ref() -> None:
    assert SEND_MESSAGE_COMMAND == "send_message"
    named = parse_send_message_payload(
        {
            "product_session_ref": "psess:H",
            "body": {"text": "hello"},
            "kind": "handoff",
        }
    )
    assert is_ok(named)
    assert named.value["product_session_ref"] == "psess:H"
    omitted = parse_send_message_payload({"body": {"text": "hello"}, "kind": "notify"})
    assert is_ok(omitted)
    assert "product_session_ref" not in omitted.value
    assert is_ok(validate_family_payload("send_message", dict(named.value)))
    assert is_ok(validate_family_payload("send_message", dict(omitted.value)))


def test_send_message_payload_omits_null_and_wrong_names() -> None:
    null = parse_send_message_payload({"product_session_ref": None, "kind": "handoff"})
    assert is_refusal(null)
    assert null.context["field"] == "product_session_ref"
    own_id = parse_send_message_payload({"product_session_id": "psess:H"})
    assert is_refusal(own_id)
    assert own_id.context["field"] == "product_session_id"
    originating = parse_send_message_payload({"originating_psess": "psess:H"})
    assert is_refusal(originating)
    epic73 = parse_send_message_payload({"originating_product_session_ref": "psess:H"})
    assert is_refusal(epic73)
    assert epic73.context["field"] == "originating_product_session_ref"


def test_inspect_sha_field_absent_types_present() -> None:
    assert MAILBOX_INSPECT_SHA == "34c148be"
    assert PRODUCT_SESSION_REF_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_product_session_ref_existed_at_inspect_sha(True))
    assert is_ok(claim_product_session_ref_existed_at_inspect_sha(False))
    assert is_refusal(claim_envelope_types_absent_at_inspect_sha(True))
    assert is_ok(claim_envelope_types_absent_at_inspect_sha(False))
