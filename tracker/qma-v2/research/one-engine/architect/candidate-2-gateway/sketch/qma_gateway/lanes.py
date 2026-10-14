"""The three lanes and the per-route request adapter.

    PlanRoute -> plan_relay()   verbatim bytes, sealed credential, constant host
    KeyRoute  -> key_call()     adapted body, provider key from the OS keyring
    GptRoute  -> translator.gpt_call()

The plan lane is deliberately dumb. It does not parse, rewrite or re-serialize the
body, it forwards `anthropic-beta` verbatim (it carries the OAuth capability the
upstream requires, 02b C item 3), it does not buffer the stream, and it forwards
every response header (including anthropic-ratelimit-unified-*) back to the CLI.
That is what Anthropic's gateway protocol asks of a router (02b C item 5).

The key lane is where QMX's provider knowledge lives: quirks, cache marker
hoisting, forced thinking, model id rewrite, and thinking-signature provenance.
These are pure functions of (route, request), testable without a network.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Final

from qma_gateway.contract import CredentialRef, GptRoute, KeyRoute, PlanRoute, Route
from qma_gateway.sealed import PlanUpstreamKey, Sealed

PLAN_UPSTREAM: Final[str] = "https://api.anthropic.com"
"""A constant, not a setting. No code path builds a plan request to any other host."""

_PLAN_KEY: Final[PlanUpstreamKey] = PlanUpstreamKey()
"""The only unseal capability. Never leaves this module."""


@dataclass(frozen=True, slots=True)
class UpstreamResponse:
    """What every lane returns to the server: status, headers to send to the CLI, and
    the body as raw chunks. The server tees the chunks into the meter and wire gate."""

    status: int
    headers: tuple[tuple[bytes, bytes], ...]
    chunks: AsyncIterator[bytes]


# ------------------------------------------------------------------ plan lane


async def plan_relay(
    route: PlanRoute,
    path: str,
    credential: Sealed | None,
    forward: tuple[tuple[bytes, bytes], ...],
    body: bytes,
) -> UpstreamResponse:
    """Forward to PLAN_UPSTREAM + path.

    # TODO pseudocode
    # if credential is None: return 401 "not signed in: run /login in the QMX console"
    # headers = list(forward) + [(b"accept-encoding", b"identity")]
    # credential.forward_into(_PLAN_KEY, headers)     # the one unseal in the codebase
    # open streaming POST with httpx, no retries here (the CLI retries)
    # return status, all response headers, aiter_raw() chunks
    """
    raise NotImplementedError


# ------------------------------------------------------------------- key lane


@dataclass(frozen=True, slots=True)
class AnthropicRequest:
    """A parsed Messages request, used only on key and GPT lanes. The plan lane never
    builds one, so it can never re-serialize a Claude request by mistake."""

    model: str
    system: list[Mapping[str, object]]
    messages: list[Mapping[str, object]]
    tools: list[Mapping[str, object]]
    thinking: Mapping[str, object] | None
    stream: bool
    rest: Mapping[str, object]  # every other top-level field, untouched unless a quirk strips it

    @staticmethod
    def parse(body: bytes) -> AnthropicRequest:
        raise NotImplementedError

    def dump(self) -> bytes:
        raise NotImplementedError


def adapt_for_key(route: KeyRoute, request: AnthropicRequest) -> AnthropicRequest:
    """Pure. Everything QMX knows about one key provider's dialect.

    # TODO pseudocode
    # model -> route.upstream
    # drop fields in route.quirks.strip_fields
    # if not route.caps.server_tools: drop server tools (web_search_*) from tools
    # route.caps.thinking is FORCED_ON and request.thinking disabled -> enable with a budget
    # route.caps.cache_markers:
    #     TOP_LEVEL_ONLY -> remove block markers, set one top-level cache_control
    #     AUTOMATIC      -> remove markers
    # messages = provenance.for_upstream(messages, own=route.provider)
    """
    raise NotImplementedError


def adapt_headers_for_key(route: KeyRoute, forward: tuple[tuple[bytes, bytes], ...]) -> tuple[tuple[bytes, bytes], ...]:
    """Pure. Drops anthropic-beta when the route strips it. Never adds a credential;
    `key_call` adds the provider key last, from the keyring."""
    raise NotImplementedError


async def key_call(
    route: KeyRoute,
    path: str,
    credential: Sealed | None,
    forward: tuple[tuple[bytes, bytes], ...],
    body: bytes,
    keys: ProviderKeys,
) -> UpstreamResponse:
    """`credential.discard()` first, unread. Then adapt, add
    `Authorization: Bearer <provider key>`, stream. Response chunks pass through
    `provenance.tag_stream` so thinking signatures from this provider are tagged
    `qmx:<provider>:` before the CLI stores them."""
    raise NotImplementedError


class ProviderKeys:
    """Reads provider keys from the OS keyring by CredentialRef, caches them in
    memory for the life of the process. Read-only on the keyring. Backends: Windows
    Credential Manager, macOS Keychain, Linux Secret Service (CO-10)."""

    def get(self, ref: CredentialRef) -> str:
        raise NotImplementedError


# ------------------------------------------------- thinking-signature provenance


class provenance:
    """Stateless provider provenance for thinking blocks, so a mid-chat model switch
    across providers does not send one provider's signatures to another.

    Responses from key and GPT lanes have each thinking signature rewritten to
    `qmx:<lane-or-provider>:<original>`. Plan responses are never touched, so a bare
    signature means Anthropic. On every outbound request:
      - to the plan lane: thinking blocks whose signature starts with `qmx:` are
        dropped. This is the only body edit on the plan lane, it only ever happens
        after a cross-provider switch, and that switch already re-reads the whole
        prompt uncached (02a section 8). It is skipped entirely (bytes forwarded
        verbatim) when the body contains no `qmx:` signature, which a byte search
        decides without parsing.
      - to provider P: blocks tagged `qmx:P:` are untagged, all others dropped.
    """

    @staticmethod
    def for_upstream(messages: list[Mapping[str, object]], own: str) -> list[Mapping[str, object]]:
        raise NotImplementedError

    @staticmethod
    def strip_foreign_for_plan(body: bytes) -> bytes:
        raise NotImplementedError

    @staticmethod
    async def tag_stream(chunks: AsyncIterator[bytes], own: str) -> AsyncIterator[bytes]:
        raise NotImplementedError


# ------------------------------------------------------------------- dispatch


async def dispatch(
    route: Route,
    path: str,
    credential: Sealed | None,
    forward: tuple[tuple[bytes, bytes], ...],
    body: bytes,
    keys: ProviderKeys,
) -> UpstreamResponse:
    """Exhaustive match on the route variant. A new lane fails type checking here
    until it is handled."""
    match route:
        case PlanRoute():
            return await plan_relay(route, path, credential, forward, body)
        case KeyRoute():
            return await key_call(route, path, credential, forward, body, keys)
        case GptRoute():
            from qma_gateway.translator import gpt_call

            if credential is not None:
                credential.discard()
            return await gpt_call(route, path, forward, body)
