"""The loopback relay for key-provider traffic.

A key chat's CLI gets `ANTHROPIC_BASE_URL` = this relay and `ANTHROPIC_AUTH_TOKEN` = its
grant's per-launch secret. The relay checks the secret, stops any request that carries a Claude
token, runs the family and tier guards on the requested and the served model, swaps in the real
key from the OS keyring, applies the provider's wire quirks and forwards the stream.

What it is worth. The egress stop is a tripwire for plain-text Claude tokens, not a structural
guarantee: an agent that encodes, splits or reverses a token gets past it, and a plan chat can
send a token out without touching the relay. Everything else is correctness and accounting:
wire quirks, authoritative usage, the family guard, and keys that never sit in a CLI env or a
transcript by accident. It is not a key boundary against agent Bash, which can read `qmx/*`
keyring entries as the same OS user.

Plan traffic never comes here. `grant` accepts only a `KeyProvider`, and a relayed CLI runs in
the relayed home, which holds no login.

- Binds 127.0.0.1 on an ephemeral port, never 0.0.0.0.
- A request whose bearer is not a live grant gets 401 before the body is read. Only a counter
  moves, unless the bearer is itself a Claude token.
- A request with a `TOKEN_SHAPES` match in a header value, the query or the body, raw or as a
  decoded JSON string, gets 400 naming the rule and is never forwarded or logged.
- Header values are never logged, and the relay keeps no access log.
- Forwarded bytes are unchanged except the auth swap, the model pinned to the tier's id, and
  the profile's `WireQuirks`. Nothing of a stream reaches the CLI before its `message_start`
  passes the family test; after that each event is passed on as it arrives.
- Usage is read from the stream and written as one journal row per upstream request, through
  one writer per session. For relayed chats this is the only usage source. A journal failure
  alerts the chat and never changes the reply, because a changed reply makes the CLI retry
  and spend again.
- A CLI that disconnects, or a revoked grant, stops the upstream request at once.

Paths are matched without the query string, which is forwarded as sent: `POST /v1/messages`
and `POST /v1/messages/count_tokens`. Anything else is 404.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import re
import secrets
import socket
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterator, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final, NewType, Protocol, cast
from urllib.parse import unquote_plus

import httpx
import keyring
import uvicorn

from qma.harness.profiles import (
    KeyProvider,
    ModelId,
    ProfileError,
    ProfileName,
    family_refusal,
    resolve_model,
)

if TYPE_CHECKING:
    from starlette.types import Receive, Scope, Send

    from qma.harness.home import SessionId
    from qma.harness.launch import TestMode
    from qma.harness.profiles import Profiles

TOKEN_SHAPES: Final = re.compile(r"sk-ant-(?:oat|ort|api|admin|sid)\d{2}-[A-Za-z0-9_-]{20,}")
"""Full Claude credential shapes, never the bare prefix: OAuth access and refresh tokens, API
keys, admin keys and session keys, each with at least 20 token characters. Source: the
secret-scanner patterns inside Claude Code 2.1.296, plus `sid` session keys. A chat that read
this file, API docs or an `.env.example` holds only the bare prefix and keeps working."""

MESSAGES: Final = "/v1/messages"
PATHS: Final = frozenset({MESSAGES, "/v1/messages/count_tokens"})
HOP_BY_HOP: Final = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
        "host",
        "content-length",
        "accept-encoding",
    }
)
"""Transport headers httpx sets itself on each leg."""
AUTH_HEADERS: Final = frozenset({"authorization", "x-api-key"})
DROPPED_REPLY_HEADERS: Final = HOP_BY_HOP | {"content-encoding", "set-cookie"}
"""The body arrives decoded, and the provider's cookies are not the CLI's business."""
ROUTING_FIELDS: Final = frozenset({"models", "route", "provider"})
"""Top-level fields that let a vendor such as OpenRouter route to another model."""
PRE_START: Final = frozenset({None, "ping", "error"})
"""Event types that may come before `message_start`. None of them carries model output."""
EVENT_END: Final = re.compile(rb"(?:\r\n|\r(?!\n)|\n)(?:\r\n|\r(?!\n)|\n)")
"""A blank line ends an SSE event, and a line ends in CRLF, LF or a lone CR."""
START_BYTES: Final = 64 * 1024
START_WAIT_S: Final = 120.0
STOP_WAIT_S: Final = 5.0
CLIENT_GONE: Final = 499
UPSTREAM_TIMEOUT: Final = httpx.Timeout(connect=30.0, read=600.0, write=60.0, pool=30.0)

GrantSecret = NewType("GrantSecret", str)
"""256 random bits, minted per CLI launch. Lives in relay memory and in one CLI's env. Any
process of the same OS user can read another's env, so this is a speed bump against a
neighbouring chat, not a boundary."""

type SecretLookup = Callable[[str], str]
"""Reads a `qmx/*` keyring entry. Raises `KeyError` if missing. Never logs the value."""


def keyring_secret(reference: str) -> str:
    value = keyring.get_password(reference, reference.removeprefix("qmx/"))
    if value is None:
        raise KeyError(reference)
    return value


@dataclass(frozen=True)
class RelayGrant:
    """What one relayed CLI launch needs. Minted only by `Relay.grant` and revoked by the chat
    that holds it when its CLI goes, so a secret left in an old transcript opens nothing."""

    base_url: str
    secret: GrantSecret
    session_id: SessionId
    profile: KeyProvider


class GrantRefused(RuntimeError):
    """The relay will not serve this grant: a plan profile, a row that no longer validates, or
    a keyring entry it cannot read."""


@dataclass(frozen=True)
class RelayUsage:
    """One upstream request's outcome and usage. Becomes one row of the session's run journal."""

    session_id: SessionId
    profile: ProfileName
    path: str
    status: int
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


class UsageJournal(Protocol):
    """One session's usage writer. Blocking, so the relay calls it off the event loop."""

    def append(self, usage: RelayUsage) -> None: ...
    def close(self) -> None: ...


