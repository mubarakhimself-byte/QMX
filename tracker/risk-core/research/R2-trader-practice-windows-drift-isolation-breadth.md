# R2: Trader practice on sniping windows, live drift, market isolation, breadth and profit sweeps

Written 2026-11-03 for the risk-core design session. Research only: it reports practice and evidence and does not design QMX. Nothing here is ratified.

## How to read this

- **Labels.** Each claim cites a URL or a `path:line`. **[judgment]** marks my own opinion. **[arithmetic]** marks numbers I computed. The scripts are `D:\QMX-worktrees\risk-plan\tracker\risk-core\research\R2-scripts\checks.py` and `...\R2-scripts\breaker.py` (standard-library Python; run with `python -I`). They assume Gaussian, independent trades with a standard deviation of 1R. **RETAIL** marks retail jargon or a retail vendor source.
- **Short paths.**

| Alias | Path |
|---|---|
| `R05` | `D:\QMX-worktrees\risk-plan\tracker\risk-sizing\research\05-academic.md` |
| `R08` | `D:\QMX-worktrees\risk-plan\tracker\risk-sizing\research\08-old-qmx-testing-and-decay.md` |
| `R30` | `D:\QMX-worktrees\risk-plan\tracker\risk-sizing\research\30-desk-analysis.md` |
| `R37` | `D:\QMX-worktrees\risk-plan\tracker\risk-sizing\research\37-mis-academic.md` |
| `OW` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\seeds\operator-words-2026-11-03.md` |
| `G3`, `G6` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\grounding\G3-old-system.md`, `...\G6-book-bms-levels-and-paper.md` |

- **Not redone.** I cite the earlier files and do not repeat them on: Kelly and drawdown odds (`R05:202-210`), CUSUM and decay checks (`R08:42`, `R08:283-313`), session and fix evidence (`R30:101-116`, `R37:47-48`, `R37:69-70`), and 1/N and HRP (`R05:161-162`).

## Short answer

