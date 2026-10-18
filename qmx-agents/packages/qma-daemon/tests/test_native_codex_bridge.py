"""Offline native bridge checks through the actual released CodexClient."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import threading
import time
from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

pytest.importorskip("openai_codex", reason="Install examples/native-session-requirements.lock")
pytest.importorskip("claude_agent_sdk", reason="Install examples/native-session-requirements.lock")

from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage, TextBlock
from openai_codex.client import CodexClient, CodexConfig
from qma.daemon.request_runtime import native_claude, native_composition
from qma.daemon.request_runtime.contracts import CopilotProfile, ProviderRequest, RequestSpec
from qma.daemon.request_runtime.native_claude import ClaudeSessionBackend
from qma.daemon.request_runtime.native_codex import CONFIG, CodexSessionBackend
from qma.daemon.request_runtime.native_sessions import NativeSessionProvider, SessionEvent
from qma.daemon.request_runtime.providers import ProviderError
from test_native_sessions import FakeBackend, FakeClaudeClient, native_host
from test_research_workflow import value

SCHEMA = {
    "type": "object",
    "properties": {"snapshot_ref": {"type": "string"}},
    "required": ["snapshot_ref"],
    "additionalProperties": False,
}


def proof_module() -> Any:
    path = Path(__file__).resolve().parents[3] / "examples" / "native_session_proof.py"
    spec = importlib.util.spec_from_file_location("native_session_proof_offline", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_proof_default_makes_no_model_auth_or_store_calls(tmp_path: Path, monkeypatch: Any) -> None:
    proof = proof_module()

    def forbidden(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("Dry proof cannot construct a native provider")

    monkeypatch.setattr(proof, "compose_native_metadata_provider", forbidden)
    assert (
        proof.main(
            [
                "--provider",
                "codex",
                "--executable",
                str(tmp_path / "absent-cli.exe"),
                "--native-home",
                str(tmp_path / "home"),
                "--empty-workspace",
                str(tmp_path / "workspace"),
                "--root",
                str(tmp_path / "proof"),
            ]
        )
        == 0
    )
    assert not list(tmp_path.iterdir())


def test_proof_two_turn_path_real_sdk_and_observed_host_receipt(
    tmp_path: Path, monkeypatch: Any
) -> None:
    proof = proof_module()
    home, workspace, trace = tmp_path / "home", tmp_path / "workspace", tmp_path / "protocol.jsonl"
    home.mkdir()
    workspace.mkdir()

    def backend_factory(**options: Any) -> CodexSessionBackend:
        arguments = {
            "snapshot_ref": options["tool_schemas"]["research_browse"]["properties"][
                "snapshot_ref"
            ]["enum"][0]
        }

        def client_factory(*, config: CodexConfig, approval_handler: Any) -> CodexClient:
            config.launch_args_override = (
                sys.executable,
                str(Path(__file__).with_name("native_codex_fixture.py")),
                json.dumps(CONFIG),
                json.dumps(arguments),
                "proof",
                str(workspace),
                str(trace),
            )
            return CodexClient(config=config, approval_handler=approval_handler)

        return CodexSessionBackend(**options, client_factory=client_factory, verify_runtime=False)

    monkeypatch.setattr(native_composition, "CodexSessionBackend", backend_factory)
    assert (
        proof.main(
            [
                "--provider",
                "codex",
                "--executable",
                str(tmp_path / "fake-cli.exe"),
                "--native-home",
                str(home),
                "--empty-workspace",
                str(workspace),
                "--root",
                str(tmp_path / "proof"),
                "--allow-live",
            ]
        )
        == 0
    )
    report = json.loads((tmp_path / "proof" / "proof-result.json").read_text())
    assert report["host_operations"] == 1 and len(report["effect_receipts"]) == 1
    assert report["effect_receipts"][0]["body"]["status"] == "observed"
    transcript = [json.loads(line) for line in trace.read_text().splitlines()]
    turns = [row["params"] for row in transcript if row.get("method") == "turn/start"]
    assert len(turns) == 2
    assert "NATIVE-PROOF-" in json.dumps(turns[0]) and "NATIVE-PROOF-" not in json.dumps(turns[1])
    assert sum(row.get("method") == "thread/resume" for row in transcript) == 1


def submit(runtime: Any, key: str = "one") -> str:
    return value(
        runtime.submit(
            RequestSpec(
                key,
                "operator",
                "psess:desk-1",
                0,
                CopilotProfile(
                    "reader", instructions="Host restrictions for reader: no unsupported claims."
                ),
                "Assess supplied hypothesis",
                "research",
                timeout_seconds=3,
            )
        )
    ).request_id


def bridge_host(tmp_path: Path, *, scenario: str = "normal") -> Any:
    placeholder = FakeBackend()
    substrate, journal, runtime, old_provider, observed = native_host(tmp_path, placeholder)
    home, workspace = tmp_path / "native-home", tmp_path / "empty-workspace"
    home.mkdir()
    workspace.mkdir()
    configurations: list[CodexConfig] = []

    def factory(*, config: CodexConfig, approval_handler: Any) -> CodexClient:
        configurations.append(config)
        config.launch_args_override = (
            sys.executable,
            str(Path(__file__).with_name("native_codex_fixture.py")),
            json.dumps(CONFIG),
            json.dumps(placeholder.arguments),
            scenario,
            str(workspace),
            str(tmp_path / "protocol.jsonl"),
        )
        return CodexClient(config=config, approval_handler=approval_handler)

    backends: list[CodexSessionBackend] = []

    def backend() -> CodexSessionBackend:
        driver = CodexSessionBackend(
            executable=tmp_path / "codex.exe",
            dedicated_home=home,
            empty_workspace=workspace,
            tool_schemas={"research_browse": SCHEMA},
            client_factory=factory,
            verify_runtime=False,
        )
        backends.append(driver)
        return driver

    provider = NativeSessionProvider(
        backend,
        provider_id="research",
        now=old_provider.now,
        tools=old_provider.tools,
        profile_tools=old_provider.profile_tools,
    )
    provider.bind_runtime(runtime)
    runtime.providers["research"] = provider
    return substrate, journal, runtime, provider, observed, configurations, backends


def test_codex_released_transport_host_operation_start_and_resume(tmp_path: Path) -> None:
    substrate, _, runtime, provider, observed, configurations, backends = bridge_host(tmp_path)
    try:
        first = value(runtime.execute(submit(runtime)))
        assert first.status == "completed", first
        second = value(runtime.execute(submit(runtime, key="two")))
        assert second.status == "completed", second
        assert first.result.thread_id == second.result.thread_id == "sdk-thread-1"
        assert len(observed) == 2 and provider.capabilities.resume
        assert not provider.capabilities.native_tools
        assert all(backend.client is None for backend in backends)
        assert all(
            'forced_login_method="chatgpt"' in config.config_overrides for config in configurations
        )
        assert all("features.hooks=false" in config.config_overrides for config in configurations)
        transcript = [
            json.loads(line) for line in (tmp_path / "protocol.jsonl").read_text().splitlines()
        ]
        resumed = [row for row in transcript if row.get("method") == "thread/resume"]
        assert len(resumed) == 1 and resumed[0]["params"]["threadId"] == first.result.thread_id
        assert "dynamicTools" not in resumed[0]["params"]
    finally:
        substrate.close()


@pytest.mark.parametrize(
    "scenario",
    [
        "unsafe-config",
        "api-account",
        "wrong-terminal",
        "approval",
        "permissions",
        "unknown-request",
        "subagent",
        "wrong-tool-id",
        "forbidden-terminal",
        "wrong-initialize",
        "withheld-config",
    ],
)
def test_codex_unexpected_authority_config_or_identity_fails_closed(
    tmp_path: Path, scenario: str
) -> None:
    substrate, _, runtime, _, observed, _, _ = bridge_host(tmp_path, scenario=scenario)
    try:
        result = value(runtime.execute(submit(runtime)))
        assert result.status != "completed", result
        assert len(observed) == (1 if scenario in {"wrong-terminal", "forbidden-terminal"} else 0)
        expected = {
            "unsafe-config": "unsafe_config",
            "api-account": "auth_required",
            "wrong-initialize": "unsafe_config",
        }.get(scenario, "outcome_unknown")
        assert value(runtime.execute(submit(runtime, key="two"))).error == expected
    finally:
        substrate.close()


def test_codex_cancel_observes_interrupted_terminal(tmp_path: Path) -> None:
    substrate, _, runtime, provider, observed, _, backends = bridge_host(tmp_path, scenario="wait")
    request_id = submit(runtime)
    original_factory = provider.backend_factory

    class CancelBackend(CodexSessionBackend):
        async def events(self) -> AsyncIterator[SessionEvent]:
            async for event in super().events():
                if event.kind == "started":
                    value(runtime.cancel(request_id))
                yield event

    def factory() -> CodexSessionBackend:
        driver = original_factory()
        driver.__class__ = CancelBackend
        return driver

    provider.backend_factory = factory
    try:
        row = value(runtime.execute(request_id))
        assert row.status == "cancelled", row
        assert not observed and all(backend.client is None for backend in backends)
    finally:
        substrate.close()


@pytest.mark.parametrize("scope", ["revoked", "expired"])
def test_codex_callback_checks_real_current_host_scope(tmp_path: Path, scope: str) -> None:
    substrate, _, runtime, provider, observed, _, _ = bridge_host(tmp_path)
    original_factory = provider.backend_factory

    class ChangedScope(CodexSessionBackend):
        async def _host_call(self, params: Any) -> Any:
            if scope == "expired":
                provider.now = lambda: "2099-01-01T00:00:00Z"
            else:
                value(
                    runtime.product_sessions.revoke_grant(
                        "psess:desk-1",
                        grant_id="grant:1",
                        principal="operator",
                        reason="fixture",
                        revoked_at="2026-10-04T00:00:00Z",
                    )
                )
            return await super()._host_call(params)

    def factory() -> CodexSessionBackend:
        driver = original_factory()
        driver.__class__ = ChangedScope
        return driver

    provider.backend_factory = factory
    try:
        row = value(runtime.execute(submit(runtime)))
        assert row.status != "completed" and not observed, row
    finally:
        substrate.close()


@pytest.mark.parametrize("key", ["OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"])
def test_codex_no_paid_fallback_or_credential_inspection(
    tmp_path: Path, monkeypatch: Any, key: str
) -> None:
    substrate, _, runtime, _, observed, configurations, _ = bridge_host(tmp_path)
    monkeypatch.setenv(key, "unread-fixture-value")
    try:
        row = value(runtime.execute(submit(runtime)))
        assert row.status != "completed" and not configurations and not observed
    finally:
        substrate.close()


def test_claude_public_supplied_text_requires_scoped_policy_review(tmp_path: Path) -> None:
    home, workspace = tmp_path / "home", tmp_path / "workspace"
    home.mkdir()
    workspace.mkdir()
    options: dict[str, Any] = {
        "executable": tmp_path / "claude.exe",
        "dedicated_home": home,
        "empty_workspace": workspace,
        "client_factory": FakeClaudeClient,
        "verify_runtime": False,
    }
    driver = ClaudeSessionBackend(**options)
    assert not driver.available
    with pytest.raises(ProviderError, match="policy review"):
        asyncio.run(driver.start(ProviderRequest("hello"), lambda: None, check=lambda: None))
    driver = ClaudeSessionBackend(**options, native_policy_reviewed=True)
    assert driver.available

    async def scenario() -> None:
        await driver.start(
            ProviderRequest("hello", cwd="untrusted-model-workspace"),
            lambda: None,
            check=lambda: None,
        )
        assert driver.client.options.cwd == str(workspace)
        assert driver.client.options.tools == [] and not driver.client.options.fallback_model
        first = [event async for event in driver.events()]
        await driver.close()
        await driver.resume(
            first[0].session_id, ProviderRequest("resume"), lambda: None, check=lambda: None
        )
        assert driver.client.options.resume == first[0].session_id
        await driver.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("backend_type", [CodexSessionBackend, ClaudeSessionBackend])
def test_slow_preflight_cannot_launch_after_deadline(
    tmp_path: Path, backend_type: Any, monkeypatch: Any
) -> None:
    clients: list[Any] = []

    def create_client(**_kwargs: Any) -> Any:
        clients.append(True)
        raise AssertionError("Client cannot be created after preflight deadline")

    options: dict[str, Any] = {
        "executable": tmp_path / "cli.exe",
        "dedicated_home": tmp_path / "home",
        "empty_workspace": tmp_path / "workspace",
        "client_factory": create_client,
    }
    if backend_type is ClaudeSessionBackend:
        options["native_policy_reviewed"] = True
    driver = backend_type(**options)

    def slow_preflight(*_args: Any) -> None:
        time.sleep(0.15)

    monkeypatch.setattr(driver, "_preflight", slow_preflight)

    async def scenario() -> None:
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(
                driver.start(ProviderRequest("fixture"), lambda: None, check=lambda: None), 0.02
            )
        await driver.close()

    started = time.monotonic()
    asyncio.run(scenario())
    assert time.monotonic() - started < 0.12 and not clients


@pytest.mark.parametrize(
    "auth_method", ["claude.ai", "api_key", "api_key_helper", "third_party", "oauth_token"]
)
def test_claude_native_auth_metadata_prevents_api_routing(
    tmp_path: Path, monkeypatch: Any, auth_method: str
) -> None:
    home, workspace = tmp_path / "home", tmp_path / "workspace"
    home.mkdir()
    workspace.mkdir()
    commands: list[list[str]] = []

    def run(command: list[str], **_kwargs: Any) -> Any:
        commands.append(command)
        if command[-1] == "--version":
            return SimpleNamespace(stdout="2.1.299 (Claude Code)", returncode=0)
        assert command[-2:] == ["auth", "status"]
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "loggedIn": True,
                    "authMethod": auth_method,
                    "apiProvider": "firstParty",
                    "configDirectory": str(home),
                }
            ),
        )

    monkeypatch.setattr(native_claude.subprocess, "run", run)
    driver = ClaudeSessionBackend(
        executable=tmp_path / "claude.exe",
        dedicated_home=home,
        empty_workspace=workspace,
        native_policy_reviewed=True,
        client_factory=FakeClaudeClient,
    )

    async def scenario() -> None:
        if auth_method == "claude.ai":
            await driver.start(ProviderRequest("fixture"), lambda: None, check=lambda: None)
            assert driver.client is not None
            await driver.close()
        else:
            with pytest.raises(ProviderError, match="subscription"):
                await driver.start(ProviderRequest("fixture"), lambda: None, check=lambda: None)
            assert driver.client is None

    asyncio.run(scenario())
    assert len(commands) == 2  # Both native commands were fakes; no actual auth read.
    (workspace / "money-config.txt").write_text("fixture")
    with pytest.raises(ProviderError, match="empty workspace"):
        asyncio.run(driver.start(ProviderRequest("hello"), lambda: None, check=lambda: None))


def test_codex_startup_cancellation_waits_for_turn_identity(tmp_path: Path) -> None:
    substrate, _, runtime, provider, observed, _, _ = bridge_host(tmp_path, scenario="delayed-turn")
    original_factory = provider.backend_factory

    def factory() -> CodexSessionBackend:
        driver = original_factory()
        original = driver._sdk_call  # pyright: ignore[reportPrivateUsage] - precise SDK start race

        async def call(function: Any, *args: Any, **kwargs: Any) -> Any:
            if function.__name__ == "turn_start":
                threading.Timer(0.02, cancel_scope.set).start()
            return await original(function, *args, **kwargs)

        driver._sdk_call = call  # pyright: ignore[reportPrivateUsage] - offline race injection
        return driver

    cancel_scope = threading.Event()
    provider.backend_factory = factory
    request_id = submit(runtime)

    def cancel_after_send() -> None:
        cancel_scope.wait(timeout=2)
        value(runtime.cancel(request_id))

    cancellation = threading.Thread(target=cancel_after_send)
    cancellation.start()
    try:
        row = value(runtime.execute(request_id))
        cancellation.join(timeout=2)
        assert row.status == "cancelled" and not observed, row
        transcript = (tmp_path / "protocol.jsonl").read_text()
        assert '"method": "turn/interrupt"' in transcript
    finally:
        substrate.close()


def test_codex_terminal_text_fallback(tmp_path: Path) -> None:
    substrate, _, runtime, _, _, _, _ = bridge_host(tmp_path, scenario="no-delta")
    try:
        result = value(runtime.execute(submit(runtime)))
        assert result.status == "completed" and result.result.content == "Metadata received", result
    finally:
        substrate.close()


def test_codex_late_start_fenced_and_no_executor_shutdown_hang(tmp_path: Path) -> None:
    class SlowClient:
        alive = False

        def start(self) -> None:
            time.sleep(0.2)
            self.alive = True

        def close(self) -> None:
            self.alive = False

    client = SlowClient()
    driver = CodexSessionBackend()
    driver.client = client  # type: ignore[assignment] # pyright: ignore[reportAttributeAccessIssue] - SDK-compatible fake lifecycle

    async def scenario() -> None:
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(driver._sdk_call(driver._start_client), 0.02)  # pyright: ignore[reportPrivateUsage] - late launch seam
        await driver.close()

    started = time.monotonic()
    asyncio.run(scenario())
    assert not client.alive and time.monotonic() - started < 1


@pytest.mark.parametrize(
    "mode", ["peer", "channel", "observer", "unclassified", "wrong-assistant", "task_started"]
)
def test_claude_rejects_injected_or_wrong_session_messages(tmp_path: Path, mode: str) -> None:
    home, workspace = tmp_path / "home", tmp_path / "workspace"
    home.mkdir()
    workspace.mkdir()

    class Client(FakeClaudeClient):
        async def receive_response(self) -> Any:
            yield SystemMessage("init", {"session_id": self.session_id, "tools": []})
            if mode == "wrong-assistant":
                yield AssistantMessage(
                    [TextBlock("wrong")], "fixture", session_id="another-session"
                )
            elif mode == "task_started":
                yield SystemMessage("task_started", {"session_id": self.session_id})
            else:
                yield ResultMessage(
                    "success", 1, 1, False, 1, self.session_id, origin=cast("Any", {"kind": mode})
                )  # pyright: ignore[reportArgumentType] - documented/unknown injected origin

    driver = ClaudeSessionBackend(
        executable=tmp_path / "claude.exe",
        dedicated_home=home,
        empty_workspace=workspace,
        native_policy_reviewed=True,
        client_factory=Client,
        verify_runtime=False,
    )

    async def scenario() -> None:
        await driver.start(ProviderRequest("hello"), lambda: None, check=lambda: None)
        with pytest.raises(ProviderError, match="refused"):
            _ = [event async for event in driver.events()]
        await driver.close()

    asyncio.run(scenario())
