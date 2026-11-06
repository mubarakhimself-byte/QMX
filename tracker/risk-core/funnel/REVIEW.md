# Independent review of the funnel

Opus reviewer, 6 Nov 2026. Method: `bmad-review` with the adversarial, edge-case and verification-gap lenses, run non-interactively. Tags: **[adv]**, **[edge]**, **[verif]**. **[judgment]** marks my opinion.

## Verdict

Not yet a funnel: it keeps 90 % of the hybrids and about 92 % of the ledger, and it names no core.
As written it is a handbrake with better paperwork: run together, the picks turn a weak real edge into about +5 % in four months.
The sizer, money over count, the CUSUM step-down, the guard and RiskState are sound; cut to about twelve parts and take the evidence ceiling out from under the baseline before any architecture starts.

Paths are under `tracker/risk-core/` unless they start with `A/` (`D:\QMX-worktrees\audit-ship`) or `S/` (`D:\QMX-worktrees\repair-ship`). Short names: `X2`, `X3`, `X4`, `X5` are `expansion/X*.md`; `RANKING.md`, `FUNNEL-BRIEF.md` are in `linking/`; `G3`, `G12` are in `grounding/`; `out-200.txt` and `x3_brake_sim.py` are in `linking/stage-b/X3-brakes-exits-drift/`; `out-1000*.txt` are in `linking/stage-b/X2-sizing-accelerators/sims/`. Component ids such as A2-135 are in `linking/components/`. My scripts and outputs are in `funnel/working/review/`: `size_count.py`, `stack_sim.py`, `sens.py`, `more_arith.py`, `out-*.txt`. All sim numbers are model numbers, not evidence about a real strategy.

**What I read.** In full: `FUNNEL.md`, `SEEDS.md`, `STATE.md`, `G12`, the brief, the rubric, the roundtable, the pre-mortem, the arithmetic script, the X2 and X3 sim outputs. In part, by targeted reading: `HYBRID-FATES.md`, `ledger-merge.yaml`, X2 to X5, the components named below. Not read: X0, X1, X6, X7 end to end, research papers' text, code at the tips (I relied on G12). So "no pick says X" means none in `FUNNEL.md` and the hybrids I opened.

---

## Must-fix

### M1. It did not narrow. **[adv]**
- **Where.** `HYBRID-FATES.md:518-532`; `FUNNEL.md:9-23`; `ledger-merge.yaml`; `STATE.md:307`.
- **Wrong.** Only 6 of 510 hybrids were dropped and 34 deferred. Of the 34 deferred, 26 carry the authors' own "wild" tag, so the real filter was the tag `RANKING.md:3` calls "only a hint". Every decision scores one big bundle against strawmen, so no single part ever has to earn its place.
- **Evidence** (`size_count.py`).
  - 462 picked. After the "=" merges that is still 256 distinct mechanisms, not counting scenarios.
  - 33 of 34 picks are option (a), and DP1's (b) is the same kind of bundle. DP32 holds 35 ids, DP30 29, DP28 26, DP23 23, DP27 20.
  - The ledger goes from 903 to about 834 variables. Every earlier QMX generation together held 267 (`STATE.md:124`).
  - `RANKING.md:16` says to count ledger variables as cost. No score does. DP28 scores A3 while X5 alone adds 154 variables.
  - His words: "too much machine" (`STATE.md:334`), "Design for complexity. Don't design a complex system" (`SEEDS.md:929`), "let's just design the baseline" (`SEEDS.md:936`), "we need one that can take us off the ground" (`SEEDS.md:284`). Standing rule: "what is the base that lets this grow on its own? ... cut the rest to the backlog" (memory `foundation-first-design.md:22`).
  - Agent-safety parts survive that the operator ruled out: "agents have no path to money, so ... machinery is over-engineering" (memory `design-for-complexity-not-complex-system.md:13`). See DP32 (per-agent random de-risker, sealed scenarios, rationale-blind admission, autonomy ladder) and DP8 (trust ladder, three faces, quarantine hatch).
- **Fix.** Add a column to `HYBRID-FATES.md`: **core**, **plug-in later**, **dropped**. Build the core from "The true core" below. Score each core part alone, with its variable count. Everything else goes to a backlog with its plug point named. [judgment] The full set is 100 or more builder PRs at the unit build's scale; the core is 25 to 35.

