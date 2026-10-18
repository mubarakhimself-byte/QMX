"""Anthropic Messages <-> OpenAI Responses, for the Sign in with ChatGPT route. Pure.

The CLI believes it talks to an Anthropic-compatible host. These functions are the whole format
knowledge; the GPT lane of `qma.harness.relay` is the HTTP shell around them. Rules come from
02b section D and HP2's measurements on this route (scripts/probes/qma/FINDINGS.md, HP2).

Request direction (`to_responses`). The body is built from scratch, so a field the route bars
can never ride along from the Anthropic side:
- `store: false`, `stream: true` always. Full history each call, no `previous_response_id`.
- `system` blocks become `instructions`; the route refuses system-role items. The CLI also
  puts system-role messages in `messages` (its environment block, measured with CLI 2.1.299);
  their text joins `instructions` in order, the one system channel this route was probed with.
- Dropped, never mapped: `max_tokens`, `temperature`, `top_p`, `top_k`, `metadata`,
  `stop_sequences`, `thinking`, `context_management`, `output_config`, cache markers and every
  beta-only field. Server tools (a `type` other than `custom`) are dropped too.
- Function tools go in one `namespace` tool named `qma`, with `strict: false` because Claude
  Code's schemas leave optional fields out of `required`. A name the route cannot take (over
  64 characters, or outside `[A-Za-z0-9_-]`) gets a short wire name, mapped back on the way out.
- `tool_use` -> `function_call` in namespace `qma`, `tool_result` -> `function_call_output`.
- `thinking` and `redacted_thinking` blocks are dropped. Reasoning carry-over is off: HP2 got
  no reasoning item back, and a thinking block with an invented signature would break a later
  switch of the chat to the Claude plan.

Response direction (`StreamState`): Responses SSE -> Anthropic SSE (`message_start`,
`content_block_*`, `message_delta` with usage and stop_reason, `message_stop`). Output items are
read from `response.output_item.*` events: this route sends an empty `output` on
`response.completed`. Only `response.completed` ends a turn successfully.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final, Literal, cast

NAMESPACE: Final = "qma"
WIRE_NAME: Final = re.compile(r"[A-Za-z0-9_-]{1,64}")
NOT_ELIGIBLE: Final = "subscription_sharing_user_not_eligible"

type Json = dict[str, Any]
type AnthropicErrorType = Literal[
    "invalid_request_error",
    "authentication_error",
    "permission_error",
    "rate_limit_error",
    "api_error",
]


class RefusedRequest(ValueError):
    """A request this route must not send, such as audio input. Becomes an Anthropic
    `invalid_request_error`."""


@dataclass(frozen=True)
class Translation:
    body: Mapping[str, object]
    """The `/v1/responses` request body."""
    tool_names: Mapping[str, str]
    """Wire name -> Claude Code tool name, for every name this request renamed."""


def wire_name(name: str) -> str:
    """`name` itself when the route takes it, else a stable short name: the legal part cut to
    55 characters, then an 8-character hash of the whole name."""
    if WIRE_NAME.fullmatch(name):
        return name
    legal = re.sub(r"[^A-Za-z0-9_-]", "_", name)[:55]
    return f"{legal}_{hashlib.sha256(name.encode()).hexdigest()[:8]}"


def to_responses(request: Mapping[str, Any], *, model: str) -> Translation:
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
    body: Json = {
        "model": model,
        "input": [
            item
            for message in turns
            if message.get("role") != "system"
            for item in _input_items(message, wire)
        ],
        "store": False,
        "stream": True,
    }
    system = [_text(request.get("system"))]
    system += [_text(m.get("content")) for m in turns if m.get("role") == "system"]
    instructions = "\n\n".join(text for text in system if text)
    if instructions:
        body["instructions"] = instructions
    functions: list[Json] = [
        {
            "type": "function",
            "name": wire(str(tool["name"])),
            "description": str(tool.get("description", "")),
            "parameters": tool.get("input_schema") or {"type": "object", "properties": {}},
            "strict": False,
        }
        for tool in cast("list[Json]", request.get("tools") or [])
        if tool.get("type", "custom") == "custom"
    ]
    if functions:
        body["tools"] = [
            {"type": "namespace", "name": NAMESPACE, "description": "QMA tools", "tools": functions}
        ]
        choice = _tool_choice(request.get("tool_choice"))
        if choice is not None:
            body["tool_choice"] = choice
    return Translation(body, renamed)


def _tool_choice(choice: object) -> str | None:
    if not isinstance(choice, dict):
        return None
    kind = cast("Json", choice).get("type")
    return {"auto": "auto", "any": "required", "tool": "required", "none": "none"}.get(str(kind))


def _text(value: object) -> str:
    """A string, or the text blocks of a block list joined by blank lines."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        blocks = cast("list[Json]", value)
        return "\n\n".join(str(b["text"]) for b in blocks if b.get("type") == "text")
    return ""


