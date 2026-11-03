# X4: the scenario catalogue

Expansion layer: scenarios. File id `X4-scenarios`. Written 2026-11-03 by a Fable expansion agent. Read-only everywhere except this file and `ledger/additions/X4-scenarios.yaml`.

His ask (M12, `seeds/operator-words-2026-11-03.md:79`): "we also need to generate scenarios that can happen more than that ... scenarios of losing together, all together, scenarios of ... the isolation scenarios, scenarios of correlation, scenarios of new[s], scenarios of switching." And (M10, `:13`): worst, realistic and best cases "all factors considered", because "most agents don't consider all factors". His objection to the lead's "losing together" sim stands: it had no brakes, no exposure and no drawdown rules in it (SEEDS C32, replies row 23).

This catalogue is the seed for the numbers-lens simulations and for every design test. It does not pick a brake set. It says what each scenario demands of every level, so the funnel and the architecture can check a proposed template against all of them.

## How to read this

- **Levels** (his, B1 and the brief): **trade** (one position and its stop or exit), **unit** (one unit's entries, size and own brakes), **book** (the cluster of one style), **methodology** (every unit that shares one logic, across books; his fourth level, which no shipped layer owns today), **BMS** (the portfolio: splits capital, isolates, opens and closes slots), **account** (the broker account: equity, margin, floor), **node** (the machine: feed, clock, stand-downs, orders), **operator** (him). "—" means that level has nothing to do.
- **Engages** lists the brakes (B), accelerators (A) and ledger variables that the scenario touches. Ledger ids are the ones in `ledger/additions/X4-scenarios.yaml`. Where ledger v0 lands with an id for the same thing, the funnel should map mine onto it; I could not read v0, it did not exist when I wrote this.
- **Likely / bad** is a first guess, **[judgment]** throughout, to be replaced by measured rates in the simulations. Likelihood per live month: **L5** most days, **L4** most weeks, **L3** most months, **L2** a few times a year, **L1** rare. Severity if no brake acts: **S1** nuisance (under one trade), **S2** a bad day (about a day budget), **S3** eats much of the cushion, **S4** reaches the floor, **S5** beyond the floor (margin call, stuck positions, debt).
- **Sim proves** names the pass test a simulation must run for this scenario. The harness idea is X4-scenarios-80.
- Maturity tags per the brief: **solid**, **plausible**, **wild**.
- Facts cited by file: G3, G6, G7, G8, G9, G10, G11 in `grounding/`; R2, R3 in `research/`; SEEDS ids (A1 to E30, D1 to D51) in `seeds/SEEDS.md`; sims in `grounding/sims/`.

## The families

| Family | Scenarios | What they test |
|---|---|---|
| A. Losing together | 01-07 | shared drivers, correlation, the event window, N_eff |
| B. One class or region goes bad; isolation | 08-14 | evidence, scope, time-to-live, resume |
| C. News and the calendar | 15-21 | sectoring by instrument and region, unknown events, windows |
| D. Sessions, clocks and the 24/7 split | 22-30 | switching, overlaps, rollover, weekend, holidays, DST, day boundary |
| E. Market structure shocks | 31-37 | flash crash, gaps, halts, auctions, limit moves, spreads everywhere |
| F. Costs and execution | 38-44 | slippage, cost drift, demo against live, min lot, conversion, partial fills |
| G. Infrastructure | 45-52 | broker, feed, clock, VPS, network, disk, restart loops, split brain |
| H. Units, software and agents | 53-59 | misbehaving unit, bug, runaway, upgrade mid-day, agent wrong, blank config |
| I. Edge and regime | 60-66 | decay, regime change, losing streak with a real edge, winning streak, same signal |
| J. Account and capital | 67-73 | margin, leverage, floor, cushion, restart, sweep, deposits |
| K. Operator | 74-77 | away, error, panic, unreachable with open trades |
| L. Instrument-specific | 78-79 (plus items inside E and J) | rolls, funding, dividends, expiry |
| M. Two at once | 80-89 | combinations |
| Design ideas drawn from the catalogue | 90-99 | the harness, the event window, N_eff, scenario-as-data, and more |

---

# Part 1. Ideas: the scenarios

## Family A. Losing together

### X4-scenarios-01. Many units lose on one shared move (the "losing together" case, with brakes on)

- **What happens.** A single driver moves several markets at once: a USD move takes EURUSD, GBPUSD, gold and the US indices in one direction for an hour. Five units in three books are short the same thing without knowing it. Each takes a full stop. The lead's sim of this had no brakes (`sims/units_split.py`, the ρ = 0.5 row: 32 % floor touches); this scenario is the same case with every level acting.
- **Why a trader wants it.** This is the normal way a small book dies: not a black swan, a Tuesday. His words: "many markets losing together isn't a black swan. Good correction" (C27). R2 §4.2: the correlation that bites is shared exposure, not noise.
- **Levels.** trade: each stop fires on its own; exits are never blocked. unit: each unit counts its own loss; a unit-level count brake must not fire on one correlated loss as if it were a streak (it is one event). book: the book's loss budget counts the five losses **once as one event** inside an event window (idea 91), so the book brake reads "one big hit", not "five strikes". methodology: if all five share one logic (say mean reversion), the methodology view flags "logic X lost everywhere in one hour" as a regime tell, not a unit fault. BMS: computes same-bet exposure before the move (idea 92) so the five were never allowed to add to more than one unit's worth of USD risk; after the move, raises a caution (no new entries on the same driver for a cooling time). account: equity, marked, is read fresh; open risk sum drops as stops fire. node: nothing special; orders flow. operator: a ticket, not a page, unless the book budget is gone.
- **Engages.** B: book daily loss budget, event window, same-bet cap, BMS driver caution. A: house money must be **off** for the rest of the window (one shared winning move is not five independent wins either). Ledger: `scenario_event_window`, `same_bet_exposure_cap`, `shared_driver_tags`, `effective_units`, `book_day_loss_budget`, `house_money_lockout`.
- **Correct outcome.** Total loss ≤ one event's allowance (for example the book's per-event cap, about one day budget), no unit benched for a streak it did not have, no new same-driver entries for the cooling time, the book trades again next day. Growth over 60 days stays close to the independent case because the cap on shared exposure, not a smaller size everywhere, did the work.
- **Sim proves.** With the shared-factor model (ρ by driver) and the brakes on: floor-touch rate at ρ = 0.5 falls from 32 % toward the ρ = 0 rate, and growth stays within X % of the ρ = 0 growth. It also measures how many "streak" fires the event window prevented.
- **Likely / bad.** L4 / S3 without brakes; S2 with them.
- **Sources.** C27, C29, C32, B15; `sims/units_split.py`; R2 §4.2, §4.3; R3 §3.3 (hours clause); G9 §6 (no cross-unit exposure exists).
- **Maturity.** solid.

### X4-scenarios-02. Correlation spike: independent yesterday, one bet today

