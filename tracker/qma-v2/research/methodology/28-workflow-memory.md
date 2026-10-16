# 28 — Workflow memory: providers, QMA v2 today, and a MemoryPort for the engine

Written 2026-10-16 for ruling 49 (section G of `26-operator-rulings-and-alignment.md`). Ruling 57 (nothing waits for him) shapes the write and approval rules.

**How this was read.** The built-in browser opened one page (Hermes memory providers), but the pane is shared with another agent: `tabs_create` failed twice, and the shared tab was moved to another site mid-read. Every web source after that was read with firecrawl. No sign-in anywhere. Local files were read directly. Labels: **[web]** read today from the URL given, **[repo]** read in a QMX file, **[10-12]** from the 2026-10-12 memory research (`rebuild/research/2026-10-12-agent-system/memory.md`, every claim there carries its own URL), **[inferred]** my reasoning.

---

## 1. The short answer

- **The Alibaba project is ReMe ("Remember Me, Refine Me")**, now at `github.com/agentscope-ai/ReMe`. It started at ModelScope. `github.com/modelscope/MemoryScope` now redirects to the same repository (same repo id), so MemoryScope and ReMe are one project under two names. Apache-2.0, about 3.6k stars, v0.4.1.13. Its paper is the one that targets "don't redo what was done": it keeps a pool of experiences from past task runs, retrieves them before a new task, and prunes the ones that stop helping. [web]
- **QMA v2 today has almost no memory and no self-improvement.** The harness points Claude Code's auto memory at `<qmx_home>/agent-memory/<workspace>/` and loads the workspace's `CLAUDE.md` and `AGENTS.md` once. That is all. The `lessons` table was deleted in revision 3 (B53). A dormant refinement-proposal record in `qma-core` has its evaluation gates refused as "Deferred GAP-0074". [repo]
- **Proposal.** One `MemoryPort` in the engine with eight verbs. **The Library holds the memory rows as evidence; the memory provider is only a rebuildable recall index**, the same way `catalog.db` is an index over Library objects (Library AD-5). That one choice gives memory backups, remote access through the Hub, one writer per ref, and a clean answer to "memory or Library?".
- **"Already built" is a deterministic check first, a search second.** Each build step gets an intent key (a hash of kind, inputs and parameters). Before building, the engine asks the Library for an object with that key. Fuzzy recall from the provider only comes after.
- **Default provider: QMX built-in** (Library rows plus SQLite FTS5, no model call on read), with ReMe's experience schema and pruning rule copied in. **Pluggable alternatives: Hindsight first, ReMe second, Mem0 third.** A bake-off with real cheap models (ruling 51) decides whether a plug-in beats the built-in.
- **Self-improvement runs without him.** Lessons become a proposed change on an agent branch. The change is replayed against past runs (a fix set and a guard set). If it passes, a standing rule he sets once lets the scheduler run the improved version. `main` is not touched until he looks, and nothing waits for that.

---

## 2. Hermes Agent's memory setup [web]

Sources: `hermes-agent.nousresearch.com/docs/user-guide/features/memory`, `.../memory-providers`, `.../developer-guide/memory-provider-plugin`.

