"""No settings write replaces a section (design 06 I14): the REST route merges what it is sent and
removes only what it names, an in-process change can still remove a key, and the read's defaults
are never stored."""

from __future__ import annotations

import secrets
import tomllib
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from qmx_control.models import Document
from qmx_control.server import create_app
from qmx_control.service import ControlError, ControlService

ENGINE = cast("Any", "engine")
HIS = """[engine]
host_name = "pc-1"
disk.floor_gb = 3

[engine.scheduler]
tick = 5
grace = 900

[engine.placement.usb]
id = "01J-USB"
via = "folder"
can = ["keep"]
path = 'E:\\'

[backup]
repository = "git@example.invalid:qmx.git"
remote = "fixture"
bucket = "qmx"

[backup.place.01J-USB]
every = "1d"

[remote]
default_target = "vps"
"""


def stored(home: Path) -> dict[str, Any]:
    return tomllib.loads((home / "settings.toml").read_text(encoding="utf-8"))


@pytest.fixture
def service(tmp_path: Path) -> ControlService:
    home = tmp_path / "QMX" / "data"
    home.mkdir(parents=True)
    (home / "settings.toml").write_text(HIS, encoding="utf-8")
    return ControlService(home, secret_getter=lambda _service, _name: None)


def test_a_put_of_one_key_keeps_every_other_and_remove_drops_only_what_it_names(
    service: ControlService,
) -> None:
    token = secrets.token_urlsafe(32)
    bearer = {"Authorization": f"Bearer {token}"}
    with TestClient(create_app(service, token)) as rest:
        one = rest.put("/api/settings/engine", headers=bearer, json={"scheduler": {"tick": 30}})
        assert one.status_code == 200, one.text
        engine = stored(service.home)["engine"]
        removed = rest.put(
            "/api/settings/engine", headers=bearer, json={"remove": ["placement.usb"]}
        )
        assert removed.status_code == 200, removed.text
        remote = rest.put("/api/settings/remote", headers=bearer, json={"x": 1})
        weekly = rest.post("/api/backup/weekly", headers=bearer)

    assert engine == {
        "host_name": "pc-1",
        "disk": {"floor_gb": 3},
        "scheduler": {"tick": 30, "grace": 900},
        "placement": {"usb": {"id": "01J-USB", "via": "folder", "can": ["keep"], "path": "E:\\"}},
    }
    after = stored(service.home)
    assert after["engine"] == {
        "host_name": "pc-1",
        "disk": {"floor_gb": 3},
        "scheduler": {"tick": 30, "grace": 900},
    }
    assert after["remote"] == {"default_target": "vps"}
    assert 400 <= remote.status_code < 500
    assert weekly.status_code == 404


def test_an_in_process_change_that_drops_a_key_removes_it_and_old_keys_survive(
    service: ControlService,
) -> None:
    def dropped(section: Document) -> Document:
        return {k: v for k, v in section.items() if k != "place"}

    service.settings_update("backup", dropped)

    assert stored(service.home)["backup"] == {
        "repository": "git@example.invalid:qmx.git",
        "remote": "fixture",
        "bucket": "qmx",
    }


def test_the_read_names_every_default_and_a_write_after_it_stores_none(
    service: ControlService,
) -> None:
    read = service.settings_get("backup")
    assert read["place"] == {
        "pc": {
            "on": True,
            "save": ["recipe", "content", "result", "prices"],
            "every": "1h",
            "at": "03:00",
            "keep": {"hours": 48, "days": 7},
        },
        "01J-USB": {
            "on": True,
            "save": ["recipe", "content", "result", "prices"],
            "every": "1d",
            "keep": {"days": 14, "weeks": 8, "months": 12},
            "at": "03:00",
            "floor": "auto",
        },
    }

    def switched_off(section: Document) -> Document:
        return {**section, "on": False}

    service.settings_update("backup", switched_off)

    assert stored(service.home)["backup"] == {
        "repository": "git@example.invalid:qmx.git",
        "remote": "fixture",
        "bucket": "qmx",
        "place": {"01J-USB": {"every": "1d"}},
        "on": False,
    }


def test_a_policy_whose_storage_row_is_gone_is_dropped_at_the_next_in_process_write(
    service: ControlService,
) -> None:
    def gone(section: Document) -> Document:
        placement = cast("dict[str, Any]", section["placement"])
        return {**section, "placement": {k: v for k, v in placement.items() if k != "usb"}}

    service.settings_update(ENGINE, gone)
    service.settings_update("backup", lambda section: {**section, "leave_out": ["exports/**"]})

    assert "place" not in stored(service.home)["backup"]


@pytest.mark.parametrize("name", ["api_key", "token", "Password", "client-key", "secret", "key"])
def test_a_key_named_like_a_secret_is_refused_as_before(service: ControlService, name: str) -> None:
    with pytest.raises(ControlError) as refused:
        service.settings_put("providers", {"kimi": {name: "planted"}})
    assert refused.value.code == "secret_ref_required"
