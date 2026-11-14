# Plan intent audit B, 12 November: RC-47 to RC-69

Read-only. Covers every UPDATE section from RC-47 to RC-69 in `PLAN-STALENESS-2026-11-12.md` (RC-48, 49, 50, 53, 54, 55, 56, 58, 63, 64, 65, 68, 69: 13 sections, 19 stale facts), and the report's six shared facts where they reach these sections. RC-47, 51, 52, 57, 59 to 62, 66 and 67 are VALID there and are touched only where a shared fact reaches them.

Code is read at the tip `8d0a9758` unless a branch is named. "Root" is `351e7521`.

**How intent is weighed.** The owner's own words, from user messages in the planning transcript `2928e6ee…jsonl`, are quoted with their timestamp. Everything the lead agent or its subagents decided (SPINE, OPEN defaults, FIXES, the lead's 7 Nov trims) is labelled **agent decision** and judged on its merits and blast radius, not as settled. One more source counts as the owner's: the docs corpus he signed off on 21 August (ADR headers say so).

What the owner said that bears on these sections, in his words:

- Pods, 3 Nov 10:46: "units are not mini apps, obviously, but pods are meant to be mini apps. But if you look at the definition of a pod in a hedge fund setup, it's more like the book". Later in the same message: "a scalping based pod or scalping based system, risk management [and] sizing system of a unit".
- Pods, 7 Nov 13:00: "question number five [portfolio day stop] goes back to the customizability layer because we have pods inside the UI… I highly doubt you even know what a pod is."
- Pods, 7 Nov 14:47: "when I mentioned the hedge fund style, I said, I think… I did not say it is." Then at 17:41: "If the pod thing makes no sense, you can propose something new, but [you'll] talk about everything you've overhauled when we come back."
- Book and BMS, 3 Nov 10:46: "self-optimizing at a portfolio level… At a BMS level, opens up more slots to go to intraday… if the capital allows… the BMS was doing this… It's just that it wasn't self-configured." The 1 Nov session summary records his ruling, quoting him: "The Book/BMS system is the skeleton to enhance and rebuild ('everything is sort of falling into place inside the book system')". (This one comes from the summary, not a raw message.)
- Configurability, 7 Nov 13:00: "I want to first make something customizable, something more of like a baseline, something we can build on."
- Trust, 8 Nov 16:07: "I'm just going to trust your work." That is general consent to run the plan. It is not a ruling on any single item below.
- "Stop at stage B" (3 Nov 16:06) refers to a planning stage of that session, not to build stop point B. The assistant's reply at 16:07 confirms it. The three stop points (OPEN 8) are an **agent decision** he has never ruled on.

## Summary

| Section | Stale fact | Verdict |
|---|---|---|
| RC-48 | 1. Depends on rc-29, which is parked | DESIGN CALL |
| RC-48 | 2. Node version already 0.1.15; BACKLOG's journal-kinds item missing | MECHANICAL |
| RC-49 | 1. Lifting `tags` needs `compiler.py` and the generated files | MECHANICAL (two design calls ride on it, D3 and D4) |
| RC-50 | 1. `RiskState` has no money, open-risk or cushion fields; the cushion is in R | DESIGN CALL |
| RC-53 | 1. Lifting `risk_locks` and `recipe` moves the generated files; the `enabled` field | MECHANICAL |
| RC-54 | 1. `promote.py:422-447` is now `_no_live_deployment` at `:490-513` | MECHANICAL for the pointer; DESIGN CALL on the paper-twin test it carries (D5) |
| RC-55 | 1. `unit.py:990-991` is now `_cold_reason`, `unit.py:2252-2258` | MECHANICAL |
| RC-55 | 2. `runtime.py:2098` is now `self._compiler`, `runtime.py:2424` | MECHANICAL |
| RC-56 | 1. Lift `stages` and `stage_values`; the guide and schema files are missing | MECHANICAL, plus a stacked-code finding (F2) |
| RC-58 | 1. The `sections.py:57` fix must land here | MECHANICAL |
| RC-58 | 2. `runtime.py:367-369` is now `runtime.py:403-416` and `:503-528` | MECHANICAL; one sub-gap is a DESIGN CALL (D6) |
| RC-58 | 3. `reads`, `home_markets`, `context_needs` lift; `Read` has no publisher | MECHANICAL |
| RC-63 | 1. QMB already reports a motion-off arm | DESIGN CALL |
| RC-64 | 1. Templates bind `@2`, not `@1` | MECHANICAL |
| RC-64 | 2. `classify` has no caller; `diff.py` and the judge are not in Files | MECHANICAL |
| RC-65 | 1. "Format 6 at 5" is stale | MECHANICAL |
| RC-68 | 1. `runtime.py:1807-1808` is now `runtime.py:2114-2115` | MECHANICAL |
| RC-68 | 2. The six-exit-stack test moves into this row | MECHANICAL |
| RC-69 | 1. `_netted` is live-only, text-only; extend to every lane? | DESIGN CALL |

