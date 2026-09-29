"""Pairing bearer custody, AM-03 projections (Story 68.1), HTTP/WS auth (68.3).

``pairing_proof`` is the RFC 6750 bearer. ``pairing_record_id`` is the nonsecret
journal identity. Projections ``pairing_pending`` and ``pairing_session`` store
``proof_fp1`` (and pending ``code_fp1``) never the raw proof. Named add on the
existing sqlite class — not a new class, not definition-store slot 17+, not
CT-28 ``pairing_record``. Do not mint ``pairing_session_id``.

Authenticated HTTP is ``Authorization: Bearer pairing:<proof>`` plus Origin.
Authenticated WebSocket offers ``qmx.ct40.v1`` and ``qmx.pair.<proof>``; the
daemon echoes ``qmx.ct40.v1``. Access logs redact ``qmx.pair.*`` values.
"""

from __future__ import annotations

import hmac
import json
import secrets
import sqlite3
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, cast

from qma.daemon.host_control.channel import HOST_CONTROL_INSPECT_SHA, redact_host_surface
from qma.daemon.host_control.local_operator import (
    DEC_0429_SUPERSEDED_BY,
    DEC_0440_SUPERSEDED_BY,
    LOCAL_OPERATOR_PRINCIPAL_ID,
)
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.journal.stores import StoreClass
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.wire.auth import (
    PAIRING_RECORD_ID_PREFIX,
    PAIRING_SESSION_ID_FIELD,
    AuthenticatedWireSession,
    authenticate_pairing_record,
    format_pairing_authorization,
    is_pairing_record_id,
    is_rfc6455_token,
    looks_like_bearer_proof,
    parse_pairing_bearer_authorization,
    refuse_pairing_proof_in_query,
)
from qma.wire.listener import (
    COOKIE_LOGIN_SHIPPED,
    CT40_WS_SUBPROTOCOL,
    HANDLE_CLIENT_DISCARDED_BYTES_AT_INSPECT_SHA,
    LOCALSTORAGE_PROOF_SHIPPED,
    PAIRING_BEARER_TRANSPORT_EXISTED_AT_INSPECT_SHA,
    PAIRING_WS_SUBPROTOCOLS_EXISTED_AT_INSPECT_SHA,
    WEBSOCKETS_IMPORTS_AT_INSPECT_SHA,
    claim_cookie_login_or_localstorage_proof_shipped,
    claim_pairing_transports_existed_at_inspect_sha,
    extract_pairing_ws_proof,
    selected_websocket_subprotocol,
)
from qmf.core import Ok, Result, fingerprint_bytes, is_refusal
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal
from qmf.data.store.refusals import invalid_input, storage_failure

__all__ = [
    "COOKIE_LOGIN_SHIPPED",
    "CT28_PAIRING_RECORD_REUSED",
    "CT40_WS_SUBPROTOCOL",
    "DEC_0429_SUPERSEDED_BY",
    "DEC_0440_SUPERSEDED_BY",
    "HANDLE_CLIENT_DISCARDED_BYTES_AT_INSPECT_SHA",
    "LOCALSTORAGE_PROOF_SHIPPED",
    "PAIRING_BEARER_TRANSPORT_EXISTED_AT_INSPECT_SHA",
    "PAIRING_DELIVERED_COPILOT_PROFILE",
    "PAIRING_HTTP_EXISTED_AT_INSPECT_SHA",
    "PAIRING_INSPECT_SHA",
    "PAIRING_NEW_SQLITE_CLASS",
    "PAIRING_PENDING_EVENT_STARTED",
    "PAIRING_PENDING_EXISTED_AT_INSPECT_SHA",
    "PAIRING_PENDING_FOLD_ID",
    "PAIRING_PENDING_STORE",
    "PAIRING_PENDING_TABLE",
    "PAIRING_PROOF_MAY_BIND_MULTIPLE_CONNECTIONS",
    "PAIRING_SESSION_EVENT_ISSUED",
    "PAIRING_SESSION_EXISTED_AT_INSPECT_SHA",
    "PAIRING_SESSION_FOLD_ID",
    "PAIRING_SESSION_ID_FIELD_MINTED",
    "PAIRING_SESSION_STORE",
    "PAIRING_SESSION_TABLE",
    "PAIRING_STORE_CLASS",
    "PAIRING_TABLE_EXISTED_AT_INSPECT_SHA",
    "PAIRING_WS_SUBPROTOCOLS_EXISTED_AT_INSPECT_SHA",
    "WEBSOCKETS_IMPORTS_AT_INSPECT_SHA",
    "IssuedPairingPending",
    "IssuedPairingProof",
    "PairingPendingLive",
    "PairingSessionLive",
    "PairingWsUpgrade",
    "authenticate_http_pairing_bearer",
    "authenticate_ws_pairing_upgrade",
    "claim_cookie_login_or_localstorage_proof_shipped",
    "claim_pair_http_existed_at_inspect_sha",
    "claim_pairing_pending_existed_at_inspect_sha",
    "claim_pairing_session_existed_at_inspect_sha",
    "claim_pairing_table_existed_at_inspect_sha",
    "claim_pairing_transports_existed_at_inspect_sha",
    "claim_this_story_delivered_copilot_profile",
    "fold_pairing_pendings_from_journal",
    "fold_pairing_sessions_from_journal",
    "issue_pairing_session",
    "journal_blob_contains_secret",
    "load_pairing_pending",
    "load_pairing_session",
    "match_pairing_session_by_proof",
    "mint_pairing_proof",
    "mint_pairing_record_id",
    "pairing_proof_fp1",
    "pairing_status_record_ids",
    "redact_pairing_access_log",
    "restore_pairing_projections",
    "start_pairing_pending",
]


