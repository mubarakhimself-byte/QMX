"""Official Codex SDK lifecycle; local execution fails closed on scope limits.

The reviewed runtime lacks a demonstrated complete restricted-read/network
boundary for ordinary native tools on this Windows host. Approval hooks cannot
repair that gap. The public backend is unavailable and cannot launch a process.
The lifecycle below is tested against SDK-compatible offline clients so a later
host isolation implementation can reuse it without adding a JSONL protocol.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any, Literal, cast

from openai_codex import ApprovalMode, AsyncCodex, Sandbox
from openai_codex.generated.v2_all import (
    AgentMessageDeltaNotification,
    TurnCompletedNotification,
)

from .contracts import ProviderRequest
from .native_sessions import SessionEvent
from .providers import ProviderError

CODEX_SDK_VERSION = "0.160.0"
CODEX_RUNTIME_VERSION = "0.160.0"


class CodexSessionBackend:
    provider_id = "openai-codex:0.160.0:cli-0.160.0"
    binding_identity = provider_id
    available = False

    async def start(
        self, request: ProviderRequest, operation: Callable[..., Any], *, check: Callable[[], None]
    ) -> None:
        raise ProviderError(
            "unsupported", "Codex native tools require a demonstrated host isolation boundary"
        )

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
        raise ProviderError("unsupported", "Codex native sessions are unavailable on this host")
        yield  # pragma: no cover - async iterator protocol

    async def cancel(self) -> None:
        return

    async def close(self) -> None:
        return


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
