"""The in-house chat-completions lane (H12, AD-38): the translator on recorded bodies, and the
relay routing a chat-wire row to it over a fake upstream. Bodies are literals in the shape the
OpenAI-compatible routes (Kimi, DeepSeek, GLM, OpenRouter) answer in.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

import httpx
import pytest

from qmx_router.chat_lane import (
    RefusedRequest,
    StreamState,
    Translation,
    map_error,
    thinking_signature,
    to_chat,
)
from qmx_router.ids import SessionId
from qmx_router.profiles import ModelId, ProfileName, Profiles, parse_profiles
from qmx_router.registry import ModelRow, Provider, QmxId, Registry
from qmx_router.relay import Relay, RelayUsage

CHAT = SessionId("6f1d2c3b-4a59-4e8d-9c7b-1a2b3c4d5e6f")
KEY = "chat-lane-key-for-tests"
LONG_TOOL = "mcp__qmx__library_search_with_a_name_far_too_long_for_the_route_and_more"
LONG_WIRE = "mcp__qmx__library_search_with_a_name_far_too_long_for_t_b31a3c31"
ROW = ModelRow(
    qmx_id=QmxId("chatty/kimi-k3"),
    provider=ProfileName("chatty"),
    native=ModelId("kimi-k3"),
    wire="openai_chat",
    forward_headers=frozenset({"x-chatty-session"}),
)
CLI_REQUEST: dict[str, Any] = {
    "model": "chatty/kimi-k3",
    "max_tokens": 2048,
    "stream": True,
    "temperature": 1,
    "metadata": {"user_id": "u"},
    "thinking": {"type": "enabled", "budget_tokens": 4000},
    "system": [
        {"type": "text", "text": "You are Claude Code."},
        {"type": "text", "text": "Second block."},
    ],
    "tools": [
        {
            "name": "Bash",
            "description": "Run a command.",
            "input_schema": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
        {"name": LONG_TOOL, "description": "Search.", "input_schema": {"type": "object"}},
        {"type": "web_search_20250305", "name": "web_search"},
    ],
    "tool_choice": {"type": "any"},
    "messages": [
        {"role": "user", "content": "Make hello.txt"},
        {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "plan", "signature": "anthropic-sig=="},
                {"type": "text", "text": "I will run a command."},
                {"type": "tool_use", "id": "toolu_01", "name": "Bash", "input": {"command": "ls"}},
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_01",
                    "content": [{"type": "text", "text": "hello.txt"}],
                },
                {"type": "text", "text": "now search"},
            ],
        },
    ],
}
EXPECTED_CHAT_BODY: dict[str, Any] = {
    "model": "kimi-k3",
    "messages": [
        {"role": "system", "content": "You are Claude Code.\n\nSecond block."},
        {"role": "user", "content": "Make hello.txt"},
        {
            "role": "assistant",
            "content": "I will run a command.",
            "tool_calls": [
                {
                    "id": "toolu_01",
                    "type": "function",
                    "function": {"name": "Bash", "arguments": '{"command":"ls"}'},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "toolu_01", "content": "hello.txt"},
        {"role": "user", "content": "now search"},
    ],
    "stream": True,
    "stream_options": {"include_usage": True},
    "max_tokens": 2048,
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "Bash",
                "description": "Run a command.",
                "parameters": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": LONG_WIRE,
                "description": "Search.",
                "parameters": {"type": "object"},
            },
        },
    ],
    "tool_choice": "required",
}


def test_a_cli_request_becomes_the_chat_body_the_route_reads() -> None:
    translation = to_chat(CLI_REQUEST, model="kimi-k3")
    assert translation.body == EXPECTED_CHAT_BODY
    assert translation.tool_names == {LONG_WIRE: LONG_TOOL}


def test_only_a_thinking_block_this_translator_signed_goes_back_out() -> None:
    def assistant(block: dict[str, Any]) -> dict[str, Any]:
        return to_chat(
            {"messages": [{"role": "assistant", "content": [block]}]}, model="kimi-k3"
        ).body["messages"][0]

    mine = {"type": "thinking", "thinking": "plan", "signature": thinking_signature("plan")}
    assert assistant(mine)["reasoning_content"] == "plan"
    assert "reasoning_content" not in assistant(
        {"type": "thinking", "thinking": "plan", "signature": "sk-ant-sig"}
    )
    assert "reasoning_content" not in assistant(
        {"type": "thinking", "thinking": "other", "signature": thinking_signature("plan")}
    )


def test_a_block_with_no_route_mapping_is_refused_by_name() -> None:
    request: dict[str, Any] = {
        "messages": [{"role": "user", "content": [{"type": "document", "source": {}}]}]
    }
    with pytest.raises(RefusedRequest, match="chat-completions mapping"):
        to_chat(request, model="kimi-k3")


CHUNKS: list[dict[str, Any]] = [
    {
        "id": "gen-1",
        "model": "kimi-k3",
        "choices": [
            {"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}
        ],
    },
    {
        "choices": [
            {"index": 0, "delta": {"reasoning_content": "Let me think."}, "finish_reason": None}
        ]
    },
    {"choices": [{"index": 0, "delta": {"content": "I will call echo."}, "finish_reason": None}]},
    {
        "choices": [
            {
                "index": 0,
                "delta": {
                    "tool_calls": [
                        {
                            "index": 0,
                            "id": "call_a1",
                            "type": "function",
                            "function": {"name": "echo", "arguments": '{"text":'},
                        }
                    ]
                },
                "finish_reason": None,
            }
        ]
    },
    {
        "choices": [
            {
                "index": 0,
                "delta": {"tool_calls": [{"index": 0, "function": {"arguments": '"a"}'}}]},
                "finish_reason": None,
            }
        ]
    },
    {"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]},
    {
        "choices": [],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "prompt_tokens_details": {"cached_tokens": 4},
        },
    },
]
EXPECTED_EVENTS: list[tuple[str, dict[str, Any]]] = [
    (
        "message_start",
        {
            "type": "message_start",
            "message": {
                "id": "msg_gen-1",
                "type": "message",
                "role": "assistant",
                "model": "kimi-k3",
                "content": [],
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        },
    ),
    (
        "content_block_start",
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "thinking", "thinking": "", "signature": ""},
        },
    ),
    (
        "content_block_delta",
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "thinking_delta", "thinking": "Let me think."},
        },
    ),
    ("content_block_stop", {"type": "content_block_stop", "index": 0}),
    (
        "content_block_start",
        {"type": "content_block_start", "index": 1, "content_block": {"type": "text", "text": ""}},
    ),
    (
        "content_block_delta",
        {
            "type": "content_block_delta",
            "index": 1,
            "delta": {"type": "text_delta", "text": "I will call echo."},
        },
    ),
    ("content_block_stop", {"type": "content_block_stop", "index": 1}),
    (
        "content_block_start",
        {
            "type": "content_block_start",
            "index": 2,
            "content_block": {"type": "tool_use", "id": "call_a1", "name": "echo", "input": {}},
        },
    ),
    (
        "content_block_delta",
        {
            "type": "content_block_delta",
            "index": 2,
            "delta": {"type": "input_json_delta", "partial_json": '{"text":'},
        },
    ),
    (
        "content_block_delta",
        {
            "type": "content_block_delta",
            "index": 2,
            "delta": {"type": "input_json_delta", "partial_json": '"a"}'},
        },
    ),
    ("content_block_stop", {"type": "content_block_stop", "index": 2}),
    (
        "message_delta",
        {
            "type": "message_delta",
            "delta": {"stop_reason": "tool_use", "stop_sequence": None},
            "usage": {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 4},
        },
    ),
    ("message_stop", {"type": "message_stop"}),
]


def test_a_recorded_stream_becomes_anthropic_events_and_a_finished_message() -> None:
    state = StreamState(Translation({"model": "kimi-k3"}, {}), "kimi-k3")
    events: list[tuple[str, dict[str, Any]]] = []
    for chunk in CHUNKS:
        events += [(event.event, dict(event.data)) for event in state.feed(chunk)]
    events += [(event.event, dict(event.data)) for event in state.finish()]
    assert events == EXPECTED_EVENTS
    message = state.message()
    assert message["content"] == [
        {
            "type": "thinking",
            "thinking": "Let me think.",
            "signature": thinking_signature("Let me think."),
        },
        {"type": "text", "text": "I will call echo."},
        {"type": "tool_use", "id": "call_a1", "name": "echo", "input": {"text": "a"}},
    ]
    assert (message["stop_reason"], message["usage"]) == (
        "tool_use",
        {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 4},
    )


def test_a_tool_call_id_survives_ten_turns_of_history() -> None:
    """The vendor's `tool_calls` id is the CLI's `tool_use` id and its `tool_call_id` comes back
    as the same string, ten turns deep with every earlier call in the history."""
    history: list[dict[str, Any]] = []
    for turn in range(1, 11):
        state = StreamState(Translation({"model": "kimi-k3"}, {}), "kimi-k3")
        state.feed(
            {
                "id": f"gen-{turn}",
                "model": "kimi-k3",
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": f"call_{turn}",
                                    "type": "function",
                                    "function": {"name": "echo", "arguments": '{"text":"x"}'},
                                }
                            ]
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
            }
        )
        state.finish()
        message = state.message()
        call_id = message["content"][0]["id"]
        assert call_id == f"call_{turn}"
        history.append({"role": "user", "content": f"turn {turn}"})
        history.append({"role": "assistant", "content": message["content"]})
        history.append(
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": call_id, "content": "ok"}],
            }
        )
        sent = to_chat({"messages": history}, model="kimi-k3").body["messages"]
        assert sent[-2]["tool_calls"][0]["id"] == call_id
        assert sent[-1] == {"role": "tool", "tool_call_id": call_id, "content": "ok"}


def test_map_error_names_the_class_the_cli_shows() -> None:
    assert map_error(429, {"message": "slow down"}) == (429, "rate_limit_error", "slow down")
    assert map_error(0, {"message": "boom"}) == (502, "api_error", "boom")
    assert map_error(400, {"code": "context_length_exceeded", "message": "too long"}) == (
        400,
        "invalid_request_error",
        "too long",
    )
    assert map_error(404, {"message": "no such model"}) == (
        400,
        "invalid_request_error",
        "no such model",
    )


@dataclass
class Journals:
    rows: list[RelayUsage] = field(default_factory=list[RelayUsage])

    def open(self, _session: SessionId) -> Writer:
        return Writer(self)


@dataclass
class Writer:
    journals: Journals

    def append(self, usage: RelayUsage) -> None:
        self.journals.rows.append(usage)

    def close(self) -> None:
        return None


def secret(reference: str) -> str:
    if reference != "qmx/chatty":
        raise KeyError(reference)
    return KEY


def registry() -> Registry:
    provider = Provider(
        name=ProfileName("chatty"),
        kind="key",
        base_url=MappingProxyType({"global": "https://upstream.test"}),
        models=(ROW,),
    )
    return Registry(MappingProxyType({ProfileName("chatty"): provider}))


ROWS: dict[str, object] = {
    "chatty": {
        "base_url": "https://upstream.test",
        "credential_ref": "qmx/chatty",
        "tiers": {"opus": "kimi-k3", "sonnet": "kimi-k3", "haiku": "kimi-k3", "fable": "kimi-k3"},
    }
}
CHAT_STREAM = (
    b'data: {"id":"gen-9","model":"kimi-k3","choices":[{"index":0,"delta":'
    b'{"role":"assistant","content":"Hello"},"finish_reason":null}]}\n\n'
    b'data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n'
    b'data: {"choices":[],"usage":{"prompt_tokens":12,"completion_tokens":3}}\n\n'
    b"data: [DONE]\n\n"
)


@dataclass
class Rig:
    relay: Relay
    journals: Journals
    alerts: list[str]
    seen: list[httpx.Request]

    @property
    def usage(self) -> list[RelayUsage]:
        return self.journals.rows

    async def post(
        self, path: str, body: dict[str, Any], bearer: str, **headers: str
    ) -> httpx.Response:
        async with httpx.AsyncClient(base_url=self.relay.base_url, trust_env=False) as client:
            return await client.post(
                path,
                content=json.dumps(body).encode(),
                headers={"authorization": f"Bearer {bearer}", "content-type": "application/json"}
                | headers,
            )


def run(
    test: Callable[[Rig], Awaitable[None]], handler: Callable[[httpx.Request], httpx.Response]
) -> None:
    async def main() -> None:
        journals, alerts, seen = Journals(), list[str](), list[httpx.Request]()

        def capture(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return handler(request)

        async def alert(_chat: SessionId, reason: str) -> None:
            alerts.append(reason)

        def profiles() -> Profiles:
            return parse_profiles(ROWS)

        relay = await Relay(
            secrets=secret,
            journal=journals.open,
            alert=alert,
            profiles=profiles,
            registry=registry,
            transport=httpx.MockTransport(capture),
        ).start()
        try:
            await test(Rig(relay, journals, alerts, seen))
        finally:
            await relay.close()

    asyncio.run(main())


def text_stream(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content=CHAT_STREAM, headers={"content-type": "text/event-stream"})


def reader(document: dict[str, Any]) -> Callable[[], Awaitable[bytes]]:
    async def provide() -> bytes:
        return json.dumps(document).encode()

    return provide


CHAT_REQUEST: dict[str, Any] = {
    "model": "chatty/kimi-k3",
    "max_tokens": 4096,
    "stream": True,
    "thinking": {"type": "enabled", "budget_tokens": 4000},
    "system": [{"type": "text", "text": "system"}],
    "tools": [
        {
            "name": "Bash",
            "description": "Run.",
            "input_schema": {"type": "object"},
            "defer_loading": True,
        }
    ],
    "messages": [{"role": "user", "content": "hi"}],
}


def test_a_chat_wire_row_reaches_the_chat_route_with_no_anthropic_field() -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("chatty"))
        answer = await rig.post(
            "/v1/messages",
            CHAT_REQUEST,
            grant.secret,
            **{
                "x-chatty-session": "s-1",
                "anthropic-version": "2023-06-01",
                "anthropic-beta": "oauth-2025-04-20",
                "x-claude-code-session-id": "leak",
            },
        )
        assert answer.status_code == 200
        sent = rig.seen[0]
        assert (sent.method, sent.url.path) == ("POST", "/v1/chat/completions")
        assert sent.headers["x-chatty-session"] == "s-1"
        assert "anthropic-version" not in sent.headers
        assert "anthropic-beta" not in sent.headers
        assert "x-claude-code-session-id" not in sent.headers
        body = json.loads(sent.content)
        assert body["model"] == "kimi-k3"
        assert body["max_tokens"] == 4096
        assert body["messages"] == [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "hi"},
        ]
        assert body["tools"] == [
            {
                "type": "function",
                "function": {
                    "name": "Bash",
                    "description": "Run.",
                    "parameters": {"type": "object"},
                },
            }
        ]
        assert "thinking" not in body
        assert "defer_loading" not in json.dumps(body)
        events = sse(answer.content)
        assert [name for name, _ in events] == [
            "message_start",
            "content_block_start",
            "content_block_delta",
            "content_block_stop",
            "message_delta",
            "message_stop",
        ]
        assert events[2][1]["delta"] == {"type": "text_delta", "text": "Hello"}
        assert events[4][1]["usage"] == {
            "input_tokens": 12,
            "output_tokens": 3,
            "cache_read_input_tokens": 0,
        }
        assert (rig.usage[0].model, rig.usage[0].path, rig.usage[0].status) == (
            "kimi-k3",
            "/v1/messages",
            200,
        )
        assert (rig.usage[0].input_tokens, rig.usage[0].output_tokens) == (12, 3)
        assert rig.alerts == []

    run(check, text_stream)


def test_a_chat_row_counts_tokens_locally_and_never_calls_the_route() -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("chatty"))
        answer = await rig.post(
            "/v1/messages/count_tokens",
            {"model": "chatty/kimi-k3", "messages": [{"role": "user", "content": "hi"}]},
            grant.secret,
        )
        assert answer.status_code == 200
        assert answer.json()["input_tokens"] > 0
        assert rig.seen == []

    run(check, text_stream)


def test_a_usage_limit_answer_stops_the_cli_retrying_and_is_journalled() -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("chatty"))
        answer = await rig.post(
            "/v1/messages",
            {
                "model": "chatty/kimi-k3",
                "stream": True,
                "messages": [{"role": "user", "content": "hi"}],
            },
            grant.secret,
        )
        assert (answer.status_code, answer.headers["x-should-retry"]) == (429, "false")
        assert answer.json() == {
            "type": "error",
            "error": {"type": "rate_limit_error", "message": "usage limit reached"},
        }
        assert rig.usage[0].status == 429

    def limited(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "usage limit reached", "code": None}})

    run(check, limited)


def sse(data: bytes) -> list[tuple[str, dict[str, Any]]]:
    """(event name, payload) pairs from a served set of Anthropic SSE chunks."""
    out: list[tuple[str, dict[str, Any]]] = []
    name = ""
    for line in data.decode().splitlines():
        if line.startswith("event:"):
            name = line[6:].strip()
        elif line.startswith("data:"):
            out.append((name, json.loads(line[5:].strip())))
    return out
