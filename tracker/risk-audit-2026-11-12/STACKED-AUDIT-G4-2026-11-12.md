# Stacked audit G4, 12 November: rc-30, rc-31, rc-32, rc-23, rc-21, rc-24, rc-25

Read-only audit of the seven rows stacked after stop A, from `baf7c9fa` to the tip `8d0a9758`. Code was read with `git show`, `git diff` and `git grep`. Probes and the rows' own new tests ran once in a detached copy at `D:/Temp/stacked-g4` (tip `8d0a9758`), each under `timeout`. The copy was removed with `git worktree remove`. Nothing else was written.

rc-30, rc-31, rc-32, rc-23 and rc-21 were built and reviewed by DeepSeek, so each gets a second-family code review and an intent check here. rc-24 and rc-25 were joined, fixed and reviewed by Claude Opus, so they get the intent check only.

Owner intent means his own words only, from the registers `seeds/operator-words-*.md` (M numbers) and the transcript user turns. Everything else is labelled "agent decision".

**Counts.** 7 rows. 3 OK (rc-32, rc-23, rc-24), 4 FINDING (rc-30, rc-31, rc-21, rc-25). Findings by severity: 2 high, 2 medium, and 4 new lows (rc-30 ×2, rc-32 ×2), plus lows carried from the earlier reviews. 2 OWNER CALLs.

## Summary

| Row | PR | Head | Verdict | Severity | One line |
|---|---|---|---|---|---|
| rc-30 | 366 | a9abd534 | FINDING | **high** | A 15-minute bucket with one quiet minute at its start, its second minute or its end is dropped on a live feed. Proven at the tip. The Opus re-review found it, and the store does not track it. |
| rc-31 | 369 | f166baed | FINDING | medium | A stateful block reading the slower stream is fed that stream's bar once per primary step, so an EMA on m5 is not the m5 EMA. Proven. No look-ahead leak. |
| rc-32 | 379 | fa2b3a39 | OK | low ×2 | Exits key by position id on both hosts, and a netting venue refuses above one. The "same bet check" he accepted is a fact only until RC-50. |
| rc-23 | 377 | a774f3d1 | OK + OWNER CALL | none | His "has to have a reason... a derivation" is met as a field. Every shipped number's reason reads "unargued until the numbers talk", and `derivation` is refused. |
| rc-21 | 376 | a477f907 | FINDING | **high** | A modifier answering a finite factor inside its own declared range can raise `decimal.Overflow` out of `price` and drop a held exit. Proven at the tip. rc-28's sizer fix does not cover it. |
| rc-24 | 378 | 74c1e7ba | OK | (backlog) | Intent met. The scaled-number-to-exit gap needs a compile refusal before any template binds `scaled`. |
| rc-25 | 383 | 8d0a9758 | FINDING | medium | `own-r-step@1` moves `risk_fraction` on R before costs. That goes against his "costs... so that the unit can know. That's how configuring". |

High findings:
1. rc-30 `qmn/src/qmn/app/runtime.py:599-610` (`_Roll.add`) and `qml/src/qml/feed/rollup.py:35,50-54`: a live 15-minute bar is lost when its first, second or last base minute has no spot.
2. rc-21 `qml/src/qml/protocol/unit.py:1209,1214,1220`: the factor product and the two multiplies sit outside the fault wall. An extreme finite factor raises `decimal.Overflow`, and the held position's exit at that step is not minted.

## What ran

All of this ran in `D:/Temp/stacked-g4` at `8d0a9758`, with `PYTHONPATH` on that copy's `src` folders and the interpreter from `bld-rc-25/.venv`. The import paths printed confirmed the copy's `qml` and `qmn` were the ones loaded.

- The rows' new qml tests: `test_rollup`, `test_second_stream`, `test_many_positions`, `test_number_spec`, `test_modifiers`, `test_motion_widened` and `test_number_moves`. 37 passed, exit 0.
- The Opus `gap_probe.py` (from `review/rc-30-opus-a9abd534.md`), rerun at the tip with an interior-minute control added. It exited 1:
  ```
  no quiet minute        : closed buckets ending at minutes [0, 15, 30]
  quiet last minute (15)  : [0, 30]
  quiet second minute (2) : [0, 30]
  quiet first minute (1)  : [0, 30]
  quiet minute 8 (interior): [0, 15, 30]
  ```
