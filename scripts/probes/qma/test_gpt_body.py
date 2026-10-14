# ruff: noqa: S101
from __future__ import annotations

import base64
import hashlib
import json
import threading
import urllib.parse
import urllib.request
from pathlib import Path

import p_gpt
import pytest

ANTHROPIC_REQUEST = {
    "model": "gpt-6.1-sol",
    "system": [
        {"type": "text", "text": "You are QMA."},
        {"type": "text", "text": "Be terse.", "cache_control": {"type": "ephemeral"}},
    ],
    "messages": [{"role": "user", "content": "hello"}],
    "max_tokens": 32000,
    "temperature": 1,
    "top_p": 0.9,
    "metadata": {"user_id": "u"},
    "stop_sequences": ["x"],
}

TOOL = {
    "name": "Bash",
    "description": "Run a command.",
    "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}},
}


def test_body_is_store_false_stream_true_without_barred_fields() -> None:
    body = p_gpt.responses_body(ANTHROPIC_REQUEST)

    assert body == {
        "model": "gpt-6.1-sol",
        "instructions": "You are QMA.\n\nBe terse.",
        "input": [{"role": "user", "content": "hello"}],
        "store": False,
        "stream": True,
    }


def test_string_system_moves_into_instructions_and_never_into_input() -> None:
    body = p_gpt.responses_body({**ANTHROPIC_REQUEST, "system": "Only this."})

    assert body["instructions"] == "Only this."
    assert all(item.get("role") != "system" for item in body["input"])


def test_tools_are_wrapped_in_the_qma_namespace() -> None:
    body = p_gpt.responses_body({**ANTHROPIC_REQUEST, "tools": [TOOL]})

    assert body["tools"] == [
        {
            "type": "namespace",
            "name": "qma",
            "description": "QMA tools",
            "tools": [
                {
                    "type": "function",
                    "name": "Bash",
                    "description": "Run a command.",
                    "parameters": TOOL["input_schema"],
                }
            ],
        }
    ]


def test_plain_shape_sends_top_level_functions() -> None:
    body = p_gpt.responses_body({**ANTHROPIC_REQUEST, "tools": [TOOL]}, tools_shape="plain")

    assert body["tools"] == [
        {
            "type": "function",
            "name": "Bash",
            "description": "Run a command.",
            "parameters": TOOL["input_schema"],
        }
    ]


def test_reasoning_include_only_when_asked() -> None:
    assert "include" not in p_gpt.responses_body(ANTHROPIC_REQUEST)
    body = p_gpt.responses_body(ANTHROPIC_REQUEST, include_reasoning=True)
    assert body["include"] == ["reasoning.encrypted_content"]


def test_tool_use_and_tool_result_map_to_function_items_in_order() -> None:
    messages = [
        {"role": "user", "content": "run it"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Running."},
                {"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": "ls"}},
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_1",
                    "content": [{"type": "text", "text": "a.txt"}],
                },
                {"type": "text", "text": "now say done"},
            ],
        },
    ]
    body = p_gpt.responses_body({**ANTHROPIC_REQUEST, "messages": messages})

    assert body["input"] == [
        {"role": "user", "content": "run it"},
        {"role": "assistant", "content": "Running."},
        {
            "type": "function_call",
            "call_id": "toolu_1",
            "name": "Bash",
            "arguments": '{"command": "ls"}',
        },
        {"type": "function_call_output", "call_id": "toolu_1", "output": "a.txt"},
        {"role": "user", "content": "now say done"},
    ]


def test_unknown_content_block_is_refused() -> None:
    messages = [{"role": "user", "content": [{"type": "audio", "data": "..."}]}]
    with pytest.raises(ValueError, match="audio"):
        p_gpt.responses_body({**ANTHROPIC_REQUEST, "messages": messages})


def _sse(*events: dict[str, object]) -> list[str]:
    lines: list[str] = []
    for event in events:
        lines += [f"event: {event['type']}\n", f"data: {json.dumps(event)}\n", "\n"]
    return lines


