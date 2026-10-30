# 30. How trading desks analyse markets and strategies, and his day-to-day experience

Research ticket: `wayfinder/tickets/research-desk-analysis.md`. Written 2026-10-30 by research agent 4. Options and evidence, not a design. Out of scope: risk, sizing, the book, correlation between units. Companion: `research/29-agent-failure-modes.md` (how agent analysts go wrong).

## How to read this

**Labels.** CHECKED = read at the cited path and line, in the output of the cited command, or at the cited URL on 2026-10-30. PRACTITIONER = a trader's own report on a forum, blog or review (URL given). INFERRED = my reading. A point "any trader knows" is stated as such, not asked.

**Short names.** `T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md` (line = the line holding his turn). `TPL` = `origin/engine/base:qmx-agents/packages/qmx-engine/src/qmx_engine/templates` in `C:/Users/Mubarak/Desktop/QMX` (read with `git show`). `R18`, `R19`, `R42` = research 18, 19, 42.

**Numbers.** Every cadence or threshold below is a named number with a starting default. None is settled.

---

## 0. Short answer

1. **Every desk runs the same loop at different speeds:** prepare before the market, watch during it, review after it, re-plan weekly, recalibrate rarely. Only the clock changes with style. A scalper's loop turns per session, an intraday trader's per day, a swing trader's per week (INFERRED from the practitioner sources in §2; any trader knows the shape).
2. **Discretionary desks review from charts and numbers; systematic desks from numbers only.** A prop desk grades three things each day (the idea, how it was traded, the preparation) and replays charts "bar by bar" (SMB Capital, PRACTITIONER). A systematic trader reads text reports: warnings by email, verbose reports on disk, costs per trade, realised against expected risk (Carver, PRACTITIONER). For unit analysis the systematic pattern fits. For market analysis an agent can use both (research 29 §6).
3. **Weekly market selection is honest only on what can be forecast.** Volatility, liquidity, cost and the event calendar can be known or forecast a week ahead. Direction and "which pair my bot will win on" cannot. The old system's own rule says the same: not trading a pair this week "has to be backed by a lot of evidence" (R19 §2, CHECKED there).
4. **Session habits are a real almanac for activity, not for profit.** Volume and volatility by time of day are strong and stable in gold and FX (Batten et al. 2017; Caminschi and Heaney on the gold fix; Andersen et al. on announcements; all CHECKED). "Gold moves at the New York open" is honest. "My unit makes money at the New York open", picked from the same backtest it is judged on, is look-ahead. A retail guide that drops a robot's losing weekdays after three months of stats shows the trap exactly (tlap.io, CHECKED).
5. **Fundamentals enter intraday trading as scheduled surprises.** FX jumps within minutes of an announcement surprise; volatility settles more slowly; bad news moves more than good (Andersen, Bollerslev, Diebold and Vega 2003, CHECKED). The shipped calendar template already sets blackouts and scores surprises, but its free feed has no actual values, so it finds no surprise live (CHECKED `TPL/t3-news-calendar-watch/README.md`).
6. **The shipped templates cover the news half and none of the trading half.** Calendar watch, overnight research desk, morning brief and morning digest run today. Every template that reads trades, units or MIS state is a draft waiting on the trading node or the backtest door (R18 §1.5, CHECKED there). The shipped "weekly review" reviews the engine's own workflow runs, not markets or units (CHECKED `TPL/rv-weekly-review/README.md`).
7. **His day-to-day experience today, on any retail platform, stalls in the same six places** (§8): the backtest-to-live gap in fills and costs, optimisation with no count of tries, data that differs by source, review that is manual and not linked back to the test, markets and hours picked by hand from noisy stats, and monitoring that only asks "is it running?". Units, journals, QMX workflows and the MIS map onto five of the six. None of them removes real execution costs or makes a weak edge strong.

---

## 1. His words (seeds, not rulings)