- `slow_ema_probe.py`, written for this audit. It compiles the rc-31 test's two-stream unit (m1 primary, m5 slow) with its context binding replaced by `ema@1` (period 3) on `m5.close`, and drives it beside a one-stream m5 unit with the same binding. It exited 1 with 9 mismatches. Two sample bars:
  ```
  m5 bar 2 at minute 15: two-stream 1.10085781250  one-stream m5 1.10110000000  direct 1.10110
  m5 bar 9 at minute 50: two-stream 1.10135443549  one-stream m5 1.10131875000  direct 1.10132
  ```
  The two-stream EMA also answers at minute 10, after three m1 updates and only two m5 bars.
- `factor_probe.py`. This is the exit probe's `probe_handler.py` (real `UnitSliceHandler`, real `HostedUnit.price`, a held position whose `close_full` exit is minted on the same step as an entry proposal), with modifier cases added. It exited 1:
  ```
  control (real sizer, factor 0.5)                 EXIT_WENT_OUT
  sizer Amount float value (factor 0.5)            EXIT_BLOCKED  TypeError at unit.py:1214
  modifier factor 1E+999999 in range (0,1E+999999) EXIT_BLOCKED  decimal.Overflow at unit.py:1214
  modifier factor 1E+5000 in range                 EXIT_WENT_OUT
  modifier factor 1E-999999 in range               EXIT_WENT_OUT
  ```
  The second line confirms the known rc-06 + rc-21 malformed-sizer block is still present at the tip. It is fixed on rc-28 (`cb7efa414`), which is not stacked.

## Per-row detail

### rc-30, one base bar per feed, roll every stream up (PR 366), FINDING high

**Code.** `roll_up` is pure and its two literal tests hold. Windows key by `(stream, market)`. `_host` refuses only a stream that is not a whole multiple of the base. The warm-up fix (step every replayed bar while warming, flip after the batch) is correct, and the DeepSeek and Opus reviews both proved it red to green.

**Finding, high.** `qmn/src/qmn/app/runtime.py:599-610` and `qml/src/qml/feed/rollup.py:35,50-54`.
- The cTrader builder emits no base bar for a minute with no spot (`ctrader_account.py:1395-1421`, read at the tip).
- If a bucket's last minute is quiet, `_Roll.add` resets its held bars when the next bucket's bar arrives (`:604`), so the bucket is never emitted. AD-25's spine says "a bucket closes on the first base bar at or past its end".
- If the second minute is quiet, `_base_ns` infers a 2-minute base from the run's spacing, the start is misaligned, and `roll_up` returns None.
- If the first minute is quiet, the bucket reads as a reconnect and is dropped.
- At the parent, a 900 s feed built the 15-minute bar from any spot in the bucket. So on a real feed (rollover, the gold break, thin hours) the head's 15-minute units step on fewer bars than the parent's. Entries and per-bar exits skip those bars, and the indicator windows are built from a different series. The section's fact holds only on gapless input.
- The Opus second-family review wrote this as a blocker at `a9abd534` (`review/rc-30-opus-a9abd534.md`, NOT CLEAN, 11 Nov 15:55). The store still shows CLEAN: `REREVIEW-QUEUE.tsv` says "running", `ledger.tsv` says CLEAN, and STACK-LIST's "Reds found in stacked rows" does not list it.
- **Smallest fix (on a tip row):**
  - Pass the known `base_ns` into `roll_up` instead of inferring it.
  - In `_Roll.add`, when a bar lands in a later bucket, roll and emit the held bucket first.
  - Treat a bucket as seen from its start when the roll saw the previous bucket.
  - Add a test with the first, second and last minute missing, asserting literal OHLC.
  - Add the same holes to the fact's input.

