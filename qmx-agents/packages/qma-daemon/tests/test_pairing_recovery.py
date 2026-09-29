"""Story 68.6 — reload, cold start, clone, and renew are different recoveries."""

from __future__ import annotations

from pathlib import Path

import pytest
from qma.daemon import AuthoritativeJournal, PersistenceSubstrate
from qma.daemon.http_pair import (
    ACCESS_CONTROL_ALLOW_CREDENTIALS,
    CORS_EXISTED_AT_INSPECT_SHA,
    CORS_REFLECT_ANY_AFTER_PAIR,
    PairHttpRequest,
    PairHttpResponse,
    claim_cors_existed_at_inspect_sha,
    cors_allow_origin,
    cors_options_response,
    refuse_cors_preflight_retarget,
)
from qma.daemon.pairing import (
    CHROME_SERVED_FROM_DAEMON_PORT,
    DAEMON_HTTP_PORT,
    LIST_MAILBOX_MINTED_THIS_STORY,
    PAIRING_HTTP_EXISTED_AT_INSPECT_SHA,
    PAIRING_PROOF_MAY_BIND_MULTIPLE_CONNECTIONS,
    PAIRING_WS_SUBPROTOCOLS_EXISTED_AT_INSPECT_SHA,
    QMX_UI_SCAFFOLDED_THIS_STORY,
    SPA_SAMPLE_ORIGIN,
    PairingRecoveryKind,
    PairingWsHandle,
    PairingWsRegistry,
    authenticate_http_pairing_bearer,
    authenticate_ws_pairing_upgrade,
    claim_chrome_served_from_8765,
    claim_pair_http_existed_at_inspect_sha,
    claim_pairing_transports_existed_at_inspect_sha,
    claim_this_story_scaffolded_qmx_ui,
    classify_pairing_recovery,
    close_expired_pairing_sockets,
    is_daemon_http_origin,
    issue_pairing_session,
    journal_blob_contains_secret,
    pairing_proof_fp1,
    recover_pairing_connection,
    refuse_auto_resend,
    refuse_journal_proof_retrieval,
    refuse_origin_only_recovery,
    renew_pairing_session,
)
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.wire.auth import PAIRING_HTTP_AUTHORIZATION_PREFIX, format_pairing_authorization
from qma.wire.initialize import LiveProducerRegistry
from qma.wire.listener import CT40_WS_SUBPROTOCOL, format_pairing_websocket_subprotocols
from qmf.core import DataDrivenClock, Instant, is_ok, is_refusal
from qmf.core.refusal import RefusalCategory

_ORIGIN = "http://127.0.0.1:5173"
_OTHER_ORIGIN = "http://127.0.0.1:4173"
_DAEMON_ORIGIN = "http://127.0.0.1:8765"
_EXPIRES_AT = 1_800_000_000_000_000_000
_NOW_NS = 1_710_000_000_000_000_010


def _test_clock(*, boot: str = "boot-68-6", n: int = 64) -> DataDrivenClock:
    base = 1_710_000_000_000_000_000
    walls = tuple(Instant(value_ns=base + i) for i in range(n))
    monos = tuple(i * 1_000 for i in range(n))
    return DataDrivenClock(boot_epoch_id=boot, wall_instants=walls, monotonic_ns=monos)


def _open_journal(
    tmp_path: Path, *, boot: str = "boot-68-6"
) -> tuple[PersistenceSubstrate, AuthoritativeJournal]:
    substrate_result = PersistenceSubstrate.open(tmp_path, machine="test-host", boot_epoch_id=boot)
    assert is_ok(substrate_result), substrate_result
    substrate = substrate_result.value
    journal_result = AuthoritativeJournal.bind(substrate, clock=_test_clock(boot=boot))
    assert is_ok(journal_result), journal_result
    return substrate, journal_result.value


