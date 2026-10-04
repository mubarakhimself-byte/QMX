"""Loopback-only HTTP/SSE tests; no external inference or real credentials."""

from __future__ import annotations

import http.client
import json
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest
from qma.daemon.request_runtime import http_provider
from qma.daemon.request_runtime.contracts import ProviderEvent, ProviderRequest
from qma.daemon.request_runtime.http_provider import ChatCompletionsProvider
from qma.daemon.request_runtime.providers import ProviderError


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    mode: str = "json"
    calls: int = 0
    payload: dict[str, Any]
    authorization: str | None = None
    dispatched: threading.Event

    def handle_error(self, request: object, client_address: object) -> None:
        # Interrupted local fake connections are expected in cancellation tests.
        pass


def _chunk(content: str | None = None, reason: str | None = None) -> bytes:
    delta = {} if content is None else {"content": content}
    return (
        "data: "
        + json.dumps({"choices": [{"index": 0, "delta": delta, "finish_reason": reason}]})
        + "\n\n"
    ).encode()


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        server: _Server = self.server  # type: ignore[assignment]
        server.calls += 1
        server.payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        server.authorization = self.headers.get("Authorization")
        server.dispatched.set()
        mode = server.mode
        if mode == "stall":
            time.sleep(2)
            return
        if mode in {"auth", "quota", "redirect", "error"}:
            self.send_response({"auth": 401, "quota": 429, "redirect": 307, "error": 500}[mode])
            self.send_header("Location", "http://127.0.0.1:9/stolen")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header(
            "Content-Type", "text/event-stream" if mode.startswith("sse") else "application/json"
        )
        self.end_headers()
        try:
            if mode.startswith("sse"):
                if mode == "sse_malformed":
                    self.wfile.write(b"data: nope\n\n")
                elif mode == "sse_tool":
                    self.wfile.write(
                        b'data: {"choices":[{"delta":{"tool_calls":[{}]},'
                        b'"finish_reason":null}]}\n\n'
                    )
                elif mode == "sse_large":
                    self.wfile.write(b"data: " + b"x" * 70000 + b"\n\n")
                else:
                    self.wfile.write(b": comment\n\n" + _chunk("hello ") + _chunk("world"))
                    self.wfile.flush()
                    if mode == "sse_stall":
                        time.sleep(2)
                        return
                    if mode != "sse_truncated":
                        self.wfile.write(
                            _chunk(reason="length" if mode == "sse_length" else "stop")
                        )
                        self.wfile.write(b'data: {"choices":[],"usage":{"total_tokens":1}}\n\n')
                        self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
                return
            if mode == "malformed":
                self.wfile.write(b"nope")
                return
            message: dict[str, Any] = {"role": "assistant", "content": "hello world"}
            if mode == "tool":
                message["tool_calls"] = [{"function": {"name": "danger"}}]
            if mode == "large":
                message["content"] = "x" * 600000
            reason = "length" if mode == "length" else "stop"
            self.wfile.write(
                json.dumps(
                    {"choices": [{"index": 0, "message": message, "finish_reason": reason}]}
                ).encode()
            )
        except BrokenPipeError, ConnectionResetError:
            pass

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def server() -> Iterator[_Server]:
    instance = _Server(("127.0.0.1", 0), _Handler)
    instance.dispatched = threading.Event()
    thread = threading.Thread(
        target=instance.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
    )
    thread.start()
    try:
        yield instance
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=1)


def adapter(
    server: _Server, *, stream: bool = False, api_key_env: str | None = None
) -> ChatCompletionsProvider:
    return ChatCompletionsProvider(
        f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
        "fake-model",
        deployment_id="local-fake",
        stream=stream,
        api_key_env=api_key_env,
    )


def test_json_post_has_explicit_model_no_tools(server: _Server) -> None:
    result = adapter(server).execute(
        ProviderRequest("hi", instructions="be concise"), lambda _: None, threading.Event()
    )
    assert result.content == "hello world"
    assert result.deployment_id == "local-fake"
    assert server.calls == 1
    assert server.payload == {
        "model": "fake-model",
        "messages": [
            {"role": "system", "content": "be concise"},
            {"role": "user", "content": "hi"},
        ],
        "stream": False,
        "n": 1,
    }
    assert server.authorization is None


