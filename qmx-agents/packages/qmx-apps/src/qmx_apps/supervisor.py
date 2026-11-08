"""One host owns each volume and the corresponding long-lived MCP connection."""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import re
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
from typing import Any, Final, TypeVar, cast

import keyring
import psutil
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic import JsonValue
from qmx_home import Layout
from qmx_home.versions import open_sqlite

from qmx_apps.artifacts import Artifacts, LibrarySink, contract_problems
from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Breaker, Definition, Trust, image_files, image_hash
from qmx_apps.road import PackSink, Road
from qmx_apps.store import open_store
from qmx_apps.volume import Lease, Volume, VolumeLease, checksum, snapshot
from qmx_apps.windows_job import WindowsJob

T = TypeVar("T")
type EventSink = Callable[[str, Document], None]
type Wait = Callable[[float, threading.Event], bool]
"""Wait `seconds` unless the event is set first; true when it was set."""

PARENT_SURFACES: Final = frozenset(
    {
        ("qmf-registry", "value_type"),
        ("qmf-registry", "typed_refusal"),
        ("qmf-registry", "pure_calculation"),
        ("qmf-registry", "dev_zone_candidate_write"),
        ("qmf-risk", "value_type"),
        ("qmf-risk", "typed_refusal"),
        ("qmf-risk", "pure_calculation"),
    }
)
"""The parent-library surfaces a pack's tool may name (AD-2); every other pair is refused."""
MARKET_STORE: Final = "market"
"""The machine's market-data store under the home, the folder the host's market door opens."""


def refuse_tool(name: str, tool: Document) -> None:
    """Refuse a listed tool whose metadata names a parent surface off `PARENT_SURFACES` or any
    parent `record_family`. The app manifest cannot declare either, so the tool's own metadata
    is where a pack would claim one."""
    sources: list[Document] = [tool]
    while sources:
        source = sources.pop()
        for key in ("mcp", "tool", "annotations", "_meta"):
            nested = source.get(key)
            if isinstance(nested, dict):
                sources.append(nested)
        if "parent_library" in source:
            surface = (str(source["parent_library"]), str(source.get("parent_surface", "")))
            if surface not in PARENT_SURFACES:
                raise AppError("tool_refused", f"Parent surface refused: {name}", 403)
        if source.get("record_family") is not None:
            raise AppError("tool_refused", f"Parent record mutation refused: {name}", 403)


def _snapshot_files(root: Path) -> list[Path]:
    """Every file a move carries, in one order, leaving out its own manifest."""
    return [path for path in sorted(root.rglob("*")) if path.is_file() and path.name != SNAPSHOT]


def _verify_snapshot(root: Path, app_id: str, snapshot_id: str) -> Document:
    """A snapshot's manifest, after its identity and every checksum is checked."""
    try:
        manifest = cast(Document, json.loads((root / SNAPSHOT).read_text(encoding="utf-8")))
        if manifest["app_id"] != app_id or manifest["snapshot_id"] != snapshot_id:
            raise ValueError("snapshot identity differs")
        actual = {
            path.relative_to(root).as_posix(): checksum(path) for path in _snapshot_files(root)
        }
        if actual != manifest["checksums"] or not actual:
            raise ValueError("snapshot checksums differ")
        if not isinstance(manifest.get("lease"), dict):
            raise ValueError("snapshot carries no lease")
    except OSError, ValueError, KeyError, TypeError:
        raise AppError(
            "invalid_snapshot", "Snapshot identity, checksums or lease failed.", 409
        ) from None
    return manifest


APPS_SCHEMA: Final = (
    "CREATE TABLE IF NOT EXISTS definitions"
    " (id TEXT, version TEXT, hash TEXT PRIMARY KEY, trust TEXT, UNIQUE(id,version))",
    "CREATE TABLE IF NOT EXISTS selected (id TEXT PRIMARY KEY, hash TEXT)",
    "CREATE TABLE IF NOT EXISTS runtime (id TEXT PRIMARY KEY, data TEXT)",
    "CREATE TABLE IF NOT EXISTS active (id TEXT PRIMARY KEY, hash TEXT, revision TEXT)",
    "CREATE TABLE IF NOT EXISTS homes"
    " (id TEXT PRIMARY KEY, placement TEXT, generation INTEGER, moved_at TEXT)",
)
"""`apps.db` at version 1 (design 62 B1). A later version adds a step; it never edits these."""
JOB_QUEUE: Final = "data/jobs"
"""Where `run_job` leaves a request and the app's bootstrap leaves its answer, inside the volume."""
JOB_POLL_SECONDS: Final = 0.25
PROFILES: Final = "profiles"
"""One folder per profile under the app's own `data/` (AD-64). The host's files, the heartbeat
and the job queue, stay at `data/` because the app's bootstrap writes them there."""
MOVES: Final = "moves"
"""Where a move's snapshot waits for the machine that takes the instance: `moves/<app>/<id>`."""
SNAPSHOT: Final = "snapshot.json"
"""A move's manifest: the app, the machine it came from and will go to, the lease generation and
one checksum per file. It is left out of its own checksums."""


