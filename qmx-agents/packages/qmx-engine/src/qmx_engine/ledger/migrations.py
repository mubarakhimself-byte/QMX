"""The ledger schema: forward-only steps, and the gate that opens, upgrades or refuses a file.

Step N moves the schema from version N-1 to N. Step 3 rebuilds `triggers` for the wider kind
check (SQLite cannot alter a CHECK) and adds a trigger's `priority` and `ready_by`, and a fire's
webhook `delivery_id`, its `delivery` outcome and its re-run count. Step 4 rebuilds `triggers`
without the `home_engine IN ('pc', 'contabo')` check, every row kept: a trigger's home is any
place in his list, which the service checks when it writes (AD-72). Step 5 adds a trigger's stored
`inputs`, `{}` for every row it finds.

The version lives in `meta` as `schema_version` (the release before this one reads it) and in
`PRAGMA user_version`, beside `min_reader` in `meta` (design 62 B1). Step 3 changes what a
trigger's kind may mean, so it raises `min_reader` to 3; steps 4 and 5 only widen a check or add
a column and leave it, so a version 3 engine may still open a version 5 ledger. Such an engine
reads its own named columns, so it fires triggers without their stored inputs.
`qmx_home.versions.open_sqlite` applies design 62 B2: a newer ledger whose `min_reader` this
engine meets opens as it is, one it does not meet is refused by name and never written, and an
older one is copied into the folder's `backups/` before its first step. The SQLite library
version is recorded in `meta` at every writer open: below 3.51.3 (the B1 WAL-reset floor)
concurrent checkpointers can corrupt a WAL database, which is why only the writer thread ever
checkpoints, whatever the version.
"""

from __future__ import annotations

import sqlite3
from typing import Final

from qmx_home.versions import open_sqlite

