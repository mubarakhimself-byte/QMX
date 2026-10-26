"""Every command line program finds his QMX folder through `resolve`, run as he would run it."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from qmx_home import NoQmxFolder, pointer_file, resolve

REFUSAL = "no QMX folder found: start QMX once, or pass --home"
PROGRAMS = {
    "host": (["-m", "qmx_host", "status"], 2),
    "console": (["-m", "qma.console"], 2),
    "engine": (["-m", "qmx_engine", "templates", "list"], 1),
    "node pair": (["-c", "from qmx_control.node import main; main()", "node", "pair"], 2),
    "node setup": (
        ["-c", "from qmx_control.node import main; main()", "node", "setup", "qmx-server"],
        2,
    ),
    "broker": (["-c", "from qmx_broker.server import main; main()"], 1),
    "tools": (["-c", "from qmx_tools.servers import data; data()"], 1),
}


@pytest.fixture
def scratch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """A scratch profile with no QMX folder in it, as the environment of a child program."""
    user = tmp_path / "profile"
    folders = {
        "USERPROFILE": user,
        "HOME": user,
        "APPDATA": user / "AppData" / "Roaming",
        "LOCALAPPDATA": user / "AppData" / "Local",
        "XDG_CONFIG_HOME": user / ".config",
    }
    for name, folder in folders.items():
        folder.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(name, str(folder))
    for name in ("QMX_HOME", "QMX_TOOLS_ROOT"):
        monkeypatch.delenv(name, raising=False)
    try:
        found = resolve()
    except NoQmxFolder:
        pass
    else:
        pytest.skip(f"this machine has a labelled QMX folder at {found.root}")
    (tmp_path / "cwd").mkdir()
    return dict(os.environ)


def ran(argv: list[str], env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *argv],
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


@pytest.mark.parametrize("program", sorted(PROGRAMS))
def test_each_program_with_no_folder_refuses_in_one_line_and_creates_nothing(
    program: str, scratch: dict[str, str], tmp_path: Path
) -> None:
    argv, code = PROGRAMS[program]
    before = tree(tmp_path)

    done = ran(argv, scratch, tmp_path / "cwd")

    assert (done.returncode, done.stdout, done.stderr.strip()) == (code, "", REFUSAL)
    assert tree(tmp_path) == before


@pytest.mark.parametrize("way", ["flag", "QMX_HOME", "pointer"])
def test_the_engine_and_the_host_open_the_same_folder_each_way(
    way: str, scratch: dict[str, str], tmp_path: Path
) -> None:
    home = tmp_path / "QMX"
    home.mkdir()
    flag: list[str] = []
    if way == "flag":
        flag = ["--home", str(home)]
    elif way == "QMX_HOME":
        scratch["QMX_HOME"] = str(home)
    else:
        pointer = pointer_file()
        assert pointer is not None
        pointer.parent.mkdir(parents=True)
        pointer.write_text(f"home = '{home}'\n", encoding="utf-8")

    stats = ran(["-m", "qmx_engine", "ledger", "stats", *flag], scratch, tmp_path / "cwd")
    host = ran(["-m", "qmx_host", "status", *flag], scratch, tmp_path / "cwd")

    ledger = home.resolve() / "engine" / "engine.sqlite"
    assert (stats.returncode, stats.stdout) == (1, f"no ledger at {ledger}\n")
    assert (host.returncode, host.stdout) == (0, "qmx_host is stopped.\n")
    assert tree(home) == []
