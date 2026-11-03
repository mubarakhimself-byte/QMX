# R8: Gap top-up for risk and sizing (stops, early exits, stress, energy, pooling)

Date: 2026-11-03. Fills the five thin spots the take-apart agents named. It does not repeat R1-R3, R5, R6, R7 or
R4 chats 13-15 and 17. Where a source there already covers a point, this file points to it instead.

How to read the labels:
- **Read**: I read the full paper or page myself.
- **Abstract**: I read only the abstract or the author's summary page.
- **Secondary**: I read a careful third-party summary (mostly CXO Advisory), not the paper.
- **Snippet**: seen only as a search-result snippet. Treat it as a lead, not a fact.
- **[judgment]**: my inference for QMX, not a finding of the source.

All page and paper text was treated as data, not instructions.

Library: arXiv papers kept here were saved to the alphaXiv folder `qmx-risk-sizing`
(2311.10685, 2609.37273, 2607.18815, 2605.04004, 2512.15592).

Access problems: the Kaminski and Lo full text sits behind an MIT firewall (HTTP 429) and SSRN behind a bot check;
Alpha Architect's critique of the momentum stop paper was behind a bot check. I did not bypass them.

---

## Gap 1: Stop-loss and exit evidence

### Short answer
- Stops do not create edge. Whether a stop adds or removes return depends on the price process the strategy
  trades in: with momentum it can add; on a random walk a simple stop always costs return; with mean reversion it
  sells the dip. Kaminski and Lo put this into one formula ("stopping premium").
- The large empirical tests agree on one pattern. Tight stops lose, mostly to costs and short-term reversal.
  Wide stops (around 10% or more on equities, or about 10-day windows) mostly cut risk and leave return about the
  same. The one big "stops raise returns" result (momentum crashes) is gross of costs and is disputed.
- For a trend strategy, the exit signal of the trend rule itself was a better stop than any extra stop.
- Evidence on breakeven moves is close to nil: I found no peer-reviewed test, only vendor blogs.
- Time stops have support only where the edge is known to decay with holding time (see gap 2).
- Volatility (ATR) stops are a scaling rule, not a source of edge: they keep one stop rule usable across
  instruments and regimes.

### 1.1 Kaminski and Lo, "When do stop-loss rules stop losses?"
- Link: https://ideas.repec.org/a/eee/finmar/v18y2014icp234-254.html (Journal of Financial Markets 18, 2014,
  234-254). Earlier version: Kaminski's MIT PhD thesis, https://dspace.mit.edu/handle/1721.1/40384 (2007).
  Label: **Abstract** (journal and thesis abstracts), plus the summary in Clare et al. (1.4) which I read in full.
- Method in plain words: treat a stop as a switch that moves the portfolio from the risky asset into a safe
  asset after cumulative losses pass a threshold, and back in after a recovery. Measure the change in expected
  return ("stopping premium") and in volatility versus never stopping.
- Theory result: under a random walk a simple 0/1 stop always lowers expected return. With momentum (positive
  autocorrelation) it can add value. A regime-switching model with periodic "flights to quality" explains the
  gains they observed.
- Evidence: US equities, stopping into long-term US government bonds, monthly data January 1950 to December
  2004: some stop rules added 50 to 100 basis points per month during stop-out periods (thesis abstract). The
  journal version uses daily index futures and says that at longer sampling frequencies some stop rules raise
  expected return and cut volatility substantially. **Snippet**: one search summary says the 1993-2011 futures
  test showed +1.5% return and -5% volatility for a monthly calibration; not verified.
- Where it fails: the gain is measured only "during stop-out periods" and depends on bonds rallying when stocks
  fall (flight to quality). That link does not hold in every era (2022 broke it). No intraday or cost-heavy
  setting.
- By instrument class: the premium is proportional to return persistence. Trend-prone markets (some futures, FX
  trends) suit stops; mean-reverting instruments (many FX crosses intraday, index futures at short horizons) are
  where stops cost most.
- What QMX could borrow **[judgment]**:
  - Before a strategy gets a stop, measure the autocorrelation of its own P&L or price at its holding horizon.
    Positive: a stop can pay. Negative: a stop is insurance with a cost, sized as such.
  - Report a stop's effect as two numbers, the change in mean return and the change in volatility, never only
    "fewer big losses".

### 1.2 Lo and Remorov, "Stop-loss strategies with serial correlation, regime switching, and transaction costs"
- Link: Journal of Financial Markets 34 (2017) 1-15; summary at
  https://www.cxoadvisory.com/equity-premium/stop-losses-on-stock-positions-in-depth/ . Label: **Secondary**.
- Method: daily and 10-day loss windows; stop thresholds 0% to -6% (daily) and 0% to -14% (10-day); switch to
  T-bills; re-enter when cumulative return passes a threshold. Two executions: sell at the same close, or sell at
  the next day's close. Costs: real half-spreads (0.2% average used in simulations).
- Evidence (US common stocks, daily, 1964-2014; simulations plus history):
  - Tight stops cut returns significantly, mostly because of trading costs.
  - Stock autocorrelation turned significantly negative in the second half of the sample, which hurts tight stops.
  - Spreads blow out during crashes, exactly when stops fire.
  - Wide 10-day stops matched buy-and-hold on a risk-adjusted basis, through lower downside volatility. They raised
    skew and cut maximum drawdown.
  - Waiting one day to execute beat immediate execution, by a lot for tight stops (prices revert in that day).
  - Quick re-entry helped tight stops.
- Where it fails: single stocks only; broker fees and impact left out; many settings tested on one sample
  (snooping risk, which the summary flags).
- By instrument class: the costs-versus-volatility trade-off is the general lesson. A stop must be wide relative
  to spread and noise. For FX majors and index futures with tight spreads, the cost part is smaller; the
  reversion part may be larger.
- What QMX could borrow **[judgment]**:
  - Model the stop fill at the spread prevailing in a stress window, not the average spread.
  - Allow an "execution delay" option for slow strategies (confirm on a close), and test it against the immediate
    stop, because reversion after a stop trigger is a measured effect.

### 1.3 Lei and Li, "The value of stop loss strategies"
- Link: Financial Services Review 18 (2009) 23-51; summary at
  https://www.cxoadvisory.com/technical-trading/using-trailing-stop-losses-to-reduce-risk/ . Label: **Secondary**,
  also cited in Clare et al. (read).
- Method: random buy dates in NYSE/AMEX stocks, 1970-2005; holding 3, 6 or 12 months; stops at 5, 10 or 20 daily
  standard deviations (a volatility-scaled stop); fixed versus trailing; money goes to the S&P 500 or T-bills.