**Lows.**
- `runtime.py` `NodeUnit._exit` answers `Blocked("the intent names a stream this unit does not read")`. It is unreachable today, but it would drop an exit if reached (Opus low 4).
- `[node] ctrader_bar_s` is a module constant labelled "a setting", and it is not in the registry catalog. His standing rule (memory, `qmx-operator-standing-rules.md`) is that "configurable" means UI-editable. This predates the row, which restated it.

**Intent.** His words back a 60-second base: "I think 1 minute is the best" (M60, 9 Nov). He also gave the fast-scalper example "a 1 minute or 5 minute time frame" (M5, 1 Nov). The 60 s default, the roll-up design and the drop-a-partial-bucket rule are agent decisions (AD-25). They are sound, apart from the finding.

**Conflicts with the intent reports.** None of the listed ones apply.

**Later rows.**
- RC-39's 1m, 5m and 15m templates share this roll. An m1 stream on the m1 base passes through and is unaffected. m5 and m15 lose quiet-minute buckets.
- RC-37's quote-gap measurement will see the same quiet minutes.

### rc-31, a second stream with no look-ahead (PR 369), FINDING medium

**Code.** There is no look-ahead.
- The step refuses any bar knowable after the instant (`unit.py`, `_Run.step`).
- The handler answers a slower stream's latest window bar with `ns <= instant`.
- The node pushes each rolled bar into its window before the primary's frontier closes, so an m5 bar closing at the same instant as the m1 bar is read at exactly its `knowable_at`.
- rc-30's warm-up fix survives the join unchanged. The DeepSeek review checked this, and the diff agrees.

**Finding, medium.** `qml/src/qml/protocol/unit.py:1690-1709` (`_Run.side`).
- Every binding's `update()` runs on every primary step, and `resolve()` hands a slower-stream ref the last closed slow bar. So a stateful block on m5 receives each m5 bar five times.
- Proven above: an `ema@1` on `m5.close` in an m1+m5 unit differs from the same block in an m5 unit on 9 of 10 m5 bars. It also "warms" in primary steps, not slow bars.
- The row's tests cannot see this, because the slow binding is `value-above@1`, which is stateless.
- The plan's "You see" promise is "a scalper can look at 5-minute bars while it trades 1-minute ones". That holds for the bar itself, not for any indicator on it.
- Reachability today: nil. QMB and the G check host one stream only, so a two-stream unit cannot pass G or reach paper. That is why this is medium and not high.
- **Smallest fix:**
  - Record each binding's stream at compile. `_warm_up` already maps bindings to streams.
  - In `side()`, update a binding only when its stream's bar is fresh this step, and otherwise reuse its last output.
  - Add a test that a two-stream unit's `ema@1` on m5 equals the one-stream m5 unit's.

**Lows.** These are carried from the DeepSeek review, and I agree with them.
- No node test hosts a two-stream document.
- A mid-bucket recording start leaves the slow stream one bar short at the flip. This costs timing only.
- K9 17 drives two units through the node where the spine names three.

**Intent.** He said "the 1 minute against 5 minutes, man, I did not say use that... Seriously, if it's useful, use it" (M63, 9 Nov), and "this thing of 1 minute to 5 minutes... If you think it's viable, then sure, take it" (M62). So the feature is an agent decision he delegated. It stands, but it must compute the slow indicator correctly to be "useful".

**Conflicts.** None.

**Later rows.** RC-39, if a scalper template reads m5 context. Any row that lifts QMB or G to multi-stream will expose the finding.

### rc-32, more than one position per market (PR 379), OK

**Code.**
- `_held` and `open_positions` key by position id.
- The node's `_exit` looks a position up by `exit_.position_ref.position_id` (`runtime.py:2109`).
- `adopt`, `_restore_stops` and the reconciler key by the venue position name, so a hedging account's two positions on one symbol keep their own stops.
- `nets_positions` comes from the cTrader account's own `position_model` (`ctrader_account.py:1154-1156`), and the compiler's default is to refuse (`compiler.py:191`), so an unstated venue refuses.
- The fix round's three test-double repairs are honest (DeepSeek review at `fa2b3a39`).
- I found no exit that can close the wrong position and no new exit block.

