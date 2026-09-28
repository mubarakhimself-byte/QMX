"""AM-03 ``local_operator`` journal projection (Story 67.2).

Named add on the existing sqlite class — not a new class, not definition-store
slot 17+. Live shape: one local operator principal plus current
``host_control_fp1``. Fold: stream ``noun.verb``, ordering ``journal_seq``,
knowledge-time ``as_of`` over ``recorded_at``, equal-instant ascending
``journal_seq``. Do not set ``superseded_by``.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.host_control.channel import (
    HOST_CONTROL_FILE,
    HOST_CONTROL_INSPECT_SHA,
    ensure_host_control_token,
    mint_recovered_host_control_token,
    read_host_control_token,
    rotate_host_control_token,
)
from qma.daemon.host_control.root import caller_owns_daemon_root
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.journal.stores import StoreClass
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qmf.core import Ok, Result, fingerprint_bytes, is_refusal
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal
from qmf.data.store.refusals import policy_rejection, storage_failure

__all__ = [
    "DEC_0429_SUPERSEDED_BY",
    "DEC_0440_SUPERSEDED_BY",
    "HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA",
    "LOCAL_OPERATOR_ESTABLISHED_EVENT",
    "LOCAL_OPERATOR_EXISTED_AT_INSPECT_SHA",
    "LOCAL_OPERATOR_FOLD_ID",
    "LOCAL_OPERATOR_NEW_SQLITE_CLASS",
    "LOCAL_OPERATOR_PRINCIPAL_ID",
    "LOCAL_OPERATOR_RECOVERED_EVENT",
    "LOCAL_OPERATOR_ROTATED_EVENT",
    "LOCAL_OPERATOR_STORE",
    "LOCAL_OPERATOR_STORE_CLASS",
    "LOCAL_OPERATOR_TABLE",
    "HostControlRotation",
    "LocalOperatorLive",
    "bootstrap_first_operator",
    "claim_host_configure_existed_at_inspect_sha",
    "claim_local_operator_existed_at_inspect_sha",
    "host_control_fp1",
    "load_local_operator",
    "principal_count",
    "recover_local_operator_control",
    "rotate_local_operator_control",
]


LOCAL_OPERATOR_STORE: Final[str] = "local_operator"
LOCAL_OPERATOR_FOLD_ID: Final[str] = "local_operator"
LOCAL_OPERATOR_TABLE: Final[str] = "local_operator"
LOCAL_OPERATOR_STORE_CLASS: Final[str] = StoreClass.JOURNAL_DERIVED_PROJECTION.value
LOCAL_OPERATOR_PRINCIPAL_ID: Final[str] = "local_operator"
LOCAL_OPERATOR_ESTABLISHED_EVENT: Final[str] = "local_operator.established"
LOCAL_OPERATOR_ROTATED_EVENT: Final[str] = "local_operator.host_control_rotated"
LOCAL_OPERATOR_RECOVERED_EVENT: Final[str] = "local_operator.host_control_recovered"
LOCAL_OPERATOR_NEW_SQLITE_CLASS: Final[bool] = False
LOCAL_OPERATOR_EXISTED_AT_INSPECT_SHA: Final[bool] = False
HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA: Final[bool] = False
DEC_0429_SUPERSEDED_BY: Final[None] = None
DEC_0440_SUPERSEDED_BY: Final[None] = None

_SCHEMA_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS local_operator (
    principal_id TEXT PRIMARY KEY NOT NULL,
    principal_class TEXT NOT NULL,
    host_control_fp1 TEXT NOT NULL,
    journal_seq INTEGER NOT NULL,
    recorded_at INTEGER NOT NULL
);
"""


def _policy(field: str, reason: str, **extra: object) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION,
        retryability=Retryability.NO,
        context=context,
    )


def _invalid(field: str, reason: str, **extra: object) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context=context,
    )


