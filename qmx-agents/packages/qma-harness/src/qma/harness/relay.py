"""The loopback relay for key-provider traffic.

A key chat's CLI gets `ANTHROPIC_BASE_URL` = this relay and `ANTHROPIC_AUTH_TOKEN` = its
grant's per-launch secret. The relay checks the secret, stops any body that carries a Claude
token, runs the family guard on the requested and the served model, swaps in the real key from
the OS keyring, applies the provider's wire quirks and forwards the stream.

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
  moves.
- A body matching `TOKEN_SHAPES` gets 400 naming the rule and is never forwarded or logged.
- Header values are never logged, and the relay keeps no access log.
- Forwarded bytes are unchanged except the auth swap and the profile's `WireQuirks`. The stream
  is passed on event by event as it arrives.
- Usage is read from the stream and written as one `model_call` per upstream request. For
  relayed chats this is the only usage source.

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
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final, NewType, cast

import httpx
import keyring
import uvicorn

from qma.harness.profiles import (
    KeyProvider,
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

TOKEN_SHAPES: Final = re.compile(rb"sk-ant-(?:oat|ort|api|admin)\d{2}-[A-Za-z0-9_-]{20,}")
"""Full Claude credential shapes, never the bare prefix: OAuth access and refresh tokens, API
keys and admin keys, each with at least 20 token characters. Source: the secret-scanner
patterns inside Claude Code 2.1.296. A chat that read this file, API docs or an `.env.example`
holds only the bare prefix and keeps working."""

PATHS: Final = frozenset({"/v1/messages", "/v1/messages/count_tokens"})
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
DECODED: Final = frozenset({"content-encoding", "content-length"})
"""Response headers that no longer hold once httpx has decoded the body."""
EVENT_END: Final = re.compile(rb"\r?\n\r?\n")
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
    """What one relayed CLI launch needs. Minted only by `Relay.grant`, revoked when the chat's
    CLI disconnects, so a secret left in an old transcript opens nothing."""

    base_url: str
    secret: GrantSecret
    session_id: SessionId
    profile: KeyProvider


class GrantRefused(RuntimeError):
    """The relay will not serve this grant: a plan profile, a row that no longer validates, or
    a missing keyring entry."""


@dataclass(frozen=True)
class RelayUsage:
    """One upstream request's outcome and usage. Becomes a `model_call` journal event."""

    session_id: SessionId
    profile: ProfileName
    path: str
    status: int
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


type UsageSink = Callable[[RelayUsage], Awaitable[None]]
type AlertSink = Callable[[SessionId, str], Awaitable[None]]
"""Tells a chat the relay refused its request, so the chat shows `needs_you`."""


@dataclass
class Counters:
    bearer: int = 0
    egress: int = 0
    family: int = 0
    upstream: int = 0


@dataclass(frozen=True)
class Reply:
    status: int
    headers: list[tuple[str, str]]
    body: AsyncGenerator[bytes]


def _error(status: int, kind: str, message: str) -> Reply:
    async def body() -> AsyncGenerator[bytes]:
        yield json.dumps({"type": "error", "error": {"type": kind, "message": message}}).encode()

    return Reply(status, [("content-type", "application/json")], body())


class _Server(uvicorn.Server):
    """The host process owns the signal handlers."""

    @contextlib.contextmanager
    def capture_signals(self) -> Generator[None]:
        yield


