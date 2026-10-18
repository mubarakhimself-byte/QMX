"""GPT through the operator's ChatGPT sign-in: SIWC session plus the
Anthropic-to-Responses translator. Operator side only.

Lives behind the relay, so it serves only requests carrying the zone
credential and naming one of the ChatGptPlan profile's models. It is not a
general local OpenAI endpoint (SIWC terms: no general-purpose API access).

Invariants:
- QMA's own SIWC registration: client_id=dynamic_agent_client,
  agent_name_hint="QMA", a persisted ext_agent_host_id. Never the Codex login.
- Upstream is https://api.openai.com/v1/responses, never chatgpt.com/backend-api.
- Every request has store=false and stream=true, no system-role items, and
  none of the barred fields (max_output_tokens, temperature, top_p, metadata,
  user, truncation and the rest of the documented list).
- The refresh token sits in the operator keyring at qmx/chatgpt. The access
  token lives in memory and is refreshed before its hour runs out.
- Nothing here runs until the probe ladder P0..P7 has passed and is recorded
  on the profile.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from qma_harness.model import GptProbe, SecretRef


class SiwcSession:
    """PKCE sign-in on a 127.0.0.1 callback, token storage and refresh."""

    def __init__(self, token_ref: SecretRef, secrets: Any) -> None:
        raise NotImplementedError

    async def sign_in(self) -> AsyncIterator[str]:
        """Yields the authorize URL for the console to open. Stores the refresh
        token on success and checks the granted scopes include
        chatgpt.tokens.use.direct."""
        raise NotImplementedError
        yield  # pragma: no cover

    async def access_token(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class ResponsesRequest:
    model: str
    instructions: str
    input: list[dict[str, Any]]
    tools: list[dict[str, Any]]  # function tools wrapped in one namespace tool "qma"
    include: list[str]  # ["reasoning.encrypted_content"] only if P4 passed


def to_responses(anthropic_request: dict[str, Any], reasoning_replay: bool) -> ResponsesRequest:
    """Pure. system blocks -> instructions (attribution block dropped);
    messages -> input items with tool_use -> function_call and tool_result ->
    function_call_output; tools -> namespace "qma"; thinking blocks carrying a
    QMA reasoning blob -> reasoning items when reasoning_replay is on; every
    barred field dropped."""
    raise NotImplementedError


async def to_anthropic_stream(events: AsyncIterator[dict[str, Any]]) -> AsyncIterator[bytes]:
    """Pure stream transform. Responses SSE -> Anthropic SSE (message_start,
    content_block_*, message_delta, message_stop, pings). Unwraps the
    namespace on function calls. Only response.completed ends a message
    successfully; response.failed and subscription_sharing_* codes become an
    Anthropic error event with the code in the message."""
    raise NotImplementedError
    yield  # pragma: no cover


ProbeStep = Literal["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]


async def run_probe_ladder(session: SiwcSession, zone_cli_check: Any) -> GptProbe:
    """02b section D, in order, stopping at the first failure. P6 and P7 run
    the zone CLI and the zone SDK through the relay. The result is written to
    the profile; ChatGptPlan.usable reads it."""
    raise NotImplementedError
