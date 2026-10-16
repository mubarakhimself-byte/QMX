# 27d: Independent check of the 27c gap fixes (2026-10-16, night)

One Opus 5.5 checker, working alone with no sub-agents. It edited nothing except this file and made no commit. **Opus is checking Opus:** the applier of 27c was also Opus 5.5, so this check shares that model's blind spots. Fable was not used, per ruling 87.

Inputs:
- the fix list: 27b §1 and §6, plus `wayfinder/REWRITE-NOTES.md`;
- the applier's claims: 27c;
- rulings 1-88 (file 26);
- the three edited folders and `UI-HANDOFF.md`, read in the working tree. `git diff --stat` matches 27c: 26 files, +543 / −328.

Paths are relative to `tracker/qma-v2/`. `ENG` = `architecture/workflow-engine/`, `LIB` = `architecture/library-and-data/`, `LAB` = `architecture/lab-and-pods/`, `SP` = `ARCHITECTURE-SPINE.md`, `SD` = `ENG/SOLUTION-DESIGN.md`. Line numbers are working-tree lines on 2026-10-16.

## Verdict

**1 critical, 13 should-fix, 8 notes.** All 6 blockers and the 26 should-fix items of 27b were applied in substance. Nineteen are clean. Thirteen pass with leftovers or new seams, listed in §2. The 6 blockers were also applied in the spines, the designs, the plain-words files, the request files and the doc-changes files.

The edits introduced one critical contradiction. B4 says a published workflow is "the same object" as the tested draft, so its `tested-by` edge carries over. That cannot hold while the version number and lifecycle live in the object's identity. As written, a published workflow can never be "tested", so it can never be enabled. This is B3's deadlock again, by another route.

All three linters are clean. AD cross-references are all in range. Of the five judgment calls, four are sound and one (Library OPEN-7) is sound in effect but cites the wrong ruling for its governed-kind half.

---

## 1. Pass/fail per fix

PASS = applied consistently everywhere. PARTIAL = applied, with a leftover or a new seam (see §2). FAIL = not applied.

### Blockers

| # | Fix | Result | Evidence / leftover |
|---|---|---|---|
| B1 | Ruling 78: chunking, compaction, caching, hooks, tool spans | PASS | ENG SP AD-5 (`chunk`, broadcast refused), AD-15, AD-25, new AD-34; SD §2.1 example, §2.2, §2.4 lint, §3.2 `compacted`, §3.3, §7.3 affinity, §10.1, §15, §16, §17 (`chunk.fill`, `compact_at`, `max_tool_calls`), E29-E31; HARNESS H15/H16 with fallbacks; PLAIN-WORDS. The E29 arithmetic is right (⌈400k/300k⌉ = 2; ⌈400k/60k⌉ = 7). |
| B2 | Real models for test runs (ruling 51) | PASS | AD-11, AD-22; SD §6.2, §9, §16 rows 853/860, E7, E21; DOC-CHANGES row 2. The only "fake provider" left is the explicit `fake: true` switch, plus the executor's name in the source tree (SP:396), which is fine. |
| B3 | Run `mode` split from `status`; one shared table | PARTIAL | The table is identical on both sides (SD §3.1; LIB SP AD-15, Conventions; L9/L17 answered; UI-HANDOFF §9 row 8). The leftover is new: "tested" is keyed on two different things (critical C1). |
| B4 | Drafts off `main`, `refs/drafts`, triggers pin objects | PARTIAL | Applied in ENG AD-10/11/14/22/26, LIB AD-7/9/11/15/18/19, MIGRATION step 8, LAB AD-2 and Conventions. Three leftovers. (a) The same-object claim breaks (C1). (b) Lab pods still put a "`draft`-stage version" on `main` (S-1). (c) SD §4.1 still binds triggers to `workflow_id, version` (S-2). |
| B5 | Harness touch points (H0, H17, Effects) | PASS | ENG SP AD-3; SD §7.4, §13 (with every Effect); HARNESS H0 and H17 with no-edit fallbacks; LIB LLD §7 and LAB LLD §7 now point to H17; OPEN-DECISIONS A. |
| B6 | Contabo capacity from RAM (ruling 76) | PASS | No "twenty", "semaphore 20" or "32-48" left anywhere. AD-12, AD-25 and AD-30 use the formula; SD §5.4, §7.3, §17, §21 (12,288 − 6,144) / 1,536 = 4; E8, E27; PLAIN-WORDS. One small seam remains, the PC's fixed concurrency of 3 (N-3). |

