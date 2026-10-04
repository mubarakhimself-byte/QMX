"""Official SDK-compatible fakes and real QMX host admission, never inference."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import anyio
import pytest

pytest.importorskip("claude_agent_sdk", reason="Install examples/native-session-requirements.lock")
pytest.importorskip("openai_codex", reason="Install examples/native-session-requirements.lock")

from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage, TextBlock
from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams
from mcp.types import TextContent
from openai_codex import AsyncCodex
from openai_codex.generated.v2_all import (
    AgentMessageDeltaNotification,
    TurnCompletedNotification,
)
from qma.daemon.request_runtime.contracts import ProviderRequest
from qma.daemon.request_runtime.native_claude import (
    ClaudeSessionBackend,
    _ClaudeSDKLifecycle,  # pyright: ignore[reportPrivateUsage] - offline-only lifecycle review
)
from qma.daemon.request_runtime.native_codex import (
    CodexSessionBackend,
    _CodexSDKLifecycle,  # pyright: ignore[reportPrivateUsage] - offline-only lifecycle review
)
from qma.daemon.request_runtime.native_sessions import NativeSessionProvider, SessionEvent
from qma.daemon.request_runtime.providers import ProviderError
from test_research_workflow import compose, submit, supply, value


class FakeBackend:
    available = True
    provider_id = "native-fixture"
    binding_identity = "native-fixture:scope-1"

    def __init__(self) -> None:
        self.starts = 0
        self.resumes: list[str] = []
        self.cancelled = asyncio.Event()
        self.closed = False
        self.mode = "normal"
        self.before_tool: Any = None
        self.after_start: Any = None
        self.operation: Any = None
        self.arguments: dict[str, Any] = {}

    async def start(self, request: ProviderRequest, operation: Any, *, check: Any) -> None:
        check()
        self.starts += 1
        self.operation = operation

    async def resume(
        self, session_id: str, request: ProviderRequest, operation: Any, *, check: Any
    ) -> None:
        check()
        self.resumes.append(session_id)
        self.operation = operation

    async def events(self) -> AsyncIterator[SessionEvent]:
        yield SessionEvent("started", "native-session-1", "native-turn-1")
        if self.after_start:
            self.after_start()
        if self.mode == "wait":
            await self.cancelled.wait()
            yield SessionEvent("text", "native-session-1", text="late forbidden text")
            yield SessionEvent("terminal", "native-session-1", status="interrupted")
            return
        if self.mode == "missing":
            return
        if self.before_tool:
            self.before_tool()
        if self.mode != "no-tool":
            await self.operation(
                "research_browse",
                self.arguments,
                "call-1",
                agent_id="subagent-1" if self.mode == "subagent" else None,
            )
        yield SessionEvent("text", "native-session-1", text="Bounded observation")
        yield SessionEvent(
            "terminal",
            "wrong-id" if self.mode == "wrong-id" else "native-session-1",
            status="completed",
        )

    async def cancel(self) -> None:
        self.cancelled.set()

    async def close(self) -> None:
        self.closed = True


def native_host(tmp_path: Path, backend: FakeBackend) -> Any:
    substrate, journal, runtime, _, workflow, observed = compose(
        tmp_path / "store", supply(tmp_path)
    )
    backend.arguments = workflow.operation_arguments
    provider = NativeSessionProvider(
        lambda: backend,
        provider_id="research",
        now=lambda: "2026-10-04T00:00:00Z",
        tools={"research_browse": workflow.operation},
        profile_tools={"reader": frozenset({"research_browse"})},
    )
    runtime.providers["research"] = provider
    provider.bind_runtime(runtime)
    return substrate, journal, runtime, provider, observed


def test_native_start_resume_real_domain_receipts_and_restart(tmp_path: Path) -> None:
    backend = FakeBackend()
    substrate, journal, runtime, provider, observed = native_host(tmp_path, backend)
    try:
        first = value(runtime.execute(submit(runtime)))
        assert first.status == "completed", first
        assert first.result.thread_id == "native-session-1"
        assert provider.results(first.request_id) == first.result
        second = value(runtime.execute(submit(runtime, key="two")))
        assert second.status == "completed", second
        assert backend.starts == 1 and backend.resumes == ["native-session-1"]
        assert len(observed) == 2  # Distinct admitted jobs have distinct effect identities.
        # Reopen the disk substrate and journal, not just the adapter object.
        journal.close()
        substrate.close()
        substrate, journal, runtime, _, workflow, _ = compose(
            tmp_path / "store", tmp_path / "corpus", restore=True
        )
        replacement = NativeSessionProvider(
            lambda: backend,
            provider_id="research",
            now=provider.now,
            tools={"research_browse": workflow.operation},
            profile_tools=provider.profile_tools,
        )
        replacement.bind_runtime(runtime)
        runtime.providers["research"] = replacement
        third = value(runtime.execute(submit(runtime, key="three")))
        assert third.status == "completed"
        assert backend.resumes == ["native-session-1", "native-session-1"]
        assert value(journal.read_events())
    finally:
        substrate.close()


@pytest.mark.parametrize("mode", ["missing", "wrong-id", "subagent"])
def test_native_unknown_never_replays_or_falls_back(tmp_path: Path, mode: str) -> None:
    backend = FakeBackend()
    backend.mode = mode
    substrate, _, runtime, _, observed = native_host(tmp_path, backend)
    try:
        first = value(runtime.execute(submit(runtime)))
        assert first.status in {"interrupted", "failed"}
        second = value(runtime.execute(submit(runtime, key="two")))
        assert second.status == "interrupted" and second.error == "outcome_unknown"
        assert backend.starts == 1 and not backend.resumes
        assert len(observed) == (1 if mode == "wrong-id" else 0)
    finally:
        substrate.close()


def test_native_cancel_drains_matching_terminal(tmp_path: Path) -> None:
    backend = FakeBackend()
    backend.mode = "wait"
    substrate, _, runtime, _, observed = native_host(tmp_path, backend)
    try:
        request_id = submit(runtime)
        backend.after_start = lambda: value(runtime.cancel(request_id))
        row = value(runtime.execute(request_id))
        assert row.status == "cancelled" and row.error == "cancelled", row
        assert backend.cancelled.is_set() and backend.closed and not observed
    finally:
        substrate.close()


@pytest.mark.parametrize("scope_change", ["revoked", "expired"])
def test_native_operation_rechecks_live_scope(tmp_path: Path, scope_change: str) -> None:
    backend = FakeBackend()
    substrate, _, runtime, provider, observed = native_host(tmp_path, backend)
    try:
        request_id = submit(runtime)
        if scope_change == "expired":
            backend.before_tool = lambda: setattr(provider, "now", lambda: "2099-01-01T00:00:00Z")
        else:
            backend.before_tool = lambda: value(
                runtime.product_sessions.revoke_grant(
                    "psess:desk-1",
                    grant_id="grant:1",
                    principal="operator",
                    reason="test",
                    revoked_at="2026-10-04T00:00:00Z",
                )
            )
        row = value(runtime.execute(request_id))
        assert row.status != "completed" and not observed
    finally:
        substrate.close()


def test_codex_public_backend_cannot_launch_or_claim_resume(tmp_path: Path) -> None:
    backend = CodexSessionBackend()
    assert not backend.available
    with pytest.raises(ProviderError, match="isolation"):
        asyncio.run(backend.start(ProviderRequest("hello"), lambda: None, check=lambda: None))
    provider = NativeSessionProvider(
        CodexSessionBackend, provider_id=backend.provider_id, now=lambda: ""
    )
    assert not provider.capabilities.resume


class FakeClaudeClient:
    def __init__(self, *, options: Any) -> None:
        self.options = options
        self.interrupted = False
        self.disconnected = False
        self.prompt = ""
        self.session_id = options.resume or "claude-session-1"

    async def connect(self) -> None:
        return

    async def query(self, prompt: str) -> None:
        self.prompt = prompt

    async def receive_response(self) -> Any:
        yield SystemMessage(
            "init", {"session_id": self.session_id, "tools": self.options.allowed_tools}
        )
        yield AssistantMessage([TextBlock("hello")], "fixture")
        yield ResultMessage(
            "success",
            1,
            1,
            False,
            1,
            self.session_id,
            terminal_reason="aborted_streaming" if self.interrupted else "completed",
        )

    async def interrupt(self) -> None:
        self.interrupted = True

    async def disconnect(self) -> None:
        self.disconnected = True


def test_claude_sdk_options_remove_native_access_and_resume_verbatim(tmp_path: Path) -> None:
    async def scenario() -> None:
        driver = _ClaudeSDKLifecycle(
            executable=tmp_path / "claude.exe",
            dedicated_home=tmp_path,
            client_factory=FakeClaudeClient,
            verify_runtime=False,
        )
        request = ProviderRequest("@private.txt /command", cwd=str(tmp_path))
        await driver.resume("claude-session-1", request, lambda: None, check=lambda: None)
        client = driver.client
        options = client.options
        assert options.tools == [] and options.setting_sources == []
        assert options.skills == [] and options.plugins == [] and options.agents == {}
        assert options.strict_mcp_config and options.verbatim_prompts
        assert options.fallback_model is None and options.permission_mode == "dontAsk"
        command = SubprocessCLITransport("", options)._build_command()  # pyright: ignore[reportPrivateUsage] - verify released flag construction
        assert command[command.index("--tools") + 1] == ""
        assert "--strict-mcp-config" in command and "--setting-sources=" in command
        assert client.prompt == request.prompt
        events = [event async for event in driver.events()]
        assert events[-1].status == "completed" and events[0].session_id == "claude-session-1"
        hook = options.hooks["PreToolUse"][0].hooks[0]
        denied = await hook({"tool_name": "Bash", "agent_id": "child"}, None, {})
        assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"
        await driver.cancel()
        interrupted = [event async for event in driver.events()]
        assert interrupted[-1].status == "interrupted"
        await driver.close()
        assert client.disconnected

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "key",
    ["ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "CLAUDE_CODE_USE_BEDROCK"],
)
def test_claude_refuses_api_environment_without_reading_values(
    tmp_path: Path, monkeypatch: Any, key: str
) -> None:
    monkeypatch.setenv(key, "do-not-read")
    driver = _ClaudeSDKLifecycle(
        executable=tmp_path / "claude.exe",
        dedicated_home=tmp_path,
        client_factory=FakeClaudeClient,
        verify_runtime=False,
    )
    with pytest.raises(ProviderError, match="API routing"):
        asyncio.run(driver.start(ProviderRequest("hello"), lambda: None, check=lambda: None))
    assert driver.client is None


def test_codex_official_typed_lifecycle_and_interrupt() -> None:
    class Turn:
        id = "turn-1"
        interrupted = False

        async def interrupt(self) -> None:
            self.interrupted = True

        async def stream(self) -> Any:
            yield SimpleNamespace(
                payload=AgentMessageDeltaNotification.model_validate(
                    {
                        "threadId": "thread-1",
                        "turnId": "turn-1",
                        "itemId": "item-1",
                        "delta": "hi",
                    }
                )
            )
            yield SimpleNamespace(
                payload=TurnCompletedNotification.model_validate(
                    {
                        "threadId": "thread-1",
                        "turn": {
                            "id": "turn-1",
                            "items": [],
                            "status": "interrupted" if self.interrupted else "completed",
                        },
                    }
                )
            )

    class Thread:
        id = "thread-1"

        async def turn(self, prompt: str) -> Any:
            assert prompt == "hello"
            return turn

    class Client:
        def __init__(self) -> None:
            self.resumed: list[str] = []

        async def thread_start(self, **kwargs: Any) -> Any:
            assert kwargs["approval_mode"].value == "deny_all"
            return Thread()

        async def thread_resume(self, session_id: str, **kwargs: Any) -> Any:
            self.resumed.append(session_id)
            return Thread()

        async def close(self) -> None:
            return

    turn = Turn()
    client = Client()
    driver = _CodexSDKLifecycle(cast("AsyncCodex", client))

    async def scenario() -> None:
        await driver.start(ProviderRequest("hello"), lambda: None)
        events = [event async for event in driver.events()]
        assert events[-1].status == "completed"
        await driver.resume("thread-1", ProviderRequest("hello"), lambda: None)
        await driver.cancel()
        events = [event async for event in driver.events()]
        assert events[-1].status == "interrupted" and client.resumed == ["thread-1"]
        await driver.close()

    asyncio.run(scenario())


def test_claude_public_backend_cannot_launch() -> None:
    backend = ClaudeSessionBackend()
    assert not backend.available
    with pytest.raises(ProviderError, match="isolation"):
        asyncio.run(backend.start(ProviderRequest("hello"), lambda: None, check=lambda: None))
    provider = NativeSessionProvider(
        ClaudeSessionBackend, provider_id=backend.provider_id, now=lambda: ""
    )
    assert not provider.capabilities.resume


def test_claude_checks_scope_after_connect_before_query(tmp_path: Path) -> None:
    driver = _ClaudeSDKLifecycle(
        executable=tmp_path / "claude.exe",
        dedicated_home=tmp_path,
        client_factory=FakeClaudeClient,
        verify_runtime=False,
    )
    calls = 0

    def check() -> None:
        nonlocal calls
        calls += 1
        if calls > 2:
            raise ProviderError("scope_interrupt", "Scope revoked during connect")

    async def scenario() -> None:
        with pytest.raises(ProviderError, match="revoked"):
            await driver.start(ProviderRequest("hello"), lambda: None, check=check)
        assert driver.client.prompt == ""
        await driver.close()

    asyncio.run(scenario())


def test_sdk_mcp_server_real_host_operation_and_resume(tmp_path: Path) -> None:
    """Real released SDK MCP server and protocol client; native process is a fake."""
    placeholder = FakeBackend()
    substrate, _, runtime, old_provider, observed = native_host(tmp_path, placeholder)
    snapshot_args = dict(placeholder.arguments)
    clients: list[Any] = []

    class Client(FakeClaudeClient):
        async def receive_response(self) -> Any:
            yield SystemMessage(
                "init", {"session_id": self.session_id, "tools": self.options.allowed_tools}
            )
            server = self.options.mcp_servers["qmx"]["instance"]
            async with (
                create_client_server_memory_streams() as (client_streams, server_streams),
                anyio.create_task_group() as group,
            ):
                group.start_soon(
                    server.run, *server_streams, server.create_initialization_options()
                )
                async with ClientSession(*client_streams) as session:
                    await session.initialize()
                    result = await session.call_tool("research_browse", snapshot_args)
                    assert not result.is_error
                    assert isinstance(result.content[0], TextContent)
                    assert "visible.md" in result.content[0].text
                group.cancel_scope.cancel()
            yield AssistantMessage([TextBlock("SDK host observation received")], "fixture")
            yield ResultMessage(
                "success", 1, 1, False, 1, self.session_id, terminal_reason="completed"
            )

    def client_factory(**kwargs: Any) -> Client:
        client = Client(**kwargs)
        clients.append(client)
        return client

    class OfflineLifecycle(_ClaudeSDKLifecycle):
        available = True  # Test-only; public production backend has no enabling switch.

    provider = NativeSessionProvider(
        lambda: OfflineLifecycle(
            executable=tmp_path / "claude.exe",
            dedicated_home=tmp_path,
            tool_schemas={
                "research_browse": {
                    "type": "object",
                    "properties": {"snapshot_ref": {"type": "string"}},
                    "required": ["snapshot_ref"],
                    "additionalProperties": False,
                }
            },
            client_factory=client_factory,
            verify_runtime=False,
        ),
        provider_id="research",
        now=old_provider.now,
        tools=old_provider.tools,
        profile_tools=old_provider.profile_tools,
    )
    provider.bind_runtime(runtime)
    runtime.providers["research"] = provider
    try:
        first = value(runtime.execute(submit(runtime)))
        assert first.status == "completed", first
        second = value(runtime.execute(submit(runtime, key="two")))
        assert second.status == "completed", second
        assert len(observed) == 2
        assert clients[0].options.resume is None
        assert clients[1].options.resume == first.result.thread_id
        assert all(client.disconnected for client in clients)
    finally:
        substrate.close()


def test_cleanup_deadline_and_unknown_terminal_not_replayed(tmp_path: Path) -> None:
    class StalledCleanup(FakeBackend):
        async def close(self) -> None:
            await asyncio.Event().wait()

    backend = StalledCleanup()
    backend.mode = "missing"
    substrate, _, runtime, _, _ = native_host(tmp_path, backend)
    try:
        row = value(runtime.execute(submit(runtime)))
        assert row.status == "interrupted" and row.error == "outcome_unknown"
        assert value(runtime.execute(submit(runtime, key="two"))).error == "outcome_unknown"
        assert backend.starts == 1
    finally:
        substrate.close()


def test_resume_binding_changes_start_fresh_instead_of_reusing_context(tmp_path: Path) -> None:
    backend = FakeBackend()
    substrate, _, runtime, _, _ = native_host(tmp_path, backend)
    try:
        assert value(runtime.execute(submit(runtime))).status == "completed"
        backend.binding_identity = "native-fixture:another-native-home"
        assert value(runtime.execute(submit(runtime, key="two"))).status == "completed"
        assert backend.starts == 2 and not backend.resumes
    finally:
        substrate.close()


def test_result_access_after_revocation_is_refused(tmp_path: Path) -> None:
    backend = FakeBackend()
    substrate, _, runtime, provider, _ = native_host(tmp_path, backend)
    try:
        first = value(runtime.execute(submit(runtime)))
        assert provider.results(first.request_id) == first.result
        value(
            runtime.product_sessions.revoke_grant(
                "psess:desk-1",
                grant_id="grant:1",
                principal="operator",
                reason="test",
                revoked_at="2026-10-04T00:00:00Z",
            )
        )
        with pytest.raises(ProviderError, match="scope"):
            provider.results(first.request_id)
    finally:
        substrate.close()


def test_cancellation_during_connect_prevents_query(tmp_path: Path) -> None:
    backend = FakeBackend()
    substrate, _, runtime, provider, observed = native_host(tmp_path, backend)
    request_id = submit(runtime)

    class ConnectingBackend(FakeBackend):
        queried = False

        async def start(self, request: ProviderRequest, operation: Any, *, check: Any) -> None:
            self.starts += 1
            value(runtime.cancel(request_id))
            await asyncio.sleep(0.12)
            check()
            self.queried = True

    connecting = ConnectingBackend()
    provider.backend_factory = lambda: connecting
    try:
        row = value(runtime.execute(request_id))
        assert row.status == "interrupted" and row.error == "outcome_unknown"
        assert connecting.cancelled.is_set() and not connecting.queried and not observed
    finally:
        substrate.close()


def test_cancellation_during_active_validation_preserves_observed_interrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = FakeBackend()
    backend.mode = "wait"
    substrate, _, runtime, _, observed = native_host(tmp_path, backend)
    request_id = submit(runtime)
    original_validate = runtime.validate_active_request
    raced = False

    def cancel_before_validation(current: str, *, now: str) -> Any:
        nonlocal raced
        if backend.starts and not raced:
            raced = True
            # The provider guard has already read the unset token. Canonical
            # validation now observes the cancellation committed by the host.
            value(runtime.cancel(request_id))
        return original_validate(current, now=now)

    monkeypatch.setattr(runtime, "validate_active_request", cancel_before_validation)
    try:
        row = value(runtime.execute(request_id))
        assert raced and row.status == "cancelled" and row.error == "cancelled", row
        assert backend.cancelled.is_set() and backend.closed and not observed
    finally:
        substrate.close()


def test_completed_native_terminal_wins_cancellation_race(tmp_path: Path) -> None:
    backend = FakeBackend()
    backend.mode = "no-tool"
    substrate, _, runtime, _, observed = native_host(tmp_path, backend)
    try:
        request_id = submit(runtime)
        backend.after_start = lambda: value(runtime.cancel(request_id))
        row = value(runtime.execute(request_id))
        assert row.status == "completed", row
        assert backend.cancelled.is_set() and not observed
    finally:
        substrate.close()
