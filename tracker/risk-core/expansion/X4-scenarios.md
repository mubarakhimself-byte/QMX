# X4: the scenario catalogue

Expansion layer: scenarios. File id `X4-scenarios`. Scenarios 01 to 37 were drafted on 2026-11-03 by a Fable expansion agent before the alphaXiv harvest; Stage B (2026-11-03, the X4 linking agent) finished families F to M, the combinations, the harness, the problems, collisions, restructure proposals, gaps and the roundtable, and mapped the draft's ledger ids onto ledger v0. Read-only everywhere except this file, `ledger/additions/X4-scenarios.yaml` and `linking/stage-b/X4-scenarios/`.

His ask (M12, `seeds/operator-words-2026-11-03.md:79`): "we also need to generate scenarios that can happen more than that ... scenarios of losing together, all together, scenarios of ... the isolation scenarios, scenarios of correlation, scenarios of new[s], scenarios of switching." And (M10, `:13`): worst, realistic and best cases "all factors considered", because "most agents don't consider all factors". His objection to the lead's "losing together" sim stands: it had no brakes, no exposure and no drawdown rules in it (SEEDS C32, replies row 23).

This catalogue is the seed for the numbers-lens simulations and for every design test. It does not pick a brake set. It says what each scenario demands of every level, so the funnel and the architecture can check a proposed template against all of them.

## How to read this

- **Levels** (his, B1 and the brief): **trade** (one position and its stop or exit), **unit** (one unit's entries, size and own brakes), **book** (the cluster of one style), **methodology** (every unit that shares one logic, across books; his fourth level, which no shipped layer owns today), **BMS** (the portfolio: splits capital, isolates, opens and closes slots), **account** (the broker account: equity, margin, floor), **node** (the machine: feed, clock, stand-downs, orders), **operator** (him). "—" means that level has nothing to do.
- **Engages** lists the brakes (B), accelerators (A) and ledger variables that the scenario touches. Ledger ids are v0 ids (`ledger/variables.yaml`, marked "(v0)" from scenario 38 on) where the idea already exists there, and otherwise the ids in `ledger/additions/X4-scenarios.yaml`. The draft's ids for scenarios 01 to 37 were mapped onto v0 in Stage B; the mapping table is in Part 1c.
- **Likely / bad** is a first guess, **[judgment]** throughout, to be replaced by measured rates in the simulations. Likelihood per live month: **L5** most days, **L4** most weeks, **L3** most months, **L2** a few times a year, **L1** rare. Severity if no brake acts: **S1** nuisance (under one trade), **S2** a bad day (about a day budget), **S3** eats much of the cushion, **S4** reaches the floor, **S5** beyond the floor (margin call, stuck positions, debt).
- **Sim proves** names the pass test a simulation must run for this scenario. The harness is X4-scenarios-90; its parts are 96 to 99.
- Maturity tags per the brief: **solid**, **plausible**, **wild**.
- **Components** (Stage B): from scenario 38 on, each scenario names the Stage A components it links by short id (`A3-095` means `A3-structure-regimes-scenarios-095`; `A1` sizing and allocation, `A2` brakes, drift and exits, `A3` structure, regimes and scenarios, `A4` template, agents and telemetry, `A5` top-up). Scenarios 01 to 37 are themselves components `A3-191` to `A3-227`; their links are tabled in Part 1c. **Per class** lines appear where the classes differ.
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
| I. Edge and regime | 60-66 | decay, regime change, losing streak with a real edge, winning streak with accelerators, same signal across the day, the August 2007-style unwind, the overfit backtest and the upside alarm |
| J. Account and capital | 67-73 | margin, leverage, floor, cushion, restart, sweep, deposits |
| K. Operator | 74-77 | away, error, panic, unreachable with open trades |
| L. Instrument-specific | 78-81 | futures rolls and expiry, energy reports, crypto liquidation cascades, single stocks (funding is in 44, halts in 33) |
| M. Two at once | 82-89 | combinations: news plus stale feed, flash crash plus link down, decay plus cost drift, isolation plus operator away, bug plus accelerators, correlation spike plus leverage cut, floor plus losing run, the energy triple |
| The harness and the design ideas | 90-99 | the harness (90), event window (91), same bet (92), N_eff (93), isolation lifecycle (94), sectoring (95), scenario as data (96), scorecard (97), reverse stress (98), interactive bench (99) |
| Parts 2 to 7 and Appendix A | | problems with options, collisions, restructure proposals, gaps, his questions, method notes, the roundtable |

---

# Part 1. Ideas: the scenarios

## Family A. Losing together

### X4-scenarios-01. Many units lose on one shared move (the "losing together" case, with brakes on)

- **What happens.** A single driver moves several markets at once: a USD move takes EURUSD, GBPUSD, gold and the US indices in one direction for an hour. Five units in three books are short the same thing without knowing it. Each takes a full stop. The lead's sim of this had no brakes (`sims/units_split.py`, the ρ = 0.5 row: 32 % floor touches); this scenario is the same case with every level acting.
- **Why a trader wants it.** This is the normal way a small book dies: not a black swan, a Tuesday. His words: "many markets losing together isn't a black swan. Good correction" (C27). R2 §4.2: the correlation that bites is shared exposure, not noise.
- **Levels.** trade: each stop fires on its own; exits are never blocked. unit: each unit counts its own loss; a unit-level count brake must not fire on one correlated loss as if it were a streak (it is one event). book: the book's loss budget counts the five losses **once as one event** inside an event window (idea 91), so the book brake reads "one big hit", not "five strikes". methodology: if all five share one logic (say mean reversion), the methodology view flags "logic X lost everywhere in one hour" as a regime tell, not a unit fault. BMS: computes same-bet exposure before the move (idea 92) so the five were never allowed to add to more than one unit's worth of USD risk; after the move, raises a caution (no new entries on the same driver for a cooling time). account: equity, marked, is read fresh; open risk sum drops as stops fire. node: nothing special; orders flow. operator: a ticket, not a page, unless the book budget is gone.
- **Engages.** B: book daily loss budget, event window, same-bet cap, BMS driver caution. A: house money must be **off** for the rest of the window (one shared winning move is not five independent wins either). Ledger: `loss_event_window`, `same_bet_exposure_cap`, `shared_driver_tags`, `effective_independent_bets`, `period_loss_budget`, `house_money_lockout`.
- **Correct outcome.** Total loss ≤ one event's allowance (for example the book's per-event cap, about one day budget), no unit benched for a streak it did not have, no new same-driver entries for the cooling time, the book trades again next day. Growth over 60 days stays close to the independent case because the cap on shared exposure, not a smaller size everywhere, did the work.
- **Sim proves.** With the shared-factor model (ρ by driver) and the brakes on: floor-touch rate at ρ = 0.5 falls from 32 % toward the ρ = 0 rate, and growth stays within X % of the ρ = 0 growth. It also measures how many "streak" fires the event window prevented.
- **Likely / bad.** L4 / S3 without brakes; S2 with them.
- **Sources.** C27, C29, C32, B15; `sims/units_split.py`; R2 §4.2, §4.3; R3 §3.3 (hours clause); G9 §6 (no cross-unit exposure exists).
- **Maturity.** solid.

### X4-scenarios-02. Correlation spike: independent yesterday, one bet today

- **What happens.** The measured correlation between the units' markets jumps (risk-off, a central-bank surprise, a liquidity squeeze). Positions sized on yesterday's correlation are now one bet. R2 §3.3: correlation rises in bear moves and extreme losses are far more correlated than a normal model says.
- **Why.** The same-bet check is only as good as its correlation input; a spike is when it is wrong.
- **Levels.** trade: —. unit: —. book: the book's N_eff falls; the book's per-unit share should fall with it (R2 §4.3: share = 1/√(N(1+(N−1)ρ))). methodology: —. BMS: reads the fast tells (spread and volatility against the usual for this hour, across the class) rather than waiting for a correlation window (R2 §3.3 says those are the fast ones); on a spike, trims new entry size across the correlated group and raises the same-bet count. account: —. node: —. operator: ticket.
- **Engages.** B: same-bet cap with a **stress correlation** input (use the higher of measured and stressed ρ); BMS trim. A: none. Ledger: `correlation_stress_rho`, `effective_independent_bets`, `co_move_score`, `entry_size_trim_on_comove`.
- **Correct outcome.** New entries during the spike are sized as if ρ were high; open positions keep their stops; no brake fires on healthy units; the trim lifts when the tells clear.
- **Sim proves.** Two-regime correlation (ρ 0.1 normal, 0.7 stressed, switching daily with persistence): the stressed-ρ sizing keeps floor touches under the bound while the measured-ρ sizing does not.
- **Likely / bad.** L3 / S3.
- **Sources.** R2 §3.3, §4.2; C18 (correlation ledger "internally external").
- **Maturity.** solid.

### X4-scenarios-03. Same signal, many units (crowding inside QMX)