### M2. The evidence ceiling makes a sitting duck of the unit he cares about most. **[adv] [verif]**
- **Where.** DP15 `FUNNEL.md:139-143`, F6 `:355`, F11 `:360`, DP10 `:102-107`; `X5-edge-verification.md:241`; `flaw_arithmetic.py:93-98`.
- **Wrong.** The baseline is built to survive at zero edge. The ladder then holds size at about 10 % of that baseline until the e-meter proves the edge. Both guard against the same fear. For a weak edge the ladder never lets go.
  - `X5:241` and `FUNNEL.md:140` call this "his squeeze some money out of a weak edge". He said the opposite: "carry or amplify the load" (`SEEDS.md:206`). He also said "setting it in stone ... Then what is the point" (`SEEDS.md:130`) and "why would you tell him to risk only $20?" (`SEEDS.md:456`). This is a relabel, not a fit.
  - F11's "about 60 baseline trades" of ramp counts cohorts only. The script leaves out the e-bars that F6 says are the ceiling. F6 and F11 cannot both stand.
  - `FUNNEL.md:335` says "the e-meter is display", while `:139` and `:355` make it the ceiling.
  - `:107` says QMB's evidence "survives as the gate and the level", while `X5:241` says "a backtest never raises a level" and `X2:201` says the same. His ruling is that QMB proves the edge before demo (`SEEDS.md:762`), yet the meter starts at 1.
- **Evidence.** No sim in the funnel runs the picks together. `stack_sim.py` does, on the milder reading of every pick, with no SQS, news, isolation, weekend or agent cuts and no lot rounding. One unit, 10 trades a day, $500 seed, $300 floor, 120 days, median equity:

| True edge | Sizer alone | Core (cohorts, p1 bench, CUSUM) | All picks | All picks, X5 bars as written |
|---|---|---|---|---|
| Healthy +0.10R | $6,027 | $2,259 | **$612** | $560 |
| Weak +0.05R | $1,160 | $842 | **$525** | $500 |
| Thin +0.03R | $694 | $635 | **$514** | $500 |
| +0.03R with a +0.30R streak on days 40-60 | $2,424 | $1,394 | **$551** | $518 |
| Card +0.10R, true +0.03R | $693 | $512 | $506 | $500 |
| Card +0.10R, true 0 | $426 | $472 | $499 | $500 |
| Card +0.10R, true -0.05R | $318 | $454 | $494 | $500 |

  - Live size against the baseline: healthy 1.00 / 0.93 / **0.26**, weak 1.00 / 0.93 / **0.12**.
  - Half the cushion lost: core 0 % on all but the thin unit (6 %), picks 0 %, sizer alone 98 % on the bleeding unit. Compounding widens the dollar gaps, so read the size ratio too.
  - Adding one pick at a time, the e-bars cut size from 0.94 to 0.38 on the healthy unit and from 0.93 to 0.15 on the weak one. Nothing else comes close (`out-attrib-n10.txt`). An oracle e-meter barely helps: 0.30 and 0.12 (`out-sens.txt`).
  - Time to the bars, from `X5:854` scaled by 1/edge²: +0.10R reaches e 20 in 48 days at 10 a day, 121 at 4, 242 at 2. +0.05R takes 194, 485, 970. So a +0.05R unit at 10 a day sits at level 1 for over six months.
  - Honest price of the fix: on a bad unit the core loses $28 to $46 of the $200 cushion where the picks lose $1 to $6. On a good unit it gains $120 to $1,650 more. [judgment] That is the asymmetry `RANKING.md:16` asks for.
- **Fix.**
  1. The e-meter stops gating anything under baseline. Below baseline, use cohorts for speed and CUSUM for step-down.
  2. QMB's deflated holdout sets the starting level, so a proved unit does not start at 10 %.
  3. Keep the e-meter for two jobs: raises above baseline, and moving the edge dial.
  4. Rewrite F11 from the integrated sim, and make the harness run it.

### M3. The cut-only stack is April's handbrake again. **[adv]**
- **Where.** `FUNNEL.md:134` rejects April because "multipliers did each other's jobs; one cap bound always". F8 `:357` and F11 `:360` count only five factors.
- **Wrong.** I count about 39 things that can only cut size. Merge them as you like; it does not fall below 25 [judgment]. April had nine multipliers and six caps (`G3-old-system.md:33`).
  - Sizing: reserve, cost denominator, stressed correlation, Kelly ceiling, level, cohort limit, e-bar, memory ceiling, lock, share ladder, ratchet, per-R cap, bet key, worst-case veto, margin headroom, sanity band, lot round-down.
  - Unit and portfolio brakes: brake half, REDUCING, BENCHED, loss points, count brake, drift step, two-key halve, AIMD, burn permit, chorus, methodology CUSUM, BMS breaker, shedding, clip.
  - Market: SQS shrink, class caution, isolation, weekend scale, macro governor, calm-vol cut, news and open windows, hourly gate, agent cut.
  - On top of these: world and version resets.
  - What can lift above baseline: house money (off), tiers, press (after a block test), pyramiding (trend only), lending (recalled by any brake). None is on at go-live, and any raise needs every brake clear (`FUNNEL.md:13`). Nothing lifts size above baseline without him (`:181`).
