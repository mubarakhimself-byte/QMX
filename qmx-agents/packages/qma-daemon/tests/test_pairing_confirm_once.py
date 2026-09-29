"""Story 68.4 — Origin never issues a proof; confirm-once or authenticated renew."""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from typing import cast

from qma.core.refusals.variants import CredentialOutOfScope
from qma.daemon import AuthoritativeJournal, PersistenceSubstrate
from qma.daemon.host_control import host_control_call
from qma.daemon.http_pair import (
    PairHttpDeps,
    PairHttpRequest,
    handle_pair_confirm,
    handle_pair_http,
    handle_pair_renew,
    handle_pair_start,
    require_pair_renew_bearer,
)
from qma.daemon.journal.authoritative import JournalAppendReceipt
from qma.daemon.journal.variables import (
    expires_at_from_pairing_ttl,
    pairing_ttl_duration_ns,
    refuse_pair_issue_without_ttl,
)
from qma.daemon.pairing import (
    CONFIRM_ONCE_COUNT,
    LOCAL_OPERATOR_BOOTSTRAP_IS_THIS_STORY,
    ORIGIN_ONLY_AUTO_APPROVE,
    PAIRING_HTTP_EXISTED_AT_INSPECT_SHA,
    PAIRING_SESSION_EVENT_ISSUED,
    QMB_HOST_PAIR_EXISTED_AT_INSPECT_SHA,
    IssuedPairingProof,
    PairingWsHandle,
    PairingWsRegistry,
    authenticate_ws_pairing_upgrade,
    claim_local_operator_bootstrap_is_this_story,
    claim_pair_http_existed_at_inspect_sha,
    claim_qmb_host_pair_existed_at_inspect_sha,
    confirm_pairing_pending_by_code,
    confirm_pairing_session_once,
    journal_blob_contains_secret,
    live_pairing_sessions_for_origin,
    load_pairing_pending,
    match_pairing_session_by_proof,
    pairing_status_record_ids,
    renew_pairing_session,
    start_pairing_pending,
)
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.auth import (
    format_pairing_authorization,
    is_pairing_record_id,
    is_rfc6455_token,
)
from qmf.core import DataDrivenClock, Instant, Result, is_ok, is_refusal
from qmf.core.refusal import RefusalCategory
from qmf.data.store.refusals import storage_failure

_ORIGIN = "http://127.0.0.1:5173"
_FIXTURE_TTL = "PT15M"
_NOW_NS = 1_710_000_000_000_000_000


def _test_clock(*, boot: str = "boot-68-4", n: int = 128) -> DataDrivenClock:
    walls = tuple(Instant(value_ns=_NOW_NS + i) for i in range(n))
    monos = tuple(i * 1_000 for i in range(n))
    return DataDrivenClock(boot_epoch_id=boot, wall_instants=walls, monotonic_ns=monos)


def _open_journal(
    tmp_path: Path, *, boot: str = "boot-68-4"
) -> tuple[PersistenceSubstrate, AuthoritativeJournal]:
    substrate_result = PersistenceSubstrate.open(tmp_path, machine="test-host", boot_epoch_id=boot)
    assert is_ok(substrate_result), substrate_result
    substrate = substrate_result.value
    journal_result = AuthoritativeJournal.bind(substrate, clock=_test_clock(boot=boot))
    assert is_ok(journal_result), journal_result
    return substrate, journal_result.value


def _seed_configs(tmp_path: Path) -> dict[str, dict[str, object]]:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    return research_corpus_plugin_load_config(seed)


def _expires(now_ns: int = _NOW_NS) -> int:
    expires = expires_at_from_pairing_ttl(now_ns=now_ns, ttl=_FIXTURE_TTL)
    assert is_ok(expires), expires
    return expires.value


def _deps(
    journal: AuthoritativeJournal,
    sqlite: SingleSqliteWriter,
    *,
    ttl: object = _FIXTURE_TTL,
    now_ns: int = _NOW_NS,
    ws_registry: PairingWsRegistry | None = None,
) -> PairHttpDeps:
    return PairHttpDeps(
        journal=journal,
        sqlite=sqlite,
        ttl=ttl,
        now_ns=now_ns,
        ws_registry=ws_registry,
    )


