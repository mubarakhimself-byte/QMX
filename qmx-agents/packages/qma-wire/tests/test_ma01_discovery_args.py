"""Closed MA-01 wire requests and host-only capability scope."""

from __future__ import annotations

import pytest
from qma.wire.discovery_queries import parse_discovery_args, require_discovery_capability
from qma.wire.initialize import InitializeParams, negotiate_initialize
from qma.wire.schemas import validate_instance
from qmf.core import is_ok, is_refusal


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("list_installed_plugins", None),
        ("list_installed_plugins", []),
        ("list_installed_plugins", {"grant_id": "grant:forged"}),
        ("list_installed_plugins", {1: "bad"}),
        ("list_installed_plugins", {"product_session_ref": ""}),
        ("list_installed_plugins", {"product_session_ref": "psess:"}),
        ("list_installed_plugins", {"product_session_ref": None}),
        ("facade_search", {}),
        ("facade_search", {"query": " "}),
        ("facade_search", {"query": True}),
        ("facade_search", {"query": "x", "mode": "hybrid"}),
        ("facade_search", {"query": "x", "hit_class": "hypothesis"}),
        ("facade_search", {"query": "x", "source_ref": "unmounted"}),
        ("facade_get", {}),
        ("facade_get", {"hit": {"hit_class": "qml_candidate"}}),
    ],
)
def test_malformed_closed_requests_refuse(name: str, value: object) -> None:
    assert is_refusal(parse_discovery_args(name, value))


@pytest.mark.parametrize(
    "value", [None, {}, {"facade_search": False}, {"facade_search": 1}, {"facade_search": "true"}]
)
def test_capability_requires_exact_host_boolean(value: object) -> None:
    result = require_discovery_capability("facade_search", value)
    assert is_refusal(result) and result.context["reason"] == "query_unavailable"


def test_host_advertises_partial_facade_and_client_cannot_expand_classes() -> None:
    params = InitializeParams.try_create(
        protocol_version="1.0.0",
        client_producer_id="client-ma01",
        capabilities={
            "facade_search": True,
            "get_instance_health": True,
            "discovery_hit_classes": ["artifact", "knowledge"],
        },
    )
    assert is_ok(params)
    result = negotiate_initialize(
        params.value,
        server_capabilities={
            "facade_search": True,
            "get_instance_health": False,
            "discovery_hit_classes": ["contribution"],
        },
    )
    assert is_ok(result)
    assert result.value.capabilities["facade_search"] is True
    assert result.value.capabilities["get_instance_health"] is False
    assert result.value.capabilities["discovery_hit_classes"] == ["contribution"]


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("list_installed_plugins", {}),
        ("list_installed_plugins", {"product_session_ref": "psess:home"}),
        ("facade_search", {"query": "analysis-backtest"}),
        ("facade_search", {"query": "x", "hit_class": "artifact"}),
        (
            "facade_get",
            {
                "hit": {
                    "hit_class": "knowledge",
                    "source_ref": "s",
                    "snapshot_ref": "snap",
                    "locator": "loc",
                }
            },
        ),
    ],
)
def test_accepted_requests_match_shipped_schema(name: str, args: object) -> None:
    result = parse_discovery_args(name, args)
    assert is_ok(result), result
    assert is_ok(validate_instance(args, "discovery_args"))


@pytest.mark.parametrize("requested", [False, 1, "true", None])
def test_discovery_negotiation_does_not_enable_false_or_nonboolean_requests(
    requested: object,
) -> None:
    params = InitializeParams.try_create(
        protocol_version="1.0.0",
        client_producer_id="client-ma01",
        capabilities={"facade_search": requested, "invoke_contribution_pin": requested},
    )
    if requested is None:
        assert is_refusal(params)  # Existing initialize grammar prohibits null values.
        return
    assert is_ok(params)
    negotiated = negotiate_initialize(
        params.value,
        server_capabilities={"facade_search": True, "invoke_contribution_pin": True},
    )
    assert is_ok(negotiated)
    assert negotiated.value.capabilities.get("facade_search") is not True
    assert negotiated.value.capabilities.get("invoke_contribution_pin") is not True
