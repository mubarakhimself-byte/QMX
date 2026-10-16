from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

LIVE = Path(__file__).resolve().parents[4] / "scripts" / "live" / "qma"
SCRIPTS = ("common", "s30_os_cap", "s30b_orphans")
THROWAWAY = ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TEMP")


@pytest.fixture
def live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, ModuleType]]:
    monkeypatch.setenv("QMA_LIVE_SCRATCH", str(tmp_path))
    monkeypatch.setattr(sys, "path", [str(LIVE), *sys.path])
    for name in SCRIPTS:
        sys.modules.pop(name, None)
    yield {name: importlib.import_module(name) for name in SCRIPTS}
    for name in SCRIPTS:
        sys.modules.pop(name, None)


def test_the_builder_refuses_bypass_permissions_without_a_tools_list(
    live: dict[str, ModuleType], tmp_path: Path
) -> None:
    common = live["common"]
    with pytest.raises(ValueError, match="bypassPermissions needs an explicit tools list"):
        common.chat_options(common.home_env(), tmp_path / "chat", tools=None)
    options = common.chat_options(common.home_env(), tmp_path / "chat", tools=[])
    assert options.permission_mode == "bypassPermissions"
    assert options.tools == []


@pytest.mark.parametrize(
    ("script", "chat", "tools"),
    [
        ("s30_os_cap", "heavy", ["Bash"]),
        ("s30_os_cap", "calm-1", []),
        ("s30_os_cap", "calm-2", []),
        ("s30b_orphans", "bg", ["Bash"]),
        ("s30b_orphans", "idle-1", []),
        ("s30b_orphans", "idle-2", []),
    ],
)
def test_each_live_chat_gets_only_the_tools_its_turn_needs_and_a_throwaway_home(
    live: dict[str, ModuleType], tmp_path: Path, script: str, chat: str, tools: list[str]
) -> None:
    options = live[script].options(chat, tmp_path / "procs", "cap")
    assert options.permission_mode == "bypassPermissions"
    assert options.tools == tools
    assert Path(str(options.cwd)).is_relative_to(tmp_path)
    for name in THROWAWAY:
        assert Path(options.env[name]).is_relative_to(tmp_path), name
    assert options.env["QMA_CHAT_ID"] == chat


def test_the_evidence_folder_survives_the_boot_scrub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QMA_EVIDENCE_DIR", str(tmp_path / "evidence"))
    monkeypatch.setenv("QMA_LIVE_SCRATCH", str(tmp_path))
    monkeypatch.setattr(sys, "path", [str(LIVE), *sys.path])
    sys.modules.pop("common", None)
    common = importlib.import_module("common")
    monkeypatch.setattr(common.os, "environ", dict(common.os.environ))
    try:
        common.boot()
        assert "QMA_EVIDENCE_DIR" not in common.os.environ
        log = common.Log("after-boot")
        log("written")
    finally:
        sys.modules.pop("common", None)
    assert log.path == tmp_path / "evidence" / "after-boot.log"
    assert log.path.read_text(encoding="utf-8").endswith(" written\n")
