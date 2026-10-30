---
title: How quant desks judge and iterate without overfitting, and which habits fit agents
date: 2026-10-30
author: research agent 2 (poteto-mode, no sub-agents)
ticket: wayfinder/tickets/research-quant-judging.md
status: research; options and evidence, not a design
---

# 26: Judging and iterating without overfitting

**Labels.** CHECKED = read at the cited place this session, or printed by a command I ran (named). INFERRED = my reasoning. Every threshold is a starting default, never a ruling (standing order 5). Replaying the old sizing is the risk session's; this file only lists what QMB must record so that replay is possible (section 6). Sizing maths and exit maths are out of scope.

**Keys.** `T1`, `T2` = the two verbatim transcripts in `operator/`. `R03`, `R05` and so on = files in this folder. Simulations live in my scratchpad's `sim24/` folder (section 9). Research 24 (earning a market's own version) and 45 (vocabulary) are cross-referenced, not repeated.

**What is already settled and not redone here.** QMB's parts and what is kept or rebuilt (`R43` §3.4, CHECKED); the borrow list from LEAN and Jesse (`R14` §9.3, CHECKED); the old QMX pass numbers and the decay check (`R08`, CHECKED); holdouts are his choice per study, off by default (rulings 136-137, `R43` §3.4, CHECKED); the judge shows each result with the unit's own sizer and with a fixed-size baseline (`R43` §3.4, CHECKED).

---

## 0. What matters most (short)

