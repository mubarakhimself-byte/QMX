"""The model relay behind /zone/model/{profile}.

The CLI in the zone sends Anthropic Messages here with the zone credential.
The relay swaps in the real provider credential from the operator keyring
and forwards the bytes unchanged. Provider keys and the ChatGPT token never
enter the zone.

Plan traffic never comes here. A ClaudePlan thread has the Direct route, so
its CLI talks to Anthropic with its own login and no QMX process sees it.

Invariants:
- `ViaDoor` env always sets ANTHROPIC_AUTH_TOKEN with ANTHROPIC_BASE_URL (see
  qma_zone.runner.cli_env), so the plan login is never sent here. If an
  Authorization header is not the zone credential, the request is refused
  before any logging.
- The family guard runs on every request body's `model` field, operator-side.
  Claude and GPT model names never reach a key upstream (R4).
- Pass-through keeps `anthropic-beta`, `cache_control`, system array order,
  SSE pings and streaming, and forwards rate-limit response headers.
- Usage for key providers is measured here from the response, so it is
  authoritative, unlike plan usage reported by the zone.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from qma_harness.model import ChatGptPlan, KeyProvider, ProfileId, ProviderProfile


@dataclass(frozen=True)
class PassThrough:
    profile: KeyProvider


@dataclass(frozen=True)
class Translate:
    profile: ChatGptPlan


Upstream = PassThrough | Translate


def upstream_for(profile: ProviderProfile) -> Upstream:
    """Pure. KeyProvider -> PassThrough, ChatGptPlan -> Translate. A ClaudePlan
    has no upstream here; the relay answers 404 for it."""
    raise NotImplementedError


def guard_model(profile: KeyProvider | ChatGptPlan, model: str) -> str | None:
    """Pure. Returns a refusal reason, or None if the model is allowed.
    KeyProvider: the model must parse as KeyModelName and be one of the
    profile's tier names. ChatGptPlan: the model must be in profile.models."""
    raise NotImplementedError


def swap_auth(headers: dict[str, str], provider_key: str) -> dict[str, str]:
    """Pure. Drop Authorization and x-api-key from the zone request, set the
    provider's bearer, drop hop-by-hop headers. Everything else is kept."""
    raise NotImplementedError


@dataclass(frozen=True)
class RelayUsage:
    profile: ProfileId
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int


class Relay:
    def __init__(self, profiles: dict[ProfileId, ProviderProfile], secrets: Any,
                 translator: Any) -> None:
        raise NotImplementedError

    async def handle(self, profile: ProfileId, headers: dict[str, str],
                     body: bytes) -> AsyncIterator[bytes]:
        """Guard the model, then stream: PassThrough forwards to
        `<base_url>/v1/messages` (and count_tokens) with swap_auth; Translate
        hands the parsed request to the GPT translator. Tees usage events to
        the Harness."""
        raise NotImplementedError
        yield  # pragma: no cover
