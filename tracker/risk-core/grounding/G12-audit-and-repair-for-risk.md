# G12: what changed since 3 Nov, and what other sessions handed to this session

Grounding for the risk-core session, 6 Nov 2026, read at about 14:30 local. Read-only. No code run, no test run. Facts first, no design and no ranking. **[judgment]** marks my own reading. Everything else is read from the place cited.

**The repair program is running while this is read.** A DeepSeek coordinator took over at 14:16 (`S/RESUME.md:5-9`). `git ls-remote` at 14:31 matched the heads below. They will move.

## Paths and the tips

| Alias | Path |
|---|---|
| `A` | `D:\QMX-worktrees\audit-ship` |
| `S` | `D:\QMX-worktrees\repair-ship` |
| `P` | `D:\QMX-worktrees\unit-plan\tracker\risk-sizing` |
| `PL` | `P\build\repair\plan-parts` |
| `U` | `D:\QMX-worktrees\unit-ship` |
| `RC` | `D:\QMX-worktrees\risk-plan\tracker\risk-core` |

**There is no single newest tip.** The stack split into tracks, and `S/STACK-LIST.md:18-33` says so. Ancestry was checked with `git merge-base --is-ancestor`.

| Tip | Worktree | Holds | Does not hold | State |
|---|---|---|---|---|
| **J** = `a4f64510` | `D:\QMX-worktrees\bld-repair-10` | R01-R06 stacked, R07-R10 joined on them. The newest joined tip | R11-R13, R15-R21 | R01-R06 gated. R07-R10 reviews not moved yet (`S/RESUME.md:12`) |
| **N** = `ef011af4` | `D:\QMX-worktrees\bld-repair-21` | R01-R03, old forms of R07-R12, R20, R21. The newest node code | **R04, R05, R06**, R15, R16, R19 | R20 CLEAN, gate passed. R21 built, tests and review not run (`S/STACK-LIST.md:33`) |
| **R** = `7ada84ed` | `D:\QMX-worktrees\bld-repair-19` | R01-R03, old R07-R12, R15, R19 | R04-R06, R16, R20, R21 | R15 gated on its track. R19 not reviewed (`S/STACK-LIST.md:31`) |
| **Q** = `97d65941` | `D:\QMX-worktrees\bld-repair-16` | Same base, R15, R16 | as above | R16 lanes running (`S/RESUME.md:24`) |

- Not started: R14, R17, R18, R22, R23, R24 (`S/RESUME.md:14`). R14 and R17 builders are being set up now (`S/dispatch/r14.md`, `S/dispatch/r17.md`).
- R11 at `155d0b1f` was NOT CLEAN with two blockers, and a last fix round went out at 14:30 (`S/RESUME.md:20`). It parks for good if not clean (`S/QUESTIONS-FOR-OPERATOR.md:9`).
- All of this stacks on `build/us-c14` at `50c83a4e`, 94 unmerged PRs (`S/STACK-LIST.md:3`).
- G8, G9 and G11 read `d02af358`. That is 17 PRs before `50c83a4e`: C-12d, C-12e, C-14, C-17, C-25 to C-38 (`U/STACK-LIST.md:82-98`, `git log d02af358..50c83a4e`). So some staleness below comes from those, not from the repair.

---

## 1. Everything handed to the risk session

The base list is unchanged: 31 placeholder rows in `P/build/RISK-SIZING-PLACEHOLDERS.md:15-47`, four slot contracts at `:51-56`, four questions at `:60-63`. The older copy at `U/evidence/a15/RISK-SIZING-PLACEHOLDERS.md` is the A15 query result. Its line "No halt block ships" (`:44`) is out of date (G8 §2.3).

The newest full hand-off is **Appendix F** of the repair plan, `PL/90-appendices.md:184-207`. The table below is that list, plus what `rows-out.tsv`, the audit, the old backlog and the reviews add. **Kind** says what is asked: *decision* (a rule to choose), *design* (a shape to draw), *value* (a number).

### A. The exit half ("agree the socket with it first")

| # | Item | Evidence | Kind | Plumbing state |
|---|---|---|---|---|
| 1 | The exits socket itself. Step 2: feed every per-bar exit real evidence and the side, about 60 lines. Step 3: trails, partial closes, stop moves, about 250 lines | `A/REPAIR-SCOPE.md:76`, `A/MORNING-REPORT.md:68`, `A/reports/ground-unit.md:47-50,68`, `PL/90-appendices.md:202` | design | Waits on this session. No PR number. `P/build/repair/PLAN-SHAPE.md:88` |
| 2 | Six exits refused until then: `unrealised-profit-cap`, `roi-table-exit`, `peak-holdings-giveback-exit`, `offset-gated-trailing-stop`, `stepped-profit-stop`, `profit-fraction-trailing-stop` (p1a-2, p1b-1, p1b-3) | `PL/90-appendices.md:192`, `A/FINDINGS.tsv:82,98,100`, `PL/rows-out.tsv:3-4,26` | design | Refused at J `qml/src/qml/compile/compiler.py:350-364` |
| 3 | The signed stop distance. May a stop go past entry, and how is that sent? Decides whether trails can lock in profit on the node (known-1, triage-1) | `U/RISK-NOTE-2026-11-04.md`, `A/FINDINGS.tsv:21,279`, `A/RULINGS-NOW.md:194`, `PL/90-appendices.md:194` | decision and design | R21 answers `Blocked`, at N `qmn/src/qmn/app/runtime.py:1278-1287`. `abs(entry - new_stop)` still at N `:1320`. The encoder's loss-side sign is `_LEVEL_RULES`, J `packages/qmf-venue/src/qmf/venue/encode.py:115-120` |
| 4 | Whether a stop may ever widen. The placeholder swing stop can widen | placeholder 9, `P/build/RISK-SIZING-PLACEHOLDERS.md:25`, `U/BACKLOG.md:37` | decision | Tighten-only stays |
| 5 | Scale-out ladders, and what a partial close means for R (p1b-4, p5a-17). A partial close may leave a rest below the minimum lot | placeholder 10, `A/FINDINGS.tsv:101,180`, `U/lows.md:274`, `PL/rows-out.tsv:27,35` | decision and design | Node blocks it, N `runtime.py:1722-1723`. QMB fills it, so backtest and node differ |
| 6 | Targets resting at the broker, or closed by the node (seams-7). One wicked bar read +2.00R in QMB and -0.55R on the node | `A/FINDINGS.tsv:269`, `A/reports/seams.md:65`, `A/reports/ground-qmb.md:112`, `PL/90-appendices.md:197` | decision | Node way stands. "Do not change QMB's fill to match" |
| 7 | May a unit have no price stop (p0a-8). Today's sizer needs a stop, so it also needs another sizer | placeholder 11, `A/FINDINGS.tsv:36`, `A/reports/p0a.md:98`, `PL/90-appendices.md:198` | decision | `stop_not_built`, J `compiler.py:500-506` |
| 8 | Whether a moved number changes an open trade's exits | placeholder 8, `PL/90-appendices.md:199` | decision | `open_positions_not_built`, J `compiler.py:996-1000` |
| 9 | Which exit wins when two fire on one bar | `A/reports/ground-unit.md:60` | decision | Open |
| 10 | Which position facts exits read: `bars_held`, `mfe_r`, `mae_r` | `A/reports/ground-unit.md:61`, `PL/90-appendices.md:201` | design | R10 computes MAE and MFE in the handler for results only, J `qmb/src/qmb/host/unit_handler.py:97-99,249-250` |
| 11 | A long-wicked bar gives a stop above the close (p1a-8) | `A/FINDINGS.tsv:88`, `PL/90-appendices.md:202` | decision | Whoever wires exits decides |
| 12 | `timer()` builds exits long-only, so shorts would never fire once fed (unit-n2) | `A/reports/ground-unit.md:46`, `PL/rows-out.tsv:62` | design note | Repair with step 2 |
| 13 | A lost stop returns at the entry's level once trails ship | `S/RESUME.md:163`, `S/evidence/r21/owner-sketch.md:109`, `S/evidence/r21/owner-how.md:123` | design | R21 reads the send row, not later amends |
| 14 | Exits read bid bars, so a short's trail is off by the spread. A short swing stop reads bid | `U/BACKLOG.md:259`, `U/lows.md:147` | design | Open |

