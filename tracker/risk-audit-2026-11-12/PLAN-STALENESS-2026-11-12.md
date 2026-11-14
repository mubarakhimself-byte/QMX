# Plan staleness audit, 12 November

Read-only recheck of every PLAN.md section not yet stacked, against the stack tip `8d0a9758` (rc-25).
In-flight rows were also read at their branch heads: rc-22 `1b09f81c`, rc-26 `908ed68f`, rc-28 `0b1ad1eb`, rc-29 `72bbee12` (parked), rc-33 `34fb9d99`, rc-34 `5b0a5684`.
Line numbers are at `8d0a9758` unless a branch is named. "Root" means the plan's code truth `351e7521`.

## Counts

41 sections checked: 6 in flight or parked, and RC-35 to RC-69.
12 VALID, 29 UPDATE, 0 OBSOLETE. No section is already done. RC-63 is partly done (see its detail).

Every Files block passes the path check. Each "Edit" path exists at the tip, or is made by an earlier remaining row (entry_chain.py and sqs-floor by RC-35, node_links.py by RC-41, outbox.py by RC-42, host roll.py by RC-54). No "Create" path exists yet at the tip. The in-flight branches hold their own creates.

## Summary

| Section | Plain name | Depends on (status) | Verdict | Stale facts |
|---|---|---|---|---|
| RC-22 | House money as one rule on one ledger | RC-14, RC-21 (stacked) | UPDATE | 3 |
| RC-26 | Open trades keep their numbers, restart mid-count | RC-25 (stacked) | UPDATE | 5 |
| RC-28 | Costs observed from fills, sizer reads them | RC-25, RC-27 (stacked) | UPDATE | 4 |
| RC-29 | Feasibility verdict, account brakes on two units | RC-27 (stacked) | UPDATE | 3 |
| RC-33 | Sessions and per-market settings | RC-32 (stacked) | UPDATE | 2 |
| RC-34 | The remaining logic roles | RC-33 (in flight) | UPDATE | 4 |
| RC-35 | SQS as a gate slot, cost hurdle first | RC-28, RC-34 (in flight) | UPDATE | 6 |
| RC-36 | Isolation, news and caution on one sticker | RC-35 | UPDATE | 3 |
| RC-37 | Spread and quote-gap sensor, one curve per world | RC-35 | VALID | 0 |
| RC-38 | Move the SQS rule and producer to the floor | RC-37 | VALID | 0 |
| RC-39 | Scalper and intraday templates reach paper | RC-19 (stacked), RC-22, RC-26 (in flight), RC-36 | UPDATE | 3 |
| RC-40 | One admit seam for both hosts | RC-35 | UPDATE | 3 |
| RC-41 | Kill effects on entries, an off switch per veto | RC-40 | UPDATE | 4 |
| RC-42 | Node in two passes, exits first | RC-41 | UPDATE | 2 |
| RC-43 | A parked entry's lifetime, never sent twice | RC-42 | UPDATE | 4 |
| RC-44 | Entries pass bounded in time, honest watchdog | RC-43 | UPDATE | 2 |
| RC-45 | A declared no-stop entry compiles, sizes, sends | RC-44 | UPDATE | 3 |
| RC-46 | A no-stop position survives ticks and restart | RC-45 | UPDATE | 1 |
| RC-47 | Copilot doors for one unit | RC-36 | VALID | 0 |
| RC-48 | Single-unit guide, stop point B | RC-39, RC-46, RC-47, RC-29 (parked) | UPDATE | 2 |
| RC-49 | Group document, limits as live facts | RC-48 | UPDATE | 1 |
| RC-50 | Group caps that only cut, one ledger | RC-49 | UPDATE | 1 |
| RC-51 | Default group rows, kill line, restart rules | RC-50 | VALID | 0 |
| RC-52 | Replay a group, prove it at 200 | RC-51 | VALID | 0 |
| RC-53 | A pod as a recipe, with drift | RC-48 | UPDATE | 1 |
| RC-54 | One pod edit, one plan, one click | RC-53, RC-49 | UPDATE | 1 |
| RC-55 | Move risk in place | RC-54 | UPDATE | 2 |
| RC-56 | Stages compiled in | RC-55 | UPDATE | 1 |
| RC-57 | Pod gallery | RC-54 | VALID | 0 |
| RC-58 | Readings bus with publisher and fallback | RC-48 | UPDATE | 3 |
| RC-59 | Land items from a mini app, save a block | RC-53 | VALID | 0 |
| RC-60 | Trace a Library block to a node deploy | RC-58, RC-59 | VALID | 0 |
| RC-61 | Apps read journals and the fold, raise a card | RC-48 | VALID | 0 |
| RC-62 | Scripted fleet watch, decay flood off | RC-61, RC-51 | VALID | 0 |
| RC-63 | Report both motion arms, stamp run arms | RC-25 (stacked) | UPDATE | 1 |
| RC-64 | Keep the record when a placeholder is swapped | RC-55, RC-28 (in flight) | UPDATE | 2 |
| RC-65 | Re-test every deployed unit after a bump | RC-64 | UPDATE | 1 |
| RC-66 | Guide and stop point C | RC-52, 56, 57, 60, 62, 63, 65 | VALID | 0 |
| RC-67 | Signed stop, amend with read-back | RC-66 | VALID | 0 |
| RC-68 | Partial close and trail on the node | RC-67 | UPDATE | 2 |
| RC-69 | Venue targets, entry forms, netting per venue | RC-68 | UPDATE | 1 |