- **Evidence.**
  - One running loss is read four times: the anchor recompute, the brake half (`X2:166`), REDUCING and BENCHED. Near -3R of a 5.3R allowance the brake half gives about 0.4 and REDUCING makes it about 0.2 of the level's size, before any market cut. His own diagnosis: "some were also doing the job of others. I think that's why the handbrake" (`SEEDS.md:546`).
  - All picks without the e-bars still run at 0.68 of baseline on a healthy, independent stream (`out-sens.txt`). On such a stream a cut after a loss buys nothing (R9, `X3:50`).
  - The choke budget (`FUNNEL.md:155`) is per brake. Nothing caps the total. The meter of F8 reports; it does not relieve.
- **Fix.** One reading of the running loss enforces; the rest stay in shadow. Enforce the own-p1 bench and the CUSUM step. Ship REDUCING, loss points, the brake half and the count brake in shadow. Set a total choke budget for a healthy unit across all cuts, tested in the harness. If a healthy unit runs under it, that is a defect that blocks shipping, not a line on a meter.

### M4. F1 is not resolved, and it collides with DP11. **[adv] [verif]**
- **Where.** F1 `FUNNEL.md:350`, DP26 `:216`, DP11 `:110`, `:499`; `X2:495`; `flaw_arithmetic.py:24-26`.
- **Wrong.** F1 is marked resolved, yet its arithmetic assumes the cut never touches a winner. `:499` says no paper tests this. And the scalper F1 rescues fails the gate in the same set.
- **Evidence** (`more_arith.py`).
  - Same 55 % unit, 0.16R cost, half the losers cut at -0.35R. Winners also cut: 0 % gives +0.086R, 10 % gives +0.012R, 20 % gives -0.062R. A cut at -0.5R with 20 % of winners caught gives -0.112R.
  - `X2:495` sets the gate at "gross edge at least k x stressed cost (2x, 3x for negative skew)". At a 5-pip stop the gross edge is 0.246R and the bar is 0.32R with no stress at all, and that is the point estimate, not the low end. Refused. An 8-pip stop passes unstressed and is refused at 1.5x stress. A 10-pip stop passes.
  - So k and the stop size decide whether his scalper exists. No question and no flaw says so.
- **Fix.** Mark F1 open. State the condition: the frequency thesis needs a cut that catches few winners, proven per unit by two-arm test, before the sizer's growth is believed. Write what happens if it fails: wider stops, fewer trades. Put k on the numbers lens with this table beside it.

### M5. On day one, no brake may enforce. **[adv] [edge]**
- **Where.** `FUNNEL.md:17` ("Every brake ships shadow-first, must beat a random brake"), `:171-174`, against `:132-133` ("brake half on from day one"), `ledger-merge.yaml:241-243` (certificate is "a compile requirement in the first increment"), `X3:225,230`.
- **Wrong.** `X3:230` leans on "the old brakes stay enforcing". There are none: halts have never run on the node (`G12:263`). So the first live unit has clamps and no brake, against "Brex first" (`SEEDS.md:501`). The funnel also dropped `X3:214`'s escape clause, that a brake with a tail job may act without beating its twin.
- **Evidence.**
  - On X3's own sim the picked money brake earns +1.2R, +1.2R, +25.9R, +1.1R, +0.8R over its random twin on five units (`out-200.txt:18,40,62,84,106`). Four of five would fail the rule as the funnel states it.
  - In a model of that regime world one unit earns +1.5R a year with a spread of 6R, so a z of 2 takes about **60 unit-years** (`out-more-arith.txt` K). A portfolio breaker at one fire a month cannot pass before going live either.
- **Fix.** Two classes of brake on the registry row. **Tail brakes** (own-p1 bench, dollar clamp, portfolio stop, clip) enforce from day one and carry a card saying "tail, timing unproven". **Timing brakes** (count, REDUCING, class tells) stay in shadow until they pass. Make the certificate a pooled report, not a compile gate.