### B. The sizer

| # | Item | Evidence | Kind | State |
|---|---|---|---|---|
| 15 | Placeholder sizer wrong on USDJPY. It divides account money by a loss in the quote currency | `A/reports/p0a.md:99`, `A/REPAIR-SCOPE.md:134`, `PL/90-appendices.md:190`, J `qml/src/qml/blocks/stdlib/fixed-fraction-at-stop/1/block.py:52-53` | design (rip-out) | Unchanged |
| 16 | Costs and edge numbers missing from the sizer (plan-check-7). The Kelly sizing he asked for needs them | `A/FINDINGS.tsv:258`, `A/RULINGS-NOW.md:205`, `PL/rows-out.tsv:52` | design | Unchanged, J `qml/src/qml/protocol/unit.py:785-793` |
| 17 | The sizer's receipt is a literal (p0a-12). Add the residue to `Size` | `A/FINDINGS.tsv:40`, `A/reports/ground-unit.md:98`, J `unit.py:827-830` | design | Goes with this session's sizer |
| 18 | Sizer sizes on a wrong-side stop. `risk_fraction` is bounded only at 1, so 50% passes if a range allows it | `U/LOOSE-ENDS.md:179`, `U/BACKLOG.md:37`, `U/lows.md:88` | value | Placeholders |
| 19 | Socket contract tests are weak: sizer tests long only, an exit that never answers passes, Library-only blocks not enrolled, the slot follows today's runtime and not CONTRACTS 4.3 | `U/lows.md:475-478`, `U/review/a15-check-9ec37fc4.md:32` | design | Unchanged |
| 20 | A trade's real risk differs from planned, because it fills at the next open | `U/lows.md:219` | decision | Open |
| 21 | Margin a metal really takes. Read `ProtoOASymbol.leverageId` before risk-core reads margin | `U/BACKLOG.md:500`, `U/review/c34-check-102f7eda.md:68`, `A/verify/triage-items.tsv:95` | design | Record writes the account's leverage, J `qmx-agents/packages/qmx-host/src/qmx_host/venue_records.py:243-253` |

### C. R and costs

| # | Item | Evidence | Kind | State |
|---|---|---|---|---|
| 22 | Whether a trade's R includes costs (p0b-13, p2-6, seams-10), and the misleading name `r_after_costs` | `A/FOR-HIM.md:19`, `A/FINDINGS.tsv:65,125,272`, `A/reports/ground-qmb.md:99`, `PL/90-appendices.md:203` | decision | R stays. One named read `trade_r`, J `qmx-agents/packages/qmx-judge/src/qmx_judge/judge.py:224-227`. `net_r` and `cash` sit beside it, J `qmx-agents/apps/qmb/jobs/backtest.py:96,112-113` |

**[judgment]** `trade_r` flips the judge in one line. It does not flip the unit's own motion, which reads `r_after_costs` at J `unit_handler.py:724`.

### D. Kill and protection

| # | Item | Evidence | Kind | State |
|---|---|---|---|---|
| 23 | What each kill level means, YELLOW to BLACK | placeholder 18, `A/FOR-HIM.md:18`, `PL/90-appendices.md:157,204`, `qmn/src/qmn/protection/effect_matrix.py:137-146` | decision and values | Table stays a placeholder. R21 makes it act |
| 24 | The third-refusal alarm count `CLOSE_REFUSALS_ALARM` | `S/evidence/r21/pr-body.md:19`, N `runtime.py:176` | value | Placeholder |
| 25 | Protection that cannot be placed: close, hedge or alarm only. No failure-register row of its own | placeholder 19, `U/BACKLOG.md:406` | decision | As built |
| 26 | The kill line's verb and floor | placeholder 20, `A/reports/plan-check.md:32`, `A/RULINGS-NOW.md:195` | decision and value | Off the path |

### E. SQS

| # | Item | Evidence | Kind | State |
|---|---|---|---|---|
| 27 | Where SQS sits (plan-check-2). Ruling: "Kill switch and SQS stay" | `RC/STATE.md:327`, `A/RULINGS-NOW.md:196`, `A/FINDINGS.tsv:253`, `A/FOR-HIM.md:17`, `PL/90-appendices.md:163,205` | design | See section 2 |

### F. Halts, hook, cross-unit

| # | Item | Evidence | Kind | State |
|---|---|---|---|---|
| 28 | `equity-drawdown-halt` is silent at zero equity (p1a-7). It has no release path, and a binding's scope is not checked against what it reads | `A/FINDINGS.tsv:87`, `PL/90-appendices.md:207`, `U/BACKLOG.md:259` | design and value | Compile refuses all halts |
| 29 | No host runs halts or passes their statistics | `U/BACKLOG.md:163,255`, `U/LOOSE-ENDS.md:169` | design | Unchanged |
| 30 | What the cross-unit hook holds. Host call or slot | placeholder 6, `P/build/RISK-SIZING-PLACEHOLDERS.md:60`, `U/evidence/a15/RISK-SIZING-PLACEHOLDERS.md:43`, `S/evidence/r15/owner-how.md:28` | design | Passes every order |
| 31 | Kill-line distance and daily loss budget in node rows. `rk2`, `rk5`, `p1`, `pp` drafts wait on it | `U/evidence/b21/owner-pr-body.md:75,77` | design | Unchanged |
| 32 | The Book and correlation control. Where a correlation ledger sits | `A/RULINGS-NOW.md:129,193` | decision | Book path and `qmf-risk` wait for this session (section 4) |
| 33 | Whether units may use grid, martingale or averaging families | `A/plan-current.md:1653`, `U/dispatch/a13d.md:9` | decision | Dictionary entries only |

### G. The judge and the "version pull"