### Should-fix items (27b S1-S26)

| # | Result | Note |
|---|---|---|
| S1 QMB machine is the default backtest door | PASS | LAB AD-5, AD-8; LLD §3; ENG AD-31 |
| S2 no `ask_above_usd` | PASS | Only UI-HANDOFF:76 mentions it, to say it does not exist |
| S3 runaway guard replaces the USD budget | PASS | AD-16; SD §2.2, §10.2-10.3, §15, §17 |
| S4 harness `[budgets]` | PASS | SD §7.4; OPEN-DECISIONS B |
| S5 no keys on workers; L11-L14 answered | PASS | LIB AD-12, AD-13, HLD §5b/§7, LLD §8d; ENGINE-REQUESTS-ANSWERED L11-L14. The relay-placement seam is in SD §5.4 (S-4) |
| S6 GatewayPort fronts the Hub and `qmx-node` | PASS | SD §5.3, §14.4; LIB AD-11 |
| S7 `refs/challengers` | PASS | LIB AD-7, AD-11; SD §10.2, §11.3; L16 |
| S8 Library kind and edge names | PARTIAL | SD:233 still says "`supersedes` or `archived_as`"; LIBRARY-REQUESTS L13 still says `workflow_run` (S-6) |
| S9 pack types with `base_kind` | PARTIAL | The base kind of `qmb.compile` and `qmb.compare` differs between LAB SP:102 (`app_op`) and LLD:70, :77 (`script`) (S-12) |
| S10 paper as finite runs | PASS (variant) | Daily segments instead of a per-bar interval; judgment call 1 in §4 |
| S11 `KernelPort` on `sandbox_python` | PASS | LAB AD-9, LLD §11 |
| S12 `qmb.*` effect `none` | PARTIAL | `ml.train` (LAB LLD:82) is still `irreversible`, so a dead worker parks it with an urgent ask, the same defect S12 fixed for `qmb.*` (S-8) |
| S13 one placement vocabulary | PARTIAL | LAB LLD:398 `placement=colab-or-ssh` (N-5) |
| S14 one template model | PASS | |
| S15 `setup` keeps only its CT-47 meaning | PARTIAL | LIB MIGRATION:44 `ran-on → setup(target)`; LIB LLD:117 "machine descriptors" (S-7) |
| S16 new engine tools with Effects | PASS | SD §13. One seam with the Lab's Effect for live runs (S-3) |
| S17 principal mapping | PARTIAL | LIBRARY-REQUESTS L2 and L3 still name the old owners (S-6) |
| S18 inbox severity (ruling 77) | PARTIAL | AD-17 and SD §10.4 are right, but AD-10, SD §4.2 step 4 and SD §15 rows 800, 801 and 803 contradict them (S-5) |
| S19 OPEN-DECISIONS refreshed | PARTIAL | The engine side is done. `33-state-of-play.md` was left untouched on purpose (outside the target list). It must be fixed in the "centralize" step |
| S20 provider onboarding (ruling 74) | PASS | AD-30; SD §21; UI-HANDOFF §9 row 4 |
| S21 Data track | NOT DESIGNED (by choice) | Left to his call C; this is one of the two options 27b offered |
| S22 §2.1 example | PASS | |
| S23 stale OPEN-6 references | PARTIAL | SD:863 "Library OPEN-6 respected" (S-6) |
| S24 pod/book mapping | PASS | |
| S25 verb count | PASS | The applier is right that the port has 14 verbs plus `adopt`; `archive` is `put(state)`, not a verb (LIB LLD §7) |
| S26 approvals row | PASS | UI-HANDOFF:21 |

Notes N1 (central relay), N2/F10 (`runsc` claim), N5 (E32) and N7 (run-made lifecycle kinds become drafts) are PASS. The 27b §5 UI-HANDOFF items are PASS: 33 kinds, 24 relations, "compact now" waits on H15, and all 15 rows of §9 are present.

