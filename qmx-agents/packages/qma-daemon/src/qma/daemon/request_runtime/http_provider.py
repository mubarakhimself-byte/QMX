"""Explicit Chat Completions transport, including bounded text SSE.

This is inference transport only. No subscription credentials, native provider
identity emulation, redirects, retries, fallback, tools or account pooling.
"""

from __future__ import annotations

import http.client
import ipaddress
import json
import math
import os
import queue
import re
import socket
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from typing import Any, cast
from urllib.parse import urlsplit

from qma.core.barriers.reachability import is_denied_host, is_forbidden_model_adapter

from .contracts import ProviderCapabilities, ProviderEvent, ProviderRequest, ProviderResult
from .providers import ProviderError

_MAX_BYTES = 4 * 1024 * 1024
_MAX_TEXT = 512 * 1024
_MAX_LINE = 64 * 1024
# DNS/connect cannot always be interrupted by socket shutdown. Retained workers
# hold this shared capacity until they actually exit, including after a caller
# stops waiting. This bounds resources across every HTTP provider instance.
_TRANSPORT_SLOTS = threading.BoundedSemaphore(4)


def _object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProviderError("protocol_error", "Completion response object required")
    return cast("dict[str, Any]", value)


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _choice(data: dict[str, Any], *, allow_empty: bool = False) -> dict[str, Any] | None:
    choices: object = data.get("choices")
    if not isinstance(choices, list):
        raise ProviderError("protocol_error", "Completion choices must be an array")
    values = cast("list[object]", choices)
    if not values and allow_empty:
        return None
    if len(values) != 1:
        raise ProviderError("protocol_error", "Exactly one text completion choice required")
    choice = _object(values[0])
    if choice.get("index", 0) != 0:
        raise ProviderError("protocol_error", "Unexpected completion choice index")
    return choice


