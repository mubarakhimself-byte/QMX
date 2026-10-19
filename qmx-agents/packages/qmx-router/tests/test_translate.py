"""`qma.gpt.translate` over fixtures shaped like the traffic HP2 recorded on the ChatGPT route:
the CLI's Anthropic request on one side, the route's Responses SSE event sequence on the other
(`hp2-p2.log`, `hp2-p3-namespace.log`: created, in_progress, output_item.added, the deltas,
output_item.done, completed with an empty `output`)."""

from __future__ import annotations

from typing import Any

import pytest

from qmx_router.gpt.translate import (
    RefusedRequest,
    StreamState,
    Translation,
    estimate_tokens,
    map_error,
    parse_sse,
    to_responses,
    wire_name,
)

LONG_TOOL = "mcp__qmx__" + "library_search_with_a_name_far_too_long_for_the_route_" + "x" * 20
LONG_WIRE = "mcp__qmx__library_search_with_a_name_far_too_long_for_t_1e1a07dd"

CLI_REQUEST: dict[str, Any] = {
    "model": "gpt-6.1-sol",
    "max_tokens": 32000,
    "temperature": 1,
    "top_p": 0.9,
    "metadata": {"user_id": "u"},
    "stop_sequences": ["END"],
    "stream": True,
    "thinking": {"type": "enabled", "budget_tokens": 4000},
    "context_management": {"edits": []},
    "system": [
        {"type": "text", "text": "x-anthropic-billing-header: cc_version=2.1.299"},
        {"type": "text", "text": "You are Claude Code.", "cache_control": {"type": "ephemeral"}},
    ],
    "tools": [
        {
            "name": "Bash",
            "description": "Run a command.",
            "input_schema": {
                "type": "object",
                "properties": {"command": {"type": "string"}, "timeout": {"type": "number"}},
                "required": ["command"],
            },
        },
        {"name": LONG_TOOL, "description": "Search.", "input_schema": {"type": "object"}},
        {"type": "web_search_20250305", "name": "web_search"},
    ],
    "tool_choice": {"type": "auto"},
    "messages": [
        {"role": "user", "content": "Make hello.txt"},
        {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "plan", "signature": "sig"},
                {"type": "text", "text": "I will run a command."},
                {"type": "tool_use", "id": "call_1", "name": "Bash", "input": {"command": "ls"}},
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "call_1",
                    "content": [
                        {"type": "text", "text": "hello.txt"},
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": "image/png", "data": "AA"},
                        },
                    ],
                },
                {"type": "text", "text": "now search", "cache_control": {"type": "ephemeral"}},
            ],
        },
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "call_2", "name": LONG_TOOL, "input": {}}],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "call_2", "content": "none"}],
        },
    ],
}

EXPECTED_BODY: dict[str, Any] = {
    "model": "gpt-6.1-sol",
    "store": False,
    "stream": True,
    "instructions": "x-anthropic-billing-header: cc_version=2.1.299\n\nYou are Claude Code.",
    "input": [
        {"role": "user", "content": "Make hello.txt"},
        {"role": "assistant", "content": "I will run a command."},
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "Bash",
            "namespace": "qma",
            "arguments": '{"command": "ls"}',
        },
        {
            "type": "function_call_output",
            "call_id": "call_1",
            "output": "hello.txt\n\n[image block not sent: GPT tool results carry text only]",
        },
        {"role": "user", "content": "now search"},
        {
            "type": "function_call",
            "call_id": "call_2",
            "name": LONG_WIRE,
            "namespace": "qma",
            "arguments": "{}",
        },
        {"type": "function_call_output", "call_id": "call_2", "output": "none"},
    ],
    "tools": [
        {
            "type": "namespace",
            "name": "qma",
            "description": "QMA tools",
            "tools": [
                {
                    "type": "function",
                    "name": "Bash",
                    "description": "Run a command.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "timeout": {"type": "number"},
                        },
                        "required": ["command"],
                    },
                    "strict": False,
                },
                {
                    "type": "function",
                    "name": LONG_WIRE,
                    "description": "Search.",
                    "parameters": {"type": "object"},
                    "strict": False,
                },
            ],
        }
    ],
    "tool_choice": "auto",
}


