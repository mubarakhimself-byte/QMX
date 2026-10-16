from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import replace
from typing import Any, cast

import httpx
import pytest
import test_chat
from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, PermissionUpdate
from claude_agent_sdk.types import PermissionRuleValue, ToolPermissionContext
from fastapi import FastAPI
from test_chat import FakeClient, blocks, run

import qma.harness.chat
from qma.harness import (
    AllowAlways,
    AllowOnce,
    Answers,
    AskId,
    Harness,
    NewChat,
    OperatorText,
    QmxHome,
    Reject,
)
from qma.harness.home import read_record, session_id, workspace_key
from qma.harness.launch import Background
from qma.harness.project import PlanMeter, Reading
from qma.harness.routes import chat_router, control_service
from qma.harness.tools import Grants, args_digest

PROPOSE = "mcp__qmx__propose_order"
ORDER = {"symbol": "EURUSD", "side": "buy", "volume": 0.01}
RM_RULE = PermissionRuleValue("Bash", "rm:*")
SUGGEST_RM = [PermissionUpdate("addRules", rules=[RM_RULE], behavior="allow")]

type Ask = Callable[[str, dict[str, Any], ToolPermissionContext], Coroutine[Any, Any, Any]]

home = test_chat.home


async def open_chat(harness: Harness, title: str = "asks") -> tuple[str, Ask]:
    chat = await harness.start_chat(NewChat(title=title, model="haiku"))
    await harness.send(chat, OperatorText("go"))
    ask = FakeClient.made[-1].options.can_use_tool
    assert ask is not None
    return chat, cast("Ask", ask)


async def asked(home: QmxHome, chat: str, count: int = 1) -> list[int]:
    """The seqs of the open asks once `count` of them are written."""
    for _ in range(200):
        seqs = [
            n
            for n, (kind, content) in enumerate(blocks(home, chat), start=1)
            if kind in {"permission", "question"} and content.get("state") == "asking"
        ]
        if len(seqs) >= count:
            return seqs
        await asyncio.sleep(0.01)
    raise AssertionError("no ask was written")


def context(*suggestions: PermissionUpdate) -> ToolPermissionContext:
    return ToolPermissionContext(suggestions=list(suggestions), tool_use_id="t1")


