"""Story 69.2 — addable list_mailbox query name, capability, and typed unavailability."""

from __future__ import annotations

from typing import cast

from qma.core.ports.mailbox import (
    ENVELOPE_TYPES_EXISTED_AT_INSPECT_SHA,
    claim_envelope_types_absent_at_inspect_sha,
)
from qma.wire import (
    ADDABLE_QUERY_COUNT,
    LIST_MAILBOX_CAPABILITY,
    LIST_MAILBOX_CAPABILITY_MINTED,
    LIST_MAILBOX_CONTRACT,
    LIST_MAILBOX_EXISTED_AT_INSPECT_SHA,
    LIST_MAILBOX_HANDLER_OWNER,
    LIST_MAILBOX_HTTP_PATH,
    LIST_MAILBOX_INSPECT_SHA,
    LIST_MAILBOX_NEW_CT_MINTED,
    LIST_MAILBOX_QUERY_NAME,
    SEED_COMMAND_COUNT,
    SEED_EVENT_COUNT,
    SEED_QUERY_COUNT,
    WIRE_QUERIES,
    WireConnection,
    WireQuery,
    claim_list_mailbox_existed_at_inspect_sha,
    parse_list_mailbox_args,
    parse_mailbox_snapshot,
    query_unavailable,
    require_list_mailbox_capability,
    validate_family_payload,
)
from qma.wire.initialize import WIRE_PROTOCOL_VERSION, InitializeParams
from qmf.core.refusal import Ok, RefusalCategory, is_ok, is_refusal

_RECORD_ID = "prid:" + ("ab" * 16)


def test_list_mailbox_is_addable_ct40_and_absent_at_inspect_sha() -> None:
    assert LIST_MAILBOX_QUERY_NAME == "list_mailbox" == WireQuery.LIST_MAILBOX.value
    assert LIST_MAILBOX_QUERY_NAME in WIRE_QUERIES
    assert LIST_MAILBOX_CONTRACT == "CT-40"
    assert LIST_MAILBOX_NEW_CT_MINTED is False
    assert LIST_MAILBOX_HANDLER_OWNER == "COMP-QMA-DAEMON"
    assert LIST_MAILBOX_HTTP_PATH == "/q/list_mailbox"
    assert SEED_COMMAND_COUNT == 9
    assert SEED_QUERY_COUNT == 7
    assert SEED_EVENT_COUNT == 10
    assert ADDABLE_QUERY_COUNT == 7
    assert LIST_MAILBOX_EXISTED_AT_INSPECT_SHA is False
    assert LIST_MAILBOX_INSPECT_SHA == "34c148be"
    assert ENVELOPE_TYPES_EXISTED_AT_INSPECT_SHA is True
    assert is_refusal(claim_list_mailbox_existed_at_inspect_sha(True))
    assert is_ok(claim_list_mailbox_existed_at_inspect_sha(False))
    assert is_refusal(claim_envelope_types_absent_at_inspect_sha(True))
    assert is_ok(claim_envelope_types_absent_at_inspect_sha(False))
    assert is_ok(validate_family_payload("list_mailbox", {}))
    assert is_ok(validate_family_payload("list_mailbox", {"product_session_ref": "psess:H"}))


def test_parse_list_mailbox_args_pair_without_client_msg_id() -> None:
    empty = parse_list_mailbox_args({})
    assert isinstance(empty, Ok)
    assert dict(empty.value) == {}
    session = parse_list_mailbox_args({"product_session_ref": "psess:H"})
    assert isinstance(session, Ok)
    assert session.value["product_session_ref"] == "psess:H"
    pair = parse_list_mailbox_args(
        {
            "product_session_ref": "psess:H",
            "producer_id": "tab:P",
            "wire_id": "C1",
            "msg_id": "client-should-be-ignored",
        }
    )
    assert isinstance(pair, Ok)
    assert pair.value["producer_id"] == "tab:P"
    assert pair.value["wire_id"] == "C1"
    assert "msg_id" not in pair.value
    half = parse_list_mailbox_args({"product_session_ref": "psess:H", "producer_id": "tab:P"})
    assert is_refusal(half)
    aliased = parse_list_mailbox_args({"product_session_id": "psess:H"})
    assert is_refusal(aliased)
    assert aliased.context["field"] == "product_session_id"


def test_query_unavailable_is_typed_never_empty_mailbox() -> None:
    refused = query_unavailable()
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["reason"] == "query_unavailable"
    assert refused.context["name"] == LIST_MAILBOX_QUERY_NAME
    assert refused.context["empty_mailbox"] is False
    missing = require_list_mailbox_capability({})
    assert is_refusal(missing)
    assert missing.context["reason"] == "query_unavailable"
    assert missing.context["empty_mailbox"] is False
    present = require_list_mailbox_capability({LIST_MAILBOX_CAPABILITY: True})
    assert is_ok(present)


def test_initialize_omit_list_mailbox_is_query_unavailable() -> None:
    assert LIST_MAILBOX_CAPABILITY_MINTED is True
    conn = WireConnection()
    assert isinstance(conn.authenticate_pairing(_RECORD_ID), Ok)
    params = InitializeParams.try_create(
        protocol_version=WIRE_PROTOCOL_VERSION,
        capabilities={"commands": True},
        client_producer_id="tab:omit",
    )
    assert isinstance(params, Ok)
    finished = conn.complete_initialize(
        params.value,
        assign_producer_id="tab:omit",
        advertise_pairing=False,
        server_capabilities={"commands": True},
    )
    assert isinstance(finished, Ok)
    assert conn.capabilities.get("list_mailbox") is not True
    gated = conn.require_query_capability("list_mailbox")
    assert is_refusal(gated)
    assert gated.context["reason"] == "query_unavailable"
    assert gated.context["empty_mailbox"] is False


def test_parse_mailbox_snapshot_round_trip() -> None:
    parsed = parse_mailbox_snapshot(
        {
            "query": "list_mailbox",
            "product_chat": True,
            "product_session_ref": "psess:H",
            "rows": [
                {
                    "envelope": {"msg_id": "msg-1", "kind": "handoff"},
                    "delivery_state": "queued",
                    "msg_id": "msg-1",
                    "producer_id": "tab:P",
                    "wire_id": "C1",
                }
            ],
        }
    )
    assert isinstance(parsed, Ok)
    payload = dict(parsed.value.to_payload())
    assert payload["product_chat"] is True
    assert payload["product_session_ref"] == "psess:H"
    rows = payload["rows"]
    assert isinstance(rows, list)
    first = cast("dict[str, object]", rows[0])
    assert first["msg_id"] == "msg-1"