@dataclass(frozen=True, slots=True)
class Pin:
    """The `(pack, version)` an ask is pinned to: which pack ships the operation and which of its
    versions answered. A call revalidates it before the app sees the tool call, so an app that
    moved on under a queued ask is refused instead of answering from a version nobody pinned."""

    pack: str
    version: str

    @classmethod
    def parse(cls, value: object) -> Pin | None:
        if value is None:
            return None
        if isinstance(value, Pin):
            return value
        if isinstance(value, dict):
            table = cast(dict[str, object], value)
            pack, version = table.get("pack"), table.get("version")
            if isinstance(pack, str) and isinstance(version, str):
                return cls(pack, version)
        raise AppError("invalid_pin", "A pin is {pack, version}, two strings.")


@dataclass(frozen=True, slots=True)
class Move:
    """One instance's snapshot on its way from the machine that held it to the machine that takes
    it (AD-64). `lease` is the handover the receiving machine must present before it writes."""

    app_id: str
    snapshot_id: str
    folder: Path
    origin: str
    to: str
    definition_hash: str
    lease: Lease
    files: int
    bytes: int

    @property
    def generation(self) -> int:
        return self.lease.generation

    def document(self) -> Document:
        return {
            "app_id": self.app_id,
            "snapshot_id": self.snapshot_id,
            "folder": str(self.folder),
            "from": self.origin,
            "to": self.to,
            "definition_hash": self.definition_hash,
            "lease": self.lease.document(),
            "files": self.files,
            "bytes": self.bytes,
        }


def wait(seconds: float, cancel: threading.Event) -> bool:
    return cancel.wait(seconds)


@dataclass
class Healing:
    """An opted-in app's restarts since someone last stopped it (AD-33 change 3). `trips`
    counts the trips and the failed restarts that set the next wait; `cancel` ends the pending
    wait when he stops the app or the host closes. `thread` is the one restart loop, if any."""

    breaker: Breaker
    profile: str | None
    trips: int = 0
    cancel: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None


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
    started: float = field(default_factory=time.monotonic)
    secrets: list[str] = field(default_factory=list[str])
    limits: Document = field(default_factory=dict[str, JsonValue])
    node: str = "laptop"
    tier: str = "T1"
    profile: str | None = None

    @property
    def data(self) -> Path:
        """This instance's partition of the app's `data/`: `data/profiles/<profile>` under a
        named profile, `data/` itself when the app runs without one."""
        root = self.volume.root / "data"
        return root if self.profile is None else root / PROFILES / self.profile

    def document(self) -> Document:
        return {
            "app_id": self.definition.manifest.id,
            "instance_id": self.id,
            "definition_hash": self.definition.hash,
            "version": self.definition.manifest.version,
            "profile": self.profile,
            "data": self.data.relative_to(self.volume.root).as_posix(),
            "status": self.state,
            "pid": self.process.pid
            if self.process and self.state in {"starting", "running", "stopping"}
            else None,
            "node": self.node,
            "tier": self.tier,
            "breaker": {"open": self.state == "tripped", "reason": self.reason},
            "metrics": {
                "runs": self.runs + self.job_runs,
                "errors": self.errors + self.job_errors,
                "cpu_seconds": self.cpu,
                "memory_bytes": self.memory,
            },
            "heartbeat_age_seconds": max(0, time.monotonic() - self.heartbeat)
            if self.heartbeat
            else None,
            "limits": self.limits,
        }


