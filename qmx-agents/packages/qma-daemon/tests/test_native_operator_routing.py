"""Operator routing is explicit, nonsecret, and separate from inference graphs."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import pytest
from qma.daemon.request_runtime.provider_config import load_agent_request_config
from qmf.core import is_refusal
from test_request_runtime_configured_daemon import (
    app_session,
    compose_configured,
    discover,
    sdk_config,
)
from test_request_runtime_provider_config import configuration, write


def native_configuration(tmp_path: Path, backend: str = "codex") -> dict[str, Any]:
    sdk = configuration()
    sdk["providers"] = {
        "native": {
            "protocol": "native-session",
            "backend": backend,
            "executable": str(tmp_path / "pinned-native.exe"),
            "dedicated_home": str(tmp_path / "native-home"),
            "empty_workspace": str(tmp_path / "empty-workspace"),
        }
    }
    sdk["profiles"]["research-reader"]["provider_id"] = "native"
    return sdk


@pytest.mark.parametrize("backend", ["codex", "claude"])
def test_native_operator_configuration_is_constructed_without_sdk_or_auth_io(
    tmp_path: Path, backend: str, monkeypatch: Any
) -> None:
    def forbidden(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("Operator parsing must not launch a runtime or inspect native auth")

    monkeypatch.setattr("subprocess.run", forbidden)
    sdk = native_configuration(tmp_path, backend)
    if backend == "claude":
        sdk["providers"]["native"]["native_policy_reviewed"] = True
    write(tmp_path, sdk)
    loaded = load_agent_request_config(tmp_path)
    assert not is_refusal(loaded) and loaded.value is not None
    policy = loaded.value.policies["research-reader"]
    provider = loaded.value.providers[policy.provider_id]
    assert provider.capabilities.execution_kind == "agent_session"
    assert provider.capabilities.resume is True
    assert provider.capabilities.native_tools is False
    assert policy.provider_id.startswith("configured:native:")
    assert not (tmp_path / "native-home").exists()


@pytest.mark.parametrize(
    "change",
    [
        "backend",
        "relative",
        "same-directory",
        "api-key",
        "fallback",
        "native-tools",
        "no-tools",
        "workflow",
        "implicit-workflow",
        "claude-policy",
        "codex-policy",
    ],
)
def test_native_configuration_refuses_unsupported_capabilities_or_routing(
    tmp_path: Path, change: str
) -> None:
    sdk = native_configuration(tmp_path)
    row = sdk["providers"]["native"]
    if change == "backend":
        row["backend"] = "unreviewed"
    elif change == "relative":
        row["executable"] = "native.exe"
    elif change == "same-directory":
        row["empty_workspace"] = row["dedicated_home"]
    elif change in {"api-key", "fallback", "native-tools"}:
        row[
            {"api-key": "api_key_env", "fallback": "fallback", "native-tools": "native_tools"}[
                change
            ]
        ] = "fixture-refused"
    elif change == "no-tools":
        sdk["profiles"]["research-reader"]["tools"] = []
    elif change in {"workflow", "implicit-workflow"}:
        workflow: dict[str, Any] = {"specialist_id": "s", "version": "1", "instructions": "Read"}
        sdk["research_workflow"] = workflow
        if change == "workflow":
            workflow["profiles"] = ["research-reader"]
    elif change == "claude-policy":
        row["backend"] = "claude"
    else:
        row["native_policy_reviewed"] = True
    write(tmp_path, sdk)
    refused = load_agent_request_config(tmp_path)
    assert is_refusal(refused)
    assert "fixture-refused" not in repr(refused)


def test_native_paths_and_manifest_bind_the_accepted_identity(tmp_path: Path) -> None:
    sdk = native_configuration(tmp_path)
    write(tmp_path, sdk)
    first = load_agent_request_config(tmp_path)
    assert not is_refusal(first) and first.value is not None
    identity = first.value.policies["research-reader"].provider_id
    sdk["providers"]["native"]["empty_workspace"] = str(tmp_path / "another-empty")
    write(tmp_path, sdk)
    other = load_agent_request_config(tmp_path)
    assert not is_refusal(other) and other.value is not None
    assert other.value.policies["research-reader"].provider_id != identity
    sdk["research_browse"]["allowed_locators"] = ["different.md"]
    write(tmp_path, sdk)
    changed = load_agent_request_config(tmp_path)
    assert not is_refusal(changed) and changed.value is not None
    assert (
        changed.value.policies["research-reader"].provider_id
        != other.value.policies["research-reader"].provider_id
    )
    assert "fixture-refused" not in json.dumps(sdk)


def native_host(tmp_path: Path, *, second_profile: bool = False) -> Any:
    instance, contribution, snapshot = discover(tmp_path)
    sdk = sdk_config("http://127.0.0.1:9876/v1/chat/completions", instance, snapshot)
    sdk["providers"] = native_configuration(tmp_path)["providers"]
    sdk["profiles"] = {"app-reader": sdk["profiles"]["app-reader"]}
    sdk["profiles"]["app-reader"]["provider_id"] = "native"
    if second_profile:
        sdk["profiles"]["other-reader"] = dict(sdk["profiles"]["app-reader"])
    process = compose_configured(tmp_path, sdk, "native-gates")
    app_session(process, instance, contribution)
    return process


def test_missing_optional_native_dependency_refuses_without_api_fallback(
    tmp_path: Path, monkeypatch: Any
) -> None:
    import builtins

    from qma.daemon.request_runtime import CopilotProfile, RequestSpec

    original = builtins.__import__

    def without_sdk(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "native_composition":
            raise ImportError("synthetic missing optional SDK")
        return original(name, *args, **kwargs)

    process = native_host(tmp_path)
    try:
        runtime = process.agent_requests.runtime
        policy = process.agent_requests.policies["app-reader"]
        request = runtime.submit(
            RequestSpec(
                "missing-sdk",
                "operator",
                "psess:configured-app",
                0,
                CopilotProfile(
                    "app-reader", "application", app_instance_id=policy.profile.app_instance_id
                ),
                "Synthetic metadata",
                policy.provider_id,
            )
        )
        assert not is_refusal(request)
        monkeypatch.setattr(builtins, "__import__", without_sdk)
        result = runtime.execute(request.value.request_id)
        assert not is_refusal(result) and result.value.status == "failed"
        assert result.value.error == "unsupported"
    finally:
        process.close()


def test_native_wrapper_serializes_distinct_profiles_before_fresh_composition(
    tmp_path: Path, monkeypatch: Any
) -> None:
    pytest.importorskip("openai_codex")
    pytest.importorskip("claude_agent_sdk")
    from qma.daemon.request_runtime import (
        CopilotProfile,
        ProviderResult,
        RequestSpec,
        native_composition,
    )

    started, release = threading.Event(), threading.Event()
    compositions: list[Any] = []

    class ControlledNative:
        def execute(self, *_args: Any) -> ProviderResult:
            started.set()
            assert release.wait(5)
            return ProviderResult("Synthetic bounded result")

    def compose(*args: Any, **kwargs: Any) -> ControlledNative:
        compositions.append((args, kwargs))
        return ControlledNative()

    process = native_host(tmp_path, second_profile=True)
    thread = None
    try:
        runtime = process.agent_requests.runtime
        policy = process.agent_requests.policies["app-reader"]
        requests = [
            runtime.submit(
                RequestSpec(
                    key,
                    "operator",
                    "psess:configured-app",
                    0,
                    CopilotProfile(
                        profile_id, "application", app_instance_id=policy.profile.app_instance_id
                    ),
                    "Synthetic metadata",
                    policy.provider_id,
                )
            )
            for key, profile_id in (("first", "app-reader"), ("second", "other-reader"))
        ]
        assert all(not is_refusal(request) for request in requests)
        monkeypatch.setattr(native_composition, "compose_native_metadata_provider", compose)
        thread = threading.Thread(target=runtime.execute, args=(requests[0].value.request_id,))
        thread.start()
        assert started.wait(5)
        blocked = runtime.execute(requests[1].value.request_id)
        assert not is_refusal(blocked) and blocked.value.error == "session_busy"
        assert len(compositions) == 1
    finally:
        release.set()
        if thread is not None:
            thread.join(5)
        process.close()
