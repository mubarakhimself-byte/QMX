"""The prompt-surface snapshot test (engine AD-15, AD-62): what each chat kind and node kind gets.

A change to what a model sees shows here as a reviewed diff.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from qma.harness.chat import unexpected_extensions
from qma.harness.home import QmxHome, SessionId
from qma.harness.launch import Background, ChatKind, Child, Home, Interactive, SubAgent
from qma.harness.surface import (
    CLI_BUILTINS,
    CLI_SKILLS,
    Declaration,
    HomeSlots,
    Supply,
    Surface,
    build,
    child_scope,
    render_state,
    surface_files,
)
from qma.harness.tools import Effect, ToolDef

PARENT = SessionId("0b9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e1f")
SCHEDULING = {"CronCreate", "CronDelete", "CronList", "ScheduleWakeup", "RemoteTrigger", "Workflow"}


async def _call(_arguments: dict[str, Any]) -> dict[str, Any]:
    return {}


def tool(toolset: str, op: str, description: str = "Does a thing.") -> ToolDef:
    schema: dict[str, object] = {"type": "object", "properties": {}}
    return ToolDef(toolset, op, description, schema, Effect.READ, _call)


TOOLS = (
    tool("library", "search"),
    tool("library", "get"),
    tool("research", "scout"),
    tool("data", "bars"),
    tool("workflows", "list"),
    tool("workflows", "start"),
    tool("delegate", "run"),
    tool("ops", "capacity"),
)


@pytest.fixture
def home(tmp_path: Path) -> QmxHome:
    plugin = tmp_path / "plugin"
    (plugin / "skills" / "qmx-overview").mkdir(parents=True)
    (plugin / "QMX.md").write_text("Money is read-only.\n", encoding="utf-8")
    (plugin / "skills" / "qmx-overview" / "SKILL.md").write_text(
        "---\nname: qmx-overview\ndescription: What QMX is. Use when asked.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    return QmxHome(tmp_path / "qmx", plugin_dir=plugin)


def supply(home: QmxHome, settings: dict[str, object] | None, tools: tuple[ToolDef, ...]) -> Supply:
    spill = home.root / "chats" / PARENT / "qmx-slots" / "skills"
    return Supply(tools, HomeSlots(home), settings or {}, (home.plugin_dir,), spill)


def surface(
    home: QmxHome,
    kind: ChatKind,
    wanted: Declaration = Declaration(),  # noqa: B008
    *,
    chat_home: Home = Home(),  # noqa: B008
    parent: Surface | None = None,
    settings: dict[str, object] | None = None,
    tools: tuple[ToolDef, ...] = TOOLS,
) -> Surface:
    return build(
        kind,
        chat_home,
        (),
        wanted,
        supply(home, settings, tools),
        workspace=home.root / "ws",
        parent=parent,
    )


def snapshot(found: Surface) -> dict[str, object]:
    return {
        "toolsets": found.toolsets,
        "tools": found.tools,
        "builtins_left_out": sorted(set(CLI_BUILTINS) - set(found.builtins)),
        "builtins_added": sorted(set(found.builtins) - set(CLI_BUILTINS)),
        "skills_left_out": sorted({*CLI_SKILLS, "qmx:qmx-overview"} - set(found.skills)),
        "slots": [slot.name for slot in found.slots if slot.text],
        "hooks": found.hooks,
        "env": dict(found.env),
    }


COPILOT_TOOLS = (
    "mcp__qmx_library__search",
    "mcp__qmx_library__get",
    "mcp__qmx_research__scout",
    "mcp__qmx_data__bars",
    "mcp__qmx_workflows__list",
    "mcp__qmx_workflows__start",
    "mcp__qmx_delegate__run",
    "mcp__qmx_ops__capacity",
)


def test_the_copilot_gets_its_home_preset_and_loses_only_the_cli_schedulers(
    home: QmxHome,
) -> None:
    assert snapshot(surface(home, Interactive())) == {
        "toolsets": ("library", "workflows", "data", "research", "delegate", "ops"),
        "tools": COPILOT_TOOLS,
        "builtins_left_out": sorted(SCHEDULING),
        "builtins_added": [],
        "skills_left_out": ["loop", "schedule"],
        "slots": ["rules", "pack_layers", "skills_index"],
        "hooks": ("PreToolUse",),
        "env": {},
    }


def test_a_background_chat_also_loses_the_worktree_tools(home: QmxHome) -> None:
    found = snapshot(surface(home, Background(), Declaration(observed=True, compact_at=0.4)))
    assert found == {
        "toolsets": ("library", "workflows", "data", "research", "delegate", "ops"),
        "tools": COPILOT_TOOLS,
        "builtins_left_out": sorted({*SCHEDULING, "EnterWorktree", "ExitWorktree"}),
        "builtins_added": [],
        "skills_left_out": ["loop", "schedule"],
        "slots": ["rules", "pack_layers", "skills_index"],
        "hooks": ("PreToolUse", "PostToolUse", "PreCompact", "Stop", "SubagentStop"),
        "env": {"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "40"},
    }


def test_an_engine_agent_node_sees_only_its_declared_toolsets_and_tools(home: QmxHome) -> None:
    intake = Declaration(
        toolsets=("library", "research", "data", "memory"),
        builtins=("Read",),
        skills=(),
        brief="Read each source and reply with JSON.",
    )
    found = surface(home, Background(), intake)
    assert (found.toolsets, found.tools, found.builtins, found.skills) == (
        ("library", "research", "data"),
        (
            "mcp__qmx_library__search",
            "mcp__qmx_library__get",
            "mcp__qmx_research__scout",
            "mcp__qmx_data__bars",
        ),
        ("Read",),
        (),
    )
    assert [slot.name for slot in found.slots if slot.text] == ["rules", "pack_layers", "brief"]
    assert found.append.endswith("Read each source and reply with JSON.")
    assert "- memory" not in found.append


def test_a_node_that_declares_skills_gets_them_and_the_skill_tool(home: QmxHome) -> None:
    found = surface(home, Background(), Declaration((), (), ("qmx:qmx-overview", "loop")))
    assert (found.builtins, found.skills, found.toolsets) == (
        ("Skill",),
        ("qmx:qmx-overview",),
        (),
    )


def test_an_llm_node_chat_gets_no_tool_at_all(home: QmxHome) -> None:
    found = surface(home, Background(), Declaration(builtins=()))
    assert (found.toolsets, found.tools, found.builtins, found.skills) == ((), (), (), ())


def test_a_helper_is_never_wider_than_its_parent(home: QmxHome) -> None:
    lab = Declaration(toolsets=("library", "research", "delegate"))
    parent = surface(home, Interactive(), lab, chat_home=Home("lab", "pod-7"))
    asked = child_scope(parent)
    child = surface(home, Child(PARENT, unattended=False), asked, chat_home=Home("lab", "pod-7"))
    wider = surface(
        home, Child(PARENT, unattended=False), Declaration(toolsets=("ops",)), parent=parent
    )
    assert (child.toolsets, wider.toolsets) == (("library", "research"), ())
    assert set(child.tools) <= set(parent.tools)
    assert set(child.builtins) <= set(parent.builtins) - {"Task", "EnterWorktree"}
    assert set(child.skills) <= set(parent.skills)
    assert "mcp__qmx_delegate__run" not in child.tools


def test_a_sub_agent_never_holds_a_tool_outside_the_surface(home: QmxHome) -> None:
    agents = {"reviewer": SubAgent("Reviews.", "Review it.", ("Read", "Bash", "CronCreate"))}
    found = surface(home, Background(), Declaration(builtins=("Read", "Bash"), agents=agents))
    assert found.agents["reviewer"].tools == ("Read", "Bash")


def test_the_home_preset_comes_from_settings(home: QmxHome) -> None:
    settings: dict[str, object] = {"home_toolsets": {"lab": ["research", "library"]}}
    found = surface(home, Interactive(), chat_home=Home("lab"), settings=settings)
    assert found.toolsets == ("research", "library")


def test_the_digest_changes_when_a_description_or_a_slot_changes(home: QmxHome) -> None:
    first = surface(home, Interactive()).digest
    again = surface(home, Interactive()).digest
    described = (*TOOLS[:-1], tool("ops", "capacity", "Reads the capacity queue."))
    retold = surface(home, Interactive(), tools=described).digest
    (home.root / "slots").mkdir(parents=True)
    (home.root / "slots" / "persona.md").write_text("Be brief.", encoding="utf-8")
    persona = surface(home, Interactive())
    assert first == again
    assert len({first, retold, persona.digest}) == 3
    assert "# Persona\n\nBe brief." in persona.append
    assert "Be brief." not in surface(home, Background()).append


def test_a_slot_over_budget_spills_to_a_skill_and_keeps_a_pointer(home: QmxHome) -> None:
    (home.root / "slots" / "methodology").mkdir(parents=True)
    long = "Step one. " * 2_000 + "!`rm -rf /`"
    (home.root / "slots" / "methodology" / "general.md").write_text(long, encoding="utf-8")
    found = surface(home, Interactive())
    [slot] = [slot for slot in found.slots if slot.name == "methodology"]
    files = surface_files(found, home.root / "chats" / PARENT)
    skill = files[
        home.root / "chats" / PARENT / "qmx-slots" / "skills" / "methodology" / "SKILL.md"
    ]
    assert (slot.spilled, len(slot.text) <= 8_000) == (True, True)
    assert "the skill qmx-slots:methodology" in slot.text
    assert "qmx-slots:methodology" in found.skills
    assert found.plugins[-1] == home.root / "chats" / PARENT / "qmx-slots"
    assert "! `rm -rf /`" in skill and "!`" not in skill
    assert skill.count("Step one.") == 2_000


def test_a_slot_budget_comes_from_settings(home: QmxHome) -> None:
    settings: dict[str, object] = {"slot_budgets": {"rules": 10}}
    found = surface(home, Interactive(), settings=settings)
    assert [slot.name for slot in found.slots if slot.spilled] == ["rules"]


def test_per_turn_state_rides_the_user_message() -> None:
    assert render_state() == ""
    assert render_state("pod-7", "split", ("run-1", "run-2"), ("pack lab added",)) == (
        "<qmx_state>\nopen subject: pod-7\nlayout: split\nticked runs: run-1, run-2\n"
        "note: pack lab added\n</qmx_state>"
    )


def test_a_child_kind_loses_the_agent_tool_even_when_declared(home: QmxHome) -> None:
    found = surface(home, Child(PARENT, unattended=True), Declaration(builtins=("Task", "Read")))
    assert found.builtins == ("Read",)
    assert "delegate" not in found.toolsets


def test_the_chats_own_slots_plugin_is_not_an_unexpected_extension() -> None:
    info = {"commands": [{"name": "qmx-slots:methodology"}, {"name": "planted:go"}]}
    found = unexpected_extensions(info, {"mcpServers": []}, frozenset())  # pyright: ignore[reportArgumentType]
    assert found == ["command planted:go"]
