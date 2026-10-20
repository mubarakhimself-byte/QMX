"""Anthropic Messages <-> OpenAI chat completions, for the in-house chat lane (H12, AD-38). Pure.

The CLI believes it talks to an Anthropic host. These functions are the whole format knowledge
for a registry row whose `wire` is `openai_chat` (OpenCode Go's GLM, Kimi and DeepSeek rows
today); the relay's chat lane is the HTTP shell around them. `model` is always the native id the
registry resolved, never one read back out of the request.

Request direction (`to_chat`). The body is built from scratch, so a field chat completions has no
home for cannot ride along: dropped, never mapped, are `temperature`, `top_p`, `top_k`,
`metadata`, `stop_sequences`, `thinking`, cache markers, every beta-only field, and the
`anthropic-*` and `x-claude-code-*` headers, which the relay does not send on this lane at all.
- `system` blocks and system-role messages fold into one `system` message.
- Text blocks become text; a `tool_use` becomes one `tool_calls` entry; a `tool_result` becomes
  one `tool` message of its own, because chat completions answers each call in its own message.
- A tool name outside the route's 64-character rule gets the same stable wire name the GPT lane
  mints, mapped back on the way out.
- Thinking round-trips only through the translator's own signature. `reasoning_content` from this
  lane becomes a `thinking` block signed `qmx-chat-1:<hash of its text>`; on a later request that
  exact text goes back out as `reasoning_content`. A thinking block signed by anyone else, an
  Anthropic signature included, is dropped, because a signature is a provider's claim about its
  own hidden state: another provider's model would reject it or reason from a state it never had.

Response direction (`StreamState`): chat-completions chunks -> Anthropic SSE (`message_start`,
`content_block_*`, `message_delta` with usage and stop_reason, `message_stop`). `delta.content` is
a text block, `delta.reasoning_content` (some vendors name it `reasoning`) a thinking block, and
`delta.tool_calls[]` a `tool_use` block keyed by the vendor's own call index, so arguments split
across chunks land in one block and an id the vendor repeats is kept. The stream ends at EOF, not
at the chunk carrying `finish_reason`, because `stream_options.include_usage` puts the usage
counts in a trailing chunk after it; `finish` writes the tail once.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final, Literal, cast

from qmx_router.gpt.translate import parse_sse, wire_name

__all__ = [
    "RefusedRequest",
    "SseEvent",
    "StreamState",
    "Translation",
    "map_error",
    "owns_thinking",
    "parse_sse",
    "thinking_signature",
    "to_chat",
    "wire_name",
]

SIGNATURE_PREFIX: Final = "qmx-chat-1:"
"""The translator's own signature prefix. A later version changes it, so a thinking block minted
by this one is dropped rather than replayed to a model whose reasoning format changed."""

type Json = dict[str, Any]
type AnthropicErrorType = Literal[
    "invalid_request_error",
    "authentication_error",
    "permission_error",
    "rate_limit_error",
    "api_error",
]
type BlockKind = Literal["text", "thinking", "tool"]


class RefusedRequest(ValueError):
    """A request this lane must not send, such as a PDF block. Becomes an Anthropic
    `invalid_request_error`."""


@dataclass(frozen=True)
class Translation:
    body: Mapping[str, Any]
    """The `/v1/chat/completions` request body."""
    tool_names: Mapping[str, str]
    """Wire name -> CLI tool name, for every name this request renamed."""


def thinking_signature(thinking: str) -> str:
    """The signature this translator puts on `thinking` when it reads it back off this lane."""
    return SIGNATURE_PREFIX + hashlib.sha256(thinking.encode()).hexdigest()[:32]


def owns_thinking(block: Json) -> bool:
    """True when `block` is a thinking block this translator minted and nothing edited since."""
    thinking, signature = block.get("thinking"), block.get("signature")
    return (
        block.get("type") == "thinking"
        and isinstance(thinking, str)
        and isinstance(signature, str)
        and signature == thinking_signature(thinking)
    )


def to_chat(request: Mapping[str, Any], *, model: str) -> Translation:
    """`model` is the pinned id the relay resolved; the request's own `model` is not read."""
    renamed: dict[str, str] = {}

    def wire(name: str) -> str:
        found = wire_name(name)
        if found != name:
            renamed[found] = name
        return found

    messages = request.get("messages")
    if not isinstance(messages, list):
        raise RefusedRequest("the request has no messages list")
    turns = cast("list[Json]", messages)
    if not any(turn.get("role") != "system" for turn in turns):
        raise RefusedRequest("the request has no messages to send")
    body: Json = {
        "model": model,
        "messages": _chat_messages(_text(request.get("system")), turns, wire),
    }
    body["stream"] = True
    body["stream_options"] = {"include_usage": True}
    max_tokens = request.get("max_tokens")
    if isinstance(max_tokens, int) and not isinstance(max_tokens, bool):
        body["max_tokens"] = max_tokens
    tools = _tools(request.get("tools"), wire)
    if tools:
        body["tools"] = tools
        body["tool_choice"] = _tool_choice(request.get("tool_choice"), wire)
    return Translation(body, renamed)


