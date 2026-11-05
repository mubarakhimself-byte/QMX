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
    "qmf.calendar_cme",
    "qmf.calendar_crypto247",
    "qmf.calendar_forex",
    "qmf.calendar_indices",
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
MIS = Path("qmx-agents/apps/mis")
HOST_START = """
import json
import sys
from pathlib import Path

import qmx_host.connect
from qmx_apps.supervisor import Supervisor
from qmx_host import first_start

home, folder = Path(sys.argv[1]), Path(sys.argv[2])
home.mkdir(parents=True, exist_ok=True)
(home / first_start.FIRST_PARTY).write_text(json.dumps({"enable": ["mis"]}), "utf-8")
first_start.APP_FOLDERS = {"mis": folder}
owner = Supervisor(home)
try:
    assert first_start.enable_first_party(home, owner) == ["mis"]
    print(owner.python(str(owner.status("mis")["definition_hash"])))
finally:
    owner.close()
"""


def _libraries(app: Path = APP) -> dict[Path, str]:
    """Each path source of the app's lock, and the module its wheel installs."""
    lock = tomllib.loads((ROOT / app / "uv.lock").read_text(encoding="utf-8"))
    folders = [
        (ROOT / app / package["source"]["editable"]).resolve().relative_to(ROOT)
        for package in lock["package"]
        if "editable" in package["source"]
    ]
    return {
        folder: tomllib.loads((ROOT / folder / "pyproject.toml").read_text(encoding="utf-8"))[
            "tool"
        ]["uv"]["build-backend"]["module-name"]
        for folder in folders
    }


def _copy_tree(copy: Path, libraries: dict[Path, str], app: Path = APP) -> None:
    for library in libraries:
        target = copy / library
        target.mkdir(parents=True)
        for name in ("pyproject.toml", "README.md"):
            if (ROOT / library / name).exists():
                shutil.copy2(ROOT / library / name, target / name)
        shutil.copytree(ROOT / library / "src", target / "src", ignore=COPIED)
    # The libraries' `workspace = true` sources resolve against the root workspace.
    shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
    shutil.copytree(ROOT / app, copy / app, ignore=COPIED)


def _mark(copy: Path, libraries: dict[Path, str], value: str) -> None:
    for library, module in libraries.items():
        init = copy / library / "src" / Path(*module.split(".")) / "__init__.py"
        text = init.read_text(encoding="utf-8").split("\nC26_MARKER = ")[0]
        init.write_text(f"{text}\nC26_MARKER = {value!r}\n", encoding="utf-8")


def _run(script: str, home: Path, folder: Path) -> Path:
    """Run `script` in the agents env on a throwaway home; return the env interpreter it printed."""
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
            script,
            str(home),
            str(folder),
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return Path(result.stdout.strip().splitlines()[-1])


def _install(copy: Path, home: Path) -> Path:
    """Install the copied app through the real supervisor; return the env's interpreter."""
    return _run(INSTALL, home, copy / APP)


def _ask(python: Path, script: str) -> object:
    result = subprocess.run(
        [str(python), "-I", "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _served(python: Path, modules: tuple[str, ...] = MODULES) -> object:
    return _ask(
        python,
        "import importlib, json; print(json.dumps({m: importlib.import_module(m).C26_MARKER "
        f"for m in {modules!r}}}))",
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


def test_a_changed_library_reaches_the_app_env_at_the_next_start(tmp_path: Path) -> None:
    copy, home = tmp_path / "repo", tmp_path / "QMX" / "data"
    libraries = _libraries(MIS)
    modules = tuple(sorted(libraries.values()))
    _copy_tree(copy, libraries, MIS)
    _mark(copy, libraries, "shipped")
    python = _run(HOST_START, home, copy / MIS)
    assert _served(python, modules) == dict.fromkeys(modules, "shipped")

    _mark(copy, libraries, "repaired")
    assert _run(HOST_START, home, copy / MIS) == python, "a library repair keeps the app's hash"
    assert _served(python, modules) == dict.fromkeys(modules, "repaired")

    built = _records(python)
    _run(HOST_START, home, copy / MIS)
    assert _records(python) == built, "a start with nothing repaired builds nothing"