Two dependency notes. RC-48 waits on rc-29, which is parked, so stop point B cannot be readied until rc-29 is unparked. RC-63 depends only on RC-25, which is stacked, so it is the one remaining section that could start now.

## Facts that apply to many sections

These hold for every remaining section that does the named thing. Each brief should carry them.

1. **The compiler format is 12 at the tip** (`qml/src/qml/compile/compiler.py:115`). It is 13 on rc-33, 14 on rc-34 (which sits on rc-33), and 11 on parked rc-29. The next bump after rc-34 lands is 15.
2. **Lifting a refusal or bumping the format moves generated files that no Files block names.** They are `tools/qml/extending.py` (the probe table), `qml/EXTENDING.md` (every row says "compiler format 12"), `qml/tests/test_unit_refuses.py`, the two schema copies `qml/src/qml/unit/qmx.unit.1.schema.json` and `qmx-agents/packages/qmx-library/src/qmx_library/kinds/unit.schema.json`, the stored hash in `qml/tests/test_receipt.py`, and the judge's pack (`qmx-agents/packages/qmx-judge/src/qmx_judge/conformance_pack/pack.json`, `golden.json`, `fixture.json`). RC-13, RC-16 and rc-33 each had to add these outside their blocks. The fields still refused at the tip are listed at `compiler.py:1186-1407`. Sections that lift one: RC-35 (`gates`), RC-36 (`tolerations`), RC-49 (`tags`), RC-53 (`risk_locks`, `recipe`), RC-56 (`stages`, `stage_values`), RC-58 (`reads`, `home_markets`, `context_needs`).
3. **A new stdlib block moves two count pins.** They are `qml/tests/test_nothing_silent.py:251` (130 at the tip) and `qmx-agents/packages/qmx-host/tests/test_dictionary_full_size.py:117,119` (473 pages, 130 entries). No Files block names them. RC-35 adds 2, RC-39 adds 5 and RC-51 adds 3. In flight, rc-22 adds 2 and rc-28 adds 1.
4. **A new skip or refusal code must join two closed lists,** or the node files it as `unlisted`. They are `REASON_CODES` at `packages/qmf-data/src/qmf/data/journal_kinds/unit.py:48` and `_REASON_WORDS` at `qmb/src/qmb/results/journal.py:69`. rc-33 had to add `outside_session` this way. New codes in the remaining plan include `net_edge_below_zero`, `sticker:news`, `kill_effect`, `past_liquidation`, `budget_expired`, `budget_impossible`, `logic_changed`, `stop_widen`, `partial_full` and `netting_not_attributed`.
5. **`qmn/src/qmn/app/runtime.py` grew by 190 to 600 lines,** so every root line number in it is wrong. The new numbers are in each section below.
6. **Facts are named `market.<name>:<market>`.** Examples are `market.rate:<quote>` and, on rc-28, `market.cost_cell:<market>`, `market.gap_factor:<market>` and `market.funding:<market>` (`qmb/src/qmb/host/facts.py:234-241` on rc-28). RC-35 and RC-37 should use that form.

