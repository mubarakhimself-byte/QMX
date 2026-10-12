"""Story 41.4 — secure listener posture and remote dial-out spool (FR-Q17, FR-Q18)."""

from __future__ import annotations

from typing import cast

from qma.wire import (
    DAEMON_DIAL_DIRECTION,
    DEFAULT_BIND_HOST,
    FORBIDDEN_SECRET_SURFACE_KEYS,
    REMOTE_DIAL_DIRECTION,
    WIRE_PROTOCOL_VERSION,
    DeployedSideConfig,
    InitializeParams,
    ListenerBindConfig,
    WireConnection,
    assert_no_secret_on_wire_surface,
    authenticate_before_protocol,
    is_loopback_host,
    load_schema,
    validate_deployed_side,
    validate_instance,
    validate_listener_startup,
    validate_remote_dial_out,
)
from qmf.core.refusal import Ok, RefusalCategory, is_ok, is_refusal


def test_default_bind_is_loopback() -> None:
    assert DEFAULT_BIND_HOST == "127.0.0.1"
    assert is_loopback_host(DEFAULT_BIND_HOST) is True
    assert is_loopback_host("localhost") is True
    assert is_loopback_host("::1") is True
    assert is_loopback_host("10.0.0.1") is False
    assert is_loopback_host("192.168.1.10") is False

    cfg = ListenerBindConfig.try_create()
    assert isinstance(cfg, Ok)
    assert cfg.value.host == DEFAULT_BIND_HOST
    posture = validate_listener_startup(cfg.value)
    assert isinstance(posture, Ok)
    assert posture.value.loopback is True
    assert posture.value.authentication_required is True
    assert posture.value.websocket_url_prefix == "ws://"


def test_non_loopback_requires_wss_https_and_recorded_operator_config() -> None:
    cfg = ListenerBindConfig.try_create(
        host="10.0.0.8",
        websocket_scheme="wss",
        query_scheme="https",
        require_authentication=True,
        operator_recorded_config=True,
    )
    assert isinstance(cfg, Ok)
    posture = validate_listener_startup(cfg.value)
    assert isinstance(posture, Ok)
    assert posture.value.loopback is False
    assert posture.value.websocket_url_prefix == "wss://"
    assert posture.value.query_url_prefix == "https://"
    assert posture.value.operator_recorded_config is True


def test_plaintext_non_loopback_is_hard_startup_refusal() -> None:
    cfg = ListenerBindConfig.try_create(
        host="10.0.0.8",
        websocket_scheme="ws",
        query_scheme="http",
        require_authentication=True,
        operator_recorded_config=True,
    )
    assert isinstance(cfg, Ok)
    refused = validate_listener_startup(cfg.value)
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["startup"] is True
    assert "plaintext" in str(refused.context["reason"])


def test_non_loopback_without_recorded_operator_config_refused() -> None:
    cfg = ListenerBindConfig.try_create(
        host="10.0.0.8",
        websocket_scheme="wss",
        query_scheme="https",
        require_authentication=True,
        operator_recorded_config=False,
    )
    assert isinstance(cfg, Ok)
    refused = validate_listener_startup(cfg.value)
    assert is_refusal(refused)
    assert refused.context["field"] == "operator_recorded_config"
    assert refused.context["startup"] is True


def test_unauthenticated_bind_is_hard_startup_refusal() -> None:
    for host in (DEFAULT_BIND_HOST, "10.0.0.8"):
        cfg = ListenerBindConfig.try_create(
            host=host,
            websocket_scheme="wss" if host != DEFAULT_BIND_HOST else "ws",
            query_scheme="https" if host != DEFAULT_BIND_HOST else "http",
            require_authentication=False,
            operator_recorded_config=host != DEFAULT_BIND_HOST,
        )
        assert isinstance(cfg, Ok)
        refused = validate_listener_startup(cfg.value)
        assert is_refusal(refused)
        assert refused.context["field"] == "require_authentication"
        assert refused.context["startup"] is True
        assert refused.retryability.value == "no"


