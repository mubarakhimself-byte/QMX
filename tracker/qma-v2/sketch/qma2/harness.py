"""The harness: one facade, one actor per thread, one host process per live thread.

    qmx-control process                                       host process (per live thread)
    -------------------                                       -----------------------------
    Harness ──owns──> _ThreadActor (sole owner of a thread)   python -m qma2.host
       │                 │  policy.evaluate  (one policy point)   ├─ host/claude.py  (claude_agent_sdk
       │                 │  hooks.HookRunner                       │     -> spawns the Claude CLI)
       │                 │  store.Store (single writer)            └─ host/openai.py  (openai-agents,
       │                 │  Sink -> ControlService (blocks)             QMX tools in host/tools.py)
       │                 └── stdio link (wire.py) <────────────────────── every tool call asks first
       ├── _RuleBook (sole owner of remembered rules)
       ├── _HostSupervisor (spawn with allow-listed env, kill-tree)
       └── Accounts, router.pick, usage

Shared-state rule (separate-before-serializing): each thread's live state has exactly one
writer, its actor. Cross-thread state has one owner each: the RuleBook (rules), the Store
(harness.db), the Supervisor (processes). Hosts own only their SDK's in-memory state and
never write anything durable themselves.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Protocol

from qma2.accounts import Accounts
from qma2.config import ConfigHome, ResolvedConfig
from qma2.hooks import HookRunner
from qma2.model import (
    AgentPath,
    Answer,
    ApprovalId,
    ApprovalView,
    Block,
    Decision,
    Event,
    JsonValue,
    Mode,
    OperatorProof,
    Route,
    SwitchQuote,
    SwitchTarget,
    ThreadId,
    ThreadSpec,
    ThreadStatus,
    ThreadView,
    ToolCall,
    TurnAccepted,
    TurnId,
    TurnInput,
    UsageReport,
    Verdict,
)
from qma2.money import MoneySurface, OrderProposal, ToolCatalog
from qma2.policy import PolicyState, RuleSnapshot
from qma2.store import Store
from qma2.wire import Down, Up

# ------------------------------------------------------------------ ports (implemented by qmx_control)


class Sink(Protocol):
    """Where the UI-facing record goes. qmx_control implements it over ControlService, so
    the 14 block kinds, the events table and SSE stay exactly as they are."""

    async def create_session(self, title: str, origin: str, parent: ThreadId | None) -> ThreadId: ...

    async def block(self, session: ThreadId, block: Block) -> None:
        """Durable, append-only (sessions_append)."""
        ...

    async def topic(self, topic: Literal["approvals", "usage", "sessions"], subject: str, data: Mapping[str, JsonValue]) -> None:
        """Durable topic event for cross-session views (approvals inbox, usage page)."""
        ...


class ProposalSink(Protocol):
    """qmx_control's handler for the one proposal tool (writes an unsigned Portfolio
    proposal through qmx_broker). qma2 never imports qmx_broker."""

    async def propose(self, proposal: OrderProposal, thread: ThreadId, agent_path: AgentPath) -> Mapping[str, JsonValue]: ...


class AgentOps(Protocol):
    """QMX control operations offered to agents as `mcp__qmx__<op>` tools. qmx_control
    derives the list from OPERATIONS rows with who=ANY; operator rows can't appear."""

    def catalog(self) -> Sequence[Mapping[str, JsonValue]]: ...
    async def call(self, name: str, args: Mapping[str, JsonValue], thread: ThreadId, agent_path: AgentPath) -> JsonValue: ...


@dataclass(frozen=True, slots=True)
class HarnessOptions:
    home: Path
    sink: Sink
    proposals: ProposalSink
    agent_ops: AgentOps
    control_settings: Mapping[str, JsonValue]  # settings.toml sections (router, mcp_servers, brokers)
    idle_host_seconds: int = 1800
    max_live_hosts: int = 8  # Claude needs ~1 GiB per live session (H1 fact 9)


class HarnessError(Exception):
    """Mapped to {"error": {code, message}} by qmx_control."""

    code: Literal[
        "not_found", "turn_in_progress", "thread_locked", "quote_stale", "already_resolved",
        "approval_expired", "no_route", "auth_required", "archived",
    ]


# --------------------------------------------------------------------------- the facade