def _input_items(message: Json, wire: Callable[[str], str]) -> list[Json]:
    role = message.get("role")
    if role not in ("user", "assistant"):
        raise RefusedRequest(f"a message with role {role!r} has no Responses mapping")
    content = message.get("content")
    if isinstance(content, str):
        return [{"role": role, "content": content}]
    items: list[Json] = []
    parts: list[Json] = []

    def flush() -> None:
        if not parts:
            return
        if all(part["type"] in ("input_text", "output_text") for part in parts):
            items.append({"role": role, "content": "\n\n".join(p["text"] for p in parts)})
        else:
            items.append({"role": role, "content": list(parts)})
        parts.clear()

    for block in cast("list[Json]", content or []):
        match block.get("type"):
            case "text":
                kind = "output_text" if role == "assistant" else "input_text"
                parts.append({"type": kind, "text": str(block.get("text", ""))})
            case "image" if role == "user":
                parts.append({"type": "input_image", "image_url": _source_url(block)})
            case "document" if role == "user":
                parts.append(_document(block))
            case "tool_use":
                flush()
                items.append(
                    {
                        "type": "function_call",
                        "call_id": str(block["id"]),
                        "name": wire(str(block["name"])),
                        "namespace": NAMESPACE,
                        "arguments": json.dumps(block.get("input") or {}, ensure_ascii=False),
                    }
                )
            case "tool_result":
                flush()
                items.append(
                    {
                        "type": "function_call_output",
                        "call_id": str(block["tool_use_id"]),
                        "output": _tool_output(block.get("content")),
                    }
                )
            case "thinking" | "redacted_thinking":
                continue
            case other:
                raise RefusedRequest(
                    f"a {other} block in a {role} message has no Responses mapping"
                )
    flush()
    return items


def _source_url(block: Json) -> str:
    source = cast("Json", block.get("source") or {})
    match source.get("type"):
        case "base64":
            return f"data:{source.get('media_type')};base64,{source.get('data')}"
        case "url":
            return str(source.get("url"))
        case other:
            raise RefusedRequest(f"an image with a {other} source has no Responses mapping")


def _document(block: Json) -> Json:
    source = cast("Json", block.get("source") or {})
    if source.get("type") == "text":
        return {"type": "input_text", "text": str(source.get("data", ""))}
    if source.get("type") == "base64" and source.get("media_type") == "application/pdf":
        return {
            "type": "input_file",
            "filename": str(block.get("title") or "document.pdf"),
            "file_data": f"data:application/pdf;base64,{source.get('data')}",
        }
    raise RefusedRequest("only PDF and text documents have a Responses mapping")


def _tool_output(content: object) -> str:
    """Text only: an image a tool returned is named, not sent."""
    if isinstance(content, str):
        return content
    texts: list[str] = []
    for block in cast("list[Json]", content or []):
        if block.get("type") == "text":
            texts.append(str(block.get("text", "")))
        else:
            texts.append(f"[{block.get('type')} block not sent: GPT tool results carry text only]")
    return "\n\n".join(texts)


