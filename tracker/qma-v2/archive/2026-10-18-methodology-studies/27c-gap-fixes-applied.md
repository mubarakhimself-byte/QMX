# 27c: Gap fixes applied to the three architectures (2026-10-16, night)

Ruling 88 says that gaps go back into the architectures before the plan continues. This pass applied every blocker and should-fix from `27b-final-rubric-walk.md` §6, together with the gaps listed in `wayfinder/REWRITE-NOTES.md`. Where 27b and a ruling disagreed, the ruling won. One Opus 5.5 agent did the work headless. It spawned no sub-agents, edited no code and made no commit.

Paths below are relative to `tracker/qma-v2/`. Abbreviations: `ENG` = `architecture/workflow-engine/`, `LIB` = `architecture/library-and-data/`, `LAB` = `architecture/lab-and-pods/`, `SP` = `ARCHITECTURE-SPINE.md`, `SD` = `ENG/SOLUTION-DESIGN.md`.

**Totals:** 23 target files changed, plus the 3 memlogs (+543 / −328 lines). No AD id moved. New ADs: engine **AD-34** and **AD-35**, appended at the end. `lint_spine.py` reports 0 findings on all three spines (section 4).

---

## 1. Fixes applied

| # | Fix (brief item; 27b ref) | What changed | Files | ADs touched |
| --- | --- | --- | --- | --- |
| 1 | **Ruling 78: context discipline** (B1; wayfinder gap 4) | New engine AD-34 covers five things. (1) **Chunking:** a `map: chunk` edge with `by: items \| tokens` and `fill` 0.30 of the resolved model's window runs one agent per chunk. Broadcasting a list into an `llm` or `agent` node is refused. The chunk plan is recorded and replayed, and each chunk has its own memo. (2) **Compaction** at `agent.compact_at` 0.40. (3) **Cache:** the prompt order is fixed, with the chunk payload last, and leases stick by `run_id:node_id`. (4) **Hooks:** per-chat PreToolUse (observe only, after the money gate), PostToolUse, PreCompact, Stop and SubagentStop. (5) **Tool calls:** one child span per call, plus a `max_tool_calls` limit of 200. New harness requests: **H15** (per-chat compaction threshold) and **H16** (per-chat hooks), each with a fallback that needs no harness edit. New live checks: **E29** (chunk count, chunk-only rerun, broadcast refused), **E30** (`cache_read > 0` from chunk 2, lease affinity) and **E31** (compaction, `memory_note`, tool spans, no hook leakage into copilot chats). Each check states its fallback form. Supporting changes: AD-5 (`chunk` mapping), AD-15 (tool and chunk spans), SD §2.1 example, §2.2-2.4, §3.2 events, §3.3, §7.3, §8.4, §10.1, §15 rows, §16 candidates, §17 defaults | ENG SP, SD, HARNESS-REQUESTS, PLAIN-WORDS | ENG AD-5, AD-15, AD-25, AD-34 (new) |
| 2 | **Real models for tests** (B2; ruling 51) | Every fake-provider default is gone. The builder test is a real-model run on cheap candidates. The fake provider exists only as an explicit `fake: true` switch. Places changed: AD-22; SD §9 (the line "the fake provider is selected by `mode: test`" now names the switch); §16 Test-step row; checks E7 and E21; DOC-CHANGES row 2 | ENG SP, SD, DOC-CHANGES | ENG AD-11, AD-22 |
| 3 | **Run mode kept separate from status** (B3) | Every run has `mode: live \| test`, fixed at birth. SD §3.1 defines **one shared status table**: `queued \| running \| waiting \| passed \| failed \| stopped \| interrupted`, with a `reason` field on waiting, failed and stopped. The engine and the Library use these words identically, and the state diagram and JobHandle mapping were redrawn to match. "Tested" means a `passed` run in either mode. Among passed runs, only `mode: test` is excluded from fast-forwarding to `main`. Engine-side changes: AD-11, AD-16 (park now ends a run `failed`, reason `parked`), Conventions "Run vocabulary", SD §3.2 and §8.1 `put_run_summary`. Library-side changes: AD-15, AD-18, Conventions, LLD rows, HLD §6. LIBRARY-REQUESTS L9 was reworded and L17 added; ENGINE-REQUESTS-ANSWERED answers L9 and L17 | ENG SP, SD, LIBRARY-REQUESTS, DOC-CHANGES row 25; LIB SP, HLD, LLD, ENGINE-REQUESTS-ANSWERED, DOC-CHANGES, PLAIN-WORDS | ENG AD-11, AD-16; LIB AD-15, AD-18 |
| 4 | **Drafts off `main`** (B4, S7; rulings 57, 80) | A new ref namespace, `refs/drafts/<item>`, is owned by `operator` on the primary store. `engine:<store>` may advance it only to land run-made lifecycle objects. `main` holds published versions only. Triggers pin an exact published object, or its champion when `follow_champion` is set and the champion descends from the pinned object. They never run a draft. Workflows, mini apps, pods, skills and methodologies made by runs land as drafts. Results, artifacts, notes and memory rows still land on `main` without asking (ruling 57). Publishing is a merge into `main` and asks him once (MANAGE). Because object ids are content, an unchanged tested draft keeps its `tested-by` edge when it is published. Also added: `refs/challengers/<item>` (S7). Engine side: AD-10, AD-11, AD-14, AD-22, AD-26. Library side: AD-7, AD-9, AD-11, AD-15, AD-18, AD-19, MIGRATION step 3. Lab side: AD-2, Conventions, LLD §6/§8.5. LIBRARY-REQUESTS gains L15 and L16, and both are answered | ENG SP, SD §8.1, §11.3; LIB SP, LLD, HLD, MIGRATION, ENGINE-REQUESTS-ANSWERED; LAB SP, LLD | ENG AD-10, AD-11, AD-14, AD-22, AD-26; LIB AD-7, AD-9, AD-11, AD-15, AD-18, AD-19; LAB AD-2 |
| 5 | **Harness edits** (B5) | **H0** asks to export `Background` and `Child`. Its fallback needs no harness edit: one adapter module is allow-listed to import exactly those two names from `qma.harness.launch`. **H17** asks for `AGENT_OPERATIONS` rows for the new `workflow_*` tools, `apps_archive`, the Library rows and the Lab rows. Its fallback: drafts are saved with the existing `library_save` (DOMAIN_WRITE), an engine watcher test-runs a draft whose `meta.test_requested` changed, and reads use existing rows. **`workflows_put` and `workflows_run`** are re-scoped to publish and live run, which stay MANAGE and correctly ask once. Draft save (`workflow_drafts_put`) and test run (`workflow_tests_run`) are DOMAIN_WRITE and **never ask**. SD §13 was rewritten with every tool's Effect (S16). Both requests are flagged as needing his grant. The Library and Lab notes that said "nothing else in the harness changes" now point to H17 | ENG SP AD-3, AD-22; SD §7.4, §13; HARNESS-REQUESTS; LIB LLD §7, §13, DOC-CHANGES, SP AD-9; LAB LLD §7, DOC-CHANGES, SP inherited table | ENG AD-3, AD-22; LIB AD-9; LAB AD-14 (text in LLD only) |
| 6 | **Capacity from RAM** (B6; ruling 76) | Every "twenty", "semaphore 20", "32-48 GiB" and "20 Background chats" was removed. `max_sessions = floor((ram_budget_mb − overhead_mb) / session_mb)` is always derived, and a hand-set value may only lower it. Contabo's `overhead_mb` defaults to 6,144 (Hub, vault, market data, monitoring, server engine, warm workers), which gives **4 sessions on the 12 GB, 6-core box**. Burst placements absorb the overflow through ordered `runs_on` candidates. Places changed: AD-12, AD-25, AD-30 ("Prevents" rewritten); SD §5.4 server row, §7.3, §17 (semaphore row deleted), §21 worked example, E8 (8 chats over two accounts), E27 (12,288/6,144 gives 4, with spill to burst); OPEN-DECISIONS; PLAIN-WORDS | ENG SP, SD, OPEN-DECISIONS, PLAIN-WORDS, DOC-CHANGES row 26 | ENG AD-12, AD-25, AD-30 |
| 7 | **Ruling 74: provider onboarding** (S20; wayfinder gap 2) | AD-30 adds a `provider-onboarding` copilot template. The copilot reads the provider's published skill, `llms.txt`, MCP or agent instructions **as data only**. It maps the provider onto a generic adapter (`ssh`, `http_api` with a declarative `adapter.toml`, `host_harness`, or `dashboard_mcp`) and drafts the placement row, an optional `KeyProvider` row and the adapter spec (a Library `artifact`). He applies them in Settings with one MANAGE click, because agents never write settings and `settings_put` stays out of the tool table. Preflight then runs, followed by a smoke test. Contabo is first. SD §21 lists the steps. The Lab's `compute.add` and UI-HANDOFF §9 row 4 point to this flow | ENG SP, SD §16, §21; LAB LLD §7, UI-TO-BACKEND-MAP; UI-HANDOFF | ENG AD-30 |
| 8 | **Ruling 75: central relay** (N1; wayfinder gap 1) | Each placement row now has `relay: local \| central`. **Default:** `pc` is local, because its copilots must survive a Contabo outage. `contabo` is local and is itself the central relay. Every non-owned placement, and any further owned machine, uses `central`. Trade-off stated in AD-28: keys sit on two machines only, there is one rotation and audit point, and burst machines hold nothing key-bearing; the costs are one tailnet hop, Contabo bandwidth, and a single point of failure for remote placements. H11 notes that Contabo needs it first. SD §16 candidate row, §17 default, §19 row | ENG SP, SD, HARNESS-REQUESTS, PLAIN-WORDS | ENG AD-28, AD-30 |
| 9 | **Library answers L11-L14; no key on any worker** (S5; wayfinder gap 5) | Library AD-12 was rewritten: the run token grows into the engine-minted **run pass** (attempt, placement, `model_scope`, `relay_url`, nonce), verified by signature with a revocation list. The line "provider keys injected at start by the submitter (`credentials_scope` over stdin or sandbox env)" is **deleted**. Every `ComputeProvider.start` call passes only `{QMX_RUN_PASS}`. AD-13's sidecar now redacts the pass. HLD §5b and §7 and LLD §8d and §9 were changed to match. ENGINE-REQUESTS-ANSWERED adds L11 (vault beside the Hub, a note), L12 (pass), L13 (imported traces in the `trace` blob slot, `provenance: imported`, no new kind) and L14 (placement fields on `workflow-run`, which replace `ran-on` and stop the `setup` double meaning, S15) | LIB SP, HLD, LLD, ENGINE-REQUESTS-ANSWERED, DOC-CHANGES, PLAIN-WORDS; ENG LIBRARY-REQUESTS, DOC-CHANGES row 19 | LIB AD-4, AD-11, AD-12, AD-13, AD-15 |
| 10 | **Session home field** (B30; N6; wayfinder gap 7) | New engine AD-35. The **owner** is the engine spine, because its surfaces and its `home` memory scope key on the home. The data lives in `qmx_control` (`session_homes`), not in the harness, so ruling 24 is untouched. Shape: `home: {kind: general \| lab \| portfolio \| library \| app, project_id}`. It is written once at birth: by the UI with `PUT /api/sessions/<id>/home` after `POST /api/chats`, and by the engine after `start_chat`. Child chats inherit their parent's home, and a session with no row reads as `general`. Every surface resumes a session through the same session id and turn routes, and "open in its home" is the way back. UI-HANDOFF §1.2 was updated | ENG SP, SD §8.4, §16, PLAIN-WORDS; UI-HANDOFF | ENG AD-35 (new), AD-18 (scope keyed), AD-21 |
| 11 | **Ruling 27: no spend caps** (S2, S3, S4; wayfinder gap 6) | The Lab's `ask_above_usd`, every "MANAGE above spend threshold" note and its default row are deleted. Lab AD-13 is retitled "no asks inside the Lab except money and publishing out". On the engine side, the per-run budget becomes the **runaway guard**: tokens, agents, tool calls and wall time, with no USD figure. A breach **pauses** the run (`waiting(runaway)`, an info digest line, then `stopped` when the next occurrence starts) or **degrades** it (it switches to the cheapest candidates and continues once). It never asks him. Budget-breach urgent inbox items are gone (AD-16, SD §10.2-10.3, §15). Pass token caps now come from the guard. SD §7.4 explains how the harness `[budgets]` settings bind: `max_budget_usd` is raised on engine hosts and mapped to `waiting(runaway)`, and `max_live_chats` should be at least 6. **H7 re-checked:** the per-chat `max_budget_usd` is dropped from the request | ENG SP, SD, HARNESS-REQUESTS, PLAIN-WORDS; LAB SP, LLD, UI-TO-BACKEND-MAP, PLAIN-WORDS; UI-HANDOFF | ENG AD-4, AD-16, AD-26, AD-28; LAB AD-13 |
| 12 | **Ruling 68: backtests go to the QMB machine** (S1, S12) | Lab `QmbPort`'s default adapter is the engine's `app_op qmb_backtest` on the `qmb` placement. The in-process `qmb.doors.api` is used only when the `qmb` placement is the PC, as a developer fallback. The `qmb` CLI in remote workers is dropped. A "controlled host" is `pc` or `qmb`, and both produce evidence. `qmb.*` compute types now have base kind `app_op` and effect `none`; only `holdout_touch` stays irreversible. Engine AD-31 states the effect and the Lab link. Lab LLD §2, §3.1 (`placement: qmb`), §3.2, the §8.2 sequence and §11 seams were changed to match | LAB SP, LLD, HLD, PLAIN-WORDS, DOC-CHANGES, UI-TO-BACKEND-MAP; ENG SP | LAB AD-3, AD-5, AD-8; ENG AD-31 |
| 13 | **Lab paper as a chain of finite runs** (S10) | A paper soak is now one finite run per trading day. A daily cron fires at session open with `continuity`, `max_concurrent 1` and a bounded loop over the day's bars (`wait` then `paper.step`), with `paper.check` at the close. Each day appends a version of the `paper-run`. Pause and resume disable and enable the trigger, extend raises `days_planned`, and stop keeps the record. `gate_resolved` is no longer misused. A new FM-17 covers a day that dies or is missed | LAB SP, LLD §5.5, §8.4, §9, §10, HLD, PLAIN-WORDS, UI-TO-BACKEND-MAP, DOC-CHANGES; ENG SD §5.4 | LAB AD-12 |
| 14 | **UI-HANDOFF** (S26; 27b §5) | Approvals now list the four **decisions** in code: `allow_once`, `allow_always`, `reject` and `answers`, with the statuses `resolved \| already_answered \| expired \| invalid \| unknown`. "Compact now" is marked as needing H15. The kind count is **33** and the Library relation count **24** (with `ran-on` retired). "Where it ran" adds managed agent hosts, `agent_mode` and the `mode` badge. §5 adds no spend asks, the QMB machine and daily paper. The session home is designed. A new **§9 adds the 15 missing rows** | `UI-HANDOFF.md` | — |
| 15 | **OPEN-DECISIONS refreshed** (S19) | **Engine:** three calls for him sit at the top: (A) harness grants H0/H15/H16/H17; (B) whether the 50% plan background cap still applies to workflows; (C) whether to accept study 30 for the first data packets. Still open: burst provider, `host_harness`, plan logins, irreversible effects. Closed with their rulings: server specs (76), self-improvement default (79), hosting start (74), central relay (75), inbox volume (77), creation and publishing (80). **Library:** OPEN-7 is closed by ruling 80; OPEN-2, 3, 4 and 5 remain. **Lab:** OPEN-3 and OPEN-5 are closed by ruling 80 (plus engine AD-22); OPEN-1, 2, 4 and 6 remain | ENG, LIB, LAB `OPEN-DECISIONS.md` | — |

