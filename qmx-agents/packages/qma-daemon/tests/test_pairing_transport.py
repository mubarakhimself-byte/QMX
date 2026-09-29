"""Story 68.3 — HTTP Bearer pairing:<proof> plus WS subprotocols."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from qma.daemon import AuthoritativeJournal, PersistenceSubstrate
from qma.daemon.pairing import (
    COOKIE_LOGIN_SHIPPED,
    CT40_WS_SUBPROTOCOL,
    HANDLE_CLIENT_DISCARDED_BYTES_AT_INSPECT_SHA,
    LOCALSTORAGE_PROOF_SHIPPED,
    PAIRING_BEARER_TRANSPORT_EXISTED_AT_INSPECT_SHA,
    PAIRING_PROOF_MAY_BIND_MULTIPLE_CONNECTIONS,
    PAIRING_WS_SUBPROTOCOLS_EXISTED_AT_INSPECT_SHA,
    WEBSOCKETS_IMPORTS_AT_INSPECT_SHA,
    PairingWsUpgrade,
    authenticate_http_pairing_bearer,
    authenticate_ws_pairing_upgrade,
    claim_cookie_login_or_localstorage_proof_shipped,
    claim_pairing_transports_existed_at_inspect_sha,
    issue_pairing_session,
    mint_pairing_proof,
    redact_pairing_access_log,
)
from qma.wire import (
    PAIRING_HTTP_AUTHORIZATION_PREFIX,
    PAIRING_RECORD_ID_PREFIX,
    PAIRING_WS_SUBPROTOCOL_PREFIX,
    format_pairing_authorization,
    format_pairing_websocket_subprotocols,
)
from qmf.core import DataDrivenClock, Instant, is_ok, is_refusal
from qmf.core.refusal import RefusalCategory

_ORIGIN = "http://127.0.0.1:5173"
_OTHER_ORIGIN = "http://127.0.0.1:9999"
_EXPIRES_AT = 1_800_000_000_000_000_000
_NOW_NS = 1_710_000_000_000_000_010


def _test_clock(*, boot: str = "boot-68-3", n: int = 64) -> DataDrivenClock:
    base = 1_710_000_000_000_000_000
    walls = tuple(Instant(value_ns=base + i) for i in range(n))
    monos = tuple(i * 1_000 for i in range(n))
    return DataDrivenClock(boot_epoch_id=boot, wall_instants=walls, monotonic_ns=monos)


def _open_journal(
    tmp_path: Path, *, boot: str = "boot-68-3"
) -> tuple[PersistenceSubstrate, AuthoritativeJournal]:
    substrate_result = PersistenceSubstrate.open(tmp_path, machine="test-host", boot_epoch_id=boot)
    assert is_ok(substrate_result), substrate_result
    substrate = substrate_result.value
    journal_result = AuthoritativeJournal.bind(substrate, clock=_test_clock(boot=boot))
    assert is_ok(journal_result), journal_result
    return substrate, journal_result.value


def test_inspect_sha_and_forbidden_proof_homes() -> None:
    assert PAIRING_BEARER_TRANSPORT_EXISTED_AT_INSPECT_SHA is False
    assert PAIRING_WS_SUBPROTOCOLS_EXISTED_AT_INSPECT_SHA is False
    assert WEBSOCKETS_IMPORTS_AT_INSPECT_SHA == 0
    assert HANDLE_CLIENT_DISCARDED_BYTES_AT_INSPECT_SHA is True
    assert COOKIE_LOGIN_SHIPPED is False
    assert LOCALSTORAGE_PROOF_SHIPPED is False
    assert is_refusal(claim_pairing_transports_existed_at_inspect_sha(True))
    assert is_ok(claim_pairing_transports_existed_at_inspect_sha(False))
    assert is_refusal(claim_cookie_login_or_localstorage_proof_shipped(True))
    assert is_ok(claim_cookie_login_or_localstorage_proof_shipped(False))
    assert PAIRING_PROOF_MAY_BIND_MULTIPLE_CONNECTIONS is True


def test_http_bearer_plus_origin_and_refusals(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        issued = issue_pairing_session(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_EXPIRES_AT,
        )
        assert is_ok(issued)
        proof = issued.value.pairing_proof
        record_id = issued.value.pairing_record_id
        header = f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{proof}"

        authed = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=header,
            origin=_ORIGIN,
            now_ns=_NOW_NS,
        )
        assert is_ok(authed)
        assert authed.value.pairing_record_id == record_id
        assert authed.value.credential_ref is None

        again = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=header,
            origin=_ORIGIN,
            now_ns=_NOW_NS,
            cookie=f"pairing_proof={proof}",
        )
        assert is_ok(again)
        assert again.value.pairing_record_id == record_id

        cookie_only = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization="",
            origin=_ORIGIN,
            cookie=f"pairing_proof={proof}",
        )
        assert is_refusal(cookie_only)
        assert cookie_only.category is RefusalCategory.POLICY_REJECTION
        assert cookie_only.context["cookie_is_proof"] is False

        as_id = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{record_id}",
            origin=_ORIGIN,
        )
        assert is_refusal(as_id)

        cred = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization="Bearer cred://models/openai",
            origin=_ORIGIN,
        )
        assert is_refusal(cred)
        assert "cred://" in str(cred.context["reason"])

        guessed = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{mint_pairing_proof()}",
            origin=_ORIGIN,
        )
        assert is_refusal(guessed)
        assert guessed.context["field"] == "pairing_proof"

        other = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=header,
            origin=_OTHER_ORIGIN,
        )
        assert is_refusal(other)
        assert other.context["field"] == "origin"

        expired = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=header,
            origin=_ORIGIN,
            now_ns=_EXPIRES_AT + 1,
        )
        assert is_refusal(expired)
        assert expired.context["field"] == "pairing_proof"

        in_query = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=header,
            origin=_ORIGIN,
            query={"pairing_proof": proof},
        )
        assert is_refusal(in_query)
    finally:
        journal.close()
        substrate.close()


def test_ws_upgrade_requires_ct40_and_pair_proof(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-3-ws")
    try:
        issued = issue_pairing_session(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_EXPIRES_AT,
        )
        assert is_ok(issued)
        proof = issued.value.pairing_proof
        record_id = issued.value.pairing_record_id
        offered = format_pairing_websocket_subprotocols(proof)
        assert is_ok(offered)

        upgrade = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=list(offered.value),
            origin=_ORIGIN,
            now_ns=_NOW_NS,
            cookie=f"pairing_proof={proof}",
        )
        assert is_ok(upgrade)
        admitted = upgrade.value
        assert isinstance(admitted, PairingWsUpgrade)
        assert admitted.echoed_subprotocol == CT40_WS_SUBPROTOCOL
        assert admitted.pairing_record_id == record_id
        assert admitted.origin == _ORIGIN
        assert admitted.sends_ct40_bytes is False
        assert admitted.initializes is False
        assert admitted.multiple_connections_allowed is True
        assert admitted.session.pairing_record_id == record_id
        assert admitted.session.credential_ref is None

        second = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=f"{CT40_WS_SUBPROTOCOL}, {PAIRING_WS_SUBPROTOCOL_PREFIX}{proof}",
            origin=_ORIGIN,
            now_ns=_NOW_NS,
        )
        assert is_ok(second)
        assert second.value.pairing_record_id == record_id

        missing = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=[CT40_WS_SUBPROTOCOL],
            origin=_ORIGIN,
        )
        assert is_refusal(missing)

        malformed = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=[CT40_WS_SUBPROTOCOL, "qmx.pair."],
            origin=_ORIGIN,
        )
        assert is_refusal(malformed)

        as_id = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=[
                CT40_WS_SUBPROTOCOL,
                f"{PAIRING_WS_SUBPROTOCOL_PREFIX}{record_id}",
            ],
            origin=_ORIGIN,
        )
        assert is_refusal(as_id)
        assert "pairing:<id>" in str(as_id.context["reason"])

        literal_id = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=[CT40_WS_SUBPROTOCOL, f"pairing:{record_id}"],
            origin=_ORIGIN,
        )
        assert is_refusal(literal_id)

        guessed = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=[
                CT40_WS_SUBPROTOCOL,
                f"{PAIRING_WS_SUBPROTOCOL_PREFIX}{mint_pairing_proof()}",
            ],
            origin=_ORIGIN,
        )
        assert is_refusal(guessed)

        other = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=list(offered.value),
            origin=_OTHER_ORIGIN,
        )
        assert is_refusal(other)
        assert other.context["field"] == "origin"

        expired = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=list(offered.value),
            origin=_ORIGIN,
            now_ns=_EXPIRES_AT + 1,
        )
        assert is_refusal(expired)

        in_query = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=list(offered.value),
            origin=_ORIGIN,
            query=f"qmx.pair.{proof}",
        )
        assert is_refusal(in_query)
    finally:
        journal.close()
        substrate.close()


def test_access_logs_redact_qmx_pair_values(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-3-log")
    try:
        issued = issue_pairing_session(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_EXPIRES_AT,
        )
        assert is_ok(issued)
        proof = issued.value.pairing_proof
        record_id = issued.value.pairing_record_id
        header = format_pairing_authorization(proof)
        assert is_ok(header)
        logged = cast(
            "dict[str, object]",
            redact_pairing_access_log(
                {
                    "authorization": header.value,
                    "pairing_record_id": record_id,
                    "sec-websocket-protocol": (
                        f"{CT40_WS_SUBPROTOCOL}, {PAIRING_WS_SUBPROTOCOL_PREFIX}{proof}"
                    ),
                    "origin": _ORIGIN,
                }
            ),
        )
        assert logged["pairing_record_id"] == record_id
        assert logged["authorization"] == "[redacted]"
        protocol = logged["sec-websocket-protocol"]
        assert isinstance(protocol, str)
        assert CT40_WS_SUBPROTOCOL in protocol
        assert proof not in protocol
        assert f"{PAIRING_WS_SUBPROTOCOL_PREFIX}{proof}" not in protocol
        assert "qmx.pair.[redacted]" in protocol
        assert PAIRING_RECORD_ID_PREFIX in record_id
    finally:
        journal.close()
        substrate.close()
