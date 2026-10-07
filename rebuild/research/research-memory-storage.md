# QMX research: pluggable agent memory + per-mini-app storage

Date: 2026-10-07. Research input only. Nothing here is ratified.
Method: primary docs, fetched today. The Hermes docs were read from their own
`llms-full.txt` dump (5.5 MB, every page), searched for every memory, profile,
session, compaction, delegation, skills and gateway page.

QMX context already ratified, which the recommendations below respect:
- DEC-0117: Parquet / DuckDB / SQLite / JSONL behind QMF-owned contracts, no database server.
- DEC-0118 / DEC-0198: nightly, encrypted, versioned off-machine backup to an object-storage bucket, using rclone v1.75.0.
- AD-6 / DEC-0334: the daemon's SQLite journal uses one connection as the sole writer, and every checkpoint runs on that connection.
- 2026-10-04: agents run on LangChain/LangGraph.
(Sources: `docs/architecture/stack.md`, `docs/components/qma-daemon.md`.)

---

## A. Hermes Agent: architecture, memory and profiles

Sources:
- Index: https://hermes-agent.nousresearch.com/docs/llms.txt
- Full dump: https://hermes-agent.nousresearch.com/docs/llms-full.txt
- Memory: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- Providers: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers
- Provider plugin guide: https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin
- Profiles: https://hermes-agent.nousresearch.com/docs/user-guide/profiles
- Architecture: https://hermes-agent.nousresearch.com/docs/developer-guide/architecture
- Compression: https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching
- Session storage: https://hermes-agent.nousresearch.com/docs/developer-guide/session-storage
- Delegation: https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation

### A1. System map (short)
- Entry points: CLI, gateway (messaging on 20+ platforms), ACP (editor integration), API server and batch runner. All of them drive one `AIAgent` loop.
- `AIAgent` contains the prompt builder, provider resolution, tool dispatch (70+ tools in about 28 toolsets), a compression engine and prompt caching.
- Session storage is SQLite with FTS5 full-text search (`state.db`). Sessions keep parent/child lineage across compressions.
- Hermes has two single-select "provider plugin" kinds, both chosen in config:
  - memory provider (`memory.provider`)
  - context engine (`context.engine`), which replaces the built-in ContextCompressor
- Code locations:
  - `agent/memory_provider.py`: the ABC
  - `agent/memory_manager.py`: orchestration
  - `plugins/memory/<name>/`: bundled providers
  - `agent/context_engine.py`: context-engine ABC

### A2. Built-in memory (always on, independent of any provider)
- Two files in `$HERMES_HOME/memories/`:
  - `MEMORY.md`: agent notes, 2,200 characters (about 800 tokens)
  - `USER.md`: user profile, 1,375 characters (about 500 tokens)
- **Frozen snapshot.** Both files are injected into the system prompt once at session start and never change mid-session, which keeps the prefix cache intact. Writes reach disk immediately but show up in the prompt only from the next session.
- `memory` tool actions are add, replace and remove. replace/remove locate an entry by unique substring (`old_text`). There is no read action, because memory is already in the prompt.
- Hard character limits, no auto-compaction. An overflow returns an error with `current_entries`, and the agent must consolidate in one `operations` batch. Exact duplicates are rejected.
- Writes are security-scanned for prompt injection, exfiltration patterns and invisible Unicode.
- `memory.write_approval: true` stages writes for approval (`/memory pending|approve|reject`). Staged replace/remove operations pin the exact target entry.
- **Background review.** After a turn, a forked review may write memories or skills. Notes:
  - It can run on a cheaper model (`auxiliary.background_review`), which then sees a digest instead of the full transcript.
  - It is cost-capped by `max_input_tokens`.
  - On a local GPU it is deferred until the machine is idle.
- `session_search` runs FTS5 over every past session in `state.db`, with no LLM call. Hermes splits recall into "memory = always in prompt" and "search = on demand".
- Memory pays off at session boundaries. The docs tell users to run `/new` at natural breaks, because a messaging chat is one continuous session.
- Skills are procedural memory: `SKILL.md` documents the agent creates and patches, loaded by progressive disclosure, with the same write_approval gate.

### A3. MemoryProvider plugin interface (exact)
Discovery (earliest source wins; the reverse of the general plugin order, so a working tree cannot shadow a shipped provider):
1. Bundled `plugins/memory/<name>/` (closed to new providers)
2. User `$HERMES_HOME/plugins/<name>/` (per profile)
3. Project `./.hermes/plugins/<name>/` (opt-in env var)
4. Package entry point `hermes_agent.memory_providers`

Discovery only enumerates. Nothing is imported until `memory.provider` names it.

Shape: subclass `agent.memory_provider.MemoryProvider` and register it with `register(ctx): ctx.register_memory_provider(P())`. Optional extras:
- `ctx.register_skill(...)`, namespaced `provider:skill` and loaded only while the provider is active
- `cli.py` defining `register_cli(subparser)`, which adds `hermes <provider> ...` commands (shown only while active)
- `config_schema.py` for the dashboard panel
- `plugin.yaml` listing the hooks the provider implements

