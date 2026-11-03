# X5: real edge verification as a workflow

Expansion layer, written 2026-11-03. Nothing here is ratified. The funnel clusters, dedupes and picks.

## How to read this

- Ideas are numbered `X5-edge-verification-01` and so on, shortened to `X5-01` in cross references.
- Every variable named here is in `ledger/additions/X5-edge-verification.yaml`, with the id prefix `ev.`. Ledger v0 did not exist when this was written, so where v0 later names the same thing, v0's id wins and mine is an alias.
- **[judgment]** marks my opinion. **[arithmetic]** marks a number I computed (`x5_numbers.py` in my scratchpad, standard library, independent ±1R trades). Numbers from R3 are cited as R3.
- Short paths: `RC` = `D:\QMX-worktrees\risk-plan\tracker\risk-core\`; `R3` = `RC\research\R3-edge-verification-and-analogues.md`; `R2` = `RC\research\R2-trader-practice-windows-drift-isolation-breadth.md`; `G8`, `G9`, `G10`, `G11` = the files in `RC\grounding\`; `R08` = `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\research\08-old-qmx-testing-and-decay.md`; `R26` = `...\26-quant-judging.md`; `R05` = `...\05-academic.md`; `SEEDS` = `RC\seeds\SEEDS.md`.
- His rulings that bound this layer: QMB proves or enhances the edge before demo (SEEDS D18); picking units to promote is not this session's (D19); only he promotes to live (C-23, G9 §3.2); luck is not an argument (D18); paper is demo trading and "half the edge" made no sense to him (D14); 7 days of paper is doable, 14 is too long, and days still matter (D22); agents must solve issues, not list them (E28).

---

## 0. The two-minute explanation (for him)

**What "verifying an edge" means.** A unit's result on any one trade is mostly the market moving around. The edge is a small lean on top of that movement. Verification is the job of telling the lean from the movement. The only way to do that is to count trades: enough trades that the lean stands out above the wobble of the average.

**How many trades.** The wobble of an average shrinks slowly, by one over the square root of the trade count. After 100 trades the average can still be off by about 0.10R. A unit that wins 55% of 1:1 trades has a lean of exactly +0.10R per trade. So after 100 trades the lean and the wobble are the same size, and you cannot tell them apart. After about 600 trades the lean is about 2.4 times the wobble, which is where professionals say "this is probably real" [arithmetic]. That is the 610 trades in the earlier table.

**Why "half the edge" (52.5%).** The 55% came from a backtest. Backtests overstate, for three recorded reasons: the search picked the best-looking variant, costs were modelled, and markets move on. The evidence says published strategies lose about a quarter to a half of their edge once they leave the backtest (R3 §1.1, R05 §6.2). So the honest planning case is not "it will be 55%" but "it may be 52.5%". That is not a guess about demo; it is a discount on the backtest. And a half-size lean needs four times the trades to prove, about 2,470 instead of 610, because the wobble shrinks with the square root and the lean has halved. This has nothing to do with demo splitting the edge; demo results count as real trades. His objection in D14 was right about demo and wrong about what the halving refers to.

**Why "ten times faster".** Proof is counted in trades, but you wait in days. One unit at 4 trades a day reaches 610 trades in about 153 days. Ten units of the same logic at 4 trades a day each reach 610 trades together in about 15 days. Nothing about the maths changed; the trades arrived ten times faster. Two catches: the ten units must be testing the **same claim** (the same logic on markets where it is supposed to work), and they must not win and lose together. If their days move together 30% of the time, ten units count as about 2.7 and the wait is about 57 days, not 15 [arithmetic]. A unit on its own still needs its own trades to prove its own placement; pooling proves the logic, not the placement.

**What a bad day looks like.** A perfectly healthy 55% unit at 4 trades a day has a day of −2R or worse one day in four, and a day of −4R (every trade lost) one day in 24 [arithmetic]. So a bad day is not evidence of anything. A broken edge shows up only as a run of trades, hundreds long, whose average sits below what the unit promised. The verification workflow therefore has two speeds: fast rules that stop bleeding today (brakes, kill switch, SQS, another layer's job), and slow proof that looks at planned trade counts. Nothing in the slow lane ever acts on one day.

**What the workflow does.** Before a unit trades, it gets a plan: the edge it claims (as a range), how many trades proof needs at the low end of the range, and roughly when those trades will arrive. Then it trades, in paper and then at the smallest live size, and the plan is checked at planned trade counts, not every morning. Each check puts the unit in one of three zones: green (carry on, may step up one size level), yellow (hold, gather more trades, an agent explains), red (step down or back to paper). Every move is a formula on recorded trades. Agents propose units, write the plain-words explanations, and spot cost and fill problems. The one thing no formula and no agent does is move a unit to live money. That stays his click.

---

## 1. The whole path, as stages

Each stage names the question it answers, the evidence it needs, who acts, and what today's stack has (from G8 §4-5, G9 §3 and §7, G10 §2, R26 §2).

| # | Stage | Question | Evidence it needs | Who acts | Today |
|---|---|---|---|---|---|
| S0 | Idea | Is there a reason this should work? | A claim card written before any run: logic, context, market classes, claimed edge range, source | Agent writes it (B19 step 1); a deterministic check refuses a unit without it | B19 has a claim card (G8 §4.2) |
| S1 | Build and prove (QMB: B12, B13, B14) | Does it show an edge after costs on history, and is the best-of-many luck removed? | Cost stress, out-of-sample in R, plateau, PBO on the family, deflated Sharpe with effective tries | Scripts run; the judge writes a verdict and a frozen baseline card; agents explain | Built: verdict, card, effective tries (G8 §5.2). Missing: calibrated costs, commission in R, PBO (R08 §1.2) |
| S2 | Verification plan | How many trades will proof need, and can this unit make them in time? | The card's edge range and trade rate; the allowed incubation | Script computes; refuses "too thin to prove" | Not built. New (X5-01, X5-02) |
| S3 | Event replay | Does one real bad day break it? | 5 to 10 recorded event days | Script | Not built (R08 §1.6 optional) |
| S4 | Paper (C-12c) | Does the machine work, and do the first trades match the card? | Fills, trade rate, replay match, cost per trade; a sequential score | Script scores; agent explains | Built: paper lane and paper judge, 30 trades and 28 days (G9 §3.2). Paper has zero slippage (G9 §3.1) |
| S5 | His click (C-23) | Does he want this live? | The promotion card with the plan, the zone, the inputs check | Him only | Built (G9 §3.2) |
| S6 | Live at level 1 (smallest size) | Do live fills and costs match the card? Do the trades keep adding to proof? | Live cost and slippage per trade; the evidence meter | Script; agent explains | Not built: no live binding yet (G9 "missing" 17) |
| S7 | Planned looks | Is the edge proved, unproved, or out of reach? | Trades since the last look; the look schedule and its error budget | Script computes the zone | Not built. The nightly decay check uses the last 20 trades (G9 §7.2) |
| S8 | Step up | Has this size level been safe for enough cohorts? | Bad-cohort rate at the current level | Script proposes; the sizer's level moves by rule inside the template, or by his click (open, Q3) | Not built |
| S9 | Monitoring | Is the live footprint still the card's footprint? | CUSUM on R, cone, cost and fill drift, trade-rate drift, brake-fire density | Script; agent reads journals | Partly: `dc-decay-and-limit-report` (G9 §7.2) |
| S10 | Step down | Has the bad-cohort rate crossed the high bar? | Same cohorts | Script | Not built; nothing sizes down (G11 §4.3) |
| S11 | Demotion | Is the goal out of reach (futility), or has the edge died (CUSUM)? | Planned-look futility or an alarm | Script moves to paper; journal keeps running | Pipe exists (risk stop), nothing feeds it (G9 §1.1) |
| S12 | Rehab | Can a child variant bring it back? | A new counted try; the parent's live record as prior | Agent proposes children; QMB tests; the same path from S1 | Old WF3 D6 (R08 §2.1); not built |
| S13 | Re-promotion | Has the demoted unit earned its way back? | An e-value on post-demotion trades above 1/α plus a minimum time | Script says ready; he clicks | Old rule: 10 profitable demo trades (R08 §1.1), too weak (R2 §2.4) |
| S14 | Retirement | Have all children failed, or is the family's error budget spent? | Rehab count; alpha wealth of the family | Script; he confirms | Old WF3 retire branch |

**What stays outside this layer:** the brakes that act within a day (unit streak, Book daily, BMS daily, kill switch, SQS, isolation). They are the fast lane and belong to the brakes layer. This layer only reads their fire counts (X5-21).

---

## 2. Method passes on this design

Run on my own draft, playing every role, before the ideas below were finalised.

**CIS, problem statement refinement.** The vague ask: "how do we verify a valid edge". The refined problem: *QMX has every record a verification needs (trades in R, a frozen card, effective tries, a paper score) and no rule that turns them into a state a sizer, a screen or he can act on; and the only verdicts that exist are either a daily 20-trade comparison, which fires on noise, or his own click, which has no evidence standard behind it.* Success: a unit's verification state is a formula on its own recorded trades, priced in trades before it trades, visible on screen, and checked at planned counts.

**CIS, is / is not.** The problem IS: separating a lean from noise over hundreds of trades; backtest-to-live shrinkage; counting tries. It IS NOT: stopping a bad day (brakes), choosing markets (placement, MIS), deciding which unit to promote (his). Keeping the fast lane out of this layer was the main cut.

**CIS, five whys on "a bad day cannot be told from a broken edge".** Why? Because one day holds 4 trades and proof needs hundreds. Why does that matter? Because the only tool today compares the last 20 trades with the record, so it answers a question nobody asked. Why was it built that way? Because the decay definition was left to this session (G10 §5.4). Why is a definition hard? Because "decay" mixes three drifts (signal, fill, cost) and two speeds. Root cause: no stage in the path states, in trades, what evidence would change its mind. Hence X5-01 (the plan), X5-13 (inputs first), X5-18 (futility at looks).

**CIS, force field.** Driving: the records exist; he wants agents to carry the load; the baseline card is frozen already. Restraining: paper has zero slippage, so it cannot verify costs; costs are uncalibrated, so QMB cannot claim edge; R leaves out commission; trade rows lack session, streak and exit mechanism; no live binding. The strongest restraint is costs (X5-14, P8).

**CIS, constraint identification.** The bottleneck is **trades per calendar day**, not statistics. Everything that shortens calendar time (breadth, pooling, proof continuing into live) is worth more than any smarter test. Hence X5-10, X5-11, X5-12.

**Elicitation, first principles.** Strip it down: a verification is (a) a claim stated before data, (b) data that could not have shaped the claim, (c) a pre-set rule for what the data must show, (d) a count of how many claims were tried. Everything else is machinery. The stack has (a) partly and (d) fully; (b) exists only as paper; (c) does not exist. The ideas are ordered to give (c) first.

**Elicitation, Socratic questioning (on my own draft).** *Who said proof must finish in paper?* Nobody; the old vault let live Kelly come from the paper record and the unit build shows "one week on demo" as a hint (G10 §2.3). So proof can continue at the smallest live size (X5-10). *Why plan at half the edge rather than at the deflated holdout number?* Because "half" is a rule of thumb and the deflated holdout expectancy is the unit's own number; use the deflated number, and fall back to half only when the deflation cannot be computed (X5-38). *If sizing must not lean on the edge, why does verification?* Because verification is the gate (in or out, which level) and sizing is the amount; the edge decides the gate, the risk share decides the amount (X5-30). *What is "a cohort"?* A fixed count of trades, never a day, so that fast and slow units get the same rule (X5-16). *Can an agent be trusted to count its own tries?* No; the count must come from result streams at QMB's door (X5-07).

**Elicitation, pre-mortem.** It is 2027. The verification layer failed. Most likely causes, each now covered: (1) looks were taken daily "just to see", inflating false passes (X5-04, X5-05); (2) every unit sat yellow for months because trade counts never arrived (X5-02, X5-10, X5-11); (3) a unit went red on cost drift that was really a broker change (X5-13 splits the drifts; X5-56 measures slippage per hour); (4) a healthy unit was demoted because the decay check used the in-sample number as baseline (X5-19's rule); (5) the agent that wrote the claim card also wrote the explanation that waved the failure through (X5-28, an independent challenger); (6) ten units shared one US-release exposure and "proved" the logic in a week (X5-37); (7) nobody could see the state on screen and he clicked on feel (X5-33).

---

## 3. Ideas

Format: what; why a trader wants it; how; ledger ids; sources; maturity (solid, plausible, wild).

### A. The plan before trading

**X5-01. A verification plan per unit, priced in trades.**
What: before a unit trades paper, a script writes a plan: the claimed edge range, the trades proof needs at the low end, the expected trade rate, the calendar estimate, the look schedule, and the "too thin" verdict.
Why: a trader wants to know, before risking anything, how long until he knows. Today the only clock is "30 trades and 28 days" for every unit, whatever its edge.
How: trades needed ≈ ((z_conf + z_power) ÷ Sharpe_per_trade)², with the Sharpe from the card's deflated holdout record (R3 §1.1). Calendar = trades ÷ (trade rate × effective units). The plan is frozen with the card; a new card means a new plan.
Ledger: `ev.edge_band_low`, `ev.edge_band_high`, `ev.trades_to_proof`, `ev.calendar_to_proof`, `ev.confidence`, `ev.power`, `ev.trade_rate_expected`.
Sources: R3 §1.1, §5.1; R05 §2.4 (MinTRL); G8 §5.2 (card has `record_r`, `trade_rate`).
Maturity: solid.

**X5-02. "Too thin to prove" is a verdict, not a failure.**
What: if the trades to proof at the low end of the band exceed what the unit can make inside the allowed incubation (trade rate × max days × effective units), the plan says "closed, thin": the edge may be real, but QMX cannot prove it in time.
Why: a trader stops pouring time into a claim that cannot be settled. It also answers his "carry the load" goal honestly: a weak edge can pay, but only if it trades often enough to be proved; a weak and rare edge is a wish.
How: compare `ev.trades_to_proof` with `ev.trade_rate_expected × ev.max_incubation_days × ev.n_effective`. Below the line: proceed. Above: close, with the shortfall shown ("needs 2,470 trades, can make 480 in 60 days").
Ledger: `ev.max_incubation_days`, `ev.too_thin_verdict`, `ev.n_effective`.
Sources: R05 §7.3 rule 2; R3 §5.1.
Maturity: solid.

**X5-03. The claim is a range with a stated low end.**
What: the card carries an edge band, not a point: low = the deflated holdout expectancy minus one standard error (or half the in-sample number when deflation cannot be computed), high = the raw holdout number. Verification tests the low end. Sizing reads the low end for the gate.
Why: his rule "give the edge a range" (A24). A point edge invites false precision; a band tells the trader how unsure the claim is.
How: `ev.edge_band_low = max(0, deflated_mean − 1 × SE)`; `ev.edge_band_high = raw holdout mean`. The band width shrinks as trades arrive (X5-08).
Ledger: `ev.edge_band_low`, `ev.edge_band_high`, `ev.edge_band_rule`.
Sources: R2 §4.4 (lower-bound sizing is too strict for the amount, fine for the gate); R05 §6.1 (deflation).
Maturity: solid.

**X5-04. Planned looks with an error budget, never a daily 95% test.**
What: the plan fixes when the unit is judged: at trade counts (200, 400, 600, 800, 1,000 by default for a 0.1R claim), with a stricter bar early (O'Brien-Fleming style) so that the total false-pass rate stays at the budget.
Why: a trader who checks every morning and acts on the first good or bad week fools himself. Five casual looks at the usual bar turn a 5% false-pass rate into 14% (R3 §1.3).
How: bars z_k = 2.04 ÷ √(k/5) for five looks; "proved" when the running t-statistic crosses the bar; "futile" when the running mean is below zero at look 2 or later (non-binding). Looks are at trade counts, so fast and slow units get the same protection. Lan-DeMets spending allows calendar-timed looks for rare traders (X5-46).
Ledger: `ev.look_schedule`, `ev.look_count`, `ev.alpha_total`, `ev.alpha_spending_rule`, `ev.look_bar`.
Sources: R3 §2.2 (FDA 2019, simulated table: at 0 edge, 2.5% proved, 69% stopped futile, mean 646 trades).
Maturity: solid.

**X5-05. An evidence meter that may be read any day (e-process).**
What: beside the planned looks, a running evidence number: start at 1; each trade multiplies it up or down by how much more likely the trade is under "edge = claimed low end" than under "no edge". It can be shown on screen every day without breaking the error rate; a decision needs it above 1/α (20 at α = 0.05).
Why: he will look daily whatever the plan says. A meter that is safe to peek at makes looking harmless and gives the screen something honest to show.
How: log e += δ·x − δ²/2 per trade with δ the low-end edge in R and x the trade's R (sd 1R). [arithmetic] at a true +0.10R edge the meter passes 20 in a median of about 460 trades and 98% of units pass by 2,000; at no edge 4.5% ever pass; at +0.05R about half pass by 2,000 (median 700).
Ledger: `ev.evidence_e`, `ev.e_threshold`, `ev.e_alternative`.
Sources: R05 §7.2 (safe anytime-valid inference); R08 §2.3 "loosening after an alarm".
Maturity: solid; the choice between X5-04 and X5-05 as the deciding rule is a collision (C1).

**X5-06. Three zones, Basel style.**
What: every unit in verification or live is green, yellow or red. Green: evidence on track, may step up. Yellow: evidence behind plan or one input drifted; hold, no loosening, an agent explains. Red: futility, a CUSUM alarm, or two inputs drifted; step down or paper.
Why: banks found no single cutoff that both protects good models and catches bad ones, so yellow is the honest name for "we don't know yet" (R3 §1.4). It is also his "size down, but not quickly".
How: zone = f(planned-look state, evidence meter, inputs check, CUSUM). Yellow carries no penalty and asks for evidence. Red acts by formula.
Ledger: `ev.zone`, `ev.zone_rule`, `ev.yellow_entry`, `ev.red_entry`.
Sources: R3 §1.4, §5.3; R08 §2.3 (OK, Watch, Alarm).
Maturity: solid.

**X5-07. Count every try by its result stream.**
What: the family's effective try count comes from clustering the trade streams of every run at QMB's door (ONC or a correlation cluster), not from counting edits. The deflated Sharpe uses that count. Agents cannot lower it.
Why: more backtesting predicted a bigger live gap better than any other record (R05 §6.2). A trader who knows "this is the best of 40" discounts it.
How: every run lands a daily-R stream on a shared clock; streams with correlation above `ev.try_cluster_threshold` are one try; pre-registered edits count once, post-hoc edits twice (R26 §3.1 C and D).
Ledger: `ev.effective_tries`, `ev.try_cluster_threshold`, `ev.prereg_weight`, `ev.posthoc_weight`.
Sources: R26 §3 (51 variants → 11 effective; the shortcut formula said 1.9); G8 §5.2 (B13 already records effective tries).
Maturity: solid.

**X5-08. One evidence ledger per unit, every trade tagged by stage.**
What: all trades a unit ever made, with a stage tag (backtest, holdout, event-replay, paper, live-L1, live-L2, ...), in one append-only journal. Only stages at or after paper count toward live proof; backtest and holdout set the prior and the plan.
Why: a trader wants one place to see what the unit did, when, and under which rules. It also stops the oldest cheat: re-counting the backtest as evidence.
How: the Library `trade` item already has the fields (`session`, `streak`, `equity_before`, `costs`, `mae_r`); the journal rows that feed it do not carry them (G9 §7.1). Add `stage`, `exit_mechanism`, `replay_match` and `would_have` rows.
Ledger: `ev.stage_tag`, `ev.counts_toward_proof`, `ev.exit_mechanism`, `ev.replay_match`, `ev.would_have_row`.
Sources: G9 §7.1 gap; G11 §3.4-3.5; R26 §6.
Maturity: solid.

**X5-09. Two clocks: the machine check in days, the proof in trades.**
What: paper answers two questions and the plan separates them. Machine check (days): does it place orders, do fills land, does the trade rate match the card, is the replay match above 80%? Done in 5 to 7 days or N trades, whichever first. Edge proof (trades): continues past paper.
Why: this is what he accepted in M8 ("I think I get you"). It makes 7 days of paper honest: it never claimed to prove an edge.
How: `ev.machine_check_days` (7) and `ev.machine_check_trades` (30) close the machine check; the proof clock keeps running into live.
Ledger: `ev.machine_check_days`, `ev.machine_check_trades`, `ev.replay_match_min`.
Sources: SEEDS D22; G9 §3.2 (paper judge: fresh at 30 trades and 14 days).
Maturity: solid.

**X5-10. Proof continues at the smallest live size.**
What: after the machine check and his click, the unit trades live at level 1 (the smallest size) and those trades count toward proof with the same plan. Proof does not have to finish in paper.
Why: it is the clinical-trial shape (phase 1 small and real, phase 2 bigger), and it is the only way to honour "7 days doable" without pretending. Level-1 trades also carry real fills and costs, which paper cannot (G9 §3.1).
How: the look schedule spans stages; a step up to level 2 needs green at a planned look (X5-16).
Ledger: `ev.proof_counts_live_min_size`, `ev.size_level`.
Sources: R3 §2.1 (phases); R3 §1.4 (Numerai: stake small until out-of-sample scores show readiness).
Maturity: solid; the open point is his click timing (Q1).

### B. Shortening the wait

**X5-11. Pooled proof of a shared claim across units.**
What: units that run the same logic (a family) pool their paper and level-1 trades to prove the claim "this logic has an edge in this context". Each unit's own placement still needs its own trades, but it starts from the family's estimate (partial pooling), so a thin cell is shrunk toward its parent instead of judged alone.
Why: this is "ten times faster" made safe. An ORB on 12 session opens proves the ORB logic in weeks; each open proves itself later.
How: family estimate = pooled mean; cell estimate = w·cell + (1 − w)·family, w = n ÷ (n + k), k from the spread across cells (R05 §2.4). A unit's zone reads its shrunk estimate.
Ledger: `ev.family_id`, `ev.pool_shrink_k`, `ev.cell_estimate`.
Sources: R3 §1.1 (pooling proves a shared claim); R05 §2.4 (Stein, efficiency 3.5×).
Maturity: plausible.

**X5-12. A breadth-and-time calculator on the plan.**
What: the plan shows how units, markets, trade rate and correlation change the calendar: "1 unit: 153 days; 10 units independent: 15; 10 at ρ 0.3: 57; 40 at ρ 0.3: 49" [arithmetic].
Why: he reasons in frequency; this shows him exactly what frequency buys and what correlation takes back.
How: N_eff = N ÷ (1 + (N − 1)ρ), ρ measured from paper daily P&L across the family (X5-37).
Ledger: `ev.n_effective`, `ev.pool_corr_measured`.
Sources: R2 §4.2; R3 §1.1.
Maturity: solid.

**X5-13. Inputs first: the fast honest checks.**
What: before any P&L judgment, check the inputs against the card over the last 50 trades: cost per trade in R, slippage per trade in R, trade rate, holding time, replay match. Any one outside its band puts the unit in yellow at once; two put it in red. These need tens of trades, not hundreds.
Why: costs, fills and trade rate drift before profit does (R08 §2.2 trap 3). A unit whose cost doubled is broken today whatever its P&L says, and that is a thing a trader can act on the same day.
How: bands from the card: cost ≤ 1.5× card cost; trade rate inside 0.5×–2×; replay match ≥ 80%; holding time inside the card's 10th–90th percentile.
Ledger: `ev.cost_per_trade_r`, `ev.slippage_per_trade_r`, `ev.cost_drift_ratio`, `ev.cost_drift_window`, `ev.trade_rate_band`, `ev.holding_time_band`, `ev.replay_match_min`.
Sources: R08 §2.3 D3-D4; R2 §2.5; G9 §3.4 (slippage is in node order rows, unused).
Maturity: solid.

**X5-14. Live costs replace modelled costs in the verdict.**
What: once level-1 trades exist, the cost stress test is re-run with measured live cost and slippage, and the edge band is re-cut after measured costs. A unit whose low end goes below zero after live costs is red, however good its backtest.
Why: for scalpers cost is the master state; an edge smaller than its cost is no edge (R2 §4.2).
How: `ev.edge_band_low_after_live_costs = edge_band_low − (live_cost − card_cost)`; the QMB cost calibration artifact is refreshed from the same rows (closes GAP-0048 from the live side).
Ledger: `ev.edge_band_low_after_live_costs`, `ev.cost_stress_multiple`.
Sources: R08 §1.6 T1; R26 §2.1 step 2; G9 §5 (cost ports have no producer).
Maturity: solid.

**X5-15. The baseline is frozen; an edit restarts the paper record.**
What: the card and plan never refit on live data. Any edit to the unit is a counted try and a new version whose paper record starts at zero. The old version's trades become the new version's prior only through the family pool (X5-11).
Why: otherwise the unit is quietly fitted to its own live trades and the proof means nothing.
How: enforced at the Library: a new `qmx.unit/<n>` fingerprint gets a new evidence ledger; the old stays readable.
Ledger: `ev.baseline_frozen`, `ev.version_restart_rule`.
Sources: R26 §2.2 ("paper trades count as out-of-sample only for the frozen version"); R08 §2.3.
Maturity: solid.

### C. Size levels and the slow lane

**X5-16. Dose-escalation size levels.**
What: a unit's size is a level, L0 (paper) to Ln, never a free number. It moves one level at a time on cohorts of trades. Up when the bad-cohort rate at the current level is under a low bar; down when over a high bar; a level that proves dangerous is locked out; levels are never skipped. Steps rest on paper and live trades only, never on backtests.
Why: a trader sizes up a new strategy a notch at a time and backs off a notch when it bites. This is that habit with numbers, and it is his "size down, not quickly" with a rule.
How: cohort = `ev.cohort_trades` (25 by default); bad cohort = net R ≤ `ev.bad_cohort_r` (−5R); bars from the BOIN formulas at a target derived from the unit's own healthy rate. [arithmetic] a 55% unit has a bad 25-trade cohort 9.7% of the time, a 52.5% unit 14.9%, a no-edge unit 21.4%. With the target at 15% the bars are: step up below 11.8%, step down above 17.9%. So the healthy unit climbs, the half-edge unit holds, the dead unit descends. A fixed 30% target (the drug default) would let the dead unit climb, so the target must come from the card, not from a constant.
Ledger: `ev.size_level`, `ev.level_count`, `ev.cohort_trades`, `ev.bad_cohort_r`, `ev.bad_cohort_target`, `ev.level_up_bar`, `ev.level_down_bar`, `ev.level_lockout`, `ev.level_min_cohorts`.
Sources: R3 §2.4 (FDA review of BOIN); R3 §5.4.
Maturity: plausible; the level-to-dollars map is the sizing layer's (collision C4).

**X5-17. A minimum number of events before any slow-lane signal.**
What: no verification state changes before M trades at the current level (M = 25 by default, one cohort), and no zone changes on fewer than `ev.min_events` losing trades.
Why: a brake that can fire on the first loss has an unknown false-alarm rate (R3 §2.5). A trader does not judge a new size on its first trade.
How: thresholds are computed for the chosen M, so the false-alarm rate stays known.
Ledger: `ev.min_events`.
Sources: R3 §2.5 (Kulldorff and Silva).
Maturity: solid.

**X5-18. Futility at planned looks is the demotion rule.**
What: a unit is demoted to paper (keeps trading, keeps journaling, no money) when, at a planned look, the accumulated evidence says the claimed low-end edge is out of reach: running mean below zero at look 2 or later, or the e-meter's reciprocal above 1/α against the claim.
Why: this is the only honest answer to "bad day or broken edge": a bad day is less than one look; a broken edge is what futility catches, at a planned count, never on a single result.
How: non-binding futility (may be overridden by him with a reason logged); binding futility is an option that buys a looser final bar.
Ledger: `ev.futility_rule`, `ev.futility_binding`.
Sources: R3 §2.2 (FDA: non-binding futility does not raise the false-positive rate).
Maturity: solid.

**X5-19. CUSUM on R against the holdout baseline, with the first-hundreds rule.**
What: the live monitor adds, per trade, (baseline R − trade R − allowance), floored at zero, and alarms at a limit set for about one false alarm per 1,000 healthy trades. An alarm in the first few hundred live trades is read as "the holdout was optimistic" (re-cut the band) before it is read as decay.
Why: it is the fastest test for a dropped mean at a given false-alarm rate, and traders already use stacked levels on it.
How: allowance 0.05R, limit 19.5 at sd 1R. [arithmetic] a dead unit alarms in a median of about 190 trades; a half-edge unit in about 315; a healthy unit in about 670, which is the once-per-thousand false alarm rate (median ≈ 0.69 × mean). Watch at 70% of the limit.
Ledger: `ev.cusum_baseline`, `ev.cusum_allowance`, `ev.cusum_limit`, `ev.cusum_watch_share`, `ev.first_hundreds_rule`.
Sources: R08 §0 correction, §2.3 D1; R2 §2.2.
Maturity: solid.

**X5-20. The cone check.**
What: cumulative live R against the card's Monte Carlo cone at the same trade count; below the 5th percentile is a yellow mark, below for two looks is red.
Why: StrategyQuant and QuantConnect users rely on it because it is readable at a glance.
How: the card already holds the cone at 25, 50, 100 and N trades (G9 §7.1).
Ledger: `ev.cone_percentile`, `ev.cone_looks_to_red`.
Sources: R08 §2.2-2.3 D2; G9 §7.1.
Maturity: solid.

**X5-21. Brake-fire density against an expected rate.**
What: the card states the brake-fire rate a healthy unit would show (from the holdout, run through the same brakes). Live fires per 100 trades above that band are decay evidence; fires inside the band are noise. The old WF3 did this without a baseline; July planned the baseline and never filled it.
Why: brake fires are the fastest coarse signal there is (visible in days), and this is the only way to stop them being read as decay when they are the brake doing its job at the unit's normal trade count.
How: `ev.brake_fire_rate_expected` from the holdout replay with the unit's halts; `ev.brake_fire_rate_observed` per 100 trades from `stand_down` and `lifecycle` rows (G9 "what his ideas could hang on").
Ledger: `ev.brake_fire_rate_expected`, `ev.brake_fire_rate_observed`, `ev.brake_fire_band`.
Sources: G10 §0.3-0.4, §1.7; R08 §2.1; STATE item 10 (count brakes fire by chance as trades pile up).
Maturity: plausible.

**X5-22. The test of the tests: each gate's precision and lift.**
What: a monthly job measures, for every gate (cost stress, PBO, plateau, machine check, CUSUM, cone, each brake), the share of its fires that needed action and the share of its passes that later held. A gate with no lift for a unit type is reported as a defect and can be switched off per type.
Why: hospitals learned that 85 to 99% of alarms need no action and staff then ignore all of them (R3 §3.6). A trader wants few, true alarms.
How: cohort of the month's candidates; later outcome on held-back trades; lift = P(held | passed) ÷ P(held).
Ledger: `ev.gate_precision`, `ev.gate_lift`, `ev.gate_enabled_per_type`.
Sources: R3 §3.6, §5.6; R08 §1.6 "keep the tests honest".
Maturity: plausible.

**X5-23. Upside alarm.**
What: results far above the card (above the cone's 95th percentile for two looks) also go yellow: check for a sizing bug, a hidden shared exposure or a broker change.
Why: traders learn the hard way that "too good" is usually leverage they did not mean to take.
How: same cone, upper side; agent explanation requested.
Ledger: `ev.upside_alarm_percentile`.
Sources: R08 §2.2 trap 4.
Maturity: solid.

### D. Demotion, rehab, retirement

**X5-24. Rehab is a counted try with the parent's record as prior.**
What: a demoted unit's rehab children are new versions (new tries) whose plan starts from the parent's pooled estimate, not from scratch; the parent stays on paper, journaling.
Why: a trader keeps the knowledge and drops the version.
How: the old WF3 D6 "mini-WF2" shape, with B19 as the engine and the family pool as the prior.
Ledger: `ev.rehab_children_max`, `ev.parent_prior_weight`.
Sources: R08 §2.1 (branches); G8 §4.2 (B19).
Maturity: plausible.

**X5-25. Re-promotion needs evidence, not a streak.**
What: a demoted unit is "ready for his card" again when the e-meter on trades after demotion passes 1/α and a minimum time has passed. Ten profitable trades in a row is not a rule: a 2/3-win-rate unit with zero edge makes ten straight wins 1.7% of the time (R2 §2.4).
Why: a trader wants to know the comeback is real, not that the unit had a good week.
How: `ev.evidence_e` restarted at demotion; `ev.loosen_min_days`.
Ledger: `ev.e_threshold`, `ev.loosen_min_days`.
Sources: R2 §2.4; R08 §2.3 "loosening after an alarm".
Maturity: solid.

**X5-26. An error budget per family (alpha investing).**
What: each logic family holds a wealth of allowed false discoveries. Each unit put into verification spends some; each proved unit earns some back. A family whose wealth is spent cannot start new units until a proved one refunds it.
Why: with agents proposing units by the dozen, this is the only thing that bounds how many false edges reach paper across the whole system, not just per unit.
How: LORD-style online FDR; order the tests before looking at data so the wealth cannot be gamed.
Ledger: `ev.family_alpha_wealth`, `ev.alpha_spend_per_test`, `ev.alpha_refund_per_discovery`.
Sources: R05 §7.2-7.4.
Maturity: plausible, leaning wild for v1.

**X5-27. Retirement rules.**
What: a unit retires when `ev.rehab_children_max` children have failed, or its family wealth is spent and no refund is in sight, or every market cell is closed-thin. Retirement is final for that version; a comeback is a new unit with a parent link.
Why: a pool that never retires fills with ghosts.
How: deterministic; he confirms.
Ledger: `ev.retire_rule`.
Sources: R08 §2.1 (retire branch).
Maturity: solid.

### E. Where agents add value, and where they must not decide

**X5-28. An independent challenger before paper.**
What: a second agent, which did not build the unit, attacks the claim card and the verdict before the unit enters paper: is the reason economic, is the context claim testable, how many tries does the family show, what would make it fail. It writes a challenge note, never a verdict.
Why: bank model-risk rules call this "effective challenge" and require independence (R3 §1.4, SR 26-2). A trader who shows his idea to one sceptical colleague loses fewer months.
How: a B19 step after the referee, with the `unit_explain`, `backtest_results` and `journal_query` tools, writing only an artifact.
Ledger: `ev.challenge_note_required`.
Sources: R3 §1.4; G8 §4.1 (tools).
Maturity: plausible.

**X5-29. Agents explain the state in plain words.**
What: every zone change gets a short explanation written by an agent from the formula's inputs ("yellow because cost per trade rose from 0.06R to 0.11R over the last 50 trades; the edge has not moved"). The explanation is attached, never used as an input.
Why: this is the "two-minute read" he asked for, per unit, every time it matters.
How: an agent step after the nightly job; `notes_write` to the Library; shown on the unit card.
Ledger: `ev.explanation_note`.
Sources: G8 §4.1; G10 §2.4 (agents produce and diagnose; code gates).
Maturity: solid.

**X5-30. Sizing off the range: the edge is the gate, the risk share is the amount.**
What: the verification state decides whether a unit trades and at which level; the amount at a level comes from the risk share the sizing layer gives it, not from the edge number. Only the low end of the band enters, and only as "positive with evidence" or not.
Why: his two rules at once: do not lean on the edge for the amount (A24), but never size a thing with no evidence (D18). Desks size many strategies by risk and use the edge as a gate (R2 §4.4).
How: `size = level_fraction[ev.size_level] × risk_share`; the level moves by X5-16; `ev.edge_band_low > 0` is required for level ≥ 1.
Ledger: `ev.size_level`, `ev.gate_requires_low_end_positive`.
Sources: R2 §4.4; R3 §5.5 (do not chase performance across units).
Maturity: solid; collision with X5-31.

**X5-31. A soft evidence multiplier (optional, per template).**
What: for templates that want some lean on the edge, multiply the level's size by t² ÷ (1 + t²), where t is the low-end edge's t-statistic so far. At 300 trades of +0.05R it is 0.43; at 3,000 it is 0.88.
Why: some traders do want size to grow with proof; this gives that as a dial with a reason, and it never reaches full size without trades.
How: a sizer block input; off by default.
Ledger: `ev.evidence_multiplier_enabled`, `ev.evidence_t`.
Sources: R2 §4.4 (shrunk Kelly).
Maturity: plausible.

**X5-32. Journal fields the workflow needs.**
What: trade rows carry stage, session, streak, equity before, costs in R (commission, swap, funding included), slippage in R, MAE and MFE in R, exit mechanism (stop, FI cut, breakeven, time, signal, forced flat) and outcome, replay match flag; `would_have` rows while stopped or isolated.
Why: without the exit mechanism no brake or verification can count an FI cut differently from a full stop (G11 §3.5); without would-have rows a halted unit's evidence stops flowing.
How: extend `journal.py:397-418` rows to fill the Library `trade` schema that already has the fields; add the `exit_mechanism` enum from the exit block that fired.
Ledger: `ev.exit_mechanism`, `ev.would_have_row`, `ev.stage_tag`, `ev.costs_in_r_complete`.
Sources: G9 §7.1; G11 §3.4-3.5, "problem list" 5 and 7; R26 §6.
Maturity: solid.

**X5-33. The verification state on screen.**
What: on the unit card: the zone colour; "trades toward proof 212 / 610, next look at 400"; the evidence meter; an inputs strip (cost, slippage, rate, replay) each green or amber against the card; the size level with its cohort count; the last explanation. On the node and home pages: units grouped by zone; "Needs you" lists reds and ready-for-card units. Both dollars and R.
Why: his M12 ask: the UI must show wrong, right, working, up, on, trading. "Right or wrong" for the edge has no state word today (G11 §4.3).
How: the node emits `ev.zone`, `ev.size_level`, `ev.trades_toward_proof`, `ev.next_look_at`, `ev.evidence_e` and the inputs; the UI session takes the list.
Ledger: `ev.trades_toward_proof`, `ev.next_look_at`, plus the ones above.
Sources: G11 §4.2-4.3; SEEDS item 51.
Maturity: solid.

**X5-34. A verification passport per unit.**
What: one frozen record per unit version: claim card, verdict, card, plan, effective tries, challenge note, looks taken with their results, zone history, levels and cohorts, demotions, rehab links. The promotion card reads it. It is the bank "model inventory" for units.
Why: a trader with twenty units needs one page per unit that says what was promised and what happened.
How: a Library item kind `verification-passport`, appended by the nightly job.
Ledger: `ev.passport`.
Sources: R3 §1.4 (SR 26-2 inventory); G8 §5.2.
Maturity: solid.

**X5-35. The workflow is a nightly deterministic job, with an agent pass after it.**
What: once a day in the dead zone, a script per unit journal: inputs check, cohort update, planned-look check if a look count was reached, e-meter, CUSUM, cone, brake density; writes the zone and the passport; lands proposal cards for steps and demotions as the template allows. Then an agent reads the journal and writes the explanation and any diagnosis (fills, costs).
Why: every gate is a formula on recorded trades, so scripts can run it; agents are for prose and diagnosis.
How: extend `dc-decay-and-limit-report` to read the baseline card (its README says it cannot today) or replace it; schedule in the old dead-zone slot.
Ledger: `ev.job_schedule`.
Sources: R3 §5.9; G9 §7.2; R08 §2.3.
Maturity: solid.

**X5-36. Thresholds calibrated by simulation on the unit's own record.**
What: before paper, the plan simulates its own looks, cohorts and CUSUM on block-bootstrapped holdout trades, and reports the false-alarm rate and power of every rule for this unit. Any rule whose simulated false-alarm rate exceeds its budget is loosened by formula and the change logged.
Why: every number needs a reason (his rule); this gives each threshold one, per unit, instead of a constant.
How: 1,000 block-bootstrap paths (block of 5) from the holdout; run the whole slow lane on each; record the rates.
Ledger: `ev.sim_false_alarm`, `ev.sim_power`, `ev.sim_paths`, `ev.sim_block`.
Sources: R08 §1.6 T5 (block bootstrap for sizing); R3 §6 model limits (streaks shorten false-alarm spacing).
Maturity: plausible.

**X5-37. Correlation discount for pooled proof and for budget.**
What: measure the daily-P&L correlation between units of a family in paper; use it to compute N_eff for pooled proof (X5-11) and to flag "adds tries, not breadth" when a new unit correlates above a cap with live units.
Why: ten USD pairs on one US release are one bet. Without this the family "proves" its logic in a week on one shared move (pre-mortem cause 6).
How: ρ from daily R; `ev.pool_corr_cap` (0.5); N_eff formula.
Ledger: `ev.pool_corr_measured`, `ev.pool_corr_cap`, `ev.n_effective`.
Sources: R2 §4.2; R05 §7.3 rule 4.
Maturity: solid.

**X5-38. "Half the edge" becomes "the deflated holdout number".**
What: the planning low end is the deflated holdout expectancy from B13, not a flat half. Half is the fallback when deflation cannot be computed (fewer than two effective tries, or no holdout).
Why: his objection was fair: "half" sounds arbitrary. The deflated number is the unit's own and usually lands near half of the in-sample number for a thin edge after a search (R3 §1.1 table: best of 10 tries needs 1,026 trades against 612).
How: `ev.edge_band_rule` chooses the source; the plan shows which was used.
Ledger: `ev.edge_band_rule`.
Sources: R3 §1.1; R05 §6.1.
Maturity: solid.

**X5-39. A paper twin beside every live unit.**
What: the live unit keeps a paper twin on the same signals and the same code. The gap between twin and live per trade is the fill-and-cost drift, measured continuously; the twin's trades also keep flowing when the live unit is paused or isolated.
Why: this is the "run demo and small live side by side" answer he accepted, and it is Google's canary-versus-control in trading form.
How: the paper lane already exists (C-12c); add a `twin_of` link and a per-trade diff row.
Ledger: `ev.twin_enabled`, `ev.twin_gap_r`.
Sources: G9 §3.1, §3.3; R3 §1.4 (canarying).
Maturity: plausible.

**X5-40. Verification per cell with partial pooling.**
What: a unit's record is cut by market × session (its cells). Each cell's estimate is shrunk toward the unit's pooled estimate; no cell is judged alone until it has its own MinTRL. A cell whose shrunk estimate stays below zero after costs is proposed as `drop_market` (the existing `s2-tag-units-to-markets` card).
Why: a 2,000-trade scalper has about 40 trades per cell across 48 cells (R05 §2.4); judging cells raw would drop good ones and keep lucky ones.
How: empirical-Bayes weights; the MIS word at entry is a cell key when stamps exist.
Ledger: `ev.cell_key`, `ev.cell_estimate`, `ev.pool_shrink_k`.
Sources: R05 §2.4; G9 §7.2 (`s2`).
Maturity: plausible.

**X5-41. A demotion ladder, never a jump.**
What: green → yellow (hold, no loosening, no new markets) → orange (step down one level) → red (paper, journal on). Only the fast lane (brakes, kill switch) may jump straight to stop, and that is a different mechanism.
Why: his "size down, but not quickly"; the July law "shrink before block" that never had a mechanism (G10 §5.2).
How: zone transitions need a planned look or an inputs fire; each step is logged with the rule and its values.
Ledger: `ev.zone`, `ev.orange_entry`.
Sources: G10 §5.2, §5.6; R08 §2.2 stacked levels.
Maturity: solid.

**X5-42. Evidence keeps flowing while stopped.**
What: a unit paused by news, isolation, a brake or a demotion keeps computing its signals on paper and writes `would_have` rows, tagged so they never count toward proof but do count toward the replay match and the trade rate.
Why: the July rider ("keep collecting so decay data keeps flowing"); without it a stopped unit's clock freezes and nobody learns anything during the pause.
How: the node runs the unit in paper mode under the stand-down; rows tagged `would_have`.
Ledger: `ev.would_have_row`, `ev.would_have_counts`.
Sources: R08 §2.1 (July rethink); R26 §6; G9 §7.1 (nothing writes `would_have` today).
Maturity: solid.

**X5-43. Event replays as a gate before paper.**
What: five to ten recorded event days (news spikes, gap opens, spread blowouts) on the unit's instruments; no single event may lose more than `ev.event_replay_loss_cap` (3R).
Why: the old Stage H intent, done with real history.
How: a B14 run kind over a curated event list per instrument class.
Ledger: `ev.event_replay_loss_cap`, `ev.event_days_count`.
Sources: R08 §1.6 optional.
Maturity: plausible.

**X5-44. Calendar-timed looks for rare traders (Lan-DeMets).**
What: for units with few trades a day (an ORB once per session per market), looks happen at calendar times with alpha spent in proportion to the information fraction, so the error budget still holds.
Why: a once-a-day unit would wait years for 200-trade looks; calendar looks with correct spending are the trial-world answer.
How: `ev.alpha_spending_rule = lan-demets`; information fraction = trades so far ÷ planned trades.
Ledger: `ev.alpha_spending_rule`, `ev.look_schedule`.
Sources: R3 §2.2 (FDA on Lan-DeMets).
Maturity: plausible.

**X5-45. The old WF3 branches as zone transitions.**
What: keep = green; reduce weight = orange; demote = red; retire = X5-27; rehab = X5-24. Each old branch now has a formula and a baseline, which WF3 never had.
Why: his memory of the circuit breaker catching decay is right (G10 §0.1); this is the version with numbers.
How: a mapping table in the template.
Ledger: `ev.zone_rule`.
Sources: R08 §2.1; G10 §1.7.
Maturity: solid.

**X5-46. A verification template per unit type.**
What: scalper: trade-count looks, cohorts of 25, CUSUM, pooled by session; ORB: calendar looks, pooled across session opens and markets, cohorts of 10; intraday: cohorts of 15, looks at 100 trades; each with defaults and their reasons, each overridable, each extendable with new gates.
Why: one template per type is his ruling (A5); the trade rate differs by an order of magnitude between types, so one schedule cannot fit.
How: the template is data (the ledger rows for that type), read by the nightly job.
Ledger: `ev.verification_template`.
Sources: SEEDS A5; R26 §2.1.
Maturity: solid.

**X5-47. The plan states what counts as unseen data.**
What: since sealed holdouts are off by default (rulings 136-137), the plan must name, per unit, which data could not have shaped the claim: the holdout if one was sealed, else paper and live only. Backtest trades never count, even when the backtest ran after the build.
Why: a verification is worth nothing if the unit could have been fitted to the data that verifies it.
How: `ev.unseen_data_source` ∈ {sealed-holdout, paper-and-live}.
Ledger: `ev.unseen_data_source`.
Sources: R26 §2.3; R26 "what is already settled".
Maturity: solid.

**X5-48. "Bad day" gets a definition from the card.**
What: a day is "bad, normal" when its R sits inside the card's daily distribution down to the 5th percentile (for a 55% unit at 4 trades: −4R happens one day in 24 [arithmetic]); below that it is an event for the fast lane and still not a verdict on the edge.
Why: it gives him and the agent a sentence to say the next morning: "yesterday was a one-in-24 day for a healthy unit of this type; nothing about the edge has changed".
How: the card stores the daily-R quantiles from the holdout.
Ledger: `ev.bad_day_percentile`.
Sources: R2 §2.1; this file §0.
Maturity: solid.

**X5-49. Agents diagnose fills and costs from node rows.**
What: an agent (or script first) reads node `order` rows (asked versus filled), the reconciler's slippage, and the market journal's spread at the hour, and writes per-instrument, per-hour slippage and cost profiles. The verification job reads those; QMB's cost calibration artifact is refreshed from them.
Why: the data is already there and nothing uses it (G9 §3.4); it closes "costs never reach the sizer" from the live side.
How: a `dm-demo-monitor` extension; a cost-profile artifact per instrument.
Ledger: `ev.slippage_per_trade_r`, `ev.cost_profile_source`.
Sources: G9 §3.4, §5; G8 §5.1 (R leaves out commission).
Maturity: solid.

**X5-50. Agents propose which units to pool.**
What: an agent proposes family membership ("these six units are the same logic in different contexts") from claim cards and result-stream correlation; a script confirms by correlation; the family is the unit of pooled proof and of alpha wealth.
Why: pooling is the biggest calendar win and a human would not keep the families straight across forty units.
How: a weekly agent step; `blocks_match` and `journal_query`.
Ledger: `ev.family_id`.
Sources: R26 §3; G8 §4.1.
Maturity: plausible.

**X5-51. A live control arm: random-entry twin.**
What: beside the paper twin, a randomised-entry twin with the unit's own exits trades paper; the real unit must beat its twin at planned looks. It is rule significance, run live.
Why: it separates "the entry has an edge" from "the exits are kind", with no model and no history.
How: paper lane, entries drawn at the unit's trade rate, same exits.
Ledger: `ev.control_twin_enabled`.
Sources: R26 §2.1 step 1 (Jesse's random-entry test); R3 §1.4 (canary control).
Maturity: wild.

**X5-52. Cross-context transfer as stronger evidence.**
What: a unit that claims a market-physics context (a Hurst or variance-ratio word) is also run on markets with the same reading it was never built on; a pass there counts as extra evidence for the logic (System 1 over System 2).
Why: his own rule: a logic placed where the market suits it, not a strategy fitted to one pair.
How: the MIS board's reading history picks the transfer markets; the family pool takes the trades at a lower weight.
Ledger: `ev.transfer_weight`.
Sources: SEEDS D3; G9 §4 (readings exist; direct reads refused).
Maturity: wild.

**X5-53. Agents stake family wealth on their proposals.**
What: when an agent proposes a unit, it bids a share of the family's alpha wealth as its confidence; a failed unit burns the stake, a proved one refunds with interest. The agent's stake history is shown next to its proposals.
Why: it makes the try count honest by making it cost something, the Numerai way.
How: X5-26 plus a per-agent ledger.
Ledger: `ev.family_alpha_wealth`, `ev.agent_stake`.
Sources: R3 §1.4 (Numerai staking); R05 §7.2.
Maturity: wild.

**X5-54. Family lineage credit.**
What: a family whose members keep passing earns a looser prior for new children (a higher starting weight in the pool); a family with failures gets a stricter one.
Why: a trader trusts the tenth variation of a logic that has paid nine times more than a new idea.
How: hierarchical prior with the family's proved count as its strength.
Ledger: `ev.parent_prior_weight`.
Sources: R05 §7.2 (hierarchical priors).
Maturity: wild.

**X5-55. Live canary across markets.**
What: promote a multi-market unit live on a subset of its markets (the canary) while the rest stay paper (the control); compare at looks; widen only on green.
Why: Google's canary rule, "sizeable and long enough to be representative", applied to placement; it limits the money at risk while proof runs.
How: a deployment flag per market; the plan's look schedule per market.
Ledger: `ev.canary_share`.
Sources: R3 §1.4 (canarying); G9 §3.2 (one unit version per deployment refuses a second market today).
Maturity: plausible.

**X5-56. Verification state is a halt input.**
What: the unit's zone and level are inputs the halt and sizer slots can read (today the sizer gets equity, entry, stop and the instrument only). A red zone is a `no_new_entries` halt by rule.
Why: otherwise the verification is a report nobody acts on, which is G9's finding for every drift piece today.
How: a host-side input `verification.zone` and `verification.level` on the slot contract.
Ledger: `ev.zone`, `ev.size_level`.
Sources: G8 §2.4, §5.1; G9 §7.3.
Maturity: solid; collision with the chassis layer (C3).

---

## 4. Problems and proposed solutions

Each with at least two options and their trade-offs. Options are not picks.

**P1. A bad day cannot be told from a broken edge quickly.**
- Option A: planned looks with non-binding futility (X5-04, X5-18). Pro: known error rates; never acts on a day. Con: slow by design; at half the edge nearly half of plans are undecided at 1,000 trades (R3 §2.2).
- Option B: the e-meter as the continuous read and the sole decider (X5-05). Pro: safe to peek at; one number on screen. Con: less power than planned looks for the same trades; needs a chosen alternative edge.
- Option C: inputs-first (X5-13) plus brake-fire density (X5-21), with P&L judged only at looks. Pro: the fast honest signals act in days; P&L noise never acts. Con: needs the exit mechanism and cost fields in the journal first.
- Option D: a plain-words definition of "bad day" from the card (X5-48), with no action attached. Pro: cheapest; removes the question for most mornings. Con: answers the feeling, not the decision.

**P2. "Half the edge" versus "paper is demo trading".**
- Option A: replace "half" with the deflated holdout number (X5-38) and say so on the plan. Pro: the unit's own number; answers his "where does it come from". Con: needs effective tries and a holdout; falls back to half otherwise.
- Option B: keep a flat discount as a template default with its reason (published shrinkage 26 to 58%). Pro: simple; always computable. Con: looks arbitrary to him, and is.
- Both: demo trades count fully; the discount is backtest-to-reality, never demo-to-live. The demo-to-live gap is costs and fills, measured separately (X5-13, X5-14).

**P3. Seven days of paper versus 600 trades of proof.**
- Option A: two clocks (X5-09) plus proof continuing at level 1 (X5-10). Pro: paper is short and honest; real fills feed the proof. Con: he clicks live before proof is complete (Q1), at minimum size.
- Option B: pooled proof across the family (X5-11) so the logic is proved in paper and only placement continues live. Pro: no live money before the logic is proved. Con: needs several units of one logic at once; correlation can stretch it back.
- Option C: longer paper for thin edges only, by plan (X5-02 computes it). Pro: no money at risk. Con: for a thin scalper that is months; against his patience.

**P4. Daily peeking inflates false passes.**
- Option A: planned looks only; the screen shows "next look at N" and no interim verdict. Pro: clean. Con: he will look anyway.
- Option B: the e-meter on screen every day (X5-05) and looks for decisions. Pro: looking is harmless. Con: two numbers to explain.

**P5. Which trades count: FI cuts, breakevens, forced flats, would-have rows.**
- Option A: every closed trade counts by its R, whatever the mechanism; the mechanism is a field for brakes and diagnosis only (X5-32). Pro: one rule; the edge is the edge after the unit's own exits. Con: a unit with many 0R breakevens shows a smaller edge and needs more trades; that is true, not a flaw.
- Option B: exclude forced flats (kill, isolation) and count would-have rows for rate and replay only (X5-42). Pro: outside events do not read as decay. Con: a unit that is often flattened has a thinner record.
- Option C: count FI cuts as 0.5 trade toward proof. Pro: none I can defend. Con: invents a number. Listed to show it was considered and should be rejected.

**P6. He wants weak edges to pay; weak edges are the hardest to prove.**
- Option A: "too thin to prove" closes the claim, and breadth and pooling are the only ways to reopen it (X5-02, X5-11, X5-12). Pro: honest; frequency is the lever he already believes in. Con: a weak rare edge never gets live money.
- Option B: let weak edges trade at level 1 indefinitely with a fixed small risk share and no step up until proved (X5-30 gate plus X5-16 lockout at L1). Pro: "squeeze some money" while proof accumulates. Con: level 1 on $500 may be below the minimum lot; many level-1 units are many small bets on unproved claims.
- Option C: shrunk-size multiplier (X5-31). Pro: a dial with a formula. Con: leans on the edge number, against A24.

**P7. QMB's outputs never reach the sizer or the node.**
- Option A: the verification job writes zone and level into a host-side input that the slots read (X5-56). Pro: one new input; the chassis stays. Con: needs the slot contract change the chassis layer owns.
- Option B: the node reads the passport from the Library (X5-34) at deployment and at each nightly job. Pro: no slot change. Con: a Library read on the money path; stale between jobs.

**P8. Costs are uncalibrated, commission is outside R, paper has zero slippage.**
- Option A: live level-1 costs refresh the calibration and re-cut the band (X5-14, X5-49). Pro: real numbers; closes the gap from the live side. Con: needs the live binding (C-21) first.
- Option B: a paper lane that models slippage from node order rows on demo (G9 §3.4 data). Pro: paper becomes useful for cost checks before live. Con: demo fills are kinder than live; still a model.
- Option C: refuse to claim "verified" for any scalper until measured costs exist; verify only "machine works" and "inputs match". Pro: honest. Con: delays everything on $500.

**P9. Agents iterate; tries get undercounted.**
- Option A: result-stream clustering at QMB's door (X5-07). Pro: counts every edit the same. Con: needs streams on a shared clock; ONC or a stand-in.
- Option B: pre-registration weights (claim before result counts once, after counts twice) (X5-07 D). Pro: rewards the habit. Con: timestamps can be gamed by a careless agent.
- Option C: staking (X5-53). Pro: makes it cost something. Con: wild; needs the wealth ledger.

**P10. Correlated units overstate pooled proof and breadth.**
- Option A: measured ρ and N_eff in the plan (X5-37). Pro: cheap. Con: ρ needs weeks of paper to measure.
- Option B: a prior ρ by shared driver (same currency, same class, same session) until measured. Pro: available at day one. Con: a guess with a label.

**P11. Who acts on a verdict.**
- Option A: scripts step levels down and demote to paper; only step-ups and live need his click. Pro: brakes-first; no human in the loop for safety. Con: he said demotion on one bad day is wrong; this acts only at looks, but he has not ruled on automatic demotion (Q2).
- Option B: everything is a card; he clicks all. Pro: his control. Con: G10 §2.4 warned this adds clicks he may not want; a red at 02:00 waits for morning.
- Option C: scripts act within the template's allowed moves (down and paper), cards for the rest, with his override logged. Pro: the clinical shape. Con: the template must say what is allowed, per type.

**P12. Rare traders (ORB) wait years for trade-count looks.**
- Option A: calendar looks with Lan-DeMets spending (X5-44). Pro: correct error rates. Con: more maths to explain.
- Option B: pooled across session opens and markets (X5-11); the ORB logic is one family. Pro: his "ORB gets frequency through breadth". Con: the opens are correlated on risk-off days.

**P13. How the band feeds size.**
- Option A: gate only (X5-30). Pro: does not lean on the edge. Con: a unit with twice the evidence gets the same amount; he may find that odd too.
- Option B: gate plus the soft multiplier (X5-31). Pro: size grows with proof. Con: leans on the edge.
- Option C: the level is the only thing the edge touches (X5-16); the amount per level is the sizing layer's. Pro: one mechanism, readable. Con: steps are coarse.

**P14. Re-promotion after demotion.**
- Option A: e-meter above 1/α on post-demotion trades plus minimum days (X5-25). Pro: evidence-based. Con: a thin edge takes months to come back.
- Option B: rehab child through the full path (X5-24). Pro: a fresh counted try. Con: the parent's paper trades are wasted unless pooled.

**P15. The verification needs fields the stack does not write.**
- Option A: fill the Library `trade` schema from the journal rows (X5-32). Pro: schema exists. Con: a unit-path change in the builders' lane.
- Option B: compute what can be derived (streak, equity before) in the nightly job from the row order, and add only `exit_mechanism` and `stage` at the source. Pro: smaller change. Con: two homes for one fact.

---

## 5. Collisions noticed

Named, not resolved.

- **C1. Planned looks (X5-04) versus the e-meter (X5-05) as the deciding rule.** Both are valid; using both means two decision rules that can disagree. The funnel must pick one decider and let the other be display.
- **C2. "Proof continues at level 1 live" (X5-10) versus his rule that promotion is his click and QMB proves the edge before demo (D18, D19).** Under X5-10 he clicks a unit live before its edge is proved. Either he accepts clicking "live at minimum size, proof pending", or proof must finish in paper, which collides with "7 days doable".
- **C3. Zone and level as halt and sizer inputs (X5-56) versus the chassis layer's slot contract.** The sizer gets four inputs today; adding verification inputs is a contract change that layer owns.
- **C4. Size levels (X5-16) versus the sizing layer's amount.** X5-16 says what level; the sizing layer says what a level is in dollars and how the day budget splits across units. If the sizing layer sizes continuously (Kelly fraction), levels are a second mechanism.
- **C5. X5-30 (edge is only a gate) versus X5-31 (soft multiplier) versus his A24 (don't lean on the edge) versus the lead's "twice the edge, twice the size".** Four positions on one dial.
- **C6. Count-brake fire density as decay evidence (X5-21) versus the brakes layer's redesign of count brakes.** If count brakes are replaced by money or drawdown brakes, the "expected fire rate" baseline changes meaning.
- **C7. Pooled proof (X5-11) versus "each unit stands alone" and per-unit placement.** Pooling proves the logic; a unit's own cell may still be unproved while the family is green. The screen must show both or he will read family green as unit green.
- **C8. Alpha wealth per family (X5-26) versus "agents propose freely, the sky's the limit" (D42).** A spent family blocks new proposals.
- **C9. Automatic demotion by script (P11 A) versus "you can't simply pull out" (A25).** Futility at a planned look is not one bad day, but he has only ruled on the day case.
- **C10. Would-have rows during isolation (X5-42) versus the brakes layer's isolation protocol.** Which host computes the would-have signals while a class is switched off is unassigned.
- **C11. The decay check's 20-trade comparison (shipped) versus everything in section C here.** The shipped job will be replaced or rewritten; its tighten-only cards assume a sizer input that does not exist.
- **C12. "Every closed trade counts by its R" (P5 A) versus a brakes layer that counts FI cuts by size or not at all (G11 §3.5 four histories).** Verification and brakes may count the same trade differently; the ledger must record both rules.
- **C13. The grounding's "same floor odds for many units" (STATE item 10) versus X5-37.** Ten units at full size with ρ = 0.3 are 2.7 units for proof and more than one unit for floor odds; the two layers must use the same ρ.
- **C14. Calendar-timed looks (X5-44) versus his "days still matter for paper, but trades count".** Lan-DeMets uses days to schedule and trades to decide; it is both, which may read as neither.

---

## 6. Questions only he can answer

Kept short. Technical questions were researched above.

- **Q1 (irreversible scope).** May a unit go live at the smallest size *before* its edge is proved, with the plan showing "proof pending, 212 of 610 trades"? If no, proof must finish in paper and paper gets longer than 7 days for most units.
- **Q2 (scope).** May a script move a unit from live back to paper by itself at a planned look (never on one day), with his override logged? Or is every demotion a card for his click?
- **Q3 (scope).** May a script step a unit's size level *up* by itself when a level has been green for the required cohorts, or is every step up his click?
- **Q4 (vocabulary).** The three zones: green, yellow, red (Basel), or his own words? And "proved", "pending", "closed-thin", "retired" as the state words on screen?
- **Q5 (money, numbers lens).** What is the smallest live size level on $500 in dollars per trade, and is it above the broker's minimum lot on the instruments he means to start with? This decides whether level 1 exists at all for FX micro-lots, indices and crypto.

---

## 7. Sources

All grounding and research files cited inline. Outside sources are those R3, R2, R08, R26 and R05 read; none were re-read here. New arithmetic: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\2928e6ee-7392-4c1c-87c8-23b375749b4f\scratchpad\x5_numbers.py` (standard library; run with `python -I`). Its results: trades to proof 612 / 2,467 / 15,450 at 55 / 52.5 / 51%; calendar 153 days for one unit at 4 a day, 15 for ten independent, 57 for ten at ρ 0.3; a healthy 55% unit has a −2R-or-worse day 24% of days and a −4R day 4%; the e-meter crosses 20 in a median of 456 trades at +0.10R, 4.5% false crossings at no edge; CUSUM medians 187 / 315 / 668 trades at 0 / +0.05 / +0.10R; bad 25-trade cohorts (≤ −5R) 9.7 / 14.9 / 21.4% at 55 / 52.5 / 50%; BOIN bars at a 15% target 11.8% up and 17.9% down.
