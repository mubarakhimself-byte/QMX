from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from fastmcp import Client

from qmx_control.catalog import control_rows
from qmx_control.server import create_app, create_mcp
from qmx_control.service import ControlService

REMOVED_ROUTES = [
    ("POST", "/api/runs/remote"),
    ("GET", "/api/runs/r1/status"),
    ("GET", "/api/runs/r1/logs"),
    ("POST", "/api/runs/r1/fetch"),
    ("POST", "/api/runs/r1/resume"),
    ("POST", "/api/runs/r1/stop"),
    ("POST", "/api/jobs/remote"),
    ("GET", "/api/jobs/r1/status"),
    ("GET", "/api/jobs/r1/logs"),
    ("POST", "/api/jobs/r1/fetch"),
]
REMOVED_TOOLS = {
    "workflows_remote_start",
    "workflows_remote_status",
    "workflows_remote_logs",
    "workflows_remote_fetch",
    "workflows_remote_resume",
    "workflows_remote_stop",
    "workflows_jobs_run",
    "workflows_jobs_status",
    "workflows_jobs_logs",
    "workflows_jobs_fetch",
}


def test_the_old_remote_run_routes_are_gone(tmp_path: Path) -> None:
    token = str(uuid4())
    headers = {"Authorization": "Bearer " + token}
    with TestClient(create_app(ControlService(tmp_path), token)) as rest:
        answers = {
            (verb, url): rest.request(verb, url, headers=headers).status_code
            for verb, url in REMOVED_ROUTES
        }
    # `runs_get` still serves GET /api/runs/{run_id}, so this one path answers "wrong method".
    assert answers == {**dict.fromkeys(REMOVED_ROUTES, 404), ("POST", "/api/runs/remote"): 405}


def test_no_catalog_row_or_tool_starts_old_remote_work(tmp_path: Path) -> None:
    assert not {row.wire for row in control_rows()} & REMOVED_TOOLS

    async def listed() -> set[str]:
        async with Client(create_mcp(ControlService(tmp_path))) as mcp:
            return {tool.name for tool in await mcp.list_tools()}

    assert not asyncio.run(listed()) & REMOVED_TOOLS
