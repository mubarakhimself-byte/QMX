# ruff: noqa: S101
from __future__ import annotations

import base64
import hashlib
import json
import socket
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

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
    lines = _sse(
        {"type": "response.created", "response": {}},
        {"type": "response.output_text.delta", "delta": "hello "},
        {"type": "response.output_text.delta", "delta": "from QMA"},
        {"type": "response.completed", "response": {"output": []}},
    )
    result = p_gpt.fold_events(200, "req_1", 0.5, p_gpt.parse_sse(lines))

    assert result.completed
    assert result.text == "hello from QMA"
    assert result.event_types == (
        "response.created",
        "response.output_text.delta",
        "response.output_text.delta",
        "response.completed",
    )


def test_items_come_from_output_item_done_when_completed_output_is_empty() -> None:
    added = {
        "type": "function_call",
        "id": "fc_1",
        "status": "in_progress",
        "call_id": "call_1",
        "name": "echo_word",
        "arguments": "",
    }
    done = {**added, "status": "completed", "arguments": '{"word":"pineapple"}'}
    lines = _sse(
        {"type": "response.created", "response": {}},
        {"type": "response.in_progress", "response": {}},
        {"type": "response.output_item.added", "output_index": 0, "item": added},
        {"type": "response.function_call_arguments.delta", "output_index": 0, "delta": "{"},
        {
            "type": "response.function_call_arguments.done",
            "output_index": 0,
            "arguments": '{"word":"pineapple"}',
        },
        {"type": "response.output_item.done", "output_index": 0, "item": done},
        {"type": "response.completed", "response": {"output": []}},
    )
    result = p_gpt.fold_events(200, None, 3.2, p_gpt.parse_sse(lines))

    assert result.completed
    assert result.function_calls() == [done]
    assert p_gpt.replay_items(result.output, keep_reasoning=False) == [
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "echo_word",
            "arguments": '{"word":"pineapple"}',
        }
    ]


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


def test_a_busy_callback_port_moves_the_listener_to_the_next_port() -> None:
    with p_gpt.open_callback_server(ports=(0,)) as first:
        port = first.server_address[1]
        with p_gpt.open_callback_server(ports=(port, 0)) as second:
            assert second.server_address[1] != port


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

    assert p_gpt.scan_for_secrets([clean, leaky], {"at-secret", ""}) == [leaky]


def test_stop_rule_row_names_the_step() -> None:
    verdict = p_gpt.Verdict(
        outcome="not viable",
        model="gpt-6.1-sol",
        tools_shape=None,
        reasoning_replay=None,
        stopped_at="P2 (stop rule: subscription_sharing_user_not_eligible)",
        steps=(p_gpt.StepResult("P1", True, "3 models"),),
    )
    row = verdict.row()

    assert "not viable | stop rule at P2 (stop rule: subscription_sharing_user_not_eligible)" in row
    assert "P1 PASS: 3 models" in row


