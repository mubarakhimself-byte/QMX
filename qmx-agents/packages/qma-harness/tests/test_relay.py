from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import httpx
import pytest

from qma.harness.home import SessionId
from qma.harness.launch import TestMode
from qma.harness.profiles import (
    BaseUrl,
    KeyProvider,
    ModelId,
    ProfileName,
    Profiles,
    Quirks,
    SecretRef,
    TierMap,
    WireQuirks,
    parse_profiles,
)
from qma.harness.relay import (
    GrantRefused,
    Relay,
    RelayUsage,
    apply_wire_quirks,
    swap_auth,
)

CHAT = SessionId("0b9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e1f")
KEY = "provider-key-for-tests"
KIMI_ROW: dict[str, object] = {
    "base_url": "https://upstream.test/anthropic",
    "credential_ref": "qmx/kimi",
    "tiers": {"opus": "kimi-k3", "sonnet": "kimi-k3", "haiku": "kimi-k2.6", "fable": "kimi-k3"},
}
TAIL = "Zq7Xw2Lp9V" * 2


def sse(*events: dict[str, Any]) -> bytes:
    return b"".join(
        f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode() for event in events
    )


def stream(served: str) -> bytes:
    return sse(
        {
            "type": "message_start",
            "message": {
                "model": served,
                "usage": {
                    "input_tokens": 120,
                    "output_tokens": 1,
                    "cache_read_input_tokens": 40,
                    "cache_creation_input_tokens": 7,
                },
            },
        },
        {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "ok"}},
        {"type": "message_delta", "usage": {"output_tokens": 9}},
        {"type": "message_stop"},
    )


@dataclass
class Upstream:
    served: str = "kimi-k3"
    seen: list[httpx.Request] = field(default_factory=list[httpx.Request])

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        if request.url.path.endswith("count_tokens"):
            return httpx.Response(200, json={"input_tokens": 33})
        return httpx.Response(
            200,
            content=stream(self.served),
            headers={"content-type": "text/event-stream", "anthropic-ratelimit-x": "5"},
        )


@dataclass
class Rig:
    relay: Relay
    upstream: Upstream
    usage: list[RelayUsage]
    alerts: list[str]

    async def post(
        self, path: str, body: bytes | dict[str, Any], *, bearer: str | None, **headers: str
    ) -> httpx.Response:
        content = body if isinstance(body, bytes) else json.dumps(body).encode()
        auth = {"authorization": f"Bearer {bearer}"} if bearer else {}
        async with httpx.AsyncClient(base_url=self.relay.base_url, trust_env=False) as client:
            return await client.post(path, content=content, headers=auth | headers)


def secret(reference: str) -> str:
    if reference != "qmx/kimi":
        raise KeyError(reference)
    return KEY


def run(
    test: Callable[[Rig], Awaitable[None]],
    *,
    rows: dict[str, object] | None = None,
    mode: TestMode | None = None,
    served: str = "kimi-k3",
) -> None:
    async def main() -> None:
        usage: list[RelayUsage] = []
        alerts: list[str] = []
        upstream = Upstream(served)

        async def sink(item: RelayUsage) -> None:
            usage.append(item)

        async def alert(_chat: SessionId, reason: str) -> None:
            alerts.append(reason)

        def profiles() -> Profiles:
            return parse_profiles(rows if rows is not None else {"kimi": KIMI_ROW})

        relay = await Relay(
            secrets=secret,
            usage=sink,
            alert=alert,
            profiles=profiles,
            test=mode,
            transport=httpx.MockTransport(upstream),
        ).start()
        try:
            await test(Rig(relay, upstream, usage, alerts))
        finally:
            await relay.close()

    asyncio.run(main())


def body(model: str = "kimi-k3", text: str = "hi") -> dict[str, Any]:
    return {"model": model, "stream": True, "messages": [{"role": "user", "content": text}]}


def test_no_bearer_and_a_revoked_grant_get_401_before_the_body_is_read() -> None:
    async def check(rig: Rig) -> None:
        async def unread() -> bytes:
            raise AssertionError("the body was read")

        reply = await rig.relay.handle("POST", "/v1/messages", "", {}, unread)
        assert reply.status == 401
        grant = rig.relay.grant(CHAT, ProfileName("kimi"))
        rig.relay.revoke(CHAT)
        rig.relay.revoke(CHAT)
        revoked = await rig.relay.handle(
            "POST", "/v1/messages", "", {"authorization": f"Bearer {grant.secret}"}, unread
        )
        assert revoked.status == 401
        answer = await rig.post("/v1/messages", body(), bearer="wrong")
        assert (answer.status_code, answer.json()["error"]["type"]) == (
            401,
            "authentication_error",
        )
        assert rig.relay.counters.bearer == 3
        assert rig.upstream.seen == []

    run(check)