### Other should-fix items applied

| 27b | Fix | Where |
| --- | --- | --- |
| S6 | `GatewayPort` fronts both the Hub and `qmx-node`; `placement_status` and `cancel` come from `qmx-node` | SD §5.3, §14.4 |
| S8 | The engine uses the Library's kind and edge names (no `workflow_version`; `workflow-run`, `test-report`). The engine's `supersedes` is the Library's `replaces`, so there is one relation, not two (27b's alternative, chosen to avoid a near-duplicate); LIB LLD FM-10 matches | ENG AD-14, ER diagram, SD; LIB AD-4 |
| S9 | Pack types are named `<pack>.<name>` and carry a `base_kind` that the validator checks; `note` is the one draft-only type, and the Lab no longer has `lab.note` | ENG AD-5, SD §2.3; LAB AD-3, LLD §1-2 |
| S11 | The Lab `KernelPort` defaults to the engine's `sandbox_python` kernel in `qmx-worker`; a host subprocess is allowed only for cells he saved himself, or when Docker is off | LAB AD-9, LLD §11, PLAIN-WORDS |
| S13 | One placement vocabulary: `pc`, `contabo`, `qmb`, plus provider rows. "Controlled host" means `pc` or `qmb` | ENG AD-3, AD-30, Conventions, SD §2.2, §9, §14.4, §15, E13; LAB AD-8, UI map |
| S14 | A workflow template is a published `workflow` version tagged `template`; the Library `template` kind is kept for non-workflow templates only | ENG AD-22, SD §6.5; LIB AD-3, HLD, LLD |
| S15 | `setup` keeps only its CT-47 meaning; placement becomes a field on `workflow-run` | LIB AD-4, AD-15, HLD, L14 |
| S17 | `caller_kind` maps to the Library principal; a run's writes carry `run:<run_id>` | ENG AD-14, Conventions; LIB Conventions |
| S18 | Inbox severity policy: only provider and harness-level failures reach `normal` and above (ruling 77) | ENG AD-17, SD §10.4, §14.3 |
| S22 | The §2.1 example's `human_gate` was replaced with a `rule` node | SD §2.1 |
| S23 | Stale OPEN-6 references now point to Library AD-18 | LIB HLD §6 note 3, LLD §8d; ENG DOC-CHANGES row 16 |
| S24 | The stale pod/book mapping text now cites Library AD-3 | LAB AD-11, DOC-CHANGES |
| S25 | Verb count corrected. **27b miscounted:** the port has **fourteen** verbs plus the operator-only `adopt`, not "fifteen plus adopt" (LLD §7 lists 14 + 1) | LIB SP layer table, AD-9 title, source tree; HLD; LAB inherited table |
| N2 / F10 | The "Docker+runsc is 80% coded" claim is corrected (`runc` flags only, secrets passed as `--env`, no local Docker provider) | SD §16 |
| N5 | New check **E32**: every shipped template passes a real-model test run before it is listed | SD §18 |
| N7 | Run-made lifecycle kinds land as drafts; everything else still lands freely | LIB AD-18 |

