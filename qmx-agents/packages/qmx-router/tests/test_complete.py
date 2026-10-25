"""`complete` replays recorded provider answers: one request, one lease, one journal row.

The transports below are recorded answers in the shape their provider sends: OpenRouter's
Anthropic-compatible reply on its DeepSeek row, DeepSeek's own route, and a credit refusal. The
expected text, account and journal row are literals.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest

from qmx_router.complete import (
    Ask,
    Completion,
    Refused,
    ask_body,
    chat_request,
    check,
    streamed_answer,
)
from qmx_router.ids import SessionId
from qmx_router.pool import AccountPool, AccountSpec
from qmx_router.profiles import ModelId, ProfileName, Profiles, SecretRef, parse_profiles
from qmx_router.registry import ModelRow, QmxId, bundled
from qmx_router.relay import Relay, RelayUsage

OPENROUTER_ROW: dict[str, Any] = {
    "base_url": "https://openrouter.ai/api",
    "credential_ref": "qmx/openrouter",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "deepseek/deepseek-v4.1-flash"),
}
DEEPSEEK_ROW: dict[str, Any] = {
    "base_url": "https://api.deepseek.com/anthropic",
    "credential_ref": "qmx/deepseek",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "deepseek-v4-pro"),
}
DECISION: dict[str, object] = {
    "type": "object",
    "required": ["bias", "why"],
    "additionalProperties": False,
    "properties": {
        "bias": {"type": "string", "enum": ["bullish", "bearish", "neutral"]},
        "why": {"type": "string"},
    },
}
OPENROUTER_MODEL = "deepseek/deepseek-v4.1-flash"
MESSAGES = [{"role": "user", "content": [{"type": "text", "text": "bias?"}]}]


def replied(text: str, model: str = OPENROUTER_MODEL) -> dict[str, Any]:
    """One finished `/v1/messages` reply, in Anthropic's own envelope."""
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 41, "output_tokens": 9},
    }


@dataclass
class Journals:
    rows: list[RelayUsage] = field(default_factory=list[RelayUsage])

    def open(self, _session: SessionId) -> Writer:
        return Writer(self)


@dataclass
class Writer:
    journals: Journals

    def append(self, usage: RelayUsage) -> None:
        self.journals.rows.append(usage)

    def close(self) -> None:
        return None


@dataclass
class Rig:
    relay: Relay
    journals: Journals
    pool: AccountPool

    async def ask(self, model: str, **fields: Any) -> Completion:
        return await self.relay.complete(model, MESSAGES, **fields)


def run(
    test: Callable[[Rig], Any],
    *,
    rows: Mapping[str, object],
    handler: Callable[[httpx.Request], httpx.Response],
    pool: AccountPool,
) -> None:
    async def main() -> None:
        journals = Journals()

        async def alert(_chat: SessionId, _reason: str) -> None:
            return None

        def profiles() -> Profiles:
            return parse_profiles(rows)

        def fake(reference: str) -> str:
            return f"key-for-{reference}"

        relay = await Relay(
            secrets=fake,
            journal=journals.open,
            alert=alert,
            profiles=profiles,
            pool=pool,
            transport=httpx.MockTransport(handler),
        ).start()
        try:
            await test(Rig(relay, journals, pool))
        finally:
            await relay.close()

    asyncio.run(main())


def one_account(provider: str = "openrouter", credential: str = "qmx/openrouter") -> AccountPool:
    return AccountPool(
        [AccountSpec(provider, ProfileName(provider), credential=SecretRef(credential))]
    )


def test_complete_answers_the_openrouter_deepseek_row_with_a_schema() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/messages"
        body = json.loads(request.content)
        assert body["model"] == OPENROUTER_MODEL
        assert body["stream"] is False
        assert "Answer with one JSON document" in body["system"]
        return httpx.Response(200, json=replied('{"bias": "neutral", "why": "no driver data"}'))

    async def check(rig: Rig) -> None:
        answer = await rig.ask(
            "openrouter/deepseek/deepseek-v4.1-flash", schema=DECISION, session="run-7:writer"
        )
        assert answer.data == {"bias": "neutral", "why": "no driver data"}
        assert (answer.model, answer.account) == (OPENROUTER_MODEL, "openrouter")
        assert answer.usage == {"input_tokens": 41, "output_tokens": 9}
        assert [(row.profile, row.path, row.status, row.account) for row in rig.journals.rows] == [
            (ProfileName("openrouter"), "/complete", 200, "openrouter")
        ]

    run(check, rows={"openrouter": OPENROUTER_ROW}, handler=handler, pool=one_account())


def test_complete_reads_another_providers_anthropic_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/anthropic/v1/messages"
        return httpx.Response(200, json=replied("OK", model="deepseek-v4-pro"))

    async def check(rig: Rig) -> None:
        answer = await rig.ask("deepseek/deepseek-v4-pro")
        assert (answer.text, answer.data) == ("OK", None)
        assert (answer.model, answer.account) == ("deepseek-v4-pro", "deepseek")

    run(
        check,
        rows={"deepseek": DEEPSEEK_ROW},
        handler=handler,
        pool=one_account("deepseek", "qmx/deepseek"),
    )


