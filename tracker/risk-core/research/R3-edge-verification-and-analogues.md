# R3: Proving an edge is real, and what other fields teach about many brakes and many variables

Written 2026-11-03 for the risk-core design session. Research only: it reports evidence and does not design QMX. Nothing here is ratified.

## How to read this

- **Labels.** Every claim cites a URL or a `path:line`. **READ** means I read the page itself in the built-in browser, or downloaded the document and extracted its text. **SNIPPET** means I saw the claim only as a search excerpt, so treat it as unconfirmed. **[arithmetic]** marks numbers I computed. **[judgment]** marks my opinion.
- **Scripts.** `D:\QMX-worktrees\risk-plan\tracker\risk-core\research\R3-scripts\edge_numbers.py` computes every [arithmetic] number. `...\R3-scripts\pdftext.py` is the standard-library PDF text extractor I used on downloaded PDFs. Run both with `python -I`. The edge maths assumes independent trades that win +1R or lose −1R.
- **Short paths.**

| Alias | Path |
|---|---|
| `R05` | `D:\QMX-worktrees\risk-plan\tracker\risk-sizing\research\05-academic.md` |
| `R08` | `D:\QMX-worktrees\risk-plan\tracker\risk-sizing\research\08-old-qmx-testing-and-decay.md` |
| `R26` | `D:\QMX-worktrees\risk-plan\tracker\risk-sizing\research\26-quant-judging.md` |
| `R2` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\research\R2-trader-practice-windows-drift-isolation-breadth.md` |
| `G7`, `G8` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\grounding\G7-unit-inputs-qmb-mis-instruments.md`, `...\G8-unit-chassis-and-extensibility.md` |
| `OW` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\seeds\operator-words-2026-11-03.md` |
| `SEEDS` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\seeds\SEEDS.md` |

- **Not redone here.** These are already covered and I only cite them: the toolset (deflated Sharpe, PBO, White's Reality Check, Hansen's SPA, the Harvey-Liu haircut, CPCV, MinTRL) at `R05:309-357`; online testing, e-values and alpha-investing at `R05:359-393`; old QMX test numbers and the decay check at `R08:29-44`, `R08:283-327`; the seven judging steps and counting tries by result stream at `R26:54-126`; SPRT, CUSUM, the CFM drawdown test and breadth at `R2:75-124`, `R2:191-224`; what QMB's judge (B13) already outputs at `G8:302-322`.

## Short answer

1. **Proof costs trades, and the cost grows with one over the edge squared.** A unit that wins 55% at 1:1 needs about 610 trades for an 80% chance of proving its edge at 95% confidence. At half that edge (52.5%) it needs about 2,470. That is the whole reason "half the edge" changes the picture: the same test takes four times as long **[arithmetic]**.
2. **"Ten times faster" is calendar time, not proof per unit.** Ten units at 4 trades a day reach 610 trades in about 15 days instead of 153. That holds only if the ten units test the same claim and trade independently **[arithmetic]**. Correlated units count as fewer (`R2:200`).
3. **Planning at half the believed edge matches the evidence.** Published anomalies lose 26% out of sample and 58% after publication (`R05:331`). The Harvey-Liu haircut is above 50% for Sharpe ratios under 0.4 (`R05:320`). Backtests overstate live results (`R05:326-328`).
4. **Checking every day breaks a fixed 95% test.** Five looks at the usual 1.96 bar give a 14% false-pass rate instead of 5% **[arithmetic]**. Trials fix this with pre-planned looks and stricter early bars (FDA 2019, READ). A trial-style plan of five looks at 200-trade steps stops a dead unit after about 650 trades on average **[arithmetic]**.
5. **Banks sort test results into three zones, not pass and fail.** Basel says no single cutoff can both protect good models and catch bad ones, so it uses green, yellow (ask for more information) and red (automatic) (BIS 1996, READ). An accurate model still lands in yellow about one year in nine.
6. **Clinical trials size up the way QMX could size up a unit.** Dose finding starts at the lowest dose, raises it one step only while the observed harm rate stays low, steps down when it is high, and removes doses that are clearly too toxic (FDA review of BOIN, READ).
7. **Giving more money to whatever is winning is risky.** Adaptive randomisation often put more patients on the worse arm and overstated the effect. The authors prefer fixed allocation plus planned stopping rules (Thall, Fox and Wathen 2015, READ).
8. **Every field with many brakes uses the same few tricks.** The nearest brake acts first and the next one waits a set time (power grids). The system retries a few times before it locks out (reclosers). It sheds load in stages (frequency load shedding). It alerts only when action is needed, one alert at a time (aviation). It alerts on the burn rate over two windows (Google SRE). Insurers count many losses inside one time window as a single event (the hours clause). Each is cited in §3.
9. **Alarms that fire too often get ignored.** In hospitals 85 to 99% of alarm signals need no clinical action, and staff then turn alarms down or off (Joint Commission 2013, READ).
10. **Many variables are tamed with three structures:** defaults with overrides (pysystemtrade, READ), classes and buckets with a catch-all bucket (ISDA SIMM, READ), and a standard code for each instrument (ISO 10962 CFI, READ). Styles are better grouped by how their returns behave than by their labels (Brown and Goetzmann; Fung and Hsieh, READ).
11. **SR 11-7 is gone.** The Fed replaced it on 17 April 2026 with SR 26-2. The new text still asks for outcomes analysis against thresholds, ongoing monitoring, independent challenge and a model inventory. It also names aggregate risk from models that share assumptions (Fed, READ).

---

## 1. Edge verification

### 1.1 Why "half the edge" and "ten times faster" (he asked, `OW:79`)

