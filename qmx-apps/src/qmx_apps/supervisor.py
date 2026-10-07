"""One host owns each volume and the corresponding long-lived MCP connection."""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable, Coroutine
from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar, cast

import keyring
import psutil
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic import JsonValue

from qmx_apps.artifacts import Artifacts
from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition, Trust, image_files, image_hash
from qmx_apps.volume import Volume, VolumeLease
from qmx_apps.windows_job import WindowsJob

T = TypeVar("T")
type EventSink = Callable[[str, Document], None]


@dataclass
class Instance:
    definition: Definition
    volume: Volume
    lease: VolumeLease
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ready: concurrent.futures.Future[None] = field(default_factory=concurrent.futures.Future[None])
    stop: asyncio.Event | None = None
    client: Client[StdioTransport] | None = None
    task: concurrent.futures.Future[None] | None = None
    job: WindowsJob | None = None
    process: psutil.Process | None = None
    tools: list[Document] = field(default_factory=list[Document])
    resources: list[Document] = field(default_factory=list[Document])
    state: str = "starting"
    reason: str = ""
    runs: int = 0
    errors: int = 0
    job_runs: int = 0
    job_errors: int = 0
    cpu: float = 0
    memory: int = 0
    heartbeat: float = 0
    secrets: list[str] = field(default_factory=list[str])
    limits: Document = field(default_factory=dict[str, JsonValue])

    def document(self) -> Document:
        return {
            "app_id": self.definition.manifest.id,
            "instance_id": self.id,
            "definition_hash": self.definition.hash,
            "status": self.state,
            "pid": self.process.pid
            if self.process and self.state in {"starting", "running", "stopping"}
            else None,
            "node": "laptop",
            "tier": "T1",
            "breaker": {"open": self.state == "tripped", "reason": self.reason},
            "metrics": {
                "runs": self.runs + self.job_runs,
                "errors": self.errors + self.job_errors,
                "budget_used": {"runs": self.runs + self.job_runs, "cpu_seconds": self.cpu},
                "memory_bytes": self.memory,
            },
            "heartbeat_age_seconds": max(0, time.monotonic() - self.heartbeat)
            if self.heartbeat
            else None,
            "limits": self.limits,
        }


