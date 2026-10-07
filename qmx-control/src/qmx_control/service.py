"""Persistent platform operations, independent of either transport."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
import tomllib
import uuid
from collections.abc import AsyncIterator, Generator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Literal, cast

import tomli_w
from pydantic import BaseModel, ConfigDict, Field, JsonValue

type Document = dict[str, JsonValue]
type SettingsSection = Literal["providers", "mcp_servers", "budgets", "memory_provider"]
type EventTopic = Literal["runs", "jobs", "sessions", "apps", "library", "settings"]
type WorkKind = Literal["runs", "jobs"]


class ControlError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status

    def document(self) -> Document:
        return {"error": {"code": self.code, "message": str(self)}}


class SessionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    origin: str = Field(default="copilot", min_length=1)
    parent_id: str | None = None


class SessionBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal[
        "user",
        "text",
        "plan",
        "agents",
        "tool",
        "changed",
        "artifact",
        "table",
        "entity",
        "question",
        "permission",
        "panel",
        "handoff",
    ]
    content: Document


class LibraryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    kind: str = Field(min_length=1)
    content: Document


def _document(value: str) -> Document:
    return cast(Document, json.loads(value))


def _no_secrets(value: JsonValue) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = key.lower().replace("_", "").replace("-", "")
            if normalized in {"key", "apikey", "token", "password", "secret", "clientkey"}:
                raise ControlError(
                    "secret_ref_required",
                    "Store secrets in Credential Manager; use credential_ref.",
                )
            _no_secrets(item)
    elif isinstance(value, list):
        for item in value:
            _no_secrets(item)


class ControlService:
    def __init__(self, home: Path) -> None:
        self.home = home.resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS blocks (session_id TEXT NOT NULL, seq INTEGER NOT NULL,
                    data TEXT NOT NULL, PRIMARY KEY(session_id, seq));
                CREATE TABLE IF NOT EXISTS library (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS work (kind TEXT NOT NULL, id TEXT NOT NULL,
                    data TEXT NOT NULL, PRIMARY KEY(kind, id));
                CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL, subject TEXT NOT NULL, data TEXT NOT NULL);
            """)

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.home / "control.db", timeout=5)) as db, db:
            yield db

    def _event(
        self, db: sqlite3.Connection, topic: EventTopic, subject: str, data: Document
    ) -> None:
        db.execute(
            "INSERT INTO events(topic,subject,data) VALUES(?,?,?)",
            (topic, subject, json.dumps(data)),
        )

    def events(
        self, topic: EventTopic, after: int = 0, subject: str = "", limit: int = 100
    ) -> list[Document]:
        if after < 0 or not 1 <= limit <= 1000:
            raise ControlError("invalid_cursor", "Use after >= 0 and limit between 1 and 1000.")
        with self._connect() as db:
            rows = db.execute(
                "SELECT seq,subject,data FROM events WHERE topic=? AND seq>? "
                "AND (?='' OR subject=?) ORDER BY seq LIMIT ?",
                (topic, after, subject, subject, limit),
            ).fetchall()
        return [
            {"id": row[0], "topic": topic, "subject": row[1], "data": _document(row[2])}
            for row in rows
        ]

    async def stream(
        self, topic: EventTopic, after: int = 0, subject: str = "", max_events: int = 0
    ) -> AsyncIterator[Document]:
        count = 0
        while True:
            for event in self.events(topic, after, subject):
                after = cast(int, event["id"])
                yield event
                count += 1
                if max_events and count >= max_events:
                    return
            await asyncio.sleep(0.05)

    def settings_get(self, section: SettingsSection) -> Document:
        """Read UI-editable provider, MCP, budget or memory settings."""
        with self._lock:
            path = self.home / "settings.toml"
            if not path.exists():
                return {}
            with path.open("rb") as file:
                settings = tomllib.load(file)
            return cast(Document, settings.get(section, {}))

    def settings_put(self, section: SettingsSection, values: Document) -> Document:
        """Replace a settings section; credentials must be vault references."""
        _no_secrets(values)
        with self._lock:
            path = self.home / "settings.toml"
            settings: Document = {}
            if path.exists():
                with path.open("rb") as file:
                    settings = cast(Document, tomllib.load(file))
            settings[section] = values
            try:
                encoded = tomli_w.dumps(settings)
            except (TypeError, ValueError) as error:
                raise ControlError(
                    "invalid_settings", "Settings must contain TOML-compatible values (no nulls)."
                ) from error
            temporary = path.with_suffix(".tmp")
            temporary.write_text(encoded, encoding="utf-8")
            temporary.replace(path)
            with self._connect() as db:
                self._event(db, "settings", section, {"section": section})
        return values

    def sessions_create(self, session: SessionInput) -> Document:
        """Create a durable Copilot session, optionally a child session."""
        with self._lock, self._connect() as db:
            if (
                session.parent_id
                and db.execute("SELECT 1 FROM sessions WHERE id=?", (session.parent_id,)).fetchone()
                is None
            ):
                raise ControlError("not_found", "Parent session does not exist.", 404)
            session_id = str(uuid.uuid4())
            data: Document = {"id": session_id, **session.model_dump(mode="json")}
            db.execute("INSERT INTO sessions VALUES(?,?)", (session_id, json.dumps(data)))
            self._event(db, "sessions", session_id, {"type": "created", "session": data})
        return data

    def sessions_list(self, offset: int = 0, limit: int = 100) -> list[Document]:
        """List saved sessions, including their origin and parent."""
        self._page(offset, limit)
        with self._connect() as db:
            rows = db.execute(
                "SELECT data FROM sessions ORDER BY rowid LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()
        return [_document(row[0]) for row in rows]

    def sessions_append(self, session_id: str, block: SessionBlock) -> Document:
        """Append a typed block; history is never rewritten."""
        with self._lock, self._connect() as db:
            if db.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
                raise ControlError("not_found", "Session does not exist.", 404)
            seq = db.execute(
                "SELECT COALESCE(MAX(seq),0)+1 FROM blocks WHERE session_id=?", (session_id,)
            ).fetchone()[0]
            data: Document = {"seq": seq, **block.model_dump(mode="json")}
            db.execute("INSERT INTO blocks VALUES(?,?,?)", (session_id, seq, json.dumps(data)))
            self._event(db, "sessions", session_id, {"type": "block", "block": data})
        return data

    def sessions_stream(self, session_id: str, after: int = 0, limit: int = 100) -> list[Document]:
        """Read a page of session events. REST also offers a continuous SSE stream."""
        with self._connect() as db:
            if db.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
                raise ControlError("not_found", "Session does not exist.", 404)
        return self.events("sessions", after, session_id, limit)

    def library_save(self, item: LibraryInput) -> Document:
        """Save a typed Library item and its content."""
        item_id = str(uuid.uuid4())
        data: Document = {"id": item_id, **item.model_dump(mode="json")}
        with self._lock, self._connect() as db:
            db.execute("INSERT INTO library VALUES(?,?)", (item_id, json.dumps(data)))
            self._event(db, "library", item_id, {"type": "saved", "item_id": item_id})
        return data

    def library_search(self, query: str = "", offset: int = 0, limit: int = 100) -> list[Document]:
        """Search saved Library titles and content with pagination."""
        self._page(offset, limit)
        with self._connect() as db:
            rows = db.execute(
                "SELECT data FROM library WHERE instr(lower(data),lower(?))>0 "
                "ORDER BY rowid LIMIT ? OFFSET ?",
                (query, limit, offset),
            ).fetchall()
        return [_document(row[0]) for row in rows]

    @staticmethod
    def _page(offset: int, limit: int) -> None:
        if offset < 0 or not 1 <= limit <= 1000:
            raise ControlError("invalid_page", "Use offset >= 0 and limit between 1 and 1000.")

    def record_work(self, kind: WorkKind, work_id: str, data: Document) -> Document:
        """Called by the owner of a real run or job to publish its state."""
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO work VALUES(?,?,?) ON CONFLICT(kind,id) "
                "DO UPDATE SET data=excluded.data",
                (kind, work_id, json.dumps(data)),
            )
            self._event(db, kind, work_id, data)
        return data

    def _work_list(self, kind: WorkKind, offset: int, limit: int) -> list[Document]:
        self._page(offset, limit)
        with self._connect() as db:
            rows = db.execute(
                "SELECT id,data FROM work WHERE kind=? ORDER BY rowid LIMIT ? OFFSET ?",
                (kind, limit, offset),
            ).fetchall()
        return [{**_document(row[1]), "id": row[0]} for row in rows]

    def runs_list(self, offset: int = 0, limit: int = 100) -> list[Document]:
        """List recorded runs; an empty installation has no runs."""
        return self._work_list("runs", offset, limit)

    def jobs_list(self, offset: int = 0, limit: int = 100) -> list[Document]:
        """List recorded background jobs."""
        return self._work_list("jobs", offset, limit)

    def _cancel(self, kind: WorkKind, work_id: str) -> Document:
        with self._connect() as db:
            if (
                db.execute("SELECT 1 FROM work WHERE kind=? AND id=?", (kind, work_id)).fetchone()
                is None
            ):
                raise ControlError("not_found", f"Unknown {kind} id.", 404)
        return self._unavailable(f"{kind}.cancel", "P12/P22")

    def runs_cancel(self, run_id: str) -> Document:
        """Cancel a run through its owner; unavailable until the runner is connected."""
        return self._cancel("runs", run_id)

    def jobs_cancel(self, job_id: str) -> Document:
        """Cancel a job through its owner; unavailable until the runner is connected."""
        return self._cancel("jobs", job_id)

    @staticmethod
    def _unavailable(operation: str, packet: str = "P12-P14") -> Document:
        raise ControlError(
            "not_implemented", f"{operation} is not available yet; requires {packet}.", 501
        )

    def apps_list(self) -> list[Document]:
        """List installed apps (requires the mini-app supervisor)."""
        self._unavailable("apps.list")
        return []

    def apps_get(self, app_id: str) -> Document:
        """Read an app definition and runtime status."""
        return self._unavailable("apps.get")

    def apps_create(self, path: str) -> Document:
        """Install an app definition from a local package directory."""
        return self._unavailable("apps.create")

    def apps_update(self, app_id: str, path: str) -> Document:
        """Install a new immutable version of an app."""
        return self._unavailable("apps.update")

    def apps_versions(self, app_id: str) -> list[Document]:
        """List immutable app definitions."""
        self._unavailable("apps.versions")
        return []

    def apps_test(self, app_id: str) -> Document:
        """Run road-to-live validation (requires P14)."""
        return self._unavailable("apps.test", "P14")

    def apps_publish(self, app_id: str) -> Document:
        """Publish after road-to-live evidence (requires P14)."""
        return self._unavailable("apps.publish", "P14")

    def apps_start(self, app_id: str) -> Document:
        """Start an installed app instance."""
        return self._unavailable("apps.start")

    def apps_stop(self, app_id: str) -> Document:
        """Stop an app's process tree."""
        return self._unavailable("apps.stop")

    def apps_logs(self, app_id: str, limit: int = 100) -> list[Document]:
        """Read structured app logs."""
        self._unavailable("apps.logs")
        return []

    def apps_evidence(self, app_id: str) -> list[Document]:
        """Read app evidence records (requires P14)."""
        self._unavailable("apps.evidence", "P14")
        return []

    def workflows_get(self, workflow_id: str) -> Document:
        """Read a workflow definition."""
        return self._unavailable("workflows.get", "P10")

    def workflows_put(self, workflow_id: str, graph: Document) -> Document:
        """Save a workflow graph."""
        return self._unavailable("workflows.put", "P10")

    def workflows_validate(self, graph: Document) -> Document:
        """Validate a workflow graph."""
        return self._unavailable("workflows.validate", "P10")

    def workflows_run(self, workflow_id: str) -> Document:
        """Run a compiled workflow."""
        return self._unavailable("workflows.run", "P10/P22")