- Evidence: over the full sample neither fixed nor trailing stops changed the level of returns. Trailing stops
  reduced the spread of returns (risk). Fixed stops helped only in some decades and for high-volatility stocks.
  In simulations (independent, autocorrelated or trending returns), stops did not change the return level.
- Where it fails: long holding periods only; no intraday data.
- What QMX could borrow **[judgment]**: when a stop is justified as "risk control", score it on the change in loss
  spread and tail, and do not expect a return gain.

### 1.4 Clare, Seaton, Smith and Thomas, "Breaking into the blackbox: trend following, stop losses and the frequency of trading: the case of the S&P 500"
- Link: https://openaccess.city.ac.uk/id/eprint/17842/ (Journal of Asset Management 14(3), 2013, 182-194).
  Label: **Read** (accepted version).
- Method: moving-average, crossover and breakout rules on the S&P 500, daily data July 1988 to June 2011 and
  monthly from 1952; 0.2% cost per trade. On top of a 200-day breakout entry, test trailing percentage stops
  (3% to 15%), breakout stops, and a "purchase cost" stop at 5 standard deviations below entry.
- Evidence (daily, 1988-2011):
  - Buy and hold: return 9.49%, volatility 18.16%, Sharpe 0.31.
  - 200-day breakout without an extra stop: return 10.61%, volatility 12.20%, Sharpe 0.56.
  - Adding a trailing stop: 3% gives Sharpe -0.11 (return 3.02%); 5% gives 0.08; 7% 0.31; 10% 0.52; 12% 0.54;
    15% 0.49. No stop setting beat the plain trend exit.
  - The purchase-cost stop had no benefit. Their summary: "a change of trend is the best stop loss".
  - End-of-month decisions were as good as or better than daily ones.
- Where it fails: one index, long-only, long-horizon trend rules; nothing intraday.
- By instrument class: the result is about trend strategies whose own signal already exits. It says little about
  scalpers, where there may be no slower exit signal to rely on.
- What QMX could borrow **[judgment]**:
  - For trend strategies, the strategy's own reversal signal is the primary exit; the hard stop is a catastrophe
    stop set wide, at a level where it rarely fires.
  - Never add a stop to a strategy without testing "same strategy, no extra stop" as the baseline.

### 1.5 Han, Zhou and Zhu, "Taming momentum crashes: a simple stop-loss strategy"
- Link: SSRN abstract 2407199 (2016 version); summary at
  https://www.cxoadvisory.com/technical-trading/stop-losses-to-avoid-stock-momentum-crashes/ . Label: **Secondary**.
- Method: monthly cross-sectional stock momentum (top minus bottom decile). Inside the month, any stock that
  moves 10%, 15% or 20% against the position is closed via a limit order at 1.5 times the threshold, else at the
  close.
- Evidence (US stocks, January 1926 to December 2013, gross of costs), equal-weighted, 15% stop:
  - Average monthly return 0.99% to 1.93%; monthly volatility 6.01% to 4.61%; monthly Sharpe 0.17 to 0.40.
  - Worst monthly loss -49.8% to -17.4%.
  - About 10-11% of positions stopped out per month; turnover rose (winner side 39% to 49%).
  - 10% stop: monthly Sharpe 0.50; 20% stop: 0.32.
- Where it fails: gross returns; heavy dependence on a few crash months; a critique ("fact or fiction", Alpha
  Architect, 2016) exists but I could not open it.
- By instrument class: works on the short side of momentum mostly (losers that rebound sharply). Most relevant to
  any book with short positions in crash-prone instruments (equities, crypto).
- What QMX could borrow **[judgment]**: position-level stops inside a portfolio strategy can cut the left tail of
  the whole strategy. Test them per leg (long side, short side) separately; the benefit was mostly on one side.

### 1.6 Carver, "What is the right way to set stop losses?" (practitioner)
- Link: https://qoppac.blogspot.com/2020/02/what-is-right-way-to-set-stop-losses.html (2020). Label: **Read**.
- Method: a trailing stop set at X times the instrument's annual volatility. X is chosen from the holding period
  you want, not from your capital. Position size is set separately from capital, risk appetite and instrument
  risk. Example: X = 0.5 with 20% annual volatility gives a 10% trailing stop; an asset 4 times as volatile gets a
  stop 4 times as wide and a position a quarter the size, so the money at risk at the stop is the same.
- Claims (opinion, with worked examples, no backtest in this post):
  - A breakeven stop is just another fixed stop: "nothing special about your entry level".
  - Profit targets make sense only for mean reversion, and then from an analysis of the reversion process.
  - Time-based stops make little sense for trend strategies.
- Where it fails: written for slow trend trading; not tested for scalpers.
- What QMX could borrow **[judgment]**:
  - Two separate knobs: stop width comes from volatility times a horizon factor; size comes from the risk budget.
    This differs from the common "size = risk budget / stop distance" rule (Steward, T-04). Both give the same money
    at risk at the stop when the stop is volatility-scaled; they differ when someone tightens a stop to "fit" more
    size. QMX should forbid that move: tightening a stop must not raise size unless the strategy's own tests show
    the tighter stop keeps the edge after costs.
  - This answers "volatility and ATR stops": use them so one stop rule transfers across FX, indices, metals,
    energy and crypto, and so stops widen automatically when volatility rises.

### 1.7 Triple-barrier labelling and meta-labelling for exits
- Already covered in R4 chat 14 (triple barrier, meta-labelling, exit classifiers, 2411.12753, 2504.02249,
  2610.13126). Two additions:
- Joubert, "Meta-Labeling: Theory and Framework" (Journal of Financial Data Science, 2022) and a 2023 JFDS paper
  "Meta-Labeling: Calibration and Position Sizing". Label: **Snippet**. The 2023 abstract (as listed) compares six
  sizing rules with calibrated and uncalibrated probabilities: calibration significantly helps fixed sizing
  functions and gives no significant gain for sizing functions learned from training data.
- What QMX could borrow **[judgment]**: if an exit or entry classifier's probability feeds a fixed sizing curve,
  calibrate it first (and re-check calibration live). The barrier widths in triple-barrier labelling are the same
  stop and target choice as here, so they should be volatility-scaled for the same reason.

### 1.8 How stops change win rate, payoff and Kelly sizing (worked math) **[judgment]**
- A stop turns a continuous loss distribution into something close to a fixed loss of 1R (R = stop distance), so
  a binary Kelly formula becomes usable for the fraction of equity risked at the stop:
  f* = p - (1 - p) / b, where p is the win rate and b the average win in R.
- Costs c, measured in R, enter both sides: f* = [p(b - c) - (1 - p)(1 + c)] / [(b - c)(1 + c)].
  Example: p = 0.45, b = 2: no costs gives f* = 17.5% of equity at risk; with c = 0.1R it falls to about 12%.