**The idea in plain words.** Each trade is mostly noise. A 1:1 trade moves about ±1R, and the edge is a small tilt, for example +0.1R. After n trades the noise in the average shrinks like 1 ÷ √n. You can only "see" the tilt once it is a few noise-widths tall. So the trades you need grow with (bar ÷ edge)². Halve the edge and you need four times the trades.

**One line of maths.** For a ±1R trade that wins with probability p, the edge is 2p − 1 and the per-trade Sharpe is (2p − 1) ÷ √(1 − (2p − 1)²). Trades needed ≈ ((z_confidence + z_power) ÷ Sharpe)². At 55%: ((1.645 + 0.842) ÷ 0.1005)² ≈ 612.

| Unit (1:1 payoff) | Edge per trade | MinTRL 95% (50% power) | t > 3 bar (Harvey, Liu and Zhu) | 95% with 80% power | Deflated, best of 10 tries | Deflated, best of 100 tries |
|---|---|---|---|---|---|---|
| 55% wins, as believed | +0.10R | 274 | 891 | 612 | 1,026 | 1,726 |
| 52.5% wins, half the edge | +0.05R | 1,086 | 3,591 | 2,467 | 4,136 | 6,956 |
| 51% wins, a fifth of the edge | +0.02R | 6,768 | 22,491 | 15,450 | 25,902 | 43,569 |

All [arithmetic] (`R3-scripts/edge_numbers.py`, block 1). MinTRL matches `R05:131-135`. The "t > 3" column uses Harvey, Liu and Zhu's hurdle for a new finding after data mining: "a t-ratio greater than 3.0" instead of 2.0 (https://www.nber.org/papers/w20592, READ). The "deflated" columns raise the bar by the luck of the best of N tries. The best of 10 pure-luck tries sits about 1.57 standard errors up, and the best of 100 about 2.53 (DSR approximation, `R05:315`; [arithmetic]).

**Calendar time** [arithmetic] (block 2), for the 80%-power count:

| Unit | 1 trade a day | 4 a day | 10 units × 4 a day | 40 units × 4 a day |
|---|---|---|---|---|
| 55% wins | 612 days | 153 days | 15 days | 4 days |
| 52.5% wins | 2,467 days | 617 days | 62 days | 15 days |

This is what "ten units reach whatever the true edge says ten times faster" means (`D:\QMX-worktrees\risk-plan\tracker\risk-core\STATE.md:45`; the sim is in `SEEDS:565`). Two limits apply **[judgment]**:
- Pooling speeds up proof of a **shared** claim, such as "this logic has an edge on USD pairs". Each unit's own edge still needs its own trades.
- Correlated units are fewer bets: N_eff = N ÷ (1 + (N − 1)ρ) (`R2:200`). Ten units at ρ = 0.3 prove at the speed of 2.7 units.

**Why plan at half the believed edge.** The believed edge comes from a backtest, and backtests overstate. The evidence already gathered: backtest Sharpe barely predicts live Sharpe (`R05:326`); published anomalies lose 26% out of sample and 58% after publication (`R05:331`); the multiple-testing haircut is above 50% for Sharpe ratios under 0.4 (`R05:320`). So half the believed edge is a realistic planning case, not a pessimistic one **[judgment]**.

### 1.2 The tools, priced in trades

| Tool | Question | What it needs | Rough trades for a 55% unit | Where QMX stands |
|---|---|---|---|---|
| MinTRL | Is this one record long enough? | the record's mean, spread, skew and kurtosis | 274 (coin-flip power) | maths in `R05:127`; not wired |
| Harvey-Liu-Zhu bar | Is this finding above the data-mining bar? | a t-statistic | 891 | not used |
| Deflated Sharpe | Is the best of N tries above best-of-N luck? | the try count and the spread of Sharpe ratios across tries | 1,026 at N = 10 | B13 records effective tries (`G8:309`) |
| PBO by CSCV | Does the in-sample winner fall below the median out of sample? | every variant's returns on a shared clock, cut into S slices | 16 slices give 12,870 splits; at 1,000 trades that is about 62 trades a slice **[arithmetic]** | named, deferred (`R08:115`) |
| White's Reality Check, Hansen's SPA | Is the best of a universe better than a benchmark after snooping? | every tried variant's return series and a bootstrap | same order as the deflated Sharpe **[judgment]** | not built (`R05:318-319`) |
| Walk-forward | Do settings fitted on older data work on newer data? | train and test windows | old QMX: 6 months train, 1 month test, 200 test trades or more (`R08:31`) | mechanics built (`R26:63`) |
| Paper | Does it work on trades that did not exist when it was frozen? | frozen code, live quotes | old QMX: 7 to 21 days by type (`R08:73`); shipped default 30 trades or 4 weeks (`R26:84`) | paper scoring built (`G8:311`) |
| SPRT | Edge 0 or edge 0.1R, stopping as soon as evidence suffices? | a chosen pair of edges | about 540 on average (`R2:27`) | not built |
| CUSUM | Did the edge drop? | a baseline from the holdout | about 240 to flag +0.1R → 0 (`R08:42`) | designed (`R08:301`) |

**Reading [judgment].** Every test costs hundreds to thousands of trades for an edge near 0.1R. No test proves a thin edge in days. The fast checks are inputs (costs, fills, trade rate), as `R2:123` and `R08:303-304` already say.

### 1.3 The peeking problem

