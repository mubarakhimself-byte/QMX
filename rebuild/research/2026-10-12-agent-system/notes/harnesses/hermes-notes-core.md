# Hermes Agent (Nous Research) — Core Harness Notes

Reference study for the QMX Deep Agents / LangGraph agent layer. Every claim cites
the public page URL. Config keys, file names, method/hook names are quoted verbatim.
Base URL: `https://hermes-agent.nousresearch.com/docs/<path>`. Pages read fully as of
2026-10-12. Hermes is a Python synchronous agent (not LangGraph); treat it as a design
reference, not an API to copy.

---

## Architecture & loop

Source: `/developer-guide/architecture`, `/developer-guide/agent-loop`.

- Entry points (CLI `cli.py`, Gateway `gateway/run.py`, ACP `acp_adapter/`, Batch Runner,
  API Server, Python Library) all converge on one `AIAgent` class. `run_agent.py` is a thin
  **facade**; the loop body lives in `agent/conversation_loop.py`, each turn phase in
  `agent/turn_*.py` (iteration_prep, api_call, api_error, overflow, truncation, recovery),
  constructor wiring in `agent/agent_init.py`. "One AIAgent class serves CLI, gateway, ACP,
  batch, and API server" — platform differences live at the entry point (`/developer-guide/architecture`, Design Principles).
- **Two public entry points:** `agent.chat("...")` (returns final string) wraps
  `agent.run_conversation(user_message, system_message=None, conversation_history=None, task_id=...)`
  (returns dict with messages/metadata/usage). `chat()` extracts `final_response`
  (`/developer-guide/agent-loop`, Two Entry Points).
- **Three API modes**, all converging on OpenAI-style `role`/`content`/`tool_calls` dicts
  internally: `chat_completions` (OpenAI-compatible, `openai.OpenAI`), `codex_responses`
  (OpenAI Codex/Responses), `anthropic_messages` (native Anthropic via
  `agent/anthropic_adapter.py`). Resolution order: explicit `api_mode` arg → provider detection
  → base-URL heuristic → default `chat_completions` (`/developer-guide/agent-loop`, API Modes).
- **Turn lifecycle** (`run_conversation()`): generate task_id → append user msg → build/reuse
  cached system prompt → preflight compression check (>50% context) → build API messages →
  inject ephemeral layers (budget/pressure) → apply prompt-cache markers (Anthropic) →
  interruptible API call → if `tool_calls` execute + append + loop, else persist + flush memory + return
  (`/developer-guide/agent-loop`, Turn Lifecycle).
- **Strict message alternation** enforced: never two assistant or two user in a row; only `tool`
  role may be consecutive (parallel results) (`/developer-guide/agent-loop`, Message Alternation Rules).
- **Interruptible calls:** `_interruptible_api_call()` runs HTTP in a background thread while the
  main thread watches response/interrupt/timeout. On `/stop`, new input, or signal the API thread is
  abandoned; no partial response enters history (`/developer-guide/agent-loop`, Interruptible API Calls).
- **Tool execution:** single call runs in main thread; multiple run concurrently via
  `ThreadPoolExecutor`; interactive tools (e.g. `clarify`) force sequential; results reinserted in
  original order. Per-call flow fires `pre_tool_call` hook → dangerous-command check
  (`tools/approval.py`) → execute → `post_tool_call` hook → append `{"role":"tool",...}`
  (`/developer-guide/agent-loop`, Tool Execution).
- **Agent-level tools** intercepted by `agent/tool_executor.py` BEFORE registry dispatch (they touch
  agent state and return synthetic results): `todo` / `todo_list`, `memory`, `session_search`,
  `delegate_task` (`/developer-guide/agent-loop`, Agent-Level Tools; `/developer-guide/tools-runtime`, Agent-loop tools).
- **Budget:** `IterationBudget` default 500 iterations (`agent.max_turns`); subagents get independent
  budgets capped at `delegation.max_iterations` (default 50); at 100% the agent returns a work summary
  (`/developer-guide/agent-loop`, Iteration Budget).
- **Fallback:** on 429/5xx/401/403 tries `fallback_providers` chain in order; refreshes creds on
  401/403; a Codex Responses reasoning-only stall (3 consecutive continuations) fails over with reason
  `incomplete_response`. Auxiliary tasks (vision/compression/web-extract) have their own `auxiliary.*`
  fallback chains (`/developer-guide/agent-loop`, Fallback Model; `/developer-guide/provider-runtime`, Fallback models).
- **Callbacks** for real-time UI: `tool_progress_callback`, `thinking_callback`, `reasoning_callback`,
  `clarify_callback`, `step_callback`, `stream_delta_callback`, `tool_gen_callback`, `status_callback`
  (`/developer-guide/agent-loop`, Callback Surfaces).
- Design principles: prompt stability (no mid-conversation mutation except `/model`), observable
  execution, interruptible, loose coupling via registry + `check_fn` gating, profile isolation
  (`/developer-guide/architecture`, Design Principles).

---

## Profiles and the on-disk HERMES_HOME layout

Source: `/developer-guide/session-storage`, `/user-guide/profiles`, `/user-guide/which-file-does-what`,
`/user-guide/profile-distributions`, `/user-guide/features/memory`, `/user-guide/features/skills`,
`/user-guide/features/curator`.

- A **profile = a separate HERMES_HOME directory** with its own config, keys, memory, sessions, skills,
  cron, state DB, gateway PID, logs. Default profile is `~/.hermes` itself; named profiles live at
  `~/.hermes/profiles/<name>/`. Resolver `get_hermes_home()` precedence: context-local override →
  `HERMES_HOME` env var → platform default (`~/.hermes` on macOS/Linux, `%LOCALAPPDATA%/hermes` on
  Windows) (`/developer-guide/session-storage`, Hermes home and profile isolation; `/user-guide/profiles`, How it works).
- A dir under `profiles/` counts as a profile only if it carries an identity file: `config.yaml`,
  `.env`, `SOUL.md`, `profile.yaml`, `auth.json`, or `state.db` (`/user-guide/profiles`, What are profiles).