def claim_local_operator_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``local_operator`` existed at inspect SHA ``34c148be`` fails."""
    if existed is True or existed == "true":
        return _policy(
            "local_operator",
            "local_operator was absent at inspect SHA 34c148be (AM-03 named add)",
            existed_at_inspect_sha=False,
            inspect_sha=HOST_CONTROL_INSPECT_SHA,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_host_configure_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``qmb host configure`` existed at inspect SHA ``34c148be`` fails."""
    if existed is True or existed == "true":
        return _policy(
            "host.configure",
            "qmb host configure was absent at inspect SHA 34c148be",
            existed_at_inspect_sha=False,
            inspect_sha=HOST_CONTROL_INSPECT_SHA,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def host_control_fp1(token: str) -> str:
    """fp1 of the host_control token bytes. Journal stores this, never the token."""
    return fingerprint_bytes(token.encode("utf-8")).value


@dataclass(frozen=True, slots=True)
class HostControlRotation:
    """In-process rotate-control result. The token is never journaled."""

    live: LocalOperatorLive
    previous_host_control_fp1: str
    token: str


@dataclass(frozen=True, slots=True)
class LocalOperatorLive:
    """Live fold shape: one local operator principal plus current host_control_fp1."""

    principal_id: str
    principal_class: str
    host_control_fp1: str
    journal_seq: int
    recorded_at: int
    minted: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "principal_id": self.principal_id,
            "principal_class": self.principal_class,
            "host_control_fp1": self.host_control_fp1,
            "journal_seq": self.journal_seq,
            "recorded_at": self.recorded_at,
        }


def _ensure_schema(sqlite: SingleSqliteWriter) -> None:
    def _ddl(conn: sqlite3.Connection) -> None:
        conn.executescript(_SCHEMA_SQL)

    sqlite.run(_ddl)


def load_local_operator(sqlite: SingleSqliteWriter) -> LocalOperatorLive | None:
    """Return the live sqlite fold row, or None when the projection is empty."""
    _ensure_schema(sqlite)
    rows = sqlite.execute(
        "SELECT principal_id, principal_class, host_control_fp1, journal_seq, "
        "recorded_at FROM local_operator"
    )
    if not rows:
        return None
    principal_id, principal_class, fp1, journal_seq, recorded_at = rows[0]
    if not isinstance(principal_id, str) or not isinstance(principal_class, str):
        return None
    if not isinstance(fp1, str):
        return None
    if not isinstance(journal_seq, int) or isinstance(journal_seq, bool):
        return None
    if not isinstance(recorded_at, int) or isinstance(recorded_at, bool):
        return None
    return LocalOperatorLive(
        principal_id=principal_id,
        principal_class=principal_class,
        host_control_fp1=fp1,
        journal_seq=journal_seq,
        recorded_at=recorded_at,
        minted=False,
    )


def principal_count(sqlite: SingleSqliteWriter) -> int:
    _ensure_schema(sqlite)
    rows = sqlite.execute("SELECT COUNT(*) FROM local_operator")
    if not rows:
        return 0
    count = rows[0][0]
    if isinstance(count, int) and not isinstance(count, bool):
        return count
    return 0


def _put(sqlite: SingleSqliteWriter, live: LocalOperatorLive) -> None:
    _ensure_schema(sqlite)
    sqlite.execute(
        "INSERT OR REPLACE INTO local_operator "
        "(principal_id, principal_class, host_control_fp1, journal_seq, recorded_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            live.principal_id,
            live.principal_class,
            live.host_control_fp1,
            live.journal_seq,
            live.recorded_at,
        ),
    )


def _live_from_row(row: dict[str, object]) -> LocalOperatorLive | None:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        return None
    body = cast("dict[str, object]", payload)
    principal_id = body.get("principal_id")
    principal_class = body.get("principal_class")
    fp1 = body.get("host_control_fp1")
    journal_seq = row.get("journal_seq")
    recorded_at = row.get("recorded_at")
    if not isinstance(principal_id, str) or principal_id.strip() == "":
        return None
    if not isinstance(principal_class, str) or principal_class.strip() == "":
        return None
    if not isinstance(fp1, str) or fp1.strip() == "":
        return None
    if not isinstance(journal_seq, int) or isinstance(journal_seq, bool):
        return None
    if not isinstance(recorded_at, int) or isinstance(recorded_at, bool):
        return None
    if "superseded_by" in body:
        return None
    return LocalOperatorLive(
        principal_id=principal_id,
        principal_class=principal_class,
        host_control_fp1=fp1,
        journal_seq=journal_seq,
        recorded_at=recorded_at,
        minted=False,
    )