- Looking at a fixed 95% test after every batch of trades inflates false passes. With five looks at 1.96, a dead unit "passes" 14% of the time instead of 5% (block 8, [arithmetic]).
- The FDA states the same for trials: testing at each interim look at the usual level "would inflate the Type I error probability" (FDA 2019 guidance, §V.A, https://www.fda.gov/media/78495/download, READ).
- The fixes are a pre-planned look schedule with a stricter early bar (§2.2), or evidence that may be checked at any time, such as e-values (`R05:368`).

### 1.4 How regulated and professional shops run verification as a pipeline

**Basel backtesting traffic light** (BIS 1996, https://www.bis.org/publications/199601-standards-supervisory-framework-use-backtesting-conjunction-internal-models-approach-market-risk-capital.pdf, READ, pp. 6-8 and Tables 1-2):
- A bank counts days when its loss beat its 99% risk estimate, over 250 days.
- Zones: 0-4 green, 5-9 yellow, 10 or more red. The yellow zone starts where the chance of seeing that many or fewer reaches 95%. The red zone starts at 99.99%.
- The reason for three zones: "there is no threshold number of exceptions that yields both a low probability of erroneously rejecting an accurate model and a low probability of erroneously accepting all of the relevant inaccurate models" (p. 7).
- Yellow means the supervisor asks the bank for more information before acting, and penalties are "not meant to be purely automatic" (p. 8). Red brings an automatic penalty.
- Causes are sorted into four kinds: the model's basic integrity, an imprecise model, bad luck or unexpected markets, and intraday trading (p. 8).
- Worked numbers [arithmetic] (block 4): an accurate model lands in yellow or red 10.8% of years. A model that is really at 97% still lands green 12.8% of years. The BIS table shows the same trade-off (Table 1: a 97% model escapes a 7-exception cutoff 37.5% of the time, READ).

**US model risk guidance (SR 26-2, which replaced SR 11-7 on 17 April 2026)** (https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm and attachment https://www.federalreserve.gov/supervisionreg/srletters/SR2602a1.pdf, READ):
- Outcomes analysis "compares model outputs to corresponding real-world outcomes". "Persistent deviations outside of the banking organization's established performance thresholds" can warrant "model adjustment, recalibration, or redevelopment" (attachment p. 9).
- Ongoing monitoring checks whether a model still performs "given potential changes in products, exposures, activities, clients, data relevance, or market conditions" (p. 9).
- "Effective challenge" needs expertise, "sufficient independence" and the standing to force change (p. 5).
- Aggregate model risk comes from "reliance on common assumptions, data, or methodologies" that "could adversely affect several models ... simultaneously" (p. 5). That is the losing-together problem in bank words.
- Banks keep a model inventory with "sufficient information to understand model risks" (p. 11).

**Numerai, a live-only payout tournament** (https://docs.numer.ai/numerai-tournament/staking, READ):
- Payouts and burns come from scores on live rounds. Simulated returns "never affect payouts or balances".
- New users are told to start unstaked or small, because "Validation metrics are easy to overfit". They should let out-of-sample scores show the model is ready before staking much.
- Numerai scores daily and settles each round after its final scoring day.

**Google's canary releases** (https://sre.google/workbook/canarying-releases/, READ):
- A canary is "a partial and time-limited deployment of a change in a service and its evaluation". The rest of the service is the control.
- It must be "sizeable and last long enough to be representative".
- Metrics must be split by canary and control. A 5% canary failing 20% of requests shows as only 1% in a whole-service view.
- The evaluation feeds the release process, which can stop or roll back.

**WorldQuant BRAIN** (SNIPPET only). Community repositories report automated gates on Sharpe, "fitness", turnover and self-correlation below 0.7. I found no official public list (search results, e.g. https://github.com/RussellDash332/WQ-Brain). Do not rely on the numbers.

**QMX today.** The seven-step sequence is in `R26:56-68`. B13 already writes a verdict with effective tries, a baseline card and a paper score (`G8:309-311`). None of it reaches the sizer (`G8:316`).

---

## 2. Clinical trials as an analogue

### 2.1 Phases

From FDA, https://www.fda.gov/patients/drug-development-process/step-3-clinical-research (READ):

| Phase | People | Length | Purpose | Share that moves on |
|---|---|---|---|---|
| 1 | 20 to 100 | several months | safety and dosage | about 70% |
| 2 | up to several hundred | months to 2 years | efficacy and side effects | about 33% |
| 3 | 300 to 3,000 | 1 to 4 years | efficacy and adverse reactions | 25 to 30% |
| 4 | several thousand | after approval | safety and efficacy | n/a |

**Mapping [judgment].** Phase 1 asks "does it break things at a small dose?": a unit at minimum size. Phase 2 asks "does it work?": paper or micro size. Phase 3 confirms: full size after a planned test. Phase 4 is surveillance: live decay monitoring. Most drugs die early, which matches "most units should die in the first three steps" (`R26:23`).

### 2.2 Group sequential designs: stopping early for success or futility

From the FDA 2019 guidance, §V.A (https://www.fda.gov/media/78495/download, READ):
- Interim looks are "prospectively planned" and stopping criteria are "prespecified".
- Trials may stop for efficacy or for futility ("unlikely to demonstrate efficacy").
- O'Brien-Fleming "tends to require very persuasive early results". Pocock requires less and stops early more often.
- Lan-DeMets alpha spending lets looks happen at calendar times rather than fixed sample sizes.
- One interim look with an O'Brien-Fleming bound cuts the expected sample size by about 15%.
- Futility rules are often "nonbinding": guidelines that may or may not be followed. Adding them does not raise the false-positive rate. Binding futility rules allow a looser final bar but must always be followed.

Five-look boundaries (two-sided 0.05): O'Brien-Fleming z = 2.04 ÷ √(k/5), so 4.56, 3.23, 2.63, 2.28, 2.04; Pocock 2.41 at every look. The constants came from search excerpts (SNIPPET, e.g. https://eclass-b.uoa.gr/modules/document/file.php/MATH301/PracticalSession3/LanDeMets.pdf). I checked both by simulation: overall false-positive rates 0.0496 and 0.0502 (block 8, [arithmetic]).

**A trial-style plan for one unit** [arithmetic] (block 3): looks every 200 trades, at most 1,000. Efficacy uses O'Brien-Fleming. The non-binding futility rule is "stop if the running mean is below zero at look 2 or later".

| True edge | Proved | Stopped as futile | Undecided at 1,000 | Average trades used |
|---|---|---|---|---|
| 0 | 2.5% | 69% | 28% | 646 |
| +0.05R (half) | 34% | 21% | 46% | 832 |
| +0.10R (as believed) | 87% | 3% | 11% | 734 |

**Mapping to "bad day or broken edge" [judgment].**
- A bad day is one look's worth of data or less. Trials never stop on one patient. The first look needs z = 4.56, so early evidence must be overwhelming.
- A broken edge is what futility rules catch: accumulated evidence that the goal is out of reach. They act at planned looks, not on a single result.
- The "undecided" column is real. At half the edge, nearly half of plans end without a verdict at 1,000 trades. That is the trade-count problem of §1.1 again.

### 2.3 Adaptive allocation: more patients to the arm that is winning

- **FDA, §V.E** (READ). Response-adaptive randomisation changes each new patient's chance of each arm based on outcomes so far. Its ethical case is that more patients get "the more promising" arm. The FDA calls the arguments "controversial". It notes that the method "works best in trials with relatively short-term ascertainment of outcomes".
- **Thall, Fox and Wathen, Annals of Oncology 26(8), 2015** (https://mdanderson.elsevierpure.com/en/publications/statistical-controversies-in-clinical-research-scientific-and-eth, READ abstract). In simulated 200-patient trials, outcome-adaptive randomisation often had "a sample size imbalance in the wrong direction". It "greatly overestimated" the effect, had smaller power, and its bias grew when patient prognosis drifted during the trial. They prefer fixed randomisation with group sequential rules.
- **I-SPY 2** (SNIPPET; the PMC page showed a bot check, which I did not bypass). An arm "graduates" at an 85% predicted chance of phase 3 success and is dropped below 10%, with at most 120 patients per arm (search excerpts of https://pmc.ncbi.nlm.nih.gov/articles/PMC5259558).

**Mapping [judgment].** Sizing units by recent results is adaptive allocation. Its known failures are overweighting a lucky arm and bias when conditions drift, which is a regime change in trading terms. This agrees with the earlier advice to size by risk and use the edge as a gate (`R2:237`) and with the caution on bandits (`R05:181`).

### 2.4 Dose escalation: sizing up step by step

- **The rule** (FDA statistical review of BOIN, https://www.fda.gov/media/155364/download, READ). Start at the lowest dose. If the observed toxicity rate at the current dose is at or below λe, go up one level. At or above λd, go down one level. Otherwise stay. A dose-elimination rule removes a dose and every higher dose when the data say it is very likely too toxic. The FDA designated the revised design "fit-for-purpose" for finding the maximum tolerated dose.
- **Boundaries.** For a 30% target with the usual settings, λe = 0.236 and λd = 0.359 (block 9, [arithmetic], from the Liu and Yuan 2015 formulas; search excerpts give 0.236 and 0.358).
- The older 3+3 design does the same with cohorts of three. It goes up after 0 of 3 patients have toxicity, adds patients at 1 of 3, and stops at 2 or more (SNIPPET, e.g. https://odin.mdacc.tmc.edu/~yyuan/Software/BOIN/BOIN-CCR-wAppend.pdf).

**Mapping [judgment].** Size levels play the part of dose levels. A "toxicity" is a pre-defined bad outcome for a cohort of trades, such as a day that breaches its loss limit. The unit moves up one level only while the bad-outcome rate stays under a low bar. It moves down when the rate is over a high bar. A level that proves too dangerous is locked out. The design never skips levels.

### 2.5 Surveillance after launch: a minimum number of events before a signal

Kulldorff and Silva, "Continuous Post-Market Sequential Safety Surveillance with Minimum Events to Signal" (https://ar5iv.arxiv.org/html/1503.01978, READ):
- Continuous testing can signal after very few events, which suits a phase 2 trial but "in post-market safety surveillance it is not" appropriate.
- An ad-hoc "at least two or three events" rule "leads to a conservative type 1 error". The paper gives exact critical values for a required minimum number of events, M.
- "For fixed T, the power always increases with increasing M". The average time to signal can rise or fall.

**Mapping [judgment].** A brake that may fire on the first loss is the same mistake. Require a minimum number of events, then use thresholds computed for that minimum, so the false-alarm rate stays known.

### 2.6 Summary map

| Trial concept | Bad day or broken edge? | Sizing step it suggests [judgment] |
|---|---|---|
| Phases 1-4 | each phase is a bigger, longer test | minimum size → paper or micro → full → monitored |
| Planned interim looks | neither alone; stops only on accumulated evidence | review size at fixed trade counts, not daily |
| O'Brien-Fleming efficacy | early proof must be overwhelming | size up early only on very strong evidence |
| Non-binding futility | broken edge | stop or step down when the goal is out of reach |
| Adaptive randomisation | n/a | caution: performance-chasing allocation |
| Dose escalation (BOIN, 3+3) | bad-outcome rate per cohort | one level up or down at a time; lock dangerous levels |
| Minimum events to signal | bad day | no brake fires before M events |

---

## 3. Layered protection in other industries

### 3.1 Power-grid protection

- **Selectivity.** "The primary protection closest to the fault should act promptly to isolate the fault." Backup protection farther away "might begin to operate but should not actually initiate any tripping functions" while the primary works. Inverse-time relays are spaced 0.3 to 0.4 seconds apart, so the device closest to the fault can clear it "before other upstream devices respond". The margin may shrink only if field tests show it still works, and maintenance must then keep confirming it (US Tri-Service Electrical Working Group, TSEWG TP-7, https://www.wbdg.org/FFC/DOD/STC/twewg_tp7.pdf, READ, pp. 1-3).
- **Retry before lockout.** "80-90% of the faults are transient" on overhead lines, so breakers reclose automatically. A single-shot scheme allows "only one reclose operation and lockout for subsequent tripping" (University of Western Ontario course report, https://eng.uwo.ca/people/tsidhu/documents/auto-reclosing.pdf, READ; a student report, so secondary). Lockout needs a human to reset it (SNIPPET, https://ibiblio.org/kuphaldt/socratic/model/mod_79_relay.pdf).
- **Staged shedding.** Under-frequency load shedding must shed load "with a minimum of three frequency set points". The highest is set between 59.3 and 59.6 Hz (NERC PRC-006-SERC-03, https://nerc.com/pa/Stand/Reliability%20Standards/PRC-006-SERC-03.pdf, READ). One region's stages are 59.5, 59.3, 59.1 and 58.9 Hz, each shedding about 6.5 to 7.5% of load (SNIPPET, NPCC directory via https://www.nyiso.com).

How it avoids firing too often or all at once: the nearest device acts first and the others wait a set time; temporary faults get a retry; shedding comes in steps.

**Borrow [judgment]:** the nearest brake trips first (unit, then book, then account), each higher level waits a graded delay, and a paused unit gets a set number of automatic retries before it locks out for a human.

### 3.2 Aviation alerting and envelope protection

- **Alerting** (FAA Human Factors guidance, quoting AC 25.1322-1, https://hfcc.dot.gov/publications/docs/GeneralGuidance/zz_FAA_GeneralGuidanceDoc_Chapter_04_Section_01.html, READ). "Conditions that do not require flightcrew awareness should not generate an alert." Aural alerts are prioritised "so that only one aural alert is presented at a time". A design can follow its alerting philosophy and still have a number of alerts that "may be unacceptable". In incident reports, the most common alert-related cause was an alert so loud it distracted the crew. Missed alerts were second.
- **Envelope protection** (Airbus, https://www.airbus.com/en/newsroom/stories/2023-02-safety-innovation-7-flight-envelope-protection, READ). In "normal law" the aircraft cannot pass its angle-of-attack, speed, pitch, bank and load limits. The protections "remain available under any single system failure". Airbus reports loss-of-control accidents "reduced by 89%" for aircraft with them. That is Airbus's own claim, with no method given.

How it avoids firing too often or all at once: alerts exist only for conditions that need action, one sounds at a time by priority, and hard limits act inside the controls without an alarm.

**Borrow [judgment]:** hard envelope limits that the unit cannot exceed and that act quietly (size caps, a maximum open risk), plus alerts only for things a human must act on, ranked, one at a time.

### 3.3 Insurance accumulation

- **Scenarios everyone reports** (Lloyd's, https://www.lloyds.com/market-resources/underwriting/realistic-disaster-scenarios, READ). Lloyd's "maintains a set of mandatory Realistic Disaster Scenarios (RDS) to stress test both individual syndicates and the market as a whole". There are three sets. Compulsory scenarios are reported by all syndicates, and Lloyd's "monitors the total of all syndicate losses" (for example two consecutive Atlantic windstorms, a California earthquake, terrorism, cyber). Each syndicate also defines two scenarios of its own for losses "not captured in other scenarios". Specialist scenarios are reported only above a loss threshold.
- **One event = one time window** (Verisk, https://www.verisk.com/blog/modeling-fundamental--accounting-for-the-hours-clause/, READ). The hours clause counts all losses "accumulated in a defined number of hours" as one event: tornado 24 hours, windstorm 72, flood 168 in the US or 504 in Europe. Storms that cluster make the window contentious.
- **Standard zones.** CRESTA zones are the standard geographic units for adding up catastrophe exposure (SNIPPET, https://en.wikipedia.org/wiki/CRESTA).

How it avoids firing too often or all at once: one shared event counts once, and exposure is summed per zone against named scenarios.

**Borrow [judgment]:** count all units' losses from one market move inside a set window as one event for the book's brakes. Keep a fixed list of scenarios every book reports against, plus a few it defines itself. Sum exposure per shared driver (currency, region, class).

### 3.4 Bank limit hierarchies

- The FSB principles cover four parts: the framework, the appetite statement, "risk limits", and the duties of board and management (https://www.fsb.org/2013/11/r_131118/, READ abstract). The draft defines risk limits as measures "that allocate the firm's aggregate risk appetite" to business lines, legal entities and risk categories (SNIPPET, July 2013 draft https://www.fsb.org/uploads/r_130717.pdf).
- One bank discloses VaR limits with sub-limits, stop-loss limits per business unit, and "a system of warning signals" (SNIPPET, BBVA, https://accionistaseinversores.bbva.com/microsites/bbvain2013/en/R/m1.html).
- Basel's yellow zone (§1.4) is a formal "explain before we act" band.

How it avoids firing too often or all at once: one appetite number at the top is split into smaller limits, warnings come before hard limits, and a middle band triggers a review instead of a penalty.

**Borrow [judgment]:** one book-level budget split down to units, a soft warning before every hard brake, and a yellow state that asks for evidence instead of acting.

### 3.5 Site reliability engineering

From Google's SRE workbook, https://sre.google/workbook/alerting-on-slos/ (READ):
- Judge an alert rule on precision, recall, detection time and reset time.
- Burn rate is "how fast, relative to the SLO, the service consumes the error budget".
- Recommended: page at 2% of the monthly budget burned in 1 hour (burn rate 14.4) or 5% in 6 hours (rate 6). Open a ticket at 10% in 3 days (rate 1). Each alert also needs a short window, such as 5 minutes, to stay over the bar, so it resets quickly.
- A naive rule could send "up to 144 alerts per day every day" and the service would still meet its target.
- Low-traffic services are hard, because one failed request is a large share of the budget.

Arithmetic: 14.4 × 1 hour ÷ 720 hours = 2% (block 5).

How it avoids firing too often or all at once: it alerts on how fast the budget is going, not on every error. Two windows must agree, and only urgent cases page a person.

**Borrow [judgment]:** a loss budget per day or week, with brakes keyed to how fast it burns over two windows. A "page" class (stop now) is kept apart from a "ticket" class (look later). Low-frequency units need their own rule, as low-traffic services do.

### 3.6 Hospital alarm fatigue

"Between 85 and 99 percent of alarm signals do not require clinical intervention". Clinicians "become desensitized" and may turn alarms down or off (Joint Commission Sentinel Event Alert 50, 2013, https://digitalassets.jointcommission.org/api/public/content/f65e5c9df2b94000a99445e0a7877007, READ).

**Borrow [judgment]:** record, for every brake, how often its fires needed action (its precision), and treat a noisy brake as a defect.

### 3.7 The shared toolkit

| Mechanism | Where | Stops firing too often | Stops all firing at once |
|---|---|---|---|
| Nearest device first, time grading | grid relays | backups wait | only one level trips |
| Retry then lockout | reclosers | temporary faults clear | lockout is local |
| Staged set points | load shedding | small first step | steps, not one big cut |
| Alert only if action needed; one at a time | aviation | fewer alerts | priority order |
| Hard envelope | fly-by-wire | no alarm needed | acts inside the controls |
| One event per time window | reinsurance | many losses count once | n/a |
| Standard scenarios | Lloyd's | n/a | measures the joint hit in advance |
| Three zones | Basel | yellow asks, does not act | n/a |
| Burn rate, two windows, page vs ticket | SRE | spikes filtered | only urgent cases page |
| Precision tracking | hospitals | noisy alarms found | n/a |

---

## 4. Many variables across instruments, styles and timeframes

### 4.1 How risk terms differ by class

QMX's planned instrument record already holds tick, pip, contract size, value per point, lot limits, swap, margin, expiry and funding fields (`G7:181-197`). Outside facts:

| Class | Size and value of a move | Retail CFD leverage cap (ESMA) | Carry or funding | Settlement and sessions |
|---|---|---|---|---|
| FX majors | lot = 100,000 units in QMX's fixture (`G7:196`) | 30:1 | swap at rollover; the forex calendar rolls at 17:00 New York (`G7:159`) | 24 hours on weekdays |
| FX non-majors | as above | 20:1 | swap | as above |
| Gold | COMEX GC: 100 troy ounces, minimum tick $10.00; micro MGC: 10 ounces, $1.00 tick (https://www.cmegroup.com/education/lessons/product-gold.html, READ) | 20:1 | futures roll; CFD swap | deliverable future, "nearly around the clock, six days a week" (same page) |
| Major indices | Micro E-mini S&P 500: "$5 x the S&P 500 Index", tick 0.25 points (https://www.cmegroup.com/markets/equities/sp/micro-e-mini-sandp-500.contractSpecs.html, READ), so $1.25 a tick [arithmetic]; E-mini $50 × index, $12.50 a tick (SNIPPET, https://www.schwab.com/learn/story/stock-index-futures-tick-values) | 20:1 (major), 10:1 (non-major) | futures roll | exchange sessions and breaks |
| Other commodities | per contract | 10:1 | roll | per exchange |
| Single stocks | per share | 5:1 | dividends | US cash stocks settle T+1 since 28 May 2024 (SEC, https://www.sec.gov/newsroom/press-releases/2023-29, READ) |
| Crypto | per coin or contract | 2:1 | perpetuals: funding "every 8 hours at 00:00 (UTC), 08:00 (UTC), and 16:00 (UTC)"; amount = position notional × funding rate; paid between traders, not to the exchange (Binance, https://www.binance.com/en/support/faq/detail/360033525031, READ) | 24/7 |

ESMA leverage caps and the reason they differ: limits "vary according to the volatility of the underlying". The package also has a margin close-out rule per account and negative balance protection (https://www.esma.europa.eu/press-news/esma-news/esma-adopts-final-product-intervention-measures-cfds-and-binary-options, READ, measures from 1 August 2018).

### 4.2 How practitioners put risk on one scale

| Scale | What it divides by | Who uses it | Note [judgment] |
|---|---|---|---|
| R (risk to the stop) | money lost if the stop is hit | QMX's judge and journals (`G8:300`, `R08:118`) | compares trades; ignores how volatile the market is between stops |
| Volatility units | the money value of a typical daily move | pysystemtrade: `get_block_value` is the "value of a 1% move in the price", `get_instrument_value_vol` is daily volatility in the account's currency, default `percentage_vol_target: 16.0` (https://github.com/pst-group/pysystemtrade/blob/master/docs/backtesting.md, lines 4069-4074 and 4535, READ) | compares instruments and days; R and volatility agree only when stops are a fixed multiple of volatility |
| Notional | price × size | funding, swaps, broker exposure (Binance above) | shows size, not risk |
| Margin | required collateral | ESMA caps, close-outs | shows survival, not risk |

**Worked number: the same rule across classes on a $500 account [arithmetic].** A 16% yearly volatility target on $500 is $80 a year, or about $5 a day (÷ 16, the square root of 256 trading days). One Micro E-mini at 7,565.5 (CME page above, delayed price, 3 Nov 2026) is $37,828 notional. At an assumed 1% daily move that is about $378 a day, so the target position is 0.013 contracts, which rounds to zero. EUR/USD at an assumed 1.15 with a 0.01 lot (1,000 units, from QMX's fixture lot step) is about $1,150 notional. At an assumed 0.5% daily move that is about $5.75 a day, roughly the target. So one sizing rule gives a tradable size in one class and nothing in another. Lot granularity per class is a real variable, not a detail.

### 4.3 How large parameter spaces are organised

- **Defaults, then overrides, in a fixed order.** pysystemtrade takes a setting from the backtest config first, then the private config, then `defaults.yaml`. The private config "will overwrite the system defaults, but will in turn be overwritten by the backtest configuration" (docs line 363, READ). For nested settings, change one element only, or you wipe the other defaults (docs around line 1167, READ).
- **Classes and buckets with a catch-all.** ISDA SIMM has "six risk classes": interest rate, credit (qualifying), credit (non-qualifying), equity, commodity and FX. Each class splits into buckets with their own risk weights, correlations and concentration thresholds. Equity buckets are grouped by market and size, for example "Emerging Markets Large Cap" and "Developed Markets Small Cap". Commodity buckets are grouped by type: coal, crude, power, precious metals and so on. A "Residual" bucket holds anything unclassified, with a 0% within-bucket correlation (ISDA SIMM v2.6, https://www.isda.org/a/b4ugE/ISDA-SIMM_v2.6_PUBLIC.pdf, READ, sections B, G.2, J.4).
- **A standard code per instrument.** ISO 10962 CFI is "a six-letter-code" that classifies an instrument's structure and function. The first letter is the category (E equity, D debt, C collective investment vehicles, and so on), and the later letters are its group and attributes (https://en.wikipedia.org/wiki/ISO_10962, READ; the code list itself lives outside the standard since 2021, SNIPPET).
- **Group styles by return behaviour, not by label.** Brown and Goetzmann found "a number of distinct styles" from hedge funds' monthly returns over 1989-2000, with style explaining "about 20 per cent" of the spread in performance (https://www.nber.org/papers/w8173, READ). A later paper says they found eight styles, where database vendors use 11 to 23 (SNIPPET). Fung and Hsieh showed trend followers' returns are "option-like" and are better modelled by lookback straddles than by asset indices (https://ideas.repec.org/a/oup/rfinst/v14y2001i2p313-41.html, READ).
- **Cluster units by their results.** ONC, HRP and correlation-cluster try counts are covered in `R05:104-110` and `R26:92-120`.
- **Keep an inventory.** SR 26-2's model inventory (§1.4) is the bank version of his "ledger of variables" (`OW:79`).

**Reading [judgment].** The three structures fit his growing variable list. Defaults with overrides answer "every variable has a value without hand-setting all of them". Classes and buckets with a residual answer "many instruments, few parameter sets, and a safe home for the odd one". A code per instrument answers "which defaults apply here" without free text.

---

## 5. What this means for QMX [judgment]

All of this section is opinion, offered as input for the design.

1. **Give every unit a verification plan before it trades, priced in trades.** From the claimed edge and the trade rate, the plan states how many trades proof needs and when that should arrive (§1.1). A unit that cannot reach proof in the allowed time is "too thin to prove", as `R05:376` already suggests. This turns "is the edge real?" into a schedule he can read.
2. **Look at fixed trade counts and spend the error budget, never test daily at a flat 95%.** Use an O'Brien-Fleming-style plan or e-values (§1.3, §2.2). Daily checks at 95% pass dead units about three times as often as intended.
3. **Use three zones, as Basel does.** Green: carry on. Yellow: gather evidence and maybe step down one size level, with no penalty. Red: act automatically. This answers "a bad day cannot be told from a broken edge quickly": the yellow zone is the honest name for that state.
4. **Size up like dose escalation.** Define size levels. Move one level at a time on cohorts of trades. Move up only while the bad-outcome rate is under a low bar, move down above a high bar, and lock levels that prove dangerous. Steps up should rest on live or paper evidence only (Numerai's rule), never on backtests.
5. **Do not chase performance across units.** Adaptive allocation's known faults (wrong-way imbalance, overstated effects, drift bias) argue for fixed risk shares plus sequential gates. That matches `R2:237`.
6. **Brakes: nearest first, graded delays, a minimum event count, retry then lockout, two-window burn rates, and page versus ticket.** Each brake records its own precision, the share of fires that needed action. A brake that fires mostly on healthy units is a defect, which is his "sweet spot" for frequency stated as a measurable number.
7. **"Losing together" gets an event window and a scenario set.** Losses from one move within a set window count once for the book. A fixed scenario list in the RDS style is run against every book, and each book adds its own. Bank guidance names the root cause as models that share assumptions. This is also the "generate scenarios" ask (`OW:79`).
8. **Organise variables as defaults → class → bucket → instrument → unit overrides, with a residual bucket.** Each variable in the ledger records its default, its override chain, the level it acts at, and which brakes or sizers read it. That last field is how "when this changes, what else moves" becomes answerable.
9. **The verification workflow can be deterministic.** Every gate above is a formula on recorded trades, so scripts can run it on a schedule. Agents propose units and explanations. Only he promotes to live (`R26:68`).

---

## 6. Not verified

- **Snippet-only claims:** WorldQuant gates; I-SPY 2 thresholds (the PMC page showed a bot check, which I did not bypass); the 3+3 rule wording; the O'Brien-Fleming and Pocock constants (checked by my simulation); E-mini $50 multiplier; NPCC stage sizes; recloser lockout needing a human; the FSB risk-limit definition (draft wording; the final PDF's text could not be extracted); the BBVA disclosure; CRESTA details; Brown and Goetzmann's eight styles; the CFI code list's move outside the standard.
- **Secondary sources used as READ:** the recloser figure comes from a university student report; the ISO 10962 page is Wikipedia; Verisk is a vendor blog; Airbus's 89% has no stated method.
- **Not read:** IEEE 242 (paywalled; I used the TSEWG document, which cites it); the full Lloyd's RDS specification (its PDF text is in an unreadable font encoding); the full Liu and Yuan 2015 paper (the FDA review quotes its rules).
- **Model limits:** all trade counts assume independent ±1R trades. Fat tails, streaks and regime change make proof slower. The group sequential simulation uses Gaussian trades with a standard deviation of 1R.
- **Tools:** Firecrawl was out of credits and Exa is not connected to this session. I used web search only to find URLs, then read pages in the built-in browser or downloaded the documents and extracted their text.

## 7. Sources

Read in the browser or from the document:
- NBER w20592, Harvey, Liu and Zhu: https://www.nber.org/papers/w20592
- BIS 1996 backtesting framework: https://www.bis.org/publications/199601-standards-supervisory-framework-use-backtesting-conjunction-internal-models-approach-market-risk-capital.pdf
- Fed SR 26-2 and attachment: https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm ; https://www.federalreserve.gov/supervisionreg/srletters/SR2602a1.pdf
- Numerai staking: https://docs.numer.ai/numerai-tournament/staking
- Google SRE workbook: https://sre.google/workbook/alerting-on-slos/ ; https://sre.google/workbook/canarying-releases/
- FDA: https://www.fda.gov/patients/drug-development-process/step-3-clinical-research ; https://www.fda.gov/media/78495/download ; https://www.fda.gov/media/155364/download
- Thall, Fox and Wathen 2015: https://mdanderson.elsevierpure.com/en/publications/statistical-controversies-in-clinical-research-scientific-and-eth
- Kulldorff and Silva: https://ar5iv.arxiv.org/html/1503.01978
- TSEWG TP-7: https://www.wbdg.org/FFC/DOD/STC/twewg_tp7.pdf
- UWO auto-reclosing report: https://eng.uwo.ca/people/tsidhu/documents/auto-reclosing.pdf
- NERC PRC-006-SERC-03: https://nerc.com/pa/Stand/Reliability%20Standards/PRC-006-SERC-03.pdf
- FAA human factors guide, alerting: https://hfcc.dot.gov/publications/docs/GeneralGuidance/zz_FAA_GeneralGuidanceDoc_Chapter_04_Section_01.html
- Airbus envelope protection: https://www.airbus.com/en/newsroom/stories/2023-02-safety-innovation-7-flight-envelope-protection
- Lloyd's RDS: https://www.lloyds.com/market-resources/underwriting/realistic-disaster-scenarios
- Verisk hours clause: https://www.verisk.com/blog/modeling-fundamental--accounting-for-the-hours-clause/
- FSB RAF page: https://www.fsb.org/2013/11/r_131118/
- Joint Commission SEA 50: https://digitalassets.jointcommission.org/api/public/content/f65e5c9df2b94000a99445e0a7877007
- ESMA CFD measures: https://www.esma.europa.eu/press-news/esma-news/esma-adopts-final-product-intervention-measures-cfds-and-binary-options
- CME: https://www.cmegroup.com/markets/equities/sp/micro-e-mini-sandp-500.contractSpecs.html ; https://www.cmegroup.com/education/lessons/product-gold.html
- SEC T+1: https://www.sec.gov/newsroom/press-releases/2023-29
- Binance funding: https://www.binance.com/en/support/faq/detail/360033525031
- pysystemtrade docs: https://github.com/pst-group/pysystemtrade/blob/master/docs/backtesting.md
- ISDA SIMM v2.6: https://www.isda.org/a/b4ugE/ISDA-SIMM_v2.6_PUBLIC.pdf
- ISO 10962: https://en.wikipedia.org/wiki/ISO_10962
- Brown and Goetzmann: https://www.nber.org/papers/w8173 ; Fung and Hsieh: https://ideas.repec.org/a/oup/rfinst/v14y2001i2p313-41.html

Snippet only: https://github.com/RussellDash332/WQ-Brain ; https://pmc.ncbi.nlm.nih.gov/articles/PMC5259558 ; https://odin.mdacc.tmc.edu/~yyuan/Software/BOIN/BOIN-CCR-wAppend.pdf ; https://eclass-b.uoa.gr/modules/document/file.php/MATH301/PracticalSession3/LanDeMets.pdf ; https://www.schwab.com/learn/story/stock-index-futures-tick-values ; https://ibiblio.org/kuphaldt/socratic/model/mod_79_relay.pdf ; https://www.fsb.org/uploads/r_130717.pdf ; https://accionistaseinversores.bbva.com/microsites/bbvain2013/en/R/m1.html ; https://en.wikipedia.org/wiki/CRESTA ; https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2006-Madrid/papers/313461_full.pdf
