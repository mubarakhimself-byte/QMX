"""Installed QMA startup resources and operator-owned bootstrap configuration."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from qma.daemon.plugins.packs import default_plugins_root


def test_default_pack_root_is_installed_and_has_mandatory_manifests() -> None:
    root = default_plugins_root()
    mandatory = {
        "research-corpus",
        "analysis-backtest",
        "dev-factory",
        "trading-readonly",
        "pm-coordination",
    }
    assert {p.parent.name for p in root.glob("*/manifest.json")} >= mandatory
    source_root = Path(__file__).resolve().parents[3] / "plugins"
    for pack_id in mandatory:
        for relative in ("manifest.json", "daemon/plugin.py"):
            assert (root / pack_id / relative).read_bytes() == (
                source_root / pack_id / relative
            ).read_bytes()


def test_entrypoint_reports_missing_operator_configuration(tmp_path: Path) -> None:
    env = dict(os.environ)
    env.update(
        QMA_DAEMON_ROOT=str(tmp_path / "daemon"),
        QMA_DAEMON_BIND_PORT="0",
        PYTHONDONTWRITEBYTECODE="1",
    )
    env.pop("QMA_DAEMON_CONFIG", None)
    result = subprocess.run(
        [sys.executable, "-m", "qma.daemon"],
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 2
    assert "operator-config.json" in result.stderr
    assert "daemon.composed" not in result.stderr


def test_entrypoint_reads_operator_owned_research_root(tmp_path: Path) -> None:
    daemon_root = tmp_path / "daemon"
    corpus_root = tmp_path / "operator-seed"
    corpus_root.mkdir()
    daemon_root.mkdir()
    config = daemon_root / "operator-config.json"
    config.write_text(
        json.dumps({"research_corpus_root_path": str(corpus_root)}),
        encoding="utf-8",
    )
    # Parsing is independently testable without starting a long-running listener.
    from qma.daemon.bootstrap_config import load_plugin_load_configs

    assert load_plugin_load_configs(daemon_root) == {
        "research-corpus": {"root_path": str(corpus_root)}
    }
