# Unit idea bank seeds, cluster A4 (template, agents, telemetry)

Stage A, 3 Nov 2026. Trading signals and market readings found in this cluster's sources (agent and harness papers, agent articles, operator words). They are not risk-and-sizing components and are not ranked. Paper results are the alphaXiv assistant's claims unless R6 read the paper. Some seeds also appear in `research/R4-alphaxiv/R4-alphaxiv-synthesis.md` "Unit and reading seeds"; they are repeated here only where this cluster's sources add detail.

"MIS reading" means a market-state input the MIS could publish. "QML block" means a statistic or signal block in the dictionary.

## 1. Crypto open-interest unwind with missing taker-flow confirmation (AQuA)

- **Source:** AQuA, arXiv 2608.12841, via `research/R4-alphaxiv/chat-18-agent-harness-alpha-discovery.md:150`; R6 read the paper (`research/R6-alphaxiv-papers/T-04-agents-macro-micro-news.md:132-148`).
- **Signal:** open interest unwinds, price rebounds weakly, and taker buy flow fails to confirm the rebound. A falsifiable hypothesis the Idea Miner wrote before building.
- **Style, timeframe, classes:** crypto perpetuals, 5-minute bars, intraday or scalper.
- **Data QMX would need:** per-venue open interest, taker buy and sell volume, 5-minute bars; funding times.
- **New MIS reading or QML block:** yes, an open-interest-change block and a taker-flow imbalance block; possibly an MIS reading "OI unwind" per crypto venue.
- **Evidence:** author backtest. Single factors have IC about 0.026 to 0.037; the headline 0.190 is a combined validation IC, not a costed out-of-sample return.

## 2. Simple, original OHLCV factors combined by a gradient-boosted model (AlphaAgent)

- **Source:** AlphaAgent, arXiv 2502.16789, via `chat-18-agent-harness-alpha-discovery.md:141` and `:151`.
- **Signal:** agent-generated price and volume factors filtered for novelty, hypothesis alignment and low complexity, combined by LightGBM into a top-ranked stock portfolio.
- **Style, timeframe, classes:** daily cross-sectional stocks (CSI 500, S&P 500).
- **Data QMX would need:** daily OHLCV for a point-in-time universe; QMX does not trade cross-sectional stock books today.
- **New MIS reading or QML block:** no; a family of factor blocks if stocks are added.
- **Evidence:** author backtest, 11.0 % (IR 1.5) and 8.74 % (IR 1.05) annual excess after fees, 2021-24; current-index universe, so survivorship may remain.

## 3. Cash or exposure filter that sits out declines (Quant-Arena finding)

- **Source:** Quant-Arena, arXiv 2610.30113, via `chat-18-agent-harness-alpha-discovery.md:144` and `:152`.
- **Signal:** the best agent result profited mainly by staying in cash through the early-2024 decline: a market-exposure filter, not stock picking.
- **Style, timeframe, classes:** index-level timing, daily; A-shares in the paper; could apply to index CFDs or futures units as an overlay.
- **Data QMX would need:** index bars, a regime or trend reading.
- **New MIS reading or QML block:** possibly an index risk-on or risk-off reading; overlaps the regime work in A3.
- **Evidence:** author backtest on a sealed 2024 year; the filtered configuration still underperformed the market (excess return about -6.3 points with -6.8 % drawdown).

## 4. Heterogeneous simulated investors aggregated into one view (MASS)

- **Source:** MASS, arXiv 2505.10278, via `chat-18-agent-harness-alpha-discovery.md:154`.
- **Signal:** many simulated investor agents with different feature access and styles; a learned aggregation of their decisions.
- **Style, timeframe, classes:** stock portfolio construction, A-shares.
- **Data QMX would need:** per-agent feature sets and a training history.
- **New MIS reading or QML block:** no; the assistant suggests it as a stress or diversity mechanism rather than an alpha source.
- **Evidence:** author backtest with predictive metrics only (2023) and a Q1 2025 leakage check; no net Sharpe or drawdown.

## 5. Evolved factor trees for hourly crypto and index constituents (EvoQuantLab)

- **Source:** EvoQuantLab, arXiv 2610.17130, via `chat-18-agent-harness-alpha-discovery.md:22`, `:76-82`, `:142`.
- **Signal:** typed genetic-programming factor trees with LLM-proposed mechanisms, family-diverse elites.
- **Style, timeframe, classes:** hourly crypto; daily CSI 500 and S&P 500.
- **Data QMX would need:** point-in-time bars per venue and constituent lists.
- **New MIS reading or QML block:** factor blocks per discovered family; the paper names no specific family that is proven.
- **Evidence:** author backtest on short windows (crypto 37.91 % annualised, 7.17 % cumulative, -3.23 % drawdown over April to June 2026).