class StubRoute(BaseHTTPRequestHandler):
    not_eligible = False
    barred_keys = frozenset({"max_output_tokens", "temperature", "metadata"})

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        models = {"models": [{"slug": "gpt-stub", "visibility": "list"}]}
        self._send(200, "application/json", json.dumps(models).encode())

    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert self.headers["Authorization"] == "Bearer at-stub"
        if self.not_eligible:
            error = {"error": {"code": "subscription_sharing_user_not_eligible"}}
            self._send(403, "application/json", json.dumps(error).encode())
            return
        barred = sorted(self.barred_keys & body.keys())
        system = any(item.get("role") == "system" for item in body["input"])
        if barred or system:
            message = (
                f"Unsupported parameter: {barred[0]}"
                if barred
                else "System messages are not allowed"
            )
            error = {"error": {"message": message, "type": "invalid_request_error", "code": None}}
            self._send(400, "application/json", json.dumps(error).encode())
            return
        assert body["store"] is False and body["stream"] is True
        kinds = {item.get("type") for item in body["input"]}
        if "include" in body and "function_call_output" in kinds and "reasoning" not in kinds:
            error = {"error": {"code": "reasoning_not_replayed"}}
            self._send(400, "application/json", json.dumps(error).encode())
            return
        self._send(200, "text/event-stream", self._stream(body))

    def _stream(self, body: p_gpt.Json) -> bytes:
        output: list[dict[str, object]] = []
        answered = any(item.get("type") == "function_call_output" for item in body["input"])
        if body.get("tools") and not answered:
            if "include" in body:
                output.append({"type": "reasoning", "id": "rs_1", "encrypted_content": "blob"})
            output.append(
                {
                    "type": "function_call",
                    "id": "fc_1",
                    "call_id": "call_1",
                    "name": "echo_word",
                    "namespace": "qma",
                    "arguments": '{"word": "pineapple"}',
                }
            )
        events: list[p_gpt.Json] = [
            {"type": "response.created", "response": {}},
            {"type": "response.output_text.delta", "delta": "hello from QMA"},
            *(
                {"type": "response.output_item.done", "output_index": index, "item": item}
                for index, item in enumerate(output)
            ),
            {"type": "response.completed", "response": {"output": []}},
        ]
        return "".join(f"data: {json.dumps(e)}\n\n" for e in events).encode()

    def _send(self, status: int, kind: str, payload: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _serve(handler: type[BaseHTTPRequestHandler]) -> str:
    server = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


def _stub_session(monkeypatch: pytest.MonkeyPatch, handler: type[StubRoute]) -> p_gpt.Session:
    monkeypatch.setattr(p_gpt, "API", f"{_serve(handler)}/v1")
    session = p_gpt.Session(
        p_gpt.Registration("oaiapp_1", "urn:uuid:1", "rt-stub", ()), FakeVault()
    )
    session.accept({"access_token": "at-stub", "refresh_token": "rt-stub-2", "expires_in": 3600})
    return session


def test_chain_against_a_stub_route_reads_viable_and_leaves_no_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _stub_session(monkeypatch, StubRoute)
    ev = p_gpt.Evidence(tmp_path)
    verdict = p_gpt.run_chain(session, ev, model=None, perf_runs=2, perf_spacing_s=0)
    findings = tmp_path / "FINDINGS.md"
    findings.write_text(verdict.row(), encoding="utf-8")

    assert [(s.step, s.passed) for s in verdict.steps] == [
        ("P1", True),
        ("P2", True),
        ("P3-namespace", True),
        ("P3-plain", True),
        ("P4", True),
        ("P5", True),
        ("perf", True),
    ]
    assert (verdict.outcome, verdict.model, verdict.tools_shape, verdict.reasoning_replay) == (
        "viable",
        "gpt-stub",
        "namespace",
        True,
    )
    assert p_gpt.secrets_scan(session, ev, findings).passed
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "FINDINGS.md",
        "hp2-p1.log",
        "hp2-p2.log",
        "hp2-p3-namespace.log",
        "hp2-p3-plain.log",
        "hp2-p4.log",
        "hp2-p5.log",
        "hp2-perf.log",
        "hp2-secrets.log",
    ]


class LenientRoute(StubRoute):
    barred_keys = frozenset({"temperature", "metadata"})


def test_a_barred_field_the_route_accepts_is_recorded_and_the_chain_runs_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _stub_session(monkeypatch, LenientRoute)
    verdict = p_gpt.run_chain(
        session, p_gpt.Evidence(tmp_path), model=None, perf_runs=1, perf_spacing_s=0
    )

    assert [(s.step, s.passed) for s in verdict.steps][-2:] == [("P5", True), ("perf", True)]
    assert verdict.steps[-2].detail == (
        "refused ['temperature', 'metadata', 'system_role_item']; "
        "accepted ['max_output_tokens']; unclassified []"
    )
    assert verdict.row().split(" | ")[2:4] == ["viable", "model `gpt-stub`"]
    log = (tmp_path / "hp2-p5.log").read_text(encoding="utf-8")
    assert "max_output_tokens: http_status=200 outcome=accepted message=None" in log
    assert (
        "temperature: http_status=400 outcome=refused message='Unsupported parameter: temperature'"
        in log
    )
    assert (
        "system_role_item: http_status=400 outcome=refused "
        "message='System messages are not allowed'" in log
    )


