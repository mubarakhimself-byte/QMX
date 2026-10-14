from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from qmx_control.server import create_app

from qma.harness.home import (
    ChatRecord,
    ClaudeSettings,
    QmxHome,
    SessionId,
    code_settings,
    doctor,
    ensure_homes,
    list_records,
    parse_claude_settings,
    read_record,
    remember_rule,
    workspace_key,
    write_record,
)
from qma.harness.launch import PLAN, ChatConfig, Child, Interactive, LaunchRefused
from qma.harness.routes import control_service, router

TOKEN = "test-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
LAUNCHER = Path("D:/venv/Scripts/qma-cli-launcher.exe")
CHAT = SessionId("0b9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e1f")


@pytest.fixture
def home(tmp_path: Path) -> QmxHome:
    return QmxHome(tmp_path / "qmx")


@pytest.mark.parametrize(
    ("raw", "named"),
    [
        ({"apiKeyHelper": "echo key"}, "[claude] apiKeyHelper is not allowed"),
        ({"forceLoginMethod": "console"}, "[claude] forceLoginMethod is not allowed"),
        ({"enabledPlugins": {"x@y": True}}, "[claude] enabledPlugins is not allowed"),
        ({"env": {"HTTPS_PROXY": "http://p"}}, "[claude] env.HTTPS_PROXY is not allowed"),
        ({"permissions": {"defaultMode": "auto"}}, "[claude] permissions.defaultMode"),
        ({"permissions": {"allow": ["Bash(git *"]}}, "is not a permission rule"),
        ({"hooks": {"Stop": [{"hooks": [{"type": "exec"}]}]}}, "[claude] hooks.Stop"),
    ],
)
def test_parse_claude_settings_refuses_keys_outside_the_allow_list(
    raw: dict[str, object], named: str
) -> None:
    with pytest.raises(LaunchRefused) as refused:
        parse_claude_settings(raw)
    assert named in str(refused.value)


