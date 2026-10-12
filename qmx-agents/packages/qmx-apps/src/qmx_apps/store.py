"""SQLite belongs to the instance; analytics only reads its durable files."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path

import duckdb

from qmx_apps.errors import AppError
from qmx_apps.volume import Volume


def open_store(volume: Volume, migrations: Path | None = None) -> sqlite3.Connection:
    """Open the instance's writer connection and apply numbered SQL migrations."""
    db = sqlite3.connect(volume.check_write("app.db"), timeout=5)
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA busy_timeout=5000")
        if migrations is not None:
            migrate(db, migrations)
        return db
    except BaseException:
        db.close()
        raise


def migrate(db: sqlite3.Connection, directory: Path) -> None:
    files = sorted(directory.glob("*.sql"))
    numbered: dict[int, Path] = {}
    for path in files:
        match = re.fullmatch(r"(\d+)(?:[-_].+)?\.sql", path.name)
        if not match or int(match[1]) < 1 or int(match[1]) in numbered:
            raise AppError("invalid_migration", "Use unique positive numbered SQL files.")
        numbered[int(match[1])] = path
    db.execute("CREATE TABLE IF NOT EXISTS _qmx_migrations (number INTEGER PRIMARY KEY, hash TEXT)")
    db.commit()
    for number, path in sorted(numbered.items()):
        sql = path.read_text(encoding="utf-8")
        digest = hashlib.sha256(sql.encode()).hexdigest()
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT hash FROM _qmx_migrations WHERE number=?", (number,)
            ).fetchone()
            if row:
                if row[0] != digest:
                    raise AppError("immutable_migration", "Applied SQL migrations cannot change.")
            else:
                highest = db.execute(
                    "SELECT COALESCE(MAX(number),0) FROM _qmx_migrations"
                ).fetchone()[0]
                if number <= highest:
                    raise AppError(
                        "invalid_migration", "New migrations must follow applied numbers."
                    )
                statement = ""
                for character in sql:
                    statement += character
                    if character == ";" and sqlite3.complete_statement(statement):
                        # Migrations cannot commit around the version record.
                        db.set_authorizer(_migration_authorizer)
                        try:
                            db.execute(statement)
                        finally:
                            db.set_authorizer(None)
                        statement = ""
                if statement.strip():
                    raise AppError("invalid_migration", "SQL statements must end with a semicolon.")
                db.execute("INSERT INTO _qmx_migrations VALUES(?,?)", (number, digest))
            db.commit()
        except BaseException:
            db.rollback()
            raise


def _migration_authorizer(
    action: int, first: str | None, second: str | None, database: str | None, trigger: str | None
) -> int:
    return (
        sqlite3.SQLITE_DENY
        if action in {sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT}
        else sqlite3.SQLITE_OK
    )


def analytics(volume: Volume) -> duckdb.DuckDBPyConnection:
    """Attach app.db as `app`; expose data/*.parquet as `parquet` when present."""
    connection = duckdb.connect()
    try:
        path = volume.check_write("app.db").as_posix().replace("'", "''")
        connection.execute(f"ATTACH '{path}' AS app (TYPE sqlite, READ_ONLY)")
        if list(volume.check_write("data").glob("*.parquet")):
            pattern = volume.check_write("data/*.parquet").as_posix().replace("'", "''")
            # DuckDB DDL does not accept parameters; the path is a quoted local literal.
            connection.execute(f"CREATE VIEW parquet AS SELECT * FROM read_parquet('{pattern}')")  # noqa: S608
        return connection
    except BaseException:
        connection.close()
        raise
