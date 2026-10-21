"""Both control doors drive real stages; only REST can obtain an operator signature."""

from __future__ import annotations

import asyncio
import json
import secrets
import shutil
from pathlib import Path
from typing import cast

from fastapi.testclient import TestClient
from fastmcp import Client
from qmx_apps.errors import Document

from qmx_control.server import create_app, create_mcp
from qmx_control.service import ControlService


def test_actual_road_evidence_signature_and_transport_parity(tmp_path: Path) -> None:
    source = tmp_path / "definition"
    example = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
    shutil.copytree(example, source)
    manifest = source / "app.toml"
    manifest.write_text(manifest.read_text().replace('risk = "shows"', 'risk = "money"'))
    (source / "server.py").write_text(
        'from fastmcp import FastMCP\nm = FastMCP("proposal fixture")\n'
        '@m.tool(annotations={"readOnlyHint": True})\n'
        'def read_proposal(): return {"proposal": "unsigned", "sent": False}\n'
        "m.run()\n"
    )
    (source / "tests").mkdir()
    (source / "tests/test_own.py").write_text(
        "import os, unittest\nclass Own(unittest.TestCase):\n"
        ' def test_stage(self): self.assertEqual(os.environ["QMX_STAGE"], "tests")\n'
    )
    (source / "proofs").mkdir()
    for stage, origin in (("sandbox", "recorded"), ("shadow", "live")):
        (source / f"proofs/{stage}.json").write_text(
            json.dumps(
                {
                    "source": origin,
                    "cases": [
                        {
                            "tool": "read_proposal",
                            "arguments": {},
                            "expected": {"proposal": "unsigned", "sent": False},
                        },
                    ],
                }
            )
        )
    service = ControlService(tmp_path / "home")
    token = secrets.token_urlsafe(32)
    headers = {"Authorization": f"Bearer {token}"}

    async def journey() -> None:
        with TestClient(create_app(service, token)) as rest:
            async with Client(create_mcp(service)) as mcp:
                created = rest.post(
                    "/api/apps",
                    headers=headers,
                    params={"path": str(source), "trust": "first_party"},
                )
                assert created.status_code == 200, created.text
                revision = created.json()["definition_hash"]
                refused = rest.post("/api/apps/exchange-status/start", headers=headers)
                assert refused.status_code == 409
                first = rest.post(
                    "/api/apps/exchange-status/test",
                    headers=headers,
                    params={"expected_hash": revision, "stage": "tests"},
                )
                assert first.status_code == 200, first.text
                for stage in ("sandbox", "shadow"):
                    result = await mcp.call_tool(
                        "apps_admin_test",
                        {"app_id": "exchange-status", "expected_hash": revision, "stage": stage},
                    )
                    assert result.data["stage"] == stage
                evidence = rest.get("/api/apps/exchange-status/evidence", headers=headers)
                assert (
                    evidence.json()
                    == (
                        await mcp.call_tool("apps_admin_evidence", {"app_id": "exchange-status"})
                    ).data
                )
                denied = await mcp.call_tool(
                    "apps_admin_publish",
                    {"app_id": "exchange-status", "expected_hash": revision},
                    raise_on_error=False,
                )
                assert denied.is_error and "signature_required" in str(denied.content)
                assert "apps_sign" not in [tool.name for tool in await mcp.list_tools()]
                signed = rest.post(
                    "/api/apps/exchange-status/sign",
                    headers=headers,
                    params={"definition_hash": revision},
                )
                assert signed.status_code == 200
                published = await mcp.call_tool(
                    "apps_admin_publish",
                    {
                        "app_id": "exchange-status",
                        "expected_hash": revision,
                        "signature": signed.json()["signature"],
                    },
                )
                assert published.data["stage"] == "live"
                assert (
                    cast(Document, service.apps_get("exchange-status")["runtime"])["status"]
                    == "running"
                )
                stale = rest.post(
                    "/api/apps/exchange-status/publish",
                    headers=headers,
                    params={"expected_hash": revision, "signature": signed.json()["signature"]},
                )
                assert (
                    stale.status_code == 409
                    and stale.json()["error"]["code"] == "publication_conflict"
                )
                assert (
                    await mcp.call_tool("apps_admin_evidence", {"app_id": "exchange-status"})
                ).data[-1] == published.data

                # Replacement and rollback must run different immutable processes.
                service.apps_stop("exchange-status")
                manifest.write_text(
                    manifest.read_text().replace('version = "1.0.0"', 'version = "1.1.0"')
                )
                server_script = source / "server.py"
                server_script.write_text(
                    server_script.read_text().replace('"unsigned"', '"unsigned v2"')
                )
                for stage in ("sandbox", "shadow"):
                    plan = source / f"proofs/{stage}.json"
                    plan.write_text(plan.read_text().replace('"unsigned"', '"unsigned v2"'))
                updated = rest.put(
                    "/api/apps/exchange-status",
                    headers=headers,
                    params={
                        "path": str(source),
                        "trust": "first_party",
                        "expected_hash": revision,
                    },
                )
                assert updated.status_code == 200, updated.text
                next_revision = updated.json()["definition_hash"]
                for stage in ("tests", "sandbox", "shadow"):
                    check = await mcp.call_tool(
                        "apps_admin_test",
                        {
                            "app_id": "exchange-status",
                            "expected_hash": next_revision,
                            "stage": stage,
                        },
                    )
                    assert check.data["passed"] is True
                signed_next = rest.post(
                    "/api/apps/exchange-status/sign",
                    headers=headers,
                    params={
                        "definition_hash": next_revision,
                        "expected_active": published.data["revision"],
                    },
                )
                replaced = await mcp.call_tool(
                    "apps_admin_publish",
                    {
                        "app_id": "exchange-status",
                        "expected_hash": next_revision,
                        "expected_active": published.data["revision"],
                        "signature": signed_next.json()["signature"],
                    },
                )
                assert service.apps_call("exchange-status", "read_proposal", {})["result"] == {
                    "proposal": "unsigned v2",
                    "sent": False,
                }
                signed_undo = rest.post(
                    "/api/apps/exchange-status/sign",
                    headers=headers,
                    params={
                        "definition_hash": revision,
                        "expected_active": replaced.data["revision"],
                        "rollback": True,
                    },
                )
                undone = rest.post(
                    "/api/apps/exchange-status/rollback",
                    headers=headers,
                    params={
                        "expected_active": replaced.data["revision"],
                        "signature": signed_undo.json()["signature"],
                    },
                )
                assert undone.status_code == 200, undone.text
                assert (
                    undone.json()["action"] == "rollback"
                    and undone.json()["definition_hash"] == revision
                )
                assert undone.json()["revision"] != published.data["revision"]
                assert service.apps_get("exchange-status")["definition_hash"] == next_revision
                assert service.apps_call("exchange-status", "read_proposal", {})["result"] == {
                    "proposal": "unsigned",
                    "sent": False,
                }

    try:
        asyncio.run(journey())
    finally:
        service.close()
