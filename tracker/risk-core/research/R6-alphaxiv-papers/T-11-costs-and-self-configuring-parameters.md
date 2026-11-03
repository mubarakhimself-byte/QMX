# T-11: Costs and self-configuring parameters

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`. Read after the operator's plan upgrade; kept
short (two new papers plus cross-references).

## The short answer for QMX

- Backtests overstate. Adding slippage and funding to a crypto perpetual strategy cut CAGR from
  5.2 (zero cost) to 4.3 (fees only) to 2.7 (full costs) in one audited case (AutoQuant). A three-stage
  benchmark (backtest, exchange paper trading, real-money live) found strong backtests did not
  transfer, paper trading was closer to live but still off, and no AI method beat the market live.
- Tune parameters for robustness, not for the best number: a second screening stage over rolling
  windows and a 9-scenario cost grid (fees and funding varied) picked settings with lower drawdown
  but lower return; residual PBO stayed at 0.586. Robust selection is a fragility filter, not an
  alpha source.
- Self-configuring parameters need the same honesty as any search: count trials, hold a blind
  window, accept that the result is "less fragile", not "better".
- Paper trading on the real venue is a required stage between backtest and money (also in Steward).

## Papers

### 1. AutoQuant: An Auditable Expert-System Framework for Execution-Constrained Auto-Tuning in Cryptocurrency Perpetual Futures
- Link: https://www.alphaxiv.org/abs/2512.22476 (2025, Deng, Guangzhou College of Commerce)
- Method in plain words: one execution convention for backtest, replay and monitoring (signal at bar
  close t, position from bar t+1); net return = raw - fees - slippage - funding; leverage and
  notional caps shrink size automatically. Stage I: Bayesian optimisation (TPE) of a 4-hour momentum
  family on a training window. Stage II: screen the candidate pool across rolling windows and a
  nine-scenario cost grid with fixed rules (average monthly return >= 0.5%, worst-scenario month
  >= 0, mean max drawdown <= 30%, switch density <= 12%). A live guard issues ok / watch / kill.
- Inputs: 4-hour OHLCV and 8-hour funding for BTC, ETH, SOL, AVAX perpetuals, 2019-2025; 4 bp taker
  fee, 2 bp slippage. Outputs: configurations, per-bar ledgers, audits.
- Evidence: cost ablation (BTC): CAGR 5.225 zero-cost, 4.308 fees-only, 2.726 full cost; Sharpe
  2.71, 2.51, 2.05. Two-stage selection lowered drawdown (validation 0.231 vs 0.318) with lower
  return; on AVAX drawdown fell from 0.62 to 0.10 in validation. Post-ETF blind hold-out:
  buy-and-hold beat both. PBO 0.586; deflated Sharpe weak after 360-3,240 effective trials.
  Offline vs live-style replay reconciled to zero differences.
- Where it fails: one strategy family; linear costs, no impact; validation window reused in Stage II;
  limited paper trading of the live guard.
- Across instrument classes: funding is a crypto-perpetual cost; the analogues are swap/rollover for
  FX and CFDs and roll cost for futures. Each class needs its own cost terms in the same ledger.
- What QMX could borrow: (a) one execution and cost ledger shared by backtest, paper and live, with
  reconciliation tests; (b) a cost-stress grid (fees, spread, swap/funding x 0.5-2) in every
  backtest; (c) Stage II robustness rules as defaults for any auto-tuning; (d) ok / watch / kill guard.
- Layer: X1, X2, X5, X6.

### 2. Can AI Make Money in Crypto? Measuring the Gap from Backtests to Real Markets
- Link: https://www.alphaxiv.org/abs/2609.34510 (2026, Yu, Zhou, Ding et al.; CUHK, USTC, SMU and others)
- Method in plain words: one benchmark running ML, RL, LLM and agent trading methods through three
  stages: historical backtest, prospective paper trading on an exchange, and real-money live trading.
- Evidence: strong backtests did not reliably transfer; paper trading was closer to live than
  backtesting but a gap remained under real money; none of the methods sustained market-beating
  performance live. Open-source system and a public, updating leaderboard.
- Where it fails: crypto only; details of sizes and costs per method not extracted here.
- Across instrument classes: crypto; the stage design is generic.
- What QMX could borrow: make "exchange paper trading on the real venue" a mandatory stage with its
  own pass rule, and measure the backtest-to-paper and paper-to-live gaps per strategy as an
  observable.
- Layer: X5, X6.

## Also relevant, read under other topics
- Cost-aware filter (T-02, 2606.00060): no trade unless expected move > 2 x round-trip cost.
- Friction floors per instrument (T-02, 2605.04004): MNQ 2 points, MGC 0.5 points; units matter.
- Crypto fees bind, not spreads (T-02, 2608.21888); taker fee kills the imbalance edge (T-02, 2502.18625).
- Impact = order flow / depth; worst at the open and around news (T-03, 1011.6402, 2508.06788).
- Netting across strategies lowers real turnover (T-01, 2412.03305).
- Slow scale estimates beat adaptive ones inside a sizing rule (T-05, 2608.01494).
- Promote ledger (T-09, 2611.03384): costs known before each scored return; next-session start.

## Not read
- 2606.08285 Execution realism and reproducibility in LLM trading research (audit).
- 2603.29086 Realistic market impact for RL trading environments.
- 2609.04712 Convex cross-impact over time (commodities and macro).
- Self-configuring parameters across many instruments (hierarchical pooling of parameters) had no
  strong finance paper in the search; Pav's James-Stein pooling (T-05) is the nearest tool.

## What changes by instrument class
- Crypto perpetuals: funding every 8 hours plus fees; 24/7.
- FX / CFD: spread plus overnight swap; broker-specific; weekend gaps.
- Futures: commission per contract, tick value, roll; session gaps.
- Stocks: commission, spread, borrow for shorts, earnings gaps.

## Combinations
- AutoQuant ledger and cost grid (1) + Promote (T-09): costs fixed before each scored return; cost
  stress decides whether the candidate is even registered.
- Three-stage benchmark (2) + Steward paper deployment (T-04) + operator promotion: backtest ->
  venue paper trading -> small live, each with its own gate.
