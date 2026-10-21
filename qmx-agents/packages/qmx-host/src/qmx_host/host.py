"""The composition (SOLUTION-DESIGN 27.1): one process per home serves the copilot's chats, the
workflow engine, the control doors and the webhook door on one port behind one bearer.

`serve` builds, in order: the home's single-instance lock, the router's own thread and loop,
`ControlService` (the one settings reader), the `Harness` (whose relay adopts the router's loop),
the engine with its scheduler, and the control app with the chat, engine and control routes behind
the principal door. The host is the one writer of the home's Library store `<home>/library/`
(Library AD-5): it opens the store with the engine's one redaction (AD-37) and the engine reads and
writes it through `EngineLibraryAdapter`. The control's own `library.db` stays
`ControlService.library`, the truth until the cut-over, and every `library_save` and `library_link`
also writes the store through the dual write (MIGRATION step 5) attached as soon as the store
opens. The apps supervisor is `ControlService.app_runtime()`. The engine's permission policy and
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
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager, suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import IO, Any, Final, Literal

import httpx
import psutil
import qmx_control.server
import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request
from pydantic import JsonValue
from qma.harness import Harness, QmxHome, chat_routes, control_service
from qma.harness.tools import HostRead
from qmx_control.models import Document
from qmx_control.service import ControlService
from qmx_engine.admission import setting
from qmx_engine.control_door import EngineDoor
from qmx_engine.heartbeat import (
    INTERVAL_S,
    WINDOW_DAYS,
    ClassUse,
    Heartbeat,
    HeartbeatLog,
    kinds_digest,
    latest,
    node_kinds,
    qmx_version,
)
from qmx_engine.ledger import redact
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.ports.library import JsonObject
from qmx_engine.ports.router import Refused, Reply
from qmx_engine.ports.router import Row as EngineRow
from qmx_engine.ports.router import adopt as adopt_router
from qmx_engine.runner import Engine
from qmx_engine.service.rest import engine_router
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.migrate.from_library_b import DualWrite
from qmx_library.store import Store
from qmx_router import complete as router_complete
from qmx_router.pool import NoAccount
from qmx_router.relay import Relay
from qmx_router.server import RouterService

from qmx_host.door import PrincipalDoor
from qmx_host.sessions import RecordedHarness, SessionRecorder

type Role = Literal["pc", "node"]

LOCK: Final = "engine.lock"
LIBRARY: Final = "library"
STATE: Final = "control-process.json"
"""The running host's pid, port and start time, for `status`, `stop` and the refusal line."""
START_S: Final = 30.0
HOST_HISTORY: Final = 10
"""The host rows `ops_heartbeats` returns beside the newest row per subject: five minutes at the
default interval."""
DELIVERY_HEADERS: Final = ("X-QMX-Delivery", "X-GitHub-Delivery", "Idempotency-Key", "X-Request-Id")


class HostRunning(Exception):
    def __init__(self, home: Path, pid: int | None) -> None:
        who = "an unknown process" if pid is None else f"PID {pid}"
        super().__init__(f"refused: {home} already has a host, {who}; stop it first.")


def _lock(handle: IO[bytes]) -> None:
    if sys.platform == "win32":
        import msvcrt  # noqa: PLC0415

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl  # noqa: PLC0415

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


@contextmanager
def single_instance(home: Path) -> Generator[None]:
    """Hold the home's lock and its record for as long as the block runs. Raises `HostRunning`
    while another process holds it."""
    handle = (home / LOCK).open("a+b")
    try:
        _lock(handle)
    except OSError:
        handle.close()
        raise HostRunning(home, recorded_host(home)) from None
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


def recorded_host(home: Path) -> int | None:
    """The pid of the live host the home's record names, or None."""
    try:
        state = json.loads((home / STATE).read_text(encoding="utf-8"))
        pid, created = state["pid"], state["created"]
    except OSError, ValueError, KeyError, TypeError:
        return None
    if not isinstance(pid, int):
        return None
    try:
        return pid if psutil.Process(pid).create_time() == created else None
    except psutil.Error:
        return None


def serve_forever(
    home: Path,
    *,
    port: int,
    role: Role,
    ui_origin: str,
    scrubbed: Sequence[str],
    keep: Sequence[str],
) -> int:
    try:
        with single_instance(home):
            record(home, port)
            asyncio.run(serve(home, port, role, ui_origin, scrubbed, keep))
    except HostRunning as refused:
        print(refused, file=sys.stderr)
        return 1
    return 0


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