class UnrelatedFourHundredRoute(StubRoute):
    barred_keys = frozenset()

    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        extra = set(body) - {"model", "input", "store", "stream", "instructions"}
        if extra or any(item.get("role") == "system" for item in body["input"]):
            error = {"error": {"message": "Rate of requests too high", "code": None}}
            self._send(400, "application/json", json.dumps(error).encode())
            return
        self._send(200, "text/event-stream", self._stream(body))


def test_p5_does_not_count_a_400_that_names_another_cause_as_the_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _stub_session(monkeypatch, UnrelatedFourHundredRoute)
    result = p_gpt.probe_barred(session, p_gpt.Evidence(tmp_path), "gpt-stub")

    assert (result.passed, result.detail) == (
        False,
        "refused []; accepted []; unclassified "
        "['max_output_tokens', 'temperature', 'metadata', 'system_role_item']",
    )
    log = (tmp_path / "hp2-p5.log").read_text(encoding="utf-8")
    assert (
        "metadata: http_status=400 outcome=unclassified message='Rate of requests too high'" in log
    )


class NotEligibleRoute(StubRoute):
    not_eligible = True


def test_chain_stops_at_p2_when_the_plan_is_not_eligible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _stub_session(monkeypatch, NotEligibleRoute)
    verdict = p_gpt.run_chain(
        session, p_gpt.Evidence(tmp_path), model=None, perf_runs=0, perf_spacing_s=0
    )

    assert verdict.outcome == "not viable"
    assert verdict.stopped_at == "P2 (stop rule: subscription_sharing_user_not_eligible)"
    assert [s.step for s in verdict.steps] == ["P1", "P2"]


class StubOpenAIAuth(BaseHTTPRequestHandler):
    """OpenAI's authorize and token endpoints, with the token endpoint's measured error
    codes: a missing parameter or a JSON body is invalid_request, dynamic_agent_client is
    invalid_client, and a code, verifier, redirect or client mismatch is invalid_grant."""

    issued = "oaiapp_stub"
    nonce: str | None = None
    rejected_exchanges = 0
    authorizations: list[dict[str, str]]
    exchanges: list[dict[str, str]]
    codes: dict[str, dict[str, str]]

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
        self.authorizations.append(params)
        code = f"code-{len(self.authorizations)}"
        self.codes[code] = params
        callback = {"code": code, "state": params["state"]}
        if params["client_id"] == p_gpt.REGISTRATION_CLIENT:
            callback["client_id"] = self.issued
        self.send_response(302)
        self.send_header("Location", f"{params['redirect_uri']}?{urllib.parse.urlencode(callback)}")
        self.end_headers()

    def do_POST(self) -> None:
        raw = self.rfile.read(int(self.headers["Content-Length"])).decode()
        if self.headers["Content-Type"] != "application/x-www-form-urlencoded":
            self._reply(400, {"error": "invalid_request"})
            return
        form = dict(urllib.parse.parse_qsl(raw))
        self.exchanges.append(form)
        if "client_id" not in form or "redirect_uri" not in form:
            self._reply(400, {"error": "invalid_request"})
            return
        if form["client_id"] == p_gpt.REGISTRATION_CLIENT:
            self._reply(400, {"error": "invalid_client"})
            return
        granted = self.codes.pop(form.get("code", ""), None)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(form.get("code_verifier", "").encode()).digest()
        ).rstrip(b"=")
        if (
            granted is None
            or len(self.exchanges) <= self.rejected_exchanges
            or granted["redirect_uri"] != form["redirect_uri"]
            or granted["code_challenge"] != challenge.decode()
            or granted["resource"] != form.get("resource")
            or form["client_id"] != self.issued
        ):
            self._reply(400, {"error": "invalid_grant"})
            return
        nonce = self.nonce or granted["nonce"]
        claims = {"iss": p_gpt.ISSUER, "aud": self.issued, "nonce": nonce}
        payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
        self._reply(
            200,
            {
                "access_token": "at-signin",
                "refresh_token": "rt-signin",
                "id_token": f"h.{payload}.s",
                "expires_in": 3600,
                "scope": "openid chatgpt.tokens.use.direct",
            },
        )

    def _reply(self, status: int, payload: p_gpt.Json) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("x-request-id", f"req-{len(self.exchanges)}")
        self.end_headers()
        self.wfile.write(body)


