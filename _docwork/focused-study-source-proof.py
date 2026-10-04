"""Record source identity in the parent and a child without PYTHONPATH overrides."""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

MODULES = (
    "qmb.host.operator_study_replay",
    "qmb.host.delegated_cli",
    "qma.daemon.process",
    "qma.daemon.backtest.cli",
    "qmf.core",
    "qmf.data",
    "qml",
)


def imports() -> dict[str, str]:
    return {
        name: str(Path(importlib.import_module(name).__file__).resolve())
        for name in MODULES
    }


if "--child" in sys.argv:
    print(json.dumps(imports(), sort_keys=True))
    raise SystemExit(0)

repo = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1]).resolve()
env = dict(os.environ)
env.pop("PYTHONPATH", None)
env.pop("PYTHONHOME", None)
env["PYTHONDONTWRITEBYTECODE"] = "1"
child = json.loads(
    subprocess.check_output(
        [sys.executable, str(Path(__file__).resolve()), "--child"],
        env=env,
        cwd=output.parent,
        text=True,
        timeout=60,
    )
)
parent = imports()
assert parent == child, (parent, child)
assert all(Path(path).is_relative_to(repo) for path in parent.values()), parent
changed = subprocess.check_output(
    ["git", "-c", f"safe.directory={repo.as_posix()}", "diff", "--name-only",
     "5acb4a6483567976be771880d57b30482da4ec6b", "--", "*.py"],
    cwd=repo,
    text=True,
).splitlines()
changed += [
    "qmb/src/qmb/host/delegated_cli.py",
    "qmb/src/qmb/host/operator_study_replay.py",
    "qmb/tests/operator_study_fixture_support.py",
    "qmb/tests/test_operator_study_cli.py",
    "qa/integration/test_qma_authenticated_study.py",
]
files = {
    relative: hashlib.sha256((repo / relative).read_bytes()).hexdigest()
    for relative in sorted(set(changed))
    if not relative.startswith("_docwork/")
}
record = {
    "base": "5acb4a6483567976be771880d57b30482da4ec6b",
    "checkout": str(repo),
    "interpreter": sys.executable,
    "python_version": sys.version,
    "parent_imports": parent,
    "stripped_child_imports": child,
    "tested_python_files_sha256": files,
    "distributions": {
        name: importlib.metadata.version(name)
        for name in ("qmb", "optuna", "langchain", "langgraph", "deepagents")
    },
    "dependency_setup": "Isolated interpreter; borrowed pinned third-party distributions, not fresh frozen install",
}
output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(f"Verified {len(parent)} parent/stripped-child imports and {len(files)} file hashes: {output}")
