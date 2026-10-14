"""The loopback relay for NON-plan traffic: key providers and the GPT lane.

A key or GPT chat's CLI gets `ANTHROPIC_BASE_URL` = this relay and
`ANTHROPIC_AUTH_TOKEN` = its grant's per-launch secret. The relay checks the secret, stops
any body that carries a Claude token, runs the family guard on the requested and the served
model, swaps in the real key from the OS keyring, applies the provider's wire quirks and
forwards the stream.

What it is worth, stated plainly (interrogate A25, B14). It is the one structural stop
between an agent and a third party for the plan token: the egress stop below. Everything
else it gives is correctness and accounting: wire quirks, authoritative usage, the family
guard, one home for the GPT lane, and keys that never sit in a CLI env or a transcript by
accident. It is not a key boundary against agent Bash, which can read `qmx/*` keyring
entries as the same OS user; the usage page lists those entries.

Plan traffic never comes here. A plan chat's CLI has no base URL and talks to Anthropic with
its own login, so no QMX process is in the plan token's path (02b A, "clearly barred":
relaying the token; 01 section 7 requirement 1). `Relay.grant` accepts only
`KeyProvider | GptPlan`. A relayed CLI runs in the relayed home, which holds no login, and
its auth token outranks `/login` (02a section 11), so it has no plan login to send.

Invariants:
- Binds 127.0.0.1 on an ephemeral port, never 0.0.0.0. Its own listener inside the
  qmx-control process, not under `BearerGate`.
- A request whose bearer (Authorization or x-api-key) is not a live grant gets 401 before
  the body is read and before anything is logged. Only a counter moves.
- Egress stop: a body containing `SECRET_PREFIX` gets 400 naming the rule and is never
  forwarded or logged. Only a counter moves. Both lanes.
- Header values are never logged. The access record is grant session, profile, model,
  status and usage.
- Family guard on the way in: `profiles.resolve_model(profile, body.model)` must accept it.
  On the way out: `message_start.message.model` is checked with the same function; a
  barred served family aborts the stream and moves a counter (R4).
- Forwarded bytes are unchanged except the auth swap and the profile's declared
  `WireQuirks`. `anthropic-beta`, `cache_control`, system order, SSE pings and the
  rate-limit response headers pass through (02b C item 5).
- Usage is read from the stream (key lane: `message_start`, `message_delta`; GPT lane: the
  translator's count) and written as one `model_call` journal event per upstream request.
  For relayed chats this is the only usage source; `chat.py` does not also journal
  `ResultMessage` usage for them, so `RunIndex` never counts a request twice.

Paths are matched on the parsed path, ignoring the query string, which is forwarded as sent
(the CLI calls `/v1/messages?beta=true`): `POST /v1/messages` and
`POST /v1/messages/count_tokens` (key lane: forwarded; GPT lane: local estimate). Anything
else is 404.

Later seam (U10, not built): the same listener can serve the `qmx` tools as an HTTP MCP
endpoint behind the same grant, so a CLI under another OS account reaches QMX tools and
providers without any caller of `Harness` changing.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, NewType

from qma.harness.profiles import GptPlan, KeyProvider, ProfileName

if TYPE_CHECKING:
    from qma.gpt.probe import ProbePassed, ProbeRun
    from qma.gpt.siwc import SiwcSession
    from qma.harness.home import SessionId
    from qma.harness.launch import SecretLookup, TestMode
    from qma.harness.profiles import Profiles

SECRET_PREFIX: Final = b"sk-ant-"
"""The prefix every Claude credential carries (`sk-ant-oat`, `sk-ant-ort`, `sk-ant-api`).
A body that contains it never leaves this process."""

GrantSecret = NewType("GrantSecret", str)
"""256 random bits, minted per CLI launch. Lives in relay memory and in one CLI's env. Not a
provider key. Any process under the same OS user can read another process's env, so this
is a speed bump against a neighbouring chat, not a boundary (A27, noted)."""


@dataclass(frozen=True)
class RelayGrant:
    """What one relayed CLI launch needs: where the relay is and its bearer.

    Minted only by `Relay.grant` or `Relay.probe_grant`. Revoked when the chat's CLI
    disconnects (close, reap, relaunch), so a secret left in an old transcript opens nothing.
    """

    base_url: str
    """`http://127.0.0.1:<port>`. The CLI appends `/v1/messages`."""
    secret: GrantSecret
    session_id: SessionId
    profile: ProfileName


@dataclass(frozen=True)
class GptLane:
    """Proof that the GPT lane is open for the current translator version.

    Only `Relay.open_gpt_lane` returns one, and it needs a `ProbePassed`. `Relay.grant`
    refuses a `GptPlan` while no lane is open. The pass is a correctness gate (has this
    translator been shown to work), not a security gate.
    """

    translator_version: str
    reasoning_replay: bool
    tools_shape: str


class GrantRefused(RuntimeError):
    """`grant` was asked for something the relay will not serve: a GPT grant with the lane
    closed, a GPT grant for an unattended chat without stored background consent, a
    provider row that no longer validates, or a missing keyring entry. The chat shows
    `needs_you`."""


@dataclass(frozen=True)
class RelayUsage:
    """One upstream response's usage. Becomes a `model_call` journal event for the grant's
    session. Key lane: read from the provider's stream. GPT lane: counted by the translator."""

    session_id: SessionId
    profile: ProfileName
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int