def test_stream_with_response_completed_is_a_success() -> None:
    call = {"type": "function_call", "id": "fc_1", "call_id": "c1", "name": "echo_word"}
    lines = _sse(
        {"type": "response.created", "response": {}},
        {"type": "response.output_text.delta", "delta": "hello "},
        {"type": "response.output_text.delta", "delta": "from QMA"},
        {"type": "response.completed", "response": {"output": [call]}},
    )
    result = p_gpt.fold_events(200, "req_1", 0.5, p_gpt.parse_sse(lines))

    assert result.completed
    assert result.text == "hello from QMA"
    assert result.function_calls() == [call]
    assert result.event_types == (
        "response.created",
        "response.output_text.delta",
        "response.output_text.delta",
        "response.completed",
    )


def test_usage_limit_mid_stream_is_not_a_success() -> None:
    lines = _sse(
        {"type": "response.output_text.delta", "delta": "hel"},
        {
            "type": "response.failed",
            "response": {"error": {"code": "subscription_sharing_usage_limit_exceeded"}},
        },
    )
    result = p_gpt.fold_events(200, None, 0.1, p_gpt.parse_sse(lines))

    assert not result.completed
    assert result.terminal == "response.failed"
    assert result.error_code == "subscription_sharing_usage_limit_exceeded"


def test_stream_that_ends_without_a_terminal_event_is_not_a_success() -> None:
    lines = _sse({"type": "response.output_text.delta", "delta": "hel"})
    assert not p_gpt.fold_events(200, None, 0.1, p_gpt.parse_sse(lines)).completed


def test_error_body_keeps_code_and_param() -> None:
    raw = json.dumps(
        {
            "error": {
                "code": "subscription_sharing_unsupported_capability",
                "param": "temperature",
                "message": "no",
            }
        }
    ).encode()
    result = p_gpt.error_result(400, "req_9", raw)

    assert (result.status, result.error_code, result.error_param) == (
        400,
        "subscription_sharing_unsupported_capability",
        "temperature",
    )


def test_admission_detail_body_is_kept_as_message() -> None:
    result = p_gpt.error_result(503, None, b'{"detail":"direct routing unavailable"}')
    assert (result.error_code, result.error_message) == (None, "direct routing unavailable")


def test_replay_drops_ids_and_reasoning_without_encrypted_content() -> None:
    output: list[p_gpt.Json] = [
        {"type": "reasoning", "id": "rs_1", "summary": []},
        {"type": "reasoning", "id": "rs_2", "summary": [], "encrypted_content": "blob"},
        {"type": "message", "id": "msg_1", "content": []},
        {
            "type": "function_call",
            "id": "fc_1",
            "status": "completed",
            "call_id": "c1",
            "name": "echo_word",
            "namespace": "qma",
            "arguments": "{}",
        },
    ]
    call = {
        "type": "function_call",
        "call_id": "c1",
        "name": "echo_word",
        "namespace": "qma",
        "arguments": "{}",
    }

    assert p_gpt.replay_items(output, keep_reasoning=False) == [call]
    assert p_gpt.replay_items(output, keep_reasoning=True) == [
        {"type": "reasoning", "summary": [], "encrypted_content": "blob"},
        call,
    ]


def test_model_slugs_keep_listed_models_in_server_order() -> None:
    payload = {
        "models": [
            {"slug": "gpt-6.1-sol", "visibility": "list"},
            {"slug": "gpt-internal", "visibility": "hide"},
            {"slug": "gpt-6-astra", "visibility": "list"},
        ]
    }
    assert p_gpt.model_slugs(payload) == ["gpt-6.1-sol", "gpt-6-astra"]


def test_first_registration_url_names_qma_and_uses_s256() -> None:
    verifier, challenge = p_gpt.pkce_pair()
    url = p_gpt.authorize_url(
        client_id="dynamic_agent_client",
        host_id="urn:uuid:1",
        redirect_uri="http://127.0.0.1:1455/auth/callback",
        state="s",
        nonce="n",
        challenge=challenge,
    )
    base, query = url.split("?", 1)
    params = dict(urllib.parse.parse_qsl(query))
    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=")

    assert base == "https://auth.openai.com/api/accounts/authorize"
    assert params["agent_name_hint"] == "QMA"
    assert params["code_challenge"] == expected.decode()
    assert params["code_challenge_method"] == "S256"
    assert params["scope"].split() == [
        "openid",
        "profile",
        "email",
        "offline_access",
        "resource.invoke",
        "chatgpt.tokens.use.direct",
    ]
    assert params["resource"] == "https://api.openai.com/v1"