- Tightening the stop raises c in R terms, because the cost is fixed in price. Halving the stop doubles c/R. This
  is the mechanism behind 1.2 and 1.4: tight stops raise the stated payoff b but also raise c and usually lower p.
- Gaps: if the average stop fill is g times R (g above 1 after gaps and slippage), use loss = g + c. For energy
  around inventory reports and for index futures at the open, g can be well above 1 (see gap 4).
- A breakeven move creates a third outcome (a scratch at about -c), so the win rate falls and a two-outcome
  Kelly formula overstates the edge. Use the full outcome distribution, or simulate.
- Full Kelly from these inputs is far too large in practice because p and b are estimates; the sizing chats (R4
  chats 01 and 04) already cover shrinking toward fractional Kelly.

---

## Gap 2: Fast invalidation and early exits

### Short answer
- I found no study that measures "cut at a fixed fraction of the stop when the premise fails" as a rule, with
  costs. That is a real gap in the literature, not just in our reading.
- The nearest evidence comes from four directions:
  1. Human traders hold losers and take more risk after losses, and this costs them money. A mechanical
     invalidation rule removes that failure mode.
  2. For short-horizon signals, the edge often arrives in the first bar or few bars and then reverses. A fixed time
     exit, or a "no progress by bar N" exit, has a measurable basis.
  3. Tight cuts on noisy, mean-reverting prices lose to costs and reversal (gap 1).
  4. Exit classifiers have only thin out-of-sample evidence (R4 chat 14).
- The size of the cut should be measured per strategy from its own trade paths (adverse excursion of winners),
  not set by a rule of thumb.

### 2.1 Garvey, Murphy and Wu, "Do losses linger? Evidence from proprietary stock traders"
- Link: https://www.nuff.ox.ac.uk/Users/MurphyA/Do%20Losses%20Linger.pdf (revised November 2005; published in the
  Journal of Portfolio Management). Label: **Read** (working-paper version).
- Method: split each day into morning and afternoon; standardise each trader's profits and risk measures; regress
  afternoon risk-taking on morning profit.
- Evidence: 150 professional day traders at a Nasdaq dealer, June 2002 to May 2003; 1.3 million trades; 730,000
  intraday round trips; average holding time 13 minutes; no overnight positions.
  - Gross loss for the year about $45,000; trading costs about $1.66 million; net loss about $1.70 million. Costs
    turned a near-breakeven book into a large loss.
  - After a morning loss, traders traded more, bigger and wider in the afternoon (roughly 0.05 to 0.07 standard
    deviations above normal); after gains they did not.
  - Traders with a significant "get even" bias lost $4,300 to $14,400 more per year than the others (average
    trader -$11,400).
  - The firm already forced flat-by-close and trained traders to use trailing stops.
- Where it fails: one firm, one year, just after decimalisation (the firm's own explanation of the losses).
- By instrument class: a human-behaviour result; any discretionary override in QMX would face it.
- What QMX could borrow **[judgment]**: an alert or brake on "risk raised after a loss" for any human or agent that
  can change sizes intraday. The authors suggest exactly this kind of automated alert. For QMX the same check
  applies to agents: an agent that proposes bigger sizes after a losing session should be flagged.
- Related, not read: Garvey and Murphy, "Are professional traders too slow to realize their losses?" (Financial
  Analysts Journal 60(4), 2004; same desk, disposition effect, **Snippet**); Locke and Mann, "Professional trader
  discipline and trade disposition" (Journal of Financial Economics 76, 2005; CME floor traders, **Abstract**
  only); Coval and Shumway, "Do behavioral biases affect prices?" (Journal of Finance 2005; CBOT traders take more
  afternoon risk after morning losses, as cited by Garvey et al.).

### 2.2 Mesfin, "Structural limits of OHLCV-based intraday momentum signals in MNQ futures"
- Link: https://www.alphaxiv.org/abs/2605.04004 (2026, independent researcher). Label: **Read**.
- Method: 14 common retail intraday signal families on Micro Nasdaq futures, 5-minute bars, December 2021 to
  August 2025, expanding walk-forward with three out-of-sample years; signal at bar close, entry at next open; cost
  2.0 points round trip on MNQ (0.5 points on micro gold).
- Evidence relevant to exits:
  - 11 of 14 families have a gross edge of 0.07 to 1.50 points per trade, below the 2.0-point cost. The best
    "near misses" fail on stability, not costs.
  - The two signals that pass use fixed time exits (about 65 minutes; 60 minutes or 08:30 ET).
  - London signal: delaying entry by one 15-minute bar flips the t-statistic from +4.30 to -2.78. The move happens
    inside the first bar; after it, the price reverses.
  - Asia session expansion bars: continuation entry after the bar has a t-statistic of -11.5; the move is
    exhausted within the breakout bar.
  - An opening-range pullback entry was stopped out 80.7% of the time at a 20-point stop.
- Where it fails: one researcher; positive controls carry selection exposure (53+ settings tried, said openly); bar
  data only.
- By instrument class: index micro futures; the gold test is weaker. The cost floor in points is specific to the
  contract.
- What QMX could borrow **[judgment]**:
  - For each strategy, plot average signed return by bars since entry (the edge-versus-time curve). If the edge is
    realised in the first k bars, a time stop at about k bars, or an exit when the trade has not moved favourably
    by bar k, is grounded in the strategy's own data.
  - Treat "the move already happened inside the signal bar" as a named failure mode for fast strategies.

### 2.3 Maximum adverse excursion and the edge ratio (practitioner methods)
- Sources: J. Sweeney, *Maximum Adverse Excursion* (Wiley, 1997); C. Faith, *Way of the Turtle* (2007), the
  "E-ratio". Label: **not read this round**; method as widely described.
- Method in plain words:
  - Adverse excursion: for every closed trade, record how far it went against you before it closed, in R or in
    ATR. Winners usually have small adverse excursions. The level that most winners never reach is a natural
    invalidation level: past it, the trade is far more likely to be a loser.
  - Edge ratio: average favourable excursion divided by average adverse excursion, both in ATR, measured N bars
    after entry for every signal. It shows how fast a signal's edge appears and when it fades.
- Where it fails: in-sample; the distribution moves with regime and volatility; no published cost-adjusted test I
  could find.
- What QMX could borrow **[judgment]**:
  - Set the early-cut level from the adverse-excursion distribution of the strategy's own winners. Example rule:
    if 90% of winners never go below -0.4R, an invalidation exit at -0.5R loses at most about 10% of winners and
    cuts losers early. Then test it with costs, out of sample, and counted as a search trial (T-09).
  - Pick the time stop from the bar where the edge ratio peaks.
  - This is the measured answer to "how big should the average cut be": it is a per-strategy number, read from
    data, re-measured live.

