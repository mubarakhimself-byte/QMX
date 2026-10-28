"""Settings `[backup]`: the sync policies are checked by the plan's own reader before they are
saved, and the read names every default (design 06 section 15)."""

from __future__ import annotations

import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qmx_control.models import Document
from qmx_control.server import create_app
from qmx_control.service import ControlError, ControlService


def _service(tmp_path: Path) -> ControlService:
    return ControlService(tmp_path / "QMX" / "data", secret_getter=lambda _service, _name: None)


def test_this_pcs_policy_saves_through_the_route_and_the_read_fills_every_default(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    token = secrets.token_urlsafe(32)
    values: Document = {"place": {"pc": {"every": "2h", "keep": {"hours": 4}}}}
    bearer = {"Authorization": f"Bearer {token}"}
    with TestClient(create_app(service, token)) as rest:
        saved = rest.put("/api/settings/backup", headers=bearer, json=values)
        assert saved.status_code == 200, saved.text
        read = rest.get("/api/settings/backup", headers=bearer).json()
    assert read["place"]["pc"] == {
        "on": True,
        "save": ["recipe", "content", "result", "prices"],
        "every": "2h",
        "keep": {"hours": 4},
    }
    assert (read["on"], read["leave_out"], read["upkeep"]["drill_sample"]) == (True, [], 200)
    assert (tmp_path / "QMX" / "data" / "settings.toml").read_text(encoding="utf-8") == (
        '[backup.place.pc]\nevery = "2h"\n\n[backup.place.pc.keep]\nhours = 4\n'
    )


def test_a_bad_policy_is_refused_by_name_and_nothing_is_saved(tmp_path: Path) -> None:
    service = _service(tmp_path)
    with pytest.raises(ControlError) as refused:
        service.settings_put("backup", {"place": {"pc": {"every": "soon"}}})
    assert (refused.value.code, refused.value.status, str(refused.value)) == (
        "invalid_backup_settings",
        400,
        "[backup.place.pc]: every is a span of an hour or more, such as 1h, 1d or 1w",
    )
    assert not (tmp_path / "QMX" / "data" / "settings.toml").exists()


def test_a_key_neither_the_plan_nor_an_older_release_knows_is_refused_by_name(
    tmp_path: Path,
) -> None:
    with pytest.raises(ControlError, match="tape") as refused:
        _service(tmp_path).settings_put("backup", {"tape": "E:"})
    assert refused.value.code == "invalid_backup_settings"


def test_the_old_volume_keys_are_kept_as_written_and_the_app_backup_routes_are_gone(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    token = secrets.token_urlsafe(32)
    bearer = {"Authorization": f"Bearer {token}"}
    old: Document = {"remote": "fixture", "bucket": "qmx", "enabled": False, "repository": "r"}
    with TestClient(create_app(service, token)) as rest:
        saved = rest.put("/api/settings/backup", headers=bearer, json=old)
        backup = rest.post("/api/apps/demo/backup", headers=bearer)
        restore = rest.post("/api/apps/demo/restore", headers=bearer, params={"snapshot_id": "s"})
    assert saved.status_code == 200, saved.text
    assert (tmp_path / "QMX" / "data" / "settings.toml").read_text(encoding="utf-8") == (
        '[backup]\nremote = "fixture"\nbucket = "qmx"\nenabled = false\nrepository = "r"\n'
    )
    assert (backup.status_code, restore.status_code) == (404, 404)