type UsageSink = Callable[[RelayUsage], Awaitable[None]]


class Relay:
    """One per qmx-control process. Owns the grant table and is the only run-time reader
    of provider keys. Everything runs on qmx-control's event loop, so the grant table has
    one writer and no lock."""

    @classmethod
    async def start(cls, *, secrets: SecretLookup, usage: UsageSink, profiles: Callable[[], Profiles], test: TestMode) -> Relay:
        """Bind 127.0.0.1:0. No grants, GPT lane closed. `profiles` re-reads and re-parses
        settings.toml [providers] on each call, so a grant always uses the row as it is now."""
        raise NotImplementedError

    def grant(self, session_id: SessionId, profile: ProfileName, *, unattended: bool) -> RelayGrant:
        """Mint a fresh secret bound to (session_id, profile).

        Re-parses the provider row first (`profiles()`), refusing a row that no longer
        validates. KeyProvider: checks the keyring entry exists (fail closed, value not kept
        here). GptPlan: raises `GrantRefused` unless a `GptLane` is open, and, when
        `unattended`, unless the SIWC session holds background consent (SIWC terms, 02b D
        item 9). A second grant for the same session revokes the first (a relaunch), so a
        session never holds two live secrets.
        """
        raise NotImplementedError

    def probe_grant(self, run: ProbeRun) -> RelayGrant:
        """A single-use grant for probes P6 and P7 while the GPT lane is still closed.
        Bound to one `ProbeRun` (minted only by `qma.gpt.probe`), valid for that run's CLI
        process only, revoked when the run ends. The only way GPT traffic flows before a
        `ProbePassed` exists."""
        raise NotImplementedError

    def revoke(self, session_id: SessionId) -> None:
        """Drop the session's grant. Idempotent."""
        raise NotImplementedError

    async def open_gpt_lane(self, passed: ProbePassed, session: SiwcSession, allowed_models: frozenset[str]) -> GptLane:
        """The only way to open the GPT lane. The pass is keyed to `translate.py`'s version
        hash, so a changed translator reads as unprobed and the lane stays closed."""
        raise NotImplementedError

    async def close_gpt_lane(self) -> None:
        """Revokes every GPT grant. Idempotent."""
        raise NotImplementedError

    async def handle(self, path: str, query: str, headers: Mapping[str, str], body: bytes) -> AsyncIterator[bytes]:
        """The request pipeline, each step owning one decision:
        bearer -> grant (401 if none, nothing logged) -> egress stop (400 if `SECRET_PREFIX`
        is in `body`, unless the test switch turned it off) -> parse `model` ->
        `guard_model` (400 naming the rule) -> key lane: `swap_auth` + `apply_wire_quirks`
        + stream to `<base_url><path>?<query>`, checking the served model and teeing
        `RelayUsage`; GPT lane: `qma.gpt.translate`, teeing its count.
        """
        raise NotImplementedError
        yield  # pragma: no cover

    async def close(self) -> None:
        """Stop listening, revoke every grant. Idempotent."""
        raise NotImplementedError


def guard_model(profile: KeyProvider | GptPlan, model: str) -> str | None:
    """Pure. A refusal reason, or None. Delegates to `profiles.resolve_model`, the same
    function `quote` uses for `ChatConfig.model`."""
    raise NotImplementedError


def swap_auth(headers: Mapping[str, str], provider_key: str, style: str) -> dict[str, str]:
    """Pure. Drop the CLI's Authorization and x-api-key and the hop-by-hop headers, set the
    provider's key in the header `style` names (`WireQuirks.auth_header`). Everything else
    is kept as sent."""
    raise NotImplementedError


def apply_wire_quirks(profile: KeyProvider, body: bytes) -> bytes:
    """Pure. Returns `body` unchanged when the profile declares no body quirks, so the
    common path never re-serializes. Otherwise strips `strip_fields` and applies
    `cache_markers`."""
    raise NotImplementedError
