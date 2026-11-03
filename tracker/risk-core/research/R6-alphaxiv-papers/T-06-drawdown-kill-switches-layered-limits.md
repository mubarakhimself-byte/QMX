# T-06: Drawdown control, kill switches, layered limits, safe de-risking

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`. Overlaps R4 chat-06.

## The short answer for QMX

- Size from the cushion, not from equity. Every policy that keeps drawdown below a hard limit d_max
  on every possible path has the form: exposure = cushion x direction, where
  cushion = equity - (1 - d_max) x high-water mark. Among those, the best policy earns at least as
  much as any fixed-fraction policy that meets the same limit (Hsieh 2026). This is the formal form
  of "cut size as you approach the limit". It needs a bound on the worst one-step return per
  instrument (gap risk).
- Know how deep a normal drawdown is before cutting. For a Gaussian P&L with Sharpe S, the
  one-in-ten max drawdown over 1 year is about 1.32 annual vols at S = 1 and 0.97 at S = 2.
  Sharpe uncertainty (a 3-year track) raises worst cases by 21-48%; short-vol / mean-reversion
  books are 30% deeper; trend books stay under water about 10% longer (Landolfi 2026).
- Halts must sit outside the model. Across 15 academic LLM trading designs, none had a halt that
  skips LLM inference, and none of 7 code releases enforced a stop or position limit outside the
  LLM. In simulation, hard loss limits and a fast path outside the model removed agent-caused
  crashes; the US exchange pause (LULD) never triggered in the fake-headline runs (FARSIGHT).
- A breached limit must halt the strategy, not sell everything. In FARSIGHT, agents selling after
  true bad news overshot the new value by 9.6-11.1%; with halts the price ended within 0.1%.

## Papers

### 1. On Control of Drawdown: Robust Invariance and Optimality
- Link: https://www.alphaxiv.org/abs/2609.23272 (2026, Hsieh, National Tsing Hua)
- Method in plain words: account value V, its running peak V_max, a drawdown limit d_max. Given a
  known bounded set of possible one-step returns per asset (for example a box [X_min, X_max]),
  an action is safe if the worst loss plus costs is no larger than the cushion
  C = V - (1 - d_max) V_max. Every safe policy is cushion x a normalised direction. With
  independent returns, the best safe policy comes from a one-dimensional Bellman recursion.
- Inputs: return support (worst and best one-step move per asset), cost rates, d_max.
  Outputs: allowed exposure each step.
- Evidence: proofs; illustration on SPY and TLT daily returns 2015-2026 with 0.5 bp costs: the
  drawdown-modulated policy beat the best constant-gain policy at every positive drawdown limit, for
  21, 63 and 252-day horizons.
- Where it fails: the guarantee is only as good as the return support. A gap beyond X_min (weekend,
  news, crypto wick, broker outage) breaks it. Finite horizon; independence assumed for optimality.
- Across instrument classes: X_min must be set per class and per holding time: FX majors small,
  crypto and single stocks large, index CFDs over weekends large.
- What QMX could borrow: account-level and sleeve-level sizing as cushion-based modulation; the
  cushion uses the true high-water mark (never reset by a restart); X_min from stress scenarios
  (X4), not from recent volatility.
- Layer: X2, X3, X4.
- Assistant (chat-06): it described the 2023 restart paper (same author) as scaling exposure with
  the cushion as drawdown nears the bound. Consistent with this 2026 paper's framing. The 2023 paper
  itself was not read here.

### 2. Drawdown Risk Beyond Brownian Motion: A Monte-Carlo Framework, Non-Gaussian Extensions, and Long Memory
- Link: https://www.alphaxiv.org/abs/2608.00127 (2026, Landolfi, Epiphany), building on
  Rej, Seager, Bouchaud "You are in a drawdown. When should you start worrying?" (1707.01457, not
  read directly).
- Method in plain words: simulate equity curves for a given Sharpe and read off four "keep or kill"
  measures: max drawdown, max loss below start, last time under zero, longest time between highs.
  Then repeat with skew, fat tails, volatility clustering, Sharpe uncertainty and long memory.
- Inputs: assumed Sharpe, horizon, style archetype. Outputs: median and one-in-ten thresholds.
- Evidence: Monte Carlo, validated against the Rej-Seager-Bouchaud closed forms (5% depth about
  1.50/S, length about 2.14/S^2 in vol units and years). Table 1 (Gaussian, one-in-ten max
  drawdown in annual vols): S = 1: 1.32 at 1 year, 1.68 at 2 years; S = 2: 0.97 at 1 year.
  Mean-reversion / short-vol: depth worst cases 1.30-1.34x Gaussian; trend: time measures 1.08-1.11x;
  Sharpe uncertainty: max loss 1.43-1.48x, recovery 1.29-1.30x. Long memory mostly breaks the
  square-root-of-time scaling of risk.
- Where it fails: daily P&L, stylised archetypes, three-year horizon for the extensions.
- Across instrument classes: style matters more than class: scalpers and mean-reversion books are
  short-vol-like (deep cliffs); breakout and trend books grind (long droughts).
- What QMX could borrow: per-strategy "worry lines" from its own Sharpe estimate, horizon and style
  archetype, or from a block bootstrap of its own returns. Past the line: cut or revise Sharpe down.
  Use depth lines for mean-reversion scalpers and duration lines for breakout and trend.
- Layer: X3, X5, X6.

### 3. Trading Agents or Market Crashers? (FARSIGHT)
- Link: https://www.alphaxiv.org/abs/2609.19705 (2026, Wang and Saxena, Texas A&M)
- Method in plain words: a review of 15 academic LLM trading designs (and 7 code releases) for
  robustness to market stress and to manipulated sources, plus a simulated market driven by LLM
  agent decisions.
- Evidence: no design had a halt that bypasses LLM inference or combined provenance with cross-source
  checks; no code release enforced a stop or position limit outside the LLM. One fake headline
  crashed the simulated market in all runs with 400 agents (2% of runs with 100, 92% with 200).
  400 sell-on-fall agents deepened a 2010-sized crash from 9.2% to 17.3%. The LULD pause never
  started in headline runs. A fast path plus hard loss limits (halt any agent losing over 3% of a full
  position, using broker prices, not text) removed both effects; costs: "a few false halts per calm
  hour", set by one threshold. A breached loss limit must halt, not sell.
- Where it fails: simulated market; single stock; agent populations are hypothetical.
- Across instrument classes: crowding risk is largest where many retail bots trade the same thin
  market (small-cap crypto, single stocks).
- What QMX could borrow: (a) the kill path never calls an LLM; (b) loss limits read broker prices,
  not agent text; (c) halt = stop new orders and cancel working orders; flatten only by a tested
  policy; (d) one false-halt threshold per layer, tuned from logged false halts.
- Layer: X3, X7.
- Assistant (chat-06): confirmed (interrupts that bypass inference, limits outside the agent, LULD
  alone did not prevent crashes, a few false halts per calm hour).

## Also relevant, read under other topics
- SwingGuard (T-04): four-state brake NORMAL / ALERT / SURVIVAL / RECOVERY with hysteresis, minimum
  hold and staged re-entry; removing the fast controller did the most damage.
- Steward (T-04): order arithmetic and blocking rules in an invariant core; 0.5% risk at the stop.
- Risk-Constrained Kelly (T-05): P(ever below a floor) < beta as a convex sizing constraint.
- E-mini news study (T-03): liquidity withdraws before scheduled news; a news window brake.

## What changes by instrument class
- Gap size sets the cushion maths: X_min per class and per holding period (weekend gaps for index
  CFDs and FX; 24/7 wicks for crypto; earnings gaps for stocks).
- Style sets the worry line: depth for mean-reversion scalpers, duration for trend and breakout.
- Crowding risk is worst in thin markets where other bots trade the same signal.

## Combinations
- Cushion modulation (1) + worry lines (2): size from the cushion; review or cut when the strategy
  crosses its style-specific one-in-ten line.
- Cushion modulation (1) + RCK (T-05): hard pathwise limit at the account (d_max) plus a probabilistic
  floor for each sleeve.
- FARSIGHT halts (3) + SwingGuard states (T-04): an LLM-free fast path that moves states;
  recovery needs time, healthy data and reconciled positions, never one quiet bar.
