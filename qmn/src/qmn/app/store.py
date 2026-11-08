"""The node's volume store, ``data/node.sqlite``: what he asked for, what the node saw, who it is.

Three owned tables (Part C AD-301, NODE.md section 4):

- ``desired``: one row per change an operation handler took, in arrival order, never edited.
  Each row keeps its op id, so a repeated op id answers the first answer again.
- ``observed``: the latest value per key, written by the runtime (in C-10 by the server at
  start, until the runtime of C-12a takes the table over).
- ``identity``: the install id and machine fingerprint minted at first start, then one row per
  confirmation he gave on another machine.

Every connection is short and opened per call, so the MCP server's worker threads never share
one. A change is checked and inserted inside one ``BEGIN IMMEDIATE`` transaction, so two changes
arriving at once are still ordered one after the other. ``busy_seconds`` bounds the wait for that
lock, so a handler answers ``busy`` instead of outliving the supervisor's call timeout.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Generator
from contextlib import closing, contextmanager
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Final, TypeAlias, cast

__all__ = [
    "BUSY_SECONDS",
    "Change",
    "Desired",
    "IdentityRow",
    "Json",
    "Outcome",
    "Store",
    "StoreBusyError",
]

Json: TypeAlias = "bool | int | float | str | list[Json] | dict[str, Json] | None"

BUSY_SECONDS: Final = 1.0
"""`[node] store_busy_s`: how long a handler waits for the store's write lock before it answers
`busy`. Far under the 2 s answer budget and the supervisor's 20 s inner call timeout."""

_SCHEMA: Final = (
    "CREATE TABLE IF NOT EXISTS desired ("
    " seq INTEGER PRIMARY KEY AUTOINCREMENT,"
    " op_id TEXT NOT NULL UNIQUE,"
    " kind TEXT NOT NULL,"
    " register TEXT,"
    " args TEXT NOT NULL,"
    " stamped TEXT NOT NULL,"
    " issued_at_ns INTEGER NOT NULL,"
    " arrived_at_ns INTEGER NOT NULL,"
    " outcome TEXT NOT NULL,"
    " answer TEXT NOT NULL)",
    "CREATE INDEX IF NOT EXISTS desired_register ON desired (register, outcome)",
    "CREATE TABLE IF NOT EXISTS observed ("
    " key TEXT PRIMARY KEY, value TEXT NOT NULL, at_ns INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS identity ("
    " one INTEGER PRIMARY KEY CHECK (one = 1),"
    " install_id TEXT NOT NULL, fingerprint TEXT, minted_at_ns INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS identity_confirmations ("
    " seq INTEGER PRIMARY KEY AUTOINCREMENT, op_id TEXT NOT NULL, kind TEXT NOT NULL,"
    " from_fingerprint TEXT, to_fingerprint TEXT, at_ns INTEGER NOT NULL)",
)


class StoreBusyError(Exception):
    """The store's write lock stayed held past ``busy_seconds``."""


class Outcome(StrEnum):
    ACCEPTED = "accepted"
    """Applied to the target the reconciler folds."""
    SUPERSEDED = "superseded"
    """Older than the newest change applied for the same register; kept for the record only."""
    REFUSED = "refused"
    """Refused for the node's state (not set up, identity unconfirmed); kept so a repeat of its
    op id answers the same."""


@dataclass(frozen=True, slots=True)
class Change:
    """One row of ``desired``. ``register`` is the scope a newer change supersedes an older one
    in; ``None`` for a change that always applies (``kill``, ``flatten``). ``stamped`` says
    whether ``issued_at_ns`` came with the call (``caller``) or was stamped on arrival."""

    seq: int
    op_id: str
    kind: str
    register: str | None
    args: dict[str, Json]
    stamped: str
    issued_at_ns: int
    arrived_at_ns: int
    outcome: Outcome
    answer: dict[str, Json]


@dataclass(frozen=True, slots=True)
class IdentityRow:
    install_id: str
    fingerprint: str | None
    minted_at_ns: int


class Desired:
    """``desired`` as one write transaction sees it, for a change being decided."""

    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def newest_applied(self, register: str) -> Change | None:
        """The applied change of ``register`` with the latest ``issued_at``."""
        row = self._db.execute(
            "SELECT seq, op_id, kind, register, args, stamped, issued_at_ns, arrived_at_ns,"
            " outcome, answer FROM desired WHERE register = ? AND outcome = ?"
            " ORDER BY issued_at_ns DESC, seq DESC LIMIT 1",
            (register, Outcome.ACCEPTED.value),
        ).fetchone()
        return None if row is None else _change(row)

    def accepted(self) -> list[Change]:
        """Every applied change, in arrival order."""
        rows = self._db.execute(
            "SELECT seq, op_id, kind, register, args, stamped, issued_at_ns, arrived_at_ns,"
            " outcome, answer FROM desired WHERE outcome = ? ORDER BY seq",
            (Outcome.ACCEPTED.value,),
        )
        return [_change(row) for row in rows.fetchall()]

    def rebind_identity(
        self, *, op_id: str, kind: str, fingerprint: str | None, at_ns: int
    ) -> IdentityRow:
        """Bind the identity to ``fingerprint`` and keep his confirmation beside it."""
        row = self._db.execute("SELECT fingerprint FROM identity WHERE one = 1").fetchone()
        self._db.execute(
            "INSERT INTO identity_confirmations (op_id, kind, from_fingerprint, to_fingerprint,"
            " at_ns) VALUES (?,?,?,?,?)",
            (op_id, kind, None if row is None else row[0], fingerprint, at_ns),
        )
        self._db.execute("UPDATE identity SET fingerprint = ? WHERE one = 1", (fingerprint,))
        return cast(IdentityRow, _identity(self._db))


