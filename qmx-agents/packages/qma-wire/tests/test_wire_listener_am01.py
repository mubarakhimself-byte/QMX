"""Story 68.2 — AM-01 named carve-out of the Story 41.4 unauthenticated bind."""

from __future__ import annotations

from pathlib import Path

from qma.wire import (
    AM_01_NAME,
    AM_01_UNAUTHENTICATED_POST_PATHS,
    CORS_EXISTED_AT_INSPECT_SHA,
    DAEMON_DIAL_DIRECTION,
    DEC_0304_SUPERSEDED_BY,
    DEC_0323_SUPERSEDED_BY,
    DEFAULT_BIND_HOST,
    LISTENER_POSTURE_TYPES_EXISTED_AT_INSPECT_SHA,
    PAIR_HTTP_EXISTED_AT_INSPECT_SHA,
    REMOTE_DIAL_DIRECTION,
    UNAUTHENTICATED_BIND_SENTENCE,
    UNAUTHENTICATED_BIND_SENTENCE_HELD,
    Am01UnauthenticatedHttp,
    ListenerBindConfig,
    ListenerPosture,
    claim_cors_existed_at_inspect_sha,
    claim_listener_posture_types_absent_at_inspect_sha,
    claim_pair_http_existed_at_inspect_sha,
    claim_unauthenticated_bind_sentence_dropped,
    classify_am01_unauthenticated_http,
    is_am01_cors_route,
    is_loopback_host,
    validate_listener_startup,
)
from qma.wire.listener import (
    PAIR_CONFIRM_PATH,
    PAIR_RENEW_PATH,
    PAIR_START_PATH,
    is_artifacts_get_path,
    is_snapshot_family_path,
)
from qmf.core.refusal import RefusalCategory, is_ok, is_refusal

_LISTENER_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "wire" / "listener.py"


def test_am01_holds_unauthenticated_bind_sentence_and_does_not_supersede() -> None:
    assert UNAUTHENTICATED_BIND_SENTENCE_HELD is True
    assert UNAUTHENTICATED_BIND_SENTENCE == "unauthenticated bind is a hard startup refusal"
    assert AM_01_NAME == "AM-01"
    assert DEC_0304_SUPERSEDED_BY is None
    assert DEC_0323_SUPERSEDED_BY is None
    source = _LISTENER_SRC.read_text(encoding="utf-8")
    assert UNAUTHENTICATED_BIND_SENTENCE in source
    assert "AM-01" in source
    assert is_refusal(claim_unauthenticated_bind_sentence_dropped(True))
    assert is_ok(claim_unauthenticated_bind_sentence_dropped(False))

    cfg = ListenerBindConfig.try_create(require_authentication=False)
    assert is_ok(cfg)
    refused = validate_listener_startup(cfg.value)
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["startup"] is True
    assert refused.context["field"] == "require_authentication"
    assert refused.context["reason"] == UNAUTHENTICATED_BIND_SENTENCE
    assert refused.context["named_amendment"] == AM_01_NAME
    assert refused.context["am01_http_carve_out_is_not_unauthenticated_bind"] is True


def test_story_41_4_loopback_tls_never_dials_in_unchanged() -> None:
    assert DEFAULT_BIND_HOST == "127.0.0.1"
    assert is_loopback_host(DEFAULT_BIND_HOST) is True
    loopback = ListenerBindConfig.try_create()
    assert is_ok(loopback)
    posture = validate_listener_startup(loopback.value)
    assert is_ok(posture)
    assert isinstance(posture.value, ListenerPosture)
    assert posture.value.authentication_required is True
    assert posture.value.loopback is True

    tls = ListenerBindConfig.try_create(
        host="10.0.0.8",
        websocket_scheme="wss",
        query_scheme="https",
        require_authentication=True,
        operator_recorded_config=True,
    )
    assert is_ok(tls)
    assert is_ok(validate_listener_startup(tls.value))

    plaintext = ListenerBindConfig.try_create(
        host="10.0.0.8",
        websocket_scheme="ws",
        query_scheme="http",
        require_authentication=True,
        operator_recorded_config=True,
    )
    assert is_ok(plaintext)
    refused = validate_listener_startup(plaintext.value)
    assert is_refusal(refused)
    assert "plaintext" in str(refused.context["reason"])
    assert DAEMON_DIAL_DIRECTION == "never_in"
    assert REMOTE_DIAL_DIRECTION == "out"


