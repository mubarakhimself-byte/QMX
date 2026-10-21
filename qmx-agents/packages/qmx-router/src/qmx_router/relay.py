"""The loopback relay for non-plan traffic: key providers, the GPT lane and the chat lane.

A key or GPT chat's CLI gets `ANTHROPIC_BASE_URL` = this relay and `ANTHROPIC_AUTH_TOKEN` = its
grant's per-launch secret. The relay checks the secret and stops any request that carries a
Claude token. Key lane: it runs the family and tier guards on the requested and the served
model, swaps in the real key from the OS keyring, applies the provider's wire quirks and
forwards the stream. GPT lane: it pins the tier, translates the request to OpenAI Responses
with `qmx_router.gpt.translate`, sends it with the ChatGPT sign-in's access token, checks the served
model is a GPT model, and translates the stream back. Chat lane: a row whose `wire` is
`openai_chat` goes through `qmx_router.chat_lane`, key only, with the same normaliser first and a
header set of its own, so no Anthropic-only field leaves.

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

Every request is routed by its own `model` field, never by the grant's main profile alone
(AD-29, AD-38). A tier alias belongs to the main profile; any other id is looked up in the model
registry and goes to the provider, wire and key row it names, so one Kimi-main chat runs a
DeepSeek sub-agent and a GLM judge in the same process. An id no row holds is refused, never
guessed, and a provider outside the grant's `model_scope` is refused. Each request is normalised
for its target row before it leaves (AD-50, `qmx_router.normalise`).

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
import time
from collections.abc import (
    AsyncGenerator,
    Awaitable,
    Callable,
    Coroutine,
    Generator,
    Iterator,
    Mapping,
    Sequence,
)
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final, NewType, Protocol, cast
from urllib.parse import unquote_plus, urlsplit

import httpx
import keyring
import uvicorn

from qmx_router import chat_lane, complete
from qmx_router.classify import Classification, classify
from qmx_router.gpt import translate
from qmx_router.gpt.probe import ProbePassed, ProbeRun, stored_result, translator_version
from qmx_router.gpt.siwc import SignInError, SiwcSession
from qmx_router.ids import SessionId
from qmx_router.normalise import normalise, refuse_retry
from qmx_router.pool import AccountPool, AccountSpec, Lease, NoAccount
from qmx_router.profiles import (
    ClaudePlan,
    GptPlan,
    KeyProvider,
    ModelId,
    ProfileError,
    ProfileName,
    family_refusal,
    gpt_refusal,
    normalize,
    resolve_model,
)
from qmx_router.registry import ModelRow, QmxId, Registry, bundled

if TYPE_CHECKING:
    from pathlib import Path

    from starlette.types import Receive, Scope, Send

    from qmx_router.profiles import Profiles

TOKEN_SHAPES: Final = re.compile(r"sk-ant-(?:oat|ort|api|admin|sid)\d{2}-[A-Za-z0-9_-]{20,}")
"""Full Claude credential shapes, never the bare prefix: OAuth access and refresh tokens, API
keys, admin keys and session keys, each with at least 20 token characters. Source: the
secret-scanner patterns inside Claude Code 2.1.296, plus `sid` session keys. A chat that read
this file, API docs or an `.env.example` holds only the bare prefix and keeps working."""

MESSAGES: Final = "/v1/messages"
CHAT: Final = "/v1/chat/completions"
"""The chat lane's upstream path under the provider's base URL. That holds for a host whose one
base serves both routes, as OpenRouter's does; a profile whose chat route sits elsewhere has no way
to say so yet (BACKLOG, RTR3)."""
COMPLETE_PATH: Final = "/complete"
"""The journal path a `complete` row carries: not a CLI request, so not `MESSAGES`."""
ROUTER_SESSION: Final = "router"
"""The journal session a `complete` with no session writes its one row under."""
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
UPSTREAM_TIMEOUT: Final = httpx.Timeout(connect=30.0, read=None, write=60.0, pool=30.0)
"""No read bound on the upstream. A legal 1M-token prefill waits 720 s before its first token,
so a fixed read timeout would cut the very request AD-50 (8) sizes for. The first event is
bounded per row in `_events`, and the CLI bounds the whole request by `API_TIMEOUT_MS`."""
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
    that holds it when its CLI goes, so a secret left in an old transcript opens nothing.

    `profile` is the chat's main, which owns a tier alias and the GPT sign-in. `model_scope` is
    every provider the chat may address under this grant (H14), so a Kimi-main chat reaches the
    DeepSeek row and nothing outside its scope. `agent_id` is the launching agent, journalled
    with every row (H36); empty when the launcher names none."""

    base_url: str
    secret: GrantSecret
    session_id: SessionId
    profile: KeyProvider | GptPlan
    model_scope: frozenset[ProfileName] = frozenset()
    agent_id: str = ""


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
    agent_id: str = ""
    """The launching agent (H36), empty when the launcher names none."""
    account: str = ""
    """The pool account that served it (AD-12), empty on a plan or pre-pool row."""


class EgressTest(Protocol):
    """The one switch of the harness's `TestMode` the relay reads."""

    @property
    def relay_egress_stop(self) -> bool: ...


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


@dataclass(frozen=True)
class _KeyLaneRequest:
    """A request for a row on the Anthropic wire: the provider to lease and the row's id."""

    provider: KeyProvider
    row: ModelRow | None
    pinned: str


@dataclass(frozen=True)
class _GptLaneRequest:
    """A request for a GPT row, through the process's one ChatGPT sign-in."""

    profile: GptPlan
    pinned: str
    row: ModelRow | None


@dataclass(frozen=True)
class _Refused:
    """A refusal worded here, alerted by `handle`, or a finished reply when one is already
    built."""

    reason: str | None = None
    reply: Reply | None = None