## 6. Semantic factor selection from a timestamped market-state description (Alpha-R1)

- **Source:** Alpha-R1, arXiv 2512.23515, via `chat-18-agent-harness-alpha-discovery.md:25`.
- **Signal:** an RL-trained LLM picks a sparse subset of an existing factor pool by matching factor descriptions to a market-state description; memory frozen before the test.
- **Style, timeframe, classes:** daily stock factors (S&P 500, CSI 300).
- **Data QMX would need:** a described factor library and a timestamped market-state text.
- **New MIS reading or QML block:** a reading-to-block selector; for QMX the nearer analogue is the MIS choosing which units' logic suits a market (placement).
- **Evidence:** author backtest, 2025 one-year test after 10 bp fees (47.87 % and 40.57 %), S&P interval includes zero under two of three block lengths.

## 7. Calibrated firm-day news sentiment (MFAST)

- **Source:** MFAST, arXiv 2609.23703, R6 read (`research/R6-alphaxiv-papers/T-04-agents-macro-micro-news.md:114-130`); `chat-28-F-agents-macro-micro-news.md:142-146` and `:238`.
- **Signal:** timestamped firm news, entity-matched, deduplicated, classified by a decoder LLM, calibrated, aggregated to a firm-day score; gains concentrate in complex articles (negation, guidance, numbers).
- **Style, timeframe, classes:** liquid single stocks, daily to five-day holds. R6: FX, indices and commodities react to macro releases, so a different pipeline is needed there.
- **Data QMX would need:** licensed timestamped news, entity mapping, point-in-time universe, costs, a GPU (54.2 GB peak for LLaMA-3).
- **New MIS reading or QML block:** a news-sentiment reading per stock; not a QML block (model inference).
- **Evidence:** author backtest, post-cutoff out-of-sample June 2024 to January 2026, long-short Sharpe 2.85 (CI 2.31-3.34) after 5 bp and a 10 % ADV cap; deflated Sharpe 2.19; revise-and-resubmit.

## 8. Macro surprise against a timestamped consensus (LiveMacroEval)

- **Source:** LiveMacroEval, arXiv 2608.30110, via `chat-28-F-agents-macro-micro-news.md:130-138` and `:237`.
- **Signal:** hourly pre-release nowcasts compared with the consensus snapshot available just before the release; size and direction of the surprise.
- **Style, timeframe, classes:** event-driven around scheduled releases; FX (pair-relative surprises), indices, rates, metals.
- **Data QMX would need:** release calendar with actuals (the free calendar in `t3-news-calendar-watch` has no actuals, G9 2), vintages, consensus snapshots, quotes around releases.
- **New MIS reading or QML block:** an MIS event-surprise reading per currency or index; ties to the parked news layer.
- **Evidence:** live forecast evaluation (pre-release, November 2025 to March 2026); a forecast score, not a trading return.

## 9. Auction-market order-flow features (ViperQ)

- **Source:** ViperQ, arXiv 2609.13825, via `chat-28-F-agents-macro-micro-news.md:65`, `:78`, `:239`. Also in the R4 synthesis seeds.
- **Signal:** volume-area position, cumulative volume delta slope and divergence, tape velocity, imbalance, fed to an RL policy.
- **Style, timeframe, classes:** short-horizon single stocks and futures with real books; not spot FX or CFDs.
- **Data QMX would need:** trades with aggressor side, session volume profile, book imbalance.
- **New MIS reading or QML block:** QML blocks for CVD and volume-area position; an MIS order-flow regime reading.
- **Evidence:** author backtest on two stocks (TSLA, NVDA) with drawdowns of -27.5 % and -47.8 %; RL, not LLM.

## 10. Daily multi-agent swing stack for BTC and ETH under a fast risk loop (SwingGuard)

- **Source:** SwingGuard, arXiv 2610.12988, R6 read (`T-04-agents-macro-micro-news.md:76-95`).
- **Signal:** daily technical, sentiment, on-chain and macro agents plus a bull-versus-bear debate form a long-only target; a 5-minute deterministic controller caps it.
- **Style, timeframe, classes:** crypto swing, daily targets, long only.
- **Data QMX would need:** 5-minute bars, 7-day news, on-chain data, latest M2 release.
- **New MIS reading or QML block:** on-chain and M2 readings would be new to the MIS.
- **Evidence:** author backtest, August 2024 to January 2025, 15 bp one-way cost; Sharpe 2.98, drawdown 6.44 %, average exposure 31.74 %; no trial count.

