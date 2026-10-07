from __future__ import annotations

import asyncio
import secrets
from pathlib import Path

import psutil
from fastapi.testclient import TestClient
from fastmcp import Client

from qmx_control.server import create_app, create_mcp
from qmx_control.service import ControlService


def test_real_app_registry_parity_artifact_and_owner_cancellation(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    token = secrets.token_urlsafe(32)
    headers = {"Authorization": f"Bearer {token}"}
    example = Path(__file__).resolve().parents[2] / "examples/apps/exchange-status"

    async def journey() -> None:
        with TestClient(create_app(service, token)) as rest:
            async with Client(create_mcp(service)) as mcp:
                denied = rest.post("/api/apps", headers=headers, params={"path": str(example)})
                assert denied.status_code == 409
                assert denied.json()["error"]["code"] == "tier_required"
                installed = rest.post(
                    "/api/apps",
                    headers=headers,
                    params={"path": str(example), "trust": "first_party"},
                )
                assert installed.status_code == 200, installed.text
                assert (await mcp.call_tool("apps_list", {})).data == rest.get(
                    "/api/apps", headers=headers
                ).json()
                started = rest.post("/api/apps/exchange-status/start", headers=headers)
                assert started.status_code == 200, started.text
                pid = started.json()["pid"]
                assert psutil.pid_exists(pid)
                registry = rest.get("/api/apps/registry", headers=headers)
                assert registry.status_code == 200
                assert (await mcp.call_tool("apps_registry", {})).data == registry.json()
                response = rest.post(
                    "/api/apps/exchange-status/tools/record",
                    headers=headers,
                    json={
                        "exchange": "api-fixture",
                        "status": "operational",
                        "observed_at": "2026-10-07",
                    },
                )
                assert response.status_code == 200, response.text
                snapshot = await mcp.call_tool(
                    "apps_call", {"app_id": "exchange-status", "tool": "snapshot", "arguments": {}}
                )
                assert snapshot.data["artifact_ref"]["producer_app"] == "exchange-status"
                resource = rest.get(
                    "/api/apps/exchange-status/resources",
                    headers=headers,
                    params={"uri": "ui://exchange-status/view.html"},
                )
                assert resource.status_code == 200
                assert "api-fixture" in resource.json()[0]["text"]
                job_id = started.json()["instance_id"]
                canceled = rest.post(f"/api/jobs/{job_id}/cancel", headers=headers)
                assert canceled.status_code == 200, canceled.text
                assert canceled.json()["status"] == "cancel_requested"
                jobs = rest.get("/api/jobs", headers=headers).json()
                assert next(job for job in jobs if job["id"] == job_id)["status"] == "stopped"
                assert not psutil.pid_exists(pid)
                assert rest.get("/api/apps/registry", headers=headers).json() == []
                assert (
                    rest.get("/api/apps/exchange-status", headers=headers).json()["runtime"]["pid"]
                    is None
                )
                failed = await mcp.call_tool(
                    "apps_start", {"app_id": "missing"}, raise_on_error=False
                )
                assert failed.is_error
                assert "not_found" in str(failed.content)

    asyncio.run(journey())