**Lows.**
1. **The bet check is a fact only.** `own.open_risk_by_bet_key` is published (`unit.py:1483-1485`) and nothing reads it. The spine says "the live control is the bet key and group cap", and the group cap is RC-50. Until then, a document with `per_instrument` above 1 puts R per position on one bet, bounded only by the size band (`PER_TRADE_CAP_SHARE` 1 = whole equity, `SIZE_BAND_MAX_LOTS` 100). Both shipped templates keep 1. Fix: none now. Name it in the stop-B note.
2. **QMB always states `nets_positions=False`** (`qmb/src/qmb/host/unit_runner.py:537`). So a two-position document backtests and is then refused at a netting node. `UnitRunResult.open_positions` now lists position ids where it listed markets (`backtest.py:235`). Both are disclosed in the PR.

**Intent.** His words: "isn't it possible for us to be able to hold more than one position at a go?... Position number one... has its rules and its sizing... Position number two also has the same rules, sizing" (M7, 1 Nov). Later: "you're saying two positions in an overlap aren't in contradiction. Each is sized on its own and they are related together by the same bet check. Okay." (3 Nov). His first example was a multi-pair bot holding gold and crypto at once, which the root already did (one position per market). The 3 Nov overlap case is what this row builds. Each position sized on its own: built. Bet check: key only (low 1). The default limit of 1 and the netting refusal are agent decisions, and sound.

**Conflicts.** None.

**Later rows.**
- RC-43 must count parked entries in the limit. Intent A already names it.
- RC-50 must read `open_risk_by_bet_key` for the bet check he accepted.

### rc-23, every number's derivation, range, authority and reason (PR 377), OK + OWNER CALL

**Code.**
- `_number_fields` (`compiler.py:1360-1411`) refuses by name every field the compiled format cannot run: `derivation`, `guard`, `cautious`, `never_self_tune`, `stage_values`, `authority: at_anchor`, and `authority: off` on a moving number. So no field is accepted in silence.
- Layer C refuses a missing reason or range.
- `CHECKER_FORMAT_VERSION` 2→3 is the honest counter. No compiled decision changed.
- Old documents upgrade and read (the fact).
- The DeepSeek review's lows are style and evidence-trail only. I agree with them.

**Intent.** His words: "that number 5%, for example, has to have a reason as to why it's 5, not 10... There has to be a derivation or a reason as to why it's set at 5. That's why we need to come up with a way in which a unit can self-configure it" (M7, 1 Nov). The row gives every number a reason, a range and an owner, and it refuses an unlabelled one. That is his ask in structure.
- **Agent decision:** every shipped value's reason is a placeholder ("unargued until the numbers talk"), and `derivation` is text that the compiler refuses. So no number yet carries the derivation he asked for. That is honest labelling, not a defect, but it is the gap his words point at. See OWNER CALL 1.

**Conflicts.** `stage_values` is added to `NumberSpec` here, and `sections.py` `_staged` ignores it (intent B finding F2). It cannot be reached while `stage_values_not_built` refuses it, so it is not a finding on this row.

**Later rows.** RC-56, which lifts `stage_values`, must make `stages` logic when any logic-half number has `stage_values`. Intent B gives that brief text.

### rc-21, size's named modifiers (PR 376), FINDING high

**Code.**
- The chain runs in document order and multiplies.
- A non-`Factor`, non-finite, float or malformed answer faults on the modifier's pin and benches entries. That is the review blocker, now closed.
- An out-of-range factor is refused by name and reads neutral.
- Exits never read the chain.
- A unit with no modifiers prices byte-equal to its parent (the fact).