def fold_local_operator_from_journal(journal: AuthoritativeJournal) -> LocalOperatorLive | None:
    """as_of recorded_at; equal instants by ascending journal_seq."""
    rows = journal.read_all()
    if is_refusal(rows):
        return None
    chosen: LocalOperatorLive | None = None
    chosen_key: tuple[int, int] | None = None
    for raw in rows.value:
        event = raw.get("event")
        if not isinstance(event, str) or not event.startswith("local_operator."):
            continue
        live = _live_from_row(raw)
        if live is None:
            continue
        key = (live.recorded_at, live.journal_seq)
        if chosen_key is None or key >= chosen_key:
            chosen_key = key
            chosen = live
    return chosen


def _declare_fold(journal: AuthoritativeJournal) -> Result[None]:
    declared = journal.declare_store(LOCAL_OPERATOR_STORE)
    if is_refusal(declared):
        return declared
    registered = journal.register_fold(LOCAL_OPERATOR_FOLD_ID)
    if is_refusal(registered):
        return registered
    return Ok(None)


def bootstrap_first_operator(
    root: Path,
    *,
    journal: AuthoritativeJournal,
    sqlite: SingleSqliteWriter,
) -> Result[LocalOperatorLive]:
    """Mint local_operator + host_control on an empty root. Never remint a principal."""
    declared = _declare_fold(journal)
    if is_refusal(declared):
        return declared

    existing = load_local_operator(sqlite)
    if existing is None:
        existing = fold_local_operator_from_journal(journal)
        if existing is not None:
            _put(sqlite, existing)

    if existing is not None:
        materialized = journal.stores.materialize_on_first_write(LOCAL_OPERATOR_STORE)
        if is_refusal(materialized):
            return materialized
        return Ok(existing)

    minted = ensure_host_control_token(root)
    if is_refusal(minted):
        return minted
    token = minted.value
    if not token:
        return storage_failure(
            "empty-root bootstrap minted an empty host_control",
            context={"field": "host_control", "root": str(root)},
        )
    fp1 = host_control_fp1(token)
    payload: dict[str, object] = {
        "principal_id": LOCAL_OPERATOR_PRINCIPAL_ID,
        "principal_class": PrincipalClass.OPERATOR.value,
        "host_control_fp1": fp1,
    }
    append = journal.append_event(LOCAL_OPERATOR_ESTABLISHED_EVENT, payload=payload)
    if is_refusal(append):
        return append
    record = append.value.record
    live = LocalOperatorLive(
        principal_id=LOCAL_OPERATOR_PRINCIPAL_ID,
        principal_class=PrincipalClass.OPERATOR.value,
        host_control_fp1=fp1,
        journal_seq=record.journal_seq,
        recorded_at=record.recorded_at,
        minted=True,
    )
    _put(sqlite, live)
    materialized = journal.stores.materialize_on_first_write(LOCAL_OPERATOR_STORE)
    if is_refusal(materialized):
        return materialized
    if principal_count(sqlite) != 1:
        return policy_rejection(
            "local_operator",
            "live shape is a single local operator principal (AM-03)",
            count=principal_count(sqlite),
        )
    held = read_host_control_token(root)
    if is_refusal(held):
        return held
    path = root / HOST_CONTROL_FILE
    if not path.is_file():
        return policy_rejection(
            "host_control",
            "empty-root bootstrap must mint an owner-only host_control file",
            root=str(root),
        )
    return Ok(live)


def _restore_host_control_token(root: Path, token: str) -> None:
    path = root / HOST_CONTROL_FILE
    try:
        path.write_text(token + "\n", encoding="utf-8")
    except OSError:
        return


