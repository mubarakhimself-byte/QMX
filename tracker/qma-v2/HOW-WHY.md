---
label: qma-v2:how-why
created: 2026-10-12
requirements: tracker/qma-v2/PRD.md (148 FRs, 81 WED, 39 NFRs)
builds-on: tracker/agent-system/research/24-how-why-integration-surface.md (not repeated here), 27-requirements-from-audit-session.md §4 (port facts)
source: origin/rebuild/base @ bc32b46a (PR #67). The only change since 24's snapshot 4fa38ffe is the deletion of qma-wire attach (5 files, -525 lines). Every new package is byte-identical, so 24's citations still hold.
method: pstack /how then /why, run in one pass by one agent with no sub-agents (brief rule). Planning only. Nothing committed.
---

# QMA v2: how the code stands today, and why it has that shape

## Summary in plain words

1. Nothing on `rebuild/base` runs a QMA v2 agent today. The agent core is LangChain, LangGraph and Deep Agents, and the PRD drops all three.
2. No line of agent code has ever run against a real model. Every live smoke was deferred (PR #31, #33, #35, #44, #46 bodies). Everything "works" only with fake models.
3. GitHub Actions has never produced a run for this branch (PR #46 body; `gh run list` is empty today). `just ci` passes only on the laptop.
4. The platform under the agents is real and reusable: `qmx-control` (sessions, typed blocks, SSE, 52 operations on two doors), the mini-app runtime, the road to live, artifacts, and the remote-run lane.
5. Of the 81 WED requirements, 14 are fully served by code that runs today and 24 are partly served. 18 exist only as fake-tested LangChain code that must be rebuilt, 3 are stubs, and 22 have no code at all (tally of the §2 rows).
6. The four biggest blockers are the same as in 24: no `Engine` contract, no turn route, no approvals table, and no workflow runner or store.
7. Three facts are new since 24. Background tasks, cancellers and admission approvals live only in process memory, so nothing survives a host restart (FR-014, FR-104).
8. An agent can declare its own app trust. `apps_create` takes `trust` as a tool argument, and the fake Copilot test passes `"reviewed"` itself (`agents/../tests/test_copilot.py:92`).
9. The T1 laptop tier refuses agent-written apps outright (`apps/supervisor.py:139-144`). That collides with FR-072 plus FR-075 (laptop, no Docker) until an approval record replaces the refusal.
10. The router cannot hold account rows. Providers are a closed `Literal` of five names, and the `providers` settings section is read only for Litestream replicas.
11. The only Claude Agent SDK recipe is `native_claude.py`, still in `qma-daemon`. Its isolation and subscription checks are worth keeping. Its "no tools, no skills, no sub-agents, no plugins" lockdown contradicts the PRD.
12. `openai-agents` is not in any lockfile. `claude-agent-sdk 0.2.163` is, through the old daemon.
13. The import cycle control → apps → agents → tools → control still stands. It must break before an engine package lands.
14. "money-path-scan" in CI is a binary-float scanner for quant code. It does not check agent tools. FR-102 needs its own test.
15. The why record mostly survives. About two thirds of the old reasons stay as RESPECT constraints. What drops is LangChain itself, CLIProxy, modes, the owned VPS, Docker-by-default for agent code, and the "lock everything down" Claude recipe.

## Path keys and labels

- `ctl/` = `qmx-agents/packages/qmx-control/src/qmx_control/`. `apps/` = `.../qmx-apps/src/qmx_apps/`. `agents/` = `.../qmx-agents/src/qmx_agents/`. `tools/` = `.../qmx-tools/src/qmx_tools/`. `remote/` = `.../qmx-remote/src/qmx_remote/`. `daemon/` = `.../qma-daemon/src/qma/daemon/request_runtime/`. Other paths are from the repo root.
- **RUNS** means real code with real dependencies, tested without a model (SQLite, subprocesses, MCP stdio). **FAKE** means the behaviour is proven only with fake models or stub SDKs. **STUB** means a 501 route or a placeholder file. **MISSING** means no code.
- **Neutral** means plain Python or Pydantic that any engine can call. **Bound** means it exists because of a LangChain, LangGraph or Deep Agents primitive and must be replaced.

## 1. Area table

| PRD area | State today | Reusable as is | Main blocker |
|---|---|---|---|
| 4.1 Copilot and organogram | FAKE (LangChain copilot), sessions RUN | `sessions` table, `origin`, `parent_id`, typed blocks, block mapping rules | No plugin unit; sessions have no target or status; plan/do mode still in code |
| 4.2 Turn host, sessions, errands | FAKE (`stream_turn`, `start_task`), no route | `sessions_append`, `record_work`, child sessions | No turn route; tasks and cancellers live in memory, nothing resumes |
| 4.3 Engines | MISSING (reference recipe only) | `AgentSpec` schema, `native_claude.py` isolation and auth checks | No `Engine` contract; no SDK fakes; `openai-agents` not locked |
| 4.4 Plugins and skills | STUB (placeholder skills) | `~/.qmx` home, skill folder format | No plugin format or loader; old `qmx-agents/plugins/` name collides |
| 4.5 Router, accounts, usage | FAKE (tier router via LangChain) | override chain, `model_selector`, `credential()`, journal usage, RunIndex cost sum | Providers are a closed Literal; no accounts, no stickiness, no limits, no USD |
| 4.6 Workflows | `workflow.v1` RUNS; compiler FAKE; API STUB | `models.py`, schema, validation, pointer/template helpers, status set | `workflows_*` return 501; no store; LangGraph executor; no hash pin, retries or idempotency |
| 4.7 Triggers and scheduler | MISSING (app interval schedule only) | `Schedule.interval_seconds`, backup schedule | No QMX scheduler (all NEXT) |
| 4.8 Mini apps | RUNS (runtime, road, artifacts); copilot build FAKE | supervisor, manifest, hash, road, artifacts, breaker, Docker tier | T1 refuses agent apps; trust is caller-declared; agent apps embed `qmx_agents` |
| 4.9 Sub-agents | FAKE (Deep Agents `task`) | spec refs, cycle check, child sessions in the log | Per-request model overrides sub-agents; no depth cap outside workflows |
| 4.10 Memory | FAKE (LangGraph SqliteStore + middleware) | `MemoryProvider` protocol, scopes, namespaces, approval and cap rules | No SDK default memory; store and hooks are LangGraph |
| 4.11 Context, prompts, compaction | FAKE (Deep Agents defaults) | 10-line custom `copilot.md` idea, result offload idea | No cache check; summariser is Deep Agents; prompt still names plan tier |
| 4.12 Approvals, hooks, money path | money path RUNS (neutral core); hooks FAKE | `check_descriptor`, act list, journal, admission rule, app hook rules | Policy sits in LangChain middleware; approvals not durable; no two-engine test |
| 4.13 Placement, off-machine | RUNS with fake and stub providers | bundle, manifest, hashes, bucket flush, verified fetch, resume, `runs/<id>` branch | Default is an owned VPS; worker runs LangGraph; Claude sign-in on Linux unverified |
| 4.14 Observability, DevOps | RUN index RUNS; traces MISSING | `runs.db` over journals, supervisor logs and heartbeat | No trace store; no four axes; no watchdog |
| 4.15 UI contract and events | RUNS (blocks, SSE, two doors) | `SessionBlock`, `events`, `OPERATIONS`, `not_implemented` | No delta channel; block list lacks usage and cursor kinds; sessions lack status |
| 4.16 Tools and reach | RUNS (13 domain functions, FastMCP) | `domain_functions`, four FastMCP servers, Library seam module | No capability registry, no tool lint, no baseline shell/web/video set |
| 4.17 Concurrency, self-improvement | MISSING | none | No RAM cap or session counter |
| 4.18 Shipping, docs, platform | process only | `rebuild/base` PR flow, `just ci` | GitHub Actions never ran; Q7 says ship into `rebuild/base` |

## 2. Per-area detail

Each WED FR gets one row. NEXT and LATER FRs get one line per area where code already exists.

### 4.1 Copilot and organogram

**How.** `agents/copilot.py:54-95` builds the Copilot as a Deep Agent from `agents/agents/copilot.yaml` with the `qmx-control`, data, backtest, research and broker MCP servers. `stream_turn` (`copilot.py:98-213`) maps LangGraph updates onto typed blocks. Sessions are a JSON row of `{id, title, origin, parent_id}` (`ctl/service.py:47-51`, `300-313`). The proof is `agents/../tests/test_copilot.py` (436 lines, fake models). Modes survive in code: `mode: Literal["plan","do"]` and the tier switch at `copilot.py:105`, `112`, and the prompt line "Plan with the reasoning tier" (`agents/copilot.md:4`).

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-001 general copilot | FAKE | `copilot.py:54-95`, `copilot.yaml:1-16` | Replace builder; keep block mapping rules `copilot.py:123-212` | No engine, no turn route |
| FR-002 Lab/Portfolio seats as plugins | MISSING | only `copilot.yaml` plus four sub-agent YAMLs | YAMLs become plugin seeds | No plugin unit; `qmx-agents/plugins/` holds old desk packs (24 risk 13) |
| FR-003 session records surface and target | partial RUNS | `origin` field `service.py:50` | Keep `origin` as surface | No `target` (app, version, account, environment) field |
| FR-004 list sessions from every surface | RUNS | `sessions_list` `service.py:315-322` | Reuse | Add surface filter and status |
| FR-005 Lab reaches Portfolio | RUNS (tools exist) | `portfolio_proposals` `service.py:296-298`; broker read tools `spec.py:278-290` | Reuse; Portfolio write stays `propose_order` | Needs plugin tool lists |
| FR-006 no modes | STUB to remove | `copilot.py:105-113`; `copilot.md:4`; COPILOT.md §2 withdrawn; P24 on hold | Delete in the rewrite | None; subtraction only |

**Neutral.** The session row, `origin`, `parent_id`, the block kinds and the mapping rules (todos to `plan`, delegation to `agents`, interrupts to `permission`, artifact results to `artifact`).
**Bound.** `build_copilot`, `stream_turn`'s LangGraph `astream` loop, `AppSandbox` (a Deep Agents backend).
**Why.** Y11 and Y44 (RESPECT) keep the two doors and the block contract. Y18 (DROP by C-10) removes the mode code. Y03 (DROP by C-01) removes the Deep Agent copilot.

NEXT. FR-008 has a seed in `hooks.py` (the app-edit guard idea) but no app-use seat. FR-010 maps to the `artifact` block kind (`service.py:63`). FR-011 has no attachment path.

### 4.2 Turn host, sessions and errands

**How.** A turn exists only inside `stream_turn`, called by `scripts/live/copilot_build_app.py` and by `tasks.py:136`. `POST /api/sessions/{id}/blocks` stores a row and starts nothing (`service.py:324-335`). Background tasks are `asyncio.create_task` inside the agent process (`tasks.py:42`). Their cancel callbacks sit in `ControlService._cancellers`, a dict (`service.py:106`, `455`). A host restart loses both. `_cancel` then answers 501 (`service.py:621-623`).

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-013 turn host, no UI | FAKE | `stream_turn` `copilot.py:98-213` | Keep the append-blocks pattern; replace the LangGraph loop | No turn route, no cancel-turn route |
| FR-014 errands, parallel, resumable, linked | MISSING | child-session pattern `tasks.py:38-40` | Reuse child sessions and `record_work` | Tasks and cancellers are in memory; no errand record |
| FR-015 start/check/cancel/list tasks | FAKE | `tasks.py:31-89` (`@tool`, `AsyncSqliteSaver`) | Keep the four verbs and ownership check `tasks.py:91-93` | Bound to LangChain tools and LangGraph saver |

**Neutral.** `record_work` with its status vocabulary (`service.py:443-471`), child sessions, the ownership rule for tasks.
**Bound.** `@tool` wrappers, `AsyncSqliteSaver` per task (`tasks.py:126-139`), `graph.aget_state` to decide `needs_you`.
**Why.** Y13 and Y21 (RESPECT) say QMX owns the turn host and job runner. Y20 (RESPECT) says runs resume by id and never merge. Nothing in the record explains why tasks were left in memory; the inferred reason is that P15 only needed one live script process.

NEXT. FR-016 and FR-017 have only the journal (`agents/guards/journal.py:36-127`). FR-018's "assumptions card" is written down in COPILOT.md §6 and never built.

### 4.3 Engines

**How.** No `Engine` interface exists in any new package (git grep for `claude_agent_sdk` and `agents import` in `qmx-*` is empty). The single Claude Agent SDK recipe is `daemon/native_claude.py` (435 lines). It pins SDK 0.2.163 and CLI 2.1.286 (`:40-41`). It refuses any `ANTHROPIC_*` variable (`:97-102`), checks `claude auth status` for `authMethod == "claude.ai"` in a dedicated home (`:116-145`), and refuses a home holding settings, hooks, plugins, agents or skills (`:149-160`). Its options are `tools=[]`, `skills=[]`, `agents={}`, `plugins=[]`, `setting_sources=[]`, `strict_mcp_config`, `disableAllHooks`, `max_turns=8`, an in-process `create_sdk_mcp_server`, and a `PreToolUse` deny for anything outside the allow-list (`:222-280`). It refuses sub-agent output and background tasks (`:309-345`). `native_codex.py` drives the Codex CLI through `openai_codex` (`:19-20`, `81`). The lock `qmx-agents/uv.lock` holds `claude-agent-sdk 0.2.163` and `openai-codex 0.160.0`, and no `openai-agents`.

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-020 one Engine contract, ten verbs | MISSING | none | `native_claude` start/resume/events/cancel/close shape is a seed | Contract and both fakes must come first (NFR-027) |
| FR-021 Agent SDK only, no session per step, no codex | MISSING | `native_claude.py` reference | Recipe kept as reference; `native_codex.py` dropped (K-15) | Session cap and reuse logic absent |
| FR-022 Max plan only, no token handling | reference only | `native_claude.py:97-160` | RESPECT the preflight wholesale | The SDK spawns the `claude` binary; sign-in is the operator's |
| FR-023 GPT via SIWC or "unavailable" | MISSING | none | none | A-01 feasibility unknown |
| FR-024 any provider by base URL plus key | partial FAKE | `router.py:167-192` (`init_chat_model`, OpenAI-compatible `base_url`) | Keep the base-URL idea | `Provider` is a closed Literal (`router.py:30`, `48`) |
| FR-025 capability built once, mapped to both | MISSING | money path and admission are neutral (see 4.12) | Neutral rules are the first such capabilities | No contract layer to map onto |
| FR-026 per-agent engine and model chain, recorded | FAKE | `RunContext` `router.py:125-141`; `resolve_model` `:194-203`; journal records model | Keep chain, add engine | `request_model` overrides every level (`:199-200`) |
| FR-028 engine-neutral AgentSpec | partial RUNS | `AgentSpec` `spec.py:108-126`; `load_spec` `:129-141` | Keep schema; replace `_build` `:246-499` | No `engine` field; `interrupt_on` and `Permissions.rules()` emit Deep Agents types |

**Neutral.** `AgentSpec` fields, `load_spec` path resolution, `mcp_configuration` with its Firecrawl HTTPS and `qmx/*` rules (`spec.py:197-243`), the native recipe's preflight and init-time tool check.
**Bound.** `_build` and `guards()` (`spec.py:246-499`), `init_chat_model`, Deep Agents harness profiles (`router.py:15`, `105-106`).
**Why.** Y01 (RESPECT) wants one way to reach a model. Y39 and Y41 (RESPECT) keep the recipe's isolation. Y40 (DROP by FR-030, FR-084, FR-133) and Y42 (DROP by K-15) remove its lockdown and the Codex driver.

NEXT. FR-027 is blocked by the same Literal. FR-029's retry and fallback are LangChain middleware (`router.py:243-250`) and act per request, which C-07 forbids.

### 4.4 Plugins and skills

**How.** Three skill folders exist, each five lines that say "Pending authoring" (`agents/skills/{build-mini-app,build-workflow,debug-app}/SKILL.md`). The QMX home is `~/.qmx` (`ctl/server.py:255-256`). The isolated-home pattern for Claude is `CLAUDE_CONFIG_DIR` plus `setting_sources=[]` (`native_claude.py:121`, `261`, `275`). The old desk packs in `qmx-agents/plugins/` (583 lines on `qma.core.plugins`, per 24) are still present.

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-030 one plugin format on both engines | MISSING | none | none | Format and OpenAI-side loader not designed |
| FR-031 default general/Lab/Portfolio plugins | MISSING | `copilot.yaml`, `researcher.yaml`, `data-analyst.yaml`, `app-builder.yaml` | Seeds for content | Plugin lint absent |
| FR-032 QMX-only home | partial RUNS | `~/.qmx` home; `CLAUDE_CONFIG_DIR` recipe | Reuse both | Dedicated Claude home not provisioned anywhere new |
| FR-035 three default skills naming real tools | STUB | placeholders above | Folder format reusable | Skill content and skill lint absent; `maintain-app` missing (`debug-app` exists) |

**Neutral.** The Agent Skills folder format (agentskills.io, per 27 §4) and the QMX home.
**Bound.** Deep Agents loads skills through its `/skills/` backend route (`copilot.py:70-75`; `spec.py:490`).
**Why.** P20 says Claude writes skills with the operator after the tools exist, so skills name real tools (P20 "Who"). That is RESPECT and is FR-035's lint. 27 [149] seeded "a plugin is skills + hooks + tools"; it was never built.

NEXT and LATER. COPILOT.md §4 lists 13 skill ideas and §5 lists `SkillWriteControl`. Nothing implements them.

### 4.5 Router, accounts and usage

**How.** `router.py` (322 lines) maps four fixed tiers to `provider:model` in `models.yaml`, which points `daily` at CLIProxy on `127.0.0.1:8317` (`models.yaml:1-14`). `model_selector` refuses `latest` aliases (`router.py:40-52`). `credential()` reads `qmx/<provider>` from keyring and allows an env key only under `CI` (`:110-122`). CLIProxy account and quota calls are `:280-302`. Usage exists only as journal `model_call` records (`guards/middleware.py:104-121`), summed into `cost` by `RunIndex.refresh` (`ctl/runs.py:86-134`). The settings section `providers` is read only for Litestream replicas (`ctl/service.py:759-776`). Budgets are call counts (`spec.py:102-105`, `418-425`).

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-038 accounts as rows, no limit | MISSING | `providers` settings section exists, unused | Reuse `settings_put` and `_no_secrets` (`service.py:79-91`) | Closed `Provider` Literal; router reads a YAML file |
| FR-039 balance per session, never switch | MISSING | CLIProxy affinity was external | Lesson only | No session-to-account binding |
| FR-040 availability, limits, usage, resets | MISSING | CLIProxy quota call `router.py:291-295` | DELETE with CLIProxy | No documented usage source chosen per vendor |
| FR-041 capability first, then usage | MISSING | static tiers | Tier names may become capability labels | No capability data per model |
| FR-042 provider defaults per workflow/role | FAKE | `RunContext.workflow`, `subagent` levels | Keep chain | Same per-request bug |
| FR-046 keys from Credential Manager, removed at teardown | RUNS | `credential()`; remote `credentials_scope` refs (`remote/models.py:73`, `88-92`); `secret-scan` in CI | RESPECT | OpenAI-engine key hand-off not designed |
| FR-048 own usage count, refusal card at limit | partial RUNS | journal usage; `runs.py:86-134` | Keep journal as ledger source | No limits, no refusal event |
| FR-049 documented usage sources only | RUNS after deletion | only CLIProxy management calls exist | Delete them | none |
| FR-051 caps per turn and job, USD pauses | FAKE (counts only) | `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware` `spec.py:418-425` | Keep the numbers; move to QMX wrappers | No USD; exits `end`/`error` instead of pause |

**Neutral.** `model_selector`, `RouterConfig`'s URL validation (`router.py:55-71`), `credential()`, `RunContext`, the chain walk in `resolve_model`, RunIndex cost aggregation.
**Bound.** `init_chat_model`, `router_middleware`, `ModelFallbackMiddleware`, `ModelRetryMiddleware`, `RecordModel` (`router.py:205-278`).
**Why.** Y14 (DROP the proxy by C-07, RESPECT stickiness and the own ledger), Y15 (DROP fixed tiers by FR-027), Y16 and Y17 (RESPECT pins and the chain), Y10 (RESPECT settings rows with vault refs).

NEXT. FR-043 to FR-045 and FR-047 have nothing beyond `list_models()` against CLIProxy (`router.py:280-286`). FR-050 has the `aggregates` SSE topic to build on (`service.py:164-169`).

### 4.6 Workflows

**How.** 24 §3 covers the format and compiler in full. New findings: the local runner stores no definition hash (git grep for `hash` in `agents/workflows/*.py` is empty), and no node has retries, timeouts or idempotency keys (grep empty). Validation already covers all four FR-057 faults: unbounded cycles (`models.py:270-272`), port types (`:128-165`, `:201`), loop maximum (`REQUIREMENTS` `:65`, `max_iterations` `:101`), and unsatisfied inputs (`:240`). The 501 stubs are `service.py:880-894`.

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-052 own runner over `workflow.v1`, own store | format RUNS; runner FAKE | `models.py` 289, schema 473; `compiler.py` 375; `runs.py` 124 | KEEP format; REPLACE compiler and `WorkflowRuns` | No store; A-09 open |
| FR-053 deterministic, agentic or mixed | FAKE | `python`, `agent`, `app_call` kinds | Keep kinds | Runner |
| FR-054 non-AI by default | FAKE | `python` node `compiler.py:102-109` | Keep | No usage ledger to prove zero calls |
| FR-055 typed IO across workflows, apps, widgets | partial RUNS | ports `models.py:29-42`; app `provides`/`feeds` `apps/manifest.py:98-99`; `artifacts.accept` `supervisor.py:673-675` | Reuse both schemas | No check across a workflow-to-app boundary before run |
| FR-056 copilot edits workflows via same API | STUB | `workflows_*` 501 | Keep op names and paths `server.py:47-50` | Store, validator wiring, runner |
| FR-057 validate before every run | RUNS | `models.py:175-283` | KEEP | Fix-it wording only |
| FR-058 gates bind to revision | FAKE | `human_gate` = LangGraph `interrupt()` `compiler.py:162-163` | Gate kind kept | No revision binding |
| FR-059 per-node checkpoint, resume days later | FAKE | `AsyncSqliteSaver` per run `runs.py:33-40` | Keep status set `runs.py:98-124` | Replace checkpointer |
| FR-060 run pins definition hash | MISSING locally | remote bundle hash `remote/models.py:70`, `82-85` | Reuse remote fingerprint rule | Local runner has no hash |
| FR-061 safe side effects, retries, caps, merge rules | partial | `Edge.mapping` five rules `models.py:120-125` | Keep mappings | No gate-per-write, idempotency, retries, timeouts, branch isolation |
| FR-062 `run_workflow` tool | FAKE | `as_subagent` `compiler.py:312-334`; `SubagentSpec.workflow` `spec.py:70-79` | Replace with a QMX tool | Runner |

**Neutral.** `models.py`, the schema file, `compatible`, topology checks, `pointer`, `template`, `input_view` and port checks (`compiler.py:56-99`, `142-157`), the seven-value status set.
**Bound.** `WorkflowState` reducers, `StateGraph`, `Send`, barrier edges, `interrupt`, `Command(resume=...)`, `AsyncSqliteSaver`, `CompiledSubAgent`, `to_python`.
**Why.** Y33 to Y36 (RESPECT) keep the format, defaults, hash pinning, depth rule and host-authored paths. Y02 (RESPECT one engine) and 24 F8 (DROP LangGraph) mean the runner must supply checkpoints, gate resume, fan-out, joins and recursion bounds itself.

NEXT and LATER. FR-063 and FR-066 have no code. FR-068 needs a new Code-view emitter (`to_python` emits LangGraph, `compiler.py:337-375`). FR-069 is a validator test only.

### 4.7 Triggers and scheduler (no WED FRs)

`AppDefinition.schedule` holds one `interval_seconds` that needs job entrypoints (`apps/manifest.py:80-81`, `165-166`). `BackupSchedule` (`apps/backup_schedule.py`) and the 60-second maintenance loop (`ctl/server.py:152-165`) are the only timers. FR-070 and FR-071 start from zero.

**Why.** COPILOT §4 planned a `schedule-routine` skill and §5 an approval for new schedules (Direct). FR-071's scheduled-job rules (bookmarks, a failed read is never a quiet day) come from 21-S62, not from code. The 60-second loop exists to refresh runs and the weekly backup (`server.py:152-165`); it is not a general scheduler and should not become one by accretion.

### 4.8 Mini apps

**How.** 24 §2 covers define, build, run, stop, storage and the road. New findings. Install refuses `trust == "agent"` at T1 with `tier_required` (`apps/supervisor.py:139-144`). `trust` is a plain argument of `apps_create` and `apps_update` (`ctl/service.py:657-667`), which `create_mcp` exports as tools (`server.py:120-129`). The fake Copilot passes `"trust": "reviewed"` itself (`agents/../tests/test_copilot.py:92`). The tool deadline is 20 s inside 30 s, and a timeout stops the app (`supervisor.py:676`, `715-726`). `check_descriptor` runs on discovery (`:473`) and on every call (`:671`).

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-072 copilot creates, runs, maintains, edits apps | FAKE | P15 copilot + `AppHooksMiddleware` `hooks.py:22-150` | Keep hook rules (tests before publish, test after build) | Engine; T1 refusal; never run live (PR #47) |
| FR-073 packaged, versioned, hashed unit | RUNS | `image_hash` `manifest.py:130-139`; volume `apps/volume.py:16-51` | KEEP | none |
| FR-074 typed refs, every app an MCP server | RUNS | `supervisor.py:686-692`; `apps/artifacts.py:43-109`; `apps_call` `service.py:732-749` | KEEP | none |
| FR-075 laptop subprocess, venv, limits, no Docker | RUNS for first-party | Windows Job Object `apps/windows_job.py`; scrubbed env `supervisor.py:390-419` | KEEP | Agent-trust apps refused at T1 |
| FR-076 Build→Tests→Sandbox→Shadow→Live | RUNS | `road/models.py:14-15`; `road/__init__.py:77-146` | KEEP | none |
| FR-077 publish gate, breaker notice, auto-test | partial FAKE | hooks `hooks.py:75-108`; money refusal at start `supervisor.py:473`; breaker notify `service.py:857-865` | Rules neutral, binding Bound | No "undeclared capabilities" check (COPILOT §7 lint, P24 on hold) |
| FR-078 host logs, heartbeat, metrics, breaker, budget | RUNS | `supervisor.py:587-638`; `Budget`, `Breaker` `manifest.py:68-78` | KEEP | Placement shown only as `node` string |
| FR-079 agent apps rebuilt; Macro daily bias live | FAKE | `examples/apps/macro-daily-bias/macro_bias.py:21-22` imports `qmx_agents.spec` and `router` | New app versions through the road (24 risk 2) | Engine seam for apps; 20 s deadline (A-17) |

**Neutral.** The whole of `qmx-apps` except its four imports of `qmx_agents.guards` (P12 below), plus the two LangChain-free hook rules in `hooks.py:41-73`, `153-179`.
**Bound.** `AppHooksMiddleware.wrap_tool_call` (`hooks.py:120-150`); the embedded Deep Agents in `weekend-watcher` and `macro-daily-bias`.
**Why.** Y27 (RESPECT MCP and refs), Y29 (RESPECT the sign door), Y28 (DROP T2/T3 default by C-09, K-06; RESPECT operator review), Y31 (DROP embedded agent core by FR-079), Y32 (RESPECT the deadline, move long agent work to jobs).

NEXT. FR-080 and FR-081 have no code. FR-081's "approval record" is also the natural fix for the T1 refusal.

### 4.9 Sub-agents

**How.** Sub-agents are Deep Agents `CompiledSubAgent` graphs built recursively with a cycle check only (`spec.py:297-324`). An automatic general-purpose sub-agent is added with explicit guards because Deep Agents omits custom middleware on it (`spec.py:444-476`; PR #35 body). Workflow agent nodes default to no general-purpose sub-agent (`workflows/models.py:103`). `stream_turn` turns each LangGraph namespace into a child session and an `agents` block (`copilot.py:131-145`, `208-213`).

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-084 own model, scope, tools; returns refs | FAKE | child `RunContext.subagent` `spec.py:303-308` | Keep spec refs | `request_model` beats `subagent` (`router.py:199-200`) |
| FR-085 lead and workers on different providers | FAKE (one LangChain engine) | router per agent | Chain reused | Cross-engine delegate missing |
| FR-086 Claude pattern as reference | MISSING | none | none | Engine |
| FR-088 depth cap, default no nesting | partial | `_NoDelegation` `spec.py:183-187`; workflow default `models.py:103` | Keep the default | Spec recursion has no depth limit |
| FR-089 sub-agent events on SSE | FAKE | child sessions and `agents` blocks | Keep mapping | Engine events must feed it |

**Neutral.** `SubagentSpec` (one `ref` or one `workflow`), the cycle check, child-session projection.
**Bound.** `CompiledSubAgent`, `SubAgent`, `SubAgentMiddleware`, the automatic general-purpose agent.
**Why.** Y06 (RESPECT) says every helper gets the parent's guards. Y35 (RESPECT) sets depth 1. Y17 (RESPECT chain, fix the override) protects FR-084. Sub-agent cost rules come from the operator (NFR-003), not from code history.

LATER. FR-090's `data-analyst.yaml` needs a sandbox backend (`copilot.py:57-58`), which is Bound.

### 4.10 Memory

**How.** `agents/memory.py` (678 lines). Neutral parts are `Scope` (`:53-57`), `MemoryRecord`, the `MemoryProvider` protocol (`:98-131`), `namespace` (`:185-195`), `memory_path` (`:198-207`), the injection filter (`:39-50`) and `MemoryManager` caps and pinning (`:365-417`). Bound parts are `tools() -> list[BaseTool]` (`:130`, `464-515`), the middleware (`:517-678`) and the default `StoreMemoryProvider` on LangGraph `SqliteStore` (`:31`, `210-353`). Global writes need an approval callback (`:246-250`). External providers load by entry point `qmx.memory_providers` (`:354-362`). Tests are 564 lines.

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-091 each engine's SDK default memory | MISSING | none | none | Engines |
| FR-093 records never in memory | RUNS by design | kinds `facts/episodes/profile/notes` `memory.py:36-37`; records in Library, `runs.db`, QMB | KEEP the split | Needs a test that memory writes touch no record table |

**Why.** Y23 (DROP the Hermes rule by K-10), Y24 (RESPECT the write rules), Y25 (DROP `SqliteStore`, RESPECT one file per profile). PR #33 adds that `SqliteStore` rejects async methods, which is why every call goes through `asyncio.to_thread` (Direct). That workaround disappears with the store.

NEXT and LATER. FR-092 can reuse the protocol, scopes and approval rule. K-10 retires the "at most one external provider" check (`memory.py:380-381`). FR-094 has no list or edit API.

### 4.11 Context, prompts and compaction

**How.** The Copilot prompt is 10 lines (`agents/copilot.md`). It still describes plan/do tiers and placeholder skills (`:4`, `:10`). Compaction is Deep Agents summarisation wrapped for the pre-compress memory hook (`spec.py:386`; `memory.py:636-678`). `ContextEditingMiddleware` clears old tool results for the Copilot (`spec.py:406-407`). Nothing measures cache reads.

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-096 own short prompts, no CLAUDE.md | partial | `copilot.md`; `setting_sources=[]` `native_claude.py:261` | Rewrite prompt; RESPECT the recipe | Engine |
| FR-097 stable prefix, no mid-session swaps | violated | per-turn tier switch `copilot.py:112`; router rewrites model per call `router.py:205-217` | DROP both | Cache field capture missing |
| FR-098 automatic compaction both engines | FAKE | Deep Agents summariser | Keep offload-to-file idea | OpenAI-engine summariser absent |

**Why.** Y26 (DROP Deep Agents context defaults, RESPECT offload). Y18 (DROP) removes the per-turn tier switch that breaks caching. DESIGN §5.5 relied on "prompt caching for Claude" being automatic through Deep Agents (Direct). QMA v2 must prove it with cache fields instead (NFR-004, NFR-005).

NEXT. FR-100's tool-search has no code. FR-101's progress events would ride the `sessions` topic.

### 4.12 Approvals, hooks and the money path

**How.** `check_descriptor` (`guards/money_path.py:247-279`) is neutral and already used on MCP descriptors by the supervisor. The act vocabulary is `:21-60`. The two `propose_order` tools are LangChain `BaseTool`s (`:181-238`), and `check_tool` reads `BaseTool` (`:240-244`). `MoneyPathMiddleware` re-checks at model and tool time (`guards/middleware.py:34-72`). The admission gate keeps `_staged` and `_approved` in memory (`guards/admission.py:62-63`), and `approve` takes `principal == "operator"` (`:84-93`). HITL approvals are LangGraph interrupts journaled by `JournalApprovals` (`middleware.py:208-237`). Live approvals are answered on stdin (`scripts/live/copilot_build_app.py:64-76`, per 24). The journal writes `run_start`, `run_end`, `model_call`, `model_error`, `tool_start`, `tool_end`, `interrupt`, `approval_resolved`, `order_proposed`, `proposal_staged` and `approval` (`middleware.py:85-202`; `money_path.py:197`; `admission.py:78-92`).

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-102 propose only, enforced in QMX wrappers | core RUNS; binding FAKE | `check_descriptor`; broker exposes no order tool (`qmx-broker/.../service.py:164-185`) | KEEP core, rewrap tools | No wrapper layer; Claude built-ins (Bash) bypass QMX tools (24 risk 5) |
| FR-103 hooks decide write locations, verify writes | partial FAKE | `Permissions` `spec.py:82-99`; admission `before_hash`/`after_hash` `admission.py:99-111` | Keep rule | No per-kind folders (strategies) |
| FR-104 one approval contract, durable queue | MISSING | in-memory admission; LangGraph interrupts | Keep "exact content plus before-hash" rule | No approvals table or answer route |
| FR-105 operator's always-ask list as Settings row | partial | `interrupt_on` per spec `copilot.yaml:12`; destructive flag `server.py:127` | Keep destructive flags as default source | Not a Settings row |
| FR-106 journal every run, call, interrupt, approval | FAKE (events) / RUNS (writer) | `RunJournal` `journal.py:36-127` | KEEP writer; move to neutral package | Event producers are middleware |

**Neutral.** `check_descriptor`, `MoneyPathAct`, `MoneyPathDeniedAct`, aliases, `OrderProposalInput`, `RunJournal`, `AdmissionGate`, `valid_path`, `WriteProposal`.
**Bound.** `OrderProposalTool`, `BrokerOrderProposalTool`, `check_tool`, `AdmissionBackend`, `AdmissionSandboxBackend`, all of `middleware.py`.
**Why.** Y04, Y05, Y07, Y08, Y09 (RESPECT). 24 §4 adds that OpenAI Agents SDK hooks only observe, so blocking must sit inside QMX's own tool wrappers on both engines. Y19 (RESPECT content) carries the COPILOT §5 hooks into FR-109.

NEXT. FR-107 to FR-109 have only the hook ideas in COPILOT.md §5 (`EvidenceBeforeClaims`, `ReviewLoopCap`).

### 4.13 Placement and off-machine runs

**How.** 24 §5 covers the lane. New findings. `RemoteSettings` defaults to target `vps` and bucket `vps:/srv/qmx/bucket` (`remote/models.py:122-139`). Providers are `ssh`, `amp`, `modal`, `e2b` (`:101`). Tests use a `FakeProvider` and stub Modal/E2B/Amp SDKs (`qmx-remote/tests/test_remote.py:74`, `343`, `382-428`). PR #46 says no live provisioning was ever run.

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-110 runs on rented on-demand compute | FAKE | `ModalProvider`, `E2BProvider` `remote/providers.py:169-324` | Keep protocol and rented adapters | Default target is an owned VPS (K-01); worker runs LangGraph (`worker.py:137-208`) |
| FR-111 one provider interface; idempotent setup | partial RUNS | `ComputeProvider` `providers.py:18-24`; `ctl/node-bootstrap.sh:11-74` (PR #40 "idempotent") | Keep both | Bootstrap targets an owned Ubuntu box with CLIProxy note; no pass/fail verify per rented provider |
| FR-112 placement, status, cost, log tail | partial RUNS | `runs_status`, `runs_logs`, `job_*` `service.py:522-587`; RunIndex `node`, `cost` | Keep | Cost only from provider metadata |
| FR-113 Git-like results | RUNS (fake provider) | manifest `remote/models.py:142-183`; verified fetch `service.py:531-559`; `runs/<id>` `remote/code.py:32-47` | KEEP | Resume means a LangGraph checkpoint today |

**Neutral.** `models.py`, `providers.py`, `store.py`, `code.py`, `runs.py`, and `execute_job` (`worker.py:211`).
**Bound.** `execute_workflow` and `execute_agent` (`worker.py:137-208`); the manifest's `langgraph` version entry (`worker.py:104`).
**Why.** Y37 (DROP owned VPS and Amp by C-08, K-01, §2.3). Y38 (RESPECT the result model). PR #46 records that the Amp SDK ignores `mcp_config`, skills and tool lists remotely and has no cancel API (Direct), which supports dropping it.

NEXT. FR-114 resume elsewhere exists for remote runs only (`remote/runs.py:196-220`). FR-116 can reuse the rclone backup with restore test (`apps/backup.py:122-196`). FR-117 needs a Windows-only flag. FR-118 can reuse `Target.gpu` and `place` (`remote/models.py:106`, `127-139`).

### 4.14 Observability and DevOps

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-119 transcripts and logs exported by host | partial RUNS | block log; remote fetch of journal/logs/traces | Keep | Engine transcripts not captured |
| FR-120 one local trace store, nothing to OpenAI | MISSING | DESIGN §5.8 planned LangSmith or OTel | none | Engines; OpenAI tracing off by default |
| FR-121 run index with four axes | partial RUNS | RunIndex fields `ctl/runs.py:34-47` | Keep table | No caching, where, who, how fields |

**Neutral.** `RunIndex` (record, refresh, rewrite detection at `ctl/runs.py:74-79`), supervisor JSONL logs, journal.
**Why.** DESIGN §5.8 planned LangSmith or local OTel (Direct). LangSmith is a §2.3 non-goal, and FR-120 forbids sending traces to OpenAI, so only "local file" survives. DESIGN §7.7 says observability is host-provided, never per app (RESPECT, NFR-013).

NEXT. FR-122 can reuse supervisor health. FR-123 has no watchdog.

### 4.15 UI contract and events

**How.** `SessionBlock.type` is 14 closed kinds (`service.py:54-72`). `events` has seven topics (`:43`) and SSE polls every 50 ms (`:187-198`). `OPERATIONS` lists 52 rows feeding both doors (`server.py:28-81`). The sign door is REST only (`:184-196`).

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-126 one event stream from both engines | partial RUNS | blocks plus `sessions` topic | KEEP | No `usage` or cursor kind; engine adapters absent |
| FR-127 sessions shown with running state | partial RUNS | `sessions_list` | Keep | No status column |
| FR-128 two doors, same results | RUNS | `create_mcp` and REST loop `server.py:120-129`, `206-213` | KEEP | New routes must join `OPERATIONS` |
| FR-129 honest `not_implemented` | RUNS | `_unavailable` `service.py:643-647` | KEEP | none |
| FR-130 SSE push, deltas unstored | partial | SSE exists | Keep block log | Every event is a row; no delta channel (24 risk 6) |

**Neutral.** All of it. qmx-control imports no LangChain.
**Why.** Y11, Y12, Y43, Y44 (RESPECT). The UI on `ui-review/repair` is wired later and calls none of these routes yet (24 §1.6), so new fields cost no UI migration.

NEXT. FR-131 has `runs/<id>` branches in the remote lane only.

### 4.16 Tools and reach

| FR | State | Code today | Reuse or replace | Blocker |
|---|---|---|---|---|
| FR-132 capability registry, named seams | partial RUNS | 13 functions over data/backtest/research/node `tools/registry.py:26-271`; Library module `ctl/library.py` | KEEP functions | No registry object; QMB and QMF seams unnamed |
| FR-133 Claude Code baseline on every agent | MISSING | shell only through a sandbox app `copilot.py:30-51` | none | Native recipe removes built-ins (`tools=[]`) |
| FR-134 one tool design, lint, allow-list, MCP in Settings | partial RUNS | `response_format` `tools/service.py:24-29`; `mcp_servers` settings `service.py:208-217` | Keep | No tool lint |

**Neutral.** `domain_functions`, `DomainContext`, `create_server`.
**Bound.** One line, `tool(...)(function)` (`tools/registry.py:274-281`).
**Why.** P09's title says "share recorded domain tools between agents and MCP" (PR #34). DESIGN §5.6b lists the agent tool catalogue. The FastMCP servers stay (27 §4, RESPECT). The `tools/service.py:1` docstring says agents never choose filesystem roots or execution code (Direct, RESPECT; it matches 24 F9).

NEXT. FR-135 keeps `examples/apps/mql5-articles` and the Firecrawl settings guard (`service.py:230-254`). FR-138 is served today by `qmx-broker` read tools plus `propose_order`.

### 4.17 Concurrency and self-improvement

FR-141 (WED) is MISSING. No code counts Claude sessions or reads free RAM. `psutil` is already a dependency of `qmx-control` and `qmx-apps` (their pyprojects), and app memory limits use a Windows Job Object (`apps/windows_job.py`; `Budget.memory_mb` at `manifest.py:71`), so the measuring tools exist. NEXT and LATER items have no code.

**Why.** The old runtime never needed a cap because it ran no native Claude sessions under QMX (the native backends sit unused in `qma-daemon`). The ~1 GB per session figure is a capability fact from 19 §11, not from code history.

### 4.18 Shipping, documents and platform

FR-144 (WED) is process only. DESIGN §2 rule 7 says main holds no code. Q7 (answered 2026-10-12) says QMA v2 ships into `rebuild/base`. `just ci` is the gate. GitHub has never run it (fact F14). Branch protection rules were not checked in this pass.

**Why.** Y45 (RESPECT one gate). Every rebuild PR body reports a local `just ci` table and an exclusive `.ci-lock` with at most two pytest workers (PR #33, #35, #44, #46), which is the operator's machine-limits rule (NFR-034) in practice.

FR-145 to FR-148 have no code. FR-146's "agent-facing data API" today is the `qmx-control` operation set plus the Library module.

## 3. Why: constraints from the existing shape

Sources consulted. Source control through git log, git grep and `gh pr view` bodies #29, #31, #33, #35, #44, #46, plus 24's set (#36, #37, #47, #49, #58, #66). Long-form documents `rebuild/DESIGN.md`, `rebuild/COPILOT.md`, packets P06, P07, P08, P11, P20, P21, P22, P24, and 24 and 27. Issue tracker, chat, observability, error tracking and analytics were skipped because no such MCP is connected for QMX. The GitHub MCP failed to connect, so the `gh` CLI was used.

Confidence. "Direct" means an author wrote the reason. "Inferred" is marked. RESPECT means QMA v2 keeps it. DROP names the PRD item that drops it. 24 §7-9 rows W1-W10, A1-A7 and F1-F9 stand and are cited by ID, not repeated.

| # | Reason, with evidence | Confidence | Constraint for QMA v2 | Verdict |
|---|---|---|---|---|
| Y01 | Audit found three ways to reach a model and a 4,007-line god process (24 W1) | Direct | One `Engine` contract; no parallel runtime | RESPECT (C-01, NFR-029) |
| Y02 | Two glued workflow engines caused the failing tests (24 W2) | Direct | Exactly one graph engine | RESPECT; engine changes (C-06) |
| Y03 | "Adopt before building" chose Deep Agents for planning, sub-agents, files, compaction, approvals (DESIGN §1, §2.1) | Direct | Adopt the two SDKs for loop, tools, sessions, hooks, compaction | RESPECT principle; DROP Deep Agents and LangChain (C-01, C-06, §2.3) |
| Y04 | Invariants survive as thin wrappers, never a parallel runtime (DESIGN §2.4, §5.7) | Direct | Each rule once, neutral, called from both engines | RESPECT (NFR-020) |
| Y05 | Order tools never appear in any tool list; only `propose_order`, signed by the operator (DESIGN §5.7; P08) | Direct | Money check inside QMX tool wrappers at call time, not only at build | RESPECT (C-11, FR-102, NFR-015) |
| Y06 | Deep Agents' automatic general-purpose agent drops custom middleware, so QMX gave it explicit guards (PR #35) | Direct | Every engine-spawned helper runs through the same wrappers | RESPECT (FR-102, FR-084) |
| Y07 | Journal has one exclusive writer, fingerprints, reopen verification, hashed args and result refs (PR #35; `journal.py`) | Direct | Journal stays the single evidence writer | RESPECT (FR-106, NFR-013) |
| Y08 | Admission approves only for `principal == "operator"` and re-checks exact content and before-hash (`admission.py:84-111`) | Direct | Approval binds to exact content | RESPECT rule; replace in-memory state (FR-104) |
| Y09 | A Windows probe showed `/ARTIFA~1/` bypassed admission; path rules were hardened (PR #35) | Direct | Keep `valid_path` rules on every write hook | RESPECT (FR-103) |
| Y10 | Configurable means UI-editable; secrets refused in settings (DESIGN §2.5; `service.py:79-91`) | Direct | Router, plugins, approvals, budgets live as settings rows | RESPECT (C-16, C-15) |
| Y11 | One API, two doors; no agent back doors (DESIGN §8; P11; P15) | Direct | New turn, approval and workflow routes join `OPERATIONS` | RESPECT (FR-128) |
| Y12 | Unbuilt routes answer `not_implemented`, never fake success (P11) | Direct | Keep for every unbuilt QMA v2 route | RESPECT (FR-129) |
| Y13 | No LangGraph Agent Server: no extra server, no licence (DESIGN §8) | Direct | QMX owns the turn host and job runner | RESPECT (C-08, 24 W7) |
| Y14 | CLIProxy was primary: subscription accounts, rotation, affinity; it keeps no usage history (DESIGN §5.3) | Direct | Sticky session per account; QMX keeps its own ledger | DROP proxy (C-07, §2.3); RESPECT lessons (FR-039, FR-048) |
| Y15 | Four fixed tiers in a `daily` and a `test` profile, from P06 | Direct | Models are rows, not a fixed tier file | DROP (FR-027, FR-038, NFR-019) |
| Y16 | `model_selector` refuses `latest` aliases (`router.py:40-52`) | Inferred: reproducibility | Pin exact model ids per row | RESPECT (NFR-031) |
| Y17 | Override chain global → node → app → workflow → agent node → sub-agent (DESIGN §5.3) | Direct | Chain plus engine per level | RESPECT (FR-026); fix the request override (FR-084) |
| Y18 | Plan/do modes with a per-turn tier switch (`copilot.py:105-113`; COPILOT §2) | Direct; withdrawn 2026-10-09 (COPILOT.md:3) | No mode code | DROP (C-10, FR-006, FR-097) |
| Y19 | COPILOT §5 hook list (EvidenceBeforeClaims, ReviewLoopCap, BudgetGuard, SecretsGuard, ArtifactEmitter) | Direct | Hook content carries over; middleware binding does not | RESPECT content (FR-109, FR-051, FR-010); DROP binding (C-06) |
| Y20 | COPILOT §6 session log, resume by run id, headless assumptions card | Direct | Runs never merge; unattended runs end with a card | RESPECT (FR-017, FR-018) |
| Y21 | Background tasks are QMX-owned because `AsyncSubAgent` needed an Agent Server (27 §4) | Direct | `start_task` family stays QMX tools | RESPECT (FR-015) |
| Y22 | Fakes in tests, live calls only in `scripts/live/` (README; DESIGN; P06) | Direct | Fakes for both SDKs before the first engine PR | RESPECT (NFR-027) |
| Y23 | Hermes rule: built-in plus at most one external memory provider (P07; DESIGN §5.4) | Direct | Per-agent provider binding | DROP (K-10, FR-092) |
| Y24 | Memory scopes, primary-only automatic writes, global approval, 2k profile cap, no LangMem (P07; PR #33) | Direct | Same rules on the new layer | RESPECT (FR-092, FR-095) |
| Y25 | Default memory store is LangGraph `SqliteStore` (DESIGN §5.4) | Direct | SQLite file per profile, without LangGraph | DROP store (C-06); RESPECT file layout (NFR-009) |
| Y26 | Deep Agents context defaults: summarise at 85 %, offload at 20k tokens (DESIGN §5.5) | Direct | Large tool results go to files | DROP mechanism; RESPECT offload (FR-098) |
| Y27 | Every app speaks MCP; artifacts by reference; no app bus (DESIGN §7.3; 24 A2-A3) | Direct | Engines consume apps as MCP | RESPECT (FR-074) |
| Y28 | Agent-written app code starts at T2/T3; T1 only after operator review (DESIGN §7.5) | Direct | Laptop subprocess by default; enable only after an approval record | DROP T2/T3 default (C-09, K-06, FR-075); RESPECT review (FR-081, FR-077) |
| Y29 | Money apps need the operator's signature; the sign door is not an MCP tool (`server.py:184-196`) | Direct | No engine or plugin reaches the sign door | RESPECT (C-11) |
| Y30 | Everything is files, one writer per file, no DB server (DESIGN §7.6b) | Direct | Approvals, runner checkpoints, ledger in SQLite or JSONL | RESPECT (NFR-009) |
| Y31 | Agent-bearing apps embed `qmx_agents` at a pinned commit for portable locks (`qmx-apps/README.md:68-70`) | Direct | Apps get a thin engine seam | DROP (FR-079; 24 A7) |
| Y32 | 20 s app tool deadline that stops the app (`supervisor.py:676`, `715-726`) | Inferred: protect the host from hung apps | Keep for tool calls; long agent work runs as a job | RESPECT with change (A-17) |
| Y33 | `workflow.v1` is stored truth with typed ports, five mappings, bounded loops (24 F1, F2, F4) | Direct | Keep format and validator | RESPECT (FR-052, FR-057) |
| Y34 | Deterministic by default; a run pins its definition (24 F3, F6) | Direct | Runner works with no engine; hash per run | RESPECT (FR-054, FR-060) |
| Y35 | Workflow agent nodes get no general-purpose sub-agent (24 F5) | Direct | Depth 1 by default | RESPECT (FR-088) |
| Y36 | Function and AgentSpec paths are host config, never model arguments (24 F9) | Direct | Copilot writes graphs only via `workflows_put` plus validation | RESPECT (FR-056) |
| Y37 | Own VPS is the default target; Amp is the second adapter; CLIProxy on the server (P21 §0, §1, §7) | Direct | Rented on-demand providers only | DROP (C-08, K-01, §2.3) |
| Y38 | Bundle, manifest, hashes, 5 s flush, verified fetch, resume, `runs/<id>` (P21; PR #46) | Direct | Keep the result model | RESPECT (FR-113) |
| Y39 | Native Claude recipe: dedicated `CLAUDE_CONFIG_DIR`, `setting_sources=[]`, no `ANTHROPIC_*`, auth must be `claude.ai`, pinned SDK and CLI (`native_claude.py:40-160`) | Direct (docstring `:55-62`) | Same isolation and subscription checks | RESPECT (FR-022, FR-032, FR-096) |
| Y40 | Native recipe locks out built-ins, skills, agents, plugins and hooks; `max_turns=8` | Direct (`:58-61`) | Allow plugins, skills, sub-agents and baseline tools behind QMX hooks | DROP (FR-030, FR-035, FR-084, FR-133) |
| Y41 | Recipe refuses any advertised tool outside the allow-list (`native_claude.py:300-306`) | Direct | Check the advertised tool list at session init | RESPECT (FR-102) |
| Y42 | Codex native driver (`native_codex.py`) | Direct | No Codex process | DROP (K-15, FR-021) |
| Y43 | SSE reads the `events` table with a 50 ms poll; every change is a row (`service.py:156-198`) | Inferred: simplicity, durable replay via `Last-Event-ID` | Whole blocks stay rows; deltas get an unstored channel | RESPECT with change (FR-130) |
| Y44 | The 14-kind block list is the UI's contract (24 §1.3) | Direct | New engine events map to kinds or extend the list on purpose | RESPECT (FR-126) |
| Y45 | One sequential runner for `just ci` and GitHub (PR #29) | Direct | Keep one gate | RESPECT; note F14 |

## 4. Facts the architecture must not get wrong

### 4a. Platform facts

**P1. qmx-control tables and migrations.** `control.db` (WAL) holds `sessions(id, data)`, `blocks(session_id, seq, data)`, `work(kind, id, data)` and `events(seq AUTOINCREMENT, topic, subject, data)` (`ctl/service.py:119-128`). `runs.db` holds `runs` and `journals(path, digest, size)` (`ctl/runs.py:23-28`). `library.db` belongs to the Library. There is no migration framework. Each class runs `CREATE TABLE IF NOT EXISTS` in its constructor, with one hand-written move of an old `library` table inside `BEGIN IMMEDIATE` (`service.py:129-149`). New QMA v2 tables (approvals, errands, accounts, workflow definitions) need either the same pattern or a first real migration step. Rows are JSON blobs, so new fields need no schema change.

**P2. Blocks and SSE.** Block kinds are `user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you` (`service.py:54-72`). Event topics are `runs, jobs, sessions, apps, library, settings, aggregates` (`:43`). A block append emits `{"type":"block","block":...}` on `sessions` (`:334`). Changes to runs, jobs, apps or Library also emit an `aggregates` row (`:164-169`). `GET /api/events/{topic}` honours `Last-Event-ID` and `after`, and polls every 50 ms (`server.py:215-228`).

**P3. Mini-app manifest and lifecycle.** `app.toml` holds `id, name, version (semver), risk (shows|runs|money), kind (screens|headless|both), startup_timeout_seconds, entrypoints {mcp, jobs, agents, workflows, ui}, capabilities {network, secrets, data_reads}, schedule, budget {runs, cpu_seconds, memory_mb, cpu_percent}, breaker {max_errors, heartbeat_timeout}, provides, feeds` (`apps/manifest.py:54-99`). Secrets must be `qmx/*` (`:173-179`). `pyproject.toml` and `uv.lock` are required (`:183-185`). Trust is `first_party | operator | reviewed | agent` (`:18`). Road stages are `build, tests, sandbox, shadow, live` (`road/models.py:14-15`). A money app needs a signature before `start` (`supervisor.py:354-357`).

**P4. `workflow.v1`.** `{version, name, entry, nodes, edges}` (`workflows/models.py:168-173`). Ten kinds: `python, agent, tool, app_call, condition, parallel, join, loop, human_gate, subworkflow` (`:11-22`). Ports have `kind (reference|data|event|control)`, `cardinality (one|many)`, a local-only JSON Schema, `select` and `required` (`:29-42`). Edges carry `mapping (one|zip|broadcast|keyed-join|cartesian)` and an optional `route (true|false|repeat|done)` (`:120-125`). `max_iterations` is capped at 1000 (`:101`). There is no field for triggers, retries, timeouts, idempotency keys or a definition hash.

**P5. qmx-remote bundle and placement.** `RunBundle.kind` is `workflow | agent | app | job | amp` and its hash must equal `fingerprint({definition, files})` (`remote/models.py:67-97`). Credentials are env-name to `qmx/*` refs. `Target.provider` is `ssh | amp | modal | e2b`. `place` picks the requested or default target and falls back to any target with enough GPUs (`:127-139`). Manifest artifacts must live under `outputs, logs, traces, checkpoints` or be `journal.jsonl` (`:150-153`).

**P6. qmx_tools and FastMCP.** Thirteen plain functions in four groups (`data`, `backtest`, `research`, `node`), served as FastMCP stdio servers (`tools/servers.py:9-38`) and wrapped as LangChain tools in one place (`tools/registry.py:274-281`). The `node` group includes `propose_order` (`registry.py:234`, `270`). `DomainContext` imports QMB, QMF, QML and QMN directly (`tools/service.py:14-22`), so `qmx-tools` pulls the whole quant core into any environment that installs it.

**P7. Guards.** `journal.py`, `experiments.py` and `parent_surfaces.py` are neutral. `money_path.py` is neutral except the two `BaseTool` classes and `check_tool`. `admission.py`'s gate is neutral and its backend is Deep Agents. `hooks.py`'s `_test` and `watch_breakers` are neutral. `middleware.py` is fully Bound.

**P8. memory.py.** See 4.10. The neutral protocol has ten methods, including `on_pre_compress` and `on_scope_end`, and returns LangChain tools from `tools()` (`:98-131`). That one return type must change to a neutral tool descriptor.

**P9. router.py.** See 4.5. `RunContext` is a dataclass that both the router and the memory module import (`memory.py:34`). It is the de facto run identity type today.

**P10. native_claude recipe.** See 4.3 and Y39-Y41. The Claude Agent SDK spawns the pinned `claude` CLI binary per client (`cli_path`, `native_claude.py:240`), and `auth status` runs through that binary (`:116-128`). "Never the Claude Code CLI" in C-02 means no CLI harness. The binary is still a runtime dependency on every machine that hosts a Claude session, including rented ones (A-02).

**P11. Test harness.** `just ci` runs `tools/ci.py`. Steps: `uv sync --frozen` at the root and in `qmx-agents` (all packages, all groups); `fmt-check`, `lint` and `types` (Pyright strict, Python 3.14) in eight workspaces; `money-path-scan` and `secret-scan`; then `tools/test_all.py` (`tools/ci.py:23-38`). Suites are QMF/QML/QMB/QMN, tools, adws, QMA (all of `qmx-agents/packages` plus `qmx-agents/tests`, which includes the old `qma-*` tests), qmx-agents, qmx-tools, qmx-control, qmx-apps, qmx-broker, qmx-remote, QA gates and each `qa/tests/epic_*` (`test_all.py:57-127`). Every suite runs with `-n 2 -m "not serial"` (`:136`). The fakes are LangChain `GenericFakeChatModel` subclasses (`agents/../tests/conftest.py:10`, `21-63`).

**P12. Import cycle.** `qmx-control` depends on `qmx-apps`, `qmx-broker`, `qmx-remote` (its pyproject). `qmx-apps` depends on `qmx-agents` for `check_descriptor` (`supervisor.py:29`) and the journal (`road/__init__.py:11`, `road/history.py:13`, `road/validation.py:12`). `qmx-agents` depends on `qmx-tools` and `qmx-broker`, and imports `qmx_control` (`spec.py:35`, `copilot.py:16-18`, `tasks.py:13-14`). `qmx-tools` depends on `qmx-control` (`tools/service.py:20-22`). `qmx-remote` depends on `qmx-agents` and `qmx-apps` (`remote/models.py:11`, `runs.py:16`, `worker.py:29-34`). Moving `journal`, `experiments`, `parent_surfaces` and `check_descriptor` into a neutral package removes every edge from apps and remote into `qmx-agents` except the worker's executors.

### 4b. Traps

- **F1.** Trust is caller-declared. `apps_create(path, trust="agent")` is an MCP tool, so an agent can pass `"reviewed"` or `"operator"` and skip the T1 refusal (`service.py:657-667`; `test_copilot.py:92`). Trust must come from the host or an approval record, never a tool argument.
- **F2.** T1 refuses agent trust (`supervisor.py:139-144`). FR-072 on the laptop with no Docker (FR-075) is impossible until that refusal becomes "disabled until approved".
- **F3.** Cancellers (`service.py:106`), background tasks (`tasks.py:29`) and admission approvals (`admission.py:62-63`) are in memory. A restart loses them, and `runs_cancel` then answers 501.
- **F4.** `RunIndex.record` defaults a missing `kind` to `"agent"` and `status` to `"running"` (`ctl/runs.py:34-47`). A run that dies without a terminal record shows as running forever. The watchdog (FR-123) must own that.
- **F5.** Sessions have no status and no target. FR-003 and FR-127 need new fields, not a new table (rows are JSON).
- **F6.** The router's `Provider` Literal and four-tier profile check (`router.py:29-30`, `84-93`) make "a model is a config row" impossible without a rewrite.
- **F7.** The `providers` settings section already exists and is read for Litestream replicas on T2 (`service.py:759-776`). Account rows need their own section, or the Litestream use must move.
- **F8.** The per-request override at `router.py:199-200` silently sets every sub-agent's model. FR-084's acceptance check fails on today's code by construction.
- **F9.** The CI "money-path-scan" checks binary floats in quant code (`tools/money_path_scan.py:1-8`). It never inspects agent tools. FR-102 needs a dedicated two-engine test.
- **F10.** `openai-agents` is in no lockfile. `claude-agent-sdk` 0.2.163 is locked only because `qma-daemon` needs it. P16 deleting the daemon would drop the pin unless QMA v2 adds it first.
- **F11.** `native_claude.py`, `native_codex.py` and `native_sessions.py` are still on `rebuild/base` in `qma-daemon/src/qma/daemon/request_runtime/`. P16 lists them for deletion. Copy the Claude one into the tracker first (24 risk 9).
- **F12.** App tool calls time out at 20 s and the timeout stops the app (`supervisor.py:676`, `721-726`). An agent call inside an app tool will trip it on a real model.
- **F13.** The old `qmx-agents/plugins/` desk packs and the word "plugin" collide (24 risk 13). Delete before the plugin loader lands.
- **F14.** GitHub Actions has produced no run on any rebuild PR (PR #46 body; `gh pr checks 67` reports none; `gh run list` is empty while Actions is enabled). Every "CI green" claim so far is a local `just ci`.
- **F15.** No line of `qmx_agents` has run against a real model. Every PR from P06 to P21 deferred its live smoke. Treat all FAKE rows as unproven behaviour, not as working features.
- **F16.** `settings_put` rejects any key named like `key`, `token`, `password` or `secret` at any depth (`service.py:79-91`). Account rows must store `credential_ref`, never a field with those names.
- **F17.** Two control planes exist. A T2 node runs its own `ControlService` and `control.db` (`ctl/node.py:158`). Remote events land on the node, so the laptop UI needs a merge or relay (24 risk 16, A-15).
- **F18.** Installing `qmx-tools` installs QMB, QMF, QML and QMN (`qmx-tools` pyproject dependencies). Any engine or plugin package that imports `qmx_tools` drags the quant core into its environment and into every rented-machine image. Engines should reach domain tools over their FastMCP servers, not by import.
- **F19.** The "QMA" suite in `test_all.py` runs all of `qmx-agents/packages`, so it re-runs every `qmx-*` package test plus the old `qma-*` tests (`test_all.py:66-71`). Deleting LangChain code changes that suite's count, and the old tests keep the 110k-line anchor in CI until P16 ends.
- **F20.** `default_home()` is `~/.qmx` on C: (`server.py:255-256`). NFR-034 keeps bulk data off C:, so run volumes, checkpoints and engine homes need a configurable root.
