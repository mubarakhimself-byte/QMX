# X3: brakes, restores, exits and drift (Stage B, linking)

File id: `X3-brakes-exits-drift`. Written 2026-11-03 by the X3 Stage B agent. Expansion, not a decision: nothing here is ranked or ratified. The Fable funnel judge ranks (`linking/RANKING.md`).

## 0. How to read this

**Paths.** All under `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. Components are cited by their Stage A ids (`A2-093` means `A2-brakes-drift-exits-093`; `A1-`, `A3-`, `A4-`, `A5-` likewise). The method record is in `linking\stage-b\X3-brakes-exits-drift\`:
- `.memlog.md` (the brainstorm log), `brainstorm-working.md` (the seven techniques), `brainstorm-intent.md`;
- `problem-solving.md` (diagnosis per problem), `party-mode-roundtable.md` (the stress round);
- `x3_brake_sim.py` and `out-200.txt` (the arithmetic below).

**Words.** Brake, accelerator, restore and clamp as R9 defines them (`research\R9-accelerators-and-brake-pairs.md` §0.2): a brake holds risk at or below the unit's declared baseline on evidence of danger; a restore is the brake's own way back to baseline, never above it; a clamp is a fixed bound that reads no evidence. FI means fast invalidation. "Own percentile" means a level read from the unit's own frozen record (its card or holdout), not a number typed by anyone. "Bench" means no new entries for the rest of the brake's window; exits keep running. "Shadow" or "metrics only" means a brake that records what it would have done and acts on nothing.

**Labels.** **[judgment]** is my opinion. **SIM** is my own arithmetic (below). Evidence words follow Stage A: live, controlled test, author backtest, simulation, idea, old QMX rule.

**New kinds this layer adds to R9's taxonomy** (R9 invited extensions):
- **Sentinel**: a brake that reads another brake's fire record, not P&L, and acts slowly (H08).
- **Probe restore**: a restore that tests the danger is over with a few small trades judged as a group (H15).
- **Certificate**: a gate on brakes themselves; a brake must beat a random brake of equal fire rate before it may act (H13).
- **Choke budget**: a clamp on a brake's own healthy fire rate (H65).

### 0.1 The arithmetic (SIM)

`x3_brake_sim.py`, standard library, 200 paths per scenario, 250 trading days, size 1 per trade in R, costs netted into the outcomes. Units: `fs10` (55 % wins at 1:1, 10 trades a day), `fi10` (same edge, half the losers cut at -0.3R), `fi40` (the same at 40 a day), `be4` (intraday with 15 % breakeven scratches, 4 a day), `orb2` (40 % wins at +2R, 2 a day). Scenarios: healthy; decay (edge turns to -0.05R at day 100); a bad week (days 100-104 at about -0.15R); bad spells (good spells about 100 trades, bad about 50). Model limits: independent trades inside a state, no gaps, no fat tails, one unit at a time, thresholds calibrated on a long healthy record (an honest card).

| Brake (bench for the rest of the day unless said) | Healthy R kept, fs10 / fi10 / fi40 / be4 / orb2 | Healthy fire days |
|---|---|---|
| 2 full stops a day (the old breaker) | 43.8 / 65.3 / 18.1 / 87.8 / 100 % | 36-100 % |
| 3 losses in a row | 83.9 / 74.6 / 27.8 / 98.2 / 100 % | 0-98 % |
| 3 in a row, halve instead of bench | 91.9 / 87.3 / 63.9 / 99.1 / 100 % | same |
| Loss points (FI cut costs its size) at own p99 | 100 / 99.9 / 100 / 100 / 100 % | 0.4-2.0 % (36 % at orb2, where it can only fire on the last trade) |
| Money at own p1 of the running minimum, window of 10+ trades | 99.8 / 99.8 / 99.8 / 99.4 / 99.4 % | 1.0-1.2 % |
| Ladder: halve at own p10, bench at own p1 | 98.8 / 98.6 / 97.6 / 97.3 / 98.0 % | 6.3-10.5 % |
| AIMD as a pure brake (x0.7 after a day at own p10, +0.05 per green day, cap 1.0) | 69.4 / 84.0 / 83.3 / 77.7 / 32.5 % | 58-98 % |

Against a random brake with the same fire rate and action, in the bad-spell world: "3 in a row" earned +20.5R (fs10) and +22.5R (fi10) of timing over 250 days, but cost 40-63R on healthy units. Money at own p1 earned +1.2R at 10 a day (noise) and +25.9R at 40 a day. "2 full stops" at 40 a day lost 32.8R to its random twin, because it fires every day and so carries no information. The ladder lifted bad-spell R over no brake (fi40 165 → 208R) and cut the 95th-percentile drawdown (178 → 143R).

Slow lane, every detector set to 5 % false alarms per 250 healthy days:

| Unit | Trade CUSUM: dead edge caught in 150 days, median delay | Fire density: caught, median delay | Alarm within 20 days of a bad week: CUSUM / density |
|---|---|---|---|
| fs10 | 97.0 %, 40 days | 48.5 %, 76 days | 3.0 / 0.0 % |
| fi10 | 99.5 %, 29 days | 58.0 %, 71 days | 2.5 / 1.0 % |
| fi40 | 98.5 %, 10 days | 99.5 %, 36 days | 54.5 / 18.0 % |
| be4 | 91.5 %, 66 days | 52.5 %, 73 days | 4.0 / 2.5 % |
| orb2 | 68.5 %, 99 days | 25.5 %, 93 days | 0.5 / 0.5 % |

Policies in R, fi40: after a bad week, "demote for good at the CUSUM alarm" kept 614R of 950R; "graded and reversible" (half size at half the threshold, paper at the threshold, back as the statistic falls) kept 902R. After a real decay, both saved about the same (380 and 383R against 99R with no slow lane).

**What the arithmetic says [judgment].** A fair fast brake is cheap and fires rarely, but it adds little timing on independent trades: its value is the tail and its fire record. Count brakes buy timing in bad spells at a heavy price on healthy days. The old breaker's fire density is a calm but slow decay sensor; the trade stream is faster. Reversible steps are the cheap way to handle "a bad day".

## 1. The needs this layer serves

| Need | What the template must do | His words (SEEDS) |
|---|---|---|
| N1 | A unit fast brake that is fair to frequency and to FI cuts and breakevens, and does not choke a healthy unit | A6, A28, C31, C33, M33 |
| N2 | The old circuit breaker improved: fast and slow, an expected fire rate, fire density as a decay signal | A26, A27 |
| N3 | Proof that a brake works: random control, precision, its cost | A26, D20 |
| N4 | Restores that let go on evidence, without re-raising into the trip | A25, M33 ("sitting duck") |
| N5 | Cluster (Book) brakes that see losing together | B11, B13, C32 |
| N6 | A BMS breaker and the buffer above the floor | C10, C27 |
| N7 | Market, class and region isolation on evidence; news; SQS | C27, C28, C21 |
| N8 | Account and node brakes; the kill switch and SQS fit | C21, C7 |
| N9 | Exits: stop mechanism per style, FI cut size, the dynamic SL/TP and breakeven, survival exits, exit families | A9, A10, A28, M15 |
| N10 | Live drift: three zones, sequential tests with planned looks, graded demotion, re-promotion, bad day vs broken edge | A25 |
| N11 | Coordination: what wins when many brakes act; fail modes; one spine | C7, B13 |
| N12 | Self-configuring thresholds with a derivation he can change | D29, D46, A13 |
| N13 | Where agents sit near brakes, without touching money | D41, D42 |
| N14 | Performance: measure what brakes cost, so safety does not become the goal | M33 |

## 2. Hybrids

Each hybrid: links, need, what it does and how, levels, behaviour per class and style, ledger ids (existing v0 ids, then ids new to v0 in *italics*: most are added in `ledger\additions\X3-brakes-exits-drift.yaml`; where another layer had already added the same idea, its id is reused, listed in Appendix B), a performance note, a survival note, the evidence chain with its weakest link, and a maturity tag. Numbers H19, H57 and H68 are not used: H19 merged into H15 and H59, H57 into H49, H68 (a probe above baseline) belongs to X2 and is listed under collisions.

### A. Unit fast brakes, fair to frequency and to fast invalidation

#### X3-H01. Own-percentile money breaker (the fast half of the improved circuit breaker) [solid]
- **Links:** A5-144 (money brake at the unit's own percentile), A2-078 (count scaled to trade count), A2-088 (expected fire rate on the card), A2-115 and A4-059 (declared equity series and base), A2-011, A2-064 and A4-061 (persisted counters and day baseline), A2-116 (rolling window, minimum bench rest), A2-108 (session loss in R), A2-227 (thresholds calibrated on the unit's own bootstrap).
- **Need:** N1, N2.
- **What and how:** The unit's running P&L in R over a rolling window of at least ten trades is watched after every close and every mark. When it reaches the unit's own 1st percentile of that window's running minimum, the unit is benched for the rest of the window (no new entries; exits run). The percentile comes from the frozen card: a block bootstrap of the holdout, run through the same brake. A dollar ceiling from his budget clamps the level, so an optimistic card cannot set a loose brake (roundtable, Dana). The brake's job is stated on its row: tail control and evidence for the slow lane, not alpha (roundtable, Ilya).
- **Levels:** unit; the same rule at position scope for multi-position units.
- **Classes and styles:** The rule is class-free because it reads R, not price. What changes per class is the window and the anchor: FX uses the declared FX day (rollover) only for budgets; crypto has no day, so the window in trades is the only clock; indices, stocks and futures need the window to end at the session close so an overnight gap is not counted twice; energy and metals add the event allowance from H75 to marks. Scalpers at 10-40 trades a day get a one-day window; intraday at 4 a day gets about three days; ORB at 2 a day gets about five (SIM); swing units need a window of weeks and lean on H08 instead.
- **Ledger:** `unit_daily_loss_limit`, `session_loss_limit_r`, `breaker_expected_fire_rate`, `brake_equity_basis`, `day_boundary`, `circuit_breaker_window`, `circuit_breaker_reset`; *`money_brake_percentile`*, *`money_brake_window_trades`*, *`money_brake_threshold_r`*, *`money_brake_dollar_clamp`*.
- **Performance:** keeps 99.4-99.8 % of a healthy unit's R at 2 to 40 trades a day (SIM); the old "2 full stops" keeps 18-65 % at 10-40 a day.
- **Survival:** caps the worst run inside a window near the unit's own normal; at 40 a day it also earned +26R of timing in bad spells. It does not stop a slow bleed (that is H08 and H49).
- **Evidence chain:** R9 §4.1 fire rates (simulation) → SIM fire rates and R kept (simulation) → prop and pod rules are all in money (live practice, R9 §4.4). Weakest link: the card's tail is only as honest as the holdout; fat tails and gaps make the live fire rate higher than 1 %.

#### X3-H02. Graded money ladder: REDUCING before HALTED [plausible]
- **Links:** H01, A2-052 and A1-044 (taper to the remaining budget), A2-093 (drawdown pressure), A2-074 and A1-045 (size zones), A2-023 (staged load shedding with three or more set points), A2-112 (trading states), A5-136 (dead band, steps by distance).
- **Need:** N1, N14.
- **What and how:** Two steps on the same window statistic as H01: at the unit's own 10th percentile, halve size for the rest of the window (REDUCING); at the own 1st percentile, bench (HALTED for the window). A third step can be added at the 5th percentile. Every step is one level on the size ladder, so it plugs into the same restore (H15).
- **Levels:** unit; also usable at cluster scope on the Book's window P&L.
- **Classes and styles:** as H01. Where the minimum lot cannot be halved (gold or index contracts at $500), the halve step becomes "skip every second signal" so the money at risk still halves on average **[judgment]**. Scalpers fire the halve step most (6-10 % of days); ORB units rarely.
- **Ledger:** `drawdown_pressure_multiplier`, `size_levels`, `brake_state`; *`reduce_step_percentile`*, *`reduce_step_factor`*, plus the H01 ids.
- **Performance:** keeps 97.3-98.8 % of healthy R; in bad spells it adds +3 to +43R over no brake (SIM).
- **Survival:** cuts the 95th-percentile drawdown in bad spells (fi40 178 → 143R; fs10 133 → 124R).
- **Evidence chain:** NERC staged shedding (live in its own field) → April taper (old rule, never ran) → SIM ladder (simulation). Weakest link: the bad-spell world is my model; real intraday persistence is unmeasured (R9 §2.4).

#### X3-H03. Loss points at the unit's own percentile (FI cuts count by size, breakevens at cost) [plausible]
- **Links:** A2-091 and A1-050 (loss points), A2-090 (qualifying loss at -q), A2-113 (declared counting rule), A5-145 (two ledgers), A2-260 (exit mechanism on the row), his A28 and M12 ("breaks ... also take into account ... first invalidation").
- **Need:** N1.
- **What and how:** Each loss adds its size in R to today's points: a full stop 1, an FI cut at -0.3R 0.3, a breakeven its fees. Wins erase nothing. The unit is benched when points reach its own 99th percentile of daily points. It answers his point that brakes must count FI and exits: a unit that cuts early accumulates points slowly, so it is not punished for the good habit.
- **Levels:** unit.
- **Classes and styles:** class-free in R. Units with no price stop need R from H44's tail-loss budget first. Scalpers: the threshold scales with trade count by itself (fs10 9.0 points, fi10 6.9, fi40 20.5 in SIM). Units with two trades a day cannot use it (it can only fire on the last trade).
- **Ledger:** `loss_points_total`, `loss_points_bench_threshold`, `fast_invalidation_cut_r`, `loss_counting_rule`, `qualifying_loss_threshold_r`; *`loss_points_percentile`*.
- **Performance:** keeps 99.9-100 % of healthy R (SIM).
- **Survival:** weak alone: no timing value in bad spells beyond its random twin except at 40 a day (+10.7R). Pair it with H01 or H02.
- **Evidence chain:** October proposal (old rule, never ran) → R9 two-ledger arithmetic → SIM. Weakest link: the October idea never ran, and trade rows cannot yet tell an FI cut from a time exit (G11).

#### X3-H04. Two ledgers: money for brakes, events for decay [solid]
- **Links:** A5-145, R9 §4.3, A2-260 and A4-150 (exit mechanism and outcome on every row), A2-240 (live MAE and MFE), A2-166 (input-first drift).
- **Need:** N1, N2, N10.
- **What and how:** Brakes act on the money ledger (cuts by size, scratches at cost). A second, event ledger keeps rates: FI-cut rate, scratch rate, full-stop share, stop slippage, time to FI. These rates are not brakes. They feed the slow lane (H08, H49): a rising full-stop share or a falling FI precision says the edge is changing before money shows it.
- **Levels:** trade rows, read at unit and methodology scope.
- **Classes and styles:** FX: rollover swaps booked as cost, not loss; crypto: funding the same; futures: roll costs; stocks: halts tagged. Scalpers depend on it most (FI is their main exit); intraday units with a breakeven ratchet need the scratch rate.
- **Ledger:** `exit_reason_code`, `excursion_mae_mfe_r`, `loss_counting_rule`, `loss_points_total`, `breaker_fire_density`; *`fire_context_tags`*, *`event_ledger_rates`*.
- **Performance:** none direct; it lets brakes stop punishing scratches (counting a breakeven as a loss doubles a count brake's fires, R9 §4.1).
- **Survival:** earlier decay evidence than P&L.
- **Evidence chain:** R9 arithmetic; Gen 3 separate mechanism and outcome fields (docs). Weakest link: the stack's trade row keeps only the fill kind today (G11, G8 §1.4).

#### X3-H05. Streak attenuator scaled to the unit (his "three losses or a pattern", made fair) [plausible]
- **Links:** A2-129 and A1-051 (his A6), A2-092 (old reverse house money), A2-054 (MT5 DecreaseFactor), A2-078, A2-090, A2-251 (0.25x after two losses, crypto replay), Miller-Sanjurjo streak bias (R9 §2.1).
- **Need:** N1.
- **What and how:** A losing run counts only qualifying losses (at or worse than -q, so scratches and small cuts do not count). The trigger is a run longer than the unit's own 99th percentile run for its trade count and win rate, not a fixed three. The action is halve, not bench, and it clears on the next win or at the window end. This keeps his picture ("so that we don't really go with a straight downfall") while removing the frequency flaw.
- **Levels:** unit.
- **Classes and styles:** class-free in R. For a 70 % win-rate mean-reverting scalper the own-p99 run is short (about 4-5 at 20 trades a day **[judgment, from binomial arithmetic]**); for ORB at 40 % wins it is long, so the brake rarely fires and H01 carries the load.
- **Ledger:** `loss_streak`, `reverse_house_money_steps`, `qualifying_loss_threshold_r`, `win_rate`, `trade_rate`.
- **Performance:** a fixed "3 in a row, halve" keeps 87-92 % at 10 a day but 64 % at 40 a day (SIM); the scaled trigger is meant to bring this near H01's 99 % **[judgment, not simulated]**.
- **Survival:** small; useful mainly when runs cluster (H06).
- **Evidence chain:** his idea → R9 count-brake rates → SIM for the fixed version only. Weakest link: the scaled version was not simulated.

#### X3-H06. Conditional streak brake: on only when the unit's results persist [plausible]
- **Links:** H05, A5-121 (block-persistence press-and-ease), R9 §2.2 (block tests find a regime in about 950 trades), A2-135 (random control), A2-249 (stops help with momentum, cost with mean reversion).
- **Need:** N1, N3.
- **What and how:** SIM shows count brakes carry real timing only when losses cluster (+20R over their random twin in bad spells) and cost 16-26 % on healthy days. So the streak brake stays in shadow until the unit's own block-persistence test (correlation of consecutive block P&L, block size near the suspected regime length, tries counted) passes. Then it enforces; if persistence fades, it returns to shadow.
- **Levels:** unit.
- **Classes and styles:** persistence is a property of the unit, not the class. Trend and breakout units are more likely to show it; mean-reverting scalpers less **[judgment]**.
- **Ledger:** `loss_streak`, `brake_state`; *`block_persistence_score`*, *`x1_brake_shadow_mode`*.
- **Performance:** removes the healthy-day cost of a streak brake for units with no persistence.
- **Survival:** keeps the streak brake where it earns timing.
- **Evidence chain:** factor persistence (Ehsani-Linnainmaa, READ in R9) → R9 block arithmetic → SIM timing test. Weakest link: no study measures intraday retail strategy persistence after costs (R9 §2.4); a unit needs about a thousand trades to show it.

#### X3-H07. AIMD day pair with a memory ceiling, as a red-zone survival mode [plausible]
- **Links:** A5-133 (AIMD day pair), A5-134 and A5-110 (memory ceiling), A2-039 (TCP severity-graded cut), A2-040 (Netflix AIMD), R9 §3.5.
- **Need:** N1, N10.
- **What and how:** Size x0.7 after a day at the unit's own 10th percentile; +0.05 per green day; never above baseline; regrowth slows near the level of the last trip. Used only while the unit sits in the yellow or red zone of H48, never as the default brake.
- **Levels:** unit.
- **Classes and styles:** day = the unit's window from H01. Slow units (ORB) are hurt most because few green days restore it (kept 32 % of R in SIM).
- **Ledger:** `drawdown_pressure_multiplier`, `grow_back_rule`; *`aimd_cut_factor`*, *`aimd_add_step`* (both X2's ids; here the add step stops at baseline), *`last_trip_size_level`*.
- **Performance:** as a default it chokes: 32-84 % of healthy R kept (SIM). R9's version looked better because it also allowed size above 1.0, which is an accelerator.
- **Survival:** strong: the 95th-percentile drawdown fell from 34 to 19R (fs10) and the loss after decay from 69 to 21R.
- **Evidence chain:** TCP and Netflix (live in their field) → R9 script → SIM. Weakest link: the restore rule; with +0.05 per green day the unit spends most days under baseline.

### B. The improved circuit breaker: fast, slow, proven

#### X3-H08. Two-speed circuit breaker: fast trip plus a fire-density sentinel with zones [plausible]
- **Links:** H01 or H02 (fast half), A2-083 (April two-strike breaker), A2-086 and A4-143 (WF3 fire density as decay evidence), A2-126 (his ruling: baseline, improve it), A2-088 (expected fire rate on the card), A2-196 (Basel three zones), A2-031 (minimum events), A2-079 (three speeds of brake).
- **Need:** N2.
- **What and how:** The fast half is H01. The slow half, a new kind called a sentinel, reads the fast half's fire record. Because H01 fires at a known healthy rate p0 (about 1 %), its fire count is exactly a one-day 99 % VaR exception count, and Basel's zones apply: over 250 windows, 0-4 fires green, 5-9 yellow, 10 or more red, with zone cuts recomputed from the binomial for the unit's own p0. A sequential form (Bernoulli CUSUM tuned to detect a fire rate three times p0) watches between looks. Green: nothing. Yellow: hold size, no loosening, no new markets, gather evidence. Red: one level down and a review card. Paper needs the second key (H11).
- **Levels:** unit; the same sentinel reads cluster and BMS breakers (H21, H24).
- **Classes and styles:** class-free once H01 is in R. Fast units fill the zones quickly (at 40 a day it caught a dead edge in 99.5 % of runs, median 36 days); slow units barely (orb2 25.5 %). For swing and ORB units the sentinel is too slow alone; H49's trade test leads there.
- **Ledger:** `breaker_fire_density`, `breaker_expected_fire_rate`, `circuit_breaker_strikes`, `drift_state`; *`ev_brake_fire_band`*, *`density_alarm_ratio`*, *`density_cusum_threshold`*, *`slow_lane_false_alarm_rate`*.
- **Performance:** calm: alarms after 0-2.5 % of bad weeks at 10 a day, 18 % at 40 (SIM), so it rarely demotes a good unit for a bad week.
- **Survival:** slower than a trade CUSUM (median 36-93 days against 10-99), so it cannot be the only decay sensor.
- **Evidence chain:** his memory of WF3 (old rule, spec only) → Basel zones (live regulatory practice) → SIM detection rates. Weakest link: the expected fire band was never filled in any generation (A2-088); it needs an honest card.

#### X3-H09. Expected fire band on the unit's card [solid]
- **Links:** A2-088, A2-227 (every slow-lane threshold calibrated by simulation on the unit's record), A2-212 (Monte Carlo on out-of-sample trades; use blocks), A2-216 (B13 card), A2-125 (context tags), A2-031.
- **Need:** N2, N12.
- **What and how:** When QMB writes a unit's card, it also runs the unit's holdout through every bound brake on 1,000 block-bootstrapped paths and stores, per brake: expected fire rate per 100 trades and per window, the Basel zone cuts, and the fire rate per context (session, class). Live fires are then read against a band, never against a feeling.
- **Levels:** unit; cluster bands from pooled member cards.
- **Classes and styles:** bands per class and session when the unit trades several; crypto weekends are their own context.
- **Ledger:** `breaker_expected_fire_rate`, `mc_cone_floor_percentile`, `monte_carlo_shuffle_count`; *`ev_brake_fire_band`*, *`fire_context_tags`*.
- **Performance:** removes false decay reads on busy units (a busy healthy unit fires more by chance; WF3 had no baseline, A2-086).
- **Survival:** gives the sentinel its yardstick.
- **Evidence chain:** July planned it (docs, never filled) → X5 draft's calibration-by-simulation (idea) → SIM shows the method. Weakest link: holdouts are optimistic; first-month fires above band are read first as "the card was optimistic" (A2-149).

#### X3-H10. Context-tagged fire density: bad market or bad unit [plausible]
- **Links:** A2-125 and A3-112 (fires tagged and stacked upward), A2-086, A2-089 (chorus), A3-123 (keep strategy decay, bucket stress and account drawdown apart), A2-174.
- **Need:** N2, N7, N10.
- **What and how:** Every fire carries tags: session, market, class, region, MIS words, news window, SQS state. Density by context splits two stories. If a unit's fires gather in one context that other units also fire in, the market is the problem, and the evidence goes up to isolation (H28). If its fires spread across contexts while peers stay calm, the unit is the problem, and the evidence goes to its slow lane (H49).
- **Levels:** unit → cluster → BMS.
- **Classes and styles:** FX: tag both currency legs; indices: home exchange; crypto: venue; energy: event (EIA, OPEC); stocks: earnings day.
- **Ledger:** `breaker_fire_density`, `isolation_scope`, `instrument_class`, `session_windows`; *`fire_context_tags`*.
- **Performance:** fewer false demotions of good units on bad-market days.
- **Survival:** faster isolation of bad markets.
- **Evidence chain:** April annotation `region_blocked` (old rule) → idea. Weakest link: trade rows lack session today (G9 §7).

#### X3-H11. Two-key demotion: either key cuts, both keys send to paper [plausible]
- **Links:** H08, A2-149 (trade CUSUM on R), A2-152 (e-detectors), A5-028 (e-value investigates, burn rate pages, hard limit acts), A2-175 (three evidence tiers), A2-160 (demotion cause).
- **Need:** N2, N10.
- **What and how:** Key 1 is a fast trade-stream test (CUSUM on R with allowance half the edge, or an e-detector). Key 2 is the fire-density sentinel. Either key at warning level halves size at once, reversibly. A step to paper needs both keys, or one key that stays at alarm past the next planned look (H48). The roundtable added the "at once" (Dana) and "past a planned look" (Ada).
- **Levels:** unit.
- **Classes and styles:** fast units lean on key 1 (it caught decay in 10-40 days at 10-40 a day); ORB and swing units lean on calendar looks and pooled evidence (H23) because both keys are slow there.
- **Ledger:** `cusum_limit`, `cusum_allowance_r`, `drift_state`, `drift_size_down_step`; *`demotion_two_key_rule`*, *`demotion_cause`*.
- **Performance:** at 40 a day, a reversible policy kept 902R of 950R after a bad week where permanent demotion at the CUSUM alarm kept 614R (SIM).
- **Survival:** after a real decay both policies saved the same (about 380R against 99R with no slow lane).
- **Evidence chain:** SIM (simulation); trial practice of separate futility and efficacy looks (R3). Weakest link: the second key at low frequency is slow; for ORB the rule degenerates to key 1 plus looks.

#### X3-H12. Brake scorecard: precision, recall, detection time, reset time and trip tax [solid]
- **Links:** A2-030 and A4-156 (precision; noisy brake is a defect), A2-142 (four-number scorecard), A2-143 (monthly gate lift), A4-202 (trip tax), A5-073 (cost of conservatism), A2-145 (would_have rows), A2-025 (alerts only for action).
- **Need:** N3, N14.
- **What and how:** For each brake and each unit, a monthly job writes: precision (share of fires followed by a loss beyond the unit's normal in the next window, judged against the matched random arm, not by hindsight alone); recall (share of the unit's worst windows that the brake caught); detection time; reset time; trip tax (would_have R forgone while benched, minus loss avoided). The row is shown on the brake. A brake with no lift for its unit type is reported as a defect.
- **Levels:** every scope.
- **Classes and styles:** per class and session; thin units pool by brake type within a family (roundtable, Ada).
- **Ledger:** `brake_precision`, `breaker_fire_density`; *`brake_recall`*, *`trip_tax_r`*, *`under_baseline_share`*.
- **Performance:** turns "brakes must not choke a healthy unit" into a number per brake.
- **Survival:** a noisy brake gets fixed instead of turned off by hand (alarm fatigue: 85-99 % of hospital alarms need no action, A2-030).
- **Evidence chain:** SRE scorecards and hospital alarm studies (live in their fields). Weakest link: precision labels are noisy for rare events.

#### X3-H13. Random-control certificate for every brake [solid]
- **Links:** A2-135 (random brake at matched frequency, MQL5 23482), A2-136 (fixed-count placebo), A2-137 (path-independent split, right denominator), A2-138 (random admission at the same adoption rate), A2-141 (trade-list re-sizer), A2-140 (counterfactual exit replay), A5-029 (proven at one place is not proven at another), RANKING evidence rule 2.
- **Need:** N3.
- **What and how:** Before a brake may enforce, it is replayed on the unit's own trades three ways: no brake, the brake, and a random brake with the same fire rate and the same action. The margin (R per 100 trades, with a block-permutation p-value) is stored on the brake's row. The test repeats on shadow live data. A brake type is certified per family (pooled), its threshold per unit. A brake that cannot beat its random twin may still act if its job is the tail, but the row must say so.
- **Levels:** every scope; for isolation, the random twin isolates a random class on a random day at the same rate.
- **Classes and styles:** run per instrument; fire rates differ by class.
- **Ledger:** `brake_precision`, `breaker_expected_fire_rate`; *`brake_random_control_margin`*.
- **Performance:** stops brakes that only "trade less" from passing as skill (any brake looks good on a losing strategy, R5 trap 1).
- **Survival:** keeps the brakes that carry timing (count brakes in bad spells: +20R in SIM).
- **Evidence chain:** MQL5 23482 (controlled test, author's, small) → SIM. Weakest link: thin samples; the random arm varies run to run.

#### X3-H14. Shadow-first brake rollout with an enforcing ramp [solid]
- **Links:** A2-145 (would_have rows, ramped enforcement), A2-032 and A4-191 (METRICS_ONLY), A2-033 (Envoy enforcing percentage), A4-002 (VPA update modes), A2-036 and A4-006 (guarded tuned number with freeze).
- **Need:** N3, N12.
- **What and how:** Every new brake, and every new threshold for an old one, starts in metrics-only mode and writes would_have rows. After its certificate (H13) passes, enforcement ramps: it acts on a share of its fires, then all. Outside code may run in shadow for N trades but is never the only brake at a scope.
- **Levels:** every scope.
- **Classes and styles:** shadow on a calm month proves little; the ramp waits for at least one stressed period per class (news day, weekend for crypto) **[judgment]**.
- **Ledger:** `brake_state`; *`x1_brake_shadow_mode`*, *`x1_enforcement_percent`*.
- **Performance:** a bad brake costs nothing while it is being proven.
- **Survival:** the old brakes stay enforcing until the new one passes.
- **Evidence chain:** resilience4j, Argo, Envoy (live in software). Weakest link: shadow cannot measure the brake's effect on later trades (a bench changes the path).

### C. Restores

#### X3-H15. Half-open probe restore ladder [solid]
- **Links:** A2-007 (state-based re-enable, not a timer), A2-032 (half-open, probes judged as a group), A2-022 (recloser, then lockout), A2-033 (ejection time grows with each trip), A1-056 (probe at minimum size, then step back), A2-190 (BOIN levels), A5-137 (settle before the next change), A2-041 and A4-004 (asymmetric windows), A5-138 (no raise while a cut settles), A2-051 (RESTORE state).
- **Need:** N4.
- **What and how:** After a bench or a level cut: (1) a cool-down of one brake window in the unit's own trades or time, and the trigger cleared; (2) half-open: a few probe trades at the smallest feasible size, judged as a group; (3) pass, and size steps up one level per settled cohort; (4) fail, and the unit re-trips with a doubled cool-down; (5) after K failures it locks for his hand. No size change happens while the last one is settling. The restore never goes above baseline. A HALTED state from a risk stop still waits for his resume; only benched and reduced states restore by rule (roundtable).
- **Levels:** unit; the same ladder restores clusters and isolated classes (H33).
- **Classes and styles:** where the smallest lot is above the probe's money (gold, index contracts at $500), probes run on the paper twin (H16). Crypto: no session reset, so the cool-down is in trades. Stocks and futures: no probe until the session's opening auction or reopen has settled (H33).
- **Ledger:** `grow_back_rule`, `circuit_breaker_reset`, `risk_stop_resume_rule`, `size_levels`, `size_ramp_to_full`, `calibration_cadence_trades`; *`x1_restore_probe_trades`*, *`restore_cooldown_trades`*, *`retrip_backoff_multiplier`*, *`bench_retry_max_in_window`*, *`size_change_settle_trades`*.
- **Performance:** a bench ends on evidence, not at midnight and not at his next look; this is the anti-sitting-duck half of every brake.
- **Survival:** the back-off and lockout stop a broken unit from retrying forever (a recloser on a permanent fault repeats the loss, A2-022).
- **Evidence chain:** resilience4j, reclosers, BOIN (live in their fields); 15085 (author backtest). Weakest link: a handful of probe trades is mostly noise for a thin edge; the probe proves the machine and the conditions, not the edge.

#### X3-H16. Probe on the paper twin first [plausible]
- **Links:** A2-178 (paper twin), A2-174 (simulated execution is not evidence that live fills recovered), A2-009 (liquidity-normalised re-entry).
- **Need:** N4.
- **What and how:** The half-open probes of H15 run first on the unit's paper twin (no money), checking orders, fills and conditions. A live probe at the smallest size follows only if the twin passes. Used when the minimum lot is too big for a live probe, and after any machine fault.
- **Levels:** unit.
- **Classes and styles:** paper fills at the last closed bar with zero slippage today (G9 §0.5), so the twin cannot prove fills on thin markets (crypto alts, stocks after halts).
- **Ledger:** `paper_to_live_carry_rule`, `replay_match_floor`; *`x1_restore_probe_trades`*.
- **Performance:** restores even where live probes are impossible.
- **Survival:** no money in the first probes.
- **Evidence chain:** idea; paper twin from X5 draft. Weakest link: paper fills differ from live.

#### X3-H17. Memory ceiling with level lock-out [plausible]
- **Links:** A5-134 and A5-110 (regrow fast to below the trip level, slowly near it), A2-190 (BOIN eliminates a level and all above it when it proves too toxic), R9 §3.4.
- **Need:** N4.
- **What and how:** The restore remembers the size level at which the unit tripped. It climbs one level per cohort to the level below that, then needs a full extra cohort to re-enter the trip level. A second trip at the same level locks that level for a set period.
- **Levels:** unit, cluster.
- **Classes and styles:** generic; the lock-out period is in trades for fast units and days for slow ones.
- **Ledger:** `grow_back_rule`, `size_levels`; *`last_trip_size_level`*, *`level_lockout_days`*.
- **Performance:** fast regrowth far from the trip; no slow crawl all the way.
- **Survival:** stops the accelerator-like re-raise straight into the same trip.
- **Evidence chain:** TCP ssthresh and CUBIC (live in networking), BOIN (trial practice). Weakest link: the remembered level may be stale after a regime change.

#### X3-H18. Restore is earned in evidence, never free [plausible]
- **Links:** A5-103 (restore definition), R9 §1.10 (reinsurance reinstatement is paid), A2-220 (family error budget), A2-221 (re-promotion on an e-value), A2-158 (re-promotion episodes).
- **Need:** N4, N10.
- **What and how:** Short benches restore by H15. A restore after a slow-lane demotion is a new evidence episode: the unit's post-cut trades must pass an e-value against "no edge" with the episode's smaller error budget. Nothing restores by calendar alone.
- **Levels:** unit.
- **Classes and styles:** generic; slow units take months (accepted cost).
- **Ledger:** `sequential_evidence_pass`, `repromotion_positive_demo_trades`; *`ev_lifetime_demotion_budget`*.
- **Performance:** avoids flipping units back to live on a lucky streak (10 straight demo wins happen 1.7 % of the time for a zero-edge 2/3-win unit, A2-213).
- **Survival:** a broken unit does not drift back.
- **Evidence chain:** e-process theory (simulation plus proofs) → reinsurance practice (snippet). Weakest link: thin edges take a long time to re-prove.

### D. Cluster (Book) and methodology brakes

#### X3-H20. Hours-clause cluster ledger: one shared-driver event, one count [plausible]
- **Links:** A2-026 and A3-146 (hours clause), A3-131 (driver tags per instrument), A2-020 (one incident key), A2-089 and A3-111 (chorus), A3-050 (currency legs).
- **Need:** N5.
- **What and how:** Losses from many units on one shared driver (a USD release, a BTC flush) inside a driver-specific window count as one event in every count and density statistic above the unit (cluster fires, chorus, methodology tests). Money still counts in full in every money brake. The key is the driver tag plus the window.
- **Levels:** cluster, methodology, BMS.
- **Classes and styles:** FX: both legs; a US release hits USD pairs, gold and US indices in minutes; crypto shocks run over hours; energy around EIA (Wednesday 10:30 New York); stocks: earnings per name.
- **Ledger:** `loss_event_window`, `chorus_expected_frequency`, `bms_circuit_breaker`; *`event_dedup_key`*.
- **Performance:** five correlated stops read as one bad event, not five strikes against five healthy units.
- **Survival:** the money brakes still see the full loss.
- **Evidence chain:** reinsurance practice (live in its field). Weakest link: clustered storms; a second wave may fall inside or outside the window.

#### X3-H21. Chorus breaker per cluster [plausible]
- **Links:** A2-089 and A3-111 (chorus flag), A2-122 (K of N), A2-188 (correlated units count as N/(1+(N-1)ρ)), A3-112, H20.
- **Need:** N5.
- **What and how:** The cluster trips when K of its N members fire their own H01 brakes inside one event window. K is the smallest count whose chance under the cluster's measured result correlation stays below the cluster's false-alarm target. Action: no new entries in the cluster for the window. Members' own slow lanes are not charged for that event (H20).
- **Levels:** cluster (Book or a driver-based cluster).
- **Classes and styles:** works best inside one class (FX scalpers, crypto units on one venue). Across classes, correlation rises in stress, so K comes from stressed correlation **[judgment]**.
- **Ledger:** `chorus_expected_frequency`, `unit_result_correlation`, `effective_independent_bets`, `loss_event_window`; *`chorus_k_of_n`*.
- **Performance:** a correlated bad hour stops the cluster once, instead of each unit tripping alone and restarting.
- **Survival:** catches "losing together" (his C32), which no unit-level brake sees.
- **Evidence chain:** July spec (threshold null, never ran) → idea. Weakest link: ρ needs weeks of paper.

#### X3-H22. Cluster burn-rate permit [solid]
- **Links:** A2-028 and A4-032 (two-window burn rate), A2-029 and A4-033 (spent budget freezes changes), A5-141 (budget-burn permit), A2-095 (the Book's day budget door), A2-052 (taper to the remaining budget).
- **Need:** N5, N11.
- **What and how:** The cluster's period loss budget is watched as a burn rate over a long and a short window. Fast burn: halt the cluster for the window. Slow burn: size down one level. Healthy budget: accelerators allowed (X2's). Spent budget: accelerators and new template versions frozen until the budget is positive again. This replaces the undefined "door refuses when drained".
- **Levels:** cluster, BMS.
- **Classes and styles:** the period follows the cluster's trading clock (crypto: rolling 24 hours). Low-frequency clusters use one loss as a large share, so they need H01's trade window.
- **Ledger:** `period_loss_budget`, `budget_remaining`, `budget_drain_rule`, `budget_door_rule`; *`burn_rate_page_threshold`*, *`burn_rate_ticket_threshold`*.
- **Performance:** no cliff at the door; size tapers.
- **Survival:** a fast burn stops at once.
- **Evidence chain:** Google SRE (live in its field). Weakest link: a gap spends the budget in one step.

#### X3-H23. Methodology pooled CUSUM [plausible]
- **Links:** A3-164 (one logic fading everywhere, caught on the pooled stream), A2-188 (pooled proof discounted for correlation), A2-152 (e-BH across streams), A2-189 (per-cell pooling).
- **Need:** N5, N10.
- **What and how:** The R of every unit sharing a logic (all mean-reverting FX scalpers, all ORB units) is pooled after H20's event dedup. A CUSUM on the pooled stream sees a logic fading in days where one unit needs weeks. Action: every unit of the methodology moves one level down; no unit is demoted on the pooled evidence alone.
- **Levels:** methodology.
- **Classes and styles:** ORB units gain most: breadth across session opens gives them the trades one unit lacks (his D11).
- **Ledger:** `cusum_limit`, `drift_size_down_step`, `effective_independent_bets`, `unit_result_correlation`.
- **Performance:** finds decay early without punishing the healthy member.
- **Survival:** catches correlated edge decay, which no count of bets removes.
- **Evidence chain:** idea, on the pooling arithmetic of R3. Weakest link: pooled correlated units overstate the evidence unless discounted.

### E. Portfolio (BMS) and account brakes

#### X3-H24. BMS breaker on stacked evidence [plausible]
- **Links:** A2-122 (K of N classes isolated or BMS burn past the page level), A2-127 and A3-103 (his BMS breaker), A2-028, A2-072 and A3-096 (exchange two-layer breakers), A2-097 (kill effects), H21.
- **Need:** N6.
- **What and how:** The BMS stops all new entries for the day when any of three fire: K of N classes isolated (H28); BMS budget fast burn (H22 at BMS scope); chorus across clusters above the expected rate. It flattens only if the buffer above the floor is threatened (H25). Target: about one fire a month or fewer on history, never on a normal day. It raises a stand-down at scope `all`, not a kill level (H62).
- **Levels:** BMS.
- **Classes and styles:** with few classes trading, "K of N classes" degenerates; then the burn and chorus legs carry it. On weekends only crypto trades, so the BMS breaker reads the crypto cluster alone (H37).
- **Ledger:** `bms_circuit_breaker`, `bms_buffer_before_floor`, `bms_daily_loss_limit`, `kill_switch_scope`; *`bms_breaker_target_fire_rate`*.
- **Performance:** a fire rate target written in advance keeps it from switching off good days.
- **Survival:** his "switch off entirely" on a correlated move, with the evidence named.
- **Evidence chain:** exchange breakers (live), his idea, X4 draft. Weakest link: no history of QMX's own multi-unit days to calibrate on.

#### X3-H25. Cushion clip above the buffer, with worst move per class [solid]
- **Links:** A2-012 and A1-038 (exposure clip: worst one-step loss at most the cushion), A2-132 (his buffer above the floor), A2-118 (floor-breach dwell), A5-010 (two anchors: the floor never resets), A2-003 (order-boundary worst-case veto).
- **Need:** N6.
- **What and how:** Total open worst-case loss (stop losses plus a gap allowance per class) may not exceed the cushion above floor plus buffer. When the cushion narrows, new entries shrink; the floor and the book high-water mark never reset on a restart, a payout or a version change. A dwell rule says whether a one-minute marked breach counts.
- **Levels:** BMS, account.
- **Classes and styles:** worst move per class from stress scenarios, not recent volatility: FX majors small; crypto and single stocks large; index CFDs over weekends large; energy on EIA and OPEC days large; futures limit moves.
- **Ledger:** `bms_buffer_before_floor`, `portfolio_floor`, `high_water_mark_equity`, `open_risk_at_stop`, `gap_loss_beyond_stop`; *`worst_step_move_r`*, *`floor_breach_dwell_s`*.
- **Performance:** size stays full while the cushion is wide.
- **Survival:** the floor is touched only by a gap larger than the class allowance (his "black swan or real system failure").
- **Evidence chain:** Hsieh lemma (proofs plus backtest, READ in R9). Weakest link: a gap beyond the assumed worst move breaks the guarantee (BTC 20.18 % against a 20 % cap).

#### X3-H26. Pod-style step ladder on a unit's capital share, time-scaled [plausible]
- **Links:** A2-073 and A1-104 (pods halve at -5 %, out at -7.5 %), A5-022 (staged cut ladder in R from the unit's high-water mark), A5-146 (drawdown thresholds widen with time in service), A2-014 (worry lines by style), A2-015 (triple penance).
- **Need:** N6, N10.
- **What and how:** The BMS watches each unit's drawdown from its own high-water mark, in R at its assigned risk. At the first line it halves the unit's capital share; at the second it stops new risk and opens a review. Lines are set from the unit's own block bootstrap and widen with time in service, because the chance of touching any line rises with time even for an unchanged unit.
- **Levels:** BMS on units.
- **Classes and styles:** depth lines for mean-reverting scalpers (short-volatility-like, worst cases 1.30-1.34x Gaussian); duration lines for trend and breakout (time under water) (A2-014).
- **Ledger:** `drift_size_down_step`, `high_water_mark_equity`, `unit_capital_share`, `equity_drawdown_halt`; *`worst_step_move_r`* (gap part).
- **Performance:** the halving is a big first step; restore by H18, so it does not stay halved for months.
- **Survival:** a decaying unit loses its capital before it loses the floor.
- **Evidence chain:** pod practice (press-reported), Man Group (READ). Weakest link: pods never restore automatically; this ladder does.

#### X3-H27. Priority shedding when the BMS tightens [plausible]
- **Links:** A2-035 and A4-189 (shed by declared class), A5-040 (tiers), H48 zones.
- **Need:** N6, N14.
- **What and how:** When BMS room shrinks (H22, H25), units are cut by priority: probation and level-1 units first, then yellow-zone units, then green proven units. A proven unit in yellow loses its priority, so status cannot shield a decaying unit.
- **Levels:** BMS.
- **Classes and styles:** generic.
- **Ledger:** `slot_rebalance_rule`, `concurrent_unit_slots`, `drift_state`.
- **Performance:** proven edges keep their size on tight days.
- **Survival:** the least-proven risk goes first.
- **Evidence chain:** Google load shedding (live in its field). Weakest link: priority by status can protect a decaying unit if zones lag.

#### X3-H75. Order-boundary worst-case veto with gap and halt allowance [solid]
- **Links:** A2-003 (compute the maximum loss from the actual order), A2-264 (halt and limit-move allowance), A2-262 (stop beyond the liquidation price refused), A2-024 (envelope protection).
- **Need:** N8.
- **What and how:** Before routing, the node computes the order's worst loss from size, stop, class gap allowance, fees and margin, and refuses an order that breaches its limit. It is a clamp, not a brake: it reads no evidence.
- **Levels:** trade, account.
- **Classes and styles:** futures and short options: large loss on small count; crypto perpetuals: liquidation price inside the check; stocks and futures: halt and limit-move allowance; energy around reports.
- **Ledger:** `risk_amount_usd`, `gap_loss_beyond_stop`, `liquidation_stop_check`, `margin_used`; *`worst_step_move_r`*.
- **Performance:** none; it only removes orders the template never meant.
- **Survival:** stops the order that would pierce the floor in one gap.
- **Evidence chain:** idea plus running liquidation check (old QMX rule, running). Weakest link: the gap allowance per class.

### F. Market, class and region isolation

#### X3-H28. Two-tell bucket isolation with calendar-aware baselines [plausible]
- **Links:** A2-080 and A3-093 (bucket-local isolation), A3-092 (fast tells and slow confirmation, no master score), A3-088 (turbulence), A3-089 (correlation surprise), A3-090 (absorption ratio), A3-095 (co-move K of N), A2-123 and A3-109 (two tells must agree; precision recorded), A2-120 and A3-108 (mode ladder), A2-128 and A3-102 (his isolation protocol).
- **Need:** N7.
- **What and how:** A bucket is a class, a region or a session. Fast tells per bucket: spread and volatility against their usual level for this hour, turbulence, correlation surprise, the share of instruments past their usual range. Slow confirmation: absorption ratio over a day. An isolation needs two tells to agree plus a minimum co-move count. Its mode is graded: no new entries (default), staged reduce-only, flatten at the top only. Each isolation records afterwards whether a loss followed in the bucket (precision), and starts in shadow (H14).
- **Levels:** class or region (BMS-owned), cluster.
- **Classes and styles:** FX: one-currency divergence is a local cut, a dollar move a region cut; indices: the home exchange's session; crypto: one extreme token cuts its cluster only; futures: a roll break cuts the contract, not the class; energy: EIA and OPEC windows; stocks: halts and earnings. Scalpers feel isolations most (they trade through them); swing units mostly hold through with exits untouched.
- **Ledger:** `market_isolation_trigger`, `isolation_scope`, `isolation_end_rule`, `cross_market_stress_reading`; *`bucket_stress_percentile`*, *`isolation_mode`*, *`isolation_ttl`*.
- **Performance:** two tells and a precision record keep isolations from cutting good days.
- **Survival:** his "it can isolate crypto ... with evidence".
- **Evidence chain:** turbulence, correlation surprise and absorption ratio (author backtests, daily data) → assistant's bucket rule (idea). Weakest link: no dependable minutes-ahead warning; thresholds untested for intraday.

#### X3-H29. SQS K-of-N class caution [solid]
- **Links:** A2-121 (class caution when SQS blocks K of N), A2-111 and A3-075 (SQS with hysteresis), A3-098 (liquidity commonality), A2-063 and A3-070 (percentile spread gate, two windows).
- **Need:** N7, N8.
- **What and how:** SQS keeps blocking entries per instrument as today. When it blocks K of N instruments of one class at once, the class goes to caution (no new entries) without waiting for any loss, and lifts when spreads re-cross their band. This catches a broker or liquidity-provider withdrawal that moves no price.
- **Levels:** class.
- **Classes and styles:** FX at one broker (a quote pull hits every pair); crypto by venue; indices by exchange; metals and energy around fixes and reports. Scalpers gain most (spread is most of their cost).
- **Ledger:** `sqs_score`, `sqs_hard_block_threshold`, `sqs_hysteresis_band`, `instrument_class`; *`class_caution_k_of_n`*.
- **Performance:** costs nothing on normal days (it needs several blocks at once).
- **Survival:** first defence on liquidity events, before any stop fills at a wide spread.
- **Evidence chain:** SQS (built, off the path) + liquidity commonality (author backtest) → X4 scenario. Weakest link: K too low gives false class cautions.

#### X3-H30. Peer ejection with a capped share and growing ejection time [plausible]
- **Links:** A2-033, A3-104 and A4-190 (Envoy outlier ejection), A2-119 (retrip back-off), H10.
- **Need:** N7, N5.
- **What and how:** A unit or instrument whose recent result stream falls below its peers' mean minus k standard deviations (peers: same class and same logic, each with enough trades) is ejected for a time that grows with each consecutive ejection and shrinks while healthy. At most a set share of a cluster may be ejected at once; an absolute floor beside it catches the case where every peer degrades (then it is the market, H28).
- **Levels:** instrument, unit, cluster.
- **Classes and styles:** peers within one class only; FX pairs sharing a leg are not independent peers.
- **Ledger:** `isolation_scope`, `isolation_end_rule`, `unit_result_correlation`; *`peer_ejection_sd_factor`*, *`isolation_max_share`*, *`retrip_backoff_multiplier`*.
- **Performance:** the cap stops a shared shock from ejecting everyone.
- **Survival:** a single broken market or unit leaves quickly.
- **Evidence chain:** Envoy (live in software). Weakest link: low-traffic units never reach the minimum sample.

#### X3-H31. Event windows by measured impact; entries only; re-entry on spreads and depth [solid]
- **Links:** A2-100 and A3-127 (news window: entries only, scope from exposure records, fail-safe up), A3-130 (measured impact per release and instrument), A3-132 (window per unit type; blocked hours reported), A3-229 (calibrate in event time against matched non-event periods), A3-133 (surprise backstop), A3-141 ("exchange resumed" is not a re-enable signal), A3-228 (event-type policy), A2-144 and A3-210 (contract test: exits pass), A3-143 (energy events), A3-144 (earnings).
- **Need:** N7.
- **What and how:** Window widths come from measured impact per release and instrument, not provider colours. Each unit template declares the impact tier it blocks on; blocked hours are reported as a cost. Windows block new entries only; exits and reduce-only orders always pass a contract test. Re-entry waits for spreads, depth and fills back inside collars. When the calendar misses an event, SQS and a volatility-jump tell raise a short caution.
- **Levels:** instrument, class, node.
- **Classes and styles:** FX: both legs of each pair; indices: home exchange releases; metals: London fix and US data; energy: EIA weekly report, OPEC, expiry; crypto: macro releases plus venue events; stocks: earnings and filings. A 5-minute scalper blocks on high impact only; an ORB blocks high and medium around its open (A3-132).
- **Ledger:** `news_blackout_before`, `news_blackout_after`, `news_impact_level_map`, `news_calendar_max_staleness`, `window_forced_flat`; *`exits_never_blocked`*.
- **Performance:** narrower measured windows give scalpers back hours a blanket ±30 minutes takes.
- **Survival:** entries stop where liquidity withdraws before releases (E-mini event study, A3-067).
- **Evidence chain:** E-mini event study (author backtest), Gen 3 window (built, off the path). Weakest link: impact drifts; windows need re-measuring.

#### X3-H32. Region shift without budget rotation; freed budget kept as reserve [plausible]
- **Links:** A2-099 and A3-110 (April region shift), A1-111 (rotation against "never redistribute"), A2-044 and A3-160 (robust MPC: keep a reserve after a shock).
- **Need:** N7, N6.
- **What and how:** On a high-impact regional event, the region is blocked and the other regions keep trading at their own budgets. The blocked region's budget is not handed to the others (the April rotation, killed in July, concentrated the book on news days); it is held as reserve until the event settles.
- **Levels:** region, BMS.
- **Classes and styles:** FX by currency region; indices by exchange region; crypto has no region, so it is never region-blocked but can be class-isolated.
- **Ledger:** `news_region_shift`, `isolation_scope`, `portfolio_daily_risk_budget`; *`disturbance_reserve_share`*.
- **Performance:** other regions keep full size.
- **Survival:** no concentration of risk on the news day.
- **Evidence chain:** April spec, July ruling (old rules), robust MPC (control theory analogue). Weakest link: region hours never matched the session windows in April.

#### X3-H33. Isolation lifecycle: time to live, staged resume, retrip back-off, aftershock lockout [solid]
- **Links:** A3-107 and A2-119 (lifecycle), A2-022 (recloser lockout), A2-009 (liquidity-normalised re-entry), A2-008 and A3-168 (separate trip and clear levels).
- **Need:** N7, N4.
- **What and how:** Every isolation has evidence and an end: a time to live or its tells clearing at a stricter clear level. Release is staged: a settling time at half size, full size after a clean period. A second trip inside the settling time doubles the next time to live; a third locks the class out for the day.
- **Levels:** class, region, cluster.
- **Classes and styles:** stocks: reopen auction minutes; futures: after a limit move; crypto: after venue outages.
- **Ledger:** `isolation_end_rule`, `sqs_hysteresis_band`; *`isolation_ttl`*, *`settling_time`*, *`resume_size_fraction`*, *`retrip_backoff_multiplier`*.
- **Performance:** ends isolations on evidence instead of leaving classes off for days.
- **Survival:** no full-size rush into a thin reopen.
- **Evidence chain:** reclosers (live in their field), X4 draft. Weakest link: half size may still be too big in a thin reopen.

#### X3-H34. Slow isolation by agent card, with evidence and a time to live (QMA flagged) [plausible]
- **Links:** A3-113 (slow isolation by agent card), A2-018 and A4-104 (de-risk-only, typed, expiring proposals), A3-145 (three bounded agents feeding one deterministic service), A3-138 and A4-108 (news provenance, cap on one item's effect), his C27 ("analysis we've come up with over 20 days").
- **Need:** N7, N13.
- **What and how:** Weeks of slow deterioration (spreads up at every hour, fills worse, every unit below its card) cannot trip a minute tell. An agent reads readings and journals and lands a card: "isolate class X for a week", with evidence ids and a time to live. The card is de-risk only. Whether it applies on his click or by itself is his call (question 3). The agent's isolations get a precision record like any brake.
- **Levels:** class, region.
- **Classes and styles:** all; most useful where structure drifts slowly (crypto alts losing liquidity, an FX broker degrading).
- **Ledger:** `market_isolation_trigger`, `isolation_scope`, `decision_freshness_bound`.
- **Performance:** catches slow decay of a market no minute tell sees.
- **Survival:** de-risk only; expiry by default.
- **Evidence chain:** idea; fabricated news moved LLM agents 62 % of the time in a sandbox (A2-018), so cards need provenance. Weakest link: an agent fooled by bad data proposes bad isolations.

#### X3-H35. Isolation scope keys: class, region, currency leg, underlying group, session [solid]
- **Links:** A3-106 (scope keys), A3-029 (group by underlying process, not wrapper), A3-131 (driver tags), A3-050 (currency legs), A2-097 (kill switch scopes today: all, account, deployment, instrument).
- **Need:** N7, N8, N11.
- **What and how:** The stand-down table and the isolation protocol gain scope keys beside `instrument:`: `class:`, `region:`, `currency:`, `underlying:` and `session:`. An ETF or CFD on gold is grouped with gold, not with equities. Every brake names its scope from this set.
- **Levels:** node, BMS.
- **Classes and styles:** this is the class lens itself; a missing base currency hides FX exposure, so a missing tag fails closed (H36).
- **Ledger:** `isolation_scope`, `kill_switch_scope`, `instrument_class`; *`x1_scope_key_set`*.
- **Performance:** none direct; it makes narrow isolations possible instead of all-or-nothing.
- **Survival:** "it can isolate crypto" needs a crypto scope; today none exists (G9 §0.7).
- **Evidence chain:** stack facts (instrument records carry class, calendar and zone). Weakest link: region is free text on venues today.

#### X3-H36. Unknown is not calm: fail-closed isolation and placement [solid]
- **Links:** A3-094 (bad data blocks new risk), A2-110 (board read fails open today), A2-114 and A4-058 (declared fail mode), A3-115 (the MIS publishes the isolation; placement fails closed), A4-005 (missing data moves the cautious way).
- **Need:** N7, N11.
- **What and how:** If prices are stale, a venue is down or a contract is rolling, the bucket's state is "unknown" and new entries there stop. An isolation is published on the board so placement does not route units into it; during an isolation the board read fails closed for that scope only. Every brake declares its fail mode.
- **Levels:** node, class.
- **Classes and styles:** a closed market is never a zero-return observation; crypto moving does not make a stale FX feed fresh.
- **Ledger:** `board_stale_after`, `feed_stale_after`, `decision_freshness_bound`.
- **Performance:** fail closed only for the affected scope, so one bad feed does not stop everything.
- **Survival:** no trading on silence.
- **Evidence chain:** node stand-downs already clear by themselves (old rule, running). Weakest link: a flaky fact stops trading in its scope.

#### X3-H37. Weekend and single-class budget scaler [plausible]
- **Links:** A3-114 (scale the day budget with open breadth), A3-058 (weekend crypto volatility predicts Monday variance elsewhere), A2-188 (effective bets).
- **Need:** N6, N7.
- **What and how:** When only one class is open (crypto through the FX weekend), the budget it may spend is capped at its weekday share, because effective breadth falls to one or two bets. A high weekend crypto volatility reading raises Monday-open caution on indices and gold.
- **Levels:** BMS.
- **Classes and styles:** crypto weekends; index and FX Monday opens.
- **Ledger:** `portfolio_daily_risk_budget`, `effective_independent_bets`; *`day_budget_breadth_scale`*.
- **Performance:** crypto keeps its normal size, no more.
- **Survival:** the whole day budget is not spent on one correlated class.
- **Evidence chain:** HAR study (author backtest, short sample). Weakest link: crypto may be the only good market that weekend.

### G. Exits

#### X3-H38. Stopping-premium gate: tight stops only where the unit's own persistence supports them [plausible]
- **Links:** Kaminski-Lo and Lo-Remorov (R8 §1.1-1.2), A5-079 (measure persistence before a stop), A5-081 (for a trend unit the trend's reversal is the exit; hard stop is a wide catastrophe stop), A2-249 (stops help or hurt by momentum vs mean reversion), A2-231 (trailing stop suboptimal under positive drift), A2-265 (exit by trend or reversion state).
- **Need:** N9.
- **What and how:** Before a unit gets any stop tighter than its disaster stop, QMB measures the autocorrelation of the unit's own P&L or price at its holding horizon (a block test). Momentum: price stops and trailing are allowed. Mean reversion: a wide disaster stop plus thesis and time exits; tight price stops are refused unless the two-arm test (H42's) shows they pay after costs. Random walk: disaster stop only.
- **Levels:** trade, unit.
- **Classes and styles:** many FX crosses and index futures mean-revert at minute scales (stops cost most); futures trends and some FX trends persist at longer horizons; crypto 15-minute reversal is common (A3-029). Scalpers: mostly the mean-reversion branch; swing trend units: the trend-exit branch (Clare et al.: no extra stop beat the plain trend exit).
- **Ledger:** `stop_policy_per_style`, `stop_distance`, `disaster_stop_distance`, `trailing_stop_setting`; *`horizon_autocorrelation`*.
- **Performance:** stops stop costing return where they only sell the dip.
- **Survival:** the disaster stop stays everywhere.
- **Evidence chain:** Kaminski-Lo (abstract and secondary in R8), Clare et al. (secondary). Weakest link: no intraday or cost-heavy test of the stopping premium.

#### X3-H39. FI cut size from the unit's own winners, with a time stop and two baselines [solid as a method]
- **Links:** A5-087 (an invalidation rule must beat "no early cut" and "cut one bar later"), R8 §2.3 (MAE of winners; edge ratio), A2-239 (stop at the winners' MAE percentile), A5-086 (edge-versus-time curve), A2-252 (FI at about 0.35R, never coded), A2-240 (live MAE and MFE journal), A2-225 (exit change as alpha or risk control), A2-072 (LULD bands double near open and close).
- **Need:** N9.
- **What and how:** The cut level is read from the adverse excursion of the unit's own winners: if 90 % of winners never go below -0.4R, a cut at -0.5R loses at most about 10 % of winners. A time stop sits at the bar where the edge ratio peaks. Before it may act live, the rule must beat "no early cut" and "cut one bar later" after costs, out of sample, counted as a trial. Near session opens and closes the cut widens, the way exchange bands double there. Re-measured live from the MAE journal.
- **Levels:** trade; the level is a unit number.
- **Classes and styles:** the cut must clear spread and commission in R on each instrument (wide-spread metals at rollover and crypto alts need wider cuts); gap-prone classes keep a disaster stop beneath. Scalpers: the main loss exit; intraday: an early exit before the structural stop; swing: rarely used.
- **Ledger:** `fast_invalidation_cut_r`, `fast_invalidation_trigger`, `excursion_mae_mfe_r`, `max_hold_time`, `effective_tries`; *`fi_cut_mae_percentile`*, *`edge_peak_bar`*.
- **Performance:** an honest cut keeps most winners and shrinks the average loss; the FI unit in SIM had the same edge with far less money at risk per loss.
- **Survival:** smaller average loss; no fake comfort from a cut that loses to costs.
- **Evidence chain:** practitioner MAE method (not read in full, R8) + MNQ evidence that the edge lives in the first bars (READ in R8) + idea. Weakest link: no paper tests fractional early cuts after costs (R8 gap 2).

#### X3-H40. Thesis-first fast invalidation with a price backstop [plausible]
- **Links:** A2-253 (named falsifying condition per trade), A2-254 (bot-proposed close with a typed reason code), A2-257 (wide disaster stop under FI), A2-258 (the safest exit wins), H39.
- **Need:** N9.
- **What and how:** Each trade carries a named condition that would prove its premise wrong (an ORB trade back inside the range; a mean-reversion level broken; order-flow imbalance flipped). FI fires on the condition. H39's price cut is the backstop when the condition is slow; the disaster stop sits beneath both. The exit row records which one fired.
- **Levels:** trade.
- **Classes and styles:** conditions are written per logic, so they travel across classes; the backstop's size is per instrument.
- **Ledger:** `fast_invalidation_trigger`, `exit_reason_code`, `disaster_stop_distance`; *`falsifying_condition`*.
- **Performance:** fires on the premise, not on noise, so fewer good trades are cut (R8 §2.4: a thesis-based trigger is safer than a price-only fraction).
- **Survival:** the price backstop and disaster stop remain.
- **Evidence chain:** Steward (author backtest, paper account); Gen 3 reason codes (docs). Weakest link: vague conditions cannot be coded.

#### X3-H41. The dynamic SL/TP rebuilt: breakeven only where it changes the forecast [plausible]
- **Links:** A2-255 (April dynamic SL/TP), A2-256 (Gen 3 breakeven ratchet), A2-269 (his M15 memory: FI for scalpers, breakeven for intraday), A2-234 (breakeven only if the trigger changes the forecast; spread-aware offset), A2-235 (breakeven modes), A2-238 (scale-out rungs from MFE percentiles), A5-046 (barrier width with a cost floor), A2-139 (two-arm exit test).
- **Need:** N9.
- **What and how:** Breakeven is off by default. For a unit that wants it, the trigger is read from the unit's own paths: the profit level past which the chance of returning to entry before the target falls clearly. The offset covers spread and commission per instrument, so "breakeven" is not a hidden loss. A take-profit extension is allowed only on a calibrated continuation reading. The whole policy must win the entries-fixed two-arm test on each instrument it trades. Scratches it creates are counted at cost, never as losses (H03).
- **Levels:** trade; numbers per unit.
- **Classes and styles:** intraday trend and ORB units are the natural users (his memory); mean-reverting scalpers rarely benefit (Carver: breakeven is just another fixed stop). Wide-spread instruments need larger offsets.
- **Ledger:** `breakeven_trigger`, `breakeven_offset`, `take_profit_extension_threshold`, `partial_close_fraction`; *`breakeven_revisit_probability`*.
- **Performance:** removes a habit that thins the edge (many 0R scratches lengthen proof) unless the data says it pays.
- **Survival:** a working breakeven limits giveback on trend days.
- **Evidence chain:** April spec (never validated), vendor blogs only (R8 gap 1). Weakest link: no peer-reviewed breakeven test exists.

#### X3-H42. Survival-analysis hold-or-close, proven by an entries-fixed two-arm test [plausible]
- **Links:** A2-241 (competing-risk hazards, hold-or-close decision), A2-139 (two runs, identical entries, only the exit differs), A5-043 (hold-or-exit classifier on hindsight-optimal labels), A5-045 (exit-model validation before it may close live trades), A2-140 (counterfactual exit replay with trial counting).
- **Need:** N9.
- **What and how:** An open trade is treated like a patient: target and stop are competing risks, a trade open at the time stop is censored. Bar by bar, two hazards (with MFE, MAE, barrier distances and volatility as inputs) give a hold-or-close decision with an edge margin. It runs in shadow until it wins the two-arm test per instrument, with thresholds fitted per instrument on a holdout.
- **Levels:** trade.
- **Classes and styles:** calibration transferred across four instruments in the source, but one shared threshold lost on USDJPY and XAUUSD; fit per instrument. Intraday and swing suit it; 1-minute scalps may lack bars.
- **Ledger:** `max_hold_time`, `excursion_mae_mfe_r`, `fast_invalidation_trigger`; *`hazard_edge_margin`*.
- **Performance:** may hold winners longer where the hazard says the edge is alive.
- **Survival:** in the source it raised win rate and lowered profit factor on all four instruments; the two-arm gate exists to catch exactly that.
- **Evidence chain:** MQL5 24106 (author out-of-sample, entries fixed). Weakest link: profit factor fell everywhere in the only test.

#### X3-H43. Exit families per style [solid as structure]
- **Links:** A2-233 (half-life time exit), A2-232 (OU entry and exit with stop and costs), A5-081 (trend exit plus wide stop), A5-083 (stop width from volatility times a horizon factor; size from budget), A2-263 and A3-018 (flatten before the close with a buffer), A2-236 (time exit), A2-244 (trail chosen by why the position was opened), A2-268 (signal persistence sets the exit and turnover), A2-248 (triple barrier as one bundle), H38-H41.
- **Need:** N9.
- **What and how:** Each unit type's template picks one exit family; each piece inside it is a block with its own proof:

| Family | Loss exit | Profit exit | Time exit | Not allowed |
|---|---|---|---|---|
| Mean-reverting scalper | thesis FI + MAE backstop + disaster stop | target at the reversion level | half-life time exit | trailing; breakeven by default |
| Momentum or order-flow scalper | tight FI on signal flip + disaster stop | quick target or edge-peak time | edge-ratio peak bar | widening stops |
| ORB or breakout | structural stop (other side of the range) | trailing only if H38 shows persistence | flat by the session deadline with a buffer | holding overnight (his ORB rule) |
| Intraday trend | ATR stop at volatility x horizon | breakeven ratchet only after H41's test; trail | flat by deadline | percent-of-price stops |
| Swing trend | trend reversal exit + wide catastrophe stop | none fixed | none | tight stops (they lost to the trend exit) |
| Pairs and spreads (OU) | spread stop | OU target | half-life exit | |
| Carry | wide stop | carry-aware hold (swap inside the hold decision) | | |

- **Levels:** trade; the family is a methodology choice.
- **Classes and styles:** stops in ATR or spread multiples, never pips across classes; energy and stocks carry the event and halt allowance; crypto has no session deadline.
- **Ledger:** `stop_policy_per_style`, `max_hold_time`, `forced_flat_instant`, `trailing_stop_setting`, `target_r`.
- **Performance:** each style gets the exit its edge needs instead of one policy for all (April's flaw).
- **Survival:** a disaster stop in every family.
- **Evidence chain:** Carver (practitioner, READ), Clare et al., OU theory, MNQ time exits (READ). Weakest link: most cells rest on one study or on theory.

#### X3-H44. Exits feed the sizer: size from the realised loss distribution [plausible]
- **Links:** A2-250 (binding size = min(stop budget, tail-loss budget)), A5-080 (stop fill at the stressed spread), A2-261 (execution evidence per stop), A2-264 (halt allowance), R8 §1.8 (costs and gaps in Kelly).
- **Need:** N9, N1 (and X2's sizer).
- **What and how:** The loss a trade really takes is a distribution: FI cuts, full stops, scratches at cost, gap fills beyond the stop, stops filled at a wide spread. The sizer takes the smaller of the nominal stop size and the size that keeps a high loss quantile inside the budget, and recomputes whenever the exit family changes. It also gives units with no price stop an R.
- **Levels:** trade, unit.
- **Classes and styles:** gap and halt classes (indices overnight, crypto weekends, stocks, energy on reports) bind on the tail budget; FX majors rarely.
- **Ledger:** `risk_amount_usd`, `mean_loss_r`, `gap_loss_beyond_stop`, `slippage_cost`, `fast_invalidation_cut_r`; *`stressed_stop_slippage_r`*.
- **Performance:** FI units may size up honestly, because their real average loss is smaller.
- **Survival:** gap-prone units size down honestly.
- **Evidence chain:** assistant design (idea); R8 worked Kelly arithmetic. Weakest link: tail quantiles from few trades are imprecise.

#### X3-H45. Exit mechanism and outcome on every trade row [solid]
- **Links:** A2-260, A4-150, A2-090 (mechanism and outcome as separate fields), A2-254, A2-145 (would_have rows while stopped).
- **Need:** N9, N1, N10 (a prerequisite for H01-H04, H39, H50).
- **What and how:** Every closed trade records its mechanism (stop, FI cut, thesis FI, breakeven, time, signal, forced flat, kill close), its outcome in R, costs in R (commission, swap, funding, slippage), MAE and MFE, session and context tags. While a unit is benched, would_have rows record what it would have done.
- **Levels:** trade.
- **Classes and styles:** cost fields per class (swap, funding, roll).
- **Ledger:** `exit_reason_code`, `excursion_mae_mfe_r`, `round_trip_cost_r`; *`fire_context_tags`*.
- **Performance:** no brake can count FI fairly without it.
- **Survival:** same.
- **Evidence chain:** stack gap (G11: a time exit, a signal exit and an FI cut all read "close"). Weakest link: a builders' change in the journal lane.

#### X3-H46. Exits never blocked: contract test, safest exit wins, close-priority rank [solid]
- **Links:** A2-101 (exit-preservation law), A2-144 and A3-210 (contract test: every brake passes reduce-only orders), A2-258 (safest exit wins), A4-103 (close-priority rank: operator, protection, forced flats above a bot's FI close), A2-046 (Nautilus HALTED denies stops: the anti-pattern).
- **Need:** N8, N11.
- **What and how:** Every brake, window and isolation implementation must pass a contract test: closes, cancels, tighter stops and reduce-only orders go through in every state. When several exits apply on one tick, the safest wins, by a declared rank.
- **Levels:** system.
- **Classes and styles:** markets impose exceptions (halts, limit-locked futures): there "cannot exit" raises the incident's urgency instead of retrying silently.
- **Ledger:** `stop_widening_allowed`, `kill_switch_effect_matrix`, `control_rank_table`; *`exits_never_blocked`*.
- **Performance:** none; this is his hard line.
- **Survival:** a naive window that blocks "orders" would block the exit (X4 scenario).
- **Evidence chain:** running law on the unit path (old QMX rule, running). Weakest link: new guards added later must rerun the test.

#### X3-H47. Stops modelled at the stressed spread; confirm-on-close option for slow units [plausible]
- **Links:** A5-080, A2-261, R8 §2.4 (next-day execution beat immediate for tight stops; quick re-entry helped).
- **Need:** N9.
- **What and how:** Backtests and the sizer fill stops at the spread of a stress window, not the average, because spreads blow out when stops fire. Slow units may declare "confirm on close" execution for their working stop (never for the disaster stop), tested against immediate execution.
- **Levels:** trade.
- **Classes and styles:** crypto perps: trigger on mark vs last; futures: limit-lock; stocks: halts; FX: rollover gaps. Scalpers stay immediate.
- **Ledger:** `slippage_cost`, `spread_cost`, `stop_buffer`; *`stop_execution_mode`*, *`stressed_stop_slippage_r`*.
- **Performance:** fewer whipsaw stop-outs for slow units if the test agrees.
- **Survival:** honest tails in every backtest.
- **Evidence chain:** Lo-Remorov (secondary in R8). Weakest link: a delay is risky for gap-exposed units.

### H. Live drift

#### X3-H48. Three-zone drift ladder on planned looks [solid]
- **Links:** A2-196 (Basel three zones), A2-184 (planned looks: O'Brien-Fleming efficacy, non-binding futility), A2-185 (alpha spending for calendar looks), A2-167 (stacked alert levels), A5-140 (three-zone pair), A5-136 (heparin dead band), A2-227 (calibrated on the unit's own record).
- **Need:** N10.
- **What and how:** At planned looks (every N trades for fast units; on a calendar with alpha spending for slow ones), the unit's evidence statistic is placed in one of three zones calibrated on its own bootstrap. Green: no change. Yellow: hold size, no loosening, no new markets, more evidence. Red: one level down (or paper if H11's second key agrees). The zones are expectations, not alarms: an accurate model lands yellow or red about one year in nine under Basel's cuts, and the unit's card says so in plain words.
- **Levels:** unit, methodology.
- **Classes and styles:** generic; ORB and swing use calendar looks and pooled evidence (H23).
- **Ledger:** `drift_state`, `drift_size_down_step`, `sequential_evidence_pass`, `mc_cone_floor_percentile`; *`ev_zone_rule`*, *`ev_look_schedule`*.
- **Performance:** yellow does not cut, so ordinary bad stretches cost nothing.
- **Survival:** red cuts on evidence planned in advance.
- **Evidence chain:** Basel (live regulatory practice), FDA group-sequential practice, X5 draft simulations. Weakest link: nearly half of half-edge plans end undecided at 1,000 trades (A2-184).

#### X3-H49. Graded demotion: money acts fast, warnings cut reversibly, confirmation suspends [solid]
- **Links:** A2-175 (three evidence tiers), A5-150 (graded live demotion workflow), A5-028 (three signals, three jobs), A5-139 (money signals fast, edge estimates slow, growth slower), A2-133 (his rule: size down slowly; not on one bad day), A2-155 (bounded betting e-process against a minimum viable edge), A2-158 (lifetime false-demotion budget), A2-160 (demotion cause), H11.
- **Need:** N10.
- **What and how:** Three lanes, kept apart:
  1. Money facts act at once: H01, H22, H25 (fast, his "we don't lose stupidly").
  2. Warnings (trade CUSUM, e-detector, fire density, input drift) cut one level, reversibly, and open a review (his "size down ... but not quickly").
  3. Confirmation (an e-process showing net edge below the minimum viable edge, at the unit's share of the false-demotion budget) suspends to paper.
  Every demotion records its cause: statistical failure, distribution change, input drift, or a money rule.
- **Levels:** unit.
- **Classes and styles:** net out swap, funding and roll before scoring (FX, crypto, futures). Fast units reach confirmation in weeks; slow units may never confirm before their money budget acts (by design).
- **Ledger:** `drift_state`, `drift_size_down_step`, `sequential_evidence_pass`, `cusum_limit`; *`ev_min_viable_edge_r`*, *`demotion_cause`*, *`demotion_two_key_rule`*.
- **Performance:** SIM: reversible steps kept 902R of 950R after a bad week at 40 a day, against 614R for permanent demotion.
- **Survival:** the same policy saved as much as permanent demotion after a real decay.
- **Evidence chain:** e-process papers (simulation plus proofs), SIM. Weakest link: about 1,200 observations to confirm a 0.1-sigma drop (A2-155); weak edges cannot be confirmed dead fast.

#### X3-H50. Bad-day sentence and bad-day classifier [plausible]
- **Links:** A2-177 ("bad day" from the card's daily distribution), A2-166 (input-first checks), A2-174 (separate edge decay from spread, slippage, volatility and faults), A2-125 (context tags), A3-123 (strategy decay, bucket stress, account drawdown apart), A2-169 (live-day replay match).
- **Need:** N10, N14.
- **What and how:** Each morning, each unit gets one sentence: "yesterday was a one-in-24 day for a healthy unit of this type". Then a classifier sorts a bad day into four bins: bad luck (inside the card, inputs normal); bad market (fires shared with peers in the same context; SQS or isolation active); bad execution (costs, slippage or replay match out of band); possible decay (none of the above, and the slow lane moved). Only the last feeds demotion; the second feeds isolation; the third feeds the cost lane.
- **Levels:** unit.
- **Classes and styles:** news windows and weekends are contexts; FX rollover costs separated.
- **Ledger:** `daily_r_digest`, `replay_match_floor`, `cost_drift_multiple`; *`bad_day_percentile`*, *`fire_context_tags`*.
- **Performance:** a bad market day does not count against a good unit.
- **Survival:** execution decay is caught as execution, not mistaken for luck.
- **Evidence chain:** idea; the inputs exist in pieces (decay check, replay diff). Weakest link: bins overlap on real days.

#### X3-H51. Input-first drift: cost, fills, rate, hold time, replay and the paper-twin gap [solid]
- **Links:** A2-166, A2-174, A2-178 (paper twin; random-entry twin), A2-224 (cost cushion and retention), A3-083 (execution-quality record with slippage asymmetry).
- **Need:** N10.
- **What and how:** Inputs drift before profit does. Over the last 50 trades: cost per trade in R against the card (band up to 1.5x), trade rate (0.5x-2x), holding time inside the card's 10th-90th percentile, replay match at least 80 %, and the per-trade gap to the paper twin. One input out of band is yellow; two are red. A random-entry twin with the unit's own exits tells "the entry has an edge" from "the exits are kind".
- **Levels:** unit.
- **Classes and styles:** cost bands per class and hour; FX rollover and crypto funding separated from decay.
- **Ledger:** `cost_drift_multiple`, `trade_rate_band`, `replay_match_floor`, `slippage_cost`, `unit_cost_target`.
- **Performance:** fixes execution problems without demoting a good edge.
- **Survival:** early warning, weeks before P&L shows it.
- **Evidence chain:** Carver's practice (practitioner), nightly replay workflow (running). Weakest link: paper has zero slippage today, so the twin gap is all real cost.

#### X3-H52. Lifetime false-demotion budget across all units [plausible]
- **Links:** A2-152 (e-BH and e-Bonferroni across streams), A2-158 (union-bound split of a total budget), A2-159 (bounded-horizon thresholds for reversible warnings), A4-161 (alarm budget across many units).
- **Need:** N10, N12.
- **What and how:** With many units watched at once, naive per-unit thresholds push the chance of some false demotion near one. A total false-demotion budget is split across units; demotions use e-Bonferroni, review lists use e-BH. Reversible warnings use a bounded-horizon threshold instead, labelled as such.
- **Levels:** BMS over units.
- **Classes and styles:** units sharing a driver share information; correlated units count as fewer streams.
- **Ledger:** `sequential_evidence_pass`, `live_unit_count`; *`ev_lifetime_demotion_budget`*.
- **Performance:** as units multiply, good units are not demoted by sheer numbers.
- **Survival:** confirmed failures still demote.
- **Evidence chain:** e-value multiple-testing papers (simulation plus proofs). Weakest link: low power; 20 units at q = 0.05 need an e-value of 400 to demote.

#### X3-H53. Re-promotion as a new funded episode, with his click [solid]
- **Links:** A2-221 (re-promotion on an e-value plus a minimum time, not a streak), A2-158 (episode budgets), A2-153 (restarted detectors with summable weights), A2-213 (old 10 straight wins rule), A2-076 (Topstep: down after patterns, up after consistency, never automatic), A5-023 (cause review, then half the pilot budget).
- **Need:** N10, N4.
- **What and how:** After a demotion, the unit trades paper (or level 1). Re-promotion to live needs an e-value on post-cut trades past the episode's bar (smaller than the first), a minimum time, the SQS of its scope green, a cause review, and his click. It returns at level 1 and climbs by H15.
- **Levels:** unit.
- **Classes and styles:** generic; slow units take long (accepted).
- **Ledger:** `repromotion_positive_demo_trades`, `sequential_evidence_pass`, `paper_to_live_carry_rule`; *`ev_lifetime_demotion_budget`*.
- **Performance:** good units come back on evidence, not on a lucky streak.
- **Survival:** each re-promotion is paid for; resetting after every bad patch would destroy the lifetime guarantee.
- **Evidence chain:** e-process theory; Topstep practice (live). Weakest link: thin edges take months.

#### X3-H54. Regime-conditional expectation card [plausible]
- **Links:** A5-072 (judge live results against the expectation for the current regime), A2-209 (worst-regime Sharpe at promotion), A2-014 (style-aware worry lines).
- **Need:** N10.
- **What and how:** The card keeps expected results per regime the unit was validated in. Live results are judged against the expectation for the regime now in force, so a known weak regime does not read as decay. A regime the unit never saw is "unknown" and counts as yellow.
- **Levels:** unit.
- **Classes and styles:** regime labels per class (sticky regime models need their own fit per class, A2-081).
- **Ledger:** `drift_state`; *`ev_regime_expectation`*.
- **Performance:** fewer false decay calls in expected bad regimes.
- **Survival:** unseen regimes are treated cautiously.
- **Evidence chain:** FINSABER-style finding (author backtest). Weakest link: thin per-regime records.

#### X3-H55. Upside drift alarm [solid, small]
- **Links:** A2-176.
- **Need:** N10.
- **What and how:** Results above the cone's 95th percentile for two looks go yellow: check for a sizing bug, hidden shared exposure or a broker change. Size is held, not cut.
- **Levels:** unit.
- **Classes and styles:** generic; crypto trend months will trip it more.
- **Ledger:** `mc_cone_floor_percentile`; *`upside_alarm_percentile`*.
- **Performance:** a hold, not a cut, so true outperformance costs nothing.
- **Survival:** "too good" is often leverage nobody meant to take.
- **Evidence chain:** idea. Weakest link: true outperformance gets flagged.

#### X3-H56. Worry lines by style, widening with time in service [plausible]
- **Links:** A2-014 (depth lines for mean-reversion, duration lines for trend), A5-146 (drawdown thresholds widen with time), A2-015 (triple penance).
- **Need:** N10.
- **What and how:** From the unit's Sharpe, horizon and style (or its own block bootstrap), the card holds normal and worry lines for drawdown depth, time under water and time between highs. Past a line: one level down, or revise the edge estimate down. The lines widen with time in service, because a fixed line fires on healthy units more the longer they run.
- **Levels:** unit.
- **Classes and styles:** depth lines for mean-reverting scalpers (short-volatility-like); duration lines for breakout and trend.
- **Ledger:** `drift_size_down_step`, `result_spread_r`, `expectancy_r`.
- **Performance:** a trend unit is not cut for a normal long flat spell.
- **Survival:** a scalper's unusually deep drawdown is caught early.
- **Evidence chain:** Landolfi worry lines (simulation validated on closed funds), Man Group (READ). Weakest link: cannot separate bad luck from an overstated Sharpe.

### I. Coordination, spine and self-configuration

#### X3-H58. One brake registry row [solid]
- **Links:** A5-106 (nine attributes), A2-113 (declared counting rule), A2-114 and A4-058 (declared fail mode), A2-115 and A4-059 (declared equity series and base), R9 §0.2, H09, H12, H13.
- **Need:** N11, N12, N3.
- **What and how:** Every brake is one row: reads (signal and window), scope, anchor, changes (lever), direction, shape, speed (attack and release), hysteresis, memory and clear; plus counting rule, fail mode, equity series and base, expected healthy fire rate, precision, trip tax, random-control margin, authority mode, and the derivation of each threshold. A brake without a filled row cannot compile. This is the "document" the template carries for brakes.
- **Levels:** all.
- **Classes and styles:** per-class fields where the row needs them (window, gap allowance).
- **Ledger:** `loss_counting_rule`, `brake_equity_basis`, `brake_state`, `brake_precision`; *`x1_brake_shadow_mode`*, *`brake_random_control_margin`*, *`trip_tax_r`*.
- **Performance:** a brake's cost is visible on its row.
- **Survival:** "5 % drawdown" can no longer mean four things (G11).
- **Evidence chain:** R9 definitions; MQL5 risk managers make the basis an enumeration (author backtests). Weakest link: rows without anchor or clear rule hide the restart hazard.

#### X3-H59. Trading-state spine with a rank table: any brake cuts, raises need all clear [solid]
- **Links:** A2-112 and A4-063 (ACTIVE, REDUCING, HALTED, RESTORE), A5-138 (any brake blocks every raise), A4-103 (rank table), A2-004 (tightest limit wins; a local breach stays local), A2-021 and A3-178 (nearest protection trips first), A2-020 (one controller per incident), A2-046 (Nautilus states, without its stop denial).
- **Need:** N11.
- **What and how:** Each scope has one state: ACTIVE, REDUCING (smaller or no new entries; amendments only tighten), BENCHED (no new entries until the window ends or the restore passes), HALTED (no new entries until his resume), RESTORE (climbing back by steps). Every brake is a transition with a reason. The nearest scope acts first; money hard limits never wait. Any active brake blocks every accelerator; a raise needs every brake clear and no cut still settling.
- **Levels:** all.
- **Classes and styles:** generic.
- **Ledger:** `brake_state`, `control_rank_table`, `kill_switch_level`, `risk_stop_resume_rule`, `grow_back_rule`.
- **Performance:** BENCHED and REDUCING clear by rule, so a good unit is not stuck waiting for him.
- **Survival:** HALTED still needs his hand.
- **Evidence chain:** Nautilus (live, open source), X1 draft. Weakest link: two state machines on one node (states and kill levels) if not unified (H62).

#### X3-H60. Dual-timescale loop: deterministic fast loop; agents only after a trigger (QMA flagged) [plausible]
- **Links:** A2-016, A3-027 and A4-134 (SwingGuard: 5-minute rule loop, LLM only if triggered), A2-001 (kill path outside model inference), A2-017 (invariant risk core no agent can edit), A2-018 (de-risk-only channel), A2-019 (read-only incident narrator).
- **Need:** N13, N11.
- **What and how:** All brakes in this file run in deterministic code on the node. Agents enter only after a trigger, as narrators (explain which units share exposure, draft the review) or as proposers on the slow lane (H34), always de-risk only and expiring. No agent is a detector, a breaker or a re-enable authority.
- **Levels:** system.
- **Classes and styles:** generic.
- **Ledger:** `kill_switch_detector_posture`, `decision_freshness_bound`, `context_size_modifier`.
- **Performance:** fast brakes never wait for a model.
- **Survival:** agents never touch money (his line).
- **Evidence chain:** SwingGuard (author backtest, six months, two coins), FARSIGHT (simulation). Weakest link: the papers are small.

#### X3-H61. Self-configuring brake thresholds: learner, bounds, applier modes, guards [solid as a pattern]
- **Links:** A4-002 (applier with owner-chosen modes), A4-006 and A2-036 (guarded guess, named reason, freeze after N trips), A2-037 and A4-007 (Simplex fallback with a dwell), A2-038 (failed self-tune reverts; hard limits clamp even manual input), A4-005 (missing data moves the cautious way), R7 (VPA), ledger `calibration_*` ids.
- **Need:** N12.
- **What and how:** For each brake threshold: the learner recomputes the own-percentile level from the unit's growing live record, shrunk toward the card value, inside low and high bounds. The applier uses it in the mode he chose per threshold: off/shadow, at the next window start, or live. A guard watches the brake's live fire rate; if it leaves its band, the threshold falls back to the card value with a named reason; after N trips it freezes. He can change how a threshold derives (which percentile, which record, which shrink), not only its value.
- **Levels:** unit, cluster.
- **Classes and styles:** generic; minimum trades before the learner may move a value scale with trade rate.
- **Ledger:** `number_motion_mode`, `calibration_min_trades`, `calibration_shrink_k`, `calibration_cadence_trades`; *`x1_brake_shadow_mode`*, *`money_brake_percentile`*.
- **Performance:** thresholds follow the unit as it matures without a rebuild.
- **Survival:** guards and freezes stop a tuned threshold drifting loose.
- **Evidence chain:** Kubernetes VPA, HotSpot, Simplex (live in their fields). Weakest link: a freeze after noise trips locks a stale value.

#### X3-H74. Day-boundary contract: persisted counters, rolling windows, minimum rest, declared day per class [solid]
- **Links:** A2-011 (counters survive restarts and dates), A2-064 and A4-061 (confirmed, persisted day baseline), A2-116 and A3-219 (the 23:50 hole), A2-047 (LEAN re-arms from the new low: the anti-pattern).
- **Need:** N1, N8.
- **What and how:** Brake windows roll in trades or hours; a bench carries a minimum rest across the day boundary while the day budget still resets. High-water marks, counters and drained budgets persist through every restart. Each class declares its day (FX rollover; crypto a fixed UTC hour; exchange products their session).
- **Levels:** unit, account.
- **Classes and styles:** crypto and FX rollover are the main cases.
- **Ledger:** `day_boundary`, `day_start_equity`, `state_carry_rule`, `circuit_breaker_window`, `circuit_breaker_reset`; *`bench_min_rest`*.
- **Performance:** none direct.
- **Survival:** closes the hole where a unit benched at 23:50 trades again at 00:01 in the same conditions.
- **Evidence chain:** MQL5 day-baseline articles (author demo tests). Weakest link: rolling windows make "what tripped" harder to say.

### J. The kill switch and the SQS

#### X3-H62. Kill switch fit: rules raise stand-downs; the kill level goes down only by his hand [solid]
- **Links:** A2-097 (kill switch at four scopes by his hand), A2-102 (node health stand-downs that clear by themselves), A4-193 (the node's fast lane stays outside the template and feeds it as facts), A3-106 (scope keys), A2-001 (kill path outside model inference), A5-061 (kill-switch lifecycle test).
- **Need:** N8, N11.
- **What and how:** Two meanings of "stop" stay apart. The kill switch remains his: only he lowers it; the template reads its level as a fact and sizes down on it. Brakes in this file never set a kill level; they raise stand-downs in the stand-down table at a scope (instrument, unit, class, region, all), each with a reason and its own clear rule. The BMS breaker (H24) raises a stand-down at `all` and may land a card asking him to raise the kill level. A lifecycle test proves a fired stop cancels working orders and leaves exits working.
- **Levels:** node, account, BMS.
- **Classes and styles:** the kill switch gains `class:` and `region:` scopes (H35).
- **Ledger:** `kill_switch_level`, `kill_switch_scope`, `kill_switch_effect_matrix`, `kill_switch_detector_posture`, `risk_stop_resume_rule`.
- **Performance:** automatic stand-downs clear by rule; only the kill level waits for him.
- **Survival:** the one control that "earned its spot" stays untouched in authority.
- **Evidence chain:** running kill switch (old rule, running). Weakest link: two tables a user must understand; the UI must show both (X6).

#### X3-H63. SQS as a sensor, not only a gate [solid]
- **Links:** A2-111 and A3-075 (SQS), A2-063 (two windows), A4-193, H29, H50, H51, H15.
- **Need:** N8, N7.
- **What and how:** SQS keeps its job: block new entries on one instrument, never shrink. Its state also feeds: the class caution (H29); the bad-day classifier (H50, bad market or bad execution); the cost lane (H51); and the restore gate (no probe and no re-promotion while the scope's SQS is not green, H15, H53).
- **Levels:** node, instrument, class.
- **Classes and styles:** baselines per instrument, session and broker; stocks via CFD have no last-price ticks.
- **Ledger:** `sqs_score`, `sqs_hard_block_threshold`, `sqs_hysteresis_band`, `sqs_baseline_conditioning`.
- **Performance:** one sensor, many uses.
- **Survival:** liquidity is checked before any restore.
- **Evidence chain:** SQS built (off the path), spread percentile gate (mechanism checked). Weakest link: SQS is not in any MIS pack today.

### K. Performance side

#### X3-H64. Cost-of-conservatism meter (the sitting-duck meter) [solid]
- **Links:** A5-073 (share of time under baseline and the return missed), A4-202 (trip tax), A2-145 (would_have rows), A2-030.
- **Need:** N14.
- **What and how:** For each unit, cluster and the BMS: share of time and capital below baseline, and the R the baseline would have earned in that time, split by the brake that held it there. A brake whose trip tax exceeds the loss it avoided over a quarter is flagged.
- **Levels:** all.
- **Classes and styles:** generic.
- **Ledger:** `brake_precision`; *`under_baseline_share`*, *`trip_tax_r`*.
- **Performance:** puts his M33 point ("I don't want just safety") on screen as a number.
- **Survival:** a counterfactual cannot see that a braked unit might have hit the floor; read with H12.
- **Evidence chain:** EvolveTrade's losing windows held far more cash than the baseline (author backtest). Weakest link: counterfactuals can be gamed.

#### X3-H65. Choke budget per brake [plausible]
- **Links:** SIM, R9 §4.1, H09, H12.
- **Need:** N1, N14, N12.
- **What and how:** A new kind, a clamp on brakes. Each bench-type brake declares its expected healthy fire rate from the card (H09). The template refuses, or forces shadow for, any bench-type brake whose expected healthy fire rate times the edge it throws away per fire exceeds a choke budget (a share of the unit's expected R). A working default: about 5 % of days for a bench brake, because SIM brakes at or under that rate kept 97 % or more of healthy R, and brakes at 40-100 % kept 18-84 %.
- **Levels:** unit, cluster.
- **Classes and styles:** generic; the derivation reads the unit's own frequency.
- **Ledger:** *`choke_budget_fire_rate`*, `breaker_expected_fire_rate`.
- **Performance:** no default brake can quietly throw away a fifth of a healthy unit's edge.
- **Survival:** brakes with timing value but high fire rates go to shadow, not to the bin, and can be switched on by H06.
- **Evidence chain:** SIM only. Weakest link: model arithmetic; real fire rates need the unit's card.

### L. Agents near brakes, and wild ideas

#### X3-H66. Danger accumulator brake (immune model) [wild]
- **Links:** A2-070 and A3-122 (accumulate weak danger signals; clear danger acts at once), A2-061 (execution anomaly), A2-162 (changepoint probability), A2-069 (stress-percentile spread).
- **Need:** N1, N7.
- **What and how:** Weak danger signals (spread percentile, execution anomaly, changepoint probability, loss points) are summed over a window; the unit is halved only when enough have gathered. Clear danger (disconnect, state mismatch) acts at once. An "inflammation" term raises sensitivity during news windows. A node-health hazard (rejects, stale quotes, disconnects) may set the soft-kill exit schedule.
- **Levels:** unit, cluster.
- **Classes and styles:** signal weights per class.
- **Ledger:** `brake_precision`; *`danger_accumulation_window`*.
- **Performance:** fewer single-signal false trips.
- **Survival:** clear danger still acts at once.
- **Evidence chain:** an analogy in the MQL5 corpus that drives an optimiser, not a risk tool. Weakest link: the weights are a new tuning surface.

#### X3-H67. Brakes stake testing wealth [wild]
- **Links:** A2-220 (alpha investing; agents bid family wealth), A2-201 (Promote testing wealth), A2-135.
- **Need:** N3.
- **What and how:** Each brake holds testing wealth. Each fire is a bet that a loss follows; the bet pays when the next window is worse than the random twin's, and costs when it is not. A brake whose wealth reaches zero retires to shadow by itself; a brake that keeps paying earns the right to a tighter threshold.
- **Levels:** unit, cluster.
- **Classes and styles:** generic.
- **Ledger:** *`brake_random_control_margin`*.
- **Performance:** brakes that only cost get retired without anyone deciding.
- **Survival:** brakes that work are kept and sharpened.
- **Evidence chain:** idea on e-value theory. Weakest link: thin fire records give small bets.

#### X3-H69. Get-even flag for humans and agents [plausible]
- **Links:** A5-085 (flag any size increase right after a loss), R8 §2.1 (Nasdaq traders raised risk after morning losses and lost more), R9 §3.1 (who asks for more credit is the worst borrower), A5-078.
- **Need:** N13, N1.
- **What and how:** Any size or limit increase proposed within a window after a loss (by him through the UI, by the copilot, by an agent) is flagged. For agent proposals it is refused; for his manual changes it is a warning he can override.
- **Levels:** unit, system.
- **Classes and styles:** generic.
- **Ledger:** *`post_loss_raise_window`*.
- **Performance:** keeps planned accelerators (X2) untouched; only increases after losses are targeted.
- **Survival:** blocks the get-even pattern that cost prop traders $4,300-14,400 a year more.
- **Evidence chain:** Garvey-Murphy-Wu (READ in R8, one firm, one year). Weakest link: one desk's behaviour.

#### X3-H70. Drawdown cuts agent autonomy as well as size (QMA flagged) [plausible]
- **Links:** A5-078 (AllPath drawdown breaker moves an agent back to human-confirmed revisions).
- **Need:** N13.
- **What and how:** When a unit's slow lane goes red, any agent that may auto-apply revisions to that unit's template falls back to proposals needing his click until a human resets it.
- **Levels:** unit, system.
- **Classes and styles:** generic.
- **Ledger:** `drift_state`.
- **Performance:** none direct.
- **Survival:** a self-revising agent cannot argue its way out of a drawdown.
- **Evidence chain:** AllPath (live in its own system). Weakest link: human resets become routine.

#### X3-H71. Execution-anomaly brake on fills, pause only [plausible]
- **Links:** A2-061 and A3-082 (isolation forest on fills), A2-135.
- **Need:** N8, N10.
- **What and how:** Each fill's slippage, spread, latency and markout are scored against the unit's own recent fills; a joint anomaly pauses entries on that instrument. It never widens stops (stops only tighten). Its value is measured on demo and live streams against a random pause.
- **Levels:** instrument, unit.
- **Classes and styles:** per broker and symbol.
- **Ledger:** `slippage_cost`, `spread_cost_guard`, `stop_widening_allowed`.
- **Performance:** cheap: it acts only on odd fills.
- **Survival:** catches a broker problem early.
- **Evidence chain:** mechanism checked (simulation); a tester P&L test is close to null by construction. Weakest link: needs live fill history.

#### X3-H72. Changepoint de-risk cooldown, proven against random [plausible]
- **Links:** A2-162 and A3-065 (BOCPD de-risk beat a random brake: max drawdown 856 → 756 skipping 4 of 97 trades), A2-163 (duration-aware hazard; flag only when the most likely run length falls), A2-150 (price CUSUM fitted per instrument).
- **Need:** N1, N7.
- **What and how:** A price-side changepoint detector (duration-aware) cuts size for a short cooldown after a break, at the instrument level. It is the one fast brake in the corpus with a fair-controlled test. Thresholds are fitted per instrument (theory thresholds fire about five times too often).
- **Levels:** instrument, unit.
- **Classes and styles:** sharp volatility breaks detected within a bar or two; small mean shifts slowly; crypto and FX untested.
- **Ledger:** `drift_state`, `context_size_modifier`, `cusum_limit`.
- **Performance:** skips few trades.
- **Survival:** small drawdown cut in the one test.
- **Evidence chain:** MQL5 23482 (controlled test, author's, small). Weakest link: all three arms lost money; a brake does not make an edge.

#### X3-H73. Regime-age taper on new adds [wild]
- **Links:** A2-173, A1-048 and A3-061 (hidden semi-Markov durations).
- **Need:** N1.
- **What and how:** New adds and pyramids taper as the current regime ages, because a semi-Markov model makes regime age informative.
- **Levels:** unit.
- **Classes and styles:** tested on XAUUSD M5 only; durations differ by class.
- **Ledger:** `context_size_modifier`.
- **Performance:** fewer late adds near a regime's end.
- **Survival:** small.
- **Evidence chain:** one 8-month gold test (author backtest; the system as a whole lost). Weakest link: short sample.

### Count by maturity

| Maturity | Hybrids |
|---|---|
| Solid (31) | H01, H04, H09, H12, H13, H14, H15, H22, H25, H29, H31, H33, H35, H36, H39, H43, H45, H46, H48, H49, H51, H53, H55, H58, H59, H61, H62, H63, H64, H74, H75 (H39 is solid as a method and H43 as a structure; their evidence is thin) |
| Plausible (38) | H02, H03, H05, H06, H07, H08, H10, H11, H16, H17, H18, H20, H21, H23, H24, H26, H27, H28, H30, H32, H34, H37, H38, H40, H41, H42, H44, H47, H50, H52, H54, H56, H60, H65, H69, H70, H71, H72 |
| Wild (3) | H66, H67, H73 |

Exact tally: 72 hybrids; 31 solid, 38 plausible, 3 wild.

## 3. Problems and solutions

Diagnosis for each is in `linking\stage-b\X3-brakes-exits-drift\problem-solving.md`. Every problem has at least two options; none is picked here.

**P1. Count brakes punish frequency and fast invalidation** (his A28, C31, C33).
- Option A, money at the unit's own percentile over a window of 10+ trades (H01). Trade-off: fair and cheap (99.4-99.8 % of healthy R kept, SIM) but little timing on independent trades; depends on an honest card.
- Option B, loss points at own p99 (H03). Trade-off: answers "count FI by size" directly; needs R and exit mechanisms on every row (H45); weak alone.
- Option C, keep counts but scale them: run length past the unit's own p99, qualifying losses only, halve not bench (H05). Trade-off: closest to his words and to the old breaker; not yet simulated in scaled form.
- Option D, the graded ladder (H02). Trade-off: more bad-spell benefit (up to +43R) for 1-2 % more healthy cost.

**P2. The circuit breaker's decay role is slow** (his A26).
- Option A, two keys: trade CUSUM fast, fire density calm (H11). Trade-off: needs both statistics and a rank rule; best SIM result.
- Option B, Basel zones on the fire count at planned looks (H08, H48). Trade-off: simple to explain, regulatory history; slow at 2-10 trades a day.
- Option C, context-tagged density pooled per methodology (H10, H23). Trade-off: catches a logic fading everywhere; pooled correlated units overstate evidence.

**P3. A brake may only be trading less.**
- Option A, random-control certificate per brake (H13). Trade-off: the fair test; noisy on thin units.
- Option B, certify brake types per family, thresholds per unit (roundtable). Trade-off: more data per test; assumes brake value transfers within a family (A5-029 warns it may not).
- Option C, brakes stake testing wealth and retire themselves (H67). Trade-off: automatic; wild, untested.

**P4. Brakes hold units below baseline too long.**
- Option A, half-open probe ladder (H15) with memory ceiling (H17). Trade-off: ends benches on evidence; probes are noise for the edge, so they test the machine and conditions only.
- Option B, restore priced in evidence for slow-lane demotions (H18). Trade-off: no lucky-streak return; thin edges come back slowly.
- Option C, measure it: trip tax and under-baseline share on every brake (H12, H64), plus a choke budget (H65). Trade-off: makes cost visible; counterfactuals ignore paths where the brake saved the floor.

**P5. Low-frequency units (ORB, swing) cannot be judged on one day.**
- Option A, windows in trades, not days (H01: a 2-a-day unit gets a 5-day window). Trade-off: fair; a window crosses days, so "today's brake" wording changes.
- Option B, calendar looks with alpha spending (H48). Trade-off: valid error rates; slow.
- Option C, pool across the family and across markets (H23; his ORB breadth, D11). Trade-off: faster proof; correlation discount required.
- Option D, duration worry lines for trend and breakout (H56). Trade-off: suits their drawdown shape; cannot tell bad luck from an overstated Sharpe.

**P6. Losing together is counted as many strikes** (his C32).
- Option A, the hours-clause ledger (H20). Trade-off: one event, one count; window edges are contentious.
- Option B, chorus breaker K of N with correlation-inflated expectation (H21). Trade-off: sees co-movement; ρ needs weeks of data.
- Option C, the BMS cushion clip with a worst move per class (H25). Trade-off: a hard guarantee short of gaps; not a detector.

**P7. Class isolation has no scope, tells or tests** (his C27).
- Option A, two-tell bucket isolation with a precision record, in shadow first (H28). Trade-off: broad; thresholds untested intraday.
- Option B, SQS K of N class caution (H29). Trade-off: cheap and early for liquidity events; misses price-only shocks.
- Option C, peer ejection with a capped share (H30). Trade-off: catches one bad market or unit; misses whole-class degradation (needs an absolute floor).
- Option D, agent cards for slow deterioration (H34). Trade-off: sees what minute tells cannot; needs his click or a TTL rule and provenance checks.
- Prerequisite for all: scope keys (H35) and fail-closed unknown data (H36).

**P8. News windows choke scalpers or under-protect** (his C28).
- Option A, widths by measured impact per release and instrument; tier chosen per unit template (H31). Trade-off: hours back for scalpers; impact must be re-measured.
- Option B, the April soft kill (staged exits before release) for units that hold through. Trade-off: flat through the release; staged exits into widening spreads cost money (A3-126).
- Option C, region shift without rotation (H32). Trade-off: other regions keep trading; crypto has no region.

**P9. FI has no cut size and no literature** (his A9).
- Option A, cut from winners' MAE plus an edge-peak time stop; must beat "no cut" and "one bar later" (H39). Trade-off: per-unit, data-driven; in-sample unless held out.
- Option B, thesis-based falsifying condition (H40). Trade-off: fires on the premise, not noise; needs codable conditions.
- Option C, survival-analysis hazards (H42). Trade-off: uses the whole open-trade state; its one test lowered profit factor.
- Option D, a family-pooled cut level shrunk toward each unit's own. Trade-off: usable for new units; may not fit a unit's own paths.

**P10. Which stop mechanism per style** (his A10, A28).
- Option A, stopping-premium gate on the unit's own persistence (H38). Trade-off: principled; persistence shifts by era.
- Option B, exit families per style as the default (H43). Trade-off: works out of the box; cells rest on thin studies.
- Option C, an entries-fixed two-arm test per instrument for any stop change (A2-139). Trade-off: clean proof; one test per instrument is slow.

**P11. The dynamic SL/TP and breakeven have no evidence** (his M15).
- Option A, breakeven off by default; on only after the two-arm test, with a data-set trigger and a cost-covering offset (H41). Trade-off: no untested habit; intraday units wait for proof.
- Option B, replace blanket breakeven with a risk-state invalidation exit (A2-266). Trade-off: reacts to real danger; thresholds untested.
- Option C, keep the Gen 3 ratchet per Book with a filled trigger as a template option. Trade-off: built already (`ratchet.py`); no evidence it pays.

**P12. Bad day vs broken edge** (his A25).
- Option A, graded, reversible demotion (H49). Trade-off: best SIM outcome after bad weeks; slow units still bleed a little before confirmation.
- Option B, two-key demotion (H11). Trade-off: fewer false demotions; slower to paper.
- Option C, the bad-day classifier (H50). Trade-off: explains each bad day; bins overlap.
- Option D, regime-conditional expectations (H54). Trade-off: fewer false calls in known regimes; thin per-regime data.

**P13. Re-promotion rules are weak.**
- Option A, a new funded episode: e-value plus minimum time plus his click (H53). Trade-off: honest; slow for thin edges.
- Option B, the Topstep pattern: up one tier after a dwell of active days, down the same day. Trade-off: live-tested practice; no effect measure published.
- Option C, BOIN cohorts at level 1 (A2-190). Trade-off: simple; a fixed toxicity target can let a dead unit climb.

**P14. Many brakes fire together.**
- Option A, the trading-state spine with a rank table (H59). Trade-off: one place to reason; needs the kill level kept separate (H62).
- Option B, one controller per incident with a root-cause key (A2-020). Trade-off: dedups alerts; a central controller is a single point of failure, so hard limits must not depend on it.
- Option C, grid selectivity: nearest scope first, backups wait, money limits never wait (A2-021). Trade-off: local breaches stay local; graded delays must never apply to money hard limits.

**P15. The kill switch and automatic brakes.**
- Option A, rules raise stand-downs; the kill level is his (H62). Trade-off: clean authority; two tables in the UI.
- Option B, the BMS breaker may raise the kill level itself (to YELLOW or ORANGE), only he lowers it. Trade-off: one table; changes a control that "earned its spot".
- Option C, the kill switch stays manual and automatic paths only land cards. Trade-off: no automation in emergencies; slow at night.

**P16. Self-tuned thresholds drift into nonsense.**
- Option A, VPA learner with bounds and applier modes (H61). Trade-off: safe pattern; needs an applier the stack lacks.
- Option B, HotSpot guard: fall back to the card value and freeze after N trips. Trade-off: robust; can freeze a stale value.
- Option C, Simplex: a fixed safe threshold set takes over when projected drawdown leaves a safe region. Trade-off: guaranteed fallback; a wrong safe region gives false confidence.

**P17. Units with no price stop have no R.**
- Option A, R from a tail-loss budget of the realised loss distribution (H44). Trade-off: works for any unit; needs a loss history.
- Option B, money brakes in dollars from the unit's budget share. Trade-off: simple; not comparable across units.
- Option C, volatility units: daily sigma = sqrt(N) x sigma per trade x risk per trade (R9 §4.2). Trade-off: comparable; assumes a stable trade distribution.

**P18. Agents near brakes** (QMA flagged).
- Option A, de-risk-only, typed, expiring proposals; precision recorded per agent (H34, H60). Trade-off: safe; still costs trades on fake bad news.
- Option B, agents as narrators only (A2-019). Trade-off: no money effect at all; loses the slow-isolation lane.
- Option C, drawdown cuts agent autonomy (H70) and the get-even flag refuses agent raises after losses (H69). Trade-off: guards against the worst agent habits; needs his resets.

## 4. Collisions (named, not resolved)

**With his words**
1. **The old breaker's count.** He named "if you had a full stop loss ... 2 times you stop trading" as the baseline to improve (A26). SIM says that trigger keeps 18-65 % of a healthy fast unit's R; H01 replaces the count with money or loss points and keeps his decay role in H08. Replacing the trigger may be more than he meant by "improve".
2. **"Three losses or a pattern"** (A6) against frequency fairness: H05's scaled run length is not three.
3. **"Size down ... but not quickly"** (A25) against "money brakes act fast" (C19) and against SIM: at 40 trades a day the trade CUSUM reacts within days. H49 splits by signal type; a fast unit's warning still cuts within days.
4. **Isolation "kicks in with evidence"** automatically (C27) against "only he promotes": restoring an isolated class is a widening. Is an automatic resume after a time to live a promotion?
5. **"The kill switch earned its spot"** (C21) against a BMS breaker that switches off everything automatically (C27): either the breaker uses stand-downs (H62) or the kill switch gains an automatic raise.

**With the grounding and the stack**
6. **Automatic demotion to paper** (old breaker, H11, H49) against the stack: a risk rule can only move paper or live to `stopped`; leaving `stopped` is his click (G9 §1.4). H59 adds BENCHED and REDUCING states that clear by rule; the stack has no such states.
7. **Automatic restore** (H15) against `risk_stop_resume_rule` (his resume). Only benched and reduced states restore by rule; whether that satisfies the rule is open.
8. **The compiler refuses halts and readings** (G8 blocker 1), and the sizer gets equity, entry, stop and record only (G8 blocker 3). H01-H07 and H44 cannot run until both change.
9. **Exits after entry do not run** (G8 blocker 4: only the first per-bar exit runs, fed an empty dict). H39-H43 need positions passed to exits and `close_partial` and `amend_protection` sent.
10. **The MIS never switches a unit on or off** (A3-184) against H36's "isolation published on the board; placement fails closed".
11. **Nautilus HALTED denies protective stops** (A2-046) against "exits are never blocked": copying Nautilus states as-is would break his line.
12. **The execution-anomaly source reacts by widening stops** (A2-061) against "stops only tighten" (A2-245).
13. **April region-shift rotation** against July law L4 ("never redistribute freed budget in a cycle"); H32 keeps L4.

**With other layers**
14. **X2 (sizing and accelerators):** brakes outrank accelerators (H59), so X2's house money, ladders and persistence presses are frozen whenever any brake here is active or settling. A probe above baseline (R9's BBR "probe", my old H68) is an accelerator and belongs to X2; if X2 adds it, it collides with H17's memory ceiling.
15. **X2 and H07:** R9 found the AIMD pair favourable because it could raise size to 2.0x; as a pure brake it chokes (SIM). Same mechanism, opposite verdicts, depending on whether the accelerator half exists.
16. **X5 (edge verification):** counting rules must agree. If verification counts a breakeven as a non-win while brakes count it at cost, the same trade means two things (X5 draft C12). Breakeven exits also add scratches that lengthen proof.
17. **X5:** the card's thresholds (H09) depend on an honest holdout; X5's "plan at the deflated holdout edge" and my "fire band from the holdout" may use different holdouts.
18. **X1 (template shape):** two state machines on one node (trading states and kill levels) unless H62's split is adopted; X1's draft proposed `reduce{factor, steps}` on the halt slot, H02 needs the same.
19. **X6 (observability):** two stop tables (kill level and stand-downs) must both be shown, with "what tripped" per brake; the brake registry row (H58) is the data source.
20. **X7 (agents):** de-risk-only agent channels change size. Is that "touching money"? H34, H60 and H70 assume it is allowed when it can only cut and expires.

**Between my own hybrids**
21. **H01 (no timing, near-free) against H05 and H06 (timing in bad spells, costly):** which is the unit default is open.
22. **H08 density (calm, slow) against H11's fast key:** at 40 a day the fast key alarms on half of all bad weeks.
23. **H15 automatic restore against H18 restore priced in evidence:** short benches restore by probe, slow-lane demotions by e-value; the line between them is a choice.
24. **H25 cushion clip (a clamp, reads exposure) against H26 pod ladder (a brake, reads drawdown):** both cut a unit's room at BMS scope from different signals.
25. **H65 choke budget against H06:** a streak brake with real timing value would be forced to shadow by the choke budget unless the persistence test switches it on.
26. **Windows in trades (H01) against the declared day (H74) and his daily framing:** a 5-day window for ORB is not a "daily" brake.
27. **Minimum lot at $500** against every halve step (H02), probe (H15) and level ladder: on gold or index contracts the smallest live size may already exceed the probe's money.

## 5. Restructure proposals

1. **Replace the circuit breaker's count trigger with own-percentile money or loss points (H01, H03).** The count moves to the event ledger as evidence (H04). Why it performs better: SIM keeps 99.4-99.8 % of a healthy unit's R against 18-65 % for "2 full stops" at 10-40 trades a day, at the same 1 % fire rate across every frequency.
2. **Replace the binary risk stop with a five-state spine** (ACTIVE, REDUCING, BENCHED, HALTED, RESTORE) where only HALTED waits for his hand (H59). Why: reversible steps kept 902R of 950R after a bad week where permanent demotion kept 614R (SIM); the stack today can only stop.
3. **Replace the nightly 20-trade decay check** (Watch and Alarm on 5 and 8 losses in a row, A2-168) with the two-key slow lane (trade CUSUM or e-detector, plus fire density against the card's band) read at planned looks in three zones (H11, H48). Why: the 20-trade check has the count flaw and ignores the card; the CUSUM caught a dead edge in 92-99.5 % of runs at 4-40 trades a day.
4. **Replace the Book's day-budget door** (refuse at zero or below one trade, never defined) with a two-window burn-rate permit and a taper (H22, H02). Why: no cliff; fast burns still halt; spent budgets also freeze accelerators.
5. **Cluster by shared driver for brakes, not by style label.** The Book stays the capital container (X2's call), but the cluster that brakes, chorus and the hours clause read is built from driver tags and measured result correlation (H20, H21). Why: correlated losses come from shared drivers (USD, equity beta, BTC), not from "all mean-reverting scalpers".
6. **Move isolation ownership to the BMS with scope keys** (class, region, currency, underlying, session) that fail closed and are published to the board (H35, H36). Why: today no class scope exists anywhere, and the board fails open, the wrong way for isolation.
7. **Replace "first per-bar exit, fed nothing" with an exit stack**: safety exits and strategy exits, the safest wins by rank, exit families per style, every exit proven by an entries-fixed two-arm test (H43, H46). Why: today a unit cannot run FI, breakeven or any trailing exit after entry (G8).
8. **Add a brake registry row as a compile-time requirement** (H58). Why: "5 % drawdown" meant four things across generations (G11), and no brake has ever stated its expected fire rate or its cost.

## 6. Gaps (what no component covers)

- **Fast invalidation evidence:** no study tests a fractional early cut after costs (R8 gap 2). H39 is a method, not a result.
- **Breakeven evidence:** no peer-reviewed test of breakeven moves after costs.
- **Restores in practice:** no source says how pods restore a cut allocation; Topstep is the only automatic rule-based restore found.
- **Intraday persistence:** no study measures win or regime persistence in intraday retail-style strategies after costs (R9), so the timing value of count brakes is a model result only.
- **Class isolation tests:** the risk-off readings (turbulence, correlation surprise, absorption ratio) are daily-data studies; none is tested as an intraday isolation trigger.
- **Units with no price stop:** no brake or R definition exists for them in any generation.
- **Multi-unit brake arithmetic:** my SIM runs one unit at a time; chorus, hours clause and BMS breaker numbers need a correlated multi-unit simulation (X4 scenarios).
- **Gaps and fat tails in brake sims:** SIM has neither; every fire rate here is a floor.
- **Energy and single stocks:** brakes rest on contract facts (EIA, halts) only.
- **Agent isolation precision:** no source measures how often agent-proposed isolations were right.
- **Fire bands on cards:** the B13 card holds a cone but no per-brake expected fire rate; H09 needs QMB to produce it.
- **LLM crowding inside QMX:** many similar units reacting to one headline (A3-165) has no QMX-specific brake beyond the chorus breaker.

## 7. Questions only he can answer

1. **Automatic steps without his click.** May a unit move live → paper, and back from benched or reduced to full size, by rule alone, while only a HALTED unit waits for him? (This sets how much of H11, H15 and H49 runs unattended.)
2. **The BMS breaker and the kill switch.** When the BMS breaker fires, should it raise the kill switch itself (he lowers it), or only stop entries and send him a card?
3. **Agent isolation cards.** May an agent's de-risk-only isolation card (with evidence and an expiry) apply by itself, or must every isolation wait for his click?

## Appendix A. Method record

- BMad brainstorming, headless: `.memlog.md` (92 entries: seven technique markers, the ideas, seven insights), `brainstorm-working.md` (Morphological Analysis, Concept Blending, Forced Relationships, Cross-Pollination, Trait Transfer, Evolutionary Pressure with its selection rule, Solution Matrix with the empty cells), `brainstorm-intent.md`. No HTML, as the brief says.
- `bmad-cis-problem-solving`, headless: `problem-solving.md` (18 problems, is / is-not, root cause, validation). Solutions are in section 3 above.
- `bmad-party-mode` roundtable, headless: `party-mode-roundtable.md` (pod-shop risk manager, retail scalper, platform engineer, his voice from his recorded words, grid protection engineer, trial statistician, sceptical quant, 24/7 crypto trader). Its seven amendments are folded into H01, H11, H13, H15, H28, H30, H41, H49 and H62.
- Arithmetic: `x3_brake_sim.py` (standard library; `python -I x3_brake_sim.py 200`, about 2.5 minutes), output `out-200.txt`.

## Appendix B. Ledger additions

`ledger\additions\X3-brakes-exits-drift.yaml` adds 30 new variables, all with status `proposal` or `idea`, sources `gen: expansion` or `research`, and couplings to v0 ids. Existing v0 ids are reused wherever the idea already exists (for example `loss_points_bench_threshold`, `breaker_expected_fire_rate`, `cusum_limit`, `isolation_scope`, `kill_switch_scope`); where a v0 entry lacks a derivation, a new entry feeds it through `affects` instead of redefining it.

Ideas another Stage B layer had already added are reused, not redefined (the checker was run with those files loaded):

| Idea here | Id reused | File |
|---|---|---|
| money brake percentile | `money_brake_percentile` | `X0-trading-lens.yaml` |
| breadth scale for weekends | `day_budget_breadth_scale` | `X0-trading-lens.yaml` |
| brake mode and enforcing ramp | `x1_brake_shadow_mode`, `x1_enforcement_percent` | `X1-template-shape.yaml` |
| half-open probe count | `x1_restore_probe_trades` | `X1-template-shape.yaml` |
| scope keys | `x1_scope_key_set` | `X1-template-shape.yaml` |
| expected fire band | `ev_brake_fire_band` | `X5-edge-verification.yaml` |
| look schedule, minimum viable edge, zones, regime expectation, lifetime false-demotion budget | `ev_look_schedule`, `ev_min_viable_edge_r`, `ev_zone_rule`, `ev_regime_expectation`, `ev_lifetime_demotion_budget` | `X5-edge-verification.yaml` |
| fire tags, event ledger, demotion cause, bad-day percentile, recall, trip tax, under-baseline share, upside alarm, burn-rate page and ticket | `fire_context_tags`, `event_ledger_rates`, `demotion_cause`, `bad_day_percentile`, `brake_recall`, `trip_tax_r`, `under_baseline_share`, `upside_alarm_percentile`, `burn_rate_page_threshold`, `burn_rate_ticket_threshold` | `X6-observability.yaml` |
| get-even window | `post_loss_raise_window` | `X7-agents.yaml` |
| AIMD cut and add step, last trip level, settle trades, block persistence, worst move per class, stressed stop slippage | `aimd_cut_factor`, `aimd_add_step`, `last_trip_size_level`, `size_change_settle_trades`, `block_persistence_score`, `worst_step_move_r`, `stressed_stop_slippage_r` | `X2-sizing-accelerators.yaml` |
| isolation mode, isolation time to live, exits-never-blocked invariant, settling time, resume size, bench minimum rest, floor-breach dwell, post-shock reserve, automatic retries before lockout | `isolation_mode`, `isolation_ttl`, `exits_never_blocked`, `settling_time`, `resume_size_fraction`, `bench_min_rest`, `floor_breach_dwell_s`, `disturbance_reserve_share`, `bench_retry_max_in_window` | `X4-scenarios.yaml` |

Notes on the X2 reuse: X3-H07 uses X2's `aimd_cut_factor` and `aimd_add_step` with one difference, a ceiling at baseline, because here the pair is a brake and its restore, never an accelerator; X2's `worst_step_move_r` is in R at a typical stop, which is the form the cushion clip (H25) and the order veto (H75) need. `retrip_backoff_multiplier` here covers a unit's restore cool-down as well as an isolation's time to live; X4's `isolation_retrip_backoff` is the isolation-only form. Near matches kept separate on purpose: `level_lockout_days` (a level locks after two trips there) differs from X5's `ev_level_lockout` (a level locks on a bad-cohort rate); `money_brake_window_trades` and `money_brake_threshold_r` refine X0's daily `money_brake_percentile` to a window of at least ten trades.