def _issue(journal: AuthoritativeJournal, sqlite: SingleSqliteWriter) -> tuple[str, str]:
    issued = issue_pairing_session(
        journal=journal,
        sqlite=sqlite,
        origin=_ORIGIN,
        expires_at=_EXPIRES_AT,
    )
    assert is_ok(issued), issued
    return issued.value.pairing_record_id, issued.value.pairing_proof


def _options(path: str, origin: str) -> PairHttpRequest:
    built = PairHttpRequest.try_create(
        method="OPTIONS",
        path=path,
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )
    assert is_ok(built), built
    return built.value


def test_honesty_inspect_sha_and_chrome_contract() -> None:
    assert PAIRING_HTTP_EXISTED_AT_INSPECT_SHA is False
    assert CORS_EXISTED_AT_INSPECT_SHA is False
    assert PAIRING_WS_SUBPROTOCOLS_EXISTED_AT_INSPECT_SHA is False
    assert CHROME_SERVED_FROM_DAEMON_PORT is False
    assert QMX_UI_SCAFFOLDED_THIS_STORY is False
    assert LIST_MAILBOX_MINTED_THIS_STORY is False
    assert CORS_REFLECT_ANY_AFTER_PAIR is False
    assert ACCESS_CONTROL_ALLOW_CREDENTIALS == "false"
    assert SPA_SAMPLE_ORIGIN == "http://127.0.0.1:5173"
    assert DAEMON_HTTP_PORT == 8765
    assert PAIRING_PROOF_MAY_BIND_MULTIPLE_CONNECTIONS is True
    assert is_refusal(claim_pair_http_existed_at_inspect_sha(True))
    assert is_ok(claim_pair_http_existed_at_inspect_sha(False))
    assert is_refusal(claim_cors_existed_at_inspect_sha(True))
    assert is_ok(claim_cors_existed_at_inspect_sha(False))
    assert is_refusal(claim_pairing_transports_existed_at_inspect_sha(True))
    assert is_ok(claim_pairing_transports_existed_at_inspect_sha(False))
    assert is_refusal(claim_chrome_served_from_8765(True))
    assert is_ok(claim_chrome_served_from_8765(False))
    assert is_refusal(claim_this_story_scaffolded_qmx_ui(True))
    assert is_ok(claim_this_story_scaffolded_qmx_ui(False))
    assert is_daemon_http_origin(_DAEMON_ORIGIN) is True
    assert is_daemon_http_origin(_ORIGIN) is False


def test_four_recoveries_are_distinct() -> None:
    kinds = {
        classify_pairing_recovery(stored_proof="abcDEF012-_~", producer_id_is_live=False),
        classify_pairing_recovery(stored_proof="", producer_id_is_live=False),
        classify_pairing_recovery(stored_proof="abcDEF012-_~", producer_id_is_live=True),
        classify_pairing_recovery(
            stored_proof="abcDEF012-_~",
            producer_id_is_live=True,
            explicit_renew=True,
        ),
    }
    assert kinds == {
        PairingRecoveryKind.RELOAD,
        PairingRecoveryKind.COLD_START,
        PairingRecoveryKind.CLONE,
        PairingRecoveryKind.RENEW,
    }
    assert (
        classify_pairing_recovery(stored_proof="abcDEF012-_~", producer_id_is_live=False)
        is PairingRecoveryKind.RELOAD
    )
    assert (
        classify_pairing_recovery(stored_proof="", producer_id_is_live=False)
        is PairingRecoveryKind.COLD_START
    )
    assert (
        classify_pairing_recovery(stored_proof="abcDEF012-_~", producer_id_is_live=True)
        is PairingRecoveryKind.CLONE
    )
    assert (
        classify_pairing_recovery(
            stored_proof="abcDEF012-_~",
            producer_id_is_live=True,
            explicit_renew=True,
        )
        is PairingRecoveryKind.RENEW
    )