def _tools(raw: object, wire: Callable[[str], str]) -> list[Json]:
    """The function tools, and no server tool: chat completions has no bridge for one."""
    return [
        {
            "type": "function",
            "function": {
                "name": wire(str(tool["name"])),
                "description": str(tool.get("description", "")),
                "parameters": tool.get("input_schema") or {"type": "object", "properties": {}},
            },
        }
        for tool in cast("list[Json]", raw or [])
        if tool.get("type", "custom") == "custom"
    ]


def _tool_choice(choice: object, wire: Callable[[str], str]) -> object:
    """`auto` unless the request named one, which is chat completions' own default."""
    if not isinstance(choice, dict):
        return "auto"
    table = cast("Json", choice)
    match table.get("type"):
        case "any":
            return "required"
        case "tool":
            return {"type": "function", "function": {"name": wire(str(table.get("name", "")))}}
        case "none":
            return "none"
        case _:
            return "auto"


def _text(value: object) -> str:
    """A string, or the text blocks of a block list joined by blank lines."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        blocks = cast("list[Json]", value)
        return "\n\n".join(str(b["text"]) for b in blocks if b.get("type") == "text")
    return ""


def _chat_messages(system: str, turns: Sequence[Json], wire: Callable[[str], str]) -> list[Json]:
    """One system message first, then the turns: a user turn may split into tool answers and a
    user message, an assistant turn becomes the one assistant message chat completions reads."""
    out: list[Json] = []
    text = "\n\n".join(part for part in [system, *_system_text(turns)] if part)
    if text:
        out.append({"role": "system", "content": text})
    for turn in turns:
        role = turn.get("role")
        if role == "system":
            continue
        if role not in ("user", "assistant"):
            raise RefusedRequest(f"a message with role {role!r} has no chat-completions mapping")
        content = turn.get("content")
        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue
        blocks = cast("list[Json]", content or [])
        if role == "assistant":
            out.append(_assistant(blocks, wire))
        else:
            out.extend(_user(blocks))
    return out


def _system_text(turns: Sequence[Json]) -> list[str]:
    """The CLI puts system-role messages beside the top-level `system` field; both are the one
    system channel chat completions has."""
    return [_text(turn.get("content")) for turn in turns if turn.get("role") == "system"]


def _assistant(blocks: Sequence[Json], wire: Callable[[str], str]) -> Json:
    texts: list[str] = []
    calls: list[Json] = []
    reasoning: list[str] = []
    for block in blocks:
        match block.get("type"):
            case "text":
                texts.append(str(block.get("text", "")))
            case "tool_use":
                calls.append(
                    {
                        "id": str(block["id"]),
                        "type": "function",
                        "function": {
                            "name": wire(str(block["name"])),
                            "arguments": json.dumps(
                                block.get("input") or {}, ensure_ascii=False, separators=(",", ":")
                            ),
                        },
                    }
                )
            case "thinking" if owns_thinking(block):
                reasoning.append(str(block.get("thinking", "")))
            case "thinking" | "redacted_thinking":
                continue
            case other:
                raise RefusedRequest(
                    f"a {other} block in an assistant message has no chat-completions mapping"
                )
    message: Json = {"role": "assistant", "content": "\n\n".join(texts)}
    if calls:
        message["tool_calls"] = calls
    if reasoning:
        message["reasoning_content"] = "\n\n".join(reasoning)
    return message


def _user(blocks: Sequence[Json]) -> list[Json]:
    """The tool answers first, in the order the calls came, then the turn's own text and images:
    chat completions reads a tool message only directly after the assistant message that called
    it."""
    answers: list[Json] = []
    parts: list[Json] = []
    for block in blocks:
        match block.get("type"):
            case "text":
                parts.append({"type": "text", "text": str(block.get("text", ""))})
            case "image":
                parts.append({"type": "image_url", "image_url": {"url": _source_url(block)}})
            case "document":
                parts.append({"type": "text", "text": _document_text(block)})
            case "tool_result":
                answers.append(
                    {
                        "role": "tool",
                        "tool_call_id": str(block["tool_use_id"]),
                        "content": _tool_output(block.get("content")),
                    }
                )
            case "thinking" | "redacted_thinking":
                continue
            case other:
                raise RefusedRequest(
                    f"a {other} block in a user message has no chat-completions mapping"
                )
    out = list(answers)
    if parts:
        text = "\n\n".join(str(part["text"]) for part in parts if part["type"] == "text")
        flat = parts if any(part["type"] != "text" for part in parts) else text
        out.append({"role": "user", "content": flat})
    return out


def _source_url(block: Json) -> str:
    source = cast("Json", block.get("source") or {})
    match source.get("type"):
        case "base64":
            return f"data:{source.get('media_type')};base64,{source.get('data')}"
        case "url":
            return str(source.get("url"))
        case other:
            raise RefusedRequest(f"an image with a {other} source has no chat-completions mapping")


def _document_text(block: Json) -> str:
    """A text document's text. A PDF has no chat-completions mapping, so it is refused rather
    than silently dropped."""
    source = cast("Json", block.get("source") or {})
    if source.get("type") == "text":
        return str(source.get("data", ""))
    raise RefusedRequest("only text documents have a chat-completions mapping")


def _tool_output(content: object) -> str:
    """Text only: a tool result's images are named, not sent."""
    if isinstance(content, str):
        return content
    texts: list[str] = []
    for block in cast("list[Json]", content or []):
        if block.get("type") == "text":
            texts.append(str(block.get("text", "")))
        else:
            texts.append(f"[{block.get('type')} block not sent: tool results carry text only here]")
    return "\n\n".join(texts)