**Finding, high.** `qml/src/qml/protocol/unit.py:1209` (`factor *= read.value`), `:1214` (`wanted.value * factor`) and `:1220` (`sized.value * reduced`).
- All three are outside every `try` in `price`. The range a factor is checked against is the one the block declares in its own answer (`api.py` `Factor.range`, SPINE §3 "inside its declared range"), so a Library block can declare a huge range.
- Proven above at the tip: a modifier answering `Factor(1E+999999, (0, 1E+999999))` raises `decimal.Overflow` at `:1214`. The QMB step dies before its intents return, and the held position's `close_full` is never filled (`EXIT_BLOCKED`).
- On the node, per the exit-probe report (read, not run), `_drive` catches the raise and benches the unit, and that bar's exit is not minted.
- Two modifiers each near 1E+500000 overflow at `:1209` the same way.
- The PR names this as open ("A finite factor past the decimal's magnitude is still open, and named for the round that owns it"), and no round owns it.
- rc-28's fix `cb7efa414` adds a finite check on the sizer's `Amount` only, and does not add the optional `_step` wrapper the exit probe proposed.
- The trigger is exotic, but it is the same class STACK-LIST treats as a stack red: a Library block's answer drops an exit.
- **Smallest fix:**
  - Move the factor product and both `Amount` multiplies inside the existing `try` around `to_quantity` (`:1228`). Its `except` already faults on the pin and benches.
  - Or add `_step`'s wrapper around the `unit.price` loop (`unit_handler.py`), so no pricing raise drops that step's minted exits.
  - Add a sibling test in `test_fault_wall_unit.py`.

**Carried, not new.** The malformed-sizer exit block (rows rc-06 and rc-21 together) is still present at the tip. The probe confirms it. It is fixed on rc-28, which must land.

**Lows.**
- `replay_decision` has no test for the `modified` and `reduced` steps.
- The three new compile refusals have no test.
- `level-factor@1`'s reason text reads "sits inside" even when out of range.
- These are all from the DeepSeek review, still open.

**Intent.** His words: "we are going to call them accelerators... House of Money is an accelerator" (M5). "So Brex first, accelerator second" and "Aggressiveness, I think, is just based off accelerators" (M8). "This is where the leveling comes in... we create multiple levels" (M8). So a modifier that may raise, and the level as a named modifier, follow his words.
- **Agent decisions:** "no ladder law", "the block declares its own range" and product combination.
- **Weak spot:** the spine's raise-permission gate ("a default row reading `group.raise_ok`") is not built, so at the tip a raise is bounded only by the document's own `max_level` and the size band. That is acceptable while the only shipped modifier's range comes from the document's `max_level`. A Library modifier is bounded only by itself, which is the high finding's root.

**Conflicts.**
- Intent A DESIGN CALL 4 recommends striking the "declared combiner / cap row" sentence. This row already departed from it, so the two agree.
- rc-22 (in flight) plugs its `cushion-rule` modifier into this chain. Its factor goes through the same unguarded multiply.

**Later rows.** rc-22's join, and rc-28's join, which should carry this fix beside its sizer check.

### rc-24, widen the engine to risk numbers, bounded memory (PR 378), OK, intent only

**Intent.** His words: "I want to make this thing self-configurable" and "it can't be set in stone" (M7). The engine now binds sizer, exit and control numbers, keeps a bounded window, and a `scaled` number follows a fact. This is the structure for his ask.
- **Agent decisions:** window bound, `cadence.at` left refused, `min_count` reused as `min_trades`. These are sound.
- **Open item (agent ruling, logged in `findings-backlog.md`):** a `scaled` number on `account.equity` bound to a per-bar exit compiles and moves the exit's value. No shipped content binds `scaled`. **Later rows:** the compile refusal ("a scaled number may not bind anything a per-bar exit reads", and per the Opus review also the sizer) must land before RC-39 or any template binds `scaled`. No row owns it yet.

**Conflicts.** None directly. rc-28 renames the R field that this engine reads (see rc-25).

### rc-25, a sizing number and an exit number really move (PR 383), FINDING medium, intent only

**Intent.** Same words as rc-24. Stamps reach the trade rows, `own-r-step@1` is a labelled placeholder rule, K9 6 holds, and the receipt names the row that moved a number. This meets "a unit can self-configure it". Agent decisions: the brake-number refusal and the range fault. Both are sound and stricter than asked.