### 2.4 Evidence against cutting too fast
- Lo and Remorov (1.2): next-day execution beat immediate execution for tight stops, and quick re-entry helped,
  because prices revert after the trigger.
- Clare et al. (1.4): stops tighter than about 7% destroyed the trend strategy's Sharpe.
- 2604.27150 (T-10): a longer stale-close timer (48 h versus 24 h) helped the crypto swarm.
- What QMX could borrow **[judgment]**: an invalidation rule must beat two baselines, "no early cut" and "cut one bar
  later", after costs, before it can go live. A thesis-based invalidation (the named falsifying condition from
  Steward, T-04) is safer than a price-only fraction, because it does not fire on ordinary noise.

### 2.5 Exit classifiers
- Covered in R4 chat 14 (SPX short-straddle exit timing 2610.13126; label imbalance 2503.09988; meta-labelling).
  Nothing new and stronger was found in this round's search. The evidence that exit classifiers improve results
  after costs remains thin and mostly single-market.

---

## Gap 3: Stress scenarios for multi-strategy books

### Short answer
- Generative scenario models are covered in R4 chat 15. The missing parts were how to choose plausible scenarios,
  how to run reverse stress tests, how to handle the factors a scenario does not name, how to check a scenario
  table against reality, and how to model accumulation (many small positions hit by one common cause).
- The main practical lessons:
  - Fill the factors a scenario does not stress with their conditional values, not zero.
  - Backtest the scenario table every day against the scenario that actually happened.
  - Model accumulation by common dependency (venue, data feed, signal family, macro factor), not by pairwise
    correlation alone.
  - Expect stop and deleveraging rules across strategies to fire together and add to the loss.

### 3.1 Cai, Haugh and Li, "When stress tests miss the risk: statistical scenario analysis for financial portfolios"
- Link: https://www.alphaxiv.org/abs/2609.37273 (2026, Imperial College). Label: **Read** (main sections).
- Method:
  - Standard scenario analysis shocks a few factors and holds the rest at zero, then reports one P&L number.
  - The paper instead treats it as prediction. It sets unstressed factors to their mean given the stress
    (conditional scenario analysis) and reports a prediction interval, not a point.
  - It calibrates that interval online with conformal methods (ACSA) and with kernel weighting of similar past
    days (KSA).
  - It backtests by re-running, each day, the scenario that actually happened yesterday and comparing with the
    realised P&L.
- Evidence (simulated equity and option books built to mimic S&P 500 markets):
  - Filling the unstressed credit factor with its conditional mean moved scenario P&L by up to about $44 in the
    example grid.
  - A portfolio built to look safe under the named factors showed scenario P&L within ±$3 under the standard
    method, while its true expected loss reached about -$20.
  - Naive intervals covered the truth less than 10% of the time in extreme cells, against a 50% target; the
    calibrated methods came close to 50%.
- Where it fails: simulated markets; the kernel method needs history similar to the stress; scaling to many
  factors is open.
- By instrument class: option-heavy and leveraged books suffer most from the convexity error; linear FX and
  futures books mostly suffer from the unstressed-factor error.
- What QMX could borrow **[judgment]**:
  - Every stress scenario names its stressed factors and fills the rest with their values conditional on the
    stress (from a factor model or nearest-neighbour history).
  - The scenario P&L is shown as a band.
  - A nightly job replays yesterday's actual moves as a scenario and logs predicted versus realised P&L. That
    gives the stress engine its own error record.
  - The "adversarial portfolio" case matters for agents: an agent that optimises against the named stress factors
    can pass the stress test while carrying unnamed risk. Scenario sets should change and include factors the
    agents do not see.

### 3.2 Breuer, Jandačka, Rheinberger and Summer, "How to find plausible, severe, and useful stress scenarios"
- Link: https://www.ijcb.org/journal/v5n3/how-find-plausible-severe-and-useful-stress-scenarios (International
  Journal of Central Banking 5(3), 2009, 205-224). Label: **Snippet** (abstract via search; PDF not opened).
- Method in plain words: define a plausibility region as all factor moves within a chosen Mahalanobis distance
  (a multi-factor "number of standard deviations") of normal, then search that region for the worst portfolio loss.
  For partial scenarios, fill the unstressed factors with their conditional mean, which the authors show is the
  most plausible fill.
- Where it fails: plausibility uses an elliptical (normal-like) distance, which understates joint tails.
- What QMX could borrow **[judgment]**: a "worst loss within k sigma" search over the book's factor exposures
  is a cheap reverse stress test that needs no scenario list. Run it at several k, and report which factor
  combination produced the worst loss.

### 3.3 Glasserman, Kang and Kang, "Stress scenario selection by empirical likelihood"
- Link: https://ideas.repec.org/a/taf/quantf/v15y2015i1p25-41.html (Quantitative Finance 15(1), 2015); OFR working
  paper 0007. Label: **Snippet**.
- Method: reverse stress testing. Given that the loss passes a threshold, estimate the most likely factor moves
  (the conditional mean of factors given a large loss) without assuming a distribution, and scale confidence
  regions to the tail type (normal, Laplace, Student t).
- What QMX could borrow **[judgment]**: from the book's own history (or simulated history), take all days where the
  book lost more than X, average the factor moves on those days, and publish that as "the scenario that breaks
  us". This is the data-driven reverse stress test; 3.2 is the model-driven one.

### 3.4 Lopez and Nkameni, "Cloud failure and cyber insurance: stress scenarios and diversification"
- Link: https://www.alphaxiv.org/abs/2607.18815 (2026, CREST/ENSAE). Label: **Read** (method and conclusion).
- Method: two regimes. In the normal regime, independent claims diversify (variance). In the stressed regime, one
  common dependency (a cloud provider) fails and hits every policy that relies on it at once. Risk in the
  stressed regime is measured per dependency as roughly linear in the share of the book exposed to it. The book
  is optimised for variance plus a penalty on stressed-regime exposure, which produces concentration limits per
  dependency.
- Evidence: synthetic portfolio; outage probabilities, durations and dependence set from a Lloyd's 2018 report and
  expert judgment, because real accumulation data are scarce (stated openly).
- Where it fails: not an empirical calibration; Gaussian approximations; individual heterogeneity simplified.
- By instrument class: not a trading paper. It is the accumulation model insurers use, and it maps onto many small
  strategies sharing hidden dependencies.
- What QMX could borrow **[judgment]**:
  - List QMX's common dependencies: broker or venue, price feed, compute host, signal family, macro factor (USD,
    equity beta, oil), scheduled event, and session (all strategies flat at the same rollover).
  - For each, compute the share of open risk exposed to it, and the loss if it fails or moves.
  - Set concentration limits per dependency. A book can look diversified by correlation and still be one outage or
    one event away from a joint loss.
  - Scenario parameters may be expert-set when data are scarce, but they must be labelled as assumptions.