---

## 2. New problems, ranked

### Critical

**C1. "Tested" cannot survive publishing, so a published workflow can never be enabled.**
- *Where:* ENG SP:128 (AD-11) says publishing an unchanged tested draft "moves that same object onto `main`, and its `tested-by` edges travel with it". ENG SP:146 (AD-14) defines a version as `(item_id, fields.semver, object_id)`. LIB SP:146 (AD-15) says tested means a `tested-by` edge "for that exact object id; because the object id is the content, publishing an unchanged tested draft keeps the edge". SD E7 (:1047) asserts the same.
- *Against:*
  - LIB LLD:54: the identity covers `fields` and `parents`, and the blob bytes ride the object id through `blobs`.
  - SD §2.1:42-43 and :89, and SD §2.2:98: the definition document stores `version`, `content_hash` and `meta.lifecycle: "draft"`, and "`version` / `content_hash` [are] assigned at publish".
  - SD §6.1 ("publish() mints (version, hash)") and SD :492 (`publish(item, from_ref, semver)`).
  - LIB AD-7: a publish from an agent ref, or after `main` moved, is a three-way merge that mints a new object with `merged-from`.
- *Problem:* publishing writes a semver and a new lifecycle into the stored document, or merges. Either way the published object id differs from the tested draft's id, so the `tested-by` edge stays on the draft. AD-11 says "Enabling a trigger on a version requires that version to be tested", so enabling is refused. There is also a second key: SD §6.2 (:388) binds the test report to the definition `content_hash`, while the Library keys "tested" on the object id.
- *Fix (exact edits; one key, the definition `content_hash`, which SD §2.2 already defines to exclude `version`, `position` and `meta`):*
  1. ENG SP:128: replace "Because a Library object id is its content, publishing an unchanged tested draft moves that same object onto `main`, and its `tested-by` edges travel with it." with "A version is **tested** when a `workflow-run` with status `passed` (either mode) ran an object whose definition `content_hash` (SOLUTION-DESIGN §2.2) equals the version's; publish copies the draft's `tested-by` edges onto the published object when the hashes match, and a publish that changes the hash (a non-fast-forward merge) needs a new test before enable."
  2. ENG SP:146: change `(item_id, fields.semver, object_id)` to `(item_id, semver annotation, object_id)`. Add: "the semver and the lifecycle are annotations or ref facts, never fields of the stored definition".
  3. SD §2.1: delete `"version"` and `"content_hash"` (:42-43) and `"lifecycle"` and `"tested_hash"` (:89) from the stored document. SD §2.2 :98: "`version` is a Library annotation set at publish; `content_hash` is computed, never stored in the document; …".
  4. LIB SP:146: replace "for that exact object id; because the object id is the content, publishing an unchanged tested draft keeps the edge" with "for an object whose `fields.content_hash` equals this one's; `publish` (engine) copies the edge onto the published object when the hashes match".
  5. LIB SP AD-3, the `workflow` kind: add that `semver` is an accepted annotation (AD-2), so setting it mints no version.
  6. SD E7 (:1047): "…publishing the unchanged draft gives a `main` object with the same `content_hash`, which reads as tested; a publish whose merge changed the hash reads as untested."
  7. LIB ENGINE-REQUESTS-ANSWERED:27 and LAB LLD:259: the same semver wording.

### Should-fix