| # | Item | Evidence | Kind | State |
|---|---|---|---|---|
| 34 | The `too_thin` number. "The number is the risk session's" | `S/BACKLOG.md:55`, J `qmx-agents/packages/qmx-judge/src/qmx_judge/presets.py:45` (`min_trades=100`), J `judge.py:605-609` | value | On a few months a dead idea leaves no memory row |
| 35 | Version pull. "A new version trading the same trades now pays the pull. One that really moves a trade escapes it, 2 of 6 seeds, tries counted. A new item with no variant-of edge starts a new family" | `S/BACKLOG.md:51`, `S/review/r11-check-155d0b1f.md` blockers 1 and 2 | decision | R11 fix in flight |
| 36 | u2 "Where a failed unit's rules still hold" can never answer that they hold on a real run. "For a later PR or the risk session" | `S/BACKLOG.md:69`, `S/review/r12-check-fdccd475.md:42-47` | design | Stack list must not say u2 works |
| 37 | A behaviour check with no orders still records a pass, and a move reads it | `S/review/r10-check-520aec27.md:39-43` | decision | Not filed anywhere (below) |

**[judgment]** Item 35 matters for the rip-out. A pure sizer swap leaves trades the same in R, so it reads the parent's number. An exit change moves trades, so it escapes the pull at some seeds.

### Messages meant for this session

**One real message was sent and did not arrive.** The build coordinator (session `ceaa48e1`) sent it at 2026-11-04T13:00:19Z, to the session named "QMX risk management and position sizing". Its text, verbatim, from the transcript `C:\Users\Mubarak\.claude\projects\C--Users-Mubarak-Desktop-QMX\ceaa48e1-e67a-4da3-8222-5320a46b084b.jsonl` line 22630:

> The operator routed this finding to you from the unit-system build: a stop moved past entry lands on the wrong side, and the node reports the wrong stop.
>
> Full note: D:/QMX-worktrees/unit-ship/RISK-NOTE-2026-11-04.md. Proof: D:/QMX-worktrees/unit-ship/review/c37-check-46a2edd0.md. Code is on branch build/us-c28 at db948daa.
>
> - qmn/src/qmn/app/runtime.py:1170-1180 sends gap = abs(entry - new_stop), and every venue reads that as the loss side. On the fake cTrader, a short entered at 1.06858 with its stop tightened to 1.06808 sent stopLoss 1.06908.
> - runtime.py:1204 then reports Placed(1.06808), the stop that was asked for, not the one the broker holds.
> - Effect: it adds no risk beyond the held stop, but a stop can never lock in profit, and his screen shows a stop the broker does not hold.
> - seats/dispatch.py:917-930 signs ProtectionAmendment.new_distance the other way, so one convention needs pinning.
>
> He wants you to own the decision: whether stops past entry are in scope for the first demo, and how the fix lands. If you want it built in the node stack, send me the scope and I will dispatch it. He plans to start QMX for the first time after your session is running.

The tool's answer, line 22635 of the same file:

> Message not delivered to session local_90bdf1b0-517c-49a5-923e-d8e59418d2ee ("QMX risk management and position sizing"): "that session gave no sign of starting on it within 20s (it may be waiting for approval there, or slow to start); it can still pick it up later". (delivery: undelivered; message_id: 09c70546-76c6-4df6-9950-af4906c8eae7)

This session's transcript `2928e6ee-...jsonl` shows a resume at 13:00:37 and his M42 at 13:03:19 (`RC/seeds/operator-words-2026-11-06.md:15`). "RISK-NOTE" appears in it 0 times. So he spoke of the message, and its text never landed here. The same text sits in `U/RISK-NOTE-2026-11-04.md`. I searched the four session logs that name that session id for other sends, and found no other.

What has moved since that note:
- Its line numbers are stale. The abs line is now N `runtime.py:1320`, and it was `:1223` at `50c83a4e` (`A/FINDINGS.tsv:21`).
- `Placed(asked)` is fixed on N, which now answers the broker's stop and raises `stop_differs` (`runtime.py:1291-1300`). Not on J.
- "The first demo" has moved. Foundation comes before the demo (`A/STATE.md:7`), and the dummy no longer goes to demo (`A/FOR-HIM.md:16`).

**Findings written for this session that were never filed on any list:**
- R10 review low 1 asks "put it in `BACKLOG.md` for the risk session" (`S/review/r10-check-520aec27.md:43`). `S/BACKLOG.md` has no such row, and `S/lows.md` has no R10 section.
- R21's "a lost stop returns at the entry's level once trails ship, for the risk session" is only in `S/RESUME.md:163`. `S/BACKLOG.md` has no R21 section.
- "R16 and R19 findings are in this session's reports and not yet filed in BACKLOG.md" (`S/RESUME.md:161`). I did not see those reports.

**Notes that say this session needs nothing:** `A/STATE.md:36`, `P/build/repair/PROMPT-REPAIR.md:151`, `PL/90-appendices.md:186`. Appendix F was written and never pushed here. It waits to be read.

---

## 2. The SQS rule text

**The gate.** The audit first named `runtime_risk_gate.py`, and that was wrong. That file is a proof harness (`A/reports/ground-node.md:135`, `PL/90-appendices.md:83`). The real gate is below.

**Verbatim**, `D:\QMX-worktrees\bld-repair-10\qmn\src\qmn\host\decision_root.py:493-510`:

```python
        for intent in intents.value:
            if isinstance(intent, ExitIntent):
                continue
            reading = snapshot.sqs_for(intent.instrument)
            if (
                reading is None
                or reading.readiness is not ProducerReadiness.OK
                or reading.hard_block
                or reading.score is None
                or reading.baseline_key.venue != self.path.venue_id
                or reading.baseline_key.environment != expected_environment
                or reading.baseline_key.instrument != intent.instrument
            ):
                return policy(
                    "sqs",
                    "hosted entry requires the same frontier's ready, non-blocked SQS reading",
                    instrument=intent.instrument.symbol,
                )
```

In plain words: exits are never checked. An entry goes only if a reading exists for that instrument at this same instant, reads ready, is not hard-blocked, has a score, and its baseline is this venue, this environment and this instrument.

**The rule behind it, which lives outside the cut.** `packages/qmf-readings/src/qmf/readings/labelers.py`, safe from C-20:

```python
# :338
    """AD-39 Spread Quality Sensor: baseline ÷ live spread, conservative sentinel."""
# :350
            "a bar-sampled SQS is refused at the door, never blocked through (DEC-0153)",
# :371-372
            "SQS freshness is the Book decision_freshness_bound — mandatory, "
            "no second bound, no invented default (DEC-0153)",
# :418
            "a demo-conditioned SQS baseline never satisfies a live environment (DEC-0230)",
# :636-650
    """At-or-above threshold passes; strictly below blocks. Hysteresis on clear."""
    score_q = score.as_fraction()
    threshold_q = threshold.as_fraction()
    blocked = score_q < threshold_q
    if not blocked and previous is True:
        clear_line = threshold_q + band.as_fraction()
        if score_q < clear_line:
            blocked = True
        elif isinstance(dispersion, PriceDelta) and dispersion.value != 0:
            deviation = abs(live_spread.as_fraction() - average.as_fraction())
            limit = guard_multiple.as_fraction() * dispersion.as_fraction()
            if deviation > limit:
                # Outlier excluded from the re-crossing test — stay blocked.
                blocked = True
    return Ok(blocked)
```

