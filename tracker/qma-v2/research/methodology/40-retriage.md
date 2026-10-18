# 40. Re-triage of the engine run's BACKLOG and lows against the amended design (2026-10-18 evening)

Written by an Opus 5.5 agent for the planning lead. No sub-agents, no skills, nothing committed. Input for the next plan only (operator rule: no unplanned work).

**Inputs read:** `39-architecture-rerun.md` (in full); the amended engine spine (AD-1 to AD-49, Conventions, Deferred), `SOLUTION-DESIGN.md` §25 and §26, `HARNESS-REQUESTS.md` (HG3, HG4), engine `OPEN-DECISIONS.md`; `34-engine-run-triage.md`; every line of `qma-ship/engine/BACKLOG.md` (98 lines) and `lows.md` (94 lines); `26` rulings 1-104; alignment `A`, `B`, `C` sections 2 and 3. Code truth: `origin/engine/base` = `132169c7`, read with `git show` and `git grep`.

**Id scheme (same as 34):** B-n is line n of `BACKLOG.md`, L-n is line n of `lows.md`, AL-n is an alignment mismatch that implies code and has no B or L row of its own. Lines B-5 to B-95 and L-3 to L-90 match 34's snapshot. Changes since 34: B-96 (test costs) was removed from BACKLOG (L-91 says the costs are now in TEMPLATES.md); **B-98 is new** (Fable in the strong ladder, a duplicate of L-23); **L-91 to L-94 are new** (TP4).

Path shorthands: `E/` = `qmx-agents/packages/qmx-engine/src/qmx_engine/`, `H/` = `qmx-agents/packages/qma-harness/src/qma/harness/`, `T/` = `E/templates/`, `S/` = engine lane and probe scripts (`scripts/live/engine/`, `scripts/probes/engine/`).

---

## 1. Summary counts

206 rows: 92 BACKLOG items, 92 lows, 22 alignment rows. 17 rows are duplicates folded into another row, which leaves **189 distinct issues**.

| Outcome | BACKLOG | lows | alignment | Total rows |
| --- | --- | --- | --- | --- |
| RESOLVED-BY-DESIGN | 55 | 19 | 21 | **95** (91 still need code, 4 need none: B-12, B-14, B-15, L-42) |
| CODE-FIX (bug or hygiene the design does not need to speak to) | 19 | 46 | 0 | **65** |
| NEW-PACKET (planned work with no spine rule of its own, only a §25 sketch) | 2 | 0 | 0 | **2** (B-40, B-47) |
| OBSOLETE | 8 | 13 | 0 | **21** |
| STILL-OPEN | 4 | 1 | 1 | **6** |
| Duplicate (folded) | 4 | 13 | 0 | **17** |

Every row that needs code names a packet in the table, so "RESOLVED-BY-DESIGN, code yes" rows are also packet work. **Code still needed: 158 distinct issues** (91 + 65 + 2).

