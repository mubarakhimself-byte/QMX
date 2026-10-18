# 47. Studies 44, 45 and 46 folded into the architecture

Written 2026-10-18 by the architect (Opus 5.5), headless, BMad architecture skill in amend mode, with the codebase-design and domain-modeling vocabularies (deep modules, seams, one word per concept). No sub-agents; the reviewer gate ran inline (§10). Nothing committed.

**Inputs read.** `43` (the base: one host, the turn API, the guard, packs as plugins, one run system, capacity classes, deletions), `44` (agentic-engineering foundations), `45` (the Lab, Library, workflows and mini apps as one domain model), `46` (domain expansion: 214 ideas, 34 kept scenarios), `26` (rulings 1-118), the three architecture spines with their memlogs, `SOLUTION-DESIGN.md`, `HARNESS-REQUESTS.md`, `OPEN-DECISIONS.md`, `UI-HANDOFF.md`, `HARDENING-PLAN.md` (read only). Code truth: `claude-agent-sdk` 0.2.166 as installed in the engine run's venv (`types.py`, `subprocess_cli.py`) [retrieved]: `ClaudeAgentOptions.skills` is a per-chat skill filter by name or `plugin:skill`; `AgentDefinition.skills` exists; `system_prompt` takes `{type: file}`, which replaces the preset, and the SDK has no append-from-file form.

**Files changed (all under `tracker/qma-v2/`).** Engine `ARCHITECTURE-SPINE.md` (AD-61 to AD-66 added; AD-4, 5, 7, 10, 11, 13, 15, 18, 19, 20, 22, 23, 26, 27, 35, 39, 41, 43, 45, 46, 47, 48, 50, 55, 57, 58 amended in place; layer table, conventions, seed, capability map, deferred), `SOLUTION-DESIGN.md` (§28), `HARNESS-REQUESTS.md` (section K, H46-H52), `OPEN-DECISIONS.md` (his two word questions), `DOC-CHANGES.md` (rows 46-50), `PLAIN-WORDS.md`, `.memlog.md`; Library `ARCHITECTURE-SPINE.md` (AD-22 to AD-24 added; AD-3, 4, 6, 7, 8, 9, 15, 18, 19, 21 amended; seed roster by class), `.memlog.md`; Lab `ARCHITECTURE-SPINE.md` (AD-2, 4, 6, 8, 9, 16, 18 amended; seed residue fixed), `LLD.md` (two residue rows), `.memlog.md`; `UI-HANDOFF.md` (§15 added, §4 and §5 rows fixed); `26` (ruling 119); `README.md`. `lint_spine.py`: 0 findings on all three spines. `HARDENING-PLAN.md` and `PROMPT-HARDENING.md` were not touched.

---

## 1. Summary in plain words

