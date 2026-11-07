# V2 walks: thirteen cases against the contracts and the code

Contracts are `SPINE.md` in this folder. Code read at `D:\QMX-worktrees\bld-repair-24`, tip `351e7521`. Nothing here ran except the two small checks under `D:\Temp\v2-pod` (`probe_unit_step.py`, `check_chain.py`), which show mechanisms only. Each walk ends with **Strains** or **Fails**, stated plainly. No dollar case.

**Where this shape strains most, in order:**
1. A size trail and a replay that must cross two stages and a queue. Designed through (AD-6); untested until slice 3.
2. Backtest against live for grouped units (walk 13). A one-unit QMB run can't see the group.
3. Venue waits, not arithmetic, set one node's limit (walk 8). UNKNOWN until R24.
4. An exit that must react faster than a closed bar (walk 2).
5. The amount of contract before a lone unit gets anything from it.

---

## 1. A newcomer installs and gets a unit on paper

1. **Install.** `tools/build_release.py` and `release/install.py` exist; `E5` G1 to G3 say a stranger can't run them yet. Release lane's.
2. **First start.** `python -m qmx_host first-start` (BUILT). This shape adds: it writes the house pod with its three labelled rows.
3. **History before a broker.** `unit_check` needs a record per market, and records come from a bound account (`E5` G8, UNKNOWN). If so, ship FX and gold seed records with the templates. Add a row if the trace says no.
4. **A unit.** Picks `scalper-mr`, `intraday-trend` or `canary`. `unit_new` writes it with an empty pod. Placement never shows: each row takes the block face's first `runs_at`.
5. **Test and paper.** As `SPINE.md` section 7, steps 2 to 9. Paper needs a binding, so day two for a real broker, because cTrader's app approval takes about a day (`E5` G6). Rehearsal needs none.
6. **Watch.** The scripted fleet watch is on by default; its row says "too thin to judge".

**Strains.** The newcomer sees none of the pod machinery, and that's the point: the house pod and the empty pod are invisible until wanted. The strain is behind the scenes: this walk can't pass K7 until slice 10, later than other shapes could manage, because chain, facts, controls, gate and stickers all sit under it. **Fails today** at step 1, on release, not on this design.

## 2. A gold scalper with fast invalidation and no fixed stop

1. **Document.** Exit set: fast-invalidation per-bar exit, time exit, no price stop. `protection.stop = NoStop(basis: tail_budget)`. The wire already holds `none_declared` (`unit_intent.py:69-72`).
2. **Sizing.** A tail-budget base answers `Amount(money_at_risk)`, where risk is the declared basis. `spell` needs a distance, so the block also declares a basis distance. Or it answers `notional` and `spell` needs none. I13.
3. **Host.** Four places widen (SWAP row 11): compile (`compiler.py:500-506`), `enter` (`unit.py:764-766`), handler (`unit_handler.py:560`), node entry (`runtime.py:1065`). `HeldPosition.risk` and `_with_excursion` divide by stop distance, so both read the basis.
4. **Veto link.** `require_venue_resident_protective_stop` is a link now. It passes on a declared no-stop basis, warned in large type.
5. **A bar.** Pass 1: the invalidation block reads `PositionFacts` and its fact, answers `CloseFull`; settle sends it first, before any entry anywhere.
6. **Bad day.** If the unit's bar step hangs, AD-9's fault path closes, and with no venue stop that default isn't optional.

**Strains, twice.** (a) "Fast" stops at the bar. The stream is closed bars (`compiler.py`, `input_not_built`) and 1m is the fastest the shape runs at first. An invalidation meant to react in seconds **fails** until a quote lane exists (deferred, section 14). (b) A node death with no venue stop leaves the position naked until restart and reconcile. The template should carry a wide disaster stop at the venue, on by default, with "no stop" one warned row away. Expressible, and honestly dangerous.

## 3. An ORB unit across several opens, one bet counted once

