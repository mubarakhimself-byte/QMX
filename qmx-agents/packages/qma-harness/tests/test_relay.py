from __future__ import annotations

import asyncio
import contextlib
import json
import socket
import threading
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import httpx
import keyring.errors
import pytest
import uvicorn

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
class Journals:
    broken: bool = False
    opened: list[SessionId] = field(default_factory=list[SessionId])
    closed: list[SessionId] = field(default_factory=list[SessionId])
    rows: list[RelayUsage] = field(default_factory=list[RelayUsage])

    def open(self, session: SessionId) -> Writer:
        self.opened.append(session)
        return Writer(self, session)


@dataclass
class Writer:
    journals: Journals
    session: SessionId

    def append(self, usage: RelayUsage) -> None:
        if self.journals.broken:
            raise FileExistsError("journal.jsonl.lock")
        self.journals.rows.append(usage)

    def close(self) -> None:
        self.journals.closed.append(self.session)


@dataclass
class Rig:
    relay: Relay
    upstream: Upstream
    journals: Journals
    alerts: list[str]

    @property
    def usage(self) -> list[RelayUsage]:
        return self.journals.rows

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
    handler: Callable[[httpx.Request], Any] | None = None,
    lookup: Callable[[str], str] = secret,
    broken_journal: bool = False,
) -> None:
    async def main() -> None:
        journals = Journals(broken=broken_journal)
        alerts: list[str] = []
        upstream = Upstream(served)

        async def alert(_chat: SessionId, reason: str) -> None:
            alerts.append(reason)

        def profiles() -> Profiles:
            return parse_profiles(rows if rows is not None else {"kimi": KIMI_ROW})

        relay = await Relay(
            secrets=lookup,
            journal=journals.open,
            alert=alert,
            profiles=profiles,
            test=mode,
            transport=httpx.MockTransport(handler or upstream),
        ).start()
        try:
            await test(Rig(relay, upstream, journals, alerts))
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
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        await rig.relay.revoke(grant)
        await rig.relay.revoke(grant)
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
        f"sk-ant-sid01-{TAIL}",
    ],
)
def test_a_full_token_shape_is_stopped_and_never_forwarded(token: str) -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
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
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post(
            "/v1/messages", body(text=f"sk-ant-oat01-{TAIL}"), bearer=grant.secret
        )
        assert answer.status_code == 200
        assert rig.relay.counters.egress == 0

    run(check, mode=TestMode(relay_egress_stop=False))


def test_the_bare_prefix_and_the_relay_source_pass() -> None:
    source = (Path(__file__).parents[1] / "src/qma/harness/relay.py").read_text(encoding="utf-8")

    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        for text in ("ANTHROPIC_API_KEY=sk-ant-...", "sk-ant-oat01-short", source):
            answer = await rig.post("/v1/messages", body(text=text), bearer=grant.secret)
            assert answer.status_code == 200
        assert rig.relay.counters.egress == 0
        assert len(rig.upstream.seen) == 3

    run(check)


def test_unknown_paths_get_404_and_the_query_string_is_forwarded() -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        other = await rig.post("/v1/other", body(), bearer=grant.secret)
        assert other.status_code == 404
        answer = await rig.post("/v1/messages?beta=true", body(), bearer=grant.secret)
        assert answer.status_code == 200
        assert (
            str(rig.upstream.seen[0].url) == "https://upstream.test/anthropic/v1/messages?beta=true"
        )

    run(check)


