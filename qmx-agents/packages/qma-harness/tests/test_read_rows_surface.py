"""The core read rows reach every chat (Part C slice C-24, Level 0 AD-31): `instrument_get` and
`readings_query` are on the default copilot surface, and a call through the chat's tool answers
from his Library, or refuses reading history where no market-data door can apply a holdout."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from pydantic import JsonValue
from qmx_broker.service import BrokerService
from qmx_control.library import OPERATOR
from qmx_control.service import ControlService
from qmx_library.port import Draft
from qmx_library.principal import MAIN
from qmx_tools.service import DomainContext

from qma.harness.home import QmxHome
from qma.harness.launch import Home, Interactive
from qma.harness.surface import Declaration, HomeSlots, Supply, build
from qma.harness.tools import ToolDef, tool_defs

EURUSD: dict[str, JsonValue] = {
    "venue": "icmarkets-ctrader",
    "symbol": "EURUSD",
    "market_id": "eurusd",
    "class": "fx",
    "currency": "USD",
    "status": "live",
    "contract_size": "100000",
}


def served(home: QmxHome) -> tuple[ControlService, list[ToolDef]]:
    control = ControlService(home.root)
    domain = DomainContext(root=home.root)
    domain.control, domain.library = control, control.library
    defs = asyncio.run(
        tool_defs(control=control, broker=BrokerService(home.root), domain=domain, delegate=None)
    )
    return control, defs


def test_both_read_rows_are_on_the_copilots_default_surface(tmp_path: Path) -> None:
    home = QmxHome(tmp_path / "home")
    control, defs = served(home)
    spill = home.root / "chats" / "c" / "qmx-slots" / "skills"
    supply = Supply(tuple(defs), HomeSlots(home), {}, (home.plugin_dir,), spill)
    try:
        found = build(Interactive(), Home(), (), Declaration(), supply, workspace=home.root / "ws")
    finally:
        control.close()

    assert {"mcp__qmx_instrument__get", "mcp__qmx_readings__query"} <= set(found.tools)


def test_the_chats_tools_read_a_record_and_refuse_history_without_a_door(tmp_path: Path) -> None:
    home = QmxHome(tmp_path / "home")
    control, defs = served(home)
    tools = {tool.name: tool for tool in defs}
    store = control.library.store
    store.wall = lambda: datetime(2025, 1, 1, tzinfo=UTC)
    store.put(
        OPERATOR,
        Draft("instrument", "eurusd-ic", "EURUSD", fields=EURUSD),
        on=MAIN,
        expected_head=None,
    )
    try:
        record = asyncio.run(tools["instrument_get"].call({"market_id": "eurusd"}))
        history = asyncio.run(
            tools["readings_query"].call(
                {
                    "reading": "volatility-state",
                    "window": {"start": "2025-01-06T00:00:00Z", "end": "2025-01-13T00:00:00Z"},
                }
            )
        )
    finally:
        control.close()
    answer = json.loads(cast("str", record["content"][0]["text"]))

    assert (answer["id"], answer["version"], answer["record"]["contract_size"]) == (
        "eurusd-ic",
        1,
        "100000",
    )
    assert history["is_error"] is True
    assert "No market-data door on this host" in history["content"][0]["text"]