1. **Your choice of Hindsight is now a ruling (119)** and the design. Hindsight is the engine that finds memories for the copilot and for workflows. The memories themselves stay QMX's own records, so Hindsight can be rebuilt or swapped without loss, and the simple built-in search stays as the backup. Memory now follows the thing you worked on (a pod, a workflow, an app), not the folder: what a Lab chat learned about a pod is found by a new hub chat and by that night's workflow. Lessons carry the period and market regime they were true for. "Forget" hides one. Hindsight runs on your PC until your server exists, then moves there with nothing to migrate.
2. **Every tool is one row in one list,** in small named sets. A chat or a workflow step gets only the sets it needs: an overnight intake on Kimi sees about fifteen tools instead of eighty-two, which matters most on the Chinese models you use, and a helper never gets more than its parent. Tool names are checked so no provider refuses them.
3. **One place decides what each chat is told and given,** in named slots (rules, persona, methodology per home, each app's notes, skills, memory) and records a fingerprint of it, so "what did the model see" always has an answer. Your later work on prompts drops into those slots with no code.
4. **Point at anything with @:** a pod, a run's output, an app's latest result, a file, a folder, a website, a video. The chat keeps that list when you reopen it from another screen. A video still being transcribed shows "pending" and never blocks you.
5. **Things talk two ways only:** ask something to act, or leave a result in the Library that something else watches for. It works across your PC and your server with nothing new to run. Each mini app keeps its saved state on one machine, can have several setups (one per currency pair) without copying, and tells its consumers when its output is stale or its format changed.
6. **Bad news travels.** Mark a data release as bad and every result, lesson and idea built on it shows it, with the path, and the schedules that use it pause. Clear the mark and all of it clears, because nothing was written onto the results.
7. **Ideas have a status** (supported, refuted, open, mixed by market regime) computed from the tests behind them, on an "Ideas" shelf.
8. **Two machines never build the same thing at the same time;** the server never runs a definition it does not understand; one button pauses all autonomous work everywhere.
9. **The Library rules got simpler:** results land at once, things you build wait for your one yes, trading records move only by your click. One rule replaces five lists that disagreed. A board is a workflow draft drawn as notes and cells. Lab results on a draft bot count as real evidence when the procedure is a published one.
10. **A test set for the copilot itself** runs whenever its instructions, skills or default model change, and shows its result on the card you click.
11. **Rejected:** the tool-based skill reader study 44 proposed. Since the unlock pass, apps load as real plugins and the SDK filters skills per chat, so the CLI's own skill tool already serves every model.
12. **Two questions about words stay yours** (§8). Nothing waits on them.

---

## 2. How the studies met study 43 (conflicts resolved)

| # | Study text | 43 (or another study) | Resolution |
| --- | --- | --- | --- |
| C1 | 44 assumes one SHA-locked plugin, the money gate, and a "harness grant?" column on every change | AD-53 (no grants), AD-54 (the guard), AD-55 (packs are plugins) | Read as superseded wording; every 44 change is an ordinary change; the bridge unwraps names before the guard |
| C2 | 44 DC-5: QMX `skill_list` and `skill_view` rows, because "only the plugin's own skill files exist" | AD-55 loads every pack's skills natively; the SDK has a per-chat `skills` filter [retrieved] | DC-5 rejected as rows; its parts (conditional activation, usage counts, Library skills outside packs) land in AD-55 and AD-62 |
| C3 | 44 DC-2: one `qmx` server built per chat, filtered | AD-55: one in-process server per pack, toggled per session | Generalised: every toolset is one in-process server, core ones included, toggled with the same call (AD-61); no relaunch on a scope change |
| C4 | 45 §2.5d: "the harness never loads a pack as a second plugin; the SHA-locked plugin stays" | AD-55 | 43 wins: the pack folder is loaded as a plugin; 45's real point (the operation is the contract) is kept in AD-61 |
| C5 | 45 §2.9 and 46 X-3: `attached` "beside `session_homes`" | AD-35 dropped that table; Library AD-21 made sessions items | The list lives on the harness chat record (owner), mirrored by the session recorder into the Library item (AD-63) |
| C6 | 45 §2.3: "sessions are not Library items" | Library AD-21 | 43 wins |
| C7 | 45 DC-4 keeps `memory_mb` and `cpu_percent`; 43 AD-57 retires the CPU-percentage breaker | — | Both hold: no breaker, no budget; the two numbers survive only as machine isolation he may set, unset by default |
| C8 | 45 and 44 use probe P-PK (`tools/list_changed`) | P-TG (`toggle_mcp_server`) | P-PK is superseded by P-TG |
| C9 | 46 says study 43 is not on disk and Library AD-21 is "memlog only" | Both exist now | Reconciled; 46's X-3 lands on Library AD-21 and AD-63 |
| C10 | 44 calls the domain unit a "tool"; 45 calls it an "operation"; 44 and 45 each give "pack" and "plugin" two meanings | — | One word each (AD-61): operation (the contract row), tool (an operation as a model sees it), toolset (the unit of scope), pack (the installable unit), plugin (the Claude format and its loading only) |
| C11 | 46 X-11 "steer a running workflow" with a new overlay on a live run | AD-11: live runs refuse drafts | A live fork takes only the overrides a live start allows (role and model, declared inputs); any edit is a test-mode replay fork of a draft (AD-7) |
| C12 | 45 DC-1 governed class (his click) against Library AD-18 landing `unit` from runs | — | 45 wins: governed objects a run produced wait on `refs/drafts`, visible to Lab reads; nothing waits on him |
| C13 | 44 DC-6 "needs his ruling" for standing grants | rulings 57 and 80 | Decided without a new ruling: his existing publish click covers what the card lists; publish, enable, governed and definition merges, settings, quarantine, purge and money proposals are never grantable |
| C14 | 46 "router role `memory`" against 44 "`memory_extractor`" | — | `memory_extractor` |
| C15 | 46 "hypothesis" and "forget" as words for him | — | Defaults taken (an "Ideas" shelf; forget hides and keeps a restorable copy); he may rename; not listed as questions |

Found while folding, and fixed: engine AD-26 still reused `qma.core.ports.refinement` although AD-59 deletes `qma-core` (the refusal rules are now carried into the engine first); the engine layer table still named "control session homes" after AD-35 moved the home; the Lab seed and LLD still showed the retired container kernel and a `.mcp.json`; UI-HANDOFF §4 still said 33 kinds.

---

## 3. Decision table: every design change

Counts: **55 items**: 45 adopt, 8 merge, 1 reject, 1 defer. "Engine" ADs unless marked Lib (Library) or Lab.

### 3.1 Study 44 (15 items: 13 adopt, 1 merge, 1 reject)

| Item | Decision | Where | Blast radius (spec / built code) |
| --- | --- | --- | --- |
| DC-1 one tool catalog | ADOPT (absorbs 45 DC-2) | AD-61 `OperationSpec`; `qmx_control.catalog` | spec: AD-4 now has `reversibility` to read, Lab and Library tool tables become rows / code: `qmx_control/server.py` `OPERATIONS`, `qma/harness/tools.py` tables, every `mcp__qmx__*` name renamed once |
| DC-2 toolsets as the unit of scope | ADOPT | AD-61, AD-62, AD-4 (node `toolsets`), AD-35, AD-41 | spec: node schema, 31 templates declare toolsets / code: `chat.py` `_tools`, `nodes/agent.py` `rules()`, `HarnessPort.start_chat` |
| DC-3 wire-name rule | ADOPT | AD-61, `qmx app check`; probe P-NM | spec: AD-19 names, Lab `qmb.*` ids stay catalog ids / code: registration check |
| DC-4 discovery per lane | ADOPT; probe merged into the existing P3 | AD-61, AD-39 (`tool_search: native | bridge | none`), AD-50 | spec: registry field / code: `profiles.py` quirks to registry rows; bridge only if P3 fails and a surface exceeds about 30 tools |
| DC-5 QMX skill rows | **REJECT** as rows; parts merged | AD-55, AD-62 | the CLI's Skill tool with the SDK `skills` filter serves every model behind the router; nothing to build |
| DC-6 standing grants at publish | ADOPT (no new ruling) | AD-4, AD-22, AD-26 | spec: publish card, AD-26 hard limit / code: `Grants` keyed by (version, operation) |
| DC-7 one Surface module | ADOPT | AD-62 `qma.harness.surface` | code: `launch.py`, `chat.py`, `nodes/agent.py`, `prompts.py`; the AD-15 snapshot test |
| DC-8 prompt slots and budgets | ADOPT; probe P-SYS | AD-62 | spec: Library `persona`, `methodology` items / code: launch; the 30,000-character command-line check stays |
| DC-9 result discipline | ADOPT (generalises AD-34's spill) | AD-61 `result` | code: the catalog wrapper, control list endpoints |
| DC-10 copilot eval battery | ADOPT | AD-66 | a template and fixtures; publish and Settings cards |
| DC-11 revolution loop | ADOPT; probe P-NEST | AD-5 (sanctioned nesting), AD-26 (reframe), AD-46 | templates; possibly one validator exception |
| DC-12 calibration as contract | ADOPT (absorbs 46 X-13, K-05) | AD-45, AD-13 | template schemas, `render-and-grade`, a grader mode `claims`, a directive `::value` |
| DC-13 subtractions | MERGE | AD-61 (subtracted list), AD-59 step 4 (LangChain wrapper), AD-55 (one meaning of plugin) | `qmx_tools/registry.py`; `apps_call` leaves the agent surface |
| DC-14 Hindsight default | ADOPT; ruling 119; probe P-MEM | AD-18, `qmx_memory` | spec: 39 §5 C M-18, H-141 superseded (DOC-CHANGES 49) / code: `ports/memory.py` stub gets real adapters |
| DC-15 context references | ADOPT (absorbs 46 X-3) | AD-63, H49 | chat record field, composer, `context` toolset, intake templates |

### 3.2 Study 45 (15 items: 13 adopt, 2 merge)

| Item | Decision | Where | Blast radius |
| --- | --- | --- | --- |
| DC-1 three classes, one landing rule, kinds as data | ADOPT | Lib AD-3, AD-9, AD-18; engine AD-11; Lab conventions | spec: four kinds retired (`board`, `bot-card`, `logic`, `template`), `pod-block` merges become MANAGE, copilot records land / code: none (Library unbuilt; the engine fake's kind check unaffected) |
| DC-2 operation is the one contract | MERGE into 44 DC-1 | AD-61, AD-64 (pins revalidate) | `definition/registry.py` packs already exist; `app_op` executor is new work |
| DC-3 two channels; events are ref-log rows | ADOPT; probe P-EV | AD-64, AD-10, AD-19, AD-23 | spec: `emits`/`accepts` retired / code: `qmx_apps/artifacts.py` through a Library adapter; trigger-kind migration (already planned) |
| DC-4 app "when" to the engine; budgets go | MERGE into 43 AD-57 | AD-57, AD-19 | `qmx_apps/manifest.py` `Schedule`, `Budget`; supervisor config; examples |
| DC-5 one lifecycle | ADOPT | AD-11, AD-46, AD-19 | wording; the built `ALLOWED` table stays; road stages write `test-report`s |
| DC-6 one home per app instance; `state` on operations | ADOPT; probe P-APP | AD-64 | `qmx_apps` `VolumeLease` reused; lazy start from a bundle by hash is new |
| DC-7 no permission union across apps | ADOPT | AD-64, AD-41, AD-19 | wording; `call_depth` setting |
| DC-8 draftness belongs to the procedure; the door decides evidence | ADOPT | Lab AD-4, AD-8; Lib AD-18 | Lab (unbuilt); UI labels |
| DC-9 the board is a workflow draft | ADOPT | Lab AD-2, engine AD-5, Lib AD-3 | Lab document registry; DOC-CHANGES 46 |
| DC-10 DevOps through one shape | ADOPT (absorbs 46 X-7, X-14) | AD-65, AD-15 | heartbeat schema mapping of the built app heartbeat |
| DC-11 Library primary defaults to the server | ADOPT; probe P-LAT gates the flip | Lib AD-19 | the Contabo setup step |
| DC-12 loops end by the intent key | ADOPT | AD-27, AD-64 | the memory packet's real `check_built` |
| DC-13 residue that contradicts settled ADs | ADOPT (done in this pass) | Lab seed, Lab LLD rows 344 and 485, UI-HANDOFF §4, engine AD-11 list | documentation only |
| DC-14 `EngineLibraryAdapter` | ADOPT | Lib AD-15 | Library build scope; the engine's fake tests become contract tests |
| DC-15 search corrected against the clipping | ADOPT (absorbs 46 X-15); probe P-SRCH | Lib AD-8 | `qmx_control/library.py` FTS5 stays until migration |

### 3.3 Study 46 (25 items: 19 adopt, 5 merge, 1 defer)

| Item | Decision | Where | Blast radius |
| --- | --- | --- | --- |
| X-1 marks on roots, derived at read | ADOPT; probe P-TAINT | Lib AD-22 (`marks`, `mark`), engine preflight, AD-18 recall weight | one reserved ref, one read function, one preflight rule |
| X-2 hypothesis kind and computed status | ADOPT | Lib AD-23, AD-3, AD-4 (`tests`); Lab AD-18 | one schema, one relation, one `outcome` field, one status function |
| X-3 `attached` on the session | MERGE into 44 DC-15 | AD-63, Lib AD-21 | H49 |
| X-4 validity window, regime, forget, Hindsight via the router | ADOPT; probe P-MEM | AD-18 | `memory-row` identity and annotations; `RecallEngine.delete` |
| X-5 app contract evolution, freshness, coalesce | ADOPT | AD-64, AD-10, AD-19 | `app.toml`, the trigger row, `qmx app check` |
| X-6 in-flight claims renewed by heartbeat | ADOPT; probe folded into P-EV | Lib AD-24, AD-27, AD-65 | two verbs, a transient namespace |
| X-7 version and kind digest on heartbeats; drain before update | ADOPT; update drill | AD-65, AD-20, AD-48 | heartbeat schema, preflight |
| X-8 priority, ready-by, market-open precheck | ADOPT | AD-10, AD-58 | trigger migration, `admission.py` order (built, small) |
| X-9 promote a session loop to a server workflow | ADOPT | AD-47 | builder skill, loop card |
| X-10 crystallise | ADOPT | AD-26 | improve workflow move; a template pattern |
| X-11 fork a run from a node | ADOPT (reconciled with AD-11, C11) | AD-7 | engine service API |
| X-12 app profiles | ADOPT | AD-64, Lib AD-3 (`app-profile`) | operation descriptor; `qmx_apps` volume layout (additive) |
| X-13 panel and answer discipline | MERGE into 44 DC-12 | AD-45, AD-46 | a template; prompt slot rule |
| X-14 `ops` toolset, bring a run home | MERGE with 45 DC-10 | AD-61 (`ops`), AD-65, AD-7 | catalog rows, Hub ingestion |
| X-15 search ranking, record retention | MERGE into 45 DC-15 | Lib AD-8, Lib AD-6 (curator rule) | ranking features |
| X-16 redaction at land, operator-only purge | ADOPT; purge drill | Lib AD-6, AD-9; engine AD-37 | the one exception to archive-never-delete |
| X-17 global autonomy pause | ADOPT | AD-10, AD-65 | one Settings flag, ticker check |
| X-18 data locality in placement | **DEFER** to the data study (ruling 91); seam named | AD-65 heartbeat field | none now |
| X-19 holdout touch ledger, similarity check | MERGE (the `touched` edge and Lab AD-5/AD-6 already count touches); similarity check adopted | Lab AD-16, Lib AD-4 | one publish check |
| X-20 checkpoint resume, GPU class | ADOPT; preemption drill deferred (paid provider, his money) | AD-4, AD-58 | node contract field |
| X-21 comparability key, resolved model id, run diff | ADOPT | AD-15, Lab AD-6 | result schema, span field, `explain.diff` |
| X-22 session fork | ADOPT; probe P-FK | AD-35, H50 | `Harness.fork` |
| X-23 "last look" cursor | ADOPT | AD-46 (digest template; one control row) | one row |
| X-24 locator on `derived-from` | ADOPT | Lib AD-4 | edge attribute |
| X-25 cell dependency capture | ADOPT; probe P-CELL | Lab AD-9 | Lab LLD |

---

## 4. Ambiguities and churn, resolved

| Topic | Resolution | Where |
| --- | --- | --- |
| One Board shape | A board is a workflow draft shown with `meta.view: board`; notes are `note` nodes, cells are `lab.cell` nodes; no board kind | Lab AD-2, engine AD-5, Lib AD-3 |
| One kind list | Each kind schema carries `class: record | definition | governed`; code reads the class; the roster is data (seed table) | Lib AD-3 |
| One mini-app lifecycle | Engine AD-11's: draft, published, enabled, disabled, archived; validated, tested, stale are marks; road stages are evidence; "suggest" is a list | AD-11, AD-19, AD-46 |
| One meaning of "plugin" | The Claude plugin format and the CLI's loading of it; a **pack** is the installable unit (mini app, agent, Lab, built-in group) whose folder is in that format plus `app.toml`; an **operation** is the contract; a **toolset** is the scope | AD-61, AD-55 |
| Lab results reaching the Library | Draftness belongs to the procedure: a published procedure on a draft subject is a live run and lands citing the exact object; only edited procedures run in test mode | Lab AD-4, Lib AD-18 |
| Where a mini app runs and keeps state | One home machine per instance; operations declare `state`; stateless ones run where called, stateful ones route home and wait if it is away; moves are snapshot and restore | AD-64 |
| The app scheduler and `runs=1000` | The app's "when" is an engine trigger created at his enable; `runs` and `cpu_seconds` budgets deleted; memory and CPU numbers only as optional isolation, unset | AD-57, AD-64 |
| The graph as refusal gate | Only plain facts refuse (nothing matched, only archived, nothing as of that date); the graph gives provenance and the admitting edge per item; abstention comes from calibrated confidence | Lib AD-8, engine AD-45 |
| Ref namespaces growing | One stated rule (each principal writes only refs it owns; `main` moves by publish, landing rule or merge); two new reserved namespaces, each tied to an owner | Lib AD-7 |
| Two `LibraryPort`s | Both kept: the engine's built port is its view; the Library ships the adapter | Lib AD-15 |
| Kernel for cells | A local process in the run's Job object by default; the container kernel by his choice; residue fixed | Lab AD-9, seed, LLD |
| App I/O words | `feeds` and `provides`; `emits` and `accepts` retired | AD-64, AD-19 |
| Copilot artifacts never reaching the Library | Chat records land at turn end through the session recorder | Lib AD-18 |
| An app's agent as a helper | Only from that app's own sessions and runs; across apps ask through operations; no permission union | AD-64, AD-41 |
| Cross-machine events | Event triggers read the Library ref log, which replicates; the bus is UI-only | AD-64, AD-23 |
| Several instances of one app | Profiles inside one instance; a truly different app is a variant pack | AD-64 |
| His Lab draft while the copilot edits | The agent edits its own ref and merges; a clash is a merge-conflict; workflow drafts merge per node | Lib AD-7 |
| Evidence from a notebook cell | Exploration, never cited; "rerun for evidence" offers the QMB door | Lab AD-8 |

**Study 46's three root mechanisms.**

| Mechanism | Decision | Where |
| --- | --- | --- |
| Marks on source items, worked out at read time | One stored mark (`quarantined`, his act, on a reserved ref); `superseded` and `corrected` computed from refs and `replaces` edges; `marks()` walks `consumed`, `derived-from`, `uses`, `compiles-to` upstream per object shown; preflight, recall, hypothesis status and search read it | Lib AD-22 |
| Memory validity windows and regime tags | `valid_from`, `valid_to` in a memory row's identity, `regime[]` as annotations; recall filters or boosts by `now` and the current regime | AD-18 |
| Claims on in-progress work renewed by heartbeat | `claim` and `release` as compare-and-swap on transient refs of the primary; batch renewal on each heartbeat; offline claims locally and accepts a rare duplicate | Lib AD-24, AD-27, AD-65 |

---

## 5. Scenario coverage (46's 34 kept scenarios)

| # | Scenario | ADs that carry it | Edge cases and how they hold | Probe |
| --- | --- | --- | --- | --- |
| K-01 | One idea end to end: video, hypothesis, tests, verdict, paper | Lib AD-23, AD-4 (`tests`, locator); Lab AD-4, AD-8, AD-6, AD-12; AD-34; AD-45 | video deleted after intake (blob kept by hash, AD-42); two hypotheses share one test (one result `tests` both); restated a month later (recall by `item:` and text, AD-18) | — |
| K-02 | A session moves between places and pulls context | AD-63, AD-35, Lib AD-21, AD-42 | video still transcribing (`pending`); 2,000-file folder (200 entries, 25 %/50 % window shares); archived item (`archived`, readable); offline remote blob (`not_cached`) | — (E62) |
| K-03 | Memory follows the subject, respects regimes, can forget | AD-18, ruling 119, Lib AD-22 | conflicting lessons kept with their windows; lesson from a tainted run down-weighted; forget archives and deletes from the index, rebuild skips it; extractor through the router; PC offline uses FTS5 | P-MEM |
| K-04 | The hypothesis ledger | Lib AD-23, AD-22; Lab AD-6, AD-18 | tainted result turns status to open; regimes give "mixed, by regime"; prose "supported" with no result is ignored | — (E66) |
| K-05 | Honest numbers everywhere | AD-45, AD-13; Lab AD-8; QMB robustness (built) | rounded prose loses to the rendered value; a number in no item reads `unverified`; control beats strategy, so "no edge over random" (the matched-control option is a QMB-session item) | — |
| K-06 | Family and holdout accounting across agents and machines | Lab AD-5, AD-6, AD-16; Lib AD-4 `touched`; qmf-data seal (built) | unlinked variant gets a proposed `variant-of`, counted at once; holdout read through a general data tool refused by the built seal | — |
| K-07 | Bad news travels | Lib AD-22; AD-20 preflight; AD-7 memo reuse; AD-18 | indicator bug marks the component version; poisoned memory down-weighted; a widely used item walked per object shown; clearing restores everything | P-TAINT |
| K-08 | The Lab and an app use one object; inputs move on | Lib AD-2, AD-7, AD-22 (`superseded`); AD-64 (state in the app's volume) | reads by immutable id never conflict; two writers merge or conflict; "newer input exists" offers a rerun | — |
| K-09 | Mini apps feed mini apps across machines and change over time | AD-64, AD-10, AD-19; Lib AD-11 | flood (`coalesce: latest`); producer dies (last output, `stale`); fan-in dedupe per trigger and object; consumer's PC asleep (the trigger's home decides); schema change refused until consumers adapt | P-EV |
| K-10 | One app, many setups | AD-64 profiles; Lib AD-3 `app-profile` | profile edited mid-run (run pins its version); one corrupt partition restored alone; a new skill needed means a variant pack | — |
| K-11 | Ask the panel; show the spread | AD-45, AD-46, AD-64, AD-38 | a member times out (shown absent); all agree on a checkable fact (noted as weak evidence); same family as the judge (labelled) | spread on 20 of his questions (informative, not a gate) |
| K-12 | Four writers on one workflow | Lib AD-7 (workflow merge driver added in this pass), AD-26, AD-49 | merges per node id and parameter; an invalid merge becomes a merge-conflict | property tests on random graph edits |
| K-13 | Two runs start the same build at once | Lib AD-24, AD-27, AD-65 | claimant dies (claim expires within one `ttl`); Hub unreachable (local claim, rare duplicate deduped by the key) | P-EV (claim round trip) |
| K-14 | Remote work and data gravity | Lib AD-10 to AD-14; AD-20, AD-30; AD-65 seam | cache eviction refetches by hash; slow bucket; offline `not_cached`; the locality score is deferred to the data study | P-APP |
| K-15 | One ops picture across machines | AD-65, AD-61 `ops`, AD-15, AD-58, AD-40 | heartbeat volume; PC disk (rolling window, server keeps the rest); Hub lag on the doctor page; spend per subject is a reading | P-OPS |
| K-16 | Scheduling in market time, under contention | AD-10, AD-58 | DST (IANA zone, built); holiday (calendar); equal priorities by age; a low-priority fan-out yields between chunks | — |
| K-17 | Market events drive work | AD-10 (webhook home `contabo`, delivery-id dedupe), AD-64 | duplicate deliveries deduped; a flood coalesces | — |
| K-18 | A copilot loop outlives the laptop | AD-47, AD-63, AD-22 | session context moves as inputs; a loop that needs his logged-in browser stays local with a note | — |
| K-19 | Workflows crystallise | AD-26 | a silent mislabel caught by the guard set and by sampling one item in N to the agent | equivalence on 20 replays (template check) |
| K-20 | Steer a running workflow | AD-7, AD-11 | a change that is not an allowed live override opens the draft and runs as a test fork | — |
| K-21 | A standing research employee | AD-35 (home `agent`), AD-55, AD-64, AD-30 | its machine down (routines wait `placement`; `ask` says home unreachable with the last landed brief); two employees disagree (the panel) | — |
| K-22 | A mini app breaks at 3 a.m. | AD-65 (incident classes, producer blame), AD-64 (`stale`), AD-57 (crash-loop breaker), AD-22 | consumers read the last good output marked stale; a fix waits as a draft | — |
| K-23 | Long training on a rented GPU | AD-4 (`checkpoint`), AD-58 (`gpu_slots`), AD-57, Lib AD-13 | preemption resumes from the latest checkpoint | preemption drill, deferred until a GPU provider is paid (his money) |
| K-24 | Version skew and upgrades | AD-65, AD-20, AD-48 | a new node kind placed only where it exists or waits "needs update"; drain before restart | update drill |
| K-25 | Library hygiene at scale | Lib AD-8 (ranking), Lib AD-6 (curator archives uncited test records, added in this pass), AD-46 | nothing deleted; search ranks trusted results first | P-SRCH extended with noise |
| K-26 | Ask QMX about its own past | Lib AD-8, AD-9 (`as_of`), AD-21; AD-18 | admission reason per item; abstains on thin evidence | P-SRCH |
| K-27 | A secret lands in the Library | Lib AD-6 (`purge`), engine AD-37 (redaction at every put) | refused at landing; if one slips through, his purge tombstones it on every copy | purge drill |
| K-28 | Pause all autonomy | AD-10, AD-65 | running attempts finish their node; chats untouched; one catch-up per trigger on resume | — (E64) |
| K-29 | A notebook cell graduates into a workflow | Lab AD-9 | hidden kernel state found by a namespace diff, confirmed by him or the copilot | P-CELL |
| K-30 | Fork a session for parallel what-ifs | AD-35, Lib AD-7 | each fork has its own agent ref; a compare explainer follows | P-FK |
| K-31 | His clippings flow into research | AD-46 template, AD-10, AD-27 | dedupe by hash and intent key | — |
| K-32 | The morning digest | AD-46 template; an operator cursor row | "since last look" from the ref log | — |
| K-33 | Disaster recovery | Lib AD-16, `backup.py` (built); restore order deferred to the data study (ruling 91) | the drill template ships once the order is written | drill after the data study |
| K-34 | Reproduce a months-old result | AD-15 (comparability key, `model_resolved`, `explain.diff`), Lab AD-6, AD-7 | a changed model behind an alias shows as drift | — |

All 34 are covered. Two needed changes this pass made beyond the X list (the workflow merge driver for K-12 and the curator retention rule for K-25); two keep an owner outside this design (the locality score in K-14 and the restore order in K-33, both with the data study, ruling 91).

---

## 6. Probes

New in this pass (exact lines in SOLUTION-DESIGN §28.8): **P-NM** (tool-name length and dots on the pinned CLI), **P-SYS** (append text from a file), **P-NEST** (a loop calling a subworkflow that holds a loop), **P-MEM** (Hindsight against the built-in search on his material, RAM, retain cost, the extractor through the router, deletion by id), **P-EV** (PC commit to server trigger, and a claim round trip), **P-APP** (an app server on the server from a bundle; a lease handover), **P-LAT** (Library screens with the server primary), **P-SRCH** (grounder precision and coverage, truncation, ranking under noise), **P-TAINT** (the mark walk on 100,000 items), **P-OPS** (heartbeat volume), **P-CELL** (five real notebooks). Kept: P-TG (now also covers core toolsets), P-PL (extended to the skills filter), P-FK, P3 (now also sets `tool_search` per row, absorbing 44's DC-4 probe), P0, P1, P1k, P2, P4, P-PERM, P-SET. Superseded: P-PK. Drills, not gates: purge, update, preemption (deferred, money). Live checks E60-E67 added.

---

## 7. Effect on the program (`HARDENING-PLAN.md` is not edited here; the planning lead edits it)

Read beside 43 §10, which this extends.

| Packet | Effect | After |
| --- | --- | --- |
| HG3 (the turn-API packet of 43) | **widen**: `NewChat.skills`, the `attached` field and `Harness.set_attached`, `Harness.fork`, home kind `agent` (H48 to H51) | P-SET, P-PERM |
| HRMH (the guard packet of 43) | add: the guard refuses a tool outside the chat's surface (lands with CAT) | — |
| PACK (43) | **re-sequence after CAT**: packs declare `[operations]`; the `library-skills` view (H48); P-PL extended | CAT |
| HRME | **widen into TRG2**: priority, `ready_by`, the `market_open` precheck, the webhook home default, the local pause flag; the `event` trigger on the Library ref log and `coalesce` wait for LIB1 | — / LIB1 |
| CAPX (43) | add priority order in admission and `gpu_slots` | — |
| DEL4 (43) | add the LangChain wrapper in `qmx_tools/registry.py` | caller scan |
| New **CAT** | one operation catalog, toolset servers, wire-name check, result envelope, the `ops` toolset, the one-time rename (AD-61) | the guard packet, HG3; P-NM |
| New **SURF** | the Surface module, slots and budgets, surface digest, snapshot test per chat and node kind (AD-62) | CAT; P-SYS |
| New **EVAL** | the copilot eval battery template (AD-66) | SURF |
| New **REF1**, **REF2** | context references for Library kinds, runs, apps, sessions and memory (REF1); files, folders, URLs and videos (REF2, with the multimodal packet) (AD-63) | SURF, SES; REF2 after MM |
| Appendix G **MEM** | **rewritten and scheduled**: `qmx_memory` with Hindsight and the FTS5 adapter, the copilot retain worker, validity and regime fields, forget (AD-18, ruling 119) | LIB1 (or the engine fake until then); P-MEM first |
| New **OPS** | one heartbeat schema, kind digest in preflight, drain before update, `fetch_home`, the pause flag synced (AD-65) | L1, RUN1; the sync part after LIB4 |
| Appendix G mini-app packet | **widened into APP2**: two channels, app artifacts into the Library, homes and `state`, profiles, freshness, contract check, no permission union, isolation unset (AD-64, AD-19) | PACK, CAT, LIB1; P-APP, P-EV |
| New **FORK** | run fork from a node and session fork (AD-7, AD-35) | BUG3, REPLAY |
| New **TPL3** | revolution loop, panel, clippings intake, morning digest, loop-to-server, crystallise pattern (AD-46, AD-26, AD-47) | TPL1, TPL2; P-NEST |
| Library program (named for the planner) | **LIB1**: store, kinds with a class, the landing rule, redaction at put, `EngineLibraryAdapter`; **LIB2**: marks, hypotheses, locators, `as_of`; **LIB3**: search corrections and ranking; **LIB4**: the Hub, claims, the primary flip, purge | P-TAINT (LIB2), P-SRCH (LIB3), P-LAT (LIB4) |
| Lab program | draftness and the evidence door, the board as a view, cell graduation, the similarity check | the Lab packets; P-CELL |
| Dropped | P-PK (superseded by P-TG); 44's skill rows; the tool-search bridge unless P3 fails; Appendix G "session homes table" (already gone in 43) | — |
| BLOCKED-ON list | unchanged from 43: only probe gates | — |

---

## 8. His two word questions (from study 45; not decided here)

1. **Does "strategy" stay a word you use?** The risk session owns "unit", the Library shows bots, and today `strategy` is the stored mirror of a strategy family. (Recommendation only: keep it as the name of a family of bots; say "bot" for the thing that trades.)
2. **Is one folder shape with two names fine?** A mini app (something you use) and an agent (a persona with its own instructions, skills and routines) are built the same way, under two names. (Recommendation only: yes.)

Both are also in `architecture/workflow-engine/OPEN-DECISIONS.md` (W1, W2). Nothing waits on them.

---

## 9. What stayed outside this pass, with owners

- The risk and sizing unit math: its seams are unchanged (Lab AD-7 slots, AD-11 ports, AD-16 identity table, engine AD-43 locked keys); owner: the risk session.
- The UI: `UI-HANDOFF.md` §15 lists eighteen landings; owner: the UI session.
- Data: the locality score, the restore order across stores and the tick backup; owner: the data study (ruling 91).
- The Library and Lab HLD and LLD companions were not re-projected from the amended spines (the spines win); owner: the next documentation pass (DOC-CHANGES rows 46 to 48).
- The matched-control backtest option (`control: random_entries`): owner: the QMB session.
- Paying for a GPU provider (the preemption drill): his money call.

---

## 10. Reviewer gate (inline; no sub-agents were allowed)

- **Lint.** `lint_spine.py`: 0 findings on all three spines (one low finding, a brace-shaped locator example read as a template token, was reworded).
- **Rubric walk.** Each new AD (engine 61 to 66, Library 22 to 24) has Binds, Prevents and an enforceable Rule, and fixes a divergence two builders would otherwise create: who decides a chat's tools and text; what an operation is called and where it is declared; where attached context lives; how apps exchange data across machines; which channel carries live facts between hosts; how prompt changes are tested; where a taint lives; how a hypothesis status is known; how two hosts avoid duplicate builds. The operational envelope is covered: where Hindsight runs before and after the server exists, heartbeat volume, the pause switch, version skew and drain.
- **Currency lens.** No new library version is bound. Hindsight is bound as a product choice (ruling 119), not a version; its facts are study 44's retrieved ones, and P-MEM checks the ones that matter before ship. The SDK facts used (`skills` filter, `system_prompt` file form, `fork_session`, `toggle_mcp_server`) were read from claude-agent-sdk 0.2.166 as installed.
- **Adversary lens (two compliant units that still clash).** (a) The plugin loader and the Surface both deciding skill visibility: closed, the Surface computes the `skills` filter and the loader only materialises views. (b) Attached references kept in two places: closed, the chat record owns them and the session recorder alone mirrors them. (c) Two engine instances advancing one event cursor: closed, a trigger has one home (AD-10). (d) A stored and a derived mark disagreeing: closed, only `quarantined` is stored. (e) A standing grant lifting publish or enable: closed, never grantable and refused in the service (AD-11). (f) Banks and scopes as two partitions of memory: closed, scopes are Library ref namespaces with one writer, banks are Hindsight's index partitions by writer, mapped one way. (g) `pod-block` asking in the Lab but not in the Library: closed, both now say MANAGE for its merge into `main`. (h) Copilot records landing on `main` through a writer that does not own `main`: closed, the session recorder is `engine:<store>`, which AD-7 already lets fast-forward under AD-18.
- **Not done:** no probe ran (all are build-time gates); the companions named in §9 were not re-projected.
