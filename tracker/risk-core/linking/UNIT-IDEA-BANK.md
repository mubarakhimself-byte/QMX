# Unit idea bank (merged)

Merged 2026-11-03 from the five Stage A files in `linking/unit-ideas/`: `A1-sizing-allocation.md` (18 seeds), `A2-brakes-drift-exits.md` (11), `A3-structure-regimes-scenarios.md` (32), `A4-template-agents-telemetry.md` (22) and `A5-topup.md` (29). The per-agent files stay as they are; this file only regroups them.

How to read it:
- Seeds are grouped by **style** (holding horizon and kind of edge), then by **instrument class**. Not ranked.
- Each entry keeps the original fields: source, signal or reading, style/timeframe/classes, data QMX would need, new MIS reading or QML block, evidence.
- **Seeds merged** names every original seed: `A1 #3` is seed 3 in the A1 file, `A3 U-A3-10` is that id in the A3 file, `A5-01` is that id in the A5 file. Where two or more files hold the same idea the entry is marked **DUPLICATE** and keeps every source; where they differ, each file's detail is kept and labelled.
- **NEGATIVE** marks a do-not-build seed (a tested idea that failed), kept so agents do not propose it again.
- "MIS reading" = a market-state input the MIS could publish. "QML block" = a statistic or signal block in the dictionary. Paths are relative to `D:\QMX-worktrees\risk-plan\tracker\risk-core\`.
- Every paper result is the source's claim; nothing here was re-tested.

Totals: all 112 original seeds placed, in 78 entries; 38 entries are marked DUPLICATE (some partial, where two files hold overlapping but not identical ideas). The table at the end lists the groups.

---

## 1. Scalping and order flow (seconds to 15 minutes)

### Exchange futures and stocks (central order books)

#### UB-01. Order-flow imbalance, best level and multi-level (OFI, MLOFI) — DUPLICATE
- **Seeds merged:** A1 #18; A3 U-A3-01; also the R4 synthesis seed list.
- **Sources:** `research/R4-alphaxiv/R4-alphaxiv-synthesis.md:184-186` and `chat-24` turn 3 (A1); `research/R4-alphaxiv/chat-27-E-microstructure.md:65-77`, Cont, Kukanov, Stoikov 2014 (https://www.alphaxiv.org/abs/1011.6402), Xu, Gould, Howison 2019 (https://www.alphaxiv.org/abs/1907.06230), `research/R6-alphaxiv-papers/T-03-macro-and-microstructure.md:78-93` (A3).
- **Signal:** signed queue changes (adds, executions, cancels) at the best quote or the first M levels as a vector; mid change is about linear in OFI with slope 1 / depth.
- **Style, timeframe, classes:** scalper, seconds to 1m; exchange futures, crypto exchange books, stocks. Not spot FX or CFDs (broker quotes are not a book).
- **Data:** timestamped L2 updates from the traded venue, depth per level (futures routes are outside this program, A1).
- **MIS or QML:** QML OFI and MLOFI blocks; an MIS depth reading per venue; a tick-tier node reading, run as a shadow label before any veto (A1).
- **Evidence:** author backtest. Contemporaneous R^2 about 65 % (OFI) vs 32 % (trade imbalance); 10-level ridge cut out-of-sample RMSE 15-74 % on six Nasdaq stocks (10-second windows). Explains price change; forecasting net of costs not shown.

#### UB-02. Event-conditioned short-lived impact (veto passive fills)
- **Seeds merged:** A3 U-A3-02.
- **Source:** `research/R4-alphaxiv/chat-27-E-microstructure.md:79-89`; Eisler, Bouchaud, Kockelkoren 2010 (https://www.alphaxiv.org/abs/0904.0900).
- **Signal:** recent order-book event flow (market orders, limit adds, cancels) predicts a short move; correlations last about 10-100 events (about 10 seconds).
- **Style, timeframe, classes:** maker scalpers on central books.
- **Data:** event-level best quotes, queue sizes, trades, cancels.
- **MIS or QML:** QML block; sub-second data.
- **Evidence:** author backtest (stocks).

#### UB-03. Auction-market order-flow features (ViperQ) — DUPLICATE
- **Seeds merged:** A3 U-A3-06; A4 #9; also the R4 synthesis seed list.
- **Sources:** `research/R4-alphaxiv/chat-28-F-agents-macro-micro-news.md:20,33,65,78,194,239`; ViperQ (https://arxiv.org/abs/2609.13825).
- **Signal:** volume-area position, cumulative volume delta slope and divergence, tape velocity, imbalance, fed to an RL policy.
- **Style, timeframe, classes:** short-horizon single stocks and futures with real books; intraday scalper filter. Not spot FX or CFDs.
- **Data:** trades with aggressor side, session volume profile, book imbalance; real volume.
- **MIS or QML:** QML blocks for CVD and volume-area position; an MIS order-flow regime reading (A4).
- **Evidence:** author backtest on TSLA and NVDA; large returns with drawdowns of -27.5 % and -47.8 %; RL, not LLM.

#### UB-04. Session order-flow regime labels as direction (Informed, Trending, Mean-Reverting)
- **Seeds merged:** A3 U-A3-07.
- **Source:** `research/R5-mql5-corpus-ideas.md:125` (MQL5 22940, rules at `md/22940.md:50-95`); `:146` (22938 imbalance thresholds).
- **Signal:** composite directional score: follow flow in Trending and Informed sessions, fade it in Mean-Reverting ones; order imbalance above p90 or below p10 as alignment.
- **Style, timeframe, classes:** index futures M1 intraday (NQ in the source).
- **Data:** M1 bars with a VPIN approximation, ARFIMA d, multifractal width, noise ratio.
- **MIS or QML:** MIS session-regime reading; QML blocks.
- **Evidence:** author backtest, in-sample, 602 sessions.

#### UB-05. Regimes in the order flow: duration-aware changepoints — DUPLICATE (partial)
- **Seeds merged:** A3 U-A3-08; overlaps A2 #7 (the same paper as a market reading, see UB-63).
- **Source:** `research/R6-alphaxiv-papers/T-03-macro-and-microstructure.md:55-74`; https://www.alphaxiv.org/abs/2609.07989.
- **Signal:** BOCPD with log-normal regime durations on signed volume as a regime filter for a scalper.
- **Style, timeframe, classes:** stocks and futures, volume clock.
- **Data:** signed volume in volume buckets.
- **MIS or QML:** QML block; volume clock in the MIS (`time_base: volume` exists in the reading record).
- **Evidence:** author backtest (internship report, two stocks).

#### UB-06. Fee-band three-class order-book model for one-minute futures moves — DUPLICATE (partial)
- **Seeds merged:** A5-16; A4 #17 lists the paper title only; also the R4 synthesis seed list.
- **Sources:** `research/R4-alphaxiv/chat-22d-saved-labelunbalance-finrlx.md:18-24,91-117`; `chat-14-early-exit-meta-labelling.md:189`; Label Unbalance in HFT (https://www.alphaxiv.org/abs/2503.09988); `conv-03-algorithmic-trading-papers.md:22-29` (A4).
- **Signal:** a 60-second window of 13 features sampled every 0.5 s (recent mid mean, volatility, skew, kurtosis, volume activity, quoted spread, return-volume beta, illiquidity) predicts whether the next minute's mid move clears the fee band up or down; fixed class weights or a cost-sensitive loss help, undersampling and focal loss sometimes hurt.
- **Style, timeframe, classes:** scalper, one minute; exchange futures (six Chinese contracts). Not CFDs or spot FX without a real book.
- **Data:** half-second book and trade data, fee schedule, a natural-mix calibration set.
- **MIS or QML:** QML blocks for the 13 features; the decision rule is component A5-topup-074.
- **Evidence:** author backtest, classification only, 20 trading days, no strategy returns.

### Crypto

#### UB-07. Maker reversal model (post when the imbalance signal is likely wrong)
- **Seeds merged:** A3 U-A3-03.
- **Source:** `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:93-115`; Albers et al. 2025 (https://www.alphaxiv.org/abs/2502.18625).
- **Signal:** a classifier (173 features) on when a top-of-book imbalance signal will reverse; post passive orders then.
- **Style, timeframe, classes:** crypto perpetual market making, sub-second.
- **Data:** L2 book, queue position, fills.
- **MIS or QML:** QML block; co-located speed the source says is required.
- **Evidence:** live (minimum-size orders, one week); round trip -0.44 bp to +0.71 bp net. Probably out of reach for QMX latency [judgment, A3].

#### UB-08. Crypto 15-minute sign reversal after taker-driven moves — DUPLICATE
- **Seeds merged:** A1 #7; A3 U-A3-04.
- **Sources:** `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:75-91` (A3), `:79-88` (A1); Kitron, Wengrowicz 2026 (https://www.alphaxiv.org/abs/2608.21888).
- **Signal:** the sign of the next 15-minute bar reverses, mostly after moves pushed by aggressive taker flow (signs, not sizes).
- **Style, timeframe, classes:** scalper 15m; crypto spot and perpetuals, maker orders only; metals ETFs inherit their metal's behaviour (A3).
- **Data:** real trade tape per venue with taker side; exact fee schedule and tier; maker fill markouts.
- **MIS or QML:** a "short-horizon reversal strength" reading per crypto market (A1); a QML taker-flow-conditioned reversal block (A3).
- **Evidence:** out-of-sample measurement with a frozen holdout and permutation null: 90 % of 183 Binance pairs significant vs 2.7 % of US stocks, every coin-year since 2021; gross about 1.3 bp vs about 5 bp cheapest round trip, so inside costs at retail fees.

#### UB-09. Quarter-hour bursts and imbalance in 24/7 markets — DUPLICATE
- **Seeds merged:** A1 #8; A3 U-A3-05.
- **Sources:** `R4-alphaxiv-synthesis.md:124` and `R6-synthesis.md` (A1); `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:117-133` (A3); https://www.alphaxiv.org/abs/2607.09426.
- **Signal:** recurring bursts in the first seconds after each quarter hour; quarter-hour order imbalance predicts the first 10 seconds (out-of-sample R^2 3.37 %, AUC 0.60, worth about 0.5 bp) and, per A3, 4-12 hours ahead.
- **Style, timeframe, classes:** execution timing in seconds (A1); intraday swing horizon for the 4-12 hour signal (A3); crypto perps.
- **Data:** tick or 10-second trade bins with signed volume and timestamps.
- **MIS or QML:** a tick-tier "bar-boundary burst" reading for execution timing (A1); an MIS reading of quarter-hour imbalance (A3).
- **Evidence:** author backtest, 2026 preprint; R6 rates it useful for execution timing, not for trading against costs.

#### UB-10. Crypto one-minute OHLCV direction model with fractional differentiation and triple-barrier labels
- **Seeds merged:** A5-17.
- **Source:** `research/R4-alphaxiv/chat-14-early-exit-meta-labelling.md:17,87,190` (https://www.alphaxiv.org/abs/2411.12753).
- **Signal:** supervised autoencoder on fractionally differentiated one-minute OHLCV plus macro and commodity features, labelled by triple barriers, trading 10-, 20- and 30-minute horizons.
- **Style, timeframe, classes:** intraday crypto (three coins).
- **Data:** one-minute crypto bars, macro and commodity series aligned point in time, realistic fills.
- **MIS or QML:** a fractional-differencing QML block; a primary signal for a meta-labeller.
- **Evidence:** author backtest over a bullish 2020-22: 20-minute portfolio 619.80 % vs 595.24 % buy-and-hold; 30-minute IR 2.56, drawdown 23.55 % vs 59.46 %; no slippage, perfect barrier fills.

#### UB-11. Open-interest unwind whose rebound taker flow (and basis) fails to confirm (AQuA) — DUPLICATE
- **Seeds merged:** A4 #1; A5-18.
- **Sources:** AQuA (arXiv 2608.12841) via `research/R4-alphaxiv/chat-18-agent-harness-alpha-discovery.md:150` (A4) and `chat-17-self-configuring-parameters.md:174` (A5); R6 read (`research/R6-alphaxiv-papers/T-04-agents-macro-micro-news.md:132-148`).
- **Signal:** open interest unwinds sharply with a high-volume unwind, price rebounds weakly, and taker buy flow (and, in chat-17, basis and funding recovery) fails to confirm; an unconfirmed rebound is more likely to fail.
- **Style, timeframe, classes:** crypto perpetuals, 5-minute bars (BTC), intraday or scalper.
- **Data:** per-venue open interest, taker buy and sell volume, 5-minute bars, basis, funding times.
- **MIS or QML:** QML open-interest-change and taker-flow-imbalance blocks; possibly an MIS "OI unwind" reading per crypto venue.
- **Evidence:** author backtest. Single factors IC about 0.026-0.037; the headline 0.190 is a combined validation IC, not a costed out-of-sample return.

## 2. Intraday and session (5 minutes to one day)

### Index futures and ETFs

#### UB-12. Intraday momentum: the first half-hour predicts the last half-hour — DUPLICATE
- **Seeds merged:** A1 #3; A3 U-A3-10; also the R4 synthesis seed list.
- **Sources:** `research/R4-alphaxiv/chat-25-C-intraday-day-trading.md:87-97` (Market Intraday Momentum 2018; international evidence 2021; China 2019); `R4-alphaxiv-synthesis.md:115-117`; `research/R2-trader-practice-windows-drift-isolation-breadth.md:58` (60+ futures; survives costs in the ETF study). Chat 25 was asked with a "$500 account" framing; the signal itself is general.
- **Signal:** the market's first 30-minute return (and the rest of the day) predicts the direction of the last 30 minutes; Chinese stocks show both momentum and reversal.
- **Style, timeframe, classes:** intraday, open and close; index futures, ETFs, stock indices. Test per market and horizon.
- **Data:** exchange session calendars; bars aligned to the cash open and close.
- **MIS or QML:** a session-tier "opening-window return" reading; a QML entry block keyed to the cash session.
- **Evidence:** author backtests; the futures and ETF study says it survives costs; sign varies by market.

#### UB-13. MNQ positive controls: regime transitions and a London signal held 60-75 minutes — DUPLICATE
- **Seeds merged:** A1 #9; A2 #3; A2 #4; A3 U-A3-12; A5-21 (time-exit detail).
- **Sources:** `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:24-50` (A1), `:33-43` (A2), `:36-41` (A3); `research/R8-gap-topup.md:229-251` (A5, read); Mesfin, https://www.alphaxiv.org/abs/2605.04004.
- **Signal:** GMM regime-transition entries in regular hours ("RTH confluence", out-of-sample t 3.11 on 196 trades) and a London-session pattern ("London signal B", t 4.30 on 247 trades), both held about 60-75 minutes; the two families that passed used fixed time exits.
- **Style, timeframe, classes:** intraday 5-minute bars; micro index futures (MNQ or index CFDs); gold weaker.
- **Data:** 5-minute bars, an RTH session calendar, a GMM regime model; tick data for the delay test; 2-point round-trip friction.
- **MIS or QML:** a regime-transition reading (or carried by the unit); an edge-versus-time curve per unit (component A5-topup-086).
- **Evidence:** author backtest; 53+ parameter combinations tried before locking, so the OOS t is optimistic; the London signal flips sign (t +4.30 to -2.78) with a 15-minute delay, a reason to test, not to trust. Weak seeds [judgment, A3].

#### UB-14. NEGATIVE: Asia-session expansion bars are spent; no post-news drift after spike bars — DUPLICATE
- **Seeds merged:** A2 #5; A2 #6; A3 U-A3-13 (first two items); A5-21 (Asia item).
- **Sources:** `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:36-37`; `research/R8-gap-topup.md:240-242`; 2605.04004.
- **Reading:** following Asia-session expansion bars on MNQ gave t -11.5 the wrong way (the move is used up inside the signal bar); on news days there was no drift after the spike bars; an opening-range pullback entry stopped out 80.7 % of the time at a 20-point stop.
- **Style, timeframe, classes:** intraday, index futures, Asia session and scheduled news.
- **Data:** 5-minute bars, session and release calendars.
- **MIS or QML:** none; a placement veto ("no continuation logic on Asia expansion bars").
- **Evidence:** author backtest (negative results); a fade is untested.

### Single stocks

#### UB-15. Opening-range breakout on markets "in play" — DUPLICATE
- **Seeds merged:** A1 #4; A3 U-A3-09.
- **Sources:** `research/R5-mql5-corpus-ideas.md:100-101` (MQL5 17745, 23226); `research/R2-trader-practice-windows-drift-isolation-breadth.md:61` (R37:72); `grounding/G7-unit-inputs-qmb-mis-instruments.md:159`.
- **Signal:** ORB taken only on stocks or markets with unusual relative volume at the open; pre-screen keeps price, volume and ATR above $0.50; three Concretum ORB variants combined at about 0.3 monthly correlation cut drawdown to about 10 % against 15 %+ alone.
- **Style, timeframe, classes:** ORB intraday, 1-5m; US stocks and index futures first; FX and gold London or NY opens with tick rate as the stand-in.
- **Data:** real volume and a 20-day median by minute (RVOL); cash-open calendars; a stock route (none in this build).
- **MIS or QML:** an RVOL MIS reading (today a dictionary concept only, blocked until bars carry volume and time of day); ORB entry blocks.
- **Evidence:** cited paper net of costs for one period (top 20 net Sharpe 2.81); the MQL5 rebuild is in-sample; win rate below 30 %.

#### UB-16. Intraday cross-sectional US equity long-short at 30 minutes (AQuA model track) — DUPLICATE
- **Seeds merged:** A4 #21; A5-19.
- **Sources:** AQuA (arXiv 2608.12841) via `research/R4-alphaxiv/chat-17-self-configuring-parameters.md:164,175`; R6 read (`T-04-agents-macro-micro-news.md:132-148`).
- **Signal:** multiscale price and volume history combined into per-stock scores, sector-neutralised, threshold longs and shorts, volatility-targeted.
- **Style, timeframe, classes:** intraday single stocks, 30-minute forecasts.
- **Data:** point-in-time equity prices and volume, sector labels, explicit turnover costs, a stock venue.
- **MIS or QML:** none; a model-based unit outside the current class mix.
- **Evidence:** author backtest, held-out 2021-25 Sharpe 2.15, 2.50 with volatility targeting, 2.00 fully walk-forward, positive every year at 2 bp two-leg cost (1.7, 3.5, 1.9, 1.8, 2.7); R6: retail costs would erase much of it and trials were not deflated.

#### UB-17. Earnings-gap reaction: continuation, reversal or no trade
- **Seeds merged:** A3 U-A3-19.
- **Source:** `research/R4-alphaxiv/chat-15-stress-scenarios.md` (turn 3 ideas); `chat-09-news-event-risk.md:22`.
- **Signal:** rule choice after an earnings gap conditioned on halt and reopening behaviour, spread and overnight volume.
- **Style, timeframe, classes:** stock intraday and swing.
- **Data:** timestamped earnings, after-hours prices, auction prints, depth, borrow.
- **MIS or QML:** stock routes (not built) and an earnings calendar.
- **Evidence:** idea.

### FX

#### UB-18. Benchmark fix reversal (Tokyo, ECB, London 16:00) — DUPLICATE
- **Seeds merged:** A1 #1; A2 #10; A3 U-A3-11 (first half).
- **Sources:** `research/R2-trader-practice-windows-drift-isolation-breadth.md:54,63` (Bank of Canada SWP 2021-48; JF 2024 version; MPRA 81583).
- **Signal:** across 9 currencies 1999-2019 the dollar rises about 2.5 bp before the Tokyo, ECB and London fixes and falls the same afterwards, driven by dealers hedging fixed dollar demand. A "sniping window" in the professional sense (A2).
- **Style, timeframe, classes:** intraday, minutes around each fix; FX majors.
- **Data:** fix times per currency; second-to-minute quotes; QMX's own measured spread per hour at cTrader (the cost journal decides).
- **MIS or QML:** a fix-window calendar state per currency (gold fix windows are in the MIS plan; FX fixes are not); one QML entry block.
- **Evidence:** author backtest, long academic sample. Gross Sharpe up to 2.45; negative at full quoted spreads; 0.12-1.03 at half spreads. Only viable if the cTrader spread is near half the indicative spread (A3).

#### UB-19. Month-end London fix rebalancing — DUPLICATE
- **Seeds merged:** A1 #2; A3 U-A3-11 (second half).
- **Sources:** `R2:56` (sciencedirect S1386418114000779).
- **Signal:** month-to-date equity gains predict the currency weakening before the month-end fix, as equity managers rebalance their hedges.
- **Style, timeframe, classes:** monthly, intraday into the fix; FX against equity-heavy currencies.
- **Data:** month-to-date equity index returns per country; fix calendar; tick quotes; the account's real spread.
- **MIS or QML:** an MIS day-tier "month-to-date equity move per currency" reading; one QML block.
- **Evidence:** academic; the abstract makes no cost claim.

#### UB-20. A rule strategy and a model that trade only when both agree (MQL5 20238)
- **Seeds merged:** A4 #14.
- **Source:** MQL5 article 20238 via `research/R5-mql5-corpus-ideas.md:422`.
- **Signal:** an ensemble of a rule-based strategy and a statistical model on shared indicators, entering only on agreement; two unprofitable systems made one profitable one.
- **Style, timeframe, classes:** FX intraday on MT5.
- **Data:** bars and indicators already available.
- **MIS or QML:** a QML "both agree" combiner block fits the logic-slot gate.
- **Evidence:** author backtest, mostly in-sample; the gate cuts trades, so exposure effect and skill are not separated.

#### UB-21. Per-symbol agents sharing signals through a coordination layer (MQL5 21115)
- **Seeds merged:** A4 #15.
- **Source:** MQL5 article 21115 via `research/R5-mql5-corpus-ideas.md:172`.
- **Signal:** each symbol's agent shares its signal; a coordination layer enforces portfolio limits; execution and risk stay in MQL5.
- **Style, timeframe, classes:** FX cross-symbol.
- **Data:** a shared signal bus across units (QMX units stand alone today).
- **MIS or QML:** possibly an MIS cross-symbol signal-agreement reading.
- **Evidence:** none (no test numbers).

#### UB-22. LLM fine-tuned on pair statistics (MQL5 20329)
- **Seeds merged:** A4 #16.
- **Source:** MQL5 article 20329 via `research/R5-mql5-corpus-ideas.md:171`.
- **Signal:** a base LLM bought EURUSD at RSI 32 and rode a 200-pip fall; fine-tuning on pair statistics reportedly raised the win rate about 10 points.
- **Style, timeframe, classes:** FX, EURUSD.
- **Data:** per-pair statistics and a fine-tuning setup.
- **MIS or QML:** none.
- **Evidence:** author backtest in-sample plus one demo week. Shows an LLM needs instrument statistics; not evidence of edge.

### Metals

#### UB-23. Hidden semi-Markov duration gate (regime age as a trade filter) — DUPLICATE
- **Seeds merged:** A3 U-A3-14; A2 #8 (as a market reading, see UB-64).
- **Source:** `research/R5-mql5-corpus-ideas.md:124` (MQL5 24460).
- **Signal:** close or skip trades by the current regime's remaining expected duration; trades closed by the gate made money (59.3 % wins) while the system lost.
- **Style, timeframe, classes:** gold M5 intraday; durations differ by class.
- **Data:** bars per instrument; a fitted duration distribution per class.
- **MIS or QML:** a QML regime-age block; an MIS `regime-age` reading (A2).
- **Evidence:** author backtest, in-sample, 8 months of XAUUSD M5.

### Cross-class intraday

#### UB-24. Dominant-cycle trend or cycle playbook switch
- **Seeds merged:** A3 U-A3-15.
- **Source:** `research/R5-mql5-corpus-ideas.md:499-504` (MQL5 23149, 23444).
- **Signal:** a Hilbert-transform dominant cycle switches a unit between trend and cycle logic.
- **Style, timeframe, classes:** FX and index intraday.
- **Data:** bars.
- **MIS or QML:** QML block; possible MIS placement reading.
- **Evidence:** author backtest, in-sample.

## 3. Event-driven (news, macro, scheduled releases, calendar flow)

### Single stocks

#### UB-25. Calibrated firm-day news sentiment with novelty filtering (MFAST) — DUPLICATE
- **Seeds merged:** A3 U-A3-16; A4 #7; also the R4 synthesis seed list.
- **Sources:** `research/R6-alphaxiv-papers/T-04-agents-macro-micro-news.md:114-130` (R6 read); `research/R4-alphaxiv/chat-28-F-agents-macro-micro-news.md:142-146,238`; MFAST (https://arxiv.org/abs/2609.23703).
- **Signal:** timestamped firm news, entity-matched, deduplicated, classified by an LLM, calibrated, aggregated to a firm-day score; trade only after publication; gains concentrate in complex articles (negation, guidance, numbers).
- **Style, timeframe, classes:** swing in liquid single stocks, daily to five-day holds. R6: FX, indices and commodities react to macro releases and need a different pipeline.
- **Data:** licensed timestamped news, entity mapping, point-in-time universe, costs, a GPU (54.2 GB peak).
- **MIS or QML:** a news-sentiment reading per stock (model inference, not a QML block); news agent output as a QML input (news is parked today).
- **Evidence:** author backtest, post-cutoff June 2024-January 2026, long-short Sharpe 2.85 (CI 2.31-3.34) after 5 bp and a 10 % ADV cap; deflated Sharpe 2.19.

#### UB-26. Filing-risk downgrade with deteriorating momentum as an exposure cut (MarketSenseAI)
- **Seeds merged:** A5-15.
- **Source:** `research/R4-alphaxiv/chat-22c-saved-marketsenseai-evolvetrade.md:20,26-30` (https://www.alphaxiv.org/abs/2502.00415).
- **Signal:** structured changes in profitability, leverage, liquidity, disclosed risk and guidance from filings and calls, combined with weakening momentum, to reduce single-stock exposure.
- **Style, timeframe, classes:** monthly; single stocks.
- **Data:** filings and transcripts with publication timestamps, five quarters of financials, prices.
- **MIS or QML:** a fundamentals-risk reading per stock under the expiring evidence contract (component A5-topup-070).
- **Evidence:** author backtest of the whole monthly pipeline (S&P 100 equal-weight 53.2 % vs 42.3 %; cap-weighted 123 % vs 73.5 % with drawdown 13.8 % vs 9.7 %); component signal untested; no walk-forward.

#### UB-27. Analyst-report synthesis with a falsifying condition per position (Steward)
- **Seeds merged:** A4 #11.
- **Source:** Steward, arXiv 2610.30557, R6 read (`T-04-agents-macro-micro-news.md:50-74`).
- **Signal:** a portfolio-manager agent synthesises news, filings, macro series and market data into target weights with conviction and a named invalidating condition; code grading found the synthesis was where value came from.
- **Style, timeframe, classes:** US equities, swing.
- **Data:** filings, news, macro series; a stock venue.
- **MIS or QML:** none; the falsifying-condition idea could become a "thesis invalidated" exit block.
- **Evidence:** author backtest plus a five-month paper-account deployment (102 trading days), not real money.

### Index futures and macro releases

#### UB-28. News-attributed jump factor
- **Seeds merged:** A3 U-A3-18; also the R4 synthesis seed list.
- **Source:** `research/R4-alphaxiv/chat-26-D-macrostructure.md:201`; https://www.alphaxiv.org/abs/2604.13458.
- **Signal:** LLM-classified news topics behind high-frequency jumps; a topic-selected macro-jump factor.
- **Style, timeframe, classes:** index futures; daily to annual rebalancing.
- **Data:** high-frequency futures prices, timestamped news.
- **MIS or QML:** news agent topic labels.
- **Evidence:** author backtest; macro-jump factor Sharpe 0.78; real-time topic selection 0.95 vs 0.28 intraday-only.

#### UB-29. Macro surprise and revision against a timestamped consensus (LiveMacroEval) — DUPLICATE
- **Seeds merged:** A3 U-A3-17; A4 #8; also the R4 synthesis seed list.
- **Sources:** `research/R4-alphaxiv/chat-28-F-agents-macro-micro-news.md:130-138,192,237`; LiveMacroEval (https://arxiv.org/abs/2608.30110); Andersen, Bollerslev, Diebold, Vega 2003/2007.
- **Signal:** hourly pre-release nowcasts against the consensus available just before the release; surprise size and direction.
- **Style, timeframe, classes:** low-frequency event-driven units; FX (pair-relative surprises), index futures, rates, metals.
- **Data:** release calendar with actuals (the free calendar in `t3-news-calendar-watch` has none, G9 2), vintages, consensus snapshots, quotes around releases.
- **MIS or QML:** an MIS event-surprise calendar state per currency or index; ties to the parked news layer.
- **Evidence:** live forecast evaluation (November 2025-March 2026); a forecast-skill score, not a costed trading return.

### Energy

#### UB-30. EIA inventory surprises move crude and gas together; OPEC decision type
- **Seeds merged:** A5-25.
- **Source:** `research/R8-gap-topup.md:445-469` (Halova, Kurov, Kucher 2014; Loutia, Mellios, Andriosopoulos 2016; snippets).
- **Reading:** inventory surprises corrected for forecast error move energy futures more than older studies found (about 10 % in gas per 1 % inventory shock, units to check); crude surprises move gas and the reverse; OPEC effects are stronger for cuts and holds and differ for WTI and Brent.
- **Style, timeframe, classes:** event windows; crude and natural gas futures and CFDs.
- **Data:** EIA schedule as data (holiday shifts), consensus inventory forecasts, OPEC calendar with decision type, tick data around releases.
- **MIS or QML:** an MIS inventory-surprise reading; an OPEC decision-type calendar field (overlay is component A5-topup-094).
- **Evidence:** author backtest (event studies, abstract-level).

#### UB-31. Trading ahead of commodity index roll windows (Goldman roll)
- **Seeds merged:** A5-26.
- **Source:** `research/R8-gap-topup.md:471-478` (Mou 2010, SSRN 1716841, abstract).
- **Signal:** positions ahead of the main index roll days earned positive-skew excess returns; index investors gave up about 3.6 % a year to the impact.
- **Style, timeframe, classes:** swing around monthly roll windows; energy and other index commodity futures.
- **Data:** index roll calendars, contract-level prices.
- **MIS or QML:** a roll-window calendar state per contract.
- **Evidence:** author backtest, Sharpe up to 4.39 for 2000 to March 2010 (abstract only).

#### UB-32. Commodity expiry and roll dislocation
- **Seeds merged:** A3 U-A3-25 (related to UB-31, a different signal).
- **Source:** `research/R4-alphaxiv/chat-15-stress-scenarios.md` (turn 3); Negative Oil and Nickel Squeeze (https://www.alphaxiv.org/abs/2610.00951).
- **Signal:** front and next-month spread, open interest, days to last trade, inventory indicators: avoid constrained front-month exposure, or trade the spread under forced roll pressure.
- **Style, timeframe, classes:** energy and metals futures, swing.
- **Data:** contract-level prices, open interest, delivery calendars.
- **MIS or QML:** MIS roll-state and days-to-expiry readings (planned in the futures pack).
- **Evidence:** idea (the paper is an explanatory model).

### ETFs and indices

#### UB-33. NEGATIVE: calendar effects promoted by repeated peeking
- **Seeds merged:** A5-24.
- **Sources:** `research/R4-alphaxiv/chat-11-backtest-overfitting-validation.md:209`; `chat-12-safe-derisk-rerisk.md:156` (Promote 2611.03384 market replay).
- **Signal:** turn of month, first and last three trading days, weekday, quarter-end, January, third Friday on ETF and industry panels.
- **Style, timeframe, classes:** short-horizon calendar rules; ETFs and indices.
- **Data:** exchange calendars, next-executable prices, costs.
- **MIS or QML:** calendar states exist in part.
- **Evidence:** controlled test, negative: none of 24 candidates crossed the funded promotion threshold; a reversed-industry January rule passed only under repeated unadjusted testing and then lost after costs.

### Any class

#### UB-34. Post-shock staged re-entry ("crisis alpha" recovery)
- **Seeds merged:** A3 U-A3-26.
- **Source:** `research/R4-alphaxiv/chat-15-stress-scenarios.md` (turn 3).
- **Signal:** after a gap or liquidation event, staged re-entry into trend or mean-reversion once spreads and liquidity normalise, separated by event type (endogenous build-up vs sudden news).
- **Style, timeframe, classes:** intraday and swing, any class.
- **Data:** spreads, depth, event classification.
- **MIS or QML:** none named.
- **Evidence:** idea; none of the cited papers shows it profitable.

## 4. Swing and trend (days to weeks)

### Futures across sectors

#### UB-35. Time-series trend across futures, and a cross-asset trend tilt — DUPLICATE
- **Seeds merged:** A1 #6; A5-04 (trend half).
- **Sources:** `research/R4-alphaxiv/chat-29-G-multi-asset-normalisation.md` (turn 3 section 2); `R4-alphaxiv-synthesis.md:161` (Value and Momentum Everywhere); `chat-05-allocation-across-strategies.md:199-201`.
- **Signal:** trend following across many futures, each scaled to comparable dollar risk; more risk to sleeves with persistent trend, less when volatility rises.
- **Style, timeframe, classes:** daily swing; futures in every sector (FX, index, rates, metals, energy).
- **Data:** continuous and point-in-time futures with correct roll mapping, financing and roll returns, realised volatility, costs; paid futures data, which this program does not include.
- **MIS or QML:** trend-against-range reading (planned); QML trend block.
- **Evidence:** long academic record (A1); the chat-05 version is the assistant's candidate (idea).

#### UB-36. Short- and long-horizon trend, sized by tick-size tier — DUPLICATE
- **Seeds merged:** A3 U-A3-22; A5-02.
- **Sources:** `research/R4-alphaxiv/chat-15-stress-scenarios.md` (turn 3); `chat-02-breadth-effective-bets.md:170,182,194`; `chat-04-drawdown-controlled-sizing.md:137`; https://www.alphaxiv.org/abs/2607.01550; CTA replication https://www.alphaxiv.org/abs/2507.15876.
- **Signal:** fast and slow trend on liquid futures; count the fast sleeve as separate only where it keeps out-of-sample diversification after costs; size or admit by volatility-normalised tick-size tier.
- **Style, timeframe, classes:** daily to intraday trend; diversified futures, FX trend sleeves.
- **Data:** contract prices, tick size, volatility, spread, depth, roll calendars.
- **MIS or QML:** a tick-size tier field on instrument records; QML fast and slow trend blocks.
- **Evidence:** author backtests. Fast trend Sharpe 0.84 -> 0.12 after 2008-09, slow 0.70 -> 0.40, small-tick markets decayed most; short-trend sleeve Sharpe 0.37 vs 0.70 long, correlation 0.50; MKT+STT Sharpe 0.80 and drawdown 14.9 % vs 0.61 and 20.3 %. Trend sleeves have long droughts (Landolfi 2608.00127).

#### UB-37. Network momentum along lead-lag links — DUPLICATE
- **Seeds merged:** A1 #14; A3 U-A3-23; A5-01.
- **Sources:** `research/R5-mql5-corpus-ideas.md:62` (MQL5 23763); `research/R4-alphaxiv/chat-02-breadth-effective-bets.md:183,193` (Follow the Leader, https://www.alphaxiv.org/abs/2501.07135).
- **Signal:** learn which markets lead which and spread momentum from leaders to laggards.
- **Style, timeframe, classes:** swing (or intraday per A3) across FX and futures; commodity futures across energy, metals and agriculture plus equity indices (paper).
- **Data:** aligned returns across markets; daily settlement or continuous futures, roll schedules, volatility-scaled returns, causal lead-lag or DTW features.
- **MIS or QML:** a cross-market lead-lag graph MIS reading on This PC (could also flag correlated units before both fire); a QML network-momentum block.
- **Evidence:** MQL5 in-sample (A1, A3); paper 2005-2024 net Sharpe 0.364 vs 0.233 for MACD, P&L correlation 0.71-0.89 with the baseline, so a related sleeve (A5).

### Metals

#### UB-38. Gold futures trend and momentum with volatility targeting (Forecast-to-Fill)
- **Seeds merged:** A5-05.
- **Source:** `research/R4-alphaxiv/chat-12-safe-derisk-rerisk.md:154` (https://www.alphaxiv.org/abs/2511.08571).
- **Signal:** smoothed trend and momentum on gold futures, volatility-targeted, ATR exits, fractional-Kelly sizing, daily settlement inputs.
- **Style, timeframe, classes:** swing; gold futures (gold CFDs by extension).
- **Data:** settlement and roll data, executable fills, changing spread and impact.
- **MIS or QML:** none new.
- **Evidence:** author backtest; abstract Sharpe 2.88 but the realised series ran about 2.65 % CAGR at 0.91 % volatility; static friction, single asset.

### ETFs and multi-asset

#### UB-39. Volatility-scaled multi-asset momentum rotation (TrendFolios)
- **Seeds merged:** A5-03.
- **Source:** `research/R4-alphaxiv/chat-02-breadth-effective-bets.md:184,195` (https://www.alphaxiv.org/abs/2506.09330).
- **Signal:** biweekly or monthly rotation among equity, fixed-income and commodity-factor ETFs; momentum and trend votes; size inversely to tracking error.
- **Style, timeframe, classes:** slow overlay; ETFs.
- **Data:** adjusted ETF prices, benchmarks, factor classes, costs, point-in-time universe.
- **MIS or QML:** none; a portfolio-level unit.
- **Evidence:** author backtest, in-sample to 2023: 7.35 % a year vs 4.80 % for 60/40, Sharpe 0.48 vs 0.51, volatility 15.36 % vs 9.50 %.

#### UB-40. Multi-asset rotation with regime as a risk gate, and KAMA trend timing (FinRL-X)
- **Seeds merged:** A5-08.
- **Source:** `research/R4-alphaxiv/chat-22d-saved-labelunbalance-finrlx.md:54-64,139-141` (https://www.alphaxiv.org/abs/2603.21330).
- **Signal:** weekly rotation picking at most two of Growth, Real Assets and Defensive by information ratio against QQQ, residual momentum within groups, regime indicators only as risk gates; KAMA-based timing scales a base allocation.
- **Style, timeframe, classes:** weekly and daily; US equities and ETFs.
- **Data:** ETF and index prices, group map, regime reading.
- **MIS or QML:** a KAMA timing block; regime reading as gate.
- **Evidence:** author backtest 2018-2025 at 10 bp per side: rotation Sharpe 1.10, drawdown -21.46 %; DRL with timing Sharpe 0.89 vs 0.55 without; rolling Nasdaq-100 top-25 % Sharpe 0.93, drawdown -38.95 %.

#### UB-41. Market-exposure filter that sits out declines (Quant-Arena finding)
- **Seeds merged:** A4 #3.
- **Source:** Quant-Arena, arXiv 2610.30113, via `research/R4-alphaxiv/chat-18-agent-harness-alpha-discovery.md:144,152`.
- **Signal:** the best agent result profited mainly by staying in cash through the early-2024 decline: a market-exposure filter, not stock picking.
- **Style, timeframe, classes:** index-level timing, daily; A-shares; could overlay index CFDs or futures.
- **Data:** index bars, a regime or trend reading.
- **MIS or QML:** possibly an index risk-on or risk-off reading (overlaps A3 regime work).
- **Evidence:** author backtest on a sealed 2024 year; still underperformed the market (excess about -6.3 points, drawdown -6.8 %).

#### UB-42. Evolved allocation score: normalised Sharpe, momentum rank, volatility, drawdown penalty (EvolveTrade)
- **Seeds merged:** A5-09.
- **Source:** `research/R4-alphaxiv/chat-22c-saved-marketsenseai-evolvetrade.md:44` (https://www.alphaxiv.org/abs/2609.17632).
- **Signal:** one evolved policy scored assets on normalised Sharpe, momentum rank, normalised volatility and a drawdown penalty and set weights by a capped softmax.
- **Style, timeframe, classes:** daily-close allocation; 15 US blue chips plus cash.
- **Data:** daily bars; 20- and 60-day returns, volatility, drawdown, ATR.
- **MIS or QML:** a capped-softmax allocation block.
- **Evidence:** author backtest, one-month windows from -6.60 % to +6.84 %; one evolved run, not a framework rule.

### Stocks and ETFs

#### UB-43. Causal multi-horizon volatility-normalised momentum (Trading-R1 labels made live-safe) — DUPLICATE (partial)
- **Seeds merged:** A5-06; A4 #17 lists Trading-R1 by title; also the R4 synthesis seed list ("volatility-aware recommendation labels").
- **Sources:** `research/R4-alphaxiv/chat-22e-saved-quantharness-tradingr1.md:28,116,201` (https://www.alphaxiv.org/abs/2509.11420); `conv-03-algorithmic-trading-papers.md:22-29`.
- **Signal:** EMA(3)-smoothed price; 3-, 7- and 15-day returns each divided by 20-period volatility; weights 0.3, 0.5, 0.2; action levels by percentiles fitted on past data only. In the paper these are forward-return training labels; a unit must use trailing returns.
- **Style, timeframe, classes:** swing, about a week; stocks and ETFs in the paper; not a scalper.
- **Data:** daily bars; past-only thresholds per instrument; the full model also needs fundamentals, dated news, sentiment, macro.
- **MIS or QML:** a QML composite-momentum block (the assistant's "build first").
- **Evidence:** author backtest of the full model (six US names, June-August 2024, +2.38 % to +8.08 %, Sharpe 0.86-2.72, no explicit cost schedule, training span overlaps the test); the causal signal is untested.

#### UB-44. QuantaAlpha families: multiscale momentum with a volatility gate, trend quality, price-volume confirmation, gap acceptance
- **Seeds merged:** A5-07.
- **Source:** `research/R4-alphaxiv/chat-22b-saved-diffusion-control-quantaalpha.md:52-57,130-140` (https://www.alphaxiv.org/abs/2602.07085).
- **Signal:** (a) agreement of 1-, 5- and 20-day momentum, damped in stressed volatility; (b) continuation with low residual noise and limited impact; (c) rolling price-volume co-movement plus a short intraday return; (d) normalised overnight gap with intraday acceptance or rejection and abnormal volume; (e) regime-filtered reversal (brittle when regimes rotate).
- **Style, timeframe, classes:** daily cross-sectional stocks; (c) and (d) nearest to intraday ideas for index CFDs and stocks.
- **Data:** daily or intraday OHLCV and VWAP, point-in-time universe, real volume for (c) and (d).
- **MIS or QML:** QML gap-acceptance and price-volume co-movement blocks; a volatility-ratio gate.
- **Evidence:** author backtest, CSI 300: IC 0.0472, excess 4.68 %, IR 0.6453, drawdown 11.8 % after 0.20 % round trip; a corrected rerun of a reused pipeline gave -0.2 % (different protocol).

#### UB-45. Moving-average crossover baselines (SMA 50/200; MA20/MA60 ranked)
- **Seeds merged:** A5-10.
- **Sources:** `research/R4-alphaxiv/chat-11-backtest-overfitting-validation.md:208`; `chat-22e-saved-quantharness-tradingr1.md:26`.
- **Signal:** SMA(50,200) crossover on liquid ETFs; MA20 over MA60 scored by max(MA20/MA60 - 1, 0), top 20 equal weight, next-session execution.
- **Style, timeframe, classes:** daily trend; ETFs and stocks.
- **Data:** adjusted daily prices, dividends, costs.
- **MIS or QML:** none; useful as control units.
- **Evidence:** idea (examples in papers, not evidence of profit).

#### UB-46. Supertrend with tuned ATR period and multiplier (weak) — DUPLICATE
- **Seeds merged:** A4 #20; A5-20.
- **Source:** arXiv 2405.14262 via `research/R4-alphaxiv/chat-17-self-configuring-parameters.md:173`.
- **Signal:** buy when the close crosses above the ATR Supertrend line; sell, exit or reverse below it.
- **Style, timeframe, classes:** daily or slower stock bars (Nifty 50, HUL, Infosys, Microsoft, NVIDIA).
- **Data:** OHLC bars; an ATR block (atr-wilder exists, G8 3.4).
- **MIS or QML:** a Supertrend QML block.
- **Evidence:** author backtest, in-sample maximum-profit optimisation only; default run lost 1.16 % overall; Infosys worse optimised than default. Too weak to use the tuned values.

#### UB-47. AI-exposed equity ranker traded only while a model-health gate passes
- **Seeds merged:** A5-14.
- **Source:** `research/R4-alphaxiv/chat-04-drawdown-controlled-sizing.md:138,152` (When Alpha Breaks, https://www.alphaxiv.org/abs/2603.13252).
- **Signal:** a cross-sectional ranker switched on and off by a point-in-time health gate from its own matured prediction errors, with a tail cap on the most uncertain positions.
- **Style, timeframe, classes:** daily to weekly; US single stocks.
- **Data:** matured prediction errors, point-in-time features, returns, turnover, costs.
- **MIS or QML:** a model-health reading per unit (risk side is component A5-topup-015).
- **Evidence:** author backtest, narrow universe: gate AUROC 0.721 vs 0.449 for VIX percentile; final-period Sharpe 0.375 -> 0.925 with the cap.

### Crypto

#### UB-48. Daily multi-agent swing stack for BTC and ETH under a fast risk loop (SwingGuard) — DUPLICATE
- **Seeds merged:** A4 #10; A5-29 (its trigger list, see UB-71); also the R4 synthesis seed list ("crypto risk triggers").
- **Sources:** SwingGuard, arXiv 2610.12988, R6 read (`T-04-agents-macro-micro-news.md:76-95`); `research/R4-alphaxiv/chat-19-llm-agents-risk-monitoring.md:136,140`.
- **Signal:** daily technical, sentiment, on-chain and macro agents plus a bull-versus-bear debate form a long-only target; a 5-minute deterministic controller caps it.
- **Style, timeframe, classes:** crypto swing, daily targets, long only.
- **Data:** 5-minute bars, 7-day news, on-chain data, latest M2 release.
- **MIS or QML:** on-chain and M2 readings would be new to the MIS.
- **Evidence:** author backtest, August 2024-January 2025, 15 bp one way: Sharpe 2.98, return 37.16 %, drawdown 6.44 %, average exposure 31.74 %; without the controller Sharpe 1.87 and drawdown 14.19 %; no trial count.

#### UB-49. Trend and relative value across crypto pairs
- **Seeds merged:** A5-28.
- **Source:** `research/R4-alphaxiv/chat-05-allocation-across-strategies.md:203` (2602.11708; 2606.04574).
- **Signal:** directional trend across major coins, or market-neutral pairs, with funding, leverage, venue and weekend controls.
- **Style, timeframe, classes:** intraday to swing; crypto.
- **Data:** venue prices and trades, funding, open interest, fees, borrow, depth, 24/7 timestamps.
- **MIS or QML:** pair-spread blocks.
- **Evidence:** idea (papers named for inspection).

## 5. Pairs and spreads

#### UB-50. OU spread unit with derived entry, target and stop
- **Seeds merged:** A2 #11.
- **Source:** `research/R4-alphaxiv/chat-13-stops-and-exits.md:76-86` (1411.5062), follow-ons 2309.16008 and 1706.07021.
- **Signal:** trade a mean-reverting spread whose entry band, take-profit and stop come from the fitted OU parameters and costs; raising the stop level lowers the optimal target.
- **Style, timeframe, classes:** pairs and spread units; FX crosses, energy calendar spreads, index pairs.
- **Data:** synchronised bars for both legs, cost per leg, a causal parameter fit.
- **MIS or QML:** spread-construction and OU-fit blocks.
- **Evidence:** simulation (analytical model with an illustrative ETF example).

## 6. Carry and basis

### FX

#### UB-51. Volatility-managed momentum and FX carry, with a risk-off brake — DUPLICATE
- **Seeds merged:** A1 #5; A3 U-A3-21; A5-04 (carry half); also the R4 synthesis seed list.
- **Sources:** `research/R4-alphaxiv/chat-29-G-multi-asset-normalisation.md:142-145` (Barroso, Santa-Clara 2015; Moreira, Muir 2017); `chat-26-D-macrostructure.md:198`; `chat-05-allocation-across-strategies.md:202`.
- **Signal:** cut momentum exposure when its realised volatility is high (crash avoidance); FX carry, time-series momentum or futures trend scaled inversely to lagged volatility; carry sized down when funding stress or risk-off indicators rise.
- **Style, timeframe, classes:** swing to monthly; equities (momentum), FX (carry), futures, indices.
- **Data:** point-in-time returns, carry and swap data per pair, forward points, short rates, bid-ask, event calendar, currency factor exposures.
- **MIS or QML:** a carry-differential reading per pair; QML carry and volatility-scaling blocks.
- **Evidence:** published backtests; Cederburg et al. challenge whether volatility timing holds in real time.

#### UB-52. FX carry with swap inside the hold decision
- **Seeds merged:** A3 U-A3-24 (related to UB-51).
- **Source:** `research/R5-mql5-corpus-ideas.md:127` (MQL5 22175).
- **Signal:** daily swap in account currency inside the entry and hold rule.
- **Style, timeframe, classes:** swing FX and metals.
- **Data:** broker swap schedule, triple-swap day.
- **MIS or QML:** swap inputs.
- **Evidence:** simulation (synthetic swap override).

### Crypto and multi-pair

#### UB-53. Perpetual funding carry and basis; cross-sectional FX signals — DUPLICATE (partial)
- **Seeds merged:** A4 #19; A5-27.
- **Sources:** `research/R4-alphaxiv/conv-02-ai-quant-trading-design.md:464-465` (starter skills `research_fx_cross_sectional_signal`, `research_crypto_perp_carry_signal`); `chat-21-multi-agent-market-simulation.md:140,155` (Agent-Based Simulation of a Perpetual Futures Market, https://www.alphaxiv.org/abs/2501.09404).
- **Signal:** crypto perpetual funding carry; a perp premium that persists when long positional traders meet short basis traders while funding keeps the perp tied to spot; cross-sectional FX signals.
- **Style, timeframe, classes:** carry and basis, hours to days, holding through funding times; crypto perps against spot; FX multi-pair.
- **Data:** funding history per venue (the CCXT refresh writes funding clocks, G9 5.1), basis, open interest, fees, liquidation data; FX swap points.
- **MIS or QML:** a funding-carry and basis reading for crypto (planned in the crypto pack); a currency-strength reading for FX (planned on This PC, G9 4.1).
- **Evidence:** idea (A4, named only); simulation without agent wealth or a liquidation engine (A5).

## 7. Cross-sectional stock factors (daily)

#### UB-54. Agent-mined simple OHLCV factors combined by LightGBM (AlphaAgent) — DUPLICATE
- **Seeds merged:** A4 #2; A5-12; also the R4 synthesis seed list.
- **Sources:** AlphaAgent, arXiv 2502.16789, via `research/R4-alphaxiv/chat-18-agent-harness-alpha-discovery.md:141,151` and `chat-22a-saved-alphaagent-mass.md:20,102-104`.
- **Signal:** factors filtered for novelty, hypothesis alignment and low complexity, combined by LightGBM into a top-ranked portfolio; base factors intraday return, daily return, 20-day relative volume and normalised daily range (the first, third and fourth are the nearest short-horizon raw material).
- **Style, timeframe, classes:** daily cross-sectional stocks (CSI 500, S&P 500), next-day return target.
- **Data:** daily or intraday OHLCV, point-in-time universe, costs.
- **MIS or QML:** a family of factor blocks if stocks are added; range and RVOL exist in part.
- **Evidence:** author backtest 2021-24: 11.00 % (IR 1.488) and 8.74 % (IR 1.0545) excess after fees, drawdown 9.36 % and 9.10 %; no slippage; current-index universe, so survivorship may remain.

#### UB-55. Heterogeneous simulated investors: consensus minus disagreement (MASS) — DUPLICATE
- **Seeds merged:** A4 #4; A5-13; also the R4 synthesis seed list.
- **Sources:** MASS, arXiv 2505.10278, via `research/R4-alphaxiv/chat-18-agent-harness-alpha-discovery.md:154` and `chat-22a-saved-alphaagent-mass.md:32-44,134`.
- **Signal:** many simulated investor agents with different feature access and styles; Signal = alpha x weighted agreement - (1 - alpha) x weighted disagreement; high disagreement linked to overpricing under short-sale limits.
- **Style, timeframe, classes:** weekly stock selection (A-shares); as a reading, agreement across QMX's own units per instrument.
- **Data:** per-agent feature sets and history; per-unit signals per instrument, timestamped.
- **MIS or QML:** an agreement-and-disagreement reading over units (component A5-topup-064); the assistant frames MASS as a stress or diversity mechanism.
- **Evidence:** author backtest: 2023 returns 2.16 %, 4.95 %, 1.17 %, drawdowns 11.98-19.06 %, 0.1 % round trip, weekly; Q1 2025 leakage check; type weights fitted on 5-day RankIC.

#### UB-56. NEGATIVE: classic factor families and an LLM-found volatility-breakout family that failed deflation — DUPLICATE
- **Seeds merged:** A4 #22; A5-11.
- **Sources:** What survives honest evaluation?, arXiv 2608.27734, via `research/R4-alphaxiv/chat-17-self-configuring-parameters.md:167,176`; `chat-11-backtest-overfitting-validation.md:207-212`.
- **Signal:** volatility breakout (five LLM runs converged on it); momentum (126-day), low volatility, short-term reversal, oscillator mean reversion, volume effects; RSI plus volume-z-score contrarian ranked monthly; rank-IC quintile sleeves on value, liquidity, volatility, momentum.
- **Style, timeframe, classes:** daily to monthly US stocks.
- **Data:** point-in-time daily stock data, delistings, borrow, publication lags, turnover costs.
- **MIS or QML:** none.
- **Evidence:** author backtest: classic factors DSR at most 0.32; search PBO 0.83; volatility-breakout OOS Sharpe 0.59-0.70 and +26-33 %, but 0 of 5 survived deflation. A profitable window is not a certified edge.

#### UB-57. Evolved factor trees for hourly crypto and index constituents (EvoQuantLab)
- **Seeds merged:** A4 #5.
- **Source:** EvoQuantLab, arXiv 2610.17130, via `research/R4-alphaxiv/chat-18-agent-harness-alpha-discovery.md:22,76-82,142`.
- **Signal:** typed genetic-programming factor trees with LLM-proposed mechanisms, family-diverse elites.
- **Style, timeframe, classes:** hourly crypto; daily CSI 500 and S&P 500.
- **Data:** point-in-time bars per venue and constituent lists.
- **MIS or QML:** factor blocks per discovered family; no family is proven.
- **Evidence:** author backtest on short windows (crypto 37.91 % annualised, 7.17 % cumulative, -3.23 % drawdown, April-June 2026).

#### UB-58. Semantic factor selection from a timestamped market-state description (Alpha-R1)
- **Seeds merged:** A4 #6.
- **Source:** Alpha-R1, arXiv 2512.23515, via `research/R4-alphaxiv/chat-18-agent-harness-alpha-discovery.md:25`.
- **Signal:** an RL-trained LLM picks a sparse subset of a factor pool by matching factor descriptions to a market-state description; memory frozen before the test.
- **Style, timeframe, classes:** daily stock factors (S&P 500, CSI 300).
- **Data:** a described factor library and a timestamped market-state text.
- **MIS or QML:** a reading-to-block selector; for QMX the nearer analogue is MIS placement.
- **Evidence:** author backtest, 2025 test after 10 bp (47.87 % and 40.57 %); S&P interval includes zero under two of three block lengths.

#### UB-59. Regime-conditioned constraint levels for LLM stock trading (Strat-LLM)
- **Seeds merged:** A4 #12.
- **Source:** Strat-LLM, arXiv 2605.06024, via `research/R4-alphaxiv/chat-28-F-agents-macro-micro-news.md:64,76`.
- **Signal:** stricter strategy constraints cut GPT-5's maximum drawdown from 20.83 % to 11.66 % in a US sample, with effects varying by regime.
- **Style, timeframe, classes:** US stocks, T+1.
- **Data:** news and filings; a regime reading.
- **MIS or QML:** a regime reading to switch constraint levels (overlaps A3).
- **Evidence:** forward-running tests, stock-only.

## 8. Options and volatility

#### UB-60. Short-dated SPX put writing with VIX-based sizing
- **Seeds merged:** A5-22.
- **Source:** `research/R4-alphaxiv/chat-12-safe-derisk-rerisk.md:155` (https://www.alphaxiv.org/abs/2508.16598).
- **Signal:** sell 0-5 DTE SPXW puts; far out-of-the-money short-dated configurations had better information ratios and lower drawdowns than near-the-money ones; size by Kelly, VIX or a hybrid.
- **Style, timeframe, classes:** short volatility, days; index options (no QMX route today).
- **Data:** option surfaces, greeks, implied and realised volatility, spread and depth, fills, margin, crash scenarios.
- **MIS or QML:** a VIX-rank reading; an options venue route.
- **Evidence:** author backtest; out-of-sample 2024 only, not a dislocation sample.

#### UB-61. SPX short straddles with a learned hold-or-exit policy
- **Seeds merged:** A5-23.
- **Source:** `research/R4-alphaxiv/chat-14-early-exit-meta-labelling.md:187` (https://www.alphaxiv.org/abs/2610.13126).
- **Signal:** a short-straddle unit whose exit is chosen by a classifier on volatility-risk-premium proxies, option spread and liquidity, moneyness, time to expiry, holding time and current P&L.
- **Style, timeframe, classes:** short volatility, multi-day; index options.
- **Data:** 30-minute SPX option quotes and position state.
- **MIS or QML:** none in today's classes; the exit is component A5-topup-043.
- **Evidence:** author backtest, locked 2024-26: 35.01 % vs 11.56 %, Sharpe 1.651 vs 0.441, drawdown 4.04 % vs 12.82 %; no crisis in the test.

## 9. Market readings for placement and risk (MIS inputs)

### All classes

#### UB-62. Mean-reversion half-life per instrument and session; gold too slow for 5-minute scalping — DUPLICATE
- **Seeds merged:** A1 #10; A2 #1; A3 U-A3-13 (third item).
- **Sources:** `research/R4-alphaxiv/chat-13-stops-and-exits.md:165` (Leung and Li, https://www.alphaxiv.org/abs/1411.5062); `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:37-38` (2605.04004 gold OU arm); `R6-synthesis.md` class table.
- **Reading:** OU half-life, ln(2)/mu, of a price or spread; tells a mean-reversion unit how long a trade should take and when a stale trade has lost its reason; gold's intraday half-life about 8 hours, too slow for 5-minute scalping (may suit swing). NEGATIVE for gold 5m mean reversion.
- **Style, timeframe, classes:** placement reading and time exit for mean-reversion scalpers and intraday units; FX crosses, spreads and pairs, metals.
- **Data:** mid prices or bars per instrument and session, with causal estimation and its uncertainty.
- **MIS or QML:** an MIS `reversion-half-life` day-tier reading per instrument and session, beside the shipped `half-life-of-mean-reversion` block; feeds the time exit (A2 component 233).
- **Evidence:** simulation of an OU model (exit use); author backtest (gold half-life).

#### UB-63. Change-point probability (BOCPD with a duration prior) as a market reading — DUPLICATE (partial)
- **Seeds merged:** A2 #7; overlaps A3 U-A3-08 (UB-05).
- **Source:** `research/R5-mql5-corpus-ideas.md:123` (MQL5 23482); `research/R6-alphaxiv-papers/T-03-macro-and-microstructure.md:55-74` (2609.07989).
- **Reading:** a per-bar probability that the regime just broke, best with log-normal durations, flagged only when the most likely run length falls; measures change, not direction; 23482 showed its timing carried information against a random brake.
- **Style, timeframe, classes:** any; tested on EURUSD M30 and US stock order flow.
- **Data:** bars or order-flow buckets per instrument.
- **MIS or QML:** a refinement: the MIS runs a CUSUM change-point block; a BOCPD reading with a duration prior would be new.
- **Evidence:** controlled test (23482, few trades); author backtest (two stocks, four months).

#### UB-64. Regime age as a market reading — DUPLICATE
- **Seeds merged:** A2 #8; A3 U-A3-14 (as a trade filter, UB-23).
- **Source:** `research/R5-mql5-corpus-ideas.md:124` (MQL5 24460).
- **Reading:** how old the current regime is under a hidden semi-Markov model with explicit durations.
- **Style, timeframe, classes:** scalper and intraday; metals tested; durations differ by class.
- **Data:** bars; a fitted duration distribution per class.
- **MIS or QML:** a `regime-age` reading, which also feeds the add-size taper (A2 component 173).
- **Evidence:** author backtest (short sample; 59.3 % wins on gated trades).

#### UB-65. Per-instrument calibrated volatility-break alarm (CUSUM)
- **Seeds merged:** A2 #9.
- **Source:** `research/R5-mql5-corpus-ideas.md:328,454-462` (MQL5 23043, 23103).
- **Reading:** CUSUM on standardised returns with its threshold fitted on each instrument's own history; theory thresholds fired about 5 times too often; alarms caught mostly variance shifts; latency at macro events a few bars.
- **Style, timeframe, classes:** all; tested on FX, gold, DE40 and USTEC across three timeframes.
- **Data:** bars; a calibration record per instrument and detector.
- **MIS or QML:** a calibration change to the shipped MIS CUSUM reading.
- **Evidence:** author backtest (cross-asset).

#### UB-66. Multi-horizon trend or reversal state; persistence words for routing — DUPLICATE (partial)
- **Seeds merged:** A2 #2; A3 U-A3-29.
- **Sources:** `research/R4-alphaxiv/chat-13-stops-and-exits.md:20,23,159,166` (Safari and Schmidhuber, https://www.alphaxiv.org/abs/2501.16772); operator M5 (`seeds/operator-words-2026-11-01.md:43`); `grounding/G9-runtime-brakes-isolation-evidence.md:153`.
- **Reading:** trend strength at several horizons (futures show reversal at minute scales and weak trend persistence over longer intraday horizons, differing by asset and time zone); per market and timeframe, whether price is mean-reverting or trending at scalping timeframes (1m, 5m), not only H1 (Hurst, variance ratio, efficiency ratio are built at H1).
- **Style, timeframe, classes:** intraday units and System 1 placement; index futures, FX, commodities.
- **Data:** minute bars per instrument, session-tagged; MIS packs at lower timeframes; a unit read path (the compiler refuses reads today).
- **MIS or QML:** a multi-horizon trend-strength reading per instrument and session; persistence words for the router; chooses between a mean-reversion and a trend exit (A2 component 265).
- **Evidence:** author backtest with very small R^2 (A2); built at H1 only, no placement evidence (A3).

#### UB-67. Session volatility features beat session flags
- **Seeds merged:** A1 #13.
- **Source:** `research/R5-mql5-corpus-ideas.md:105` (MQL5 22516; 22274 feature importance).
- **Reading:** session volatility columns carried 25.6 % of model importance against 2.5 % for session flags.
- **Style, timeframe, classes:** intraday models; FX.
- **Data:** volatility per session window.
- **MIS or QML:** a session-tier volatility reading; supports gating sessions on measured volatility.
- **Evidence:** out-of-sample inside 22274.

#### UB-68. Selective forecasting that abstains under uncertainty (FinAbstain)
- **Seeds merged:** A4 #13.
- **Source:** FinAbstain, arXiv 2607.24875, via `research/R4-alphaxiv/chat-28-F-agents-macro-micro-news.md:261`.
- **Reading:** forecasts from specialist agents with cited evidence; disagreement and retrieval quality decide whether to forecast at all.
- **Style, timeframe, classes:** not stated.
- **Data:** multimodal retrieval sources.
- **MIS or QML:** an "abstain" confidence reading.
- **Evidence:** simulation only.

#### UB-69. Sniping-window cells as library artifacts; a model that finds windows like a known one — DUPLICATE (partial)
- **Seeds merged:** A3 U-A3-32; A4 #18 (second half; parked).
- **Sources:** operator M8 (`seeds/operator-words-2026-11-01.md:94`); `research/R2-trader-practice-windows-drift-isolation-breadth.md:276`; operator M10 (`seeds/SEEDS.md` D44).
- **Reading:** per unit and instrument, time slices whose net edge in R is higher out of sample, stored as library artifacts; or a model trained on one known sniping window searches for similar ones.
- **Style, timeframe, classes:** scalpers and ORB; session opens.
- **Data:** trade rows with session and time slice; labelled window examples.
- **MIS or QML:** a copilot job that proposes and a QMB job that proves (A3); a "similar window" reading would be new (A4).
- **Evidence:** idea; A4's half was ruled out of this session by him ("that's what the lab inside KMX is for").

### FX and cross-asset

#### UB-70. Shared dollar and carry factors; currency strength, dispersion and herding counts — DUPLICATE (partial)
- **Seeds merged:** A1 #17; A3 U-A3-31.
- **Sources:** `R4-alphaxiv-synthesis.md:158` (Lustig, Roussanov, Verdelhan 2011); `grounding/G9-runtime-brakes-isolation-evidence.md:153`; `grounding/G10-brakes-decay-slots-all-generations.md:357`.
- **Reading:** FX pairs load on a common dollar factor and a carry factor; cross-market currency strength, dispersion and herding counts.
- **Style, timeframe, classes:** placement of FX units on the strongest and weakest currencies; exposure and factor budgets; risk-off sensing (A3 component 186).
- **Data:** a basket of pairs; interest differentials.
- **MIS or QML:** "USD factor" and "carry factor" readings; currency strength (planned on This PC, none built).
- **Evidence:** published factor model (A1); idea (A3).

#### UB-71. Market-stress early warnings: ETF-underlying divergence, correlated drops, order-flow toxicity, crypto risk triggers
- **Seeds merged:** A5-29 (SwingGuard part also in UB-48).
- **Source:** `research/R4-alphaxiv/chat-19-llm-agents-risk-monitoring.md:140` (FARSIGHT 2609.19705; SwingGuard 2610.12988).
- **Reading:** VIX level, correlated-asset drops, order-flow toxicity, liquidity stress and divergence between an ETF and its underlying as candidate early warnings; SwingGuard adds drawdown, ATR, momentum, exposure, on-chain and news anomalies, source diversity and six-hour accumulation as triggers for deeper diagnosis.
- **Style, timeframe, classes:** risk readings for all classes; ETF-underlying divergence for indices and commodities with listed ETFs; on-chain for crypto.
- **Data:** ETF and underlying prices aligned, a volatility index, order-flow data where a book exists, on-chain feeds.
- **MIS or QML:** an ETF-premium (divergence) reading would be new; the rest overlap A3 detectors.
- **Evidence:** idea for the FARSIGHT list; author backtest for SwingGuard.

### Activity and execution timing

#### UB-72. Quote-duration activity gauge (ACD)
- **Seeds merged:** A1 #12.
- **Source:** `research/R5-mql5-corpus-ideas.md:81` (MQL5 24742).
- **Reading:** the wait between quotes; in EURUSD's quietest half hour it is about 47 times longer than in its busiest; an Engle-Russell duration model adds a small but significant gain to next-minutes volatility forecasts on six symbols.
- **Style, timeframe, classes:** scalper 1m; FX, metals, index CFDs.
- **Data:** tick quote timestamps; recalibrate monthly and on any broker change.
- **MIS or QML:** a tick-tier "activity against usual" reading (the MIS plans tick rate against usual; this adds a duration model).
- **Evidence:** out-of-sample gain on six symbols.

### Volatility inputs

#### UB-73. Implied over realised volatility for placement and sizing — DUPLICATE
- **Seeds merged:** A1 #11; A3 U-A3-30.
- **Source:** `research/R5-mql5-corpus-ideas.md:126` (MQL5 23734).
- **Reading:** implied over realised volatility as a forward-looking risk state; "not a timing trigger".
- **Style, timeframe, classes:** intraday to swing; gold, major indices, some FX (needs liquid options).
- **Data:** an options implied-volatility feed, computed outside and published as JSON.
- **MIS or QML:** a new MIS day-tier reading; component A1-sizing-allocation-013 uses it for size.
- **Evidence:** mechanism check only (A1); author backtest (A3).

#### UB-74. Weekend crypto volatility leads Monday risk — DUPLICATE
- **Seeds merged:** A1 #15; A3 U-A3-28; also the R4 synthesis seed list.
- **Sources:** `R4-alphaxiv-synthesis.md:321`; `R6-synthesis.md`; `research/R6-alphaxiv-papers/T-07-risk-off-isolation-stress.md:49-64`; https://www.alphaxiv.org/abs/2610.35702.
- **Reading:** a volatile crypto weekend predicts larger Monday gaps and variance in the S&P 500, gold and Treasuries (+27-54 % per standard deviation, since October 2023).
- **Style, timeframe, classes:** Monday opening risk, or a Monday-open volatility unit; indices, metals, bonds (read from crypto).
- **Data:** weekend range-based crypto variance.
- **MIS or QML:** an MIS calendar-tier `weekend_crypto_vol_factor` reading; could raise the worst-move input for Monday sizing (also A3 component 058).
- **Evidence:** author backtest; read by R6.

#### UB-75. Macro prediction-market probabilities forecast crypto volatility — DUPLICATE
- **Seeds merged:** A1 #16; A3 U-A3-20; also the R4 synthesis seed list.
- **Sources:** `R4-alphaxiv-synthesis.md:164`; `research/R4-alphaxiv/chat-26-D-macrostructure.md:192,199`; https://www.alphaxiv.org/abs/2604.01431.
- **Reading:** daily changes in Kalshi macro probabilities forecast 5-day crypto realised volatility for some channels; one example implies about 7 % less BTC weight under inverse-volatility sizing. Volatility, not direction.
- **Style, timeframe, classes:** daily; crypto volatility-sized swing units.
- **Data:** timestamped prediction-market history, crypto prices.
- **MIS or QML:** a day-tier "macro repricing" reading feeding volatility forecasts; an external data reading.
- **Evidence:** author backtest, 2026 preprint, channel-specific, short sample; not read by R6.

### Crypto structure

#### UB-76. Liquidation-risk throttle
- **Seeds merged:** A3 U-A3-27.
- **Source:** `research/R4-alphaxiv/chat-15-stress-scenarios.md` (turn 3); https://www.alphaxiv.org/abs/2607.27070.
- **Reading:** taker-flow variance compression and open-interest build-up resembling prior cascades; avoid new leverage.
- **Style, timeframe, classes:** crypto perps intraday.
- **Data:** venue minute prices, taker flow, open interest, funding, liquidations.
- **MIS or QML:** MIS perps readings (funding and open interest are planned).
- **Evidence:** author backtest; population-level only (seven cascades).

## 10. Research leads without a defined signal

#### UB-77. Earlier conversation's RL and LLM trading papers (conv-03) — DUPLICATE (partial)
- **Seeds merged:** A4 #17 (UB-06 and UB-43 take two of its papers further).
- **Source:** `research/R4-alphaxiv/conv-03-algorithmic-trading-papers.md:22-29`: Trading-R1 (2509.11420), MacroHFT (2406.14537), QuantAgent / QuantHarness, price-driven multi-agent LLMs for HFT (2509.09995), JaxMARL-HFT (2511.02136), label imbalance in HFT (2503.09988), xLSTM DRL (2503.09655).
- **Signal:** RL and LLM policies for high-frequency crypto and stock trading.
- **Style, timeframe, classes:** HFT and scalping, crypto and stocks.
- **Data:** tick or order-book data per venue; GPU simulation for JaxMARL.
- **MIS or QML:** unknown until read.
- **Evidence:** idea (titles and one-line claims).

#### UB-78. An agent that reads charts like a human trader (operator, parked)
- **Seeds merged:** A4 #18 (first half; second half in UB-69).
- **Source:** operator M10 (`seeds/SEEDS.md` D44).
- **Signal:** a strong model with a trading knowledge base looks at charts and proposes trade ideas.
- **Style, timeframe, classes:** discretionary-style ideas across classes.
- **Data:** chart images or bars, a curated knowledge base.
- **MIS or QML:** none.
- **Evidence:** idea; parked by him for the lab.

---

## Duplicate groups at a glance

| Entry | Idea | Seeds |
|---|---|---|
| UB-01 | OFI / MLOFI | A1 #18, A3 U-A3-01 |
| UB-03 | ViperQ order-flow features | A3 U-A3-06, A4 #9 |
| UB-05, UB-63 | BOCPD regimes in order flow / change-point reading | A3 U-A3-08, A2 #7 |
| UB-06 | Label imbalance HFT model | A5-16, A4 #17 |
| UB-08 | Crypto 15-minute reversal | A1 #7, A3 U-A3-04 |
| UB-09 | Quarter-hour effect | A1 #8, A3 U-A3-05 |
| UB-11 | AQuA open-interest unwind | A4 #1, A5-18 |
| UB-12 | Intraday momentum into the close | A1 #3, A3 U-A3-10 |
| UB-13 | MNQ positive controls | A1 #9, A2 #3, A2 #4, A3 U-A3-12, A5-21 |
| UB-14 | MNQ negative seeds | A2 #5, A2 #6, A3 U-A3-13, A5-21 |
| UB-15 | ORB in play | A1 #4, A3 U-A3-09 |
| UB-16 | AQuA intraday cross-section | A4 #21, A5-19 |
| UB-18 | FX fix reversal | A1 #1, A2 #10, A3 U-A3-11 |
| UB-19 | Month-end fix | A1 #2, A3 U-A3-11 |
| UB-23, UB-64 | Regime age / HSMM gate | A2 #8, A3 U-A3-14 |
| UB-25 | MFAST news sentiment | A3 U-A3-16, A4 #7 |
| UB-29 | Macro surprise (LiveMacroEval) | A3 U-A3-17, A4 #8 |
| UB-35 | Futures trend and cross-asset tilt | A1 #6, A5-04 |
| UB-36 | Fast and slow trend by tick tier | A3 U-A3-22, A5-02 |
| UB-37 | Network momentum | A1 #14, A3 U-A3-23, A5-01 |
| UB-43 | Trading-R1 momentum | A5-06, A4 #17 |
| UB-46 | Supertrend | A4 #20, A5-20 |
| UB-48 | SwingGuard | A4 #10, A5-29 |
| UB-51 | Volatility-managed momentum and carry | A1 #5, A3 U-A3-21, A5-04 |
| UB-53 | Funding carry and cross-sectional FX | A4 #19, A5-27 |
| UB-54 | AlphaAgent factors | A4 #2, A5-12 |
| UB-55 | MASS consensus | A4 #4, A5-13 |
| UB-56 | Factor families that failed deflation | A4 #22, A5-11 |
| UB-62 | Mean-reversion half-life | A1 #10, A2 #1, A3 U-A3-13 |
| UB-66 | Multi-horizon trend state and persistence words | A2 #2, A3 U-A3-29 |
| UB-69 | Sniping-window cells | A3 U-A3-32, A4 #18 |
| UB-70 | Dollar and carry factors, currency strength | A1 #17, A3 U-A3-31 |
| UB-73 | Implied over realised volatility | A1 #11, A3 U-A3-30 |
| UB-74 | Weekend crypto into Monday | A1 #15, A3 U-A3-28 |
| UB-75 | Prediction-market crypto volatility | A1 #16, A3 U-A3-20 |
| UB-77 | conv-03 paper list | A4 #17 |