1. **Desks agree on one habit above all: never research by backtesting.** López de Prado: "feature importance is a research tool, and backtesting is not", and repeating a test on the same data "will likely lead to a false discovery" (GARP whitepaper of "The 10 Reasons Most Machine Learning Funds Fail", CHECKED). For agents this means the builder writes the unit and its claim before it sees any result, and a backtest report is never the input to the next edit without that edit being counted. Section 1.
2. **His "historical and paper both" is the professional answer, and it solves the holdout question too.** With holdouts off by default (his ruling), the data nobody could have fitted is the data that did not exist when the unit was frozen: paper trades and QMX's own recorded data. So paper is the out-of-sample test, not a formality after it. Section 2.
3. **The sequence is short and cheap first.** Seven steps, from a written claim (minutes) to paper (weeks); each catches a different failure; most units should die in the first three, which cost seconds. Section 2.1.
4. **An exit change or a block change can be counted as a try the same way as a number change: by its result stream, not by its edit type.** Every run lands a trade stream; variants whose streams move together are one effective try, different ones count separately. In a simulated family of 51 variants (40 exit tweaks of one base and 10 different blocks), a correlation-cluster count gave 11 effective tries, the honest answer; the common shortcut formula gave 1.9, an undercount (CHECKED by run). López de Prado and Lewis built their clustering method (ONC) for exactly this (Quantitative Finance 2019, CHECKED). This closes research 43's open weak point without classifying edits. Section 3.
5. **When the unit owns its exits, judge the whole unit as one stream; inspect entry and exit separately only as diagnostics.** The edge ratio (average favourable move over average adverse move after entry, in ATR units) tests the entry without the exit (StrategyQuant on Curtis Faith's measure, CHECKED); the share of the favourable move an exit keeps tests the exit. Neither is a pass mark. Section 4.
6. **QMB's What-If needs to be split in two.** StrategyQuant uses What-If for two opposite jobs: a robustness check ("what if we'll ommit 5% of the most profitable trades?") and an improvement tool ("pick days or hours that are not profitable"), and warns the second "might be just pure luck" (SQ docs and blog, CHECKED). QMB's six filters are all of the second kind (`R18` §2, CHECKED). Section 5 lists the gaps.
7. **To replay the old sizing later, QMB must record the trade sequence in R with the equity and session state before each trade, and keep would-have-done rows when a unit is stopped.** Without the second, any sizing rule that halts trading cannot be replayed. Section 6.

**For him, in four sentences.** Professional desks write down the idea before they test it, test it as few times as they can, and count every test. QMX can do the same: the builder agent writes the unit blind, every test is counted at QMB's door, and changes that barely change the trades count as almost nothing while real changes count fully. Your idea of judging on history and on paper is how desks work, and paper is the honest test because the unit could not have been fitted to trades that had not happened yet. Exits are judged with the whole unit, with two simple side measures that show whether the entry or the exit is doing the work.

---

## 1. How desks iterate without fooling themselves

| Habit | What it guards against | Source | Fits agents? |
| --- | --- | --- | --- |
| State the economic reason before testing | ideas with no reason that work by luck (the ticker-letter strategy that "validated" over 1989-2015) | Arnott, Harvey and Markowitz 2019, "A Backtesting Protocol in the Era of Machine Learning" (CHECKED); "finance theory can help us filter out ideas that lack an ex ante economic basis" | yes: the builder writes the claim card first (funnel4 `qml-field.md` B069 "blind building", CHECKED there) |
| Do not research by backtesting; do not use a backtest report to change the strategy | the loop of test, tweak, retest | López de Prado, 10 Reasons, pitfall 2 (CHECKED); "about 20 such iterations" reach a false 5% discovery (same) | yes, if every edit after a result is counted (section 3) |
| Record every backtest and deflate | selection among many runs | López de Prado via the deflated Sharpe (R05 §6.1, CHECKED there); QuantConnect: performance "should be scaled down" with each backtest (QuantConnect blog 2019, CHECKED) | yes: the try ledger at QMB's door (R43 F5) |
| Keep few free numbers | fitting noise | QuantConnect Research Guide: 0-10 parameters "Likely Not Overfit", 20+ "Probably" (CHECKED); "more than 3-4 parameters for a relatively simple algorithm" is risky (QuantConnect blog, CHECKED) | yes, as a gauge on the judge card |
| Count backtests per idea | the same, by count | QuantConnect Research Guide: 0-30 backtests "Likely Not Overfit", 70+ "Probably" (CHECKED) | yes, as a gauge |
| Limit research time per idea | attachment to one idea | QuantConnect: "no more than 16 hours of work per experiment" (CHECKED) | as a round limit for agents: refinement gains stop after about 15 rounds (R11 via STATE, CHECKED) |
| Optimise on older data, test on newer; or walk forward | look-ahead from the optimiser | QuantConnect Parameters page (CHECKED); Jesse's `optimize()` keeps a testing period "completely held out and is never seen during the parameter search" (Jesse docs, CHECKED) | yes |
| Prefer combinatorial cross-validation to a single walk-forward | walk-forward's high variance | López de Prado, pitfall 9 (CHECKED); R05 §6.1 (CPCV lower PBO, CHECKED there) | yes; QMB has walk-forward and carve-out built, PBO and CSCV designed only (`R18` §2, CHECKED) |
| Test the rule against random entries first | entries with no edge | Jesse MCP: "runs the rule against thousands of random-entry simulations" (CHECKED) | yes; QMB ships rule significance as a library function (`R14` §9.3, CHECKED) |
| Methods should apply to whole asset classes | per-market selection bias | López de Prado's backtesting notes, as summarised (reasonabledeviations notes on AFML ch. 11, secondary, CHECKED) | yes; research 24 §2.2 B |
| Incubate on live data before capital; compare live with the backtest | everything the backtest could not see | QuantConnect reconciliation; SQ Compare Results (R08 §2.2, CHECKED there) | yes: paper on the demo account |
| Keep the protocol's aim two-sided: few false strategies, few missed good ones | over-strict judging | Arnott, Harvey, Markowitz: rejecting every strategy is "easy" and not the goal (CHECKED) | yes: his "don't be too strict" (STATE "Judging", CHECKED) |

INFERRED: two habits from human desks do not transfer as they stand. "Limit research hours" means little for an agent that runs a thousand variants in an hour; the agent form is a limit on counted tries and refinement rounds. "A senior reviews the research" becomes a deterministic judge step the agent cannot skip, which his "make judging a skill (hooks plus deterministic scripts that call QMB)" already asks for (STATE "Judging", CHECKED).

---

## 2. The sequence of judging steps

### 2.1 Steps, what each catches, what each costs

| # | Step | Catches | Cost | Counted as a try? | Default pass mark (starting default) |
| --- | --- | --- | --- | --- | --- |
| 0 | **Claim card**: the idea, the context it claims, the source, written before any run | stories told after the result | minutes, one agent call | no | must exist; unit cannot run without it |
| 1 | **Signal check**: entry vs random entries; entry edge ratio at fixed horizons | entries with no edge, before exits hide it | seconds | yes | rule significance p below 0.05; edge ratio above 1.0 at the claimed horizon |
| 2 | **Cost check**: full backtest at 1x and stressed costs | edges that costs eat, the scalper's main killer | seconds to minutes | same try as step 3 (one run) | positive after 1.5x costs (shipped judge, `R43` §5 judge preset, CHECKED); old QMX used 2x |
| 3 | **Out-of-sample check**: walk-forward or combinatorial splits over all history | parameters fitted to one period | minutes | yes, one per configuration | walk-forward efficiency 0.5 (shipped judge, CHECKED in R43 §5) |
| 4 | **Try-corrected verdict**: deflated Sharpe with the family's effective try count (section 3) | the best of many runs being lucky | seconds once the ledger exists | no (reads the ledger) | deflated Sharpe confidence 0.95 (shipped judge, CHECKED in R43 §5) |
| 5 | **Robustness, opt-in**: parameter neighbourhood, remove-top-trades What-If, latency and fill shocks, Monte Carlo for the sizing path only | one sharp peak; a few lucky trades; fill fragility | minutes | the neighbourhood runs count | neighbourhood median above 0 after costs (R05 §7.3, CHECKED there); top 5% removed keeps 80% of profit (SQ default, CHECKED) |
| 6 | **Context check, when stamps exist**: context lift; shuffled readings | a unit whose claimed context does nothing | minutes | yes | context lift as in research 24 §2.3 |
| 7 | **Paper on the demo account**: forward trades on frozen code; live-vs-backtest overlay; sequential score | real fills, latency, regime change, and any memory a model had of past markets | weeks | no new try unless the unit is edited | sequential score as in research 24 §3.3; replay match about 80% (R08 §2.2 SQ rule, CHECKED there) |
| 8 | Live at his click | n/a | n/a | n/a | only he promotes (STATE ruling, CHECKED) |

**Why this order.** Cheapest and most-killing first: StrategyQuant users found only "the parameter-neighbourhood test and the walk-forward grid caught a planted overfit" while 70,000 Monte Carlo runs passed it (`R03:18`, a practitioner demo; CHECKED there), so Monte Carlo is not an edge test and sits in step 5 for sizing paths only. INFERRED.

**What it cost to skip a step** (explain-the-number). The shipped "100 trades" minimum in the judge preset (`R43` §5, CHECKED) passes a real 0.1R edge about one time in four at the 95% bar (research 24 §3.2, INFERRED from the run there). So steps 1-4 on a short backtest reject many good units; paper (step 7) is where a thin real edge gets the trades it needs. This is the practical meaning of "don't be too strict" (STATE "Judging", CHECKED). INFERRED.

### 2.2 When paper starts (L08-05): options

| Option | For | Against | Explain to him |
| --- | --- | --- | --- |
| A. Strict: paper only after steps 0-4 pass | fewest paper units to watch | weeks lost per unit; a thin edge that fails step 4 on short history never gets its trades | "paper only after the backtest passes" |
| **B. Early paper: paper starts after steps 0-2 pass, in parallel with 3-6** | time is the scarce resource; paper costs nothing but a slot; paper trades are the cleanest evidence | more units on the demo; needs the rule below | "if it survives costs, it starts paper while the rest of the tests run" |
| C. Everything on paper at once | maximum evidence | the demo account and feed fill with junk; costs and the trading node's load (research 31's question) | "everything goes on paper" |