def test_reload_presents_same_proof_until_expiry(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        record_id, proof = _issue(journal, substrate.sqlite)
        producers = LiveProducerRegistry()
        recovered = recover_pairing_connection(
            substrate.sqlite,
            origin=_ORIGIN,
            stored_proof=proof,
            client_producer_id="tab:reload",
            live_producers=producers,
            connection_token="tab-reload",
            now_ns=_NOW_NS,
            journal=journal,
        )
        assert is_ok(recovered), recovered
        assert recovered.value.kind is PairingRecoveryKind.RELOAD
        assert recovered.value.same_proof is True
        assert recovered.value.producer_id == "tab:reload"
        assert recovered.value.pairing_record_id == record_id
        assert recovered.value.session.principal_class.value == "operator"
        assert recovered.value.session.pairing_record_id == record_id
        assert recovered.value.session.credential_ref is None

        header = f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{proof}"
        http = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=header,
            origin=_ORIGIN,
            now_ns=_NOW_NS,
        )
        assert is_ok(http)
        assert http.value.pairing_record_id == record_id
        assert http.value.credential_ref is None

        offered = format_pairing_websocket_subprotocols(proof)
        assert is_ok(offered)
        ws = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=list(offered.value),
            origin=_ORIGIN,
            now_ns=_NOW_NS,
        )
        assert is_ok(ws)
        assert ws.value.pairing_record_id == record_id
        assert ws.value.echoed_subprotocol == CT40_WS_SUBPROTOCOL
        assert journal_blob_contains_secret(journal, proof) is False
    finally:
        journal.close()
        substrate.close()


def test_expiry_closes_ws_and_http_dead_proof_refuses(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-6-exp")
    try:
        _record_id, proof = _issue(journal, substrate.sqlite)
        registry = PairingWsRegistry()
        handle = PairingWsHandle(proof_fp1=pairing_proof_fp1(proof))
        registry.register(handle)
        closed = close_expired_pairing_sockets(
            substrate.sqlite,
            now_ns=_EXPIRES_AT + 1,
            ws_registry=registry,
        )
        assert closed == 1
        assert handle.closed is True

        header = f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{proof}"
        http = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=header,
            origin=_ORIGIN,
            now_ns=_EXPIRES_AT + 1,
            ws_registry=registry,
        )
        assert is_refusal(http)
        assert http.category is RefusalCategory.POLICY_REJECTION
        assert http.context["field"] == "pairing_proof"

        offered = format_pairing_websocket_subprotocols(proof)
        assert is_ok(offered)
        ws = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=list(offered.value),
            origin=_ORIGIN,
            now_ns=_EXPIRES_AT + 1,
            ws_registry=registry,
        )
        assert is_refusal(ws)
        assert ws.context["field"] == "pairing_proof"
    finally:
        journal.close()
        substrate.close()


