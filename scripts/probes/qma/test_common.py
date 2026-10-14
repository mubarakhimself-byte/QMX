# ruff: noqa: S101
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import common
import p_login
from common import Log, Provider, provider_env, reduced_env, require_plan_login, scrub_process_env
from plants import snapshot

PARENT = {
    "Path": "C:/Windows",
    "SystemRoot": "C:/Windows",
    "CLAUDE_CODE_GIT_BASH_PATH": "D:/Git/bin/bash.exe",
    "CLAUDE_CONFIG_DIR": "D:/ship/claude",
    "HTTPS_PROXY": "http://127.0.0.1:9",
    "ANTHROPIC_API_KEY": "sk-ant-fake",
    "NODE_EXTRA_CA_CERTS": "D:/ca.pem",
    "CLAUDE_CODE_USE_BEDROCK": "1",
}


def test_reduced_env_keeps_git_bash_and_drops_routing_names() -> None:
    assert reduced_env(PARENT) == {
        "Path": "C:/Windows",
        "SystemRoot": "C:/Windows",
        "CLAUDE_CODE_GIT_BASH_PATH": "D:/Git/bin/bash.exe",
        "CLAUDE_CONFIG_DIR": "D:/ship/claude",
    }


def test_provider_env_sends_the_base_url_with_its_own_token_and_pins_every_tier(
    tmp_path: Path,
) -> None:
    provider = Provider(
        "openrouter",
        "https://openrouter.ai/api",
        "moonshotai/kimi-k3",
        {"ENABLE_TOOL_SEARCH": "true"},
    )
    with patch.object(common, "FAKE_HOME", tmp_path / "home"):
        env = provider_env(PARENT, provider, "fake-provider-key", tmp_path / "claude")
    assert env == {
        "Path": "C:/Windows",
        "SystemRoot": "C:/Windows",
        "CLAUDE_CODE_GIT_BASH_PATH": "D:/Git/bin/bash.exe",
        "CLAUDE_CONFIG_DIR": str(tmp_path / "claude"),
        "HOME": str(tmp_path / "home"),
        "USERPROFILE": str(tmp_path / "home"),
        "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
        "ANTHROPIC_AUTH_TOKEN": "fake-provider-key",
        "ANTHROPIC_API_KEY": "",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "moonshotai/kimi-k3",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "moonshotai/kimi-k3",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "moonshotai/kimi-k3",
        "ANTHROPIC_DEFAULT_FABLE_MODEL": "moonshotai/kimi-k3",
        "ENABLE_TOOL_SEARCH": "true",
    }


def test_scrub_removes_names_in_place_and_is_idempotent() -> None:
    environ = dict(PARENT)
    assert scrub_process_env(environ) == (
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_USE_BEDROCK",
        "HTTPS_PROXY",
        "NODE_EXTRA_CA_CERTS",
    )
    assert environ == reduced_env(PARENT)
    assert scrub_process_env(environ) == ()


def test_every_probe_heals_a_hard_killed_plant_before_any_cli_start_and_keeps_the_login(
    tmp_path: Path,
) -> None:
    root = tmp_path / "claude"
    root.mkdir()
    settings = root / "settings.json"
    settings.write_text('{"theme": "dark"}', encoding="utf-8")
    credentials = root / ".credentials.json"
    credentials.write_text("fake-login-not-a-credential", encoding="utf-8")
    backup = tmp_path / "backup.json"
    snapshot(backup, root, [settings], [])
    settings.write_text('{"apiKeyHelper": "echo fake", "permissions": {"allow": ["Bash(*)"]}}')
    cli_started_with: list[str] = []

    def auth(_cli: Path) -> dict[str, Any]:
        cli_started_with.append(settings.read_text(encoding="utf-8"))
        return {"loggedIn": True, "apiProvider": "firstParty"}

    with (
        patch.object(common, "CONFIG_DIR", root),
        patch.object(common, "EVIDENCE", tmp_path / "evidence"),
        patch.object(common, "PLANT_BACKUP", backup),
        patch.object(common, "PLANT_LOCK", tmp_path / "plant.lock"),
        patch.object(common, "auth_method", auth),
    ):
        require_plan_login(Log("heal"), Path("claude.exe"))
        require_plan_login(Log("heal"), Path("claude.exe"))
    assert cli_started_with == ['{"theme": "dark"}', '{"theme": "dark"}']
    assert credentials.read_text(encoding="utf-8") == "fake-login-not-a-credential"
    assert not backup.exists()


def test_the_login_probe_heals_a_hard_killed_plant_before_the_interactive_cli(
    tmp_path: Path,
) -> None:
    root = tmp_path / "claude"
    root.mkdir()
    settings = root / "settings.json"
    settings.write_text('{"theme": "dark"}', encoding="utf-8")
    backup = tmp_path / "backup.json"
    snapshot(backup, root, [settings], [])
    settings.write_text('{"apiKeyHelper": "echo fake", "permissions": {"allow": ["Bash(*)"]}}')
    cli_started_with: list[str] = []

    def interactive_cli(*_args: object, **_kwargs: object) -> None:
        cli_started_with.append(settings.read_text(encoding="utf-8"))

    def signed_in(_cli: Path) -> dict[str, Any]:
        return {"loggedIn": True}

    with (
        patch.object(p_login, "CONFIG_DIR", root),
        patch.object(p_login, "SCRATCH", tmp_path),
        patch.object(p_login, "bundled_cli", lambda: Path("claude.exe")),
        patch.object(p_login, "auth_method", signed_in),
        patch.object(p_login.subprocess, "run", interactive_cli),
        patch.object(common, "EVIDENCE", tmp_path / "evidence"),
        patch.object(common, "PLANT_BACKUP", backup),
        patch.object(common, "PLANT_LOCK", tmp_path / "plant.lock"),
    ):
        assert p_login.main() == 0
    assert cli_started_with == ['{"theme": "dark"}']
    assert not backup.exists()
