---
title: Earning a market's own version of a unit without luck, and noticing when that market changes
date: 2026-10-30
author: research agent 2 (poteto-mode, no sub-agents)
ticket: wayfinder/tickets/research-earning-a-specialist.md (drift ticket merged in)
status: research; options and evidence, not a design
---

# 24: Earning a market's own version, and noticing when the market changes

**Labels.** CHECKED = read at the cited place this session, or printed by a command I ran (named). INFERRED = my reasoning. Every number is a starting default, never a ruling (standing order 5). Sizing, stakes and budgets are out of scope (`RISK-SIZING-PACK.md`).

**Words.** The ticket file is named "earning a specialist". He asked "Specialist, what do you mean by a specialist? I don't know what you mean by that." (`T2`, 30 Oct 06:11, CHECKED). So this file says **a market's own version**: one unit runs one logic across many markets (its broad form), and a market's own version is the same unit with that market's own settings, or with logic changed or enhanced for that market. "System 1" and "System 2" were his explanation names, not QMX terms (same message, CHECKED). Research 43 already splits the market's own version into two halves: **a market's own settings** (same unit, new version) and **a market's own logic** (a new unit in the same family) (`R43:160-162`, CHECKED). Both halves are covered here.

**Keys.** `T1` = `operator/transcript-2026-10-20-to-28.md`; `T2` = `operator/transcript-2026-10-29-to-30.md`. `R05`, `R08` and so on = files in this folder. Question ids are rows in `funnel3/party-brainstorm/playing-field.md` (L ids) and `funnel3/cis/cis-questions.md` (Q ids), CHECKED by grep. The simulation is `sim24/sim.py` in my scratchpad (path in section 9), run with numpy 2.5.2.

---

## 0. What matters most (short)

1. **His Path A ruling already removes the worst luck, but not all of it.** A market's own version is earned from the record the broad unit built on that market, never from thin air (`STATE.md:120`, CHECKED). He is right that this answers "it has no history" (`T2`, 29 Oct 17:25: "you are assuming as if this system two variant came from thin air", CHECKED). Luck still enters at one point: **choosing which market gets its own version after reading the records**. In the simulation, the best of 20 markets with 100 trades each looks like +0.23R while its true edge is +0.06R (section 2.1, CHECKED by run). The record is real; the pick overstates it.
2. **The cure is cheap: evaluate every market, do not pick one.** Fix the rule before reading results ("every market that reaches the record threshold is evaluated"), count every evaluated market as a try, and judge each market's number after pulling it toward the unit's pooled number by how little data it has. In the simulation that pull removes the overstatement completely: the shrunk estimate of the best market equals its true edge on average (+0.062R vs +0.062R, section 2.1, CHECKED by run).
3. **The "270 to 550 trades" he did not trust has a plain source, and it is weaker than it sounds.** It is the count at which a real 0.1R edge first clears the usual 95% bar on average (R05 §2.4, CHECKED). At exactly 270 trades a real 0.1R edge passes only about half the time (simulated power 0.505, CHECKED by run). A count that catches a real 0.1R edge 4 times in 5 is about 620 trades (INFERRED from the same formula). So the number should not be a fixed count he types; it should be computed per unit from that unit's own spread of results, as his "the agents can help propose and figure it out" seed suggests (`T2`, 29 Oct 17:53, CHECKED).
4. **A sequential test can replace the fixed count, and it is safer, not faster.** A betting-score test (an e-process) may be checked after every trade without inflating false passes: with no edge it passed only 3.0% of runs within 3,000 trades (limit 5%, CHECKED by run). It stops early for big edges (median 266 trades at +0.15R) and needs about as many as a well-powered fixed count for 0.1R (median 604). Section 3.
5. **A week of QMX's own recorded data cannot judge an edge, but it can judge three other things.** 60 trades give a standard error of 0.13R, larger than a 0.1R edge (CHECKED by run). He is right for edge ("backtesting across a week makes no sense", `T2`, 29 Oct 17:25, CHECKED). A week is enough to check costs and fills against the market journal, to check that QMB replays the live trades the unit actually took (QuantConnect runs a backtest beside every live deployment for this, R08 §2.2, CHECKED there), and to check the market's readings still sit inside the range seen when the version was earned. Section 5.
6. **Drift is caught fastest on the inputs, not on the profit.** A drop from +0.1R to 0 takes about 240 trades for a profit-based alarm (R08 §2.2, CHECKED there). A change in the market's own readings (volatility, trend state, spread) shows within sessions. The options are in section 4; what happens after an alarm conflicts with standing order 7 if it changes live behaviour automatically, so it is flagged, not settled.
7. **Most of these questions cannot be measured today.** They need every trade stamped with its market readings and its result in R (R43 F1, F2; STATE "the lead call most questions wait on", CHECKED). Section 7 lists which can run now.

