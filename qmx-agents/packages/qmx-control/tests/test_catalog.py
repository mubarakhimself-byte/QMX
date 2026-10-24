from __future__ import annotations

import asyncio
import json
import secrets
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fastmcp import Client

from qmx_control.catalog import (
    CatalogError,
    OperationSpec,
    check,
    control_rows,
    name_problem,
    node_types,
    rest_routes,
    rows,
    spill,
)
from qmx_control.server import create_app, create_mcp
from qmx_control.service import ControlService

BEARER = secrets.token_urlsafe(16)
HEADERS = {"Authorization": f"Bearer {BEARER}"}


def row(name: str) -> OperationSpec:
    return next(found for found in rows() if found.name == name)


def test_a_rows_rest_route_tool_and_node_type_all_come_from_it(tmp_path: Path) -> None:
    search = row("library_search")
    assert (search.target, search.id, search.toolset) == (
        "library_search",
        "qmx.library_search",
        "library",
    )
    assert [(r.name, d.verb, d.path) for r, d in rest_routes(rows()) if r is search] == [
        ("library_search", "GET", "/api/library")
    ]
    assert node_types(rows())["qmx.library_search"] == "none"
    assert "qmx.workflows_put" not in node_types(rows())
    service = ControlService(tmp_path)

    async def tools() -> set[str]:
        async with Client(create_mcp(service)) as mcp:
            return {tool.name for tool in await mcp.list_tools()}

    assert asyncio.run(tools()) == {found.name for found in control_rows()}
    with TestClient(create_app(service, BEARER)) as rest:
        schema = rest.get("/openapi.json", headers=HEADERS).json()
        assert schema["paths"]["/api/library"]["get"]["operationId"] == "library_search"
        assert rest.get("/api/apps/registry", headers=HEADERS).status_code == 200


def test_the_wire_name_check_holds_64_characters() -> None:
    assert name_problem("x" * 54) is None
    assert name_problem("x" * 55) == f"mcp__qmx__{'x' * 55} is longer than 64 characters"
    assert name_problem("library.search") == "'library.search' must match ^[a-zA-Z0-9_-]+$"
    long = replace(row("library_get"), op="get_" + "x" * 50)
    with pytest.raises(CatalogError, match="longer than 64 characters"):
        check([long])


def test_check_refuses_a_duplicate_a_silent_left_out_row_and_a_second_money_proposer() -> None:
    get = row("library_get")
    with pytest.raises(CatalogError, match="library_get is declared twice"):
        check([get, get])
    with pytest.raises(CatalogError, match="left off the agent surface without a reason"):
        check([replace(get, agent=False)])
    with pytest.raises(CatalogError, match="cannot ask money"):
        check([replace(get, approval="propose_money")])


def test_a_long_answer_spills_to_the_library_as_head_tail_and_id(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    get = row("library_get")
    assert spill("short", get, service.library_save) == "short"
    text = "a" * 10_000 + "b" * 15_000
    spilled = json.loads(spill(text, get, service.library_save))
    assert (spilled["chars"], spilled["head"], spilled["tail"]) == (25_000, "a" * 2000, "b" * 2000)
    saved = service.library_get(spilled["artifact_id"])
    assert saved["content"] == {"operation": "qmx.library_get", "text": text}


def test_only_the_broker_row_proposes_an_order() -> None:
    assert [found.name for found in rows() if found.approval == "propose_money"] == [
        "node_propose_order"
    ]


def test_rest_only_rows_stay_off_the_agent_surface() -> None:
    assert sorted(found.name for found in rows() if not found.agent) == [
        "apps_admin_call",
        "apps_admin_enable",
        "library_move",
        "library_server_lost",
        "ops_backup_weekly",
        "ops_sessions_append",
        "ops_sessions_create",
        "ops_sessions_stream",
        "settings_read_put",
    ]