| # | Where | Problem | Exact edit |
|---|---|---|---|
| S-1 | LAB SP:144 (AD-10) "`stage draft\|tested\|paper\|promoted`" and "its Save is a new `draft`-stage version"; LAB LLD:99, :163; UI map :86 "stage Draft / Tested …" | After B4, `main` holds published versions only, yet a saved pod version on `main` is still called `draft`. Two meanings of "draft" collide, and this is the "`main` holding drafts" leftover. | Rename the pod stage `draft` to `untested` in AD-10 ("`stage untested\|tested\|paper\|promoted`"; "its Save is a new `untested` version"), LLD :99 and UI map :86 ("stage Untested / Tested / On paper / Live"; the UI label may stay "Draft" only if the handoff says it means untested). |
| S-2 | SD:262 (§4.1 trigger row) `trigger: id, workflow_id, version, …` | Stale against AD-10 (`pinned_object`, `follow_champion`, `home_engine`). | `trigger: id, workflow_item, pinned_object, follow_champion, home_engine pc\|contabo, kind cron\|interval\|event\|webhook\|manual\|after,` |
| S-3 | LAB LLD:324 `qmb.backtest` "DOMAIN_WRITE … live on a version"; LAB SP AD-13 vs SD §13:684 (`runs.start` live = `workflows_run`, MANAGE) | The two architectures give a live run two different Effects. | LAB LLD:324 note becomes "test mode on a draft (DOMAIN_WRITE); a live run of a published version goes through the engine's `workflows_run` (MANAGE, asks once, SD §13)". Add the same clause to LAB SP AD-13's MANAGE list. |
| S-4 | SD:350 (`cli_inside` row "`qmx-egress` … injects the key-provider key"), SD:352 (Keys row "the egress proxy injects per lease"), SD:351 ("a second key path (egress) exists"), SD:478 (§7.4 "the proxy resolves the key from the keyring and injects it"), HARNESS H8 fallback :18 | This contradicts ENG AD-25 ("egress proxy is only a domain allow-list"), AD-28 (the relay is the only key reader on a host) and SD §19:950. It is a relay-placement contradiction: the applier edited SD:478 and kept the old sentence. | SD:350: "…model traffic carries the run pass to the nearest relay (AD-28, H11), which injects the key; `qmx-egress` holds only the domain allow-list…". SD:352: "in `cli_inside` the relay named by the pass injects the key; in neither mode…". SD:351: drop "a second key path (egress) exists". SD:478: "For a `cli_inside` node the engine mints a run pass whose `relay_url` is the nearest relay; the container's CLI uses the pass as its token and the relay as its base URL; no key enters the container or the egress proxy." H8 fallback: "…with the run pass to the relay (H11)". |
| S-5 | ENG SP:122 (AD-10 "`blocked_config` with one inbox item"), SD:278 (§4.2 step 4), SD:800 ("Worker dies mid irreversible call → `urgent` item"), SD:801 ("`normal` digest line"), SD:803 ("one item until fixed") | These contradict AD-17 and SD §10.4 (ruling 77). Row 800 also fires for every `agent` and `llm` node, because model spend is classed `irreversible`, so any worker death during an agent call would page him. | AD-10: "…sets `blocked_config` with one item whose severity follows AD-17 (`info` when the workflow's own configuration is at fault)". SD:278: same. SD:800: "Operator sees: `urgent` item with the idempotency key only when the effect is `irreversible_external`; for a model call, an `info` line (the memoised result is lost, the attempt is retried once under the ladder)". Also amend AD-8 :110 to say "a model call with an `unknown` outcome is retried once (duplicate spend is accepted, ruling 27); only `irreversible_external` effects never auto-retry". SD:801: "`normal` item". SD:803: "one item, severity per §10.4". |
| S-6 | SD:233 "`supersedes` or `archived_as`"; SD:863 "(Library OPEN-6 respected)"; ENG LIBRARY-REQUESTS :10 (L2 owner `run:<run_id>`), :11 (L3 "`hub` on the server, the local engine on the PC"), :21 (L13 `workflow_run`) | Stale names and owners from S8, S17 and S23. | SD:233: "`replaces` or `archived-as`". SD:863: "(Library AD-18: challengers never touch `main`)". Add to each of L2, L3 and L13: "(as asked; the granted shape is in ENGINE-REQUESTS-ANSWERED)". Or fix L13 to `workflow-run`. |
| S-7 | LIB MIGRATION:44 "`ran-on → setup(target)`"; LIB LLD:117 `setup` source "machine descriptors" | This is the S15 leftover. `ran-on` is retired and `setup` is CT-47 only. | MIGRATION:44: "…; the manifest's target becomes the run's placement fields (engine L14)". LLD:117: delete "; machine descriptors". |
| S-8 | LAB LLD:82 `ml.train` effect `irreversible` | Same defect as S12: a worker dying mid-training parks the run with an urgent ask (rulings 57, 77). | Effect `none` (checkpointed, memoised by intent key; a retry resumes from the last checkpoint). |
| S-9 | LAB LLD:434 (§8.5) "a governed kind (`bot`, `pod`, `pod-block`) merges under MANAGE" | This contradicts LAB Conventions :196 and LIB AD-9: `pod` is a lifecycle kind, `pod-block` stays DOMAIN_WRITE, and `bot` is governed. | "a governed kind (`bot`, `unit`, `book`, `bms`) or a lifecycle kind (`pod`, `workflow`) merges into `main` under MANAGE; `pod-block` stays DOMAIN_WRITE". |
| S-10 | LIB SP:98 (AD-7) "the store where that workflow's schedule is bound (`fields.placement` of the workflow object …)" | The engine puts a schedule's home on the trigger row (`home_engine`, ENG AD-3), and one workflow may have triggers on both homes. A `fields.placement` would also be identity, so moving a schedule would mint a version. | "…on the store of the engine instance named by the trigger's `home_engine` (engine AD-3); a workflow whose triggers live on both homes keeps one champion and memory owner, the `contabo` instance (the schedule default)". |
| S-11 | LIB SP:110 (AD-9) "a merge into `refs/drafts/<item>` is DOMAIN_WRITE"; LAB LLD:434 "brings the agent's draft into his draft (DOMAIN_WRITE)" vs LIB AD-7 "A principal may advance only refs it owns" (`refs/drafts` is owned by `operator`) | An agent merging into his draft breaks the owner table without saying so. | Add to LIB AD-7, after the `refs/drafts` owner: "`agent:<session_id>` may also merge into `refs/drafts/<item>` (DOMAIN_WRITE, recorded `merged-from`); it may not `put` onto it." |
| S-12 | LAB SP:102 (AD-3) lists `qmb.compile` and `qmb.compare` under base `app_op`; LAB LLD:70, :77 give `script` | Two base kinds for the same types. | LAB SP:102: move `qmb.compile` and `qmb.compare` out of the `app_op` list: "`qmb.compile`, `qmb.compare` (base `script` over `QmbPort`)". |
| S-13 | UI-HANDOFF:48 "goes to the inbox while the run parks [engine AD-22]"; UI-HANDOFF:62 "[library AD-18, OPEN-7]", governed kinds only | "Park" now means `failed`; that step makes the run *wait*. The citation should be AD-16/AD-17. OPEN-7 is closed, and lifecycle kinds ask too. | :48: "…which goes to the inbox while the run waits (`waiting`) [engine AD-16, AD-17]". :62: "A copilot-chat merge of governed kinds (units, bots) or lifecycle kinds (workflows, apps, pods) into `main` asks once [library AD-9]". |

