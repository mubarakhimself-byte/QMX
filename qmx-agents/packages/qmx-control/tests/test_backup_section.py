"""Settings `[backup]`: his backup plan and the mini apps' volume keys share one section; the plan
is checked by its own reader and only the volume keys go to the volumes' model (B3)."""

from __future__ import annotations

import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qmx_control.models import Document
from qmx_control.server import create_app
from qmx_control.service import ControlError, ControlService


def _service(tmp_path: Path) -> ControlService:
    return ControlService(tmp_path / "QMX" / "data")


def test_a_quick_undo_table_and_a_folder_target_save_through_the_route(tmp_path: Path) -> None:
    service = _service(tmp_path)
    token = secrets.token_urlsafe(32)
    values: Document = {
        "quick_undo": {"hours": 24, "days": 3},
        "targets": [{"id": "usb", "kind": "folder", "path": str(tmp_path / "usb"), "on": True}],
    }
    with TestClient(create_app(service, token)) as rest:
        saved = rest.put(
            "/api/settings/backup", headers={"Authorization": f"Bearer {token}"}, json=values
        )
        assert saved.status_code == 200, saved.text
        assert rest.get(
            "/api/settings/backup", headers={"Authorization": f"Bearer {token}"}
        ).json() == values


def test_a_target_of_an_unknown_kind_is_refused_by_name_and_nothing_is_saved(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    row = {"id": "usb", "kind": "tape", "path": str(tmp_path / "usb")}
    with pytest.raises(ControlError) as refused:
        service.settings_put("backup", {"targets": [row]})
    assert (refused.value.code, refused.value.status, str(refused.value)) == (
        "invalid_backup_settings",
        400,
        "backup place 'usb': the kind 'tape' is not one QMX knows; use folder",
    )
    assert service.settings_get("backup") == {}


def test_a_key_neither_the_plan_nor_the_volumes_know_is_refused_by_name(tmp_path: Path) -> None:
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