def test_a_cli_request_becomes_this_responses_body() -> None:
    translation = to_responses(CLI_REQUEST, model="gpt-6.1-sol")
    assert dict(translation.body) == EXPECTED_BODY
    assert dict(translation.tool_names) == {LONG_WIRE: LONG_TOOL}


def test_every_barred_and_beta_field_is_dropped() -> None:
    body = to_responses(CLI_REQUEST, model="gpt-6.1-sol").body
    assert sorted(body) == [
        "input",
        "instructions",
        "model",
        "store",
        "stream",
        "tool_choice",
        "tools",
    ]


@pytest.mark.parametrize(
    ("name", "wire"),
    [
        ("Bash", "Bash"),
        ("mcp__qmx__read", "mcp__qmx__read"),
        ("a.b c", "a_b_c_8640d2e2"),
        (LONG_TOOL, LONG_WIRE),
    ],
)
def test_a_name_the_route_cannot_take_gets_a_stable_short_wire_name(name: str, wire: str) -> None:
    assert wire_name(name) == wire
    assert len(wire_name(name)) <= 64


def test_an_image_from_the_user_goes_as_input_image() -> None:
    image = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AA"}}
    request = {"messages": [{"role": "user", "content": [{"type": "text", "text": "see"}, image]}]}
    assert to_responses(request, model="gpt-6.1-sol").body["input"] == [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "see"},
                {"type": "input_image", "image_url": "data:image/png;base64,AA"},
            ],
        }
    ]


@pytest.mark.parametrize(
    ("message", "reason"),
    [
        (
            {"role": "user", "content": [{"type": "audio", "source": dict[str, str]()}]},
            "a audio block in a user message has no Responses mapping",
        ),
        (
            {"role": "tool", "content": "x"},
            "a message with role 'tool' has no Responses mapping",
        ),
        (
            {
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "text/csv"}}
                ],
            },
            "only PDF and text documents have a Responses mapping",
        ),
    ],
)
def test_input_the_route_cannot_take_is_refused(message: dict[str, Any], reason: str) -> None:
    with pytest.raises(RefusedRequest) as refused:
        to_responses({"messages": [message]}, model="gpt-6.1-sol")
    assert str(refused.value) == reason


HELLO_EVENTS: list[dict[str, Any]] = [
    {
        "type": "response.created",
        "response": {"id": "resp_1", "model": "gpt-6.1-sol", "output": []},
    },
    {"type": "response.in_progress", "response": {"id": "resp_1"}},
    {"type": "response.output_item.added", "output_index": 0, "item": {"type": "message"}},
    {"type": "response.content_part.added", "output_index": 0},
    {"type": "response.output_text.delta", "output_index": 0, "delta": "hello "},
    {"type": "response.output_text.delta", "output_index": 0, "delta": "from QMA"},
    {"type": "response.output_text.done", "output_index": 0},
    {"type": "response.content_part.done", "output_index": 0},
    {"type": "response.output_item.done", "output_index": 0, "item": {"type": "message"}},
    {
        "type": "response.completed",
        "response": {
            "id": "resp_1",
            "output": [],
            "usage": {
                "input_tokens": 21,
                "output_tokens": 5,
                "input_tokens_details": {"cached_tokens": 3},
            },
        },
    },
]

HELLO_SSE: list[dict[str, Any]] = [
    {
        "type": "message_start",
        "message": {
            "id": "msg_resp_1",
            "type": "message",
            "role": "assistant",
            "model": "gpt-6.1-sol",
            "content": [],
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        },
    },
    {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "hello "}},
    {
        "type": "content_block_delta",
        "index": 0,
        "delta": {"type": "text_delta", "text": "from QMA"},
    },
    {"type": "content_block_stop", "index": 0},
    {
        "type": "message_delta",
        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
        "usage": {"input_tokens": 21, "output_tokens": 5, "cache_read_input_tokens": 3},
    },
    {"type": "message_stop"},
]


