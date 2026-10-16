"""The relay's GPT lane over an in-process OpenAI: grants, the probe grant, consent, the
translated stream and its usage row."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
import test_chat
from test_chat import run

import qma.harness.harness
import qma.harness.relay
from qma.gpt import probe
from qma.gpt.probe import PROBE_FILE, ProbePassed, ProbeRun, stored_result, translator_version
from qma.gpt.siwc import Record, SiwcSession
from qma.harness import Harness, LaunchRefused, NewChat, QmxHome
from qma.harness.home import SessionId, read_record
from qma.harness.profiles import GptPlan, ProfileName, parse_profiles
from qma.harness.relay import GrantRefused, Relay, RelayUsage
from qma.harness.routes import control_service

CHAT = SessionId("0b9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e1f")
GPT = ProfileName("gpt")
API = "https://api.openai.test/v1"
GPT_ROW = {"tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "gpt-6.1-sol")}
HELLO = {
    "model": "opus",
    "max_tokens": 64,
    "temperature": 1,
    "stream": True,
    "messages": [{"role": "user", "content": "hi"}],
}


def responses_sse(model: str) -> bytes:
    events: list[dict[str, Any]] = [
        {"type": "response.created", "response": {"id": "resp_1", "model": model}},
        {"type": "response.output_item.added", "output_index": 0, "item": {"type": "message"}},
        {"type": "response.output_text.delta", "output_index": 0, "delta": "hello"},
        {"type": "response.output_item.done", "output_index": 0, "item": {"type": "message"}},
        {
            "type": "response.completed",
            "response": {
                "output": [],
                "usage": {
                    "input_tokens": 21,
                    "output_tokens": 5,
                    "input_tokens_details": {"cached_tokens": 3},
                },
            },
        },
    ]
    return b"".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n".encode() for e in events)


@dataclass
class OpenAI:
    served: str = "gpt-6.1-sol"
    status: int = 200
    seen: list[httpx.Request] = field(default_factory=list[httpx.Request])

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        if self.status != 200:
            error = {"message": "Unsupported parameter: temperature", "code": None, "param": None}
            return httpx.Response(self.status, json={"error": error})
        return httpx.Response(
            200, content=responses_sse(self.served), headers={"content-type": "text/event-stream"}
        )


class MemoryVault:
    value: str | None = None

    def get(self) -> str | None:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


@dataclass
class Rows:
    rows: list[RelayUsage] = field(default_factory=list[RelayUsage])

    def open(self, session: SessionId) -> Rows:
        return self

    def append(self, usage: RelayUsage) -> None:
        self.rows.append(usage)

    def close(self) -> None:
        return None


@dataclass
class Rig:
    relay: Relay
    openai: OpenAI
    session: SiwcSession
    rows: Rows
    passed: ProbePassed

    async def post(
        self, secret: str, body: dict[str, Any], path: str = "/v1/messages"
    ) -> httpx.Response:
        async with httpx.AsyncClient(base_url=self.relay.base_url, trust_env=False) as client:
            return await client.post(path, json=body, headers={"authorization": f"Bearer {secret}"})


def a_pass(state: Path) -> ProbePassed:
    state.mkdir(parents=True, exist_ok=True)
    document = {
        "at": datetime(2026, 10, 15, tzinfo=UTC).isoformat(),
        "outcome": "passed",
        "translator_version": translator_version(),
        "model": "gpt-6.1-sol",
    }
    (state / PROBE_FILE).write_text(json.dumps(document), encoding="utf-8")
    found = stored_result(state, translator_version())
    assert isinstance(found, ProbePassed)
    return found


@asynccontextmanager
async def rig(tmp_path: Path, openai: OpenAI | None = None) -> AsyncIterator[Rig]:
    openai = openai or OpenAI()
    rows = Rows()
    session = SiwcSession(
        Record("oaiapp_1", "urn:uuid:1", "refresh-1", ("chatgpt.tokens.use.direct",)),
        MemoryVault(),
        api=API,
    )
    await session.accept({"access_token": "access-1", "expires_in": 3600})

    async def alert(chat: SessionId, reason: str) -> None:
        return None

    relay = await Relay(
        secrets=lambda reference: "",
        journal=rows.open,
        alert=alert,
        profiles=lambda: parse_profiles({"gpt": GPT_ROW}),
        transport=httpx.MockTransport(openai),
    ).start()
    try:
        yield Rig(relay, openai, session, rows, a_pass(tmp_path))
    finally:
        await relay.close()


def events(response: httpx.Response) -> list[dict[str, Any]]:
    return [
        json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")
    ]


def test_a_gpt_grant_is_refused_while_the_lane_is_closed(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path) as found:
            with pytest.raises(GrantRefused) as refused:
                await found.relay.grant(CHAT, GPT)
            assert str(refused.value) == (
                "the GPT lane is closed: no GPT probe has passed for this translator version; "
                "type /login chatgpt"
            )

    asyncio.run(body())


def test_a_hello_streams_through_the_open_lane_and_is_journaled(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path) as found:
            await found.relay.open_gpt_lane(found.passed, found.session)
            grant = await found.relay.grant(CHAT, GPT)
            reply = await found.post(grant.secret, HELLO)
            assert reply.status_code == 200
            assert reply.headers["content-type"] == "text/event-stream"
            assert [event["type"] for event in events(reply)] == [
                "message_start",
                "content_block_start",
                "content_block_delta",
                "content_block_stop",
                "message_delta",
                "message_stop",
            ]
            sent = found.openai.seen[0]
            assert str(sent.url) == f"{API}/responses"
            assert sent.headers["authorization"] == "Bearer access-1"
            assert json.loads(sent.content) == {
                "model": "gpt-6.1-sol",
                "input": [{"role": "user", "content": "hi"}],
                "store": False,
                "stream": True,
            }
            assert found.rows.rows == [
                RelayUsage(
                    session_id=CHAT,
                    profile=GPT,
                    path="/v1/messages",
                    status=200,
                    model="gpt-6.1-sol",
                    input_tokens=21,
                    output_tokens=5,
                    cache_read_tokens=3,
                )
            ]

    asyncio.run(body())


def test_a_non_streaming_request_gets_one_message(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path) as found:
            await found.relay.open_gpt_lane(found.passed, found.session)
            grant = await found.relay.grant(CHAT, GPT)
            reply = await found.post(grant.secret, HELLO | {"stream": False})
            assert reply.json() == {
                "id": "msg_resp_1",
                "type": "message",
                "role": "assistant",
                "model": "gpt-6.1-sol",
                "content": [{"type": "text", "text": "hello"}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 21, "output_tokens": 5, "cache_read_input_tokens": 3},
            }

    asyncio.run(body())


def test_an_unattended_gpt_grant_needs_background_consent(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path) as found:
            await found.relay.open_gpt_lane(found.passed, found.session)
            with pytest.raises(GrantRefused) as refused:
                await found.relay.grant(CHAT, GPT, unattended=True)
            assert str(refused.value) == (
                "a Background GPT chat needs your consent to use your ChatGPT plan unattended; "
                "/login chatgpt asks for it"
            )
            await found.session.set_background_consent(True)
            grant = await found.relay.grant(CHAT, GPT, unattended=True)
            assert (await found.post(grant.secret, HELLO)).status_code == 200

    asyncio.run(body())


def test_a_probe_grant_serves_its_run_once_and_is_spent_after(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path) as found:
            profile = parse_profiles({"gpt": GPT_ROW}).get(GPT)
            assert isinstance(profile, GptPlan)
            run = ProbeRun("6f1e2d3c-4b5a-4968-8776-655443322110", _mint=probe._MINT)  # pyright: ignore[reportPrivateUsage]
            grant = await found.relay.probe_grant(run, found.session, profile)
            assert found.relay.gpt is None
            assert (await found.post(grant.secret, HELLO)).status_code == 200
            with pytest.raises(GrantRefused) as refused:
                await found.relay.probe_grant(run, found.session, profile)
            assert str(refused.value) == f"probe run {run.run_id} already had its grant"
            await found.relay.revoke(grant)
            spent = await found.post(grant.secret, HELLO)
            assert (spent.status_code, spent.json()["error"]["message"]) == (
                401,
                "no live relay grant",
            )

    asyncio.run(body())


def test_closing_the_lane_revokes_chat_grants(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path) as found:
            await found.relay.open_gpt_lane(found.passed, found.session)
            grant = await found.relay.grant(CHAT, GPT)
            await found.relay.close_gpt_lane()
            assert (await found.post(grant.secret, HELLO)).status_code == 401
            assert found.relay.gpt is None

    asyncio.run(body())


def test_a_non_gpt_served_model_ends_the_stream_before_any_output(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path, OpenAI(served="claude-opus-5-5")) as found:
            await found.relay.open_gpt_lane(found.passed, found.session)
            grant = await found.relay.grant(CHAT, GPT)
            assert events(await found.post(grant.secret, HELLO)) == [
                {
                    "type": "error",
                    "error": {
                        "type": "invalid_request_error",
                        "message": "family guard: gpt served 'claude-opus-5-5' is not a GPT model",
                    },
                }
            ]
            assert found.relay.counters.family == 1

    asyncio.run(body())


def test_a_route_400_becomes_an_anthropic_invalid_request(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path, OpenAI(status=400)) as found:
            await found.relay.open_gpt_lane(found.passed, found.session)
            grant = await found.relay.grant(CHAT, GPT)
            reply = await found.post(grant.secret, HELLO)
            assert (reply.status_code, reply.json()) == (
                400,
                {
                    "type": "error",
                    "error": {
                        "type": "invalid_request_error",
                        "message": "ChatGPT: Unsupported parameter: temperature",
                    },
                },
            )

    asyncio.run(body())


def test_count_tokens_and_the_tier_guard_on_the_gpt_lane(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path) as found:
            await found.relay.open_gpt_lane(found.passed, found.session)
            grant = await found.relay.grant(CHAT, GPT)
            counted = await found.post(grant.secret, HELLO, "/v1/messages/count_tokens")
            assert counted.json() == {"input_tokens": 20}
            refused = await found.post(grant.secret, HELLO | {"model": "claude-opus-5-5"})
            assert (refused.status_code, refused.json()["error"]["message"]) == (
                400,
                "tier guard: claude-opus-5-5 is not one of gpt's tier models",
            )
            assert found.openai.seen == []

    asyncio.run(body())


def test_a_pass_for_another_translator_does_not_open_the_lane(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path) as found:
            other = ProbePassed(
                found.passed.at, "0000000000000000", "gpt-6.1-sol", _mint=probe._MINT
            )  # pyright: ignore[reportPrivateUsage]
            with pytest.raises(GrantRefused):
                await found.relay.open_gpt_lane(other, found.session)
            assert found.relay.gpt is None

    asyncio.run(body())


home = test_chat.home


def gpt_home(home: QmxHome, monkeypatch: pytest.MonkeyPatch, stored: SiwcSession | None) -> None:
    control_service(home).settings_put("providers", {"gpt": GPT_ROW})
    monkeypatch.setattr(qma.harness.harness.siwc, "load", lambda: stored)


def test_a_gpt_chat_needs_a_stored_pass_for_this_translator(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    gpt_home(home, monkeypatch, None)

    async def body(harness: Harness) -> None:
        with pytest.raises(LaunchRefused) as refused:
            await harness.start_chat(NewChat(title="s16", profile=GPT))
        assert str(refused.value) == (
            "GPT needs a passed GPT probe for this translator version; type /login chatgpt"
        )

    run(body, home)


def test_a_stored_pass_without_a_sign_in_keeps_the_lane_closed(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    gpt_home(home, monkeypatch, None)
    a_pass(home.state_dir)

    async def body(harness: Harness) -> None:
        with pytest.raises(LaunchRefused) as refused:
            await harness.start_chat(NewChat(title="s16", profile=GPT))
        assert str(refused.value) == "the GPT lane is closed: no ChatGPT sign-in is stored"

    run(body, home)


def test_a_stored_pass_and_sign_in_open_the_lane_at_open(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    signed_in = SiwcSession(
        Record("oaiapp_1", "urn:uuid:1", "refresh-1", ("chatgpt.tokens.use.direct",)),
        MemoryVault(),
    )
    gpt_home(home, monkeypatch, signed_in)
    passed = a_pass(home.state_dir)

    async def body(harness: Harness) -> None:
        relay = harness._deps.relay  # pyright: ignore[reportPrivateUsage]
        assert relay.gpt is not None
        assert (relay.gpt.passed, relay.siwc) == (passed, signed_in)
        chat = await harness.start_chat(NewChat(title="s16", profile=GPT))
        assert read_record(home, chat) is not None
        (home.state_dir / PROBE_FILE).unlink()
        with pytest.raises(LaunchRefused):
            await harness.start_chat(NewChat(title="s16", profile=GPT))
        assert (relay.gpt, relay.siwc) == (None, signed_in)

    run(body, home)


@dataclass
class SlowOpenAI(OpenAI):
    """Stalls after `response.created`, as the route does while the model thinks."""

    async def stalled(self) -> AsyncIterator[bytes]:
        events = responses_sse(self.served).split(b"\n\n")
        yield events[0] + b"\n\n"
        await asyncio.sleep(0.3)
        yield b"\n\n".join(events[1:])

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        return httpx.Response(
            200, content=self.stalled(), headers={"content-type": "text/event-stream"}
        )


def test_a_stalled_stream_gets_pings_and_still_completes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(qma.harness.relay, "PING_S", 0.1)

    async def body() -> None:
        async with rig(tmp_path, SlowOpenAI()) as found:
            await found.relay.open_gpt_lane(found.passed, found.session)
            grant = await found.relay.grant(CHAT, GPT)
            kinds = [event["type"] for event in events(await found.post(grant.secret, HELLO))]
            assert kinds[0] == "message_start"
            assert kinds[1] == "ping"
            assert [kind for kind in kinds if kind != "ping"] == [
                "message_start",
                "content_block_start",
                "content_block_delta",
                "content_block_stop",
                "message_delta",
                "message_stop",
            ]

    asyncio.run(body())


def test_no_repr_on_the_lane_shows_a_token(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path) as found:
            lane = await found.relay.open_gpt_lane(found.passed, found.session)
            shown = repr(lane) + repr(found.relay.siwc) + repr(found.session.record)
            assert "access-1" not in shown
            assert "refresh-1" not in shown
            assert "oaiapp_1" in shown

    asyncio.run(body())


def test_removing_the_stored_pass_stops_new_grants_for_open_chats(tmp_path: Path) -> None:
    async def body() -> None:
        async with rig(tmp_path) as found:
            found.relay.probe_state = tmp_path
            await found.relay.open_gpt_lane(found.passed, found.session)
            await found.relay.grant(CHAT, GPT)
            (tmp_path / PROBE_FILE).unlink()
            with pytest.raises(GrantRefused) as refused:
                await found.relay.grant(CHAT, GPT)
            assert str(refused.value) == (
                "the GPT lane is closed: no GPT probe has passed for this translator version; "
                "type /login chatgpt"
            )
            assert found.relay.gpt is None

    asyncio.run(body())


def test_login_shows_why_the_rotated_token_was_not_stored(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    signed_in = SiwcSession(
        Record("oaiapp_1", "urn:uuid:1", "refresh-1", ("chatgpt.tokens.use.direct",)),
        MemoryVault(),
    )
    gpt_home(home, monkeypatch, signed_in)
    a_pass(home.state_dir)

    def refuse(value: str) -> None:
        raise OSError("CredWrite")

    async def body(harness: Harness) -> None:
        monkeypatch.setattr(signed_in.vault, "set", refuse)
        await signed_in.accept({"access_token": "access-2", "expires_in": 3600})
        status = await harness.gpt_login(sign_in=False)
        assert status.lines[:2] == (
            "Signed in to ChatGPT for QMA (stored sign-in).",
            "Warning: the rotated ChatGPT refresh token could not be stored in qmx/chatgpt "
            "(OSError); sign in again after this host stops.",
        )
        assert status.lane

    run(body, home)
