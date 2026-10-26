"""A host's place name (LF6, AD-72): This PC is always `pc`; a server's host takes `--place` from
setup, else `[engine] host_name`, never guesses one, and refuses a name that is not a place name."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from qmx_control.service import ControlService
from qmx_home import resolve

from qmx_host.host import PlaceRefused, Role, placement_name

NOT_A_PLACE = (
    "refused: a server's place name is lowercase letters, digits and dashes, up to 63,"
    " and is not pc."
)


def test_a_host_takes_its_place_name_from_setup_then_settings_and_this_pc_is_pc(
    tmp_path: Path,
) -> None:
    control = ControlService(resolve(tmp_path / "QMX", create=True, drives=[]).home)

    on_this_pc = placement_name(control, "pc")
    given = placement_name(control, "server", "home-server")
    with pytest.raises(PlaceRefused, match=r"needs its place name"):
        placement_name(control, "node")
    control.settings_put("engine", {"host_name": "gpu-box"})

    assert (on_this_pc, given, placement_name(control, "node")) == ("pc", "home-server", "gpu-box")
    assert placement_name(control, "pc") == "pc"


@pytest.mark.parametrize(
    ("role", "place", "line"),
    [
        ("server", "Home Server", NOT_A_PLACE),
        ("server", "pc", NOT_A_PLACE),
        ("pc", "gpu-box", "refused: a host started as pc is This PC; --place names a server"),
    ],
    ids=["not-a-place-name", "server-called-pc", "pc-renamed"],
)
def test_a_place_name_that_is_not_one_is_refused_with_one_line(
    tmp_path: Path, role: Role, place: str, line: str
) -> None:
    control = ControlService(resolve(tmp_path / "QMX", create=True, drives=[]).home)

    with pytest.raises(PlaceRefused) as refused:
        placement_name(control, role, place)

    assert str(refused.value) == line


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