## 11. Analyst-report synthesis with a falsifying condition per position (Steward)

- **Source:** Steward, arXiv 2610.30557, R6 read (`T-04-agents-macro-micro-news.md:50-74`).
- **Signal:** a portfolio-manager agent synthesises news, SEC filings, macro series and market data into target weights with conviction and a named invalidating condition; code grading found the synthesis was where value came from.
- **Style, timeframe, classes:** US equities, swing.
- **Data QMX would need:** filings, news, macro series; a stock venue.
- **New MIS reading or QML block:** no; the falsifying-condition idea could become an exit trigger block ("thesis invalidated").
- **Evidence:** author backtest plus a five-month paper-account deployment (102 trading days), not real money.

## 12. Regime-conditioned constraint levels for LLM stock trading (Strat-LLM)

- **Source:** Strat-LLM, arXiv 2605.06024, via `chat-28-F-agents-macro-micro-news.md:64` and `:76`.
- **Signal:** forward-run price, news and annual-report inputs; stricter strategy constraints cut GPT-5's max drawdown from 20.83 % to 11.66 % in its US sample, with effects varying by regime.
- **Style, timeframe, classes:** US stocks, T+1.
- **Data QMX would need:** news and filings; a regime reading.
- **New MIS reading or QML block:** a regime reading to switch constraint levels; overlaps A3.
- **Evidence:** forward-running tests (paper), stock-only.

## 13. Selective forecasting that abstains under uncertainty (FinAbstain)

- **Source:** FinAbstain, arXiv 2607.24875, via `chat-28-F-agents-macro-micro-news.md:261`.
- **Signal:** forecasts from specialist agents with cited evidence; disagreement and retrieval quality decide whether to forecast at all.
- **Style, timeframe, classes:** not stated.
- **Data QMX would need:** multimodal retrieval sources.
- **New MIS reading or QML block:** an "abstain" confidence reading.
- **Evidence:** simulation only (its tables are explicitly simulated).

## 14. A rule strategy and a model that trade only when both agree (MQL5 Self Optimizing EAs Part 17)

- **Source:** MQL5 article 20238, via `research/R5-mql5-corpus-ideas.md:422`.
- **Signal:** an ensemble of a rule-based strategy and a statistical model on shared indicators, entering only on agreement; two unprofitable systems made one profitable one.
- **Style, timeframe, classes:** FX intraday on MT5.
- **Data QMX would need:** bars and indicators already available.
- **New MIS reading or QML block:** a QML combiner block ("both agree") already fits the logic-slot gate.
- **Evidence:** author backtest, mostly in-sample; the gate cuts trades, so exposure effect and skill are not separated.

## 15. Per-symbol agents sharing signals through a coordination layer (MQL5 21115)

- **Source:** MQL5 article 21115, via `research/R5-mql5-corpus-ideas.md:172`.
- **Signal:** each symbol's agent shares its signal with others; a coordination layer enforces portfolio limits; execution and risk stay in MQL5.
- **Style, timeframe, classes:** FX cross-symbol.
- **Data QMX would need:** shared signal bus across units (QMX units stand alone today).
- **New MIS reading or QML block:** possibly an MIS cross-symbol signal-agreement reading.
- **Evidence:** none (no test numbers).

## 16. LLM fine-tuned on pair statistics (MQL5 20329)

- **Source:** MQL5 article 20329, via `research/R5-mql5-corpus-ideas.md:171`.
- **Signal:** a base LLM bought EURUSD at RSI 32 and rode a 200-pip fall; fine-tuning on pair statistics reportedly raised the win rate by about 10 points.
- **Style, timeframe, classes:** FX, EURUSD.
- **Data QMX would need:** per-pair statistics and a fine-tuning setup.
- **New MIS reading or QML block:** no.
- **Evidence:** author backtest in-sample plus one demo week. Shows why an LLM needs instrument-specific statistics; not evidence of edge.

## 17. Earlier conversation's papers on RL and LLM trading (conv-03)

