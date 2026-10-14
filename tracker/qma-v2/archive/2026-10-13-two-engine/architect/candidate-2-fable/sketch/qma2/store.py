"""Single-writer SQLite store for `agents.db`. Every write in qma2 goes through one thread.

Why its own file: control.db keeps sessions/blocks/events for the UI and is written by
ControlService with per-call connections (Gotcha 1, SQLite 3.50.4 WAL bug). qma2 never opens
control.db. Cross-file references are plain ids: ThreadId == control session id.

Writer: one thread, one connection, `autocommit=False`, drains an inbox into group commits
(`BEGIN IMMEDIATE`... `COMMIT`) every 25 ms or 64 ops. Readers: a small pool of `mode=ro`
connections. Pragmas: WAL, busy_timeout=5000, synchronous=FULL (approvals, ledger, operator
verifier are precious), foreign_keys=ON.

Migrations are numbered and idempotent (`schema_version` row). Re-running `migrate()` is a
no-op.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from qma2.types import (
    Account,
    AccountId,
    Approval,
    ApprovalAnswer,
    ApprovalId,
    ApprovalRequest,
    LimitSnapshot,
    Segment,
    SegmentEnd,
    SegmentId,
    StopReason,
    Thread,
    ThreadId,
    ThreadStatus,
    Turn,
    TurnId,
    TurnInput,
    TurnStatus,
    UsageRow,
)

SCHEMA: tuple[str, ...] = (
    # v1
    """
    CREATE TABLE schema_version(version INTEGER NOT NULL);
    CREATE TABLE threads(
      id TEXT PRIMARY KEY, title TEXT NOT NULL, cwd TEXT NOT NULL, parent_id TEXT,
      status TEXT NOT NULL, current_segment_id TEXT NOT NULL, background INTEGER NOT NULL DEFAULT 0,
      archived INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
    CREATE TABLE segments(
      id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES threads(id), engine TEXT NOT NULL,
      account_id TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, effort TEXT NOT NULL,
      mode TEXT NOT NULL, engine_session_id TEXT, seed_from_block_seq INTEGER,
      started_at INTEGER NOT NULL, ended_at INTEGER, end_reason TEXT);
    CREATE INDEX segments_thread ON segments(thread_id, started_at);
    CREATE TABLE turns(
      id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES threads(id), segment_id TEXT NOT NULL,
      seq INTEGER NOT NULL, client_key TEXT NOT NULL, input_json TEXT NOT NULL, status TEXT NOT NULL,
      stop_reason TEXT, started_at INTEGER, ended_at INTEGER,
      UNIQUE(thread_id, seq), UNIQUE(thread_id, client_key));
    CREATE TABLE approvals(
      id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, turn_id TEXT NOT NULL, agent_path TEXT NOT NULL,
      request_json TEXT NOT NULL, status TEXT NOT NULL, answer_json TEXT, created_at INTEGER NOT NULL,
      answered_at INTEGER, engine_state BLOB);           -- OpenAI RunState for resume after restart
    CREATE INDEX approvals_open ON approvals(status, created_at);
    CREATE TABLE accounts(
      id TEXT PRIMARY KEY, provider TEXT NOT NULL, kind TEXT NOT NULL, label TEXT NOT NULL,
      engine TEXT NOT NULL, models_json TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
      credential_ref TEXT, claude_home TEXT, base_url TEXT, background_cap_pct INTEGER NOT NULL DEFAULT 50,
      created_at INTEGER NOT NULL);
    CREATE TABLE usage(
      dedupe_key TEXT PRIMARY KEY, at INTEGER NOT NULL, account_id TEXT NOT NULL, provider TEXT NOT NULL,
      model TEXT NOT NULL, thread_id TEXT NOT NULL, turn_id TEXT NOT NULL, agent_path TEXT NOT NULL,
      uncached_input INTEGER NOT NULL, cache_read INTEGER NOT NULL, cache_write INTEGER NOT NULL,
      output INTEGER NOT NULL, reasoning INTEGER NOT NULL DEFAULT 0, reported_cost_usd REAL,
      is_compaction INTEGER NOT NULL DEFAULT 0);
    CREATE INDEX usage_account_time ON usage(account_id, at);
    CREATE INDEX usage_thread ON usage(thread_id, at);
    CREATE TABLE limits(
      account_id TEXT NOT NULL, window TEXT NOT NULL, taken_at INTEGER NOT NULL, used_pct REAL NOT NULL,
      resets_at INTEGER, status TEXT NOT NULL, source TEXT NOT NULL,
      PRIMARY KEY(account_id, window, taken_at));
    CREATE TABLE operator(
      id INTEGER PRIMARY KEY CHECK(id = 1), verifier TEXT NOT NULL,   -- argon2id of the passphrase
      created_at INTEGER NOT NULL, rotated_at INTEGER);
    """,
)


class Store:
    @classmethod
    def open(cls, path: Path) -> Store:
        raise NotImplementedError

    def migrate(self) -> None:
        """Apply SCHEMA entries above `schema_version`; idempotent."""
        raise NotImplementedError

    async def close(self) -> None:
        """Drain the inbox, checkpoint (PASSIVE), close."""
        raise NotImplementedError

    # ---- threads / segments / turns (writes are enqueued; awaited = committed)

    async def thread_insert(self, thread: Thread, first: Segment) -> None: ...
    async def thread_set_status(self, thread_id: ThreadId, status: ThreadStatus) -> None: ...
    async def thread_set_archived(self, thread_id: ThreadId, archived: bool) -> None: ...
    def thread_get(self, thread_id: ThreadId) -> Thread | None: ...
    def thread_list(self, *, archived: bool) -> Sequence[Thread]: ...
    def threads_open(self) -> Sequence[Thread]:
        """RUNNING or WAITING: what `Harness.start` reconciles."""
        ...

    async def segment_insert(self, segment: Segment) -> None: ...
    async def segment_bind(self, segment_id: SegmentId, engine_session_id: str) -> None: ...
    async def segment_end(self, segment_id: SegmentId, reason: SegmentEnd) -> None: ...
    async def segment_set_model(self, segment_id: SegmentId, model: str, effort: str) -> None: ...
    def segment_current(self, thread_id: ThreadId) -> Segment: ...

    async def turn_insert(self, turn: Turn) -> Turn:
        """Insert-or-return on (thread_id, client_key)."""
        ...

    async def turn_set(self, turn_id: TurnId, status: TurnStatus, stop_reason: StopReason | None) -> None: ...
    def turn_running(self, thread_id: ThreadId) -> Turn | None: ...
    def turn_get(self, turn_id: TurnId) -> Turn | None: ...

    # ---- approvals

    async def approval_insert(self, approval: Approval, engine_state: bytes | None) -> None: ...

    async def approval_answer(self, approval_id: ApprovalId, answer: ApprovalAnswer, at: datetime) -> Approval:
        """Compare-and-set: PENDING → ANSWERED. Returns the row either way; the broker decides
        whether a repeat is a no-op (same answer) or `AlreadyAnswered`."""
        ...

    async def approvals_expire(self, not_in_turns: Sequence[TurnId]) -> Sequence[Approval]: ...
    def approvals_pending(self, thread_id: ThreadId | None = None) -> Sequence[Approval]: ...
    def approval_engine_state(self, approval_id: ApprovalId) -> bytes | None: ...

    # ---- accounts / usage / limits

    async def account_upsert(self, account: Account) -> None: ...
    def accounts(self) -> Sequence[Account]: ...
    async def usage_insert(self, row: UsageRow) -> bool:
        """INSERT OR IGNORE; False when the dedupe_key existed."""
        ...
    async def limit_insert(self, snapshot: LimitSnapshot) -> None: ...
    def limits_latest(self, account_id: AccountId | None = None) -> Sequence[LimitSnapshot]: ...
    def usage_between(self, since: datetime, until: datetime) -> Sequence[UsageRow]: ...

    # ---- operator verifier

    def operator_verifier(self) -> str | None: ...
    async def operator_set_verifier(self, verifier: str) -> None: ...
