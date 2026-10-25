"""The model router's own thread, loop and pinned port (AD-38, 41 H1, 42 N15).

The router shares nothing with the host's event loop. A large engine body or a slow plan stream
on the host loop cannot delay a key chat's request, and a stall in the router's loop cannot free
the copilot's. The port is pinned in `<home>/router.port` and every launch reads it, so a later
collision never splits launches across two ports.

Supervision replaces a stalled thread on the same port. An adopted `Relay` keeps its grant table
across the replacement, because the table lives on the object and every call is funnelled to
whichever loop currently serves it (`Relay._on_loop`). Streams do not survive: they belong to
the abandoned loop.

The canary is a TCP connect. It proves the listener accepts a connection and no more, which is
all this file can prove without a model call.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import socket
import threading
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from qmx_router import facts as facts_module
from qmx_router import vault as vault_module
from qmx_router.passes import Ask, PassAuthority, Refusal, bearer_of

if TYPE_CHECKING:
    from starlette.types import Receive, Scope, Send

    from qmx_router.relay import Relay

LOOPBACK: Final = "127.0.0.1"
TAILNET: Final = "0.0.0.0"  # noqa: S104  (the server's firewall admits only the tailnet, AD-71)
"""The `node` and `server` roles' bind: every interface, so the loopback health probe and the
Docker bridge reach it too. The tailnet is the only way in from outside because the server's
firewall (`qmx-recover firewall close`, engine AD-71) denies every other incoming connection but
SSH; the PC's roles keep the loopback bind."""
PORT_FILE: Final = "router.port"
"""The pinned port, one line of text, read by every launch."""
CHECK_S: Final = 5.0
"""How often the host health-checks the router (AD-38)."""
STALL_S: Final = 30.0
"""A loop that has not ticked for this long is stalled and the thread is replaced."""
TICK_S: Final = 1.0
JOIN_S: Final = 2.0
CANARY_S: Final = 2.0


class _Registered:
    service: RouterService | None = None


_registered = _Registered()


def adoptable() -> RouterService | None:
    """The service a `Relay` should join, when the host started one."""
    return _registered.service


