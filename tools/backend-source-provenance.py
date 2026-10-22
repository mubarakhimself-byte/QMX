"""Prove local parent and stripped-PYTHONPATH child use the selected source tree."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

MODULES = (
    "qmf.core",
    "qmf.data.store",
    "qml",
    "qmb.host.research_store",
    "qmn.host.configured_runtime",
)


def sources() -> dict[str, str]:
    result: dict[str, str] = {}
    for name in MODULES:
        path = importlib.import_module(name).__file__
        if path is None:
            raise RuntimeError(f"{name} has no inspectable source file")
        result[name] = path
    return result


if __name__ == "__main__":
    if sys.argv[1:] == ["--child"]:
        print(json.dumps(sources()))
    else:
        root, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
        parent = sources()
        child = json.loads(
            subprocess.check_output(
                [sys.executable, str(Path(__file__).resolve()), "--child"],
                text=True,
                env={
                    "SYSTEMROOT": os.environ["SYSTEMROOT"],
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONUTF8": "1",
                },
            )
        )
        if parent != child or any(
            not Path(path).resolve().is_relative_to(root) for path in parent.values()
        ):
            raise RuntimeError("foreign source tree or stripped-child source mismatch")
        output.write_text(
            json.dumps(
                {"python": sys.executable, "parent": parent, "child_without_pythonpath": child},
                indent=2,
            )
            + "\n"
        )
