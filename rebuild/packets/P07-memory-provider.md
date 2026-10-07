# P07: Memory provider

## Goal
One pluggable memory interface, Hermes style: built-in memory plus at most one external provider, chosen in settings. The default is a LangGraph `SqliteStore`.

## Read first
`rebuild/DESIGN.md` §5.4; `rebuild/research/research-memory-storage.md` §A3 and §B (B4 signatures, B6 rules).

## Build (`qmx_agents.memory`)
1. Types and classes:
   - `Scope`, `MemoryContext`, `MemoryRecord`, `ConfigField`
   - the `MemoryProvider` protocol, plus a base class whose hooks do nothing
   - `MemoryManager` (built-in plus at most one external provider)
   - `StoreMemoryProvider(SqliteStore)`
2. Namespaces:
   - global `("qmx", profile, "global", kind)`
   - session `("qmx", profile, "session", session_id, kind)`
   - workflow `("qmx", profile, "workflow", workflow_id, kind)`
   - task `("qmx", profile, "workflow", workflow_id, "task", task_id, kind)`
3. `MemoryManager.middleware()` returns LangChain middleware:
   - `before_agent`: loads the pinned profile block (about 2k characters, frozen for the session)
   - `before_model`: prefetch; output is capped, and long output spills to a file reference
   - `after_agent`: `on_turn_end`, without blocking
   - a summarization hook: `on_pre_compress`
4. Rules:
   - Automatic writes only when `role == "primary"`.
   - Global writes go through an approval hook, on by default.
   - Providers register via the `qmx.memory_providers` entry point.
   - Nothing is imported until config names the provider.
5. Wire into `build_agent` (P06) from `spec.memory.scope`.
6. File locations: `<qmx_home>/copilot/memory.db`, `<qmx_home>/apps/<id>/memory.db`.

## Not in scope
External providers (Mem0, Honcho, Hindsight), semantic search (needs a `sqlite-vec` Windows spike first), LangMem.

## Tests
- CRUD in each scope
- scope isolation
- a sub-agent role makes no automatic writes
- a global write needs approval
- the prefetch cap holds
- a swapped-in fake provider works with no agent changes