def _request(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes = b"",
) -> PairHttpRequest:
    built = PairHttpRequest.try_create(method=method, path=path, headers=headers, body=body)
    assert is_ok(built), built
    return built.value


def _json_body(response: object) -> dict[str, object]:
    body = getattr(response, "body", b"")
    assert isinstance(body, bytes)
    parsed: object = json.loads(body.decode("utf-8"))
    assert isinstance(parsed, dict)
    return cast("dict[str, object]", parsed)


def test_honesty_origin_never_issues_and_inspect_sha() -> None:
    assert ORIGIN_ONLY_AUTO_APPROVE is False
    assert CONFIRM_ONCE_COUNT == 1
    assert PAIRING_HTTP_EXISTED_AT_INSPECT_SHA is False
    assert QMB_HOST_PAIR_EXISTED_AT_INSPECT_SHA is False
    assert LOCAL_OPERATOR_BOOTSTRAP_IS_THIS_STORY is False
    assert is_refusal(claim_pair_http_existed_at_inspect_sha(True))
    assert is_ok(claim_pair_http_existed_at_inspect_sha(False))
    assert is_refusal(claim_qmb_host_pair_existed_at_inspect_sha(True))
    assert is_ok(claim_qmb_host_pair_existed_at_inspect_sha(False))
    assert is_refusal(claim_local_operator_bootstrap_is_this_story(True))
    assert is_ok(claim_local_operator_bootstrap_is_this_story(False))


def test_operator_ttl_fixture_is_not_product_law() -> None:
    span = pairing_ttl_duration_ns(_FIXTURE_TTL)
    assert is_ok(span)
    assert span.value == 15 * 60 * 1_000_000_000
    assert is_refusal(refuse_pair_issue_without_ttl(None))
    assert is_refusal(refuse_pair_issue_without_ttl(""))
    assert is_ok(refuse_pair_issue_without_ttl(_FIXTURE_TTL))


def test_origin_only_confirm_is_policy_rejection(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        pending = start_pairing_pending(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_expires(),
        )
        assert is_ok(pending)
        refused = confirm_pairing_session_once(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            pending_id=pending.value.pairing_record_id,
            expires_at=_expires(),
            now_ns=_NOW_NS,
        )
        assert is_refusal(refused)
        assert refused.category is RefusalCategory.POLICY_REJECTION
        assert refused.context.get("origin_only") is True
        assert refused.context.get("already_issued") is not True
        sessions = live_pairing_sessions_for_origin(
            substrate.sqlite, origin=_ORIGIN, now_ns=_NOW_NS
        )
        assert sessions == ()
        ws = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=("qmx.ct40.v1", "qmx.pair.not-a-proof"),
            origin=_ORIGIN,
            now_ns=_NOW_NS,
        )
        assert is_refusal(ws)
        assert ws.category is RefusalCategory.POLICY_REJECTION
    finally:
        journal.close()
        substrate.close()