### Notes

| # | Where | Note |
|---|---|---|
| N-1 | SD §3.1 :158 | `failed` is marked terminal, yet "he may resume it from the run card". Say "terminal unless resumed by him". |
| N-2 | ENG SP AD-16 :158; SD :581 | A runaway pause ends `stopped` "when the next occurrence starts". A manual-only workflow has no next occurrence, so it waits forever. Add "or after `limits.alert_after`". |
| N-3 | ENG AD-25, SD §5.2, §17 `placement.pc.concurrency 3` vs AD-30 "No session count is a constant anywhere" | The PC's 3 is a container cap, not a session count, but the text does not say so. Say it once in AD-30. |
| N-4 | SD E8 :1048 (8 Background chats) | With the default `max_live_chats` 4 this test cannot pass. State `max_live_chats ≥ 8` as a setup condition. |
| N-5 | LAB LLD:398 `placement=colab-or-ssh` | This is a vendor name in a placement (S13). Use a registry row name. |
| N-6 | ENG PLAIN-WORDS:9 "that one budget", "remaining budget" | Ruling 27 wording: say "token allowance". |
| N-7 | UI-HANDOFF:20 "add `failed`, `cancelled`, `expired`" | These are chat turn words. Say "chat status words" so nobody adds `cancelled` to run statuses (§9 row 8 has no `cancelled`). |
| N-8 | ENG SP:404-406 source tree | `service/` is indented under `services/qmx-vault/`. This predates 27c (it is in HEAD); move it up under `qmx_engine/`. |

---

## 3. Lint results

