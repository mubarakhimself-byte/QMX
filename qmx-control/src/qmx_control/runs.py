"""Rebuildable run projections over immutable P08 journal records."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from qmx_control.library import encoded
from qmx_control.models import ControlError, Document


class RunIndex:
    def __init__(self, home: Path) -> None:
        self.home = home
        with closing(sqlite3.connect(home / "runs.db")) as db, db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS journals(path TEXT PRIMARY KEY,digest TEXT NOT NULL,
                    size INTEGER NOT NULL);
            """)

    def record(self, run_id: str, data: Document) -> Document:
        with closing(sqlite3.connect(self.home / "runs.db", timeout=5)) as db, db:
            row = db.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
            previous = cast(Document, json.loads(row[0])) if row else {}
            result: Document = {
                "id": run_id,
                "kind": "agent",
                "target": None,
                "node": None,
                "model": {},
                "status": "running",
                "cost": None,
                "started": None,
                "ended": None,
                "artifacts": [],
                **previous,
                **data,
            }
            result["id"] = run_id
            db.execute(
                "INSERT INTO runs VALUES(?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                (run_id, json.dumps(result)),
            )
        return result

    def refresh(self) -> list[Document]:
        changed: list[Document] = []
        paths = sorted(
            {
                *self.home.glob("runs/**/*.jsonl"),
                *self.home.glob("journals/**/*.jsonl"),
            }
        )
        for path in paths:
            body = path.read_bytes()
            # A live writer may be between write() calls; only project complete records.
            complete = body[: body.rfind(b"\n") + 1]
            digest = sha256(complete).hexdigest()
            with closing(sqlite3.connect(self.home / "runs.db", timeout=5)) as db:
                seen = db.execute(
                    "SELECT digest,size FROM journals WHERE path=?", (str(path),)
                ).fetchone()
            if seen and seen[0] == digest:
                continue
            if seen and (
                len(complete) < seen[1] or sha256(complete[: seen[1]]).hexdigest() != seen[0]
            ):
                raise ControlError(
                    "invalid_journal", f"Run journal was rewritten: {path.name}.", 409
                )
            if not complete:
                continue
            run_id = ""
            data: Document = {"model": {}, "artifacts": []}
            models: Document = {}
            artifacts: list[str] = []
            cost: Decimal | None = None
            try:
                for seq, line in enumerate(complete.splitlines(), 1):
                    record = cast(JsonValue, json.loads(line))
                    if not isinstance(record, dict):
                        raise ValueError("Record must be an object")
                    fingerprint = record.pop("fingerprint")
                    if fingerprint != sha256(encoded(record)).hexdigest() or record["seq"] != seq:
                        raise ValueError("Fingerprint or sequence mismatch")
                    identity = record["run_id"]
                    if not isinstance(identity, str) or not identity.strip():
                        raise ValueError("Run identity is missing")
                    if run_id and identity != run_id:
                        raise ValueError("Run identity changed")
                    run_id = identity
                    payload = record["payload"]
                    if not isinstance(payload, dict):
                        raise ValueError("Payload must be an object")
                    event = record["event"]
                    if event == "run_start":
                        data.setdefault("started", record["time"])
                        data["status"] = "running"
                        data["ended"] = None
                        for field in (
                            "kind",
                            "target",
                            "node",
                            "app_id",
                            "workflow_id",
                            "session_id",
                        ):
                            if field in payload:
                                data[field] = payload[field]
                    elif event == "run_end":
                        data["status"] = payload["status"]
                        data["ended"] = record["time"]
                    elif event == "model_call":
                        models[str(payload.get("agent", "primary"))] = payload.get("model")
                        metadata = payload.get("metadata")
                        if isinstance(metadata, dict) and metadata.get("cost") is not None:
                            cost = (cost or Decimal(0)) + Decimal(str(metadata["cost"]))
                    reference = payload.get("artifact_ref", payload.get("result_ref"))
                    if isinstance(reference, str) and reference not in artifacts:
                        artifacts.append(reference)
                data.update(
                    {
                        "model": models,
                        "artifacts": list(artifacts),
                        "cost": str(cost) if cost is not None else None,
                        "journal": str(path),
                    }
                )
            except (KeyError, ValueError, TypeError, ArithmeticError) as error:
                raise ControlError(
                    "invalid_journal", f"Invalid run journal: {path.name}.", 409
                ) from error
            result = self.record(run_id, data)
            with closing(sqlite3.connect(self.home / "runs.db", timeout=5)) as db, db:
                db.execute(
                    "INSERT OR REPLACE INTO journals VALUES(?,?,?)",
                    (str(path), digest, len(complete)),
                )
            changed.append(result)
        return changed

    def get(self, run_id: str) -> Document:
        with closing(sqlite3.connect(self.home / "runs.db", timeout=5)) as db:
            row = db.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise ControlError("not_found", "Unknown run id.", 404)
        return cast(Document, json.loads(row[0]))

    def list(self, offset: int, limit: int) -> list[Document]:
        with closing(sqlite3.connect(self.home / "runs.db", timeout=5)) as db:
            rows = db.execute(
                "SELECT data FROM runs ORDER BY rowid LIMIT ? OFFSET ?",
                (
                    limit,
                    offset,
                ),
            ).fetchall()
        return [cast(Document, json.loads(row[0])) for row in rows]