**Also inside the cut's reach:**
- `qmn/src/qmn/replay/port.py:87-91`: "replay reuses the recorded per-instant signal snapshot; missing snapshots read not_ready and refuse entries — SQS is never recomputed".
- `qmn/src/qmn/replay/port.py:123`: "Missing/non-ok SQS is a conservative hard block (DEC-0206)."
- Baseline statistic: mean or median, "no implicit choice or quantile shape", `qmn/src/qmn/host/sqs_baseline_producer.py:81-85,132`.
- Named settings with no values, each blocking live and soak when blank, `qmn/src/qmn/config/registry_catalog.py:158-241`: `sqs_hard_block_threshold_per_class`, `sqs_hysteresis_band`, `sqs_outlier_guard_multiple`, `sqs_sample_cadence`, `sqs_baseline_conditioning`, `sqs_baseline_refit_schedule`, `sqs_staleness_horizon`, `decision_freshness_bound`.

**Who deletes it.** No repair PR, R01 to R24.
- `git diff --name-status 50c83a4e..a4f64510` and `..ef011af4` over `qmn/src/qmn/host` list nothing. Line 508 reads the same at all nine heads I checked.
- The one that deletes it is section **C-20**, "the old node cut". Its Files box deletes `qmn/src/qmn/host/` (`A/plan-current.md:4173`). It sits in Appendix B, "After G-DEMO" (`PL/90-appendices.md:77-83`), with no PR number.
- It has not happened. It waits on `c14-real.log` and `c15-demo.log`, which wait on his sign-in.
- Before it runs, `sqs_baseline_producer.py` moves out, and the rule text goes to this session (`PL/90-appendices.md:83,132`). This section is that hand-over.

**What the new node has.** Nothing. `git grep -i "sqs|spread_quality"` over `qmn/src/qmn/app`, `qml/src`, `qmb/src/qmb/host/unit_handler.py`, `qmx-agents/apps/mis` and `qmx-agents/apps/trading-node` finds 0 files at J, N, R and Q. The MIS packs carry `spread_state@v1`, not SQS (J `qmx-agents/apps/mis/packs.json:4`). No production caller builds a baseline: `D:/Temp/audit/deletion/reach.tsv` classes the producer `tests`. The reason code `spread_wide` exists and nothing writes it (R `packages/qmf-data/src/qmf/data/journal_kinds/unit.py:48`).

**The seat the plan assumes:** "one line in `Runtime.guard`" (`PL/90-appendices.md:205`). The plan's lines `2269-2314` are from `50c83a4e`. It is J `runtime.py:2266`, N `runtime.py:2531-2581`.

---

## 3. Which G8, G9 and G11 facts are stale

Status words: **unchanged**, **changed** (in code, with the tip), **planned** (no code yet). "Stacked" means it passed everything. Other tips can still move at the join.

### Unit, compiler, sizer (read at J)

| Fact in G8 | Now | Status |
|---|---|---|
| "compiler format 1" (G8:35-36) | Format 4, `qml/src/qml/compile/compiler.py:100`. R04, R05, R06 each moved it | changed, stacked |
| Compiler refuses halts and reads (G8:35-36, blocker 1) | Same rule, now `compiler.py:900-903`. The checker still says "add a halt", `qml/src/qml/check/layers.py:684-690` | **unchanged** |
| Nine fields parsed and ignored (G8 blocker 6, §1.1) | They now **refuse**: `sessions` `:904-910`, `context_needs` `:912-916`, `routes` `:919-923`, `plain_python` `:925-929`, `roll` `:939-943`, `settings` and `settings_record` `:945-957`, `position_limit` other than 1 `:959-961`, `applies_to_open_positions: true` `:996-1000`, motion fields a kind does not run `:1003-1007`, `cadence.at` alone `:1009-1014` | changed, R04, stacked |
| Same | New refusals beside them: exit `scope` other than position `:472-477`, a fixed number nothing binds `:585-590`, a role that does not run `:107-117,438-443`, combiner extras `:431-437` | changed, R04 |
| Same | A census test fails on any new schema field until someone decides run, refuse or label (`S/evidence/r04/pr-body.md:33`, `qml/tests/test_unit_refuses.py:457`) | changed, R04 |
| `authority` never read (G8 §3.10) | Still a label with one value (`S/evidence/r04/pr-body.md:97`) | unchanged |
| `sizing_modifier` gates only (G8 §1.1, blocker 7) | Now refused, not in `ROLES_BUILT`, `compiler.py:107-117` | changed, R04 |
| Moving numbers: two modes, sizer-bound number cannot move (G8 §3.10) | Same. A calibrated number needs a logic binding that stamps it, `compiler.py:617-643`. A derived one needs a logic host, `:599-613`. `risk_fraction` is still fixed, `qml/src/qml/unit/templates/dummy-trend-pullback.json:105` | **unchanged** |
| `trend-floor-from-record@1` | Dummy pins `@2`, which learns from shorts (`dummy-trend-pullback.json:88`). The calibration row holds mean R and mean stamp (`S/evidence/r05/pr-body.md`) | changed, R05 |
| Halts in a logic slot | Refused as `binding_not_read`, because they read account or trades ports (`S/evidence/r05/pr-body.md`, "The call on the five halts") | changed, R05 |
| Sizer gets four things (G8 §2.4) | Same: `equity`, `entry_price`, `stop_price`, `record`, `qml/src/qml/protocol/unit.py:785-793`. `Account` holds equity only, `:141-142`. New: `/sizer/inputs/<port>` refuses, `compiler.py:930-936`, so a sizer cannot read another block | **unchanged**, one new refusal |
| Receipt hard-coded (G8 §1.4) | Same, `unit.py:827-830`. `Size` has no residue, `qml/src/qml/blocks/api.py:105-108` | unchanged |
| Price rounding | Rounds to the record's tick (`S/evidence/r05/pr-body.md`, p0a-11) | changed, R05 |
| Exits: only the first per-bar runs, fed `{}` (G8 §1.4) | Still fed `{}`, `unit.py:686`. A stop still reads `{}` once at entry, `:757`. A second exit of a use now refuses, `compiler.py:492-495`, and so does any per-bar exit with inputs or a stop reading the position, `:358-363` | changed from silent to refused, R04. **Running them: planned, no PR, waits on this session** |
| Six exits silent (G8 §3.5) | Refused by shape, so an agent's block of that shape refuses too. The message names this session, `compiler.py:361-362` | changed, R04 |
| A unit with no time exit crashes | Fixed. `timer()` answers None, `unit.py:447-449` (p0a-2) | changed, R04 |
| `OwnPosition` lacks stop, targets, bars held, excursions (G8 §5.1) | Same, `unit.py:130-138` | unchanged |
| Close partial, amend never sent by a unit (G8 §1.4) | Same. A search of `unit.py` finds neither | unchanged |
| `position_limit` one per market | Still one. A higher one now refuses | changed, R04 |
| No row saves a block (G8 §4.3) | Same. `catalog.py` rows `unit_*`, `blocks_*` only, `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py:411-468`. A save now checks names across the store (`S/evidence/r06/pr-body.md`) | unchanged, one check added by R06 |
| `lifecycle.auto_paper` | Deleted | changed, R06 |
| Rip-out costs a unit its record (G8 §3.6) | Identity table unchanged. R11's pull changes what a same-trades version reads | unchanged, R11 parked or in fix |

### Runtime and brakes (read at N, then R and J)