---

## 2. Where a ruling overrode 27b

| 27b said | Ruling or brief | Applied |
| --- | --- | --- |
| S10: paper as an `interval` trigger per bar | Brief item 13: daily segments with continuity | Daily cron trigger. Each day is one finite run that loops over that day's bars |
| B5: H0 and H17 have "no fallback; packet 5 blocks" | Brief item 5: every harness request gets a fallback that needs no edit | H0: a narrow import allow-list. H17: `library_save` plus a test-on-save watcher, using the existing rows |
| S20: the copilot writes the placement row through `ControlService` (MANAGE) | Harness `OPERATIONS_LEFT_OUT` keeps `settings_put` out of agent reach | The copilot drafts the rows; he applies them in Settings with one click |
| B3 fix: a mapping table from engine words to Library words | Brief item 3: one shared table used identically by both | One vocabulary on both sides; no mapping layer |
| S3: a runaway breach "resumes on the next trigger" | Brief item 11: pause or degrade the run, never ask | `on_runaway: pause \| degrade`. A paused run ends `stopped` when the next occurrence starts, or resumes if he raises the guard |
| Lab OPEN-5: recommended a standing Lab allow rule | Ruling 80 plus engine AD-22: publish and enable ask once | Closed. A Lab schedule asks once, like any workflow |

