# H2: sizing, allocation, accelerators, brakes, exits, drift, breakers, the ledger, costs

Harvest, 7 Nov 2026. It recovers what the agents already produced. No new research. No policy decisions. Every number is a report of what a source found, and most are model numbers. Nothing here argues for a dollar goal.

Paths are relative to `D:\QMX-worktrees\risk-plan\tracker\risk-core\` unless they start with `unit-plan/` (`D:\QMX-worktrees\unit-plan\tracker\risk-sizing\`) or `tip/` (`D:\QMX-worktrees\bld-repair-24\`). Ids such as X2-H01 are hybrids in `expansion/`; A1-036 means `linking/components/A1-sizing-allocation.yaml` entry 036 (A2 and A5 the same way). M-numbers are his messages in `seeds/`; Q5, Q13, T1, T2 and D27 are the file keys in `unit-plan/RISK-SIZING-PACK.md` section 2.

**Read tags.** SEAT: the baseline must leave room for it, or the unit gets reworked. CONTENT: a block, template or preset someone adds later with no core change. OTHER SESSION: named. DROP: with the reason.

**Evidence tags.** REAL: live practice, a read paper or a controlled test, and I say which. MODEL: our own simulation; it shows how a rule behaves, not that a real unit behaves so. PROPOSAL: reasoned, untested. GUESS: an analogy or a hunch.

---

## 1. What's here

| File | Read |
|---|---|
| `harvest/BRIEF.md`; `seeds/operator-words-2026-11-06.md` (M41-M53) | full |
| `expansion/X2-sizing-accelerators.md` (62 hybrids, 17 problems, 25 collisions, 8 restructures) | full |
| `expansion/X3-brakes-exits-drift.md` (72 hybrids, 18 problems, 27 collisions, 8 restructures) | full |
| `research/R9-accelerators-and-brake-pairs.md` | full |
| `linking/unit-ideas/A1-sizing-allocation.md`, `A2-brakes-drift-exits.md` | full (they are market readings, so they go to the other harvest areas; used here only where a reading feeds an exit or a size) |
| `linking/components/A1-sizing-allocation.yaml` (174), `A2-brakes-drift-exits.yaml` (270) | every name and evidence line by script; full text of 30 entries |
| `linking/components/A5-topup.yaml` | names of entries 70-90 and 100-150 by script |
| `ledger/v1/core.md`, `NOTES.md` | full |
| `ledger/v1/couplings.md`, `variables.yaml` | header and counts by script; ten rows read |
| `funnel/HYBRID-FATES.md` | full |
| `funnel/FUNNEL.md` | sections B, C, part of D, 5.2, 5.3, 9 (the rest by headings) |
| `funnel/REVIEW.md` | M1-M9 and the true core; headings of the rest |
| `architecture/PICK.md`, `candidate-3/RATIONALE.md`, `candidate-2/out-fork.txt` | full; `candidate-2/SPINE.md` by headings |
| `PARKED-FOR-NUMBERS-TALK.md` | full |
| `expansion/X0-trading-lens.md` | seven hybrids in this area |
| `unit-plan/RISK-SIZING-PACK.md` | section 2 and section 4 in full; section 7 |
| `unit-plan/build/RISK-SIZING-PLACEHOLDERS.md` | full |
| `seeds/SEEDS.md`, `seeds/operator-words-2026-11-03.md` | by headings and script, plus the items quoted below |
| `tip/qml/src/qml/blocks/stdlib`, `tip/qml/catalogue-seed`, `tip/qml/src/qml/protocol/unit.py` | fact checks only |

Not read: R1-R8 in full (cited through X2 and X3), `candidate-1`, `SPINE.md`, `unit-baseline/SWAP-CHART.md` (not on disk yet).

**How I judged (the problem-solving method, run alone).**
- *The problem.* Which ideas in this area change what the unit must carry, and which can wait as things someone paints later?
- *Why the old fates misread it.* The funnel asked "does this survive at a $500 seed and go live soon?" So a fate of "later" often means "not needed on day one", never "does not matter". Three signs of it: pods, the Lab and agent jobs all sit in "later"; the fates are scored against a survival sim; his goal of a large risk without ruin was never a lens at all.
- *Is and isn't.* A hook, record or input is a baseline problem: missing it means rework. A formula, threshold or ladder is rarely a baseline problem: it is one painting on the canvas. Most of the funnel's "core" here is paintings, and some of its "later" is hooks.
- *The main constraint.* Agents never touch money, he alone promotes, exits are never blocked. Everything else is open.

---

## 2. The ideas, best first

### Group A. What makes sizing and brakes a canvas

**I1. Re-size a recorded trade list.**
Take a unit's real or paper trades and replay them under another sizing rule, with no new backtest. It answers "what would this rule have done on these same trades?" He and the copilot could test any sizing idea in minutes. Example: the same 2,000 trades under house money, then under a flat size of the same average.
- From: StrategyQuant's QuantAnalyzer (live product) and proof-card design. A1-170, A2-141, X2-H20, `expansion/X2-sizing-accelerators.md` line 277. The build already keeps the fields for it: `unit-plan/build/RISK-SIZING-PLACEHOLDERS.md` row 29.
- Touches: trade row, Lab, a mini app, the copilot's tools.
- Earlier fate: X2-H20 core only as house money's switch-on path. The go-live lens shrank a general tool to one job.
- Read: **SEAT.** The fields must be on every row. The replay tool itself can come as content. Every "numbers talk" depends on this.
- Evidence: REAL as a product; QMX has none yet. A resample of small fills cannot see what happens at bigger size.

**I2. A sizing base is a derivation; dollars first, lots last.**
A base only answers "how many dollars may this trade lose?" One small block then turns dollars into lots using the instrument's value per point. New sizing idea, new row: no socket change. This is also the answer to his "why lots?": lots are only what the broker accepts at the last step; dollars at the stop are the common currency across instruments.
- From: `architecture/PICK.md` graft 2 (candidate 2); A1-005 (policy kept apart from lot conversion); A1-160 (money from broker tick value, never pips).
- Touches: the unit's sizer slot, QML sizer role, dictionary, the receipt.
- Earlier fate: in the fold, never shown to him.
- Read: **SEAT.** It also fixes a USDJPY fault at its root, per PICK.
- Evidence: PROPOSAL resting on shipped platform code.

**I3. The rule that splits risk across units is its own swappable row.**
His complaint, "the more units I have, the less I can trade", comes from one formula: each of N units gets 1/√(N(1+(N−1)ρ)) of its solo size, about a sixth each for ten units at correlation 0.3. That is one painting. On disk are at least five others: own full size under a parent limit on losing together (X2-H29); his literal day-capital split (A1-088); budget by how few units really trade at once, with borrowing (X2-H30); a few best units until capital allows volume (A1-083, his 5 Oct words); AIMD shares (X2-H31).
- From: X2-H28, X2-H29, A1-085, A1-086, RiskMetrics limit hierarchy (live bank practice); ledger row `b_split_rule` (`ledger/v1/core.md` part 5).
- Touches: pod, portfolio config, sizer inputs.
- Earlier fate: H28 core, H29 "later, merged". The dollar sim drove this, and with a flaw: `funnel/FUNNEL.md` DP9 scores H29 with "X2's fixed-1 % row", which is a different policy. I found no run of a parent limit in X2's Appendix A. Its only figure is the lead's 11:07 sim quoted at X2-H29 (11 % floor touches against 5.8 % for one unit, at half the edge).
- Read: **SEAT** for the row; each rule is **CONTENT**, and this is pod territory.
- Evidence: REAL for parent limits in banks; MODEL for the rest. The H29 option is unsimulated.

**I4. House money and reverse house money are one rule. The anchor decides which it is.**
Keep one ledger of profit since a chosen starting point. Size = (allowance + profit so far) ÷ allowance. Below the start it shrinks: that is his reverse house money. Above it, it grows: house money. Anchor it to a fixed point and it does both. Anchor it to the running peak and it can only brake. Example from R9: with a 1 % day limit, +0.5 % on the day gives 1.5x; with a 10 % limit, 1.05x.
- From: Grossman-Zhou 1993 and the Hsieh-Barmish lemma (read in R9 §0.4); `research/R9-accelerators-and-brake-pairs.md` §0.4; X2-H10; X0-05; A5-118; his 6 Oct "bloody brilliant" (`unit-plan/RISK-SIZING-PACK.md` 2.3).
- Touches: unit's size multiplier, cushion ledger, pod, block in QML.
- Earlier fate: core at the portfolio ledger, accelerator half in shadow. Go-live lens and dollar sim. He asked on 7 Nov what "a rule I approve" means there and it was never explained (M49).
- Read: **SEAT** for ledger, anchor and scope rows; shapes (straight, April's curve, sigmoid) are **CONTENT**.
- Evidence: REAL theory. MODEL: no gain on independent trades, +37 to +42 % growth per risk under regimes, and A5-118's tail of 73 % of paths over a 25 % drawdown in slow regimes.

**I5. One row for every brake or accelerator.**
Every control states: what it reads, whose risk, measured from where, which lever, which direction, what shape, how fast on and off, what stops it chattering, what it remembers and who clears it. Plus its counting rule, what it does if data is missing, which money series it uses, how often it should fire on a healthy unit. "5 % drawdown" can then no longer mean four things. A new brake is a new row, and with graft 7 of PICK one folder in the dictionary.
- From: `research/R9-accelerators-and-brake-pairs.md` §0.2; A5-106; X3-H58; X1-H14; `architecture/PICK.md` graft 7; audio compressor vocabulary (R9 §0.2).
- Touches: dictionary entry shape, QML halt and motion roles, pods, UI, agents' read tools.
- Earlier fate: core. Here the go-live lens agrees with this lens.
- Read: **SEAT.** This is what lets his "I can't agree to all this, it's circumstantial" stay true.
- Evidence: PROPOSAL; MQL5 risk managers make the basis a declared choice.

**I6. Two ledgers: money for brakes, events for decay.**
Money ledger: a fast-invalidation cut costs its size, a breakeven costs its fees. Event ledger: cut rate, scratch rate, full-stop share, stop slippage, time to cut. Brakes act on the first; the second is early decay evidence. It needs every closed trade to record which mechanism closed it. R9: a unit that cuts losers early trips "3 in a row" on 60 % of days against 41 % for the same edge without cuts; counting a breakeven as a loss doubles a count brake's firing.
- From: R9 §4.1, §4.3; A5-145; X3-H04; X3-H45; A2-260; his "breaks ... also take into account ... first invalidation" (M12).
- Touches: trade row, journal kinds, every brake.
- Earlier fate: core. Event rates in shadow.
- Read: **SEAT** for the fields. Today a time exit, a signal exit and a cut all read "close" (G11, quoted at X3-H45).
- Evidence: MODEL plus REAL document practice.

**I7. An exit stack fed with the position.**
Several exits at once on one position, each seeing quantity, stop, bars held and best and worst excursion; each may close all, close part or tighten. The safest wins by a declared rank. His point (M49) holds: the dictionary already holds the closing mechanisms, so the risk session should use them, not ask him whether a rule may close. The facts: 9 exit blocks and 5 halts ship in `tip/qml/src/qml/blocks/stdlib`, 57 exit-family candidates with no numbers in `tip/qml/catalogue-seed/stats-2026-08-26/invalidation-exits-and-management/`, 16 more in `wave-1/exits-and-halts`. But at the tip the host runs only the first per-bar exit (`tip/qml/src/qml/protocol/unit.py:447`) and its check permits only `close_full` (`tip/qml/src/qml/check/layer_g.py:375`), while the planned slot contract promises the position and all three verbs.
- From: X3-H43, X3-H46, A2-258, A2-259, `unit-plan/build/RISK-SIZING-PLACEHOLDERS.md` slot table, `unit-plan/research/34-grounding-qml-and-dictionary.md:210`.
- Touches: unit exit slot, compiler, QMB and node hosts.
- Earlier fate: core step 2; step 3 (partial close, tighten) "later". Go-live lens.
- Read: **SEAT.** Without all three verbs, trailing, scale-out and breakeven are locked out, so "later" here means rework.
- Evidence: REAL for code facts; PROPOSAL for the stack.

**I8. Costs are observed facts; rules read them.**
QMX measures spread, commission, slippage and carry per instrument, broker, hour and world, and shows them. Then something reads them: a unit skips an instrument on its news day, shrinks in a costly hour, or ignores it. "Facts move live, numbers move at anchors": a spread is a fact the sizer reads at once, with no learned number moving. This is exactly his "think of QMX as a data analyst" (M51).
- From: `architecture/PICK.md` graft 11 (candidate 3); `ledger/v1/core.md` `hourly_cost_profile`; A1-147, A1-146, A1-143, A1-144; X2-H39; `PARKED-FOR-NUMBERS-TALK.md` "Not parked".
- Touches: instrument record, node order rows, sizer inputs, SQS, MIS calendars, Lab.
- Earlier fate: core. Driven by go-live; but picked with an admission gate as law (see I62).
- Read: **SEAT** for the record and the writer of it from fills. X2 says flatly that no slippage is measured anywhere yet and no commission key exists.
- Evidence: REAL hourly-spread research (NBER, in G7); rest PROPOSAL.

**I9. Speed by kind of signal.**
Money facts (day loss, drawdown) act at once. Edge estimates (live against backtest) act slowly, in small reversible steps. Growth is slower than either. This reconciles his two statements, "size down, but not quickly" and "we don't lose stupidly". R9's table: TCP, Netflix, Topstep and pods all cut fast and grow slow; heparin acts fast both ways because under-dosing also harms.
- From: R9 §3.2; A5-139; X2-H27; X3-H49.
- Touches: brake rows, motion rules.
- Earlier fate: core.
- Read: **SEAT** as attack and release fields on the row; the values are **CONTENT**.
- Evidence: REAL in other fields; PROPOSAL here.

**I10. A money brake at the unit's own percentile.**
Instead of "two stops and out", watch the unit's own running result over a window of at least ten trades and bench it at a level read from its own record. A scalper and an opening-range unit then fire at the same rate. R9: a unit's own 1 % worst day is −4R at 4 trades a day, −10R at 40; the old "2 full stops" keeps 18-65 % of a healthy unit's R at 10-40 trades, this keeps 99 %+ (MODEL). Honest limit: it earns about +1R over a random brake at most frequencies. Its job is the tail and its fire record, not timing.
- From: X3-H01, X0-16, A5-144, A2-078; `funnel/FUNNEL.md` DP17; prop and pod rules are all in money (R9 §4.4).
- Touches: halt slot, card, guard.
- Earlier fate: core. Survival lens; it fits this lens too, as a default.
- Read: **CONTENT** as the rule; **SEAT** for what it needs: a window in trades, own-record statistics reaching the halt slot.
- Evidence: MODEL; REAL that all live firms use money, not counts.

**I11. What a brake does is configurable per pod: stand-down, kill level, or card.**
Keep two meanings of "stop" apart. The kill switch is his. Rules raise stand-downs at a scope (instrument, unit, class, region, currency, underlying, session, all), each with a reason and a clear rule. Whether a portfolio stop raises the kill level was asked of him as a rule. He answered it is a pod question (M49 question 5). So the action must be a field, never a law.
- From: X3-H62, X3-H35, X3 P15's three options (`expansion/X3-brakes-exits-drift.md` line 996); A2-097.
- Touches: stand-down table, pods, UI.
- Earlier fate: core, framed as a question to him.
- Read: **SEAT** for scope keys and the action field; each choice **CONTENT** in a pod.
- Evidence: running code for scopes; PROPOSAL.

**I12. Every number carries how it derives.**
Each number has a derivation he can swap, a receipt, a fallback (own record, then class, then preset), which way a missing input pushes it, and a guard that reverts and freezes it after repeated trips. A learner may publish target and bounds; an authority mode per number says who applies it. He can change how it derives, not only its value. His own word was self-configuring; his game-dev seed fits.
- From: Kubernetes VPA and HotSpot (checked in R7); X2-H51, X3-H61, A4-001..006; `ledger/v1/core.md` part 3; PICK F-A.
- Touches: number spec, compiler format, Lab, agents.
- Earlier fate: core with simple modes. Note `x1_never_self_tune_list` was filled with go-live ids (floor, kill level): under the canvas lens the list should be per template, which the row already says.
- Read: **SEAT.**
- Evidence: REAL in software; never run on a trading unit.

**I13. A rule may read unit-level, pod-level and account-level statistics.**
The stale view says a sizer reads equity, entry and stop. X2 lists what every hybrid needs: budget share, committed cushion, open risk per bet key, the unit's record (spread of results, edge band, cut distribution, trade rate), cost for this hour and world, gap factor, level, trading state.
- From: X2 restructure 3, X1-H58, `unit-plan/RISK-SIZING-PACK.md` section 4 item 4.
- Touches: sizer slot contract, compiler.
- Earlier fate: core, narrowed by PICK graft 2 to a thin surface over derivations. The two are compatible only if derivations may read all of it.
- Read: **SEAT.**
- Evidence: PROPOSAL.

### Group B. Methods for a large risk per trade without ruin

These are methods. None argues for a target. He framed the question on 7 Nov: "how do we make sure we can achieve this, but without getting ruined?" (M51). **No design on disk used that lens** (see Gaps). Every method below was built for something else and is read here for what it offers.

**I14. Risk only the cushion above a fixed dollar floor.**
Size is a share of the money above a floor, not of the whole account. As equity grows, the share per trade rises by itself. G6's reading of the GitBook ladder: 2.9 % of equity per R at $250, 8.6 % at $500, 12 % at $1,250. Fall toward the floor and it shrinks by itself. Ruin in the sense of the whole account needs a gap past the floor.
- From: A1-042, A1-036, A1-041, A1-038, R9 §0.4 (CPPI shape), `grounding/G6-book-bms-levels-and-paper.md` as cited there.
- Touches: sizing base, floor row (user-set), pod.
- Earlier fate: "(f) the GitBook ladder" blocked in DP9 at 88-97 % floor touches with ten seats. That sim runs ten seats at full price each; it never tested one or two units. The dollar sim drove it.
- Read: **CONTENT** (a base). Worth a run at N = 1 and 2 before anyone repeats "blocked".
- Evidence: REAL theory; never ran live in QMX.

**I15. Ring-fence the stake.**
Give units only part of the money and keep the rest out of reach. His words: "give units $100 to $200 and let them grow". A wipe-out then costs the stake. Variants: raise the base and send the rest elsewhere (A1-077, his sweep concept); sweep above a high-water mark at pod level only (A1-076); lock a share of each new high (X2-H56, a ratchet: 0 is pure compounding, 1 is a trailing floor).
- From: A1-136, A1-077, A1-076, A1-075, X2-H56, SEEDS C11.
- Touches: portfolio config, banker acts, UI levels.
- Earlier fate: ratchet "later"; go-live lens. `out-more-arith.txt` J: a 25 % lock raises idle money from 30 to 42 % when equity doubles.
- Read: **SEAT** for banker acts re-deriving every anchor; the rest **CONTENT**.
- Evidence: REAL as fund high-water marks and Grossman-Zhou; MODEL here.

**I16. Make each loss smaller, so each bet can be bigger.**
Fast invalidation shrinks the spread of results. The survival formula then pays more dollars per trade for the same chance of touching the floor, and the tail-loss form says "FI units may size up honestly, because their real average loss is smaller". X0-13's arithmetic: a 78 % scalper with cuts at 0.35R on half its losers goes from EV about 0.09R to about 0.25R.
- From: X2-H01 (s with cuts), X3-H44, A2-250, X0-13; his "That's high, bruv. You haven't considered invalidation" (A9).
- Touches: sizer inputs, exit block, trade row.
- Earlier fate: formula core; "exits feed the sizer" later. Survival lens.
- Read: **SEAT** for the realised loss distribution as an input; rule **CONTENT**.
- Evidence: MODEL, with a hard caveat from `funnel/REVIEW.md` M4: if the cut also catches winners, +0.086R falls to +0.012R at 10 % and −0.062R at 20 %. No paper tests fractional cuts after costs (R8 gap 2). The whole method rests on a two-arm test per unit.

**I17. Concentrate: few units, best basket.**
The split formula rewards fewer truly independent units with larger shares. One unit on one bet gets the full size. Variants: fill the few slots with the best performers until capital allows volume (A1-083, his 5 Oct); poker-style bands that open another slot only when the pot holds enough of that slot's day budgets (X2-H37); admit units in order of which instruments are feasible at this size (X2-H45); rank placement by n × EV² / s² (A1-133).
- From: A1-083, A1-081, A1-133, X2-H37, X2-H45, his 29 Oct "300 can be grown by only one or two units" and M50's basket words.
- Touches: pod, MIS placement, Lab.
- Earlier fate: "(c) fewer, larger units" rejected at DP13 as "against his C1"; poker bands later. Go-live lens. M50 overrides that reading at this capital.
- Read: **CONTENT**, needs I3's row and a feasibility record. Warning kept: A1-103, ranking by recent results chases noise.
- Evidence: PROPOSAL; poker bands are practitioner lore.

**I18. Press with winnings only.**
Extra risk comes only from realised profit since the anchor, capped to a share of it, so the scope cannot end below its anchor because of the extra size. Firm-side form: Apex legacy accounts trade half size until balance passes start + allowed drawdown + $100.
- From: A1-067, A5-116, A5-122 (Apex, snippet), R9 §1.4, X2-H10, X0-19.
- Touches: size multiplier, realised-profit fact.
- Earlier fate: shadow until proof. Dollar sim plus go-live. R9's finding stands: on independent trades it is a size increase in disguise.
- Read: **CONTENT**, needs I4's seat.
- Evidence: REAL prop rule (snippet); theory; MODEL.

**I19. Cut hard after a bad day, so the average can sit higher.**
AIMD: multiply size by 0.7 after a bad day, add a little after a green one, slow near the last trip level. In R9's script it ran at 0.79x average risk, with the same growth per unit of risk, and a 0.5 % chance of a 25 % drawdown against 1.3 % for a flat 0.8x. So a path-dependent brake reshapes the tail, which is what a higher base would need. As a pure brake capped at baseline it chokes (X3 sim: 32-84 % of healthy R kept). Same mechanism, opposite verdicts: X3 collision 15.
- From: A5-133, X2-H26, X3-H07, R9 §3.5, A2-040, TCP and Netflix.
- Touches: size multiplier, day ledger.
- Earlier fate: "later"; judged on the cost at baseline, never as an enabler of a larger base.
- Read: **CONTENT**.
- Evidence: REAL in networking; MODEL; fat tails and gaps make every number worse.

**I20. The largest size that keeps a stated floor chance.**
Say what you accept, then solve for size. Options on disk: survival formula with a dial for how much edge to believe (X2-H01, H03; zero edge to low edge moved the median from $2,213 to $5,854 in its sim, at zero touches); Kelly fraction with P(wealth below α) under β, one convex problem (A1-024, X2-H05); pick the hyperparameters by median wealth subject to at most 5 % of runs falling below 90 % (A1-171, three sports with real data: plain Kelly ruined every run without a real edge; fractional was strong); average Kelly over uncertainty, with the haircut estimated, not assumed at half (A1-022).
- From: paths named; `research/R6-alphaxiv-papers/T-05-sizing-uncertain-edge-and-breadth.md`.
- Touches: sizing base, floor tolerance row, Lab.
- Earlier fate: H01 core; H05 "later, swappable". Survival lens.
- Read: **CONTENT** (bases). `floor_touch_tolerance` is a row a user may set anywhere. X2's "0 % touches" is partly structural, since it recomputes size each morning.
- Evidence: REAL for A1-171 and A1-024-type papers; MODEL for H01, which ignores jumps and has no real-data test.

**I21. Reserve for the one move that really ruins.**
Before sizing, take off the loss if the largest bet gaps to its class's worst move (N-1 from the power grid), or the worst credible event per exposure zone (from reinsurance). Then each trade's worst step plus costs must fit what is left. At a large size this term matters most, because brakes cannot act inside a gap.
- From: X2-H07, X3-H25, X3-H75, A1-038, A3-028, A2-264. Hsieh's own BTC run ended at 20.18 % drawdown against a 20 % cap.
- Touches: sizer, guard, order veto, class table.
- Earlier fate: core. Fits this lens.
- Read: **SEAT** for the hook; the worst-step table is **CONTENT**, per class, and does not exist yet (X2-C16).
- Evidence: REAL in their fields; the table is the weak link.

**I22. A step ladder earned by profit, stepped down the same day.**
Topstep: up one tier only after 10 active days in it, down the same day if profit falls below the tier, counter resets on drop-out, no skipping, no rise mid-session. On a $100K account $3,000 → $3,500 at $15k profit. It is the strongest live pair R9 found. Widths could be multiples of the unit's own day allowance.
- From: Topstep help pages (read in R9 §1.5), A5-123, A5-124, X2-H18, X0-29; FTMO consistency rule A1-079.
- Touches: size multiplier, tier record.
- Earlier fate: shadow, go-live lens.
- Read: **CONTENT.**
- Evidence: REAL rules; no published effect. On independent trades tiers add risk, not growth per risk.

**I23. Press only when the unit's own results persist.**
Test the unit's own block results; if blocks really carry over, size up after a good block and ease after a bad one, with a dead band. Script: 1.156 against 0.604 growth per risk under slow regimes. Factors: 52 bp a month after a good year, 1-2 bp after a bad one, and most of that value came from dropping losers, the brake half. It breaks abruptly and for many at once, so one book-level off switch.
- From: Ehsani-Linnainmaa (read, R9 §1.3), Miller-Sanjurjo streak bias (read), A5-121, A5-131, A5-132, X2-H19.
- Touches: size multiplier, record.
- Earlier fate: shadow.
- Read: **CONTENT.** The block test is a Lab tool too (a 500-trade regime shows in about 950 trades).
- Evidence: REAL at monthly factor level. No study of intraday retail persistence after costs.

**I24. Size where the edge is, in time: measured windows.**
A "sniping window" is a slice of hours where the unit's measured net edge after costs is higher out of sample. Risk concentrates there for a real reason. X2-H40 deletes the free session multiplier; his own words want more "if there is proof that it performs".
- From: A1-070, A1-069, X0-47, X2-H40, X5-H47, X7-H25 (agent prospector), T1:442 in the pack; collision X2-C07.
- Touches: cost cells, sizer, QML session filters, agents, MIS.
- Earlier fate: lift deleted (core); windows later. Go-live.
- Read: **CONTENT**, needs the per-session record (I65). Deleting the lift by law conflicts with the canvas: keep it as an option a preset can use.
- Evidence: MODEL and author backtests; counting tries is the guard.

**I25. Taper as you near a goal.**
Near a phase's profit goal the account is like a deep in-the-money option: little to gain, plenty to lose. Size shrinks on approach. Paired with: a wind-down mode that stops new trades after a profit lock (A2-058).
- From: A1-047 (MQL5 24250), A2-058.
- Touches: size multiplier, pod phase.
- Earlier fate: never made a hybrid.
- Read: **CONTENT.** The author calls it "a motivation, not an argument"; it only fits if a goal is a real boundary.
- Evidence: article simulation.

**I26. Restart after a near-breach, with less size.**
When drawdown comes close to its limit, reset it and restart with a smaller gain. VT out of sample +20.97 % with restart, −8.42 % without; BTC Sharpe 1.52 against −0.04, one asset each. It re-arms a unit that would otherwise be dead, but voids "never beyond the cap" across restarts. Paid forms: refill for a charge (reinsurance), with a proof that grows with the refill (X2-H57); a refund reserve (A1-078).
- From: Hsieh 2023 2303.02613 (read), A1-039, A2-013, A5-130, X2-H57, X3-H18.
- Touches: pod, banker acts.
- Earlier fate: "later" and "wild".
- Read: **CONTENT.** One seat: the true floor is never reset by a restart (AD-17 in `architecture/candidate-2/SPINE.md`).
- Evidence: REAL paper, one period, in-sample gain; insurance snippet.

**I27. Stack methods by capital stage.**
His logic: first a cash base, then breadth ("at 5,000, the math changes drastically"). On disk the nearest forms are equity bands with tier caps (A1-109), poker bands, the fixed-dollar floor, and A1-081's "grow the seed first with the most likely edges". A preset could swap sizing base and split rule at a stage line, on the pod's ledger.
- From: A1-109, A1-081, X2-H37, `ledger/v1` `equity_band` rows, M51.
- Touches: pod, preset switching, version identity (does a stage change make a new unit version?).
- Earlier fate: `equity_band` shadow.
- Read: **SEAT** only for one thing: a pod can change a unit's sizing row at an anchor, by a declared rule, with no new unit identity. The rest **CONTENT**.
- Evidence: GUESS as a stack; parts are old rules.

**I28. Audits that catch hidden ruin.**
Scan a unit's history for size rising after a loss, stacking at worse prices, payoff asymmetry and the classical ruin formula; grade A to F. Plus a firewall: no size rise after a loss unless a declared contrarian rule says so on a card. And the Monte Carlo trap: "5 % risk is stable" came from an assumed 83 % win rate. Run it with the edge estimated, or it proves nothing.
- From: A1-172 (MQL5 23673), A1-008, A1-080, X2-H60, A5-115.
- Touches: preflight, Lab, agent workflow.
- Earlier fate: firewall core. As a hard rule it blocks a grid unit someone may want to paint.
- Read: **CONTENT** as an audit that warns and informs; per the canvas a contrarian rule stays allowed with a card, which H60 already says.
- Evidence: author tools; REAL failure backtests.

**I29. Negative-skew units get a separate tail budget.**
Many small wins and rare big losses: size is the smaller of the stop budget and a tail budget from the unit's own record plus stressed slippage. Mean-reverting scalpers are the case. Symmetric units keep full size.
- From: A3-008, A2-250, X2-H08, X0-20.
- Touches: sizing base.
- Earlier fate: later, because "first units" reasoning. Scalpers are his first units, so "later" looks odd.
- Read: **CONTENT.**
- Evidence: simulation; a short record has no tail, falls back to class.

**I30. Margin as a bound of its own.**
A large size meets leverage, margin and liquidation before it meets any risk rule. Margin headroom, regulatory caps per class, a stop refused past the liquidation price, a leverage change standing a symbol's units down.
- From: A1-158, X2-H06, A2-262, `unit-plan/build/RISK-SIZING-PLACEHOLDERS.md` rows 14-15, X4-67. He asked about leverage on 6 Oct.
- Touches: order veto, account record.
- Earlier fate: core.
- Read: **SEAT** (facts and check), limits are his rows.
- Evidence: running code in part. X2 gap: margin increases in stress modelled nowhere.

### Group C. Other accelerators and growth shapes

**I31. Slow start with a first-warning switch.** Big steps from a small size while nothing is wrong; the first graded warning switches to small steps. FDA titration: ≤100 % dose steps until the first grade 2 event, then ≤50 %. TCP slow start. *From:* Rogatko 2015 (read, R9 §1.6), A5-127, X2-H14. *Touches:* level multiplier. *Fate:* merged into the level ladder, core. *Read:* **CONTENT**. He asked "what is a starting level?" and said QMB's proof setting it is "no" (M49), so no ladder belongs in the baseline; only a level slot does (I77). *Evidence:* REAL in medicine; PROPOSAL here.

**I32. Falling-risk pyramiding.** Add to a winner only if total risk on the bet does not rise. Turtle adds; adds re-sized from current baseline. *From:* A1-071, A5-120, X2-H21, X0-35. *Touches:* exit slot's amend, entry adds, bet key. *Fate:* later; compiler's `position_limit` refuses it. *Read:* **SEAT** for several positions per unit (his A8), **CONTENT** for the rule. *Evidence:* author backtests; gaps skip the stop.

**I33. Calm-volatility scaling with a guard.** Raise size when markets are calm, cap it, freeze raises after long calm, cut on spikes at once. Sharpe gain for risk assets only; tails cut everywhere. Long calm precedes crises. *From:* Harvey 2018, Danielsson 2018 (abstracts, R9 §1.7), A5-129, X2-H22. *Touches:* size multiplier. *Fate:* later. *Read:* **CONTENT**. Double-counts for stop-sized units (X2-C19). *Evidence:* REAL backtests; Cederburg: gain did not hold in real time across 103 strategies.

**I34. Probe for capacity.** Run a cohort at 1.25x, then 0.75x, then 1.0x; keep the higher size only if fills held. A proven edge meets the venue's limit: bookmakers cut a winner to $1.25 a bet. *From:* BBR (snippet), Kaunitz 1710.02824 (read), A5-135, A5-148, X2-H23. *Touches:* record, caps. *Fate:* later, wild. *Read:* **CONTENT**, at scale. *Evidence:* REAL for the betting limits; no trading test.

**I35. Overdose control on size steps.** Raise a level only while the chance the next level is too big stays under α, from resampling the unit's own trades. *From:* EWOC (read, R9 §1.6), A5-128, X2-H16. *Touches:* Lab replay. *Fate:* later, wild. *Read:* **CONTENT**. *Evidence:* simulation in dose-finding.

**I36. Bounded-cost exploration of a bigger size.** Play the larger level only while a lower bound on results stays above most of what the smaller would have made. A relative floor can pass a losing book. *From:* A5-037, A5-038, X2-H17. *Fate:* later, wild. *Read:* **CONTENT**. *Evidence:* bandit simulations.

**I37. Agents breed sizing profiles.** Agents mutate a sizing profile inside his ranges, judge each by resize replay, the scenario battery and the random-entry chassis, count every try, shrink the winner, and put the survivor on a card. A conservative bandit over a few signed profiles is the online form. This is his "hill climb challenge" (M49) and the blacksmith picture (M50). *From:* X2-H54, X2-H53, A4-182, X7-H24. *Touches:* Lab, mini app, copilot, overnight workflows. *Fate:* later, wild. Dollar and go-live lens; the wild tag did the filtering (`funnel/REVIEW.md` M1). *Read:* **CONTENT**, and worth re-rating; needs I1 only. *Evidence:* GUESS; WF1 and WF2 by analogy; overfits the replay period.

**I38. Above capacity, growth buys breadth.** When a unit hits its venue cap, new money opens a new deployment of the same logic on a low-correlation market. *From:* X2-H38. *Fate:* later, wild. *Read:* **CONTENT**, pod rule. *Evidence:* analogue (beekeeping).

**I39. Risk classes with lending.** Each unit has a guaranteed share and a burst limit. Proven units keep size under pressure; idle pots lend slack, recalled at their next open. Overbooking is the same idea. *From:* Kubernetes QoS (production), A4-188, A1-121, X2-H30, X2-H29. *Fate:* later. *Read:* **CONTENT**, pod. Answers "idle money is a cost". *Evidence:* REAL in software.

**I40. A book thermostat.** One controller holds the book's realised daily swing at its target by moving one scale on all units. *From:* X2-H55, A4-009. *Fate:* later, wild. *Read:* **CONTENT**; noisy with few days. *Evidence:* GUESS from PID practice.

**I41. Size by setup quality or calibrated probability.** Grade setups, give weaker classes less; or trade only above a hurdle and step size by how far probability sits above break-even, averaged across active bets. Closest thing to a human's conviction. *From:* A1-035, A1-033, X2-H61, A5-044. *Touches:* unit logic to sizer signal. *Fate:* later. *Read:* **SEAT** for a unit passing a conviction number to its sizer through a binding; rule **CONTENT**. *Evidence:* in-sample and author backtests.

**I42. Lot dither.** Carry the rounding remainder so average risk meets target; a single trade may run above plan. *From:* X2-H46. *Fate:* dropped. *Read:* **CONTENT** at most: harmless as an option; a user may want it on gold at small size, and "never round up" need not be law if the row says so. *Evidence:* analogue only.

**I43. Meta-allocators in the Lab.** Hierarchy decides who gets risk, a capped fractional rule sets only the total; NCO, HRP, inverse volatility; bounded learned tilts; shadow ablation to see whether the adaptive layer earns its place. Fixed sleeves often beat clever weights (A1-099). *From:* X2-H32, X2-H59, A5-018..025, A1-093..095, A1-100. *Fate:* later. *Read:* **CONTENT**, Lab. *Evidence:* author backtests.

### Group D. Brakes and circuit breakers

**I44. Graded ladder: reduce before bench.** Halve at the unit's own 10th percentile, bench at its 1st. In bad spells it adds +3 to +43R over no brake and cuts the p95 drawdown (fi40 178 → 143R). *From:* A2-023 (grid load shedding), X3-H02. *Fate:* shadow, to meet "one reading of the running loss binds". *Read:* **CONTENT**; "one reader per ledger" should be a preset's choice, since at compile it refuses a second live reader (PICK graft 3), and that compile refusal is a rigid law to reconsider. *Evidence:* REAL grid practice; MODEL.

**I45. Loss points.** A full stop costs 1, a cut costs its size, a breakeven its fees. He called it brilliant and later asked "based off what?". Weak alone. *From:* A2-091, A1-050, X3-H03, Q5:1466, Q5:1739. *Fate:* shadow. *Read:* **CONTENT**, a block over I6. *Evidence:* October proposal, never ran; MODEL.

**I46. His losing-run brake, made fair.** Count only qualifying losses; trigger at a run longer than the unit's own p90-p95 run for its rate; halve, not bench. Scaled to p99 it became 5 to 10 straight losses, at or above the six he called very high, so "three" needs telling. *From:* A2-129, X3-H05, FUNNEL DP17, his A6. *Fate:* shadow. *Read:* **CONTENT**. *Evidence:* MODEL for the fixed form only.

**I47. Streak brake only where results persist.** Stays in shadow until the unit's block test passes: count brakes earned +20R over random in bad spells at a 16-26 % healthy cost. *From:* X3-H06. *Fate:* shadow. *Read:* **CONTENT**. *Evidence:* MODEL.

**I48. Two-speed circuit breaker.** His old breaker improved: fast half is I10; slow half reads the fast half's fire record. Fires at a known healthy rate behave like a VaR exception count, so Basel's green, yellow and red zones apply. Calm but slow (median 36-93 days). *From:* A2-083, A2-086 (WF3), A2-088, A2-126, A2-196, X3-H08, his A26. *Touches:* card, mini app. *Fate:* fast half core, slow half display. Go-live. *Read:* **CONTENT**; he named this the baseline brake, so a default preset should show it. *Evidence:* REAL Basel; MODEL.

**I49. Expected fire band on the card.** At card time, run the holdout through every brake on bootstrapped paths and store expected fires. Live fires are then read against a band, never a feeling. Never filled in any generation. *From:* A2-088, A2-227, X3-H09. *Fate:* core. *Read:* **SEAT** as a card field; the producer **OTHER SESSION** (methodology, QMB). *Evidence:* PROPOSAL.

**I50. Portfolio day stop reading its own swing.** Book day loss past a multiple of the book's sized day sigma raises a stand-down at `all`. The first version at budget sigma never fired in the harder sim. Candidate 2 derives k from the group's own p1 day. *From:* X3-H24, FUNNEL DP22, section 9, PICK graft 10. *Fate:* core. *Read:* **CONTENT** as a pod rule. *Evidence:* MODEL.

**I51. Portfolio breaker on stacked evidence.** Stops new entries when K of N classes isolate, or budget burns fast, or chorus exceeds expectation. His "switch off entirely", with a fire-rate target. *From:* A2-122, A2-127, A2-072 (exchange breakers), X3-H24. *Fate:* later, beyond the day stop. *Read:* **CONTENT**, a pod. *Evidence:* REAL exchange breakers; no QMX multi-unit history.

**I52. Losing together counts once.** Losses from one shared driver in one window count as one event in all counts above the unit; money still counts in full. Five stops on one USD release are one bad event, not five strikes against five healthy units. From the insurer's hours clause. *From:* A2-026, X3-H20, X2-H11, X4-91. *Touches:* driver tags, journal. *Fate:* shadow. *Read:* **SEAT** for driver tags on instruments; rule **CONTENT**. *Evidence:* REAL in insurance (vendor blog).

**I53. Chorus breaker.** A cluster trips when K of N members fire inside one window, with K from measured correlation. *From:* A2-089, X3-H21, X6-34. *Fate:* shadow. *Read:* **CONTENT**, pod. *Evidence:* July spec, never ran.

**I54. Burn-rate permit.** Watch the loss budget over a long and a short window: fast burn halts, slow burn sizes down, healthy permits accelerators, spent freezes them. Replaces the undefined "door". *From:* Google SRE, A2-028, A2-029, A5-141, X3-H22. *Fate:* shadow. *Read:* **CONTENT**. *Evidence:* REAL in SRE. A gap spends the budget in one step.

**I55. Class, region and market isolation.** Two tells must agree (spread and volatility against usual for this hour, correlation surprise, turbulence), then no new entries; graded; ends on evidence with a staged resume and growing back-off; unknown data counts as danger for that scope only. Includes SQS K-of-N class caution, which catches a quote pull with no price move. *From:* X3-H28, H29, H33, H35, H36, A2-119..123, his C27. *Touches:* MIS, SQS, stand-down table. *Fate:* scope keys core, the rest shadow. *Read:* **SEAT** for scope keys and fail-closed read, **CONTENT** for the protocol. **OTHER SESSION** (MIS and SQS harvest) holds the readings. *Evidence:* daily-data author backtests; no intraday test.

**I56. Pod-style step ladder on capital.** Halve a unit's share at a first drawdown line, stop new risk at a second, with lines from its own bootstrap and widening with time in service. Pods: −5 % and −7.5 % (press). *From:* A2-073, A1-104, A5-022, A5-146, X3-H26. *Fate:* later. *Read:* **CONTENT**, a pod, as he asked for pod ideas. *Evidence:* REAL (press-reported). Pods never restore automatically.

**I57. Peer ejection.** A unit below its peers' mean minus k deviations is ejected for a time that grows with repeats, with a cap on how many at once. *From:* Envoy, A2-033, X3-H30. *Fate:* later. *Read:* **CONTENT**; at 200 units this becomes useful for an agent workflow. *Evidence:* REAL in software.

**I58. Five states, one rank table.** ACTIVE, REDUCING, BENCHED, HALTED, RESTORE per scope. Any brake blocks every raise. Only HALTED needs his hand. The stack today can only stop. Copying Nautilus as-is would block stops, so not that part. *From:* A2-112, A2-046, A5-138, X3-H59, X1-H10; he asked "what do you mean by unit stepping down?" (M49). *Fate:* core. *Read:* **SEAT.** *Evidence:* REAL (Nautilus); reversible steps kept 902R of 950R after a bad week against 614R (MODEL).

**I59. Restore family.** Half-open probes judged as a group, a growing cool-down, lockout after K fails; memory ceiling: regrow fast to below the last trip level, slow near it; level lock after two trips; probe on the paper twin if the lot is too big; refill priced in evidence after a slow demotion. *From:* resilience4j, reclosers, TCP, BOIN; A2-007, A2-022, A2-032, A5-134, A5-137, X3-H15..H18, X2-H15. *Fate:* retry-then-lockout core, rest later. *Read:* **SEAT** for the RESTORE state and a settle hook; methods **CONTENT**. *Evidence:* REAL elsewhere; a few probes prove the machine and the conditions, not the edge. His rule on who promotes stands: `unit-plan/RISK-SIZING-PACK.md` 2.9.

**I60. Random-control certificate and brake scorecard.** Replay a brake against a random brake with the same fire rate; report precision, recall, detection time, trip tax. Any brake looks good on a losing strategy. A tail brake's certificate would take about 60 unit-years, so it is a report, not a gate. *From:* MQL5 23482 (one small fair test, all three arms lost), A1-173, A2-135..143, X3-H12, H13. *Fate:* shadow report. *Read:* **CONTENT** with the Lab; the would-have rows are **SEAT**. *Evidence:* REAL single test.

**I61. Other brake seeds.** Each **CONTENT** unless said.
- Day-boundary contract: rolling windows, persisted counters, a bench carries a minimum rest over midnight; closes the 23:50 hole. A2-011, A2-064, A2-116, X3-H74. Core. **SEAT.** Demo tests.
- Get-even flag: any size increase right after a loss is flagged; refused for agents, warned for him. Nasdaq traders paid $4,300-14,400 a year for this habit (Garvey et al., read in R8). A5-085, X3-H69. Shadow.
- Changepoint cooldown per instrument: the one fast brake with a fair test (drawdown 856 → 756, 4 of 97 trades skipped, all arms lost). A2-162, A2-163, X3-H72. Shadow.
- Execution-anomaly pause on odd fills. A2-061, X3-H71. Shadow. Pause only, never widen.
- Danger accumulator (weak signals sum, clear danger acts at once). A2-070, X3-H66. Wild; GUESS.
- Brakes stake testing wealth and retire themselves. A2-220, X3-H67. Wild; GUESS.
- Regime-age taper on adds. A1-048, A2-173, X3-H73. One 8-month gold test.
- Staged shedding by priority when the book tightens. A2-035, X3-H27. Later. REAL at Google.
- Region blocked, freed budget kept as reserve, not rotated. A2-099, A2-044, X3-H32. Later.
- Weekend and single-class budget cap. A3-114, X2-H36, X3-H37. Shadow.
- Drawdown cuts agent autonomy back to his click. A5-078, X3-H70. Later. **OTHER SESSION** (agents).
- Re-entry cooling after a fill through the stop. A2-117. Never a hybrid.
- Order-rate limit and size sanity band as multiples of the unit's own usual. `ledger/v1/core.md` part 7. Core.

### Group E. Costs as observed facts

**I62. The cost triple, with its gate as a rule, not a law.** Costs enter at three points: the size denominator (stop + round trip + stressed slippage), a Kelly ceiling in R, and a gate (gross edge at least k × stressed cost). Shorter timeframes mean smaller stops, so the same cost is a larger share of R. REVIEW M4's table: at a 5-pip stop the bar refuses, at 8 it passes unstressed, at 10 it passes, "so k and the stop size decide whether his scalper exists". *From:* A1-142, A1-138, A2-223, A5-084, X2-H39, X2-H04, BTC cost filter 2606.00060 (author: −64 % to +65 % a year). *Touches:* sizer, unit logic. *Fate:* core; dollar sim. *Read:* denominator **SEAT**; gate **CONTENT**, and a preset's choice, since he said fees are "constant variables... I'm trying to observe them, see what I can do" (M51). *Evidence:* author backtest; no fills yet.

**I63. A missing cost starts on a stressed guess that decays.** Unmeasured cell: twice the posted spread, pooled across the class, labelled `cost:uncalibrated`, decaying to measured fills. Against: X0's "refuses sizing". *From:* FUNNEL DP11, X2-C25. *Fate:* core. *Read:* **SEAT** as the label and the fallback. *Evidence:* PROPOSAL.

**I64. News as an observed fact.** Window widths from measured impact per release and instrument, not provider colours; each unit declares what it blocks on; entries only; blocked hours reported as a cost; re-entry on spreads and depth, not on "exchange resumed". His own example. *From:* A2-100, A3-127, A3-130, A3-132, A3-229, X3-H31. *Fate:* first slice core. *Read:* **SEAT** for the unit's declared tier; widths **CONTENT**. **OTHER SESSION** owns MIS calendars. *Evidence:* E-mini event study (author).

**I65. The record must split by session and hour.** Records split per market only today, so every per-hour sizing input needs a new shape. *From:* X2 gaps, G7 §5.3. *Fate:* not a hybrid. *Read:* **SEAT.** Without it, windows, the cost map and class bands all break. *Evidence:* code fact as reported by G7.

**I66. Input-first drift.** Costs, fills, trade rate, hold time and replay match move before profit does. One out of band is yellow, two red. A paper twin's per-trade gap isolates real cost. *From:* Carver, A2-166, A2-174, A3-083, X3-H51. *Fate:* core. *Read:* **SEAT** for the twin's rows, bands **CONTENT**. *Evidence:* practitioner; paper has zero slippage today, so the twin gap is all real cost.

**I67. Graded cost shrink before the SQS block.** Live cost above the unit's band steps size down, above p90 further, above the hard block no entry. Depth and noise the spread misses. *From:* A1-014, A1-150, A3-069, X2-H42, A5-136. *Fate:* shadow. *Read:* **CONTENT**. *Evidence:* NQ study (602 sessions); thresholds do not transfer.

**I68. Other cost seeds.** All **CONTENT**.
- Carry and funding inside the hold decision. A1-148, X2-H41. Later. Real rules, MQL5 simulations.
- Minimum worthwhile risk: a per-lot minimum commission makes a too-small trade pointless. EOQ. X2-H39. It speaks to "can I trade with less than $1?".
- Combined-flow netting: units offsetting on one venue pay spread for nothing; repeat same-side flow gets skewed. A3-239, A1-118, X2-H43. Wild.
- Hour map instead of session flags: volatility columns carried 25.6 % of model importance against 2.5 % for session flags (`linking/unit-ideas/A1-sizing-allocation.md` item 13).
- Broker reality check before deploying on a symbol. A1-151.
- Cost cushion and retention score. A1-141, A2-224.
- Stop fills at the stressed spread in backtests. A5-080, X3-H47. Later. Secondary source; I think this belongs in QMB conventions.

### Group F. Exits and stops

**I69. Exit families per style, as starting templates.** One family per unit type: mean-reverting scalper (thesis cut, backstop, disaster stop, target at reversion, half-life time exit, no trailing); momentum scalper; opening-range; intraday trend; swing trend (reversal exit, wide catastrophe stop); pairs; carry. *From:* X3-H43 table, A2-268, Carver, Clare. *Touches:* QML templates, dictionary. *Fate:* core as defaults. *Read:* **CONTENT**, exactly his canvas. "Not allowed" cells should read "not advised": a user can paint anything. *Evidence:* most cells rest on one study or on theory.

**I70. Fast invalidation from the unit's own winners.** Read the cut from how far winners dip: if 90 % never pass −0.4R, a cut at −0.5R loses few. A time stop sits where the edge ratio peaks. It must beat "no cut" and "cut one bar later". Near opens and closes the cut widens, as exchange bands double there. *From:* A5-087, A2-239, A2-240, A5-086, X3-H39. *Fate:* core. *Read:* **CONTENT**; MAE/MFE on rows **SEAT**. Candidate 2 warns the right bars for a 1-minute cut arrive only after G-DEMO. *Evidence:* no paper tests it after costs; MNQ edge lives in the first bars (read in R8).

**I71. Thesis-first invalidation.** Each trade carries a named condition that would prove it wrong: ORB back inside the range, an imbalance flipped. Price cut is the backstop, a disaster stop beneath both. The row records which fired. *From:* A2-253, A2-254, A2-257, X3-H40, Steward. *Touches:* QML invalidation role; a bot-proposed close with a reason code. *Fate:* core. *Read:* **SEAT** for the reason code, rule **CONTENT**. *Evidence:* author backtest, paper account.

**I72. No stop, or a stop not used to size.** He said in Oct a stop on a scalper seems irrelevant with fast invalidation, and later "leave room". Today a unit with no price stop has undefined R and its results are flagged. Options: R from a tail-loss budget; dollars from a share; volatility units. Open question: is R the loss at the disaster stop (FUNNEL DP11) or at the working exit? A wide disaster stop shrinks lots unless the sizing reads the realised distribution. *From:* `unit-plan/RISK-SIZING-PACK.md` C7, placeholders row 11, X3 P17, X3-H44, X0-13. *Fate:* "R gross at the disaster stop" core; "our call, with his B9 reservation standing". *Read:* **SEAT**: R must be a declared basis on the row, never assumed. *Evidence:* PROPOSAL.

**I73. Stops only where they earn: the stopping premium.** Measure the unit's own persistence at its hold. Momentum: stops and trails fine. Mean reversion: wide stop plus thesis and time exits. Random walk: disaster stop only. Clare: no extra stop beat the plain trend exit. Trailing is suboptimal under positive drift (A2-231). *From:* Kaminski-Lo, Lo-Remorov (R8), A5-079, A5-081, A2-249, X3-H38. *Fate:* later; go-live. *Read:* **CONTENT**, and a strong Lab test; his "exits is where we need to be inventive". *Evidence:* REAL at daily scale (abstract and secondary); no intraday cost-heavy test.

**I74. The dynamic stop and target, rebuilt.** Breakeven off by default; trigger read from the unit's own paths, offset covers spread; target extended only on a calibrated continuation; scratches at cost. His April words: "trailing take profit and sort of like a reverse trailing stop loss". His M15: replaced by FI for scalpers, kept for intraday. Variants: risk-state invalidation instead of blanket breakeven (A2-266); half close then breakeven (A2-247); partial-close bugs (A2-237). *From:* A2-234, A2-235, A2-255, A2-256, X3-H41, X0-24. *Fate:* later; it needs step 3 and intraday units. *Read:* **CONTENT**; needs I7. *Evidence:* no peer-reviewed breakeven test; April spec never validated; Gen 3 ratchet built, off the path.

**I75. Inventive exit list.** All **CONTENT** on the stack; none needs a core change once I7 and I76 exist.
- Survival-analysis hold-or-close: target and stop as competing risks. A2-241, X3-H42. Raised win rate and lowered profit factor on all four instruments in the only test.
- Hold-or-exit classifier and model-confidence exit. A5-043, `wave-1/exits-and-halts/model-confidence-exit.json`, `stop-before-target-probability-exit.json`.
- Half-life time exit for reversion. A2-233, A2-232, Leung and Li (simulation).
- Edge-ratio time stop. A5-086. MNQ survivors held 60-75 minutes.
- Scale-out rungs from recent MFE percentiles. A2-238.
- Trail chosen by why the position opened; five methods. A2-244.
- Per-instrument asymmetric stops from a volatility signature. A2-243. Two months.
- Target and stop from a fitted reversion process on synthetic paths, with stop ceiling from account and concurrency. A2-242.
- Exit by trend or reversion state at several horizons. A2-265, Safari-Schmidhuber.
- Staged against immediate exit by the cost of waiting. A2-267.
- Basket loss cut that also deletes pendings, and a basket time stop. A2-068. Account-scope form is a pod (placeholders question).
- Triple barrier as one bundle. A2-248. Live open-source.
- Flat before the close with a buffer. A2-263. Forced flat is a core row.
- Two knobs: stop width from volatility and horizon, size from budget; tightening never buys size unless a ceiling approves. A5-083, X2-H09.
- Exit used as a trigger in another strategy: he called such ideas "very important" (T2:1000). `unit-plan/research/39-gold-mine-session.md:160` says the same primitive serves both roles.
- Avoid: suspending stops during news (A2-246). It leaves positions naked in the most gap-prone minutes. Kept as a labelled trap.

**I76. Every exit change is a counted trial on fixed entries.** Same entries, only the exit differs, across each instrument; tries are counted. Counterfactual replay over a unit's own trade paths is the cheap form. *From:* A2-139, A2-140, A2-225, X5-H29. *Touches:* QMB, Lab. *Fate:* core for the cut. *Read:* **SEAT** for keeping path data per trade (bar-level MFE/MAE); the test **OTHER SESSION** (methodology). *Evidence:* controlled test by an author.

### Group G. Levels, baseline, self-configuration around size

**I77. A level slot; no ladder in the baseline.** Size = base × level × taper. The level is one reader of the unit's edge stream. How a level starts and moves (holdout start, BOIN cohorts, whole contracts on lumpy classes, a ramp "until optimised Kelly over about a month", his word gradient) differs by unit origin: he said a unit from the Lab, QMB or a mini app are different and "no one is refusing them" (M49). *From:* X2-H13, H27, H49, A1-052, A1-055, A2-190, FUNNEL DP15. *Fate:* core, with holdout start. *Read:* **SEAT** for the slot and fractions of baseline; rules **CONTENT** or **OTHER SESSION** (methodology). The funnel's holdout start rule is the part he rejected. *Evidence:* BOIN proven elsewhere; never on a trading unit.

**I78. The edge as a gate or dial, chosen per preset.** Edge as a band; size reads a chosen point (zero, low, mid). "Twice the edge, twice the size" he refused. Kelly as a ceiling. He also said Kelly placement is brilliant. *From:* A1-030, A1-031, A1-032, X2-H03, H04, his A24. *Fate:* core. *Read:* **CONTENT**, with `edge_range` a record field (**SEAT**). Gating is the methodology session's: "how do agents actually know that something is valid?" (M49). *Evidence:* shrinkage simulations; DeMiguel second-hand here.

**I79. Asymmetric equity basis.** Committed cushion for size, marked equity for brakes, realised profit for accelerators, worst case at stops for the clip. *From:* A2-115, A4-059, A1-113, X2-H44. *Fate:* core. *Read:* **SEAT** as a declared basis per row. Facts: the balance is read once at sign-in; cTrader gives no equity field (placeholders row 17, X2-C08). *Evidence:* REAL prop practice.

**I80. Per-scope anchor clocks.** Each scope declares when its day starts: rolling for scalpers, per open for ORB, rollover for FX, a declared hour for crypto. Raises only at anchors; the floor never resets. *From:* A2-064, A5-124, X2-H12. *Fate:* core. *Read:* **SEAT.** His "weeks" and "bad week" fit here: a weekly anchor is one more clock. *Evidence:* demo tests; Topstep live.

**I81. Feasibility first, and the lot-shed rule.** For each unit, instrument and broker: can one minimum lot at this stop fit? If not, paper. When a cushion falls, shed the thinnest units so survivors clear a lot, so the book never goes dark. Sim: 100 % dark with skip, 0-4 % with shed at a $3 step. *From:* A1-157, A3-002, X2-H45, FUNNEL DP13, REVIEW M9. *Fate:* core. *Read:* **SEAT** for the feasibility verdict; shed rule **CONTENT** (shed against concentrate against borrow). *Evidence:* MODEL; product specs change.

**I82. The deployment carries share, costs and level.** Demo sizes from its share of live equity, never the demo balance, so paper results translate. Overrides DOCS's frozen balance. *From:* A1-130, A4-036, X2-H50. *Fate:* core. *Read:* **SEAT.** Reset rules on a world switch are **CONTENT**. *Evidence:* REAL build design; three-stage benchmark.

**I83. Three numbers per instrument.** Routine risk at the stop, stress loss, feasible minimum loss, on one money scale; class defaults on the override chain; pool volatility dynamics, keep costs local, never pool mechanics. One template sizes every class. *From:* ISDA SIMM, A3-001, A1-137, A1-161, A5-048, X2-H47. *Fate:* core. *Read:* **SEAT.** It is his "adjust across pips, points" (A17) and micro against mini (A1-165). *Evidence:* REAL at banks; class table missing.

**I84. Same bet counted once.** A bet key by a declared rule; open risk capped per key, per unit, per account; a heat cap derived from trade rate × hold (Little's law). The 1m and 5m on one pair are one bet. *From:* A1-113..115, A3-050, X2-H34, his T2:1000. *Fate:* core, heat cap later. *Read:* **SEAT.** The correlation ledger's home stays open (`unit-plan/RISK-SIZING-PACK.md` C5). *Evidence:* MQL5 ideas; textbook.

**I85. Smallest-wins, naming the binding cap.** Final size is the min of all caps; the receipt names the one that bound and counts how often. A cap binding over 90 % of trades is flagged. April's lesson: one cap always bound, so nine multipliers were inert, his "handbrake". *From:* A1-122, A4-014, A1-123, X2-H06. *Fate:* core. *Read:* **SEAT.** *Evidence:* REAL dash.js; April audit.

**I86. Meters of what safety costs.** Sitting-duck meter: time under baseline and R missed, split by which brake held it. Total choke budget across all cuts on a healthy unit. Review: the first funnel ran a healthy unit at about 0.26 of baseline with all picks. *From:* A5-073, A4-202, X3-H64, X3-H65, REVIEW M2, M3, his M33. *Fate:* meter shadow; choke core, blocking in CI at 0.75. *Read:* meter **SEAT** via would-have rows. A number blocking shipping is rigid; as a harness report per preset it survives. *Evidence:* MODEL; counterfactual ignores paths a brake saved.

### Group H. Drift and alpha decay

**I87. Three speeds, with cause.** Money facts now. A warning cuts a level, reversibly, and opens a review. Confirmation sends to paper. Each records a cause: statistics, change, input, money. He asked "What do you mean by unit stepping down?" (M49), so this needs saying plainly. *From:* A2-133, A2-160, A2-175, A5-028, A5-150, X3-H49, X5-H15. *Touches:* decay template, mini app. *Fate:* core. *Read:* **SEAT** for states and cause codes; rule **CONTENT**. *Evidence:* MODEL: 902R of 950R after a bad week against 614R; about the same after real decay.

**I88. Trade CUSUM on R.** A running score against the expected edge. Dead edge caught in 92-99.5 % of runs at 4-40 trades a day, 68.5 % at 2 a day; a healthy unit steps down about every 668 trades. Candidate 3's check: two warnings in 500 trades send 42 % of healthy one-unit paths to paper inside 120 days. So it must be a derivation on a row. He asked for a plain explanation of it (`unit-plan/RISK-SIZING-PACK.md` 2.5). *From:* A2-149, X3-H11, `architecture/PICK.md` graft 13, `candidate-3/out-c3.txt`. *Fate:* core. *Read:* **CONTENT**, default. *Evidence:* MODEL.

**I89. A family fading everywhere.** Pool the results of all units sharing a logic. Harder sim: at N = 5 and 10 "ten small units lose together before any one of them alarms" (18-43 % lose half the cushion). A pooled CUSUM sees it in days. Discount correlated units. *From:* A3-164, A2-188, A2-189, X3-H23, X5-H23, FUNNEL section 9. *Touches:* family tag, workflow. *Fate:* shadow, needing a cluster level. *Read:* **SEAT** for family and driver tags. At 200 units this is the main sensor, and the go-live lens hid that. *Evidence:* MODEL.

**I90. A false-demotion budget across many units.** With 200 units watched, naive thresholds make some false demotion near certain. Split a total budget; 20 units at q = 0.05 need an e-value of 400 to demote. Reversible warnings use a labelled bounded form. *From:* A2-152, A2-158, A2-159, A4-161, X3-H52, X5-H16. *Fate:* later. His 200 units were not the lens. *Read:* **CONTENT**, agent workflow input. *Evidence:* simulation with proofs; low power.

**I91. Bad luck, bad market, bad execution, or decay.** A one-line bad-day sentence each morning ("a one-in-24 day for a healthy unit of this type"), then four bins. Only the last feeds demotion. Fires tagged by session, class, news and SQS split "bad market" from "bad unit". This is exactly what an agent can carry for him. *From:* A2-125, A2-174, A2-177, A3-123, X3-H10, H50. *Fate:* sentence core; classifier shadow. *Read:* **SEAT** for fire tags; classifier **CONTENT**, an agentic mini app. *Evidence:* PROPOSAL; bins overlap.

**I92. Random-entry twin: was the edge ever real?** A twin with random entries and the unit's own exits tells "the entry has an edge" from "the exits are kind". His M49: "the unit whose edge was never real. I think this is where the agents come in... if we give them something to use". *From:* A2-178, A1-173, A1-174, X0-50. *Fate:* offline core, live twin later. *Read:* **SEAT** for running twins on the same signals; agents read it. Methodology owns judging. *Evidence:* MQL5 controlled design; PROPOSAL.

**I93. Drawdown as a decay detector, not a skill measure.** Man Group: for constant skill a total-return rule is better; drawdown rules win only when good managers turn bad. Lines must widen with time, since touching any line gets likelier. Worry lines: depth for scalpers, duration for trend. *From:* Van Hemert et al. (read, R9 §4.1), A2-014, A5-146, X3-H56. *Fate:* later. *Read:* **CONTENT**; the reason his old breaker worked. *Evidence:* REAL.

**I94. Drift seeds.** All **CONTENT** or methodology.
- Expectation per regime: a known weak regime does not read as decay. A5-072, X3-H54.
- Planned looks with three zones: yellow holds, red cuts. A2-184, A2-196, X3-H48.
- Upside alarm: too good is often leverage nobody meant. A2-176, X3-H55.
- Re-promotion on evidence plus his click; each paid. A2-221, X3-H53.
- E-process against a minimum viable edge. A2-155. About 1,200 observations for a 0.1-sigma drop.
- Nightly decay check shipping today: 20 trades. A2-168. Replace; count flaw.
- Wasserstein input drift, rolling Sharpe with bands. A2-170, A2-171.
- Change-point and regime-age readings. `linking/unit-ideas/A2-brakes-drift-exits.md` items 7-9. **OTHER SESSION** (MIS).
- Agent drift explainer, journal coroner, sitting-duck advocate, decay watch where a script decides. X7-H22, H27, H31, H32. **OTHER SESSION** (agents).
- Rehab with the parent's record as prior; "failed before COVID" blacksmith. A2-229, X5-H27. **OTHER SESSION** (methodology).

### Group I. Agents near money

**I95. Agents read, propose and carry the watching.** Cut-only evidence as a fact a unit's rule reads, with expiry; raises go to a card. Deterministic fast loop; agents enter after a trigger. *From:* A1-132, A2-018, A2-019, X2-H58, X3-H34, H60, X7-H03. *Fate:* door core, jobs later. *Read:* **SEAT** for typed read and propose tools over every record above; jobs **OTHER SESSION**. X3-H60's "no agent is a detector" is too narrow against "why would I have to be there monitoring units?": agents can detect, they just cannot act on money. *Evidence:* Steward paper run (102 days); fabricated news moved LLM agents 62 % of the time, so provenance matters.

**I96. A proposer that always wants more gets the slowest line.** Credit data: the party that most wants more limit is the one for whom it is least profitable. *From:* Agarwal et al. (snippet, R9 §3.1), X2-H58. *Read:* **CONTENT**, agents session. *Evidence:* snippet.

### Group J. The ledger of variables

**I97. A ledger of 835 variables with typed couplings.** 207 core, 72 shadow, 553 later, 3 fork; 1,743 couplings typed as a cap down, a state down, an event up or same-level. Every row has a level, measure, derivation, `seen_values` of every old value, sources. Numbers carry no weight until derived. As a map it is valuable: it lets the copilot and agents see which number touches which, and a check runs against it (X1-H65). *From:* `ledger/v1/variables.yaml`, `couplings.md`, `core.md`, `NOTES.md`, `ledger/README.md`. *Touches:* dictionary, UI, copilot. *Fate:* its tiers are the funnel's, so read them as that lens: `house_money_multiplier` core yet `reverse_house_money_steps` shadow; `breakeven_trigger`, `trailing_stop_setting`, `partial_close_fraction`, `target_r` all later. *Read:* **SEAT** for machine-readable ledger access. Re-tier before relying on it. Also fix NOTES items 6 (canary percents on a market list) and 3 (one row, two readings). *Evidence:* a catalogue of real sources. REVIEW M1 warns earlier generations together held 267 and "too much machine".

**I98. Dead and parked values keep their history.** `dead.yaml`, `seen_values`: 3-5-7, 10/5/3, 8 %, 1.5x, 2.5x sit as history with no weight. A user can resurrect one as a preset with a reason. *From:* `ledger/v1/dead.yaml`, NOTES items 8, 14. *Read:* **CONTENT.** Mind that all six decay rows run in the shipped stack today (item 8).

---

## 3. Designs and overhauls already proposed for this area

Includes options never shown to him. Where two conflict, both stay.

**Overhauls of sizing (`expansion/X2-sizing-accelerators.md` section 4).**
1. Replace the Book ladder's price of R with the horizon multiplier. Buys: a derived number that scales with correlation. Costs: per-unit dollars fall as units rise, his main complaint.
2. Replace April's nine-multiplier chain with one baseline, one cushion pair, one cost triple, one context slot and a smallest-wins stack.
3. Widen the sizer contract. `architecture/PICK.md` graft 2 narrows it again to a thin surface over derivations.
4. One declared scope for house money; retire the count form of reverse house money into events. His RHM was the count form, so tell him.
5. Delete session multipliers (conflict: his "sniping gets more if proven").
6. Budget share replaces frozen paper balances.
7. Poker pots and risk classes replace the fixed style split, with the allocator a pluggable block in the Lab.
8. Gain-lock ratchet replaces the 2.5x cycle cap.

**Overhauls of brakes and exits (`expansion/X3-brakes-exits-drift.md` section 5).** Own-percentile money replaces the count; five states replace the binary stop; two-key slow lane replaces the nightly check; burn-rate replaces the door; cluster by shared driver, not style label; isolation moves to the BMS with fail-closed scope keys; exit stack replaces "first exit, fed nothing"; registry row as compile requirement.

**Conflicting designs, both kept.**

| Question | Option A buys | Option B buys | Sources |
|---|---|---|---|
| Baseline formula | Horizon floor-odds: no edge input, trades from day one | Own full size under a parent: each unit keeps real size, closest to his "two bots use all the 300" | X2-H01 against X2-H29 |
| Sizing on edge | Zero-edge default, safe against a wrong edge | Risk-constrained Kelly: spends the whole allowance | X2-H03 against X2-H05, X2-C01 |
| Where house money lives | Unit: earns its own | Book or portfolio with event window: one event funds once; one ledger with its brake | X2 PS7, FUNNEL DP14, REVIEW M8 |
| Anchor | Fixed: pair | Trailing: pure brake | X2-C03 |
| Brake home | One guard above the unit: one rank table, cross-unit easy | Inside the compiled unit: unit stands alone between hosts | F-B, `architecture/candidate-3/RATIONALE.md` (fact kernel, rank as property test) |
| Number motion | Applier with modes: acts between anchors | Refresh at anchors: simple, facts move live | F-A; `candidate-2/out-fork.txt` shows little gap |
| Status store | Status file, rebuilt from journals | Status held only in journal rows | PICK rejection |
| Exit rank | Safest wins in guard | Compiler's fixed order in the unit (close beats partial beats amend) | FUNNEL 5.3, candidate 3 |
| Target at broker | Node closes | Rests at the venue | PICK "to settle" |
| Second drift warning | To paper | One more level down, third to paper | FUNNEL DP27 against PICK graft 13 |
| AIMD | Pair with raises above 1.0: favourable | Pure brake: chokes | R9 §3.5 against X3-H07 |
| Fast brake default | Money percentile: near free, no timing | Streak or graded: timing in bad spells, costly | X3 collision 21 |
| BMS fire | Stand-down, card | Raises kill level itself, only he lowers | X3 P15. He calls it a pod question |
| Restore authority | By rule within a retry budget | Every stop waits his click | FUNNEL DP20, placeholders row 24 |
| Missing cost | Refuse | Stressed default | X2-C25 |
| Guard down | Fail closed | Fall back to position rules | `x1_guard_unavailable_action` |
| Account and pod | One thing | Two | `unit-plan/RISK-SIZING-PACK.md` 2.7 |
| Sits where | On the unit | Pod or central | `unit-plan/RISK-SIZING-PACK.md` C1 |

**Never shown to him as such.** R9's eight pairs (`research/R9-accelerators-and-brake-pairs.md` "Brake-accelerator pairings"): day ledger, tier ladder, AIMD with memory, three zones, burn-rate, block persistence, volatility, start-up. They are ready pod ingredients. The nine-attribute row and audio-compressor vocabulary. The new kinds: probe, memory ceiling, overdose step, sentinel, certificate, choke. The X2 and X3 roundtables (`linking/stage-b/`). The 15 binding factors at FUNNEL 5.2.

---

## 4. What the unit baseline must carry because of this area

| Item | Kind | What breaks if it is missing |
|---|---|---|
| Sizing base as a derivation producing dollars at risk; a separate dollars-to-lots step | socket | Every new sizing idea is a code change; lots leak into thinking and pips misprice across classes (I2) |
| Full read surface for derivations: share, cushion, open risk per key, own record, cost cell, gap factor, level, state, conviction binding | input | Almost no hybrid can run; compiler refuses moving sizer numbers (I13, I41, X2-C10) |
| Split rule as a row at pod level | socket | "More units, less each" becomes law (I3) |
| One cushion ledger with anchor type, clock, scope, realised and marked series | record | No house money or reverse pair; brake and accelerator can contradict (I4, I79, I80) |
| Registry row per control with scope, action, attack and release, counting rule, fail mode, class, shadow switch | socket | Each brake is custom code; "5 % drawdown" means four things; a pod cannot choose an action (I5, I11) |
| Halt slot verbs beyond `none`, `no_new_entries`, `flatten`: reduce with a factor; five states with RESTORE | hook | Only stops exist: every bad day is a stop, or the book goes dark while he sleeps (I58, X3 collision 6) |
| Stand-down scope keys: class, region, currency, underlying, session, family | input | "Isolate crypto" cannot be expressed (I55) |
| Exit stack running every per-bar exit, with position facts and all three verbs | socket | Trailing, breakeven, scale-out, FI and thesis exits locked out; the tip runs only the first (I7) |
| Reason code from a unit's own close; execution form of each exit carried by the socket | hook | Thesis exits cannot be judged (I71; `unit-plan/RISK-SIZING-PACK.md` section 4 item 8) |
| R as a declared basis; a unit with no price stop allowed and judged | input | His scalper without a stop has no R, brakes and records fail (I72) |
| Trade row: mechanism, outcome, costs in R, MFE and MAE, bar path, session, tags, numbers in force, placeholders used | record | No money ledger, no fair brake, no resize replay, no two-arm test, no numbers talk (I1, I6, I76) |
| Would-have rows while benched or in shadow | record | No trip tax, no certificate, shadow is blind (I60, I86) |
| Record split by instrument, session, hour, world | record | Windows, cost map, bands, per-hour sizing all fail (I65) |
| Cost facts per instrument × broker × hour × world, written from fills, with an uncalibrated label and fallback | input | Costs never reach the unit; his "observe then act" has nothing to read; no commission key today (I8, I63) |
| Sizer receipt: resolved value, reason, binding cap and counts | record | Handbrake returns unseen (I85) |
| Number spec: derivation, authority, cautious direction, guard, freeze, `applies_to_open_positions` | input | Self-configuration has nowhere to live; a moved number might touch open trades (I12; placeholders row 8) |
| Level slot as a fraction of baseline; no ladder law | input | Forces one validation story on four kinds of unit, which he refused (I77) |
| Instrument record with routine, stress and feasible numbers; class fallback | record | One template cannot size every class; min-lot surprise (I81, I83) |
| Bet key and driver and family tags on intents | input | Three positions on one dollar are three bets; pooled decay impossible (I52, I84, I89) |
| Worst-step term and margin facts at the order boundary | hook | The one move that ruins passes every brake (I21, I30) |
| Several positions per unit | input | Pyramiding and baskets blocked; compiler's `position_limit` today (I32; his A8) |
| Budget share on the deployment; same code in every world | input | Paper results do not translate (I82) |
| Cross-unit hook able to shrink, and pod able to swap a unit's rows at an anchor without a new identity | hook | Pods stay paper; a stage change makes a new unit and wipes the record (I27; placeholders row 31) |
| Paper twin and random-entry twin slot | hook | No early read on "edge never real", no live cost gap (I66, I92) |
| Read and propose tools over all of the above, machine-readable ledger | hook | 200 units cannot be watched by agents (I95, I97) |
| Invariants: exits never blocked, stops tighten only unless a row says otherwise, floor never reset by restart | invariant | His hard lines (X3-H46, placeholders row 9) |

---

## 5. Gaps: what he asked for that nothing on disk answers

1. **The large-risk question itself.** "how do we make sure we can achieve this, but without getting ruined?" and "you are meant to put accelerators and brakes" (M51). Every sim holds survival fixed, scales size to it, and reports growth. None starts from a large per-trade risk and asks which brake stack keeps the ruin chance acceptable, with one or two units. Group B is a list of parts. No run compares them.
2. **A bad week.** "without having a bad week wiping out everything" (M51). No brake reads a week as its window; core has day and trade windows. Anchors could carry it (I80).
3. **Cents.** "do you think even if me, I'm a trader, do you think I can trade with less than $1?" (M49). Only a commission-based minimum worthwhile risk touches this (I68). Nothing gives a sensible minimum per trade.
4. **Why lots.** "Why lots? Because remember, you're not trading one instrument." (M49). The design answers it (I2) but no page ever told him.
5. **Unit stepping down, starting level, house money approval.** "What exactly is a starting level, by the way?" and "What do you mean by a rule I approve?" (M49). Definitions exist; plain explanations do not.
6. **Combining the two systems.** "we are going to combine the old systems version and then the book version to create a standard one" (T2:1000). "It was a bit radioactive" (D27). X2 restructures 1-2 replace pieces. No document lays the relentless parts and the Book parts side by side, and no relentless preset was ever built or simulated.
7. **Pods.** "I remember asking you to see if you could figure out some pod ideas or configurations" (M49). Pods appear as a slot map (X2-H59) and later rows. No catalogue of pod configurations exists. R9's pairs plus Groups C and D are the raw material.
8. **Agents on 200 units.** "Why not just have an agentic workflow that can cater for that? As a mini app also." (M49). X7 names jobs; X7-H36 is one row marked later. No design of the watching workflow, and nothing states what agents would read to spot a false edge early (I92 is the nearest).
9. **Where a unit goes as sizing.** "position sizing in terms of the unit. Where do we allocate the unit in which instrument?" (M51). A1-133, X0-46 and feasibility touch it; flagged to the MIS and left.
10. **Inventive exits.** "Now exits is where we need to be inventive." (Q13:1489). Group F mostly catalogues. The only new forms are thesis-first and the hazard exit; no paper tests fractional cuts or breakeven after costs (R8 gaps 1 and 2).
11. **Human traders.** "try to mimic a human trader into a bot" (M50). Nothing maps how a human sizes by conviction, presses a good day or stops after a bad one into blocks, beyond I41 and the behavioural papers in R9 §1.1. Fabio Valentini's method is unread here.
12. **Micro against mini.** "futures trading at a mini and at a micro are two different things... inefficiencies that can be exploited" (M50). A1-165 treats them as one underlying with one R, which is the opposite lens.
13. **Scalper cost realism.** "according to research, apparently scalpers... have a hindrance of after fees" (M50). No slippage has been measured anywhere (X2 section 5); REVIEW M4 shows the scalper's existence turns on it.
14. **Other holes named by the agents.** Intraday persistence after costs (R9); perps with funding, liquidation and stop in one size; multi-leg sizing; margin rising in stress; stock borrow and roll in the sizer; multi-unit brake arithmetic; fat tails in brake sims (X3 section 6; X2 section 5).