| Fact in G9 or G11 | Now | Status |
|---|---|---|
| Halts never run (G9 §0.2) | Same. `HaltInstance` and `before_order` have no caller in `qml/src`, `qmb/src`, `qmn/src/qmn/app`, `qmx_host` or the apps at J, N, R, Q (grep). "No host runs halts yet", `qml/src/qml/blocks/api.py:182-184` | **unchanged**. No PR plans it |
| `Runtime.risk_stop` called only by tests | Same. Definition at N `runtime.py:2602`, no production caller | **unchanged** |
| Cross-unit hook passes all | Same, N `runtime.py:1065-1069`. R15 says leave it (`PL/r15.md:28`) | unchanged |
| Sizer equity is start plus closed trades (G11 §2.1) | Same, `unit_handler.py:372` at J and `:370-372` at N | unchanged |
| cTrader equity is the balance read at sign-in (G9 §3.3) | Same. `equity()` returns `balance`, N `qmn/src/qmn/venue/ctrader_account.py:698-699`. Set only in `_authorise`, `:1062`. The unit reads it once at start, N `runtime.py:2713` | **unchanged**. C-12d landed it |
| Equity 0 after a restart with no network | Open. R22 plans a wait, then "the real balance" (`PL/r22.md`, p5a-5, seams-6) | planned, R22, not started |
| Marked equity | None. No "unrealis", "marked" or "floating" in `qmn/src/qmn/app` or `ctrader_account.py` (grep at J). PH row 17 still claims balance plus unrealised (`P/build/RISK-SIZING-PLACEHOLDERS.md:33`). The node's cost data waits for after G-DEMO. **No PR plans marked equity** | **unchanged** |
| No commission key (G9 §5.1) | Same. `qmx-agents/packages/qmx-library/src/qmx_library/kinds/instrument.schema.json` has `margin` `:119`, `swap` `:134`, `financing` `:143`, `measured` `:145`, and no commission. Neither `venue_records.py` nor the node's `server.py` holds swap or commission (grep at J) | **unchanged**. After G-DEMO (`PL/90-appendices.md:81`) |
| No writer of a cost profile (G9 §5.2) | Half changed. A stated profile can be named and reaches the run, J `qmx_host/host.py:2090-2125`, with `fills` forced to 0 so it stays uncalibrated (`S/evidence/r10/pr-body.md`). No profile from fills | changed, R10, joined. From fills: after G-DEMO |
| A backtest reads QML's test fixture | Fixed. The Library's record reaches the run (`S/evidence/r07/pr-body.md`), so a swap on the record reaches it too | changed, R07, joined |
| Trade R in results | `cash` and `net_r` beside `r`, `mae_r`, `mfe_r`, `max_drawdown_r`, J `backtest.py:96,112-113`, `unit_handler.py:391`. Money measures land | changed, R10, joined |
| Market `minute` row has no writer (G9 §5.3) | Written, with spread at the minute's close, R `qmn/src/qmn/app/feed_keeper.py:230-246`. Fees and slippage stay out | changed, R19, not reviewed |
| Node trades never reach the Library | Fixed: `account` set in `RunJournal` (`PL/r15.md:24`). A paper deployment scores. A live-lane deployment on demo gets a trade and no paper score (`S/review/r15-check-91e25415.md`, low 3) | changed, R15, gated on its track |
| Reason codes | A live journal writes `unlisted` for a text with no code, R `qmb/src/qmb/results/journal.py:76`, R `journal_kinds/unit.py:73`. A write failure stops entries and keeps exits, R `runtime.py:2285-2286`. A QMB run stays strict | changed, R15 |
| Risk stop files as `kill_switch` (G9 §1.4) | Same. Text `qmn/src/qmn/app/stand_down.py:194` holds "kill switch", which R `journal.py:57` maps first. `risk_stop`, `halt_slot`, `spread_wide`, `margin` exist unused, R `journal_kinds/unit.py:43-74` | **unchanged** |
| Trade row: exit kind only (G11 §3.4) | Same, J `journal.py:412`. No session, streak, equity before, costs or exit reason. R10's excursions go to results only | **unchanged** |
| Kill scopes: all, account, deployment, instrument (G9 §1.1) | Same four, N `qmn/src/qmn/app/operations.py:241-258`. No class or region scope. C-35 fixed the symbol-scoped hold (`P/build/TRIAGE-2026-11-03.md:39`) | unchanged, plus a C-35 fix |
| Kill table placeholder | Same, `effect_matrix.py:137-146` | unchanged |
| RED misses a position no unit holds | Fixed on N. `_close_scope` over `_mine`, `runtime.py:2311-2369`, called each tick, `:2401-2433`. Only `Claim.MINE` joins | changed, **R21, not reviewed** |
| `positions_closed` count | True only for the first try. With the connection down it reads 0 and closes later (`PL/r21.md:27`) | changed, R21 |
| Flatten does nothing (G9 §1.1) | It closes until flat, then writes one row, and a restart never replays it. It does not stop the unit, N `runtime.py:2469-2492`, `operations.py:417-418`. "RED is how he gets out and stays out" | changed, **R21, not reviewed**. At J it still does nothing |
| G11: "his resume is not journalled" (`G11:216`, `:236`) | **Stale.** C-35 journals it, N `runtime.py:2436-2458`, at `50c83a4e` `runtime.py:1821` | changed, in the base stack |
| Clock band stand-down listed as on the path (G9 §1.1) | **Overstated.** The runtime builds `StandDowns` with no clock probe, N `runtime.py:2022`, with no `clock_offset_ns` in that file, so it cannot fire (p5a-11). `"clock": None`, N `operations.py:918` | planned, R23 |
| Stale feed stand-down | Fires across a weekend (p5a-22), planned market-hours check | planned, R23 |
| Paper position | Memory only, vanishes at a restart (p5a-16) | planned, R23 |
| Spec-change row (G9 §1.1) | Still row only, `stand_down.py:93,177-178` | unchanged |
| Node constants (G9 §1.4) | Still code constants, `stand_down.py:61-83` | unchanged |
| `"paused": 0` (G11:219) | Same, N `operations.py:923` | unchanged |
| Node `positions`: no P&L, no R (G11 §4.1) | Same, N `runtime.py:1782-1801` | unchanged |
| A stop moved by hand or fired while down | Read now. The broker wins at reconcile, on events, and for a process that was down (`S/evidence/r20/pr-body.md`). Known limit: a part close by hand leaves `OwnPosition.quantity` and the trade row at full size (`S/BACKLOG.md:64`) | changed, R20, gated on its track |
| Adopted position with no stop | Put back at the send row's level, or closed with an alarm (`S/evidence/r21/pr-body.md`) | changed, R21 |
| Phone alarms (G11 §4.1) | **Stale.** On an installed node they are silently off (chief-2, `A/MORNING-REPORT.md:37`). R16 moves the register so a wheel carries it, and status says when off (`S/evidence/r16/pr-body.md`). The push list stays closed: `closed_while_down` and the like do not push | changed, R16, not reviewed |
| Netting check absent (G9 §6) | Still absent. R22 plans a one-rule refusal for a second unit on a netting symbol or Hyperliquid coin (`PL/r22.md:32`, p5a-20, p5b-6) | planned, R22 |
| Node bars: every unit gets 15-minute | R22 plans a refusal by name. The right bars come after G-DEMO (`PL/90-appendices.md:79`) | planned, R22 |
| Node saves no calibration across a restart | R22 plans a snapshot when a slow number moves (`PL/r22.md`, p5a-15) | planned, R22 |
| MIS board relay not started (G8 §6.3, G9 §4.3) | Same. No caller of `feed_relay` at J, N, R, Q (grep). `promote.py` writes no `placement` (grep at J). R18 makes the MIS publish, and the board "stays unwired, by TR:49" (`PL/90-appendices.md:120`, `PL/r18.md:22`) | **unchanged**. MIS configure planned, R18 |
| Promote: a second deployment of one version refused (G9 §3.2, `promote.py:422-447`) | **Stale wording.** A click deploys one market (J `promote.py:540-555`), and R17's plan calls one unit on two markets normal (`PL/r17.md:25`, p5d-3). The quoted line is gone (grep at J) | changed. I did not trace which PR |
| G records | Answered per market. A move on a market no check saw is checked first, J `promote.py:488-500`. The slice is `[qmb] g_slice_bars`, default 5,000 (`S/evidence/r10/pr-body.md`) | changed, R10, joined |