### 3.5 Khandani and Lo, "What happened to the quants in August 2007?"
- Link: https://web.mit.edu/~alo/www/Papers/august07.html (Journal of Investment Management 5, 2007, 29-78).
  Label: **Abstract** (plus search snippets about the 2010 revision).
- Method: TASS hedge-fund data and a simulated contrarian long/short equity strategy.
- Evidence (hypothesis, by the authors' own description tentative): the losses of the week of 6 August 2007 began
  with a rapid unwind of one or more large market-neutral equity portfolios, probably a forced liquidation by a
  multi-strategy fund or prop desk. The price impact hit similar portfolios, whose stop-loss and deleveraging
  rules then added more selling. A strong rebound came on 10 August. Snippets say the 2010 revision finds most of
  the unwind on 7-9 August.
- Where it fails: indirect evidence; equity market-neutral only.
- What QMX could borrow **[judgment]**:
  - A crowding scenario: "strategies of the same family as ours lose k sigma in 3 days, then rebound".
  - Stops across many QMX strategies of one family can fire on the same days and lock in the loss just before the
    rebound. The stress engine should simulate the book's own brakes inside the scenario, not only the price path.
  - A multi-strategy book's de-risking rules are themselves a source of correlated loss.

### 3.6 Exchange scenario grids: CME SPAN
- Links: https://www.cmegroup.com/clearing/margins-on-options.html and the CME client wiki page "Risk Arrays".
  Label: **Snippet** (CME pages via search, not opened).
- Method: for each contract, 16 profit-and-loss scenarios. Price moves up and down in thirds of the "price scan
  range", combined with volatility up or down. Two extreme scenarios move price 3 times the scan range, and only
  about 30-33% of that loss is counted. (NSE uses 2 times and 35%; that 35% figure is NSE's, not CME's.)
- What QMX could borrow **[judgment]**: a small, fixed, explainable per-instrument grid (moves of 1/3, 2/3 and 1
  scan range, plus a 3x extreme move) is a good default scenario set for every strategy. The scan range should be
  volatility-based per instrument. QMX should count the extreme move in full for its own book, because a small
  book cannot spread the loss the way a clearing house does.

### 3.7 Already covered elsewhere
- Generative scenario models (Tail-GAN, diffusion factor models, SSGEN, large-deviation scenarios, correlation
  stress, negative oil and the nickel squeeze): R4 chat 15 and R4 synthesis.

---

## Gap 4: Energy instruments (oil and gas CFDs and futures)

### Short answer
- Energy brings four hazards the other classes have less of:
  1. Scheduled weekly inventory reports that move price in seconds, with dates that shift around holidays.
  2. Monthly contract expiry and rolls, with front-month squeezes (negative WTI 2020) and roll gaps in CFDs.
  3. OPEC decisions whose effect depends on the decision type and the benchmark.
  4. Volatility regimes; natural gas is much more volatile than crude, and storage season matters.
- Retail systematic traders size energy the same way as everything else: by volatility (ATR or standard
  deviation). What changes is the event calendar, the roll handling and the gap allowance in the stop.

### 4.1 Contract facts: NYMEX WTI crude (CL)
- Link: https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.contractSpecs.html. Label: **Read**
  (specs, accessed 2026-11-03).
- Facts:
  - Contract unit: 1,000 barrels. Tick 0.01 per barrel = $10.
  - Hours: CME Globex Sunday to Friday, 5:00 pm to 4:00 pm CT, with a 60-minute break each day from 4:00 pm CT.
  - Last trade: 3 business days before the 25th calendar day of the month before the contract month (4 business
    days if the 25th is not a business day).
  - Price limits use CME's dynamic circuit-breaker rules (linked from the spec page; values not copied here).
  - Micro WTI and micro Henry Hub contracts are listed (sizes not checked on this pass).
- What QMX could borrow **[judgment]**:
  - Expiry and roll dates must come from the exchange calendar, per contract.
  - A front-month position must be rolled or closed several days before last trade. The April 2020 negative
    settlement happened at expiry (R4 chat 15, 2610.00951).

### 4.2 Scheduled reports: EIA weekly petroleum and natural-gas storage
- Links: https://www.eia.gov/petroleum/supply/weekly/schedule.php and https://ir.eia.gov/ngs/schedule.html.
  Label: **Read**.
- Facts:
  - Petroleum status report: standard Wednesday 10:30 am ET. Holiday weeks move it to Thursday 11:00 or 12:00, and
    once to Monday 5:00 pm (29 December 2025).
  - Natural-gas storage report: standard Thursday 10:30 am ET. Holiday weeks move it to Wednesday or Friday, or a
    Monday at 12:00 noon.
  - 2026 entries listed for both.
- What QMX could borrow **[judgment]**: event windows must be read from the published schedule, never hard-coded
  as "Wednesday 10:30". The event calendar is data with its own refresh job.

### 4.3 Halova, Kurov and Kucher, "Noisy inventory announcements and energy prices"
- Link: https://ideas.repec.org/a/wly/jfutmk/v34y2014i10p911-933.html (Journal of Futures Markets 34(10), 2014,
  911-933); working paper at https://www.skidmore.edu/economics/documents/NoisyInventoryAnnouncementsAndEnergyPrices.pdf .
  Label: **Snippet** (abstract and search summary).
- Method: event study of crude and natural-gas futures around EIA inventory releases, correcting for measurement
  error in analysts' inventory forecasts.
- Evidence (as summarised): older studies understated the response; energy futures react much more to inventory
  surprises than previously shown. The working paper reports natural-gas prices falling almost 10% on average for
  a 1% inventory shock (units need checking). Crude-inventory surprises also move gas futures, and the other way
  round.
- Earlier R4 work already cites Bu (2014) on crude volatility around the EIA report.
- What QMX could borrow **[judgment]**:
  - Treat the inventory release as a jump event for both crude and gas strategies, even for a strategy trading only
    one of them.
  - Default policy: no new entries in a window around the release, stops widened or positions cut before it, with
    the gap factor g (gap 1.8) raised for that window.

### 4.4 Loutia, Mellios and Andriosopoulos, "Do OPEC announcements influence oil prices?"
- Link: https://ideas.repec.org/a/eee/enepol/v90y2016icp262-272.html (Energy Policy 90, 2016, 262-272).
  Label: **Snippet** (abstract).
- Evidence (abstract): the effect of OPEC announcements changes over time and by decision type; it is stronger
  for production cuts and for holds; it differs between WTI and Brent.