- **Source:** `research/R4-alphaxiv/conv-03-algorithmic-trading-papers.md:22-29` (assistant's list, papers not read): Trading-R1 (2509.11420), MacroHFT memory-augmented RL for crypto HFT (2406.14537), QuantAgent, now listed as QuantHarness, price-driven multi-agent LLMs for HFT (2509.09995), JaxMARL-HFT simulation (2511.02136), label imbalance in HFT (2503.09988), xLSTM DRL stock trading (2503.09655).
- **Signal:** RL and LLM policies for high-frequency crypto and stock trading.
- **Style, timeframe, classes:** HFT and scalping, crypto and stocks.
- **Data QMX would need:** tick or order-book data per venue; GPU simulation for JaxMARL.
- **New MIS reading or QML block:** unknown until read.
- **Evidence:** idea (titles and one-line claims only).

## 18. An agent that reads charts like a human trader, and a model trained on one sniping window to find similar ones (operator, parked)

- **Source:** operator M10 (`seeds/SEEDS.md` D44). He ruled it out of this session: "that's what the lab inside KMX is for".
- **Signal:** a strong model with a trading knowledge base looks at charts and proposes trade ideas; or a model trained on a known sniping window searches for similar windows.
- **Style, timeframe, classes:** discretionary-style ideas across classes; sniping windows at session opens.
- **Data QMX would need:** chart images or bars, a curated knowledge base, labelled window examples.
- **New MIS reading or QML block:** a "similar window" reading would be new.
- **Evidence:** idea (parked by him).

## 19. Funding-carry and cross-sectional FX signals named as research skills (conv-02)

- **Source:** `research/R4-alphaxiv/conv-02-ai-quant-trading-design.md:464-465` (assistant's starter skill list: `research_fx_cross_sectional_signal`, `research_crypto_perp_carry_signal`).
- **Signal:** cross-sectional FX signals; crypto perpetual funding carry.
- **Style, timeframe, classes:** FX multi-pair; crypto perpetuals, holding through funding times.
- **Data QMX would need:** funding history per venue (the CCXT refresh writes funding clocks, G9 5.1), FX swap points.
- **New MIS reading or QML block:** a funding-carry reading for crypto; a currency-strength reading for FX (planned on This PC, G9 4.1).
- **Evidence:** idea (named only).

## 20. Supertrend trend-following with tuned ATR period and multiplier (weak)

- **Source:** arXiv 2405.14262, via `research/R4-alphaxiv/chat-17-self-configuring-parameters.md:173`.
- **Signal:** buy when the close crosses above the ATR-based Supertrend line; sell, exit or reverse below it.
- **Style, timeframe, classes:** daily or slower stock bars (Nifty 50, HUL, Infosys, Microsoft, NVIDIA).
- **Data QMX would need:** OHLC bars; an ATR block (atr-wilder exists in the dictionary, G8 3.4).
- **New MIS reading or QML block:** a Supertrend QML block.
- **Evidence:** author backtest, in-sample maximum-profit optimisation only; the default run lost 1.16 % overall and Infosys did worse optimised than default. Too weak to use the tuned values.

## 21. Intraday cross-sectional US equity long-short at a 30-minute horizon (AQuA model track)

- **Source:** AQuA, arXiv 2608.12841, via `chat-17-self-configuring-parameters.md:164` and `:175`; R6 read (`T-04-agents-macro-micro-news.md:132-148`).
- **Signal:** multiscale price and volume history combined into per-stock scores, sector-neutralised, threshold longs and shorts, volatility-targeted.
- **Style, timeframe, classes:** intraday single stocks, 30-minute forecasts.
- **Data QMX would need:** point-in-time equity prices and volume, sector labels, explicit turnover costs, a stock venue.
- **New MIS reading or QML block:** no; a model-based unit, outside QMX's current class mix.
- **Evidence:** author backtest, held-out 2021-25 Sharpe 2.15, 2.50 with volatility targeting, 2.00 fully walk-forward, positive every year at 2 bp two-leg cost; R6 notes retail costs would erase much of it and trials were not deflated.

## 22. Volatility-breakout family found by LLM search, which did not survive deflation

- **Source:** What survives honest evaluation?, arXiv 2608.27734, via `chat-17-self-configuring-parameters.md:167` and `:176`.
- **Signal:** five independent LLM runs converged on volatility-breakout strategies on 453 US stocks; other candidate families were momentum, low volatility, short-term reversal, oscillator mean reversion and volume effects.
- **Style, timeframe, classes:** daily US stocks.
- **Data QMX would need:** point-in-time daily stock data with costs.
- **New MIS reading or QML block:** no.
- **Evidence:** author backtest, out-of-sample Sharpe 0.59-0.70 and +26-33 %, but 0 of 5 survived deflation for search intensity. Kept as a negative seed: a profitable window is not a certified edge.

## Coverage note

R4 chats used for this file: chat-18 (all three turns, re-read after it grew), chat-28, conv-02, conv-03, plus chat-06, chat-10, chat-17 and chat-07 for template and telemetry pieces. Seed 1 (AQuA open-interest unwind) also appears in chat-17 at line 174 with basis and funding recovery added to the confirmation test. R4 chats 02, 04, 05, 09, 11, 12 and 15 appeared or grew during this run and are outside this cluster or were not read.
