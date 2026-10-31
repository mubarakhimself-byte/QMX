"""Settings `[data]`: the holdout is off unless he turns it on (ruling 137)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qmx_control.models import Document
from qmx_control.service import ControlError, ControlService


def test_a_holdout_round_trips_through_settings(tmp_path: Path) -> None:
    values: Document = {"holdout": True, "holdout_boundary": "2025-01", "holdout_months": 6}
    assert ControlService(tmp_path).settings_put("data", values) == values
    assert ControlService(tmp_path).settings_get("data") == values


def test_a_stored_month_without_the_switch_reads_as_off(tmp_path: Path) -> None:
    settings = tmp_path / "settings.toml"
    settings.write_text('[data]\nholdout_boundary = "2025-01"\n', encoding="utf-8")
    assert ControlService(tmp_path).settings_get("data") == {
        "holdout": False,
        "holdout_boundary": "2025-01",
    }
    settings.write_text("[data]\nseal_boundary_ns = 1735689600000000000\n", encoding="utf-8")
    assert ControlService(tmp_path).settings_get("data") == {
        "holdout": True,
        "seal_boundary_ns": 1_735_689_600_000_000_000,
    }


@pytest.mark.parametrize("month", ["0000-01", "1969-12"])
def test_a_month_before_1970_is_refused_by_name(tmp_path: Path, month: str) -> None:
    service = ControlService(tmp_path)
    with pytest.raises(ControlError, match="holdout_boundary") as refused:
        service.settings_put("data", {"holdout": True, "holdout_boundary": month})
    assert refused.value.code == "invalid_settings"
    assert service.settings_get("data") == {"holdout": False}
