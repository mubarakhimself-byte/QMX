"""Supplied-text Codex sessions through the official public CodexClient.

Native CLI configuration is the trusted boundary. This does not confine a
compromised process. Ordinary native filesystem tools remain unsupported.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import subprocess
import threading
from collections.abc import AsyncIterator, Callable, Mapping
from importlib.metadata import version
from pathlib import Path
from typing import Any, Literal, cast

from openai_codex import ApprovalMode, AsyncCodex, Sandbox
from openai_codex.client import CodexClient, CodexConfig
from openai_codex.generated.v2_all import (
    AgentMessageDeltaNotification,
    ConfigReadResponse,
    ItemCompletedNotification,
    ItemStartedNotification,
    TurnCompletedNotification,
)
from openai_codex.models import JsonObject, UnknownNotification

from .contracts import ProviderRequest
from .native_boundary import call_blocking, check_directories, check_environment
from .native_sessions import SessionEvent
from .providers import ProviderError

CODEX_SDK_VERSION = "0.160.0"
CODEX_RUNTIME_VERSION = "0.160.0"
DISABLED_FEATURES = (
    "shell_tool",
    "unified_exec",
    "apps",
    "multi_agent",
    "multi_agent_v2",
    "hooks",
    "memories",
    "plugins",
    "browser_use",
    "computer_use",
    "code_mode",
    "code_mode_host",
    "code_mode_prewarm",
    "view_image",
    "image_generation",
    "remote_plugin",
    "skill_mcp_dependency_install",
    "shell_snapshot",
    "tool_suggest",
    "browser_use_external",
    "request_permissions_tool",
    "executor_capability_discovery",
    "external_agent_memory_import",
    "chronicle",
    "daemon_auto_start",
    "unbounded_connection_retries",
    "recommended_plugins",
)
CONFIG: dict[str, Any] = {
    "features": {**dict.fromkeys(DISABLED_FEATURES, False), "skip_host_skill_discovery": True},
    "web_search": "disabled",
    "mcp_servers": {},
    "approval_policy": "never",
    "sandbox_mode": "read-only",
    "model_provider": "openai",
    "forced_login_method": "chatgpt",
    "cli_auth_credentials_store": "file",
    "project_doc_max_bytes": 0,
    "project_doc_fallback_filenames": [],
}


class CodexSessionBackend:
    provider_id = "openai-codex:0.160.0:cli-0.160.0"

    def __init__(
        self,
        *,
        executable: Path | None = None,
        dedicated_home: Path | None = None,
        empty_workspace: Path | None = None,
        tool_schemas: Mapping[str, dict[str, Any]] | None = None,
        client_factory: Callable[..., CodexClient] = CodexClient,
        verify_runtime: bool = True,
    ) -> None:
        self.executable, self.dedicated_home, self.workspace = (
            executable,
            dedicated_home,
            empty_workspace,
        )
        self.tool_schemas = dict(tool_schemas or {})
        self.client_factory, self.verify_runtime = client_factory, verify_runtime
        self.available = all(
            path is not None for path in (executable, dedicated_home, empty_workspace)
        )
        self.binding_identity = hashlib.sha256(
            json.dumps(
                {
                    "provider": self.provider_id,
                    "mode": "supplied_text",
                    "executable": str(executable),
                    "home": str(dedicated_home),
                    "workspace": str(empty_workspace),
                    "schemas": self.tool_schemas,
                    "config": CONFIG,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        self.client: CodexClient | None = None
        self.thread_id, self.turn_id = "", ""
        self.operation: Callable[..., Any] | None = None
        self.check: Callable[[], None] = lambda: None
        self.loop: asyncio.AbstractEventLoop | None = None
        self.ready: asyncio.Event | None = None
        self.operation_error: ProviderError | None = None
        self.calls: set[str] = set()
        self._closed = False
        self._launch_lock = threading.Lock()
        self._transport_fault = False
        self.turn_submitted = False

    async def _sdk_call(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """A daemon worker cannot strand asyncio.run's default executor on SDK EOF.

        The SDK owns process termination and protocol. close() fences start();
        cancellation of this await alone never proves native interruption.
        """
        return await call_blocking(function, *args, **kwargs)

    def _start_client(self) -> None:
        with self._launch_lock:
            if self._closed or self.client is None:
                raise ProviderError("interrupt_pending", "Codex launch already closed")
            self.client.start()
            if self._closed:
                self.client.close()

    def _close_client(self) -> None:
        with self._launch_lock:
            if self.client is not None:
                self.client.close()

    def _preflight(self) -> None:
        if not self.available:
            raise ProviderError(
                "unsupported",
                "Codex supplied-text launch configuration required; ordinary tools need isolation",
            )
        check_environment(provider="Codex")
        if self.executable is None or self.dedicated_home is None or self.workspace is None:
            raise ProviderError("unsafe_config", "Dedicated Codex launch directories required")
        check_directories(
            self.dedicated_home,
            self.workspace,
            configuration_names=(
                "config.toml",
                "hooks.json",
                "plugins",
                "skills",
                "agents",
                "AGENTS.md",
            ),
        )
        if self.verify_runtime:
            if version("openai-codex") != CODEX_SDK_VERSION:
                raise ProviderError("unsupported", "Codex SDK differs from reviewed pin")
            checked = subprocess.run(
                [str(self.executable), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            if checked.stdout.strip() != f"codex-cli {CODEX_RUNTIME_VERSION}":
                raise ProviderError("unsupported", "Codex CLI differs from reviewed pin")

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
        await self._sdk_call(self._preflight)
        check()
        self.loop, self.ready = asyncio.get_running_loop(), asyncio.Event()
        self.operation, self.check = operation, check
        if self.executable is None or self.dedicated_home is None or self.workspace is None:
            raise ProviderError("unsafe_config", "Dedicated Codex launch directories required")
        overrides = tuple(
            f"features.{key}={str(value).lower()}" for key, value in CONFIG["features"].items()
        )
        overrides += tuple(
            f"{key}={json.dumps(value)}" if not isinstance(value, dict) else f"{key}={{}}"
            for key, value in CONFIG.items()
            if key != "features"
        )
        self.client = self.client_factory(
            config=CodexConfig(
                codex_bin=str(self.executable),
                cwd=str(self.workspace),
                config_overrides=overrides,
                env={"CODEX_HOME": str(self.dedicated_home)},
                experimental_api=True,
            ),
            approval_handler=self._server_request,
        )
        await self._sdk_call(self._start_client)
        if self._closed:
            raise ProviderError("interrupt_pending", "Codex launch closed before initialization")
        initialized = await self._sdk_call(self.client.initialize)
        runtime = initialized.serverInfo.version if initialized.serverInfo else None
        if (runtime is not None and runtime != CODEX_RUNTIME_VERSION) or (
            runtime is None
            and not (initialized.userAgent or "").startswith(f"codex/{CODEX_RUNTIME_VERSION} ")
        ):
            raise ProviderError("unsafe_config", "Codex initialized runtime differs from pin")
        config = await self._sdk_call(
            self.client.request,
            "config/read",
            {"includeLayers": False},
            response_model=ConfigReadResponse,
        )
        actual = config.config.model_dump(mode="json", exclude_none=True)
        raw_features: object = actual.get("features", {})
        features = cast("dict[str, Any]", raw_features) if isinstance(raw_features, dict) else {}
        if (
            any(features.get(name) is not False for name in DISABLED_FEATURES)
            or features.get("skip_host_skill_discovery") is not True
            or any(
                actual.get(name) != expected
                for name, expected in CONFIG.items()
                if name != "features"
            )
            or actual.get("model_providers")
            or actual.get("instructions")
            or actual.get("developer_instructions")
            or actual.get("model_instructions_file")
        ):
            raise ProviderError("unsafe_config", "Codex effective launch restrictions differ")
        account = await self._sdk_call(self.client.account_read, {"refreshToken": False})
        # Native SDK account metadata only, after authorized launch; no credential access.
        if account.account is None or account.account.root.type != "chatgpt":
            raise ProviderError("auth_required", "Sign in with ChatGPT in the dedicated Codex home")
        check()
        params: JsonObject = {
            "cwd": str(self.workspace),
            "sandbox": "read-only",
            "approvalPolicy": "never",
            "approvalsReviewer": "user",
            "modelProvider": "openai",
            "developerInstructions": request.instructions,
            "runtimeWorkspaceRoots": [],
        }
        if request.model:
            params["model"] = request.model
        if session_id is None:
            params["environments"] = []
            params["dynamicTools"] = cast(
                "Any",
                [
                    {
                        "type": "function",
                        "name": name,
                        "description": "Host-admitted QMX metadata read",
                        "inputSchema": schema,
                        "deferLoading": False,
                    }
                    for name, schema in self.tool_schemas.items()
                ],
            )
            started = await self._sdk_call(self.client.thread_start, params)
        else:
            started = await self._sdk_call(self.client.thread_resume, session_id, params)
        state = started.model_dump(mode="json", by_alias=True, exclude_unset=True)
        thread = state["thread"]
        if (
            not thread["id"]
            or (session_id and thread["id"] != session_id)
            or state["approvalPolicy"] != "never"
            or state["approvalsReviewer"] != "user"
            or state["sandbox"] != {"type": "readOnly", "networkAccess": False}
            or state["modelProvider"] != "openai"
            or Path(state["cwd"]).resolve() != self.workspace.resolve()
            or state.get("instructionSources")
            or thread.get("parentThreadId")
            or thread.get("agentRole")
            or thread.get("agentNickname")
            or isinstance(thread.get("source"), dict)
        ):
            raise ProviderError(
                "outcome_unknown", "Codex native identity or thread boundary differs"
            )
        self.thread_id = thread["id"]
        check()
        if self.operation_error is not None:
            raise self.operation_error
        self.turn_submitted = True  # Persisted host pending precedes this send.
        turn = await self._sdk_call(
            self.client.turn_start,
            self.thread_id,
            request.prompt,
            {
                "environments": [],
                "runtimeWorkspaceRoots": [],
                "approvalPolicy": "never",
                "approvalsReviewer": "user",
                "sandboxPolicy": {"type": "readOnly", "networkAccess": False},
            },
        )
        self.turn_id = turn.turn.id
        if not self.turn_id:
            raise ProviderError("outcome_unknown", "Codex turn ID missing")
        for item in turn.turn.items:
            self._validate_item(item.model_dump(mode="json", by_alias=True))
        self.ready.set()

    def _validate_item(self, item: dict[str, Any]) -> None:
        if item.get("type") not in {
            "userMessage",
            "agentMessage",
            "reasoning",
            "dynamicToolCall",
            "contextCompaction",
            "plan",
        }:
            raise ProviderError("outcome_unknown", "Ordinary native tool activity refused")
        if item["type"] == "dynamicToolCall" and (
            item.get("tool") not in self.tool_schemas
            or item.get("namespace") not in {None, "functions"}
        ):
            raise ProviderError("outcome_unknown", "Unapproved native dynamic tool")

    def _server_request(self, method: str, params: JsonObject | None) -> JsonObject:
        """SDK owns transport. Never use its permissive default approval handler."""
        if method == "item/tool/call" and self.loop is not None:
            pending = asyncio.run_coroutine_threadsafe(self._host_call(params), self.loop)
            try:
                return pending.result(timeout=10)
            except Exception:
                pending.cancel()
                self.operation_error = ProviderError(
                    "outcome_unknown", "Native host callback did not complete"
                )
                return {
                    "success": False,
                    "contentItems": [{"type": "inputText", "text": "Host operation refused"}],
                }
        self.operation_error = ProviderError(
            "outcome_unknown", "Unexpected native server request refused"
        )
        if method in {"item/commandExecution/requestApproval", "item/fileChange/requestApproval"}:
            return {"decision": "decline"}
        if method == "item/permissions/requestApproval":
            return {"permissions": {}, "scope": "turn"}
        if method == "item/tool/requestUserInput":
            return {"answers": {}}
        if method == "mcpServer/elicitation/request":
            return {"action": "cancel", "content": None, "_meta": None}
        # An unknown request has no safe success schema. Raising closes the SDK
        # router with an error; it cannot become an empty successful approval.
        self._transport_fault = True
        raise self.operation_error

    async def _host_call(self, params: JsonObject | None) -> JsonObject:
        try:
            if self.ready is None or self.operation is None:
                raise ProviderError("outcome_unknown", "Native callback outside a turn")
            await asyncio.wait_for(self.ready.wait(), timeout=1)
            if self.operation_error is not None:
                raise self.operation_error
            self.check()
            data = params or {}
            call_id = data.get("callId")
            name, arguments = data.get("tool"), data.get("arguments")
            if (
                data.get("threadId") != self.thread_id
                or data.get("turnId") != self.turn_id
                or data.get("namespace") not in {None, "functions"}
                or data.get("agentId")
                or not isinstance(call_id, str)
                or not call_id
                or call_id in self.calls
                or not isinstance(name, str)
                or name not in self.tool_schemas
                or not isinstance(arguments, dict)
            ):
                raise ProviderError("outcome_unknown", "Native tool identity or authority refused")
            self.calls.add(call_id)
            result = await self.operation(name, arguments, call_id)
            self.check()
            return {
                "success": True,
                "contentItems": [{"type": "inputText", "text": json.dumps(result)}],
            }
        except ProviderError as exc:
            self.operation_error = exc
        except Exception:
            self.operation_error = ProviderError(
                "outcome_unknown", "Host operation requires reconciliation"
            )
        return {
            "success": False,
            "contentItems": [{"type": "inputText", "text": "Host operation refused"}],
        }

    async def events(self) -> AsyncIterator[SessionEvent]:
        if self.client is None or not self.thread_id or not self.turn_id:
            raise ProviderError("protocol_error", "Codex native turn not started")
        yield SessionEvent("started", self.thread_id, self.turn_id)
        while True:
            notification = await self._sdk_call(self.client.next_turn_notification, self.turn_id)
            payload = notification.payload
            if isinstance(payload, UnknownNotification):
                raise ProviderError("outcome_unknown", "Unknown or malformed native notification")
            data = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
            if (
                data.get("threadId", self.thread_id) != self.thread_id
                or data.get("turnId", self.turn_id) != self.turn_id
            ):
                raise ProviderError("outcome_unknown", "Native event identity mismatch")
            if isinstance(payload, AgentMessageDeltaNotification):
                yield SessionEvent("text", self.thread_id, self.turn_id, payload.delta)
            elif isinstance(payload, (ItemStartedNotification, ItemCompletedNotification)):
                self._validate_item(data["item"])
            elif isinstance(payload, TurnCompletedNotification):
                if payload.turn.id != self.turn_id or self.operation_error is not None:
                    raise self.operation_error or ProviderError(
                        "outcome_unknown", "Codex terminal identity mismatch"
                    )
                status = payload.turn.status.value
                if status not in {"completed", "interrupted", "failed"}:
                    raise ProviderError("outcome_unknown", "Codex terminal status invalid")
                final_text: list[str] = []
                for item in payload.turn.items:
                    body = item.model_dump(mode="json", by_alias=True)
                    self._validate_item(body)
                    if body["type"] == "agentMessage":
                        final_text.append(str(body["text"]))
                yield SessionEvent(
                    "terminal",
                    self.thread_id,
                    self.turn_id,
                    text="\n".join(final_text),
                    status=cast("Literal['completed', 'interrupted', 'failed']", status),
                )
                return

    async def cancel(self) -> None:
        if self._transport_fault:
            raise ProviderError("outcome_unknown", "Codex transport already failed")
        if self.client is None or not self.turn_id:
            raise ProviderError("interrupt_pending", "Codex turn is not yet interruptible")
        await self._sdk_call(self.client.turn_interrupt, self.thread_id, self.turn_id)

    async def close(self) -> None:
        self._closed = True
        if self.client is not None:
            await self._sdk_call(self._close_client)
            self.client = None


class _CodexSDKLifecycle:  # pyright: ignore[reportUnusedClass] - offline reviewed seam
    """Offline-reviewed SDK mapping, deliberately not an admitted backend.

    It is private and has no available flag. No host configuration or daemon
    factory exposes it. There is no runtime override to bypass the boundary.
    """

    def __init__(self, client: AsyncCodex) -> None:
        self.client = client
        self.thread: Any = None
        self.turn: Any = None

    async def start(self, request: ProviderRequest, _operation: Callable[..., Any]) -> None:
        self.thread = await self.client.thread_start(
            cwd=request.cwd,
            model=request.model,
            developer_instructions=request.instructions,
            approval_mode=ApprovalMode.deny_all,
            sandbox=Sandbox.read_only,
        )
        self.turn = await self.thread.turn(request.prompt)

    async def resume(
        self, session_id: str, request: ProviderRequest, _operation: Callable[..., Any]
    ) -> None:
        self.thread = await self.client.thread_resume(
            session_id,
            cwd=request.cwd,
            model=request.model,
            developer_instructions=request.instructions,
            approval_mode=ApprovalMode.deny_all,
            sandbox=Sandbox.read_only,
        )
        if self.thread.id != session_id:
            raise ProviderError("outcome_unknown", "Codex resumed another thread")
        self.turn = await self.thread.turn(request.prompt)

    async def events(self) -> AsyncIterator[SessionEvent]:
        yield SessionEvent("started", self.thread.id, self.turn.id)
        async for notification in self.turn.stream():
            payload = notification.payload
            if isinstance(payload, AgentMessageDeltaNotification):
                if payload.thread_id != self.thread.id or payload.turn_id != self.turn.id:
                    raise ProviderError("outcome_unknown", "Codex delta identity mismatch")
                yield SessionEvent("text", self.thread.id, self.turn.id, payload.delta)
            elif isinstance(payload, TurnCompletedNotification):
                if payload.thread_id != self.thread.id or payload.turn.id != self.turn.id:
                    raise ProviderError("outcome_unknown", "Codex terminal identity mismatch")
                status = payload.turn.status.value
                if status not in {"completed", "interrupted", "failed"}:
                    raise ProviderError("outcome_unknown", "Codex terminal status invalid")
                yield SessionEvent(
                    "terminal",
                    self.thread.id,
                    self.turn.id,
                    status=cast("Literal['completed', 'interrupted', 'failed']", status),
                )
                return

    async def cancel(self) -> None:
        if self.turn is not None:
            await self.turn.interrupt()

    async def close(self) -> None:
        await self.client.close()