@pytest.mark.parametrize(
    ("model", "outcome"),
    [
        ("claude-opus-5-5", "family guard: claude-opus-5-5 is a claude model"),
        ("openrouter/auto", "family guard: openrouter/auto lets the vendor pick"),
        ("kimi-k2.7-code", "tier guard: kimi-k2.7-code is not one of kimi's tier models"),
        ("kimi-k3[1m]", "kimi-k3"),
        ("sonnet", "kimi-k3"),
        ("opus", "kimi-k3"),
        ("KIMI-K2.6", "kimi-k2.6"),
    ],
)
def test_the_requested_model_must_be_a_tier_model_and_goes_out_pinned(
    model: str, outcome: str
) -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(model), bearer=grant.secret)
        if answer.status_code == 400:
            assert answer.json()["error"]["message"].startswith(outcome)
            rule = outcome.split(" ", 1)[0]
            assert (rig.relay.counters.family, rig.relay.counters.tier) == (
                rule == "family",
                rule == "tier",
            )
            assert rig.upstream.seen == []
        else:
            assert answer.status_code == 200
            assert json.loads(rig.upstream.seen[0].content)["model"] == outcome

    run(check)


def test_a_dated_served_id_of_the_right_family_streams_to_the_end_and_usage_is_teed() -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
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
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
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
            await rig.relay.grant(CHAT, ProfileName("claude"))
        with pytest.raises(GrantRefused, match="no qmx/other entry"):
            await rig.relay.grant(CHAT, ProfileName("other"))
        first = await rig.relay.grant(CHAT, ProfileName("kimi"))
        second = await rig.relay.grant(CHAT, ProfileName("kimi"))
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
        await rig.relay.grant(CHAT, ProfileName("kimi"))


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
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body("kimi-k2.7-code"), bearer=grant.secret)
        assert answer.status_code == 400

    run(check)


def test_a_broken_journal_never_changes_the_reply_and_alerts_the_chat() -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        streamed = await rig.post("/v1/messages", body(), bearer=grant.secret)
        counted = await rig.post("/v1/messages/count_tokens", body(), bearer=grant.secret)
        assert (streamed.status_code, streamed.content) == (200, stream("kimi-k3"))
        assert (counted.status_code, counted.json()) == (200, {"input_tokens": 33})
        assert rig.alerts == [
            "usage journal: FileExistsError: journal.jsonl.lock; "
            "this request's usage was not recorded"
        ] * 2

    run(check, broken_journal=True)


def test_one_journal_writer_per_session_closed_when_its_grant_is_revoked() -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        for _ in range(3):
            await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert (rig.journals.opened, rig.journals.closed, len(rig.usage)) == ([CHAT], [], 3)
        await rig.relay.revoke(grant)
        assert rig.journals.closed == [CHAT]

    run(check)


TOKEN = f"sk-ant-oat01-{TAIL}"


@pytest.mark.parametrize(
    ("path", "content", "headers"),
    [
        ("/v1/messages", json.dumps(body(text=TOKEN)).replace("-", "\\u002d"), {}),
        ("/v1/messages", json.dumps(body()), {"x-extra": TOKEN}),
        ("/v1/messages", json.dumps(body()), {"anthropic-beta": f"a,{TOKEN}"}),
        (f"/v1/messages?t={TOKEN}", json.dumps(body()), {}),
        (f"/v1/messages?t={TOKEN.replace('-', '%2D')}", json.dumps(body()), {}),
    ],
)
def test_the_egress_stop_reads_decoded_strings_every_header_and_the_query(
    path: str, content: str, headers: dict[str, str]
) -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post(path, content.encode(), bearer=grant.secret, **headers)
        assert answer.status_code == 400
        assert answer.json()["error"]["message"].startswith("egress stop:")
        assert (rig.relay.counters.egress, len(rig.alerts), rig.upstream.seen) == (1, 1, [])

    run(check)


def test_a_token_shaped_bearer_is_an_egress_stop_that_alerts_every_granted_chat() -> None:
    async def check(rig: Rig) -> None:
        await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=TOKEN)
        assert answer.status_code == 401
        assert answer.json()["error"]["message"].startswith("egress stop:")
        assert (rig.relay.counters.egress, rig.relay.counters.bearer) == (1, 0)
        assert len(rig.alerts) == 1
        assert rig.upstream.seen == []

    run(check)