def test_cold_start_cannot_renew_or_retrieve_or_auto_resend(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-6-cold")
    try:
        _record_id, proof = _issue(journal, substrate.sqlite)
        producers = LiveProducerRegistry()
        refused = recover_pairing_connection(
            substrate.sqlite,
            origin=_ORIGIN,
            stored_proof="",
            live_producers=producers,
            connection_token="tab-cold",
            now_ns=_NOW_NS,
            journal=journal,
        )
        assert is_refusal(refused)
        assert refused.category is RefusalCategory.POLICY_REJECTION
        assert refused.context["recovery"] == PairingRecoveryKind.COLD_START.value
        assert refused.context["auto_resend"] is False
        assert refused.context["journal_retrieval"] is False
        assert refused.context["list_mailbox_minted"] is False
        assert "/pair/renew is impossible" in str(refused.context["reason"])

        auto = refuse_auto_resend()
        assert auto.category is RefusalCategory.POLICY_REJECTION
        assert auto.context["auto_resend"] is False
        assert auto.context["list_mailbox_minted"] is False

        journal_refused = refuse_journal_proof_retrieval(journal, proof)
        assert is_refusal(journal_refused)
        assert journal_refused.context["journal_retrieval"] is False
        assert journal_blob_contains_secret(journal, proof) is False
    finally:
        journal.close()
        substrate.close()


def test_clone_keeps_existing_proof_and_mints_new_producer_id(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-6-clone")
    try:
        record_id, proof = _issue(journal, substrate.sqlite)
        producers = LiveProducerRegistry()
        first = recover_pairing_connection(
            substrate.sqlite,
            origin=_ORIGIN,
            stored_proof=proof,
            client_producer_id="tab:original",
            live_producers=producers,
            connection_token="tab-a",
            now_ns=_NOW_NS,
        )
        assert is_ok(first)
        assert first.value.kind is PairingRecoveryKind.RELOAD
        assert first.value.producer_id == "tab:original"

        clone = recover_pairing_connection(
            substrate.sqlite,
            origin=_ORIGIN,
            stored_proof=proof,
            client_producer_id="tab:original",
            live_producers=producers,
            connection_token="tab-b",
            now_ns=_NOW_NS,
        )
        assert is_ok(clone), clone
        assert clone.value.kind is PairingRecoveryKind.CLONE
        assert clone.value.same_proof is True
        assert clone.value.pairing_record_id == record_id
        assert clone.value.producer_id != first.value.producer_id
        assert clone.value.producer_id != "tab:original"
        assert producers.is_live(first.value.producer_id) is True
        assert producers.is_live(clone.value.producer_id) is True
        assert producers.owner(first.value.producer_id) == "tab-a"
        assert producers.owner(clone.value.producer_id) == "tab-b"

        origin_only = refuse_origin_only_recovery(_ORIGIN, "")
        assert is_refusal(origin_only)

        not_origin_only = refuse_origin_only_recovery(_ORIGIN, proof)
        assert is_ok(not_origin_only)

        renew_via_recover = recover_pairing_connection(
            substrate.sqlite,
            origin=_ORIGIN,
            stored_proof=proof,
            live_producers=producers,
            connection_token="tab-c",
            now_ns=_NOW_NS,
            explicit_renew=True,
        )
        assert is_refusal(renew_via_recover)
        assert renew_via_recover.context["recovery"] == PairingRecoveryKind.RENEW.value
        assert "not the clone path" in str(renew_via_recover.context["reason"])
    finally:
        journal.close()
        substrate.close()


def test_renew_rotates_proof_and_is_not_clone(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-6-renew")
    try:
        record_id, proof = _issue(journal, substrate.sqlite)
        registry = PairingWsRegistry()
        handle = PairingWsHandle(proof_fp1=pairing_proof_fp1(proof))
        registry.register(handle)
        rotated = renew_pairing_session(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            proof=proof,
            expires_at=_EXPIRES_AT,
            now_ns=_NOW_NS,
            ws_registry=registry,
        )
        assert is_ok(rotated), rotated
        assert rotated.value.pairing_proof != proof
        assert rotated.value.pairing_record_id != record_id
        assert handle.closed is True
        old = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{proof}",
            origin=_ORIGIN,
            now_ns=_NOW_NS,
        )
        assert is_refusal(old)
        new = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{rotated.value.pairing_proof}",
            origin=_ORIGIN,
            now_ns=_NOW_NS,
        )
        assert is_ok(new)
        assert new.value.pairing_record_id == rotated.value.pairing_record_id
    finally:
        journal.close()
        substrate.close()


def test_page_machine_principal_is_policy_rejection(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-6-machine")
    try:
        _record_id, proof = _issue(journal, substrate.sqlite)
        producers = LiveProducerRegistry()
        refused = recover_pairing_connection(
            substrate.sqlite,
            origin=_ORIGIN,
            stored_proof=proof,
            live_producers=producers,
            connection_token="tab-machine",
            now_ns=_NOW_NS,
            principal_class="machine",
        )
        assert is_refusal(refused)
        assert refused.category is RefusalCategory.POLICY_REJECTION
        assert refused.context["field"] == "principal_class"
    finally:
        journal.close()
        substrate.close()


def test_daemon_origin_and_8765_chrome_refused(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-6-8765")
    try:
        _record_id, proof = _issue(journal, substrate.sqlite)
        producers = LiveProducerRegistry()
        refused = recover_pairing_connection(
            substrate.sqlite,
            origin=_DAEMON_ORIGIN,
            stored_proof=proof,
            live_producers=producers,
            connection_token="tab-8765",
            now_ns=_NOW_NS,
        )
        assert is_refusal(refused)
        assert refused.context["field"] == "origin"
        assert refused.context["daemon_port"] == 8765
    finally:
        journal.close()
        substrate.close()


def test_authenticated_cors_is_exact_paired_origin(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-6-cors")
    try:
        _record_id, _proof = _issue(journal, substrate.sqlite)
        start = cors_options_response(_options("/pair/start", _OTHER_ORIGIN))
        assert is_ok(start)
        start_headers = {key.casefold(): value for key, value in start.value.headers.items()}
        assert start_headers["access-control-allow-origin"] == _OTHER_ORIGIN
        assert start_headers["access-control-allow-origin"] != "*"
        assert start_headers["access-control-allow-credentials"] == "false"
        assert "authorization" in start_headers["access-control-allow-headers"].casefold()

        paired = cors_options_response(
            _options("/pair/renew", _ORIGIN),
            sqlite=substrate.sqlite,
            now_ns=_NOW_NS,
        )
        assert is_ok(paired)
        paired_headers = {key.casefold(): value for key, value in paired.value.headers.items()}
        assert paired_headers["access-control-allow-origin"] == _ORIGIN
        assert paired_headers["access-control-allow-origin"] != "*"
        assert paired_headers["access-control-allow-credentials"] == "false"
        assert "authorization" in paired_headers["access-control-allow-headers"].casefold()

        other = cors_options_response(
            _options("/pair/renew", _OTHER_ORIGIN),
            sqlite=substrate.sqlite,
            now_ns=_NOW_NS,
        )
        assert is_ok(other)
        other_headers = {key.casefold(): value for key, value in other.value.headers.items()}
        assert "access-control-allow-origin" not in other_headers
        assert other_headers["access-control-allow-credentials"] == "false"

        daemon = cors_options_response(_options("/pair/start", _DAEMON_ORIGIN))
        assert is_refusal(daemon)
        assert daemon.context["retarget"] is False

        assert cors_allow_origin(path="/pair/start", request_origin=_ORIGIN) == _ORIGIN
        assert cors_allow_origin(path="/pair/renew", request_origin=_ORIGIN) is None
        assert (
            cors_allow_origin(
                path="/pair/renew",
                request_origin=_ORIGIN,
                paired_origin=_ORIGIN,
            )
            == _ORIGIN
        )
        assert (
            cors_allow_origin(
                path="/pair/renew",
                request_origin=_OTHER_ORIGIN,
                paired_origin=_ORIGIN,
            )
            is None
        )
        assert cors_allow_origin(path="/pair/renew", request_origin="*") is None
        assert refuse_cors_preflight_retarget().context["retarget"] is False

        with pytest.raises(ValueError, match="never be \\*"):
            PairHttpResponse(
                status=204,
                headers={"Access-Control-Allow-Origin": "*"},
                body=b"",
            )
        with pytest.raises(ValueError, match="must be false"):
            PairHttpResponse(
                status=204,
                headers={
                    "Access-Control-Allow-Origin": _ORIGIN,
                    "Access-Control-Allow-Credentials": "true",
                },
                body=b"",
            )
    finally:
        journal.close()
        substrate.close()


def test_bearer_header_round_trip_same_proof(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-6-hdr")
    try:
        _record_id, proof = _issue(journal, substrate.sqlite)
        header = format_pairing_authorization(proof)
        assert is_ok(header)
        assert header.value.startswith("Bearer pairing:")
        assert proof in header.value
    finally:
        journal.close()
        substrate.close()
