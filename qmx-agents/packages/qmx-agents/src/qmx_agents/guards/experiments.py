"""An append-only experiment notebook identified by runs and apps."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import cast

from qmx_agents.guards.journal import encoded, fingerprint


class EvidenceRejected(ValueError):
    """Rejected bytes have already been committed to quarantine."""


@dataclass(frozen=True)
class ExperimentEntry:
    seq: int
    run_id: str
    app_id: str
    data: bytes
    disposition: str
    reason: str
    fingerprint: str


class ExperimentLedger:
    """One SQLite file per experiment, with serialized, durable appends."""

    def __init__(self, path: Path, experiment_id: str) -> None:
        if not experiment_id.strip():
            raise ValueError("Experiment id is required")
        self.path = path
        self.experiment_id = experiment_id
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db, db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS identity (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    experiment_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS entries (seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL, app_id TEXT NOT NULL, data BLOB NOT NULL,
                    disposition TEXT NOT NULL, reason TEXT NOT NULL, fingerprint TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS entries_no_update BEFORE UPDATE ON entries
                    BEGIN SELECT RAISE(ABORT, 'experiment entries are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS entries_no_delete BEFORE DELETE ON entries
                    BEGIN SELECT RAISE(ABORT, 'experiment entries are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS identity_no_update BEFORE UPDATE ON identity
                    BEGIN SELECT RAISE(ABORT, 'experiment identity is immutable'); END;
                CREATE TRIGGER IF NOT EXISTS identity_no_delete BEFORE DELETE ON identity
                    BEGIN SELECT RAISE(ABORT, 'experiment identity is immutable'); END;
                """
            )
            db.execute("INSERT OR IGNORE INTO identity VALUES (1, ?)", (experiment_id,))
            if db.execute("SELECT experiment_id FROM identity").fetchone() != (experiment_id,):
                raise ValueError("Notebook belongs to a different experiment")
        self.records()  # Reject corruption before admitting any new evidence.

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def _fingerprint(
        self, seq: int, run_id: str, app_id: str, data: bytes, disposition: str, reason: str
    ) -> str:
        return fingerprint(
            {
                "experiment_id": self.experiment_id,
                "seq": seq,
                "run_id": run_id,
                "app_id": app_id,
                "data_sha256": sha256(data).hexdigest(),
                "disposition": disposition,
                "reason": reason,
            }
        )

    def append(self, data: bytes, *, run_id: str, app_id: str) -> ExperimentEntry:
        if not run_id.strip() or not app_id.strip():
            raise ValueError("Run id and app id are required")
        reason = _invalid_evidence(data)
        disposition = "quarantine" if reason else "evidence"
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            seq = db.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM entries").fetchone()[0]
            digest = self._fingerprint(seq, run_id, app_id, data, disposition, reason)
            db.execute(
                "INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?)",
                (seq, run_id, app_id, data, disposition, reason, digest),
            )
        if reason:
            raise EvidenceRejected(reason)
        return ExperimentEntry(seq, run_id, app_id, data, disposition, reason, digest)

    def records(self) -> tuple[ExperimentEntry, ...]:
        with closing(self._connect()) as db:
            rows = db.execute("SELECT * FROM entries ORDER BY seq").fetchall()
        entries = tuple(ExperimentEntry(*row) for row in rows)
        for expected, entry in enumerate(entries, 1):
            if entry.seq != expected or entry.fingerprint != self._fingerprint(
                entry.seq, entry.run_id, entry.app_id, entry.data, entry.disposition, entry.reason
            ):
                raise ValueError("Experiment notebook identity, evidence or sequence is corrupt")
        return entries


def _invalid_evidence(data: bytes) -> str:
    try:
        raw: object = json.loads(data)
        if not isinstance(raw, dict) or not raw:
            return "Evidence must be a nonempty JSON object"
        body = cast("dict[str, object]", raw)
        encoded(body)  # Reject non-finite numbers rather than admitting nonstandard JSON.
        for key, value in body.items():
            if not key.strip():
                return "Evidence keys must be nonempty strings"
            field_name = key.strip().casefold().replace("-", "_")
            if field_name.endswith("_ref"):
                if not isinstance(value, str) or not value.strip():
                    return "Evidence references must be nonempty strings"
            elif field_name in {"note", "kind"}:
                if not isinstance(value, str):
                    return "Evidence metadata must be text"
            elif field_name == "workbench_lane":
                if not isinstance(value, str) or value.strip().casefold() != "coordinated":
                    return "The experiment notebook is coordinated; QMB owns governed evidence"
            else:
                return "Store evidence references and small metadata, never copied run ledgers"
    except ValueError, TypeError, UnicodeDecodeError, RecursionError:
        return "Evidence is not valid JSON"
    return ""