def slow_stream(produced: list[int], closed: asyncio.Event) -> Callable[[httpx.Request], Any]:
    class Slow(httpx.AsyncByteStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            yield sse(
                {"type": "message_start", "message": {"model": "kimi-k3", "usage": {"input_tokens": 5}}}
            )
            for index in range(50):
                await asyncio.sleep(0.05)
                produced.append(index)
                yield sse({"type": "content_block_delta", "delta": {"text": "x"}})
            yield sse({"type": "message_delta", "usage": {"output_tokens": 999}})

        async def aclose(self) -> None:
            closed.set()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=Slow(), headers={"content-type": "text/event-stream"})

    return handler


def test_a_client_disconnect_closes_the_upstream_and_journals_the_usage_seen() -> None:
    produced: list[int] = []
    closed = asyncio.Event()

    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        auth = {"authorization": f"Bearer {grant.secret}"}
        async with (
            httpx.AsyncClient(base_url=rig.relay.base_url, trust_env=False) as client,
            client.stream("POST", "/v1/messages", json=body(), headers=auth) as answer,
        ):
            async for _chunk in answer.aiter_bytes():
                break
        await asyncio.wait_for(closed.wait(), 2)
        count = len(produced)
        await asyncio.sleep(0.3)
        assert len(produced) == count < 50
        assert [(item.input_tokens, item.output_tokens) for item in rig.usage] == [(5, 0)]

    run(check, handler=slow_stream(produced, closed))


def test_revoke_cancels_the_grants_streams_and_close_never_waits_on_them() -> None:
    produced: list[int] = []
    closed = asyncio.Event()

    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        auth = {"authorization": f"Bearer {grant.secret}"}
        received: list[bytes] = []

        async def reader() -> None:
            async with (
                httpx.AsyncClient(base_url=rig.relay.base_url, trust_env=False) as client,
                client.stream("POST", "/v1/messages", json=body(), headers=auth) as answer,
            ):
                async for chunk in answer.aiter_bytes():
                    received.append(chunk)

        task = asyncio.create_task(reader())
        while not received:
            await asyncio.sleep(0.01)
        await asyncio.wait_for(rig.relay.revoke(grant), 2)
        assert closed.is_set()
        with contextlib.suppress(httpx.HTTPError):
            await asyncio.wait_for(task, 2)
        assert len(produced) < 50
        assert [item.input_tokens for item in rig.usage] == [5]
        closed.clear()
        second = await rig.relay.grant(CHAT, ProfileName("kimi"))
        orphan = asyncio.create_task(rig.post("/v1/messages", body(), bearer=second.secret))
        await asyncio.sleep(0.2)
        await asyncio.wait_for(rig.relay.close(), 3)
        assert closed.is_set()
        orphan.cancel()

    run(check, handler=slow_stream(produced, closed))


def sse_reply(content: bytes, content_type: str = "text/event-stream") -> Callable[..., Any]:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=content, headers={"content-type": content_type})

    return handler


CLAUDE_START = {"type": "message_start", "message": {"model": "anthropic/claude-opus-4"}}
TEXT = {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "secret"}}


@pytest.mark.parametrize(
    ("content", "content_type", "message"),
    [
        (
            sse(CLAUDE_START, TEXT).replace(b"\n", b"\r"),
            "text/event-stream",
            "family guard: kimi served anthropic/claude-opus-4",
        ),
        (
            sse(CLAUDE_START, TEXT).replace(b"\n", b"\r\n"),
            "Text/Event-Stream; charset=utf-8",
            "family guard: kimi served anthropic/claude-opus-4",
        ),
        (sse(TEXT, CLAUDE_START), "text/event-stream", "the provider sent content_block_delta"),
        (sse({"type": "ping"}), "text/event-stream", "the provider stream ended without"),
        (sse({"type": "ping"}) * 2000, "text/event-stream", "no message_start in the first"),
    ],
    ids=["cr", "crlf-mixed-case", "content-first", "no-start", "pings-past-the-bound"],
)
def test_the_served_model_guard_fails_closed(
    content: bytes, content_type: str, message: str
) -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert answer.text.startswith("event: error\n")
        assert message in answer.text
        assert "secret" not in answer.text
        assert answer.text.count("\n\n") == 1
        assert len(rig.alerts) == 1

    run(check, handler=sse_reply(content, content_type))


