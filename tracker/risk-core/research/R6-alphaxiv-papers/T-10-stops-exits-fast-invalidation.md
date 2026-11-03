# T-10: Stops, exits and fast invalidation

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`.

PARTIAL: two papers were read before the alphaXiv free-plan quota ran out.

## The short answer for QMX

- Exits are usually the least tested part of a system and they matter: on 900+ replayed crypto
  trades, moving from a 25% stop to a 10% stop with earlier partial profit and a longer stale-close
  lifted Sharpe from 0.42 to 0.53; adding a 1 ATR stop / 2 ATR take-profit and a "cut size to 0.25
  after 2 losses" breaker lifted it to 0.65. But this was an in-sample grid of 8,960 settings, with
  no deflation, and a chronological test was dropped after a war-period shock gave test Sharpe near -5.
- Treat exit tuning as a search like any other: count trials, test forward, keep the result as a
  candidate default, not a fact.
- Theory: with a trailing stop, the best entry and exit levels shift with volatility; higher
  volatility raises the optimal sell level and lowers the buy level (Leung and Zhang).
- From other topics: the invariant core in Steward (T-04) put stops at 2 ATR, widened any stop
  under 1 ATR, sized to 0.5% of equity at the stop, and required reward/risk >= 1.2 after price
  moves. Each trade carried a named "falsifying condition" (fast invalidation by thesis, not only
  by price). Stop distance and size are one decision: size = risk budget / stop distance.

## Papers

### 1. Optimal Stop-Loss and Take-Profit Parameterization for Autonomous Trading Agent Swarm
- Link: https://www.alphaxiv.org/abs/2604.27150 (2026, Li, Laryea, Ihlamur; Oxford / Vela Research)
- Method in plain words: replay each closed trade's price path under alternative exit rules (stop,
  trailing activation and distance, partial take-profit level and fraction, stale close, ATR stops,
  consecutive-loss breaker). 8,960 first-pass settings, then ATR and breaker refinements.
- Inputs: 900+ closed trades with price paths from a 10-20 agent crypto swarm (15-minute refresh),
  one shared exit layer. Outputs: Sharpe, profit factor, drawdown per setting.
- Evidence: baseline (25% stop, 3% trail start, 2% trail, 5% partial at 50%, 24 h stale) Sharpe 0.419.
  Best first pass (10% stop, 48 h stale, 75% partial) 0.525; all top five used a 10% stop and 48 h.
  Best second pass with 1.0 ATR stop, 2.0 ATR take-profit and a 0.25x size cut after 2 losses 0.653.
  Randomised split used after the chronological split was dominated by a war-period shock.
- Where it fails: in-sample, large grid, randomised split leaks regimes, no deflated Sharpe; volatility
  tier results implausible; one venue and swarm.
- Across instrument classes: percentage stops of 10% only make sense for crypto; FX and index
  scalpers need stops in ATR or spread multiples.
- What QMX could borrow: a counterfactual exit replayer over each strategy's own trade paths, with
  trial counting (T-09); ATR-scaled stops and take-profits; a stale-close timer; a consecutive-loss
  size cut as a soft brake.
- Layer: X1, X3.
- Assistant (conv-01): named as a reading-list item; no specific claim to check.

### 2. Optimal Trading with a Trailing Stop
- Link: https://www.alphaxiv.org/abs/1701.03960 (2017, revised 2019, Leung and Zhang; UW / Columbia)
- Method in plain words: when to buy and then sell an asset whose position is closed automatically
  once price falls a set percentage from its running high (a trailing stop). Solved as an optimal
  double stopping problem for general diffusions; example with an exponential Ornstein-Uhlenbeck
  (mean-reverting) price.
- Evidence: theory and sensitivity analysis. As volatility rises, the optimal sell level rises and
  the buy level falls.
- Where it fails: one asset, continuous prices, no gaps or costs beyond a fixed fee.
- Across instrument classes: most relevant to mean-reverting instruments (spreads, some FX crosses).
- What QMX could borrow: the trailing stop changes the best entry, so entry and exit parameters must
  be tuned together, not separately.
- Layer: X1.

## Not read (quota)
- https://www.alphaxiv.org/abs/1411.5062 Optimal Mean Reversion Trading with Transaction Costs and
  Stop-Loss Exit (Leung and Li).
- Kaminski and Lo "When do stop-loss rules stop losses?" (Journal of Financial Markets 2014) is cited
  by paper 1; not on arXiv here.

## What changes by instrument class
- Crypto: wide percentage stops; ATR overlays added the most.
- FX/CFD: stops must clear spread plus noise; express in spread and ATR multiples.
- Index futures: gap and news windows make stop fills unreliable (T-03, T-06); stops are not hard
  loss bounds.