@dataclass
class Relay:
    """One per host process. Owns the grant table and is the only run-time reader of provider
    keys. Runs on the host's event loop, so the grant table has one writer and no lock."""

    secrets: SecretLookup
    usage: UsageSink
    alert: AlertSink
    profiles: Callable[[], Profiles]
    """Re-reads `settings.toml [providers]` on each call, so a grant uses the row as it is."""
    test: TestMode | None = None
    transport: httpx.AsyncBaseTransport | None = None
    """Tests only: an in-process upstream."""
    counters: Counters = field(default_factory=Counters)
    base_url: str = ""
    _grants: dict[str, RelayGrant] = field(default_factory=dict[str, RelayGrant])
    _client: httpx.AsyncClient | None = None
    _server: _Server | None = None
    _task: asyncio.Task[None] | None = None

    async def start(self) -> Relay:
        """Bind 127.0.0.1:0 and serve. No grants yet."""
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        )
        self._server = _Server(config)
        self._task = asyncio.create_task(self._server.serve(sockets=[listener]))
        while not self._server.started:
            if self._task.done():
                self._task.result()
            await asyncio.sleep(0.01)
        return self

    def grant(self, session_id: SessionId, profile: ProfileName) -> RelayGrant:
        """Mint a fresh secret bound to this session and the provider row as it is now. A
        second grant for the same session revokes the first."""
        try:
            found = self.profiles().get(profile)
        except ProfileError as error:
            raise GrantRefused(str(error)) from None
        if not isinstance(found, KeyProvider):
            raise GrantRefused(f"{profile} is the plan; plan traffic never passes the relay")
        try:
            self.secrets(found.credential)
        except KeyError:
            raise GrantRefused(f"the keyring holds no {found.credential} entry") from None
        self.revoke(session_id)
        minted = RelayGrant(
            self.base_url, GrantSecret(secrets.token_urlsafe(32)), session_id, found
        )
        self._grants[minted.secret] = minted
        return minted

    def revoke(self, session_id: SessionId) -> None:
        """Drop the session's grant. Idempotent."""
        for secret, held in list(self._grants.items()):
            if held.session_id == session_id:
                del self._grants[secret]

    @property
    def grants(self) -> int:
        return len(self._grants)

    async def close(self) -> None:
        """Stop listening and revoke every grant. Idempotent."""
        self._grants.clear()
        if self._server is not None and self._task is not None:
            self._server.should_exit = True
            with contextlib.suppress(Exception):
                await self._task
        if self._client is not None:
            await self._client.aclose()
        self._server = self._task = self._client = None

    async def asgi(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return
        headers = {
            name.decode("latin-1").lower(): value.decode("latin-1")
            for name, value in scope["headers"]
        }

        async def body() -> bytes:
            chunks: list[bytes] = []
            while True:
                message = await receive()
                chunks.append(message.get("body", b""))
                if not message.get("more_body"):
                    return b"".join(chunks)

        reply = await self.handle(
            scope["method"], scope["path"], scope["query_string"].decode(), headers, body
        )
        await send(
            {
                "type": "http.response.start",
                "status": reply.status,
                "headers": [(k.encode("latin-1"), v.encode("latin-1")) for k, v in reply.headers],
            }
        )
        try:
            async for chunk in reply.body:
                await send({"type": "http.response.body", "body": chunk, "more_body": True})
        finally:
            with contextlib.suppress(Exception):
                await reply.body.aclose()
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    async def handle(
        self,
        method: str,
        path: str,
        query: str,
        headers: Mapping[str, str],
        read_body: Callable[[], Awaitable[bytes]],
    ) -> Reply:
        """bearer -> grant (401, body unread) -> path (404) -> egress stop (400) -> requested
        model (400) -> key swap, wire quirks, forward, served-model check, usage tee."""
        held = self._grants.get(_bearer(headers))
        if held is None:
            self.counters.bearer += 1
            return _error(401, "authentication_error", "no live relay grant")
        if method != "POST" or path not in PATHS:
            return _error(404, "not_found_error", f"the relay serves no {method} {path}")
        body = await read_body()
        if (self.test is None or self.test.relay_egress_stop) and TOKEN_SHAPES.search(body):
            self.counters.egress += 1
            reason = (
                "egress stop: the request carries a Claude credential, so the relay did not "
                "send it. Rewind or fork the chat to before the turn that carried it."
            )
            await self.alert(held.session_id, reason)
            return _error(400, "invalid_request_error", reason)
        try:
            requested = cast("dict[str, Any]", json.loads(body))["model"]
        except ValueError, TypeError, KeyError:
            return _error(400, "invalid_request_error", "the request names no model")
        refusal = guard_model(held.profile, str(requested))
        if refusal:
            self.counters.family += 1
            await self.alert(held.session_id, f"family guard: {refusal}")
            return _error(400, "invalid_request_error", f"family guard: {refusal}")
        return await self._forward(held, path, query, headers, body, str(requested))

    async def _forward(
        self,
        held: RelayGrant,
        path: str,
        query: str,
        headers: Mapping[str, str],
        body: bytes,
        requested: str,
    ) -> Reply:
        if self._client is None:
            raise RuntimeError("the relay is not started")
        profile = held.profile
        try:
            key = await asyncio.to_thread(self.secrets, profile.credential)
        except KeyError:
            return _error(401, "authentication_error", f"the keyring holds no {profile.credential}")
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
            await self._tee(held, path, 502, requested, {})
            return _error(502, "api_error", f"the provider did not answer: {type(error).__name__}")
        kept = [(k, v) for k, v in response.headers.items() if k.lower() not in DECODED]
        if response.headers.get("content-type", "").startswith("text/event-stream"):
            return Reply(response.status_code, kept, self._events(held, path, requested, response))
        data = await response.aread()
        await response.aclose()
        usage: dict[str, Any] = {}
        served = requested
        with contextlib.suppress(ValueError, TypeError, AttributeError):
            document = cast("dict[str, Any]", json.loads(data))
            served = str(document.get("model") or requested)
            usage = cast("dict[str, Any]", document.get("usage") or {})
        await self._tee(held, path, response.status_code, served, usage)
        refusal = guard_served_model(profile, served) if response.status_code < 400 else None
        if refusal:
            self.counters.family += 1
            await self.alert(held.session_id, f"family guard: {refusal}")
            return _error(400, "invalid_request_error", f"family guard: {refusal}")

        async def once() -> AsyncGenerator[bytes]:
            yield data

        return Reply(response.status_code, kept, once())

    async def _events(
        self, held: RelayGrant, path: str, requested: str, response: httpx.Response
    ) -> AsyncGenerator[bytes]:
        """Pass each SSE event on unchanged once it is complete. A barred served model ends the
        stream with an error event, and nothing after `message_start` reaches the CLI."""
        served, usage, pending = requested, dict[str, Any](), b""
        try:
            async for chunk in response.aiter_bytes():
                pending += chunk
                while (end := EVENT_END.search(pending)) is not None:
                    event, pending = pending[: end.end()], pending[end.end() :]
                    data = _event_data(event)
                    if data.get("type") == "message_start":
                        message = cast("dict[str, Any]", data.get("message") or {})
                        served = str(message.get("model") or requested)
                        usage |= cast("dict[str, Any]", message.get("usage") or {})
                        refusal = guard_served_model(held.profile, served)
                        if refusal:
                            self.counters.family += 1
                            await self.alert(held.session_id, f"family guard: {refusal}")
                            yield _error_event(f"family guard: {refusal}")
                            return
                    elif data.get("type") == "message_delta":
                        usage |= {
                            k: v
                            for k, v in cast("dict[str, Any]", data.get("usage") or {}).items()
                            if v is not None
                        }
                    yield event
            if pending:
                yield pending
        finally:
            await response.aclose()
            await self._tee(held, path, response.status_code, served, usage)

    async def _tee(
        self, held: RelayGrant, path: str, status: int, model: str, usage: Mapping[str, Any]
    ) -> None:
        def count(name: str) -> int:
            value = usage.get(name)
            return value if isinstance(value, int) else 0

        await self.usage(
            RelayUsage(
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
        )


def _bearer(headers: Mapping[str, str]) -> str:
    value = headers.get("authorization", "")
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return headers.get("x-api-key", "").strip()


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


def guard_model(profile: KeyProvider, model: str) -> str | None:
    """A refusal reason for a requested model, or None. Uses `profiles.resolve_model`, the same
    parser that accepts `ChatConfig.model`."""
    if resolve_model(profile, model) is not None:
        return None
    return family_refusal(model) or f"{model} is not one of {profile.name}'s tier models"


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
