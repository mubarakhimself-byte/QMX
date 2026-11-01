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
hour, and serves the log to the copilot's `ops_heartbeats` row through the harness.

The lock is an OS lock on `<home>/engine.lock` (AD-3, L-64, L-70): the OS releases it when the
process dies, so a crashed host never blocks the next one, and two hosts cannot both take it.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import os
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Generator, Mapping, Sequence
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
from qmf.core import TypedRefusal, is_refusal
from qmx_apps.artifacts import Ending, Lander
from qmx_apps.artifacts import Landing as AppLanding
from qmx_apps.artifacts import Ticket as AppTicket
from qmx_apps.manifest import Definition
from qmx_apps.supervisor import Supervisor
from qmx_broker.credentials import CredentialManager, KeyStore
from qmx_control.models import Document
from qmx_control.node import PLACE, library_primary
from qmx_control.primary import CARD_REF, HOLD, Flip
from qmx_control.service import ControlService
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
from qmx_engine.runner import Engine
from qmx_engine.service.forward import (
    Forwarder,
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
from qmx_judge.landing import Lander as RunLander
from qmx_judge.landing import Stored
from qmx_judge.runs import BundleRefused, Landing, Ticket, parse_bundle
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.client import OwnerTable
from qmx_library.landing import NOT_PRIMARY
from qmx_library.port import Draft, LibraryRefused, StoreRole
from qmx_library.principal import MAIN, Act, Principal
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
from uvicorn.config import STARTUP_FAILURE

from qmx_host.backups import Backups, Refusal, backups_router
from qmx_host.bring_in import recheck_at_start
from qmx_host.clock_probe import (
    DST_NOTICE_DAYS,
    PROBE_S,
    TZDATA_MAX_AGE_DAYS,
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
from qmx_host.jobs import Jobs, Stopped
from qmx_host.keys import keys_router
from qmx_host.maintenance import maintenance_router
from qmx_host.market_data import MarketDoor, Placement, market_router
from qmx_host.process_record import STATE, recorded_host
from qmx_host.sessions import RecordedHarness, SessionRecorder, write_snapshot
from qmx_host.streams import Streams

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
PAIRING_KEY: Final = "vault/pairing-key"
DELIVERY_HEADERS: Final = ("X-QMX-Delivery", "X-GitHub-Delivery", "Idempotency-Key", "X-Request-Id")
DID_NOT_OPEN: Final = 2
"""`serve`'s exit when a store, the engine or the Library refused to open (loose strings Appendix
E); `__main__` exits 2 for a folder it refuses before the host starts."""
PORT_TAKEN: Final = 4
OPEN_REFUSALS: Final = (StoreRefused, LibraryRefused, EngineLibraryRefused)
"""What a store, the engine's ledger or either Library side raises when it must not open. Two
classes share the name `LibraryRefused`, one per side of the engine's Library port."""


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
    except (*OPEN_REFUSALS, AppDidNotStart) as refused:
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
    qmx_home = QmxHome(home)
    control = control_service(qmx_home)
    name = placement_name(control, role, place)
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
    try:
        door = market_door(home, control, role)
        control.app_runtime().attach_facts(lambda: host_facts(control, role, name, door))
        harness = await RecordedHarness.open(
            qmx_home,
            control=control,
            host_reads=host_reads(qmx_home, control, name),
            market=door if isinstance(door, MarketDoor) else None,
        )
        harness.adopt_passes(passes)
        try:
            floor = floor_bytes(section(control, "engine"), free_bytes(home))
            with open_store(home, root, serving=serving, floor=floor) as store:
                recheck_test_runs(home, store)
                control.attach_library(store)
                runtime = control.app_runtime()
                runtime.attach_landers(landers(store, runtime, name))
                harness.doctor_from(lambda: library_line(store))
                backups = Backups(
                    Layout.from_home(home),
                    control,
                    clock=lambda: datetime.now().astimezone(),
                    floor=floor,
                    store=store,
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
                        answering.append(templates_router(engine))
                        answering.append(backups_router(backups))
                        answering.append(maintenance_router(backups, triggers_of(control)))
                        answering.extend(dialog_routers(connect, control))
                        answering.append(
                            market_router(door)
                            if isinstance(door, MarketDoor)
                            else closed_market_router(door)
                        )
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
                        refreshing = asyncio.create_task(keep_facts(control))
                        syncing: list[asyncio.Task[None]] = []
                        loop = asyncio.get_running_loop()

                        def sync() -> None:
                            replicator = Replicator.for_home(home, store, control)
                            if replicator is not None:
                                syncing.append(asyncio.create_task(replicator.run()))

                        backups.when_carried_on(lambda: loop.call_soon_threadsafe(sync))
                        copying = asyncio.create_task(backups.run())
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
                                refreshing,
                                *syncing,
                                copying,
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
                *app_rows(control, core.paused),
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
    """The doctor's clock, `tzdata` and mismatch week rows. The clock row reads this host's newest
    row, so opening the doctor never waits on a time source."""

    def today() -> date:
        return datetime.now(UTC).date()

    def clock() -> DoctorLine:
        row = host_row(home, host_id)
        return clock_line(None if row is None else row.clock)

    max_age = setting(settings, "clock.tzdata_max_age_days", TZDATA_MAX_AGE_DAYS)
    notice = setting(settings, "clock.dst_mismatch_notice_days", DST_NOTICE_DAYS)
    harness.doctor_from(clock)
    harness.doctor_from(lambda: tzdata_line(tzdata_version(), today(), max_age))
    harness.doctor_from(lambda: mismatch_line(today(), notice))


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
    key_file = home / "vault" / "pairing-key"
    if not isinstance(url, str) or not url or not key_file.exists():
        return None
    return HubLink(url, key_file.read_text(encoding="utf-8").strip())


def forwarders_for(home: Path, core: Engine, name: str, role: Role) -> list[Forwarder]:
    """The owned instances this home asks: every node on the PC, none on a node (AD-65)."""
    key_file = home / "vault" / "pairing-key"
    if role != "pc" or not key_file.exists():
        return []
    key = key_file.read_text(encoding="utf-8").strip()
    return [
        Forwarder(instance, key=key, source=name, principal="operator", now=wall)
        for instance in owned_instances(placement_rows(core.settings), home=name)
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


@dataclasses.dataclass(frozen=True, slots=True)
class QmbRun:
    """`qmb-run` as the apps supervisor's lander port: qmx-judge's lander, with the tester's
    leave read as its `qmx.qmb.result-bundle/1` and its files read from the run folder."""

    lander: RunLander

    def open(
        self, app_id: str, version: str, job: str, inputs: Document, principal: str
    ) -> Ticket | None:
        return self.lander.open(app_id, version, job, inputs, principal)

    def close(self, landing: AppLanding) -> str:
        run, data = landing.run, landing.data
        if run is None or not isinstance(data, dict):
            raise BundleRefused(["the result is a qmx.qmb.result-bundle/1 object from a run"])
        ticket = cast(Ticket, run.ticket)
        return self.lander.close(Landing(ticket, parse_bundle(data), run.folder))

    def fail(self, ticket: AppTicket, reason: str, status: Ending) -> str:
        return self.lander.fail(cast(Ticket, ticket), reason, status=status)


def landers(store: Store, runtime: Supervisor, machine: str) -> dict[str, Lander]:
    """The core landers this host registers: `qmb-run`, writing as the operator, the one
    principal who puts records on `main`, and minting run ids named for this machine."""

    def provides_of(app_id: str, version: str) -> set[str]:
        for row in runtime.versions(app_id):
            if row["version"] == version:
                image = runtime.home / "definitions" / str(row["definition_hash"])
                return set(Definition.load(image).manifest.provides)
        return set()

    lander = RunLander(
        LanderLibrary(store),
        writer="operator",
        machine=machine,
        provides_of=provides_of,
        clock=lambda: datetime.now(UTC),
    )
    return {QMB_RUN: QmbRun(lander)}


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
    """The node's forwarding route, served only where a pairing key lets another host ask, and
    the cTrader sign-in routes, which refuse by name until a pairing key exists (AD-67)."""
    from qmx_host.venue_session import for_host  # noqa: PLC0415 - kept beside the mount (WU8)

    venue = for_host(home, engine)
    key_file = home / "vault" / "pairing-key"
    if not key_file.exists():
        return [venue]
    key = key_file.read_text(encoding="utf-8").strip()
    return [forward_router(engine.svc.remote(), key), venue]


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
    key_file = home / PAIRING_KEY
    if not key_file.exists():
        print("library: no pairing key, so the Library routes are not mounted", file=sys.stderr)
        return "", ()
    hub = HomeHub(store, home=home)
    return key_file.read_text(encoding="utf-8").strip(), [in_process(hub, bearer)]


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
