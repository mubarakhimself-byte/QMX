"""The composition (SOLUTION-DESIGN 27.1): one process per home serves the copilot's chats, the
workflow engine, the control doors and the webhook door on one port behind one bearer.

`serve` builds, in order: the home's single-instance lock, the router's own thread and loop,
`ControlService` (the one settings reader), the `Harness` (whose relay adopts the router's loop),
the engine with its scheduler, and the control app with the chat, engine and control routes behind
the principal door. The host is the one writer of the home's Library store `<home>/library/`
(Library AD-5): it opens the store with the engine's one redaction (AD-37) and hands it to
`ControlService`, so the engine's `EngineLibraryAdapter`, the control's `library_*` rows and the
copilot's search read and write that one store (MIGRATION step 6). The apps supervisor is
`ControlService.app_runtime()`. The engine's permission policy and
hook sink are registered on the harness, both named `engine`, before the engine resumes any run, so
a chat reloaded after a restart finds them. The harness is `RecordedHarness`: the session recorder
writes every chat's `session` item into the store (Library AD-21) and exports idle chats once a
day. On stop the engine drains, the Library store closes, then the harness closes, which stops the
relay, and the router thread stops last.

While it serves, the host writes one heartbeat row for itself and one per running app every
`heartbeat.interval` (AD-65) into the home's heartbeat log, prunes the log to its window once an
hour, and serves the log to the copilot's `ops_heartbeats` row through the harness. It also ships
every app's JSONL logs and the engine's open incidents through the one telemetry switch
(`app_logs`), and the doctor's deep-logs row says what went or that telemetry is off.

The lock is an OS lock on `<home>/engine.lock` (AD-3, L-64, L-70): the OS releases it when the
process dies, so a crashed host never blocks the next one, and two hosts cannot both take it.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Collection, Generator, Iterable, Mapping, Sequence
from contextlib import contextmanager, suppress
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import IO, Any, Final, Literal, cast

import httpx
import psutil
import qmx_control.server
import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request
from pydantic import JsonValue
from qma.harness import Harness, QmxHome, SessionId, chat_routes, control_service
from qma.harness.home import DoctorLine
from qma.harness.tools import HostRead
from qma.telemetry import THIS_PC, configured, target
from qmf.core import TypedRefusal, fingerprint_bytes, is_refusal
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qmx_apps.artifacts import Ending, Lander
from qmx_apps.artifacts import Landing as AppLanding
from qmx_apps.artifacts import Ticket as AppTicket
from qmx_apps.errors import AppError
from qmx_apps.manifest import HOST_SECRETS, Definition
from qmx_apps.supervisor import JOB_QUEUE, MARKET_STORE, RUNS, Supervisor
from qmx_apps.volume import Volume
from qmx_broker.credentials import CredentialManager, KeyStore
from qmx_control.models import Document
from qmx_control.node import PLACE, library_primary
from qmx_control.primary import CARD_REF, HOLD, Flip
from qmx_control.service import QMB_DEFAULTS, ControlService
from qmx_engine.admission import setting
from qmx_engine.control_door import EngineDoor
from qmx_engine.heartbeat import (
    INTERVAL_S,
    WINDOW_DAYS,
    ClassUse,
    ClockFacts,
    Heartbeat,
    HeartbeatLog,
    HubLink,
    Pause,
    kinds_digest,
    latest,
    node_kinds,
    qmx_version,
)
from qmx_engine.ledger import redact
from qmx_engine.memory import install
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.ports.library import JsonObject
from qmx_engine.ports.library import LibraryRefused as EngineLibraryRefused
from qmx_engine.ports.router import Refused, Reply
from qmx_engine.ports.router import Row as EngineRow
from qmx_engine.ports.router import adopt as adopt_router
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.runner import Engine
from qmx_engine.service.forward import (
    Forwarder,
    HostKeys,
    forward_router,
    owned_instances,
    placement_rows,
    wall,
)
from qmx_engine.service.rest import engine_router
from qmx_engine.settings import PC
from qmx_engine.workers.remote import PlacementWorker
from qmx_home import Layout
from qmx_home.backup.restore import RESTORE_LOCK
from qmx_home.files import Busy, Held, hold
from qmx_home.rclone import Rclone
from qmx_home.versions import StoreRefused, upgrade_moment_ended
from qmx_hub.server import Hub, in_process
from qmx_judge.judge import STUDY_KIND, VERDICT_KIND, spec_edit, spec_problems
from qmx_judge.landing import (
    G_CHECK,
    RESULT_KIND,
    TEST_REPORT,
    CheckFirst,
    GRecord,
    Stored,
    run_kind,
)
from qmx_judge.landing import Lander as RunLander
from qmx_judge.paper import PaperRule
from qmx_judge.runs import BundleRefused, Landing, ResultBundle, RunId, Ticket, parse_bundle
from qmx_judge.tries import TRY_KIND, spec_edit_item, try_item
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.cards import Partition, SeriesCard, write_card
from qmx_library.client import OwnerTable
from qmx_library.kinds import Checker, Problem
from qmx_library.landing import NOT_PRIMARY
from qmx_library.port import (
    Commit,
    Draft,
    LibraryRefused,
    MergeResult,
    ObjectId,
    StoreRole,
    Strategy,
)
from qmx_library.principal import MAIN, Act, Principal, state_ref
from qmx_library.store import Store
from qmx_memory.engine import RecallEngine
from qmx_memory.hindsight import HindsightConfig, HindsightIndex
from qmx_remote.models import Target
from qmx_remote.providers import registry as provider_registry
from qmx_router import complete as router_complete
from qmx_router import registry as model_registry
from qmx_router.passes import PassAuthority
from qmx_router.pool import NoAccount
from qmx_router.profiles import ProfileName
from qmx_router.relay import Relay
from qmx_router.server import (
    LOOPBACK,
    NODE_PORT_FILE,
    TAILNET,
    VAULT_STORE,
    NodeState,
    RouterService,
    node_app,
)
from qmx_tools.gather import check_unit, entry_problems, gather
from qmx_tools.service import attach_node
from uvicorn.config import STARTUP_FAILURE

from qmx_host.app_logs import AppLogs
from qmx_host.backups import Backups, Refusal, backups_router
from qmx_host.bring_in import recheck_at_start
from qmx_host.clock_probe import (
    CALENDAR_WARN_DAYS,
    DST_NOTICE_DAYS,
    PROBE_S,
    TZDATA_MAX_AGE_DAYS,
    calendar_line,
    clock_line,
    mismatch_line,
    probe_from,
    tzdata_line,
    tzdata_version,
)
from qmx_host.connect import KINDS, Connect, World, connect_router, placement
from qmx_host.connect_logs import Logs, NeedsAdmin, OpenObserveProcess
from qmx_host.disk import MIB, floor_bytes, free_bytes, give_way
from qmx_host.door import PrincipalDoor, templates_router
from qmx_host.first_start import enable_first_party, land_dummy, land_port, land_wave
from qmx_host.host_route import ANSWERS, Answering, Answers, held_keys, host_router
from qmx_host.jobs import Jobs, Stopped
from qmx_host.keys import keys_router
from qmx_host.lifecycle import LifecycleWriter, MoveRefused, judge_moves
from qmx_host.maintenance import maintenance_router
from qmx_host.market_data import (
    SEAL_READ_REASON,
    HoldoutAsk,
    MarketDoor,
    Placement,
    market_router,
)
from qmx_host.node_link import NodeLink
from qmx_host.process_record import STATE, recorded_host
from qmx_host.promote import Promoter, harvested_calibrations, promote_router
from qmx_host.publish_collection import publish_collection_router
from qmx_host.records import Cadence, Harvester, Projection, Pull, Records, append_roots
from qmx_host.sessions import RecordedHarness, SessionRecorder, write_snapshot
from qmx_host.streams import Streams
from qmx_host.vault_acl import KeyRefused, VaultRefused, owner_only, read_key
from qmx_host.venue_records import VenueRecords, node_call, record_markets, refresh_s

type Role = Literal["pc", "node", "server"]
"""`server` is the node role plus the Library service: on the server the one `qmx_host` process
opens the store as its one writer and answers the Library routes in process (AD-19, AD-26)."""

LOCK: Final = "engine.lock"
LIBRARY: Final = "library"
MARKET: Final = "market"
"""The home's market-data root: the price partitions the door writes, and its handles (AD-28)."""
FACTS_SCHEMA: Final = "qmx.host.facts/1"
"""The schema of `road/host/facts.json`, the host facts in every app volume (AD-307)."""
START_S: Final = 30.0
HOST_HISTORY: Final = 10
"""The host rows `ops_heartbeats` returns beside the newest row per subject: five minutes at the
default interval."""
MEMORY_FOLDER: Final = "memory"
"""The home's memory folder: the FTS5 file, Hindsight's own folders and the snapshot slot."""
MEMORY_ROLE: Final = "memory_extractor"
"""The grant Hindsight's extractor calls run on (SOLUTION-DESIGN 28.6, AD-18)."""
SYNC_INTERVAL_S: Final = 30.0
"""How often the PC asks the Library server what moved since its last sequence (AD-10). The
`[library] sync_interval` setting raises or lowers it."""
VAULT: Final = "vault"
PAIRING_KEY: Final = "pairing-key"
VAULT_FIXED: Final = "your keys folder was readable by other users, fixed"
APP_SECRET: Final = re.compile(r"qmx/[a-zA-Z0-9_-]+")
"""The secret names a manifest may declare (`qmx_apps.manifest`), checked again before a path."""
HOST_VAULT: Final = frozenset(service.removeprefix("qmx/") for service in HOST_SECRETS)
"""The host's own files in `<home>/vault/`, which no app may read: every name in
`qmx_apps.manifest.HOST_SECRETS`, among them the home's pairing key, which signs every run pass,
the control token a flat home kept there, and an unpaired home's run pass key. Names are
case-folded, because NTFS opens `PAIRING-KEY` as `pairing-key`."""
DELIVERY_HEADERS: Final = ("X-QMX-Delivery", "X-GitHub-Delivery", "Idempotency-Key", "X-Request-Id")
DID_NOT_OPEN: Final = 2
"""`serve`'s exit when a store, the engine or the Library refused to open (loose strings Appendix
E); `__main__` exits 2 for a folder it refuses before the host starts."""
PORT_TAKEN: Final = 4
OPEN_REFUSALS: Final = (StoreRefused, LibraryRefused, EngineLibraryRefused)
"""What a store, the engine's ledger or either Library side raises when it must not open. Two
classes share the name `LibraryRefused`, one per side of the engine's Library port."""
UNIT_CHECKER: Final = "qml.unit/1"
STUDY_CHECKER: Final = "qmx.study-spec/1"
ENTRY_CHECKER: Final = "qml.entry/1"
CHECK_FAILED: Final = "check_failed"


class HostRunning(Exception):
    def __init__(self, home: Path, pid: int | None) -> None:
        who = "an unknown process" if pid is None else f"PID {pid}"
        super().__init__(f"refused: {home} already has a host, {who}; stop it first.")


class PlaceRefused(Exception):
    """This host's place name is missing or not a place name; the message is the one line."""


def _lock(handle: IO[bytes]) -> None:
    if sys.platform == "win32":
        import msvcrt  # noqa: PLC0415

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl  # noqa: PLC0415

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


class RestoreFinishing(Exception):
    """A restore is being finished in the folder, so no host may start on it now."""


@contextmanager
def single_instance(home: Path) -> Generator[None]:
    """Hold the home's lock and its record for as long as the block runs. Raises `HostRunning`
    while another process holds it, and `RestoreFinishing` while a restore's finish holds the
    folder's `backups/restore.lock`, which a QMX folder's host takes first and lets go once it
    holds `engine.lock`, so no host starts while a finish runs (F5)."""
    layout = Layout.from_home(home)
    gate: Held | None = None
    if layout.label.is_file():
        try:
            gate = hold(layout.backups / RESTORE_LOCK, "")
        except Busy:
            raise RestoreFinishing(
                f"QMX did not start: a restore is finishing in {layout.root}; start QMX again "
                "when it has"
            ) from None
    handle = (home / LOCK).open("a+b")
    try:
        _lock(handle)
    except OSError:
        handle.close()
        raise HostRunning(home, recorded_host(home)) from None
    finally:
        if gate is not None:
            gate.release()
    me = psutil.Process()
    record = home / STATE
    try:
        yield
    finally:
        if recorded_host(home) == me.pid:
            record.unlink(missing_ok=True)
        handle.close()


def record(home: Path, port: int) -> None:
    me = psutil.Process()
    state = {"pid": me.pid, "port": port, "created": me.create_time()}
    (home / STATE).write_text(json.dumps(state), encoding="utf-8")


def serve_forever(
    home: Path,
    *,
    port: int,
    role: Role,
    ui_origin: str,
    scrubbed: Sequence[str],
    keep: Sequence[str],
    library_root: Path | None = None,
    place: str = "",
) -> int:
    """`serve` under the folder's lock on a port bound before anything opens. Every refusal before
    the host serves is one line on stderr and an exit code the desktop app branches on (Appendix
    E); one raised after it served stops the host like any other error."""
    served = threading.Event()
    try:
        with single_instance(home), bound(TAILNET if role == "server" else LOOPBACK, port) as sock:
            record(home, sock.getsockname()[1])
            asyncio.run(
                serve(
                    home, sock, role, ui_origin, scrubbed, keep, library_root, place, served=served
                )
            )
    except (HostRunning, PlaceRefused, RestoreFinishing) as refused:
        print(refused, file=sys.stderr)
        return 1
    except PortTaken as taken:
        print(f"QMX did not start: {taken}", file=sys.stderr)
        return PORT_TAKEN
    except (*OPEN_REFUSALS, AppDidNotStart, VaultRefused) as refused:
        if served.is_set():
            raise
        print(f"QMX did not start: {' '.join(str(refused).split())}", file=sys.stderr)
        return DID_NOT_OPEN
    return 0


class PortTaken(Exception):
    def __init__(self, port: int) -> None:
        super().__init__(
            f"port {port} is in use. Stop what holds it, or start QMX on another port."
        )