class RouterService:
    """One router thread per host. `start` it before the harness opens, so the harness's relay
    adopts its loop; `supervise` it for the life of the host; `close` it last."""

    def __init__(
        self,
        home: Path,
        *,
        bind: str = LOOPBACK,
        check_s: float = CHECK_S,
        stall_s: float = STALL_S,
    ) -> None:
        self.home = home
        self.bind = bind
        """`127.0.0.1` on the PC's roles, `0.0.0.0` on a node (AD-12, AD-38)."""
        self.check_s = check_s
        self.stall_s = stall_s
        self.port = 0
        self.url = ""
        self.restarts = 0
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._relay: Relay | None = None
        self._listener: socket.socket | None = None
        self._stop: asyncio.Event | None = None
        self._ready = threading.Event()
        self._tick = 0.0
        self._closed = False

    async def start(self) -> RouterService:
        """Start the router's thread and register it for the next `Relay.start`."""
        _registered.service = self
        self._ensure_thread()
        return self

    def _ensure_thread(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._ready.clear()
        self._thread = threading.Thread(target=self._run, name="qmx-router", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=JOIN_S * 2):
            raise RuntimeError("the router thread did not start")

    def _run(self) -> None:
        with contextlib.suppress(BaseException):
            asyncio.run(self._main())

    async def _main(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._stop = asyncio.Event()
        ticker = asyncio.create_task(self._tick_loop())
        self._ready.set()
        try:
            await self._stop.wait()
        finally:
            ticker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await ticker

    async def _tick_loop(self) -> None:
        while True:
            self._tick = time.monotonic()
            await asyncio.sleep(TICK_S)

    async def adopt(self, relay: Relay) -> bool:
        """Serve `relay` on the router's loop and pin its port. False means the service could
        not take it, and the caller binds its own ephemeral port instead."""
        loop = self._loop
        if loop is None or loop.is_closed():
            return False
        self._relay = relay
        try:
            await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(self._serve(relay), loop))
        except BaseException:
            return False
        return True

    async def _serve(self, relay: Relay) -> None:
        listener = self._listen()
        self._listener = listener
        self.port = listener.getsockname()[1]
        self.url = f"http://127.0.0.1:{self.port}"
        _pin(self.home, self.port)
        await relay.serve_on(listener)

    def _listen(self) -> socket.socket:
        """Bind the pinned port on this service's address, or the next free one and pin that
        instead. One writer, so a launch never reads a port that a second bind took."""
        wanted = _pinned(self.home)
        for port in (wanted, 0):
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                listener.bind((self.bind, port))
            except OSError:
                listener.close()
                continue
            return listener
        raise OSError(f"the router could not bind a port on {self.bind}")

    async def canary(self) -> bool:
        """True when the pinned port accepts a connection. A TCP connect, nothing more."""
        if not self.port:
            return False
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", self.port), CANARY_S
            )
        except OSError, TimeoutError:
            return False
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
        return True

    async def supervise(self) -> None:
        """Health-check the router for the life of the host: a stalled loop, or a port that
        stopped answering, replaces the thread on the same port (42 N15)."""
        while not self._closed:
            await asyncio.sleep(self.check_s)
            if self._closed:
                return
            await self.supervise_once()

    async def supervise_once(self) -> bool:
        """One health check. True when the router was replaced. A loop past `stall_s` without a
        tick is stalled whether or not its socket still accepts."""
        if time.monotonic() - self._tick <= self.stall_s and await self.canary():
            return False
        await self.restart()
        return True

    async def restart(self) -> None:
        """Abandon the serving thread and start a fresh one on the pinned port. The grant table
        survives on the relay object; in-flight streams do not."""
        self.restarts += 1
        listener, self._listener = self._listener, None
        if listener is not None:
            with contextlib.suppress(OSError):
                listener.close()
        old_loop, self._loop = self._loop, None
        old_stop, self._stop = self._stop, None
        old, self._thread = self._thread, None
        if old_loop is not None and old_stop is not None and not old_loop.is_closed():
            # A live loop stops cleanly. A stalled one never runs this, and the daemon thread
            # stays behind because there is nothing left that could end it.
            with contextlib.suppress(RuntimeError):
                old_loop.call_soon_threadsafe(old_stop.set)
        if old is not None and old is not threading.current_thread():
            old.join(timeout=JOIN_S)
        self._ensure_thread()
        relay = self._relay
        if relay is not None:
            with contextlib.suppress(Exception):
                await self.adopt(relay)

    async def close(self) -> None:
        """Stop serving, stop the thread and forget the registration. Idempotent."""
        self._closed = True
        if _registered.service is self:
            _registered.service = None
        loop, self._loop = self._loop, None
        if loop is not None and not loop.is_closed():
            with contextlib.suppress(Exception):
                await asyncio.wrap_future(
                    asyncio.run_coroutine_threadsafe(self._stop_serving(), loop)
                )
            with contextlib.suppress(Exception):
                loop.call_soon_threadsafe(self._wake_stop)
        thread, self._thread = self._thread, None
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=JOIN_S)

    async def _stop_serving(self) -> None:
        relay = self._relay
        if relay is not None:
            with contextlib.suppress(Exception):
                await relay.stop_serving()
        listener, self._listener = self._listener, None
        if listener is not None:
            with contextlib.suppress(OSError):
                listener.close()

    def _wake_stop(self) -> None:
        if self._stop is not None:
            self._stop.set()


NODE_PORT_FILE: Final = "node.port"
"""Where the `node` role pins the port of the app the PC reaches. A node still writes
`router.port` for its own relay; this is the other listener, and it is the one with the pass
bearers."""
VAULT_STORE: Final = "vault-store.json"
"""The sealed entries the PC published, on the node's disk. `qmx node vault install` writes it and
the `node` role reads it at start. The name is repeated in `qmx_control.node` because the two
packages do not depend on each other."""
OPEN_PATHS: Final = frozenset({"/v1/health"})
"""The one route a node answers without a pass. It says a node is there and no more."""