---

## 3. Deliberately not applied

| Item | Why |
| --- | --- |
| `research/methodology/33-state-of-play.md` edits (27b §6: "rulings 1-84", the answered items, a pointer to 27b) | The file is outside this pass's target list. The lead's "centralise once more" step should apply them, and should also point it at 27c |
| Wayfinder ticket status | Outside the targets. These tickets can now close or narrow: `engine-amend-chunking-compaction`, `library-engine-requests-l11-l14`, `session-homes`, `doc-changes-lab-and-pods` (spend-ask conflict), `harness-h7-subagent-defs`, `engine-open-4` (now a check, not a decision), `engine-open-6`, `lab-open-3`, `lab-open-5`, `library-open-7`. These should be **kept for his confirmation**: `central-relay-ruling-75` (HITL; a default is now designed), `placements-and-capacity` (rows designed; the measured RAM per session is still owed) and `provider-setup-from-skills` (the flow is designed, but nobody has researched what Amp, Cloudroom, E2B, Modal and Cloudflare actually publish) |
| `HEADLESS-RESULT.json` in ENG and LAB | Outside the targets. Each is a run artifact of an earlier pass, not a design document |
| A design for the Data track (27b S21; rulings 58, 81) | It is the operator's call (engine OPEN-DECISIONS C). The engine spine only adds a Deferred row. Nothing was designed beyond study 30 |
| A new Library `placement` kind (27b S15, option 2) | Fields on `workflow-run` are enough (engine L14). The roster stays at 33 |
| Adding `supersedes` to Library AD-4 (27b S8, option 1) | Option 2 was taken instead: the engine uses `replaces`, so the relation count stays at 24 |
| Build ordering: probes E23 and E24 first, data packets first (27b N4, S21) | These belong to the build plan, not the architecture. Both are noted in OPEN-DECISIONS and the AD text |
| An atomic `NewChat.home` field in the harness | Ruling 24. AD-35 stores the home in `qmx_control` with a write-once route. Listed under Deferred |
| N3, N8, N9 | 27b itself says no change is needed |