class Harness:
    """Everything a caller can do with QMX agents. qmx_control's agent_ops.py binds each
    public method to one OPERATIONS row; the temporary console calls those rows.

    What this hides: process lifecycle, both SDKs, the policy chain, hooks, approvals'
    rendezvous between an HTTP answer and a waiting engine callback, routing, resume
    across restarts, compaction, usage capture, and the single-writer store.
    """

    accounts: Accounts

    @classmethod
    @asynccontextmanager
    async def open(cls, options: HarnessOptions) -> AsyncIterator[Harness]:
        """Open harness.db, recover, yield, then stop every host.

        # TODO pseudocode (recovery is idempotent; running it twice changes nothing)
        # store = await Store.open(home / "harness.db")
        # for turn in store.running_turns(): end_turn(turn, "interrupted")
        # for aid in store.expire_pending(None): sink.block(permission{approval_id, status: expired})
        # yield harness   # actors open lazily on first use
        # finally: supervisor.stop_all(); writer.close()
        """
        raise NotImplementedError
        yield  # pragma: no cover

    # threads ----------------------------------------------------------------

    async def start_thread(self, spec: ThreadSpec) -> ThreadView:
        """Create the UI session (sink), route it (router.pick), persist thread + first
        segment. Does not spawn a host; the first `send` does."""
        raise NotImplementedError

    async def threads(self, *, archived: bool = False) -> Sequence[ThreadView]:
        raise NotImplementedError

    async def thread(self, thread: ThreadId) -> ThreadView:
        raise NotImplementedError

    async def send(self, thread: ThreadId, input: TurnInput) -> TurnAccepted:
        """Start a turn and return at once; progress arrives on `live` and as blocks.
        Idempotent on input.client_turn_id. Raises turn_in_progress (use `steer`) or
        thread_locked (until a reset or a quoted switch)."""
        raise NotImplementedError

    async def steer(self, thread: ThreadId, text: str, *, expected_turn: TurnId) -> None:
        """Add input to the running turn (Codex turn/steer precondition: refused if the
        running turn is not `expected_turn`)."""
        raise NotImplementedError

    async def interrupt(self, thread: ThreadId) -> None:
        """Stop the running turn. Pending approvals expire; tool processes are killed."""
        raise NotImplementedError

    async def compact(self, thread: ThreadId, focus: str | None = None) -> None:
        raise NotImplementedError

    async def fork(self, thread: ThreadId, *, at_turn: TurnId | None, title: str) -> ThreadView:
        raise NotImplementedError

    async def archive(self, thread: ThreadId) -> None:
        raise NotImplementedError

    async def set_mode(self, thread: ThreadId, mode: Mode, proof: OperatorProof) -> None:
        """Operator only: an agent must never raise its own permission mode."""
        raise NotImplementedError

    async def quote_switch(self, thread: ThreadId, target: SwitchTarget) -> SwitchQuote:
        """Price a model/effort/engine change before it happens (the cost pop-up)."""
        raise NotImplementedError

    async def switch(self, thread: ThreadId, quote: SwitchQuote, proof: OperatorProof) -> ThreadView:
        """Apply a quote. Refused with quote_stale when a turn ran since the quote."""
        raise NotImplementedError

    def live(self, thread: ThreadId) -> AsyncIterator[Event]:
        """Live fan-out: deltas, tool progress, usage ticks, status. Lossy by design; the
        first event is a snapshot (status, pending approvals) so a reconnect is whole."""
        raise NotImplementedError

    # approvals --------------------------------------------------------------

    async def approvals(self, *, thread: ThreadId | None = None, pending_only: bool = True) -> Sequence[ApprovalView]:
        raise NotImplementedError

    async def answer(self, approval: ApprovalId, answer: Answer, proof: OperatorProof) -> ApprovalView:
        """Resolve a pending approval. Idempotent: the same choice twice returns the stored
        view; a different choice after resolution raises already_resolved; an expired
        approval raises approval_expired. Money calls never reach here (never Pending)."""
        raise NotImplementedError

    # usage and export -------------------------------------------------------

    async def usage(self, *, since: datetime | None = None) -> UsageReport:
        raise NotImplementedError

    async def export(self, thread: ThreadId) -> Path:
        """One action: a zip with items.jsonl (canonical transcript), segments, turns,
        approvals, usage rows, Claude's raw session JSONL from claude-home, and the
        thread's local traces. Secrets redacted. Writes under <home>/exports/."""
        raise NotImplementedError


# ------------------------------------------------------------------------ internals


class _RuleBook:
    """Sole owner of remembered rules (harness.db `rules`) merged with file layers.
    Actors read snapshots; only `remember` writes. No file is ever written by an
    answer, so two threads in one project can't race on settings.local.json."""

    async def snapshot(self, thread: ThreadId, config: ResolvedConfig, project_root: Path) -> RuleSnapshot:
        raise NotImplementedError

    async def remember(self, approval: ApprovalView, answer: Answer) -> None:
        raise NotImplementedError


@dataclass
class _HostHandle:
    pid: int
    send: object  # async (Down) -> None
    receive: object  # AsyncIterator[Up]