## Sections to update

### RC-22, house money (in flight, PR 382)

1. The branch sits on `74c1e7ba` and the tip is now `8d0a9758`, so it needs another join. Its count pins read 131. They must read 132 after the join, because rc-25 added `own-r-step@1`.
2. It adds a new reader of `trade.r_after_costs` (rc-22 `qml/src/qml/protocol/unit.py:1680`). rc-28 renames that field to `gross_r`. Whichever of the two joins second must rename it.
3. The section's "read `enabled` as a bool or a fact name on every row" is half built. The runtime reads it. No document can write it, because the schema's `OneOf` holds records only (PR 382). BACKLOG gives that to RC-41 or RC-53.

### RC-26, open trades keep their numbers (in flight, PR 386)

1. `PositionFacts.numbers_at_entry` already exists at `qml/src/qml/protocol/exits.py:106`, so Build box 1 was half done before the row.
2. `_OwnJournal` is at `runtime.py:1674`, not `1479-1491`.
3. The flat rule at root `unit.py:543` is gone. Since rc-32, positions are a tuple per market (`unit.py:12`).
4. The test literal 0.98 lots is wrong. The node sizes on balance plus realised money, so the answer is 0.88 (PR 386).
5. The branch sits on `266f34e4`. That base lacks rc-25's last two commits (`5187ea89`, `8d0a9758`), which edit `compiler.py`, `unit.py`, `test_number_moves.py` and `qmb/tests/test_unit_handler.py`. Its new writer `r_after_costs=Decimal(r)` (rc-26 `runtime.py:2422`) must follow rc-28's rename.

### RC-28, costs from fills (in flight, PR 385)

1. `engine.py:57,120` are now `qml/src/qml/motion/engine.py:62,156`.
2. The branch sits on `266f34e4`, as rc-26 does. The same two rc-25 commits touch files it also edits (`test_number_moves.py`, `test_unit_handler.py`, `unit.py`).
3. Its count pins read 131 against a tip of 130. They need re-reading after the join.
4. Its review fact says every reader of `r_after_costs` moves. rc-22 and rc-26 each add a new reader on their branches, so the fact fails for whichever lands after it.

The row's departures change later sections. Cells are keyed by market, venue and hour, with no session and no world. The node starts the handler without `costs`, so node cells run at the default N and node `net_r` equals gross.

### RC-29, feasibility and two-unit brakes (parked, PR 380)

1. The branch sits on `a477f907` (rc-21), three rows behind the tip, at format 11 against the tip's 12.
2. The Files block names 4 files. The row needed 15, including `runtime.py`, `packages/qmf-data/src/qmf/data/journal_kinds/node.py` and `qmx_tools/functions.py`.
3. Its `functions.py` edit shares that file with RC-47, RC-52, RC-54, RC-59 and RC-62.

### RC-33, sessions (in flight, PR 381)

1. The branch sits on `74c1e7ba`. rc-25 has since edited `compiler.py` and `unit.py`, two of its four Files paths, so it needs a third join. The receipt pin and pack must be re-read even though the format stays 13.
2. The `stop_buffer` literals 2 and 30 must be written 0.0002 and 0.0030. The dummy stores that number as a fraction from 0 to 0.01 (PR 381).

### RC-34, remaining logic roles (in flight, PR 384)

