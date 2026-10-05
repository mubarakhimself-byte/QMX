"""MA02 names, literal opt-in and closed DTO domains."""

from __future__ import annotations

import pytest
from qma.core.app_candidate import json_object
from qma.wire.app_candidate import CANDIDATE_CAPABILITIES, parse_candidate_args
from qma.wire.initialize import InitializeParams, negotiate_initialize
from qma.wire.vocabulary import MessageFamily, family_of
from qmf.core import is_ok, is_refusal


@pytest.mark.parametrize("value", [None, False, 0, 1, "true", {}, []])
def test_candidate_names_need_literal_true(value: object) -> None:
    offered = {} if value is None else dict.fromkeys(CANDIDATE_CAPABILITIES, value)
    params = InitializeParams.try_create(
        protocol_version="1.0.0", client_producer_id="ma02", capabilities=offered
    )
    assert is_ok(params)
    result = negotiate_initialize(
        params.value,
        server_capabilities=dict.fromkeys(CANDIDATE_CAPABILITIES, True),
        advertise_pairing=True,
    )
    assert is_ok(result)
    assert not any(name in result.value.capabilities for name in CANDIDATE_CAPABILITIES)


def test_partial_optin_cannot_echo_backend_support() -> None:
    params = InitializeParams.try_create(
        protocol_version="1.0.0",
        client_producer_id="ma02",
        capabilities={"save_app_candidate": True},
    )
    assert is_ok(params)
    result = negotiate_initialize(
        params.value, server_capabilities={"save_app_candidate": True}, advertise_pairing=False
    )
    assert is_ok(result)
    assert result.value.capabilities["save_app_candidate"] is True
    unsupported = negotiate_initialize(
        params.value, server_capabilities={}, advertise_pairing=False
    )
    assert is_ok(unsupported) and "save_app_candidate" not in unsupported.value.capabilities
    assert family_of("save_app_candidate") is MessageFamily.COMMAND
    assert family_of("get_app_candidate") is MessageFamily.QUERY
    assert family_of("get_app_candidate_history") is MessageFamily.QUERY


@pytest.mark.parametrize(
    "args",
    [
        {},
        {"product_session_ref": "tab:x"},
        {"product_session_ref": "psess:a", "profile": "authoring"},
        {"product_session_ref": "psess:a", "content": {}, "expected_context_revision": True},
        {
            "product_session_ref": "psess:a",
            "content": {},
            "expected_context_revision": 0,
            "candidate_id": "appcand:client",
        },
        {
            "product_session_ref": "psess:a",
            "content": {},
            "expected_context_revision": 0,
            "expected_revision": "fp1:client",
        },
    ],
)
def test_unknown_authority_missing_fields_and_bad_cas_refuse(args: object) -> None:
    assert is_refusal(parse_candidate_args("save_app_candidate", args))


def test_json_object_does_not_evaluate_strings() -> None:
    assert is_ok(json_object(b'{"note":"import os; os.system(...)"}'))
    assert is_refusal(json_object(b'{"note":Infinity}'))