- **What happens.** The measured correlation between the units' markets jumps (risk-off, a central-bank surprise, a liquidity squeeze). Positions sized on yesterday's correlation are now one bet. R2 §3.3: correlation rises in bear moves and extreme losses are far more correlated than a normal model says.
- **Why.** The same-bet check is only as good as its correlation input; a spike is when it is wrong.
- **Levels.** trade: —. unit: —. book: the book's N_eff falls; the book's per-unit share should fall with it (R2 §4.3: share = 1/√(N(1+(N−1)ρ))). methodology: —. BMS: reads the fast tells (spread and volatility against the usual for this hour, across the class) rather than waiting for a correlation window (R2 §3.3 says those are the fast ones); on a spike, trims new entry size across the correlated group and raises the same-bet count. account: —. node: —. operator: ticket.
- **Engages.** B: same-bet cap with a **stress correlation** input (use the higher of measured and stressed ρ); BMS trim. A: none. Ledger: `correlation_stress_rho`, `effective_units`, `co_move_score`, `entry_size_trim_on_comove`.
- **Correct outcome.** New entries during the spike are sized as if ρ were high; open positions keep their stops; no brake fires on healthy units; the trim lifts when the tells clear.
- **Sim proves.** Two-regime correlation (ρ 0.1 normal, 0.7 stressed, switching daily with persistence): the stressed-ρ sizing keeps floor touches under the bound while the measured-ρ sizing does not.
- **Likely / bad.** L3 / S3.
- **Sources.** R2 §3.3, §4.2; C18 (correlation ledger "internally external").
- **Maturity.** solid.

### X4-scenarios-03. Same signal, many units (crowding inside QMX)

