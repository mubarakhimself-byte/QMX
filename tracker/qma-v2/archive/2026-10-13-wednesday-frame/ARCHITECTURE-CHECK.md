---
label: qma-v2:architecture-check
created: 2026-10-12
checks: tracker/qma-v2/ARCHITECTURE.md (783 lines) against PRD.md (148 FRs, 81 WED, 39 NFRs, §3 constraints), USER-JOURNEYS.md (21 journeys, §5 demo), HOW-WHY.md (pass 1 F/P facts, delta 2 G1-G15, X1-X14)
rule: COVERED only where the architecture names the module, type, table, route or slice that delivers it. A mention is not coverage. A WED FR whose element is named but sits in no slice is PARTIAL (unslotted).
status: planning only; nothing committed. Line numbers (l.N) are ARCHITECTURE.md lines.
---

# QMA v2 architecture: traceability check

## 1. In plain words

1. All 148 FRs: 68 covered (46%), 64 partly covered (43%), 14 missing (9%), 2 contradicted (1%).
2. The 81 Wednesday FRs: 47 covered (58%), 32 partly covered (40%), 1 missing (FR-055), 1 contradicted (FR-024).
3. The 39 NFRs: 18 covered, 19 partly covered, 1 missing (NFR-026), 1 contradicted (NFR-020).
4. The worst gap is the money barrier. Claude's `Bash` and the OpenAI `shell`/`qmx_python` tools run as his Windows user. They can read every `qmx/*` entry in Credential Manager and call the "REST-only" doors on localhost. The approval route even hard-codes `by=Principal.operator` (l.127). The "structural" claim at l.439 does not hold.
5. Second: on Claude, the approval is claimed twice, once in the hook (l.571) and once inside `invoke` (l.393). Read literally, an approved call is refused at run time.
6. Third: nothing resumes work after a crash. `adopt_orphans` only marks rows `interrupted`, and it lands in slice 4, while turn leases land in slice 1. J19 breaks at step 2.
7. Fourth: the design says a node row and its checkpoint commit "in one Write" (l.514, l.577), but they live in two database files (l.611-612). That cannot be atomic.
8. Fifth: the router comment "anthropic wire feeds either engine" (l.457) contradicts FR-024, C-03 and the Claude adapter's own `ANTHROPIC_*` refusal (l.317).
9. Smaller WED gaps: there is no cross-boundary type check (FR-055), no compute-cost source (FR-112), no local sink for Claude traces (FR-120), no credential hand-off to a rented box, and no fake for the Claude adapter in CI.
10. Of the 21 journeys, only J20 walks through cleanly. Nine of the 10 WED journeys break at a named step.
11. The demo script works through slices 1-5. It breaks at 9:45, because there is no usage API (FR-050 is NEXT), and it is weak at 0:00, 2:15 and 9:00.
12. Is Wednesday reachable? On paper, yes for SC-1, SC-3, SC-4 and SC-6. SC-2 and SC-5 hang on slice 5, the last serial slice. Splitting slice 5 (fix 30) is the cheapest schedule rescue.

## 2. FR table

Key: C = COVERED, P = PARTIAL, M = MISSING, X = CONTRADICTED. Slice = the §8 slice (0-6), NEXT = designed but after Wednesday, — = none.

