"""The three downloaders keep their months in the host door's own folder on This PC unless his
`[data]` settings name another (design 62 E2, ruling 140)."""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
from typing import Any

import pytest

from qmx_engine.templates.catalog import PACK

DOWNLOADERS = ("download-dukascopy", "download-binance", "download-ccxt")


def script(name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """The script's functions, loaded through its own dry-run path so nothing is fetched."""
    monkeypatch.setenv("QMX_WORK", str(tmp_path / "work"))
    monkeypatch.setattr("sys.stdin", io.StringIO('{"in": {"dry_run": true}}'))
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), PACK / name / "scripts" / "download.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with pytest.raises(SystemExit):
        spec.loader.exec_module(module)
    return vars(module)


@pytest.mark.parametrize("name", DOWNLOADERS)
def test_a_downloader_with_no_data_settings_writes_under_market_on_this_pc(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    door_place = script(name, tmp_path, monkeypatch)["door_place"]
    home = tmp_path / "home"

    root, placement = door_place(home, {})
    named = door_place(home, {"root": str(tmp_path / "ticks"), "placement": "node"})

    assert (root, str(placement)) == (home / "market", "pc")
    assert (named[0], str(named[1])) == (tmp_path / "ticks", "node")