- **Rule: never point two agent processes at one HERMES_HOME** — both auto-write memory and reload each
  other at session start; use an external memory provider for shared memory (`/user-guide/profiles`, caution;
  `/user-guide/features/memory`, One agent per Hermes home).
- `HERMES_HOME` is the profile boundary; `HOME` stays the OS user home by default (so `git`/`ssh`/`gh`/`npm`
  find creds). `terminal.home_mode: profile` switches tool subprocess `HOME` to `{HERMES_HOME}/home`;
  `HERMES_REAL_HOME` still exposes the real home (`/user-guide/profiles`, How it works).
- Named profiles auto-create a command alias at `~/.local/bin/<name>` = `hermes -p <name>`; `-p`/`--profile`
  flag and sticky `hermes profile use <name>` also target profiles (`/user-guide/profiles`, Using profiles).

**HERMES_HOME on-disk layout (compiled from the cited pages — exact names):**

```
~/.hermes/                         # (default profile = HERMES_HOME root)
├── config.yaml                    # model, provider, toolsets, all settings
├── .env                           # API keys, bot tokens (secrets)
├── .env.EXAMPLE                   # generated by profile install
├── SOUL.md                        # agent identity, slot #1 of prompt
├── auth.json                      # OAuth/platform creds; refresh writes back to root
├── auth.lock
├── profile.yaml                   # display_name + profile identity
├── state.db / state.db-wal / state.db-shm   # SQLite session store (WAL mode)
├── context_length_cache.yaml      # model context-window cache (bedrock_confirmed_v1 map)
├── todo.json
├── system_prompt.md               # (export-allowlisted artifact)
├── AGENTS.md / CLAUDE.md / .cursorrules     # (if present at home root)
├── memories/
│   ├── MEMORY.md                  # agent notes (2,200-char cap)
│   └── USER.md                    # user profile (1,375-char cap)
├── skills/                        # single source of truth for skills
│   ├── <category>/<skill>/SKILL.md (+ references/ templates/ scripts/ assets/ examples/)
│   ├── .bundled_manifest          # name → origin content hash for bundled sync
│   ├── .usage.json                # curator telemetry + created_by/pinned/state per skill
│   ├── .curator_ledger.jsonl      # append-only mutation ledger
│   ├── .archive/                  # curator-archived skills (recoverable)
│   ├── .curator_backups/          # pre-consolidation tar.gz snapshots + blobs/
│   ├── .hub/ (lock.json, taps.json, quarantine/, audit.log)
│   └── .no-bundled-skills         # opt-out marker
├── skill-bundles/<slug>.yaml      # bundle slash-command aliases
├── plugins/                       # general + memory/ + context_engine/ + model-providers/ + platforms/
├── cron/                          # jobs.json (+ runtime locks/ledgers/output/suggestions)
├── pending/skills/<id>.json       # staged skill writes (write_approval)
├── logs/                          # agent.log, errors.log, process-results/, curator/<ts>/
├── cache/                         # exec/, image_token_costs.json, project_skill_scans/, scratch/, *_cache/
├── knowledge/ preferences/ plans/ workspace/ scripts/ home/
├── desktop.json                   # desktop theme/layout (desktop export only)
├── mcp.json / mcp-tokens/
├── backups/ state-snapshots/ checkpoints/ profile-exports/
├── installs/ tools/ runtimes/ models/ node/ bin/   # PM-managed, machine-specific, not portable
├── .codex_gpt55_autoraise_notice  # one-time notice marker
└── profiles/<name>/               # each named profile = a full copy of the tree above
```

Sources for individual entries: `memories/` (`/user-guide/features/memory`, How It Works);
`state.db*` siblings (`/developer-guide/session-storage`, Database Location); `skills/` dotfiles
(`/user-guide/features/skills`, Skill Directory Structure; `/user-guide/features/curator`, telemetry/ledger);
`cache/exec/` (`/user-guide/features/code-execution`); `cache/image_token_costs.json` and
`context_length_cache.yaml` (`/developer-guide/context-compression-and-caching`); export allow-list and
hard-excluded paths (`/user-guide/profile-distributions`, What an export file contains / What's NOT in a
distribution); `installs/ tools/ cache/` non-portable (`/user-guide/profiles`, Sharing a profile).

- Profile cloning flags: `--clone` (config+`.env`+`SOUL.md`+skills+`memories/MEMORY.md`+`memories/USER.md`+
  `plugins/`), `--clone-all` (everything minus history/cron/OAuth), `--clone-from <src>`,
  `--no-skills`. OAuth logins are shared via root `auth.json`, never copied (single-use refresh tokens)
  (`/user-guide/profiles`, Creating a profile).
- **Profile distributions** package a whole agent as a git repo: `distribution.yaml` (only `name` required) +
  `SOUL.md` + `config.yaml` + `skills/` + `cron/jobs.json` + `mcp.json`. `hermes profile install <git-url>`;
  updates replace distribution-owned files, merge `cron/jobs.json` by id, preserve user `config.yaml`,
  never touch `memories/`/`sessions/`/`auth.json`/`.env` (`/user-guide/profile-distributions`).

---

## Prompt assembly and prompt caching

Source: `/developer-guide/prompt-assembly`, `/developer-guide/context-compression-and-caching`,
`/user-guide/features/personality`, `/user-guide/features/context-files`.

- Cached system prompt = **three ordered tiers** (assembled by `agent/system_prompt.py` /
  `agent/prompt_builder.py`), joined `stable → context → volatile`:
  1. **stable** — identity (`SOUL.md` or `DEFAULT_AGENT_IDENTITY` fallback), tool/model guidance,
     coding operating brief, platform hints (byte-stable, live in stable tier).
  2. **context** — caller `system_message`, project context file (`.hermes.md`/`AGENTS.md`/`CLAUDE.md`/
     `.cursorrules`), then worktree-dependent git workspace snapshot, operator instructions, platform hints.
  3. **volatile** — skills index (`<available_skills>`), `MEMORY.md` snapshot, `USER.md` snapshot, external
     memory-provider block, timestamp/session/model/provider line, then runtime environment block (host/home/cwd)
     which ALWAYS ends the tier (`/developer-guide/prompt-assembly`, Cached system prompt layers).
