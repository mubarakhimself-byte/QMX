"""`delegate` v2: the handle at once, the report between turns, steer and stop, and a helper
never wider than its parent (AD-41, AD-62)."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import pytest
import test_chat
from claude_agent_sdk import Message
from pydantic import JsonValue
from test_chat import FakeClient, result, run, settle, turn_of
from test_table import read_plan

import qma.harness.chat
import qma.harness.harness
from qma.harness import Harness, InjectedText, NewChat, OperatorText, QmxHome, SessionId
from qma.harness.guard import Deny, Pass, guard
from qma.harness.home import read_record
from qma.harness.launch import Background, Child, Interactive
from qma.harness.routes import control_service
from qma.harness.tools import Effect, ToolDef, failure

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
    real = qma.harness.chat.build_servers

    def keep(found: list[ToolDef], **kwargs: Any) -> Any:
        held.append(found)
        return real(found, **kwargs)

    monkeypatch.setattr(qma.harness.chat, "build_servers", keep)
    return held


@pytest.fixture
def keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """A keyring read answers, so a key profile's grant needs no real credential."""
    monkeypatch.setattr(qma.harness.harness, "keyring_secret", lambda _: "test-value")


def settings(home: QmxHome, *, targets: list[str], **written: JsonValue) -> None:
    control = control_service(home)
    control.settings_put(
        "providers",
        {"kimi": KEY_ROW, "delegate_targets": targets},  # pyright: ignore[reportArgumentType]
    )
    control.settings_put("budgets", dict(written))


def tool_of(found: list[ToolDef], name: str) -> ToolDef:
    [tool] = [tool for tool in found if tool.name == name]
    return tool


def answer(reply: dict[str, Any]) -> Any:
    return json.loads(reply["content"][0]["text"])


async def call(
    found: list[ToolDef], name: str, arguments: dict[str, Any], *, release: bool = True
) -> dict[str, Any]:
    """Run one `delegate` tool now, releasing each fake CLI that appears as it launches, so a
    helper's own turn runs only when the test lets it."""
    made = len(FakeClient.made)
    task = asyncio.ensure_future(tool_of(found, name).call(arguments))
    while not task.done():
        if release:
            for client in FakeClient.made[made:]:
                client.go.set()
        await asyncio.sleep(0.01)
    return task.result()


def helper_says(text: str) -> None:
    """A helper's prompt gets `text` as its final result; the parent's turn stays open."""

    def script(prompt: str) -> list[Message | None]:
        return [] if prompt == "go" else [result(result=text)]

    FakeClient.script = script


async def open_parent(harness: Harness, kind: Any = None) -> SessionId:
    """A plan parent whose turn is running, as it is while it calls a tool."""
    parent = await harness.start_chat(
        NewChat(title="parent", model="haiku", kind=kind or Interactive())
    )
    first = OperatorText("go") if kind is None else InjectedText("go")
    await harness.send(parent, first)
    return parent


async def started(found: list[ToolDef], arguments: dict[str, Any]) -> tuple[str, FakeClient]:
    """Start a helper and return its handle and the fake CLI that got its task, without letting
    its turn end: the handle must be there before the answer is."""
    made = len(FakeClient.made)
    reply = await call(found, "delegate_run", arguments, release=False)
    await settle(lambda: any(client.queries for client in FakeClient.made[made:]))
    [client] = [client for client in FakeClient.made[made:] if client.queries]
    return str(answer(reply)["handle"]), client


def test_a_helper_returns_its_handle_before_it_answers(
    home: QmxHome, defs: list[list[ToolDef]]
) -> None:
    settings(home, targets=["claude"])
    helper_says("the folder holds 3 files")

    async def body(harness: Harness) -> None:
        parent = await open_parent(harness)
        handle, child = await started(defs[0], {"task": "count the files", "profile": "claude"})
        assert child.queries == ["count the files"]
        assert child.disconnected is False
        listed = answer(await call(defs[0], "delegate_list", {}))
        assert [(row["handle"], row["state"]) for row in listed["helpers"]] == [(handle, "running")]
        assert turn_of(home, parent) == "running"
        child.go.set()
        await settle(lambda: control_service(home).delegate_completions_all(parent) != [])
        [stored] = control_service(home).delegate_completions_all(parent).__iter__()
        assert (stored["handle"], stored["state"]) == (handle, "done")
        assert "the folder holds 3 files" in stored["summary"]
        assert stored["delivered_at"] is None

    run(body, home)