### M6. The first live version leaves out the portfolio stop he asked for. **[adv]**
- **Where.** Shape C `FUNNEL.md:470`, DP6 `:73`, DP22, DP23, Q1 `:482`; `X4-scenarios.md:203-209`; `X3:1082`; `STATE.md:278`.
- **Wrong.** He asked for a portfolio-level breaker that can "automatically sense this type of move and switch off entirely" (`SEEDS.md:561`), and called the BMS the one level that might be standard (`SEEDS.md:338`). Shape C keeps the unit ladder he called "circumstantial" and has no BMS breaker and no isolation.
- **Walk: X4-14, everything bad everywhere, under shape C.** Every unit's own p1 trips one by one, at its own loss. The next automatic stop at portfolio level is the cushion clip at the buffer. The kill switch waits for his hand. His phone may not ring: alarms are off on an installed node until R16, which is unreviewed, and the push list is closed (`G12:294,337`). So the book can give up most of the cushion before anything portfolio-wide acts. The scenario's own bar is "leaves the cushion mostly intact" (`X4:209`). **It fails.**
- **Fix.** Put one simple stop in the first increment: portfolio day loss past a multiple of the sigma budget the sizer already computes (`X2:76`) raises a stand-down at `all`, a scope that exists (`G12:279`). Enforce it from day one as a tail brake, with an expiry at the next anchor. Isolation by class stays in shadow, but say so to him.

### M7. Two go-live blocks left inside the picks. **[edge]**
- **Where.** `X5:241` against `X5:199`; DP11 `FUNNEL.md:114` against `X2:495` and X0-37; `G12:270-271,427`; pre-mortem item 1.
- **Wrong.**
  - **Paper.** `X5:241` (picked) says "e ≥ 10 to leave paper". That is 335 paper trades at +0.10R (`X5:854`): 84 days at 4 a day, 34 at 10, 8 at 40. His limit: "7 days is doable, but 14 ... quite high" (`SEEDS.md:790`). `X5:199` says a working machine reaches level 1 in a week. Q3's default ignores the paper bar and never strikes it. A builder reading H13 builds it.
  - **Cost cells.** DP11 says live at level 1 "needs at least N measured fills in the cell". `X2:495` says "never a blanket refusal". X0-37 says "demo never calibrates live". Paper has zero slippage. No writer of a cost profile from fills exists until after G-DEMO, and no commission key exists (`G12:270-271`). With cells by instrument, hour, session and world, the first unit is refused at most hours. The pre-mortem marks this answered with the same sentence that causes it.
- **Fix.** Strike the e-bar on paper. A machine check in a week, then his click, then level 1. Live trades on the stressed default with `cost:uncalibrated`, pooled across the class, and a cell refuses only after fills show net edge below zero.

### M8. House money: the pick contradicts its own proof, has no home in C, and he is not told it is off. **[adv]**
- **Where.** DP14 `FUNNEL.md:132,136`, F7 `:356`, Q5 `:486`, `flaw_arithmetic.py:77-80`, Shape C `:470`.
- **Wrong.** The script says the accelerator "CAN" drive into the brake "on a different ledger ... which is why one declared scope per pair holds". The pick and Q5's default then put the accelerator on the cluster ledger and the brake on the unit ledger. Shape C has no cluster ledger. The proof card needs persistence (`X2:277-283`), and R9 finds no accelerator beats a constant on independent trades, so "off until proof" may mean off for good. He ruled "I don't think I want to lose the house of money" (`SEEDS.md:183`). Q5 asks only where it lives.
- **Evidence.** F7's check covers the same-ledger case only. `A5-118` also records a tail the funnel omits: "73 % of paths over 25 %" in slow regimes.
- **Fix.** One ledger per pair, as DP14's own title says. Default: portfolio ledger for both halves, with the event window, so it has a home in C. Ask him plainly whether house money off at first go-live is acceptable. Reword Q5.

### M9. The book goes dark far above the floor. **[edge]**
- **Where.** DP13 `FUNNEL.md:125,129`, F5 `:354`, `X2:565`, `X4:918-930,1173`.
- **Wrong.** Size is proportional to the cushion and never rounds up, so below one lot step the trade skips. Admission is checked as a gate, and nothing re-runs it as the cushion falls. Nothing says who stops so the others can still trade. DP13 rejects "fewer, larger units" as against his C1, yet that is the only way out.
- **Evidence** (`more_arith.py` B, one micro lot on a 5-pip stop, $0.50). Cushion below which every unit skips:

| Units | 10 trades a day | 40 trades a day |
|---|---|---|
| 1 | $16 | $32 |
| 3 | $35 | $69 |
| 5 | $53 | $105 |
| 10 | $96 | **$193** |

  - Ten 40-a-day units go dark after a 4 % fall from a $200 cushion, with $193 unspent. Before that, level 1 is already 96 % of baseline, so levels do not exist at this scale. REDUCING at a minimum lot becomes "skip every second signal" (`X3:93`). This is "seated like a duck" (`SEEDS.md:440`) produced by the sizer.