1. **Document.** Logic, `sessions` naming each open (S9), `position_limit` per open (S17), family tag. Tolerates sticker kind `open`.
2. **Bet key.** The proposal carries `bet_key` built from family, underlying and the open's name. Three markets at one open can share a key by the template's rule.
3. **Pass 2 at the bell.** Three proposals park at one bar time. Merge order: rank, then deployment id; within one unit, market order. Unit stage: hurdle passes on a wide stop. Group: a `same-bet-cap` link reads `open_risk_by_bet_key` plus reserved room. First proposal gets the room; the second is cut to what's left; the third refused with its code. All three rows name the cap.
4. **Lone unit.** Empty pod. The cap row sits in the house pod or the unit's own `caps` slot running at `group`. Works alone.
5. **Records.** Trade row splits by session and slice.

**Strains.** Which market gets the bet is merge order, not merit: first in order wins. A template wanting "best of the three" needs a chooser block that delays and compares, which the chain can't do inside one walk. The `wait` verb helps partly. The volume "in play" gate waits on I7 and Q2; tick count stands in.

## 4. A futures week with the copilot, ending in units with their own sizing

Assume the route exists. The week: a `futures-desk` mini app with profiles for mini and micro lands notes, a pod draft (`E2` Pod 15) and blocks through `library-items`. Overnight hill-climb jobs run on long history off-path, counted, ending in new versions. Unit drafts go through `unit_check`. Paper on his yes. He promotes. Stop the desk and units keep trading; its readings age.

In this shape: Pod 15's rows are data. `vol-target` base at `unit`; `worst-step-reserve` and `margin-headroom` caps at `group`; roll and session clocks as facts; `roll-stand-down` a control at `anchor` publishing a sticker. Mini and micro are two records; `spell` needs no branch.

**Still missing, with the route assumed:** `roll` compiled and a roll as a version event (`compiler.py:938-943`); contract-month records; a methodology (other session); a copilot that can read video (M51) with pod tools (`qmx_control/lab.py` says off its surface); `build-pod` and `build-mini-app` skills (placeholder); apps reading journals (`supervisor.py:891`); an installer for an app's workflows (`manifest.py:373`); workflows reading Library items (`E5` section 6 row 5); cost pools for a new class. **Strains:** the core carries it as rows. Nearly every gap is outside this shape, and most belong to the agentic upgrade.

## 5. A very aggressive setup, few units on one basket, then a stage change

1. **Pod.** Sizer slot filled: a Kelly-type base at its full setting. Throttles empty. Caps empty. Allocation: an anchor block keeping few best units on one basket, publishing a share fact. Controls: none beyond what the user keeps. Kill line absent. `unit_check` warns; ruin audit grades; large type. Compiles. House rows: the pod can't remove the house pod's kill effect link (fixed line), and the user may edit the house day stop and parent limit, warned.
2. **Trade.** Unit stage sizes large; group stage has nothing to cut.
3. **Stage change.** Two ways, both expressible. (a) Selected rows: the sizer slot uses `compose: select` over a `stage` fact, with both row sets in the one pod version. An anchor block publishes `stage`. The owner's single click on that hash already covered both, so the switch needs no second click. (b) A new pod version: draft, diff, click.
4. **Open positions.** Unaffected; exits are logic.
5. **Exit width by stage.** An exit number reads the `stage` fact inside its range, mode `at_new_position`. A swapped exit block is a new logic version and a counted try.

**Strains.** (a) needs the stage line declared in advance, so a moved line means a new click. He may find that heavy, though Q6's default asks for it. The scalper voice's "tighter cuts without a new version" holds for numbers and **fails** for block swaps, by F5 B. The feasibility fact shows what the basket can trade; concentrating is a block.

## 6. A unit from the Lab, from a workflow, from a mini app

