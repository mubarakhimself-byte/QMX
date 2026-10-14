"""The loopback relay for NON-plan traffic: key providers and the GPT lane.

A key or GPT chat's CLI gets `ANTHROPIC_BASE_URL` = this relay and
`ANTHROPIC_AUTH_TOKEN` = its grant's per-launch secret. The relay checks the secret,
runs the family guard on each request's `model`, swaps in the real key from the OS
keyring, applies the provider's wire quirks and forwards the stream. Provider keys never
sit in a CLI env, a CLI's Bash or a transcript.

Plan traffic never comes here. A Claude-plan chat's CLI has no base URL and talks to
Anthropic with its own login, so no QMX process is in the plan token's path (02b A,
"clearly barred": relaying the token; 01 section 7 requirement 1). That is structural:
`Relay.grant` accepts only `KeyProvider | GptPlan`, so no grant, and therefore no
`RelayedLaunch`, can exist for the plan. The auth token a relayed CLI carries outranks
`/login` (02a section 11), so that CLI never sends the plan login here either.

Invariants:
- Binds 127.0.0.1 on an ephemeral port, never 0.0.0.0. Its own listener inside the
  qmx-control process, not under `BearerGate`.
- A request whose bearer (Authorization or x-api-key) is not a live grant gets 401
  before the body is read and before anything is logged. Only a counter moves.
- Header values are never logged. The access record is grant session, profile, model,
  status and usage.
- The family guard runs on every request body's `model`: the grant's profile must serve
  it, and `FORBIDDEN_ON_KEY` fragments never reach a key upstream (R4). The GPT lane
  accepts only the GPT profile's models, so it is not general-purpose API access
  (SIWC terms, 02b D item 9).
- Forwarded bytes are unchanged except the auth swap and the profile's declared
  `WireQuirks`. `anthropic-beta`, `cache_control`, system order, SSE pings and the
  rate-limit response headers pass through (02b C item 5).
- Usage for key providers is read from the stream (`message_start`, `message_delta`)
  and written as one `model_call` journal event per upstream request, which `RunIndex`
  already sums. So key-provider usage is authoritative, not a client estimate.

Paths: `POST /v1/messages`, `POST /v1/messages/count_tokens` (key lane: forwarded; GPT
lane: local estimate). Anything else is 404.

Later seam (U10, not built): the same listener can serve the `qmx` tools as an HTTP MCP
endpoint behind the same grant, so a CLI under another OS account reaches QMX tools and
providers without any caller of `Harness` changing.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, NewType

from qma.harness.profiles import GptPlan, KeyProvider, ProfileName

if TYPE_CHECKING:
    from qma.gpt.probe import ProbePassed
    from qma.gpt.siwc import SiwcSession
    from qma.harness.home import SessionId
    from qma.harness.launch import SecretLookup

GrantSecret = NewType("GrantSecret", str)
"""256 random bits, minted per CLI launch. Lives in relay memory and in one CLI's env.
It is not a provider key: it reaches only its own profile, only while its chat is live."""


@dataclass(frozen=True)
class RelayGrant:
    """What one relayed CLI launch needs: where the relay is and its bearer.

    Minted only by `Relay.grant`. Revoked when the chat's CLI disconnects (close, reap,
    relaunch), so a secret left in an old transcript opens nothing.
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
    refuses a `GptPlan` while no lane is open, so GPT runs only after probes P0 to P7.
    """

    translator_version: str
    reasoning_replay: bool
    tools_shape: str


class GrantRefused(RuntimeError):
    """`grant` was asked for something the relay will not serve: a GPT grant with the lane
    closed, or a profile whose keyring entry is missing. The chat shows `needs_you`."""


@dataclass(frozen=True)
class KeyUsage:
    """One upstream key-provider response, read from its stream. Becomes a `model_call`
    journal event for the grant's session."""

    session_id: SessionId
    profile: ProfileName
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int


type UsageSink = Callable[[KeyUsage], Awaitable[None]]


class Relay:
    """One per qmx-control process. Owns the grant table and is the only run-time reader
    of provider keys. Everything runs on qmx-control's event loop, so the grant table has
    one writer and no lock."""

    @classmethod
    async def start(cls, *, secrets: SecretLookup, usage: UsageSink) -> Relay:
        """Bind 127.0.0.1:0. No grants, GPT lane closed."""
        raise NotImplementedError

    def grant(self, session_id: SessionId, profile: KeyProvider | GptPlan) -> RelayGrant:
        """Mint a fresh secret bound to (session_id, profile).

        KeyProvider: checks the keyring entry exists (fail closed, value not kept here).
        GptPlan: raises `GrantRefused` unless a `GptLane` is open.
        A second grant for the same session revokes the first (a relaunch), so a session
        never holds two live secrets.
        """
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

    async def handle(self, path: str, headers: Mapping[str, str], body: bytes) -> AsyncIterator[bytes]:
        """The request pipeline, each step owning one decision:
        bearer -> grant (401 if none, nothing logged) -> parse `model` -> `guard_model`
        (400 naming the rule) -> key lane: `swap_auth` + `apply_wire_quirks` + stream to
        `<base_url>/v1/messages`, teeing `KeyUsage`; GPT lane: `qma.gpt.translate`.
        """
        raise NotImplementedError
        yield  # pragma: no cover

    async def close(self) -> None:
        """Stop listening, revoke every grant. Idempotent."""
        raise NotImplementedError


def guard_model(profile: KeyProvider | GptPlan, model: str) -> str | None:
    """Pure. A refusal reason, or None. KeyProvider: `model` must be one of the profile's
    tier models and match no `FORBIDDEN_ON_KEY` fragment on any path segment. GptPlan:
    `model` must be one of the profile's tier models."""
    raise NotImplementedError


def swap_auth(headers: Mapping[str, str], provider_key: str) -> dict[str, str]:
    """Pure. Drop the CLI's Authorization and x-api-key and the hop-by-hop headers, set
    `Authorization: Bearer <provider_key>`. Everything else is kept as sent."""
    raise NotImplementedError


def apply_wire_quirks(profile: KeyProvider, body: bytes) -> bytes:
    """Pure. Returns `body` unchanged when the profile declares no wire quirks, so the
    common path never re-serializes. Otherwise strips `strip_fields` and applies
    `cache_markers`."""
    raise NotImplementedError