| FR | Pri | Delivering element (§) | Slice | Verdict |
|---|---|---|---|---|
| 001 | WED | `ClaudeAdapter` + general plugin + `TurnHost` (§2.3, §2.9) | 2 | C |
| 002 | WED | `PluginLoader`, Lab/Portfolio plugins, `ToolRegistry.for_plugin` (§2.4, §2.5) | 3 | C |
| 003 | WED | `SessionRow.surface/target` (§2.9) | 1 | P: `Target` is undefined and clashes with Placement's `Target` (l.550) |
| 004 | WED | `sessions_list` kept, `SessionRow.surface` (§5, §2.9) | 1 | C |
| 005 | WED | `[tools] expose` in `qma.toml` (§2.4) | 3 | P: Lab example exposes no Portfolio read tool; no always-ask rule for Portfolio writes |
| 006 | WED | `copilot.py` replaced; `qmx-agents` deleted (§5) | 6 | C |
| 007 | NEXT | plugins table, `plugins_*` ops (§3, §4) | NEXT | P: no seat CRUD op or seat-to-plugin row |
| 008 | NEXT | Q4: only general exposes `apps_update` (§6.2) | NEXT | P: no change-request artifact or app-use seat |
| 009 | NEXT | `FakeAdapter` (§2.3) | — | P: no scenario suite named |
| 010 | NEXT | `artifact` block (§4) | — | P: nothing enforces artifact-per-build |
| 011 | NEXT | `send(..., attachments)` (§2.3, A-21) | NEXT | C |
| 012 | NEXT | L1 role prompt (§2.4, Q2) | NEXT | C |
| 013 | WED | `TurnHost.submit/run_turn`, SSE, `EventSink` (§2.9, §2.10) | 1 | C |
| 014 | WED | `SessionRow.errand_id`, leases, crash flow (§2.9, §2.10) | 1/4 | P: no errand-to-artifact link; no startup resume driver; `adopt_orphans` only in slice 4 |
| 015 | WED | `delegate`, `job_status/wait/cancel/result` (§2.7) | 4 | P: no list verb among agent tools; `start_task` naming dropped |
| 016 | NEXT | state file + errand roll (§1.3 #4) | NEXT | P: §1.3 says slice 1 lays down the state file, but slice 1 scope omits it |
| 017 | NEXT | `RunJournal` per run, resume by `RunId` (§2.2, §2.8) | 1/4 | C |
| 018 | NEXT | `CallContext.unattended` (§2.1) | — | P: no assumptions card |
| 019 | NEXT | receipts, `/live` terminal/diff events (§2.5, §4) | — | P: no "What it did" receipt API |
| 020 | WED | `Engine` facade + `EngineAdapter` port (§2.3) | 1 | P: nine verbs listed, `stream` folded into `send`; Claude adapter has no CI fake |
| 021 | WED | `SessionCap`, per-step refusal (§2.3, §2.8) | 2/4 | C |
| 022 | WED | `ClaudeAdapter.open` refuses `ANTHROPIC_*`, auth `claude.ai` (§2.3) | 2 | C |
| 023 | WED | SIWC GPT rows, P1, Q5 (§6.1 A-01, §7) | 3 | C |
| 024 | WED | `OpenAIAdapter._agent` model by wire (§2.3) | 3 | X: l.457 lets anthropic-wire key providers feed "either engine" |
| 025 | WED | `ToolInvoker` single point (§2.5) | 3 | C |
| 026 | WED | `Router.pick(chain=OverrideChain)` (§2.6) | 3/4 | P: `OverrideChain` undefined; no storage for app/workflow levels |
| 027 | NEXT | `ModelRow` (§2.6) | 3 | C |
| 028 | WED | `AgentSpec` → `CompiledAgent` (§2.1, §2.4) | 1/3 | C |
| 029 | NEXT | "failover is a new session" (§2.6) | — | P: no retry or fallback component |
| 030 | WED | `PluginLoader.compile`, parity field (§2.4) | 3 | P: no skill-delivery mechanism on the OpenAI engine; `hooks.json` Claude-only |
| 031 | WED | `qma/plugins/{general,lab,portfolio}` (§2.0, §5) | 2/3 | C |
| 032 | WED | `CLAUDE_CONFIG_DIR=<home>/claude`, `setting_sources=[]` (§2.3) | 2 | C |
| 033 | NEXT | `PluginLoader.install` (§2.4) | NEXT | C |
| 034 | NEXT | `Engine.delegate`, `Broker` (§2.7) | 4 | C |
| 035 | WED | three skills + `PluginLoader.lint` (§2.4, §5) | 3 | C |
| 036 | LATER | eval gate in self-improvement (§2.11) | NEXT | P: no lifecycle states or dedupe |
| 037 | NEXT | `lessons` table + approval row (§2.11) | NEXT | C |
| 038 | WED | `AccountRow`, `accounts_*` ops (§2.6, §4) | 3 | P: called a settings row (l.447) and also an `accounts` table (l.611) |
| 039 | WED | sticky pick per session (§2.6) | 3 | C |
| 040 | WED | `Router.status → AccountStatus` (§2.6) | 3 | P: `AccountStatus` undefined; reset-time source unnamed |
| 041 | WED | rank capability, then remaining (§2.6) | 3 | C |
| 042 | WED | chain + node model in graph version (§2.6, A-07) | 3/4 | P: no workflow-level default field in `workflow.v1.1` |
| 043 | NEXT | `models_status` tool (§2.7) | 4 | C |
| 044 | NEXT | two Claude homes (A-20) | NEXT | C |
| 045 | NEXT | `ModelRow.effort_map` (A-04) | 3 | C |
| 046 | WED | `credential_ref`, `Credentials.scrub_env/redact` (§2.6, §8) | 3 | P: no teardown of in-process keys or remote keys |
| 047 | NEXT | `ModelRow` list (UI is a separate lane) | 3 | C |
| 048 | WED | `Ledger`, `limits` table, `LimitReached` (§2.6, §3) | 3 | P: no done-when; "fill gaps from local session files" silently dropped (X10) |
| 049 | WED | ledger from SDK results; CLIProxy deleted (§2.6, §5) | 3 | C |
| 050 | NEXT | `Ledger`, `usage.delta` (§2.6, §4) | — | P: no per-account series or cache-savings API |
| 051 | WED | `Budget`, `BudgetMeter`, `spend` approval (§2.1, §2.5) | 1 | P: caps live in `AgentSpec`, not Settings; USD is checked only in `invoke`; no per-turn/per-job split |
| 052 | WED | `Runner` over `workflow.v1.1`, `graph_versions` (§2.8, §3) | 4 | C |
| 053 | WED | node kinds (§2.8) | 4 | C |
| 054 | WED | code nodes, zero-ledger check (§2.10) | 4 | C |
| 055 | WED | — (validate checks inside one graph only) | — | M: no workflow-to-app type check before a run |
| 056 | WED | `workflows_*` ops, `run_workflow` (§4, §2.8) | 4 | C |
| 057 | WED | `Runner.validate` (§2.8) | 4 | C |
| 058 | WED | `_gate`, `ApprovalRow.revision_hash` (§2.8) | 4 | C |
| 059 | WED | `Checkpoints`, `Runner.resume` (§2.8) | 4 | C |
| 060 | WED | pinned `content_sha256`, `graph_refs` (§2.8, A-09) | 4 | C |
| 061 | WED | `NodePolicy`, `EffectsLedger` (§2.8, §2.5) | 4 | P: no validator rule forcing a gate and zero retries on external-write nodes; `merge` defaults to `partial` |
| 062 | WED | `run_workflow` platform tool (§2.5, §2.8) | 4 | P: `QmaClient` has no `run_workflow`, so not callable "inside an app" |
| 063 | NEXT | `AgentNode`, `StopRule`, `Checker` (§2.7) | 4 | P: no "needs human" exit in `StopRule` |
| 064 | NEXT | `workflows_put` (§4) | — | P: no promote-ad-hoc-plan path |
| 065 | NEXT | errand orchestrator (§1.3 #4, A-12) | NEXT | C |
| 066 | NEXT | — | — | M: no template store or template module |
| 067 | NEXT | — | — | M: no per-workflow compaction, sub-agent or model settings |
| 068 | NEXT | `Runner.run_scope` (§2.8) | NEXT | P: no Code-view emitter |
| 069 | LATER | format + validator (§2.8) | 4 | C |
| 070 | NEXT | `host/scheduler.py`, `triggers` (§2.0, §3) | NEXT | P: file name only |
| 071 | NEXT | `triggers` + `trigger_fires` (§3) | NEXT | P: no overlap policy; X8 remote scheduling not designed |
| 072 | WED | apps ops, host-assigned trust, `QmaClient` (§5) | 5 | C |
| 073 | WED | apps kept (§5) | 0 | C |
| 074 | WED | apps kept (§5) | 0 | C |
| 075 | WED | Job Object, T1 refusal → "disabled until approved" (§5) | 5 | C |
| 076 | WED | road kept (§5) | 0 | C |
| 077 | WED | supervisor publish gate (§5) | 5 | P: no "undeclared capabilities" check; auto-test hook has no new home after `AppHooksMiddleware` dies |
| 078 | WED | supervisor kept (§5) | 0 | C |
| 079 | WED | Macro daily bias via the road (§5) | 5 | C |
| 080 | NEXT | — | — | M: no builder/watcher errand fields |
| 081 | NEXT | agent tool code disabled until reviewed (A-13) | NEXT | C |
| 082 | LATER | — (MCP-app panels LATER, A-13) | — | M |
| 083 | LATER | `PluginLoader.install(bundle)` (§2.4) | — | P: plugins only, not apps or workflows |
| 084 | WED | `Broker.delegate`, own `RouterPick` (§2.7, §2.10) | 4 | C |
| 085 | WED | `delegate(engine=...)` both ways (§2.7) | 4 | C |
| 086 | WED | native + `as_tool` (§2.7) | 3/4 | P: the architecture lists it as weakened (§1.1) |
| 087 | NEXT | — | — | M: no sub-agent defaults per workflow |
| 088 | WED | leaf agents lose `Agent`; workers get no `delegate` (§2.7) | 3/4 | C |
| 089 | WED | `subagent.*` → `agents` block (§4) | 2-4 | C |
| 090 | LATER | A-10 "not needed" | — | X: the PRD keeps it LATER; the architecture closes it |
| 091 | WED | `SdkDefaultMemory` (§2.4) | — | P: unslotted |
| 092 | NEXT | `MemoryProvider.propose/commit` (§2.4) | NEXT | P: no per-agent provider binding field |
| 093 | WED | memory test (§2.4) | — | P: unslotted |
| 094 | NEXT | — | — | P: no memory list/edit API |
| 095 | LATER | — | — | M |
| 096 | WED | `SystemPromptFile`, `render_system` (§2.3, §2.4) | 2 | C |
| 097 | WED | byte-stable L0-L3, `snapshot_surface` (§2.4) | 2 | C |
| 098 | WED | Claude auto; OpenAI compaction session/summariser (A-04) | 3 | P: size cap only, no offload-to-file; the architecture lists it as weakened |
| 099 | NEXT | `TurnHost.switch_model` (§2.9) | NEXT | C |
| 100 | NEXT | `for_plugin` 10-15 + tool search (§2.5) | NEXT | C |
| 101 | NEXT | `tool.progress` live event (§4) | 1 | C |
| 102 | WED | no order tool, `check_descriptor`, FR-102 test (§2.5) | 1/3 | P: built-in shell reaches Credential Manager and localhost doors (fix 1) |
| 103 | WED | `write_roots`, `Receipts`, `PostToolUse` (§2.4, §2.5) | 2 | P: built-in writes stay `verified=false`; read-back mechanism unnamed |
| 104 | WED | `ApprovalQueue`, `defer`/`RunState` park (§2.5, §2.10) | 1/2/3 | P: two claim points; storage for `allow_session`/`remember` unnamed; P3-dependent |
| 105 | WED | always-ask settings row in `decide` (§2.5) | 1 | C |
| 106 | WED | `RunJournal` entry kinds (§2.2) | 1 | C |
| 107 | NEXT | demo `always_ask`, live deny (Q6) | NEXT | P: no demo/live account classifier |
| 108 | NEXT | code-constant `DenyList`, unattended deny (§2.11) | 1 | C |
| 109 | NEXT | serial write tools, truncated-reply guard (§2.10, §2.11) | — | P: four of six guards unnamed |
| 110 | WED | `Placement.ship`, `TurnHost.headless` (§2.9) | 5 | P: no credential hand-off for key-provider agent nodes on a rented box |
| 111 | WED | `ComputeProvider` kept, `setup_verify` (§2.9) | 5 | C |
| 112 | WED | `RunRecord`, `Placement` (§2.9, §2.11) | 4/5 | P: no source for compute cost-so-far; no done-when |
| 113 | WED | bundle, verified fetch kept (§2.9, §5) | 5 | C |
| 114 | NEXT | `Placement.ship(run_id)` (§2.9) | NEXT | P: no local-to-remote resume path |
| 115 | NEXT | — | — | P: no default-remote rule for cron |
| 116 | NEXT | bucket kept (§5) | — | P: snapshot and restore test unnamed |
| 117 | NEXT | `Placement.choose` refuses `windows_only` (§2.9) | 5 | C |
| 118 | LATER | `Target.gpu` (qmx-remote kept) | — | P |
| 119 | WED | "copy native file plus journal" (§1.4) | 5 | P: no export step; OpenAI session file is outside the manifest whitelist (P5) |
| 120 | WED | `QmaJsonlProcessor`, no-exporter assertion (§2.11) | 5 | P: no local OTLP receiver for Claude's OTEL export |
| 121 | WED | `RunRecord` four axes (§2.11) | 4 | P: `RunRecord` fields undefined |
| 122 | NEXT | health plane (§2.11) | — | P: no DevOps API |
| 123 | NEXT | `Watchdog` (§2.3) | 2 | P: kills and marks interrupted, never restarts |
| 124 | NEXT | — | — | M: no smoke suite (J01 step 5 and spin 3 are WED) |
| 125 | LATER | — | — | M |
| 126 | WED | `normalise_claude/openai` → `QmaEvent` (§4) | 2/3 | C |
| 127 | WED | `SessionRow.status`, `sessions_list` (§2.9) | 1 | C |
| 128 | WED | new `OPERATIONS` rows, no-overlap test (§4) | 1 | C |
| 129 | WED | `not_implemented` kept (§5) | 0 | C |
| 130 | WED | `/live` unstored channel (§4) | 1 | C |
| 131 | NEXT | `NodePolicy.write_scope` (§2.8) | NEXT | P: no worktree-per-agent or variant model |
| 132 | WED | `ToolRegistry` (§2.5, Q8) | — | P: no seam module paths for QMB/QMF; no `capabilities.list`; unslotted |
| 133 | WED | Claude built-ins; OpenAI base kit (§2.3) | 2/3 | P: no video tool; `qmx_python` kernel process unnamed |
| 134 | WED | `ToolRegistry.lint`, `expose` lists (§2.4, §2.5) | 3 | P: lint checks money and baseline only, not tool design |
| 135 | NEXT | plugin `.mcp.json` (§2.4) | — | P |
| 136 | NEXT | A-11 | NEXT | P |
| 137 | NEXT | A-11 | NEXT | P |
| 138 | NEXT | Portfolio plugin over `qmx-broker` read + `propose_order` (§0, Q6) | 3 | C |
| 139 | LATER | A-11 demo lock first | — | P |
| 140 | LATER | — | — | M |
| 141 | WED | `SessionCap` (§2.3) | 2 | C |
| 142 | NEXT | `lessons`, undo by plugin hash (§2.11) | NEXT | C |
| 143 | LATER | — | — | M |
| 144 | WED | PRs to `rebuild/base` (§8, Q7) | 0-6 | P: no branch-protection step |
| 145 | NEXT | — | — | M |
| 146 | NEXT | A-22: registry + invoker + journal | — | P: concept named, no data API |
| 147 | LATER | — | — | M |
| 148 | LATER | — | — | M |

Tally: C 68 · P 64 · M 14 · X 2. WED: C 47 · P 32 · M 1 · X 1.

## 3. NFR table

| NFR | Element (§) | Slice | Verdict | How the target is measured |
|---|---|---|---|---|
| 001 | `ANTHROPIC_*` refusal; GPT only on SIWC (§2.3, A-01) | 2/3 | C | Monthly provider billing reads $0; secret scan; refusal test |
| 002 | `AccountRow` per key (§2.6) | 3 | C | Add N rows; each completes a call (J20 probe) |
| 003 | depth 1 (§2.7) | 3/4 | P: a `defer`-parked Claude turn idles past the ~10 min cache life | Ledger cache_write on resume after park; count of park > 10 min |
| 004 | stable L0-L3 (§2.4) | 2 | P: slice 2 checks only reads > 0 | Ledger `cache_read / input` per Claude copilot turn ≥ 3, target ≥ 70% |
| 005 | `Ledger` (§2.6) | 3 | P: `LedgerRow` columns unwritten (X12 union) | % of ledger rows with cache fields where the provider reports them = 100 |
| 006 | `RunRecord` four axes (§2.11) | 4 | P: fields undefined | Null count over four axis columns = 0 |
| 007 | `SessionCap` (§2.3) | 2 | P: P4 load-tests SQLite, not 40 agents on one asyncio loop | 40-agent soak: event-loop lag p95, RAM, refusals |
| 008 | no Docker (§9) | 0 | C | FR-075 test on a box without Docker |
| 009 | one writer per file, P4 (§3, §7) | 0/1 | C | P4: p95 write < 50 ms, no `database is locked` |
| 010 | checkpoints + effects (§2.8, §2.10) | 4 | P: no resume driver, no timer | Kill -9 then time to all-resumed ≤ 60 s |
| 011 | `NodePolicy` retries, timeouts, merge (§2.8) | 4 | C | P10 tests plus new policy tests |
| 012 | `Watchdog` (§2.3) | 2 | C | P5: hung CLI marked `interrupted` ≤ 5 min |
| 013 | journal + traces (§2.2, §2.11) | 1/5 | P: Claude trace sink unnamed | Replay check: `rebuild_request` matches for 100% of calls |
| 014 | health plane (§2.11) | — | P: no DevOps slice | DevOps API answers per agent, workflow and app |
| 015 | `DenyList`, no order tool (§2.5) | 1 | P: built-in shell bypass (fix 1) | FR-102 test with shell attacks on both engines |
| 016 | `redact`, value scrubber, secret-scan (§2.11) | 1/3 | C | CI secret-scan over repo, journal, blocks, transcripts |
| 017 | read-only tool sets (§2.11) | — | P: nothing marks a reader of downloaded content | Test: a fetch tool's caller gets no write tool |
| 018 | settings rows (§2.5) | — | P: budgets live in `AgentSpec` | Diff: Settings keys vs UI-reachable keys = 0 |
| 019 | rows for accounts, models, plugins (§2.4, §2.6) | 3 | C | Add a model as a row with no code diff |
| 020 | policy in `ToolInvoker` (§2.5) | 1 | X: Claude built-ins are governed in `PreToolUse` (l.316, l.441) | Ratify the exception, or reword the NFR |
| 021 | `MemoryProvider`, `ComputeProvider`, plugins (§2.4) | 3/5 | C | Swap provider by config in a test |
| 022 | `host/platform.py` (A-14) | 0 | C | CI on Windows plus a Linux job |
| 023 | glossary words used | — | C | Doc review |
| 024 | L1 rule (Q2) | NEXT | P: prompt only | Eval: questions asked per errand (SC-C3) |
| 025 | seven slices with done-when (§8) | 0-6 | C | One PR per slice with its Actions link |
| 026 | — | — | M: the 30-item complexity list (21 §4) is not walked | Item-by-item table in the architecture |
| 027 | `FakeAdapter`, `FakeComputeProvider` (A-24) | 1 | P: no Claude-adapter fake | CI runs every engine test with no network |
| 028 | probes P1-P5 (§7) | — | C | Probe results recorded in the tracker |
| 029 | ~400-line rule (§2.0) | 0 | C | Line-count lint in `tools/ci.py` |
| 030 | `integrity_check` before backup (§3) | — | P: FR-116 is NEXT | Restore test per backup |
| 031 | `content_sha256`, `spec_hash`, plugin hash (§2.1, §2.8) | 1/4 | C | Hash equality tests |
| 032 | `submit` returns at once (§2.9) | 1 | P: 2 s not measured | First `/live` event − POST time ≤ 2 s, warm session |
| 033 | `CallContext.unattended` (§2.1) | — | P: no assumption record | Scheduled-run test: 0 prompts, 1 card |
| 034 | home `D:\QMX-data` (§3) | 0 | P: no serialiser for heavy local runs | Free-space check on C:; run queue length |
| 035 | §5 keep/replace table | 0-6 | C | Caller audit attached to each delete PR |
| 036 | FR-109 guards (§2.11) | NEXT | P | Guard unit tests |
| 037 | provider caching (§2.4) | 2 | P: no TTL on expensive read tools | Count of cache layers = 5; no Redis import |
| 038 | L0-L3 at 1.5-3k, ≤ 15 tools (§2.4, §2.5) | 2/3 | C | `snapshot_surface` token count; tool list length |
| 039 | event protocol (§4) | 1 | C | UI lane consumes only §4 routes |

Tally: C 18 · P 19 · M 1 · X 1.

## 4. Constraint check

### 4.1 PRD §3 constraints

| ID | Verdict | Where (l.) | Note |
|---|---|---|---|
| C-01 | Honoured | l.13, l.275-303 | `Engine` over two adapters |
| C-02 | Honoured | l.306-319 | Claude SDK with plugins, hooks, sub-agents; preflight kept |
| C-03 | **Violated** | l.457 | "anthropic wire feeds either engine" puts key providers on the Claude engine |
| C-04 | Honoured | l.317, l.457, l.680 | `ANTHROPIC_*` refused; GPT only through SIWC rows |
| C-05 | Honoured | l.16, l.344-370 | Plugin folder + `qma.toml` |
| C-06 | Honoured | l.19, l.496-528 | Own runner; LangGraph removed (l.670) |
| C-07 | Honoured | l.21, l.455-466 | Per session, never per request |
| C-08 | Honoured | l.22, l.776 | Bucket plus fetch; no server |
| C-09 | Honoured | l.778 | But fix 1 needs process separation (an operator call) |
| C-10 | Honoured | l.652 | Mode code goes with `copilot.py` |
| C-11 | **Violated in practice** | l.439 | "Broker credentials are never in a session's environment" is not a barrier. Credential Manager is readable by any process of his user, including Claude `Bash` |
| C-12 | Honoured by deferral | l.715, l.738 | Q7: ship into `rebuild/base` |
| C-13 | Honoured | l.773 | Named seams only |
| C-14 | At risk | l.740-750 | See §6 |
| C-15 | Honoured, with a gap | l.447, l.603 | Credential path to rented boxes unnamed |
| C-16 | **Violated (minor)** | l.211, l.218 | `Budget` and `always_ask` defaults live in spec and `qma.toml`, not UI-editable Settings |
| C-17 | Honoured | l.773 | No sizing anywhere |
| C-18 | Honoured | l.738 | Every slice ends headless |

### 4.2 HOW-WHY delta-2 facts G1-G15

| G | Verdict | Where (l.) | Note |
|---|---|---|---|
| G1 | **Violated in practice** | l.127, l.643 | Not exported as MCP, but reachable by shell `curl` with the control token from Credential Manager; the route trusts any caller as operator |
| G2 | Honoured | l.622-625 | One writer, read-only readers, assertion |
| G3 | Honoured | l.636-637 | Durable tail off the loop; `/live` push |
| G4 | Honoured | l.616 | `runs.db` derived |
| G5 | Honoured | l.617 | Memory files without LangGraph |
| G6 | Honoured | l.620 | `user_version` + typed claim columns |
| G7 | Honoured for events | l.611 | But the node_runs + checkpoint "one Write" (l.514, l.577) spans two files (fix 5) |
| G8 | Honoured | l.623 | `aggregates` read moved out |
| G9 | Honoured | l.553 | Fetch imports as new rows |
| G10 | Honoured, unslotted | l.555 | `idle_sweep` is in no slice (spin 5 is WED) |
| G11 | Honoured | l.206, l.409 | Lint refuses `effect=money` |
| G12 | **Violated by default** | l.229, l.410 | `apps_call` is a platform `ToolDef` with default `timeout_s=60`; G12 requires 20 s |
| G13 | Honoured | l.639 | Labels map to the 14 kinds |
| G14 | Honoured | l.395 | Sticky decisions excluded for always-ask, deny and money |
| G15 | Honoured | l.603, l.643 | REST-only credential write returns a reference |

### 4.3 Pass-1 traps F1-F20

| F | Verdict | Note |
|---|---|---|
| F1, F2 | Honoured | Trust from the approval record; T1 → "disabled until approved" (l.370, l.660), slice 5 |
| F3 | Honoured | Leases replace in-memory cancellers (l.651, l.662) |
| F4 | Partial | `adopt_orphans` (l.487) lands in slice 4; slices 1-3 can leave `running` rows forever |
| F5, F6, F8, F9, F10, F11, F13, F14, F18, F19, F20 | Honoured | l.536, l.455, l.456, l.439, l.670, l.668, l.654, l.703, l.184, l.670, l.618 |
| F7 | Not addressed | Which settings section holds account rows is unnamed; the Litestream `providers` collision stands |
| F12 | Honoured for apps→agents (A-17) | Violated for `apps_call` timeout (G12) |
| F15 | Honoured | Probes P1-P5 |
| F16 | **At risk** | If accounts are settings rows, `ModelRow.context_tokens` (l.452) matches the `token` pattern `_no_secrets` refuses |
| F17 | Honoured | A-15 one database per machine, imported on fetch |

## 5. Journey walk-through

Each journey runs through the §2.10 flows. "Breaks at" names the first step the architecture cannot carry.

| J | Pri | Flow used | Breaks at | Why |
|---|---|---|---|---|
| J01 | WED | turn | Step 2, then step 5 | No sign-in flow into the QMX Claude home (`ClaudeAdapter.open` only checks `claude.ai`). No smoke suite or "what works today" card (FR-124 missing). `capabilities.list` unnamed (step 6) |
| J02 | WED | turn, fetch | Step 2 | Nothing fetches remote results at start-up (`Placement.fetch` has no caller). Step 1's assumptions card is NEXT. Step 5 needs Portfolio reads in the general plugin (FR-005 P) |
| J03 | NEXT | switch_model | Step 2 | `CostEstimate` has no estimator component; parity loss per hook not computed |
| J04 | WED | turn, approval | Step 7 | "Built by errand" field missing (FR-080). Step 3: `terminal.output` from Claude `Bash` is unproven. Step 4's 5-round cap is a skill, not a guard |
| J05 | WED | turn, approval | Step 2 | No app-use seat or change-request artifact (FR-008 NEXT). Step 6 consumer type check missing (FR-055) |
| J06 | WED | workflow | Step 1 (soft) | No template module (FR-066); the copilot writes the graph from the skill instead. Step 2's "workflow default provider" has no field (FR-042) |
| J07 | WED | workflow, placement | Step 3 | A 5-minute trigger on rented compute needs the scheduler and X8's remote trigger push. Both are NEXT and X8 is undesigned. Step 5 phone notice has no channel |
| J08 | NEXT | — | Step 1 | `scheduler.py` is a file name only |
| J09 | WED/NEXT | placement, workflow | Step 3 | Agent nodes on a rented box need a key-provider credential; no hand-off is named. Step 6: a remote `spend` approval with the laptop closed waits forever (relay NEXT) |
| J10 | NEXT | delegation | Step 5 | No retry or failover component for a 429 (FR-029 P) |
| J11 | WED | delegation / native sub-agents | Step 4 | `Watchdog` kills and marks interrupted; it cannot restart one hung Claude native sub-agent inside a shared CLI process |
| J12 | NEXT | delegation | Step 1 | No research template (FR-066); Browser pane NEXT |
| J13 | NEXT | turn, approval | Step 4 | No proposal-signature record; the sign door is apps-only. Step 5 works (no order tool) |
| J14 | LATER | — | Step 5 | Computer use NEXT/LATER |
| J15 | NEXT | self-improvement | Step 2 | Weekly mining needs the scheduler |
| J16 | NEXT | ledger | Step 1 | No usage API; reset-time source unnamed |
| J17 | NEXT | approvals | Step 1 | Bucket mailbox is one sentence (l.490, l.776); no device binding or expiry design |
| J18 | NEXT | — | Step 1 | No worktree-per-agent or variant model |
| J19 | WED | crash and resume | Step 2 | `adopt_orphans` marks `interrupted`; no component calls `Runner.resume` or resumes errands. The banner has no event. Checkpoint and node row are not atomic (fix 5) |
| J20 | WED | accounts, credential door | — | Walks through: `accounts_*`, REST-only credential write, `Router.probe`, capability tag, next pick. Risk: F16 if accounts are settings rows |
| J21 | NEXT | plugin install | Step 6 | Tool search NEXT; no uninstall or rollback |

WED journeys: 10. Clean: 1 (J20). Broken at a named step: 9.

## 6. Wednesday demo feasibility (USER-JOURNEYS §5)

| Time | Needs | Slice | Verdict |
|---|---|---|---|
| Pre | Claude signed in to the QMX home; DeepSeek row; rented box verified; Usage tab | 2, 3, 5 | Sign-in procedure unnamed (fix 18). Usage tab has no backend (fix 11) |
| 0:00 | `run_workflow` with remote placement; job card with cost and log tail | 4, 5 | Weak: `run_workflow` has no placement argument; `Runner.run` takes none (l.512). Cost-so-far has no source (FR-112). The `gold-morning-check` workflow is authored by no slice |
| 0:45 | Copilot rebuilds Macro daily bias | 5 | OK if slice 5 lands. This is the longest live step on the slowest slice |
| 1:15 | "What's running and what did it cost" in < 2 s | 1, 4 | Weak: no per-errand cost aggregate tool; NFR-032 unmeasured |
| 2:15 | Lab on Claude, Portfolio on OpenAI "switched in Settings" | 3 | Weak: no Settings key moves a plugin's engine. The workaround is a home copy of `qma.toml` (home wins by name, l.344) |
| 3:15 | Lab builds a 4-node mixed workflow | 3, 4 | Gap: the Lab `expose` example lacks `workflows_*` (l.350). The data fetch uses the FastMCP domain proxy (slice 3) |
| 4:15 | Run, edit threshold, rerun; 0 model calls on run 1 | 4 | OK |
| 5:30 | DeepSeek helper under Opus in the run index | 4 | OK (slice 4 done-when) |
| 6:30 | Publish to Sandbox, run, edit → v2 at Build | 5 | OK |
| 8:00 | Remote fetch, hashes verified, transcript local | 5 | OK for a code-only workflow; an OpenAI-engine transcript would not upload (FR-119) |
| 9:00 | "Buy" refused on both engines, Journal shows denied calls | 1, 3 | Mismatch: with no order tool there is no call to deny, so the Journal may show nothing. There is also no "allow all" setting. Show the tool lists and the FR-102 test run instead (fix 21) |
| 9:45 | Usage page with cache reads and compute USD | — | **Breaks**: FR-050 is NEXT; no usage op in slices 0-6 |

Verdict. SC-1 (slice 2), SC-3 (slice 3), SC-4 (slice 4) and SC-6 (slices 1+3) are reachable if slices 1-4 hold their days. SC-2's mini-app half and SC-5 both sit on slice 5, which waits for 3 and 4. The plan has 7 slices and 5 probes in about two working days, with slice 1 green by Tuesday noon (l.766). That is reachable only if nothing slips. Fixes 11, 18, 21 and 30 make the script itself honest.

## 7. Fix list for the architect (by severity)

**S1: safety and correctness (fix before slice 1 merges)**
1. **Shell bypass of the money barrier and the REST-only doors.** Claude `Bash`/`Write` and the base-kit `shell`/`qmx_python` run as his Windows user. They can read `qmx/*` (broker credentials, the control token) and `curl` `POST /api/approvals/{id}`, which trusts any caller as operator (l.127). Fixes:
   - The REST-only doors need an operator-presence secret that agent processes cannot read: a UI-session token held in memory, not in Credential Manager.
   - Run agent shells under a separate low-rights Windows account or restricted token with no access to `qmx/*`. This is process separation, not a sandbox; ask the operator to confirm it squares with C-09.
   - Add `decide_builtin` patterns as defence in depth.
   - Extend the FR-102 test with "shell reads keyring" and "shell calls the approval route" on both engines.
2. **Approval claimed twice on Claude.** The hook claims at l.571; `invoke` claims at l.393. State one claim point, `invoke` by effect key. The hook only checks `approved`.
3. **Effect key across resume.** `mint` uses "run:node:seq" (l.432), but a host counter resets on restart. Bind the key to the deferred `tool_use_id` or a persisted counter, or the re-fired hook will not find its row.
4. **The `defer` single-call argument is wrong** (l.106). FR-109 serialises execution, but it cannot stop Claude emitting parallel `tool_use` blocks in one turn. Add P3(c), which measures how often multi-call turns happen. Treat the bounded live path as common, not rare.
5. **Checkpoint atomicity.** "node_runs row + checkpoint in one Write" (l.514, l.577) spans `control.db` and `checkpoints.db` (l.611-612). Either move checkpoints into `control.db` until P4 says otherwise, or write the checkpoint first and the node row second carrying its id, and state the resume rule.
6. **No resume driver.** Add `host.recover()` to slice 1. It adopts orphans, resumes errands and runs, emits the restart-banner event, and moves `adopt_orphans` out of slice 4 (J19, FR-014, NFR-010, F4).

**S2: WED contradictions and missing pieces**

7. Change l.457 so anthropic-wire key providers run on the OpenAI engine only (FR-024, C-03, l.317).
8. Add a cross-boundary port-type check to `Runner.validate` for `app_call` against the app manifest's `provides`/`feeds` (FR-055).
9. Name the credential hand-off for key-provider agent nodes on a rented box: `credentials_scope` resolution on the box, and teardown. Add the OpenAI session file to the manifest whitelist (FR-110, FR-119, C-15).
10. Name the Claude trace sink: a local OTLP receiver in the host, or the console exporter captured to `<home>/traces/` (FR-120, NFR-013).
11. Add a `usage_summary` operation (per account, cache reads, compute USD) and a compute-cost source (provider price × minutes) in slice 4 or 5. Demo 9:45 and FR-112 need it.
12. Add a Claude-adapter fake: a recorded CLI stream replay behind the `ClaudeAdapter` transport, before slice 2 (NFR-027, FR-020).
13. Choose one home for accounts: the `accounts` table (l.611) or a settings row (l.447). If settings, rename `context_tokens` (F16) and avoid the `providers` section (F7).
14. Set `apps_call` `timeout_s=20` explicitly (G12).
15. Rename the session `Target` (for example `SessionTarget`: app, version, account, environment) so it no longer collides with Placement's `Target` (FR-003).
16. Budgets: make the per-turn and per-job caps Settings rows. Check USD in the ledger write path, not only in `invoke`. Document "pause = `spend` approval + `waiting_approval`" (FR-051, C-16).

**S3: WED partials that weaken the demo or journeys**

17. Add a smoke suite and a "what works today" card to slice 6 (J01 step 5, spin 3, FR-124).
18. Name the Claude sign-in procedure for the QMX home: an operator script or wizard, with the token never passing through QMX (J01 step 2, demo pre-step).
19. Name where a seat's engine override lives (a `plugins` row field), so demo 2:15 is a Settings edit.
20. Add `workflows_*` and Portfolio read tools to the Lab `expose` list (l.350; FR-005, demo 3:15). Add a `jobs_list` agent tool (FR-015).
21. Rewrite demo step 9:00 to show both tool lists plus the FR-102 test output. Define what "allow all" is, or drop it from the script.
22. Add validator rules: external-write nodes need a gate and `retries=0`; a join must name its merge rule (FR-061).
23. Add an errand-to-artifact link and builder/watcher errand ids on apps (FR-014, FR-080, J04 step 7).
24. Slot `SdkDefaultMemory` and the memory-reference test into slice 2. Slot `ToolRegistry` seam modules (Library, QMB, QMF) and `capabilities.list` into slice 3 (FR-091, FR-093, FR-132).
25. List `stream` as a facade verb, or record that `send` is `send`+`stream` (FR-020).
26. Release the `SessionCap` token when a Claude turn parks on `defer`. Otherwise parked approvals starve the cap (FR-141).

**S4: NEXT, LATER and ratification items**

27. Ask the operator to ratify the NFR-020 exception (Claude built-ins governed in `PreToolUse`) and the A-10 closure of FR-090. Ask him to amend FR-048's "fill gaps from local session files" to match X10.
28. Walk the 30-item complexity list (NFR-026) in an appendix.
29. NEXT design debts:
    - `StopRule` "needs human" (FR-063).
    - A watchdog restart, not only kill (FR-123).
    - X8 remote trigger push and the missed-run policy (FR-071, J07).
    - Device binding and expiry for the bucket mailbox (J17).
    - Template store (FR-066).
    - Per-workflow settings (FR-067, FR-087).
30. **Schedule.** Split slice 5:
    - 5a, apps rewrap and Macro daily bias. Needs only slices 2 and 3, so it runs in parallel with slice 4.
    - 5b, remote. Runs after slice 4.

    This takes slice 5 off the serial tail that carries SC-2 and SC-5.
