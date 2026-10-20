"""AD-50's normaliser and AD-38's routing, at the modules' own doors.

Each fixture is a real bundled row, so the expected egress is the shape OpenRouter, Kimi and
DeepSeek actually take rather than a row invented for the test.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

import httpx

from qmx_router.ids import SessionId
from qmx_router.normalise import Egress, classify, normalise, refuse_retry
from qmx_router.profiles import ModelId, ProfileName, parse_profiles
from qmx_router.registry import ModelRow, Provider, QmxId, Registry, bundled
from qmx_router.relay import Relay, RelayUsage
from qmx_router.server import PORT_FILE, RouterService

ROWS: Registry = bundled()
KIMI = ROWS.model("openrouter/moonshotai/kimi-k2.5")
DEEPSEEK = ROWS.model("openrouter/deepseek/deepseek-v4.1-flash")

CLAUDE_SHAPED: dict[str, Any] = {
    "model": "moonshotai/kimi-k2.5",
    "max_tokens": 64_000,
    "metadata": {"user_id": "user_abc"},
    "tools": [
        {"name": "bash", "description": "run", "input_schema": {"type": "object"}},
        {"type": "tool_search_tool_20250925", "name": "tool_search"},
        {"name": "later", "defer_loading": True, "input_schema": {"type": "object"}},
    ],
    "messages": [{"role": "user", "content": "hi"}],
}
CLAUDE_HEADERS: dict[str, str] = {
    "Authorization": "Bearer grant",
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "oauth-2025-04-20,tool-search-2025-09-25",
    "x-claude-code-session-id": "session-1",
    "x-app": "cli",
}


def egress_for(
    row: ModelRow,
    body: dict[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> Egress:
    return normalise(
        row,
        json.dumps(CLAUDE_SHAPED if body is None else body).encode(),
        CLAUDE_HEADERS if headers is None else headers,
    )


def test_the_kimi_row_expands_tool_search_and_clamps_its_output() -> None:
    egress = egress_for(KIMI)
    assert json.loads(egress.body) == {
        "model": "moonshotai/kimi-k2.5",
        "max_tokens": 32_000,
        "tools": [
            {"name": "bash", "description": "run", "input_schema": {"type": "object"}},
            {"name": "later", "input_schema": {"type": "object"}},
        ],
        "messages": [{"role": "user", "content": "hi"}],
    }
    assert egress.headers == {
        "authorization": "Bearer grant",
        "anthropic-version": "2023-06-01",
        "x-app": "cli",
    }


def test_the_deepseek_row_takes_the_same_request_the_same_way() -> None:
    assert egress_for(DEEPSEEK) == egress_for(KIMI)


def test_a_forward_header_the_row_lists_is_kept() -> None:
    row = replace(KIMI, forward_headers=frozenset({"x-claude-code-session-id"}))
    assert egress_for(row).headers["x-claude-code-session-id"] == "session-1"


def test_an_unparseable_history_is_rewritten_for_the_row() -> None:
    body: dict[str, Any] = {
        "model": "deepseek/deepseek-v4.1-flash",
        "messages": [
            {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "why", "signature": "sig"},
                    {"type": "server_tool_use", "id": "srvtoolu_1", "name": "web", "input": {}},
                    {"type": "text", "text": "look"},
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": [{"type": "tool_reference", "tool_name": "TaskCreate"}],
                    }
                ],
            },
        ],
    }
    egress = egress_for(replace(DEEPSEEK, thinking="none"), body)
    assert json.loads(egress.body)["messages"] == [
        {"role": "assistant", "content": [{"type": "text", "text": "look"}]},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_1",
                    "content": [{"type": "text", "text": "[tool: TaskCreate]"}],
                }
            ],
        },
    ]


def test_an_image_is_placed_when_the_row_cannot_see() -> None:
    image = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AA"}}
    body = {"model": "moonshotai/kimi-k2.5", "messages": [{"role": "user", "content": [image]}]}
    assert json.loads(egress_for(KIMI, body).body)["messages"][0]["content"] == [
        {"type": "text", "text": "[image omitted: this model cannot see images]"}
    ]


def test_a_body_the_row_takes_as_sent_is_forwarded_byte_for_byte() -> None:
    sent = b'{"model": "moonshotai/kimi-k2.5",  "messages": []}'
    assert normalise(KIMI, sent, {}).body == sent


def test_a_usage_limit_is_classified_once_and_never_retried() -> None:
    limit = {"error": {"message": "You have hit your weekly usage limit"}}
    assert classify(429, limit) == "usage_limit"
    assert classify(429, {"error": {"message": "Too many requests"}}) == "rate_limit"
    assert classify(400, {"error": {"message": "bad"}}) == "bad_input"
    assert refuse_retry(429, limit) == {"x-should-retry": "false"}
    assert refuse_retry(400, {"error": {"message": "bad"}}) == {}


KIMI_ROW: dict[str, Any] = {
    "base_url": "https://upstream.test/anthropic",
    "credential_ref": "qmx/kimi",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "kimi-k3"),
}
CHAT = SessionId("chat-1")


class Journal:
    def append(self, usage: RelayUsage) -> None:
        _ = usage

    def close(self) -> None:
        return None


async def quiet(_session: SessionId, _reason: str) -> None:
    return None


def relay_for(rows: dict[str, Any]) -> Relay:
    profiles = parse_profiles(rows)
    return Relay(
        secrets=lambda _reference: "key",
        journal=lambda _session: Journal(),
        alert=quiet,
        profiles=lambda: profiles,
    )


def read_body(document: dict[str, Any]) -> Callable[[], Awaitable[bytes]]:
    async def read() -> bytes:
        return json.dumps(document).encode()

    return read


def test_a_claude_id_on_a_key_grant_is_refused_and_names_delegate() -> None:
    async def check() -> None:
        relay = relay_for({"kimi": KIMI_ROW})
        grant = await relay.grant(CHAT, ProfileName("kimi"))
        assert grant.model_scope == frozenset({ProfileName("kimi")})
        request: dict[str, Any] = {
            "model": "claude-opus-5-5",
            "max_tokens": 8,
            "messages": [],
        }
        reply = await relay.handle(
            "POST",
            "/v1/messages",
            "",
            {"authorization": f"Bearer {grant.secret}"},
            read_body(request),
        )
        text = b"".join([chunk async for chunk in reply.body]).decode()
        assert reply.status == 400
        assert "is a claude model" in text
        assert "`delegate`" in text
        await relay.close()

    asyncio.run(check())


def test_the_router_restarts_on_its_pinned_port_after_a_stall(tmp_path: Path) -> None:
    async def check() -> None:
        service = await RouterService(tmp_path).start()
        relay = relay_for({"kimi": KIMI_ROW})
        assert await service.adopt(relay)
        pinned = service.port
        assert (tmp_path / PORT_FILE).read_text(encoding="utf-8").strip() == str(pinned)
        assert await service.canary()
        service.stall_s = -1.0
        assert await service.supervise_once()
        assert service.restarts == 1
        assert service.port == pinned
        assert (tmp_path / PORT_FILE).read_text(encoding="utf-8").strip() == str(pinned)
        assert await service.canary()
        await relay.close()
        await service.close()

    asyncio.run(check())


BOUND_S = 1.0
SLEEP_S = 4.0
"""The fake's silence and the row's bound. A literal pair, so the assertion can name both."""


class FakeUpstream:
    """One HTTP/1.1 responder. `headers_after` delays the status line, `event_after` delays the
    first SSE event behind it, which are the two ways a prefill stalls."""

    def __init__(self, *, headers_after: float, event_after: float) -> None:
        self.headers_after = headers_after
        self.event_after = event_after
        self.requests = 0
        self.port = 0
        self._server: asyncio.Server | None = None

    async def start(self) -> FakeUpstream:
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        head = await reader.readuntil(b"\r\n\r\n")
        length = 0
        for line in head.split(b"\r\n"):
            if line.lower().startswith(b"content-length:"):
                length = int(line.split(b":", 1)[1])
        await reader.readexactly(length)
        self.requests += 1
        await asyncio.sleep(self.headers_after)
        writer.write(
            b"HTTP/1.1 200 OK\r\ncontent-type: text/event-stream\r\n"
            b"transfer-encoding: chunked\r\n\r\n"
        )
        await writer.drain()
        await asyncio.sleep(self.event_after)
        event = (
            b'event: message_start\ndata: {"type": "message_start", '
            b'"message": {"model": "fake-1m", "usage": {"input_tokens": 5}}}\n\n'
        )
        with contextlib.suppress(ConnectionError):
            writer.write(f"{len(event):x}\r\n".encode() + event + b"\r\n0\r\n\r\n")
            await writer.drain()
        writer.close()


class Rows:
    """A journal that keeps what the relay wrote."""

    def __init__(self) -> None:
        self.rows: list[RelayUsage] = []

    def append(self, usage: RelayUsage) -> None:
        self.rows.append(usage)

    def close(self) -> None:
        return None


async def first_bytes(port: int) -> tuple[float, bytes, list[RelayUsage]]:
    """One streamed request through the relay, the clock from send to first byte, and its row."""
    journal = Rows()
    row = ModelRow(
        qmx_id=QmxId("fake/one"),
        provider=ProfileName("fake"),
        native=ModelId("fake-1m"),
        window=1_000_000,
        first_token_timeout_s=int(BOUND_S),
        first_token_per_100k_s=0,
    )
    provider = Provider(
        name=ProfileName("fake"),
        kind="key",
        base_url=MappingProxyType({"local": f"http://127.0.0.1:{port}"}),
        models=(row,),
    )
    registry = Registry(MappingProxyType({ProfileName("fake"): provider}))
    profiles = parse_profiles(
        {
            "fake": {
                "base_url": f"http://127.0.0.1:{port}",
                "credential_ref": "qmx/fake",
                "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "fake-1m"),
            }
        },
        allow_loopback_http=True,
    )
    relay = await Relay(
        secrets=lambda _reference: "key",
        journal=lambda _session: journal,
        alert=quiet,
        profiles=lambda: profiles,
        registry=lambda: registry,
    ).start()
    grant = await relay.grant(SessionId("fake-chat"), ProfileName("fake"))
    started = time.monotonic()
    async with (
        httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client,
        client.stream(
            "POST",
            f"{relay.base_url}/v1/messages",
            json={
                "model": "fake/one",
                "max_tokens": 8,
                "stream": True,
                "messages": [{"role": "user", "content": "hi"}],
            },
            headers={"authorization": f"Bearer {grant.secret}"},
        ) as answer,
    ):
        first = b""
        async for chunk in answer.aiter_bytes():
            first += chunk
            break
    elapsed = time.monotonic() - started
    await relay.close()
    return elapsed, first, journal.rows


def test_a_provider_that_sends_no_headers_inside_the_row_bound_is_stopped() -> None:
    async def check() -> None:
        fake = await FakeUpstream(headers_after=SLEEP_S, event_after=0.0).start()
        elapsed, first, rows = await first_bytes(fake.port)
        await fake.close()
        assert first.startswith(b"event: error\n")
        assert b"no message_start in 1 s" in first
        assert elapsed < BOUND_S + 2.0
        assert fake.requests == 1
        assert [row.status for row in rows] == [504]

    asyncio.run(check())


def test_a_provider_that_sends_headers_and_then_stalls_is_stopped() -> None:
    async def check() -> None:
        fake = await FakeUpstream(headers_after=0.0, event_after=SLEEP_S).start()
        elapsed, first, rows = await first_bytes(fake.port)
        await fake.close()
        assert first.startswith(b"event: error\n")
        assert b"no message_start in 1 s" in first
        assert elapsed < BOUND_S + 2.0
        assert fake.requests == 1
        assert [row.status for row in rows] == [200]

    asyncio.run(check())
