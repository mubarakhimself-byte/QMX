from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fastmcp import Client
from qmx_broker.models import OrderProposal
from qmx_broker.service import BrokerService

from qmx_control.server import create_app, create_mcp
from qmx_control.service import ControlError, ControlService, Document


def test_broker_settings_and_portfolio_queue_rest_mcp_parity(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    assert service.portfolio_proposals() == []
    assert not (tmp_path / "portfolio.db").exists()
    values: Document = {
        "brokers": [
            {
                "id": "ic",
                "name": "IC Markets",
                "adapter": "ctrader",
                "connections": [
                    {
                        "id": "demo",
                        "credential_ref": "qmx/ctrader-demo",
                        "environment": "demo",
                        "accounts": [
                            {
                                "id": "101",
                                "currency": "USD",
                                "leverage": "50",
                                "permissions": ["read", "propose"],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    headers = {"Authorization": "Bearer offline-fixture"}

    async def run() -> None:
        async with Client(create_mcp(service)) as client:
            with TestClient(create_app(service, "offline-fixture")) as rest:
                written = rest.put("/api/settings/brokers", headers=headers, json=values)
                assert written.status_code == 200
                assert (
                    await client.call_tool("settings_get", {"section": "brokers"})
                ).data == written.json()
                broker = BrokerService(tmp_path, brokers=lambda: service.settings_get("brokers"))
                assert broker.list_accounts()["accounts"][0]["currency"] == "USD"
                broker.propose_order(
                    OrderProposal(
                        broker_id="ic",
                        connection_id="demo",
                        account_id="101",
                        symbol="EURUSD",
                        side="buy",
                        quantity="100",
                    )
                )
                queued = rest.get("/api/portfolio/proposals", headers=headers)
                assert queued.status_code == 200 and len(queued.json()) == 1
                assert (await client.call_tool("portfolio_proposals", {})).data == queued.json()
                assert queued.json()[0]["executed"] is False
                assert rest.get("/api/portfolio/proposals").status_code == 401
                invalid = rest.put(
                    "/api/settings/brokers",
                    headers=headers,
                    json={"brokers": [{"id": "secret", "clientSecret": "must-not-save"}]},
                )
                assert invalid.status_code == 400
                assert "must-not-save" not in (tmp_path / "settings.toml").read_text()
                assert "qmx/ctrader-demo" in (tmp_path / "settings.toml").read_text()

    asyncio.run(run())


def test_invalid_broker_settings_leave_existing_settings_unchanged(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    service.settings_put("brokers", {"brokers": []})
    before = (tmp_path / "settings.toml").read_bytes()
    with pytest.raises(ControlError, match="valid brokers"):
        service.settings_put("brokers", {"brokers": [{"id": "missing-fields"}]})
    assert (tmp_path / "settings.toml").read_bytes() == before
