# Plan intent audit A, 12 November: RC-22 to RC-46

Read-only. Covers every UPDATE section in `PLAN-STALENESS-2026-11-12.md` from RC-22 to RC-46, and the report's six "facts that apply to many sections" where they touch these sections. Code is read at the stack tip `8d0a9758` and at the in-flight heads rc-22 `1b09f81c`, rc-26 `908ed68f`, rc-28 `0b1ad1eb`, rc-29 `72bbee12`, rc-33 `34fb9d99`, rc-34 `5b0a5684`. Nothing was edited, checked out or run beyond `git show` and `git grep`.

**How intent is weighed (the owner's rule of 12 November).** Only his own words count as owner intent. Every rule in `SPINE.md`, `FIXES.md`, `OPEN.md` and `PLAN.md` was written by the lead agent or a subagent, so each is marked "agent decision" and judged on its merits and blast radius. His words come from the planning transcript's user turns (`2928e6ee...jsonl`) and from the verbatim registers `tracker/risk-core/seeds/operator-words-*.md`, `seeds/SEEDS.md` and `round-2/SEEDS-2.md` (M numbers are his message numbers there). On the topics in these sections he said very little directly. He handed the technical lens over: "For the technical part, I don't think you really need me" (3 Nov), and on 7 Nov "How it configures itself. I'll leave that part to you. Breaks and accelerators... I'll prefer you as agents to handle this part" and "Just complete it and make sure it can work. And it's maintainable, please."

Counts: 55 stale facts (the audit's 52 plus 3 found here). 43 MECHANICAL, 12 DESIGN CALL, which make 11 distinct decisions (RC-22 fact 3 and RC-41 fact 3 are one). Six findings about built code and four about agent decisions that override or misread his words.

## Summary

| Section | # | Stale fact | Verdict |
|---|---|---|---|
| RC-22 | 1 | Needs a join to `8d0a9758`; count pins 131 must read 132 | MECHANICAL |
| RC-22 | 2 | New reader of `trade.r_after_costs`, which rc-28 renames | MECHANICAL (rename to `net_r`, not `gross_r`) |
| RC-22 | 3 | `enabled` read by the runtime, but no document can write it | DESIGN CALL (with RC-41 fact 3) |
| RC-26 | 1 | `PositionFacts.numbers_at_entry` already exists | MECHANICAL |
| RC-26 | 2 | `_OwnJournal` is at `runtime.py:1674` | MECHANICAL |
| RC-26 | 3 | Root flat rule at `unit.py:543` is gone; positions are a tuple per market | MECHANICAL |
| RC-26 | 4 | Test literal 0.98 lots should be 0.88 | MECHANICAL |
| RC-26 | 5 | Base lacks rc-25's last two commits; new writer `r_after_costs=Decimal(r)` must follow rc-28 | DESIGN CALL (what the restart seed puts in `net_r`) |
| RC-28 | 1 | `engine.py:57,120` are now `:62,156` | MECHANICAL |
| RC-28 | 2 | Base lacks rc-25's last two commits | MECHANICAL |
| RC-28 | 3 | Count pins 131 against the tip's 130 | MECHANICAL |
| RC-28 | 4 | "Every reader moves" fails for whichever of rc-22, rc-26 lands later | MECHANICAL |
| RC-28 | 5 | Departures: node `net_r` equals gross; cells keyed market, venue, hour | DESIGN CALL |
| RC-29 | 1 | Branch three rows behind, format 11 | MECHANICAL |
| RC-29 | 2 | Files block names 4 files; the row needed 15 | MECHANICAL |
| RC-29 | 3 | `functions.py` shared with RC-47, 52, 54, 59, 62 | MECHANICAL |
| RC-33 | 1 | Needs a third join; receipt pin and pack re-read | MECHANICAL |
| RC-33 | 2 | `stop_buffer` literals are fractions 0.0002 and 0.0030 | MECHANICAL |
| RC-33 | 3 | (new) Session hours read the session's own zone, not the record's | MECHANICAL |
| RC-34 | 1 | Count pins 129 against 130 | MECHANICAL |
| RC-34 | 2 | `compiler.py:896-1014` is now `_shape_problems`; role refusal is `role_not_built` at `:538` | MECHANICAL |
| RC-34 | 3 | `derivation` and combiner `product`/`min` not built, owned by no section | DESIGN CALL |
| RC-34 | 4 | No stdlib block reads `bars_since` | MECHANICAL |
| RC-35 | 1 | `gates` refused at `compiler.py:1225`; lifting moves generated files | MECHANICAL |
| RC-35 | 2 | Two new stdlib blocks move the count pins | MECHANICAL |
| RC-35 | 3 | `net_edge_below_zero` must join the closed lists | MECHANICAL |
| RC-35 | 4 | `Verdict` is taken (`qml/check/result.py:102`) | MECHANICAL |
| RC-35 | 5 | The cell is `market.cost_cell:<market>`, no session or world, node at default N | MECHANICAL |
| RC-35 | 6 | An admit seam, a factor chain and rc-22's `flag` word already exist | DESIGN CALL |
| RC-36 | 1 | `tolerations` refused at `compiler.py:1229-1232` | MECHANICAL |
| RC-36 | 2 | `sticker:news` is no code and no family | DESIGN CALL |
| RC-36 | 3 | Nothing writes `Kind.SPEC_CHANGE` yet | MECHANICAL |
| RC-39 | 1 | Rig base bar 900 s; a 60-bars-an-hour scalper cannot host on it | MECHANICAL |
| RC-39 | 2 | Five new stdlib blocks move the count pins | MECHANICAL |
| RC-39 | 3 | "Reaches paper" ends on the fake broker | DESIGN CALL |
| RC-40 | 1 | `AdmitPort` already exists with another signature | DESIGN CALL |
| RC-40 | 2 | `runtime.py:1100-1106` is `:1291`; `2623-2675` is `:3079` | MECHANICAL |
| RC-40 | 3 | Price call at `unit_handler.py:910`; hook at `api.py:280,302` | MECHANICAL |
| RC-41 | 1 | Protection constants at `runtime.py:200-208` | MECHANICAL |
| RC-41 | 2 | Margin headroom and liquidation distance always read absent | DESIGN CALL |
| RC-41 | 3 | `enabled: false` cannot be written in a document | DESIGN CALL (with RC-22 fact 3) |
| RC-41 | 4 | `kill_effect`, `past_liquidation` must join the closed lists | MECHANICAL |
| RC-41 | 5 | (new) The node already refuses entries at YELLOW and above, so the red test cannot go red | DESIGN CALL |
| RC-42 | 1 | `mint_intents` at `runtime.py:2031`; price call at `unit_handler.py:910` | MECHANICAL |
| RC-42 | 2 | `_drive` at `runtime.py:3616` | MECHANICAL |
| RC-43 | 1 | `own_position` read at `unit.py:1370`, a tuple; limit is rc-32's count | MECHANICAL |
| RC-43 | 2 | `runtime.py:1705-1713` is `:2010`; unknown refusal is `:1251` | MECHANICAL |
| RC-43 | 3 | `_orders` is `dict[str, Placed | Blocked]` at `:1780`; `execute_resting` at `:1999` | MECHANICAL |
| RC-43 | 4 | `budget_expired` must join the closed lists | MECHANICAL |
| RC-44 | 1 | Constants at `:200-208`; `watch.began` at `:2518` | MECHANICAL |
| RC-44 | 2 | `budget_impossible` must join the closed lists | MECHANICAL |
| RC-45 | 1 | The sizer row has no `basis` field | DESIGN CALL |
| RC-45 | 2 | `convert.py:197-198` skips `tail_budget` by name | MECHANICAL |
| RC-45 | 3 | `stop_not_built` at `compiler.py:601-606` | MECHANICAL |
| RC-46 | 1 | `_restore_stops` at `runtime.py:2809` (and every other AD-22 line) | MECHANICAL |

## Facts that apply to many sections, as they touch RC-22 to RC-46

1. **Compiler format.** Tip 12; rc-33 13; rc-34 14; parked rc-29 11. In my range the rows that change a compiled decision are RC-35 (`gates`), RC-36 (`tolerations`) and RC-45 (`stop_not_built` lifted). rc-22, rc-26 and rc-28 keep 12 by their own PR bodies. Intent on both sides is AD-19 (agent decision): "bump only on a changed decision". MECHANICAL. Every brief should say "bump to the parent's format plus one, read from `compiler.py:115` at the parent", never a literal, because the landing order of the in-flight rows is not fixed.
2. **Generated files outside the Files blocks.** Applies to RC-35 (`gates`), RC-36 (`tolerations`), RC-45 (a compile refusal lifted, and a document field if DESIGN CALL 9 picks the row field) and to RC-41 if `enabled` becomes a document field. MECHANICAL. Add to each of those Files blocks: `tools/qml/extending.py`, `qml/EXTENDING.md`, `qml/tests/test_unit_refuses.py`, `qml/src/qml/unit/qmx.unit.1.schema.json`, `qmx-agents/packages/qmx-library/src/qmx_library/kinds/unit.schema.json`, `qml/tests/test_receipt.py`, and `qmx-agents/packages/qmx-judge/src/qmx_judge/conformance_pack/{pack,golden,fixture}.json`.
3. **Count pins.** RC-35 adds 2 stdlib blocks, RC-39 adds 5, rc-22 adds 2, rc-28 adds 1. MECHANICAL. Add `qml/tests/test_nothing_silent.py` and `qmx-agents/packages/qmx-host/tests/test_dictionary_full_size.py` to those Files blocks, with "read the count at the parent and add this row's blocks", never a literal. The in-flight literals (131, 129) are each wrong against the tip's 130.
4. **Closed reason lists.** MECHANICAL, with one correction. Two codes the plan invents already have a word in the closed list at `packages/qmf-data/src/qmf/data/journal_kinds/unit.py:48`: `kill_switch` (filed today for "kill switch", "paused at", "withdrawn" by `qmb/src/qmb/results/journal.py:80-82`) and `margin`. The old spread rule's refusal is `spread_wide`, and a record change's pause is `spec_change_pause`. Reusing them keeps old and new journal rows on one code. New codes in my range: `net_edge_below_zero`, `past_liquidation`, `budget_expired`, `budget_impossible`, the sticker family (DESIGN CALL 5) and nothing else. The node's `Blocked` text also needs its words in `_REASON_WORDS` (`qmb/src/qmb/results/journal.py:69`), or the row files as `unlisted`.
5. **`runtime.py` line numbers.** All root numbers in my range are wrong. The current ones are in each row below. MECHANICAL. Better still, briefs should cite function names, which survive joins.
6. **Fact names.** `market.<name>:<market>`, and on rc-28 `market.cost_cell:<market>`, `market.gap_factor:<market>`, `market.funding:<market>`. MECHANICAL for RC-35.

## Detail

### RC-22, house money (PR 382, in flight)

**Fact 1. Join and pins.** Plan: none stated. Code: branch at `74c1e7ba`; its pins read 131 (`test_nothing_silent.py`) and 474 pages, 131 versions. The tip adds `own-r-step@1` (130). Intent on both sides: pins count real stdlib entries. Blast radius: the two pin files only. **MECHANICAL.** Brief text: "Join `8d0a9758`. After the join the pins read 132 faces, 475 pages and 132 versions, read from the joined tree, not copied."

**Fact 2. `trade.r_after_costs` reader.** Plan: "The ledger presses on realised winnings only." Code: rc-22 `qml/src/qml/protocol/unit.py:1680` folds `"r": trade.r_after_costs`; the PR names it "one closed trade's R after costs". rc-28 renames that field `gross_r` and adds `net_r` (rc-28 `qml/src/qml/motion/engine.py:62,65`).
- Plan intent (agent decision): the repair handoff's section 2 (`tracker/risk-core/handoff/FOR-REPAIR-SOCKET.md:26`): "Brakes, the money ledger, the CUSUM and the admission gate read `net_r`". AD-11 calls the cushion "one cushion ledger". The CHECK fix of 6 Nov 15:42 (transcript) says `r_after_costs` "keeps its value and becomes `gross_r`" because it holds gross.
- Code intent: the builder meant net ("R after costs") and got gross, because the old field's name lies (SPINE E13: "`r_after_costs` holds no costs").
- His words: "I don't think I want to lose the house of money" (M5, SEEDS-2 H-54), "reverse House of Money was my idea" (M39, H-55). He did not speak to gross or net.
- Blast radius: rc-22's fixtures carry no cash, so `net_r` equals gross there and no literal moves. On the node, rc-28 makes `net_r` equal gross anyway (DESIGN CALL 3). The fold's cache keys rows by id, so the field change does not touch stored caches.
- **MECHANICAL, with a trap.** Both intents want winnings after costs. A plain rename to `gross_r`, the obvious join fix, would make the house money press on gross winnings that commission has already eaten. Brief text: "Whichever of rc-22 and rc-28 joins second changes `realise` to fold `trade.net_r`, not `gross_r`. The money ledger reads net (repair handoff section 2)."

**Fact 3. `enabled` has no document field.** See DESIGN CALL 1 below (shared with RC-41 fact 3).

**Also found, not a stale fact.** PR 382 states that AD-18's "a raise earned before the restart waits for the next anchor" is not built, and no remaining section owns it. That rule is an agent decision. A restart gives the same factor as a cold fold, which is what RC-22's own blast-radius fact asks for. File it in BACKLOG for the numbers talk. Do not add it to a section.

### RC-26, open trades keep their numbers (PR 386, in flight)

**Fact 1.** Plan Build box 1: "Add `numbers_at_entry` to `PositionFacts`". Code: `qml/src/qml/protocol/exits.py:106` already has it, written by RC-25 and read by nothing (PR 386 departure 1). Intent: same on both sides. Blast radius: none. **MECHANICAL.** Text: "Read `PositionFacts.numbers_at_entry` (RC-25, `exits.py:106`) in the exits pass. Fill it at entry where RC-25 does not."

**Fact 2.** `_OwnJournal` is at `runtime.py:1674`. **MECHANICAL.** Text: "Seed `_OwnJournal` (`runtime.py`, class `_OwnJournal`) at `NodeUnit.start`."

**Fact 3.** Plan: "Read a logic number's flat rule per market at `unit.py:543`." Code: the line is gone, and positions are a tuple per market since rc-32 (`unit.py:12`). PR 386 reads AD-14 step 5 ("read per market, not across all markets... so a many-market scalper can't starve its cadence") as "a logic number moves on a step where some market is flat". The two intents agree: don't starve the cadence. **MECHANICAL.** Text: "A logic number keeps the flat rule, read as 'at least one market holds nothing'. A sizing, exit or control number moves with positions open."

**Fact 4.** Plan: "the next entry is 0.98 lots". Code: 0.88. The plan assumed equity 100,000 at that entry. The node sizes on balance plus the unit's realised money, and 20 gold losses realise -9,450 (PR 386). Intent on both sides: size on the account as it stands (AD-15, and RC-27's "Sizing reads your real account as it stands"). **MECHANICAL.** Text: "the next entry is 0.88 lots (0.0049 of 90,550 at 500 a lot, floored), and the row shows `realised_since` -9450".

**Fact 5. Base and the rc-28 rename.** Code: rc-26 `qmn/src/qmn/app/runtime.py:2422` builds `ClosedTrade(..., r_after_costs=Decimal(r), ...)` from the trade row's `position_r`, which rc-26 adds (`qmb/src/qmb/results/journal.py:571-572`). After rc-28, `ClosedTrade` requires both `gross_r` and `net_r`, with no default (rc-28 `engine.py:62-65`). rc-28's trade row carries a per-close `net_r`, not a whole-position one.
- Intent: AD-14 step 6 (agent decision): "a restart mid-count ends in the same move". The repair handoff: brakes read `net_r`. rc-28 `qml/src/qml/protocol/controls.py:197-210` makes the loss streak, losing-day streak and session loss read `net_r` from `own_journal`, the same list rc-26 seeds.
- Blast radius: after a node restart, every seeded trade's `net_r` feeds the brakes. If the seed copies gross into `net_r`, brakes after a restart read gross while brakes before it read net. Today they are equal on the node (rc-28 departure), so nothing moves now. It moves the day the node gets a cash port (DESIGN CALL 3). The `trade` row kind lives in `qmf-data` (`journal_kinds/unit.py`), whose decimal fields are listed (rc-28 `:209`).
- **DESIGN CALL 2.** Options:
  - (a) The trade row gains `position_net_r` beside `position_r`, and the seed fills `gross_r` from one and `net_r` from the other. A row without it (written before the join) seeds `net_r` equal to gross and says so in the row's basis. Cost: one field in the row writer and the `qmf-data` kind.
  - (b) Seed `net_r` equal to gross always. Cost: none now. It is silently wrong once node cash lands, against the restart rule.
  - (c) Seed from the per-close `net_r` rows summed by position. Cost: the seed must join partial closes. More code, same answer as (a).
  - **Recommend (a).** It keeps "restart is no reset" (AD-18) true for brakes, at the price of one field.
  The rename itself is mechanical: whichever of rc-26 and rc-28 joins second spells the constructor with both fields.

### RC-28, costs from fills (PR 385, in flight)

**Fact 1.** `engine.py:57,120` are now `qml/src/qml/motion/engine.py:62,156`. **MECHANICAL.**

**Fact 2.** The branch sits on `266f34e4` without rc-25's `5187ea89` and `8d0a9758`, which touch `test_number_moves.py`, `test_unit_handler.py` and `unit.py`. **MECHANICAL:** join the tip.

**Fact 3.** Pins 131 against 130. **MECHANICAL:** after the join, the tip's 130 plus one equals 131, which is right only if rc-22 has not landed first. Read the pins at the joined tree.

**Fact 4.** The review fact "every reader of `r_after_costs` moves in this PR" (PLAN.md line 2023). Code: true at rc-28's head (PR 385: 0 hits), false once rc-22 or rc-26 joins. Intent: no reader is left on the lying name. **MECHANICAL.** Text: "Every reader of `r_after_costs` moves, re-run by `git grep -nw r_after_costs` at each join of rc-22, rc-26 and rc-28. A money-ledger or brake reader moves to `net_r`, a logic-record or motion reader to `gross_r`."

**Fact 5 (departures that change later sections).** Code: cells key by market, venue and UTC hour (rc-28 `qmb/src/qmb/host/facts.py`). There is no session (sessions compile only from RC-33) and no world (one handler serves one world). `qmn/app/runtime.py` starts the handler with no `costs` and no cash port, so node cells calibrate at the default `cell_min_fills` 50, and node `net_r` equals gross.
- Plan intent (agent decision): AD-15: "cost cells per instrument, broker, hour, session and world".
- His words: "if you are trading, let's say, in a given market for a given instrument at a given time frame, we need to know what are the fees, what are the costs, so that the unit can know" (M7, `seeds/SEEDS.md` A11). He named market, instrument, timeframe and time. He did not name session or world. The spine dropped his "time frame".
- Blast radius: RC-35's hurdle reads the cell (fact 5 there). The brakes read `net_r` (rc-28 `controls.py:197-210`), and so does rc-22's cushion (RC-22 fact 2). RC-64's `@2 -> @3` forwarding reads `@3`. The node is where money is real, and there, brakes and house money see no commission.
- **DESIGN CALL 3.** Options:
  - (a) Accept the departures as built. The node's `net_r` stays gross until the demo lane proves deal money (R24). Cost: until then node brakes are blind to commission, which is about 7 USD a lot per side on the canary's own fixture, a 1.4 % R bias at 500 USD risk.
  - (b) Give the node handler a cash port fed from the instrument record's stated `commission_per_lot` per fill, which the node's cells already use, labelled as stated, not measured. Cost: one port in `runtime.py` and a known-answer test. It belongs in RC-35, whose Files block already edits the price path, or in a small row before it.
  - (c) Also add session to the cell key once RC-33 lands. Cost: a key change and a cell migration. His words do not ask for session. A timeframe's scale already enters the hurdle through the stop distance it divides by.
  - **Recommend (b), and not (c).** (b) is the smallest change that makes "costs so the unit can know" true where money is real. (c) is an agent addition with no owner basis.

### RC-29, feasibility and two-unit brakes (PR 380, parked)

**Fact 1.** At `a477f907`, format 11. **MECHANICAL:** join at unpark.

**Fact 2.** The Files block names 4 files; PR 380 needed 15, including `qmn/src/qmn/app/runtime.py`, `packages/qmf-data/src/qmf/data/journal_kinds/node.py` (a `day_start` kind) and `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`. Plan intent ("account-scope halts re-tested with two units") needs the node to supply `account.day_start_equity`, which no host did (PR 380). **MECHANICAL:** amend the block to PR 380's list.

**Fact 3.** `functions.py` is shared with RC-47, 52, 54, 59, 62. **MECHANICAL:** an ordering note ("lands before RC-47, or rejoins").

**Finding (built code, parked).** Its Opus review at `72bbee12` is NOT CLEAN on a money-path hole: on a day the node did not see begin, the account day brake stays off all day (`PARKED`). The measured fix is about 9 lines. The coordinator's rule allows two fix rounds, so it waits for his word (`QUESTIONS-FOR-OPERATOR.md`, 11 Nov 13:51). Stop point B depends on it through RC-48.

### RC-33, sessions (PR 381, in flight)

**Fact 1.** Needs a third join; `compiler.py` and `unit.py` moved under it. **MECHANICAL.**

**Fact 2.** Plan: "`stop_buffer` 2 on EURUSD and 30 on XAUUSD". Code: the dummy stores a fraction from 0 to 0.01 (PR 381). **MECHANICAL.** Text: "`stop_buffer` 0.0002 on EURUSD and 0.0030 on XAUUSD over a unit default of 0.0010".

**Fact 3 (new).** Plan: "`sessions` compiles with the record's clock"; test "London 08:00 to 16:00 in the record's zone"; lane 3 "session hours follow the record's zone". Code: a session reads its own `zone` (PR 381 departure), because the shipped FX and metal records are `America/New_York`, so a London session could not be written. Intent on both sides: hours follow the right clock across a daylight-saving change. The code serves that better than the plan, since London and New York change clocks on different dates. **MECHANICAL.** Text: "in the session's own zone, tied to a calendar the market's record holds (layer D)".

### RC-34, remaining logic roles (PR 384, in flight)

**Fact 1.** Pins 129 against 130. **MECHANICAL:** re-read after rc-33's join.

**Fact 2.** Plan Read: `compiler.py:896-1014`. Code: that range is now `_shape_problems`; the role refusal is `role_not_built` in `_Wiring.side`, `compiler.py:538`. **MECHANICAL.**

**Fact 3.** Plan: "`derivation` and `combiner` join, with `combiner` gaining `product` and `min`." Code: not built (PR 384). The builder's reasons: SPINE S12 itself says roles run "except `sizing_modifier` (AD-11) and `derivation` (AD-14)". `derivation` is RC-23's number field. A slot's combiner is boolean, where `product` and `min` both equal `all`. Model and combiner intent (agent decisions): S12 and E2 say "`derivation`, `combiner` added", while AD-11 says modifiers combine by "product, or a declared combiner; a `cap` row takes the lowest". So the plan's sentence mixes a logic-slot combiner (meaningless for booleans) with a modifier combiner (meaningful). Blast radius: the modifier chain (RC-21, rc-22's `flag` word) and the model. No later section in my range reads a `min` modifier combiner.
- **DESIGN CALL 4.** Options:
  - (a) Strike the sentence from RC-34. `derivation` is done by RC-23. A logic combiner gains nothing. Log "modifier combiner `min` / `cap` row" to BACKLOG for the first template that needs one.
  - (b) Build the modifier `min` combiner now, in RC-34 or RC-35. Cost: a model field and the fact-2 generated files, for no shipped user.
  - **Recommend (a).** Nothing he asked for and nothing shipped needs it.

**Fact 4.** No stdlib block reads `bars_since`, and `time-exit-bars` is refused in a slot. Plan intent: the dictionary's closing and filtering blocks stop being refused. That holds for any Library block. RC-39's five blocks do not need a cooldown. **MECHANICAL.** Note in the "You see" box: "no shipped cooldown or timeout block yet; the tests pin their own".

### RC-35, gate slot

**Fact 1.** `gates` refused at `compiler.py:1225`. **MECHANICAL:** add the fact-2 files and a format bump.

**Fact 2.** Two blocks move the pins. **MECHANICAL:** add the fact-3 files.

**Fact 3.** `net_edge_below_zero` joins `REASON_CODES` and `_REASON_WORDS`. `sqs-floor`, the old spread rule as a floor, should answer the existing `spread_wide`. **MECHANICAL.**

**Fact 4. `Verdict` is taken.** Code: `qml/src/qml/check/result.py:102` (`PASS`/`FAIL`, the G check). Plan and spine (agent decision): `Verdict` in `packages/qmf-risk/src/qmf/risk/chain.py`. The two live in different packages, but `qmf.risk` already exports `RequirementVerdict` and `ReconciliationVerdict`, and a bare `Verdict` would be ambiguous in grep and in any module importing both. **MECHANICAL.** Text: "Write `LinkVerdict` (link, verb, reason, code, inputs) in `qmf/risk/chain.py`." For the decision row's shape, see DESIGN CALL 6.

**Fact 5. The cell.** Read it as `market.cost_cell:<market>`, keyed market, venue and hour. It is `uncalibrated` below `[costs] cell_min_fills` (50). Tests that need a measured cell set that setting low or seed fills, as rc-28's own `test_a_cell_moves_off_uncalibrated_at_its_count` does. **MECHANICAL.** Whether the node's cell and `net_r` see commission is DESIGN CALL 3.

**Fact 6. Where the gate's verbs sit.** Plan: "`block` is the chain's `refuse`, `shrink` rewrites the quantity, `wait`..., `warn`, `shadow` and `none` pass with a row." Code: `HostedUnit.price` (`unit.py:1077`) runs sizer → modifiers (a factor product, RC-21, plus rc-22's `flag` word, which holds raises) → converter → `admit.admit(proposal, entry)` (`unit.py:1256`, default `SIZE_BAND`). It writes text verdicts into `DecisionRow.verdicts: tuple[str, ...]` (`unit.py:318`), such as `"size_band: refuse (code)"`.
- Plan intent (agent decision, AD-9): the gate slot is in the unit chain. `shrink` rewrites the wire quantity. The spine's row carries `verdicts: tuple[Verdict, ...]`.
- Code intent (RC-06, RC-21, rc-22): one door that sizes and writes the row. Modifiers scale money before the converter. rc-22's press gate is a modifier, not a gate slot, despite the name.
- Blast radius: `explain_size`, `replay_decision` and the receipt hash read the row's verdicts (`qml/tests/test_receipt.py` pins the hash). RC-40 widens `admit` behind the same call. RC-43 turns `wait` on. RC-36 adds sticker links to the same unit chain.
- **DESIGN CALL 6.** Options:
  - (a) Run the unit chain inside `price`, after the converter and before `admit`, on the quantity. `shrink` may only lower it, and it is re-checked by the size band. Keep the row's verdicts as text in the existing grammar `"<link>: <verb> (<code>)"`, rendered from `LinkVerdict`. Cost: none to stored rows or the receipt pin beyond the new links' lines.
  - (b) Run the gate as a modifier (pre-converter factor). Cost: `shrink` becomes a factor and `block` a factor of 0. That breaks the spine's verb set and makes `wait` impossible.
  - (c) Make the row's verdicts typed records. Cost: a row shape change, which moves `explain_size`, `replay_decision`, the receipt pin and the journal kind. No reader needs it before the copilot doors (RC-47).
  - **Recommend (a).** It fits beside both built chains, and only the text verdicts grow. Also tell the brief that rc-22's "press gate" is a modifier row and is not touched by the gate slot.

### RC-36, stickers

**Fact 1.** `tolerations` at `qml/src/qml/unit/model.py:599`, refused at `compiler.py:1229-1232`. **MECHANICAL:** fact-2 files and a format bump.

**Fact 2. `sticker:news` is no code.** Code: `REASON_CODES` is closed. `BLOCK_REASON_FAMILY = "block:"` with `BLOCK_CODE` regex (`journal_kinds/unit.py:91-96`) is the only open family. Plan intent (agent decision, AD-16): sticker kinds come from several sources (calendars, isolation, caution, apps, agents), and a pod may stamp tolerations. Blast radius: the journal kind's validator, QMB's `_REASON_WORDS`, and every reader that groups skips by code (fleet watch RC-62, the "why didn't it trade" UI hand-off).
- **DESIGN CALL 5.** Options:
  - (a) A declared family `STICKER_REASON_FAMILY = "sticker:"` with a regex, like `block:`. A new sticker kind costs no table row. Cost: one family constant, one regex, and the validator.
  - (b) One closed code `sticker` with the kind in the row's detail. Cost: readers lose the kind as a code.
  - (c) One closed code per kind (`sticker_news`...). Cost: a list edit per new kind, which AD-16's app and agent sources make open-ended.
  - **Recommend (a).** It is the pattern the journal already uses for open sets.

**Fact 3.** `Kind.SPEC_CHANGE` exists (`qmn/src/qmn/app/stand_down.py:93`); nothing in `qmn/src` writes it; `Runtime.stand_down` is at `runtime.py:3146`. **MECHANICAL.** Text: "Write the first writer of `Kind.SPEC_CHANGE`: on an instrument record change seen by the node, call `Runtime.stand_down(Kind.SPEC_CHANGE, instrument:<market>, cause)`. An entry it holds files under the existing code `spec_change_pause`."

**Finding (agent decision against his words).** He said: "on news days, we had the kill switch. The kill switch had a way of handling news, I recall. Both in the old system and the new system... unless I'm mistaken" (M10, `seeds/SEEDS.md` line 521). SEEDS lists "news is the kill switch's job" as point 26 of what the technical lens must hold. AD-16 rules "the kill switch is not a sticker" and moves news to stickers (funnel subagent `agent-a0073c21e8e996642`). The sticker design meets his want, "I wouldn't trade that instrument on its news day" (M51, H-40). But it moves news out of the part he trusts ("The kill switch has survived multiple versions", M5). He should hear it said plainly once. No code is wrong yet.

### RC-39, scalper and intraday templates

**Fact 1.** Plan test: `canary`, `scalper-mr` and `intraday-trend` host on one fake-broker account at 4, 60 and 4 bars an hour. Code: the node's own default base bar is 60 s (`[node] ctrader_bar_s`, `BAR_NS` in `qmn/src/qmn/venue/ctrader_account.py`, PR 366, OPEN row 23). Only the rig pins 900 s (`qmn/tests/test_app_binding.py:864`), because `play_spots` emits four spots per 15-minute bar. A stream must be a whole multiple of the base (`runtime.py:587-588`). Intent on both sides: one 60 s base serves the scalper and the 15-minute units (PR 366: "60 seconds is the fastest stream the templates read"). Blast radius: `bound_rig` serves many `qmn` tests, so changing its default would move them. **MECHANICAL.** Text: "`test_the_three_templates_share_one_account` builds its own rig at a 60 s base, with spots per minute, and leaves `bound_rig`'s 900 s pin alone."

**Fact 2.** Five blocks move the pins. **MECHANICAL** (fact 3).

**Fact 3. What "reaches paper" means.** Code: RC-19 took its fallback. K7 ends on the fake broker, and the Library's account kind admits only `demo` or `live` (PR 374, STACK-LIST row 20).
- His words: "paper trading is simply demo trading, unless I'm wrong... paper bloody trading is demo trading. So if something is able to trade with demo on a demo account for 2 months..." (M7, `seeds/operator-words-2026-11-01.md:81`). Also "He wants demo and live split so a unit trades identically" (lead's summary of his rulings, 3 Nov).
- Plan intent (agent decision): "paper" is a lane state the node runs, on a practice venue with no broker.
- Blast radius: K9 test 7, stop point B's claim "three templates... trade on paper from nothing", and RC-48's guide.
- **DESIGN CALL 7.** Options:
  - (a) Keep the test on the fake broker and change the wording to "reaches a filled entry on the fake broker". Stop B's "paper" claim then waits for G-DEMO. Cost: honest wording, no code.
  - (b) Build the practice venue's Library account world now (RC-19's missing part). Cost: Library core edits, and it still is not what he calls paper.
  - (c) Add a demo-lane check to K7 that runs after G-DEMO. Cost: one gated lane.
  - **Recommend (a) plus (c).** By his definition, only a demo-account fill is paper. Until his demo sign-in, the plan should not tell him a template "trades on paper".

### RC-40, one admit seam

**Fact 1. `AdmitPort` already exists.** Code: `qml/src/qml/protocol/unit.py:468`, `admit(proposal, entry: PricedEntry) -> str | None`. `SizeBand` is its only implementation (`:500-520`), the default of `price(..., admit=SIZE_BAND)` (`:1077`). No host passes its own (`qmb/src/qmb/host/unit_handler.py:910` calls `unit.price(one, account)`). Its docstring reads: "this one is what every host gets until the node chain lands."
- Plan intent (agent decision, AD-9 and SPINE section 3): `AdmitPort.admit(wire, at) -> Admitted | Refused`, in `qml/chain/node_chain.py`, the wire quantity rewritten on shrink. `price(proposal, facts, admit: AdmitPort)` was already the spine's call (SPINE line 372).
- Code intent (RC-06): the same seam, built early in the shape RC-06 needed.
- So the two are one seam at two stages, not a name collision. The spine's `(wire, at)` drops what the size band reads (`money_at_risk`, `equity`).
- Blast radius: `SizeBand`, `price`, `test_price_call`, `test_receipt` (the row's verdict text), RC-41's size-band link, and RC-35's unit chain, which runs just before it (DESIGN CALL 6).
- **DESIGN CALL 8.** Options:
  - (a) Widen in place. Move `AdmitPort` to `qml/chain/node_chain.py` and re-export it from `unit.py`. Signature: `admit(proposal, entry: PricedEntry, at: Instant) -> Admitted | Refused`. `Admitted` carries the possibly lowered quantity and the links' `LinkVerdict`s. `SizeBand` becomes the first link. Cost: one signature change and its callers.
  - (b) A second protocol under a new name (`NodeAdmit`). Cost: two seams after pricing, the double door AD-9 exists to prevent.
  - (c) The spine's `(wire, at)`. Cost: the size band loses `money_at_risk` and `equity`, or reparses them from the wire.
  - **Recommend (a).**

**Fact 2.** `cross_unit_hook` call at `runtime.py:1291` (in `execute`), `guard` at `runtime.py:3079`. **MECHANICAL.**

**Fact 3.** The price call is in `UnitSliceHandler._step` (`unit_handler.py:910`), not in `mint_intents` (`:862`). `CrossUnitHook` and `PASS_EVERY_ORDER` are at `qml/src/qml/blocks/api.py:280,302`. Deleting them touches files outside the block: `tools/qml/extending.py:29,263,351`, `qml/EXTENDING.md`, and `qmx-agents/packages/qmx-host/tests/test_node_trade_reaches_the_library.py:144,195` (it monkeypatches the runtime's `cross_unit_hook`). The `cross_unit_hook` reason code stays in `REASON_CODES` (`journal_kinds/unit.py:57`), because the list is "add, never redefine" and old rows carry it. **MECHANICAL.** Add those files to the block, with "the code stays listed for old rows".

### RC-41, kill effects on entries

**Fact 1.** Constants at `runtime.py:200-208` (`PROTECT_CONFIRM_NS`, `PROTECT_RETRY_MAX`, `CLOSE_REFUSALS_ALARM`). **MECHANICAL.**

**Fact 2. Margin and liquidation read absent.** Code: `packages/qmf-risk/src/qmf/risk/facts.py:159-160,177-178` define them. The binding reads only the balance. PR 361 departure 3: the pinned `ProtoOATrader` answer gives balance, leverage and a stop-out word, not free margin or a stop-out price, and "building a margin or liquidation model here would be inventing the numbers those facts exist to report."
- Plan intent (agent decision, AD-20 table): these vetoes are rows with `enabled`, and "off makes it a warning".
- Blast radius: the margin link, `test_a_stop_past_liquidation_refuses`, and any group cap reading margin later.
- **DESIGN CALL 9.** Options:
  - (a) Ship the links reading the facts as they are. An absent fact follows its fail mode (AD-15), stated as `neutral`: the row passes with verdict `warn` and the reason "margin unknown". The tests inject a fact surface that states the two numbers. The real source comes with the demo lane after G-DEMO. Cost: no venue code. Nothing refuses on an invented number.
  - (b) Compute both from the record's `margin` rates (`qml/src/qml/numbers/shipped_records.json:23,46`) and the account's leverage. Cost: a model PR 361 refused to invent, and it could refuse real trades on a wrong number.
  - (c) Probe the venue now. Cost: blocked on G-DEMO.
  - **Recommend (a).** It obeys AD-15's fail modes and his "exits are never blocked", and invents no money number.

**Fact 3. `enabled` cannot be written.** Code: rc-22 compiles `BoundBlock.enabled: bool | str` and `price` reads it (PR 382). The document cannot set it, because the schema generator's `OneOf` holds records only. PR 382 and BACKLOG name RC-41 or RC-53.
- Plan intent (agent decisions): AD-8 "a row may bind `enabled` to a fact, so a recipe can switch a modifier... for a whole pod through one group fact". AD-20: node-chain vetoes "one row each in the node chain, with `enabled`".
- These are two different rows. RC-41's vetoes are node-chain links in `qmn/app/node_links.py`, which are host settings, not the unit document. The unit document's `enabled` serves modifiers and control rows, and its first real writer is a pod recipe (RC-53).
- Blast radius of a document field: the model, both schema copies, `parse.py`, `schema.py`, the census and the guide (fact 2), plus a format bump. Of a node setting: `qmn/src/qmn/config/registry_catalog.py` only.
- **DESIGN CALL 1 (also RC-22 fact 3).** Options:
  - (a) RC-41's veto switches are node settings rows (`[node] margin_veto_enabled` and so on) in the registry catalog. The unit document's `enabled` field lands in RC-53, its first writer, with the schema's bool-or-text union. Cost: the RC-41 Files block gains the registry catalog and drops nothing. RC-53's block gains the model and schema files.
  - (b) Add the document field in RC-41. Cost: the whole fact-2 set and a format bump, in a node PR that has no document reader.
  - (c) Add it in RC-22 now. Cost: the same, in an in-flight row whose review is done.
  - **Recommend (a).** The node's vetoes are not unit rows, and the document field should arrive with the recipe that writes it.

**Fact 4.** `kill_effect` and `past_liquidation` must join the closed lists. **MECHANICAL, corrected:** use the existing `kill_switch` code for a kill-effect refusal, since it is already filed for the same words (`qmb/src/qmb/results/journal.py:80-82`). Use the existing `margin` code for the margin veto. Add only `past_liquidation`.

**Fact 5 (new). The node already refuses entries at a raised kill level.** Plan test: "At a level whose effect has `stop_entries`, an entry answers `refuse` with `kill_effect`... At the parent the entry places." Code: `Runtime.guard` (`runtime.py:3082-3084`) refuses every entry at YELLOW or above with "the kill switch is at ...", coded `kill_switch`. The placeholder table gives YELLOW and up `stop_entries: True` (`qmn/src/qmn/protection/effect_matrix.py:139-143`), and `_apply_kills` reads the table for closes only (`runtime.py:2967`). So at the parent, the test's entry is refused, and lane 2 cannot go red then green.
- Intent: the plan wants the table's effects to govern entries (AD-9, AD-20). The root code hard-wired the same answer by rank.
- Blast radius: `guard` moves behind the seam in RC-40. The owner-edited effect matrix (`ksa_effect_matrix` in `registry_catalog.py:314`, `readiness.py`) is never read by the runtime.
- **DESIGN CALL 10.** Options:
  - (a) The kill-effect link reads `stop_entries` from the effect table in force and replaces the rank check in `guard`. Red test: a table whose YELLOW row has `stop_entries: false` lets an entry through at the head and is refused at the parent. Code `kill_switch`. Cost: the red test changes shape.
  - (b) Keep the rank check and have the link only add `cancel_resting_entries`. Cost: the table and the guard can disagree the day he edits the matrix.
  - **Recommend (a).**

### RC-42, two passes

**Fact 1.** `NodeUnit.mint_intents` at `runtime.py:2031`. The `price` call that moves to pass two is in `qmb/src/qmb/host/unit_handler.py:910` (`_step`), after the exits. **MECHANICAL.**

**Fact 2.** `_drive` at `runtime.py:3616`, `_drive_one` at `:3641`. **MECHANICAL.**

### RC-43, parked entry

**Fact 1.** The `own_position:<market>` read is at `unit.py:1370`, a tuple of positions keyed by id since rc-32. The limit is rc-32's per-market position count. **MECHANICAL.** Text: "`_Run.entries` compares the count of open positions plus parked entries on the market with the market's position limit (rc-32)."

**Fact 2.** `Blocked` → `Skip` path at `runtime.py:2010`; the unknown-answer refusal at `:1251` (`market in self.unknown.values()`). **MECHANICAL.**

**Fact 3.** `_orders: dict[str, Placed | Blocked]` at `runtime.py:1780`; `execute_resting` at `:1999`. `Unknown` is not a state in `_orders`; unknown answers sit in `self.unknown`. **MECHANICAL.** Text: "Add `Parked(expires_at)` beside `Placed` and `Blocked`."

**Fact 4.** `budget_expired` joins `REASON_CODES` and `_REASON_WORDS`. **MECHANICAL.**

### RC-44, time budget

**Fact 1.** Constants at `runtime.py:200-208`; `watch.began` set at `:2518` and cleared at `:2524,2527`. `ctrader_account.py:110` and `healing.py:64` are unchanged. **MECHANICAL.**

**Fact 2.** `budget_impossible` joins the lists. It is a refusal at start, so it also needs the node journal's start-refusal wording. **MECHANICAL.**

### RC-45, declared no-stop entry

**Fact 1. No `basis` on the sizer row.** Code: the model's sizer binding has no `basis`. The runtime already carries `Amount.basis` from the sizer's answer, and the converter reads it (`qml/src/qml/numbers/convert.py:197`).
- Plan intent (agent decision, AD-22): "declares `basis: tail_budget` on its sizer row".
- Blast radius of a row field: the model, both schemas, census, guide, pack and a format bump (fact 2). Of a block face: the compiler reading the bound sizer's `entry.json` and one new stdlib sizer.
- **DESIGN CALL 11.** Options:
  - (a) A document field on the sizer row. Cost: the fact-2 set. The unit states its basis whatever sizer it binds.
  - (b) The basis is the sizer block's declared face (`output basis: tail_budget` in `entry.json`), with a shipped `tail-budget@1` sizer. The compiler lifts `stop_not_built` when the bound sizer declares it. Cost: one stdlib block (count pins, fact 3), no document field.
  - **Recommend (b),** if the no-stop path ships in stop B at all (see the finding below). It reuses what the runtime already carries.

**Fact 2.** `convert.py:197-198` skips `tail_budget`; lift it there and divide money at risk by the declared distance. **MECHANICAL.**

**Fact 3.** `stop_not_built` at `compiler.py:601-606`; `NONE_DECLARED` at `unit_intent.py:69`. The AD-22 table's lines are all root numbers. The current ones: `enter` `unit.py:1940` (stop read `:1964`); handler entry `unit_handler.py:963`; node entry stop read `runtime.py:1255`; veto `require_venue_resident_protective_stop` `:1293`; `_protected` `:1373`; `_money` `unit_handler.py:301`; `_close` `:1058`. **MECHANICAL.**

**Finding (agent decision without a ruling).** No owner word asks for a stopless unit. His words are "a stop, we need to understand" and "stops are now part of a unit" (M5, SEEDS-2 T-77). He also said that for scalpers the old dynamic stop and target was "replaced by the first invalidation specifically for scalpers" (M15). The no-stop path came from the funnel (FUNNEL I13, "His scalper without a stop has no R", built on Stage B idea `H2 I72`) and his "canvas" (M50). The plan's "You see" box for RC-45, "Your reckless scalper with no stop can be written", attributes the idea to him. Whether cTrader accepts a stopless market order is UNKNOWN (AD-22), and the shipped default stays a far stop. RC-45 and RC-46 are two stop-B PRs touching seven order paths for a form nothing ships. He should decide whether they stay in stop B or move after G-DEMO's probe.

### RC-46, no-stop position held

**Fact 1.** `_restore_stops` at `runtime.py:2809`; `restore_stop` at `:1384`; `NodeUnit.adopt` at `:1921`; `safe_to_restart`'s "has no stop at the venue" at `:2614`; `ConformanceAccount` at `:850`; the adapter's `no-stop` rejection at `qmn/src/qmn/venue/ctrader_account.py:1481`. `reconciler.py:379-390` is unchanged (`protected = position is None or position.stop is not None` at `:386`). **MECHANICAL.** The finding under RC-45 applies here too.

## Built code against its own intent (findings, not fixes)

1. **Stacked, root code: kill level by rank, not by table.** `Runtime.guard` (`runtime.py:3082-3084`) refuses entries at YELLOW or above by rank. The effect table (`effect_matrix.py:139-143`) governs closes only, and the owner-editable `ksa_effect_matrix` is never read at runtime. The two agree today only because the placeholder table matches the rank (RC-41 fact 5).
2. **rc-22 (in flight): house money on gross.** It folds `r_after_costs`, which holds gross, as "R after costs" (`unit.py:1680`). Its own intent and the repair handoff want net (RC-22 fact 2).
3. **rc-28 (in flight): node brakes see no commission.** The node handler has no cash port, so node `net_r` equals gross, and the brakes and cushion that read `net_r` read gross where money is real (DESIGN CALL 3). The departure is stated in PR 385, but no later section owns the fix.
4. **rc-26 (in flight): restart seed carries gross only.** After the rc-28 join, brakes after a restart could read gross while brakes before it read net (DESIGN CALL 2). Harmless on the node today because of finding 3.
5. **rc-29 (parked): day brake off after an unwatched midnight.** A known money-path blocker with a measured 9-line fix, waiting for his word.
6. **rc-22 (in flight): one restart rule unbuilt.** AD-18's "a raise earned before the restart waits for the next anchor" is not built, and no section owns it. It is an agent rule, and RC-22's own fact contradicts it, so it should go to the numbers talk, not into the build.

## Agent decisions that override or misread his words

1. **Paper.** He said paper trading is demo trading (M7). The plan's "paper" ends on a fake broker (RC-39 fact 3).
2. **News.** He placed news with the kill switch (M10, "unless I'm mistaken"). AD-16 moved it to stickers and says the kill switch is not one (RC-36).
3. **No-stop.** No ruling asks for a stopless unit, and he said stops are part of a unit (M5). The plan's "You see" box says "Your reckless scalper with no stop" (RC-45).
4. **Cost key.** He named market, instrument, timeframe and time (M7). The spine changed that to hour, session and world, and the code keys market, venue and hour. His "timeframe" is covered only indirectly, through the stop distance (DESIGN CALL 3).

## DESIGN CALLs in plain English

1. **Switching a rule off (RC-22, RC-41).** Your safety vetoes on the trading node (margin, order rate, size band) get on/off switches as node settings. The on/off switch inside a unit's own document arrives later, with pods (RC-53), the first thing that writes one. Recommended.
2. **Restart and real profit (RC-26).** When the node restarts, it re-reads each closed trade's profit both before and after costs, so your brakes count the same money after a restart as before. Needs one extra number on each trade record. Recommended.
3. **Costs on the real node (RC-28, RC-35).** Today the node measures what each market costs but does not take commission off each trade's result, so brakes and house money there see trades as slightly better than they were. Recommended: take the broker's stated commission off on the node now, and use the real one once your demo account is connected. Not recommended: adding "session" to the cost table, which you never asked for.
4. **Two unused combiners (RC-34).** "Multiply" and "lowest" ways of combining signals do nothing for yes/no signals. Recommended: drop them from this step and note them for later.
5. **Why a trade was skipped for news (RC-36).** Skips caused by a news or caution sticker get their own family of reasons ("sticker:news", "sticker:caution"), so a new kind needs no code change. Recommended.
6. **Where the spread/cost gate acts (RC-35).** The gate checks a trade after its size is worked out and can only lower or block it, never raise it. The record of why keeps its current plain-text form. Recommended.
7. **What "on paper" means (RC-39).** You said paper trading is demo trading. Until your demo account is connected, the plan should say the templates "fill on the test broker", not "trade on paper". A demo check is added for after sign-in. Recommended.
8. **One door before every order (RC-40).** The early version of that door, built in RC-06, is widened, not duplicated. Recommended.
9. **Margin and liquidation numbers (RC-41).** The broker does not give these yet, so the vetoes that need them warn "unknown" rather than block on a made-up number, until your demo account supplies real ones. Recommended.
10. **The kill level and new trades (RC-41).** Today the node blocks new trades at YELLOW by a fixed rule, not by the kill table you can edit. Recommended: make it read the table, so your edits take effect.
11. **The no-stop unit (RC-45, RC-46).** Recommended form if it stays: the sizing block declares "no stop", not a new document field. The bigger question is yours. You never asked for a stopless unit, and you said stops are part of a unit. Should these two steps stay in stop point B, or wait until your demo account shows whether the broker even accepts an order with no stop?
