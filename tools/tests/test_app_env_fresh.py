"""A trading node env reinstalled by the supervisor serves the source it was installed from.

The supervisor installs a first-party app with ``uv sync --no-editable`` from the app's lock, so
QMX's own libraries arrive as wheels built from their path sources. uv reuses such a wheel until
one of the library's cache keys changes. Those keys see file times, never the file list, so a
deleted module would stay in the wheel; the supervisor reinstalls each library whose source files
changed since it built the env.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
APP = Path("qmx-agents/apps/trading-node")
MODULES = (
    "qmb",
    "qmf.core",
    "qmf.data",
    "qmf.indicators",
    "qmf.readings",
    "qmf.registry",
    "qmf.risk",
    "qmf.structure",
    "qmf.venue",
    "qml",
    "qmn",
)
COPIED = shutil.ignore_patterns("__pycache__", ".venv", ".pytest_cache", ".ruff_cache")
INSTALL = """
import sys
from pathlib import Path

from qmx_apps.supervisor import Supervisor

owner = Supervisor(Path(sys.argv[1]))
try:
    installed = owner.install(Path(sys.argv[2]), trust="first_party")
    print(owner.python(str(installed["definition_hash"])))
finally:
    owner.close()
"""


def _libraries() -> dict[Path, str]:
    """Each path source of the app's lock, and the module its wheel installs."""
    lock = tomllib.loads((ROOT / APP / "uv.lock").read_text(encoding="utf-8"))
    folders = [
        (ROOT / APP / package["source"]["editable"]).resolve().relative_to(ROOT)
        for package in lock["package"]
        if "editable" in package["source"]
    ]
    return {
        folder: tomllib.loads((ROOT / folder / "pyproject.toml").read_text(encoding="utf-8"))[
            "tool"
        ]["uv"]["build-backend"]["module-name"]
        for folder in folders
    }


def _copy_tree(copy: Path, libraries: dict[Path, str]) -> None:
    for library in libraries:
        target = copy / library
        target.mkdir(parents=True)
        for name in ("pyproject.toml", "README.md"):
            if (ROOT / library / name).exists():
                shutil.copy2(ROOT / library / name, target / name)
        shutil.copytree(ROOT / library / "src", target / "src", ignore=COPIED)
    # The libraries' `workspace = true` sources resolve against the root workspace.
    shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
    shutil.copytree(ROOT / APP, copy / APP, ignore=COPIED)


def _mark(copy: Path, libraries: dict[Path, str], value: str) -> None:
    for library, module in libraries.items():
        init = copy / library / "src" / Path(*module.split(".")) / "__init__.py"
        text = init.read_text(encoding="utf-8").split("\nC26_MARKER = ")[0]
        init.write_text(f"{text}\nC26_MARKER = {value!r}\n", encoding="utf-8")


def _install(copy: Path, home: Path) -> Path:
    """Install the copied app through the real supervisor; return the env's interpreter."""
    uv = shutil.which("uv")
    assert uv is not None, "uv is on PATH, as the supervisor requires"
    environment = {name: value for name, value in os.environ.items() if name != "VIRTUAL_ENV"}
    result = subprocess.run(
        [
            uv,
            "run",
            "--project",
            str(ROOT / "qmx-agents"),
            "--no-sync",
            "python",
            "-c",
            INSTALL,
            str(home),
            str(copy / APP),
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return Path(result.stdout.strip().splitlines()[-1])


def _ask(python: Path, script: str) -> object:
    result = subprocess.run(
        [str(python), "-I", "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _served(python: Path) -> object:
    return _ask(
        python,
        "import importlib, json; print(json.dumps({m: importlib.import_module(m).C26_MARKER "
        f"for m in {MODULES!r}}}))",
    )


def _importable(python: Path, module: str) -> object:
    return _ask(
        python,
        f"import importlib.util, json; print(json.dumps(bool(importlib.util.find_spec({module!r}))))",
    )


def _records(python: Path) -> dict[str, int]:
    env = python.parents[1]
    found = [
        *env.glob("Lib/site-packages/*.dist-info/RECORD"),
        *env.glob("lib/python*/site-packages/*.dist-info/RECORD"),
    ]
    return {path.parent.name: path.stat().st_mtime_ns for path in found}


def test_a_reinstall_serves_edits_and_deletions_without_touching_pyproject(
    tmp_path: Path,
) -> None:
    copy, home = tmp_path / "repo", tmp_path / "home"
    libraries = _libraries()
    assert tuple(sorted(libraries.values())) == MODULES
    _copy_tree(copy, libraries)
    fixture = copy / "qmn/src/qmn/c26b_fixture.py"
    fixture.write_text("HELD = True\n", encoding="utf-8")
    _mark(copy, libraries, "first")
    python = _install(copy, home)
    assert _served(python) == dict.fromkeys(MODULES, "first")
    assert _importable(python, "qmn.c26b_fixture") is True
    pyprojects = [(copy / library / "pyproject.toml").stat().st_mtime_ns for library in libraries]

    _mark(copy, libraries, "second")
    assert _install(copy, home) == python
    assert _served(python) == dict.fromkeys(MODULES, "second"), "an edit reached every library"

    fixture.unlink()
    _install(copy, home)
    assert _importable(python, "qmn.c26b_fixture") is False, "a deleted module left the env"

    installed = _records(python)
    assert len(installed) > len(MODULES)
    _install(copy, home)
    assert _records(python) == installed, "an unchanged source reinstalls nothing"
    assert [(copy / lib / "pyproject.toml").stat().st_mtime_ns for lib in libraries] == pyprojects
