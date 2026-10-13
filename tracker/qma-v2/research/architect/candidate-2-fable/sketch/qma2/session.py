"""SessionActor: the single owner of one thread's runtime, and the projector from engine
events to UI blocks and ledger rows.

Why an actor: three parties want to change a thread (a turn starting, the operator answering
or stopping, the engine finishing). Rather than lock shared state, each thread has one asyncio
task with an inbox; everyone else posts a message. Per separate-before-serializing.

Trace: agent_ops.py → Harness.turn_start → SessionActor.post(StartTurn) → engine.run() →
project(event). Three files from route to SDK.

Truth per purpose (no duplicate owners):
- model context      → the engine's own transcript (Claude JSONL under claude-home/projects;
                       OpenAI items in QMX's SQLiteSession at <home>/qma2/openai-sessions.db)
- what the operator saw → control.db blocks, written only by this projector via BlockSink
- cost               → agents.db usage rows
- control state      → agents.db threads/segments/turns/approvals
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from qma2.accounts import Router
from qma2.approvals import ApprovalBroker
from qma2.config import ConfigHome, ResolvedConfig
from qma2.engines.base import Engine, EngineSession
from qma2.gate import Gate, Remembered
from qma2.harness import BlockSink
from qma2.store import Store
from qma2.supervisor import Supervisor
from qma2.tools.registry import ToolRegistry
from qma2.types import (
    ApprovalId,
    Effort,
    EngineEvent,
    EngineKind,
    ModelRef,
    PermissionMode,
    Segment,
    SwitchPreview,
    Thread,
    ThreadId,
    Turn,
    TurnId,
    TurnInput,
)

# ------------------------------------------------------------- inbox messages (closed)


@dataclass(frozen=True)
class StartTurn:
    turn: Turn


@dataclass(frozen=True)
class Steer:
    input: TurnInput
    expected_turn: TurnId


@dataclass(frozen=True)
class Stop: ...


@dataclass(frozen=True)
class Switch:
    model: ModelRef | None
    effort: Effort | None
    mode: PermissionMode | None


@dataclass(frozen=True)
class Resume:
    """An OpenAI approval was answered after a restart; continue from stored RunState."""

    approval_id: ApprovalId


@dataclass(frozen=True)
class Compact:
    focus: str


type Message = StartTurn | Steer | Stop | Switch | Resume | Compact


class SessionActor:
    """One per open thread. Started lazily by Harness on first message; idle actors are kept
    (sessions run for days) and their engine session stays open until `close`."""

    def __init__(
        self,
        thread: Thread,
        *,
        engines: Mapping[EngineKind, Engine],
        store: Store,
        sink: BlockSink,
        home: ConfigHome,
        registry: ToolRegistry,
        approvals: ApprovalBroker,
        router: Router,
        supervisor: Supervisor,
    ) -> None:
        self.remembered = Remembered()
        raise NotImplementedError

    def post(self, message: Message) -> None:
        """Enqueue; never blocks. Ordering per thread is the inbox order."""
        raise NotImplementedError

    async def run(self) -> None:
        """The loop.
        # TODO: for msg in inbox:
        #   StartTurn → ensure engine session open for the current segment (open on demand,
        #     resume with segment.engine_session_id); set thread RUNNING; stream events;
        #     project each; on TurnFinished set turn/thread status; usage rows via store.
        #   Steer → refuse if expected_turn != running turn (StaleTurn); else engine.steer.
        #   Stop → engine.interrupt(); supervisor.tree(thread).kill() if the engine doesn't
        #     finish within 2 s; turn INTERRUPTED.
        #   Switch → same engine: engine.switch(model, effort); segment_set_model.
        #            different engine/account: end segment (SWITCHED), new segment seeded with
        #            render_history(blocks); open the new engine lazily on next turn.
        #   Resume → engine.resume_from(approvals.engine_state(id), answer) (OpenAI only).
        #   Compact → engine.compact(focus).
        # Crash mid-turn: the actor's finally block marks the turn FAILED and the thread IDLE;
        # Harness.start reconciles anything the process didn't get to."""
        raise NotImplementedError

    def gate(self, segment: Segment, config: ResolvedConfig) -> Gate:
        """Build the Gate for this segment: policy from config + remembered, hooks runner,
        registry, approvals. One Gate per segment; sub-agents share it."""
        raise NotImplementedError

    async def project(self, event: EngineEvent, turn: Turn) -> None:
        """Exhaustive match over EngineEvent → BlockSink / store. Mapping (copied from
        copilot.stream_turn, extended by research 32 B3):
          TextDone          → `text` {text, role, agent_path, v:1}
          TextDelta         → nothing durable (live channel is later; console prints it)
          ToolStarted       → `tool` {id, name, arguments(preview), state:"started", effect, agent_path}
          ToolFinished      → `tool` {id, state, result(preview), files_changed} ; files → `changed`
          PlanUpdated       → `plan`
          SubagentStarted   → child session via sink.create_session(parent_id=thread) if new
                              agent_path; `agents` {session_id, name, model, state:"working"}
          SubagentFinished  → `agents` {state: outcome}
          Compacted         → `text` {kind:"compaction"}
          UsageRecorded     → store.usage_insert (dedupe)
          LimitUpdated      → store.limit_insert
          SessionBound      → store.segment_bind
          TurnFinished      → turn/thread status; `needs_you` if stop_reason == "needs_input"
        Approval requests are not events: the gate appends `permission` {approval_id, request}
        when it parks, and `permission` {approval_id, decision} when answered."""
        raise NotImplementedError

    async def preview_switch(self, model: ModelRef | None, effort: Effort | None) -> SwitchPreview:
        """Pure over segment + engine capabilities: cache breaks on any model change; on effort
        change only for models without effort-stable caches (H1 fact 6)."""
        raise NotImplementedError


def render_history(blocks: list[tuple[int, str, dict[str, object]]], *, max_tokens: int = 20_000) -> str:
    """Pure: blocks → a handoff summary for a new segment on another engine. Keeps user and
    assistant text verbatim (most recent first within budget), tool calls as one line each."""
    raise NotImplementedError


def child_agent_path(parent: str, name: str, ordinal: int) -> str:
    return f"{parent}/{name}#{ordinal}"