- **What happens.** Ten units built from the same logic family on correlated markets all get the same entry in the same minute (a breakout on the London open on five EUR pairs). The frequency thesis counts ten bets; there is one.
- **Why.** His "twice the edge, twice the size" worry and his frequency thesis both assume independence (STATE item 10; the brief's facts).
- **Levels.** trade: —. unit: a unit cannot see the others; it must not try. book: counts same-bet entries once toward the day budget. methodology: the methodology level is exactly for this: "units of logic X on driver Y" is one bet; show N_eff per methodology. BMS: before funding, the cross-unit hook refuses or trims the eleventh same-bet entry (today it passes every order, G9 §6). account: —. node: —. operator: sees "effective units: 2.3 of 10" on the BMS screen (idea 93).
- **Engages.** B: same-bet cap, methodology N_eff. Ledger: `same_bet_exposure_cap`, `effective_units`, `methodology_tag`.
- **Correct outcome.** Total risk on the driver stays at the cap; the frequency benefit is counted honestly; no false "ten independent bets" growth claim.
- **Sim proves.** The "10 units, $10 each" table rerun with ρ by driver and the cap on: growth and floor touches land between the independent and the half-correlated rows, and the N_eff reported matches the realised one.
- **Likely / bad.** L5 (it happens by design every day) / S3.
- **Sources.** C29, C13, D11, R2 §4.2-4.3, `sims/frequency_flaw_and_brakes.py`.
- **Maturity.** solid.

### X4-scenarios-04. Losing together in the edge, not in the noise (the logic fades everywhere)

- **What happens.** Nothing dramatic on any day. Over three weeks every mean-reversion unit's expectancy slides toward zero at once, because the regime stopped mean-reverting. Per-unit decay checks each see "within noise"; the methodology sees a cliff.
- **Why.** R2 §4.2: "all edges of one logic fading together in a regime change ... is a correlation in the edge itself, and no bet count removes it."
- **Levels.** trade/unit: —. book: —. methodology: pools the R of every unit sharing the logic; a CUSUM on the pooled stream sees the drop in a fraction of the trades one unit needs (R2 §2.2: about 240 trades for one unit at +0.1R → 0; a pool of ten gets there in days). BMS: steps the methodology's share down one level (yellow), not off. account: —. node: —. operator: a ticket with the pooled chart.
- **Engages.** B: methodology drift state, size level step. A: none. Ledger: `methodology_pooled_cusum`, `drift_state`, `size_level_now`.
- **Correct outcome.** The pooled check flags in days, the step-down costs little, no unit is killed for a bad week, and the step is undone on new evidence.
- **Sim proves.** Ten units whose shared edge decays linearly to zero over 400 trades each: pooled detection time against per-unit detection time; the cost (in R) of the delay under each.
- **Likely / bad.** L2 / S3.
- **Sources.** R2 §2.2, §4.2; G10 §5; A25 ("size down, not quickly").
- **Maturity.** solid.

### X4-scenarios-05. Winning together (the mirror image): one move pays everyone, accelerators fire

- **What happens.** The same USD move goes the book's way. Five units are up on the day in one hour. House money triggers on each. The next five entries are 1.5× size, all still on USD.
- **Why.** An accelerator that reads "the day is paid for" five times from one event multiplies the next correlated loss. He keeps house money (A21); it needs this guard.
- **Levels.** trade: —. unit: house money may be earned only from the unit's own realised P&L **after the event window closes**. book: house money is capped at book level: the extra size across units cannot exceed what one event's profit covers. methodology: —. BMS: no accelerator while a driver caution or isolation is on. account: —. node: —. operator: —.
- **Engages.** A: house money (scoped, windowed, capped). B: accelerator lockout. Ledger: `house_money_threshold`, `house_money_scope`, `house_money_lockout`, `scenario_event_window`.
- **Correct outcome.** Accelerators add size only on independent, realised, cushion-covered profit; a correlated reversal after a correlated win costs no more than it would without house money.
- **Sim proves.** Correlated win then correlated loss within two hours: equity path with naive house money against windowed house money.
- **Likely / bad.** L4 / S2-S3.
- **Sources.** A21, C19, G3 §4.2 (house money details and its cap rule), G6 (house money absent from Book sources).
- **Maturity.** solid.

### X4-scenarios-06. Three books, one account: the losses net but the brakes don't

- **What happens.** The scalper book is up $40, the intraday book is down $60, the account is down $20. Each book brakes on its own budget: the intraday book stops, the scalper book keeps sizing off a $500 start it believes is untouched (G9 §6: each unit sizes from the account's equity at its start plus its own results).
- **Why.** Book budgets must be allocated from the account, and each unit's equity view must be the one the account has. Pod shops run this as net limits per pod plus a firm limit (R2 §2.3).
- **Levels.** trade: —. unit: sizes from its allocated share, refreshed, not from the whole account. book: its budget is a share of the BMS's; its brake reads its own realised and marked loss. methodology: —. BMS: holds the account-level daily loss budget and allocates; when the account hits the BMS budget every book stops entries even if one book is under its own. account: equity is marked and refreshed (today cTrader equity is read once at sign-in, G9 §3.3). node: —. operator: —.
- **Engages.** B: BMS daily budget, book budgets as shares, account equity refresh. Ledger: `bms_day_loss_budget`, `book_day_loss_budget`, `unit_equity_share`, `equity_refresh_s`, `equity_series` (marked or realised, named per brake).
- **Correct outcome.** No unit sizes from money another unit lost; the account-level brake trips before the sum of book budgets would; profits in one book do not silently fund losses in another unless the BMS said so.
- **Sim proves.** Three books with independent P&L on one account: with per-unit "start equity" sizing the account breaches the floor while every book brake is quiet; with shares and refresh it does not.
- **Likely / bad.** L5 / S3.
- **Sources.** G9 §6, G11 §2, B2, C6, R2 §2.3.
- **Maturity.** solid.

### X4-scenarios-07. The slow bleed with no event: death by a thousand small losses across the whole book

- **What happens.** No single bad day. Costs are a little higher than modelled on every market; each unit is at −0.02R per trade net; across 300 trades a day the book bleeds 6R a day, under every daily brake.
- **Why.** Brakes keyed on a day's loss never fire; the floor arrives in a month. R2 §2.5: "A unit whose costs doubled is broken today, whatever its P&L."
- **Levels.** trade: —. unit: input checks (cost per trade against calibrated, fill quality) alarm before P&L does. book: a weekly burn rate (loss of cushion per week) with a slow window, the SRE "ticket" class (R3 §3.5). methodology: —. BMS: cushion burn rate across the whole portfolio; steps size levels down when the slow window burns faster than the plan. account: —. node: —. operator: a weekly ticket with the burn chart.
- **Engages.** B: slow-window burn rate, cost drift alarm, size level step. Ledger: `burn_rate_slow_window`, `burn_rate_ticket_threshold`, `cost_drift_alarm`, `cushion_burn_rate`.
- **Correct outcome.** The bleed is named within a week; the cause (costs) is shown; size steps down; the floor is never approached by drift alone.
- **Sim proves.** Edge net of costs set to −0.02R with daily brakes only against with a slow-window burn brake: days to detection and cushion lost before detection.
- **Likely / bad.** L3 / S4 (it is the way a thin edge dies).
- **Sources.** R2 §2.2, §2.5, §4.2 (costs); R3 §3.5 (burn rate, two windows); A11 (costs feed sizing); G9 §5 (no cost input to the sizer).
- **Maturity.** solid.

## Family B. One class or region goes bad; isolation

### X4-scenarios-08. One class turns toxic (crypto flash, indices limit-down, FX fix chaos) while the others are fine

- **What happens.** A crypto exchange incident, or a US index limit-down day, or a sudden FX intervention: every instrument in one class shows spreads 5× usual and volatility jumps, for hours. The other classes trade normally.
- **Why.** His market isolation protocol (C27): "it can isolate crypto. And everything is off for crypto." The exchange pattern: per-product breakers pause one product while the rest trade (R2 §3.1).
- **Levels.** trade: open positions in the class keep their stops; exits allowed; the soft kill may stage exits (G10 §7.10). unit: a unit on that class gets "no new entries: class isolated" with the reason; a unit on other classes is untouched. book: —. methodology: —. BMS: raises an **isolation** at scope `class:crypto` on evidence (a co-move score: share of the class's instruments beyond their usual spread or volatility for this hour, plus any calendar event tagged to the class), with a time-to-live and a staged resume (idea 94). account: —. node: a new scope key `class:` beside `instrument:` in the stand-down table (G9 "What his ideas could hang on"). operator: a page only if positions are open and cannot be protected; else a ticket with the evidence. The MIS adjusts by publishing the isolation on the board so placement does not route new units into the class (his "how does the MIS adjust?").
- **Engages.** B: class isolation, SQS per instrument, spread-against-cost guard. A: none during isolation. Ledger: `isolation_scope`, `co_move_score`, `isolation_evidence_threshold`, `isolation_ttl`, `isolation_resume_rule`, `sqs_ratio`.
- **Correct outcome.** No new entries in the class from the moment the evidence crosses the bar; other classes keep their frequency; the isolation ends by itself when tells clear or the TTL runs out, in stages (half size first); the whole thing is journalled with the evidence.
- **Sim proves.** Historical class shocks replayed (the `rk5` list: SNB unpeg, Brexit night, COVID week, plus crypto exchange outages) with and without isolation: loss avoided, entries missed, and the false-isolation rate on calm history.
- **Likely / bad.** L3 / S3-S4.
- **Sources.** C27, C28, G9 §4.4 (no class scope exists), G10 §6, R2 §3.1, §3.3, §3.5, §6.5.
- **Maturity.** solid.

### X4-scenarios-09. Isolation fires on calm markets (the false isolation)

- **What happens.** The co-move score crosses its bar on a thin holiday afternoon because every instrument's spread is "unusual" against a baseline that did not know it was a holiday. Crypto is switched off for four hours of normal trade. Forty entries are missed.
- **Why.** Every brake has a false-fire rate; isolation's is the cost of breadth. Hospitals: 85 to 99 % of alarms need no action and clinicians then mute them (R3 §3.6). He will mute it too.
- **Levels.** BMS: isolation needs two tells to agree (spread and volatility, or spread and calendar), a minimum co-move count, and a calendar-aware baseline; every isolation records its own precision afterwards (did a loss follow?). operator: sees the isolation's precision on screen; a noisy isolation rule is a defect. Others: —.
- **Engages.** B: isolation with two-tell agreement. Ledger: `isolation_two_tell_rule`, `brake_precision`, `baseline_calendar_aware`.
- **Correct outcome.** Isolation precision above a bar (say most fires were followed by a real loss in the class within the window) and a recall that catches the historical shocks.
- **Sim proves.** On two years of calm-plus-shock history: precision and recall of each isolation rule; the rule the funnel picks must beat a bar on both.
- **Likely / bad.** L4 if naive / S1-S2 (missed trades), but S3 in a second-order sense: a muted brake is no brake.
- **Sources.** R3 §3.6, §3.7; R2 §6.5 ("scored on history for false alarms").
- **Maturity.** solid.

### X4-scenarios-10. One region goes bad (Asia session chaos while Europe sleeps)

- **What happens.** A Japanese intervention at 02:00 UTC: JPY pairs, the Nikkei CFD and gold all move. The European and US instruments are closed or quiet. Only the units awake are JPY scalpers.
- **Why.** His sectoring by region (C27): news in Tokyo is not news in New York. April had region shifting (G10 §3.1); July killed the budget rotation but kept the pair block.
- **Levels.** unit: JPY units get "no new entries, region isolated". book: —. methodology: —. BMS: scope `region:asia` or `currency:JPY` (the instrument record has `zone` and the quote currency, but no base-currency field, G9 §2); whether the freed budget moves to other regions is the July conflict (G10 §7.6) and a collision (Part 3). account: —. node: region scope key. operator: ticket.
- **Engages.** B: region or currency isolation. Ledger: `isolation_scope` (region, currency), `shared_driver_tags`, `budget_rotation_on_isolation` (open).
- **Correct outcome.** Only the affected region's instruments stop; the system does not go dark worldwide for a Tokyo event; the budget either stays parked or rotates by a rule he chose.
- **Sim proves.** Region-tagged shocks on history: loss avoided in the region, growth kept elsewhere, under "park" and "rotate".
- **Likely / bad.** L3 / S2-S3.
- **Sources.** C27, G10 §3.1, §3.2, §7.6; G9 §2.
- **Maturity.** solid.

### X4-scenarios-11. Isolation with positions open: what happens to what is already in

- **What happens.** The class isolates while three positions are open in it. The stops are at the broker. Spreads are 5× usual, so the stops will fill badly.
- **Why.** "Exits are never blocked" (C21) does not say exits are wise. April's soft kill staged exits in 25 % chunks (G10 §3.1); Gen 3 windows never close positions (G10 §7.10).
- **Levels.** trade: the broker-side hard stop stays; the working stop is not widened; a staged reduce-only exit policy may run if the isolation says "exit" rather than "no new entries". unit: decides per position with its own exit logic; a unit may hold if its logic says so. BMS: isolation carries a **mode** (no new entries, reduce, flatten) chosen by evidence strength; "flatten" is the top level only. operator: a page if "flatten" fires with positions open.
- **Engages.** B: isolation mode, protection escalation (exists, G9 §1.1). Ledger: `isolation_mode`, `staged_exit_fraction`, `staged_exit_interval_s`.
- **Correct outcome.** Open positions are closed at the cost the mode accepts; nothing is forced flat into a 5× spread when "no new entries" would do.
- **Sim proves.** Shock replay with open positions: realised loss under hold-to-stop, staged exit and instant flatten, per shock type.
- **Likely / bad.** L3 / S2-S3.
- **Sources.** C21, G10 §3.1, §7.10; G9 §1.1 (flatten does nothing today, "What is missing" 9).
- **Maturity.** plausible.

### X4-scenarios-12. The resume after isolation (the reopen is where people get hurt)

- **What happens.** The isolation's TTL runs out at 14:00. Every unit in the class re-enters at once at full size into the first minutes of a reopened, still-thin market. Exchanges know this: the reopen auction is staged for a reason (R2 §3.1).
- **Why.** A brake that releases all at once makes its own shock.
- **Levels.** unit: after a release, first entries at half size for a settling time (April's ×0.1 weights for the settling window, G10 §3.1). BMS: staged resume: half size, then full after N clean minutes with the tells still clear; a second trip inside the settling time doubles the next TTL (retry then lockout, R3 §3.1). operator: ticket.
- **Engages.** B: staged resume. A: locked out during settling. Ledger: `isolation_resume_rule`, `settling_time`, `resume_size_fraction`, `isolation_retrip_backoff`.
- **Correct outcome.** No re-entry cluster; a second shock inside the settling time is caught small.
- **Sim proves.** Shock with aftershock (second wave 30 minutes after the first): loss under instant resume against staged resume.
- **Likely / bad.** L3 / S2.
- **Sources.** R2 §3.1, R3 §3.1, G10 §3.1 (settling time), §7.6.
- **Maturity.** solid.

### X4-scenarios-13. Isolation by agent evidence over days, not by a tell in minutes

- **What happens.** No single tell. Over three weeks an agent's weekly market map shows that one class's microstructure has changed (spreads up 40 % at every hour, fills worse), and every unit on it is below its record. He wants this to be isolation evidence too (C27: "based off maybe the analysis we've come up with over 20 days").
- **Why.** Two speeds: tells in minutes, evidence in weeks (R2 §6.4).
- **Levels.** methodology/BMS: an agent lands a proposal card: "isolate class X for a week, evidence attached". He clicks; the BMS applies it with a TTL. Nothing automatic from prose. operator: the click.
- **Engages.** B: slow isolation by proposal. Ledger: `isolation_scope`, `isolation_ttl`, `agent_proposal_bounds`.
- **Correct outcome.** A slow deterioration is caught before a month of bleed; the agent cannot switch a class off by itself.
- **Sim proves.** Not a Monte Carlo case; a workflow test: the card carries the evidence fields the BMS needs and a TTL.
- **Likely / bad.** L2 / S3.
- **Sources.** C27, D41, D42, G10 §2.4, §7.13, G9 §7.2.
- **Maturity.** plausible.

### X4-scenarios-14. Everything is bad everywhere (the BMS-level breaker)

- **What happens.** A real risk-off day: all classes show the tells; several books are at their budgets within two hours.
- **Why.** His BMS-level circuit breaker: "switch off entirely" (C27). The market-wide breaker is the top level only (R2 §3.1).
- **Levels.** BMS: when K of N classes are isolated, or the BMS budget burn rate crosses the page threshold, the BMS stops all new entries for the day (the kill switch at `all`, YELLOW effect: entries only) and does **not** flatten unless the floor buffer is threatened. account: the floor buffer check reads marked equity. operator: page.
- **Engages.** B: BMS breaker, kill switch `all` with the YELLOW effect, floor buffer. Ledger: `bms_breaker_rule`, `burn_rate_page_threshold`, `buffer_before_floor`.
- **Correct outcome.** A system-wide stop happens once a month at most on history, never on a normal day, and leaves the cushion mostly intact.
- **Sim proves.** On history: the number of days per year the BMS breaker fires, and the loss it saved on the ones it should have.
- **Likely / bad.** L2 / S4.
- **Sources.** C27, C10, G9 §1.1 (kill switch effects), R2 §3.1.
- **Maturity.** solid.

## Family C. News and the calendar

### X4-scenarios-15. A scheduled high-impact release with units in

- **What happens.** US CPI at 13:30 UTC. Four units hold USD exposure; two scalpers are about to enter. The minute after the print, spreads are 10× and the price gaps 40 pips.
- **Why.** He says the kill switch handled news in both systems (C28). Today news is parked on the unit path (G9 §2). The calendar ingest exists, fails closed, and the t3 strip blocks ±30 minutes, but only informs.
- **Levels.** trade: stops stay; nothing widens them. unit: "no new entries, news window for USD" from T−X to T+Y, with the reason; its own exit logic may flatten before the print if the style says so (an ORB that never holds through CPI). book: —. BMS: the window scope comes from the event's currency mapped to every instrument that depends on it (idea 95 sectoring), fail-safe up: unknown mapping means affected. node: the window is a local guard on the order path. operator: nothing; it is routine.
- **Engages.** B: news window (pre, post), fail-safe. A: house money off inside the window. Ledger: `news_window_pre_min`, `news_window_post_min`, `news_impact_map`, `news_fail_safe_affected`, `house_money_lockout`.
- **Correct outcome.** No new entries in the window; positions already open are the unit's own call; the window is sized to the release's measured impact, not a colour.
- **Sim proves.** Replay of release days with the window on and off: losses avoided, entries missed, and the best pre and post widths per release class by measured post-release move and spread (R2 §3.4).
- **Likely / bad.** L5 (several releases a week) / S2-S3 per event.
- **Sources.** C28, D9, G9 §2, G10 §3, R2 §3.4.
- **Maturity.** solid.

### X4-scenarios-16. The release the calendar did not have, or had wrong

- **What happens.** An unscheduled statement, a wrong time (DST shift in the provider), a holiday moving a release, or the free calendar simply missing it (G9 §2: the free source has no actuals). Units trade straight through.
- **Why.** Fail-safe up is the only honest rule when the calendar is a free feed (G10 §7.11).
- **Levels.** unit: the SQS and spread guard are the backstop: a spread 5× usual blocks the entry whatever the calendar says. BMS: a surprise detector on the tells (volatility jump within 12 one-minute bars, R2 §3.3) raises a short caution on the affected currency's instruments. node: calendar staleness itself is a stand-down for new entries on calendar-dependent instruments (the ingest already fails closed when stale). operator: ticket "calendar missed X".
- **Engages.** B: SQS, spread guard, surprise caution, calendar-stale stand-down. Ledger: `sqs_ratio`, `spread_cost_guard`, `surprise_caution_min`, `calendar_stale_after_h`.
- **Correct outcome.** The tells catch what the calendar missed; losses are one spread-guarded entry at most.
- **Sim proves.** Remove 20 % of events from the calendar at random in replay; measure the loss with tells-only protection against calendar-only.
- **Likely / bad.** L4 / S2.
- **Sources.** G9 §2, G10 §3.4, §7.11, R2 §3.3.
- **Maturity.** solid.

### X4-scenarios-17. News by region hits instruments the currency map does not cover

- **What happens.** A US release moves gold, oil, the Nikkei CFD and bitcoin. Every generation scoped news by currency only (G10 §3.5). Gold is tagged USD at best; the index and crypto are not.
- **Why.** His sectoring ask: "at an instrument level, at a regional level" (C27). Each instrument needs its own list of drivers.
- **Levels.** BMS: each instrument record carries `shared_driver_tags` (currencies, home exchange, region, class, plus named events it reacts to); the news window resolves through the tags, not the symbol. The tags are seeded by class defaults and refined by the measured post-release move per instrument. operator: can edit the tags.
- **Engages.** Ledger: `shared_driver_tags`, `news_impact_map`, `measured_event_impact`.
- **Correct outcome.** A US release blocks gold and the US index entries; a Japanese release blocks the Nikkei CFD and JPY pairs; crypto reacts to its own event classes (G10 §3.5 notes they need their own vocabulary).
- **Sim proves.** Event-study replay per release and instrument: the move and spread in the minutes after, which both sets the tag and the window width.
- **Likely / bad.** L4 / S2.
- **Sources.** C27, G9 §2, G10 §3.5, R2 §3.4.
- **Maturity.** solid.

### X4-scenarios-18. Medium-impact news every hour: the window swallows the day

- **What happens.** On a busy data day, ±30 minutes around every medium release leaves a scalper 90 minutes of trading. The frequency thesis dies by calendar.
- **Why.** Windows are a brake with a cost; width must follow measured impact, not colour.
- **Levels.** unit: its template states the impact level it blocks on (a 5-minute scalper may block only high; an ORB blocks high and medium around its open). BMS: windows by measured impact class per instrument; the "missed entries" count is a reported cost. operator: sees "hours blocked today".
- **Engages.** Ledger: `news_block_impact_min` (per unit type), `news_window_pre_min`, `entries_blocked_by_window`.
- **Correct outcome.** Blocked hours per day under a bar on a normal week, with the high-impact protection intact.
- **Sim proves.** Hours blocked and R lost to blocked entries, per width policy, against R saved.
- **Likely / bad.** L4 / S1 (missed trades), S2 in growth terms.
- **Sources.** R2 §3.4, G10 §3.4 (±30 minutes in t3).
- **Maturity.** solid.

### X4-scenarios-19. The post-event tail: spreads stay wide for days (demand surge)

- **What happens.** After a shock, costs stay high for a week (liquidity providers widen). The window closed; the units trade into 2× costs. Reinsurers call the parallel "demand surge" after a catastrophe.
- **Why.** The cost state, not the calendar, decides whether a scalper's edge exists (R2 §4.2: cost is the master state for scalpers).
- **Levels.** unit: the spread-against-cost guard (planned, L0:383, not built) refuses entries whose cost exceeds the unit's cost target in R. BMS: the class's `cost_state` word (normal, elevated, toxic) feeds placement; elevated means half size for scalpers. operator: ticket.
- **Engages.** B: spread guard, cost state. Ledger: `spread_cost_guard`, `cost_state`, `cost_target_r` (per unit).
- **Correct outcome.** Scalpers trade less, not worse, while costs are elevated; the ORB keeps trading if its cost in R is still small.
- **Sim proves.** Post-shock weeks replayed with the measured spread path: R with and without the guard.
- **Likely / bad.** L3 / S2-S3.
- **Sources.** R2 §2.5, §4.2; G9 §1.1 (no spread guard built); R3 §3.3.
- **Maturity.** solid.

### X4-scenarios-20. A unit's own exit logic wants out before the print; the window says "no entries", not "no exits"

- **What happens.** An ORB unit that never holds through a US release signals `close_full` at T−10. A naive window implementation blocks "orders" and so blocks the exit.
- **Why.** "Exits are never blocked" (C21, confirmed in G9 §1.1: exits skip the stand-downs). This scenario is a test that the rule holds in every window and isolation implementation.
- **Levels.** node: every refusal path must let reduce-only orders through. unit: —. operator: —.
- **Engages.** Ledger: `exits_never_blocked` (an invariant row, not a number).
- **Correct outcome.** The exit fills at T−10 at normal spread.
- **Sim proves.** A contract test, not a Monte Carlo case: every brake implementation passes reduce-only orders.
- **Likely / bad.** L5 if wrong / S2 each time.
- **Sources.** C21, G9 §1.1.
- **Maturity.** solid.

### X4-scenarios-21. A news window on a correlated group, not the headline currency

- **What happens.** An ECB decision; EURUSD is blocked. EURGBP, EURJPY and the DAX CFD are not, because the mapping holds only the quote currency (G9 §2: no base-currency field).
- **Why.** The old spec mapped a currency to every pair holding it (G10 §3.1). The record today cannot.
- **Levels.** BMS: the driver tags carry both currencies of an FX pair and the home exchange of an index; the window resolves on all. operator: —.
- **Engages.** Ledger: `shared_driver_tags`.
- **Correct outcome.** Every EUR-exposed instrument is in the window.
- **Sim proves.** A mapping test over the instrument set: every FX pair resolves to two currencies; every CFD to a home exchange.
- **Likely / bad.** L5 / S2.
- **Sources.** G9 §2, G10 §3.1.
- **Maturity.** solid.

## Family D. Sessions, clocks and the 24/7 split

### X4-scenarios-22. Session switch: the ORB is out, the scalpers take over, and the hand-off hour is the worst hour

- **What happens.** 16:00 London: the ORB flattens; the scalpers start the afternoon; the hand-over hour has thin liquidity and a London fix at 16:00. His own phrase: "there is a lot that happens in between" (D7).
- **Why.** Switching is where two styles' budgets, exposures and windows meet.
- **Levels.** unit: a session-open or hand-over caution window (D9: agreed, not built; today a `session_handover_buffer` window kind exists with no width, G6 §3.12). book: the intraday book's day closes; the scalper book's afternoon budget starts. BMS: the day budget is not "reset at hand-over"; one budget per day boundary, with per-session shares if a template wants them. operator: —.
- **Engages.** B: hand-over caution window, session shares. Ledger: `session_handover_buffer_min`, `session_budget_share`, `fix_window_min`.
- **Correct outcome.** No entries in the first minutes after a hand-over or a fix; the ORB's result is in the book's day before the scalpers size.
- **Sim proves.** Hand-over hours replayed: cost and R of entries inside the buffer against outside it.
- **Likely / bad.** L5 / S1-S2.
- **Sources.** D7, D9, D10, G6 §3.12, G10 §3.5.
- **Maturity.** solid.

### X4-scenarios-23. Overlap: two units on one pair in opposite directions

- **What happens.** London-New York overlap. A mean-reversion scalper is long EURUSD; a breakout unit goes short EURUSD. On a netting account the second order closes the first (G7 §5.1: netting accounts need one unit per symbol, a placeholder, not checked, G9 §6).
- **Why.** His "how are we making sure that it's not contradicting" (D10); the lead's answer was "each is sized on its own and limited by the same-bet check", which he accepted.
- **Levels.** node: refuses a second unit on one symbol of a netting account at deploy (the placeholder made real); on a hedging account keeps one virtual position per unit. BMS: the same-bet ledger nets the two (zero net exposure, two sets of costs); shows it. unit: —. operator: —.
- **Engages.** Ledger: `netting_refusal`, `same_bet_exposure_cap` (net), `gross_vs_net_exposure`.
- **Correct outcome.** No accidental close; the book sees net exposure zero and gross cost doubled; a template may forbid opposite units on one symbol by rule.
- **Sim proves.** A contract test on account mode; a cost test on the gross-against-net case.
- **Likely / bad.** L4 / S2.
- **Sources.** D10, G7 §5.1, G9 §6.
- **Maturity.** solid.

### X4-scenarios-24. Crypto trades through the FX weekend: one class carries the whole book for 48 hours

- **What happens.** Friday 22:00 UTC to Sunday 22:00: FX, metals and indices are closed; only perps and spot crypto trade. The BMS day budget, built for ten units across five classes, is now spent by two crypto units on the thinnest weekend liquidity.
- **Why.** 24/7 against FX hours is his explicit scenario. The frequency thesis assumes breadth that is gone at the weekend.
- **Levels.** unit: crypto units' own weekend mode (smaller size or fewer entries, their template's choice). BMS: the day budget scales with the open breadth: with one class open, the budget share that class may spend is capped at its weekday share, not the whole; N_eff is 2, not 10, and the sizes know it. account: margin for the weekend positions is the only margin in use; fine. node: FX feeds are stale by design at the weekend; the stale-feed stand-down must know the calendar or it stands down the wrong things (today: 120 s stale means stand down, G9 §1.1; the calendar is on the record). operator: —.
- **Engages.** B: open-breadth budget scaling, calendar-aware stale rule. Ledger: `open_breadth_budget_scale`, `class_budget_share_cap`, `weekend_mode` (per unit type), `feed_stale_after_s` (calendar-aware).
- **Correct outcome.** Weekend losses are bounded by the crypto class's own share; the system does not read closed FX feeds as a fault; Sunday night does not open with a crypto-sized hole.
- **Sim proves.** A week with weekday breadth 10 and weekend breadth 2, crypto with weekend volatility 1.5×: floor touches under whole-budget against scaled-budget.
- **Likely / bad.** L5 (every weekend) / S3.
- **Sources.** D10, C1, G9 §1.1, §2 (calendars per market), G7 §4.1.
- **Maturity.** solid.

### X4-scenarios-25. The weekend gap: Sunday open 80 pips through the stop

- **What happens.** A weekend headline. The Sunday open gaps through every FX stop; fills are at the open, not the stop. The per-trade loss limit (A19) was a hope.
- **Why.** The stop limits the loss only when the market trades through it. The gap allowance is a sizing input.
- **Levels.** trade: the stop fills at the open; the unit journal records `gap_through_stop` (exists in the trade row, G9 §7.1). unit: templates for styles that hold over the weekend (swing, some intraday) size with a gap allowance (stop distance plus the instrument's historical weekend gap at a percentile); styles that do not (scalpers, ORB) are flat by Friday close by rule. book: the Friday-close flat rule per book. BMS: weekend-held exposure cap. account: —. node: —. operator: —.
- **Engages.** B: Friday flat rule, gap allowance, weekend exposure cap. Ledger: `weekend_flat_rule`, `gap_allowance_pct`, `weekend_exposure_cap`, `gap_through_stop` (exists).
- **Correct outcome.** Scalpers never hold over the weekend; held positions were sized so that the gap costs at most the planned R plus the allowance.
- **Sim proves.** Monte Carlo with weekend gaps drawn from the instrument's history: realised loss distribution against planned R under each rule.
- **Likely / bad.** L2 for a big gap / S3.
- **Sources.** A19, G9 §7.1, D7 ("ORB won't hold overnight").
- **Maturity.** solid.

### X4-scenarios-26. The 17:00 New York rollover: spread spike, swap charge, day boundary, all in one minute

- **What happens.** At 21:00/22:00 UTC the FX day rolls: spreads spike for minutes, swaps are charged (triple on Wednesday), and the forex calendar's day ends (G9 §2). A scalper enters at 21:59 into a 10× spread.
- **Why.** The retail scalper's oldest scar; G7 §4.3 notes the spike.
- **Levels.** unit: a rollover caution window per instrument from its calendar; swap as a cost input the template knows (A11). book: the day boundary for budgets is a declared choice per book (UTC, the venue's day, or the book's own), named in the ledger. node: the stale-feed and spread guards must not read the spike as a fault. operator: —.
- **Engages.** B: rollover window, spread guard. Ledger: `rollover_window_min`, `swap_cost_input`, `day_boundary_source` (per book), `triple_swap_day`.
- **Correct outcome.** No entries in the rollover window; swaps are in every held position's cost; the day boundary is one declared thing.
- **Sim proves.** Entries inside the window against outside: cost in R; a day-boundary test that budgets and brakes reset at one declared time.
- **Likely / bad.** L5 / S1-S2.
- **Sources.** G7 §4.3, G9 §2, A11.
- **Maturity.** solid.

### X4-scenarios-27. Holidays and half days: thin liquidity with the calendar saying "open"

- **What happens.** Boxing Day, US Thanksgiving afternoon, Golden Week: the calendar says open; the book is 20 % as deep; a mean-reversion scalper's edge, built on normal depth, is gone, and its stops get run.
- **Why.** "Open" is not "normal"; baselines need a holiday flag.
- **Levels.** unit: its template may name holiday behaviour (half size, off). BMS: a holiday flag per calendar lowers the class's cost state to "elevated"; placement avoids thin days for scalpers. node: calendar carries holidays (the exchange calendars do; forex has none, G9 §2). operator: —.
- **Engages.** Ledger: `holiday_thin_flag`, `cost_state`, `baseline_calendar_aware`.
- **Correct outcome.** Scalpers sit out or halve on thin days; the ORB may still trade an index with a real open.
- **Sim proves.** Holiday-flagged days from history: R per entry against normal days, per style.
- **Likely / bad.** L3 / S2.
- **Sources.** G9 §2, R2 §1 (hours and costs).
- **Maturity.** solid.

### X4-scenarios-28. Daylight-saving shifts: the session is an hour off for three weeks

- **What happens.** US and UK DST change on different dates; for two to three weeks the London-New York overlap is an hour shorter, the opens move, and any "sniping window" or session rule written in UTC is wrong. The calendar provider's times may be off too (scenario 16).
- **Why.** Every clock-based rule breaks twice a year.
- **Levels.** unit: session windows are written in the market's own zone (the record has `zone`), never in UTC. node: a DST self-check on each calendar; a session check against the venue's reported session (the connect-time verifier exists and has never run, G7 §4.2). operator: ticket on mismatch.
- **Engages.** Ledger: `session_windows_zone_source`, `dst_mismatch_check`.
- **Correct outcome.** Windows move with the market; no entries land in the wrong hour.
- **Sim proves.** A calendar test across the four DST dates of a year.
- **Likely / bad.** L2 (twice a year, for weeks) / S2.
- **Sources.** G9 §2, G7 §4.2.
- **Maturity.** solid.

### X4-scenarios-29. The day-boundary exploit: two strikes at 23:50, reset at 00:00

- **What happens.** A unit takes its second full stop at 23:50 UTC, is benched, and at 00:00 the counter resets (April and July both reset at the boundary, G10 §1). It trades again at 00:01 in the same bad conditions.
- **Why.** A count brake with a hard reset is a brake with a hole. The red team found this first (Part 5).
- **Levels.** unit: the brake's window is rolling (last N hours or last N trades), not the calendar day; or a bench carries a minimum rest (hours or trades) across the boundary. book: the day budget resets at the boundary, but a benched unit's rest does not. operator: —.
- **Engages.** B: rolling-window count brake, minimum bench rest. Ledger: `count_brake_window` (rolling), `bench_min_rest`.
- **Correct outcome.** A bench lasts its rest whatever the clock says.
- **Sim proves.** Losses clustered around the boundary: fires and re-entries under calendar against rolling windows.
- **Likely / bad.** L3 / S2.
- **Sources.** G10 §1.1, §1.4, §7.9; G3 §4.8.
- **Maturity.** solid.

### X4-scenarios-30. Mode switching: paper to live, live to paper, PC to VPS, cTrader to Hyperliquid

- **What happens.** A unit moves worlds. Its numbers carry over (promote carries the paper lane's last calibrated values, G9 §3.2), but its costs do not (paper has zero slippage), its equity base changes ($10,000 demo to a $200 share, G9 §3.1), and its brake counters may or may not reset.
- **Why.** His "scenarios of switching" and his demo/live split (D13). Every switch is a place where a number means something else.
- **Levels.** unit: on any world switch, brake counters reset, house money is zero, the size starts at the first ladder level (dose escalation, R3 §2.4), costs are "uncalibrated" until N live fills. book: the unit's share is the live share, not the demo balance. node: a switch happens only when the unit is flat and at a day boundary unless he forces it. operator: the click (promotion is his, D19).
- **Engages.** Ledger: `world_switch_reset_rule`, `size_level_now` (starts at level 1), `live_fills_until_calibrated`, `switch_only_when_flat`.
- **Correct outcome.** A freshly promoted unit cannot trade a demo-sized position live; its first live week is a measured ramp.
- **Sim proves.** A workflow test on the switch, plus a Monte Carlo of the ramp: cushion at risk in the first 50 live trades under "full size at once" against the ladder.
- **Likely / bad.** L3 / S3-S4 (the demo-sized position live is an account killer).
- **Sources.** D13, D19, G9 §3.1-3.3, R3 §2.4, §5.4.
- **Maturity.** solid.

## Family E. Market structure shocks

### X4-scenarios-31. Flash crash: 3 % in 90 seconds and back

- **What happens.** A liquidity hole (the 2010 US flash crash, the 2016 GBP flash crash at 00:07 UTC, the 2019 JPY flash in the Tokyo holiday gap): stops fill 2 % through, then the price returns. Every stop in the move is a maximum loss at the worst price; a unit with no stop at the broker gets no fill at all.
- **Why.** The stop at the broker is the only protection that works when the node cannot react in time; the worst-price cap on Hyperliquid (5 %, G9 §3.4) is a protection too.
- **Levels.** trade: the broker-side stop (every live order carries one, G4 §3.7) fills; the node journals `gap_through_stop`. unit: after a fill far through its stop, a cooling time before re-entry on that market (the market is broken, not the unit). book: the event window counts the crash as one event. BMS: a velocity tell (price moved too far too fast, the CME idea, R2 §3.1) raises a short instrument caution; if several instruments show it, a class isolation. account: marked equity may breach the floor buffer for a minute and recover: the floor rule must say whether a one-minute breach counts (R2 §2.3: FTMO measures on equity; the kill line in Gen 3 is marked on every fill). node: —. operator: page if the floor buffer was breached.
- **Engages.** B: broker stop, velocity caution, event window, floor rule with a dwell time. Ledger: `broker_side_stop_required`, `velocity_caution_rule`, `floor_breach_dwell_s`, `reentry_cooling_after_gap`.
- **Correct outcome.** Loss per position at most stop plus the gap allowance; no re-entry into the hole; the floor does not trip on a one-minute spike unless the rule says marked-instant.
- **Sim proves.** The `rk5` shock list replayed tick by tick: realised loss per stop policy; floor-rule variants (instant marked, dwell, realised).
- **Likely / bad.** L2 / S3-S4.
- **Sources.** G9 §1.1, §3.4, §7.1; G10 §6.2 (`rk5`); R2 §3.1; G4 §3.7.
- **Maturity.** solid.

### X4-scenarios-32. Spreads widen everywhere at once (no news, no crash)

- **What happens.** A liquidity provider pulls quotes; every FX pair at the broker shows 4× spread for twenty minutes. Nothing moved. Scalpers' edge after costs is negative for those minutes.
- **Why.** The SQS exists for this (C21: it stays), per instrument. Everywhere-at-once is the class-level version.
- **Levels.** unit: the SQS blocks each entry on its own instrument (built, off the path, G9 §1.1). BMS: when the SQS blocks on K of N instruments of a class at once, the co-move score fires the class caution (no new entries) without waiting for a loss. node: —. operator: ticket "broker-wide spread event".
- **Engages.** B: SQS, class caution. Ledger: `sqs_ratio`, `sqs_block_threshold`, `co_move_score`.
- **Correct outcome.** No entries at 4× cost; positions open stay on their stops; trading resumes when spreads normalise.
- **Sim proves.** Replay of spread-only events: R of entries blocked against taken.
- **Likely / bad.** L4 / S1-S2.
- **Sources.** C21, G9 §1.1, §4.1 (SQS in no pack), R2 §3.3.
- **Maturity.** solid.

### X4-scenarios-33. A stock or index halt while a position is open

- **What happens.** A single-stock halt (LULD, news pending) or an index-wide halt (7 % breaker). The position cannot be closed; the stop at the venue is suspended; the reopen auction prints far away.
- **Why.** "Exits are never blocked" has an exception the market imposes. The template must know a halt is possible on these classes and size for it.
- **Levels.** trade: the stop is held, not cancelled; the reopen price is the fill. unit: no new entries on a halted instrument; after reopen, a caution for the auction minutes (idea in scenario 12). book: halt-prone classes carry a halt allowance in sizing (like the gap allowance). BMS: an index halt is a class isolation by definition. node: detects the halt from the venue status (today nothing reads a halt state; a market with no quotes for 120 s stands down as stale, which is the wrong word, G9 §1.1). operator: ticket.
- **Engages.** B: halt detection, auction window, halt allowance. Ledger: `halt_detection_rule`, `auction_no_entry_window`, `halt_allowance_pct`.
- **Correct outcome.** The loss on the reopen is within the allowance; the system does not misread a halt as a feed fault and restart things.
- **Sim proves.** Historical halts replayed on the stock and index records: loss distribution and the allowance that covers 95 %.
- **Likely / bad.** L3 on stocks, L1 on indices / S3.
- **Sources.** R2 §3.1, G9 §1.1, G7 §4.1 (stock routes do not exist yet; the class enum does).
- **Maturity.** plausible (no stock route exists yet).

### X4-scenarios-34. Futures limit up or down, and the contract that stops trading

- **What happens.** A future hits its daily limit; no trade is possible in that direction; the velocity logic halts it (R2 §3.1). A unit short the limit-up contract cannot cover.
- **Why.** Futures are in the class enum with records from CME documents but no route (G7 §4.1). When a route exists this is day one.
- **Levels.** trade: the stop cannot fill; the loss is bounded only by the limit sequence. unit/book: limit-prone contracts carry a limit allowance; the template may refuse to hold through the overnight session. BMS: isolate the contract on a limit event. operator: page if a position is locked.
- **Engages.** Ledger: `limit_move_allowance`, `halt_detection_rule`, `overnight_hold_rule` (per unit type).
- **Correct outcome.** No scalper holds a limit-prone future overnight; a locked position's worst case was in its size.
- **Sim proves.** Limit days from history: loss under the allowance.
- **Likely / bad.** L1 (no route yet) / S4.
- **Sources.** G7 §4.1, R2 §3.1.
- **Maturity.** plausible.

### X4-scenarios-35. A black swan (the SNB, a de-peg, a broker going under)

- **What happens.** A 20 % move in a currency in minutes; broker-side stops fill 10 % through; the broker's own book is wrecked; negative balances appear. The 2015 SNB unpeg.
- **Why.** His floor is for "black swan or something genuinely wrong" (C10). The only sizing defence is exposure per driver small enough that a 20 % gap costs at most the cushion, plus a broker that offers negative-balance protection (a fact to check per broker; not checked here).
- **Levels.** trade: stops fill where they can. unit: nothing it can do in time. book: —. BMS: the per-driver exposure cap (idea 92) is sized so that a 20 % gap on any one driver costs at most the buffer before the floor, not the floor; the kill switch at `all` with BLACK (close all, pause) after the event, raised automatically by the velocity tell at the top level or by him. account: marked equity may be below the floor; the floor's action (stop the pot till re-seed) runs. node: expects rejections, unknown answers, a reconcile hold (all exist, G9 §1.1). operator: page; the day's work is reconciliation.
- **Engages.** B: per-driver exposure cap sized to a tail gap, kill BLACK, floor action, reconcile hold. Ledger: `per_driver_exposure_cap`, `tail_gap_assumption_pct`, `kill_black_auto_trigger`, `floor_hit_action`, `negative_balance_protection` (a fact per broker, to be filled).
- **Correct outcome.** The account survives below the floor but above zero; nothing is owed; the system is paused, journalled and reconcilable.
- **Sim proves.** The `rk5` SNB replay with the cap on: worst loss as a share of seed per cap level.
- **Likely / bad.** L1 / S5.
- **Sources.** C10, C27, G10 §6.2, R2 §3.3.
- **Maturity.** solid.

### X4-scenarios-36. Liquidity hole on one instrument: the stop is there, nobody is on the other side

- **What happens.** A thin CFD at 03:00: the stop is hit, the broker fills in three partial pieces over 40 seconds at worsening prices; or rejects the market order.
- **Why.** Partial fills and rejections are modelled nowhere on the unit path (paper has none, G9 §3.1).
- **Levels.** trade: partial exits are accepted and journalled per piece; a rejected stop escalates (protection escalation exists: three tries, then reduce-only close, G9 §1.1). unit: the residue is closed by the escalation; its journal records the slippage per piece. BMS: the instrument's measured fill quality by hour feeds placement (a 03:00 thin CFD is not a scalper's market). operator: page only on an escalation failure.
- **Engages.** B: protection escalation. Ledger: `partial_fill_policy`, `fill_quality_by_hour`, `protect_retry_max` (exists as a placeholder).
- **Correct outcome.** Residue is zero within the escalation; the hour is marked as bad for that instrument.
- **Sim proves.** Paper lane with a partial-fill and rejection model: residue and slippage distribution; the escalation closes every residue.
- **Likely / bad.** L3 / S2.
- **Sources.** G9 §1.1, §3.1, §3.4.
- **Maturity.** solid.

### X4-scenarios-37. The aftershock: a second wave an hour after the first

- **What happens.** The first shock is caught; brakes release; the second wave (a second headline, a margin cascade) hits the re-entered positions. Reinsurers' "secondary peril".
- **Why.** Every release rule is a bet that the event is over.
- **Levels.** BMS: after any isolation or BMS breaker, a settling window with half size and a retrip back-off (scenario 12); a second trip within the settling window locks the class out for the day. operator: ticket.
- **Engages.** Ledger: `settling_time`, `isolation_retrip_backoff`, `retrip_lockout_rule`.
- **Correct outcome.** The second wave costs less than the first.
- **Sim proves.** Two-wave shocks from history (Brexit night had several): loss per wave under each resume rule.
- **Likely / bad.** L2 / S3.
- **Sources.** R3 §3.1 (retry then lockout), G10 §3.1, R2 §3.1.
- **Maturity.** solid.
