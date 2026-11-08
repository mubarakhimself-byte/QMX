"""An app env built from the trading node's lock serves a source edit after a plain reinstall.

The supervisor installs a first-party app with ``uv sync --no-editable`` from the app's lock, so
QMX's own libraries arrive as wheels built from their path sources. uv reuses such a wheel until
one of the library's cache keys changes, and by default the only key is ``pyproject.toml``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
APP = Path("qmx-agents/apps/trading-node")
EDITED = ("qmn", "qmb", "qml")
# The variables qmx_apps.supervisor.Supervisor._install_environment passes to uv.
KEPT = {
    "PATH",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "USERPROFILE",
    "HOME",
    "LOCALAPPDATA",
    "APPDATA",
    "TEMP",
    "TMP",
    "UV_CACHE_DIR",
    "UV_PYTHON_INSTALL_DIR",
}


def _libraries() -> list[Path]:
    lock = tomllib.loads((ROOT / APP / "uv.lock").read_text(encoding="utf-8"))
    return [
        (ROOT / APP / package["source"]["editable"]).resolve().relative_to(ROOT)
        for package in lock["package"]
        if "editable" in package["source"]
    ]


def _copy_tree(copy: Path) -> None:
    for library in _libraries():
        target = copy / library
        target.mkdir(parents=True)
        for name in ("pyproject.toml", "README.md"):
            if (ROOT / library / name).exists():
                shutil.copy2(ROOT / library / name, target / name)
        shutil.copytree(
            ROOT / library / "src", target / "src", ignore=shutil.ignore_patterns("__pycache__")
        )
    # The libraries' `workspace = true` sources resolve against the root workspace.
    shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
    (copy / APP).mkdir(parents=True)
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copy2(ROOT / APP / name, copy / APP / name)


def _mark(copy: Path, value: str) -> None:
    for library in EDITED:
        init = copy / library / "src" / library / "__init__.py"
        text = init.read_text(encoding="utf-8").split("\nC26_MARKER = ")[0]
        init.write_text(f"{text}\nC26_MARKER = {value!r}\n", encoding="utf-8")


def _install(copy: Path, env: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None, "uv is on PATH, as the supervisor requires"
    environment = {name: value for name, value in os.environ.items() if name.upper() in KEPT}
    environment["UV_PROJECT_ENVIRONMENT"] = str(env)
    result = subprocess.run(
        [
            uv,
            "sync",
            "--project",
            str(copy / APP),
            "--locked",
            "--no-dev",
            "--no-editable",
            "--no-install-project",
            "--compile-bytecode",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _served(copy: Path, env: Path) -> str:
    python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    result = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import qmn, qmb, qml; print(qmn.C26_MARKER, qmb.C26_MARKER, qml.C26_MARKER)",
        ],
        cwd=copy,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_a_reinstall_serves_a_source_edit_without_touching_pyproject(tmp_path: Path) -> None:
    copy = tmp_path / "repo"
    env = tmp_path / "env"
    _copy_tree(copy)
    pyprojects = [(copy / library / "pyproject.toml").stat().st_mtime_ns for library in EDITED]

    _mark(copy, "first")
    _install(copy, env)
    assert _served(copy, env) == "first first first"

    _mark(copy, "second")
    _install(copy, env)

    assert [(copy / lib / "pyproject.toml").stat().st_mtime_ns for lib in EDITED] == pyprojects
    assert _served(copy, env) == "second second second"