- Ordering is deliberate for caching: shared project files come BEFORE anything naming the current worktree,
  so sessions of one project in different worktrees share a longest-prefix cacheable prefix. `_stored_prompt_matches_runtime()`
  (`agent/conversation_loop.py`) validates the stored prompt against the `# Hermes runtime environment` boundary
  (`/developer-guide/prompt-assembly`, Cached system prompt layers).
- **Surface/skills changes ride a one-shot per-turn user-message note, not a prompt mutation**, to keep the
  cached prefix: a surface switch (desktop↔TUI) via `agent/surface_switch.py`; a changed `<available_skills>`
  index via `agent/skills_index_delta.py` (compared each turn in `build_turn_context`); the index converges at
  the next compaction rebuild (`/developer-guide/prompt-assembly`, Cached system prompt layers).
- **API-call-time-only layers (never cached):** `ephemeral_system_prompt`, prefill messages,
  gateway session-context overlays, later-turn external recall, and `pre_llm_call` plugin context (appended to
  the current turn's USER message, never the system prompt) (`/developer-guide/prompt-assembly`, API-call-time-only layers).
- `SOUL.md` loaded by `load_soul_md()` from `get_hermes_home()/SOUL.md` only (never cwd); security-scanned
  (`_scan_context_content`, warn-but-load for user SOUL) and truncated (`_truncate_content`, cap scales with
  context window, 20k floor, `context_file_max_chars` override wins). `build_context_files_prompt(skip_soul=True)`
  prevents double-loading. `skip_context_files` (subagent delegation) uses the hardcoded `DEFAULT_AGENT_IDENTITY`
  (`/developer-guide/prompt-assembly`, How SOUL.md appears; `/user-guide/features/personality`).
- **Project context priority (first match wins, ONE loaded):** `.hermes.md`/`HERMES.md` (walks to git root) →
  `AGENTS.override.md` → `AGENTS.md` (cwd + progressive subdirectory discovery via `agent/subdirectory_hints.py`,
  `SubdirectoryHintTracker`) → `CLAUDE.md` → `.cursorrules`/`.cursor/rules/*.mdc`. Subdir hints capped at 32,000
  chars; startup context files capped at `context_file_max_chars` (`/user-guide/features/context-files`).
- All context files are prompt-injection scanned; a hit on a project file inserts `[BLOCKED: …]`; the user's
  own `SOUL.md` warns but loads (`/user-guide/features/context-files`, Security).
- **Prompt caching (Anthropic), `agent/prompt_caching.py`:** strategy `system_and_3` — 4 `cache_control`
  breakpoints: system prompt (stable) + rolling last-3 non-system messages. Markers `{"type":"ephemeral"}` or
  `{"type":"ephemeral","ttl":"1h"}`. TTL config `prompt_caching.cache_ttl: "5m"|"1h"|"auto"`; `auto` resolves
  per session (`_init_prompt_cache_config` / `auto_cache_ttl_for_source`): `1h` for human-paced, `5m` for
  `MACHINE_PACED_SOURCES` (subagent, cron, oneshot, webhook, kanban, api, tool, batch). ~75% input-token savings.
  **Model identity is part of the cache key** — any mid-session `/model`/fallback/credential-pool rotation = zero
  cache hits (`/developer-guide/context-compression-and-caching`, Prompt Caching).
- **Prompt surface is CI-committed:** `scripts/ci/prompt_surface.py render` renders 9 surfaces into
  `tests/fixtures/prompt_surface/`; `tests/ci/test_prompt_surface.py` fails on stale snapshot; changes need
  `hermes-agent-core` approval (`/developer-guide/prompt-assembly`, Reviewing changes to the prompt surface).

---

## Compression, compaction, micro-compaction

Source: `/developer-guide/context-compression-and-caching`, `/developer-guide/micro-compaction`,
`/developer-guide/context-engine-plugin`.

- **Pluggable `ContextEngine` ABC** (`agent/context_engine.py`); default `ContextCompressor`
  (`agent/context_compressor.py`); selected via `context.engine` in config.yaml (`"compressor"` default,
  `"lcm"` example). Resolution: `plugins/context_engine/<name>/` → general plugin `register_context_engine()`
  → built-in. Plugin engines are never auto-activated (`/developer-guide/context-compression-and-caching`, Pluggable Context Engine).
- **Dual compression:** (1) Gateway Session Hygiene at **85%** of context (`gateway/run_turn.py`, safety net,
  fires only when `len(history)>=4`); (2) Agent `ContextCompressor` at **50%** default (`compression.threshold: 0.50`),
  in-loop with real API token counts (`/developer-guide/context-compression-and-caching`, Dual Compression System).
- **Token accounting via usage anchor** (`agent/usage_anchor.py`): provider's last prompt+completion tokens +
  rough estimate of only messages appended since; identified by content fingerprint; persisted on session row to
  survive `--resume`/desktop per-turn serve. Without an anchor, a whole-context rough estimate over threshold
  **waits one request** for provider evidence (`should_defer_preflight_to_real_usage`) (same page, Token accounting).
- **Key config keys** (`compression:` block): `enabled` (true), `threshold` (0.50; floored at 0.75 below 512K
  windows), `threshold_tokens` (null = ratio-only absolute cap), `model_thresholds` (substring match, longest-key-wins,
  `<provider>:<substring>` scoping), `target_ratio` (0.20, legacy-tail only), `tail_mode` (`lean` default | `legacy`),
  `protect_last_n` (20), `min_tail_user_messages` (1), `protect_first_n` (3, hardcoded), `idle_compact_after_seconds`
  (0), `in_place` (true), `micro_compact` (false), `codex_gpt55_autoraise` (true, raises trigger to 85% for Codex
  OAuth gpt-5.x/Astra at 272K), `codex_app_server_auto` (`native`), `codex_responses_native` (false),
  `checkpoint_required` (false). Summary model under `auxiliary.compression.{model,provider,base_url}`
  (`/developer-guide/context-compression-and-caching`, Configuration / Parameter Details).
- **`lean` tail** keeps a clamped tail of `2.5% × context window` (10K floor, 25K cap) and carries continuity in
  the summary: identifier-preserving session log, mechanically extracted anchor index (PR#/SHAs/paths/error strings
  via regex), every real user message quoted verbatim newest-first, and a `session_search` recovery pointer. One
  auxiliary LLM call per attempt. `legacy` keeps a `target_ratio`-sized verbatim tail (`/developer-guide/context-compression-and-caching`, tail_mode).
- **In-place compaction (`in_place: true`, default):** rewrites live message list on the SAME session id;
  pre-compaction rows soft-archived under same id (`active=0, compacted=1`), still searchable/recoverable. No
  `parent_session_id` chain. `in_place: false` = legacy rotation with `parent_session_id` links
  (`/developer-guide/context-compression-and-caching`, In-place compaction).
- **`ContextCompressor.compress()` 4-phase algorithm:** Phase 1 prune old tool results (>200 chars outside tail →
  `[Old tool output cleared to save context space]`, no LLM); Phase 2 determine boundaries (token-budget tail walk
  backward, aligned via `_align_boundary_backward()` to keep tool_call/result groups intact; `protect_first_n=3`
  head); Phase 3 structured summary via `call_llm(task="compression")` with a fixed template (Goal / Constraints &
  Preferences / Progress [Done/In Progress/Blocked] / Key Decisions / Relevant Files / Next Steps / Critical
  Context); Phase 4 assemble head + summary + unmodified tail, `_sanitize_tool_pairs()` fixes orphans. Summary
  budget `content_tokens × 0.20` (`_SUMMARY_RATIO`), min 2,000, max `min(context_length × 0.05, 12,000)`
  (`/developer-guide/context-compression-and-caching`, Compression Algorithm).
- **Warning:** summary model context window must be ≥ main model's, else context-length error →
  `_generate_summary()` returns `None` and the middle is dropped WITHOUT a summary (most common cause of degraded
  compaction) (`/developer-guide/context-compression-and-caching`, Phase 3 warning).
- **Iterative re-compression:** previous summary (`_previous_summary` field) passed back to update in place rather
  than resummarize (`/developer-guide/context-compression-and-caching`, Iterative Re-compression).
- **Failure cooldown:** escalating 60s→300s→900s per-session, persisted in `state.db`; three stall paths run a real
  attempt anyway (manual `/compress force=True`, same-turn `fallback_chain` `bypass_cooldown`, provider-proven
  overflow); repeated stall → deterministic fallback summary (`DETERMINISTIC_SUMMARY_ROUTE`);
  `abort_on_summary_failure` (default false). Telemetry line `context compression attempt telemetry: {...}` with
  `trigger_source`/`route`/`commit_status`/`method`/token counts (`/developer-guide/context-compression-and-caching`, Failure cooldown / Attempt telemetry).
- **Native Responses compaction** (gpt-5.6 / Astra on OpenAI or Codex OAuth): server prunes into opaque encrypted
  `compaction` output item, captured into the assistant replay sidecar; opt-in `codex_responses_native: true`,
  threshold clamped ~8K below local trigger (`/developer-guide/context-compression-and-caching`, Native Responses compaction).
- **Micro-compaction** (`compression.micro_compact: true`, OFF by default): after each turn `finalize_turn` folds
  the single oldest un-absorbed EXCHANGE into one rolling summary. An exchange starts at the ASSISTANT message, so
  **user messages are never summarized** (source of truth kept, derived material compacted). Head and tail stay
  verbatim. Keys: `micro_compact_every_n_turns` (1), `micro_compact_defrag_threshold_tokens` (2000). A **cursor**
  tracks first-unabsorbed index (recovered from last summary marker on resume). **Defrag** re-summarizes the rolling
  summary when it crosses the threshold. Uses `auxiliary.compression` model (favor small fast non-reasoning instruct
  model — latency dominates, runs every turn). **Cost: rewrites sent history every turn → breaks provider prompt
  cache every turn** (the main argument against it). DB sync via `archive_and_compact` (soft-archive + insert).
  3 consecutive failures on one exchange → advance cursor past it. Best-effort/fail-open. Telemetry
  `micro compaction telemetry: {...}` with `occupancy_pct` (`/developer-guide/micro-compaction`).
- **Pre-compress checkpoint (fail-closed), memory providers:** `on_pre_compress(messages, require_checkpoint=False)`
  with `pre_compress_checkpoint_api_version = 2`; `compression.checkpoint_required: true` blocks lossy rewrite until
  an advertising provider commits; checkpoints must be idempotent (key by content digest). The gate suppresses
  native compaction, forces `micro_compact` off, refuses `codex_app_server` (`/developer-guide/memory-provider-plugin`, Pre-Compress Checkpoints).
- Intermediate context-pressure warnings were REMOVED (they made models "give up"); compression simply fires at
  `compression.threshold` (`/developer-guide/context-compression-and-caching`, Context Pressure Warnings).

---

## Sessions and storage

Source: `/developer-guide/session-storage`, `/user-guide/sessions`, `/user-guide/features/memory`.

- SQLite `state.db` (WAL mode) at `get_hermes_home()/state.db`. Facade `hermes_state.py` +
  `hermes_state_*.py` siblings. Tables: `sessions`, `messages`, `session_model_usage`, `messages_fts`
  (FTS5), `messages_fts_trigram`, `messages_fts_cjk`, `state_meta`, `gateway_routing`,
  `compression_locks`, `async_delegations`, `delivery_obligations`, `schema_version`
  (`/developer-guide/session-storage`, Architecture Overview).
- Design: WAL for concurrent readers + 1 writer; FTS5 full-text; **session lineage** via
  `parent_session_id` (rotation mode); source tagging (`cli`, `telegram`, `oneshot`, `subagent`, `cron`,
  `kanban`, `tool`, `webhook`, `acp`, `batch`, …) for platform filtering (`/developer-guide/session-storage`,
  Key design decisions; `/user-guide/sessions`, Session Sources).
- `messages` carries stable ids: `message_uid` (32-hex `uuid4().hex`, minted once, copied across clones),
  `absorbed_message_uids` (merge witness), `tool_call_uids`/`tool_call_uid` (per-occurrence tool-call ids).
  Current schema **version 31** added these (`/developer-guide/session-storage`, Messages Table / Schema Version).
- `reasoning`/`reasoning_content`/`reasoning_details` always kept; `api_content` is a byte-fidelity replay
  sidecar (exact wire bytes when they differ from `content`) (`/developer-guide/session-storage`, Messages Table).
- Write contention: short 1s SQLite timeout + time-budgeted app retry with jitter (`_WRITE_PATIENCE_S=20`,
  `_TRANSCRIPT_WRITE_PATIENCE_S=60`, `_ACTIVITY_WRITE_PATIENCE_S=0.5`), `BEGIN IMMEDIATE`, PASSIVE WAL
  checkpoint every 50 writes; exhaustion → `session_persistence_failed:locked`
  (`/developer-guide/session-storage`, Write Contention Handling).
- FTS5 query syntax (`search_messages()`): implicit AND, quoted phrase, `OR`, `NOT`, prefix `deploy*`;
  filters `source_filter`/`exclude_sources`/`role_filter`; snippets with `>>>match<<<`
  (`/developer-guide/session-storage`, Full-Text Search).
- **Memory needs session boundaries**: memory snapshot is frozen at session start (preserves prefix cache);
  messaging chats are one continuous session surviving restarts → run `/new` at task boundaries so memory +
  `session_search` loop fires (`/user-guide/sessions`, What Counts Toward Context; `/user-guide/features/memory`, Memory Needs Session Boundaries).
- Media is turn-scoped: images attached once / pre-analyzed to text, audio transcribed, raw bytes not recopied
  into future prompts (`/user-guide/sessions`, What Counts Toward Context).

---

## Tools, toolsets, registry, tool search, code execution

Source: `/developer-guide/tools-runtime`, `/developer-guide/adding-tools`, `/user-guide/features/tools`,
`/user-guide/features/tool-search`, `/user-guide/features/code-execution`, `/reference/toolsets-reference`.

- **Self-registering tools:** each `tools/*.py` calls `registry.register(name, toolset, schema, handler,
  check_fn, requires_env, is_async, description, emoji)` at import time → `ToolEntry` in singleton
  `ToolRegistry._tools`. `schema["description"]` is the authoritative model-facing description. Cross-toolset
  shadowing rejected unless `override=True` (+ `plugins.entries.<id>.allow_tool_override: true` for plugin
  overrides of built-ins) (`/developer-guide/tools-runtime`, Tool registration model).
- **Discovery:** `discover_builtin_tools()` AST-scans `tools/*.py` for top-level `registry.register()` calls
  and imports them (skips `__init__.py`, `registry.py`, `mcp_tool.py`); then MCP tools
  (`tools.mcp_tool_discovery.discover_mcp_tools()`) and plugin tools (`hermes_cli.plugins.discover_plugins()`)
  (`/developer-guide/tools-runtime`, Discovery).
- **`check_fn`**: returns True/available else tool silently excluded; exceptions = unavailable; results cached
  per-call; `is_toolset_available()` for UI (`/developer-guide/tools-runtime`, Tool availability checking).
- **Toolset resolution** `model_tools.get_tool_definitions(enabled_toolsets, disabled_toolsets, quiet_mode)`:
  enabled → only those (expanded via `resolve_toolset()`); disabled → all minus those; `registry.get_definitions()`
  applies `check_fn`; dynamic schema patching for `execute_code`/`browser_navigate`; legacy `_tools` names mapped
  via `_LEGACY_TOOLSET_MAP` (`/developer-guide/tools-runtime`, Toolset resolution).
- **Dispatch:** model tool_call → conversation loop → `handle_function_call()` → [agent-loop tools handled
  directly] → `pre_tool_call` hook → `registry.dispatch()` (async bridged by `_run_async()`) → `post_tool_call`.
  Handlers MUST return JSON strings; errors `{"error":"..."}`; double error-wrapping ensures well-formed result
  (`/developer-guide/tools-runtime`, Dispatch; `/developer-guide/adding-tools`, Key Rules).
- **Adding a built-in tool touches 2 files:** `tools/your_tool.py` (handler + schema + check_fn +
  `registry.register()`) and `toolsets.py` (`_HERMES_CORE_TOOLS` or a new toolset). Optional `OPTIONAL_ENV_VARS`
  in `hermes_cli/config.py`. Default to **plugins** for custom tools; prefer a **Skill** when the capability is
  instructions + shell + existing tools (`/developer-guide/adding-tools`).
- **Dangerous-command approval** (`tools/approval.py`): `DANGEROUS_PATTERNS` regex list (rm -rf, mkfs, dd, DROP
  TABLE, curl|sh, fork bombs…); `detect_dangerous_command()`; CLI interactive / gateway async callback / optional
  smart-approval aux LLM; per-session approval memory; "allow permanently" → `command_allowlist` in config.yaml
  (`/developer-guide/tools-runtime`, DANGEROUS_PATTERNS approval flow).
- Terminal backends: `local`, `docker`, `ssh`, `singularity`, `modal`, `daytona`, `vercel_sandbox` — Docker is
  one persistent container shared across the process (`docker exec`). Background processes via `process` tool;
  completed receipts kept (64 results / 7 days) under `logs/process-results/` (`/user-guide/features/tools`;
  `/developer-guide/tools-runtime`, Terminal/runtime environments).
- **Tool Search** (`tools.tool_search`, opt-in progressive disclosure): replaces MCP/plugin (+ deferred built-ins)
  tools with three bridge tools `tool_search(queries, limit?)`, `tool_describe(names)`, `tool_call(calls)`;
  `calls` batched up to 10. Tiered: Tier 0 (no deferred, pass-through), Tier 1 (bridge + per-server manifest),
  Tier 2 (bridge + one-line-per-server summary). Config `tools.tool_search.{enabled: auto, threshold_pct: 5,
  search_default_limit: 5, max_search_limit: 25, listing: auto, listing_max_tokens: 4000, defer: [...]}`.
  Retrieval = BM25 over name/source/description/params + Snowball stemming + rarest-token rule; catalog stateless
  per turn, scoped to session toolsets. Trade-offs: 1 extra round trip on cold tools, no cache on deferred schemas,
  model-quality-dependent (`/user-guide/features/tool-search`).
- **`execute_code`** (programmatic tool calling): agent writes Python importing `from hermes_tools import ...`;
  runs in a child process over a Unix-domain-socket RPC (loopback TCP on Windows; file-based on remote backends);
  only `print()` output returns — intermediate tool results never hit context. In-script tools: `web_search`,
  `web_extract`, `read_file`, `write_file`, `search_files`, `patch`, `terminal` (foreground only). Modes
  `code_execution.mode: project|strict`. **Persistent session kernel** (vars/imports persist; `reset:true` clears;
  `kernel_idle_timeout` 1800s, `max_session_kernels` 4). Limits: 300s timeout, 50KB stdout, 50 tool calls.
  Env scrubbed (KEY/TOKEN/SECRET/PASSWORD/… stripped); only `HERMES_HOME/HERMES_PROFILE/HERMES_CONFIG/HERMES_ENV`
  pass through (`/user-guide/features/code-execution`).

---

## Skills lifecycle

Source: `/developer-guide/creating-skills`, `/user-guide/features/skills`, `/user-guide/features/curator`.

- Skills are on-demand knowledge docs following **progressive disclosure**; compatible with the
  agentskills.io standard. All live in `~/.hermes/skills/` (bundled copied from repo on install; hub + agent
  created land here too) (`/user-guide/features/skills`).
- Progressive disclosure levels: `skills_list()` (~3k tokens, name/description/category) → `skill_view(name)`
  (full SKILL.md) → `skill_view(name, path)` (specific reference file). Full content loaded only when needed
  (`/user-guide/features/skills`, Progressive Disclosure).
- **SKILL.md frontmatter:** `name`, `description` (≤60 chars, shown in search), `version`, `author`, `license`,
  `platforms: [macos,linux,windows]`, and `metadata.hermes.{tags, related_skills, requires_toolsets, requires_tools,
  fallback_for_toolsets, fallback_for_tools, config, blueprint}`, plus `required_environment_variables` (name/prompt/
  help/required_for) and `required_credential_files`. Body sections: When to Use / Quick Reference / Procedure /
  Pitfalls / Verification (`/developer-guide/creating-skills`, SKILL.md Format).
- **Conditional activation:** `requires_toolsets`/`requires_tools` hide the skill when absent; `fallback_for_toolsets`/
  `fallback_for_tools` hide when the premium tool IS present (e.g. `duckduckgo-search` with
  `fallback_for_toolsets: [web]`) (`/developer-guide/creating-skills`, Conditional Skill Activation).
- Directory layout: `SKILL.md` (required) + `references/`, `templates/`, `scripts/`, `assets/`, `examples/`.
  Template tokens `${HERMES_SKILL_DIR}` and `${HERMES_SESSION_ID}` substituted in body; activation message exposes
  `[Skill directory: /abs/path]`. Optional inline shell `` !`cmd` `` (off by default, `skills.inline_shell`)
  (`/developer-guide/creating-skills`, Referencing bundled scripts / Inline shell snippets).
- **Precedence across skill dirs:** `project → local (~/.hermes/skills/) → skills.create_dir → external_dirs`.
  Project skills require `hermes skills trust`; scanned per git-pull; tagged `[project]`
  (`/user-guide/features/skills`, External Skill Directories / Project-Local Skills / Precedence).
- **Agent-created skills (procedural memory):** `skill_manage` tool with actions `create` (full SKILL.md via
  `content`), `patch` (targeted `old_string`/`new_string`, preferred; or full rewrite via `content`), `delete`,
  `write_file`, `remove_file`. Advisory linter rules `incident-log-shape`, `references-sprawl`, `oversized-body`
  (warn, never block). Skills capture "lessons not logs" (`/user-guide/features/skills`, Agent-Managed Skills).
- **`/learn`** turns sources (dirs, URLs, pasted notes, a whole book) into skills; large sources become
  knowledge-base skills (lean SKILL.md + per-topic `references/`). Foreground-created skills are `created_by: learn`
  (user-directed, curator-exempt) (`/user-guide/features/skills`, Learning a skill).
- **Write gate:** `skills.write_approval: true` stages every `skill_manage` write under `~/.hermes/pending/skills/<id>.json`;
  review with `/skills pending | diff | approve | reject | approval on`. Separate `skills.guard_agent_created`
  content scanner (`/user-guide/features/skills`, Gating agent skill writes).
- **Background self-improvement review** forks `AIAgent` after a turn (~every 10 turns), can save memory + skills;
  `auxiliary.background_review.{provider, model, enabled, max_input_tokens, defer, extra_tools}`; same-model review
  inherits parent reasoning effort; notifications `display.memory_notifications: off|on|verbose`
  (`/user-guide/features/memory`, Running the review on a cheaper model).
- **Curator** = background maintenance for agent-created skills (`/user-guide/features/curator`):
  - Triggered by inactivity check (CLI start / gateway housekeeping / serve maintenance timer), not cron.
    `curator.interval_hours` (168 = 7d), `min_idle_hours` (2).
  - Two phases: (1) deterministic auto-transitions `active → stale (stale_after_days 14) → archived
    (archive_after_days 30)` into `~/.hermes/skills/.archive/` (always on); (2) LLM consolidation
    (`curator.consolidate: true`, OFF by default; ~50-100 API calls) building umbrella skills via `skill_view` +
    `skill_manage`.
  - Config `curator.{enabled, interval_hours, min_idle_hours, stale_after_days, archive_after_days, consolidate,
    prune_builtins, backup.{enabled,keep}, archive_ttl_days}`; review model slot `auxiliary.curator`.
  - Never auto-deletes (worst case = archive). Pinned skills (`hermes curator pin`, stored `"pinned": true` in
    `.usage.json`) and cron-referenced skills are exempt from auto-transitions. "agent-created" = not in
    `.bundled_manifest`, not in `.hub/lock.json`, and `.usage.json` `created_by: agent`/`agent_created: true`
    (only the background review fork sets this).
  - Telemetry `~/.hermes/skills/.usage.json` (use_count/view_count/last_used_at/patch_count/state/pinned);
    ledger `~/.hermes/skills/.curator_ledger.jsonl`; snapshots `~/.hermes/skills/.curator_backups/<utc>/skills.tar.gz`;
    reports `~/.hermes/logs/curator/<ts>/{run.json,REPORT.md}`.
- Bundled-skill sync: `.bundled_manifest` records origin hash; locally-modified skills skipped forever;
  `hermes skills reset [--restore]` re-baselines (`/user-guide/features/skills`, Bundled skill updates).

---

## Memory: built-in files, limits, providers

Source: `/user-guide/features/memory`, `/user-guide/which-file-does-what`, `/developer-guide/memory-provider-plugin`,
`/user-guide/features/memory-providers`.

- Two built-in files in `~/.hermes/memories/`: **`MEMORY.md`** (agent notes, **2,200 chars ≈ 800 tokens**) and
  **`USER.md`** (user profile, **1,375 chars ≈ 500 tokens**). Injected as a frozen snapshot at session start;
  mid-session writes persist to disk immediately but only appear in the prompt next session (preserves prefix cache)
  (`/user-guide/features/memory`, How It Works / Frozen snapshot).
- Memory does NOT auto-compact: an over-limit write returns an error; agent reissues one `operations` batch that
  frees space + adds (limit checked on batch result). `memory` tool actions: `add`, `replace` (substring `old_text`,
  overwrites whole matched entry), `remove`; no `read` (`/user-guide/features/memory`, What Happens When Memory is Full / Memory Tool Actions).
- Entries rendered with a header (`MEMORY … [67% — 1,474/2,200 chars]`) and `§` delimiters; entries scanned for
  injection/exfiltration + invisible unicode before accepting (`/user-guide/features/memory`, How Memory Appears / Security Scanning).
- `memory.{memory_enabled, user_profile_enabled, memory_char_limit: 2200, user_char_limit: 1375, write_approval,
  prefetch_spill_enabled, provider}`. Both `_enabled` false drops the `memory` tool entirely
  (`/user-guide/features/memory`, Configuration).
- `write_approval: true` stages writes (foreground CLI prompts inline; everywhere else `/memory pending | approve |
  reject`) (`/user-guide/features/memory`, Controlling memory writes).
- `session_search` tool (FTS5 over `state.db`) = unbounded recall, ~20ms query, free (no LLM) — the complement to
  bounded in-prompt memory (`/user-guide/features/memory`, Session Search).
- `/journey` (learning journey): timeline of learned skills + memory chunks; `hermes journey list|delete|edit`
  (`/user-guide/features/memory`, Learning Journey).
- **External memory providers** (`MemoryProvider` ABC, `agent/memory_provider.py`), single-select via
  `memory.provider`, additive to built-in files. Discovery sources (earlier wins — REVERSE of general plugins):
  bundled `plugins/memory/<name>/` → user `$HERMES_HOME/plugins/<name>/` → project `./.hermes/plugins/<name>/`
  (`HERMES_ENABLE_PROJECT_PLUGINS=1`) → pip entry point `hermes_agent.memory_providers`
  (`/developer-guide/memory-provider-plugin`, Installation Layouts).
- **Provider interface** — required: `name` (property), `is_available()` (no network calls), `initialize(session_id,
  **kwargs)` (kwargs include `hermes_home`, `platform`, `cwd`, `gateway_session_key`, `agent_context` ∈
  primary/cron/subagent), `get_tool_schemas()`, `handle_tool_call(tool_name, args, **kwargs)`. Config:
  `get_config_schema()`, `save_config(values, hermes_home)`. Optional hooks: `system_prompt_block()`,
  `prefetch(query, *, session_id)`, `queue_prefetch(...)`, `sync_turn(user, assistant, *, session_id, messages=None)`
  (MUST be non-blocking, use `spawn_context_thread`), `on_session_end(messages)`, `on_pre_compress(messages)`,
  `on_memory_write(action, target, content, metadata)`, `shutdown()`. Entry point `register(ctx)` →
  `ctx.register_memory_provider(...)` (can also `ctx.register_skill(...)`). Profile isolation: storage MUST use the
  `hermes_home` kwarg (`/developer-guide/memory-provider-plugin`).
- Bundled providers: RetainDB, ByteRover; catalog: Honcho, Hindsight, Supermemory, Mem0, OpenViking, Holographic.
  `hermes memory setup | status | off`. All data handed to providers passes the secret-scrub first
  (`/user-guide/features/memory-providers`).

---

## Context files (AGENTS.md / SOUL.md / etc.)

Source: `/user-guide/features/context-files`, `/user-guide/which-file-does-what`, `/user-guide/features/personality`.

- **SOUL.md** = agent identity, slot #1, global to the instance (`HERMES_HOME/SOUL.md` only, never cwd); seeded if
  missing, never overwritten; durable voice/tone/style, not project rules (`/user-guide/features/personality`).
- **AGENTS.md** = project instructions; loads a merged chain git-root→cwd (deeper later = higher precedence), then
  progressive subdirectory discovery during the session; `AGENTS.override.md` (gitignored) loads INSTEAD of a
  committed `AGENTS.md` (`/user-guide/features/context-files`, AGENTS.md).
- Master table — who writes / when seen / where it lives: SOUL.md (you; slot #1; `~/.hermes/SOUL.md`), USER.md
  (agent via `memory` tool; frozen snapshot; `~/.hermes/memories/`), MEMORY.md (agent; frozen snapshot;
  `~/.hermes/memories/`), AGENTS.md (you; startup + progressive; project dir), `.hermes.md`/`HERMES.md` (you;
  startup, highest priority; project, walks to git root) (`/user-guide/which-file-does-what`, Master Table).
- `/personality` = session overlay (slot #8, after SOUL.md baseline); built-in presets + `agent.personalities`
  custom; `/personality none|default|neutral` resets (`/user-guide/features/personality`, Built-in personalities / Custom personalities).

---

## Provider runtime (brief)

Source: `/developer-guide/provider-runtime`.

- Shared resolver (`hermes_cli/runtime_provider.py`, `hermes_cli/auth.py`, `providers/`) maps `(provider, model)` →
  `(api_mode, api_key, base_url, source)`; used by CLI/gateway/cron/ACP/auxiliary. Precedence: explicit CLI/runtime →
  `config.yaml` → env vars → provider defaults. Per-provider plugins under `plugins/model-providers/<name>/` declare
  `api_mode`/`base_url`/`env_vars`/`fallback_models` and `register_provider()`. Native Anthropic prefers refreshable
  Claude Code credentials. 18+ provider families supported.

---

## Ideas QMX should borrow for a Deep Agents harness

1. **Three-tier cached prompt (`stable → context → volatile`) with the runtime/cwd block LAST** so multiple
   worktrees/sessions share a longest-prefix cache. Maps directly to LangGraph state assembly: keep volatile
   (memory snapshot, timestamp, cwd) at the tail of the system message (`/developer-guide/prompt-assembly`).
2. **Never mutate the cached prefix mid-session; ride changes on a one-shot user-message note** (skills-index delta,
   surface switch). A QMX copilot that gains/loses a tool should append a turn note, not rebuild the system prompt
   (`/developer-guide/prompt-assembly`, skills_index_delta / surface_switch).
3. **Frozen memory snapshot captured once at session start** (writes persist to disk, surface next session) — the
   cheap, cache-safe way to give copilots durable facts without per-turn invalidation (`/user-guide/features/memory`, Frozen snapshot).
4. **Bounded, hard-capped curated memory (2,200 / 1,375 chars) that errors instead of auto-dropping**, forcing the
   agent to consolidate — keeps the Portfolio/Lab copilots' standing context small and auditable
   (`/user-guide/features/memory`, Capacity Management).
5. **Lossy structured compaction with a fixed template (Goal/Constraints/Progress/Decisions/Files/Next/Critical) +
   a mechanically-extracted anchor index (regex SHAs/paths/IDs) + a search recovery pointer** — the `lean` tail is a
   strong model for QMX workflow-agent long runs over market data (`/developer-guide/context-compression-and-caching`, Compression Algorithm / tail_mode).
6. **Usage-anchor token accounting (real provider counts + delta since) with a one-request wait for evidence** rather
   than trusting local estimates to trigger compaction — avoids premature/needless compaction on noisy estimators
   (`/developer-guide/context-compression-and-caching`, Token accounting).
7. **Micro-compaction's asymmetry: compact derived material (assistant/tool output), never the user's instructions.**
   For QMX, never summarize the operator's trading intent/constraints; summarize tool spew. But note the per-turn
   prompt-cache break cost — keep it opt-in (`/developer-guide/micro-compaction`).
8. **In-place compaction on one stable session id (soft-archive `active=0,compacted=1`, still searchable)** instead
   of rotation chains — eliminates lost-state/orphan bugs; good fit for long-lived Portfolio sessions
   (`/developer-guide/context-compression-and-caching`, In-place compaction).
9. **Progressive-disclosure Tool Search bridge (`search`/`describe`/`call`) with BM25 + rarest-token rule + a visible
   name manifest** when many MCP/broker/data tools attach — keeps schema tokens bounded without hiding capabilities
   from the model (`/user-guide/features/tool-search`).
10. **`execute_code` programmatic tool calling over an RPC socket where only `print()` returns** — collapses
    multi-step quant data pipelines (fetch → filter → compute) into one turn and keeps intermediate results out of
    context; persistent kernel for iterative analysis (`/user-guide/features/code-execution`).
11. **Self-registering tool registry with `check_fn` availability gating + dynamic schema patching** so
    credential/data-source-gated tools (broker API, news feed) appear only when configured and the model can't
    hallucinate unavailable ones (`/developer-guide/tools-runtime`).
12. **Dangerous-command approval layer (`DANGEROUS_PATTERNS`, per-session memory, optional aux-LLM smart approval,
    persistent allowlist)** — a ready pattern for gating irreversible trade/transfer actions behind operator consent
    (`/developer-guide/tools-runtime`, DANGEROUS_PATTERNS approval flow).
13. **Skills as progressive-disclosure procedural memory (`skills_list → skill_view → skill_view(path)`) with
    conditional activation and knowledge-base `references/`** — exactly the Lab-copilot's "load the right playbook
    only when relevant" need; fits the QMX Lego vision (`/user-guide/features/skills`).
14. **Curator background maintenance (deterministic stale/archive by inactivity, opt-in LLM consolidation, pin +
    cron-reference exemption, audit ledger, recoverable archive, never auto-delete)** — prevents agent-created
    strategy/skill sprawl from bloating the catalog over a week-long soak (`/user-guide/features/curator`).
15. **Context-engine / memory-provider ABCs as single-select config-driven plugins with fail-open optional hooks
    (`select_context`, `on_turn_complete`, `sync_turn`, `on_pre_compress` fail-closed checkpoint) and a stable
    `message_uid` identity** — the clean seam for swapping QMX's own retrieval/RAG or compaction strategy under
    LangGraph without forking the loop (`/developer-guide/context-engine-plugin`, `/developer-guide/memory-provider-plugin`).

---

*UNVERIFIED notes:* exact SQLite column list is abridged in the docs (`SCHEMA_SQL` in
`hermes_state_common.py` is the authority, not reproduced on the page). The precise set of root-level HERMES_HOME
files is assembled across several pages, not given as one canonical tree anywhere; entries like
`knowledge/`/`preferences/` appear only in the export allow-list and their runtime role is not documented on the
read pages. Honcho/RetainDB/ByteRover per-provider internals beyond the plugin ABC were not read in full.
