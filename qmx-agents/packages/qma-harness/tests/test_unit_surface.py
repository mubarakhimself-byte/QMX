"""The copilot sees what every agent sees (Part A AD-117, A8): the unit doors are on the default
copilot surface, a Library refusal reaches the model with every problem it named, and the
model's merge of a unit onto `main` is refused because publishing is his click."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from qmx_broker.service import BrokerService
from qmx_control.service import ControlService, WorkflowEngine
from qmx_library.kinds import Checker, Problem
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import Principal, drafts_ref
from qmx_tools.gather import template
from qmx_tools.service import DomainContext

from qma.harness.home import QmxHome
from qma.harness.launch import Home, Interactive
from qma.harness.surface import Declaration, HomeSlots, Supply, build
from qma.harness.tools import ToolDef, tool_defs

SEVEN = {
    "mcp__qmx_unit__new",
    "mcp__qmx_unit__check",
    "mcp__qmx_unit__explain",
    "mcp__qmx_blocks__find",
    "mcp__qmx_blocks__get",
    "mcp__qmx_blocks__check",
    "mcp__qmx_blocks__match",
}


def served(home: QmxHome) -> tuple[ControlService, list[ToolDef]]:
    control = ControlService(home.root)
    domain = DomainContext(root=home.root)
    domain.control, domain.library = control, control.library
    defs = asyncio.run(
        tool_defs(control=control, broker=BrokerService(home.root), domain=domain, delegate=None)
    )
    return control, defs


def test_every_served_core_tool_and_the_seven_unit_doors_are_on_the_copilots_surface(
    tmp_path: Path,
) -> None:
    home = QmxHome(tmp_path / "home")
    control, defs = served(home)
    spill = home.root / "chats" / "c" / "qmx-slots" / "skills"
    supply = Supply(tuple(defs), HomeSlots(home), {}, (home.plugin_dir,), spill)
    try:
        found = build(Interactive(), Home(), (), Declaration(), supply, workspace=home.root / "ws")
    finally:
        control.close()

    assert set(found.tools) >= SEVEN
    assert sorted({tool.full for tool in defs} - set(found.tools)) == []


def test_unit_check_through_the_chat_answers_every_problem_and_saves_only_a_draft(
    tmp_path: Path,
) -> None:
    home = QmxHome(tmp_path / "home")
    control, defs = served(home)
    tools = {tool.name: tool for tool in defs}
    try:
        made = json.loads(asyncio.run(tools["unit_new"].call({}))["content"][0]["text"])
        item = made["item"]
        document = template()
        document["direction"] = "sideways"
        answer = asyncio.run(tools["unit_check"].call({"document": document, "item": item}))
        checked = json.loads(answer["content"][0]["text"])
        store = control.library.store
        kinds = store.catalog.db.execute("SELECT DISTINCT kind FROM objects").fetchall()
    finally:
        control.close()

    assert (checked["verdict"], checked["counts"]["errors"]) == ("fail", 1)
    assert checked["saved"]["object_id"] is None
    assert [p["where"] for p in checked["saved"]["refused"]] == [["/direction"]]
    assert kinds == [("unit",)]


def two_problems(fields: JsonObject) -> list[Problem]:
    return [
        Problem("ema@1 is not in the unit's pins", ("/logic/long",), "check_failed", "B/pin"),
        Problem("no market is named", ("/markets",), "check_failed", "A/shape"),
    ]


def no_runs(workflow_id: str | None) -> list[object]:
    return []


def a_unit_draft(control: ControlService, checker: Checker, principal: str) -> str:
    """A unit draft on `u`'s draft ref, with the engine door's caller reader naming `principal`."""
    caller = SimpleNamespace(principal=principal)
    door = SimpleNamespace(principal=lambda: caller, workflow_runs_list=no_runs)
    control.attach_workflow_engine(cast("WorkflowEngine", door))
    store = control.library.store
    store.register_checker("qml.unit/1", checker)
    fields = cast("JsonObject", {**template(), "unit_id": "u"})
    draft = Draft("unit", "u", "u", fields=fields)
    return store.put(Principal("operator"), draft, on=drafts_ref("u"), expected_head=None).object_id


def merged_by_the_model(control: ControlService, defs: list[ToolDef], saved: str) -> dict[str, Any]:
    merge = next(tool for tool in defs if tool.name == "library_merge")
    try:
        answer = asyncio.run(merge.call({"artifact_id": saved, "from_ref": drafts_ref("u")}))
        head = control.library.store.head("u", "main")
    finally:
        control.close()
    assert answer["is_error"] is True
    return {"error": json.loads(answer["content"][0]["text"])["error"], "main": head}


def test_the_models_merge_of_a_unit_draft_is_refused_as_his_click(tmp_path: Path) -> None:
    control, defs = served(QmxHome(tmp_path / "home"))
    saved = a_unit_draft(control, lambda fields: [], "agent:chat-1")

    found = merged_by_the_model(control, defs, saved)

    assert (found["error"]["code"], found["error"]["message"]) == (
        "his_click",
        "publishing a unit onto main is his click; agent:chat-1 writes unit drafts only, and he "
        "publishes them from his own door",
    )
    assert found["main"] is None


def test_a_refusal_reaches_the_tool_error_with_every_problem_it_named(tmp_path: Path) -> None:
    control, defs = served(QmxHome(tmp_path / "home"))
    saved = a_unit_draft(control, two_problems, "operator")

    found = merged_by_the_model(control, defs, saved)

    assert (found["error"]["code"], found["error"]["message"]) == (
        "check_failed",
        "unit: ema@1 is not in the unit's pins",
    )
    assert [p["where"] for p in found["error"]["problems"]] == [["/logic/long"], ["/markets"]]
    assert found["main"] is None