Counts: 19 stale facts. 15 are MECHANICAL and 4 are DESIGN CALLs (RC-48 fact 1, RC-50, RC-63, RC-69). The audit raised 5 more design calls that are not stale facts themselves (D2 pods, D3 tag partition, D4 which group answers, D5 paper twins, D6 empty home markets), for **9 DESIGN CALLs** in all. It also found 4 places where stacked code misses its own intent (section "Stacked code against its own intent").

## Shared facts, as they reach these sections

1. **Compiler format.** It is 12 at the tip, 13 on rc-33 and 14 on rc-34. `build/rc-35` currently points at rc-34's early commits at format 13 and has no rc-35 commit yet. The brief should never name a number. Corrected text for every row below that touches the compiler: "Bump `COMPILER_FORMAT_VERSION` by one from the parent's value only when this row changes a compiled decision (AD-19)." By that rule:
   - **Bump:** RC-56 (stages compile into the plan), RC-58 (reads compile), RC-68 (partials and trails), and RC-69 when `OrderSpec` is compiled.
   - **No bump:** RC-49 (`tags` is not in the plan) and RC-53 (a stamped document compiles like a hand-written one).
2. **Generated files.** RC-49, 53, 56 and 58 must add the generated-file list to Files, verbatim:
   - `qml/src/qml/compile/compiler.py`
   - `qml/src/qml/unit/qmx.unit.1.schema.json`
   - `qmx-agents/packages/qmx-library/src/qmx_library/kinds/unit.schema.json`
   - `qml/tests/test_unit_refuses.py`
   - `tools/qml/extending.py`
   - `qml/EXTENDING.md`
   - when the format moves, also `qml/tests/test_receipt.py` and `qmx-agents/packages/qmx-judge/src/qmx_judge/conformance_pack/{pack.json,golden.json,fixture.json}`

   rc-33 shows the full set: it touched exactly these 9 paths beside its own files.
3. **Stdlib count pins** (`qml/tests/test_nothing_silent.py:251`, `qmx-agents/packages/qmx-host/tests/test_dictionary_full_size.py:117,119`). None of the UPDATE sections here adds a stdlib block. RC-51 (VALID) adds 3, so its brief must name both pins.
4. **The closed reason lists.** This fact over-reaches for these sections:
   - `partial_full` (RC-68) is an exit close reason. Trade rows carry exit reasons with no closed list (`journal_kinds/unit.py:180-189`, `_trade` checks only the rate stamps).
   - `netting_not_attributed` (RC-69) and `retest_missing` (RC-65) are deploy refusals. They set `Phase.REFUSED` with a detail (`runtime.py:3284-3286`); they are not decision skips.
   - `logic_changed` (RC-55), `stale_click` (RC-49), `stale_plan` (RC-54) and `recipe_touches_logic` (RC-53) are door or host answers.

   None of them needs `REASON_CODES` or `_REASON_WORDS`, unless a builder writes one as a decision skip's text. There is a real trap here: `_REASON_WORDS` maps any text containing "venue cannot" to `health_stop` (`qmb/src/qmb/results/journal.py:87`). So a new capability refusal worded "the venue cannot…" files silently as a health stop, not as `unlisted` (finding F3).
5. **`runtime.py` line numbers.** Lines move on every branch. For example, `_cold_reason` sits at `unit.py:2257` at the tip, `:2301` on rc-22, `:2282` on rc-26 and `:2449` on rc-34. Briefs should anchor on symbols, not lines. The symbols are given per section below.
6. **Fact names.** `market.<name>:<market>` is the convention. It reaches RC-49 and RC-50 through design call D4: a unit may sit in two groups, so a bare `group.limit.day_stop` is ambiguous.

## Detail

### RC-48, stop point B