**The rule that keeps paper honest under any option.** Paper trades count as out-of-sample only for the frozen version that took them. If a paper result leads to an edit, the edit is a counted try and the new version's paper record starts again. INFERRED; this is López de Prado's "never use a backtest report to modify your strategy" applied to paper reports.

**Starting default** for "paper before his card": 30 trades or 4 weeks, whichever is later (`R43` §5, CHECKED; placeholder until this file). This file adds: and the sequential score of research 24 §3.3 has not fallen below its start. INFERRED.

### 2.3 Why paper also answers "models remember past markets"

He objected that agents will use live data, not memory (`T2`, 30 Oct 04:38, CHECKED). For analysis he is right. For judging a backtest built by a model, the clean answer is the same as above: trades after the unit was frozen cannot be remembered by any model. Paper and recorded data make the question moot without a special test. INFERRED.

---

## 3. Counting an exit change or a block change as a try (L08-06, R43's open weak point)

The problem: the try ledger counts runs, but "change the exit family" or "add a filter block" is a different kind of edit from "move a number", and the literature has "no settled way to count a change of exit family or filter as a fraction of a try" (`R35` §7 item 9, CHECKED).

### 3.1 Options

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| A. Every structural edit = one full try; numbers inside a declared range = calibration, not a try | over-counts near-identical exit tweaks; under-counts a block swap that changes every trade | simple table (R43 identity table) | "a structure change is one test" |
| B. Weight by edit type (a block swap = k tries, an exit tweak = 1) | k is invented | a table of weights to argue about | "big changes cost more" |
| **C. Count by result stream: every run lands its trade stream; the family's effective try count is the number of clusters of streams that move together** | handles every edit the same, including ones nobody classified; numbers, exits, blocks, markets and Python units all fall out of one rule | one clustering step over the ledger | "if a change hardly changes the trades, it hardly counts; if it changes them a lot, it counts fully" |
| D. Pre-registered changes are cheap, post-hoc changes are dear: an edit proposed with a reason before seeing the result counts once; an edit made after reading a result counts double | rewards the claim card habit | needs the card time-stamped before the run | "guesses written first are cheaper" |

