"""The `llm` node over a fake harness port: one repair turn in the same chat, a run whose span names
the resolved candidate and its tokens, the fake switch that calls no model, a provider failure
redacted before the ledger, and the `complete` path a key row takes with no chat at all (RTR5)."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

from fake_library import fake_service
from fake_port import TOKENS, FakePort

from qmx_engine.admission import Admission
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.spans import Span
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import Failed, NodeJob, Ok
from qmx_engine.nodes.llm import BAD_OUTPUT, Llm
from qmx_engine.ports.harness_adapter import Turn
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.router import Reply, Row, adopt
from qmx_engine.runner import Engine, Outcome
from qmx_engine.service.context import OPERATOR
from qmx_engine.settings import DEFAULTS

ONE_LLM = Path(__file__).resolve().parent / "fixtures" / "workflows" / "one-llm"
GOOD = '{"country": "France", "capital": "Paris"}'


class Router:
    """A `RouterPort` that answers one schema reply and records the calls a key row makes."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.held: list[tuple[str, str, str]] = []
        self.let_go_calls: list[str] = []

    def rows(self) -> tuple[Row, ...]:
        return (Row("kimi/k3", "kimi", "k3", "strong", 1_000_000),)

    async def complete(
        self,
        role_or_model: str,
        messages: Sequence[Mapping[str, object]],
        *,
        schema: Mapping[str, object] | None = None,
        session: str | None = None,
        system: str = "",
        max_tokens: int = 4096,
        roles: Mapping[str, Sequence[str]] | None = None,
    ) -> Reply:
        self.calls.append(
            {
                "model": role_or_model,
                "messages": [dict(message) for message in messages],
                "schema": schema,
                "session": session,
                "system": system,
            }
        )
        return Reply(
            GOOD,
            "kimi/k3",
            "k3",
            "kimi-1",
            {"input_tokens": 30, "output_tokens": 12},
            {"country": "France", "capital": "Paris"},
            21,
        )

    def hold(self, *, provider: str, model: str, affinity: str) -> str:
        self.held.append((provider, model, affinity))
        return "kimi-1"

    def let_go(self, affinity: str) -> None:
        self.let_go_calls.append(affinity)


def job() -> NodeJob:
    return NodeJob(
        run_id="r1",
        node_id="capital",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="r1:capital:0:-:1",
        node_definition={
            "type": "llm",
            "role": "triage",
            "parameters": {
                "prompt_ref": "prompts/capital.md",
                "schema_ref": "schemas/capital.json",
            },
        },
        inputs={"in": "France"},
        now=None,
        resolved_model={"role": "triage", "profile": "claude", "model": "haiku"},
    )


def llm(port: FakePort, tmp_path: Path) -> Llm:
    return Llm(ONE_LLM, port, Admission(port, DEFAULTS), tmp_path)


def test_an_invalid_answer_gets_one_repair_turn_in_the_same_chat(tmp_path: Path) -> None:
    port = FakePort('{"country": "France"}', f"```json\n{GOOD}\n```")

    result = asyncio.run(llm(port, tmp_path).run(job()))

    assert isinstance(result, Ok)
    assert result.outputs == {"main": {"country": "France", "capital": "Paris"}}
    assert [chat for chat, _ in port.sent] == ["chat-1", "chat-1"]
    assert port.sent[1][1].startswith(
        "That answer does not match the JSON schema "
        "(the document: 'capital' is a required property)"
    )
    assert (result.span["turns"], result.span["repaired"]) == (2, True)
    assert result.span["tokens"] == {"in": 20, "out": 10, "cache_read": 200, "cache_write": 0}
    assert port.chats == [
        {
            "title": "r1:capital:0:-:1",
            "profile": "claude",
            "model": "haiku",
            "tools": (),
            "toolsets": (),
            "skills": (),
            "system": None,
            "compact_at": None,
        }
    ]


def test_a_second_invalid_answer_fails_bad_output_with_a_stable_message(tmp_path: Path) -> None:
    port = FakePort("Paris", "The capital is Paris.")

    result = asyncio.run(llm(port, tmp_path).run(job()))

    assert isinstance(result, Failed)
    assert (result.code, result.message, result.retryable) == ("bad_output", BAD_OUTPUT, True)
    assert len(port.sent) == 2