type OpenJournal = Callable[[SessionId], UsageJournal]
type AlertSink = Callable[[SessionId, str], Awaitable[None]]
"""Tells a chat the relay refused its request or lost its usage, so the chat shows
`needs_you`."""


@dataclass
class Counters:
    bearer: int = 0
    egress: int = 0
    family: int = 0
    tier: int = 0
    upstream: int = 0


@dataclass(frozen=True)
class Reply:
    """`finish`, when set, runs once after the body whether or not it was sent: it closes the
    upstream response and journals the request."""

    status: int
    headers: list[tuple[str, str]]
    body: AsyncGenerator[bytes]
    finish: Callable[[], Awaitable[None]] | None = None


async def _once(data: bytes) -> AsyncGenerator[bytes]:
    yield data


def _error(status: int, kind: str, message: str) -> Reply:
    error = {"type": "error", "error": {"type": kind, "message": message}}
    return Reply(status, [("content-type", "application/json")], _once(json.dumps(error).encode()))


class _ClientGone(Exception):
    """The CLI disconnected before its request body arrived."""


class _Server(uvicorn.Server):
    """The host process owns the signal handlers."""

    @contextlib.contextmanager
    def capture_signals(self) -> Generator[None]:
        yield


@dataclass
class _Upstream:
    """One forwarded request: what its reply reported so far, and its one journal row."""

    relay: Relay
    held: RelayGrant
    path: str
    response: httpx.Response
    served: str
    status: int | None = None
    """Overrides the upstream status in the journal when the reply broke off."""
    usage: dict[str, Any] = field(default_factory=dict[str, Any])
    finished: bool = False

    async def finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        with contextlib.suppress(Exception):
            await self.response.aclose()
        status = self.status or self.response.status_code
        await self.relay.tee(self.held, self.path, status, self.served, self.usage)


