"""Explicit backup-first Task Graph outbox schema migration.

Run while the daemon is stopped:
``python -m qma.daemon.persistence.task_graph_outbox_migration SOURCE BACKUP DESTINATION``.
The source is never modified. The backup is a full SQLite online-backup copy;
the destination is a distinct transformed copy and must be selected by the
operator only after the report and verification succeed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from qma.daemon.persistence.lock import DaemonWriterLock, WriterLockToken
from qmf.core import Ok, Result, fingerprint, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection, storage_failure

__all__ = ["TaskGraphOutboxMigrationReceipt", "migrate_task_graph_outbox"]

_TABLE: Final[str] = "task_graph_outbox"
_META: Final[str] = "task_graph_outbox_schema"
_OLD_VERSION: Final[int] = 1
_NEW_VERSION: Final[int] = 2
_LOCK_NAME: Final[str] = ".daemon_writer"
_OUTBOX_COLUMNS: Final[tuple[str, ...]] = (
    "graph_run_id",
    "successor_node_id",
    "predecessor_revision",
    "partition_id",
    "outbox_id",
    "predecessor_node_id",
    "logical_invocation_id",
    "target",
    "envelope_hash",
    "transport_state",
    "acceptance_state",
    "effect_state",
    "receiver_acceptance_id",
)


@dataclass(frozen=True, slots=True)
class TaskGraphOutboxMigrationReceipt:
    """Verification report for one backup-first SQLite copy migration."""

    source: str
    backup: str
    destination: str
    source_sha256: str
    backup_sha256: str
    destination_sha256: str
    source_layout_version: int
    destination_layout_version: int
    preserved_outbox_rows: int
    steps: tuple[str, ...]
    restore_path: str
    fingerprint: str

    def to_payload(self) -> MappingProxyType[str, object]:
        return MappingProxyType(
            {
                "class": "qma-task-graph-outbox-migration-v1",
                "source": self.source,
                "backup": self.backup,
                "destination": self.destination,
                "source_sha256": self.source_sha256,
                "backup_sha256": self.backup_sha256,
                "destination_sha256": self.destination_sha256,
                "source_layout_version": self.source_layout_version,
                "destination_layout_version": self.destination_layout_version,
                "preserved_outbox_rows": self.preserved_outbox_rows,
                "steps": list(self.steps),
                "restore_path": self.restore_path,
                "fingerprint": self.fingerprint,
            }
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _sync_file(path: Path) -> None:
    # Windows' CRT _commit (os.fsync) requires a writable descriptor.
    # Only migration-owned output copies are flushed through this function.
    descriptor = os.open(path, os.O_RDWR)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _sync_directory(path: Path) -> None:
    # Windows has no POSIX directory-fsync operation through os.open. The
    # SQLite copies and their writable file descriptors are still flushed;
    # source preservation remains the recovery path, not directory durability.
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _reserve_output(path: Path) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    os.close(descriptor)


def _user_tables(connection: sqlite3.Connection) -> tuple[str, ...]:
    return tuple(
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )
    )


def _read_only_connection(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)


def _table_rows(connection: sqlite3.Connection, table: str) -> tuple[tuple[object, ...], ...]:
    quoted = '"' + table.replace('"', '""') + '"'
    try:
        # Table names come only from sqlite_master and are quoted above.
        rows = connection.execute(f"SELECT * FROM {quoted} ORDER BY rowid").fetchall()  # noqa: S608
    except sqlite3.OperationalError:
        rows = connection.execute(f"SELECT * FROM {quoted}").fetchall()  # noqa: S608
    return tuple(tuple(row) for row in rows)


def _database_rows(connection: sqlite3.Connection) -> dict[str, tuple[tuple[object, ...], ...]]:
    return {table: _table_rows(connection, table) for table in _user_tables(connection)}


def _schema_objects(connection: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    rows = connection.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    return tuple(tuple(row) for row in rows)


def _preserved_schema_objects(
    objects: tuple[tuple[object, ...], ...],
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        row
        for row in objects
        if not (row[0] == "table" and row[1] in {_TABLE, _META})
        and not (row[0] == "index" and row[1] == "task_graph_outbox_logical")
    )


def _source_snapshot_matches(
    path: Path,
    expected_hash: str,
    expected_rows: dict[str, tuple[tuple[object, ...], ...]],
    expected_schema: tuple[tuple[object, ...], ...],
) -> bool:
    if _sha256(path) != expected_hash:
        return False
    connection = _read_only_connection(path)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        return (
            integrity is not None
            and integrity[0] == "ok"
            and _database_rows(connection) == expected_rows
            and _schema_objects(connection) == expected_schema
        )
    except sqlite3.Error:
        return False
    finally:
        connection.close()


def _checked_layout(connection: sqlite3.Connection) -> Result[tuple[int, int]]:
    tables = set(_user_tables(connection))
    if _TABLE not in tables:
        return invalid_input("source", "source database has no Task Graph outbox table")
    meta_present = _META in tables
    if meta_present:
        row = connection.execute(
            "SELECT schema_version FROM task_graph_outbox_schema WHERE singleton = 1"
        ).fetchone()
        if row is None or row[0] != _OLD_VERSION:
            return policy_rejection(
                "task_graph_outbox_schema",
                "migration accepts only an explicitly versioned layout 1 source",
                found=None if row is None else row[0],
            )
    columns = connection.execute("PRAGMA table_info(task_graph_outbox)").fetchall()
    if tuple(str(column[1]) for column in columns) != _OUTBOX_COLUMNS:
        return policy_rejection(
            "task_graph_outbox_schema",
            "migration accepts only the exact version 1 column layout",
        )
    predecessor = next((column for column in columns if column[1] == "predecessor_node_id"), None)
    indexes = connection.execute("PRAGMA index_list(task_graph_outbox)").fetchall()
    if (
        predecessor is None
        or not bool(predecessor[3])
        or not any(row[1] == "task_graph_outbox_logical" and bool(row[2]) for row in indexes)
    ):
        return policy_rejection(
            "task_graph_outbox_schema",
            "source physical layout is not the predecessor-required version 1 table",
        )
    return Ok((_OLD_VERSION, len(columns)))


def _copy_database(source: Path, destination: Path) -> None:
    source_connection = _read_only_connection(source)
    destination_connection = sqlite3.connect(destination)
    try:
        source_connection.backup(destination_connection)
        destination_connection.commit()
    finally:
        destination_connection.close()
        source_connection.close()


def _transform_destination(path: Path) -> Result[int]:
    connection = sqlite3.connect(path)
    try:
        before = connection.execute("SELECT * FROM task_graph_outbox ORDER BY rowid").fetchall()
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DROP INDEX IF EXISTS task_graph_outbox_logical")
        connection.execute("ALTER TABLE task_graph_outbox RENAME TO task_graph_outbox_v1")
        connection.execute(
            "CREATE TABLE task_graph_outbox ("
            "graph_run_id TEXT NOT NULL, successor_node_id TEXT NOT NULL, "
            "predecessor_revision INTEGER NOT NULL, partition_id TEXT NOT NULL, "
            "outbox_id TEXT NOT NULL, predecessor_node_id TEXT, "
            "logical_invocation_id TEXT NOT NULL, target TEXT NOT NULL, "
            "envelope_hash TEXT NOT NULL, transport_state TEXT NOT NULL, "
            "acceptance_state TEXT, effect_state TEXT, receiver_acceptance_id TEXT, "
            "PRIMARY KEY (graph_run_id, successor_node_id, predecessor_revision, partition_id))"
        )
        connection.execute("INSERT INTO task_graph_outbox SELECT * FROM task_graph_outbox_v1")
        connection.execute("DROP TABLE task_graph_outbox_v1")
        connection.execute(
            "CREATE UNIQUE INDEX task_graph_outbox_logical "
            "ON task_graph_outbox (logical_invocation_id)"
        )
        meta_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (_META,)
        ).fetchone()
        if meta_exists is None:
            connection.execute(
                "CREATE TABLE task_graph_outbox_schema "
                "(singleton INTEGER PRIMARY KEY CHECK (singleton = 1), "
                "schema_version INTEGER NOT NULL)"
            )
            connection.execute(
                "INSERT INTO task_graph_outbox_schema (singleton, schema_version) VALUES (1, ?)",
                (_NEW_VERSION,),
            )
        else:
            connection.execute(
                "UPDATE task_graph_outbox_schema SET schema_version = ? WHERE singleton = 1",
                (_NEW_VERSION,),
            )
        connection.commit()
        after = connection.execute("SELECT * FROM task_graph_outbox ORDER BY rowid").fetchall()
        if before != after:
            return policy_rejection(
                "migration_verify", "all existing Task Graph outbox rows remain byte-equivalent"
            )
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            return policy_rejection(
                "migration_verify", "destination SQLite integrity check succeeds"
            )
        marker = connection.execute(
            "SELECT schema_version FROM task_graph_outbox_schema WHERE singleton = 1"
        ).fetchone()
        predecessor = next(
            (
                row
                for row in connection.execute("PRAGMA table_info(task_graph_outbox)")
                if row[1] == "predecessor_node_id"
            ),
            None,
        )
        columns = connection.execute("PRAGMA table_info(task_graph_outbox)").fetchall()
        indexes = connection.execute("PRAGMA index_list(task_graph_outbox)").fetchall()
        if (
            marker != (_NEW_VERSION,)
            or tuple(str(column[1]) for column in columns) != _OUTBOX_COLUMNS
            or predecessor is None
            or bool(predecessor[3])
            or not any(row[1] == "task_graph_outbox_logical" and bool(row[2]) for row in indexes)
        ):
            return policy_rejection(
                "migration_verify", "destination carries the exact version 2 nullable layout"
            )
        return Ok(len(after))
    except sqlite3.Error as exc:
        connection.rollback()
        return storage_failure(
            "SQLite outbox migration failed",
            context={"error": type(exc).__name__},
        )
    finally:
        connection.close()


def _dry_run_transform(backup: Path, scratch: Path) -> Result[int]:
    """Exercise the full transform on a disposable copy of the verified backup."""

    created = False
    try:
        _reserve_output(scratch)
        created = True
        _copy_database(backup, scratch)
        transformed = _transform_destination(scratch)
        if is_refusal(transformed):
            return transformed
        source_connection = _read_only_connection(backup)
        dry_connection = _read_only_connection(scratch)
        try:
            backup_rows = _database_rows(source_connection)
            dry_rows = _database_rows(dry_connection)
            backup_schema = _schema_objects(source_connection)
            dry_schema = _schema_objects(dry_connection)
        finally:
            source_connection.close()
            dry_connection.close()
        expected = dict(backup_rows)
        expected[_TABLE] = _table_rows_from_migrated(scratch)
        expected[_META] = ((1, _NEW_VERSION),)
        if dry_rows != expected or _preserved_schema_objects(
            dry_schema
        ) != _preserved_schema_objects(backup_schema):
            return policy_rejection(
                "migration_dry_run", "disposable transform preserves all source table records"
            )
        return transformed
    except OSError as exc:
        return storage_failure(
            "SQLite outbox migration dry-run failed",
            context={"error": type(exc).__name__},
        )
    finally:
        if created:
            scratch.unlink(missing_ok=True)
            Path(f"{scratch}-wal").unlink(missing_ok=True)
            Path(f"{scratch}-shm").unlink(missing_ok=True)


def migrate_task_graph_outbox(
    *,
    source: Path | str,
    backup: Path | str,
    destination: Path | str,
) -> Result[TaskGraphOutboxMigrationReceipt]:
    """Copy v1 SQLite to a verified backup and distinct v2 destination.

    The daemon must be stopped. An extant writer lock is treated as active or
    uncertain and blocks migration; callers may not infer stale locks safe.
    """
    source_path = Path(source)
    backup_path = Path(backup)
    destination_path = Path(destination)
    if any(path.is_symlink() for path in (source_path, backup_path, destination_path)):
        return policy_rejection("path", "migration source and outputs cannot be symlinks")
    try:
        source_path = source_path.resolve(strict=True)
        backup_path = backup_path.resolve(strict=False)
        destination_path = destination_path.resolve(strict=False)
    except OSError as exc:
        return invalid_input("source", "migration source resolves", error=type(exc).__name__)
    if not source_path.is_file():
        return invalid_input("source", "migration source is a SQLite file")
    if len({source_path, backup_path, destination_path}) != 3:
        return policy_rejection("path", "source, backup, and destination are distinct files")
    if backup_path.exists() or destination_path.exists():
        return policy_rejection(
            "destination", "backup and migration destination must not already exist"
        )
    if not backup_path.parent.is_dir() or not destination_path.parent.is_dir():
        return invalid_input("destination", "backup and destination parent directories exist")
    if Path(f"{source_path}-wal").exists() or Path(f"{source_path}-shm").exists():
        return policy_rejection(
            "source_wal",
            "checkpoint and close SQLite before migrating a source with WAL sidecars",
        )
    lock_root = (
        source_path.parent.parent
        if source_path.parent.name == "daemon" and source_path.name == "daemon.sqlite"
        else source_path.parent
    )
    token = WriterLockToken(
        machine="qma-local-migration",
        role="task-graph-outbox-migration",
        boot_epoch_id=f"migration-{os.getpid()}",
        pid=os.getpid(),
    )
    lock = DaemonWriterLock(lock_root, token)
    acquired = lock.acquire()
    if is_refusal(acquired):
        return acquired
    try:
        return _migrate_locked(
            source_path=source_path,
            backup_path=backup_path,
            destination_path=destination_path,
        )
    finally:
        lock.release()


def _migrate_locked(
    *,
    source_path: Path,
    backup_path: Path,
    destination_path: Path,
) -> Result[TaskGraphOutboxMigrationReceipt]:
    """Perform the copy and transformation under the source-root writer lock."""

    source_before = _sha256(source_path)
    source_connection = _read_only_connection(source_path)
    try:
        integrity = source_connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            return policy_rejection("source", "source SQLite integrity check succeeds")
        layout = _checked_layout(source_connection)
        if is_refusal(layout):
            return layout
        source_tables = _database_rows(source_connection)
        source_schema = _schema_objects(source_connection)
    except sqlite3.Error as exc:
        return storage_failure(
            "cannot inspect migration source",
            context={"error": type(exc).__name__},
        )
    finally:
        source_connection.close()

    backup_created = False
    destination_created = False
    backup_verified = False
    try:
        _reserve_output(backup_path)
        backup_created = True
        _copy_database(source_path, backup_path)
        _sync_file(backup_path)
        _sync_directory(backup_path.parent)
        if not _source_snapshot_matches(source_path, source_before, source_tables, source_schema):
            return policy_rejection("source", "migration leaves the original database unchanged")
        backup_connection = _read_only_connection(backup_path)
        try:
            backup_layout = _checked_layout(backup_connection)
            if is_refusal(backup_layout):
                return backup_layout
            backup_tables = _database_rows(backup_connection)
            backup_schema = _schema_objects(backup_connection)
        finally:
            backup_connection.close()
        if backup_tables != source_tables or backup_schema != source_schema:
            return policy_rejection(
                "backup", "full SQLite backup preserves every table row and schema object"
            )
        backup_verified = True
        scratch_path = destination_path.with_name(f".{destination_path.name}.dry-run-{os.getpid()}")
        dry_run = _dry_run_transform(backup_path, scratch_path)
        if is_refusal(dry_run):
            return dry_run
        _reserve_output(destination_path)
        destination_created = True
        _copy_database(backup_path, destination_path)
        transformed = _transform_destination(destination_path)
        if is_refusal(transformed):
            destination_path.unlink(missing_ok=True)
            return transformed
        _sync_file(destination_path)
        _sync_directory(destination_path.parent)
        destination_connection = _read_only_connection(destination_path)
        try:
            destination_tables = _database_rows(destination_connection)
        finally:
            destination_connection.close()
        expected_tables = dict(backup_tables)
        expected_tables[_TABLE] = _table_rows_from_migrated(destination_path)
        expected_tables[_META] = ((1, _NEW_VERSION),)
        destination_connection = _read_only_connection(destination_path)
        try:
            destination_schema = _schema_objects(destination_connection)
        finally:
            destination_connection.close()
        if destination_tables != expected_tables or _preserved_schema_objects(
            destination_schema
        ) != _preserved_schema_objects(backup_schema):
            destination_path.unlink(missing_ok=True)
            return policy_rejection(
                "migration_verify", "destination preserves every non-outbox source record"
            )
        if not _source_snapshot_matches(source_path, source_before, source_tables, source_schema):
            destination_path.unlink(missing_ok=True)
            return policy_rejection("source", "migration leaves the original database unchanged")
        backup_hash = _sha256(backup_path)
        destination_hash = _sha256(destination_path)
        identity = {
            "class": "qma-task-graph-outbox-migration-v1",
            "source_sha256": source_before,
            "backup_sha256": backup_hash,
            "destination_sha256": destination_hash,
            "source_layout_version": _OLD_VERSION,
            "destination_layout_version": _NEW_VERSION,
            "preserved_outbox_rows": transformed.value,
            "steps": ("preflight", "backup", "dry-run", "migrate", "verify"),
            "restore_path": str(source_path),
        }
        fp = fingerprint(identity)
        if is_refusal(fp):
            return fp
        return Ok(
            TaskGraphOutboxMigrationReceipt(
                source=str(source_path),
                backup=str(backup_path),
                destination=str(destination_path),
                source_sha256=source_before,
                backup_sha256=backup_hash,
                destination_sha256=destination_hash,
                source_layout_version=_OLD_VERSION,
                destination_layout_version=_NEW_VERSION,
                preserved_outbox_rows=transformed.value,
                steps=("preflight", "backup", "dry-run", "migrate", "verify"),
                restore_path=str(source_path),
                fingerprint=fp.value.value,
            )
        )
    except OSError as exc:
        if destination_created and destination_path.exists():
            destination_path.unlink(missing_ok=True)
        if backup_created and not backup_verified and backup_path.exists():
            backup_path.unlink(missing_ok=True)
        return storage_failure(
            "SQLite outbox migration filesystem step failed",
            context={"error": type(exc).__name__},
        )


def _table_rows_from_migrated(path: Path) -> tuple[tuple[object, ...], ...]:
    connection = _read_only_connection(path)
    try:
        return _table_rows(connection, _TABLE)
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("backup", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    result = migrate_task_graph_outbox(
        source=args.source,
        backup=args.backup,
        destination=args.destination,
    )
    if is_refusal(result):
        print(json.dumps(dict(result.context), sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(dict(result.value.to_payload()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