def test_a_mislabelled_stream_fails_closed_and_crlf_streams_parse() -> None:
    async def mislabelled(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert answer.status_code == 502
        assert b"claude" not in answer.content

    run(mislabelled, handler=sse_reply(sse(CLAUDE_START, TEXT), "application/json"))

    async def crlf(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert answer.content == stream("kimi-k3").replace(b"\n", b"\r\n")
        assert [(item.input_tokens, item.output_tokens) for item in rig.usage] == [(120, 9)]

    run(crlf, handler=sse_reply(stream("kimi-k3").replace(b"\n", b"\r\n")))


def test_keyring_errors_refuse_the_grant_or_answer_401_with_an_alert() -> None:
    threads: list[str] = []

    def locked(_reference: str) -> str:
        threads.append(threading.current_thread().name)
        raise keyring.errors.KeyringLocked("locked")

    async def at_grant(rig: Rig) -> None:
        with pytest.raises(GrantRefused, match="could not read qmx/kimi: KeyringLocked"):
            await rig.relay.grant(CHAT, ProfileName("kimi"))
        assert threads
        assert threading.main_thread().name not in threads

    run(at_grant, lookup=locked)
    calls: list[str] = []

    def flaky(reference: str) -> str:
        calls.append(reference)
        if len(calls) > 1:
            raise keyring.errors.KeyringLocked("locked")
        return KEY

    async def at_forward(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert answer.status_code == 401
        assert rig.alerts == ["the keyring could not read qmx/kimi: KeyringLocked"]
        assert rig.upstream.seen == []

    run(at_forward, lookup=flaky)


def test_a_broken_upstream_read_closes_it_and_journals_one_row() -> None:
    closed = asyncio.Event()

    class Broken(httpx.AsyncByteStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            yield b'{"model":'
            raise httpx.ReadError("reset")

        async def aclose(self) -> None:
            closed.set()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=Broken(), headers={"content-type": "application/json"})

    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert answer.status_code == 502
        assert closed.is_set()
        assert [item.status for item in rig.usage] == [502]

    run(check, handler=handler)


def test_a_failed_response_start_closes_the_upstream_and_journals_one_row() -> None:
    produced: list[int] = []
    closed = asyncio.Event()

    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        scope: dict[str, Any] = {
            "type": "http",
            "method": "POST",
            "path": "/v1/messages",
            "query_string": b"",
            "headers": [(b"authorization", f"Bearer {grant.secret}".encode())],
        }
        sent = json.dumps(body()).encode()
        delivered: list[bool] = []

        async def receive() -> dict[str, Any]:
            if delivered:
                await asyncio.Event().wait()
            delivered.append(True)
            return {"type": "http.request", "body": sent, "more_body": False}

        async def send(_message: dict[str, Any]) -> None:
            raise OSError("the socket is gone")

        with pytest.raises(OSError, match="the socket is gone"):
            await rig.relay.asgi(scope, receive, send)  # pyright: ignore[reportArgumentType]
        assert closed.is_set()
        assert [item.input_tokens for item in rig.usage] == [0]

    run(check, handler=slow_stream(produced, closed))


def test_a_redirect_is_never_passed_on_and_hop_by_hop_and_cookies_are_dropped() -> None:
    def redirect(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(307, headers={"location": "https://elsewhere.test/v1/messages"})

    async def moved(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert answer.status_code == 502
        assert "location" not in answer.headers
        assert [item.status for item in rig.usage] == [307]

    run(moved, handler=redirect)

    def cookies(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=stream("kimi-k3"),
            headers={
                "content-type": "text/event-stream",
                "set-cookie": "session=1",
                "keep-alive": "timeout=99",
                "proxy-authenticate": "Basic",
                "anthropic-ratelimit-x": "5",
            },
        )

    async def stripped(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert answer.headers["anthropic-ratelimit-x"] == "5"
        assert not {"set-cookie", "keep-alive", "proxy-authenticate"} & set(answer.headers)

    run(stripped, handler=cookies)


@pytest.mark.parametrize(
    ("extra", "status"),
    [
        ({"models": ["anthropic/claude-opus-4"]}, 400),
        ({"provider": {"order": ["anthropic"]}}, 400),
        ({"route": "fallback"}, 400),
        ({"metadata": {"user_id": "u"}}, 200),
    ],
)
def test_vendor_routing_fields_are_refused(extra: dict[str, Any], status: int) -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body() | extra, bearer=grant.secret)
        assert answer.status_code == status
        if status == 400:
            assert answer.json()["error"]["message"].startswith("family guard: the request sets")
            assert rig.upstream.seen == []

    run(check)


def test_a_routing_field_the_row_strips_is_a_declared_quirk() -> None:
    row = KIMI_ROW | {"quirks": {"wire": {"strip_fields": ["provider"]}}}

    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body() | {"provider": {}}, bearer=grant.secret)
        assert answer.status_code == 200
        assert "provider" not in json.loads(rig.upstream.seen[0].content)

    run(check, rows={"kimi": row})


def test_the_exact_pinned_id_is_forwarded_byte_for_byte() -> None:
    sent = b'{"model": "kimi-k3",  "stream": true, "messages": []}'

    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        await rig.post("/v1/messages", sent, bearer=grant.secret)
        assert rig.upstream.seen[0].content == sent

    run(check)


def test_the_listener_is_released_when_the_server_fails_to_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def broken(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("no serve")

    async def ignore(_chat: SessionId, _reason: str) -> None:
        return None

    monkeypatch.setattr(uvicorn.Server, "serve", broken)

    async def main() -> None:
        relay = Relay(
            secrets=secret,
            journal=Journals().open,
            alert=ignore,
            profiles=lambda: parse_profiles({}),
        )
        with pytest.raises(RuntimeError, match="no serve"):
            await relay.start()
        port = int(relay.base_url.rsplit(":", 1)[1])
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))

    asyncio.run(main())


@dataclass
class HeldWriter(Writer):
    entered: threading.Event = field(default_factory=threading.Event)
    release: threading.Event = field(default_factory=threading.Event)
    shut: bool = False

    def append(self, usage: RelayUsage) -> None:
        self.entered.set()
        self.release.wait(5)
        if self.shut:
            raise ValueError("I/O operation on closed journal")
        super().append(usage)

    def close(self) -> None:
        self.shut = True
        super().close()


async def _revoke_mid_append(rig: Rig, writer: HeldWriter, *, release_after: float) -> None:
    rig.relay.journal = lambda _session: writer
    grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
    answer = asyncio.create_task(rig.post("/v1/messages", body(), bearer=grant.secret))
    await asyncio.to_thread(writer.entered.wait, 5)
    threading.Timer(release_after, writer.release.set).start()
    await asyncio.wait_for(rig.relay.revoke(grant), 10)
    with contextlib.suppress(httpx.HTTPError):
        await answer


def test_a_revoke_during_a_journal_append_waits_for_the_row_before_closing() -> None:
    async def check(rig: Rig) -> None:
        writer = HeldWriter(rig.journals, CHAT)
        await _revoke_mid_append(rig, writer, release_after=0.3)
        assert [(row.status, row.input_tokens, row.output_tokens) for row in rig.usage] == [
            (200, 120, 9)
        ]
        assert (rig.journals.closed, rig.alerts) == ([CHAT], [])

    run(check)


def test_a_journal_append_that_outlasts_the_revoke_wait_alerts_the_chat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("qma.harness.relay.STOP_WAIT_S", 0.3)

    async def check(rig: Rig) -> None:
        writer = HeldWriter(rig.journals, CHAT)
        await _revoke_mid_append(rig, writer, release_after=1.0)
        assert rig.journals.closed == [CHAT]
        assert rig.alerts[0] == (
            "usage journal: a write was still running when the writer closed; "
            "that request's usage may not be recorded"
        )

    run(check)


NOT_ONE_OBJECT = "the request body is not one JSON object with unique keys, nested 512 deep at most"
ESCAPED_TOKEN = b"sk-ant-oat01\\u002d" + TAIL.encode()


@pytest.mark.parametrize(
    "content",
    [
        b'{"model":"anthropic/claude-opus-4","model":"kimi-k3","messages":[]}',
        b'{"model":"kimi-k3","messages":[{"role":"user","content":"a","content":"b"}]}',
        b'{"model":"kimi-k3","messages":[],"system":"' + ESCAPED_TOKEN + b'","system":"x"}',
    ],
    ids=["model", "nested", "escaped-token"],
)
def test_a_body_with_a_repeated_json_key_is_refused_and_never_forwarded(content: bytes) -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", content, bearer=grant.secret)
        assert answer.status_code == 400
        assert answer.json()["error"]["message"] == NOT_ONE_OBJECT
        assert rig.upstream.seen == []

    run(check)


def raw_event(name: str | None, data: object) -> bytes:
    named = f"event: {name}\n" if name else ""
    return f"{named}data: {json.dumps(data)}\n\n".encode()


MALFORMED_START = "the provider sent a malformed message_start"


def raw_start(message: bytes) -> bytes:
    return b'event: message_start\ndata: {"type":"message_start","message":' + message + b"}\n\n"


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (sse({"type": "message_start", "message": "kimi-k3"}, TEXT), MALFORMED_START),
        (
            sse({"type": "message_start", "message": {"model": "kimi-k3", "usage": "x"}}, TEXT),
            MALFORMED_START,
        ),
        (sse({"type": "message_start", "message": {"usage": {}}}, TEXT), MALFORMED_START),
        (sse({"type": "message_start", "message": {"model": 7}}, TEXT), MALFORMED_START),
        (
            raw_event("message_start", {"message": {"model": "anthropic/claude-opus-4"}})
            + raw_event("content_block_delta", {"delta": {"text": "secret"}})
            + sse({"type": "error", "error": {"type": "overloaded_error"}}),
            "family guard: kimi served anthropic/claude-opus-4",
        ),
        (
            raw_event("ping", CLAUDE_START) + sse(TEXT),
            "the provider sent an event named ping whose type is message_start",
        ),
        (
            sse({"type": "message_start", "message": {"model": "kimi-k3"}})
            + raw_event("message_delta", {"type": "message_delta", "usage": "x"}),
            "the provider sent a malformed message_delta",
        ),
        (
            raw_event(None, {"type": ["message_start"]}) + sse(TEXT),
            "the provider sent an event whose type is not a string",
        ),
        (
            raw_start(b'{"model":"kimi-k3","x":' + b"[" * 100_000 + b"]" * 100_000 + b"}")
            + sse(TEXT),
            MALFORMED_START,
        ),
    ],
    ids=[
        "message-not-object",
        "usage-not-object",
        "no-model",
        "model-not-string",
        "named-start-typeless",
        "name-type-mismatch",
        "delta-usage-not-object",
        "type-not-string",
        "start-nested-too-deep",
    ],
)
def test_a_malformed_stream_ends_in_an_error_event_an_alert_and_one_row(
    content: bytes, message: str
) -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert answer.status_code == 200
        last = answer.text.split("\n\n")[-2]
        assert last.startswith("event: error\n")
        assert message in last
        assert "secret" not in answer.text
        assert "claude" not in answer.text.removesuffix(f"{last}\n\n")
        assert len(rig.alerts) == 1
        assert [row.status for row in rig.usage] == [200]

    run(check, handler=sse_reply(content))


def test_a_provider_error_before_message_start_passes_alone() -> None:
    error = {"type": "error", "error": {"type": "overloaded_error", "message": "busy"}}
    content = raw_event(None, {"delta": {"text": "secret"}}) + sse({"type": "ping"}, error)

    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert answer.content == sse(error)
        assert [row.status for row in rig.usage] == [200]

    run(check, handler=sse_reply(content))


def test_a_stale_revoke_of_a_replaced_grant_leaves_the_new_one_serving() -> None:
    async def check(rig: Rig) -> None:
        old = await rig.relay.grant(CHAT, ProfileName("kimi"))
        new = await rig.relay.grant(CHAT, ProfileName("kimi"))
        await rig.relay.revoke(old)
        answer = await rig.post("/v1/messages", body(), bearer=new.secret)
        assert (answer.status_code, answer.content) == (200, stream("kimi-k3"))
        assert rig.relay.grants == 1

    run(check)


def test_a_json_reply_whose_usage_is_not_an_object_still_answers_and_journals() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"model": "kimi-k3", "usage": "x"})

    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", body(), bearer=grant.secret)
        assert (answer.status_code, answer.json()) == (200, {"model": "kimi-k3", "usage": "x"})
        assert [(row.status, row.input_tokens) for row in rig.usage] == [(200, 0)]

    run(check, handler=handler)