class Store:
    """``data/node.sqlite`` in the node's volume."""

    def __init__(self, path: Path, *, busy_seconds: float = BUSY_SECONDS) -> None:
        self.path = path
        self.busy_seconds = busy_seconds
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            for statement in _SCHEMA:
                db.execute(statement)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=self.busy_seconds, isolation_level=None)
        db.execute("PRAGMA journal_mode=WAL")
        return db

    @contextmanager
    def _write(self) -> Generator[sqlite3.Connection]:
        with closing(self._connect()) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as error:
                raise StoreBusyError(str(error)) from error
            try:
                yield db
            except BaseException:
                db.execute("ROLLBACK")
                raise
            db.execute("COMMIT")

    # --- desired -------------------------------------------------------------------------

    def accepted(self) -> list[Change]:
        """Every applied change, in arrival order."""
        with closing(self._connect()) as db:
            return Desired(db).accepted()

    def change(self, op_id: str) -> Change | None:
        """The change kept under ``op_id``, or None."""
        with closing(self._connect()) as db:
            return _change_by_op(db, op_id)

    def record(self, op_id: str, decide: Callable[[Desired], Change]) -> Change:
        """Decide and keep one change under the write lock, in arrival order.

        A repeated op id keeps nothing and answers the earlier row. Otherwise ``decide`` reads
        ``desired`` (and may rebind the identity) through the transaction's :class:`Desired` and
        returns the row to keep; ``seq`` is assigned here.
        """
        with self._write() as db:
            earlier = _change_by_op(db, op_id)
            if earlier is not None:
                return earlier
            decided = decide(Desired(db))
            cursor = db.execute(
                "INSERT INTO desired (op_id, kind, register, args, stamped, issued_at_ns,"
                " arrived_at_ns, outcome, answer) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    decided.op_id,
                    decided.kind,
                    decided.register,
                    _dump(decided.args),
                    decided.stamped,
                    decided.issued_at_ns,
                    decided.arrived_at_ns,
                    decided.outcome.value,
                    _dump(decided.answer),
                ),
            )
            seq = cast(int, cursor.lastrowid)
        return replace(decided, seq=seq)

    # --- observed ------------------------------------------------------------------------

    def observe(self, key: str, value: Json, at_ns: int) -> None:
        with self._write() as db:
            db.execute(
                "INSERT INTO observed (key, value, at_ns) VALUES (?,?,?) ON CONFLICT(key)"
                " DO UPDATE SET value = excluded.value, at_ns = excluded.at_ns",
                (key, _dump(value), at_ns),
            )

    def observed(self, key: str) -> Json:
        with closing(self._connect()) as db:
            row = db.execute("SELECT value FROM observed WHERE key = ?", (key,)).fetchone()
        return None if row is None else cast(Json, json.loads(str(row[0])))

    # --- identity ------------------------------------------------------------------------

    def identity(self) -> IdentityRow | None:
        with closing(self._connect()) as db:
            return _identity(db)

    def mint_identity(self, minted: IdentityRow) -> IdentityRow:
        """Keep ``minted`` unless an identity is already there; answer the one kept."""
        with self._write() as db:
            db.execute(
                "INSERT OR IGNORE INTO identity (one, install_id, fingerprint, minted_at_ns)"
                " VALUES (1, ?, ?, ?)",
                (minted.install_id, minted.fingerprint, minted.minted_at_ns),
            )
            kept = _identity(db)
        return cast(IdentityRow, kept)


def _dump(value: Json) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _change(row: tuple[object, ...]) -> Change:
    return Change(
        seq=cast(int, row[0]),
        op_id=str(row[1]),
        kind=str(row[2]),
        register=None if row[3] is None else str(row[3]),
        args=cast(dict[str, Json], json.loads(str(row[4]))),
        stamped=str(row[5]),
        issued_at_ns=cast(int, row[6]),
        arrived_at_ns=cast(int, row[7]),
        outcome=Outcome(str(row[8])),
        answer=cast(dict[str, Json], json.loads(str(row[9]))),
    )


def _change_by_op(db: sqlite3.Connection, op_id: str) -> Change | None:
    row = db.execute(
        "SELECT seq, op_id, kind, register, args, stamped, issued_at_ns, arrived_at_ns,"
        " outcome, answer FROM desired WHERE op_id = ?",
        (op_id,),
    ).fetchone()
    return None if row is None else _change(row)


def _identity(db: sqlite3.Connection) -> IdentityRow | None:
    row = db.execute(
        "SELECT install_id, fingerprint, minted_at_ns FROM identity WHERE one = 1"
    ).fetchone()
    if row is None:
        return None
    return IdentityRow(str(row[0]), None if row[1] is None else str(row[1]), int(row[2]))
