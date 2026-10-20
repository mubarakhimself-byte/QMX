"""AD-50's normaliser and AD-38's routing, at the modules' own doors.

Each fixture is a real bundled row, so the expected egress is the shape OpenRouter, Kimi and
DeepSeek actually take rather than a row invented for the test.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from qmx_router.ids import SessionId
from qmx_router.normalise import Egress, classify, normalise, refuse_retry
from qmx_router.profiles import ProfileName, parse_profiles
from qmx_router.registry import ModelRow, Registry, bundled
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