type _Routed = _KeyLaneRequest | _GptLaneRequest | _Refused

NO_OUTPUT_LIMIT: Final = 2**31 - 1
"""A settings row no bundled profile describes clamps nothing: no one declared a limit."""


def _unknown_row(profile: KeyProvider, pinned: str) -> ModelRow:
    """The row for a provider that exists only in `settings.toml`: the identity rules still
    apply, every beta is dropped, the capabilities are kept, and `max_tokens` is not clamped."""
    return ModelRow(
        qmx_id=QmxId(f"{profile.name}/{pinned}"),
        provider=profile.name,
        native=ModelId(pinned),
        tool_search=(
            "native" if profile.quirks.env.get("ENABLE_TOOL_SEARCH") == "true" else "none"
        ),
        cache_ttl="1h",
        vision=True,
        pdf=True,
        audio=True,
        max_output=NO_OUTPUT_LIMIT,
    )


async def _once(data: bytes) -> AsyncGenerator[bytes]:
    yield data


def _dumps(document: object) -> bytes:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()


def _error(status: int, kind: str, message: str) -> Reply:
    error = {"type": "error", "error": {"type": kind, "message": message}}
    return Reply(status, [("content-type", "application/json")], _once(json.dumps(error).encode()))


def _ping() -> bytes:
    """One SSE ping, only for a row that opted into keepalive."""
    return translate.SseEvent("ping", {"type": "ping"}).encode()


def _prompt_tokens(row: ModelRow, body: bytes) -> int:
    """A prompt estimate from the bytes, at the row's own chars_per_token (AD-34)."""
    return max(0, int(len(body) / row.chars_per_token))


class _ClientGone(Exception):
    pass


class _Server(uvicorn.Server):
    """The host process owns the signal handlers."""

    @contextlib.contextmanager
    def capture_signals(self) -> Generator[None]:
        yield


@dataclass(frozen=True)
class _RefusedCandidate:
    """One `complete` candidate's refusal: the sentence the caller reads, and whether another
    account of the same row could still serve it."""

    reason: str
    rotate: bool


@dataclass(frozen=True)
class _Sent:
    """An upstream request whose response headers arrived inside the row's bound. `lease` is the
    account it was sent on, settled when the request ends."""

    response: httpx.Response
    wait: float
    deadline: float
    lease: Lease