def test_fixed_values_win_and_remembered_rules_stay_in_their_workspace(tmp_path: Path) -> None:
    here, there = tmp_path / "here", tmp_path / "there"
    user = ClaudeSettings(
        {
            "forceLoginMethod": "console",
            "cleanupPeriodDays": 1,
            "permissions": {"allow": ["Read"]},
            "env": {"CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "2"},
            "hooks": {"ConfigChange": [{"hooks": [{"type": "command", "command": "true"}]}]},
            "remembered": {workspace_key(here): {"allow": ["Bash(git status)", "Read"]}},
        }
    )
    memory = tmp_path / "memory"
    rendered = json.loads(code_settings(user, launcher=LAUNCHER, workspace=here, memory_dir=memory))
    assert rendered == {
        "forceLoginMethod": "claudeai",
        "cleanupPeriodDays": 3650,
        "autoMemoryDirectory": memory.as_posix(),
        "permissions": {"allow": ["Read", "Bash(git status)"]},
        "env": {"CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "2"},
        "hooks": {
            "ConfigChange": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "'D:/venv/Scripts/qma-cli-launcher.exe' "
                            "--qma-block-config-change",
                            "timeout": 10,
                        }
                    ]
                }
            ]
        },
    }
    elsewhere = json.loads(
        code_settings(user, launcher=LAUNCHER, workspace=there, memory_dir=memory)
    )
    assert elsewhere["permissions"] == {"allow": ["Read"]}
    defaults = json.loads(
        code_settings(ClaudeSettings(), launcher=LAUNCHER, workspace=there, memory_dir=memory)
    )
    assert defaults["env"] == {"CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "1"}


def test_ensure_homes_is_idempotent_and_links_the_transcript_folder(home: QmxHome) -> None:
    ensure_homes(home)
    ensure_homes(home)
    (home.plan_dir / "projects" / "marker.jsonl").write_text("{}", encoding="utf-8")
    linked = home.relayed_dir / "projects"
    assert linked.resolve() == (home.plan_dir / "projects").resolve()
    assert (linked / "marker.jsonl").read_text(encoding="utf-8") == "{}"
    assert sorted(path.name for path in home.root.iterdir()) == [
        "chats",
        "claude",
        "claude-relayed",
        "procs",
        "state",
        "workspaces",
    ]


def test_ensure_homes_refuses_a_login_file_in_the_relayed_home(home: QmxHome) -> None:
    ensure_homes(home)
    (home.relayed_dir / ".credentials.json").write_text("{}", encoding="utf-8")
    with pytest.raises(LaunchRefused, match=r"relayed home holds a login file: .*credentials"):
        ensure_homes(home)


def test_records_round_trip_and_replace_atomically(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = ChatConfig(PLAN, "haiku", None, "default", home.root / "ws", Interactive())
    first = ChatRecord(CHAT, config, started=False, turn="idle")
    write_record(home, first)
    child = ChatConfig(PLAN, "opus", "high", "plan", home.root / "ws", Child(CHAT, True))
    other = ChatRecord(SessionId("child-1"), child, started=True, turn="running")
    write_record(home, other)
    assert read_record(home, CHAT) == first
    assert list_records(home) == [first, other]
    assert read_record(home, SessionId("missing")) is None

    def interrupted(self: Path, target: Path) -> Path:
        raise OSError("power cut")

    monkeypatch.setattr(Path, "replace", interrupted)
    with pytest.raises(OSError, match="power cut"):
        write_record(home, ChatRecord(CHAT, config, started=True, turn="running"))
    assert read_record(home, CHAT) == first


def test_remember_rule_writes_exactly_one_rule_through_the_control_service(
    home: QmxHome,
) -> None:
    control = control_service(home)
    remember_rule(control, "Bash(npm test)", home.root / "ws")
    remember_rule(control, "Bash(npm test)", home.root / "ws")
    assert control.settings_get("claude") == {
        "remembered": {workspace_key(home.root / "ws"): {"allow": ["Bash(npm test)"]}}
    }


def test_the_settings_door_refuses_a_forbidden_key_and_leaves_the_file_alone(
    home: QmxHome,
) -> None:
    control = control_service(home)
    extra = router(home, control, scrubbed=(), keep=())
    with TestClient(create_app(control, TOKEN, extra_routers=[extra])) as rest:
        allowed = {"permissions": {"allow": ["Bash(git status)"]}}
        assert rest.put("/api/claude-settings", json=allowed, headers=HEADERS).json() == allowed
        before = (home.root / "settings.toml").read_text(encoding="utf-8")
        for door in ("/api/claude-settings", "/api/settings/claude"):
            refused = rest.put(door, json={"apiKeyHelper": "x"}, headers=HEADERS)
            assert refused.status_code == 400
            assert "apiKeyHelper is not allowed" in refused.json()["error"]["message"]
        keep = rest.put(
            "/api/settings/environment", json={"keep": ["HTTPS_PROXY"]}, headers=HEADERS
        )
        assert "banned fragment 'PROXY'" in keep.json()["error"]["message"]
        assert (home.root / "settings.toml").read_text(encoding="utf-8") == before
        assert rest.get("/api/claude-settings", headers=HEADERS).json() == allowed


def test_doctor_names_the_homes_scrubbed_names_and_a_relayed_login(
    home: QmxHome, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(name, str(tmp_path / "throwaway"))
    ensure_homes(home)
    (home.relayed_dir / ".credentials.json").write_text("{}", encoding="utf-8")
    lines = {
        line.name: line
        for line in doctor(
            home,
            control_service(home),
            scrubbed=("ANTHROPIC_API_KEY", "HTTPS_PROXY"),
            keep=("JAVA_HOME",),
            launcher=LAUNCHER,
        )
    }
    assert lines["boot scrub removed"].detail == "ANTHROPIC_API_KEY, HTTPS_PROXY"
    assert not lines["relayed home login"].ok
    assert str(home.relayed_dir / ".credentials.json") in lines["relayed home login"].detail
    assert lines["relayed projects link"].ok
    assert not lines["plan auth method"].ok
    settings = json.loads(lines["inline settings"].detail.split(": ", 1)[1])
    assert settings["forceLoginMethod"] == "claudeai"
    assert lines["keep list"].detail == "JAVA_HOME; an edit applies at the next start"
    assert sum(name.startswith("departure ") for name in lines) == 19
    if os.name == "nt":
        assert "managed policy C:/Program Files/ClaudeCode/managed-settings.json" in lines
