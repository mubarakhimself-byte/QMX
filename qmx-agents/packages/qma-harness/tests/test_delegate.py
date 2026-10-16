"""`mcp__qmx__delegate`: the allow-list, the full table, `unattended` inheritance, the child's
launch, and the gate's sub-agent rule."""

from __future__ import annotations

import asyncio
from typing import Any

import anyio
import pytest
import test_chat
from claude_agent_sdk import Message
from test_chat import STOP_RULE_2, FakeClient, blocks, rate_limit, result, run, settle, turn_of
from test_money import RULES
from test_table import read_plan

import qma.harness.chat
from qma.harness import Harness, InjectedText, NewChat, OperatorText, QmxHome, SessionId
from qma.harness.home import read_record
from qma.harness.procs import AgentProcessCap
from qma.harness.launch import Background, ChatKind, Child, Interactive
from qma.harness.money import Deny, Pass, gate
from qma.harness.profiles import ProfileName, parse_profiles
from qma.harness.routes import control_service
from qma.harness.tools import Effect, ToolDef

home = test_chat.home

KEY_ROW = {
    "base_url": "https://openrouter.ai/api",
    "credential_ref": "qmx/openrouter",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "moonshotai/kimi-k2.5"),
}


@pytest.fixture
def defs(monkeypatch: pytest.MonkeyPatch) -> list[list[ToolDef]]:
    """The QMX tool list of every launch, in launch order."""
    held: list[list[ToolDef]] = []
    real = qma.harness.chat.build_server

    def keep(found: list[ToolDef], **kwargs: Any) -> Any:
        held.append(found)
        return real(found, **kwargs)

    monkeypatch.setattr(qma.harness.chat, "build_server", keep)
    return held


def settings(home: QmxHome, *, targets: list[str], **budgets: object) -> None:
    control = control_service(home)
    control.settings_put("providers", {"kimi": KEY_ROW, "delegate_targets": targets})
    control.settings_put("budgets", dict(budgets))


def delegate_of(found: list[ToolDef]) -> ToolDef:
    [tool] = [tool for tool in found if tool.name == "delegate"]
    return tool


def helper_says(text: str) -> None:
    """The parent's turn stays open; a helper's prompt gets `text` as its final result."""

    def script(prompt: str) -> list[Message | None]:
        return [result(result=text)] if prompt.startswith("help:") else []

    FakeClient.script = script


async def open_parent(harness: Harness, kind: ChatKind | None = None) -> SessionId:
    """A plan parent whose turn is running, as it is while it calls a tool."""
    parent = await harness.start_chat(
        NewChat(title="parent", model="haiku", kind=kind or Interactive())
    )
    first = OperatorText("go") if kind is None else InjectedText("go")
    await harness.send(parent, first)
    FakeClient.made[-1].go.set()
    return parent


async def call(found: list[ToolDef], profile: str, prompt: str = "help: count") -> dict[str, Any]:
    """Run the parent's delegate tool, releasing each helper's fake CLI as it launches."""
    made = len(FakeClient.made)
    task = asyncio.create_task(delegate_of(found).call({"profile": profile, "prompt": prompt}))
    while not task.done():
        for client in FakeClient.made[made:]:
            client.go.set()
        await asyncio.sleep(0.01)
    return task.result()


def test_delegate_targets_parse_from_the_providers_section() -> None:
    profiles = parse_profiles({"kimi": KEY_ROW, "delegate_targets": ["kimi", "claude"]})
    assert profiles.delegate_targets == frozenset({ProfileName("kimi"), ProfileName("claude")})
    assert sorted(profiles.by_name) == ["claude", "kimi"]
    assert profiles.delegate_refusal("kimi") is None
    assert parse_profiles({"kimi": KEY_ROW}).delegate_targets == frozenset()
    assert parse_profiles({"delegate_targets": "kimi"}).errors == {
        "delegate_targets": "[providers] delegate_targets must be a list of names"
    }


def test_a_profile_outside_the_allow_list_is_refused_before_any_child(
    home: QmxHome, defs: list[list[ToolDef]]
) -> None:
    settings(home, targets=["claude"])

    async def body(harness: Harness) -> None:
        await open_parent(harness)
        assert await call(defs[0], "kimi") == {
            "content": [
                {
                    "type": "text",
                    "text": "'kimi' is not in the delegate allow-list, [providers] "
                    "delegate_targets, which lists claude",
                }
            ],
            "is_error": True,
        }
        assert len(FakeClient.made) == 1
        assert len(control_service(home).sessions_list()) == 1

    run(body, home)


def test_a_full_table_refuses_at_once_with_a_tool_error(
    home: QmxHome, defs: list[list[ToolDef]]
) -> None:
    settings(home, targets=["claude"], max_live_chats=1)

    async def body(harness: Harness) -> None:
        parent = await open_parent(harness)
        FakeClient.script = lambda _: []
        reply = await asyncio.wait_for(call(defs[0], "claude"), 2)
        [text] = reply["content"]
        assert reply["is_error"] is True
        assert text["text"] == (
            f"the helper did not start: all 1 live chats are busy ({parent}); interrupt or "
            "close one, or raise [budgets] max_live_chats"
        )
        assert len(FakeClient.made) == 1

    run(body, home)