### What `qmf-risk` still holds

`packages/qmf-risk/src/qmf/risk/`, 18,517 lines at J. R01 removed four examples and their tests only (`git diff 50c83a4e..a4f64510`). Direct importers by file, from `git grep "qmf.risk.<file>"` at J. A `from qmf.risk import X` is not counted, so read this as a floor.

| File | Lines | Direct importers | After C-20 and the old door [judgment] |
|---|---|---|---|
| `unit_intent` | 799 | `qml`, `qmb` handler, `qmn/app` | **Stays. The live contract** |
| `paper` | 1,522 | `qml`, `qmb`, `qmn/app`, old node | Stays for `ExecutionTarget` |
| `door` | 1,481 | `qml/protocol`, `qmb`, old node | Stays while `qml/protocol/intents.py` imports it |
| `control_action`, `control_rank` | 1,903 | `qmn/protection`, `qmb/results`, old node | Stay for `effect_matrix.py` |
| `control_window` | 1,478 | `qmn/data`, `qmn/protection`, old node | Follows windows, below |
| `performance` | 1,059 | `qmb`, QMB app | Stays |
| `exit_record`, `r_faces`, `numeraire`, `templates`, `binding`, `dimensional` | 4,088 | `qmb` and old node mix | Mixed |
| `admission_bar`, `exit_policy`, `footprint_requirements`, `migrations` | 1,830 | `qml/conformance` | Follow `qml.conformance` |
| `admission`, `grammar`, `journal` | 2,524 | `qmn/host` only | Lose their callers |
| `sizing` | 289 | `qmn/capital` only | Loses its caller if the kill line goes |
| `versioning` | 295 | none direct | Same bodies as QML's copy. "Waits for the risk session" (`A/reports/deletion.md:47`) |

Due for deletion in `qmf-risk`: **nothing is planned.** "All of `qmf-risk`, which belongs to the risk session" (`A/reports/deletion.md:58`). A second wave of 4,732 lines has no caller by name once the old node and old QMB go, not proved by a run, and "nobody should cut them on a graph alone" (`A/FINDINGS.tsv:16`).

---

## 4. What R15-R24 and the deletion plan will do that touches the template

**Build on, once landed:**
- R15: every node trade reaches the Library, and a reason census test. **Any new brake text needs a code** in `_REASON_WORDS` and `REASON_CODES`, or CI fails (`PL/r15.md:29`).
- R19: `Projection` reads `trade` and `lifecycle` partitions, so a paper score counts every month (`PL/r19.md:25`). A minute spread row gives a spread by hour. Fees and slippage stay out.
- R20: the broker wins. A closing deal's price and kind land, or a guess alarm (`S/evidence/r20/pr-body.md`).
- R21: one way to close a scope, `_close_scope`. Whatever the kill table says now acts, hosted or not.
- R22: a held unit starts at the real balance. A moved number survives a restart or says why not.
- R23: market-hours stand-downs, a working clock stand-down, paper positions that survive.
- R24: the demo probes answer facts this session needs: whether a fill carries the stop, deal-history fields, what a close on a gone position answers (`PL/r24.md:37`). Their answers are read against R20 after G-DEMO (`PL/90-appendices.md:84`). None of these are known yet.

**Collide, or set a limit:**
- R21 blocks a stop past entry, and restores a lost stop at the send row's level. "A later amend row is not read, because no shipped unit emits one" (`S/evidence/r21/owner-sketch.md:109`). Trails must change this.
- R16 keeps the push list closed. "`raised` pushes only two names, and that list is promised closed" (`S/BACKLOG.md:65`). A risk alarm on his phone needs his word.
- R22's netting refusal is "one seam" for a second unit on a netting symbol (`PL/r22.md:32`). **[judgment]** It meets his multi-position idea only on one symbol, and it does meet a Book-level hedge.
- R22 writes the unit's snapshot under `data/deployments/<id>/`. **[judgment]** X1-H01's spec and status split will have to say how status relates to this file.
- R18 leaves the board unwired. Isolation by the board stays off.
- R17 changes `_admit` and `_leave` and adds an outbox rule. A profile document that travels beside a unit would pass through here (`PL/r17.md:25-26`). **[judgment]**
- R15's `unlisted` makes a live node tolerant and QMB strict, so a brake's text with no code runs on the node and fails a backtest at close (`PL/r15.md:25-26`).

**Remove, in the deletion plan:**
- C-20 (`A/plan-current.md:4173`): `qmn/host` (SQS gate, `runtime_risk_gate.py`), `seats`, `promotion`, `paper`, `doors`, `bench`, `deploy`, most of `observability`.
- **deletion-4, in Appendix B with C-20, sweeps 29,160 more lines** of `qmn/data`, `ledger`, `order`, `venue`, `config`, `replay`, `protection`, `reconcile` (`A/FINDINGS.tsv:7`, `PL/90-appendices.md:83`). `D:/Temp/audit/deletion/reach.tsv` shows `qmn/protection/windows.py`, `qmn/protection/dispatch.py`, `qmn/data/news_calendar.py` and `qmn/replay/port.py` with no caller by name. **[judgment]** So G9's "built, off the path" news windows, calendar ingest and the SQS replay rule go in that sweep unless this session claims them. `qmn/capital` (kill line, bench fold, ratchet) is kept out of the count, and its callers are in the shell (`A/FINDINGS.tsv:5,7`).
- The live lanes, after the first real start (`PL/90-appendices.md:82`).
- The old QMB door, on his word. **The Book path stays for this session:** `replay_execution`, `replay_request`, `execution/binder`, `orchestrator/ledger`, `book_handler`, 5,951 lines (`A/reports/ground-qmb.md:150-157`).