class AppDidNotStart(Exception):
    """Uvicorn exits 3 when the app's startup fails, the code Appendix E keeps for a first start
    that is due; the host names it as one line and exits 2 instead."""

    def __init__(self) -> None:
        super().__init__(
            "the host's app failed while it started up. Its error is in the lines above; fix that "
            "and start QMX again."
        )


@contextmanager
def bound(address: str, port: int) -> Generator[socket.socket]:
    """The host's one socket, bound once so a taken port is found before anything opens; uvicorn
    listens on it later.

    Uvicorn sets `SO_REUSEADDR` on the sockets it binds itself; on Windows that lets a second bind
    take a port in use, so here it is set only elsewhere, where it only skips `TIME_WAIT`. Windows
    also lets a loopback bind share a port another program listens on at every interface, so there
    the wildcard address is tried first, and the host's own socket is exclusive, so no later
    program can share its port either.
    """
    if os.name == "nt" and port and address != TAILNET:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wildcard:
            try:
                wildcard.bind((TAILNET, port))
            except OSError:
                raise PortTaken(port) from None
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if os.name == "nt":
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    else:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    with sock:
        try:
            sock.bind((address, port))
        except OSError:
            raise PortTaken(port) from None
        yield sock


class RelayRouter:
    """The engine's `RouterPort` over this host's one relay (AD-56): the registry's rows, one
    `complete` on the key and GPT lanes, and the pool lease an engine attempt holds."""

    def __init__(self, relay: Relay) -> None:
        self.relay = relay

    def rows(self) -> tuple[EngineRow, ...]:
        registry = self.relay.registry()
        return tuple(
            EngineRow(
                row.qmx_id,
                row.provider,
                row.native,
                row.class_,
                row.window,
                row.chars_per_token,
                row.count_tokens,
                registry.providers[row.provider].use == "test_only",
            )
            for row in registry.rows()
        )

    async def complete(
        self,
        role_or_model: str,
        messages: Sequence[Mapping[str, object]],
        *,
        schema: Mapping[str, object] | None = None,
        session: str | None = None,
        system: str = "",
        max_tokens: int = 4096,
        roles: Mapping[str, Sequence[str]] | None = None,
    ) -> Reply:
        try:
            done = await self.relay.complete(
                role_or_model,
                messages,
                schema=schema,
                session=session,
                system=system,
                max_tokens=max_tokens,
                roles=roles,
            )
        except router_complete.Refused as refused:
            raise Refused(str(refused)) from None
        return Reply(
            done.text,
            done.qmx_id,
            done.model,
            done.account,
            dict(done.usage),
            done.data,
            done.ms,
        )

    def hold(self, *, provider: str, model: str, affinity: str) -> str:
        try:
            lease = self.relay.accounts().lease(provider=provider, model=model, affinity=affinity)
        except NoAccount as refused:
            raise Refused(str(refused)) from None
        return lease.account.id

    def let_go(self, affinity: str) -> None:
        self.relay.accounts().release_affinity(affinity)


def harness_relay(harness: Harness) -> Relay:
    """The relay the harness started. It lives in the harness's chat dependencies, which
    `qma.harness` exposes no public accessor for; RTRP moves the router behind the tailnet."""
    deps = harness._deps  # pyright: ignore[reportPrivateUsage]  # the one private read
    return deps.relay


TARGET_FIELDS: Final = frozenset(
    {
        "provider",
        "host",
        "root",
        "bucket_local",
        "image",
        "gpu",
        "gpu_type",
        "executor",
        "runner_id",
        "runner_dir",
        "project",
    }
)
"""The `Target` fields a `[placement]` row may carry; the rest of the row is QMX's own."""


class HubGateway:
    """The Hub's run endpoints: the event tail and the result for one run (AD-13, AD-20)."""

    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, run_id: str, name: str) -> httpx.Response:
        return httpx.get(f"{self.base_url}/runs/{run_id}/{name}", timeout=self.timeout)

    def events(self, run_id: str) -> list[dict[str, Any]]:
        try:
            found = self._get(run_id, "events")
        except httpx.HTTPError:
            return []
        if found.status_code != 200:
            return []
        rows = found.json()
        if not isinstance(rows, list):
            return []
        listed = cast(list[object], rows)
        return [cast(dict[str, Any], row) for row in listed if isinstance(row, dict)]

    def result(self, run_id: str) -> Document | None:
        try:
            found = self._get(run_id, "result")
        except httpx.HTTPError:
            return None
        if found.status_code != 200:
            return None
        body = found.json()
        return cast(Document, body) if isinstance(body, dict) else None


def remote_worker(
    home: Path, core: Engine, authority: PassAuthority, own_door: str = "", *, host_id: str = ""
) -> PlacementWorker | None:
    """The `node` role's worker: an attempt placed on another owned machine runs there (AD-20).

    A `[placement]` row with a provider is a machine this host dispatches to; the row's
    `gateway_url` is the Hub that serves its `runs/<run_id>/` tail and result. With no such row
    this host keeps its local worker, which is the one-machine case. The pass is minted here and
    travels in `QMX_RUN_PASS`; no key does. It carries the node's `parameters.data_scope`, which
    this host's door checks a remote read against, and a row's `door_url` is the door its
    attempts read price data through (AD-70). A row that names none reads through `own_door`,
    this host's door, which verifies the pass it minted. `authority` is the one it verifies with.
    """
    settings = core.settings
    names = sorted(
        {
            key.split(".")[1]
            for key in settings
            if key.startswith("placement.") and key.count(".") >= 2 and key.split(".")[1]
        }
    )
    providers: dict[str, Any] = {}
    doors: dict[str, str] = {}
    gateway_url = ""
    for name in names:
        if settings.get(f"placement.{name}.provider") is None:
            continue
        target = Target.model_validate(
            {
                field: settings[f"placement.{name}.{field}"]
                for field in TARGET_FIELDS
                if f"placement.{name}.{field}" in settings
            }
        )
        bucket = settings.get(f"placement.{name}.bucket")
        providers[name] = provider_registry(target, str(bucket) if bucket is not None else "")
        door = settings.get(f"placement.{name}.door_url") or own_door
        if door:
            doors[name] = str(door)
        found = settings.get(f"placement.{name}.gateway_url")
        if found is not None:
            gateway_url = str(found)
    if not providers or not gateway_url:
        return None

    def mint(job: Any) -> str:
        return authority.mint(
            run=job.run_id,
            placement=job.placement,
            attempt=job.attempt,
            data_scope=data_scope_of(job.node_definition),
        )[1]

    return PlacementWorker(
        gateway=HubGateway(gateway_url),
        providers=providers,
        settings=settings,
        mint=mint,
        remote=providers,
        live=lambda: host_row(home, host_id),
        doors=doors,
    )


def data_scope_of(node_definition: Mapping[str, Any]) -> tuple[str, ...]:
    """The series a node's `parameters.data_scope` names, which its run pass may read."""
    parameters: object = node_definition.get("parameters")
    if not isinstance(parameters, Mapping):
        return ()
    found: object = cast("Mapping[str, object]", parameters).get("data_scope")
    return (
        tuple(str(item) for item in cast("list[object]", found)) if isinstance(found, list) else ()
    )


def host_row(home: Path, host_id: str) -> Heartbeat | None:
    """The newest heartbeat row of the machine `host_id`, or None before its first beat. A home
    that also runs the Hub holds every machine's row, so it is read by id, never the first host
    row found. A dispatched attempt's resources and session count read it (D-11)."""
    return latest(home).get(f"host:{host_id}")


def hindsight_runs(control: ControlService, role: Role) -> bool:
    """Hindsight is the PC's index (ruling 119). On the `node` and `server` roles it runs only
    when `[memory] hindsight` says so (PRB-S measured it over the server's RAM line), and recall
    there runs on the built FTS5 engine otherwise (engine AD-52)."""
    return role == "pc" or section(control, "memory").get("hindsight") is True


def compose_memory(
    harness: RecordedHarness, store: Store, home: Path, control: ControlService, role: Role
) -> RecallEngine:
    """Build the home's memory engine and feed it to the port the engine reads and to the
    harness's retain worker, then render the snapshot slot (AD-18).

    Hindsight is the index where `hindsight_runs` says so, and it starts lazily on the first read
    or retain, so a host that never touches memory pays nothing. Its extractor calls go through
    the router's key lane on a `memory_extractor` grant: Hindsight holds the grant, never a
    provider key. A grant the relay refuses is reported and left out, and Hindsight then retains
    without a model call, because a row is already QMX's own digest.
    """
    index = (
        HindsightIndex(_hindsight(harness, home, control))
        if hindsight_runs(control, role)
        else None
    )
    engine = RecallEngine(store, index=index, home=home / MEMORY_FOLDER)
    install(engine)
    harness.remember_into(engine)
    try:
        write_snapshot(engine, home)
    except (OSError, LibraryRefused) as error:
        print(f"memory: the snapshot slot was not written: {error}", file=sys.stderr)
    return engine


def _hindsight(harness: RecordedHarness, home: Path, control: ControlService) -> HindsightConfig:
    """Hindsight's folders in the QMX folder, the relay's address, the grant minted for the
    extractor role, and the telemetry target `[telemetry] send_to` names."""
    profile, model = _extractor(control)
    grant, base = "", ""
    if model:
        try:
            minted = asyncio.run(harness_relay(harness).grant(SessionId("memory"), profile))
            base, grant = minted.base_url, str(minted.secret)
        except Exception as error:  # no grant: retain stays local, reflect refuses
            print(f"memory: no extractor grant: {type(error).__name__}: {error}", file=sys.stderr)
    return HindsightConfig(
        layout=Layout.from_home(home),
        base_url=f"{base}/v1" if base else "",
        grant=grant,
        model=model,
        telemetry=configured(home),
    )


def _extractor(control: ControlService) -> tuple[ProfileName, str]:
    """The `memory_extractor` role's first candidate as `(profile, model)`. The role is his to
    edit; the plan's default list is the mid tier (E/settings.py)."""
    roles = control.settings_get("roles")
    found = roles.get(MEMORY_ROLE)
    for row in found if isinstance(found, list | tuple) else []:
        profile, _, model = str(row).partition("/")
        return ProfileName(profile), model or profile
    return ProfileName(""), ""


async def node_sidecar(home: Path, authority: PassAuthority) -> None:
    """The `node` role's tailnet app (AD-12, AD-41): the facts this machine holds, the vault
    ciphertext it was given, and the pass list. It binds every interface on an ephemeral port,
    pinned in `<home>/node.port`, and every route but health needs a pass from `authority`, the
    host's one."""
    state = NodeState(site=socket.gethostname(), passes=authority)
    stored = home / VAULT_STORE
    if stored.exists():
        # The entries `qmx node vault install` wrote. A file that does not parse is skipped: the
        # next install rewrites it, and a node with no ciphertext still serves facts and passes.
        with suppress(OSError, ValueError):
            state.vault.sync(json.loads(stored.read_text(encoding="utf-8")))
    config = uvicorn.Config(
        node_app(state),
        host=TAILNET,
        port=0,
        lifespan="off",
        access_log=False,
        log_config=None,
    )
    server = uvicorn.Server(config)
    serving = asyncio.create_task(server.serve())
    while not server.started:
        if serving.done():
            serving.result()
        await asyncio.sleep(0.01)
    port = 0
    for listener in server.servers[0].sockets if server.servers else ():
        if listener.family == socket.AF_INET:
            port = listener.getsockname()[1]
            break
    (home / NODE_PORT_FILE).write_text(f"{port}\n", encoding="utf-8")
    try:
        await serving
    finally:
        server.should_exit = True


def store_role(home: Path, serving: bool) -> StoreRole:
    """The server's store is the writer, and so is the PC's while `[library] primary` is `pc`, the
    default before the flip. After the flip the PC keeps a replica (AD-14, AD-19)."""
    return "writer" if serving or library_primary(home) == "pc" else "replica"


def primary_of(home: Path, store: Store) -> str:
    """Which store is primary: the record on `refs/primary` once a flip wrote one, else the
    home's `[library] primary` (AD-14, AD-19)."""
    learned = store.epoch
    return library_primary(home) if learned is None else learned.primary


class HostStore(Store):
    """The host's one store, with the two refusals the host owes before every ref move.

    While a flip holds (MIGRATION step 8.2), every move but the flip's own card is refused
    `primary_moving`; reads keep working. On the server, while the PC is primary, `main` is
    refused: the PC's history arrives by sync, which mirrors and never puts, and a server run
    lands on `refs/runs` and reaches `main` through the PC.
    """

    flip: Flip | None = None
    """The flip he started, while one is in progress."""
    primary: Callable[[], str] | None = None
    """On the server only: which store is primary right now."""
    lifecycle: LifecycleWriter | None = None
    """This PC's lifecycle writer, which records the judge's move when a verdict lands."""

    def put(
        self, who: Principal, draft: Draft, *, on: str, expected_head: ObjectId | None
    ) -> Commit:
        commit = super().put(who, draft, on=on, expected_head=expected_head)
        if on == MAIN and commit.object_id != commit.prev_head:
            self._landed(who, commit.object_id)
        return commit

    def merge(
        self, who: Principal, item: str, *, from_ref: str, into: str, strategy: Strategy = "auto"
    ) -> MergeResult:
        merged = super().merge(who, item, from_ref=from_ref, into=into, strategy=strategy)
        if into == MAIN and merged.outcome in ("fast-forward", "merged"):
            self._landed(who, merged.object_id)
        return merged

    def close(self) -> None:
        if self.lifecycle is not None:
            self.lifecycle.close()
        super().close()

    def _landed(self, who: Principal, object_id: ObjectId) -> None:
        """What the host owes once a record reaches `main`, after its put has committed (a
        checker runs inside the put and cannot write): a verdict's judge moves, and a study
        spec's `spec_edit` try when a result exists against an earlier version of it."""
        kind = str(self._require(object_id)[2])
        if kind == VERDICT_KIND and self.lifecycle is not None:
            record_judge_moves(self, self.lifecycle, object_id)
        elif kind == STUDY_KIND:
            land_spec_edit(self, who, object_id)

    def _check_owner(self, who: Principal, ref: str, act: Act) -> None:
        super()._check_owner(who, ref, act)
        if self.flip is not None and self.flip.held and ref != CARD_REF:
            raise LibraryRefused(HOLD, f"the Library is moving to the server; {ref} waits for it")
        if ref == MAIN and self.primary is not None and self.primary() != "server":
            raise LibraryRefused(
                NOT_PRIMARY, "primary is pc; main moves on the server only by sync from it"
            )


