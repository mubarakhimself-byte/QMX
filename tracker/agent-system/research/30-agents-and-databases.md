# 30: Agents and databases (what QMA v2 should store, where, and how)

Research only. Written 2026-10-12. Every claim carries a URL or a local path; **UNVERIFIED** marks anything not confirmed from a primary source during this pass.
"Local" paths are under `D:\QMX-research\sources\harnesses\` unless they say otherwise.

## Plain-words summary (read this first)

1. Serious agent runtimes keep two things apart: an **append-only log** of what happened (the truth) and **tables** derived from it for fast reads (the index). Codex, Hermes, Temporal, DBOS, Restate and Cordis all work this way.
2. **Stay on SQLite.** One operator on one Windows PC with about 40 agents is well inside what SQLite does, *if* exactly one process writes each file and writes are batched. QMX already follows this rule (FR-A98).
3. **Split by job, not by feature.** Use a few SQLite files, chosen by how fast they are written and whether they can be rebuilt: control (small, precious), agents (sessions, turns, items, journal), checkpoints (large, rebuildable), library (later).
4. **Found today: QMX's Python bundles SQLite 3.50.4.** SQLite's "WAL-reset" corruption bug is fixed only in 3.51.3 and later (backports exist, but not for 3.50.4). The bug needs two connections writing or checkpointing at once. With a single writer connection per file, it cannot happen.
5. **Never copy a live `.db` with rclone.** Snapshot with SQLite's backup API or `VACUUM INTO` first, then upload the snapshot. QMX's backup job already uses the backup API.
6. Litestream is not officially supported on Windows. Use it only on the Linux remote nodes.
7. **Move to Postgres only when** a second machine must write the same data live (the future server), or one writer process cannot keep up. The cost of moving later is small if all SQL sits behind one storage module from day one.
8. **Checkpointing alone does not stop double side effects.** A 2026 study shows LangGraph re-runs a finished, recorded step after a hard crash. QMX needs its own **effects table with idempotency keys**, plus a "claim once" step for approvals.
9. **"Model-visible means logged"** (Cordis): every model request must be rebuildable from the journal. Make this a test, not a hope.
10. The schema below covers all 13 areas asked for. Each table is marked with the file it lives in, and why.
11. **For the Library, use Git's ideas but not Git itself:** immutable content-addressed blobs, immutable versions with parent links, and named refs for branches and variants, all in SQLite. QMX's `library.db` already does half of this (`artifacts/<sha256>`, `previous_id`).
12. Dolt, lakeFS and DVC each solve a bigger or different problem (a MySQL server, a data lake, ML datasets in Git). None fits a single-PC Library today.
13. **For agents sharing state, don't lock for long and don't throw work away.** Give each object one writer through a short lease, use version numbers for small shared records, and keep both copies (a variant) when two agents edit the same artifact.
14. The research agrees: long-held locks and abort-and-retry both waste minutes of model work. Planning disjoint scopes up front, and notifying agents of conflicts so they can repair, works better.
15. The biggest risks are listed at the end: write contention you never measured, the duplicate-effects gap, journal growth, and the SQLite version.

---

## 1. What state stores serious agent runtimes use, and why

### 1.1 System by system

**LangGraph checkpointers.**
- A checkpointer "saves a snapshot of graph state at each super-step, organized into threads" ([checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)).
- It uses two tables. The checkpoints table holds one row per superstep, with `channel_values`, `channel_versions`, `versions_seen` and a parent link. The writes table holds one row per node output, as `(task_id, channel, value)` (same page).
- **Pending writes:** if one node fails in a superstep, writes from the sibling nodes that finished are kept, so they are not re-run (same page).
- **Durability modes:** `exit`, `async` and `sync` (same page).
- **Growth:** checkpoints grow without bound; LangChain's fix is pruning or a retention cron ([persistence](https://docs.langchain.com/oss/python/langgraph/persistence)). `DeltaChannel` (beta, `langgraph>=1.2`) stores deltas instead of full values ([checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)).
- **Store:** a separate "Store" holds cross-thread long-term memory ([persistence](https://docs.langchain.com/oss/python/langgraph/persistence)).
- **Backends:** `SqliteSaver` is "ideal for experimentation and local workflows"; `PostgresSaver` is for production ([checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)).
- **Subgraphs:** checkpoints are namespaced by `checkpoint_ns` (`""` for the root, `node:uuid|node:uuid` for nested subgraphs) (same page).

**Temporal.**
- The Event History is an append-only, durably persisted log. It doubles as an audit log ([events](https://docs.temporal.io/workflow-execution/event)).
- Limits: a warning at 10,240 events; termination above 51,200 events, 2,000 Updates or 10,000 Signals. **Continue-As-New** closes a run and starts a fresh one to stay under these limits (same page).
- Activities may run more than once. Temporal guarantees an Activity is *observed* as completed exactly once, but its code "may be executed multiple times". It suggests Workflow Run ID plus Activity ID as an idempotency key ([activity definition](https://docs.temporal.io/activity-definition)).

**DBOS.**
- A library inside your app, with Postgres as its only infrastructure. It records workflow inputs and every step output in a "system database" ([architecture](https://docs.dbos.dev/architecture)).
- Cost: one write per step, plus two per workflow (same page).
- On recovery, it re-runs the workflow; finished steps return their saved output; "once a step completes and is checkpointed, it is never re-executed" (same page).
- Steps must be idempotent, because the step that was running at the crash is retried (same page).
- Measured at ">40K workflows or steps per second" on one Postgres. Large outputs belong in blob storage (same page).
- The Python SDK's system database can be SQLite (the default when no URL is set), but "Postgres is recommended for production". SQLite always polls instead of using LISTEN/NOTIFY ([config](https://docs.dbos.dev/python/reference/configuration)).

**Restate.**
- Restate journals every step and replays the journal after a crash, skipping completed steps ([durable execution](https://docs.restate.dev/concepts/durable_execution)).
- Idempotency keys deduplicate requests (same page).
- **Virtual Objects** give per-key state with a single-writer guarantee: "Only one handler can modify state at a time" (same page).
- It ships as one Rust binary with an embedded key-value store (same page). The storage engine (RocksDB) is **UNVERIFIED**; the page does not name it.

**Hermes `state.db`.**
- One SQLite file in WAL mode holds: `sessions` (with token and billing columns), `messages`, `session_model_usage`, three FTS5 tables, `compression_locks`, `async_delegations`, `delivery_obligations` (a gateway outbox) and `schema_version` (Local: `hermes\pages\developer-guide__session-storage.md`).
- Lineage is kept through `parent_session_id`. Each message gets a durable `message_uid` that survives compaction and clones. Compaction archives old rows as `active=0` rather than deleting them (same file).
- Write contention handling, to avoid the "convoy effect" (same file): a 1 s SQLite timeout; application-level retry with random jitter (20-150 ms, then 250 ms-1 s) within budgets of 20 s (normal) and 60 s (transcript); `BEGIN IMMEDIATE`; a PASSIVE WAL checkpoint every 50 writes.
- Derived FTS indexes can be detached and rebuilt; canonical rows are never sacrificed. A handle that sees real corruption is quarantined and stops writing (Local: `hermes\pages\developer-guide__state-db-recovery.md`).

**Codex (codex-rs).**
- Codex runs **seven SQLite files**: `state_5`, `logs_2`, `goals_1`, `memories_1`, `memories_v2_1`, `queue_1` and `thread_history_1` (source: [sqlite.rs](https://raw.githubusercontent.com/openai/codex/main/codex-rs/state/src/sqlite.rs)).
- Each file has a recovery mode: `thread_history` is `Unavailable` (canonical, cannot be rebuilt); the other six are `BackupAndRebuild` (derivable) (same file).
- Settings: WAL, `synchronous=NORMAL`, a 5 s busy timeout, incremental auto-vacuum, pools of 5 connections (same file), and a compile-time assertion that SQLite is at least 3.51.3, "must include the WAL-reset corruption fix" ([lib.rs](https://raw.githubusercontent.com/openai/codex/main/codex-rs/state/src/lib.rs)).
- The `threads` table points at a `rollout_path` (a JSONL transcript), so the DB is an index over files ([0001_threads.sql](https://raw.githubusercontent.com/openai/codex/main/codex-rs/state/migrations/0001_threads.sql)).
- Background work uses a leased `jobs` table with `worker_id`, `ownership_token`, `lease_until`, `retry_at`, `retry_remaining` and watermarks ([0006_memories.sql](https://raw.githubusercontent.com/openai/codex/main/codex-rs/state/migrations/0006_memories.sql)).
- Sub-agents are tracked in `thread_spawn_edges(parent, child, status)` ([0021](https://raw.githubusercontent.com/openai/codex/main/codex-rs/state/migrations/0021_thread_spawn_edges.sql)).
- The migration history shows churn. Memory tables were created, then dropped from the state DB (0035), and memory moved into its own files. `agent_jobs` was added (0014) and later dropped (0042) ([migrations](https://github.com/openai/codex/tree/main/codex-rs/state/migrations)).

**OpenAI Agents SDK sessions.**
- The protocol has four methods: `get_items`, `add_items`, `pop_item`, `clear_session` ([sessions](https://openai.github.io/openai-agents-python/sessions/)).
- Backends: SQLite, async SQLite, SQLAlchemy, Redis, MongoDB, Dapr and OpenAI Conversations, plus Encrypted and Compaction wrappers (same page).
- `AdvancedSQLiteSession` adds `message_structure` (with `branch_id`, `user_turn_number`, `branch_turn_number`), `branch_reservations` and `turn_usage` (unique on `(session_id, branch_id, user_turn_number)`), with APIs such as `create_branch_from_turn` and `store_run_usage` ([advanced](https://openai.github.io/openai-agents-python/sessions/advanced_sqlite_session/)).

**Claude Agent SDK `SessionStore`.**
- Transcripts are JSONL files under `~/.claude/projects/<encoded-cwd>/`. A fork copies the history into a new session ([sessions](https://code.claude.com/docs/en/agent-sdk/sessions)).
- `SessionStore` has two required methods, `append(key, entries)` and `load(key)`. It also has optional `listSessions`, `listSessionSummaries`, `delete` and `listSubkeys` ([session-storage](https://code.claude.com/docs/en/agent-sdk/session-storage)).
- The key is `{projectKey, sessionId, subpath}`. Sub-agent transcripts use the subpath `subagents/agent-<id>` (same page).
- **It is a dual-write mirror.** The subprocess writes to local disk first, then the SDK forwards the batch to `append()` (same page).
- A failed append is retried up to 3 attempts in total. A batch that still fails is dropped and reported as a `mirror_error` message, so adapters must "deduplicate by `entry.uuid`" (same page).
- Concurrent appends for one session can race on the summary sidecar. Serialise them with a transaction, a compare-and-swap or a per-session lock (same page).
- The SDK never deletes from the store (retention is the adapter's job), and file checkpointing cannot be combined with a store (same page).

**Cordis (dsh).**
- "**Model-visible means logged.** Every model request must be reconstructable from the log." New model-visible inputs must be logged as session events (Local: `cordis\architecture.md` L124).
- The session log is append-only `SessionEvent`s. Projections fold over committed events, and durable state is added by extending `SessionEventMap`: "render and replay from the log" (same file, L59, L126, L158).
- Committed session generations are "never renamed, replaced, or deleted"; a migration writes a new file beside the old one (same file, L122).

### 1.2 What they agree on

| Pattern | Who does it | Implication for QMA v2 |
|---|---|---|
| Append-only log is the truth; tables are projections | Temporal, Restate, Cordis, Hermes (`active=0` archive), Codex (JSONL rollouts plus an index DB) | Journal first; summary columns are derived |
| One record per completed step, so recovery skips finished work | LangGraph (writes table), DBOS (step outputs), Restate (journal), Temporal (activity events) | `node_checkpoints` plus an `effects` table |
| Stable per-item IDs that survive compaction and forks | Hermes `message_uid`, Claude `entry.uuid` with UUID remap on fork | Each `item` gets a UUIDv7 that never changes |
| A history-length cap or rollover | Temporal Continue-As-New; LangGraph pruning and `DeltaChannel` | Multi-day runs need "continue as new" segments |
| Split stores by role | Codex (7 files), LangGraph (checkpointer vs Store) | A few files, chosen by write rate and whether they can be rebuilt |
| Leases for background jobs | Codex `jobs.lease_until` and `ownership_token` | Same pattern for the `jobs` and `triggers` tables |
| Idempotency is the step's or tool's job, not the engine's | Temporal, DBOS, and the paper in §7 | An effects ledger plus idempotency keys |

---

## 2. SQLite with about 40 concurrent agents on Windows

### 2.1 What SQLite actually guarantees

- **One writer at a time.** "there can only be one writer at a time". Readers and the writer do not block each other ([wal](https://www.sqlite.org/wal.html)).
- **Same host only.** All processes must be on one host; WAL "does not work over a network filesystem" (same page). Keep the DBs off OneDrive and network shares.
- **Checkpoint starvation.** If a reader is always active, checkpoints cannot complete and "the WAL file will grow without bound". The automatic checkpoint runs at 1000 pages, about 4 MB (same page).
- **`synchronous=NORMAL` in WAL mode.** It skips the sync on each commit, so the last transactions can roll back after a power loss (same page). Corruption is not listed as a consequence; **UNVERIFIED** beyond that page.
- **SQLite's own guidance:** take client/server only if writers "cannot queue up and take turns"; "a write transaction only takes milliseconds" ([whentouse](https://www.sqlite.org/whentouse.html)).
- **Python's `sqlite3` module:** `timeout` defaults to 5.0 s; `autocommit=False` is recommended but `LEGACY_TRANSACTION_CONTROL` is still the default; `Connection.backup()` "works even if the database is being accessed by other clients" ([sqlite3 docs](https://docs.python.org/3/library/sqlite3.html)).
- **`BEGIN CONCURRENT`** (optimistic page-level multi-writer) exists, but COMMIT is still serialised ([begin_concurrent](https://www.sqlite.org/src/doc/begin-concurrent/doc/begin_concurrent.md)). It lives on a separate development branch and is not in standard builds (**UNVERIFIED** from that page). Do not plan on it.

### 2.2 Found in this pass: the WAL-reset bug and QMX's SQLite version

- **The bug.** SQLite documents a corruption bug present "from 3.7.0 through 3.51.2", fixed in 3.51.3 (2026-03-13), with backports to 3.44.6 and 3.50.7 ([wal §11](https://www.sqlite.org/wal.html#walresetbug); [changes](https://www.sqlite.org/changes.html)).
- **What triggers it.** It needs "two or more database connections open on the same file, in separate threads or processes", writing or checkpointing "at the same instant" (same page).
- **Codex refuses to build against a SQLite older than 3.51.3** ([lib.rs](https://raw.githubusercontent.com/openai/codex/main/codex-rs/state/src/lib.rs)).
- **QMX's version.** On this machine, `python -c "import sqlite3; print(sqlite3.sqlite_version)"` under Python 3.14.6 prints **3.50.4**. That is before the fix, and is not the 3.50.7 backport.
- **QMX's exposure.** `qmx-control` opens short-lived connections per call, so several threads can write the same file. Examples: `library.py` L64, `service.py` L153, under `D:\QMX-worktrees\agent-system\qmx-agents\packages\qmx-control\src\qmx_control\`.
- **Fix options:** (1) make one writer connection per file the rule, which removes the precondition; (2) ship a newer SQLite through a wheel that bundles its own library (for example `apsw` or `sqlean.py`; Windows wheels for 3.14 are **UNVERIFIED**); (3) both, which is recommended.

### 2.3 Concurrency design for 40 agents

**Where writes come from.**
- About 40 OpenAI agents run in-process, in one asyncio loop.
- Claude Agent SDK sessions are child processes. Their transcript writes reach QMX only through `SessionStore.append`, which the SDK calls in the parent process ([session-storage](https://code.claude.com/docs/en/agent-sdk/session-storage)).
- So **every QMA write already funnels through the qmx-control process**. That makes "one writer per file" cheap to achieve.

**Recommended shape** (adapted from Hermes and Codex):
1. **One writer task per DB file** inside qmx-control. It owns a single connection with `autocommit=False` and takes requests from an `asyncio.Queue`.
2. **Group commit.** Drain the queue every 25-100 ms, or every N items, into one `BEGIN IMMEDIATE ... COMMIT`.
   - 40 agents produce perhaps 10-50 items a second. That becomes 10-40 transactions a second, a small load for SQLite (**UNVERIFIED** until measured; this is NFR-T11 in `26-requirements-from-today.md`).
   - Never persist token-stream deltas. Persist completed items only, as Cordis does: "commits the complete compact stream as one message" (Local: `cordis\architecture.md` L106).
3. **Readers.** Use a small pool of read-only connections (`mode=ro`); the UI SSE and the API read from it. Codex uses pools of 5 ([sqlite.rs](https://raw.githubusercontent.com/openai/codex/main/codex-rs/state/src/sqlite.rs)).
4. **Pragmas.** `journal_mode=WAL`, `busy_timeout=5000`, `foreign_keys=ON`, `auto_vacuum=INCREMENTAL` on new files (as in Codex). Use `synchronous=NORMAL` for the high-rate agents file and `FULL` for control (approvals, the usage ledger); `synchronous` is set per connection ([pragma docs](https://www.sqlite.org/pragma.html#pragma_synchronous), not re-read this pass, **UNVERIFIED**).
5. **Checkpoints and long readers.** The writer runs `wal_checkpoint(PASSIVE)` every N commits, as Hermes does every 50 (Local: `hermes\pages\developer-guide__session-storage.md`). Cap read transactions to seconds, so SSE tails never pin the WAL ([wal](https://www.sqlite.org/wal.html)).
6. **Other processes.** Remote nodes, mini-apps and scripts never open the agents or control files directly; they call the qmx-control API. Mini-apps keep their own `app.db`, which already has one writer per app (FR-A75 and FR-A98 in `27-requirements-from-audit-session.md`).
7. **When the queue backs up,** apply back-pressure to agents and slow their step rate. Never drop journal items. Hermes ends the turn with `session_persistence_failed:locked` instead of losing data (Local: `hermes\pages\developer-guide__session-storage.md`).

### 2.4 Backups: Litestream, rclone and snapshots

- **rclone on a live DB is unsafe.** A copy taken mid-transaction "might contain some old and some new content, and thus be corrupt", and separating the `-wal` file from the DB is listed among the causes of corruption ([howtocorrupt](https://www.sqlite.org/howtocorrupt.html)).
  - **Rule:** rclone only copies *snapshots* made by the backup API, `VACUUM INTO` or `sqlite3_rsync`; all three "will work even on a live database" (same page). QMX already snapshots with `source.backup(output)` (`qmx-control\src\qmx_control\backup.py` L141, in the worktree).
- **Litestream.** It takes over checkpointing by holding a long read transaction and ships WAL pages as LTX files; restore is to file boundaries only, and L0 detail expires after 5 minutes by default ([how it works](https://litestream.io/how-it-works/)).
  - "Windows binaries are provided for convenience but Windows is NOT an officially supported platform" ([releases](https://github.com/benbjohnson/litestream/releases)), even though a Windows-service guide exists ([windows guide](https://litestream.io/guides/windows/)). It also conflicts with the app's own PASSIVE checkpoints (**UNVERIFIED** in detail).
  - **Verdict:** no Litestream on the Windows PC. It is acceptable on Linux remote nodes for node-local DBs.
- **Journal segments as a second backup.** Close the journal into dated, immutable JSONL segments (`journal/2026-10-12/run-<id>.000.jsonl.zst`) and rclone them to the bucket, matching FR-A92 (`27-requirements-from-audit-session.md`). This gives point-in-time recovery for the canonical log without Litestream.

### 2.5 When to move to Postgres, and what it would cost

**Triggers for moving.** Any one of these is enough:
- **A.** A second *machine* must write the same live state, for example the planned Contabo server running workflows while the PC UI writes approvals. SQLite cannot be shared across hosts ([wal](https://www.sqlite.org/wal.html)).
- **B.** Measured writer saturation after batching, with p99 enqueue-to-commit above about 250 ms under real 40-agent load (the threshold is a proposal).
- **C.** You need many independent writer processes that "cannot queue up and take turns" ([whentouse](https://www.sqlite.org/whentouse.html)).
- **D.** You want LISTEN/NOTIFY-driven queues, as DBOS does on Postgres ([config](https://docs.dbos.dev/python/reference/configuration)).

**Embedded Postgres options on Windows.**

| Option | Facts | Fit |
|---|---|---|
| pg0 / `pg0-embedded` | "A single binary that runs PostgreSQL locally"; Windows 10/11 x86_64 supported; `pip install pg0-embedded` ([github](https://github.com/vectorize-io/pg0), [pypi](https://pypi.org/project/pg0-embedded/)) | Good dev and desktop option. It is still a server process to supervise. Upgrade path and production maturity are **UNVERIFIED** |
| PGlite | WASM Postgres for JS/TS (browser, Node, Bun) ([about](https://pglite.dev/docs/about)); "a single-connection database", with a multiplexing socket server aimed at development ([socket](https://pglite.dev/docs/pglite-socket)) | Poor fit: no Python embedding, single connection |
| Standard PostgreSQL service on Windows | The normal installer and service (**UNVERIFIED** this pass) | The production answer if A happens; the server would run it natively on Linux anyway |

**Keeping a later migration cheap.** Estimated at about 1-2 weeks if prepared; **UNVERIFIED** estimate.
- All SQL lives in one `qma_store` module behind repository functions. Agents and graphs never write SQL.
- Use portable types throughout: TEXT UUIDv7 IDs (no reliance on `rowid`), INTEGER epoch milliseconds, TEXT JSON (maps to `jsonb`), no `WITHOUT ROWID` tricks, and `ON CONFLICT DO UPDATE` (supported by both) instead of SQLite-only `INSERT OR REPLACE`.
- FTS5 is the only non-portable piece; it maps to Postgres `tsvector`. Keep search behind its own function.
- Migrations are numbered SQL files, as Codex does ([migrations](https://github.com/openai/codex/tree/main/codex-rs/state/migrations)).
- The journal is JSONL-exportable, so a move is "replay the journal into new tables" plus a bulk copy of the rest.

---

## 3. Event sourcing and append-only logs for agent runs

### 3.1 Principles, with sources

- **Event sourcing** is to "Capture all changes to an application state as a sequence of events". This gives complete rebuilds, temporal queries and replay ([Fowler](https://martinfowler.com/eaaDev/EventSourcing.html)).
- **Its classic trap:** "external systems don't know the difference between real processing and replays". The fix is a gateway that suppresses or records external calls during replay (same page). For agents, those calls are the model and the tools.
- **Model-visible means logged.** Every model request must be reconstructable from the log (Local: `cordis\architecture.md` L124).
  - QMX already has `RunJournal`, which records each run, model call and tool call (with an argument hash and a result reference), each interrupt and each approval, append-only (FR-A41 in `27-requirements-from-audit-session.md`).
  - The gap: the journal records *that* a model call happened, but not always the full *request*.
  - **Proposal:** journal a `request/header` item (model, params, tools hash) and the exact input items, or content hashes of them, per call, as Cordis does with `request/header` and `request/context` (Local: `cordis\architecture.md` L110).
  - Add a CI test that rebuilds the last N requests from the journal and compares hashes.
- **Transactional outbox.** Write the state change and the event row in *one* transaction; a relay publishes later. Consumers must be idempotent because the relay can publish twice ([microservices.io](https://microservices.io/patterns/data/transactional-outbox.html)).
  - The UI event stream already resumes with `Last-Event-ID` from a durable event store (`qmx-control\README.md`). Keep that: the SSE is a read of `events`, not a separate bus.
  - Hermes's `delivery_obligations` table is the same idea for owed replies (Local: `hermes\pages\developer-guide__session-storage.md`).

### 3.2 Exactly-once tools: what is actually possible

- **No engine gives exactly-once side effects.**
  - Temporal says the Activity "may be executed multiple times and may even partially complete more than once" ([activity](https://docs.temporal.io/activity-definition)).
  - DBOS retries the step that was in flight ([architecture](https://docs.dbos.dev/architecture)).
- **LangGraph re-runs recorded work after a crash.** It "re-executes durably recorded work after a real SIGKILL — exactly-once across interrupts, at-least-once across crashes, on one API". This held on SqliteSaver and live PostgresSaver at 1.2.9 ([arXiv:2608.03836](https://arxiv.org/abs/2608.03836)).
  - The same paper: when *k* processes resume one parked interrupt, the gated effect fires *k* times.
  - Its fix is a gate that "claims consumption in the shared store, serving one racer and refusing the rest" (same paper).
- **Idempotency keys beat every alternative.** A key on every write cut duplicates from 28% to 4%; agents "use keys when they exist" ([arXiv:2609.29095](https://arxiv.org/abs/2609.29095)).
  - "agents reported success in 90% of the episodes in which they had duplicated an effect" (same paper).
- **Stripe's model** (the reference design): the first response is saved against the key, including 500 errors; a reuse with different parameters errors; keys are pruned after at least 24 h ([stripe](https://docs.stripe.com/api/idempotent_requests)).

**Design for QMA v2: the effects ledger.** Six steps.
1. **Classify tools** in the plugin manifest as `read`, `idempotent_write`, `keyed_write` (accepts a key), `unkeyed_write` or `irreversible`.
2. **Mint the key before the call.** The key is `run_id:node_id:call_seq`. It must be stable across retries and resumes, like Temporal's run ID plus activity ID.
3. **Record intent before the call.** `INSERT INTO effects(status='intent', key, args_hash)` commits *before* the tool runs. On success, the same row is updated to `done` with a result reference, in the same transaction as the item.
4. **Resume rule:**
   - `done`: return the stored result and never re-run.
   - `intent` (unknown outcome): for `keyed_write`, re-send with the same key. For `unkeyed_write` or `irreversible`, **do not re-run**. Raise an approval ("outcome unknown, check and confirm").
   - This follows the paper's proof that "no verification-only policy is exactly-once under late commits" ([arXiv:2609.29095](https://arxiv.org/abs/2609.29095)).
5. **Approvals are consumed once.** Claim with `UPDATE approvals SET status='consumed', consumed_by=? WHERE id=? AND status='approved' RETURNING id`. Only the racer that gets a row proceeds. This is the read-path gate from [arXiv:2608.03836](https://arxiv.org/abs/2608.03836).
6. **Money path.** Broker orders must carry the broker's client-side order ID as the key. Whether cTrader Open API deduplicates on it is **UNVERIFIED**. Until verified, treat orders as `irreversible` and route them through the existing node gates.

### 3.3 Replay and multi-day runs

- **Replay means re-running from the journal with the model and tools stubbed** by recorded outputs, Fowler's gateway. Use it for debugging and for forks.
- **Live resume means continuing from the last node checkpoint**, with the effects ledger consulted.
- **Long runs.** Runs that last days need a segment rollover, Temporal's Continue-As-New ([events](https://docs.temporal.io/workflow-execution/event)).
  - Close a run segment every N items (proposal: 10,000) or every 24 h.
  - Write a compact "carry" checkpoint and start a new segment row linked by `prev_segment_id`.
  - This bounds per-segment reads and lets old segments go to cold storage.

---

## 4. Proposed QMA v2 schema

### 4.1 Which file holds what, and why

| File | Holds | Write rate | Rebuildable? | `synchronous` | Why separate |
|---|---|---|---|---|---|
| `control.db` (exists) | accounts, limits, plugins, graph definitions and versions, triggers, schedules, approvals, usage ledger, settings | low | **No**: precious | FULL | Small and precious; backed up often; it must never wait behind agent traffic |
| `agents.db` (new) | sessions, threads, turns, items, runs, jobs, node runs, effects, events, memory pointers, artifact refs, variants | high | **No**: the canonical journal | NORMAL plus segment export | The hot path, with one writer task |
| `checkpoints.db` (new) | node checkpoint blobs (state snapshots) | bursty, large | Mostly. It can be rebuilt by replay, and old ones are prunable | NORMAL | Keeps big blobs from bloating the hot file and its WAL; pruning it never touches the journal |
| `search.db` (new, optional) | FTS5 over items and memory | derived | **Yes** | OFF/NORMAL | Codex and Hermes both treat indexes as disposable. Rebuild on corruption ([sqlite.rs](https://raw.githubusercontent.com/openai/codex/main/codex-rs/state/src/sqlite.rs); Local: `hermes\pages\developer-guide__state-db-recovery.md`) |
| `memory.db` (exists) | memory records (P07) | low | No | FULL | Already separate; leave as is |
| `library.db` (exists; Library out of scope) | artifact metadata plus FTS; blobs in `artifacts/<sha256>` | low | Metadata no; blobs immutable | FULL | It is the seam (§5) |
| `runs.db` / run indexes (exist) | backtest and research run index | — | — | — | Unchanged; QMA refers to them by ID |

Notes:
- **Cross-file references** are plain TEXT IDs with no foreign keys. SQLite has no FKs across files. Integrity comes from the store module and from tests.
- **Usage ledger in control.db.** It feeds limits enforcement, which must read consistently with `limits` in one transaction.
- **Agents never get raw SQL.** They reach state only through tools, as the Library already works (`26-requirements-from-today.md` S37).
- **The UI reads through the API.** It never reads agents.db directly.

### 4.2 Tables

Conventions:
- `id TEXT PRIMARY KEY` holds a UUIDv7, so IDs are time-ordered.
- `*_at INTEGER` is epoch milliseconds.
- `*_json TEXT` holds JSON.
- Every mutable row has `version INTEGER NOT NULL DEFAULT 1` for optimistic updates (§6).

**control.db**

```sql
-- Accounts and limits (provider accounts, API keys by reference only — never the secret)
CREATE TABLE accounts (id TEXT PRIMARY KEY, provider TEXT NOT NULL, label TEXT NOT NULL,
  credential_ref TEXT NOT NULL,          -- Credential Manager label, e.g. qmx/...
  kind TEXT NOT NULL,                    -- api_key | subscription | local
  enabled INTEGER NOT NULL DEFAULT 1, created_at INTEGER NOT NULL, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE limits (id TEXT PRIMARY KEY, scope TEXT NOT NULL,   -- account|model|agent|graph|global
  scope_id TEXT, metric TEXT NOT NULL,   -- usd|input_tokens|requests|concurrent_agents
  window TEXT NOT NULL,                  -- run|day|week|month|5h_rolling
  hard_cap REAL, soft_cap REAL, action TEXT NOT NULL, -- block|ask|warn
  updated_at INTEGER NOT NULL, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE limit_snapshots (account_id TEXT NOT NULL, taken_at INTEGER NOT NULL,
  source TEXT NOT NULL, payload_json TEXT NOT NULL, PRIMARY KEY(account_id, taken_at));

-- Usage ledger: append-only, one row per model call; totals are views
CREATE TABLE usage_ledger (id TEXT PRIMARY KEY, at INTEGER NOT NULL,
  account_id TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL,
  session_id TEXT, run_id TEXT, node_run_id TEXT, agent_name TEXT, item_id TEXT,
  input_tokens INTEGER, output_tokens INTEGER, cache_read_tokens INTEGER,
  cache_write_tokens INTEGER, reasoning_tokens INTEGER,
  cost_usd REAL, cost_source TEXT NOT NULL,     -- reported|estimated
  pricing_version TEXT, request_hash TEXT);
CREATE INDEX usage_by_account_time ON usage_ledger(account_id, at);
CREATE INDEX usage_by_run ON usage_ledger(run_id);

-- Plugins (the organogram unit)
CREATE TABLE plugins (id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, current_version_id TEXT,
  enabled INTEGER NOT NULL DEFAULT 1, trust TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE plugin_versions (id TEXT PRIMARY KEY, plugin_id TEXT NOT NULL REFERENCES plugins(id),
  semver TEXT NOT NULL, manifest_sha256 TEXT NOT NULL, manifest_json TEXT NOT NULL,
  tools_json TEXT NOT NULL,              -- includes effect class per tool (§3.2)
  installed_at INTEGER NOT NULL, UNIQUE(plugin_id, semver));

-- Graph definitions and versions (immutable versions + movable refs, see §5)
CREATE TABLE graphs (id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, -- graph|loop|miniapp
  created_at INTEGER NOT NULL);
CREATE TABLE graph_versions (id TEXT PRIMARY KEY, graph_id TEXT NOT NULL REFERENCES graphs(id),
  parent_version_id TEXT, merge_parent_id TEXT,          -- git-like parents
  content_sha256 TEXT NOT NULL, definition_json TEXT NOT NULL, schema_version INTEGER NOT NULL,
  author TEXT NOT NULL,                  -- operator|agent:<name>
  message TEXT, created_at INTEGER NOT NULL);
CREATE TABLE graph_refs (graph_id TEXT NOT NULL, ref TEXT NOT NULL,   -- main|draft/<agent>|variant/<n>
  version_id TEXT NOT NULL, updated_at INTEGER NOT NULL, version INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY(graph_id, ref));

-- Triggers and schedules
CREATE TABLE triggers (id TEXT PRIMARY KEY, graph_id TEXT NOT NULL, graph_ref TEXT NOT NULL DEFAULT 'main',
  kind TEXT NOT NULL,                    -- cron|interval|event|webhook|manual
  spec_json TEXT NOT NULL, timezone TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
  next_fire_at INTEGER, last_fired_at INTEGER, last_run_id TEXT,
  lease_owner TEXT, lease_until INTEGER, version INTEGER NOT NULL DEFAULT 1);
CREATE INDEX triggers_due ON triggers(enabled, next_fire_at);
CREATE TABLE trigger_fires (trigger_id TEXT NOT NULL, fire_key TEXT NOT NULL, -- scheduled slot, dedupe
  fired_at INTEGER NOT NULL, run_id TEXT, PRIMARY KEY(trigger_id, fire_key));

-- Approvals queue
CREATE TABLE approvals (id TEXT PRIMARY KEY, created_at INTEGER NOT NULL,
  session_id TEXT, run_id TEXT, node_run_id TEXT, effect_key TEXT,
  kind TEXT NOT NULL,                    -- tool|spend|outcome_unknown|merge|plan
  request_json TEXT NOT NULL, risk TEXT NOT NULL,
  status TEXT NOT NULL,                  -- pending|approved|denied|expired|consumed
  decided_by TEXT, decided_at INTEGER, decision_json TEXT,
  consumed_by TEXT, consumed_at INTEGER, expires_at INTEGER, version INTEGER NOT NULL DEFAULT 1);
CREATE INDEX approvals_open ON approvals(status, created_at);
```

**agents.db**

```sql
-- Sessions and threads. A session is one conversational context (one SDK session);
-- a thread is the operator-visible conversation that may span sessions (compaction,
-- continue-as-new, SDK switch).
CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL, archived INTEGER NOT NULL DEFAULT 0, pinned INTEGER NOT NULL DEFAULT 0,
  origin TEXT NOT NULL,                  -- ui|trigger|agent|api
  version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE sessions (id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES threads(id),
  sdk TEXT NOT NULL,                     -- claude_agent_sdk|openai_agents
  sdk_session_id TEXT,                   -- Claude session UUID / OpenAI session_id
  agent_name TEXT NOT NULL, model TEXT, account_id TEXT,
  parent_session_id TEXT,                -- fork / compaction / continue-as-new lineage
  lineage_kind TEXT,                     -- fork|compaction|segment|subagent
  forked_from_item_id TEXT,              -- branch point
  status TEXT NOT NULL, started_at INTEGER NOT NULL, ended_at INTEGER, end_reason TEXT,
  version INTEGER NOT NULL DEFAULT 1);
CREATE INDEX sessions_thread ON sessions(thread_id, started_at);
CREATE TABLE session_edges (parent_session_id TEXT NOT NULL, child_session_id TEXT NOT NULL PRIMARY KEY,
  status TEXT NOT NULL);                 -- Codex thread_spawn_edges pattern

-- Turns and items. Item = the atomic journal unit; model-visible means logged.
CREATE TABLE turns (id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
  seq INTEGER NOT NULL, started_at INTEGER NOT NULL, ended_at INTEGER, status TEXT NOT NULL,
  request_header_json TEXT,              -- model, params, tool-set hash, system-prompt hash
  UNIQUE(session_id, seq));
CREATE TABLE items (id TEXT PRIMARY KEY,  -- stable uid, never reissued (Hermes message_uid)
  session_id TEXT NOT NULL, turn_id TEXT, seq INTEGER NOT NULL,
  kind TEXT NOT NULL,                    -- system|user|assistant|reasoning|tool_call|tool_result|
                                         -- request_header|request_context|interrupt|note|compaction
  role TEXT, content_json TEXT,          -- inline when small
  blob_sha256 TEXT,                      -- large payloads to blob store
  sdk_entry_uuid TEXT,                   -- Claude entry.uuid for dedupe on SessionStore.append
  tool_name TEXT, tool_call_id TEXT, model_visible INTEGER NOT NULL DEFAULT 1,
  active INTEGER NOT NULL DEFAULT 1,     -- compaction archives instead of deleting (Hermes)
  created_at INTEGER NOT NULL, UNIQUE(session_id, seq));
CREATE UNIQUE INDEX items_sdk_dedupe ON items(session_id, sdk_entry_uuid) WHERE sdk_entry_uuid IS NOT NULL;

-- Claude SessionStore mirror (opaque entries, kept verbatim for resume)
CREATE TABLE sdk_transcript_entries (project_key TEXT NOT NULL, session_id TEXT NOT NULL,
  subpath TEXT NOT NULL DEFAULT '', seq INTEGER NOT NULL, entry_uuid TEXT,
  entry_json TEXT NOT NULL, appended_at INTEGER NOT NULL,
  PRIMARY KEY(project_key, session_id, subpath, seq));
CREATE UNIQUE INDEX sdk_entries_uuid ON sdk_transcript_entries(project_key, session_id, subpath, entry_uuid)
  WHERE entry_uuid IS NOT NULL;
CREATE TABLE sdk_session_summaries (project_key TEXT NOT NULL, session_id TEXT NOT NULL,
  mtime INTEGER NOT NULL, data_json TEXT NOT NULL, PRIMARY KEY(project_key, session_id));

-- Jobs and runs. A run = one execution of a graph version; a job = any unit of
-- background work (run, compaction, export, remote sync) with a lease.
CREATE TABLE runs (id TEXT PRIMARY KEY, graph_id TEXT NOT NULL, graph_version_id TEXT NOT NULL,
  trigger_id TEXT, thread_id TEXT, parent_run_id TEXT, variant_of_run_id TEXT,
  status TEXT NOT NULL,                  -- queued|running|waiting|succeeded|failed|cancelled
  segment INTEGER NOT NULL DEFAULT 0, prev_segment_run_id TEXT,  -- continue-as-new
  placement TEXT NOT NULL,               -- local|remote:<node>
  inputs_json TEXT, started_at INTEGER, ended_at INTEGER, error TEXT,
  version INTEGER NOT NULL DEFAULT 1);
CREATE INDEX runs_status ON runs(status, started_at);
CREATE TABLE jobs (id TEXT PRIMARY KEY, kind TEXT NOT NULL, subject_id TEXT,
  status TEXT NOT NULL, worker_id TEXT, ownership_token TEXT, lease_until INTEGER,
  retry_at INTEGER, retries_left INTEGER NOT NULL, last_error TEXT,
  watermark INTEGER, created_at INTEGER NOT NULL, version INTEGER NOT NULL DEFAULT 1); -- Codex jobs pattern
CREATE INDEX jobs_claim ON jobs(kind, status, retry_at, lease_until);
CREATE TABLE node_runs (id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
  node_id TEXT NOT NULL, iteration INTEGER NOT NULL DEFAULT 0,   -- loops
  attempt INTEGER NOT NULL DEFAULT 1, session_id TEXT,
  status TEXT NOT NULL, started_at INTEGER, ended_at INTEGER,
  checkpoint_id TEXT,                    -- -> checkpoints.db
  output_ref TEXT, UNIQUE(run_id, node_id, iteration, attempt));

-- Effects ledger (§3.2)
CREATE TABLE effects (key TEXT PRIMARY KEY,   -- run_id:node_id:call_seq
  run_id TEXT, node_run_id TEXT, session_id TEXT, item_id TEXT,
  tool TEXT NOT NULL, effect_class TEXT NOT NULL, args_sha256 TEXT NOT NULL,
  status TEXT NOT NULL,                  -- intent|done|failed|unknown|compensated
  result_ref TEXT, external_ref TEXT,    -- e.g. broker order id
  created_at INTEGER NOT NULL, settled_at INTEGER);

-- Event stream to the UI (outbox; same transaction as the state change)
CREATE TABLE events (seq INTEGER PRIMARY KEY AUTOINCREMENT,  -- SSE Last-Event-ID
  at INTEGER NOT NULL, topic TEXT NOT NULL, subject_id TEXT NOT NULL, type TEXT NOT NULL,
  payload_json TEXT NOT NULL);
CREATE INDEX events_subject ON events(subject_id, seq);

-- Memory pointers (memory content lives in memory.db / SDK memory; this links use)
CREATE TABLE memory_refs (id TEXT PRIMARY KEY, memory_store TEXT NOT NULL,  -- qmx|claude_md|openai_session
  memory_id TEXT NOT NULL, scope TEXT NOT NULL, session_id TEXT, run_id TEXT, item_id TEXT,
  op TEXT NOT NULL,                      -- read|write|propose|retract
  at INTEGER NOT NULL);

-- Artifact references (pointers into the Library seam; never copies)
CREATE TABLE artifact_refs (id TEXT PRIMARY KEY, library_version_id TEXT,   -- library.db version
  blob_sha256 TEXT, uri TEXT,            -- bucket path for remote outputs
  role TEXT NOT NULL,                    -- input|output|evidence|attachment
  run_id TEXT, node_run_id TEXT, session_id TEXT, item_id TEXT, created_at INTEGER NOT NULL);

-- Variants and branches of work (keep-both, §6)
CREATE TABLE variants (id TEXT PRIMARY KEY, subject_kind TEXT NOT NULL,  -- session|run|graph|artifact
  subject_id TEXT NOT NULL, base_ref TEXT NOT NULL,      -- item id / version id branched from
  label TEXT, created_by TEXT NOT NULL, status TEXT NOT NULL,  -- open|chosen|discarded|merged
  chosen_at INTEGER, created_at INTEGER NOT NULL);
```

**checkpoints.db**

```sql
CREATE TABLE node_checkpoints (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, node_run_id TEXT NOT NULL,
  parent_checkpoint_id TEXT, ns TEXT NOT NULL DEFAULT '',  -- subgraph namespace (LangGraph checkpoint_ns idea)
  state_codec TEXT NOT NULL,            -- json|msgpack|zstd+json
  state_blob BLOB, state_sha256 TEXT NOT NULL, journal_seq_upto INTEGER NOT NULL,
  created_at INTEGER NOT NULL);
CREATE INDEX ckpt_run ON node_checkpoints(run_id, created_at);
CREATE TABLE pending_writes (checkpoint_id TEXT NOT NULL, task_id TEXT NOT NULL, channel TEXT NOT NULL,
  value_blob BLOB, PRIMARY KEY(checkpoint_id, task_id, channel));   -- LangGraph writes-table idea
```

Why these shapes:
- **turns and items** mirror the Claude `entry.uuid` and OpenAI item model, plus Hermes's stable `message_uid` and `active` archive flag.
- **sdk_transcript_entries** exists because `load()` must return entries "deep-equal to what was appended" ([session-storage](https://code.claude.com/docs/en/agent-sdk/session-storage)). Normalised `items` cannot guarantee that, so keep both.
- **runs, jobs and node_runs** borrow Codex leases and LangGraph pending writes.
- **variants** is the OpenAI `branch_id` idea, made generic.

---

## 5. Versioned, "git-like" data: the Library and definitions

### 5.1 Options compared

| Option | What it is | Strengths | Problems for QMX |
|---|---|---|---|
| Git plus blobs | A content-addressable store: blobs, trees and commits named by SHA-1 ([git internals](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)) | Universal; diff and review tooling; QMX already backs up to a private Git repo (`backup.py`) | Built for one writer per working tree; 40 agents writing one repo serialise on the index (**UNVERIFIED** for `index.lock` behaviour this pass); poor for big binaries; no query |
| Dolt | "a SQL database you can fork, clone, branch, merge, push and pull just like a Git repository", MySQL-compatible ([dolt](https://www.dolthub.com/docs/introduction/what-is-dolt)); prolly trees give content addressing, structural sharing and diffs that scale "with the size of the differences" ([prolly](https://www.dolthub.com/docs/architecture/storage-engine/prolly-tree)); cell-wise merge ([merge](https://www.dolthub.com/docs/concepts/dolt/git/merge)) | True table versioning | A second DB engine and server (MySQL dialect); BranchBench measured reads 5-4000x slower as branches deepen, and throughput plateauing at 4 branches in one process ([arXiv:2604.17180](https://arxiv.org/abs/2604.17180)) |
| lakeFS | Git-like repos, branches and commits over object storage; immutable commits; a KV metadata store; optimistic locking on commits ([internals](https://docs.lakefs.io/latest/understand/how/versioning-internals/), summary-level read) | Zero-copy branching of big bucket data | A server plus KV store; aimed at data lakes. Overkill for one PC; possibly relevant later for bucket datasets |
| DVC | A content-addressed cache by MD5 (`.dvc/cache`, 2-character prefix directories); `.dir` manifests for directories; only `.dvc` files go in Git ([internal files](https://doc.dvc.org/user-guide/project-structure/internal-files)) | Good for big datasets paired with Git | ML-pipeline tool; Git-centric; MD5 |
| SQLite immutable versions plus a content-addressed blob store | Rows never update; each save is a new version with a parent; blobs named by SHA-256 | Fits the stack; one file; FTS works; QMX already does it: `artifacts/<sha256>`, immutable versions via `previous_id` (`qmx-control\README.md`) | No built-in diff or merge (you write it); garbage collection of unreferenced blobs is yours |

### 5.2 Recommendation: Git's object model, stored in SQLite

The seam has four object kinds.
- **blob:** `sha256 → bytes` in `artifacts/<sha256>`, immutable, deduplicated.
- **version:** `{id, object_id, parents[], manifest_sha256, meta_json, author, created_at}`, immutable.
  - The manifest lists blob hashes, like a Git tree or a DVC `.dir`.
- **ref:** `{object_id, name, version_id, version}` and nothing else is movable. Names look like `main`, `draft/<agent>` and `variant/<n>`.
  - A ref moves only by compare-and-swap on `version`.
- **link:** typed edges between versions (`derived_from`, `evidence_for`). QMX already has `library_link` (`qmx-control\README.md`).

Interface for QMA (tools and Python):
- `put_blob`, `commit(object, parents, manifest, meta) → version_id`
- `get(version|ref)`, `move_ref(name, expected_version, new_version_id)`
- `log(object)`, `diff(a, b)` (a manifest diff, plus text diff for text blobs)
- `fork(ref → new ref)`, `search(query)`

Rules for the seam:
- **No automatic content merge.** Merging means "a new version with two parents, written by an agent or the operator".
- **Workflow, graph and mini-app definitions use the same object model** (`graph_versions` and `graph_refs` in §4.2). For human review and backup, export `main` refs nightly as files into a Git repo.
- **Exports are one-way.** Git is a mirror for review, never the source of truth, which avoids multi-writer Git.
- **Big data stays out.** Parquet and run outputs stay in buckets as `uri` and `sha256` references. Revisit lakeFS or DVC only if dataset branching becomes a need.

**The operator's "database of Git".** Yes, in the sense above: immutable versions and movable refs in SQLite. Not Git or Dolt as the engine.
- [Git4Data](https://arxiv.org/abs/2609.02106) argues the same direction: version control inside the DB, at a cost "proportional to the size of the change rather than the size of the data".

---

## 6. Multi-agent concurrency on shared state

### 6.1 Three tools, and when to use each

1. **Locks or leases** (pessimistic). Use them for *ownership* of a unit of work, never across a model call that may take minutes.
   - Codex jobs use `lease_until` plus an `ownership_token` ([0006](https://raw.githubusercontent.com/openai/codex/main/codex-rs/state/migrations/0006_memories.sql)).
   - Restate's Virtual Objects allow one writer per key ([restate](https://docs.restate.dev/concepts/durable_execution)).
   - Hermes uses a `compression_locks` table for cross-process work (Local: `hermes\pages\developer-guide__session-storage.md`).
   - **Use for:** triggers firing, job claiming, "this agent owns this draft ref".
2. **Optimistic versions** (compare-and-swap on a `version` column). Use them for *small shared records*: settings, refs, approvals, limits.
   - A conflict costs one cheap re-read.
   - lakeFS uses optimistic locking for commits ([internals](https://docs.lakefs.io/latest/understand/how/versioning-internals/)).
3. **Branch or variant** ("keep both"). Use it for *large artifacts and plans produced by long inference*.
   - Never throw away minutes of model work. Both results become versions on different refs, and a chooser (the operator, a judge agent or a rule) picks one, or writes a merge version with two parents.

### 6.2 What the research says

- **CoAgent** ([arXiv:2606.15376](https://arxiv.org/abs/2606.15376)):
  - "Locks block long inference intervals; OCC abort-and-retry discards minutes of work on every conflict."
  - Its fix: fix a serialisation order, apply writes speculatively, and notify affected agents so they repair. It stays within 5% of serial correctness at a 1.4x speedup.
- **STORM** ([arXiv:2605.20563](https://arxiv.org/abs/2605.20563)): mediating writes to the shared workspace and catching conflicts *at write time* beat one git worktree per agent with a merge afterwards (+18.7 on Commit0-Lite).
- **NP-Bench / Nerveplane** ([arXiv:2610.07261](https://arxiv.org/abs/2610.07261)):
  - Partitioning work into disjoint scopes *up front* raised clean integration from 1/9 to 9/9 scenarios and cut merge conflicts from 13 to 0.
  - "routing facts to agents does not rescue long-context accuracy".
- **CodeCRDT** ([arXiv:2510.18893](https://arxiv.org/abs/2510.18893)): CRDTs give 100% textual convergence, but still a 5-10% *semantic* conflict rate. Convergence is not correctness.
- **Verified anomaly detection** ([arXiv:2606.17182](https://arxiv.org/abs/2606.17182)): it reproduces a silent lost update in deer-flow and tool-effect reordering in LangGraph's ToolNode. Shared memory stores need isolation too.
- **MemTX** ([arXiv:2607.23929](https://arxiv.org/abs/2607.23929)): "a memory write is not a belief commit". Stage memory writes, then validate and commit them before they can drive irreversible tools.

### 6.3 Policy for QMA v2

- **Plan scopes first.** The graph engine assigns each parallel node a declared write scope (refs or objects). Overlapping scopes are serialised or turned into variants at plan time (NP-Bench).
- **Leases.** One owner per draft ref, with a lease of 60-300 s renewed per step. A lapsed lease reverts the owner to "variant".
- **Small records:** CAS on `version` with `UPDATE ... WHERE id=? AND version=?`. Retry once, then surface.
- **Artifacts:** "keep both" by default. A conflict creates `variant/<n>` and emits a `variant.created` event to the agent that lost the race, so it can re-judge (the CoAgent notify idea).
- **Memory:** only the primary agent writes, which matches P07 in `27-requirements-from-audit-session.md`. Sub-agents *propose* (`memory_refs.op='propose'`), and the primary commits.

---

## 7. Academic research, 2025-2026 (the 8 most relevant)

1. **Resume Means Resume** ([arXiv:2608.03836](https://arxiv.org/abs/2608.03836), Aug 2026).
   - Six resume properties (prefix continuation, effect exactly-once, fork determinism, checkpoint validity, consume-once, recovery determinism), model-checked in TLA+.
   - LangGraph 1.2.9 re-runs recorded work after SIGKILL. A second resume value is stored but ignored. Concurrent resumes fire the gated effect *k* times.
   - **Use:** adopt the six properties as QMA's engine test suite. Gate consume-once in the store.
2. **Where Does Exactly-Once Live?** ([arXiv:2609.29095](https://arxiv.org/abs/2609.29095), Microsoft, Sep 2026).
   - 25,930 episodes. Idempotency keys on writes cut duplicates from 28% to 4%. Harness choice barely matters.
   - Verification alone cannot be exactly-once under late commits.
   - **Use:** add an idempotency key to every write tool in the plugin contract.
3. **Atomix: Transactional Tool Use** ([arXiv:2602.14849](https://arxiv.org/abs/2602.14849), Feb 2026).
   - Records reads and effects. Buffers effects until a transaction "seals" and earlier conflicting work is exhausted. Lets irreversible effects through only at commit.
   - **Use:** treat `irreversible` tools as gated at node commit, not at the tool call.
4. **CoAgent: Concurrency Control for Multi-Agent Systems** ([arXiv:2606.15376](https://arxiv.org/abs/2606.15376), Jun 2026). Advisory concurrency control: notify and repair instead of locking or aborting (see §6).
5. **BranchBench** ([arXiv:2604.17180](https://arxiv.org/abs/2604.17180), Apr 2026).
   - Benchmarks branchable DBs (Neon, DoltgreSQL, Xata, Tiger, Postgres) on agent workloads.
   - Fast branching costs 5-4000x slower reads; fast data operations cost 25-1500x slower branching. "no current system supports the representative workloads at scale".
   - **Use:** don't buy a branchable DB for variants; use app-level refs.
6. **Supporting Our AI Overlords: Redesigning Data Systems to be Agent-First** ([arXiv:2509.00997](https://arxiv.org/abs/2509.00997), Sep 2025).
   - Agentic speculation has scale, heterogeneity, redundancy and steerability. It calls for new query interfaces and "new agentic memory stores".
   - **Use:** design the agent-facing DB tools (FR-T117) as narrow, steerable queries, not raw SQL.
7. **Experience Graphs / Trellis** ([arXiv:2606.29823](https://arxiv.org/abs/2606.29823), Jun 2026).
   - Treat agents' artifacts, tool outputs, rewards and lineage as queryable DB state, not "disposable state — JSON checkpoints and session logs".
   - At Meta, cross-session reuse reached the target speedup about 10x faster at 52% lower token cost.
   - **Use:** for QMX's research loops, lineage via `artifact_refs`, `variants` and parent links is the asset. Keep it queryable.
8. **Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers** ([arXiv:2603.07670](https://arxiv.org/abs/2603.07670), Mar 2026).
   - A survey framing memory as a write-manage-read loop, with engineering concerns: write-path filtering, contradiction handling, latency, privacy.
   - Pair it with MemTX ([arXiv:2607.23929](https://arxiv.org/abs/2607.23929)) for transactional memory commits.

Also relevant (abstracts read only): Chronos, bolt-on branching across PostgreSQL, SQLite, DuckDB and others ([arXiv:2609.14889](https://arxiv.org/abs/2609.14889)); Git4Data ([arXiv:2609.02106](https://arxiv.org/abs/2609.02106)); Cordon, semantic transactions with an effect outbox ([arXiv:2606.17573](https://arxiv.org/abs/2606.17573)); SagaLLM ([arXiv:2503.11951](https://arxiv.org/abs/2503.11951)); STORM ([arXiv:2605.20563](https://arxiv.org/abs/2605.20563)).

Most papers above are 2026 preprints, many by a single author, and are not peer reviewed (**UNVERIFIED** quality). Their *measurements of LangGraph and of idempotency keys* are the load-bearing parts. Re-check them against QMA's own tests.

---

## 8. Recommendations for QMA v2

1. **Keep SQLite, with one writer task per file, inside qmx-control.** Batch commits (25-100 ms), use `BEGIN IMMEDIATE`, run PASSIVE checkpoints every N commits, and keep a small read-only pool. Nothing outside qmx-control opens `agents.db` or `control.db`.
2. **Fix the SQLite version exposure now.** Either enforce single-writer access to every existing DB (library, control, runs), or ship SQLite 3.51.3 or later. Add a start-up assertion like Codex's ([lib.rs](https://raw.githubusercontent.com/openai/codex/main/codex-rs/state/src/lib.rs)).
3. **Use four logical files:** control (precious, FULL sync), agents (canonical journal), checkpoints (bulky, prunable) and search (derived, rebuildable). `memory.db` and `library.db` stay as they are.
4. **The journal is the truth.** Items are append-only, with stable UUIDv7 IDs. Compaction archives rows (`active=0`) and never deletes them. The UI event stream is the `events` outbox, written in the same transaction.
5. **Make "model-visible means logged" a test.** Journal the request header and context per call, then rebuild and hash-compare in CI.
6. **Effects ledger with idempotency keys** (`run:node:seq`), intent recorded before the call, and the resume rules in §3.2. Approvals are consumed by atomic compare-and-swap. Broker orders stay `irreversible` until cTrader dedupe is verified.
7. **Write the Claude `SessionStore` adapter onto `sdk_transcript_entries`.** Deduplicate on `entry.uuid`, serialise summary folds per session, and alert on `mirror_error`.
   - Keep local JSONL as a second copy for fresh sessions; the SDK writes it anyway ([session-storage](https://code.claude.com/docs/en/agent-sdk/session-storage)).
   - For OpenAI agents, implement the four-method `Session` protocol on `items`.
8. **Roll long runs over into segments** (Continue-As-New style) and prune or offload old checkpoints. Export closed journal segments as JSONL to the bucket.
9. **Library seam:** blobs, immutable versions, CAS-moved refs and links, in SQLite. Definitions use the same model. Git is an export mirror only. Not Dolt, lakeFS or DVC for now.
10. **Concurrency:** declared scopes at plan time, short leases for ownership, CAS for small records, "keep both" variants for artifacts, and primary-only memory commits.
11. **Backups:** snapshot first (backup API or `VACUUM INTO`), then rclone. No Litestream on Windows. Restore-test as FR-A99 already requires.
12. **Postgres trigger list** (§2.5): a second live writer host, measured saturation, or a need for LISTEN/NOTIFY. Keep SQL portable and behind `qma_store` so the move is a replay plus a copy. Use pg0 for desktop Postgres if it ever comes to that, and native Postgres on the server.
13. **Measure before 40 agents** (NFR-T11). Run a synthetic load of 40 writers × 2 items/s for 1 h on the operator's PC. Record p50 and p99 commit latency, WAL size and checkpoint lag. The design assumes this passes; it has not been run.

## 9. Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| SQLite 3.50.4 WAL-reset bug | Rare corruption when two connections write or checkpoint at once ([wal §11](https://www.sqlite.org/wal.html#walresetbug)) | Single writer per file; newer SQLite; integrity check at start-up and before backup |
| Unmeasured write contention at 40 agents | Turns stall or fail with `locked` (Hermes shows it happens) | One writer task, group commit, back-pressure, the load test in R13 |
| Duplicate side effects on resume or crash | Double orders, posts or spend; agents claim success anyway (90% in [arXiv:2609.29095](https://arxiv.org/abs/2609.29095)) | Effects ledger, keys, "outcome unknown" approvals, consume-once CAS |
| Journal and checkpoint growth in multi-day runs | Slow reads; WAL bloat; Temporal-style limits are there for a reason | Segments, checkpoint pruning, cold export |
| Checkpoint starvation from long SSE readers | WAL grows without bound ([wal](https://www.sqlite.org/wal.html)) | Short read transactions; poll-and-release instead of an open read |
| Claude `SessionStore` mirror loss | A dropped batch on a store-resumed run has "no surviving copy" ([session-storage](https://code.claude.com/docs/en/agent-sdk/session-storage)) | Alert on `mirror_error`; local JSONL retained for fresh runs; the adapter writes inside the single writer |
| Schema churn | Codex dropped and re-added tables repeatedly ([migrations](https://github.com/openai/codex/tree/main/codex-rs/state/migrations)) | Numbered migrations; derived tables are rebuildable; the journal is the stable contract |
| Library scope creep | "Git-like" invites building Dolt | Freeze the seam interface (§5.2); no merge engine in v2 |
| A premature Postgres move | Adds a server to supervise on Windows | Use the explicit trigger list; portable SQL |
| Preprint evidence | Several numbers come from un-reviewed 2026 preprints | Re-verify the key behaviours with QMA's own conformance tests |

## 10. Sources read in this pass

- **Web (full pages):** LangGraph persistence and checkpointers; Temporal events and activity; DBOS architecture and config; Restate; OpenAI Agents SDK sessions and advanced SQLite session; Claude Agent SDK sessions and session-storage; Codex `migrations/`, `sqlite.rs`, `lib.rs` and six migration files; SQLite wal, begin-concurrent, howtocorrupt, whentouse and changes; Python sqlite3; Litestream how-it-works and releases; pg0; PGlite about and socket; Dolt what-is, prolly and merge; lakeFS internals; DVC internal files; Git objects; Stripe idempotency; transactional outbox; Fowler event sourcing. All URLs are inline above.
- **Papers:** full-text passages read for 2608.03836, 2609.29095 and 2604.17180; abstracts only for the others cited in §6 and §7.
- **Local:** `hermes\pages\developer-guide__session-storage.md`, `hermes\pages\developer-guide__state-db-recovery.md`, `cordis\architecture.md`; in `D:\QMX-worktrees\agent-system`: `qmx-agents\packages\qmx-control\{README.md, src\qmx_control\backup.py, library.py, service.py}` and `tracker\agent-system\research\{20,26,27}-*.md`.