**Evidence for C.** The deflated Sharpe needs two "meta-research variables": the number of effectively uncorrelated trials and the spread of Sharpe across them, and López de Prado and Lewis's ONC algorithm "determines the number of effectively uncorrelated trials" by clustering trial returns (Quantitative Finance 2019, CHECKED). Their distance is built from the correlation of the trials' returns (same paper, CHECKED).

**What the simulation shows** (`sim24/tries.py`, CHECKED by run). Families of trade streams on a shared clock of 500 periods:

| Family | Raw runs | Shortcut formula (eigenvalue participation) | Correlation clusters (corr > 0.5) |
| --- | --- | --- | --- |
| 40 exit tweaks of one base (corr 0.95) | 41 | 1.2 | 1 |
| 40 different blocks (corr 0.2) | 41 | 35.7 | 41 |
| 40 tweaks + 10 different blocks | 51 | 1.9 | 11 |
| 40 looser tweaks (corr 0.8) + 10 blocks | 51 | 3.3 | 11 |

**Explaining the numbers.** The shortcut formula lets the big cluster of tweaks swamp the ten genuinely different variants and reports about 2 tries where 11 is right. A clustering count gets 11. So if option C is used, it must cluster (ONC or similar), not use the shortcut. My threshold clustering is a crude stand-in for ONC and only illustrates the point. INFERRED.

**What C needs.** Every run's trade stream on a common clock (daily R per run is enough), which the try ledger plus results in R give (R43 F1, F5). The clock must be shared, so streams from different markets are compared on calendar days. INFERRED.

**C and D combine.** C sets the count; D can halve or double it by whether the edit was written before the run. Both are numbers on the judge card. INFERRED.

### 3.2 What still needs the edit type

Counting does not decide identity. Whether an edit makes a new version or a new unit stays with R43's identity table (`R43:147-156`, CHECKED). C only says how much the edit costs in tries. INFERRED.

---

## 4. Judging when the unit owns its exits

Since the unit owns its exits (STATE 30 Oct, CHECKED), an exit change and an entry change both change the unit's trades. Options for judging them the same way:

| Option | For | Against |
| --- | --- | --- |
| **A. Judge the whole unit as one stream; run entry and exit diagnostics beside it, never as gates** | one verdict; exits and entries treated alike (section 3 C counts both) | the diagnostics need MFE and MAE per trade |
| B. Judge the entry first with a fixed generic exit, then the exit on top | finds a weak entry early | a generic exit is a choice that biases the entry test; Faith notes exits are harder to judge alone because they depend on the entry (book summary, secondary, CHECKED) |
| C. Judge exits from a library of exit sets per context | matches research 35's open "exit by context" question | not built; exit maths is the risk session's |

**Diagnostics for A** (all need excursions in R per trade, `R43` F1):
- **Entry edge ratio**: average favourable excursion over average adverse excursion, each divided by ATR at entry, at fixed horizons after entry; a random entry sits near 1.0 (StrategyQuant blog, CHECKED; Build Alpha, CHECKED). It tests the entry without its exit.
- **Exit capture**: realised R as a share of the trade's best favourable excursion, and give-back from the peak ("give-back from peak" is one of the exit families research 35 found missing, STATE research 35 row, CHECKED). It tests the exit without changing the entry.
- **Same entries, other exits**: rerun the unit's own entries with its exit swapped for a reference exit; the difference is the exit's contribution, counted as a try under section 3. INFERRED.

