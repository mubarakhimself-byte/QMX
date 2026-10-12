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


## Delta pass 2 (journeys, research 30-32)

Written 2026-10-12. Inputs: `tracker/qma-v2/USER-JOURNEYS.md` (21 journeys, 25 spin ideas, §4 gaps), research 31 (tools, skills, prompts, comms), research 32 (DevOps planes, UI protocol, usage), research 30 (agents and databases). Code read with `git show` on `origin/rebuild/base` @ a82f5897 (PR #68). `git diff --stat bc32b46a a82f5897 -- qmx-agents/packages/qmx-*` is empty, so every pass-1 citation still holds. Same method and labels as pass 1: one agent, no sub-agents, planning only. Paths use the pass-1 keys (`ctl/`, `apps/`, `agents/`, `tools/`, `remote/`, `daemon/`).

### D0. Summary in plain words

1. All four inputs fit the platform that runs today. None of them needs LangChain, and none of them breaks the 14 block kinds.
2. The inputs give three different homes for "a run": `work` rows in `control.db` (32), a new `runs` table in a new `agents.db` (30), and today's `runs.db` projection over journals. One must win (X1).
3. Five vocabularies describe run, job and approval states. Two exist in code (`record_work`, the workflow runner). Research 31, 32 and 30 add three more. One enum must be written down before any table lands (X2).
4. FR-104 needs a pending approval to survive a restart. Research 32 lets Claude approvals expire when the process dies. J19 shows the card still pending. The PRD and the journey win (X4).
5. The approval answer route, the credential route and the operator terminal route must be REST-only, like today's sign door. If they joined `OPERATIONS`, an agent could approve its own request through MCP (G1).
6. Research 30's SQLite finding is real and confirmed here. The bundled SQLite is 3.50.4, and `qmx-control` opens a fresh connection per call from several threads, while SSE readers poll without the lock. One writer connection per file is the fix the code is closest to (G2).
7. Research 30 splits storage into four files. That breaks its own outbox rule, because approvals and their events would no longer share a transaction. Recommended: one `control.db` with one writer task; split off only checkpoints, and later only on a failed load test (X3).
8. Research 31 and 30 both mention a Contabo server. C-08 and K-01 dropped any owned server, so remote work reaches the laptop through the bucket and fetch, never live (X7).
9. Research 31 sets spawn depth 2. FR-088 (WED) and J11 say depth 1. Recommended: keep depth 1 and make the orchestrator an errand session, not a sub-agent (X6).
10. The journeys add 17 missing requirements. Four have a seam in today's code (phone relay → bucket, idle teardown → `ComputeProvider.teardown`, key-safe chat → `_no_secrets`, stale evidence → road hashes). The other 13 start from zero.

### D1. Input 1: USER-JOURNEYS.md

**What it proposes.** 21 journeys (J01-J21), each with a trigger, steps, machinery, FRs, failure paths and DevOps records. It adds a drawer with five panes, chat block names, 25 spin ideas, 17 uncovered steps and a 10-minute demo script.

| Proposal | /how: code it touches (file:line) | Fit | /why: recorded reason | Verdict |
|---|---|---|---|---|
| Chat block names `tools, cards, ask, changes` (§0) | `SessionBlock.type` 14 kinds `ctl/service.py:54-72` names them `tool, question, changed`; no `cards` | Seam: UI labels map onto kinds; `cards` → `panel` or `entity` | Y44: the 14 kinds are the UI contract | RESPECT the code names; journey words are labels only |
| Drawer panes Activity, Artifacts, Diff, Terminal, Browser | No terminal or browser stream; supervisor JSONL logs `apps/supervisor.py:587-638`; `changed`, `artifact` kinds exist | Needs 32's `/live` channel and `panel` with `content.pane` | 24 §1.6: no UI calls these routes yet, so new fields cost no migration | Fits (via 32 B7) |
| J01 QMX home on D: | `default_home()` is `~/.qmx` `ctl/server.py:255-256` | Seam: configurable root | F20, NFR-034 | Fits once the root moves |
| J01/J20 key typed into a QMX secure field → Credential Manager | Only write today is the control token, `keyring.set_password` `ctl/server.py:89`; `settings_put` refuses secret-named keys `ctl/service.py:79-91` | Seam: a new REST-only credential route | Y10, F16; operator rule that creds never pass through chat | Fits as a REST-only door (G1, G15) |
| J02/J03 one errand spans several engine sessions | `sessions` row `{id,title,origin,parent_id}` `ctl/service.py:47-51` | Seam: errand = parent session, engine sessions are children (30's `threads` row is the same idea) | F5: sessions have no status or target | Fits; call it "errand" (PRD glossary), not "thread" |
| J03 operator-driven switch, compaction first | Per-request override `agents/router.py:199-200`; tier switch `agents/copilot.py:112` | Collides with today's code, which the PRD drops | Y17, Y18; K-11 | Fits the PRD |
| J04/J05 app build, fix as new version, revision-bound approval | Road `road/__init__.py:77-146`; `image_hash` `apps/manifest.py:130-139`; signature binds `definition_hash` `ctl/server.py:184-196`; T1 refusal `apps/supervisor.py:139-144` | Needs the F1/F2 fix (host-assigned trust, approval record) | Y28 RESPECT review; Y29 sign door | Fits after F1/F2 |
| J05 app copilot uses the app, never edits it | `AppHooksMiddleware` binding is Bound `agents/guards/hooks.py:120-150` | Seam: per-plugin tool list without `apps_update` | FR-008 | Fits |
| J06 edit while running; the run finishes on the old hash | No local definition hash (pass 1 4.6); remote fingerprint `remote/models.py:82-85` | Seam: 30's `graph_versions` | Y34 | Fits |
| J07/J08 cron on rented compute, PC off | Only timers: maintenance loop `ctl/server.py:152-165`, backup schedule, `AppDefinition.schedule` `apps/manifest.py:80-81` | Collides: 30's `triggers` table sits in the laptop's `control.db`, which is off | Pass 1 4.7: the 60 s loop must not grow into a scheduler | Needs a design (X8) |
| J09 laptop closed, phone checks, $5 approval | Bucket flush `remote/worker.py:72-100`; verified fetch `ctl/service.py:531-559`; teardown on stop, move, failure `remote/runs.py:126`, `158`, `211`, `230` | Partial: no idle teardown, no relay | Y37 DROP owned VPS; Y38 RESPECT result model | Fits with a relay (X9, G10) |
| J10 orchestrator delegating across engines | `SubagentSpec` refs `agents/spec.py:70-79`; child sessions `agents/copilot.py:131-145` | Needs 31's `delegate` and the engine contract | Y06: every helper gets the parent's guards | Fits; depth via X6 |
| J11 depth-1 refusal, watchdog restart | `_NoDelegation` `agents/spec.py:183-187`; no watchdog; RunIndex defaults to `running` (F4) | Partial | Y35 depth 1 | Fits; collides with 31 (X6) |
| J12 Firecrawl off by default, paid, asks | Firecrawl HTTPS guard `ctl/service.py:230-254`; `mcp_configuration` `agents/spec.py:197-243` | Fits | Pass 1 4.16 | Fits |
| J13 sign versus approve | Sign door is apps-only `ctl/server.py:184-196`; `propose_order` `agents/guards/money_path.py:181-238`; `portfolio_proposals` `ctl/service.py:296-298` | Seam: a proposal signature record beside the app signature | Y05, Y29 | Fits; keep signature ≠ approval |
| J14 computer use with a demo lock | Nothing | MISSING | C-11 | Fits (LATER) |
| J15 lesson → gated skill change | Placeholder skills `agents/skills/*/SKILL.md` | MISSING | P20: skills name real tools | Fits; matches 31 §2.4 |
| J16 usage "estimated from local session files" | Journal `model_call` `agents/guards/middleware.py:104-121`; RunIndex cost `ctl/runs.py:86-134` | Collides mildly with 32 rec 9 | FR-049 documented sources only | X10 |
| J17 phone approvals, no owned server | Nothing | MISSING | C-08 | New requirement (X9) |
| J18 two agents on one strategy → variants | `runs/<id>` branch `remote/code.py:32-47`; Library `previous_id` `ctl/library.py:95-96` | Fits | Y20, Y38 | Fits; 30 §6 gives the policy |
| J19 crash, resume, approval still pending | Cancellers `ctl/service.py:106`; tasks `agents/tasks.py:29`; admission `agents/guards/admission.py:62-63`, all in memory | Collides with today's code (F3) | FR-014, FR-104, NFR-010 | Fits the PRD; collides with 32 B5 (X4) |
| J20 provider probe on add | Closed `Provider` Literal `agents/router.py:29-30` | Collides with today's code (F6) | Y15 DROP | Fits the PRD |
| J21 plugin tool code "disabled until reviewed" | App trust values `apps/manifest.py:18`; F1 caller-declared trust | Seam: plugin trust host-assigned (30's `plugins.trust` column) | Y28; F1 | Fits only if trust is never a tool argument |
| Demo 9:00: "buy" on both engines → two refusals | Broker has no order tool `qmx-broker/.../service.py:164-185`; `check_descriptor` `agents/guards/money_path.py:247-279` | Fits; needs the wrapper layer | Y05 | Fits |

**Spin ideas grouped by the seam today's code gives them.**

| Seam in code | Ideas |
|---|---|
| `ComputeProvider.teardown` `remote/providers.py:24`; `place` `remote/models.py:127-139` | 4 (remote loop needs a home), 5 (idle teardown, machines chip), 9 (pre-flight estimate, compute half) |
| `_no_secrets` refusal `ctl/service.py:79-91`, settings only today | 12 (key-safe chat: extend the refusal into a value scrubber on user blocks before storage, as 32 A2.8 proposes) |
| Road hashes and signature `road/__init__.py:77-146`, `ctl/server.py:184-196` | 16 (stale evidence), 25 (cooling-off), 17 (variant tournament via `runs/<id>`) |
| `not_implemented` `ctl/service.py:643-647` | 3 ("what works today" card) |
| Journal and RunIndex `agents/guards/journal.py:36-127`, `ctl/runs.py` | 1 (restart digest), 7 (trial counter), 8 (negative-results ledger), 21 (re-run with a fixed assumption), 24 (node replay) |
| `workflow.v1` kinds `agents/workflows/models.py:11-22` | 6 (watch node: `condition` plus `python` today; a new kind is a format change, so ship a template first), 14 (missed-run policy: no field today), 20 (dry run: needs the SDK fakes, NFR-027) |
| None | 2, 10, 11, 13, 15, 18, 19, 22, 23 |

### D2. Input 2: research 31 (tools, skills, prompts, comms)

**What it proposes.** (a) A `QmxTool` record (effect, idempotency, timeout, size cap, defer, callers, approval) with two generated adapters (Claude in-process SDK MCP, OpenAI `FunctionTool`), FastMCP kept for outside clients. (b) Tool search with a core set of 8-12 tools and a QMX bridge for non-OpenAI providers. (c) A persistent `qmx_python` kernel. (d) A base kit for the OpenAI engine. (e) One skill store, QMX metadata, a lifecycle and an eval gate. (f) Five prompt layers, XML templates, rendered prompt snapshots in CI. (g) One broker with delegate/job, mailbox and board, an envelope, and runaway guards.

| Proposal | /how (file:line) | Fit | /why | Verdict |
|---|---|---|---|---|
| (a) Plain function as the single source, two adapters | 13 plain functions `tools/registry.py:26-271`; one LangChain wrap line `:274-281`; in-process SDK server already used `daemon/native_claude.py:222-280` | Fits: replace one Bound line with two adapters | P09 (PR #34): share recorded domain tools between agents and MCP | RESPECT |
| (a) Adapters in-process for domain tools too | `DomainContext` imports QMB, QMF, QML, QMN `tools/service.py:14-22` | Collides with F18: the quant core lands in every engine host and rented image | F18 | Split: platform tools (sessions, jobs, delegate, board, approvals, apps_call) in-process; domain tools stay behind FastMCP, reached through one in-process proxy that applies policy |
| (a) Effect classes `read/write/external/money` | Act vocabulary `agents/guards/money_path.py:21-60`; `destructive` meta `ctl/server.py:127` | Seam | Y05: no order tool in any tool list | RESPECT with change (G11) |
| (a) Default timeout 60 s | App tool deadline 20 s inside 30 s; a timeout stops the app `apps/supervisor.py:676`, `715-726` | Collides for `apps_call` | Y32 (inferred: protect the host) | G12 |
| (a) `idempotency_key` filled by the caller | No keys anywhere (pass 1 4.6) | Collides with 30, which mints the key in the host | 30 §3.2 | X5 |
| (b) Tool search, core set, QMX bridge | Nothing | MISSING | FR-100 | Fits |
| (c) `qmx_python` persistent kernel | Shell only via a sandbox app `agents/copilot.py:30-51`; Job Object `apps/windows_job.py`; scrubbed env `apps/supervisor.py:390-419` | Seam: run the kernel as a supervised subprocess with the same Job Object and env scrub | `tools/service.py:1` docstring: agents never choose filesystem roots or execution code | RESPECT, scoped: the rule binds domain-tool arguments; the kernel is a separate sandboxed capability whose stub has no money tools |
| (d) Base kit for the OpenAI engine | Nothing | MISSING | FR-133 | Fits |
| (e) Store at `qma/plugins/<p>/skills/` in the repo | Old desk packs in `qmx-agents/plugins/` (F13); QMX home `~/.qmx` | Collides on the name, and on runtime skill writes landing in the repo | FR-032; F13 | X14 |
| (e) Claude plugins via `plugins`/`skills`, `setting_sources=[]` | `setting_sources=[]` `daemon/native_claude.py:261`; lockdown `plugins=[]`, `skills=[]` `:222-280` | Keeps the isolation, drops the lockdown | Y39 RESPECT; Y40 DROP | Fits |
| (f) Five layers; live state in the newest message | Per-turn tier switch `agents/copilot.py:112`; prompt names a plan tier `agents/copilot.md:4` | Collides with code the PRD drops | Y18 DROP; FR-097 | Fits |
| (f) `claude_code` preset for copilots | Native recipe uses a custom prompt and no built-ins | Fits FR-133 | FR-096 bans CLAUDE.md, not the preset | Fits while `setting_sources=[]` stays |
| (f) Rendered prompt snapshots in CI | `just ci` steps `tools/ci.py:23-38` | Seam: one more step | Y45 one gate | Fits |
| (g) Broker job table with MCP-Tasks states | `start_task` family `agents/tasks.py:31-89`; ownership check `:91-93`; `record_work` `ctl/service.py:443-471` | Seam: reuse the four verbs and the ownership rule | Y21: background tasks are QMX-owned | RESPECT; state names collide (X2) |
| (g) Mailbox and board tables "in the QMX database" | Nothing; 30 §4 defines no mailbox or board table | Gap between 31 and 30 | none | Add `messages` and `board_items` to `control.db` (X3) |
| (g) Broker publishes every change as events | `_event` `ctl/service.py:156-169` | Fits | Y43 | Fits |
| (g) Spawn depth 2 | `_NoDelegation` `agents/spec.py:183-187`; workflow default `agents/workflows/models.py:103` | Collides with FR-088 | Y35 depth 1 | X6 |
| (g) Sessions talk across laptop and "the Contabo server" | T2 node runs its own `ControlService` `ctl/node.py:158` | Collides with C-08 | Y37 DROP | X7 |
| (g) Agent messages never count as consent | Admission takes `principal == "operator"` only `agents/guards/admission.py:84-93` | Fits | Y08 | RESPECT |

### D3. Input 3: research 32 (DevOps and UI protocol)

**What it proposes.** (a) Three planes (session log, OTLP traces, content-free health) joined on shared ids. (b) A run record of about 20 fields as an extended `work` row. (c) Storage: blocks, events, runs, approvals and ledger in `control.db`; traces as daily JSONL. (d) Write receipts with read-back, and a `completed_with_warnings` status. (e) A "What it did" card, alerts, retention, redaction, replay. (f) An event envelope of about 30 kinds over the 14 blocks, with the durable channel plus a new unstored `/live` SSE route. (g) An `approvals` table and topic, one answer route, ACP decision kinds. (h) Sub-agents as child sessions. (i) Steer, stop and terminal routes. (j) A per-call usage ledger and limit snapshots.

| Proposal | /how (file:line) | Fit | /why | Verdict |
|---|---|---|---|---|
| (a) Session log is the truth for what the model saw | Blocks `ctl/service.py:121-123`; journal JSONL `agents/guards/journal.py:36-127` | Collides with 30, where `items` are the truth | Y07: the journal is the one evidence writer | X11 |
| (a) OTLP JSONL traces; `set_trace_processors` only | Nothing | MISSING | FR-120; LangSmith is a §2.3 non-goal | Fits |
| (b) Run record as an extended `work` row | `work(kind,id,data)`, `WorkKind = runs|jobs` `ctl/service.py:44`; RunIndex `ctl/runs.py:22-47` | Seam: JSON rows take new fields | P1 | Fits; collides with 30's `runs` table (X1) |
| (c) All durable state in `control.db` | Four tables `ctl/service.py:119-128` | Fits | DESIGN rule zero `rebuild/DESIGN.md:314` | Fits; agrees with X3 |
| (d) Write receipts with read-back | Admission `before_hash`/`after_hash` `agents/guards/admission.py:99-111`; `changed` kind | Seam: reuse the admission hash rule | Y08, Y09 | RESPECT; new status joins X2 |
| (d) Disable Claude Write/Edit or reconcile from `files_persisted` | No wrapper layer | Open | 24 risk 5; FR-133 keeps baseline tools | Reconcile; do not disable |
| (f) New `approvals` topic | `EventTopic` closed Literal `ctl/service.py:43` | Fits: additive | Y44 | Fits |
| (f) `/live` unstored channel, asyncio push | SSE runs a sync SQLite read every 50 ms inside an async generator, without the lock `ctl/service.py:176-198` | Fits, and removes an event-loop stall (G3) | Y43 inferred; FR-130 | RESPECT with change |
| (f) No new block kind in release 1 | 14 kinds | Fits | Y44 | RESPECT |
| (g) Answer route `POST /api/approvals/{id}` | Every `OPERATIONS` row is a REST route and an MCP tool `ctl/server.py:120-129`, `206-213`; sign door REST-only `:184-196` | Collides if added to `OPERATIONS` | Y11 two doors; Y29 sign door | G1 |
| (g) Claude approvals expire when the process dies | Nothing durable today (F3) | Collides with FR-104 | FR-104 WED | X4 |
| (g) Sticky `allow_always` per tool identity | `interrupt_on` per spec `agents/agents/copilot.yaml:12` | Collides with FR-105/108 if unbounded | FR-105, FR-108, C-11 | G14 |
| (h) Child sessions with `parent_id` | `SessionInput.parent_id` `ctl/service.py:46-51`; projection `agents/copilot.py:131-145` | Fits | Y44 | Fits |
| (i) Operator terminal `POST /api/sessions/{id}/terminal` | Nothing | Collides like (g) if exported | Y11 | REST-only, through the sandbox app policy (G1) |
| (i) Stop → `stopping` → `cancelled` | `_cancel` answers 501 once a canceller is lost `ctl/service.py:621-623` | Needs durable cancel | F3 | Fits after F3 |
| (j) Ledger per model call with `cost_source` | Journal `model_call` `agents/guards/middleware.py:104-121` | Seam: the neutral journal writer feeds both | Y14 RESPECT own ledger | Fits; merge columns (X12) |
| Node `control.db` synced on fetch | `ctl/node.py:158`; fetch `ctl/service.py:531-559` | Fits | F17 | Fits; the only cross-host path (X7, G9) |

### D4. Input 4: research 30 (agents and databases)

**What it proposes.** (a) Stay on SQLite with one writer task per file, group commit, a read pool and back-pressure. (b) Fix the WAL-reset exposure on 3.50.4. (c) Four logical files: `control.db` (precious), `agents.db` (journal), `checkpoints.db`, `search.db`, with `memory.db` and `library.db` unchanged. (d) 29 tables (§4.2: 12 in control, 15 in agents, 2 in checkpoints). (e) An effects ledger with host-minted keys and resume rules. (f) Approvals consumed once by CAS. (g) The Library and definitions as git objects in SQLite. (h) Leases, CAS and variants for concurrency. (i) Snapshot-then-rclone; no Litestream on Windows. (j) Numbered migrations, portable SQL behind one `qma_store` module, and a Postgres trigger list.

**Today's schema, for comparison.** `control.db`: `sessions(id,data)`, `blocks(session_id,seq,data)`, `work(kind,id,data)`, `events(seq AUTOINCREMENT,topic,subject,data)` (`ctl/service.py:119-128`). `runs.db`: `runs(id,data)` and `journals(path,digest,…)`, a rebuildable projection (`ctl/runs.py:1`, `22-28`). `library.db`: `items(id,data)` with a fetched-source unique index, `search` FTS5, `links`, `memo` (`ctl/library.py:36-44`). Memory: LangGraph `SqliteStore` at `copilot/memory.db` and `apps/<id>/memory.db` (`agents/memory.py:201`, `206`). Every row except FTS is a JSON blob. Migrations are `CREATE TABLE IF NOT EXISTS` in each constructor plus one hand move inside `BEGIN IMMEDIATE` (`ctl/service.py:129-149`). There is no `user_version` and no numbered file.

| Proposal | /how (file:line) | Fit | /why | Verdict |
|---|---|---|---|---|
| (a) One writer per file | New connection per call: `_connect` `ctl/service.py:152-154`, `Library.connect` `ctl/library.py:63-64`, `RunIndex.record` `ctl/runs.py:31`; writers serialise on an `RLock` `ctl/service.py:105` and `Library.lock`; `events()` reads unlocked `:176-181` | Seam: the RLock already serialises writers inside one process | DESIGN rule zero: one writer *process* per file `rebuild/DESIGN.md:314` | RESPECT; tighten to one writer connection |
| (b) WAL-reset bug on 3.50.4 | Confirmed this pass: Python 3.14.6 bundles SQLite 3.50.4. FastAPI runs the sync service methods on a thread pool (`ctl/server.py:206-213`), maintenance uses `asyncio.to_thread` (`:155-159`), SSE opens its own connections | Exposure is reachable in principle (INFERRED); never observed | none recorded | Fix first (G2) |
| (c) `agents.db` holds sessions, items, runs, events | Sessions, blocks, events in `control.db` | Collides with 30's own outbox rule (§3.1): an approval in `control.db` and its event in `agents.db` cannot commit together | Y43; G7 | X3 |
| (c) `memory.db` "exists, leave as is" | The file is a LangGraph `SqliteStore` `agents/memory.py:31`, `214-230` | Collides with C-06 | Y25 DROP store, RESPECT one file per profile | G5 |
| (c) `runs.db` described as a backtest and research index | It is the agent and workflow run projection over P08 journals `ctl/runs.py:1`, `60` | Misread in 30 | Y07 | G4 |
| (d) Typed columns, UUIDv7, `version` CAS column | JSON-blob rows everywhere | Seam: CAS and lease claims need real columns | `rebuild/DESIGN.md:515`: no data migration, old stores held only test data (the inferred reason no framework exists) | G6 |
| (d) `threads` table | `sessions` plus `parent_id` | Seam | PRD glossary says "errand" | Fits under the name errand |
| (d) `sdk_transcript_entries` (Claude `SessionStore` mirror) | Claude writes its JSONL under `CLAUDE_CONFIG_DIR` `daemon/native_claude.py:121` | Optional | FR-119 asks for export, not a mirror | Defer; the native JSONL is the transcript in release 1 |
| (e) Effects ledger, key `run:node:seq`, intent before the call | Journal hashes args, writes `tool_start`/`tool_end` `agents/guards/middleware.py:85-202`; no keys | Seam: the journal already records intent and outcome; the table adds the claim | FR-061, NFR-010; J19 steps 2 and 4 | RESPECT; it is J19's backbone |
| (f) Approvals consumed once by CAS | In-memory `_staged`/`_approved` `agents/guards/admission.py:62-63` | Fits | Y08: exact content plus before-hash | RESPECT; CAS on `status` and the content hash |
| (f) Orders `irreversible` until cTrader dedupe is verified | No order tool exists | Fits trivially for agents | Y05, C-11 | RESPECT |
| (g) Git objects in SQLite for Library and definitions | `artifacts/<sha256>` with a hash check `ctl/library.py:51`; `previous_id` versions `:95-96`; `links` table | Half built | 24 A2-A3; DESIGN §7.6b | RESPECT; Library is out of QMA v2 scope, so only `graph_versions`/`graph_refs` land now |
| (h) Leases, CAS, variants | `runs/<id>` branches `remote/code.py:32-47` | Fits | Y20 | RESPECT |
| (i) No Litestream on Windows | Litestream replicas read from the `providers` section on T2 `ctl/service.py:759-776` | Fits | `rebuild/DESIGN.md:308`: Litestream only on Linux nodes | RESPECT |
| (i) Snapshot before rclone | Backup uses the SQLite backup API (30 cites `backup.py:141`) | Fits | FR-116 | RESPECT |
| (j) Numbered migrations, one `qma_store` module | SQL spread across `service.py`, `library.py`, `runs.py`, `memory.py` | Seam | DESIGN :515 (inferred) | `PRAGMA user_version` plus numbered steps before the first new table |
| (j) Postgres trigger A, "the planned Contabo server" | none | Collides with C-08 | Y37 DROP | X7 |

### D5. Conflicts and recommended resolutions

**X1. Where a run lives.** 32: an extended `work` row in `control.db`, where a run is a turn, workflow, node, job or app action. 30: a precious `runs` table in a new `agents.db`, `graph_id NOT NULL`, so only graph executions count. Code: `work` plus the rebuildable `runs.db` projection. *Resolution.* One run record of any kind, as 32 defines, stored in `control.db`. `work(kind='runs')` becomes that row. `runs.db` stays a derived index rebuilt from journals. The name `runs` is not reused for a second precious table.

**X2. One status vocabulary.** Code: `record_work` terminals `complete, completed, failed, cancelled, canceled, stopped` (`ctl/service.py:456-463`) and the workflow runner's seven values (pass 1 4.6). 31: `working, input_required, completed, failed, cancelled`. 32: `queued, running, waiting_approval, stopping, completed, completed_with_warnings, failed, cancelled, interrupted`. 30: `queued, running, waiting, succeeded, failed, cancelled`. *Resolution.* 32's nine values are the one enum; they include `interrupted`, which F4 needs. MCP-Tasks names appear only at the broker's tool edge. The `canceled` and `stopped` spellings are deleted in the same wave that migrates their callers.

**X3. How many database files.** 30: four files, with `events` in `agents.db`. 32: all durable state in `control.db`. 30 also requires the outbox (state change and event in one transaction). *Resolution.* Release 1 keeps one `control.db` for everything that emits UI events: sessions, blocks, runs, approvals, effects, ledger, triggers, plugins, graph versions, messages, board items and events. One writer task owns it. Split off only stores that emit no events: `checkpoints.db` now, `search.db` and a transcript mirror only if built. Move hot rows to `agents.db` only when the 40-agent load test (NFR-009, 30 rec 13) fails. Per **principle-separate-before-serializing-shared-state**, remote runs and apps already own their files, so `control.db` is the one shared target left, and a single writer serialises it structurally.

**X4. Approvals across a restart.** FR-104 (WED) and J19 step 5: a pending approval survives and stays answerable. 32 B5: a Claude approval whose process died becomes `expired` and its run `interrupted`. *Resolution.* The row stays `pending`. Answering it after a restart resumes the session by id (Y20). The tool call is re-issued under the same effect key, and the decision is consumed once by CAS (30 §3.2 step 5). The UI says the turn restarts from its last saved point. `expired` is kept for real timeouts and for late phone answers (J17).

**X5. Who mints the idempotency key.** 31: each write tool takes an `idempotency_key` argument. 30: the host mints `run_id:node_id:call_seq` before the call. *Resolution.* The host mints it and records intent. Tools receive it in context, not as a model-filled argument; 31's own source [O5] says not to make the model fill values code already knows. Keep two fields: 31's `effect` (policy reach: read, write, external) and 30's recovery class (idempotent, keyed, unkeyed, irreversible).

**X6. Spawn depth.** 31: depth 2 (copilot → orchestrator → worker). FR-088 (WED), Y35, J11: depth 1, and sub-agents do not spawn by default. J10 needs an orchestrator that delegates. *Resolution.* The orchestrator is an errand session started through `delegate(mode="async")` as a peer job, not a sub-agent. Its workers are depth 1. Nothing below an errand spawns. FR-088's acceptance check still passes.

**X7. The Contabo server.** 31 §4.5 routes session messages "across the laptop and the Contabo server". 30's Postgres trigger A assumes "the planned Contabo server". C-08 and K-01 removed any owned agent server; the trading node belongs to QMN and is not an agent host. *Resolution.* Strike both mentions. Cross-host traffic is the qmx-remote bucket plus verified fetch (Y38) and the relay in X9. Postgres trigger A has no live case in QMA v2.

**X8. Schedules while the PC is off.** J07 and J08 run cron on rented compute with the laptop off. 30 keeps `triggers` with leases in the laptop's `control.db`, so nothing fires while it is off. *Resolution.* `triggers` stay in `control.db` as the source of truth. A trigger placed `remote` is pushed as a bundle to a provider-native scheduler. Its fires come back on fetch and land in `trigger_fires` by `fire_key`. The missed-run policy (spin 14) decides gaps. FR-111's setup verify must check that each rented provider has a scheduler.

**X9. Phone approvals without a server.** J17 and spin 11 versus C-08; 32's approvals table sits on a laptop that may be off. *Resolution.* A bucket mailbox. The remote run writes the request into its bucket prefix and parks. A phone client answers into the same prefix with a device-bound, expiring token. The laptop imports both on fetch into the one `approvals` table. Money signatures stay desk-only (J17 step 4; Y29). This is a new requirement and needs an operator call on the push service, which costs money.

**X10. Usage from local session files.** J16 step 5 labels some numbers "estimated (from local session files)". 32 rec 9 forbids parsing Claude JSONL for QMX runs, and FR-049 allows documented sources only. *Resolution.* QMX runs feed the ledger from SDK `result` and usage objects at call time. "Estimated" means `cost_source=modelPriced`, not file parsing.

**X11. One truth for what the model saw.** 32: blocks (the Cordis rule). 30: `items` in `agents.db`. Code: blocks (UI) plus RunJournal JSONL (evidence, Y07). *Resolution.* Release 1 keeps two stores, each with one job. RunJournal stays the evidence and replay truth, extended with request header and context hashes so 30's "model-visible means logged" test can run on it. Blocks stay the UI projection. No `items` table until a feature needs a query the journal cannot answer, per **principle-laziness-protocol**. OpenAI-engine sessions use the SDK's own SQLite session file under the QMX home.

**X12. Ledger columns.** 30 and 32 agree the usage ledger lives in `control.db`. 30 lacks `engine`, `where`, `agent_path`, `speed`, `dedupe_key`. 32 lacks `pricing_version`, `request_hash`. *Resolution.* Take the union. Make `dedupe_key` unique, because Claude's `result` is cumulative and 32 C2 records deltas.

**X13. Approval decision words.** FR-104: ask, allow once, allow for session, remember. 32: ACP's `allow_once, allow_always, reject_once, reject_always, cancel`. 30: statuses `pending, approved, denied, expired, consumed`. *Resolution.* Decisions use FR-104's words mapped onto ACP (`remember` = `allow_always`, plus `allow_for_session`). Status uses 30's set. Both sit in one row.

**X14. Skill locations.** 31 puts the canonical store in the repo. FR-032 wants a QMX-only home, and J15 writes skills at runtime. *Resolution.* Shipped defaults live in the repo under a new path. Every runtime write (operator, agent, self-improvement) goes to the QMX home in the same layout. The loader reads both, and the home wins by name. The old `qmx-agents/plugins/` is deleted before the loader lands (F13).

### D6. New facts the architecture must not get wrong

**G1. Two doors means agents can call every operation.** Every `OPERATIONS` row becomes a REST route and an MCP tool (`ctl/server.py:120-129`, `206-213`). The only exception is the sign door, documented as "Operator-only door: never exported as an agent MCP tool" (`ctl/server.py:184-196`). The approval answer route, the credential write route (J20) and the operator terminal route (32 B7) must be built the same way, outside `OPERATIONS`. Otherwise an agent can approve its own request, the same flaw as F1.

**G2. SQLite 3.50.4 and connection churn.** Python 3.14.6 here bundles SQLite 3.50.4, which predates the WAL-reset fix (3.51.3; backport 3.50.7) (30 §2.2; version re-checked in this pass). `qmx-control` opens a new connection per call in `_connect`, `Library.connect` and `RunIndex.record`. Writers serialise on the RLock, but `events()` reads without it from every SSE stream every 50 ms, and thread-pool handlers and `to_thread` maintenance open their own connections. Do both fixes: one writer connection per file, and a start-up assertion on `sqlite3.sqlite_version`.

**G3. The SSE loop blocks the event loop.** `stream()` calls the sync SQLite read inside an async generator every 50 ms per open stream (`ctl/service.py:187-198`). With several streams and in-process OpenAI agents on the same loop, every stream stalls them. The `/live` channel must be asyncio push, and the durable tail must read off the loop.

**G4. `runs.db` is derived, not precious.** Its docstring reads "Rebuildable run projections over immutable P08 journal records" (`ctl/runs.py:1`), and it is rebuilt from `journals/**/*.jsonl` (`:60`). Run truth written only into `runs.db` is lost on rebuild.

**G5. The memory file is a LangGraph store.** `copilot/memory.db` and `apps/<id>/memory.db` are `SqliteStore` files that run their own migrations (`agents/memory.py:201`, `206`, `217`). Research 30's "leave as is" would keep LangGraph alive. Keep the paths and replace the store.

**G6. Rows are JSON, but claims need columns.** Every table today is `(key, data JSON)`. CAS on approvals, lease claims on jobs and triggers, and sums over the ledger need typed `status`, `version`, `lease_until` and token columns. The first such table must bring `PRAGMA user_version` and numbered migrations with it. Keep JSON documents for rows that are only displayed.

**G7. The outbox only works inside one file.** `_event` writes the event inside the caller's transaction (`ctl/service.py:156-169`), and `Last-Event-ID` is one integer `seq`. Splitting event-emitting tables across files breaks both (X3).

**G8. `aggregates` crosses files inside a transaction.** `_event` calls `_aggregate_counts`, which opens `runs.db` while the `control.db` transaction is open (`ctl/service.py:420-423`). A single-writer design must move that read out of the write transaction.

**G9. Remote runs cannot call the laptop.** Research 30 §2.3 rule 6 has remote nodes call the qmx-control API. With rented compute and the lid closed (C-08, J09) there is nothing to call. Remote runs write their journal and files into the bucket (`remote/worker.py:72-100`), and the laptop imports them on verified fetch as new rows, never merged (Y20, Y38).

**G10. Teardown exists; idle teardown does not.** `ComputeProvider.teardown` exists and runs on stop, move and failure (`remote/providers.py:24`; `remote/runs.py:126`, `158`, `211`, `230`). There is no idle timer and no live machine count. Spin 5 is a timer plus a list, not a new provider verb.

**G11. `money` is not a tool effect.** Research 31's `effect=money` puts a money-labelled tool in a registry agents can see. Y05 says no order tool appears in any tool list. The registry lint must refuse `effect=money` on every agent-visible tool. `propose_order` is a `write` into the proposal queue.

**G12. App tool calls keep 20 s.** Research 31's 60 s default must not reach `apps_call`, where a timeout stops the app (`apps/supervisor.py:676`, `715-726`; Y32). Host tools may take 60 s. Anything longer becomes a job.

**G13. The journeys' block names are labels.** `tools`, `ask`, `changes` and `cards` do not exist in `SessionBlock` (`ctl/service.py:54-72`). The UI maps them onto `tool`, `question`, `changed` and `panel` or `entity`. Renaming a kind breaks Y44.

**G14. Sticky approvals have three hard limits.** An `allow_always` decision (32 B5) never covers an always-ask action (FR-105), a deny-listed action (FR-108) or anything touching money (C-11). Research 32 left this as an open question. The PRD already answers it.

**G15. No credential write route exists.** The only `keyring.set_password` call writes the control token (`ctl/server.py:89`). J20's secure field needs a new REST-only route that writes a `qmx/*` entry and returns only the reference. `settings_put` keeps refusing secret-named fields (F16).


## Delta pass 3 (architecture revision 2) and fix verification

Written 2026-10-12. Input: `ARCHITECTURE.md` revision 2 (commit 32806d83; `git diff 00a1d1b5 32806d83`), its §10 log, `ARCHITECTURE-CHECK.md`, `reviews/review-opus.md`, `reviews/review-sonnet.md`. Code read with `git show` on `origin/rebuild/base` @ 9ab4c884 (PR #69). Since delta 2's a82f5897 the only code change is the deletion of `qma-wire`'s copilot-profile DTO (4 files, -260 lines), so every earlier citation still holds. Same method as passes 1 and 2: one agent, no sub-agents, planning only. `l.N` is an `ARCHITECTURE.md` line. Paths use the pass-1 keys (`ctl/`, `apps/`, `agents/`, `tools/`, `remote/`). Why sources: git log, `gh pr view` bodies (#32, #42, #43, #46, #49), `rebuild/DESIGN.md`, `rebuild/packets/P08, P11, P22`. No issue, chat, observability or analytics MCP is connected, and the GitHub MCP failed to connect, so `gh` was used.

### E0. Summary in plain words

1. Revision 2 fixes most of what the three reviews asked for, on paper. Of 60 BLOCKER and MAJOR findings checked, 49 are VERIFIED, 11 are WEAKENED, and none is NOT FIXED.
2. The biggest hole the reviews missed is in today's code. The control token is also the HMAC key that signs money-app publishes (`ctl/server.py:147`; PR #42 body). Any agent that reads `qmx/control-token` can forge the operator's signature without touching the sign door. `PrincipalGate` alone does not close this.
3. Example apps already ask for that token as an app secret (`examples/apps/macro-daily-bias/app.toml`, `QMX_DATA_TOKEN = "qmx/control-token"`), and the supervisor hands it over (`apps/supervisor.py:411-417`).
4. The operator secret is "printed once into the launch window", but `qmx-control start` sends stdout to `control.log` (`ctl/__main__.py:57-73`) and QMB's `control_host` captures it (`qmb/src/qmb/doors/cli/host.py:1821-1828`). Neither launch path has a window.
5. The protected settings list misses four live sections: `backup`, `brokers`, `mcp_servers` and `providers` (`ctl/service.py:40-42`). An agent could still repoint the weekly backup or edit broker connections.
6. Settings live in `settings.toml`, not a table (`ctl/service.py:200-294`; DESIGN §7.6b), and `qmx-broker` reads that file directly (`qmx_broker/service.py:121`). Revision 2 puts `settings` in `control.db` (l.598), which breaks both.
7. Packet 0's "audit `qmx-tools` for `control.db` access" already has its answer. `DomainContext` builds a full `ControlService` inside the FastMCP child and writes events through it (`tools/service.py:126-136`). With the new OS lock that child either fails to start or becomes a second writer.
8. On Windows the Claude SDK spawns the CLI itself, and its `user=` option is POSIX-only (`claude_agent_sdk` 0.2.163 `subprocess_cli.py:873-881`). Running Claude as `qmx-agent` (Q10) inside a host Job Object needs a custom `Transport` or a `cli_path` shim. Neither is named, and P5 does not probe it.
9. Many new elements fit the code as it stands. The remote lane already resolves keys at launch and passes them to the provider (`remote/runs.py:104-131`). Modal and E2B already get a TTL from `Resources.timeout` (`remote/models.py:48`). `ClaudeSDKClient` accepts a custom transport, the clean home for `ClaudeReplayAdapter`.
10. GitHub Actions is already enabled on this public repo and all six workflows are `active`, yet the repo has 0 runs (measured with `gh api` in this pass). Homework item 1 will pass and unblock nothing.

### E1. Touchpoints

Verdict key. **Fits** means the element lands as written. **Seam** means it fits once one named adapter or change is added. **Collides** means the element as written contradicts code or a recorded rule.

| # | New or changed element | Existing code it touches | Verdict | What is needed |
|---|---|---|---|---|
| T1 | `PrincipalGate` replaces `BearerGate` (l.584) | `ctl/server.py:93-117` (`BearerGate`), `:178-182` (`authenticate`), `:206-213` (every row gets the same dependency), `:238` (middleware); `ctl/__main__.py:38`, `:83`, `:118` (start and status call `/api/health` with the token); `ctl/node.py:153` (T2 per-node token) | Seam | The swap is local to `server.py`. `/api/health` must stay callable by the launcher, so make it pid-only and token-free. Say what the T2 node token resolves to |
| T2 | Operator credential, per launch, "printed once into the launch window" (l.580) | `ctl/__main__.py:57-73` (`start` sends stdout and stderr to `control.log`, `CREATE_NO_WINDOW`); `qmb/src/qmb/doors/cli/host.py:1799-1828` (`control_host` captures output) | Collides | No launch path has a window. Printing into `control.log` puts the secret in a file every same-user process reads. Name the hand-off |
| T3 | Operator secret vs the road signing key | `ctl/server.py:146-147` (`road.signing_key(token)`); `apps/road/__init__.py:29-30`, `:152-175`, `:237-247` (HMAC over app, hash and action) | Collides | Today the signing key is the vault token. Revision 2 never says what it becomes. It must become the operator secret, and `qmx/control-token` must leave the laptop's Credential Manager |
| T4 | "Optionally DPAPI-wrapped for the UI lane" (l.580) | none | Collides with its own goal | DPAPI's CurrentUser scope decrypts for any process of the same user, so it is no barrier before Q10 (platform fact) |
| T5 | Agent token "passed only in the session's MCP server config" (l.581) | `ctl/server.py:120-129` (`create_mcp`: "in-process and stdio callers are trusted"); revision 2's Claude `mcp_servers` holds only the in-process `qmx` SDK server (l.318) | Seam | Name the MCP server that carries the agent token. The in-process SDK server and the OpenAI in-process tools never present a token, so it matters only for HTTP callers |
| T6 | App token minted at app start (l.582) | `apps/supervisor.py:411-418` (every manifest secret is read from the vault by `qmx/*` label); `examples/apps/macro-daily-bias/app.toml`, `examples/apps/mql5-articles/app.toml` (both request `qmx/control-token`) | Seam | The per-app token needs an injection path that is not a vault label, and the supervisor must refuse `qmx/control-token` in any manifest |
| T7 | Operator-only `settings_put_protected` for `approvals, deny, accounts, seats, budgets, remote` (l.584) | `ctl/service.py:40-42` (sections `providers, mcp_servers, budgets, memory_provider, backup, brokers, remote`), `:220-294` (`settings_put` validates `remote`, `mcp_servers`, `backup`, `brokers`); `ctl/server.py:74-75` | Collides | `backup` (destination repo), `brokers` (accounts and connections), `mcp_servers` and `providers` stay agent-writable. §3.2 keys say `budget.*` and `seat.*`, while the protected list says `budgets` and `seats` |
| T8 | Settings as a `control.db` table (l.598; migration 001 at l.769) | `ctl/service.py:200-294` (TOML file, atomic replace); `qmx_broker/service.py:121` (reads `brokers` from the TOML); `ctl/backup.py:113` (backs up `settings.toml`) | Collides | Keep `settings.toml` with the host as its one writer, or move all three readers in the same packet |
| T9 | `sessions_append` refuses `permission`, `needs_you`, `user` from agents (l.581) | `ctl/service.py:324-335` (no caller identity); `ctl/server.py:123-128`, `:206-213` (rows bound straight to service methods) | Seam | The check needs the principal inside the service call. Name the plumbing for both doors (a FastAPI dependency and the FastMCP request context) |
| T10 | Package `qma2`, dist `qma-v2`; `qma` stays a namespace (l.33, l.667) | `qmx-agents/pyproject.toml` workspace members (`qma-core`, `qma-wire`, `qma-daemon` still listed); `qmb/src/qmb/doors/cli/host.py:104` (`DAEMON_SPAWN_MODULE = "qma.daemon"`); PRs #58 to #70 (P16c in flight) | Fits | No `qma2` exists anywhere. `import-linter` is in no lockfile, so packet 0 adds it to the dev group. Whether import-linter can forbid a PEP 420 namespace root is unverified (guess) |
| T11 | One writer thread per file, `SAVEPOINT` per `Write`, group commit (l.250-264) | `ctl/service.py:105` (RLock), `:152-154` (`_connect`, 22 call sites), `:118-149` (DDL in the constructor); `ctl/runs.py` (`RunIndex.record`) | Seam | Every `ControlService` method is sync and runs in FastAPI's thread pool. `Store` offers only `async def write`. Add a blocking submit for thread callers |
| T12 | OS file lock for the process lifetime (l.262, l.610) | `tools/service.py:126-128` (`DomainContext` builds `ControlService(self.root)` in the FastMCP stdio child), `:131-136`, `:225-227` (writes through it); `ctl/__main__.py:35-37` (`weekly-backup` builds a `ControlService`, which runs DDL) | Collides | The audit's answer is known. Packet 0 must change `qmx-tools`: Library writes go to `Library` directly or through the host, and events through the host. `qmx-tools` is not in packet 0's file list |
| T13 | Backup as a host request; `quick_check` before backup (l.610) | `ctl/backup.py:135-145` (already opens the source `mode=ro` and runs `integrity_check` on the copy); `:18-26` (`DATABASES` omits `control.db`); `:17` (95 MB cap) | Fits, with a gap | The read-only part is already true. `control.db` is not backed up at all today, and revision 2 now puts approvals, accounts, graph versions and checkpoints there |
| T14 | Checkpoints inside `control.db` (l.511, l.598, l.606) | `agents/workflows/runs.py` (`AsyncSqliteSaver` per workflow, to be deleted); `remote/worker.py:28` (`AsyncSqliteSaver`); `remote/runs.py:196-216` (`resume` needs `manifest.checkpoint` from the bucket) | Seam | A rented box has no laptop `control.db`. Name how the headless worker exports checkpoint rows under the manifest's `checkpoints/` prefix so `RemoteRuns.resume` still works |
| T15 | `recover()` step 1 kills `claude` processes by `CLAUDE_CONFIG_DIR` (l.531) | `ctl/__main__.py:131-134` (ownership by pid plus `create_time`); `ctl/service.py:106` (in-memory cancellers, F3) | Seam | Reading another process's environment works for same-user processes. Under Q10 the children run as `qmx-agent`, and the host cannot read their environment. Record pid and `create_time` per session and match on those |
| T16 | Claude child in a kill-on-close Job Object, as `qmx-agent` when Q10 is yes (l.311, l.586) | `claude_agent_sdk` 0.2.163 `_internal/transport/subprocess_cli.py:873-881` (`anyio.open_process(..., user=options.user)`; `user` is POSIX-only); `types.py:2099` (`cli_path`) | Seam, unprobed | The SDK owns the spawn. Use a custom `Transport` or a `cli_path` shim in `host/platform.py`, or put the whole host in a Job Object so every descendant inherits it. Add both to P5 |
| T17 | Remote self-terminate, exit on approval (l.545-546) | `remote/models.py:44-48` (`Resources.timeout = 3600`); `remote/providers.py:200-222` (Modal sandbox `timeout`), `:282-284` (E2B `timeout`); `remote/worker.py:354-357` (SIGTERM handler) | Fits | The provider TTL already exists and comes from the bundle. `max_lifetime_min` should map onto `Resources.timeout`, not a second field |
| T18 | Keys through the provider's secret store via `setup_verify` (l.542) | `remote/runs.py:104-131` (resolve `credentials_scope` from the vault at launch, pass to `provider.start`, then `credentials.clear()`); `remote/providers.py:221` (`Secret.from_dict`), `:284` (`envs=`) | Fits; duplicates | Launch-time injection already keeps keys out of the bundle and the bucket. A persistent provider secret written by `setup_verify` is a second copy. Prefer the existing path |
| T19 | `answer_remote` relaunches from saved state with a decision file (l.541) | `remote/runs.py:196-216` (`resume` reuses the bucket request, needs a verified checkpoint, re-places, calls `_launch`) | Seam | Add the decision file to the staged request before `_launch` |
| T20 | `price_per_minute` on `RemoteLimits` (l.544) | `remote/models.py:100-111` (`Target` has no price); `:122-124` (`default_target = "vps"`) | Seam | Name where the price lives (a `Target` field in the `remote` section) and which packet sets it |
| T21 | Router family guard (l.450-453) | `agents/router.py:29-30` (`Provider` Literal), `:40-52` (`model_selector` refuses aliases, Y16) | Fits | The `qma.toml` example `default = "claude:opus"` (l.359) is an alias, which Y16 refuses. The `gpt-*` and `openai/*` patterns also block open-weight `gpt-oss` on key providers (inferred) |
| T22 | Wednesday console at `/console`, served by `qmx-control` (l.642) | `ctl/server.py:238` (the gate wraps every route); `:215-228` (SSE needs the `Authorization` header); `:239-251` (CORS for the UI origin) | Seam | A browser cannot send a header on navigation or through `EventSource`. Serve the static page outside the gate and read SSE with `fetch` streaming. Never put the token in a query string |
| T23 | UI handoff `openapi.json` (l.644) vs packet 1b "`openapi.json` lacks the doors" (l.770) | P11 packet: "The OpenAPI document is generated and used by the UI" | Collides | The UI must call the approval door, so the handoff must document that route. Publish a second, operator-only schema or tag the doors |
| T24 | `scripts/operator_setup.py` (l.748-756) | `ctl/server.py:89` (the only vault write today); `remote/providers.py:184-185` (`qmx/modal-token-id`, `qmx/modal-token-secret`), `:265` (`qmx/e2b`); `native_claude.py` recipe (Y39) | Fits | Use exactly those labels. Homework 1 checks something already true (T29) |
| T25 | FastMCP proxy for domain tools and non-first-party MCP; effect key as `_meta` (l.178, l.413) | `tools/servers.py:9-22` (plain functions registered with `server.tool`); fastmcp 4.0.11 `create_proxy` and `Client.call_tool(meta=...)` (installed); `ctl/service.py:208-254` (Firecrawl is a remote HTTP MCP) | Seam | The proxy side exists in the library. The domain servers must read `_meta` from the request context to use the key, which changes `servers.py` |
| T26 | `normalise_tool_name` (l.393) | `agents/guards/money_path.py:128-138` (`_normalize_act_token` strips role prefixes, never `mcp_<server>_`) | Fits | Today `mcp__qmx__place_order` normalises to `mcp_qmx_place_order` and is not denied. Call `normalise_tool_name` before `match_money_path_act` |
| T27 | `ClaudeReplayAdapter` (l.331-333, l.638) | `claude_agent_sdk/client.py:67-85` and `query.py:15` (a custom `Transport` is accepted) | Seam | A replay `Transport` under the real `ClaudeAdapter` exercises hooks and `can_use_tool` too. Revision 2 says only `engine.claude`, `claude_replay` and `openai` import an SDK (l.68), while `events/normalise_claude.py` reads SDK types (l.638). One rule must change |
| T28 | Packets, acceptance commands and lanes (§8.1) | `tools/ci.py:12-38` (no arguments; fixed workspace list); `tools/test_all.py` (runs all of `qmx-agents/packages`) | Seam | `tools/ci.py --workspace qma-v2` (l.768) uses a flag that does not exist. Packet 0 adds it, plus the new workspace's `poe` tasks |
| T29 | "`battery.yml` exists and has never run"; homework 1 "Actions enabled?" (l.706, l.750) | `.github/workflows/battery.yml:3-8`, `:26` (rebuild branches, 60 min); `gh api .../actions/permissions` gives `enabled: true`; `.../actions/workflows` gives 6 workflows, all `active`; `.../actions/runs` gives `total_count: 0` | Collides | The premise is wrong. The repo is public, Actions is on, and nothing has ever run. Packets cannot carry an Actions link. Use a local `just ci` log as the gate until the cause is found |

### E2. Why: recorded reasons, RESPECT or DROP

| # | Recorded reason, with source | Element it meets | Verdict |
|---|---|---|---|
| Z1 | "Both HTTP doors and OpenAPI require the Credential Manager bearer token" (PR #32 body; P11 "stored in Credential Manager as `qmx/control-token`") | T1, T2 | DROP for the operator, because every same-user process reads the vault (review-opus 1; G1). RESPECT for the T2 node's per-node token (P17), which no agent shares a user with |
| Z2 | "The existing local bearer token is the signing key; authenticated REST alone exposes the signing door, and MCP has no signing tool" (PR #42 body) | T3 | DROP the key choice. RESPECT the door rule. The key must move to the operator secret, or the door is decorative |
| Z3 | "The local token replaces pairing" (DESIGN §12c.1; PR #49 removed `pair` and `rotate-control`) | T1, T5, T6 | DROP in part. Scoped credentials come back without the pairing ceremony |
| Z4 | Settings get and put serve "both the UI and the Copilot" (P11 Goal and Build) | T7 | DROP for protected sections (FR-104, C-11). RESPECT for the rest |
| Z5 | "The OpenAPI document is generated and used by the UI" (P11) | T23 | RESPECT. The operator doors need a documented schema |
| Z6 | Start, authenticated health and stop with "process-ownership checks" (PR #32; `ctl/__main__.py:86-101`, `:131-134`; QMB `control_host` docstring) | T1, T15 | RESPECT. Keep pid plus `create_time` ownership, and reuse it in `recover()` |
| Z7 | "Each file has exactly one writer process, and everyone else reads it or asks the owner through `qmx-control`" (DESIGN §7.6b); "One writer per file" (P08) | T11, T12 | RESPECT |
| Z8 | "Domain tools use the shared service" (PR #43 body; commit 9ba5d12c) | T12 | DROP. A `ControlService` in the tool child breaks Z7 and the new lock |
| Z9 | Settings are `settings.toml`, owned by `qmx-control`, backed up weekly to GitHub (DESIGN §7.6b) | T8 | RESPECT. Revision 2 gives no reason to move them |
| Z10 | Weekly backup of small stores, 95 MB cap, `integrity_check` on the copy (P22; PR #43 body; `ctl/backup.py:17-26`) | T13, T14 | RESPECT. Decide whether `control.db` joins `DATABASES`. Checkpoints in it then need pruning under the cap |
| Z11 | Keys resolved at launch, passed to the provider, cleared after (PR #46 body; `remote/runs.py:104-131`); "Run bundles and placement settings contain references, never credentials" (`remote/models.py:1`) | T18 | RESPECT. It already meets FR-046 |
| Z12 | `Resources.timeout` drives the provider sandbox lifetime (P21; `remote/providers.py:222`, `:284`) | T17 | RESPECT. It is the provider TTL revision 2 asks for |
| Z13 | Owned VPS as the default target (P21 §0; `RemoteSettings.default_target = "vps"`) | T17, T20 | DROP (C-08, K-01; already Y37) |
| Z14 | `model_selector` refuses `latest` aliases (Y16) | T21 | RESPECT. Fix the `claude:opus` example |
| Z15 | Money-path tokens normalised with role prefixes and aliases (PR #35; `money_path.py:70-138`) | T26 | RESPECT. Put `normalise_tool_name` in front |
| Z16 | `qma.daemon` stays a QMB anchor until the QMB review; no compatibility bridge (DESIGN §12c.1; PRD §2.2) | T10 | RESPECT. `qma2` avoids the shadowing |
| Z17 | One sequential runner for `just ci` and GitHub (PR #29; Y45) | T28, T29 | RESPECT. Extend `tools/ci.py`; add no workflow |
| Z18 | CORS limited to the UI origin (P11; `ctl/server.py:239-251`) | T22 | RESPECT. The console is same-origin and needs no new CORS entry |
| Z19 | Fakes in tests, live calls only in `scripts/live/` (Y22) | T27 | RESPECT. A replay transport keeps CI off the network |

### E3. Fix verification

Rule. VERIFIED means `ARCHITECTURE.md` names the module, type, table, route or packet that delivers the fix. WEAKENED means it is named but a gap, a contradiction or a code fact undercuts it. NOT FIXED means it is absent. `ARCHITECTURE-CHECK.md` grades S1 to S4, so S1 is read as BLOCKER and S2 as MAJOR. S3, S4 and every MINOR are out of scope.

| Finding | Severity | Verdict | Where (l.N) and why |
|---|---|---|---|
| CHECK 1 shell bypass of doors and money | BLOCKER | WEAKENED | l.574-588, l.723. Gate, three credentials, deny patterns, Q10 and both FR-102 shell tests are named. Undercut by T2 (secret lands in `control.log`), T3 (the vault token still signs money publishes) and T4 (DPAPI) |
| CHECK 2 double claim on Claude | BLOCKER | VERIFIED | l.399, l.426 ("the ONLY claim"), l.562. `_pre` only decides (l.322-325) |
| CHECK 3 effect key across resume | BLOCKER | VERIFIED | l.435-436: engine-native ids and a persisted node attempt |
| CHECK 4 `defer` single-call premise | BLOCKER | VERIFIED | l.98, l.325, P3c at l.742. The FR-109 citation is gone |
| CHECK 5 checkpoint atomicity | BLOCKER | VERIFIED | l.511, l.598, l.606 (P4 fallback with the order rule). Remote checkpoints are a separate gap (T14) |
| CHECK 6 no resume driver | BLOCKER | VERIFIED | l.529-534, packet 1b at l.770 |
| CHECK 7 anthropic wire on OpenAI only | MAJOR | VERIFIED | l.452-453 |
| CHECK 8 FR-055 port types | MAJOR | VERIFIED | l.502-503 |
| CHECK 9 remote credential hand-off | MAJOR | VERIFIED | l.542, l.547, l.662. Duplicates the existing launch-time injection (T18) |
| CHECK 10 Claude trace sink | MAJOR | VERIFIED | l.572, packet 2 at l.772 |
| CHECK 11 `usage_summary` and compute cost | MAJOR | WEAKENED | l.466, l.554, l.544. No source is named for `price_per_minute` (T20) |
| CHECK 12 Claude-adapter fake | MAJOR | VERIFIED | l.331-333, packet 2 at l.772. Conflicts with the SDK-import rule at l.68 (T27) |
| CHECK 13 one home for accounts | MAJOR | VERIFIED | l.446-449 (`accounts` table); `context_tokens_window` at l.228 |
| CHECK 14 `apps_call` 20 s | MAJOR | VERIFIED | l.661, packet 5a at l.778 |
| CHECK 15 `SessionTarget` | MAJOR | VERIFIED | l.202 |
| CHECK 16 budgets as settings, USD in the ledger path | MAJOR | WEAKENED | l.619. Keys are `budget.*`, but the protected section is `budgets` (l.584), and today's section is `budgets` (`ctl/service.py:41`) |
| opus 1 REST-only is not a boundary | BLOCKER | WEAKENED | l.580-584, l.640, l.770. The protected list misses `backup`, `brokers`, `mcp_servers`, `providers` (T7); the signing key is unchanged (T3) |
| opus 2 money barrier vs Credential Manager | BLOCKER | VERIFIED, partial by declaration | l.586, l.828, Q10 at l.723. §10 says it is partial. The Q10 spawn path is unnamed (T16) |
| opus 3 `defer` common case, no resume path | BLOCKER | VERIFIED | l.98, l.137, l.199 (`orphaned`), l.323 (sibling rule), l.337-338 |
| opus 17 idle teardown on the laptop | BLOCKER | VERIFIED | l.544-547, l.836 |
| opus 4 `defer` untested shapes | MAJOR | VERIFIED | l.742 (P3 a, d, e), l.325, l.329 |
| opus 5 plugin `PermissionRequest` hooks | MAJOR | WEAKENED | l.316, l.370, l.376-377. §10 claims a test in 3a, but 3a's done-when (l.773) has no "allow hook, the write does not run" case |
| opus 6 effect keys from a host counter | MAJOR | VERIFIED | l.436, l.438, l.274 with packet 1c at l.771, l.413 |
| opus 7 OpenAI parked state per row | MAJOR | VERIFIED | l.301, l.348-349, l.518 |
| opus 8 checkpoint across two files | MAJOR | VERIFIED | l.606 |
| opus 9 "every call through `invoke`" | MAJOR | VERIFIED | l.36, l.393, l.409-413 |
| opus 10 single-writer holes on Windows | MAJOR | VERIFIED | l.251-264, l.610. The audit is now a known change (T12), and the writer needs a sync bridge (T11) |
| opus 12 subscription usage and herding | MAJOR | VERIFIED | l.449, l.458-463 |
| opus 14 plugin parity on OpenAI | MAJOR | VERIFIED | l.368-381 |
| opus 15 agent nodes vs approvals and crashes | MAJOR | VERIFIED | l.500, l.505, l.511 |
| opus 18 remote keys, approvals, missed runs | MAJOR | VERIFIED | l.537, l.541-542 |
| opus 19 Claude cwd, cleanup, orphan CLIs | MAJOR | VERIFIED | l.211, l.311, l.314, l.531. Spawn mechanics are unnamed (T16) |
| opus 20 prompt-injection trifecta | MAJOR | WEAKENED | l.317, l.488, l.627. Raw fetch tools are gone, but Claude `Bash` and the OpenAI `shell` can still reach any host after taint. `decide_builtin` blocks only the host's own port (l.403-404). Neither the taint rule nor §9 covers shell egress |
| opus 21 agent apps gain trust and credentials | MAJOR | WEAKENED | l.379, l.582, l.661. Manifests can still request `qmx/control-token` from the vault (T6) |
| opus 23 `qma` name collision | MAJOR | VERIFIED | l.33, l.157, l.667 |
| opus 24 Wednesday slice plan | MAJOR | VERIFIED | l.21, l.174, l.493, l.784, l.814 |
| sonnet 1 nothing he can see | BLOCKER | WEAKENED | l.642, l.644, l.722. The console is named. The handoff's `openapi.json` must lack the approval door (l.770), which the UI needs (T23). Console SSE needs `fetch` streaming (T22) |
| sonnet 2 slices 2 and 3 not parallel | BLOCKER | VERIFIED | l.227-242 (frozen producer types, `StaticRegistry`), J23 at l.775 |
| sonnet 3 no clock or cut line | BLOCKER | VERIFIED | l.784, l.786-801 |
| sonnet 4 his setup has no surface | BLOCKER | VERIFIED | l.622, l.748-756. The homework 1 premise is false (T29) |
| sonnet 5 probes unowned | MAJOR | VERIFIED | l.174, l.736, packet 0 at l.768 |
| sonnet 6 demo ingredients | MAJOR | VERIFIED | l.776, l.778, l.779 |
| sonnet 7 Usage page | MAJOR | VERIFIED | l.466, l.554, l.818 |
| sonnet 8 WED behaviours in prose only | MAJOR | VERIFIED | l.385, l.549-555 |
| sonnet 9 rented machines bill after the demo | MAJOR | WEAKENED | l.540, l.544, l.753. The price source is unnamed (T20) |
| sonnet 10 no reader for the DevOps plane | MAJOR | VERIFIED | l.469, l.555 |
| sonnet 11 no-API-spend bypasses | MAJOR | VERIFIED | l.450-453, packet 3b at l.774 |
| sonnet 12 money barrier overstated | MAJOR | VERIFIED | l.586, l.817, l.828 |
| sonnet 13 packets and commands | MAJOR | WEAKENED | l.766-782. Packet 0's command uses `tools/ci.py --workspace`, which does not exist (T28) |
| sonnet 14 38 WED FRs uncited | MAJOR | VERIFIED | l.820-822. The CHECK's WED half is deferred on purpose (l.853) |
| sonnet 15 SC-2 skills inside plumbing | MAJOR | VERIFIED | packet S at l.780 |
| sonnet 16 `qma` name collision | MAJOR | VERIFIED | l.667, packet 0 at l.768 |
| sonnet 17 slice 0 misdescribes CI | MAJOR | VERIFIED | l.154, l.706, l.768 |
| sonnet 18 slice 0 edits the Library | MAJOR | VERIFIED | l.603, Q12 at l.725 |
| sonnet 19 deletion wave on demo eve | MAJOR | VERIFIED | l.673, packet 7 at l.782 |
| sonnet 20 Max 5x budget | MAJOR | VERIFIED | l.803-805 |
| sonnet 21 §0 not plain words | MAJOR | VERIFIED | l.12-29 |
| sonnet 22 his questions not asked | MAJOR | VERIFIED | l.722-728 |
| sonnet 23 settings keys not enumerated | MAJOR | WEAKENED | l.612-630. Keys are listed, but their store is a table (l.598) while the code and DESIGN use `settings.toml` (T8), and two key prefixes do not match the protected names (T7) |
| sonnet 24 model switch with cost | MAJOR | VERIFIED | l.23, l.525, packet 3b at l.774 |

Tally. 60 checked: 49 VERIFIED (one partial by declaration), 11 WEAKENED, 0 NOT FIXED.

### E4. Remaining must-fix items for the architect

Ordered by risk. Each names where it lands.

1. **Move the signing key.** `road.signing_key` takes the operator secret, not the vault token (`ctl/server.py:147`). Delete `qmx/control-token` from the laptop's Credential Manager once the per-launch secret exists, and keep it only for the T2 node (Z1, Z2). Packet 1b, with a test that a signature computed from the old vault token is refused.
2. **Close the app path to the operator token.** The supervisor refuses `qmx/control-token` and any broker `qmx/*` label in an app manifest. The per-app token arrives through a host-injected variable, not a vault label (T6). Packet 5a, with the example manifests changed in packet 0.
3. **Name the operator-secret hand-off.** `start` and QMB's `control_host` have no window, and `control.log` is readable by agents (T2). Make `/api/health` token-free and pid-only so the ownership checks survive (Z6). Packet 1b.
4. **Complete the protected settings list.** Add `backup`, `brokers`, `mcp_servers` and `providers`. Rename keys or sections so `budget`/`budgets` and `seat`/`seats` match (T7). Packet 1b's negative test covers every protected section.
5. **Keep `settings.toml`.** Drop `settings` from migration 001 and from l.598, or move `qmx-broker`'s reader and the backup list in the same packet (T8, Z9).
6. **Fix `qmx-tools`, do not audit it.** `DomainContext` must stop constructing `ControlService` (`tools/service.py:126-128`). Add `qmx-tools/src/qmx_tools/service.py` to packet 0's files, with a test that the FastMCP child starts while the host holds the lock (T12, Z8).
7. **Give `Store` a blocking submit** for the sync `ControlService` methods that run in the thread pool (T11). Packet 1a.
8. **Name the Claude spawn path for Job Objects and Q10.** A custom `Transport` or a `cli_path` shim in `host/platform.py`, or a host-wide Job Object. Add "spawn as `qmx-agent` inside the job" to P5. Make `recover()` match orphans by recorded pid and `create_time`, not by environment (T15, T16).
9. **Remote checkpoints and price.** Name how `TurnHost.headless` exports checkpoint rows into the manifest's `checkpoints/` prefix (T14). Put `price_per_minute` on `Target` and map `max_lifetime_min` onto `Resources.timeout` (T17, T20). Prefer the existing launch-time key injection over `setup_verify` secrets (T18).
10. **Console and handoff mechanics.** Serve `/console` outside the gate, read SSE with `fetch` streaming, and publish an operator-only schema for the doors so the UI lane can call the approval route (T22, T23).
11. **Shell egress after taint.** Either extend `decide_builtin` and the OpenAI `shell` executor so a tainted session's network calls ask first, or list shell exfiltration as a residual in §9 (opus 20).
12. **Small consistency fixes.** Add the `PermissionRequest` allow-hook test to packet 3a's done-when (opus 5). Decide whether `events/normalise_claude.py` may import the SDK, or move it under `engine/` (T27). Build `ClaudeReplayAdapter` as a replay `Transport`. Change `default = "claude:opus"` to a pinned id (T21). Add `--workspace` to `tools/ci.py` in packet 0 (T28). Decide whether `control.db` joins the weekly backup (T13).
13. **CI reality.** Actions is enabled and active with zero runs ever. Replace homework 1 with "find why no run starts" (cause unknown; an account-level Actions setting is a guess), and let packets carry a local `just ci` log until then (T29).
