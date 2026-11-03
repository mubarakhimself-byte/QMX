# Unit idea bank: A3 (structure, regimes, news, scenarios)

Trading signals and market readings found while dissecting the A3 cluster. They are seeds for units or for readings QMX would need to support units, not risk components, and they are not ranked. Paths are relative to `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. "MIS reading" means a new reading the MIS would publish; "QML block" means a statistic or signal block a unit could embed.

## Scalping and order flow

### U-A3-01. Multi-level order-flow imbalance (MLOFI)
- **Source:** `research/R4-alphaxiv/chat-27-E-microstructure.md:65-77`; Cont, Kukanov, Stoikov 2014 (https://www.alphaxiv.org/abs/1011.6402); Xu, Gould, Howison 2019 (https://www.alphaxiv.org/abs/1907.06230); `research/R6-alphaxiv-papers/T-03-macro-and-microstructure.md:78-93`.
- **Signal:** signed queue changes at the first M book levels (adds, executions, cancels) as a vector; mid change is about linear in OFI with slope 1 / depth.
- **Fits:** scalper, seconds to 1m; futures, crypto exchange books, stocks. Not spot FX or CFDs (broker quotes are not a book).
- **Data:** timestamped L2 updates from the venue the unit trades; depth per level.
- **Needs:** a QML block for OFI and MLOFI; an MIS depth reading per venue.
- **Evidence:** author backtest. Contemporaneous R^2 about 65 % (OFI) vs 32 % (trade imbalance); 10-level ridge cut out-of-sample RMSE 15-74 % on six Nasdaq stocks. Explains price change; not shown to forecast it net of costs.

### U-A3-02. Event-conditioned short-lived impact (veto passive fills)
- **Source:** `research/R4-alphaxiv/chat-27-E-microstructure.md:79-89`; Eisler, Bouchaud, Kockelkoren 2010 (https://www.alphaxiv.org/abs/0904.0900).
- **Signal:** recent order-book event flow (market orders, limit adds, cancels) predicts a short move; correlations last about 10-100 events (about 10 seconds).
- **Fits:** maker scalpers on central books.
- **Data:** event-level best quotes, queue sizes, trades, cancels.
- **Needs:** QML block; sub-second data.
- **Evidence:** author backtest (stocks).

### U-A3-03. Maker reversal model (post when the imbalance signal is likely wrong)
- **Source:** `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:93-115`; Albers et al. 2025 (https://www.alphaxiv.org/abs/2502.18625).
- **Signal:** a classifier (173 features) on when a top-of-book imbalance signal will reverse; post passive orders then.
- **Fits:** crypto perpetual market making, sub-second.
- **Data:** L2 book, queue position, fills.
- **Needs:** QML block; co-located speed the source says is required.
- **Evidence:** live (minimum-size orders, one week). Round trip -0.44 bp to +0.71 bp net. Probably out of reach for QMX latency [judgment].

### U-A3-04. Crypto 15-minute reversal after taker-driven moves
- **Source:** `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:75-91`; Kitron, Wengrowicz 2026 (https://www.alphaxiv.org/abs/2608.21888).
- **Signal:** the sign of the next 15-minute bar reverses, mostly after moves pushed by aggressive taker flow.
- **Fits:** crypto spot and perps, 15m, maker orders only; metals ETFs inherit their metal's behaviour.
- **Data:** trades with taker side; exact fee schedule.
- **Needs:** QML block for taker-flow-conditioned reversal.
- **Evidence:** author backtest, 90 % of 183 pairs significant, frozen holdout; gross about 1.3 bp vs 5 bp cheapest round trip, so inside costs at retail fees.

### U-A3-05. Quarter-hour order imbalance predicts 4-12 hours ahead
- **Source:** `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:117-133`; https://www.alphaxiv.org/abs/2607.09426.
- **Signal:** order imbalance in the bursts at quarter-hour marks; the first 10 seconds after each quarter hour are predictable (out-of-sample R^2 3.37 %, AUC 0.60) but worth about 0.5 bp.
- **Fits:** crypto perps; intraday swing horizon for the 4-12 hour signal.
- **Data:** 10-second trade bins with signed volume.
- **Needs:** MIS reading of quarter-hour imbalance.
- **Evidence:** author backtest.

### U-A3-06. Auction-market order-flow features (CVD slope, tape velocity, volume-area position)
- **Source:** `research/R4-alphaxiv/chat-28-F-agents-macro-micro-news.md:20,33,194`; ViperQ (https://arxiv.org/abs/2609.13825).
- **Signal:** cumulative volume delta slope and divergence, tape velocity, position in the volume area, imbalance, fed to an RL policy.
- **Fits:** stocks and futures intraday scalper filter.
- **Data:** trades with side, volume profile.
- **Needs:** QML blocks; real volume.
- **Evidence:** author backtest on TSLA and NVDA; large returns with drawdowns of -27.5 % and -47.8 %.

### U-A3-07. Session order-flow regime labels as direction (Informed, Trending, Mean-Reverting)
- **Source:** `research/R5-mql5-corpus-ideas.md:125` (MQL5 22940, rules at `md/22940.md:50-95`); `:146` (22938 imbalance thresholds).
- **Signal:** composite directional score: follow flow in Trending and Informed sessions, fade it in Mean-Reverting ones; order imbalance above p90 or below p10 as alignment.
- **Fits:** index futures M1 intraday (NQ in the source).
- **Data:** M1 bars with VPIN approximation, ARFIMA d, multifractal width, noise ratio.
- **Needs:** MIS session-regime reading; QML blocks.
- **Evidence:** author backtest, in-sample, 602 sessions.

### U-A3-08. Regimes in the order flow (duration-aware changepoints)
- **Source:** `research/R6-alphaxiv-papers/T-03-macro-and-microstructure.md:55-74`; https://www.alphaxiv.org/abs/2609.07989.
- **Signal:** BOCPD with log-normal regime durations on signed volume as a regime filter for a scalper.
- **Fits:** stocks and futures, volume clock.
- **Data:** signed volume in volume buckets.
- **Needs:** QML block; volume clock in the MIS (`time_base: volume` exists in the reading record).
- **Evidence:** author backtest (internship report, two stocks).

## Intraday and session opens

### U-A3-09. Opening-range breakout on markets "in play"
- **Source:** `research/R5-mql5-corpus-ideas.md:100-101` (MQL5 17745, 23226); `research/R2-trader-practice-windows-drift-isolation-breadth.md:61` (R37:72); `grounding/G7-unit-inputs-qmb-mis-instruments.md:159`.
- **Signal:** ORB taken only when relative volume at the open is unusual; three ORB variants combined at about 0.3 monthly correlation.
- **Fits:** ORB intraday; stocks and index futures first; FX and gold opens with tick rate as the stand-in.
- **Data:** volume by minute with a 20-day median; cash-open calendars.
- **Needs:** an RVOL MIS reading (today a dictionary entry only, blocked until bars carry volume and time of day).
- **Evidence:** author backtest (cited paper: top 20 net Sharpe 2.81, one period); win rate below 30 %.

### U-A3-10. Intraday momentum into the close
- **Source:** `research/R4-alphaxiv/chat-25-C-intraday-day-trading.md:87-97` (Market Intraday Momentum 2018; international evidence 2021; Chinese momentum and reversal 2019); `research/R2-trader-practice-windows-drift-isolation-breadth.md:58` (R37:47-48, survives costs in the ETF study).
- **Signal:** the first half-hour return (and the rest of the day) predicts the last half-hour.
- **Fits:** intraday; index futures and ETFs; test per market and horizon.
- **Data:** intraday bars; session calendars.
- **Needs:** QML block keyed to the session's cash open and close.
- **Evidence:** author backtest; sign varies by market.

### U-A3-11. Benchmark fix reversal
- **Source:** `research/R2-trader-practice-windows-drift-isolation-breadth.md:54-56` (Bank of Canada SWP 2021-48; MPRA 81583; month-end fix study).
- **Signal:** the dollar rises about 2.5 bp before the Tokyo, ECB and London fixes and falls the same afterwards; month-end equity gains predict currency weakening before the month-end fix.
- **Fits:** FX intraday around fixes.
- **Data:** fix calendar; tick quotes; the account's real spread.
- **Needs:** fix-window calendar state (gold fix windows are already in the MIS plan; FX fixes are not).
- **Evidence:** author backtest. Sharpe negative at full quoted spreads, 0.12-1.03 at half spreads: only viable if the cTrader spread is near half the indicative spread.

### U-A3-12. Positive controls from the MNQ falsification study
- **Source:** `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:36-41`; https://www.alphaxiv.org/abs/2605.04004.
- **Signal:** GMM regime-transition entries in regular hours ("RTH confluence", out-of-sample t 3.11 on 196 trades) and a London-session signal (t 4.30 on 247 trades), both held 60-75 minutes.
- **Fits:** micro index futures intraday.
- **Data:** 5m bars; tick data to confirm.
- **Needs:** QML blocks.
- **Evidence:** author backtest; 53+ variants tried; the London signal flips sign with a 15-minute delay. Weak seeds [judgment].

### U-A3-13. Do-not-build list from the same study
- **Source:** same as U-A3-12.
- **Signal:** Asia-session expansion bars (t -11.52 the wrong way), news-day drift after spike bars (none), gold OU mean reversion at 5m (half-life about 8 hours).
- **Fits:** recorded so agents do not propose them again for intraday; gold mean reversion may suit swing.
- **Evidence:** author backtest (negative).

### U-A3-14. Hidden semi-Markov duration gate
- **Source:** `research/R5-mql5-corpus-ideas.md:124` (MQL5 24460).
- **Signal:** close or skip trades by the current regime's remaining expected duration; trades closed by the gate made money (59.3 % wins) while the system lost.
- **Fits:** gold M5 intraday.
- **Needs:** QML block for regime age.
- **Evidence:** author backtest, in-sample.

### U-A3-15. Dominant-cycle trend or cycle playbook switch
- **Source:** `research/R5-mql5-corpus-ideas.md:499-504` (MQL5 23149, 23444).
- **Signal:** Hilbert-transform dominant cycle switches a unit between trend and cycle logic.
- **Fits:** FX and index intraday.
- **Needs:** QML block; possible MIS placement reading.
- **Evidence:** author backtest, in-sample.

## Macro, news and events

### U-A3-16. Calibrated news sentiment with novelty filtering (firm news)
- **Source:** `research/R6-alphaxiv-papers/T-04-agents-macro-micro-news.md:114-130`; MFAST (https://arxiv.org/abs/2609.23703).
- **Signal:** firm-day signal from calibrated LLM sentiment on deduplicated articles; trade only after publication.
- **Fits:** swing in liquid single stocks (daily horizon).
- **Data:** licensed timestamped news, entity mapping, point-in-time universe.
- **Needs:** news agent output as a QML input (today news is parked).
- **Evidence:** author backtest. Long-short Sharpe 2.85 (CI 2.31-3.34) at 5 bp; deflated Sharpe 2.19.

### U-A3-17. Macro surprise and revision around scheduled releases
- **Source:** `research/R4-alphaxiv/chat-28-F-agents-macro-micro-news.md:192`; LiveMacroEval (https://arxiv.org/abs/2608.30110); Andersen, Bollerslev, Diebold, Vega 2003/2007.
- **Signal:** surprise magnitude and direction against a timestamped consensus.
- **Fits:** low-frequency event-driven units in FX and index futures.
- **Data:** release calendar with vintages, consensus snapshot, quotes before and after.
- **Needs:** an MIS calendar state with actuals (the free feed has none today).
- **Evidence:** controlled test of forecast skill only; no costed strategy.

### U-A3-18. News-attributed jump factor
- **Source:** `research/R4-alphaxiv/chat-26-D-macrostructure.md:201`; https://www.alphaxiv.org/abs/2604.13458.
- **Signal:** LLM-classified news topics behind high-frequency jumps; topic-selected macro-jump factor.
- **Fits:** index futures; daily to annual rebalancing.
- **Data:** high-frequency futures prices, timestamped news.
- **Needs:** news agent topic labels.
- **Evidence:** author backtest. Macro-jump factor Sharpe 0.78; real-time topic selection 0.95 vs 0.28 intraday-only.

### U-A3-19. Earnings-gap reaction (continuation, reversal or no trade)
- **Source:** `research/R4-alphaxiv/chat-15-stress-scenarios.md` (turn 3 ideas); `chat-09-news-event-risk.md:22` (post-earnings drift is a longer-horizon pattern).
- **Signal:** rule choice after an earnings gap conditioned on halt and reopening behaviour, spread and overnight volume.
- **Fits:** stock intraday and swing.
- **Data:** timestamped earnings, after-hours prices, auction prints, depth, borrow.
- **Needs:** stock routes (not built) and an earnings calendar.
- **Evidence:** idea.

### U-A3-20. Macro probabilities as a crypto volatility trade input
- **Source:** `research/R4-alphaxiv/chat-26-D-macrostructure.md:192,199`; https://www.alphaxiv.org/abs/2604.01431.
- **Signal:** daily Kalshi macro-probability changes forecast five-day crypto realised volatility.
- **Fits:** crypto volatility-sized swing units (volatility, not direction).
- **Data:** prediction-market history, crypto prices.
- **Needs:** an external data reading.
- **Evidence:** author backtest; channel-specific; short sample.

## Swing and cross-asset

### U-A3-21. Volatility-managed trend, momentum and FX carry
- **Source:** `research/R4-alphaxiv/chat-26-D-macrostructure.md:198`; `chat-29-G-multi-asset-normalisation.md:142-145` (Barroso, Santa-Clara 2015; Moreira, Muir FX carry).
- **Signal:** time-series momentum, FX carry or futures trend scaled inversely to lagged volatility.
- **Fits:** swing; futures, FX, index.
- **Data:** point-in-time returns, swap and carry data, costs, roll calendars.
- **Needs:** QML blocks; swap inputs.
- **Evidence:** author backtest; Cederburg et al. challenge the real-time benefit.

### U-A3-22. Microstructure-filtered futures trend
- **Source:** `research/R4-alphaxiv/chat-15-stress-scenarios.md` (turn 3); https://www.alphaxiv.org/abs/2607.01550.
- **Signal:** fast and slow trend on liquid futures with sizing by volatility-normalised tick-size tier; small-tick markets decayed most after 2008 (fast trend Sharpe 0.84 to 0.12).
- **Fits:** swing futures.
- **Data:** contract prices, tick size, spread, depth, roll calendars.
- **Needs:** a tick-size tier field on instrument records.
- **Evidence:** author backtest.

### U-A3-23. Network momentum along lead-lag links
- **Source:** `research/R5-mql5-corpus-ideas.md:62` (MQL5 23763).
- **Signal:** learned lead-lag graph spreads momentum from leaders to laggards.
- **Fits:** swing or intraday across FX and futures.
- **Needs:** MIS cross-market lead-lag reading.
- **Evidence:** author backtest, in-sample.

### U-A3-24. FX carry with swap in the hold decision
- **Source:** `research/R5-mql5-corpus-ideas.md:127` (MQL5 22175).
- **Signal:** daily swap in account currency inside the entry and hold rule.
- **Fits:** swing FX and metals.
- **Data:** broker swap schedule, triple-swap day.
- **Evidence:** simulation (synthetic swap override).

### U-A3-25. Commodity expiry and roll dislocation
- **Source:** `research/R4-alphaxiv/chat-15-stress-scenarios.md` (turn 3); Negative Oil and Nickel Squeeze (https://www.alphaxiv.org/abs/2610.00951).
- **Signal:** front and next-month spread, open interest, days to last trade, inventory indicators: avoid constrained front-month exposure or trade the spread under forced roll pressure.
- **Fits:** energy and metals futures, swing.
- **Data:** contract-level prices, open interest, delivery calendars.
- **Needs:** MIS roll-state and days-to-expiry readings (planned in the futures pack).
- **Evidence:** idea (the paper is an explanatory model).

### U-A3-26. Post-shock staged re-entry ("crisis alpha" recovery)
- **Source:** `research/R4-alphaxiv/chat-15-stress-scenarios.md` (turn 3).
- **Signal:** after a gap or liquidation event, staged re-entry into trend or mean-reversion once spreads and liquidity normalise, separated by event type (endogenous build-up vs sudden news).
- **Fits:** intraday and swing, any class.
- **Evidence:** idea; none of the cited papers shows it profitable.

## Crypto-specific

### U-A3-27. Liquidation-risk throttle
- **Source:** `research/R4-alphaxiv/chat-15-stress-scenarios.md` (turn 3); https://www.alphaxiv.org/abs/2607.27070.
- **Signal:** taker-flow variance compression and open-interest build-up resembling prior cascades; avoid new leverage.
- **Fits:** crypto perps intraday.
- **Data:** venue minute prices, taker flow, open interest, funding, liquidations.
- **Needs:** MIS perps readings (funding and open interest are planned).
- **Evidence:** author backtest; population-level only (seven cascades).

### U-A3-28. Weekend crypto volatility into the Monday open
- **Source:** `research/R6-alphaxiv-papers/T-07-risk-off-isolation-stress.md:49-64`; https://www.alphaxiv.org/abs/2610.35702.
- **Signal:** common weekend crypto volatility predicts Monday variance of the S&P 500, gold and Treasuries (+27-54 % per standard deviation, since October 2023).
- **Fits:** a Monday-open volatility unit on indices or gold (also used as a risk component, A3-058).
- **Data:** weekend range-based crypto variance.
- **Needs:** MIS reading `weekend_crypto_vol_factor`.
- **Evidence:** author backtest.

## Placement readings the MIS would need

### U-A3-29. Persistence words for routing (mean-reverting, trending)
- **Source:** operator M5 (`seeds/operator-words-2026-11-01.md:43`, the MIS as router); `grounding/G9-runtime-brakes-isolation-evidence.md:153` (Hurst, variance ratio, efficiency ratio built on H1).
- **Reading:** per market and timeframe, whether price is mean-reverting or trending, at scalping timeframes (1m, 5m), not only H1.
- **Fits:** placement of System 1 units.
- **Needs:** MIS packs at lower timeframes; a unit read path (the compiler refuses reads today).
- **Evidence:** built at H1 only; no placement evidence.

### U-A3-30. Implied over realised volatility for placement and sizing
- **Source:** `research/R5-mql5-corpus-ideas.md:126` (MQL5 23734).
- **Reading:** implied/realised ratio per market with options (gold, indices, major FX).
- **Needs:** an external options data bridge (compute outside, publish JSON).
- **Evidence:** author backtest; "not a timing trigger".

### U-A3-31. Currency strength, dispersion and herding counts
- **Source:** `grounding/G9-runtime-brakes-isolation-evidence.md:153`; `grounding/G10-brakes-decay-slots-all-generations.md:357`.
- **Reading:** cross-market readings planned for This PC's MIS, none built.
- **Fits:** placement of FX units on the strongest and weakest currencies; risk-off sensing (A3-186).
- **Evidence:** idea.

### U-A3-32. Sniping-window cells as library artifacts
- **Source:** operator M8 (`seeds/operator-words-2026-11-01.md:94`: findings "in the library as artifacts, so the copilot can have jobs"); `research/R2-trader-practice-windows-drift-isolation-breadth.md:276`.
- **Reading:** per unit and instrument, time slices whose net edge in R is higher out of sample (A3-033), stored as library artifacts.
- **Fits:** scalpers and ORB.
- **Needs:** trade rows with session and time slice; a copilot job that proposes and a QMB job that proves.
- **Evidence:** idea.
