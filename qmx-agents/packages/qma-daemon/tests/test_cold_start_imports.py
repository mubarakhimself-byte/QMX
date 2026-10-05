"""Unconfigured daemon composition must not import opt-in agent SDKs."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_unconfigured_cold_composition_has_no_agent_sdk_imports(tmp_path: Path) -> None:
    # A subprocess prevents other SDK tests from warming sys.modules first.
    script = """
import importlib.abc
import json
import sys
from pathlib import Path

class RefuseOptionalSDK(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"langchain", "langchain_core", "langgraph", "deepagents"}:
            raise AssertionError("unconfigured startup imported " + fullname)
        return None

sys.meta_path.insert(0, RefuseOptionalSDK())
from qma.daemon.process import DaemonProcess
from qma.daemon.bootstrap_config import load_plugin_load_configs
from qmf.core import is_ok
root = Path(sys.argv[1])
corpus = root / "corpus"
corpus.mkdir()
(root / "operator-config.json").write_text(json.dumps({"research_corpus_root_path": str(corpus)}))
result = DaemonProcess.compose(
    root, machine="cold-test", boot_epoch_id="cold-test", bind_port=0,
    plugin_load_configs=load_plugin_load_configs(root),
)
assert is_ok(result), result
result.value.close()
assert not (root / ".daemon_writer").exists()
"""
    env = dict(os.environ)
    for name in ("QMA_DAEMON_CONFIG", "QMA_DAEMON_PLUGINS_ROOT", "QMA_DAEMON_RECOVER_CONTROL"):
        env.pop(name, None)
    child = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script, str(tmp_path)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert child.returncode == 0, child.stdout + child.stderr