def test_a_plan_row_is_refused_by_name() -> None:
    async def check(rig: Rig) -> None:
        with pytest.raises(Refused) as raised:
            await rig.ask("claude/haiku")
        assert "one-turn, tool-less chat" in str(raised.value)
        assert rig.journals.rows == []

    run(
        check,
        rows={"openrouter": OPENROUTER_ROW},
        handler=lambda _request: httpx.Response(500),
        pool=one_account(),
    )


def test_a_429_on_the_first_account_moves_the_request_to_the_second() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers["authorization"] == "Bearer key-for-qmx/primary":
            return httpx.Response(
                429,
                json={"type": "error", "error": {"type": "rate_limit_error", "message": "slow"}},
                headers={"retry-after": "30"},
            )
        return httpx.Response(200, json=replied('{"bias": "bearish", "why": "oil"}'))

    pool = AccountPool(
        [
            AccountSpec("primary", ProfileName("openrouter"), credential=SecretRef("qmx/primary")),
            AccountSpec("backup", ProfileName("openrouter"), credential=SecretRef("qmx/backup")),
        ]
    )

    async def check(rig: Rig) -> None:
        answer = await rig.ask("openrouter/deepseek/deepseek-v4.1-flash", schema=DECISION)
        assert (answer.account, answer.data) == ("backup", {"bias": "bearish", "why": "oil"})
        assert rig.pool.state("primary", OPENROUTER_MODEL)[0] == "cooling"
        assert [row.account for row in rig.journals.rows] == ["backup"]

    run(check, rows={"openrouter": OPENROUTER_ROW}, handler=handler, pool=pool)


def test_a_credit_refusal_names_the_class_and_writes_no_row() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            402,
            json={"error": {"message": "Insufficient credits. Add more credits to continue."}},
        )

    async def check(rig: Rig) -> None:
        with pytest.raises(Refused) as raised:
            await rig.ask("openrouter/deepseek/deepseek-v4.1-flash")
        assert "billing: Insufficient credits" in str(raised.value)
        assert rig.pool.state("openrouter", OPENROUTER_MODEL)[0] == "cooling"
        assert rig.journals.rows == []

    run(check, rows={"openrouter": OPENROUTER_ROW}, handler=handler, pool=one_account())


def test_a_refused_schema_is_a_refusal_not_an_answer() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=replied('{"bias": "neutral"}'))

    async def check(rig: Rig) -> None:
        with pytest.raises(Refused) as raised:
            await rig.ask("openrouter/deepseek/deepseek-v4.1-flash", schema=DECISION)
        assert str(raised.value) == "answer is missing why"

    run(check, rows={"openrouter": OPENROUTER_ROW}, handler=handler, pool=one_account())


def test_the_schema_check_reads_a_literal_document() -> None:
    check(DECISION, {"bias": "bullish", "why": "carry"})
    with pytest.raises(Refused) as raised:
        check(DECISION, {"bias": "sideways", "why": "carry"})
    assert str(raised.value) == "answer.bias is not one of the schema's enum values"
    with pytest.raises(Refused) as extra:
        check(DECISION, {"bias": "bullish", "why": "carry", "confidence": 0.4})
    assert str(extra.value) == "answer carries confidence, which the schema does not allow"


def test_a_chat_wire_row_carries_the_schema_as_response_format() -> None:
    """The chat lane takes a schema in its own field, which the Anthropic wire has no room for."""
    row = ModelRow(
        qmx_id=QmxId("opencode-go/glm-5.3"),
        provider=ProfileName("opencode-go"),
        native=ModelId("glm-5.3"),
        wire="openai_chat",
    )
    body = json.loads(chat_request(row, Ask(MESSAGES, schema=DECISION), "glm-5.3"))
    assert body["response_format"]["json_schema"]["schema"] == DECISION
    assert body["stream"] is True
    assert "Answer with one JSON document" in json.dumps(body)
    plain = ask_body(Ask(MESSAGES), "glm-5.3")
    assert "system" not in plain
    assert bundled().model(row.qmx_id) == row or row.provider in bundled().providers


CHAT_CHUNKS: list[dict[str, object]] = [
    {"id": "c1", "model": "glm-5.3", "choices": [{"index": 0, "delta": {"content": "bull"}}]},
    {"id": "c1", "choices": [{"index": 0, "delta": {"content": "ish"}}]},
    {"id": "c1", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
    {"id": "c1", "choices": [], "usage": {"prompt_tokens": 12, "completion_tokens": 2}},
]


def test_a_multi_chunk_chat_stream_reads_as_one_answer() -> None:
    lines: list[str] = []
    for chunk in CHAT_CHUNKS:
        lines += [f"data: {json.dumps(chunk)}", ""]
    lines += ["data: [DONE]", ""]
    row = bundled().model("opencode-go/glm-5.3")
    answer = streamed_answer(lines, row, "glm-5.3")
    assert (answer.text, answer.model, answer.usage["output_tokens"]) == ("bullish", "glm-5.3", 2)