def test_credential_ref_authenticates_before_protocol_no_secret_on_surface() -> None:
    session = authenticate_before_protocol(
        "cred://models/openai",
        principal_class="machine",
    )
    assert isinstance(session, Ok)
    assert session.value.authenticated_before_protocol is True
    assert str(session.value.credential_ref) == "cred://models/openai"
    assert session.value.principal_class.value == "machine"

    diagnostic = session.value.to_diagnostic()
    trace = session.value.to_trace()
    assert is_ok(assert_no_secret_on_wire_surface(diagnostic))
    assert is_ok(assert_no_secret_on_wire_surface(trace))
    assert "secret" not in diagnostic
    assert diagnostic["principal_class"] == "machine"
    assert FORBIDDEN_SECRET_SURFACE_KEYS  # closed deny list is non-empty

    secretish = authenticate_before_protocol(
        "secret=literally-a-value",
        principal_class="operator",
    )
    assert is_refusal(secretish)

    envelope_with_secret: dict[str, object] = {
        "v": "1.0.0",
        "type": "start_mission",
        "id": "1",
        "producer_id": "p",
        "correlation_id": "c",
        "scope_path": [],
        "payload": {"token": "abc"},
    }
    assert is_refusal(assert_no_secret_on_wire_surface(envelope_with_secret))

    schema = load_schema("initialize")
    examples_obj = schema.get("examples", [])
    assert isinstance(examples_obj, list)
    for example_obj in cast(list[object], examples_obj):
        assert isinstance(example_obj, dict)
        example = cast(dict[str, object], example_obj)
        assert is_ok(assert_no_secret_on_wire_surface(example))
        assert "credential_ref" in example
        assert "secret" not in example
        assert is_ok(validate_instance(example, "initialize"))


def test_wire_connection_requires_auth_before_initialize() -> None:
    conn = WireConnection()
    params = InitializeParams.try_create(protocol_version=WIRE_PROTOCOL_VERSION)
    assert isinstance(params, Ok)
    refused = conn.complete_initialize(params.value, assign_producer_id="p")
    assert is_refusal(refused)
    assert refused.context["field"] == "authentication"

    authed = conn.authenticate("cred://models/openai", principal_class="operator")
    assert isinstance(authed, Ok)
    assert conn.credential_ref == "cred://models/openai"
    assert conn.principal_class is not None
    assert conn.principal_class.value == "operator"
    finished = conn.complete_initialize(params.value, assign_producer_id="p")
    assert is_ok(finished)


def test_remote_dials_out_daemon_never_dials_in() -> None:
    assert REMOTE_DIAL_DIRECTION == "out"
    assert DAEMON_DIAL_DIRECTION == "never_in"

    cfg = DeployedSideConfig.try_create(
        dials_out_to_daemon=True,
        exposes_inbound_listener=False,
        second_transport_channel=False,
        daemon_address="wss://daemon.example:8443",
    )
    assert isinstance(cfg, Ok)
    posture = validate_remote_dial_out(cfg.value)
    assert isinstance(posture, Ok)
    assert posture.value.daemon_is_sole_inbound is True
    assert posture.value.deployed_exposes_listener is False
    assert posture.value.deployed_second_transport is False
    assert posture.value.remote_dial_direction == "out"

    listening = DeployedSideConfig.try_create(
        dials_out_to_daemon=True,
        exposes_inbound_listener=True,
        daemon_address="wss://daemon.example:8443",
    )
    assert isinstance(listening, Ok)
    assert is_refusal(validate_deployed_side(listening.value))

    second = DeployedSideConfig.try_create(
        dials_out_to_daemon=True,
        second_transport_channel=True,
        daemon_address="wss://daemon.example:8443",
    )
    assert isinstance(second, Ok)
    assert is_refusal(validate_deployed_side(second.value))