def feed_all(state: StreamState, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(sse.data) for event in events for sse in state.feed(event)]


def test_a_hello_stream_becomes_these_anthropic_events() -> None:
    state = StreamState(Translation({}, {}), "gpt-6.1-sol")
    assert feed_all(state, HELLO_EVENTS) == HELLO_SSE
    assert state.served == "gpt-6.1-sol"
    assert dict(state.usage) == {
        "input_tokens": 21,
        "output_tokens": 5,
        "cache_read_input_tokens": 3,
    }
    assert state.ended


def test_each_event_is_encoded_with_its_name() -> None:
    state = StreamState(Translation({}, {}), "gpt-6.1-sol")
    first = state.feed(HELLO_EVENTS[0])[0].encode()
    assert first.startswith(b"event: message_start\ndata: {")
    assert first.endswith(b"}\n\n")


TOOL_EVENTS: list[dict[str, Any]] = [
    {"type": "response.created", "response": {"id": "resp_2", "model": "gpt-6.1-sol"}},
    {"type": "response.in_progress", "response": {"id": "resp_2"}},
    {
        "type": "response.output_item.added",
        "output_index": 0,
        "item": {
            "type": "function_call",
            "call_id": "call_9",
            "name": LONG_WIRE,
            "namespace": "qma",
            "arguments": "",
        },
    },
    {"type": "response.function_call_arguments.delta", "output_index": 0, "delta": '{"word":'},
    {"type": "response.function_call_arguments.delta", "output_index": 0, "delta": '"pineapple"}'},
    {"type": "response.function_call_arguments.done", "output_index": 0},
    {
        "type": "response.output_item.done",
        "output_index": 0,
        "item": {
            "type": "function_call",
            "call_id": "call_9",
            "name": LONG_WIRE,
            "namespace": "qma",
            "arguments": '{"word":"pineapple"}',
        },
    },
    {
        "type": "response.completed",
        "response": {"output": [], "usage": {"input_tokens": 50, "output_tokens": 12}},
    },
]


def test_a_namespaced_function_call_becomes_a_tool_use_with_the_claude_name() -> None:
    state = StreamState(Translation({}, {LONG_WIRE: LONG_TOOL}), "gpt-6.1-sol")
    assert feed_all(state, TOOL_EVENTS)[1:] == [
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "tool_use", "id": "call_9", "name": LONG_TOOL, "input": {}},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "input_json_delta", "partial_json": '{"word":'},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "input_json_delta", "partial_json": '"pineapple"}'},
        },
        {"type": "content_block_stop", "index": 0},
        {
            "type": "message_delta",
            "delta": {"stop_reason": "tool_use", "stop_sequence": None},
            "usage": {"input_tokens": 50, "output_tokens": 12, "cache_read_input_tokens": 0},
        },
        {"type": "message_stop"},
    ]


def test_a_call_whose_arguments_arrive_only_at_done_still_sends_them() -> None:
    events = [TOOL_EVENTS[0], TOOL_EVENTS[2], TOOL_EVENTS[6], TOOL_EVENTS[7]]
    state = StreamState(Translation({}, {}), "gpt-6.1-sol")
    deltas = [e for e in feed_all(state, events) if e["type"] == "content_block_delta"]
    assert deltas == [
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "input_json_delta", "partial_json": '{"word":"pineapple"}'},
        }
    ]


