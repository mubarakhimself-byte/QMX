from __future__ import annotations

import json
import os
import re
import sys
import threading
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient
from qmx_control.models import ControlError, Document
from qmx_control.server import create_app

from qma.harness.home import (
    ChatRecord,
    ClaudeSettings,
    PlanAuth,
    QmxHome,
    SessionId,
    code_settings,
    doctor,
    ensure_homes,
    list_records,
    parse_claude_settings,
    plan_auth_method,
    read_record,
    remember_rule,
    workspace_key,
    write_record,
)
from qma.harness.launch import PLAN, ChatConfig, Child, Interactive, LaunchRefused
from qma.harness.routes import control_service, router

BEARER = "test-token"
HEADERS = {"Authorization": f"Bearer {BEARER}"}
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
        (
            {"permissions": {"defaultMode": ["bypassPermissions"]}},
            "[claude] permissions.defaultMode is not allowed",
        ),
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
    with TestClient(create_app(control, BEARER, extra_routers=[extra])) as rest:
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


def _throwaway_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    personal = tmp_path / "throwaway" / ".claude"
    for name in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(name, str(personal.parent))
    personal.mkdir(parents=True)
    return personal


def _junction(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


@pytest.mark.parametrize("inside", ["", "nested/qmx"])
def test_ensure_homes_refuses_a_home_inside_the_operators_claude_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, inside: str
) -> None:
    personal = _throwaway_home(monkeypatch, tmp_path)
    with pytest.raises(LaunchRefused, match=r"inside the operator's own ~/\.claude"):
        ensure_homes(QmxHome(personal / inside))
    assert list(personal.iterdir()) == []


def test_ensure_homes_refuses_a_plan_home_linked_to_the_operators_claude_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    personal = _throwaway_home(monkeypatch, tmp_path)
    home = QmxHome(tmp_path / "qmx")
    _junction(home.plan_dir, personal)
    with pytest.raises(LaunchRefused, match=r"inside the operator's own ~/\.claude"):
        ensure_homes(home)
    assert list(personal.iterdir()) == []


@pytest.mark.parametrize(
    ("logged_in", "method", "provider", "subscription"),
    [
        (True, "claude.ai", "firstParty", True),
        (False, "claude.ai", "firstParty", False),
        (True, "api_key_helper", "firstParty", False),
        (True, "claude.ai", "bedrock", False),
    ],
)
def test_plan_auth_accepts_only_a_signed_in_claude_ai_first_party_login(
    logged_in: bool, method: str, provider: str, subscription: bool
) -> None:
    auth = PlanAuth(logged_in=logged_in, method=method, provider=provider, subscription="max")
    assert auth.is_subscription is subscription
    if subscription:
        auth.require()
        return
    with pytest.raises(LaunchRefused) as refused:
        auth.require()
    assert str(refused.value) == (
        f"the plan home is not signed in to a claude.ai plan "
        f"(method {method}, provider {provider}); run /login in the console"
    )


