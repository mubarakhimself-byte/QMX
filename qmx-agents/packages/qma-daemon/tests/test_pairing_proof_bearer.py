"""Story 68.1 — pairing_proof is the bearer; journal stores proof_fp1."""

from __future__ import annotations

import json
from pathlib import Path

from qma.daemon import AuthoritativeJournal, PersistenceSubstrate
from qma.daemon.host_control import (
    DEC_0429_SUPERSEDED_BY,
    DEC_0440_SUPERSEDED_BY,
    claim_types_absent_at_inspect_sha,
)
from qma.daemon.journal import CLOSED_PROJECTIONS, DEFINITION_STORE_MEMBERS, v1_fold_contract
from qma.daemon.journal.stores import StoreClass
from qma.daemon.pairing import (
    CT28_PAIRING_RECORD_REUSED,
    PAIRING_DELIVERED_COPILOT_PROFILE,
    PAIRING_HTTP_EXISTED_AT_INSPECT_SHA,
    PAIRING_NEW_SQLITE_CLASS,
    PAIRING_PENDING_EXISTED_AT_INSPECT_SHA,
    PAIRING_PENDING_FOLD_ID,
    PAIRING_PENDING_STORE,
    PAIRING_PENDING_TABLE,
    PAIRING_SESSION_EVENT_ISSUED,
    PAIRING_SESSION_EXISTED_AT_INSPECT_SHA,
    PAIRING_SESSION_FOLD_ID,
    PAIRING_SESSION_ID_FIELD_MINTED,
    PAIRING_SESSION_STORE,
    PAIRING_SESSION_TABLE,
    PAIRING_STORE_CLASS,
    PAIRING_TABLE_EXISTED_AT_INSPECT_SHA,
    authenticate_http_pairing_bearer,
    claim_pair_http_existed_at_inspect_sha,
    claim_pairing_pending_existed_at_inspect_sha,
    claim_pairing_session_existed_at_inspect_sha,
    claim_pairing_table_existed_at_inspect_sha,
    claim_this_story_delivered_copilot_profile,
    fold_pairing_pendings_from_journal,
    fold_pairing_sessions_from_journal,
    issue_pairing_session,
    journal_blob_contains_secret,
    load_pairing_pending,
    load_pairing_session,
    pairing_proof_fp1,
    pairing_status_record_ids,
    restore_pairing_projections,
    start_pairing_pending,
)
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.auth import (
    PAIRING_HTTP_AUTHORIZATION_PREFIX,
    is_rfc6455_token,
    parse_pairing_bearer_authorization,
)
from qmf.core import DataDrivenClock, Instant, is_ok, is_refusal

_ORIGIN = "http://127.0.0.1:5173"
_EXPIRES_AT = 1_800_000_000_000_000_000


def _test_clock(*, boot: str = "boot-68-1", n: int = 64) -> DataDrivenClock:
    base = 1_710_000_000_000_000_000
    walls = tuple(Instant(value_ns=base + i) for i in range(n))
    monos = tuple(i * 1_000 for i in range(n))
    return DataDrivenClock(boot_epoch_id=boot, wall_instants=walls, monotonic_ns=monos)


def _open_journal(
    tmp_path: Path, *, boot: str = "boot-68-1"
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


def test_honesty_pairing_absent_at_inspect() -> None:
    assert PAIRING_HTTP_EXISTED_AT_INSPECT_SHA is False
    assert PAIRING_TABLE_EXISTED_AT_INSPECT_SHA is False
    assert PAIRING_PENDING_EXISTED_AT_INSPECT_SHA is False
    assert PAIRING_SESSION_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_pair_http_existed_at_inspect_sha(True))
    assert is_ok(claim_pair_http_existed_at_inspect_sha(False))
    assert is_refusal(claim_pairing_table_existed_at_inspect_sha(True))
    assert is_ok(claim_pairing_table_existed_at_inspect_sha(False))
    assert is_refusal(claim_pairing_pending_existed_at_inspect_sha(True))
    assert is_ok(claim_pairing_pending_existed_at_inspect_sha(False))
    assert is_refusal(claim_pairing_session_existed_at_inspect_sha(True))
    assert is_ok(claim_pairing_session_existed_at_inspect_sha(False))
    assert is_refusal(claim_types_absent_at_inspect_sha(True))
    assert is_ok(claim_types_absent_at_inspect_sha(False))
    assert PAIRING_DELIVERED_COPILOT_PROFILE is False
    assert is_refusal(claim_this_story_delivered_copilot_profile(True))
    assert is_ok(claim_this_story_delivered_copilot_profile(False))