class NodeState:
    """What a node shares over the tailnet: the facts it holds, the vault ciphertext it was
    given, and the pass list it reads. One instance per process, one writer, no lock."""

    def __init__(
        self,
        *,
        site: str,
        passes: PassAuthority,
        facts: facts_module.FactStore | None = None,
        vault: vault_module.VaultStore | None = None,
    ) -> None:
        self.site = site
        self.passes = passes
        self.facts = facts or facts_module.FactStore(site)
        self.vault = vault or vault_module.VaultStore()
        self.accepted_vault = 0
        """Entries this node took from the PC's vault sync. A rotation and a deletion each move
        it, which is what the E26 lane reads."""

    def require(self, scope: dict[str, Any], *, read: str = "", write: str = "") -> None:
        """Check the authenticated pass against this route's scope. Raises `Refusal` so a
        handler never returns 403 on its own: one place decides what a pass may do."""
        minted = scope.get("qmx.pass")
        if not minted:
            raise _Refused(Refusal("absent", "no pass on this connection"))
        for refusal in self.passes.refusals(minted, Ask(read=read, write=write)):
            raise _Refused(refusal)

    async def health(self, request: Any) -> Any:
        from starlette.responses import JSONResponse  # noqa: PLC0415

        return JSONResponse({"node": self.site, "facts": len(self.facts.snapshot().facts)})

    async def facts_route(self, request: Any) -> Any:
        from starlette.responses import JSONResponse  # noqa: PLC0415

        if request.method == "POST":
            self.require(request.scope, write="facts")
            document = await request.json()
            taken = self.facts.merge(facts_module.State.from_document(document))
            return JSONResponse({"taken": taken, "facts": len(self.facts.snapshot().facts)})
        self.require(request.scope, read="facts")
        return JSONResponse(self.facts.snapshot().document())

    async def vault_route(self, request: Any) -> Any:
        from starlette.responses import JSONResponse  # noqa: PLC0415

        if request.method == "POST":
            self.require(request.scope, write="vault")
            taken = self.vault.sync(await request.json())
            self.accepted_vault += taken
            return JSONResponse(
                {
                    "taken": taken,
                    "names": list(self.vault.names()),
                    "gone": list(self.vault.tombstones()),
                }
            )
        self.require(request.scope, read="vault")
        return JSONResponse(
            {
                "key": vault_module.as_text(self.vault.public_key),
                "names": list(self.vault.names()),
                "gone": list(self.vault.tombstones()),
            }
        )

    async def passes_route(self, request: Any) -> Any:
        """`{"revoke": "<pass id>"}` or `{"end_run": "<run id>"}`. The list is a file both ends
        read, so a refusal survives a restart on either side."""
        from starlette.responses import JSONResponse  # noqa: PLC0415

        self.require(request.scope, write="passes")
        document = await request.json()
        if not isinstance(document, dict):
            return JSONResponse({"refused": "malformed"}, status_code=400)
        body = cast("dict[str, Any]", document)
        revoked = str(body.get("revoke", ""))
        ended = str(body.get("end_run", ""))
        if revoked:
            self.passes.revocations.revoke(revoked)
        if ended:
            self.passes.end_run(ended)
        return JSONResponse(
            {
                "passes": list(self.passes.revocations.passes()),
                "runs": list(self.passes.revocations.runs()),
            }
        )


class _Refused(Exception):
    """A route's scope refusal, carried to `_refuse` so one place writes the reply."""

    def __init__(self, refusal: Refusal) -> None:
        super().__init__(str(refusal))
        self.refusal = refusal


class PassBearer:
    """The ASGI gate on a node's tailnet listener. It authenticates the bearer once, puts the
    pass in the request scope, and lets a route check scopes; a request with no pass never
    reaches a handler. The health line stays open so a lane can tell "not answering" from
    "refused"."""

    def __init__(self, app: Callable[..., Awaitable[None]], state: NodeState) -> None:
        self.app = app
        self.state = state

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope.get("path", "") in OPEN_PATHS:
            await self.app(scope, receive, send)
            return
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        token = bearer_of(headers.get("authorization", ""))
        minted, refusal = self.state.passes.check(token, Ask())
        if refusal is not None:
            await _refuse(send, refusal)
            return
        scope = dict(scope)
        scope["qmx.pass"] = minted
        await self.app(scope, receive, send)


def node_app(state: NodeState) -> Callable[..., Awaitable[None]]:
    """The node's tailnet application: four routes, every one but the health line behind a pass.
    `qmx node install-vault` and the pools' sync are the only callers (AD-12, AD-38)."""
    from starlette.applications import Starlette  # noqa: PLC0415
    from starlette.routing import Route  # noqa: PLC0415

    async def refusal_reply(request: Any, error: Exception) -> Any:
        from starlette.responses import JSONResponse  # noqa: PLC0415

        refusal = error.refusal if isinstance(error, _Refused) else Refusal("absent", str(error))
        return JSONResponse({"refused": refusal.code, "detail": refusal.detail}, status_code=403)

    return PassBearer(
        Starlette(
            routes=[
                Route("/v1/health", state.health),
                Route("/v1/facts", state.facts_route, methods=["GET", "POST"]),
                Route("/v1/vault", state.vault_route, methods=["GET", "POST"]),
                Route("/v1/passes", state.passes_route, methods=["POST"]),
            ],
            exception_handlers={_Refused: refusal_reply},
        ),
        state,
    )


async def _refuse(send: Send, refusal: Refusal) -> None:
    body = json.dumps({"refused": refusal.code, "detail": refusal.detail}).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": 403,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


def _pinned(home: Path) -> int:
    try:
        return int((home / PORT_FILE).read_text(encoding="utf-8").strip())
    except OSError, ValueError:
        return 0


def _pin(home: Path, port: int) -> None:
    home.mkdir(parents=True, exist_ok=True)
    (home / PORT_FILE).write_text(f"{port}\n", encoding="utf-8")