- **Workflow.** `unit_new`, `unit_check`, `backtest_run`, G report, his promote. Works once sockets land. Empty pod, own blocks.
- **Mini app.** Lands `unit` and blocks through the new lander (`E2` (e) rows 1 to 3). A landed draft is a draft; the money rule holds. Library block path traced in slice 0. Joins a pod: filled slots win; its own sizer shows a warning.
- **Lab.** No Lab package exists (`qmx_control/lab.py`). In this shape the Lab's stack is the pod document and its compile target is pod plus `qmx.unit/1`, so a Lab-born unit holds a reference. `unsupported_blocks` becomes the needs list. Lab replay drives the shared handler with a merge lane.

All three end at the same deployment contract: logic fingerprint, stack fingerprint, side. `promote.py:10-12` asks for a G report, not a judge verdict, which fits M49.

**Strains.** The Lab is the weakest: this shape needs slice 14 before a Lab pod replay matches live, and the Lab's own code is another session's. One real conflict: `H3 T7` says Lab-born units need no QMB card; the G report is still required by the node. A G report isn't a verdict, so it holds, but a Lab replay must be able to produce one.

## 7. A mini app feeding another; a desk publishing a reading a unit reads

- **App to app.** Roads A and B are BUILT and unchanged (`E2` (e)).
- **Desk to unit (road D).** A desk's job produces a reading. The host stamps `source: app:fx-desk` and writes the record. The one relay passes it to the node's feed by whole-file replace. The unit's `Read` pins publisher, reading, version, stale limit, fallback. At the next proposal the gate, a modifier or a logic slot reads it as a fact with its age. Row shows publisher, version, age.
- **Desk stops.** The reading ages, the fallback applies, the unit trades on home markets or stands aside as declared.

**Strains.** (a) The relay has no production importer today and passes one MIS file (`feed_relay.py:40`); generalising it is real work in slice 9, and a reader holding a file on Windows can make `os.replace` raise (CHECK B3), so the relay retries next pass and the node copies and closes fast. (b) Latency: relay passes at 5 s by default. Fine for anchors; **wrong** for anything fast, by design. (c) Cycles between apps are unguarded. (d) Meaning drift: one word from two publishers. Pinning and shadow rows are the only defence; no central approval, on purpose.

## 8. 200 units: one pod edit, the fleet watch, herding, one node's limits

**One pod edit.** Copilot writes a draft. Diff shown: rows changed, stack fingerprint moves, logic doesn't. Owner clicks once on the hash; the click covers all members or a named ten first. The node swaps stacks between ticks for those deployments. Next proposal uses the new stack. Open trades keep their exits. Control states persist by row id; a new row starts on its `until_n`. No G record moves, because the gate reads logic (AD-3). Slice 8's test does this on 200 fakes.

**Fleet watch.** One nightly fold row per unit, rank, top K, strict bar, one card per root cause, one screen at any size; decay card off. The fold keeps running scores, so no 236,000-row reread (`E5` 1.6). From zero everything reads "too thin to judge".

**Herding on one volatility shift.** Facts move at once: `scaled` numbers read the new value in the same bar, and many units shift together. Learners publish targets; each applier moves in its own mode. F2 A's real use: a `retune-room` group fact lets a pod cap the share of members moving per day (off by default). `E5`'s filter test says a cap only delays a correct move (MODEL), and sizes weren't tested. The group stage is the honest guard for sizes: parent limit and day stop see the summed risk at admission. Rows carry the cluster, so a fold query shows it.

**One node's limits.** PROBE at the tip: a real dummy `on_instant` on two markets, median 0.34 ms, p99 0.78 ms, so about 68 ms a bar for 200 units; real blocks and more markets will cost more. A toy of 200 group admits: about 1 ms. The limit is elsewhere: each entry waits on the runtime thread for the venue and for the stop to show, up to 3 × 2 s (`runtime.py:1183-1190`), and `StuckWatch` kills the process at 30 s. At a shared bell that's a real number of sends per pass, UNKNOWN until R24. Pass 2's budget stops at a labelled share of 30 s, carries the rest to the next tick, and re-runs group links on fresh facts.