async def serve(
    home: Path, port: int, role: Role, ui_origin: str, scrubbed: Sequence[str], keep: Sequence[str]
) -> None:
    """Assumes the caller scrubbed the environment and holds the home's lock."""
    qmx_home = QmxHome(home)
    control = control_service(qmx_home)
    router = await RouterService(home).start()
    # Its own thread and loop, pinned in `<home>/router.port`; the harness's relay adopts it.
    supervising = asyncio.create_task(router.supervise())
    try:
        harness = await RecordedHarness.open(
            qmx_home, control=control, host_reads={"heartbeats": heartbeats_read(home)}
        )
        try:
            with Store.open(home / LIBRARY, redactor=redact) as store:
                control.attach_library_mirror(DualWrite(store))
                harness.record_into(SessionRecorder(store))
                adopt_router(RelayRouter(harness_relay(harness)))
                try:
                    async with EngineDoor.open(
                        control,
                        harness=HarnessAdapter(harness),
                        library=EngineLibraryAdapter(store),
                    ) as engine:
                        harness_api = chat_routes(harness, scrubbed=scrubbed, keep=keep)
                        origin = ui_origin if role == "pc" else ""
                        bearer = qmx_control.server.local_token()
                        app = compose(control, engine, harness_api, bearer, origin)
                        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port))
                        beating = asyncio.create_task(
                            heartbeats(home, role, control, harness, engine)
                        )
                        exporting = asyncio.create_task(harness.idle_exports())
                        try:
                            await server.serve()
                        finally:
                            for task in (beating, exporting):
                                task.cancel()
                                with suppress(asyncio.CancelledError):
                                    await task
                finally:
                    adopt_router(None)
        finally:
            await harness.close()
    finally:
        supervising.cancel()
        with suppress(asyncio.CancelledError):
            await supervising
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
    home: Path, host_id: str, me: psutil.Process, engine: Engine, harness: Harness
) -> Heartbeat:
    """This host's row: its own process and every child, the CLI trees included."""
    tree = [me, *me.children(recursive=True)]
    cpu, rss = 0.0, 0
    for member in tree:
        with suppress(psutil.Error):
            times = member.cpu_times()
            cpu += times.user + times.system
            rss += member.memory_info().rss
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
        free_disk_bytes=shutil.disk_usage(home).free,
    )


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
    home: Path, host_id: str, control: ControlService, harness: Harness, engine: EngineDoor
) -> None:
    """Write this host's rows every `heartbeat.interval` until cancelled. A failed beat is
    skipped, never fatal: the next one carries the same facts."""
    core = engine.svc.ctx.engine
    me = psutil.Process()
    log = HeartbeatLog(home, setting(core.settings, "heartbeat.window_days", WINDOW_DAYS))
    pruned: int | None = None
    while True:
        try:
            rows = [beat(home, host_id, me, core, harness), *app_rows(control, core.paused)]
            await asyncio.to_thread(log.write, rows)
            hour = int(time.time() // 3600)
            if hour != pruned:
                await asyncio.to_thread(log.prune, datetime.now(UTC))
                pruned = hour
        except (OSError, ValueError, psutil.Error) as error:
            print(f"heartbeat skipped: {type(error).__name__}: {error}", file=sys.stderr)
        await asyncio.sleep(setting(core.settings, "heartbeat.interval", INTERVAL_S))


def heartbeats_read(home: Path) -> HostRead:
    """The `ops_heartbeats` read: the newest row per subject and the host's last rows."""

    async def read(_arguments: dict[str, Any]) -> Mapping[str, object]:
        def load() -> Mapping[str, object]:
            newest = latest(home)
            since = datetime.now(UTC) - timedelta(hours=1)
            found = HeartbeatLog(home, 1).rows(since)
            hosts = [row for row in found if row.subject == "host"][-HOST_HISTORY:]
            return {
                "latest": {key: row.model_dump(mode="json") for key, row in newest.items()},
                "host_history": [row.model_dump(mode="json") for row in hosts],
            }

        return await asyncio.to_thread(load)

    return read


def compose(
    control: ControlService,
    engine: EngineDoor,
    harness_api: Sequence[APIRouter],
    bearer: str,
    ui_origin: str,
) -> FastAPI:
    """The one REST app: control, chat and engine routes behind one bearer and the principal
    door. `ui_origin` is the one origin CORS allows, none when empty."""
    app = qmx_control.server.create_app(
        control,
        bearer,
        ui_origin,
        extra_routers=[*harness_api, engine_router(engine), webhook_door(engine)],
    )
    routes = [route for api in harness_api for route in api.routes]
    app.add_middleware(PrincipalDoor, chat_routes=routes)
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


def health(port: int) -> int | None:
    """The pid the host on `port` reports, or None."""
    try:
        response = httpx.get(
            f"http://127.0.0.1:{port}/api/health",
            headers={"Authorization": f"Bearer {qmx_control.server.local_token()}"},
            timeout=2,
        )
    except httpx.HTTPError:
        return None
    pid = response.json().get("pid") if response.status_code == 200 else None
    return pid if isinstance(pid, int) else None


def start(home: Path, port: int, role: Role, ui_origin: str) -> int:
    """`serve` in a background process, once it answers `/api/health`."""
    running = recorded_host(home)
    if running is not None:
        print(HostRunning(home, running), file=sys.stderr)
        return 1
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            print(f"Port {port} is already occupied.", file=sys.stderr)
            return 1
    command = [sys.executable, "-m", "qmx_host", "serve", "--home", str(home), "--port", str(port)]
    command += ["--role", role, "--ui-origin", ui_origin]
    with (home / "control.log").open("ab") as log:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    deadline = time.monotonic() + START_S
    while time.monotonic() < deadline:
        if process.poll() is not None:
            print("The host failed to start; see control.log.", file=sys.stderr)
            return 1
        pid = health(port)
        if pid is not None and pid == recorded_host(home):
            print(f"Started qmx_host as PID {pid} on port {port}.")
            return 0
        time.sleep(0.1)
    terminate(process.pid)
    print("The host did not become ready; see control.log.", file=sys.stderr)
    return 1


def status(home: Path) -> int:
    pid = recorded_host(home)
    if pid is None:
        print("qmx_host is stopped.")
        return 0
    port = json.loads((home / STATE).read_text(encoding="utf-8"))["port"]
    if health(port) != pid:
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