**Verified against code at `132169c7`** (this changes 34's picture):
- Fixed already, so OBSOLETE: B-45 / L-53 (`service/versions.py:22-26` `operator_only` refuses non-`user` publish and enable), B-58 and B-59 (`control_door.py:258-264` starts `Scheduler.serve` with `configured_refs` and `shipped_skills`), L-71 (fixed in the EP13 round; the rule is now in the spine's Conventions "Test homes").
- Still open in code: B-75 (`qma-core/tests/test_extensibility.py:136` pins the member set; `qmx-agents/pyproject.toml:17` has `packages/qmx-engine`, so `just ci` is still red), B-44 (`E/__main__.py:56` `--mode` offers `live`), B-98 (`E/settings.py:22` `_STRONG` names `claude/fable`), B-95 (`E/settings.py:70-71`), every cap (`H/launch.py:229-232`, `:518-519`; `H/harness.py:378`, `:624`; `E/settings.py:36-52`; `E/admission.py:43`), L-51 (`E/service/runs.py:208-212` reads any non-draft ref as published), L-52 (`E/service/explain.py` holds no redact call), B-69 (`E/nodes/agent.py:239` sends `RESUMED`), B-91 (`E/templates/install.py:139`), trigger kinds (`E/ledger/migrations.py:35`), no `py.typed` in `qma-harness`.

**Critical and high (distinct):** critical B-30, B-89. High: B-17, B-31, B-39 (with L-58), B-44, B-51, B-63, B-69, B-75, B-95, B-98, AL-1 and AL-2 (the caps; settled operator rule, and they break his fan-out case).

---

## 2. The full table

Outcome codes: **R** RESOLVED-BY-DESIGN, **C** CODE-FIX, **N** NEW-PACKET, **O** OBSOLETE, **S** STILL-OPEN, **D** duplicate (folded into the named row). Severity is 34's, adjusted where the amended design changed the stakes. Packet codes are defined in §3.

### 2.1 BACKLOG.md

| Id | Item | Sev | Out | Design (AD) | Code? | Packet | File(s) | Depends on / notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B-5 | Draft save and test run still ask once in default mode | med | S | AD-22; H20 deferred (36 S8) | — | HG3 (deferred) | — | fallback: first-run card offers the allow rule (UI); his call D |
| B-6 | `compact_at` and hooks lost when a Background chat reloads after restart | med | R | AD-34; H19 | yes | HG3 | `H/harness.py:230,355`, `H/home.py` | decision D; folds L-7 |
| B-7 | Refusal text points at `POST /api/usage/meter` | low | O | AD-40 (BackgroundCap goes) | removed | CAP-H | `H/usage.py`, `H/harness.py:378` | if CAP-H slips, a one-line text fix; folds L-6 |
| B-8 | Meter turn leaves a "Plan usage meter" session row; chat listed for seconds | low | R | H18 close only, list filtered by kind; row kept as audit (AD-25) | yes | HG3 | `H/harness.py:671` meter, qmx-control chat list | folds L-18 |
| B-9 | `usage.py` docstrings stale; `project.py` METER pattern matches nothing on CLI 2.1.299 | low | C | — | yes | CAP-H | `H/usage.py`, `H/project.py` | same files as the cap removal |
| B-10 | `qma-harness` ships no `py.typed` | low | R | H22 | yes | HG3 | `qma-harness` package root | decision D |
| B-11 | No public way to build `ControlService` | med | R | AD-3; H23 dropped, Appendix G L1 seats the engine in `qma.serve` | yes | L1 | `qma.serve` composition, `E/host.py` | scripts keep the private import until L1 |
| B-12 | Spine layer diagram drew core → ledger/ports/nodes | low | R | AD-1, structural seed (35) | no | — | — | doc only |
| B-13 | Money lint uses the smaller `money_path` matcher | med | R | AD-36, AD-3 (descriptors import allowed) | yes | SEC-1 | `E/definition/lint.py`, `qma-core` `barriers/descriptors.py` (`name_money_act_called`) | decision F |
| B-14 | AD-4 port kinds not typed | low | R | AD-4 (v1 ports carry data; kinds by a later `typeVersion`) | no | — | — | |
| B-15 | `rule` and `loop` port names invented | low | R | AD-4 ratified the built names | no | — | — | |
| B-16 | Lint requires `agent.max_turns`; default split | med | R | AD-4, AD-40 (no default; lint refuses only < 1) | yes | CAP-E | `E/definition/lint.py`, `E/settings.py:36-37` | |
| B-17 | A node's `credentials` may name a broker ref | high | R | AD-36 credential refs (`qmx/tool/*` only, fail-closed broker set) | yes | SEC-1 | `E/definition/lint.py`, qmx-control Settings validator | |
| B-18 | Node events lack node id, iteration, partition; no event sets span `gate`/`cancelled` | med | R | AD-15 event keys | yes | BUG-2 | `E/ledger/store.py`, `E/ledger/spans.py`, `E/core/simulate.py` | folds L-29, L-34 work |
| B-19 | Memo validity read from events, not `ledger.memo.valid`; `invalidate_by_definition` has no reader | low | C | AD-7 is silent on which is the truth (§5 item 4) | yes | BUG-2 | `E/ledger/memo.py`, `E/core/fold.py` | folds L-35; pick events, drop the unread flag |
| B-20 | Nested fan-out, loop over fanned input, loop in loop body park at run time | med | R | AD-5 (refuse at validation `nesting_unsupported` until the packet) | yes | BUG-2, then NFO | `E/definition/validate.py`, `E/core/` | refusal now, packet later |
| B-21 | Chunk window from the `context_window` setting; tokens = JSON bytes / 4 | low | R | AD-34, AD-39 (window from the registry) | yes | ROUTER | `E/core/partitions.py`, `E/settings.py:56` | estimator rule unbound (§5 item 11) |
| B-22 | `validate` skips loop, join, wait parameters and the one-`one`-edge join rule | med | C | — | yes | BUG-2 | `E/definition/validate.py` | |
| B-23 | Late partition failure leaves no line; `no_progress_rounds` has no direction; join timeout uses reason `wait` | low | R | AD-16 | yes | BUG-2 | `E/core/joins.py`, `E/nodes/join.py`, `E/nodes/loop.py` | |
| B-24 | Loop-body node runs on an outside value alone | med | R | AD-5 readiness (outside edge is context) | yes | BUG-2 | `E/core/ready.py` | with B-87 |
| B-25 | Ledger accepts a second `run_created` | med | C | — | yes | BUG-1 | `E/ledger/store.py`, `E/core/fold.py` (keep the first) | folds L-36 |
| B-26 | Script `idle_seconds` not enforced; big stdout kept inline; declared credentials refused | med | R | AD-24 run context, AD-36 allow-list, AD-16 script idle, AD-34 spill | yes | SEC-2 | `E/nodes/script.py:167` | after SEC-1 |
| B-27 | Subworkflow child folder, `caller_policy` at dispatch only, waiting child fails parent | med | R | AD-5 subworkflows | yes | BUG-2 | `E/nodes/subworkflow.py`, `E/definition/validate.py` | with B-76 |
| B-28 | Nothing folds a gate answer; irreversible step with unknown outcome waits forever; pinData ignored | med | R | AD-17 answers fold; SD §25 | yes | GATE (+PIN) | `E/core/fold.py`, `E/ports/inbox.py`, `E/service/inbox.py` | after BUG-1 |
| B-29 | Reversible retry undoes files another attempt wrote into the same zone | med | S | not bound (§5 item 2) | — | — | `E/workers/effects.py` | design must choose per-attempt zones or attribution |
| B-30 | Host script reaches the plan login and `qmx/*` keyring | **crit** | R | AD-24 (zones, provenance tier, AppContainer, container) | yes | SEC-2 | `E/nodes/script.py`, `E/workers/local.py`, new confine module, script runtime | decision E; probe E33 first |
| B-31 | Script outlives an engine crash | high | R | AD-24 lifetime (Job object, `--rm --init`, sweep) | yes | SEC-2 | `E/workers/local.py` | |
| B-32 | `InboxPort.resolve` records but nothing folds | med | R | AD-17 | yes | GATE | `E/service/inbox.py`, `E/core/fold.py` | |
| B-33 | Raise the runaway guard and resume | med→low | O | AD-40 (no guard) | removed | CAP-E | `E/core/ladder.py` | "resume a pause at his own limit" lives in GATE |
| B-34 | Doctor `bad_input` rerun; `logic` writes a challenger | low | R | AD-16, AD-26 | yes | LATER (self-improvement) | `E/nodes/doctor.py` | |
| B-35 | Failed partition read only by joins does not walk the ladder | med | R | AD-16 (partition walks alone) | yes | CHUNK | `E/core/joins.py`, `E/core/ladder.py` | after BUG-1 |
| B-36 | Degrade does not know the cheapest candidate | low | O | AD-40 (degrade gone) | removed | CAP-E | `E/core/ladder.py` | |
| B-37 | Reversible attempt cancelled by `LocalWorker.cancel` is retried | low | R | AD-15 (`cancelled` from `run_cancelled`) | yes | BUG-1 | `E/workers/local.py`, `E/core/ladder.py` | |
| B-38 | Guard defaults disagree (SD 17 vs settings.py) | med | O | AD-40 | removed | CAP-E | `E/settings.py:38-42` | folds L-49; see AL-2 |
| B-39 | Provider failure messages reach ledger and inbox unredacted | high | R | AD-37 write seams | yes | SEC-1 | `E/ledger/store.py`, `E/ledger/inbox_table.py` | folds L-50; with L-58 |
| B-40 | `interrupted` derived only from a drive's outcome | low | N | SD §25 ledger-derived run state | yes | LDR | `E/service/runs.py`, `E/control_door.py` | cancel/resume landed in EP13 |
| B-41 | Subworkflow child run not exported to the Library | med | R | AD-14; Library L11 | yes | LIB | `E/trace_export.py`, Library adapter | |
| B-42 | Settings read once at service open | med | R | Conventions "Config" (read at use, snapshot on `run_created`) | yes | BUG-1 | `E/service/api.py`, `E/runner.py` | |
| B-43 | Variant draft loses `variant_of`; fake Library does not enforce `refs/drafts` ownership | low | C | ownership: Library AD-7 | yes | BUG-2 (+LIB) | `E/service/drafts.py`, `E/ports/library_fake.py` | ownership waits for the real Library |
| B-44 | `--mode live` CLI runs any folder live | high | R | AD-11 (CLI test-only) | yes | P0 | `E/__main__.py:56` | verified still present |
| B-45 | Agent or workflow caller may publish and enable | med | O | AD-11 | no (fixed) | — | `E/service/versions.py:22-26,46,82` | folds L-53 |
| B-46 | Grader `llm` mode unbuilt | med | R | AD-5 (refuse at validation until the packet) | yes | BUG-2, then GRADE | `E/definition/registry.py`, `E/nodes/grader.py` | folds B-81 |
| B-47 | pinData in test mode unbuilt for every kind | med | N | SD §25 pinData; AD-11 hash | yes | PIN | `E/runner.py`, `E/nodes/base.py` | needs L-26 hash change (BUG-2) first |
| B-48 | Default `gpt` role rows name no model | low | R | AD-13, AD-39 (defaults generated from configured providers by class) | yes | ROUTER | `E/settings.py:21-22`, `E/roles.py` | folds L-19 |
| B-49 | Guard counts cache reads | med | O | AD-40 | removed | CAP-E | `E/core/ladder.py` | |
| B-50 | No public close for a chat | med | R | H18 | yes | HG3 | `H/harness.py` | decision D |
| B-51 | `NewChat` has no tools option | high | R | AD-24, H2 (SDK `tools` list) | yes | HG3 (H2 first) | `H/launch.py`, `H/harness.py`; engine side `E/nodes/llm.py`, `E/nodes/agent.py` | folds B-70; E35 |
| B-52 | Agent prompts carry no frozen memory snapshot | med | R | AD-18 | yes | MEM | `E/memory/`, `E/prompts.py` | |
| B-53 | Node brief not cached across chunks | med | S | H21 deferred with a size cap (36 S8) | — | HG3 (deferred) | — | cost accepted: each chunk pays its brief |
| B-54 | Limit timer holds `Engine.start` for hours | med | R | AD-10 (only the ticker resumes; caller returns `waiting`) | yes | BUG-1 | `E/runner.py` | verify after EP13's scheduler |
| B-55 | Watchdog counts the worker's own heartbeat | med | R | AD-16 (heartbeat never counts) | yes | CAP-E | `E/watchdog.py` | folds L-44; **collides with L-60** (§5 item 1) |
| B-56 | Engine records session id, not home | med | R | AD-35 (engine writes `session_homes` after `start_chat`) | yes | L1 | `E/nodes/agent.py`, qmx-control `session_homes` | needs the control write path L1 gives |
| B-57 | `after_unknown` retries a model node that declares an irreversible effect | med | R | AD-8 (partly; §5 item 5) | yes | BUG-1 | `E/workers/effects.py:57` | must land before agent writes (L6) |
| B-58 | Nothing ran `Scheduler.serve` | low | O | AD-10 | no (fixed) | — | `E/control_door.py:258-264` | |
| B-59 | Scheduler got no preflight inventory | low | O | AD-10 | no (fixed) | — | `E/control_door.py:57,259` | |
| B-60 | Trigger `role_pins`/`effort_pin` unread; `after` fires only on scheduler runs | med | R | AD-10 | yes | BUG-1 | `E/triggers/rows.py:10`, `E/triggers/ticker.py`, `E/runner.py` | |
| B-61 | Test run resumed by a wake writes no fresh report | med | C | AD-11 test-report | yes | BUG-2 | `E/service/tests.py`, `E/runner.py` | |
| B-62 | Fire endings written one by one (1.9 s for 500) | low | C | — | yes | HYG | `E/triggers/ticker.py` | perf only |
| B-63 | Time `wait` never resumes on its own | high | R | AD-10 wakes | yes | BUG-1 | `E/nodes/wait.py`, `E/core/waits.py`, `E/triggers/ticker.py` | with L-37, B-73 |
| B-64 | Engine host serves no chat routes | med | R | AD-3 via L1 (H25 dropped) | yes | L1 | `E/host.py`, `qma.serve` | |
| B-65 | qmx-control cannot tell REST from a tool call | med | R | H24 (labelling only) | yes | HG3 | qmx-control `server.py` | fallback: publish/enable/live start only on engine REST |
| B-66 | Cancel does not reach subworkflow children | med | R | AD-5 (cancelling the parent cancels children) | yes | BUG-1 | `E/nodes/subworkflow.py`, `E/service/runs.py` | |
| B-67 | `GET /api/runs` lists chat journals as agent runs | low | C | — | yes | HG3 (bug fix) | qmx-control runs route | |
| B-68 | Disable leaves the version enabled | med | R | AD-10 enablement derived | yes | BUG-2 | `E/service/versions.py`, `E/control_door.py` | |
| B-69 | Agent chunk killed before its task arrives resumes with `RESUMED` only | high | C | AD-34 re-seed covers compaction only (§5 item 10) | yes | BUG-1 | `E/nodes/agent.py:65,239` | resend the full prompt when the transcript holds no task |
| B-70 | `tools: []` stated in the brief only | high | D | → B-51 | | | | |
| B-71 | `explain` text lists no spans | low | C | — | yes | BUG-2 | `E/service/explain.py` | same file as L-52 (SEC-1) |
| B-72 | `run-now` on a parked trigger silently starts nothing | med | C | AD-10 `explain_trigger` gives the reason surface | yes | BUG-1 | `E/triggers/ticker.py`, `E/service/` | |
| B-73 | Resumed `wait` run reads `running` | med | R | AD-10 ("a held run reads `waiting`"); SD §25 LDR | yes | BUG-1, LDR | `E/service/runs.py` `status_of` | with B-63 |
| B-74 | `x10_llm doctor` lane cannot pass on Kimi | low | C | Conventions (tests on haiku) | yes | HYG | `S/x10_llm.py` | deterministic fake recording; with L-79 |
| B-75 | qma-core test red since EP2 | high | C | — | yes | P0 | `qmx-agents/packages/qma-core/tests/test_extensibility.py:136` | verified red; folds B-94 |
| B-76 | Bundle drops a subworkflow's child folder | med | R | AD-5, AD-14 (block folders in bundle; Library L18) | yes | BUG-2 (+LIB) | `E/definition/folder.py`, `E/ports/library_fake.py` | then TPL drops `SHARED_COPIES` |
| B-77 | Fake switch answers `llm` only | med | C | AD-11 (fake is an explicit switch) | yes | BUG-2 | `E/nodes/fake_provider.py`, `E/runner.py` | with B-85 |
| B-78 | Script cannot tell test from live | med | R | AD-24 run context (`QMX_MODE`, `QMX_FAKE`) | yes | SEC-2 | `E/nodes/script.py` | unblocks L-86 |
| B-79 | Template `needs` live twice | low | C | — | yes | TPL | `T/catalog.py`, template tests | |
| B-80 | Script env has no run id or home; `week.py` reads cwd | med | R | AD-24 (run context, never the home) + SD §25 `engine_view` | yes | SEC-2, then EVR | `E/nodes/script.py`; RV `week.py` | folds L-84 |
| B-81 | Grader judge refuses, RS4 cannot route | med | D | → B-46 | | | | |
| B-82 | No replay of a past run on an edited folder | med | R | AD-7 replay fork | yes | REPLAY | `E/service/runs.py`, `E/core/replay.py` | needs Library L20 (`replay-of`) |
| B-83 | Run artifacts typed only `run-file` | low | R | AD-14 (L19 optional type) | yes | LIB | `E/nodes/script.py`, `E/trace_export.py` | |
| B-84 | Number check accepts numbers from LLM intermediates (circular) | med | S | AD-45 "grade before display" names no evidence rule (§5 item 3) | — | TPL once decided | shared `render_and_grade` block | with L-81, L-87 |
| B-85 | Fake answers every chunk with the whole file | low | C | — | yes | BUG-2 | `E/nodes/fake_provider.py` | |
| B-86 | Card roles missing from `[roles]` defaults | low | R | AD-13 role table, generated defaults | yes | ROUTER (then TPL remaps) | `E/settings.py`, `E/roles.py` | |
| B-87 | Multi-branch node runs on any input | med | R | AD-5 `required` edges | yes | BUG-2 | `E/core/ready.py`, `E/definition/model.py` | |
| B-88 | Human points end as result cards | med | R | AD-17 (typed `proposal`, closed action enum); folds C M-10 | yes | TPL | pp, dm templates; `E/service/` | UI cards with the UI session |
| B-89 | Money lint skips script text, prompts, names | **crit** | R | AD-36 | yes | SEC-1 (scan) + SEC-2 (runtime refuses imports) | `E/definition/lint.py` → `definition/scan`, `E/nodes/script.py` | decision F; folds B-93, L-25 |
| B-90 | `validate` never runs `expr.check` | med | C | — | yes | BUG-2 | `E/definition/validate.py`, `E/definition/expr.py` | |
| B-91 | `install.py` "not yet built" is dead code | low | C | — | yes | TPL | `E/templates/install.py:139` | AD-46 renames touch the same file |
| B-92 | Draft view hides `needs_unmet` | med | C | — | yes | BUG-2 | `E/service/drafts.py` | |
| B-93 | (coordinator) money lint | crit | D | → B-89 | | | | |
| B-94 | (coordinator) `just ci` red | high | D | → B-75 | | | | |
| B-95 | Default test model is OpenRouter Kimi | high | R | AD-11, AD-13 (haiku through the plan) | yes | P0 | `E/settings.py:70-71` | |
| B-98 | Fable in the default strong ladder | high | R | AD-13, ruling 87 | yes | P0 | `E/settings.py:22` | folds L-23 |

### 2.2 lows.md

| Id | Item | Sev | Out | Design (AD) | Code? | Packet | File(s) | Depends on / notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L-3 | plan_harness log names the wrong reading source | low | C | — | yes | HYG | `S/common.py` | |
| L-4 | p_cache check cannot fail | low | O | finished EP0 probe evidence | no | — | — | FINDINGS already says so |
| L-5 | Seeding leaves a chat record in the ship home | low | C | Conventions "Test homes" | yes | HYG | `S/common.py` | |
| L-6 | Stale `/api/usage/meter` advice | low | D | → B-7 | | | | |
| L-7 | `compact_at`/hooks only in `_options` | med | D | → B-6 | | | | |
| L-8 | `Harness._options` never pruned | low | C | — | yes | HG3 (bug fix) | `H/harness.py:230,355,804` | |
| L-9 | `_observer` catches `Exception` only | low | C | — | yes | HG3 (bug fix) | `H/launch.py:324-331` | |
| L-10 | 40 % compaction not proven live | low | R | AD-34 (0.40 at ≥512k, 0.75 below) | yes | HG3 lane + ROUTER | `E/nodes/agent.py` | live proof in HG3's lanes; per-model point with the registry |
| L-11 | `p_runner_outside.py` writes without a log prefix | low | C | — | yes | HYG | `S/p_runner_outside.py:416` | |
| L-12 | Scratch-folder fallback isolates env, not files | low | O | AD-24, AD-25 supersede the fallback | no | — | — | FINDINGS wording only |
| L-13 | `raw_client.py` duplicates the lane lock | low | C | — | yes | HYG | `S/raw_client.py`, `S/common.py` | |
| L-14 | EP1 perf note disputes | low | O | finished evidence | no | — | — | |
| L-15 | Shutdown tracebacks in `p_model_ids.py` | low | C | — | yes | HYG | `S/p_model_ids.py` | |
| L-16 | `meter()` has no cooldown | med | C | AD-12 (plan meter feeds `least_used`) | yes | HG3 (bug fix) | `H/harness.py:671` | still needed: the meter survives the cap removal |
| L-17 | `meter()` cleanup order | low | C | — | yes | HG3 (bug fix) | `H/harness.py` meter | |
| L-18 | Meter session row | low | D | → B-8 | | | | |
| L-19 | `gpt` rows without a model | low | D | → B-48 | | | | |
| L-20 | AD-6 rule allows `monotonic`/`perf_counter` in core | low | R | AD-6 (no clock of any kind in core or definition) | yes | BUG-2 | engine import-rule test | |
| L-21 | Settings test reads `settings.py` as text | low | C | — | yes | CAP-E | engine settings test | rewritten anyway when CAP-E edits the defaults |
| L-22 | Import and AD-6 rules miss aliases, `importlib`, `uuid4`/`urandom`/`secrets` | med | C | AD-1, AD-6 | yes | BUG-2 | engine import-rule tests | |
| L-23 | Fable in the strong ladder | med | D | → B-98 | | | | |
| L-24 | `money_path` spelling gaps (`placeorder`, `set_leverage`, `flatten`) | med | R | AD-36 (one matcher; named misses accepted) | yes | SEC-1 | `E/definition/lint.py` | |
| L-25 | Lint reads type and parameters only | high | D | → B-89 | | | | |
| L-26 | pinData outside the content hash | low | R | AD-11 (hash covers `pinData`) | yes | BUG-2 | `E/definition/folder.py` | before PIN |
| L-27 | Racing writers refused with "an unknown pid" | low | C | — | yes | HYG | `E/ledger/store.py` | |
| L-28 | BaseException kills the writer thread | low | C | — | yes | BUG-1 | `E/ledger/store.py` | |
| L-29 | Ending event without keys closes no span | low | R | AD-15 (one `partition` spelling, keys on every node event) | yes | BUG-2 | `E/ledger/spans.py`, `E/ledger/store.py` | with B-18 |
| L-30 | Lane made the connection read-only, not the file | low | O | finished EP4 lane wording | no | — | — | |
| L-31 | `append()` non-dict gives AttributeError | low | C | — | yes | BUG-1 | `E/ledger/store.py` | |
| L-32 | Fold ignores `data.attempt` on endings | med | R | AD-15 attempt key | yes | BUG-1 | `E/core/fold.py` | |
| L-33 | `step()` does not catch executor errors | low | C | — | yes | BUG-1 | `E/nodes/base.py` | verify the runner owns it |
| L-34 | `node_scheduled` lacks the input hash | low | R | AD-15 | yes | BUG-2 | `E/core/simulate.py` | |
| L-35 | Memo: two sources of truth | low | D | → B-19 | | | | |
| L-36 | Last `run_created` wins in fold | med | D | → B-25 | | | | |
| L-37 | Wait times compared as text, naive local `now` | med | R | AD-10 (RFC 3339 UTC, compared as instants) | yes | BUG-1 | `E/nodes/wait.py`, `E/core/waits.py` | with B-63 |
| L-38 | Idempotency keys can collide on `:` | med | R | Conventions "Naming" (ids are lowercase kebab-case) | yes | BUG-1 | `E/definition/validate.py` (refuse non-kebab node ids) or `E/core/replay.py` | |
| L-39 | `restore()` lacks a containment check | low | R | AD-24 lifetime (restore only inside `work/`) | yes | SEC-2 | `E/workers/effects.py:100` | |
| L-40 | Junction in the zone kills the engine | med | R | AD-24 (`zone_link` fails the attempt) | yes | SEC-2 | `E/workers/effects.py:70` | |
| L-41 | x07 monitor lane prints non-JSON yet passes | low | C | — | yes | HYG | `S/x07_nodes.py` | |
| L-42 | `LocalWorker.run(job, executor, emit)` vs contract | low | R | AD-20 ratified `run(job, emit)` | no | — | — | |
| L-43 | `.snap` folders never pruned | low | C | retention unbound (§5 item 8) | yes | SEC-2 | `E/workers/effects.py` | same file as L-39, L-40 |
| L-44 | Watchdog keys on the worker heartbeat | med | D | → B-55 | | | | |
| L-45 | Guard checked only before rungs | low | O | AD-40 (guard gone; detector every tick) | removed | CAP-E | — | his own `limits` per-tick check unbound (§5 item 7) |
| L-46 | Degrade lets the whole batch through | low | O | AD-40 | removed | CAP-E | — | |
| L-47 | Inbox `tried` taken before the ladder walks | low | C | AD-17 ("what was tried") | yes | BUG-1 | `E/ledger/inbox_table.py`, `E/core/ladder.py` | |
| L-48 | Wall time counts sleep in waits | low | O | AD-40 (no default) | removed | CAP-E | — | for his own `wall_seconds` unbound (§5 item 7) |
| L-49 | Guard defaults | med | D | → B-38 | | | | |
| L-50 | Inbox copies messages unredacted | high | D | → B-39 | | | | |
| L-51 | `version_state` reads any non-draft ref as published | med | R | AD-11 ("published means reachable on `main`") | yes | SEC-1 | `E/service/runs.py:208-212` | verified open |
| L-52 | `explain` echoes failure messages verbatim | med | R | AD-37 (ledger seam + REST serializer) | yes | SEC-1 | `E/service/explain.py` | verified: no redact call |
| L-53 | `Caller("workflow")` may publish | med | D | → B-45 (fixed) | | | | |
| L-54 | Overlay draft reads tested, publish refuses | low | C | — | yes | BUG-2 | `E/service/versions.py`, `E/service/drafts.py` | |
| L-55 | `tests.run` rewrites the variant head even on failure | low | C | — | yes | BUG-2 | `E/service/tests.py:57` | |
| L-56 | Passed live run adds no `tested-by` | low | R | AD-11 (a passed run in either mode) | yes | BUG-2 | `E/trace_export.py`, `E/service/runs.py` | |
| L-57 | `HarnessAdapter.marks` never pruned | low | C | — | yes | BUG-1 | `E/ports/harness_adapter.py:109` | |
| L-58 | `redact` misses keys glued to a word | high | R | AD-37 shapes (high-specificity prefixes match anywhere) | yes | SEC-1 | `E/definition/lint.py:36,126` → `E/ledger` redact | |
| L-59 | x10/e21 overwrite owner homes | low | C | — | yes | HYG | `S/x10_llm.py`, `S/e21_*` | |
| L-60 | Warm-first gate holds chunks with no event | med | S | AD-16 no-progress + "heartbeat never counts" would stall every held chunk (§5 item 1) | — | CAP-E once decided | `E/nodes/agent.py:122-133` | must be settled with B-55 |
| L-61 | `limit_wait` admits a plan attempt over the share | low | O | AD-40, AD-9 (share gone) | removed | CAP-E | `E/admission.py` | |
| L-62 | EP11 lane overwrote the EP10 log | low | C | — | yes | HYG | `S/e21_real_tests.py` | |
| L-63 | Anti-spin guard waits on a stale past reset | med | C | AD-12 "provider `reset_at` wins" does not cover a past reset (§5 item 6) | yes | ROUTER | `E/runner.py` `Run.wake`, `E/admission.py` | pool owns readings |
| L-64 | Two Schedulers on one Engine double-drive | low | C | AD-3 (one instance per home), not bound per process (§5 item 9) | yes | BUG-1 | `E/triggers/claims.py` | |
| L-65 | Wake vs fire settle race | low | C | — | yes | BUG-1 | `E/triggers/ticker.py`, `E/triggers/claims.py` | |
| L-66 | `scheduler.heartbeat` dead; tick ≥ lease not warned | low | C | — | yes | CAP-E | `E/settings.py:28`, Settings validator | same file |
| L-67 | x12 loses its log prefix | low | C | — | yes | HYG | `S/x12_scheduler.py` | |
| L-68 | `workflow_runs_list` drops in-flight runs | med | R | SD §25 ledger-derived run state | yes | LDR | `E/control_door.py:316` | |
| L-69 | Cancelled fire holds its slot until the lease lapses | med | C | — | yes | BUG-1 | `E/triggers/ticker.py:227` | |
| L-70 | Host refusal is check-then-write | low | C | AD-48 supervisor implies one instance (§5 item 9) | yes | BUG-1 (or DESK) | `E/host.py:97,136`, `qma.serve` | `host.py` goes away at L1 |
| L-71 | x13 clients read his real control token | low | O | Conventions "Test homes" | no (fixed EP13) | — | — | |
| L-72 | `run_all` guard compares hash only | low | C | — | yes | HYG | `S/run_all.py` | |
| L-73 | `run_all` attributes evidence by mtime | low | C | — | yes | HYG | `S/run_all.py` | |
| L-74 | Lane 4 never kills in a chunk's first seconds | low | C | — | yes | HYG | EP14 lane 4 script | after B-69, to prove it |
| L-75 | `meta.needs` outside the hash | low | R | AD-11 (hash covers `meta.needs`) | yes | BUG-2 | `E/definition/folder.py` | with L-26 |
| L-76 | RS1, T3 carry unread `fixture_ref` parameters | low | C | — | yes | TPL | rs1, t3 definitions | |
| L-77 | T3 live never finds a surprise; README silent | low | C | — | yes | TPL | t3 README | |
| L-78 | `t_templates.py` loses its prefix | low | C | — | yes | HYG | `S/t_templates.py` | |
| L-79 | x10 schema and ask lanes depend on Kimi misbehaving | low | C | Conventions (haiku; fakes for failure paths) | yes | HYG | `S/x10_llm.py` | with B-74 |
| L-80 | `trace_export.run_files` reads unguarded | med | C | — | yes | BUG-1 | `E/trace_export.py` | |
| L-81 | RS4 counts LLM free text as evidence; `gaps` not in `x-prose` | med | C | see B-84 | yes | TPL | rs4 | after the B-84 rule |
| L-82 | RS0 writer launders numbers as assumptions | low | C | — | yes | TPL | rs0 | |
| L-83 | `citation_check` lets a claim cite itself | low | C | — | yes | TPL | TP1 `citation_check` block and its RS4 copy | |
| L-84 | `week.py` opens InboxTable, home from cwd | med | D | → B-80 | | | | |
| L-85 | No invented-number plant in TP2 tests | low | C | — | yes | TPL | template tests | |
| L-86 | DB `gather.py` fail-open on mode; `--fake` counts as live | med | R | AD-24 (`QMX_MODE`, `QMX_FAKE`), AD-11 (fake is always test) | yes | TPL | db `gather.py` | after SEC-2 (B-78) |
| L-87 | `render_and_grade` matches timestamps | low | C | see B-84 | yes | TPL | shared `render_and_grade` block | |
| L-88 | Blocks tell inputs apart by shape and order | low | C | — | yes | TPL | `links_check`, `lines_check`, assembles | |
| L-89 | Live start of a force-published draft omits the need line | low | C | — | yes | BUG-2 | `E/service/runs.py` | |
| L-90 | Mild test overlap | low | O | accepted | no | — | — | |
| L-91 | Stale TEMPLATES.md review image | low | O | evidence for a merged PR | no | — | — | |
| L-92 | Review gate files in the wrong folder; mp4 replays a log | low | O | evidence for a merged PR | no | — | — | |
| L-93 | `test_cost` strings read "0k in" | low | C | — | yes | TPL | `T/catalog.py`, `docs/TEMPLATES.md` | show cache tokens |
| L-94 | Builder's BACKLOG lines above the new heading | low | O | doc tidy; this file supersedes | no | — | — | |

### 2.3 Alignment mismatches that imply code (no B or L row of their own)

| Id | Item (sources) | Sev | Out | Design (AD) | Code? | Packet | File(s) | Depends on / notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AL-1 | Harness caps: `max_budget_usd` 5.0, `background_cap` 0.5, Background/Child `max_turns` 50, usage `needs_you`; `parse_budgets` cannot say "off" (A M-2, B 1, C M-2, C M-8, C M-9) | high | R | AD-40 (1); H28 | yes | CAP-H | `H/launch.py:221-261,518-519`, `H/harness.py:362-385,624`, `H/usage.py` | H28 follows the settled rule (OPEN-DECISIONS G) |
| AL-2 | Engine caps: `runaway.*`, `on_runaway`, `agent.max_turns`/`max_tool_calls`, `timeout.*.run`, `background_share` 0.5 (B 1, C M-9) | high | R | AD-40 (2), AD-16 | yes | CAP-E | `E/settings.py:36-52`, `E/admission.py:43`, `E/core/ladder.py`, `E/nodes/agent.py:193-255`, `E/watchdog.py`, all 31 template `runaway` blocks | folds B-38, B-49, L-45/46/48/49, L-61 |
| AL-3 | Pool default `fill-first`; copilot account not protected (B 2) | med | R | AD-12 (`least_used`, `background_priority: last`) | yes | CAP-E (default) + ROUTER (pool) | `E/settings.py:46`; new `H/pool.py` | |
| AL-4 | GPT capped at one account (B 3) | med | R | AD-12, AD-28; H33 | yes | ROUTER | `H/profiles.py`, GPT sign-in homes | |
| AL-5 | OpenCode excluded (B 4) | med | R | AD-38, AD-39; H12 chat lane | yes | ROUTER | `H/relay.py`, shaped like `qma/gpt/translate.py` | |
| AL-6 | Plan main with API sub-agents; split only for top-level chats; central proxy (C M-1, C M-20, C M-12; C chat 2, 3, 4) | high | R | AD-38, AD-29; H27, H10, H14 | yes | ROUTER | `H/relay.py`, `H/launch.py` (plan launch env), `H/harness.py` (grants) | probes P1, P2 first; kill switch `router.plan_lane` |
| AL-7 | Model registry: wire and capabilities per model, window-based chunks and compaction, defaults `key → gpt → plan` (C M-6, C M-15, C chat 1) | med | R | AD-39, AD-34, AD-13; H29 | yes | ROUTER | `H/profiles.py` → `profiles/*.toml`, `E/roles.py`, `E/core/partitions.py`, `E/nodes/agent.py` | probe P3; folds B-21, B-48, B-86 |
| AL-8 | One monitoring view for copilot and workflows (C M-16) | med | R | AD-15; H36 | yes | ROUTER (+UI) | router journal, `E/ledger/spans.py` | |
| AL-9 | MT5 and cTrader demo click-through (A M-1) | med | R | AD-33, AD-44 | yes | BRW | Cua manifest schema, driver account check | E46; money gate first |
| AL-10 | Copilot browser, watching, take-over, HUD (A M-6) | med | R | AD-44; H35 | yes | BRW | new browser pack, tool rows | ruling 30: journeys explained to him first |
| AL-11 | Mini-app load path; packs mid-session (A M-3, A M-15) | med | R | AD-19, AD-35; H32 | yes | HG4 | `qmx` MCP server listing, control session record | probe P-PK first |
| AL-12 | Output methodology: directives, previews (A M-5) | med | R | AD-45 | yes | DESK (with the UI session) | UI registry, renderer | screen content is methodology work later |
| AL-13 | `qmx app check`, app DevOps, `apps_archive` stub (A M-10) | med | R | AD-19 | yes | LATER (mini-app packet) | `qmx_control/service.py:1017` | |
| AL-14 | Template A intake without asking; plain names for all 31 (A M-4, B 5) | med | R | AD-46; SD §26.9 | yes | TPL | `T/catalog.py`, every template folder id, `a-fill-the-library/scripts/intake.py`, README | |
| AL-15 | 10 of 31 templates break under AD-24 and AD-36 (C M-5) | high | R | AD-24 manifest `tier`/`network`, AD-36 narrowed surfaces; E48 | yes | SEC-1 (t7, dm, ma) + SEC-2 (manifest, `capture.py` to container) + TPL (E48 gate) | listed templates | the security packets are done only when all 31 pass |
| AL-16 | Builder skill is a placeholder; skills lifecycle, curator, `/learn`; traces first (B 10, A M-11, A M-17) | high | R | AD-22, AD-46 | yes | TPL (builder) | `qmx_agents/skills/build-workflow/SKILL.md`, engine tool rows | E42 |
| AL-17 | Desktop app has no owner (B 9) | med | R | AD-48 | yes | DESK | new `qmx-desktop` | shell framework by probe |
| AL-18 | Multimodal input, `doc_read`, alphaXiv (A M-14, C M-14) | med | R | AD-42, AD-36 (`qmx/tool/alphaxiv`); H30 | yes | MM | harness turn routes, composer | E44 |
| AL-19 | Memory unbuilt; persona slot (C M-18, C chat 12) | med | R | AD-18 | yes | MEM | `E/memory/__init__.py` (docstring only) | folds B-52 |
| AL-20 | `engine/base` lacks HP2 and two fixes that `rebuild/base` holds (C M-19) | high | S | not architecture | — | — | — | his merge click; harness packets should start from a base that has HP2 (§3.3) |
| AL-21 | `delegate` v2 for helper chats on any provider (C M-1 option B, ruling 92) | med | R | AD-41; H26 | yes | DLG | `H/tools.py:388`, `H/harness.py:425`, `control.db` completions | decision G; probe P5 |
| AL-22 | "We have hooks": his rules guard engine chats; permission floor (B chat 4) | med | R | AD-43; H31 | yes | HERMES | `H/money.py` deny rules as data, `H/chat.py` asks | decision G |

---

## 3. Proposed packet grouping

### 3.1 Packets, in order

Each packet is one builder at a time unless "parallel" is written. Order follows 34's rule (security before bugs) with two changes the amended design forces: the caps go first because AD-40 is settled and the stuck detector replaces the guard, and the harness rounds run beside the engine packets because their files are disjoint.

| # | Packet | Rows | Design gate before build | Must land first |
| --- | --- | --- | --- | --- |
| 0 | **P0 pre-land hygiene** (hours) | B-75, B-95, B-98, B-44 | none | — |
| 1a | **CAP-E caps removal, engine, plus stuck detector** | AL-2, AL-3 (default), B-16, B-33, B-36, B-38, B-49, B-55, L-21, L-45, L-46, L-48, L-61, L-66, and L-60 once decided | settle L-60 (§5 item 1); choose "remove" or "read as `limits`" for the 31 template `runaway` blocks | P0 (`settings.py`) |
| 1b | **CAP-H caps removal, harness (H28)** — parallel with 1a | AL-1, B-7, B-9 | none (settled rule; G lists H28 as following it) | P0 only for CI; AL-20 merge base advised |
| 2 | **SEC-1 scan, redaction, publish guards** | B-89, B-13, L-24, B-17, B-39, L-58, L-51, L-52, AL-15 (t7, dm, ma) | decision F; `name_money_act_called` in `qma-core` | CAP-E (`definition/lint.py`, templates) |
| 3 | **SEC-2 script isolation** | B-30, B-31, B-26, B-78, B-80 (env half), L-39, L-40, L-43, AL-15 (manifest, `capture.py`) | decision E; probe E33 | SEC-1 (`nodes/script.py`; scan refuses imports first) |
| 4 | **HG3 harness round** — parallel with 2 and 3 (harness files only) | B-51, B-6, B-8, B-10, B-50, B-65, L-8, L-9, L-16, L-17, B-67, L-10 lane | decision D | CAP-H (`launch.py`, `harness.py`); the engine side of H2 (`nodes/llm.py`, `nodes/agent.py`) follows in BUG-1 |
| 5 | **BUG-1 run state and resume** | B-69, B-63, L-37, B-73, B-72, B-25, L-32, L-38, B-57, B-66, L-69, B-42, B-60, B-37, B-54, L-80, L-28, L-31, L-33, L-47, L-57, L-64, L-65, L-70, plus the engine side of H2 | none | SEC-1 (`ledger/store.py`), SEC-2 (`workers/effects.py`), CAP-E (`nodes/agent.py`, `core/fold.py`) |
| 6 | **BUG-2 spec-gap code ("2b") and validation** | B-18, L-29, L-34, B-24, B-87, B-27, B-76, B-68, B-23, B-20 (refusal), B-46 (refusal), B-22, B-90, L-20, L-22, L-26, L-75, L-54, L-55, L-56, B-61, B-92, L-89, B-77, B-85, B-71, B-19, B-43 | none | BUG-1 (`runner.py`, `service/runs.py`, `nodes/subworkflow.py`) |
| 7 | **L1 engine inside `qma.serve`** | B-11, B-64, B-56 | none (Appendix G L1) | BUG-2 (`control_door.py`); HG3 |
| 8 | **Engine later packets** (SD §25), one at a time: GATE (B-28, B-32), LDR (B-40, B-73, L-68), CHUNK (B-35), GRADE (B-46/B-81), PIN (B-47), NFO (B-20), REPLAY (B-82), EVR (B-80/L-84 with RV) | as listed | REPLAY needs Library L20 | BUG-2 (hash change before PIN; refusals before GRADE and NFO); all share `core/fold.py` and `core/joins.py`, so strictly sequential |
| 9 | **ROUTER router, registry and pool** (HG4 pool exception: H10, H12, H14, H27, H29, H33, H36) | AL-3 (pool), AL-4 to AL-8, B-21, B-48, B-86, L-63, L-10 (per-model point) | probes P1, P2, P3, P7; the one error classifier (AD-40) lands here | CAP-H, CAP-E, HG3 (`launch.py`, `harness.py`, `settings.py`, `nodes/agent.py`) |
| 10 | **DLG `delegate` v2** (H26) | AL-21 | decision G; probe P5 | ROUTER (one runtime resolver, leases), HG3 (H18 close) |
| 11 | **HERMES refactors**: permissions floor and rules (H31); trigger kinds `event`/`webhook`/`session`, spend-neutral re-run, delivery field, `[QMX_FAILURE]`, incidents, `explain_trigger` | AL-22 | decision G | ROUTER (classifier), BUG-1 (`triggers/ticker.py`) |
| 12 | **HG4 non-pool rows**: H32 pack sets, H34 session loops, H37 review fork | AL-11 | decision G; probes P-PK, P-FK | ROUTER, DLG (`H/harness.py`) |
| 13 | **TPL templates and builder** | AL-14, AL-16, B-88, B-84 (once decided), L-81, L-82, L-83, L-85, L-86, L-87, L-88, L-76, L-77, L-93, B-79, B-91, B-86 (remap), E48 over all 31 | B-84 evidence rule | SEC-1, SEC-2 (manifest, `QMX_MODE`), CAP-E (`runaway` blocks), BUG-2 (B-76 lets `SHARED_COPIES` go), ROUTER (role defaults) |
| 14 | **MM multimodal** (H30) | AL-18 | none | ROUTER (capability rows), DLG (images to children) |
| 15 | **BRW browser and Cua** (H35) | AL-9, AL-10 | ruling 30 journeys shown to him | HERMES (SSRF guard, blocklist), HG4 (pack sets) |
| 16 | **MEM memory** | B-52, AL-19 | none | BUG-2 (`prompts.py` order), real or fake LibraryPort |
| 17 | **LIB Library contract pieces** | B-41, B-43 (ownership), B-76 (L18), B-83 (L19), B-82 (L20) | Library Hub design | runs on `library_fake.py` until the Hub exists |
| 18 | **DESK desktop app and output renderer** | AL-17, AL-12 | shell probe | L1 (`qma.serve` is what it supervises) |
| 19 | **HYG lane and probe scripts** — parallel any time (no `src` files) | L-3, L-5, L-11, L-13, L-15, L-41, L-59, L-62, L-67, L-72, L-73, L-74, L-78, L-79, B-74, L-27, B-62 | none | L-74 after B-69; B-62 and L-27 touch `src` (`ticker.py`, `store.py`), so schedule those two after BUG-1 |
| — | **LATER** | B-34 (doctor verdicts, self-improvement), AL-13 (mini-app packet) | — | — |

Not packet work: STILL-OPEN rows B-5 and B-53 (deferred harness rows with accepted fallbacks), B-29, B-84 and L-60 (design calls, §5), AL-20 (his merge click).

### 3.2 Files two packets touch (never give these to two builders at once)

| File | Packets |
| --- | --- |
| `E/settings.py` | P0, CAP-E, ROUTER |
| `E/definition/lint.py` | CAP-E (B-16), SEC-1 |
| `E/nodes/agent.py` | CAP-E (caps, L-60), BUG-1 (B-69, H2 side), ROUTER (compaction point), MEM (snapshot) |
| `E/watchdog.py`, `E/core/ladder.py` | CAP-E, BUG-1 (B-37, L-47), CHUNK |
| `E/core/fold.py` | CAP-E (`run_created.runaway`), BUG-1, BUG-2, GATE, LDR |
| `E/core/joins.py`, `E/core/ready.py` | BUG-2, CHUNK, NFO |
| `E/ledger/store.py` | SEC-1 (redaction seam), BUG-1 (B-25, L-28, L-31), BUG-2 (event keys), HYG (L-27) |
| `E/ledger/inbox_table.py` | SEC-1, BUG-1 (L-47), GATE |
| `E/nodes/script.py` | SEC-1 (scan at dispatch), SEC-2, LIB (B-83) |
| `E/workers/effects.py` | SEC-2 (L-39, L-40, L-43), BUG-1 (B-57); B-29 when decided |
| `E/workers/local.py` | SEC-2 (B-31), BUG-1 (B-37) |
| `E/service/runs.py` | SEC-1 (L-51), BUG-1 (B-66, B-73), BUG-2 (L-56, L-89), LDR, REPLAY |
| `E/service/explain.py` | SEC-1 (L-52), BUG-2 (B-71) |
| `E/service/versions.py`, `E/service/drafts.py`, `E/service/tests.py` | BUG-2 (B-68, L-54, L-55, B-61, B-92, B-43) |
| `E/control_door.py` | BUG-2 (B-68), L1, LDR (L-68) |
| `E/triggers/ticker.py`, `claims.py` | BUG-1 (B-60, B-63, B-72, L-64, L-65, L-69), HERMES, HYG (B-62) |
| `E/runner.py` | BUG-1 (B-42, B-54, B-60), BUG-2 (B-61, B-77), PIN, ROUTER (L-63) |
| `E/definition/validate.py`, `registry.py`, `folder.py` | BUG-1 (L-38), BUG-2, GRADE, NFO, PIN |
| `E/templates/*`, `T/catalog.py`, `install.py` | CAP-E (`runaway` blocks), SEC-1 (t7, dm, ma), SEC-2 (manifest), TPL (renames, every template id) |
| `H/launch.py`, `H/harness.py` | CAP-H, HG3, ROUTER, DLG, HG4 |
| `H/usage.py` | CAP-H, ROUTER (usage hook) |
| `H/relay.py`, `H/profiles.py` | ROUTER only |

Safe parallel pairs: CAP-E with CAP-H; SEC-1 or SEC-2 with HG3; HYG (scripts only) with anything; MEM with ROUTER only if `nodes/agent.py` edits are split (snapshot in `prompts.py`, compaction in `agent.py`), otherwise sequential.

### 3.3 Dependencies worth naming

- **His decisions gate four packets:** F before SEC-1, E before SEC-2 (and probe E33), D before HG3, G before DLG, HERMES (H31), HG4 rows. H28 (CAP-H) and the pool-exception rows (ROUTER) need no new yes per OPEN-DECISIONS G.
- **AL-20 merge base:** `engine/base` lacks HP2 and two fixes that `rebuild/base` holds. Every harness packet (CAP-H, HG3, ROUTER, DLG, HG4) edits `H/launch.py` and `H/harness.py`; building them on `engine/base` before his merge click invites conflicts with HP2. Recommend his merge click before CAP-H starts.
- **Stuck detector before caps go live:** CAP-E must ship the AD-16 detector in the same PR as the guard removal, or a looping agent has no stop at all.
- **H2 before engine agent nodes run on the PC:** until HG3's H2 lands, AD-24 holds agent nodes `waiting(placement)` if E35 shows a shell tool running without an ask.
- **B-57 before Appendix G L6** (agent writes). **L-26 before PIN.** **B-76 before TPL drops `SHARED_COPIES`.** **B-78 before L-86.** **B-69 before L-74.** **ROUTER's classifier before HERMES and DLG.** **Library L20 before REPLAY.**

---

## 4. What changed from 34

- 34's SECURITY step is now two packets (SEC-1 lint and redaction, SEC-2 OS isolation), because AD-36 and AD-37 are pure code while AD-24 needs E33 and Docker.
- 34's SPEC-GAP rows are all resolved in the spine except the four in §5 below; the runaway rows (B-38, B-49, L-46, L-48, L-49) and B-33, B-36 are obsolete with the guard.
- 34's HG3 list shrank per 36 S8: H20 (B-5) and H21 (B-53) deferred, H23 (B-11) and H25 (B-64) dropped in favour of L1, H24 (B-65) labelling only.
- Four items 34 listed as open are already fixed on `engine/base` (B-45/L-53, B-58, B-59, L-71).
- New packet families the rerun added (ROUTER, DLG, HERMES, HG4, MM, BRW, DESK, MEM, TPL builder) now carry the alignment mismatches as AL-1 to AL-22.

---

## 5. What the amended design missed (called out, not fixed)

1. **The no-progress detector will stall held chunks (L-60 with B-55).** AD-16 says the worker heartbeat never counts as progress, and its detector stalls an attempt with no executor event past `timeout.idle`. The warm-first gate in `E/nodes/agent.py:122-133` holds chunks 2..N inside started attempts with no events, and AD-9's "work past capacity queues" does the same. Under the amended rule every held chunk ends `stalled` after 300 s. The spine needs one line: a held or queued chunk is a recorded wait (or is not started), and the detector skips recorded waits.
2. **Concurrent attempts in one run share one write zone (B-29).** AD-24 gives a run one `<zones_root>/<run_id>/work`; AD-8's reversible restore cannot tell one attempt's files from another's, so a retry undoes a sibling's work. AD-49's checkpoints do not answer it. Needs per-attempt zones, per-attempt attribution, or a rule that reversible nodes in one run do not overlap.
3. **No evidence rule for number checks (B-84, L-81, L-87).** AD-45 says numbers are graded before display, but not what counts as evidence. Today LLM-written intermediates and timestamps count, so the check is circular. A pack-wide rule (evidence = source inputs plus the final output only, timestamps excluded) is a design call before TPL.
4. **Memo truth (B-19, L-35).** AD-7 does not say whether the ledger events or `ledger.memo`'s `valid` flag decides memo validity; the code has both and one has no reader.
5. **Retry rule for a model node that declares `irreversible` (B-57).** AD-8 separates "model call" (retried once after `unknown`) from `irreversible_external` (never), but not a model-bearing node that also declares a non-external `irreversible` effect, which agent writes (L6) will create.
6. **A past `reset_at` that is never refreshed (L-63).** AD-12 says the provider's `reset_at` wins; it does not say what happens when the reading's reset is already past and no new reading comes. The run spins or waits forever.
7. **His own `limits` block (L-45, L-48).** AD-16 honours a `limits` block he writes as a pause, but does not say whether it is checked every tick for in-flight attempts or whether `wall_seconds` counts time asleep in waits and backoff.
8. **Snapshot retention (L-43).** No rule prunes `.snap` reversible snapshots or AD-49's shadow-git checkpoint stores.
9. **One scheduler and one instance per home, enforced (L-64, L-70).** AD-3 and AD-48 imply it; nothing binds an atomic single-instance lock per home or one `Scheduler` per engine object, and the code is check-then-write.
10. **Resume of an attempt whose chat never received its task (B-69).** AD-34's re-seed covers compaction restarts only. The code fix is clear (resend the full prompt), but the spine is silent on resume after a kill at chat start.
11. **Token estimation for `chunk by: tokens` (B-21).** The registry carries `count_tokens`, but no rule says what the planner uses when a model lacks it (today JSON bytes / 4).
12. **The 31 template `runaway` blocks.** 39 §7 says they are "removed or read as `limits` once"; that choice changes whether shipped templates carry his-style limits, which AD-40 says templates never ship. Pick "removed".
