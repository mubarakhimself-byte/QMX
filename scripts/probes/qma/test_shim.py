# ruff: noqa: S101
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import tomllib
from p_shim import stage


def test_the_staged_launcher_package_imports_on_its_own_and_lists_every_module(
    tmp_path: Path,
) -> None:
    stage(tmp_path)
    shipped = sorted(p.stem for p in tmp_path.glob("*.py"))
    pyproject = tomllib.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    assert sorted(pyproject["tool"]["setuptools"]["py-modules"]) == shipped
    done = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            f"import sys; sys.path.insert(0, {str(tmp_path)!r}); "
            "import p_shim; print(p_shim.shim_main.__name__)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (done.returncode, done.stdout.strip(), done.stderr) == (0, "shim_main", "")
