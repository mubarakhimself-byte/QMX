"""A road reader waits for whoever holds the road for a moment, and is refused past the bound."""

from __future__ import annotations

import importlib
import threading
from pathlib import Path

import pytest
from qmx_apps.errors import AppError
from qmx_apps.volume import Volume, VolumeLease

road = importlib.import_module("qmx_apps.road.history")


def test_a_reader_waits_for_a_backup_that_holds_the_road_for_a_moment(tmp_path: Path) -> None:
    Volume(tmp_path, "app").create(agents=False)
    held = VolumeLease(tmp_path / "road-locks", "app")
    threading.Timer(0.5, held.close).start()

    with road.history(tmp_path, "app") as state:
        assert state.head is None


def test_a_reader_is_refused_past_the_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(road, "ROAD_WAIT_S", 0.2)
    Volume(tmp_path, "app").create(agents=False)
    held = VolumeLease(tmp_path / "road-locks", "app")
    try:
        with pytest.raises(AppError) as refused, road.history(tmp_path, "app"):
            pass
    finally:
        held.close()
    assert refused.value.code == "volume_busy"