**Fact 1: it depends on rc-29, which is parked.**
- Plan: Depends on "RC-39, RC-46, RC-47, RC-29". Stop B is "the whole single-unit baseline", and its fact runs "K9 2, 11, 12, 15, 16, 17 … in one run".
- Code: `build/rc-29` is parked after two fix rounds (`PARKED`). Its Opus review is NOT CLEAN with one money-path blocker: on a day the node did not watch begin, the account day brake is off all day. The measured fix is about 9 lines of code plus one test (`QUESTIONS-FOR-OPERATOR.md`, "rc-29 is parked: may it take a third small fix?").
- Intent: the plan (agent) wants account brakes proven on two units inside the baseline. The run rules (agent) cap fix rounds at two. No owner words. His word is already asked for in `QUESTIONS-FOR-OPERATOR.md`.
- Blast radius: RC-48 lists the rip-out rows, and rc-29 adds a labelled placeholder for the node's day-start clock (decisions.tsv 2026-11-11 00:55). Without rc-29, stop B's rip-out list and K9 run lack the account-brake rows. Nothing between RC-35 and RC-47 depends on rc-29.
- Options:
  - (a) He says "fix rc-29 a third time". Cost: one small fix round and one review. It closes a money-path hole.
  - (b) Drop rc-29 from stop B and say in the stop-B note that the account day brake has a known hole after an unwatched midnight. Cost: stop B ships a known money-path hole.
  - (c) A fresh builder rebuilds rc-29 from the tip. Cost: most of a row.
- **Recommend (a).** It is the smallest change, and the hole is on the money path.

**Fact 2: the node is already at 0.1.15, and the journal-kinds item is missing.**
- Plan: "Bump version rows and digests". No number is named, so nothing is wrong, only unstated. At root the version is 0.1.14. RC-20 moved it to 0.1.15 (`beca0a1d8`). No row since then, and no in-flight branch, touches `qmx-agents/apps/trading-node/` (checked by diff).
- BACKLOG line 8 (from RC-02): the guide's journal kinds are hand literals (`tools/qml/extending.py`, `_JOURNAL` and the host-owned list), so a new kind in the qmf-data registry (`SPECS`, `journal_kinds/unit.py:276-336`) never fails `--check`.
- Intent: SPINE §7 "`EXTENDING.md`" (agent) says the guide generates "reason codes and journal kinds". The RC-02 builder kept the generator qml-only on purpose: its docstring line 12 says "imports only `qml`, so qml's declared package dependencies do not move". Both intents fit if the check reads the registry in a test, not in the generator.
- Blast radius: RC-49, 50, 55 and 56 add row kinds (`stage_move`, `risk_move`, group rows). Without the check, the guide drifts with each of them.
- **MECHANICAL.** Corrected brief text:
  - Build: "Move the trading node from `0.1.15` to `0.1.16` and re-pin its digest."
  - Files: add "Edit `tools/tests/test_extending.py`".
  - Verify, unit, add: "`test_the_guide_lists_every_unit_kind`. The guide's journal kinds equal the kinds `qmf.data.journal_kinds.unit.SPECS` declares for the unit stream, so a new kind fails `--check`."

### RC-49, group document

**Fact 1: lifting `tags` needs `compiler.py` and the generated files.**
- Plan: "selector by unit id or tag", and `test_many_to_many_selector` (a unit tagged `fx` and `scalper` belongs to both groups).
- Code: `tags` is refused as `tags_not_built` at `compiler.py:1259-1263`. `Unit.tags` exists (`model.py:604`).
- Intent: AD-8 says membership is by selector, unit ids and/or tags (agent). The refusal was RC-03's placeholder until "its own PR lifts it" (PLAN line 303). Both agree.
- **MECHANICAL.** Add the shared-fact-2 file list. No format bump.

Two design questions ride on this lift. They are D3 and D4 below.

- **D3, the tag's partition (agent decision, not stale).** `sections.py` puts every field not in `RISK_FIELDS` into the logic half (`sections.py:33-39`). So adding a tag to a unit moves its logic fingerprint. That means a new version and a G re-run for every member tagged after deploy: about 17 minutes per 200 units by OPEN 13. AD-8 wants membership that "touches no member" and AD-5 one click. AD-2's catch-all is the agent's safe default; it did not consider tags.
  - Options:
    - (a) Leave tags in logic. Cost: retagging a fleet re-proves it.
    - (b) Move `tags` into `RISK_FIELDS`. A tag edit then needs his one click and no G re-run. Cost: `sections.py`, `test_unit_sections.py:80` and RC-03's partition test change.
    - (c) Put tags outside both halves, like `recipe`. Cost: a tag could move a unit into a group whose `group.raise_ok` lets a modifier raise size with no click.
  - **Recommend (b).** A tag changes which caps and group facts apply, which is a risk change, so it needs a click but not a logic re-proof.