def test_close_waits_for_a_row_whose_writer_is_still_opening() -> None:
    async def check(rig: Rig) -> None:
        entered, release = threading.Event(), threading.Event()

        def slow_open(session: SessionId) -> Writer:
            entered.set()
            release.wait(5)
            return rig.journals.open(session)

        rig.relay.journal = slow_open
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = asyncio.create_task(rig.post("/v1/messages", body(), bearer=grant.secret))
        await asyncio.to_thread(entered.wait, 5)
        threading.Timer(0.3, release.set).start()
        await asyncio.wait_for(rig.relay.close(), 10)
        assert (rig.journals.opened, rig.journals.closed, len(rig.usage)) == ([CHAT], [CHAT], 1)
        with contextlib.suppress(httpx.HTTPError):
            await answer

    run(check)


def test_a_stream_with_no_message_start_is_stopped_at_120_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed = asyncio.Event()

    class Silent(httpx.AsyncByteStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            await closed.wait()
            yield b""

        async def aclose(self) -> None:
            closed.set()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=Silent(), headers={"content-type": "text/event-stream"})

    async def check(rig: Rig) -> None:
        loop = asyncio.get_running_loop()
        real = loop.time
        skew = [0.0]
        monkeypatch.setattr(loop, "time", lambda: real() + skew[0])
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        auth = {"authorization": f"Bearer {grant.secret}"}
        async with (
            httpx.AsyncClient(base_url=rig.relay.base_url, trust_env=False, timeout=None) as client,
            client.stream("POST", "/v1/messages", json=body(), headers=auth) as answer,
        ):
            chunks = aiter(answer.aiter_bytes())
            await asyncio.sleep(0.1)
            skew[0] = 118.5
            first = asyncio.ensure_future(anext(chunks))
            await asyncio.sleep(0.2)
            assert not first.done()
            skew[0] = 121.0
            chunk = await asyncio.wait_for(first, 2)
        assert chunk.startswith(b"event: error\n")
        assert b"no message_start in 120 s" in chunk
        assert closed.is_set()

    run(check, handler=handler)