---

## 4. Lint results

Command: `python C:\Users\Mubarak\Desktop\QMX\.claude\skills\bmad-architecture\scripts\lint_spine.py --workspace <folder>`, run after the last edit.

| Spine | ok | findings |
| --- | --- | --- |
| `architecture/workflow-engine/ARCHITECTURE-SPINE.md` | true | 0 |
| `architecture/library-and-data/ARCHITECTURE-SPINE.md` | true | 0 |
| `architecture/lab-and-pods/ARCHITECTURE-SPINE.md` | true | 0 |

During the pass, the engine spine briefly showed 2 low "template token" findings, because the new AD-35 used `{id}` in route paths. They became `<session_id>` and the spine is clean again. A final search across every target file finds no "twenty", "32-48", "semaphore 20", `ask_above_usd` (except the UI-HANDOFF line saying it does not exist), fake-provider default, `status test`, "keys over stdin", `reject_once`, "29 object kinds", "17 Library", "eleven verbs", `server-1` (except the Conventions line that bans it) or `refs/agents/<engine>`.

Every change is logged in each folder's `.memlog.md` as `event`, `decision`, `question` and `assumption` entries. The memlogs keep their CRLF endings, and every other file keeps its original line endings.

---

## 5. What he decides next (engine OPEN-DECISIONS, top)

