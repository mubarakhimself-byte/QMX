"""`complete`: one model call with no CLI process (engine AD-56, AD-13, H3).

The engine's `llm` nodes, a mini app's `llm_complete(role, schema)` and any other one-shot caller
ask the router for one answer. The relay serves it on the key and GPT lanes: one request through
the same normaliser, the same lease, the same classifier and the same journal row as a chat
request. A plan row is refused, because only the CLI holds the plan sign-in; that caller keeps
the one-turn, tool-less Background chat of AD-13.

This module holds the wire shapes and the schema check, so they can be tested without HTTP:

- `ask_body` builds the Anthropic-shaped request from the caller's messages; `normalise` edits it
  for the row and `chat_lane.to_chat` or `translate.to_responses` translates it, exactly as a
  chat request is edited.
- `reply` reads a finished chat-completions or Responses stream through the lane's own
  `StreamState`, so the answer is the message a chat would have seen.
- `check` validates a schema answer: object, required, type, enum, items and properties, which
  is what the router's own schemas use. A schema that needs more belongs in the caller.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, cast

from qmx_router import chat_lane
from qmx_router.gpt import translate
from qmx_router.normalise import normalise
from qmx_router.profiles import ProfileName
from qmx_router.registry import ModelRow

SCHEMA_NAME: Final = "qmx_complete"
SCHEMA_INSTRUCTION: Final = (
    "Answer with one JSON document that matches this schema and nothing else: "
)
"""Because an Anthropic-wire row with no structured-output beta has no field for a schema."""


@dataclass(frozen=True)
class Ask:
    """One completion request: the caller's messages, an optional system prompt, and a schema
    the answer must hold to."""

    messages: Sequence[Mapping[str, object]]
    system: str = ""
    max_tokens: int = 4096
    schema: Mapping[str, object] | None = None


@dataclass(frozen=True)
class Completion:
    """One answer, with where it came from and what it used."""

    text: str
    qmx_id: str
    model: str
    """The model the provider says it served."""
    account: str
    usage: Mapping[str, int]
    data: Mapping[str, object] | None = None
    """The parsed answer when the caller asked for a schema."""
    ms: int = 0


class Refused(RuntimeError):
    """The router will not serve this completion, or the answer broke the schema."""


def plan_refusal(provider: ProfileName) -> str:
    """The one sentence a plan row gets, naming where a plan call does run."""
    return (
        f"{provider} is the plan, and only the CLI holds the plan sign-in, so complete never "
        "serves a plan row: a plan row runs as the one-turn, tool-less chat of AD-13"
    )


def ask_body(ask: Ask, model: str) -> dict[str, Any]:
    """The request in Anthropic's shape, before the normaliser edits it for the row. A schema
    rides as its own field for a row that takes one, and as an instruction for a row that does
    not."""
    messages = [dict(message) for message in ask.messages]
    system = ask.system
    if ask.schema is not None:
        hint = SCHEMA_INSTRUCTION + json.dumps(ask.schema, sort_keys=True)
        system = f"{system}\n\n{hint}".strip() if system else hint
    body: dict[str, Any] = {"model": model, "max_tokens": ask.max_tokens, "messages": messages}
    if system:
        body["system"] = system
    return body


def chat_request(row: ModelRow, ask: Ask, model: str) -> bytes:
    """The `/v1/chat/completions` body for a `openai_chat` row: normalised, then translated, then
    given the schema as `response_format`, which is where chat completions takes one."""
    document = json.loads(normalise(row, _dumps(ask_body(ask, model)), {}).body)
    translation = chat_lane.to_chat(cast("dict[str, Any]", document), model=model)
    body = dict(translation.body)
    if ask.schema is not None:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": SCHEMA_NAME, "schema": ask.schema, "strict": True},
        }
    return _dumps(body)


def responses_request(row: ModelRow, ask: Ask, model: str) -> bytes:
    """The `/responses` body for a GPT row, with the schema in `text.format`."""
    document = json.loads(normalise(row, _dumps(ask_body(ask, model)), {}).body)
    translation = translate.to_responses(cast("dict[str, Any]", document), model=model)
    body = dict(translation.body)
    if ask.schema is not None:
        body["text"] = {
            "format": {
                "type": "json_schema",
                "name": SCHEMA_NAME,
                "schema": ask.schema,
                "strict": True,
            }
        }
    return _dumps(body)


def anthropic_request(row: ModelRow, ask: Ask, model: str) -> bytes:
    """The `/v1/messages` body for a key row on the Anthropic wire, with no stream.

    Thinking is off wherever the row lets the request say so: a completion's caller reads only
    the answer, and a reasoning row that spends its whole answer inside a thinking block returns
    no text (measured on OpenRouter's DeepSeek V4.1 Flash row, 2026-10-20). A row whose thinking
    is forced keeps it, because the route refuses a request that turns it off."""
    document = json.loads(normalise(row, _dumps(ask_body(ask, model)), {}).body)
    document["stream"] = False
    if row.thinking != "forced":
        document["thinking"] = {"type": "disabled"}
    return _dumps(cast("dict[str, Any]", document))


@dataclass(frozen=True)
class Answer:
    """What one provider reply carried: the text, the served model and the usage."""

    text: str
    model: str
    usage: Mapping[str, int]


def anthropic_answer(payload: Mapping[str, Any]) -> Answer:
    """A finished `/v1/messages` reply."""
    return Answer(_text_of(payload.get("content")), str(payload.get("model", "")), _usage(payload))


def streamed_answer(lines: Sequence[str], row: ModelRow, model: str) -> Answer:
    """A finished lane stream, read through the lane's own state machine, so a chat and a
    completion read one answer the same way."""
    if row.wire == "responses":
        state = translate.StreamState(translate.Translation({}, {}), model)
        for event in translate.parse_sse(list(lines)):
            state.feed(event)
        return Answer(_text_of(state.message().get("content")), state.served or model, state.usage)
    translation = chat_lane.Translation({}, {})
    chat = chat_lane.StreamState(translation, model)
    for chunk in chat_lane.parse_sse(list(lines)):
        chat.feed(chunk)
    if not chat.ended:
        chat.finish()
    return Answer(_text_of(chat.message().get("content")), chat.served or model, chat.usage)


def answer_text(answer: Answer, ask: Ask) -> tuple[str, Mapping[str, object] | None]:
    """The text, and the parsed document when a schema was asked for. A refusal names what the
    answer was, never the schema's own words."""
    if ask.schema is None:
        return answer.text, None
    try:
        parsed: object = json.loads(answer.text)
    except ValueError:
        raise Refused(f"the answer is not JSON: {answer.text[:200]!r}") from None
    if not isinstance(parsed, dict):
        raise Refused("the answer is JSON but not one object")
    document = cast("dict[str, object]", parsed)
    check(ask.schema, document)
    return answer.text, document


def check(schema: Mapping[str, object], value: object, at: str = "answer") -> None:
    """Refuse a value the schema does not allow: type, enum, required, properties, items and
    `additionalProperties: false`."""
    choices = schema.get("enum")
    if isinstance(choices, list) and value not in cast("list[object]", choices):
        raise Refused(f"{at} is not one of the schema's enum values")
    expected = schema.get("type")
    if expected is not None and isinstance(expected, str) and not _is_type(expected, value):
        raise Refused(f"{at} is {type(value).__name__}, and the schema says {expected}")
    if isinstance(value, dict):
        _check_object(schema, cast("dict[str, object]", value), at)
    elif isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for at_item, item in enumerate(cast("list[object]", value)):
                check(cast("Mapping[str, object]", item_schema), item, f"{at}[{at_item}]")


def _check_object(schema: Mapping[str, object], table: dict[str, object], at: str) -> None:
    required = schema.get("required")
    if isinstance(required, list):
        missing = [name for name in cast("list[str]", required) if name not in table]
        if missing:
            raise Refused(f"{at} is missing {', '.join(missing)}")
    properties = schema.get("properties")
    known = cast("Mapping[str, object]", properties) if isinstance(properties, Mapping) else None
    if schema.get("additionalProperties") is False and known is not None:
        extra = sorted(set(table) - set(known))
        if extra:
            raise Refused(f"{at} carries {', '.join(extra)}, which the schema does not allow")
    if known is None:
        return
    for name, child in known.items():
        if name in table and isinstance(child, Mapping):
            check(cast("Mapping[str, object]", child), table[name], f"{at}.{name}")


def _is_type(expected: str, value: object) -> bool:
    match expected:
        case "object":
            return isinstance(value, dict)
        case "array":
            return isinstance(value, list)
        case "string":
            return isinstance(value, str)
        case "boolean":
            return isinstance(value, bool)
        case "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        case "number":
            return isinstance(value, int | float) and not isinstance(value, bool)
        case "null":
            return value is None
        case _:
            return True


def _text_of(content: object) -> str:
    """The text blocks of a message's content, joined by blank lines."""
    if isinstance(content, str):
        return content
    blocks = cast("list[dict[str, Any]]", content or [])
    return "\n\n".join(
        str(block.get("text", "")) for block in blocks if block.get("type") == "text"
    )


def _usage(payload: Mapping[str, Any]) -> Mapping[str, int]:
    usage = payload.get("usage")
    table: dict[str, Any] = dict(cast("dict[str, Any]", usage)) if isinstance(usage, dict) else {}
    return {
        name: int(value) if isinstance(value, int) and not isinstance(value, bool) else 0
        for name, value in table.items()
        if name in {"input_tokens", "output_tokens", "cache_read_input_tokens"}
    }


def _dumps(document: object) -> bytes:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()