def test_allow_once_resolves_and_a_second_answer_is_already_answered(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat, ask = await open_chat(harness)
        call = asyncio.create_task(ask("Write", {"file_path": "hello.txt"}, context()))
        [n] = await asked(home, chat)
        assert harness.answer(AskId(session_id(chat), n), AllowOnce()) == "resolved"
        assert await call == PermissionResultAllow()
        assert harness.answer(AskId(session_id(chat), n), AllowOnce()) == "already_answered"
        assert harness.answer(AskId(session_id(chat), n), Reject()) == "already_answered"
        assert blocks(home, chat)[-2:] == [
            (
                "permission",
                {"tool": "Write", "input": {"file_path": "hello.txt"}, "state": "asking"},
            ),
            ("permission", {"ask": n, "state": "allowed"}),
        ]

    run(body, home)


def test_reject_denies_with_the_operator_message(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat, ask = await open_chat(harness)
        call = asyncio.create_task(ask("Bash", {"command": "rm hello.txt"}, context()))
        [n] = await asked(home, chat)
        assert harness.answer(AskId(session_id(chat), n), Reject("keep it")) == "resolved"
        assert await call == PermissionResultDeny(message="keep it")
        assert blocks(home, chat)[-1] == ("permission", {"ask": n, "state": "rejected"})

    run(body, home)


def test_allow_always_saves_the_rule_for_the_workspace_and_returns_it_for_the_session(
    home: QmxHome,
) -> None:
    async def body(harness: Harness) -> None:
        chat, ask = await open_chat(harness)
        record = read_record(home, session_id(chat))
        assert record is not None
        call = asyncio.create_task(ask("Bash", {"command": "rm a"}, context(*SUGGEST_RM)))
        [n] = await asked(home, chat)
        assert blocks(home, chat)[-1][1]["always"] == ["Bash(rm:*)"]
        assert harness.answer(AskId(session_id(chat), n), AllowAlways()) == "resolved"
        assert await call == PermissionResultAllow(
            updated_permissions=[
                PermissionUpdate(
                    "addRules", rules=[RM_RULE], behavior="allow", destination="session"
                )
            ]
        )
        remembered = control_service(home).settings_get("claude")["remembered"]
        assert remembered == {workspace_key(record.config.workspace): {"allow": ["Bash(rm:*)"]}}

    run(body, home)


def test_answers_that_do_not_fit_the_ask_are_invalid(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat, ask = await open_chat(harness)
        sid = session_id(chat)
        order = asyncio.create_task(ask(PROPOSE, ORDER, context(*SUGGEST_RM)))
        [n] = await asked(home, chat)
        assert "always" not in blocks(home, chat)[-1][1]
        assert harness.answer(AskId(sid, n), AllowAlways()) == "invalid"
        assert harness.answer(AskId(sid, n), Answers({"q": "a"})) == "invalid"
        bare = asyncio.create_task(ask("Bash", {"command": "rm a"}, context()))
        question = asyncio.create_task(ask("AskUserQuestion", {"questions": []}, context()))
        [_, m, q] = await asked(home, chat, 3)
        assert harness.answer(AskId(sid, m), AllowAlways()) == "invalid"
        assert harness.answer(AskId(sid, q), AllowOnce()) == "invalid"
        for each in (n, m, q):
            assert harness.answer(AskId(sid, each), Reject()) == "resolved"
        await asyncio.gather(order, bare, question)

    run(body, home)


def test_a_question_resolves_with_the_chosen_answers_in_the_input(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat, ask = await open_chat(harness)
        questions = {"questions": [{"question": "Colour?", "options": [{"label": "red"}]}]}
        call = asyncio.create_task(ask("AskUserQuestion", questions, context()))
        [n] = await asked(home, chat)
        assert blocks(home, chat)[-1][0] == "question"
        assert harness.answer(AskId(session_id(chat), n), Answers({"Colour?": "red"})) == "resolved"
        assert await call == PermissionResultAllow(
            updated_input={**questions, "answers": {"Colour?": "red"}}
        )
        assert blocks(home, chat)[-1] == ("question", {"ask": n, "state": "answered"})

    run(body, home)


def test_allow_once_on_an_asking_qmx_tool_grants_its_exact_input_once(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    held: list[Grants] = []
    real = qma.harness.chat.build_server

    def keep(defs: Any, *, grants: Grants, **kwargs: Any) -> Any:
        held.append(grants)
        return real(defs, grants=grants, **kwargs)

    monkeypatch.setattr(qma.harness.chat, "build_server", keep)

    async def body(harness: Harness) -> None:
        chat, ask = await open_chat(harness)
        edited = {**ORDER, "volume": 0.02}
        call = asyncio.create_task(ask(PROPOSE, ORDER, context()))
        [n] = await asked(home, chat)
        assert harness.answer(AskId(session_id(chat), n), AllowOnce(edited)) == "resolved"
        assert await call == PermissionResultAllow(updated_input=edited)

    run(body, home)
    [grants] = held
    assert grants.consume(PROPOSE, args_digest(PROPOSE, ORDER)) is False
    assert grants.consume(PROPOSE, args_digest(PROPOSE, {**ORDER, "volume": 0.02})) is True
    assert grants.consume(PROPOSE, args_digest(PROPOSE, {**ORDER, "volume": 0.02})) is False


def test_asks_expire_when_the_process_ends_and_after_a_restart(home: QmxHome) -> None:
    seen: list[tuple[str, int]] = []

    async def first(harness: Harness) -> None:
        chat, ask = await open_chat(harness)
        call = asyncio.create_task(ask("Write", {"file_path": "a"}, context()))
        [n] = await asked(home, chat)
        seen.append((chat, n))
        await harness.close()
        assert await call == PermissionResultDeny(
            message="the agent process ended before the operator answered"
        )
        assert harness.answer(AskId(session_id(chat), n), AllowOnce()) == "expired"

    async def again(harness: Harness) -> None:
        chat, n = seen[0]
        assert harness.answer(AskId(session_id(chat), n), AllowOnce()) == "expired"

    run(first, home)
    run(again, home)


def test_an_unattended_ask_rejects_after_the_budget(home: QmxHome) -> None:
    control_service(home).settings_put("budgets", {"unattended_ask_seconds": 0.05})

    async def body(harness: Harness) -> None:
        harness._deps.on_plan_limits(PlanMeter((Reading("five_hour", 0.1, None),)))
        chat = await harness.start_chat(NewChat(title="bg", model="haiku", kind=Background()))
        await harness.send(chat, OperatorText("go"))
        ask = FakeClient.made[-1].options.can_use_tool
        assert ask is not None
        verdict = await ask("Bash", {"command": "rm a"}, context())
        assert verdict == PermissionResultDeny(message="the operator did not answer in time")
        n = len(blocks(home, chat)) - 1
        assert blocks(home, chat)[-1] == ("permission", {"ask": n, "state": "expired"})
        assert harness.answer(AskId(chat, n), AllowOnce()) == "expired"

    run(body, home)


def test_the_route_answers_and_names_unknown_ids(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        app = FastAPI()
        app.include_router(chat_router(harness))
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            chat, ask = await open_chat(harness)
            call = asyncio.create_task(ask("Write", {"file_path": "a"}, context()))
            [n] = await asked(home, chat)
            once = {"decision": "allow_once"}
            first = await client.post(f"/api/approvals/{chat}.{n}", json=once)
            second = await client.post(f"/api/approvals/{chat}.{n}", json=once)
            ghost = await client.post(f"/api/approvals/{'0' * 32}.1", json=once)
            junk = await client.post("/api/approvals/nonsense", json=once)
            wrong = await client.post(f"/api/approvals/{chat}.{n}", json={"decision": "maybe"})
            await call
        assert [r.json() for r in (first, second, ghost, junk)] == [
            {"status": "resolved"},
            {"status": "already_answered"},
            {"status": "unknown"},
            {"status": "unknown"},
        ]
        assert wrong.status_code == 422

    run(body, home)


def test_fifty_concurrent_answers_each_resolve_their_own_ask(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat, ask = await open_chat(harness)
        calls = [
            asyncio.create_task(ask("Bash", {"command": f"echo {i}"}, context())) for i in range(50)
        ]
        seqs = await asked(home, chat, 50)

        async def answer(n: int) -> str:
            await asyncio.sleep(0)
            return harness.answer(AskId(session_id(chat), n), AllowOnce())

        statuses = await asyncio.gather(*(answer(n) for n in seqs))
        assert statuses == ["resolved"] * 50
        assert await asyncio.gather(*calls) == [PermissionResultAllow()] * 50

    run(body, home)


def test_an_edited_input_goes_through_the_money_gate_and_the_grant_binds_it(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    held: list[Grants] = []
    real = qma.harness.chat.build_server

    def keep(defs: Any, *, grants: Grants, **kwargs: Any) -> Any:
        held.append(grants)
        return real(defs, grants=grants, **kwargs)

    monkeypatch.setattr(qma.harness.chat, "build_server", keep)
    to_broker = {"command": "curl https://demo.ctraderapi.com:5035"}

    async def body(harness: Harness) -> None:
        chat, ask = await open_chat(harness)
        sid = session_id(chat)
        shell = asyncio.create_task(ask("Bash", {"command": "touch a"}, context()))
        [n] = await asked(home, chat)
        assert harness.answer(AskId(sid, n), AllowOnce(to_broker)) == "resolved"
        assert await shell == PermissionResultDeny(
            message="money rule: agents cannot reach a broker (ctraderapi.com)"
        )
        assert blocks(home, chat)[-1] == ("permission", {"ask": n, "state": "denied"})
        order = asyncio.create_task(ask(PROPOSE, ORDER, context()))
        [_, m] = await asked(home, chat, 2)
        edited = {**ORDER, "volume": 0.05}
        assert harness.answer(AskId(sid, m), AllowOnce(edited)) == "resolved"
        assert await order == PermissionResultAllow(updated_input=edited)

    run(body, home)
    [grants] = held
    assert grants.consume(PROPOSE, args_digest(PROPOSE, ORDER)) is False
    assert grants.consume(PROPOSE, args_digest(PROPOSE, {**ORDER, "volume": 0.05})) is True
