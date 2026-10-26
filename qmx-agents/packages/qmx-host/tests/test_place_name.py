"""A host's place name (LF6, AD-72): `--place` from setup, else `[engine] host_name`, else `pc` on
This PC; a server's host never guesses one."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from qmx_control.service import ControlService
from qmx_home import resolve

from qmx_host.host import PlaceUnnamed, placement_name


def test_a_host_takes_its_place_name_from_setup_then_settings_then_this_pc(
    tmp_path: Path,
) -> None:
    control = ControlService(resolve(tmp_path / "QMX", create=True, drives=[]).home)

    on_this_pc = placement_name(control, "pc")
    given = placement_name(control, "server", "home-server")
    with pytest.raises(PlaceUnnamed):
        placement_name(control, "node")
    control.settings_put("engine", {"host_name": "gpu-box"})

    assert (on_this_pc, given, placement_name(control, "node")) == ("pc", "home-server", "gpu-box")


def test_a_server_host_started_with_no_place_name_refuses_with_one_line(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True, drives=[])
    refused = subprocess.run(
        [
            sys.executable,
            "-m",
            "qmx_host",
            "serve",
            *("--home", str(layout.root), "--port", "1", "--role", "server"),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert refused.returncode == 1
    assert refused.stderr.splitlines() == [
        "refused: a host started as server needs its place name; pass --place <name>, the name"
        " he gave this machine in his place list, or set [engine] host_name."
    ]
