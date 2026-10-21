# ruff: noqa: S101
from __future__ import annotations

import json
import socket
import threading
from http.client import HTTPResponse
from pathlib import Path

from router import Echo, Recorder, Router, Upstream, compare_secret, is_claude

FIXTURE_CREDENTIAL = "Bearer fixture-oauth-value-0123456789"
BODY = b'{"model":"claude-haiku-4-5","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}'


class Capture:
    """A raw socket upstream that keeps the exact bytes it receives."""

    def __init__(self) -> None:
        self.listener = socket.create_server(("127.0.0.1", 0))
        self.netloc = f"127.0.0.1:{self.listener.getsockname()[1]}"
        self.received = b""
        threading.Thread(target=self.serve, daemon=True).start()

    def serve(self) -> None:
        conn, _ = self.listener.accept()
        with conn:
            data = b""
            while b"\r\n\r\n" not in data:
                data += conn.recv(65536)
            head, _, rest = data.partition(b"\r\n\r\n")
            length = next(
                int(line.split(b":")[1])
                for line in head.split(b"\r\n")
                if line.lower().startswith(b"content-length")
            )
            while len(rest) < length:
                rest += conn.recv(65536)
            self.received = data[: len(head) + 4] + rest
            conn.sendall(b"HTTP/1.1 200 OK\r\ncontent-length: 2\r\n\r\nok")


def send(url: str, raw: bytes) -> tuple[int, bytes]:
    host, port = url.removeprefix("http://").split(":")
    with socket.create_connection((host, int(port)), timeout=30) as conn:
        conn.sendall(raw)
        reply = HTTPResponse(conn)
        reply.begin()
        return reply.status, reply.read()


def fixture(netloc: str, model_body: bytes = BODY) -> bytes:
    head = (
        "POST /v1/messages?beta=true HTTP/1.1\r\n"
        f"Host: {netloc}\r\n"
        "accept-encoding: gzip, br\r\n"
        "anthropic-beta: oauth-2025-04-20\r\n"
        "anthropic-beta: second-repeat\r\n"
        f"authorization: {FIXTURE_CREDENTIAL}\r\n"
        "x-qmx-grant: fixture-grant\r\n"
        "content-type: application/json\r\n"
        f"content-length: {len(model_body)}\r\n\r\n"
    )
    return head.encode() + model_body


def without_grant(raw: bytes) -> bytes:
    return raw.replace(b"x-qmx-grant: fixture-grant\r\n", b"")


def test_a_claude_request_is_forwarded_byte_for_byte_and_no_secret_is_written(
    tmp_path: Path,
) -> None:
    upstream = Capture()
    with Router(lambda _: Upstream("anthropic", f"http://{upstream.netloc}")) as router:
        reply = send(router.url, fixture(upstream.netloc))
        recording = tmp_path / "recording.json"
        router.recorder.write(recording)

    assert reply == (200, b"ok")
    assert upstream.received == without_grant(fixture(upstream.netloc))
    written = recording.read_text("utf-8")
    assert "fixture-oauth-value" not in written
    assert "fixture-grant" not in written
    headers = json.loads(written)["requests"][0]["headers"]
    assert ["authorization", "<withheld>"] in headers
    assert [h[0] for h in headers].count("anthropic-beta") == 2


def test_a_third_party_id_reaches_the_echo_without_the_incoming_credential() -> None:
    echo = Echo("KIMI-ECHO-1").start()
    try:
        route = lambda model: None if is_claude(model) else echo.upstream("kimi-echo")  # noqa: E731
        body = BODY.replace(b"claude-haiku-4-5", b"kimi/k3")
        with Router(route) as router:
            reply = send(router.url, fixture(router.url.removeprefix("http://"), body))
            lanes = [(e.lane, e.model) for e in router.recorder.exchanges]
    finally:
        echo.stop()

    assert reply[0] == 200
    assert b"KIMI-ECHO-1" in reply[1]
    assert lanes == [("kimi-echo", "kimi/k3")]
    assert len(echo.requests) == 1
    assert "authorization" not in echo.requests[0].headers
    assert "x-qmx-grant" not in echo.requests[0].headers


def test_an_unrouted_model_is_refused_with_400() -> None:
    with Router(lambda _: None) as router:
        reply = send(router.url, fixture(router.url.removeprefix("http://")))
        statuses = [e.status for e in router.recorder.exchanges]
    assert reply[0] == 400
    assert statuses == [400]


def test_secret_values_compare_as_same_or_different_only() -> None:
    upstream = Capture()
    recorder = Recorder()
    with Router(lambda _: Upstream("anthropic", f"http://{upstream.netloc}")) as router:
        send(router.url, fixture(upstream.netloc))
        recorder.exchanges = list(router.recorder.exchanges)
    first = recorder.exchanges[0]
    other = type(first)(**{**first.__dict__, "headers": [("authorization", "Bearer other")]})

    assert compare_secret(first, first, "authorization") == "same"
    assert compare_secret(first, other, "authorization") == "different"
    assert compare_secret(first, other, "x-api-key") == "absent in both"