- **D4, which group a member's row reads (agent decision, not stale).** A unit in two groups that reads `group.limit.day_stop` or `group.raise_ok` cannot know which group's value it got. Caps run at the group, so they are not affected. Member-side rows are (AD-8: "a member's cap row or modifier row reads it").
  - Options:
    - (a) Name facts `group.<name>:<group_id>` (shared fact 6). Cost: the member's row must name a group id, which edits the member document and contradicts AD-8.
    - (b) Member-side reads resolve through the deployment's own `group_id` (AD-8 already allows "a deployment may also name `group_id`"). Selector membership by tag then applies caps only. Cost: a member's own group must be chosen at deploy.
    - (c) Allow one group per unit. Cost: drops many-to-many.
  - **Recommend (b).** Publish on `group:<id>` as planned, and have the node map `group.*` for a member to its deployment's `group_id`. `test_many_to_many_selector` then asserts caps from both groups and member facts from one.

Also: the `book` and `bms` Library kinds go read-only with no migration (Appendix H 2, agent decision). Both kinds are empty shells (`bms.schema.json` has `"properties": {}`), so no data is lost. But the owner named Book/BMS as "the skeleton to enhance and rebuild" and described the BMS opening "more slots… if the capital allows". The spine maps that to a thin group with `parent`, `share_cap` and an off-path share reading (AD-8). That mapping is defensible, but he has never seen it (see D2).

### RC-50, group caps

**Fact 1: `RiskState` has no money, open-risk or cushion fields, and the cushion is in R.**
- Plan: "Fold group scope. Expose `group.day_pnl`, `open_risk`, `raise_ok`, `cushion`, `members`, `limit.<name>`." `test_a_day_stop_fires_with_no_entry_pending` crosses -500, which is money.
- Code:
  - `RiskState` at `packages/qmf-risk/src/qmf/risk/controls.py:144-161` has `scope, word, since, reason, stamp, unknown`.
  - RC-14 (PR 368) departure 1 says: "Shipping them as fields that always read `None` would tell a reader nothing true, so they land with the rows that feed them. Section 3's shape is additive."
  - On rc-22, the cushion ledger is `Cushion(realised, peak)` "in R after costs" (`build/rc-22:controls.py:222`). The fold's `realised` rows carry only `r` (`build/rc-22:qml/fold.py`, docstring). Every modifier receives `cushion.<clock>.realised` and `.peak` with no scope (`build/rc-22:qml/protocol/unit.py:1131-1132`).
- Intent:
  - SPINE §3 "Status and records" (agent): `RiskState` carries `money; open_risk; drawdowns; control_distances; cushion; stage`.
  - WALKS 12 line 125 (agent): "scope `group` reads `group.cushion` from the ledger".
  - AD-11 (agent): "one cushion ledger".
  - RC-14's builder (agent): add fields with their rows.
  - No owner words on units. He asked to "Keep house money and accelerators; brakes first" (summary).
- Blast radius:
  - rc-22's `cushion-rule@1` reads unscoped keys, so a group cushion needs a scope parameter, which means a new block version.
  - A day stop in money needs money on `realised` rows, and rc-22 writes R only.
  - RC-51 (kill line in money), RC-57 ("Cushion pair" gallery pod) and RC-62 (fleet watch, "money since anchor") all read these.
  - `RiskState` lives in qmf-risk, and that file is not in RC-50's Files.