def rotate_local_operator_control(
    root: Path,
    *,
    journal: AuthoritativeJournal,
    sqlite: SingleSqliteWriter,
) -> Result[HostControlRotation]:
    """Remint host_control while held. Same principal; journals stay intact."""
    existing = load_local_operator(sqlite)
    if existing is None:
        existing = fold_local_operator_from_journal(journal)
        if existing is not None:
            _put(sqlite, existing)
    if existing is None:
        return policy_rejection(
            "local_operator",
            "rotate-control requires an established local_operator",
            root=str(root),
        )
    held = read_host_control_token(root)
    if is_refusal(held):
        return held
    previous_token = held.value
    minted = rotate_host_control_token(root)
    if is_refusal(minted):
        return minted
    new_token = minted.value
    new_fp1 = host_control_fp1(new_token)
    previous_fp1 = existing.host_control_fp1
    payload: dict[str, object] = {
        "principal_id": existing.principal_id,
        "principal_class": existing.principal_class,
        "host_control_fp1": new_fp1,
        "previous_host_control_fp1": previous_fp1,
    }
    append = journal.append_event(LOCAL_OPERATOR_ROTATED_EVENT, payload=payload)
    if is_refusal(append):
        _restore_host_control_token(root, previous_token)
        return append
    record = append.value.record
    live = LocalOperatorLive(
        principal_id=existing.principal_id,
        principal_class=existing.principal_class,
        host_control_fp1=new_fp1,
        journal_seq=record.journal_seq,
        recorded_at=record.recorded_at,
        minted=False,
    )
    _put(sqlite, live)
    if principal_count(sqlite) != 1:
        return policy_rejection(
            "local_operator",
            "live shape is a single local operator principal (AM-03)",
            count=principal_count(sqlite),
        )
    return Ok(
        HostControlRotation(
            live=live,
            previous_host_control_fp1=previous_fp1,
            token=new_token,
        )
    )


def _owns_root_gate(root: Path, owns_root: object) -> Result[None]:
    if owns_root is None:
        if caller_owns_daemon_root(root):
            return Ok(None)
        return policy_rejection(
            "QMA_DAEMON_ROOT",
            "caller is not the OS owner of the daemon root",
            root=str(root),
        )
    if owns_root is True:
        return Ok(None)
    if owns_root is False:
        return policy_rejection(
            "QMA_DAEMON_ROOT",
            "caller is not the OS owner of the daemon root",
            root=str(root),
        )
    if callable(owns_root):
        try:
            owned = owns_root(root)
        except OSError, TypeError, ValueError:
            owned = False
        if owned is True:
            return Ok(None)
        return policy_rejection(
            "QMA_DAEMON_ROOT",
            "caller is not the OS owner of the daemon root",
            root=str(root),
        )
    return _invalid("owns_root", "owns_root is a bool or callable", given=repr(owns_root))


def _drop_recovered_token(root: Path) -> None:
    path = root / HOST_CONTROL_FILE
    try:
        path.unlink()
    except OSError:
        return


def recover_local_operator_control(
    root: Path,
    *,
    journal: AuthoritativeJournal,
    sqlite: SingleSqliteWriter,
    owns_root: object = None,
) -> Result[HostControlRotation]:
    """Remint host_control without the lost token. Same principal; journals stay."""
    owned = _owns_root_gate(root, owns_root)
    if is_refusal(owned):
        return owned
    held = read_host_control_token(root)
    if isinstance(held, Ok):
        return policy_rejection(
            "recover-control",
            "host_control is still readable; use rotate-control",
            root=str(root),
        )
    existing = load_local_operator(sqlite)
    if existing is None:
        existing = fold_local_operator_from_journal(journal)
        if existing is not None:
            _put(sqlite, existing)
    if existing is None:
        return policy_rejection(
            "local_operator",
            "recover-control requires an established local_operator",
            root=str(root),
        )
    minted = mint_recovered_host_control_token(root)
    if is_refusal(minted):
        return minted
    new_token = minted.value
    new_fp1 = host_control_fp1(new_token)
    previous_fp1 = existing.host_control_fp1
    payload: dict[str, object] = {
        "principal_id": existing.principal_id,
        "principal_class": existing.principal_class,
        "host_control_fp1": new_fp1,
        "previous_host_control_fp1": previous_fp1,
    }
    append = journal.append_event(LOCAL_OPERATOR_RECOVERED_EVENT, payload=payload)
    if is_refusal(append):
        _drop_recovered_token(root)
        return append
    record = append.value.record
    live = LocalOperatorLive(
        principal_id=existing.principal_id,
        principal_class=existing.principal_class,
        host_control_fp1=new_fp1,
        journal_seq=record.journal_seq,
        recorded_at=record.recorded_at,
        minted=False,
    )
    _put(sqlite, live)
    if principal_count(sqlite) != 1:
        return policy_rejection(
            "local_operator",
            "live shape is a single local operator principal (AM-03)",
            count=principal_count(sqlite),
        )
    return Ok(
        HostControlRotation(
            live=live,
            previous_host_control_fp1=previous_fp1,
            token=new_token,
        )
    )