- What QMX could borrow **[judgment]**: OPEC meetings belong in the event calendar with a decision-type field. The
  CME spec page links an "OPEC Watch" tool that reads meeting-outcome odds from options, which could feed a
  pre-event risk flag.

### 4.5 Mou, "Limits to arbitrage and commodity index investment: front-running the Goldman roll"
- Link: https://papers.ssrn.com/abstract=1716841 (2010). Label: **Snippet** (abstract via search).
- Evidence (abstract): strategies that trade ahead of the index roll window earned positive-skew excess returns
  with Sharpe ratios up to 4.39 from 2000 to March 2010; index investors gave up about 3.6% a year to the price
  impact.
- What QMX could borrow **[judgment]**: roll windows are predictable flow events. Strategies holding energy
  futures through the main index roll days should know they are there, and a futures roll inside that window
  costs more.

### 4.6 CFD specifics: rolls, leverage caps, broker price source
- Rollover mechanics (XTB help pages, **Snippet**):
  - Futures-based oil CFDs switch to the next contract on a broker-set date and post a one-time swap credit or
    debit equal to the price difference, so the position's value is unchanged in principle.
  - Pending orders priced inside the roll gap fill at the new opening price.
  - A secondary site describes a roughly $5 gap at the October-to-November 2026 WTI roll (unverified).
  - A 2016 forum thread reports a broker whose rolled price differed from benchmark sources for days (anecdote).
- ESMA 2018 retail CFD measures (ESMA press release, **Snippet**):
  - Leverage caps: 10:1 for commodities other than gold; gold and major indices 20:1; major FX 30:1; crypto 2:1.
  - Margin close-out at 50% of required margin, and negative-balance protection.
  - Current status after the 2019 renewals not checked here. From memory, not verified this round: national
    regulators then made similar rules permanent.
- What QMX could borrow **[judgment]**:
  - Store the broker's roll calendar per CFD. Show roll adjustments as their own P&L line, so they never read as
    strategy losses or as stop triggers.
  - Never let a stop sit inside a roll gap unflagged.
  - The leverage cap is a hard ceiling on any sizing output for energy CFDs where it applies.

### 4.7 Volatility regimes and sizing
- Bollerslev, Hood, Huss and Pedersen (gap 5.2, **Read**): normalised realised volatility of 20 commodities
  (including energy) behaves almost the same as other classes, and pooled volatility models forecast energy risk
  better out of sample than per-instrument models.
- Carver (gap 5.3, **Read**): in his pooling run, crude (ICE, micro WTI), heating oil, gasoline and US gas mini all
  fell into the same large pool as most other futures. Their trend-rule Sharpe vectors were not distinct from the
  general pool.
- Retail practice (Turtle "N" units, Carver's volatility targeting; not re-read here): one unit of risk per
  instrument, sized by ATR or annualised volatility.
- What QMX could borrow **[judgment]**:
  - Energy needs no special sizing formula. It needs the general volatility-scaled sizing, plus three energy
    overlays: the event calendar (EIA, OPEC), the roll calendar, and a larger gap allowance in the stop.
  - Natural gas should get its own volatility estimate and its own event set (storage report, weather season);
    sharing crude's parameters would undersize the risk.
  - Units for a vol-targeted position: notional = risk budget / (instrument volatility x contract value per
    point).

### 4.8 Already covered elsewhere
- Negative WTI 2020 and the nickel squeeze as forced-closure scenarios: R4 chat 15 (2610.00951).
- Intraday energy hours and event policy: R4 chats 24-26 and 28.
- Stat-arb stop and leverage on an energy pair: 1706.07021 in R4 chat 13.

---

## Gap 5: Pooling parameters across many instruments

### Short answer
- Out of sample, pooled or shrunk estimates usually beat per-instrument estimates, unless the instrument has a lot
  of its own history. Carver's honest test found per-instrument estimates win once about 10 or more years are
  available.
- How much to pool can be estimated from the data itself (empirical Bayes). The amount of shrinkage depends on how
  far the group's results are from pure luck.
- Volatility dynamics pool very well across asset classes once each instrument's own level is removed. Edge (Sharpe)
  pools less well: the dispersion across instruments is about 20% more than luck alone would produce.
- Defaults and overrides fall out naturally:
  - The group (class, family or whole book) gives the default.
  - An instrument's own estimate gets weight in proportion to its data and how distinct it has proven.
  - Overrides need statistical evidence, not a single good year.

### 5.1 Chen and Dim, "High-throughput asset pricing"
- Link: https://www.alphaxiv.org/abs/2311.10685 (2023, revised June 2025; Federal Reserve Board and GWU).
  Label: **Read** (method, results, limits).
- Method: empirical Bayes over 136,000 long-short strategies.
  - Each strategy's t-statistic is treated as true performance plus noise.
  - The distribution of true performance is a two-part normal mixture, fitted separately for each of six
    strategy families on a rolling 20-year window.
  - Each strategy's prediction is its own result shrunk toward the family prior. In the simple case the shrink
    factor is 1 - 1/(variance of t-statistics within the family). If a family's t-statistics look like pure noise
    (variance near 1), everything shrinks to zero.
- Evidence (US stocks, out of sample 1983-2020):
  - The top 1% by shrunk Sharpe earned 5.7% a year (Sharpe 1.46), versus 5.9% for 200 published anomalies, which
    have look-ahead bias.
  - Before 2004, predictions fell within 2 standard errors of out-of-sample results in almost all of 120 test
    portfolios.
  - Ticker-based (nonsense) strategies were correctly shrunk 100% to zero.
  - In one family, extreme in-sample returns of -8% and +9% were shrunk to about -3% and +2%.
  - Strict multiple-testing hurdles (Harvey-Liu-Zhu style) rejected nearly everything, including thousands of
    strategies that did earn returns out of sample. Storey's false-discovery method did better.
- Where it fails: after the 2004 structural break, predictions stayed too optimistic, because the 20-year window
  was slow to forget. Grouping is by hand (six families).
- By instrument class: single stocks only; the method itself is general.
- What QMX could borrow **[judgment]**:
  - Shrink each strategy's (or strategy-instrument pair's) measured edge toward its family's prior. Estimate the
    shrink factor from how far the family's results are from a no-skill null.
  - A family of agent-proposed strategies that looks like noise gets shrunk to zero edge automatically, with no
    hand-set hurdle.
  - Use a shorter or break-aware window for the prior.
  - This complements post-selection Sharpe correction (2606.01650, R4 chat 17).

### 5.2 Bollerslev, Hood, Huss and Pedersen, "Risk everywhere: modeling and managing volatility"
- Link: https://pure.au.dk/ws/files/154593513/Bollerslev_2018_Risk_everywhere_VOR.pdf (Review of Financial
  Studies 31(7), 2018, 2729-; open access). Label: **Read** (main results).