**Where the plan assumes a socket shape** (none of these are rulings; each is the plan's guess of this session's answer):
1. Exit answers stay in `qml/blocks/api.py`, with "an answer type beyond `Signal`", mapped to the existing intents `close_full`, `close_partial`, `amend_protection` (`A/reports/ground-unit.md:50`).
2. A new exit use in the compiler, so a slot-per-use shape stays. Six exits are refused "by rule" by shape (`PL/90-appendices.md:192`).
3. Step 2 feeds per-bar exits "real evidence and the side", and `time-exit-bars` keeps its reason code (`A/reports/ground-unit.md:45-46`).
4. SQS is "one line in `Runtime.guard`", which answers a string that blocks entries and never exits (`PL/90-appendices.md:205`, N `runtime.py:2534-2579`). This assumes SQS is a node-side gate.
5. The kill stays a table keyed by level, read by `_enact`, closing or not (N `runtime.py:2419,2463-2467`). This assumes the four levels stay, and effects stay on or off.
6. Whether R includes costs flips one line, `trade_r` (`PL/r10.md:39`). Motion reads a different field.
7. `cross_unit_hook` stays a static method on `OrderPath` taking a command, answering a string or None (N `runtime.py:1065-1069`). G8 §2.1's `before_order(intent, open_positions, dispersion)` is not what the node calls.
8. A sizer answers `Size`, "by adding the residue" (`A/reports/ground-unit.md:98`). So a sizer stays one call at entry.

---

## 5. The cTrader MCP safety flag

**X7's flag:** "if either is a separate server with order or position tools, it bypasses the door" (`RC/expansion/X7-agents.md:831`). `RC/STATE.md:256,285` asked the build session to put order tools behind the operator-only guard, or leave them out.

**The flag was overruled before it was answered.** His ruling of 3 Nov: agents get MCP tools as they are, and the one control is the demo-only blocker (`P/research/46-mcp-connections.md:4`, `P/build/TRIAGE-2026-11-03.md:65`). `A/RULINGS-NOW.md:112`: "Every agent can use cTrader's MCP, on demo accounts only. Replaces the risk session's flag that order tools need an operator-only guard, for demo."

**Built?** Yes. C-36 is stacked as PR 324 at `61928840` (`U/STACK-LIST.md:96`, `U/ledger.tsv:199-201`). It is in `50c83a4e`, so at every tip. Not merged.

**Are order tools offered on demo? Yes, as Spotware ships them.** Paths below starting `qma/`, `qmx_engine/`, `qmx_control/` or `qmx_apps/` sit under `qmx-agents/packages/<package>/src/`.
- `create_order`, `amend_order`, `cancel_order`, `amend_position`, `close_position` come with a `trading` profile token (`P/research/46-mcp-connections.md:33`). The test is named `test_a_session_bound_to_a_demo_account_record_is_offered_every_remote_tool` (J `qmx-agents/packages/qma-harness/tests/test_demo_only.py:106`, tools at `:47-51`).
- Reached by every copilot chat, and by any workflow step naming `mcp:ctrader`, unattended by default. `EXTERNAL_UNATTENDED_DEFAULT = ("ctrader/*",)`, J `qma/harness/home.py:291-292`. The engine policy lets an external tool pass, J `qmx_engine/policy.py:45-46`.
- It ships off. He must paste a url and one demo token (J `qmx_control/service.py:388-392,1133`).
- The `data` read-only profile exists, and how a token gets it is not documented (`P/research/46-mcp-connections.md:34`).
- cTrader's Local MCP is not offered (`P/build/TRIAGE-2026-11-03.md:65`).

**What stops a live account.** `demo_account`, J `qma/harness/demo_only.py:35-60`, at every launch for a row with a `venue` (J `qma/harness/tools.py:1220-1231`). It reads the bound account from `get_balance`, or a one-row `get_accounts_list`. It refuses if:
- no record reader exists;
- no account is named;
- cTrader marks it `isLive`;
- no `account` record on Library main has that id;
- any record says other than `demo`.

Refusal leaves the server out of the chat, with a note. `qmx/ctrader-mcp` may not be declared by any app (J `qmx_apps/manifest.py:80`), and goes only to an HTTPS url (J `tools.py:1112-1121`).

**Its limits:**
- **A row with no `venue` skips the check** (p5d-6, `A/FINDINGS.tsv:225`, test at `test_demo_only.py:152`, code J `tools.py:1093-1097,1220`). It takes his own hand edit. R17 plans three lines, for a row naming the wired credential only (`PL/r17.md:27`). R17 is just starting. **[judgment]** A stdio row with its own key in `env` and no venue stays unchecked after R17.
- **A token swap is caught at the next launch, not mid-session** (`demo_only.py:7-8`).
- **The Remote surface "does not distinguish demo from live"** (`P/research/46-mcp-connections.md:76`). So the `isLive` mark may not be there, and the Library record is the real check. An agent can put any record but a unit on Library main (triage-3), parked as "before any live account" (`A/REPAIR-SCOPE.md:88`, `PL/90-appendices.md:109`). He dropped the forged-record case because his live logins are never in QMX (`P/build/TRIAGE-2026-11-03.md:11`).
- **The check may refuse every real token.** Whether `get_balance.traderId` is the number in `account_id` is unproven until G-DEMO (`U/evidence/c36/findings-backlog.md:1-2`).
- **The token reaches the CLI's command line**, and agent Bash can read `qmx/*` keyring entries (`U/evidence/c36/findings-backlog.md:3`).

**[judgment] What this means for risk.** The only `account` records come from the node's bindings (C-34, J `venue_records.py:169-191`). So the demo account an agent acts on is likely the one the node trades. A position an agent opens carries no node tag: it reads "not ours" (J `qmn/src/qmn/app/attribution.py:43`), RED never touches it, and no unit's record holds it. It still moves the balance the next sign-in reads. An agent can also close a node position, which the node then reads through R20 as a broker close. So on demo, agent actions can touch the numbers a risk rule reads, with no row in the node journal. Nothing I read addresses this.

**Hyperliquid and crypto.**
- No MCP for it. No "hyperliquid" in `qma-harness/src` or `qmx-control/src` at J. `demo_only.VENUES` is `{"ctrader"}`, and any other `venue` value is refused (`demo_only.py:25`, `tools.py:1094-1095`).
- He said a crypto MCP was missed (`RC/STATE.md:188`). No plan or backlog line holds it (plan-check-9, `A/FINDINGS.tsv:260`, grade `leave`).
- The node's binding: `VENUES` includes `("hyperliquid", "testnet")`, J `qmn/src/qmn/app/operations.py:72`, and nothing binds a `CcxtClient` (`U/LOOSE-ENDS.md:161`). `bind` answers `not_set_up` (J `qmn/src/qmn/app/server.py:458`). All of `p5b-1` to `p5b-7` wait for G-WALLET (`PL/90-appendices.md:103-105`, `A/RULINGS-NOW.md:160`). R21 clears the close's reference price at the runtime's lines (`PL/r21.md:36`), and R22 adds the one-coin refusal.
- `CcxtClient.equity()` answers 0 when the read fails, J `qmn/src/qmn/venue/ccxt_client.py:597-601`. **[judgment]** A sizer on that value skips, and a drawdown brake on it would fire.

---

## 6. Effect on the Stage B themes