def test_am03_named_add_not_new_sqlite_class_or_ct28() -> None:
    assert PAIRING_NEW_SQLITE_CLASS is False
    assert StoreClass.JOURNAL_DERIVED_PROJECTION.value == PAIRING_STORE_CLASS
    assert PAIRING_PENDING_STORE in CLOSED_PROJECTIONS
    assert PAIRING_SESSION_STORE in CLOSED_PROJECTIONS
    assert PAIRING_PENDING_STORE not in DEFINITION_STORE_MEMBERS
    assert PAIRING_SESSION_STORE not in DEFINITION_STORE_MEMBERS
    assert len(DEFINITION_STORE_MEMBERS) == 16
    assert DEC_0429_SUPERSEDED_BY is None
    assert DEC_0440_SUPERSEDED_BY is None
    assert CT28_PAIRING_RECORD_REUSED is False
    assert PAIRING_SESSION_ID_FIELD_MINTED is False
    pending = v1_fold_contract(PAIRING_PENDING_FOLD_ID)
    session = v1_fold_contract(PAIRING_SESSION_FOLD_ID)
    assert pending is not None
    assert session is not None
    assert pending.source_stream == "pairing_pending.*"
    assert session.source_stream == "pairing_session.*"
    assert pending.ordering_key == "journal_seq"
    assert session.knowledge_time_bound == "as_of_recorded_at"
    assert pending.equal_instant_disposition == "ascending_journal_seq"


def test_issue_folds_proof_fp1_never_raw_proof(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        pending = start_pairing_pending(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_EXPIRES_AT,
        )
        assert is_ok(pending)
        code = pending.value.pending_code
        pending_id = pending.value.pairing_record_id
        issued = issue_pairing_session(
            journal=journal,
            sqlite=substrate.sqlite,
            origin=_ORIGIN,
            expires_at=_EXPIRES_AT,
            pending_lineage=pending_id,
        )
        assert is_ok(issued)
        proof = issued.value.pairing_proof
        record_id = issued.value.pairing_record_id
        assert is_rfc6455_token(proof)
        assert proof != record_id
        assert issued.value.proof_fp1 == pairing_proof_fp1(proof)
        assert issued.value.proof_fp1.startswith("fp1:sha256:")

        live = load_pairing_session(substrate.sqlite, record_id)
        assert live is not None
        assert live.pairing_record_id == record_id
        assert live.origin == _ORIGIN
        assert live.operator_principal == "local_operator"
        assert live.proof_fp1 == issued.value.proof_fp1
        assert live.pending_lineage == pending_id
        assert not hasattr(live, "pairing_proof")
        assert live.revoked is False

        folded_pending = load_pairing_pending(substrate.sqlite, pending_id)
        assert folded_pending is not None
        assert folded_pending.code_fp1 == pending.value.code_fp1
        assert folded_pending.proof_fp1 == ""
        assert not hasattr(folded_pending, "pending_code")

        assert journal_blob_contains_secret(journal, proof) is False
        assert journal_blob_contains_secret(journal, code) is False
        rows = journal.read_all()
        assert is_ok(rows)
        blob = json.dumps(rows.value)
        assert proof not in blob
        assert code not in blob
        assert "pairing_proof" not in blob
        assert "pending_code" not in blob
        assert "superseded_by" not in blob
        assert "pairing_session_id" not in blob
        session_event = next(
            row for row in rows.value if row["event"] == PAIRING_SESSION_EVENT_ISSUED
        )
        payload = session_event["payload"]
        assert isinstance(payload, dict)
        assert payload["pairing_record_id"] == record_id
        assert payload["proof_fp1"] == issued.value.proof_fp1
        assert "pairing_proof" not in payload

        sqlite_rows = substrate.sqlite.execute("SELECT * FROM pairing_session")
        assert proof not in str(sqlite_rows)
        sqlite_pending = substrate.sqlite.execute("SELECT * FROM pairing_pending")
        assert code not in str(sqlite_pending)
        table_rows = substrate.sqlite.execute("SELECT name FROM sqlite_master WHERE type='table'")
        names = {str(row[0]) for row in table_rows}
        assert PAIRING_PENDING_TABLE in names
        assert PAIRING_SESSION_TABLE in names

        status = pairing_status_record_ids(substrate.sqlite)
        assert pending_id in status["pending_record_ids"]
        assert record_id in status["bound_record_ids"]
        assert proof not in status["pending_record_ids"]
        assert proof not in status["bound_record_ids"]
        assert code not in status["pending_record_ids"]

        header = issued.value.authorization_header()
        assert is_ok(header)
        assert header.value.startswith(PAIRING_HTTP_AUTHORIZATION_PREFIX)
        parsed = parse_pairing_bearer_authorization(header.value)
        assert is_ok(parsed)
        assert parsed.value == proof
        as_id = parse_pairing_bearer_authorization(f"Bearer pairing:{record_id}")
        assert is_refusal(as_id)

        authed = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=header.value,
            origin=_ORIGIN,
        )
        assert is_ok(authed)
        assert authed.value.pairing_record_id == record_id
        assert authed.value.credential_ref is None
        diagnostic = authed.value.to_diagnostic()
        assert diagnostic["pairing_record_id"] == record_id
        assert proof not in json.dumps(diagnostic)

        wrong_origin = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=header.value,
            origin="http://127.0.0.1:9999",
        )
        assert is_refusal(wrong_origin)

        in_query = authenticate_http_pairing_bearer(
            substrate.sqlite,
            authorization=header.value,
            origin=_ORIGIN,
            query={"pairing_proof": proof},
        )
        assert is_refusal(in_query)

        folded_sessions = fold_pairing_sessions_from_journal(journal)
        assert len(folded_sessions) == 1
        assert folded_sessions[0].proof_fp1 == issued.value.proof_fp1
        folded_pendings = fold_pairing_pendings_from_journal(journal)
        assert len(folded_pendings) == 1
        assert folded_pendings[0].code_fp1 == pending.value.code_fp1
    finally:
        journal.close()
        substrate.close()


