# G3: The old system's risk and sizing, recovered

Written 2026-11-01 by grounding reader G3. Read-only recovery. Nothing here is a design or a ruling.

## How to read this

**Labels.**
- **SRC**: stated in the old folder. Path and line given.
- **OP**: the operator's own words in a primary transcript.
- **SUM**: taken from an earlier summary and not re-checked line by line.
- **MINE**: my own reading, arithmetic or trader judgment. Never a source fact.

**Short paths.**

| Alias | Path |
|---|---|
| `V` | `C:\Users\Mubarak\Documents\Claude\QMX-discussion\` (the old folder) |
| `R0`..`R7` | `V\02-Components\01-risk-and-sizing\` files `00-overview`, `01-canonical-formula`, `02-multiplier-stack`, `03-equity-bands-and-tiers`, `04-slot-competition-model`, `05-session-architecture`, `06-kill-switch-and-sl-tp-integration`, `07-known-gaps` |
| `CB`, `KSA`, `PTDS`, `PRS`, `BT`, `BRL` | `V\02-Components\` `02-circuit-breaker-policy-engine`, `09-kill-switch-authority`, `08-paper-trading-demotion-service`, `06-performance-rating-service`, `11-backtest-engine`, `07-bot-registry-and-lifecycle` |
| `PRD`, `PROT`, `BS` | `V\bmad-docs\planning-artifacts\prd.md`, `...\qml-protocols-catalogue.md`, `V\bmad-docs\brainstorming\brainstorming-session-2026-04-28-125147.md` |
| `GPTR` | `V\07-Source-Material\gpt-trading-algorithm-research.md` (April GPT conversation, operator dictation) |
| `CORE` | `V\.brain\entities\qmx-new-core.md` (July Book/BMS core) |
| `CFS` | `C:\Users\Mubarak\Downloads\Coding-formulas-strategies.md` (Sep 2026 ChatGPT sitting, outside `V`; read for the operator's own words only) |
| `G01`, `G02`, `G06`, `G09` | `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\grounding\` `01-old-system`, `02-book-and-prior-sims`, `06-qrmx-transcript-recovery`, `09-original-design-recovery` |
| `R08`, `R19`, `R21` | `D:\QMX-worktrees\risk-plan\tracker\risk-sizing\research\` `08-old-qmx-testing-and-decay`, `19-grounding-old-system`, `21-old-system-loose-ends` |

---

## 1. Which "old system" this is

The old folder holds three designs. Mixing them causes most misreadings (`R19` §"Three eras").

1. **April to May 2026, the vault.** Kelly sizing, nine multipliers, six caps, three slots, sessions, house money. This is the system the operator calls "old" and "radioactive". It is the subject of this file. SRC (`R0`..`R7`).
2. **July 2026, the Book/BMS core.** Books, Treasury cycles, seven doors. It forbade compounding between cycles and put "declared-weight multiplier stacks" on the dead list (`CORE:31-34, 46-49, 63-67`). That is the *current* side of the operator's comparison, not the old side.
3. **October 2026, Claude sessions.** Loss points, the 40% kill line, "risk today's winnings". These are new proposals, not old design (`G06` §2.2-2.4).

**Words that are not old-system words.** SRC by grep over all of `V`:
- **"Radioactive"** appears nowhere in `V`. It is the operator's October label for the April system (`R19:215`).
- **"Loss points"** appears nowhere in `V`. Claude proposed it on 6 Oct 2026 (`G06` §2.2).
- **"Session capital"** appears nowhere in `V` as a term. The idea is in the operator's own words in `CFS:1317` (see §4.1). In the vault it exists only as a side effect: sizing reads current equity on every trade.

**What the operator says the old system was.** OP:
- "it uses a more enhanced Kelly plus other things yeah it is standardized to my own liking" (`GPTR:50`, via `R19` §5).
- "there is that formula i can't give it to you it's a bit uh contemporary" (`GPTR:19556`).
- "If it's trading across let's say seven total sessions with House of money and reverse house of money Those things like made the system very insane… that thing can't lose" (`CFS:706`).
- Old code location: `src/router/enhanced_governor.py — Kelly + house money` (`GPTR:7077`). The code was lost in the laptop crash.

---

## 2. The model, step by step

Every number below is the source's default or illustration. `R3:19` and `R3:74` say the real values live in an "account-tier registry" that was never written down.

### Step 0: safety gates (before any sizing)

Session, warm-up, kill switch, news, two breaker hits today, spread, chaos regime, missing data, slots full. The first "no" stops the trade. SUM (`G01` §2, citing `V\02-Components\00-QML-shared-library\04-QML-runtime.md:155-165`).

### Step 1a: fee gate

- **Net R:R** = average win after fees ÷ average loss after fees. "R" means one unit of the money risked on a trade.
- If net R:R is below **1.1**, the trade is blocked. SRC (`R1:66-71`).
- The old code used a weaker gate (fees ≥ average win). That is Gap 3 (`R7`).

### Step 1b: half-Kelly base

- **Kelly** is a formula for the fraction of capital to bet that maximises long-run growth, given a win rate and a payoff ratio.
- `raw_kelly = ((net_RR + 1) × win_rate − 1) / net_RR`
- `base_kelly = max(0, raw_kelly) × 0.5`. Half-Kelly is a safety margin against wrong estimates. SRC (`R1:79-80`).
- Inputs: the vault says the bot's figures; the 28 Apr decision D1 says "paper-trading realized stats (not planned R:R)" (`BS:105`); the PRD says Kelly comes "exclusively from the bot's own paper-trade record" (`PRD` FR11, line 884).

### Step 1c: nine multipliers

Each defaults to 1.0 (neutral) when its data is missing. A value of 0 blocks the trade. SRC (`R2` table and definitions).

| # | Multiplier | Rule | Range | Line |
|---|---|---|---|---|
| 1 | DPR (bot rating) | T1 1.00, T2 0.75, T3 0.50, below minimum 0 (block) | 0–1 | `R2:44` |
| 2 | Session | per window and family, from history; premium windows near 1.2, OVERNIGHT near 0.5 | 0.5–1.2 | `R2:62` |
| 3 | House money | 1.5 if the slot's day P&L ≥ threshold, else 1.0 | 1.0–1.5 | `R2:81` |
| 4 | RVOL (relative volume) | below 0.5 → block; above 1.5 → 1.0; else rvol ÷ 1.5 | 0–1.0 | `R2:99` |
| 5 | Physics (chaos measures) | block if Ising ≥ 1.0 or Lyapunov above threshold; else 1 − score, floor 0.1 | 0–1 | `R2:126` |
| 6 | Correlation | `max(0.3, 1 − penalty)` | 0.3–1 | `R2:146` |
| 7 | Drawdown pressure | `max(0.2, 1 − (day loss ÷ day limit)²)` | 0.2–1 | `R2:164` |
| 8 | Microstructure (spread and depth) | `clamp(1 − 0.5 × score, 0.5, 1.0)` | 0.5–1 | `R2:182` |
| 9 | Reverse house money | ORB-led windows only: losses this session <2 → 1.0; 2–3 → 0.7; 4+ → 0.5 | 0.5–1 | `R2:203` |

`candidate_risk_pct = base_kelly × all nine`. SRC (`R1:88-99`).

### Step 2: six caps (the lowest wins)

`final_risk_pct = min(candidate, family_slot_cap, tier_kelly_cap, open_risk_remaining, family_budget_remaining, daily_loss_remaining)`. SRC (`R1:112-119`).

**Equity bands.** A band is a size class of the account, set once a day from closing equity, with no buffer zone against flip-flopping. SRC (`R3:13, 100`).

| Band | Daily loss limit | Open-risk ceiling (all open trades together) | Tier Kelly cap | Scalper cap per trade | ORB cap per trade |
|---|---|---|---|---|---|
| Growth (small account) | 10% | ~2.5% | 2.0% | 0.5% | 0.8% |
| Scaling | 5% | ~3.5% | 1.5% | 0.75% | 1.2% |
| Guardian (large account) | 3% | ~5.0% | 1.0% | 1.0% | 1.5% |

SRC (`R3:23-25, 70-72`). The thresholds between bands were never given (`R3:19`). ORB means "opening-range breakout", the second bot family beside scalpers.

**Deliberately absent: a per-session cap.** "The system's compounding edge accumulates across sessions… A hard per-session dollar ceiling would sever this compounding loop… not negotiable." SRC (`R1:137`; `R0:46`). Design principle 5: "Compounding is the edge, drawdown is the floor… The only stop is daily drawdown thresholds (the 357 rule)." SRC (`V\01-System-Overview\01-system-overview.md:15`).

### Step 3: money and lots

- `risk_cash = current_equity × final_risk_pct`. Current equity, read at the moment of each trade. SRC (`R1:121`).
- `lots = risk_cash ÷ (stop_pips × pip_value_per_lot)`, then clamped to the broker's minimum and maximum lot and rounded to the lot step. Zero lots → blocked as `below_min_lot`, which does not count against the bot. SRC (`R1:146-159`).

---

## 3. Worked example from $300

MINE, using the source formulas. Assumptions: EURUSD scalper, Growth band, 60% win rate, average win $12 and average loss $8 after fees, 10-pip stop, $10 per pip per standard lot.

1. Net R:R = 12 ÷ 8 = 1.5. Passes the 1.1 gate.
2. Raw Kelly = (2.5 × 0.6 − 1) ÷ 1.5 = 0.333. Half-Kelly = **16.7%**.
3. Multipliers at London open, slot not yet in profit: DPR 1.0 × session 1.2 × house money 1.0 × RVOL 0.8 × physics 0.9 × correlation 1.0 × pressure 1.0 × micro 0.9 × reverse 1.0 = 0.78. Candidate = **13.0%**.
4. Caps: scalper cap 0.5%, tier cap 2.0%, open risk left 2.5%, day loss left 10%. Final = **0.5%**.
5. Risk cash = $300 × 0.5% = **$1.50**. Lots = 1.50 ÷ (10 × 10) = 0.015, which rounds to 0.01 lot (**$1.00** at risk, 0.33%) or 0.02 lot (**$2.00**, 0.67%). The source does not say which way it rounds.
6. A win at 1.5R adds about $2.25. The next trade sizes off **$302.25**. After a good Tokyo session, London starts on a larger balance. That is the "session capital" effect (§4.1).
7. One win of +0.75% clears the provisional house-money threshold (>0.5%, `PROT:3135`). The candidate jumps to 19.4%. Final size **does not change**: the 0.5% cap still binds.
8. The day stops when realised losses reach 10% of start-of-day equity, about 20 full losses at 0.5% each.

**What this shows.** MINE. With any real edge, half-Kelly is 15 to 30 times the per-trade cap. The cap almost always binds. So in the written spec the old system was, in practice, **fixed-fraction sizing: 0.5% (scalper) or 0.8% (ORB) of current equity per trade**, compounding on every fill, with up to 10% loss allowed per day. The nine multipliers only change the trade when one is zero (a block) or when the edge is tiny. `G01` §2 reached the same conclusion (line 124). The source's own claim that 1.5× is "the maximum booster the clamp can absorb" (`R5:112`) does not hold arithmetically.

**But the old code may have run much hotter.** MINE, from SRC gaps. Gap 1: the scalper/ORB cap was computed but "never passed into the final min()" (`R7` Gap 1). Gap 4: the open-risk ceiling was fixed at 5%. Gap 6: some multipliers were applied twice, so house money could act as 2.25×. With the per-trade cap missing, the binding cap becomes the tier Kelly cap: **2% per trade** at Growth, four times the spec. Any old simulation that "couldn't lose" may have reflected this, not the spec. No old simulation scripts or results survive (`G02` §2.1).

---

## 4. Each mechanism

### 4.1 Session capital (multi-session compounding)

- **What.** One pot of money passes through the day's sessions in order: Sydney/Tokyo, then London, then New York, with the overlaps in between. Each session sizes off whatever the last one left. OP: "the capital that starts in Tokyo… it's not the same capital that reaches London… New York. Those are three different types of capitals… it has been used by the bots in the sessions" (`CFS:1317`).
- **How in the spec.** No separate session pots. It is a result of `current_equity × final_risk_pct` plus having no per-session cap. SRC (`R1:121, 137`).
- **When.** Every trade. The equity band only changes at day rollover (`R3:13`).
- **Why.** The edge comes from compounding many small trades, not from speed. The founding story: *The Hummingbird Project*, "being fast an absurd amount of times" (`G02` §2.3, second-hand). The vault: "let capital compound across sessions without exposing the book to ruin" (`R0:11`).
- **Ten UTC windows** from SYDNEY_PRE (20–22) to OVERNIGHT (19–20); hours 02–07 and 11–12 are in none. SRC (`R5:21-32`; `G01` §6.1).

### 4.2 House money (HME)

- **What.** When the slot is up on the day, the next trade's candidate risk is multiplied by **1.5**. SRC (`R2:75-84`).
- **Trigger.** The slot's day P&L as a % of start-of-day equity crosses `HOUSE_MONEY_THRESHOLD`. The vault never gives the value. The protocol catalogue gives a provisional default: above 0.5% of equity per session (`PROT:3135`).
- **Scope.** The vault ties it to the **slot**: a new bot entering a slot inherits it (`R5:96-110`). The 28 Apr decision D3 says the opposite: "House money is bot-scoped, resets on swap, session-aware activation" (`BS:107, 161`).
- **Off** during the London–NY warm-up (the first 1,500 seconds, ORB only). SRC (`R5:264-268`).
- **Cap rule.** House money + reverse house money ≤ 1.25 × RVOL multiplier in sessions with a dominant family. SRC (`PRD:887`; `PROT:3145`). Marked provisional.
- **Why.** OP: "since you have house of money effect, which increases the risk, we actually give the bots more… But remember, we are already holding most of that drawdown" (`GPTR:19556`). The vault: profit above the day's plan is a buffer, so size can grow without risking the day's starting equity (`R2:75`).
- **In practice.** Inert under the 0.5% cap (§3). MINE, matches `G06` §2.2.

### 4.3 Reverse house money (RHME)

- **What.** It shrinks size during a losing streak: under 2 losses → 1.0; 2–3 → 0.70; 4–5 → 0.50; 6+ → 0.50 (floor). SRC (`R2:197-213`; `R5:135-148`).
- **When.** Only in windows where ORB is the dominant family (London peak, London–NY overlap, NY open). Streaks count per slot per session. SRC (`R5:21-32, 135`).
- **Why.** ORB setups fail often but win big; long losing streaks are normal for them. Cutting size during a streak limits the damage while the family's signal recovers. SRC (`R5:150`).
- **With house money.** 1.5 × 0.5 = 0.75. The streak counts as stronger evidence than the earlier profit. SRC (`R5:156-162`).
- **Note.** The PRD says "Reverse-house-money compounds normally outside dominant sessions" (`PRD:887`), while the vault says it is 1.0 outside ORB windows. Unresolved.

### 4.4 Premium sessions and the session multiplier

- A window is "premium" when its history beats the session median by 1.25 standard deviations. The flag is re-earned daily. SRC (`V\02-Components\04-market-intelligence-service.md:150-158`, via `G09` A.5).
- Effects: the dominant family's session multiplier moves toward 1.2, and the tier Kelly cap "may be marginally relaxed" (amount never given). SRC (`R5:116-125`).

### 4.5 Daily loss ceiling ("the 357 rule")

- **What.** No new trades after realised loss today reaches the band's limit: 10% Growth, 5% Scaling, 3% Guardian. Resets at day rollover. SRC (`R3:30-36`; `KSA:98`).
- **Escalation.** At 90% of the limit → YELLOW warning. At the limit → ORANGE, no new entries for the rest of the day. A "hard account drawdown lock" → RED, with no threshold given. SRC (`KSA:98-104`).
- **"357".** Named once (`V\01-System-Overview\01-system-overview.md:15`) and never defined. MINE: the band limits are 10/5/3, not 3/5/7. It may echo the common retail "3-5-7" rule (3% per trade, 5% total exposure, 7% target), or an older band table. Unknown.
- **Only realised losses count.** Open losses are not mentioned (`G01` G29).

### 4.6 Drawdown pressure (soft brake)

- `max(0.2, 1 − (loss used ÷ limit)²)`. At 50% of the day's limit used → 0.75; at 80% → 0.36; at about 90% or more → 0.2. SRC (`R2:162-164`).
- **Why.** Without it, trades stay full size up to the last dollar of the budget. SRC (`R2:167`).
- **In practice.** Inert under the cap with a real edge (MINE, §3).

### 4.7 Slots, family budget and correlation

- **Three slots**, fixed. More equity means more dollars per slot, not more slots. SRC (`R4:19-24`). The operator remembers slots tied to "current capital" and probably increasing: OP (`GPTR:19556`; `CFS:1317`).
- **How a bot got a slot.** The vault uses a scored auction at each window boundary: DPR tier weight × regime fit × session relevance (`R4:44-78`). The operator's version: "the boat that actually gets uh the setup first is the one that goes into our slot" (`GPTR:19556`).
- **Family budget.** Each family has a daily risk budget = slot cap × session count ("illustrative"). R1 says it resets per session; R4 says it is daily. SRC (`R4:128-133`; `R1:132`).
- **Correlation, three control points.** The funding-stage score cut (missing in old code, Gap 5); the sizing multiplier with a 0.3 floor; and the Intent Aggregator, which drops intents that push portfolio correlation too high (`R4:80-120`; `R19` §2).

### 4.8 Circuit breaker (two strikes per day)

- First hit: record it, and the bot keeps trading. Second hit in the UTC day: demote to paper or demo, free the slot. Reset at rollover. SRC (`CB:17-23`).
- **What a "hit" is.** CB says: a loss streak over threshold, fee burn over a share of the daily budget, failing to recover from a drawdown N times, or the rating dropping mid-session. All thresholds are missing (`CB:46-51`). Other files say every full-stop loss is a hit (`R6:124`). OP: "if a bot hits two consecutive losses… it stops trading… downgraded to paper trading" (`GPTR:19556`).

### 4.9 Stops and why the stop is one-shot

- The stop moves once, to entry plus spread, at +1R. It never trails after that. Take-profit extends while continuation looks likely. SRC (`R6:93-120`).
- **Why.** If stops trailed, a bad bot would show many small losses instead of clean full stops, and the circuit breaker would fire late. SRC (`R6:122-128`).
- MINE: this is a sizing fact too. Average losses stay near −1R, so Kelly inputs are honest on the loss side but overstated on the win side (winners exit early). `R0:168-169` flags this.

### 4.10 Kelly probation discount

On first live promotion, Kelly is multiplied by about **0.85** until the bot leaves probation. The exit criteria were never set. SRC (`PRD` FR63, line 975; `BS` D10). `BRL:121` calls it "a fresh multiplier", which breaks the "locked nine" rule (`G01` G17).

### 4.11 Not in the old system

- **Loss points, benching by points, a 40% kill line, "risk today's winnings", a size ramp to a Kelly ceiling over about a month**: October 2026 proposals (`G06` §2.2-2.4).
- **Treasury cycle** (seed $500, kill line $200, cap 2.5× seed, sweep at rollover, equity reset to seed, no compounding between cycles): July 2026 Book core (`CORE:46-49`). It pulls the opposite way from the April system on compounding (`R19` §5).

---

## 5. Testing and decay checks tied to sizing

- **Parity replay**: backtests ran the live sizing, stops and kill switch (`BT:17-43`).
- **Monte Carlo.** 1,000 shuffles of the out-of-sample trades; report the 5th, 50th and 95th percentile of final equity, max drawdown, Sharpe and profit factor. "A strategy whose 5th-percentile equity remains above the guardian drawdown band is considered robust to sequence risk." SRC (`BT:141-152`). This was the only sizing-linked survival test.
- **PBO** (probability of backtest overfitting) by splitting history into 16 pieces: below 0.25 pass, above 0.50 do not promote. SRC (`BT:156-171`).
- **Kelly from paper.** No live Kelly without a paper record (`PRD` FR11). Paper windows: scalper 7 trading days, ORB 14, sniper 21, mean-reversion 14 (`PTDS:231-242`, suggestions only).
- **Re-promotion** after demotion: rolling tier T2 or better, 10 consecutive net-positive demo trades, operator approval. SRC (`PTDS:65-71`).
- **DPR rating** (0–100 from six weighted parts; T1 80–100, T2 50–79, T3 0–49) feeds the size multiplier and slot priority. SRC (`PRS:26-41`).
- **WF3 pool cleaning.** WF3 is the old workflow that decided keep, reduce weight, demote, retire or rehab, from circuit-breaker fire density, MAE/MFE drift (how far a trade went against or for the bot), DPR drawdown, and session and regime slices. "Reduce weight" is the only decay output that touches size. No formula, window or threshold was ever written. SUM (`R08` §2.1).

---

## 6. Trader's judgment (MINE, not sources)

### Strengths

- **Sound bones.** Half-Kelly as an upper bound, hard per-trade and per-day caps, sizing off current equity, a cost gate, and a separation between "what the edge says" and "what the account allows" (`R0:15`).
- **The one-shot stop.** It keeps loss data honest for the breaker.
- **Session-aware compounding** is a real lever when a bot genuinely has an edge in many windows a day. Trade count, not size, drives the growth.
- **House money and reverse house money** match desk practice: press when the day is paid for, cut size in a streak.

### Weaknesses

- **Most of the machinery did nothing.** Under the spec's caps, the nine multipliers, house money, premium boosts and drawdown pressure are almost always overridden by the 0.5% or 0.8% cap (§3). The "enhanced Kelly" was in effect fixed-fraction.
- **The spec and the code differed by about 4×.** The code dropped the per-trade cap (Gap 1). Any memory of "insane" growth needs to say which one it came from.
- **Ten percent a day at the small band is loose.** Two bad days take about 19% of the account. The Growth band was the loosest per day and the tightest per trade, so its risk sat in the number of trades.
- **Kelly inputs were fragile.** A paper sample of 7 to 14 days, initial R:R, and winners cut short by the asymmetric exits all push Kelly high. The cap hides this until the cap is raised.
- **Many key numbers were never set**: band thresholds, house-money threshold, breaker thresholds, family budget formula, how lots round. `G01` §8 lists 38 gaps.
- **Minimum-lot clamp.** `clamp(raw_lots, broker_min_lot, …)` raises a too-small position *up* to the minimum lot. On $300 that can mean 0.66% or more risk where 0.5% was intended. It is a silent oversize, not a block.
- **Leverage and margin are not in the sizing maths.** At 30:1, margin on three slots is a real limit on $300 (`G06` §2.3).

### Ruin odds: a rough illustration

MINE. Script: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\3843585b-786c-489b-aec5-b6c33ec14833\scratchpad\oldsim.py`. Assumptions: $300 start, 12 independent trades a day, 250 days, the old 10% daily stop, compounding off current equity, no fees, no lot rounding, no leverage limit. Toy numbers only, not a forecast.

