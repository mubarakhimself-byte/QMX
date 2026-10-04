"""Bounded native activities. QMX owns admission; the SDK owns the inner loop.

These are host composition entrypoints, never renderer-configurable factories.
Session references are journal observations, not grants. Unknown turns are never
automatically replayed. No BaseChatModel or second agent graph is involved.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import math
import threading
import time
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import asdict, dataclass
from typing import Any, Literal, Protocol

from qmf.core import is_refusal

from .contracts import ProviderCapabilities, ProviderEvent, ProviderRequest, ProviderResult
from .graph_storage import JournalRecords
from .providers import ProviderCancelled, ProviderError
from .service import RequestRuntime
from .tool_loop import ToolBinding, ToolLoopProvider


@dataclass(frozen=True)
class SessionEvent:
    kind: Literal["started", "text", "terminal"]
    session_id: str
    turn_id: str = ""
    text: str = ""
    status: Literal["completed", "interrupted", "failed"] = "completed"


class SessionBackend(Protocol):
    """A single native turn, with explicit lifecycle and terminal evidence."""

    provider_id: str
    binding_identity: str
    available: bool

    async def start(
        self, request: ProviderRequest, operation: Callable[..., Any], *, check: Callable[[], None]
    ) -> None: ...

    async def resume(
        self,
        session_id: str,
        request: ProviderRequest,
        operation: Callable[..., Any],
        *,
        check: Callable[[], None],
    ) -> None: ...

    def events(self) -> AsyncIterator[SessionEvent]: ...

    async def cancel(self) -> None: ...

    async def close(self) -> None: ...


class NativeSessionProvider:
    """Synchronous daemon seam, also usable as one bounded LangGraph activity.

    A factory creates one SDK client per activity. Successful consecutive turns
    resume only the journal-bound conversation. An unobserved terminal outcome
    blocks continuation until explicit external reconciliation; retry never
    creates another native session to conceal an unknown outcome.
    """

    def __init__(
        self,
        backend_factory: Callable[[], SessionBackend],
        *,
        provider_id: str,
        now: Callable[[], str],
        tools: Mapping[str, ToolBinding] | None = None,
        profile_tools: Mapping[str, frozenset[str]] | None = None,
        max_events: int = 1024,
        max_result_bytes: int = 65536,
        max_tool_calls: int = 8,
    ) -> None:
        self.backend_factory = backend_factory
        self.now = now
        self.tools = dict(tools or {})
        self.profile_tools = dict(profile_tools or {})
        self.runtime: RequestRuntime | None = None
        self._capabilities = ProviderCapabilities(
            provider_id,
            resume=backend_factory().available,
            native_tools=False,
            execution_kind="agent_session",
        )
        self.max_events = max_events
        self.max_result_bytes = max_result_bytes
        self.max_tool_calls = max_tool_calls
        self._activity_lock = threading.Lock()
        if min(max_events, max_result_bytes, max_tool_calls) <= 0:
            raise ValueError("positive native activity limits required")

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    def bind_runtime(self, runtime: RequestRuntime) -> None:
        if self.runtime is not None and self.runtime is not runtime:
            raise ValueError("native activity already bound to another host")
        self.runtime = runtime

    def results(self, request_id: str) -> ProviderResult | None:
        """Return an observed result only under the original current host scope."""
        if self.runtime is None:
            raise ProviderError("unbound_session", "Host request owner unavailable")
        row = self.runtime.validate_request_context(request_id, now=self.now())
        if is_refusal(row):
            raise ProviderError(
                "scope_interrupt", "Current host scope forbids native result access"
            )
        return row.value.result

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        return asyncio.run(self.activity(request, emit, cancellation))

    async def activity(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        """One start/resume/terminal activity; no graph-owned native context."""
        if not self._activity_lock.acquire(blocking=False):
            raise ProviderError("session_busy", "Another native activity owns this provider")
        try:
            return await self._activity(request, emit, cancellation)
        finally:
            self._activity_lock.release()

    async def _activity(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        runtime = self.runtime
        if runtime is None or not request.request_id or request.thread_id is not None:
            raise ProviderError("unbound_session", "Host-owned native session binding required")
        if not math.isfinite(request.timeout_seconds) or not 0 < request.timeout_seconds <= 600:
            raise ProviderError("invalid_input", "Native activity duration must be bounded")
        deadline = time.monotonic() + request.timeout_seconds

        def guard() -> None:
            if cancellation.is_set():
                raise ProviderError("cancellation_requested", "Host requested interruption")
            if time.monotonic() >= deadline:
                raise ProviderError("scope_interrupt", "Native activity deadline elapsed")
            if is_refusal(runtime.validate_active_request(request.request_id, now=self.now())):
                raise ProviderError("scope_interrupt", "Current host scope forbids continuation")

        guard()
        owner = runtime.get(request.request_id)
        if is_refusal(owner):
            raise ProviderError("unbound_session", "Host request owner unavailable")
        spec = owner.value.spec
        if (request.prompt, request.instructions, request.model) != (
            spec.prompt,
            spec.profile.instructions,
            spec.model,
        ):
            raise ProviderError(
                "unbound_session", "Native input differs from admitted host request"
            )
        backend = self.backend_factory()
        if not backend.available:
            raise ProviderError(
                "unsupported",
                "Native supplied-text configuration or required policy review is missing",
            )
        body = asdict(spec)
        for key in ("idempotency_key", "prompt", "timeout_seconds"):
            body.pop(key)
        body["context_binding"] = owner.value.context_binding
        body["native_contract"] = "sdk-session-1"
        body["backend_binding"] = backend.binding_identity
        body["cwd"] = request.cwd
        body["tools"] = {
            name: {
                "descriptor": dict(binding.descriptor.to_payload()),
                "contribution": asdict(binding.contribution),
                "instance": asdict(binding.instance),
                "grant": binding.grant_id,
                "argument_scope": binding.argument_scope,
            }
            for name, binding in self.tools.items()
        }
        body["profile_tools"] = {
            profile: sorted(names) for profile, names in self.profile_tools.items()
        }
        key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        records = JournalRecords(runtime.journal)
        previous = records.get("native_session", key)
        if previous and previous["status"] not in {"completed", "interrupted", "not_submitted"}:
            raise ProviderError("outcome_unknown", "Native turn requires external reconciliation")
        allowed = self.profile_tools.get(spec.profile.profile_id, frozenset())
        if allowed - self.tools.keys():
            raise ProviderError("tool_denied", "Native host operation binding unavailable")
        # Reuse dispatch and durable effect receipts, never ToolLoopProvider.execute.
        dispatcher = ToolLoopProvider(
            self,
            provider_id=self.capabilities.provider_id,
            tools=self.tools,
            profile_tools=self.profile_tools,
            now=self.now,
        )
        dispatcher.bind_runtime(runtime)
        calls = 0
        operation_lock = threading.Lock()

        async def operation(
            name: str,
            arguments: Mapping[str, object],
            invocation_id: str,
            agent_id: str | None = None,
        ) -> Mapping[str, object]:
            nonlocal calls
            guard()
            if agent_id is not None or name not in allowed or not invocation_id:
                raise ProviderError("tool_denied", "Subagent or ungranted native tool refused")
            with operation_lock:
                calls += 1
                if calls > self.max_tool_calls:
                    raise ProviderError("tool_denied", "Native host operation limit exhausted")
            # Host callbacks remain bounded/cooperative, as in the existing runtime.
            output = dispatcher.dispatch(
                request,
                name,
                arguments,
                f"{request.request_id}:native:{invocation_id}",
                emit,
                cancellation,
                records=records,
            )
            guard()  # Do not disclose an observation after scope expiry/revocation.
            return output

        session_id = str(previous["session_id"]) if previous else ""
        turn_id = ""
        status = "unknown"
        content = ""
        stop_reason: str | None = None
        records.put(
            "native_session",
            key,
            {
                "status": "pending",
                "session_id": session_id,
                "request_id": request.request_id,
            },
        )

        async def watch() -> None:
            nonlocal stop_reason
            warned = False
            while status == "unknown":
                await asyncio.sleep(0.05)
                try:
                    guard()
                except ProviderError as exc:
                    stop_reason = exc.code
                    # connect/query may not yet be interruptible. Keep watching
                    # until the SDK accepts interruption, or the outer deadline.
                    try:
                        await backend.cancel()
                    except Exception:
                        if not warned:
                            emit(ProviderEvent("native_interrupt_pending"))
                            warned = True
                        continue
                    return

        watcher: asyncio.Task[None] | None = None
        try:
            # Timeout covers connection/start as well as streaming. Interrupt gets
            # a bounded drain window; timeout/kill alone is never cancellation proof.
            async with asyncio.timeout(request.timeout_seconds + 2):
                guard()
                watcher = asyncio.create_task(watch())
                if session_id:
                    await backend.resume(session_id, request, operation, check=guard)
                else:
                    await backend.start(request, operation, check=guard)
                count = 0
                async for event in backend.events():
                    count += 1
                    if count > self.max_events:
                        raise ProviderError("outcome_unknown", "Native event limit exhausted")
                    if not event.session_id or (session_id and event.session_id != session_id):
                        raise ProviderError("outcome_unknown", "Native session identity mismatch")
                    session_id = event.session_id
                    if event.turn_id:
                        if turn_id and event.turn_id != turn_id:
                            raise ProviderError("outcome_unknown", "Native turn identity mismatch")
                        turn_id = event.turn_id
                    if event.kind == "started":
                        records.put(
                            "native_session",
                            key,
                            {
                                "status": "pending",
                                "session_id": session_id,
                                "request_id": request.request_id,
                            },
                        )
                        emit(
                            ProviderEvent(
                                "native_session_started",
                                {
                                    "thread_id": session_id,
                                    "resumed": bool(previous),
                                },
                            )
                        )
                    elif event.kind == "text":
                        if stop_reason is not None:
                            continue
                        try:
                            guard()
                        except ProviderError as exc:
                            stop_reason = exc.code
                            await backend.cancel()
                            continue
                        content += event.text
                        if len(content.encode()) > self.max_result_bytes:
                            raise ProviderError("outcome_unknown", "Native result limit exhausted")
                    elif event.kind == "terminal":
                        if not content and event.text:
                            if len(event.text.encode()) > self.max_result_bytes:
                                raise ProviderError(
                                    "outcome_unknown", "Native result limit exhausted"
                                )
                            content = event.text
                        status = event.status
                        break
                if status == "unknown":
                    raise ProviderError("outcome_unknown", "Native terminal evidence missing")
                records.put(
                    "native_session",
                    key,
                    {
                        "status": status,
                        "session_id": session_id,
                        "turn_id": turn_id,
                        "request_id": request.request_id,
                    },
                )
                emit(
                    ProviderEvent(
                        "native_session_terminal",
                        {
                            "thread_id": session_id,
                            "turn_id": turn_id,
                            "status": status,
                        },
                    )
                )
                if status == "interrupted":
                    if stop_reason == "cancellation_requested":
                        raise ProviderCancelled()
                    raise ProviderError("scope_interrupt", "Native interruption observed")
                if status != "completed":
                    raise ProviderError("native_failed", "Native session reported failure")
                if cancellation.is_set():
                    # Interruption may race a completed turn. Preserve actual
                    # terminal evidence, while retaining current disclosure checks.
                    context = runtime.validate_request_context(request.request_id, now=self.now())
                    if is_refusal(context):
                        raise ProviderError(
                            "scope_interrupt", "Current scope forbids result access"
                        )
                else:
                    guard()
                return ProviderResult(content, session_id, turn_id or None)
        except (TimeoutError, asyncio.CancelledError) as exc:
            raise ProviderError("outcome_unknown", "Native terminal outcome unobserved") from exc
        except Exception as exc:
            if status == "unknown":
                if (
                    getattr(backend, "turn_submitted", True) is False
                    and calls == 0
                    and isinstance(exc, ProviderError)
                    and exc.code
                    in {
                        "unsupported",
                        "unsafe_config",
                        "auth_required",
                        "subscription_required",
                        "invalid_input",
                        "interrupt_pending",
                        "scope_interrupt",
                        "cancellation_requested",
                    }
                ):
                    # Known pre-turn refusal is safe to fix/retry. Preserve a
                    # previous proven native session; no turn was submitted.
                    records.put(
                        "native_session",
                        key,
                        previous
                        or {
                            "status": "not_submitted",
                            "session_id": "",
                            "request_id": request.request_id,
                        },
                    )
                    raise
                raise ProviderError(
                    "outcome_unknown", "Native terminal outcome unobserved"
                ) from exc
            raise
        finally:
            if watcher is not None:
                watcher.cancel()
            # Cleanup errors must neither hang the daemon nor erase an observed
            # terminal outcome. Missing evidence stays pending in the journal.
            with contextlib.suppress(Exception):
                async with asyncio.timeout(2):
                    if watcher is not None:
                        await asyncio.gather(watcher, return_exceptions=True)
                    if status == "unknown":
                        with contextlib.suppress(Exception):
                            async with asyncio.timeout(0.5):
                                await backend.cancel()
                    await backend.close()