@dataclass
class Relay:
    """One per host process. Owns the grant table, the in-flight streams and one usage journal
    writer per session, and is the only run-time reader of provider keys. Runs on the host's
    event loop, so these tables have one writer and no lock."""

    secrets: SecretLookup
    journal: OpenJournal
    alert: AlertSink
    profiles: Callable[[], Profiles]
    """Re-reads `settings.toml [providers]` on each call, so a grant uses the row as it is."""
    test: TestMode | None = None
    transport: httpx.AsyncBaseTransport | None = None
    """Tests only: an in-process upstream."""
    counters: Counters = field(default_factory=Counters)
    base_url: str = ""
    _grants: dict[str, RelayGrant] = field(default_factory=dict[str, RelayGrant])
    _streams: dict[asyncio.Task[None], RelayGrant] = field(
        default_factory=dict[asyncio.Task[None], RelayGrant]
    )
    _journals: dict[SessionId, UsageJournal] = field(default_factory=dict)
    _opening: asyncio.Lock = field(default_factory=asyncio.Lock)
    _client: httpx.AsyncClient | None = None
    _server: _Server | None = None
    _task: asyncio.Task[None] | None = None

    @property
    def egress_stop(self) -> bool:
        return self.test is None or self.test.relay_egress_stop

    async def start(self) -> Relay:
        """Bind 127.0.0.1:0 and serve. No grants yet."""
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind(("127.0.0.1", 0))
            self.base_url = f"http://127.0.0.1:{listener.getsockname()[1]}"
            self._client = httpx.AsyncClient(
                transport=self.transport, timeout=UPSTREAM_TIMEOUT, trust_env=False
            )
            config = uvicorn.Config(
                self.asgi,
                interface="asgi3",
                lifespan="off",
                proxy_headers=False,
                access_log=False,
                log_config=None,
                timeout_graceful_shutdown=int(STOP_WAIT_S),
            )
            self._server = _Server(config)
            self._task = asyncio.create_task(self._server.serve(sockets=[listener]))
            while not self._server.started:
                if self._task.done():
                    self._task.result()
                await asyncio.sleep(0.01)
        except BaseException:
            listener.close()
            if self._client is not None:
                await self._client.aclose()
            self._server = self._task = self._client = None
            raise
        return self

    async def grant(self, session_id: SessionId, profile: ProfileName) -> RelayGrant:
        """Mint a fresh secret bound to this session and the provider row as it is now. A
        second grant for the same session revokes the first."""
        try:
            found = self.profiles().get(profile)
        except ProfileError as error:
            raise GrantRefused(str(error)) from None
        if not isinstance(found, KeyProvider):
            raise GrantRefused(f"{profile} is the plan; plan traffic never passes the relay")
        try:
            await asyncio.to_thread(self.secrets, found.credential)
        except Exception as error:
            raise GrantRefused(_keyring_refusal(found.credential, error)) from None
        for older in [held for held in self._grants.values() if held.session_id == session_id]:
            await self.revoke(older)
        minted = RelayGrant(
            self.base_url, GrantSecret(secrets.token_urlsafe(32)), session_id, found
        )
        self._grants[minted.secret] = minted
        return minted

    async def revoke(self, grant: RelayGrant) -> None:
        """Drop exactly this grant, stop its in-flight streams, then close its session's
        journal writer. Idempotent."""
        if self._grants.get(grant.secret) == grant:
            del self._grants[grant.secret]
        await self._stop([task for task, held in self._streams.items() if held == grant])
        if all(held.session_id != grant.session_id for held in self._grants.values()):
            await self._close_journal(grant.session_id)

    @property
    def grants(self) -> int:
        return len(self._grants)

    async def close(self) -> None:
        """Stop every stream, stop listening and close every journal writer. Idempotent."""
        self._grants.clear()
        await self._stop(list(self._streams))
        if self._server is not None and self._task is not None:
            self._server.should_exit = True
            with contextlib.suppress(Exception):
                await self._task
        if self._client is not None:
            await self._client.aclose()
        self._server = self._task = self._client = None
        for session in list(self._journals):
            await self._close_journal(session)

    async def _stop(self, streams: list[asyncio.Task[None]]) -> None:
        streams = [task for task in streams if task is not asyncio.current_task()]
        for task in streams:
            task.cancel()
        if streams:
            await asyncio.wait(streams, timeout=STOP_WAIT_S)

    async def asgi(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Answers in a task of its own, raced against the CLI's disconnect, so a CLI that goes
        away stops the upstream request instead of leaving it streaming into a dead socket."""
        if scope["type"] != "http":
            return
        headers = {
            name.decode("latin-1").lower(): value.decode("latin-1")
            for name, value in scope["headers"]
        }
        body_read = asyncio.Event()
        started = False

        async def read_body() -> bytes:
            chunks: list[bytes] = []
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    raise _ClientGone
                chunks.append(message.get("body", b""))
                if not message.get("more_body"):
                    body_read.set()
                    return b"".join(chunks)

        async def respond() -> None:
            nonlocal started
            reply = await self.handle(
                scope["method"], scope["path"], scope["query_string"].decode(), headers, read_body
            )
            try:
                await send(
                    {
                        "type": "http.response.start",
                        "status": reply.status,
                        "headers": [
                            (name.encode("latin-1"), value.encode("latin-1"))
                            for name, value in reply.headers
                        ],
                    }
                )
                started = True
                async for chunk in reply.body:
                    await send({"type": "http.response.body", "body": chunk, "more_body": True})
            finally:
                with contextlib.suppress(Exception):
                    await reply.body.aclose()
                if reply.finish is not None:
                    await reply.finish()
            await send({"type": "http.response.body", "body": b"", "more_body": False})

        async def disconnected() -> None:
            await body_read.wait()
            while (await receive())["type"] != "http.disconnect":
                pass

        pump = asyncio.create_task(respond())
        watch = asyncio.create_task(disconnected())
        try:
            await asyncio.wait({pump, watch}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            watch.cancel()
            pump.cancel()
            await asyncio.wait({pump})
            self._streams.pop(pump, None)
        if not pump.cancelled():
            if not isinstance(pump.exception(), _ClientGone):
                pump.result()
        elif watch.cancelled():
            await _cut_off(send, started=started)

    async def handle(
        self,
        method: str,
        path: str,
        query: str,
        headers: Mapping[str, str],
        read_body: Callable[[], Awaitable[bytes]],
    ) -> Reply:
        bearer = _bearer(headers)
        held = self._grants.get(bearer)
        if held is None:
            if self.egress_stop and TOKEN_SHAPES.search(bearer):
                return await self._token_bearer()
            self.counters.bearer += 1
            return _error(401, "authentication_error", "no live relay grant")
        if (task := asyncio.current_task()) is not None:
            self._streams[cast("asyncio.Task[None]", task)] = held
        if method != "POST" or path not in PATHS:
            return _error(404, "not_found_error", f"the relay serves no {method} {path}")
        body = await read_body()
        parsed = _json(body)
        if self.egress_stop and carries_token(query, headers, body, parsed):
            self.counters.egress += 1
            return await self._refuse(
                held,
                "egress stop: the request carries a Claude credential, so the relay did not "
                "send it. Rewind or fork the chat to before the turn that carried it.",
            )
        if not isinstance(parsed, dict):
            return _error(400, "invalid_request_error", "the request names no model")
        document = cast("dict[str, object]", parsed)
        requested = document.get("model")
        if not isinstance(requested, str):
            return _error(400, "invalid_request_error", "the request names no model")
        refusal = _routing_refusal(held.profile, document) or family_refusal(requested)
        if refusal:
            self.counters.family += 1
            return await self._refuse(held, f"family guard: {refusal}")
        pinned = resolve_model(held.profile, requested)
        if pinned is None:
            self.counters.tier += 1
            return await self._refuse(
                held, f"tier guard: {requested} is not one of {held.profile.name}'s tier models"
            )
        if pinned != requested:
            document["model"] = pinned
            body = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()
        return await self._forward(held, path, query, headers, body, pinned)

    async def _token_bearer(self) -> Reply:
        """A Claude token as the bearer names no grant, so every chat that holds one hears."""
        self.counters.egress += 1
        reason = (
            "egress stop: a request to the relay used a Claude credential as its bearer, so "
            "the relay did not send it. A relayed CLI found a Claude login."
        )
        for session in {held.session_id for held in self._grants.values()}:
            await self._alert(session, reason)
        return _error(401, "authentication_error", reason)

    async def _refuse(self, held: RelayGrant, reason: str) -> Reply:
        await self._alert(held.session_id, reason)
        return _error(400, "invalid_request_error", reason)

    async def _forward(
        self,
        held: RelayGrant,
        path: str,
        query: str,
        headers: Mapping[str, str],
        body: bytes,
        model: ModelId,
    ) -> Reply:
        if self._client is None:
            raise RuntimeError("the relay is not started")
        profile = held.profile
        try:
            key = await asyncio.to_thread(self.secrets, profile.credential)
        except Exception as error:
            reason = _keyring_refusal(profile.credential, error)
            await self._alert(held.session_id, reason)
            return _error(401, "authentication_error", reason)
        request = self._client.build_request(
            "POST",
            f"{profile.base_url}{path}" + (f"?{query}" if query else ""),
            headers=swap_auth(headers, key, profile.quirks.wire.auth_header),
            content=apply_wire_quirks(profile, body),
        )
        del key
        self.counters.upstream += 1
        try:
            response = await self._client.send(request, stream=True)
        except httpx.HTTPError as error:
            await self.tee(held, path, 502, model, {})
            return _error(502, "api_error", f"the provider did not answer: {type(error).__name__}")
        except asyncio.CancelledError:
            await self.tee(held, path, CLIENT_GONE, model, {})
            raise
        upstream = _Upstream(self, held, path, response, model)
        try:
            reply = await self._reply(upstream)
        except BaseException:
            await upstream.finish()
            raise
        if reply.finish is None:
            await upstream.finish()
        return reply

    async def _reply(self, upstream: _Upstream) -> Reply:
        response, path = upstream.response, upstream.path
        if 300 <= response.status_code < 400:
            return _error(502, "api_error", "the provider answered with a redirect")
        kept = [
            (name, value)
            for name, value in response.headers.multi_items()
            if name.lower() not in DROPPED_REPLY_HEADERS
        ]
        kind = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if kind == "text/event-stream":
            events = self._events(upstream, guarded=path == MESSAGES and response.is_success)
            return Reply(response.status_code, kept, events, upstream.finish)
        try:
            data = await response.aread()
        except httpx.HTTPError as error:
            upstream.status = 502
            return _error(502, "api_error", f"the provider reply broke off: {type(error).__name__}")
        parsed = _json(data)
        document = cast("dict[str, Any]", parsed) if isinstance(parsed, dict) else {}
        upstream.usage = cast("dict[str, Any]", document.get("usage") or {})
        if path == MESSAGES and response.is_success:
            served = document.get("model")
            if not isinstance(served, str):
                return _error(502, "api_error", "the provider's reply names no model")
            upstream.served = served
            refusal = guard_served_model(upstream.held.profile, served)
            if refusal:
                self.counters.family += 1
                return await self._refuse(upstream.held, f"family guard: {refusal}")
        return Reply(response.status_code, kept, _once(data))

    async def _events(self, upstream: _Upstream, *, guarded: bool) -> AsyncGenerator[bytes]:
        """SSE events, each passed on once complete. A guarded stream holds every byte until a
        `message_start` passes the family test, and ends with an error event when the served
        model is barred, content comes first, or no `message_start` comes in time."""
        held, pending, started, failed = b"", b"", not guarded, False
        chunks = aiter(upstream.response.aiter_bytes())
        deadline = asyncio.get_running_loop().time() + START_WAIT_S
        try:
            while True:
                try:
                    async with asyncio.timeout_at(None if started else deadline):
                        chunk = await anext(chunks)
                except StopAsyncIteration:
                    break
                except TimeoutError:
                    reason = f"no message_start in {START_WAIT_S:.0f} s"
                    yield await self._stop_stream(upstream, reason)
                    return
                pending += chunk
                while (end := EVENT_END.search(pending)) is not None:
                    event, pending = pending[: end.end()], pending[end.end() :]
                    data = _event_data(event)
                    kind = data.get("type")
                    if kind == "message_start":
                        message = cast("dict[str, Any]", data.get("message") or {})
                        upstream.served = str(message.get("model") or upstream.served)
                        upstream.usage |= cast("dict[str, Any]", message.get("usage") or {})
                        refusal = guard_served_model(upstream.held.profile, upstream.served)
                        if refusal:
                            self.counters.family += 1
                            yield await self._stop_stream(upstream, f"family guard: {refusal}")
                            return
                        if not started:
                            started, event, held = True, held + event, b""
                    elif kind == "message_delta":
                        usage = cast("dict[str, Any]", data.get("usage") or {})
                        upstream.usage |= {k: v for k, v in usage.items() if v is not None}
                    if started:
                        yield event
                    elif kind in PRE_START:
                        held, failed = held + event, failed or kind == "error"
                    else:
                        reason = f"the provider sent {kind} before message_start"
                        yield await self._stop_stream(upstream, reason)
                        return
                if not started and len(held) + len(pending) > START_BYTES:
                    reason = f"no message_start in the first {START_BYTES} bytes"
                    yield await self._stop_stream(upstream, reason)
                    return
            if started or failed:
                if held + pending:
                    yield held + pending
            else:
                reason = "the provider stream ended without message_start"
                yield await self._stop_stream(upstream, reason)
        finally:
            with contextlib.suppress(Exception):
                await chunks.aclose()

    async def _stop_stream(self, upstream: _Upstream, reason: str) -> bytes:
        await self._alert(upstream.held.session_id, reason)
        return _error_event(reason)

    async def _alert(self, session_id: SessionId, reason: str) -> None:
        """Best effort: the refusal reply is the stop, so a chat that cannot take the block
        never turns it into a server error."""
        with contextlib.suppress(Exception):
            await self.alert(session_id, reason)

    async def tee(
        self, held: RelayGrant, path: str, status: int, model: str, usage: Mapping[str, Any]
    ) -> None:
        """One journal row for one upstream request. A failure alerts the chat and drops the
        writer, so the next request opens a fresh one."""

        def count(name: str) -> int:
            value = usage.get(name)
            return value if isinstance(value, int) else 0

        row = RelayUsage(
            session_id=held.session_id,
            profile=held.profile.name,
            path=path,
            status=status,
            model=model,
            input_tokens=count("input_tokens"),
            output_tokens=count("output_tokens"),
            cache_read_tokens=count("cache_read_input_tokens"),
            cache_write_tokens=count("cache_creation_input_tokens"),
        )
        try:
            async with self._opening:
                journal = self._journals.get(held.session_id)
                if journal is None:
                    journal = await asyncio.to_thread(self.journal, held.session_id)
                    self._journals[held.session_id] = journal
            await asyncio.to_thread(journal.append, row)
        except Exception as error:
            await self._close_journal(held.session_id)
            await self._alert(
                held.session_id,
                f"usage journal: {type(error).__name__}: {error}; "
                "this request's usage was not recorded",
            )

    async def _close_journal(self, session_id: SessionId) -> None:
        journal = self._journals.pop(session_id, None)
        if journal is not None:
            with contextlib.suppress(Exception):
                await asyncio.to_thread(journal.close)


async def _cut_off(send: Send, *, started: bool) -> None:
    """The grant was revoked while the CLI still listens: end its answer."""
    with contextlib.suppress(Exception):
        if not started:
            reply = _error(401, "authentication_error", "the relay grant was revoked")
            await send({"type": "http.response.start", "status": 401, "headers": reply.headers})
            async for chunk in reply.body:
                await send({"type": "http.response.body", "body": chunk, "more_body": True})
        await send({"type": "http.response.body", "body": b"", "more_body": False})


def _bearer(headers: Mapping[str, str]) -> str:
    value = headers.get("authorization", "")
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return headers.get("x-api-key", "").strip()


def _keyring_refusal(reference: str, error: Exception) -> str:
    if isinstance(error, KeyError):
        return f"the keyring holds no {reference} entry"
    return f"the keyring could not read {reference}: {type(error).__name__}"


def _json(data: bytes) -> object:
    try:
        return cast("object", json.loads(data))
    except ValueError:
        return None


def _strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in cast("dict[str, object]", value).items():
            yield key
            yield from _strings(item)
    elif isinstance(value, list):
        for item in cast("list[object]", value):
            yield from _strings(item)


def carries_token(query: str, headers: Mapping[str, str], body: bytes, document: object) -> bool:
    """True when a Claude token shape appears in the query, raw or percent-decoded, in a
    header value, in the raw body, or in a string of the decoded JSON body, where escapes such
    as `\\u002d` no longer hide it."""
    texts = (query, unquote_plus(query), *headers.values(), body.decode("latin-1"))
    return any(TOKEN_SHAPES.search(text) for text in (*texts, *_strings(document)))


def _routing_refusal(profile: KeyProvider, document: Mapping[str, object]) -> str | None:
    found = sorted(ROUTING_FIELDS & document.keys() - profile.quirks.wire.strip_fields)
    if not found:
        return None
    return f"the request sets {', '.join(found)}, which lets the vendor pick the model"


def _event_data(event: bytes) -> dict[str, Any]:
    lines = [line[5:].strip() for line in event.splitlines() if line.startswith(b"data:")]
    if not lines:
        return {}
    try:
        found: object = json.loads(b"\n".join(lines))
    except ValueError:
        return {}
    return cast("dict[str, Any]", found) if isinstance(found, dict) else {}


def _error_event(message: str) -> bytes:
    error = {"type": "error", "error": {"type": "invalid_request_error", "message": message}}
    return b"event: error\ndata: " + json.dumps(error).encode() + b"\n\n"


def guard_served_model(profile: KeyProvider, served: str) -> str | None:
    """A refusal reason for `message_start.message.model`, or None. The family test only:
    vendors report dated or canonical ids that differ from the requested one."""
    refusal = family_refusal(served)
    return f"{profile.name} served {refusal}" if refusal else None


def swap_auth(headers: Mapping[str, str], provider_key: str, style: str) -> dict[str, str]:
    """Drop the CLI's credentials and the transport headers, then set the provider's key in the
    header `style` names. Everything else is kept as sent."""
    kept = {
        name: value
        for name, value in headers.items()
        if name.lower() not in AUTH_HEADERS | HOP_BY_HOP
    }
    if style == "x-api-key":
        return kept | {"x-api-key": provider_key}
    return kept | {"authorization": f"Bearer {provider_key}"}


def apply_wire_quirks(profile: KeyProvider, body: bytes) -> bytes:
    """`body` unchanged when the profile declares no body quirks, so the common path never
    re-serializes. Otherwise strips `strip_fields` and applies `cache_markers`."""
    wire = profile.quirks.wire
    if not wire.strip_fields and wire.cache_markers == "as_sent":
        return body
    document = cast("dict[str, Any]", json.loads(body))
    for name in wire.strip_fields:
        document.pop(name, None)
    if (
        wire.cache_markers == "top_level_only"
        and "cache_control" not in document
        and '"cache_control"' in json.dumps(document.get("messages", []))
    ):
        document["cache_control"] = {"type": "ephemeral"}
    return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()
