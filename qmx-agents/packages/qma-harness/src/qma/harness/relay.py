"""The loopback relay for non-plan traffic: key providers and the GPT lane.

A key or GPT chat's CLI gets `ANTHROPIC_BASE_URL` = this relay and `ANTHROPIC_AUTH_TOKEN` = its
grant's per-launch secret. The relay checks the secret and stops any request that carries a
Claude token. Key lane: it runs the family and tier guards on the requested and the served
model, swaps in the real key from the OS keyring, applies the provider's wire quirks and
forwards the stream. GPT lane: it pins the tier, translates the request to OpenAI Responses
with `qma.gpt.translate`, sends it with the ChatGPT sign-in's access token, checks the served
model is a GPT model, and translates the stream back.

The GPT lane opens only through `open_gpt_lane(ProbePassed, ...)`. Before a pass exists, probes
P2 to P7 reach it through `probe_grant(ProbeRun, ...)`, a grant bound to one probe run and
refused for a run that already had one. A GPT grant for an unattended chat needs the sign-in's
stored background consent (SIWC terms, B17).

What it is worth. The egress stop is a tripwire for plain-text Claude tokens, not a structural
guarantee: an agent that encodes, splits or reverses a token gets past it, and a plan chat can
send a token out without touching the relay. Known misses, kept as limits: a percent-encoded
header value, a query percent-encoded twice, a JSON escape inside a JSON document nested in a
string, base64, and a token split across two strings. Everything else is correctness and
accounting: wire quirks, authoritative usage, the family guard, and keys that never sit in a
CLI env or a transcript by accident. It is not a key boundary against agent Bash, which can
read `qmx/*` keyring entries as the same OS user.

Plan traffic never comes here. `grant` accepts only a `KeyProvider` or the `GptPlan`, and a
relayed CLI runs in the relayed home, which holds no login.

- Binds 127.0.0.1 on an ephemeral port, never 0.0.0.0.
- A request whose bearer is not a live grant gets 401 before the body is read. Only a counter
  moves, unless the bearer is itself a Claude token.
- A request with a `TOKEN_SHAPES` match in a header value, the query or the body, raw or as a
  decoded JSON string, gets 400 naming the rule and is never forwarded or logged. A body that
  is not one JSON object with unique keys at every depth, nested at most `JSON_DEPTH` deep,
  gets 400, so the bytes forwarded always parse to the document that was checked.
- Header values are never logged, and the relay keeps no access log.
- Forwarded bytes are unchanged except the auth swap, the model pinned to the tier's id, and
  the profile's `WireQuirks`. Nothing of a stream reaches the CLI before its `message_start`
  passes the family test; after that each event is passed on as it arrives. A `message_start`
  with no string model, an event whose `event:` name and `type` differ, or a non-object
  `message` or `usage` ends the stream with an error event and an alert. A provider error
  before `message_start` reaches the CLI alone, without the events held before it.
- Usage is read from the stream and written as one journal row per upstream request, through
  one writer per session. For relayed chats this is the only usage source. A journal failure
  alerts the chat and never changes the reply, because a changed reply makes the CLI retry
  and spend again. A revoke waits up to `STOP_WAIT_S` for rows still being written before it
  closes the writer, and alerts the chat if one is still running.
- A CLI that disconnects, or a revoked grant, stops the upstream request at once.

Paths are matched without the query string, which is forwarded as sent: `POST /v1/messages`
and `POST /v1/messages/count_tokens`. Anything else is 404. On the GPT lane `count_tokens` is a
local estimate, since the route has no counting endpoint.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import re
import secrets
import socket
from collections.abc import (
    AsyncGenerator,
    Awaitable,
    Callable,
    Coroutine,
    Generator,
    Iterator,
    Mapping,
)
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final, NewType, Protocol, cast
from urllib.parse import unquote_plus

import httpx
import keyring
import uvicorn

from qma.gpt import translate
from qma.gpt.probe import ProbePassed, ProbeRun, translator_version
from qma.gpt.siwc import SignInError, SiwcSession
from qma.harness.home import SessionId
from qma.harness.profiles import (
    GptPlan,
    KeyProvider,
    ModelId,
    ProfileError,
    ProfileName,
    family_refusal,
    gpt_refusal,
    resolve_model,
)

if TYPE_CHECKING:
    from starlette.types import Receive, Scope, Send

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
JSON_DEPTH: Final = 512
"""Deeper JSON is refused: the relay's own walks and `json.dumps` recurse, and a deeper
document would raise `RecursionError` mid-request."""
START_WAIT_S: Final = 120.0
STOP_WAIT_S: Final = 5.0
CLIENT_GONE: Final = 499
UPSTREAM_TIMEOUT: Final = httpx.Timeout(connect=30.0, read=600.0, write=60.0, pool=30.0)
PING_S: Final = 15.0
"""A GPT stream silent this long gets an Anthropic `ping`, as Anthropic's own streams do."""

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
    profile: KeyProvider | GptPlan