- **A.** Grant H0, H15, H16 and H17. The recommendation is yes. Each has a no-edit fallback, so a "no" slows the build down rather than blocking it.
- **B.** Should the 50% plan background cap still apply to workflows? The recommendation is to keep it for plan accounts only.
- **C.** Should study 30 §4-§5 be accepted as the design for the first data packets? The recommendation is yes, starting with the 10 GB tick backup.

---

## 27d applied (2026-10-16, night)

This section applies `27d-fix-check.md`: 1 critical, 13 should-fix and 8 notes, plus its judgment-call conditions. Same rules as before: no sub-agents, no code, no commit. AD ids are unchanged and no AD was added. `lint_spine.py` still reports 0 findings on all three spines. Every change has a memlog entry.

### Critical

| # | Applied | Files |
| --- | --- | --- |
| C1 | **"Tested" keys on the definition `content_hash`.** All seven edits in 27d §2 are done. The semver is a Library annotation and the lifecycle is a ref fact; neither is stored in the definition. When the hashes match, `publish` copies `tested-by` onto the published object. A publish whose merge changed the hash needs a new test before enable. `extends` and `get_version_bundle` now name `workflow_item` and `object_id` | ENG SP AD-11, AD-14; SD §2.1 (removed `version`, `content_hash`, `meta.lifecycle`, `tested_hash`), §2.2, §6.1, §6.5, §8.1, E7; LIB SP AD-3, AD-15; LIB LLD workflow row; ENGINE-REQUESTS-ANSWERED mismatch 1; LAB LLD `drafts.publish` and `drafts.save` |

