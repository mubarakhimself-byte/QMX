"""Switching profile, model, effort and mode: `classify_change`, `resets_cache`, the quote's
warning, and `apply` with its refusals and its relaunch."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import httpx
import pytest
import qma.harness.chat
import qma.harness.harness
import test_chat
from claude_agent_sdk import Message, TaskStartedMessage
from qmx_control.server import create_app
from test_chat import (
    ROUTER_ROW,
    STOP_RULE_2,
    FakeClient,
    answers,
    blocks,
    no_plan_login,
    rate_limit,
    record_grants,
    run,
    settle,
    turn_of,
)

from qma.harness import (
    ConfigChange,
    Harness,
    LaunchRefused,
    NewChat,
    OperatorText,
    QmxHome,
    QuoteStale,
    SessionId,
)
from qma.harness.chat import context_tokens, warning
from qma.harness.home import read_record
from qma.harness.launch import (
    Background,
    ChatConfig,
    Interactive,
    Step,
    classify_change,
    resets_cache,
)
from qma.harness.profiles import ProfileName
from qma.harness.relay import Relay, RelayGrant
from qma.harness.routes import chat_router, control_service

home = test_chat.home

BASE = ChatConfig(
    profile=ProfileName("claude"),
    model="opus",
    effort="low",
    mode="default",
    workspace=Path("D:/work"),
    kind=Interactive(),
)
KIMI = ProfileName("kimi")
BEARER = {"Authorization": "Bearer route-check"}


@pytest.mark.parametrize(
    ("change", "kind", "steps"),
    [
        ({}, Interactive(), ()),
        ({"mode": "acceptEdits"}, Interactive(), (Step.SET_MODE,)),
        ({"model": "sonnet"}, Interactive(), (Step.SET_MODEL,)),
        ({"effort": "high"}, Interactive(), (Step.SET_EFFORT,)),
        ({"effort": "high"}, Background(), (Step.RELAUNCH,)),
        ({"effort": None}, Interactive(), (Step.RELAUNCH,)),
        ({"mode": "plan", "model": "haiku"}, Interactive(), (Step.SET_MODE, Step.SET_MODEL)),
        (
            {"mode": "plan", "model": "haiku", "effort": "max"},
            Interactive(),
            (Step.SET_MODE, Step.SET_MODEL, Step.SET_EFFORT),
        ),
        ({"profile": KIMI}, Interactive(), (Step.RELAUNCH,)),
        ({"profile": KIMI, "model": "kimi-k3", "mode": "plan"}, Background(), (Step.RELAUNCH,)),
        ({"mode": "plan"}, Background(), (Step.SET_MODE,)),
    ],
)
def test_classify_change(change: dict[str, Any], kind: Any, steps: tuple[Step, ...]) -> None:
    old = replace(BASE, kind=kind)
    assert classify_change(old, replace(old, **change)) == steps


@pytest.mark.parametrize(
    "change", [{"workspace": Path("D:/other")}, {"kind": Background()}]
)
def test_a_workspace_or_kind_change_is_a_new_chat(change: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="new chat"):
        classify_change(BASE, replace(BASE, **change))


@pytest.mark.parametrize(
    ("change", "resets"),
    [
        ({}, False),
        ({"mode": "bypassPermissions"}, False),
        ({"model": "sonnet"}, True),
        ({"model": "opus[1m]"}, True),
        ({"effort": "high"}, True),
        ({"profile": KIMI}, True),
    ],
)
def test_resets_cache(change: dict[str, Any], resets: bool) -> None:
    assert resets_cache(BASE, replace(BASE, **change)) is resets


@pytest.mark.parametrize(
    ("change", "tokens", "tasks", "said"),
    [
        (
            {"profile": KIMI},
            182_400,
            1,
            "Switching to kimi resends ~182k tokens uncached and stops 1 background task.",
        ),
        ({"profile": KIMI}, 0, 2, "Switching to kimi stops 2 background tasks."),
        ({"model": "sonnet"}, 950, 3, "Switching to sonnet resends ~950 tokens uncached."),
        ({"effort": "high"}, 40_000, 0, "Setting effort to high resends ~40k tokens uncached."),
        ({"mode": "plan"}, 182_400, 1, None),
        ({"model": "sonnet"}, 0, 0, None),
    ],
)
def test_the_warning(change: dict[str, Any], tokens: int, tasks: int, said: str | None) -> None:
    new = replace(BASE, **change)
    assert warning(BASE, new, classify_change(BASE, new), tokens, tasks) == said


def reply_line(usage: dict[str, int], *, sidechain: bool = False) -> str:
    entry = {"type": "assistant", "isSidechain": sidechain, "message": {"usage": usage}}
    return json.dumps(entry)


def write_transcript(home: QmxHome, chat: str, *lines: str) -> Path:
    path = home.plan_dir / "projects" / "D--work" / f"{chat}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(['{"type":"user"}', *lines]) + "\n", encoding="utf-8")
    return path


LAST_REPLY = {
    "input_tokens": 3,
    "cache_creation_input_tokens": 2_000,
    "cache_read_input_tokens": 180_000,
    "output_tokens": 400,
}


def test_context_tokens_reads_the_last_main_reply(tmp_path: Path) -> None:
    path = tmp_path / "chat.jsonl"
    path.write_text(
        "\n".join(
            [
                reply_line({"input_tokens": 10, "output_tokens": 5}),
                reply_line(LAST_REPLY),
                "not json",
                reply_line({"input_tokens": 999_999}, sidechain=True),
                '{"type":"user"}',
            ]
        ),
        encoding="utf-8",
    )
    assert context_tokens(path) == 182_403
    assert context_tokens(None) == 0


def key_rows(home: QmxHome, monkeypatch: pytest.MonkeyPatch) -> list[RelayGrant]:
    monkeypatch.setattr(qma.harness.harness, "keyring_secret", lambda _ref: "key")  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    tiers = {"opus": "kimi-k3", "sonnet": "kimi-k3", "haiku": "kimi-k2.6", "fable": "kimi-k3"}
    rows = {"openrouter": ROUTER_ROW, "kimi": {**ROUTER_ROW, "tiers": tiers}}
    control_service(home).settings_put("providers", rows)
    return record_grants(monkeypatch)


async def warm(harness: Harness, home: QmxHome, chat: SessionId, client: int) -> None:
    await harness.send(chat, OperatorText("warm"))
    FakeClient.made[client].go.set()
    await settle(lambda: turn_of(home, chat) == "idle")
    write_transcript(home, chat, reply_line(LAST_REPLY))


def test_a_provider_switch_warns_first_then_resumes_the_same_session_relayed(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    minted = key_rows(home, monkeypatch)

    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="s", model="opus"))
        await warm(harness, home, chat, 0)
        quote = await harness.quote(chat, ConfigChange(profile=ProfileName("openrouter")))
        assert quote.warning == "Switching to openrouter resends ~182k tokens uncached."
        assert quote.steps == (Step.RELAUNCH,)
        assert len(FakeClient.made) == 1
        await harness.apply(chat, quote.id)
        old, new = FakeClient.made
        assert old.disconnected
        assert new.options.resume == chat
        assert new.options.env["CLAUDE_CONFIG_DIR"] == str(home.relayed_dir)
        assert new.options.env["ANTHROPIC_AUTH_TOKEN"] == minted[0].secret
        record = read_record(home, chat)
        assert record is not None
        assert record.config.profile == "openrouter"
        assert harness._chat(chat).is_live  # pyright: ignore[reportPrivateUsage]
        assert blocks(home, chat)[-1] == (
            "changed",
            {
                "kind": "config",
                "steps": ["relaunch"],
                "from": {"profile": "claude", "model": "opus", "effort": None, "mode": "default"},
                "to": {
                    "profile": "openrouter",
                    "model": "opus",
                    "effort": None,
                    "mode": "default",
                },
            },
        )
        with pytest.raises(QuoteStale, match="no such quote"):
            await harness.apply(chat, quote.id)

    run(body, home)


def test_a_relaunch_revokes_the_old_grant_before_the_new_cli_starts(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    minted = key_rows(home, monkeypatch)
    order: list[str] = []
    revoke, connect = Relay.revoke, FakeClient.connect

    async def logged_revoke(relay: Relay, grant: RelayGrant) -> None:
        order.append(f"revoke {minted.index(grant)}")
        await revoke(relay, grant)

    async def logged_connect(client: FakeClient) -> None:
        order.append(f"connect {FakeClient.made.index(client)}")
        await connect(client)

    monkeypatch.setattr(Relay, "revoke", logged_revoke)
    monkeypatch.setattr(FakeClient, "connect", logged_connect)
    monkeypatch.setattr(qma.harness.chat, "plan_auth_method", no_plan_login)

    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="k", model="opus", profile="openrouter"))
        await warm(harness, home, chat, 0)
        quote = await harness.quote(chat, ConfigChange(profile=KIMI, model="kimi-k3[1m]"))
        await harness.apply(chat, quote.id)
        assert order == ["connect 0", "revoke 0", "connect 1"]
        assert [await answers(grant) for grant in minted] == [401, 404]
        assert minted[1].profile.name == "kimi"

    run(body, home)


def test_a_model_change_within_the_plan_uses_set_model_and_warns(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="m", model="opus"))
        await warm(harness, home, chat, 0)
        quote = await harness.quote(chat, ConfigChange(model="sonnet"))
        assert (quote.steps, quote.warning) == (
            (Step.SET_MODEL,),
            "Switching to sonnet resends ~182k tokens uncached.",
        )
        await harness.apply(chat, quote.id)
        assert len(FakeClient.made) == 1
        assert FakeClient.made[0].set == [("model", "sonnet")]

    run(body, home)


def test_a_mode_change_has_no_warning_and_applies_at_once_even_mid_turn(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="m", model="opus"))
        await warm(harness, home, chat, 0)
        FakeClient.made[0].go.clear()
        await harness.send(chat, OperatorText("long job"))
        quote = await harness.quote(chat, ConfigChange(mode="acceptEdits"))
        assert (quote.steps, quote.warning) == ((Step.SET_MODE,), None)
        await harness.apply(chat, quote.id)
        assert FakeClient.made[0].set == [("mode", "acceptEdits")]
        assert turn_of(home, chat) == "running"

    run(body, home)


def test_an_effort_change_sends_slash_effort_without_a_relaunch(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="e", model="sonnet", effort="low"))
        await warm(harness, home, chat, 0)
        quote = await harness.quote(chat, ConfigChange(effort="high"))
        assert quote.steps == (Step.SET_EFFORT,)
        await harness.apply(chat, quote.id)
        assert FakeClient.made[0].queries == ["warm", "/effort high"]
        assert len(FakeClient.made) == 1
        assert turn_of(home, chat) == "idle"
        record = read_record(home, chat)
        assert record is not None
        assert record.config.effort == "high"

    run(body, home)


def test_a_quote_goes_stale_after_another_prompt(home: QmxHome) -> None:
    statuses: list[tuple[int, str]] = []

    async def body(harness: Harness) -> None:
        app = create_app(control_service(home), "route-check", extra_routers=[chat_router(harness)])
        chat = await harness.start_chat(NewChat(title="s34", model="opus"))
        await warm(harness, home, chat, 0)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://t", headers=BEARER
        ) as client:
            quoted = await client.post(f"/api/sessions/{chat}/quote", json={"model": "sonnet"})
            assert quoted.json()["warning"] == "Switching to sonnet resends ~182k tokens uncached."
            await client.post(f"/api/sessions/{chat}/turns", json={"text": "another"})
            await settle(lambda: turn_of(home, chat) == "idle")
            for quote_id in (quoted.json()["id"], "forged"):
                applied = await client.post(
                    f"/api/sessions/{chat}/apply", json={"quote_id": quote_id}
                )
                statuses.append((applied.status_code, applied.json()["error"]["code"]))
        assert FakeClient.made[0].set == []

    run(body, home)
    assert statuses == [(409, "quote_stale"), (409, "quote_stale")]


def background_task(task: str) -> Message:
    return TaskStartedMessage(
        subtype="task_started",
        data={},
        task_id=task,
        description="sleep 300",
        uuid="u",
        session_id="s",
    )


def test_more_background_tasks_than_quoted_refuse_then_a_new_quote_relaunches(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_rows(home, monkeypatch)

    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="s40", model="opus"))
        await warm(harness, home, chat, 0)
        inbox = FakeClient.made[0].inbox
        inbox.put_nowait(background_task("bg1"))
        live = harness._chat(chat)  # pyright: ignore[reportPrivateUsage]
        await settle(lambda: live.idle_seconds == 0)
        change = ConfigChange(profile=ProfileName("openrouter"))
        first = await harness.quote(chat, change)
        assert first.warning == (
            "Switching to openrouter resends ~182k tokens uncached and stops 1 background task."
        )
        inbox.put_nowait(background_task("bg2"))
        await asyncio.sleep(0.05)
        with pytest.raises(QuoteStale, match="2 background tasks run now and the quote named 1"):
            await harness.apply(chat, first.id)
        assert len(FakeClient.made) == 1
        second = await harness.quote(chat, change)
        assert second.background_tasks == 2
        await harness.apply(chat, second.id)
        assert len(FakeClient.made) == 2
        assert FakeClient.made[0].disconnected

    run(body, home)


def test_a_relaunch_waits_for_the_turn_to_end(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_rows(home, monkeypatch)

    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="r", model="opus"))
        await harness.send(chat, OperatorText("long job"))
        quote = await harness.quote(chat, ConfigChange(profile=ProfileName("openrouter")))
        with pytest.raises(QuoteStale, match="a turn is running"):
            await harness.apply(chat, quote.id)
        assert not FakeClient.made[0].disconnected

    run(body, home)


def test_a_model_outside_the_tier_set_gets_no_quote(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_rows(home, monkeypatch)

    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="s41", model="opus"))
        for model in ("kimi-k2.7-code", "claude-opus-5"):
            with pytest.raises(LaunchRefused, match="kimi cannot run the model"):
                await harness.quote(chat, ConfigChange(profile=KIMI, model=model))
        alias = await harness.quote(chat, ConfigChange(profile=KIMI, model="haiku"))
        suffixed = await harness.quote(chat, ConfigChange(profile=KIMI, model="kimi-k3[1m]"))
        assert (alias.new.model, suffixed.new.model) == ("haiku", "kimi-k3[1m]")
        with pytest.raises(LaunchRefused, match="no provider is named 'nope'"):
            await harness.quote(chat, ConfigChange(profile=ProfileName("nope")))
        assert FakeClient.made == []

    run(body, home)


def test_a_cold_chat_records_the_change_and_its_next_send_launches_with_it(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_rows(home, monkeypatch)
    monkeypatch.setattr(qma.harness.chat, "plan_auth_method", no_plan_login)

    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="c", model="opus"))
        quote = await harness.quote(chat, ConfigChange(profile=ProfileName("openrouter")))
        assert quote.warning is None
        await harness.apply(chat, quote.id)
        assert FakeClient.made == []
        await harness.send(chat, OperatorText("hi"))
        assert FakeClient.made[0].options.env["CLAUDE_CONFIG_DIR"] == str(home.relayed_dir)

    run(body, home)


def test_a_switch_onto_the_plan_is_refused_while_the_overage_stop_holds(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_rows(home, monkeypatch)

    async def body(harness: Harness) -> None:
        plan = await harness.start_chat(NewChat(title="p", model="opus"))
        await warm(harness, home, plan, 0)
        keyed = await harness.start_chat(NewChat(title="k", model="opus", profile="openrouter"))
        await warm(harness, home, keyed, 1)
        early = await harness.quote(keyed, ConfigChange(profile=ProfileName("claude")))
        FakeClient.made[0].inbox.put_nowait(
            rate_limit(status="rejected", rateLimitType="five_hour", overageStatus="allowed")
        )
        await settle(lambda: ("needs_you", {"reason": STOP_RULE_2}) in blocks(home, plan))
        stopped = "plan use is stopped: rule 2"
        with pytest.raises(LaunchRefused, match=stopped):
            await harness.quote(keyed, ConfigChange(profile=ProfileName("claude")))
        with pytest.raises(LaunchRefused, match=stopped):
            await harness.apply(keyed, early.id)
        record = read_record(home, keyed)
        assert record is not None
        assert record.config.profile == "openrouter"
        assert not FakeClient.made[1].disconnected
        within = await harness.quote(keyed, ConfigChange(model="sonnet"))
        await harness.apply(keyed, within.id)
        assert FakeClient.made[1].set == [("model", "sonnet")]

    run(body, home)


def test_a_background_chat_keeps_its_limits_across_a_relaunch(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_rows(home, monkeypatch)
    monkeypatch.setattr(qma.harness.chat, "plan_auth_method", no_plan_login)

    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(
            NewChat(title="b", model="opus", profile="openrouter", kind=Background())
        )
        await warm(harness, home, chat, 0)
        quote = await harness.quote(chat, ConfigChange(effort="high", profile=KIMI))
        await harness.apply(chat, quote.id)
        before, after = (made.options for made in FakeClient.made)
        limits = [
            (o.verbatim_prompts, o.max_turns, o.max_budget_usd, o.effort) for o in (before, after)
        ]
        assert limits == [(True, 50, 5.0, None), (True, 50, 5.0, "high")]

    run(body, home)