| Method | When | Required |
|---|---|---|
| `name` (property) | always | yes |
| `is_available()` | before activation; NO network calls | yes |
| `initialize(session_id, **kwargs)` | agent startup | yes |
| `get_tool_schemas()` | after init; injects the provider's tools | yes |
| `handle_tool_call(tool_name, args, **kw)` | the agent calls a provider tool | yes if the provider has tools |
| `get_config_schema()` | `hermes memory setup` wizard fields | yes |
| `save_config(values, hermes_home)` | writes non-secret config | yes, unless configured by env vars only |
| `post_setup(hermes_home, config)`, `get_status_config()` | OAuth or first sync; `memory status` | optional |
| `system_prompt_block()` | system prompt assembly (static) | optional |
| `prefetch(query, *, session_id)` | before each API call; returns recalled context | optional |
| `queue_prefetch(query, *, session_id)` | after each turn; pre-warms the next turn | optional |
| `sync_turn(user, assistant, *, session_id, messages=None)` | after each turn; MUST be non-blocking | optional |
| `on_session_end(messages)` | explicit boundary (`/new`, `/reset`, `/resume`) | optional |
| `on_pre_compress(messages)` | before lossy compaction; save insights | optional |
| `on_memory_write(action, target, content, metadata)` | mirrors built-in MEMORY/USER writes | optional |
| `shutdown()` | process exit | optional |