class Supervisor:
    tier = "T1"

    def __init__(
        self,
        home: Path,
        *,
        event_sink: EventSink | None = None,
        secret_getter: Callable[[str, str], str | None] = keyring.get_password,
        proof_mode: str = "",
        call_depth: int | None = None,
        library: LibrarySink | None = None,
        placement: str = "pc",
        restart_wait: Wait = wait,
    ) -> None:
        """`call_depth` is the host's bound on a ring of asks (AD-64): the longest chain of app
        operations that may sit behind one ask. There is no default number, and a host that sets
        none is unbounded. `library` is where an app's landings go; without one they stay in the
        volume and the index here. `placement` is the machine this store is: the home every app
        instance here runs on, and the machine a move hands a volume to or takes it from.
        `restart_wait` is how an opted-in app's back-off waits before it starts again."""
        self.home = home.resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self.catalog = self.home / "apps.db"
        self.artifacts = Artifacts(self.home, library)
        self.event_sink = event_sink
        self.secret_getter = secret_getter
        self.proof_mode = proof_mode
        self.call_depth = call_depth
        self.placement = placement
        self._proof_images: dict[str, Definition] = {}
        self.environments = Layout.from_home(self.home).cache / "envs"
        """Each definition's uv environment, rebuilt from its lock on demand (design 62 A3)."""
        self.road = Road(self)
        self._lock = threading.RLock()
        self._instances: dict[str, Instance] = {}
        self._healing: dict[str, Healing] = {}
        self.restart_wait = restart_wait
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        with closing(sqlite3.connect(self.catalog, isolation_level=None)) as db:
            open_sqlite(db, "apps", (APPS_SCHEMA,))
            for statement in APPS_SCHEMA:
                db.execute(statement)

    def attach_library(self, library: LibrarySink | None) -> None:
        """Give the supervisor the Library its landings go to, or take it away."""
        self.artifacts.attach(library)

    def attach_packs(self, sink: PackSink | None) -> None:
        """Give the supervisor the Library a published pack lands in, or take it away."""
        self.road.attach_packs(sink)

    def install(
        self,
        path: Path,
        *,
        trust: Trust = "agent",
        expected_id: str | None = None,
        expected_hash: str | None = None,
    ) -> Document:
        if trust == "agent" and self.tier == "T1":
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
            return self._install(definition, trust, expected_hash)
        finally:
            lease.close()

    def _install(self, definition: Definition, trust: Trust, expected_hash: str | None) -> Document:
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
            with closing(sqlite3.connect(self.catalog)) as db:
                head = db.execute("SELECT hash FROM selected WHERE id=?", (manifest.id,)).fetchone()
            if head and head[0] not in {expected_hash, definition.hash}:
                raise AppError(
                    "head_conflict", "Candidate head changed; reload before saving.", 409
                )
            image = self.home / "definitions" / definition.hash
            image.mkdir(parents=True, exist_ok=True)
            if not existing and definition.root.resolve() != image.resolve():
                # A bundle fetched from another store already sits at its own hash.
                for source in image_files(definition.root):
                    target = image / source.relative_to(definition.root)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
            if image_hash(image) != definition.hash:
                raise AppError("definition_corrupt", "The immutable image hash changed.", 409)
            self._install_environment(definition, image)
            if image_hash(image) != definition.hash:
                raise AppError(
                    "definition_corrupt", "Installation changed the immutable image.", 409
                )
            self.road.register(definition, trust, expected_hash)
            self._log(
                manifest.id,
                "installed",
                {"definition_hash": definition.hash, "version": manifest.version},
            )
            self.emit(
                manifest.id,
                {"app_id": manifest.id, "status": "installed", "definition_hash": definition.hash},
            )
        return self.get(manifest.id)

    def _install_environment(self, definition: Definition, image: Path) -> None:
        uv = shutil.which("uv")
        if uv is None:
            raise AppError("uv_missing", "uv is required to install the locked environment.", 503)
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
                "UV_CACHE_DIR",
                "UV_PYTHON_INSTALL_DIR",
            }
        }
        environment["UV_PROJECT_ENVIRONMENT"] = str(self.environments / definition.hash)
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
                # The runtime cannot write bytecode into its locked dependencies.
                "--compile-bytecode",
            ],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode:
            said = [
                line.strip()
                for line in result.stderr.splitlines()
                if line.strip().startswith(("error:", "Caused by:"))
            ]
            why = f" uv said: {' '.join(said[:3])[:400]}" if said else ""
            raise AppError(
                "install_failed",
                f"uv could not install the app's lock; check its lock and sources.{why}",
                422,
            )

    def _definition(self, app_id: str) -> Definition:
        if self.proof_mode and app_id in self._proof_images:
            image = self._proof_images[app_id]
            checked = Definition.load(image.root)
            if checked.hash != image.hash:
                raise AppError("definition_corrupt", "The immutable proof image changed.", 409)
            return checked
        with closing(sqlite3.connect(self.catalog)) as db:
            row = db.execute("SELECT hash FROM selected WHERE id=?", (app_id,)).fetchone()
        if row is None:
            raise AppError("not_found", "The app is not installed.", 404)
        definition = Definition.load(self.home / "definitions" / row[0])
        if definition.hash != row[0]:
            raise AppError("definition_corrupt", "The immutable definition hash changed.", 409)
        return definition

    def select_image(self, definition: Definition) -> None:
        """Disposable proof catalogs point at the host's immutable image."""
        with closing(sqlite3.connect(self.catalog)) as db, db:
            db.execute(
                "INSERT INTO selected VALUES(?,?)", (definition.manifest.id, definition.hash)
            )
        self._proof_images[definition.manifest.id] = definition

    def python(self, definition_hash: str) -> Path:
        return (
            self.environments
            / definition_hash
            / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        )

    def list(self) -> list[Document]:
        with closing(sqlite3.connect(self.catalog)) as db:
            rows = db.execute("SELECT id FROM selected ORDER BY id").fetchall()
        return [self.get(row[0]) for row in rows]

    def get(self, app_id: str) -> Document:
        road: Document | None = None
        if not self.proof_mode and (Volume(self.home, app_id).root / "road/steps.jsonl").exists():
            from qmx_apps.road.history import history, project  # noqa: PLC0415

            with history(self.home, app_id) as state:
                project(self.home, app_id, state)
                road = {"stage": state.stages.get(state.head or ""), "active": state.active}
        definition = self._definition(app_id)
        result: Document = {
            "definition": cast(Document, definition.manifest.model_dump(mode="json")),
            "definition_hash": definition.hash,
            "runtime": self.status(app_id),
        }
        if road is not None:
            result["road"] = road
        return result

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

    def start(
        self,
        app_id: str,
        *,
        definition_hash: str | None = None,
        profile: str | None = None,
    ) -> Document:
        """Start the selected definition, or the one `definition_hash` pins, writing that
        `profile`'s partition of `data/`. An app that declares `[profiles]` keeps one partition
        per profile, so two of his setups never read each other's files."""
        with self._lock:
            existing = self._instances.get(app_id)
            if existing:
                return existing.document()
            definition = self._definition(app_id)
            self.check_profile(definition, profile)
            home = self.home_of(app_id)
            if home != self.placement:
                raise AppError(
                    "not_home",
                    f"{app_id} lives on {home}; this machine is {self.placement}.",
                    409,
                )
            if definition_hash is None and not self.proof_mode:
                from qmx_apps.road.history import history, project  # noqa: PLC0415

                with history(self.home, app_id) as state:
                    project(self.home, app_id, state)
                with closing(sqlite3.connect(self.catalog)) as db:
                    active = db.execute("SELECT hash FROM active WHERE id=?", (app_id,)).fetchone()
                definition_hash = active[0] if active else None
                if definition.manifest.risk == "money" and not active:
                    raise AppError(
                        "signature_required",
                        "Publish a proposal-only money app with an operator signature first.",
                        409,
                    )
            if definition_hash:
                from qmx_apps.road.history import definition as checked_definition  # noqa: PLC0415

                definition = checked_definition(self.home, app_id, definition_hash)
            volume = Volume(self.home, app_id)
            lease = VolumeLease(self.home, app_id)
            instance = Instance(
                definition, volume, lease, tier=self.tier, profile=profile, node=self.placement
            )
            try:
                volume.create(agents=bool(definition.manifest.entrypoints.agents))
                instance.data.mkdir(parents=True, exist_ok=True)
                # A request an earlier instance never answered has no caller left waiting.
                shutil.rmtree(volume.root / JOB_QUEUE, ignore_errors=True)
                migrations = definition.root / "migrations"
                if migrations.is_dir():
                    # The host finishes migrations before handing the writer to the instance.
                    with closing(open_store(volume, migrations)):
                        pass
            except BaseException:
                lease.close()
                raise
            self._instances[app_id] = instance
            instance.task = self._submit(self._serve(instance))
        try:
            instance.ready.result()
        except Exception as error:
            self._halt(app_id)
            if isinstance(error, AppError):
                raise
            raise AppError(
                "start_failed", "The app did not establish its MCP connection.", 503
            ) from error
        return self.status(app_id)

    def check_profile(self, definition: Definition, profile: str | None) -> None:
        """A profile exists only where the app declares a `[profiles]` schema, and its id is a
        folder name: a word of letters, digits and hyphens."""
        declared = definition.manifest.profiles is not None
        if profile is None:
            return
        if not declared:
            raise AppError(
                "undeclared_profile",
                f"{definition.manifest.id} declares no [profiles], so it has one partition.",
                409,
            )
        if not re.fullmatch(r"[a-z][a-z0-9-]*", profile):
            raise AppError("invalid_profile", "A profile id is lowercase letters and hyphens.")

    def environment(self, instance: Instance) -> dict[str, str]:
        environment = {
            name: value
            for name, value in os.environ.items()
            if name.upper() in {"SYSTEMROOT", "WINDIR", "COMSPEC"}
        }
        root = str(instance.volume.root)
        data = instance.data
        tmp = str(data / "tmp")
        for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
            environment[name] = root
        environment.update(
            {
                "TEMP": tmp,
                "TMP": tmp,
                "PYTHONDONTWRITEBYTECODE": "1",
                "QMX_VOLUME": root,
                "QMX_DATA_DIR": str(data),
                "FASTMCP_SHOW_BANNER": "false",
            }
        )
        if instance.profile is not None:
            environment["QMX_PROFILE"] = instance.profile
        environment["QMX_STAGE"] = self.proof_mode or "live"
        if "market" in instance.definition.manifest.capabilities.data_reads:
            # Read-only because it sits outside the volume, where the bootstrap refuses writes.
            environment["QMX_MARKET_ROOT"] = str(self.home / MARKET_STORE)
        env = self.environments / instance.definition.hash
        environment["PATH"] = str(env / ("Scripts" if sys.platform == "win32" else "bin"))
        for name, service in instance.definition.manifest.capabilities.secrets.items():
            if self.proof_mode in {"tests", "sandbox"}:
                continue
            secret = self.secret_getter(service, service.split("/", 1)[1])
            if not secret:
                raise AppError("missing_secret", f"Missing declared credential {service}.", 503)
            environment[name] = secret
            instance.secrets.append(secret)
        return environment

    def configuration(
        self, instance: Instance, job_name: str, environment: dict[str, str]
    ) -> Document:
        manifest = instance.definition.manifest
        return {
            "image": str(instance.definition.root),
            "volume": str(instance.volume.root),
            "data": str(instance.data),
            "profile": instance.profile,
            "mcp": manifest.entrypoints.mcp,
            "jobs": [] if self.proof_mode else list(manifest.entrypoints.jobs),
            "instance_id": instance.id,
            "job_name": job_name,
            "env_names": list(environment),
            "secret_names": list(manifest.capabilities.secrets),
            "memory_mb": manifest.isolation.memory_mb,
            "recorded": self.proof_mode in {"tests", "sandbox"},
        }

    async def _serve(self, instance: Instance) -> None:
        manifest = instance.definition.manifest
        app_id = manifest.id
        instance.stop = asyncio.Event()
        try:
            environment = self.environment(instance)
            job_name = f"Local\\qmx-{instance.id}"
            if sys.platform == "win32" and self.tier == "T1":
                instance.job = WindowsJob(job_name, manifest.isolation)
                instance.limits = instance.job.limits()
            else:
                instance.limits = {
                    "memory_mb": manifest.isolation.memory_mb,
                    "cpu_percent": None,
                    "fallback": "RLIMIT_AS and psutil",
                }
            config = self.configuration(instance, job_name, environment)
            transport = self.transport(instance, config, environment)
            # One deadline covers imports, negotiation and discovery. Disable the
            # client's competing timer and release this deadline only on readiness.
            async with (
                asyncio.timeout(manifest.startup_timeout_seconds) as startup,
                Client(transport, init_timeout=0) as client,
            ):
                instance.client = client
                instance.tools = [
                    cast(Document, tool.model_dump(mode="json", by_alias=True))
                    for tool in await client.list_tools()
                ]
                for tool in instance.tools:
                    refuse_tool(str(tool["name"]), tool)
                instance.resources = [
                    cast(Document, resource.model_dump(mode="json", by_alias=True))
                    for resource in await client.list_resources()
                ]
                self._heartbeat(instance)
                if not instance.heartbeat:
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
                startup.reschedule(None)
                instance.ready.set_result(None)
                while not instance.stop.is_set():
                    await asyncio.sleep(0.25)
                    if instance.stop.is_set():
                        break
                    self._heartbeat(instance)
                    breach = self._breach(instance)
                    if breach:
                        self._trip(instance, breach)
                    elif instance.state == "running":
                        self._persist(instance)
                self.kill(instance)
        except Exception as error:
            if instance.state not in {"tripped", "stopping"}:
                instance.state = "tripped"
                instance.reason = "startup_failed" if not instance.ready.done() else "process_exit"
            message = str(error)
            for secret in instance.secrets:
                message = message.replace(secret, "[redacted]")
            self._log(
                app_id,
                "process_error",
                {"reason": instance.reason, "error_type": type(error).__name__, "message": message},
            )
            if not instance.ready.done():
                instance.ready.set_exception(
                    error
                    if isinstance(error, AppError)
                    else AppError(
                        "start_failed", "The app could not start its locked MCP server.", 503
                    )
                )
        finally:
            self.kill(instance)
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
            if (
                instance.state == "tripped"
                and manifest.breaker.restart == "backoff"
                and instance.ready.done()
                and instance.ready.exception() is None
            ):
                self._heal(app_id, manifest.breaker, instance.profile)

    def transport(
        self, instance: Instance, config: dict[str, Any], environment: dict[str, str]
    ) -> StdioTransport:
        python = self.python(instance.definition.hash)
        command = str(python)
        if sys.platform == "win32" and not command.startswith("\\\\?\\"):
            # Keep sys.prefix extended too, so native DLL imports may exceed MAX_PATH.
            command = (
                "\\\\?\\UNC\\" + command[2:] if command.startswith("\\\\") else "\\\\?\\" + command
            )
        return StdioTransport(
            command=command,
            args=[str(Path(__file__).with_name("bootstrap.py")), json.dumps(config)],
            cwd=str(instance.volume.root),
            env=environment,
            keep_alive=False,
            log_file=instance.volume.root / f"logs/{instance.id}.stderr.log",
        )

    def heartbeats(self) -> list[Document]:
        """One row per running app in the host heartbeat's schema (AD-65), less the facts the
        host adds: `qmx_version`, `kinds_digest` and `paused`."""
        at = datetime.now(UTC).isoformat()
        with self._lock:
            running = [i for i in self._instances.values() if i.state == "running"]
        return [
            {
                "subject": "app",
                "id": instance.definition.manifest.id,
                "at": at,
                "cpu_seconds": instance.cpu,
                "rss_bytes": instance.memory,
                "machine_minutes": (time.monotonic() - instance.started) / 60,
            }
            for instance in running
        ]

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
        self.kill(instance)

    def kill(self, instance: Instance) -> None:
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
        self.kill(instance)

    def stop(self, app_id: str) -> Document:
        """Stop the app and any restart it was waiting for: a stopped app stays down."""
        self._definition(app_id)
        self._cancel_healing(app_id)
        self._halt(app_id)
        self._cancel_healing(app_id)
        return self.status(app_id)

    def _halt(self, app_id: str) -> None:
        with self._lock:
            instance = self._instances.get(app_id)
        if instance:
            self._submit(self._stop(instance)).result(timeout=10)
            if instance.task:
                instance.task.result(timeout=30)

    def _heal(self, app_id: str, breaker: Breaker, profile: str | None) -> None:
        """Count a trip of an opted-in app and start it again after its back-off, on the profile
        it ran. The restart is a plain `start`, so a `money` app gets only its active signed
        version (MA-05) and any other app what `restart` would start."""
        with self._lock:
            healing = self._healing.setdefault(app_id, Healing(breaker, profile))
            healing.breaker, healing.profile = breaker, profile
            healing.trips += 1
            if healing.thread is None:
                healing.thread = threading.Thread(
                    target=self._restart_loop,
                    args=(app_id, healing),
                    name=f"qmx-app-restart-{app_id}",
                    daemon=True,
                )
                healing.thread.start()

    def _restart_loop(self, app_id: str, healing: Healing) -> None:
        """Wait, start, and wait longer after each start that fails, until one runs or he stops
        the app. A refusal (a 4xx, such as a money app with no signed version) ends the loop,
        because waiting does not change it. A trip that lands while this loop is starting the app
        is caught by the last check, so no trip is left without its restart."""
        while True:
            with self._lock:
                trips = healing.trips
            seconds = healing.breaker.backoff(trips)
            self._log(app_id, "restart_scheduled", {"trips": trips, "wait_seconds": seconds})
            if self.restart_wait(seconds, healing.cancel) or healing.cancel.is_set():
                return
            with self._lock:
                if app_id in self._instances:
                    healing.thread = None
                    return
            try:
                started = self.start(app_id, profile=healing.profile)
            except Exception as error:
                if healing.cancel.is_set():
                    return
                code = error.code if isinstance(error, AppError) else type(error).__name__
                if isinstance(error, AppError) and error.status < 500:
                    self._log(app_id, "restart_refused", {"code": code, "trips": trips})
                    with self._lock:
                        if self._healing.get(app_id) is healing:
                            self._healing.pop(app_id)
                    return
                self._log(app_id, "restart_failed", {"code": code, "trips": trips})
                with self._lock:
                    healing.trips += 1
                continue
            if healing.cancel.is_set():
                self._halt(app_id)
                return
            self._log(
                app_id,
                "restarted",
                {
                    "trips": trips,
                    "instance_id": started.get("instance_id"),
                    "definition_hash": started.get("definition_hash"),
                },
            )
            with self._lock:
                if healing.trips == trips:
                    healing.thread = None
                    return

    def _cancel_healing(self, app_id: str) -> None:
        with self._lock:
            healing = self._healing.pop(app_id, None)
        if healing:
            healing.cancel.set()

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
        instance.runs += 1
        try:
            resolved = next((item for item in instance.tools if item["name"] == tool), None)
            if resolved is None:
                raise AppError("tool_not_found", "Tool is not in the connected MCP catalog.", 404)
            refuse_tool(tool, resolved)
            inputs = dict(arguments)
            for feed in instance.definition.manifest.feeds:
                if feed in inputs:
                    inputs[feed] = self.artifacts.accept(instance.definition, feed, inputs[feed])
            result = await instance.client.call_tool(tool, inputs, timeout=20)
            data = cast(JsonValue, result.structured_content)
            document: Document = {
                "result": data,
                "content": [
                    cast(Document, block.model_dump(mode="json", by_alias=True))
                    for block in result.content
                ],
                "meta": cast(JsonValue, result.meta),
            }
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

    def call(
        self,
        app_id: str,
        tool: str,
        arguments: Document,
        *,
        pin: Pin | Document | None = None,
        depth: int = 0,
    ) -> Document:
        """Call one of the app's tools: an *ask* (AD-64). A `pin` names the `(pack, version)` the
        caller meant, and is revalidated here before the app sees the call. `depth` is how many
        app operations already sit behind this one: past the host's `call_depth` the ask is
        refused, so a ring of apps cannot run forever."""
        pinned = Pin.parse(pin)
        with self._lock:
            instance = self._instances.get(app_id)
        if instance is None:
            raise AppError("not_running", "Start the app before calling it.", 409)
        self.revalidate(instance, pinned)
        self.bounded(depth)
        try:
            return self._submit(self._call(instance, tool, arguments)).result(timeout=30)
        except concurrent.futures.TimeoutError as error:
            self.stop(app_id)
            raise AppError(
                "tool_timeout", "The tool did not complete within its timeout.", 504
            ) from error

    def revalidate(self, instance: Instance, pin: Pin | None) -> None:
        if pin is None:
            return
        active = instance.definition.manifest
        if (pin.pack, pin.version) == (active.id, active.version):
            return
        raise AppError(
            "pin_stale",
            f"pinned {pin.pack} {pin.version}; {active.id} {active.version} is what runs",
            409,
        )

    def bounded(self, depth: int) -> None:
        if depth < 0:
            raise AppError("invalid_depth", "An ask's depth is never negative.")
        if self.call_depth is not None and depth > self.call_depth:
            raise AppError(
                "call_depth_exceeded",
                f"an ask at depth {depth} passes the host's call_depth {self.call_depth}",
                409,
            )

    def run_job(
        self,
        app_id: str,
        job: str,
        *,
        pin: Pin | Document | None = None,
        profile: str | None = None,
        inputs: Document | None = None,
        principal: str | None = None,
    ) -> Document:
        """Run one job entrypoint in the app's supervised process, after the jobs queued before
        it: the app's own queue is the only capacity a job takes (engine AD-58). The engine's
        `app_op` node calls this when a trigger fires; the supervisor schedules nothing itself.
        It waits as long as the job runs and fails with the supervisor's reason when the app
        stops first. `pin` revalidates the run's `(pack, version)` and `profile` names the
        partition it must write; a job aimed at another profile is refused.

        `inputs` is what the caller tells the job to do (AD-33 change 1): a feed it names is
        accepted as an operation call's is, and a request without inputs is `{"job": job}` as it
        always was. The job's answer comes back under `result` when it gave one. `principal` is
        the caller, recorded on the app's log line for the job."""
        pinned = Pin.parse(pin)
        with self._lock:
            instance = self._instances.get(app_id)
        if instance is None or instance.state != "running":
            raise self._not_running(app_id)
        self.revalidate(instance, pinned)
        if profile is not None:
            self.check_profile(instance.definition, profile)
            if profile != instance.profile:
                raise AppError(
                    "profile_mismatch",
                    f"{app_id} runs profile {instance.profile}; restart it on {profile} to run "
                    "there",
                    409,
                )
        if job not in instance.definition.manifest.entrypoints.jobs:
            raise AppError("job_not_found", f"The app declares no job {job}.", 404)
        asked: Document = {"job": job}
        if inputs is not None:
            given = dict(inputs)
            for feed in instance.definition.manifest.feeds:
                if feed in given:
                    given[feed] = self.artifacts.accept(instance.definition, feed, given[feed])
            asked["inputs"] = given
        queue = instance.volume.root / JOB_QUEUE
        queue.mkdir(parents=True, exist_ok=True)
        name = f"{time.time_ns():020d}-{uuid.uuid4().hex}"
        request, done = queue / f"{name}.request.json", queue / f"{name}.done.json"
        staged = queue / f"{name}.tmp"
        staged.write_text(json.dumps(asked), encoding="utf-8")
        staged.replace(request)
        while not done.exists():
            if instance.state != "running":
                request.unlink(missing_ok=True)
                raise self._not_running(app_id)
            time.sleep(JOB_POLL_SECONDS)
        result = cast(Document, json.loads(done.read_text(encoding="utf-8")))
        done.unlink()
        logged: Document = {"job": job, "ok": result.get("ok") is True}
        if principal is not None:
            logged["principal"] = principal
        self._log(app_id, "job_completed", logged)
        if result.get("ok") is not True:
            raise AppError("job_failed", f"Job {job} raised {result.get('error')}.", 422)
        ran: Document = {
            "app_id": app_id,
            "instance_id": instance.id,
            "job": job,
            "version": instance.definition.manifest.version,
            "profile": instance.profile,
        }
        if "result" in result:
            ran["result"] = result["result"]
        return ran

    def read_output(self, app_id: str, output: str) -> Document:
        """Read the newest artifact `app_id` landed under `output`, with its freshness: its
        `landed_at`, its age, the `stale_after` the app declared and `stale`."""
        found = self.artifacts.latest(app_id, output)
        if found is None:
            raise AppError("unknown_output", f"{app_id} has not landed {output}.", 404)
        return found

    def home_of(self, app_id: str) -> str:
        """The one machine that owns this app instance's volume (AD-64): the placement a move
        recorded for it, or this machine when nothing has moved it."""
        with closing(sqlite3.connect(self.catalog)) as db:
            row = db.execute("SELECT placement FROM homes WHERE id=?", (app_id,)).fetchone()
        return str(row[0]) if row else self.placement

    def snapshot_instance(self, app_id: str, *, to: str) -> Move:
        """Stop the instance and write a verified snapshot of its volume for the machine `to`,
        then hand it the volume lease and record it as the instance's home. The old machine's copy
        stays where it is and is never resumed: it lost the lease by a generation."""
        definition = self._definition(app_id)
        here = self.home_of(app_id)
        if here != self.placement:
            raise AppError("not_home", f"{app_id} is homed on {here}, not {self.placement}.", 409)
        self.stop(app_id)
        volume = Volume(self.home, app_id)
        if not volume.check_write("app.db").is_file():
            raise AppError("volume_missing", "Start the app once before moving it.", 409)
        snapshot_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:8]
        folder = self.home / MOVES / app_id / snapshot_id
        shutil.rmtree(folder, ignore_errors=True)
        snapshot(volume, folder)
        road_lease = VolumeLease(self.home / "road-locks", app_id)
        try:
            # The authority journal and blobs must travel at one serialized point.
            if (volume.root / "road").is_dir():
                shutil.copytree(
                    volume.root / "road", folder / "road", ignore=shutil.ignore_patterns("*.lock")
                )
        finally:
            road_lease.close()
        files = _snapshot_files(folder)
        manifest: Document = {
            "app_id": app_id,
            "snapshot_id": snapshot_id,
            "definition_hash": definition.hash,
            "from": self.placement,
            "to": to,
            "created_at": datetime.now(UTC).isoformat(),
            "checksums": {path.relative_to(folder).as_posix(): checksum(path) for path in files},
        }
        (folder / SNAPSHOT).write_text(json.dumps(manifest), encoding="utf-8")
        lease = VolumeLease(self.home, app_id)
        try:
            handed = lease.handover(to)
        finally:
            lease.close()
        manifest["lease"] = handed.document()
        (folder / SNAPSHOT).write_text(json.dumps(manifest), encoding="utf-8")
        self._record_home(app_id, to, handed.generation)
        self._log(
            app_id,
            "moved",
            {
                "snapshot_id": snapshot_id,
                "from": self.placement,
                "to": to,
                "generation": handed.generation,
            },
        )
        return Move(
            app_id,
            snapshot_id,
            folder,
            self.placement,
            to,
            definition.hash,
            handed,
            len(files),
            sum(path.stat().st_size for path in files),
        )

    def restore_instance(self, app_id: str, snapshot_id: str, *, folder: str | Path) -> Document:
        """Take one instance's snapshot as this machine's volume: verify every checksum, take the
        lease generation the old machine handed over, and record this machine as the home. A
        snapshot for another app, or a lease another machine has already taken, is refused."""
        self._definition(app_id)
        root = Path(folder)
        manifest = _verify_snapshot(root, app_id, snapshot_id)
        handed = Lease.parse(cast("Document", manifest["lease"]))
        if handed is None:
            raise AppError("invalid_snapshot", "The snapshot carries no lease.", 409)
        volume = Volume(self.home, app_id)
        lease = VolumeLease(self.home, app_id, holder=self.placement, expect=handed)
        try:
            # Stage beside the volume, so the swap is one move on one filesystem.
            volume.root.parent.mkdir(parents=True, exist_ok=True)
            staging = volume.root.parent / f".{snapshot_id}.restore"
            shutil.rmtree(staging, ignore_errors=True)
            staging.mkdir(parents=True)
            for path in _snapshot_files(root):
                target = staging / path.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
            if volume.root.is_dir():
                replaced = self.home / MOVES / app_id / f"{snapshot_id}.replaced"
                shutil.rmtree(replaced, ignore_errors=True)
                replaced.parent.mkdir(parents=True, exist_ok=True)
                volume.root.replace(replaced)
            staging.replace(volume.root)
        finally:
            lease.close()
        generation = handed.generation
        self._record_home(app_id, self.placement, generation)
        files = _snapshot_files(volume.root)
        self._log(
            app_id,
            "restored",
            {"snapshot_id": snapshot_id, "placement": self.placement, "generation": generation},
        )
        return {
            "app_id": app_id,
            "snapshot_id": snapshot_id,
            "placement": self.placement,
            "generation": generation,
            "files": len(files),
            "bytes": sum(path.stat().st_size for path in files),
        }

    def _record_home(self, app_id: str, placement: str, generation: int) -> None:
        with closing(sqlite3.connect(self.catalog)) as db, db:
            db.execute(
                "INSERT INTO homes VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                "placement=excluded.placement, generation=excluded.generation, "
                "moved_at=excluded.moved_at",
                (app_id, placement, generation, datetime.now(UTC).isoformat()),
            )

    def contract_problems(
        self, definition: Definition, previous: Definition | None = None
    ) -> dict[str, list[str]]:
        """Every installed consumer that this image's changed `provides` would break, by output
        name, against the image `previous` it replaces. The publish gate calls this before it
        activates the version."""
        with closing(sqlite3.connect(self.catalog)) as db:
            installed = [str(row[0]) for row in db.execute("SELECT id FROM selected ORDER BY id")]
        consumers = [
            self._definition(app_id) for app_id in installed if app_id != definition.manifest.id
        ]
        return contract_problems(definition, consumers, previous)

    def _not_running(self, app_id: str) -> AppError:
        status = self.status(app_id)
        breaker = status.get("breaker")
        reason = breaker.get("reason") if isinstance(breaker, dict) else None
        why = f" ({reason})" if reason else ""
        return AppError("not_running", f"The app is {status.get('status')}{why}.", 409)

    async def _resource(self, instance: Instance, uri: str) -> list[Document]:
        if instance.client is None:
            raise AppError("not_running", "Start the app before reading a resource.", 409)
        contents = await asyncio.wait_for(instance.client.read_resource(uri), timeout=20)
        return [
            cast(Document, content.model_dump(mode="json", by_alias=True)) for content in contents
        ]

    def resource(self, app_id: str, uri: str) -> list[Document]:
        with self._lock:
            instance = self._instances.get(app_id)
        if instance is None:
            raise AppError("not_running", "Start the app before reading a resource.", 409)
        try:
            return self._submit(self._resource(instance, uri)).result(timeout=30)
        except concurrent.futures.TimeoutError as error:
            raise AppError(
                "resource_timeout", "The resource did not complete within its timeout.", 504
            ) from error

    def emit(self, app_id: str, data: Document) -> None:
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
        self.emit(app_id, data)

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
        for app_id in list(self._healing):
            self._cancel_healing(app_id)
        for app_id in list(self._instances):
            self.stop(app_id)
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread:
                self._thread.join(timeout=10)
            self._loop.close()
            self._loop = None