def test_sse_text_usage_and_done(server: _Server) -> None:
    server.mode = "sse"
    events: list[ProviderEvent] = []
    result = adapter(server, stream=True).execute(
        ProviderRequest("hi"), events.append, threading.Event()
    )
    assert result.content == "hello world"
    assert [event.payload["delta"] for event in events] == ["hello ", "world"]


@pytest.mark.parametrize(
    ("mode", "code"),
    [
        ("auth", "auth_required"),
        ("quota", "rate_limited"),
        ("redirect", "http_rejected"),
        ("error", "http_rejected"),
        ("malformed", "outcome_unknown"),
        ("tool", "outcome_unknown"),
        ("length", "incomplete"),
        ("large", "outcome_unknown"),
        ("sse_malformed", "outcome_unknown"),
        ("sse_tool", "outcome_unknown"),
        ("sse_large", "outcome_unknown"),
        ("sse_truncated", "outcome_unknown"),
        ("sse_length", "incomplete"),
    ],
)
def test_failures_never_retry(server: _Server, mode: str, code: str) -> None:
    server.mode = mode
    with pytest.raises(ProviderError) as error:
        adapter(server, stream=mode.startswith("sse")).execute(
            ProviderRequest("hi"), lambda _: None, threading.Event()
        )
    assert error.value.code == code
    assert server.calls == 1


def test_deadline_and_cancel_after_dispatch_are_unknown(server: _Server) -> None:
    server.mode = "stall"
    started = time.monotonic()
    with pytest.raises(ProviderError) as error:
        adapter(server).execute(
            ProviderRequest("hi", timeout_seconds=0.1), lambda _: None, threading.Event()
        )
    assert error.value.code == "outcome_unknown"
    assert time.monotonic() - started < 0.8


def test_cancel_during_sse_is_unknown(server: _Server) -> None:
    server.mode = "sse_stall"
    cancellation = threading.Event()

    def emit(event: ProviderEvent) -> None:
        if event.name == "text_delta":
            cancellation.set()

    with pytest.raises(ProviderError) as error:
        adapter(server, stream=True).execute(ProviderRequest("hi"), emit, cancellation)
    assert error.value.code == "outcome_unknown"


def test_precancel_and_missing_key_dispatch_nothing(
    server: _Server, monkeypatch: pytest.MonkeyPatch
) -> None:
    cancellation = threading.Event()
    cancellation.set()
    with pytest.raises(ProviderError) as error:
        adapter(server).execute(ProviderRequest("hi"), lambda _: None, cancellation)
    assert error.value.code == "cancelled"
    monkeypatch.delenv("QMA_FAKE_HTTP_KEY", raising=False)
    with pytest.raises(ProviderError) as error:
        adapter(server, api_key_env="QMA_FAKE_HTTP_KEY").execute(
            ProviderRequest("hi"), lambda _: None, threading.Event()
        )
    assert error.value.code == "auth_required"
    assert server.calls == 0


def test_explicit_key_reference_is_transport_only(
    server: _Server, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QMA_FAKE_HTTP_KEY", "test-value-not-a-real-key")
    result = adapter(server, api_key_env="QMA_FAKE_HTTP_KEY").execute(
        ProviderRequest("hi"), lambda _: None, threading.Event()
    )
    assert server.authorization == "Bearer test-value-not-a-real-key"
    assert "test-value" not in repr(result)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://example.com/v1/chat/completions",
        "http://localhost/v1/chat/completions",
        "https://example.com/",
        "https://user:key@example.com/v1/chat/completions",
        "https://example.com/v1/chat/completions?key=secret",
    ],
)
def test_endpoint_is_explicit_and_has_no_embedded_credentials(endpoint: str) -> None:
    with pytest.raises(ValueError):
        ChatCompletionsProvider(endpoint, "model", deployment_id="deployment")


