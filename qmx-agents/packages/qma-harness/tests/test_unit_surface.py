"""The copilot sees what every agent sees (Part A AD-117, A8): the unit doors are on the default
copilot surface, and a Library refusal reaches the model with every problem it named."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import cast

from qmx_broker.service import BrokerService
from qmx_control.service import ControlService
from qmx_library.kinds import Problem
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


def test_a_publish_refusal_reaches_the_model_with_every_problem(tmp_path: Path) -> None:
    home = QmxHome(tmp_path / "home")
    control, defs = served(home)
    merge = next(tool for tool in defs if tool.name == "library_merge")
    store = control.library.store
    store.register_checker("qml.unit/1", two_problems)
    fields = cast("JsonObject", {**template(), "unit_id": "u"})
    draft = Draft("unit", "u", "u", fields=fields)
    saved = store.put(Principal("operator"), draft, on=drafts_ref("u"), expected_head=None)
    try:
        answer = asyncio.run(
            merge.call({"artifact_id": saved.object_id, "from_ref": drafts_ref("u")})
        )
    finally:
        control.close()

    error = json.loads(answer["content"][0]["text"])["error"]
    assert answer["is_error"] is True
    assert (error["code"], error["message"]) == (
        "check_failed",
        "unit: ema@1 is not in the unit's pins",
    )
    assert [p["where"] for p in error["problems"]] == [["/logic/long"], ["/markets"]]
