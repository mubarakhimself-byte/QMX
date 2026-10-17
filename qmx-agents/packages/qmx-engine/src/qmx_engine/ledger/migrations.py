"""The ledger schema: a `schema_version` row in `meta` and forward-only steps.

Step N moves the schema from version N-1 to N. A file whose version is newer than this code knows
is refused, never downgraded. The SQLite library version is recorded in `meta` at every writer
open: below 3.51.3 (the B1 WAL-reset floor) concurrent checkpointers can corrupt a WAL database,
which is why only the writer thread ever checkpoints, whatever the version.
"""

from __future__ import annotations

import sqlite3
from typing import Final

STEPS: Final[tuple[tuple[str, ...], ...]] = (
    (
        "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID",
        "CREATE TABLE events ("
        " run_id TEXT NOT NULL, seq INTEGER NOT NULL, at TEXT NOT NULL, kind TEXT NOT NULL,"
        " data TEXT NOT NULL, PRIMARY KEY (run_id, seq)) WITHOUT ROWID",
        "CREATE TABLE memos ("
        " fingerprint TEXT PRIMARY KEY, run_id TEXT NOT NULL, node_id TEXT NOT NULL,"
        " iteration INTEGER NOT NULL, partition_id TEXT NOT NULL, inputs_hash TEXT NOT NULL,"
        " definition_hash TEXT NOT NULL, outputs TEXT NOT NULL, valid INTEGER NOT NULL)",
        "CREATE INDEX memos_by_node ON memos (run_id, node_id)",
        "CREATE TABLE spans ("
        " span_id TEXT PRIMARY KEY, trace_id TEXT NOT NULL, started_at TEXT NOT NULL,"
        " record TEXT NOT NULL)",
        "CREATE INDEX spans_by_trace ON spans (trace_id, started_at)",
    ),
)


class LedgerSchemaError(Exception):
    pass


def schema_version(connection: sqlite3.Connection) -> int:
    has_meta = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'meta'"
    ).fetchone()
    if has_meta is None:
        return 0
    row = connection.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    return 0 if row is None else int(row[0])


def migrate(connection: sqlite3.Connection) -> list[int]:
    """Apply every step the file lacks, each in its own transaction, and return the versions
    applied. `connection` must be in autocommit mode (`isolation_level=None`)."""
    current = schema_version(connection)
    if current > len(STEPS):
        raise LedgerSchemaError(
            f"ledger schema version {current} is newer than this engine's {len(STEPS)}"
        )
    applied: list[int] = []
    for version in range(current + 1, len(STEPS) + 1):
        connection.execute("BEGIN IMMEDIATE")
        try:
            for statement in STEPS[version - 1]:
                connection.execute(statement)
            connection.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)",
                (str(version),),
            )
            connection.execute("COMMIT")
        except BaseException:
            connection.execute("ROLLBACK")
            raise
        applied.append(version)
    connection.execute(
        "INSERT INTO meta (key, value) VALUES ('sqlite_version', ?)"
        " ON CONFLICT (key) DO UPDATE SET value = excluded.value WHERE value != excluded.value",
        (sqlite3.sqlite_version,),
    )
    return applied
