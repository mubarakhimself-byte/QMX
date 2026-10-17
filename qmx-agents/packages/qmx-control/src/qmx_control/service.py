"""Persistent platform operations, independent of either transport."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
import tomllib
import uuid
from collections.abc import AsyncIterator, Callable, Generator, Mapping
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Literal, NoReturn, cast
from urllib.parse import urlsplit

import keyring
import tomli_w
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from qmx_apps.backup import BackupSettings, backup, restore
from qmx_apps.backup_schedule import BackupSchedule
from qmx_apps.docker import DockerSupervisor
from qmx_apps.manifest import Trust
from qmx_apps.road.models import Stage
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import Volume
from qmx_broker.models import BrokerSettings
from qmx_broker.service import read_proposals
from qmx_remote.models import RemoteSettings, RunBundle
from qmx_remote.runs import RemoteRuns

from qmx_control.backup import weekly_backup
from qmx_control.cache import read_cache
from qmx_control.library import Library
from qmx_control.models import ControlError as ControlError  # noqa: PLC0414 - public re-export
from qmx_control.models import Document, MemoKey
from qmx_control.models import LibraryInput as LibraryInput  # noqa: PLC0414 - public re-export
from qmx_control.runs import RunIndex

type SettingsSection = Literal[
    "providers",
    "mcp_servers",
    "budgets",
    "memory_provider",
    "backup",
    "brokers",
    "remote",
    "claude",
    "environment",
    "agents",
]
type SettingsParser = Callable[[Document, Document], Document]
"""(values written, section stored now) -> the section to store."""
HOST_SECTIONS: frozenset[SettingsSection] = frozenset({"claude", "environment"})
"""Sections only a host that registers a parser for them can write."""
ENGINE = "an attached workflow engine"
type EventTopic = Literal["runs", "jobs", "sessions", "apps", "library", "settings", "aggregates"]
type WorkKind = Literal["runs", "jobs"]


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
        "needs_you",
    ]
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
        settings_parsers: Mapping[SettingsSection, SettingsParser] | None = None,
    ) -> None:
        self.home = home.resolve()
        self.settings_parsers = dict(settings_parsers or {})
        self.home.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._cancellers: dict[tuple[WorkKind, str], Callable[[], None]] = {}
        self._app_hooks: dict[str, Callable[[str, Document], None]] = {}
        self._apps: Supervisor | None = None
        self._remote: RemoteRuns | None = None
        self._backup_lock = threading.Lock()
        self._backup_schedule: BackupSchedule | None = None
        self.tier = tier
        self.node = node
        self.secret_getter = secret_getter
        self.library = Library(self.home)
        self.run_index = RunIndex(self.home)
        self._aggregate = read_cache(ttl=5)(self._aggregate_read)
        with self._connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS blocks (session_id TEXT NOT NULL, seq INTEGER NOT NULL,
                    data TEXT NOT NULL, PRIMARY KEY(session_id, seq));
                CREATE TABLE IF NOT EXISTS work (kind TEXT NOT NULL, id TEXT NOT NULL,
                    data TEXT NOT NULL, PRIMARY KEY(kind, id));
                CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL, subject TEXT NOT NULL, data TEXT NOT NULL);
            """)
            db.execute("BEGIN IMMEDIATE")
            legacy_catalog = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='library'"
            ).fetchone()
            # Preserve IDs returned by the first service version when moving its catalog.
            old_items = (
                db.execute("SELECT id,data FROM library").fetchall() if legacy_catalog else []
            )
            for item_id, raw in old_items:
                try:
                    self.library.get(item_id)
                except ControlError as error:
                    if error.code != "not_found":
                        raise
                    item = _document(raw)
                    item.pop("id")
                    self.library.save(LibraryInput.model_validate(item), item_id=item_id)
            if legacy_catalog:
                db.execute("DROP TABLE library")
            for work_id, raw in db.execute("SELECT id,data FROM work WHERE kind='runs'").fetchall():
                self.run_index.record(work_id, _document(raw))

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.home / "control.db", timeout=5)) as db, db:
            yield db

    def _event(
        self, db: sqlite3.Connection, topic: EventTopic, subject: str, data: Document
    ) -> None:
        self._aggregate.cache_clear()
        cursor = db.execute(
            "INSERT INTO events(topic,subject,data) VALUES(?,?,?)",
            (topic, subject, json.dumps(data)),
        )
        if topic in {"runs", "jobs", "apps", "library"}:
            summary = self._aggregate_counts(db, cursor.lastrowid or 0)
            db.execute(
                "INSERT INTO events(topic,subject,data) VALUES('aggregates','',?)",
                (json.dumps(summary),),
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
            values: Document = {}
            if path.exists():
                with path.open("rb") as file:
                    values = cast(Document, tomllib.load(file).get(section, {}))
            if section == "mcp_servers":
                firecrawl = values.get("firecrawl", {})
                if not isinstance(firecrawl, dict):
                    raise ControlError("invalid_settings", "Firecrawl settings must be a table.")
                values["firecrawl"] = {
                    "url": "https://mcp.firecrawl.dev/v2/mcp",
                    "enabled": False,
                    "credential_ref": "qmx/firecrawl",
                    **firecrawl,
                }
            return values

    def settings_update(
        self, section: SettingsSection, change: Callable[[Document], Document]
    ) -> Document:
        """Read, change and write one section under the settings lock, so concurrent updates
        all land. Writes nothing when the change returns the section as it was."""
        with self._lock:
            current = self.settings_get(section)
            values = change(current)
            return values if values == current else self.settings_put(section, values)

    def settings_put(self, section: SettingsSection, values: Document) -> Document:
        """Replace a settings section; credentials must be vault references."""
        with self._lock:
            return self._settings_put(section, values)

    def _settings_put(self, section: SettingsSection, values: Document) -> Document:
        _no_secrets(values)
        if section in HOST_SECTIONS:
            parser = self.settings_parsers.get(section)
            if parser is None:
                raise ControlError(
                    "invalid_settings", f"The {section} section is written only by the QMA host."
                )
            values = parser(values, self.settings_get(section))
        if section == "remote":
            try:
                RemoteSettings.model_validate(values)
            except ValueError as error:
                raise ControlError(
                    "invalid_settings", "Use valid remote targets and bucket settings."
                ) from error
        if section == "mcp_servers" and "firecrawl" in values:
            firecrawl = values["firecrawl"]
            if not isinstance(firecrawl, dict) or set(firecrawl) - {
                "url",
                "enabled",
                "credential_ref",
            }:
                raise ControlError(
                    "invalid_settings", "Use Firecrawl url, enabled and credential_ref only."
                )
            try:
                url = urlsplit(str(firecrawl.get("url", "https://mcp.firecrawl.dev/v2/mcp")))
            except ValueError as error:
                raise ControlError("invalid_settings", "Firecrawl URL is malformed.") from error
            if (
                not isinstance(firecrawl.get("enabled", False), bool)
                or firecrawl.get("credential_ref", "qmx/firecrawl") != "qmx/firecrawl"
                or url.scheme != "https"
                or not url.hostname
                or any((url.username, url.password, url.query, url.fragment))
            ):
                raise ControlError(
                    "invalid_settings",
                    "Firecrawl needs HTTPS, an enabled boolean and qmx/firecrawl.",
                )
        if section == "backup":
            if "repository" in values:
                repository = values["repository"]
                if not isinstance(repository, str) or not repository.strip():
                    raise ControlError(
                        "invalid_settings", "Backup repository must be nonempty text."
                    )
            app_settings = {key: value for key, value in values.items() if key != "repository"}
            if app_settings:
                BackupSettings.model_validate(app_settings).destination("validation", "validation")
        elif section == "brokers":
            try:
                values = BrokerSettings.model_validate(values).model_dump(
                    mode="json", exclude_none=True
                )
            except ValueError as error:
                raise ControlError(
                    "invalid_brokers",
                    "Use valid brokers, connections and accounts with qmx/* vault references.",
                ) from error

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

    def portfolio_proposals(self, offset: int = 0, limit: int = 100) -> list[Document]:
        """Read unsigned broker proposals awaiting the operator's Portfolio signature."""
        return cast(list[Document], read_proposals(self.home, offset, limit))

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
        """Save an immutable artifact, optionally a new version or URL/date result."""
        with self._lock, self._connect() as db:
            data = self.library.save(item)
            self._event(db, "library", str(data["id"]), {"type": "saved", "item_id": data["id"]})
        return data

    def library_search(self, query: str = "", offset: int = 0, limit: int = 100) -> list[Document]:
        """FTS5 search over title, tags and extracted text, ordered by relevance."""
        return self.library.search(query, offset, limit)

    def library_get(self, artifact_id: str) -> Document:
        """Read an artifact with its verified blob content."""
        return self.library.get(artifact_id)

    def memoized_backtest(self, identity: MemoKey, produce: Callable[[], LibraryInput]) -> Document:
        """Reuse a deterministic backtest artifact, recording newly computed results."""
        produced = False

        def compute() -> LibraryInput:
            nonlocal produced
            item = produce()
            produced = True
            return item

        with self._lock:
            result = self.library.memoized(identity, compute)
            if produced:
                with self._connect() as db:
                    self._event(
                        db,
                        "library",
                        str(result["id"]),
                        {"type": "saved", "item_id": result["id"], "memo_key": result["memo_key"]},
                    )
        return result

    def library_versions(self, artifact_id: str) -> list[Document]:
        """Read an artifact's immutable version chain."""
        return self.library.versions(artifact_id)

    def library_link(self, source_id: str, target_id: str, relation: str = "related") -> Document:
        """Link two existing artifacts without changing their contents."""
        with self._lock, self._connect() as db:
            data = self.library.link(source_id, target_id, relation)
            self._event(db, "library", source_id, {"type": "linked", **data})
        return data

    def library_links(self, artifact_id: str) -> list[Document]:
        """Read incoming and outgoing artifact links."""
        return self.library.links(artifact_id)

    def backup_weekly(self, dry_run: bool = False) -> Document:
        """Snapshot small stores to the private backup repo in Settings, at most weekly."""
        settings = self.settings_get("backup")
        repository = settings.get("repository")
        if not isinstance(repository, str) or not repository:
            raise ControlError("backup_not_configured", "Set backup.repository in Settings.")
        try:
            result = weekly_backup(self.home, repository, dry_run=dry_run)
        except (OSError, sqlite3.Error) as error:
            raise ControlError(
                "backup_failed", "Snapshot creation failed; backup was not published.", 409
            ) from error
        if result["status"] in {"completed", "dry_run"}:
            self.record_work("jobs", "weekly-backup", {**result, "status": "completed"})
        return result

    def _aggregate_read(self, revision: int) -> Document:
        with self._connect() as db:
            return self._aggregate_counts(db, revision)

    def _aggregate_counts(self, db: sqlite3.Connection, revision: int) -> Document:
        statuses = [
            _document(row[0]).get("status")
            for row in db.execute("SELECT data FROM work WHERE kind='jobs'").fetchall()
        ]
        count = self.library.count()
        with closing(sqlite3.connect(self.home / "runs.db")) as index:
            runs = index.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        return {
            "revision": revision,
            "library_items": count,
            "runs": runs,
            "active_jobs": sum(status == "running" for status in statuses),
        }

    def aggregates_get(self) -> Document:
        """Read short-lived UI totals; event revisions invalidate the cached view."""
        self._refresh_runs()
        with self._lock, self._connect() as db:
            revision = db.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0]
            return cast(Document, self._aggregate(revision)).copy()

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
            if kind == "runs":
                data = self.run_index.record(work_id, data)
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
        self._page(offset, limit)
        self._refresh_runs()
        return self.run_index.list(offset, limit)

    def runs_get(self, run_id: str) -> Document:
        """Read a journal-indexed run, including resolved models and artifacts."""
        self._refresh_runs()
        return self.run_index.get(run_id)

    def remote_runtime(self) -> RemoteRuns:
        if self._remote is None:
            self._remote = RemoteRuns(
                self.home,
                RemoteSettings.model_validate(self.settings_get("remote")),
                secret_getter=self.secret_getter,
            )
        else:
            self._remote.settings = RemoteSettings.model_validate(self.settings_get("remote"))
        return self._remote

    def runs_start_remote(
        self, bundle: RunBundle, target: str | None = None, definition_path: str | None = None
    ) -> Document:
        """Send an immutable workflow, app, agent or job bundle to a configured target."""
        result = self.remote_runtime().start(
            bundle, target, Path(definition_path) if definition_path else None
        )
        return self._record_remote(result)

    def _record_remote(self, result: Document) -> Document:
        bundle = RunBundle.model_validate(result["bundle"])
        result.update(kind=bundle.kind, node=result["target"], model=bundle.model_profile)
        run_id = str(result["run_id"])
        recorded = self.record_work("runs", run_id, result)
        if bundle.kind == "job":
            self.record_work("jobs", run_id, recorded)
        return recorded

    def runs_status(self, run_id: str) -> Document:
        """Read actual remote status and publish it to the shared run index."""
        result = self.remote_runtime().status(run_id)
        return self._record_remote(result)

    def runs_logs(self, run_id: str) -> Document:
        """Read the remote worker's incremental, redacted logs."""
        return self.remote_runtime().logs(run_id)

    def runs_fetch(self, run_id: str) -> Document:
        """Verify remote output hashes, register artifacts and journal the fetch."""
        result = self.remote_runtime().fetch(run_id)
        artifacts = result["artifacts"]
        if not isinstance(artifacts, list):
            raise ControlError("invalid_remote_result", "Remote artifact list is invalid.")
        registered: list[JsonValue] = []
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise ControlError("invalid_remote_result", "Remote artifact entry is invalid.")
            if str(artifact["path"]).startswith("outputs/"):
                item = self.library_save(
                    LibraryInput(
                        title=str(artifact["path"]),
                        kind="remote-result",
                        content={
                            **artifact,
                            "path": str(Path(str(result["path"])) / str(artifact["path"])),
                        },
                        source="remote:" + run_id,
                        tags=["remote", run_id],
                    )
                )
                registered.append(item["id"])
        result["library_items"] = registered
        self.record_work("runs", run_id, {"status": result["status"], "artifacts": registered})
        if self.runs_get(run_id)["kind"] == "job":
            self.record_work("jobs", run_id, self.runs_get(run_id))
        return result

    def runs_resume(self, run_id: str, target: str | None = None) -> Document:
        """Restart an interrupted remote run from its verified LangGraph checkpoint."""
        result = self.remote_runtime().resume(run_id, target)
        return self._record_remote(result)

    def runs_stop(self, run_id: str) -> Document:
        """Stop remote work and remove its container or sandbox, including credentials."""
        result = self.remote_runtime().stop(run_id)
        return self._record_remote(result)

    def run_job(
        self, bundle: RunBundle, target: str | None = None, definition_path: str | None = None
    ) -> Document:
        """Place a job on a CPU or GPU target and record it automatically."""
        return self.runs_start_remote(bundle, target, definition_path)

    def job_status(self, run_id: str) -> Document:
        """Read a placed job's actual status."""
        return self.runs_status(run_id)

    def job_logs(self, run_id: str) -> Document:
        """Read a placed job's durable logs."""
        return self.runs_logs(run_id)

    def job_fetch(self, run_id: str) -> Document:
        """Fetch and register a placed job's verified results."""
        return self.runs_fetch(run_id)

    def _refresh_runs(self) -> None:
        with self._lock, self._connect() as db:
            for data in self.run_index.refresh():
                run_id = str(data["id"])
                db.execute(
                    "INSERT INTO work VALUES('runs',?,?) ON CONFLICT(kind,id) "
                    "DO UPDATE SET data=excluded.data",
                    (run_id, json.dumps(data)),
                )
                self._event(db, "runs", run_id, data)

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
    def _unavailable(operation: str, packet: str = "P12-P14") -> NoReturn:
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

    def apps_update(
        self, app_id: str, path: str, trust: Trust = "agent", expected_hash: str | None = None
    ) -> Document:
        """Install a new immutable version of an app."""
        return self.app_runtime().install(
            Path(path), trust=trust, expected_id=app_id, expected_hash=expected_hash
        )

    def apps_versions(self, app_id: str) -> list[Document]:
        """List immutable app definitions."""
        return self.app_runtime().versions(app_id)

    def apps_test(
        self,
        app_id: str,
        expected_hash: str | None = None,
        stage: Stage | None = None,
        auto_publish: bool = True,
    ) -> Document:
        """Run the next actual test, recorded sandbox or isolated shadow stage."""
        owner = self.app_runtime()
        current = str(owner.get(app_id)["definition_hash"])
        return owner.road.advance(
            app_id, expected_hash or current, stage, auto_publish=auto_publish
        )

    def apps_publish(
        self,
        app_id: str,
        expected_hash: str | None = None,
        expected_active: str | None = None,
        signature: str | None = None,
    ) -> Document:
        """Activate current proven code using publication CAS and risk rules."""
        owner = self.app_runtime()
        current = str(owner.get(app_id)["definition_hash"])
        return owner.road.publish(app_id, expected_hash or current, expected_active, signature)

    def apps_rollback(
        self, app_id: str, expected_active: str, signature: str | None = None
    ) -> Document:
        """Reactivate the previous publication as a new evidenced transition."""
        owner = self.app_runtime()
        return owner.road.publish(
            app_id,
            str(owner.get(app_id)["definition_hash"]),
            expected_active,
            signature,
            rollback=True,
        )

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
        result = self.app_runtime().call(app_id, tool, arguments)
        reference = result.get("artifact_ref")
        output = result.get("result")
        if isinstance(reference, dict) and isinstance(output, dict) and "data" in output:
            saved = self.library_save(
                LibraryInput(
                    title=f"{app_id}: {reference['output']}"[:200],
                    kind="app-output",
                    tags=[app_id, str(reference["output"])],
                    source=f"app://{app_id}/{reference['output']}/{reference['sha256']}",
                    content={"artifact_ref": reference, "data": output["data"]},
                )
            )
            result["library_id"] = saved["id"]
            result["library_ref"] = saved["ref"]
        return result

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
        values = {
            key: value for key, value in self.settings_get("backup").items() if key != "repository"
        }
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
        with self._lock:
            for hook in list(self._app_hooks.values()):
                hook(app_id, data)

    def watch_app_events(self, session_id: str, hook: Callable[[str, Document], None]) -> None:
        """Keep one subscription per session across agent rebuilds."""
        with self._lock:
            self._app_hooks.setdefault(session_id, hook)

    def notify_app(self, app_id: str, data: Document) -> None:
        """Publish an actionable operator notification on the existing app stream."""
        with self._lock, self._connect() as db:
            self._event(db, "apps", app_id, data)

    def close(self) -> None:
        if self._backup_schedule is not None:
            self._backup_schedule.close()
            self._backup_schedule = None
        if self._apps is not None:
            self._apps.close()
            self._apps = None
        self._app_hooks.clear()

    def apps_evidence(self, app_id: str) -> list[Document]:
        """Read verified version and stage evidence from the app volume."""
        return self.app_runtime().road.evidence(app_id)

    def workflows_get(self, workflow_id: str) -> Document:
        """Read a workflow definition."""
        return self._unavailable("workflows.get", "P10")

    def workflows_put(self, workflow_id: str, graph: Document) -> Document:
        """Publish a workflow graph as a new version. Saving a draft is workflow_drafts_put."""
        return self._unavailable("workflows.put", "P10")

    def workflows_validate(self, graph: Document) -> Document:
        """Validate a workflow graph."""
        return self._unavailable("workflows.validate", "P10")

    def workflows_run(self, workflow_id: str) -> Document:
        """Start a live run of a published workflow. A test run is workflow_tests_run."""
        return self._unavailable("workflows.run", "P10/P22")

    def workflow_drafts_get(self, workflow_id: str) -> Document:
        """Read a workflow's draft."""
        return self._unavailable("workflow_drafts.get", ENGINE)

    def workflow_drafts_put(self, workflow_id: str, graph: Document) -> Document:
        """Save a workflow draft. Nothing is published."""
        return self._unavailable("workflow_drafts.put", ENGINE)

    def workflow_tests_run(
        self, workflow_id: str, subgraph: list[str] | None = None, fake: bool = False
    ) -> Document:
        """Test-run a workflow's draft, whole or only the named nodes, on fake models if asked."""
        return self._unavailable("workflow_tests.run", ENGINE)

    def workflow_versions_list(self, workflow_id: str) -> list[Document]:
        """List a workflow's published versions."""
        return self._unavailable("workflow_versions.list", ENGINE)

    def workflow_versions_archive(self, workflow_id: str, version: int) -> Document:
        """Archive one published version of a workflow."""
        return self._unavailable("workflow_versions.archive", ENGINE)

    def workflow_runs_list(self, workflow_id: str | None = None) -> list[Document]:
        """List workflow runs, newest first, optionally for one workflow."""
        return self._unavailable("workflow_runs.list", ENGINE)

    def workflow_runs_get(self, run_id: str) -> Document:
        """Read one workflow run and its node states."""
        return self._unavailable("workflow_runs.get", ENGINE)

    def workflow_runs_explain(self, run_id: str) -> Document:
        """Explain what a workflow run did and why it stopped."""
        return self._unavailable("workflow_runs.explain", ENGINE)

    def workflow_runs_cancel(self, run_id: str) -> Document:
        """Cancel a workflow run."""
        return self._unavailable("workflow_runs.cancel", ENGINE)

    def workflow_runs_resume(self, run_id: str) -> Document:
        """Resume a paused or failed workflow run."""
        return self._unavailable("workflow_runs.resume", ENGINE)

    def workflow_triggers_list(self, workflow_id: str | None = None) -> list[Document]:
        """List workflow triggers, optionally for one workflow."""
        return self._unavailable("workflow_triggers.list", ENGINE)

    def workflow_triggers_create(self, workflow_id: str, trigger: Document) -> Document:
        """Create a trigger for a published workflow. It starts disabled."""
        return self._unavailable("workflow_triggers.create", ENGINE)

    def workflow_triggers_enable(self, trigger_id: str) -> Document:
        """Enable a workflow trigger."""
        return self._unavailable("workflow_triggers.enable", ENGINE)

    def workflow_triggers_disable(self, trigger_id: str) -> Document:
        """Disable a workflow trigger."""
        return self._unavailable("workflow_triggers.disable", ENGINE)

    def workflow_triggers_run_now(self, trigger_id: str) -> Document:
        """Fire a workflow trigger once, now."""
        return self._unavailable("workflow_triggers.run_now", ENGINE)

    def workflow_inbox_list(self) -> list[Document]:
        """List open workflow inbox items."""
        return self._unavailable("workflow_inbox.list", ENGINE)

    def apps_archive(self, app_id: str) -> Document:
        """Archive a mini app."""
        return self._unavailable("apps.archive", ENGINE)