### Should-fix

| # | Applied | Files |
| --- | --- | --- |
| S-1 | The pod stage `draft` is renamed `untested`. "Draft" now means only the unpublished head on `refs/drafts`, which never sits on `main` | LAB SP AD-10; UI-TO-BACKEND-MAP pod row |
| S-2 | The trigger row is now `workflow_item, pinned_object, follow_champion, home_engine` | SD §4.1 |
| S-3 | A live run of a published version goes through `workflows_run`, which is MANAGE in both the Lab and the engine | LAB SP AD-13; LAB LLD `qmb.backtest` row |
| S-4 | The relay is the only key reader. `cli_inside` carries the run pass to the relay, and `qmx-egress` is only an allow-list. H8's fallback is fixed, H9 is marked superseded, and H11's fallback no longer adds a second key reader | SD §5.4 (three rows), §7.4, §16 note; HARNESS-REQUESTS H8, H9, H11 |
| S-5 | Per ruling 77, a model call with an unknown outcome is retried once and writes an `info` line. Only `irreversible_external` effects never retry and page him. Preflight severity follows AD-17. An engine crash is a `normal` item (a harness-level error) | ENG SP AD-8, AD-10; SD §3.4, §4.2, §10.2, §15 (three rows), E4 |
| S-6 | Wording fixes: `replaces`/`archived-as`; the AD-18 citation that replaced the old OPEN-6 one; L2, L3 and L13 marked "as asked"; L13 now says `workflow-run` | SD §3.4, §16; LIBRARY-REQUESTS |
| S-7 | The `ran-on → setup` relation and the "machine descriptors" leftovers are removed | LIB MIGRATION, LLD |
| S-8 | `ml.train` effect is `none`: it is checkpointed and memoised | LAB LLD §2 |
| S-9 | The kind lists for MANAGE merges into `main` are fixed | LAB LLD §8.5 |
| S-10 | Champion, challenger and workflow-memory owners follow the trigger's `home_engine`. A workflow with triggers on both homes is owned by `contabo` | LIB SP AD-7 |
| S-11 | An agent may merge into `refs/drafts`, but may not `put` onto it | LIB SP AD-7 |
| S-12 | `qmb.compile` and `qmb.compare` have base kind `script` | LAB SP AD-3 |
| S-13 | UI-HANDOFF line 48 now cites AD-16/AD-17 and says `waiting`. Line 62 now covers lifecycle kinds and cites Library AD-9 | `UI-HANDOFF.md` |

### Notes and judgment conditions