**Built-in memory (always on).**
- Two bounded files: `MEMORY.md` (2,200 characters, the agent's notes) and `USER.md` (1,375 characters, the user profile).
- One `memory` tool with `add`, `patch` and `remove`.
- **Frozen snapshot.** The files go into the system prompt once at session start and never change mid-session, which protects the prompt cache. Writes land on disk at once and show up next session.
- **Overflow is an error.** A write that would pass the cap fails, and the agent must consolidate in the same turn. QMX's engine already copied this rule (SOLUTION-DESIGN §11).
- Optional `write_approval`. In scripts and the background review, writes are staged for `/memory pending`.
- A background "self-improvement review" can run after a turn and save memory or update skills.
- Hermes says a fact needed on every run of a recurring task belongs in a skill, not in memory.

**Session search.** `session_search` runs SQLite FTS5 over every past conversation in `~/.hermes/state.db`. No model call, about 20 ms per query and 1 ms to scroll. It returns real messages, not summaries.

**Plug-in interface (`MemoryProvider`).**
- Required: `name`, `is_available()` (no network), `initialize(session_id, **kwargs)`, `get_tool_schemas()`, `handle_tool_call()`, `get_config_schema()`, `save_config()`.
- Optional hooks: `system_prompt_block()`, `prefetch(query)` before each call, `queue_prefetch()` after each turn, `sync_turn()` (must not block), `on_session_end()`, `on_pre_compress()`, `on_memory_write()` (mirrors built-in writes), `shutdown()`.
- Init kwargs carry scope: `hermes_home` (the profile), `cwd`, `agent_identity`, `gateway_session_key`, and `agent_context` = `primary | cron | subagent`. **Providers must skip automatic writes when the context is `cron` or `subagent`.**
- Discovery: bundled `plugins/memory/<name>/`, user `$HERMES_HOME/plugins/<name>/`, project `./.hermes/plugins/<name>/`, or a Python entry point. Each has `plugin.yaml`.
- **One external provider at a time.** It runs beside the built-in files, never instead of them.
- Everything handed to a provider passes through a secret scrub first.

**Scopes.** Hermes has no scope parameter in the interface. Scope comes from the profile (`hermes -p <name>` gets its own home, memory and sessions), and each provider maps the profile to its own unit: Honcho peers, Supermemory container tags such as `hermes-{identity}`, Hindsight `bank_id_template`.

**Providers listed today (it changed since 10-12).** Two ship bundled: **RetainDB** (cloud, $20/month, 10 tools, hybrid search, seven memory types) and **ByteRover** (local `brv` CLI, knowledge tree). From the plugin catalog: **Honcho** (cloud or self-host, peer modelling with dialectic reasoning), **OpenViking** (Volcengine/ByteDance, AGPL-3.0, filesystem-style tiers), **Mem0** (cloud, self-host server or in-process), **Hindsight** (cloud, embedded Postgres or a local server; graph plus reflect), **Holographic** (local SQLite FTS5 with trust scores), **Supermemory**, **Memori** (cloud). ReMe also ships a Hermes plugin (ReMe README).

**What QMX copies.** The frozen snapshot, error-on-overflow, no automatic writes from cron or sub-agents unless the engine says so, one external provider beside a built-in layer, scrub before handing anything over, and FTS5 session search with no model call.

---

## 3. Hindsight (vectorize-io/hindsight)

Sources: `github.com/vectorize-io/hindsight` [web]; details from `hindsight.vectorize.io/developer/*` [10-12].

- **Licence and size.** MIT, about 50.3k stars. [web]
- **Three verbs.** `retain` uses a model to pull facts, times, entities and relations out of text and stores them in canonical form. `recall` runs four searches in parallel (semantic, keyword, graph, temporal), fuses them with reciprocal rank fusion, reranks with a cross-encoder, and trims to a **token budget** rather than a top-k. `reflect` is an agent loop (up to 10 steps) that reasons over stored memories and cites only what it retrieved. [web; 10-12]
- **Memory banks.** A bank is an isolated store, one per user, agent or project, with no leakage across banks. Tags narrow scope inside a bank. A bank carries a mission, directives (hard rules) and a disposition (skepticism, literalism, empathy) that shape `reflect`. [web; 10-12]
- **Entity graph.** Facts link by entity, time, meaning and cause. Two time axes: when it happened and when it was learned. [10-12]
- **Mental models.** A standing question ("what are this workflow's known dead ends?"). Hindsight writes the answer and rewrites it in the background when the bank changes. Reading one is a database read with no model call. This maps well onto a frozen per-run snapshot. [web; 10-12]
- **Self-host.** Docker, `pip install hindsight-api`, or embedded `hindsight-all` with its own Postgres. Windows x86_64 is documented as supported. RAM: full API about 1.5–2 GB plus Postgres. [web; 10-12]
- **Any LLM.** Yes. 25+ providers, local ones (Ollama, LM Studio, llama.cpp), any OpenAI-compatible endpoint, LiteLLM, and existing subscriptions (`claude-code`, `openai-codex`) with no API key. That last option fits the "no Anthropic API spend" ruling, but check the terms before relying on it. [web]
- **API and SDKs.** REST, Python, TypeScript, Go, a CLI, and a built-in MCP endpoint per bank (`/mcp/{bank_id}/`). Integrations include Claude Code, Codex, LangGraph, OpenAI Agents SDK and n8n. [web]
- **Cost and evidence.** One independent study found Hindsight the most accurate but the most expensive to serve; on short histories it can cost more than keeping the transcript. Retain takes 0.5–2 s per batch; recall 100–600 ms. [10-12]

---

## 4. The Alibaba project: ReMe (formerly MemoryScope)

Sources: `github.com/agentscope-ai/ReMe`, `reme.agentscope.io/zh/{quick_start,auto_memory,auto_dream}`, `github.com/modelscope/MemoryScope` (redirects to ReMe), arXiv 2512.10696 (ACL Findings 2026), AgentScope Java memory docs. All [web].

**Why this is the one.** It is Alibaba's (ModelScope, then the AgentScope org), the name is a phrase someone would half-remember ("Remember Me"), MemoryScope folded into it, and AgentScope lists it as its memory layer (AgentScope Java ships `ReMeLongTermMemory` beside Mem0 and Alibaba's hosted Bailian memory). Other candidates checked: AgentScope's own memory module now delegates long-term memory to ReMe, Mem0 or Bailian, so it is a wrapper, not a separate project.

