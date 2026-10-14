"""harness.db: the harness's own SQLite file, with exactly one writer.

One `Writer` thread owns the only write connection (autocommit off, WAL, busy_timeout,
synchronous=FULL), drains a queue and group-commits every 25-100 ms. Readers use a small
read-only pool. Hosts never open this file; they send `Persist`/`Emit` over the link and
the thread actor writes. This removes the SQLite 3.50.4 WAL-reset precondition (two
writing connections) by construction, without touching control.db's existing writers.

Why a separate file instead of new tables in control.db: control.db already has a
writer path (ControlService's per-call connections under its RLock). A second writer
connection on the same file would recreate the WAL-bug precondition. UI-facing records
still land in control.db, but only through ControlService.sessions_append (the Sink).

Every write is idempotent on a natural key, so replays after a crash are no-ops:
turns(thread, client_turn_id), items(thread, source_key), usage(dedupe_key),
approvals(id), rules(scope, scope_key, behavior, rule_text).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from sqlite3 import Connection

from qma2.model import (
    Account,
    AccountId,
    Answer,
    ApprovalId,
    ApprovalView,
    LimitSnapshot,
    Segment,
    SegmentId,
    ThreadId,
    ThreadView,
    TurnId,
    TurnInput,
    UsageRow,
)
from qma2.policy import Rule

SCHEMA_V1 = """
CREATE TABLE threads (
  id TEXT PRIMARY KEY,                 -- == control.db session id
  cwd TEXT NOT NULL, profile TEXT NOT NULL, origin TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('default','acceptEdits','plan','dontAsk','bypassPermissions')),
  archived INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);

CREATE TABLE segments (
  id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES threads(id),
  ordinal INTEGER NOT NULL,
  engine TEXT NOT NULL, account_id TEXT NOT NULL, model TEXT NOT NULL, effort TEXT NOT NULL,
  sdk_session_id TEXT,                 -- Claude resume id
  lineage TEXT NOT NULL, parent_segment_id TEXT, fork_turn_id TEXT,
  started_at INTEGER NOT NULL, ended_at INTEGER, end_reason TEXT,
  UNIQUE (thread_id, ordinal));

CREATE TABLE turns (
  id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, segment_id TEXT NOT NULL,
  client_turn_id TEXT NOT NULL, input_json TEXT NOT NULL,
  status TEXT NOT NULL,                -- running|completed|interrupted|failed|locked_out
  started_at INTEGER NOT NULL, ended_at INTEGER,
  UNIQUE (thread_id, client_turn_id));

-- The canonical transcript for both engines (export, UI rebuild, cross-engine seed).
-- OpenAI resume truth too: the OpenAI host's Session is a view over active rows.
-- Claude's own JSONL in claude-home stays its resume cache (opaque; SDK-owned).
CREATE TABLE items (
  id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, segment_id TEXT NOT NULL,
  seq INTEGER NOT NULL, turn_id TEXT, agent_path TEXT NOT NULL,
  kind TEXT NOT NULL,                  -- user|assistant|reasoning|tool_call|tool_result|compaction|note
  text TEXT, tool_name TEXT, tool_call_id TEXT, tool_input_json TEXT,
  engine TEXT NOT NULL, engine_payload_json TEXT,   -- verbatim SDK item for same-engine replay
  source_key TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
  created_at INTEGER NOT NULL,
  UNIQUE (thread_id, seq), UNIQUE (thread_id, source_key));

CREATE TABLE approvals (
  id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, turn_id TEXT NOT NULL,
  tool_use_id TEXT NOT NULL, agent_path TEXT NOT NULL, kind TEXT NOT NULL,
  call_json TEXT NOT NULL, reason TEXT NOT NULL, suggested_rule TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending','resolved','expired')),
  answer_json TEXT, decided_by TEXT, decided_at INTEGER, created_at INTEGER NOT NULL);
CREATE INDEX approvals_open ON approvals(status, created_at);

CREATE TABLE rules (
  id TEXT PRIMARY KEY, scope TEXT NOT NULL CHECK (scope IN ('user','project','thread')),
  scope_key TEXT NOT NULL,             -- '' | normalised project root | thread id
  behavior TEXT NOT NULL CHECK (behavior IN ('allow','ask','deny')),
  rule_text TEXT NOT NULL, from_approval TEXT, created_at INTEGER NOT NULL,
  UNIQUE (scope, scope_key, behavior, rule_text));