def test_a_non_streaming_request_gets_one_assembled_message() -> None:
    state = StreamState(Translation({}, {LONG_WIRE: LONG_TOOL}), "gpt-6.1-sol")
    text = [*HELLO_EVENTS[:7], HELLO_EVENTS[8]]
    feed_all(state, [*text, *TOOL_EVENTS[2:]])
    assert state.message() == {
        "id": "msg_resp_1",
        "type": "message",
        "role": "assistant",
        "model": "gpt-6.1-sol",
        "content": [
            {"type": "text", "text": "hello from QMA"},
            {"type": "tool_use", "id": "call_9", "name": LONG_TOOL, "input": {"word": "pineapple"}},
        ],
        "stop_reason": "tool_use",
        "stop_sequence": None,
        "usage": {"input_tokens": 50, "output_tokens": 12, "cache_read_input_tokens": 0},
    }


def test_a_usage_limit_mid_stream_becomes_a_rate_limit_error_event() -> None:
    state = StreamState(Translation({}, {}), "gpt-6.1-sol")
    failed = {
        "type": "response.failed",
        "response": {
            "error": {
                "code": "subscription_sharing_usage_limit_exceeded",
                "message": "You have reached your usage limit.",
            }
        },
    }
    assert feed_all(state, [HELLO_EVENTS[0], failed])[1] == {
        "type": "error",
        "error": {
            "type": "rate_limit_error",
            "message": "ChatGPT: You have reached your usage limit.",
        },
    }
    assert state.ended
    assert state.error == (429, "rate_limit_error", "ChatGPT: You have reached your usage limit.")


@pytest.mark.parametrize(
    ("status", "error", "mapped"),
    [
        (
            400,
            {"message": "Unsupported parameter: temperature", "code": None, "param": None},
            (400, "invalid_request_error", "ChatGPT: Unsupported parameter: temperature"),
        ),
        (
            400,
            {"message": "System messages are not allowed", "code": None, "param": None},
            (400, "invalid_request_error", "ChatGPT: System messages are not allowed"),
        ),
        (
            429,
            {"code": "subscription_sharing_usage_limit_exceeded", "message": "Limit reached"},
            (429, "rate_limit_error", "ChatGPT: Limit reached"),
        ),
        (
            400,
            {
                "code": "subscription_sharing_unsupported_capability",
                "message": "Not here",
                "param": "include",
            },
            (400, "invalid_request_error", "ChatGPT: Not here (unsupported: include)"),
        ),
        (
            403,
            {"code": "subscription_sharing_user_not_eligible", "message": "Plan not eligible"},
            (403, "permission_error", "ChatGPT: Plan not eligible"),
        ),
        (
            403,
            {"code": "subscription_sharing_route_not_supported", "message": "No route"},
            (403, "permission_error", "ChatGPT: No route"),
        ),
        (
            401,
            {"message": "Invalid token"},
            (401, "authentication_error", "ChatGPT: Invalid token; type /login chatgpt"),
        ),
        (503, {}, (502, "api_error", "ChatGPT: the ChatGPT route returned an error")),
    ],
)
def test_map_error(status: int, error: dict[str, Any], mapped: tuple[int, str, str]) -> None:
    assert map_error(status, error) == mapped


def test_count_tokens_is_a_local_estimate_of_four_characters_a_token() -> None:
    request: dict[str, Any] = {"model": "gpt-6.1-sol", "system": "abcd" * 10, "messages": []}
    assert estimate_tokens(request) == 21


def test_parse_sse_reads_one_block_and_skips_done() -> None:
    assert parse_sse(["event: response.created", 'data: {"type": "response.created"}']) == [
        {"type": "response.created"}
    ]
    assert parse_sse(["data: [DONE]"]) == []


def test_system_role_messages_join_the_instructions_in_order() -> None:
    request = {
        "system": [{"type": "text", "text": "You are Claude Code."}],
        "messages": [
            {"role": "system", "content": "# Environment"},
            {"role": "user", "content": "hi"},
            {"role": "system", "content": [{"type": "text", "text": "Reminder"}]},
        ],
    }
    body = to_responses(request, model="gpt-6.1-sol").body
    assert body["instructions"] == "You are Claude Code.\n\n# Environment\n\nReminder"
    assert body["input"] == [{"role": "user", "content": "hi"}]