def open_store(home: Path, root: Path, *, serving: bool, floor: int) -> HostStore:
    """The host's store at `root`, as the writer or replica its role names."""
    opened = HostStore.open(
        root,
        redactor=redact,
        floor_bytes=floor,
        name="server" if serving else "pc",
        role=store_role(home, serving),
        upstream=None if serving else HubBlobs(library_client(home)),
    )
    store = cast("HostStore", opened)
    if serving:
        store.primary = lambda: primary_of(home, store)
    return store


def recheck_test_runs(home: Path, store: Store) -> None:
    """The bring-in's one pass for test runs at host start (MD3). A refusal is printed and the
    host starts anyway; the report stays unstamped, so the next start tries again."""
    try:
        archived = recheck_at_start(home, store)
    except (LibraryRefused, OSError, sqlite3.Error, ValueError, KeyError) as refused:
        frozen = home / "migration" / "pre" / "library.db"
        print(
            f"library: test runs from the old Library not checked in {frozen}: {refused}",
            file=sys.stderr,
        )
        return
    if archived:
        print(f"library: {archived} old items made by test runs archived", file=sys.stderr)


def unit_problems(store: Store) -> Checker:
    """`qml.unit/1`, the `unit` kind's publish check: QML's layers A to F over the document with
    what `gather` found in this store."""

    def checked(fields: JsonObject) -> list[Problem]:
        result, warnings = check_unit(store, fields)
        for line in warnings:
            print(f"library: {line}", file=sys.stderr)
        return [
            Problem(p.message, p.where, CHECK_FAILED, f"{p.layer}/{p.kind.value}")
            for p in result.errors
        ]

    return checked


def entry_check(fields: JsonObject) -> list[Problem]:
    """`qml.entry/1`, the put check of a `component` marked `qmx.entry/1`: its face reads as
    QML's entry. QML names a face problem by its place in the face, under `/entry` here."""
    return [
        Problem(
            p.message,
            (p.where if p.where == "/component_type" else f"/entry{p.where}".rstrip("/"),),
            CHECK_FAILED,
            "entry/face",
        )
        for p in entry_problems(fields)
    ]


def study_check(fields: JsonObject) -> list[Problem]:
    """`qmx.study-spec/1`, the `study-spec` kind's put check: the judge's own rules for a spec
    beyond its shape. A new version saved after a result exists lands its `spec_edit` try from
    the host's store once the put commits (`land_spec_edit`)."""
    return [Problem(text, ("",), CHECK_FAILED, "study-spec") for text in spec_problems(fields)]


def register_checkers(store: Store) -> None:
    """The checkers the Library's kind files name, registered at composition (Part A AD-112)."""
    store.register_checker(UNIT_CHECKER, unit_problems(store))
    store.register_checker(ENTRY_CHECKER, entry_check)
    store.register_checker(STUDY_CHECKER, study_check)


JOURNALS: Final = "journals"
"""This PC's journal root, where the host's own streams append (Part B AD-209)."""


def lifecycle_writer(home: Path, control: ControlService, machine: str) -> LifecycleWriter:
    """This PC's one lifecycle writer, reading `[units] lifecycle.auto_paper` at each move."""

    def auto_paper() -> bool:
        units = cast(dict[str, object], control.settings_get("units"))
        return cast(dict[str, object], units.get("lifecycle") or {}).get("auto_paper") is True

    return LifecycleWriter(home / JOURNALS, machine, f"qmx-host {qmx_version()}", auto_paper)


def record_judge_moves(store: Store, writer: LifecycleWriter, verdict_id: str) -> list[str]:
    """The judge's draft to tested or draft to parked moves of a landed verdict. A refusal is
    printed: the verdict stands, and the market keeps its state."""
    fields = store.get(OPERATOR_READ, verdict_id).fields
    unit = str(fields.get("unit", ""))
    document = store.get(OPERATOR_READ, unit).fields if store.catalog.row(unit) else {}
    unit_id = str(document.get("unit_id") or unit)
    try:
        return writer.record_verdict(
            judge_moves(verdict_id, fields, unit_id=unit_id, at=datetime.now(UTC))
        )
    except MoveRefused as refused:
        print(f"lifecycle: {verdict_id} moved nothing: {refused}", file=sys.stderr)
        return []


def land_spec_edit(store: Store, who: Principal, spec_id: str) -> str | None:
    """Land the `spec_edit` try of a study spec version whose earlier versions already have a
    result: editing the rules after a result is a counted try (Level 0 AD-25). Once per version;
    saving the same fields again is no edit."""
    earlier: list[str] = []
    queue = list(store.catalog.parents(spec_id))
    while queue:
        parent = queue.pop()
        if parent not in earlier:
            earlier.append(parent)
            queue += store.catalog.parents(parent)
    results = [r for e in earlier for r in store.with_field(RESULT_KIND, "study", e)]
    fields = store.get(OPERATOR_READ, spec_id).fields
    same = [
        p for p in store.catalog.parents(spec_id) if store.get(OPERATOR_READ, p).fields == fields
    ]
    item = spec_edit_item(spec_id)
    found = store.head(item, MAIN)
    if not results or same or found is not None:
        return None if found is None else found[0]
    first = store.get(OPERATOR_READ, results[0]).fields
    unit, run_id = str(first.get("unit", "")), str(first.get("run_id", ""))
    opened = store.head(try_item(run_id, "opened"), MAIN)
    family = store.get(OPERATOR_READ, opened[0]).fields.get("family") if opened else None
    edit = spec_edit(
        spec_id,
        unit=unit,
        family=str(family or unit),
        principal=str(who),
        at=datetime.now(UTC).isoformat(),
    )
    title = f"spec_edit {spec_id}"
    draft = Draft(TRY_KIND, item, title, title, fields=cast(JsonObject, edit.fields()))
    return store.put(OPERATOR_READ, draft, on=MAIN, expected_head=None).object_id


def enable_apps(home: Path, runtime: Supervisor) -> None:
    """The first start's one click, kept at every start: the first-party apps enabled in this
    folder, QMB first, are installed if missing and started beside the host, which does not wait
    for their environments."""
    try:
        enabled = enable_first_party(home, runtime)
    except (AppError, OSError, ValueError) as refused:
        print(
            f"apps: the first-party apps did not start, again next start: {refused}",
            file=sys.stderr,
        )
        return
    if enabled:
        print(f"apps: {', '.join(enabled)} started", file=sys.stderr)


def close_stranded_runs(home: Path, run: QmbRun) -> None:
    """Close what the last host left open. A store or volume that refuses is named and the host
    starts anyway; the next start tries again."""
    try:
        closed = fail_stranded_runs(home, run)
    except (AppError, LibraryRefused, OSError, ValueError) as refused:
        print(f"apps: the runs the last host left open did not close: {refused}", file=sys.stderr)
        return
    if closed:
        print(f"apps: closed as failed, the host restarted: {', '.join(closed)}", file=sys.stderr)


def land_first_unit(store: Store) -> None:
    """The dummy unit waits in his Library as a draft from the first start on (AD-118). A store
    that refuses the put (a replica, a read-only store) is named and the host starts anyway."""
    try:
        landed = land_dummy(store)
    except LibraryRefused as refused:
        print(f"library: the dummy unit did not land: {refused}", file=sys.stderr)
        return
    if landed is not None:
        print("library: the dummy unit waits in the Library as a draft", file=sys.stderr)


def land_ported_dictionary(store: Store) -> None:
    """The 239 ported dictionary entries wait in his Library as drafts in one collection from the
    PC's first start on (AD-114). A server or a node, which may run without the seed folder,
    never lands them. A store that refuses the put, or a QMX that runs without its seed
    folder, is named and the host starts anyway; the next start tries again."""
    try:
        landed = land_port(store)
    except (LibraryRefused, OSError, ValueError) as refused:
        print(f"library: the ported dictionary did not land: {refused}", file=sys.stderr)
        return
    if landed is not None:
        print(f"library: the ported dictionary waits in the Library: {landed}", file=sys.stderr)


def land_dictionary_wave(store: Store) -> None:
    """The first content wave's entries wait in his Library as drafts, one collection per
    family, from the PC's first start on (A13). As the port, a store that refuses the put or a
    QMX that runs without its seed folders is named and the host starts anyway."""
    try:
        landed = land_wave(store)
    except (LibraryRefused, OSError, ValueError) as refused:
        print(f"library: the dictionary's first wave did not land: {refused}", file=sys.stderr)
        return
    for family in landed:
        print(
            f"library: the dictionary's first wave waits in the Library: {family}", file=sys.stderr
        )


def library_line(store: Store) -> DoctorLine:
    """The doctor's Library row: the store's health, its alarms and the line that stopped it."""
    state = store.state
    alarms = ", ".join(store.alarms) or "none"
    incident = f"; stopped at {state.incident}" if state.incident else ""
    return DoctorLine(
        "library",
        state.health == "open" and not store.alarms,
        f"store {store.name} ({store.role}) is {state.health}; alarms: {alarms}{incident}",
    )