- Options:
  - (a) Group cushion in R (the sum of members' realised R since the anchor), named `group.cushion.<clock>.realised` and `.peak` to match rc-22's keys. `group.day_pnl` and `group.open_risk` are in account money. Add `money` to `realised` rows. Cost: rows widen; `cushion-rule` gains a scope parameter (`@2`). R summed across units of different size understates a big unit's loss.
  - (b) Group cushion in money. Cost: two ledgers in two units, against AD-11's "one ledger".
- **Recommend (a).** Put the group ledger's figures in RC-50's own `qml/group/ledger.py` and publish them as facts. Keep `RiskState` to the word. Add to Files:
  - `packages/qmf-risk/src/qmf/risk/controls.py`, only if the fields go on `RiskState`
  - `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`, for money on `realised` rows
  - `qml/src/qml/blocks/stdlib/cushion-rule/2/`, with the count pins of shared fact 3

  Every brief line naming `group.cushion` should say "in R", and `group.day_pnl` "in account money".

### RC-53, pods as recipes

**Fact 1: lifting `risk_locks` and `recipe` moves the generated files, and the `enabled` field is not writable.**
- Code: refusals at `compiler.py:1241-1252`. `recipe` already sits outside both halves (`sections.py:37-38`). `risk_locks` falls in logic, by the catch-all.
- The `enabled` document field: the RC-22 plan says "Read `enabled` as a bool or a fact name on every row" (PLAN line 1585). rc-22 built the runtime read (`controls.py`, `if isinstance(row.enabled, bool)`) but left the document schema at records only (BACKLOG line 58). RC-41's own test writes `enabled: false` in a document, and RC-41 lands first in the chain.
- Intent: AD-4 and AD-8 (agent). "A row may bind `enabled` to a fact, so a recipe can switch a modifier… for a whole pod."
- **MECHANICAL.** Corrected text:
  - Files: add the shared-fact-2 list (`compiler.py` is already there).
  - Build: "`enabled` is writable in a document from RC-41. If RC-41 shipped without it, add it here to `model.py`, both schema copies, the census and the guide."
  - Apply D3's reasoning to `risk_locks` too: a lock decides which risk rows a pod may replace, so it belongs in `RISK_FIELDS`.

Owner intent on the whole row is a finding (D2). The owner's "pod" sounds most like the spine's **group** ("more like the book", portfolio day stop is "a pod question"), plus a "scalping based… risk management [and] sizing system of a unit", which is the spine's recipe. He also said pods "are meant to be mini apps", and nothing here makes a pod a mini app. OPEN 1's default "recipes" is an **agent decision**. He was promised a walk-through of overhauls ("talk about everything you've overhauled when we come back"), and the store defers that to stop B. RC-53 to RC-55 are the rows thrown away if he rules "governing pod".

### RC-54, one plan, one click

**Fact 1: the pointer.**
- `promote.py:422-447` at root is `_no_live_deployment`, now at `promote.py:490-513`.
- **MECHANICAL.** Corrected text: "and `_no_live_deployment` (`qmx_host/promote.py`) and its tests stay green."

**D5, the test that pointer sits in.**
- Plan: `test_two_deployments_of_one_version`, "Paper twins both deploy", and "Keep the deployment key as unit version, market, lane and recipe hash". The word "keep" assumes the key already has those parts.
- Code: the lifecycle key is `MarketKey(unit, version, market)` (`qml/lifecycle/machine.py:65`). A click's digest has no lane and no recipe hash (`promote.py:154-166`). One key holds one state, so paper and live of one version on one market cannot coexist. A second click for the same target is treated as a retry (`promote.py:407-410`).
- Intent:
  - The plan: S14 and FUNNEL 3.8, with twins as "content on S14's deployment key" in FATES (agent research).
  - Against it: ADR-0009 (operator-ratified corpus, 21 August) lists "Parallel Bot paper twins — dead (DEC-0069)", and ADR-0022's dead list says "paper twins" stays dead. The ADR quotes the owner: "by default the paper is meant to be the Book".
  - Separately, AD-5 gives each stamped member "a new unit version", so the recipe hash in the key is redundant.
- Blast radius: changing `MarketKey` touches `qml/lifecycle`, `qmx_host/lifecycle.py`, `promote.py` and 5 test files. None of them except `promote.py` is in RC-54's Files.
- Options:
  - (a) Drop the twins test and keep the key.
  - (b) Build twins, which revives a dead-listed item and widens the key.
- **Recommend (a),** unless he revives twins. The plan reversed a ratified dead-list item without citing it.

### RC-55, move risk in place

**Fact 1.** `unit.py:990-991` is now `_cold_reason`, `qml/protocol/unit.py:2252-2258` at the tip. It still judges one compiled fingerprint, and that is exactly what this row changes.

**Fact 2.** `runtime.py:2098` is now `self._compiler = ThreadPoolExecutor(max_workers=1, thread_name_prefix="node-compile")`, at `runtime.py:2424`.

- Intent: AD-6 (agent) and the code agree. **MECHANICAL.** Corrected Read line: "AD-3, AD-6, AD-12; `_cold_reason` in `qml/protocol/unit.py`; the node's one compile worker `Runtime._compiler` (thread `node-compile`) in `qmn/app/runtime.py`."
- Blast radius: rc-22, 26, 28, 33 and 34 all move `_cold_reason`, so symbols are the only stable anchor. rc-26 ("open trades keep their numbers") must have stacked first: `move_risk` keeps positions whose exits read `numbers_at_entry`.

### RC-56, stages

**Fact 1: lift `stages` and `stage_values`; the guide and schema files are missing.**
- Refusals at `compiler.py:1235-1240` (`stages_not_built`) and `:1393-1398` (`stage_values_not_built`).
- **MECHANICAL.** Add the shared-fact-2 list; `test_unit_refuses.py`, `sections.py` and `compiler.py` are already in Files. The format bumps.

Finding F2 (stacked code). There are two homes for per-stage values: `StageRow.numbers` (`model.py:552`) and `NumberSpec.stage_values` (`model.py:505`, added by rc-23). `sections.py` reads only the first (`_staged`, `sections.py:219-224`).
- AD-2 (agent) says "a `stages` selector with any exit in its `stage_values` is logic". RC-03's test proves that only through stage rows (`test_unit_sections.py:86`). An exit number carrying `stage_values` under a risk-fact selector leaves `stages` in the risk half, so a risk edit to the threshold or hysteresis moves which exit value is in force with no logic re-proof. That is exactly RC-56's blast-radius fact. It cannot be reached today only because `stage_values` is refused.
- Add to Build: "`stages` is logic when any number the logic half binds has a non-empty `stage_values`." Add to Verify, unit: "`test_an_exit_stage_value_on_the_number_makes_stages_logic`. `target_r` with `stage_values` and the selector `account.equity` puts `stages` in the logic half."

### RC-58, readings bus

**Fact 1: the `sections.py:57` fix lands here.**
- `logic_inputs = _input_values(document.get("logic"))` at `sections.py:57` ignores `exit_set`. AD-2 (agent) says a `reads` row read by logic is logic, and exits are logic.
- **MECHANICAL.** Files: add "Edit `qml/src/qml/unit/sections.py`" and "Edit `qml/tests/test_unit_sections.py`". Build: "Collect `_input_values(document.get('exit_set'))` with the logic inputs." Verify, unit: "`test_a_read_an_exit_names_is_logic`."

**Fact 2: the board pointer.**
- `runtime.py:367-369` is now the `BoardRead` docstring at `runtime.py:403-416`. The behaviour lives in `BoardFeed.read`, at `runtime.py:503-528`, which returns `fallback=admitted` (every market) when the board is empty or stale.
- Intent:
  - The code's own docstring cites "Level 0 AD-2" (an earlier unit-system agent architecture): trade every market on its own conditions.
  - The plan (AD-16, agent) reverses that on purpose: fall back to home markets.
  - Owner: on 3 Nov he pasted an agent note that "If the board is stale or missing, the unit trades all its markets on its own rules". He stated no ruling.
- The pointer is **MECHANICAL.** Corrected Read line: "`BoardRead` and `BoardFeed.read` in `qmn/app/runtime.py`."
- **D6, a sub-gap.** `home_markets` defaults to empty (`model.py`, `Unit.home_markets = ()`). With the planned fallback, a unit that declares no home markets stands aside on every market when the board dies. A unit with no placement read is unaffected.
  - Options:
    - (a) Empty home means stand aside. That is safe, but a placement unit stops on any board outage.
    - (b) Empty home means every market, which keeps the fault for undeclared units.
    - (c) Promote refuses a deployment with a placement read whose unit declares no `home_markets`.
  - **Recommend (c).** It makes the choice explicit where the deployment is made. Cost: one refusal code and one line in `promote.py`.

**Fact 3: `reads`, `home_markets` and `context_needs` lift, and `Read` has no publisher yet.**
- Refusals at `compiler.py:1195-1196`, `:1253-1258` and `:1203-1209`. `Read` is at `model.py:429`.
- `READING_SOURCES` is closed at `{"unit", "node", "mis"}` (`journal_kinds/unit.py`). AD-16's `app:<id>` and `agent:<id>` need a family pattern beside it. That file is already in Files.
- **MECHANICAL.** Add the shared-fact-2 list, and to Build: "Widen `READING_SOURCES` with an `app:` and `agent:` family pattern."

### RC-63, both motion arms

**Fact 1: QMB already reports a motion-off arm.**
- Code: `qmx-agents/apps/qmb/jobs/backtest.py:6-7,62,259-270` runs the unit twice "with `motion = both`", writes `journal/motion_off/…`, and reports `motion_off`. The test is `qmb/tests/test_run_journal.py:428-444`. It came from the unit build (`49d9625dd`) and is opt-in per request (`"motion": asked.get("motion", "on")`).
- Plan: "`MotionSwitch` reports **every** run with and without motion" (AD-14, FUNNEL R8, agent).
- The two intents agree on reporting both arms. They differ on **every run** (plan) against **opt-in** (code).
- Blast radius:
  - Making it every run doubles every backtest's wall time. That hits the judge's G, RC-52's group replay and RC-65's re-test of 200 units (OPEN 13).
  - rc-28 (in flight) edits the same `engine.py` and `journal.py`, and rc-33 edits `journal.py`, so "could start now" collides with them.
- Options:
  - (a) Keep opt-in. The row adds only arm id, link id and parent stamps, plus the reserved `proposal` row. Rewrite the test: "`test_both_arms_carry_their_stamps`. A `motion = both` run's two records read arm ids `motion_on` and `motion_off`, one shared link id and the parent run id", which fails at the parent.
  - (b) Default to `both`. Cost: double wall time everywhere.
- **Recommend (a).** The proposal-row reservation stays. It is the lead's 7 Nov trim (agent), and harmless.

### RC-64, forwarding a swapped placeholder

**Fact 1: templates bind `@2`, not `@1`.**
- `canary.json:81` and `dummy-trend-pullback.json:80` bind `fixed-fraction-at-stop@2`. `@3` exists only on `build/rc-28`. All three versions take one parameter, `fraction`. `@1` answers lots; `@2` and `@3` answer money. The engine fixture `b-build-and-prove/fixtures/recorded/build.json:248` still binds `@1`.
- Intent: retire the stand-in without losing the record (agent). The plan wrote `@1` before RC-06 created `@2`.
- **MECHANICAL.** Corrected Build text: "Declare `fixed-fraction-at-stop@2 -> @3` (fraction unchanged) and `@1 -> @3` (fraction unchanged, the old answer read as lots), and point both shipped templates at `@3`."
- Note: `@3` is still `origin: placeholder`, so "swap a placeholder" is a version forward, not the end of the placeholder.

**Fact 2: `classify` has no caller, and `diff.py` and the judge are missing from Files.**
- `classify` is at `qml/identity/diff.py:302-315`. `diff` labels any version change of one entry `block_fix`. The default table makes `block_fix` a new version and a counted try (`qmx_control/service.py:429-445`). The judge counts tries in `qmx-agents/packages/qmx-judge/src/qmx_judge/landing.py:451,518`.
- **MECHANICAL.** Files: add "Edit `qml/src/qml/identity/diff.py`" (a declared forward is not a `block_fix`) and "Edit `qmx-agents/packages/qmx-judge/src/qmx_judge/landing.py`".
- Blast radius: RC-54 adds the identity table's section column and RC-63 asserts that effective tries are unchanged, so land RC-64 after both and rerun the judge's tries tests.

### RC-65, re-test after a bump

**Fact 1: the format numbers are stale.**
- **MECHANICAL.** Corrected test line: "`test_a_bump_with_no_report_is_refused`. A unit recorded at `COMPILER_FORMAT_VERSION` and a node running that value plus one answers `retest_missing`."
- BACKLOG line 17's "needs the script fixed first" is stale. The pack's golden step was repaired by RC-11 (PR 364). The remaining risk is rc-31's QMB child hanging after the last write (PR 369). Add to Build: "Regenerate the judge's conformance pack through the re-test, under a time limit."
- Blast radius: once RC-65 stands, RC-68 and RC-69's format bumps need a re-test report for every deployed fixture unit. OPEN 13's wall time is an agent default.

### RC-68, partial close and trail

**Fact 1.** `runtime.py:1807-1808` is now `runtime.py:2114-2115`: `case ClosePartial(): return Blocked("the venue cannot close part of a position")`. Note that this text files as `health_stop` (F3). `AmendProtection` already routes to `_amend`, which only tightens (`runtime.py:2116-2118,2125`).

**Fact 2: the six-exit-stack test moves here.**
- The refusal is at `compiler.py:410-420` ("it reads the position, and a stop is read before…"). rc-12 shipped the substitute `test_six_exits_on_one_unit_are_each_run_or_named` (`qml/tests/test_exit_blocks_v2.py:228`), which asserts the refusal and so turns red when this row lifts it.
- **MECHANICAL.** Corrected text:
  - Build: "Close with a quantity in the `ClosePartial` case of the node's exit path in `qmn/app/runtime.py`."
  - Files: add "Edit `qml/tests/test_exit_blocks_v2.py`".
  - Verify, unit, add: "`test_six_exits_compile_on_one_unit`. All six exits of rc-12's stack compile, replacing `test_six_exits_on_one_unit_are_each_run_or_named`."

### RC-69, venue targets and netting

**Fact 1: `_netted` is live-only and text-only.**
- Code: `_netted`, at `runtime.py:3394-3412` and present at root, refuses only when `deployment.lane == "live"` and the venue nets. It sets `Phase.REFUSED` with text (`:3284-3286`). Non-market entries are blocked at `runtime.py:1247-1248`.
- Intent:
  - Code (node build): netting is a venue fact, and the paper lane fills virtually per unit, so paper cannot net.
  - Plan (S18, agent): "two units on one netting symbol stay refused until attribution exists". It does not name a lane.
  - "Every lane" is the staleness auditor's reading, not the plan's words.
- Blast radius: refusing on paper blocks multi-unit paper trials on a netting account. Those are RC-52's and the fleet's evidence. Leaving paper open means paper shows two units trading a symbol that live would refuse.
- Options:
  - (a) Keep live-only, give the refusal the code `netting_not_attributed`, and have the paper lane write a `would_have` row saying live would refuse.
  - (b) Refuse on every lane.
- **Recommend (a).** Corrected test text: "`test_two_units_on_one_netting_symbol_refuse`. On a netting live account the second deployment answers `netting_not_attributed`; on paper it deploys and writes a `would_have` row with that code."

## Stacked code against its own intent (findings, not fixes)

- **F1** (RC-03, BACKLOG line 70, known). `sections.py:57` misses `exit_set` reads. It cannot be reached today because `reads_not_built` refuses them. RC-58 carries the fix.
- **F2** (RC-03 with rc-23, new). `sections.py` `_staged` ignores `NumberSpec.stage_values`, so the AD-2 rule RC-03 proved holds only for stage rows. It cannot be reached today because `stage_values_not_built` refuses it. RC-56 carries the fix.
- **F3** (node and QMB, new and low). `_REASON_WORDS` maps "venue cannot" to `health_stop` (`qmb/results/journal.py:87`). The node writes capability refusals in those words ("the venue cannot close part of a position", "the venue cannot take a {kind} entry", `runtime.py:2115,1248`). So capability gaps read as health stops, not as their own code or `unlisted`. RC-68 and RC-69 remove two of these texts.
- **F4** (rc-22, in flight). The cushion ledger reaches every modifier as unscoped `cushion.<clock>.*` in R, while WALKS 12 wants a group-scope cushion read the same way. This is not wrong for rc-22's own unit scope. It forces a `cushion-rule@2` at RC-50 (D1).

## Where the agent overruled or misread the owner

- **What a pod is.** The agent split his "pod" into a recipe (built as "pod") and a thin group (his "book"). It is building RC-53 to RC-55 on that split before telling him, even though he asked to be walked through overhauls. His mini-app sense of pod is not built anywhere in RC-49 to RC-57.
- **Book and BMS.** He called Book/BMS "the skeleton to enhance and rebuild" and wanted the BMS to reopen slots as capital allows. The spine retires both Library kinds into the group, and slot reallocation becomes an off-path reading. The mapping is defensible, but he has never ruled on it.
- **Paper twins.** RC-54 builds paper twins, which his ratified corpus lists as dead (ADR-0009, ADR-0022). The plan does not cite that.
- **Stop points.** The three stop points, and "RC-49 to RC-69 are opt-in", are agent defaults he has never confirmed. His "stop at stage B" on 3 Nov was about a planning stage.

## Decisions for the owner, in plain English

1. **D-rc29. The daily account brake (rc-29).** It has one known hole: if the PC is off over midnight, the next day's loss brake stays off. The fix is about 9 lines, but the rules allowed only two fix rounds. Stop point B needs it. Recommended: say "fix rc-29 a third time".
2. **D2. What a "pod" is.** The build made a pod a saved sizing recipe stamped into units, and put your "book" idea into a "group" that can only cut risk. You described a pod as like a hedge-fund book, and said pods should be mini apps. Recommended: look at this before RC-53, because RC-53 to RC-55 are the rows thrown away if you choose otherwise.
3. **D1. Units for the group's house-money ledger.** Recommended: the group's house-money figure counts in R, like each unit's, and the group's daily loss counts in dollars. This needs one new version of the house-money block.
4. **D3. Does tagging a unit force it to be re-tested?** Today a tag counts as a change to the trading logic, so tagging 200 units re-tests 200 units. Recommended: treat a tag as a risk change, which needs your one click but no re-test.
5. **D4. A unit in two groups.** When a unit's own rules ask for "the group's limit", which group answers? Recommended: the group named when you deployed it. Both groups' caps still apply.
6. **D5. Paper twins.** The plan lets one unit run twice side by side. Your August decisions list that as dead. Recommended: don't build twins. Drop that one test.
7. **D6. A unit with no home markets when the market board goes dead.** Recommended: refuse to deploy a unit that uses the board unless it names its home markets.
8. **D7. Reporting "with and without learning" (RC-63).** Doing it on every backtest doubles test time. Recommended: keep it as an option you switch on, and only add the labels.
9. **D8. Two units on one symbol on a netting account (RC-69).** Recommended: refuse it in live trading only. Paper still runs, but writes a note that live would have refused it.