Command: `uv run C:\Users\Mubarak\Desktop\QMX\.claude\skills\bmad-architecture\scripts\lint_spine.py --workspace <folder>`. It exits 0 under `uv run`.

| Spine | ok | findings |
|---|---|---|
| `ENG/ARCHITECTURE-SPINE.md` | true | 0 |
| `LIB/ARCHITECTURE-SPINE.md` | true | 0 |
| `LAB/ARCHITECTURE-SPINE.md` | true | 0 |

The linter checks only within one spine. It does not check AD references across the three architectures, so I checked them by hand. Every "engine AD-n" is at most 35, every "Library AD-n" at most 19 and every "Lab AD-n" at most 17, and the sampled ones point at the right topic. The one wrong pointer is UI-HANDOFF:48 → AD-22 (S-13). Every "SOLUTION-DESIGN §n" cited from a spine exists. SD sections run 1-17, 19-24, then 18, out of order, which predates 27c.

---

## 4. Judgment calls of the applier

| # | Call | Verdict | Reason |
|---|---|---|---|
| 1 | Paper soak = one finite run per trading day (daily cron, `continuity`, bounded loop over the day's bars), overriding 27b's per-bar interval trigger | **Sound, with two conditions** | It meets engine AD-25 (a finite run with a bounded ledger) and avoids the Library churn of one `workflow-run` and one `paper-run` version per bar. It keeps pause and resume as trigger toggles. The source is the brief, not a ruling; 27c's header "Ruling or brief" says so honestly. Conditions: (a) for 24-hour markets, define a "day" as the market's session boundary and end each daily run before the next fire, or `max_concurrent 1` will block the next day; (b) the paper template's runaway `wall_seconds` must cover that session, and the §17 default of 4 h does not. Add both to LAB LLD §5.5. |
| 2 | H0 fallback: one allow-listed adapter imports `Background` and `Child` from `qma.harness.launch` | **Sound** | Ruling 24 forbids editing the harness, not importing from it. The rule is narrow (one module, two names) and lint-enforced. Its risk, coupling to a private path, is stated. |
| 3 | H17 fallback: drafts through `library_save` plus a test-on-save watcher; `workflows_put` and `workflows_run` re-scoped to publish and live run | **Sound** | No harness row changes. Re-scoping changes `qmx_control` behaviour, not the harness table, and both rows stay MANAGE as they should. The watcher must run `validate` and refuse non-`workflow` kinds before it starts a test. Add that to SD §13:694. |
| 4 | Library OPEN-7 closed by ruling 80 | **Sound in effect; cites the wrong ruling for half of it** | Ruling 80 names workflows, mini apps and pods ("creation is human-driven first"), so the lifecycle-kind half stands. The governed half (`unit`, `strategy`, `bot`, `book`, `bms`, `binding`) is not ruling 80. It is the earlier recommendation, consistent with DEC-0188's click-gated promotion. `skill` and `methodology` were added by inference. Edit LIB OPEN-DECISIONS:5 to "…lifecycle kinds closed by ruling 80; governed kinds keep MANAGE on the existing recommendation (DEC-0188); `skill` and `methodology` follow the lifecycle rule by inference". |
| 5 | Lab OPEN-3 (who starts paper) and OPEN-5 (Lab schedules) closed by ruling 80 | **Sound** | OPEN-3: ruling 80 says it in words ("Starting a pod on paper is part of that human-driven creation"). OPEN-5: "build, test, paper if needed, then run autonomously" plus engine AD-22 gives one yes at publish or enable, then no asks (ruling 57). Dropping the earlier "standing Lab allow rule" idea is consistent. |

Other overrides in 27c §2 also hold:
- one vocabulary with no mapping layer;
- the copilot drafts placement rows and he applies them, because `settings_put` is out of agent reach;
- a runaway breach pauses or degrades the run.

The pause wording needs N-2.

---

## 5. What to do before the plan continues

1. Fix C1 (seven edits, §2). Without it, packets 2 and 4 would code an enable gate that can never open.
2. Apply S-1 to S-13. They are one-line edits in place, with no AD id moved.
3. Apply 27b's `33-state-of-play.md` edits in the "centralize" step (S19). 27c left them out on purpose.
