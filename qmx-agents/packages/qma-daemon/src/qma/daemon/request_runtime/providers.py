"""Native Codex text-turn transport; QMA retains work and authority ownership.

No credentials are read by this module. The operator must authenticate the native
CLI in an explicitly dedicated CODEX_HOME. Native tools and resume are excluded.
"""

from __future__ import annotations

import json
import math
import os
import queue
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from .contracts import ProviderCapabilities, ProviderEvent, ProviderRequest, ProviderResult


class ProviderError(RuntimeError):
    """A sanitized transport failure with machine-readable outcome classification."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ProviderCancelled(ProviderError):
    def __init__(self) -> None:
        super().__init__("cancelled", "Native turn acknowledged interruption")


def _object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProviderError("protocol_error", "Native protocol object required")
    return cast("dict[str, Any]", value)


_DISABLED_FEATURES = (
    "shell_tool",
    "unified_exec",
    "apps",
    "multi_agent",
    "hooks",
    "memories",
    "plugins",
    "browser_use",
    "computer_use",
    "code_mode",
    "view_image",
    "image_generation",
    "remote_plugin",
    "skill_mcp_dependency_install",
    "shell_snapshot",
    "tool_suggest",
    "browser_use_external",
    "code_mode_host",
)


class _Rpc:
    """Bounded JSONL reader; errors never contain arbitrary native output."""

    def __init__(self, process: subprocess.Popen[str]) -> None:
        self.process = process
        self.messages: queue.Queue[dict[str, Any] | ProviderError] = queue.Queue(maxsize=128)
        self.next_id = 0
        self.closed = threading.Event()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self) -> None:
        if self.process.stdout is None:
            self._put(ProviderError("protocol_error", "Native stdout is unavailable"))
            return
        try:
            while not self.closed.is_set():
                line = self.process.stdout.readline(1_048_577)
                if not line:
                    self._put(ProviderError("protocol_eof", "Native process closed stdout"))
                    return
                if len(line) > 1_048_576:
                    raise ValueError("oversize")
                message = _object(json.loads(line))
                self._put(message)
        except ValueError, OSError, ProviderError:
            self._put(ProviderError("protocol_error", "Invalid native JSONL protocol"))

    def _put(self, message: dict[str, Any] | ProviderError) -> None:
        while not self.closed.is_set():
            try:
                self.messages.put(message, timeout=0.1)
                return
            except queue.Full:
                continue

    def send(self, message: Mapping[str, object]) -> None:
        if self.process.stdin is None:
            raise ProviderError("protocol_error", "Native stdin is unavailable")
        try:
            self.process.stdin.write(json.dumps(dict(message)) + "\n")
            self.process.stdin.flush()
        except (OSError, ValueError) as exc:
            raise ProviderError("protocol_eof", "Cannot write native protocol") from exc

    def request(self, method: str, params: Mapping[str, object]) -> int:
        self.next_id += 1
        self.send({"id": self.next_id, "method": method, "params": dict(params)})
        return self.next_id

    def receive(self, deadline: float, cancellation: threading.Event) -> dict[str, Any]:
        while time.monotonic() < deadline:
            if cancellation.is_set():
                raise ProviderError("cancel_requested", "Cancellation requested")
            try:
                message = self.messages.get(
                    timeout=min(0.05, max(0.001, deadline - time.monotonic()))
                )
            except queue.Empty:
                continue
            if isinstance(message, ProviderError):
                raise message
            return message
        raise ProviderError("timeout", "Native request deadline elapsed")

    def close(self) -> None:
        self.closed.set()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        self.reader.join(timeout=1)
        for stream in (self.process.stdin, self.process.stdout):
            if stream is not None:
                stream.close()


class CodexAppServerProvider:
    """Fresh, text-only native turns with subscription auth owned by Codex.

    Dedicated home must contain no config.toml or hooks.json. Startup overrides and
    effective-config verification disable native capabilities before a model call.
    The installed 0.159 schema lacks restricted read roots; readOnly is defense in
    depth, not a claim of OS isolation. A fresh empty workspace is always used.
    """

    def __init__(self, executable: str | Path | Sequence[str], codex_home: str | Path) -> None:
        self.command = (
            (str(executable),) if isinstance(executable, (str, Path)) else tuple(executable)
        )
        if not self.command:
            raise ValueError("native executable required")
        self.codex_home = Path(codex_home).resolve()

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities("codex-native", resume=False, native_tools=False)

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        if request.thread_id or request.cwd:
            raise ProviderError("unsupported", "Native v1 requires a fresh empty workspace/thread")
        if not math.isfinite(request.timeout_seconds) or request.timeout_seconds <= 0:
            raise ProviderError("invalid_input", "Positive finite timeout required")
        if not self.codex_home.is_dir():
            raise ProviderError(
                "auth_required", "Create and authenticate a dedicated Codex home first"
            )
        if self.codex_home == Path.home().joinpath(".codex").resolve():
            raise ProviderError("unsafe_config", "Default Codex home is excluded from this adapter")
        if any((self.codex_home / name).exists() for name in ("config.toml", "hooks.json")):
            raise ProviderError(
                "unsafe_config", "Dedicated native home must have no config or hooks"
            )
        if cancellation.is_set():
            raise ProviderCancelled()
        with tempfile.TemporaryDirectory(prefix="qma-native-text-") as workspace:
            return self._execute(request, emit, cancellation, workspace)

    def _execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
        workspace: str,
    ) -> ProviderResult:
        env = {
            key: os.environ[key]
            for key in (
                "PATH",
                "SYSTEMROOT",
                "WINDIR",
                "TEMP",
                "TMP",
                "USERPROFILE",
                "HOME",
                "APPDATA",
                "LOCALAPPDATA",
            )
            if key in os.environ
        }
        env["CODEX_HOME"] = str(self.codex_home)
        args = [*self.command, "app-server", "--stdio"]
        for feature in _DISABLED_FEATURES:
            args.extend(["-c", f"features.{feature}=false"])
        for override in (
            'web_search="disabled"',
            "features.skip_host_skill_discovery=true",
            "mcp_servers={}",
            'approval_policy="untrusted"',
            'sandbox_mode="read-only"',
        ):
            args.extend(["-c", override])
        try:
            process = subprocess.Popen(
                args,
                cwd=workspace,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                shell=False,
            )
        except OSError as exc:
            raise ProviderError("unavailable", "Native Codex executable could not start") from exc
        rpc = _Rpc(process)
        deadline = time.monotonic() + request.timeout_seconds
        thread_id: str | None = None
        turn_id: str | None = None
        started = False
        deltas: list[str] = []
        final_messages: dict[str, str] = {}
        terminal: dict[str, Any] | None = None

        def notification(message: dict[str, Any]) -> None:
            nonlocal terminal
            method = message.get("method")
            params = message.get("params", {})
            if "id" in message and method:
                if method in {
                    "item/commandExecution/requestApproval",
                    "item/fileChange/requestApproval",
                }:
                    rpc.send({"id": message["id"], "result": {"decision": "decline"}})
                else:
                    rpc.send(
                        {
                            "id": message["id"],
                            "error": {"code": -32601, "message": "QMA denies native tool requests"},
                        }
                    )
                emit(ProviderEvent("tool_denied", {"method": str(method)}))
                return
            params = _object(params)
            if thread_id and params.get("threadId") not in (None, thread_id):
                raise ProviderError("protocol_error", "Native thread mismatch")
            if method == "item/agentMessage/delta":
                delta = params.get("delta")
                if isinstance(delta, str):
                    deltas.append(delta)
                    emit(ProviderEvent("text_delta", {"delta": delta}))
            elif method in {"item/started", "item/completed"}:
                item = params.get("item", {})
                item = _object(item)
                kind = item.get("type")
                if kind not in {
                    "userMessage",
                    "agentMessage",
                    "reasoning",
                    "plan",
                    "contextCompaction",
                }:
                    raise ProviderError(
                        "native_tool_violation", "Unexpected native tool item; terminating"
                    )
                if (
                    method == "item/completed"
                    and kind == "agentMessage"
                    and isinstance(item.get("text"), str)
                ):
                    final_messages[str(item.get("id", len(final_messages)))] = item["text"]
            elif method == "turn/completed":
                terminal = _object(params.get("turn"))

        def call(method: str, params: Mapping[str, object]) -> dict[str, Any]:
            request_id = rpc.request(method, params)
            while True:
                message = rpc.receive(deadline, cancellation)
                if message.get("id") == request_id and "method" not in message:
                    if "error" in message:
                        raise ProviderError("native_error", f"Native {method} rejected request")
                    result = message.get("result")
                    return _object(result)
                notification(message)

        try:
            call("initialize", {"clientInfo": {"name": "qma_sdk", "version": "0.1.0"}})
            rpc.send({"method": "initialized", "params": {}})
            config = call("config/read", {"includeLayers": False}).get("config", {})
            config = _object(config)
            features = _object(config.get("features", {}))
            if (
                any(features.get(key) is not False for key in _DISABLED_FEATURES)
                or features.get("skip_host_skill_discovery") is not True
                or config.get("web_search") != "disabled"
                or config.get("mcp_servers")
            ):
                raise ProviderError(
                    "unsafe_config", "Native tool restrictions could not be verified"
                )
            account = call("account/read", {"refreshToken": False}).get("account")
            if account is None or _object(account).get("type") != "chatgpt":
                raise ProviderError(
                    "auth_required", "Sign in with ChatGPT in the dedicated Codex home"
                )
            params: dict[str, object] = {
                "cwd": workspace,
                "sandbox": "read-only",
                "approvalPolicy": "untrusted",
                "approvalsReviewer": "user",
                "developerInstructions": request.instructions,
            }
            if request.model:
                params["model"] = request.model
            thread = call("thread/start", params).get("thread", {})
            thread_id = _object(thread).get("id")
            if not isinstance(thread_id, str) or not thread_id:
                raise ProviderError("protocol_error", "Missing native thread id")
            emit(ProviderEvent("thread_started", {"thread_id": thread_id}))
            # Sending turn/start can have effects even if its response is lost.
            started = True
            turn = call(
                "turn/start",
                {
                    "threadId": thread_id,
                    "input": [{"type": "text", "text": request.prompt}],
                    "sandboxPolicy": {"type": "readOnly"},
                    "approvalPolicy": "untrusted",
                    "approvalsReviewer": "user",
                },
            ).get("turn", {})
            turn_id = _object(turn).get("id")
            if not isinstance(turn_id, str) or not turn_id:
                raise ProviderError("protocol_error", "Missing native turn id")
            emit(ProviderEvent("turn_started", {"turn_id": turn_id}))
            while terminal is None:
                notification(rpc.receive(deadline, cancellation))
            if terminal.get("id") != turn_id:
                raise ProviderError("protocol_error", "Native terminal turn mismatch")
            if terminal.get("status") == "interrupted":
                raise ProviderCancelled()
            if terminal.get("status") != "completed":
                raise ProviderError("native_failed", "Native turn failed")
            return ProviderResult(
                "\n".join(final_messages.values()) if final_messages else "".join(deltas),
                thread_id,
                turn_id,
                "codex-native",
            )
        except ProviderError as exc:
            if started and exc.code not in {"cancelled", "native_failed"}:
                if thread_id and turn_id:
                    grace = time.monotonic() + 2
                    try:
                        rpc.request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})
                        while terminal is None:
                            notification(rpc.receive(grace, threading.Event()))
                        if (
                            terminal.get("id") == turn_id
                            and terminal.get("status") == "interrupted"
                            and cancellation.is_set()
                        ):
                            raise ProviderCancelled() from exc
                    except ProviderCancelled:
                        raise
                    except ProviderError:
                        pass
                raise ProviderError(
                    "outcome_unknown", "Native turn outcome requires reconciliation"
                ) from exc
            if exc.code == "cancel_requested":
                raise ProviderCancelled() from exc
            raise
        finally:
            rpc.close()
