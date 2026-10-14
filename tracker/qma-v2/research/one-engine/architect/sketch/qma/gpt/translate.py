"""Anthropic Messages <-> OpenAI Responses, for the Sign in with ChatGPT route. Pure.

The CLI believes it talks to an Anthropic-compatible host. These functions are the whole
format knowledge; the GPT lane of `qma.harness.relay` is the thin HTTP shell around them. Rules come from 02b D
(SIWC preview limitations) and are tested against recorded fixtures, then live by probes P3
to P7.

Request direction (`to_responses`):
- `store: false`, `stream: true` always.
- `system` blocks -> `instructions` (system-role items are rejected on this route).
- Dropped, never mapped: `max_tokens`, `temperature`, `top_p`, `top_k`, `metadata`,
  `stop_sequences`, `context_management`, cache_control markers, beta-only fields.
- Tools -> one `namespace` tool named "qma" holding function tools (or `additional_tools`
  input items, whichever probe P3 shows the route accepts). Names unwrapped on the way back.
- Full history each call (no `previous_response_id` on this route).
- `tool_use` -> `function_call`, `tool_result` -> `function_call_output`.
- Anthropic `thinking` blocks whose signature carries `qma-r1:<encrypted_content>` ->
  reasoning items replayed with `include: ["reasoning.encrypted_content"]`, only if probe P4
  passed; otherwise thinking blocks are dropped (reasoning carry-over lost, stated in doctor).
- Model must be in the GPT profile's tier map; anything else is refused with 400.

Response direction (`StreamState`): Responses SSE -> Anthropic SSE (`message_start`,
`content_block_*`, `message_delta` with usage and stop_reason, `message_stop`, `ping`
while idle). Only `response.completed` ends a turn successfully (02b D item 5).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Translation:
    body: Mapping[str, object]
    """The `/v1/responses` request body."""
    tool_names: Mapping[str, str]
    """Namespaced name -> original Claude Code tool name, for unwrapping calls."""


class RefusedRequest(ValueError):
    """A request this route must not send (unknown model, unsupported input such as audio).
    Becomes an Anthropic `invalid_request_error`."""


def to_responses(
    anthropic_request: Mapping[str, object],
    *,
    allowed_models: frozenset[str],
    reasoning_replay: bool,
) -> Translation:
    raise NotImplementedError


@dataclass(frozen=True)
class SseEvent:
    event: str
    data: Mapping[str, object]


class StreamState:
    """One response stream's state machine: which content block is open, its index, the
    accumulated tool-call arguments, the usage numbers."""

    def __init__(self, translation: Translation, model: str) -> None:
        raise NotImplementedError

    def feed(self, responses_event: Mapping[str, object]) -> list[SseEvent]:
        raise NotImplementedError

    def idle_ping(self) -> SseEvent:
        raise NotImplementedError

    @property
    def usage(self) -> Mapping[str, int]:
        """Locally counted input and output tokens. The ChatGPT side has no usage API
        (02b F), so this is what the usage page shows for GPT."""
        raise NotImplementedError


type AnthropicErrorType = Literal["invalid_request_error", "rate_limit_error", "permission_error", "api_error"]


def map_error(openai_error: Mapping[str, object]) -> tuple[int, AnthropicErrorType, str]:
    """`subscription_sharing_usage_limit_exceeded` -> 429 rate_limit_error (the GPT profile
    sets a low CLAUDE_CODE_MAX_RETRIES so the CLI does not hammer a plan limit);
    `..._unsupported_capability` -> 400 naming `error.param`; `..._user_not_eligible` and
    `..._route_not_supported` -> 403 permission_error. Never retried onto another billing
    path, matching OpenAI's own rule."""
    raise NotImplementedError
