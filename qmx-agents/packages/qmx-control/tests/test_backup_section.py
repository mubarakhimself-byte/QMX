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


def test_the_volume_keys_save_as_before_and_only_they_reach_the_volume_model(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    values: Document = {
        "remote": "fixture",
        "bucket": "qmx",
        "enabled": False,
        "repository": "git@example.invalid:qmx.git",
        "quick_undo": {"hours": 48},
    }
    assert service.settings_put("backup", values) == values
    volumes = service._backup_settings()  # pyright: ignore[reportPrivateUsage]
    assert volumes is not None
    assert (volumes.remote, volumes.bucket, volumes.enabled) == ("fixture", "qmx", False)


def test_a_plan_without_volume_keys_gives_the_volumes_nothing_to_run(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.settings_put("backup", {"quick_undo": {"hours": 48, "days": 7}})
    assert service._backup_settings() is None  # pyright: ignore[reportPrivateUsage]
