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
import socket
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from qmx_router.relay import Relay

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
        check_s: float = CHECK_S,
        stall_s: float = STALL_S,
    ) -> None:
        self.home = home
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
        """Bind the pinned port, or the next free one and pin that instead. One writer, so a
        launch never reads a port that a second bind took."""
        wanted = _pinned(self.home)
        for port in (wanted, 0):
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                listener.bind(("127.0.0.1", port))
            except OSError:
                listener.close()
                continue
            return listener
        raise OSError("the router could not bind a loopback port")

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
        old, self._thread, self._loop = self._thread, None, None
        self._stop = None
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


def _pinned(home: Path) -> int:
    try:
        return int((home / PORT_FILE).read_text(encoding="utf-8").strip())
    except OSError, ValueError:
        return 0


def _pin(home: Path, port: int) -> None:
    home.mkdir(parents=True, exist_ok=True)
    (home / PORT_FILE).write_text(f"{port}\n", encoding="utf-8")
