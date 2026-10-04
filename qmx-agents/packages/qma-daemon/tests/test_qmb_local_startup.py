"""Operator-configured local QMB declaration survives normal composition/restart."""

from __future__ import annotations

import json
from pathlib import Path

from qma.daemon.process import DaemonProcess
from qmf.core import is_ok, is_refusal


def test_local_qmb_environment_bound_on_each_start(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (tmp_path / "operator-config.json").write_text(
        json.dumps(
            {
                "research_corpus_root_path": str(corpus),
                "qmb_local_environment": {"provider_ref": "operator-local-qmb", "network": "none"},
            }
        ),
        encoding="utf-8",
    )
    for boot in ("first", "restart"):
        result = DaemonProcess.compose(
            tmp_path,
            machine="local-qmb-test",
            boot_epoch_id=boot,
            plugin_load_configs={"research-corpus": {"root_path": str(corpus)}},
        )
        assert is_ok(result), result
        process = result.value
        try:
            declaration = process.execution_environments.declaration("local")
            assert declaration is not None
            assert declaration.provider_ref == "operator-local-qmb"
            assert declaration.network.value == "none"
            assert process.backtesting.environments is process.execution_environments
            assert process.compute_router.environments is process.execution_environments
            assert process.execution_environments.kinds() == frozenset({"local"})
        finally:
            process.close()


def test_invalid_local_posture_refuses_startup_before_binding(tmp_path: Path) -> None:
    (tmp_path / "operator-config.json").write_text(
        json.dumps({"qmb_local_environment": {"provider_ref": "local", "network": "all"}}),
        encoding="utf-8",
    )
    result = DaemonProcess.compose(tmp_path, machine="test", boot_epoch_id="invalid")
    assert is_refusal(result), result
    assert "qmb_local_environment" in str(result.context)
