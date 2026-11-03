# Unit idea bank seeds, file A5-topup

Stage A, 3 Nov 2026. Trading signals and market readings found in the top-up sources: R4 chats 02 (turns 2-3), 04, 05, 07, 11, 12, 14, 17, 19-21, 22a-22e, the R4 synthesis, R8 and R9. They are not risk-and-sizing components and are not ranked. Paper results are the alphaXiv assistant's claims unless R8 marks them read. Paths are relative to `D:\QMX-worktrees\risk-plan\tracker\risk-core\`.

"MIS reading" means a market-state input the MIS could publish. "QML block" means a statistic or signal block in the dictionary. Where a seed repeats one in A1-A4, it says so and adds only what these sources add.

## Trend and momentum (swing and daily)

### A5-01. Network momentum: leaders' trends spread to followers
- **Source:** `research/R4-alphaxiv/chat-02-breadth-effective-bets.md:183,193` (Follow the Leader, https://www.alphaxiv.org/abs/2501.07135).
- **Signal:** trend following plus cross-market lead-lag, learned as a network; momentum flows from leading to lagging contracts.
- **Style, timeframe, classes:** daily trend; commodity futures across energy, metals and agriculture, plus equity indices.
- **Data QMX would need:** daily settlement or continuous futures, roll schedules, volatility-scaled returns, causal rolling lead-lag or dynamic-time-warping features.
- **New MIS reading or QML block:** an MIS lead-lag graph reading; a QML network-momentum block.
- **Evidence:** author backtest, 2005-2024: best variant net Sharpe 0.364 vs 0.233 for MACD, beats baseline in bootstrap; P&L correlation with the baseline 0.71-0.89, so a related sleeve, not a new cluster. Same idea as A1 #14 and A3 U-A3-23 (MQL5 23763), here with paper numbers.

### A5-02. Short- and long-horizon trend overlay, split by tick-size tier
- **Source:** `chat-02-breadth-effective-bets.md:170,182,194` (CTA replication 2507.15876; Is Trend Still Your Friend? 2607.01550); `chat-04-drawdown-controlled-sizing.md:137` (Landolfi 2608.00127 drought calibration; Lemperiere et al. 2014).
- **Signal:** blend fast and slow futures trend; count the fast sleeve as separate only where it keeps out-of-sample diversification after costs.
- **Style, timeframe, classes:** daily to intraday trend; diversified futures, FX trend sleeves.
- **Data QMX would need:** intraday or daily prices, contract tick size, volatility, spread and depth for short-horizon execution.
- **New MIS reading or QML block:** a tick-size tier field per instrument; QML fast and slow trend blocks.
- **Evidence:** author backtest. Short-trend sleeve Sharpe 0.37 vs 0.70 long-trend, correlation 0.50; MKT+STT Sharpe 0.80 and drawdown 14.9 % vs 0.61 and 20.3 % for MKT alone; fast trend Sharpe fell to 0.12 after 2009, slow to 0.40. Trend sleeves have long droughts (longer time under water than mean reversion). Close to A3 U-A3-22.

### A5-03. Volatility-scaled multi-asset momentum rotation (TrendFolios)
- **Source:** `chat-02-breadth-effective-bets.md:184,195` (https://www.alphaxiv.org/abs/2506.09330).
- **Signal:** two-week or monthly rotation among equity, fixed-income and commodity-factor ETFs; momentum and trend votes; size inversely to tracking error.
- **Style, timeframe, classes:** slow portfolio overlay, biweekly to monthly; ETFs (index and commodity exposure).
- **Data QMX would need:** adjusted ETF prices, benchmarks, factor classes, costs, point-in-time universe.
- **New MIS reading or QML block:** no; a portfolio-level unit.
- **Evidence:** author backtest, in-sample ETF data to 2023: 7.35 % a year vs 4.80 % for 60/40, but Sharpe 0.48 vs 0.51 and volatility 15.36 % vs 9.50 %. Higher growth, not better risk-adjusted.

### A5-04. Cross-asset trend tilt and FX carry with a risk-off brake
- **Source:** `chat-05-allocation-across-strategies.md:199-204`.
- **Signal:** medium-term time-series trend across FX, index, rates, metals and energy futures with more risk to persistent trends; FX carry sized down when volatility, funding stress or risk-off indicators rise.
- **Style, timeframe, classes:** swing; futures, FX.
- **Data QMX would need:** point-in-time futures with roll mapping, financing and roll returns; spot, forward points and swaps, short rates, bid-ask, event calendar.
- **New MIS reading or QML block:** a carry-differential reading; a risk-off state feeding size.
- **Evidence:** idea (assistant's candidate list). Duplicate of A1 #5-6 and A3 U-A3-21/24.

### A5-05. Gold futures trend and momentum with volatility targeting (Forecast-to-Fill)
- **Source:** `chat-12-safe-derisk-rerisk.md:154` (https://www.alphaxiv.org/abs/2511.08571).
- **Signal:** smoothed trend and momentum on gold futures, volatility-targeted, ATR exits, fractional-Kelly sizing, daily settlement inputs.
- **Style, timeframe, classes:** swing; gold futures (and gold CFDs by extension).
- **Data QMX would need:** settlement and roll data, executable fills, changing spread and impact, non-overlapping test periods.
- **New MIS reading or QML block:** no new reading; trend blocks exist.
- **Evidence:** author backtest. Abstract claims Sharpe 2.88, but the realised-volatility series ran about 2.65 % CAGR at 0.91 % volatility; the high numbers are a volatility-normalised 15 % series. Static friction, single asset.

### A5-06. Causal multi-horizon volatility-normalised momentum (Trading-R1 labels made live-safe)
- **Source:** `chat-22e-saved-quantharness-tradingr1.md:28,116,201` (Trading-R1, https://www.alphaxiv.org/abs/2509.11420).
- **Signal:** smooth price with a 3-span EMA; take 3-, 7- and 15-day returns, each divided by 20-period volatility; weight 0.3, 0.5, 0.2; assign action levels by percentiles fitted on past data only. In the paper these were forward-return training labels; as a unit they must use trailing returns.
- **Style, timeframe, classes:** swing, about a week; stocks and ETFs in the paper, any liquid class in principle.
- **Data QMX would need:** daily bars; past-only percentile thresholds per instrument.
- **New MIS reading or QML block:** a QML composite-momentum block (the assistant's 'build first' from this paper).
- **Evidence:** author backtest of the full model (six US names, June-August 2024, +2.38 % to +8.08 %, Sharpe 0.86-2.72, no explicit cost schedule; training span overlaps the test dates). The causal signal itself is untested.

### A5-07. Multiscale momentum with a volatility gate; trend quality; price-volume confirmation (QuantaAlpha families)
- **Source:** `chat-22b-saved-diffusion-control-quantaalpha.md:52-57,130-140` (https://www.alphaxiv.org/abs/2602.07085).
- **Signal:** families the evolutionary search produced: (a) agreement of 1-, 5- and 20-day momentum, damped in stressed volatility (a simpler volatility-ratio-plus-momentum form preferred over an over-engineered one); (b) continuation conditioned on low residual noise and limited price impact; (c) rolling correlation of price and volume changes combined with a short intraday return; (d) normalised overnight gap with intraday acceptance or rejection and abnormal volume; (e) regime-filtered reversal and exhaustion (shown brittle when regimes rotate).
- **Style, timeframe, classes:** daily cross-sectional stocks in the paper; (c) and (d) are the nearest to intraday ideas for index CFDs and stocks.
- **Data QMX would need:** daily or intraday OHLCV and VWAP, a point-in-time universe, real volume (not tick counts) for (c) and (d).
- **New MIS reading or QML block:** QML blocks for gap acceptance and price-volume co-movement; a volatility-ratio gate.
- **Evidence:** author backtest, CSI 300: IC 0.0472, excess 4.68 %, IR 0.6453, drawdown 11.8 % after 0.20 % round trip; a corrected rerun of a reused pipeline gave -0.2 % (different protocol). A combined-momentum example raised return but worsened drawdown.

### A5-08. Multi-asset rotation with regime as a risk gate, and KAMA trend timing (FinRL-X)
- **Source:** `chat-22d-saved-labelunbalance-finrlx.md:54-64,139-141` (https://www.alphaxiv.org/abs/2603.21330).
- **Signal:** weekly rotation that picks at most two of Growth, Real Assets and Defensive groups by information ratio against QQQ, allocates within groups by residual momentum, and uses regime indicators only as risk gates; separately, trend or KAMA-based timing scales a base allocation.
- **Style, timeframe, classes:** weekly and daily; US equities and ETFs (index, commodity, defensive exposure).
- **Data QMX would need:** ETF and index prices, group map, regime reading.
- **New MIS reading or QML block:** a KAMA timing block; regime reading as gate.
- **Evidence:** author backtest 2018-2025, 10 bp per side: rotation Sharpe 1.10, drawdown -21.46 %; DRL allocation with timing Sharpe 0.89 vs 0.55 without; rolling Nasdaq-100 top-25 % selection Sharpe 0.93, drawdown -38.95 %; short paper-trading run +19.76 % (pipeline check, not alpha).

### A5-09. Evolved allocation score: normalised Sharpe, momentum rank, volatility and a drawdown penalty (EvolveTrade)
- **Source:** `chat-22c-saved-marketsenseai-evolvetrade.md:44` (https://www.alphaxiv.org/abs/2609.17632).
- **Signal:** one evolved policy scored assets on normalised Sharpe, momentum rank, normalised volatility and a drawdown penalty, then set weights with a capped softmax; in changing regimes the agent began computing VaR, EMA, RSI and SMA.
- **Style, timeframe, classes:** daily-close allocation; 15 US blue chips plus cash.
- **Data QMX would need:** daily bars; 20- and 60-day returns, volatility, drawdown, ATR.
- **New MIS reading or QML block:** a capped-softmax allocation block (allocator, not entry).
- **Evidence:** author backtest, one-month windows, -6.60 % to +6.84 %; one evolved run, not a framework rule.

### A5-10. Moving-average crossover baselines (SMA 50/200; MA20/MA60 ranked)
- **Source:** `chat-11-backtest-overfitting-validation.md:208`; `chat-22e-saved-quantharness-tradingr1.md:26`.
- **Signal:** SMA(50,200) crossover on liquid ETFs; MA20 above MA60, scored by max(MA20/MA60 - 1, 0), top 20 equal weight, next-session execution.
- **Style, timeframe, classes:** daily trend; ETFs and stocks.
- **Data QMX would need:** adjusted daily prices, dividends, costs.
- **New MIS reading or QML block:** no; useful as control units and baselines.
- **Evidence:** idea (examples in papers, not evidence of profit).

## Factors and cross-section (daily stocks)

### A5-11. Classic daily factor families and rank-IC sleeves found by agent search
- **Source:** `chat-11-backtest-overfitting-validation.md:207-212`; `chat-17-self-configuring-parameters.md:167,176` (What survives honest evaluation? 2608.27734).
- **Signal:** RSI plus volume-z-score contrarian ranked monthly; 126-day momentum, low volatility, short-term reversal; volatility breakout; oscillator mean reversion; quintile long-short rank-IC sleeves on value, liquidity, volatility, momentum.
- **Style, timeframe, classes:** daily to monthly cross-sectional stocks.
- **Data QMX would need:** point-in-time prices, constituents, delistings, borrow, publication lags, turnover costs.
- **New MIS reading or QML block:** no (QMX has no stock cross-section route today).
- **Evidence:** author backtest; negative overall: on 453 stocks classic factors had DSR at most 0.32, search PBO 0.83, and 0 of 5 LLM-found volatility-breakout strategies (OOS Sharpe 0.59-0.70) survived deflation. Duplicate of A4 #22.

### A5-12. Agent-mined OHLCV base families (AlphaAgent)
- **Source:** `chat-22a-saved-alphaagent-mass.md:20,102-104`.
- **Signal:** intraday return, daily return, 20-day relative volume and normalised daily range as base factors; intraday return, range and relative volume are the nearest short-horizon raw material.
- **Style, timeframe, classes:** daily stock ranking (next-day return target).
- **Data QMX would need:** daily or intraday OHLCV, point-in-time universe, costs.
- **New MIS reading or QML block:** range and relative-volume blocks exist in part (RVOL is a dictionary concept).
- **Evidence:** author backtest, 11.00 % and 8.74 % excess, IR 1.488 and 1.0545, drawdown 9.36 % and 9.10 %, fees but no slippage. Duplicate of A4 #2 and the synthesis seed.

### A5-13. Consensus minus disagreement across differently informed views (MASS)
- **Source:** `chat-22a-saved-alphaagent-mass.md:32-44,134` (https://www.alphaxiv.org/abs/2505.10278).
- **Signal:** Signal = alpha x weighted agreement - (1 - alpha) x weighted disagreement among investor types; high disagreement linked to overpricing under short-sale limits.
- **Style, timeframe, classes:** weekly stock selection (A-shares); as a reading, agreement across QMX's own units per instrument.
- **Data QMX would need:** per-view signals per instrument, timestamped.
- **New MIS reading or QML block:** an agreement-and-disagreement reading over units (catalogued as component A5-topup-064).
- **Evidence:** author backtest, 2023 returns 2.16 %, 4.95 %, 1.17 % with drawdowns 11.98-19.06 %; type weights fitted on 5-day RankIC. Duplicate of A4 #4 and the synthesis seed.

### A5-14. AI-exposed equity ranker traded only while a model-health gate passes
- **Source:** `chat-04-drawdown-controlled-sizing.md:138,152` (When Alpha Breaks, https://www.alphaxiv.org/abs/2603.13252).
- **Signal:** a cross-sectional ranker on AI-exposed US stocks, switched on and off by a point-in-time health gate built from its own matured prediction errors, with a tail cap on the most uncertain positions.
- **Style, timeframe, classes:** daily to weekly; US single stocks.
- **Data QMX would need:** matured live-style prediction errors, point-in-time features, returns, turnover, costs.
- **New MIS reading or QML block:** a model-health reading per unit (risk side catalogued as A5-topup-015).
- **Evidence:** author backtest on a narrow universe: gate AUROC 0.721 vs 0.449 for VIX percentile; final-period Sharpe 0.375 -> 0.925 with the cap.

### A5-15. Filing-risk downgrade with deteriorating momentum as an exposure cut (MarketSenseAI)
- **Source:** `chat-22c-saved-marketsenseai-evolvetrade.md:20,26-30`.
- **Signal:** structured changes in profitability, leverage, liquidity, disclosed risk and guidance from filings and earnings calls, combined with weakening price momentum, to reduce single-stock exposure.
- **Style, timeframe, classes:** monthly; single stocks.
- **Data QMX would need:** filings and transcripts with publication timestamps, five quarters of financials, prices.
- **New MIS reading or QML block:** a fundamentals-risk reading per stock (agent output under the expiring evidence contract, A5-topup-070).
- **Evidence:** author backtest of the whole monthly pipeline (S&P 100 equal-weight 53.2 % vs 42.3 %, cap-weighted 123 % vs 73.5 % with drawdown 13.8 % vs 9.7 %); the component signal itself was not tested; no documented walk-forward.

## Intraday and scalping

### A5-16. Fee-band three-class order-book model for one-minute futures moves
- **Source:** `chat-22d-saved-labelunbalance-finrlx.md:18-24,91-117` (Label Unbalance in HFT, https://www.alphaxiv.org/abs/2503.09988); `chat-14-early-exit-meta-labelling.md:189`.
- **Signal:** a 60-second window of 13 features sampled every 0.5 seconds (recent mid mean, volatility, skew, kurtosis, volume activity, quoted spread, return-volume beta, illiquidity) predicts whether the next minute's mid move clears the fee band up or down; fixed class weights or a cost-sensitive loss help.
- **Style, timeframe, classes:** scalper, one minute; exchange futures (six Chinese contracts). Not CFDs or spot FX without a real book.
- **Data QMX would need:** half-second book and trade data, fee schedule, a natural-mix calibration set.
- **New MIS reading or QML block:** QML blocks for the 13 features; decision rule catalogued as A5-topup-074.
- **Evidence:** author backtest, classification only, 20 trading days, no strategy returns. In the synthesis seeds and A4 #17 (title only).

### A5-17. Crypto one-minute OHLCV direction model with fractional differentiation and triple-barrier labels
- **Source:** `chat-14-early-exit-meta-labelling.md:17,87,190` (https://www.alphaxiv.org/abs/2411.12753).
- **Signal:** supervised autoencoder on fractionally differentiated one-minute OHLCV plus macro and commodity features, labelled by triple barriers, trading 10-, 20- and 30-minute horizons.
- **Style, timeframe, classes:** intraday crypto (three coins).
- **Data QMX would need:** one-minute crypto bars, macro and commodity series aligned point in time, realistic fills.
- **New MIS reading or QML block:** a fractional-differencing QML block; could act as a primary signal feeding a meta-labeller.
- **Evidence:** author backtest over a bullish 2020-22: 20-minute portfolio 619.80 % vs 595.24 % buy-and-hold; 30-minute IR 2.56, drawdown 23.55 % vs 59.46 %; no slippage, perfect barrier fills.

### A5-18. Post-deleveraging BTC rebound that taker flow and basis fail to confirm (AQuA)
- **Source:** `chat-17-self-configuring-parameters.md:174`.
- **Signal:** after a sharp open-interest drop and high-volume unwind, a rebound without taker-flow and basis recovery is more likely to fail.
- **Style, timeframe, classes:** crypto perps, 5-minute bars.
- **Data QMX would need:** price, volume, open interest, basis and funding, taker buy and sell flow.
- **New MIS reading or QML block:** open-interest-change and taker-imbalance blocks.
- **Evidence:** author backtest; validation IC about 0.190 for the combined factor system, not a standalone return. Duplicate of A4 #1.

### A5-19. Intraday US equity cross-sectional long-short at 30 minutes (AQuA)
- **Source:** `chat-17-self-configuring-parameters.md:175`.
- **Signal:** multiscale price and volume scores, sector-neutral, threshold longs and shorts, volatility-targeted.
- **Style, timeframe, classes:** intraday single stocks.
- **Data QMX would need:** point-in-time equity bars, sectors, turnover costs, a stock venue.
- **New MIS reading or QML block:** no.
- **Evidence:** author backtest, Sharpe 2.15 / 2.50 / 2.00, positive each year 2021-25 at 2 bp two-leg cost. Duplicate of A4 #21.

### A5-20. Supertrend with tuned ATR period and multiplier (weak)
- **Source:** `chat-17-self-configuring-parameters.md:173`.
- **Signal:** ATR Supertrend crossover.
- **Style, timeframe, classes:** daily stocks.
- **Evidence:** author backtest, in-sample optimisation only. Duplicate of A4 #20.

### A5-21. MNQ first-bar edge with fixed time exits; Asia expansion bars already spent
- **Source:** `research/R8-gap-topup.md:229-251` (Mesfin 2605.04004, read).
- **Signal:** the two signal families that passed used fixed time exits of about 60-65 minutes; the London signal's edge sits inside the first 15-minute bar (one-bar delay flips t +4.30 to -2.78); Asia expansion-bar continuation is t -11.5; an opening-range pullback stopped out 80.7 % of the time at 20 points.
- **Style, timeframe, classes:** intraday 5-minute; micro index futures (gold weaker).
- **Data QMX would need:** 5-minute bars, ticks for the delay test, 2-point round-trip friction.
- **New MIS reading or QML block:** an edge-versus-time curve per unit (catalogued as A5-topup-086).
- **Evidence:** author backtest with walk-forward; 53+ settings tried. Duplicate of A1 #9, A2 #3-5 and A3 U-A3-12/13; R8 adds the time-exit reading.

## Options and volatility

### A5-22. Short-dated SPX put writing with VIX-based sizing
- **Source:** `chat-12-safe-derisk-rerisk.md:155` (Sizing the Risk, https://www.alphaxiv.org/abs/2508.16598).
- **Signal:** sell 0-5 DTE SPXW puts; far out-of-the-money short-dated configurations had higher information ratios and lower drawdowns than near-the-money ones; size by Kelly, VIX or a hybrid.
- **Style, timeframe, classes:** short-volatility, days; index options (no QMX route today).
- **Data QMX would need:** option surfaces, greeks, implied and realised volatility, spread and depth, fills, margin, crash scenarios.
- **New MIS reading or QML block:** a VIX-rank reading; options would need a new venue route.
- **Evidence:** author backtest; out-of-sample year 2024 only, not a dislocation sample; short-put tail risk not made safe by Sharpe.

### A5-23. SPX short straddles with a learned hold-or-exit policy
- **Source:** `chat-14-early-exit-meta-labelling.md:187` (https://www.alphaxiv.org/abs/2610.13126).
- **Signal:** a short-straddle unit whose exit is chosen by a classifier on volatility-risk-premium proxies, option spread and liquidity, moneyness, time to expiry, holding time and current P&L.
- **Style, timeframe, classes:** short-volatility, multi-day; index options.
- **Data QMX would need:** 30-minute SPX option quotes and position state.
- **New MIS reading or QML block:** none in today's classes; exit mechanism catalogued as A5-topup-043.
- **Evidence:** author backtest, locked 2024-26: 35.01 % vs 11.56 % hold-to-expiry, Sharpe 1.651 vs 0.441, drawdown 4.04 % vs 12.82 %; no 2008- or 2020-style shock in the test.

## Calendar and events

### A5-24. Calendar effects (negative seed)
- **Source:** `chat-11-backtest-overfitting-validation.md:209`; `chat-12-safe-derisk-rerisk.md:156` (Promote 2611.03384 market replay).
- **Signal:** turn of month, first and last three trading days, weekday, quarter-end, January, third Friday, on ETF and industry panels.
- **Style, timeframe, classes:** short-horizon calendar rules; ETFs and indices.
- **Data QMX would need:** exchange calendars, next-executable prices, costs.
- **New MIS reading or QML block:** calendar states exist in part.
- **Evidence:** controlled test, negative: none of 24 candidates crossed the funded promotion threshold; a reversed-industry January rule passed only under repeated unadjusted testing and then lost after costs.

### A5-25. EIA inventory surprises move crude and gas together; OPEC decision type
- **Source:** `research/R8-gap-topup.md:445-469` (Halova, Kurov, Kucher 2014; Loutia, Mellios, Andriosopoulos 2016; snippets).
- **Reading:** inventory surprises (corrected for analyst forecast error) move energy futures more than older studies found, about 10 % in gas per 1 % inventory shock (units to check), and crude surprises move gas and the reverse; OPEC effects are stronger for cuts and holds and differ for WTI and Brent.
- **Style, timeframe, classes:** event windows; crude and natural gas futures and CFDs.
- **Data QMX would need:** EIA schedule as data, consensus inventory forecasts, OPEC calendar with decision type, tick data around releases.
- **New MIS reading or QML block:** an MIS inventory-surprise reading and an OPEC decision-type calendar field (overlay catalogued as A5-topup-094).
- **Evidence:** author backtest (event studies, abstract-level reading).

### A5-26. Trading ahead of commodity index roll windows (Goldman roll)
- **Source:** `research/R8-gap-topup.md:471-478` (Mou 2010, SSRN 1716841, abstract).
- **Signal:** positions taken ahead of the main index roll days earned positive-skew excess returns; index investors gave up about 3.6 % a year to the impact.
- **Style, timeframe, classes:** swing around monthly roll windows; energy and other index commodities (futures).
- **Data QMX would need:** index roll calendars, contract-level prices.
- **New MIS reading or QML block:** a roll-window calendar state per contract.
- **Evidence:** author backtest, Sharpe up to 4.39 for 2000 to March 2010 (abstract only).

## Crypto structure

### A5-27. Perpetual premium from long positional and short basis traders
- **Source:** `chat-21-multi-agent-market-simulation.md:140,155` (Agent-Based Simulation of a Perpetual Futures Market, https://www.alphaxiv.org/abs/2501.09404).
- **Signal:** with long positional traders and short basis traders, funding incentives keep the perp linked to spot while a premium persists: a candidate basis and funding mechanism to test on real venues.
- **Style, timeframe, classes:** carry and basis, hours to days; crypto perps against spot.
- **Data QMX would need:** venue funding history, basis, open interest, fees, liquidation data.
- **New MIS reading or QML block:** a funding-carry and basis reading (planned in the crypto pack).
- **Evidence:** simulation (no agent wealth, no liquidation engine). Related to A4 #19.

### A5-28. Trend and relative value across crypto pairs
- **Source:** `chat-05-allocation-across-strategies.md:203` (Systematic Trend-Following with Adaptive Portfolio Construction 2602.11708; Dynamic Multi-Pair Trading with DRL 2606.04574).
- **Signal:** directional trend across major coins, or market-neutral pairs, with funding, leverage, venue and weekend controls.
- **Style, timeframe, classes:** intraday to swing; crypto.
- **Data QMX would need:** venue prices and trades, funding, open interest, fees, borrow, depth, 24/7 timestamps.
- **New MIS reading or QML block:** pair-spread blocks.
- **Evidence:** idea (papers named for inspection, not summarised).

## Readings for risk and placement

### A5-29. Market-stress early warnings: ETF-underlying divergence, correlated drops, order-flow toxicity
- **Source:** `chat-19-llm-agents-risk-monitoring.md:140` (FARSIGHT 2609.19705); SwingGuard 2610.12988.
- **Reading:** VIX level, correlated-asset drops, order-flow toxicity, liquidity stress and divergence between an ETF and its underlying as candidate early warnings; SwingGuard adds drawdown, ATR, momentum, exposure, on-chain and news anomalies, source diversity and six-hour accumulation as triggers for a deeper diagnosis.
- **Style, timeframe, classes:** risk readings for all classes; ETF-underlying divergence for indices and commodities with listed ETFs; on-chain for crypto.
- **Data QMX would need:** ETF and underlying prices aligned, volatility index, order-flow data where a book exists, on-chain feeds.
- **New MIS reading or QML block:** an ETF-premium (divergence) reading would be new; the rest overlap A3 detectors.
- **Evidence:** idea for the FARSIGHT list (recommendations); SwingGuard author backtest. SwingGuard also A4 #10.
