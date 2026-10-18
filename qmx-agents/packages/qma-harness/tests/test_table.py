"""The live-chat table: budgets, prompt kinds, eviction, `ChatTableFull`, reaping, the
background cap and the overage stop on a Background chat."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest
import test_chat
from claude_agent_sdk import Message, TaskNotificationMessage, TaskStartedMessage
from pydantic import JsonValue
from qmx_control.server import create_app
from test_chat import STOP_RULE_2, FakeClient, blocks, rate_limit, result, run, settle, turn_of

from qma.harness import (
    ChatTableFull,
    Harness,
    InjectedText,
    LaunchRefused,
    NewChat,
    OperatorText,
    QmxHome,
    SessionId,
    UntrustedPrompt,
)
from qma.harness.chat import Prompt, admits
from qma.harness.launch import Background, Budgets, ChatKind, Child, Interactive, parse_budgets
from qma.harness.project import PlanMeter, Reading
from qma.harness.routes import chat_router, control_service

home = test_chat.home

CHILD = SessionId("0" * 32)
NO_READING = (
    "the background cap holds this chat: there is no reading of the plan's five-hour window "
    "yet; POST /api/usage/meter reads it with one haiku plan turn"
)


def budgets(home: QmxHome, **values: JsonValue) -> None:
    control_service(home).settings_put("budgets", dict(values))


def read_plan(harness: Harness, used: float) -> None:
    harness._deps.on_plan_limits(PlanMeter((Reading("five_hour", used, None),)))  # pyright: ignore[reportPrivateUsage]


async def chat(harness: Harness, title: str, kind: ChatKind | None = None) -> SessionId:
    return await harness.start_chat(NewChat(title=title, model="haiku", kind=kind or Interactive()))


async def finished(harness: Harness, home: QmxHome, sid: SessionId, text: str = "hi") -> None:
    """Send, let the fake CLI answer, and wait for the turn to end."""
    await harness.send(sid, OperatorText(text))
    FakeClient.made[-1].go.set()
    await settle(lambda: turn_of(home, sid) == "idle")


def live(harness: Harness) -> list[SessionId]:
    return sorted(sid for sid, found in harness._chats.items() if found.is_live)  # pyright: ignore[reportPrivateUsage]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({}, Budgets(4, 900.0, 300.0, 0.5, 50, 5.0)),
        (
            {
                "max_live_chats": 2,
                "idle_reap_seconds": 30,
                "unattended_ask_seconds": 0.5,
                "background_cap": 0.3,
                "max_turns": 7,
                "max_budget_usd": 0.25,
            },
            Budgets(2, 30.0, 0.5, 0.3, 7, 0.25),
        ),
        (
            {
                "max_live_chats": 2.5,
                "idle_reap_seconds": "soon",
                "unattended_ask_seconds": True,
                "background_cap": 1.5,
                "max_turns": 0,
                "max_budget_usd": float("inf"),
            },
            Budgets(4, 900.0, 300.0, 0.5, 50, 5.0),
        ),
        ({"unattended_ask_seconds": -5, "background_cap": float("nan")}, Budgets()),
        ({"background_cap": 1}, Budgets(background_cap=1.0)),
    ],
)
def test_budgets_parse_and_fall_back_per_value(raw: dict[str, object], expected: Budgets) -> None:
    assert parse_budgets(raw) == expected


@pytest.mark.parametrize(
    ("kind", "prompt", "admitted"),
    [
        (Interactive(), OperatorText("/compact"), True),
        (Interactive(), InjectedText("/compact"), False),
        (Background(), OperatorText("/compact"), True),
        (Background(), InjectedText("/compact"), True),
        (Child(CHILD, unattended=False), InjectedText("@x"), True),
        (Child(CHILD, unattended=True), InjectedText("@x"), True),
        (Child(CHILD, unattended=True), OperatorText("@x"), True),
    ],
)
def test_the_prompt_kind_table(kind: ChatKind, prompt: Prompt, admitted: bool) -> None:
    assert admits(kind, prompt) is admitted


def test_injected_text_into_an_interactive_chat_is_refused_before_any_launch(
    home: QmxHome,
) -> None:
    async def body(harness: Harness) -> None:
        sid = await chat(harness, "operator")
        with pytest.raises(UntrustedPrompt):
            await harness.send(sid, InjectedText("/compact and @~/.qmx/settings.toml"))
        assert FakeClient.made == []
        assert blocks(home, sid) == []

    run(body, home)


def test_only_background_and_child_chats_launch_verbatim_and_bounded(home: QmxHome) -> None:
    budgets(home, max_turns=7, max_budget_usd=0.25)

    async def body(harness: Harness) -> None:
        read_plan(harness, 0.1)
        operator = await chat(harness, "operator")
        await finished(harness, home, operator)
        await harness.send(await chat(harness, "news", Background()), InjectedText("news"))
        child = await chat(harness, "helper", Child(operator, unattended=True))
        await harness.send(child, InjectedText("review"))

    run(body, home)
    seen = [
        (made.options.verbatim_prompts, made.options.max_turns, made.options.max_budget_usd)
        for made in FakeClient.made
    ]
    assert seen == [(False, None, None), (True, 7, 0.25), (True, 7, 0.25)]


def test_the_least_recently_used_idle_chat_is_evicted_first(home: QmxHome) -> None:
    budgets(home, max_live_chats=2)
    order: list[list[SessionId]] = []

    async def body(harness: Harness) -> None:
        first, second, third = [await chat(harness, name) for name in ("a", "b", "c")]
        await finished(harness, home, first)
        test_chat.plant_transcript(home, first)
        await finished(harness, home, second)
        await finished(harness, home, third)
        order.append(live(harness))
        await finished(harness, home, first, "again")
        order.append(live(harness))
        assert [made.disconnected for made in FakeClient.made] == [True, True, False, False]
        assert FakeClient.made[3].options.resume == first
        assert order == [sorted([second, third]), sorted([third, first])]

    run(body, home)


def test_a_full_table_of_busy_chats_refuses_and_names_them(home: QmxHome) -> None:
    budgets(home, max_live_chats=2)

    async def body(harness: Harness) -> None:
        first, second, third = [await chat(harness, name) for name in ("a", "b", "c")]
        await harness.send(first, OperatorText("long"))
        await harness.send(second, OperatorText("long"))
        with pytest.raises(ChatTableFull) as refused:
            await harness.send(third, OperatorText("one more"))
        busy = sorted([first, second])
        reason = (
            f"all 2 live chats are busy ({', '.join(busy)}); interrupt or close one, "
            "or raise [budgets] max_live_chats"
        )
        assert (refused.value.busy, str(refused.value)) == (tuple(busy), reason)
        assert blocks(home, third) == [("needs_you", {"reason": reason, "busy": busy})]
        assert len(FakeClient.made) == 2
        await harness.send(first, OperatorText("queued into the running turn"))
        assert len(FakeClient.made) == 2

    run(body, home)


def test_the_turn_route_answers_a_full_table_with_409(home: QmxHome) -> None:
    budgets(home, max_live_chats=1)
    answers: list[tuple[int, Any]] = []

    async def body(harness: Harness) -> None:
        app = create_app(control_service(home), "test-token", extra_routers=[chat_router(harness)])
        transport = httpx.ASGITransport(app=app)
        first, second = await chat(harness, "a"), await chat(harness, "b")
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            for sid in (first, second):
                sent = await client.post(
                    f"/api/sessions/{sid}/turns",
                    json={"text": "go"},
                    headers={"Authorization": "Bearer test-token"},
                )
                answers.append((sent.status_code, sent.json()))

    run(body, home)
    assert [status for status, _ in answers] == [202, 409]
    assert answers[1][1]["error"]["code"] == "chat_table_full"


def background_bash(text: str) -> list[Message]:
    started = TaskStartedMessage(
        subtype="task_started",
        data={},
        task_id="bash1",
        description="sleep 600",
        uuid="u",
        session_id="s",
        task_type="local_bash",
    )
    return [started, result()]


def bash_done() -> TaskNotificationMessage:
    return TaskNotificationMessage(
        subtype="task_notification",
        data={},
        task_id="bash1",
        status="completed",
        output_file="",
        summary="done",
        uuid="u",
        session_id="s",
    )


def test_idle_seconds_stay_zero_while_a_background_task_runs(home: QmxHome) -> None:
    budgets(home, max_live_chats=1)
    FakeClient.script = background_bash

    async def body(harness: Harness) -> None:
        worker, other = await chat(harness, "worker"), await chat(harness, "other")
        await finished(harness, home, worker, "start the job")
        await asyncio.sleep(0.05)
        found = harness._chat(worker)  # pyright: ignore[reportPrivateUsage]
        assert found.idle_seconds == 0.0
        with pytest.raises(ChatTableFull):
            await harness.send(other, OperatorText("hi"))
        FakeClient.made[0].inbox.put_nowait(bash_done())
        await settle(lambda: found.idle_seconds > 0)
        assert found.idle_seconds > 0
        await harness.send(other, OperatorText("hi"))
        assert live(harness) == [other]

    run(body, home)


def test_reaping_closes_idle_chats_and_spares_one_with_a_background_task(
    home: QmxHome,
) -> None:
    budgets(home, idle_reap_seconds=0.2)

    async def body(harness: Harness) -> None:
        idle, working = await chat(harness, "idle"), await chat(harness, "working")
        await finished(harness, home, idle)
        test_chat.plant_transcript(home, idle)
        FakeClient.script = background_bash
        await finished(harness, home, working, "start the job")
        await settle(lambda: live(harness) == [working])
        await asyncio.sleep(0.5)
        assert live(harness) == [working]
        assert [made.disconnected for made in FakeClient.made] == [True, False]
        FakeClient.script = test_chat.replies
        await finished(harness, home, idle, "back")
        assert FakeClient.made[2].options.resume == idle

    run(body, home)


def test_a_background_plan_send_fails_closed_without_a_reading(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        news = await chat(harness, "news", Background())
        with pytest.raises(LaunchRefused) as refused:
            await harness.send(news, InjectedText("headlines"))
        assert str(refused.value) == NO_READING
        assert blocks(home, news) == [("needs_you", {"reason": NO_READING})]
        assert FakeClient.made == []
        await finished(harness, home, await chat(harness, "operator"))

    run(body, home)


def test_a_background_plan_send_is_refused_at_the_cap(home: QmxHome) -> None:
    budgets(home, background_cap=0.3)

    async def body(harness: Harness) -> None:
        read_plan(harness, 0.4)
        news = await chat(harness, "news", Background())
        with pytest.raises(LaunchRefused) as refused:
            await harness.send(news, InjectedText("headlines"))
        assert str(refused.value) == (
            "the background cap holds this chat: the five-hour window is 40% used, at or over "
            "the 30% cap"
        )
        read_plan(harness, 0.1)
        await harness.send(news, InjectedText("headlines"))
        assert len(FakeClient.made) == 1

    run(body, home)


def test_a_refused_overage_window_does_not_hold_the_background_cap(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        read_plan(harness, 0.1)
        news = await chat(harness, "news", Background())
        FakeClient.script = lambda _: [
            rate_limit(status="rejected", rateLimitType="overage", overageStatus="rejected"),
            result(),
        ]
        await finished(harness, home, await chat(harness, "operator"))
        await harness.send(news, InjectedText("headlines"))
        assert len(FakeClient.made) == 2

    run(body, home)


def test_the_overage_stop_ends_a_running_background_chat(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        read_plan(harness, 0.1)
        news = await chat(harness, "news", Background())
        await harness.send(news, InjectedText("headlines"))
        FakeClient.made[0].inbox.put_nowait(
            rate_limit(status="rejected", rateLimitType="five_hour", overageStatus="allowed")
        )
        await settle(lambda: ("needs_you", {"reason": STOP_RULE_2}) in blocks(home, news))
        assert FakeClient.made[0].disconnected is True
        assert turn_of(home, news) == "idle"
        assert live(harness) == []

    run(body, home)


async def release_next_client() -> None:
    made = len(FakeClient.made)
    await settle(lambda: len(FakeClient.made) > made)
    FakeClient.made[-1].go.set()


def test_the_meter_runs_one_bare_haiku_turn_on_a_cold_ledger(home: QmxHome) -> None:
    FakeClient.script = lambda _: [
        rate_limit(status="allowed", rateLimitType="five_hour", utilization=0.2),
        result(),
    ]

    async def body(harness: Harness) -> None:
        release = asyncio.create_task(release_next_client())
        reading = await harness.meter()
        await release
        assert reading is not None
        assert reading.reading.utilization == 0.2
        (made,) = FakeClient.made
        assert (made.queries, made.options.model) == (["Reply with the single word OK."], "haiku")
        assert (made.options.tools, made.options.mcp_servers) == ([], {})
        assert list(home.chats_dir.glob("*.json")) == []
        assert list(home.workspaces_dir.iterdir()) == []
        FakeClient.script = test_chat.replies
        await harness.send(await chat(harness, "news", Background()), InjectedText("headlines"))
        assert len(FakeClient.made) == 2

    run(body, home)


def test_the_meter_runs_no_turn_while_a_reading_is_live(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        read_plan(harness, 0.1)
        reading = await harness.meter()
        assert reading is not None
        assert reading.reading.utilization == 0.1
        assert FakeClient.made == []

    run(body, home)


def test_the_meter_refuses_without_a_turn_while_a_plan_window_is_used_up(
    home: QmxHome,
) -> None:
    async def body(harness: Harness) -> None:
        FakeClient.script = lambda _: [
            rate_limit(status="rejected", rateLimitType="five_hour", overageStatus="rejected"),
            result(),
        ]
        await finished(harness, home, await chat(harness, "operator"))
        with pytest.raises(LaunchRefused) as refused:
            await harness.meter()
        assert str(refused.value) == "the plan meter will not run: a plan window is used up"
        with pytest.raises(LaunchRefused):
            await harness.send(await chat(harness, "news", Background()), InjectedText("x"))
        assert len(FakeClient.made) == 1

    run(body, home)
