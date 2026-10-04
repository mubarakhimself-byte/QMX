"""Host configuration binds inference and authority without starting providers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from qma.daemon.request_runtime.provider_config import load_agent_request_config
from qmf.core import is_refusal


def configuration() -> dict[str, Any]:
    return {
        "enabled": True,
        "providers": {
            "local-proxy": {
                "protocol": "chat-completions",
                "endpoint": "http://127.0.0.1:9876/v1/chat/completions",
                "model": "configured-workhorse",
                "deployment_id": "test-local-proxy",
                "api_key_env": "SDK_TEST_TOKEN",
                "stream": True,
            }
        },
        "profiles": {
            "research-reader": {
                "role": "application",
                "authority_profile": "app-use",
                "app_instance_id": "inst:research",
                "provider_id": "local-proxy",
                "tools": ["research_browse"],
            }
        },
        "research_browse": {
            "source_id": "research-corpus",
            "snapshot_ref": "fp1:configured-snapshot",
            "allowed_locators": ["hypotheses.md"],
        },
        "instance_revisions": {"inst:research": 1},
    }


def write(root: Path, sdk: dict[str, Any]) -> None:
    (root / "operator-config.json").write_text(json.dumps({"agent_sdk": sdk}), encoding="utf-8")


def test_absent_or_explicitly_disabled_has_no_default_transport(tmp_path: Path) -> None:
    absent = load_agent_request_config(tmp_path)
    assert not is_refusal(absent) and absent.value is None
    write(tmp_path, {"enabled": False})
    disabled = load_agent_request_config(tmp_path)
    assert not is_refusal(disabled) and disabled.value is None


def test_valid_configuration_constructs_without_reading_auth_or_connecting(tmp_path: Path) -> None:
    write(tmp_path, configuration())
    loaded = load_agent_request_config(tmp_path)
    assert not is_refusal(loaded) and loaded.value is not None
    configured = loaded.value
    policy = configured.policies["research-reader"]
    assert policy.authority_profile == "app-use"
    assert policy.profile.app_instance_id == "inst:research"
    assert policy.provider_id.startswith("configured:local-proxy:")
    assert policy.provider_id in configured.providers
    assert configured.profile_tools["research-reader"] == frozenset({"research_browse"})
    # The named credential is not present; construction still succeeds because
    # authorization is resolved only at explicitly admitted provider execution.
    assert configured.max_workers == 2


def test_changed_deployment_config_changes_accepted_provider_identity(tmp_path: Path) -> None:
    sdk = configuration()
    write(tmp_path, sdk)
    first = load_agent_request_config(tmp_path)
    assert not is_refusal(first) and first.value is not None
    original = first.value.policies["research-reader"].provider_id
    sdk["providers"]["local-proxy"]["model"] = "other-workhorse"
    write(tmp_path, sdk)
    second = load_agent_request_config(tmp_path)
    assert not is_refusal(second) and second.value is not None
    assert second.value.policies["research-reader"].provider_id != original


def test_changed_corpus_scope_changes_accepted_provider_identity(tmp_path: Path) -> None:
    sdk = configuration()
    write(tmp_path, sdk)
    first = load_agent_request_config(tmp_path)
    assert not is_refusal(first) and first.value is not None
    original = first.value.policies["research-reader"].provider_id
    sdk["research_browse"]["allowed_locators"] = ["other.md"]
    write(tmp_path, sdk)
    second = load_agent_request_config(tmp_path)
    assert not is_refusal(second) and second.value is not None
    assert second.value.policies["research-reader"].provider_id != original


@pytest.mark.parametrize(
    "field,value",
    [
        ("api_key", "fixture-only-do-not-echo"),
        ("fallback", "paid-provider"),
        ("endpoint", "http://example.invalid/v1/chat/completions"),
        ("endpoint", "https://example.invalid/v1/chat/completions?key=fixture-only-do-not-echo"),
        ("protocol", "credential-translation"),
        ("stream", "true"),
        ("api_key_env", "raw-token-with-dashes"),
    ],
)
def test_unsupported_provider_config_fails_sanitized(
    tmp_path: Path, field: str, value: object
) -> None:
    sdk = configuration()
    sdk["providers"]["local-proxy"][field] = value
    write(tmp_path, sdk)
    refused = load_agent_request_config(tmp_path)
    assert is_refusal(refused)
    assert "fixture-only-do-not-echo" not in repr(refused)


@pytest.mark.parametrize(
    "change",
    ["authority", "app", "provider", "tool", "locators", "capacity", "instructions"],
)
def test_incomplete_or_widened_host_policy_is_not_enabled(tmp_path: Path, change: str) -> None:
    sdk = configuration()
    profile = sdk["profiles"]["research-reader"]
    if change == "authority":
        del profile["authority_profile"]
    elif change == "app":
        del profile["app_instance_id"]
    elif change == "provider":
        profile["provider_id"] = "not-configured"
    elif change == "tool":
        profile["tools"] = ["shell"]
    elif change == "locators":
        sdk["research_browse"]["allowed_locators"] = []
    elif change == "capacity":
        sdk["max_workers"] = 9
    else:
        profile["instructions"] = "x" * 32769
    write(tmp_path, sdk)
    assert is_refusal(load_agent_request_config(tmp_path))


def test_global_behavior_does_not_imply_authoring_authority(tmp_path: Path) -> None:
    sdk = configuration()
    sdk["profiles"]["research-reader"].update({"role": "global"})
    del sdk["profiles"]["research-reader"]["app_instance_id"]
    write(tmp_path, sdk)
    assert is_refusal(load_agent_request_config(tmp_path))
    sdk["profiles"]["research-reader"]["session_app_instance_id"] = "inst:research"
    write(tmp_path, sdk)
    configured = load_agent_request_config(tmp_path)
    assert not is_refusal(configured) and configured.value is not None
    assert configured.value.policies["research-reader"].authority_profile == "app-use"


def test_duplicate_or_oversize_operator_configuration_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "operator-config.json"
    path.write_text('{"agent_sdk":{"enabled":false,"enabled":true}}', encoding="utf-8")
    assert is_refusal(load_agent_request_config(tmp_path))
    path.write_text(" " * 1_048_577, encoding="utf-8")
    assert is_refusal(load_agent_request_config(tmp_path))


def test_research_workflow_is_host_selected_and_pins_provider_identity(tmp_path: Path) -> None:
    sdk = configuration()
    sdk["research_workflow"] = {
        "specialist_id": "corpus-analyst",
        "version": "1",
        "instructions": "Analyze supplied evidence.",
        "profiles": ["research-reader"],
    }
    write(tmp_path, sdk)
    first = load_agent_request_config(tmp_path)
    assert not is_refusal(first) and first.value is not None
    assert first.value.research_workflow == sdk["research_workflow"]
    identity = first.value.policies["research-reader"].provider_id
    sdk["research_workflow"]["instructions"] = "Changed analysis behavior."
    write(tmp_path, sdk)
    changed = load_agent_request_config(tmp_path)
    assert not is_refusal(changed) and changed.value is not None
    assert changed.value.policies["research-reader"].provider_id != identity
    sdk["research_workflow"]["profiles"] = ["unknown-profile"]
    write(tmp_path, sdk)
    assert is_refusal(load_agent_request_config(tmp_path))