- "A human trader who's a scalper will not wake up at the same time to look at charts as a person who day trades" (T2:135, CHECKED).
- "So intraday and scalpers, but mostly scalpers" (T1:376, CHECKED). Swing trading "is not going to be so much" (same line).
- On session study: an opening-range-breakout unit at the New York open, "this is now we are doing maybe a weekly or fortnight or bi-weekly analysis" (T1:1903, CHECKED).
- On premium hours: the London and New York overlap is good "especially for scalpers"; "Gold has one of the cleanest moves for most people." (T1:442, CHECKED)
- On fundamentals: wire MIS variables to a QMX workflow that is agentic; "It can do the fundamental analysis." (T1:376, CHECKED)
- Split analysis into markets and units (T2:385, CHECKED). Agents "can request for that day's data" like a trader with a journal at day's end (T2:325, CHECKED).
- On platforms: "I think MT5 is the best example, or CTrader or Ninja Trader" (T1:783, CHECKED); "Strategy Quant is better in terms of testing"; "Quant Connect is heavy, that's all I can say." (T1:828, CHECKED)
- "Multiple experiences": "if me, I'm a user, how am I going to be using units, okay, to literally trade and make money" and why that gives "a beefier advantage compared to a person just using a simple bot" (T2:858, CHECKED).

---

## 2. How desks analyse, by kind of desk

### 2.1 Discretionary prop desk