- **Fix.** Re-run feasibility at each anchor. When the baseline falls under a lot, shed units by a declared rank so N and B fall and the survivors clear a lot. Show him the state. Harness test: a slow bleed from $500 at each N.

### M10. The headline numbers for the brake pick are cherry-picked and come from an arm the set rejects. **[verif]**
- **Where.** DP17 `FUNNEL.md:156`, DP20 `:177-178`, DP27 `:241`.
- **Wrong.**
  - "Adds +26R of timing at 40 a day" is the best of five. The other four are +0.8R to +1.2R.
  - "Keeps 97 to 100 %" comes from arms that bench for the day and return next morning at full size (`x3_brake_sim.py`, docstring). DP20 rejects that as option (c). The picked restore (cool-down, probes, one level per settled cohort, memory, lock) was never simmed. With every pick but the e-bars, my sim gives 0.68 of baseline, not 0.97.
  - "902R of 950R" for DP20 is the CUSUM policy at 40 a day (`X3:48`), not a restore by probes.
  - P3 on DP17: the brake adds no growth. `X3:50` says so, and `X3:85` says it "does not stop a slow bleed". On the decay case it keeps -69.1R against -69.3R with no brake (`out-200.txt`).
- **Fix.** Report all five units. Score DP17 at P1 and DP20 at E0 or E1. State the brake's job as the tail. Sim the picked restore before keeping it. The slow CUSUM is the part that earns: 29R becomes 78-86R on decay.

### M11. "Settled, not asked" has no quote for its first item, and his "about three" is inverted. **[adv]**
- **Where.** `FUNNEL.md:490`, `:67`, `:159`; `X3:998,1082`; `STATE.md:278`; `more_arith.py` A.
- **Wrong.**
  - "The BMS breaker does not raise the kill level (rulings: kill switch earned its spot)". He said it "earned its spot" for surviving versions (`SEEDS.md:516`). The standing ruling covers lowering only (`FUNNEL-BRIEF.md:26`). X3 asks him this question, and `STATE.md:278` lists it open. No quote settles it. The default is fine; the claim is not.
  - The sweep cap is listed as settled. He asked twice, "Are we having a sweep cap or not?" (`SEEDS.md:319,453`). The judge has answered him; he has settled nothing. He must be told.
  - "R stays gross" is not settled by him either. `A/FOR-HIM.md:19` says "The risk session decides". That makes it this session's call, with his B9 reservation standing (`SEEDS.md:307`).
  - DP17(d) scores F3 with "his picture kept". He said six straight losses "is a very high number", and "from six to around three or two" (`SEEDS.md:68`). Scaled to own p99, the count is 5 / 7 / 8 / 10 at 4 / 10 / 16 / 40 trades a day for a 55 % unit, and 4 / 6 / 6 / 7 for a 70 % one. That is at or above the number he called too high.
- **Fix.** Move the BMS question to the list in one line. Tell him the sweep answer. Reword R as "our call". For (d): use a higher fire rate (own p90 to p95) since the action is only a halve, and tell him plainly what "three" became.

### M12. Shapes A and B are one fork, C is a build order, and C's list is incomplete. **[adv]**
- **Where.** `FUNNEL.md:466-472`, Q2 `:483`, `ledger-merge.yaml:237-243`.
- **Wrong.**
  - A and B share the profile, guard, applier and harness, and differ in one layer. Q2's default (keep the words on screen, use cluster and portfolio in the schema) already picks A, so "his vocabulary" cannot decide between them. Architects would compete on the smallest axis in the set.
  - The real forks are not offered: an evidence ladder against cohorts plus drift step-down; an applier with modes against refresh at anchors; brakes in one guard against slots in the unit.
  - C omits things the set needs at go-live: the level ladder (Q3 requires it), SQS (a ruling: "Kill switch and SQS stay", and `G12:222` says the new node has nothing), kill level effects, news windows, the click packet, the light harness. Yet the ledger makes the certificate a compile rule in C, and that rule needs the harness. "The money brake and ladder" is ambiguous between REDUCING and levels.
  - Q2 files replacing the Book and BMS documents as vocabulary. It frees 5,951 lines and up to 4,732 more (`G12:413`). M33's bar is "can perform better" (`operator-words-2026-11-03.md:188`) and `FUNNEL.md:55` says "no QMX generation ran tag clusters". That is scope, and his.
- **Fix.** One first increment, listed fully (see below). For the arena, offer the three real forks. Book against tags waits until after go-live, and he hears it as a structure question.

