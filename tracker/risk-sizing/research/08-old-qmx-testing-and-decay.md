# 08: Old QMX testing and alpha decay

Written 2026-10-24. Research only. Nothing here is ratified, and no repo was changed.

## How to read this

**Labels.**
- **CHECKED**: I read it at the cited path or URL on 2026-10-24.
- **REMEMBERED**: the operator said it, but no written design backs it.
- **INFERRED**: my reading, arithmetic or proposal.
- **PRACTITIONER**: a trader or vendor said it on a forum, blog or help page. It is evidence of practice, not proof.

**Numbers.** Every number below is a configurable starting value. None is fixed.

**Short paths.**

| Alias | Path |
|---|---|
| `VAULT` | `C:\Users\Mubarak\Documents\Claude\QMX-discussion\` (old QMX, Apr–Jul 2026; read only, nothing run from it) |
| `WIKI` | `C:\Users\Mubarak\Documents\QMX\wiki\` (the July GitBook generation of old QMX) |
| `QMB` | `C:\Users\Mubarak\Desktop\QMX\docs\components\qmb.md` |
| `ADR17` | `C:\Users\Mubarak\Desktop\QMX\docs\decisions\ADR-0017-qmb-experimentation-library.md` |
| `DW` | `C:\Users\Mubarak\Desktop\QMX\_docwork\` |
| `R` | `D:\QMX-worktrees\agent-system\tracker\risk-sizing\research\` (`01-ground-truth.md`, `03-strategyquant.md`, `05-academic.md`) |
| `G09` | `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\grounding\09-original-design-recovery.md` |

---

## 0. The answer in ten lines

1. **Old QMX tested every bot with walk-forward, a 1,000-shuffle Monte Carlo and PBO,** inside a parity replay that ran the same risk, stops and kill switch as live. The July registry gave numbers: 6 months train, 1 month test, at least 200 test trades per window, at least +0.15R per trade after costs, PBO below 0.25 to pass and above 0.50 dead. CHECKED (`VAULT\02-Components\11-backtest-engine.md`; `WIKI\topics\backtest-and-replay.md:41-49`).
2. **New QMB has more test machinery in code than old QMX ever had** (trade shuffle, candle perturbation, rule significance, walk-forward, optimisation with sensitivity, sweeps). But it has **no pass numbers, no applied correction for tries, no calibrated costs and no results in R**. So nothing it produces counts as evidence yet. CHECKED (`R\01-ground-truth.md` §1.3).
3. **What old QMX did better and the new one dropped:** fixed pass numbers in R, PBO actually in the battery, a minimum trade count per window, parity replay of the live rules, slices by session and regime, MAE/MFE, a scenario stress stage, and a per-bot paper window before live.
4. **What the new one does better:** it counts every try, refuses to call synthetic or shuffled runs "edge", keeps raw measures and judges them later, calibrates costs from real fills, and seals a holdout.
5. **Research says most robustness tests do not predict live survival.** Trade-shuffle Monte Carlo cannot catch an overfit trade list. What works best together: count the tries and deflate, test the family for overfitting (PBO), stress the costs, and watch the bot live with a sequential test. CHECKED (`R\05-academic.md` §6.2; `R\03-strategyquant.md` §2.3).
6. **Recommended QMB set: five tests plus one automatic record** (§1.6). The output is a frozen **baseline card** per unit that the live decay check later reads.
7. **WF3 was "pool cleaning":** a workflow that read the synced trade journals, scored decay, split drawdowns, and chose keep, reduce, demote, retire or rehab. There was no WF5. CHECKED (`VAULT\02-Components\14-agentic-system\12-wf3-pool-cleaning.md`).
8. **The decay maths was never written down.** The vault named four kinds of evidence but no formula, window or threshold. The new docs already ruled "design it fresh" (DEC-0092). CHECKED (`VAULT\outputs\alpha-decay-spec.md` §2, §8; `DW\ratification-packet.md:208`).
9. **Outside practice converges on one shape:** compare live trades with a frozen expectation, use a pre-set band (Monte Carlo cone) and a sequential test (CUSUM), and split the gap into signal, fill and cost. Prop firms add hard loss ladders and "call down to sim". CHECKED (§2.2 URLs).
10. **Recommended decay check** (§2.3): one nightly job per unit journal with four readings (CUSUM on R, cone, cost and fill drift, trade-rate drift) and three states (OK, Watch, Alarm). Loss limits stay a separate, fast rule.

**A correction to `05-academic.md` §4.6.** Its table says a CUSUM needs about 1,400 trades to notice an edge falling from +0.1R to 0. With the same false-alarm rate (one per 1,000 trades), the standard Siegmund formula and my own 1,500-path simulation both give about **240 trades**. The other two rows shrink too: about 115 trades (+0.1R → −0.1R) and about 55 trades (+0.1R → −0.3R). INFERRED (script in my scratchpad; a forum simulation got 237: https://moltbook.com/post/6337962c-8e19-4d02-9ccf-491c7fdc5f58, PRACTITIONER). The conclusion of 05 still holds: decay detection is slow, so fast protection must stay a set of rules.

---

# Job 1: Backtesting and stress testing

## 1.1 How old QMX tested (Apr–Jul 2026)

**Parity replay.** The backtest had to run every live authority: sizing, stops (break-even at +1R), the kill switch (checked before stops on every bar) and the same journal schema. Only two swaps were allowed: history instead of live ticks, and a fill simulator instead of the broker. "Known production gaps" had to be replayed too. CHECKED (`VAULT\02-Components\11-backtest-engine.md:17-43`).

**Fill simulator.** Per symbol: spread (fixed or drawn from history), slippage (fitted to journal slippage), commission, chance of a partial fill, chance of a rejection. CHECKED (same file, 47-71).

**Walk-forward.** Expanding or rolling windows. Settings: train length, test length, step, and a **minimum trade count per window** (windows below it do not count). Only the test windows are evidence. CHECKED (same file, 97-137).
- *Example:* train on Jan–Jun, test on Jul; train on Feb–Jul, test on Aug; and so on. The bot's score is the joined test months only.

**Monte Carlo.** Shuffle the order of the test trades 1,000 times. Report the 5th, 50th and 95th percentile of final equity, max drawdown, Sharpe and profit factor. The 5th-percentile curve had to stay above the drawdown band. CHECKED (same file, 141-152).
- *Example:* 300 test trades, shuffled 1,000 times. In the worst 5% of orderings the drawdown reaches 18%. If the account's limit is 15%, the bot fails.

**PBO (probability of backtest overfitting) by CSCV.** Cut history into 16 equal pieces. Try every way of using 8 as "train" and 8 as "test". Each time, take the best variant on train and see where it ranks on test. PBO is the share of splits where the train winner lands in the bottom half on test. Below 0.25 pass, above 0.50 do not promote. CHECKED (same file, 156-171).
- *Example:* 20 variants of one idea. In 45% of the splits the train winner is below the test median. PBO = 0.45: the "best" variant is close to a coin flip.

**The July registry numbers** (the "Examination Engine" battery): train 6 months, test 1 month, at least 200 test trades per window, test expectancy at least +0.15R after modelled costs, 1,000 shuffles, PBO pass below 0.25 and dead above 0.50. CHECKED (`WIKI\topics\backtest-and-replay.md:41-49`; `WIKI\registry\variables.md:33-37`). The certificate gated on "edge after cost" plus "non-fiction". CHECKED (`VAULT\outputs\clash-report-backtest-replay.md:30-33`).

**Report slices.** Every WF1 report had to carry Monte Carlo and walk-forward, plus session, overlap, regime and regime-transition slices, spread, liquidity and cost sensitivity, MAE/MFE and a complexity summary. Reports were written by the engine, never by an LLM. CHECKED (`VAULT\bmad-docs\planning-artifacts\workflows-architecture.md:216-221`; `VAULT\bmad-docs\planning-artifacts\prd.md` FR64, L977).

**A family gate.** A variant whose backtest R:R fell below its archetype's family average did not leave WF1. CHECKED (`prd.md` FR25 note, L911).

**Stress.** WF2 Stage H, "scenario stress probe", dropped variants that failed "configured stress criteria". The criteria were **never written**. The GPT design talk wanted synthetic data built on real return shapes: bootstrapping, regime simulation and controlled noise. CHECKED (`VAULT\outputs\clash-report-backtest-replay.md:56-59`; `VAULT\07-Source-Material\gpt-trading-algorithm-research.md` ~18715-18740).

**Promotion to paper and live.**
- WF1 ended at a report. WF2 wrote the first registry record and started paper. CHECKED (`prd.md` L355).
- Paper ran about two weeks by default. Per type: scalper 7 trading days, ORB 14, sniper 21, mean-reversion 14. All UI-editable. CHECKED (`VAULT\02-Components\08-paper-trading-demotion-service.md:231-249`).
- Live was only the operator's click. Kelly came from the bot's own paper record, with a probation discount of about 0.85 on first live. CHECKED (`prd.md` FR11, FR63).
- Re-promotion after a demotion needed rolling tier T2 or better on demo, 10 consecutive profitable demo trades, and the operator's click. CHECKED (`08-paper-trading-demotion-service.md:65-73`).

**Mental model (from the GPT talk the operator agreed with):** "Monte Carlo = robustness probe", "Walk-forward = realism filter", and both are filters, not generators. CHECKED (`gpt-trading-algorithm-research.md` ~18678-18690, 18903).

## 1.2 New QMB: what is intended and what exists

**Intended (docs, ratified 21 Aug, extended 14 Sep).**
- A "validation ladder" of library functions: backtest, optimise, Monte Carlo (trade shuffle; candle perturbation seeded from real data), rule-significance test (signals only, against a detrended zero-edge null), and walk-forward. CHECKED (`QMB` L121).
- Thresholds and pass batteries are deferred (GAP-0048/0049, "keep it simple"). The operator confirmed walk-forward and kept PBO/CSCV deferred on 20 Aug. CHECKED (`QMB` L121; `DW\extractions.yaml` ~3711).
- Shuffles and perturbations can only claim "robustness", never "edge". Nothing synthetic validates edge (L20). CHECKED (`QMB` L91, L121).
- Raw measures are stored; pass or fail is computed later against the Book's bar. Composite scores are banned. Trials and replicates can never be read as confirmations. CHECKED (`QMB` L79).
- Costs are calibrated from QMX's own data, never invented: spreads from recorded ticks, slippage from live and paper fills, financing from the broker. Until then every fill carries an "optimistic" taint and cannot claim edge. CHECKED (`QMB` L85-87).
- Optimisation ships with an anti-overfit readout: per-parameter slices, clusters of good regions, and a flag for isolated spike winners. CHECKED (`QMB` L95).
- A named "stress-spread preset" can be a config fragment. CHECKED (`QMB` L67).
- Research-paper is a QMB replay before promotion. Node-paper is Book-level demo on the node. There is no per-bot paper lane on the node. CHECKED (`QMB` L209, L229).
- A replay verdict can never gate live money. CHECKED (`QMB` L25, L79).

**Exists in code (engine/base `f05fc64b`).** Run loop, ledger, fill/spread/slippage/commission/swap ports, Optuna with train/test splits, trade shuffle, candle perturbation, rule significance, walk-forward, sweeps (instruments × timeframes × parameters for one bot), ranking, projection and rerun. CHECKED (`R\01-ground-truth.md` §1.3).

**Missing in code.**
- Every cost port refuses without a calibration artifact, and none exists. CHECKED (`R\01` §1.3).
- Results are in money; per-trade R is not a QMB measure. CHECKED (same).
- No correction for the number of tries. PBO/CSCV is named and deferred. A deflated-Sharpe script sits idle in a workflow template. CHECKED (`R\01` line 43, §2 row 15).
- The reader holds about 16 GB for one month of M1, so scalper-scale tests cannot run yet. CHECKED (`R\01` §1.3).
- Agents cannot reach robustness, walk-forward or sweeps through any tool row. CHECKED (`R\01` §1.3).

## 1.3 Side by side

| Feature | Old QMX (vault + July wiki) | New QMB | Research verdict |
|---|---|---|---|
| Parity replay (same live rules in backtest) | Required, "including known gaps" | One run loop for replay and node (B-2), Book/BMS in the config | **Keep.** Removes the backtest-to-platform gap SQ users fight (`R\03` §5) |
| Cost model | Per-symbol parameters, slippage fitted to journals | Calibration from own ticks and fills; ports exist; **no content yet** | **Cost is the main test for scalpers.** Cheapest strong filter is a cost multiple (`R\03` H18) |
| Cost stress | "Spread/liquidity/cost sensitivity" slice | Stress-spread preset allowed; no rule | **Keep and make it a gate** (2× cost to start) |
| Walk-forward | 6m / 1m, ≥200 OOS trades per window | Mechanics in code; no numbers | **Useful, but weakest of the OOS schemes** (CPCV beat it; `R\05` §6.1). Fine as a realism check, not alone |
| Sealed holdout | Not explicit | `qmf-data` seal with the operator's click | **Strongest single guard:** data the search never saw (`R\05` §7.3) |
| Monte Carlo trade shuffle | Gate: 5th percentile above drawdown band | In code, "robustness only" | **Not a selection test.** A shuffle cannot change total profit. **Use it for sizing and for the live cone** (`R\03` §2.3, H7) |
| Block bootstrap / regime blocks | Not present | Real-seeded block bootstrap allowed | **Better than plain shuffle** for streaky scalpers (SQ MACHR; `R\03` §2.3) |
| Candle / parameter perturbation | Not present | Candle perturbation in code | Weak: "10,000 retests barely flinched on the overfit strategy" (PRACTITIONER, `R\03` §2.3) |
| Rule significance vs zero-edge null | Not present | In code | Useful early filter for "is there any signal", INFERRED; not shown to predict survival |
| Parameter plateau | Not present | Sensitivity readout, spike-winner flag | **Keep.** Judge by the median of neighbours (SPP), not the best point (`R\03` §2.3) |
| PBO / CSCV | In the battery, 0.25 / 0.50 | Named, deferred | **Keep, per family.** Authors suggest rejecting PBO > 0.05 (`R\05` §6.1) |
| Count of tries, deflated Sharpe | Not present | Every trial ledgered; no correction applied | **Most predictive record of all:** more backtests meant a bigger live gap (888 algos; `R\05` §6.2) |
| Minimum trades | 200 per OOS window | None | **Keep, but derive it** from MinTRL in trades (`R\05` §2.4) |
| Results unit | R (expectancy floor 0.15R) | Money | **Use R.** Needed to compare instruments and for MinTRL |
| Session / regime slices | Required slices | Projection can filter trades; no MIS label on backtests | Keep as **descriptions**, never as hindsight filters (`R\03` H3) |
| MAE / MFE | Required output | Not a QMB measure | Keep. Old WF3 used it to spot "fragile" bots |
| Scenario stress (news, gaps, spread blowouts) | Stage H, never specified | Not present | Worth a small set of real event replays, not synthetic data (INFERRED) |
| Synthetic data | Wanted (bootstrap, regime sim) | Allowed for infra and smoke tests only | **Never proof of edge** (L20 agrees with research) |
| Pass/fail storage | Fixed thresholds | Raw measures, verdict at read time | New is better: a rule ruled later re-judges old runs with no rerun |
| Paper before live | Per bot, 7–21 trading days by type | Research-paper in QMB; node-paper per Book; no per-bot paper on node | Operator wants a journal and paper **per unit** (G09 B.15). Incubation is the step practitioners trust most (`R\03` §6 item 5) |
| Meta-test of the tests | Not present | Not present | **Add** (`R\03` H1): measure each test's lift on held-back data |

## 1.4 What old QMX did better, which the new one dropped

1. **It had numbers.** 200 trades, +0.15R, 0.25 / 0.50. QMB has the mechanics but defers every threshold. A test with no bar decides nothing. CHECKED.
2. **It measured in R.** An expectancy floor in R works across instruments and account sizes. QMB measures money. CHECKED.
3. **It put PBO in the battery.** QMB deferred it on 20 Aug for simplicity. The research says it is one of the few tests worth keeping. CHECKED + INFERRED.
4. **It required a minimum trade count per window.** QMB has none. CHECKED.
5. **It required report slices**: session, regime, regime transition, cost sensitivity, MAE/MFE. These are the inputs the router and the decay check need. QMB applies no MIS label to a backtest. CHECKED (`R\01` line 236).
6. **It wanted a stress stage** (Stage H). The intent was right even though it was never specified. CHECKED.
7. **It gave every bot its own paper window and journal** before live, and kept both paper and live journals "live for retrospection and for WF3". The new docs have Book-level paper only. CHECKED (`prd.md` L666; `trading-node.md` DEC-0261 via `R\01` row 5).

## 1.5 What the new QMB does better

1. **It counts every try** (`role = trial`). Old QMX never counted. Research says this record predicts disappointment best. CHECKED.
2. **It labels honesty.** Shuffled, perturbed or synthetic runs can only claim robustness. Old QMX let the Monte Carlo gate pass or fail a bot. CHECKED.
3. **Raw measures, judged later.** Old QMX froze pass/fail at run time. CHECKED.
4. **Costs from real fills,** each calibration fingerprinted. Old QMX fitted a normal curve to slippage. CHECKED.
5. **A sealed holdout** with one final look. CHECKED (`R\01` §1.1).
6. **More tests in code**: rule significance, block bootstrap, sensitivity, sweeps across instruments and timeframes. CHECKED.
7. **Reproducible runs** by fingerprinted config, as old QMX also wanted (bot version, data snapshot, config hash, seed). CHECKED.

## 1.6 Recommended QMB test set

Goal: few tests, each one known to catch overfitting, run cheap to expensive, stop at the first failure. QMB measures and publishes. It never benches or promotes. Live trading stays out of QMB.

**Always on (a record, not a test).**

**T0. The tries ledger and deflated Sharpe.**
- Every QMB run on a unit's family counts as a try: optimiser trials, agent retries, What-If ideas turned into rules, new instrument cells.
- Every headline number shows "best of N effective tries" and a deflated Sharpe.
- *Example:* 100 variants, 500 trades each. One trade's Sharpe has a standard error of about 1/√500 ≈ 0.045. The best of 100 pure-luck variants is about 2.5 standard errors up, so luck alone reaches about 0.11 per trade. A best variant at 0.12 has barely beaten luck. INFERRED arithmetic.
- Home: compute in QMB `robustness/`, record in the Library families ledger, and move the idle template script there (`R\05` §6.5).

**The five tests, in order.**

| # | Test | Catches | Starting rule (all configurable) | Example |
|---|---|---|---|---|
| T1 | **Cost stress** | Edges that are really spread | Net expectancy > 0 at 1× calibrated cost **and** at 2× cost | Gross +0.20R, cost 0.08R: net +0.12R at 1×, +0.04R at 2× → pass. Gross +0.12R, cost 0.08R: +0.04R at 1×, −0.04R at 2× → fail |
| T2 | **Out-of-sample in R** (walk-forward test months plus the sealed holdout) | Curve fitting in time | Test expectancy ≥ +0.15R after cost, ≥ 200 test trades in total, holdout expectancy > 0 | Train Jan–Jun, test Jul, slide monthly. Joined test months +0.18R over 420 trades; holdout +0.09R over 160 trades → pass |
| T3 | **Plateau** (median of neighbours) | A lucky parameter point | Median expectancy of the parameter neighbourhood > 0 after cost; no "isolated spike" flag | Stop = 10 pips gives +0.15R, but 8 and 12 pips give −0.02R and +0.01R: the median is about 0 → fail (a needle, not a plateau) |
| T4 | **PBO on the family** | Picking the luckiest of many variants | Run when the family has ≥ 10 effective tries. PBO ≤ 0.25 pass, > 0.50 dead (old values); the paper's stricter 0.05 is an option | 20 variants, 16 slices: the train winner is below the test median in 45% of splits → PBO 0.45 → do not promote |
| T5 | **Block-bootstrap Monte Carlo, for size only** | Not overfitting. It sets the risk the unit can carry and draws the live cone | 1,000 runs of resampled trade blocks (block of 5 trades). Output: drawdown at 95% confidence and the cumulative-R cone. **Not a pass/fail gate** | 300 test trades → 95% drawdown 9R. With an account limit of 20R, risk per trade can be up to about 2.2× the base unit. The cone after 100 trades: 5th percentile +2R, median +10R |

**Optional, when a unit needs it.**
- **Event replays:** five to ten real days with news spikes, gap opens or spread blowouts on the unit's instruments. The rule: no single event loses more than a set number of R (start at 3R). This is the old Stage H intent, done with real history, not synthetic data. INFERRED.
- **Rule significance** as a cheap first filter for raw ideas. INFERRED.

**Drop as gates.**
- Trade-shuffle Monte Carlo as a pass/fail test (keep it for sizing only).
- What-If filters (they become hypotheses that need unseen data).
- Candle and parameter perturbation as gates.
- Composite robustness scores.
- Reason: no lift in practitioner meta-tests and none in the research. CHECKED (`R\03` §2.3, §5).

**Keep the tests honest (monthly job).** Run the "test of the tests" (`R\03` H1): take all candidates from a month, measure what share are profitable on a later held-back period, then measure that share among those that passed each test. A test that shows no lift for a bot type gets dropped. *Example:* 30% of all candidates are profitable later, and 31% of those that passed T3 are. T3 adds nothing for that bot type. INFERRED.

**Output: the baseline card.** When a unit passes, QMB freezes one card in the Library. The live decay check reads it later. The card holds:
- expectancy per trade in R from the **holdout**, already deflated (not the in-sample number);
- its standard deviation and standard error;
- the T5 cone and the 95% drawdown;
- cost per trade in R, and slippage per trade in R;
- trades per week;
- win rate and MAE/MFE in R;
- the effective tries count.

INFERRED. This card is the "certified footprint" the July clash report proposed. CHECKED (`VAULT\outputs\clash-report-alpha-decay.md` §3).

**What QMB needs first** (from §1.2): calibrated costs, per-trade R, a windowed reader for M1 and ticks, and an agent door for robustness and walk-forward. Without these the set cannot run. CHECKED (`R\01` §1.3).

---

# Job 2: Alpha decay

## 2.1 WF3, recovered

**Name and number.** WF3 = "pool cleaning". It is the alpha-decay workflow. **WF5 does not exist,** and WF4 was deleted as a phantom. CHECKED (`VAULT\02-Components\07-bot-registry-and-lifecycle.md:160`; `G09` A.10).

**Two circuit breakers.** The April brainstorm named them: an **acute** one (two strikes in a day, on the trading node) and a **chronic** one (WF3). CHECKED (`VAULT\bmad-docs\brainstorming\brainstorming-session-2026-04-28-125147.md:131`).

**The acute breaker (daily).**
- Triggers: a loss streak past the bot's threshold; fees for the day above a share of the daily budget; failing to recover from a drawdown N times in a session; or the rating tier dropping mid-session. CHECKED (`VAULT\02-Components\02-circuit-breaker-policy-engine.md:46-51`).
- First hit: keep trading. Second hit in the window: route the bot to the demo account. At daily rollover: reset the count and put demoted bots back in paper. CHECKED (same, 19-21; `08-paper-trading-demotion-service.md:41-47`).

**The rating feed (DPR).** A score 0–100 from six weighted parts, recomputed at every session end, with tiers T1 80–100, T2 50–79, T3 0–49. It kept a rolling 10-session tier history, the "modal" tier, and a count of consecutive T3 sessions. WF3 read the rolling stream. CHECKED (`VAULT\02-Components\06-performance-rating-service.md`; `VAULT\outputs\alpha-decay-spec.md` §3).

**When WF3 ran: two cadences in the sources.**
- **Daily:** the "Dead Zone", about three hours a day with no session open. Journals synced from the node to cold storage, then WF3 read them and found decayed bots. CHECKED (`VAULT\04-Integration-Flows\03-integration-flows.md:287-336`; `VAULT\07-Source-Material\README.md:50`).
- **Fortnightly:** the April brainstorm decided "WF3 fortnight cadence (NOT in dead zones); dead zones for self-assessment". The PRD kept "fortnight". CHECKED (brainstorm D7, line 111; `prd.md` FR27).
- My reading: **daily decay spotting** ran in the dead zone (self-assessment), and the **actions** (demote, retire, rehab) ran fortnightly. That matches the operator's memory of a daily check. INFERRED.

**The pipeline (stages D0–D6).** CHECKED (`12-wf3-pool-cleaning.md:44-55`):

| Stage | What it did |
|---|---|
| D0 | Wait for the dead zone and for the journal sync to finish |
| D1 | Build the candidate set from registry, trade journals and DPR |
| D2 | Score decay per bot, with a written rationale |
| D3 | Split each candidate's drawdown (Riskfolio-Lib, allowed only here) |
| D4 | Choose a branch per bot from the scores and the split |
| D5 | Apply the branch through the deterministic registry |
| D6 | Hand rehab candidates to a mini-WF2 |

**The evidence D2 used.** Four named kinds, CHECKED (`alpha-decay-spec.md` §2):
1. **Circuit-breaker fire density:** fires per rolling window.
2. **MAE/MFE drift:** for example, a high win rate but average MAE creeping toward the stop ("fragile" bot). CHECKED (`VAULT\02-Components\10-trade-journal-service.md:273`).
3. **DPR drawdown context.**
4. **Regime and session overlays:** performance by regime and session.

The journal gained fields for this: `mae`, `mfe`, `realized_rr_rolling_20`, `realized_rr_rolling_50`, `regime_label_at_open`, `session_id`, `overlap_id`. CHECKED (`10-trade-journal-service.md:269-281`).

**The branches.** CHECKED (`alpha-decay-spec.md` §5; `07-bot-registry-and-lifecycle.md:314-332`):
- **keep:** nothing crossed.
- **reduce weight** (soft trigger): tag `decayed`, still live at lower weight, "on watch". At the next window: recovered → full; still decaying → demo.
- **demote to demo** (hard trigger).
- **retire** (hard trigger): final. A comeback needs a new bot version with a parent link. Also fired when every rehab child failed.
- **rehab:** a mini-WF2 makes child variants while the parent sits on demo. A child that works brings the parent back through probation.

**What was never written.** No decay formula, no weights, no window lengths, no thresholds, no drawdown sub-metrics. CHECKED (`alpha-decay-spec.md` §2, §8). The new docs record two independent sources agreeing it is unrecoverable, and rule "design it fresh" (DEC-0092, GAP-0045). CHECKED (`DW\extractions.yaml` ~1845; `DW\ratification-packet.md:98, 208`).

**What the July rethink added** (unratified, but useful):
- **Decay = live behaviour drifting from the certified backtest footprint,** measured, not a weighted score. CHECKED (`VAULT\outputs\clash-report-alpha-decay.md` §3).
- **Sense, do not dispose:** the decay service informs; the Book door, the rules or the operator act. CHECKED (same §4).
- **Compare in R, and refuse a comparison across mismatched groups.** CHECKED (`DW\extractions.yaml` ~3613, paper package rider).
- **Keep collecting:** paused or news-blocked bots keep running on paper "so alpha-decay data keeps flowing". CHECKED (`DW\extractions.yaml` ~1051, ~1299).
- The operator's own definition: decay is "when a [strategy] defaults below its backtested results". CHECKED (`DW\extractions.yaml` ~2325).

## 2.2 How others detect a dying edge

**StrategyQuant QuantAnalyzer.**
- *Predict & Verify:* project the Monte Carlo runs forward as a band; from a chosen date, check whether live equity stays inside. Outside the band → "consider stopping this strategy". CHECKED: https://strategyquant.com/doc/quantanalyzer/predict-verify-strategy-performance-using-monte-carlo-simulation/ . Users load live results and set the verify date to the go-live day. CHECKED: https://strategyquant.com/forum/topic/monte-carlo-verify-function/ .
- *Compare Results:* bulk side-by-side of live and backtest by name or magic number. SQ's own rule of thumb: if about 80% of trades match, the logic is fine; live at 70–100% of backtest profit is normal; at 30% investigate (often slippage or liquidity). Checks at the end of a ~3-month test period, then yearly. CHECKED: https://strategyquant.com/blog/real-trading-compare-live-strategy-results-backtest/ .
- *Practice:* users run about 200 systems on demo and live across 30+ accounts and swap them by hand. Fewer than 10% trade like their backtest. PRACTITIONER (`R\03` §2.3).

**QuantConnect.** Runs an out-of-sample backtest in parallel with every live deployment and overlays the two equity curves. Gaps are explained as data differences, fill and fee modelling error, market impact, or different start parameters. CHECKED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/reconciliation .

**Prop firms and pod shops.**
- Topstep's "shoulder tap": a live trader is moved back to a simulated account after **patterns** (repeated daily-loss hits, big drawdown of seed capital, risk imbalance), never for one bad day. They return to live after showing consistency, never automatically. CHECKED: https://help.topstep.com/en/articles/13747178-live-funded-account-call-up-and-call-down-process .
- Pod shops: a reported ladder at Millennium is about 5% drawdown → capital halved, about 7.5% → wound down. The figures come from one source (Net Interest, 2023) and the reference point is not public. PRACTITIONER: https://hedgefundinterview.com/pod-shop-risk-limits .
- Retail prop practice: size zones by how much of the loss limit is used (0–30% full size, 30–60% half, 60–80% micro, 80%+ stop). PRACTITIONER: https://bestprops.com/drawdown-rules-explained/ .
- My reading: prop practice is **bleeding control** (loss ladders) plus **call down to sim**, which is the old QMX demote-to-demo. It is not decay detection. INFERRED.

**Sequential tests.**
- **CUSUM** (Page, 1954): each trade, add how far it fell short of the expected R, minus a small allowance. Never go below zero. Alarm when the total passes a limit. It is the fastest test for a drop in the mean at a given false-alarm rate. CHECKED: https://www.edgekit.pro/tutorials/live-monitoring , https://mathandmarkets.com/p/detecting-decay-in-real-time-when .
  - *Example:* expected +0.10R per trade, allowance 0.05R. Trades of −1R, +1R, −1R add 1.05, then fall back to 0, then add 1.05 again. Wins drain the total and losses fill it. Limit 19.5 → about one false alarm per 1,000 healthy trades. If the edge falls to 0, the alarm comes after about 240 trades on average. INFERRED (formula plus simulation).
  - The limit is set from the false-alarm rate you accept, not tuned on the live record. PRACTITIONER (moltbook post above).
- **A big single loss is nearly blind to decay.** In one simulation a "one loss worse than 3 SD" rule took 764 trades to fire on a dead strategy, against 1,012 on a healthy one. Keep it as a blow-up breaker only. PRACTITIONER (moltbook post).
- **Rolling window and t-test:** compare the last 50 trades' mean R with the prior 200. Simple, but about 25% slower than CUSUM at the same false-alarm rate. PRACTITIONER: https://trading.glass/en/academy/trading-intelligence/advanced-statistical-thinking/edge-degradation ; moltbook post.
- **Bayesian change-point (BOCPD):** gives a probability that a change happened. More power, more parts. CHECKED (mathandmarkets above).
- **E-processes:** evidence you may check after every trade without breaking the error rate. Best for "loosen only on proof". CHECKED (`R\05` §7.2).
- **Stacked alert levels** are common: green; yellow (CUSUM above 70% of its limit → size down); orange (alarm → stop new trades); red (several alarms → paper until re-proven). PRACTITIONER (mathandmarkets above).

**Traps everyone names.**
1. **The expected value must come from the holdout, not the in-sample backtest.** Otherwise the alarm fires on the overfit gap, which looks exactly like decay. Treat an alarm in the first few hundred live trades as "the holdout was optimistic" before calling it decay. PRACTITIONER (moltbook post) + INFERRED.
2. **Loss streaks are normal.** At a 55% win rate, a 10-loss streak appears in about 30% of 200-trade windows. PRACTITIONER (trading.glass above).
3. **Check inputs as well as outputs:** fills, trade frequency and holding time often drift before profit does. PRACTITIONER: https://www.luxalgo.com/library/concept/live-decay-tracking/ .
4. **Watch the upside too:** results far better than expected usually mean a sizing bug or hidden beta. PRACTITIONER (edgekit above).

## 2.3 Recommended decay check, per unit journal

**The journal.** One append-only journal per unit, from creation to retirement. Every row carries a stage tag: `backtest`, `stress`, `research-paper`, `node-paper`, `live`. Journals keep running when the unit is paused or blocked, on paper, so evidence keeps flowing. INFERRED from the operator's wish and the July rider.

Each trade row holds, at minimum:
- R result, cost in R, slippage in R;
- MAE and MFE in R;
- session, instrument, timeframe, and the MIS state at entry;
- whether a replay of the same day would have taken the same trade (for signal drift).

The fill importers and the Library `trade` item already give a base. CHECKED (`R\01` line 430: `qmf-data/importers/journal.py`).

**The baseline.** The QMB baseline card from §1.6, frozen at promotion. It is never refitted on live data. A new card means a new unit version. INFERRED.

**The nightly job.** Runs once a day after the last session closes: the old dead-zone slot, used for sensing only. INFERRED. Four readings:

| # | Reading | How | Starting setting (configurable) | Example |
|---|---|---|---|---|
| D1 | **Edge alarm (CUSUM on R)** | Each trade adds (baseline R − trade R − allowance). Floor at zero | Allowance = half the drop you care about (0.05R for a 0.1R drop). Limit set for about 1 false alarm per 1,000 trades (≈19.5 when trade SD is 1R) | Baseline +0.10R. The edge dies at trade 0; the alarm fires around trade 240 |
| D2 | **Outside the cone** | Cumulative live R against the baseline Monte Carlo cone for the same trade count | Below the 5th percentile | After 100 live trades the cone's 5th percentile is +2R. Live is −3R → outside |
| D3 | **Cost and fill drift** | Live cost per trade in R and slippage in R against the card | Live cost > 1.5× card cost over the last 50 trades | Card cost 0.06R; last 50 trades average 0.11R → drift. This also feeds QMB's slippage calibration |
| D4 | **Behaviour drift** | Trades per week and replay match rate against the card | Trade rate outside 0.5×–2× of the card; replay match below 80% | Card 40 trades a week; live 12 a week for two weeks → the unit no longer sees its setups |

**States, not scores.** No weighted decay score (the old vault never had one, and DEC-0162 bans composites).
- **OK:** nothing fired.
- **Watch:** D1 above 70% of its limit, or any one of D2–D4 fired. *Suggested action:* hold size, no loosening, no new instruments.
- **Alarm:** D1 fired, or two of D2–D4 fired. *Suggested action:* back to paper, keep the journal running, and hand it to a rehab or research workflow.

The check **informs**. Who acts stays as today's docs say: the Book door, the unit's own rules or the operator. Going back to live is the operator's click, as in old QMX. CHECKED (`QMB` L25; `08-paper-trading-demotion-service.md:65-73`).

**Kept separate.** Fast loss rules (daily loss, loss points per session, the kill switch) stay on the node and act at once. The decay check never replaces them, because it needs hundreds of trades (§0 correction). INFERRED; `R\05` §4.6 reaches the same split.

**Loosening after an alarm.** Only on new evidence: an e-value on trades after the alarm crosses 1/α (for example 20 at α = 0.05), plus a minimum time. *Example:* after going back to paper, the unit bets its evidence on "edge > 0". Each good trade multiplies the score up and each bad one down. When the score passes 20, the evidence is strong enough. INFERRED (`R\05` §4.6, §7.2).

**Where it runs.** A small read-only job over the journals, outside QMB and outside the node's hot path. QMB only supplies the frozen card and later recalibrates costs from the drift. INFERRED.

**What it fixes from old WF3.**
- It has a formula (CUSUM and the cone), where WF3 had none.
- It uses R and the unit's own frozen baseline.
- It covers paper and live alike.
- It keeps "sense" and "act" apart.

INFERRED.

---

## 3. Numbers in this file (all configurable starting points)

| Number | Source | Where it lives |
|---|---|---|
| Train 6 months / test 1 month | CHECKED, WIKI registry | QMB walk-forward |
| ≥ 200 test trades | CHECKED, WIKI registry | QMB T2 |
| Test expectancy ≥ +0.15R after cost | CHECKED, WIKI registry | QMB T2 |
| Cost stress 2× | INFERRED from `R\03` H18 | QMB T1 |
| PBO pass ≤ 0.25, dead > 0.50 (strict option 0.05) | CHECKED, WIKI registry; `R\05` | QMB T4 |
| PBO runs from ≥ 10 effective tries | INFERRED | QMB T4 |
| Monte Carlo 1,000 runs, block of 5 trades, 95% drawdown, 5th-percentile cone | CHECKED (old 1,000); SQ MACHR default 5 | QMB T5 |
| Event replay loss cap 3R | INFERRED | QMB optional |
| Paper window 7 / 14 / 21 / 14 trading days by type | CHECKED, vault | unit paper stage |
| Re-promotion: 10 profitable demo trades, tier ≥ T2 (old) | CHECKED, vault | historical reference |
| CUSUM allowance 0.05R, limit ≈ 19.5 (about 1 false alarm per 1,000 trades) | INFERRED, Siegmund formula + simulation | decay D1 |
| Watch at 70% of the CUSUM limit | PRACTITIONER | decay states |
| Cost drift 1.5× over 50 trades | INFERRED | decay D3 |
| Trade-rate band 0.5×–2×; replay match ≥ 80% | INFERRED; SQ 80% rule | decay D4 |
| E-value loosen threshold 1/α = 20 | CHECKED method (`R\05`) | loosen gate |

## 4. Not verified

- The old code was lost in the crash. Old behaviour is known only from the vault and wiki docs.
- The "daily spot, fortnightly act" reading of the two WF3 cadences is my inference from two documents that disagree.
- QMB behaviour was read from docs and `R\01`, not run.
- The pod-shop drawdown numbers rest on one press source.
- The CUSUM delays assume independent trades with an SD of 1R. Streaky trades shorten the false-alarm spacing, so the limit should be set from the holdout's own autocorrelation.