class GrantRefused(RuntimeError):
    """The relay will not serve this grant: a plan profile, a row that no longer validates, a
    keyring entry it cannot read, a GPT grant while the GPT lane is closed, a GPT grant for an
    unattended chat without background consent, or a second probe grant for one probe run."""


@dataclass(frozen=True)
class GptRoute:
    """What a GPT request needs: the sign-in whose access token it carries."""

    session: SiwcSession


@dataclass(frozen=True)
class GptLane:
    """The GPT lane is open for chats. Only `Relay.open_gpt_lane` builds one, from a
    `ProbePassed` for the current translator version."""

    passed: ProbePassed
    route: GptRoute


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


def _dumps(document: object) -> bytes:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()


def _error(status: int, kind: str, message: str) -> Reply:
    error = {"type": "error", "error": {"type": kind, "message": message}}
    return Reply(status, [("content-type", "application/json")], _once(json.dumps(error).encode()))


class _ClientGone(Exception):
    pass


class _Server(uvicorn.Server):
    """The host process owns the signal handlers."""

    @contextlib.contextmanager
    def capture_signals(self) -> Generator[None]:
        yield


@dataclass
class _Upstream:
    relay: Relay
    held: RelayGrant
    path: str
    response: httpx.Response
    served: str
    journal_status: int | None = None
    usage: dict[str, Any] = field(default_factory=dict[str, Any])
    finished: bool = False

    async def finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        await self.relay.settle(self.held.session_id, self._close_and_journal())

    async def _close_and_journal(self) -> None:
        with contextlib.suppress(Exception):
            await self.response.aclose()
        status = self.journal_status or self.response.status_code
        await self.relay.write_row(self.held, self.path, status, self.served, self.usage)


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
    gpt: GptLane | None = None
    siwc: SiwcSession | None = None
    """The one ChatGPT sign-in of this process, kept while the lane closes and reopens, so its
    in-memory access token is never thrown away: OpenAI allows a refresh only near the end of
    a token's hour."""
    _grants: dict[str, RelayGrant] = field(default_factory=dict[str, RelayGrant])
    _probes: dict[str, GptRoute] = field(default_factory=dict[str, GptRoute])
    """Probe grant secret -> route, while its run lasts."""
    _probe_runs: set[str] = field(default_factory=set[str])
    """Every probe run that has had its grant, so a run never gets a second one."""
    _streams: dict[asyncio.Task[None], RelayGrant] = field(
        default_factory=dict[asyncio.Task[None], RelayGrant]
    )
    _journals: dict[SessionId, UsageJournal] = field(default_factory=dict[SessionId, UsageJournal])
    _writes: dict[asyncio.Task[None], SessionId] = field(
        default_factory=dict[asyncio.Task[None], SessionId]
    )
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

    async def grant(
        self, session_id: SessionId, profile: ProfileName, *, unattended: bool = False
    ) -> RelayGrant:
        """Mint a fresh secret bound to this session and the provider row as it is now. A
        second grant for the same session revokes the first. A GPT grant needs the GPT lane
        open and, for an unattended chat, the sign-in's background consent."""
        try:
            found = self.profiles().get(profile)
        except ProfileError as error:
            raise GrantRefused(str(error)) from None
        match found:
            case KeyProvider():
                try:
                    await asyncio.to_thread(self.secrets, found.credential)
                except Exception as error:
                    raise GrantRefused(_keyring_refusal(found.credential, error)) from None
            case GptPlan():
                if self.gpt is None:
                    raise GrantRefused(
                        "the GPT lane is closed: no GPT probe has passed for this translator "
                        "version; type /login chatgpt"
                    )
                if unattended and not self.gpt.route.session.background_consent:
                    raise GrantRefused(
                        "a Background GPT chat needs your consent to use your ChatGPT plan "
                        "unattended; /login chatgpt asks for it"
                    )
            case _:
                raise GrantRefused(f"{profile} is the plan; plan traffic never passes the relay")
        return await self._mint(session_id, found)

    async def _mint(self, session_id: SessionId, profile: KeyProvider | GptPlan) -> RelayGrant:
        for older in [held for held in self._grants.values() if held.session_id == session_id]:
            await self.revoke(older)
        minted = RelayGrant(
            self.base_url, GrantSecret(secrets.token_urlsafe(32)), session_id, profile
        )
        self._grants[minted.secret] = minted
        return minted

    async def probe_grant(
        self, run: ProbeRun, session: SiwcSession, profile: GptPlan
    ) -> RelayGrant:
        """A grant for probes P2 to P7 while the GPT lane may still be closed. Bound to one
        `ProbeRun` (minted only by `qma.gpt.probe`) and revoked when the run ends, so a spent
        grant answers 401. A run gets one grant only."""
        if run.run_id in self._probe_runs:
            raise GrantRefused(f"probe run {run.run_id} already had its grant")
        self._probe_runs.add(run.run_id)
        minted = await self._mint(SessionId(run.run_id), profile)
        self._probes[minted.secret] = GptRoute(session)
        return minted

    async def open_gpt_lane(self, passed: ProbePassed, session: SiwcSession) -> GptLane:
        """The only way to open the GPT lane for chats. The pass is keyed to `translate.py`'s
        version hash, so a pass for a changed translator is refused."""
        if passed.translator_version != translator_version():
            raise GrantRefused("the GPT probe passed for another translator version; re-probe")
        self.siwc = session
        self.gpt = GptLane(passed, GptRoute(session))
        return self.gpt

    async def close_gpt_lane(self) -> None:
        """Close the lane and revoke every GPT chat grant. Probe grants belong to their run.
        Idempotent."""
        self.gpt = None
        for held in [
            held
            for held in self._grants.values()
            if isinstance(held.profile, GptPlan) and held.secret not in self._probes
        ]:
            await self.revoke(held)

    async def revoke(self, grant: RelayGrant) -> None:
        """Drop exactly this grant, stop its in-flight streams, then close its session's
        journal writer. Idempotent."""
        if self._grants.get(grant.secret) == grant:
            del self._grants[grant.secret]
            self._probes.pop(grant.secret, None)
        await self._stop([task for task, held in self._streams.items() if held == grant])
        if all(held.session_id != grant.session_id for held in self._grants.values()):
            await self._close_journal(grant.session_id)

    @property
    def grants(self) -> int:
        return len(self._grants)

    async def close(self) -> None:
        """Stop every stream, stop listening and close every journal writer. Idempotent."""
        self._grants.clear()
        self._probes.clear()
        self.gpt = None
        await self._stop(list(self._streams))
        if self._server is not None and self._task is not None:
            self._server.should_exit = True
            with contextlib.suppress(Exception):
                await self._task
        if self._client is not None:
            await self._client.aclose()
        self._server = self._task = self._client = None
        for session in {*self._journals, *self._writes.values()}:
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
            await _end_revoked(send, started=started)

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
            message = (
                "the request body is not one JSON object with unique keys, "
                f"nested {JSON_DEPTH} deep at most"
            )
            return _error(400, "invalid_request_error", message)
        document = cast("dict[str, object]", parsed)
        requested = document.get("model")
        if not isinstance(requested, str):
            return _error(400, "invalid_request_error", "the request names no model")
        profile = held.profile
        if isinstance(profile, GptPlan):
            return await self._gpt(held, profile, path, document, requested)
        refusal = _routing_refusal(profile, document) or family_refusal(requested)
        if refusal:
            self.counters.family += 1
            return await self._refuse(held, f"family guard: {refusal}")
        pinned = resolve_model(profile, requested)
        if pinned is None:
            return await self._tier_refusal(held, requested)
        if pinned != requested:
            document["model"] = pinned
            body = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()
        return await self._forward(held, profile, path, query, headers, body, pinned)

    async def _tier_refusal(self, held: RelayGrant, requested: str) -> Reply:
        self.counters.tier += 1
        return await self._refuse(
            held, f"tier guard: {requested} is not one of {held.profile.name}'s tier models"
        )

    def _gpt_route(self, held: RelayGrant) -> GptRoute | None:
        if held.secret in self._probes:
            return self._probes[held.secret]
        return None if self.gpt is None else self.gpt.route

    async def _gpt(
        self,
        held: RelayGrant,
        profile: GptPlan,
        path: str,
        document: dict[str, object],
        requested: str,
    ) -> Reply:
        """The GPT lane: tier pin, translation, the sign-in's token, then the stream back."""
        route = self._gpt_route(held)
        if route is None:
            self.counters.bearer += 1
            return _error(401, "authentication_error", "the GPT lane is closed")
        pinned = resolve_model(profile, requested)
        if pinned is None:
            return await self._tier_refusal(held, requested)
        if path != MESSAGES:
            count = {"input_tokens": translate.estimate_tokens(document)}
            return Reply(200, [("content-type", "application/json")], _once(_dumps(count)))
        try:
            translation = translate.to_responses(document, model=pinned)
        except translate.RefusedRequest as error:
            return _error(400, "invalid_request_error", str(error))
        try:
            token = await route.session.access_token()
        except SignInError as error:
            await self._alert(held.session_id, f"ChatGPT sign-in: {error}")
            return _error(401, "authentication_error", f"ChatGPT sign-in: {error}")
        if self._client is None:
            raise RuntimeError("the relay is not started")
        request = self._client.build_request(
            "POST",
            f"{route.session.api}/responses",
            headers={
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "accept": "text/event-stream",
            },
            content=_dumps(translation.body),
        )
        del token
        self.counters.upstream += 1
        try:
            response = await self._client.send(request, stream=True)
        except httpx.HTTPError as error:
            await self.tee(held, path, 502, pinned, {})
            return _error(502, "api_error", f"ChatGPT did not answer: {type(error).__name__}")
        except asyncio.CancelledError:
            await self.tee(held, path, CLIENT_GONE, pinned, {})
            raise
        upstream = _Upstream(self, held, path, response, pinned)
        state = translate.StreamState(translation, pinned)
        try:
            if response.status_code != 200:
                data = await response.aread()
                parsed = _json(data)
                body = cast("dict[str, Any]", parsed) if isinstance(parsed, dict) else {}
                error = body.get("error")
                found = cast("dict[str, Any]", error) if isinstance(error, dict) else {}
                status, kind, message = translate.map_error(response.status_code, found)
                await upstream.finish()
                return _error(status, kind, message)
            events = self._gpt_events(upstream, state)
            if document.get("stream") is True:
                headers = [("content-type", "text/event-stream"), ("cache-control", "no-cache")]
                return Reply(200, headers, events, upstream.finish)
            async for _ in events:
                pass
            await upstream.finish()
            if state.error is not None:
                return _error(*state.error)
            return Reply(
                200, [("content-type", "application/json")], _once(_dumps(state.message()))
            )
        except BaseException:
            await upstream.finish()
            raise

    async def _gpt_events(
        self, upstream: _Upstream, state: translate.StreamState
    ) -> AsyncGenerator[bytes]:
        """Responses SSE in, Anthropic SSE out. The served model must be a GPT model before
        any output reaches the CLI. Usage is taken from `response.completed`."""
        lines: asyncio.Queue[str | None] = asyncio.Queue()
        broken: list[str] = []

        async def pump() -> None:
            """Reads in a task of its own, so a ping timeout cancels only a queue wait and
            never the upstream read."""
            try:
                async for line in upstream.response.aiter_lines():
                    lines.put_nowait(line)
            except httpx.HTTPError as error:
                broken.append(type(error).__name__)
            finally:
                lines.put_nowait(None)

        reader = asyncio.create_task(pump())
        block: list[str] = []
        try:
            while not state.ended:
                try:
                    async with asyncio.timeout(PING_S if state.started else START_WAIT_S):
                        line = await lines.get()
                except TimeoutError:
                    if not state.started:
                        yield await self._stop_stream(
                            upstream, f"ChatGPT sent nothing in {START_WAIT_S:.0f} s"
                        )
                        return
                    yield translate.SseEvent("ping", {"type": "ping"}).encode()
                    continue
                if line is None:
                    break
                if line:
                    block.append(line)
                    continue
                for event in translate.parse_sse(block):
                    out = state.feed(event)
                    refusal = None if state.served is None else gpt_refusal(state.served)
                    if refusal:
                        self.counters.family += 1
                        yield await self._stop_stream(
                            upstream, f"family guard: gpt served {refusal}"
                        )
                        return
                    for sse in out:
                        yield sse.encode()
                block = []
            if not state.ended:
                cut = f" ({broken[0]})" if broken else ""
                yield await self._stop_stream(
                    upstream, f"the ChatGPT stream ended without response.completed{cut}"
                )
        finally:
            reader.cancel()
            await asyncio.wait({reader})
            upstream.served = state.served or upstream.served
            upstream.usage = dict(state.usage)
            if state.error is not None:
                upstream.journal_status = state.error[0]

    async def _token_bearer(self) -> Reply:
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
        profile: KeyProvider,
        path: str,
        query: str,
        headers: Mapping[str, str],
        body: bytes,
        model: ModelId,
    ) -> Reply:
        if self._client is None:
            raise RuntimeError("the relay is not started")
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
            upstream.journal_status = 502
            return _error(502, "api_error", f"the provider reply broke off: {type(error).__name__}")
        parsed = _json(data)
        document = cast("dict[str, Any]", parsed) if isinstance(parsed, dict) else {}
        usage = document.get("usage")
        upstream.usage = cast("dict[str, Any]", usage) if isinstance(usage, dict) else {}
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
        held, errors, pending, started = b"", b"", b"", not guarded
        chunks = cast("AsyncGenerator[bytes]", upstream.response.aiter_bytes())
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
                    try:
                        kind, data = _parse_event(event)
                    except _MalformedEvent as error:
                        yield await self._stop_stream(upstream, f"the provider sent {error}")
                        return
                    if kind == "message_start":
                        message = cast("dict[str, Any]", data["message"])
                        upstream.served = cast("str", message["model"])
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
                        held += event
                        if kind == "error":
                            errors += event
                    else:
                        reason = f"the provider sent {kind} before message_start"
                        yield await self._stop_stream(upstream, reason)
                        return
                if not started and len(held) + len(pending) > START_BYTES:
                    reason = f"no message_start in the first {START_BYTES} bytes"
                    yield await self._stop_stream(upstream, reason)
                    return
            if started:
                if pending:
                    yield pending
            elif errors:
                yield errors
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
        await self.settle(held.session_id, self.write_row(held, path, status, model, usage))

    async def settle(self, session_id: SessionId, work: Coroutine[Any, Any, None]) -> None:
        """Runs `work` to the end even when the caller is cancelled, and lets `_close_journal`
        wait for it, so a revoke never closes the writer under a row still being written."""
        task = asyncio.create_task(work)
        self._writes[task] = session_id
        task.add_done_callback(self._writes.pop)
        await asyncio.shield(task)

    async def write_row(
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
            await self._drop_journal(held.session_id)
            await self._alert(
                held.session_id,
                f"usage journal: {type(error).__name__}: {error}; "
                "this request's usage was not recorded",
            )

    async def _close_journal(self, session_id: SessionId) -> None:
        writes = [task for task, session in self._writes.items() if session == session_id]
        if writes:
            _, late = await asyncio.wait(writes, timeout=STOP_WAIT_S)
            if late:
                await self._alert(
                    session_id,
                    "usage journal: a write was still running when the writer closed; "
                    "that request's usage may not be recorded",
                )
        await self._drop_journal(session_id)

    async def _drop_journal(self, session_id: SessionId) -> None:
        journal = self._journals.pop(session_id, None)
        if journal is not None:
            with contextlib.suppress(Exception):
                await asyncio.to_thread(journal.close)


async def _end_revoked(send: Send, *, started: bool) -> None:
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


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    document = dict(pairs)
    if len(document) < len(pairs):
        raise ValueError("repeated key")
    return document


def _json(data: bytes) -> object:
    """None for anything but JSON with unique keys at every depth, nested at most
    `JSON_DEPTH` deep. With a repeated key the relay would check the last value while a
    first-wins upstream parser acts on the first."""
    try:
        document = cast("object", json.loads(data, object_pairs_hook=_unique_keys))
    except ValueError, RecursionError:
        return None
    level = [document]
    for _ in range(JSON_DEPTH):
        level = [child for value in level for child in _children(value)]
    return None if any(isinstance(value, dict | list) for value in level) else document


def _children(value: object) -> list[object]:
    if isinstance(value, dict):
        return list(cast("dict[str, object]", value).values())
    if isinstance(value, list):
        return cast("list[object]", value)
    return []


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


class _MalformedEvent(Exception):
    pass


def _parse_event(event: bytes) -> tuple[str | None, dict[str, Any]]:
    """The event's kind and data. The CLI's SDK dispatches on the `event:` name and the guards
    read the data's `type`, so an event where the two differ is refused, and an unnamed
    event's kind is its `type`."""
    lines = event.splitlines()
    names = [line[6:].strip().decode("latin-1") for line in lines if line.startswith(b"event:")]
    payload = [line[5:].strip() for line in lines if line.startswith(b"data:")]
    found = _json(b"\n".join(payload)) if payload else None
    data = cast("dict[str, Any]", found) if isinstance(found, dict) else {}
    name = names[-1] if names else None
    kind = data.get("type", name)
    if not isinstance(kind, str | None):
        raise _MalformedEvent("an event whose type is not a string")
    if name is not None and kind != name:
        raise _MalformedEvent(f"an event named {name} whose type is {kind}")
    if kind == "message_start":
        message = data.get("message")
        start = cast("dict[str, Any]", message) if isinstance(message, dict) else {}
        if not isinstance(start.get("model"), str) or not isinstance(
            start.get("usage") or {}, dict
        ):
            raise _MalformedEvent("a malformed message_start")
    if kind == "message_delta" and not isinstance(data.get("usage") or {}, dict):
        raise _MalformedEvent("a malformed message_delta")
    return kind, data


def _error_event(message: str) -> bytes:
    error = {"type": "error", "error": {"type": "invalid_request_error", "message": message}}
    return b"event: error\ndata: " + json.dumps(error).encode() + b"\n\n"


def guard_served_model(profile: KeyProvider | GptPlan, served: str) -> str | None:
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
