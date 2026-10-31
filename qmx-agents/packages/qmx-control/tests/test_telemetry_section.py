"""`PUT /api/settings/telemetry` refuses a `send_to` no sender can use (UI handoff section 26 gap
6; design 06 section 9), and its read names every default."""

from __future__ import annotations

import secrets
import tomllib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qmx_control.server import create_app
from qmx_control.service import ControlService

HIS = """[engine.placement.myserver]
provider = "ssh"
kind = "owned"
can = ["run"]

[engine.placement.usb]
via = "folder"
can = ["keep"]
path = 'E:\\'
"""


@pytest.fixture
def rest(tmp_path: Path) -> tuple[TestClient, dict[str, str], Path]:
    home = tmp_path / "QMX" / "data"
    home.mkdir(parents=True)
    (home / "settings.toml").write_text(HIS, encoding="utf-8")
    token = secrets.token_urlsafe(32)
    service = ControlService(home, secret_getter=lambda _service, _name: None)
    return TestClient(create_app(service, token)), {"Authorization": f"Bearer {token}"}, home


def test_send_to_takes_off_this_pc_and_a_machine_and_refuses_the_rest_naming_the_value(
    rest: tuple[TestClient, dict[str, str], Path],
) -> None:
    client, bearer, home = rest
    with client:
        answers = {
            value: client.put("/api/settings/telemetry", headers=bearer, json={"send_to": value})
            for value in ("banana", "Not a place!", "usb", "off", "this-pc", "myserver")
        }
    assert {value: answer.status_code for value, answer in answers.items()} == {
        "banana": 400,
        "Not a place!": 400,
        "usb": 400,
        "off": 200,
        "this-pc": 200,
        "myserver": 200,
    }
    assert answers["Not a place!"].json()["error"]["message"] == (
        "[telemetry] send_to is 'Not a place!': use off, this-pc or a place name"
    )
    assert answers["usb"].json()["error"]["message"] == (
        "[telemetry] send_to is 'usb', which only keeps copies; use off, this-pc or a machine "
        "that runs work, such as your server"
    )
    assert answers["banana"].json()["error"]["message"] == (
        "[telemetry] send_to is 'banana', which is not one of your machines; use off, this-pc "
        "or a machine that runs work, such as your server"
    )
    stored = tomllib.loads((home / "settings.toml").read_text(encoding="utf-8"))
    assert stored["telemetry"] == {"send_to": "myserver"}


def test_the_read_names_every_default_and_openobserves_sizes_are_checked(
    rest: tuple[TestClient, dict[str, str], Path],
) -> None:
    client, bearer, home = rest
    with client:
        before = client.get("/api/settings/telemetry", headers=bearer).json()
        too_few = client.put(
            "/api/settings/telemetry", headers=bearer, json={"openobserve": {"keep_days": 2}}
        )
        kept = client.put(
            "/api/settings/telemetry", headers=bearer, json={"openobserve": {"cache_gb": 4}}
        )
        after = client.get("/api/settings/telemetry", headers=bearer).json()
    assert before == {"send_to": "off", "openobserve": {"cache_gb": 1, "keep_days": 30}}
    assert too_few.status_code == 400
    assert kept.status_code == 200
    assert after == {"send_to": "off", "openobserve": {"cache_gb": 4, "keep_days": 30}}
    stored = tomllib.loads((home / "settings.toml").read_text(encoding="utf-8"))
    assert stored["telemetry"] == {"openobserve": {"cache_gb": 4}}, "the defaults are never stored"