- **Daily report card.** Each trader sets a few goals and grades each one A to F at day's end, with reasons; the coach replies daily and they review weekly (Steenbarger, TraderFeed 2008, http://traderfeed.blogspot.com/2008/03/using-trading-journals-to-improve.html, PRACTITIONER). SMB says the report card did more for its traders' results in 2017 than anything else (https://www.smbtraining.com/blog/the-biggest-spark-for-our-trading-improvement-in-2017, PRACTITIONER).
- **Three grades a day.** The quality of the idea, how it was traded (entry, size, management, exit), and the preparation; every trade is replayed on the charts bar by bar (SMB review talk, https://www.smbtraining.com/blog/how-to-conduct-a-professional-review-of-your-trading, PRACTITIONER).
- INFERRED for QMX: "idea versus execution" is the split between a unit's logic and its fills. The unit-analysis family can grade both separately from the journal.

### 2.2 Systematic desk

- **Warnings by email, detail on disk.** One daily report holds only problems, the other is verbose; any report reruns on demand for other dates (Carver, https://qoppac.blogspot.com/2015/09/systems-building-checks-and-balances.html, PRACTITIONER).
- **Monitor and reconcile.** Did each process run on time; do positions, fills and the broker agree; are any forecasts missing; is anything switched off or overridden and forgotten (same page).
- **Costs and risk.** Every trade's cost against mid and against crossing the spread, daily; total costs against expectations every couple of weeks; realised against expected risk daily (https://qoppac.blogspot.com/2015/08/systems-building-accounting.html, PRACTITIONER).
- **He reads profit and loss last.** He calls daily P&L "just random numbers" (same page).
- INFERRED for QMX: this is the "monitoring vs observability" split he made in July (R19 §8). Most of it is scripts with no model call; an agent only explains a flagged item.

### 2.3 Retail EA operator

- **Morning:** check the server and the platform are connected and the EA is on; read overnight trades; three numbers (equity, margin level, floating loss); flag the day's red calendar events. About 15 to 20 minutes (https://fxtool.co/en/classroom/day-in-the-life-ea-trader-routine, PRACTITIONER).
- **Weekly:** export trades; compare win rate and profit factor with the backtest; inspect parameters but do not change them before about 100 trades (same page). Others say weekly plus alerts is enough and daily checking breeds meddling (https://botfxpro.io/monitor-forex-ea-remotely-tools-best-practices/, PRACTITIONER).
- **Switch-off rules set in advance:** drawdown beyond the backtest's worst, a regime change, odd behaviour, a losing streak longer than tested (https://forexr.com/learn/running-an-ea-24-7, PRACTITIONER).
- **Tools:** the platform's Experts and Journal tabs, phone push alerts, Myfxbook for curves and per-hour and per-weekday statistics (same pages; https://www.pro-scalper.com/questions/how-to-monitor-your-xauusd-expert-advisor-remotely).

### 2.4 Rhythm by style (stated; any trader knows the shape)

| Loop step | Scalper | Intraday | Swing |
| --- | --- | --- | --- |
| Prepare | 15-30 min before each session they trade | Before the day's main session | Sunday, plus a look at each daily close |
| Watch | Continuously in session: spreads, news blackouts, fills | A few checks a day | Alerts only |
| Review | After each session, and a daily summary | End of day | Weekly |
| Re-plan markets | Daily or weekly | Weekly | Weekly to monthly |
| Recalibrate | Monthly, on enough trades | Monthly to quarterly | Quarterly or less |

The numbers in this table are defaults for QMX workflow triggers, not facts (§10). Scalpers trade more, so they reach a meaningful trade count sooner; the review clock can follow trade count rather than the calendar (the `dc` template already names an event every N closed trades, CHECKED `TPL/dc-decay-and-limit-report/README.md`).

---

## 3. Numbers, charts, or both, in the daily review

- Humans: both. The chart for context and to relive the trade, numbers for grades and statistics (§2.1, PRACTITIONER).
- Systematic desks: numbers only; charts on demand for diagnosis (§2.2, PRACTITIONER).
- Agents: research 29 §6. Charts for shape, numbers through tools for every value; models misread values off unlabelled charts and do worst on candlesticks (CHECKED there).
- Options for QMX (INFERRED, not ranked): (a) unit review from numbers only, with a chart rendered for him, not for the agent; (b) market review with chart and number twins; (c) charts with levels printed on them, which models read far better (FinChart-Bench, research 29 §6).

---

## 4. Weekly market selection: what counts as evidence

| Basis | Can it be known before the week? | Evidence | Verdict (INFERRED) |
| --- | --- | --- | --- |
| Volatility level | Forecastable; volatility clusters and has long memory (gold: Cai, Cheung and Wong 2001, https://onlinelibrary.wiley.com/doi/10.1002/1096-9934(200103)21:3%3C257::AID-FUT4%3E3.0.CO;2-W, CHECKED abstract) | Strong | Honest |
| Spread, fees, slippage per broker and hour | Measured, stable by hour (precious metals spread lowest in European hours: Batten et al. 2017, https://centaur.reading.ac.uk/79175/1/BattenLuceyMcGroartyPeatUrquhart2017.pdf, CHECKED) | Strong | Honest, needs the market journal (R12) |
| Scheduled events | Known in advance (calendar) | Strong | Honest |
| Trend versus reversion state | Partly; a state seen over the last weeks may persist, but takes hours to show at 1m (R15, CHECKED in STATE) | Medium | Honest if labelled with its window and scored later |
| Direction | Not forecastable from price alone (any trader knows) | Weak | Commentary, not evidence |
| The unit's own recent P&L per market | Noisy; picks the luckiest | Weak | Look-ahead unless shrunk toward the unit's average and counted as a try |

INFERRED option set for a weekly selection template: compute the forecastable columns by script, let an agent write the week's narrative with receipts (the old "Week-Map", R19 §8), and score the week's calls on Friday in the forecast ledger (research 29 §4). The unit's own record enters only through the judging rules, never as a raw ranking.

---

## 5. Session habits: honest almanac or look-ahead?

**What is real (CHECKED).**
- Precious metals show strong time-of-day patterns in returns, volatility, volume and spread, tied to market opens and closes, over 2000-2015 (Batten et al. 2017).
- Gold futures volume rises about 48% and volatility about 33% in the minutes after the London afternoon fix starts (Caminschi and Heaney, https://scispace.com/pdf/fixing-a-leaky-fixing-short-term-market-reactions-to-the-3vun2pp3ja.pdf).
- Gold and platinum volatility rises into the New York open in a U-shape over global hours (Iwatsubo, Watkins and Xu 2017, https://rieti.go.jp/jp/publications/dp/17e120.pdf, CHECKED highlight).
- US employment, GDP, CPI and personal income are the announcements that move gold most (Cai et al. 2001).

**Where it turns into look-ahead (INFERRED).**
- Picking a unit's hours or weekdays from the same results it is judged on. Example of the trap: a guide finds Thursday and Friday losing over three months of one robot's stats, removes them, and says the result "is guaranteed to improve" (https://tlap.io/en/how-to-limit-forex-advisor-trading-hours, PRACTITIONER).
- His ORB example (T1:1903) is honest if the session is chosen in one period and judged in a later one, and if each tried window counts as a try (R05, R08).

**Options for an honest session almanac (not ranked).**
- (a) An almanac computed from market data only (volume, volatility, spread by hour per instrument and broker), dated and versioned, never from unit P&L. This is the market journal's job (R12).
- (b) A unit's session window as a declared setting, tuned only inside QMB with tries counted (the edit type decides "new unit", STATE).
- (c) A forward check: the window chosen last month is scored on this month, by script.

---

## 6. Fundamentals: through what, with what proof

- **Through scheduled surprises.** Announcement surprises cause jumps in FX; the mean adjusts at once, volatility gradually; bad news hits harder (Andersen et al. 2003, https://www.aeaweb.org/articles?id=10.1257%2F000282803321455151, CHECKED abstract).
- **What QMX already does.** The calendar template sets blackouts of 30 minutes either side of high-impact releases and calls a miss of 1.5 typical misses a surprise, at most 10 a day (CHECKED `TPL/t3-news-calendar-watch/README.md`). The free feed gives forecasts and previous values only, so live it finds no surprise until a source with actual values is added (same file). The overnight desk reads Fed, ECB and Bank of Japan feeds and cuts any claim resting on one item unless it is a scheduled tier-one release (CHECKED `TPL/t4-research-desk-overnight/README.md`). Positioning data, technical structure and cross-asset reads are left out (same file).
- **Proof options (INFERRED).** (a) An event study per release type and instrument, recomputed from the market journal: the move and the spread in the minutes after. (b) Fundamental calls written into the forecast ledger before the release and scored after. (c) Release times from `data.calendar` only, never from model memory (models muddle release dates, research 29 F17).
- **Crypto and perps** add funding and open interest as "fundamentals" (R02 and R16 rows in STATE, CHECKED). Out of the shipped templates today.

---

## 7. The catalogue mapped onto shipped templates

Shipped status from R18 §1.5 (CHECKED there) and the READMEs read here.

| Analysis | Style and default cadence | Inputs | Output | Shipped template | Status | Waits on |
| --- | --- | --- | --- | --- | --- | --- |
| Morning brief | all; before his first session | calendar, desk lines, inbox | one card | `morning-market-brief` (db) | BUILT, without node facts or MIS grid | trading node, MIS state |
| Pre-session read per market | scalper; before each session | spreads, volatility vs usual for the hour, MIS state, calendar | "in play" list per unit | none (db's T2 card left out) | MISSING | MIS state readable, unit conditions |
| News and calendar | all; daily, and per release | calendar, actuals | strip with blackouts and surprises | `news-and-macro-calendar-watch` (t3) | BUILT, no live actuals | a feed with actuals |
| Overnight research | intraday, swing; Sun-Thu 03:00 London | central-bank feeds, releases | ranked brief | `research-desk-overnight` (t4) | BUILT | more feeds (COT, sentiment, cross-asset) |
| During-session watch | scalper | guard state, spreads, connection | alerts only | `trading-guards-alive` (gw), `connections-health` | gw draft; connections BUILT | trading node |
| End-of-session or day wrap | scalper per session, intraday daily | journal in R, costs, missed and skipped signals | day card | db's T10 wrap left out | MISSING | node journal |
| Daily unit report card (rules followed? traded, skipped, missed) | all; per session or day | journal, replay of the same day | grades per unit | none (workflows field I1, I2) | MISSING | journal read path, qmb-door |
| Fill and cost quality | scalper, intraday; per trade, daily | fills, market journal | cost tiles | `demo-trades-fill-quality` (dm) | draft | trading node |
| Weekly unit review in R | all; Saturday | R journal with tags | at most three lessons | `trade-journal-in-risk-units` (t7) | draft | trading node |
| Decay check | all; daily or every N trades | journals, exam baseline | OK, watch, alarm cards | `decay-and-limit-report` (dc) | draft | trading node |
| Weekly market selection and narrative | scalper, intraday; Sunday | volatility, costs, calendar, state | week map, scored Friday | none (workflows field H2) | MISSING | data door default open (PR 207), forecast ledger kind |
| Session-close forecasts | scalper; each session close | bars, state | dated calls, scored next close | none (workflows field H1) | MISSING | same |
| Recalibration or walk-forward rerun | monthly to quarterly | QMB | new settings proposal | `iterate-against-qmb-with-overfit-guards` (d3), `overnight-lab-loop` (l4) | drafts | qmb-door |
| Incident post-mortem | event | logs, journal | cause card | `incident-post-mortem` (rk8) | draft | trading node |
| Weekly review | weekly | the engine's own runs | prompt and rule edits | `weekly-review` (rv) | BUILT | none; reviews workflows, not trading |
| Daily digest of what landed | daily 07:00 London | Library log | digest | `morning-digest` | BUILT | none |

Pattern (INFERRED): what desks do before and around the market is half-built; what they do with their own trades is all waiting on the node, the journal read path and the backtest door. Desk cadence is mostly cron triggers already supported (cron with time zones and DST, R18 §1.2, CHECKED there); per-session clocks for 24-hour markets and "every N trades" events are the missing trigger sources.

---

## 8. His day-to-day experience on today's platforms

Each row runs idea → build → backtest → optimise → live → review. "Stalls" cites user forums and the vendors' own docs.

| Platform | How a retail algo trader uses it | Where it stalls (evidence) |
| --- | --- | --- |
| **MT5** (Strategy Tester, Wizard) | Code in MQL5 or assemble signal, trailing and money modules in the Wizard (R04, CHECKED there); test in the Strategy Tester; optimise (genetic); run on a server; watch the Experts and Journal tabs, phone alerts, Myfxbook | Tick modes give opposite results on one EA ("Every tick" profit, real ticks loss: https://www.mql5.com/en/forum/462504). Optimised settings that pass a forward split fail on new data (https://www.mql5.com/en/forum/326752). Commission often not modelled unless in the symbol spec; spread not widened at news (https://www.mql5.com/en/forum/508077). Optimisation and single runs disagreed after one build (https://www.mql5.com/en/forum/376067/page3). Results differ by broker data (https://www.mql5.com/en/forum/439236). |
| **cTrader Automate** | Write cBots in C#; backtest on server tick data; optimise; run on the desktop | Tick optimisation too slow to finish; minute-bar winners lose on ticks (https://community.ctrader.com/forum/ctrader-algo/37908/). Optimisation and backtest results disagree, reported 2019 and still open years later (https://community.ctrader.com/forum/cbot-support/15410/). Backtest prices differ from live and from other sources (https://community.ctrader.com/forum/ctrader-algo/41408/, /12122/). Demo-server history not accurate, per the vendor (https://community.ctrader.com/forum/ctrader-support/43888/). |
| **TradingView** | Pine scripts and the Strategy Tester; alerts by webhook to a third-party executor | Fills at the next bar from OHLC only; settings that fill sooner cause repainting or look-ahead; results change as the history start moves; bars capped by plan (5,000 to 40,000); strategies cannot place orders (CHECKED https://www.tradingview.com/pine-script-docs/faq/strategies/, https://www.tradingview.com/pine-script-docs/writing/limitations/). Webhooks are best effort with a 3-second timeout (https://pickmytrade.trade/tradingview-webhooks-faq/, PRACTITIONER citing TradingView's help pages). |
| **QuantConnect** (LEAN) | Python or C# in the cloud; research notebooks; live through a broker | 20-30 s to start each backtest and slow Python iteration (https://www.quantconnect.com/forum/discussion/5206/); a 14-month backtest took about half an hour (https://exchange.ml4trading.io/t/lean-quant-connect-vs-zipline-reloaded/200, PRACTITIONER). Data updates moved old results overnight (https://www.quantconnect.com/forum/discussion/7797/). Strength worth copying: **live reconciliation**, a backtest of the live period drawn over the live curve with an error score (CHECKED https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/reconciliation). His word: "heavy" (T1:828). |
| **StrategyQuant** | Generate thousands of strategies, filter through robustness tests, export to MT4/MT5 or others | The robustness funnel does not reliably pick survivors; out-of-sample stops being out of sample when extra markets join the search; no correction for tries (R03 short answer and §4, CHECKED there). |
| **NinjaTrader** | NinjaScript strategies; Strategy Analyzer; Market Replay to rehearse; futures | Backtest fills come from OHLC unless a 1-tick series is added; Tick Replay does not make fills accurate and cannot be combined with high fill resolution; backtest, simulation and live use three different fill models (CHECKED https://static.ninjatrader.com/support/helpGuides/nt8/discrepancies_real-time_vs_bac.htm; https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1268101-strategy-analyzer-backtesting-order-fill-resolution-vs-tick-replay). |

**The six common stalls** (INFERRED synthesis of the rows above):
1. **Backtest-to-live gap in fills and costs.** Every vendor's own docs admit it.
2. **Optimisation without a count of tries.** Overfit is the forums' most common complaint.
3. **Data differs by source and broker,** and a demo feed is not the live feed.
4. **Review is manual and not linked to the test.** Exports, spreadsheets, Myfxbook. QuantConnect's reconciliation is the exception.
5. **Markets and hours are picked by hand** from small samples (the tlap example in §5).
6. **Monitoring asks "is it running?",** not "is its edge still there?". Win rate is eyeballed against the backtest.

### 8.1 Which steps units, QMX workflows, the MIS and self-configuring would change

| Stall | What changes in QMX (INFERRED, each a seed or a shipped piece) | What does not change |
| --- | --- | --- |
| 1. Fill and cost gap | The market journal measures real spread, fees and slippage per broker and hour, and QMB uses it (R12; GAP-0048 empty today) | Slippage and spreads still exist; a scalper edge smaller than costs is still no edge |
| 2. Tries | QMB counts every run at its door, hand runs too (R43) | A small sample is still small |
| 3. Data by source | One recorded feed per broker, and every read stamped demo or live (PR 215, R18 §1.4) | Brokers still differ; QMX measures it, does not remove it |
| 4. Review not linked | Every live trade links to the unit's exam baseline and the market readings at entry; a replay-match step (workflows field I2) does what QuantConnect's reconciliation does, per trade | He still reads the card and decides |
| 5. Hand-picked markets and hours | The MIS points units at markets from forecastable facts (volatility, costs, state, calendar); the almanac comes from market data, not unit P&L (§5) | Promotion stays his click (STATE Q3) |
| 6. "Is it running?" only | Decay checks per unit (CUSUM, band, cost drift) as scripts, agents only explain flags (`dc` draft) | Guards still stop units on their own; that is the only automatic transition (standing order 7) |

**Self-configuring** changes the numbers inside a unit's declared ranges from its own journal (R20: shipped platforms do this much; nobody changes the policy itself without a human). On MT5 the operator reoptimises by hand on a calendar; in QMX the unit's settings move by rule, logged, and anything bigger becomes a proposal card (INFERRED from R20 and STATE).

### 8.2 "Multiple experiences": a day in his life, two ways (INFERRED narrative, for him to react to)

- **Today, with a simple bot on MT5 or cTrader.** Morning: check the server is up and the bot is on; read overnight trades; check the calendar and maybe switch the bot off for a release. Day: glance at the phone. Weekend: export trades, compare with the backtest by eye, maybe reoptimise, maybe drop a weekday that lost. One bot, one market, his judgement everywhere, nothing written down unless he writes it.
- **With QMX units.** Morning: one card. Overnight results in R per unit, which markets are in play this session and why (with receipts), proposals waiting for his click, nothing he has to check by hand because guards and decay checks ran alone. Day: nothing unless an alarm. Session close: forecasts are written and scored by the market, not by him. Weekend: lessons per unit that already passed a statistics check, the week's market map scored against what happened, a family tree showing where winners came from. His time goes to approving or rejecting proposals, not to checking.
- **The advantage, honestly stated.** Breadth (many units across many markets, each pointed where its conditions hold), memory (every trade, skip and miss recorded and linked back to its test), and discipline (tries counted, costs measured, changes logged). The edge itself still has to come from the unit's logic.

---

## 9. Questions this leaves (for the funnel; marked where only he can answer)

1. Should review clocks follow the calendar, trade count, or both? Scalpers reach a meaningful count daily, swing units monthly.
2. For 24-hour markets (crypto, perps), what is a "session" for a pre-session read and a session-close forecast? A fixed UTC clock, volume regimes, or the trader's own hours?
3. Is weekly market selection a template (Sunday, scripts plus a narrative) or a standing MIS output that a template only summarises?
4. Which feed with actual release values should the calendar template use (a data and licence question, research 33)?
5. For him: what does he want on the one morning card, and at what time? (His preference; no experiment settles it.)
6. For him: does he want to approve hour and weekday restrictions on a unit as settings he clicks, or let QMB-tested windows apply inside the unit's ranges?

---

## 10. Numbers named (starting defaults, to edit)

| Number | Default | Why this start (INFERRED) |
| --- | --- | --- |
| Pre-session read lead time | 30 minutes before each session open | The archived T2 card and common desk practice |
| Scalper review clock | after each session, plus daily | §2.4 |
| Intraday review clock | end of day (17:05 New York for FX) | The archived T10 card's FX day roll |
| Weekly unit review | Saturday 09:00 | `t7` README, CHECKED |
| Trades before a slice is reported | 20, with a 90% bootstrap interval | `t7` README, CHECKED |
| Trades before a parameter change is considered | 100 | PRACTITIONER (fxtool.co) |
| Weekly market selection run | Sunday evening before Asia opens; scored Friday close | §4 |
| News blackout | 30 minutes either side of high-impact releases | `t3` README, CHECKED |
| Surprise threshold | 1.5 typical misses, at most 10 a day | `t3` README, CHECKED |
| Almanac window | rolling 60 trading days, dated and versioned | INFERRED; long enough for hour-of-day averages |

---

## Not verified

- Practitioner pages were read from search highlights, not in full; some (fxtool.co, botfxpro.io, pro-scalper.com, pickmytrade.trade) are vendor blogs and are used only for routine, not for performance claims.
- The archived trader card catalogue (`tracker/qma-v2/research/methodology/16-templates-trader-risk.md` in commit `93051cde`) was read only for its summary table.
- MT5 Wizard and StrategyQuant were not re-researched; their facts come from R04 and R03.
- cTrader cloud hosting for cBots and NinjaTrader's current licensing were not checked.
- Iwatsubo et al. and Cai et al. were read from abstracts and highlights only.