class Supervisor:
    def __init__(
        self,
        home: Path,
        *,
        event_sink: EventSink | None = None,
        secret_getter: Callable[[str, str], str | None] = keyring.get_password,
    ) -> None:
        self.home = home.resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self.catalog = self.home / "apps.db"
        self.artifacts = Artifacts(self.home)
        self.event_sink = event_sink
        self.secret_getter = secret_getter
        self._lock = threading.RLock()
        self._instances: dict[str, Instance] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        with closing(sqlite3.connect(self.catalog)) as db, db:
            db.executescript(
                "PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS definitions "
                "(id TEXT, version TEXT, hash TEXT PRIMARY KEY, trust TEXT, "
                "UNIQUE(id,version)); CREATE TABLE IF NOT EXISTS selected "
                "(id TEXT PRIMARY KEY, hash TEXT); CREATE TABLE IF NOT EXISTS runtime "
                "(id TEXT PRIMARY KEY, data TEXT);"
            )

    def install(
        self, path: Path, *, trust: Trust = "agent", expected_id: str | None = None
    ) -> Document:
        if trust == "agent":
            raise AppError(
                "tier_required",
                "Agent-authored code needs T2/T3 or operator review before T1.",
                409,
            )
        definition = Definition.load(path)
        manifest = definition.manifest
        if expected_id is not None and manifest.id != expected_id:
            raise AppError("id_mismatch", "An update must keep the app id.")
        lease = VolumeLease(self.home, manifest.id)
        try:
            return self._install(definition, trust)
        finally:
            lease.close()

    def _install(self, definition: Definition, trust: Trust) -> Document:
        manifest = definition.manifest
        with self._lock:
            if manifest.id in self._instances:
                raise AppError("app_running", "Stop the instance before installing a version.", 409)
            with closing(sqlite3.connect(self.catalog)) as db:
                existing = db.execute(
                    "SELECT hash FROM definitions WHERE id=? AND version=?",
                    (manifest.id, manifest.version),
                ).fetchone()
            if existing and existing[0] != definition.hash:
                raise AppError("immutable_version", "Changed content requires a new version.", 409)
            image = self.home / "definitions" / definition.hash
            image.mkdir(parents=True, exist_ok=True)
            if not existing:
                for source in image_files(definition.root):
                    target = image / source.relative_to(definition.root)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
            if image_hash(image) != definition.hash:
                raise AppError("definition_corrupt", "The immutable image hash changed.", 409)
            uv = shutil.which("uv")
            if uv is None:
                raise AppError(
                    "uv_missing", "uv is required to install the locked environment.", 503
                )
            environment = {
                name: value
                for name, value in os.environ.items()
                if name.upper()
                in {
                    "PATH",
                    "SYSTEMROOT",
                    "WINDIR",
                    "COMSPEC",
                    "USERPROFILE",
                    "HOME",
                    "LOCALAPPDATA",
                    "APPDATA",
                    "TEMP",
                    "TMP",
                }
            }
            environment["UV_PROJECT_ENVIRONMENT"] = str(
                self.home / "environments" / definition.hash
            )
            result = subprocess.run(
                [
                    uv,
                    "sync",
                    "--project",
                    str(image),
                    "--locked",
                    "--no-dev",
                    "--no-editable",
                    "--no-install-project",
                ],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode:
                raise AppError(
                    "install_failed",
                    "uv could not install the app's lock; check its lock and sources.",
                    422,
                )
            if image_hash(image) != definition.hash:
                raise AppError(
                    "definition_corrupt", "Installation changed the immutable image.", 409
                )
            with closing(sqlite3.connect(self.catalog)) as db, db:
                db.execute(
                    "INSERT OR IGNORE INTO definitions VALUES(?,?,?,?)",
                    (manifest.id, manifest.version, definition.hash, trust),
                )
                db.execute(
                    "INSERT INTO selected VALUES(?,?) ON CONFLICT(id) "
                    "DO UPDATE SET hash=excluded.hash",
                    (manifest.id, definition.hash),
                )
            self._log(
                manifest.id,
                "installed",
                {"definition_hash": definition.hash, "version": manifest.version},
            )
            self._emit(
                manifest.id,
                {"app_id": manifest.id, "status": "installed", "definition_hash": definition.hash},
            )
        return self.get(manifest.id)

    def _definition(self, app_id: str) -> Definition:
        with closing(sqlite3.connect(self.catalog)) as db:
            row = db.execute("SELECT hash FROM selected WHERE id=?", (app_id,)).fetchone()
        if row is None:
            raise AppError("not_found", "The app is not installed.", 404)
        definition = Definition.load(self.home / "definitions" / row[0])
        if definition.hash != row[0]:
            raise AppError("definition_corrupt", "The immutable definition hash changed.", 409)
        return definition

    def list(self) -> list[Document]:
        with closing(sqlite3.connect(self.catalog)) as db:
            rows = db.execute("SELECT id FROM selected ORDER BY id").fetchall()
        return [self.get(row[0]) for row in rows]

    def get(self, app_id: str) -> Document:
        definition = self._definition(app_id)
        return {
            "definition": cast(Document, definition.manifest.model_dump(mode="json")),
            "definition_hash": definition.hash,
            "runtime": self.status(app_id),
        }

    def versions(self, app_id: str) -> list[Document]:
        self._definition(app_id)
        with closing(sqlite3.connect(self.catalog)) as db:
            rows = db.execute(
                "SELECT version,hash,trust FROM definitions WHERE id=? ORDER BY rowid", (app_id,)
            ).fetchall()
        return [{"version": row[0], "definition_hash": row[1], "trust": row[2]} for row in rows]

    def status(self, app_id: str) -> Document:
        self._definition(app_id)
        with self._lock:
            instance = self._instances.get(app_id)
            if instance:
                return instance.document()
        with closing(sqlite3.connect(self.catalog)) as db:
            row = db.execute("SELECT data FROM runtime WHERE id=?", (app_id,)).fetchone()
        data: Document = (
            cast(Document, json.loads(row[0])) if row else {"app_id": app_id, "status": "stopped"}
        )
        if data.get("status") in {"running", "starting"}:
            # A persisted running flag is not evidence of a connected process after host restart.
            data = {**data, "status": "disconnected", "pid": None}
        return data

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        with self._lock:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
                self._thread = threading.Thread(
                    target=self._loop.run_forever, name="qmx-app-supervisor", daemon=True
                )
                self._thread.start()
            return self._loop

    def _submit(self, operation: Coroutine[Any, Any, T]) -> concurrent.futures.Future[T]:
        return asyncio.run_coroutine_threadsafe(operation, self._ensure_loop())

    def start(self, app_id: str) -> Document:
        with self._lock:
            existing = self._instances.get(app_id)
            if existing:
                return existing.document()
            definition = self._definition(app_id)
            volume = Volume(self.home, app_id)
            lease = VolumeLease(self.home, app_id)
            try:
                volume.create(agents=bool(definition.manifest.entrypoints.agents))
            except BaseException:
                lease.close()
                raise
            instance = Instance(definition, volume, lease)
            self._instances[app_id] = instance
            instance.task = self._submit(self._serve(instance))
        try:
            instance.ready.result(timeout=45)
        except Exception as error:
            self.stop(app_id)
            if isinstance(error, AppError):
                raise
            raise AppError(
                "start_failed", "The app did not establish its MCP connection.", 503
            ) from error
        return self.status(app_id)

    def _environment(self, instance: Instance) -> dict[str, str]:
        environment = {
            name: value
            for name, value in os.environ.items()
            if name.upper() in {"SYSTEMROOT", "WINDIR", "COMSPEC"}
        }
        root = str(instance.volume.root)
        for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
            environment[name] = root
        environment.update(
            {
                "TEMP": str(instance.volume.root / "data/tmp"),
                "TMP": str(instance.volume.root / "data/tmp"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "QMX_VOLUME": root,
                "FASTMCP_SHOW_BANNER": "false",
            }
        )
        env = self.home / "environments" / instance.definition.hash
        environment["PATH"] = str(env / ("Scripts" if sys.platform == "win32" else "bin"))
        for name, service in instance.definition.manifest.capabilities.secrets.items():
            secret = self.secret_getter(service, service.split("/", 1)[1])
            if not secret:
                raise AppError("missing_secret", f"Missing declared credential {service}.", 503)
            environment[name] = secret
            instance.secrets.append(secret)
        return environment

    async def _serve(self, instance: Instance) -> None:
        manifest = instance.definition.manifest
        app_id = manifest.id
        instance.stop = asyncio.Event()
        try:
            environment = self._environment(instance)
            job_name = f"Local\\qmx-{instance.id}"
            if sys.platform == "win32":
                instance.job = WindowsJob(job_name, manifest.budget)
                instance.limits = instance.job.limits()
            else:
                instance.limits = {
                    "memory_mb": manifest.budget.memory_mb,
                    "cpu_seconds": manifest.budget.cpu_seconds,
                    "cpu_percent": None,
                    "fallback": "RLIMIT_AS/RLIMIT_CPU and psutil",
                }
            config = {
                "image": str(instance.definition.root),
                "volume": str(instance.volume.root),
                "mcp": manifest.entrypoints.mcp,
                "jobs": manifest.entrypoints.jobs,
                "interval_seconds": manifest.schedule.interval_seconds if manifest.schedule else 0,
                "instance_id": instance.id,
                "job_name": job_name,
                "env_names": list(environment),
                "secret_names": list(manifest.capabilities.secrets),
                "memory_mb": manifest.budget.memory_mb,
                "cpu_seconds": manifest.budget.cpu_seconds,
            }
            env = self.home / "environments" / instance.definition.hash
            python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            transport = StdioTransport(
                command=str(python),
                args=[str(Path(__file__).with_name("bootstrap.py")), json.dumps(config)],
                cwd=str(instance.volume.root),
                env=environment,
                keep_alive=False,
                log_file=instance.volume.root / f"logs/{instance.id}.stderr.log",
            )
            async with Client(transport, timeout=20) as client:
                instance.client = client
                instance.tools = [
                    cast(Document, tool.model_dump(mode="json", by_alias=True))
                    for tool in await client.list_tools()
                ]
                instance.resources = [
                    cast(Document, resource.model_dump(mode="json", by_alias=True))
                    for resource in await client.list_resources()
                ]
                self._heartbeat(instance)
                if instance.process is None:
                    raise AppError(
                        "heartbeat_missing", "The bootstrap did not publish a heartbeat.", 503
                    )
                instance.state = "running"
                self._log(
                    app_id,
                    "started",
                    {
                        "instance_id": instance.id,
                        "network": cast(list[JsonValue], manifest.capabilities.network),
                        "data_reads": cast(list[JsonValue], manifest.capabilities.data_reads),
                        "secret_names": list(manifest.capabilities.secrets),
                    },
                )
                self._persist(instance)
                instance.ready.set_result(None)
                while not instance.stop.is_set():
                    await asyncio.sleep(0.25)
                    if instance.stop.is_set():
                        break
                    self._heartbeat(instance)
                    breach = self._breach(instance)
                    if breach:
                        self._trip(instance, breach)
                self._kill(instance)
        except Exception as error:
            if instance.state not in {"tripped", "stopping"}:
                instance.state = "tripped"
                instance.reason = "startup_failed" if not instance.ready.done() else "process_exit"
            self._log(app_id, "process_error", {"reason": instance.reason})
            if not instance.ready.done():
                instance.ready.set_exception(
                    error
                    if isinstance(error, AppError)
                    else AppError(
                        "start_failed", "The app could not start its locked MCP server.", 503
                    )
                )
        finally:
            self._kill(instance)
            instance.client = None
            self._heartbeat(instance)
            if instance.job:
                instance.job.close()
            if instance.state != "tripped":
                instance.state = "stopped"
            self._capture_stderr(instance)
            self._persist(instance)
            instance.lease.close()
            with self._lock:
                self._instances.pop(app_id, None)

    def _heartbeat(self, instance: Instance) -> None:
        path = instance.volume.root / f"data/heartbeat-{instance.id}.json"
        try:
            if instance.job and not instance.job.closed:
                instance.cpu = instance.job.cpu_seconds()
            data = cast(Document, json.loads(path.read_text(encoding="utf-8")))
            instance.heartbeat = float(cast(float, data["at"]))
            instance.job_runs = int(cast(int, data["job_runs"]))
            instance.job_errors = int(cast(int, data["job_errors"]))
            pid = int(cast(int, data["pid"]))
            if instance.process is None:
                process = psutil.Process(pid)
                if str(Path(__file__).with_name("bootstrap.py")) not in process.cmdline():
                    raise AppError("process_mismatch", "Heartbeat belongs to another process.", 409)
                instance.process = process
            processes = [instance.process, *instance.process.children(recursive=True)]
            if instance.job is None:
                instance.cpu = max(
                    instance.cpu,
                    sum(p.cpu_times().user + p.cpu_times().system for p in processes),
                )
            instance.memory = sum(p.memory_info().rss for p in processes)
        except OSError, ValueError, KeyError, psutil.Error:
            return

    @staticmethod
    def _breach(instance: Instance) -> str:
        manifest = instance.definition.manifest
        if instance.runs + instance.job_runs > manifest.budget.runs:
            return "run_budget"
        if instance.cpu > manifest.budget.cpu_seconds:
            return "cpu_budget"
        if instance.errors + instance.job_errors >= manifest.breaker.max_errors:
            return "error_limit"
        if time.monotonic() - instance.heartbeat > manifest.breaker.heartbeat_timeout:
            return "heartbeat_timeout"
        if instance.process and not instance.process.is_running():
            return "process_exit"
        return ""

    def _trip(self, instance: Instance, reason: str) -> None:
        instance.state = "tripped"
        instance.reason = reason
        self._log(instance.definition.manifest.id, "breaker_open", {"reason": reason})
        self._persist(instance)
        if instance.stop:
            instance.stop.set()
        self._kill(instance)

    @staticmethod
    def _kill(instance: Instance) -> None:
        if instance.job:
            instance.job.terminate()
        elif instance.process:
            try:
                processes = [*instance.process.children(recursive=True), instance.process]
                for process in processes:
                    process.kill()
                psutil.wait_procs(processes, timeout=5)
            except psutil.Error:
                pass

    async def _stop(self, instance: Instance) -> None:
        if instance.state != "tripped":
            instance.state = "stopping"
        if instance.stop:
            instance.stop.set()
        self._kill(instance)

    def stop(self, app_id: str) -> Document:
        self._definition(app_id)
        with self._lock:
            instance = self._instances.get(app_id)
        if instance:
            self._submit(self._stop(instance)).result(timeout=10)
            if instance.task:
                instance.task.result(timeout=30)
        return self.status(app_id)

    def restart(self, app_id: str) -> Document:
        self.stop(app_id)
        return self.start(app_id)

    def registry(self) -> list[Document]:
        with self._lock:
            return [
                cast(
                    Document,
                    {
                        "app_id": app_id,
                        "instance_id": instance.id,
                        "transport": "stdio",
                        "tools": instance.tools,
                        "resources": instance.resources,
                    },
                )
                for app_id, instance in self._instances.items()
                if instance.state == "running"
            ]

    async def _call(self, instance: Instance, tool: str, arguments: Document) -> Document:
        if instance.client is None or instance.state != "running":
            raise AppError("not_running", "Start the app before calling it.", 409)
        if instance.runs + instance.job_runs >= instance.definition.manifest.budget.runs:
            self._trip(instance, "run_budget")
            raise AppError("budget_exceeded", "The app's run budget is exhausted.", 409)
        instance.runs += 1
        try:
            inputs = dict(arguments)
            for feed in instance.definition.manifest.feeds:
                if feed in inputs:
                    inputs[feed] = self.artifacts.accept(instance.definition, feed, inputs[feed])
            result = await instance.client.call_tool(tool, inputs)
            data = cast(JsonValue, result.structured_content)
            document: Document = {"result": data}
            if isinstance(data, dict) and "output" in data and "data" in data:
                output = data["output"]
                if not isinstance(output, str):
                    raise AppError("invalid_output", "Output names must be strings.")
                document["artifact_ref"] = self.artifacts.save(
                    instance.definition, output, data["data"]
                )
            self._log(
                instance.definition.manifest.id,
                "tool_completed",
                {"tool": tool, "run": instance.runs},
            )
            return document
        except Exception as error:
            instance.errors += 1
            self._log(instance.definition.manifest.id, "tool_error", {"tool": tool})
            if isinstance(error, AppError):
                raise
            message = str(error)
            for secret in instance.secrets:
                message = message.replace(secret, "[redacted]")
            raise AppError("tool_failed", message, 422) from error
        finally:
            self._heartbeat(instance)
            breach = self._breach(instance)
            if breach and instance.state == "running":
                self._trip(instance, breach)
            self._persist(instance)

    def call(self, app_id: str, tool: str, arguments: Document) -> Document:
        with self._lock:
            instance = self._instances.get(app_id)
        if instance is None:
            raise AppError("not_running", "Start the app before calling it.", 409)
        try:
            return self._submit(self._call(instance, tool, arguments)).result(timeout=30)
        except concurrent.futures.TimeoutError as error:
            self.stop(app_id)
            raise AppError(
                "tool_timeout", "The tool did not complete within its timeout.", 504
            ) from error

    async def _resource(self, instance: Instance, uri: str) -> list[Document]:
        if instance.client is None:
            raise AppError("not_running", "Start the app before reading a resource.", 409)
        return [
            cast(Document, content.model_dump(mode="json", by_alias=True))
            for content in await instance.client.read_resource(uri)
        ]

    def resource(self, app_id: str, uri: str) -> list[Document]:
        with self._lock:
            instance = self._instances.get(app_id)
        if instance is None:
            raise AppError("not_running", "Start the app before reading a resource.", 409)
        return self._submit(self._resource(instance, uri)).result(timeout=30)

    def _emit(self, app_id: str, data: Document) -> None:
        if self.event_sink:
            self.event_sink(app_id, data)

    def _persist(self, instance: Instance) -> None:
        data = instance.document()
        app_id = instance.definition.manifest.id
        with closing(sqlite3.connect(self.catalog)) as db, db:
            db.execute(
                "INSERT INTO runtime VALUES(?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                (app_id, json.dumps(data)),
            )
        self._emit(app_id, data)

    def _log(self, app_id: str, event: str, data: Document) -> None:
        path = Volume(self.home, app_id).check_write("logs/supervisor.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"at": datetime.now(UTC).isoformat(), "event": event, **data}
        with self._lock, path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry) + "\n")

    def _capture_stderr(self, instance: Instance) -> None:
        path = instance.volume.root / f"logs/{instance.id}.stderr.log"
        if path.exists():
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                redacted = line
                for secret in instance.secrets:
                    redacted = redacted.replace(secret, "[redacted]")
                self._log(instance.definition.manifest.id, "stderr", {"message": redacted})

    def logs(self, app_id: str, limit: int = 100) -> list[Document]:
        self._definition(app_id)
        if not 1 <= limit <= 1000:
            raise AppError("invalid_limit", "Use a log limit between 1 and 1000.")
        path = Volume(self.home, app_id).check_write("logs/supervisor.jsonl")
        if not path.exists():
            return []
        with self._lock, path.open(encoding="utf-8") as file:
            return [cast(Document, json.loads(line)) for line in deque(file, maxlen=limit)]

    def close(self) -> None:
        for app_id in list(self._instances):
            self.stop(app_id)
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread:
                self._thread.join(timeout=10)
            self._loop.close()
            self._loop = None