@pytest.mark.parametrize(
    ("kind", "unattended"), [(None, False), (Background(), True)], ids=["interactive", "background"]
)
def test_the_child_copies_unattended_and_launches_verbatim_bounded_and_without_agents(
    home: QmxHome, defs: list[list[ToolDef]], kind: ChatKind | None, unattended: bool
) -> None:
    settings(home, targets=["claude"], max_turns=7, max_budget_usd=0.25)
    helper_says("the folder holds 3 files")

    async def body(harness: Harness) -> None:
        read_plan(harness, 0.1)
        parent = await open_parent(harness, kind)
        assert await call(defs[0], "claude") == {
            "content": [{"type": "text", "text": "the folder holds 3 files"}]
        }
        [child] = [
            row["id"]
            for row in control_service(home).sessions_list()
            if row.get("parent_id") == parent
        ]
        record = read_record(home, SessionId(str(child)))
        assert record is not None
        assert record.config.kind == Child(parent, unattended=unattended)
        assert (record.config.profile, record.config.model) == ("claude", "haiku")
        options = FakeClient.made[1].options
        assert FakeClient.made[1].queries == ["help: count"]
        assert (options.verbatim_prompts, options.max_turns, options.max_budget_usd) == (
            True,
            7,
            0.25,
        )
        assert options.disallowed_tools[:2] == ["Agent", "Task"]
        assert FakeClient.made[1].disconnected is True
        assert not harness._chat(SessionId(str(child))).is_live  # pyright: ignore[reportPrivateUsage]

    run(body, home)
    parent_tools, child_tools = defs
    assert delegate_of(parent_tools).effect is Effect.DOMAIN_WRITE
    assert [tool.name for tool in child_tools if tool.name == "delegate"] == []


def test_a_plan_child_is_refused_while_the_overage_stop_holds(
    home: QmxHome, defs: list[list[ToolDef]]
) -> None:
    settings(home, targets=["claude"])

    async def body(harness: Harness) -> None:
        parent = await open_parent(harness)
        FakeClient.made[0].inbox.put_nowait(
            rate_limit(status="rejected", rateLimitType="five_hour", overageStatus="allowed")
        )
        await settle(lambda: ("needs_you", {"reason": STOP_RULE_2}) in blocks(home, parent))
        assert await call(defs[0], "claude") == {
            "content": [
                {
                    "type": "text",
                    "text": "the helper did not start: plan use is stopped: rule 2: the "
                    "five_hour window is used up and paid extra usage is allowed, so the next "
                    "request could bill",
                }
            ],
            "is_error": True,
        }
        assert len(FakeClient.made) == 1
        assert turn_of(home, parent) == "idle"

    run(body, home)


def test_a_child_whose_process_ends_mid_turn_is_a_tool_error(
    home: QmxHome, defs: list[list[ToolDef]]
) -> None:
    settings(home, targets=["claude"])
    FakeClient.script = lambda prompt: [None] if prompt.startswith("help:") else []

    async def body(harness: Harness) -> None:
        await open_parent(harness)
        assert await call(defs[0], "claude") == {
            "content": [{"type": "text", "text": "the helper's process ended before it answered"}],
            "is_error": True,
        }

    run(body, home)


def test_a_delegate_cancelled_mid_turn_still_stops_the_child_process(
    home: QmxHome, defs: list[list[ToolDef]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The SDK cancels an interrupted tool call through an anyio cancel scope, which cancels
    every await again, including the CLI disconnect in the child's teardown."""
    settings(home, targets=["claude"])
    FakeClient.script = lambda _: []
    stopped: list[str] = []
    real = AgentProcessCap.stop_chat

    def stop_chat(self: AgentProcessCap, chat: str) -> None:
        stopped.append(chat)
        real(self, chat)

    monkeypatch.setattr(AgentProcessCap, "stop_chat", stop_chat)
    disconnect = FakeClient.disconnect

    async def slow_disconnect(self: FakeClient) -> None:
        await asyncio.sleep(0.05)
        await disconnect(self)

    monkeypatch.setattr(FakeClient, "disconnect", slow_disconnect)

    async def body(harness: Harness) -> None:
        parent = await open_parent(harness)
        scope = anyio.CancelScope()

        async def interrupted() -> None:
            with scope:
                await delegate_of(defs[0]).call({"profile": "claude", "prompt": "help: wait"})

        task = asyncio.create_task(interrupted())
        while len(FakeClient.made) < 2:
            await asyncio.sleep(0.01)
        scope.cancel()
        await task
        assert scope.cancelled_caught is True
        [child] = [
            SessionId(str(row["id"]))
            for row in control_service(home).sessions_list()
            if row.get("parent_id") == parent
        ]
        await settle(lambda: child in stopped)
        assert stopped == [child]
        assert FakeClient.made[1].disconnected is True
        assert not harness._chat(child).is_live  # pyright: ignore[reportPrivateUsage]

    run(body, home)


@pytest.mark.parametrize(
    ("tool", "agent_id", "verdict"),
    [
        (
            "mcp__qmx__delegate",
            "a1b2",
            Deny("money rule: a sub-agent cannot start a helper chat (mcp__qmx__delegate)"),
        ),
        (
            "mcp__QMX__Delegate",
            "a1b2",
            Deny("money rule: a sub-agent cannot start a helper chat (mcp__qmx__delegate)"),
        ),
        ("mcp__qmx__delegate", None, Pass()),
        ("mcp__qmx__delegate", "", Pass()),
        ("mcp__qmx__library_search", "a1b2", Pass()),
    ],
)
def test_the_gate_denies_delegate_only_inside_a_sub_agent(
    tool: str, agent_id: str | None, verdict: Deny | Pass
) -> None:
    found = gate(
        tool,
        {"profile": "kimi", "prompt": "x"},
        RULES,
        cwd="/d/w",
        agent_id=agent_id,
        permission_mode="default",
    )
    assert found == verdict
