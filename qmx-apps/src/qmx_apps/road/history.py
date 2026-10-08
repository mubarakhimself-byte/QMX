"""Reuse the run journal; catalog rows never authorize publication."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import cast

from qmx_agents.guards.journal import RunJournal, encoded

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition
from qmx_apps.road.models import STAGES, Evidence, Stage, json_document
from qmx_apps.volume import Volume, VolumeLease


@dataclass
class History:
    journal: RunJournal
    records: list[Document] = field(default_factory=list[Document])
    head: str | None = None
    stages: dict[str, Stage] = field(default_factory=dict[str, Stage])
    publications: list[Document] = field(default_factory=list[Document])

    @property
    def active(self) -> Document | None:
        return self.publications[-1] if self.publications else None

    def accept(self, evidence: Evidence, revision: str) -> None:
        definition_hash = evidence.definition_hash
        if evidence.stage == "build":
            if (
                not evidence.passed
                or evidence.parent != self.head
                or definition_hash in self.stages
                or any(
                    record["stage"] == "build" and record["version"] == evidence.version
                    for record in self.records
                )
            ):
                raise ValueError("Invalid immutable version chain")
            self.head = definition_hash
            self.stages[definition_hash] = "build"
        elif evidence.stage == "live":
            if evidence.action not in {"publish", "rollback"}:
                raise ValueError("Live requires a publication action")
            current = str(self.active["revision"]) if self.active else None
            if evidence.expected_active != current or self.stages.get(definition_hash) not in {
                "shadow",
                "live",
            }:
                raise ValueError("Publication lacks current shadow evidence or CAS")
            if evidence.passed:
                if evidence.action == "rollback":
                    previous = [
                        p for p in self.publications[:-1] if p["definition_hash"] == definition_hash
                    ]
                    if not previous:
                        raise ValueError("Rollback requires an earlier publication")
                elif definition_hash != self.head:
                    raise ValueError("Publication is not the candidate head")
                self.stages[definition_hash] = "live"
        else:
            current_stage = self.stages.get(definition_hash)
            if (
                definition_hash != self.head
                or current_stage is None
                or STAGES.index(evidence.stage) != STAGES.index(current_stage) + 1
            ):
                raise ValueError("Out-of-order or stale evidence")
            if evidence.passed:
                self.stages[definition_hash] = evidence.stage
        record = {**evidence.document(), "revision": revision}
        self.records.append(record)
        if evidence.stage == "live" and evidence.passed:
            self.publications.append(record)

    def append(self, evidence: Evidence) -> Document:
        # Validate before writing, using the same replay rules as restart.
        trial = History(
            self.journal, list(self.records), self.head, dict(self.stages), list(self.publications)
        )
        trial.accept(evidence, "pending")
        data = encoded(evidence)
        reference = (
            Path(self.journal.store_result(data)).relative_to(self.journal.path.parent).as_posix()
        )
        record = self.journal.append("app_step", {"result_ref": reference, "byte_count": len(data)})
        self.accept(evidence, str(record["fingerprint"]))
        return self.records[-1]


@contextmanager
def history(home: Path, app_id: str) -> Generator[History]:
    volume = Volume(home, app_id)
    lease = VolumeLease(home / "road-locks", app_id)
    path = volume.root / "road/steps.jsonl"
    try:
        # The OS lease proves no writer survived; recover a crashed journal lock.
        path.with_suffix(".jsonl.lock").unlink(missing_ok=True)
        with RunJournal(path, app_id) as journal:
            state = History(journal)
            for line in path.read_bytes().splitlines() if path.exists() else []:
                envelope = json_document(line)
                if envelope["event"] != "app_step":
                    raise ValueError("Unexpected road event")
                payload = cast(Document, envelope["payload"])
                reference = str(payload["result_ref"])
                folder, _, digest = reference.partition("/")
                if (
                    folder != "steps.jsonl.results"
                    or len(digest) != 64
                    or any(c not in "0123456789abcdef" for c in digest)
                ):
                    raise ValueError("Invalid result reference")
                data = (path.parent / reference).read_bytes()
                if sha256(data).hexdigest() != digest or len(data) != payload["byte_count"]:
                    raise ValueError("Evidence bytes changed")
                evidence = Evidence.model_validate(json_document(data))
                image = definition(home, app_id, evidence.definition_hash)
                if image.manifest.version != evidence.version:
                    raise ValueError("Evidence version differs from its image")
                if evidence.versions.get("definition") != image.hash:
                    raise ValueError("Evidence inputs differ from their immutable version")
                state.accept(evidence, str(envelope["fingerprint"]))
            yield state
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise AppError(
            "road_corrupt", "Road history or its evidence failed verified replay.", 409
        ) from error
    finally:
        lease.close()


def definition(home: Path, app_id: str, definition_hash: str) -> Definition:
    if len(definition_hash) != 64 or any(c not in "0123456789abcdef" for c in definition_hash):
        raise AppError("invalid_revision", "Use an installed definition hash.")
    image = Definition.load(home / "definitions" / definition_hash)
    if image.hash != definition_hash or image.manifest.id != app_id:
        raise AppError("definition_corrupt", "Immutable definition identity changed.", 409)
    return image


def project(home: Path, app_id: str, state: History) -> None:
    # These are P12's disposable rows. Full history is checked before repairing them.
    with closing(sqlite3.connect(home / "apps.db")) as db, db:
        for record in state.records:
            if record["stage"] == "build":
                db.execute(
                    "INSERT OR IGNORE INTO definitions VALUES(?,?,?,?)",
                    (app_id, record["version"], record["definition_hash"], record["trust"]),
                )
        if state.head:
            db.execute(
                "INSERT INTO selected VALUES(?,?) ON CONFLICT(id) DO UPDATE SET hash=excluded.hash",
                (app_id, state.head),
            )
        if state.active:
            db.execute(
                "INSERT INTO active VALUES(?,?,?) ON CONFLICT(id) "
                "DO UPDATE SET hash=excluded.hash, revision=excluded.revision",
                (app_id, state.active["definition_hash"], state.active["revision"]),
            )
        else:
            db.execute("DELETE FROM active WHERE id=?", (app_id,))