def test_a_provider_failure_is_redacted_before_it_reaches_the_ledger(tmp_path: Path) -> None:
    leaked = "upstream 401 unauthorized for key sk-or-v1-0123456789abcdef0123456789abcdef"
    port = FakePort(Turn(None, needs_you=f"the turn failed: {leaked}"))

    result = asyncio.run(llm(port, tmp_path).run(job()))

    assert isinstance(result, Failed)
    assert (result.code, result.retryable) == ("auth", False)
    assert result.message == "the turn failed: upstream 401 unauthorized for key [redacted]"


def test_a_key_row_calls_complete_with_no_chat_and_spans_the_router_row(tmp_path: Path) -> None:
    router = Router()
    adopt(router)
    port = FakePort(GOOD)
    key = replace(job(), resolved_model={"role": "triage", "profile": "kimi", "model": "k3"})
    try:
        result = asyncio.run(llm(port, tmp_path).run(key))
    finally:
        adopt(None)

    assert isinstance(result, Ok)
    assert result.outputs == {"main": {"country": "France", "capital": "Paris"}}
    assert port.chats == [] and port.sent == []
    assert router.held == [("kimi", "k3", "r1:capital")]
    assert router.let_go_calls == ["r1:capital"]
    call = router.calls[0]
    assert call["model"] == "kimi/k3"
    assert call["session"] == "r1:capital"
    assert call["messages"] == [
        {"role": "user", "content": [{"type": "text", "text": 'Input:\n{"in": "France"}'}]}
    ]
    assert result.span["router"] == {
        "qmx_id": "kimi/k3",
        "model": "k3",
        "account": "kimi-1",
        "session": "r1:capital",
        "ms": 21,
    }
    assert result.span["tokens"] == {"in": 30, "out": 12, "cache_read": 0}


def test_a_plan_row_keeps_the_chat_even_when_a_router_is_adopted(tmp_path: Path) -> None:
    router = Router()
    adopt(router)
    port = FakePort(GOOD)
    try:
        result = asyncio.run(llm(port, tmp_path).run(job()))
    finally:
        adopt(None)

    assert isinstance(result, Ok)
    assert router.calls == [] and router.held == []
    assert [chat for chat, _ in port.sent] == ["chat-1"]


def run(home: Path, port: FakePort | None, *, fake: bool = False) -> tuple[Outcome, Span]:
    """One run of the one-llm fixture, and the span of its llm attempt."""
    found = checked(ONE_LLM)
    assert not isinstance(found, list), found

    async def go() -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, harness=port)
            return await engine.start(ONE_LLM, found[1], mode="test", inputs=None, fake=fake)

    outcome = asyncio.run(go())
    with Reader.open(home) as reader:
        return outcome, next(s for s in reader.spans(outcome.run_id) if s.node_id == "capital")


def test_a_test_run_spans_the_plan_haiku_candidate_and_its_tokens(tmp_path: Path) -> None:
    port = FakePort(GOOD)

    outcome, span = run(tmp_path, port)

    assert outcome.status == "passed"
    assert outcome.outputs == {"capital": {"main": {"country": "France", "capital": "Paris"}}}
    assert (span.role, span.profile, span.model, span.status) == ("triage", "claude", "haiku", "ok")
    assert span.tokens == TOKENS
    assert port.chats[0]["title"] == span.idempotency_key


def test_the_fake_switch_answers_from_the_schema_and_calls_no_model(tmp_path: Path) -> None:
    port = FakePort()

    outcome, span = run(tmp_path, port, fake=True)
    with fake_service(tmp_path / "svc") as svc:
        item = svc.drafts.put(None, Bundle.read(ONE_LLM), 0, caller=OPERATOR).item
        report = asyncio.run(svc.tests.run(item, caller=OPERATOR, fake=True))
        state = svc.drafts.state(item)

    assert (report.status, state) == ("passed", "validated")
    assert outcome.status == "passed"
    assert outcome.outputs == {"capital": {"main": {"country": "", "capital": ""}}}
    assert (span.profile, port.chats, port.sent) == ("fake", [], [])