| Edge per trade | Risk per trade | Median max drawdown | Chance of a 50% drawdown | 5th-percentile final |
|---|---|---|---|---|
| Thin (+0.21R: 55% wins, 1.2R) | 0.5% | 8% | 0% | ~$4k |
| Thin | 2% | 28% | ~0% | huge |
| Thin | 8% | 75% | 100% | huge, but only after a 75% hole |
| Near zero (+0.05R: 50% wins, 1.1R) | 0.5% | 16% | 0% | $384 |
| Near zero | 2% | 53% | 60% | $451 |
| Near zero | 8% | 98% | 100% | **$2 (ruined)** |

**Reading.** With a true edge and thousands of trades, every size compounds to absurd numbers. That explains why old runs looked like they "couldn't lose". The danger is the edge you think you have but don't. At 8% risk a near-zero edge is ruin. At 8% even a good edge sits through a 75% drawdown and hits the 10% day stop on about 110 days a year. An 8% unit needs either a proven large edge, very few trades, or a hard pot it is allowed to lose. That is the scenario maths for later.

---

## 7. Where summaries disagree with the folder

| Point | Summary says | Folder says | Verdict |
|---|---|---|---|
| House money trigger | `G09` A.9: "when the slot's session P&L is positive" | `R2:78`: "slot's cumulative **daily** P&L crosses a **threshold**"; `PROT:3135`: >0.5% per session, provisional. "Positive" is the GPT extract's wording (`qml-architecture-context-gpt-extract-delta.md:235`) | `G09` simplifies; the folder itself disagrees on daily vs session. |
| House money scope | `G01` and `G09`: slot-scoped | `R5:96` slot-scoped; `BS:107` D3 bot-scoped, resets on swap | `R19` §5 caught this; `G01` lists it only as a PRS/BRL conflict. |
| What house money does | All summaries: a booster | `qml-types-catalogue.md:3824`: "Reduced risk after profit milestones" | A contradiction inside the folder that no summary records. |
| Realised R:R for Kelly | `G01` §2: "proposed but deferred" (`R0:169`) | `BS:105` D1 and `PRD` FR11: Kelly from paper realised stats, decided | `R19` is right; `G01` is incomplete. |
| Slot count | `G09`, `G02`: fixed at 3 | `R4:24` fixed; operator: tied to current capital, "increasing" (`GPTR:19556`; `CFS:1317`) | The folder and operator memory differ; unresolved. |
| House money "inert" | `G06`: "Inert under the 0.5% cap" | Folder claims 1.5× is sized to the clamp (`R5:112`) | The arithmetic supports `G06`; the folder's rationale is wrong. |
| Old system was aggressive | `R19`, the risk-sizing pack: "aggressive radioactive sizing" | Written caps are conservative (0.5%/trade); aggression is only possible through compounding, many trades, 10%/day, and the Gap 1 bug | MINE: the "aggressive" label fits the code and the intent, not the written caps. |
| Old simulations | `G02` §2.1: none survive | None in `V`; `CFS:1323-1380` shows a Sep 2026 ChatGPT "legacy pilot" that it later judged not a faithful test (pool of 3, no bands, spot preset ate the account) | No faithful old-system simulation result exists anywhere I found. |

---

## 8. Values never given

Band thresholds; the house-money threshold (only a provisional 0.5%); session multipliers per window; the DPR minimum; physics, correlation and RVOL maths; the family budget; breaker thresholds; probation exit; lot rounding direction; whether open losses count; trade rates, win rates and R:R per family. The folder cannot supply them and the code is lost (`G01` §8).

**Not read:** the Gemini PDF in `07-Source-Material` (README only); `GPTR` beyond the cited passages.