def test_three_path_carve_out_classifier() -> None:
    assert frozenset({PAIR_START_PATH, PAIR_CONFIRM_PATH}) == AM_01_UNAUTHENTICATED_POST_PATHS
    assert classify_am01_unauthenticated_http("POST", "/pair/start") is (
        Am01UnauthenticatedHttp.POST_PAIR_START
    )
    assert classify_am01_unauthenticated_http("POST", "/pair/confirm") is (
        Am01UnauthenticatedHttp.POST_PAIR_CONFIRM
    )
    assert classify_am01_unauthenticated_http("OPTIONS", "/pair/start") is (
        Am01UnauthenticatedHttp.CORS_OPTIONS
    )
    assert classify_am01_unauthenticated_http("OPTIONS", "/pair/confirm") is (
        Am01UnauthenticatedHttp.CORS_OPTIONS
    )
    assert classify_am01_unauthenticated_http("OPTIONS", "/pair/renew") is (
        Am01UnauthenticatedHttp.CORS_OPTIONS
    )
    assert classify_am01_unauthenticated_http("OPTIONS", "/artifacts/stage") is (
        Am01UnauthenticatedHttp.CORS_OPTIONS
    )
    assert classify_am01_unauthenticated_http("OPTIONS", "/q/list_mailbox") is (
        Am01UnauthenticatedHttp.CORS_OPTIONS
    )
    assert classify_am01_unauthenticated_http("OPTIONS", "/q/facade_search") is (
        Am01UnauthenticatedHttp.CORS_OPTIONS
    )
    assert (
        classify_am01_unauthenticated_http(
            "OPTIONS",
            "/artifacts/fp1:sha256:abcd",
        )
        is Am01UnauthenticatedHttp.CORS_OPTIONS
    )

    assert classify_am01_unauthenticated_http("POST", PAIR_RENEW_PATH) is None
    assert classify_am01_unauthenticated_http("GET", "/pair/start") is None
    assert classify_am01_unauthenticated_http("PUT", "/artifacts/stage") is None
    assert classify_am01_unauthenticated_http("GET", "/q/list_mailbox") is None
    assert classify_am01_unauthenticated_http("GET", "/artifacts/fp1:sha256:abcd") is None
    assert classify_am01_unauthenticated_http("OPTIONS", "/initialize") is None
    assert classify_am01_unauthenticated_http("OPTIONS", "/host/status") is None
    assert classify_am01_unauthenticated_http("POST", "/host/pair") is None


def test_cors_routes_are_the_named_ad5_catalogue() -> None:
    assert is_am01_cors_route("/pair/start") is True
    assert is_am01_cors_route("/pair/confirm") is True
    assert is_am01_cors_route("/pair/renew") is True
    assert is_am01_cors_route("/artifacts/stage") is True
    assert is_snapshot_family_path("/q/list_mailbox") is True
    assert is_snapshot_family_path("/q/get_pack_ui_request") is True
    assert is_snapshot_family_path("/q/get_editor_draft_head") is True
    assert is_artifacts_get_path("/artifacts/fp1:sha256:deadbeef") is True
    assert is_artifacts_get_path("/artifacts/stage") is False
    assert is_am01_cors_route("/initialize") is False
    assert is_am01_cors_route("/") is False


def test_inspect_sha_honesty_pair_http_and_listener_types() -> None:
    assert PAIR_HTTP_EXISTED_AT_INSPECT_SHA is False
    assert CORS_EXISTED_AT_INSPECT_SHA is False
    assert LISTENER_POSTURE_TYPES_EXISTED_AT_INSPECT_SHA is True
    assert is_refusal(claim_pair_http_existed_at_inspect_sha(True))
    assert is_ok(claim_pair_http_existed_at_inspect_sha(False))
    assert is_refusal(claim_cors_existed_at_inspect_sha(True))
    assert is_ok(claim_cors_existed_at_inspect_sha(False))
    assert is_refusal(claim_listener_posture_types_absent_at_inspect_sha(True))
    assert is_ok(claim_listener_posture_types_absent_at_inspect_sha(False))