def _stub_auth(
    monkeypatch: pytest.MonkeyPatch, *, rejected: int, nonce: str | None = None
) -> type[StubOpenAIAuth]:
    handler = type(
        "Auth",
        (StubOpenAIAuth,),
        {
            "nonce": nonce,
            "rejected_exchanges": rejected,
            "authorizations": [],
            "exchanges": [],
            "codes": {},
        },
    )
    server = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    monkeypatch.setattr(p_gpt, "AUTHORIZE_URL", f"{base}/api/accounts/authorize")
    monkeypatch.setattr(p_gpt, "TOKEN_URL", f"{base}/api/accounts/oauth/token")

    def visit(url: str) -> None:
        with urllib.request.urlopen(url, timeout=10) as response:  # noqa: S310
            response.read()

    def browser(url: str) -> bool:
        threading.Thread(target=visit, args=(url,)).start()
        return True

    monkeypatch.setattr(p_gpt.webbrowser, "open", browser)
    return handler


def test_new_registration_exchanges_the_code_with_the_issued_client_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = _stub_auth(monkeypatch, rejected=0)
    vault = FakeVault()
    lines: list[str] = []
    session = p_gpt.sign_in(vault, timeout_s=10, log=lines.append)

    assert [a["client_id"] for a in auth.authorizations] == ["dynamic_agent_client"]
    assert [e["client_id"] for e in auth.exchanges] == ["oaiapp_stub"]
    assert session.registration.scopes == ("chatgpt.tokens.use.direct", "openid")
    assert json.loads(vault.value or "{}")["refresh_token"] == "rt-signin"  # noqa: S105


def test_invalid_grant_on_first_exchange_reauthorizes_with_the_issued_client_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = _stub_auth(monkeypatch, rejected=1)
    vault = FakeVault()
    lines: list[str] = []
    session = p_gpt.sign_in(vault, timeout_s=10, log=lines.append)

    assert [a["client_id"] for a in auth.authorizations] == [
        "dynamic_agent_client",
        "oaiapp_stub",
    ]
    assert "agent_name_hint" not in auth.authorizations[1]
    assert (
        auth.authorizations[0]["ext_agent_host_id"] == auth.authorizations[1]["ext_agent_host_id"]
    )
    assert [e["code"] for e in auth.exchanges] == ["code-1", "code-2"]
    assert session.registration.client_id == "oaiapp_stub"
    assert "exchange_1: http 400 invalid_grant request_id=req-1" in "\n".join(lines)
    assert not any("code-" in line or "rt-signin" in line for line in lines)


def test_two_rejected_codes_keep_the_issued_client_id_for_the_next_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_auth(monkeypatch, rejected=2)
    vault = FakeVault()

    with pytest.raises(p_gpt.SignInError, match="invalid_grant"):
        p_gpt.sign_in(vault, timeout_s=10, log=lambda _: None)

    assert json.loads(vault.value or "{}")["client_id"] == "oaiapp_stub"
    with pytest.raises(p_gpt.SignInError, match="no refresh token"):
        p_gpt.load_session(vault)


def test_token_error_names_the_code_request_id_and_its_meaning() -> None:
    reply = p_gpt.HttpReply(400, b'{"error": "invalid_request"}', "req-9")

    assert p_gpt.token_error(reply).startswith(
        "http 400 invalid_request request_id=req-9: request bug"
    )


class NoNamespaceRoute(StubRoute):
    def _stream(self, body: p_gpt.Json) -> bytes:
        return super()._stream(body).decode().replace('"namespace": "qma", ', "").encode()


def test_namespace_shape_fails_when_the_call_names_no_namespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _stub_session(monkeypatch, NoNamespaceRoute)
    ev = p_gpt.Evidence(tmp_path)

    namespace = p_gpt.probe_tools(session, ev, "gpt-stub", "namespace")
    plain = p_gpt.probe_tools(session, ev, "gpt-stub", "plain")

    assert (namespace.passed, namespace.detail) == (
        False,
        "call echo_word namespace=None (expected qma), turn2 response.completed",
    )
    assert (plain.passed, plain.detail) == (
        True,
        "call echo_word namespace=None, turn2 response.completed",
    )