**Two layers in one project.**

1. **The research method (the paper; the 0.3 line advertised "Personal + Task + Tool" memory).** This is the "don't redo what was done" part.
   - An **experience** record has five fields: `when_to_use` (the scenario), `content` (the lesson or strategy), `keywords`, `confidence` (0–1) and `tools_used`.
   - **Distillation** reads finished runs three ways: what made successes work, what triggered failures, and what differed between a success and a failure on the same task. A model judge drops lessons that are not actionable. Near-duplicates are dropped by embedding similarity.
   - **Reuse.** Experiences are indexed by their `when_to_use` text. Before a new task, the top 5 are retrieved, optionally reranked, and rewritten into one short task-specific brief.
   - **Refinement.** Only lessons tied to a success are stored. On failure the agent reflects and retries (at most 3 times), and keeps the lesson only if the retry works. Each experience counts how often it was retrieved (`f`) and how often that retrieval ended in success (`u`). **After 5 retrievals, an experience whose `u/f` is 0.5 or less is deleted.**
   - Result: with ReMe, Qwen3-8B beat memoryless Qwen3-14B. On AppWorld, Qwen3-8B went from 14.97 to 24.70 average success.
2. **The current product (v0.4).** "Memory as file." Durable memory is plain Markdown with frontmatter and wikilinks. Indexes (BM25, optional vectors through FAISS or Alibaba's zvec) can be rebuilt.
   - **Auto Memory** turns each session into at most one daily card under `daily/YYYY-MM-DD/`, keeps the source transcript in `session/dialog/<id>.jsonl`, and records preferences, facts, decisions (including rejected options), current state and reusable experience.
   - **Auto Dream** runs on a cron (example `30 3 * * *`) or by hand. It scans the last 2 days of changed daily cards, pulls out at most 5 reusable units, and folds each into `digest/` as one of four moves: **create, corroborate, refine, correct**. Folders: `digest/procedure/` (methods, runbooks, executable experience), `digest/personal/`, `digest/wiki/`.
   - Access: Python API, CLI (`reme search | read | write`), HTTP and MCP on `127.0.0.1:2333`, a `SKILL.md` for any CLI agent, and plugins for Claude Code, Hermes, Codex and others.
   - Install: `pip install "reme-ai[core]"`, Python 3.11+. The model is set by environment: `LLM_BACKEND=openai` plus any OpenAI-compatible `LLM_BASE_URL` (the example uses DashScope's Qwen). Windows support is not stated.

**What QMX should take from ReMe even if it never installs it.** The experience schema, success-only storage with retry-to-confirm, the `u/f` pruning rule, and the four consolidation moves. These are small and can live in the built-in provider.

---

## 5. The rest, briefly (all [10-12] unless marked)

| System | One-line read |
|---|---|
| **Mem0** | Extracts fact memories scoped by `user_id`, `agent_id`, `app_id`, `run_id`. OSS is Apache-2.0 and runs in-process; graph memory is platform-only. Cloud $0–249/month. Cheap; accuracy swings with the backbone model. |
| **Letta** | Now a whole agent harness. Memory is files in a per-agent git repo; root files re-render into the system prompt every turn (breaks caching). Take the ideas (git-versioned memory, background "dreaming"), not the runtime. |
| **Zep / Graphiti** | Zep is cloud only now (Community Edition deprecated). Graphiti is Apache-2.0 and bi-temporal but needs Neo4j or FalkorDB, and scored 55–56% against 77–81% for Mem0 or plain RAG on LoCoMo in one independent study. |
| **LangGraph store / LangMem / Deep Agents** | What QMX lost (ruling 8): namespaced `BaseStore` (`(namespace, key, value)`, prefix search, optional vectors, SQLite or Postgres), memory as files under `/memories/`, episodic search over past threads, and a background consolidation agent on a cron. LangMem has had no release since 2025-10, so treat it as stalled. |
| **Anthropic memory tool** | `memory_20250818`: the model issues `view/create/str_replace/insert/delete/rename` on `/memories`, and your code stores it anywhere. Results arrive as tool results, so caching is safe. A good pattern for a QMX tool shape. |
| **Claude Code auto memory** | Per-project notes, first 200 lines or 25 KB loaded at session start; `CLAUDE.md` loaded at start. In QMA v2 the folder is moved per workspace with `autoMemoryDirectory` [repo]. |

### Comparison table

"Task/experience memory" means it stores what worked and what failed on past tasks and offers it before a new task. "Windows" means the server or library runs natively on Windows without WSL, as documented.

| Provider | Scopes | Task / experience memory | Graph | Self-host | Licence | Windows | Any LLM | Cost |
|---|---|---|---|---|---|---|---|---|
| **QMX built-in (proposed)** | run, workflow, home, operator (namespaces) | Yes, by design (`lesson`, `dead_end`, `built`, `negative_result` rows) | Library edges (typed, closed list) | Yes, it is QMX | QMX | Yes | No model on read; consolidation uses any engine model | Free; consolidation tokens only |
| **Hindsight** | Banks + tags; bank templates | Partial: "experience" fact type and mental models; no success/failure pruning | Yes (entity, time, cause) | Yes: Docker, pip, embedded Postgres | MIT | Yes (documented) | Yes: 25+, local, OpenAI-compatible, claude-code subscription | Free self-host; heaviest to run (1.5–2 GB RAM + Postgres, most tokens per retain) |
| **ReMe** | Workspace; folders `daily/`, `digest/{procedure,personal,wiki}`; user id in the AgentScope adapter | **Yes, strongest**: procedure digest, experience pool with utility pruning (paper) | Wikilinks only | Yes: pip, local service | Apache-2.0 | Not stated | OpenAI-compatible endpoint | Free; extraction and dream tokens |
| **Mem0 (OSS)** | `user_id`, `agent_id`, `app_id`, `run_id` | No (facts, not task outcomes) | Platform only | Yes: library or Docker server | Apache-2.0 | Library yes; fix the `/tmp/qdrant` default path | Yes (LiteLLM, Ollama, Anthropic) | Free OSS; cloud $0–249/month |
| **Honcho** | Workspace, peers, sessions, named scopes | No (user and agent modelling) | No | Yes: Docker, Postgres, Redis | AGPL-3.0 | Docker only | OpenAI-compatible | Free self-host; priciest in one agent benchmark |
| **Letta** | Per-agent memory repo | Background "dreaming" | No | Yes, as a whole harness | Apache-2.0 | Yes, as a harness | Yes | $0–20/month plus usage |
| **Zep / Graphiti** | User graphs / group ids | No | Yes (bi-temporal) | Zep no; Graphiti yes with a graph DB | Zep closed; Graphiti Apache-2.0 | Graphiti via Neo4j/FalkorDB | Yes | Zep credits from $125/month; Graphiti own infra |
| **LangGraph store / Deep Agents** | Namespace tuples | Only if you build it | No | Yes: SQLite, Postgres | MIT | Yes | Yes | Free |
| **Anthropic memory tool** | One `/memories` tree per binding you choose | Only if the model writes it | No | You store it | API feature | Yes | Claude only | Model tokens |
| **Claude Code auto memory** | Per workspace folder | Free-form notes only | No | Local files | Claude Code | Yes | Claude Code providers | Free |
| **Hermes built-in** | Per profile | Free-form notes; skills via background review | No | Local files | MIT (Hermes, unverified) | Hermes runs on Windows | Any | Free |
| **RetainDB, Memori, Supermemory** | Cloud projects / containers | No | Supermemory yes | No (Supermemory's server is a closed binary) | Closed | n/a | n/a | $20/month or usage credits |

---

## 6. What QMA v2 does today

**On branch `qma/hp17` (code)** [repo]:
- `qma-harness/src/qma/harness/home.py:148-153`: `memory_dir(workspace)` returns `<qmx_home>/agent-memory/<slug>-<hash>/`. `home.py:442` passes it as `autoMemoryDirectory` on every launch. One memory per workspace, shared by every provider.
- `launch.py:315-321`: the system prompt append is `QMX.md`, then the workspace root's `CLAUDE.md` and `AGENTS.md`, read once. `setting_sources=[]` keeps the operator's own `~/.claude` out.
- `SIGNOFF.md:145-148`: `/memory`, `#` and `/init` edit files that apply only at the next launch.
- The old daemon (`qma-daemon/.../native_claude.py:264,276`) **turned auto memory off** (`autoMemoryEnabled: False`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`). It is scheduled for deletion.
- `qma-core/src/qma/core/ports/refinement.py`: a `RefinementProposal` record and a validate → verify → review → stage → approve → apply pipeline vocabulary (CT-50, AD-22). The evaluation gates return a typed refusal: "Deferred GAP-0074". It also refuses model self-judgement as a gate. `qma-core` stays only for its `barriers` package (DELETION-PLAN line 313), so this file is dormant.

**In the plan** [repo]:
- `research/one-engine/architect/DESIGN.md` §3.1 and open question 20: auto memory is moved out of the protected Claude homes; whether `autoMemoryDirectory` takes effect from `--settings` is checked by probes S7 and S13.
- BACKLOG **B40** (memory bake-off: SDK memory by default, pluggable Hermes-style layer, test Hindsight, Mem0, LangChain memory and plain files), **B41** (self-improvement: lessons so a mistake is not repeated; traces and evals), **B51** (provider interface research), **B53** (designs deleted by revisions).
- **B53, the deleted `lessons` table** (revision 1, `git show 00a1d1b5:tracker/qma-v2/ARCHITECTURE.md` line 601): "a `lessons` table of proposals, a weekly mining job, a skill draft as a new plugin version, an eval gate against 'no skill' on `FakeAdapter`, an approval row before activation, undo by the previous plugin hash". Revision 3 dropped it with the runner.
- Engine **AD-18** and SOLUTION-DESIGN **§11**: scopes `run | workflow | home | operator`, one writer each, hard caps that error (workflow 200 lines, home 400, operator 200), tags `lesson | dead_end | do_not_retry | negative_result`, `home` and `operator` written only by a `consolidation` subworkflow, and `dead_end` rows read by the builder and by `loop` stop rules.
- Wayfinder tickets `memory-candidates-facts` (AFK, this file answers it) and `memory-scopes-and-lessons` (HITL).

**Gaps found while reading.**
1. SOLUTION-DESIGN §11 stores `home` and `operator` memory as "Library kind `memory` rows", but the Library's closed kind roster (Library AD-3) has no `memory` kind. One of the two must change. Section 7.4 proposes the fix.
2. The `workflow` scope is two stores: harness auto memory (free-form, written by the agent) and tagged Library rows. Nothing says which wins, and auto memory has no tags, no cap enforced by QMX and no one-writer rule when two runs share a workspace. `max_concurrent: 1` hides this for agent workflows but not for copilots.
3. Nothing answers "has another workflow already built this?". AD-18 is scoped per workflow; cross-workflow reuse is not designed.
4. Library OPEN-6 makes `skill`, `workflow` and `methodology` merges manual. With ruling 57, an improved workflow would sit in a queue forever. Section 8 works around this without touching `main`.

---

## 7. Proposed `MemoryPort`

### 7.1 Principles

1. **Evidence in the Library, recall in the provider.** Every memory row is a Library object. The provider (built-in FTS5, Hindsight, ReMe, Mem0) is an index built from those objects and can be wiped and rebuilt. This is Library AD-5 applied to memory. It also means memory replicates to the server and bucket, and remote runs reach it through the Hub with no extra design.
2. **Memory points; the Library holds.** A row says "a 20-year EURUSD H1 dataset was already built, see Library object `X`". It never copies the dataset, the metrics or the code. Numbers that move money are never memory.
3. **One writer per scope.** Each scope maps to a Library ref namespace that one principal owns (Library AD-7).
4. **Deterministic before fuzzy.** "Already built" and "known dead end" are exact lookups first. Model-based recall only adds candidates.
5. **Memory is data, never instructions.** Recalled text reaches an agent as a tool result or a fenced block in the newest user message, never as system text.
6. **Frozen per run.** A run reads a snapshot at start and never sees it change mid-run (Hermes rule, prompt cache).

### 7.2 Scopes and their one writer

| Scope | Library ref namespace (proposed) | Writer | Readers | Cap |
|---|---|---|---|---|
| `run` | `refs/runs/<run_id>` (rows inside the `workflow-run` object) | the run (`run:<run_id>`) | that run | budget only |
| `workflow` | `refs/memory/wf/<workflow_item>` | the workflow's `consolidate` step at run end (as `run:<run_id>`, via a per-workflow ref the engine owns) | later runs of that workflow | 200 lines in the snapshot; unlimited rows behind recall |
| `home` | `refs/memory/home/<home>` | the `consolidation` subworkflow of that home | copilots and workflows of that home | 400 lines |
| `operator` | `refs/memory/operator` | the `consolidation` subworkflow, operator namespace | everything | 200 lines |
| `global built-registry` | no ref; it is the Library's own `produced-by` edges plus an `intent_key` annotation | whoever produced the object | every workflow | n/a |

The caps apply to the **snapshot** loaded at run start (the hot set). Rows behind recall are unbounded but pruned (section 8.4). This keeps the AD-18 rule (overflow errors, then consolidate) and still lets a long-lived workflow keep hundreds of dead ends.

Writes from `cron` and sub-agent contexts follow Hermes: an agent inside a scheduled run or a sub-agent never writes `home` or `operator` directly. It writes `run` rows, and the consolidation step decides what rises.

### 7.3 Verbs

```text
MemoryPort
  snapshot(scopes, budget_tokens)        -> Snapshot{text, version, row_ids}   # frozen at run start
  recall(query, scopes, tags?, budget)   -> [Hit{row_id, text, tag, refs, score, provenance}]
  check_built(intent_key)                -> [LibraryObjectId]                  # exact, no model
  check_dead_end(intent_key | query)     -> [Hit]                              # exact first, then recall
  note(row, scope=run)                   -> row_id                             # any node, run scope only
  consolidate(run_id, into_scope)        -> {added, merged, corrected, pruned} # consolidation step only
  feedback(row_ids, outcome)             -> ()                                 # bumps f and u (ReMe rule)
  search_runs(query, workflow?)          -> [RunHit]                           # FTS5 over run summaries, no model
```

- `note` is the only write an ordinary node or agent has. It always lands in `run` scope.
- `consolidate` is the only path into `workflow`, `home` and `operator`. It applies ReMe's four moves (create, corroborate, refine, correct) and writes Library objects on the scope's ref.
- `feedback` is called by the engine, not the agent: when a run ends, every row that was in its snapshot or recall results gets `f += 1`, and `u += 1` if the run passed its checks.
- `search_runs` is Hermes's `session_search` for workflows: FTS5 over `workflow-run` summaries and transcripts. AD-18's deferral to "a Library query the Library agent designs" can use this shape.
- Agents see three tools: `memory_recall`, `memory_note`, `memory_check` (built and dead-end). Tools are declared from the first turn so the tool list never changes mid-run.

### 7.4 The row

Add one kind to the Library roster: **`memory-row`** (fixing gap 1). Fields:

```text
memory-row
  identity (hashed): scope, tag, intent_key?, when_to_use, content, refs[]
  annotations:       keywords[], confidence, f (retrieved), u (useful), source_run_ids[], learned_at, occurred_at
  tag ∈ { built, lesson, dead_end, do_not_retry, negative_result, procedure, preference }
  relations: mentions -> any Library object; derived-from -> workflow-run; replaces -> older memory-row
```

- `when_to_use`, `content`, `keywords`, `confidence` come straight from ReMe's experience record. `tools_used` is dropped; `refs` carries Library ids instead.
- `f` and `u` are annotations, so updating them mints no new version (Library AD-2).
- A correction is a new row with a `replaces` edge. Nothing is deleted (Library AD-6); pruning archives.

### 7.5 What goes where

| Thing | Memory (`memory-row`) | Library (other kinds) | Neither |
|---|---|---|---|
| A dataset, backtest, bot, model, report, code | A `built` row: "intent K was built, see `X`" (only when the intent key alone is not enough) | The object itself | |
| Why an idea failed | `dead_end` row with `refs` to the run and result | The `backtest-result` and `workflow-run` | |
| How to do a recurring step | `procedure` row while it is young | A `skill` or `methodology` once it is proven (section 8) | |
| Operator preferences | `preference` row, `operator` scope | | |
| Risk limits, sizing, credentials | | Config and governed docs | Never memory |
| Raw transcripts and logs | | Blobs on the `workflow-run` (Library AD-13) | |
| Live execution state | | | Engine SQLite (Library AD-15) |

### 7.6 "Already built": the check

1. Each build-type node (a `library` put, a data pull, a backtest, an agent step that declares `produces: <kind>`) computes an **intent key**: `fp1(kind, canonical inputs (Library object ids), canonical parameters, code object id)`. Deterministic, no model.
2. The object it produces carries `intent_key` as an annotation. The Library already dedupes identical content (AD-2); the intent key also catches "same request, different bytes" (for example a backtest re-run with a new timestamp in the output).
3. Before running, the engine calls `check_built(intent_key)`. A hit on an `active` object whose producing run `passed` means **skip and link**: the node returns the existing object and records a `consumed` edge. A hit on a `dead_end` row means **stop, or run only if the node says `retry_dead_ends: true`**.
4. Only if the exact check misses does an agent step get `recall("build <description>")`, which may surface near matches ("someone built H4, you asked for H1"). The agent decides.
5. This is a node option, default on for script nodes and offered to agent steps as `memory_check`. A workflow can opt out with `reuse: never` (for example a nightly refresh).

---

## 8. Self-improvement loop (no human in the path)

### 8.1 The loop

```text
runs ──> note() rows ──> consolidate ──> lessons pool
                                            │
                    nightly "improve" workflow (per workflow or per home)
                                            │
                         proposal on an agent branch (Library)
                                            │
                  replay: fix set (past failures) + guard set (past passes)
                                            │
                        gate passes? ── no ──> archive proposal + dead_end row
                                            │ yes
                        champion pointer moves; scheduler runs it
                                            │
                     live results feed feedback() ──> keep or roll back
```

### 8.2 Steps

1. **Collect.** Every run writes `run` rows (`note`) and the engine records outcomes. `consolidate` at run end lifts lessons into `workflow` scope with ReMe's four moves.
2. **Propose.** A scheduled `improve` workflow (itself an ordinary QMX workflow) reads the lessons pool, the last N runs and their failures, and drafts **one** change: a prompt or brief edit, a skill, a parameter default, or a node added to the definition. The draft is a new object on `refs/agents/<session>/<workflow_item>`. It names the lessons it acts on.
3. **Test against past runs.** The engine replays the proposal on a **fix set** (recent failed runs it claims to fix) and a **guard set** (recent passed runs it must not break), with pinned inputs and the same models. This is the 13-failure-and-rlm takeaway ("validate any fix against a fix set and a guard set") and B53's "eval gate against no-skill". Scoring is deterministic where it can be (checks, schema, numbers); a model judge is allowed only as a tiebreak, and never the same model that wrote the proposal (`refinement.py` already refuses self-judgement).
4. **Adopt.** If the fix set improves and the guard set holds, the proposal becomes the workflow's **champion** (see 8.3). The `tested-by` edge points at the replay runs (Library AD-15 "tested" rule).
5. **Watch and roll back.** Live runs of the champion feed `feedback()`. If its pass rate over the next K runs falls below the old version's, the champion pointer moves back automatically and a `dead_end` row records why.
6. **Promote knowledge.** A `procedure` row that has `f ≥ 5` and `u/f > 0.8` is drafted into a `skill` object by the same `improve` workflow. Rows with `f ≥ 5` and `u/f ≤ 0.5` are archived (ReMe rule).

### 8.3 Who approves, given ruling 57

- **Nobody, per change.** The gate in step 3 is the approval. This matches ruling 57.
- **He approves once, up front, per workflow or per home:** a standing rule `self_improve: auto | propose_only | off`, default `auto` for workflows he created or enabled. Library PLAIN-WORDS already allows "you (or a rule you set) merge it".
- **`main` is not touched.** The champion is a ref the engine owns (proposed: `refs/champions/<workflow_item>`). The scheduler runs the champion when the rule says `auto`. `main` stays the last version he accepted. This works around OPEN-6's "workflow merges are manual" without breaking it: nothing waits, and nothing he trusts changes silently.
- **Hard limits that no rule lifts:** a proposal may not edit money-path tools, risk or sizing settings, credentials, or the deny-list (`refinement.py`'s `refuse_money_path_edit_target` already exists). It may not raise its own budget. It may not touch another workflow.
- **What he sees later:** a review card per champion change (what changed, which lessons, replay scores, live results since). Merging it to `main` is optional tidying, not a gate.

---

## 9. Recommended default provider and the alternatives

**Default: the QMX built-in provider.**
- Rows are Library objects. Recall is SQLite FTS5 over them plus Library edges, with optional `sqlite-vec` reordering (Library AD-8 already plans this index). No model on read.
- `snapshot` renders the hot set per scope within the caps. `consolidate` and `improve` are engine workflows that use whatever model the workflow is configured with (Claude through the harness, or a cheap model; ruling 51 says real models).
- ReMe's schema, success-only storage and `u/f` pruning are built in.
- Why default: zero new services on his PC or server, nothing to keep in sync, same backups and Hub as everything else, and independent studies keep finding plain retrieval ties dedicated memory products [10-12].

**Plug-in 1: Hindsight.** The best general recall engine available that is MIT, runs on Windows, has a graph, any LLM, and an MCP endpoint. Use one bank per scope (`qmx-wf-<id>`, `qmx-home-<home>`, `qmx-operator`), feed it from Library `memory-row` objects (retain in `chunks` mode to avoid an extraction call, or `concise` mode if the bake-off shows gains), and use mental models as the snapshot. Run it on his server, not the PC (RAM).

**Plug-in 2: ReMe.** Best fit for procedure and experience memory, and it is file-native, which sits well beside a git-shaped Library. Point its workspace at a checkout of the memory refs; its Auto Dream can stand in for QMX's `consolidate`. Needs a Windows check and an OpenAI-compatible model endpoint (OpenRouter is fine for tests).

**Plug-in 3: Mem0 OSS.** Cheapest fact memory with clean `agent_id`/`run_id` scoping. Weak on task outcomes.

**Not recommended:** Honcho (AGPL, Docker, user modelling not task memory), Zep (no self-host), Graphiti (graph database to run), Letta (a harness), Supermemory, RetainDB, Memori (closed or cloud only).

**Adapter contract** (Hermes-shaped, fed from the Library):

```text
MemoryProvider
  name, is_available()                     # no network
  open(config) / close()
  index(rows: [memory-row])                # called by the Library watcher; idempotent by object id
  forget(row_ids)                          # on archive
  recall(query, scopes, tags, budget)      # returns row ids + scores; text comes from the Library
  snapshot(scopes, budget)                 # optional; built-in renders one if missing
  reflect(question, scopes)                # optional (Hindsight)
  rebuild(all_rows)                        # wipe and reindex from the Library
```

One active plug-in per scope binding, always beside the built-in index (Hermes rule). Because a provider only ever returns row ids, swapping providers loses nothing.

**Bake-off (B40).** Run the 10-12 plan with these changes: candidates are built-in, Hindsight, ReMe (Mem0 optional); add an "already built" task family (repeat a build request across two workflows; must skip) and a dead-end family (a known failing idea; must not retry); use real cheap models through the existing providers. Ship the built-in unless a plug-in wins by 5 points on action tasks with zero leaks.

---

## 10. Open questions, each with a recommendation

1. **Where does memory evidence live: Library or provider?** Recommend the Library (`memory-row` kind) with providers as indexes. Otherwise memory needs its own backups, Hub route and writer rules.
2. **Add `memory-row` to the Library roster, or reuse `note` with tags?** Recommend a new kind. `note` is free text for people; memory rows need `f`/`u` annotations, a `scope` field and a closed tag list.
3. **Does harness auto memory stay as the `workflow` scope?** Recommend: keep it on for copilots (people like it), but for workflow agents treat it as `run`-scope scratch. At run end `consolidate` reads it and writes proper rows; the folder is cleared per run. This fixes gap 2.
4. **How strict is the intent key?** Recommend exact match on inputs, parameters and code object id, with a per-node `reuse: exact | similar | never` (default `exact`). `similar` lets an agent accept a near match; it is never automatic.
5. **Who owns `refs/champions/*`?** Recommend the `hub` or local engine principal that runs the workflow's schedule, recorded as a new owner line in Library AD-7. Needs the Library agent's sign-off.
6. **Does a champion ever reach `main` without him?** Recommend no. It runs as champion indefinitely; `main` moves by his click or a standing rule he writes per workflow. This respects OPEN-6 and ruling 57 together.
7. **What model scores the replay gate?** Recommend deterministic checks first, then a cheap judge from a different provider than the proposer, as ruling 51 allows (OpenRouter is fine for tests).
8. **Cross-workflow lessons: who lifts a lesson from one workflow to its home?** Recommend the home's nightly `consolidation` run, only for rows corroborated by two or more workflows or with `u/f > 0.8` after 5 uses.
9. **Hindsight's `claude-code` subscription provider: allowed?** Recommend not relying on it until checked against the harness's sign-in rules; use a cheap OpenAI-compatible model for retain and reflect.
10. **Does the built-in need vectors on day one?** Recommend no. FTS5 plus Library edges first; turn on `sqlite-vec` reordering only if the bake-off shows misses that words cannot catch.
11. **Where do providers run?** Recommend his server beside the Hub (ruling 55, 56). The PC keeps only the built-in FTS5 index, which rebuilds from replicated objects.
12. **Should the dormant `qma-core` refinement pipeline be revived?** Recommend reusing its refusal rules (money-path targets, self-judgement, runtime instance edits) as the proposal guard in section 8.3, and dropping its manual approve stage.

---

## Sources

Web (read 2026-10-16): `hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers`, `.../features/memory`, `.../developer-guide/memory-provider-plugin`; `github.com/vectorize-io/hindsight`; `github.com/agentscope-ai/ReMe`; `github.com/modelscope/MemoryScope` (redirects to ReMe); `reme.agentscope.io/zh/quick_start`, `/zh/auto_memory`, `/zh/auto_dream`; `arxiv.org/abs/2512.10696` and `/html/2512.10696v2`; `aclanthology.org/2026.findings-acl.829`; `java.agentscope.io/v1/en/docs/task/memory`.

Repo: `tracker/qma-v2/architecture/workflow-engine/ARCHITECTURE-SPINE.md` AD-18; `SOLUTION-DESIGN.md` §11; `architecture/library-and-data/ARCHITECTURE-SPINE.md` AD-2..AD-15, `PLAIN-WORDS.md`, `OPEN-DECISIONS.md` OPEN-6; `research/one-engine/architect/DESIGN.md` §3.1, OQ 20; `BACKLOG.md` B40, B41, B51, B53; `research/methodology/05-qmx-today.md` (B53 section), `13-failure-and-rlm.md`, `25-hermes-n8n-loadbalancer.md` §1.5; `wayfinder/tickets/memory-*.md`; `rebuild/research/2026-10-12-agent-system/memory.md`; branch `qma/hp17`: `qma-harness/src/qma/harness/{home.py,launch.py}`, `qma-harness/docs/SIGNOFF.md`, `qma-core/src/qma/core/ports/refinement.py`, `qma-daemon/.../native_claude.py`.