class ChatCompletionsProvider:
    """Configured direct endpoint, optionally an operator's CLIProxyAPI instance.

    API keys are resolved lazily from an explicitly named environment variable;
    they never enter results, events or errors. HTTP is accepted only for literal
    loopback hosts. Other endpoints require HTTPS with normal certificate checks.
    Closing a connection does not prove upstream cancellation: post-dispatch
    cancellation/timeouts are outcome_unknown and are never retried here.
    Up to four retained transport workers may outlive callers during blocked DNS
    or connect. Capacity remains occupied until teardown; overload is refused.
    """

    def __init__(
        self,
        endpoint: str,
        model: str,
        *,
        deployment_id: str,
        provider_id: str = "api-compatible",
        api_key_env: str | None = None,
        stream: bool = False,
    ) -> None:
        parsed = urlsplit(endpoint)
        if is_denied_host(parsed.hostname) or is_forbidden_model_adapter(provider_id):
            raise ValueError("Configured inference endpoint or adapter violates host reachability")
        openrouter = parsed.hostname == "openrouter.ai"
        expected_path = "/api/v1/chat/completions" if openrouter else "/v1/chat/completions"
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path != expected_path
            or (openrouter and (parsed.scheme != "https" or parsed.port not in {None, 443}))
        ):
            raise ValueError("Explicit supported Chat Completions endpoint required")
        if parsed.scheme == "http":
            try:
                loopback = ipaddress.ip_address(parsed.hostname).is_loopback
            except ValueError:
                loopback = False
            if not loopback:
                raise ValueError("Plain HTTP requires a literal loopback host")
        if not all(
            _text(value)
            for value in (
                model,
                deployment_id,
                provider_id,
            )
        ):
            raise ValueError("Explicit model, deployment and provider identity required")
        if api_key_env is not None and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", api_key_env):
            raise ValueError("API key reference must name an environment variable")
        self.endpoint = endpoint
        self.model = model
        self.deployment_id = deployment_id
        self.provider_id = provider_id
        self.api_key_env = api_key_env
        self.stream = stream
        self._url = parsed

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(self.provider_id, resume=False, native_tools=False)

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        if request.thread_id or request.cwd:
            raise ProviderError("unsupported", "HTTP inference has no native workspace or resume")
        if request.model not in (None, self.model):
            raise ProviderError(
                "invalid_input", "Requested model differs from configured deployment"
            )
        if not math.isfinite(request.timeout_seconds) or request.timeout_seconds <= 0:
            raise ProviderError("invalid_input", "Positive finite timeout required")
        if cancellation.is_set():
            raise ProviderError("cancelled", "Cancelled before HTTP dispatch")
        key = os.environ.get(self.api_key_env) if self.api_key_env else None
        if self.api_key_env and not key:
            raise ProviderError("auth_required", "Configured API key reference is unavailable")
        if key and ("\r" in key or "\n" in key):
            raise ProviderError("invalid_input", "Invalid authentication reference value")
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if self.stream else "application/json",
        }
        if key:
            headers["Authorization"] = f"Bearer {key}"
        messages: list[dict[str, str]] = []
        if request.instructions:
            messages.append({"role": "system", "content": request.instructions})
        messages.append({"role": "user", "content": request.prompt})
        payload: dict[str, object] = {
            "model": self.model,
            "messages": messages,
            "stream": self.stream,
            "n": 1,
        }
        if self._url.hostname == "openrouter.ai":
            payload["provider"] = {"allow_fallbacks": False}
        body = json.dumps(payload).encode("utf-8")
        if len(body) > _MAX_BYTES:
            raise ProviderError("invalid_input", "Completion request exceeds byte budget")
        connection_type = (
            http.client.HTTPSConnection
            if self._url.scheme == "https"
            else http.client.HTTPConnection
        )
        connection = connection_type(
            self._url.hostname or "", self._url.port, timeout=request.timeout_seconds
        )
        inbox: queue.Queue[ProviderEvent | ProviderResult | ProviderError] = queue.Queue(
            maxsize=128
        )
        stop = threading.Event()
        dispatched = threading.Event()
        dispatch_gate = threading.Lock()
        sockets: list[socket.socket] = []
        deadline = time.monotonic() + request.timeout_seconds
        transport_slots = _TRANSPORT_SLOTS
        if not transport_slots.acquire(blocking=False):
            raise ProviderError("unavailable", "HTTP transport capacity is occupied")

        def interrupt_socket() -> None:
            for connected_socket in sockets:
                with suppress(OSError):
                    connected_socket.shutdown(socket.SHUT_RDWR)

        def put(item: ProviderEvent | ProviderResult | ProviderError) -> None:
            while not stop.is_set():
                try:
                    inbox.put(item, timeout=0.05)
                    return
                except queue.Full:
                    continue

        def work() -> None:
            try:
                # Establish connection before dispatch so connect failures are retry-safe.
                connection.connect()
                if connection.sock is not None:
                    sockets.append(connection.sock)
                # Stop and dispatch admission share one gate. The owner never
                # closes HTTPConnection while this call can start: closing it
                # resets sock to None and can cause http.client to reconnect.
                with dispatch_gate:
                    if stop.is_set() or cancellation.is_set() or time.monotonic() >= deadline:
                        code = "cancelled" if cancellation.is_set() else "timeout"
                        put(ProviderError(code, "Stopped before HTTP dispatch"))
                        return
                    dispatched.set()
                    connection.request("POST", self._url.path, body=body, headers=headers)
                response = connection.getresponse()
                if sum(len(name) + len(value) for name, value in response.getheaders()) > _MAX_LINE:
                    raise ProviderError("protocol_error", "Completion headers exceed byte budget")
                if response.status != 200:
                    code = (
                        "auth_required"
                        if response.status in {401, 403}
                        else "rate_limited"
                        if response.status == 429
                        else "http_rejected"
                    )
                    put(
                        ProviderError(
                            code, f"Completion endpoint rejected request ({response.status})"
                        )
                    )
                    return
                content_type = (
                    response.getheader("Content-Type", "").split(";", 1)[0].strip().lower()
                )
                if self.stream:
                    if content_type != "text/event-stream":
                        raise ProviderError("protocol_error", "Expected text/event-stream")
                    result = self._read_stream(response, put)
                else:
                    if content_type != "application/json":
                        raise ProviderError("protocol_error", "Expected application/json")
                    raw = response.read(_MAX_BYTES + 1)
                    if len(raw) > _MAX_BYTES:
                        raise ProviderError(
                            "protocol_error", "Completion response exceeds byte budget"
                        )
                    choice = _choice(_object(json.loads(raw)))
                    if choice is None:
                        raise ProviderError("protocol_error", "Missing completion choice")
                    message = _object(choice.get("message"))
                    self._verify_text_message(message)
                    if choice.get("finish_reason") != "stop":
                        raise ProviderError("incomplete", "Completion did not finish normally")
                    content = message.get("content")
                    if not isinstance(content, str) or len(content) > _MAX_TEXT:
                        raise ProviderError("protocol_error", "Bounded text content required")
                    result = ProviderResult(content, deployment_id=self.deployment_id)
                put(result)
            except ProviderError as exc:
                put(exc)
            except OSError, http.client.HTTPException, ValueError:
                code = "outcome_unknown" if dispatched.is_set() else "unavailable"
                put(ProviderError(code, "Completion transport failed"))
            finally:
                try:
                    connection.close()
                finally:
                    transport_slots.release()

        try:
            worker = threading.Thread(target=work, daemon=True)
            worker.start()
        except Exception as exc:
            transport_slots.release()
            connection.close()
            raise ProviderError("unavailable", "HTTP transport worker could not start") from exc
        try:
            while True:
                # Observe completed results first: completion may win a cancel race.
                try:
                    item = inbox.get(timeout=0.01)
                except queue.Empty:
                    item = None
                if isinstance(item, ProviderResult):
                    return item
                if isinstance(item, ProviderError):
                    if dispatched.is_set() and item.code in {"protocol_error", "unsupported_tool"}:
                        raise ProviderError(
                            "outcome_unknown", "Completion outcome requires reconciliation"
                        ) from item
                    raise item
                if isinstance(item, ProviderEvent):
                    try:
                        emit(item)
                    except Exception as exc:
                        raise ProviderError(
                            "outcome_unknown", "Completion event consumer failed"
                        ) from exc
                if cancellation.is_set() or time.monotonic() >= deadline:
                    stop.set()
                    interrupt_socket()
                    admitted_stop = dispatch_gate.acquire(timeout=0.01)
                    if admitted_stop:
                        dispatch_gate.release()
                    code = (
                        "outcome_unknown"
                        if dispatched.is_set() or not admitted_stop
                        else "cancelled"
                        if cancellation.is_set()
                        else "timeout"
                    )
                    raise ProviderError(code, "Completion wait stopped; no automatic retry")
        finally:
            stop.set()
            interrupt_socket()
            # Worker owns close. An uninterruptible connect retains its slot;
            # after it returns the stop gate prevents any new POST.
            worker.join(timeout=0.2)

    @staticmethod
    def _verify_text_message(message: dict[str, Any]) -> None:
        if message.get("tool_calls") or message.get("function_call"):
            raise ProviderError("unsupported_tool", "HTTP transport excludes provider tool calls")

    def _read_stream(
        self,
        response: http.client.HTTPResponse,
        emit: Callable[[ProviderEvent | ProviderResult | ProviderError], None],
    ) -> ProviderResult:
        total = 0
        text: list[str] = []
        text_size = 0
        event: list[str] = []
        event_size = 0
        finished = False
        while True:
            line = response.readline(_MAX_LINE + 1)
            total += len(line)
            if not line or len(line) > _MAX_LINE or total > _MAX_BYTES:
                raise ProviderError("protocol_error", "SSE ended or exceeded byte budget")
            decoded = line.decode("utf-8").rstrip("\r\n")
            if decoded:
                if decoded.startswith("data:"):
                    value = decoded[5:].removeprefix(" ")
                    event.append(value)
                    event_size += len(value)
                    if event_size > _MAX_LINE:
                        raise ProviderError("protocol_error", "SSE event exceeds byte budget")
                continue
            if not event:
                continue
            data = "\n".join(event)
            event.clear()
            event_size = 0
            if data == "[DONE]":
                if not finished:
                    raise ProviderError("protocol_error", "SSE lacks terminal finish reason")
                return ProviderResult("".join(text), deployment_id=self.deployment_id)
            choice = _choice(_object(json.loads(data)), allow_empty=True)
            if choice is None:
                continue
            delta = _object(choice.get("delta", {}))
            self._verify_text_message(delta)
            content = delta.get("content")
            if content is not None:
                if finished or not isinstance(content, str):
                    raise ProviderError("protocol_error", "Unexpected SSE text after completion")
                text_size += len(content)
                if text_size > _MAX_TEXT:
                    raise ProviderError("protocol_error", "SSE text exceeds output budget")
                text.append(content)
                emit(ProviderEvent("text_delta", {"delta": content}))
            reason = choice.get("finish_reason")
            if reason is not None:
                if reason != "stop":
                    raise ProviderError("incomplete", "Stream did not finish normally")
                finished = True