def test_a_completion_is_delivered_once_even_across_a_restart(
    home: QmxHome, defs: list[list[ToolDef]]
) -> None:
    settings(home, targets=["claude"])
    helper_says("the answer is 3")
    parent: list[SessionId] = []

    async def first(harness: Harness) -> None:
        parent.append(await open_parent(harness))
        _, child = await started(defs[0], {"task": "count", "profile": "claude"})
        child.go.set()
        await settle(lambda: control_service(home).delegate_completions_all(parent[0]) != [])
        assert FakeClient.made[1] is child

    run(first, home)
    assert FakeClient.made[1].disconnected is True

    async def second(harness: Harness) -> None:
        await harness.send(parent[0], OperatorText("what did you find"))
        report = FakeClient.made[-1].queries
        assert len(report) == 1
        assert report[0].startswith("Helper reports, which arrived between your turns:")
        assert "the answer is 3" in report[0]
        assert report[0].endswith("what did you find")
        await harness.send(parent[0], OperatorText("and now"))
        assert FakeClient.made[-1].queries[-1] == "and now"
        assert "Helper reports" not in FakeClient.made[-1].queries[-1]
        assert len(FakeClient.made[-1].queries) == 2

    run(second, home)


def test_steer_reaches_a_running_helper_and_stop_ends_another(
    home: QmxHome, defs: list[list[ToolDef]]
) -> None:
    settings(home, targets=["claude"])
    helper_says("done with what I had")

    async def body(harness: Harness) -> None:
        parent = await open_parent(harness)
        one, first_client = await started(defs[0], {"task": "first job", "profile": "claude"})
        two, second_client = await started(defs[0], {"task": "second job", "profile": "claude"})
        assert answer(
            await call(defs[0], "delegate_steer", {"handle": one, "text": "count the folders too"})
        ) == {"handle": one, "steer": "queued_for_checkpoint", "state": "running"}
        first_client.go.set()
        await settle(lambda: len(first_client.queries) == 2)
        assert first_client.queries[1] == "A note from your parent: count the folders too"
        assert answer(
            await call(defs[0], "delegate_stop", {"handle": two, "reason": "not needed"})
        ) == {"handle": two, "state": "stopped", "reason": "not needed"}
        await settle(lambda: len(control_service(home).delegate_completions_all(parent)) == 2)
        rows = {
            str(row["handle"]): row
            for row in control_service(home).delegate_completions_all(parent)
        }
        assert (rows[one]["state"], "1 steer read" in str(rows[one]["summary"])) == ("done", True)
        assert (rows[two]["state"], "not needed" in str(rows[two]["summary"])) == ("stopped", True)
        await settle(lambda: second_client.disconnected)

    run(body, home)


def test_a_helper_surface_is_inside_its_parents(home: QmxHome, defs: list[list[ToolDef]]) -> None:
    settings(home, targets=["claude"])
    helper_says("read it")

    async def body(harness: Harness) -> None:
        parent = await open_parent(harness)
        _, plain = await started(defs[0], {"task": "skim it", "profile": "claude"})
        _, judged = await started(
            defs[0], {"task": "judge it", "profile": "claude", "role": "judge"}
        )
        children = [
            SessionId(str(row["id"]))
            for row in control_service(home).sessions_list()
            if row.get("parent_id") == parent
        ]
        parent_surface = harness.surface(parent)
        plain_surface = harness.surface(children[0])
        judged_surface = harness.surface(children[1])
        assert parent_surface is not None and plain_surface is not None
        assert judged_surface is not None
        assert set(plain_surface.toolsets) == set(parent_surface.toolsets) - {"delegate"}
        assert judged_surface.toolsets == ()
        assert set(plain_surface.tools) <= set(parent_surface.tools)
        assert "Agent" not in plain_surface.builtins
        assert "qmx_delegate" not in set(plain.options.mcp_servers)
        assert {name for name, on in judged.toggled if not on} == {
            f"qmx_{name}" for name in set(parent_surface.toolsets) - {"delegate"}
        }

    run(body, home)


def test_a_profile_outside_the_allow_list_is_refused_before_any_child(
    home: QmxHome, defs: list[list[ToolDef]]
) -> None:
    settings(home, targets=["claude"])

    async def body(harness: Harness) -> None:
        await open_parent(harness)
        assert await call(defs[0], "delegate_run", {"task": "x", "profile": "kimi"}) == failure(
            "refused",
            "'kimi' is not in the delegate allow-list, [providers] delegate_targets, which "
            "lists claude",
        )
        assert len(FakeClient.made) == 1
        assert len(control_service(home).sessions_list()) == 1

    run(body, home)