@pytest.mark.parametrize(
    "token",
    [
        f"sk-ant-oat01-QMXCANARY{TAIL}",
        f"sk-ant-ort01-{TAIL}",
        f"sk-ant-api03-{TAIL}",
        f"sk-ant-admin01-{TAIL}",
    ],
)
def test_a_full_token_shape_is_stopped_and_never_forwarded(token: str) -> None:
    async def check(rig: Rig) -> None:
        grant = rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(text=f"print {token}"), bearer=grant.secret)
        assert answer.status_code == 400
        assert answer.json()["error"]["message"].startswith("egress stop:")
        assert rig.relay.counters.egress == 1
        assert len(rig.alerts) == 1
        assert rig.upstream.seen == []
        assert rig.usage == []

    run(check)


def test_the_egress_stop_switch_lets_a_token_through_for_layer_checks() -> None:
    async def check(rig: Rig) -> None:
        grant = rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post(
            "/v1/messages", body(text=f"sk-ant-oat01-{TAIL}"), bearer=grant.secret
        )
        assert answer.status_code == 200
        assert rig.relay.counters.egress == 0

    run(check, mode=TestMode(relay_egress_stop=False))


def test_the_bare_prefix_and_the_relay_source_pass() -> None:
    source = (Path(__file__).parents[1] / "src/qma/harness/relay.py").read_text(encoding="utf-8")

    async def check(rig: Rig) -> None:
        grant = rig.relay.grant(CHAT, ProfileName("kimi"))
        for text in ("ANTHROPIC_API_KEY=sk-ant-...", "sk-ant-oat01-short", source):
            answer = await rig.post("/v1/messages", body(text=text), bearer=grant.secret)
            assert answer.status_code == 200
        assert rig.relay.counters.egress == 0
        assert len(rig.upstream.seen) == 3

    run(check)


def test_unknown_paths_get_404_and_the_query_string_is_forwarded() -> None:
    async def check(rig: Rig) -> None:
        grant = rig.relay.grant(CHAT, ProfileName("kimi"))
        other = await rig.post("/v1/other", body(), bearer=grant.secret)
        assert other.status_code == 404
        answer = await rig.post("/v1/messages?beta=true", body(), bearer=grant.secret)
        assert answer.status_code == 200
        assert (
            str(rig.upstream.seen[0].url) == "https://upstream.test/anthropic/v1/messages?beta=true"
        )

    run(check)


@pytest.mark.parametrize(
    ("model", "status"),
    [
        ("claude-opus-5-5", 400),
        ("kimi-k2.7-code", 400),
        ("openrouter/auto", 400),
        ("kimi-k3[1m]", 200),
        ("opus", 200),
        ("kimi-k2.6", 200),
    ],
)
def test_the_requested_model_must_be_a_tier_model(model: str, status: int) -> None:
    async def check(rig: Rig) -> None:
        grant = rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(model), bearer=grant.secret)
        assert answer.status_code == status
        assert rig.relay.counters.family == (status == 400)
        assert len(rig.upstream.seen) == (status == 200)

    run(check)


def test_a_dated_served_id_of_the_right_family_streams_to_the_end_and_usage_is_teed() -> None:
    async def check(rig: Rig) -> None:
        grant = rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages?beta=true", body(), bearer=grant.secret)
        assert answer.content == stream("kimi-k3-20261001")
        assert answer.headers["anthropic-ratelimit-x"] == "5"
        counted = await rig.post("/v1/messages/count_tokens", body(), bearer=grant.secret)
        assert counted.json() == {"input_tokens": 33}
        assert rig.usage == [
            RelayUsage(
                CHAT, ProfileName("kimi"), "/v1/messages", 200, "kimi-k3-20261001", 120, 9, 40, 7
            ),
            RelayUsage(CHAT, ProfileName("kimi"), "/v1/messages/count_tokens", 200, "kimi-k3"),
        ]

    run(check, served="kimi-k3-20261001")