---

## 5. What-If: gaps and how it can improve (L08-09)

QMB today: a saved view over one result with predicates `days`, `exclude`, `hours`, `include`, `max_trades`, `session`; "Never a new result, never admission evidence" (`R18` §2, CHECKED). R43 already says a What-If that changes which trades count should become a counted variant rerun (`R43` §3.4, CHECKED).

| Gap | Kind | Source or reason |
| --- | --- | --- |
| Remove the top N% most profitable trades | robustness (should not need a rerun) | SQ What If: "ommit 5% of the most profitable trades"; filter on keeping 80% of net profit (SQ docs, CHECKED) |
| Fixed size instead of the unit's sizer | robustness; the sizing-neutral view R43 asks for | SQ blog lists "use fixed lots size" (CHECKED) |
| Remove overlapping trades | robustness | SQ blog (CHECKED) |
| Every second trade, random 50% of trades | robustness against a few lucky clusters | SQ custom What-If example "takes every second trade" (CHECKED) |
| Entry one bar late, or a fixed latency | execution robustness | INFERRED; scalpers' main fragility (R35 §2.1, CHECKED there) |
| Cost shock per trade (spread at the hour's 90th percentile from the market journal) | cost robustness | INFERRED; market journal (R12, CHECKED there) |
| Missed fills: drop a share of limit-order fills that touched but did not trade through | fill robustness | INFERRED |
| Only trades in context state X (needs stamps) | improvement → counted variant | INFERRED; R43 F1 |
| Stops triggered on mark price instead of last price (perps) | venue realism | research 45 §3.6 |
| Funding charged at each settlement (perps) | carry realism | R43 §3.4 "funding as a carry cost" (CHECKED) |

**One rule makes What-If safe.** A robustness What-If (removes good trades, adds costs, adds latency) can stay a view: it can only make results worse. An improvement What-If (removes bad trades by day, hour, session or context) becomes a hypothesis: it creates a counted variant and must be rerun, because "if you don't take one trade it might influence subsequent trades" (SQ blog, CHECKED). INFERRED rule; the warning is SQ's own.

---

## 6. What QMB must record so the old sizing can be replayed (note only)

The old system's "radioactive" sizing was enhanced Kelly with house money, reverse house money and cross-session compounding (`R19` §5, CHECKED). Its design belongs to the risk session. For any sizing rule to be replayed later, each trade row needs (INFERRED from what those rules read, `R19` §5):
- result in R and in money, initial risk in money, costs in R and money (R43 F1);
- equity before the trade, and the session and day the trade belongs to (house money reads profit so far in the session);
- the trade's order in the unit's sequence and the win/loss streak before it (reverse house money and streak rules read it);
- the account and the slot or unit it traded in (old house money was bot-scoped, then slot-scoped, `R19` §5, CHECKED);
- **would-have-done rows when the unit was stopped or skipped** (R43 lifecycle: "A stopped unit keeps writing would-have-done rows", CHECKED). Without these, a rule that halts after losses cannot be replayed with a different halt.

**Replay options** (for the risk session to choose): (a) sizing-only replay over the fixed trade list, fast but wrong when sizing changes which trades happen (margin, halts); (b) full rerun with the sizer in the loop; (c) both, flagging any run where (a) and (b) disagree. INFERRED.

---

## 7. What can run today

| Step | Today? | Needs |
| --- | --- | --- |
| 0 claim card | yes as a template field | a field on the unit spec |
| 1 rule significance | yes (library function, `R14` §9.3, CHECKED) | a unit runner (PR 204 runs no trades, `R18` §2, CHECKED) |
| 1 edge ratio | no | excursions per trade |
| 2-3 cost stress, walk-forward | built in QMB (`R18` §2, CHECKED) | calibrated costs (GAP-0048) for a real verdict |
| 4 deflated Sharpe with effective tries | the formula exists in a template script (`R18` §2, CHECKED) | the ledger at the door; trade streams in R; clustering |
| 5 neighbourhood, Monte Carlo | built | nothing more |
| 5 What-If robustness filters | partly (six improvement filters only) | the gaps in section 5 |
| 6 context lift | no | readings stamped on trades (R43 F1, F2) |
| 7 paper and live-vs-backtest overlay | no | node paper, recorded quotes, LEAN-style overlay (`R14` §9.3, CHECKED) |

---

## 8. Numbers named here (all starting defaults)

| Number | Default | Why |
| --- | --- | --- |
| Rule significance | p below 0.05 vs random entries | Jesse's test; conventional |
| Entry edge ratio | above 1.0 at the claimed horizon | random entry is about 1.0 (Faith via SQ) |
| Cost stress | 1.5x (shipped), 2x (old QMX) | R43 §5 |
| Walk-forward efficiency | 0.5 | shipped judge |
| Deflated Sharpe confidence | 0.95 | shipped judge |
| Remove-top-trades What-If | remove 5%, keep 80% of profit | SQ default |
| Parameters gauge | warn above 10, flag above 20 | QuantConnect Research Guide |
| Backtests per idea gauge | warn above 30, flag above 70 | QuantConnect Research Guide |
| Refinement rounds | stop after 15 without a validated gain | R11 |
| Effective-try clustering | correlation of daily R above 0.5 joins a cluster (illustration; ONC preferred) | section 3 |
| Pre-registered vs post-hoc weight | 1 vs 2 | placeholder |
| Paper before his card | 30 trades or 4 weeks, later of the two, and the sequential score not below its start | R43 §5 plus research 24 |
| Replay match on paper | about 80% of trades | SQ rule of thumb via R08 |

---

## 9. Sources

Read this session:
- Arnott, Harvey, Markowitz 2019: https://doi.org/10.3905/jfds.2019.1.064 ; https://people.duke.edu/~charvey/Research/Published_Papers/P138_A_backtesting_protocol.pdf
- López de Prado, The 10 Reasons Most Machine Learning Funds Fail: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104816 ; https://www.garp.org/hubfs/Whitepapers/a1Z1W0000054x6lUAA.pdf
- López de Prado and Lewis 2019, ONC: https://doi.org/10.1080/14697688.2019.1622311 ; https://codemacher.com/wp-content/uploads/2021/02/Detection-of-false-investment-strategies-using-unsupervised-learning-methods_M.LopezDePrado_and_M.Lewis_2018.pdf
- Bailey, Borwein, López de Prado, Zhu 2014, minimum backtest length: https://www.davidhbailey.com/dhbpapers/backtest-pseudo.pdf ("if only 5 years of data are available, no more than 45 independent model configurations should be tried")
- QuantConnect: https://www.quantconnect.com/docs/v2/cloud-platform/backtesting/research-guide ; https://www.quantconnect.com/docs/v2/writing-algorithms/optimization/parameters ; https://www.quantconnect.com/announcements/15502/making-models-that-fit-the-signal-not-the-noise/
- Jesse: https://docs.jesse.trade/docs/research/optimize ; https://docs.jesse.trade/docs/mcp/
- StrategyQuant: https://strategyquant.com/doc/strategyquant/what-if-simulations/ ; https://strategyquant.com/blog/analyzing-and-improving-your-strategies-using-what-if-scenarios/ ; https://strategyquant.com/doc/create-a-new-what-if-function/ ; https://strategyquant.com/blog/edge-ratio-in-strategyquant-x/
- Build Alpha, E-ratio: https://www.buildalpha.com/eratio/
- Secondary, used only where a primary agrees: https://reasonabledeviations.com/notes/adv_fin_ml/ ; https://www.bookey.app/book/way-of-the-turtle ; https://tradingtact.com/edge-ratio/

Through earlier files (CHECKED there): deflated Sharpe, PBO, CPCV vs walk-forward, Quantopian 888 algorithms (R05); old QMX pass numbers, decay check, QuantConnect reconciliation, SQ compare (R08); refinement-depth papers (R11); LEAN and Jesse borrow list (R14 §9.3); QMB as built (R18 §2); the old sizing system (R19 §5); QMB rebuild table and judge defaults (R43 §3.4, §5).

Simulations: `C:/Users/Mubarak/AppData/Local/Temp/claude/C--Users-Mubarak-Desktop-QMX/ed09cf0c-69f1-44ab-8c6b-76992918774a/scratchpad/sim24/tries.py` (seed 11) and `sim.py` (seed 7, used in research 24), run with `C:/Users/Mubarak/Desktop/QMX/.venv/Scripts/python.exe -I`.