def test_a_helper_is_bounded_verbatim_and_copies_its_parent(
    home: QmxHome, defs: list[list[ToolDef]]
) -> None:
    settings(home, targets=["claude"], max_turns=7, max_budget_usd=0.25)
    helper_says("the folder holds 3 files")

    async def body(harness: Harness) -> None:
        read_plan(harness, 0.1)
        parent = await open_parent(harness, Background())
        handle, child = await started(defs[0], {"task": "help: count", "profile": "claude"})
        session = next(
            row["id"]
            for row in control_service(home).sessions_list()
            if row.get("parent_id") == parent
        )
        record = read_record(home, SessionId(str(session)))
        assert record is not None
        assert record.config.kind == Child(parent, unattended=True)
        assert (record.config.profile, record.config.model) == ("claude", "haiku")
        options = child.options
        assert (options.verbatim_prompts, options.max_turns, options.max_budget_usd) == (
            True,
            7,
            0.25,
        )
        assert options.disallowed_tools[:2] == ["Agent", "Task"]
        child.go.set()
        await settle(lambda: control_service(home).delegate_completions_all(parent) != [])
        assert answer(await call(defs[0], "delegate_list", {}))["helpers"][0]["handle"] == handle

    run(body, home)


def test_a_cli_helper_asks_on_its_first_version_then_runs_under_its_grant(
    home: QmxHome, defs: list[list[ToolDef]], keys: None
) -> None:
    settings(home, targets=["claude", "kimi"])
    control = control_service(home)
    program = "import sys; print('cli answer: ' + sys.stdin.read().strip())"
    control.settings_put(
        "agents",
        {"cli_helper": [sys.executable, "-c", program]},  # pyright: ignore[reportArgumentType]
    )

    async def body(harness: Harness) -> None:
        parent = await open_parent(harness)
        ask = await call(
            defs[0], "delegate_run", {"task": "count", "profile": "kimi", "target": "cli"}
        )
        message = json.loads(ask["content"][0]["text"])["error"]["message"]
        assert "allow_cli=true" in message
        reply = await call(
            defs[0],
            "delegate_run",
            {"task": "count the files", "profile": "kimi", "target": "cli", "allow_cli": True},
        )
        handle = str(answer(reply)["handle"])
        await settle(
            lambda: (
                [
                    row
                    for row in control_service(home).delegate_completions_all(parent)
                    if row["handle"] == handle
                ]
                != []
            )
        )
        [stored] = [
            row
            for row in control_service(home).delegate_completions_all(parent)
            if row["handle"] == handle
        ]
        assert stored["state"] == "done"
        assert "cli answer: count the files" in str(stored["summary"])

    run(body, home)


@pytest.mark.parametrize(
    ("tool", "agent_id", "verdict"),
    [
        (
            "mcp__qmx_delegate__run",
            "a1b2",
            Deny("guard: a sub-agent cannot start a helper chat (mcp__qmx_delegate__run)"),
        ),
        ("mcp__qmx_delegate__run", None, Pass()),
        ("mcp__qmx_delegate__list", "a1b2", Pass()),
    ],
)
def test_the_gate_refuses_a_helper_from_inside_a_native_sub_agent(
    tool: str, agent_id: str | None, verdict: Deny | Pass
) -> None:
    from test_guard import RULES

    found = guard(
        tool,
        {"task": "x"},
        RULES,
        cwd="/d/w",
        agent_id=agent_id,
        permission_mode="default",
    )
    assert found == verdict


def test_a_handle_of_another_chat_is_refused(home: QmxHome, defs: list[list[ToolDef]]) -> None:
    settings(home, targets=["claude"])

    async def body(harness: Harness) -> None:
        await open_parent(harness)
        await harness.start_chat(NewChat(title="other", model="haiku", kind=Background()))
        assert await call(defs[0], "delegate_stop", {"handle": "h-nope"}) == failure(
            "refused", "no helper of this chat has the handle 'h-nope'"
        )
        assert answer(await call(defs[0], "delegate_list", {})) == {"helpers": []}

    run(body, home)


def test_the_start_tool_declares_its_effect_and_the_three_others_their_own(
    home: QmxHome, defs: list[list[ToolDef]]
) -> None:
    settings(home, targets=["claude"])

    async def body(harness: Harness) -> None:
        await open_parent(harness)
        found = {tool.name: tool.effect for tool in defs[0]}
        assert found["delegate_run"] is Effect.DOMAIN_WRITE
        assert found["delegate_list"] is Effect.READ
        assert found["delegate_steer"] is Effect.DOMAIN_WRITE
        assert found["delegate_stop"] is Effect.DOMAIN_WRITE

    run(body, home)