@dataclass(frozen=True)
class SseEvent:
    event: str
    data: Mapping[str, object]

    def encode(self) -> bytes:
        payload = json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
        return f"event: {self.event}\ndata: {payload}\n\n".encode()


def _event(data: Json) -> SseEvent:
    return SseEvent(str(data["type"]), data)


STOP_REASONS: Final[Mapping[str, str]] = {
    "tool_calls": "tool_use",
    "function_call": "tool_use",
    "stop": "end_turn",
    "length": "max_tokens",
    "content_filter": "end_turn",
}


@dataclass
class StreamState:
    """One chat-completions stream's state machine: which block is open and where, the tool calls
    keyed by the vendor's index, the usage counts, and the finished blocks for a plain reply."""

    translation: Translation
    model: str
    served: str | None = None
    error: tuple[int, AnthropicErrorType, str] | None = None
    ended: bool = False
    stop_reason: str | None = None
    _started: bool = False
    _open: BlockKind | None = None
    _open_at: int = -1
    _tools: dict[int, int] = field(default_factory=dict[int, int])
    """The vendor's `tool_calls` index -> the Anthropic block index holding it."""
    _finish: str | None = None
    _id: str = "msg_qma"
    _usage: dict[str, int] = field(
        default_factory=lambda: {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_input_tokens": 0,
        }
    )
    _blocks: list[Json] = field(default_factory=list[Json])

    @property
    def usage(self) -> Mapping[str, int]:
        return dict(self._usage)

    @property
    def started(self) -> bool:
        return self._started

    @property
    def tool_calls(self) -> int:
        return len(self._tools)

    def feed(self, chunk: Mapping[str, Any]) -> list[SseEvent]:
        """One chunk's events. `finish` writes the tail; a chunk never ends the stream."""
        if self.ended:
            return []
        if isinstance(chunk.get("error"), Mapping):
            return self._fail(cast("Json", chunk["error"]))
        if self.served is None and isinstance(chunk.get("model"), str):
            self.served = chunk["model"]
        if isinstance(chunk.get("id"), str) and not self._started:
            self._id = f"msg_{chunk['id']}"
        usage = chunk.get("usage")
        if isinstance(usage, Mapping):
            self._count(cast("Json", usage))
        out = self._start()
        for choice in cast("list[Json]", chunk.get("choices") or []):
            if choice.get("index", 0) != 0:
                continue
            out += self._delta(cast("Json", choice.get("delta") or {}))
            reason = choice.get("finish_reason")
            if isinstance(reason, str):
                self._finish = reason
        return out

    def finish(self) -> list[SseEvent]:
        """The tail: close the open block, then `message_delta` and `message_stop`. A stream that
        ended without a `finish_reason` is an error, not a short answer."""
        if self.ended:
            return []
        if self._finish is None:
            return self._fail({"message": "the chat-completions stream ended mid-answer"})
        self.stop_reason = STOP_REASONS.get(self._finish, "end_turn")
        self.ended = True
        delta = {
            "type": "message_delta",
            "delta": {"stop_reason": self.stop_reason, "stop_sequence": None},
            "usage": self.usage,
        }
        return [*self._close(), _event(delta), _event({"type": "message_stop"})]

    def message(self) -> Json:
        """The finished reply as one Anthropic message, for a request with `stream: false`."""
        return {
            "id": self._id,
            "type": "message",
            "role": "assistant",
            "model": self.served or self.model,
            "content": [_block(block) for block in self._blocks],
            "stop_reason": self.stop_reason,
            "stop_sequence": None,
            "usage": self.usage,
        }

    def _count(self, usage: Json) -> None:
        details = cast("Json", usage.get("prompt_tokens_details") or {})
        self._usage = {
            "input_tokens": _int(usage.get("prompt_tokens")),
            "output_tokens": _int(usage.get("completion_tokens")),
            "cache_read_input_tokens": _int(details.get("cached_tokens")),
        }

    def _delta(self, delta: Json) -> list[SseEvent]:
        out: list[SseEvent] = []
        reasoning = delta.get("reasoning_content")
        if not isinstance(reasoning, str) or not reasoning:
            reasoning = delta.get("reasoning")
        if isinstance(reasoning, str) and reasoning:
            out += self._open_kind("thinking")
            self._blocks[self._open_at]["thinking"] += reasoning
            out.append(
                self._delta_event(self._open_at, {"type": "thinking_delta", "thinking": reasoning})
            )
        content = delta.get("content")
        if isinstance(content, str) and content:
            out += self._open_kind("text")
            self._blocks[self._open_at]["text"] += content
            out.append(self._delta_event(self._open_at, {"type": "text_delta", "text": content}))
        for call in cast("list[Json]", delta.get("tool_calls") or []):
            out += self._tool(call)
        return out

    def _tool(self, call: Json) -> list[SseEvent]:
        index = _int(call.get("index"))
        found = cast("Json", call.get("function") or {})
        at = self._tools.get(index)
        out: list[SseEvent] = []
        if at is None:
            name = str(found.get("name", ""))
            at = len(self._blocks)
            self._tools[index] = at
            out += self._open_block(
                {
                    "type": "tool_use",
                    "id": str(call.get("id") or f"call_qmx_{index}"),
                    "name": self.translation.tool_names.get(name, name),
                    "input": {},
                },
                "tool",
                at,
            )
        arguments = found.get("arguments")
        if isinstance(arguments, str) and arguments:
            self._blocks[at]["arguments"] += arguments
            out.append(
                self._delta_event(at, {"type": "input_json_delta", "partial_json": arguments})
            )
        return out

    def _start(self) -> list[SseEvent]:
        if self._started:
            return []
        self._started = True
        message: Json = {
            "id": self._id,
            "type": "message",
            "role": "assistant",
            "model": self.served or self.model,
            "content": [],
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }
        return [_event({"type": "message_start", "message": message})]

    def _open_kind(self, kind: BlockKind) -> list[SseEvent]:
        """The given block kind, opening one when a different kind is open."""
        if self._open == kind:
            return []
        block: Json = {"type": "text", "text": ""}
        if kind == "thinking":
            block = {"type": "thinking", "thinking": "", "signature": ""}
        return self._open_block(block, kind, len(self._blocks))

    def _open_block(self, block: Json, kind: BlockKind, at: int) -> list[SseEvent]:
        """One block open at a time, as Anthropic's own streams carry them, so the open one is
        closed first."""
        out = self._close()
        self._open, self._open_at = kind, at
        self._blocks.append(dict(block) | ({"arguments": ""} if kind == "tool" else {}))
        start = {"type": "content_block_start", "index": at, "content_block": block}
        return [*out, _event(start)]

    def _delta_event(self, at: int, delta: Json) -> SseEvent:
        return _event({"type": "content_block_delta", "index": at, "delta": delta})

    def _close(self) -> list[SseEvent]:
        """Close the open block. A thinking block takes its signature here, as a
        `signature_delta`, because only now is its whole text known: that signature is what lets
        the next request carry the text back as `reasoning_content`, and what marks the block as
        this translator's own."""
        if self._open is None:
            return []
        at, self._open = self._open_at, None
        out: list[SseEvent] = []
        if self._blocks[at]["type"] == "thinking":
            signature = thinking_signature(str(self._blocks[at]["thinking"]))
            self._blocks[at]["signature"] = signature
            out.append(self._delta_event(at, {"type": "signature_delta", "signature": signature}))
        out.append(_event({"type": "content_block_stop", "index": at}))
        return out

    def _fail(self, error: Json) -> list[SseEvent]:
        self.error = map_error(0, error)
        self.ended = True
        _, kind, text = self.error
        return [_event({"type": "error", "error": {"type": kind, "message": text}})]


