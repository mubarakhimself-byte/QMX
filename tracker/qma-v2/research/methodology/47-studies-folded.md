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

---

## Review 48 applied (2026-10-18, the one fix round)

Written by the architect (Opus 5.5), headless, BMad architecture skill in amend mode. No sub-agents, nothing committed. Input: `48-review-unlocked-and-folded.md` (0 critical, 8 high, 15 medium, 10 low). Where a finding rests on the SDK, the code truth was checked again: `claude-agent-sdk` 0.2.166 with its bundled CLI 2.1.299 in `D:/QMX-worktrees/eng-ep12/qmx-agents/.venv`, and `origin/engine/base` 132169c7 (`qma/harness/chat.py`, `launch.py`, `qmx_remote/*`).

**Counts.** All 8 highs, all 15 mediums and all 10 lows were applied. No medium was rejected. One part was logged instead of designed: M10's question about ruling 116 goes to him as W3. `lint_spine.py` gives 0 findings on all three spines.

**Verified while fixing, beyond the review:**

- **`list_changed` cannot reach the CLI through the SDK today.** The pinned SDK's MCP bridge drops server notifications, `list_changed` included (`_internal/sdk_mcp_bridge.py` docstring). The CLI does advertise `sdk_mcp_tools_list_changed`. So H6 uses `reconnect_mcp_server("qmx")` until the SDK forwards the notification, and P-PK decides between the two.
- **`exclude_dynamic_sections` moves, not drops.** The stripped sections go into the first user message (`types.py:46-56`), so the working folder still reaches the model.
- **The bundled CLI knows every name the fixes use.** It contains the strings `excludeDynamicSections`, `systemPromptSnapshot`, `autoMemoryEnabled`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY`, `CronCreate`, `CronDelete`, `CronList`, `ScheduleWakeup`, `RemoteTrigger`, `EnterWorktree` and `ExitWorktree`.
- **The built `qmx` server is already one server per chat** (`launch.py:468`), so H6 extends what exists. The `_keep_off` loop guards vetted external servers, not in-process ones.
- **`qmx_remote/code.py` stays.** It is the isolated checkout with one push refspec that `worker.py` calls, and remote build attempts keep using it.

### Finding to outcome

| Finding | Outcome | Where |
| --- | --- | --- |
| H1 per-attempt folders break the cache | Applied. Every chat sets `exclude_dynamic_sections: true`. AD-18's stale workspace sentence is replaced. The CLI's auto memory is off for Background and Child chats. | AD-62, AD-18; H53, H54; P-SET cache case |
| H2 recorded prompt after resume | Applied. Every chat sets `snapshot: false`. The spine says what reaches the model after a resume. The digest is computed per launch over what that launch passed. | AD-62, AD-35; H53; P-SYS resume case |
| H3 declared Bash writes anywhere | Applied without a sandbox (rulings 115-117). File tools are confined by path. A declared shell writes the way Claude Code's does, within the guard's floor. What a run keeps is its declared outputs, and he is told so plainly. | AD-60, AD-24; E55, P-PERM; PLAIN-WORDS; UI-HANDOFF §14.2 |
| H4 server runs invisible on the PC | Applied. The PC service forwards reads and inbox answers to the node with a host pass. It holds one event stream per reachable node and merges lists by `home_engine`. When a node is down its rows show "server unreachable since". Nothing replicates. | AD-3, AD-21, AD-65; §29.2; E68; UI-HANDOFF §16.1 |
| H5 server chains stall when the PC sleeps | Applied (the review's second option). The flip to `primary = server` happens at the Contabo setup, unconditionally. P-LAT now measures latency and no longer gates the flip. | Library AD-19, AD-14; engine AD-64; E63 extended |
| H6 toggle unreliable | Applied. Each chat has one `qmx` server that lists the Surface. A scope change re-lists it, by `list_changed` once the SDK forwards it and by `reconnect_mcp_server` until then. Nothing is switched off with `toggle_mcp_server`. Per-toolset servers return only if P-PK fails. | AD-61, AD-35, AD-55, AD-19; H47 rewritten, H32 superseded; P-PK restored, P-TG extended as the fallback |
| H7 RUN1 deletes remote compute early | Applied. No remote code is deleted until the remote `WorkerPort` adapter passes E57 on a real placement. `code.py` is kept. | AD-57; program below |
| H8 skills, agents and commands mid-chat | Applied. A chat loads only its pack set's plugins. Tools join at once. Skills, agents, commands and pack text join at the next turn, when the chat relaunches by resume. Two UI rows now say "tools now, skills on your next message". | AD-35, AD-55, Lab AD-14; H55; P-PL extended; UI-HANDOFF §14.5, §15.1 |
| M1 resume across machines | Applied, because ruling 117 lists it. The ledger is mirrored to the Hub at each node end, and `runs.adopt` takes a Hub claim with fencing. Zone files do not travel, so nodes that wrote `work/` run again. | AD-7, Deferred row; E69 |
| M2 E55 resume contradicts overlay deletion | Applied. After a crash, the retry is a new attempt with a fresh chat and a fresh overlay. | AD-51; E55; S7 |
| M3 steer a live run with an edit | Applied. A live fork may name a newer published version and reuse memos under the replay rule. | AD-7; UI-HANDOFF §16.4 |
| M4 claims in two channels | Applied. Claims live on the Hub store, which is the primary once the server exists. | Library AD-24, AD-7 |
| M5 pause flag direction | Applied. The Hub holds the authoritative flag and sends it back in its heartbeat reply. A host that loses the Hub shows "pause state unknown". | AD-10, AD-65; §28.5 |
| M6 memory rows outside the walk | Applied. A memory row gets its `derived-from` relations when it is written, and memory rows are in the P-TAINT fixture. | AD-18, Library AD-3 |
| M7 battery on haiku | Applied. The battery runs on the model under change and compares it with the current model. | AD-66 |
| M8 `complete` untested by default | Applied. Unit tests use a recorded transport. A provider-proof lane gates any packet that touches `complete`. | AD-56 |
| M9 CLI scheduling tools | Applied. Every chat loses `CronCreate`, `CronDelete`, `CronList`, `ScheduleWakeup`, `RemoteTrigger` and `Workflow`, and the skills `schedule` and `loop`. Background and Child chats also lose the worktree tools. | AD-62; H56; E60 |
| M10 money name check | Applied as hygiene: the vendored word list now covers operation names and external tool lists. His reading of ruling 116 is asked as W3. | AD-54; H58; E61; OPEN-DECISIONS W3 |
| M11 probes without pass lines | Applied. P-MEM, P-LAT, P-TAINT, P-SRCH, P-EV and P-OPS each have a number and a fail branch. Contabo's overhead now counts Hindsight, which leaves 2 sessions with it and 4 without. | §28.8; AD-30, AD-25 |
| M12 probes after their work | Applied in the program below. | — |
| M13 `@folder` copies files | Applied. A file or folder is pinned by a manifest, and bytes are stored only for files the model reads. | AD-63 |
| M14 delete floor too blunt | Applied. The floor now covers only what lies outside the chat's folder or worktree. In an Interactive chat it asks instead of refusing. | AD-54; H57 |
| M15 agent tools have nowhere to load | Applied. An unreviewed tool loads only into the run that made it, and anywhere after his review. | AD-4, Library AD-3 |
| L1 incomplete caller list | Applied in AD-59, including the two QML tests that would pass without checking anything. 43 §2 row 23 is left as written; this row corrects it. | AD-59 |
| L2 DELETION-PLAN D2 target | Applied: D2 now names `qmx_host`. | DELETION-PLAN D2 |
| L3 old SOLUTION-DESIGN rows | Applied: marked superseded in place (the §11 remote worker, the §8 adapter list, S7). | SOLUTION-DESIGN |
| L4 Lab server count | Applied: the Lab brings two toolsets, `lab` and `pods`, on the one server. | Lab AD-14; DOC-CHANGES 52 |
| L5 example apps | Applied: they migrate in the mini-app packet. | AD-57 |
| L6 `pending` owner | Applied: `pending` is resolved when read. | AD-63 |
| L7 `library-skills` hash | Applied: the hash covers a manifest of member ids. | AD-55 |
| L8 skills on the command line | Applied: P-SET gains a case with 150 skills. | P-SET |
| L9 draining Contabo | Applied: `qmx node update` drains the node first. | AD-30 |
| L10 P-SYS repeats a probe | Applied: P-SYS keeps only its size, cache and resume cases. | AD-62; §28.8 |

### Probe changes

- **Restored:** P-PK, the first option for H47. It checks that a list change reaches the CLI, by `list_changed` or by reconnect, and runs before CAT.
- **Demoted:** P-TG becomes the fallback. It now also checks:
  - a switch-off sent while the server is still connecting;
  - whether a switch-off persists across two chats in one workspace, and across a resume;
  - a launch with 40 servers.
- **Extended:**
  - P-SET: cache reads across two folders, and a filter of 150 skills.
  - P-SYS: trimmed to size and cache, plus a resume case with `snapshot: false`.
  - P-PERM: a declared Bash writing outside the overlay.
  - P-PL: a pack joining mid-session by resume, and agents limited to the pack set.
- **Pass lines added:** P-MEM, P-LAT (which no longer gates the flip), P-TAINT (memory rows now in the fixture), P-SRCH, P-EV and P-OPS.
- **Live checks:**
  - New: E68 (a server run's 401 is seen and retried from the PC) and E69 (a run adopted on another machine).
  - Rewritten: E55.
  - Extended: E60 (no CLI scheduling tools), E61 (order-shaped names, wire names on the one server) and E63 (the chain runs with the PC asleep).

### Program effects (against `HARDENING-PLAN.md`, 43 §10 and §7 above; the plan itself is not edited)

| Packet | Effect | After |
| --- | --- | --- |
| HG3 (turn API) | **Widen:** add H53 (`exclude_dynamic_sections`, `snapshot: false`) and H54 (auto memory off for Background and Child). Both must land before AGW makes overlays the working folder. | P-SET with the cache case, P-PERM with the declared-Bash case |
| AGW | **Re-gate:** after HG3's H53. E55 is rewritten for the honest Bash boundary and for retries in a new attempt. | HG3, SEC2A |
| HRMH (guard) | **Widen:** add H57 (the delete floor scoped to the chat folder, with an Interactive ask) and the external-server half of H58. | — |
| CAT | **Changed:** one `qmx` server per chat, re-listed on a scope change, replaces a server per toolset (H47 rewritten). The gate is **P-PK first**, and P-TG runs only if P-PK fails. | HRMH, HG3; P-NM, P-PK |
| PACK | **Changed:** a chat loads only its pack set's plugins, and a pack change relaunches it by resume at the next turn (H55). | CAT; P-PL extended |
| SURF | **Widen:** the digest is computed per launch over what was passed; add H56 (CLI scheduling tools and skills denied) and the P-SYS resume case. | CAT, HG3; P-SYS |
| RUN1 | **Split.** **RUN1a:** the one run list, app schedules as triggers, and `RunIndex` dropping chat journals; nothing remote is deleted. **RUN1b:** deletes the control `runs_*` and `jobs_*` operations and `qmx_remote`'s `worker.py`, `runs.py` and `store.py`. | RUN1a after L1. RUN1b after **REM** passes E57 on a real placement |
| New **REM** | The remote `WorkerPort` adapter with the sidecar, the Hub client and run passes, keeping `code.py` (AD-25, AD-57, Library AD-11 to AD-13). This turns Appendix G's row "Contabo node, vault and run passes" into a packet. | the RTR packets (passes) and LIB4 (the Hub); his Contabo setup |
| DEL1-DEL3 | Now after RUN1a; otherwise unchanged. DEL3 also handles L1's extra callers and the two QML tests. | the guard, RUN1a, L1 |
| DEL4 (LangChain) | **Re-sequenced** after RUN1b, because `qmx_remote/worker.py` is the LangGraph loop. | RUN1b |
| OPS | **Widen:** forwarding for remote homes and the event stream (H4, E68), the pause flag in the Hub's heartbeat reply (M5), and draining the node before an update (L9). | L1, RUN1a; **P-OPS first** (M12); the sync part after LIB4 |
| New **ADOPT** | Journal mirroring at each node end, and `runs.adopt` (M1, E69). | OPS, LIB4 |
| TRG2 | The `event` part now waits on **P-EV** (M12), which has a pass line. | LIB1; P-EV |
| LIB4 | **Changed:** the primary flip happens at the Contabo setup, unconditionally; claims live on the Hub; P-LAT measures but no longer gates. | the Hub; P-LAT |
| LIB2 | The P-TAINT fixture includes memory rows (M6). | P-TAINT |
| MEM | Memory rows are written with `derived-from`; P-MEM has pass and fail lines; Contabo's overhead includes Hindsight. | LIB1; P-MEM |
| EVAL | Runs on the model under change and compares it with the current one (M7). | SURF |
| FORK | Adds the live fork onto a newer published version (M3). | BUG3, REPLAY |
| RTR4 or the `complete` packet | Unit tests use a recorded transport, and a provider-proof lane gates the merge (M8). | — |
| REF1, REF2 | REF1 resolves `pending` when read (L6). REF2 pins files and folders by manifest (M13). | as before |
| APP2 | Adds the `qmx app check` half of H58 (order-shaped names, M10), the example-app migration (L5) and the one-server wire names. | PACK, CAT, LIB1; P-APP, P-EV |
| Dropped | Nothing. The design with a server per toolset survives only as P-TG's fallback. | — |

### Reviewer gate (inline; sub-agents were not allowed)

- **Lint.** `lint_spine.py` gives 0 findings on the engine, Library and Lab spines.
- **Rubric.** No AD id changed. Each amended Rule still names what it binds and what it prevents. Every new mechanism reuses one that exists:
  - one server per chat, as built;
  - the SDK's prompt options;
  - forwarding over the host pass and the tailnet, as already designed;
  - Hub claims and object replication for `runs.adopt`.
- **Adversary (two compliant units that still clash):**
  - (a) The Surface and the plugin loader disagree on what a chat sees. Closed: one rule in AD-35, cited by AD-55 and Lab AD-14.
  - (b) The PC and the node both fold an inbox answer. Closed: the PC forwards the answer, and only the run's home folds it.
  - (c) The old and the new home both resume an adopted run. Closed: the adopter takes a Hub claim on `adopt:<run_id>`, and the old home checks the Hub before any resume.
  - (d) The digest records slots that never reached the model. Closed: it is recorded per launch, over what was passed.
  - (e) Claims split across two stores while the PC sleeps. Closed: all claims live on the Hub.
- **Not done:**
  - No probe ran; all of them are build-time gates.
  - The Library and Lab HLD and LLD companions were not re-projected (DOC-CHANGES 51, 52).
  - `HARDENING-PLAN.md` and `PROMPT-HARDENING.md` were not touched.