def nested(depth: int) -> bytes:
    return b'{"model":"kimi-k3","messages":[],"x":' + b"[" * depth + b"]" * depth + b"}"


@pytest.mark.parametrize(
    ("content", "status"),
    [(nested(511), 200), (nested(512), 400), (nested(1_500), 400), (nested(100_000), 400)],
    ids=["512-levels", "513-levels", "1501-levels", "100001-levels"],
)
def test_a_body_nested_past_512_levels_is_refused_and_never_forwarded(
    content: bytes, status: int
) -> None:
    async def check(rig: Rig) -> None:
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = await rig.post("/v1/messages", content, bearer=grant.secret)
        assert answer.status_code == status
        assert len(rig.upstream.seen) == (status == 200)
        if status == 400:
            assert answer.json()["error"]["message"] == NOT_ONE_OBJECT

    run(check)


@dataclass
class FailingTogether(Writer):
    both: threading.Barrier = field(default_factory=lambda: threading.Barrier(2))

    def append(self, usage: RelayUsage) -> None:
        self.both.wait(5)
        raise OSError("disk full")


def test_two_journal_writes_that_fail_together_never_hold_the_reply_or_cry_wolf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("qma.harness.relay.STOP_WAIT_S", 10.0)

    async def check(rig: Rig) -> None:
        writer = FailingTogether(rig.journals, CHAT)
        rig.relay.journal = lambda _session: writer
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        posts = (rig.post("/v1/messages", body(), bearer=grant.secret) for _ in range(2))
        answers = await asyncio.wait_for(asyncio.gather(*posts), 3)
        assert [(answer.status_code, answer.content) for answer in answers] == [
            (200, stream("kimi-k3"))
        ] * 2
        assert rig.alerts == [
            "usage journal: OSError: disk full; this request's usage was not recorded"
        ] * 2
        assert rig.journals.closed == [CHAT]

    run(check)


