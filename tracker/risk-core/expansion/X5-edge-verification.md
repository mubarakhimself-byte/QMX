# X5: real edge verification and promotion

Stage B expansion layer, revised 2026-11-03 from the stopped draft of the same day. Nothing here is ratified. The Fable judge funnels and ranks (`linking/RANKING.md`); this file widens.

## How to read this

- The stopped draft's ideas `X5-01` to `X5-56` stay as **seeds**, listed in section 3 by number with one line each. The Stage A catalogue dissected them into components (`A2-brakes-drift-exits-181` to `-229`, `A4-template-agents-telemetry-136`, `-148`, `-149`, `-159`, `-165`, `-181`, `A1-sizing-allocation-031`, `-052`, `-053`), so a seed is cited either way.
- **Hybrids** are numbered `X5-H01` and on. Each links components by id, names the need it serves, and carries a maturity tag. Component ids are shortened: `A2-186` means `A2-brakes-drift-exits-186`, `A4-121` means `A4-template-agents-telemetry-121`, `A1-031` means `A1-sizing-allocation-031`, `A3-164` means `A3-structure-regimes-scenarios-164`, `A5-034` means `A5-topup-034`.
- Every variable is in `ledger/additions/X5-edge-verification.yaml`. New ids carry the prefix `ev_`; existing v0 ids are reused as they are (`drift_state`, `size_levels`, `verification_trades_needed`, `sequential_evidence_pass`, `effective_tries`, `edge_range` and others).
- **[judgment]** marks my opinion. **[arithmetic]** marks a number I computed (`x5_numbers.py` and `x5b_numbers.py`, standard library, independent ±1R trades; results in section 9). Numbers from research files are cited as R3, R6 and so on.
- Short paths: `RC` = `D:\QMX-worktrees\risk-plan\tracker\risk-core\`; `R3` = `RC\research\R3-edge-verification-and-analogues.md`; `R6-T08`, `R6-T09` = `RC\research\R6-alphaxiv-papers\T-08...`, `T-09...`; `R4` = `RC\research\R4-alphaxiv\R4-alphaxiv-synthesis.md`; `R9` = `RC\research\R9-accelerators-and-brake-pairs.md`; `G8`, `G9`, `G11` = `RC\grounding\`; `SEEDS` = `RC\seeds\SEEDS.md`.
- His rulings that bound this layer: QMB proves or enhances the edge before demo and luck is not an argument (SEEDS D18); picking which units to promote is not this session's (D19); only he promotes to live (C-23 in G9 §3.2); paper is demo trading and "half the edge" made no sense to him (D14); 7 days of paper is doable, 14 is too long, and days still matter (D22); size down slowly, never pull out on one bad day (A25); the edge is a range and sizing must not lean on it (A24); agents must solve issues, not list them (E28); agents get tools and propose, the sky's the limit (D42).
- Brake, accelerator, restore and clamp are used as `R9` §0.2 defines them. Under those definitions this layer's **step down and demotion are brakes of the kinds "demotion" and "step ladder"**, its **step up is an accelerator of the kind "evidence step-up"**, and the two together are a **coupled pair** with a dead band (the yellow zone). I use those words below.

---

## 0. The two-minute explanation (for him)

**What verifying an edge means.** Any one trade is mostly the market moving around. The edge is a small lean on top of that movement. Verification is the job of telling the lean from the movement. The only way to do that is to count trades: enough trades that the lean stands out above the wobble of the average. Nothing else works: not a good week, not a strong feeling, not a backtest.

**How many trades.** The wobble of an average shrinks slowly, by one over the square root of the trade count. After 100 trades the average can still be off by about 0.10R. A unit that wins 55% of 1:1 trades has a lean of exactly +0.10R per trade. So after 100 trades the lean and the wobble are the same size, and you cannot tell them apart. After about 600 trades the lean is about 2.4 times the wobble, which is where professionals say "this is probably real" [arithmetic]. That is the 610 in the earlier table.

**What "half the edge" (52.5%) means.** The 55% came from a backtest. Backtests overstate, for three recorded reasons: the search picked the best-looking variant, costs were modelled, and markets move on. Published strategies lose about a quarter to a half of their edge once they leave the backtest (R3 §1.1; R6-T09). So the honest planning case is not "it will be 55%" but "it may be 52.5%". That is a discount on the **backtest**, not a prediction about demo. Demo trades count fully as real evidence. And a half-size lean needs four times the trades to prove, about 2,470 instead of 610, because the wobble shrinks with the square root and the lean has halved. His objection in D14 was right about demo and wrong about what the halving refers to. In this revision "half" is only the fallback: the unit's own deflated number replaces it whenever it can be computed (X5-38, X5-H04), and the card shows which was used.

**What "ten times faster" means.** Proof is counted in trades, but you wait in days. One unit at 4 trades a day reaches 610 trades in about 153 days. Ten units of the same logic at 4 trades a day each reach 610 trades together in about 15 days. Nothing about the maths changed; the trades arrived ten times faster. Two catches. First, the ten units must be testing the **same claim** (the same logic on markets where it is supposed to work); pooling proves the logic, and each unit's own placement still needs its own trades. Second, they must not win and lose together. If their days move together 30% of the time, ten units count as about 2.7 and the wait is about 57 days, not 15 [arithmetic]. The plan shows both numbers side by side so the speed-up is never overstated (X5-H06).

**What a bad day looks like.** A perfectly healthy 55% unit at 4 trades a day has a day of −2R or worse one day in four, and a day of −4R (every trade lost) one day in 24 [arithmetic]. So a bad day is not evidence of anything. A broken edge shows up only as a run of trades, hundreds long, whose average sits below what the unit promised. The workflow therefore has three speeds. Inputs (costs, fills, trade rate) are checked in days, because a doubled cost is visible after fifty trades. Warnings (a CUSUM or an evidence detector) come in weeks and only step size down one notch. Confirmation that the edge is below its minimum worthwhile line takes hundreds of trades and is the only thing that moves a unit back to paper. The fast money brakes (a day's loss limit, the kill switch) are another layer's job and never wait for statistics.

**What the workflow does.** Before a unit trades, it gets a plan: the edge it claims as a range, how many trades proof needs at the low end, how many units of the same logic are helping, and roughly when those trades will arrive. Then it trades, in paper and then at the smallest live size, and the plan is checked at planned trade counts, not every morning; an evidence meter that is safe to look at daily sits on the screen. Each check puts the unit in one of three zones: green (carry on, may step up one size level when the evidence bar for that level is met), yellow (hold, gather trades, an agent explains why), red (step down, or back to paper when the edge is confirmed below its line). Every move is a formula on recorded trades, and every rule has been tested against a random rule that fires as often. Agents propose units, write the plain-words explanations, and spot cost and fill problems. The one thing no formula and no agent does is move a unit to live money. That stays his click, and the click approves one exact thing: this version, on these markets, at this level, until this date.

---

## 1. The whole path, as stages

Each stage names the question it answers, the evidence it needs, who acts, what today's stack has (G8 §4-5, G9 §3 and §7, G11 §4), and which hybrids serve it.

| # | Stage | Question | Evidence it needs | Who acts | Today | Hybrids |
|---|---|---|---|---|---|---|
| S0 | Idea and claim | Is there a reason this should work, and has it been tried before? | A registered claim card: logic, context, market classes, claimed edge band, source, falsification tests, novelty check against the family ledger | Agent writes it; a script refuses a unit without one | B19 has a claim card (G8 §4.2); no novelty check, no search ledger | H01, H02 |
| S1 | Build and prove (QMB B12-B14, judge B13) | Does it show an edge after costs on unseen data, with best-of-many luck removed and look-ahead blocked? | Five gates on excess returns, cost-stress grid, deflated Sharpe over the family's tries, PBO, replay match, validity stamp, worst-regime block | Scripts run; the judge writes a verdict and a frozen card; the challenger attacks it | Built: verdict, card, effective tries (G8 §5.2). Missing: calibrated costs, commission in R, PBO, excess-return basis | H03, H04, H05, H07 |
| S2 | Verification plan | How many trades will proof need, how many units help, and can this unit make them in time? | The card's band, trade rate, the family's measured or prior correlation, the allowed incubation | Script computes; refuses "too thin to prove" | Not built | H06 |
| S3 | Event replay and dry chassis | Does one real bad day break it, and does it beat a random-entry twin on the same battery? | 5-10 recorded event days; the random-entry unit's result | Script | Not built | H08 |
| S4 | Paper (C-12c) | Does the machine work, and do the first trades match the card? | Fills, trade rate, holding time, replay match, cost per trade against a paper twin started at the same minute | Script scores; agent explains | Paper lane and judge built (30 trades, 28 days); paper has zero slippage (G9 §3.1) | H09, H21 |
| S5 | His click (C-23) | Does he want this live, at this level, on these markets? | A promotion packet bound to the hash, the plan, the zone, the inputs check, the book's marginal effect | Him only | Built (G9 §3.2), without binding or expiry | H10, H11, H12 |
| S6 | Live at level 1 | Do live fills and costs match the card? Do the trades keep adding to proof? | Live cost and slippage per trade; the evidence meter; the twin gap | Script; agent explains | Not built: no live binding (G9 missing 17) | H13, H38 |
| S7 | Planned looks and anytime evidence | Is the edge proved at this level, unproved, or out of reach? | Trades since the last look; the look schedule; the funded e-process; the level's threshold | Script computes the zone | Not built; the nightly decay check compares the last 20 trades (G9 §7.2) | H13, H15, H16, H17 |
| S8 | Step up | Has this level been safe for enough cohorts, and is the evidence bar for the next level met? | Bad-cohort rate; e-value above the level's threshold; the family's error budget not spent | Script proposes; the ladder moves by rule inside the template, or by his click (Q3) | Not built | H14, H24, H25 |
| S9 | Monitoring | Is the live footprint still the card's footprint, in this regime? | Inputs strip, CUSUM, cone against the regime's expectation, worry lines, brake-fire density, twin gap, upside and consistency checks | Script; agent reads journals | Partly: `dc-decay-and-limit-report` (G9 §7.2) | H15, H18, H19, H21, H22, H23 |
| S10 | Step down | Has a warning fired, or the bad-cohort rate crossed the high bar? | Same cohorts; the e-detector's warning level; the inputs strip | Script | Not built; nothing sizes down (G11 §4.3) | H14, H24 |
| S11 | Demotion | Is the edge confirmed below its minimum worthwhile line, or is the goal out of reach? | The funded e-process against the minimum viable edge; futility at a look; a demotion cause code | Script moves to paper; journal keeps running; orders cancelled by the tested path | Pipe exists (risk stop), nothing feeds it (G9 §1.1) | H26 |
| S12 | Rehab | Can a child variant bring it back? | A new counted try; the parent's live record as the family prior | Agent proposes children; QMB tests; the same path from S1 | Old WF3 D6; not built | H27 |
| S13 | Re-promotion | Has the demoted unit earned its way back, in a funded episode? | An e-value on post-demotion trades above the episode's threshold plus a minimum time | Script says ready; he clicks | Old rule: 10 profitable demo trades (dropped; A2-213) | H26 |
| S14 | Retirement | Have all children failed, or is the family's budget spent with no refund in sight? | Rehab count; the family's alpha wealth; every cell closed-thin | Script; he confirms | Old WF3 retire branch | H27 |
| S15 | The test of the tests | Do the gates themselves work? | Each gate's precision and lift; the pipeline's null and injected-edge runs with its delay | Monthly script; defects reported | Not built | H20, H42 |

**What stays outside this layer:** the brakes that act within a day (unit streak, Book daily, BMS daily, kill switch, SQS, isolation). They are the fast lane and belong to X3. This layer only reads their fire counts (X5-21, H19) and hands them a zone (H41).

---

## 2. Method passes on this revision

Run headless, playing every role. The memlog is `linking/stage-b/X5-edge-verification/.memlog.md` (108 entries) and the intent summary is beside it.

**Brainstorming, Morphological Analysis.** Ten parameters of a verification design (claim source, try count, unseen data, evidence rule, look timing, zone rule, size step, demotion trigger, who acts, screen word), each with the options the catalogue holds. The one empty cell in "who acts" is "agent acts", which stays empty by his ruling. The combinations that survived became H01, H04, H06, H13, H15, H16 and H19.

**Concept Blending.** Trial phases with Kubernetes rollouts (H46); Basel's traffic light with an audio compressor's attack and release (H24); Numerai staking with alpha investing (H34); the bank model inventory with the passport (H39); Kayenta's fresh baseline with the paper twin (H09); AutoQuant's one cost ledger with live-cost re-cutting (H38); Promote's funded wealth with his click (H12); Steward's protected core with the verification state (H32).

**Forced Relationships.** Contract-level replay onto verification (H28); competing-risks censoring onto the observation unit (H05); same-bar ambiguity onto replay match (H09); point-in-time availability onto the challenge note (H07); FIDES agreement onto the claim card (H01); the dry chassis onto every gate (H08); conservative UCB onto version replacement (H45); the no-edge synthetic market onto the family's false-discovery rate (H08); the kill-switch lifecycle test onto demotion (H26); loopjacking onto the click (H10); decision-process audit onto level-1 trades (H33); rank martingales on inputs beside the P&L test (H15).

**Cross-Pollination.** Grid zones of protection (H16), the insurers' event window (H06, H23), hospital alarm precision (H20), SRE burn rates (H25), TCP's memory ceiling (H14), EWOC's overdose-controlled step (H14), Argo analysis templates (H46), the VPA learner and applier (H41), Numerai's live-only payouts (H13), OtterTune's deny-list (H42), Simplex's verified fallback (H15), aviation's envelope (section 1, "outside this layer").

**Trait Transfer.** Hash-frozen (H10), next-session start (H14), paid restarts (H17), a variance cap in advance (H17), excess returns per class (H03), per-criterion rejection rates (H03), patience logging (H16), demotion cause codes (H26), marginal effect on the book (H11), a ring-fenced exploration budget (H48), pooling policy per parameter type (H23), streak-bias correction (H26).

**Evolutionary Pressure.** Selection rule: survives at half the believed edge, needs no agent judgment in the money path, adds at most three ledger variables. Ten variants bred; "all planned looks" died (undecided in 46% of half-edge plans at 1,000 trades), "agent staking" died the rule but is kept wild, and the strongest line was bred from "bounded bets for promotion, e-meter for display, looks for level steps" × "inputs first, P&L last" × "risk-tiered thresholds by level" (H13, H15).

**Solution Matrix.** Fourteen problem rows against the components. Every row is covered by at least two components; the empty cells are QMX gaps, listed in section 7.

**CIS problem solving** on each open problem is in section 4 (at least two options each, with trade-offs). The five-whys, is/is-not and force-field passes from the draft still hold; the root cause stands: no stage in the path states, in trades, what evidence would change its mind.

**Party mode roundtable** on the strongest hybrids is in section 8, with a pod-shop risk manager, a retail scalper, a platform engineer, a trial statistician and his own voice from SEEDS.

---
## 3. Seeds and hybrids

### 3.0 The seeds, from the stopped draft (one line each)

Kept as written; the catalogue holds their detail. Maturity as in the draft unless a hybrid below changes it.

- X5-01 verification plan per unit, priced in trades (A2-186). X5-02 "too thin to prove" is a verdict (A2-186). X5-03 the claim is a band with a stated low end (A2-187, `edge_range`). X5-04 planned looks with an error budget (A2-184). X5-05 an evidence meter safe to read any day (X5 draft §3; `sequential_evidence_pass`). X5-06 three zones (A2-196, A4-159). X5-07 count every try by its result stream (A2-202, A4-110). X5-08 one evidence ledger per unit, trades tagged by stage (A2-219). X5-09 two clocks (A2-217). X5-10 proof continues at the smallest live size (A2-218, A1-053).
- X5-11 pooled proof of a shared claim (A2-188). X5-12 breadth-and-time calculator (A2-181). X5-13 inputs first (A2-166). X5-14 live costs replace modelled costs in the verdict (A1-146). X5-15 the baseline is frozen; an edit restarts the paper record (A2-219, A4-041). X5-16 dose-escalation size levels (A2-190, A1-052). X5-17 a minimum number of events before any slow-lane signal (A2-031). X5-18 futility at planned looks is the demotion rule (A2-184). X5-19 CUSUM on R against the holdout baseline with the first-hundreds rule (A2-149). X5-20 the cone check (A2-212).
- X5-21 brake-fire density against an expected rate (A2-086, A2-088). X5-22 the test of the tests (A2-143). X5-23 upside alarm (A2-176). X5-24 rehab is a counted try (A2-229). X5-25 re-promotion needs evidence, not a streak (A2-221). X5-26 an error budget per family (A2-220). X5-27 retirement rules (A2-229). X5-28 an independent challenger (A2-197, A4-136). X5-29 agents explain the state in plain words (A4-135). X5-30 the edge is the gate, the risk share is the amount (A1-031).
- X5-31 a soft evidence multiplier, off by default (A1-019). X5-32 journal fields the workflow needs (G9 §7.1). X5-33 the verification state on screen (A4-165). X5-34 a verification passport (A2-198). X5-35 a nightly deterministic job with an agent pass (A4-148). X5-36 thresholds calibrated by simulation on the unit's own record (A2-227). X5-37 correlation discount for pooled proof (A2-188). X5-38 "half the edge" becomes the deflated holdout number (A2-187). X5-39 a paper twin (A2-178, A4-035). X5-40 verification per cell with partial pooling (A2-189).
- X5-41 a demotion ladder, never a jump (A2-167). X5-42 evidence keeps flowing while stopped (would-have rows). X5-43 event replays as a gate before paper (A3-174). X5-44 calendar-timed looks for rare traders (A2-185). X5-45 the old WF3 branches as zone transitions (A4-143). X5-46 a verification template per unit type (A2-228). X5-47 the plan states what counts as unseen data. X5-48 "bad day" defined from the card (A2-177). X5-49 agents diagnose fills and costs from node rows (G9 §3.4). X5-50 agents propose which units to pool (A4-149).
- X5-51 a random-entry control twin (A2-178; wild). X5-52 cross-context transfer as stronger evidence (wild). X5-53 agents stake family wealth (A2-220; wild). X5-54 family lineage credit (wild). X5-55 live canary across markets (A4-026). X5-56 verification state is a halt input.

### 3.1 Hybrids

Format per hybrid: components; need; what and how; levels; per class and style; ledger; performance and survival; evidence chain with the weakest link; maturity.

#### A. Before trading: the claim, the proof battery, the band, the plan

**X5-H01. Counted birth: a registered claim with a novelty check, in a search ledger that counts failures.**
- Components: A4-117 (register a falsifiable hypothesis with a novelty check), A4-110 (append-only search ledger, failures included), A2-202 (trial ledger with pre-registration weights), A5-032 (description, code and behaviour must agree), A4-041 (identity table: which edit is a counted try), X5-07.
- Need: an honest try count, so the deflated Sharpe and the family budget mean something when agents propose units by the dozen (D42, R6-T09 "every LLM-discovered strategy failed once trials were counted").
- What and how: a unit cannot be born without a claim card that states thesis, context, classes, claimed band, falsification tests and a novelty check against the family's ledger. Every evaluation, including syntax failures, abandoned branches and logic-changing repairs, gets an immutable trial id with a parent. The identity table maps each edit label to "none / calibration row / new version / new unit" and whether it counts as a try. Before any test, the card's words, the compiled unit and the backtest's behaviour are compared and must agree. The effective try count is the stream-clustered count of X5-07 over this ledger, never a count of edits.
- Levels: unit (the card), methodology (the family ledger), system (the identity table).
- Per class and style: the same for all classes; the novelty check keys on logic plus context word, so a mean-reversion scalper on gold and on EURUSD is one family. Swing units have fewer trials per month, so their ledger is thin and their deflation small; scalpers run hundreds of variants and their deflation is the whole story.
- Ledger: `effective_tries`, `ev_claim_registered`, `ev_novelty_check`, `ev_trial_ledger_id`, `ev_prereg_weight`.
- Performance: fewer false edges reach paper, so paper lanes and level-1 budget go to units with a real chance. Survival: a false unit at level 1 is the main way a weak book bleeds; counting tries cuts that at the source.
- Evidence chain: R6-T09 paper 2608.27734 (author backtest, two models; the trial-count finding is strong); A4-041 is built in the unit stack; A5-032 is a controlled test in its own paper. Weakest link: the novelty check is an idea with no test anywhere.
- Maturity: solid.

**X5-H02. Look-ahead blocked in the tools: a frozen experiment contract, a sealed evaluator, typed tools and point-in-time gating.**
- Components: A4-118 (frozen experiment contract, capped evaluations, sealed test scored once), A2-208 (sealed evaluator), A4-111 (registry-validated typed tools), A4-113 (model-training contamination apart from code leakage), A3-057 and A4-180 (point-in-time availability gating), A5-068 (audit reused pipelines; replicate a headline on a pinned version), A2-146 (backtest validity stamp), A5-047 (same-bar barrier ambiguity: conservative fill).
- Need: statistics cannot catch leakage (a planted Sharpe-35 oracle passed deflated Sharpe and PBO, R6-T09), so the block must be in the tool layer, which is where QMB's B12 conformance pack already lives.
- What and how: the harness, not the agent, sets the data snapshot, universe, decision and execution lag, folds, costs and candidate budget. Agents compose only typed, registry-validated tools (B19's `unit` and `blocks` toolsets are nearly this), so a unit cannot read a bar it could not have seen. Every input carries event time and availability time; a record is visible only if available at decision time. The test window is scored once; any further look is a new counted try. A validity stamp on every result records tick share, cost model version, fill convention and the same-bar rule (conservative fill when a bar crosses both stop and target). Any evaluation code reused across families is audited for look-ahead, and a headline result is replicated on a pinned version before the judge trusts it.
- Levels: system (the harness), unit (the stamp).
- Per class and style: futures, energy and metals need the contract-level rule (H28); crypto needs funding and liquidation in the stamp; stocks need point-in-time constituents. Scalpers are the most exposed to the same-bar rule; swing units to the availability-time rule on macro inputs.
- Ledger: `ev_unseen_data_source`, `ev_validity_stamp`, `decision_freshness_bound`, `ev_test_window_scored_once`.
- Performance: none directly; it stops false edges from costing paper and live budget. Survival: a leaky edge is the worst survival case, because it looks perfect until it meets live data.
- Evidence chain: 2608.27734 (planted oracle, author backtest), AQuA 2608.12841 (sealed sandbox), A5-068 (a real audit finding), QMB B12 (built). Weakest link: no QMX piece pins and replicates a headline today.
- Maturity: solid.

**X5-H03. The proof battery: five gates on excess returns with a friction floor, a cost-stress grid, a delay test and per-criterion rejection rates.**
- Components: A2-206 and A3-005 (five-gate falsification with a +1 bar delay test), A2-203 (gates on excess returns, per-criterion rejection rates), A1-146 and A5-157 (one cost ledger and a cost-stress grid), A1-138 and A2-223 (edge-to-cost admission: lower bound of gross edge at least 2× stressed cost, 3× for negative skew), A2-212 (Monte Carlo shuffles, 5th percentile), A2-211 (walk-forward with an efficiency score and a plateau choice), A2-179 and A2-180 (deflated Sharpe over effective tries; PBO by CSCV), A2-209 (worst-regime Sharpe), A3-240 (re-rank under alternate execution assumptions).
- Need: QMB's "prove" step must answer "edge after costs on unseen data, luck removed", which today it answers only in part (G8 §5.2: costs uncalibrated, commission outside R, PBO deferred).
- What and how: every gate runs out of sample at once: net t-statistic at least 2 per fold, at least 30 trades per fold, positive net after instrument-specific cost, same sign every test year, a permutation test, a +1 bar delay test (a sign flip means reject), the lower bound of gross edge at least twice the stressed round-trip cost, the Monte Carlo 5th percentile above the guardian band, walk-forward efficiency above its floor, deflated Sharpe over the family's effective tries, PBO below its threshold, and a worst-regime block mean that is not deeply negative. Gates are computed on **excess** returns against the class benchmark over the holding time (index drift, carry, funding), because absolute-return gates reject even true t = 4 signals when market volatility hides the edge (R6-T09 paper 2). The death certificate prints which gate killed how many candidates per family. Results are re-ranked under a default-stress execution assumption; a ranking that flips is reported.
- Levels: unit, methodology (per-family rejection rates).
- Per class and style: cost floors in the instrument's own units (MNQ points, not percent); crypto's 15-minute reversal is real but fees bind, so the 2× cost gate decides; FX dealer quotes have no public queue, so the delay test uses the next quote, not the next bar; stocks need survivorship-safe universes. Scalpers live or die on the cost gates; swing units on the regime block.
- Ledger: `expectancy_floor_r`, `round_trip_cost_r`, `cost_stress_multiple`, `deflated_sharpe_min`, `pbo_pass_threshold`, `walk_forward_efficiency_min`, `monte_carlo_p5_floor`, `ev_excess_return_basis`, `ev_delay_test_bars`, `ev_worst_regime_sharpe`, `ev_regime_min_length`, `ev_gate_rejection_rates`.
- Performance: the battery kills strategies that cannot pay their costs before any paper time is spent. Survival: the regime block catches the "looks fine on average, dies in one regime" case that cost quant funds in 2007.
- Evidence chain: 2605.04004 (author backtest, out of sample, 11 of 14 retail patterns fail), 2610.07701 (injected-truth, controlled), AutoQuant 2512.22476 (author backtest), R3 §1.2 (arithmetic), old QMX Monte Carlo rule (spec). Weakest link: the worst-regime block on a 600-trade record is noisy; 22% of healthy +0.10R units show a negative worst block by chance [arithmetic], so the bar must be "deeply negative", calibrated per unit (H42).
- Maturity: solid.

**X5-H04. The edge band from four shrinkages: take the lowest computable low end.**
- Components: A2-187 (deflated holdout, half the in-sample as fallback), A2-205 and A1-027 (James-Stein shrink of the promoted winner toward the pool), A1-028 and A5-098 (hierarchical and empirical-Bayes family shrink; noise families shrink to zero), A2-204 (replication-ratio haircut), A1-021 (lower-confidence-bound sizing for the gate only), X5-03.
- Need: "give the edge a range" (A24) with a low end that has a reason he can read, and that replaces the flat "half" he rejected (D14).
- What and how: the card computes up to four low ends: (1) the deflated holdout expectancy minus one standard error; (2) the James-Stein shrink of the winner's Sharpe toward the family pool, using the full candidate pool (except when variants are near copies, where the raw estimate ranks better); (3) the empirical-Bayes family shrink, where a family whose true-performance spread fits near zero pulls every child toward zero; (4) the replication-ratio haircut from the number of signals and assets and the history length. The planning low end is the lowest of those computable; "half the in-sample number" is used only when none is. The high end is the raw holdout mean. The card prints all four with their inputs, so he sees where the number came from and can change how it derives (STATE item 37).
- Levels: unit (the band), methodology (the family prior).
- Per class and style: the family prior is per logic × class; crypto and single-stock families start with a wider prior spread; scalper families have many near-copies, so the James-Stein term is checked against a correlation cap before it is used.
- Ledger: `edge_range`, `ev_edge_band_rule`, `effective_tries`, `judge_market_shrink_k`, `ev_replication_ratio`, `ev_family_prior_spread`.
- Performance: a thin edge is not over-trusted, so level-1 budget is not wasted on it; a strong edge keeps a high low end and steps up sooner. Survival: sizing's gate reads the low end only (H44 in X2's terms, X5-30), so a wrong point estimate cannot size a unit.
- Evidence chain: 2606.01650 (simulation, James-Stein default; miss under correlation above 0.75), R3 §1.1 (published shrinkage 26-58%), 2501.03938 (closed form, linear models), A5-098 (author backtest). Weakest link: the family prior needs a family with history; a first child of a new logic gets only (1) and (4).
- Maturity: solid.

**X5-H05. The honest counts on the card: evidence-count report, observation unit and worst-regime score.**
- Components: A5-030 (four counts: days, non-overlapping episodes, independent blocks, distinct regimes), A2-161 (observation unit: completed campaigns or non-overlapping risk blocks), A2-241 (competing risks: an open trade is censored), A2-209 (minimum regime performance), A5-131 (block-persistence test with tries counted).
- Need: "600 trades" means nothing if twenty fills came from one position or all trades share one session; the plan must count independent opportunities (R4 technique 11: N_eff ≈ N(1 − ρ)/(1 + ρ) for autocorrelated streams).
- What and how: every validation result carries four counts beside its nominal trade count. The observation unit is chosen before data: a completed position campaign for scalpers that add to positions, a non-overlapping risk block for units holding several positions at once. An open trade at the look is censored, not dropped. The worst-regime block mean is reported beside the average with a fixed split count and minimum length, so cards compare. Persistence of good and bad regimes in the unit's own record is measured in block sums, with each block size scanned counted as a try.
- Levels: unit.
- Per class and style: 24/7 crypto has no weekend break to separate blocks; FX blocks follow sessions; a swing unit's "regime" is weeks, so its regime score is noisy and reported with its standard error.
- Ledger: `verification_trades_needed`, `min_trades_for_verdict`, `ev_independent_episodes`, `ev_observation_unit`, `ev_worst_regime_sharpe`, `ev_regime_min_length`.
- Performance: proof is not overclaimed, so a unit is not stepped up on fake evidence. Survival: units whose evidence is really a handful of sessions are held at level 1.
- Evidence chain: A5-030 and A2-161 are the alphaXiv assistant's proposals (idea); 2604.08356 (author backtest, monthly factors). Weakest link: no paper gives the observation unit for a retail scalper; it is a convention.
- Maturity: plausible.

**X5-H06. The verification plan with a correlation column, an event window and a provable-edge line.**
- Components: A2-186 (plan with a "too thin" verdict), A2-181 (trades to proof), A2-188 (pooled proof discounted for correlation), A5-002 (breadth in independent opportunities), A5-007 (breadth haircut chain), A2-210 (certified alpha capacity: price decay while proving), R3 §3.3 (insurers' event window), X5-01, X5-02, X5-12, X5-37.
- Need: he reasons in frequency; the plan must show what frequency buys and what correlation and shared moves take back, before any unit trades (M11's flaw check).
- What and how: before paper, a script writes the plan: the band (H04), trades to proof at the low end ((z_conf + z_power) ÷ per-trade Sharpe)², the expected trade rate from the card, the number of units of the same logic in the family, their measured correlation (or a prior by shared driver: same currency, same class, same session, until weeks of paper exist), N_eff = N ÷ (1 + (N − 1)ρ), and the calendar estimate for the family claim and for this unit's own placement. An event window (one US release, one risk-off hour) counts losses from one move once across the family, so twelve units on one release add one episode of evidence, not twelve. The plan prints the "too thin" verdict against the allowed incubation, and the provable-edge line: at 4 trades a day for 60 days, one unit can prove +0.16R (58% wins) and ten independent units +0.05R (52.5%) [arithmetic §3]. A certified-capacity note prices what the edge is worth after the time proof takes, so a slow-decaying edge that needs 2,000 trades is called out as "proved after it is gone".
- Levels: unit (own plan), methodology (the family plan), portfolio (the BMS sees the sum of calendars).
- Per class and style: FX pairs sharing USD get a prior ρ of 0.3 to 0.5; index futures across regions 0.5 in risk-off; crypto coins 0.6 to 0.8; metals against each other 0.4; a cross-class family starts at 0.1. Scalpers reach proof in weeks; ORB units only through breadth across session opens (X5-44, H43); swing units are "too thin" almost by construction and are verified as a family or not at all.
- Ledger: `verification_trades_needed`, `ev_calendar_to_proof`, `ev_confidence`, `ev_power`, `ev_max_incubation_days`, `ev_too_thin_verdict`, `effective_independent_bets`, `unit_result_correlation`, `ev_pool_corr_prior`, `ev_pool_corr_cap`, `ev_event_window_minutes`, `ev_capacity_note`.
- Performance: it steers agents toward logics that can be proved in time, which is where his frequency edge lives. Survival: the "too thin" verdict stops money going to claims that can never be settled.
- Evidence chain: R3 §1.1 (arithmetic, MinTRL in `R05`), R2 §4.2 (N_eff), 2610.01115 (certified capacity, simulation), the insurers' hours clause (industry practice). Weakest link: the prior ρ table is a guess with a label until paper measures it.
- Maturity: solid.

**X5-H07. Effective challenge: an independent challenger that also commissions the random control.**
- Components: A4-136 and A2-197 (independent challenger before paper, writing a note), A4-137 (prove an agent's value by ablation), A2-138 (validate a gate against random admission at the same rate), A1-173 (any claim must beat a random control at the same activity), A3-057 (point-in-time check on inputs), X5-28.
- Need: the agent that built the unit must not be the one that waves it through (SR 26-2 "effective challenge" with independence); and his "how do we prove it works rather than assume" (1 Nov backstory).
- What and how: after the referee and before the paper card, a second agent that did not build the unit reads the claim card, the verdict, the search ledger and the journals, and writes a challenge note: is the reason economic, is the context claim testable, how many tries does the family show, which inputs could have been unavailable at decision time, what would make it fail. It never writes a verdict. It may request one deterministic run: the same logic with random entries at the same activity (H08), or a random-admission comparison for a filter the unit uses. The note is attached to the passport and shown on the promotion packet.
- Levels: unit; methodology (the challenger sees the family).
- Per class and style: the challenger's checklist is per class (rolls and contract months for futures and energy; funding and liquidation for crypto; corporate actions for stocks; dealer-quote skew for FX).
- Ledger: `ev_challenge_note_required`, `ev_control_run_requested`.
- Performance: fewer months lost on units a sceptical colleague would have killed. Survival: catches the shared-assumption case (bank guidance's "aggregate model risk") before ten units share it live.
- Evidence chain: SR 26-2 (regulatory practice, READ in R3), A4-137 (assistant's evaluation design, idea), A1-173 (controlled test in its paper). Weakest link: no evidence that an LLM challenger finds what a human would; the ablation in A4-137 is how to find out.
- Maturity: plausible.

**X5-H08. The null beside every unit: event replays, the dry chassis and a no-edge synthetic market.**
- Components: A3-174 and A2-222 (event-replay gate before paper), A3-175, A4-181 and A1-174 (dry chassis: random entries with the full template), A2-147 and A3-173 (no-edge agent-based market as a null), A2-148 (a null chosen to match the claim), A2-136 (fixed-count placebo for filters), X5-43, X5-51.
- Need: a gate that a random-entry unit can pass measures the risk layer, not the edge; and a family's search needs a false-discovery rate it can show.
- What and how: three nulls. (1) Five to ten recorded event days per instrument class; no single event may lose more than the cap. (2) The dry chassis: the unit's own exits and the full risk template with random entries at the unit's trade rate, run through the same battery; every gate must fail it, and the unit must beat it on the same trades-to-proof arithmetic. (3) The family's search procedure run on a synthetic no-edge market grown from rules; the share of "winners" it finds is the family's false-discovery rate, printed on every child's card. Filters a unit uses are judged against placebo selections of the same count.
- Levels: unit (1, 2), methodology (3).
- Per class and style: event lists per class (NFP and FOMC for USD pairs and indices; EIA for energy; exchange outages and funding spikes for crypto; earnings gaps for stocks). The dry chassis matters most for scalpers, whose "edge" is often the exit.
- Ledger: `ev_event_replay_loss_cap`, `ev_event_days_count`, `ev_dry_chassis_result`, `ev_family_false_discovery_rate`.
- Performance: kills exit-flattered edges early and sends agents back to the entry. Survival: event replays are the only pre-paper check against the gap-through-stop case the B10 market rules already model.
- Evidence chain: A1-173 (controlled test: a 48%-accurate classifier cut drawdown 93% by trading less), the minority-game null (simulation), event replays (idea, old Stage H). Weakest link: the synthetic market's realism; its two gates (stylised facts on held-out data, closed-loop response) are A5-060's and unbuilt.
- Maturity: plausible; (3) wild.

#### B. Paper and the click

**X5-H09. The honest machine check: a paper twin started at the same minute as the control, inputs first, in a week.**
- Components: A2-217 (two clocks), A2-166 (inputs first: cost, fills, trade rate, holding time, replay match), A4-025 (Kayenta: judge against a fresh baseline started at the same time, critical metrics, no-data fails), A4-035 and A2-178 (paper twin with a per-trade gap row), A5-047 (conservative same-bar fill in replay), A2-169 (replay match below 0.80 lands a bench card), X5-09, X5-13.
- Need: 7 days of paper that is honest about what it proves (D22), and a cost and fill check that acts in days.
- What and how: the machine check never compares live to the backtest's history; it compares the live (or demo) lane to a paper twin on the same signals and code started at the same minute, so market drift cancels. Critical metrics over the first 50 trades or 7 days, whichever first: cost per trade in R (card 0.06R; a rise to 0.11R is 8.8 standard errors after 50 trades [arithmetic §12]), slippage per trade, trade rate (a halved rate is 2.6 standard deviations out after 7 days at 4 a day [arithmetic §11]), holding time inside the card's 10th-90th percentile, replay match at or above 0.80 under the conservative fill rule, and the twin gap per trade. No data on a critical metric fails the check. One metric out: yellow; two: red for the machine, which is a bench card, not a verdict on the edge. The edge clock keeps running into live (H13).
- Levels: unit; node (the twin runs there).
- Per class and style: crypto twin gaps include funding; FX gaps are dealer skew after fills; futures gaps include the tick rounding; scalpers get the 50-trade window, ORB and intraday the 7-day window, swing units a 30-day window with trade-rate only.
- Ledger: `ev_machine_check_days`, `ev_machine_check_trades`, `replay_match_floor`, `cost_drift_multiple`, `trade_rate_band`, `ev_holding_time_band`, `ev_twin_enabled`, `ev_twin_gap_r`.
- Performance: a working machine reaches level 1 in a week instead of waiting 28 days for a verdict paper cannot give. Survival: a broken machine (doubled cost, wrong rate) never reaches money.
- Evidence chain: Kayenta (production practice, CHECKED in R7), the arithmetic above, G9 §3.4 (slippage data exists in node rows). Weakest link: paper has zero slippage (G9 §3.1), so the twin's cost gap is only meaningful once the paper lane models slippage from node order rows (gap, section 7).
- Maturity: solid.

**X5-H10. The bound click: a promotion packet that approves one exact thing, expires, and is re-checked at use time.**
- Components: A4-120 (human-signed packet of one immutable artifact; any change is a new candidate), A5-154 (bound approval packet), A5-057 (class-aware pre-queue checks), A4-041 (identity table), R4 technique 20 ("Approve What, Exactly?": effect binding, single-use expiring grants; loopjacking: re-check at use time), A5-061 (kill-switch lifecycle test), X5-15, X5-34.
- Need: his click is the only door to live (C-23); the click must approve exactly the version that executes, at the level and on the markets he saw, and nothing an agent did later may widen it.
- What and how: the packet is one immutable artifact: the claim card hash, the compiled unit hash, the sizer and cost model versions, the market list, the proposed size level, the limits, the plan, the zone, the inputs strip, the challenge note, the book's marginal effect (H11) and every tried candidate and failure in the family. Deterministic pre-queue checks run before he sees it: reproducible from frozen inputs, contract tests, no data later than decision time, no evaluation-window reuse, realistic costs, limits respected, class-aware facts (contract month, roll, funding, borrow). His decision binds to the hash, the markets, the level and an expiry. The runtime holds a narrow capability to activate only that hash at that level; a version change, a market change, a level change above the approved one, or a stale approval revokes it, and the check runs again at use time, not only at review. The record is append-only and replayable.
- Levels: unit, node (the capability), system (the record).
- Per class and style: class-aware pre-queue checks as in A5-057; a multi-market unit's packet lists every market, so the one-market refusal in `promote.py` (G9 §3.2) becomes a market list with a canary subset (H46).
- Ledger: `ev_approval_hash`, `ev_approval_expiry_days`, `ev_approval_level_max`, `ev_approval_markets`, `paper_to_live_carry_rule`.
- Performance: none; it is the control that lets everything else be automatic. Survival: closes the "agent promotes itself" path that 9 of 10 models found in the I-HITL test (R4 technique 20).
- Evidence chain: AllPath (paper account, one operator; live practice), "Approve What, Exactly?" (27,108 scripted trials, controlled), C-23 (built, operator-only). Weakest link: expiry and re-check at use time exist in no QMX code; the capability model is a chassis change (collision with X1).
- Maturity: solid.

**X5-H11. Two vetoes, logged apart: statistical authorisation and portfolio approval.**
- Components: A5-035 (statistical authorisation kept apart from portfolio approval), A5-005 (admit a sleeve by its marginal effect on the book), A1-106 (effective-bet measures and the three-number test), A1-095 (inverse volatility as the default allocator), X5-30.
- Need: a unit can pass every evidence gate and still be a bad addition (correlated with live units, too big for its venue, concentrated); and the opposite: a weak but uncorrelated unit may be the best addition (his "carry the load").
- What and how: the promotion packet carries two verdicts. The evidence verdict (this file) says the low end is positive with evidence. The portfolio verdict (X2's and the BMS's) says what the unit does to the book out of sample after costs: change in book Sharpe, max drawdown, tail loss, worst cluster contribution, effective number of bets. Each veto is logged on its own with its reason; a unit vetoed by the portfolio is not "proven false", it is "not now", and it stays on paper with its evidence clock running. The allocator's default is inverse volatility with the edge as a gate (X5-30), so the evidence verdict never sets the amount.
- Levels: unit (evidence), book and portfolio (marginal effect).
- Per class and style: cross-class units score well on marginal effect; same-currency FX scalpers score badly however strong their own edge; crypto's weekend factor raises its marginal tail contribution to index sleeves (R6 §T-07).
- Ledger: `ev_statistical_authorisation`, `ev_portfolio_veto_reason`, `effective_independent_bets`, `unit_result_correlation`, `unit_capital_share`.
- Performance: the book grows by breadth, not by stacking the same bet; a weak uncorrelated edge gets its place. Survival: the worst-cluster test keeps ten USD scalpers from being one bet.
- Evidence chain: A5-005 (author backtest), A1-106 (idea, measures standard), R3 §2.3 (adaptive allocation warned against). Weakest link: the book-level out-of-sample test needs the paper lanes of every live unit to run in step, which the node does not do today.
- Maturity: plausible.

**X5-H12. The funded promotion ledger: Promote's wealth as the paper-to-level-1 gate for agent-born units.**
- Components: A2-201 and A4-121 (anytime-valid funded promotion ledger), A2-220 (family error budget, alpha investing), A4-149 (agents propose families; stakes), A2-155 (bounded betting e-process), A2-156 (small-bet-heavy priors for weak edges), A4-120 (the packet), X5-26.
- Need: with agents proposing freely (D42), the system needs a bound on false promotions across the whole family, not per unit; repeated "is it significant yet?" checks promote a false rule in 94.5% of null paths, a funded e-process in 0.0% (R6-T09).
- What and how: each candidate is hashed at birth and receives testing wealth π from its family's lifetime budget (the budgets sum to at most 1). From the next trade on, it bets on a clipped, cost-adjusted score Y = clip(R ÷ scale, −1, 1) with a fixed bet grid; the running wealth E is the average over the grid. Paper and level-1 trades both count; backtest and holdout never do. Crossing E ≥ 1 ÷ (α × π) is an **authorisation request**, never an order: it lands on the packet (H10), and the unit starts at the next session open after his click. Abandoning a candidate does not refund its wealth; any edit, revival or restart is a new candidate needing new wealth; a proved unit refunds the family. [arithmetic §4] on ±1R trades with scale 2R: a no-edge unit crosses in 2.3% of paths by 3,000 trades at π = 1 (0.8% at π = 0.25); a +0.10R unit in 99.7% (median 624 trades; 925 at π = 0.25); a +0.05R unit in 60% (median 1,372). The price of strictness is a thin edge waiting longer, which the plan already shows.
- Levels: unit (the candidate), methodology (the family budget), system (the ledger).
- Per class and style: the clip scale is per class (crypto clips more often; set the scale at the 95th percentile of |R| from the holdout); families of near-copies are conservative, so near-copies are merged by result-stream clustering (X5-07) before wealth is split.
- Ledger: `sequential_evidence_pass`, `ev_promotion_wealth`, `ev_family_alpha_wealth`, `ev_alpha_spend_per_test`, `ev_alpha_refund_per_discovery`, `ev_bet_grid`, `ev_score_scale_r`, `ev_evidence_e`.
- Performance: strong edges cross in a few hundred trades; the family budget pushes agents toward fewer, better candidates. Survival: the only gate in this file with a proven 0.0% null rate under adaptive births (1.77% false-family rate against 18.4% unfunded).
- Evidence chain: 2611.03384 (3,000 null paths, ETF panels, retrospective; simulation grade), my arithmetic on ±1R trades. Weakest link: the paper tests daily calendar rules at 5 bp; QMX's scale, clipping and grid are untested on scalper R streams.
- Maturity: solid for the mechanism; plausible for the numbers.

#### C. Live: levels, speeds, monitors

**X5-H13. Risk-tiered proof: the evidence bar rises with the size level, and proof continues at the smallest live size.**
- Components: A2-218 and A1-053 (proof continues at level 1; trial phases), A5-077 (risk-tiered gate strength: more evidence for bigger or irreversible allocations, never a gate loosened because it rejects too much), A5-039 (six-tier ramp stepped only on matured, independent evidence), A2-195 and A4-027 (payouts and steps from live rounds only), A2-190 (BOIN levels), X5-10, X5-16.
- Need: "7 days doable" and "QMB proves before demo" at once (D22, D18): the machine is proved in a week, the edge keeps proving itself while real money is small, and bigger money waits for more evidence.
- What and how: size is a level L0 (paper) to Ln. Each level has its own evidence threshold on the same e-meter (H12, H15): e ≥ 10 to leave paper, 20 to hold level 1, 50 for level 2, 100 for level 3, and so on, with the ladder's bad-cohort rule (H14) as the second condition. [arithmetic §7] a +0.10R unit reaches e 10 in a median 335 trades, 20 in 485, 50 in 641, 100 in 750, so the ladder spends trades before it spends money, and a thin edge that never reaches 50 simply stays at level 1, earning a little, which is his "squeeze some money out of a weak edge" without ever leaning on it. Steps rest on paper and live trades only; a backtest never raises a level. A step applies at the next session open (Promote's next-session start).
- Levels: unit (the ladder), book (the level-to-dollars map is X2's, collision C4).
- Per class and style: level 1 must be above the venue's minimum lot or it does not exist for that instrument (Q5); crypto perpetuals allow tiny notional, FX micro-lots allow $0.10 per pip, index CFDs often do not; scalpers climb in weeks, intraday in months, swing units hold level 1 for a long time or are pooled.
- Ledger: `size_levels`, `ev_level_count`, `ev_level_evidence_alpha`, `size_ramp_to_full`, `grow_back_rule`, `ev_proof_counts_live_min_size`.
- Performance: a proved edge reaches full size on evidence, not on a calendar; a thin edge still pays at level 1. Survival: money at risk grows only as the chance of being wrong shrinks; at level 1 the whole exploration budget is bounded (H48).
- Evidence chain: Numerai (live practice), FDA phases (regulatory practice), A5-077 (simulation in its paper), my arithmetic. Weakest link: the thresholds 10/20/50/100 are reasoned, not derived from a loss model; H42 calibrates them per unit.
- Maturity: solid.

**X5-H14. The level ladder as a coupled pair: BOIN cohorts, slow start with a first-warning switch, overdose-controlled steps and a memory ceiling.**
- Components: A2-190 and A1-052 (BOIN: up below λe, down above λd, lock dangerous levels, never skip), A2-191 (3+3 cohorts), A5-128 (EWOC: overdose-controlled step, raise only while P(next level too high) < α), R9 §0.3 new kinds (slow start with first-warning switch; memory ceiling), A2-124 (world-switch reset), A4-002 (applier mode "at start"), X5-16, X5-41.
- Need: his "size down, but not quickly" and "brakes first, accelerators second" as one rule with hysteresis, so the ladder does not flap and a restart after a trip is fast but careful.
- What and how: cohorts of trades (25 by default for scalpers, 10 for ORB, 15 for intraday), a bad cohort is net R at or below the unit's own bad-cohort line (from the card's daily distribution, X5-48). The step-up bar λe and step-down bar λd come from the BOIN formulas at a target derived from the unit's own healthy bad-cohort rate (a fixed 30% drug default would let a dead unit climb: [arithmetic] a 55% unit has a bad 25-trade cohort 9.7% of the time, a 52.5% unit 14.9%, a no-edge unit 21.4%; at a 15% target the bars are 11.8% up and 17.9% down). Slow start: while no warning has fired, steps may be two levels at a time with small cohorts; the first warning (H15) switches to one level and double cohorts. Overdose control: a step up is allowed only while the posterior chance that the next level's bad-cohort rate exceeds the target stays under α_level. Memory ceiling: after a step down, the unit regrows quickly to one level below the level where it tripped, then one cohort at a time near it. A locked level stays locked until he unlocks it. A world switch (paper to live, PC to VPS, venue change) resets the ladder to level 1 and marks costs uncalibrated.
- Levels: unit.
- Per class and style: cohort sizes by trade rate; the bad-cohort line in R so classes compare; crypto's weekend cohorts are tagged; a unit with several positions at once counts a cohort in non-overlapping risk blocks (H05).
- Ledger: `ev_cohort_trades`, `ev_bad_cohort_r`, `ev_bad_cohort_target`, `ev_level_up_bar`, `ev_level_down_bar`, `ev_level_lockout`, `ev_level_min_cohorts`, `ev_level_memory_ceiling`, `ev_slow_start_enabled`, `state_carry_rule`.
- Performance: fast climb while nothing is wrong (slow start) beats a fixed monthly ramp. Survival: the first warning halves the speed; the ceiling stops the re-raise straight into the trip; levels never skip.
- Evidence chain: FDA review of BOIN (regulatory, fit-for-purpose), TCP (production software, CHECKED in R7), EWOC (dose finding, literature), my cohort arithmetic. Weakest link: none of it was ever run on a trading unit; R9 §1.6 rates dose escalation "idea" for trading.
- Maturity: plausible.

**X5-H15. Three speeds, three signals, three jobs: inputs first, e-detector warnings, funded confirmation; a money brake apart.**
- Components: A2-079 (three speeds of brake), A5-028 (three signals, three jobs: e-value says investigate, burn rate says page, hard limit acts), A2-166 (inputs first), A2-149 (trade-side CUSUM against the holdout baseline), A2-152 (multi-stream e-detectors), A2-155 (bounded betting e-process against a minimum viable edge), A2-160 (economic failure against relative degradation, cause recorded), A2-174 (separate edge decay from spread, slippage, volatility and faults), A5-069 (input-shift monitor by rank martingales, apart from the net-return test), A4-007 (Simplex: a verified fallback decider beside the high-performance one), X5-05, X5-18, X5-19.
- Need: "bad day or broken edge" answered with three honest clocks instead of one 20-trade comparison (E28; the shipped `dc-decay` job).
- What and how: **Speed 1, days:** the inputs strip (H09) and an input-shift monitor on the unit's live features (spread at entry, hour mix, volatility state) by rank martingales, kept apart from P&L; one input out is yellow, two are red for the machine. **Speed 2, weeks:** a warning detector on trade R: CUSUM against the holdout baseline (allowance 0.05R, limit for about one false alarm per 1,000 healthy trades; dead unit alarms in a median 190 trades, half-edge 315 [arithmetic]) or a restarted e-detector; a warning steps size down one level and opens a review; the first-hundreds rule reads an early alarm as "the holdout was optimistic" first. **Speed 3, hundreds of trades:** a one-sided funded e-process against the minimum viable edge m (the cost-adjusted line below which the unit is not worth running); crossing confirms economic failure and demotes to paper; [arithmetic §6] at m = +0.05R with a lifetime budget of 0.05 over 20 units (e ≥ 400): a healthy +0.10R unit is never demoted in 4,000 trades, a unit at the line 0.4%, a dead unit 35% (median 1,860 trades), a bleeding −0.05R unit 99% (median 1,025). The dead unit is mostly caught by speed 2 and by the ladder long before. **Apart:** a pre-authorised money rule (X3's) that demotes before either when the loss budget says so, with its own cause code. The planned-look plan (X5-04) runs beside the e-process as the verified fallback: when the two disagree for more than a dwell time, the fallback decides.
- Levels: unit; portfolio holds the lifetime budget (H16).
- Per class and style: m per class in R after class costs; CUSUM limits per instrument (R5's per-instrument thresholds); crypto's heavy tails use the clipped score; swing units run speed 2 on calendar blocks.
- Ledger: `drift_state`, `cusum_limit`, `cusum_allowance_r`, `ev_cusum_watch_share`, `ev_first_hundreds_rule`, `ev_min_viable_edge_r`, `ev_evidence_e`, `ev_demotion_alpha`, `ev_input_shift_monitor`, `ev_fallback_dwell_trades`, `ev_demotion_cause`.
- Performance: a warning costs one level, not the unit; a healthy unit is almost never demoted by statistics. Survival: nothing in the slow lane acts on one day; the money brake does, and it does not wait.
- Evidence chain: CUSUM (Page 1954; R5 23103 per-instrument thresholds, author backtest), e-processes (2010.09686, theory; R4 technique 10 numbers are the assistant's), Simplex (secondary paper), my arithmetic. Weakest link: the minimum viable edge m is a number nobody has set for a retail scalper; it must come from the cost ledger (H38) and his minimum worthwhile return per unit (Q6).
- Maturity: solid.

**X5-H16. Many units, one alarm budget: e-BH for the review list, e-Bonferroni for demotion, patience logged, held at the BMS.**
- Components: A2-152 (multi-stream e-detectors with e-BH and e-Bonferroni; error over patience), A2-158 (lifetime false-demotion budget and re-promotion episodes), A4-161 (an alarm budget across many units), A2-030 and A2-142 (brake precision and alert scorecard), R3 §3.1 (grid zones of protection, graded delays).
- Need: twenty units watched for a year will throw alarms; without one budget the morning list is noise and he stops reading it (hospital alarm fatigue, R3 §3.6).
- What and how: one detector per live unit (H15 speed 2 and 3). The BMS holds the lifetime false-demotion budget q (0.05) and splits it by a union bound (α_i = q ÷ N, so 0.0025 at 20 units, e ≥ 400 to demote). The review list ("look at these") uses e-BH: flag the k largest if the k-th largest e-value is at least K ÷ (k α). Demotion uses e-Bonferroni. Every alarm count is shown beside its patience (how long the unit has been watched), and the review workload is sized to it. Zones of protection: a unit's own detector trips first; the family's pooled stream (H23) second with a delay; the BMS budget last. Each alarm source keeps its precision and recall, detection time and reset time.
- Levels: unit (detectors), methodology (family stream), portfolio (the budget).
- Per class and style: units sharing a driver (USD, BTC) must have detectors valid on the combined information; asynchronous sessions complicate the global filtration, so the family stream uses a daily clock.
- Ledger: `ev_lifetime_demotion_budget`, `ev_demotion_alpha`, `ev_review_list_rule`, `ev_patience_days`, `brake_precision`, `ev_alarm_recall`.
- Performance: fewer, truer alarms mean reviews happen. Survival: "any monitor that will eventually fire is, at its first alarm under no change, wrong" (R6-T08): the budget is the only honest way to watch many units.
- Evidence chain: 2501.04130 (theory plus simulation), hospital alarm data (industry). Weakest link: no holder for the budget exists in the stack; the BMS layer is "ideas only" (ledger v0 holes).
- Maturity: plausible.
**X5-H17. Evidence that restarts and pays for it; raw money under a variance cap.**
- Components: R6-T08 paper 2 (restarted, weighted conformal detectors; restart weights sum to one), A2-154 (Catoni bounds with a known variance cap), A2-161 (observation unit), A2-124 (world-switch reset), X5-19's first-hundreds rule.
- Need: one long cumulative test from promotion day goes sluggish after a long healthy period (delay grows with time monitored), and raw P&L in money is heavy-tailed.
- What and how: the warning detector restarts at every level change, world switch and version, and each restart spends a restart weight from a schedule that sums to one, so restarts are paid for and the lifetime error stays bounded. Monitoring in R uses the clipped score; monitoring in money (the Book's view) uses a running Catoni bound under a variance cap in R set per unit at promotion from the X4 stress battery, never from a sample variance of a dozen trades. Where no cap is defensible, money is not monitored statistically at all; only the clipped R score and the money brake are.
- Levels: unit; book (money view).
- Per class and style: crypto and single stocks need wider caps; FX majors narrower; energy needs a cap that includes inventory-release jumps.
- Ledger: `ev_restart_weight_schedule`, `ev_variance_cap_r`, `state_carry_rule`.
- Performance: a monitor that stays alert after six healthy months catches decay months earlier. Survival: the money view cannot be fooled by a sample variance from a quiet week.
- Evidence chain: 2609.27179 and 2202.01250 (proofs and simulations). Weakest link: independence within regimes is assumed; strategy P&L has volatility clustering.
- Maturity: plausible.

**X5-H18. The cone, judged in the current regime, with worry lines by style.**
- Components: A2-212 and X5-20 (Monte Carlo cone from the card), A5-072 (judge live results against the unit's expectation for the current regime), A2-014 (style-aware drawdown worry lines: depth and duration), A2-177 (bad day from the card's daily distribution), A3-189 (persistence readings: the MIS regime word).
- Need: a unit whose backtest spans three regimes is judged live against one of them; "below the cone" in a known bad regime is not decay.
- What and how: the card keeps the cone and the expected net R and drawdown per regime word (from its validation record, keyed by the MIS persistence words it was built with). The nightly job compares cumulative live R against the cone for the regime the MIS board shows now, falls back to the whole-record cone when the board is stale, and marks the fallback. Worry lines for max drawdown and time under water come from the unit's Sharpe, horizon and style archetype (trend units draw down deeper and longer than mean-reversion units at the same Sharpe), so "normal versus worry" is per style. Below the 5th percentile for one look: yellow; two looks: red for the ladder (step down), never for demotion, which is H15's job.
- Levels: unit; the MIS provides the regime word (G9 §4: the board path is built but unfed).
- Per class and style: the regime word is per class pack; crypto has no session-based regimes; swing units use weekly regimes.
- Ledger: `mc_cone_floor_percentile`, `ev_cone_looks_to_red`, `ev_regime_expectation`, `ev_worry_line_depth`, `ev_worry_line_duration`, `ev_bad_day_percentile`.
- Performance: fewer healthy units stepped down in a known bad regime. Survival: worry lines give a style-aware "cut or revise" line before the money brake.
- Evidence chain: 2608.00127 (simulation validated against history), A5-072 (author backtest), the cone (built, G9 §7.1). Weakest link: the board relay is unfed, so the regime word is not available on the node today.
- Maturity: plausible.

**X5-H19. The old WF3 signal made honest: brake-fire density with a baseline, a null, the right denominator and a trip tax.**
- Components: A2-086 (WF3 chronic breaker: fire density as decay evidence), A2-088 (expected fire rate on the certificate), A2-135 (random-control brake test at matched frequency), A4-155 and A2-137 (count every refusal by reason with the right denominator), A4-202 (measure the trip tax), A2-030 (brake precision), X5-21.
- Need: his memory is right that the circuit breaker caught decay (A26); it never had a baseline, so it also fired on healthy units as trade counts rose (STATE item 10).
- What and how: the card states the brake-fire rate a healthy unit shows, from the holdout run through the same brakes with the same counting rule (full stops, FI cuts by size, forced flats excluded). Live fires per 100 trades, counted against the signals that actually reached each brake, above the band are decay evidence for the ladder; inside the band they are noise. Every brake keeps its precision (share of fires that needed action), and the trip tax (time lost, forgone net P&L, exit costs, loss avoided) is replayed per trip. A brake whose precision is no better than a random brake firing as often is a defect and is switched off per unit type, never loosened globally.
- Levels: unit; the brakes themselves are X3's.
- Per class and style: the counting rule per style (FI cuts for scalpers); count brakes scale with the unit's trade rate and win rate (STATE item 10), so the expected rate is per unit, not a constant.
- Ledger: `breaker_fire_density`, `breaker_expected_fire_rate`, `ev_brake_fire_band`, `brake_precision`, `ev_trip_tax`, `exit_reason_code`.
- Performance: a brake that fires on healthy units stops stealing trades. Survival: the fastest coarse decay signal there is (days), now with a known false rate.
- Evidence chain: WF3 (old QMX spec, never run), R5 23482 (random-control brake test, author backtest), A4-155 (a real denominator error). Weakest link: the risk-stop reason code is wrong at the tip (G9 §1.4), and no brake runs, so there are no fires to count yet.
- Maturity: plausible.

**X5-H20. The test of the tests: gate scorecards, random-control validation, and the whole pipeline run on nulls and injected edges with its delay reported.**
- Components: A2-143 (monthly gate precision and lift), A2-142 (alert-rule scorecard), A2-138 (validate a gate against random admission at the same rate), A1-173 (beat a random control at the same activity), A5-034 (test the whole promotion pipeline end to end against nulls and injected edges), A5-050 (evaluate a monitoring agent as an alerting system), A2-029 (an incident over 20% of budget needs a postmortem), X5-22.
- Need: no universal "true winners lost versus false strategies caught" rate exists outside injected-truth simulation (R4 technique 11); QMX must measure its own, or its gates are decoration.
- What and how: monthly, for every gate (cost stress, PBO, plateau, machine check, CUSUM, cone, each brake, each level step), measure precision (share of fires that needed action) and lift (share of passes that later held, over the base rate). Quarterly, run the full gate sequence, sequential stopping included, on null paths and on injected edges of several strengths (0.02R, 0.05R, 0.10R, 0.20R) with realistic cost, latency and roll shocks, and report the false-promotion rate, the power at each strength and the delay in trades and days. Any gate with no lift for a unit type is reported as a defect and switched off per type. Any demotion that cost more than 20% of a family's budget gets a written postmortem (an agent drafts it; H30).
- Levels: system (the job), methodology (per family).
- Per class and style: nulls and injected edges per class, because cost floors and tails differ; a gate proven on FX majors is not proven on crypto (A5-029).
- Ledger: `brake_precision`, `ev_gate_lift`, `ev_gate_enabled_per_type`, `ev_pipeline_null_rate`, `ev_pipeline_power`, `ev_pipeline_delay_trades`.
- Performance: dead gates stop costing adoptions; the pipeline's delay becomes a number agents can design against. Survival: a gate that passes nulls is found before it passes a real null unit.
- Evidence chain: 2610.07701 (injected-truth, controlled), hospital alarm data, A5-034 (simulation design). Weakest link: injected edges on real tapes need the simulation bench (A5-161), which is X4's and unbuilt.
- Maturity: solid as a method; plausible for QMX now.

**X5-H21. Three twins on one paper lane: the paper twin, the random-entry control, and the shadow after suspension.**
- Components: A2-178 and A4-035 (paper twin with a gap row), X5-51 (random-entry control twin), A2-174 (shadow after suspension), A2-145 (shadow-first rollout: would-have rows, then ramped enforcement), A4-025 (fresh baseline), X5-39, X5-42.
- Need: fill-and-cost drift measured continuously; entry edge separated from kind exits; evidence that keeps flowing while a unit is stopped, isolated or demoted.
- What and how: the paper lane (C-12c) runs three lanes per live unit. (1) The twin: same signals and code, started with the live lane; the per-trade gap is fill-and-cost drift. (2) The control: random entries at the unit's trade rate with the unit's own exits; the real unit must beat it at planned looks. (3) The shadow: when the unit is paused, isolated, benched or demoted, its signals keep computing and write `would_have` rows tagged so they never count toward proof but do count toward trade rate and replay match. A new brake also runs shadow-first, writing would-have rows before it may enforce.
- Levels: unit; node (lanes).
- Per class and style: 24/7 crypto twins never rest; FX twins pause with the market; the control twin's random entries respect the unit's session windows so the comparison is fair.
- Ledger: `ev_twin_enabled`, `ev_twin_gap_r`, `ev_control_twin_enabled`, `ev_would_have_counts`, `ev_would_have_row`.
- Performance: the control twin is the cheapest proof that the entry, not the exit, carries the edge. Survival: a stopped unit's clock does not freeze, so re-promotion rests on evidence.
- Evidence chain: canarying (production practice), Jesse's random-entry test (practitioner), resilience4j metrics-only state (production software). Weakest link: three lanes per unit triple the paper load on the node; and paper has zero slippage, so (1) measures demo-versus-paper drift until the slippage model exists.
- Maturity: plausible; (2) wild.

**X5-H22. "Too good" checks: the upside alarm, the consistency rule and the hidden-ruin audit.**
- Components: A2-176 (upside alarm), A2-226 and A1-079 (best day at most half of total profit), A1-172 (hidden risk-of-ruin audit: volume escalation after a loss, stacking at worse prices, payoff asymmetry), X5-23.
- Need: traders learn that "too good" is usually leverage they did not mean to take, or a sizing bug; and one lucky day can pass as edge.
- What and how: above the cone's 95th percentile for two looks: yellow, an agent explanation requested (sizing bug, hidden shared exposure, broker change). Best day above half of a month's profit: yellow (it happens in 15% of healthy months [arithmetic §9], so never red). A nightly audit over closed positions for the four ruin fingerprints flags a unit whose exit set or sizer is martingale-shaped by accident.
- Levels: unit.
- Per class and style: the consistency rule needs a month of days; for ORB units use the best week; crypto's weekend days are tagged so a Monday gap does not trip it.
- Ledger: `ev_upside_alarm_percentile`, `ev_consistency_best_day_share`, `ev_ruin_audit_flags`.
- Performance: none. Survival: catches the "it was leverage" case before it meets its first bad day.
- Evidence chain: FTMO (live practice), A1-172 (idea from an MQL5 article). Weakest link: the ruin audit's fingerprints are heuristics.
- Maturity: solid (upside), plausible (the rest).

**X5-H23. Family-level decay: one logic fading everywhere, caught on the pooled stream, while cells are shrunk and judged slowly.**
- Components: A3-164 (correlation in the edge: one logic fading everywhere, caught on the pooled stream), A2-188 (pooled proof), A2-189 (per-cell verification with partial pooling), A1-166 (partial pooling of numbers per market and cell), A5-048 (pooling policy: pool normalised statistics, keep costs local, never pool market mechanics), X5-11, X5-40.
- Need: breadth proves the logic faster; it also means the logic can die everywhere at once, which no bet count removes; and a scalper's 48 cells have 40 trades each, too few to judge alone.
- What and how: the family's units pool their paper and level-1 trades on a daily clock into one stream; a CUSUM and an e-detector run on the pooled stream with a graded delay after the units' own (H16). A pooled alarm steps every member down one level and opens a family review. Each unit's record is cut by market × session (cells); a cell's estimate is shrunk toward the unit's pooled estimate by n ÷ (n + k); no cell is judged alone until it has its own trades-to-proof; a cell whose shrunk estimate stays below zero after local costs is proposed as `drop_market` (the existing `s2-tag-units-to-markets` card). Pooling policy: pool R, e-values and normalised evidence; keep costs, slippage and fill statistics local; never pool market mechanics (tick size, session, roll).
- Levels: unit (cells), methodology (the family stream).
- Per class and style: FX families by currency leg; index families by region; crypto families by coin cluster; a cross-class mean-reversion family pools on the regime word, not the class.
- Ledger: `ev_family_id`, `ev_cell_key`, `ev_cell_estimate`, `judge_market_shrink_k`, `correlated_market_merge_threshold`, `ev_family_stream_alarm`.
- Performance: the family proves the logic in weeks; cells are not dropped on noise. Survival: the pooled stream catches the regime change that kills a logic across markets months before any cell could.
- Evidence chain: R05 §2.4 (Stein efficiency), A3-164 (idea), R8 §5 (pooling across instruments, Carver and Jones-Shanken). Weakest link: the family definition is an agent proposal confirmed by correlation (X5-50); a wrong family pools unlike things.
- Maturity: plausible.

**X5-H24. Three zones as the coupled pair: red steps down or trips, green steps up, yellow holds; attack fast, release slow, with a dead band.**
- Components: A5-140 (three-zone pair), A2-196 and A4-159 (Basel traffic light), A2-167 (stacked levels and a demotion ladder), R9 §0.2 (coupled pair, hysteresis, asymmetric speeds; the audio compressor's attack and release), A2-076 (Topstep: down on patterns, up on shown consistency, never automatically), X5-06, X5-41.
- Need: one readable state word that is also the mechanism, and that does not flap.
- What and how: zone = f(inputs strip, warning detector, e-meter against the level's threshold, cohort rule, cone, family stream). Green: carry on; a step up when the level's evidence bar and cohort bar are both met and the family budget permits (H25). Yellow: hold, no loosening, no new markets, an agent explains; yellow carries no penalty. Orange (a sub-state of red for the ladder): step down one level. Red: paper, when H15's speed 3 confirms, or when futility at a planned look says the goal is out of reach. Attack is fast (one inputs fire is enough for yellow); release is slow (green again needs the e-meter back above the bar and a minimum number of days); separate trip and clear levels and a minimum hold stop chatter. The old WF3 branches map onto it: keep = green, reduce weight = orange, demote = red, retire and rehab as H27.
- Levels: unit; book and portfolio read the zone (H41).
- Per class and style: the minimum hold is in trades for scalpers and in days for intraday and swing units.
- Ledger: `drift_state`, `ev_zone_rule`, `ev_zone_min_hold`, `ev_zone_release_days`, `ev_orange_entry`.
- Performance: green units climb; yellow costs nothing. Survival: nothing jumps; a red at 02:00 steps down by rule and waits for morning only for the paper move if Q2 says so.
- Evidence chain: Basel (regulatory practice), Topstep (live practice), R9's pair definitions. Weakest link: the mapping of six inputs to three colours is a convention; H42 reports its simulated false rates per unit.
- Maturity: solid.

**X5-H25. Error-budget burn as the accelerator's permit: a spent family budget freezes step-ups and births.**
- Components: A5-141 (budget-burn permit pair), A2-029 (SRE error-budget policy), A4-032 (burn-rate alerting over two windows), A2-220 (family alpha wealth), R9 §0.3 "budget-burn permit".
- Need: accelerators that keep re-raising size into a family that is spending its false-discovery budget are the "sitting duck" in reverse; and his "brakes first, accelerators second".
- What and how: each family's lifetime budget (H12) and each family's loss budget (X3's) are burned by false promotions and by losses. Two windows: a fast burn (a week) pages (red, freeze all step-ups and new births in the family); a slow burn (a month) tickets (yellow, step-ups need his click). A healthy budget permits automatic step-ups by rule; an exhausted budget freezes them until a proved unit refunds it or the window rolls. The permit is read by the ladder (H14) before any step up.
- Levels: methodology (family), portfolio (the sum of budgets).
- Per class and style: budgets per family, not per class; a class isolation (X3's) freezes all families on that class.
- Ledger: `ev_family_alpha_wealth`, `ev_budget_burn_fast_window`, `ev_budget_burn_slow_window`, `ev_step_up_permit`, `period_loss_budget`.
- Performance: a family that is proving itself climbs freely. Survival: a family that is failing cannot climb while it fails.
- Evidence chain: SRE workbook (production practice), LORD-style online FDR (theory). Weakest link: no family budget exists; it is an idea with a strong analogue.
- Maturity: plausible.

#### D. Demotion, rehab, retirement

**X5-H26. Graded demotion with a cause code, a tested stop path, and re-promotion as a funded episode.**
- Components: A5-150 (workflow: graded live demotion), A2-160 (economic failure versus relative degradation, cause recorded), A2-158 (re-promotion episodes with halving budgets), A2-221 (re-promotion on an e-value plus a minimum time, not a streak), A5-132 (streak-bias correction), A5-061 (kill-switch lifecycle test), A1-064 (loosen only on proof after a cut), X5-18, X5-25.
- Need: demotion that is never one bad day (A25), that leaves no working orders behind, and that comes back on evidence, not on ten green trades (the old rule, dropped; a 2/3-win unit with zero edge makes ten straight wins 1.7% of the time, R2 §2.4).
- What and how: a warning (H15 speed 2) steps down and opens a review; confirmed economic failure (speed 3) suspends to paper; a pre-authorised money rule may demote first. Every demotion records its cause: statistical, distribution change, inputs drift, money rule, his hand. The demotion path cancels working orders, sets reduce-only, alerts, and names its re-enable condition; it is tested end to end, because a stop that leaves orders working is a failed control. Re-promotion is a new funded episode: the e-meter restarts on post-demotion paper trades, the episode's budget is half the previous one's (α_i × 2^−j), and a minimum number of days must pass; then it is "ready for his card". Streak rules are dropped because "wins after k wins" inside a short record is biased low.
- Levels: unit; node (the stop path).
- Per class and style: cause codes include class-specific ones (funding regime change for crypto; roll for futures); the minimum days are longer for swing units.
- Ledger: `ev_demotion_cause`, `ev_repromotion_episode_budget`, `ev_loosen_min_days`, `sequential_evidence_pass`, `repromotion_positive_demo_trades` (dropped, pointed at).
- Performance: a demoted unit with a real edge comes back on evidence in a few hundred paper trades. Survival: no orders left working; no free resets of evidence.
- Evidence chain: R4 technique 10 (assistant's numbers), A5-061 (simulation), R2 §2.4 (arithmetic). Weakest link: the halving episode budget is an illustration from the assistant, not a paper result.
- Maturity: solid.

**X5-H27. Rehab as a counted try with the family prior; retirement when the family's budget is spent; lineage credit.**
- Components: A2-229 (rehab as a counted try, retirement rules), A5-098 (empirical-Bayes family shrink; retired units stay in the prior), A1-028 (hierarchical shrinkage), A4-143 (old WF3 pool cleaning branches), A4-114 (champion plus a diverse archive; drop duplicates and correlated candidates), X5-24, X5-27, X5-54.
- Need: keep the knowledge, drop the version; stop the pool filling with ghosts; let a family that keeps paying earn a looser prior for its children.
- What and how: a demoted unit's rehab children are new candidates (new tries, new wealth) whose plan starts from the family's posterior, with the parent's live record in the prior; the parent stays on paper, journaling. A retired unit stays in the family prior so the family's spread is not biased by survivors. A family whose members keep passing earns a higher starting weight for new children; a family with failures gets a stricter one. Retirement: `ev_rehab_children_max` children failed, or the family's wealth is spent with no refund in sight, or every cell is closed-thin; retirement is final for that version, and a comeback is a new unit with a parent link. The archive keeps family-diverse elites and drops duplicates and correlated candidates before they spend wealth.
- Levels: unit, methodology.
- Per class and style: families are per logic × class, so a logic retired on FX may live on indices with its own prior.
- Ledger: `ev_rehab_children_max`, `ev_parent_prior_weight`, `ev_retire_rule`, `ev_family_prior_spread`.
- Performance: the tenth variation of a paying logic starts warm. Survival: a family that is noise shrinks every child toward zero.
- Evidence chain: A5-098 (author backtest, fund data), WF3 (old spec), EvoQuantLab (author backtest). Weakest link: the lineage credit (X5-54) is wild; a strong family prior can also pull a truly different child toward the family's mean.
- Maturity: plausible; lineage credit wild.

**X5-H28. World switches and contract mechanics: reset on any world change; replay futures, energy and metals at contract level.**
- Components: A2-124 (world-switch reset rule), A5-031 (contract-level replay with explicit rolls), A4-036 (one code path for demo and live), A2-146 (validity stamp), A3-022 (session clock contract, via X4 scenario 38).
- Need: a freshly promoted unit must not trade a demo-sized position live (X4 scenario 38); and a back-adjusted series never counts as P&L.
- What and how: on any world switch (paper to live, PC to VPS, broker to broker): the ladder resets to level 1, house money is zero, brake counters reset, costs are "uncalibrated" until N live fills, the evidence ledger starts a new stage tag, and the e-meter restarts under a paid restart (H17). For futures, energy and metals, the evidence ledger tags contract months; verification and P&L are on individual contracts with explicit roll trades and point-in-time specifications; a back-adjusted series may be used for signals, never for evidence.
- Levels: unit, node.
- Per class and style: energy has inventory-release jumps and negative-price history that the stamp must record; crypto perpetuals switch venues more often than any other class.
- Ledger: `state_carry_rule`, `paper_to_live_carry_rule`, `ev_stage_tag`, `ev_contract_level_replay`.
- Performance: none. Survival: the first live week is a measured ramp; roll artefacts cannot masquerade as edge.
- Evidence chain: A2-124 (idea), A5-031 (idea, assistant), G9 §3.3 (built: one code path). Weakest link: no live binding exists (C-21).
- Maturity: solid.

**X5-H29. Exits and fast invalidation are candidates too: an exit change is a counted trial judged on the same gate.**
- Components: A2-225 (exit change judged as alpha or as risk control), A5-087 (an invalidation rule must beat "no early cut" and "cut one bar later" after costs, and is counted as a trial), A5-045 (exit-model validation before it may close live trades), A2-139 (two-arm, entries-fixed exit test), A2-140 (counterfactual exit replayer with trial counting), X5-32.
- Need: the unit's edge is the edge after its own exits; an exit edit that quietly improves the backtest is an uncounted try (G11: FI never existed in code and trade rows cannot tell an FI cut from a time exit).
- What and how: any change to an exit or FI rule is a new candidate with new wealth. It is judged on two arms with byte-identical entries, risk and data, so the equity difference is the exit and nothing else; it must beat "no early cut" and "cut one bar later" after costs; before it may close live trades it runs shadow (would-have rows) with a false-exit budget. The trade row's `exit_mechanism` (stop, FI cut, breakeven, time, signal, forced flat) is written from the exit block that fired, so verification and brakes can count the same trade by different rules and the ledger records both rules.
- Levels: unit.
- Per class and style: the early-cut level comes from the adverse-excursion distribution of the unit's own winners, per instrument.
- Ledger: `exit_reason_code`, `ev_exit_mechanism`, `effective_tries`, `ev_false_exit_budget`.
- Performance: exits that add are kept; exits that only trade less are found. Survival: an exit rule cannot reach live without shadow evidence.
- Evidence chain: R8 §1 (Kaminski-Lo: stops help only under momentum), A2-139 (controlled, author), A5-087 (idea). Weakest link: FI is not in code, so no FI trial can run yet.
- Maturity: solid as a rule; blocked in the stack.

#### E. Agents: where they help, where they must not decide

**X5-H30. Read-only narrators: an explainer and an incident bundle with evidence ids, never a verdict.**
- Components: A4-135 (read-only explainer agent: narrates incidents, explains a zone change, never trips or clears), A5-049 (incident bundle protocol: a deterministic service detects, the LLM explains measured components with evidence ids), A4-136 (challenger), A5-053 (false-alarm triage ranking), X5-29.
- Need: his two-minute read per unit every time it matters, with no agent in the decision; and triage of the morning list so true alarms are read first.
- What and how: after the nightly job, a deterministic incident bundle is written per zone change (the formula's inputs, the thresholds, the evidence ids of the trades and rows involved). An agent reads the bundle and the journals and writes the explanation ("yellow because cost per trade rose from 0.06R to 0.11R over the last 50 trades; the edge has not moved; the twin's gap is 0.04R, so it is fills, not the market") and a suggested next check. A triage ranker orders the morning list by the chance that an alarm is false, without silencing any critical one. Nothing an agent writes is an input to any formula.
- Levels: unit; system (the job).
- Per class and style: the explainer's templates are per class (funding, rolls, dealer skew).
- Ledger: `ev_explanation_note`, `ev_incident_bundle`, `ev_alarm_triage_rank`.
- Performance: he reads the list, so reviews happen. Survival: none directly; the boundary is the point.
- Evidence chain: A5-049 (idea, from LLM risk-monitoring papers), A5-050 (controlled evaluation design). Weakest link: no measurement yet that explanations change his decisions for the better; A5-050's injected-fault test is how to measure it.
- Maturity: solid.

**X5-H31. Agents as evidence interpreters: typed, expiring, de-risk-only proposals through the slow lane.**
- Components: A4-104 (agents as evidence interpreters: typed, expiring, de-risking-only proposals to a deterministic risk service), A3-113 (slow isolation by proposal card with evidence and a time to live), A5-070 (per-agent evidence contract with expiry and permitted use), C-24 (the slow lane, built), X5-49, X5-50.
- Need: agents can see what the formulas cannot (a broker changed its feed; a session's spread profile moved; twelve units are one bet), and must only ever lower risk.
- What and how: an agent reads journals, node order rows, readings and the passport, and lands a typed proposal card: `step_down(unit, reason, evidence ids, expires)`, `drop_market`, `pool_units(family)`, `isolate(class, ttl)`, `request_control_run`. The service applies only proposals in its allowed set per template; every proposal that would raise risk (step up, widen markets, loosen a threshold) is converted into a request for his click. Proposals expire; the service re-checks the evidence ids at use time.
- Levels: unit, book, portfolio; system (the door, X7's).
- Per class and style: per-class evidence contracts (news, fundamentals, macro, dynamics, synthesis) with permitted use.
- Ledger: `ev_agent_proposal_kinds`, `ev_proposal_ttl_hours`, `decision_freshness_bound`.
- Performance: agents find cost and fill problems in days that P&L would show in months. Survival: no proposal can raise risk; the door is one-way.
- Evidence chain: SwingGuard and FARSIGHT (author backtests; LLM-free loop), C-24 (built). Weakest link: the proposal schema is X7's to design; this file only names the kinds.
- Maturity: solid.

**X5-H32. The protected core: zone, level and plan live in code no agent edit can reach; agents write intent and prose.**
- Components: A4-131 (Steward core: agents write intent only; a protected code core sizes, builds orders and holds the brakes), A1-131 (code-built size as the smaller of agent weight and fixed risk at the stop), A4-132 (governed self-evolution: a reflector proposes, a deterministic gate applies, reversible), A4-017 (deny-list of numbers that may never self-tune), A5-078 (drawdown demotes an agent's autonomy), X5-56.
- Need: the verification state is only worth something if nothing an agent does can move it except through recorded trades.
- What and how: the nightly job, the ladder, the e-meter, the budget and the zone rule run in a core module the unit's slots and the agents' tools cannot write to. The deny-list holds the lifetime budget, the bet grid, the level thresholds, the CUSUM lookback and the ladder's bars: they derive by formula per unit and he may change the formula, but no agent and no self-tuner may. After a red, any auto-applied threshold change (H42) falls back to his confirmation until he resets. Agent-proposed prompt or template changes to the explainer go through a deterministic, reversible gate with replay checks.
- Levels: system.
- Per class and style: the same for all.
- Ledger: `ev_core_deny_list`, `ev_autonomy_fallback_after_red`.
- Performance: none. Survival: the Steward finding: a core no self-edit can reach is what kept the agent's risk rules intact across revisions.
- Evidence chain: 2610.30557 (author backtest with revisions), OtterTune (research system). Weakest link: it collides with the chassis layer's slot contract (C3) and with "whole app unlocked"; it is a boundary, not a lock on him.
- Maturity: solid.

**X5-H33. Decision-process audit and red-teaming of the information path.**
- Components: A5-058 (reported action, submitted order, fill, account state and cited evidence must agree), A4-138 (red-team: fake headlines, prompt injection, stale data, wrong entities), A3-139 (act only after news is public; never test an LLM on news it saw in training), A4-113 (training contamination).
- Need: an agent's explanation or proposal that cites evidence that did not exist at decision time is worse than silence; and the information path into agents is attackable.
- What and how: every agent proposal and every level-1 trade is audited for agreement between the reported action, the submitted order, the fill, the account change and the cited evidence's availability time; disagreement tags the row `audit_fail`, which excludes the trade from proof and lands a review. Quarterly, the information path is red-teamed with fake or conflicting headlines, injected instructions in journal notes, stale boards and wrong-entity matches; the proposals the agents land under attack are scored, and any that would have raised risk is a defect in the door.
- Levels: system, unit.
- Per class and style: entity matching is hardest for crypto tickers and single stocks.
- Ledger: `ev_audit_fail_count`, `ev_red_team_schedule`.
- Performance: none. Survival: closes the path by which a planted note becomes a demotion or a step-up request.
- Evidence chain: AStockArena and measurement-boundary papers (author backtests), fake-news-attack paper (author). Weakest link: a quarterly red-team is a chore nobody has scheduled.
- Maturity: plausible.

**X5-H34. Agents propose families and stake family wealth on their proposals; lineage shown beside every proposal.**
- Components: A4-149, A2-220 (family wealth and agent stakes), A2-195 (Numerai staking), X5-50, X5-53.
- Need: pooling is the biggest calendar win, and a human would not keep forty units' families straight; staking makes the try count cost something.
- What and how: weekly, an agent proposes family membership from claim cards and result-stream correlation; a script confirms by correlation above a threshold; the family is the unit of pooled proof and of wealth. When an agent proposes a unit, it bids a share of the family's wealth as its confidence; a failed unit burns the stake, a proved one refunds with interest; the agent's stake history is shown beside its proposals and feeds the triage ranker (H30).
- Levels: methodology, system.
- Per class and style: families never cross market mechanics (A5-048).
- Ledger: `ev_family_id`, `ev_agent_stake`, `ev_family_alpha_wealth`.
- Performance: families form without his bookkeeping; careless agents run out of stake. Survival: the stake is evidence budget, never money.
- Evidence chain: Numerai (live practice for money stakes), alpha investing (theory). Weakest link: an agent "staking" has no cost to the agent; it only has a cost to its future proposals, which may not shape its behaviour.
- Maturity: wild.
**X5-H35. The governed research pipeline as the B19 upgrade: eight steps from idea to his click, with a frozen referee and an outer loop.**
- Components: A5-155 (workflow: governed research pipeline), A4-130 (a minimal complete research harness in eight steps), A4-119 (a frozen referee decides admission; code grades agents' decisions), A4-115 (an outer diagnostic loop changes the protocol only for the next cycle), A4-118 (frozen experiment contract), A4-145 (the shipped unit-build workflows), A4-142 (the old WF1 and WF2 path), A5-076 (research harness with information, action and commitment boundaries).
- Need: B19 `b-build-and-prove` already goes from a sentence to a paper card; it lacks the counted ledger, the sealed contract, the challenger and the funded gate, and nothing closes the loop on how the pipeline itself performs.
- What and how: B19's steps become: (1) register the hypothesis with a novelty check (H01); (2) freeze the experiment contract (H02); (3) build through typed tools; (4) run the proof battery on excess returns (H03); (5) the frozen referee (B13's judge, sealed, seeing only post-registration returns) writes the verdict, the band (H04), the counts (H05) and the plan (H06); (6) the challenger writes its note and commissions the nulls (H07, H08); (7) the paper card, with wealth assigned (H12); (8) the packet for his click (H10, H11). An outer loop, monthly, reads the gate scorecards (H20) and may change the protocol for the next cycle only, never rescoring finished candidates. Agents' decisions inside the loop are graded by code (did the challenger's predicted failure happen?).
- Levels: system.
- Per class and style: class-aware contract and pre-queue checks.
- Ledger: `ev_pipeline_version`, `ev_protocol_change_log`.
- Performance: the path agents already walk, made honest; frozen referees admitted 5 to 11 times fewer sub-threshold factors than leaky ones. Survival: the outer loop cannot rescue a finished candidate, so there is no quiet re-grading.
- Evidence chain: QuantHarness (author benchmark), "Propose, Don't Judge" (author backtest, scripted referee), B19 (built). Weakest link: B19's builder prompt says nothing about sizing or costs (G8 §4.2).
- Maturity: solid.

**X5-H36. Versions compete fairly: a new version runs beside the incumbent under a conservative floor, judged by the contrast.**
- Components: A5-037 (conservative UCB live gate: try the new unit or size only while a cumulative floor against the incumbent holds), A5-038 (contrast certificate: bound candidate-minus-incumbent directly), A4-025 (fresh baseline at the same time), A4-023 (rollout steps with pass, fail, inconclusive), X5-15.
- Need: an edit restarts the record (X5-15), which is right for proof but slow for improvement; a new version should be able to prove it beats the old one without proving the whole edge again.
- What and how: a new version of a live unit runs at level 1 beside the incumbent (paper twin or live canary, H46) started at the same minute. Its result may continue only while its cumulative R stays above a chosen fraction of the incumbent's; the contrast (new minus old) is bounded directly, with a prefix refresh when the incumbent itself changes, so shared market noise is not charged twice. The rollout analysis ends pass (replace at the next session), fail (retire the version), or inconclusive (pause for his look).
- Levels: unit.
- Per class and style: the contrast is in R; the canary subset of markets per class.
- Ledger: `ev_version_floor_fraction`, `ev_contrast_bound`, `ev_rollout_outcome`.
- Performance: improvements ship in weeks on the contrast instead of months on the full proof. Survival: the floor stops a worse version from running long.
- Evidence chain: A5-037, A5-038 (simulation, bandit papers), Argo (production software). Weakest link: two versions trading the same markets on one account may net or collide; the node refuses a second deployment of one unit today (G9 §3.2).
- Maturity: plausible.

#### F. Records, costs, screen, template

**X5-H37. The evidence ledger: stage tags, two records (logic in R, money per profile version), and would-have rows.**
- Components: A2-219 (evidence ledger with stage tags; frozen baseline; an edit restarts the record), A4-042 (two records per unit: logic in R across versions, money per profile version), A2-145 (would-have rows, shadow-first), A2-240 (live MAE, MFE and R journal per trade), G9 §7.1 (the Library `trade` kind has the fields; the journal rows do not), X5-08, X5-32, X5-42.
- Need: one place that says what the unit did, when, under which rules; the judge works in R so a sizer change cannot change a verdict, and the money record must still be judged somewhere.
- What and how: every trade a unit ever made sits in one append-only journal with a stage tag (backtest, holdout, event replay, paper, live-L1, live-L2, ...), a world, a contract month where relevant, `exit_mechanism`, costs in R complete (spread, commission, swap, funding, slippage), MAE and MFE in R, replay match, audit flag, and a `counts_toward_proof` flag (paper and later stages only). The logic record in R runs across profile versions; a new sizer or risk profile starts a new money record and leaves the R record alone. Would-have rows are written while stopped, isolated, benched or demoted, and while a new brake runs shadow. The journal rows at `journal.py:397-418` are extended to fill the Library `trade` schema that already has `session`, `streak`, `equity_before`, `costs` and `mae_r`.
- Levels: unit; system (the Library).
- Per class and style: contract month and roll flags for futures, energy and metals; funding rows for crypto; corporate-action flags for stocks.
- Ledger: `ev_stage_tag`, `ev_counts_toward_proof`, `ev_exit_mechanism`, `ev_would_have_row`, `ev_costs_in_r_complete`, `ev_money_record_version`.
- Performance: none. Survival: stops the oldest cheat (re-counting the backtest) and the newest (a sizer edit that re-judges the logic).
- Evidence chain: G9 §7.1 (built schema, unfilled rows), R26 §6 (old spec). Weakest link: a unit-path change in the builders' lane.
- Maturity: solid.

**X5-H38. One cost ledger from backtest to live, reconciled to zero; live costs refresh the calibration and re-cut the band.**
- Components: A1-146 (one cost ledger with a cost-stress grid), A5-157 (workflow: shared cost ledger with per-fill markouts and conditional passive-fill odds), A4-168 (one execution convention, reconciled; the risk model checked daily against realised results), A1-141 and A2-224 (cost cushion and retention), A1-138 (edge-to-cost gate), G9 §3.4 (slippage data in node order rows, unused), X5-14, X5-49.
- Need: costs must reach the sizer and the plan (STATE item 38, "facts that hold everywhere"); paper has zero slippage and QMB's costs are uncalibrated (G9 §5), so no verification of a scalper is honest until this exists.
- What and how: one convention for backtest, replay, paper and live: signal at bar close, fill from the next quote, net R = raw − spread − commission − slippage − swap or funding. A script over node `order` rows (asked versus filled) and reconcile rows writes per-instrument, per-hour cost and slippage profiles with markouts; the paper lane draws its slippage from them instead of zero; QMB's cost calibration artifact is refreshed from the same rows; the band's low end is re-cut after measured costs (`ev_edge_band_low_after_live_costs = low − (live cost − card cost)`), and a unit whose re-cut low end is below zero is red whatever its backtest. The cost cushion (net profit ÷ total assumed cost) and retention are on the card. The ledger reconciles paper, live and backtest to zero difference on the same trades, and the difference is itself a monitored number.
- Levels: trade (rows), unit (profiles), node (the script).
- Per class and style: FX dealer skew after fills; crypto maker fills adversely selected (R6 §T-02), so passive-fill odds are conditional, not fixed; futures tick rounding; stocks borrow; energy roll costs. Scalpers: cost is the master state; swing: swap and funding dominate.
- Ledger: `round_trip_cost_r`, `spread_cost`, `commission_cost`, `slippage_cost`, `swap_financing_cost`, `funding_cost`, `unit_cost_target`, `ev_edge_band_low_after_live_costs`, `ev_cost_profile_source`, `ev_cost_reconciliation_gap_r`.
- Performance: a scalper that clears its true costs is sized on a true band; one that does not is found in fifty trades. Survival: the edge-smaller-than-cost case is the most common scalper death and the cheapest to detect.
- Evidence chain: AutoQuant 2512.22476 (author backtest, one ledger), market maker's dilemma 2502.18625 (live), G9 §3.4 (data exists). Weakest link: no commission key on the instrument record (G9 missing 13).
- Maturity: solid.

**X5-H39. The passport is the screen: every verification number with its band, the zone, the ladder, the looks, the explanation.**
- Components: A2-198 and A4-165 (verification passport; the state on screen), A2-171 (rolling Sharpe with significance bands; uncertainty bands on every live number), A4-159 (three-zone state), A4-069 (a settings schema generates the form and the ledger generates the risk UI), X5-33, X5-34.
- Need: his M12 ask ("wrong, right, working, up, on, trading"); "right or wrong" for the edge has no state word today (G11 §4.3).
- What and how: one frozen passport per unit version (claim card, verdict, band with its four low ends, counts, plan, challenge note, wealth, looks taken and their results, zone history, levels and cohorts, demotions with causes, rehab links, audit flags). The unit card shows: the zone colour and the state word (proving, proved at level n, pending, closed-thin, demoted, retired); "trades toward proof 212 of 610, next look at 400"; the evidence meter against the level's bar; the inputs strip (cost, slippage, rate, holding time, replay match, twin gap), each green or amber against the card; the level with its cohort count and the ceiling; the family's state beside the unit's (so family green is never read as unit green, C7); the last explanation with its evidence ids; every number with its uncertainty band. The node and home pages group units by zone; "Needs you" lists reds, ready-for-card units, expiring approvals and inconclusive rollouts. Both dollars and R. The passport's schema generates the card, so a new gate or a new template field appears without UI work.
- Levels: unit, node, portfolio (the home page).
- Per class and style: class-specific inputs strips (funding, roll, borrow).
- Ledger: `ev_passport`, `ev_trades_toward_proof`, `ev_next_look_at`, `ev_state_word`, `drift_state`, `ev_evidence_e`.
- Performance: he clicks on evidence, not on feel. Survival: an expiring approval and an inconclusive rollout are visible, not silent.
- Evidence chain: SR 26-2 inventory (regulatory), the unit plan's UI notes (design), A2-171 (mechanism). Weakest link: the node emits no verification state today (G11 §4.3); X6 owns the screen and must take this list.
- Maturity: solid.

**X5-H40. A verification template per unit type, as data, with class notes; the applier mode per number.**
- Components: A2-228 (verification template per type), A4-001 and A4-002 (VPA learner with bounds; applier with owner-chosen modes off/shadow, at start, live), A4-023 (reusable analysis templates), A4-069 (a settings schema generates the form), X5-46.
- Need: one template per unit type is his ruling (A5); trade rates differ by an order of magnitude between types; and the self-configuring model is Kubernetes plus the VPA (STATE item 31).
- What and how: the template is a typed document per type (scalper, intraday, ORB, swing) carrying every `ev_` default with its derivation and its applier mode. Scalper: trade-count looks, cohorts of 25, CUSUM per instrument, pooled by session, machine check at 50 trades. ORB: calendar looks with alpha spending, pooled across session opens and markets, cohorts of 10, machine check at 7 days. Intraday: cohorts of 15, looks at 100 trades. Swing: family-only proof, calendar looks, cohorts of 5, machine check at 30 days. The nightly job is the learner: it publishes each unit's zone, level and the bounds of every self-calibrated threshold (H42); the applier mode per number decides whether the published value is shown only, applied at the next session, or live. Every default has a class note (what changes for crypto, futures, stocks) and he can change how it derives.
- Levels: unit (the document), system (the templates).
- Per class and style: the class notes are the point.
- Ledger: `ev_verification_template`, `ev_applier_mode`, `number_motion_mode`.
- Performance: a scalper is not judged on an ORB's clock. Survival: shadow mode for every new rule before it may act.
- Evidence chain: VPA (production software, CHECKED), his A5 ruling (his words). Weakest link: QMX has the learner and no applier (STATE item 31).
- Maturity: solid.

**X5-H41. The node emits verification state; zone and level are inputs to the host guard, the halt slot and the sizer.**
- Components: X5-56, A4-091 (one guard module on the host: unit, book and account scope; before_order can pass, shrink or refuse), A4-098 (the ledger frozen into the compiled unit, with affects edges executed at run time), A4-171 (modes read as a fold over a transition stream), G11 §4.3 (the node must emit risk state, not only health).
- Need: otherwise the verification is a report nobody acts on, which is G9's finding for every drift piece today.
- What and how: the nightly job writes `verification.zone`, `verification.level`, `verification.state_word` and `verification.next_look_at` per deployment into a host-side input. The host guard reads them before every order: red refuses new entries (never exits); orange shrinks to the level's size; the sizer reads the level and the risk share (X5-30) and nothing else from this file. Every transition is journalled as a row, and the current state is a fold over the transition stream, so a restart recovers it. The watcher (B21) and the phone wake read the same rows.
- Levels: node, unit.
- Per class and style: the same for all.
- Ledger: `drift_state`, `size_levels`, `brake_state`, `ev_state_word`.
- Performance: a green unit's step up is applied, not only proposed. Survival: a red unit cannot open a position because of a stale card.
- Evidence chain: G8 §2.4 (the sizer's inputs), G9 §7.3, G11 §4.3. Weakest link: a slot-contract change the chassis layer owns (C3).
- Maturity: solid.

**X5-H42. Every slow-lane threshold calibrated by simulation on the unit's own record, published with bounds, and re-checked against the pipeline test.**
- Components: A2-227 (thresholds calibrated by block bootstrap on the holdout), A5-034 (pipeline test), A4-001 (learner publishes target with low and high bounds), A4-017 (deny-list), X5-36.
- Need: every number needs a derivation, and he can change how it derives (STATE item 37); constants like 19.5 or 11.8% are placeholders until the unit's own record says otherwise.
- What and how: before paper, the plan simulates its own looks, cohorts, CUSUM, e-meter and ladder on 1,000 block-bootstrapped holdout paths (block of 5) and reports the false-alarm rate and power of every rule for this unit; any rule whose simulated false-alarm rate exceeds its budget is loosened by formula, the change logged, and the published value carries low and high bounds. The pipeline test (H20) checks the calibration on nulls and injected edges. The thresholds are on the deny-list for self-tuning: they derive by formula, and only he changes the formula.
- Levels: unit.
- Per class and style: block length per class (crypto blocks span weekends; FX blocks are sessions).
- Ledger: `ev_sim_false_alarm`, `ev_sim_power`, `ev_sim_paths`, `ev_sim_block`, `ev_threshold_bounds`.
- Performance: a unit with a smooth record gets tighter rules and climbs faster. Survival: a unit with streaky results gets looser rules, so it is not demoted on its own normal streaks.
- Evidence chain: R08 T5 block bootstrap (old spec), R3 §6 model limits. Weakest link: a bootstrap of the holdout cannot see regimes the holdout did not contain.
- Maturity: plausible.

**X5-H43. Rare traders: calendar looks with alpha spending, pooled across session opens and markets, with the session clock contract.**
- Components: A2-185 (Lan-DeMets alpha spending for calendar-timed looks), A2-188 (pooled proof), A3-022 (session clock contract: broker time zone, DST, the market's own zone), A3-033 (a sniping window as a measured slice proven out of sample, counted as a try), X5-44, X5-11.
- Need: an ORB unit once per session per market waits years for 200-trade looks; his "ORB gets frequency through breadth" (SEEDS, 1 Nov).
- What and how: for units with few trades a day, looks happen at calendar times with the false-alarm budget spent by the information fraction (trades so far ÷ planned trades). The ORB logic is one family across session opens (Tokyo, London, New York) and markets, pooled on a daily clock with the event window (H06) so one risk-off open counts once. Session windows are written in the market's own zone, with a DST self-check. A "sniping window" claim is a measured slice of the record (hour × instrument) proven out of sample and counted as a try, never a label.
- Levels: unit, methodology.
- Per class and style: index opens are correlated on risk-off days (prior ρ 0.5); FX opens by region less so (0.2); crypto has no opens, so an ORB on crypto uses funding-hour windows.
- Ledger: `ev_alpha_spending_rule`, `ev_look_schedule`, `ev_family_id`, `premium_window_flag`, `session_windows`.
- Performance: the ORB family proves itself in weeks instead of years. Survival: the event window stops one shared open from proving the logic.
- Evidence chain: FDA on Lan-DeMets (regulatory), R2 §4.2 (N_eff), A3-033 (idea). Weakest link: the opens' correlation on risk-off days is a prior until measured.
- Maturity: plausible.

**X5-H44. The edge decides the gate and the level; the risk share decides the amount; the soft multiplier stays off.**
- Components: A1-031 (edge as a gate, risk share as the amount), A1-021 (lower-confidence-bound Kelly, for the gate only), A1-019 (shrunk Kelly by the t-statistic, off by default), A1-095 (inverse volatility default), A1-103 and A2-192 (performance-chasing allocation warned against), X5-30, X5-31.
- Need: his two rules at once: do not lean on the edge for the amount (A24), never size a thing with no evidence (D18); and the lead's "twice the edge, twice the size" he rejected.
- What and how: the verification state decides whether a unit trades and at which level (H13, H14); the amount at a level comes from the risk share the sizing layer (X2) gives it, by inverse volatility or a budgeted share, never from the edge number. Only the low end of the band enters, and only as "positive with evidence at this level" or not. The soft multiplier t² ÷ (1 + t²) exists as a template dial for operators who want some lean, off by default; at 300 trades of +0.05R it is 0.43, at 3,000 it is 0.88. Adaptive allocation to the winning unit is warned against in the template's notes with the trial result (more patients on the worse arm, overstated effect).
- Levels: unit (gate, level), book and portfolio (amount).
- Per class and style: the same.
- Ledger: `edge_range`, `size_levels`, `unit_capital_share`, `risk_fraction`, `edge_t_statistic`, `kelly_shrink_factor`, `ev_gate_requires_low_end_positive`, `ev_evidence_multiplier_enabled`.
- Performance: a weak uncorrelated edge gets its full risk share at its level; a strong one climbs levels. Survival: a wrong point estimate cannot size a unit.
- Evidence chain: R2 §4.4 (desk practice), R3 §2.3 (adaptive allocation trial results), A1-021 (arithmetic). Weakest link: C5, four positions on one dial, is not resolved here.
- Maturity: solid.

**X5-H45. Certified capacity: one planned interim review, and the plan prices what the edge is worth after proof.**
- Components: A2-210 (certified alpha capacity: plan interim reviews, price decay while proving), A2-184 (one interim look with an O'Brien-Fleming bound cuts expected sample size about 15%), R6-T08 "one interim decision keeps far more value than one fixed date".
- Need: a plan that proves an edge after it has decayed proves nothing worth money; and too many looks spend the budget.
- What and how: the plan carries a capacity estimate: expected value left when evidence finally allows the next level, under the family's measured decay rate (from retired members' records). A plan whose capacity at proof is below the level's minimum worthwhile return is marked "proved too late" and the unit is pooled or closed-thin. The default look schedule has one planned interim review plus the final, with the e-meter for display; more looks are a template choice with their cost shown.
- Levels: unit, methodology.
- Per class and style: crypto and single-stock edges decay fastest; swing edges slowest.
- Ledger: `ev_capacity_note`, `ev_family_decay_rate`, `ev_look_schedule`.
- Performance: budget goes to edges that are still alive when proved. Survival: none directly.
- Evidence chain: 2610.01115 (simulation; Gaussian drift), FDA guidance. Weakest link: the family decay rate needs retired members to measure.
- Maturity: plausible.

**X5-H46. Live canary across markets: promote a subset, keep the rest as control, widen on green, with declared promote and rollback times.**
- Components: A4-026 (partial, time-limited canary with split metrics; live canary across markets), A2-199 (canary against a fresh baseline), A2-200 and A4-023 (rollout steps with pass, fail, inconclusive; declared promote and rollback times), A4-024 (declared promote and rollback times; no judging while another loop moves the version), X5-55.
- Need: limit money at risk while proof runs on a multi-market unit; the node today refuses a second market per deployment (G9 §3.2).
- What and how: his click (H10) approves a market list and a canary subset. The canary markets trade live at level 1; the control markets stay paper with the same signals. Metrics are split by canary and control (a 5% canary failing badly shows as 1% in a whole-unit view). The rollout has steps (widen to the next subset, pause, analyse) with a declared promote time and rollback time; analysis ends pass, fail or inconclusive; no analysis runs while a version change is in flight. Widening is a step up in scope, which under R9 is an accelerator and needs the permit (H25).
- Levels: unit, node.
- Per class and style: the canary subset is one market per class where the unit claims several classes, so a class-wide fault shows in its own control.
- Ledger: `ev_canary_share`, `ev_rollout_promote_time`, `ev_rollout_rollback_time`, `ev_rollout_outcome`.
- Performance: a multi-market unit reaches its breadth in planned steps instead of one click. Survival: a market-specific fault is caught against its own control.
- Evidence chain: Google SRE (production practice), Argo and Flagger (production software). Weakest link: the one-market refusal in `promote.py` and the absent live binding.
- Maturity: plausible.

**X5-H47. The sniping window is a measured slice, proven out of sample, counted as a try, and never a label.**
- Components: A3-033, A2-136 (fixed-count placebo for filters), A5-014 (a filter judged by a pre-registered walk-forward that reports time out and rebound missed), A2-189 (per-cell verification), `premium_window_flag`.
- Need: his research ask (SEEDS, 3 Nov) and the lead's finding that "sniping window" is retail jargon; the honest version is a slice of the record where edge after costs is higher.
- What and how: a window claim (hour × instrument × session) is a cell (H23); it is tested as a filter: the unit with the window against the unit without, on pre-registered walk-forward periods, reporting time out of the market and rebound missed, and against placebo selections of the same count. Each window tried is a counted try. A proven window raises the cell's estimate; an unproven one stays a reading.
- Levels: unit (cell).
- Per class and style: session opens for FX and indices; funding hours for crypto; inventory-release hours for energy.
- Ledger: `premium_window_flag`, `ev_cell_key`, `effective_tries`.
- Performance: a real premium hour is found and used. Survival: a lucky hour is not.
- Evidence chain: A5-014 (author backtest), A2-136 (placebo selection, controlled). Weakest link: multiple windows tried per unit inflate the count quickly.
- Maturity: plausible.

**X5-H48. A ring-fenced exploration budget for level 1, and admission to the book by marginal effect.**
- Components: A5-026 (ring-fenced exploration budget), A5-005 (marginal effect on the book), A2-029 (budget policy), X5-30.
- Need: many level-1 units are many small bets on unproved claims; the sum must be bounded apart from the book's capacity, and each must earn its place by what it does to the book.
- What and how: all level-1 (proof-pending) units share one explicit exploration risk budget kept apart from the live book's capacity; a failed exploration costs only that budget. A unit leaves the exploration budget for the book's budget only when it is proved at level 2 and its marginal effect on the book (H11) is positive. The BMS sees the exploration budget as one line.
- Levels: portfolio.
- Per class and style: the exploration budget is split by class cap so one class cannot fill it.
- Ledger: `ev_exploration_budget_share`, `unit_capital_share`, `portfolio_seed_capital`.
- Performance: exploration is always on, bounded, and never starves the proved book. Survival: the sum of unproved bets has a hard line.
- Evidence chain: A5-026 (idea, bandits), A5-005 (author backtest). Weakest link: on $500 the exploration line may be below one minimum lot (Q5).
- Maturity: plausible.

---
## 4. Problems and solutions

CIS problem-solving pass on every open problem in this layer. Each has at least two options and their trade-offs. Options are not picks.

**P1. A bad day cannot be told from a broken edge quickly.**
- A: three speeds with one evidence currency (H15): inputs in days, warnings in weeks, confirmation in hundreds of trades; the money brake apart. Pro: each clock answers one question; nothing in the slow lane acts on a day. Con: three numbers to explain; the minimum viable edge m must be set.
- B: planned looks with non-binding futility only (X5-04, X5-18). Pro: known error rates. Con: undecided at 1,000 trades in 46% of half-edge plans (R3 §2.2).
- C: a plain-words "bad day" definition from the card (X5-48, H18) with no action. Pro: removes the question for most mornings. Con: answers the feeling, not the decision.
- D: the e-meter alone as decider (X5-05). Pro: one number. Con: less power than looks; needs an alternative or bounded bets.

**P2. "Half the edge" versus "paper is demo trading".**
- A: four shrinkages, lowest computable low end, printed with inputs (H04). Pro: the unit's own number; he can change how it derives. Con: a first child of a new logic gets only two of the four.
- B: a flat discount as a template default with its published reason (26-58%). Pro: always computable. Con: looks arbitrary, and is.
- Both: demo trades count fully; the discount is backtest-to-reality, never demo-to-live; the demo-to-live gap is costs and fills, measured by the twin (H09, H38).

**P3. Seven days of paper versus 600 trades of proof.**
- A: two clocks plus proof at level 1 with risk-tiered thresholds (H09, H13). Pro: paper is short and honest; real fills feed the proof; money grows only with evidence. Con: he clicks live before proof is complete (Q1).
- B: pooled family proof in paper, placement continues live (H23). Pro: no live money before the logic is proved. Con: needs several units of one logic at once; correlation and the event window stretch it.
- C: longer paper for thin edges only, by plan (H06). Pro: no money at risk. Con: months for a thin scalper.

**P4. Daily peeking inflates false passes.**
- A: the e-meter on screen every day, planned looks for decisions (H15, H39). Pro: looking is harmless. Con: two numbers to explain.
- B: planned looks only; the screen shows "next look at N". Pro: clean. Con: he will look anyway.
- C: Promote's funded wealth is itself anytime-valid (H12), so one number serves both. Pro: one number, proven null rate. Con: a weak edge waits longer than under looks.

**P5. Which trades count: FI cuts, breakevens, forced flats, would-have rows.**
- A: every closed trade counts by its R, whatever the mechanism; the mechanism is a field for brakes and diagnosis (H37). Pro: one rule; the edge is the edge after the unit's own exits. Con: a unit with many 0R breakevens shows a smaller edge and needs more trades; true, not a flaw.
- B: exclude forced flats (kill, isolation) and count would-have rows for rate and replay only (H21). Pro: outside events do not read as decay. Con: a unit often flattened has a thinner record.
- C: the observation unit is a completed campaign or risk block, not a trade (H05). Pro: honest for units that add to positions. Con: fewer observations; proof slower.

**P6. He wants weak edges to pay; weak edges are the hardest to prove.**
- A: "too thin" closes the claim; breadth and pooling reopen it (H06, H23). Pro: honest; frequency is the lever he already believes in. Con: a weak rare edge never gets money.
- B: level 1 indefinitely under the exploration budget, with a positive low end required and no step up until the level-2 bar (H13, H48). Pro: "squeeze some money" while proof accumulates, bounded. Con: level 1 on $500 may be below the minimum lot (Q5).
- C: the soft multiplier (H44). Pro: a dial with a formula. Con: leans on the edge, against A24.

**P7. QMB's outputs never reach the sizer or the node.**
- A: the nightly job writes zone and level into a host-side input the guard and slots read (H41). Pro: one input; the chassis stays. Con: a slot-contract change the chassis layer owns.
- B: the node reads the passport from the Library at deployment and nightly (H39). Pro: no slot change. Con: a Library read on the money path; stale between jobs.

**P8. Costs are uncalibrated, commission is outside R, paper has zero slippage.**
- A: one cost ledger from node rows; paper draws slippage from it; live re-cuts the band (H38). Pro: real numbers; closes the gap from the live side. Con: needs a commission key and the live binding.
- B: refuse to claim "verified" for any scalper until measured costs exist; verify only "machine works" and "inputs match". Pro: honest. Con: delays everything on $500.
- C: a prior cost profile per instrument class from the research tables (R6 §T-02 class costs) until measured. Pro: available day one. Con: a guess with a label.

**P9. Agents iterate; tries get undercounted.**
- A: the search ledger with failures plus stream clustering at QMB's door (H01). Pro: counts every edit the same. Con: needs result streams on a shared clock.
- B: pre-registration weights (H01). Pro: rewards the habit. Con: timestamps can be gamed by a careless agent.
- C: staking (H34). Pro: makes it cost something. Con: wild.

**P10. Correlated units overstate pooled proof and breadth.**
- A: measured ρ and N_eff in the plan plus an event window (H06). Pro: cheap; the window is model-free. Con: ρ needs weeks of paper.
- B: a prior ρ by shared driver until measured (H06's table). Pro: day one. Con: a guess with a label.
- C: family-stream detection on top (H23). Pro: catches the shared fade. Con: another detector in the alarm budget.

**P11. Who acts on a verdict.**
- A: scripts step down and demote to paper at planned looks or on confirmation; step-ups and live need his click (H24, H26). Pro: brakes-first; no human in the loop for safety. Con: he has not ruled on automatic demotion (Q2).
- B: everything is a card. Pro: his control. Con: a red at 02:00 waits for morning.
- C: scripts act within the template's allowed moves (down, paper); automatic step-ups only while the family permit is healthy (H25); cards for the rest, override logged. Pro: the clinical shape with a budget. Con: the template must say what is allowed per type.

**P12. Rare traders wait years for trade-count looks.**
- A: calendar looks with alpha spending (H43). Pro: correct error rates. Con: more maths to explain.
- B: pooled across session opens and markets with the event window (H43). Pro: his "ORB gets frequency through breadth". Con: opens correlate on risk-off days.

**P13. How the band feeds size.**
- A: gate only (H44). Pro: does not lean on the edge. Con: a unit with twice the evidence gets the same amount at the same level.
- B: gate plus the soft multiplier (H44, off by default). Pro: size grows with proof. Con: leans on the edge.
- C: the level is the only thing the edge touches; the amount per level is X2's (H13). Pro: one mechanism, readable. Con: steps are coarse.

**P14. Re-promotion after demotion.**
- A: funded episode with a halving budget plus minimum days (H26). Pro: evidence-based; episodes are paid for. Con: a thin edge takes months to come back.
- B: rehab child through the full path with the family prior (H27). Pro: a fresh counted try. Con: the parent's paper trades are wasted unless pooled.

**P15. The verification needs fields the stack does not write.**
- A: fill the Library `trade` schema from the journal rows (H37). Pro: the schema exists. Con: a unit-path change in the builders' lane.
- B: derive what can be derived (streak, equity before) in the nightly job and add only `exit_mechanism`, `stage` and costs at the source. Pro: smaller change. Con: two homes for one fact.

**P16. Many units, many alarms; he stops reading.**
- A: one lifetime budget held at the BMS with e-BH and e-Bonferroni (H16). Pro: the only honest way to watch many units. Con: no holder exists; the BMS is ideas only.
- B: per-unit thresholds with a triage ranker (H30). Pro: no new holder. Con: FDR and FWER near one in long runs (R6-T08).

**P17. The gates themselves are unproven.**
- A: monthly scorecards plus a quarterly pipeline test on nulls and injected edges (H20). Pro: QMX measures its own rates. Con: injected edges on real tapes need the simulation bench (X4).
- B: every new gate runs shadow-first with would-have rows before it may act (H21). Pro: cheap; no bench. Con: measures precision, not power.

**P18. Agents could move the state.**
- A: the protected core with a deny-list (H32). Pro: Steward's finding. Con: a chassis boundary.
- B: audit every proposal and trade for agreement with evidence (H33). Pro: catches what the core cannot. Con: after the fact.

**P19. Versions and improvement are slow under "an edit restarts the record".**
- A: contrast testing against the incumbent under a conservative floor (H36). Pro: weeks, not months. Con: two versions on one account may collide.
- B: keep the restart rule and pool the old version's trades through the family prior (H27). Pro: simple. Con: slow.

**P20. The minimum viable edge m is unset.**
- A: m = stressed round-trip cost × a cushion factor from the template (the retention score, H38). Pro: derived from costs. Con: the factor is a template number.
- B: m from his minimum worthwhile return per unit (Q6) divided by the trade rate. Pro: his number. Con: a numbers-lens question, later.

---

## 5. Collisions

Named, not resolved.

- **C1. Planned looks (X5-04) versus the e-meter (X5-05) versus Promote's wealth (H12) as the deciding rule.** Three valid deciders; H15 makes the looks a verified fallback and the wealth the promotion gate, which is a pick the funnel must confirm or undo.
- **C2. "Proof continues at level 1 live" (H13) versus "QMB proves before demo" and "only he promotes" (D18, D19).** He clicks a unit live before its edge is proved. Either he accepts "live at minimum size, proof pending", or proof finishes in paper, which collides with "7 days doable".
- **C3. Zone and level as host inputs (H41) and the protected core (H32) versus X1's slot contract.** The sizer gets four inputs today; adding verification inputs and a core module is a contract change X1 owns.
- **C4. Size levels (H13, H14) versus X2's amount.** If X2 sizes continuously (a Kelly fraction with shrinkage), levels are a second mechanism; if X2 sizes by risk share, levels are the mechanism. The two layers must share `size_levels`.
- **C5. The edge as a gate (H44) versus the soft multiplier versus A24 versus "twice the edge, twice the size".** Four positions on one dial.
- **C6. Brake-fire density (H19) versus X3's redesign of count brakes.** If count brakes become money or drawdown brakes, the expected fire rate changes meaning; H19 needs X3's counting rule.
- **C7. Pooled proof (H23) versus "each unit stands alone".** Family green is not unit green; the screen must show both (H39).
- **C8. Family wealth and the burn permit (H12, H25) versus "the sky's the limit" for agent proposals (D42).** A spent family blocks new births.
- **C9. Automatic demotion by script (H26) versus "you can't simply pull out" (A25).** Confirmation at e ≥ 400 is not one bad day, but he has only ruled on the day case (Q2).
- **C10. Would-have rows during isolation (H21) versus X3's isolation protocol.** Which host computes the would-have signals while a class is off is unassigned.
- **C11. The shipped decay check (20 trades, tighten-only cards) versus everything in section C.** It is replaced (section 6).
- **C12. "Every closed trade counts by its R" (P5 A) versus X3 counting FI cuts by size or not at all.** Verification and brakes count the same trade differently; the ledger records both (H37).
- **C13. Floor odds for many units (STATE item 10) versus N_eff for proof (H06).** Both layers must use the same ρ; X4's scenarios and this plan must share `unit_result_correlation`.
- **C14. Calendar-timed looks (H43) versus "days matter for paper, but trades count".** Lan-DeMets uses days to schedule and trades to decide.
- **C15. The three-speed monitor (H15) versus X3's "three speeds of brake" (A2-079).** Same shape, two owners: X3 owns speed 1's money rules; this file owns speeds 2 and 3; the boundary at "a warning steps down one level" is shared.
- **C16. Promote's "any change is a new candidate" (H12) versus calibrated numbers that move inside a range (the unit build's motion rows).** A calibration move is not a new candidate under the identity table (A4-041); a block swap is. The table must say which numbers' motion is "none".
- **C17. The paper twin and control twin (H21) versus the node's paper load and X6's observability budget.** Three lanes per unit.
- **C18. H32's deny-list versus "whole app unlocked" (memory: nothing is legacy, any lock is temporary).** The deny-list locks self-tuners and agents, not him; it must be stated that way or it reads as a lock.
- **C19. Excess-return gates (H03) versus the unit's own R convention.** R is per trade after spread; an excess return needs a class benchmark over the holding time, which QMB does not compute.
- **C20. X4's scenario 38 (world switch) and this file's H28** both specify the reset; one owner is needed.
- **C21. H11's marginal-effect veto versus D19 ("picking which units to promote is not this session's").** The portfolio veto is a BMS decision input, not a pick; the funnel must say whether it belongs to the numbers lens.

---

## 6. Restructure proposals

Where this layer suggests replacing a level, a stack component or the Book/BMS shape, with what replaces it and why it performs better.

1. **Replace `dc-decay-and-limit-report` (B20) with the nightly verification job (H15, H24, H41).** The shipped job compares the last 20 trades with the unit's own record, cannot read the baseline card, and lands tighten-only cards nothing applies. The replacement reads the card, runs three speeds with a known false-alarm rate per unit, writes a zone and a level the host applies, and keeps the agent pass. Performs better: a healthy unit is demoted by statistics in 0% of 4,000 trades instead of being flagged by a 20-trade comparison on noise; a dead unit is stepped down in a median 190 trades.
2. **Replace the paper judge's "ready at 30 trades and 28 days" with the two clocks and risk-tiered thresholds (H09, H13).** The machine check closes in 7 days or 50 trades; the edge clock runs into live with a rising bar. Performs better: paper is short and honest; money grows with evidence, not with a calendar.
3. **Replace the paper lane's zero slippage with a slippage model drawn from node order rows (H38).** Performs better: the twin gap and the cost strip mean something before the live binding exists.
4. **Replace the promotion endpoint's one-shot click with a bound, expiring packet and a canary market list (H10, H46).** Performs better: closes agent self-promotion; lets a multi-market unit go live in steps.
5. **Add a verification core module to the unit host (H32, H41)** beside the guard: zone, level, plan and budget in code no slot or tool writes to. Performs better: the state cannot be moved except by recorded trades.
6. **Book/BMS shape: the family is the Book's verification unit; the BMS holds the alarm budget and the exploration budget (H16, H25, H48).** Today a Book is a cluster by style. Under this layer a Book's members share a logic family's proof, a family wealth, a pooled decay stream and a burn permit; the BMS holds one lifetime false-demotion budget and one exploration line across Books. Performs better: proof arrives by breadth inside a Book; false alarms and unproved bets are bounded at the top instead of per unit. [judgment] This is a reshaping of what a Book is for, not a replacement of the levels.
7. **B19 `b-build-and-prove` becomes the governed pipeline (H35)** with a counted ledger, a sealed contract, a frozen referee, a challenger and a funded gate. Performs better: 5 to 11 times fewer sub-threshold admissions in the paper that tested frozen referees.
8. **Trade rows carry what the Library schema already has (H37):** session, streak, equity before, costs complete, exit mechanism, stage, audit flag, would-have. Performs better: every gate in this file becomes computable.

---

## 7. Gaps

What no component covers.

1. A commission key on the instrument record and a writer of cost profiles (G9 missing 13); without it no R is complete and no band is honest for scalpers.
2. A paper lane that models slippage; every component assumes paper has costs.
3. The node emitting verification state (G11 §4.3); every screen component assumes it exists.
4. Fast invalidation in code (G11); H29's FI trials cannot run.
5. A holder for the lifetime alarm budget and the exploration budget; the BMS layer is ideas only.
6. Per-class trade-rate and correlation priors for the plan; the ρ table in H06 is mine.
7. The observation unit for a retail scalper (campaign or trade); a convention with no source.
8. The minimum viable edge m per unit; no source sets it for retail.
9. A pinned-version replication job for headline results (H02); no QMX piece does it.
10. A simulation bench for injected-edge pipeline tests (X4's A5-161), unbuilt.
11. Energy-specific verification evidence; no energy paper was read (R6).
12. A measured answer to whether LLM explanations change his decisions for the better (H30); A5-050's test design exists, no result.
13. The minimum lot per instrument against level 1 on $500 (Q5).

---

## 8. Party mode: the roundtable on the strongest hybrids

Headless, played by me. Personas: a pod-shop risk manager (RM), a retail scalper (SC), a platform engineer (PE), a trial statistician (ST), and his own voice (OP, lines from SEEDS and the word files). The hybrids on the table: H13 risk-tiered proof, H15 three speeds, H12 funded promotion, H06 the plan with correlation, H10 the bound click.

🧮 **RM:** Three speeds is how a desk already runs. Inputs first is the only thing that ever saved me money in a week. But your speed 3 at e ≥ 400 takes 1,900 trades to catch a dead unit. On a $500 book that unit is gone before the statistics say so.

📈 **SC:** Then the money brake catches it, and that's not this layer. What I care about is level 1. If level 1 is below one micro-lot on indices, your ladder has no first rung and I'm trading paper for months.

⚙️ **PE:** The ladder is fine; it's a fold over a transition stream, the node already does that for modes. What I can't build is "the evidence bar rises with the level" without a core module no slot can write to. That's a chassis change. Say it in the collisions.

📊 **ST:** Say the honest thing about H12. The 0.0% null rate is on daily ETF rules at 5 bp. On ±1R scalper trades with a 2R clip I got 2.3% at π = 1. Still ten times better than repeated looks, but not zero. And a +0.05R edge crosses in 60% of paths by 3,000 trades. That's the price.

🎙️ **OP:** "Edge is not something you can just come up with simply. It takes months, if not years." So why are you asking me to click a unit live before it's proved?

🧮 **RM:** Because the alternative is 28 days of paper that proves nothing either. Level 1 is a canary, not a promotion. Your click approves a hash, a market list, a level and an expiry. That's the bound click. It's tighter than what you have.

🎙️ **OP:** "You can't simply say if they differ, you simply pull out. It can be a bad day."

📊 **ST:** Nothing here pulls out on a day. A warning steps down one level after a CUSUM crosses, median 190 trades for a dead unit. Demotion waits for e ≥ 400 or a planned look. A healthy unit was demoted in zero of 4,000 trades in my runs.

📈 **SC:** The plan with the correlation column is the one I'd print and stick on the wall. Ten units at 0.3 are 2.7. I've been fooled by that exact thing with six USD pairs on one NFP.

⚙️ **PE:** Then give me the event window as a row, not a story. "Losses from one move count once" needs a clock and a window length in the ledger.

🧮 **RM:** It's `ev_event_window_minutes`, and it collides with X3's isolation protocol and X4's correlation scenarios. Same ρ everywhere or the layers lie to each other.

🎙️ **OP:** "Let's give a range for the edge."

📊 **ST:** Four low ends, lowest computable wins, half only as the fallback. The card shows which one it used. You can change the rule.

📈 **SC:** And the twin. A paper twin started the same minute tells me in fifty trades whether my fills are the problem. That's worth more than any of your e's.

⚙️ **PE:** Paper has zero slippage. The twin measures nothing until the lane draws slippage from node order rows. That's gap 2 and it's a builder PR, not research.

🧮 **RM:** Last one. Who holds the alarm budget? Twenty units, a year, you will get alarms. If nobody holds the budget, he stops reading the list.

🎙️ **OP:** "The BMS was doing this. I now remember. It's just that it wasn't self-configured."

📊 **ST:** Then the BMS holds it. Error over patience, logged beside every alarm.

Takeaways (not consensus): level 1 must exist in dollars (Q5); H12's numbers are "far better", not "zero"; the bound click is tighter than today's and is the honest form of C2; the twin needs paper slippage first; the alarm budget needs a holder; the same ρ must serve X3, X4 and X5.

---

## 9. Arithmetic

`x5_numbers.py` (draft) and `x5b_numbers.py` (this revision), standard library, independent ±1R trades, Gaussian where noted. Paths: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\2928e6ee-7392-4c1c-87c8-23b375749b4f\scratchpad\`. Run with `python -I`.

- Trades to proof (95% one-sided, 80% power): 612 at 55%, 2,467 at 52.5%, 15,450 at 51%.
- Calendar to 612 trades at 4 a day: 1 unit 153 days; 10 units at ρ 0, 0.1, 0.3, 0.5: 15, 29, 57, 84 days; 40 units: 4, 19, 49, 78 days.
- Smallest provable edge in 60 days at 80% power: 1 unit at 4 a day +0.16R (58%); 2.7 effective units +0.10R; 10 effective +0.05R; at 16 a day, 10 effective, +0.025R.
- Promote-style wealth on clipped ±1R (scale 2R, the paper's grid, α 0.05): no edge crosses 2.3% at π 1 (0.8% at π 0.25); +0.05R 60% (median 1,372); +0.10R 99.7% (median 624; 925 at π 0.25); +0.20R 100% (median 189).
- Likelihood e-meter against no edge at 1/α 20: true 0 crosses 4-5%; true +0.10R with alternative +0.10R: median 466; alternative +0.05R: median 735.
- "Edge gone" e-process against m = +0.05R at e ≥ 400 (20-unit budget): healthy +0.10R demoted 0%; at the line 0.4%; dead 35% by 4,000 (median 1,863); bleeding −0.05R 99% (median 1,025).
- Evidence tiers at +0.10R: e 10 median 335 trades, 20: 485, 50: 641, 100: 750.
- Worst of three 200-trade blocks for a healthy +0.10R unit: negative in 22% of units; 5th percentile −0.05R.
- Best day above half of a month's profit on a healthy 55% unit at 4 a day: 15% of profitable months.
- Machine check: at 4 a day a halved trade rate is 2.6 sd out after 7 days; a 0.05R cost rise is 8.8 SE out after 50 trades.
- CUSUM (allowance 0.05R, limit 19.5): medians 187 (dead), 315 (half), 668 (healthy, the false-alarm spacing).
- Bad 25-trade cohorts (≤ −5R): 9.7% at 55%, 14.9% at 52.5%, 21.4% at 50%; BOIN bars at a 15% target 11.8% up, 17.9% down.
- A healthy 55% unit at 4 a day: a −2R-or-worse day 24% of days; a −4R day 4%.

---

## 10. Questions only he can answer

Kept short. Technical questions were researched above.

- **Q1 (irreversible scope).** May a unit go live at the smallest size *before* its edge is proved, with the packet showing "proof pending, 212 of 610 trades, level 1"? If no, proof finishes in paper and paper gets longer than 7 days for most units.
- **Q2 (scope).** May a script move a unit from live back to paper by itself when the funded e-process confirms the edge is below its line, or at a planned look (never on one day), with his override logged? Or is every demotion a card?
- **Q3 (scope).** May a script step a unit's level *up* by itself when the level's evidence bar and cohort bar are met and the family permit is healthy, or is every step up his click?
- **Q4 (vocabulary).** Green, yellow, red (Basel) and orange for the ladder, or his own words? And the state words on screen: proving, proved at level n, pending, closed-thin, demoted, retired?
- **Q5 (money, numbers lens).** What is level 1 in dollars per trade on $500, and is it above the venue's minimum lot on the instruments he means to start with? This decides whether level 1 exists for index CFDs and some futures.
- **Q6 (money, numbers lens).** What is the smallest return per unit per month that makes a unit worth running at all? It sets the minimum viable edge m that confirmation tests against.

---

## 11. Sources

All grounding and research files cited inline: G8, G9, G11; R3, R4 synthesis (techniques 10, 11, 20; workflows 1-15), R6 synthesis and T-08, T-09; R9 §0.2-0.3; R5 (23482, 23103); R8 §5; SEEDS and the 3 Nov word file; STATE items 25-40. Component ids from `linking/components/A1`-`A5`. Papers named by arXiv id are those R6 read or R4 cited; none was re-read here. The stopped draft's sources stand for the seeds.
