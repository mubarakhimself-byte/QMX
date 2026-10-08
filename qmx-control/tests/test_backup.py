from __future__ import annotations

import asyncio
import secrets
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fastmcp import Client

from qmx_control.server import create_app, create_mcp
from qmx_control.service import ControlService


def test_backup_settings_and_rest_mcp_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert shutil.which("rclone"), "rclone must be installed for backup integration tests"
    config = tmp_path / "rclone.conf"
    config.write_text("[fixture]\ntype = local\n")
    monkeypatch.setenv("RCLONE_CONFIG", str(config))
    service = ControlService(tmp_path / "home")
    example = Path(__file__).resolve().parents[2] / "examples/apps/exchange-status"
    service.apps_create(str(example), "first_party")
    service.apps_start("exchange-status")
    volume = service.home / "apps/exchange-status"
    (volume / "blobs/report.txt").write_text("original")
    token = secrets.token_urlsafe(32)
    headers = {"Authorization": f"Bearer {token}"}

    async def journey() -> None:
        with TestClient(create_app(service, token)) as rest:
            async with Client(create_mcp(service)) as mcp:
                values = {
                    "repository": str(tmp_path / "weekly.git"),
                    "remote": "fixture",
                    "bucket": (tmp_path / "bucket").as_posix(),
                    "enabled": False,
                }
                response = rest.put("/api/settings/backup", headers=headers, json=values)
                assert response.status_code == 200, response.text
                assert (await mcp.call_tool("settings_get", {"section": "backup"})).data == values
                backed = rest.post("/api/apps/exchange-status/backup", headers=headers)
                assert backed.status_code == 200, backed.text
                assert backed.json()["restore_test"] == {"passed": True}
                refused = rest.post(
                    "/api/apps/exchange-status/restore",
                    headers=headers,
                    params={"snapshot_id": backed.json()["snapshot_id"]},
                )
                assert refused.status_code == 409
                assert refused.json()["error"]["code"] == "volume_busy"
                service.apps_stop("exchange-status")
                (volume / "blobs/report.txt").write_text("changed")
                restored = await mcp.call_tool(
                    "apps_restore",
                    {"app_id": "exchange-status", "snapshot_id": backed.json()["snapshot_id"]},
                )
                assert restored.data["checksums"] == backed.json()["checksums"]
                assert (volume / "blobs/report.txt").read_text() == "original"
                data = service.events("apps")[-1]["data"]
                assert isinstance(data, dict) and data["type"] == "restored"

    try:
        asyncio.run(journey())
    finally:
        service.close()