- **What happens.** Ten units built from the same logic family on correlated markets all get the same entry in the same minute (a breakout on the London open on five EUR pairs). The frequency thesis counts ten bets; there is one.
- **Why.** His "twice the edge, twice the size" worry and his frequency thesis both assume independence (STATE item 10; the brief's facts).
- **Levels.** trade: —. unit: a unit cannot see the others; it must not try. book: counts same-bet entries once toward the day budget. methodology: the methodology level is exactly for this: "units of logic X on driver Y" is one bet; show N_eff per methodology. BMS: before funding, the cross-unit hook refuses or trims the eleventh same-bet entry (today it passes every order, G9 §6). account: —. node: —. operator: sees "effective units: 2.3 of 10" on the BMS screen (idea 93).
- **Engages.** B: same-bet cap, methodology N_eff. Ledger: `same_bet_exposure_cap`, `effective_independent_bets`, `methodology_tag`.
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
- **Engages.** A: house money (scoped, windowed, capped). B: accelerator lockout. Ledger: `house_money_threshold`, `house_money_scope`, `house_money_lockout`, `loss_event_window`.
- **Correct outcome.** Accelerators add size only on independent, realised, cushion-covered profit; a correlated reversal after a correlated win costs no more than it would without house money.
- **Sim proves.** Correlated win then correlated loss within two hours: equity path with naive house money against windowed house money.
- **Likely / bad.** L4 / S2-S3.
- **Sources.** A21, C19, G3 §4.2 (house money details and its cap rule), G6 (house money absent from Book sources).
- **Maturity.** solid.

### X4-scenarios-06. Three books, one account: the losses net but the brakes don't

- **What happens.** The scalper book is up $40, the intraday book is down $60, the account is down $20. Each book brakes on its own budget: the intraday book stops, the scalper book keeps sizing off a $500 start it believes is untouched (G9 §6: each unit sizes from the account's equity at its start plus its own results).
- **Why.** Book budgets must be allocated from the account, and each unit's equity view must be the one the account has. Pod shops run this as net limits per pod plus a firm limit (R2 §2.3).
- **Levels.** trade: —. unit: sizes from its allocated share, refreshed, not from the whole account. book: its budget is a share of the BMS's; its brake reads its own realised and marked loss. methodology: —. BMS: holds the account-level daily loss budget and allocates; when the account hits the BMS budget every book stops entries even if one book is under its own. account: equity is marked and refreshed (today cTrader equity is read once at sign-in, G9 §3.3). node: —. operator: —.
- **Engages.** B: BMS daily budget, book budgets as shares, account equity refresh. Ledger: `bms_daily_loss_limit`, `period_loss_budget`, `unit_capital_share`, `equity_refresh_s`, `brake_equity_basis` (marked or realised, named per brake).
- **Correct outcome.** No unit sizes from money another unit lost; the account-level brake trips before the sum of book budgets would; profits in one book do not silently fund losses in another unless the BMS said so.
- **Sim proves.** Three books with independent P&L on one account: with per-unit "start equity" sizing the account breaches the floor while every book brake is quiet; with shares and refresh it does not.
- **Likely / bad.** L5 / S3.
- **Sources.** G9 §6, G11 §2, B2, C6, R2 §2.3.
- **Maturity.** solid.

### X4-scenarios-07. The slow bleed with no event: death by a thousand small losses across the whole book

- **What happens.** No single bad day. Costs are a little higher than modelled on every market; each unit is at −0.02R per trade net; across 300 trades a day the book bleeds 6R a day, under every daily brake.
- **Why.** Brakes keyed on a day's loss never fire; the floor arrives in a month. R2 §2.5: "A unit whose costs doubled is broken today, whatever its P&L."
- **Levels.** trade: —. unit: input checks (cost per trade against calibrated, fill quality) alarm before P&L does. book: a weekly burn rate (loss of cushion per week) with a slow window, the SRE "ticket" class (R3 §3.5). methodology: —. BMS: cushion burn rate across the whole portfolio; steps size levels down when the slow window burns faster than the plan. account: —. node: —. operator: a weekly ticket with the burn chart.
- **Engages.** B: slow-window burn rate, cost drift alarm, size level step. Ledger: `burn_rate_slow_window`, `burn_rate_ticket_threshold`, `cost_drift_multiple`, `cushion_burn_rate`.
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
- **Engages.** B: class isolation, SQS per instrument, spread-against-cost guard. A: none during isolation. Ledger: `isolation_scope`, `co_move_score`, `market_isolation_trigger`, `isolation_ttl`, `isolation_end_rule`, `sqs_score`.
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
- **Engages.** B: isolation mode, protection escalation (exists, G9 §1.1). Ledger: `isolation_mode`, `soft_kill_exit_schedule`.
- **Correct outcome.** Open positions are closed at the cost the mode accepts; nothing is forced flat into a 5× spread when "no new entries" would do.
- **Sim proves.** Shock replay with open positions: realised loss under hold-to-stop, staged exit and instant flatten, per shock type.
- **Likely / bad.** L3 / S2-S3.
- **Sources.** C21, G10 §3.1, §7.10; G9 §1.1 (flatten does nothing today, "What is missing" 9).
- **Maturity.** plausible.

### X4-scenarios-12. The resume after isolation (the reopen is where people get hurt)

- **What happens.** The isolation's TTL runs out at 14:00. Every unit in the class re-enters at once at full size into the first minutes of a reopened, still-thin market. Exchanges know this: the reopen auction is staged for a reason (R2 §3.1).
- **Why.** A brake that releases all at once makes its own shock.
- **Levels.** unit: after a release, first entries at half size for a settling time (April's ×0.1 weights for the settling window, G10 §3.1). BMS: staged resume: half size, then full after N clean minutes with the tells still clear; a second trip inside the settling time doubles the next TTL (retry then lockout, R3 §3.1). operator: ticket.
- **Engages.** B: staged resume. A: locked out during settling. Ledger: `isolation_end_rule`, `settling_time`, `resume_size_fraction`, `isolation_retrip_backoff`.
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
- **Engages.** B: BMS breaker, kill switch `all` with the YELLOW effect, floor buffer. Ledger: `bms_circuit_breaker`, `burn_rate_page_threshold`, `bms_buffer_before_floor`.
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
- **Engages.** B: news window (pre, post), fail-safe. A: house money off inside the window. Ledger: `news_blackout_before`, `news_blackout_after`, `news_impact_level_map`, `news_fail_safe_affected`, `house_money_lockout`.
- **Correct outcome.** No new entries in the window; positions already open are the unit's own call; the window is sized to the release's measured impact, not a colour.
- **Sim proves.** Replay of release days with the window on and off: losses avoided, entries missed, and the best pre and post widths per release class by measured post-release move and spread (R2 §3.4).
- **Likely / bad.** L5 (several releases a week) / S2-S3 per event.
- **Sources.** C28, D9, G9 §2, G10 §3, R2 §3.4.
- **Maturity.** solid.

### X4-scenarios-16. The release the calendar did not have, or had wrong

- **What happens.** An unscheduled statement, a wrong time (DST shift in the provider), a holiday moving a release, or the free calendar simply missing it (G9 §2: the free source has no actuals). Units trade straight through.
- **Why.** Fail-safe up is the only honest rule when the calendar is a free feed (G10 §7.11).
- **Levels.** unit: the SQS and spread guard are the backstop: a spread 5× usual blocks the entry whatever the calendar says. BMS: a surprise detector on the tells (volatility jump within 12 one-minute bars, R2 §3.3) raises a short caution on the affected currency's instruments. node: calendar staleness itself is a stand-down for new entries on calendar-dependent instruments (the ingest already fails closed when stale). operator: ticket "calendar missed X".
- **Engages.** B: SQS, spread guard, surprise caution, calendar-stale stand-down. Ledger: `sqs_score`, `spread_cost_guard`, `surprise_caution_min`, `news_calendar_max_staleness`.
- **Correct outcome.** The tells catch what the calendar missed; losses are one spread-guarded entry at most.
- **Sim proves.** Remove 20 % of events from the calendar at random in replay; measure the loss with tells-only protection against calendar-only.
- **Likely / bad.** L4 / S2.
- **Sources.** G9 §2, G10 §3.4, §7.11, R2 §3.3.
- **Maturity.** solid.

### X4-scenarios-17. News by region hits instruments the currency map does not cover

- **What happens.** A US release moves gold, oil, the Nikkei CFD and bitcoin. Every generation scoped news by currency only (G10 §3.5). Gold is tagged USD at best; the index and crypto are not.
- **Why.** His sectoring ask: "at an instrument level, at a regional level" (C27). Each instrument needs its own list of drivers.
- **Levels.** BMS: each instrument record carries `shared_driver_tags` (currencies, home exchange, region, class, plus named events it reacts to); the news window resolves through the tags, not the symbol. The tags are seeded by class defaults and refined by the measured post-release move per instrument. operator: can edit the tags.
- **Engages.** Ledger: `shared_driver_tags`, `news_impact_level_map`, `measured_event_impact`.
- **Correct outcome.** A US release blocks gold and the US index entries; a Japanese release blocks the Nikkei CFD and JPY pairs; crypto reacts to its own event classes (G10 §3.5 notes they need their own vocabulary).
- **Sim proves.** Event-study replay per release and instrument: the move and spread in the minutes after, which both sets the tag and the window width.
- **Likely / bad.** L4 / S2.
- **Sources.** C27, G9 §2, G10 §3.5, R2 §3.4.
- **Maturity.** solid.

### X4-scenarios-18. Medium-impact news every hour: the window swallows the day

- **What happens.** On a busy data day, ±30 minutes around every medium release leaves a scalper 90 minutes of trading. The frequency thesis dies by calendar.
- **Why.** Windows are a brake with a cost; width must follow measured impact, not colour.
- **Levels.** unit: its template states the impact level it blocks on (a 5-minute scalper may block only high; an ORB blocks high and medium around its open). BMS: windows by measured impact class per instrument; the "missed entries" count is a reported cost. operator: sees "hours blocked today".
- **Engages.** Ledger: `news_block_impact_min` (per unit type), `news_blackout_before`, `entries_blocked_by_window`.
- **Correct outcome.** Blocked hours per day under a bar on a normal week, with the high-impact protection intact.
- **Sim proves.** Hours blocked and R lost to blocked entries, per width policy, against R saved.
- **Likely / bad.** L4 / S1 (missed trades), S2 in growth terms.
- **Sources.** R2 §3.4, G10 §3.4 (±30 minutes in t3).
- **Maturity.** solid.

### X4-scenarios-19. The post-event tail: spreads stay wide for days (demand surge)

- **What happens.** After a shock, costs stay high for a week (liquidity providers widen). The window closed; the units trade into 2× costs. Reinsurers call the parallel "demand surge" after a catastrophe.
- **Why.** The cost state, not the calendar, decides whether a scalper's edge exists (R2 §4.2: cost is the master state for scalpers).
- **Levels.** unit: the spread-against-cost guard (planned, L0:383, not built) refuses entries whose cost exceeds the unit's cost target in R. BMS: the class's `cost_state` word (normal, elevated, toxic) feeds placement; elevated means half size for scalpers. operator: ticket.
- **Engages.** B: spread guard, cost state. Ledger: `spread_cost_guard`, `cost_state`, `unit_cost_target` (per unit).
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
- **Engages.** B: hand-over caution window, session shares. Ledger: `session_handover_buffer_width`, `session_budget_share`, `fix_window_min`.
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
- **Engages.** B: open-breadth budget scaling, calendar-aware stale rule. Ledger: `open_breadth_budget_scale`, `class_budget_share_cap`, `weekend_mode` (per unit type), `feed_stale_after` (calendar-aware).
- **Correct outcome.** Weekend losses are bounded by the crypto class's own share; the system does not read closed FX feeds as a fault; Sunday night does not open with a crypto-sized hole.
- **Sim proves.** A week with weekday breadth 10 and weekend breadth 2, crypto with weekend volatility 1.5×: floor touches under whole-budget against scaled-budget.
- **Likely / bad.** L5 (every weekend) / S3.
- **Sources.** D10, C1, G9 §1.1, §2 (calendars per market), G7 §4.1.
- **Maturity.** solid.

### X4-scenarios-25. The weekend gap: Sunday open 80 pips through the stop

- **What happens.** A weekend headline. The Sunday open gaps through every FX stop; fills are at the open, not the stop. The per-trade loss limit (A19) was a hope.
- **Why.** The stop limits the loss only when the market trades through it. The gap allowance is a sizing input.
- **Levels.** trade: the stop fills at the open; the unit journal records `gap_loss_beyond_stop` (exists in the trade row, G9 §7.1). unit: templates for styles that hold over the weekend (swing, some intraday) size with a gap allowance (stop distance plus the instrument's historical weekend gap at a percentile); styles that do not (scalpers, ORB) are flat by Friday close by rule. book: the Friday-close flat rule per book. BMS: weekend-held exposure cap. account: —. node: —. operator: —.
- **Engages.** B: Friday flat rule, gap allowance, weekend exposure cap. Ledger: `weekend_flat_rule`, `gap_allowance_pct`, `weekend_exposure_cap`, `gap_loss_beyond_stop` (exists).
- **Correct outcome.** Scalpers never hold over the weekend; held positions were sized so that the gap costs at most the planned R plus the allowance.
- **Sim proves.** Monte Carlo with weekend gaps drawn from the instrument's history: realised loss distribution against planned R under each rule.
- **Likely / bad.** L2 for a big gap / S3.
- **Sources.** A19, G9 §7.1, D7 ("ORB won't hold overnight").
- **Maturity.** solid.

### X4-scenarios-26. The 17:00 New York rollover: spread spike, swap charge, day boundary, all in one minute

- **What happens.** At 21:00/22:00 UTC the FX day rolls: spreads spike for minutes, swaps are charged (triple on Wednesday), and the forex calendar's day ends (G9 §2). A scalper enters at 21:59 into a 10× spread.
- **Why.** The retail scalper's oldest scar; G7 §4.3 notes the spike.
- **Levels.** unit: a rollover caution window per instrument from its calendar; swap as a cost input the template knows (A11). book: the day boundary for budgets is a declared choice per book (UTC, the venue's day, or the book's own), named in the ledger. node: the stale-feed and spread guards must not read the spike as a fault. operator: —.
- **Engages.** B: rollover window, spread guard. Ledger: `rollover_window_min`, `swap_financing_cost`, `day_boundary` (per book), `triple_swap_day`.
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
- **Engages.** Ledger: `session_windows`, `dst_mismatch_check`.
- **Correct outcome.** Windows move with the market; no entries land in the wrong hour.
- **Sim proves.** A calendar test across the four DST dates of a year.
- **Likely / bad.** L2 (twice a year, for weeks) / S2.
- **Sources.** G9 §2, G7 §4.2.
- **Maturity.** solid.

### X4-scenarios-29. The day-boundary exploit: two strikes at 23:50, reset at 00:00

- **What happens.** A unit takes its second full stop at 23:50 UTC, is benched, and at 00:00 the counter resets (April and July both reset at the boundary, G10 §1). It trades again at 00:01 in the same bad conditions.
- **Why.** A count brake with a hard reset is a brake with a hole. The red team found this first (Part 5).
- **Levels.** unit: the brake's window is rolling (last N hours or last N trades), not the calendar day; or a bench carries a minimum rest (hours or trades) across the boundary. book: the day budget resets at the boundary, but a benched unit's rest does not. operator: —.
- **Engages.** B: rolling-window count brake, minimum bench rest. Ledger: `circuit_breaker_window` (rolling), `bench_min_rest`.
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
- **Levels.** trade: the broker-side stop (every live order carries one, G4 §3.7) fills; the node journals `gap_loss_beyond_stop`. unit: after a fill far through its stop, a cooling time before re-entry on that market (the market is broken, not the unit). book: the event window counts the crash as one event. BMS: a velocity tell (price moved too far too fast, the CME idea, R2 §3.1) raises a short instrument caution; if several instruments show it, a class isolation. account: marked equity may breach the floor buffer for a minute and recover: the floor rule must say whether a one-minute breach counts (R2 §2.3: FTMO measures on equity; the kill line in Gen 3 is marked on every fill). node: —. operator: page if the floor buffer was breached.
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
- **Engages.** B: SQS, class caution. Ledger: `sqs_score`, `sqs_hard_block_threshold`, `co_move_score`.
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
- **Engages.** B: protection escalation. Ledger: `partial_fill_policy`, `fill_quality_by_hour`, `protection_retry_max` (exists as a placeholder).
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

## Family F. Costs and execution

### X4-scenarios-38. Live slippage is twice demo slippage (the demo/live divergence)

- **What happens.** A unit promoted after 30 clean demo trades. Its demo fills came from the broker's demo server (G9 §3.4: a weak stand-in) and its paper lane had zero slippage by construction (G9 §3.1). Live, each entry fills 0.6 pips worse and each stop 1.2 pips worse. On a 6-pip stop that is 0.3R a round trip. The edge after costs is gone and P&L will take 300 trades to say so (R2 §2.1); the fills say so in 20.
- **Why.** His "can slippage be measured on demo" (D13) and "split QMX into demo and live, only the account differs" (D13). The node already writes what is needed: the send row carries the asked price, the filled row the venue price (G9 §3.4); no script reads them.
- **Levels.** trade: every fill writes slippage in price and in R, entry and exit apart (A4-167). unit: a cost ledger per unit and world (A1-146): demo, paper and live each calibrated on their own fills; `costs_uncalibrated` until N live fills; the unit's size uses the live cost once it exists and the demo cost plus a stress multiple before that (A2-223). book: —. methodology: —. BMS: the live-to-demo slippage ratio per instrument and hour is a placement input; an instrument whose live fills are far worse than demo is not a scalper's market at this broker. account: —. node: the slippage script over order rows (G9 "What is missing" 15) runs nightly. operator: a ticket when the ratio crosses a bar; the first live week shows "costs: calibrating, 14 of 50 fills".
- **Components.** A1-143, A1-144, A1-146, A2-166, A3-083, A4-035, A4-167, A4-168, A5-157.
- **Engages.** B: cost-drift input check (fast, tens of trades), live-fills-until-calibrated size discount. A: none until calibrated. Ledger: `slippage_cost` (v0), `cost_drift_multiple` (v0), `live_fills_until_calibrated`, `demo_live_slippage_ratio`, `cost_stress_multiple` (v0), `unit_cost_target` (v0).
- **Per class.** FX and metals at cTrader: last-look rejections must be read with the spread (A3-238). Index CFDs: slippage jumps at the cash open. Crypto perps: taker fee plus the 5 % worst-price cap (G9 §3.4); slippage is a fee question first. Futures: no route yet.
- **Correct outcome.** The gap is measured in the first 20 live fills; size is discounted until the live cost is known; a unit whose live cost in R exceeds its cost target stops entries on that instrument before P&L shows anything.
- **Sim proves.** Paper lane with a slippage model drawn from measured live fills, against the zero-slippage lane: R lost per 100 trades, and days to detection under an input-first check against a P&L check.
- **Likely / bad.** L5 (every promotion) / S3 for scalpers (a thin edge dies silently), S1 for swing.
- **Sources.** D13, A11; G9 §3.1, §3.4; G7 §4.3; R2 §2.2, §2.5; R8 numbers (costs dominate a 13-minute hold book).
- **Maturity.** solid.

### X4-scenarios-39. The broker changes its costs (commission schedule, spread tier, swap table)

- **What happens.** Overnight the broker moves the account to a wider spread tier, or raises commission per lot, or doubles the swap on a pair. Nothing in the record changes (there is no commission key, G9 §5.1). The unit trades on at the old cost assumption.
- **Why.** "A unit whose costs doubled is broken today, whatever its P&L" (R2 §2.5). Costs must reach the sizer (brief, facts that hold everywhere).
- **Levels.** trade: cost per trade written in R on every row (A4-150). unit: the hourly cost profile (A3-084) is refit from fills daily; a cost state word per instrument (normal, elevated, toxic) feeds the sizer's cost input; the edge-to-cost admission gate (A3-003) re-runs on the new cost and may refuse the instrument. book: —. BMS: the broker's cost schedule is a record refreshed weekly from documents (G7 §4.2) and daily from fills; a schedule change raises the spec-change stand-down that today has no producer (G9 §1.1). account: —. node: a spec-change row for cost fields too, not only lot step, margin, digits and leverage. operator: a card: "commission on EURUSD rose 40 %; three units now below their cost target".
- **Components.** A1-138, A1-146, A1-147, A2-166, A3-003, A3-014, A3-084, A2-102, A5-157.
- **Engages.** B: edge-to-cost gate, cost state, spec-change stand-down. Ledger: `commission_cost` (v0), `round_trip_cost_r` (v0), `cost_state`, `cost_drift_multiple` (v0), `spec_change_fields`.
- **Per class.** FX: spread tier and commission per lot. Crypto: maker and taker fee tiers change with volume. Index CFDs: financing rate. Energy CFDs: the roll adjustment is a cost line (scenario 78). Futures: exchange fees are stable, clearing fees are not.
- **Correct outcome.** The new cost is in the sizer within a day; units that no longer clear costs stop entries on that instrument; nothing is read as edge decay (A2-174 keeps the two apart).
- **Sim proves.** Step the cost up by 1.5x and 2x mid-run: R under "sizer reads the cost" against "sizer ignores it", and whether the decay check falsely flags the unit.
- **Likely / bad.** L2 / S2-S3.
- **Sources.** A11, D17; G9 §5; G7 §4.3; R2 §2.5; A3-014 (which cost binds per class).
- **Maturity.** solid.

### X4-scenarios-40. Demo and live disagree in behaviour, not only in fills (the paper twin)

- **What happens.** The same unit version runs on demo and live side by side. Live rejects two entries (last look), fills one partially, and sees a different bar close because the live feed lagged 400 ms. The two journals diverge; the live-day replay match drops under 0.80 and lands a bench card (G9 §7.2) although nothing is wrong with the unit.
- **Why.** "The unit trades identically on both and only the account differs" (D13) is the goal; the built shape is one code path with the world set by the account (G9 §3.3). Behaviour gaps are a fault class of their own.
- **Levels.** trade: a per-trade gap row between twin and live (A4-035): same signal, different outcome, with the cause (reject, partial, lag, price). unit: the replay match is split by cause before it may bench; a feed-lag cause is a node fault, not a unit fault. book: —. BMS: —. node: records feed lag per market; a lag past a bar's worth makes the bar unusable (bad data is "risk state unknown", A3-094). operator: the bench card says the cause.
- **Components.** A2-169, A2-174, A3-094, A4-035, A4-036, A4-028, A5-058.
- **Engages.** B: replay-match floor (v0 `replay_match_floor`), gap-cause split. Ledger: `replay_match_floor` (v0), `twin_gap_cause`, `feed_lag_max_ms`.
- **Correct outcome.** A behaviour gap is attributed before anything benches; the unit is never blamed for the node.
- **Sim proves.** A workflow test: inject rejects, partials and a 500 ms lag into one twin; the gap rows carry the right cause and no bench card lands.
- **Likely / bad.** L4 / S1 (a false bench costs trades, not money).
- **Sources.** D13; G9 §3.3, §7.2; R2 §2.2 (input checks).
- **Maturity.** plausible.

### X4-scenarios-41. The minimum lot is bigger than the planned risk (the silent oversize)

- **What happens.** A unit sized at $5 of risk on an index CFD with a 20-point stop needs 0.004 lots; the minimum is 0.01. The old Book clamp raised the size to the minimum (A1-154, "silent oversize"); the shipped sizer skips (G7 §4.4). On a $500 account whole classes are untradable at the planned risk (R3 §4.2: a Micro E-mini rounds to zero at a 16 % volatility target).
- **Why.** Lot granularity is a real per-class variable, not a detail (R3 §4.2). A clamp that rounds up is an accelerator nobody chose.
- **Levels.** trade: round down, skip below one step, record the residue and the reason (A1-153, A1-156). unit: a feasibility flag per instrument at the current budget (A3-002): "untradable at this size"; the unit's placement list drops the instrument instead of trading it oversize. book: —. BMS: the class feasibility map on the BMS screen: which classes this seed can trade at all; the budget split per style reads it (a $200 intraday share may fund no index CFD). account: —. operator: sees "3 of 9 classes feasible at $500".
- **Components.** A1-002, A1-153, A1-154, A1-155, A1-157, A3-001, A3-002, A5-042.
- **Engages.** B: min-lot skip (clamp). Ledger: `min_lot` (v0), `lot_step` (v0), `rounding_residue_r` (v0), `class_feasibility_flag`, `sleeve_feasible_min_loss_usd`.
- **Per class.** FX micro lots fit; gold at 0.01 lot of 100 oz is about $1 a point, borderline; index CFDs and crude often do not fit; crypto spot and fractional sizes fit; full-size futures never fit at this seed.
- **Correct outcome.** No trade ever risks more than planned because of a lot step; infeasible classes are named up front, not discovered by a stop.
- **Sim proves.** A contract test over the instrument set at seeds of $500, $1,000 and $2,000: which instruments are feasible at which risk per trade; and a Monte Carlo of the old clamp against the skip on a thin edge.
- **Likely / bad.** L5 (by construction at $500) / S3 under the clamp, S1 under the skip (missed trades).
- **Sources.** G3 §6 (min lot → oversize); G7 §4.4; R3 §4.2; A1-157.
- **Maturity.** solid.

### X4-scenarios-42. The conversion is wrong: quote currency, stale rate, points against pips

- **What happens.** The account is USD; the unit trades a JPY-quoted pair or a EUR-quoted index. The value per point is converted through a rate that is stale, or the record's pip is read as a point. The size is 10x or 0.1x what was meant. Stops are placed "ten times what was intended on another market" (the A3 test the plan wrote, G11 §1.3).
- **Why.** Every number has a measure and converts through the record (G11 §1.3); the conversion check at 0.1 % exists in the plan (G7 §4.2) and the sizer does no conversion today (G7 §4.4).
- **Levels.** trade: money at the stop from the broker's tick value, never from pips, conversion read live with a cross-check (A1-160); a conversion older than its freshness limit refuses the size (fail closed). unit: a size sanity band: the lots this trade asks for against the unit's own usual lots on this instrument; a 5x jump is refused with a reason (A2-003, the order-boundary veto). node: the connect-time verifier that "has never run" (G7 §4.2) runs at every session: pip formula, money exponent, timestamp unit. operator: a page on a refused 5x size with positions open; a ticket otherwise.
- **Components.** A1-160, A1-161, A1-165, A2-003, A4-179, A5-042, A3-001.
- **Engages.** B: order-boundary worst-case veto, conversion freshness, size sanity band. Ledger: `value_per_point` (v0), `value_conversion_max_age_s`, `size_sanity_band_multiple`.
- **Correct outcome.** No order leaves with a worst-case loss above the per-trade cap; a wrong conversion is caught at the order, not at the stop.
- **Sim proves.** A contract test that feeds a wrong pip and a stale rate into the sizer and asserts the veto fires; the dry chassis (A1-174) with a planted conversion fault.
- **Likely / bad.** L2 (once per new instrument class) / S4 (a 10x size is an account killer).
- **Sources.** G7 §4.2, §4.4; G11 §1.3; A17 (pips, points, ticks); R3 §4.2.
- **Maturity.** solid.

### X4-scenarios-43. Partial fills, rejections and duplicates on the entry

- **What happens.** A market order on a thin CFD fills half; the rest is left working; a retry on a transient error submits twice (the MQL5 trap, A2-060); the unit now holds 1.5x its intended size with one stop for one lot.
- **Why.** Paper has no partials or rejections (G9 §3.1); the node's unknown-answer path exists (G9 §1.1) but duplicates are a real risk event (R5, article 23315).
- **Levels.** trade: an entry is complete only when the venue shows the full quantity and its stop (the protection escalation already closes a position whose stop never shows, G9 §1.1); a residue beyond the lot step is closed reduce-only or the stop is amended to cover the whole position. unit: the order-send breaker with an error taxonomy: transient errors retry with back-off, permanent ones fail fast and never trip the breaker; a half-open probe before full restore (A2-060). node: an idempotency key per intent so a second tick cannot resend. operator: a push only when a residue cannot be closed.
- **Components.** A2-060, A2-104, A3-010, A3-073, A5-061, A2-101.
- **Engages.** B: order-send breaker, protection escalation. Ledger: `protection_retry_max` (v0), `partial_fill_policy`, `order_idempotency_required`, `order_send_breaker_state`.
- **Correct outcome.** Position size never exceeds the sized quantity; every lot has a stop; a venue that keeps rejecting is paused and probed, not hammered.
- **Sim proves.** Paper lane with a fill model (partial, reject, duplicate): final position against intent over 10,000 entries; the breaker's open and half-open transitions.
- **Likely / bad.** L3 / S2 (S3 if a duplicate meets a gap).
- **Sources.** G9 §1.1, §3.1; R5 (23315); R4 technique 6 (duplicate or partial fills as a trigger family).
- **Maturity.** solid.

### X4-scenarios-44. Carry shocks: a funding spike, the triple-swap night, a dividend on the index CFD

- **What happens.** A perp's funding rate goes from 0.01 % to 0.3 % per 8 hours in a squeeze; a held long pays 0.9 % a day. A Wednesday triple swap on an exotic pair costs a swing position a third of its planned R. An index CFD held over an ex-dividend date is debited the dividend on a short, or credited on a long, and the stop sits at the wrong price after the adjustment.
- **Why.** Carry and funding belong in the hold-and-size decision (A3-026, A1-148). QMB books them as cash events (G9 §5.2), the sizer never sees them, and the node reads no swap from the broker (G9 §5.1).
- **Levels.** trade: carry per day in R is a field on the position; a planned hold's carry is in the size (A1-148). unit: a hold-or-close rule when carry per day crosses a share of the expected edge per day; perps read the funding clock from the record (`funding_interval`, G7 §4.2). book: —. BMS: a funding spike across many perps is a crypto stress tell (A3-235 is population-level only; funding is the cheap tell). node: dividend and roll adjustments are booked as their own P&L line and never read as a stop trigger (A5-095). operator: —.
- **Components.** A1-148, A3-026, A3-055, A5-095, A4-150, A3-235.
- **Engages.** B: carry-to-edge hold rule, funding-spike tell. Ledger: `swap_financing_cost` (v0), `funding_cost` (v0), `carry_per_day_r`, `carry_hold_ceiling_share`, `funding_spike_tell`.
- **Per class.** Crypto perps: funding every 8 hours, paid between traders (R3 §4.1). FX: swap at the 17:00 New York roll, triple on Wednesday. Indices and stocks: dividends and financing. Futures: no carry, a roll instead (scenario 78). Metals: CFD swap or futures roll.
- **Correct outcome.** No position is held through a carry cost that eats its edge; adjustments never trigger stops; funding spikes feed the crypto stress reading.
- **Sim proves.** Replay with the funding and swap series: R with carry in the hold decision against carry ignored; count of stops falsely hit by adjustment gaps.
- **Likely / bad.** L4 (funding swings weekly) / S2 for scalpers (rarely hold), S3 for swing on exotics and perps.
- **Sources.** A11; G7 §4.2; G9 §5; R3 §4.1; R8 §4.6.
- **Maturity.** solid.

## Family G. Infrastructure

### X4-scenarios-45. The broker link drops with positions open

- **What happens.** The cTrader session falls over at 14:28 with four positions open and CPI at 14:30. The node cannot send, amend or read. The stops are at the broker or they are nowhere.
- **Why.** The April connectivity kill meant "a broker-side hard stop on every order" (G10 §3.1); every live order carries one (G4 §3.7, G9 §1.1). This is the scenario that justifies it.
- **Levels.** trade: the broker-side stop is the only protection that works; the working stop must never be only virtual (the MQL5 virtual-stop pattern is a trap here). unit: nothing it can do; entries are refused by the venue-not-ready stand-down (G9 §1.1). book: —. BMS: open risk during a link gap is counted at the broker stops, not at the working stops. account: —. node: reconnect with back-off; on reconnect a reconcile hold until the venue state is read (G9 §1.1); check whether stops were hit while offline (A2-059, Safe Mode); the phone push "broker link down with open trades" fires (C-18). operator: a page; the decision to flatten by hand through the broker's own app is his.
- **Components.** A2-059, A2-098 (connectivity kill), A2-102, A2-104, A4-170, A4-151, A1-146.
- **Engages.** B: venue-not-ready stand-down, reconcile hold, Safe Mode. Ledger: `broker_side_stop_required`, `reconnect_backoff_s`, `link_down_page_after_s`, `reconciliation_cadence` (v0).
- **Correct outcome.** Every position has a broker-side stop at all times, so a link gap of any length costs at most the stops plus gaps; on reconnect nothing trades until the book is reconciled; the page reaches him.
- **Sim proves.** A workflow test: kill the link with positions open, replay a 40-pip move, reconnect; assert the stops filled at the venue, the reconcile ran before any entry, and the push fired. And a Monte Carlo: loss distribution with broker-side stops against virtual stops under link gaps drawn from the node's own outage history.
- **Likely / bad.** L3 (links drop monthly) / S4 with virtual stops, S2 with broker-side stops.
- **Sources.** C21, C23; G9 §1.1, §1.2; G10 §3.1; G4 §3.7; R5 (22615, Safe Mode).
- **Maturity.** solid.

### X4-scenarios-46. The feed is stale, frozen or wrong (a bad tick, a flat line, a wrong symbol map)

- **What happens.** The quote for GBPUSD freezes for 90 seconds while the market moves; or one tick prints 2 % away and back (a bad tick); or after a broker update the symbol map points XAUUSD at XAGUSD. Units size and signal on the wrong price.
- **Why.** The stale-feed stand-down exists (120 s stale, 60 s fresh to clear, code constants, G9 §1.1) but 120 s is long for a scalper, a frozen quote inside 120 s is invisible, and nothing checks a tick against its neighbours. Bad data is "risk state unknown", never calm (A3-094).
- **Levels.** trade: a stale-price-used-in-an-order is a hard stop at once (R4 technique 6). unit: no entry on a market whose last quote is older than the unit's own bar fraction (a 1-minute scalper cannot use a 90-second-old quote; the stand-down's 120 s is a floor, the unit's limit is tighter); a bad-tick guard (a tick further than k spreads from the previous and reverting next tick is dropped). node: the connect-time verifier checks the symbol map on every session (G7 §4.2); a frozen quote (same bid and ask for N ticks while others move) is stale even inside 120 s. BMS: a stale feed on many markets at once is a node fault, not a market tell: the co-move score must exclude stale markets (never fill a closed or stale market with zero, R4 technique 8). operator: ticket; page if orders went out on stale prices.
- **Components.** A2-102, A3-094, A3-073, A3-078, A4-179, A4-180, A2-062.
- **Engages.** B: stale-feed stand-down (per unit tighter than the node's), bad-tick guard, symbol verifier. Ledger: `feed_stale_after` (v0), `unit_quote_max_age_s`, `bad_tick_spread_multiple`, `symbol_map_verified_at`.
- **Correct outcome.** No order prices off a frozen or bad quote; a stale market is excluded from every cross-market reading; a wrong symbol map is caught at connect, before any order.
- **Sim proves.** Replay with injected freezes, bad ticks and a swapped symbol: orders sent on bad prices under each guard; false stand-downs on calm history.
- **Likely / bad.** L4 (bad ticks weekly on CFDs) / S2, S4 for the symbol map.
- **Sources.** G9 §1.1; G7 §4.2; R4 technique 6 and 8; A3-094.
- **Maturity.** solid.

### X4-scenarios-47. The clock is wrong

- **What happens.** The VPS clock drifts 40 seconds, or the machine boots in the wrong zone after an update. Session windows open a minute early, the news window ends before the print, bar closes are mislabelled, and the day boundary moves.
- **Why.** The clock band stand-down exists (500 ms, 5 minutes inside 100 ms to clear, code constants, G9 §1.1). Every clock-based rule breaks twice a year anyway (scenario 28); a drifting clock breaks them every day.
- **Levels.** unit: windows run in the market's own zone from the calendar, never from the machine's local time. node: the clock band stand-down at `all`; a second check against the venue's server time at every reconnect (the record has `server_zone`, G9 §5.1); a time offset past the band stops entries and the phone push fires (C-18). BMS: cross-market readings that join markets by time are suspended while the band is open. operator: page on the halt (it already is one).
- **Components.** A2-102, A3-022, A4-179, A4-180.
- **Engages.** B: clock band. Ledger: `clock_drift_no_new_entry` (v0), `clock_drift_halt` (v0), `venue_time_check_cadence_s`.
- **Correct outcome.** No window or boundary ever runs on a bad clock; the halt clears itself when the clock is back.
- **Sim proves.** A calendar and clock test: inject offsets of 2, 30 and 400 seconds; assert which rules misfire and that the stand-down catches 400 s before any entry.
- **Likely / bad.** L2 / S2.
- **Sources.** G9 §1.1; A3-022; scenario 28.
- **Maturity.** solid.

### X4-scenarios-48. A restart mid-trade, and a crash loop

- **What happens.** The node process dies at 09:31 with a position open and a benched unit; the supervisor restarts it. The stand-downs that wait for him are rebuilt from journals, the kill level comes back (G9 §1.2), and the unit's own snapshot restores its block state for the same version. But the day-start equity, the loss counters and the benched state live nowhere a host writes (G9 §1.3), and a snapshot from another fingerprint starts cold (G8 §3.7). The unit trades again as if the day were new. Worse: 5 restarts in 10 minutes is a crash loop; the stand-down at `all` fires and waits for him (G9 §1.1).
- **Why.** "Loss counters survive restarts, market closes and date changes" (A2-011, R4 technique 6). A restart that resets the anchor voids the drawdown cap (R9 §3.4, Hsieh's 20.18 % against a 20 % cap).
- **Levels.** trade: open positions are adopted on restart (G9 §1.2). unit: brake state (counters, bench, anchor) is journalled, not only held in block memory; a restart replays the journal to rebuild it; a cold start (new fingerprint) carries the brake state in as a starting assignment, the way calibrated values are carried (G8 §3.7). book: the day's budget used is a persisted baseline (A2-064, A4-061), confirmed on restart. account: the floor and the high-water mark never reset on a restart (A5-010, two anchors). node: the crash-loop stand-down; a restart during a window or isolation re-reads the window state from the journal before any entry. operator: page on the crash loop (exists).
- **Components.** A2-011, A2-064, A4-061, A4-040, A5-010, A2-102, A4-170.
- **Engages.** B: crash-loop stand-down, persisted day baseline, journalled brake state. Ledger: `crash_loop_max_restarts` (v0), `day_start_equity` (v0), `brake_state` (v0), `brake_state_persisted`, `high_water_mark_equity` (v0).
- **Correct outcome.** A restart changes nothing a brake can see: same counters, same bench, same anchor, same window; a crash loop stops entries and wakes him.
- **Sim proves.** A workflow test: kill the process at ten random points of a replayed day; assert every brake variable equals the no-restart run's value; a Monte Carlo of the "anchor reset on restart" fault against the drawdown cap.
- **Likely / bad.** L3 / S3 (a reset anchor is a hidden accelerator).
- **Sources.** G9 §1.2, §1.3; G8 §3.7; R9 §3.4; R4 technique 6; A2-011.
- **Maturity.** solid.

### X4-scenarios-49. Split brain: two nodes think they own the same account

- **What happens.** His PC and the VPS both run the node against one cTrader account after a failed hand-over ("PC is home, servers substitute"). Both adopt the open positions; both place entries; one flattens what the other opened. Or one node's view of the position is stale and it places a "protective" order that doubles the exposure.
- **Why.** One account, one node is an invariant nobody has written; the orphan-position check (G9 §1.1) catches a position no unit holds, not a position two units hold.
- **Levels.** node: a lease on the account (one writer, renewed, with a fence token on every order); a node without the lease trades nothing and reads only; a lease hand-over happens flat and at a boundary. account: the reconciler flags a position the ledger cannot attribute to exactly one deployment. BMS: the board shows which machine holds the lease. operator: the hand-over is his click; a page if two writers were ever seen.
- **Components.** A2-067 (account-wide pause as a shared resource with a lock), A4-184 (PC and node run the same guard), A2-059, A4-170.
- **Engages.** B: account lease, orphan and double-owner check. Ledger: `account_writer_lease`, `lease_handover_only_when_flat`.
- **Correct outcome.** At most one node ever writes to an account; a hand-over never happens with positions open unless he forces it.
- **Sim proves.** A workflow test with two node instances against one paper account: no order leaves the node without the lease; the hand-over waits for flat.
- **Likely / bad.** L1 / S4.
- **Sources.** C23 (runs on the node and on his PC); memory ruling "PC is home, servers substitute"; G9 §1.1 (orphans); A2-067.
- **Maturity.** plausible.

### X4-scenarios-50. The disk fills and the journal cannot be written or read

- **What happens.** Logs and bars fill the VPS disk. The disk stand-down (2 GB, G9 §1.1) stops entries. But the journal that brake state is rebuilt from (scenario 48) is now the thing that cannot be written; a restart finds an unreadable journal and holds a repeated-fault stand-down at `all` (G9 §1.2). Open positions keep their broker-side stops.
- **Why.** Every brake that persists state depends on the disk; "unknown brake state" must mean no new entries, never "clean slate".
- **Levels.** unit: no entries while its brake journal is unwritable (fail closed, A4-058 declared fail mode). node: the disk stand-down; the journal write is checked, not fire-and-forget; log rotation keeps bars and logs under a budget. operator: ticket at 3 GB, page at 2 GB with positions open.
- **Components.** A2-102, A2-114, A4-058, A4-169.
- **Engages.** B: disk stand-down, journal-write check. Ledger: `disk_headroom_min` (v0), `journal_write_fail_mode`.
- **Correct outcome.** A full disk stops new risk and never erases brake state; exits still flow (the exit path must not depend on the journal write succeeding).
- **Sim proves.** A workflow test with a read-only journal path: entries refused, exits allowed, state intact after the disk is freed.
- **Likely / bad.** L2 / S2.
- **Sources.** G9 §1.1, §1.2; A4-058.
- **Maturity.** solid.

### X4-scenarios-51. The broker changes the instrument's spec (lot step, leverage, margin, digits, mode)

- **What happens.** The broker halves the leverage on indices before an election, changes gold's lot step, or switches the account from hedging to netting. The record is refreshed daily (G7 §4.2); between refreshes every size is computed on the old spec. The spec-change stand-down row exists and nothing raises it (G9 §1.1).
- **Why.** The plan already says a changed lot step, margin, digits or leverage stands that symbol's units down until his click (G7 §4.2); the code does not.
- **Levels.** trade: a size computed on a spec older than the venue's current spec is refused (the venue document is compared at order time, A4-179). unit: —. node: raise the spec-change stand-down on any difference between the stored record and the venue's `symbol_info` at reconnect and daily; the leverage cut is also a margin event (scenario 67). operator: the change card and his click (as planned).
- **Components.** A4-179, A2-102, A1-158, A1-162.
- **Engages.** B: spec-change stand-down. Ledger: `spec_change_fields`, `record_refresh_cadence_h`.
- **Correct outcome.** No order is sized on a stale spec; a spec change is a card, not a surprise at the fill.
- **Sim proves.** A contract test: change the lot step and leverage in the venue document; assert the stand-down fires before the next entry.
- **Likely / bad.** L2 (brokers change leverage around events) / S3 (a leverage cut with positions open is a margin call).
- **Sources.** G7 §4.2; G9 §1.1 (row only).
- **Maturity.** solid.

### X4-scenarios-52. The crypto venue: testnet against mainnet, the 5 % worst-price cap, mark against last, an outage that concentrates flow

- **What happens.** Hyperliquid testnet fills are not mainnet fills; the liquidation engine marks on an index price while the stop is on last; a market order's 5 % worst-price cap rejects an exit in a fast market (G9 §3.4), so "exits are never blocked" meets a venue that refuses the exit; a venue outage pushes forced flow onto the venue QMX uses.
- **Why.** Crypto venue rules are implementation risk a stop does not cover (A3-001 class notes); venue outages concentrate forced flow elsewhere (R4 technique 15, per-class scenarios).
- **Levels.** trade: the stop sits above the liquidation price (the node refuses a stop past liquidation, G11 §2.1) with a margin for mark-against-last divergence; an exit rejected by the worst-price cap is retried as a limit at the cap and then escalated (the protection escalation). unit: testnet results are labelled `venue:testnet` and never calibrate mainnet costs. BMS: a stricter exposure cap on crypto than the class share alone (R4 technique 6 per-class rules: no daily close resets the budget, weekend baselines, an independent account monitor). node: the venue's status endpoint and cross-venue basis as a venue-health tell. operator: page when an exit is rejected twice.
- **Components.** A2-262, A2-104, A3-235, A3-040, A3-058, A1-158, A4-179.
- **Engages.** B: liquidation-distance check, exit escalation, crypto exposure cap. Ledger: `liquidation_stop_check` (v0), `liquidation_buffer_pct`, `exit_cap_rejection_policy`, `cluster_exposure_cap` (v0).
- **Correct outcome.** A position is never liquidated before its stop; an exit the cap rejects fills by escalation within a bounded time; mainnet costs are calibrated on mainnet only.
- **Sim proves.** Perp venue model with funding, liquidation and a worst-price cap (R4 technique 21: the perpetual-futures ABM): loss distribution per stop-distance rule; exit completion time under the cap.
- **Likely / bad.** L3 / S3.
- **Sources.** G9 §3.4; G11 §2.1; R4 techniques 6, 15, 21; D39 (Hyperliquid second).
- **Maturity.** plausible (testnet only today).

## Family H. Units, software and agents

### X4-scenarios-53. A unit bug: the size is 10x, or the stop is on the wrong side

- **What happens.** A block update multiplies lots by contract size twice; or a sign error puts the stop above a long's entry. The checker's layer G drives the unit over a recorded slice (G8 §3.3) and may not hit the branch. Live, the first order carries a worst-case loss of 40 % of the account.
- **Why.** The order-boundary veto computes the worst-case loss on the actual order (A2-003); the stop-side check exists on the order path (G9 §1.1); the envelope must act "quietly inside the controls" (A2-024). A unit's logic is never trusted to size itself safely.
- **Levels.** trade: worst-case loss at the stop (plus the gap allowance) against the per-trade cap, checked by code outside the unit; a stop on the wrong side is refused (exists); a lot count above the unit's max lots is refused (A1-159). unit: —. book: —. account: the open-risk ceiling (A1-108) counts the new order; it is refused if it would breach. node: the guard is the home of these clamps; the unit cannot reach them (A2-017, invariant core). operator: a page on the first refusal of a new version, because a refusal means the version is wrong.
- **Components.** A2-003, A2-017, A2-024, A1-159, A1-108, A2-101, A4-091, A4-131.
- **Engages.** Clamps: per-trade cap, max lots, open-risk ceiling, stop side. Ledger: `max_lot` (v0), `max_position_size_lots` (v0), `open_risk_ceiling` (v0), `per_trade_worst_case_cap_r`.
- **Correct outcome.** No order from any unit, however broken, can risk more than the per-trade cap; the first refusal stops the version (one refusal of a new version is a defect, not noise).
- **Sim proves.** The dry chassis (A1-174) with planted faults (10x size, wrong stop side, missing stop): every planted order is refused; the clamp report names which clamp bound each size (A4-153).
- **Likely / bad.** L2 (every few versions) / S4 without clamps, S1 with them.
- **Sources.** G8 §3.3; G9 §1.1; A2-003; R4 technique 6 (Knight Capital; worst-case loss at the order boundary).
- **Maturity.** solid.

### X4-scenarios-54. A runaway unit: an order every tick

- **What happens.** A signal that never clears fires an entry on every tick; the position limit (one per market) holds the size, but the unit opens and closes two hundred times an hour, paying the spread each time. Or a stop-and-reverse loop. Knight Capital lost $460M in 45 minutes to dormant code (R4 technique 6).
- **Why.** A frequency jump is a behaviour trigger (R4 technique 6 trigger families); an order rate limit is a clamp no unit should be without; the session fill limit exists as a halt block and runs nowhere (G9 §1.3).
- **Levels.** unit: an order-rate clamp per unit (orders per minute and per session) at a multiple of the unit's own approved trade rate from its baseline card (`trade_rate`, G9 §7.1); a jump beyond it stops entries and journals a risk stop. book: a book-level order-rate ceiling, lower than the sum of its units'. node: the clamp is in the guard; the venue's own rate limit is read as a fault, not retried. operator: page.
- **Components.** A2-109, A1-159, A2-003, A4-091, A3-134 (news-collision rate check is the same shape), A2-166 (trade-rate drift).
- **Engages.** Clamp: order rate. B: session fill limit (v0 `session_fill_limit`), trade-rate band (v0 `trade_rate_band`). Ledger: `order_rate_limit_per_min`, `session_fill_limit` (v0), `trade_rate_band` (v0).
- **Correct outcome.** A unit cannot trade faster than a multiple of its approved rate; a runaway costs minutes of spread, not an account.
- **Sim proves.** The dry chassis with a never-clearing signal: orders sent before the clamp fires; cost in R of the burst.
- **Likely / bad.** L2 / S3.
- **Sources.** R4 technique 6; G9 §1.3, §7.1; A2-109.
- **Maturity.** solid.

### X4-scenarios-55. An upgrade lands mid-day with positions open

- **What happens.** A new unit version (or a new profile version, X1) is deployed at 11:00 with a position open from the old version. The position belongs to the version that opened it until flat (G7 §5.3), but the snapshot from another fingerprint starts cold (G8 §3.7): the sizer's memory, the day's counters and the bench vanish; the new version's first entry is sized as if the day were clean. A rollout with no rollback is the Knight pattern again (A4-034).
- **Why.** Deployment and rollback controls matter as much as strategy logic (A4-034); a world or version switch resets things that should not reset (scenario 30).
- **Levels.** unit: a version switch happens only when the unit is flat and at a boundary unless he forces it (`switch_only_when_flat`); brake state carries across versions as a starting assignment (scenario 48); a new version starts at the first size level (slow start, A5-127) with a canary against the old version running on the paper twin (A4-025, A4-026). book: —. node: the deployment keeps the old version's compiled unit until flat; the rollback is a one-click return to the previous pin (A4-022). operator: the click; the rollback button.
- **Components.** A4-022, A4-023, A4-024, A4-025, A4-026, A4-034, A4-040, A4-041, A5-127, A2-124.
- **Engages.** B: switch-only-when-flat, slow start after a version change. Ledger: `switch_only_when_flat`, `world_switch_reset_rule`, `size_level_now`, `canary_against_baseline`.
- **Correct outcome.** No version change ever clears a brake or sizes from a clean slate; a bad version is one click from gone.
- **Sim proves.** A workflow test: deploy a new version mid-day; assert counters and bench carry, the first entry is at level 1, and the rollback restores the old pin.
- **Likely / bad.** L4 (weekly, once agents produce versions) / S2-S3.
- **Sources.** G7 §5.3; G8 §3.6, §3.7; R7 §4 (Argo, Flagger, Kayenta); A4-034.
- **Maturity.** solid.

### X4-scenarios-56. A blank or placeholder number reaches live

- **What happens.** A template ships with `risk_fraction` as a placeholder (origin `placeholder`, G8 §1.2) and a halt list empty. Promote needs his tick on placeholders (G9 §3.2) and he ticks. The unit trades live with a size nobody derived and no brake. The old system's unfilled thresholds (D30) by another door.
- **Why.** No key setting may be left blank (D30); a blank value blocks live (A4-101, Gen 3 `value_status_required`); every number needs a derivation (D29).
- **Levels.** unit: a placeholder on a risk number refuses live, not "needs a tick"; a halt list that is empty is a checker error for live, a warning for paper; the derivation fallback ladder (A4-055) fills every number from defaults, class and bucket so nothing is blank by construction. node: the placeholder labels that ride every order (A4-085) are a refusal reason in the live world. operator: the tick is removed for risk numbers; the card says "derived from X" instead.
- **Components.** A4-055, A4-085, A4-101, A4-031, A4-054, A1-063.
- **Engages.** Clamp: placeholder refusal in live. Ledger: `placeholder_blocks_live`, `derivation_fallback_order`.
- **Correct outcome.** A unit with any undetermined risk number cannot bind live; every live number has a derivation receipt.
- **Sim proves.** A contract test: a unit with a placeholder sizer fraction is refused by promote to live and accepted to paper with a warning.
- **Likely / bad.** L3 (every template start) / S3.
- **Sources.** D29, D30, D31; G8 §1.2; G9 §3.2; A4-101.
- **Maturity.** solid.

### X4-scenarios-57. An agent proposes something wrong

- **What happens.** The weekly market-map agent proposes "isolate FX for a week" on a misread; the decay agent proposes a size increase for a unit that just lost (the get-even pattern, A5-085); a tuning agent proposes a stop twice as wide "to reduce stop-outs" (which doubles the loss per full stop). Today every proposal is a card for his click (G10 §2.4), and he is not a trader.
- **Why.** Agents never touch money, only he promotes (brief); but a wrong card he clicks is money. The defences are in the card, not in him: bounds, direction, effect-binding, and a checker that does not see the proposer's story (A5-051).
- **Levels.** unit: the proposal door accepts only typed, bounded, expiring, de-risking proposals by default (A2-018, A4-104); a size increase, a wider stop or a loosened brake is a different proposal class with a higher evidence bar (A5-077) and a cooling time after any loss (A5-085). book: —. BMS: an isolation proposal needs the two-tell evidence attached (scenario 09) and a TTL; the card shows what the proposal would have cost on the last 30 days (A4-202, the trip tax). node: nothing an agent writes reaches the guard without his signature and the effect-bound card (A5-055). operator: the click, with the card rendered from the canonical effect, and a "what this costs if wrong" line.
- **Components.** A2-018, A4-104, A4-112, A5-051, A5-054, A5-055, A5-077, A5-085, A4-202, A2-133.
- **Engages.** B: proposal bounds, loosening evidence bar, get-even cooling. Ledger: `agent_proposal_bounds`, `loosening_evidence_bar`, `get_even_cooling_min`, `proposal_ttl_h`.
- **Correct outcome.** A wrong de-risking proposal costs missed trades at most; a wrong loosening proposal cannot pass without evidence above a bar; he never sees a card without its cost-if-wrong.
- **Sim proves.** A workflow test: three wrong proposals of each class; assert the de-risking ones apply with a TTL and the loosening ones are refused for evidence; replay the trip tax of a wrong isolation.
- **Likely / bad.** L4 (agents are wrong often) / S1 for de-risking, S3 for loosening.
- **Sources.** D41, D42, D43; G10 §2.4; R3 §2.3 (adaptive allocation's faults); A5-085; handoff boundary (agents never touch money).
- **Maturity.** solid.

### X4-scenarios-58. The news an agent reads is fake, stale or injected

- **What happens.** A news agent reads a fabricated headline (a fake central-bank statement), or a page carrying text aimed at the agent ("ignore your limits"), or a real headline from last year resurfaced. It emits an event record that would widen a window or trip an isolation.
- **Why.** Agents' outputs are data, never instructions (brief); fabricated news needs provenance, a cap on any single item's effect and corroboration (A4-108, A3-138); a news record separates event time from availability time (A4-107).
- **Levels.** BMS: a news event record from an agent may only de-risk, expires, needs two sources, and its effect is capped (one feed counted as one risk); an unverifiable item raises a short caution, never an isolation; the scheduled calendar and the market tells (scenario 16) outrank it. node: nothing from the news path reaches the kill switch. operator: the red-team battery (A4-138) runs against the information path before any news agent is wired.
- **Components.** A3-137, A3-138, A3-139, A4-107, A4-108, A4-138, A4-141.
- **Engages.** B: provenance gate, single-item cap, de-risk-only channel. Ledger: `news_item_effect_cap`, `news_corroboration_min`, `news_agent_de_risk_only`.
- **Correct outcome.** A fake headline costs at most a short caution's missed entries; no agent text can widen risk or lower a kill level.
- **Sim proves.** A red-team workflow test: fake, stale and injected items through the news path; assert the effects are capped and de-risking only.
- **Likely / bad.** L3 / S1 (by construction, if the channel is de-risk only).
- **Sources.** R4 technique 9 (news agents), A4-108, A4-138; brief instruction-source rules.
- **Maturity.** solid.

### X4-scenarios-59. Two controls disagree on the same tick

- **What happens.** House money says 1.5x; the class caution says half; the unit's own bench says none; the kill switch at `deployment` says YELLOW. Or a halt says `flatten` while an isolation says `no new entries`. April combined by product (1.5 x 0.5 = 0.75, G3 §4.3); Gen 3 had a rank table (A4-103); the shipped stack has a fixed check order for entry refusals (G9 §1.1) and nothing for size.
- **Why.** "Many caps, smallest wins, each with a reason" (A1-122); "any brake blocks every raise" (A5-138); one central controller reconciles simultaneous triggers (A2-020).
- **Levels.** trade: permission first (any refusal wins), then exposure (flatten beats reduce beats hold), then size (smallest cap wins, accelerators apply only if no brake is active), and the receipt names the binding control (A4-153). unit: —. book and BMS: the same rank at every scope; a wider scope's brake outranks a narrower scope's accelerator. node: one guard module applies the rank (A4-091). operator: the receipt shows "size bound by: class caution".
- **Components.** A1-122, A2-020, A4-103, A4-153, A5-138, A4-093, A2-004.
- **Engages.** Rank table. Ledger: `control_rank_table` (v0), `binding_control_on_receipt`.
- **Correct outcome.** The same inputs always give the same size and permission; no product of multipliers; every receipt names the control that bound it.
- **Sim proves.** A property test over random control states: the rank gives a unique answer; an accelerator never raises size while any brake is active.
- **Likely / bad.** L5 (every tick with more than one control) / S2 (a product of multipliers is how April got 2.25x house money, G3 §3).
- **Sources.** G3 §3, §4.3; G9 §1.1; A4-103; R9 §3.4.
- **Maturity.** solid.

## Family I. Edge and regime

### X4-scenarios-60. The edge fades slowly (decay, the chronic case)

- **What happens.** A scalper that paid +0.10R per trade in its holdout pays +0.04R over its first 400 live trades, then +0.01R. No bad day; the cone still contains the path for a while (R2 §2.2: a fixed band fires late for slow decay). The shipped decay check compares the last 20 trades with the unit's own past and lands a tighten-only card (G10 §5.4).
- **Why.** His "size down, but not quickly" (A25) and "the circuit breaker caught alpha decay" (A26). No generation sized down gradually on drift evidence (G10 §5.6). Count brakes cannot see this; a CUSUM needs about 240 trades to flag +0.1R → 0 (R2 §2.2); inputs (costs, fills, trade rate) move first (R2 §2.5).
- **Levels.** trade: —. unit: three detectors with three jobs (A2-172): inputs first (cost, fills, trade rate, holding time, A2-166), then a CUSUM on R against the holdout baseline (A2-149), then an e-detector for the economic verdict (A2-152); three zones (A2-196): green carry on, yellow hold the size and gather evidence, red step one size level down (A2-190); the demotion ladder green, yellow, orange (no new entries), red (paper until re-proven) (A2-167); a step up again only on an e-value plus a minimum time (A2-221), never on a win streak. book: —. methodology: the pooled stream of the logic family (scenario 04) flags the family days before any unit. BMS: the unit's share steps with its level. account: —. node: —. operator: a yellow is a ticket with the three detectors' states; a red is a card.
- **Components.** A2-149, A2-152, A2-166, A2-167, A2-172, A2-174, A2-175, A2-190, A2-196, A2-221, A5-012, A5-146, A3-063.
- **Engages.** B: input-first drift, CUSUM, e-detector, three zones, size-level step-down. A: locked while yellow or red. Ledger: `drift_state` (v0), `cusum_limit` (v0), `cost_drift_multiple` (v0), `trade_rate_band` (v0), `drift_size_down_step` (v0), `size_level_now`, `edge_zone`, `e_value_reloosen_bar`.
- **Per class and style.** Scalpers: inputs decay first and fastest (cost is the master state). Intraday and swing: too few trades for a CUSUM in weeks; the drawdown rule earns its keep only when skill decays (R9 §4.1, Man Group), so a style-aware worry line (A2-014) is the slow detector there.
- **Correct outcome.** Size steps down in one level at a planned look, never on one day; the cause is named (inputs, edge, regime) before any demotion; a dead edge is paper within the planned trade count; a live edge is never pulled for noise.
- **Sim proves.** The X5 group-sequential plan on a linearly decaying edge: cushion lost before each zone change under daily 95 % checks, planned looks and e-detectors; false-red rate on a stable unit over 2,000 trades.
- **Likely / bad.** L3 (every edge decays eventually) / S3 (the slow bleed, scenario 07, by another route).
- **Sources.** A25, A26; R2 §2.1-2.5; R3 §1.2, §2.2; G10 §5; R9 §4.1; X5 draft section C.
- **Maturity.** solid.

### X4-scenarios-61. Regime change: the market stops doing what the unit needs

- **What happens.** A mean-reversion scalper placed on a ranging index CFD meets a trend day: every fade is run over. The MIS reading flips its word (Hurst, variance ratio) a session later; the unit's edge did not decay, its placement did.
- **Why.** System 1 over System 2 (D3): a logic placed where the market suits it; placement is the shared job (D2). The MIS amplifies and never switches (A3-184); regimes cut gross, never re-weight (A3-045).
- **Levels.** unit: a context need (A3-183) that blocks new entries when the reading word is against the unit's logic, with the stale-board fallback that today trades everything (G9 §4.3) replaced by "no new entries on a stale board for a unit that declared the need" (fail closed for declared needs, fail open for the rest). book: —. methodology: "this logic is against its regime on K markets" is a methodology tell, separate from decay (A3-123 keeps three signals apart). BMS: the class regime brake (A3-044, sticky jump model) cuts the class's gross, never re-weights units; placement (C-22) moves the unit's admitted markets at a boundary. node: the board relay, wired. operator: sees "placed against regime" on the unit card.
- **Components.** A3-043, A3-044, A3-045, A3-123, A3-182, A3-183, A3-184, A3-189, A3-190, A2-081, A2-110.
- **Engages.** B: context-need block, class regime brake. Ledger: `board_stale_after` (v0), `context_need_fail_mode`, `class_regime_brake_state`.
- **Per class.** FX ranges by session; indices trend at the cash open and range into the close; crypto flips with funding; energy trends on inventory surprises. The regime label is per class and per session, never one word for the book.
- **Correct outcome.** A unit against its regime stops entering before it loses a day's budget; nothing calls it decay; it resumes when the word turns.
- **Sim proves.** Replay on labelled regime history: R per entry with the context need on and off; false blocks on calm history; the regime brake against a random brake of the same rate (R5 23482 design, A2-135).
- **Likely / bad.** L4 / S2.
- **Sources.** D1, D2, D3, D6; G9 §4; G7 §2; A3-044; R5 (23482).
- **Maturity.** solid.

### X4-scenarios-62. A losing streak with a real edge (the normal pain)

- **What happens.** A 55 % scalper loses 8 in a row. In 200 trades that happens 17 % of the time (R2 §2.1); over 2,000 trades a 27R drawdown is the median (R2 §2.1). Every count brake in history fires: "2 full stops" on 79 % of days at 10 trades (R2 §3.2), "3 in a row" on 41 % (R9 §4.1). The unit is benched for being normal.
- **Why.** His A6 ("brake at about three or on a pattern") and A28 ("just by chance does not hold"; brakes must count fast invalidation) and C33 (a sweet spot per level). "Don't lean on luck" means the brake must know the unit's own distribution.
- **Levels.** trade: a fast-invalidation cut counts by its size in money, a breakeven at its cost (A5-145, two ledgers). unit: the fast brake is in money at the unit's own k-th percentile of daily P&L for its trade count (A5-144: −4R at 4 trades, −6R at 10, −8R at 16, −10R at 40), not a count; a count brake, if kept, is scaled to the trade count and win rate (A2-078) with a minimum number of events before it may fire (A2-031); a bench carries a minimum rest across the day boundary (A2-116). book: the book's day budget reads the unit's loss once. methodology: —. BMS: —. operator: nothing; the screen shows "normal drawdown: 11R of a 27R median".
- **Components.** A2-031, A2-078, A2-116, A5-144, A5-145, A2-177 ("bad day" defined from the card's daily distribution), A2-014, A1-051.
- **Engages.** B: percentile money brake, scaled count brake, minimum events, bench rest. Ledger: `unit_daily_loss_limit` (v0, set at the percentile), `loss_counting_rule` (v0), `circuit_breaker_strikes` (v0, scaled), `min_events_before_signal`, `bench_min_rest`, `bad_day_percentile`.
- **Per style.** A 1-trade-a-day ORB: "2 full stops" is rare and a fair alarm. A 40-trade scalper: only money at its own percentile keeps the false-fire rate steady. A fast-invalidation unit trips count brakes more often than a plain one with the same edge (60 % against 41 %, R9 §4.1): the count brake punishes the good habit.
- **Correct outcome.** A healthy unit's brakes fire on about k % of days whatever its frequency; a streak inside its distribution costs nothing but the losses; the streak is logged as decay evidence (fire density) without stopping the unit.
- **Sim proves.** The R9 script extended: fire rate per brake design for healthy units at 1, 4, 10, 16 and 40 trades a day, with and without fast invalidation and scratches; cushion lost on the true-decay path under each design; the random-control test (A2-135).
- **Likely / bad.** L5 / S1 if the brake is right, S2 in growth terms if it is wrong (benched days are the sitting duck).
- **Sources.** A6, A28, C31, C33; R2 §2.1, §3.2; R9 §4.1-4.3; STATE item 10; G10 §1.
- **Maturity.** solid.

### X4-scenarios-63. A winning streak with the accelerators on

- **What happens.** A unit wins 9 of 10; house money triggers; the tier ladder steps up; a pressing rule adds size. The tenth trade is the reversal, at 1.8x size. Win streaks say little about the edge of a high-win-rate unit (R2 §2.4: 10 straight wins at 70 % with +0.05R edge happens 2.8 % of the time); with independent trades no accelerator beats a fixed size (R9 short answer 4).
- **Why.** He keeps house money and the accelerator idea (A21), brakes first (C19). The accelerator must not re-raise into a trip (R9 §3.4).
- **Levels.** unit: house money funds extra risk only from realised profit above the day anchor, capped at a share of that profit (A5-116, A5-118); the tier ladder steps up only after a dwell of active days or trades and down the same day (A5-123); a persistence press is switched on only after the unit's own block-persistence test passes (A5-121, A5-131); a memory ceiling after any trip (A5-134); settle before the next change (A5-137); a consistency rule: the best day may not exceed half of total profit (A2-226). book: house money is capped at book level (scenario 05). BMS: no accelerator while any caution or isolation is on (A5-138). operator: sees "size 1.4x: house money, funded by +$18 today".
- **Components.** A5-116, A5-118, A5-119, A5-121, A5-123, A5-131, A5-133, A5-134, A5-137, A5-138, A2-226, A1-068.
- **Engages.** A: house money (windowed, capped), tier ladder, persistence press (gated). B: memory ceiling, settling, consistency rule. Ledger: `house_money_winnings_share` (v0), `house_money_scope` (v0), `house_money_lockout`, `tier_dwell_trades`, `persistence_block_test_pass`, `trip_memory_ceiling`, `settling_trades_after_change`, `best_day_share_max`.
- **Correct outcome.** The reversal after a streak costs no more than one baseline trade plus the profit that funded the extra size; growth per unit of risk is not below a fixed size on independent trades and above it where persistence is real.
- **Sim proves.** The R9 accelerator script with correlated units and a regime: growth per unit risk and P(drawdown > 25 %) for naive house money, windowed house money, the tier ladder and the AIMD day pair (A5-133); the "re-raise into a trip" count per design.
- **Likely / bad.** L4 / S2-S3.
- **Sources.** A21, C19; R9 §0.4, §1, §3; R2 §2.4; G3 §4.2-4.3.
- **Maturity.** solid.

### X4-scenarios-64. Many units on one signal, across instruments and sessions (crowding inside QMX, the family case)

- **What happens.** The ORB family runs on every open (D11, "brilliant"): Tokyo, London, New York, on indices and FX. Six units take the London open breakout on EURUSD, GBPUSD, the DAX and the FTSE in the same minute. Across sessions the bets are near independent; within one open they are one bet with six costs. Scenario 03 is the same-minute case; this is the family across the day.
- **Why.** Size the family of session-open units as one (A3-020, A1-135); breadth through session opens is the lever, correlation its limit (R2 §4.2); the unit-level agreement report (A5-064) is the crowding diagnostic.
- **Levels.** unit: —. book: —. methodology: the ORB family carries one same-bet budget per open (a bet key = logic + open + driver); within one open the family's total is capped and split; across opens each is its own bet; N_eff per family on the screen (A3-163). BMS: an agreement report across QMX's own units (A5-064): which units take the same side on the same driver in the same minute, how often, and the loss when they do (co-loss breadth, A3-158). operator: sees "ORB family: 6 units, 1.4 effective bets at the London open, 4.1 over the day".
- **Components.** A1-115, A1-135, A3-020, A3-032, A3-158, A3-163, A5-001, A5-002, A5-064, A2-188.
- **Engages.** B: family same-bet budget per open. Ledger: `same_bet_exposure_cap`, `bet_key_rule`, `effective_independent_bets` (v0), `methodology_tag`, `co_loss_breadth`.
- **Correct outcome.** The family's risk per open equals one well-sized bet; the frequency benefit across opens and markets is kept; the agreement report is flat on a diversified book and spikes before a crowded loss.
- **Sim proves.** Six ORB units on history with and without the family budget: growth and floor touches against the independent case; the agreement report's lead over the co-loss.
- **Likely / bad.** L5 / S3.
- **Sources.** D11, C29; R2 §4.2-4.3; A3-020; A5-064.
- **Maturity.** solid.

### X4-scenarios-65. The August 2007-style unwind: a family like ours deleverages, our stops fire into the bottom

- **What happens.** A large player unwinds a family of strategies like one QMX runs (mean-reversion on indices, a carry basket). Prices move k sigma against the family for three days as the unwind feeds on itself; every stop and deleveraging rule in the family fires on the same days and adds to the move; the rebound comes on day four (Khandani and Lo, R8 §3.5). QMX's own brakes sell the bottom.
- **Why.** A multi-strategy book's de-risking rules are themselves a source of correlated loss (R8 §3.5); the stress engine must simulate the book's own brakes inside the path, not only the price path (R8 §3.5, A5-092). Stops help only under momentum, not under mean reversion (R8 Kaminski-Lo).
- **Levels.** trade: a stop is still a stop; the question is what re-enters. unit: no re-entry into the same bet within the cooling time after a fill through the stop (A2-117). book: the event window (idea 91) counts the three days as one event for the budget; a book-level de-risk is staged (shed by priority class, A2-035), never all at once. methodology: the family's pooled stream flags "losing everywhere" within a day (scenario 04) but the action is "no new entries", not "flatten", because the family's own flatten is the mechanism of the loss. BMS: a disturbance reserve after the shock (A3-160) so the rebound can be traded small; the crowding scenario is in the standing scenario set. operator: a ticket on day one, a page only if the budget is gone.
- **Components.** A5-092, A3-165, A3-160, A2-035, A2-117, A2-249, A3-146, A3-147, A3-158.
- **Engages.** B: event window, staged de-risk, re-entry cooling, disturbance reserve. Ledger: `loss_event_window` (v0), `reentry_cooling_after_gap`, `shed_priority_class`, `disturbance_reserve_share`.
- **Correct outcome.** The family loses its event allowance, not three days of budgets; nothing flattens into the bottom by rule; the rebound is traded at a fraction of size.
- **Sim proves.** The k-sigma three-day unwind with a rebound, with QMX's brakes inside the path: loss under hold-to-stop, staged de-risk and instant flatten; the share of the rebound caught.
- **Likely / bad.** L1-L2 / S3-S4.
- **Sources.** R8 §3.5; A5-092; R4 technique 15 (FARSIGHT amplification); R8 Kaminski-Lo.
- **Maturity.** plausible.

### X4-scenarios-66. The backtest was overfit, and the twin case: results too good

- **What happens.** A unit with a Sharpe of 2 in-sample and 100 tries behind it goes to paper, passes 30 trades by luck (a 14 % false pass under daily 95 % checks, R3 §1.3), and goes live with no edge at all. Ten such units at full size touch the floor in 68 % of runs (STATE item 10, no edge). The twin case: a unit's first live week prints a daily Sharpe above 3 because of a lookahead bug in a new block; the accelerators fire on it.
- **Why.** Backtests overstate (R3 §1.1); the best of 100 tries sits 2.5 standard errors up (R3 §1.1); luck is not a variable (D18) so the plan must not need it. An upside alarm (A2-176) is as necessary as a downside one.
- **Levels.** unit: the verification plan priced in trades at the deflated holdout edge (A2-181, A2-187), planned looks with a non-binding futility rule (A2-184), the smallest live size while proof is pending (A2-218); the upside alarm holds the verdict and the accelerators when results sit above the card's cone (A2-176; the shipped gate already holds a daily Sharpe above 2 for a lookahead audit, G7 §1.4). book: —. BMS: the family's try count feeds the deflated Sharpe (A2-179); ten unproved units never run at full size together (A1-087: splitting is insurance against a wrong edge). operator: the card shows "proof pending, 212 of 610 trades" (X5).
- **Components.** A2-176, A2-179, A2-180, A2-181, A2-184, A2-187, A2-218, A1-087, A2-202, A2-146.
- **Engages.** B: proof-pending size level, upside alarm, futility stop. Ledger: `verification_trades_needed` (v0), `deflated_sharpe_min` (v0), `daily_sharpe_audit_trigger` (v0), `upside_alarm_cone_percentile`, `size_level_now`.
- **Correct outcome.** A no-edge unit costs at most its level-1 size times the trades to futility; a lookahead bug is caught by the upside alarm before any accelerator pays it; ten unproved units cannot be ten full-size bets.
- **Sim proves.** The frequency-flaw sim (`sims/frequency_flaw_and_brakes.py`) with the size ladder on: floor touches at no edge and half edge for ten units at level 1 against full size; the upside alarm's detection time on a planted lookahead.
- **Likely / bad.** L4 (most candidates have no edge) / S4 at full size, S1 at level 1.
- **Sources.** D18, D20; R3 §1; STATE items 10 and 16; G7 §1.4; X5 draft.
- **Maturity.** solid.

## Family J. Account and capital

### X4-scenarios-67. The broker cuts leverage overnight (or raises margin)

- **What happens.** Before an election the broker moves indices from 20:1 to 5:1 and gold from 20:1 to 10:1. Margin used on the open positions doubles; free margin goes to zero; the next entry is refused by the broker for margin, or worse, the broker's own margin close-out (50 % of required margin under ESMA rules, R8 §4.6) starts closing positions it chooses.
- **Why.** Margin is its own limit, apart from risk (A1-158); "an R-sized position may exceed what the account can margin" (G4 §3.7); a second unit can use up the margin the first assumed (G6 §3.9). Nothing in any generation counted margin across units.
- **Levels.** trade: the margin for this order at the current leverage tier, plus the margin already used, against free margin with a reserve; refused if it would pass the reserve (A1-158). unit: —. book: —. BMS: a margin headroom rule across all units on the account: total margin used may not exceed a share of equity, so a leverage cut of 2x cannot trigger the broker's close-out; a leverage change is read from the record refresh and the spec-change stand-down (scenario 51); on a cut the BMS reduces gross by its own rule (which positions, in what order: by stressed contribution, A5-041) before the broker does it for us. account: margin used and free margin are refreshed with equity (G9 §3.3: today cTrader equity is read once at sign-in). operator: a page on a leverage cut with positions open.
- **Components.** A1-158, A5-096, A5-041, A1-108, A2-105, A4-179, A3-001.
- **Engages.** Clamp: margin headroom. B: spec-change stand-down, BMS de-gross by stressed contribution. Ledger: `margin_used` (v0), `leverage` (v0), `margin_headroom_min_share`, `leverage_cut_degross_rule`.
- **Per class.** ESMA-style caps differ by class (30:1 FX majors, 20:1 gold and major indices, 10:1 other commodities, 5:1 stocks, 2:1 crypto, R3 §4.1); the cap is a hard ceiling on any size where it applies (A5-096). Futures: margin rises with volatility by exchange rule.
- **Correct outcome.** A 2x leverage cut never triggers the broker's close-out; QMX reduces its own gross, by its own order, before the broker chooses.
- **Sim proves.** Replay with a leverage cut injected at 03:00 on a book at 60 % margin use: positions closed by the broker's rule against positions reduced by QMX's rule; loss under each.
- **Likely / bad.** L2 (around elections and crises) / S4 (a broker close-out picks the worst positions at the worst time).
- **Sources.** G4 §3.7; G6 §3.9; R3 §4.1; R8 §4.6; A1-158.
- **Maturity.** solid.

### X4-scenarios-68. The margin close-out with many small positions (the broker flattens, not us)

- **What happens.** Twelve positions across six units, each tiny, together use 80 % of margin after a gap. Equity falls below the close-out level; the broker closes positions in its own order until margin is restored. The book's "exits are never blocked" rule is kept, but the exits were not ours and came at the worst prices.
- **Why.** Open risk at the stop is not the same as margin at risk (G11 §2.1: April's measure was risk at the stop); a book can look safe in R and be one gap from a margin close-out.
- **Levels.** BMS: two ceilings read together: open risk at the stop (A1-108, the heat cap) and margin used as a share of equity; the lower binding wins; a gap allowance per class is in the margin headroom too. account: the close-out level from the record (`liquidation_rule`, G7 §4.2) with a buffer; the BMS acts at the buffer, the broker at the level. node: equity and margin refreshed on every fill and on a timer. operator: page at the buffer.
- **Components.** A1-108, A1-158, A3-162, A2-096 (the kill line on marked equity is the same shape), A4-152 (RiskState row).
- **Engages.** Clamp: margin headroom. B: kill line (marked) as the last stop above the close-out. Ledger: `open_risk_at_stop` (v0), `margin_headroom_min_share`, `kill_line_floor` (v0), `equity_refresh_s`.
- **Correct outcome.** The broker's close-out is never reached; QMX's own kill line (marked) acts first, by its own order, with its own exits.
- **Sim proves.** A gap scenario on a book at 80 % margin use: distance to close-out under each headroom rule; the kill line's trip before the broker's.
- **Likely / bad.** L2 / S4.
- **Sources.** G11 §2.1; G7 §4.2; G4 §3.7; A1-108.
- **Maturity.** solid.

### X4-scenarios-69. The seed near the floor

- **What happens.** Equity is $330 with a $300 floor and a $20 buffer. The cushion is $10. Cushion-proportional sizing (A1-037, A1-036) gives a size below the minimum lot on everything but FX micro lots. A unit that trades is risking the floor; a unit that does not is the sitting duck. His rule: the floor is almost never touched (C10) and after the cushion hits zero "how does the next day start" (C12) is open.
- **Why.** This is the edge of the whole design: the floor is user-set, the cushion is where accelerators and brakes live, and the maths of sizing from the cushion goes to zero at the floor. Every brake is on, by construction, and the question is what "on" means at $10 of cushion.
- **Levels.** trade: the min-lot skip (scenario 41) makes most instruments untradable; only instruments whose minimum lot's worst case fits the cushion are feasible (A3-001 feasible size). unit: size at the smallest feasible level or skip; no accelerator (the budget-burn permit is exhausted, A5-141). book: the day budget is the cushion, not a share of equity. BMS: the floor-hit action is declared (`floor_hit_action`): stop the pot and wait for a re-seed (the lead's answer), or trade one feasible FX micro unit at level 1 until the cushion rebuilds to a bar (his "give units $100 and let them grow", C11); a re-seed is his signed act (G6 §3.8) and is priced like reinsurance reinstatement, never free (A5-130). account: marked equity against the floor on every fill. operator: the page he said he wants only for a black swan or a real failure (C10): being here is one.
- **Components.** A1-036, A1-037, A1-038, A1-136, A3-001, A3-002, A5-010, A5-130, A5-141, A2-132, A1-078.
- **Engages.** Clamp: floor, min lot. B: buffer before the floor, budget-burn permit (exhausted). Ledger: `portfolio_floor` (v0), `bms_buffer_before_floor` (v0), `floor_touch_tolerance` (v0), `floor_hit_action`, `class_feasibility_flag`, `reseed_rule`.
- **Correct outcome.** Below the buffer nothing trades that can touch the floor; what trades is the smallest feasible thing; the floor is crossed only by a gap, never by a sized trade; the restart path is declared and his.
- **Sim proves.** Monte Carlo from $330 with a $300 floor: floor touches under "stop the pot", "one micro unit at level 1" and "trade as usual"; time to rebuild to $400 under each; gap-only floor breaches.
- **Likely / bad.** L2 on $500 (one bad month gets here) / S4 by definition.
- **Sources.** C10, C11, C12, C13; G6 §3.8; R9 §0.4 (cushion rule); A1-037; the brief ("sitting duck").
- **Maturity.** solid.

### X4-scenarios-70. The cushion after a big win: the ladder accelerates, and the sweep question

- **What happens.** The book doubles in a month. With a fixed dollar floor the share of equity risked per R rises from 8.6 % at seed to 12 % at the cap (G6 §3.11: the GitBook ladder was an accelerator); without a cap or sweep the share keeps climbing toward 14.3 %. Nothing in the current docs sweeps automatically (G6 §3.8). The next drawdown is at the biggest size the book has ever run.
- **Why.** The anchor decides whether a cushion rule is an accelerator (R9 §0.4): a fixed floor presses, a trailing anchor brakes. His open question: does the sweep cap return (C12, B10)?
- **Levels.** unit: —. book: a rising floor (v0 `rising_floor_fraction`) that follows the high-water mark by a share, so the cushion grows slower than equity (A1-037, Grossman-Zhou); the ladder's share per R is capped (A1-042 names the trap). BMS: the sweep is a BMS act at a high-water mark (A1-076, R2 §5): a share of profit above the mark leaves the risk zone, the rest compounds; the sweep never takes the cushion below the buffer (the Topstep lesson, A2-077); the cap and sweep are declared per book (C12 stays his). operator: the sweep is a signed act (G6 §3.8); a proposal card at the mark.
- **Components.** A1-037, A1-042, A1-075, A1-076, A1-077, A2-077, A5-010, A1-079.
- **Engages.** A: cushion ladder (capped). B: rising floor, best-day consistency rule. Ledger: `rising_floor_fraction` (v0), `high_water_mark_equity` (v0), `sweep_cap_equity` (v0), `equity_share_per_r` (v0), `share_per_r_cap`, `sweep_share_above_hwm`.
- **Correct outcome.** The share of equity risked per trade is bounded above; the drawdown after a run of wins is bounded in cushion terms; profit leaves the risk zone by his rule, not by the next loss.
- **Sim proves.** Equity paths through a 2x run then a 30 % drawdown: fixed floor, rising floor, capped share, sweep at the mark; growth and maximum drawdown per rule.
- **Likely / bad.** L3 / S3.
- **Sources.** B10, C12, C22; G6 §3.8, §3.11; R2 §5; R9 §0.4; A1-042.
- **Maturity.** solid.

### X4-scenarios-71. The restart after a day budget hit

- **What happens.** The book hits its day budget at 11:00. April and July reset at the day boundary by themselves (G10 §1); the unit build makes every risk stop wait for his click (G10 §1.6). Both are wrong for a 24-hour, many-class book: the automatic reset re-arms at 00:00 into the same conditions (scenario 29); the click wakes him for a routine event.
- **Why.** "How does the next day start" (C12); the bench needs its own row in the stand-down table (G10 §7.9); retry then lockout (R3 §3.1): a few automatic retries, then a human.
- **Levels.** unit: a benched unit returns by itself after its minimum rest and a clean condition check (tells clear, no isolation), at level 1 (A5-127 slow start), with no accelerator; the second bench in a rolling window lengthens the rest; the third in the window locks out for his click (A2-022, recloser). book: the day budget renews at the declared boundary; a renewed budget does not clear a locked unit. BMS: the BMS budget renews the same way; a BMS breaker trip (scenario 14) is the one that waits for him. operator: a ticket per bench; a page only on lockout.
- **Components.** A2-022, A2-007 (state-based re-enable, not a timer), A2-116, A2-064, A5-127, A2-103, A2-058.
- **Engages.** B: bench with rest, retry-then-lockout, slow start on return. Ledger: `bench_min_rest`, `bench_retry_max_in_window`, `risk_stop_resume_rule` (v0), `size_level_now`.
- **Correct outcome.** A routine budget hit costs the rest of the day and nothing of his sleep; a repeated hit escalates to him; a return is never at full size into the same conditions.
- **Sim proves.** Clustered bad days on history: re-arms and losses under calendar reset, click-only, and retry-then-lockout; the count of pages per month under each.
- **Likely / bad.** L4 / S2.
- **Sources.** C12; G10 §1, §7.9; R3 §3.1; A2-022; scenario 29.
- **Maturity.** solid.

### X4-scenarios-72. The sweep that takes the cushion (payout, withdrawal, subscription)

- **What happens.** He withdraws $150 of profit for subscriptions. The account is $500 again, but the units' anchors, the high-water mark and the book budgets still read the $650 state; or they reset and the unit that was in house money is now sized off a cushion that left. Topstep's rule: after a payout the loss limit resets to $0, so the remaining balance is the whole cushion (R2 §5).
- **Why.** A sweep is a banker act that resets what the cushion rules feed on (R9 §0.2 definitions: banker and re-seed); it never acts on the next trade but changes every cushion-based rule.
- **Levels.** unit: house money and the day ledger re-anchor at the sweep (the sweep is a boundary event); size levels are recomputed on the new cushion before the next entry. book: the budget is re-derived from the post-sweep equity. BMS: the sweep never takes the cushion below the buffer (scenario 70); the high-water mark is recorded as "mark before sweep, mark after sweep" so the drawdown rule is not voided (A5-010: the account floor and the book mark never reset by a restart; a sweep is the one declared exception, journalled). account: the floor moves only by his hand. operator: the signed act, with a card showing every anchor before and after.
- **Components.** A1-076, A1-077, A2-077, A5-010, A5-105, A1-078.
- **Engages.** Banker act. Ledger: `sweep_share_above_hwm`, `sweep_min_cushion_after`, `anchor_reset_on_sweep_rule`.
- **Correct outcome.** A sweep never leaves a unit sized for money that left; the drawdown record is continuous across it.
- **Sim proves.** A workflow test: sweep $150; assert every anchor, budget and level is re-derived before the next order, and the mark history is intact.
- **Likely / bad.** L3 (monthly) / S2.
- **Sources.** R2 §5; R9 §0.2; G6 §3.8; C2 (seed after subscriptions).
- **Maturity.** solid.

### X4-scenarios-73. A deposit or re-seed after losses (the capital accelerator)

- **What happens.** After a bad month he deposits $200. The units' cushions jump; the ladder sizes up; a unit that was decaying gets fresh capital at full size. A re-seed after losses is a capital accelerator that bets on the unit's own recovery (R9 §0.2); reinsurance refills a spent layer for a premium, never free (A5-130).
- **Why.** Capital is the one lever that resets every cushion rule at once; it must not reset the evidence.
- **Levels.** unit: the edge zone and the size level are evidence state, not capital state: a yellow unit stays yellow after a deposit; a re-seeded unit starts at level 1 (slow start). book: the budget re-derives from the new equity; the loss history is kept. BMS: the deposit is journalled as a boundary act; the drawdown record keeps "drawdown from the pre-deposit mark" beside "drawdown from the new equity" (two anchors, A5-010). operator: the signed act; the card says which units will size up and why.
- **Components.** A5-010, A5-105, A5-130, A1-078, A5-127, A2-196.
- **Engages.** Capital act. Ledger: `reseed_rule`, `anchor_reset_on_reseed_rule`, `size_level_now`, `edge_zone`.
- **Correct outcome.** New capital changes budgets, never verdicts; a decaying unit cannot be rescued by a deposit.
- **Sim proves.** A workflow test: deposit after a yellow; assert the zone holds and the level stays at 1.
- **Likely / bad.** L2 / S2.
- **Sources.** R9 §0.2; A5-130; G6 §3.8; C11.
- **Maturity.** solid.

## Family K. Operator

### X4-scenarios-74. The operator is away for a week with units live

- **What happens.** He is unreachable for seven days. Three stand-downs wait for him (crash loop, risk stop, kill level); a benched unit's return needs his click under the unit build's rule (G10 §1.6); an isolation's TTL runs out; a proposal card to isolate a class sits unclicked. Either the book goes dark for a week (the sitting duck) or things that should wait for him do not.
- **Why.** Only he promotes, only he lowers the kill switch (brief); but "never block on the human" is also a principle of the harness he runs. The design must say which waits are his and what the system does when he does not answer.
- **Levels.** unit: benches return by rule within their retry budget (scenario 71); locked-out units stay locked. book: budgets renew by rule. BMS: an isolation ends by its own TTL and staged resume (scenario 12) without him; a BMS breaker trip waits for him, and while it waits the book is in "no new entries" for every unit (safe, dark). node: his kill level and his stand-downs wait, as built; a dead-man rule (`operator_absent_after_h`): after N hours with no acknowledgement of a page, the node assumes absence and applies the absence policy he declared (for example: no new entries after the open positions close; or trade on at level 1 under every brake). operator: he sets the absence policy before he leaves; a ticket queue, not a page storm.
- **Components.** A2-007, A2-022, A2-103, A2-097, A3-107, A4-201, A5-056, A4-176.
- **Engages.** B: absence policy, dead-man rule. Ledger: `operator_absent_after_h`, `absence_policy`, `isolation_ttl`, `bench_retry_max_in_window`.
- **Correct outcome.** Routine brakes clear themselves; the ones that need him keep the book safe until he returns; nothing that needs his hand is done by a rule; he chooses in advance how dark "safe" is.
- **Sim proves.** A week replayed with no clicks under each absence policy: growth lost, pages queued, and whether any rule crossed a line that is his.
- **Likely / bad.** L3 (he travels) / S2 in growth terms, S1 in money.
- **Sources.** C21; G9 §1.1, §1.2; G10 §1.6, §7.9; brief hard lines; memory "never block on the human" principle.
- **Maturity.** plausible.

### X4-scenarios-75. Operator error: the wrong scope, the wrong unit, the wrong world

- **What happens.** He resumes `all` when he meant one instrument; kills `account` when he meant one deployment; promotes a unit whose paper lane ran on a $10,000 demo balance to a $200 live share with its calibrated numbers carried over (G9 §3.1, §3.2); ticks "placeholders acknowledged" without reading.
- **Why.** He is not technical and not a trader (brief); every irreversible click must be bound to its effect and show its cost (A5-055, A5-057).
- **Levels.** node: resume and kill render the effect before the click ("this resumes 4 units on 9 markets; 2 are benched by rule and will stay benched"); a `resume all` after a BMS breaker needs a second confirmation; promote refuses a live share whose first-level size is infeasible (scenario 41) and resets the size ladder to level 1 on any world switch (scenario 30). operator: the card is rendered from the canonical effect and re-checked at use time (A5-055); a 30-second undo on resume (a resume that has sent no order can be reverted).
- **Components.** A5-055, A5-057, A5-056, A2-124, A4-041, A4-049.
- **Engages.** Clamp: effect-bound confirmation. Ledger: `world_switch_reset_rule`, `confirm_twice_scopes`, `resume_undo_window_s`.
- **Correct outcome.** A wrong click of the widening kind (resume, promote, loosen) is caught by the effect card or undone within its window; a wrong click of the narrowing kind (kill) costs missed trades and is reversible.
- **Sim proves.** A workflow test of each wrong click against the cards and refusals.
- **Likely / bad.** L3 / S3 (the demo-sized promote is the account killer).
- **Sources.** G9 §3.1, §3.2; A5-055; D19, D30.
- **Maturity.** solid.

### X4-scenarios-76. Operator panic, and the other panic: resuming too early

- **What happens.** A normal 4R morning and he kills `all` BLACK (close everything, pause). Or an isolation is holding a class off and he resumes it at the first green candle. The kill switch is his and must stay his (brief); the design cannot stop him and should not try. It can show him the cost.
- **Why.** The trip tax (A4-202): replay each trip for units paused, time lost, forgone net P&L, exit costs and loss avoided. Alerts that fire too often get ignored and alerts that scare get over-used (R3 §3.6, §3.2).
- **Levels.** BMS: the screen shows the book's state against its own distribution before he acts ("today: −4R, a normal day at the 30th percentile"); after a manual kill the trip tax is computed and shown; a manual resume inside an isolation's settling time is allowed and journalled as his override with the evidence still red. operator: the numbers, not a lock.
- **Components.** A4-202, A2-177, A4-164, A4-171, A2-030, A4-135 (the read-only explainer).
- **Engages.** None (his hand). Ledger: `trip_tax_record`, `operator_override_journalled`.
- **Correct outcome.** His overrides are always possible, always journalled, and always shown with their cost afterwards; over months the trip-tax record teaches both of them.
- **Sim proves.** Not a Monte Carlo: a replay job that computes the trip tax for every manual action in the journal.
- **Likely / bad.** L3 / S1-S2 (missed trades, exit costs).
- **Sources.** C21 (the kill switch is his); R3 §3.2, §3.6; A4-202.
- **Maturity.** solid.

### X4-scenarios-77. Unreachable with open trades and a page pending

- **What happens.** A protection escalation fails (a stop never shows at the venue after three tries; the reduce-only close is rejected); the page fires; his phone is off. The position is naked.
- **Why.** The push list exists (C-18, G9 §7.2); what the system does when no answer comes is unwritten. Pages need a deadline and an action (A4-201).
- **Levels.** trade: the escalation keeps trying on a schedule (back-off, not three tries then nothing); a limit close at the worst-price cap, then a market close, then a hedge on the same instrument if the venue allows (a hedging account) so the exposure is flat even if the position is not. node: after the page's deadline with no acknowledgement, the declared no-answer action runs (default: keep closing reduce-only; never widen). operator: the page says what will happen at the deadline.
- **Components.** A2-104, A4-201, A4-157, A2-002, A5-061.
- **Engages.** B: protection escalation (extended). Ledger: `protection_retry_max` (v0, becomes a schedule), `page_deadline_min`, `no_answer_action`.
- **Correct outcome.** No position stays naked past the deadline; the action at the deadline is one he chose.
- **Sim proves.** A workflow test: venue refuses the stop and the first two closes; assert the schedule continues and the deadline action runs.
- **Likely / bad.** L2 / S3.
- **Sources.** G9 §1.1, §7.2; A4-201; A5-061 (a stop that fires but leaves orders working is a failed control).
- **Maturity.** solid.

## Family L. Instrument-specific

### X4-scenarios-78. Futures rolls and expiry, and the CFD roll gap

- **What happens.** WTI's last trade is three business days before the 25th of the prior month (R8 §4.1); a front-month position held into expiry is the April 2020 case (negative settlement). On a futures-based CFD the broker rolls on its own date and posts a one-time adjustment equal to the price difference; pending orders inside the roll gap fill at the new price; a stop inside the gap is hit by the roll, not by the market (R8 §4.6). The record carries `expiry`, `last_trade`, `rolls_to` (G7 §4.2); no code reads them for risk.
- **Why.** Roll windows are predictable flow events (R8 §4.5); a back-adjusted series never counts as P&L (A5-031); the roll adjustment is its own P&L line (A5-095).
- **Levels.** trade: no stop sits unflagged inside a roll gap; a stop near the roll is moved with the adjustment (an amendment that keeps the same risk, not a widening). unit: a unit that holds futures declares its roll policy (roll N days before last trade, or flat before); a unit that does not declare one may not hold through the window (`overnight_hold_rule` already covers the daily session). book: —. BMS: roll windows per contract are in the standing event calendar (A3-143); the index roll days are a cost-elevated window. node: reads the broker's roll calendar per CFD (A5-095) and the exchange calendar per contract; contract identity is checked on every order (R4 technique 6: hard stop on uncertain contract identity). operator: a ticket the week before each roll.
- **Components.** A5-031, A5-094, A5-095, A3-143, A1-165, A4-179, A3-018.
- **Engages.** B: roll-window entry block, contract-identity check. Ledger: `roll_days_before_last_trade`, `roll_adjustment_pnl_line`, `stop_in_roll_gap_check`, `contract_identity_verified`.
- **Per class.** Futures: exchange calendar per contract, delivery risk. Energy CFDs: broker roll dates and a large gap (about $5 on WTI in the October 2026 roll, unverified, R8 §4.6). Index CFDs: dividends instead. Metals: GC rolls quarterly. Crypto perps: no roll, funding instead.
- **Correct outcome.** No position is held into last trade by accident; no stop is triggered by a roll adjustment; roll costs are a cost line, never a strategy loss.
- **Sim proves.** Contract-level replay with explicit rolls (A5-031): P&L with and without the roll line; stops hit by adjustments under each policy.
- **Likely / bad.** L1 (no futures route yet; CFD rolls monthly) / S4 for expiry, S2 for the CFD gap.
- **Sources.** R8 §4.1, §4.5, §4.6; G7 §4.1-4.2; A5-031, A5-095.
- **Maturity.** plausible.

### X4-scenarios-79. Energy reports: EIA petroleum, gas storage, OPEC

- **What happens.** Wednesday 10:30 ET the EIA petroleum report prints; in a holiday week it is Thursday at 11:00, or once a Monday at 17:00 (R8 §4.2). Crude and gas jump within seconds; a surprise in one moves the other (R8 §4.3). A crude scalper with no energy event in its calendar enters at 10:29.
- **Why.** Energy needs no special sizing, it needs three overlays: the event calendar as data with its own refresh, the roll calendar, and a larger gap allowance (A5-094, R8 §4.7). Gas apart from crude.
- **Levels.** unit: the energy pack's event windows (EIA, gas storage, OPEC with a decision-type field) resolve through the driver tags (scenario 17): the EIA petroleum report tags crude, gas, the energy ETFs and the CAD pairs (an energy currency); window width by measured impact per release and instrument (A3-130). book: —. BMS: the energy calendar is read from the published schedule, never hard-coded (R8 §4.2); a missing schedule fails safe up (the week's report is "unknown time", so the usual time and the holiday alternatives are both blocked). node: the calendar ingest covers the EIA and OPEC sources beside the FX calendar. operator: —.
- **Components.** A3-143, A3-130, A3-131, A3-132, A5-094, A3-051 (oil shock type as a scenario selector), A3-129.
- **Engages.** B: energy event windows, fail-safe-up on a missing schedule, gap allowance (energy). Ledger: `news_impact_level_map` (v0, extended to energy sources), `energy_event_sources`, `gap_allowance_pct` (energy value), `shared_driver_tags`.
- **Per class.** Crude and gas are separate volatility and event sets; gas is far more volatile and seasonal (R8 §4.7); CAD pairs carry an energy driver tag; metals and indices do not react to the EIA report in the same way, so the tag is not "USD".
- **Correct outcome.** No entry into an energy release; a holiday-shifted report is still caught; a surprise in crude blocks gas and the reverse.
- **Sim proves.** Event-study replay around every EIA and OPEC release on the energy records: move and spread after the print per instrument; R of entries inside the window against outside; the count of releases the hard-coded "Wednesday 10:30" would have missed.
- **Likely / bad.** L5 (weekly) / S3 per event for an energy scalper.
- **Sources.** R8 §4.2-4.4, §4.7; A5-094; A3-143.
- **Maturity.** solid.

### X4-scenarios-80. The crypto liquidation cascade

- **What happens.** On a perp venue, a 4 % drop triggers a band of liquidations; forced selling pushes the price through the next band; funding spikes; the mark price (an index) and the last price split; QMX's stop on last fires late, or its position is liquidated by the engine before the stop. Taker order-flow variance compression preceded 6 of 7 BTC cascades at the population level, and is not a per-event alarm (R4 technique 15, 2607.27070).
- **Why.** Liquidation can beat the stop (A3-001 class notes); the venue's rules, not only its prices, must be in the scenario (R4 technique 21); a cascade is the crypto version of scenario 31 plus scenario 52.
- **Levels.** trade: the stop sits above the liquidation price with a buffer that covers the mark-against-last divergence seen in the venue's own history (scenario 52). unit: a crypto unit's gap allowance covers a two-band cascade; leverage on perps is capped below the venue's maximum by a wide margin (the ESMA 2:1 cap is a fair default for a retail book, R3 §4.1). book: —. BMS: the crypto class isolation reads funding, open-interest change, cross-venue basis and the liquidation-flow tell together (two tells agree, scenario 09); the crypto exposure cap is stricter than its class share (scenario 52); weekend crypto stress is a Monday review trigger (A3-058). node: mark, last and index are all read; a divergence past a band stands the market down. operator: ticket; page if a liquidation happened.
- **Components.** A3-235, A3-058, A2-262, A3-040, A3-093, A3-109, A5-096, A3-001, R4 technique 21 (perp ABM, A5-059).
- **Engages.** B: liquidation buffer, crypto leverage cap, class isolation on crypto tells, mark-last divergence stand-down. Ledger: `liquidation_buffer_pct`, `crypto_leverage_cap`, `mark_last_divergence_max_pct`, `funding_spike_tell`, `co_move_score`.
- **Correct outcome.** QMX is never liquidated by the engine (its own stop is always first); a cascade costs at most the stop plus the cascade allowance; the class is off before the second band.
- **Sim proves.** The perpetual-futures agent-based market with liquidation mechanics (R4 technique 21): loss distribution per stop-distance and leverage rule; the isolation's precision on the venue's cascade history.
- **Likely / bad.** L3 / S3-S4.
- **Sources.** R4 techniques 15 and 21; A3-235; G9 §3.4; R3 §4.1; D39.
- **Maturity.** plausible.

### X4-scenarios-81. Single stocks and index constituents: earnings, dividends, borrow, the reopen auction

- **What happens.** A stock CFD held into earnings gaps 15 %; a short pays a dividend; a borrow is recalled; a halt (scenario 33) reopens in an auction far from the last print. No stock route exists today (G7 §4.1); the class enum and a pack do.
- **Why.** Single-stock hazards are one-name events and name-level cuts (R4 technique 8 per class); an earnings, filings and halts calendar is its own source (A3-144).
- **Levels.** unit: a stock unit declares its earnings policy (flat before, or hold with the earnings gap in its size); borrow availability is a pre-trade check for shorts. book: —. BMS: single-name exposure caps apart from the sector cap (A3-048, two layers); a name-level cut never isolates the class. node: the stock calendar ingest (earnings dates, ex-dividend dates, halts). operator: —.
- **Components.** A3-144, A3-048, A2-264, A1-108, A3-018.
- **Engages.** B: earnings window, name-level cap, halt allowance. Ledger: `earnings_window_policy`, `per_instrument_exposure_cap` (v0), `halt_allowance_pct`, `borrow_check_required`.
- **Correct outcome.** No stock is held into a declared earnings date by accident; one name's event never trips the class; shorts never meet a recall unprepared.
- **Sim proves.** Historical earnings gaps on the stock records: loss under each policy; the allowance that covers 95 % of gaps.
- **Likely / bad.** L1 (no route) / S3.
- **Sources.** G7 §4.1; R4 technique 8 and 15 per-class rows; A3-144.
- **Maturity.** plausible (no route exists).

## Family M. Two at once (combinations)

Each combination names the two or three scenarios it joins and only what the join adds. The harness (idea 90) runs every pair in the catalogue by construction; these are the pairs whose join changes the answer.

### X4-scenarios-82. A scheduled release while the feed is stale (news plus unknown state)

- **Joins.** 15, 16 and 46.
- **What the join adds.** The news window is clock-driven and the stale-feed stand-down is data-driven. At 13:30 the window opens as planned; at 13:33 the feed freezes for 100 seconds; at 14:00 the window closes while the feed is still unreliable and the tells (spread, volatility) cannot be read. "Window closed" plus "no tells" reads as calm to a naive rule.
- **Levels.** unit: a window may not close into an unknown state: the post-release side of every window ends on tells clear, with the timer as the earliest end, never the only end (the "exchange resumed is not a re-enable signal" rule, A3-141). node: a stale market during a window extends that market's window until fresh quotes and a clean tell. BMS: unknown is not calm (A3-094).
- **Components.** A3-094, A3-141, A2-007, A3-133, A2-102.
- **Engages.** B: state-based window end. Ledger: `news_blackout_after` (v0, becomes the earliest end), `window_end_requires_fresh_quotes`.
- **Correct outcome.** No entry in the minutes after a release on a market whose state is unknown.
- **Sim proves.** Replay of release days with injected freezes: entries sent into unknown state under timer-end against state-end.
- **Likely / bad.** L3 / S2.
- **Maturity.** solid.

### X4-scenarios-83. A flash crash while the broker link is down

- **Joins.** 31 and 45.
- **What the join adds.** The node cannot see the crash. The broker-side stops fill 2 % through; the price returns; by reconnect the positions are gone and the equity is down 3 %. Marked equity never showed the dip to the node, so a floor rule with a dwell time never saw a breach; the reconcile finds closed positions it did not close. The velocity tell never fired because there were no ticks.
- **Levels.** node: on reconnect the reconcile reads the venue's deal history, not only the open positions, and books every fill that happened offline with its slippage (A2-059, Safe Mode); the gap-through-stop rows are written after the fact. unit: the re-entry cooling after a fill through the stop applies from the reconcile, not from the fill time. BMS: the event window is opened retroactively at the first offline fill so the book counts the crash once. account: the floor rule reads the venue's equity history for the gap, so a breach that happened offline is still a breach (the dwell-time variant must be computed on the venue's series, not the node's).
- **Components.** A2-059, A2-117, A2-118, A2-026, A4-170.
- **Engages.** B: Safe Mode reconcile with deal history, retroactive event window. Ledger: `reconcile_reads_deal_history`, `floor_breach_dwell_s`, `loss_event_window` (v0).
- **Correct outcome.** Nothing that happened offline is invisible to a brake afterwards; the book re-arms only after the reconcile has booked every offline fill.
- **Sim proves.** A workflow test: replay a crash tick-by-tick on the venue side with the node link cut; assert the reconcile books the fills, the window opens and the cooling applies.
- **Likely / bad.** L1 / S3.
- **Maturity.** plausible.

### X4-scenarios-84. Edge decay and cost drift at the same time (which is it?)

- **Joins.** 60, 39 and 38.
- **What the join adds.** The unit's net R falls. Costs rose 40 % and the gross edge fell 30 %. One signal cannot tell them apart; acting on the wrong one either cuts a unit whose costs can be fixed (change instrument or hour) or keeps trading a dead edge on a cheaper instrument. Gen 3 said decay is judged in R never cash and costs are never folded into a decay verdict (G10 §5.3).
- **Levels.** unit: two streams kept apart: gross R before costs (the edge stream) and cost in R (the cost stream); the CUSUM runs on gross R, the cost drift check on the cost stream (A2-174 separates edge decay from spread, slippage and implementation faults); the verdict names the cause. book: —. BMS: a cost-caused fall moves placement (another hour, another instrument, another broker); an edge-caused fall moves the size level. operator: the card says "costs +40 %, edge −30 %: half of the loss is placement".
- **Components.** A2-174, A2-166, A2-149, A5-008 (latent-state edge tracker: skill, exposure, horizon and execution as separate states), A3-084.
- **Engages.** B: split-stream drift. Ledger: `gross_edge_r`, `cost_stream_r`, `drift_cause_code`.
- **Correct outcome.** A cost problem is never treated as a dead edge, and a dead edge is never hidden by a cost excuse.
- **Sim proves.** Planted paths: costs up only, edge down only, both; the attribution's accuracy and the action taken under each.
- **Likely / bad.** L3 / S2.
- **Maturity.** solid.

### X4-scenarios-85. An isolation while the operator is away

- **Joins.** 08, 12 and 74.
- **What the join adds.** The isolation's TTL runs out on day two of his absence. If isolation waits for him the class is dark for a week (the sitting duck). If it resumes by rule into a second wave (scenario 37) nobody is there to kill it. The staged resume with retrip back-off is exactly the rule for this: resume at half size, retrip doubles the next TTL, a second retrip inside the settling window locks the class out until he returns.
- **Levels.** BMS: isolation ends by TTL and staged resume without him; a retrip inside the settling window locks the class for the rest of his absence (the absence policy, scenario 74, sets the lockout to "until acknowledged"). operator: the absence policy he set.
- **Components.** A3-107, A2-119, A2-022, A5-056.
- **Engages.** B: staged resume, retrip lockout under absence. Ledger: `isolation_ttl`, `isolation_retrip_backoff`, `retrip_lockout_rule`, `absence_policy`.
- **Correct outcome.** A one-off shock costs two days of the class, not a week; a repeating shock locks the class until he is back.
- **Sim proves.** Shock with aftershocks replayed under the absence policy: class dark time and loss under TTL-only, click-only and staged-with-lockout.
- **Likely / bad.** L2 / S2.
- **Maturity.** solid.

### X4-scenarios-86. A unit bug with the accelerators on

- **Joins.** 53 and 63.
- **What the join adds.** A new version sizes 2x by mistake (inside the per-trade cap, so the clamp does not fire), wins its first three trades by luck, house money triggers, the tier ladder is already one step up from the previous version's record, and the fourth trade is at 3.6x the intended size. The clamps are per trade; the accelerators compound a bug that stays under the per-trade cap.
- **Levels.** unit: a new version starts at level 1 with every accelerator locked for its settling period (slow start, A5-127), whatever the previous version's tier; the size sanity band (scenario 42) compares to the unit's own usual lots and flags 2x; the canary against the paper twin (scenario 55) shows "live size 2x twin size" on trade one. BMS: no accelerator in the first N trades of any version.
- **Components.** A5-127, A5-137, A5-138, A4-025, A4-035, A2-003.
- **Engages.** B: version slow start with accelerator lockout, size sanity band. Ledger: `size_level_now`, `house_money_lockout`, `size_sanity_band_multiple`, `accelerator_lockout_trades_after_version`.
- **Correct outcome.** A bug under the cap costs level-1 trades, not accelerated ones; the twin shows it on the first trade.
- **Sim proves.** The dry chassis with a 2x size fault and the accelerators on: size path with and without the version lockout.
- **Likely / bad.** L2 / S3.
- **Maturity.** solid.

### X4-scenarios-87. A correlation spike while the broker cuts leverage

- **Joins.** 02 and 67.
- **What the join adds.** Risk-off: everything moves together and the broker halves leverage on indices and crypto in the same hour. The same-bet cap says the book is one bet and trims; the margin headroom says free margin is gone; the two rules want different positions cut first (the most correlated against the most margin-hungry). The broker's close-out order is a third opinion.
- **Levels.** BMS: one de-gross order for the whole book: by stressed contribution (loss under the standing scenario set with correlations raised, A5-041, A3-159), which already weights both the correlation and the size; margin headroom is a constraint the order must satisfy, not a second ranking; the de-gross runs before the broker's level. account: margin and equity refreshed every fill.
- **Components.** A5-041, A3-159, A1-129, A1-158, A5-091.
- **Engages.** B: stressed-contribution de-gross, margin headroom. Ledger: `leverage_cut_degross_rule`, `margin_headroom_min_share`, `correlation_stress_rho`, `sleeve_stress_loss_usd`.
- **Correct outcome.** One ranking, one order of cuts, done before the broker chooses; the cuts take the most stressed contributors first.
- **Sim proves.** Risk-off replay with a leverage cut: loss under "cut by correlation", "cut by margin" and "cut by stressed contribution".
- **Likely / bad.** L2 / S4.
- **Maturity.** plausible.

### X4-scenarios-88. The seed near the floor during a normal losing run

- **Joins.** 69 and 62.
- **What the join adds.** At $330 with a $300 floor a healthy unit's normal 8-loss run is the floor. Every brake is on and correct, and the floor is still crossed because the cushion is smaller than one normal drawdown. The brakes cannot save a cushion smaller than the unit's own median drawdown (27R at 2,000 trades, R2 §2.1); only size can, and size is already at the minimum lot.
- **Levels.** BMS: a feasibility test before any unit trades near the floor: the cushion must cover the unit's own 95th-percentile drawdown at level 1 (from its baseline card's cone, G9 §7.1); if it does not, the unit may not trade and the floor-hit action runs early (stop the pot, or his re-seed). operator: the card says "cushion $30 covers 4R; this unit's normal drawdown is 16R: not feasible".
- **Components.** A1-036 (floor-touch size bound from the cushion), A2-165 (cone check), A3-001, A5-141, A2-132.
- **Engages.** Clamp: cushion-covers-drawdown feasibility. Ledger: `cushion_covers_drawdown_percentile`, `floor_hit_action`, `mc_cone_floor_percentile` (v0).
- **Correct outcome.** The floor is crossed by a gap or never; a unit whose normal pain exceeds the cushion is not allowed to find out.
- **Sim proves.** Monte Carlo from $330: floor touches with the feasibility test on and off.
- **Likely / bad.** L2 / S4.
- **Maturity.** solid.

### X4-scenarios-89. Roll week, the EIA report and a limit move on the same Wednesday (the energy triple)

- **Joins.** 78, 79 and 34.
- **What the join adds.** The CFD rolls Tuesday night with a $5 gap; the EIA report prints Wednesday 10:30 ET; crude moves limit-down on the surprise; the broker's CFD keeps quoting with a 10x spread while the future is halted. A stop placed before the roll sits inside the roll gap; the roll adjustment and the report move land within hours; the velocity logic halts the future and the CFD has no reference price.
- **Levels.** unit: an energy unit is flat across a roll that falls inside two days of a scheduled report (the two windows are joined into one); after a limit move the CFD is isolated until the future reopens and trades inside its band (A3-141). BMS: the energy calendar joins roll and report windows per contract. node: a CFD whose underlying future is halted is marked "reference unknown" and stood down.
- **Components.** A5-094, A5-095, A3-143, A2-264, A3-141, A2-072.
- **Engages.** B: joined roll-and-report window, reference-unknown stand-down, limit-move allowance. Ledger: `roll_report_join_window_h`, `limit_move_allowance`, `reference_unknown_standdown`.
- **Correct outcome.** No energy position crosses a joined roll-and-report window; a limit move never traps a CFD position against a halted reference.
- **Sim proves.** The April 2020 week and the 2022 limit-move days replayed on the energy records with the joined window on and off.
- **Likely / bad.** L1 / S4.
- **Maturity.** plausible.

---

# Part 1b. The scenario harness and the design ideas drawn from the catalogue

These are hybrids in the Stage B sense: each links components by id and names the need it serves. Idea 90 is the harness itself; 96 to 99 are its parts; 91 to 95 are the design ideas the scenarios above lean on.

### X4-scenarios-90. The scenario harness: every scenario against every template version, with QMX's own brakes inside the path

- **Components.** A5-088 (conditional scenario fill), A5-089 (daily backtest of the stress engine, hidden factors), A5-091 (concentration limits per common dependency), A5-092 (the unwind scenario with brakes simulated inside), A5-093 (SPAN-style per-instrument grid), A3-147 (mandatory scenario set plus own), A3-149 (common-shock construction), A3-151 (historical replay through the real strategy stack), A3-155 (liquidity and execution inside every scenario), A3-157 (validate generated scenarios through the downstream strategy), A3-159 (stress results as survival gates, marginal stress contribution as the growth control), A3-169 (rk5 shock list), A3-175 and A1-174 (the dry chassis), A2-135 (random-control brake test), A2-141 (trade-list re-sizer), A4-097 (self-test card per profile version, PASS or FAIL gate), A4-186 (resize replay), A5-024 (shadow allocator ablation), A2-144 (contract test: every brake passes reduce-only orders), A4-202 (trip tax), A5-034 (test the whole pipeline against nulls and injected edges), A3-176 and A3-177 (his ask, and the lead's bare sims as the baseline).
- **Need it serves.** His D40 and C32: worst, realistic and best cases "all factors considered", every scenario run with the brakes in place, not bare; his "losing together" objection (SEEDS replies row 23); capability 43 and 48 of the technical lens; and the funnel's survival gate (RANKING: a 0 on survival blocks an idea) needs a machine that produces the survival number for every candidate template.
- **What it does.** A scenario is data (idea 96). A template version is data (X1: a profile version with its sizer, brakes, accelerators, clamps and derivations). The harness takes the cross product and, for each cell, runs the whole stack (entries, exits, sizer, every brake at every level, the guard's rank table, the kill switch effects) through the scenario path, and writes a scorecard (idea 97). It never runs a return simulation of the brakes; it runs the brakes.
- **How it works, in six rules.**
  1. **Stressed factors, filled factors.** A scenario names the factors it stresses (a USD move, a class's spread multiple, a feed gap) and a path shape. Every factor it does not name is filled with its expected value *given* the stress, never zero and never "yesterday" (R8 §3.1, Cai, Haugh and Li: the conditional fill moved scenario P&L by up to about $44 on their grid and the naive method hid a −$20 book inside ±$3). With QMX's short history the conditional fill comes from class pooling (A5-097, A5-099) and nearest-neighbour days on the shared history, labelled as an assumption until QMX's own history is long enough. The output per cell is a band (p5, p50, p95), not a point.
  2. **Accumulation per shared dependency.** Before any path runs, the harness lists the book's common dependencies (R8 §3.4, Lopez and Nkameni): broker and venue, price feed, compute host, clock, signal family, macro factor (USD, equity beta, oil, crypto beta), scheduled event, session and rollover. For each it computes the share of open risk exposed and the loss if it fails or moves (A5-091). A book that passes every price scenario and has 70 % of its risk on one feed is failed on accumulation. The concentration limits per dependency are a survival gate of their own.
  3. **QMX's own brakes inside the path.** Every brake, accelerator, clamp and restore in the template version runs inside the scenario, on the scenario's clock, with the rank table deciding ties (scenario 59). The unwind case (R8 §3.5, A5-092) is the proof that this matters: a book whose stops and de-risking fire together deepens its own loss and sells the rebound. The harness reports both the price-path loss and the brake-path loss, and their difference is the brake's contribution, positive or negative. FARSIGHT's 9.2 % to 17.3 % amplification (R4 technique 21) is the same effect across agents.
  4. **Three cases per scenario, not one.** Worst (the stressed factors at their p95 severity, filled factors at their conditional mean, costs at 2x), realistic (p50, costs at 1.5x), best (p5 severity, costs as measured). His words: worst, realistic and best, all factors considered (D40). The lead's bare "losing together" sim is kept as the zero-brake baseline row so the brakes' effect is always visible against it (A3-177).
  5. **Controls beside every claim.** The dry chassis (random entries with the full template on, A1-174) runs through the same battery: what the template alone does with no edge. Every brake is scored against a random brake that fires as often (A2-135, the MQL5 23482 design). Every template version's survival is compared with the previous version's on the same scenarios (the canary pattern, A4-025).
  6. **The engine backtests itself.** Every night the harness replays yesterday's actual moves as a scenario and logs predicted against realised P&L per unit and per book (R8 §3.1, A5-089). The error record is the harness's own precision; a scenario set the agents can see is also stressed with factors they cannot (the adversarial-portfolio warning, R8 §3.1).
- **Where it runs.** Numbers-lens simulations on This PC and the Lab, never on the node; QMB's resize replay (A4-186) and what-if jobs are the engine for trade-list cases; a light Python harness over the guard module is the engine for brake-path cases; the interactive bench (idea 99) for crowding cases. Fable agents rerun it (capability 43). It reads the ledger v1 for every variable it sweeps (STATE item 12: the ledger is central through the simulations).
- **Levels.** It scores every level: trade (stop and gap), unit (size and own brakes), book (budget, event window), methodology (pooled stream), BMS (isolation, breaker, same-bet, budgets), account (floor, margin), node (stand-downs), operator (pages per month, trip tax).
- **Per class and style.** The scenario set has a per-class block (R4 technique 15's per-class list: FX interventions and weekend breaks; index gaps and halts; metal squeezes and margin hikes; energy expiry, negative prices and limit moves; crypto cascades, depegs, funding spikes and venue outages; futures rolls and margin shocks; stock earnings and halts) and a per-style block (scalpers: cost and spread paths; intraday: session hand-overs and news; swing: gaps, carry and weekends). Contagion between classes is a time-indexed dependency graph with direction, lag and regime per edge, including one market closed or one venue down (A3-234).
- **Ledger ids.** `scenario_set_version`, `scenario_severity_percentile`, `conditional_fill_method`, `dependency_concentration_limit`, `brake_path_delta_r`, `harness_prediction_error`, `cost_stress_multiple` (v0), `correlation_stress_rho`, `sleeve_stress_loss_usd`, `loss_event_window` (v0), plus every brake variable the templates carry.
- **Performance note.** The harness is what lets the funnel pick for performance under a survival constraint instead of for safety alone: a template that never touches the floor and grows nothing scores zero on growth in the same table. Marginal stress contribution is the growth control (A3-159): a sleeve with low stress loss earns budget.
- **Survival note.** Survival gates are hard: floor touches per 1,000 runs at half edge, worst loss against the buffer, accumulation per dependency, brake-path loss not worse than price-path loss by more than a declared share.
- **Evidence chain.** Conditional fill: a read paper on simulated books (R8 §3.1). Accumulation: an insurance model with expert-set parameters (R8 §3.4). Brakes inside the path: an abstract-level hypothesis about 2007 plus a 2026 agent simulation (R8 §3.5, R4 technique 21). The random-control brake test: one MQL5 article with a proper control (R5 23482). **Weakest link:** the conditional fill on QMX's own history, which does not exist yet; the first versions fill from pooled public history and label it.
- **Maturity.** solid as a design; the engine does not exist.

### X4-scenarios-91. The event window (the hours clause)

- **Components.** A2-026, A3-146, A3-149, A3-158, A2-011.
- **Need.** Scenarios 01, 05, 65, 83: many units' losses from one move count once for the book's brakes, so a correlated hit is one big event, not five strikes (R3 §3.3).
- **How.** A window per shared driver opens at the first loss tagged with that driver and closes after the driver's measured co-move duration (default by class; tornado, windstorm and flood have 24, 72 and 168 hours in insurance; a USD move on FX is minutes to an hour, a risk-off day is a session). Inside the window: the book's budget drains once by the event's total; count brakes see one event; house money is off; the window's losses are summed per driver for the accumulation report. The window is journalled with its driver, members and total.
- **Levels.** book and BMS. **Per class.** The window length is a class default, refined per driver from history.
- **Ledger.** `loss_event_window` (v0), `event_window_by_driver`, `shared_driver_tags`, `house_money_lockout`.
- **Performance and survival.** Keeps healthy units trading after a correlated hit (no false benches); bounds the book's loss per event at its event allowance.
- **Evidence.** Insurance practice (read, Verisk); no trading test. Weakest link: the window length per driver.
- **Maturity.** solid.

### X4-scenarios-92. Same-bet exposure by bet key, with per-driver caps sized to a tail gap

- **Components.** A1-115, A1-114, A1-129, A3-048, A3-050, A5-091, A3-161, A1-108.
- **Need.** Scenarios 01, 03, 35, 64, 87: the same bet counted once; exposure per driver small enough that a 20 % gap on one driver costs at most the buffer.
- **How.** Every intent carries a bet key (logic family, driver tags, direction). The guard sums open risk per key and per driver (currency legs for FX, covariance or beta for the rest) *after this trade* (A1-114) and refuses or trims the order that would pass the cap. The per-driver cap is derived: cap = buffer before the floor ÷ tail gap assumption for that driver (an SNB-sized 20 % for a pegged currency, 7 % for an index, 30 % for a crypto cascade), so the derivation is visible and he can change the tail assumption or the formula (D46). Parent limits sit below the sum of their children, sized on how often the children lose together (A3-161).
- **Levels.** BMS computes, the guard applies, the unit never sees it (C18: the correlation ledger is "internally external").
- **Per class.** FX by currency leg; indices by region beta; metals split precious and industrial; energy by contract cluster; crypto by BTC beta plus venue; futures by contract, not class.
- **Ledger.** `same_bet_exposure_cap`, `bet_key_rule`, `per_driver_exposure_cap`, `tail_gap_assumption_pct`, `currency_exposure_limit` (v0), `cluster_exposure_cap` (v0), `open_risk_at_stop` (v0).
- **Performance and survival.** The cap, not a smaller size everywhere, does the work: growth stays near the independent case (scenario 01). A black swan on one driver costs the buffer, not the floor.
- **Evidence.** Breadth maths (R2 §4.2); pod practice of per-pod and firm limits (R2 §2.3); no QMX test. Weakest link: the tail gap assumptions, expert-set and labelled.
- **Maturity.** solid.

### X4-scenarios-93. Effective units on the BMS screen

- **Components.** A3-163, A1-105, A1-106, A5-001, A5-002, A5-004, A5-064.
- **Need.** Scenarios 03, 24, 64: show "effective units: 2.3 of 10" so the frequency thesis is counted honestly; the BMS day budget scales with open breadth.
- **How.** N_eff = N ÷ (1 + (N − 1)ρ) from the realised daily correlation of unit P&L, and the entropy version on the book's own weights (A5-001); residualised breadth after shared exposures (A5-004). Shown per book, per family and for the open hours (weekend: 2 of 10). The budget per open hour scales with N_eff (A3-114).
- **Levels.** BMS. **Ledger.** `effective_independent_bets` (v0), `effective_bets_drop_trip` (v0), `open_breadth_budget_scale`, `unit_result_correlation` (v0).
- **Performance and survival.** Breadth is the lever and correlation its limit; the number on screen is what stops ten correlated units being funded as ten.
- **Evidence.** Grinold and Meucci (cited in R2); A5-003's procedure. Weakest link: ρ from few days of live data.
- **Maturity.** solid.

### X4-scenarios-94. The isolation lifecycle

- **Components.** A3-106, A3-107, A3-108, A3-109, A3-093, A3-095, A3-113, A3-115, A2-119, A2-120, A2-121, A2-122, A2-123, A2-125, A5-152.
- **Need.** Scenarios 08 to 14, 32, 37, 85: his market isolation protocol (C27) with evidence, scope, mode, time to live, staged resume, retrip back-off and a precision record.
- **How.** Scope keys class, region, currency, underlying group (A3-106) beside instrument in the kill switch and the stand-down table. Evidence: two tells must agree (spread and volatility against the usual for this minute of the session, across many instruments of the scope; or one tell plus a calendar event tagged to the scope), with a calendar-aware baseline (A3-109). Mode graded by evidence strength: no new entries, reduce, flatten (A3-108). TTL with staged resume (half size, settling time, full after N clean minutes), a retrip doubles the next TTL, a second retrip inside the settling window locks the scope out for the day (A3-107, A2-119). Slow isolation by agent proposal card with evidence and a TTL (A3-113). The MIS publishes the isolation on the board and placement fails closed during it (A3-115). Every isolation records its own precision afterwards (A2-123).
- **Levels.** BMS decides; node applies; MIS publishes. **Per class.** Crypto by local turbulence plus funding; Asian-session indices from instruments trading in that session only; FX by currency and session; metals precious apart from industrial; energy by contract cluster (R4 technique 8).
- **Ledger.** `isolation_scope` (v0), `market_isolation_trigger` (v0), `isolation_end_rule` (v0), `isolation_mode`, `isolation_ttl`, `isolation_two_tell_rule`, `co_move_score`, `settling_time`, `resume_size_fraction`, `isolation_retrip_backoff`, `retrip_lockout_rule`, `brake_precision` (v0).
- **Performance and survival.** The exchange pattern: one small breaker per product that pauses and resumes, one big breaker for everything (R2 §3.1); the staged resume avoids the re-entry cluster; the precision record keeps the brake from being muted.
- **Evidence.** Exchange breakers (read); fund risk-off tells (cited); no public source on a fund switching off one class by rule (R2 not verified). Weakest link: the two-tell thresholds, to be scored on history for precision and recall (scenario 09).
- **Maturity.** solid.

### X4-scenarios-95. Sectoring: driver tags per instrument and measured event impact

- **Components.** A3-131, A3-130, A3-132, A3-124, A3-125, A3-133, A3-135, A3-143, A3-144, A3-229.
- **Need.** Scenarios 15, 17, 18, 21, 79: news by instrument and region (C27, C28), not by quote currency; window width by measured impact and unit type, not by colour.
- **How.** Each instrument record carries driver tags: both FX legs, home exchange, region, class, and named events it reacts to (the EIA report for crude, gas and CAD; US CPI for USD pairs, gold, US indices and crypto). Tags are seeded by class defaults and refined by the event-study measure per release and instrument (move and spread in the minutes after, A3-130), kept in a versioned historical event file so the rules are testable (A3-135). Window width per release class and unit type from that measure (A3-132); blocked hours reported as a cost. Unknown mapping fails safe up (A3-125). The calendar's misses are backstopped by the tells (A3-133).
- **Levels.** BMS owns the tags; node applies the windows; units declare the impact level they block on.
- **Ledger.** `shared_driver_tags`, `measured_event_impact`, `news_impact_level_map` (v0), `news_blackout_before` (v0), `news_blackout_after` (v0), `news_block_impact_min`, `entries_blocked_by_window`, `news_fail_safe_affected`, `energy_event_sources`.
- **Performance and survival.** Narrow, measured windows keep a scalper's day; fail-safe-up and the tells keep the one release that matters from costing a day budget.
- **Evidence.** Event-study practice (R2 §3.4); the April currency scope table (G10 §3.1). Weakest link: the first tag set is class defaults until the event file has a year of measures.
- **Maturity.** solid.

### X4-scenarios-96. Scenario as data: the scenario record

- **Components.** A3-147, A3-152, A3-232, A3-233, A3-234, A4-087 (Library governed kinds), A4-098 (the ledger as schema source), A5-089, A3-169.
- **Need.** The harness (90) needs scenarios it can run, version, add to and score; he wants to generate many (C32) and agents to add more; Lloyd's keeps a mandatory set every syndicate reports against plus two of its own (R3 §3.3).
- **How.** A Library kind `scenario` with: id and version; family; the stressed factors with severity percentiles and a path shape (jump, drift, two-wave, limit sequence, freeze); the shared dependencies it stresses (venue, feed, clock, driver, event); the fill method for unstressed factors; the levels it tests and what each should do (the "Levels" paragraph of this catalogue, as data); the brakes, accelerators and ledger variables it expects to engage; the pass test (the "Sim proves" paragraph, as a check with a threshold); likelihood and severity, first expert-set and labelled, then measured from the harness's own error record and live history; sources. The mandatory set is this catalogue's solid scenarios; each book and template adds its own; agents propose new ones as cards (the proposal door, X7), and a scenario an agent can see is paired with one it cannot (R8 §3.1).
- **Levels.** All, as fields. **Ledger.** `scenario_set_version`, `scenario_likelihood_class`, `scenario_severity_class`, `scenario_expected_engagements`.
- **Performance and survival.** A fixed crisis library that calm data cannot erase (R4 technique 15) and a growing one that agents extend.
- **Evidence.** Lloyd's RDS practice (read); CME SPAN grids (snippet). Weakest link: likelihood classes are guesses until measured.
- **Maturity.** solid.

### X4-scenarios-97. The scenario scorecard per template version

- **Components.** A3-159, A4-097, A2-142, A2-030, A4-202, A5-073, A4-025, A1-171, A1-172, A4-139.
- **Need.** The funnel's six scores (RANKING) need numbers; he wants to compare versions and pick the better parts (arena pattern, STATE item 25).
- **How.** One row per template version, per scenario and case (worst, realistic, best): survival (floor touches per 1,000 runs at half edge, worst loss as a share of buffer, accumulation per dependency, margin headroom at the worst point); growth (final equity against the unstressed run and against the dry chassis; the cost of conservatism, A5-073: idle exposure and the return it missed); brakes (fires, precision, recall, detection time, reset time per brake, A2-142; brake-path delta against the price path; the trip tax); operator load (pages and tickets per month); per class and per style breakdowns. A PASS or FAIL release gate per profile version on the survival rows (A4-097), and a comparison against the previous version on every row (the canary). Separate scorecards for rules followed and money made (A4-139).
- **Levels.** All. **Ledger.** `scorecard_survival_gate`, `brake_path_delta_r`, `trip_tax_record`, `cost_of_conservatism_r`, `brake_precision` (v0).
- **Performance and survival.** This is where "performance with intention, not just safety" becomes a number next to the survival number.
- **Evidence.** SRE alert scorecards and canary practice (read, R3 §3.5, R7 §4). Weakest link: no QMX version has a scorecard yet.
- **Maturity.** solid.

### X4-scenarios-98. Reverse stress and "the scenario that breaks us"

- **Components.** A3-153, A3-231, A5-090, A5-088, A5-089, A3-157.
- **Need.** The catalogue is a list of what we thought of; reverse stress finds the failures we did not (R4 technique 15); the book's own history says which days actually hurt (R8 §3.3).
- **How.** Two jobs. Model-driven: search the plausibility region (a Mahalanobis distance of k sigma over the book's factor exposures) for the worst loss, at several k, and report which factor combination produced it (R8 §3.2, Breuer et al.). Data-driven: from the harness's simulated history and later QMX's own, take every day the book lost more than X and average the factor moves on those days (R8 §3.3, Glasserman et al.); publish it as a scenario card. Both run weekly; a new worst case becomes a scenario record (96) and a candidate for a new per-dependency limit.
- **Levels.** BMS. **Ledger.** `reverse_stress_k_sigma`, `reverse_stress_loss_threshold_r`.
- **Performance and survival.** Finds the empty cell in the solution matrix before the market does; an agent-tuned book that passes the named scenarios is caught by the unnamed ones.
- **Evidence.** Snippets of two published methods; no QMX run. Weakest link: elliptical plausibility understates joint tails (R8 §3.2).
- **Maturity.** plausible.

### X4-scenarios-99. The interactive bench for crowding among QMX's own units (wild)

- **Components.** A5-059, A5-060, A5-062, A5-063, A3-173, A2-147, A3-165, A3-166.
- **Need.** A rule can look safe against a fixed tape and fail when other agents react (R4 technique 21: a 9.2 % crash became 17.3 % with 400 reactive agents). QMX's own units are such agents to each other once there are many of them on one broker; the August 2007 case (65) is the historical version.
- **How.** Production units behind an exchange adapter in an agent-based market (ABIDES-style) with adaptive liquidity providers and switchable amplification channels (CrashGym-style); paired-seed ablation (A5-059): the same shock with QMX's units reactive and frozen; a no-edge agent-based market as the null (A3-173). Two gates before the simulator is trusted: stylised facts on held-out data, then closed-loop response to injected orders (A5-060). Used to compare rules, never to forecast P&L.
- **Levels.** BMS and methodology. **Ledger.** `bench_amplification_delta`, `simulator_realism_gate_pass`.
- **Performance and survival.** The only way to see QMX's units crowding each other before live; the cost is a calibration nobody has done for a multi-asset retail book.
- **Evidence.** Research simulators, equity-only or synthetic (R4 technique 21). Weakest link: calibration to cTrader and Hyperliquid markets does not exist. Wild by the brief's definition; kept.
- **Maturity.** wild.

---

# Part 1c. Component links for scenarios 01 to 37, and the ledger id mapping

Scenarios 01 to 37 were dissected by Stage A as components `A3-191` to `A3-227` (one per scenario, in order). Their links to the rest of the catalogue:

| Scenario | Links (short ids) |
|---|---|
| 01 | A3-146, A3-149, A3-158, A3-161, A1-115, A2-026, A3-177 |
| 02 | A3-046, A3-049, A1-129, A3-088, A3-089, A3-101 |
| 03 | A1-115, A1-135, A3-163, A5-064, A1-105 |
| 04 | A3-164, A2-188, A2-149, A5-098 |
| 05 | A1-068, A5-116, A5-118, A5-138, A2-026 |
| 06 | A1-086, A1-107, A1-130, A2-115, A4-059 |
| 07 | A2-028, A2-166, A1-138, A2-174 |
| 08 | A3-095, A3-096, A3-098, A3-106, A3-107, A3-115, A2-121 |
| 09 | A3-109, A2-123, A2-030, A3-181 |
| 10 | A3-110, A1-111, A3-106 |
| 11 | A3-108, A2-120, A3-126, A2-104 |
| 12 | A2-119, A3-107, A2-009, A2-022 |
| 13 | A3-113, A4-104, A3-086 |
| 14 | A2-122, A3-103, A3-096, A2-097 |
| 15 | A3-127, A3-125, A3-131, A3-067 |
| 16 | A3-133, A3-129, A3-101, A3-111 |
| 17 | A3-131, A3-130, A3-124 |
| 18 | A3-132, A3-128 |
| 19 | A3-085, A3-068, A3-237, A1-150 |
| 20 | A2-101, A2-144 |
| 21 | A3-131, A3-125 |
| 22 | A3-036, A3-035, A3-038, A2-064 |
| 23 | A3-030, A1-118, A1-116 |
| 24 | A3-114, A3-040, A3-058, A2-102 |
| 25 | A3-025, A3-018, A3-028 |
| 26 | A3-026, A3-039, A3-022, A2-064 |
| 27 | A3-023, A3-181 |
| 28 | A3-022 |
| 29 | A2-116, A2-083, A2-011 |
| 30 | A2-124, A4-036, A4-028, A5-127 |
| 31 | A3-167, A3-097, A2-117, A2-118, A2-104 |
| 32 | A3-075, A2-111, A2-121, A3-098 |
| 33 | A2-264, A3-144, A3-141, A2-072 |
| 34 | A2-264, A3-096, A3-097 |
| 35 | A1-129, A3-048, A5-091, A2-097, A2-098 |
| 36 | A2-104, A2-060, A3-083, A3-011 |
| 37 | A2-119, A3-168, A2-008 |

**Ledger id mapping.** The draft was written before ledger v0 existed. Stage B mapped its ids onto v0 where the idea already exists there; the text above now uses the v0 ids. The mapping, for the funnel: `buffer_before_floor` → `bms_buffer_before_floor`; `protect_retry_max` → `protection_retry_max`; `feed_stale_after_s` → `feed_stale_after`; `sqs_ratio` → `sqs_score`; `sqs_block_threshold` → `sqs_hard_block_threshold`; `gap_through_stop` → `gap_loss_beyond_stop`; `news_window_pre_min` → `news_blackout_before`; `news_window_post_min` → `news_blackout_after`; `news_impact_map` → `news_impact_level_map`; `calendar_stale_after_h` → `news_calendar_max_staleness`; `session_handover_buffer_min` → `session_handover_buffer_width`; `book_day_loss_budget` → `period_loss_budget`; `bms_day_loss_budget` → `bms_daily_loss_limit`; `effective_units` → `effective_independent_bets`; `cost_target_r` → `unit_cost_target`; `day_boundary_source` → `day_boundary`; `isolation_resume_rule` → `isolation_end_rule`; `bms_breaker_rule` → `bms_circuit_breaker`; `isolation_evidence_threshold` → `market_isolation_trigger`; `count_brake_window` → `circuit_breaker_window`; `scenario_event_window` → `loss_event_window`; `unit_equity_share` → `unit_capital_share`; `equity_series` → `brake_equity_basis`; `cost_drift_alarm` → `cost_drift_multiple`; `swap_cost_input` → `swap_financing_cost`; `session_windows_zone_source` → `session_windows`; `staged_exit_fraction` and `staged_exit_interval_s` → `soft_kill_exit_schedule`. Every other id named in Part 1 is new and lives in `ledger/additions/X4-scenarios.yaml`.

---

# Part 2. Problems and solutions

Run with `bmad-cis-problem-solving`, non-interactively: problem statement, boundaries (is / is not), root cause, forces and constraints, at least two options with trade-offs, the evaluation, and how the harness validates. He wants solutions, not lists (E25, E28). No time estimates.

### P1. How long is "one event"? (the event window length per driver)

- **Problem.** The hours clause needs a window; too short and a correlated hit counts as five strikes, too long and two separate losses merge and the second one is hidden from the brakes.
- **Is / is not.** It is a book and BMS question about a driver (USD, risk-off, a class). It is not a unit question; a unit never sees it. It happens on co-moves; it does not happen on independent losses.
- **Root cause.** No measure of co-move duration exists in QMX; insurance borrowed the number from physical events.
- **Forces.** For: the brake precision record will show the cost of each error. Against: QMX's own co-move history is days old.
- **Options.**
  - (a) Class defaults from public history (FX minutes to an hour, indices a session, crypto hours), refined per driver by the harness's error record. Cheap, explainable, wrong at first.
  - (b) A state-based window: opens on the first tagged loss, closes when the driver's tells (spread, volatility, co-move score) are back inside their band, with a maximum. No number to guess, but it depends on the tells being right, and a tell that never clears holds the window open all day.
  - (c) Both: the state rule with the class default as the maximum.
- **Evaluation.** (c) wins on asymmetry: one number per class, a rule that explains itself, and a cap. (b) alone fails on a stale tell. (a) alone fails on the first new driver.
- **Validation.** The harness replays every co-move in the rk5 list and in calm history: strikes counted per unit under each option; merged separate losses per option.

### P2. How severe is a historical shock on a $500 book? (the severity scale)

- **Problem.** The SNB unpeg was a 20 % move; on a $500 account with a 0.3 % stop the question is what it does to each unit, each book and the floor, and the answer depends on how the scenario is scaled.
- **Is / is not.** It is a harness question. It is not an account-size question in research (M33: research is not anchored to a dollar budget); the scale must be in R and in cushion shares.
- **Root cause.** Two scales exist and neither is declared: price moves (in sigma or percent) and losses (in R per unit and in cushion share per book).
- **Options.**
  - (a) Scale in price: the shock is a price path per instrument; each unit's loss follows from its stop and gap. Honest, but a small book sees the same percentage loss whatever its size (fine) and the floor question depends on the seed (he wants the seed open, C30).
  - (b) Scale in R: the shock is "k R per unit, with correlations raised"; fast, size-free, but it hides the gap-through-stop and the min-lot effects that are the whole point of scenarios 25, 31 and 41.
  - (c) The SPAN grid per instrument (A5-093): moves of one, two and three thirds of a volatility-based scan range, plus a 3x extreme counted in full; the harness runs the grid on every open position and the historical list on top.
- **Evaluation.** (a) plus (c): price paths for the named shocks, the grid for every instrument every day. (b) is kept as the quick table the funnel reads.
- **Validation.** The same scenario under (a) and (b) on one book: where the R-scaled answer differs from the price-scaled one, the grid names which instrument's gap or lot step caused it.

### P3. What fills the factors a scenario does not stress, when QMX has no history?

- **Problem.** The conditional fill (R8 §3.1) needs a factor model or similar past days; QMX's live history is weeks.
- **Is / is not.** It is a harness-engine problem for year one. It is not a problem for the price-path replays (history fills itself).
- **Root cause.** Short history and a book that spans seven classes.
- **Options.**
  - (a) Pool: a class-level factor model from public daily data (USD, equity beta, oil, crypto beta, rates), with pooled volatility dynamics (A5-097) and each instrument's own level; fill = conditional mean under that model; labelled "pooled, assumption".
  - (b) Nearest neighbours: the 20 most similar days in public history by the stressed factors' values; fill = their average; labelled.
  - (c) Zero, as a declared worst case beside the conditional fill, never as the only number.
- **Evaluation.** (a) for the standing set, (b) for the named shocks, (c) shown in the band's label so the naive number is visible. The harness replaces all three with QMX's own history as it grows (the daily backtest, A5-089, measures when the pooled fill is worse than the own-history fill).
- **Validation.** Coverage of the predicted band against realised P&L in the nightly backtest, per fill method (the paper's own test: naive intervals covered less than 10 % in extreme cells against a 50 % target).

### P4. Which dependencies does the book share, and what is the concentration limit per dependency?

- **Problem.** A book can look diversified by correlation and be one outage from a joint loss (R8 §3.4). The list of dependencies and the limit per dependency are unwritten.
- **Is / is not.** It is BMS and node accounting. It is not a price risk.
- **Root cause.** No generation modelled accumulation by cause; April's open risk was risk at the stop (G11 §2.1).
- **Options.**
  - (a) A fixed dependency list (broker and venue, price feed, compute host, clock, signal family, macro factor, scheduled event, session and rollover) with a limit per dependency as a share of open risk, expert-set and labelled, as the insurers do when data are scarce (R8 §3.4).
  - (b) Derive each limit from the dependency's failure loss: limit = buffer before the floor ÷ loss if the dependency fails (a feed outage with broker-side stops costs the stops; without them it costs the gaps; a signal family failing costs its stress loss). The derivation is visible and he can change it (D46).
  - (c) A single broker and feed for now, so the only dependency limits that bind are signal family and macro factor; the rest are "100 % by necessity" and listed as such on the screen, which is honest and shows what the second broker buys.
- **Evaluation.** (b) with (c)'s honesty: derive where a failure loss exists, show "100 % by necessity" where it does not, and let the number itself argue for Hyperliquid and a second feed.
- **Validation.** The accumulation report on the harness's book: which dependency binds first; the loss under each dependency's failure scenario against the limit.

### P5. Which engine simulates the brakes inside the path, and in what order do controls act on the same tick?

- **Problem.** Running QMX's own brakes inside a scenario needs the guard's logic in the simulator, with the same rank table as live, or the simulation proves a different system.
- **Is / is not.** It is an engine and architecture question (X1 owns the guard's shape). It is not solved by QMB's what-ifs, which filter trades and never resize (G8 §5.3).
- **Root cause.** No sizing-only or brake-only replay exists (G8 "what blocks it" 10); the rank on the same tick exists in Gen 3 docs (A4-103) and nowhere in code.
- **Options.**
  - (a) The guard module itself, imported into the harness, driven by the scenario's bars and fills: one code path for live and simulation (A4-184's "the same compiled unit and guard run on his PC and on the node"). Honest; slow; needs the guard built first.
  - (b) A light Python harness that re-implements the brakes from the ledger (every brake row carries its signal, anchor, trip, clear and speed, R9's nine attributes). Fast now; two implementations drift apart.
  - (c) QMB's resize replay (A4-186, A2-141) for the sizer and the trade-list cases, plus (a) for the brake-path cases.
- **Evaluation.** (c), with (b) only until the guard exists and with a conformance test that the two agree trade by trade on a fixed tape (the B12 conformance pattern). The rank on the same tick is one declared table (scenario 59) read by both.
- **Validation.** The conformance test; the brake-path delta on the unwind scenario (65) under each engine.

### P6. Where is the bar for isolation precision and recall?

- **Problem.** A noisy isolation is muted (R3 §3.6); a deaf one lets the SNB through. The bar is unset.
- **Options.**
  - (a) Recall first: every shock in the rk5 list plus the catalogue's class shocks must be caught; precision then falls where it falls and is shown. Safe, costs trades.
  - (b) Precision first: the false-isolation rate on two years of calm history must sit under a bar (say most fires followed by a real class loss inside the window); recall then falls where it falls. Keeps the frequency thesis, misses shocks.
  - (c) A trip-tax budget: isolation may cost at most X % of the class's net R per month in missed entries, and inside that budget the rule with the best recall wins. Turns the sweet spot into one number he can move.
- **Evaluation.** (c), with recall on the named shocks as a hard floor (a rule that misses the SNB is out whatever its precision).
- **Validation.** Precision, recall, detection time and reset time per isolation rule on history (A2-142), and the trip tax (A4-202).

### P7. What does the system do when he does not answer?

- **Problem.** Only he lowers the kill switch and promotes; the unit build makes every risk stop wait for him; he will be away. Scenarios 74, 77 and 85.
- **Options.**
  - (a) Everything that waits for him keeps waiting; the book goes dark on the first such event. Safe, the sitting duck.
  - (b) Routine brakes clear by rule with retry-then-lockout; the kill switch, promotion and lockouts wait for him; an absence policy he sets in advance says how dark "safe" is (no new entries after flat; or level 1 under every brake).
  - (c) A delegated acknowledger (a second person or an agent with a narrow grant) can acknowledge pages, never lower a kill level.
- **Evaluation.** (b); (c) is a QMA question, flagged not designed (STATE item 26).
- **Validation.** The week-without-clicks replay under each policy (scenario 74).

### P8. Likelihood and severity are guesses

- **Problem.** L1 to L5 and S1 to S5 are the author's judgment. The funnel will weight scenarios by them.
- **Options.**
  - (a) Count on history: for each scenario family, fires per live month on the public history the harness replays (news releases, spread events, gaps, halts) and on the node's own logs (link drops, restarts, bad ticks). Honest where history exists.
  - (b) Expert-set and labelled, revised by the harness's error record and the live journal every month (the insurers' way when data are scarce).
  - (c) Both, with the label "measured" or "assumed" on every scenario card and the funnel told to discount assumed ones.
- **Evaluation.** (c).
- **Validation.** The scenario card's likelihood against the journal's count after three live months.

### P9. How to measure the demo-to-live gap before there is live

- **Problem.** Scenario 38 needs live fills; the stack trades only demo and testnet (G9 §3.3).
- **Options.**
  - (a) Demo fills from the node's order rows now (the script G9 §3.4 says is missing), labelled "demo", as the first calibration; live replaces it fill by fill.
  - (b) Public measures of retail FX and crypto execution (R4 technique 16: conditional passive-fill odds, slippage-at-risk from visible depth) as a prior, shrunk toward QMX's own measure as it grows.
  - (c) Run the first live units at level 1 for the explicit purpose of measuring (proof continues at the smallest live size, A2-218).
- **Evaluation.** All three in that order; (c) is what level 1 is for.
- **Validation.** The demo-to-live slippage ratio per instrument and hour after 50 live fills.

### P10. How do we know a family is missing from the catalogue?

- **Problem.** A catalogue is what its authors thought of.
- **Options.**
  - (a) The solution matrix (families against components, Part 7): an empty row or column is a gap; the matrix is rerun whenever the component catalogue grows.
  - (b) Reverse stress (idea 98): the failures the search finds that no scenario names become scenarios.
  - (c) The live journal: every stand-down, risk stop, page and manual override is matched to a scenario id; one with no match is a new scenario.
- **Evaluation.** All three; (c) is the cheapest and runs itself.
- **Validation.** The share of live events with a scenario id, per month.

---

# Part 3. Collisions

Named, not resolved. The funnel judges.

1. **Count brakes.** Scenario 62 and R9 §4.1 want money brakes at the unit's own percentile and count brakes scaled to frequency; his A6 wants "brake at about three or on a pattern" and his E27 says the brake set is circumstantial. X3 owns the brake redesign; X4 only says what each scenario needs the brake to do.
2. **Automatic resume against "waits for his click".** Scenarios 12, 71, 74 and 85 resume benches and isolations by rule with retry-then-lockout; the unit build makes every risk stop wait for him (G10 §1.6, L0:375). Both cannot stand.
3. **Fail closed against fail open.** Scenarios 61 and 82 want context needs and window ends to fail closed; the board read fails open by design (G9 §4.3) and X1 names the same collision (X1 collision 9).
4. **The event window against the count brakes.** Scenario 01 counts five losses as one event; a per-unit count brake sees five. Which ledger a unit-level brake reads during a book-level event is undecided (A5-145's two ledgers help; the scope rule is X3's).
5. **House money windowed and capped (scenario 05, 63) against his A21 "keep house money".** The windowed version is a different rule from the April one; it may read to him as losing it.
6. **The floor-hit action (69, 88) against "the floor is almost never touched" (C10).** The scenarios design for the day it is touched; he has ruled on the frequency, not on the action. C12 is open.
7. **The BMS budget scaled by open breadth (24, 93) against "each unit keeps its full size" (the lead's units table, SEEDS replies row 6).** A weekend-scaled budget changes a crypto unit's size by the clock; the frequency thesis and the breadth scale pull apart.
8. **Isolation by class (08) against placement by the MIS (61).** Two mechanisms narrow a unit's markets; one is a brake with a TTL, the other a router word; a unit may be off by one and on by the other.
9. **Scenario 42's size sanity band and scenario 53's per-trade cap against X1's "a unit stands alone".** Both clamps live in the guard outside the unit; X1 must own that the guard may refuse what the unit decided.
10. **Scenario 55's switch-only-when-flat against the identity table (G8 §3.6).** A new version that waits for flat may wait a week for a swing unit; the table has no notion of time.
11. **Scenario 57's proposal bounds against D42 ("the sky's the limit").** A de-risk-only door by default limits what agents can propose; X7 owns the door.
12. **Scenario 66's level-1 live while proof is pending against X5's C2 (he clicks a unit live before its edge is proved).** Same collision, two layers.
13. **Scenario 90's engine (P5) against G2 rulings that nothing a unit needs may depend on the Library or the PC at trade time.** The harness runs off the node and must never be mistaken for a live dependency; X1 names the seam.
14. **The scenario record as a Library kind (96) against "he wants no files from agents" (STATE item 25).** A scenario record is data the harness reads, not a report; the funnel should say which it is.
15. **Within X4.** Scenario 20 ("exits are never blocked") against 52 (a venue's worst-price cap rejects an exit) and 33 (a halt suspends the stop): the rule holds for QMX's controls, and the market can still block; the scenario text says so, the invariant row in the ledger should too.
16. **Within X4.** Scenario 65 wants "no new entries, never flatten" for a family losing everywhere; scenario 14's BMS breaker flattens when the floor buffer is threatened. The join (which wins at the buffer) is the rank table of scenario 59, which X1 owns.

---

# Part 4. Restructure proposals

Where this layer says a level, a part of the stack or the Book/BMS shape should change, and why the replacement performs better. Opinions, **[judgment]** throughout.

1. **Replace calendar-day count brakes with rolling money brakes at the unit's own percentile.** Scenarios 29 and 62. Performs better: the false-fire rate stays steady across styles and frequencies, so no healthy unit is benched for a normal day, and the fire density is then real decay evidence (G10 §7.1-7.2). Survival is unchanged or better: the percentile money brake fires on 1 to 3 % of days at any trade count (R9 §4.1).
2. **Make scope a first-class key in the kill switch and the stand-downs: class, region, currency, underlying group, beside instrument and deployment.** Scenarios 08 to 14. Performs better: a Tokyo event switches off JPY, not the book; the frequency thesis keeps every other class trading. The shipped shape has the hooks (G9 "What his ideas could hang on").
3. **Add one guard module on the host, outside every unit, that holds the clamps and the rank table.** Scenarios 42, 53, 54, 59, 67. The unit never sizes itself safely; the guard refuses, shrinks or passes with a receipt naming the binding control. X1's idea 12 is the same seam; X4 adds the invariants it must hold (per-trade worst-case cap, order rate, margin headroom, stop side, size sanity band, exits never blocked).
4. **Replace "every risk stop waits for his click" with retry-then-lockout.** Scenarios 71, 74, 85. Performs better: routine benches cost the rest of the day, not a week; survival is kept by the lockout and by leaving the kill switch his.
5. **Scale the BMS day budget with open breadth, and show N_eff beside the unit count.** Scenarios 24, 64, 93. Performs better: a weekend does not spend a weekday budget on two crypto units; a crowded open is not funded as ten bets.
6. **Make the node emit a RiskState row every pass** (A4-152): equity series, drawdown, open risk, exposure per driver, budget used, each brake's distance to trip, the trading state, the kill level now. Every scenario's "operator" line needs it; G11 §4 shows nothing on the node carries it. This is X6's deliverable; X4 lists it because no scenario can be verified live without it.
7. **Scenarios as a Library kind and the harness as a nightly job**, not a one-off study: the daily backtest of the stress engine against yesterday (idea 90 rule 6) is what keeps the catalogue honest.
8. **Replace the per-unit "start equity plus own results" sizing basis with a refreshed budget share per deployment** (A1-130). Scenario 06. Performs better: three books on one account net correctly; no unit sizes from money another unit lost.
9. **Replace the Book/BMS budget shape's single day budget with a budget that drains once per event window and renews at a declared boundary with a bench rest.** Scenarios 01, 29, 71. The Book's "drain and refuse" (G6 §3.6) is kept; what drains it is defined.

---

# Part 5. Gaps

What no component covers, found by the solution matrix (Part 7).

1. A co-move duration measure per driver (P1). Nothing in A1 to A5 measures how long one shared move lasts.
2. An account lease and a double-owner check for two nodes on one account (scenario 49). The nearest is A2-067 (a pause as a shared resource).
3. A dead-man rule and an absence policy (scenarios 74, 77). Pages have deadlines in A4-201; nothing says what runs at the deadline.
4. A reconcile that reads the venue's deal history, not only open positions (scenario 83).
5. Mark-against-last divergence as a stand-down (scenarios 52, 80). A3-235 is population-level flow; nothing reads the venue's own price split.
6. A journal-write fail mode (scenario 50). A4-058 declares fail modes for inputs, not for the journal itself.
7. A size sanity band against the unit's own usual lots (scenario 42). A2-003 vetoes worst-case loss; nothing compares to the unit's history.
8. The roll-and-report joined window for energy (scenario 89). A5-094 and A3-143 have the parts; the join is new.
9. A measured likelihood per scenario (P8). No component counts scenario fires.
10. A sweep's anchor re-derivation (scenario 72). A1-076 and A2-077 describe the sweep; nothing says what every cushion rule does at the boundary.
11. The harness engine itself (P5): no sizing-only or brake-path replay exists in QMB or anywhere (G8 "what blocks it" 10).

---

# Part 6. Questions only he can answer

Kept short; the technical questions were researched above.

1. **Money (numbers lens).** At the floor: stop the pot until a re-seed, or trade one feasible FX micro unit at level 1 until the cushion rebuilds (scenario 69, C12)? Both are designed; one is the default.
2. **Irreversible scope.** May a bench or an isolation clear by rule with retry-then-lockout, so that only lockouts, the kill switch and promotion wait for his click (scenarios 71, 74)? The unit build says every risk stop waits for him.
3. **Vocabulary.** "Event window", "isolation", "trip tax", "absence policy", "scenario card": his words for these, since the screen and the agents will use them (D37).
4. **Scope.** The absence policy's default while he is away: dark after flat, or level 1 under every brake (scenario 74)?

---

# Part 7. Method notes: the headless brainstorm, the solution matrix and the selection rule

The brief's techniques were run headless (memlog in `linking/stage-b/X4-scenarios/.memlog.md`; intent artifact only, no HTML, per M31).

- **Morphological Analysis.** Parameters: level (trade, unit, book, methodology, BMS, account, node, operator) × trigger family (financial, execution, system health, behaviour, calendar, capital, human) × class (seven) × brake kind (R9's nine) × accelerator state (off, on). Scenarios 38 to 89 are the untried cells; the old draft covered the financial and calendar columns, the new families cover execution, system health, behaviour, capital and human.
- **Concept Blending.** Hours clause + scenario = the event window (91). Canary release + scenario = the harness as a release gate per profile version (90, 97). Reinsurance reinstatement + re-seed = the priced re-seed (73). Dose escalation + version change = slow start after every version (55, 86).
- **Forced Relationships.** Heparin dead band ↔ isolation resume (a settling time before the next change, 12, 94). Grid selectivity ↔ which brake trips first on the same tick (59). Account lease ↔ database writer locks (49).
- **Cross-Pollination.** Aviation alerting (one page at a time, a deadline per page, 76, 77). Lloyd's RDS (a mandatory set plus own, 96). CME SPAN (a per-instrument grid, 90). Google SRE (burn rate, page against ticket, 07, 14). Hospitals (precision record, 09, 94).
- **Trait Transfer.** From exchange breakers: per-product pause, market-wide stop, bands that move (08, 14, 31, 34). From Topstep tiers: dwell, same-day step-down, no skipping (63). From Kubernetes: cut fast, grow slow, missing data is no change (46, 60).
- **Evolutionary Pressure.** Variants of each scenario's "correct outcome" were bred under one selection rule: *survives at half the believed edge with ten units, and loses less than 20 % of the ρ = 0 growth*. Variants that survived by trading less (the sitting duck) were culled; variants that grew by leaning on the edge number were culled. What survived is the "Correct outcome" line of each scenario.
- **Solution Matrix.** Families A to M against the component clusters (sizing, brakes, structure, agents and telemetry, top-up). Empty cells became Part 5. The densest cells (isolation, event window, same-bet) are where the draft already was; the emptiest (infrastructure, operator, capital boundary acts) are where Stage A found least.

---

# Appendix A. The roundtable (party mode, session mode, non-interactive)

Personas chosen for this layer: **Dara**, a pod-shop risk manager; **Kofi**, a retail scalper who has blown two accounts; **Ines**, a platform engineer who ran a trading node through two outages; **Mubarak's voice**, taken from his words (SEEDS, M5 to M40); **Yara**, the numbers-lens quant who will run the harness. One mind behind every voice; no party memory file written outside the doc workspace.

Dara: Your catalogue has ninety scenarios and one question: how much do I lose when they all happen in the same week. Show me the accumulation table, not the list.
Yara: That is rule 2 of the harness. Per dependency: broker, feed, host, signal family, USD. Today it reads 100 % on broker and feed, by necessity. The number argues for Hyperliquid better than any of us.
Kofi: You lot keep saying "brake". I had brakes. Two stops a day and I was out by 10:30 most days, then I watched the afternoon pay everyone else. The brake was the account killer.
Mubarak's voice: "Having two stops in a full day, like, that's for the old system." And "just by chance" does not hold, because the cuts are small. Count them right.
Yara: Sixty-two does. A money brake at your own worst-day percentile fires one day in fifty whether you trade four times or forty. The count brake fires on forty percent of your days at ten trades. We can show you the table.
Kofi: And the day it fires for real?
Yara: It is the same day the count brake fires. The difference is the forty-nine days it does not.
Dara: Fine. Sixty-nine. Equity three-thirty, floor three hundred. What trades?
Yara: Nothing whose normal drawdown is bigger than thirty dollars. Eighty-eight makes that a test: the cushion must cover the unit's own ninety-fifth percentile at level one, or the unit does not trade.
Mubarak's voice: "I'd rather give units part of the seed and let them grow than leave three hundred idle." The sitting duck.
Dara: Then the floor is not three hundred. If you want to trade at three-thirty, the floor you actually hold is two-sixty and you should say so. A floor you will not defend is a number on a screen.
Mubarak's voice: "The floor should almost never be touched." "Losing two hundred in a day is stupid."
Ines: Can I say the thing nobody wants to hear? Forty-five, forty-six, forty-eight, fifty. The broker-side stop is the only brake that works when my box is dead. Everything else in this catalogue runs on a process that restarts five times in ten minutes and then waits for him.
Dara: Which is why seventy-four exists.
Ines: Seventy-four is a policy he sets before he leaves. He will not set it. He will leave.
Mubarak's voice: "For the technical part, I don't think you really need me."
Ines: Exactly my point. So the default absence policy has to be the one he would pick if he were here: dark after flat. Not level one. Dark.
Yara: The harness can price both. A week dark costs the week's expected R; a week at level one costs the week's worst case at level one. He reads two numbers and picks.
Kofi: Sixty-three. House money. I pressed after a streak and gave it all back on the next trade every single time.
Yara: With independent trades no accelerator beats a fixed size. Nine's script says so. House money paid in R9 only when the regime persisted, and your streaks did not.
Mubarak's voice: "Keep house money." "Brakes first, accelerator second."
Dara: Then house money funds extra size only from today's realised profit, capped at a share of it, off during any window, and the book caps the total. That is not house money, that is a budget with a bonus pool.
Mubarak's voice: "Reverse house of money was my idea." One ledger, one anchor. Sixty-three keeps it.
Ines: Ninety. You want to run the guard inside the simulator. There is no guard. There is a runtime with a fixed check order for refusals and nothing for size.
Yara: P5. The light harness reads the ledger rows until the guard exists, and a conformance test on one tape says when the two agree. If they never agree, the simulation proved a different system and we say so.
Dara: What I like about ninety is rule six. The engine backtests itself every night against yesterday. Every stress engine I have used was right about the crisis it was built after.
Kofi: What I like is that you kept the bare sim as a row. I want to see what the brakes cost me on the good days, not only what they saved on the bad one.
Yara: The cost of conservatism is a column. Seventy-three in the top-up catalogue.
Mubarak's voice: "I don't want just safety. I want something that can perform."
Dara: Then the floor is not touched because the per-driver cap is sized to the gap, not because the units are small. Ninety-two. Everything else in the book stays at size.
Ines: And forty-nine. One account, one writer, a lease with a fence token. I have seen two nodes on one account. It was not a scenario, it was a Tuesday.
Yara: It is plausible, not solid, because nothing in the catalogue has it. Gap two.
Kofi: Last thing. Sixty-two says the screen shows "normal drawdown, eleven R of a twenty-seven R median". If the screen had said that to me in March I would still have the account.
Mubarak's voice: "The UI must show what is wrong, right, working, up, on and trading."
Dara: Then that is the first thing X6 builds. We are done; the harness decides the rest.

What the room surfaced that no one voice had: the floor he will not defend is the floor he does not have (69, 88); the default absence policy must be the conservative one because he will not set one (74); and the accumulation table is the argument for the second venue (90, P4).
