"""Optional method capability and authority-free parser contracts."""

from __future__ import annotations

import pytest
from qma.wire.agent_request import (
    AGENT_REQUEST_CAPABILITIES,
    parse_cancel_agent_request,
    parse_get_agent_request,
    parse_submit_agent_request,
    require_agent_request_capability,
)
from qma.wire.initialize import WIRE_PROTOCOL_VERSION, InitializeParams, WireConnection
from qma.wire.principals import authorize_wire_command
from qma.wire.vocabulary import MessageFamily, family_of
from qmf.core import is_ok, is_refusal


def test_submit_exact_data_and_no_authority_fields() -> None:
    body: dict[str, object] = {
        "product_session_ref": "psess:one",
        "profile_id": "app-reader",
        "prompt": "Read the corpus metadata",
        "idempotency_key": "one",
    }
    result = parse_submit_agent_request(body)
    assert is_ok(result) and result.value.to_payload() == body
    for field in ("principal", "provider", "model", "instructions", "grants", "target", "tools"):
        assert is_refusal(parse_submit_agent_request({**body, field: "injected"}))
    assert is_refusal(parse_submit_agent_request({**body, "prompt": "a" * 16385}))
    assert is_refusal(parse_submit_agent_request({**body, "product_session_ref": "other:one"}))


def test_reference_parsers_and_method_families() -> None:
    body = {"request_id": "req:one", "product_session_ref": "psess:one"}
    assert is_ok(parse_get_agent_request(body))
    assert is_ok(parse_cancel_agent_request(body))
    assert is_refusal(parse_get_agent_request({**body, "principal": "operator"}))
    assert family_of("submit_agent_request") == MessageFamily.COMMAND
    assert family_of("cancel_agent_request") == MessageFamily.COMMAND
    assert family_of("get_agent_request") == MessageFamily.QUERY


@pytest.mark.parametrize("method", sorted(AGENT_REQUEST_CAPABILITIES))
def test_distinct_server_owned_capabilities(method: str) -> None:
    assert is_refusal(require_agent_request_capability({}, method))
    assert is_refusal(require_agent_request_capability({method: 1}, method))
    assert is_ok(require_agent_request_capability({method: True}, method))
    conn = WireConnection()
    assert is_ok(conn.authenticate("cred://test/operator", principal_class="operator"))
    params = InitializeParams.try_create(
        protocol_version=WIRE_PROTOCOL_VERSION,
        capabilities=dict.fromkeys(AGENT_REQUEST_CAPABILITIES, True),
    )
    assert is_ok(params)
    result = conn.complete_initialize(
        params.value,
        server_capabilities={method: True},
        assign_producer_id="producer:" + method,
        request_id=1,
    )
    assert is_ok(result)
    assert conn.capabilities.get(method) is True
    for other in AGENT_REQUEST_CAPABILITIES - {method}:
        assert conn.capabilities.get(other) is not True


@pytest.mark.parametrize("method", ["submit_agent_request", "cancel_agent_request"])
def test_machine_cannot_issue_operator_agent_commands(method: str) -> None:
    assert is_refusal(authorize_wire_command(method, "machine"))
    assert is_ok(authorize_wire_command(method, "operator"))


@pytest.mark.parametrize(
    "field", ["profile_id", "prompt", "product_session_ref", "idempotency_key"]
)
def test_lone_surrogates_are_typed_refusals(field: str) -> None:
    body: dict[str, object] = {
        "product_session_ref": "psess:one",
        "profile_id": "reader",
        "prompt": "read",
        "idempotency_key": "one",
    }
    body[field] = "\ud800"
    assert is_refusal(parse_submit_agent_request(body))