**Strains.** The hardest case in the shape. Entries late in the queue trade later than their bar, so a queued scalper entry goes stale; the row shows it and a `max_age` can refuse it. Exits are safe from entries, but exits themselves are serial on one thread: a flash crash closing 200 positions one venue call at a time is slow, and a slow account delays the next account. If that shows up, section 14's thread per account reopens.

## 9. Swapping a placeholder on a unit with a record and an open position

**Sizer swap (`fixed-fraction-at-stop@1` to a real base).**
1. Forwarding row: old pin, new pin, parameter transform (R17).
2. Own-stack change: stack fingerprint moves, logic doesn't. The node gate passes. `opened_by` holds, so the open position stays the unit's.
3. Promote or pod click on the new hash.
4. Open trade: its stop and targets are at the venue and its numbers are frozen on `numbers_at_entry`. Risk and R unchanged. New base from the next proposal.
5. Record: logic in R continues; the money record starts per version (`X1-H44`); version pull as R11 says.
6. Rip-out query drops the label; `placeholders` on rows stop naming it.

**Exit swap (`time-exit-bars@1` to a real exit).** Logic changes, so it's a new logic fingerprint, a new G report and a counted try. The old deployment keeps managing its open position to flat; the new one takes entries. `promote.py:529` already has `when: flat`.

**Strains.** The exit case. On a hedging account two deployments can overlap. On a netting account `_netted` refuses a second unit on a symbol (`runtime.py:2888-2906`), so the new version waits for flat. And a compiled-fingerprint mismatch starts a unit cold (`unit.py:990-991`): numbers rebuilt from calibration rows is UNKNOWN (`E5` 4.5). `r_after_costs` gaining real costs shifts numbers that read it (R17): the field renames gross, `net_r` is new, per CHECK B1.

## 10. A brand-new brake, instrument class, sizing base

- **Brake.** One block, one `ControlRow` with required fields, code appended. If it reads existing facts, no core edit. Shadow first if the row says so. **Holds**, on the traced Library path.
- **Instrument class.** Records, calendar package, cost pool, enum value, MIS pack. The money path reads record fields, and `E5` found `instrument_class` read in only two files. **Holds** for one on cTrader. A new venue is an adapter plus capability rows, and a real job.
- **Sizing base.** Block answering `Amount`. A leverage target answers `notional`; a fixed contract count `quantity`. **Holds.**

**Strains.** A brake needing a new statistic hits the kernel: table row, two providers, signature bump (C50, said plainly). "One folder, zero core edits" is true only for known facts, and only after slice 0 traces it. A stdlib default bumps the money app.

## 11. MIS down, guard or chain failure with open positions, a hung stage, a restart past an anchor

**MIS down mid-session.** Readings age. Each `Read`'s fallback applies. No shipped template reads it. Curves stay on the node, with an older word. Finder list ages to home markets (I5). Nothing else notices.

**A chain link raises, positions open.** `run_budgeted` returns `Fault`. That entry refuses with `link_fault`, the link's scope stands down, a card lands. Pass 1 already ran; the next pass runs too. Frontier stays Ok; the unit stays TRADING, so protective reads go on (fixes `runtime.py:3039-3046`).

**The fold or a control raises.** That event's state reads per row `fail` on entries. Exits read none of it.

**A hung stage.** Link overruns its budget: refused, worker abandoned, a new one made, scope stood down. A logic block hung in the bar step: that unit isolated, entries stop, venue stops stay, per-bar exits can't run, so its positions take the fault path (default close through `_close_scope`). A hang the worker can't escape (a C call holding the GIL): `StuckWatch` at 30 s exits the process, the supervisor restarts, reconcile adopts positions (`runtime.py:1616-1654`). Stops at the venue held throughout. PROBE: 57 ms at a 50 ms budget, exit sent first.