**For him, in four sentences.** A market gets its own version only from the unit's own trades on that market, as you ruled. The one trap left is looking at twenty markets and picking the best-looking one, because the best-looking one is partly lucky. The fix is to judge every market the same way, pull each market's result toward the unit's overall result when it has few trades, and count every market judged. A week of QMX's own data cannot prove an edge, but it can prove the costs are right, the backtester matches live, and the market still looks like it did when the version was earned.

---

## 1. Where the luck can enter, step by step

INFERRED from R16 §1.3-1.4, R15 and the playing field rows below. The steps follow his description: the broad unit trades many markets on paper or live; its record per market grows; a market's own version is made once the record shows it.

| Step | Where luck enters | Guard | Question rows |
| --- | --- | --- | --- |
| The broad unit's markets list is chosen | markets chosen because a backtest looked good on them | count every market tested at QMB's door (R43 F5) | L02-09 |
| The record per market grows | none: trades happen | the record must be stamped with readings and R (R43 F1) | L02-02 |
| Someone reads the records and picks markets | **picking the best-looking record** | evaluate all markets that reached the threshold; count each as a try; shrink | L02-03, Q64 |
| A market's own settings are fitted on that record | fitting settings to the same trades that chose the market | fit on the earlier part, check on the later part, or count each settings profile as a try | Q27, C11 |
| A market's own logic is written for it | free search over logic for one market | logic change is a new unit, counted in the family (R43 identity table) | L02-12 |
| Agents shortlist markets for him | the agent's shortlist is a fresh pick | an agent's proposal is a try at QMB's door like any run | L11-05 via L02-03 cross-map |
| He clicks it live | none | only he promotes (STATE ruling Q3, CHECKED) | |

**His challenge on "picking the luckiest".** He wrote that it is "kind of impossible" because the guards (spread quality, news, kill switch) stop a unit trading in bad conditions (`T2`, 29 Oct 17:53, CHECKED). Plain answer: the guards remove bad *conditions*; they do not remove luck in the *record*. A market can pass every guard and still have a record that looks better than its true edge because it was the top of a noisy list. Both are needed. INFERRED.

---

## 2. Earning without luck: the options

### 2.1 What the simulation shows about picking

