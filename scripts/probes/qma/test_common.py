# ruff: noqa: S101
from __future__ import annotations

from common import reduced_env, scrub_process_env

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