def test_no_native_resume_workspace_or_model_switch(server: _Server) -> None:
    provider = adapter(server)
    assert not provider.capabilities.resume
    assert not provider.capabilities.native_tools
    for request in (
        ProviderRequest("hi", thread_id="native"),
        ProviderRequest("hi", cwd="excluded-workspace"),
        ProviderRequest("hi", model="other"),
    ):
        with pytest.raises(ProviderError):
            provider.execute(request, lambda _: None, threading.Event())
    assert server.calls == 0


@pytest.mark.parametrize("cancel", [False, True])
def test_stalled_connect_retains_capacity_and_never_posts_after_return(
    server: _Server,
    monkeypatch: pytest.MonkeyPatch,
    cancel: bool,
) -> None:
    slots = threading.BoundedSemaphore(1)
    monkeypatch.setattr(http_provider, "_TRANSPORT_SLOTS", slots)
    release_connect = threading.Event()
    connect_started = threading.Event()
    worker_closed = threading.Event()
    cancellation = threading.Event()
    original_connection = http.client.HTTPConnection

    class BlockingConnection(original_connection):
        def connect(self) -> None:
            connect_started.set()
            if cancel:
                cancellation.set()
            release_connect.wait(timeout=3)
            super().connect()

        def close(self) -> None:
            super().close()
            worker_closed.set()

    monkeypatch.setattr(http.client, "HTTPConnection", BlockingConnection)
    try:
        started = time.monotonic()
        with pytest.raises(ProviderError) as error:
            adapter(server).execute(
                ProviderRequest("hi", timeout_seconds=0.05),
                lambda _: None,
                cancellation,
            )
        assert error.value.code == ("cancelled" if cancel else "timeout")
        assert time.monotonic() - started < 0.8
        assert connect_started.is_set()
        assert not worker_closed.is_set()
        assert not slots.acquire(blocking=False)
        with pytest.raises(ProviderError, match="capacity"):
            adapter(server).execute(ProviderRequest("another"), lambda _: None, threading.Event())
        release_connect.set()
        assert worker_closed.wait(timeout=1)
        # Allow finally to release the retained worker slot after close.
        deadline = time.monotonic() + 1
        while not slots.acquire(blocking=False):
            assert time.monotonic() < deadline
            time.sleep(0.01)
        slots.release()
        assert server.calls == 0
    finally:
        release_connect.set()


def test_worker_start_failure_releases_capacity(
    server: _Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    slots = threading.BoundedSemaphore(1)
    monkeypatch.setattr(http_provider, "_TRANSPORT_SLOTS", slots)

    def fail_start(self: threading.Thread) -> None:
        raise RuntimeError("injected startup failure")

    monkeypatch.setattr(threading.Thread, "start", fail_start)
    with pytest.raises(ProviderError, match="could not start"):
        adapter(server).execute(ProviderRequest("hi"), lambda _: None, threading.Event())
    assert slots.acquire(blocking=False)
    slots.release()
    assert server.calls == 0


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://live.ctraderapi.com/v1/chat/completions",
        "https://api.icmarkets.com/v1/chat/completions",
        "https://trading-node-vps/v1/chat/completions",
        "https://platform-registry/v1/chat/completions",
    ],
)
def test_http_inference_preserves_shared_host_reachability(endpoint: str) -> None:
    with pytest.raises(ValueError, match="reachability"):
        ChatCompletionsProvider(endpoint, "test-model", deployment_id="test")


def test_openrouter_documented_endpoint_constructs_without_auth_or_network() -> None:
    provider = ChatCompletionsProvider(
        "https://openrouter.ai/api/v1/chat/completions",
        "operator/model",
        deployment_id="openrouter-test",
        provider_id="openrouter",
        api_key_env="NOT_CONFIGURED",
    )
    assert provider.endpoint == "https://openrouter.ai/api/v1/chat/completions"


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://openrouter.ai/v1/chat/completions",
        "http://openrouter.ai/api/v1/chat/completions",
        "https://openrouter.ai:8443/api/v1/chat/completions",
        "https://example.com/api/v1/chat/completions",
    ],
)
def test_openrouter_path_exception_cannot_expand_other_endpoints(endpoint: str) -> None:
    with pytest.raises(ValueError):
        ChatCompletionsProvider(endpoint, "operator/model", deployment_id="test")