def _block(block: Json) -> Json:
    """One finished block as the reply carries it, without the streaming bookkeeping."""
    match block.get("type"):
        case "text":
            return {"type": "text", "text": block["text"]}
        case "thinking":
            return {
                "type": "thinking",
                "thinking": block["thinking"],
                "signature": block.get("signature") or thinking_signature(str(block["thinking"])),
            }
        case _:
            return {
                "type": "tool_use",
                "id": block["id"],
                "name": block["name"],
                "input": _parse_arguments(str(block.get("arguments", ""))),
            }


def _parse_arguments(text: str) -> Json:
    try:
        found = json.loads(text or "{}")
    except ValueError:
        return {}
    return cast("Json", found) if isinstance(found, dict) else {}


def _int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


ERROR_CODES: Final[Mapping[str, tuple[int, AnthropicErrorType]]] = {
    "invalid_api_key": (401, "authentication_error"),
    "insufficient_quota": (429, "rate_limit_error"),
    "context_length_exceeded": (400, "invalid_request_error"),
    "model_not_found": (404, "invalid_request_error"),
}
"""Codes OpenAI-compatible routes share. Anything else maps by HTTP status, `status` 0 meaning an
error inside a 200 stream."""


def map_error(status: int, error: Mapping[str, Any]) -> tuple[int, AnthropicErrorType, str]:
    """The Anthropic status, error type and message for a chat-completions error."""
    code = str(error.get("code") or "")
    message = str(error.get("message") or code or "the chat-completions upstream returned an error")
    if code in ERROR_CODES:
        mapped, kind = ERROR_CODES[code]
        return mapped, kind, message
    if status == 429:
        return 429, "rate_limit_error", message
    if status == 401:
        return 401, "authentication_error", message
    if status == 403:
        return 403, "permission_error", message
    if 400 <= status < 500:
        return 400, "invalid_request_error", message
    return 502, "api_error", message
