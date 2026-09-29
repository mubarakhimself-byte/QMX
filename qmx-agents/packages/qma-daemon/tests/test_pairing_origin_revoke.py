"""Story 68.5 — origin-revoke is a journal_seq barrier; session revoke is one row."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import cast

from qma.daemon import AuthoritativeJournal, PersistenceSubstrate
from qma.daemon.host_control import host_control_call
from qma.daemon.http_pair import (
    PairHttpDeps,
    PairHttpRequest,
    handle_pair_confirm,
    handle_pair_renew,
    handle_pair_start,
)
from qma.daemon.journal.variables import expires_at_from_pairing_ttl
from qma.daemon.pairing import (
    ORIGIN_REVOKE_MINTS_TTL,
    ORIGIN_REVOKE_USES_WALL_CLOCK,
    PAIRING_ORIGIN_REVOKE_EXISTED_AT_INSPECT_SHA,
    PAIRING_ORIGIN_REVOKED_EVENT,
    QMB_HOST_PAIR_REVOKE_EXISTED_AT_INSPECT_SHA,
    PairingWsHandle,
    PairingWsRegistry,
    claim_qmb_host_pair_revoke_existed_at_inspect_sha,
    confirm_pairing_pending_by_code,
    confirm_pairing_session_once,
    fold_origin_barriers_from_journal,
    fold_pairing_sessions_from_journal,
    journal_blob_contains_secret,
    live_pairing_sessions_for_origin,
    load_origin_barrier_seq,
    load_pairing_pending,
    load_pairing_session,
    match_pairing_session_by_proof,
    origin_revoke_pairing,
    restore_pairing_projections,
    session_revoke_pairing,
    start_pairing_pending,
)
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.auth import format_pairing_authorization
from qmf.core import DataDrivenClock, Instant, is_ok, is_refusal
from qmf.core.refusal import RefusalCategory

_ORIGIN = "http://127.0.0.1:5173"
_OTHER_ORIGIN = "http://127.0.0.1:4173"
_FIXTURE_TTL = "PT15M"
_NOW_NS = 1_710_000_000_000_000_000


def _test_clock(*, boot: str = "boot-68-5", n: int = 256) -> DataDrivenClock:
    walls = tuple(Instant(value_ns=_NOW_NS + i) for i in range(n))
    monos = tuple(i * 1_000 for i in range(n))
    return DataDrivenClock(boot_epoch_id=boot, wall_instants=walls, monotonic_ns=monos)


def _open_journal(
    tmp_path: Path, *, boot: str = "boot-68-5"
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
    ws_registry: PairingWsRegistry | None = None,
) -> PairHttpDeps:
    return PairHttpDeps(
        journal=journal,
        sqlite=sqlite,
        ttl=_FIXTURE_TTL,
        now_ns=_NOW_NS,
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


def _bearer(proof: str) -> str:
    auth = format_pairing_authorization(proof)
    assert is_ok(auth), auth
    return auth.value


def _register_ws(sqlite: SingleSqliteWriter, record_id: str) -> PairingWsHandle:
    live = load_pairing_session(sqlite, record_id)
    assert live is not None
    return PairingWsHandle(proof_fp1=live.proof_fp1)


def _issue_proof(
    journal: AuthoritativeJournal,
    sqlite: SingleSqliteWriter,
    *,
    origin: str = _ORIGIN,
) -> tuple[str, str, str]:
    pending = start_pairing_pending(
        journal=journal,
        sqlite=sqlite,
        origin=origin,
        expires_at=_expires(),
    )
    assert is_ok(pending), pending
    host = confirm_pairing_pending_by_code(
        journal=journal,
        sqlite=sqlite,
        code=pending.value.pending_code,
        now_ns=_NOW_NS,
    )
    assert is_ok(host), host
    issued = confirm_pairing_session_once(
        journal=journal,
        sqlite=sqlite,
        origin=origin,
        pending_id=pending.value.pairing_record_id,
        expires_at=_expires(),
        now_ns=_NOW_NS,
    )
    assert is_ok(issued), issued
    return (
        issued.value.pairing_record_id,
        issued.value.pairing_proof,
        pending.value.pairing_record_id,
    )


def test_honesty_origin_revoke_absent_and_not_ttl() -> None:
    assert ORIGIN_REVOKE_USES_WALL_CLOCK is False
    assert ORIGIN_REVOKE_MINTS_TTL is False
    assert PAIRING_ORIGIN_REVOKE_EXISTED_AT_INSPECT_SHA is False
    assert QMB_HOST_PAIR_REVOKE_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_qmb_host_pair_revoke_existed_at_inspect_sha(True))
    assert is_ok(claim_qmb_host_pair_revoke_existed_at_inspect_sha(False))
    source = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "pairing.py"
    text = source.read_text(encoding="utf-8")
    assert "PT15M" not in text
    assert "pairing.origin_revoked" in text


def test_scn0029_ordering_a_renew_then_origin_revoke(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        record_id, proof, _pending_id = _issue_proof(journal, substrate.sqlite)
        registry = PairingWsRegistry()
        handle = _register_ws(substrate.sqlite, record_id)
        registry.register(handle)
        deps = _deps(journal, substrate.sqlite, ws_registry=registry)
        renewed = handle_pair_renew(
            _request(
                "POST",
                "/pair/renew",
                headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
            ),
            deps,
        )
        assert is_ok(renewed), renewed
        new_body = _json_body(renewed.value)
        p2_id = new_body["pairing_record_id"]
        p2_proof = new_body["pairing_proof"]
        assert isinstance(p2_id, str)
        assert isinstance(p2_proof, str)
        p2 = load_pairing_session(substrate.sqlite, p2_id)
        assert p2 is not None
        p2_seq = p2.journal_seq
        p2_handle = PairingWsHandle(proof_fp1=p2.proof_fp1)
        registry.register(p2_handle)
        barrier = origin_revoke_pairing(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            ws_registry=registry,
        )
        assert is_ok(barrier), barrier
        r_seq = barrier.value["journal_seq"]
        assert isinstance(r_seq, int)
        assert p2_seq < r_seq
        assert barrier.value["barrier"] == "journal_seq"
        assert barrier.value["noop"] is False
        revoked_ids = barrier.value["revoked_record_ids"]
        assert isinstance(revoked_ids, tuple)
        assert p2_id in revoked_ids
        assert p2_handle.closed is True
        old = load_pairing_session(substrate.sqlite, record_id)
        assert old is not None
        assert old.revoked is True
        p2_after = load_pairing_session(substrate.sqlite, p2_id)
        assert p2_after is not None
        assert p2_after.revoked is True
        assert load_origin_barrier_seq(substrate.sqlite, _ORIGIN) == r_seq
        refused = handle_pair_renew(
            _request(
                "POST",
                "/pair/renew",
                headers={"Origin": _ORIGIN, "Authorization": _bearer(p2_proof)},
            ),
            deps,
        )
        assert is_refusal(refused)
        rows = journal.read_all()
        assert is_ok(rows)
        events = [str(row.get("event")) for row in rows.value]
        assert PAIRING_ORIGIN_REVOKED_EVENT in events
        assert "pairing_session.issued" in events
        assert journal_blob_contains_secret(journal, p2_proof) is False
    finally:
        journal.close()
        substrate.close()


def test_scn0029_ordering_b_origin_revoke_then_renew_refuses(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        record_id, proof, _ = _issue_proof(journal, substrate.sqlite)
        pre_r_pending = start_pairing_pending(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_expires(),
        )
        assert is_ok(pre_r_pending)
        confirm_pre = confirm_pairing_pending_by_code(
            journal=journal,
            sqlite=substrate.sqlite,
            code=pre_r_pending.value.pending_code,
            now_ns=_NOW_NS,
        )
        assert is_ok(confirm_pre)
        assert confirm_pre.value.consumed is False
        pending_before = load_pairing_pending(
            substrate.sqlite, pre_r_pending.value.pairing_record_id
        )
        assert pending_before is not None
        pending_seq = pending_before.journal_seq
        barrier = origin_revoke_pairing(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
        )
        assert is_ok(barrier), barrier
        r_seq = barrier.value["journal_seq"]
        assert isinstance(r_seq, int)
        assert pending_seq < r_seq
        deps = _deps(journal, substrate.sqlite)
        refused = handle_pair_renew(
            _request(
                "POST",
                "/pair/renew",
                headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
            ),
            deps,
        )
        assert is_refusal(refused)
        assert refused.category is RefusalCategory.POLICY_REJECTION
        confirm = handle_pair_confirm(
            _request(
                "POST",
                "/pair/confirm",
                headers={"Origin": _ORIGIN},
                body=json.dumps({"pending_id": pre_r_pending.value.pairing_record_id}).encode(
                    "utf-8"
                ),
            ),
            deps,
        )
        assert is_refusal(confirm)
        live_pending = load_pairing_pending(substrate.sqlite, pre_r_pending.value.pairing_record_id)
        assert live_pending is not None
        assert live_pending.revoked is True
        session = load_pairing_session(substrate.sqlite, record_id)
        assert session is not None
        assert session.revoked is True
    finally:
        journal.close()
        substrate.close()


def test_session_revoke_is_that_record_only_and_renew_old_id_is_noop(
    tmp_path: Path,
) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        r1, proof, _ = _issue_proof(journal, substrate.sqlite)
        other_id, other_proof, _ = _issue_proof(journal, substrate.sqlite, origin=_OTHER_ORIGIN)
        registry = PairingWsRegistry()
        handle = _register_ws(substrate.sqlite, r1)
        registry.register(handle)
        deps = _deps(journal, substrate.sqlite, ws_registry=registry)
        renewed = handle_pair_renew(
            _request(
                "POST",
                "/pair/renew",
                headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
            ),
            deps,
        )
        assert is_ok(renewed), renewed
        p2_id = _json_body(renewed.value)["pairing_record_id"]
        assert isinstance(p2_id, str)
        p2 = load_pairing_session(substrate.sqlite, p2_id)
        assert p2 is not None
        p2_handle = PairingWsHandle(proof_fp1=p2.proof_fp1)
        registry.register(p2_handle)
        assert handle.closed is True
        noop = session_revoke_pairing(
            journal=journal,
            sqlite=substrate.sqlite,
            pairing_record_id=r1,
            ws_registry=registry,
        )
        assert is_ok(noop), noop
        assert noop.value["noop"] is True
        assert noop.value["revoked_record_ids"] == ()
        assert p2_handle.closed is False
        p2_live = load_pairing_session(substrate.sqlite, p2_id)
        assert p2_live is not None
        assert p2_live.revoked is False
        other = load_pairing_session(substrate.sqlite, other_id)
        assert other is not None
        assert other.revoked is False
        killed = session_revoke_pairing(
            journal=journal,
            sqlite=substrate.sqlite,
            pairing_record_id=p2_id,
            ws_registry=registry,
        )
        assert is_ok(killed), killed
        assert killed.value["noop"] is False
        assert p2_handle.closed is True
        p2_after = load_pairing_session(substrate.sqlite, p2_id)
        assert p2_after is not None
        assert p2_after.revoked is True
        other_after = load_pairing_session(substrate.sqlite, other_id)
        assert other_after is not None
        assert other_after.revoked is False
        still = match_pairing_session_by_proof(
            substrate.sqlite, origin=_OTHER_ORIGIN, proof=other_proof, now_ns=_NOW_NS
        )
        assert is_ok(still)
    finally:
        journal.close()
        substrate.close()


def test_origin_revoke_does_not_cut_other_origin_and_post_r_start_is_legal(
    tmp_path: Path,
) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        _issue_proof(journal, substrate.sqlite)
        other_id, other_proof, _ = _issue_proof(journal, substrate.sqlite, origin=_OTHER_ORIGIN)
        barrier = origin_revoke_pairing(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
        )
        assert is_ok(barrier), barrier
        r_seq = barrier.value["journal_seq"]
        assert isinstance(r_seq, int)
        other = load_pairing_session(substrate.sqlite, other_id)
        assert other is not None
        assert other.revoked is False
        matched = match_pairing_session_by_proof(
            substrate.sqlite, origin=_OTHER_ORIGIN, proof=other_proof, now_ns=_NOW_NS
        )
        assert is_ok(matched)
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
        live = load_pairing_pending(substrate.sqlite, pending_id)
        assert live is not None
        assert live.journal_seq > r_seq
        assert live.revoked is False
        host = confirm_pairing_pending_by_code(
            journal=journal,
            sqlite=substrate.sqlite,
            code=code,
            now_ns=_NOW_NS,
        )
        assert is_ok(host)
        issued = handle_pair_confirm(
            _request(
                "POST",
                "/pair/confirm",
                headers={"Origin": _ORIGIN},
                body=json.dumps({"pending_id": pending_id}).encode("utf-8"),
            ),
            deps,
        )
        assert is_ok(issued), issued
        proof_body = _json_body(issued.value)
        assert "pairing_proof" in proof_body
        live_sessions = live_pairing_sessions_for_origin(
            substrate.sqlite, origin=_ORIGIN, now_ns=_NOW_NS
        )
        assert len(live_sessions) == 1
        assert live_sessions[0].journal_seq > r_seq
        second = origin_revoke_pairing(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
        )
        assert is_ok(second)
        r2 = second.value["journal_seq"]
        assert isinstance(r2, int)
        assert r2 > r_seq
        barriers = fold_origin_barriers_from_journal(journal)
        assert barriers[_ORIGIN][0] == r2
    finally:
        journal.close()
        substrate.close()


def test_restore_keeps_barrier_and_does_not_delete_history(tmp_path: Path) -> None:
    first_sub, first_journal = _open_journal(tmp_path, boot="boot-68-5-a")
    try:
        record_id, proof, _ = _issue_proof(first_journal, first_sub.sqlite)
        barrier = origin_revoke_pairing(
            journal=first_journal,
            sqlite=first_sub.sqlite,
            origin=_ORIGIN,
        )
        assert is_ok(barrier)
        r_seq = barrier.value["journal_seq"]
        rows = first_journal.read_all()
        assert is_ok(rows)
        history_len = len(rows.value)
        assert any(row.get("event") == "pairing_session.issued" for row in rows.value)
    finally:
        first_journal.close()
        first_sub.close()

    second_sub, second_journal = _open_journal(tmp_path, boot="boot-68-5-b")
    try:
        restored = restore_pairing_projections(second_journal, second_sub.sqlite)
        assert is_ok(restored)
        live = load_pairing_session(second_sub.sqlite, record_id)
        assert live is not None
        assert live.revoked is True
        assert load_origin_barrier_seq(second_sub.sqlite, _ORIGIN) == r_seq
        folded = fold_pairing_sessions_from_journal(second_journal)
        assert any(item.pairing_record_id == record_id and item.revoked for item in folded)
        rows = second_journal.read_all()
        assert is_ok(rows)
        assert len(rows.value) == history_len
        assert journal_blob_contains_secret(second_journal, proof) is False
        refused = match_pairing_session_by_proof(
            second_sub.sqlite, origin=_ORIGIN, proof=proof, now_ns=_NOW_NS
        )
        assert is_refusal(refused)
    finally:
        second_journal.close()
        second_sub.close()


def test_running_daemon_pair_revoke_over_host_control(tmp_path: Path) -> None:
    async def _run() -> None:
        composed = DaemonProcess.compose(
            tmp_path,
            machine="test-host",
            boot_epoch_id="boot-68-5-host",
            bind_port=0,
            plugin_load_configs=_seed_configs(tmp_path),
        )
        assert is_ok(composed), composed
        process = composed.value
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            record_id, _proof, _ = _issue_proof(process.journal, process.sqlite)
            revoked = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "pair-revoke",
                fields={"origin": _ORIGIN},
            )
            assert is_ok(revoked), revoked
            payload = revoked.value
            assert payload["ok"] is True
            body = payload["revoked"]
            assert isinstance(body, dict)
            assert body["scope"] == "origin"
            assert body["barrier"] == "journal_seq"
            assert isinstance(body["journal_seq"], int)
            assert "pairing_proof" not in body
            live = load_pairing_session(process.sqlite, record_id)
            assert live is not None
            assert live.revoked is True
            session_noop = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "pair-revoke",
                fields={"pairing_record_id": record_id},
            )
            assert is_ok(session_noop), session_noop
            noop_body = session_noop.value["revoked"]
            assert isinstance(noop_body, dict)
            assert noop_body["noop"] is True
            missing = await asyncio.to_thread(host_control_call, tmp_path, "pair-revoke")
            assert is_ok(missing)
            assert missing.value["ok"] is False
        finally:
            if not process.is_closed:
                await process.aclose()

    asyncio.run(_run())
