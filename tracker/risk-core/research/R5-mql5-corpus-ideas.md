---
ticket: R5-mql5-corpus-ideas
title: Ideas from the local MQL5 article corpus for QMX risk and sizing
date: 2026-11-03
author: opus research agent (read-only on the repo; this file is the only write)
asked by: lead, plus three operator steers during the run (trading lens A-F first; many instruments; borrowed logic from other fields)
corpus: C:\Users\Mubarak\Desktop\QMX\.worktrees\mql5-library\data\mql5-library\ (3,128 articles with text, catalog.jsonl, md\)
method: topic searches over catalog.jsonl titles and descriptions; ripgrep full-text searches for multi-asset sizing and for analogies to other fields; then reading the strongest articles in md\ (prose read in full or by section, code skipped). About 150 articles reviewed, about 110 kept. Scripts in the session scratchpad, not in the repo.
not repeated: R1 section 3 (21720, 24477, 24237, 24249, 15085, 14336, 18918, 17249, 24147, the money classes), the 06 pilot (50 ids), the 03 survey (about 55 ids). They appear only as anchors in "Ideas that could combine".
not done: QMX is not designed here. No browser used. Nothing committed.
---

# R5: Ideas from the MQL5 corpus for QMX risk and sizing

## How to read this

- Citations are `md\<id>.md:line`, lines in the local Markdown copy. Article URL is `https://www.mql5.com/en/articles/<id>`.
- Evidence labels:
  - **NONE**: no test result.
  - **BT-IS**: the author's own backtest on data used to build or tune it, or no split stated.
  - **BT-OOS**: the author's backtest on a holdout or forward period. "thin" means few trades or one regime.
  - **SIM**: synthetic data, Monte Carlo, or a simulated market.
  - **DEMO**: run on a demo account. No article here shows a real-money track record.
  - **MECH**: the maths or code is checked (unit tests, Python cross-check), not a trading result.
- **[idea]** is my suggestion for what QMX could borrow. It is an idea for the expansion round, not a design. **INFERRED** is my reasoning, not the article's.
- Layers: **X1** template shape, **X2** sizing and accelerators, **X3** brakes, exits and drift, **X4** scenarios, **X5** edge verification, **X6** observability, **X7** agents.
- Structure: Part I is the trading lens (A-F) and shapes everything after it. Part II normalises risk across instrument classes. Part III holds the eleven technique topics. Part IV covers logic borrowed from other fields. Parts V and VI hold combinations and traps. Part VII lists coverage.

## 0. Short version

1. **The unit of control moves outward.** The best 2026 articles stack trade, basket and account checks, and each one says what the level below cannot see. Three trades that each risk 1 % can still overload the account (`md\24331.md:71-73`). Long EURUSD, long GBPUSD and short USDJPY are one bet against the dollar (`md\24392.md:58-66`).
2. **When size comes from a target, risk is an output.** Cap the loss each leg's stop implies, and cap the sum across legs, after sizing (`md\24331.md:479-501`, `:597-632`).
3. **The most useful habit in the corpus is a fair control.** BOCPD-timed de-risking beat a random brake that fired just as often (`md\23482.md:682-699`). Without that control, any brake on a losing strategy looks good just because it trades less. Two articles show the effect and do not control for it: `md\22833.md:928-936` and `md\22274.md:240`.
4. **For scalpers, costs and data quality decide the result.** The corpus measures slippage asymmetry (`md\22998.md:55`), a cost cushion (`md\23299.md:78`) and spread against the instrument's own history (`md\23355.md:42`). A test reporting 100 % real ticks had 33,584 of 46,252 minutes on generated ticks (`md\24562.md:40`). An EA drained its account in under a year on another broker's quotes, because its signal read tick volume (`md\15330.md:62`, `:107-109`).
5. **Thresholds taken from textbook theory misfire.** CUSUM fired about five times more often than its formula predicts, across six instruments (`md\23103.md:489`, `:674`). A curvature gate "refuses 0 of 82 signals while looking like a working filter" (`md\24202.md:767`). Calibrate per instrument against a null.
6. **Exits need per-instrument calibration.** A survival model from medicine produced calibrated hold-or-close probabilities on four instruments. One shared decision threshold still lost more on USDJPY and XAUUSD (`md\24106.md:476-487`, `:509`).
7. **Brake design borrowed from software reliability.** A half-open probe comes before full restore (`md\23315.md:1320`). Safe mode starts when stored state and the broker disagree (`md\22615.md:338-343`).
8. **Instruments do not normalise themselves.** FX positions split exactly into currency legs (`md\24392.md:381`). Metals, indices and crypto do not split that way (`md\24392.md:728`, `:734`). Pip-based logic breaks on indices, oil and metals (`md\23618.md:1546`). Costs written as fractional returns work on any instrument (`md\22372.md:900`). No article normalises all seven instrument classes in one unit (INFERRED).
9. **Agents.** MetaTrader's own MCP agent treats tool content as data and leaves trading on manual confirmation (`md\24265.md:551`, `:579`). The LLM trading-bot articles show thin tests (`md\19345.md:611`, `md\20329.md:812`) or none (20071).
10. **Borrowed logic is common, and its tests are worth more than its profit claims.** Control theory, industrial quality control, survival analysis, immunology, reliability engineering, random matrices, optimal transport and compression all appear (Part IV). What QMX can use is the gates, nulls and test designs. The profits are mostly in-sample.

---

# Part I. The trading lens (A-F)

Each lens names the articles that answer it, then says how it shapes the technique topics in Part III.

## A. Portfolio-level sizing and optimisation across many EAs