PAIRING_PENDING_STORE: Final[str] = "pairing_pending"
PAIRING_SESSION_STORE: Final[str] = "pairing_session"
PAIRING_PENDING_FOLD_ID: Final[str] = "pairing_pending"
PAIRING_SESSION_FOLD_ID: Final[str] = "pairing_session"
PAIRING_PENDING_TABLE: Final[str] = "pairing_pending"
PAIRING_SESSION_TABLE: Final[str] = "pairing_session"
PAIRING_STORE_CLASS: Final[str] = StoreClass.JOURNAL_DERIVED_PROJECTION.value
PAIRING_PENDING_EVENT_STARTED: Final[str] = "pairing_pending.started"
PAIRING_SESSION_EVENT_ISSUED: Final[str] = "pairing_session.issued"
PAIRING_NEW_SQLITE_CLASS: Final[bool] = False
PAIRING_INSPECT_SHA: Final[str] = HOST_CONTROL_INSPECT_SHA
PAIRING_HTTP_EXISTED_AT_INSPECT_SHA: Final[bool] = False
PAIRING_TABLE_EXISTED_AT_INSPECT_SHA: Final[bool] = False
PAIRING_PENDING_EXISTED_AT_INSPECT_SHA: Final[bool] = False
PAIRING_SESSION_EXISTED_AT_INSPECT_SHA: Final[bool] = False
PAIRING_SESSION_ID_FIELD_MINTED: Final[bool] = False
CT28_PAIRING_RECORD_REUSED: Final[bool] = False
PAIRING_DELIVERED_COPILOT_PROFILE: Final[bool] = False
PAIRING_PROOF_MAY_BIND_MULTIPLE_CONNECTIONS: Final[bool] = True

_PENDING_SCHEMA_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS pairing_pending (
    pairing_record_id TEXT PRIMARY KEY NOT NULL,
    origin TEXT NOT NULL,
    operator_principal TEXT NOT NULL,
    proof_fp1 TEXT NOT NULL,
    code_fp1 TEXT NOT NULL,
    issued_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    revoked INTEGER NOT NULL,
    pending_lineage TEXT NOT NULL,
    journal_seq INTEGER NOT NULL,
    recorded_at INTEGER NOT NULL
);
"""

_SESSION_SCHEMA_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS pairing_session (
    pairing_record_id TEXT PRIMARY KEY NOT NULL,
    origin TEXT NOT NULL,
    operator_principal TEXT NOT NULL,
    proof_fp1 TEXT NOT NULL,
    issued_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    revoked INTEGER NOT NULL,
    pending_lineage TEXT NOT NULL,
    journal_seq INTEGER NOT NULL,
    recorded_at INTEGER NOT NULL
);
"""

_EMPTY_PROOF_FP1: Final[str] = ""


def _policy(field: str, reason: str, **extra: object) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION,
        retryability=Retryability.NO,
        context=context,
    )