def estimate_tokens(request: Mapping[str, Any]) -> int:
    """`count_tokens` on the GPT lane: about four characters a token over what is sent. The
    route has no counting endpoint."""
    sent = {key: request.get(key) for key in ("system", "messages", "tools")}
    return max(1, len(json.dumps(sent, ensure_ascii=False)) // 4)


@dataclass(frozen=True)
class SseEvent:
    event: str
    data: Mapping[str, object]

    def encode(self) -> bytes:
        payload = json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
        return f"event: {self.event}\ndata: {payload}\n\n".encode()


def _event(data: Json) -> SseEvent:
    return SseEvent(str(data["type"]), data)


@dataclass
class StreamState:
    """One response stream's state machine: which content block is open and its index, the
    tool calls seen, the usage numbers, and the finished blocks for a non-streaming reply."""

    translation: Translation
    model: str
    served: str | None = None
    """`response.model` from the first event that carries it."""
    error: tuple[int, AnthropicErrorType, str] | None = None
    ended: bool = False
    stop_reason: str | None = None
    _started: bool = False
    _index: int = -1
    _open: Literal["text", "tool"] | None = None
    _streamed_args: bool = False
    _tool_calls: int = 0
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
        """The route's own counts from `response.completed`. ChatGPT has no usage API (02b F),
        so this is what the usage page shows for GPT."""
        return dict(self._usage)

    @property
    def started(self) -> bool:
        return self._started

    def feed(self, event: Mapping[str, Any]) -> list[SseEvent]:
        kind = str(event.get("type"))
        response = cast("Json", event.get("response") or {})
        if self.served is None and isinstance(response.get("model"), str):
            self.served = str(response["model"])
        if kind == "error":
            return self._fail(0, cast("Json", event.get("error") or event))
        if kind == "response.failed":
            return self._fail(0, cast("Json", response.get("error") or {}))
        out = self._start(response)
        match kind:
            case "response.output_item.added":
                item = cast("Json", event.get("item") or {})
                if item.get("type") == "function_call":
                    out += self._open_tool(item)
            case "response.output_text.delta":
                if self._open != "text":
                    out += self._close()
                    out += self._open_block({"type": "text", "text": ""}, "text")
                delta = str(event.get("delta", ""))
                self._blocks[-1]["text"] += delta
                out.append(self._delta({"type": "text_delta", "text": delta}))
            case "response.function_call_arguments.delta":
                if self._open == "tool":
                    delta = str(event.get("delta", ""))
                    self._blocks[-1]["arguments"] += delta
                    self._streamed_args = True
                    out.append(self._delta({"type": "input_json_delta", "partial_json": delta}))
            case "response.output_item.done":
                item = cast("Json", event.get("item") or {})
                if item.get("type") == "function_call":
                    if self._open != "tool":
                        out += self._open_tool(item)
                    if not self._streamed_args:
                        arguments = str(item.get("arguments") or "{}")
                        self._blocks[-1]["arguments"] = arguments
                        out.append(
                            self._delta({"type": "input_json_delta", "partial_json": arguments})
                        )
                    out += self._close()
                elif item.get("type") == "message":
                    out += self._close()
            case "response.completed":
                out += self._complete(response)
            case "response.incomplete":
                details = cast("Json", response.get("incomplete_details") or {})
                reason = details.get("reason") or "no reason given"
                self.error = (502, "api_error", f"the GPT response ended incomplete: {reason}")
                out.append(self._error_event())
            case _:
                pass
        return out

    def message(self) -> Json:
        """The finished reply as one Anthropic message, for a request with `stream: false`."""
        content: list[Json] = []
        for block in self._blocks:
            if block["type"] == "text":
                content.append({"type": "text", "text": block["text"]})
            else:
                try:
                    arguments: object = json.loads(block["arguments"] or "{}")
                except ValueError:
                    arguments = {}
                content.append(
                    {
                        "type": "tool_use",
                        "id": block["id"],
                        "name": block["name"],
                        "input": arguments,
                    }
                )
        return {
            "id": self._id,
            "type": "message",
            "role": "assistant",
            "model": self.served or self.model,
            "content": content,
            "stop_reason": self.stop_reason,
            "stop_sequence": None,
            "usage": self.usage,
        }

    def _start(self, response: Json) -> list[SseEvent]:
        if self._started:
            return []
        self._started = True
        if isinstance(response.get("id"), str):
            self._id = f"msg_{response['id']}"
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

    def _open_block(self, block: Json, kind: Literal["text", "tool"]) -> list[SseEvent]:
        self._index += 1
        self._open = kind
        self._blocks.append(dict(block) | ({"arguments": ""} if kind == "tool" else {}))
        start = {"type": "content_block_start", "index": self._index, "content_block": block}
        return [_event(start)]

    def _open_tool(self, item: Json) -> list[SseEvent]:
        out = self._close()
        self._tool_calls += 1
        self._streamed_args = False
        name = str(item.get("name", ""))
        block: Json = {
            "type": "tool_use",
            "id": str(item.get("call_id") or item.get("id")),
            "name": self.translation.tool_names.get(name, name),
            "input": {},
        }
        return out + self._open_block(block, "tool")

    def _delta(self, delta: Json) -> SseEvent:
        return _event({"type": "content_block_delta", "index": self._index, "delta": delta})

    def _close(self) -> list[SseEvent]:
        if self._open is None:
            return []
        self._open = None
        return [_event({"type": "content_block_stop", "index": self._index})]

    def _complete(self, response: Json) -> list[SseEvent]:
        usage = cast("Json", response.get("usage") or {})
        details = cast("Json", usage.get("input_tokens_details") or {})
        self._usage = {
            "input_tokens": int(usage.get("input_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or 0),
            "cache_read_input_tokens": int(details.get("cached_tokens") or 0),
        }
        self.stop_reason = "tool_use" if self._tool_calls else "end_turn"
        self.ended = True
        delta = {
            "type": "message_delta",
            "delta": {"stop_reason": self.stop_reason, "stop_sequence": None},
            "usage": self.usage,
        }
        return [*self._close(), _event(delta), _event({"type": "message_stop"})]

    def _fail(self, status: int, error: Json) -> list[SseEvent]:
        self.error = map_error(status, error)
        return [self._error_event()]

    def _error_event(self) -> SseEvent:
        self.ended = True
        _, kind, text = self.error or (502, "api_error", "unknown")
        return _event({"type": "error", "error": {"type": kind, "message": text}})


ERROR_CODES: Final[Mapping[str, tuple[int, AnthropicErrorType]]] = {
    "subscription_sharing_usage_limit_exceeded": (429, "rate_limit_error"),
    "subscription_sharing_unsupported_capability": (400, "invalid_request_error"),
    NOT_ELIGIBLE: (403, "permission_error"),
    "subscription_sharing_route_not_supported": (403, "permission_error"),
}


def map_error(status: int, error: Mapping[str, Any]) -> tuple[int, AnthropicErrorType, str]:
    """The Anthropic status, error type and message for a Responses error. The documented
    `subscription_sharing_*` codes map by code. HP2 measured every 400 on this route with
    `code` and `param` null and only `error.message` naming the cause, so the rest map by HTTP
    status, `status` 0 meaning an error inside a 200 stream. Never retried onto another billing
    path, matching OpenAI's own rule."""
    code = str(error.get("code") or "")
    message = str(error.get("message") or code or "the ChatGPT route returned an error")
    if code == "subscription_sharing_unsupported_capability" and error.get("param"):
        message = f"{message} (unsupported: {error['param']})"
    text = f"ChatGPT: {message}"
    if code in ERROR_CODES:
        mapped, kind = ERROR_CODES[code]
        return mapped, kind, text
    if status == 429:
        return 429, "rate_limit_error", text
    if status == 401:
        return 401, "authentication_error", f"{text}; type /login chatgpt"
    if status == 403:
        return 403, "permission_error", text
    if 400 <= status < 500:
        return 400, "invalid_request_error", text
    return 502, "api_error", text


def parse_sse(lines: Sequence[str]) -> list[Json]:
    """The JSON payloads of one block of SSE lines. `[DONE]` and non-JSON payloads are
    skipped."""
    data = [line[5:].strip() for line in lines if line.startswith("data:")]
    if not data or data[0] == "[DONE]":
        return []
    try:
        found = json.loads("\n".join(data))
    except ValueError:
        return []
    return [cast("Json", found)] if isinstance(found, dict) else []