---

## Should-fix

**Evidence and scoring**
1. **E scores above evidence. [verif]** 25 of 34 picks score E2. `RANKING.md:13` defines 2 as a fair-controlled test. `FUNNEL.md:496` says no money brake has run on QMX streams. Spot checks:
   - DP15: BOIN "analogue, no trading result" (A2-190); "never run on a trading unit" (`X5:257`).
   - DP10: "DeMiguel and Chopra-Ziemba are strong", but A1-031 and A1-019 read `evidence: idea`, and the 11x is second-hand from R2:236 and about portfolio weights, not trade size.
   - DP21: hours clause from a "vendor blog" (A2-026). DP20's recloser source is "a student report" (A2-022).
   - DP24: E-mini is an "author backtest" (`X3:426`). DP11: the BTC filter is an "author backtest" (`X2:500`). DP22: Hsieh reads `evidence: idea` (A1-038). DP3: its own text says no trading study exists.
   - DP19's single fair test held: 97 trades, one author, all three arms lost money (A2-135). Keep E2 with that note.
   - For software patterns, write "proven pattern, no trading test" rather than E2.
2. **P scores on meters. [adv]** DP19, DP27 and DP29 score P3. A meter or a harness adds no growth by a named mechanism, which is what `RANKING.md:9` asks for.
3. **Omissions beside true numbers. [verif]**
   - DP27 cites "none of 4,000 trades" for demotion but omits CUSUM's healthy alarm spacing of 668 trades (`X5:858`). A healthy 40-a-day unit steps down about every 17 days. In a bad week at 40 a day CUSUM alarms 54.5 % of the time (`X3:44`), against "It can be a bad day, man" (`SEEDS.md:213`).
   - DP9 omits that half the cushion goes in 30 to 42 % of zero-edge runs in 60 days (`out-1000.txt`, `out-1000-gaps.txt`).
   - DP18 quotes CUSUM "at 4 to 40 trades" and leaves out 68.5 % at 2 a day, while its density range includes 2 a day.
4. **F11's inputs are guesses.** News share and isolation days are marked guess in the script (`flaw_arithmetic.py:89-90`), not in the table.

**Logic and edge cases**
5. **Unused swing stays idle. [edge]** B assumes all N units run at full size. With nine at level 1 and one at full, the book uses 1.36 of an allowed 6.08, so the proved unit could be 4.5x larger at equal book swing. All ten at level 1 run at 10 % of the allowed swing (`more_arith.py` I). Compute B on actual level-weighted sizes.
6. **What N counts. [edge]** After a correlated day with 3 of 10 benched and the cushion down 10 %, the survivors' r rises 24 % next morning if N counts live units. DP9 computes at each anchor; `X2:372` says weekly. State that N is admitted units, changes weekly, and never rises under a caution.
7. **Trade rate works backward. [edge]** H is the measured rate, so a dead month raises r (rate halves, r up 41 %). Floor the rate at the card's.
8. **Windows in trades cannot roll while benched. [edge]** `FUNNEL.md:161,362`; `X3:238`. Say which clock applies: the paper twin or a time equivalent.
9. **Ratchet against the floor. [adv]** `FUNNEL.md:11` puts the floor on the never-self-tune list, and `:146` raises it by rule. `:147` says "no idle reserve", yet at a 25 % share idle money goes from 30 % to 42 % of equity when equity doubles (`more_arith.py` J). Split his base floor from the lock line, and tell him it is a sitting-duck trade-off.
10. **Halve or level. [edge]** `FUNNEL.md:161` halves, `:244` steps a level. Levels run 10, 25, 50, 75, 100. Define one size step.
11. **F4's direction. [verif]** `FUNNEL.md:353` says the holes make fire rates read high. A node protection close leaving no trade row (`S/BACKLOG.md:66`) hides a loss, so they read low. No PR owns these holes, and "the repair's" overstates it. The guard's money ledger should read broker deals.
12. **DP12's fallback is not there. [verif]** "Balance minus open risk" assumes a live balance. It is read once at sign-in, and the sizer uses start plus closed trades (`G12:266-267`). Count the build.
13. **Automatic closes missing from Q1. [adv]** `FUNNEL.md:193` "reduce until above the buffer" and X4-87's de-gross close positions by rule. The ruling covers "a risk rule stopping a unit" (`A/RULINGS-NOW.md:197`).
14. **The edge dial never moves. [adv]** `FUNNEL.md:102`: default zero, moved only by a version or his click. X2's own sim has zero to low lifting $2,213 to $5,854 at zero touches (`X2:91`). "A high one will get even a bigger buffer" (`SEEDS.md:206`). No question asks. A proved unit stays at day-one size for good. Let a proved level release the dial to `low`, and ask him.
15. **Survival days have no owner. [edge]** r falls with the square root of days, and Q4 does not list them. The ledger has only "Proposal: a month". Add a derivation and list it.
16. **Twelve "picked" hybrids have no decision point. [verif]** X0-47, X0-51, X1-H31, X1-H66, X1-H67, X2-H34, X2-H37, X4-23, X4-49, X5-H47, X7-H25, X7-H35 point at TLH rows or "downstream" and were never scored. Multi-position units (his A8) and BMS slot optimising (his C26) sit here, and `G12:254` says a higher position limit refuses.
17. **DP1's chain has eleven keys. [adv]** Preset, style, class, bucket, instrument, venue account, unit, market, timeframe, session, event (`FUNNEL.md:38`). Start with four and reserve the rest.
18. **His direct question unanswered.** "How does the MIS adjust?" (`SEEDS.md:561`). `FUNNEL.md:199` flags it. Give one plain line: the board keeps publishing, the guard refuses, the router must not place into a stand-down.

