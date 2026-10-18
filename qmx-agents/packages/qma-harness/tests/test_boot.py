from __future__ import annotations

from pathlib import Path

import pytest

from qma.boot import (
    KEEP_NAMES,
    KeepListRefused,
    parse_keep_names,
    read_keep_names,
    scrub_process_env,
)


def test_scrub_removes_unlisted_names_sorted_and_is_idempotent() -> None:
    environ = {
        "PATH": "p",
        "ANTHROPIC_API_KEY": "fake",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "CLAUDE_CODE_GIT_BASH_PATH": "D:/Git/bin/bash.exe",
        "CLAUDE_CODE_USE_BEDROCK": "1",
    }
    removed = scrub_process_env(environ)
    assert removed == ("ANTHROPIC_API_KEY", "CLAUDE_CODE_USE_BEDROCK", "HTTPS_PROXY")
    assert environ == {"PATH": "p", "CLAUDE_CODE_GIT_BASH_PATH": "D:/Git/bin/bash.exe"}
    assert scrub_process_env(environ) == ()


def test_scrub_matches_names_case_insensitively() -> None:
    environ = {"Path": "p", "SystemRoot": "C:/Windows", "java_home": "j", "Https_Proxy": "x"}
    removed = scrub_process_env(environ, extra_keep=frozenset({"JAVA_HOME"}))
    assert removed == ("Https_Proxy",)
    assert environ == {"Path": "p", "SystemRoot": "C:/Windows", "java_home": "j"}


@pytest.mark.parametrize(
    "name", ["HTTPS_PROXY", "MY_OPENAI_KEY", "AWS_REGION", "NODE_OPTIONS", "SSL_CERT_FILE"]
)
def test_parse_keep_names_refuses_banned_fragments(name: str) -> None:
    with pytest.raises(KeepListRefused, match=name):
        parse_keep_names(["JAVA_HOME", name])


def test_parse_keep_names_refuses_non_names_and_upper_cases_the_rest() -> None:
    with pytest.raises(KeepListRefused, match="not an environment variable name"):
        parse_keep_names(["A=B"])
    assert parse_keep_names(["java_home", "GOPATH"]) == {"JAVA_HOME", "GOPATH"}


def test_keep_names_allow_git_bash_and_no_other_claude_name() -> None:
    assert "CLAUDE_CODE_GIT_BASH_PATH" in KEEP_NAMES
    assert parse_keep_names(["claude_code_git_bash_path"]) == {"CLAUDE_CODE_GIT_BASH_PATH"}
    with pytest.raises(KeepListRefused):
        parse_keep_names(["CLAUDE_CONFIG_DIR"])


def test_read_keep_names_drops_bad_names_and_tolerates_missing_input(tmp_path: Path) -> None:
    settings = tmp_path / "settings.toml"
    settings.write_text(
        '[environment]\nkeep = ["JAVA_HOME", "HTTPS_PROXY", 3, "bad name", "gopath"]\n',
        encoding="utf-8",
    )
    assert read_keep_names(settings) == {"JAVA_HOME", "GOPATH"}
    assert read_keep_names(tmp_path / "missing.toml") == frozenset()
    settings.write_text("[budgets]\nagent_memory_mb = 4096\n", encoding="utf-8")
    assert read_keep_names(settings) == frozenset()
    settings.write_text("not = = toml", encoding="utf-8")
    assert read_keep_names(settings) == frozenset()