def test_a_barred_served_model_aborts_the_stream_and_moves_the_family_counter() -> None:
    async def check(rig: Rig) -> None:
        grant = rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert answer.text.startswith("event: error\n")
        assert "kimi served claude-opus-x is a claude model" in answer.text
        assert "text_delta" not in answer.text
        assert rig.relay.counters.family == 1
        assert [item.model for item in rig.usage] == ["claude-opus-x"]

    run(check, served="claude-opus-x")


def test_grants_refuse_the_plan_a_missing_key_and_a_row_that_no_longer_validates() -> None:
    async def check(rig: Rig) -> None:
        with pytest.raises(GrantRefused, match="plan traffic never passes the relay"):
            rig.relay.grant(CHAT, ProfileName("claude"))
        with pytest.raises(GrantRefused, match="no qmx/other entry"):
            rig.relay.grant(CHAT, ProfileName("other"))
        first = rig.relay.grant(CHAT, ProfileName("kimi"))
        second = rig.relay.grant(CHAT, ProfileName("kimi"))
        assert first.secret != second.secret
        assert rig.relay.grants == 1
        stale = await rig.post("/v1/messages", body(), bearer=first.secret)
        assert stale.status_code == 401

    run(check, rows={"kimi": KIMI_ROW, "other": KIMI_ROW | {"credential_ref": "qmx/other"}})
    run(
        lambda rig: _refused(rig, "tiers.opus: gpt-5 is a gpt model"),
        rows={
            "kimi": KIMI_ROW
            | {"tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "gpt-5")}
        },
    )


async def _refused(rig: Rig, message: str) -> None:
    with pytest.raises(GrantRefused, match=message):
        rig.relay.grant(CHAT, ProfileName("kimi"))


def test_swap_auth_replaces_the_bearer_and_keeps_the_rest() -> None:
    sent = {
        "Authorization": "Bearer grant",
        "x-api-key": "grant",
        "anthropic-beta": "a,b",
        "anthropic-version": "2023-06-01",
        "Host": "127.0.0.1:1",
        "Content-Length": "9",
        "Connection": "keep-alive",
        "accept-encoding": "br",
        "user-agent": "claude-cli",
    }
    assert swap_auth(sent, KEY, "bearer") == {
        "anthropic-beta": "a,b",
        "anthropic-version": "2023-06-01",
        "user-agent": "claude-cli",
        "authorization": f"Bearer {KEY}",
    }
    assert swap_auth(sent, KEY, "x-api-key") == {
        "anthropic-beta": "a,b",
        "anthropic-version": "2023-06-01",
        "user-agent": "claude-cli",
        "x-api-key": KEY,
    }


PLAIN = KeyProvider(
    ProfileName("p"),
    BaseUrl("https://h"),
    SecretRef("qmx/p"),
    TierMap(*[ModelId("m")] * 4),
)


def test_wire_quirks_leave_a_plain_body_byte_identical() -> None:
    raw = b'{"model": "m",   "top_k": 3}'
    assert apply_wire_quirks(PLAIN, raw) is raw


def test_wire_quirks_strip_fields_and_add_a_top_level_cache_marker() -> None:
    strict = replace(
        PLAIN,
        quirks=Quirks(
            wire=WireQuirks(
                strip_fields=frozenset({"top_k", "stop_sequences"}), cache_markers="top_level_only"
            )
        ),
    )
    marked = {
        "model": "m",
        "top_k": 3,
        "stop_sequences": ["x"],
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": "é", "cache_control": {"type": "ephemeral"}}],
            }
        ],
    }
    assert (
        apply_wire_quirks(strict, json.dumps(marked).encode())
        == (
            '{"model":"m","messages":[{"role":"user","content":[{"type":"text","text":"é",'
            '"cache_control":{"type":"ephemeral"}}]}],"cache_control":{"type":"ephemeral"}}'
        ).encode()
    )
    unmarked: dict[str, object] = {"model": "m", "top_k": 3, "messages": []}
    assert (
        apply_wire_quirks(strict, json.dumps(unmarked).encode()) == b'{"model":"m","messages":[]}'
    )


def test_the_relay_listens_on_loopback_only() -> None:
    async def check(rig: Rig) -> None:
        assert rig.relay.base_url.startswith("http://127.0.0.1:")

    run(check)


def test_a_failing_alert_never_turns_a_refusal_into_a_server_error() -> None:
    async def check(rig: Rig) -> None:
        async def broken(_chat: SessionId, _reason: str) -> None:
            raise RuntimeError("no such session")

        rig.relay.alert = broken
        grant = rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body("kimi-k2.7-code"), bearer=grant.secret)
        assert answer.status_code == 400

    run(check)