class NoToolCallRoute(StubRoute):
    def _stream(self, body: p_gpt.Json) -> bytes:
        return super()._stream({**body, "tools": []})


def test_chain_stops_as_not_viable_when_both_tool_shapes_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _stub_session(monkeypatch, NoToolCallRoute)
    verdict = p_gpt.run_chain(
        session, p_gpt.Evidence(tmp_path), model=None, perf_runs=0, perf_spacing_s=0
    )

    assert [(s.step, s.passed) for s in verdict.steps] == [
        ("P1", True),
        ("P2", True),
        ("P3-namespace", False),
        ("P3-plain", False),
    ]
    assert verdict.row().split(" | ")[2:4] == [
        "not viable",
        "stop rule at P3 (both tool shapes failed)",
    ]


class TurnTwoFailsRoute(StubRoute):
    def _stream(self, body: p_gpt.Json) -> bytes:
        if any(item.get("type") == "function_call_output" for item in body["input"]):
            event = {"type": "response.failed", "response": {"error": {"code": "server_error"}}}
            return f"data: {json.dumps(event)}\n\n".encode()
        return super()._stream(body)


def test_p3_fails_when_turn_two_does_not_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _stub_session(monkeypatch, TurnTwoFailsRoute)
    result = p_gpt.probe_tools(session, p_gpt.Evidence(tmp_path), "gpt-stub", "plain")

    assert (result.passed, result.detail) == (
        False,
        "call echo_word namespace=qma, turn2 response.failed",
    )


class NoTerminalRoute(StubRoute):
    def _stream(self, body: p_gpt.Json) -> bytes:
        event = {"type": "response.output_text.delta", "delta": "hello from QMA"}
        return f"data: {json.dumps(event)}\n\n".encode()


class RateLimitedRoute(StubRoute):
    def do_POST(self) -> None:
        self.rfile.read(int(self.headers["Content-Length"]))
        error = {"error": {"code": "subscription_sharing_usage_limit_exceeded"}}
        self._send(429, "application/json", json.dumps(error).encode())


class ModelsDownRoute(StubRoute):
    def do_GET(self) -> None:
        self._send(503, "application/json", b'{"detail": "busy"}')


@pytest.mark.parametrize(
    ("route", "stopped"),
    [
        (NoTerminalRoute, "P2 (no response.completed (status 200, code None))"),
        (
            RateLimitedRoute,
            "P2 (no response.completed (status 429, code "
            "subscription_sharing_usage_limit_exceeded))",
        ),
        (ModelsDownRoute, "P1 (/v1/models returned 503)"),
    ],
)
def test_a_failure_outside_the_stop_rule_is_inconclusive_not_unviable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: type[StubRoute], stopped: str
) -> None:
    session = _stub_session(monkeypatch, route)
    verdict = p_gpt.run_chain(
        session, p_gpt.Evidence(tmp_path), model=None, perf_runs=0, perf_spacing_s=0
    )

    assert verdict.row().split(" | ")[2:4] == ["inconclusive", f"rerun: {stopped}"]


def test_perf_fails_when_the_median_exceeds_the_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _stub_session(monkeypatch, StubRoute)
    ev = p_gpt.Evidence(tmp_path)
    assert p_gpt.perf_series(session, ev, "gpt-stub", 2, 0).passed

    monkeypatch.setattr(p_gpt, "PERF_LIMIT_S", 0.0)
    assert not p_gpt.perf_series(session, ev, "gpt-stub", 2, 0).passed


def test_an_id_token_with_another_nonce_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_auth(monkeypatch, rejected=0, nonce="replayed")

    with pytest.raises(p_gpt.SignInError, match="nonce"):
        p_gpt.sign_in(FakeVault(), timeout_s=10, log=lambda _: None)