- N-1: SD §3.1 now says `failed` is terminal unless he resumes the run.
- N-2: AD-16 and SD §10.2 end a runaway pause after `limits.alert_after` too.
- N-3: AD-30 says the PC's 3 is a container cap, not a session cap.
- N-4: E8 sets `max_live_chats ≥ 8` first.
- N-5: Lab training uses a registry row as its placement.
- N-6: engine PLAIN-WORDS now says "token allowance".
- N-7: UI-HANDOFF says "chat status words".
- N-8: the engine spine's source tree is fixed.
- Judgment 1: a "day" in a 24-hour market is the session boundary (00:00 UTC for crypto), and each day's run ends before the next fire. The paper template's runaway wall time is one session plus 30 minutes (LAB SP AD-12; LLD §5.5, §9).
- Judgment 3: the test-on-save watcher refuses non-`workflow` kinds and validates before it tests (SD §13).
- Judgment 4: the Library OPEN-7 citation is split. The lifecycle-kind half rests on ruling 80. The governed-kind half rests on the existing recommendation, DEC-0188.

### Centralize

- `33-state-of-play.md` now reflects the current state:
  - rulings 1-88;
  - the HP stack merged into `rebuild/base` at `ed704c92` (verified in the QMX repo);
  - architectures amended through 27c and 27d (engine 35 ADs);
  - `ENGINE-PLAN.md` and `PROMPT-ENGINE.md` exist;
  - drafts 06, 07, 12, 19, 20a/b, 21 and 22 archived in `archive/2026-10-16-methodology-drafts/`;
  - open decisions merged, with his three calls first;
  - stale blockers struck.
- Wayfinder: 6 tickets are closed, each with a one-line resolution:
  - `engine-amend-chunking-compaction`
  - `library-engine-requests-l11-l14`
  - `session-homes`
  - `engine-open-6-self-improve-default`
  - `lab-open-5-lab-schedules`
  - `library-open-7-chat-merge-ask`

  There was no Lab OPEN-3 ticket: the map rewrite had already folded it in.
- Wayfinder: 6 tickets stay open with an "Update (27c/27d)" note, because part of the work is still owed or awaits his confirmation:
  - `central-relay-ruling-75`
  - `placements-and-capacity`
  - `provider-setup-from-skills`
  - `harness-h7-subagent-defs`
  - `engine-open-4-server-check`
  - `doc-changes-lab-and-pods`
- `python frontier.py` exits 0; the frontier went from 42 to 37.

### What changes under `ENGINE-PLAN.md` (not edited here; the planner should fold these in)

1. **EP3 (`model.py`, fixture, `overlay.py`).** The stored `qmx.workflow/1` document no longer holds `version`, `content_hash`, `meta.lifecycle` or `meta.tested_hash`. `content_hash` is computed. `extends` names `workflow_item` and `object_id`, so the overlay records the parent's object id rather than `(workflow_id, version)`.
2. **EP9 (`ports/library.py`, `service`).** ENGINE-PLAN lines 629 and 633 must change in four ways:
   - a version is `(item_id, semver annotation, object_id)`, not `fields.semver`;
   - `versions.publish` merges into `main`, sets the semver annotation and copies `tested-by` when `content_hash` matches;
   - enabling is keyed on a passed run (either mode) of the same `content_hash`;
   - a hash-changing merge needs a new test.

   Add a lane for "publish an unchanged tested draft, then enable succeeds", which is 27d C1.
3. **EP7 (`effects.py`, E4 lane 3) and EP11 (lane 4, `e04b_agent_unknown.py`).** An unknown outcome on a **model call** is retried once with an `info` line and no inbox item. Only `irreversible_external` effects never retry and raise an `urgent` item with the idempotency key. EP11 lane 4's pass condition ("nothing retries automatically and one `system_fault` item") must flip. EP7's script case holds only if that script node is `irreversible_external`.
4. **EP12 (`preflight.py`).** It already grades by cause. Make sure that an `info` digest line, not an item, is raised when the workflow's own configuration is at fault, which matches §10.4.
5. **EP13 / any `cli_inside` path.** No key is injected by `qmx-egress`. The pass goes to the relay. Until H11 is granted, `cli_inside` and `host_harness` nodes are not scheduled.
