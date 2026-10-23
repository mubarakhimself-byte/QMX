"""The `brokers` section is read once into `connections`, and broker rows are read-only."""

from __future__ import annotations

import tomllib
from pathlib import Path

from qmx_broker.service import BrokerService

from qmx_control.service import ControlService, Document

LEGACY: Document = {
    "brokers": [
        {
            "id": "ic",
            "name": "IC Markets",
            "adapter": "ctrader",
            "connections": [
                {
                    "id": "demo",
                    "credential_ref": "qmx/read/ic-demo",
                    "environment": "demo",
                    "accounts": [{"id": "101", "currency": "USD", "leverage": "50"}],
                }
            ],
        }
    ]
}


def test_the_brokers_section_is_read_once_into_connections(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    written = service.settings_put("brokers", LEGACY)

    stored = tomllib.loads((tmp_path / "settings.toml").read_text("utf-8"))

    assert "brokers" not in stored
    assert stored["connections"][0]["kind"] == "broker"
    assert written == service.settings_get("brokers")
    assert service.settings_get("brokers")["brokers"][0]["adapter"] == "ctrader"
    assert service.settings_get("connections")["connections"][0]["connections"][0]["scope"] == (
        "read"
    )

    rows = BrokerService(
        tmp_path, brokers=lambda: service.settings_get("connections")
    ).list_connections()

    assert rows["total"] == 1
    assert rows["connections"][0]["home"] == "pc"
    assert [account["id"] for account in rows["connections"][0]["accounts"]] == ["101"]
    assert "credential_ref" not in str(rows)