1. It sits on rc-33's head at format 14. Its count pins read 129, while the tip reads 130.
2. `compiler.py:896-1014` is now `_shape_problems`'s range. The role refusal is `role_not_built` in `_Wiring.side`, `compiler.py:538`.
3. `derivation`, and a combiner with `product` and `min`, are not built (PR 384). The section's second sentence is unmet. No remaining section owns it.
4. No stdlib block reads `bars_since`, and `time-exit-bars` is refused in a slot (BACKLOG, rc-34).

### RC-35, gate slot

1. `gates` is already a model field, refused as `gates_not_built` at `compiler.py:1225`. Lifting it moves the generated files in fact 2. None of them is in the Files block.
2. Two new stdlib blocks move the count pins in fact 3.
3. `net_edge_below_zero` must join the closed lists in fact 4.
4. The name `Verdict` is taken by the G check's enum at `qml/src/qml/check/result.py:102`.
5. The hurdle reads rc-28's cell. That cell is keyed by market, venue and hour, with no session or world. It is read as `market.cost_cell:<market>`. On the node it runs at the default N because `runtime.py` passes no `costs`.
6. An admit seam already exists after pricing: `AdmitPort` at `unit.py:468`, with `SIZE_BAND` as the default (`unit.py:1077`, RC-06). The modifier chain multiplies factors (RC-21), and rc-22 adds a `flag` chain word for its press gate. The new `shrink` verb has to fit beside both.

### RC-36, stickers

1. `Unit.tolerations` exists at `qml/src/qml/unit/model.py:599`, refused as `tolerations_not_built` at `compiler.py:1229-1232`. Lifting it moves the generated files in fact 2.
2. `sticker:news` is not a `REASON_CODES` word. A `sticker:` family would need a declared family, like `BLOCK_REASON_FAMILY` at `journal_kinds/unit.py`.
3. `Kind.SPEC_CHANGE` exists at `qmn/src/qmn/app/stand_down.py:93`, but nothing in `qmn/src` writes it yet. The Build box "wire record change to `Runtime.stand_down(SPEC_CHANGE, ...)`" is new work, and `Runtime.stand_down` is at `runtime.py:3146`.

### RC-39, scalper and intraday templates