**Code reality and order**
19. **Not carried from G12. [verif]** No mention in `FUNNEL.md` of R22's snapshot against the status split (`G12:339`), R17's `_admit` path (`G12:341`), or R16's closed push list. `G12:337` says a risk alarm on his phone "needs his word", so Q6 must carry it.
20. **SQS as "one line". [verif]** `FUNNEL.md:210-212`. The new node has no SQS, no baseline producer runs, and eight settings block live when blank (`G12:214,222`). Size it as a real slice.
21. **Claims list. [verif]** `handoff/FOR-REPAIR-CLAIMS-BEFORE-C20.md` omits `qmn/protection/dispatch.py`, which `G12:346` names, `control_window`, which follows windows (`G12:312`), and `registry_catalog.py`, which holds the SQS rows (`G12:214`).
22. **No build order. [adv]** F1 says the cut comes first and F3 says the guard's facts come first, and nothing joins them. Proposed order, on landed repair tips only:
   - exit socket step 2 and trade row with mechanism;
   - guard facts (balance refresh, open risk, bet keys) and RiskState;
   - sizer socket with its compiler refusal lifted;
   - tail brakes and the portfolio stop;
   - SQS and news first slices;
   - light harness;
   - click packet.

**Questions**
23. **Rewrite the list. [adv]** Q1 packs at least four decisions; split it. Q4 is not a question today. Add the ones that are really his:
   - a weak unit at about 10 % of safe size for months, or near it with drift watching (M2);
   - does QMB's proof set the starting level (M2);
   - house money off at first go-live (M8);
   - may the portfolio breaker raise the kill level (M11);
   - the edge dial after proof (item 14);
   - the phone push list (item 19);
   - the Book and BMS as a structure question (M12).
   Keep Q3, Q6, Q7.

---

## Held up

I tried to break these and could not.