def _claim_absent(field: str, reason: str, existed: object) -> Result[bool]:
    if existed is True or existed == "true":
        return _policy(
            field,
            reason,
            existed_at_inspect_sha=False,
            inspect_sha=PAIRING_INSPECT_SHA,
        )
    if existed is not False:
        return invalid_input(
            "existed_at_inspect_sha",
            "inspect-SHA claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_pair_http_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``/pair/*`` existed at inspect SHA ``34c148be`` fails."""
    return _claim_absent(
        "pair_http",
        "/pair/* was absent at inspect SHA 34c148be (DEC-0507 ABSENT)",
        existed,
    )


def claim_pairing_table_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming the pairing table existed at inspect SHA ``34c148be`` fails."""
    return _claim_absent(
        "pairing_table",
        "the pairing table was absent at inspect SHA 34c148be (DEC-0507 ABSENT)",
        existed,
    )


def claim_pairing_pending_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``pairing_pending`` existed at inspect SHA ``34c148be`` fails."""
    return _claim_absent(
        "pairing_pending",
        "pairing_pending was absent at inspect SHA 34c148be (AM-03 named add)",
        existed,
    )


def claim_pairing_session_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``pairing_session`` existed at inspect SHA ``34c148be`` fails."""
    return _claim_absent(
        "pairing_session",
        "pairing_session was absent at inspect SHA 34c148be (AM-03 named add)",
        existed,
    )


def claim_this_story_delivered_copilot_profile(delivered: object) -> Result[bool]:
    """Claiming this story delivered PluginManifest.copilot_profile fails."""
    if delivered is True or delivered == "true":
        return _policy(
            "copilot_profile",
            "PluginManifest.copilot_profile belongs to Story 60.1 / FEAT-0058, not Story 68.1",
            delivered=False,
        )
    if delivered is not False:
        return invalid_input(
            "delivered_copilot_profile",
            "copilot_profile delivery claim is a boolean",
            given=repr(delivered),
        )
    return Ok(False)


def mint_pairing_record_id() -> str:
    """Nonsecret journal identity. Never used as the Bearer value."""
    return f"{PAIRING_RECORD_ID_PREFIX}{uuid.uuid4().hex}"


def mint_pairing_proof() -> str:
    """High-entropy unguessable RFC 6455 token. Not a product entropy number."""
    while True:
        proof = secrets.token_urlsafe(32)
        if is_rfc6455_token(proof) and not is_pairing_record_id(proof):
            return proof


def pairing_proof_fp1(proof: str) -> str:
    """fp1 of the raw proof bytes. Journal stores this, never the proof."""
    return fingerprint_bytes(proof.encode("utf-8")).value


def _code_fp1(code: str) -> str:
    return fingerprint_bytes(code.encode("utf-8")).value


@dataclass(frozen=True, slots=True)
class IssuedPairingPending:
    """Once-returned pending code. Not a journal row."""

    pairing_record_id: str
    pending_code: str
    expires_at: int
    code_fp1: str


@dataclass(frozen=True, slots=True)
class IssuedPairingProof:
    """Once-returned confirm/renew body. Not a journal row."""

    pairing_record_id: str
    pairing_proof: str
    expires_at: int
    proof_fp1: str

    def to_once_returned_body(self) -> dict[str, object]:
        return {
            "pairing_record_id": self.pairing_record_id,
            "pairing_proof": self.pairing_proof,
            "expires_at": self.expires_at,
        }

    def authorization_header(self) -> Result[str]:
        return format_pairing_authorization(self.pairing_proof)


@dataclass(frozen=True, slots=True)
class PairingPendingLive:
    """Folded pending row. Never holds the raw code or raw proof."""

    pairing_record_id: str
    origin: str
    operator_principal: str
    proof_fp1: str
    code_fp1: str
    issued_at: int
    expires_at: int
    revoked: bool
    pending_lineage: str
    journal_seq: int
    recorded_at: int

    def to_payload(self) -> dict[str, object]:
        return {
            "pairing_record_id": self.pairing_record_id,
            "origin": self.origin,
            "operator_principal": self.operator_principal,
            "proof_fp1": self.proof_fp1,
            "code_fp1": self.code_fp1,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "pending_lineage": self.pending_lineage,
        }


@dataclass(frozen=True, slots=True)
class PairingSessionLive:
    """Folded session row. Never holds the raw proof."""

    pairing_record_id: str
    origin: str
    operator_principal: str
    proof_fp1: str
    issued_at: int
    expires_at: int
    revoked: bool
    pending_lineage: str
    journal_seq: int
    recorded_at: int

    def to_payload(self) -> dict[str, object]:
        return {
            "pairing_record_id": self.pairing_record_id,
            "origin": self.origin,
            "operator_principal": self.operator_principal,
            "proof_fp1": self.proof_fp1,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "pending_lineage": self.pending_lineage,
        }


def _ensure_schema(sqlite: SingleSqliteWriter) -> None:
    def _ddl(conn: sqlite3.Connection) -> None:
        conn.executescript(_PENDING_SCHEMA_SQL)
        conn.executescript(_SESSION_SCHEMA_SQL)

    sqlite.run(_ddl)


def _table_names(sqlite: SingleSqliteWriter) -> frozenset[str]:
    rows = sqlite.execute("SELECT name FROM sqlite_master WHERE type='table'")
    names: list[str] = []
    for row in rows:
        name = row[0]
        if isinstance(name, str):
            names.append(name)
    return frozenset(names)


def _int_flag(value: object) -> bool:
    return value in (1, True)


def _as_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _coalesce_issued(issued_at: object, recorded_at: int) -> int:
    issued = _as_int(issued_at)
    if issued is None or issued == 0:
        return recorded_at
    return issued


def _pending_from_tuple(row: tuple[object, ...]) -> PairingPendingLive | None:
    if len(row) < 11:
        return None
    pairing_record_id, origin, operator, proof_fp1, code_fp1 = row[:5]
    issued_at, expires_at, revoked, lineage, journal_seq, recorded_at = row[5:11]
    if not isinstance(pairing_record_id, str) or not is_pairing_record_id(pairing_record_id):
        return None
    if not isinstance(origin, str) or origin.strip() == "":
        return None
    if not isinstance(operator, str) or operator.strip() == "":
        return None
    if not isinstance(proof_fp1, str) or not isinstance(code_fp1, str):
        return None
    expires = _as_int(expires_at)
    seq = _as_int(journal_seq)
    recorded = _as_int(recorded_at)
    if expires is None or seq is None or recorded is None:
        return None
    if not isinstance(lineage, str):
        return None
    return PairingPendingLive(
        pairing_record_id=pairing_record_id,
        origin=origin,
        operator_principal=operator,
        proof_fp1=proof_fp1,
        code_fp1=code_fp1,
        issued_at=_coalesce_issued(issued_at, recorded),
        expires_at=expires,
        revoked=_int_flag(revoked),
        pending_lineage=lineage,
        journal_seq=seq,
        recorded_at=recorded,
    )


def _session_from_tuple(row: tuple[object, ...]) -> PairingSessionLive | None:
    if len(row) < 10:
        return None
    pairing_record_id, origin, operator, proof_fp1 = row[:4]
    issued_at, expires_at, revoked, lineage, journal_seq, recorded_at = row[4:10]
    if not isinstance(pairing_record_id, str) or not is_pairing_record_id(pairing_record_id):
        return None
    if not isinstance(origin, str) or origin.strip() == "":
        return None
    if not isinstance(operator, str) or operator.strip() == "":
        return None
    if not isinstance(proof_fp1, str) or proof_fp1.strip() == "":
        return None
    expires = _as_int(expires_at)
    seq = _as_int(journal_seq)
    recorded = _as_int(recorded_at)
    if expires is None or seq is None or recorded is None:
        return None
    if not isinstance(lineage, str):
        return None
    return PairingSessionLive(
        pairing_record_id=pairing_record_id,
        origin=origin,
        operator_principal=operator,
        proof_fp1=proof_fp1,
        issued_at=_coalesce_issued(issued_at, recorded),
        expires_at=expires,
        revoked=_int_flag(revoked),
        pending_lineage=lineage,
        journal_seq=seq,
        recorded_at=recorded,
    )


def load_pairing_pending(
    sqlite: SingleSqliteWriter,
    pairing_record_id: str,
) -> PairingPendingLive | None:
    names = _table_names(sqlite)
    if PAIRING_PENDING_TABLE not in names:
        return None
    rows = sqlite.execute(
        "SELECT pairing_record_id, origin, operator_principal, proof_fp1, code_fp1, "
        "issued_at, expires_at, revoked, pending_lineage, journal_seq, recorded_at "
        "FROM pairing_pending WHERE pairing_record_id = ?",
        (pairing_record_id,),
    )
    if not rows:
        return None
    return _pending_from_tuple(rows[0])


def load_pairing_session(
    sqlite: SingleSqliteWriter,
    pairing_record_id: str,
) -> PairingSessionLive | None:
    names = _table_names(sqlite)
    if PAIRING_SESSION_TABLE not in names:
        return None
    rows = sqlite.execute(
        "SELECT pairing_record_id, origin, operator_principal, proof_fp1, "
        "issued_at, expires_at, revoked, pending_lineage, journal_seq, recorded_at "
        "FROM pairing_session WHERE pairing_record_id = ?",
        (pairing_record_id,),
    )
    if not rows:
        return None
    return _session_from_tuple(rows[0])


def _put_pending(sqlite: SingleSqliteWriter, live: PairingPendingLive) -> None:
    _ensure_schema(sqlite)
    sqlite.execute(
        "INSERT OR REPLACE INTO pairing_pending "
        "(pairing_record_id, origin, operator_principal, proof_fp1, code_fp1, "
        "issued_at, expires_at, revoked, pending_lineage, journal_seq, recorded_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            live.pairing_record_id,
            live.origin,
            live.operator_principal,
            live.proof_fp1,
            live.code_fp1,
            live.issued_at,
            live.expires_at,
            1 if live.revoked else 0,
            live.pending_lineage,
            live.journal_seq,
            live.recorded_at,
        ),
    )


def _put_session(sqlite: SingleSqliteWriter, live: PairingSessionLive) -> None:
    _ensure_schema(sqlite)
    sqlite.execute(
        "INSERT OR REPLACE INTO pairing_session "
        "(pairing_record_id, origin, operator_principal, proof_fp1, "
        "issued_at, expires_at, revoked, pending_lineage, journal_seq, recorded_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            live.pairing_record_id,
            live.origin,
            live.operator_principal,
            live.proof_fp1,
            live.issued_at,
            live.expires_at,
            1 if live.revoked else 0,
            live.pending_lineage,
            live.journal_seq,
            live.recorded_at,
        ),
    )


def _payload_has_raw_secret(payload: Mapping[str, object]) -> bool:
    if PAIRING_SESSION_ID_FIELD in payload or "pairing_session_id" in payload:
        return True
    if "pairing_proof" in payload or "pending_code" in payload:
        return True
    if "superseded_by" in payload:
        return True
    for value in payload.values():
        if isinstance(value, str) and looks_like_bearer_proof(value):
            return True
    return False


def _pending_from_row(row: Mapping[str, object]) -> PairingPendingLive | None:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        return None
    body = cast("dict[str, object]", payload)
    if _payload_has_raw_secret(body):
        return None
    pairing_record_id = body.get("pairing_record_id")
    origin = body.get("origin")
    operator = body.get("operator_principal")
    proof_fp1 = body.get("proof_fp1")
    code_fp1 = body.get("code_fp1")
    issued_at = body.get("issued_at")
    expires_at = body.get("expires_at")
    revoked = body.get("revoked", False)
    lineage = body.get("pending_lineage", "")
    journal_seq = row.get("journal_seq")
    recorded_at = row.get("recorded_at")
    if not isinstance(pairing_record_id, str) or not is_pairing_record_id(pairing_record_id):
        return None
    if not isinstance(origin, str) or origin.strip() == "":
        return None
    if not isinstance(operator, str) or operator.strip() == "":
        return None
    if not isinstance(proof_fp1, str) or not isinstance(code_fp1, str):
        return None
    expires = _as_int(expires_at)
    seq = _as_int(journal_seq)
    recorded = _as_int(recorded_at)
    if expires is None or seq is None or recorded is None:
        return None
    if not isinstance(lineage, str):
        return None
    return PairingPendingLive(
        pairing_record_id=pairing_record_id,
        origin=origin,
        operator_principal=operator,
        proof_fp1=proof_fp1,
        code_fp1=code_fp1,
        issued_at=_coalesce_issued(issued_at, recorded),
        expires_at=expires,
        revoked=bool(revoked),
        pending_lineage=lineage,
        journal_seq=seq,
        recorded_at=recorded,
    )


def _session_from_row(row: Mapping[str, object]) -> PairingSessionLive | None:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        return None
    body = cast("dict[str, object]", payload)
    if _payload_has_raw_secret(body):
        return None
    pairing_record_id = body.get("pairing_record_id")
    origin = body.get("origin")
    operator = body.get("operator_principal")
    proof_fp1 = body.get("proof_fp1")
    issued_at = body.get("issued_at")
    expires_at = body.get("expires_at")
    revoked = body.get("revoked", False)
    lineage = body.get("pending_lineage", "")
    journal_seq = row.get("journal_seq")
    recorded_at = row.get("recorded_at")
    if not isinstance(pairing_record_id, str) or not is_pairing_record_id(pairing_record_id):
        return None
    if not isinstance(origin, str) or origin.strip() == "":
        return None
    if not isinstance(operator, str) or operator.strip() == "":
        return None
    if not isinstance(proof_fp1, str) or proof_fp1.strip() == "":
        return None
    expires = _as_int(expires_at)
    seq = _as_int(journal_seq)
    recorded = _as_int(recorded_at)
    if expires is None or seq is None or recorded is None:
        return None
    if not isinstance(lineage, str):
        return None
    return PairingSessionLive(
        pairing_record_id=pairing_record_id,
        origin=origin,
        operator_principal=operator,
        proof_fp1=proof_fp1,
        issued_at=_coalesce_issued(issued_at, recorded),
        expires_at=expires,
        revoked=bool(revoked),
        pending_lineage=lineage,
        journal_seq=seq,
        recorded_at=recorded,
    )


def fold_pairing_pendings_from_journal(
    journal: AuthoritativeJournal,
) -> tuple[PairingPendingLive, ...]:
    """as_of recorded_at; equal instants by ascending journal_seq."""
    rows = journal.read_all()
    if is_refusal(rows):
        return ()
    chosen: dict[str, PairingPendingLive] = {}
    chosen_key: dict[str, tuple[int, int]] = {}
    for raw in rows.value:
        event = raw.get("event")
        if not isinstance(event, str) or not event.startswith("pairing_pending."):
            continue
        live = _pending_from_row(raw)
        if live is None:
            continue
        key = (live.recorded_at, live.journal_seq)
        previous = chosen_key.get(live.pairing_record_id)
        if previous is None or key >= previous:
            chosen_key[live.pairing_record_id] = key
            chosen[live.pairing_record_id] = live
    ordered = sorted(chosen.values(), key=lambda item: (item.recorded_at, item.journal_seq))
    return tuple(ordered)


def fold_pairing_sessions_from_journal(
    journal: AuthoritativeJournal,
) -> tuple[PairingSessionLive, ...]:
    """as_of recorded_at; equal instants by ascending journal_seq."""
    rows = journal.read_all()
    if is_refusal(rows):
        return ()
    chosen: dict[str, PairingSessionLive] = {}
    chosen_key: dict[str, tuple[int, int]] = {}
    for raw in rows.value:
        event = raw.get("event")
        if not isinstance(event, str) or not event.startswith("pairing_session."):
            continue
        live = _session_from_row(raw)
        if live is None:
            continue
        key = (live.recorded_at, live.journal_seq)
        previous = chosen_key.get(live.pairing_record_id)
        if previous is None or key >= previous:
            chosen_key[live.pairing_record_id] = key
            chosen[live.pairing_record_id] = live
    ordered = sorted(chosen.values(), key=lambda item: (item.recorded_at, item.journal_seq))
    return tuple(ordered)


def _declare_folds(journal: AuthoritativeJournal) -> Result[None]:
    for store, fold_id in (
        (PAIRING_PENDING_STORE, PAIRING_PENDING_FOLD_ID),
        (PAIRING_SESSION_STORE, PAIRING_SESSION_FOLD_ID),
    ):
        declared = journal.declare_store(store)
        if is_refusal(declared):
            return declared
        registered = journal.register_fold(fold_id)
        if is_refusal(registered):
            return registered
    return Ok(None)


def restore_pairing_projections(
    journal: AuthoritativeJournal,
    sqlite: SingleSqliteWriter,
) -> Result[None]:
    """Reload hashes from the journal. Raw proofs are not in sqlite."""
    declared = _declare_folds(journal)
    if is_refusal(declared):
        return declared
    pendings = fold_pairing_pendings_from_journal(journal)
    sessions = fold_pairing_sessions_from_journal(journal)
    if pendings:
        for live in pendings:
            _put_pending(sqlite, live)
        materialized = journal.stores.materialize_on_first_write(PAIRING_PENDING_STORE)
        if is_refusal(materialized):
            return materialized
    if sessions:
        for live in sessions:
            _put_session(sqlite, live)
        materialized = journal.stores.materialize_on_first_write(PAIRING_SESSION_STORE)
        if is_refusal(materialized):
            return materialized
    return Ok(None)


def _require_origin(origin: object) -> Result[str]:
    if not isinstance(origin, str) or origin.strip() == "":
        return invalid_input("origin", "Origin is required", given=repr(origin))
    return Ok(origin.strip())


def _require_expires_at(expires_at: object) -> Result[int]:
    value = _as_int(expires_at)
    if value is None:
        return invalid_input(
            "expires_at",
            "expires_at is required; this story mints no TTL number",
            given=repr(expires_at),
        )
    return Ok(value)


def _require_operator(operator_principal: object) -> Result[str]:
    if not isinstance(operator_principal, str) or operator_principal.strip() == "":
        return invalid_input(
            "operator_principal",
            "operator principal is required",
            given=repr(operator_principal),
        )
    return Ok(operator_principal.strip())


def start_pairing_pending(
    *,
    journal: AuthoritativeJournal,
    sqlite: SingleSqliteWriter,
    origin: object,
    expires_at: object,
    operator_principal: object = LOCAL_OPERATOR_PRINCIPAL_ID,
) -> Result[IssuedPairingPending]:
    """Fold a pending row. Returns the code once; stores ``code_fp1`` only."""
    declared = _declare_folds(journal)
    if is_refusal(declared):
        return declared
    parsed_origin = _require_origin(origin)
    if is_refusal(parsed_origin):
        return parsed_origin
    parsed_expires = _require_expires_at(expires_at)
    if is_refusal(parsed_expires):
        return parsed_expires
    parsed_operator = _require_operator(operator_principal)
    if is_refusal(parsed_operator):
        return parsed_operator
    record_id = mint_pairing_record_id()
    code = mint_pairing_proof()
    hashed = _code_fp1(code)
    payload: dict[str, object] = {
        "pairing_record_id": record_id,
        "origin": parsed_origin.value,
        "operator_principal": parsed_operator.value,
        "proof_fp1": _EMPTY_PROOF_FP1,
        "code_fp1": hashed,
        "expires_at": parsed_expires.value,
        "revoked": False,
        "pending_lineage": "",
    }
    if _payload_has_raw_secret(payload):
        return storage_failure(
            "pending payload refused raw secret",
            context={"field": "pairing_pending"},
        )
    append = journal.append_event(PAIRING_PENDING_EVENT_STARTED, payload=payload)
    if is_refusal(append):
        return append
    record = append.value.record
    live = PairingPendingLive(
        pairing_record_id=record_id,
        origin=parsed_origin.value,
        operator_principal=parsed_operator.value,
        proof_fp1=_EMPTY_PROOF_FP1,
        code_fp1=hashed,
        issued_at=record.recorded_at,
        expires_at=parsed_expires.value,
        revoked=False,
        pending_lineage="",
        journal_seq=record.journal_seq,
        recorded_at=record.recorded_at,
    )
    _put_pending(sqlite, live)
    materialized = journal.stores.materialize_on_first_write(PAIRING_PENDING_STORE)
    if is_refusal(materialized):
        return materialized
    issued = IssuedPairingPending(
        pairing_record_id=record_id,
        pending_code=code,
        expires_at=parsed_expires.value,
        code_fp1=hashed,
    )
    return Ok(issued)


def issue_pairing_session(
    *,
    journal: AuthoritativeJournal,
    sqlite: SingleSqliteWriter,
    origin: object,
    expires_at: object,
    operator_principal: object = LOCAL_OPERATOR_PRINCIPAL_ID,
    pending_lineage: object = "",
) -> Result[IssuedPairingProof]:
    """Mint a bearer proof, journal ``proof_fp1`` only, return the proof once."""
    declared = _declare_folds(journal)
    if is_refusal(declared):
        return declared
    parsed_origin = _require_origin(origin)
    if is_refusal(parsed_origin):
        return parsed_origin
    parsed_expires = _require_expires_at(expires_at)
    if is_refusal(parsed_expires):
        return parsed_expires
    parsed_operator = _require_operator(operator_principal)
    if is_refusal(parsed_operator):
        return parsed_operator
    lineage = pending_lineage if isinstance(pending_lineage, str) else ""
    if lineage and not is_pairing_record_id(lineage):
        return invalid_input(
            "pending_lineage",
            "pending lineage is a pairing_record_id",
            given=repr(pending_lineage),
        )
    record_id = mint_pairing_record_id()
    proof = mint_pairing_proof()
    hashed = pairing_proof_fp1(proof)
    payload: dict[str, object] = {
        "pairing_record_id": record_id,
        "origin": parsed_origin.value,
        "operator_principal": parsed_operator.value,
        "proof_fp1": hashed,
        "expires_at": parsed_expires.value,
        "revoked": False,
        "pending_lineage": lineage,
    }
    if _payload_has_raw_secret(payload):
        return storage_failure(
            "session payload refused raw secret",
            context={"field": "pairing_session"},
        )
    append = journal.append_event(PAIRING_SESSION_EVENT_ISSUED, payload=payload)
    if is_refusal(append):
        return append
    record = append.value.record
    live = PairingSessionLive(
        pairing_record_id=record_id,
        origin=parsed_origin.value,
        operator_principal=parsed_operator.value,
        proof_fp1=hashed,
        issued_at=record.recorded_at,
        expires_at=parsed_expires.value,
        revoked=False,
        pending_lineage=lineage,
        journal_seq=record.journal_seq,
        recorded_at=record.recorded_at,
    )
    _put_session(sqlite, live)
    materialized = journal.stores.materialize_on_first_write(PAIRING_SESSION_STORE)
    if is_refusal(materialized):
        return materialized
    issued = IssuedPairingProof(
        pairing_record_id=record_id,
        pairing_proof=proof,
        expires_at=parsed_expires.value,
        proof_fp1=hashed,
    )
    return Ok(issued)


def match_pairing_session_by_proof(
    sqlite: SingleSqliteWriter,
    *,
    origin: object,
    proof: object,
    now_ns: object = None,
) -> Result[PairingSessionLive]:
    """Match Origin + proof_fp1. Does not store the presented proof.

    One unexpired unrevoked proof may be presented on multiple connections for
    that Origin until expiry, revoke, or rotate.
    """
    parsed_origin = _require_origin(origin)
    if is_refusal(parsed_origin):
        return parsed_origin
    if not isinstance(proof, str) or not is_rfc6455_token(proof):
        return _policy(
            "pairing_proof",
            "presented proof is not a pairing bearer",
            given="malformed",
        )
    hashed = pairing_proof_fp1(proof)
    names = _table_names(sqlite)
    if PAIRING_SESSION_TABLE not in names:
        return _policy("pairing_proof", "pairing table has no matching proof_fp1")
    rows = sqlite.execute(
        "SELECT pairing_record_id, origin, operator_principal, proof_fp1, "
        "issued_at, expires_at, revoked, pending_lineage, journal_seq, recorded_at "
        "FROM pairing_session"
    )
    origin_mismatch = False
    expired_match = False
    now = _as_int(now_ns)
    for row in rows:
        live = _session_from_tuple(row)
        if live is None:
            continue
        stored = live.proof_fp1.encode("utf-8")
        presented = hashed.encode("utf-8")
        if not (len(stored) == len(presented) and hmac.compare_digest(stored, presented)):
            continue
        if live.origin != parsed_origin.value:
            origin_mismatch = True
            continue
        if live.revoked:
            continue
        if now is not None and live.expires_at <= now:
            expired_match = True
            continue
        return Ok(live)
    if origin_mismatch:
        return _policy(
            "origin",
            "Origin + proof_fp1 do not match the pairing table",
        )
    if expired_match:
        return _policy("pairing_proof", "pairing_proof is expired")
    return _policy("pairing_proof", "pairing table has no matching proof_fp1")


def authenticate_http_pairing_bearer(
    sqlite: SingleSqliteWriter,
    *,
    authorization: object,
    origin: object,
    query: object = None,
    now_ns: object = None,
    cookie: object = None,
) -> Result[AuthenticatedWireSession]:
    """HTTP Bearer pairing:<proof> plus Origin. Never pairing:<id> or cred://.

    A cookie presented is ignored as proof (DEC-0501). Fetch credentials omit.
    """
    refused_query = refuse_pairing_proof_in_query(query)
    if is_refusal(refused_query):
        return refused_query
    if isinstance(authorization, str) and "cred://" in authorization.casefold():
        return _policy(
            "authorization",
            "never uses a provider cred:// as the Bearer value",
        )
    auth_missing = not isinstance(authorization, str) or authorization.strip() == ""
    cookie_presented = cookie is not None and str(cookie).strip() != ""
    if auth_missing and cookie_presented:
        return _policy(
            "cookie",
            "Cookie header is not operator proof; a cookie presented is ignored as pairing_proof",
            cookie_is_proof=False,
        )
    parsed = parse_pairing_bearer_authorization(authorization)
    if is_refusal(parsed):
        return parsed
    matched = match_pairing_session_by_proof(
        sqlite,
        origin=origin,
        proof=parsed.value,
        now_ns=now_ns,
    )
    if is_refusal(matched):
        return matched
    return authenticate_pairing_record(matched.value.pairing_record_id)


@dataclass(frozen=True, slots=True)
class PairingWsUpgrade:
    """Admitted WebSocket upgrade. Echoes ``qmx.ct40.v1``. No initialize yet."""

    echoed_subprotocol: str
    pairing_record_id: str
    origin: str
    session: AuthenticatedWireSession
    sends_ct40_bytes: bool = False
    initializes: bool = False
    multiple_connections_allowed: bool = PAIRING_PROOF_MAY_BIND_MULTIPLE_CONNECTIONS

    def __post_init__(self) -> None:
        if self.echoed_subprotocol != CT40_WS_SUBPROTOCOL:
            msg = "daemon echoes qmx.ct40.v1"
            raise ValueError(msg)
        if self.sends_ct40_bytes or self.initializes:
            msg = "WS upgrade does not send CT-40 bytes or initialize"
            raise ValueError(msg)


def authenticate_ws_pairing_upgrade(
    sqlite: SingleSqliteWriter,
    *,
    offered_subprotocols: object,
    origin: object,
    now_ns: object = None,
    query: object = None,
    cookie: object = None,
) -> Result[PairingWsUpgrade]:
    """Inspect offered subprotocols; refuse missing/malformed/expired/mismatch.

    Browsers cannot set ``Authorization`` on ``WebSocket``. The subprotocol is
    the proof. A cookie presented is ignored as proof. Refused upgrades send no
    CT-40 bytes and do not ``initialize``.
    """
    refused_query = refuse_pairing_proof_in_query(query)
    if is_refusal(refused_query):
        return refused_query
    _ = cookie  # never operator proof; WS proof is qmx.pair.<proof>
    extracted = extract_pairing_ws_proof(offered_subprotocols)
    if is_refusal(extracted):
        return extracted
    matched = match_pairing_session_by_proof(
        sqlite,
        origin=origin,
        proof=extracted.value,
        now_ns=now_ns,
    )
    if is_refusal(matched):
        return matched
    session = authenticate_pairing_record(matched.value.pairing_record_id)
    if is_refusal(session):
        return session
    return Ok(
        PairingWsUpgrade(
            echoed_subprotocol=selected_websocket_subprotocol(),
            pairing_record_id=matched.value.pairing_record_id,
            origin=matched.value.origin,
            session=session.value,
            sends_ct40_bytes=False,
            initializes=False,
        )
    )


_PAIR_LOG_PREFIX: Final[str] = "qmx.pair."
_REDACTED_PAIR_TOKEN: Final[str] = f"{_PAIR_LOG_PREFIX}[redacted]"
_PAIR_TOKEN_STOP: Final[frozenset[str]] = frozenset(" \t\r\n,;\"'<>")


def _redact_qmx_pair_tokens(text: str) -> str:
    """Replace ``qmx.pair.<proof>`` tokens even when embedded in a header value."""
    lower = text.casefold()
    needle = _PAIR_LOG_PREFIX
    out: list[str] = []
    cursor = 0
    while True:
        idx = lower.find(needle, cursor)
        if idx < 0:
            out.append(text[cursor:])
            return "".join(out)
        out.append(text[cursor:idx])
        out.append(_REDACTED_PAIR_TOKEN)
        end = idx + len(needle)
        while end < len(text) and text[end] not in _PAIR_TOKEN_STOP:
            end += 1
        cursor = end


def _redact_access_log_value(value: object) -> object:
    if isinstance(value, Mapping):
        body = cast("Mapping[object, object]", value)
        out: dict[str, object] = {}
        for key, item in body.items():
            out[str(key)] = _redact_access_log_value(item)
        return out
    if isinstance(value, list):
        items = cast("list[object]", value)
        return [_redact_access_log_value(item) for item in items]
    if isinstance(value, tuple):
        items = cast("tuple[object, ...]", value)
        return [_redact_access_log_value(item) for item in items]
    if isinstance(value, str):
        return _redact_qmx_pair_tokens(value)
    return value


def redact_pairing_access_log(value: object) -> object:
    """Access logs redact Authorization, ``qmx.pair.*``, and raw proofs.

    ``pairing_record_id`` may be shown.
    """
    return _redact_access_log_value(redact_host_surface(value))


def pairing_status_record_ids(
    sqlite: SingleSqliteWriter,
) -> dict[str, tuple[str, ...]]:
    """Pending/bound record ids for status. Never proofs or codes."""
    names = _table_names(sqlite)
    pending: list[str] = []
    bound: list[str] = []
    if PAIRING_PENDING_TABLE in names:
        rows = sqlite.execute(
            "SELECT pairing_record_id, revoked FROM pairing_pending ORDER BY journal_seq"
        )
        for row in rows:
            record_id, revoked = row[0], row[1]
            if (
                isinstance(record_id, str)
                and is_pairing_record_id(record_id)
                and not _int_flag(revoked)
            ):
                pending.append(record_id)
    if PAIRING_SESSION_TABLE in names:
        rows = sqlite.execute(
            "SELECT pairing_record_id, revoked FROM pairing_session ORDER BY journal_seq"
        )
        for row in rows:
            record_id, revoked = row[0], row[1]
            if (
                isinstance(record_id, str)
                and is_pairing_record_id(record_id)
                and not _int_flag(revoked)
            ):
                bound.append(record_id)
    return {
        "pending_record_ids": _status_record_ids(pending),
        "bound_record_ids": _status_record_ids(bound),
    }


def _status_record_ids(record_ids: list[str]) -> tuple[str, ...]:
    kept: list[str] = []
    for record_id in record_ids:
        redacted = redact_host_surface(record_id)
        if isinstance(redacted, str) and is_pairing_record_id(redacted):
            kept.append(redacted)
    return tuple(kept)


def journal_blob_contains_secret(journal: AuthoritativeJournal, secret: str) -> bool:
    """True when a raw secret appears in the durable journal JSON."""
    rows = journal.read_all()
    if is_refusal(rows):
        return False
    blob = json.dumps(rows.value, ensure_ascii=True)
    return secret in blob