@dataclass
class _Upstream:
    relay: Relay
    held: RelayGrant
    path: str
    response: httpx.Response
    served: str
    row: ModelRow | None = None
    provider: ProfileName | None = None
    """The provider the request went to, which differs from the main on a mixed chat."""
    lease: Lease | None = None
    """The account this request holds, settled once at `finish`."""
    error: Classification | None = None
    """The provider's refusal, read once by the classifier. Its class cools or benches the
    account; a success leaves it None and lifts a stale cooldown."""
    start_wait: float = START_WAIT_S
    """The row's no-progress bound on the first event, or the Claude default when no row
    describes the target (AD-50 (8), Appendix H)."""
    deadline: float | None = None
    """When that bound runs out, on the loop clock, measured from before the request was sent.
    A provider that sends its SSE headers late spends the same window, so a slow prefill cannot
    hide behind the headers."""
    keepalive: bool = False
    """Per-row opt-in, off by default: nothing is sent to the CLI before the upstream's first
    event, so a late error keeps its own status (42 N3)."""
    error_class: str = ""
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
        await self.relay.write_row(
            self.held, self.path, status, self.served, self.usage, self.provider
        )
        await self.relay.settle_lease(self)


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
    registry: Callable[[], Registry] = bundled
    """The model rows a request's `model` field resolves through. Bundled by default; a host
    passes its user-overridden load."""
    test: EgressTest | None = None
    transport: httpx.AsyncBaseTransport | None = None
    """Tests only: an in-process upstream."""
    counters: Counters = field(default_factory=Counters)
    base_url: str = ""
    pool: AccountPool | None = None
    """The host's pool (AD-12). A host passes its own, with the accounts and overrides the
    settings hold; a relay with none keeps one built from the profiles it serves, so every key
    and GPT request still takes a lease."""
    gpt: GptLane | None = None
    siwc: SiwcSession | None = None
    probe_state: Path | None = None
    """The folder holding the stored GPT probe result. When set, every GPT grant re-reads
    it, so a removed pass or a changed translator stops new grants at once, not only at the
    next start or switch."""
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
    _loop: asyncio.AbstractEventLoop | None = None
    """The loop that serves this relay. Its own thread's loop when the host runs one
    (`qmx_router.server`); the caller's loop otherwise. Every mutation happens on it."""
    _built_pool: AccountPool | None = None
    """The pool this relay built from its profiles when the host passed none."""

    @property
    def egress_stop(self) -> bool:
        return self.test is None or self.test.relay_egress_stop

    async def start(self) -> Relay:
        """Serve on 127.0.0.1 and own a loop. The host's router service adopts the socket and
        serving task on its own thread's loop when one is running; otherwise this loop binds an
        ephemeral port. No grants yet either way."""
        from qmx_router.server import adoptable  # noqa: PLC0415  (server imports this module)

        service = adoptable()
        if service is not None and await service.adopt(self):
            return self
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind(("127.0.0.1", 0))
            await self.serve_on(listener)
        except BaseException:
            listener.close()
            await self.stop_serving()
            raise
        return self

    async def serve_on(self, listener: socket.socket) -> None:
        """Create one loop's client and serving task on `listener`, and wait until it serves."""
        self._loop = asyncio.get_running_loop()
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

    async def stop_serving(self) -> None:
        """Stop serving and forget the loop-bound client, so a restarted thread can bind again."""
        if self._server is not None:
            self._server.should_exit = True
        if self._task is not None:
            with contextlib.suppress(Exception):
                await self._task
        if self._client is not None:
            with contextlib.suppress(Exception):
                await self._client.aclose()
        self._server = self._task = self._client = None
        self._loop = None

    async def _on_loop[T](self, work: Coroutine[Any, Any, T]) -> T:
        """Run `work` on the loop that serves this relay, so its tables keep one writer and no
        lock, whichever loop the caller holds."""
        loop = self._loop
        if loop is None or loop is asyncio.get_running_loop():
            return await work
        return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(work, loop))

    async def grant(
        self,
        session_id: SessionId,
        profile: ProfileName,
        *,
        unattended: bool = False,
        agent_id: str = "",
    ) -> RelayGrant:
        """Mint a fresh secret bound to this session and the provider row as it is now. A
        second grant for the same session revokes the first. A GPT grant needs the GPT lane
        open and, for an unattended chat, the sign-in's background consent. `agent_id` is
        journalled with every row this grant makes (H36)."""
        return await self._on_loop(
            self._grant(session_id, profile, unattended=unattended, agent_id=agent_id)
        )

    async def _grant(
        self,
        session_id: SessionId,
        profile: ProfileName,
        *,
        unattended: bool = False,
        agent_id: str = "",
    ) -> RelayGrant:
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
                if self.gpt is not None and not await self._pass_holds(self.gpt.passed):
                    await self.close_gpt_lane()
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
        return await self._mint(session_id, found, agent_id)

    async def _pass_holds(self, passed: ProbePassed) -> bool:
        version = translator_version()
        if passed.translator_version != version:
            return False
        if self.probe_state is None:
            return True
        return await asyncio.to_thread(stored_result, self.probe_state, version) == passed

    async def _mint(
        self, session_id: SessionId, profile: KeyProvider | GptPlan, agent_id: str = ""
    ) -> RelayGrant:
        for older in [held for held in self._grants.values() if held.session_id == session_id]:
            await self.revoke(older)
        minted = RelayGrant(
            self.base_url,
            GrantSecret(secrets.token_urlsafe(32)),
            session_id,
            profile,
            self._scope(profile),
            agent_id,
        )
        self._grants[minted.secret] = minted
        return minted

    def _scope(self, main: KeyProvider | GptPlan) -> frozenset[ProfileName]:
        """Every provider a chat under this relay may address (H14). The default is every
        configured provider: a chat narrows its own scope only when it says so, and the plan is
        never in it because no request here reaches the plan."""
        try:
            names = set(self.profiles().by_name) - {ProfileName("claude")}
        except Exception:
            names = {main.name}
        return frozenset(names)

    def accounts(self) -> AccountPool:
        """The pool this relay leases accounts from. A host passes its own; a relay with none
        keeps one built from the profiles it serves, re-read with each call so a settings change
        lands, and keeps every cooldown it already learned."""
        if self.pool is not None:
            return self.pool
        if self._built_pool is None:
            self._built_pool = AccountPool()
        self._built_pool.sync(_account_specs(self.profiles()))
        return self._built_pool

    def _lease_affinity(self, session_id: SessionId, provider: ProfileName) -> str:
        """One account per chat per provider, so a running chat keeps its account (AD-12)."""
        return f"{session_id}:{provider}"

    def release_session(self, session: str) -> None:
        """Give back every account a chat or a run held. Its revoke does this too; a `complete`
        caller that ends a run without a grant calls this."""
        pool = self.pool if self.pool is not None else self._built_pool
        if pool is not None:
            pool.release_prefix(f"{session}:")

    async def _lease(self, held: RelayGrant, provider: ProfileName, model: str) -> Lease | Reply:
        """One account for one request, or the error the CLI gets when every one is out."""
        try:
            return self.accounts().lease(
                provider=provider,
                model=model,
                affinity=self._lease_affinity(held.session_id, provider),
            )
        except NoAccount as error:
            if error.alert:
                await self._alert(held.session_id, str(error))
            return _error(503, "api_error", str(error))

    async def settle_lease(self, upstream: _Upstream) -> None:
        """Record one request's outcome on its account: a success lifts a stale cooldown, a
        refusal closes the account as its class says. One alert per account bench."""
        lease = upstream.lease
        if lease is None:
            return
        notice = self.accounts().settle(lease, upstream.error)
        if notice is not None:
            await self._alert(upstream.held.session_id, notice.text)

    async def probe_grant(
        self, run: ProbeRun, session: SiwcSession, profile: GptPlan
    ) -> RelayGrant:
        """A grant for probes P2 to P7 while the GPT lane may still be closed. Bound to one
        `ProbeRun` (minted only by `qmx_router.gpt.probe`) and revoked when the run ends, so a spent
        grant answers 401. A run gets one grant only."""
        return await self._on_loop(self._probe_grant(run, session, profile))

    async def _probe_grant(
        self, run: ProbeRun, session: SiwcSession, profile: GptPlan
    ) -> RelayGrant:
        if run.run_id in self._probe_runs:
            raise GrantRefused(f"probe run {run.run_id} already had its grant")
        self._probe_runs.add(run.run_id)
        minted = await self._mint(SessionId(run.run_id), profile)
        self._probes[minted.secret] = GptRoute(session)
        return minted

    async def open_gpt_lane(self, passed: ProbePassed, session: SiwcSession) -> GptLane:
        """The only way to open the GPT lane for chats. The pass is keyed to `translate.py`'s
        version hash, so a pass for a changed translator is refused."""
        return await self._on_loop(self._open_gpt_lane(passed, session))

    async def _open_gpt_lane(self, passed: ProbePassed, session: SiwcSession) -> GptLane:
        if passed.translator_version != translator_version():
            raise GrantRefused("the GPT probe passed for another translator version; re-probe")
        self.siwc = session
        self.gpt = GptLane(passed, GptRoute(session))
        return self.gpt

    async def close_gpt_lane(self) -> None:
        """Close the lane and revoke every GPT chat grant. Probe grants belong to their run.
        Idempotent."""
        await self._on_loop(self._close_gpt_lane())

    async def _close_gpt_lane(self) -> None:
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
        await self._on_loop(self._revoke(grant))

    async def _revoke(self, grant: RelayGrant) -> None:
        if self._grants.get(grant.secret) == grant:
            del self._grants[grant.secret]
            self._probes.pop(grant.secret, None)
        pool = self.pool if self.pool is not None else self._built_pool
        if pool is not None:
            pool.release_prefix(f"{grant.session_id}:")
        await self._stop([task for task, held in self._streams.items() if held == grant])
        if all(held.session_id != grant.session_id for held in self._grants.values()):
            await self._close_journal(grant.session_id)

    @property
    def grants(self) -> int:
        return len(self._grants)

    async def close(self) -> None:
        """Stop every stream, stop listening and close every journal writer. Idempotent."""
        await self._on_loop(self._close())

    async def _close(self) -> None:
        self._grants.clear()
        self._probes.clear()
        self.gpt = None
        await self._stop(list(self._streams))
        await self.stop_serving()
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
        match self._route(held, requested):
            case _Refused(reason=reason, reply=reply):
                if reason is None:
                    return cast("Reply", reply)
                return await self._refuse(held, reason)
            case _GptLaneRequest(profile=route_profile, pinned=pinned, row=row):
                return await self._gpt(held, route_profile, path, document, pinned, row)
            case _KeyLaneRequest(provider=provider, row=row, pinned=pinned):
                refusal = _routing_refusal(provider, document)
                if refusal:
                    self.counters.family += 1
                    return await self._refuse(held, f"family guard: {refusal}")
                if row is not None and row.wire == "openai_chat":
                    return await self._chat(
                        held, provider, path, query, headers, document, pinned, row
                    )
                if pinned != requested:
                    document["model"] = pinned
                    body = _dumps(document)
                return await self._forward(
                    held,
                    provider,
                    path,
                    query,
                    headers,
                    body,
                    pinned,
                    row,
                    streamed=document.get("stream") is True,
                )

    def _route(self, held: RelayGrant, requested: str) -> _Routed:
        """The lane and provider one request's `model` field names (AD-29, AD-38). A tier alias
        belongs to the grant's main; any other id goes through the registry; anything left is a
        refusal, never a guess."""
        main = held.profile
        pinned = resolve_model(main, requested)
        if pinned is not None:
            if isinstance(main, GptPlan):
                return _GptLaneRequest(main, pinned, self._row_for(main, pinned))
            return _KeyLaneRequest(main, self._row_for(main, pinned), pinned)
        row = self._registry_row(requested)
        if (
            row is not None
            and row.provider != ProfileName("claude")
            and (row.provider != main.name or requested == row.qmx_id)
        ):
            return self._by_row(held, row)
        if isinstance(main, GptPlan):
            return self._tier_reply(held, requested)
        refusal = family_refusal(requested)
        if refusal:
            self.counters.family += 1
            return self._family_reply(requested, refusal)
        return self._tier_reply(held, requested)

    def _registry_row(self, requested: str) -> ModelRow | None:
        """The row whose `qmx_id` or native id is `requested`, or None. Two rows that both claim
        it are an ambiguity the request gets to keep: None."""
        rows = self.registry().rows()
        norm = normalize(requested)
        found = [
            row
            for row in rows
            if requested in (row.qmx_id, row.native)
            or norm in (normalize(row.qmx_id), normalize(row.native))
        ]
        return found[0] if len(found) == 1 else None

    def _row_for(self, main: KeyProvider | GptPlan, pinned: str) -> ModelRow | None:
        """The row describing `pinned` under the grant's main provider, so the normaliser uses
        the row's own quirks rather than a profile-wide guess."""
        registry = self.registry()
        provider = registry.providers.get(main.name)
        if provider is None and isinstance(main, KeyProvider):
            provider = registry.for_host(urlsplit(main.base_url).hostname or "")
        if provider is not None:
            row = next((row for row in provider.models if row.native == pinned), None)
            if row is not None:
                return row
        if isinstance(main, GptPlan):
            return None
        return _unknown_row(main, pinned)

    def _by_row(self, held: RelayGrant, row: ModelRow) -> _Routed:
        """A row the registry holds, on the wire it names. The scope check comes first so a
        grant never reaches a provider it was not given."""
        if held.model_scope and row.provider not in held.model_scope:
            return _Refused(
                reply=_error(
                    403,
                    "permission_error",
                    f"{row.provider} is outside this chat's model_scope",
                )
            )
        try:
            target = self.profiles().get(row.provider)
        except ProfileError as error:
            return _Refused(reply=_error(400, "invalid_request_error", f"family guard: {error}"))
        match (target, row.wire):
            case (KeyProvider(), "anthropic" | "openai_chat"):
                return _KeyLaneRequest(target, row, row.native)
            case (GptPlan(), "responses"):
                return _GptLaneRequest(target, row.native, row)
            case _:
                return _Refused(
                    reply=_error(
                        400,
                        "invalid_request_error",
                        f"family guard: {row.qmx_id} is a {row.wire} row on a "
                        f"{target.name} provider",
                    )
                )

    def _family_reply(self, requested: str, refusal: str) -> _Refused:
        message = f"family guard: {refusal}"
        if "is a claude model" in refusal:
            message += f"; reach {requested} through `delegate` on a plan profile"
        return _Refused(reason=message)

    def _tier_reply(self, held: RelayGrant, requested: str) -> _Refused:
        self.counters.tier += 1
        return _Refused(
            reason=f"tier guard: {requested} is not one of {held.profile.name}'s tier models"
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
        pinned: str,
        row: ModelRow | None,
    ) -> Reply:
        """The GPT lane: the sign-in's token, the normalised body, translation, the stream back."""
        route = self._gpt_route(held)
        if route is None:
            self.counters.bearer += 1
            return _error(401, "authentication_error", "the GPT lane is closed")
        if path != MESSAGES:
            count = {"input_tokens": translate.estimate_tokens(document)}
            return Reply(200, [("content-type", "application/json")], _once(_dumps(count)))
        if row is not None:
            document = cast(
                "dict[str, object]",
                json.loads(normalise(row, _dumps(document), {}).body),
            )
        try:
            translation = translate.to_responses(document, model=pinned)
        except translate.RefusedRequest as error:
            return _error(400, "invalid_request_error", str(error))
        leased = await self._lease(held, held.profile.name, pinned)
        if isinstance(leased, Reply):
            return leased
        try:
            token = await route.session.access_token()
        except SignInError as error:
            self.accounts().release(leased)
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
            await self._settle_now(leased, classify(502, {}), held.session_id)
            await self.tee(held, path, 502, pinned, {})
            return _error(502, "api_error", f"ChatGPT did not answer: {type(error).__name__}")
        except asyncio.CancelledError:
            await self.tee(held, path, CLIENT_GONE, pinned, {})
            self.accounts().release(leased)
            raise
        upstream = _Upstream(
            self, held, path, response, pinned, provider=held.profile.name, lease=leased
        )
        state = translate.StreamState(translation, pinned)
        try:
            if response.status_code != 200:
                data = await response.aread()
                parsed = _json(data)
                body = cast("dict[str, Any]", parsed) if isinstance(parsed, dict) else {}
                error = body.get("error")
                found = cast("dict[str, Any]", error) if isinstance(error, dict) else {}
                status, kind, message = translate.map_error(response.status_code, found)
                upstream.error = classify(
                    response.status_code, found or body, dict(response.headers)
                )
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
                upstream.error = classify(state.error[0], {"message": state.error[2]})

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
        model: str,
        row: ModelRow | None,
        streamed: bool = False,
    ) -> Reply:
        if row is None:
            egress, out_headers = body, dict(headers)
        else:
            normalised = normalise(row, body, headers)
            egress, out_headers = normalised.body, normalised.headers
        leased = await self._lease(held, profile.name, model)
        if isinstance(leased, Reply):
            return leased
        sent = await self._send(
            held,
            profile,
            path,
            query,
            out_headers,
            apply_wire_quirks(profile, egress),
            model,
            row,
            _prompt_tokens(row, body) if row is not None else 0,
            streamed,
            leased,
        )
        if isinstance(sent, Reply):
            return sent
        upstream = _Upstream(
            self,
            held,
            path,
            sent.response,
            model,
            row,
            provider=profile.name,
            lease=sent.lease,
            start_wait=sent.wait,
            deadline=sent.deadline,
            keepalive=bool(row is not None and row.keepalive),
        )
        try:
            reply = await self._reply(upstream)
        except BaseException:
            await upstream.finish()
            raise
        if reply.finish is None:
            await upstream.finish()
        return reply

    async def _send(
        self,
        held: RelayGrant,
        profile: KeyProvider,
        path: str,
        query: str,
        headers: Mapping[str, str],
        content: bytes,
        model: str,
        row: ModelRow | None,
        prompt_tokens: int,
        streamed: bool,
        lease: Lease,
        target: str | None = None,
    ) -> _Sent | Reply:
        """One upstream request up to its response headers, under the row's no-progress bound
        (AD-50 (8)). Both key-lane paths share it, so the bound and the 504 reply are one.
        `target` is the upstream path when it is not the CLI's own, and the journal keeps the
        CLI's either way. Every failure on this leg settles the lease itself, because nothing
        downstream will see it."""
        if self._client is None:
            raise RuntimeError("the relay is not started")
        credential = lease.account.credential or profile.credential
        try:
            key = await asyncio.to_thread(self.secrets, credential)
        except Exception as error:
            # A local keyring miss is not a provider answer, so nothing is learned about the
            # account: the lease goes back and the chat is told.
            self.accounts().release(lease)
            reason = _keyring_refusal(credential, error)
            await self._alert(held.session_id, reason)
            return _error(401, "authentication_error", reason)
        request = self._client.build_request(
            "POST",
            f"{profile.base_url}{target or path}" + (f"?{query}" if query else ""),
            headers=swap_auth(headers, key, profile.quirks.wire.auth_header),
            content=content,
        )
        del key
        self.counters.upstream += 1
        loop = asyncio.get_running_loop()
        wait = START_WAIT_S if row is None else row.first_token_timeout(prompt_tokens)
        deadline = loop.time() + wait
        try:
            async with asyncio.timeout_at(deadline):
                response = await self._client.send(request, stream=True)
        except TimeoutError:
            await self._settle_now(lease, classify(504, {}), held.session_id)
            return await self._late(held, path, model, profile, wait, streamed)
        except httpx.HTTPError as error:
            await self._settle_now(lease, classify(502, {}), held.session_id)
            await self.tee(held, path, 502, model, {}, profile.name)
            return _error(502, "api_error", f"the provider did not answer: {type(error).__name__}")
        except asyncio.CancelledError:
            await self.tee(held, path, CLIENT_GONE, model, {}, profile.name)
            self.accounts().release(lease)
            raise
        return _Sent(response, wait, deadline, lease)

    async def _settle_now(
        self, lease: Lease, error: Classification | None, session_id: SessionId | None = None
    ) -> None:
        """Settle a lease on a request leg that built no upstream object."""
        notice = self.accounts().settle(lease, error)
        if notice is not None and session_id is not None:
            await self._alert(session_id, notice.text)

    async def _chat(
        self,
        held: RelayGrant,
        profile: KeyProvider,
        path: str,
        query: str,
        headers: Mapping[str, str],
        document: dict[str, object],
        pinned: str,
        row: ModelRow,
    ) -> Reply:
        """The chat lane: normalise for the row, translate to chat completions, translate the
        stream back (H12). A fresh body and this lane's own headers mean no Anthropic-only field
        leaves, and a thinking block another provider signed never arrives."""
        streamed = document.get("stream") is True
        if path != MESSAGES:
            count = {"input_tokens": translate.estimate_tokens(document)}
            return Reply(200, [("content-type", "application/json")], _once(_dumps(count)))
        normalised = normalise(row, _dumps(document), headers)
        document = cast("dict[str, object]", json.loads(normalised.body))
        try:
            translation = chat_lane.to_chat(document, model=pinned)
        except chat_lane.RefusedRequest as error:
            return _error(400, "invalid_request_error", str(error))
        leased = await self._lease(held, profile.name, pinned)
        if isinstance(leased, Reply):
            return leased
        sent = await self._send(
            held,
            profile,
            path,
            query,
            self._chat_headers(row, normalised.headers),
            _dumps(translation.body),
            pinned,
            row,
            _prompt_tokens(row, normalised.body),
            streamed,
            leased,
            target=CHAT,
        )
        if isinstance(sent, Reply):
            return sent
        upstream = _Upstream(
            self,
            held,
            path,
            sent.response,
            pinned,
            row,
            provider=profile.name,
            lease=sent.lease,
            start_wait=sent.wait,
            deadline=sent.deadline,
        )
        state = chat_lane.StreamState(translation, pinned)
        try:
            if not sent.response.is_success:
                return await self._chat_error(upstream)
            events = self._chat_events(upstream, state)
            if streamed:
                headers_out = [("content-type", "text/event-stream"), ("cache-control", "no-cache")]
                return Reply(200, headers_out, events, upstream.finish)
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

    def _chat_headers(self, row: ModelRow, headers: Mapping[str, str]) -> dict[str, str]:
        """Chat completions' own header set. Only the headers the row forwards come across, so
        `anthropic-version`, `anthropic-beta` and every `x-claude-code-*` header stay behind."""
        kept = {"content-type": "application/json", "accept": "text/event-stream"}
        for name in row.forward_headers:
            if name in headers:
                kept[name] = headers[name]
        return kept

    async def _chat_error(self, upstream: _Upstream) -> Reply:
        """An error reply, mapped once and refused a retry the pool must rotate away from."""
        data = await upstream.response.aread()
        parsed = _json(data)
        document = cast("dict[str, Any]", parsed) if isinstance(parsed, dict) else {}
        error = document.get("error")
        table = cast("dict[str, Any]", error) if isinstance(error, dict) else document
        status, kind, message = chat_lane.map_error(upstream.response.status_code, table)
        upstream.error = classify(
            upstream.response.status_code, table, dict(upstream.response.headers)
        )
        await upstream.finish()
        reply = _error(status, kind, message)
        refused = list(refuse_retry(upstream.response.status_code, data).items())
        return Reply(reply.status, reply.headers + refused, reply.body)

    async def _chat_events(
        self, upstream: _Upstream, state: chat_lane.StreamState
    ) -> AsyncGenerator[bytes]:
        """Chat-completions SSE in, Anthropic SSE out. Nothing reaches the CLI before the first
        chunk, so a late error keeps its own status; after that the row's no-progress bound is
        spent. A served model outside the provider family ends the stream as the key lane does."""
        lines: asyncio.Queue[str | None] = asyncio.Queue()
        broken: list[str] = []
        loop = asyncio.get_running_loop()
        deadline = upstream.deadline or (loop.time() + upstream.start_wait)

        async def pump() -> None:
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
                    async with asyncio.timeout_at(None if state.started else deadline):
                        line = await lines.get()
                except TimeoutError:
                    yield await self._stop_stream(
                        upstream, f"no chat-completions chunk in {upstream.start_wait:.0f} s"
                    )
                    return
                if line is None:
                    break
                if line:
                    block.append(line)
                    continue
                for chunk in chat_lane.parse_sse(block):
                    for event in state.feed(chunk):
                        yield event.encode()
                    if state.error is not None:
                        status, _, message = state.error
                        upstream.error = classify(status, {"message": message})
                        upstream.error_class = upstream.error.kind
                        upstream.journal_status = status
                        await self._alert(
                            upstream.held.session_id,
                            f"{upstream.provider} stream error ({upstream.error_class}): {message}",
                        )
                        return
                    refusal = None if state.served is None else family_refusal(state.served)
                    if refusal:
                        self.counters.family += 1
                        yield await self._stop_stream(upstream, f"family guard: {refusal}")
                        return
                block = []
            if not state.ended:
                cut = f" ({broken[0]})" if broken else ""
                for event in state.finish():
                    yield event.encode()
                if state.error is not None:
                    status, _, message = state.error
                    upstream.error = classify(status, {"message": message})
                    upstream.error_class = upstream.error.kind
                    upstream.journal_status = status
                    await self._alert(
                        upstream.held.session_id,
                        f"{upstream.provider} stream error ({upstream.error_class}): "
                        f"{message}{cut}",
                    )
        finally:
            reader.cancel()
            await asyncio.wait({reader})
            upstream.served = state.served or upstream.served
            upstream.usage = dict(state.usage)
            if state.error is not None:
                upstream.journal_status = state.error[0]

    async def _late(
        self,
        held: RelayGrant,
        path: str,
        model: str,
        profile: KeyProvider,
        wait: float,
        streamed: bool,
    ) -> Reply:
        """No headers inside the row's bound. Nothing was answered, so nothing is retried: one
        request was sent and the CLI gets an error event it stops on."""
        reason = f"no message_start in {wait:.0f} s"
        await self.tee(held, path, 504, model, {}, profile.name)
        await self._alert(held.session_id, reason)
        if streamed:
            headers = [("content-type", "text/event-stream"), ("cache-control", "no-cache")]
            return Reply(200, headers, _once(_error_event(reason)))
        return _error(504, "api_error", reason)

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
        if not response.is_success:
            upstream.error = classify(
                response.status_code, document or data, dict(response.headers)
            )
            kept += list(refuse_retry(response.status_code, document or data).items())
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
        loop = asyncio.get_running_loop()
        deadline = upstream.deadline or (loop.time() + upstream.start_wait)
        try:
            while True:
                try:
                    limit = None if started else deadline
                    if not started and upstream.keepalive:
                        limit = min(deadline, loop.time() + PING_S)
                    async with asyncio.timeout_at(limit):
                        chunk = await anext(chunks)
                except StopAsyncIteration:
                    break
                except TimeoutError:
                    if not started and upstream.keepalive and loop.time() < deadline:
                        yield _ping()
                        continue
                    reason = f"no message_start in {upstream.start_wait:.0f} s"
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
                            upstream.error = classify(500, data)
                            upstream.error_class = upstream.error.kind
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
                await self._alert(
                    upstream.held.session_id,
                    f"the provider answered with an error event ({upstream.error_class})",
                )
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
        self,
        held: RelayGrant,
        path: str,
        status: int,
        model: str,
        usage: Mapping[str, Any],
        provider: ProfileName | None = None,
    ) -> None:
        await self.settle(
            held.session_id, self.write_row(held, path, status, model, usage, provider)
        )

    async def settle(self, session_id: SessionId, work: Coroutine[Any, Any, None]) -> None:
        """Runs `work` to the end even when the caller is cancelled, and lets `_close_journal`
        wait for it, so a revoke never closes the writer under a row still being written."""
        task = asyncio.create_task(work)
        self._writes[task] = session_id
        task.add_done_callback(self._writes.pop)
        await asyncio.shield(task)

    async def write_row(
        self,
        held: RelayGrant,
        path: str,
        status: int,
        model: str,
        usage: Mapping[str, Any],
        provider: ProfileName | None = None,
    ) -> None:
        """One journal row for one upstream request, naming the provider that served it rather
        than the chat's main."""

        def count(name: str) -> int:
            value = usage.get(name)
            return value if isinstance(value, int) else 0

        await self.record_usage(
            RelayUsage(
                session_id=held.session_id,
                profile=provider or held.profile.name,
                path=path,
                status=status,
                model=model,
                input_tokens=count("input_tokens"),
                output_tokens=count("output_tokens"),
                cache_read_tokens=count("cache_read_input_tokens"),
                cache_write_tokens=count("cache_creation_input_tokens"),
                agent_id=held.agent_id,
            )
        )

    async def record_usage(self, row: RelayUsage) -> None:
        """Write one row through the session's writer. A failure alerts the session and drops
        the writer, so the next request opens a fresh one."""
        try:
            async with self._opening:
                journal = self._journals.get(row.session_id)
                if journal is None:
                    journal = await asyncio.to_thread(self.journal, row.session_id)
                    self._journals[row.session_id] = journal
            await asyncio.to_thread(journal.append, row)
        except Exception as error:
            await self._drop_journal(row.session_id)
            await self._alert(
                row.session_id,
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
    ) -> complete.Completion:
        """One answer from a key or GPT row, with no CLI process (AD-56): one request through
        the same normaliser, lease, classifier and journal row as a chat request.

        `role_or_model` is a model id the registry holds, or a role name found in `roles`, whose
        candidates are tried in order. A plan row is refused: only the CLI holds that sign-in.
        `session` names the journal row's session and the lease's affinity, so a run's calls
        land together; `complete` alone writes a `router` journal.
        """
        return await self._on_loop(
            self._complete(
                role_or_model,
                messages,
                schema=schema,
                session=session,
                system=system,
                max_tokens=max_tokens,
                roles=roles,
            )
        )

    async def _complete(
        self,
        role_or_model: str,
        messages: Sequence[Mapping[str, object]],
        *,
        schema: Mapping[str, object] | None,
        session: str | None,
        system: str,
        max_tokens: int,
        roles: Mapping[str, Sequence[str]] | None,
    ) -> complete.Completion:
        """The candidates in order, the first that answers wins. A model the registry does not
        hold, a plan row and a closed lane are named and the next candidate is tried. A refusal
        that another account could survive (a 429, a 402, a refused key) rotates to the next
        account of the same row first, because no CLI retries this request."""
        ask = complete.Ask(messages, system, max_tokens, schema)
        candidates = list(roles.get(role_or_model, ())) if roles else []
        refusals: list[str] = []
        for name in candidates or [role_or_model]:
            row = self._registry_row(name)
            if row is None:
                refusals.append(f"{name!r} is not a model row the registry holds")
                continue
            try:
                profile = self.profiles().get(row.provider)
            except ProfileError as error:
                refusals.append(str(error))
                continue
            if isinstance(profile, ClaudePlan):
                refusals.append(complete.plan_refusal(row.provider))
                continue
            affinity = f"{session}:{row.provider}" if session else None
            for _attempt in range(max(3, len(self.accounts().accounts))):
                try:
                    lease = self.accounts().lease(
                        provider=row.provider, model=row.native, affinity=affinity
                    )
                except NoAccount as error:
                    refusals.append(str(error))
                    break
                served = await self._complete_on(profile, row, lease, ask, session)
                if isinstance(served, complete.Completion):
                    return served
                refusals.append(served.reason)
                if not served.rotate:
                    break
        raise complete.Refused(
            "; ".join(refusals) or f"complete has no candidate for {role_or_model!r}"
        )

    async def _complete_on(
        self,
        profile: KeyProvider | GptPlan,
        row: ModelRow,
        lease: Lease,
        ask: complete.Ask,
        session: str | None,
    ) -> complete.Completion | _RefusedCandidate:
        """One candidate's request. A refusal is a sentence for the caller, with the lease
        already settled so the pool has cooled or released the account."""
        started = time.perf_counter()
        journal = SessionId(session or ROUTER_SESSION)
        headers: dict[str, str]
        if isinstance(profile, KeyProvider):
            credential = lease.account.credential or profile.credential
            try:
                key = await asyncio.to_thread(self.secrets, credential)
            except Exception as error:
                self.accounts().release(lease)
                return _RefusedCandidate(_keyring_refusal(credential, error), rotate=True)
            headers = swap_auth(
                {"content-type": "application/json"}, key, profile.quirks.wire.auth_header
            )
            del key
            base = profile.base_url
        else:
            sign_in = self.gpt.route.session if self.gpt is not None else self.siwc
            if sign_in is None:
                self.accounts().release(lease)
                return _RefusedCandidate(
                    "the GPT lane is closed: no ChatGPT sign-in is loaded; type /login chatgpt",
                    rotate=False,
                )
            try:
                api_key = await sign_in.access_token()
            except SignInError as error:
                self.accounts().release(lease)
                return _RefusedCandidate(f"ChatGPT sign-in: {error}", rotate=True)
            headers = {
                "authorization": f"Bearer {api_key}",
                "content-type": "application/json",
                "accept": "text/event-stream",
            }
            del api_key
            base = sign_in.api
        if row.wire == "anthropic":
            url, body = f"{base}{MESSAGES}", complete.anthropic_request(row, ask, row.native)
        elif row.wire == "openai_chat":
            url, body = f"{base}{CHAT}", complete.chat_request(row, ask, row.native)
        else:
            url, body = f"{base}/responses", complete.responses_request(row, ask, row.native)
        if self._client is None:
            raise RuntimeError("the relay is not started")
        request = self._client.build_request(
            "POST",
            url,
            headers={**headers, "accept": headers.get("accept", "application/json")},
            content=body,
        )
        try:
            response = await self._client.send(request, stream=True)
        except httpx.HTTPError as error:
            await self._settle_now(lease, classify(502, {}), journal)
            return _RefusedCandidate(
                f"{row.qmx_id}: the provider did not answer ({type(error).__name__})", rotate=True
            )
        try:
            if not response.is_success:
                data = await response.aread()
                found = classify(response.status_code, data, dict(response.headers))
                await self._settle_now(lease, found, journal)
                return _RefusedCandidate(
                    f"{row.qmx_id}: {found.kind}: {found.message[:200]}",
                    rotate=found.kind != "content",
                )
            if row.wire == "anthropic":
                payload = _json(await response.aread())
                answer = complete.anthropic_answer(
                    cast("dict[str, Any]", payload) if isinstance(payload, dict) else {}
                )
            else:
                answer = complete.streamed_answer(
                    [line async for line in response.aiter_lines()], row, row.native
                )
        finally:
            with contextlib.suppress(Exception):
                await response.aclose()
        notice = self.accounts().settle(lease, None)
        if notice is not None:
            await self._alert(journal, notice.text)
        if not answer.text.strip():
            # A reply with no text block is not an answer: the caller gets one more ask, which
            # the request shape above makes rare.
            return _RefusedCandidate(f"{row.qmx_id}: the provider answered with no text", True)
        text, data = complete.answer_text(answer, ask)
        ms = round((time.perf_counter() - started) * 1000)
        await self.record_usage(
            RelayUsage(
                session_id=journal,
                profile=profile.name,
                path=COMPLETE_PATH,
                status=200,
                model=answer.model or row.native,
                input_tokens=int(answer.usage.get("input_tokens", 0)),
                output_tokens=int(answer.usage.get("output_tokens", 0)),
                cache_read_tokens=int(answer.usage.get("cache_read_input_tokens", 0)),
                account=lease.account.id,
            )
        )
        return complete.Completion(
            text=text,
            qmx_id=row.qmx_id,
            model=answer.model or row.native,
            account=lease.account.id,
            usage=answer.usage,
            data=data,
            ms=ms,
        )

    def _complete_refusal(self, name: str) -> str | None:
        """Why `complete` cannot serve this model id, or None when it can."""
        row = self._registry_row(name)
        if row is None:
            return f"{name!r} is not a model row the registry holds"
        try:
            profile = self.profiles().get(row.provider)
        except ProfileError as error:
            return str(error)
        if isinstance(profile, ClaudePlan):
            return complete.plan_refusal(row.provider)
        return None


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


def _account_specs(profiles: Profiles) -> list[AccountSpec]:
    """One account per profile: its own credential on a key row, its one sign-in home on the GPT
    row, and the plan. A host that sets extra accounts on a provider passes its own pool."""
    found: list[AccountSpec] = []
    for name, profile in profiles.by_name.items():
        match profile:
            case KeyProvider(credential=credential):
                found.append(AccountSpec(str(name), name, "key", credential=credential))
            case GptPlan():
                found.append(AccountSpec(str(name), name, "gpt"))
            case ClaudePlan():
                found.append(AccountSpec(str(name), name, "plan"))
    return found


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