CREATE TABLE accounts (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('claude_subscription','chatgpt','api_key')),
  provider TEXT NOT NULL, label TEXT NOT NULL,
  base_url TEXT, wire TEXT, credential_ref TEXT, config_dir TEXT, models_json TEXT,
  enabled INTEGER NOT NULL DEFAULT 1, created_at INTEGER NOT NULL);
CREATE UNIQUE INDEX exactly_one_claude ON accounts(kind) WHERE kind = 'claude_subscription';

CREATE TABLE usage (
  dedupe_key TEXT PRIMARY KEY, at INTEGER NOT NULL,
  thread_id TEXT NOT NULL, turn_id TEXT, agent_path TEXT NOT NULL,
  account_id TEXT NOT NULL, model TEXT NOT NULL,
  uncached_input INTEGER NOT NULL, cache_read INTEGER NOT NULL, cache_write INTEGER NOT NULL,
  output INTEGER NOT NULL, reasoning INTEGER NOT NULL,
  cost_usd REAL, cost_source TEXT NOT NULL);
CREATE INDEX usage_by_account_time ON usage(account_id, at);

CREATE TABLE limits (                  -- latest per window; history lives in usage events
  account_id TEXT NOT NULL, window TEXT NOT NULL,
  utilization REAL, status TEXT NOT NULL, resets_at INTEGER,
  observed_at INTEGER NOT NULL, source TEXT NOT NULL,
  PRIMARY KEY (account_id, window));

CREATE TABLE operator_sessions (       -- console pairing; only a hash is stored
  hash TEXT PRIMARY KEY, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL);
"""


class Writer:
    """The single writer for one SQLite file. Thread + queue + group commit."""

    def __init__(self, path: Path, migrations: Sequence[str]) -> None:
        raise NotImplementedError

    async def run[T](self, work: Callable[[Connection], T]) -> T:
        """Queue `work`, await its result after the batch commits. Back-pressure, never
        drop: when the queue is full callers wait (Hermes rule)."""
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class Store:
    """Typed reads and writes over harness.db. Only harness.py constructs it; the Writer is
    private to this module (import-linted), so nothing else can open a write connection."""

    @classmethod
    async def open(cls, path: Path) -> Store:
        raise NotImplementedError

    # threads / segments / turns
    async def create_thread(self, view: ThreadView) -> None: ...
    async def thread(self, thread: ThreadId) -> ThreadView | None: ...
    async def threads(self, *, archived: bool) -> Sequence[ThreadView]: ...
    async def open_segment(self, segment: Segment) -> None: ...
    async def end_segment(self, segment: SegmentId, reason: str) -> None: ...
    async def begin_turn(self, thread: ThreadId, segment: SegmentId, input: TurnInput) -> tuple[TurnId, bool]:
        """Returns (turn id, duplicate). Duplicate when client_turn_id was seen."""
        raise NotImplementedError

    async def end_turn(self, turn: TurnId, status: str) -> None: ...

    # transcript
    async def append_items(self, thread: ThreadId, items: Sequence[dict[str, object]]) -> None:
        """Assigns seq; ignores rows whose source_key already exists (idempotent)."""
        raise NotImplementedError

    async def active_items(self, thread: ThreadId) -> Sequence[dict[str, object]]: ...
    async def archive_items(self, thread: ThreadId, upto_seq: int, summary: dict[str, object]) -> None:
        """Compaction on the OpenAI engine: mark older rows inactive, insert the summary
        item, one transaction. Never deletes (export keeps everything)."""
        raise NotImplementedError

    # approvals and rules
    async def open_approval(self, view: ApprovalView) -> None: ...
    async def resolve_approval(self, approval: ApprovalId, answer: Answer, by: str) -> ApprovalView: ...
    async def expire_pending(self, thread: ThreadId | None) -> Sequence[ApprovalId]: ...
    async def approvals(self, *, thread: ThreadId | None, pending_only: bool) -> Sequence[ApprovalView]: ...
    async def add_rule(self, rule: Rule, scope_key: str, from_approval: ApprovalId | None) -> None: ...
    async def rules(self) -> Sequence[tuple[Rule, str]]: ...

    # accounts, usage, limits
    async def accounts(self) -> Sequence[Account]: ...
    async def put_account(self, account: Account) -> None: ...
    async def record_usage(self, rows: Sequence[UsageRow]) -> None: ...
    async def record_limits(self, snapshots: Sequence[LimitSnapshot]) -> None: ...
    async def limits(self, account: AccountId | None) -> Sequence[LimitSnapshot]: ...
    async def usage_since(self, at_ms: int) -> Sequence[UsageRow]: ...