def test_restore_reloads_hashes_not_proofs(tmp_path: Path) -> None:
    first_sub, first_journal = _open_journal(tmp_path, boot="boot-68-1-a")
    try:
        issued = issue_pairing_session(
            journal=first_journal,
            sqlite=first_sub.sqlite,
            origin=_ORIGIN,
            expires_at=_EXPIRES_AT,
        )
        assert is_ok(issued)
        proof = issued.value.pairing_proof
        record_id = issued.value.pairing_record_id
        fp1 = issued.value.proof_fp1
    finally:
        first_journal.close()
        first_sub.close()

    second_sub, second_journal = _open_journal(tmp_path, boot="boot-68-1-b")
    try:
        restored = restore_pairing_projections(second_journal, second_sub.sqlite)
        assert is_ok(restored)
        live = load_pairing_session(second_sub.sqlite, record_id)
        assert live is not None
        assert live.proof_fp1 == fp1
        assert not hasattr(live, "pairing_proof")
        assert journal_blob_contains_secret(second_journal, proof) is False
        header = f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{proof}"
        authed = authenticate_http_pairing_bearer(
            second_sub.sqlite,
            authorization=header,
            origin=_ORIGIN,
        )
        assert is_ok(authed)
        assert authed.value.pairing_record_id == record_id
    finally:
        second_journal.close()
        second_sub.close()


def test_host_status_lists_record_ids_never_proofs(tmp_path: Path) -> None:
    process = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id="boot-68-1-status",
        bind_port=0,
        plugin_load_configs=_seed_configs(tmp_path),
    )
    assert is_ok(process), process
    daemon = process.value
    try:
        issued = issue_pairing_session(
            journal=daemon.journal,
            sqlite=daemon.sqlite,
            origin=_ORIGIN,
            expires_at=_EXPIRES_AT,
        )
        assert is_ok(issued)
        proof = issued.value.pairing_proof
        snapshot = daemon.host_status_snapshot()
        bound_ids = snapshot["bound_record_ids"]
        assert isinstance(bound_ids, list | tuple)
        assert issued.value.pairing_record_id in bound_ids
        blob = json.dumps(dict(snapshot))
        assert proof not in blob
        assert "pairing_proof" not in blob
        assert PAIRING_HTTP_AUTHORIZATION_PREFIX not in blob
    finally:
        daemon.close()