def test_plan_auth_reads_no_settings_file_from_the_plan_home(
    home: QmxHome, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _throwaway_home(monkeypatch, tmp_path)
    ensure_homes(home)
    ran = tmp_path / "helper-ran"
    python = Path(sys.executable).as_posix()
    helper = f"'{python}' -c \"open('{ran.as_posix()}', 'w').close()\""
    (home.plan_dir / "settings.json").write_text(
        json.dumps({"apiKeyHelper": helper}), encoding="utf-8"
    )
    settings = code_settings(
        ClaudeSettings(), launcher=LAUNCHER, workspace=tmp_path, memory_dir=tmp_path / "memory"
    )
    assert plan_auth_method(home, settings) == PlanAuth(
        logged_in=False, method="none", provider="firstParty", subscription=None
    )
    assert not ran.exists()


def test_concurrent_remembers_all_land(home: QmxHome) -> None:
    control = control_service(home)
    rules = [f"Bash(job {number})" for number in range(16)]
    start = threading.Barrier(len(rules))

    def remember(rule: str) -> None:
        start.wait()
        remember_rule(control, rule, home.root / "ws")

    threads = [threading.Thread(target=remember, args=(rule,)) for rule in rules]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    remembered = cast(
        "dict[str, dict[str, list[str]]]", control.settings_get("claude")["remembered"]
    )
    assert sorted(remembered[workspace_key(home.root / "ws")]["allow"]) == sorted(rules)


def test_a_whole_section_put_keeps_remembered_rules_unless_it_names_them(
    home: QmxHome,
) -> None:
    control = control_service(home)
    remember_rule(control, "Bash(npm test)", home.root / "ws")
    remembered = {workspace_key(home.root / "ws"): {"allow": ["Bash(npm test)"]}}
    extra = router(home, control, scrubbed=(), keep=())
    with TestClient(create_app(control, BEARER, extra_routers=[extra])) as rest:
        allowed = {"permissions": {"allow": ["Read"]}}
        rest.put("/api/claude-settings", json=allowed, headers=HEADERS)
        assert rest.get("/api/claude-settings", headers=HEADERS).json() == {
            **allowed,
            "remembered": remembered,
        }
        rest.put("/api/settings/claude", json={"remembered": {}}, headers=HEADERS)
        assert rest.get("/api/claude-settings", headers=HEADERS).json() == {"remembered": {}}


def _http_hook(headers: dict[str, str]) -> Document:
    hook: dict[str, object] = {"type": "http", "url": "http://127.0.0.1:9/hook", "headers": headers}
    return _hook(hook)


def _hook(hook: dict[str, object]) -> Document:
    return cast("Document", {"hooks": {"Stop": [{"hooks": [hook]}]}})


@pytest.mark.parametrize(
    ("hook", "key"),
    [
        ({"type": "http", "url": "http://h/x", "Headers": {"X-Auth": "abc"}}, "Headers"),
        ({"type": "http", "url": "http://h/x", "inner": {"ApiKey": "abc"}}, "inner"),
        ({"type": "command", "command": "x", "url": "http://h/x"}, "url"),
        ({"type": "http", "url": "http://h/x", "command": "x"}, "command"),
        ({"type": "command", "command": "x", "headers": {}}, "headers"),
        ({"type": "prompt", "prompt": "x", "args": ["a"]}, "args"),
        ({"type": "agent", "prompt": "x", "shell": "bash"}, "shell"),
        ({"type": "agent", "prompt": "x", "continueOnBlock": True}, "continueOnBlock"),
    ],
)
def test_parse_claude_settings_refuses_a_hook_key_its_type_does_not_document(
    hook: dict[str, object], key: str
) -> None:
    with pytest.raises(LaunchRefused) as refused:
        parse_claude_settings(_hook(hook))
    assert str(refused.value) == f"[claude] hooks.Stop {hook['type']} hook key {key} is not allowed"


def test_parse_claude_settings_accepts_every_documented_hook_key() -> None:
    common = {"if": "Bash(git *)", "timeout": 5, "statusMessage": "s", "once": False}
    hooks: list[dict[str, object]] = [
        {
            "type": "command",
            "command": "notify",
            "args": ["a"],
            "async": True,
            "asyncRewake": False,
            "shell": "bash",
            "onFailure": "continue",
            **common,
        },
        {
            "type": "http",
            "url": "http://127.0.0.1:9/hook",
            "headers": {"Authorization": "Bearer $QMX_HOOK_TOKEN"},
            "allowedEnvVars": ["QMX_HOOK_TOKEN"],
            "onFailure": "block",
            **common,
        },
        {"type": "prompt", "prompt": "p", "model": "haiku", "continueOnBlock": True, **common},
        {"type": "agent", "prompt": "p", "model": "haiku", **common},
    ]
    document = cast("Document", {"hooks": {"Stop": [{"hooks": hooks}]}})
    assert parse_claude_settings(document).raw == document


@pytest.mark.parametrize("name", ["Authorization", "X-Auth", "X-Trace", "Cookie"])
@pytest.mark.parametrize(
    "value",
    [
        "Bearer abc123",
        "Bearer sk-1 $X",
        "abc $QMX_HOOK_TOKEN",
        "$QMX_HOOK_TOKEN abc",
        "Bearer ${QMX_HOOK_TOKEN",
        "$QMX_HOOK_TOKEN}",
        "${}",
        "${QMX_HOOK_TOKEN}X",
        "Token $QMX_HOOK_TOKEN",
        "$qmx_hook_token",
        "literal",
    ],
)
def test_parse_claude_settings_refuses_a_hook_header_that_is_not_one_reference(
    name: str, value: str
) -> None:
    with pytest.raises(LaunchRefused) as refused:
        parse_claude_settings(_http_hook({name: value}))
    assert str(refused.value) == (
        f"[claude] hooks.Stop header {name} must be $NAME or ${{NAME}}, "
        "optionally after Bearer or Basic"
    )


@pytest.mark.parametrize(
    "value",
    [
        "$QMX_HOOK_TOKEN",
        "Bearer $QMX_HOOK_TOKEN",
        "Basic $B64",
        "${QMX_HOOK_TOKEN}",
        "Bearer ${QMX_HOOK_TOKEN}",
        "Basic ${B64}",
    ],
)
def test_parse_claude_settings_accepts_a_hook_header_that_is_one_reference(value: str) -> None:
    accepted = _http_hook({"X-Auth": value})
    assert parse_claude_settings(accepted).raw == accepted


@pytest.mark.parametrize(
    "url",
    [
        "https://user:pw1@h/x",
        "https://user@h/x",
        "http://:pw1@h/x",
        "https://u:p@h:8/x?a=b",
        "https:\\\\u:p@h/x",
        "https:u:p@h/x",
        "https:/u:p@h/x",
        " https://h/x",
        "\thttps://h/x",
        "https://h/x ",
        "https://h/x\n",
        "https://h\\x",
        "ftp://h/x",
        "//h/x",
        "h/x",
    ],
)
def test_parse_claude_settings_refuses_a_hook_url_that_is_not_plain_http(url: str) -> None:
    with pytest.raises(LaunchRefused) as refused:
        parse_claude_settings(_hook({"type": "http", "url": url}))
    assert str(refused.value) == (
        "[claude] hooks.Stop http hook url must be http(s)://host[/path] with no user, "
        "password, backslash or whitespace; put a credential in a $NAME header"
    )


@pytest.mark.parametrize(
    "url", ["https://h/x/@team?to=a@b", "http://127.0.0.1:9/hook", "https://h:8", "https://h#f"]
)
def test_parse_claude_settings_accepts_a_plain_http_hook_url(url: str) -> None:
    accepted = _hook({"type": "http", "url": url})
    assert parse_claude_settings(accepted).raw == accepted


def test_doctor_shows_hooks_as_structure_and_hides_every_operator_value(
    home: QmxHome, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _throwaway_home(monkeypatch, tmp_path)
    ensure_homes(home)
    control = control_service(home)
    quoted = "'csecret3'"
    hooks: list[dict[str, object]] = [
        {
            "type": "http",
            "url": "https://hooks.example/stop?token=qsecret1",
            "headers": {"Authorization": "Bearer $QMX_HOOK_TOKEN"},
            "allowedEnvVars": ["QMX_HOOK_TOKEN"],
            "statusMessage": "posting with ssecret2",
        },
        {
            "type": "command",
            "command": f"notify --secret={quoted}",
            "args": ["--token", "asecret4"],
        },
        {
            "type": "command",
            "command": "curl -u ops:csecret5 https://h/x",
            "if": "Bash(isecret6 *)",
        },
        {"type": "prompt", "prompt": "the password is psecret7", "timeout": 5},
    ]
    document = {"hooks": {"Stop": [{"matcher": "Bash", "hooks": hooks}]}}
    control.settings_put("claude", cast("Document", document))
    lines = doctor(home, control, scrubbed=(), keep=(), launcher=LAUNCHER)
    leaked = ["qsecret1", "QMX_HOOK_TOKEN", "ssecret2", "csecret3", "asecret4", "csecret5"]
    leaked += ["isecret6", "psecret7", "hooks.example", "notify", "curl"]
    assert [(line.name, word) for line in lines for word in leaked if word in line.detail] == []
    inline = {line.name: line for line in lines}["inline settings"]
    settings = json.loads(inline.detail.split(": ", 1)[1])
    assert settings["hooks"] == {
        "Stop": [
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "http",
                        "url": "<set>",
                        "headers": "<set>",
                        "allowedEnvVars": "<set>",
                        "statusMessage": "<set>",
                    },
                    {"type": "command", "command": "<set>", "args": "<set>"},
                    {"type": "command", "command": "<set>", "if": "<set>"},
                    {"type": "prompt", "prompt": "<set>", "timeout": "<set>"},
                ],
            }
        ],
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
        ],
    }


