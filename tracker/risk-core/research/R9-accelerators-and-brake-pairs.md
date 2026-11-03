# R9: Accelerators, and how brakes and accelerators work as pairs

Written 2026-11-03 for the risk-core design session. Research only: it reports practice, evidence and arithmetic, and does not design QMX. Nothing here is ratified. Never committed.

## How to read this

- **Labels.** **READ**: I read the primary page or paper text. **ABSTRACT**: only the abstract or the publisher's summary. **SNIPPET**: a search-result excerpt, not read in full; treat as unconfirmed. **[judgment]**: my opinion. **[arithmetic]**: my own numbers from the script below.
- **Script.** `D:\QMX-worktrees\risk-plan\tracker\risk-core\research\R9-scripts\accelerators.py` (standard-library Python; run `python -I accelerators.py 400`; about one minute). Output: `...\R9-scripts\out-400.txt`. Model: trades pay +1R or −1R with costs netted into the win rate, 10 trades a day, 250 days, base risk 0.5 % of current equity per trade, 400 paths per scenario, the same trade streams for every policy. These are model numbers, not evidence about real strategies.
- **Short paths.**

| Alias | Path |
|---|---|
| `A1`, `A2` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\linking\components\A1-sizing-allocation.yaml`, `...\A2-brakes-drift-exits.yaml` |
| `R2`, `R3`, `R7`, `R8` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\research\R2-...`, `R3-...`, `R7-...`, `R8-gap-topup.md` |
| `R6` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\research\R6-alphaxiv-papers\R6-synthesis.md` |
| `G3`, `G6` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\grounding\G3-old-system.md`, `...\G6-book-bms-levels-and-paper.md` |
| `SEEDS`, `OW1`, `OW3` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\seeds\SEEDS.md`, `...\operator-words-2026-11-01.md`, `...\operator-words-2026-11-03.md` |
| `V` | `C:\Users\Mubarak\Documents\Claude\QMX-discussion\02-Components\01-risk-and-sizing\` (old vault; read for definitions only) |
| `MQL` | `C:\Users\Mubarak\Desktop\QMX\.worktrees\mql5-library\data\mql5-library\md\<id>.md` |

- **Not redone.** I cite and do not repeat: the 13 accelerator components and the sizing rules in `A1` (house money A1-066/067/068, ladder A1-042, prop scaling A1-065, pyramiding A1-071, BOIN A1-052, starter budget A1-054, warm-up A1-061, e-value loosening A1-064, restore ladder A1-056, Kelly family A1-016..030); the 85 brakes in `A2`; the TCP, Netflix AIMD, HPA, Guava and SRE burn-rate mechanics in `R7` §2 and §5; the BOIN, Basel and SRE material in `R3` §2-3; the stop-loss and serial-correlation papers in `R8` §1 (Kaminski-Lo, Lo-Remorov); shrunk and Bayesian Kelly in `R2` §4.4.
- **alphaXiv.** Papers kept were saved to the folder `qmx-risk-sizing`: 1902.01265 (Miller-Sanjurjo), 2303.02613 (drawdown control with restart), 1710.02824 (Kaunitz et al., betting).

---

## Short answer

1. **Definitions.** A brake moves risk-taking below the unit's baseline on evidence of danger. An accelerator moves it above baseline on evidence of opportunity or proof. Both are judged against a declared baseline, not against the last value. Letting a brake go ("growing back after a cut") is a third thing, a **restore**, and it is not an accelerator. Section 0 gives the attributes (what it reads, its anchor, what it changes, direction, shape, speed, hysteresis, memory, who clears it) and a taxonomy.
2. **The old pair was not a pair.** Old house money read the slot's day P&L in money and stepped to 1.5x. Old reverse house money read a count of losses in a row, only in ORB-led windows, with tiers 1.0 / 0.7 / 0.5 (`V\02-multiplier-stack.md:191-212`). Different signal, scope and shape. A true pair reads one ledger from one anchor.
3. **On one ledger, house money and reverse house money are the same rule.** Under a floor, the optimal size is proportional to the cushion above the floor (Grossman-Zhou; Hsieh-Barmish, READ). With a fixed anchor such as the day's start, that rule raises size after gains and cuts it after losses. With a 1 % day limit, +0.5 % on the day gives 1.5x, the old house-money step; with the old 10 % limit it gives only 1.05x **[arithmetic]**. The GitBook ladder was this rule at Book level (`G6` §3.11).
4. **With independent trades, no accelerator beats a fixed size of the same average risk.** In the script, house money, equity-curve rules and the cushion rule all earn the same growth per unit of risk as a constant size (0.59-0.61 on a thin edge), and their drawdowns follow their average risk **[arithmetic]**. House money then is a 12 % size increase in disguise.
5. **Accelerators pay only when results persist.** With a hidden good/bad regime (60 % / 45 % wins), growth per unit of risk rises by a third (cushion rule 0.80 against 0.58) and doubles for an equity-curve rule in slow regimes (1.16 against 0.60) **[arithmetic]**. The regime sits in the trade stream although the lag-1 autocorrelation of single trades is only 0.02.
6. **Persistence is real at some timescales and absent at others.** Factor returns persist: the average factor earns 52 bp a month after a positive year and 1-2 bp after a negative one (Ehsani-Linnainmaa, READ). Returns themselves are nearly uncorrelated beyond about 20 minutes, while volatility clusters for days (Cont 2001, SNIPPET). Streak studies are biased against finding persistence unless corrected (Miller-Sanjurjo, READ). No study measures win-streak persistence in intraday retail strategies after costs; each unit must measure its own.
7. **Measure persistence in blocks, not trade to trade.** For a 50-trade regime, block sums show it in about 950 trades; lag-1 needs about 8,900 **[arithmetic]**.
8. **The strongest live brake-accelerator pair found is Topstep's Dynamic Live Risk Expansion** (READ): one signal (net profit), up one tier at a time only after 10 active trading days in the new tier, down the same day when profit falls below the tier, no skipping, counter reset on drop-out.
9. **Do not let an accelerator re-raise into a trip.** Field patterns: remember the level where the trip happened and regrow slowly near it (TCP ssthresh, CUBIC plateau); any brake outranks every accelerator (AWS scales out if any policy says so and in only if all do, SNIPPET); wait for the last change to settle before the next (heparin rechecks 6 hours after each change, about four half-lives, READ); never skip levels (BOIN, Topstep); a restart that resets the peak voids the drawdown cap (Hsieh 2023: 20.18 % against a 20 % cap, READ).
10. **Brakes in money beat brakes in counts, and must scale with trade frequency.** A "3 losses in a row" brake fires on 41 % of days for a healthy 55 % unit at 10 trades a day and on 60 % for an equally good unit that cuts losers early (fast invalidation). A brake at the unit's own 1st percentile of daily P&L fires on 1-3 % of days at every trade count **[arithmetic]**.
11. **Drawdown brakes earn their keep when edges decay, not when they are stable.** Man Group's study: total-return rules beat drawdown rules for managers of constant skill; drawdown rules win when good managers turn bad (READ). This is the case for the old circuit breaker as an alpha-decay sensor.
12. **Path-dependent brakes buy tail safety cheaply.** A cut-on-bad-day, grow-on-green-day rule (AIMD) ran at 79 % of base risk with the same growth per unit of risk, and cut the chance of a 25 % drawdown to 0.5 %, against 1.3 % for a constant size at 80 % **[arithmetic]**.

---

## 0. Definitions

### 0.1 What he and the lead have said

These shape the definitions. Quotes are his exact words from `SEEDS`, `OW1` and `OW3`; "breaks", "Brex" and "bricks" are dictation for brakes, "house of money" for house money (`SEEDS` A21, A28).

**Accepted by him**

| Item | His words | What it fixes in the definitions |
|---|---|---|
| A21 | "we are going to call them accelerators, I think. So, for example, House of Money is an accelerator." (M5) and "The word accelerator, actually. I like it." (M8) | Accelerator is a kept category. |
| A21 | "Now these two are accelerators and decelerators. Well, I don't know." (M7, on house money and reverse house money) | His own word "decelerator" pairs the two families. |
| C19 | "So Brex first, accelerator second." (M8) and "Money breaks are important." (M5) | Brakes outrank accelerators; money is a first-class brake signal. |
| C19 | "aggressive and nuclear are two things" ... "we needed to have clamps that make sure that, okay, in its aggressiveness, while we lose, we don't lose stupidly." (M8) | A clamp (fixed bound) is separate from a brake. |
| A6 | "the same way reverse house of money worked. So at maybe half of the six ... at three losses, or if we can sort of figure out a pattern ... so that we don't really go with a straight downfall." (M8) | Reverse house money's purpose: stop a losing run from compounding. |
| A26 | "these are part of the breaks ... installed so to keep this thing intact" ... "it helped us detect alpha decay ... It was a big break. One of the biggest, but again, it's a baseline improve it, please." (M10); "The old circuit breaker. All right, good." (M12) | A brake's fire record is also a sensor. |
| C21 | "The kill switch has survived multiple versions ... it earned its spot" and "closing a trade is never blocked" (M5) | Brakes never block a close. |
| C27 | "it can isolate crypto. And everything is off for crypto." (M10) | Scope (class, region, instrument) is a brake actuator. |
| C10 | "the BMS doesn't allow the floor to be touched. So we give a buffer." (M8) | A buffer brake sits above the floor clamp. |

**Questioned or refused by him**

| Item | His words | Consequence |
|---|---|---|
| B13, C7 | "I can't just say unit break. BMS daily break. I can't agree to all this ... it's circumstantial" ... "Let's first explore." (M10) | No brake set is agreed; definitions must not presuppose one. |
| A25 | "You can't simply say if they differ, you simply pull out. It can be a bad day" ... "You're meant to size down, I think, but not quickly" (M10) | Speed is an attribute, and drift brakes are slow. |
| A28, C33 | "having two stops in a full day, like, that's for the old system" ... "breaks ... also take into account ... first invalidation" (M12); "us having one standardized way doesn't add up" (M12) | Brakes must count fast-invalidation cuts and exits; frequency scaling per level. |
| C7 | "Because if you're trading 24 hours a day, multiple instruments, we need to be able to not just do one break at a go ... We need to be able to know what is breaking." (M8) | Every brake names its signal and scope. |
| A14, M33 | low-end sizing is "too safe" (M8); "I don't want just safety. I want something that can like perform" ... "the sitting duck thing" (M33, `OW3:188`) | Holding size below baseline has a cost; a brake needs a release rule. |
| A24 | the risk system should "carry or amplify the load" so "even with a low performing bot or edge, we can still squeeze some money out of it" (M10) | Accelerators should lean on breadth and cushions, not on a point edge. |

**His corrections that apply here**: the lead missed the circuit breaker (M10, `SEEDS` corrections 22); brakes and sims left out fast invalidation (A9, A28; corrections 15, 30); "breaks that count losses fire ... just by chance" ignored exits (M12). And on 3 Nov: "break and accelerator are just words we are using ... You should define them ... House of Money was simple to see, but reverse House of Money was my idea ... this is how linking of logic comes in." (M39, `OW3:224`).

### 0.2 Brake, accelerator, restore, clamp: first-principles definitions

Start from what a sizing system does. For each candidate trade it turns a **baseline** risk (the unit's neutral policy, for example a fixed share of its budget at the stop) into a final risk, and it decides whether the trade may happen at all. Everything that moves the final risk away from baseline because of evidence is a brake or an accelerator.

- **Baseline.** The risk the unit takes when nothing special is happening. It must be declared, because direction is measured from it. Compounding on current budget is part of the baseline, not an accelerator **[judgment]**.
- **Brake.** A rule that, on evidence of danger, holds the unit's risk-taking **at or below** baseline: smaller size, fewer trades, no new entries, narrower scope, or less exposure. A brake can never raise risk above baseline. It never blocks a close, a cancel or a tighter stop (`G6` §3.10).
- **Accelerator.** A rule that, on evidence of opportunity or proof, raises risk-taking **above** baseline: bigger size, more trades, wider scope, or more capital. It always has a ceiling, and any active brake outranks it.
- **Restore (release).** The path by which a brake lets go, back toward baseline. It is part of the brake's design (its clear rule). "Growing back after a cut" is a restore. Calling it an accelerator mixes two questions: "is the danger over?" and "is there proof to go above normal?" **[judgment]**.
- **Clamp (envelope).** A fixed bound that does not read evidence: the floor, max lots, the per-trade cap. Brakes and accelerators act inside it (his "clamps", M8).
- **Banker (sweep) and re-seed.** Moves realised money out of the risk zone (sweep) or back in (re-seed). Neither acts on the next trade, but both reset what the cushion-based rules feed on. A sweep is a slow de-accelerator; a re-seed after losses is a capital accelerator that bets on the unit's own recovery (§1.10).

**The nine attributes of any brake or accelerator** (one row in a registry):

| Attribute | Question it answers | Values found in the research |
|---|---|---|
| Reads | Which signal, over which window? | outcome (P&L, drawdown, streaks, loss points); evidence (tests, cohorts, milestones); environment (volatility, spread, liquidity, regime, news, correlation); exposure (open risk, heat, margin, crowding); health (data, fills, errors, costs); time (session, warm-up, idle) |
| Scope | Whose signal and whose risk? | trade, unit, cluster or Book, class or region, BMS, account |
| Anchor | Measured from what? | day start, session start, running peak (trailing), seed, fixed floor, tier threshold |
| Changes | Which lever? | size, frequency, permission (on/off, paper/live), scope (which markets), exposure (flatten), capital |
| Direction | Down (brake) or up (accelerator) from baseline | |
| Shape | How the lever moves | step, ladder of levels, smooth taper, latch (trip until cleared) |
| Speed | How fast it acts, and how fast it lets go | attack (immediate, next trade, next session); release (rate per period, dwell before each step, settling time) |
| Hysteresis | Can it chatter? | separate trip and clear levels; dead band; minimum hold |
| Memory and clear | What it remembers and who ends it | stateless; counter with reset rules; latch cleared by time, state, evidence or a human |

The audio engineers' compressor uses the same knobs under fixed names: threshold, ratio, knee width, attack time and release time (MathWorks Compressor reference, READ; it cites Giannoulis, Massberg and Reiss, JAES 60(6), 2012). In that family a compressor or limiter is a brake, a noise gate is a permission brake, and an expander is an accelerator **[judgment]**.

### 0.3 Taxonomy

**Brakes** (all already have members in `A2`; the kinds name the pattern):

| Kind | Reads → changes | Example |
|---|---|---|
| Taper | budget used → size, smoothly | drawdown pressure `max(0.2, 1 − used²)` (A2-093) |
| Step ladder | drawdown from peak → size in big steps | pods: halve at −5 %, out at −7.5 % (A2-073) |
| Trip (latch) | event count or burn → permission, until cleared | circuit breaker (A2-083), freqtrade lock (A2-056) |
| Throttle | recent activity → frequency | cooldowns, minimum bench rest (A2-116) |
| Isolation | co-moving tells → scope | class or region off (A2-128) |
| Gate | per-trade precondition → permission for that trade | spread gate (A1-150) |
| Demotion | evidence of decay → venue (live to paper) | July bench (A2-087) |
| Flatten | severe danger → exposure | kill line (A2-096) |
| Streak attenuator | losses in a row → size | old reverse house money (A2-092) |

**Accelerators**:

| Kind | Reads → changes | Example |
|---|---|---|
| Cushion leverage | distance above a fixed floor → size | GitBook ladder (A1-042), CPPI |
| Profit-funded boost (house money) | realised profit since an anchor → size, paid from that profit | A1-066/067 |
| Evidence step-up | proof milestones → size level | BOIN levels (A1-052), prop tiers (§1.5) |
| Conviction add (pyramiding) | open-trade progress → added size | A1-071, Turtles (§1.2) |
| Environment boost | calm volatility, premium hours → size | volatility targeting (A1-010), session multiplier (A1-069) |
| Persistence press | recent block P&L of the unit → size | equity-curve scaling (§1.3) |
| Evidence-relaxed shrinkage | growing sample → smaller haircut on the edge | shrunk or Bayesian Kelly (`R2` §4.4) |
| Capital injection | allocation decision → capital | re-seed, allocator raising a unit (§1.10) |

**New kinds the research suggests** (no QMX component yet):

| Proposed kind | Where it comes from | What it does |
|---|---|---|
| Probe | BBR congestion control | Briefly runs above the current level, keeps the gain only if it pays, then drains back. Finds a ceiling nobody knows (capacity, slippage at size). |
| Memory ceiling | TCP ssthresh, CUBIC | After a trip, regrows fast to below the level where the trip happened, then slowly near it. |
| Overdose-controlled step | EWOC dose finding | Raises a level only while the chance that the next level is too high stays under a set bound α. |
| Slow start with first-warning switch | FDA accelerated titration, TCP slow start | Big steps from minimum while nothing has gone wrong; the first warning switches to small steps and bigger cohorts. |
| Coupled pair | heparin nomogram, Topstep tiers, poker bankroll | One signal, both directions, with a dead band between them. |
| Budget-burn permit | SRE error-budget policy | A healthy budget permits risk-taking; an exhausted budget freezes accelerators until it recovers. |
| Contrarian accelerator (anti-pattern) | martingale family; StrategyQuant's "double below the MA" (A1-073) | Raises size after losses. It bets that the unit's own results mean-revert. Flag it, never default it. |

### 0.4 House money and reverse house money, defined properly

**What the old system wrote** (`V\02-multiplier-stack.md:71-84`, `:191-212`; `V\05-session-architecture.md:96-110`, `:135-162`; `G3` §4.2-4.3):

| | House money (HME) | Reverse house money (RHME) |
|---|---|---|
| Reads | slot's cumulative day P&L as % of day-start equity | the slot's consecutive losses in the session |
| Signal type | money | count |
| Trigger | ≥ `HOUSE_MONEY_THRESHOLD` (provisional 0.5 %, `G3` §4.2) | 2 losses in a row |
| Output | 1.5x, else 1.0x | <2 → 1.00; 2-3 → 0.70; 4-5 → 0.50; 6+ → 0.50 floor |
| Scope | slot, all day; a bot entering the slot inherits it, to stop "cash out" by rotation | slot, per session, only in ORB-dominant windows; 1.0 elsewhere |
| Clear | day rollover | a win (it is a streak) and session end |
| Combined | product: 1.5 × 0.5 = 0.75, because "the loss streak signal is stronger evidence than the earlier profits" (`V\05-session-architecture.md`, G3 §4.3) |
| In practice | inert under the 0.5 % cap; double-applied in old code (2.25x) (`G3` §3) |

**Finding.** They are not mirror images. One reads money from a day anchor; the other counts a run of losses inside one session and one family. So a day can be both "in house money" and "in a losing streak" at once, which is why the vault needed a rule for their product.

**Proposed definitions** **[judgment]**:

- **House money.** An accelerator, at a declared scope (unit, Book or BMS), that funds extra risk only from realised profit above an anchor (for example the day's start). Its bound: the extra risk on open trades never exceeds a share *s* of that profit, so the scope cannot finish below its anchor because of the extra size. Inputs: realised P&L since the anchor, open risk, *s*. Output: an extra-risk allowance.
- **Reverse house money.** The brake twin on the **same ledger and anchor**: while the scope is below its anchor, size shrinks in proportion to the loss budget left, so a losing run cannot compound into "a straight downfall" (his A6). This is exactly the old drawdown-pressure taper (A1-043) read as a pair with house money. The count form the old system built is a **streak attenuator**, a separate brake kind. In money it counts a fast-invalidation cut by its size (a −0.3R cut costs 0.3R) and a breakeven as nothing, which answers his A28 point.

**The one rule behind both.** Size proportional to the cushion above a floor is the growth-optimal policy under a drawdown floor (Grossman and Zhou 1993, cited in `R2` §4.6). Hsieh's drawdown-modulation lemma gives the exact bound: exposure ≤ (d_max − d)/(1 − d) × equity ÷ worst one-step loss, where d is the current drawdown (2303.02613, Lemma 3.1, READ). With a **fixed** anchor (day start, seed, a dollar floor) gains widen the cushion, so the rule presses: house money. Losses narrow it, so the rule cuts: reverse house money. With a **trailing** anchor (running peak) a new high moves the floor up too, so the rule never goes above baseline and is a pure brake. **The anchor decides whether a cushion rule is an accelerator.**

Size multiplier (L + P) ÷ L for a day loss limit L and day profit P **[arithmetic]**:

| Day limit L | P = −1 % | −0.5 % | 0 | +0.5 % | +1 % |
|---|---|---|---|---|---|
| 1 % | 0.00 (stop) | 0.50 | 1.00 | **1.50** | 2.00 |
| 2 % | 0.50 | 0.75 | 1.00 | 1.25 | 1.50 |
| 5 % | 0.80 | 0.90 | 1.00 | 1.10 | 1.20 |
| 10 % (old Growth band) | 0.90 | 0.95 | 1.00 | 1.05 | 1.10 |

So the old 1.5x at +0.5 % is what a 1 % day limit implies; at the old 10 % limit the same logic gives 1.05x. The GitBook ladder is the same rule at Book level with a fixed dollar floor: share of equity per R = (1 − K/E) ÷ 7, from 2.9 % at $250 to 12 % at $1,250 (`G6` §3.11). That is a constant-proportion portfolio insurance (CPPI) shape. MQL5 article 1367 notes the same move in Vince: size only the funds above a minimum deposit (`MQL\1367.md:500`).

---

## 1. Every accelerator, with evidence

Each entry: mechanism, inputs and outputs, evidence, failure, and class and style. The script results are summarised in §2.3.

### 1.1 Anti-martingale and pressing when winning

- **Mechanism.** Size up after a win or during a winning run; size down after losses. Plain fixed-fraction sizing is "sometimes called anti-martingale (though, strictly speaking, it is incorrect)" (`MQL\1367.md:381`); pressing proper conditions size on recent outcomes.
- **Inputs → outputs.** last outcomes or day P&L → a size multiplier.
- **Evidence.** Theory: with independent trades the growth-optimal policy is a constant fraction (Kelly, Breiman; `R2` §4.4), so any outcome-conditioned rule can at best match a constant of the same average size. Field: professionals do press. Market makers on the Taiwan index options market "take above-average risks in afternoon trading after morning gains", in all three types of market-maker accounts (Liu, Tsai, Wang and Zhu, Management Science 56(4), 2010, ABSTRACT, https://ideas.repec.org/a/inm/ormnsc/v56y2010i4p606-620.html). Sydney Futures Exchange floor traders show the same house-money effect (Frino, Grant and Johnstone, Pacific-Basin Finance Journal 16, 2008, SNIPPET). Neither paper shows the pressing paid. The mirror behaviour, risk raised after morning losses, cost Nasdaq day traders money (`R8` §2.1).
- **Script.** Independent trades: every pressing rule earns the same growth per unit of risk as a constant (thin edge: 0.59-0.61; 55 %: 1.20-1.22) **[arithmetic]**.
- **Fails when.** Outcomes are independent (then it is a disguised size increase); many units press on one shared move (`A1-068`); the trigger fires by noise.
- **By class and style.** No class-specific evidence. It matters more for high-frequency units, because their day P&L crosses thresholds often by chance.

### 1.2 Pyramiding into winners

- **Mechanism.** Add to an open winning position, usually at fixed favourable steps, up to a cap, with stops moved so total risk does not grow.
- **Inputs → outputs.** open-trade progress in volatility units (N) → added units.
- **Evidence.** The Turtle rules add one unit every ½ N up to four units per market (SNIPPET; `MQL\23448.md` implements adds at N/2). A forum note says Covel's book gives 1 N instead (SNIPPET). The falling-risk pyramid adds only when locked profit exceeds the new risk (A1-071, author backtests). Pyramiding is the one accelerator whose trigger is the strategy's own premise: a trend trade that has moved is evidence the trend exists. Trend persistence in futures at 1-12 months is the reason (time-series momentum; Moskowitz, Ooi and Pedersen 2012, not re-read here).
- **Fails when.** The style mean-reverts (adding near the target of a scalp); gaps skip the unified stop (`R5` trap 7); partial fills; adds cluster across units on one theme.
- **By class and style.** Trend units in futures, FX trends, metals and indices: plausible. Mean-reverting scalpers: no. Crypto: weekend gaps make "risk-free" adds false.

### 1.3 Equity-curve scaling up

- **Mechanism.** Size by the unit's own recent P&L: above its moving average or positive over a window → bigger; below → smaller or off.
- **Inputs → outputs.** the unit's own last *n* trades or months → a multiplier.
- **Evidence.** For one strategy, StrategyQuant's on/off filter "doesn't improve anything"; doubling below the average made more money (A1-073, A2-055). For diversified strategies the evidence is strong at monthly horizons: across 20 academic factors from 1963, "the average factor earns 52 basis points per month following a year of gains but just 2 basis points following a year of losses" (t = 4.67; Ehsani and Linnainmaa, NBER w25551, Journal of Finance 2022, READ, https://www.nber.org/papers/w25551). The winners-only portfolio had a Sharpe ratio of 1.33 against 1.06 for equal weight; the time-series long-short version had 0.98 (same, Table 3). So most of the value came from **dropping the losers**, the brake half, not from levering the winners **[judgment]**. A one-month formation and holding period still earned 35 bp a month (t = 6.61; Table A2).
- **Fails when.** The autocorrelations break down, which happens abruptly and for many factors at once. In months when the aggregate autocorrelation index was negative, stock momentum averaged −1.6 % with a 5th percentile of −8.8 %; in positive months +2.4 % and −1.9 % (same paper, §4.6). An equity-curve accelerator crashes when persistence stops, and it stops for everyone together.
- **Script.** Slow regimes: equity-curve rule 1.16 growth per unit of risk against 0.60 for a constant; independent trades: 0.589 against 0.603 **[arithmetic]**.
- **By class and style.** Evidence is for equity factors at monthly horizons. For intraday units the persistence must be measured per unit (§2.2).

### 1.4 House money (risking gains, or a share of them)

- **Mechanism, inputs, outputs.** §0.4.
- **Evidence.** Behavioural evidence that traders do it (§1.1); lab origin Thaler and Johnson 1990 (not re-read). Firm-side house money exists in prop rules: Apex legacy accounts trade half their maximum contracts until the end-of-day balance passes initial balance + trailing drawdown + $100, for example $52,600 on a $50,000 account with a $2,500 drawdown; after that the trailing threshold stops and full size opens (SNIPPET of Apex help pages; the support site was blocked from this location). So full size is granted only once a profit cushion equal to the loss allowance exists. Theory: §0.4 (cushion rule).
- **Script.** Step form (1.5x at +0.5 %): independent trades, 0.599 growth per unit of risk against 0.603 constant; its drawdown odds match a constant at its average risk (1.12). Regime-fast: 0.646 against 0.583. Cushion form on the day ledger: 0.796 in regime-fast, 0.855 in regime-slow, 0.600 independent **[arithmetic]**.
- **Fails when.** Wins are independent; a correlated winning hour across units funds a correlated reversal (A1-067/068); the threshold is so low that noise reaches it most days.
- **By class and style.** Works where a fixed anchor and loss limit exist (day budgets, prop-style limits). For swing units with one trade a day the day ledger rarely moves, so it does little.

### 1.5 Profit ladders and step-ups

- **Mechanism.** Size or loss limit rises in discrete tiers as profit or balance reaches thresholds; falls when it drops back.
- **Evidence (live, no measured effect).**
  - Topstep Express Funded Account: the Scaling Plan "sets your Maximum Position Size ... based on your current account balance"; "Your max contracts do not increase mid-session" (READ, https://help.topstep.com/en/articles/8284223-what-is-the-scaling-plan). The tier table is an image; third-party pages say a $50K account starts at 2 contracts (SNIPPET).
  - Topstep Live Funded Account, Dynamic Live Risk Expansion (READ, https://help.topstep.com/en/articles/11748475-dynamic-live-risk-expansion): net profit sets the tier; the daily loss limit rises "after 10 Active Trading Days in the new Tier"; "If your net profit falls below your Tier at end of day, your Daily Loss Limit scales down that same day"; "If you drop out of a Tier before 10 days, the counter resets"; "You must move one Tier at a time. No skipping." For a $100K account the limit goes $3,000 → $3,500 at $15k profit, $4,000 at $20k, $4,500 at $50k; position limits stay at 10 lots until $100k profit. A balance safeguard cuts the limit to $2,000 when the end-of-day balance is at or below $10,000 and restores it after Friday's close.
  - FTMO scaling: +25 % balance for consistent traders (`R2` §2.4).
  - Ryan Jones's fixed ratio (The Trading Game, 1999): one more contract per "delta" of profit times contracts held; sources disagree on the formula; Jones also described cutting faster on the way down than adding on the way up (SNIPPET; `MQL\3280.md:211-232` describes the stepwise version).
  - Poker cash-game bankroll rules: move up when the bankroll holds 20-30 buy-ins of the next stake, move down below 15-20 of the current one; take "shots" with a pre-set stop (SNIPPET, commercial training sites).
- **Fails when.** Fixed thresholds without a gap between up and down levels flap; noise reaches a threshold; the ladder rewards luck if tiers are small next to the unit's normal swing. Topstep's first step needs $15k profit, five times the $3,000 starting limit, for +17 % more limit: a very slow accelerator.
- **By class and style.** Discrete levels suit lot-step and contract-size limits (futures, indices) where size is lumpy anyway.

### 1.6 Dose-escalation size levels

- **Mechanism.** Size is a level, moved one step at a time on cohorts of results (A1-052, `R3` §2.4).
- **New evidence.** In 2012 the FDA rejected an EWOC design and imposed accelerated titration: one patient per dose level "only until the first patient experiences a grade 2 adverse event"; after that at least 3 patients per level; "Do not increase dose by more than 100% at any time. Do not increase the dose by more than 50% after the first instance of grade 2 toxicity." (Rogatko, Cook-Wiens, Tighiouart and Piantadosi, Entropy 17(8), 2015, READ, https://pmc.ncbi.nlm.nih.gov/articles/PMC4859761/). EWOC's "defining property is that the expected proportion of patients treated at doses above the MTD is equal to a specified value α, the feasibility bound" (same, READ). Their simulations: EWOC had lower bias and error and put more patients in the optimal range than accelerated titration "without compromising safety" (same, abstract).
- **Mapping [judgment].** Accelerated titration is TCP slow start with a first-warning switch. EWOC is an accelerator with a built-in brake: raise only while P(next level is too big) ≤ α.
- **Fails when.** Cohorts are slow to fill (rare traders); the "bad event" is defined loosely; the level-to-money map is unset (A1-052).
- **By class and style.** Cohort size should be in trades for fast units and in days for slow ones.

### 1.7 Volatility-scaled leverage in calm regimes

- **Mechanism.** Exposure ∝ target volatility ÷ forecast volatility, so size rises when markets are calm (A1-010).
- **New evidence.** The Sharpe gain is confined to risk assets (equity, credit) and tied to the leverage effect; for bonds, currencies and commodities the effect on Sharpe is negligible, but extreme returns fall in every class, because large losses tend to come when volatility is already high and the position is small (Harvey, Hoyle, Korgaonkar, Rattray, Sargaison and Van Hemert, JPM 45(1), 2018, ABSTRACT via Duke listing and summaries). Volatility is the quantity that really clusters; returns barely do (Cont 2001, SNIPPET; §2.1). The failure case: across up to 211 years and 60 countries, "prolonged periods of low volatility" predicted banking crises in and out of sample, while volatility itself did not (Danielsson, Valenzuela and Zer, RFS 31(7), 2018, ABSTRACT, https://researchonline.lse.ac.uk/id/eprint/91136). Calm is when leverage builds.
- **Fails when.** A jump follows a quiet spell; the estimate lags a gap; costs of resizing. In real time across 103 strategies the gain did not hold (Cederburg et al., A1-010).
- **By class and style.** Equity indices and credit-like CFDs: Sharpe gain plausible. FX, bonds, commodities: tail control only. Crypto: weekend volatility now leads Monday risk elsewhere (`R6`). For scalpers the volatility input is the session's normal, not a daily figure **[judgment]**.

### 1.8 Kelly growth as equity rises

- **Mechanism.** A constant Kelly fraction compounds, so dollar size grows with equity. That is baseline compounding, not an accelerator **[judgment]**. It becomes one when the fraction itself rises: shrunk Kelly t² ÷ (1 + t²) rises from 0.43 at 300 trades to 0.88 at 3,000 for a +0.05R edge (`R2` §4.4), so the haircut relaxes as evidence grows.
- **Evidence.** Theory (Kelly, Breiman, MacLean-Thorp-Ziemba; `A1` 016-030). Half Kelly keeps about 75 % of growth (`R2`).
- **Fails when.** The edge estimate is inflated (selection, `R6` James-Stein); regimes change faster than the sample grows.
- **By class and style.** Thin-edge scalpers stay at a deep haircut for months; that is the "too safe" tension (A14).

### 1.9 Raising size after verification milestones

- **Mechanism.** Size steps up when a pre-set proof passes: an e-value, a trade count, a dwell in a tier.
- **Evidence.** Promote's e-process gate (`R6`); A1-054 starter budget at 10-25 %; Topstep's 10 active trading days per tier (READ, §1.5); TCP grows only on acknowledged data and restarts small after idle (`R7` §2.1). The FDA's accelerated titration switches to slower, larger cohorts at the first warning (§1.6).
- **Fails when.** Milestones are calendar-only (A1-055: "a month" means few trades for a slow unit); the proof is peeked at daily (`R3` §1.3).
- **By class and style.** Count milestones in trades or independent days, scaled to the unit's frequency.

### 1.10 Sweeps and re-seeding as accelerators

- **Mechanism.** Under a cushion rule a growing cushion raises risk (§0.4). A sweep takes profit out and resets the cushion, so it de-levers the next cycle: a slow de-accelerator. A re-seed after losses refills the cushion: an accelerator that bets on the unit's recovery (contrarian).
- **Evidence.**
  - Restart after a near-breach: Hsieh resets the drawdown when it comes within ε of the limit and restarts with a smaller gain (a forgetting factor α e^(−k/N)). Out of sample on VT (2020-2022): +20.97 % with restart, −8.42 % without, both at the 10 % drawdown cap; on BTC (2020-2022, 0.1 % costs): Sharpe 1.52 with restart against −0.04 without; without costs the maximum drawdown was **20.18 % against a 20 % cap** (2303.02613, READ). One asset each, one period, in-sample gain. The restart re-arms the sizing but voids the "never beyond d_max" guarantee across restarts.
  - Reinsurance reinstatements: after a layer pays, its limit is refilled for an extra premium, usually "100% additional premium ... pro-rata to amount" used (Munich Re, Features of Non-Proportional Reinsurance 2021, SNIPPET, example: a 400k loss on a 500k layer with 25k premium costs 20k to reinstate). A refill is priced, not free.
  - Prop: Topstep payouts "do not count as drawdown" in the live account (READ, DLRE page); in the express account a payout resets the loss limit to $0 (`R2` §5). Pods: the firm, not the PM, re-sizes the allocation (`R2` §5).
  - Microfinance progressive lending: repeat borrowers given bigger loans defaulted less, new borrowers given big first loans defaulted more, and the ladder invites "cash out" at the top (Carlson, MIT thesis and Management Science, SNIPPET).
- **Fails when.** A re-seed rewards a broken unit; a restart resets the anchor the brakes depend on.
- **By class and style.** Sweeps belong at Book or BMS level (`R2` §5, his B10).

### 1.11 Summary

| Accelerator | Best evidence | Grade | Pays only if |
|---|---|---|---|
| Pressing after wins | Kelly theory; traders do it | theory; field behaviour | results persist |
| Pyramiding | Turtle practice; trend persistence | practice; author backtests | the unit trends at its holding horizon |
| Equity-curve scaling | factor momentum 52 vs 1-2 bp | strong for factors, monthly | persistence measured for this unit |
| House money | cushion theory; prop half-size rule | theory; live practice | fixed anchor and loss limit exist, or results persist |
| Profit ladders | Topstep, FTMO, poker | live practice, no effect measure | tiers are large next to normal swing, with dwell |
| Dose levels | FDA, BOIN, EWOC | regulated practice; simulations | bad-cohort events are defined |
| Calm-vol leverage | Harvey et al.; Moreira-Muir | backtests; real-time doubts | risk-asset-like units, with a calm-duration guard |
| Kelly relaxing with evidence | theory | theory | the edge estimate is honest |
| Milestone step-ups | Promote, Topstep dwell | live practice | milestones count trades, not days |
| Sweep, re-seed, restart | Hsieh restart; reinsurance | one backtest; insurance practice | the account anchor is never reset |

MQL5 corpus check: across 3,128 article bodies, no article mentions "house money" and none tests equity-curve sizing; pyramiding is covered by 22187 and 22684 (`R5`), fixed ratio by 3280 and 12550 (mentions only) **[grep result]**.

---

## 2. Serial correlation and clustering

### 2.1 What the studies find, by timescale

| Timescale | Finding | Source |
|---|---|---|
| Seconds to minutes (prices) | Linear return autocorrelations are near zero except at very short intraday scales (about 20 minutes); volatility shows positive autocorrelation over several days | Cont, Quantitative Finance 1, 2001 (SNIPPET via 2311.07738, which finds 8 of 11 stylised facts hold in modern intraday US stocks) |
| Trade outcomes (sequences) | Measuring "win rate after k wins" inside a finite sequence is biased low. For 100 fair trials and k = 5 the expected proportion after 5 wins is about 0.35, not 0.50; for k = 3 the bias in "after 3 hits minus after 3 misses" is about −8 points. Corrected, the canonical "no hot hand" data show +13 points (p < .01) | Miller and Sanjurjo, Econometrica 86(6), 2018 (READ, 1902.01265) |
| One day (behaviour) | Professionals take more afternoon risk after morning gains (TAIFEX market makers; SFE locals) and after morning losses (Nasdaq prop traders, CBOT locals) | Liu et al. 2010 (ABSTRACT); Frino et al. 2008 (SNIPPET); `R8` §2.1 |
| Months to a year (trader level) | Taiwan day traders ranked on one year: the top 500 earned 61.3 bp a day before fees and 37.9 bp after, the next year; skill is rare and losers also persist | Barber, Lee, Liu and Odean, Journal of Financial Markets 2014 (SNIPPET of abstract) |
| Months to a year (strategy level) | Factor returns are positively autocorrelated; factor momentum explains stock momentum; persistence breaks down abruptly and together | Ehsani and Linnainmaa 2022 (READ) |
| Regimes | Sticky jump-model regimes per class (`R6` T-03); regime-dependent stop-loss value (`R8` §1.1) | `R6`, `R8` |

### 2.2 What persistence looks like in numbers [arithmetic]

- **Regimes hide from lag-1 tests.** A good/bad regime of 60 % / 45 % wins that lasts 50 trades on average produces a trade-to-trade autocorrelation of only about 0.02. Detecting ρ = 0.02 at two standard errors needs about 10,000 trades.
- **Block sums show it sooner.** Correlation of consecutive block P&L sums, and trades needed for two standard errors:

| Scenario | 1 trade | 10-trade blocks | 50-trade blocks | 200-trade blocks |
|---|---|---|---|---|
| independent | ≈0 | ≈0 | ≈0 | ≈0 |
| regime, mean length 50 trades | 0.022 (≈8,300 trades) | 0.121 (≈2,700) | 0.129 (≈12,000) | 0.038 |
| regime, mean length 500 trades | 0.021 (≈8,900) | 0.175 (≈1,300) | 0.460 (≈950) | 0.490 (≈3,300) |

  The right block size is near the regime length. A unit's persistence test should scan block sizes, with each try counted (`R6`, honest evaluation).
- **How much pressing earns.** Sizing 1 + k after a win and 1 − k after a loss adds about k × ρ R per trade over a constant of the same average size. At ρ = 0.05 and k = 0.5 that is +0.025R, half of a thin +0.05R edge; at ρ = 0.02, +0.01R.

### 2.3 Script results: accelerators and brakes on the same trade streams [arithmetic]

Growth per unit of average risk (mean log growth ÷ average risk multiplier); higher is better. P(DD>25 %) is the share of paths with a drawdown over 25 % in 2,500 trades.

| Policy | Independent, 52.5 % | Independent, 55 % | Regime, 50-trade | Regime, 500-trade |
|---|---|---|---|---|
| constant 1.0x | 0.603 (DD>25 %: 3.7 %) | 1.220 | 0.583 (28.5 %) | 0.604 (77.5 %) |
| constant 0.8x | 0.609 (1.3 %) | 1.226 | 0.589 (12.2 %) | 0.611 (63.0 %) |
| old house money step | 0.599 (4.8 %, avg 1.12x) | 1.215 | 0.646 | 0.679 |
| old reverse house money | 0.606 (2.2 %, avg 0.94x) | 1.222 | 0.621 | 0.648 |
| both old, multiplied | 0.601 | 1.216 | 0.683 | 0.721 |
| cushion on day ledger (L = 2 %) | 0.600 | 1.211 | 0.796 (19.8 %) | 0.855 (73.0 %) |
| equity curve, flip at 0 | 0.589 (7.0 %) | 1.204 | 0.831 (15.0 %) | 1.156 (63.2 %) |
| equity curve, ±5R dead band | 0.593 | 1.210 | 0.774 | 1.044 |
| AIMD on day result | 0.603 (**0.5 %**, avg 0.79x) | 1.220 | 0.700 (3.7 %) | 1.105 (46.5 %) |

Reading **[judgment]**:
- Independent trades: every rule sits on the same growth-per-risk line; accelerators buy growth with drawdown at the same rate as a bigger constant. They are neither harmful nor useful there.
- The path-dependent brake (AIMD) is the exception on the safety side: at the same growth per unit of risk it cut deep-drawdown odds well below a constant of equal average size (0.5 % against 1.3 %). Brakes reshape the drawdown tail; accelerators cannot add growth without persistence.
- With persistence, the same-ledger cushion rule and the equity-curve rule capture most of the gain; the old step and streak rules capture less.
- The 500-trade regime has a losing state (45 % wins, −0.10R) that lasts weeks: that is alpha decay that comes back. The constant sizes suffer most there.

### 2.4 Is it enough after costs?

- Accelerators do not add trades, so per-trade costs do not change; what changes is the risk carried on the trades that follow a signal. The cost of an accelerator without persistence is the extra drawdown and correlation, not fees **[judgment]**.
- Factor momentum's monthly version (35 bp a month at t = 6.61 for 1-month formation) is the cleanest positive case, but the paper's numbers are gross of trading costs, and its universe is academic factors, not intraday units.
- No study found measures win or regime persistence in intraday FX, index, metal, energy or crypto strategy P&L after costs. That is a real gap, and each unit has to measure its own (block test, §2.2) before any persistence accelerator switches on **[judgment]**.

---

## 3. The brake-accelerator pair

### 3.1 Designs where one signal drives both directions

| Design | Signal | Up | Down | Between | Source |
|---|---|---|---|---|---|
| TCP AIMD | loss signals per round trip | +1 segment per round trip | halve; timeout → 1 segment | slow start below ssthresh | `R7` §2.1; Chiu and Jain 1989: AIMD satisfies the conditions for converging to an efficient and fair state from any start (ABSTRACT) |
| TCP CUBIC | time since last loss | cubic curve with a plateau at the remembered window W_max: concave before it, convex after | ×0.7 (β_cubic) | plateau at W_max | RFC 9438 via implementations (SNIPPET: β = 0.7, C = 0.4) |
| BBR probe cycle | delivered bandwidth | one round at 1.25x (probe) | one round at 0.75x (drain) | six rounds at 1.0x | BBRv1 (SNIPPET via 1909.03673 and QUIC source) |
| Heparin nomogram | one blood test (aPTT) | < 35 s: bolus 80 U/kg, +4 U/kg/h; 35-45 s: bolus 40, +2 | 71-90 s: −2; > 90 s: hold 60 min, −3 | 46-70 s: no change | Raschke et al. 1993 nomogram (READ, perinatology.com order set) |
| Dose finding | toxicity rate per cohort | ≤ λe (0.236 at a 30 % target): up one level | ≥ λd (0.359): down; eliminate very toxic levels | stay | BOIN (`R3` §2.4) |
| SRE error budget | budget left in 4 weeks | within budget: releases continue | exhausted: halt all changes except P0 and security fixes until positive | | Google SRE workbook Appendix B (SNIPPET) |
| Topstep live tiers | net profit | one tier after 10 active days in it | same day when below tier | counter resets on drop-out | READ (§1.5) |
| Poker bankroll | buy-ins held | 20-30 buy-ins of next stake | below 15-20 of current | stay | SNIPPET |
| Apex legacy funded | end-of-day balance | full contracts after balance passes start + drawdown + $100 | (trailing drawdown until then) | half contracts | SNIPPET |
| Credit cards | repayment and borrowing behaviour | limit increases | limit cuts | | Agarwal et al.: marginal propensity to borrow falls from 59 % below FICO 660 to about 0 above 740, and banks pass extra credit least to those who want it most (NBER w21567, SNIPPET) |

Two lessons beyond `R7` **[judgment]**:
- The heparin table and BOIN both put a **dead band** between up and down, and both size the step by how far the signal is from the band. TCP and Topstep instead use **asymmetric speed** to stop chatter.
- The credit result is a warning for agent-proposed size: the party that most wants more limit is the one for whom more limit is least profitable. An agent that always asks for more size should get the slowest accelerator.

### 3.2 Asymmetric speeds

| System | Cut | Grow | Ratio of speeds |
|---|---|---|---|
| TCP Reno | halve on one mild signal | +1 segment per round trip | fast down, slow up |
| Netflix AIMD | ×0.9 per drop | +1 only when half the limit is in use | fast down, slow up (`R7` §2.2) |
| CUBIC | ×0.7 | fast far from W_max, slow near it | down fast; up depends on distance from last trip |
| Kubernetes HPA | 300 s window before scaling down | no window up | the reverse, because availability is the goal (`R7` §2.4) |
| AWS EC2 Auto Scaling | scale-in only when **all** target policies agree; blocked while new instances warm up | scale-out if **any** policy is ready, immediately | the reverse, for availability (AWS docs, SNIPPET) |
| Topstep live tiers | same day | after 10 active trading days | ≥ 10 days to 1 |
| Turtle rules | cut the sizing account 20 % for each 10 % drawdown | restore as equity recovers | cut 2x the loss (SNIPPET; attribution to Faith's book unconfirmed) |
| Pods | halve at −5 %, out at −7.5 % | the firm re-sizes later | step down, slow and discretionary up (`R2` §2.3) |
| Heparin | hold 60 minutes at the high end | bolus at the low end | both fast, because under-dosing also harms: recurrent clots were 5x more frequent on the standard-dose arm (Raschke RCT, READ) |

His A25 position ("size down, but not quickly" when live drifts from backtest) and his C19 position ("while we lose, we don't lose stupidly") are both right once speed is tied to the signal **[judgment]**:
- **Money-at-risk signals** (day loss, drawdown, loss budget burn) are facts: act fast.
- **Edge signals** (live versus backtest, cohort win rates, block persistence) are estimates: act slowly, by evidence thresholds.
- **Growth** in either case is slower than the cut, with a dwell at each level.

### 3.3 Hysteresis, so they don't flap

- **Separate trip and clear levels** (A2-008).
- **Dead band**: heparin 46-70 s; BOIN's stay zone; HPA's 10 % tolerance.
- **Dwell before the next step**: Topstep 10 active days per tier; heparin rechecks 6 hours after any change, "four half-lives ... the time required to achieve steady-state" (READ); after 2 consecutive in-range results the check interval lengthens to 24 hours. A sizing analogue: the next size change waits until enough trades have been taken at the current size to measure it **[judgment]**.
- **Counter reset on drop-out**: Topstep resets the 10-day count if the trader leaves the tier.
- **No skipping**: Topstep and BOIN move one level at a time.

### 3.4 Stopping an accelerator re-raising size straight into a brake's trip

1. **Remember the trip level.** TCP sets ssthresh to half the window at the loss; CUBIC plateaus at the remembered W_max. Regrow fast to a fraction of the trip size, then slowly near it.
2. **Brakes outrank accelerators, structurally.** Inverting AWS: cut if any brake says cut; raise only if every accelerator agrees and no brake is active. No raise while a cut is still settling (AWS blocks scale-in during warm-up).
3. **One ledger, one anchor.** If house money and its twin read the same day ledger (§0.4), they cannot point in opposite directions at the same moment.
4. **Overdose control.** Raise only while P(next level is too big) ≤ α (EWOC).
5. **Level elimination.** BOIN removes a level and all above it when it proves too toxic; a unit's tripped level could be locked for a period **[judgment]**.
6. **Never reset the account anchor.** Hsieh's restart re-arms trading but its BTC run ended at 20.18 % drawdown against a 20 % cap. Restarts may reset a unit's working anchor, never the floor.
7. **Settling time.** Wait the heparin "four half-lives": no new size change until the last one has been measured.

### 3.5 Pair results in the script

The AIMD day pair (×0.7 after a day ≤ −1.5 %, +0.05 after a green day, 0.25x-2.0x) is the only tested rule that both kept growth per unit of risk and cut deep drawdowns sharply on independent trades, and it improved growth per unit of risk under regimes (0.700 and 1.105 against 0.583 and 0.604) **[arithmetic]**.

---

## 4. Brakes in more depth

### 4.1 Money and drawdown brakes against count brakes

Healthy units, 20,000 simulated days each; share of days each brake fires **[arithmetic]**:

| Unit (all positive edge) | Trades a day | 3 losses in a row | 3 non-wins in a row | day ≤ −3R | at its own 1 % worst day |
|---|---|---|---|---|---|
| 55 % at 1:1 (+0.10R) | 4 | 14 % | 14 % | 4.3 % | 4.3 % (−4R) |
| | 10 | 41 % | 41 % | 10.5 % | 2.9 % (−6R) |
| | 16 | 59 % | 59 % | 12.5 % | 1.4 % (−8R) |
| | 40 | 91 % | 91 % | 13.4 % | 1.9 % (−10R) |
| fast-invalidation unit: 45.5 % wins, half of losers cut at −0.3R (+0.10R) | 10 | 60 % | 60 % | 8.0 % | 1.2 % (−5.2R) |
| | 40 | 98 % | 98 % | 9.4 % | 1.0 % (−8.8R) |
| scratch unit: 15 % breakevens, 47 % wins, 38 % losses (+0.09R) | 10 | 28 % | **57 %** | 12.2 % | 1.4 % (−6R) |
| | 40 | 77 % | **98 %** | 14.4 % | 1.6 % (−9R) |

(The 1 % column is not exactly 1 % because daily P&L takes few values.)

- Count brakes punish the good habit: a unit that cuts losers early has the same edge and less money at risk, yet trips "3 in a row" more often (60 % of days against 41 %).
- Counting a breakeven as a loss doubles the count brake's firing (57 % against 28 % at 10 trades). The MQL5 money-management article defines a result equal to the start as a loss (`MQL\1367.md:55`); that convention is the trap.
- A money brake set at the unit's own percentile fires at a steady rate whatever the frequency. Its level moves with frequency: −4R at 4 trades, −6R at 10, −8R at 16 and −10R at 40, rising more slowly than √N because the drift is positive.

**Drawdown rules: when they help.** Man Group's study (Van Hemert, Ganz, Harvey et al., "Drawdowns", SSRN 3583864; summary article READ, https://www.man.com/insights/youre-fired):
- At a Sharpe of 0.5 and 10 % volatility over 10 years, the chance of a maximum drawdown of 1, 2, 3 and 4 annual standard deviations is 97.1 %, 43.0 %, 9.9 % and 1.5 %.
- For managers of constant skill, a total-return rule separates good from bad better than a drawdown rule. When good managers turn bad at 0.5 % a month, drawdown rules match or beat total return, "as they put more emphasis on recent history".
- "a drawdown rule might be considered ... 'poor man's volatility scaling'"; "Taking risk in bursts will increase the probability of hitting a certain drawdown level"; they suggest "a time-varying drawdown rule", because the chance of touching a level rises with time even for an unchanged manager.

Reading **[judgment]**: a drawdown brake is a decay detector, not a skill measure. That is the old circuit breaker's real job (his A26). Its threshold should widen with time in service, or be read as a rate.

### 4.2 Brakes that scale with trade frequency

- Daily P&L spread grows with √N trades; drift grows with N. A fixed money limit is loose for slow units and tight for fast ones; a fixed count limit is worse (table above).
- Two ways to scale **[judgment]**: (a) set the limit at the unit's own k-th percentile for its trade count, from its record or its approved backtest; (b) express it in daily standard deviations, σ_day = √N × σ_trade × risk per trade.
- Low-frequency units hit the SRE "low-traffic" problem: one loss is a large share of the budget (`R3` §3.5). Require a minimum number of events before a count signal (`R3` §2.5).
- Burn-rate brakes (A2-028) already scale: they compare spend with elapsed time, not with a count.

### 4.3 Fast-invalidation cuts and breakeven exits

- In money, a cut counts by its size and a breakeven by its costs. In counts, both look like losses or, worse, like "non-wins". Medicine grades events by severity and counts only the serious ones as dose-limiting: EWOC "can be implemented ... for ... ordinal toxicity grades" (Rogatko et al. 2015, READ); the FDA's titration switch fired on the first grade 2 event, not on any event (READ).
- Two ledgers **[judgment]**: a **money ledger** that brakes act on (cuts by size, scratches at cost), and an **event ledger** (fast-invalidation rate, scratch rate, full-stop rate, stop-slippage) that is decay evidence. A rising full-stop share or falling fast-invalidation precision says the edge is changing before money shows it; this is the old fire-density idea (`G3` §4, WF3) moved to the right signal.
- Breakevens should neither extend nor reset a loss streak in any count rule that survives **[judgment]**; the script shows the difference is a factor of two.
- His M15 note that the intraday "dynamic SL/TP" moved the stop to breakeven "depending on how much you are winning", while fast invalidation replaced it for scalpers (`OW3:97`), means breakeven exits will be common for intraday units, so this choice matters there most.

### 4.4 Prop-firm and pod drawdown rules

| Rule | Measured in | Anchor | Shape | Source |
|---|---|---|---|---|
| FTMO daily loss 3 % or 5 % | money, on equity incl. open trades | midnight CET balance | trip | `R2` §2.3 |
| FTMO total loss 10 % | money | static (2-step) or trailing end-of-day high (1-step) | trip | `R2` |
| Topstep live daily loss limit | money | day | trip; tier-linked size (§1.5) | READ |
| Topstep balance safeguard | money | balance ≤ $10,000 or ≤ $5,000 | step down; restore after Friday close | READ |
| Topstep "shoulder tap" | human review | losses from starting balance | discretionary | READ |
| Apex legacy funded | money | trailing threshold until start + drawdown + $100, then fixed | half size until then | SNIPPET |
| Millennium (press) | drawdown % | from peak | halve at −5 %, out at −7.5 % | `R2` §2.3 |
| Multi-manager norms (forums) | drawdown % | high-water mark | "soft stop" at the first level, "hard stop" at the second; risk desks expect de-grossing before either | SNIPPET (Wall Street Oasis) |
| BlueCrest (2010 press) | drawdown % | allocation | halve at −3 %, lose the allocation at a further −3 % | SNIPPET (Monevator) |

Every one is in money or drawdown; none counts trades or losses **[judgment]**. Every pod rule cuts by a large step at the first level, and none restores automatically; Topstep is the only one found with an automatic, rule-based restore.

---

## 5. Ideas from other fields

| Field | Mechanism | Both directions? | Speeds and hysteresis | Evidence | Borrow [judgment] |
|---|---|---|---|---|---|
| Congestion control | AIMD, slow start, ssthresh, CUBIC plateau, BBR probe/drain | yes | down fast, up slow; remembers the last trip | production standards; AIMD convergence proof (ABSTRACT) | memory ceiling; probe cycle for unknown capacity; AIMD shares converge to fair splits among units sharing one budget |
| Autoscaling | AWS any/all rule; default cooldown 300 s; instance warm-up; HPA windows | yes | asymmetric by policy; warm-up blocks the opposite move | vendor documentation (SNIPPET for AWS, READ in `R7` for HPA) | "cut if any brake, raise only if all agree"; no raise during a cut's settling time |
| Adaptive dosing | heparin nomogram; accelerated titration; EWOC; BOIN | yes | dead band; recheck after four half-lives; first-warning switch; overdose bound α | one RCT (heparin: 97 % against 77 % reached therapeutic level in 24 h, fewer recurrences); FDA practice; simulations | scale the starting size to the unit (as dose to weight), not a standard dose; settle before re-adjusting; overdose control on accelerators |
| Credit limits | line increases on repayment and behaviour; progressive microloans | yes | increases earned over time | regression discontinuities on 8.5 million accounts (SNIPPET); digital-credit studies (SNIPPET) | price an increase by who wants it; ladders invite "cash out" at the top |
| Reinsurance | layers (retention, limit); reinstatement for a premium pro rata to the amount used; hours clause (A2-026) | refill after loss | refill is paid | market practice (SNIPPET, Munich Re) | a re-seed or restore is earned or priced, never free |
| Sports betting and poker | fractional Kelly (`R6`); bookmakers limit winners; bankroll move-up and move-down | yes | move up at 20-30 buy-ins, down below 15-20 | Kaunitz et al.: +8.5 % on 265 real $50 bets, then stakes limited to as little as $1.25-$11.11 (READ, 1710.02824); poker rules are practitioner lore | a proven edge meets a capacity ceiling set by the other side: accelerators need a capacity cap per venue |
| Audio dynamics | compressor, limiter, gate, expander; threshold, ratio, knee, attack, release | yes | attack and release set separately | engineering standard (READ, MathWorks) | a shared vocabulary for brake and accelerator settings |

---

## Accelerator designs worth carrying

Each is research input, not a design. Evidence first, then the condition under which it pays.

1. **Same-ledger cushion sizing (house money and reverse house money as one rule).**
   - Evidence: theory (Grossman-Zhou; Hsieh-Barmish lemma, READ); script: equal growth per risk on independent trades, +37 % (0.796 against 0.583) and +42 % (0.855 against 0.604) under regimes **[arithmetic]**; the GitBook ladder already had this shape (`G6` §3.11).
   - Pays when: a fixed anchor and a real loss limit exist at that scope, and the extra size is funded from profit above the anchor. Without persistence it only moves risk around; with persistence it presses the good regime.
2. **Tiered step-up with dwell and same-day step-down (the Topstep pattern).**
   - Evidence: live real-money rules (READ).
   - Pays when: tiers are wide next to the unit's normal swing (Topstep's first tier is 5x the starting loss limit), the dwell counts active days or trades, and levels are never skipped.
3. **Slow start with a first-warning switch, for new or returning units.**
   - Evidence: FDA accelerated titration (≤ 100 % steps until the first grade 2 event, then ≤ 50 % and 3 per cohort, READ); TCP slow start (`R7`).
   - Pays when: "warning" is defined as an event in money or a graded event, and the unit starts at a level where a fast early climb is cheap.
4. **Persistence press, switched on only after the unit's own block test passes.**
   - Evidence: factor momentum (52 bp against 1-2 bp a month, READ); script: equity-curve rule 1.156 against 0.604 under slow regimes **[arithmetic]**.
   - Pays when: block-sum autocorrelation at the unit's horizon is positive and significant with tries counted (about 950 trades for a 500-trade regime, more for faster ones). The brake half (cut after a bad block) carried most of the factor-level value.
5. **Falling-risk pyramiding for trend units only.**
   - Evidence: Turtle practice (SNIPPET), MQL5 22187/22684 (author backtests), trend persistence literature.
   - Pays when: the unit's returns trend at its holding horizon and gaps are small next to the stop; never for mean-reverting scalpers.
6. **Calm-volatility scaling with a calm-duration guard.**
   - Evidence: Harvey et al. 2018 (risk assets only, ABSTRACT); Danielsson et al. 2018 (long calm precedes crises, ABSTRACT).
   - Pays when: the unit trades equity-index or credit-like risk, the multiplier is capped, and a long calm spell stops further levering.
7. **Overdose-controlled level steps (EWOC-style).**
   - Evidence: EWOC's defining property and simulations against accelerated titration (READ).
   - Pays when: there is a model of how bad-cohort risk rises with size, so P(next level too big) can be estimated.
8. **Probe-and-drain for unknown capacity.**
   - Evidence: BBR in production (SNIPPET); no trading test.
   - Pays when: the limit is capacity, slippage or venue tolerance (Kaunitz's bookmaker limits), not edge.

## Brake-accelerator pairings

Each is one pair with a shared signal and asymmetric speeds.

| Pair | Shared evidence | Brake side (speed) | Accelerator side (speed) | Anti-flap |
|---|---|---|---|---|
| P1 Day ledger | realised P&L (and open risk) since the day's start, per scope | below anchor: size × (L + P)/L, continuous; stop at −L (fast) | above anchor: extra risk ≤ share of profit (only on realised profit) | one anchor, so no contradiction; resets at the day boundary with a minimum bench rest (A2-116) |
| P2 Tier ladder | net profit in tiers | same day when below tier (fast) | one tier after a dwell of active days or trades (slow) | no skipping; counter resets on drop-out (Topstep) |
| P3 AIMD with memory | loss-budget breaches | ×0.7 per breach day (fast) | +5 % per good day, slowing near the last trip level (slow) | remembered trip level (ssthresh, CUBIC) |
| P4 Three zones | cohort or evidence score | red: down one level or trip | green: up one level | yellow: hold and gather evidence (Basel, BOIN, heparin dead band) |
| P5 Burn-rate permit | loss budget burn over two windows | fast burn: halt; slow burn: size down | healthy budget: accelerators allowed | exhausted budget freezes accelerators until positive (SRE policy) |
| P6 Block persistence | unit's own block P&L | bad block: ease size (this half carried most of the factor evidence) | good block: press | dead band (±5R in the script) |
| P7 Volatility | forecast against normal volatility for that session | spike: cut at once | calm: raise toward a cap, slowly | calm-duration guard |
| P8 Start-up | events since promotion or restart | first warning: halve and switch to small steps | slow start: double per clean cohort | settle before the next step (four half-lives idea) |

Across all pairs **[judgment]**: brakes outrank accelerators (any brake blocks every raise); money signals act fast and edge signals slowly; no raise while a cut is settling; restores are the brake's own clear rule and never reset the account floor.

## Numbers worth carrying

| Number | Source |
|---|---|
| Average factor: 52 bp a month after a positive year, 1-2 bp after a negative one (t = 4.67); time-series factor momentum Sharpe 0.98, winners 1.33, equal weight 1.06 | Ehsani and Linnainmaa, NBER w25551 (READ) |
| Momentum in months of negative factor autocorrelation: mean −1.6 %, 5th percentile −8.8 %; positive months +2.4 % and −1.9 % | same |
| Streak bias: after 5 wins in 100 fair trials the expected proportion is about 0.35; the "after 3 hits minus after 3 misses" gap is biased about −8 points; corrected hot-hand effect +13 points | Miller and Sanjurjo 2018 (READ) |
| Linear return autocorrelation near zero beyond about 20 minutes; volatility clusters over days | Cont 2001 (SNIPPET) |
| Top 500 Taiwan day traders: 61.3 bp a day before fees, 37.9 after, next year | Barber et al. 2014 (SNIPPET) |
| A 50-trade regime of 60 %/45 % wins gives lag-1 autocorrelation of about 0.02 (≈10,000 trades to detect); 50-trade blocks detect a 500-trade regime in about 950 trades | `R9-scripts` **[arithmetic]** |
| Pressing 1 ± k adds about k × ρ R per trade (ρ = 0.05, k = 0.5 → +0.025R) | **[arithmetic]** |
| Independent trades: all accelerators 0.59-0.61 growth per unit risk against 0.603 constant | **[arithmetic]** |
| AIMD day pair: P(drawdown > 25 %) 0.5 % at 0.79x average risk, against 1.3 % for constant 0.8x | **[arithmetic]** |
| Cushion multiplier (L + P)/L: 1.5x at +0.5 % with a 1 % limit; 1.05x with a 10 % limit | **[arithmetic]** |
| "3 losses in a row" fires on 41 % of days at 10 trades (55 % unit), 60 % for an equal-edge fast-invalidation unit, 91 % at 40 trades; "3 non-wins" with 15 % scratches 57 % | **[arithmetic]** |
| Unit's own 1 % worst day: −4R at 4 trades, −6R at 10, −8R at 16, −10R at 40 (55 % unit) | **[arithmetic]** |
| Topstep live: up one tier after 10 active days, down the same day; $100K: $3,000 → $3,500 / $4,000 / $4,500 at $15k / $20k / $50k profit; safeguard $2,000 at balance ≤ $10,000 | Topstep help (READ) |
| Topstep express: max contracts never rise mid-session | Topstep help (READ) |
| Apex legacy: half contracts until balance passes start + drawdown + $100 ($52,600 on $50K) | Apex help (SNIPPET) |
| Pods: halve at −5 %, out at −7.5 % (Millennium, press); halve at −3 %, out at −6 % (BlueCrest 2010, press) | `R2`; Monevator (SNIPPET) |
| Max drawdown ≥ 2 annual σ over 10 years at Sharpe 0.5: 43 %; ≥ 3σ: 9.9 % | Man Group, "You're fired" (READ) |
| Drawdown rules beat total-return rules only when skill decays (0.5 %/month migration in their test) | same |
| FDA titration: ≤ 100 % dose steps until the first grade 2 event; then ≤ 50 % and ≥ 3 patients per level | Rogatko et al. 2015 (READ) |
| EWOC: expected share of patients above the MTD equals the feasibility bound α | same |
| Heparin: dead band 46-70 s; recheck 6 h after any change (≈ four half-lives); 97 % against 77 % therapeutic within 24 h; recurrence risk ratio 5.0 for standard dosing | Raschke et al. 1993 (READ) |
| CUBIC: multiplicative decrease 0.7; plateau at the last window before loss | RFC 9438 via code (SNIPPET) |
| BBR probe cycle: 1.25, 0.75, then six rounds at 1.0 | BBRv1 (SNIPPET) |
| AWS: default cooldown 300 s; scale out on any policy, scale in only when all agree; scale-in blocked during warm-up | AWS docs (SNIPPET) |
| Restart after near-breach: VT +20.97 % against −8.42 %; BTC Sharpe 1.52 against −0.04 (0.1 % costs); max drawdown 20.18 % against a 20 % cap | Hsieh 2023, 2303.02613 (READ) |
| Credit: marginal propensity to borrow 59 % below FICO 660, about 0 above 740 | Agarwal et al., NBER w21567 (SNIPPET) |
| Betting: +8.5 % on 265 real $50 bets, then stakes cut to $1.25-$11.11 by bookmakers | Kaunitz et al., 1710.02824 (READ) |
| Volatility targeting: Sharpe gain only for risk assets; tails cut in all classes | Harvey et al. 2018 (ABSTRACT) |
| Long calm volatility predicts banking crises; volatility level does not | Danielsson et al. 2018 (ABSTRACT) |

---

## Not verified

- **Snippet-only**: Cont's 20-minute figure; Barber et al.'s 61.3 / 37.9 bp; Apex's safety-net rule (its support site was blocked from this location); Topstep's express tier table (an image); the SRE error-budget freeze wording; AWS any/all and warm-up wording; CUBIC and BBR constants (from implementations citing the RFC and draft); the Turtle 20 %-per-10 % drawdown rule and its attribution; Ryan Jones's formula; poker bankroll thresholds; Munich Re reinstatement example; credit and microfinance figures; Frino et al.; BlueCrest and forum pod levels.
- **Abstract-only**: Liu et al. 2010 (no performance-after-pressing figure); Harvey et al. 2018; Danielsson et al. 2018; Chiu and Jain 1989.
- **Not re-read here**: Moskowitz-Ooi-Pedersen time-series momentum; Thaler-Johnson; Getmansky-Lo-Makarov; Grossman-Zhou (cited via `R2`).
- **Gaps**: no study of win or regime persistence in intraday retail-style strategies after costs; no study measuring whether house money pays for professional traders (only that they do it); no source on how pods restore a cut allocation; Topstep publishes no effect measure for its tiers.
- **Model limits**: the script uses ±1R trades (plus −0.3R cuts and 0R scratches in part 2), independent within a regime, no costs beyond the win rate, no gaps, one unit at a time with no correlation across units, 400 paths per scenario (so P(DD) figures carry about ±2 points of noise). Fat tails, gaps and correlated units make every drawdown number worse and every accelerator riskier.