def test_path1_confirm_once_returns_proof_json(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        deps = _deps(journal, substrate.sqlite)
        started = handle_pair_start(
            _request("POST", "/pair/start", headers={"Origin": _ORIGIN}),
            deps,
        )
        assert is_ok(started), started
        body = _json_body(started.value)
        pending_id = body["pairing_record_id"]
        code = body["pending_code"]
        assert isinstance(pending_id, str)
        assert isinstance(code, str)
        host = confirm_pairing_pending_by_code(
            journal=journal,
            sqlite=substrate.sqlite,
            code=code,
            now_ns=_NOW_NS,
        )
        assert is_ok(host), host
        assert host.value.confirmed_at > 0
        assert host.value.consumed is False
        rows = journal.read_all()
        assert is_ok(rows)
        assert journal_blob_contains_secret(journal, code) is False
        confirmed = handle_pair_confirm(
            _request(
                "POST",
                "/pair/confirm",
                headers={"Origin": _ORIGIN},
                body=json.dumps({"pending_id": pending_id}).encode("utf-8"),
            ),
            deps,
        )
        assert is_ok(confirmed), confirmed
        proof_body = _json_body(confirmed.value)
        assert set(proof_body) == {"pairing_record_id", "pairing_proof", "expires_at"}
        proof = proof_body["pairing_proof"]
        assert isinstance(proof, str)
        assert is_rfc6455_token(proof)
        assert not is_pairing_record_id(proof)
        assert journal_blob_contains_secret(journal, proof) is False
        live = load_pairing_pending(substrate.sqlite, pending_id)
        assert live is not None
        assert live.consumed is True
        status = pairing_status_record_ids(substrate.sqlite)
        blob = json.dumps(status, ensure_ascii=True)
        assert proof not in blob
        assert code not in blob
        second = handle_pair_confirm(
            _request(
                "POST",
                "/pair/confirm",
                headers={"Origin": _ORIGIN},
                body=json.dumps({"pending_id": pending_id}).encode("utf-8"),
            ),
            deps,
        )
        assert is_refusal(second)
        assert second.category is RefusalCategory.POLICY_REJECTION
        assert second.context.get("already_issued") is True
        assert second.context.get("field") == "already_issued"
    finally:
        journal.close()
        substrate.close()


def test_concurrent_confirm_loser_is_already_issued(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        pending = start_pairing_pending(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_expires(),
        )
        assert is_ok(pending)
        host = confirm_pairing_pending_by_code(
            journal=journal,
            sqlite=substrate.sqlite,
            code=pending.value.pending_code,
            now_ns=_NOW_NS,
        )
        assert is_ok(host)
        results: list[Result[IssuedPairingProof]] = []
        barrier = threading.Barrier(2)

        def _confirm() -> None:
            barrier.wait()
            results.append(
                confirm_pairing_session_once(
                    journal=journal,
                    sqlite=substrate.sqlite,
                    origin=_ORIGIN,
                    pending_id=pending.value.pairing_record_id,
                    expires_at=_expires(),
                    now_ns=_NOW_NS,
                )
            )

        first = threading.Thread(target=_confirm)
        second = threading.Thread(target=_confirm)
        first.start()
        second.start()
        first.join()
        second.join()
        oks = [item for item in results if is_ok(item)]
        refusals = [item for item in results if is_refusal(item)]
        assert len(oks) == 1
        assert len(refusals) == 1
        loser = refusals[0]
        assert is_refusal(loser)
        assert loser.context.get("already_issued") is True
    finally:
        journal.close()
        substrate.close()


def test_renew_rotates_and_closes_old_ws(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        pending = start_pairing_pending(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_expires(),
        )
        assert is_ok(pending)
        host = confirm_pairing_pending_by_code(
            journal=journal,
            sqlite=substrate.sqlite,
            code=pending.value.pending_code,
            now_ns=_NOW_NS,
        )
        assert is_ok(host)
        issued = confirm_pairing_session_once(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            pending_id=pending.value.pairing_record_id,
            expires_at=_expires(),
            now_ns=_NOW_NS,
        )
        assert is_ok(issued)
        old_proof = issued.value.pairing_proof
        registry = PairingWsRegistry()
        handle = PairingWsHandle(proof_fp1=issued.value.proof_fp1)
        registry.register(handle)
        auth = format_pairing_authorization(old_proof)
        assert is_ok(auth)
        deps = _deps(journal, substrate.sqlite, ws_registry=registry)
        renewed = handle_pair_renew(
            _request(
                "POST",
                "/pair/renew",
                headers={"Origin": _ORIGIN, "Authorization": auth.value},
            ),
            deps,
        )
        assert is_ok(renewed), renewed
        new_body = _json_body(renewed.value)
        new_proof = new_body["pairing_proof"]
        assert new_proof != old_proof
        assert new_body["pairing_record_id"] != issued.value.pairing_record_id
        assert handle.closed is True
        live = live_pairing_sessions_for_origin(substrate.sqlite, origin=_ORIGIN, now_ns=_NOW_NS)
        assert len(live) == 1
        assert live[0].pairing_record_id == new_body["pairing_record_id"]
        old = match_pairing_session_by_proof(
            substrate.sqlite, origin=_ORIGIN, proof=old_proof, now_ns=_NOW_NS
        )
        assert is_refusal(old)
        ws_old = authenticate_ws_pairing_upgrade(
            substrate.sqlite,
            offered_subprotocols=("qmx.ct40.v1", f"qmx.pair.{old_proof}"),
            origin=_ORIGIN,
            now_ns=_NOW_NS,
        )
        assert is_refusal(ws_old)
        missing = require_pair_renew_bearer(
            _request("POST", "/pair/renew", headers={"Origin": _ORIGIN})
        )
        assert is_refusal(missing)
        unauth = handle_pair_http(
            _request("POST", "/pair/renew", headers={"Origin": _ORIGIN}),
            deps,
        )
        assert is_refusal(unauth)
    finally:
        journal.close()
        substrate.close()


def test_lost_confirm_proof_is_unrecoverable(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        pending = start_pairing_pending(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_expires(),
        )
        assert is_ok(pending)
        host = confirm_pairing_pending_by_code(
            journal=journal,
            sqlite=substrate.sqlite,
            code=pending.value.pending_code,
            now_ns=_NOW_NS,
        )
        assert is_ok(host)
        issued = confirm_pairing_session_once(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            pending_id=pending.value.pairing_record_id,
            expires_at=_expires(),
            now_ns=_NOW_NS,
        )
        assert is_ok(issued)
        proof = issued.value.pairing_proof
        rows = journal.read_all()
        assert is_ok(rows)
        blob = json.dumps(rows.value, ensure_ascii=True)
        assert proof not in blob
        assert pending.value.pending_code not in blob
        status = pairing_status_record_ids(substrate.sqlite)
        status_blob = json.dumps(status, ensure_ascii=True)
        assert proof not in status_blob
        retry = confirm_pairing_session_once(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            pending_id=pending.value.pairing_record_id,
            expires_at=_expires(),
            now_ns=_NOW_NS,
        )
        assert is_refusal(retry)
        assert retry.context.get("already_issued") is True
    finally:
        journal.close()
        substrate.close()


def test_missing_ttl_refuses_start_and_confirm_issue(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        deps = _deps(journal, substrate.sqlite, ttl=None)
        started = handle_pair_start(
            _request("POST", "/pair/start", headers={"Origin": _ORIGIN}),
            deps,
        )
        assert is_refusal(started)
        assert started.category is RefusalCategory.POLICY_REJECTION
        assert "pairing.session_ttl" in str(started.context.get("reason", ""))
        pending = start_pairing_pending(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_expires(),
        )
        assert is_ok(pending)
        host = confirm_pairing_pending_by_code(
            journal=journal,
            sqlite=substrate.sqlite,
            code=pending.value.pending_code,
            now_ns=_NOW_NS,
        )
        assert is_ok(host)
        confirm = handle_pair_confirm(
            _request(
                "POST",
                "/pair/confirm",
                headers={"Origin": _ORIGIN},
                body=json.dumps({"pending_id": pending.value.pairing_record_id}).encode("utf-8"),
            ),
            deps,
        )
        assert is_refusal(confirm)
        assert confirm.category is RefusalCategory.POLICY_REJECTION
    finally:
        journal.close()
        substrate.close()


def test_running_daemon_pair_sets_confirmed_at_without_proof(tmp_path: Path) -> None:
    async def _run() -> None:
        composed = DaemonProcess.compose(
            tmp_path,
            machine="test-host",
            boot_epoch_id="boot-68-4-host",
            bind_port=0,
            plugin_load_configs=_seed_configs(tmp_path),
        )
        assert is_ok(composed), composed
        process = composed.value
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            stamps = process.journal.stamp_durable()
            assert is_ok(stamps), stamps
            expires = expires_at_from_pairing_ttl(
                now_ns=stamps.value.recorded_at,
                ttl=_FIXTURE_TTL,
            )
            assert is_ok(expires), expires
            pending = start_pairing_pending(
                journal=process.journal,
                sqlite=process.sqlite,
                origin=_ORIGIN,
                expires_at=expires.value,
            )
            assert is_ok(pending)
            paired = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "pair",
                fields={"code": pending.value.pending_code},
            )
            assert is_ok(paired), paired
            payload = paired.value
            assert payload["ok"] is True
            confirmed = payload["paired"]
            assert isinstance(confirmed, dict)
            assert confirmed["confirmed"] is True
            assert confirmed["pairing_record_id"] == pending.value.pairing_record_id
            assert "pairing_proof" not in confirmed
            live = load_pairing_pending(process.sqlite, pending.value.pairing_record_id)
            assert live is not None
            assert live.confirmed_at > 0
            missing = await asyncio.to_thread(host_control_call, tmp_path, "pair")
            assert is_ok(missing)
            assert missing.value["ok"] is False
            forged = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "pair",
                fields={"code": "cred://operator/login"},
            )
            assert is_ok(forged)
            forged_payload = forged.value
            assert forged_payload["ok"] is False
            refusal = forged_payload.get("refusal")
            assert isinstance(refusal, dict)
            body = cast("dict[str, object]", refusal)
            context_raw: object = body.get("context")
            assert isinstance(context_raw, dict)
            context = cast("dict[str, object]", context_raw)
            assert context.get("variant") == CredentialOutOfScope.VARIANT
            assert str(context.get("credential_ref", "")).startswith("cred://")
        finally:
            if not process.is_closed:
                await process.aclose()

    asyncio.run(_run())


def _issued_session(
    journal: AuthoritativeJournal, sqlite: SingleSqliteWriter
) -> IssuedPairingProof:
    pending = start_pairing_pending(
        journal=journal,
        sqlite=sqlite,
        origin=_ORIGIN,
        expires_at=_expires(),
    )
    assert is_ok(pending)
    host = confirm_pairing_pending_by_code(
        journal=journal,
        sqlite=sqlite,
        code=pending.value.pending_code,
        now_ns=_NOW_NS,
    )
    assert is_ok(host)
    issued = confirm_pairing_session_once(
        journal=journal,
        sqlite=sqlite,
        origin=_ORIGIN,
        pending_id=pending.value.pairing_record_id,
        expires_at=_expires(),
        now_ns=_NOW_NS,
    )
    assert is_ok(issued)
    return issued.value


def test_renew_failed_second_append_does_not_leave_two_live_proofs(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-4-renew-fail")
    try:
        issued = _issued_session(journal, substrate.sqlite)
        old_proof = issued.pairing_proof
        real_append = journal.append_event

        def _fail_issued(
            event: object,
            *args: object,
            **kwargs: object,
        ) -> Result[JournalAppendReceipt]:
            if event == PAIRING_SESSION_EVENT_ISSUED:
                return storage_failure(
                    "injected second-append failure",
                    context={"field": "journal", "event": event},
                )
            return real_append(event, *args, **kwargs)

        journal.append_event = _fail_issued  # type: ignore[method-assign]
        rotated = renew_pairing_session(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            proof=old_proof,
            expires_at=_expires(),
            now_ns=_NOW_NS,
        )
        assert is_refusal(rotated)
        live = live_pairing_sessions_for_origin(substrate.sqlite, origin=_ORIGIN, now_ns=_NOW_NS)
        assert live == ()
        old = match_pairing_session_by_proof(
            substrate.sqlite, origin=_ORIGIN, proof=old_proof, now_ns=_NOW_NS
        )
        assert is_refusal(old)
    finally:
        journal.close()
        substrate.close()


def test_renew_lock_serializes_and_does_not_issue_two_live_proofs(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-68-4-renew-lock")
    try:
        issued = _issued_session(journal, substrate.sqlite)
        old_proof = issued.pairing_proof
        results: list[Result[IssuedPairingProof]] = []
        barrier = threading.Barrier(2)

        def _worker() -> None:
            barrier.wait()
            results.append(
                renew_pairing_session(
                    journal=journal,
                    sqlite=substrate.sqlite,
                    origin=_ORIGIN,
                    proof=old_proof,
                    expires_at=_expires(),
                    now_ns=_NOW_NS,
                )
            )

        first = threading.Thread(target=_worker)
        second = threading.Thread(target=_worker)
        first.start()
        second.start()
        first.join()
        second.join()
        oks = [item for item in results if is_ok(item)]
        refusals = [item for item in results if is_refusal(item)]
        assert len(oks) == 1
        assert len(refusals) == 1
        live = live_pairing_sessions_for_origin(substrate.sqlite, origin=_ORIGIN, now_ns=_NOW_NS)
        assert len(live) == 1
        assert live[0].pairing_record_id == oks[0].value.pairing_record_id
        old = match_pairing_session_by_proof(
            substrate.sqlite, origin=_ORIGIN, proof=old_proof, now_ns=_NOW_NS
        )
        assert is_refusal(old)
    finally:
        journal.close()
        substrate.close()