Setup (`sim24/sim.py`, CHECKED by run): each market has a true edge drawn around +0.02R with a spread of 0.05R between markets; trades are +1R or -1R; each market has n trades. Pick the best market by its raw record. Compare what it looks like, what it truly is, and the shrunk estimate (each market's number pulled toward the average of all markets with weight n/(n+400)).

| Markets looked at | Trades per market | Best looks like | Best truly is | Shrunk estimate | Chance its true edge is above 0 |
| --- | --- | --- | --- | --- | --- |
| 5 | 100 | +0.148R | +0.047R | +0.045R | 0.84 |
| 20 | 30 | +0.371R | +0.045R | +0.045R | 0.82 |
| 20 | 100 | +0.228R | +0.062R | +0.062R | 0.90 |
| 20 | 300 | +0.163R | +0.081R | +0.081R | 0.98 |
| 100 | 100 | +0.297R | +0.075R | +0.075R | 0.95 |
| 100 | 1000 | +0.168R | +0.127R | +0.126R | 1.00 |

**Explaining the numbers** (per explain-the-number). The overstatement is the winner's curse: "The largest few ... are likely to substantially overestimate" their true values (Efron 2011, CHECKED). It shrinks as records grow, which is why his "no rush" helps. The shrunk estimate matches the truth here because the simulation used the true spread between markets (0.05R) to set the weight; in practice that spread is estimated from the unit's own markets (empirical Bayes, R05 §2.4, CHECKED there), so the match will be rougher. The chance-above-zero column depends on the assumed spread of true edges: if most markets truly have no edge, it falls. INFERRED.

**What it means.** Under Path A, the best market usually does have a real edge; the error is in *how big*. A market's own settings sized or judged on the raw record would be judged on numbers two to four times too good at 100 trades. INFERRED from the table.

### 2.2 Is the market chosen before or after its trail is read? (L02-03)

| Option | Guard against luck | Hard cases | Maintain | Explain |
| --- | --- | --- | --- | --- |
| A. Choose before: he or a rule names the markets that may earn their own version before records exist | strongest; the Stats "chosen before results are seen" rule (R16 §1.3 citing `10:182`, CHECKED there) | weak: Path A says the record comes first, so naming markets in advance throws away the breadth he wants | simple | "decide where you will look before you look" |
| **B. Evaluate all: a fixed rule says every market reaching the record threshold is evaluated; all count as tries; each is shrunk** | strong: no pick, so no winner's curse in the decision; shrinkage fixes the size | handles 100 markets; low-trade markets stay "too thin to judge" (R05 §7.3, CHECKED there) | one rule, one formula | "every market gets judged the same way when it has enough trades" |
| C. Choose after, correct after: pick the best, then raise the bar for the number looked at (deflated Sharpe) | moderate: corrects the pass mark, not the size | breaks when markets move together (effective count unknown) | needs the effective-count method (R05 §6.1, CHECKED there) | "the more you look, the higher the bar" |
| D. Choose after, confirm on fresh trades: pick, then require new trades after the pick before his click | strong; the pick's luck does not carry into fresh data | slow for low-frequency units | simple | "it must keep winning after we noticed it" |

INFERRED: B and D combine cheaply. B decides which markets are candidates without picking; D asks each candidate for some trades after it became a candidate. Starting default for D: the later of 30 fresh trades or 2 weeks (placeholder; R43's paper default is "30 trades or 4 weeks", `R43:426`, CHECKED).

### 2.3 Is a "wins broadly" test still needed? (L02-09)

His Path A means a market's own version comes from its own record, so the version does not need the broad test to be earned. The broad test still has two jobs. INFERRED:
- **It is the prior.** The shrinkage in 2.2 B pulls each market toward the unit's pooled result. If the unit has no broad edge, the pull is toward zero, which is the honest prior.
- **It answers "is the logic real at all".** Research 15's "context lift" form (the unit wins when its context is present and not when it is absent, on most independent markets) tests the unit's claim, not a list of markets (`R15:21, 82`, CHECKED).

Options: (a) keep the broad test as a gate before any market's own version; (b) keep it only as the prior, no gate; (c) drop it. (b) fits Path A and his "no rush" without adding a step. Settings for context lift as R15 gives them: in-context minus out-of-context edge at least +0.05R, positive on at least 60% of independent markets (`R15:82`, CHECKED; both placeholders).

### 2.4 Pooled read or per-market read, and the cost in tries (Q64)

| Read | Tries | What it can say |
| --- | --- | --- |
| Pooled: all markets' trades judged as one record | 1 per unit version | "the logic works on this list"; nothing per market |
| Per market, picking the best | N markets looked at (fewer if they move together) | per-market claims, with the winner's curse |
| Per market, evaluate all with shrinkage (2.2 B) | N, but no pick, so the correction is in the estimate, not the bar | per-market numbers that are honest about size |

Research 16 already says a pooled read "is one test" and reading and picking 100 cells "is 100 tries (fewer after correlation)" (`R16 §1.3`, CHECKED). The effective count for markets that move together is not settled; options are the ONC clustering method (R05 §6.1, CHECKED there) or counting each same-idea group as one (his 30 Oct ruling on 1m and 5m, STATE, CHECKED). INFERRED: start with same-idea groups, add clustering when the tries ledger exists.

### 2.5 Two markets' own versions from what is really one trail (L02-16)

EURUSD and GBPUSD trades taken at the same minutes on the same dollar move are close to one record. Two versions earned from them are one piece of evidence counted twice. Options (INFERRED):
- (a) group markets whose trade results correlate above a set level (starting default 0.6, placeholder) and count the group as one try and one record;
- (b) require each market's record to hold after removing trades that overlap in time with the other market's;
- (c) leave it to the risk session's correlation control (that session owns correlation between live units, `RISK-SIZING-PACK.md` §6).
(a) is the only one that also fixes the try count. It needs the trade stamps (section 7).

### 2.6 Markets' own versions from different parents combined into a new unit (L02-12)

The Stats lineage already has `composite` packages pointing at parent ids and relationship types `variant_of`, `derived_from`, `supersedes` (`C:/Users/Mubarak/Desktop/Stats/lineage/composites/README.md`, `relationships/README.md`, CHECKED). R43's identity table makes a transplant across families "a new unit ... Yes (both families for a transplant)" in the tries column (`R43:154`, CHECKED). INFERRED: combining is allowed; the new unit starts with no record of its own as a combination (its parents' records are of different logic), so it is earned like any new unit, and the try is charged to both parent families. The parents' records can serve as its prior only on the markets where both parents traded.

### 2.7 Retired children's trades in the parent's record (Q73)

Yes, they stay. Dropping a dead market's trades from the pooled record is survivorship bias: "funds that disappear tend to do so due to poor performance" (Elton, Gruber and Blake 1996, CHECKED). A pooled record without its failures overstates the logic. INFERRED: the trades stay, tagged with the retired market's state; the pooled read always includes them.

### 2.8 Paper runs on markets he has not admitted (Q76)

They are evidence **and** tries, and the two do not conflict. INFERRED:
- As evidence: paper trades are real-time, after-cost (if the market journal supplies costs), and unseen by any search. They are the best out-of-sample data QMX has.
- As tries: if the paper markets were chosen by reading backtests, the choice is a pick (2.2), so the markets paper-traded count at QMB's door.
- The guard: the paper markets list is set by a rule before results, as in 2.2 B, or every paper market counts as a try.

### 2.9 The fail branch counts every context it tries (L10-06)

His seed: "Most strategies can work ... If they fail, we need to be able to know why" (`T1`, 20 Oct 12:59, CHECKED). Research 16 says the context search "finds contexts by luck" unless every context tried is a try and proof comes from data the search never saw (`R16 §1.4`, CHECKED). Research 05 calls the fail branch "the strictest" (`R05 §7.3`, CHECKED). Options (INFERRED):
- (a) count every context tried; judge only on trades after the search;
- (b) limit the context search to the dictionary's context words (no invented contexts), so the count is finite and known;
- (c) an alpha-spending budget per family: each search spends from it, discoveries earn some back (R05 §7.2, CHECKED there).
(a) plus (b) is simple and explains in one sentence: "the fail branch may try any context from the dictionary, every try is counted, and a found context must win again on new trades".

### 2.10 Do more research variants still help once breadth comes from placement? (Q16)

Two kinds of breadth. INFERRED:
- **Breadth of markets** (placement): one logic on many markets. More trades for one hypothesis, one try.
- **Breadth of logic** (variants): new rules. Each is a try, and the research papers show gains stop: refinement "gains stop and decay after about 15 rounds" and the in-sample gap widens with depth (`R11:24, 151`, CHECKED).
So variants still help when they are different ideas (low correlation with existing units), and stop helping when they are near-copies. Starting default: a family stops spawning variants after 15 refinement rounds without a validated gain (from R11; R43 already uses "30 trials without a better validated score" for its overnight loop, `R43:444`, CHECKED). Both placeholders.

---

## 3. How many trades: fixed count or sequential test (C11, Q27)

### 3.1 Where the fixed count comes from, in plain words

Research 05 used the minimum track record length: how many trades before the average result is far enough from zero to trust at 95% (`R05:127-134`, CHECKED). For a unit winning 55% at 1:1 that is about 270 trades; for a 70%-win unit with bigger losses about 550; for a thin 0.05R edge about 1,090 (same lines, CHECKED). In the coin words the lead already gave him: telling a 55% coin from a fair one needs about 270 flips (`T2:236`, CHECKED).

**What that number hides** (per explain-the-number). At the minimum length, a real edge passes only about half the time. The simulation, 20,000 runs (CHECKED by run):

| True edge | Trades | Share that pass the 95% bar |
| --- | --- | --- |
| 0 (no edge) | 270 | 4.7% (false passes, as designed) |
| +0.05R | 270 | 20.6% |
| +0.10R | 270 | 50.5% |

INFERRED from the same formula: for a real 0.1R edge to pass 4 times in 5, about (1.645 + 0.84)² ÷ 0.1² ≈ 620 trades are needed.

### 3.2 Options for where the count comes from (C11)

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| A. One fixed default for all units (R43's placeholder: 100 trades on that market, `R43:427`, CHECKED) | fails skewed scalpers and thin edges; 100 trades passes a real 0.1R edge about 1 time in 4 (INFERRED) | trivial | "100 trades" |
| **B. Computed per unit from its own results** (its win rate, payoff shape and spread give its own minimum length) | handles skew and thin edges; a lumpy unit is asked for more | one formula already in R05 | "a steady unit needs fewer trades, a lumpy one needs more" |
| C. Proposed by an agent workflow from performance, his seed | adapts to evidence, but an agent picking its own bar is the agent grading itself | needs a check that cannot be argued with | "agents suggest the bar, a script checks it" |
| **D. A sequential test, no count at all** | handles every case; checks after every trade | one score per market | "every trade adds to or takes from its score; when the score passes 20 it has earned it" |

His seed C fits best as "agents explain and propose, the script decides": the agent writes the card with the reason; the number comes from B or D. That is his own rule that agents "should judge best of results from performance" and not by eye (2026-10-27 dictation, `T1`, 27 Oct 03:03, CHECKED).

### 3.3 The sequential test, measured

A betting score (an e-process) multiplies by (1 + λ × trade R) after every trade; with no edge its average never grows, so it can be checked at any time (R05 §7.2 citing Ramdas et al., CHECKED there; always-valid inference "lets users try to take advantage of data as fast as it becomes available" (Johari et al., Operations Research 2021, CHECKED)). The simulation mixes four bet sizes (λ = 0.025, 0.05, 0.1, 0.2) and passes at a score of 20 (5% error), 4,000 runs of 3,000 trades (CHECKED by run):

| True edge | Passed within 3,000 trades | Median trades to pass | 90% passed by |
| --- | --- | --- | --- |
| 0 | 3.0% (error held below 5%) | 357 (among false passes) | 1,917 |
| +0.05R | 62% | 1,337 | 2,651 |
| +0.10R | 99.8% | 604 | 1,421 |
| +0.15R | 100% | 266 | 632 |

**Reading.** The sequential test is not a shortcut. For 0.1R it needs about what a well-powered fixed count needs (604 vs about 620). Its gains: it never needs a count typed in; it stops early for big edges; it can be watched daily without the peeking error a fixed count has; and the same score, run on trades after an alarm, is the "loosen only on new evidence" rule research 08 already proposes (`R08 §2.3`, CHECKED). INFERRED.

**Starting defaults.** Pass score 20 (5% error); bet mix as above; trades in R after costs; one score per market's own version, started at the moment the market became a candidate (so luck before the pick does not count). All placeholders.

### 3.4 How long is "no rush"? (L15-05)

He said a market's own version comes "over a given period of time ... a couple of weeks or days" and "There is no rush to trade" (`T2`, 29 Oct 17:25, CHECKED). INFERRED options:
- **Trades only** (B or D above): fast units earn in weeks, slow units in months or never.
- **Trades and calendar**: also require the record to span a minimum time, so one quiet fortnight cannot earn a version. Starting default 4 weeks, matching R43's paper default (`R43:426`, CHECKED).
- **Trades, calendar and conditions**: also require the record to include each of the context states the version claims to handle (for example, both volatility states). Most honest; needs the trade stamps.
A market that cannot reach the bar within a set time (starting default 6 months, placeholder) is labelled "too thin to judge", not failed (R05 §7.3, CHECKED there).

---

## 4. Noticing that the market changed (L02-04, Q24)

His case: a version is made on a market the unit rarely traded, then "markets change. The price action, the market structure changes" (`T2`, 29 Oct 17:25, CHECKED).

### 4.1 Detectors and their lag

| Detector | Watches | Lag | Source |
| --- | --- | --- | --- |
| CUSUM on trade R against the version's frozen baseline | profit | about 240 trades for +0.1R falling to 0, at about 1 false alarm per 1,000 healthy trades | `R08 §2.2` (CHECKED there) |
| Rolling window t-test (last 50 vs prior 200) | profit | about 25% slower than CUSUM | `R08 §2.2` (CHECKED there) |
| Adaptive window (ADWIN) on trade R | profit | no fixed lag; bounded false and missed alarms | Bifet and Gavaldà 2007: guarantees "as bounds on the rates of false positives and false negatives" (CHECKED) |
| Sequential score turned around (betting against the edge) | profit | similar to CUSUM; anytime-valid | `R05 §7.2` (CHECKED there) |
| Monte Carlo cone | profit path | at the 5th percentile, slow | `R08 §2.3` D2 (CHECKED there) |
| Behaviour drift: trade rate, hold time, replay match | inputs | days to two weeks | `R08 §2.3` D4: trade rate outside 0.5× to 2×; replay match below 80% (CHECKED there) |
| Cost and fill drift | inputs | about 50 trades | `R08 §2.3` D3: 1.5× card cost (CHECKED there) |
| **Market readings drift**: the market's own readings (volatility, trend state, efficiency ratio, spread) leave the range seen while the version was earned | the market itself | sessions, not trades | INFERRED; needs readings stored with their time (R43 F2) |

INFERRED: the last row is the new one. It catches "the market changed" before the profit shows it, and it does not depend on the unit trading at all, so it works for a version the unit trades rarely, which is exactly his case.

### 4.2 What happens after an alarm: options

| Option | Fits standing order 7? | Hard cases | Explain |
| --- | --- | --- | --- |
| A. Inform only: a card to him; nothing changes until he clicks (R08's design: "The check informs", `R08 §2.3`, CHECKED) | yes | slow if he is away | "QMX tells you; you decide" |
| B. The market falls back to the unit's pooled settings automatically | **no as written**: it changes live behaviour without his click and is not a risk rule stopping a unit | handles away-time | "it goes back to the general settings" |
| C. The market's own version stops new entries on that market, logged; open trades kept | yes, if the risk session counts it as a risk rule | handles away-time | "it stops trading that market until you look" |
| D. Size down on Watch, stop on Alarm (practitioner stacked levels, `R08 §2.2`, CHECKED there) | sizing is the risk session's | | |

**Conflict to watch.** B is the most natural trader answer and breaks standing order 7. C keeps the rule if the risk session accepts "a market's version expired" as one of its stop rules. That is the risk session's call, so this file names it and stops. INFERRED.

### 4.3 Earning and expiring share one clock

The same score that earned the version (3.3) can be run backwards after earning: the version keeps its status while the score on recent trades stays above a floor. Research 08's loosening rule is the same mechanism in the other direction (`R08 §2.3`, CHECKED). INFERRED: one score per market's version, one clock, two thresholds (earn at 20, flag on the opposite score at 20). Placeholders.

**Old results after a change.** "Stale, not false; re-run" is the Stats rule for cost-model changes (R16 §1.4 citing `10:177`, CHECKED there). INFERRED: the same applies to a market change: old trades stay, marked as from the earlier state; the version is re-judged on trades after the change.

---

## 5. QMX's own recorded data: is a week enough? (Q25, L08-08)

**Edge: no.** Standard error of the mean R by trade count (CHECKED by run): 20 trades 0.22R; 60 trades 0.13R; 150 trades 0.08R; 400 trades 0.05R. A week of a scalper (say 60 trades) cannot separate +0.1R from 0. Trades inside one week also share one set of conditions, so they count for less than independent trades (INFERRED). He is right.

**Three things a week can do** (INFERRED unless cited):

| Job | Shortest useful window | Why |
| --- | --- | --- |
| Check costs: spread, fees, slippage by hour against the market journal | one day per session type | the market journal measures his broker's real costs (`R12:26, 225`, CHECKED) |
| Check that QMB replays what the unit actually did live | one week | QuantConnect runs an out-of-sample backtest beside every live deployment to explain gaps (`R08 §2.2`, CHECKED there); SQ's rule of thumb is about 80% of trades matching (same, CHECKED there) |
| Check the market still looks the same (readings drift, 4.1) | one week of sessions | readings, not trades |

**Shortest window for edge (L08-08)**: a trade count, not a time. Starting default: whatever 3.2 B or 3.3 gives for that unit. A window is "worth testing" when its expected trade count reaches the unit's own minimum (R05 §7.3 item 2, CHECKED there).

**A second reason to record.** The recorded data is the only data after any model's training date and after the unit was written, so it is the cleanest out-of-sample data QMX will have (`R11` LLM-memory test via STATE, CHECKED). His objection that agents use live data, not memory, stands for analysis (`T2`, 30 Oct 04:38, CHECKED); for judging a backtest, recorded data removes the question entirely. INFERRED.

---

## 6. Agents in the loop (his 29 Oct seed)

He proposed workflows where agents read the day's chart, the indicators, the market readings and the unit's trades, find "the pattern of why did this ... unit trade this", so that by the time a market's own version is proposed "the agents would have already seen this also" (`T2`, 29 Oct 17:53, CHECKED). Options for where that fits without bringing luck back (INFERRED):
- **Agents explain, scripts decide.** The agent's card says why a market might deserve its own version; the score in 3.3 decides whether it has earned it.
- **Agent shortlists are tries.** A shortlist is a pick (section 1), so each market an agent proposes is counted at QMB's door like any run (R43 F5).
- **Agents' calls are scored later.** A dated agent call ("this market will stay mean-reverting this week") is scored by the market afterwards, which research 29 and the funnel3 CIS run name as uncheatable proof (STATE funnel3 CIS row, CHECKED). Over time this gives each agent workflow a record, like a unit.

---

## 7. What can be measured today, and what waits for stamped trades

Today means with shipped code (R18, R42 via STATE, CHECKED) plus a script over existing data.

| Question | Today? | Needs |
| --- | --- | --- |
| Winner's curse size for a given unit (2.1) | yes, by simulation from its backtest's per-market results | per-market results, which QMB gives per run |
| Per-unit trade count (3.2 B) | yes, from any backtest's trade list | trades in R; QMB gives money only today (R43 F1, CHECKED) |
| Sequential score (3.3) | yes on backtest or paper trades as a script | trades in R |
| CUSUM decay (4.1) | yes as a script on a trade list | a frozen baseline per version (R08 §2.3) |
| Context lift (2.3) | **no** | market readings stamped on every trade (R43 F1, F2) |
| Readings drift (4.1) | **no** | readings stored with their time (R43 F2) |
| One-trail check for correlated markets (2.5) | partly: correlation of per-market daily results | trade times per market |
| Costs check with a week of recorded data (5) | **no** | the feed recorder and market journal (planned, not built: `T2:243`, CHECKED) |
| QMB replay of live trades (5) | **no** | live trades and recorded quotes |
| Retired trades kept in the pooled record (2.7) | yes, by rule | the journal keeps them |

---

## 8. Numbers named here (all starting defaults)

| Number | Default | Why |
| --- | --- | --- |
| Shrinkage weight | n ÷ (n + k), k estimated from the spread between the unit's markets; if unknown, half weight at 100 trades as in R43 (`R43:428`) | empirical Bayes (R05 §2.4); the simulation used k = 400 for a 0.05R spread |
| Fresh trades after becoming a candidate | the later of 30 trades or 2 weeks | 2.2 D; placeholder |
| Pass score for a sequential test | 20 (5% error) | R05 §7.2, R08 §2.3 |
| Bet sizes in the score | 0.025, 0.05, 0.1, 0.2 | simulation; placeholder |
| Minimum calendar span to earn | 4 weeks | R43 paper default |
| "Too thin to judge" after | 6 months | placeholder |
| Context lift | +0.05R gap, positive on 60% of independent markets | R15:82 |
| Correlated-trail grouping | trade-result correlation above 0.6 | placeholder |
| Variant stop | 15 rounds without a validated gain | R11 |
| CUSUM | allowance half the drop of interest; limit for 1 false alarm per 1,000 trades | R08 |

---

## 9. Sources

Papers and primary pages read this session:
- Efron 2011, Tweedie's formula and selection bias: https://doi.org/10.1198/jasa.2011.tm11181 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC3325056/
- Johari, Koomen, Pekelis, Walsh, always valid inference: https://pubsonline.informs.org/doi/10.1287/opre.2021.2135 ; https://arxiv.org/abs/1512.04922
- Bifet and Gavaldà 2007, ADWIN: https://epubs.siam.org/doi/10.1137/1.9781611972771.42 ; https://www.cs.upc.edu/~gavalda/papers/ds06.pdf
- Elton, Gruber, Blake 1996, survivor bias: https://doi.org/10.1093/rfs/9.4.1097
- Bailey, Borwein, López de Prado, Zhu 2014, minimum backtest length: https://www.davidhbailey.com/dhbpapers/backtest-pseudo.pdf (used in research 26)

Through earlier research files (cited there, CHECKED there, not re-fetched): Bailey and López de Prado minimum track record length; Efron and Morris; deflated Sharpe; PBO; alpha-investing and LORD; e-processes (R05); CUSUM, QuantConnect reconciliation, SQ compare (R08); the refinement-depth papers (R11).

Local: `STATE.md`, `operator/transcript-*.md`, `research/05`, `08`, `11`, `12`, `15`, `16`, `17` (C10, C11), `43`, `funnel3/party-brainstorm/playing-field.md`, `funnel3/cis/cis-questions.md`, `C:/Users/Mubarak/Desktop/Stats/lineage/*/README.md`.

Simulation: `C:/Users/Mubarak/AppData/Local/Temp/claude/C--Users-Mubarak-Desktop-QMX/ed09cf0c-69f1-44ab-8c6b-76992918774a/scratchpad/sim24/sim.py`, run with `C:/Users/Mubarak/Desktop/QMX/.venv/Scripts/python.exe -I sim.py` (seed 7). Its trade model (+1R or -1R) is the simplest one; skewed scalpers need more trades than shown (R05 §2.4).