def own_door(role: Role, port: int) -> str:
    """This host's door on the tailnet, the default `door_url` of every placement it dispatches
    to, or "" where Tailscale gives no address."""
    if role == "pc":
        return ""
    try:
        found = subprocess.run(
            ["tailscale", "ip", "-4"],  # noqa: S607 - the node's own CLI, as `qmx node` runs it
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except OSError, subprocess.TimeoutExpired:
        return ""
    address = next(iter(found.stdout.split()), "") if found.returncode == 0 else ""
    return f"http://{address}:{port}" if address else ""


def vault_secrets(vault: Path) -> Callable[[str, str], str | None]:
    """An app's declared secret `qmx/<name>`, read from `vault/<name>` by `read_key`. A missing
    file is None, so the supervisor refuses the start with `missing_secret`. A link, a hard link, a
    file another user owns and, on POSIX, a file its group or others can read are refused; start
    made the vault's Windows DACL owner-only (`vault_acl`). No refusal carries the file's
    content."""

    def read(service: str, _username: str) -> str | None:
        name = service.removeprefix("qmx/")
        if not APP_SECRET.fullmatch(service) or name.casefold() in HOST_VAULT:
            raise AppError("vault_refused", f"{service!r} is not a secret an app may declare.")
        try:
            found = read_key(vault / name)
            return None if found is None else found.decode("utf-8").strip()
        except KeyRefused as refused:
            raise AppError("vault_refused", f"The vault file for {service} {refused}.") from None
        except (OSError, UnicodeDecodeError) as error:
            raise AppError(
                "vault_refused",
                f"The vault file for {service} cannot be read ({type(error).__name__}).",
            ) from None

    return read


def control_for(role: Role, home: QmxHome) -> ControlService:
    """The host's control service. On role `server` an app's declared secrets come from the home's
    owner-only vault, because a headless server's keyring has no backend (AD-33 change 6). This
    PC and a node keep the OS keyring, Credential Manager on Windows."""
    if role == "server":
        return control_service(home, secret_getter=vault_secrets(home.root / "vault"))
    return control_service(home)


async def serve(
    home: Path,
    sock: socket.socket,
    role: Role,
    ui_origin: str,
    scrubbed: Sequence[str],
    keep: Sequence[str],
    library_root: Path | None = None,
    place: str = "",
    *,
    served: threading.Event,
) -> None:
    """Assumes the caller scrubbed the environment, holds the home's lock and bound `sock`, the
    port the app answers on. `place` is the `--place` name setup gives a server's host. `served`
    is set once uvicorn has served, so a refusal after that is not named a start that failed."""
    port: int = sock.getsockname()[1]
    # Before any key is written: the run pass key below, a pairing, a venue session's tokens.
    vault = owner_only(home / VAULT)
    qmx_home = QmxHome(home)
    control = control_for(role, qmx_home)
    name = placement_name(control, role, place)
    control.place = name
    serving = role == "server"
    # Computed once, so the REST gate, the door's restamp and the Library routes share one bearer.
    bearer = qmx_control.server.local_token(home, create=True)
    root = (library_root or home / LIBRARY) if serving else home / LIBRARY
    router = await RouterService(
        home, bind=TAILNET if role in ("node", "server") else LOOPBACK
    ).start()
    # Its own thread and loop, pinned in `<home>/router.port`; the harness's relay adopts it.
    # The `node` and `server` roles bind the tailnet instead of the loopback: those machines are
    # reached over Tailscale or not at all, and the relay is still the only caller on that port
    # (AD-12).
    supervising = asyncio.create_task(router.supervise())
    # One authority per process, from the home's secret: the door, the node sidecar and the
    # harness's helpers mint and verify with it, and so does every other machine of the home.
    passes = PassAuthority.for_home(home)
    sidecar = (
        asyncio.create_task(node_sidecar(home, passes)) if role in ("node", "server") else None
    )
    nodes = node_link(home, control, name)
    attach_node(control, nodes)
    try:
        door = market_door(home, control, role)
        control.app_runtime().attach_facts(lambda: host_facts(control, role, name, door))
        harness = await RecordedHarness.open(
            qmx_home,
            control=control,
            host_reads=host_reads(qmx_home, control, name),
            market=door if isinstance(door, MarketDoor) else None,
            accounts=lambda account: account_worlds(control, account),
        )
        harness.adopt_passes(passes)
        if vault == "repaired":
            harness.doctor_from(lambda: DoctorLine(VAULT, True, VAULT_FIXED))
        try:
            floor = floor_bytes(section(control, "engine"), free_bytes(home))
            with open_store(home, root, serving=serving, floor=floor) as store:
                recheck_test_runs(home, store)
                register_checkers(store)
                if not serving:
                    land_first_unit(store)
                if role == "pc":
                    store.lifecycle = lifecycle_writer(home, control, name)
                    land_ported_dictionary(store)
                    land_dictionary_wave(store)
                control.attach_library(store)
                runtime = control.app_runtime()
                registered = landers(
                    store,
                    runtime,
                    name,
                    settings=lambda: control.settings_get("qmb"),
                    door=door,
                )
                runtime.attach_landers(registered)
                close_stranded_runs(runtime.home, cast(QmbRun, registered[QMB_RUN]))
                threading.Thread(
                    target=enable_apps, args=(home, runtime), name="qmx-first-apps", daemon=True
                ).start()
                harness.doctor_from(lambda: library_line(store))
                backups = Backups(
                    Layout.from_home(home),
                    control,
                    clock=lambda: datetime.now().astimezone(),
                    floor=floor,
                    store=store,
                )
                records = records_job(home, control, role, door, store, nodes)
                node_settings = control.settings_get("node")
                venue_records = (
                    VenueRecords(
                        node_call(runtime),
                        store,
                        every_s=refresh_s(node_settings),
                        markets=record_markets(node_settings),
                    )
                    if role == "pc"
                    else None
                )
                # Before the engine opens: a restored folder's fires and held runs stay paused.
                backups.hold_after_restore(store)
                harness.doctor_from(backups.doctor_line)
                connect = storage_dialog(Layout.from_home(home), control, backups)
                harness.doctor_from(connect.doctor_line)
                harness.record_into(SessionRecorder(store))
                memory = await asyncio.to_thread(
                    compose_memory, harness, store, home, control, role
                )
                backups.reindex(lambda: memory.rebuild("all"), hindsight=memory.index is not None)
                adopt_router(RelayRouter(harness_relay(harness)))
                deep_logs(home, connect)
                try:
                    async with EngineDoor.open(
                        control,
                        harness=HarnessAdapter(harness),
                        library=EngineLibraryAdapter(store),
                        placements=nodes.placements(),
                    ) as engine:
                        core = engine.svc.ctx.engine
                        placed = (
                            remote_worker(home, core, passes, own_door(role, port), host_id=name)
                            if role in ("node", "server")
                            else None
                        )
                        if placed is not None:
                            core.worker = placed
                        core.worker.place = name
                        link = hub_link(home, control)
                        asking = Streams.of(forwarders_for(home, core, name, role))
                        engine.svc.watching(name=name, forwarders=asking.forwarders)
                        harness_api = chat_routes(harness, scrubbed=scrubbed, keep=keep)
                        origin = ui_origin if role == "pc" else ""
                        answering = [*answering_router(home, engine), drain_router(core)]
                        answering.append(
                            host_router(
                                Answering(
                                    nodes,
                                    pass_keys=lambda: held_keys(home),
                                    heartbeats=lambda: heartbeats_read(home, name)({}),
                                    store_root=lambda: (
                                        door.store_root if isinstance(door, MarketDoor) else None
                                    ),
                                    answers=Answers(home / ANSWERS),
                                    door=lambda: door if isinstance(door, MarketDoor) else None,
                                )
                            )
                        )
                        answering.append(templates_router(engine))
                        answering.append(backups_router(backups))
                        answering.append(maintenance_router(backups, triggers_of(control), records))
                        answering.append(publish_collection_router(control))
                        answering.extend(dialog_routers(connect, control))
                        answering.append(
                            market_router(door)
                            if isinstance(door, MarketDoor)
                            else closed_market_router(door)
                        )
                        if store.lifecycle is not None:
                            promoter = Promoter(
                                store,
                                store.lifecycle,
                                nodes,
                                LanderLibrary(store),
                                calibrations=harvested_calibrations(home, time.time_ns),
                                trading_profile=lambda place: (
                                    place == name
                                    and host_facts(control, role, name, door)["trading_profile"]
                                    is True
                                ),
                            )
                            answering.append(promote_router(promoter))
                        app = compose(
                            control,
                            engine,
                            harness_api,
                            bearer,
                            origin,
                            answering,
                            passes,
                            library_service(home, store, serving, bearer),
                        )
                        upgrade_moment_ended(Layout.from_home(home))
                        server = uvicorn.Server(uvicorn.Config(app))
                        clock_doctor(harness, home, name, core.settings)
                        shipper = AppLogs(home, lambda: section(control, "telemetry"))
                        harness.doctor_from(shipper.doctor_line)
                        beating = asyncio.create_task(
                            heartbeats(
                                home,
                                name,
                                control,
                                harness,
                                engine,
                                link,
                                heeding=lambda: backups.after is None,
                            )
                        )
                        exporting = asyncio.create_task(harness.idle_exports())
                        holding = asyncio.create_task(asking.hold_all())
                        linking = asyncio.create_task(nodes.keep())
                        refreshing = asyncio.create_task(keep_facts(control))
                        shipping = asyncio.create_task(shipper.run())
                        syncing: list[asyncio.Task[None]] = []
                        loop = asyncio.get_running_loop()

                        def sync() -> None:
                            replicator = Replicator.for_home(home, store, control)
                            if replicator is not None:
                                syncing.append(asyncio.create_task(replicator.run()))

                        backups.when_carried_on(lambda: loop.call_soon_threadsafe(sync))
                        copying = asyncio.create_task(backups.run())
                        harvesting = [] if records is None else [asyncio.create_task(records.run())]
                        if venue_records is not None:
                            harvesting.append(asyncio.create_task(venue_records.run()))
                        # Uvicorn logs no started line for a socket it was handed.
                        address, _ = sock.getsockname()
                        print(f"qmx_host serves on http://{address}:{port}", file=sys.stderr)
                        try:
                            await server.serve(sockets=[sock])
                        except SystemExit as exited:
                            if server.started or exited.code != STARTUP_FAILURE:
                                raise
                            raise AppDidNotStart from None
                        finally:
                            if server.started:
                                served.set()
                            for task in (
                                beating,
                                exporting,
                                holding,
                                linking,
                                refreshing,
                                shipping,
                                *syncing,
                                copying,
                                *harvesting,
                            ):
                                task.cancel()
                                with suppress(asyncio.CancelledError):
                                    await task
                            await asking.close()
                finally:
                    if connect.world.logs is not None and connect.world.logs.process is not None:
                        await asyncio.to_thread(connect.world.logs.process.close)
                    adopt_router(None)
                    install(None)
                    await asyncio.to_thread(memory.close)
        finally:
            await harness.close()
    finally:
        attach_node(control, None)
        supervising.cancel()
        with suppress(asyncio.CancelledError):
            await supervising
        if sidecar is not None:
            sidecar.cancel()
            with suppress(asyncio.CancelledError):
                await sidecar
        await router.close()


def capacity(engine: Engine, harness: Harness) -> dict[str, ClassUse]:
    """Slots in use, slots there are, and work waiting, per engine class and for chats."""
    found: dict[str, ClassUse] = {}
    for name, slots in engine.worker.capacity.slots.items():
        found[name] = ClassUse(used=slots.used, size=slots.size, waiting=len(slots.queue))
    table = harness.slot_table()
    found["chat"] = ClassUse(used=len(table.held), size=table.capacity, waiting=len(table.waiting))
    return found


def beat(
    home: Path,
    host_id: str,
    me: psutil.Process,
    engine: Engine,
    harness: Harness,
    pause: Pause | None = None,
    *,
    floor: int | None = None,
    clock: ClockFacts | None = None,
) -> Heartbeat:
    """This host's row: its own process and every child, the CLI trees included. `pause` is what
    this host heard from the Hub, so the row says whether its flag is still current (AD-65).

    The row carries this machine's live capacity: the room left on its volume and the floor it
    keeps, and the RAM it can give together with what one of its sessions really holds in memory.
    Admission reads the RAM figure, so no reserved constant stands in for it (D-11, F39). `floor`
    is the one measured when the host started; left out, it is measured here. `clock` is this
    machine's newest clock probe (AD-10).
    """
    tree = [me, *me.children(recursive=True)]
    cpu, rss = 0.0, 0
    for member in tree:
        with suppress(psutil.Error):
            times = member.cpu_times()
            cpu += times.user + times.system
            rss += member.memory_info().rss
    free_disk = free_bytes(home)
    kept = floor if floor is not None else floor_bytes(engine.settings, free_disk)
    free_ram = psutil.virtual_memory().available
    engine.worker.capacity.observe_free_ram(free_ram)
    engine.worker.capacity.observe_session(rss)
    kinds = node_kinds()
    return Heartbeat(
        subject="host",
        id=host_id,
        at=datetime.now(UTC).isoformat(),
        cpu_seconds=cpu,
        rss_bytes=rss,
        machine_minutes=(time.time() - me.create_time()) / 60,
        capacity=capacity(engine, harness),
        qmx_version=qmx_version(),
        node_kinds=kinds,
        kinds_digest=kinds_digest(kinds),
        paused=engine.paused,
        pause_state="known" if pause is None else pause.state(time.time()),
        free_disk_bytes=free_disk,
        disk_floor_bytes=kept,
        free_ram_bytes=free_ram,
        session_bytes=rss,
        clock=clock,
    )


def make_room(home: Path, engine: Engine, floor: int) -> None:
    """Below the floor, take this machine's expendable classes in the table's order and say which
    went. Nothing durable is in that table (F22, P-DISKFULL)."""
    free = free_bytes(home)
    if free >= floor:
        return
    taken = give_way(home, floor)
    print(
        f"disk below its floor: {free // MIB} MB free, {floor // MIB} MB kept; "
        f"gave way: {', '.join(taken) or 'nothing was expendable'}",
        file=sys.stderr,
    )


def storage_dialog(
    layout: Layout, control: ControlService, backups: Backups, keys: KeyStore | None = None
) -> Connect:
    """The connect dialog on this folder (design 06 section 9): its rclone from
    `[backup] rclone_path`, Credential Manager as its key store, the first sync of a storage
    it connected asked of `backups`, and this PC's OpenObserve, which the host runs."""
    store = CredentialManager() if keys is None else keys
    named = section(control, "backup").get("rclone_path")
    rclone = Rclone(layout, keys=store, path=named if isinstance(named, str) else "")

    def first_sync(place_id: str) -> str:
        try:
            started = backups.start(place_id, asked=True)
        except Refusal as refused:
            return f"the first sync did not start: {refused}"
        return f"the first sync started (job {started.job.id})"

    deep = OpenObserveProcess(layout, store, lambda: section(control, "telemetry"))
    world = World(layout, store, rclone, Jobs(), control, first_sync, logs=Logs(deep))
    return Connect(world, KINDS)


def deep_logs(home: Path, connect: Connect) -> None:
    """With `[telemetry] send_to = "this-pc"`, start this PC's OpenObserve on its own thread, so
    the host answers before it does. The host stops it with its other work."""
    found = connect.world.logs
    if target(home) != THIS_PC or found is None or found.process is None:
        return
    process = found.process

    def start() -> None:
        try:
            print(f"deep logs: {process.start()}", file=sys.stderr)
        except (Stopped, NeedsAdmin) as refused:
            print(f"deep logs: OpenObserve did not start: {refused}", file=sys.stderr)

    threading.Thread(target=start, name="openobserve", daemon=True).start()


def triggers_of(control: ControlService) -> Callable[[str], Sequence[Mapping[str, object]]]:
    """One installed workflow's triggers, as the maintenance list reads them."""

    def listed(workflow_id: str) -> Sequence[Mapping[str, object]]:
        return control.workflow_triggers_list(workflow_id)

    return listed


def dialog_routers(connect: Connect, control: ControlService) -> list[APIRouter]:
    """The connect routes and the write-only key routes, both behind the bearer."""

    def referred() -> list[str]:
        rows = placement(control).values()
        return [str(row["credential_ref"]) for row in rows if "credential_ref" in row]

    return [connect_router(connect), keys_router(connect.world.keys, referred)]


def app_rows(control: ControlService, paused: bool) -> list[Heartbeat]:
    """The supervisor's app rows, completed with the facts only the host knows."""
    version, digest = qmx_version(), kinds_digest(())
    return [
        Heartbeat.model_validate(
            {**row, "qmx_version": version, "kinds_digest": digest, "paused": paused}
        )
        for row in control.app_runtime().heartbeats()
    ]


async def heartbeats(
    home: Path,
    host_id: str,
    control: ControlService,
    harness: Harness,
    engine: EngineDoor,
    link: HubLink | None = None,
    *,
    heeding: Callable[[], bool] = lambda: True,
) -> None:
    """Write this host's rows every `heartbeat.interval` until cancelled. A failed beat is
    skipped, never fatal: the next one carries the same facts.

    When a Hub answers, the row goes there too and the reply's flag becomes this host's own, so
    one switch pauses every machine (AD-65). A Hub that stops answering leaves the last flag in
    force and the row reads `pause_state: unknown` once five minutes have passed. While
    `heeding()` is False (after a restore, until he carries on) the row still goes but the Hub's
    flag is not written, so a Hub cannot end the pause.

    Every `clock.probe_s` the host probes its clock first, and each row carries the newest facts.
    """
    core = engine.svc.ctx.engine
    me = psutil.Process()
    clock: ClockFacts | None = None
    probed: float | None = None
    log = HeartbeatLog(home, setting(core.settings, "heartbeat.window_days", WINDOW_DAYS))
    floor = floor_bytes(core.settings, free_bytes(home))
    pruned: int | None = None
    while True:
        try:
            pause = None if link is None else link.pause
            await asyncio.to_thread(make_room, home, core, floor)
            every = setting(core.settings, "clock.probe_s", PROBE_S)
            if probed is None or time.monotonic() - probed >= every:
                probed = time.monotonic()
                clock = await asyncio.to_thread(probe_from, core.settings)
            rows = [
                beat(home, host_id, me, core, harness, pause, floor=floor, clock=clock),
                # Off the loop: an install holds the supervisor's lock and hops onto this loop.
                *await asyncio.to_thread(app_rows, control, core.paused),
            ]
            await asyncio.to_thread(log.write, rows)
            if link is not None:
                await asyncio.to_thread(hear, link, rows[0], control, heed=heeding())
            hour = int(time.time() // 3600)
            if hour != pruned:
                await asyncio.to_thread(log.prune, datetime.now(UTC))
                pruned = hour
        except (OSError, ValueError, psutil.Error) as error:
            print(f"heartbeat skipped: {type(error).__name__}: {error}", file=sys.stderr)
        await asyncio.sleep(setting(core.settings, "heartbeat.interval", INTERVAL_S))


def clock_doctor(
    harness: Harness, home: Path, host_id: str, settings: Mapping[str, object]
) -> None:
    """The doctor's clock, `tzdata`, mismatch week and market calendars rows. The clock row reads
    this host's newest row, so opening the doctor never waits on a time source."""

    def today() -> date:
        return datetime.now(UTC).date()

    def clock() -> DoctorLine:
        row = host_row(home, host_id)
        return clock_line(None if row is None else row.clock)

    max_age = setting(settings, "clock.tzdata_max_age_days", TZDATA_MAX_AGE_DAYS)
    notice = setting(settings, "clock.dst_mismatch_notice_days", DST_NOTICE_DAYS)
    warn = setting(settings, "clock.calendar_warn_days", CALENDAR_WARN_DAYS)
    harness.doctor_from(clock)
    harness.doctor_from(lambda: tzdata_line(tzdata_version(), today(), max_age))
    harness.doctor_from(lambda: mismatch_line(today(), notice))
    harness.doctor_from(lambda: calendar_line(today(), warn))


def section(control: ControlService, name: str) -> Document:
    """One settings section by name. The schema's Literal predates `engine` and `library`."""
    return control.settings_get(cast("Any", name))


def hear(link: HubLink, row: Heartbeat, control: ControlService, *, heed: bool = True) -> None:
    """One push, and with `heed` the Hub's flag merged into `[engine] autonomy.paused` when it
    changes the value the engine reads; every other `[engine]` key stays."""
    reply = link.push(row)
    if not heed:
        return

    def heeded(engine: Document) -> Document:
        found = engine.get("autonomy")
        autonomy = dict(found) if isinstance(found, dict) else {}
        if bool(autonomy.get("paused")) == reply.autonomy_paused:
            return engine
        return {**engine, "autonomy": {**autonomy, "paused": reply.autonomy_paused}}

    control.settings_update(cast("Any", "engine"), heeded)


def placement_name(control: ControlService, role: Role, place: str = "") -> str:
    """This host's place name (AD-30, AD-72). This PC is always `pc`. A host started for a server
    takes `--place`, which setup passes, else `[engine] host_name`, and never guesses one; the
    name is a place name (`PLACE`) other than `pc`. A refusal is one line that echoes nothing he
    typed."""
    if role == "pc":
        if place not in ("", PC):
            raise PlaceRefused("refused: a host started as pc is This PC; --place names a server")
        return PC
    found = section(control, "engine").get("host_name")
    name = place or (found if isinstance(found, str) else "")
    if not name:
        raise PlaceRefused(
            f"refused: a host started as {role} needs its place name; pass --place <name>, the"
            " name he gave this machine in his place list, or set [engine] host_name."
        )
    if name == PC or not PLACE.fullmatch(name):
        raise PlaceRefused(
            "refused: a server's place name is lowercase letters, digits and dashes, up to 63,"
            " and is not pc."
        )
    return name


def hub_link(home: Path, control: ControlService) -> HubLink | None:
    """The Hub this home answers to, or None when no `[library] hub_url` names one."""
    url = section(control, "library").get("hub_url")
    if not isinstance(url, str) or not url:
        return None
    key = vault_key(home)
    return None if key is None else HubLink(url, key)


def vault_key(home: Path, name: str = PAIRING_KEY) -> str | None:
    """One of the host's own vault files, read by `read_key`, or None when it is missing. A link,
    a hard link, a file another user owns and, on POSIX, a file others can read raise
    `VaultRefused`, which names the file and never its content, so a start stops with that line."""
    try:
        found = read_key(home / VAULT / name)
    except KeyRefused as refused:
        raise VaultRefused(f"the vault file {name} {refused}") from None
    return None if found is None else found.decode("utf-8").strip()


def node_link(home: Path, control: ControlService, name: str) -> NodeLink:
    """This host's one node link (Part C AD-303), over its supervisor and its place rows."""

    def tuning() -> Mapping[str, object]:
        found = section(control, "engine").get("node_link")
        return cast("Mapping[str, object]", found) if isinstance(found, dict) else {}

    def blobs(fingerprint: str) -> Iterable[bytes] | None:
        store = control.library.store
        try:
            store.blob_size(fingerprint)
        except LibraryRefused:
            return None
        return store.blob_stream(fingerprint)

    return NodeLink(
        home,
        here=name,
        apps=control.app_runtime(),
        settings=ControlSettings(control).values,
        pass_keys=lambda: held_keys(home),
        tuning=tuning,
        blobs=blobs,
    )


def forwarders_for(home: Path, core: Engine, name: str, role: Role) -> list[Forwarder]:
    """The owned instances this home asks: every node on the PC, none on a node (AD-65), each
    with the pass key it was paired with; a node not paired yet is not asked."""
    keys: HostKeys = held_keys(home) if role == "pc" else {}
    return [
        Forwarder(instance, key=keys[instance.name], source=name, principal="operator", now=wall)
        for instance in owned_instances(placement_rows(core.settings), home=name)
        if instance.name in keys
    ]


def market_door(home: Path, control: ControlService, role: Role) -> MarketDoor | TypedRefusal:
    """This machine's market-data door, open with no holdout by default (AD-28, ruling 137).

    It is refused only for a store it cannot read or a `[data]` it cannot use, and the log line
    says which; the host then answers every data route with that refusal. The door reads `[data]`
    live, so a holdout turned on in Settings reaches the next read, and the door at `[library]
    primary` serves the final look.
    """
    root = home / MARKET
    built = MarketDoor.open(
        root,
        section(control, "data"),
        placement=Placement(role),
        primary=Placement.SERVER if library_primary(home) == "server" else Placement.PC,
        handles=root / "handles",
        settings=lambda: section(control, "data"),
    )
    if is_refusal(built):
        print(f"market-data: {shut_line(built)} {dict(built.context)}", file=sys.stderr)
        return built
    return built.value


def records_job(
    home: Path,
    control: ControlService,
    role: Role,
    door: MarketDoor | TypedRefusal,
    store: Store,
    nodes: NodeLink,
) -> Records | None:
    """The records job on this machine: the one harvester of every app's append streams, through
    this machine's own door (Part B AD-209). This PC also pulls each node's records home over the
    node link's places (AD-210), projects round trips into `trade` items and scores paper lanes,
    since its Library is where they land. A door that did not open leaves the job out; its
    refusal is already on stderr."""
    if not isinstance(door, MarketDoor):
        return None
    folder = home / "records"
    harvester = Harvester(lambda: append_roots(home), door, folder, journals_open=role == "pc")
    projection = (
        Projection(store, folder, rule=lambda: PaperRule.of(section(control, "judge")))
        if role == "pc"
        else None
    )
    return Records(
        harvester,
        lambda: Cadence.of(section(control, "records"), section(control, "journals")),
        clock=lambda: datetime.now(UTC),  # ambient-scan: allow (the host is the composition root)
        projection=projection,
        store=store,
        pull=Pull(door, folder, here=nodes.here, places=nodes.places, pass_keys=nodes.pass_keys)
        if role == "pc"
        else None,
    )


def host_facts(
    control: ControlService, role: Role, name: str, door: MarketDoor | TypedRefusal
) -> Document:
    """This host's facts as every app volume holds them (AD-307, Part C `CONTRACTS.md` section
    5), read live from Settings. This PC never reports the trading profile on, whatever `[host]
    trading_profile` says. This host mounts its chat routes and may place agent steps on every
    role today, so `chats` and `agent_steps` say so until the bind-live step turns them off."""
    trading = role != "pc" and section(control, "host").get("trading_profile") is True
    return {
        "schema_version": FACTS_SCHEMA,
        "placement": name,
        "role": role,
        "trading_profile": trading,
        "chats": True,
        "agent_steps": True,
        "holdout": holdout_fact(door),
    }


def holdout_fact(door: MarketDoor | TypedRefusal) -> Document:
    """The Settings `[data]` default seal exactly as the door applies it. A door or `[data]` that
    cannot be read reports the holdout on with no boundary, so a reader seals every month rather
    than none."""
    seal = door.default_seal() if isinstance(door, MarketDoor) else door
    if is_refusal(seal):
        return {"on": True}
    if seal.value is None:
        return {"on": False}
    instant = seal.value.seal_boundary.instant
    if instant is None:
        return {"on": True, "months": seal.value.holdout_months}
    start = datetime.fromtimestamp(instant.value_ns // 1_000_000_000, UTC)
    return {"on": True, "boundary": start.strftime("%Y-%m"), "months": seal.value.holdout_months}


def settings_tip(control: ControlService) -> int:
    """The newest Settings event's position, so a watcher starts after what already happened."""
    after = 0
    while page := control.events("settings", after=after, limit=1000):
        after = cast(int, page[-1]["id"])
    return after


QMB_RUN: Final = "qmb-run"
"""The one core lander today (Level 0 AD-34): a tester's provides name it to land its runs."""


class LanderLibrary:
    """The lander's Library port over the host's store: each record onto `main`, written once by
    the principal the lander names, and each edge kept once by the store."""

    def __init__(self, store: Store) -> None:
        self.store = store
        self._units: dict[str, tuple[Mapping[str, JsonObject], RunUnit | str]] = {}

    def find(self, item: str) -> str | None:
        head = self.store.head(item, MAIN)
        return None if head is None else head[0]

    def put(
        self,
        kind: str,
        fields: Mapping[str, object],
        blobs: Mapping[str, bytes],
        *,
        item: str | None,
        title: str,
        summary: str,
        principal: str,
    ) -> Stored:
        draft = Draft(
            kind, item, title, summary, fields=cast(JsonObject, dict(fields)), blobs=dict(blobs)
        )
        commit = self.store.put(Principal.parse(principal), draft, on=MAIN, expected_head=None)
        return Stored(commit.object_id)

    def link(self, from_id: str, relation: str, to_id: str, *, principal: str) -> str:
        return self.store.relate(Principal.parse(principal), from_id, relation, to_id)

    def holds(self, object_id: str) -> bool:
        return self.store.catalog.row(object_id) is not None

    def family_of(self, unit: str) -> str:
        """The root item of `unit`'s `variant-of` lineage (judge.md §2). Versions of an item
        share it, and an edge from any version of a variant leads to its parent's item. A pin
        the Library does not hold is its own root."""
        if not self.holds(unit):
            return unit
        found = self.store.get(OPERATOR_READ, unit)
        item, kind, seen = found.item, found.kind, {found.item}
        while True:
            placed = [object_id for object_id, _ in self.store.placed(item, kind, None)]
            up = self.store.walk(OPERATOR_READ, placed, (LINEAGE,), "out", depth=1)
            parent = None if not up else self.store.get(OPERATOR_READ, up[0].object_id)
            if parent is None or parent.item in seen:
                return item
            item, kind = parent.item, parent.kind
            seen.add(item)

    def unit(self, pin: str) -> RunUnit | str | None:
        """The unit document `pin` names, compiled with the blocks and records `gather` finds now;
        why it does not compile; or None when the pin names an object of another kind. An object
        never changes but the records it reads do, so a pin compiles again only when they moved.
        The documents are the key, because a fixture, a first item and an item replacing an
        archived one can all read as version 1."""
        view = self.store.get(OPERATOR_READ, pin)
        if view.kind != "unit":
            return None
        document = cast(dict[str, object], view.fields)
        gathered = gather(self.store, document)
        held = self._units.get(pin)
        if held is not None and held[0] == gathered.record_documents:
            return held[1]
        compiled = compile_unit(document, gathered.context)
        found: RunUnit | str
        if isinstance(compiled, CompiledUnit):
            found = RunUnit(
                document, gathered.context, compiled, gathered.record_documents, gathered.warnings
            )
        else:
            first = compiled[0].message if compiled else "the unit does not compile"
            found = f"the unit {pin} does not compile: {first}"
        self._units[pin] = (gathered.record_documents, found)
        return found

    def compiled_fingerprint(self, unit: str) -> str | None:
        found = self.unit(unit) if self.holds(unit) else None
        return found.compiled.compiled_fingerprint.value if isinstance(found, RunUnit) else None

    def markets_of(self, unit: str) -> Sequence[str]:
        found = self.unit(unit)
        return found.markets if isinstance(found, RunUnit) else ()

    def g_record(self, compiled_fp: str, markets: Collection[str]) -> GRecord | None:
        """The layer G verdict of `compiled_fp` over `markets`, read from each finished
        `test-report`'s own slice. A failure seen on any of them answers first. Otherwise the
        first pass that saw them all, and otherwise none, so a market no check saw is checked
        before it runs and refused a move. A check that failed or was killed gave no verdict."""
        asked, passed = set(markets), None
        for object_id in self.store.with_field(TEST_REPORT, "compiled_fingerprint", compiled_fp):
            fields = self.store.get(OPERATOR_READ, object_id).fields
            if fields.get("check") != G_CHECK or fields.get("status") != "finished":
                continue
            behaviour = cast(dict[str, dict[str, list[str]]], fields.get("behaviour") or {})
            saw = set(behaviour.get("slice", {}).get("market_ids", ()))
            safety = cast(dict[str, object], fields.get("safety") or {})
            if safety.get("verdict") != "pass" and saw & asked:
                return GRecord(object_id, False)
            if passed is None and safety.get("verdict") == "pass" and asked <= saw:
                passed = GRecord(object_id, True)
        return passed


OPERATOR_READ: Final = Principal.parse("operator")
LINEAGE: Final = "variant-of"
BAR_SIDES: Final = ("bid", "ask")
BARS_TEMPLATE: Final = "download-dukascopy"
DEFAULT_SOURCE: Final = "dukascopy"
STORE_SHAPES: Final = (("bar-m1", BAR_SIDES), ("ticks", ("-",)))
"""What a run reads from the market store, a month's bid and ask bars before its ticks, because a
month holds far fewer of them. The child reads either, so the reader stays when a derived step
writes `bar-m1` next to the ticks."""
_CARDS_LOCK: Final = threading.Lock()
"""One `dataset` card head at a time on this host, so two runs of a new series both land."""


COST_PROFILE: Final = "cost-profile"
"""The word `library_save` keeps for a stated cost profile. The Library has no such kind yet."""
HOST_RESTARTED: Final = "host restarted"


@dataclasses.dataclass(frozen=True, slots=True)
class StatedCosts:
    """A cost profile a run was told to pay: its pin, each market's `qmx.qmb.cost-profile/1`, and
    each market's funding rates as the tester's `timestamp,rate` CSV text."""

    pin: str
    profiles: Mapping[str, JsonObject]
    funding: Mapping[str, str]


@dataclasses.dataclass(frozen=True, slots=True)
class CsvPair:
    """One market's hand-saved bid and ask files for exactly the run's window."""

    bid: Path
    ask: Path


@dataclasses.dataclass(frozen=True, slots=True)
class RunWindow:
    """A run's window, its months, and the seal it reads them through. `run` names that seal only
    when a study states a holdout: a name fixes its first answer for good, so a name for no stated
    holdout would keep today's Settings default for this study and window after he changes it. A
    quick study's "off" is no statement, because he never wrote it, so his Settings seal holds."""

    start: str
    end: str
    months: tuple[str, ...]
    holdout: HoldoutAsk
    run: str | None


@dataclasses.dataclass(frozen=True, slots=True)
class StoreSide:
    """One series a market reads: its folder under `in/data/<market>/`, and the window's months
    oldest first. `card` is `MarketDoor.card` of the whole series, for its `dataset` item."""

    name: str
    series: str
    fingerprints: tuple[str, ...]
    card: Mapping[str, Any]


@dataclasses.dataclass(frozen=True, slots=True)
class StoreMonths:
    """One market's whole window in the market store, in one shape and at one stated scale."""

    kind: str
    scale: int
    sides: tuple[StoreSide, ...]
    window: RunWindow


@dataclasses.dataclass(frozen=True, slots=True)
class NotInStore:
    """Why a market's window cannot read the store: months no shape holds, series with no scale."""

    months: tuple[str, ...] = ()
    unscaled: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True, slots=True)
class RunUnit:
    """A unit pin as a run lays it out: its document, what its pins and markets read, and what
    it compiled to."""

    document: dict[str, object]
    context: CompileContext
    compiled: CompiledUnit
    record_documents: Mapping[str, JsonObject]
    fixture_records: tuple[str, ...]
    """`gather`'s warnings. Any other warning leaves a market with no record, and such a unit does
    not compile, so on a run these only name markets on a fixture."""

    @property
    def markets(self) -> tuple[str, ...]:
        return tuple(market.market_id for market, _ in self.compiled.plan.markets)


@dataclasses.dataclass(frozen=True, slots=True)
class QmbRun:
    """`qmb-run` as the apps supervisor's lander port: qmx-judge's lander, with the tester's
    leave read as its `qmx.qmb.result-bundle/1` and its files read from the run folder.

    For a unit document it lays the run out before the job starts (Part B AD-202 step 1), so
    the tester reads files only: `in/request.json` with the core's fields filled (among them
    `[qmb] gap_bars_refuse` and `calibrated_min_fills`, `allow_gaps` as a named study states it
    and otherwise as the request does, and `fixture_records` naming any market on a test fixture),
    the unit, its pinned blocks, the record documents `gather` read, and each market's data for
    the window. A market's data is the CSV pair `<symbol>-<stream>-<side>-<start>-<end>.csv` when
    `[qmb] bars` (default the market store's `bars/` folder) holds it, the test and hand-saved
    route. Otherwise it is the months in the market store, copied through the door to
    `in/data/<market>/` beside a `card.json`, and the result links their `dataset` items."""

    lander: RunLander
    library: LanderLibrary
    folder_of: Callable[[str, str], Path]
    """The run folder the supervisor makes for `(app_id, run_id)` inside the app's volume."""
    settings: Callable[[], Mapping[str, object]]
    market: Path
    door: MarketDoor | TypedRefusal

    def open(
        self, app_id: str, version: str, job: str, inputs: Document, principal: str
    ) -> Ticket | None:
        """Refuse a unit or study pin that names no Library object, a unit that does not
        compile, or a window with no data or a sealed month before any try lands: the result's
        `uses` and `tests` edges point at the pins, so such a run could never close. A copy that
        fails after the try opened fails that try, so no run stays open for good."""
        unknown = [
            f"{name} {pin} names no object in the Library"
            for name in ("unit", "study", "cost_profile")
            if isinstance(pin := inputs.get(name), str) and pin and not self.library.holds(pin)
        ]
        if unknown:
            raise BundleRefused(unknown)
        pin = inputs.get("unit")
        found = self.library.unit(pin) if isinstance(pin, str) and pin else None
        if isinstance(found, str):
            raise BundleRefused([found])
        bars = None if found is None else self._bars(found, inputs)
        costs = None if bars is None else self._stated_costs(inputs, bars)
        ticket = self.lander.open(app_id, version, job, inputs, principal)
        if ticket is not None and found is not None and bars is not None:
            laid = self.folder_of(app_id, ticket.run_id) / "in"
            try:
                self._lay_out(laid, ticket, found, bars, costs)
            except (OSError, ValueError, LibraryRefused) as error:
                self.lander.fail(ticket, str(error), status="failed")
                _lighten(laid)
                raise BundleRefused([str(error)]) from error
        return ticket

    def _stated_costs(self, inputs: Document, markets: Collection[str]) -> StatedCosts | None:
        """The cost profile a run is told to pay: the study's `cost_rule` when it names a Library
        object, as a study's `allow_gaps` beats a chat's, else the request's `cost_profile`. A
        `cost_rule` naming no object is words. The object is what `library_save` lands, and
        anything else is refused before any try, as is a profile that charges one of `markets`
        nothing. Only a `costs` entry counts: funding reaches a market only if its record pays
        funding, so funding alone can charge nothing while the result names the profile."""
        rule = self._study_fields(inputs).get("cost_rule")
        named = rule if isinstance(rule, str) and self.library.holds(rule) else None
        pin = named or inputs.get("cost_profile")
        if pin is None:
            return None
        if not isinstance(pin, str):
            raise BundleRefused(["cost_profile names one cost-profile in the Library, as text"])
        store = self.library.store
        view = store.get(OPERATOR_READ, pin)
        said = view.fields.get("legacy_kind", view.kind)
        blob = view.blobs.get("content")
        if said != COST_PROFILE or blob is None:
            raise BundleRefused([f"cost_profile {pin} is a {said}, not a {COST_PROFILE}"])
        body: object = json.loads(store.read_blob(blob.blob_id))
        held = cast(dict[str, Any], body).get("content", body) if isinstance(body, dict) else body
        stated = cast(dict[str, Any], held) if isinstance(held, dict) else {"costs": held}
        profiles, funding = stated.get("costs") or {}, stated.get("funding") or {}
        if not (_maps_to(profiles, dict) and _maps_to(funding, str)):
            raise BundleRefused(
                [
                    f"cost_profile {pin} needs costs by market, each an object, and funding by "
                    "market, each CSV text"
                ]
            )
        missing = [market for market in markets if market not in profiles]
        if missing:
            raise BundleRefused([f"cost_profile {pin} names no costs for {', '.join(missing)}"])
        return StatedCosts(pin, profiles, funding)

    def _study_fields(self, inputs: Document) -> Mapping[str, Any]:
        pin = inputs.get("study")
        if not isinstance(pin, str) or not pin:
            return {}
        return self.library.store.get(OPERATOR_READ, pin).fields

    def _bars(self, found: RunUnit, inputs: Document) -> dict[str, CsvPair | StoreMonths]:
        """Each market the request names and where its window's data sits, or a refusal that
        names every missing month and the template that downloads it (LD-06)."""
        window = self._run_window(inputs)
        self._refuse_sealed(window)
        study = self._study_fields(inputs)
        named = self.settings().get("bars")
        folder = Path(named) if isinstance(named, str) and named else self.market / "bars"
        stream = found.compiled.plan.stream
        sources = _sources(inputs.get("source"), study.get("source"))
        read: dict[str, CsvPair | StoreMonths] = {}
        lacking: dict[str, NotInStore] = {}
        files_missing: list[str] = []
        for market in _asked_markets(found.markets, inputs.get("markets")):
            record = found.context.records.get(market)
            symbol = record.symbol if record else market.rsplit(".", 1)[-1]
            bid, ask = (
                folder / f"{symbol.lower()}-{stream}-{s}-{window.start}-{window.end}.csv"
                for s in BAR_SIDES
            )
            if bid.is_file() and ask.is_file():
                read[market] = CsvPair(bid, ask)
                continue
            files_missing += [str(path) for path in (bid, ask) if not path.is_file()]
            in_store = self._from_store(market, symbol.upper(), sources, window)
            if isinstance(in_store, StoreMonths):
                read[market] = in_store
            else:
                lacking[market] = in_store
        if lacking:
            csv_named = files_missing if isinstance(named, str) and named else []
            raise BundleRefused(_lacking_words(lacking, sources, window, csv_named))
        return read

    def _run_window(self, inputs: Document) -> RunWindow:
        window = inputs.get("window")
        if not isinstance(window, dict) or not {"start", "end"} <= set(window):
            raise BundleRefused(["a unit run names its window, {start, end} as dates"])
        start, end = str(window["start"])[:10], str(window["end"])[:10]
        study = self._study_fields(inputs)
        holdout = None if study.get("origin") == "quick" else study.get("holdout")
        return RunWindow(
            start,
            end,
            _months_of(start, end),
            cast("HoldoutAsk", holdout),
            None if holdout is None else f"{inputs['study']}@{start}/{end}",
        )

    def _refuse_sealed(self, window: RunWindow) -> None:
        """A month the run's holdout seals never reaches a run folder, by either route, because
        `materialise` copies whatever it is given. With no door there is no seal to ask, unless
        a study states one."""
        if isinstance(self.door, TypedRefusal):
            if window.holdout is None:
                return
            raise BundleRefused([f"this study names a holdout: {shut_line(self.door)}"])
        sealed = self.door.sealed_months(window.months, holdout=window.holdout, run=window.run)
        if is_refusal(sealed):
            raise BundleRefused([_door_reason(sealed)])
        if sealed.value:
            raise BundleRefused([f"{SEAL_READ_REASON}: {', '.join(sealed.value)}"])

    def _from_store(
        self, market: str, symbol: str, sources: Sequence[str], window: RunWindow
    ) -> StoreMonths | NotInStore:
        """The one source whose store holds this market's whole window. Two is a refusal, because
        they can differ only when the request and the study name different sources."""
        if isinstance(self.door, TypedRefusal):
            raise BundleRefused([f"the market-data door did not open: {shut_line(self.door)}"])
        found = [self._held(self.door, source, symbol, window) for source in sources]
        usable = [one for one in found if isinstance(one, StoreMonths)]
        if len(usable) > 1:
            raise BundleRefused(
                [
                    f"{market} holds this window under both {' and '.join(sources)}; the request "
                    "and the study name different sources, so name one"
                ]
            )
        if usable:
            return usable[0]
        lacking = [one for one in found if isinstance(one, NotInStore)]
        return NotInStore(
            tuple(sorted({month for one in lacking for month in one.months})),
            tuple(sorted({series for one in lacking for series in one.unscaled})),
        )

    def _held(
        self, door: MarketDoor, source: str, symbol: str, window: RunWindow
    ) -> StoreMonths | NotInStore:
        """The first shape that holds the whole window on every side at one stated scale."""
        lacking = NotInStore()
        for kind, variants in STORE_SHAPES:
            sides: list[StoreSide] = []
            absent: list[str] = []
            for variant in variants:
                series = f"{source}/{symbol}/{kind}/{variant}"
                card = door.card(series)
                whole: dict[str, Any] = {} if is_refusal(card) else cast(dict[str, Any], card.value)
                months = {
                    str(p["month"]): str(p["fingerprint"]) for p in whole.get("partitions", [])
                }
                absent += [month for month in window.months if month not in months]
                name = kind if variant == "-" else variant
                in_order = tuple(months[m] for m in window.months if m in months)
                sides.append(StoreSide(name, series, in_order, whole))
            if absent:
                lacking = NotInStore(tuple(sorted(set(absent))), lacking.unscaled)
                continue
            scales = {door.price_scale(side.series) for side in sides}
            scale = scales.pop()
            if scale is None or scales:
                unscaled = [s.series for s in sides if door.price_scale(s.series) is None]
                lacking = NotInStore((), (*lacking.unscaled, *unscaled))
                continue
            return StoreMonths(kind, scale, tuple(sides), window)
        return lacking

    def _lay_out(
        self,
        root: Path,
        ticket: Ticket,
        found: RunUnit,
        bars: Mapping[str, CsvPair | StoreMonths],
        costs: StatedCosts | None = None,
    ) -> None:
        settings = self.settings()
        pin = ticket.study
        study = {} if pin is None else self.library.store.get(OPERATOR_READ, pin).fields
        request: dict[str, object] = {
            "schema_version": 1,
            "equity": settings.get("equity"),
            "execution_target": settings.get("execution_target"),
            "g_slice_margin": settings.get("g_slice_margin"),
            "g_slice_bars": settings.get("g_slice_bars"),
            "gap_bars_refuse": settings.get("gap_bars_refuse"),
            "calibrated_min_fills": settings.get("calibrated_min_fills"),
            "motion": "on",
            "allow_gaps": False,
            **ticket.request,
            **({"allow_gaps": study["allow_gaps"]} if "allow_gaps" in study else {}),
            "kind": run_kind(ticket.job),
            "run_id": ticket.run_id,
            "markets": list(bars),
            "fixture_records": list(found.fixture_records),
            **({} if costs is None else {"cost_profile": costs.pin}),
        }
        root.mkdir(parents=True, exist_ok=True)
        (root / "request.json").write_text(json.dumps(request, indent=2), "utf-8")
        (root / "unit.json").write_text(json.dumps(found.document, indent=2), "utf-8")
        for pin, source in found.context.sources.items():
            block = root / "blocks" / pin
            block.mkdir(parents=True, exist_ok=True)
            (block / "block.py").write_bytes(source)
            (block / "entry.json").write_bytes(found.context.entries[pin])
        (root / "records").mkdir(exist_ok=True)
        for market, document in found.record_documents.items():
            (root / "records" / f"{market}.json").write_text(
                json.dumps(document, indent=2), "utf-8"
            )
        for market, data in bars.items():
            if isinstance(data, StoreMonths):
                self._copy_months(root / "data" / market, market, data)
                continue
            (root / "bars" / market).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(data.bid, root / "bars" / market / "bid.csv")
            shutil.copyfile(data.ask, root / "bars" / market / "ask.csv")
        if costs is not None:
            self._lay_costs(root, costs, bars)

    def _lay_costs(
        self, root: Path, costs: StatedCosts, bars: Mapping[str, CsvPair | StoreMonths]
    ) -> None:
        """Each market's stated profile and funding where the tester reads them. A stated profile
        measured no fills whatever it says, so the run stays `costs_uncalibrated`."""
        (root / "costs").mkdir(exist_ok=True)
        for market in bars:
            (root / "costs" / f"{market}.json").write_text(
                json.dumps({**costs.profiles[market], "fills": 0}, indent=2), "utf-8"
            )
            if market in costs.funding:
                (root / "funding").mkdir(exist_ok=True)
                (root / "funding" / f"{market}.csv").write_text(costs.funding[market], "utf-8")

    def _copy_months(self, folder: Path, market: str, data: StoreMonths) -> None:
        """A market's months as verified copies, beside the card the tester reads them by."""
        door = cast(MarketDoor, self.door)
        files: dict[str, list[str]] = {}
        for side in data.sides:
            copied = door.materialise(
                side.fingerprints,
                into=folder / side.name,
                holdout=data.window.holdout,
                run=data.window.run,
            )
            if is_refusal(copied):
                raise BundleRefused([f"{market}: {_door_reason(copied)}"])
            files[side.name] = [path.relative_to(folder).as_posix() for path in copied.value]
        card = {
            "kind": data.kind,
            "scale": data.scale,
            "fidelity": "quotes",
            "series": [side.series for side in data.sides],
            "window": {"start": data.window.start, "end": data.window.end},
            "months": list(data.window.months),
            "files": files,
            "datasets": [self._land_card(side, data.scale) for side in data.sides],
        }
        (folder / "card.json").write_text(json.dumps(card, indent=2), "utf-8")

    def _land_card(self, side: StoreSide, scale: int) -> str:
        """The series' `dataset` item as the door states it now, unchanged when it already is."""
        source, subject, kind, variant = side.series.split("/")
        parts = tuple(
            Partition(
                int(str(part["month"])[:4]),
                int(str(part["month"])[5:]),
                str(part["fingerprint"]),
                int(part["rows"]),
                bool(part["frozen"]),
                tuple(str(gap) for gap in part["gaps"]),
            )
            for part in side.card["partitions"]
        )
        card = SeriesCard(
            source,
            subject,
            kind,
            "" if variant == "-" else variant,
            quality={"price_scale": scale},
        )
        with _CARDS_LOCK:
            return write_card(self.library.store, OPERATOR_READ, card, parts).object_id

    def close(self, landing: AppLanding) -> str:
        run, data = landing.run, landing.data
        if run is None or not isinstance(data, dict):
            raise BundleRefused(["the result is a qmx.qmb.result-bundle/1 object from a run"])
        ticket = cast(Ticket, run.ticket)
        bundle = _with_its_data(parse_bundle(data), run.folder / "in")
        try:
            landed = self.lander.close(Landing(ticket, bundle, run.folder))
        except LibraryRefused as refused:
            raise BundleRefused([str(refused)]) from refused
        _lighten(run.folder / "in")
        return landed

    def fail(self, ticket: AppTicket, reason: str, status: Ending) -> str:
        own = cast(Ticket, ticket)
        try:
            landed = self.lander.fail(own, reason, status=status)
        except LibraryRefused as refused:
            raise BundleRefused([str(refused)]) from refused
        _lighten(self.folder_of(own.app_id, own.run_id) / "in")
        return landed


def _lighten(laid: Path) -> None:
    """A landed run's copies of its bars go, last of all, because the lander reads them first. The
    market store and the result keep what they held. A file still open stays, and fails no run."""
    for copied in ("bars", "data"):
        shutil.rmtree(laid / copied, ignore_errors=True)


def fail_stranded_runs(home: Path, run: QmbRun) -> list[str]:
    """Close each run this machine left open, before any app starts. The thread that waited on it
    died with the last host, and a leftover request would run with nobody to close it. Answers the
    run ids it closed; a second start finds none."""
    store = run.library.store
    prefix = f"qmbr-{run.lander.machine}"
    closed: list[str] = []
    for object_id in store.with_field(TRY_KIND, "state", "opened"):
        view = store.get(OPERATOR_READ, object_id)
        fields = cast(dict[str, Any], view.fields)
        run_id = str(fields["run_id"])
        if run_id.rpartition("-")[0] != prefix or run.library.find(try_item(run_id, "failed")):
            continue
        app = str(fields["tester"]["app"])
        queue = Volume(home, app).root / JOB_QUEUE
        for request in queue.glob("*.request.json"):
            asked = json.loads(request.read_text("utf-8"))
            if asked.get("inputs", {}).get("run_id") == run_id:
                request.unlink(missing_ok=True)
        laid = run.folder_of(app, run_id) / "in" / "request.json"
        ticket = Ticket(
            run_id=RunId(run_id),
            app_id=app,
            version=str(fields["tester"]["version"]),
            job=view.title.split(" ")[0],
            principal=str(fields["principal"]),
            unit=str(fields["unit"]),
            study=fields.get("study"),
            family=str(fields["family"]),
            opened=object_id,
            request=json.loads(laid.read_text("utf-8")) if laid.is_file() else {},
        )
        run.fail(ticket, HOST_RESTARTED, "failed")
        closed.append(run_id)
    return closed


def _months_of(start: str, end: str) -> tuple[str, ...]:
    """Every `YYYY-MM` a half-open window of dates touches, oldest first."""
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as error:
        raise BundleRefused(["a unit run names its window, {start, end} as dates"]) from error
    if last <= first:
        raise BundleRefused([f"this window's end, {end}, comes after its start, {start}"])
    final = last - timedelta(days=1)
    return tuple(
        f"{at // 12:04d}-{at % 12 + 1:02d}"
        for at in range(first.year * 12 + first.month - 1, final.year * 12 + final.month)
    )


def _sources(asked: object, studied: object) -> list[str]:
    """The sources a run may read: those the request and the study name, else the default. No
    other is read, so an old import with no stated scale cannot block or change a result."""
    named = [source for source in (asked, studied) if source is not None]
    if not all(isinstance(source, str) and source for source in named):
        raise BundleRefused(["source names one source in the market store, as text"])
    return list(dict.fromkeys(cast(list[str], named))) or [DEFAULT_SOURCE]


def _maps_to(value: object, kind: type) -> bool:
    return isinstance(value, dict) and all(
        isinstance(entry, kind) for entry in cast(dict[str, object], value).values()
    )


def _asked_markets(traded: Sequence[str], asked: object) -> tuple[str, ...]:
    """The markets a run names, in the unit's order, or every one when it names none."""
    if asked is None:
        return tuple(traded)
    named = cast(list[str], asked)
    stray = [market for market in named if market not in traded]
    if stray or not named:
        raise BundleRefused(
            [
                f"this unit does not trade {', '.join(stray) or 'an empty list'}; it trades "
                f"{', '.join(traded)}"
            ]
        )
    return tuple(market for market in traded if market in named)


def _lacking_words(
    lacking: Mapping[str, NotInStore],
    sources: Sequence[str],
    window: RunWindow,
    csv_missing: Sequence[str],
) -> list[str]:
    """Every reason a run has no data, the months first, since the first one is the message."""
    months = ", ".join(f"{market} {m}" for market, why in lacking.items() for m in why.months)
    unscaled = sorted({series for why in lacking.values() for series in why.unscaled})
    words: list[str] = []
    if months:
        also = f"; {csv_missing[0]} is missing too" if csv_missing else ""
        words.append(
            f"no data for {window.start} to {window.end}: {months} not in the market store under "
            f"{' or '.join(sources)}; run the {BARS_TEMPLATE} template for each month{also}"
        )
    words += [
        f"{series} states no price scale; run the {BARS_TEMPLATE} template's check on its card, "
        "or download the month again"
        for series in unscaled
    ]
    return words


def _door_reason(refusal: TypedRefusal) -> str:
    return str(refusal.context.get("reason", refusal.category.value))


def _with_its_data(bundle: ResultBundle, laid: Path) -> ResultBundle:
    """A store run's leave, with what only the core knows: the `dataset` items it read, their
    series in its labels, and the hash of its request. A hand-saved CSV run has no such card."""
    cards = [
        cast("dict[str, list[str]]", json.loads(path.read_text("utf-8")))
        for path in sorted(laid.glob("data/*/card.json"))
    ]
    if not cards:
        return bundle
    series = [name for card in cards for name in card["series"]]
    return dataclasses.replace(
        bundle,
        consumed=tuple(dataset for card in cards for dataset in card["datasets"]),
        request_fp=fingerprint_bytes((laid / "request.json").read_bytes()).value,
        labels={**(bundle.labels or {}), "datasets": series},
    )


def landers(
    store: Store,
    runtime: Supervisor,
    machine: str,
    *,
    settings: Callable[[], Mapping[str, object]] = lambda: QMB_DEFAULTS,
    door: MarketDoor | TypedRefusal | None = None,
) -> dict[str, Lander]:
    """The core landers this host registers: `qmb-run`, writing as the operator, the one
    principal who puts records on `main`, and minting run ids named for this machine. It runs a
    unit's behaviour check first through the supervisor's own `run_job`. `settings` reads the
    `[qmb]` section at each run. `door` is the host's market-data door, or a refusal when it did
    not open; left out, a door with no holdout on the same store."""

    def provides_of(app_id: str, version: str) -> set[str]:
        for row in runtime.versions(app_id):
            if row["version"] == version:
                image = runtime.home / "definitions" / str(row["definition_hash"])
                return set(Definition.load(image).manifest.provides)
        return set()

    def run_job(
        app_id: str, job: str, inputs: Mapping[str, object], principal: str
    ) -> Mapping[str, object]:
        return runtime.run_job(
            app_id, job, inputs=cast(Document, dict(inputs)), principal=principal
        )

    def folder_of(app_id: str, run_id: str) -> Path:
        data = runtime.status(app_id).get("data")
        return Volume(runtime.home, app_id).root / str(data or "data") / RUNS / run_id

    library = LanderLibrary(store)
    lander = RunLander(
        library,
        writer="operator",
        machine=machine,
        provides_of=provides_of,
        clock=lambda: datetime.now(UTC),
        check_first=CheckFirst(run_job, library),
        family_of=library.family_of,
    )
    market = runtime.home / MARKET_STORE
    if door is None:
        opened = MarketDoor.open(market, {})
        door = opened if is_refusal(opened) else opened.value
    return {QMB_RUN: QmbRun(lander, library, folder_of, settings, market, door)}


async def keep_facts(control: ControlService) -> None:
    """Rewrite the host facts in every running app's volume after each Settings write, so a
    holdout he turns on reaches each app's copy while it runs. Copies already equal stay as
    they are."""
    runtime = control.app_runtime()
    async for _ in control.stream("settings", after=settings_tip(control)):
        try:
            await asyncio.to_thread(runtime.refresh_facts)
        except OSError as error:
            print(f"host facts not rewritten until the next change: {error}", file=sys.stderr)


def shut_line(refusal: TypedRefusal) -> str:
    """What a shut price door says, in plain words: what is wrong and what to do."""
    reason = refusal.context.get("reason") or refusal.category
    field = refusal.context.get("field")
    if field is None:
        return f"QMX's market data did not open: {reason}. Fix that and restart QMX."
    return (
        f"QMX's market data did not open because [data] {field} in Settings cannot be used: "
        f"{reason}. Fix it in Settings and restart QMX."
    )


def closed_market_router(refusal: TypedRefusal) -> APIRouter:
    """Every `/api/data/*` route of a door that did not open: 503 with the door's own refusal
    shape and its line, so the UI reads one shape for the whole route family."""
    router = APIRouter()
    detail = {
        "refused": str(refusal.category),
        "retryability": str(refusal.retryability),
        "context": dict(refusal.context),
        "line": shut_line(refusal),
    }

    @router.api_route("/api/data/{rest:path}", methods=["GET", "POST"])
    def shut() -> None:
        raise HTTPException(503, detail)

    _ = shut
    return router


def answering_router(home: Path, engine: EngineDoor) -> list[APIRouter]:
    """The node's forwarding route and the cTrader sign-in routes, which answer only a pass
    signed with the pass key this host shares with its sender (AD-67, C-28)."""
    from qmx_host.venue_session import for_host  # noqa: PLC0415 - kept beside the mount (WU8)

    return [forward_router(engine.svc.remote(), lambda: held_keys(home)), for_host(home, engine)]


def drain_router(core: Engine) -> APIRouter:
    """`POST /api/node/drain`: stop claiming fires, then say whether attempts are still running.

    `qmx node update` polls this and restarts nothing until `drained` is true, so a restart never
    cuts a node's attempt (AD-65). Nothing starts claiming again until the host restarts.
    """
    router = APIRouter()

    @router.post("/api/node/drain")
    def drain() -> dict[str, JsonValue]:
        core.claiming = False
        running = sorted(core.worker.running)
        return {"draining": True, "in_flight": len(running), "drained": not running}

    _ = drain
    return router


def account_worlds(control: ControlService, account_id: str) -> list[str]:
    """The `world` of each live `account` record on the Library's main whose `account_id` is
    the id. The harness's demo-only check of a broker MCP server reads it at every launch
    (C-36). An archived record names nothing, as for a promote."""
    store = control.library.store
    found = store.with_field("account", "account_id", account_id)
    worlds: list[str] = []
    for item in sorted({store.get(OPERATOR_READ, object_id).item for object_id in found}):
        head, state = store.head(item, MAIN), store.head(item, state_ref(item))
        if head is None or (state is not None and state[0] == "archived"):
            continue
        fields = store.get(OPERATOR_READ, head[0]).fields
        if fields.get("account_id") == account_id:
            worlds.append(str(fields.get("world")))
    return worlds


def host_reads(home: QmxHome, control: ControlService, host_id: str) -> dict[str, HostRead]:
    """The reads this host serves to a chat's `agent_tool` rows, by target."""
    return {
        "heartbeats": heartbeats_read(home.root, host_id),
        "provider_rows": provider_rows_read(home.root),
        "provider_test": provider_test_read(home),
        "mark": mark_read(control),
    }


def provider_rows_read(home: Path) -> HostRead:
    """The `ops_providers` read: every provider profile and model row, bundled and the home's
    own, read fresh each call so a profile edited in Settings shows at once."""

    async def read(_arguments: dict[str, Any]) -> Mapping[str, object]:
        def load() -> Mapping[str, object]:
            return model_registry.describe(model_registry.load(home / "profiles"))

        return await asyncio.to_thread(load)

    return read


def provider_test_read(home: QmxHome) -> HostRead:
    """The `ops_provider_test` read: one row's one-token Test, the plan row through the plan
    login. A key value never leaves the keyring lookup."""

    async def read(arguments: dict[str, Any]) -> Mapping[str, object]:
        qmx_id = arguments.get("qmx_id")
        if not isinstance(qmx_id, str):
            raise ValueError("qmx_id is a model row's id, for example openrouter/z-ai/glm-5.3")
        found = await asyncio.to_thread(model_registry.load, home.root / "profiles")
        result = await model_registry.one_token_test(
            found, qmx_id, plan_turn=model_registry.plan_test(home.plan_dir, home.root)
        )
        return dataclasses.asdict(result)

    return read


OPERATOR: Final = Principal.parse("operator")


def mark_read(control: ControlService) -> HostRead:
    """The `library_mark` read: the row is MANAGE, so it runs only after his approval, and the
    mark is written as the operator, the one principal who marks (Library AD-22)."""

    async def read(arguments: dict[str, Any]) -> Mapping[str, object]:
        item, quarantined = arguments.get("item"), arguments.get("quarantined")
        reason = arguments.get("reason")
        if not isinstance(item, str) or not isinstance(quarantined, bool):
            raise ValueError("item is a string and quarantined is true or false")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason says why, in a sentence")
        store = control.library.store
        try:
            await asyncio.to_thread(store.mark, OPERATOR, item, quarantined, reason)
        except LibraryRefused as refused:
            if refused.code == "not_found":
                raise KeyError(item) from None
            raise ValueError(str(refused)) from None
        return {"item": item, "quarantined": quarantined, "reason": reason}

    return read


def heartbeats_read(home: Path, host_id: str) -> HostRead:
    """The `ops_heartbeats` read: the newest row per subject, the host's last rows, and the clock
    of `host_id`, this machine."""

    async def read(_arguments: dict[str, Any]) -> Mapping[str, object]:
        def load() -> Mapping[str, object]:
            newest = latest(home)
            since = datetime.now(UTC) - timedelta(hours=1)
            found = HeartbeatLog(home, 1).rows(since)
            hosts = [row for row in found if row.subject == "host"][-HOST_HISTORY:]
            own = newest.get(f"host:{host_id}")
            clock = None if own is None else own.clock
            return {
                "latest": {key: row.model_dump(mode="json") for key, row in newest.items()},
                "host_history": [row.model_dump(mode="json") for row in hosts],
                "clock": None if clock is None else clock.model_dump(mode="json"),
            }

        return await asyncio.to_thread(load)

    return read


def compose(
    control: ControlService,
    engine: EngineDoor,
    harness_api: Sequence[APIRouter],
    bearer: str,
    ui_origin: str,
    extra: Sequence[APIRouter] = (),
    passes: PassAuthority | None = None,
    library: tuple[str, Sequence[APIRouter]] = ("", ()),
) -> FastAPI:
    """The one REST app: control, chat and engine routes behind one bearer and the principal
    door. `ui_origin` is the one origin CORS allows, none when empty. `extra` carries the node's
    forwarding route, which has its own host pass and no bearer (AD-65). `passes` is the authority
    whose run passes the door admits on the one data read (AD-70). `library` is the pairing key
    and the in-process Hub's routes, which the door admits that key on."""
    key, library_api = library
    app = qmx_control.server.create_app(
        control,
        bearer,
        ui_origin,
        extra_routers=[
            *harness_api,
            engine_router(engine),
            webhook_door(engine),
            *extra,
            *library_api,
        ],
    )
    routes = [route for api in harness_api for route in api.routes]
    app.add_middleware(
        PrincipalDoor,
        bearer=bearer,
        chat_routes=routes,
        passes=passes,
        library_key=key,
        library_routes=[route for api in library_api for route in api.routes],
    )
    return app


def webhook_door(engine: EngineDoor) -> APIRouter:
    """`POST /api/hooks/<trigger_id>`: one webhook delivery, fired once per delivery id (AD-10).
    The id is the first of `DELIVERY_HEADERS` the sender set; a delivery without one is refused,
    since nothing else could dedupe it. The body is the run's `webhook.body` input."""
    router = APIRouter()

    @router.post("/api/hooks/{trigger_id}")
    async def deliver(trigger_id: str, request: Request) -> Document:
        delivery_id = next(
            (found for name in DELIVERY_HEADERS if (found := request.headers.get(name))), None
        )
        if delivery_id is None:
            raise HTTPException(400, f"a webhook needs one of {', '.join(DELIVERY_HEADERS)}")
        raw = await request.body()
        try:
            body: JsonValue = json.loads(raw) if raw else None
        except ValueError:
            body = raw.decode("utf-8", "replace")
        payload: JsonObject = body if isinstance(body, dict) else {"value": body}
        return await asyncio.to_thread(
            engine.workflow_triggers_deliver, trigger_id, delivery_id, payload
        )

    _ = deliver
    return router


def health(port: int, home: Path) -> int | None:
    """The pid the host of `home` on `port` reports, or None, also while a starting host has not
    yet written the token file a machine without a keyring reads."""
    try:
        bearer = qmx_control.server.local_token(home)
        response = httpx.get(
            f"http://127.0.0.1:{port}/api/health",
            headers={"Authorization": f"Bearer {bearer}"},
            timeout=2,
        )
    except httpx.HTTPError, RuntimeError:
        return None
    pid = response.json().get("pid") if response.status_code == 200 else None
    return pid if isinstance(pid, int) else None


def start(
    home: Path,
    port: int,
    role: Role,
    ui_origin: str,
    library_root: Path | None = None,
    place: str = "",
) -> int:
    """`serve` in a background process, once it answers `/api/health`. The child is given the
    QMX folder, which it resolves again, and writes to the folder's `logs/host.log`. A child that
    exits first has its last line repeated and its exit code returned, the codes `serve` uses."""
    layout = Layout.from_home(home)
    running = recorded_host(home)
    if running is not None:
        print(HostRunning(home, running), file=sys.stderr)
        return 1
    try:
        with bound(LOOPBACK, port):
            pass
    except PortTaken as taken:
        print(f"QMX did not start: {taken}", file=sys.stderr)
        return PORT_TAKEN
    command = [sys.executable, "-m", "qmx_host", "serve", "--home", str(layout.root)]
    command += ["--port", str(port)]
    command += ["--role", role, "--ui-origin", ui_origin]
    if library_root is not None:
        command += ["--library-root", str(library_root)]
    if place:
        command += ["--place", place]
    host_log = layout.logs / "host.log"
    host_log.parent.mkdir(parents=True, exist_ok=True)
    with host_log.open("ab") as log:
        written = log.tell()
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    deadline = time.monotonic() + START_S
    while time.monotonic() < deadline:
        if (code := process.poll()) is not None:
            with host_log.open("rb") as log:
                log.seek(written)
                said = log.read().decode("utf-8", "replace").splitlines()
            last = next((line for line in reversed(said) if line.strip()), None)
            if last is not None:
                print(last, file=sys.stderr)
            print(f"The host failed to start; see {host_log}.", file=sys.stderr)
            return code or 1
        pid = health(port, home)
        if pid is not None and pid == recorded_host(home):
            print(f"Started qmx_host as PID {pid} on port {port}.")
            return 0
        time.sleep(0.1)
    terminate(process.pid)
    print(f"The host did not become ready; see {host_log}.", file=sys.stderr)
    return 1


def status(home: Path) -> int:
    pid = recorded_host(home)
    if pid is None:
        print("qmx_host is stopped.")
        return 0
    port = json.loads((home / STATE).read_text(encoding="utf-8"))["port"]
    if health(port, home) != pid:
        print(f"Recorded PID {pid} does not answer on port {port}.", file=sys.stderr)
        return 1
    print(f"qmx_host is running as PID {pid} on port {port}.")
    return 0


def stop(home: Path) -> int:
    pid = recorded_host(home)
    if pid is None:
        (home / STATE).unlink(missing_ok=True)
        print("qmx_host is stopped.")
        return 0
    terminate(pid)
    (home / STATE).unlink(missing_ok=True)
    print(f"Stopped qmx_host PID {pid}.")
    return 0


def terminate(pid: int) -> None:
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    tree = [*reversed(process.children(recursive=True)), process]
    for member in tree:
        with suppress(psutil.NoSuchProcess):
            member.terminate()
    _, alive = psutil.wait_procs(tree, timeout=10)
    for member in alive:
        with suppress(psutil.NoSuchProcess):
            member.kill()


class HubBlobs:
    """The PC replica's `upstream`: a blob it does not hold comes from the Library server and is
    kept as a cache copy it may give up at any time (AD-10). A Hub that cannot answer returns
    None, so the read refuses `blob_unavailable` instead of pretending."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def fetch(self, blob_id: str) -> bytes | None:
        if self.client is None:
            return None
        try:
            return self.client.blob(blob_id)
        except OSError, ValueError, LibraryRefused:
            return None


def library_client(home: Path) -> Any:
    """The Hub client this home writes and syncs through, or None while the PC is primary.

    `[library] primary = server` is the flip's cached word (AD-19); the record on `refs/primary`
    is the truth, and a store that learns a higher epoch stops acting as primary (AD-14).
    """
    try:
        from qmx_library.client import HubClient, primary  # noqa: PLC0415 (only a PC uses it)
    except ImportError:  # pragma: no cover (the package ships with the host)
        return None
    if primary(home) != "server":
        return None
    try:
        return HubClient.connect(home)
    except LibraryRefused as refused:
        print(f"library: no Library server to sync with: {refused}", file=sys.stderr)
        return None


class HomeHub(Hub):
    """The server host's Hub. Its store is the writer either way, so which refs a mirror may
    move follows the primary (the flip's record, else the home's setting), not the store's role:
    while the PC is primary the PC's `main` arrives here by sync."""

    def __init__(self, store: Store, *, home: Path) -> None:
        super().__init__(store, home=home)
        self.primary_home = home

    def refuse_owned(self, ref: str) -> None:
        primary = "server" if primary_of(self.primary_home, self.store) == "server" else "pc"
        if OwnerTable(primary).owner(ref) == "server":
            raise LibraryRefused("ref_not_owned", f"the server owns {ref}; a mirror never moves it")

    def health(self) -> dict[str, Any]:
        return super().health() | {"primary": primary_of(self.primary_home, self.store)}


def library_service(
    home: Path, store: Store, serving: bool, bearer: str
) -> tuple[str, Sequence[APIRouter]]:
    """The Library service inside the server's one host (AD-19, AD-26): one store, one writer.

    Returns the pairing key and the Hub's routes. The routes check the local `bearer`, because the
    host's bearer gate sits in front of them; the door turns a call carrying the pairing key into
    one carrying `bearer` (`PrincipalDoor`)."""
    if not serving:
        return "", ()
    key = vault_key(home)
    if key is None:
        print("library: no pairing key, so the Library routes are not mounted", file=sys.stderr)
        return "", ()
    return key, [in_process(HomeHub(store, home=home), bearer)]


class HubTarget:
    """The primary as the outbox sees it: its ref log, its head, its put, its kinds (AD-14)."""

    def __init__(self, hub: Any) -> None:
        self.hub = hub

    def ever_placed(self, object_id: str, item: str, ref: str) -> bool:
        return bool(self.hub.call("ever_placed", object_id=object_id, item=item, ref=ref))

    def head(self, item: str, ref: str) -> str | None:
        found = self.hub.call("head", item=item, ref=ref)
        return None if found is None else str(found)

    def put(self, draft: Any, *, on: str, expected_head: str | None) -> Any:
        return self.hub.put(draft, on=on, expected_head=expected_head)

    def can_read(self, kind: str, version: int) -> bool:
        found = self.hub.versions().get(kind)
        return found is not None and int(found) >= version

    def park(self, entry: Any) -> str:
        return str(
            self.hub.call(
                "park",
                item=entry.item,
                ref=entry.ref,
                expected_head=entry.expected_head,
                intended=entry.object_id,
            )
        )


class Replicator:
    """The PC's sync loop and outbox (AD-10, AD-14, AD-26).

    One sync runs at a time and a burst of commits coalesces into the next one. Each tick asks the
    Library server for the ref moves after the sequence it last read, copies their text slots and
    no other blob, then replays the saves the primary has not taken yet.
    """

    def __init__(self, store: Store, hub: Any, outbox: Any, table: Any, interval: float) -> None:
        self.store = store
        self.hub = hub
        self.outbox = outbox
        self.table = table
        self.interval = interval
        self.cursor = 0
        self.target = HubTarget(hub)
        from qmx_hub.replicate import Synchroniser  # noqa: PLC0415 (the PC's sync)

        self.synchroniser: Any = Synchroniser(self.sync_once)

    @classmethod
    def for_home(cls, home: Path, store: Store, control: ControlService) -> Replicator | None:
        hub = library_client(home)
        if hub is None:
            return None
        from qmx_library.client import owners  # noqa: PLC0415
        from qmx_library.outbox import OUTBOX, Outbox  # noqa: PLC0415

        interval = float(setting(section(control, "library"), "sync_interval", SYNC_INTERVAL_S))
        return cls(store, hub, Outbox(home / LIBRARY / OUTBOX), owners(home), interval)

    def sync_once(self) -> Any:
        from qmx_hub.replicate import StorePeer, sync_since  # noqa: PLC0415

        done = sync_since(StorePeer(self.store), self.hub, self.table, cursor=self.cursor)
        self.cursor = done.cursor
        return done

    def tick(self) -> tuple[Any, Any]:
        from qmx_library.outbox import replay  # noqa: PLC0415

        synced = self.synchroniser.request()
        if synced is None:
            return None, None
        return synced, replay(self.outbox, self.target)

    async def run(self) -> None:
        while True:
            try:
                await asyncio.to_thread(self.tick)
            except (OSError, ValueError, LibraryRefused) as error:
                print(f"library sync skipped: {type(error).__name__}: {error}", file=sys.stderr)
            await asyncio.sleep(self.interval)