- **The arithmetic in `flaw_arithmetic.py`** re-runs clean. Sections A, B, C, F and G are right as algebra. H01 and H02 are one formula when H = rate x days (F2).
- **DP9 over edge-led sizing.** I checked `out-1000.txt`: half Kelly touches 100 % at half edge with ten units, the GitBook ladder 92 %, fixed 1 % 18.7 %, the sizer 0 %. Quoted right. F12's honesty about the structural zero stands. As the base it is the best in the set. Its problem is what sits on top of it.
- **Money over count as the enforced default.** "3 in a row" fires on 41 % of days at 10 a day and 91 % at 40. A fixed count cannot be the default.
- **The CUSUM slow lane.** It carries the decay job. Graded and reversible beats permanent demotion after a bad week, 902R against 614R, as a drift result.
- **Hard lines.** I found no path from any brake, applier or agent to lowering the kill level, promoting, or blocking an exit. SQS skips exits by text (`G12:178`). The agents' door holds for live; DP33 catches the demo gap.
- **DP7's two records** fit G12's reading of the version pull (`G12:114`). Hand-off 37's "no orders ends inconclusive" is right.
- **Cited numbers I checked against source:** 18.7 %, 2.8x (of ending equity), 97-100 % (with the caveat in M10), 92-99.5 %, 36-93 days, 902/614, A1-087, A1-105, A1-153.
- **Rulings "agents get cTrader's MCP on demo"** (`A/RULINGS-NOW.md:112`) and D44's parking (`SEEDS.md:878`) are real.
- **X4-01 walked:** five units on one USD move. The bet key shrinks the stack at `before_order`; each stop fires and exits run; no unit trips on one -1R; the cushion falls and r falls at the next anchor. This holds even in shape C, as long as bet keys exist.
- **X4-66 walked:** overfit card. CUSUM and the climb catch it at small loss, with or without e-bars ($512 in the sim's +0.03R case).

**Walks that failed:**
- **X4-14:** see M6.
- **X4-62:** a healthy 10-a-day unit loses 8 straight. At -3.2R the brake half and REDUCING take it to about 0.2 of the level. At -5.3R it benches, sits out the next window, runs 5 probes at level 1, then climbs one level per 50 trades after the first warning: about 20 days under full size. The scenario's bar is "costs nothing but the losses" (`X4:831`).
- **X4-69 and X4-88:** see M9.
- **X4-63, a good streak:** no raise inside the anchor, house money off. In the sim the unit spends most of the streak climbing past the e-bars: $551 against $1,394 for the core.

---

## The true core

The smallest set that delivers a self-configuring, extensible template that can go live. **[judgment]** About twelve parts, 25 to 35 builder PRs.

| # | Part | From | What it leaves out for later |
|---|---|---|---|
| 1 | Risk profile document: spec, status; embedded at compile; needs list | DP2 | suggestions, combiners beyond smallest cap |
| 2 | Presets over a short chain: preset, class, instrument, unit | DP1 | seven other keys, reserved |
| 3 | Derivation block on every number, fallback ladder, receipt, refreshed at anchors; his never-self-tune rows | DP3 | learner bounds, applier modes, herding cap |
| 4 | Guard: one package, two adapters, `before_order`, one rank table, one fact set; registry row with a shadow switch and a tail or timing class | DP5, DP19 | certificate as a gate, ramps |
| 5 | Sizer: horizon formula, reserve, cost denominator, round down, re-admission at anchors, level-weighted B | DP9, DP11, DP13 | Kelly ceiling while unproved, lending, QoS, ratchet |
| 6 | Short climb: three or four cohorts, starting level from QMB's holdout; CUSUM step-down, second alarm to paper; the edge dial released by proof | DP15, DP27 | e-bars under baseline, BOIN posteriors, EWOC, pooled cohorts, exploration budget, e-BH |
| 7 | Tail brakes enforcing: own-p1 bench with dollar clamp, retry then lockout; portfolio day stop at `all`; cushion clip; order-boundary clamps | DP17, DP20, DP22 | REDUCING, loss points, count, brake half, density, chorus, burn tiers (all shadow) |
| 8 | Exit socket step 2, disaster stop, cut as a counted two-arm trial; trade row with mechanism; `net_r` | DP11, DP26 | step 3 until the signed stop lands, six refused exits |
| 9 | SQS gate and news window as real first slices; kill level effects; scope keys in the table | DP5, DP24, DP25 | isolation enforcing (shadow), macro, agent evidence |
| 10 | RiskState row, six words, closed reason codes, phone alarm if he says yes | DP30, DP31 | the other twenty observability parts |
| 11 | Machine check in a week, one bound click, pinned versions, two records | DP7, DP28 | the 22-part proof path, canary, challenger, funded e-process |
| 12 | Light harness: sizing and brake replay, three cases, integrated sim, the numbers lens's first tool; agents read and propose through tool rows only | DP29, DP32 | engine import, 89 scenarios beyond the mandatory set, agent jobs, trust ladder, Lab tenant |

**Why this is complete and not thin.**
- It answers "how does it self configure" (part 3).
- It answers "what if I want to change the way it is derived" (part 3).
- It holds "no key setting blank" (part 3).
- It holds "brakes first" (part 7).
- It meets "must go live" (parts 8, 9, 11).
- It is extensible because a new brake, sizer base or tag is a registry row plus a scope key (parts 1 and 4). The set's own "add without rework" claim rests on those same two parts.

**Cut with no loss to the deliverable until the numbers lens or he asks.** Tags and drop-ins. Tier ladder, press, pyramiding, calm-vol scale, AIMD, nomogram. Peer ejection, region shift. Basel zones and Bernoulli density as a demotion key (keep it as a display). Lifetime false-demotion budget. Regime-conditional cones. Trust ladder and the raw-code hatch: only signed `qml` and `human` blocks size live for now. Everything in DP32 past read, propose, the direction field and the cut-only evidence fact.

**What this review did not prove.** Core is a proposal. It beats the picks in one model with no fat tails, no gaps, no lot rounding and made-up edges. The harness must test it against the picks under X4's mandatory scenarios before anyone trusts it. The direction is the finding: the size lost by the stack is far larger than the cushion it saves.
