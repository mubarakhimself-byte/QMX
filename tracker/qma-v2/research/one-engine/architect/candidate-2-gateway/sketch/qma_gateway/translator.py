"""The GPT lane: Anthropic Messages in, OpenAI Responses out, on the operator's
ChatGPT plan through Sign in with ChatGPT (SIWC).

Why it lives in the gateway and not as its own server: the SIWC terms forbid
"general-purpose API access for other tools" (02b D item 9). Inside the gateway,
a GPT request is only reachable with a live QMX lease whose allowed set names a
QMX GPT model id. There is no separate OpenAI-compatible or Anthropic-compatible
port that another tool could point at.

Rules this module implements (02b D items 1 to 6):
- POST https://api.openai.com/v1/responses only, never chatgpt.com/backend-api.
- store=false, stream=true, full history every call, no previous_response_id.
- system blocks -> `instructions`; no system-role items.
- Strip max_tokens, temperature, top_p, top_k, metadata, stop_sequences, and every
  field on the unsupported list. Never map max_tokens to max_output_tokens.
- Tools wrapped in one namespace tool `qma` (or plain, per the ProbeReceipt).
- tool_use / tool_result <-> function_call / function_call_output, ids preserved.
- Reasoning carry-over only if the receipt says P4 passed: include
  reasoning.encrypted_content, carried in a thinking block whose signature is
  `qmx:gpt:<blob>` (provenance tagging, lanes.provenance).
- Only `response.completed` is success. `response.failed` mid-stream becomes an
  Anthropic error event.
- QMA's own registration: client_id=dynamic_agent_client, agent_name_hint="QMA",
  persisted ext_agent_host_id. Never the Codex login (impersonation).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from datetime import datetime

from qma_gateway.contract import GptRoute
from qma_gateway.lanes import AnthropicRequest, UpstreamResponse


@dataclass(frozen=True, slots=True)
class ResponsesRequest:
    model: str
    instructions: str
    input: list[Mapping[str, object]]
    tools: list[Mapping[str, object]]
    include: tuple[str, ...]
    # store=False and stream=True are not fields: they are always written by `dump`.

    def dump(self) -> bytes:
        raise NotImplementedError


def to_responses(route: GptRoute, request: AnthropicRequest) -> ResponsesRequest:
    """Pure. The whole request mapping. Unit-tested against recorded CLI requests."""
    raise NotImplementedError


class AnthropicStreamWriter:
    """Pure state machine: Responses SSE events in, Anthropic SSE bytes out.

    Emits message_start, content_block_start/delta/stop for text, thinking and
    tool_use, ping every 10 s of upstream silence, message_delta with usage and
    stop_reason, message_stop. Unwraps namespaced function names back to the tool
    names the CLI sent.
    """

    def feed(self, event: Mapping[str, object]) -> list[bytes]:
        raise NotImplementedError

    def finish(self) -> list[bytes]:
        raise NotImplementedError


ERROR_MAP: Mapping[str, tuple[int, str]] = {
    # SIWC error code -> (HTTP status to the CLI, Anthropic error type)
    # Usage limit is not retryable within minutes, so it is not a 429 the CLI would
    # retry ten times. Live check L13 confirms the CLI surfaces it once.
    "subscription_sharing_usage_limit_exceeded": (403, "permission_error"),
    "subscription_sharing_unsupported_capability": (400, "invalid_request_error"),
    "subscription_sharing_user_not_eligible": (403, "permission_error"),
    "subscription_sharing_route_not_supported": (403, "permission_error"),
}


class SiwcTokens:
    """The ChatGPT access and refresh tokens. The gateway is the only reader and the
    only writer of the keyring entry `qmx/chatgpt` (per
    separate-before-serializing-shared-state). Access tokens last one hour; refresh
    is single-flight so concurrent requests do not race the rotating refresh token.
    """

    async def access_token(self) -> str:
        raise NotImplementedError

    def begin_sign_in(self) -> str:
        """Return the authorize URL (PKCE S256, loopback redirect to this gateway's
        /auth/chatgpt/callback). The console opens it in the operator's browser."""
        raise NotImplementedError

    async def complete_sign_in(self, code: str, state: str) -> datetime:
        """Exchange, verify the granted scopes contain chatgpt.tokens.use.direct,
        store to the keyring. Returns the expiry."""
        raise NotImplementedError


async def gpt_call(
    route: GptRoute,
    path: str,
    forward: tuple[tuple[bytes, bytes], ...],
    body: bytes,
) -> UpstreamResponse:
    """count_tokens -> 404 (the CLI falls back to its estimate).
    messages -> parse, to_responses, POST with the SIWC bearer, translate the stream."""
    raise NotImplementedError