@pytest.mark.parametrize(
    ("attribution", "why"),
    [
        ({"commit": "c", "apiToken": "asecret1"}, "attribution.apiToken is not allowed"),
        ({"Commit": "c"}, "attribution.Commit is not allowed"),
        ({"commit": True}, "attribution.commit must be a string"),
        ({"pr": 1}, "attribution.pr must be a string"),
        ({"sessionUrl": "false"}, "attribution.sessionUrl must be true or false"),
        (True, "attribution must be a table or false"),
    ],
)
def test_settings_put_refuses_an_attribution_key_or_type_the_docs_do_not_list(
    home: QmxHome, attribution: object, why: str
) -> None:
    control = control_service(home)
    with pytest.raises(ControlError) as refused:
        control.settings_put("claude", cast("Document", {"attribution": attribution}))
    assert str(refused.value) == f"[claude] {why}"
    assert control.settings_get("claude") == {}


@pytest.mark.parametrize("attribution", [{"commit": "c", "pr": "", "sessionUrl": False}, False])
def test_parse_claude_settings_accepts_every_documented_attribution_form(
    attribution: object,
) -> None:
    document = cast("Document", {"attribution": attribution})
    assert parse_claude_settings(document).raw == document


def test_a_whole_section_put_racing_remember_rule_keeps_the_rule(home: QmxHome) -> None:
    control = control_service(home)
    parse = control.settings_parsers["claude"]
    put_read_current = threading.Event()
    remembered = threading.Event()
    putter = threading.current_thread()

    def slow_parse(values: Document, current: Document) -> Document:
        parsed = parse(values, current)
        if threading.current_thread() is putter:
            put_read_current.set()
            remembered.wait(timeout=1)
        return parsed

    control.settings_parsers["claude"] = slow_parse

    def remember() -> None:
        put_read_current.wait(timeout=5)
        remember_rule(control, "Bash(npm test)", home.root / "ws")
        remembered.set()

    thread = threading.Thread(target=remember)
    thread.start()
    control.settings_put("claude", {"permissions": {"allow": ["Read"]}})
    thread.join(timeout=10)
    assert control.settings_get("claude") == {
        "permissions": {"allow": ["Read"]},
        "remembered": {workspace_key(home.root / "ws"): {"allow": ["Bash(npm test)"]}},
    }


ARGV_LINE = re.compile(
    r"(\d+) characters of 30000 for a plan launch in .+; largest part: (.+) at (\d+)"
)


def test_doctor_reports_the_whole_plan_launch_command_line(
    home: QmxHome, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _throwaway_home(monkeypatch, tmp_path)
    ensure_homes(home)
    control = control_service(home)

    def read() -> tuple[int, bool, int, str]:
        lines = {
            line.name: line
            for line in doctor(home, control, scrubbed=(), keep=(), launcher=LAUNCHER)
        }
        inline = int(lines["inline settings"].detail.split(" ", 1)[0])
        line = lines["plan launch command line"]
        found = ARGV_LINE.fullmatch(line.detail)
        assert found is not None, line.detail
        return inline, line.ok, int(found[1]), found[2]

    inline, ok, total, _ = read()
    assert ok
    assert total > inline + 200
    (home.workspaces_dir / "CLAUDE.md").write_text("x" * 31_000, encoding="utf-8")
    _, ok, total, largest = read()
    assert not ok
    assert total > 31_000
    assert largest == "QMX.md and the workspace CLAUDE.md and AGENTS.md"