TRIGGER_COLUMNS: Final = (
    "id, workflow_item, pinned_object, follow_champion, home_engine, kind, spec, enabled,"
    " precheck_ref, role_pins, effort_pin, delivery, continuity, catch_up, max_concurrent, source,"
    " created_by, created_at, next_fire_at, last_status, failure_streak, quota_hold_until,"
    " incident_id, last_outputs, priority, ready_by"
)
"""Every `triggers` column since step 3, named so step 4's copy cannot shift one."""

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
    (
        "CREATE TABLE triggers ("
        " id TEXT PRIMARY KEY, workflow_item TEXT NOT NULL, pinned_object TEXT NOT NULL,"
        " follow_champion INTEGER NOT NULL,"
        " home_engine TEXT NOT NULL CHECK (home_engine IN ('pc', 'contabo')),"
        " kind TEXT NOT NULL CHECK (kind IN ('cron', 'interval', 'manual', 'after')),"
        " spec TEXT NOT NULL, enabled INTEGER NOT NULL, precheck_ref TEXT,"
        " role_pins TEXT NOT NULL, effort_pin TEXT, delivery TEXT NOT NULL,"
        " continuity INTEGER NOT NULL, catch_up TEXT NOT NULL, max_concurrent INTEGER NOT NULL,"
        " source TEXT NOT NULL, created_by TEXT NOT NULL, created_at TEXT NOT NULL,"
        " next_fire_at TEXT, last_status TEXT, failure_streak INTEGER NOT NULL,"
        " quota_hold_until TEXT, incident_id TEXT, last_outputs TEXT)",
        "CREATE INDEX triggers_due ON triggers (home_engine, enabled, next_fire_at)",
        "CREATE TABLE fires ("
        " id TEXT PRIMARY KEY, trigger_id TEXT NOT NULL, occurrence_at TEXT NOT NULL,"
        " claimed_by TEXT, claimed_at TEXT, lease_until TEXT, status TEXT NOT NULL, detail TEXT,"
        " run_id TEXT, merged_into TEXT, merged INTEGER NOT NULL, payload TEXT, digest TEXT,"
        " ended_at TEXT, UNIQUE (trigger_id, occurrence_at))",
        "CREATE INDEX fires_by_status ON fires (status, trigger_id)",
        "CREATE TABLE wakes ("
        " run_id TEXT PRIMARY KEY, resume_at TEXT NOT NULL, claimed_by TEXT, lease_until TEXT)",
        "CREATE INDEX wakes_due ON wakes (resume_at)",
    ),
    (
        "CREATE TABLE triggers_next ("
        " id TEXT PRIMARY KEY, workflow_item TEXT NOT NULL, pinned_object TEXT NOT NULL,"
        " follow_champion INTEGER NOT NULL,"
        " home_engine TEXT NOT NULL CHECK (home_engine IN ('pc', 'contabo')),"
        " kind TEXT NOT NULL CHECK (kind IN"
        " ('cron', 'interval', 'event', 'webhook', 'session', 'manual', 'after')),"
        " spec TEXT NOT NULL, enabled INTEGER NOT NULL, precheck_ref TEXT,"
        " role_pins TEXT NOT NULL, effort_pin TEXT, delivery TEXT NOT NULL,"
        " continuity INTEGER NOT NULL, catch_up TEXT NOT NULL, max_concurrent INTEGER NOT NULL,"
        " source TEXT NOT NULL, created_by TEXT NOT NULL, created_at TEXT NOT NULL,"
        " next_fire_at TEXT, last_status TEXT, failure_streak INTEGER NOT NULL,"
        " quota_hold_until TEXT, incident_id TEXT, last_outputs TEXT,"
        " priority INTEGER NOT NULL DEFAULT 0, ready_by TEXT)",
        "INSERT INTO triggers_next SELECT *, 0, NULL FROM triggers",
        "DROP TABLE triggers",
        "ALTER TABLE triggers_next RENAME TO triggers",
        "CREATE INDEX triggers_due ON triggers (home_engine, enabled, next_fire_at)",
        "ALTER TABLE fires ADD COLUMN delivery_id TEXT",
        "ALTER TABLE fires ADD COLUMN delivery TEXT",
        "ALTER TABLE fires ADD COLUMN rerun INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE fires ADD COLUMN rerun_of TEXT",
        "CREATE UNIQUE INDEX fires_by_delivery ON fires (trigger_id, delivery_id)"
        " WHERE delivery_id IS NOT NULL",
    ),
    (
        "CREATE TABLE triggers_next ("
        " id TEXT PRIMARY KEY, workflow_item TEXT NOT NULL, pinned_object TEXT NOT NULL,"
        " follow_champion INTEGER NOT NULL, home_engine TEXT NOT NULL,"
        " kind TEXT NOT NULL CHECK (kind IN"
        " ('cron', 'interval', 'event', 'webhook', 'session', 'manual', 'after')),"
        " spec TEXT NOT NULL, enabled INTEGER NOT NULL, precheck_ref TEXT,"
        " role_pins TEXT NOT NULL, effort_pin TEXT, delivery TEXT NOT NULL,"
        " continuity INTEGER NOT NULL, catch_up TEXT NOT NULL, max_concurrent INTEGER NOT NULL,"
        " source TEXT NOT NULL, created_by TEXT NOT NULL, created_at TEXT NOT NULL,"
        " next_fire_at TEXT, last_status TEXT, failure_streak INTEGER NOT NULL,"
        " quota_hold_until TEXT, incident_id TEXT, last_outputs TEXT,"
        " priority INTEGER NOT NULL DEFAULT 0, ready_by TEXT)",
        f"INSERT INTO triggers_next ({TRIGGER_COLUMNS}) SELECT {TRIGGER_COLUMNS} FROM triggers",  # noqa: S608
        "DROP TABLE triggers",
        "ALTER TABLE triggers_next RENAME TO triggers",
        "CREATE INDEX triggers_due ON triggers (home_engine, enabled, next_fire_at)",
    ),
    ("ALTER TABLE triggers ADD COLUMN inputs TEXT NOT NULL DEFAULT '{}'",),
)


def schema_version(connection: sqlite3.Connection) -> int:
    has_meta = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'meta'"
    ).fetchone()
    if has_meta is None:
        return 0
    row = connection.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    return 0 if row is None else int(row[0])


def migrate(connection: sqlite3.Connection) -> list[int]:
    """Bring the ledger to this engine's version and return the versions applied, each step in its
    own transaction after the pre-change copy. Raises `StoreRefused` for a ledger too new, a file
    that is not a ledger, an upgrade whose copy cannot be made and a step that fails.
    `connection` must be in autocommit mode (`isolation_level=None`)."""
    opened = open_sqlite(connection, "engine", STEPS)
    connection.execute(
        "INSERT INTO meta (key, value) VALUES ('sqlite_version', ?)"
        " ON CONFLICT (key) DO UPDATE SET value = excluded.value WHERE value != excluded.value",
        (sqlite3.sqlite_version,),
    )
    return list(opened.applied)