def test_reauthorization_url_omits_agent_name_hint() -> None:
    url = p_gpt.authorize_url(
        client_id="oaiapp_x",
        host_id="urn:uuid:1",
        redirect_uri="http://127.0.0.1:1455/auth/callback",
        state="s",
        nonce="n",
        challenge="c",
    )
    assert "agent_name_hint" not in url


def test_callback_with_wrong_state_or_denial_is_refused() -> None:
    with pytest.raises(p_gpt.SignInError, match="state"):
        p_gpt.parse_callback({"state": "other", "code": "c"}, "mine")
    with pytest.raises(p_gpt.SignInError, match="access_denied"):
        p_gpt.parse_callback({"state": "mine", "error": "access_denied"}, "mine")


def test_loopback_listener_hands_back_the_callback_query() -> None:
    server = p_gpt.open_callback_server(ports=(0,))
    port = server.server_address[1]
    with server:
        waiter = threading.Thread(target=p_gpt.wait_for_callback, args=(server, 10))
        waiter.start()
        url = f"http://127.0.0.1:{port}/auth/callback?code=abc&state=st&client_id=oaiapp_1"
        with urllib.request.urlopen(url, timeout=5) as response:
            page = response.read()
        waiter.join(10)

    assert b"QMA sign-in received" in page
    assert p_gpt.parse_callback(server.query or {}, "st") == p_gpt.Callback("abc", "oaiapp_1", None)


class FakeVault:
    def __init__(self) -> None:
        self.value: str | None = None

    def get(self) -> str | None:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


def test_token_response_stores_rotated_refresh_token_and_never_the_access_token() -> None:
    vault = FakeVault()
    registration = p_gpt.Registration("oaiapp_1", "urn:uuid:1", "rt-old", ())
    session = p_gpt.Session(registration, vault)
    session.accept(
        {
            "access_token": "at-secret",
            "refresh_token": "rt-new",
            "expires_in": 3600,
            "scope": "openid chatgpt.tokens.use.direct",
        }
    )
    stored = json.loads(vault.value or "{}")

    assert stored == {
        "client_id": "oaiapp_1",
        "host_id": "urn:uuid:1",
        "refresh_token": "rt-new",
        "scopes": ["chatgpt.tokens.use.direct", "openid"],
        "earliest_refresh_at": None,
    }
    assert session.access_token() == "at-secret"
    assert session.secrets_seen == {"rt-old", "rt-new", "at-secret"}


def test_earliest_refresh_at_accepts_seconds_and_iso() -> None:
    assert p_gpt.epoch_seconds(1790032532) == 1790032532.0
    assert p_gpt.epoch_seconds("2026-10-14T00:00:00Z") == 1791936000.0
    assert p_gpt.epoch_seconds(None) is None


def test_secret_scan_names_only_files_holding_a_value(tmp_path: Path) -> None:
    clean = tmp_path / "hp2-p2.log"
    leaky = tmp_path / "hp2-p3.log"
    clean.write_text("http_status: 200\n", encoding="utf-8")
    leaky.write_text("Authorization: Bearer at-secret\n", encoding="utf-8")

    assert p_gpt.scan_for_secrets([clean, leaky, tmp_path / "missing.md"], {"at-secret", ""}) == [
        leaky
    ]


def test_stop_rule_row_names_the_step() -> None:
    verdict = p_gpt.Verdict(
        viable=False,
        model="gpt-6.1-sol",
        tools_shape=None,
        reasoning_replay=None,
        stopped_at="P2 (stop rule: subscription_sharing_user_not_eligible)",
        steps=(p_gpt.StepResult("P1", True, "3 models"),),
    )
    row = verdict.row()

    assert "not viable | stop rule at P2 (stop rule: subscription_sharing_user_not_eligible)" in row
    assert "P1 PASS: 3 models" in row