**A restart past an anchor.** Fold replays journals. Anchors passed settle: day boundary resets, restores due fire, expired stickers clear. Reservations rebuild from `send` rows with no outcome. Applier: `at_period_open` runs once on the first bar. Published facts past `valid_until` read stale and take their fail row. Word reads UNKNOWN until reconciled, and entries wait; exits don't. V5: a floor survives.

**Strains.** Abandoned worker threads leak until restart, so a repeatedly hanging block should trip `REPEATED_FAULT`. A hung logic block costs its unit's per-bar exits, the one case exits lose service; the fault path closes instead, which may be a costly close in a healthy market. Cold restore of calibrated values is UNKNOWN. Across places: a lost server's account-wide sticker expires or reads `unknown` on the other place, later than the loss.

## 12. House money, reverse house money, press after wins, on and off, per pod

1. **The ledger.** One `CushionLedger` per scope in the fold. Anchor `fixed` or `running_peak`, clock (day, session), scope (unit, pod, account), basis realised or marked.
2. **House money and its reverse.** One modifier block in the throttles slot, `runs_at: unit`, reads `cushion` at its scope, answers a `Factor`. A fixed anchor presses and brakes; a running peak only brakes. Shape swappable.
3. **Press after wins.** A press-gate block reads the record and `raises allowed`. Press with winnings only is a cap row on the ledger.
4. **Per pod.** Fill the pod's throttles slot, or leave it empty for the unit's own. Off: remove the row. `scalper-mr` ships it on with a day anchor because he asked; the cold factor is one.
5. **Trail.** Each shows on the row with before, after and the ledger value read. Group cuts after it.
6. **Stage or anchor crossing.** Anchor settles in the fold, also on restart.

**Strains.** A pod-scope cushion read in the unit stage sees realised profit of all members, fresh on one thread, and two units on one bar both press from the same ledger: the second sees the first's reservation only as group room. A pod that fills the slot loses a unit's own modifier entirely, by AD-2. Whether this pays is C1-style evidence: MODEL says no gain on independent trades. That argument is parked; the mechanism behaves as described.

## 13. Backtest against live on the same unit: where can they differ?

**May differ, by contract:** fills, costs, latency.

**Differ in practice, and the row or stamp says so:**
| # | Difference | How it's handled |
|---|---|---|
| 1 | **Group stage.** QMB alone runs a group of one; live has other members' open risk | `group: alone` on the run. A merge-lane replay for pods (slice 14). **The largest gap in this shape** |
| 2 | Decision time. QMB steps and rests for next bar; node sends at once and books next bar (BUILT) | Fill port; kept |
| 3 | Queue delay. Live entries may wait for a budget | Row carries queue age; QMB has none |
| 4 | Target on a wick. Node closes today; venue rest at step 3; when both touch one bar QMB says stop first (`unit_handler.py:183`), venue path unknown | `target_held_by` stamp; a test per AD-18 |
| 5 | Partial close | Refused on node until step 3; compile checks capability, so a unit needing it fails early |
| 6 | Published facts | As-of query in QMB (R13); live reads the feed with relay lag |
| 7 | Sensor and stickers | Recorded where they exist; else a labelled bar sample; the row says which |
| 8 | Costs | Cost cell or live quote, labelled; QMB uses stated cost profile |
| 9 | Equity | QMB from fills and cash; node from balance re-read; `basis` on the fact |
| 10 | Slow learners | Off-path in live, inline at anchor instants in QMB: same block, as-of data |
| 11 | Exit timing under load | Pass 1 on the node is ordered; QMB has no load |

**Same, by test:** chain arithmetic given the same facts, settle, fold, applier, `spell`. Conformance tape through all drivers; `replay_size` on real live rows through QMB's code reproduces the size from stored inputs.

**Strains.** The tape proves arithmetic and says nothing about row 1. A backtest of one pod member can't show a parent limit binding, so its result reads richer than live. A run-level warning says it, and it's a real weakness of any shape where the group runs apart.
