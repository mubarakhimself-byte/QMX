"""Official Claude SDK session driver with no ordinary native tool access."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import uuid
from collections.abc import AsyncIterator, Callable, Mapping
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    PermissionResultDeny,
    ResultMessage,
    SystemMessage,
    TextBlock,
    create_sdk_mcp_server,
    tool,
)

from .contracts import ProviderRequest
from .native_sessions import SessionEvent
from .providers import ProviderError

CLAUDE_SDK_VERSION = "0.2.163"
CLAUDE_CLI_VERSION = "2.1.286"
_API_ENV = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK",
    }
)


class ClaudeSessionBackend:
    """Public boundary: managed policy cannot be isolated by this SDK on this host."""

    provider_id = "claude-agent-sdk:0.2.163:cli-2.1.286"
    binding_identity = provider_id
    available = False

    async def start(
        self, request: ProviderRequest, operation: Callable[..., Any], *, check: Callable[[], None]
    ) -> None:
        raise ProviderError("unsupported", "Claude managed policy requires host isolation")

    async def resume(
        self,
        session_id: str,
        request: ProviderRequest,
        operation: Callable[..., Any],
        *,
        check: Callable[[], None],
    ) -> None:
        await self.start(request, operation, check=check)

    async def events(self) -> AsyncIterator[SessionEvent]:
        raise ProviderError("unsupported", "Claude native sessions are unavailable on this host")
        yield  # pragma: no cover - async iterator protocol

    async def cancel(self) -> None:
        return

    async def close(self) -> None:
        return


class _ClaudeSDKLifecycle:  # pyright: ignore[reportUnusedClass] - offline reviewed seam
    """Only the explicit in-process QMX MCP server is available to the model.

    tools=[] removes builtins; allowed_tools alone is not a security boundary.
    strict_mcp_config excludes discovered servers; empty setting sources and
    disabled hooks/auto-memory prevent user/project configuration expansion.
    verbatim_prompts prevents @file/slash-command preprocessing. No subagents.
    """

    provider_id = "claude-agent-sdk:0.2.163:cli-2.1.286"

    def __init__(
        self,
        *,
        executable: Path,
        dedicated_home: Path,
        tool_schemas: Mapping[str, dict[str, Any]] | None = None,
        client_factory: Callable[..., Any] = ClaudeSDKClient,
        verify_runtime: bool = True,
    ) -> None:
        self.executable = executable
        self.dedicated_home = dedicated_home
        self.tool_schemas = dict(tool_schemas or {})
        self.client_factory = client_factory
        self.verify_runtime = verify_runtime
        self.client: Any = None
        self.session_id = ""
        self.operation_error: ProviderError | None = None
        self.binding_identity = hashlib.sha256(
            json.dumps(
                {
                    "provider": self.provider_id,
                    "executable": str(executable.resolve()),
                    "dedicated_home": str(dedicated_home.resolve()),
                    "tool_schemas": self.tool_schemas,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

    def _preflight(self, request: ProviderRequest) -> None:
        # Check names only; never inspect credential values or files.
        if _API_ENV.intersection(key.upper() for key in os.environ) or any(
            key.upper().startswith("ANTHROPIC_") for key in os.environ
        ):
            raise ProviderError("subscription_required", "API routing environment is present")
        if not self.verify_runtime:
            return
        if version("claude-agent-sdk") != CLAUDE_SDK_VERSION:
            raise ProviderError("unsupported", "Claude SDK version differs from reviewed pin")
        checked = subprocess.run(
            [str(self.executable), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        if checked.stdout.strip() != f"{CLAUDE_CLI_VERSION} (Claude Code)":
            raise ProviderError("unsupported", "Claude CLI version differs from reviewed pin")
        if not self.dedicated_home.is_dir() or not Path(request.cwd).is_dir():
            raise ProviderError("unsupported", "Dedicated native home and workspace required")
        # Metadata only. Authentication is exclusively the human's native flow.
        if any(
            (self.dedicated_home / name).exists()
            for name in (
                "settings.json",
                "settings.local.json",
                "hooks.json",
                "plugins",
                "agents",
                "skills",
            )
        ):
            raise ProviderError("unsupported", "Dedicated home contains unreviewed configuration")

    async def start(
        self, request: ProviderRequest, operation: Callable[..., Any], *, check: Callable[[], None]
    ) -> None:
        await self._connect(None, request, operation, check)

    async def resume(
        self,
        session_id: str,
        request: ProviderRequest,
        operation: Callable[..., Any],
        *,
        check: Callable[[], None],
    ) -> None:
        if not session_id:
            raise ProviderError("invalid_input", "Explicit native resume ID required")
        await self._connect(session_id, request, operation, check)

    async def _connect(
        self,
        session_id: str | None,
        request: ProviderRequest,
        operation: Callable[..., Any],
        check: Callable[[], None],
    ) -> None:
        check()
        self._preflight(request)
        native_tools: list[Any] = []
        for name, schema in self.tool_schemas.items():

            async def call(arguments: dict[str, Any], *, op_name: str = name) -> dict[str, Any]:
                try:
                    if self.operation_error is not None:
                        raise self.operation_error
                    result = await operation(op_name, arguments, uuid.uuid4().hex)
                except ProviderError as exc:
                    self.operation_error = exc
                    # Do not return arbitrary host exceptions or denied observations.
                    return {
                        "content": [{"type": "text", "text": "Host operation refused"}],
                        "is_error": True,
                    }
                except Exception:
                    self.operation_error = ProviderError(
                        "outcome_unknown", "Host operation outcome requires reconciliation"
                    )
                    return {
                        "content": [{"type": "text", "text": "Host operation refused"}],
                        "is_error": True,
                    }
                return {"content": [{"type": "text", "text": json.dumps(result)}]}

            native_tools.append(tool(name, "Host-admitted QMX read operation", schema)(call))

        async def deny(_name: str, _arguments: dict[str, Any], _context: Any) -> Any:
            return PermissionResultDeny(message="Outside the QMX native tool boundary")

        async def pre_tool(payload: Any, _tool_id: Any, _context: Any) -> Any:
            permitted = {f"mcp__qmx__{name}" for name in self.tool_schemas}
            if payload.get("agent_id") or payload.get("tool_name") not in permitted:
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": "Unapproved native tool or subagent",
                    }
                }
            # The callback itself performs live host admission, even if permission
            # allow rules shadow can_use_tool. No permission is persisted.
            return {}

        options = ClaudeAgentOptions(
            cli_path=self.executable,
            cwd=request.cwd,
            resume=session_id,
            model=request.model,
            system_prompt=request.instructions,
            tools=[],
            skills=[],
            agents={},
            allowed_tools=[f"mcp__qmx__{name}" for name in self.tool_schemas],
            disallowed_tools=[
                "Agent",
                "Task",
                "Skill",
                "Bash",
                "Read",
                "Write",
                "Edit",
                "WebFetch",
                "WebSearch",
                "ToolSearch",
            ],
            setting_sources=[],
            strict_mcp_config=True,
            plugins=[],
            settings=json.dumps({"disableAllHooks": True, "autoMemoryEnabled": False}),
            permission_mode="dontAsk",
            can_use_tool=deny,
            hooks={"PreToolUse": [HookMatcher(hooks=[pre_tool])]},
            mcp_servers={"qmx": create_sdk_mcp_server(name="qmx", tools=native_tools)},
            max_turns=8,
            include_partial_messages=False,
            max_buffer_size=262144,
            verbatim_prompts=True,
            extra_args={"disable-slash-commands": None},
            env={
                "CLAUDE_CONFIG_DIR": str(self.dedicated_home),
                "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
            },
        )
        self.session_id = session_id or ""
        self.operation_error = None
        self.client = self.client_factory(options=options)
        await self.client.connect()
        check()
        await self.client.query(request.prompt)

    async def events(self) -> AsyncIterator[SessionEvent]:
        if self.client is None:
            raise ProviderError("protocol_error", "Claude client is not connected")
        async for message in self.client.receive_response():
            if isinstance(message, SystemMessage) and message.subtype == "init":
                incoming = message.data.get("session_id")
                if not isinstance(incoming, str) or not incoming:
                    raise ProviderError("outcome_unknown", "Claude initialization ID missing")
                if self.session_id and self.session_id != incoming:
                    raise ProviderError("outcome_unknown", "Claude resumed another session")
                self.session_id = incoming
                advertised = message.data.get("tools", [])
                permitted = {f"mcp__qmx__{name}" for name in self.tool_schemas}
                if (
                    not isinstance(advertised, list)
                    or set(cast("list[Any]", advertised)) - permitted
                ):
                    raise ProviderError("outcome_unknown", "Claude advertised unapproved tools")
                yield SessionEvent("started", incoming)
            elif isinstance(message, AssistantMessage):
                if message.parent_tool_use_id is not None:
                    raise ProviderError("outcome_unknown", "Native subagent output refused")
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield SessionEvent("text", self.session_id, text=block.text)
            elif isinstance(message, ResultMessage):
                if self.operation_error is not None:
                    raise self.operation_error
                status = "completed"
                if message.origin is not None and message.origin.get("kind") == "task-notification":
                    raise ProviderError("outcome_unknown", "Native background result refused")
                if message.terminal_reason in {"aborted_streaming", "aborted_tools"}:
                    status = "interrupted"
                elif message.is_error or message.subtype != "success":
                    status = "failed"
                yield SessionEvent(
                    "terminal", message.session_id, text=message.result or "", status=status
                )
                return

    async def cancel(self) -> None:
        if self.client is not None:
            await self.client.interrupt()

    async def close(self) -> None:
        if self.client is not None:
            await self.client.disconnect()
            self.client = None