async def refused(_request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("refused")


async def hung(_request: httpx.Request) -> httpx.Response:
    await asyncio.Event().wait()
    raise AssertionError


@pytest.mark.parametrize(
    ("handler", "status"), [(refused, 502), (hung, 499)], ids=["no-answer", "client-gone"]
)
def test_a_revoke_during_a_teed_row_waits_for_the_row_before_closing(
    handler: Callable[[httpx.Request], Any], status: int
) -> None:
    async def check(rig: Rig) -> None:
        writer = HeldWriter(rig.journals, CHAT)
        rig.relay.journal = lambda _session: writer
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))

        async def post() -> None:
            auth = {"authorization": f"Bearer {grant.secret}"}
            with contextlib.suppress(httpx.HTTPError):
                async with httpx.AsyncClient(
                    base_url=rig.relay.base_url, trust_env=False, timeout=0.3
                ) as client:
                    await client.post("/v1/messages", json=body(), headers=auth)

        answer = asyncio.create_task(post())
        await asyncio.to_thread(writer.entered.wait, 5)
        threading.Timer(0.3, writer.release.set).start()
        await asyncio.wait_for(rig.relay.revoke(grant), 10)
        await answer
        assert [(row.status, row.input_tokens) for row in rig.usage] == [(status, 0)]
        assert (rig.journals.closed, rig.alerts) == ([CHAT], [])

    run(check, handler=handler)


def test_a_revoke_waits_5_seconds_for_a_journal_row_then_closes_and_alerts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def check(rig: Rig) -> None:
        loop = asyncio.get_running_loop()
        real = loop.time
        skew = [0.0]
        monkeypatch.setattr(loop, "time", lambda: real() + skew[0])
        writer = HeldWriter(rig.journals, CHAT)
        rig.relay.journal = lambda _session: writer
        grant = await rig.relay.grant(CHAT, ProfileName("kimi"))
        answer = asyncio.create_task(rig.post("/v1/messages", body(), bearer=grant.secret))
        await asyncio.to_thread(writer.entered.wait, 5)
        revoking = asyncio.ensure_future(rig.relay.revoke(grant))
        await asyncio.sleep(0.1)
        skew[0] = 4.5
        await asyncio.sleep(0.2)
        assert not revoking.done()
        skew[0] = 5.5
        await asyncio.wait_for(revoking, 2)
        writer.release.set()
        with contextlib.suppress(httpx.HTTPError):
            await answer
        assert rig.journals.closed == [CHAT]
        assert rig.alerts[0] == (
            "usage journal: a write was still running when the writer closed; "
            "that request's usage may not be recorded"
        )

    run(check)