1. **"Sniping window" is not a professional term.** Retail traders use "sniper entry" for a precise, patient entry; most sources are courses and indicators for sale (search results, e.g. https://www.tradingview.com/script/IjxinGvz , RETAIL). "Kill zones" are ICT retail jargon for four session windows (https://innercircletrader.net/tutorials/master-ict-kill-zones/ , RETAIL). To professionals, "sniping" means latency arbitrage: picking off stale quotes in microseconds (https://cramton.umd.edu/market-design-papers/aquilina-budish-o'neill-quantifying-the-hft-arms-race.pdf). The professional relatives are time-of-day effects, benchmark fixes and scheduled-event windows.
2. **Edge after costs in those windows is mixed.** Costs are lowest when activity is highest: FX spreads are narrow in London hours and widest at 21:00-22:00 GMT (https://www.nber.org/system/files/working_papers/w12413/w12413.pdf). The fix reversal is real, about 2.5 bp a day, but it turns negative at full quoted spreads and positive only at half spreads (https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf). At news, spreads widen in the minute before, and much of the price jump comes before the volume does (https://www.jstor.org/stable/40282668). So a window lowers cost or raises activity. It does not hand out edge.
3. **Nobody can tell a bad day from a broken edge quickly.** The CFM fund's own researchers say a drawdown test "cannot separate" bad luck from an overstated Sharpe ratio and should be used as a precautionary signal (https://ar5iv.arxiv.org/html/1707.01457). At a Sharpe of 0.5 there is a 5% chance a normal drawdown lasts about 7 years (same source).
4. **Pods use a two-step drawdown ladder, but the numbers are second-hand.** The WSJ, as reported by eFinancialCareers, says a 5% loss halves a Millennium PM's capital and 2.5% more usually ends the job (https://www.efinancialcareers.com/news/pratik-madhvani-glen-scheinberg). Millennium's own filing only says "prescriptive risk controls" and pay judged "over a multi-year period" (Millennium 2024 MIFIDPRU disclosure, p. 8: https://www.mlp.com/wp-content/uploads/2025/09/2024-MiFIDPRU-8-Disclosures-Final.pdf).
5. **Sequential tests need hundreds of trades.** To decide between "no edge" and "+0.1R edge" at 5% error each way, an SPRT needs about 540 trades on average, and about 900 when the truth sits halfway between **[arithmetic]**. A CUSUM needs about 240 trades to flag an edge falling from +0.1R to 0 (`R08:42`). So fast protection must be loss rules, and edge checks are slow.
6. **A "two losses and stop" breaker fires most days for a scalper.** At a 55% win rate and 10 trades a day, the chance of two losses in a row somewhere in the day is 79% **[arithmetic]**. The old two-strike breaker (`G3:184-187`) was built for bots that trade a few times a day. A scalper's breaker has to scale with its trade count.
7. **Exchanges isolate markets in two layers.** Single products pause on their own: Limit Up-Limit Down pauses one stock, and CME's dynamic breakers halt one future. Market-wide breakers at 7%, 13% and 20% halt everything (https://www.sec.gov/investor/alerts/circuitbreakersbulletin.htm ; https://www.cmegroup.com/solutions/market-access/globex/trade-on-globex/faq-dynamic-circuit-breakers.html). Funds read risk-off from correlation spikes, turbulence, liquidity drying up together, volatility jumps and safe-haven moves (§3.3).
8. **Breadth carries a weak edge only if the bets are independent.** IR = IC × √breadth (Grinold 1989, via https://am.vontobel.com/en/insights/from-a-consultants-perspective-active-investing-in-emerging-markets?lang=en). With an average correlation ρ between bets, the Sharpe ratio can never exceed (per-bet Sharpe) ÷ √ρ, however many bets there are **[arithmetic]**. At 0.05R per trade and ρ = 0.05 that ceiling is 0.22.
9. **Sizing that leans on the edge number is fragile.** Errors in expected returns did about 11 times more damage than errors in variances (Chopra & Ziemba 1993, quoted in DeMiguel et al. 2009; https://scinapse.io/papers/2164883547). That is why professionals size many-strategy books mainly by risk (1/N in risk units, equal risk contribution) and use the edge as a gate (`R05:161`, `R05:182`).
10. **Profits are swept and pay is netted.** Hedge funds pay fees only above a high-water mark (https://ideas.repec.org/a/bla/jfinan/v58y2003i4p1685-1718.html). Funded-account prop firms let traders withdraw profit, but after a Topstep payout the loss limit "resets to $0 permanently", so the remaining balance becomes the whole cushion (https://help.topstep.com/en/articles/8284233).

---

## 1. Sniping windows

### 1.1 What the words mean

| Term | Who uses it | Meaning | Status |
|---|---|---|---|
| Sniper entry / sniping | Retail courses, indicator sellers | A precise entry at a planned price, after waiting for confirmation. No standard definition (search results, e.g. https://www.tradingview.com/script/IjxinGvz) | RETAIL; mostly marketing |
| Kill zone | ICT (Michael Huddleston) followers | Four windows in New York time: Asian, London 02:00-05:00, New York 07:00-09:00 or 07:00-10:00, London close 10:00-12:00 (https://innercircletrader.net/tutorials/master-ict-kill-zones/). Sources disagree on the exact hours (https://backtrex.com/en/blog/ict-kill-zones-trading-hours-strategy) | RETAIL. A prop-firm guide says "The time window does not produce any edge" (https://audacity.capital/trading-guides/ict-kill-zones/) |
| Sniping, picking off stale quotes | Market-structure research, regulators | Latency arbitrage. A FTSE 100 stock sees about one race a minute; the modal race is won by 5-10 microseconds and pays about half a tick (https://cramton.umd.edu/market-design-papers/aquilina-budish-o'neill-quantifying-the-hft-arms-race.pdf). Also used for competing algorithms in https://arxiv.org/pdf/1912.04012 | Professional, and out of reach for a retail account **[judgment]** |
| Session open, overlap | Everyone | Hours when a regional market opens or two overlap. London-New York holds the largest share of cross-region deals (https://www.nber.org/system/files/working_papers/w12413/w12413.pdf) | Professional and well documented |
| Fix | Dealers, regulators | A benchmark rate set in a short window. The WM/Reuters London fix is at 16:00 London (https://mpra.ub.uni-muenchen.de/81583). Others are the Tokyo fix and the ECB rate (https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf) | Professional |
| News or event window | Everyone | Minutes around a scheduled release | Professional |

### 1.2 Evidence by window: does edge after costs rise?

| Window | What is documented | After costs? | Source |
|---|---|---|---|
| Active session hours, overlaps | Deals, volume and volatility move together. More deals go with narrower spreads. EUR/USD spreads are narrow in London hours, widen after 16:00-17:00 GMT and peak at 21:00-22:00. Opens themselves had "insignificant effects" on spreads | Lower cost; the paper makes no claim about edge | https://www.nber.org/system/files/working_papers/w12413/w12413.pdf |
| Fixes (Tokyo, ECB, London 16:00) | The dollar rises about 2.5 bp before the fixes and falls the same afterwards, in 9 currencies over 1999-2019. The cause is dealers hedging fixed dollar demand | Gross Sharpe up to 2.45. At full indicative spreads the Sharpe is negative; at half spreads it is 0.12 to 1.03 | https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf ; JF 2024 version: https://wrap.warwick.ac.uk/id/eprint/177333 |
| London 16:00 fix | "Extraordinary volatility and negative serial correlation" around the fix (21 currencies, about 10 years) | Not tested | https://mpra.ub.uni-muenchen.de/81583 |
| Month-end London fix | Equity gains over the month predict the currency weakening before the month-end fix, as equity managers rebalance hedges | Abstract makes no cost claim | https://www.sciencedirect.com/science/article/abs/pii/S1386418114000779 |
| Gold PM fix | Gold futures volume up over 50% and volatility over 40% around the fix | Activity, not edge | `R37:69` |
| Intraday momentum into the close (futures, ETFs) | The first half-hour predicts the last half-hour, and the rest of the day predicts the last 30 minutes, across 60+ futures | Survives costs in the ETF study | `R37:47-48` |
| Scheduled news | Volume spikes even when the number matches forecasts. Much of the price jump comes before the volume surge | The jump goes to the fastest | https://www.jstor.org/stable/40282668 |
| Seconds before news | HFT spreads widen by over 30% and dealer spreads by 10% in the minute before an announcement (FCA Occasional Paper 63; read only as a search excerpt, so the market studied is not confirmed) | Cost rises just when the move comes | https://www.fca.org.uk/publication/occasional-papers/op63.pdf |
| Stocks at the open | An opening-range breakout limited to "stocks in play" (unusual relative volume) had a net Sharpe of 2.81 for the top 20 | Net of costs, one period | `R37:72` |

**Worked number [arithmetic].** 2.5 bp of EUR/USD at 1.10 is about 2.75 pips. A trade into and out of each fix pays the spread twice. The paper's result depends on whether the trader pays the full quoted spread or half of it. Where a cTrader account sits is something QMX's own cost journal can answer **[judgment]**.

### 1.3 Reading for QMX [judgment]

- The honest meaning of a sniping window is a **time slice where a unit's measured net edge, in R, is higher than in the rest of its day**. That is a property of one unit on one instrument. A clock cannot hand it out.
- Windows are where activity and liquidity concentrate (Ito-Hashimoto; `R30:101-107`). For a scalper, lower cost can turn a gross edge into a net one. That is a cost effect, not a new edge.
- Picking a unit's hours from its own backtest P&L is look-ahead (`R30:109-111`). A window should be chosen on one period, judged on a later one, and counted as a try.

---

## 2. Live results drifting from the backtest

### 2.1 Why "bad day or broken edge" cannot be answered fast

- **The CFM method.** Model P&L as a random walk with drift. For a strategy with Sharpe SR, the drawdown length and depth that occur with only 5% chance are about 2.14 ÷ SR² years and 1.50 ÷ SR in units of annual volatility (fits for a 10-year window). A drawdown outside those bounds is a reason to worry, but the test "cannot separate" bad luck from an overestimated Sharpe ratio, so the authors use it as a precaution and to update the Sharpe ratio (https://ar5iv.arxiv.org/html/1707.01457).
  - Worked numbers from the fit **[arithmetic]**: SR 0.5 → 8.6 years and 3.0 × annual volatility (the paper itself says about 7 years); SR 1 → 2.1 years and 1.5 ×; SR 2 → 0.5 years and 0.75 ×.
- **The triple penance rule.** Under standard assumptions it takes about three times as long to climb back from the worst likely loss as it took to fall into it, "regardless of the PM's Sharpe ratio". The paper also explains why firms give higher-Sharpe PMs looser stop-outs (https://escholarship.org/content/qt758637dr/qt758637dr.pdf ; https://www.quantresearch.org/AllAboutAlpha_%20Hedge%20Fund%20Trends%20&%20Alternative%20Investment%20Analysis%20%C2%BB%20Doing%20Penance%20for%20the%20Draw-down%20%C2%BB%20Print.pdf). Serial correlation in hedge fund returns cut the penance factor to as low as 1.6 (same summary).
- **A unit's normal pain, in R [arithmetic].** For a unit with +0.05R per trade and a standard deviation of 1R, the drawdown at a random moment follows P(DD > d) = e^(−2μd), with μ the edge per trade. So there is a 50% chance it sits 7R below its peak, 20% for 16R and 5% for 30R. Over 2,000 trades the worst drawdown has a median of 27R and a 95th percentile of 50R. In 200 trades at a 55% win rate, a run of 7 or more losses happens 33% of the time, 8 or more 17%, and 10 or more 3.5%. **Correction:** `R08:279` quotes a practitioner page saying a 10-loss streak appears in about 30% of 200-trade windows. My computation gives 3.5%; the practitioner's 30% fits a 7-loss streak.
- **Sharpe ratios are measured with error.** Their standard error is about √((1 + SR²/2) ÷ n) for n independent observations, and serial correlation can overstate an annual Sharpe by up to 65% (Lo 2002, via https://ideas.repec.org/a/taf/ufajxx/v58y2002i4p36-52.html and search summaries).
- **Backtests overstate.** Backtest Sharpe barely predicted live Sharpe across 888 algorithms, and more backtesting meant a bigger gap (`R05:29`).

### 2.2 The tools desks use

| Tool | What it answers | Speed (one worked case) | Source |
|---|---|---|---|
| Fixed band (Monte Carlo cone) | Is live equity inside the band the backtest drew? | Checked at any time; it fires late for slow decay | StrategyQuant Predict & Verify; QuantConnect reconciliation (`R08:255-259`) |
| Drawdown depth and length bands | Is this drawdown longer or deeper than 5% odds allow? | Years at a low Sharpe | https://ar5iv.arxiv.org/html/1707.01457 |
| CUSUM on per-trade R | Did the average edge drop? | About 240 trades for +0.1R → 0 at one false alarm per 1,000 trades | `R08:42`, `R08:268-270` |
| SPRT (Wald) | Edge = 0 or edge = target? Stops as soon as the evidence suffices | H0 "0R" against H1 "+0.1R", 5% error each way: bounds ±2.94 on the summed log-likelihood ratio. Mean about 540 trades and median about 430 when either hypothesis is true; about 900 when the truth is +0.05R, and then it splits 49/51 **[arithmetic]** | Bounds and optimality: https://en.wikipedia.org/wiki/Sequential_probability_ratio_test ; https://commit-web.commit.tu-berlin.de/en/book/fsi/chapter/ch04/section/s01 |
| E-values | Evidence that may be checked after every trade without breaking the error rate; suited to "loosen only on proof" | Depends on the edge | `R05:368` |
| Input checks | Did fills, cost, trade rate or holding time change? These drift before profit does | Fast; tens of trades | `R08:280`, `R08:303-304`. Carver checks realised against expected risk daily and costs against expectation every couple of weeks (`R30:52`) |
| Stacked alert levels | Green, yellow (CUSUM above 70% of its limit, size down), orange (stop new trades), red (paper until re-proven) | n/a | PRACTITIONER (`R08:275`) |

One-line maths for the SPRT **[arithmetic]**: each trade x adds (μ1 − μ0)(x − (μ0 + μ1)/2) ÷ σ² to the score. Stop at ln((1 − β)/α) = +2.94 ("edge is +0.1R") or ln(β/(1 − α)) = −2.94 ("no edge"). With μ0 = 0 and μ1 = 0.1, a +1R win adds 0.095 and a −1R loss adds −0.105.

### 2.3 Pod and prop drawdown rules

| Firm type | Rule | Reliability | Source |
|---|---|---|---|
| Millennium (pod) | A 5% loss halves capital; a further 2.5% usually means fired | Press (WSJ via eFinancialCareers); Millennium declined to comment | https://www.efinancialcareers.com/news/pratik-madhvani-glen-scheinberg |
| Millennium (filing) | "Prescriptive risk controls"; pay reflects risk "over a multi-year period"; malus and clawback up to three years | Primary | Millennium 2024 MIFIDPRU disclosure, p. 8 (https://www.mlp.com/wp-content/uploads/2025/09/2024-MiFIDPRU-8-Disclosures-Final.pdf) |
| Multi-managers in general | A mid-single-digit loss cuts the allocation; a high-single-digit or about 10% loss from peak and the PM is asked to leave | Secondary explainer | https://capitalgains.thediff.co/p/multimanagerpodhedge-fund-101 |
| Pods after the cut | Firms recruit traders after a bad streak elsewhere (Bloomberg headline only) | Press, read as a title | https://www.bloomberg.com/news/articles/2025-09-10/hedge-funds-even-millennium-and-citadel-s-losing-traders-are-hot-recruits |
| Topstep (futures prop) | "Call down" to sim after patterns of losses, never one bad day; "call up" after consistency, never automatic | Firm's own help page | `R08:262` |
| Retail prop | Size zones by share of the loss limit used: 0-30% full size, 30-60% half, 60-80% micro, 80%+ stop | RETAIL | `R08:264` |
| FTMO (retail prop) | Daily loss 3% (1-Step) or 5% (2-Step) of starting capital, measured on equity against the midnight CET balance. Total loss 10%, static (2-Step) or trailing on end-of-day highs (1-Step) | Firm's own page | https://ftmo.com/en/trading-objectives/ |

Note the shape: one level cuts size and a second level stops. Both are measured from a peak, and the step-down is big (half), not gradual **[judgment]**. A cut also forces the trader to rebuild on less capital. Under the triple penance rule, recovery after a halving takes longer still **[judgment]**.

### 2.4 Probation and re-promotion

- **Old QMX.** A Kelly discount of about 0.85 on first live trading, with exit criteria never written (`G3:196-198`). Re-promotion after a demotion needed tier T2 or better, 10 profitable demo trades in a row and the operator's click (`R08:75`).
- **Retail prop.** FTMO's scaling plan adds 25% to the balance and raises the split to 90% for consistent traders (https://ftmo.oanda.com/reward-growth-and-scaling-plan/). Sources disagree on the exact profit condition (https://backtrex.com/en/blog/prop-firm-scaling-plan-guide , RETAIL). Topstep's call-up needs shown consistency (`R08:262`).
- **The statistical version.** Loosen only when an e-value on trades after the cut passes 1/α, for example 20, plus a minimum time (`R08:315`). A ratchet that only tightens drifts to the minimum size, because it tracks the lowest value of a noisy estimate (`R05:240`).
- **What 10 wins in a row proves [arithmetic].** A coin-flip unit with a 50% win rate makes 10 straight wins with probability 0.1%. A unit paying +0.5R per win and −1R per loss has zero edge at a 2/3 win rate, and it still makes 10 straight wins 1.7% of the time (2.8% at 70%, where its edge is only +0.05R). Win streaks say little about the edge of a high-win-rate unit.

### 2.5 Reading for QMX [judgment]

- His instinct, "size down, but not quickly", matches practice: no desk stops a strategy on one bad day (Topstep, `R08:262`). Desks cut by a large step at a pre-set drawdown and stop at a second.
- The two-speed split stands: loss rules act at once, and edge tests take hundreds of trades (`R08:313`).
- The fastest honest signal is **inputs**: costs, fills and trade rate (§2.2). A unit whose costs doubled is broken today, whatever its P&L.

---

## 3. Circuit breakers and market isolation

### 3.1 Exchange breakers as a concept

| Breaker | Trigger | Action | Scope | Source |
|---|---|---|---|---|
| US market-wide | S&P 500 down 7% or 13% from the prior close | 15-minute halt (none at or after 15:25) | Whole market | https://www.sec.gov/investor/alerts/circuitbreakersbulletin.htm |
| US market-wide | S&P 500 down 20% | Halt for the rest of the day | Whole market | same |
| Limit Up-Limit Down | Price outside a 5%, 10% or 20% band around the last 5 minutes' average (bands double near the open and close) | 5-minute pause if the price does not come back within 15 seconds | One stock | same |
| CME dynamic circuit breakers | Metals: a ±10% move in a rolling 60-minute window | 2-minute halt; the band "moves with the market" | One product | https://www.cmegroup.com/solutions/market-access/globex/trade-on-globex/faq-dynamic-circuit-breakers.html (read as a search excerpt; the page timed out) |
| CME velocity logic | Price moves "too far, too fast" inside a short lookback | Halt of the future and its options | One product | https://cmegroup.com/education/demos-and-tutorials/understanding-velocity-logic.html (search excerpt) |
| Firm kill switch | Firm, account or product level | Disable trading and cancel resting orders | Chosen scope | https://www.fia.org/sites/default/files/2019-05/Order-Handling-for-Executing-Brokers.pdf (search excerpt) |

The pattern **[judgment]**: one small breaker per product that pauses and then resumes, one big breaker for everything, and levels that move with the market rather than being fixed prices. A pause is the normal action. A stop for the whole day is reserved for the top level.

### 3.2 The old QMX breakers

- Two breakers: an acute one (two strikes in a day, on the node) and a chronic one (WF3 pool cleaning) (`R08:203`).
- Acute: on the first hit the bot keeps trading; on the second in the UTC day it goes to paper or demo; the count resets at rollover. "Hit" was a loss streak, fee burn, failed recoveries or a falling rating, with every threshold missing. Other files say every full-stop loss counts as a hit (`G3:184-187`).
- WF3 read how often the breaker fired in a rolling window as decay evidence (`R08:229`).

**How often a two-strike rule fires on a healthy unit [arithmetic]:**

| Trades a day | P(2+ losses in the day), 55% win | P(2 losses in a row), 55% win | P(2 in a row), 70% win | 95th percentile of daily losses, 55% win |
|---|---|---|---|---|
| 2 | 0.20 | 0.20 | n/a | 2 |
| 5 | 0.74 | 0.51 | n/a | 4 |
| 10 | 0.98 | 0.79 | 0.50 | 7 |
| 20 | 1.00 | 0.96 | 0.77 | 13 |

For an ORB unit trading once or twice a day, two strikes is a rare event and a fair alarm. For a scalper it is a normal day. The breaker's rare-event idea carries over; its fixed count does not **[judgment]**. A count tied to trade volume, such as "more losses today than the 95th percentile for this many trades", keeps the false-alarm rate the same across styles **[judgment]**. Fire density over many days (WF3's idea) is then real decay evidence, because a healthy unit fires only about 5% of days **[judgment]**.

### 3.3 How funds detect risk-off days

| Signal | What it shows | Evidence | Speed |
|---|---|---|---|
| Correlation spike | Correlation rises in bear markets, not in bull markets; large negative returns are far more correlated than a normal model predicts | Longin & Solnik 2001 (https://faculty.essec.edu/en/research/extreme-correlation-of-international-equity-markets) | Needs a window of returns: slow |
| Absorption ratio | The share of total variance taken up by a few principal components. It rises when markets couple, and spikes came before major US crashes | Kritzman, Li, Page & Rigobon 2011 (https://globalmarkets.statestreet.com/research/portal/insights/article/2a8e282a-343b-443c-b362-1634c71d2d26 ; review https://portfoliooptimizer.io/blog/the-absorption-ratio-measuring-financial-risk/) | Rolling window |
| Turbulence index | How unusual today's joint returns are (a Mahalanobis distance). Returns to risk are weaker in turbulence, and turbulence persists. Proposed as a filter to scale risk | Kritzman & Li 2010 (https://ideas.repec.org/a/taf/ufajxx/v66y2010i5p30-41.html ; https://alphaarchitect.com/skulls-financial-turbulence-and-risk-management/) | Daily or faster |
| Liquidity drying up together | FX liquidity moves in common across currencies and with stocks and bonds. Liquidity risk hit carry trades in 2007-2009 | Mancini, Ranaldo & Wrampelmeyer 2013 (https://www.snb.ch/en/publications/research/working-papers/2010/working_paper_2010_03) | Spread is observed directly: fast |
| Liquidity in stress | FX liquidity falls when funding is tight and global risk rises, and co-moves more in stress | Karnaukh, Ranaldo & Söderlind 2015 (https://papers.ssrn.com/abstract=2329738) | Fast |
| Volatility jump | A doubling of deseasonalised volatility shows within about 12 one-minute bars | `R05:62` | Minutes |
| Carry unwind | Carry crashes come when risk appetite and funding liquidity fall; unwinding grows as the VIX rises | Brunnermeier, Nagel & Pedersen 2008 (https://www.nber.org/papers/w14473) | Daily |
| Safe-haven moves | CHF and JPY rise against USD when US stocks fall and bond prices and FX volatility rise, over hours to days | Ranaldo & Söderlind 2010 (https://ideas.repec.org/a/oup/revfin/v14y2010i3p385-407.html) | Hours |

Reading **[judgment]**: the fast tells are spread and volatility against their usual levels for that hour. QMX's SQS and the seasonal-baseline idea already cover these (`R05:89-90`). Correlation and turbulence are confirmation over a day. For a class switch, the useful extra tell is co-movement: many instruments in one class showing wide spreads or a volatility jump at once.

### 3.4 How news calendars are tagged

- **Retail calendars** tag each event by currency and by "expected impact" in colours: red high, orange medium, yellow low, grey non-economic (https://fxnx.com/en/blog/forex-factory-impact-colours-red-orange-yellow-grey , RETAIL). One guide calls the impact level "a subjective assessment" (https://completetradersedge.com/how-to-read-a-forex-economic-calendar-like-a-professional/ , RETAIL).
- **Measured impact.** Research ranks releases by their measured price impact. Across 36 US releases, timing and the release's value for nowcasting GDP, inflation and the policy rate explain much of the bond-futures impact (https://www.federalreserve.gov/econres/feds/is-the-intrinsic-value-of-macroeconomic-news-announcements-related-to-their-asset-price-impact.htm). Surprises move FX within minutes, and bad news moves it more (`R30:21`). For gold, US employment, GDP, CPI and personal income matter most (`R37:69`).
- **What QMX ships.** The t3 calendar template blocks 30 minutes either side of high-impact releases and flags surprises. Its free feed lacks actual values, so it finds no surprise live (`R30:123`).
- **Tagging by region and instrument [judgment].** A release belongs to a currency or country. Each instrument maps to the currencies or exchange it depends on: EUR/USD to EUR and USD; gold to USD releases and the London fixes; an index CFD to its home exchange. The event-study measure per release and instrument (the "move and spread in the minutes after", `R30:124`) can replace the subjective colour.

### 3.5 Switching off one market class

- Exchanges already work this way. A per-product breaker halts one future or one stock while the rest trade; only the market-wide breaker stops everything (§3.1).
- Firm kill switches can be set at firm, account or product level (§3.1, FIA excerpt).
- No public source I found describes how a fund turns off one asset class by rule. Pod platforms cut per pod by drawdown (§2.3). This gap is marked in "Not verified".

---

## 4. Making a weak edge pay

### 4.1 The fundamental law

- IR = IC × √BR. IC is the correlation between forecasts and outcomes, and BR is the number of independent bets a year (Grinold 1989, JPM 15(3); citation via https://am.vontobel.com/en/insights/from-a-consultants-perspective-active-investing-in-emerging-markets?lang=en ; breadth = "independent investment opportunities", https://www.robeco.com/en-int/insights/2018/04/fundamental-law-of-active-management-shows-way-to-higher-information-ratio).
- Constraints cut this by a transfer coefficient: IR = TC × IC × √BR. Realised results are often only 0.3 to 0.8 of what the original law predicts (Clarke, de Silva & Thorley 2002, https://ideas.repec.org/a/taf/ufajxx/v58y2002i5p48-66.html).
- **Worked number [arithmetic].** A 1:1 bet that wins 52.5% has an IC of about 2p − 1 = 0.05, which is also its per-bet Sharpe at 0.05R per trade. With 2,000 independent bets a year, IR = 0.05 × √2,000 ≈ 2.2. The same bet taken 20 times a year gives 0.22.

### 4.2 Breadth needs independence

- Counting bets overstates breadth when bets are correlated. Effective breadth can be well below the bet count (Polakow & Gebbie, https://arxiv.org/abs/physics/0601166). Meucci's "effective number of bets" counts uncorrelated bets from the entropy of principal components (https://www.bayes.citystgeorges.ac.uk/__data/assets/pdf_file/0003/213699/Meucci-ReDefining-and-Managing-Diversification.pdf).
- **One-line maths [arithmetic].** For N bets of equal size with average pairwise correlation ρ: N_eff = N ÷ (1 + (N − 1)ρ), and Sharpe = s × √N_eff. As N grows, the Sharpe tends to s ÷ √ρ.

| Bets N, per-bet Sharpe 0.05 | ρ = 0 | ρ = 0.01 | ρ = 0.05 | ρ = 0.2 |
|---|---|---|---|---|
| 10 | 0.16 | 0.15 | 0.13 | 0.09 |
| 100 | 0.50 | 0.35 | 0.21 | 0.11 |
| 2,000 | 2.24 | 0.49 | 0.22 | 0.11 |

- **Units, by the day [arithmetic].** One unit making 10 trades a day at 0.05R has a daily Sharpe of 0.16 (2.5 a year). Ten such units with independent daily P&L give 7.9 a year. At a daily correlation of 0.3 between units they give 4.1, the same as 2.7 independent units.
- **Where correlation hides [judgment].** Trades at different hours on one pair are close to independent in their noise. The correlation that bites is shared exposure: several USD pairs on one US release, many classes on one risk-off day, or all edges of one logic fading together in a regime change. That last one is a correlation in the edge itself, not in the noise, and no bet count removes it.
- **Costs [judgment].** Breadth multiplies the net edge, whatever its sign. For scalpers, cost is the master state (`R05:409`), and an edge smaller than costs is no edge (`R30:181`). So many bets on a negative net edge lose faster and more surely.

### 4.3 "One unit gets $20 alone but ten units get $2 each?"

He asked about this directly (`OW:13`). Two different rules give two different answers **[arithmetic]**:

| Rule | Size of each of N units | 10 independent units | 10 units, ρ = 0.3 |
|---|---|---|---|
| Kelly (maximise growth) for independent small bets | The same as alone: μ ÷ σ² per bet | Each 1.0 × its solo size; total risk 3.2× | Each about 0.27× (scale by 1 ÷ (1 + (N − 1)ρ) = 1 ÷ 3.7) |
| Fixed total risk budget (volatility target) | 1 ÷ √(N(1 + (N − 1)ρ)) of the budget | 0.32 of the budget each, not 0.10 | 0.16 each |
| Plain split of a daily amount | 1 ÷ N | 0.10 each | 0.10 each |

- So "split a daily budget across units" is the volatility-target rule. Splitting by 1/N under-uses the budget when units are independent. With 10 independent units, each can carry about 3 times the 1/N share for the same total daily swing.
- "Each unit gets the size it would get alone" is the Kelly rule for independent bets. It means total risk grows with the number of units.
- The two are compatible: fix the book's daily risk, then the number of units and their correlation set each unit's share **[judgment]**.

### 4.4 Sizing when the edge is uncertain

| Method | What it does | Effect on a small edge | Source |
|---|---|---|---|
| Fractional Kelly | Bet c × Kelly. Half Kelly keeps about 75% of the growth; P(ever falling to 60% of the bankroll) is 60% at full, 22% at half, 3% at quarter Kelly | Scales everything | `R05:202-206` |
| Shrunk Kelly | Multiply Kelly by t² ÷ (1 + t²), where t is the edge's t-stat | 0.05R over 300 trades (t = 0.87) → 0.43; over 3,000 trades → 0.88 **[arithmetic]** | `R05:208-210` (derivation there) |
| Bayesian Kelly | Bet a fraction linear in the posterior mean edge; the cost of learning can be computed | Size grows as evidence builds | Browne & Whitt 1996 (https://econpapers.repec.org/RePEc:fth:colubu:95-03) |
| Lower-confidence-bound sizing | Size on edge − 1.645 × SE | 0.05R: zero size until about 1,100 trades; 0.40 of point Kelly at 3,000 **[arithmetic]** | Standard statistics; no fund source found |
| Risk-based sizing (1/N in risk units, equal risk contribution) | Each strategy gets the same risk; the edge only decides in or out | Does not depend on the edge number | 1/N: `R05:161`, `R05:182`. ERC: Maillard, Roncalli & Teiletche 2010 (https://www.msci.com/documents/10199/36c8ed57-cfad-4d77-8d40-6cbcc107a778 , summary) |

- **Why desks avoid sizing on point edges.** Errors in means did about 11 times the damage of errors in variances and 21 times that of covariances (Chopra & Ziemba 1993, as quoted in DeMiguel et al. 2009; https://scinapse.io/papers/2164883547). A re-simulation found the effect may be overstated (https://swopec.hhs.se/lunewp/abs/lunewp2003_017.htm).
- **Reading [judgment].** Lower-bound sizing is the strictest form of "lean on the edge". It gives a thin-edge scalper no size for months, against his goal. Risk-based sizing with the edge as a gate (a range: "positive with evidence") is what many-strategy books do. It fits his request to give the edge a range rather than a point (`OW:13`).

### 4.5 Volatility targeting

- Scaling exposure by the inverse of recent variance raised Sharpe ratios for equity factors (Moreira & Muir 2017, https://www.nber.org/papers/22208).
- Across 60+ assets it helped Sharpe only for risk assets, though it cut extreme returns everywhere (`R05:214`). In real time it did not beat unmanaged portfolios across 103 strategies (`R05:215`).
- Reading [judgment]: treat it as a tail-control tool at book level, not as a source of edge.

### 4.6 Caps across many strategies

- **Portfolio heat** (RETAIL term): the total loss if every open stop were hit at once, as a share of equity. It is commonly capped at 4-12%, lower for correlated books (https://therighttrader.com/learn/risk-management/portfolio-heat ; https://nexusfi.com/a/risk-management/portfolio-heat). Correlation "does not delete those dollars"; it changes how likely the stops are to be hit together (same sources).
- **Daily loss limits.** FTMO measures its daily limit on equity, open positions included, and resets it at midnight CET (https://ftmo.com/en/trading-objectives/). Old QMX had a day budget that drained and refused entries, but what drained it was never defined (`D:\QMX-worktrees\risk-plan\tracker\risk-core\STATE.md:21`).
- **Drawdown floor.** The optimal policy under a drawdown limit risks in proportion to the cushion above a floor that rises with the high-water mark (Grossman & Zhou; `R05:220-222`).

---

## 5. Profit sweeps and high-water marks

| Setting | How profit leaves and how losses are netted | Source |
|---|---|---|
| Hedge fund fees | Performance fees are paid only above the high-water mark, which limits what the fees are worth | Goetzmann, Ingersoll & Ross 2003 (https://ideas.repec.org/a/bla/jfinan/v58y2003i4p1685-1718.html) |
| Pod PM pay | A share of net P&L, often reported as 10-20%. Contracts "can set high-water marks, loss carry-forwards, deferral and clawback". Millennium publishes no standard percentage | Secondary (https://www.quantt.co.uk/resources/millennium-pm-salary) |
| Millennium (filing) | Pay is set annually; malus and clawback apply for up to three years | Primary, p. 8 (https://www.mlp.com/wp-content/uploads/2025/09/2024-MiFIDPRU-8-Disclosures-Final.pdf) |
| Topstep funded account | Withdraw up to 50% of the balance after 5 winning days of $150+; after a payout the loss limit "resets to $0 permanently"; a 100% payout closes the account | https://help.topstep.com/en/articles/8284233 |
| FTMO | Per its page, a Reward withdrawal resets the 1-Step trailing loss limit to 90% of initial capital. The best day must not exceed 50% of total profit (30% on Instant). Scaling adds 25% to the balance | https://ftmo.com/en/trading-objectives/ ; https://ftmo.oanda.com/reward-growth-and-scaling-plan/ |
| Old QMX Book | At rollover, if equity reached 2.5× seed, the Treasury swept equity above seed and reset the Book to seed. Today's code has operator-signed sweep acts with no cap check | `G6:75`, `G6:166`, `G6:40` |
| His open question | "Is the sweep cap thing coming back?" (deferred) | `D:\QMX-worktrees\risk-plan\tracker\risk-core\seeds\SEEDS.md:219-223`, `:312-316` |

Reading **[judgment]**:
- A sweep turns profit into safety for the owner but takes the cushion away from the trader. Topstep makes this explicit: after a payout, everything left can be lost.
- Pods do not compound a PM's capital from his own P&L. The firm resizes the allocation and pays the PM a share above his own high-water mark. A unit-level "sweep cap" is the same idea: the BMS, not the unit, decides whether profit stays in play.
- A consistency rule (best day ≤ 50% of profit) is a cheap guard against one lucky day passing as edge.

---

## 6. What this means for QMX [judgment]

All of this section is my opinion, offered as input for the design, not as design.

1. **Define a sniping window as a measured slice, not a clock.** Its definition: hours where one unit's net edge in R, on one instrument, is higher out of sample. Agents can propose candidates from activity and cost maps (sessions, fixes, releases). QMB proves them on later data, and each try is counted. The ICT hours are a starting list of candidates, not evidence.
2. **Size by risk and let edge be a gate with a range.** This answers his "don't lean on the edge" and "edge as a range" (`OW:13`). Units get equal risk shares inside a book budget. The edge decides only whether a unit trades (positive with evidence) and perhaps a small number of tiers. The number of units and their correlation set each share (§4.3). That is how many small bets carry the load.
3. **Breadth is the lever, and correlation is its limit.** Show "effective units" (N_eff) next to the unit count on the BMS. Ten scalpers on USD pairs during the London-New York overlap may be two or three bets. Breadth across classes and hours is worth more than more units on one theme.
4. **Keep three speeds of brake.** (a) Instant loss rules per unit and per day. (b) A breaker with a style-aware threshold, such as the 95th percentile of daily losses for that trade count, whose fire density over weeks is a decay signal (the old WF3 idea, kept). (c) Slow edge tests in hundreds of trades (CUSUM, SPRT, cone). Size steps down in one large step at a pre-set drawdown, stops at a second, and comes back only on new evidence (an e-value plus a minimum time).
5. **Market isolation should copy the exchange pattern.** Per-class pause on co-moving tells (spreads and volatility against their usual levels for that hour, across many instruments in the class, plus calendar events tagged by currency and instrument), resuming automatically when the tells clear. A whole-system stop is kept for a rare top level. The MIS supplies the tells; the BMS acts on them. Evidence first: each isolation rule should be scored on history for false alarms, the way the breaker table in §3.2 does.
6. **Check inputs before profit.** Cost, fill and trade-rate drift detects a broken unit in tens of trades. A P&L test needs hundreds.
7. **Sweep at book or BMS level, with a high-water mark.** A unit should not lose its whole cushion to a sweep. The Topstep rule shows what happens if it does.

## 7. Not verified

- Firecrawl credits ran out mid-run. After that I read pages with WebFetch and WebSearch summaries. Rows marked "search excerpt" or "summary" were not read in full: FCA OP63 (encrypted PDF), CME dynamic breakers (page timed out), FIA kill switch, Kritzman papers (paywalled), Chopra-Ziemba (quoted second-hand), Maillard et al. (summary), Lo 2002 standard error (secondary).
- The Millennium 5% and 7.5% figures rest on WSJ reporting via eFinancialCareers. Millennium's own filing gives no number.
- I found no public source on how a fund switches off one asset class by rule, and none on pod onboarding sizes or ramp schedules.
- Krohn et al.'s cost result uses indicative quotes. I did not check how cTrader ECN spreads compare with them.
- All SPRT, breaker, drawdown and breadth numbers come from my scripts. They assume independent Gaussian trades with SD 1R. Fat tails, streaks and regimes make real drawdowns deeper and tests slower.
- FTMO and Topstep rules were read on 2026-11-03 and change often.