def test_secrets_scan_reads_subfolders_and_lists_only_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _stub_session(monkeypatch, StubRoute)
    (tmp_path / "run1").mkdir()
    old = tmp_path / "run1" / "old.log"
    old.write_text("Bearer at-stub\n", encoding="utf-8")
    findings = tmp_path / "FINDINGS.md"
    findings.write_text("clean", encoding="utf-8")

    result = p_gpt.secrets_scan(session, p_gpt.Evidence(tmp_path), findings)

    assert (result.passed, result.detail) == (False, "1 files hold a token value")
    log = (tmp_path / "hp2-secrets.log").read_text(encoding="utf-8")
    assert [line for line in log.splitlines() if line.startswith("scanned:")] == [
        f"scanned: {findings}",
        f"scanned: {old}",
    ]


class StubRefresh(BaseHTTPRequestHandler):
    scope = "openid chatgpt.tokens.use.direct"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        raw = self.rfile.read(int(self.headers["Content-Length"])).decode()
        assert dict(urllib.parse.parse_qsl(raw))["grant_type"] == "refresh_token"
        tokens = {
            "access_token": "at-stub",
            "refresh_token": "rt-stub-3",
            "expires_in": 3600,
            "scope": self.scope,
        }
        body = json.dumps(tokens).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _reuse_args(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, scope: str = StubRefresh.scope
) -> list[str]:
    monkeypatch.setattr(p_gpt, "API", f"{_serve(StubRoute)}/v1")
    refresh = type("Refresh", (StubRefresh,), {"scope": scope})
    monkeypatch.setattr(p_gpt, "TOKEN_URL", f"{_serve(refresh)}/api/accounts/oauth/token")
    vault = FakeVault()
    vault.set(
        p_gpt.Registration("oaiapp_1", "urn:uuid:1", "rt-stub", (p_gpt.DIRECT_SCOPE,)).dumps()
    )
    monkeypatch.setattr(p_gpt, "KeyringVault", lambda: vault)
    findings = tmp_path / "FINDINGS.md"
    findings.write_text("clean", encoding="utf-8")
    evidence = tmp_path / "ev"
    return [
        "run",
        "--reuse",
        "--evidence",
        str(evidence),
        "--findings",
        str(findings),
        "--perf-runs",
        "3",
        "--perf-spacing",
        "0",
    ]


def test_reuse_stops_when_the_refreshed_grant_lacks_the_direct_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _reuse_args(monkeypatch, tmp_path, scope="openid offline_access")

    assert p_gpt.main(args) == 1
    log = (tmp_path / "ev" / "hp2-reuse.log").read_text(encoding="utf-8")
    assert "result: FAIL chatgpt.tokens.use.direct granted=False (scopes from refresh reply)" in log
    assert not (tmp_path / "ev" / "hp2-p1.log").exists()


def test_reuse_with_the_direct_scope_runs_the_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _reuse_args(monkeypatch, tmp_path)

    assert p_gpt.main(args) == 0
    log = (tmp_path / "ev" / "hp2-reuse.log").read_text(encoding="utf-8")
    assert "result: PASS chatgpt.tokens.use.direct granted=True (scopes from refresh reply)" in log
    verdict = json.loads((tmp_path / "ev" / "hp2-verdict.json").read_text(encoding="utf-8"))
    assert verdict["outcome"] == "viable"


def test_a_network_error_mid_chain_still_writes_the_verdict_and_scans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _reuse_args(monkeypatch, tmp_path)
    real = urllib.request.urlopen
    responses: list[str] = []

    def flaky(request: urllib.request.Request, *rest: Any, **kw: Any) -> Any:
        if request.full_url.endswith("/responses"):
            responses.append(request.full_url)
            if len(responses) == 13:
                raise urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed"))
        return real(request, *rest, **kw)

    monkeypatch.setattr(p_gpt.urllib.request, "urlopen", flaky)

    assert p_gpt.main(args) == 1
    evidence = tmp_path / "ev"
    verdict = json.loads((evidence / "hp2-verdict.json").read_text(encoding="utf-8"))
    assert (verdict["outcome"], verdict["steps"][-1]["detail"]) == ("viable", "2 of 3 completed")
    perf = (evidence / "hp2-perf.log").read_text(encoding="utf-8")
    assert "run 2: first_byte_s=None terminal=None error=" in perf
    assert "getaddrinfo failed" in perf
    assert (evidence / "hp2-secrets.log").read_text(encoding="utf-8").endswith("result: PASS\n")