| Theme | Effect | Evidence |
|---|---|---|
| **Money brakes at the unit's own percentile** (X3-H01) | **Helps the evidence, blocks nothing new, and is still blocked at its old place.** Trades reach the Library, excursions and `net_r` exist. Halts still refuse at compile and no host computes the statistics. X3-H01 watches "every close and every mark", and no mark exists on the node. | J `compiler.py:902-903`, section 3. `RC/expansion/X3-brakes-exits-drift.md:80`. Record gaps: `S/BACKLOG.md:64,66` |
| **The applier with authority modes** (X1-H03) | **Neutral, a little harder.** `authority` is still a one-value label, and `applies_to_open_positions: true` now refuses. So the applier needs a format bump and `_MOTION_READ` widened. The census forces the decision. R22's snapshot gives it a place to persist. | J `compiler.py:869-877,996-1000`, `S/evidence/r04/pr-body.md:33,97`, `RC/expansion/X1-template-shape.md:53-60` |
| **The floor-odds sizer** (X2-H01) | **Blocked until the socket widens, and no repair PR widens it.** It needs usable cushion, result spread, unit count and correlation. The sizer gets four things, its inputs now refuse, and its number cannot move. The floor and marked equity do not exist. R10's records help compute `s` offline. | J `unit.py:785-793`, `compiler.py:930-936,617-643`, `RC/expansion/X2-sizing-accelerators.md:62-65`, plan-check-7 |
| **The random-brake control** (X3-H13) | **Helps a little, and is offline-capable.** It replays a unit's own trades, so R10's per-trade rows, money measures and comparable runs serve it. A brake's fire count on the node stays blurred: a risk stop still files as `kill_switch`, and a trade row cannot tell why it closed. | `RC/expansion/X3-brakes-exits-drift.md:211-214`, section 3, `R journal.py:57`, J `journal.py:412` |
| **One RiskState from the node** (X1-H49, H57) | **Helps the truth under it, builds none of it.** R20 and R21 make positions, stops and scopes true, and `_mine` is one list with scopes. The node still shows no equity, drawdown, open risk or budget. `"paused": 0` and `"clock": None` stand. No PR plans a `risk_state` row. A phone push on it is his call. | N `runtime.py:2311-2357`, `operations.py:918,923`, `RC/expansion/X1-template-shape.md:547`, `S/BACKLOG.md:65` |
| **The agents' door** (X1-H49, H50; X7) | **Premise changed by his ruling.** "Read, propose or cut, never raise or touch money" now holds for live only. On demo, agents hold cTrader's order tools. The judge hardening helps: a late study pays a try (R11, in fix), a forged verdict is refused (R12). Still no row saves a block. | `A/RULINGS-NOW.md:112`, section 5, `PL/r11.md`, `S/review/r12-check-fdccd475.md:37` |
| **Replacing Book and BMS** (X1-H40) | **Neutral to helping, and a deletion waits on it.** Nothing in R15-R24 touches them. `bms`, `book`, `pod` kinds stay shells. C-20 removes the old node's Book seats. The Book path, `qmf-risk` and the `versioning` copy all wait for this session's word, so a ruling frees about 5,951 and up to 4,732 lines. R22's netting rule is the one new cross-unit rule. | `A/reports/ground-qmb.md:157`, `A/FINDINGS.tsv:16,20`, `A/reports/deletion.md:47,58`, `PL/r22.md:32` |

---

## What the funnel must know

1. **Read the code at the right tip.** Unit, compiler and sizer facts: J. Kill, flatten, broker truth: N, and R21 is not reviewed. Records and reason codes: R. Nothing above R06 has passed everything, and nothing is merged. R04-R06 are not in N, and R20-R21 are not in J. The first whole-repo run past R03 is running now (`S/RESUME.md:25`).
2. **"Ignored" is now "refused".** G8's nine ignored fields and its list of silent things refuse at compile on J. A hybrid that says "read `sessions`" or "run halts" is still right, and must also lift a named refusal and take a format bump, which moves the compiled fingerprint and `pack.json` (`S/evidence/r04/pr-body.md:11`). X1-H56's "compiler format 2" is now past format 4. The census test means a new field cannot arrive silently.
3. **Still true, and nobody is building it:** halts unrun, hook passing, sizer starved, exits unfed, `risk_fraction` unable to move, `risk_stop` with no producer, no marked equity, no commission key, no budget, no open risk, no RiskState, no spread guard. **The repair builds plumbing around these, and none of them.** Appendix F says they are this session's.
4. **The exit half is waiting on this session.** "Agree the socket with it first." The plan's guess of the shape is in section 4. Step 3 must not ship on the node before the signed distance is answered (`A/reports/ground-unit.md:67`, `PL/90-appendices.md:202`).
5. **Rulings to carry, not to reopen:** "Kill switch and SQS stay. Exits never blocked" (`RC/STATE.md:327`). No gate is built now, and it is placed by this session (`A/FOR-HIM.md:17`). Flatten closes and does not stop a unit, and RED closes every position with this node's tag (`PL/90-appendices.md:157`). The dummy does not go to demo without the judge (`A/FOR-HIM.md:16`). Agents get cTrader's MCP on demo (`A/RULINGS-NOW.md:112`).
6. **X7's C9 flag is answered and closed by him for demo.** The live side rests on his live logins staying out of QMX. The open fact is agent orders on the node's own demo account (section 5, my reading).
7. **The SQS gate's text is now saved here.** The new node has no SQS, no MIS pack carries it, and no baseline producer runs. C-20 deletes the gate and is the last thing to fire, after G-DEMO. `sqs_baseline_producer.py` must move first.
8. **The deletion sweep can take this session's parts.** News windows, the calendar ingest and the replay rule read as no-caller in the audit's graph (section 4). If a hybrid needs them, it must say so before C-20 runs. Kill line, bench fold and ratchet are outside that count.
9. **Facts nobody knows until his demo sign-in.** Whether a fill carries the stop. What a close on a gone position answers. Deal-history fields for a stop. Whether `traderId` is the account id. Real slippage. Real commission and swap on cTrader (`PL/r24.md:37`). A ruling that leans on any of these should say so.
10. **Records under a money brake have known holes.** A protection close leaves no trade row (`S/BACKLOG.md:66`). A hand part-close leaves full size in the handler (`S/BACKLOG.md:64`). A trade found after an outage reads the first bar after it as its closed time (`S/BACKLOG.md:67`). A retried exit that closes, then a crash, loses the row (`S/RESUME.md:163`). A live lane on demo gets no paper score.
11. **Decisions on this session's desk from the hand-offs,** unranked: stop past entry, stop widening, target at the broker, a unit with no stop, a moved number and open trades, two exits on one bar, partial close and R, R and costs, kill level meanings, `too_thin`, the version pull, grid and martingale families, the Book's fate, a move on a check with no orders.
12. **This grounding is a snapshot.** The DeepSeek run is moving R11, R07-R10 reviews, R14, R16 and R17 now. Re-check the tip before any slice is written. Repair PRs lean hardest on `qmn/src/qmn/app/runtime.py`, `host.py` and `first_start.py` (`PL/90-appendices.md:137`), and any risk PR will meet them there.

## Not checked

- No code run, no test run. Every "changed" is read from code or a PR body, and R19, R21 and R16 have no review behind them.
- I read no R16 or R19 session reports (`S/RESUME.md:161`). They are not on disk under those names.
- I did not read `Q` beyond R16's PR body and the greps named.
- `qmf-risk` importers count direct `qmf.risk.<file>` imports only. The "after C-20" column is my reading.
- `reach.tsv` is the audit's static graph at `50c83a4e`, not proved by a run for each file.
- I did not trace which PR changed promote's one-deployment rule.
- Whether C-36 reaches a shared demo account in practice is my reading of `venue_records.py` and the check. It has never run against Spotware.