class _HostSupervisor:
    """Spawns `python -m qma2.host` with secrets.host_env, cwd pinned to the workspace,
    in its own Job Object (Windows, KILL_ON_JOB_CLOSE) or process group (POSIX), so
    killing a host kills the Claude CLI and every tool process under it (H1)."""

    async def spawn(self, route: Route, cwd: Path) -> _HostHandle:
        raise NotImplementedError

    async def kill(self, handle: _HostHandle) -> None:
        raise NotImplementedError

    async def stop_all(self) -> None:
        raise NotImplementedError


class _ThreadActor:
    """Sole writer of one thread's state. Mailbox-driven; one asyncio task.

    State machine (model.ThreadStatus): Idle -> Running -> Idle; Running may hold pending
    approvals; any -> LockedOut on a `rejected` limit for the route's account; any ->
    Failed when the host exits unexpectedly (other threads unaffected).
    """

    status: ThreadStatus
    config: ResolvedConfig
    hooks: HookRunner
    catalog: ToolCatalog
    surface: MoneySurface
    _pending: dict[ApprovalId, asyncio.Future[Verdict]]
    _granted: set[str]  # tool_use_ids with an Allow verdict, consumed by CallOp (one shot)
    _cache_epoch: int  # bumps every turn; pins SwitchQuotes

    async def send(self, input: TurnInput) -> TurnAccepted:
        """# TODO pseudocode
        # turn, dup = await store.begin_turn(...)  ; if dup: return TurnAccepted(dup=True)
        # outcome = await hooks.run(UserPromptSubmit(...)); if outcome.block: end turn, return
        # host = await self._ensure_host()   # spawn + Spawn msg + SessionStart hook context
        # await host.send(Turn(turn, input, outcome.context + session_start_context))
        # sink.block(user block); emit turn.started; status = Running(turn)
        """
        raise NotImplementedError

    async def on_up(self, message: Up) -> None:
        """# TODO pseudocode
        # Emit      -> event = wrap(message); store items (idempotent on source_key);
        #              block = to_block(event) -> sink.block; fan out live
        # Started   -> record sdk_session_id on the segment (first time only)
        # Ask(Gate) -> reply(await self.gate(call))
        # Ask(Await)-> reply(await self._pending[aid])  (expired -> Deny("expired"))
        # Ask(Hook) -> reply(await hooks.run(event))
        # Ask(LoadItems) -> reply(store.active_items(thread))
        # Ask(CallOp) -> require tool_use_id in _granted (discard it); route to
        #               proposals.propose (ProposalToolSpec) or agent_ops.call
        # TurnEnded -> store.end_turn; status Idle (or LockedOut); bump _cache_epoch
        # Usage/Limits -> store.record_*; sink.topic("usage"); maybe LockedOut
        # Bye / EOF -> Failed("host_exited"); expire pending approvals; end turn interrupted
        """
        raise NotImplementedError

    async def gate(self, call: ToolCall) -> Verdict:
        """The one entry from either engine into policy.

        # TODO pseudocode
        # d: Decision = await policy.evaluate(call, self._policy_state(), hooks, catalog, surface)
        # Allow -> self._granted.add(call.tool_use_id); return d
        # Deny  -> emit tool.finished(status=denied, source); return d
        # NeedsOperator ->
        #     pr = await hooks.run(PermissionRequest(call))     # may allow/deny without a human
        #     if pr.decision in {"allow","deny"}: return as above
        #     view = ApprovalView(new id, PENDING, ...); await store.open_approval(view)
        #     sink.block(permission{approval_id,...}); sink.topic("approvals", ...); live
        #     self._pending[id] = Future(); return Pending(id)
        """
        raise NotImplementedError

    async def resolve(self, approval: ApprovalId, answer: Answer) -> ApprovalView:
        """# TODO pseudocode
        # if answer.edited_input: money.classify(edited call) is MoneyHit -> Deny(MONEY)
        # view = await store.resolve_approval(...)      # idempotent on same choice
        # if choice in {ALLOW_THREAD, ALLOW_ALWAYS}: await rulebook.remember(view, answer)
        # future.set_result(Allow(edited or original input) | Deny(message, OPERATOR))
        # sink.block(permission{approval_id, decision}); if DENY_AND_STOP: self.interrupt()
        """
        raise NotImplementedError

    def _policy_state(self) -> PolicyState:
        raise NotImplementedError

    async def _ensure_host(self) -> object:
        """Spawn on demand; reap after idle_host_seconds; resume from the segment
        (Claude: resume=sdk_session_id; OpenAI: LoadItems)."""
        raise NotImplementedError

    async def _send(self, message: Down) -> None:
        raise NotImplementedError

    def _decision_for_log(self, decision: Decision) -> Mapping[str, JsonValue]:
        raise NotImplementedError
