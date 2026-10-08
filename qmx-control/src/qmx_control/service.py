"""Persistent platform operations, independent of either transport."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
import tomllib
import uuid
from collections.abc import AsyncIterator, Callable, Generator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Literal, cast

import keyring
import tomli_w
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from qmx_apps.backup import BackupSettings, backup, restore
from qmx_apps.backup_schedule import BackupSchedule
from qmx_apps.docker import DockerSupervisor
from qmx_apps.manifest import Trust
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import Volume

type Document = dict[str, JsonValue]
type SettingsSection = Literal["providers", "mcp_servers", "budgets", "memory_provider", "backup"]
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
    def __init__(
        self,
        home: Path,
        *,
        tier: Literal["T1", "T2"] = "T1",
        node: str = "laptop",
        secret_getter: Callable[[str, str], str | None] = keyring.get_password,
    ) -> None:
        self.home = home.resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._cancellers: dict[tuple[WorkKind, str], Callable[[], None]] = {}
        self._apps: Supervisor | None = None
        self._backup_lock = threading.Lock()
        self._backup_schedule: BackupSchedule | None = None
        self.tier = tier
        self.node = node
        self.secret_getter = secret_getter
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
        if section == "backup":
            BackupSettings.model_validate(values).destination("validation", "validation")
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

    def record_work(
        self,
        kind: WorkKind,
        work_id: str,
        data: Document,
        cancel: Callable[[], None] | None = None,
    ) -> Document:
        """Called by the owner of a real run or job to publish its state."""
        with self._lock, self._connect() as db:
            if cancel is not None:
                self._cancellers[kind, work_id] = cancel
            if data.get("status") in {
                "complete",
                "completed",
                "failed",
                "cancelled",
                "canceled",
                "stopped",
            }:
                self._cancellers.pop((kind, work_id), None)
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
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT data FROM work WHERE kind=? AND id=?", (kind, work_id)
            ).fetchone()
            if row is None:
                raise ControlError("not_found", f"Unknown {kind} id.", 404)
            data = _document(row[0])
            if data.get("status") in {
                "complete",
                "completed",
                "failed",
                "cancelled",
                "canceled",
                "stopped",
            }:
                return {**data, "id": work_id}
            cancel = self._cancellers.get((kind, work_id))
        if cancel is None:
            return self._unavailable(f"{kind}.cancel", "a connected run/job owner (P12/P22)")
        try:
            cancel()
        except Exception as error:
            raise ControlError(
                "cancel_failed", "The work owner could not accept cancellation.", 409
            ) from error
        result: Document = {"id": work_id, "status": "cancel_requested"}
        with self._lock, self._connect() as db:
            self._event(db, kind, work_id, result)
        return result

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
        """List installed definitions and their actual runtime state."""
        return self.app_runtime().list()

    def apps_get(self, app_id: str) -> Document:
        """Read an app definition and runtime status."""
        return self.app_runtime().get(app_id)

    def apps_create(self, path: str, trust: Trust = "agent") -> Document:
        """Install an app definition from a local package directory."""
        return self.app_runtime().install(Path(path), trust=trust)

    def apps_update(self, app_id: str, path: str, trust: Trust = "agent") -> Document:
        """Install a new immutable version of an app."""
        return self.app_runtime().install(Path(path), trust=trust, expected_id=app_id)

    def apps_versions(self, app_id: str) -> list[Document]:
        """List immutable app definitions."""
        return self.app_runtime().versions(app_id)

    def apps_test(self, app_id: str) -> Document:
        """Run road-to-live validation (requires P14)."""
        return self._unavailable("apps.test", "P14")

    def apps_publish(self, app_id: str) -> Document:
        """Publish after road-to-live evidence (requires P14)."""
        return self._unavailable("apps.publish", "P14")

    def apps_start(self, app_id: str) -> Document:
        """Start an installed app instance."""
        return self.app_runtime().start(app_id)

    def apps_stop(self, app_id: str) -> Document:
        """Stop an app's process tree."""
        return self.app_runtime().stop(app_id)

    def apps_logs(self, app_id: str, limit: int = 100) -> list[Document]:
        """Read structured app logs."""
        return self.app_runtime().logs(app_id, limit)

    def apps_restart(self, app_id: str) -> Document:
        """Restart the selected immutable definition, retaining its volume."""
        return self.app_runtime().restart(app_id)

    def apps_registry(self) -> list[Document]:
        """Discover connected MCP servers and their tools and resources."""
        return self.app_runtime().registry()

    def apps_call(self, app_id: str, tool: str, arguments: Document) -> Document:
        """Call a connected app; feed arguments must be registered artifact refs."""
        return self.app_runtime().call(app_id, tool, arguments)

    def apps_resource(self, app_id: str, uri: str) -> list[Document]:
        """Read an app's MCP resource, including ui:// panels."""
        return self.app_runtime().resource(app_id, uri)

    def app_runtime(self) -> Supervisor:
        with self._lock:
            if self._apps is None:
                if self.tier == "T2":
                    providers = self.settings_get("providers")
                    replica_settings = providers.get("litestream", {})
                    replicas = (
                        {
                            name: url
                            for name, url in replica_settings.items()
                            if isinstance(url, str)
                        }
                        if isinstance(replica_settings, dict)
                        else {}
                    )
                    self._apps = DockerSupervisor(
                        self.home,
                        node=self.node,
                        replicas=replicas,
                        event_sink=self._app_event,
                        secret_getter=self.secret_getter,
                    )
                else:
                    self._apps = Supervisor(
                        self.home,
                        event_sink=self._app_event,
                        secret_getter=self.secret_getter,
                    )
                self._backup_schedule = BackupSchedule(
                    self._backup_settings,
                    self._backup_apps,
                    self.apps_backup,
                    self._backup_failed,
                )
            return self._apps

    def _backup_settings(self) -> BackupSettings | None:
        values = self.settings_get("backup")
        return BackupSettings.model_validate(values) if values else None

    def _backup_apps(self) -> list[str]:
        return [
            str(item["definition"]["id"])
            for item in self.apps_list()
            if isinstance(item["definition"], dict)
            and Volume(self.home, str(item["definition"]["id"])).root.joinpath("app.db").is_file()
        ]

    def _backup_failed(self, app_id: str, error: Exception) -> None:
        with self._lock, self._connect() as db:
            self._event(
                db, "apps", app_id, {"type": "backup_failed", "error": type(error).__name__}
            )

    def apps_backup(self, app_id: str) -> Document:
        """Back up now using the UI-editable remote and verify a downloaded restore."""
        self.app_runtime().get(app_id)
        settings = self._backup_settings()
        if settings is None:
            raise ControlError(
                "backup_unconfigured", "Configure the backup remote in Settings.", 409
            )
        with self._backup_lock:
            result = backup(Volume(self.home, app_id), settings)
        with self._lock, self._connect() as db:
            self._event(db, "apps", app_id, {"type": "backup", **result})
        return result

    def apps_restore(self, app_id: str, snapshot_id: str) -> Document:
        """Verify and replace a stopped app's volume from a backup snapshot."""
        self.app_runtime().get(app_id)
        settings = self._backup_settings()
        if settings is None:
            raise ControlError(
                "backup_unconfigured", "Configure the backup remote in Settings.", 409
            )
        with self._backup_lock:
            result = restore(self.home, app_id, settings, snapshot_id)
        with self._lock, self._connect() as db:
            self._event(db, "apps", app_id, {"type": "restored", **result})
        return result

    def _app_event(self, app_id: str, data: Document) -> None:
        with self._lock, self._connect() as db:
            self._event(db, "apps", app_id, data)
        instance_id = data.get("instance_id")
        if isinstance(instance_id, str):
            status = data.get("status")
            work = {**data, "status": "failed" if status == "tripped" else status}

            def cancel() -> None:
                self.apps_stop(app_id)

            self.record_work(
                "jobs", instance_id, work, cancel=cancel if status == "running" else None
            )

    def close(self) -> None:
        if self._backup_schedule is not None:
            self._backup_schedule.close()
            self._backup_schedule = None
        if self._apps is not None:
            self._apps.close()
            self._apps = None

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
