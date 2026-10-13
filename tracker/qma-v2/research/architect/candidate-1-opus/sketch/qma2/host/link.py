"""Host side of the stdio link. The only thing adapters and tools use to reach QMX."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence

from qma2.hooks import HookEvent, HookOutcome
from qma2.model import AgentPath, Allow, ApprovalId, Deny, EventKind, JsonValue, LimitSnapshot, Pending, SegmentId, ToolCall, TurnId, UsageRow
from qma2.wire import Down, Spawn


class Link:
    async def first(self) -> Spawn:
        raise NotImplementedError

    def downs(self) -> AsyncIterator[Down]:
        raise NotImplementedError

    # facts (fire and forget, ordered)
    async def emit(self, kind: EventKind, *, turn: TurnId | None, agent_path: AgentPath, source_key: str | None, data: Mapping[str, JsonValue]) -> None: ...
    async def started(self, sdk_session_id: str | None, tools: Sequence[str]) -> None: ...
    async def turn_ended(self, turn: TurnId, status: str, detail: str | None = None) -> None: ...
    async def usage(self, rows: Sequence[UsageRow]) -> None: ...
    async def limits(self, snapshots: Sequence[LimitSnapshot]) -> None: ...

    # questions (one reply each)
    async def gate(self, call: ToolCall) -> Allow | Deny | Pending:
        raise NotImplementedError

    async def await_decision(self, approval: ApprovalId) -> Allow | Deny:
        """No timeout: the agent waits for the operator. Returns Deny("expired") if the
        control side expires the approval (interrupt, shutdown)."""
        raise NotImplementedError

    async def decide(self, call: ToolCall) -> Allow | Deny:
        """gate() then await_decision() when Pending. What OpenAI tool wrappers use."""
        raise NotImplementedError

    async def hook(self, event: HookEvent) -> HookOutcome:
        raise NotImplementedError

    async def load_items(self, segment: SegmentId) -> Sequence[Mapping[str, JsonValue]]:
        raise NotImplementedError

    async def call_op(self, tool_use_id: str, name: str, args: Mapping[str, JsonValue], agent_path: AgentPath) -> JsonValue:
        raise NotImplementedError