- Method: realised-volatility forecasting models (HAR, MIDAS and their smooth "HExp" mix of exponential averages,
  plus a global volatility factor). Each model is "centred": the instrument's own long-run volatility level is
  removed, so the remaining parameters are scale-free. The parameters are then estimated three ways: per
  instrument, pooled within an asset class, or pooled across everything ("mega").
- Evidence: intraday data on 20 commodities, 21 equity indices, 8 bond futures and 9 currencies over two decades
  to September 2014; 20-day forecasts.
  - In sample, per-instrument fits always win. Out of sample, the order reverses.
  - Average out-of-sample R² for HExp: per instrument 47.3%, pooled by class 48.7%, pooled across all 49.2%.
  - For FX with the HAR model: per instrument 28.6%, pooled across all 47.7%.
  - Pooling across all cut the variance of forecasts by almost 30%.
  - A volatility-targeting investor gains close to 0.5% of wealth a year from these models versus a static risk
    model. Gradual rebalancing kept most of the gain after spreads.
- Where it fails: liquid futures and FX only; forecasts at the 20-day horizon; the global factor needs many
  instruments.
- By instrument class: works across all four classes in the paper; crypto and single stocks were not tested.
- What QMX could borrow **[judgment]**:
  - Each instrument keeps its own volatility level. The dynamics (how fast volatility mean-reverts, how much
    weight goes to recent days) are one shared default for the whole book.
  - A new instrument with little history gets a usable volatility forecast on day one.
  - Per-instrument overrides of the dynamics should need evidence; the paper shows they usually hurt.

### 5.3 Carver, "One of these things (is not like the others). Or is it? Pooling rule p&l estimates across instruments"
- Link: https://qoppac.blogspot.com/2026/06/one-of-these-things-is-not-like-others.html (June 2026).
  Label: **Read**.
- Method: futures trend, carry and other rules on 214 instruments.
  - Compare instruments by the distance between their vectors of rule Sharpe ratios.
  - Calibrate a critical distance on random data, by years of history. At 95%: 1.65 for 1 year, 0.74 for 5,
    0.53 for 10, 0.37 for 20, 0.26 for 40.
  - Pool two instruments unless their distance is above the critical value. Repeat until nothing more pools.
  - Compare fully pooled, algorithm-pooled and unpooled estimates out of sample. In the honest version the
    optimiser may also pick a rule's opposite, which removes implicit in-sample selection.
- Evidence:
  - For one fast trend rule, Sharpe across instruments ranged from -1.85 to +1.95. The cross-sectional standard
    deviation over 4-year windows was 0.59, against about 0.50 expected from luck alone.
  - The pooling algorithm produced two big groups and a long tail of instruments that pool with nothing,
    including Bitcoin and Ether. The groups often did not match asset classes.
  - Best method in the honest test, by in-sample and out-of-sample years: 5y/1y all pooled; 5y/5y algorithm
    pooled; 10y/1y and 10y/5y unpooled.
  - Carver's suggested heuristic, not yet tested by him:
    - pooled returns under 5 years of history;
    - the instrument's own returns over 25 years;
    - in between, weight on the pooled estimate = (25 - N) x 0.05, for N years of history.
- Where it fails: blog-level testing, no costs, one rule set; results inconsistent across window lengths (he says
  so).
- By instrument class: crypto and some metals and small markets behave as their own groups; most liquid futures
  pool together.
- What QMX could borrow **[judgment]**:
  - Use history-length-weighted blending of pooled and own estimates as the default/override rule for strategy
    parameters and edge estimates.
  - Treat crypto as its own pool by default.
  - Do not trust automatic clustering to find sensible groups. Asset class or strategy family is a fine first
    grouping; the data then decides how much an instrument may depart from it.

### 5.4 Jones and Shanken, "Mutual fund performance with learning across funds"
- Link: https://nber.org/papers/w9392 (Journal of Financial Economics 78, 2005, 507-552). Label: **Abstract**.
- Method: estimate the average and spread of true alpha across all funds. Each fund's alpha is then a roughly
  precision-weighted average of its own regression estimate and the cross-fund mean. Assuming each fund is
  independent amounts to claiming the cross-fund distribution is known in advance; then even no-skill funds can
  look extreme.
- Evidence (abstract): learning across funds pulls extreme estimates in. Estimating from survivors only biases
  the average upward.
- What QMX could borrow **[judgment]**:
  - The weight on a strategy's own record should rise with the precision of that record (number of independent
    trades, not days live).
  - Retired or killed strategies must stay in the population used to set the prior; otherwise the default is too
    rosy.

### 5.5 Kutta, Schumann and Dette, "Inference for forecasting accuracy: pooled versus individual estimators in high-dimensional panel data"
- Link: https://www.alphaxiv.org/abs/2512.15592 (December 2025). Label: **Abstract** plus introduction.
- Method: a confidence interval for the difference in forecast error between a pooled and an individual estimator,
  valid with time and cross-sectional dependence, including many units relative to time.
- Evidence: simulations only.
- What QMX could borrow **[judgment]**: a formal test for "should this instrument leave the pool": override only when
  the interval for (own error minus pooled error) lies below zero.

### 5.6 Classics not re-read here
- Efron and Morris (1975), Stein shrinkage, and Karolyi (1993) Bayes-Stein shrinkage of single-stock volatility
  forecasts (cited by Bollerslev et al.). Ledoit and Wolf covariance shrinkage. These are the textbook foundations of
  5.1-5.4.

---

## Papers or methods that could combine **[judgment]**

1. **Volatility-scaled stops + separate sizing + Kelly with costs.**
   - Stop width = X x volatility, with X from the holding period (Carver).
   - Size = risk budget / (stop distance x g), where g is the gap factor.
   - The risk budget comes from fractional Kelly computed with costs in R units (1.8), shrunk toward the family
     prior (5.1).
   - This keeps a tight stop from buying more size unless the edge survives the extra cost.
2. **Adverse-excursion invalidation + edge-versus-time curve + search accounting.**
   - Set the early-cut level from winners' adverse excursion (2.3) and the time stop from the edge curve (2.2).
   - Validate both against "no cut" and "cut one bar later" (2.4).
   - Count every setting tried as a trial for deflated Sharpe (T-09, R4 chat 11).
3. **Autocorrelation check + stopping premium.** Measure each strategy's P&L autocorrelation at its horizon
   (Kaminski-Lo, 1.1). Positive: allow a tighter catastrophe stop. Negative: a wide stop only, sized as insurance.
4. **Pooled volatility model + pooled edge prior + history-weighted override.**
   - Volatility dynamics pooled across the book (5.2).
   - Edge shrunk toward the family prior by empirical Bayes (5.1).
   - Own-history weight rising with years and trades (5.3, 5.4).
   - An override only when a pooled-versus-own test favours it (5.5).
