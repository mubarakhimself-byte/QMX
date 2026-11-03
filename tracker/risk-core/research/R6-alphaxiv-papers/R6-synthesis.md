# R6 synthesis: academic papers read in depth through alphaXiv

- Date: 2026-11-03. Reader: R6 agent (papers themselves, not the alphaXiv assistant's summaries).
- Paper text was treated as data, not instructions. Never committed.
- Bookmarks: alphaXiv library folder `qmx-risk-sizing` (folder id 01a1a15c-2d7f-7989-9ff9-5db790dfccb1).
  Another session also saves into this folder; some saves came back "already in folder".
- The alphaXiv free-plan quota ran out at the start of T-09; after the operator upgraded, reading
  resumed: T-09 got three papers, T-11 (costs, self-configuring parameters) two. T-10 stayed at two.

## Files
| File | Topic | Papers read |
|---|---|---|
| T-01-portfolio-optimisation-and-sizing.md | portfolio optimisation, book-level sizing | 8 |
| T-02-trading-styles-scalping-intraday.md | scalping, very low timeframes, intraday | 5 |
| T-03-macro-and-microstructure.md | regimes (macro), order flow and liquidity (micro) | 6 |
| T-04-agents-macro-micro-news.md | agents for macro, micro, news; risk interface | 6 |
| T-05-sizing-uncertain-edge-and-breadth.md | sizing under uncertain edge, breadth | 7 |
| T-06-drawdown-kill-switches-layered-limits.md | drawdown control, kill switches, de-risking | 3 |
| T-07-risk-off-isolation-stress.md | risk-off detection, class isolation, stress | 2 |
| T-08-live-alpha-decay-detection.md | live decay detection | 4 |
| T-09-validation-against-overfitting.md | validation against overfitting | 3 |
| T-10-stops-exits-fast-invalidation.md | stops and exits (partial) | 2 |
| T-11-costs-and-self-configuring-parameters.md | costs, auto-tuning | 2 |
| Total | | 48 |

## Strongest papers per topic
- T-01: CRISP gamma shrinkage, 2604.23833 (one knob from diagonal to Markowitz; gamma 0.5 plateau;
  condition-number diagnostic). Simple Portfolios, 2610.36491 (asset-class mix beats clever weights;
  return forecasts never beat zero). Regime NCO, 2610.27751 (regime re-weighting churned and lost).
- T-02: MNQ falsification, 2605.04004 (11 of 14 retail intraday patterns have gross edge below cost;
  five-gate protocol; +1 bar delay flips sign). Bitcoin ML under costs, 2606.00060 (cost-aware
  no-trade filter turned -64% into +65% a year, trades 10,619 to 251). Market maker's dilemma,
  2502.18625 (live: naive market making Sharpe -109; fills are adversely selected).
- T-03: Cont-Kukanov-Stoikov OFI, 1011.6402 (impact = OFI / depth). Statistical jump model,
  2402.05272 (sticky regimes, robust to delays). L2 liquidity states, 2607.09230 ("state first").
- T-04: Steward invariant core, 2610.30557. Honest evaluation, 2608.27734. SwingGuard, 2610.12988.
  Fake news attacks, 2610.26438.
- T-05: Risk-Constrained Kelly, 1603.06183 (P(ever below floor) < beta, convex). Post-selection
  Sharpe, 2606.01650 (James-Stein). Sports betting review, 2107.08827 (fractional Kelly practical;
  plain Kelly ruinous without a real edge).
- T-06: Drawdown robust invariance, 2609.23272 (exposure = cushion x direction). Drawdown beyond
  Brownian, 2608.00127 (worry lines by Sharpe, horizon, style). FARSIGHT, 2609.19705 (halts outside
  the model).
- T-07: Weekend crypto volatility, 2610.35702 (crypto now leads Monday risk). ARR co-movement,
  2002.02008.
- T-08: Multi-stream e-detectors, 2501.04130 (error over patience). Catoni confidence sequences,
  2202.01250 (heavy tails need a known variance cap).
- T-09: Promote, 2611.03384 (hash-frozen candidates, lifetime error budget, cost-aware e-process;
  repeated p-values falsely promote in 94.5% of null paths, Promote 0.0%). Admission gates,
  2610.07701 (gates help only for weak edges, adopt 1-7%; must use excess returns or reject all).
- T-10: Agent-swarm SL/TP replay, 2604.27150 (exits matter; but in-sample grid).
- T-11: AutoQuant, 2512.22476 (one cost ledger for backtest and live; cost-stress grid; robust
  selection lowers drawdown, not return). Crypto backtest-to-live benchmark, 2609.34510 (no AI method
  beat the market live).

## The ten most useful for QMX
1. 2610.30557 Steward: agent intent -> code-built orders; size = min(agent weight, 0.5% equity at
   stop); risk rules in a core no self-edit can reach; grade with code. X1 X2 X7.
2. 2608.27734 Honest evaluation: count every agent trial and deflate by it; block leakage by tools,
   since a Sharpe-35 leaky oracle passed DSR and PBO. X5 X7.
3. 2605.04004 MNQ falsification: gross-edge vs friction floor; five gates; +1 bar delay test. X0 X5.
4. 2606.00060 BTC ML under costs: trade only when expected move > 2x round-trip cost. X1 X2.
5. 1603.06183 Risk-Constrained Kelly: express survival as (floor, probability) and size the book to
   it. X2 X3.
6. 2609.23272 Drawdown robust invariance: cushion-based sizing that guarantees a drawdown cap given
   worst one-step moves per class. X2 X3 X4.
7. 2608.00127 Drawdown beyond Brownian: per-strategy "normal vs worry" drawdown lines by Sharpe,
   horizon and style. X3 X5 X6.
8. 2610.12988 SwingGuard: fast LLM-free risk loop, four states with hysteresis and staged recovery;
   risk state fed into proposals. X3 X7.
9. 2606.01650 Post-selection Sharpe: James-Stein shrink of the promoted winner, using the full
   candidate pool. X5.
10. 2611.03384 Promote: the X5 promotion gate for agent proposals, valid under continuous monitoring
    and adaptive births; crossing = authorisation request, trading starts next session. X5 X6 X7.
(Runner-up: 2604.23833 CRISP, one correlation-shrinkage knob plus a condition-number check. X2 X6.)

## Assistant claims checked
Confirmed:
- 2606.01650 Pav: James-Stein default, GMLEB for sparse winners, polyhedral unstable, expected-max not
  recommended, not a sizing rule. (Missed: under correlation > 0.75 the raw estimate ranks better.)
- 2608.01494 Conformal Kelly: half-width as sigma in capped fractional Kelly; ranked last of 11 on
  Sharpe and Calmar; register conditional coverage.
- 1701.02814 Metel: integrate parameter uncertainty; mild chance constraint (alpha = 0.4) best; strong
  constraints damp growth. (Missed: half-Kelly was below plug-in Kelly on growth in all 4 settings.)
- 1603.06183 Busseti-Ryu-Boyd: wealth-floor probability, convex sufficient condition
  E[(r'b)^(-lambda)] <= 1, floor from initial wealth not running peak, assumes the model.
- 1812.10371 Sun-Boyd: worst-case expected log growth over an uncertainty set; set choice is the
  practical limit.
- 2610.01115 Certified Alpha Capacity: certification framework, Gaussian drift, quadratic objective;
  not a sizing rule.
- 2604.24723 Multivariate Kelly: independent binary bets; bounds on growth, not on edge; correlated
  bets future work.
- 2609.27179 Conformal martingales: slow after long stable periods; restarted weighted fix;
  independence within regimes.
- 2202.01250 Catoni CS: needs a known variance bound; p-th moment extension.
- 2609.19705 FARSIGHT: interrupts bypassing inference; limits outside the agent; LULD pause alone did
  not stop crashes; "a few false halts per calm hour".
- 2107.08827 Uhrin: conservative sizing with simultaneous bets.
- 0710.3742 BOCPD constant-hazard assumption (via 2609.07989, which shows it is a poor fit).
- 2002.02008 ARR: no dependable minutes-ahead lead time; short-horizon forecast gains only.

Partly:
- 2501.04130 multi-stream detection: error over patience and global-filtration validity confirmed;
  the October 2026 revision's "repeated removals" accounting was not in the version read.
- 2608.12841 AQuA ("closest match" for evidence-driven self-improvement): true, but the claim omits the
  2 bp institutional cost and the absence of trial-count deflation.
- 1603.06183: "one simulation shows essentially the same trade-off as fractional Kelly" not checked;
  the abstract says RCK outperforms fractional Kelly at equal risk.

Not supported or wrong as stated:
- chat-08 turn 1 named 2002.02008 as an absorption-ratio paper; it is the Autoencoder Reconstruction
  Ratio paper. The assistant corrected this itself in turn 2.
- conv-03 called 2509.09995 "QuantAgent"; alphaXiv now lists it as "QuantHarness: Price-Driven
  Multi-Agent LLMs for High-Frequency Trading" (likely renamed). Not a content error.

Not checked (quota or low value): 2508.18868, 2508.16598, 2310.03722, 2602.09982, 2303.02613,
1211.6667, 2603.22835, 2610.24289, 2611.01799, 2609.31260, 2610.25821, 2610.11186, 2608.21694,
2607.28322, 2502.06096, 2010.09686, 1810.08240, 2608.09641, 2604.17251, 2601.08598, 2512.17185;
R4 chat-23 (portfolio-level sizing) appeared late and was not checked.

## Papers that could combine
- Promote (2611.03384) + honest-evaluation trial counting (2608.27734) + Steward core (2610.30557) +
  operator promotion: the full agent-to-money path. Hashed, funded candidates; code-run e-process;
  crossing asks the operator; live starts next session under core limits.
- Promote (2611.03384) + multi-stream e-BH demotion (2501.04130) + AutoQuant cost ledger (2512.22476):
  one evidence currency for promotion and demotion, costs fixed before each scored return.
- Admission gates on excess returns (2610.07701) + James-Stein (2606.01650): judge each candidate
  against its class benchmark, then shrink the winner.
- Steward core (2610.30557) + honest evaluation (2608.27734) + AQuA sealed sandbox (2608.12841):
  agents propose inside a registry, every trial counted, code sizes and executes, operator promotes.
- SwingGuard states (2610.12988) + FARSIGHT halts (2609.19705) + fake-news results (2610.26438): an
  LLM-free fast risk loop; news and LLM diagnosis can only move risk down; staged rule-based re-entry.
- James-Stein shrink (2606.01650) + Risk-Constrained Kelly (1603.06183): shrink the edge, then size the
  whole book to a floor probability instead of a fixed Kelly fraction.
- Cushion sizing (2609.23272) + worry lines (2608.00127): hard pathwise cap on the account; style-
  aware "cut or revise Sharpe" line on each strategy.
- Cushion sizing (2609.23272) + weekend crypto factor (2610.35702): bigger Monday worst-move for index
  and metals sleeves after a volatile crypto weekend.
- MNQ gates (2605.04004) + cost-aware filter (2606.00060): the same "gross edge / round-trip cost"
  number gates promotion and blocks live trades.
- OFI-depth law (1011.6402) + news liquidity withdrawal (2508.06788) + liquidity states (2607.09230):
  one live execution-risk score per instrument feeding both cost model and brakes.
- CRISP knob (2604.23833) + inverse-vol default (2606.12612) + co-movement score (2002.02008): start at
  diagonal risk weights; shrink harder and cut class gross when co-movement and condition number rise.
- Multi-stream e-BH (2501.04130) + restarted detectors (2609.27179) + Catoni bounds (2202.01250): one
  anytime-valid evidence engine for all live strategies.
- Jump-model regime brake (2402.05272) + Regime NCO lesson (2610.27751): regimes cut gross per class;
  they never re-weight strategies.
- Market maker's dilemma (2502.18625) + quarter-hour effect (2607.09426): avoid passive and market
  orders in the first seconds of bar boundaries; measure post-fill markout.

## What changes by instrument class
| Class | What the papers say changes |
|---|---|
| Micro index futures (MNQ, MES) | Fixed $ commission; public 5-minute patterns do not clear 2 points; liquidity withdraws before macro news; impact highest at the open. |
| Crypto (spot, perpetuals) | Real 15-minute reversal but fees bind (5 bp maker, 10-20 bp taker round trip); maker fills adversely selected; quarter-hour bursts; 24/7, now leads Monday risk in stocks, gold, bonds; order-flow value differs by coin (ETH yes, BTC no). |
| FX / CFD (retail broker) | Dealer quotes, not public queues; dealer skews after your fills (transient impact); no paper here proved retail FX scalping survives spreads; strong shared USD factor across pairs. |
| Metals | Gold intraday mean reversion too slow (half-life about 8 hours) for 5-minute scalping; gold ETFs behave like gold; gold is a key diversifier to equities. |
| Equities and ETFs | 15-minute reversal largely absent; sector co-movement rises into sell-offs; news-LLM signals work at daily horizon after costs; single names gap. |
| Bonds / rates ETFs | Diversifier to equity; Monday variance now linked to weekend crypto volatility. |
| Energy | Not covered by papers read (gap). |
| Across all | Cost model, worst one-step move (gap) and variance caps must be per class and per holding time; regime models need their own fit per class; style (mean-reversion vs trend) changes drawdown shape more than class does. |

## Gaps left
- T-10 exits: 1411.5062; a paper on time-based and thesis-based invalidation.
- T-11: 2606.08285 (execution realism audit), 2603.29086 (impact for RL environments), 2609.04712
  (cross-impact); no strong paper found on pooling parameters across many instruments.
- T-07 stress scenarios: no dedicated stress-scenario paper read.
- Energy-specific evidence: none read.