Init kwargs (tolerate any that are missing):
- `hermes_home` (the profile's storage root; the only legal place to put data)
- `platform`, `session_title`, `session_title_source`, `cwd`
- `gateway_session_key`, `user_id`, `user_name`, `chat_id`
- `agent_identity` (profile name)
- `agent_context`: `primary`, `cron` or `subagent`. Providers are told to skip automatic writes for anything other than `primary`.

Contracts worth copying:
- **Threading.** `sync_turn` and prefetch work go to `spawn_context_thread`, never a bare thread. The profile home and secret scope live in contextvars, so a plain thread would write into the default profile.
- **Oversized prefetch.** Results over 10,000 characters spill to a file. The prompt gets a head/tail preview plus the file path.
- **Pre-compress checkpoint API v2** (opt-in): `pre_compress_checkpoint_api_version = 2` and `on_pre_compress(messages, *, require_checkpoint)`.
  - When `compression.checkpoint_required: true`, compaction fails closed unless the provider durably archived the transcript first.
  - Writes must be idempotent: content-keyed upserts.
  - v2 providers receive user/assistant text only; tool output and prior summaries are filtered out.
- **Single provider rule.** Exactly ONE external provider may be active, and it runs alongside the built-in files, never replacing them. The manager rejects a second one, which avoids tool-schema bloat and conflicting backends.
- **Turn-off switch.** Setting both `memory_enabled` and `user_profile_enabled` to false removes the built-in tool and leaves only the provider.
- **Eviction.** TTL/LRU/memory-pressure eviction commits the cached transcript to the provider before releasing the agent. Idle time never finalizes a session.

What an active provider does each turn: injects its system-prompt block → prefetches before the turn → syncs after the turn → extracts on session end → mirrors built-in writes → exposes its tools.

### A4. Providers that ship
The Hermes docs contradict themselves on what is bundled: the memory page says 3, the providers page says 5. Reconciled:

| Provider | Where | Storage | Tools | Distinctive |
|---|---|---|---|---|
| Holographic | bundled (leaves core 2026-10-15) | local SQLite with FTS5 | `fact_store` (9 actions), `fact_feedback` | HRR algebra; trust scores (+0.05 helpful / −0.10 unhelpful); contradiction detection |
| RetainDB | bundled (leaves 2026-10-15) | cloud, $20/mo | 10 | hybrid vector+BM25+rerank; delta compression |
| ByteRover | bundled (leaves 2026-10-15) | local or cloud, needs the `brv` CLI | 3 | knowledge tree; extraction before compression |
| Honcho (Plastic Labs) | plugin catalog | cloud or self-hosted | 5 (profile, search, context, reasoning, conclude) | peers/workspace model; dialectic LLM reasoning; contextCadence / dialecticCadence / dialecticDepth knobs; sessionStrategy per-directory, per-repo, per-session or global |
| Mem0 | catalog | Platform, self-hosted server, or OSS in-process (qdrant/pgvector) | 4 | server-side LLM fact extraction, dedup |
| Hindsight (vectorize-io) | catalog | cloud, embedded Postgres, or external | 3 (retain, recall, reflect) | knowledge graph; `reflect` synthesis; hybrid / context / tools modes |
| Supermemory | catalog | cloud or self-hosted | 4 | context fencing (keeps recalled text out of captures); `{identity}` container tags; multi-container |
| OpenViking (Volcengine) | catalog | self-hosted, AGPL | 6 | `viking://` filesystem hierarchy; tiered L0/L1/L2 loading |
| Memori | external installer | cloud | 5 | structured recall |

Trend: every provider is moving out of core into its maintainer's repo. As of 2026-10-15 nothing ships in-tree, and the interface is the product.

Recurring provider knobs, worth mirroring:
- recall mode: `hybrid` (inject + tools), `context` (inject only) or `tools` (tools only)
- write frequency: async, per turn, per session, or every N turns
- token budget for injected context

### A5. Profiles
- A profile is a separate Hermes home directory (`~/.hermes/profiles/<name>/`; `%LOCALAPPDATA%/hermes` on Windows). Each one has its own:
  - `config.yaml`, `.env`, `SOUL.md`
  - memories, sessions (`state.db`), skills
  - cron, logs, gateway state
- Each profile becomes a command alias (`coder chat`). It can also be selected with `-p <name>`, or made the sticky default with `hermes profile use`.
- Terms:
  - Profile = persistent home (configuration + data).
  - Agent = the running process.
  - Bot = a profile shown in the Bot Mode roster.
  - Subagent = a child with a fresh conversation, NOT a profile.
- Rule: never point two agent processes at one profile, because their memory writes compound each other.
- Clone variants:
  - `--clone`: config, `.env`, SOUL, skills and MEMORY/USER (memory counts as identity)
  - `--clone-all`: everything except session history
  - Messaging-channel tokens are never cloned without `--clone-channels`.
- Memory isolation per profile:
  - local providers use `$HERMES_HOME` paths
  - cloud providers derive per-profile names (Honcho: one AI peer per profile in a shared workspace with one shared user peer; Supermemory: `{identity}`)
- A profile is NOT a sandbox: filesystem access is unchanged. The workspace is set separately (`terminal.cwd`).
- Kanban "tenant" = a soft namespace within a board (workspace path plus a memory key prefix). The board is the hard isolation boundary.

### A6. Adjacent mechanics that touch memory
- Compaction runs in two layers:
  - gateway session hygiene at 85% of context
  - in-loop ContextCompressor at 50%
  - Either layer calls `on_pre_compress` first.
- Compaction archives old rows as `active=0`. Lineage is kept, nothing is deleted.
- Micro-compaction exists but is off by default. It has no checkpoint hook, so it is forced off when checkpoints are required.
- Subagents (`delegate_task`) start with zero parent history, plus the project context files.
  - Leaf subagents cannot call `memory`, `delegate_task`, `send_message` or `cronjob`.
  - The provider sees `agent_context=subagent` and should not auto-write.
  - Only the child's summary returns to the parent.
- Cron runs a fresh AIAgent with no history and `agent_context=cron`.

### A7. What QMX should copy
1. One built-in, always-on, bounded memory plus at most one external provider, with the provider picked in config. Do NOT allow N providers at once.
2. A frozen snapshot at session start (prefix cache) and recall on demand through tools and search.
3. A hook set: `system_block` / `prefetch` / `on_turn_end` (non-blocking) / `on_pre_compress` / `on_scope_end` / `tools`.
4. Identity context passed in, not looked up globally. Automatic writes only from primary agents.
5. A write-approval gate and security scan on anything that re-enters a prompt.
6. A profile = an isolated home. That matches QMX's "every mini app has its own DB" ruling.

---

## B. Recommended QMX MemoryProvider interface

### B1. LangGraph / LangMem primitives (verified)
Sources:
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/stores
- https://docs.langchain.com/oss/python/integrations/long-term-memory/index
- https://langchain-ai.github.io/langmem/concepts/conceptual_guide/
- BaseStore source: https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint/langgraph/store/base/__init__.py
- Agent middleware: https://docs.langchain.com/oss/python/langchain/middleware/custom

Points:
- **Checkpointer** = short-term memory scoped to one thread (one `thread_id`). **Store** = long-term memory across threads.
- `BaseStore` is abstract only in `batch`/`abatch`. The convenience methods are built on top: `put(ns, key, value, index=None, *, ttl=)`, `get`, `delete`, `search(ns_prefix, *, query=None, filter=None, limit=10, offset=0, refresh_ttl=)`, `list_namespaces(prefix, suffix, max_depth, ...)`.
- `Item` fields: namespace (a tuple), key, value (a JSON dict), created_at, updated_at. A `SearchItem` adds `score`.
- Namespace = a tuple of strings, searched by PREFIX: `("alice",)` also matches `("alice","memories")`. Results past `limit` are truncated with no signal. Ordering depends on the backend.
- Semantic search is enabled with `index={"embed":..., "dims":..., "fields":[...]}`. Embedding can be switched off per item with `index=False`. TTL is supported when `supports_ttl` is set.
- Backends:
  - InMemory
  - Postgres (`langgraph-checkpoint-postgres`)
  - Redis, MongoDB, Upstash, DynamoDB, Cosmos, Firestore, SingleStore
  - **SqliteStore**, in `langgraph-checkpoint-sqlite` (v3.1.1). Missing from the integrations page but present in source: `langgraph/store/sqlite/{base,aio}.py`, using `sqlite-vec` for vectors, with TTL.
- LangMem (v0.0.30, still 0.0.x):
  - storage-agnostic memory managers (`create_memory_manager`): extract, update, consolidate
  - store-bound pieces: `create_memory_store_manager`, `create_manage_memory_tool`, `create_search_memory_tool`
  - namespace templates such as `("acme","{user_id}","app")`, filled from `configurable`
  - memory types: semantic (collection or profile), episodic, procedural (prompt optimizer)
  - formation: hot path (tools) or background (reflection)
- LangChain v1 agent middleware hooks: `before_agent`, `before_model`, `after_model`, `after_agent`, `wrap_model_call`, `wrap_tool_call`. There is also a built-in `SummarizationMiddleware`.

### B2. Mapping Hermes → LangGraph
| Hermes | LangGraph/LangChain equivalent |
|---|---|
| profile home `$HERMES_HOME` | namespace root `("qmx", <profile>)` + the app's own store file |
| `initialize(session_id, **ctx)` | `MemoryContext` built from `Runtime.context` / `configurable` |
| `system_prompt_block` + frozen snapshot | `before_agent` middleware (once per invocation) |
| `prefetch` | `before_model` middleware or a graph node, using `store.asearch(query=...)` |
| `sync_turn` (non-blocking) | `after_agent` middleware that queues a background task (LangMem ReflectionExecutor-style) |
| `on_pre_compress` | wrap `SummarizationMiddleware`: call the provider before the summary call |
| `on_session_end` | explicit end-of-thread API call (new thread_id / session close) |
| `get_tool_schemas` / `handle_tool_call` | `tools() -> list[BaseTool]` (LangMem manage/search tools for the default provider) |
| `agent_context` primary/subagent/cron | `MemoryContext.role`; automatic writes only when primary |
| one external provider + built-in | `MemoryManager(builtin, external: MemoryProvider \| None)` |

### B3. Scopes → namespaces
QMX scopes, from narrowest to widest. Each maps to a namespace prefix:
```
GLOBAL   ("qmx", profile, "global", kind)                              # copilot-wide: operator prefs, durable lessons
SESSION  ("qmx", profile, "session", session_id, kind)                 # one copilot session (= LangGraph thread)
WORKFLOW ("qmx", profile, "wf", workflow_id, kind)                     # one workflow run (multi-task)
TASK     ("qmx", profile, "wf", workflow_id or "_", "task", task_id, kind)
```
- `kind` ∈ {"facts", "episodes", "profile", "notes"} (the LangMem memory types).
- TASK nests under WORKFLOW on purpose: a prefix search on a workflow sees its tasks. To read the workflow level alone, filter on `item.namespace` length.
- A mini app's agent uses `profile = "app:<app_id>"`, so its memory never mixes with the copilot's. That is the Hermes profile rule.
- Promotion only moves upward: TASK → WORKFLOW → (SESSION | GLOBAL). It is gated by `write_approval` for GLOBAL.
- Defaults:
  - Task and workflow scopes get a TTL (for example 7 days / 30 days) through the store TTL.
  - Session and global memories are permanent.

### B4. Python signatures (minimal)
```python
# qma/memory/types.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, Mapping, Protocol, Sequence, runtime_checkable

class Scope(StrEnum):
    TASK = "task"; WORKFLOW = "workflow"; SESSION = "session"; GLOBAL = "global"

Role = Literal["primary", "subagent", "scheduled", "headless"]

@dataclass(frozen=True, slots=True)
class MemoryContext:            # passed in; never read from globals (Hermes contextvar lesson)
    profile: str                # "copilot" or "app:<app_id>"
    node: str                   # "laptop", "sgp-1", "nyc-1"
    role: Role = "primary"      # automatic writes only when primary
    session_id: str | None = None   # == LangGraph thread_id for copilot sessions
    workflow_id: str | None = None
    task_id: str | None = None

@dataclass(slots=True)
class MemoryRecord:
    content: str                                  # text that may enter a prompt
    kind: Literal["facts", "episodes", "profile", "notes"] = "facts"
    data: dict[str, Any] = field(default_factory=dict)   # structured payload (JSON only)
    tags: tuple[str, ...] = ()
    source: str = ""                              # provenance: run id, tool, operator
    id: str | None = None                         # provider-assigned if None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    score: float | None = None                    # set by semantic search

@dataclass(frozen=True, slots=True)
class ConfigField:              # drives a UI-editable settings form (operator rule: configurable = UI-editable)
    key: str; description: str; secret: bool = False; required: bool = False
    default: Any = None; choices: tuple[str, ...] = (); env_var: str | None = None

@runtime_checkable
class MemoryProvider(Protocol):
    name: str
    capabilities: frozenset[str]   # {"semantic", "ttl", "extraction", "graph", "reasoning", "checkpoint"}

    # lifecycle
    def is_available(self) -> bool: ...                       # no network calls
    async def open(self, ctx: MemoryContext, config: Mapping[str, Any]) -> None: ...
    async def close(self) -> None: ...

    # core CRUD -- maps 1:1 onto BaseStore
    async def put(self, scope: Scope, record: MemoryRecord, *, ttl_minutes: float | None = None) -> str: ...
    async def get(self, scope: Scope, record_id: str) -> MemoryRecord | None: ...
    async def delete(self, scope: Scope, record_id: str) -> None: ...
    async def search(self, scopes: Sequence[Scope], query: str | None = None, *,
                     kinds: Sequence[str] | None = None, filter: Mapping[str, Any] | None = None,
                     limit: int = 10) -> list[MemoryRecord]: ...

    # hooks (Hermes parity). Base class gives no-op defaults.
    def system_block(self) -> str | None: ...                 # frozen at session start
    async def prefetch(self, query: str, scopes: Sequence[Scope]) -> str | None: ...
    def on_turn_end(self, user: str, assistant: str, messages: Sequence[Mapping] | None = None) -> None: ...
        # MUST return immediately; schedule work on the provider's own executor
    async def on_pre_compress(self, messages: Sequence[Mapping], *, require_checkpoint: bool = False) -> str | None: ...
        # if require_checkpoint: raise on failure (fail-closed), writes idempotent by content hash
    async def on_scope_end(self, scope: Scope, messages: Sequence[Mapping] | None = None) -> None: ...
        # task/workflow/session closed -> extraction + upward promotion

    # surface
    def tools(self) -> list["BaseTool"]: ...                  # langchain_core.tools.BaseTool
    def config_schema(self) -> list[ConfigField]: ...

class MemoryManager:
    """Built-in bounded memory + at most ONE external provider (Hermes single-provider rule)."""
    def __init__(self, builtin: MemoryProvider, external: MemoryProvider | None = None): ...
    def middleware(self) -> list["AgentMiddleware"]: ...      # before_agent / before_model / after_agent / summarization wrap
    def tools(self) -> list["BaseTool"]: ...                  # builtin tools + external tools (prefixed by provider name)
```
Provider registry: Python entry points in the group `qmx.memory_providers`, plus local `plugins/memory/<name>/`. Earliest source wins, and nothing is imported until config names the provider (both Hermes rules). The selection lives in `config.memory.provider`, which is editable in the UI.

### B5. Default provider and adapters
- **Default `builtin` = `StoreMemoryProvider(store: BaseStore)`**, backed by `SqliteStore` from `langgraph-checkpoint-sqlite`. Each profile gets its own file:
  - copilot: `<qmx_home>/copilot/memory.db`
  - each app: `<app_home>/memory.db`
  - Never the daemon journal file, which keeps AD-6's sole-writer journal untouched.
- Semantic search starts OFF and is turned on only once an embedder is chosen (any provider). Plain FTS/prefix recall plus a bounded "pinned" profile document (a Hermes-style MEMORY/USER equivalent, about 2k characters, frozen per session) covers day 1.
- Background extraction: LangMem `create_memory_manager` runs in `on_scope_end`/`on_turn_end` workers. Because LangMem is still 0.0.x, keep it behind the provider so swapping it costs nothing.
- External adapters, later and one at a time. Each wraps a vendor Python SDK and maps CRUD + hooks:
  - Mem0 (OSS mode = local, no cloud)
  - Honcho (self-hosted or cloud; best fit for "global copilot" user modeling)
  - Hindsight (embedded Postgres; graph + `reflect`)
- On a remote trading node: the same SqliteStore file inside the app's volume. Node memory never syncs implicitly back to the laptop. Export goes through the app's data-out API.

### B6. Rules (to carry into docs)
1. Automatic writes only when `role == "primary"`. Subagents, scheduled runs and headless runs write through explicit tools only, or not at all.
2. Anything that re-enters a prompt is length-bounded and passes an injection scan (Hermes A2).
3. GLOBAL writes go through `write_approval` (operator default on). TASK/WORKFLOW writes are free.
4. Prefetch output over N characters spills to a file reference (Hermes 10k rule).
5. A provider stores data only under the path in `MemoryContext`. One process per profile store.

---

## C. Per-mini-app database: option matrix

Sources:
- Litestream: https://litestream.io/reference/config/, https://litestream.io/tips/, https://litestream.io/guides/windows/, https://github.com/benbjohnson/litestream/releases
- LiteFS: https://github.com/superfly/litefs
- Turso: https://docs.turso.tech/features/embedded-replicas/introduction, https://turso.tech/pricing, https://supabase.com/blog/supabase-is-acquiring-turso
- DuckDB: https://duckdb.org/docs/stable/connect/concurrency.html, https://ducklake.select/
- Postgres: https://www.postgresql.org/docs/current/ddl-schemas.html

Facts that drive the matrix:
- **Litestream v0.5.x** is a separate process that streams the WAL to S3, GCS, Azure Blob, SFTP, NATS or file targets.
  - **Directory replication** (`dbs: - dir:, pattern: "*.db", recursive: true, watch: true`) picks up new databases within seconds and namespaces replicas by relative path. That is a natural fit for "one DB per app".
  - Snapshots default to 24h interval / 24h retention.
  - There are Windows binaries and a Windows-service guide, but the release notes say Windows is "NOT an officially supported platform".
  - **Litestream owns checkpointing.** It holds a read lock and runs its own checkpoints, and recommends `busy_timeout=5000` and `wal_autocheckpoint=0`. That is a second checkpointer, which AD-6/DEC-0334 says triggers the SQLite 3.51.3 (or 3.50.7) floor. Never point it at the daemon journal without that floor.
- **LiteFS** is FUSE-based (Linux only), still marked beta, and its last release was 2025-04. Not for QMX.
- **Turso/libSQL embedded replicas**: reads come from a local file. Writes go to the cloud primary unless `offline` mode is set. Turso now recommends the newer "Turso Sync" (push/pull CDC).
  - Pricing: Free = 100 DBs / 5 GB; Developer = $4.99/mo for unlimited DBs.
  - Supabase announced it is acquiring Turso (2026-10-02). The roadmap is uncertain.
- **DuckDB**: only one process may open a file read-write; many readers are allowed in read-only mode. Multi-process writes need the Quack protocol (beta; maturity expected in v2.0).
  - Querying Parquet on S3 is first-class.
  - DuckLake v1.0: Parquet on object storage, with the catalog in SQLite/Postgres/DuckDB, plus snapshots and time travel.
- **Postgres schemas**: one server, schema per app, `pg_dump -n` per app. It needs a running server, which DEC-0117 forbids.

| Option | $ cost | Ops burden | Windows | Backup → S3 | Analytics fit | Multi-node fit | Python fit |
|---|---|---|---|---|---|---|---|
| SQLite per app + nightly snapshot (`VACUUM INTO` / backup API) + rclone | ≈ $0 + bucket pennies | lowest; matches DEC-0118/0198 | native | yes, RPO 24h (or every N min if scheduled more often) | OLTP only; DuckDB can ATTACH it read-only | each node holds its apps' files; push-only to bucket | stdlib `sqlite3` |
| SQLite per app + Litestream (`dir` watch) | ≈ $0 + bucket | low: one sidecar per machine, owns checkpoints | binaries only, unsupported | continuous, RPO about 1s; point-in-time restore | same as above | best on Linux nodes; restore-to-new-node is one command | no code change (separate process) |
| SQLite + LiteFS | $0 | medium; FUSE | no | via LTX/Litestream | same | primary/replica cluster | transparent |
| libSQL / Turso embedded replica | free tier → $4.99/mo | low, but a cloud dependency | SDK yes (`libsql` Python) | Turso cloud holds the primary; PITR 1–10 days by plan | same as SQLite | strongest built-in multi-node read | OK; SDK churn (libsql → Turso Sync) |
| DuckDB file per app | $0 | low | native | snapshot file / `EXPORT DATABASE` to Parquet → rclone | excellent | single writer process; nodes write locally, ship Parquet | excellent |
| DuckDB + Parquet/DuckLake on S3 | bucket only | medium (catalog + compaction) | native | data already lives in S3 | excellent; shared read across nodes | good for append-only research data | excellent |
| Postgres schema per app | $0 self-hosted / $$ managed | highest: a server, upgrades, WAL archiving | native installer | `pg_dump -n` or WAL-G/pgBackRest (Linux-centric) | fair | one central server = SPOF for remote nodes | psycopg |
| Convex | see D | medium | binary exists | its own export/backup | poor | one deployment per app | client only |

### C1. Recommendation (one stack)
**Per app: one SQLite file for app state + optional DuckDB/Parquet for bulk analytics. Backup = snapshot + rclone (already ratified). Litestream only on Linux nodes. Cache = in-process.**

App volume layout (the "volume" in section E):
```
<qmx_home>/apps/<app_id>/
  app.db          # SQLite WAL: app state, config, runs, outbox (the app's "own small DB")
  memory.db       # SqliteStore for that app's agent memory (B5), only if agent-driven
  data/*.parquet  # bulk series/results (DEC-0117 columnar), DuckDB queries these in-process
  blobs/          # files in/out
  backup.json     # last snapshot id, checksum, restore-test result
```
1. **Transactional state.** SQLite (stdlib), WAL mode, `busy_timeout=5000`, one writer process per app, which is the app runtime itself.
2. **Analytics.** DuckDB in-process, opened when needed: `ATTACH 'app.db' (TYPE sqlite, READ_ONLY)` plus `read_parquet('data/*.parquet')`. Keep no persistent `.duckdb` file unless an app proves it needs one. Any such file is a rebuildable view (DEC-0117 already says this).
3. **Backup, everywhere including Windows.** On a schedule (nightly per DEC-0118; can run hourly), take a consistent snapshot of each `*.db` with `VACUUM INTO` or the sqlite3 backup API, then rclone it to `s3://<bucket>/<node>/<app_id>/<ts>/`, encrypted and versioned. Parquet files are immutable, so rclone sync covers them. The restore test is part of the job. This needs no new tool.
4. **Continuous backup, on demand.** On Linux trading nodes, for apps whose RPO must be seconds (order/fill journals), add Litestream with `dir: <qmx_home>/apps`, `pattern: "app.db"`, `recursive: true`, `watch: true`. Apps on that node then follow Litestream's checkpoint rules (`wal_autocheckpoint=0`, SQLite floor 3.51.3). Do not run it on the Windows laptop.
5. **Data in/out.** Each app exposes `export()` / `import()` as JSONL or Parquet plus a manifest. Data crosses machines as files through the bucket, never as live remote database connections.
6. **Cache layers:**
   - L1: in-process `cachetools.TTLCache` (v7.2.1, maintained) or `functools.lru_cache` for pure functions. Per process, no ops.
   - L2: the app's own SQLite or Parquet, used as a materialized cache (memoized query results and fetched market data with `fetched_at`). It is durable, backed up for free and inspectable.
   - Skip: Redis/Valkey on day 1. There is no official native Windows build, and it adds a server. Skip `diskcache` as well: its last release was 2023-08, so it is effectively unmaintained.
   - Add Valkey only on a Linux node that needs cross-process pub/sub or a shared hot cache between several app processes.

### C2. When to deviate
- An app needs multi-node reads of one live DB (for example a laptop dashboard over a Singapore node's state): use the libSQL/Turso Sync pattern, or simply poll the node's API. Prefer the API.
- Research data is large and append-only and must be shared across nodes: DuckLake (catalog in SQLite) plus Parquet on S3.
- Many concurrent writer processes per app, or relational fan-in across apps (for example a fleet-wide P&L): Postgres, as a central reporting store fed by exports and not as the apps' primary store. This breaks DEC-0117 and would need a ruling.
- An app's DB file grows past about 10–50 GB or its writes are heavy: move series into Parquet partitions and keep SQLite for metadata only.

---

## D. Convex verdict for QMX

Sources:
- https://www.convex.dev/
- https://docs.convex.dev/llms.txt
- https://docs.convex.dev/self-hosting.md
- https://github.com/get-convex/convex-backend/blob/main/self-hosted/README.md
- https://docs.convex.dev/client/python.md
- https://docs.convex.dev/quickstart/python.md
- https://docs.convex.dev/components/overview.md
- https://docs.convex.dev/production/state/limits.md
- https://www.convex.dev/pricing

What it is:
- A reactive document database plus server functions (queries, mutations, actions) plus a sync engine that live-updates subscribed clients.
- Built in: cron, scheduling, file storage, text and vector search, an Agent component.
- **Components** are mini self-contained backends with their own tables and isolated execution. They cannot read app tables unless those are passed in.

Facts that decide fit:
- **Server functions are TypeScript/JavaScript only.** The Python quickstart installs the `convex` npm package and writes `convex/tasks.ts`. Python (`pip install convex`) is a CLIENT that calls `"tasks:get"`. QMX's backend (QMF/QMB/QML/agents) is Python, so Convex would add a second backend language and move business logic out of Python.
- Self-hosting:
  - open-source backend (Rust + TS), FSL-Apache-2.0 license (fine for personal use; it only forbids competing hosting)
  - Docker or a single binary, including a published `x86_64-pc-windows-msvc` build
  - SQLite by default, optional Postgres/MySQL, optional S3 for files, exports and snapshots
  - Self-hosted = free-tier feature set, not tuned for scale
- Cloud pricing: Free/Starter $0 with 1M function calls/mo, then $2.20 per 1M. Pro is $25 per developer per month.
- Limits: 1 s user-code time per query/mutation; 16 MiB read / 16 MiB written per transaction; 32k documents scanned; 1 MiB values.
- **Per-app DB.** One Convex deployment = one database. "DB per mini app" means either a deployment per app (heavy) or a Component per app (isolated tables, but all in one deployment and one backup unit). Remote trading nodes would need their own deployment, or a hard network dependency on the laptop or cloud.
- **Analytics.** A document store with transaction scan caps is wrong for time-series and backtests. Those stay in Parquet/DuckDB anyway.

**Verdict: not a fit as QMX's storage layer.**
- It conflicts with DEC-0117 (no database server; Python-owned contracts).
- It splits the backend into TS + Python.
- It adds a server process on every node.
- It brings nothing to analytics.

The one real attraction is live UI sync. QMX can get that from its own daemon (journal events over WebSocket/SSE) without a second backend.

Revisit only if two things both happen: (a) the UI becomes a multi-device, real-time collaborative surface, and (b) the operator accepts a TypeScript backend tier. Even then, use it as the UI-sync tier, never for trading-node state.

Ideas worth stealing without adopting Convex:
- the Component model: isolated tables plus an explicit capability surface per mini app
- the end-to-end typed query/mutation API per app

---

## E. App sandbox recommendation

Sources:
- Firecracker (needs Linux KVM): https://github.com/firecracker-microvm/firecracker
- E2B persistence (pause/resume; paused sandboxes are kept indefinitely; billed per second; Pro $150/mo for multi-day sessions): https://docs.e2b.dev/sandbox/persistence, https://e2b.dev/
- Modal Sandboxes (image + volumes + filesystem/memory snapshots; runtime `gvisor` or `vm`): https://modal.com/docs/guide/sandboxes, https://modal.com/docs/guide/volumes, https://modal.com/docs/guide/sandbox-snapshots
- Hermes terminal backends (local, Docker, SSH, Daytona, Modal, Singularity, Vercel; per-session containers optional), from the Hermes docs above.

### E1. Mental model (Docker words → QMX words)
| Docker | QMX | Concretely |
|---|---|---|
| image | **App definition** | `app.toml` manifest (id, version, mode: agent-driven / agent-free / headless; entrypoints; declared capabilities such as network, broker, data rooms; schedule) + code + `uv.lock`. Immutable, content-hashed, versioned. |
| container | **App instance** | one running process tree of a definition on one node, with its own env, secrets scope, resource limits, logs, heartbeat |
| volume | **App data** | `<qmx_home>/apps/<app_id>/` (section C1): `app.db`, `memory.db`, `data/`, `blobs/`. It outlives instances and is the backup unit. |
| registry | **App catalog** | the bucket or git holding definitions; nodes pull them by hash |
| `docker run -v` | **install / start** | materialize the definition → create or attach the volume → launch with the volume path as its only writable root |
| compose / k8s | **node supervisor** | the QMX daemon on each node: start/stop/restart, health, snapshot+rclone job, Litestream on Linux |

The three app modes differ only in their entrypoints:
- agent-driven: the LangGraph agent plus the app's tools, with memory in `memory.db`
- agent-free: plain Python jobs and handlers
- headless: no UI routes; schedule-driven or API-driven

The same definition, instance and data shape covers all three.

### E2. Isolation tiers. Pick per app by trust, not by fashion.
| Tier | Mechanism | Windows laptop | Linux node | Use for |
|---|---|---|---|---|
| T0 | in-process module | yes | yes | first-party, trusted, tiny apps (avoid for anything agent-written) |
| **T1 (default)** | **subprocess + per-app venv (`uv`) + its own working dir; Windows Job Object or Linux cgroup limits; env scrubbed to the declared secrets** | **yes** | yes | first-party and operator-built apps, including trading apps |
| T2 | Docker container: image built from the definition, volume = app dir, network policy | Docker Desktop (WSL2); heavier; free for personal use | **default on nodes** | agent-generated code; any app with third-party deps; every remote trading node (reproducible deploys) |
| T3 | remote microVM (E2B Firecracker, Modal gVisor/VM, Daytona) | n/a (remote) | n/a | untrusted or agent-written code that must not touch local data or secrets; bursty compute; "any compute provider" |
| — | local Firecracker | **no** (KVM only) | possible, but heavy ops for a single operator | not recommended |

Rules:
1. **The volume is the only writable path an app gets.**
   - T1: chdir there and deny writes elsewhere, by convention plus a check in the supervisor.
   - T2: bind mount.
   - T3: sync the volume in and out at instance start and stop (Modal Volume / E2B files). The DB stays authoritative on the home node. Never run a live SQLite file over a network filesystem.
2. Secrets are injected per instance from the declared capability list (on the laptop: Windows Credential Manager `qmx/*`, per the existing ruling). They never go into the volume or the image.
3. An instance writes its own `app.db` with exactly one writer process. The supervisor's backup job uses the online backup API, so it never needs to stop the app.
4. Moving an app to another node: stop the instance → final snapshot → rclone → restore on the target → start. Litestream nodes can restore straight from the replica.
5. Agent-written app code starts at T2 or T3 and is promoted to T1 only after operator review. This mirrors Hermes's write_approval idea, applied to code.

### E3. Net recommendation
- Laptop: T1 (uv venv subprocess) for every app.
- Trading nodes: T2 Docker. The image comes from the same definition, and `/apps/<id>` is mounted as the volume.
- T3 is a pluggable "compute provider" for untrusted or bursty work, so the UI shows where each instance runs.
- The DB always lives in the app's volume on its home node. Backup is snapshot + rclone everywhere, with Litestream added on Linux nodes when the RPO needs to be seconds.

---

## Open items / uncertainty
- The Hermes docs disagree on the bundled count (3 vs 5). Moot after 2026-10-15, when everything moves to the catalog.
- LangMem is 0.0.x. Keep it behind the provider boundary.
- The SqliteStore vector path depends on the `sqlite-vec` extension loading on Windows. Verify with a spike before turning semantic search on.
- Litestream on Windows is unsupported. That is why it is recommended only for Linux nodes.
- Turso's future under Supabase is unclear. One more reason not to adopt it as a core dependency now.