5. **Common-dependency accumulation + crowding scenario + brakes inside the scenario.**
   - Concentration limits per dependency (3.4).
   - A family-wide unwind-and-rebound scenario (3.5).
   - The book's own stops and de-risking rules simulated inside each stress path, so the stress loss includes
     what QMX's brakes would do.
6. **SPAN-style grid + conditional fill + daily scenario backtest.**
   - Per-instrument 16-point grid plus a full-count extreme move (3.6).
   - Unstressed factors filled with conditional values (3.1, 3.2).
   - A nightly replay of yesterday's realised scenario that scores the stress engine (3.1).
   - A reverse stress test from "days we lost more than X" (3.3).
7. **Energy overlay on the general machinery.**
   - The EIA, OPEC and roll calendars as data (4.1, 4.2, 4.4, 4.5).
   - Event windows raise g and block entries (4.3).
   - CFD roll adjustments get their own P&L line (4.6).
   - Natural gas gets its own volatility and events; sizing otherwise stays the general vol-targeted rule (4.7).

---

## Numbers worth carrying

| Number | What it means | Source (label) |
|---|---|---|
| 50 to 100 bp per month | Gain from some stop rules during stop-out periods, US equities to bonds, 1950-2004 | Kaminski thesis abstract (Abstract) |
| Random walk: stopping premium < 0 | A simple stop always lowers expected return without momentum | Kaminski and Lo 2014 (Abstract) |
| 3% / 7% / 10% / 12% trailing stop: Sharpe -0.11 / 0.31 / 0.52 / 0.54 vs 0.56 with no extra stop | Tight stops destroy a trend strategy; wide ones roughly match it | Clare et al. 2013, S&P 500 1988-2011 (Read) |
| Buy-and-hold Sharpe 0.31 vs 200-day breakout 0.56 | The trend exit itself does the risk control | Clare et al. 2013 (Read) |
| Monthly Sharpe 0.17 to 0.40; worst month -49.8% to -17.4% | 15% stop on stock momentum, gross of costs | Han, Zhou and Zhu 2016 (Secondary) |
| ~10-11% of positions stopped per month | Stop activity in that momentum test | Han, Zhou and Zhu 2016 (Secondary) |
| 0.2% half-spread | Cost used for single-stock stop simulations | Lo and Remorov 2017 (Secondary) |
| Next-day execution > immediate, most for tight stops | Reversion after a stop trigger | Lo and Remorov 2017 (Secondary) |
| Gross -$45k vs costs -$1.66M | Costs dominate a 13-minute-hold human day-trading book | Garvey, Murphy and Wu 2005 (Read) |
| $4.3k to $14.4k per trader per year | Extra loss of traders who raise risk after morning losses | Garvey, Murphy and Wu 2005 (Read) |
| 11 of 14 signal families: gross 0.07-1.50 pts vs 2.0 pts cost | Retail intraday OHLCV signals on MNQ do not clear costs | Mesfin 2026 (Read) |
| t-stat +4.30 to -2.78 with a 15-minute delay | Edge realised inside the first bar; supports short time exits | Mesfin 2026 (Read) |
| 80.7% stop-out at a 20-point stop | Pullback entry mostly caught reversals | Mesfin 2026 (Read) |
| f* 17.5% to ~12% | Kelly fraction at stop for p=0.45, b=2 when costs = 0.1R | Worked math (judgment) |
| Halving stop distance doubles cost in R | Why tight stops lose after costs | Worked math (judgment) |
| Up to ~$44 | Scenario P&L shift from filling the unstressed factor with its conditional mean | Cai, Haugh and Li 2026 (Read) |
| ±$3 shown vs -$20 true | Portfolio tuned to the named stress factors hides its risk | Cai, Haugh and Li 2026 (Read) |
| <10% vs 50% target coverage | Naive scenario intervals in extreme cells | Cai, Haugh and Li 2026 (Read) |
| 16 scenarios; extreme = 3 x scan range, 30-33% counted | CME SPAN per-contract grid | CME pages (Snippet) |
| 7-9 Aug 2007 unwind, rebound 10 Aug | Multi-strategy liquidation, then stops and deleveraging, then rebound | Khandani and Lo 2007/2010 (Abstract, Snippet) |
| CL: 1,000 bbl; $10 per tick; daily break 4-5 pm CT | Contract facts | CME spec page (Read) |
| CL last trade: 3 business days before the 25th of prior month | Roll must happen before this | CME spec page (Read) |
| EIA petroleum Wed 10:30 ET; gas storage Thu 10:30 ET; holiday shifts | Event calendar must be data | EIA schedules (Read) |
| ~10% gas price move per 1% inventory shock | Size of inventory-surprise response (units to check) | Halova, Kurov and Kucher 2014 (Snippet) |
| Stronger effect for OPEC cuts and holds; WTI vs Brent differ | OPEC event typing | Loutia et al. 2016 (Snippet) |
| Sharpe up to 4.39; ~3.6% a year lost by index investors | Value of trading ahead of index roll windows | Mou 2010 (Snippet) |
| 10:1 leverage cap on non-gold commodity CFDs (EU retail, 2018) | Hard ceiling for energy CFD sizing where it applies | ESMA 2018 (Snippet) |
| Out-of-sample R² 47.3% own vs 49.2% pooled; FX HAR 28.6% vs 47.7% | Pooled volatility dynamics beat per-instrument fits | Bollerslev et al. 2018 (Read) |
| ~30% lower forecast variance; ~0.5% of wealth a year | Benefit of pooled, smooth volatility models | Bollerslev et al. 2018 (Read) |
| SD of rule Sharpe across instruments 0.59 vs 0.50 from luck | Edge is only a little more instrument-specific than chance | Carver 2026 (Read) |
| Critical distance 1.65 (1y), 0.74 (5y), 0.53 (10y), 0.37 (20y), 0.26 (40y) | When two instruments' rule Sharpes are really different | Carver 2026 (Read) |
| Pool under 5 years; own over 25; pooled weight (25 - N) x 0.05 | Default/override blend by history length (untested heuristic) | Carver 2026 (Read) |
| Shrink factor = 1 - 1/var(t) within family | Empirical Bayes shrink toward the family prior | Chen and Dim 2025 (Read) |
| -8%/+9% in-sample shrunk to about -3%/+2% | Typical size of shrinkage in a noisy family | Chen and Dim 2025 (Read) |

What I could not find: a measured, cost-adjusted study of "cut at a fixed fraction of the stop when the premise
fails", and any peer-reviewed test of breakeven-stop moves. Both have to be measured on QMX's own trade paths
(gap 2.3).