The corpus has two schools. One normalises each strategy to a drawdown budget and then scales the group (14336, covered in R1). The other puts a controller above many signal-only agents (RiskGate 21720, covered in R1, and 23629 below). Correlation work moved in 2026 from rolling Pearson to estimators that adapt (23322), denoise (24243) or read the network's shape (24202).

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [23629](https://www.mql5.com/en/articles/23629) Institutional-Grade Multi-Currency Portfolio Engine (Part 1), 2026 | One Portfolio Controller publishes the remaining risk budget, lot ceilings and a halt flag. Instrument Agents check the budget before every order (`md\23629.md:50`, `:114-115`). If the controller is missing, agents enter "degraded mode" with conservative defaults (`:128`, `:600`). | NONE | Use the budget-and-halt broadcast. Do **not** keep trading on defaults when the controller is gone. RiskGate rejects all trades in that case (R1 3.2), and that is the safer contract. A 10-second timer can authorise trades on stale state (`:602`). | X1, X3 |
| [14107](https://www.mql5.com/en/articles/14107) Multi-currency EA (Part 2): virtual positions, 2024 | Strategies trade only virtually and report the volume they want. One converter nets those volumes into real positions (`md\14107.md:40-42`). Nine instances came out slightly better than with real positions (`:920`). | BT-IS | Units declare intent and a netting layer places orders. This also cuts spread paid when two units offset each other (INFERRED). | X1, X2 |
| [14478](https://www.mql5.com/en/articles/14478) + [14549](https://www.mql5.com/en/articles/14549) Multi-currency EA (Parts 6-7): automatic group selection and forward period, 2024 | Picks 10-20 instances out of 20-50 thousand parameter sets so they work well *together*, using clustering (`md\14478.md:44`). Choosing groups with a forward period "did not increase our confidence" (`md\14549.md:349`). | BT-IS, BT-OOS (3 months, thin) | Group selection is itself a search, so it needs the deflated-Sharpe treatment (24150). The author's honest null on forward selection is worth keeping. | X5 |
| [23322](https://www.mql5.com/en/articles/23322) Exponentially weighted covariance, 2026 | A fixed window treats a hedge at 0.85 correlation as still a hedge after it has fallen to 0.30 (`md\23322.md:38-40`). λ = 0.94 gives an effective window of about 16.7 (`:83`). Warns about cold start (`:93`) and leaves λ at 0 so an unconfigured estimator stays inert (`:177`). | MECH | An adaptive correlation input to the exposure ledger. "Inert until configured" is a good default rule. | X2, X3 |
| [24243](https://www.mql5.com/en/articles/24243) Random Matrix Theory denoising, 2026 | With N symbols and T bars, most of a correlation matrix is sampling noise unless T is much larger than N (`md\24243.md:40`). Marchenko-Pastur cleaning made weights steadier by about 27-29 % (`:961`). Makes no P&L claim (`:963`). | SIM, MECH | Clean the correlation matrix before it sizes a basket. The steadiness gain is measured. P&L is not. | X2 |
| [24202](https://www.mql5.com/en/articles/24202) Ollivier-Ricci curvature of the correlation network, 2026 | Reads whether the market's cluster structure still exists, not how high correlation is (`md\24202.md:54-66`). March 2020 was *not* the extreme reading (`:673`). A gate whose threshold sat on the wrong scale refused 0 of 82 signals (`:767`). The result did not repeat across symbols (`:777`). | BT-IS, honest nulls | Use it as a "sectors have merged into one" alarm at most. Its main lesson is to ship a null beside every statistic (`:851`). | X3, X5 |
| [23440](https://www.mql5.com/en/articles/23440) (+23314) Measuring What Matters (Parts 2-3), 2026 | Eigen-decomposes the portfolio covariance. One factor, almost all gold, held 91.24 % of variance in a three-symbol book (`md\23440.md:38`). | MECH | A "share of risk from factor 1" readout for the book. | X6 |
| [18770](https://www.mql5.com/en/articles/18770) Self Optimizing EA (Part 8.3): weighted voting, 2025 | Gives each strategy one vote and lets the genetic optimizer set vote weights to test whether every strategy is needed (`md\18770.md:42-44`). | BT-IS | A pruning test for unit groups. Same overfit risk as 14478. | X5 |
| [23763](https://www.mql5.com/en/articles/23763) Network momentum (lead-lag graph), 2026 | Learns which markets lead which and spreads momentum along those links (`md\23763.md:40`). Its next step is to restore volatility-target sizing (`:847`). | BT-IS | Not a sizer yet. Lead-lag links could flag correlated units before both fire (INFERRED). | X2 |
| [15779](https://www.mql5.com/en/articles/15779) + [16604](https://www.mql5.com/en/articles/16604) VaR portfolio optimisation, 2025 | VaR and Markowitz weights for FX. A year of results put AUDUSD at 51 % and EURUSD and USDCAD near 0 %, with profit factor 1.03 (`md\15779.md:318-341`), yet the text says it "works successfully in real market conditions" (`:205`). | BT-IS | Keep as a trap: optimisers concentrate the book. See Part VI. | X5 |

**Shapes Part III:**
- Topic 1 (sizing): size must depend on what else is open (concurrency, 21824), not only on the trade.
- Topic 2 (limits): portfolio limits only bind if they sit outside every EA (`md\24392.md:76`).
- Topic 6 (many EAs): correlation is an input that drifts and has noise, so it must be estimated with care.
- Topic 7 (drift): picking groups is a multiple-testing problem.

**Across instruments:**
- Currency-leg exposure works for FX only (`md\24392.md:728-734`).
- Covariance methods (23322, 24243, 24202) work on any instrument but need aligned calendars. 24202 measures each symbol's coverage and refuses to compute on a partly loaded basket (`md\24202.md:845`).
- Crypto trades seven days and FX five. An aligned window silently drops weekend bars (INFERRED).

## B. Scalping and very low timeframe, where costs dominate

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [22772](https://www.mql5.com/en/articles/22772) Multi-Pair EA (Part 9): execution noise filtering, 2026 | Five gates must pass before any signal fires: spread expansion, tick velocity, quote gaps, micro-volatility, slippage stability. "The EA does not predict direction. It predicts whether the market can currently fill an order" (`md\22772.md:52-56`). Defaults are 2x median spread, 40 ticks/s and 150-point gaps (`:90-97`). The tester uses **looser** gates (`:131-134`, `:711`). | BT-IS, 2 months | The five gate types are a good checklist for an "execution fit" brake. The looser tester gates are a trap: the backtest checks a different gate from the one that runs live. | X3 |
| [24742](https://www.mql5.com/en/articles/24742) Market activity from waits between quotes (ACD), 2026 | On EURUSD the wait between quotes in the quietest half hour is about 47 times longer than in the busiest (`md\24742.md:40`). An Engle-Russell duration model adds a small but significant gain to next-minutes volatility forecasts on six symbols (`:44`). Retail ticks are quote changes, not trades (`:60`). Recalibrate monthly and on any broker change (`:984`). | BT-OOS | An activity gauge for scalper size and a stress brake. "Recalibrate on broker change" belongs in the unit's metadata. | X2, X3 |
| [24562](https://www.mql5.com/en/articles/24562) Depth of the broker's tick history, 2026 | "History Quality 100 % real ticks" can coexist with 33,584 of 46,252 minutes on generated ticks (`md\24562.md:38-40`). Shows how to read the tester journal for the true share (`:428-430`). | MECH | Stamp every scalper backtest with its real-tick share. Do not trust a scalper result without it. | X5, X6 |
| [15330](https://www.mql5.com/en/articles/15330) Multi-currency EA (Part 16): different quote histories, 2025 | On another broker's real quotes the EA lost the whole deposit in under a year (`md\15330.md:62`). The cause was a tick-volume signal, since brokers only need four correct ticks a minute to draw the same M1 bars (`:107-109`). Replaying the same deals on the other quotes came out almost the same (`:845`). | BT-IS, MECH | Score units on the broker they will trade. Mark tick-volume signals as broker-specific. | X5 |
| [15360](https://www.mql5.com/en/articles/15360) Multi-currency EA (Part 17), 2025 | Results depend even on which symbol is set as the main one in the tester (`md\15360.md:718`). | BT-IS | Add to the backtest-validity stamp. | X5 |

Weak, kept only as context: 19989 scalping vs swing modes in one EA (BT-IS), 15895 order-flow scalping with "low profit factor" (`md\15895.md:482`), 16643 titled "scalping" but trades D1 (`md\16643.md:38`).

**Shapes Part III:**
- Topic 8 (costs) comes before topic 1 for scalpers. Size is worthless if the cost cushion is thin (23299).
- Topic 3 (brakes) has to scale with trade count. R2 found a two-loss breaker fires on 79 % of days at 10 trades a day.
- Topic 5 (exits) should work in R and in account money, not pips (23716, 23618).
- Topic 7 (drift): scalpers reach a test sample quickly, but on quotes that may be generated.

**Across instruments:** quote rhythm, spread profile and tick history depth differ by symbol and broker (`md\24742.md:984`, `md\24562.md:422`). Index CFDs and crypto have their own session gaps. Stocks via CFD have no last-price ticks on the author's feed (`md\24742.md:60`).

## C. Day trading and intraday (session opens, opening ranges, intraday mean reversion)

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [17745](https://www.mql5.com/en/articles/17745) Decoding Opening Range Breakout, 2025 | Rebuilds three Concretum ORB papers on the US open. The author replaced the paper's 5-minute-candle stop with a 1 % price stop and 2 % risk because the original was "impractical for retail" (`md\17745.md:80-88`). The three combined: max drawdown about 10 % against 15 %+ alone, monthly correlation about 0.3 (`:905`, `:919`). Warns that backtest correlation depends on the period (`:897`). | BT-IS | Treat session-open units as a family and size the family, not each unit. | X2 |
| [23226](https://www.mql5.com/en/articles/23226) Low-Frequency Quant (Part 4): ORB on Stocks in Play, 2026 | Trades only stocks with unusual relative volume at the open. Cites SFI: returns went from 29 % to 1,637 % with the filter (`md\23226.md:68`, `:88`). Pre-screens on price, volume and ATR above $0.50 (`:94`). Win rate below 30 % (`:818`). | NONE (cites a paper) | Relative volume at the open as an "allowed to trade today" gate for stock units. A sub-30 % win rate needs loss-streak brakes that expect long runs. | X2, X3 |
| [17636](https://www.mql5.com/en/articles/17636) Connors RSI2 day trading, 2025 | Tests daily-bar RSI2 mean reversion on US500 M30 (`md\17636.md:46`). | BT-IS | Shows intraday mean reversion copied from daily research. Its decay needs watching. | X5 |
| [16171](https://www.mql5.com/en/articles/16171) Monochronic Trading (Part 1): broker time zone and DST, 2026 | You must know the broker's time zone and DST rules before any session test (`md\16171.md:46`). Detects them from NFP release times. | MECH | The session clock is a unit input, not a constant. | X1 |
| [23168](https://www.mql5.com/en/articles/23168) Intraday return heatmap, 2026 | Average return by hour and weekday (`md\23168.md:40`). | NONE | An observability view for session windows. | X6 |
| [22516](https://www.mql5.com/en/articles/22516) Session-aware time features, 2026 | Cyclical encodings and session volatility features (`md\22516.md:54-58`). In 22274, session *volatility* columns carried 25.6 % of importance against 2.5 % for session *flags* (`md\22274.md:242`). | BT-OOS (in 22274) | Gate sessions on measured volatility, not on clock flags alone. | X2, X3 |
| [4102](https://www.mql5.com/en/articles/4102) Night trading in the Asian session, 2018 | EUR pairs go flat at night while JPY pairs stay active (`md\4102.md:44`). | BT-IS | Session windows are per instrument. | X1 |
| [1575](https://www.mql5.com/en/articles/1575) Asian-session myth, 2010 | Finds no link between the Asian session and the rest of the day (`md\1575.md:351`), yet reports "100 % probability" for a 5-point target over 50 days (`:349`). | BT-IS, tiny | Trap, see Part VI. | X5 |

**Shapes Part III:**
- Topic 2 (limits): the "day" needs a contract. Fix it at a reset hour, persist the baseline and survive restarts (24397, 21313).
- Topic 4 (calendar): session and news windows are in server time.
- Topic 5 (exits): time exits before the close (`md\17745.md:86`).
- Topic 3 (brakes): low win-rate breakout units need streak brakes sized to their own streak distribution, not a fixed count.

**Across instruments:** "the open" means one thing for US indices and stocks (9:30 ET, `md\17745.md:48`), something else for FX (London, NY overlap), something else again for metals and energy (Comex and NYMEX hours), and nothing for crypto (24/7). Futures add a daily maintenance break. Server-time conversion and DST apply to all of them (16171).

## D. Macro structure: regimes, cross-asset links, macro drivers

The corpus is thin on real macro data (CFTC, central bank balance sheets and FRED indexes appear in 18303, 18355 and 15841, all BT-IS or untested). It is strong on online regime-break detection.

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [23482](https://www.mql5.com/en/articles/23482) Bayesian Online Change-Point Detection, 2026 | Gives each bar a probability that the regime just broke (`md\23482.md:40-42`). Used as a de-risk cooldown with three arms: none, BOCPD, and a random brake with the same trigger rate (`:586-598`, `:632`). BOCPD cut max equity drawdown from 856 to 756 while skipping 4 of 97 trades. The random brake made drawdown worse, at 1,007 (`:682-699`). All three arms lose money (`:699`). Few trades (`:720`). It "measures change, not direction" (`:721`). | BT-IS with a proper control | A regime-break brake that cuts exposure for a cooldown. Above all, the **random-control test design** for any brake (X5). | X3, X5 |
| [24460](https://www.mql5.com/en/articles/24460) Hidden semi-Markov regimes with durations, 2026 | Regime age is information. A plain HMM assumes the chance a regime ends is the same whatever its age (`md\24460.md:38-40`). On 8 months of XAUUSD M5 the trades closed by the duration gate made money (59.3 % wins) while the system as a whole lost (`:1470`). | BT-IS | Taper new adds as a regime ages. Pairs with 21833 cycle age in the pilot. | X2, X3 |
| [22940](https://www.mql5.com/en/articles/22940) Market Microstructure (Part 7): regime classification, 2026 | Six labels: Normal 50 %, Stressed 21 %, Noisy 10 %, Informed 7 %, Trending, Mean-Reverting. Rules run in priority order with Stressed checked first. Stressed sessions have 1.8x normal volatility (`md\22940.md:50-95`). | BT-IS (602 NQ M1 sessions) | A session regime label that sizing and brakes can read. "Stressed overrides everything" is a clear priority rule. | X3 |
| [23734](https://www.mql5.com/en/articles/23734) Gold volatility regime from options, 2026 | Ratio of implied to realised volatility. Most sizing rules look backward at realised volatility, while implied looks forward (`md\23734.md:81`). "Not a timing trigger" (`:85`). The data bridge (compute outside, publish JSON, read in a service) works for any data (`:87`). | MECH | A forward-looking volatility input for size where options exist (gold, indices, some FX). | X2 |
| [22175](https://www.mql5.com/en/articles/22175) Carry trade logic, 2026 | Puts the daily swap in account currency into the hold and size decision. "For scalpers, swap rates don't really matter" (`md\22175.md:38`). The test uses a synthetic swap override (`:664`). | SIM | A holding-cost input for multi-day units. Triple-swap day handling is in 23327 (`md\23327.md:329`). | X2 |
| [20946](https://www.mql5.com/en/articles/20946) Stat-arb (Part 10): structural breaks, 2026 | Chow test confirms a dead relationship. Rolling eigenvector comparison says it needs updating. Recursive CUSUM catches it early (`md\20946.md:339-345`). | BT-IS | Three break detectors with different jobs: confirm, update, early warning. | X3 |

Weak, kept as pointers: 17781 regime-switching EA (BT-IS), 18355 central-bank liquidity index (BT-IS, `md\18355.md:424` limits), 1087 macro regression (2014, NONE), 15841 CBOE vol indexes via FRED (BT-IS).

**Shapes Part III:**
- Topic 1 (sizing): a regime or stress multiplier on size. Forward-looking (23734) beats backward-looking where options exist.
- Topic 3 (brakes): change-point cooldowns. Test them against random cooldowns.
- Topic 4 (calendar): use the calendar as a volatility filter, never as a direction signal (`md\22196.md:1081`).
- Topic 7 (drift): regime breaks in price (fast) are different from edge decay in the unit's own record (slow, R2).

**Across instruments:**
- 23103 tested CUSUM on FX, gold, DE40 and USTEC. The false-alarm rate was much the same across them (`md\23103.md:436`, `:489`).
- Carry matters for FX and metals held overnight. Index CFDs and crypto have their own financing (INFERRED, not covered in the articles read).

## E. Microstructure: spread, depth, order flow and liquidity by hour

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [22938](https://www.mql5.com/en/articles/22938) Market Microstructure (Part 5): noise, 2026 | Five M1 measures: quoted spread proxy, Roll spread, noise ratio, order imbalance, adverse selection. The Roll spread comes out near zero on NQ M1, as expected at one-minute aggregation (`md\22938.md:472`). Gives an action table: reduce size above the 75th spread percentile, "reduce size materially" above the 90th (`:484-494`). Thresholds are specific to NQ M1 (`:484`). | BT-IS (602 sessions) | A percentile-based size cut on stress, with the rule that thresholds are refit per instrument. | X2, X3 |
| [22939](https://www.mql5.com/en/articles/22939) Market Microstructure (Part 6): order flow, 2026 | Approximates VPIN from bars and says what bars cannot show (`md\22939.md:44`). | BT-IS | Order-flow toxicity as a stress input, with a caveat flag. | X3 |
| [23372](https://www.mql5.com/en/articles/23372) Market Microstructure (Part 8): micro-trend strength, 2026 | A per-bar score whose thresholds loosen in high-confidence regimes and tighten in low ones (`md\23372.md:40-44`). | BT-IS | Regime confidence scales gates. Same pattern as A/D. | X3 |
| [23355](https://www.mql5.com/en/articles/23355) Adaptive spread monitoring and order gating, 2026 | Judges the live spread against the instrument's own rolling histogram (`md\23355.md:40-42`). A 5-pip edge keeps 4 at 1 pip of spread and nothing at 5 (`:54`). Two percentile thresholds, no per-instrument tuning (`:1113`). Cannot tell a lasting shift from a spike (`:1103`). | MECH | A percentile spread gate per symbol. Two window lengths separate spike from drift (`:1115`). | X3 |
| [9804](https://www.mql5.com/en/articles/9804) Bid/ask spread analysis, 2021 | Measures true spreads by hour from ticks. Advises staying on USD majors (`md\9804.md:394-398`). | BT-IS | Hourly spread profile per symbol and broker. | X6 |

Pointers not read in full: 22063 activity and imbalance bars, 15748 order-book indicator, 21876 round-number liquidity (NONE), 18661 time-at-price heatmap (NONE).

**Shapes Part III:**
- Topic 8 (costs): spread is a distribution, not a number.
- Topic 1 (sizing): a stress-percentile size cut.
- Topic 3 (brakes): "stressed session" brake (22940) and execution anomaly brake (24251).
- Topic 5 (exits): breakeven and trailing offsets need spread awareness (`md\23716.md:1571`).

**Across instruments:**
- Only exchange instruments (futures, some stocks) have real volume and depth. Spot FX and most CFDs carry tick volume only (`md\24742.md:60`).
- Microstructure thresholds are per instrument and per broker (`md\22938.md:484`).

## F. Agents and AI for reading macro, microstructure and news

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [22495](https://www.mql5.com/en/articles/22495) AI-Powered Trading Systems (Part 9): signal dispatcher, 2026 | Forces AI output into a line-based KEY:VALUE protocol, which survives prose drift better than strict JSON (`md\22495.md:2742`). | NONE | Agents propose through a narrow schema. A parse failure means "no proposal". | X7 |
| [17986](https://www.mql5.com/en/articles/17986) News + AI, 2025 | Trains a model on calendar data. Ends by warning that trading at or after releases is very risky (`md\17986.md:801`). | BT-IS | Agents can tag events and impact. They should not trigger trades. | X7 |
| [18685](https://www.mql5.com/en/articles/18685) Local AI model insights lane, 2025 | Hosts an open model locally and shows "insights" next to news (`md\18685.md:461-463`). | NONE | A local model keeps account data on the PC (matches 24265:587). | X7 |
| [20329](https://www.mql5.com/en/articles/20329) LLM with MT5 (Part II): fine-tuning, 2026 | A base LLM bought EURUSD at RSI 32 and rode a 200-pip fall (`md\20329.md:40`). Fine-tuning on pair statistics reportedly raised the win rate by about 10 points (`:812`). | BT-IS, one demo week (`:38`) | Shows why an LLM needs instrument-specific statistics. Not evidence of edge. | X7 |
| [21115](https://www.mql5.com/en/articles/21115) Multi-agent cross-symbol environment, 2026 | Per-symbol agents share signals through a coordination layer that enforces portfolio limits (`md\21115.md:57`), "while keeping execution, risk management, and validation" in MQL5 (`:1143`). | NONE | Same split as QMX: agents analyse, the core holds risk. | X7 |

**Shapes Part III:**
- Topic 10 (LLM): agents read and propose, a human gate stays on trading (24265).
- Topic 4 (news): agents can enrich event metadata, for example which instruments an event touches beyond its currency, the gap 24250 names at `md\24250.md:532`.
- Topic 7 (drift): agent-built strategies need the same deflated tests (24150).

**Across instruments:** news relevance by currency fails for indices, metals, energy and crypto (`md\24250.md:532`). Mapping events to those instruments is a reading job an agent could do, with a human check (INFERRED).

---

# Part II. Normalising risk across instrument classes

No article normalises all seven classes (FX, indices, metals, energy, crypto, futures, stocks) in one risk unit. The pieces exist across articles:

| Problem | What the corpus does | Source | [idea] |
|---|---|---|---|
| Money at the stop | Use the broker's tick value and tick size. Pips × lots "will be wrong" on gold, index CFDs and crypto. | `md\22187.md:100-104` | Every unit's risk is money at the stop, from broker metadata, never pips. |
| Profit currency differs from deposit currency | The built-in calculation drifts for crosses. A custom model matches better on close. | `md\10211.md:515` | Re-read conversion at entry and on close. |
| Tick value drifts on cross-currency symbols | A metadata cache must refresh tick value more often than static fields. | `md\23388.md:925` | Cache static fields. Read tick value live when sizing. |
| Symbol names differ by broker | GOLD, XAUUSD.a, US30Cash, EURUSDm. Resolve logical names to broker names with validation. | `md\23199.md:51-53`, `:1625` | A logical instrument id in the unit, resolved per broker. |
| Volatility differs by instrument | Volatility signatures per pair. One ATR multiple fails in different ways on gold and GBPUSD. | `md\23597.md:46-48` | Stops and sizes in volatility units, calibrated per instrument. |
| Costs differ by instrument | Write costs as fractional returns. Use the p95 spread or session-adjusted hourly spreads, not the mean. | `md\22372.md:900` | One cost model for all classes, in return units. |
| Correlated exposure | FX: exact currency legs. Others: no leg structure. Use covariance. | `md\24392.md:381`, `:728-734` | Two exposure engines: legs for FX, covariance for the rest, cleaned (24243). |
| Exposure measured in lots | Lots compare exactly only on the base leg. The quote leg is a concentration signal, not a notional. | `md\24392.md:394`, `:734` | Measure exposure in account currency notional. |
| Pip-based trailing and profit locks | A percentage-of-profit trail in pips misprices indices, oil and metals. | `md\23618.md:1546` | Trails in R or money. |
| Detector thresholds | CUSUM false alarms and microstructure cut-offs must be fitted per instrument. | `md\23103.md:676`, `md\22938.md:484` | A calibration record per instrument × detector. |
| Exit thresholds | One decision rule on a calibrated model worked on two pairs and failed on USDJPY and XAUUSD. | `md\24106.md:509-511` | Exit settings per instrument, fitted on a holdout. |
| Futures contracts | Splice expiring contracts into a continuous series. Overlap and gap choices matter. | `md\802.md:38` and its sections | Futures units need a roll rule and a spliced history. |
| Stock splits | The tester cannot handle splits (pilot, 20020). | 06 pilot | Stock units need split-adjusted history. |
| Calendar to instrument | Currency keys do not extend to indices, metals, energy or crypto. | `md\24250.md:532` | An event-to-instrument map, maintained (Part I F). |
| Session clock | Broker time zone and DST must be known before session logic. | `md\16171.md:46` | A server-time contract per broker. |
| Account-level normalisation | Size each strategy so its worst backtest drawdown is a fixed share of its fitted balance (14336, covered). Size by remaining budget (24249, covered). | R1 3.2 | Already in R1. Listed so the set is complete. |

INFERRED: the pieces combine into one "risk unit" record per (unit, instrument, broker): money per point, volatility scale, cost in return units, exposure engine (legs or covariance), session clock, roll and split rules, and calibrated detector thresholds. The corpus gives every field. No article assembles them.

---

# Part III. Technique topics

Each topic lists kept articles not covered before, plus an instrument note. An article appears in full once. Elsewhere it is cited by id.

## 1. Position sizing and money management

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [24331](https://www.mql5.com/en/articles/24331) Building Your Personal EA (Part 5): basket risk and strategy-specific sizing, 2026 | Treats all of an EA's positions as one basket, with VWAP entry, floating P/L including swap, margin and MAE (`md\24331.md:67`). An aggregate loss cut is "a policy about all of them", not a replacement for stops (`:249`). Time stop (`:251`). Pending orders are deleted when the basket is cut so it cannot rebuild itself (`:272`). Target-based sizing makes risk an output, so it is capped per leg and per basket (`:479-501`, `:597`). Committed risk is re-read from each position's stop, not from memory (`:624-632`). Averaging is "a martingale with better manners" without three caps (`:651`). | MECH (NONE for P&L) | Committed risk re-read from the broker. Basket caps on implied risk. Pending orders cancelled with the basket. MAE measured first, limits set after (`:398`). | X2, X3 |
| [22187](https://www.mql5.com/en/articles/22187) Safe pyramiding with a unified stop, 2026 | Two failure modes: equal-size adds triple the risk, and separate stops make the worst case unknowable (`md\22187.md:58-74`). Three conditions make total risk fall with each add: lots strictly decreasing, a unified stop that advances, every stop change confirmed (`:88-96`). Risk table: -$360, then +$25, then +$340 worst case (`:114-124`). Limits: lots not re-sized after equity changes (`:1145`), fixed-pip triggers (`:1154`), partial fills not handled (`:1157`). | BT-IS | An accelerator that adds only when the unified stop has locked more than the new risk. The "worst case is profit" claim ignores gaps and slippage (INFERRED, Part VI). | X2 |
| [22684](https://www.mql5.com/en/articles/22684) Falling-risk pyramid with bet sizing, 2026 | Wires 22187 to confidence sizing in five places. Floors lots so the decreasing rule survives lot-step clipping, and skips the entry if lots collapse to the minimum (`md\22684.md:119`). A budget gate blocks entries when the signal book is 90 % full (`:125`, `:138`). Add triggers can only tighten (`:157`). Needs about 500 bets before the reserve fit is stable (`:180`). | NONE (synthetic figure) | "Floor, then skip if it cannot be expressed" at tiny account sizes. A book-occupancy gate. One-way ratchets. | X2 |
| [21824](https://www.mql5.com/en/articles/21824) ML Blueprint (Part 10): bet sizing, 2026 | Fixed fraction treats a 51 % signal like a 95 % one and ignores budget already used today (`md\21824.md:79-81`). Concurrency explosion: overlapping signals pile up exposure (`:85`). Overtrading from tiny resizes (`:89`). Sizing is only as good as the probabilities fed in (`:401`). | MECH | Average size over active bets so many units firing together do not stack. Size in discrete steps to avoid churn. | X2 |
| [22274](https://www.mql5.com/en/articles/22274) Meta-labelling the classics (Part 1): RSI, 2026 | Plain RSI lost 625 pips over 576 trades, filtered lost 577 over 121, filtered and sized lost 86. The meta-classifier was **48 % accurate, below chance**. The 93 % drawdown cut "comes from exposure control, not predictive skill" (`md\22274.md:240`, `:221-232`). | BT-OOS (walk-forward, 3 years incl. 2022) | The honest lesson: drawdown cuts from fewer and smaller trades are mechanical. Any QMX sizing claim must beat a random filter of the same trade count. | X2, X5 |
| [18991](https://www.mql5.com/en/articles/18991) + [19141](https://www.mql5.com/en/articles/19141) Building a Trading System (Parts 2-3), 2025 | Monte Carlo over risk % for set win rates. Claims 5 % risk is "stable" for an 83 % win, 0.3 RRR system (`md\18991.md:608`). Part 3 works backwards from a profit target to the minimum risk % (`md\19141.md:42`). | SIM (edge assumed known) | The "minimum risk to reach a target" calculator fits the sweep-target talk. The 5 % result is a trap because the edge is assumed, not estimated. | X2, X4 |
| [16925](https://www.mql5.com/en/articles/16925) Self Optimizing EA (Part 4): dynamic position sizing, 2025 | A logistic model adds a second trade when confident. The average loss grew from $81 to $122 (`md\16925.md:688`). GBPUSD M15 2022-2024, same period (`:66`). | BT-IS | Confidence sizing also grows losses. Pair it with the calibration warning (21824:401). | X2 |
| [22338](https://www.mql5.com/en/articles/22338) Wizard (Part 87): volatility-scaled money management, 2026 | Range-scaled lot through a fast Donchian queue, plus an RBF "gatekeeper" (`md\22338.md:38-40`). RBF centres must be trained and validated (`:270`). | BT-IS | Volatility scaling as a plug-in sizer. The extra network adds overfit surface. | X2 |
| [24250](https://www.mql5.com/en/articles/24250) ML Under Constraint (Part 3): de-risking near the target, news-window rule, 2026 | Size shrinks as the phase profit target nears (`md\24250.md:51`). The option analogy is "a motivation, not an argument" (`:59`). News collisions: 0 per simulated year for timing-independent entries, about 1 in 5 for post-release entries (`:531`). Calendars keyed on currency do not reach indices, metals, energy or crypto (`:532`). Loaders are version contracts (`:533`). Timestamps carry a time-zone contract (`:534`). | SIM | Taper size near a sweep or milestone target, on top of the remaining-budget taper (24249, R1). Treat data loaders as versioned contracts. | X2, X3 |
| [17640](https://www.mql5.com/en/articles/17640) Risk Management (Part 5): integrating into an EA, 2026 | Dynamic risk kept the minimum balance near $9,086 but made recovery slower. Better for prop accounts than regular ones (`md\17640.md:1183-1185`). | BT-IS | Dynamic risk trades recovery speed for floor protection. Make the choice explicit per account goal. | X2 |
| [21372](https://www.mql5.com/en/articles/21372) Neuro-Structural Trading Engine (Part I): prop-safe multi-account crypto, 2026 | Crypto CFD risk: one candle can blow through an ATR stop and the daily limit (`md\21372.md:38`). Fixed-dollar cap of $1 per trade, stop rolled in, half closed at 50 % of TP then breakeven (`:172-188`). Stops trading near any prop limit with a margin (`:196`). Compression ratio as a regime test (`:137-146`). | NONE in part I | A fixed money cap per trade suits small accounts and crypto gaps. The "zero downside risk" runner claim is a trap (Part VI). | X2, X3 |
| Martingale and grid group: [5269](https://www.mql5.com/en/articles/5269) (2019), [15067](https://www.mql5.com/en/articles/15067) (2024), [8826](https://www.mql5.com/en/articles/8826) (2021), [20018](https://www.mql5.com/en/articles/20018) (2026), [20449](https://www.mql5.com/en/articles/20449) (2025) | 5269 names the main drawback, a high chance of losing the whole deposit (`md\5269.md:38`). 8826: the last order is 5x the first lot, and the bot stopped working before 2016 for reasons the author cannot explain (`md\8826.md:566-568`). 20018: break-even maths for grids (`md\20018.md:183`). 20449 wraps gold martingale in "multi-layered protection", tested over 2 months (`md\20449.md:52`, `:646`). | BT-IS, short | Keep as failure cases for X4 scenarios: trend runs, gaps, regime age (21833 in pilot). QMX's own rule set should forbid size growth after losses (INFERRED). | X4 |

**Across instruments:** sizing must come from money at the stop (Part II). Crypto and gold need a money cap, because ATR stops get blown through (`md\21372.md:38`). Carry changes the sizing of multi-day FX and metal units (22175). At $500, coarse lot steps make many sizes impossible. 22684's "floor, then skip" rule is the honest answer (`md\22684.md:119`).

## 2. Risk managers and limits at trade, basket, EA and account level

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [24392](https://www.mql5.com/en/articles/24392) Building Your Personal EA (Part 6): portfolio and correlated risk, 2026 | Account-wide or registered-magic scope as an explicit choice (`md\24392.md:106-108`). Net vs gross exposure per currency (`:148`). Never parse symbol names, ask the broker for base and quote (`:290`). Six pre-trade checks, each asking "what would the portfolio look like with this trade" (`:400-409`). Every limit starts at zero (off) (`:198`). Pending orders count (`:282`). Admits a race: two EAs on one tick can both pass (`:736`). State lost on restart (`:738`). | MECH | Every check asks "after this trade". Pending orders count as exposure. The race needs a lock or a single gate (RiskGate, R1). | X2, X3 |
| [21313](https://www.mql5.com/en/articles/21313) Engineering Trading Discipline (Part 2): daily trade limit enforcer, 2026 | Counts confirmed DEAL_ENTRY_IN across the whole account, manual trades and other EAs included, from a set session start (`md\21313.md:51-53`, `:906`). Result: a testable invariant (`:910`). | DEMO (scenario tests) | Write each limit as an invariant with precise definitions of "entry" and "day". | X3 |
| [21995](https://www.mql5.com/en/articles/21995) Discipline (Part 5): account-level risk enforcement, 2026 | A position is valid only with SL, TP, size within budget and RR intact (`md\21995.md:53`). A timer re-checks every open position and restores compliance (`:740-744`). | DEMO | Continuous re-validation of open positions, not only at entry. Catches manual edits or a stop removed by another tool. | X3 |
| [22560](https://www.mql5.com/en/articles/22560) + [23100](https://www.mql5.com/en/articles/23100) Discipline (Parts 6, 8), 2026 | Part 6 unifies whitelist, hours, news and daily count into one engine (`md\22560.md:711`). Part 8 gives setups a lifecycle with confirmation, expiry, freshness, session and lock, through one CanTrade() (`md\23100.md:1590`). | DEMO | One permission gate with reasons. Setups expire. | X1, X3 |
| [22833](https://www.mql5.com/en/articles/22833) Discipline (Part 7): equity governance, 2026 | Four states: NORMAL, CAUTION, RESTRICTED, LOCKDOWN. Driven by drawdown, fast equity drops, recovery threshold, cooldown and stability checks (`md\22833.md:54`, `:103-111`). With governance: net -1,282 became -37, drawdown 19.2 % became 4.1 %, trades 321 became 47 (`:928-936`). | BT-IS, no control | The graded states and gradual recovery are useful. The result is mostly fewer trades on a losing strategy (Part VI). | X3 |
| [24396](https://www.mql5.com/en/articles/24396) + [24397](https://www.mql5.com/en/articles/24397) Prop-Firm Compliance Monitor (Parts 1-2), 2026 | Persistent rules per account login and server (`md\24396.md:40`). Live readings kept separate from stored rules (`:1293`). The day's starting balance is *suggested and confirmed*, then restored on restart (`md\24397.md:42`). Rollover closes the old session before opening the new (`:1876`). The stored value is "a trader-approved reference, not a reconstruction" (`:1878`). | MECH | A confirmed, persisted day baseline. Daily limits measured from a moving balance after a restart are a classic bug (`:38`). | X3, X6 |
| [15294](https://www.mql5.com/en/articles/15294) + [17608](https://www.mql5.com/en/articles/17608) Multi-currency EA (Parts 15, 28), 2025-26 | A "soft finish" mode stops new trades and lets open ones close (`md\15294.md:812`). A closing manager restarts trading automatically after a profit-target lock (`md\17608.md:40-42`). | BT-IS | "Wind down" as a brake state between running and kill. Auto-restart after a sweep needs an operator rule. | X3 |
| [21759](https://www.mql5.com/en/articles/21759) Adaptive risk for liquidity strategies, 2026 | Stops placed mechanically get swept (`md\21759.md:44`). Flipped zones get smaller size (`:733`). | BT-IS | Size by setup quality class. | X2 |

**Across instruments:**
- A day limit needs one "day" across all instruments: one reset hour in server time.
- Crypto runs through weekends, so "daily" has to be defined for it.
- Futures halts and stock closes freeze positions that a daily cut may want to close (INFERRED).
- Margin differs by class. The margin check must be per symbol (`md\24392.md:202`).

## 3. Circuit breakers, kill switches, pauses after losses, cool-downs

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [23315](https://www.mql5.com/en/articles/23315) OrderSend retries and circuit breaker, 2026 | Sorts broker errors into transient and permanent. Retries with exponential backoff on transient errors. Fails fast on permanent ones, which never trip the breaker. Breaker states CLOSED, OPEN, HALF-OPEN, with recovery through controlled probes (`md\23315.md:1319-1321`). Duplicate submissions from a second tick are a real risk event (`:42`). | MECH | A **half-open** brake state: after a cool-down, allow one probe trade at minimum size before full restore. Error taxonomy decides what counts as a strike. | X3 |
| [22615](https://www.mql5.com/en/articles/22615) (+[22532](https://www.mql5.com/en/articles/22532), [22613](https://www.mql5.com/en/articles/22613)) Self-Healing EA (Parts 1, 2, 4), 2026 | Persists trade state in SQLite (`md\22532.md:44`). Restores virtual stops and checks whether they were hit while offline (`md\22613.md:831`). Reconciles broker position, runtime state and stored record. If any disagree, enters Safe Mode and suspends automated management (`md\22615.md:338-343`). | DEMO (scenario tests) | Safe Mode on state disagreement, with no auto-repair. Check "hit while offline" on restart. | X3, X6 |
| [24251](https://www.mql5.com/en/articles/24251) Isolation Forest for execution-quality anomalies, 2026 | Scores each fill's feature vector against the EA's own recent fills. Reacts by pausing entries, widening stops or halting (`md\24251.md:40`). Joint anomalies beat single-feature caps (`:48`). The tester cannot produce real execution anomalies, so a tester P&L test is "close to a null test by construction" (`:832`). | SIM, MECH | An execution-health brake per broker and symbol. Its P&L effect must be measured on demo or live streams. | X3 |
| [1355](https://www.mql5.com/en/articles/1355) A Pause between Trades, 2006 | A shared pause across all EAs through a terminal global variable, with a lock against two EAs racing (`md\1355.md:44`, `:314`). | DEMO | Old but on point: pauses are account-wide resources, and they race. | X3 |
| [23983](https://www.mql5.com/en/articles/23983) Isolation Forest on price bars, 2026 | An anomaly score has no direction and is not a regime meter (`md\23983.md:480`). A veto rate quoted at 3.5 % was wrong because 109 of 143 signals never reached the gate (`:556`). Gate A/B arms see different signal sets, so their totals contradict each other (`:560-568`). | BT-OOS, with nulls | Brake reports must count every refusal by reason (`:556`). Brake value must be measured on a path-independent split (`:570`). | X3, X5 |

Also in this topic, cited elsewhere: 22833 states (topic 2), 23482 change-point cooldown (D), 20449 consecutive-loss and trades-per-window breakers (`md\20449.md:642`).

**Across instruments:** brake triggers should be in the unit's own units (R, trade count, volatility), not raw pips or dollars. Execution anomalies differ per broker and symbol (24251). Index and crypto gaps mean a stop-out can be several R. A breaker counting stops should count R lost, not stops (INFERRED, R2 point 6).

## 4. News, economic calendar, session and time-of-day filters

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [21235](https://www.mql5.com/en/articles/21235) News Filtering (Part 1): pre- and post-news windows, 2026 | Lists what goes wrong at releases: spikes, spread widening, slippage, stop-hunting wicks, prop rules, currency relevance, state loss, no tester mode (`md\21235.md:40-55`). Windows before and after, importance filter, optional close before high impact (`:61-68`). | DEMO | A checklist for the news brake. | X3 |
| [21446](https://www.mql5.com/en/articles/21446) News Filtering (Part 2): suspend SL/TP during releases, 2026 | Removes stops and targets during the window and restores them after, "to prevent premature stop-outs" (`md\21446.md:40-48`). Accepts "temporary exposure during the suspension window" (`:586`). Single-symbol only (`:578`). | DEMO | Trap: a naked position during the most gap-prone minutes (Part VI). The safe version is to flatten before the window or not enter. | X3 |
| [21803](https://www.mql5.com/en/articles/21803) News Filtering (Part 3): surviving restarts, 2026 | Persists the suspension snapshot so a restart mid-window restores the right stops (`md\21803.md:42`, `:597`). | DEMO | Every brake's state must survive restarts. | X3 |
| [22231](https://www.mql5.com/en/articles/22231) News Filtering (Part 4): static data for backtests, 2026 | Calendar queries return little in the tester, so a static CSV of past events makes news logic testable (`md\22231.md:54-56`). This separates news-induced losses from strategy faults (`:1071`). | MECH | A versioned historical event file for X4 and X5. | X4, X5 |
| [22196](https://www.mql5.com/en/articles/22196) Turning news into a reproducible system, 2026 | Six mistakes. "The calendar answers when to expect volatility, not which direction to trade" (`md\22196.md:1081`). HIGH importance is an editor label, not a measured impact: NFP moves 80-150 points, Eurozone PMI 10-30 (`:1093`). Use server time, not local (`:1124`). Do not call the API every tick (`:1196`). | NONE | Event tiers from measured past impact per instrument, not the HIGH label. | X3 |

Also in this topic: 24250 news-window rule (topic 1), session pieces in Part I C (16171, 20037, 4102, 22516).

**Across instruments:**
- FX maps events by currency.
- Index CFDs react to US data and their own cash open.
- Gold reacts to US rates and data.
- Oil reacts to inventory reports.
- Crypto reacts to US macro and to news outside the calendar.
- Stocks react to earnings, which are not in the MQL5 calendar.

The currency key fails outside FX (`md\24250.md:532`). An event-to-instrument impact table is needed (INFERRED).

## 5. Stops and exits

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [24106](https://www.mql5.com/en/articles/24106) Survival analysis for trade exits, 2026 | Treats an open trade as a patient. TP and SL are competing risks, and a trade still open at the time stop is censored, not failed (`md\24106.md:42-44`). Entries are identical in both arms and only the exit changes. Four instruments, holdout only (`:452-470`). The model calibrated everywhere. Survival exits lost more on USDJPY and XAUUSD (`:476-487`, `:509`). "Report every instrument tested" (`:513`). | BT-OOS | A hold-or-close probability per bar. The two-arm, entries-fixed test design for every exit change. Per-instrument thresholds. | X3, X5 |
| [24466](https://www.mql5.com/en/articles/24466) Self-calibrating exit ladder from historical MFE, 2026 | Measures each trade's best excursion in R, persists it, and sets scale-out rungs from recent percentiles (`md\24466.md:55`, `:63`). One file per symbol, or distributions blend (`:653`). Stale samples linger after a regime shift (`:659`). | MECH | A unit's exit ladder learned from its own record, per instrument, with a lookback limit. | X3 |
| [23245](https://www.mql5.com/en/articles/23245) MAE/MFE excursion analyser, 2026 | Rebuilds trades from history and M1 bars. Stops go at the winners' MAE percentile (`md\23245.md:40`, `:413`). Change one level at a time and re-measure (`:407`, `:415`). M1 only approximates tick extremes (`:415`). | BT-IS | Stop width from winners' p90 MAE. Fits R2's "loss rules fast, edge checks slow". | X3 |
| [22855](https://www.mql5.com/en/articles/22855) Trade journal with live MAE, MFE and R-multiple, 2026 | Tracks excursions tick by tick while the trade is open, which history misses (`md\22855.md:38-40`). Monthly review of R distribution and excursion ratios (`:726`). | MECH | The per-trade record that 24466, 23245 and 24106 all consume. | X6 |
| [23716](https://www.mql5.com/en/articles/23716) Partial close engine with R ladders, 2026 | Three common bugs: close volume not rounded to lot step, percentage taken of the remainder instead of entry volume, broken breakeven move (`md\23716.md:40`). Breakeven ignores spread on wide-spread instruments (`:1571`). A near-zero stop makes R meaningless (`:1569`). | MECH | Partial closes from entry volume. Lot-step rounding. Spread-aware breakeven. | X3 |
| [23618](https://www.mql5.com/en/articles/23618) Trailing engine with five methods at once, 2026 | Each position gets the trail that fits why it was opened: fixed, ATR, SAR, percent of profit, swing (`md\23618.md:38-42`). Pip-based profit trail is wrong for indices, oil and metals (`:1546`). Choosing the method is the strategy's job (`:1554`). | MECH | The trail type is part of the unit template, not a global setting. | X1, X3 |
| [18111](https://www.mql5.com/en/articles/18111) Breakeven (Part 2): ATR and RRR modes, 2026 | Fixed-points breakeven is the most aggressive, RRR-based the most passive, ATR in between (`md\18111.md:1178`). RRR breakeven suited strategies with RR ≥ 1:3 (`:1182`). | BT-IS | Breakeven mode per unit style. | X3 |
| [23597](https://www.mql5.com/en/articles/23597) Multi-Pair EA (Part 10): asymmetric stops by pair volatility signature, 2026 | One ATR multiple fails on each pair in its own way (`md\23597.md:46`). Builds a signature from 1,000 bars per pair (`:48`). 2-month test (`:996`). | BT-IS, short | Per-instrument stop profiles. | X3 |
| [22275](https://www.mql5.com/en/articles/22275) ML Blueprint (Part 15): PT and SL from synthetic paths, 2026 | Grid-searching PT/SL on history picks noise (`md\22275.md:52`, `:62`). Fits an O-U process to cost-adjusted trade P&L, states the forecast, and derives PT and SL on 100,000 synthetic paths (`:54`). The SL ceiling comes from account size and concurrency (`:350`). The forecast choice is the key decision (`:360`). | SIM | Exit levels from a fitted process rather than the best backtest cell. The SL ceiling ties exits to account limits. | X3, X5 |
| [17213](https://www.mql5.com/en/articles/17213) Self Optimizing EA (Part 6): stop-out prevention, 2025 | Rejects "widen your stops" because it means varying risk on similar trades (`md\17213.md:46`). Result: still about 60 % losers (`:907`). | BT-IS | The principle that risk per trade stays fixed while the stop moves is sound. | X3 |

Also: 22187 unified stop (topic 1), 21446 suspended stops (topic 4, trap), 22613 virtual stops after restart (topic 3), 24331 basket time stop (topic 1), 21372 fixed-dollar roll (topic 1).

**Across instruments:**
- Exits in R and money travel across instruments. Exits in pips do not (23618).
- Gold and USDJPY behaved differently from EUR and GBP pairs under the same exit model (24106).
- Breakeven offsets must cover spread and commission per instrument (23716, plus 23755 in the 03 survey).

## 6. Running many EAs together

Main entries are in Part I A (23629, 14107, 14478/14549, 23322, 24243, 24202, 23440, 18770, 23763, 15779/16604). Added here:

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [2179](https://www.mql5.com/en/articles/2179) Universal EA (Part 4): portfolio of strategies, 2016 | Loads a portfolio of strategies from XML, with a panel per strategy (`md\2179.md:48`, `:637`). | NONE | An early "unit list as data" design. | X1 |
| [3046](https://www.mql5.com/en/articles/3046) Balance and equity by symbol and magic, 2017 | One profitable and one losing strategy can net to zero. Build curves per strategy (`md\3046.md:66`). Includes MFE and MAE per EA (`:573`). | MECH | Per-unit equity curves are the base of drift checks. | X6 |
| [16233](https://www.mql5.com/en/articles/16233) SQLite dashboard by symbol and magic, 2025 | Trading statistics broken down by EA and symbol (`md\16233.md:57`). | MECH | Same, as a dashboard. | X6 |

Also: 21313 (account-wide trade count), 1355 (shared pause), 24392 (race between EAs), 21115 (agents with a coordination layer), 17745 (portfolio of three ORB units).

**Across instruments:** magic numbers identify units. Symbol names must resolve per broker (23199). When units trade different classes, correlation estimates need aligned calendars (24202:845). Margin is shared across classes, so the account margin check is the binding one (`md\24392.md:54`).

## 7. Detecting strategy degradation live

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [23043](https://www.mql5.com/en/articles/23043) + [23103](https://www.mql5.com/en/articles/23103) CUSUM structural breaks (Parts 1-2), 2026 | Part 1: an industrial quality-control chart on standardised returns, with theory-based h (`md\23043.md:40`). Assumes iid normal returns (`:639`). Part 2: 36 runs on six instruments and three timeframes. The empirical run between alarms averaged 65.7 bars against 338.1 in theory (`md\23103.md:489`). Mostly variance shifts, rarely mean shifts. Median latency at macro events was single-digit bars (`:668-674`). | BT-IS, cross-asset | A fast volatility-regime alarm, calibrated per instrument from its own history. Not an edge-decay test. | X3 |
| [24449](https://www.mql5.com/en/articles/24449) Wasserstein drift on model inputs, 2026 | Mean and standard deviation miss a shape change (unimodal to bimodal) (`md\24449.md:38`). 1D Wasserstein is cheap (`:1458`). The gate cut 234 trades and 11.9 % of the loss, profit factor unchanged at 0.95, "limiting exposure rather than manufacturing alpha" (`:1452`). | BT-IS | Input drift alarm for any model-driven unit, with the same exposure caveat. | X3 |
| [22978](https://www.mql5.com/en/articles/22978) Rolling Sharpe with significance bands, 2026 | A 60-bar Sharpe of 1.2 is not evidence. Its standard error scales with 1/√n (`md\22978.md:38-48`). | MECH | Show uncertainty bands on every live performance number. | X5, X6 |
| [24150](https://www.mql5.com/en/articles/24150) Deflated Sharpe Ratio, 2026 | The best of 56 XAUUSD H1 backtests scored 98.5 % alone and 90.6 % once all variants were counted, below the 95 % bar (`md\24150.md:543`). Missing the bar is not proof of no edge (`:537`). | BT-IS, SIM controls | Count every variant tried when judging a unit. | X5 |
| [23665](https://www.mql5.com/en/articles/23665) Does this entry filter add edge? Block permutation, 2026 | Separates operational effect from selection skill (`md\23665.md:38-40`). The filter improved risk metrics, but the accepted-trade edge was not unusual under placebo selections (`:868`). | BT-IS with placebos | The fixed-count placebo test for any filter or brake. | X5 |
| [24260](https://www.mql5.com/en/articles/24260) Surrogate data testing, 2026 | Shuffling bars is not a valid null for many statistics (`md\24260.md:54-58`). On gold and EURUSD, 2 of 48 window tests cleared, against 2.4 expected by chance (`:701`). | MECH, BT-IS | Choose the null to match the claim. | X5 |
| [23250](https://www.mql5.com/en/articles/23250) Walk-forward efficiency scoring, 2026 | OOS-to-IS Sharpe ratio per window, with guards for sign traps (`md\23250.md:42`, `:539`). The optimiser's pick lost to a fixed 10/50 EMA on mean WFE (`:537`). | BT-OOS | A WFE score per unit as a promotion input. | X5 |
| [24238](https://www.mql5.com/en/articles/24238) ML Blueprint (Part 22): auditing the selection criterion, 2026 | Resolution ratio = spread across candidates ÷ the criterion's own noise. It was 0.49 in the study (`md\24238.md:424`). Search fewer knobs and stop at the noise floor (`:426`). Use log loss, not accuracy (`:418`). | SIM | Before choosing between unit variants, check that the score can tell them apart. | X5 |
| [22578](https://www.mql5.com/en/articles/22578) From best pass to robust plateau, 2026 | Forward optimisation removed configurations with PF above 8 "tailored to the testing period" (`md\22578.md:374`). Pick plateaus, not peaks (`:382`). | BT-OOS | Promote parameter regions, not points. | X5 |
| [24664](https://www.mql5.com/en/articles/24664) Agent-based market simulation to catch overfitting, 2026 | Grows a market from rules (minority game, from El Farol) with no data in it (`md\24664.md:74-76`). A rule that "works" there is overfitted by construction. The false discovery rate is measured over 200 markets (`:1373`). | SIM, MECH | A no-edge synthetic market for X5 controls and X4 scenarios. | X4, X5 |
| [1467](https://www.mql5.com/en/articles/1467) Automated optimisation in real trading, 2007 | Re-optimises daily. Warns not to optimise so long that the EA never trades (`md\1467.md:38`, `:750`). | BT-IS | Shows how old the "self-tuning" idea is. Needs 24238 and 24150 guards. | X5 |
| [17956](https://www.mql5.com/en/articles/17956) Regression gates for performance and trading rules, 2026 | A machine-readable PASS/FAIL gate over profile, unit tests and symbol assertions. Do not promote baselines casually (`md\17956.md:727-729`). | MECH | A release gate for unit templates. | X5 |
| [16957](https://www.mql5.com/en/articles/16957) Robustness testing on EAs, 2025 | Out-of-sample, outliers, slippage simulation (`md\16957.md:377-381`). | NONE | Checklist. | X5 |

Also: 23482 BOCPD (D), 24460 regime age (D), 20946 three break detectors (D), and the control-theory series (Part IV.1).

**Across instruments:** detectors fitted on one class do not transfer as-is. CUSUM false-alarm rates were similar across FX, gold and indices but far from theory (23103). Thin-sample units, such as daily stock units, need longer to reach any verdict (R3 point 1).

## 8. Costs: spread, slippage, commission, swap, demo vs live

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [22998](https://www.mql5.com/en/articles/22998) Measuring broker execution quality, 2026 | Slippage, observed spread, requotes, and **slippage asymmetry** between entries and exits (`md\22998.md:52-55`). It measures the whole path (PC, VPS, network, broker), not the broker alone (`:44`). Execution modes differ (`:63-69`). Probe trades are precise, passive samples approximate (`:77-78`). Keep every sample for median and p95 (`:91`). | DEMO (probe) | A per-broker, per-symbol cost record with median and p95, entry and exit separated. | X6, X3 |
| [23299](https://www.mql5.com/en/articles/23299) Execution cost and slippage sensitivity, 2026 | Break-even cost per deal = average edge (`md\23299.md:74`). Cushion = net profit ÷ total assumed cost. Retention = 1 - 1/cushion (`:78-82`). Example: PF 1.56, cushion 2.49, 40 % of profit lost to realistic costs (`:594-598`). Below 3.0 is flagged (`:598`). Real slippage is not constant (`:606`). | SIM (sample deals) | A cost cushion per unit as a promotion and demotion number. | X5, X3 |
| [23327](https://www.mql5.com/en/articles/23327) Broker Reality Check (Part 1), 2026 | Filling policy, stops level, lot step, hedging, trade mode (`md\23327.md:48-50`). Trade mode not FULL means "don't deploy there" (`:327`). Heavy or asymmetric swap and the triple-swap day (`:329`). | MECH | A broker-conditions audit before a unit goes live on a symbol. | X1, X3 |
| [22372](https://www.mql5.com/en/articles/22372) ML Blueprint (Part 14): transaction cost model, 2026 | Costs as fractional returns, p95 or session-adjusted spread, slippage and commission supplied by the caller (`md\22372.md:900`). | MECH | The cross-instrument cost model (Part II). | X2, X5 |
| [10211](https://www.mql5.com/en/articles/10211) Market math: profit, loss and costs, 2022 | Exact profit and swap formulas. The built-in calculation differs when profit currency ≠ deposit currency (`md\10211.md:515`). | MECH | Conversion accuracy for sizing on crosses. | X2 |

Also: 24562 tick depth, 15330 broker quotes, 22772 tester-relaxed gates, 23355 spread percentile, 24251 execution anomalies (Part I B and E; topic 3), 22175 swap (D).

**Across instruments:**
- FX: spread plus commission, swap.
- Metals: wide spreads at rollover, swap.
- Indices: spread jumps at the cash open, dividends adjust CFDs (not covered in articles read).
- Energy: inventory spikes.
- Crypto: wide spreads, weekend financing.
- Futures: commission per contract, roll cost.
- Stock CFDs: commission and borrow (not covered).

The corpus covers FX and gold well, indices partly (22938 NQ, 23103 DE40/USTEC), and the rest hardly at all.

## 9. Monitoring, logging and dashboards

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [22616](https://www.mql5.com/en/articles/22616) Self-Healing EA (Part 5): recovery dashboard, 2026 | Shows sync status, protection state and Safe Mode events live (`md\22616.md:40-42`, `:393`). | DEMO | Show brake and recovery state, not just P&L. | X6 |
| [22107](https://www.mql5.com/en/articles/22107) to [22449](https://www.mql5.com/en/articles/22449) Trade Analytics System (Parts 1-4), 2026 | EA posts closed trades as JSON to an HTTP API and SQLite, with summary metrics and a web dashboard (`md\22107.md:40`, `md\22449.md:40`). | MECH | Closed-trade events to a store is the QMX pattern already. Nothing new for risk. | X6 |
| [23093](https://www.mql5.com/en/articles/23093) Daily reports by SendMail, 2026 | Once-a-day report with duplicate prevention (`md\23093.md:444-447`). | MECH | Daily digest for the operator. | X6 |
| [15346](https://www.mql5.com/en/articles/15346) Push notifications service, 2025 | A terminal service that builds reports and pushes them (`md\15346.md:53`). | MECH | Alerts from a service, separate from trading EAs. | X6 |
| [19649](https://www.mql5.com/en/articles/19649) Backend operations monitor, 2025 | A separate log space for the EA, away from the crowded Experts tab (`md\19649.md:526`). | MECH | Per-unit logs. | X6 |

Monitoring content worth more than these: 23983's rule that every refusal is counted by reason with the right denominator (`md\23983.md:556`), 22998's p95 cost samples, 22855's live MAE/MFE, 3046's per-unit curves, 24392's per-currency snapshot with zero-net currencies skipped (`md\24392.md:592`), and R3's alarm-fatigue numbers.

**Across instruments:** dashboards that show pips mislead across classes. Show R and account money.

## 10. LLM and agent articles

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [24265](https://www.mql5.com/en/articles/24265) Inside MetaEditor's AI Assistant, 2026 | Build 6060 exposes MetaEditor and the terminal over MCP. The agent writes, compiles, repairs and backtests (`md\24265.md:38-40`). Tool content must never give orders (`:551`). Four routes bring in untrusted text, including third-party source files (`:566-575`). Leave Trading on manual confirmation or disabled, "never on Enabled on a live account" (`:579`). Per-task grants, read tool cards, demo first, local models keep data local (`:583-587`). The tester returns no report through a tool (`:600`). | DEMO (workflow) | Matches QMX's rule that agents never touch money. Use the four-route list of untrusted input in the X7 threat notes. | X7 |
| [21905](https://www.mql5.com/en/articles/21905) Connecting AI agents to MT5 via MCP, 2026 | A Python MCP server for MT5. Windows-only, single-threaded (`md\21905.md:577`). Proposes executing Telegram channel signals automatically (`:579`). | NONE | Trap: an agent that executes signals from chat channels. See Part VI. | X7 |
| [24527](https://www.mql5.com/en/articles/24527) Controlling MT5 from Telegram with Hermes and MCP, 2026 | Bounded MCP operations from approved messages. Keep trading tools disabled. Exact settings in every test prompt. Human confirmation before source edits or trades (`md\24527.md:570-572`). | NONE | Reproducible agent test requests: every input named. | X7 |
| [19345](https://www.mql5.com/en/articles/19345) GPT-style trading robot, 2026 | 48 trades, 87 % profitable, Sharpe 1.73 (`md\19345.md:611`). | BT-IS, thin | Trap of small samples. | X5 |
| [20071](https://www.mql5.com/en/articles/20071) Team of AI agents with profit-based rotation, 2026 | Seven "personalities". Capital multipliers reshuffled every 24 hours by recent profit (`md\20071.md:99`, `:303`). No test numbers. Claims "functional equivalent of fear" (`:453`). | NONE | Trap. Daily rotation to the recent winner is the adaptive allocation R3 warns about. | X2 |

Also: 22495, 17986, 18685, 20329, 21115 (Part I F), 20354 ("DO NOT use this script for trading on a live account", `md\20354.md:584`).

**Across instruments:** an LLM's prior is textbook-generic. 20329 shows it lacks per-instrument behaviour (`md\20329.md:44`). Any agent proposal should carry the instrument class and the evidence it used (INFERRED).

## 11. Anything else that bears on risk and sizing

| Article | Does | Evidence | [idea] for QMX | Layer |
|---|---|---|---|---|
| [23199](https://www.mql5.com/en/articles/23199) Broker-agnostic symbol resolution, 2026 | Logical names resolved and validated per broker. Unresolved names logged (`md\23199.md:51-53`, `:1625`). | MECH | The unit references a logical instrument. | X1 |
| [23388](https://www.mql5.com/en/articles/23388) Symbol metadata and trading hours cache, 2026 | Cache static fields. Tick value drifts on crosses. IsMarketOpen expects server time (`md\23388.md:925`). | MECH | Instrument metadata service with refresh rules. | X1 |
| [802](https://www.mql5.com/en/articles/802) Continuous futures contracts, 2014 | Splices expired contracts and deals with overlapping dates and splice methods (`md\802.md:38`). | MECH | Futures history for tests. | X4 |

---

# Part IV. Borrowed logic from other fields

Each block gives the field, the analogy, the method it brings, how the series builds it part by part, the evidence, and what it could become in QMX risk and sizing.

### IV.1 Control theory: feedback controllers and system identification (Self Optimizing EAs, Parts 4, 6, 13-17, 2025)

- **Analogy:** a deployed strategy is a plant. A feedback controller watches its outputs and corrects its behaviour, as engineers do for aircraft wings where turbulence has no formula (`md\19132.md:44`, `:84`).
- **Method:** collect daily "snapshots" (prices, balance, equity, indicators, position state). Fit a linear model of how snapshots evolve. Grant or refuse "permission to trade" from the predicted next state (`md\19132.md:64-70`, `:376-403`).
- **How the series builds:**
  - Part 4 sizes up when a model is confident, and losses grew (`md\16925.md:688`).
  - Part 6 refuses to widen stops because that varies risk (`md\17213.md:46`).
  - Part 13 introduces the closed loop with a 90-day observation period. Profit $134 to $245, Sharpe 0.34 to 0.68, fewer trades, gross loss down (`md\19132.md:64`, `:76-80`).
  - Part 14 treats data transforms as controller knobs (`md\19382.md:40-44`).
  - Part 15 identifies the system from data, with a forward split (`md\19891.md:42-48`). The benchmark lost $559 over 78 trades (`:369`).
  - Part 16 controls a strategy that is itself a statistical model. The controller predicted the final balance within 10 cents (`md\20023.md:851`).
  - Part 17 ensembles a rule strategy and a model on shared indicators, trading only when both agree. Two unprofitable systems made one profitable one (`md\20238.md:42`).
- **Evidence:** BT-IS mostly, Part 15 has a forward split. The permission gate cuts trades, so the exposure effect is not separated from skill (INFERRED, see Part VI trap 1).
- **[idea] in QMX:** a per-unit feedback loop where the unit's own record (R, drawdown, cost cushion, regime label) predicts next-period state and sets a size multiplier or permission. It has to beat a random gate with the same trade count (23482's design). It needs an observation period before acting, which matches R3's "minimum events before a signal".

### IV.2 Behavioural psychology turned into constraint engineering (Engineering Trading Discipline, Parts 1-8, 2026)

- **Analogy:** human discipline fails under pressure, so put it in code as constraints rather than rules (`md\21273.md:48-52`).
- **How the series builds:**
  - Part 1: rules into constraints.
  - Part 2: an account-wide daily entry cap as an invariant (`md\21313.md:910`).
  - Part 3: symbol whitelist.
  - Part 4: trading hours and news disabling.
  - Part 5: continuous re-validation of open positions (`md\21995.md:740`).
  - Part 6: one discipline engine (`md\22560.md:711`).
  - Part 7: equity governance states with cooldown and stability checks (`md\22833.md:54`, `:103-111`).
  - Part 8: a setup lifecycle and authorisation layer (`md\23100.md:1590`).
- **Evidence:** DEMO scenario tests. Part 7's backtest has no control.
- **[idea] in QMX:** the series is a ready catalogue of brakes as invariants. Each brake gets a precise definition (what is an entry, what is a day), a scope (account-wide, including manual trades), and a state that survives restarts.

### IV.3 Biology and medicine "self-healing", plus software reliability (Self-Healing EA, Parts 1-5, 2026; OrderSend circuit breaker, 2026)

- **Analogy:** an EA that recovers after a restart like an organism heals. Electrical and software circuit breakers that open on repeated faults and probe before closing.
- **How the series builds:**
  - Part 1: SQLite persistence (`md\22532.md:44`).
  - Part 2: virtual stops restored, and checked whether they were hit while offline (`md\22613.md:831`).
  - Part 3: restart-aware breakeven and trailing (22614, covered in 03).
  - Part 4: reconciliation and Safe Mode when the records disagree (`md\22615.md:338-343`).
  - Part 5: dashboard (`md\22616.md:393`).
  - Separately, 23315 adds an error taxonomy, exponential backoff and CLOSED/OPEN/HALF-OPEN states (`md\23315.md:1319-1321`).
- **Evidence:** DEMO, MECH.
- **[idea] in QMX:** a brake state machine with a half-open probe (one minimum-size trade) before full restore. This sits between R1's restore state (15085) and R3's recloser pattern. Safe Mode means "manage existing, open nothing" whenever stored and broker state disagree.

### IV.4 Industrial quality control: CUSUM (Parts 1-2, 2026; stat-arb Part 10, 2026)

- **Analogy:** a factory control chart that adds up small deviations until a threshold.
- **How the series builds:**
  - Part 1 derives thresholds from theory and states the iid normal assumption (`md\23043.md:639`).
  - Part 2 tests it on six instruments: about 5x more alarms than theory, mostly variance shifts, fast at macro events (`md\23103.md:674`).
  - 20946 sets CUSUM beside Chow and rolling eigenvectors as early warning, confirmation and update tools (`md\20946.md:339-345`).
- **Evidence:** BT-IS, cross-asset.
- **[idea] in QMX:** a price-side volatility alarm with thresholds fitted per instrument from history. It is different from R2's CUSUM on the unit's trades, which needs about 240 trades to flag decay. Two speeds, two jobs.

### IV.5 Medical statistics: survival analysis with competing risks (24106, 2026)

- **Analogy:** a live trade is a patient under observation. Take-profit and stop-loss compete. A trade still open at the time stop is censored (`md\24106.md:42-44`).
- **Method:** a person-period table and cause-specific hazards, fitted natively. Cumulative incidence gives a hold-or-close decision.
- **Evidence:** BT-OOS, four instruments, honest mixed result (`md\24106.md:476-513`).
- **[idea] in QMX:** an exit layer that reads the trade's live state (MFE, MAE, distance to barriers, volatility) and the chance of the target before the stop. Thresholds per instrument. The test design (entries fixed, only the exit varies, report all instruments) goes to X5.

### IV.6 Immunology: dendritic cells and danger theory (20479, 20430, 2026); anomaly isolation (24251, 23983)

- **Analogy:** dendritic cells collect danger and safe signals over time and decide only after they have gathered enough. "The cell does not make instantaneous decisions," which makes it robust to noise (`md\20479.md:47`). Signals come as PAMP (clear danger), danger, safe, and inflammation, which amplifies the others (`:55-58`). In the corpus this drives an *optimiser*, not a risk tool.
- **Related:** isolation forests flag what is "few and different" (`md\23983.md:67`). They are used on fills (`md\24251.md:40`) and on bars (23983).
- **Evidence:** optimiser benchmarks (20479), SIM and MECH (24251), BT-OOS with nulls (23983).
- **[idea] in QMX:**
  - An "immune" brake that integrates several weak danger signals (spread percentile, execution anomaly, change-point probability, loss streak in R) over a window before acting.
  - Clear-danger signals act at once: broker disconnect, state mismatch.
  - An inflammation term raises sensitivity during news windows.
  - This answers R3's alarm-fatigue finding (85-99 % of alarms needing no action) by deciding on accumulated evidence (INFERRED).

### IV.7 Physics and geometry: random matrices, curvature, optimal transport, chaos

- **Random matrix theory** (24243): separate signal eigenvalues from noise with Marchenko-Pastur. Steadier weights, no P&L claim (`md\24243.md:961-963`).
- **Riemannian curvature** (24202): read whether cluster structure exists, independent of correlation level. Ship nulls beside every reading (`md\24202.md:66`, `:851`).
- **Optimal transport** (24449): Wasserstein distance catches shape drift that mean and standard deviation miss (`md\24449.md:38`).
- **Chaos theory** (15332, 15445, Parts 1-2): Lyapunov exponents, recurrence, Takens embedding. "Not the Holy Grail" and results vary by instrument (`md\15445.md:1243-1247`).
- **Ornstein-Uhlenbeck process** (22275): a physics diffusion model used to derive exits on synthetic paths (`md\22275.md:54`).
- **Evidence:** MECH and SIM mainly. Chaos is BT-IS.
- **[idea] in QMX:** clean correlation inputs (RMT), a "structure has merged" alarm (curvature), an input drift alarm (Wasserstein), exits from a fitted process (O-U). Chaos measures do not earn a place yet.

### IV.8 Information theory: entropy and compression

- **Compression** (23714 Lempel-Ziv; 21372 zlib ratio): structured data compresses, random data does not (`md\23714.md:54`, `md\21372.md:137`). 23714 shows against a random null that matched historical shapes are *not* predictive (`md\23714.md:523`).
- **Shannon entropy on ticks** (22220): real-time disorder as a volatility input (`md\22220.md:57`).
- **Evidence:** MECH with honest nulls (23714). BT-IS or NONE for the others.
- **[idea] in QMX:** an "efficiency" reading as a regime feature at most. 23714 is the best example of reporting a negative result.

### IV.9 Signal processing: Ehlers DSP (Parts 1-2, 2026)

- **Analogy:** price is a signal made of noise, a cycle and a trend (`md\23444.md:49`).
- **How the series builds:** Part 1 builds the filter library (23149). Part 2 measures the dominant cycle with a Hilbert transform, drives MAMA from the phase, and switches between trend and cycle playbooks (`md\23444.md:53`, `:671-674`).
- **Evidence:** BT-IS. The author asks for multi-instrument and walk-forward tests (`:676`).
- **[idea] in QMX:** a regime label for unit placement, not a sizer.

### IV.10 Evolution and ecology: rotation, extinction, agent-based markets

- **Natural selection of agents** (20071): capital flows daily to recent winners (`md\20071.md:99`, `:303`). No test. ETARE (16971, pilot) culls weak strategies.
- **Agent-based market from the El Farol bar problem** (24664): a market with no edge in it, used to measure the false discovery rate of an optimiser over 200 markets (`md\24664.md:76`, `:1373`).
- **[idea] in QMX:** do not move capital daily to recent winners. R3's adaptive-randomisation result warns against it. Do use agent-based markets as a null for X5.

### IV.11 Finance theory analogies: options and portfolios

- **Option analogy for de-risking** (24250): an account near its target is like a deep in-the-money option, where little upside remains for a lot of downside. The author calls it "a motivation, not an argument" (`md\24250.md:59`).
- **Variance risk premium** (23734): implied against realised volatility, from the options literature (`md\23734.md:64`).
- **[idea] in QMX:** a taper near sweep targets. Forward-looking volatility for sizing.

### IV.12 Econometrics of high-frequency data (Market Microstructure, Parts 1-8, 2026; ACD 24742)

- **How the series builds:**
  - Part 1: guarded maths for fat tails at the NQ open (`md\22263.md:46-48`).
  - Parts 2-4: long memory and volatility persistence.
  - Part 5: noise decomposition with practical thresholds (`md\22938.md:484-494`).
  - Part 6: order flow and VPIN approximation (`md\22939.md:44`).
  - Part 7: six regime labels by priority (`md\22940.md:78-87`).
  - Part 8: per-bar micro-trend score with regime-adaptive thresholds (`md\23372.md:44`).
  - 24742 brings Engle-Russell duration models (`md\24742.md:42`).
- **Evidence:** BT-IS on 514-602 NQ sessions, BT-OOS for ACD.
- **[idea] in QMX:** a stress-aware size multiplier and a "Stressed overrides everything" priority rule for session brakes.

---

# Part V. Ideas that could combine

Each line is one mix and what it would do. "R1-R3" refers to the earlier research files.

1. **Exposure ledger:** 24392 currency legs (FX) + 23322 adaptive covariance (non-FX) + 24243 denoising + 24202 curvature alarm. One account-level exposure view that is exact where it can be and cleaned where it cannot. It also raises an alarm when diversification collapses.
2. **Risk-as-output accelerator:** 24331 implied-risk caps per leg and per basket + 22187 unified-stop condition + 22684 book-occupancy gate. Units may add to winners only when locked profit exceeds the new risk, committed risk is re-read from broker stops, and the book is not crowded.
3. **Brake test protocol (X5):** 23482 random-timed control at matched frequency + 23665 fixed-count placebo + 23983 path-independent forward split and denominator rule. Every new brake or filter must beat chance at the same activity level before anyone believes it.
4. **Two-speed drift:** 23103 price-side CUSUM (fast, per-instrument thresholds) + R2's trade-side CUSUM/SPRT (slow, hundreds of trades) + R3's Basel green/yellow/red zones. A volatility break cuts size at once. An edge verdict waits for evidence.
5. **Restore ladder:** 23315 half-open probe + R1's 15085 restore state + 22833 cooldown and stability checks + R3's recloser "retry a few times, then lock out". After a brake: cool-down, one probe trade at minimum size, then stepwise restore, with lockout after repeated failures.
6. **When state is uncertain:** 22615 Safe Mode (manage, do not open) + RiskGate's reject-all when the oracle is offline (R1) + 23629 degraded mode as the counter-example. Uncertainty blocks new risk and never falls back to default sizing.
7. **Live cost monitor:** 22998 p95 and asymmetric slippage + 23355 spread percentile + 24251 execution anomaly + 23299 cushion. Measured costs feed each unit's cushion. A cushion under a set multiple demotes the unit.
8. **Backtest validity stamp:** 24562 real-tick share + 15330 quote-server sensitivity + 15360 main-symbol sensitivity + 22772 tester-relaxed-gate warning. Every test result carries the conditions it ran under, so a scalper result on generated ticks cannot be promoted.
9. **Exit calibration pipeline:** 22855 live MAE/MFE journal → 23245 stop percentile → 24466 MFE ladder → 24106 hazard hold-or-close → 22275 O-U derived targets. Exit settings per unit and instrument, all learned from the unit's own record and tested with 24106's entries-fixed design.
10. **Sweep-aware taper:** 24250 de-risk near the target + 24249 remaining-budget taper (R1) + R2's Topstep payout reset. Size shrinks as a unit nears its sweep target and the cushion resets after a sweep.
11. **Concurrency-aware sizing for many scalpers:** 21824 averaging over active bets + 24331 basket caps + 23629 budget broadcast. Many units firing the same way at once get smaller each, not a stacked total.
12. **Forward-looking stress multiplier:** 23734 implied/realised ratio + 24742 activity gauge + 22938 spread percentiles + 22940 regime labels. Size follows what the market expects and how stressed it is now, not only last month's ATR.
13. **Controller with a fair test:** IV.1 permission controller + 22274's "it was exposure, not skill" lesson + 23482's random control. A self-tuning size loop is only kept if it beats a random gate with the same trade count.
14. **Trade-rate-scaled breakers:** 21313 account-wide entry counting + R2's finding that a two-loss breaker fires on 79 % of scalper days + 20449's sliding-window trade count. Loss-streak and frequency brakes measured in units of the unit's own expected rate.
15. **Agent proposal channel (X7):** 24265 data-not-instructions and manual trading gate + 22495 KEY:VALUE schema + 24527 every-input-named test requests. Agents produce parseable proposals with full settings. Parse failure means no proposal, and nothing reaches money without the operator.
16. **Session-open units:** 23226 relative-volume "in play" gate + 17745 family sizing + 18821 (03 survey) rollover spreads + 16171 DST clock. Open-range units trade only on active days, sized as a family, on a correct clock.
17. **Regime age:** 24460 HSMM remaining duration + 23482 run length + 21833 cycle age (pilot). New adds taper as a regime ages, and averaging units restart cycles.
18. **Day boundary contract:** 24397 confirmed and persisted baseline + 21313 session start + 21803 restart-safe news state + 16171 server-time DST. One definition of "the day" for every limit, which survives restarts.
19. **Immune brake:** IV.6 danger accumulation + 24251 + 23983 + 22940 Stressed label + 21235 news windows as inflammation. Fewer false alarms than single-threshold brakes (R3 alarm fatigue), with instant action reserved for clear-danger events.
20. **Instrument risk record:** Part II pieces (22187 money at stop, 22372 return-unit costs, 23199 resolution, 23388 metadata, 23597 volatility signature, 802 futures roll). One record per unit, instrument and broker that every sizer and brake reads.
21. **Group selection with honesty:** 14478 cluster-based group selection + 24150 deflated Sharpe + 24238 resolution ratio + 22578 plateaus. Choosing which units run together counts every tried combination and picks stable regions.

---

# Part VI. Traps the articles show

1. **Trading less looks like risk control.** On a losing strategy, any filter that cuts trades cuts losses and drawdown:
   - 22833: 321 trades became 47, drawdown 19.2 % became 4.1 %, no control (`md\22833.md:928-936`).
   - 22274: honest about it. The classifier was below chance and the 93 % drawdown cut came from exposure (`md\22274.md:240`).
   - 24449: profit factor unchanged (`md\24449.md:1452`).
   - 19132's gate also cut trades (`md\19132.md:76`).
   - The fix: a random control at the same rate (`md\23482.md:598`) or fixed-count placebos (23665).
2. **Gate tests that cannot answer the question.** Arms that trade less see more signals, so totals are not comparable (`md\23983.md:568`). A veto rate counted against signals that never reached the gate (`md\23983.md:556`). A threshold on the wrong scale that never bites (`md\24202.md:767`).
3. **The tester checks a different gate from the one that runs live.** 22772 loosens its spread, gap and velocity gates in the tester (`md\22772.md:131-134`, `:711`).
4. **"100 % real ticks" is not real ticks.** Most minutes can be generated (`md\24562.md:40`).
5. **Signals built on tick volume or broker-specific quotes do not travel.** The account drained on another broker (`md\15330.md:62`). Results depend even on the main tester symbol (`md\15360.md:718`).
6. **Theory-calibrated alarms.** CUSUM fired about 5x more than its formula (`md\23103.md:489`). Thresholds must be fitted per instrument (`md\22938.md:484`).
7. **"Risk-free" adds and runners.**
   - The pyramid's "worst case is profit" (`md\22187.md:48`, `:123`) and the "zero downside" runner after breakeven (`md\21372.md:188`) both assume stops fill at their price.
   - Gaps, weekend crypto moves and news slippage break that (INFERRED).
   - 22187 also needs every stop change confirmed (`:90`).
8. **Removing stops during news to avoid stop-outs.** It leaves positions naked in the most gap-prone minutes (`md\21446.md:40-48`, `:586`).
9. **Reading the calendar as a direction signal.** It tells when, not which way (`md\22196.md:1051-1081`). HIGH importance is an editorial label (`:1093`).
10. **Martingale with protection layers is still martingale.**
    - 20449 on gold over 2 months (`md\20449.md:52`, `:646`).
    - 8826's 5x last lot stopped working pre-2016 (`md\8826.md:566-568`).
    - Averaging without three caps is "a martingale with better manners" (`md\24331.md:651`).
11. **Optimisers concentrate.** VaR and Markowitz put 51 % in one pair and called PF 1.03 a real-market success (`md\15779.md:205`, `:318-341`).
12. **Best-pass selection.**
    - PF above 8 configurations were tailored to the period (`md\22578.md:374`).
    - The best of 56 fell below the bar once all variants were counted (`md\24150.md:543`).
    - Selection criteria noisier than the differences they rank (`md\24238.md:424`).
    - Grid-searching PT/SL picks noise (`md\22275.md:62`).
13. **Confidence sizing grows losses too.** The average loss rose from $81 to $122 (`md\16925.md:688`). Miscalibrated probabilities flow straight into size (`md\21824.md:401`).
14. **Monte Carlo with an assumed edge justifies high risk.** "5 % risk stable" for an assumed 83 % win rate (`md\18991.md:608`). The edge is an estimate (24147 in R1).
15. **One exit or stop rule for all instruments.**
    - The survival exit lost on USDJPY and XAUUSD (`md\24106.md:509`).
    - One ATR multiple fails per pair (`md\23597.md:46`).
    - Pip-based trails mislead on indices, oil and metals (`md\23618.md:1546`).
16. **Fixed lots that are not re-sized.** The pyramid's lots are "not automatically adjusted for account balance" (`md\22187.md:1145`).
17. **Sizing cannot fix a negative edge.** At 1 % risk per trade the survival test still reached 70 % drawdown on EURUSD (`md\24106.md:478`).
18. **Degraded mode that keeps trading.** Defaults replace the missing controller (`md\23629.md:128`). Compare RiskGate's reject-all (R1).
19. **Memory-only risk state.** Basket MAE, portfolio state and news suspensions are lost on restart (`md\24331.md:655`, `md\24392.md:738`, `md\21803.md:40`).
20. **Two EAs pass one limit on the same tick.** A shared check without a lock races (`md\24392.md:736`).
21. **Static correlation windows and noisy matrices.** A dead hedge still looks like a hedge (`md\23322.md:40`). With T not much larger than N, the matrix is mostly noise (`md\24243.md:40`).
22. **Tiny samples and short tests.**
    - "100 % probability" over 50 days (`md\1575.md:349`).
    - 48 trades at 87 % (`md\19345.md:611`).
    - 2-month M15 tests (`md\22772.md:1433`, `md\23597.md:996`).
    - A 3-month forward period (`md\14549.md:349`).
23. **Agent hype and agent overreach.**
    - Anthropomorphic claims with no test (`md\20071.md:453`).
    - Executing chat-channel signals through an agent (`md\21905.md:579`).
    - "Start trading with your AI assistant" (`md\21905.md:581`), against the platform's own advice to keep trading on manual (`md\24265.md:579`).
24. **Daily rotation of capital to recent winners.** 20071 reshuffles every 24 hours (`md\20071.md:303`). R3's adaptive-randomisation evidence says this often favours the worse arm.
25. **Regime-break detectors read as direction.** BOCPD "measures change, not direction" (`md\23482.md:721`). Anomaly scores carry no direction (`md\23983.md:480`).

---

# Part VII. Coverage and limits

**Reviewed and kept, by topic** (an article counts under its main topic):

| Section | Reviewed | Kept (full row) |
|---|---|---|
| A portfolio across EAs | 16 | 11 |
| B scalping | 10 | 5 (+3 weak noted) |
| C intraday | 11 | 8 |
| D macro and regime | 11 | 6 (+4 weak noted) |
| E microstructure | 9 | 5 |
| F agents for reading | 7 | 5 |
| 1 sizing | 19 | 13 (+5 martingale as one row) |
| 2 risk managers and limits | 15 | 11 |
| 3 brakes | 8 | 5 |
| 4 news and calendar | 7 | 5 |
| 5 exits | 13 | 10 |
| 6 many EAs (added) | 4 | 3 |
| 7 degradation | 20 | 13 |
| 8 costs | 9 | 5 |
| 9 monitoring | 9 | 5 |
| 10 LLM and agents | 8 | 5 |
| 11 other | 4 | 3 |
| IV borrowed logic (extra) | 9 | 9 (cited in IV) |
| **Total distinct** | **about 150** | **about 110** |

**Not read in full, worth a look in the expansion:**
- 22047 (bet sizing in MQL5)
- 22063 (imbalance bars)
- 15748 (order book)
- 18303 (CFTC with AI)
- 16820, 16985, 17508 (Risk Management Parts 1, 2, 4)
- 11850 (prop-firm lessons)
- 4233 (reducing trader risk)
- 14412 and 14813 (non-stationarity tests)
- 13162 (Monte Carlo permutation)
- 3279 (custom walk-forward)
- 23149 (DSP Part 1)
- 15332 (chaos Part 1)
- 15541 and 17546 (game theory)
- 16979 (biological neuron)
- 22783 (regime-adaptive mean reversion)
- 24161 (regime-adaptive EA)
- 23137 (bagging regimes)
- 1446 and 1481 (martingale explainers)
- 7219 (grid diversification)
- 17282 (capital management with home accounting)

**Limits:**
- Every result here is the author's own. None is a real-money track record. Most are in-sample.
- Line numbers are from the local copies, fetched September-October 2026.
- Formulas rendered as images are invisible in the Markdown copies.
- Instrument coverage is FX-heavy, with gold and US indices next. Energy, crypto, futures and stocks appear only in a handful of articles (21372 crypto, 23226 stocks, 802 futures, 17745/22938 indices). Energy has no risk article among those read.
- 06 pilot section 9 also applies: one model coded everything here, with no second coder.