**Finding, medium (against his words; conflicts with the commission-gap finding).**
- `qml/src/qml/motion/engine.py:156` hands each rule `t.r_after_costs`, which holds gross R (SPINE E13). At rc-28's head the same line hands `t.gross_r` (`0b1ad1ebc:engine.py:161`). Intent A's join rule ("a logic-record or motion reader [moves] to `gross_r`") keeps it gross.
- `own-r-step@1` then moves `risk_fraction`, a sizing number, on mean R before costs. A scalper that wins slightly gross and loses after commission would step its risk up.
- His words tie costs to configuring directly: "if you are trading... in a given market for a given instrument at a given time frame, we need to know what are the fees, what are the costs, so that the unit can know. That's how configuring, that's a variable or a point for configuring." (M7, 1 Nov)
- **Smallest fix:** at whichever of rc-28 and this stack joins second, the engine hands a sizing or control number's rule `net_r` and a logic number's rule `gross_r`. Pin it with one test: a trade that is +0.05 R gross and −0.05 R net moves `risk_fraction` toward cautious.
- On the node this changes nothing until it has a cash port (intent A DESIGN CALL 3), but QMB has cash today.

**Carried lows (Opus review).** A rule answering NaN escapes at the range compare (`unit.py:2062`). QMB crashes; the node benches the unit. No exit is lost, because motion runs only when flat.

**Later rows.** rc-26 (open trades keep their numbers, which closes the in-flight-entry low) and rc-28's join (the R field above).

## Conflicts with the intent reports' findings

| Intent-report finding | Rows here | Effect |
|---|---|---|
| rc-22 reads gross as net (A fact 2) | rc-25 | Same class. `own-r-step` reads gross R through the engine, and A's join rule would keep it gross. His M7 words argue net for sizing. Finding above. |
| Commission gap on the node (A DESIGN CALL 3) | rc-25, rc-21 | Node `net_r` equals gross, so a net fix on the engine moves nothing on the node until the cash port. rc-21's chain is where rc-22's cushion factor (net or gross) lands. |
| Fixed YELLOW kill rule (A fact 5) | none | `Runtime.guard` is untouched by rc-30, rc-31 and rc-32. |
| `stage_values` ignored by `sections.py` (B F2) | rc-23 | rc-23 adds the field and refuses it, so it cannot be reached. RC-56 owns the fix. |
| `sections.py:57` misses `exit_set` reads (B F1) | none | Not touched. |
| "Paper" is the fake broker (A DESIGN CALL 7) | rc-30, rc-31 | rc-30's seam proves hosting and bar counts on the fake broker, not a fill. Wording only. |

## Trips for in-flight and later rows

- **rc-28 (in flight).**
  - Its branch sits on `266f34e4`. Its diff against the tip shows rc-25's range check (`unit.py:2062-2064`) as deleted only because the branch lacks it. The join must keep it. A plain three-way merge will.
  - Its sizer finite check does not cover the rc-21 modifier overflow.
  - Its engine hands `gross_r` to every rule (rc-25 finding).
- **rc-22 (in flight).** Its `cushion-rule` is a modifier in rc-21's chain, so it goes through the same unguarded multiply.
- **RC-37 and RC-39.** rc-30's quiet-minute drop, and rc-31's slow-stream stateful blocks.
- **RC-39 or any template binding `scaled`.** rc-24's scaled-to-exit refusal must land first.
- **RC-43.** Count parked entries in rc-32's limit.
- **RC-50.** Read rc-32's bet key.
- **RC-56.** rc-23's `stage_values` and `sections.py`.

## OWNER CALLs

1. **Number reasons at stop B (rc-23).** You said a number like 5 % "has to have a reason as to why it's 5, not 10... a derivation". Every number now has a slot for its reason and a range, and the system refuses a number without one. But today every shipped number's reason honestly says "a placeholder until we talk numbers", and no number has a worked-out derivation yet. Is that acceptable for stop point B, or must the numbers talk happen before the templates trade on your demo account?

2. **The rc-30 blocker an Opus reviewer found (rc-30).** A second reviewer found that on a real feed, a 15-minute bar is lost whenever its first, second or last minute had no price. I reran that check on today's tip and the bar is still lost. The stack still lists this row as clean. It needs a small fix, which the review already describes. Do you want it fixed on a new row now, before anything else stacks? Or should it be logged and fixed with the scalper templates (RC-39)? The 60-second bar this row introduced is what makes the gaps possible.