1. The fake-broker rig's base bar is 900 s (`qmn/tests/test_app_binding.py:864`). The node refuses a stream that is not a whole multiple of the base (`runtime.py:587-588`). A scalper at 60 bars an hour cannot host on that rig as it stands, so `test_the_three_templates_share_one_account` must set a 60 s base.
2. Five new stdlib blocks move the count pins in fact 3.
3. K7 ends on the fake broker, not a practice venue (RC-19's fallback). The Library's account kind admits only demo or live. "Reaches paper" means a fill on the fake broker.

### RC-40, one admit seam

1. `AdmitPort` already exists at `qml/src/qml/protocol/unit.py:468`, as `admit(proposal, entry: PricedEntry) -> str | None`, with `SIZE_BAND` as its default at `unit.py:1077` (RC-06). The plan's new `AdmitPort.admit(wire, at)` in `qml/chain/node_chain.py` collides with it. The brief must either widen it or pick a new name.
2. `runtime.py:1100-1106` (the `cross_unit_hook` call) is now `runtime.py:1291`. `2623-2675` (`guard`) is now `runtime.py:3079`.
3. The price call is in `UnitSliceHandler._step` at `qmb/src/qmb/host/unit_handler.py:910`, and `mint_intents` is at `:862` (RC-06). `CrossUnitHook` and `PASS_EVERY_ORDER` are at `qml/src/qml/blocks/api.py:280,302`.

### RC-41, kill effects on entries

1. `runtime.py:179-187` (the protection constants) is now `runtime.py:200-208`.
2. Margin headroom and liquidation distance always read absent. The binding reads only the balance (RC-27 departure 3, PR 361, named for RC-41). The margin link and `test_a_stop_past_liquidation_refuses` need a source this section must build or name.
3. `enabled: false` on a row cannot be written in a document yet (rc-22). The model, schema copies, parser, census and guide need it, and none is in the Files block.
4. `kill_effect` and `past_liquidation` must join the closed lists in fact 4.

### RC-42, two passes

1. `runtime.py:1727-1733` is `NodeUnit.mint_intents`, now at `runtime.py:2031`. The price call it means to move is in `qmb/src/qmb/host/unit_handler.py:910` (RC-06).
2. `runtime.py:3013-3018` (`_drive`) is now `runtime.py:3616`.

### RC-43, parked entry

1. The `own_position:<market>` read is at `unit.py:1370`, not `:515`. Since rc-32 it is a tuple of positions keyed by id, and the limit is rc-32's per-market position count.
2. `runtime.py:1705-1713` is now `:2010`. The unknown-answer refusal (`runtime.py:1059`) is now `:1251`.
3. `_orders` is already `dict[str, Placed | Blocked]` at `runtime.py:1780`, and `execute_resting` is at `:1999`.
4. `budget_expired` must join the closed lists in fact 4.

### RC-44, time budget

1. `runtime.py:179-187` is now `:200-208`, and `runtime.py:2192` (`watch.began`) is now `:2518`. `ctrader_account.py:110` and `healing.py:64` are unchanged.
2. `budget_impossible` must join the closed lists in fact 4.

### RC-45, declared no-stop entry

1. The model's sizer binding has no `basis` field (`qml/src/qml/unit/model.py`). "Declares `basis: tail_budget` on its sizer row" needs the model, schema copies, census and guide, and none is in the Files block.
2. `qml/src/qml/numbers/convert.py:197-198` skips `tail_budget` by name today (RC-05). That is the line to lift.
3. `stop_not_built` is at `compiler.py:601-606`. `NONE_DECLARED` is unchanged at `unit_intent.py:69`.

### RC-46, no-stop position held

1. `runtime.py:2358-2386` (`_restore_stops`) is now `runtime.py:2809`. `reconciler.py:379-390` is unchanged.

### RC-48, stop point B

1. It depends on RC-29, which is parked.
2. The node's version is already `0.1.15` (RC-20). BACKLOG (from RC-02) asks RC-48 to widen the guide's hand-written journal kinds, but the section does not say so.

### RC-49, group document

1. Selecting by tag needs `tags`, which is refused as `tags_not_built` at `compiler.py:1261`. Lifting it moves the generated files in fact 2, and `compiler.py` is not in the Files block.

### RC-50, group caps

1. The fold's `RiskState` carries only scope, word, since, reason, stamp and unknown (RC-14 departure 1). So `day_pnl`, `open_risk` and `cushion` are new fields. rc-22's cushion ledger is in R, not money, so `group.cushion` must say its unit.

### RC-53, pods as recipes

1. `risk_locks` and `recipe` are refused at `compiler.py:1243,1249`. Lifting them moves the generated files in fact 2. BACKLOG also names this row or RC-41 for the `enabled` document field.

### RC-54, one plan, one click

1. `promote.py:422-447` points into `_no_live_deployment`, which now starts at `promote.py:490`.

### RC-55, move risk in place

1. `unit.py:990-991` (the snapshot fingerprint check) is now `unit.py:2257`.
2. `runtime.py:2098` (the one compile worker) is now `runtime.py:2424`.

### RC-56, stages

1. Both `stages` (`compiler.py:1237`) and `stage_values`, added by RC-23 and refused at `compiler.py:1395`, must be lifted. `test_unit_refuses.py` is in the block. The guide and schema files are not.

### RC-58, readings bus

1. BACKLOG (rc-03 Opus re-review) says the `sections.py:57` fix must land with RC-58. A `reads` row read by an exit lands in the risk half. `qml/src/qml/unit/sections.py` is not in the Files block.
2. `runtime.py:367-369` is now `runtime.py:406`.
3. `reads`, `home_markets` and `context_needs` are refused at `compiler.py:1196,1255,1206`. Lifting them moves the generated files in fact 2. `Read` (`model.py:429`) has no `publisher` or `valid_until_s` yet, as the plan says.

### RC-63, both motion arms

1. QMB already runs and reports a motion-off arm. It did at root too: `qmx-agents/apps/qmb/jobs/backtest.py:62`, and `qmb/tests/test_run_journal.py:440-444` reads `measures["motion_off"]["trades"]`. `test_a_run_reports_both_arms` as written would pass at the parent, so lane 2 cannot go red then green. The new work is the arm, link and parent stamps and the reserved proposal row.

### RC-64, forwarding a swapped placeholder

1. Both shipped templates bind `fixed-fraction-at-stop@2` (`qml/src/qml/unit/templates/dummy-trend-pullback.json:80`, `canary.json:81`). The map must declare `@2 -> @3`, and `@1 -> @3` if kept. `@3` is rc-28's, still in flight.
2. `classify` is at `qml/src/qml/identity/diff.py:302`, and no file in `qmx_host` or `qmx_judge` calls it. `diff.py` is not in the Files block.

### RC-65, re-test after a bump

1. "Format 6 on a unit recorded at 5" is stale. The tip is 12, and 14 once rc-34 lands. The test should take the current format and the current format plus one.

On BACKLOG's RC-04 note about the pack script: its golden step was repaired by RC-11 (PR 364). rc-31 later saw its spawned QMB child hang after the last write (PR 369).

### RC-68, partial close and trail

1. `runtime.py:1807-1808` (`case ClosePartial()`) is now `runtime.py:2114`.
2. BACKLOG (RC-12) moves the six-exit-stack test into this row. Its Verify Unit block does not name it.

### RC-69, venue targets and netting

1. The node already refuses a second live unit trading a shared market on a netting account. That is `_netted` at `runtime.py:3394-3412`, present at root `:2905`, for the live lane only, with text and no code. rc-32 added the one-unit compile answer `position_limit_nets`. `test_two_units_on_one_netting_symbol_refuse` must extend that refusal to every lane and give it the code `netting_not_attributed`. Non-market entries are still blocked by text at `runtime.py:1247-1248`, which is the line `OrderSpec` replaces.

## Merge candidates

Pairs of remaining sections where one directly depends on the other and their Files blocks share a path.

| Pair | Shared paths |
|---|---|
| RC-33 then RC-34 | `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/unit.py` |
| RC-34 then RC-35 | `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/unit.py` |
| RC-35 then RC-36 | `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/entry_chain.py` |
| RC-40 then RC-41 | `qmn/src/qmn/app/runtime.py` |
| RC-41 then RC-42 | `qmn/src/qmn/app/runtime.py` |
| RC-42 then RC-43 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/protocol/unit.py`, `qmn/src/qmn/app/outbox.py`, `qmn/src/qmn/app/runtime.py` |
| RC-43 then RC-44 | `qmn/src/qmn/app/outbox.py`, `qmn/src/qmn/app/runtime.py` |
| RC-44 then RC-45 | `qmn/src/qmn/app/runtime.py` |
| RC-45 then RC-46 | `qmn/src/qmn/app/runtime.py` |
| RC-49 then RC-54 | `qmx-agents/packages/qmx-host/src/qmx_host/promote.py` |
| RC-50 then RC-51 | `qmn/src/qmn/app/runtime.py` |
| RC-54 then RC-55 | `qmx-agents/packages/qmx-host/src/qmx_host/roll.py` |
| RC-55 then RC-56 | `qml/src/qml/protocol/unit.py` |
| RC-55 then RC-64 | `qmn/src/qmn/app/runtime.py` |
| RC-58 then RC-60 | `qmn/src/qmn/app/runtime.py` |
| RC-62 then RC-66 | `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` |
| RC-64 then RC-65 | `qmn/src/qmn/app/runtime.py` |
| RC-67 then RC-68 | `qml/src/qml/protocol/exits.py`, `qmn/src/qmn/app/runtime.py` |
| RC-68 then RC-69 | `qml/src/qml/compile/compiler.py`, `qmn/src/qmn/app/runtime.py` |

Only the plan's Files blocks and direct Depends-on edges were used. Pairs linked only through a chain, and the unlisted generated files in fact 2, are not counted.
