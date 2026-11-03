# X0: the trading lens

Stage B, 3 Nov 2026. Layer X0 sets the frame the other layers hang from: portfolio first, then style and timeframe, then market structure, then the per-class matrix. Everything here is expansion, not a pick. The Fable judge ranks (`linking/RANKING.md`).

## How to read this

- Component ids are short: `A1-070` is `A1-sizing-allocation-070`; `A2-` is brakes-drift-exits; `A3-` is structure-regimes-scenarios; `A4-` is template-agents-telemetry; `A5-` is topup.
- Brake, accelerator, restore and clamp follow `research/R9-accelerators-and-brake-pairs.md` section 0. One extension is proposed here: a **cell default**, a number whose derivation is owned by a style x class cell rather than by a level (section 1).
- Each hybrid carries: id; components; need; what it does and how; levels; per class and style; ledger ids; performance note; survival note; evidence chain with the weakest link named; maturity (solid, plausible, wild). Wild ones are kept.
- Ledger additions are in `ledger/additions/X0-trading-lens.yaml` (27 new variables). Existing ids are reused as they stand.
- Opinions are marked **[judgment]**. Arithmetic I did myself is marked **[arithmetic]**.
- Brainstorm record: `linking/stage-b/X0-trading-lens/.memlog.md` (71 entries) and `brainstorm-intent.md`. The problem-solving pass and the roundtable are sections 3 and 7 of this file.

## 0. What this layer says in one page

The template is not one list of numbers. It is a **matrix**: three styles (scalping at 1-5 minutes and tick; intraday at session opens, opening ranges and mean reversion inside the day; swing over days) by seven instrument classes (FX, indices, metals, energy, crypto, futures, stocks). Every cell answers five questions, and every other layer's default is a value in a cell:

1. **The risk unit.** What one R is, in account currency, with costs and the cut inside it.
2. **The stop and the fast-invalidation cut.** Which exit protects the trade, and what a cut costs.
3. **How frequency shapes the brakes.** Which signal a brake reads, in what window, so it fires on danger and not on healthy noise.
4. **What costs do to size.** Which cost line binds and how it reaches the sizer.
5. **Which accelerators can pay.** Which raise above baseline has evidence in that cell, and which never does.

Above the matrix sits the **portfolio frame**: one loss currency; a day risk budget split by effective bets; style sleeves as risk shares; a cushion ledger with declared anchors at every level; a slow macro governor; isolation by underlying process; three signals kept apart; a staged ramp for new units; co-loss accounting. Below it sits **market structure**: two per-instrument-hour tables (volatility and cost); a venue rule that routes microstructure methods; news as measured impact; regimes that cut gross and never re-weight.

**The frame in his words.** Risk less, do it many times, across markets, around the clock (C1). The system carries the load so a weak real edge still pays (A24). Brakes first, accelerators second (C19). Nothing is set in stone (M31). The matrix is how "one template per unit type" (A5) and "the multi-instrument lens on everything" (M26) become one thing instead of two.

## 1. Decision points the other layers must answer

Starter list; widen as the components go.

| Layer | Decision the trading lens hands over | Where it comes from here |
|---|---|---|
| X1 template shape | Is the override chain keyed by style x class cell (X0-44), with holding horizon as a number on the unit (X0-49)? Do the three sleeve numbers (routine, stress, feasible) live on the unit document? | X0-01, X0-44, X0-49 |
| X1 | Does the compiled unit carry the two hourly tables, or read them from the node? What happens when a cell is missing? | X0-37 |
| X2 sizing | Baseline rule per cell: day share by effective bets (X0-02), then the cell's bound (X0-17, X0-23, X0-31). Is the edge a gate or an amount (X0-04)? | X0-02, X0-04, X0-13, X0-17, X0-23, X0-31 |
| X2 | Which accelerator kinds are allowed per cell (X0-19, X0-29, X0-35), and what caps them (X0-12)? | sections 2.2-2.4 |
| X3 brakes | Which signal per cell: money quantile for high-frequency (X0-16), daily ladder for intraday (X0-28), drawdown and decay for swing (X0-34). The hours clause for every count (X0-10). Three signals apart (X0-08). | X0-08, X0-10, X0-16, X0-28, X0-34 |
| X3 | Stop policy per logic by a test, not by style name (X0-15, X0-24, X0-32). | X0-15, X0-24, X0-32 |
| X4 scenarios | The per-class worst one-step move table and the scenario families the matrix needs (gaps, fixes, news every hour, crypto weekend, roll, halt). | X0-27, X0-39, X0-40, X0-54, X0-55 |
| X5 verification | The admission gate per cell (X0-14), the two-arm exit test (X0-15), counted window tries (X0-47), the dry chassis per cell (X0-50). | X0-14, X0-15, X0-47, X0-50 |
| X6 observability | The exposure ledger rows (X0-11), the feasibility verdict per class (X0-45), the cost-of-conservatism meter (X0-52), blocked-minute shares (X0-30, X0-39). | X0-11, X0-45, X0-52 |
| X7 agents | What agents propose in this frame: windows (X0-47), isolation evidence (X0-07), macro state (X0-06), driver tags for news (X0-39), microstructure summaries at slow cadence (X0-38). Never a size. | X0-06, X0-07, X0-38, X0-39, X0-47 |
| MIS (flagged, not designed) | Placement needs a widen door; today the MIS only narrows (A3-184). Activity sessions for crypto. Persistence readings as placement inputs. | X0-21, X0-26, X0-46 |
| Numbers lens (his) | The day budget, the floor, the class caps' first values, the macro table's first values. | X0-02, X0-05, X0-06, X0-41 |

## 2. Hybrids

Grouped by level. Ids are not in numeric order inside a group; the index at the end of the file lists them all.

### 2.1 Portfolio frame

#### X0-01. One loss currency, three numbers per sleeve
- **Components:** A1-137, A3-001, A1-161, A1-160, A5-096, A1-158.
- **Need:** the multi-instrument lens (M26) and "sizing has to work in pips, points and ticks" (A17) without seven sizing systems.
- **What it does:** every size, cap, brake and budget at every level is stated in account-currency loss units. Each sleeve (a unit, a cluster, a style) carries three numbers on that scale: routine risk (volatility or expected shortfall at its holding horizon), stress loss (under shared shocks with correlations up and gaps in), feasible size (the smallest allowed position with costs and stressed slippage). Pips, points and ticks exist only inside the instrument record, where `value_per_point` converts them. Margin and the regulatory leverage cap are separate clamps; neither is a risk measure.
- **Levels:** trade to account.
- **Per class and style:** FX aggregates by currency leg; indices by regional equity beta with overnight gaps apart; metals split gold from industrial; energy adds expiry and limit moves to stress loss; crypto adds liquidation and funding kept apart; futures normalise the underlying; stocks add issuer and event stress. Feasible size binds scalpers on a small account; stress loss binds swing and anything held over a close.
- **Ledger:** routine_risk_usd, stress_loss_usd, feasible_size_usd (new); risk_amount_usd, value_per_point, gap_loss_beyond_stop, margin_used, leverage, numeraire.
- **Performance:** nothing is lost to a wrong unit (the MGC-charged-as-MNQ error, A2-206, is blocked by construction); budgets compare across classes so the BMS can move risk to where it pays.
- **Survival:** margin and leverage are clamps, so no accelerator can size past them; stress loss is what the buffer above the floor is sized from.
- **Evidence chain:** assistant synthesis (chats 23, 29) built on industry practice; the three-number record is a design, not a tested rule. Weakest link: routine risk from a short record is noisy, and covariance-based stress understates crisis co-movement.
- **Maturity:** solid.

#### X0-02. Day risk budget split by effective bets, not 1/N
- **Components:** A1-088, A1-087, A1-105, A3-163, A5-001, A1-086, A5-147.
- **Need:** his C29 ("take the total capital to spend in a day and split it across the units") and M11's "flaw" in ten units at full size.
- **What it does:** the BMS fixes the book's day risk budget (its daily swing). Each unit's share is budget x 1/sqrt(N(1+(N-1)rho)), with N the live units and rho their result correlation; when rho is unknown it falls back to 1/N. Ten independent units each get about 0.32 of the budget, not 0.10, for the same total swing **[arithmetic, R2 4.3]**. The Kelly-independent answer ("each unit gets what it would get alone") becomes an accelerator behind proof, not the baseline. The effective-bet count is measured two ways and the smaller wins: from result correlation (slow) and from exposure overlap (fast, X0-11).
- **Levels:** portfolio, unit.
- **Per class and style:** scalpers at different hours on one pair are near-independent in their noise, so rho is low and shares are high; ORB units across opens share a risk-off day, so rho rises on those days (X0-25); swing units across classes share factors, so rho comes from the factor map (X0-41). Crypto on a weekend is the whole book, so N drops and the share rises, which X0-40 then scales back.
- **Ledger:** unit_day_risk_share (new); portfolio_daily_risk_budget, live_unit_count, unit_result_correlation, effective_independent_bets, capital_sharing_rule, unit_capital_share.
- **Performance:** about three times the per-unit size of a plain split with independent units; growth from breadth is kept instead of thrown away by 1/N.
- **Survival:** the book's swing is fixed by construction; at half the believed edge the shares shrink only through rho and N, so the floor odds stay what the budget says. Losing-together days are where this rule is wrong, which is why the hours clause (X0-10) sits next to it.
- **Evidence chain:** Grinold's fundamental law and Meucci's effective bets (theory), R2's arithmetic, the lead's sims (`grounding/sims/frequency_flaw_and_brakes.py`). Weakest link: rho is estimated from few trades per unit; a wrong rho at 0.3 instead of 0 doubles the swing.
- **Maturity:** solid.

#### X0-03. Style sleeves as risk-budget shares, not dollar pots
- **Components:** A1-089, A1-090, A1-107, A5-027, A1-099, A1-102, A4-174, A1-121.
- **Need:** his $300 scalpers / $200 intraday proposal (C4), the BMS as pod manager (C5), and self-optimising slots (C26).
- **What it does:** a style gets a share of the day risk budget and of the stress-loss cap, not a pot of dollars. The BMS re-slots between styles slowly, capped per period and charged for turnover, on evidence (a style at its cap for weeks gains; one idle for weeks loses, X0-52). The two-level cluster map (exposure clusters and behaviour clusters) decides what counts as "a style" for risk: many FX and index scalpers are one bet on microstructure, so they share one behaviour cluster whatever their names.
- **Levels:** portfolio, book.
- **Per class and style:** a scalper sleeve is bounded by feasible size and cost; an intraday sleeve by stress loss over the close; a swing sleeve by factor caps. Energy and crypto start with the smallest shares because their stress loss per unit of routine risk is highest.
- **Ledger:** style_capital_split, slot_rebalance_rule, cluster_exposure_cap, portfolio_daily_risk_budget, cost_of_conservatism (new).
- **Performance:** capital follows the sleeve that is using its budget well, which is what "performance with intention" means at the BMS.
- **Survival:** the parent limit is below the sum of the sleeves (X0-10); a re-slot is capped per period, so one good month cannot move the whole book.
- **Evidence chain:** pod-shop practice (press, no numbers), Simple Portfolios (2005-2025 backtest, long-only, monthly), Cover's universal portfolios (theory). Weakest link: no source tests re-slotting between intraday sleeves; the cadence is a guess.
- **Maturity:** plausible.

#### X0-04. Edge as a gate, breadth as the amount
- **Components:** A1-031, A1-032, A1-095, A1-092, A5-025, A1-019, A1-028, A1-027.
- **Need:** A24 ("let's give a range for the edge... I don't want to be very dependent on the edge") against the lead's "twice the edge gets twice the size".
- **What it does:** the edge is a range with a lower bound. The range decides in or out (and which cells, X0-14). The amount comes from the risk budget and the effective-bet share (X0-02), with inverse volatility as the default allocator (Bayes-optimal when estimates are noisy, A1-095). A capped, shrunk Kelly sits on top only as a ceiling and a ranking: shrink by t-squared over one plus t-squared (A1-019) and toward the family prior (A1-028), then James-Stein the winner for the search (A1-027). Size never doubles because a point estimate doubled.
- **Levels:** unit, methodology, portfolio.
- **Per class and style:** scalpers reach a t-stat fast but on possibly generated ticks (R5 24562), so their range stays wide until live fills exist; swing units have few trades, so the family prior carries most of the weight; crypto and energy ranges are widest because their tails are.
- **Ledger:** edge_range, edge_t_statistic, kelly_shrink_factor, kelly_cap, ranking_score, expectancy_floor_r.
- **Performance:** a weak real edge trades at its breadth share from day one instead of waiting 1,100 trades for a lower-bound Kelly to let it in (R2 4.4). Growth comes from breadth, as he wants.
- **Survival:** a gate on a lower bound means a unit with no edge is out, so breadth never multiplies a negative net edge (R2 4.2 warns exactly this).
- **Evidence chain:** DeMiguel et al. on 1/N (strong, out of sample), Chopra-Ziemba on mean errors (strong), shrinkage (simulation). Weakest link: the gate's bound for a thin record is undefined, so a new unit waits, which is A14's "too safe" in another form.
- **Maturity:** solid.

#### X0-05. One cushion ledger per level with a declared anchor
- **Components:** A5-118, A5-010, A1-036, A1-042, A1-037, A2-132, A5-116, A5-117.
- **Need:** keep house money and reverse house money (A21), the floor almost never touched (C10), and "every change in size has a stated reason" (A13).
- **What it does:** at each level (unit, book, BMS) one ledger: realised P&L since an anchor, a loss limit L, and size x (L+P)/L. With a fixed anchor (day start, seed, a dollar floor) gains widen the cushion and the rule presses: house money. Losses narrow it and the rule cuts: reverse house money. With a trailing anchor (running peak) it is a pure brake. The anchor is declared per level: a unit's working anchor may restart after a cut; the account floor never restarts (A5-010). A fast-invalidation cut costs its size on the ledger; a breakeven costs nothing (answers A28). The multiplier is bounded: extra risk on open trades never exceeds a share of profit above the anchor.
- **Levels:** unit, book, portfolio.
- **Per class and style:** a scalper's ledger resets daily (many trials); an intraday ORB sleeve's resets per session family; a swing unit's anchor trails (few trades, long holds, so pressing on a day's profit is noise). Crypto needs a declared day (X0-27). Gap classes (indices, energy, FX over the weekend) count the gap into L so the press never exceeds what a gap could take back.
- **Ledger:** house_money_winnings_share, house_money_scope, drawdown_pressure_multiplier, cushion_share_per_trade, floor_touch_size_bound, rising_floor_fraction, day_start_equity, brake_equity_basis.
- **Performance:** R9's script: equal growth per risk on independent trades, +37-42 percent under regimes; the old 1.5x at +0.5 percent is what a 1 percent day limit implies.
- **Survival:** the scope cannot finish the period below its anchor because of the extra size; the account floor is a clamp under all of it.
- **Evidence chain:** Grossman-Zhou and Hsieh's lemma (theory, read), R9 script (arithmetic, 400 paths), GitBook ladder (old QMX, same shape, never live). Weakest link: no study measures whether house money pays for professionals, only that they do it.
- **Maturity:** solid.

#### X0-06. Macro as a slow governor, a fast layer decides what is usable now
- **Components:** A3-041, A3-042, A3-043, A3-045, A2-045, A3-094, A4-002, A3-052.
- **Need:** C27's portfolio circuit breaker that "senses this type of move", and the multi-instrument lens on macro.
- **What it does:** two layers. Slow: a few named states per class (calm, growth risk-off, inflation or rate shock, volatility or liquidity shock) as filtered probabilities, recomputed daily and at releases; they set a per-class budget multiplier. Fast: realised volatility, co-movement, spread state, every 5-15 minutes and before each order; it decides how much of the class cap is usable now. Limits fall fast and rise slowly with hysteresis. Uncertain means intermediate; stale means the conservative state; unknown is not calm. The multiplier starts in shadow mode (an applier mode, A4-002) and goes live as cut-only until a walk-forward shows that raises pay. Macro never picks a trade.
- **Levels:** portfolio, account.
- **Per class and style:** energy carries contract fundamentals beside macro; FX needs pair-relative macro (both legs); crypto has too little macro history and takes the overlay, with its own realised risk driving its limits; stocks add earnings and sector. Scalpers feel it only through the class cap; swing units feel it through the factor caps too (X0-41).
- **Ledger:** regime_probability_vector, macro_state_multiplier, class_risk_cap (new); cross_market_stress_reading, board_stale_after.
- **Performance:** volatility management is the one case where de-risking can raise Sharpe (Moreira-Muir, risk assets only); CAST's uncertainty penalty improved both Sharpe and drawdown in its backtest.
- **Survival:** the shock state cuts every class to 0.25 of its cap in the assistant's table; cut-only live means no macro call can raise risk into a jump.
- **Evidence chain:** Hamilton (strong, old), Moreira-Muir (strong for risk assets, contested in real time by Cederburg), the multiplier table (assistant's idea). Weakest link: the table's numbers are untested; a model fitted to one rate era misclassifies the next.
- **Maturity:** plausible.

#### X0-07. Isolation by underlying process with two tells and selective protection
- **Components:** A3-029, A3-106, A3-093, A3-109, A3-107, A3-095, A3-098, A2-128, A3-178, A3-108, A3-115.
- **Need:** his market isolation protocol (C27): "it can isolate crypto... everything is off for crypto", on evidence, sectored by instrument, region and correlated pairs.
- **What it does:** scope keys are class, region, currency and underlying group; an ETF or CFD on gold sits with gold, not with equities (A3-029). Two tells from different families must agree before an isolation (for example liquidity commonality plus a velocity tell, or SQS blocking K of N instruments plus a co-move score); baselines know the calendar; every isolation is recorded with its precision. The smallest implicated scope trips first (an instrument, then its bucket, then the class, then the BMS), with the outer level as a time-graded backup (power-grid selectivity). The mode ladder is no new entries, reduce, flatten. The lifecycle is evidence, time to live, staged resume at half size, retrip back-off. The MIS publishes the isolation; placement fails closed inside it.
- **Levels:** unit, cluster, portfolio.
- **Per class and style:** FX isolates by currency leg and region (Asia chaos while Europe sleeps, A3-200); indices by regional beta; crypto by venue and by BTC/ETH group; energy by contract; stocks by name then sector. Scalpers are the first to be cut (they need the liquidity that leaves first); swing units get reduce rather than flatten unless the tell is severe.
- **Ledger:** market_isolation_trigger, isolation_scope, isolation_end_rule, sqs_hard_block_threshold, cross_market_stress_reading, brake_state.
- **Performance:** selective protection keeps the rest of the book trading when one bucket is bad, which is what pays on a one-class-toxic day (A3-198).
- **Survival:** two-tell agreement and recorded precision are the defences against the false isolation (A3-199); the retrip back-off stops the reopen from being where people get hurt (A3-202).
- **Evidence chain:** exchange breakers (live), grid selectivity (live in its own field), the tells (author backtests), the protocol (his idea). Weakest link: class isolation is untested anywhere in trading; nobody has measured what an isolation costs in missed trades.
- **Maturity:** plausible.

#### X0-08. Three signals kept apart, each with its own speed and clear rule
- **Components:** A3-123, A5-028, A2-079, A5-139, A2-004.
- **Need:** C7 ("we need to be able to know what is breaking") and A25 (drift sizes down slowly; a bad day is not a broken edge).
- **What it does:** three signals, never merged into one score. Strategy decay reads the unit's own trades through an e-value or CUSUM, acts slowly (investigate, then reduce, then suspend), and is the only signal allowed to say "the edge is gone". Bucket stress reads market tells (X0-43), acts fast on scope (isolate), and never says anything about the edge. Account drawdown reads money against the floor, acts at once on size and permission, and is the only one that may flatten. Each has its own window, trip and clear rule. A burn-rate alert pages on a fast burn and tickets on a slow one (SRE). The nearest limit trips first; the outer ones back it up with a grade delay.
- **Levels:** unit, cluster, portfolio, account.
- **Per class and style:** scalpers give decay evidence fast (many trades) but their money signal must be in R-points with cuts (X0-16); swing units give decay evidence slowly, so their money and drawdown signal carries the load (X0-34); crypto's bucket tells include funding and liquidation flows; energy's include limit moves.
- **Ledger:** drift_state, cusum_limit, brake_state, equity_drawdown_halt, control_rank_table.
- **Performance:** a bad day no longer suspends a healthy unit; only decay evidence can, and slowly. The cost of conservatism (X0-52) is measured per signal.
- **Survival:** the account signal is independent of any model and acts at once; the three cannot cancel each other because they move different levers.
- **Evidence chain:** SRE burn-rate practice (live in its own field), e-detectors (simulation plus proofs), the separation itself (assistant's design, matches his words). Weakest link: no trading test of the three-signal split; alarm precision has to be measured in QMX.
- **Maturity:** solid.

#### X0-09. Staged ramp: pilot budget in tail-loss units, unit and book both qualify, faster down than up
- **Components:** A5-021, A5-039, A5-040, A5-041, A1-054, A5-042, A5-127, A1-053, A2-218.
- **Need:** A22 (demo units at boot), the paper-to-live route, and A14/C13 (not "too safe", "one working unit should not be cut to $20").
- **What it does:** a newly promoted unit starts at a pilot share of its eventual day risk share, stated in tail-loss units, and climbs a six-tier ladder. The climb is TCP slow start: a doubling per clean cohort until the first warning (a graded event in money), then small steps with bigger cohorts (FDA accelerated titration). Each rung is checked for feasibility per instrument (round down, re-estimate impact at the new size, zero if the minimum is too big). The unit and its book must both qualify for a step up; correlated units gain slower. Down is faster than up: a hard breach goes to zero, a soft breach one tier. Proof continues at the smallest live size; a cut tier is a counted try.
- **Levels:** unit, book.
- **Per class and style:** scalpers climb in trades (a cohort is N trades), intraday and swing in active days; crypto's first rung is spot not perps; energy's first rung is the smallest feasible exposure with no step across a roll or an EIA print; stocks' rungs are whole-share feasible.
- **Ledger:** size_ramp_to_full, size_levels, tier_dwell (new), paper_to_live_carry_rule, verification_trades_needed.
- **Performance:** a fast early climb is cheap at the bottom of the ladder, so a working unit reaches its share in days, not months; the "too safe" cost is paid only until the first warning.
- **Survival:** the first warning switches the climb to small steps; the book-level gate stops ten new correlated units from all climbing at once.
- **Evidence chain:** Topstep tiers (live, no effect measure), FDA titration (live in its own field), TCP (standard), Numerai staking (live). Weakest link: no trading study of a ramp's cost against a flat start; the pilot share's first value is a guess (10-25 percent is the assistant's).
- **Maturity:** plausible.

#### X0-10. Co-loss accounting: the hours clause on every count, the parent limit sized on co-loss
- **Components:** A3-146, A2-026, A3-149, A3-158, A5-091, A3-161, A1-086, A2-027.
- **Need:** C32 ("losing together half the time doesn't make sense once the brakes count"), B15 (exposure at book and BMS), and the count-brake problem (C31).
- **What it does:** every loss from one move inside a declared window counts as one event for every count brake, at every level (insurance's hours clause). The parent limit sits below the sum of its children by how often they lose together: measured co-loss breadth (the share of live units losing in the same window and the loss given that) sets the gap. Concentration limits sit per common dependency (broker, feed, host, signal source), not only per instrument.
- **Levels:** book, portfolio, account.
- **Per class and style:** ORB units across opens share a risk-off day (one event, not five strikes); FX pairs share a USD release (one event); crypto and indices share a weekend-to-Monday move (one event); swing units across classes share a factor shock. Scalpers at different hours on one pair rarely share a window.
- **Ledger:** co_loss_breadth (new); loss_event_window, bms_daily_loss_limit, portfolio_daily_risk_budget, effective_independent_bets, cluster_exposure_cap.
- **Performance:** a book of many units is not punished five times for one move, so it keeps trading after a shared loss that was inside its budget.
- **Survival:** the parent limit is the real defence against losing together; it is sized from measured co-loss, not from a bet count.
- **Evidence chain:** insurance practice (live in its own field), bank limit hierarchy (live in its own field), co-loss breadth (idea). Weakest link: the window width (minutes? a session?) has no derivation; too wide and everything is one event.
- **Maturity:** plausible.

#### X0-11. The exposure ledger: exposure, drawdown, realised and unrealised at book and BMS
- **Components:** A1-114, A3-050, A3-162, A1-108, A4-152, A3-120, A3-148, A3-046.
- **Need:** B15, his correction that the Book and BMS measured exposure, drawdowns, unrealised and realised profit, and that these may have been missed.
- **What it does:** one RiskState row every pass, per level: equity series and base, drawdown from the declared anchor, open risk at the stop (portfolio heat), realised and unrealised P&L, exposure summed in standard zones. FX exposure is summed by currency leg; everything else through a factor covariance with shrinkage and an adaptive window (DCC or exponentially weighted; cold start stays inert). A "share of book risk from factor 1" readout tells when the book is one bet. These rows are what the brakes and the allocator read; nothing else computes them.
- **Levels:** book, portfolio, account.
- **Per class and style:** FX legs; indices by regional beta; metals gold vs industrial; energy by contract and product; crypto by venue and BTC/ETH beta with funding apart; futures by underlying; stocks by sector. Scalpers add little to exposure but much to heat; swing units add exposure.
- **Ledger:** portfolio_exposure, open_risk_at_stop, unrealized_pnl, realized_pnl, high_water_mark_equity, currency_exposure_limit, per_instrument_exposure_cap, brake_state.
- **Performance:** the allocator can see where risk is idle and where it is crowded, which is what a re-slot needs.
- **Survival:** heat and factor-1 share catch the book that has become one bet before a brake fires on P&L.
- **Evidence chain:** RiskMetrics and SIMM (industry practice), MQL5 24392 currency legs (author checks), 23440 factor share (mechanism). Weakest link: the GitBook exposure desk never had fields or a formula; this is the first time the rows are named.
- **Maturity:** solid.

#### X0-12. Venue capacity probe on every accelerator (wild)
- **Components:** A5-148, A5-135, A1-144, A3-015, A3-238.
- **Need:** accelerators that grow size until the counterparty says no (the Kaunitz case: +8.5 percent, then stakes cut to $1.25).
- **What it does:** every accelerator carries a per-venue, per-instrument capacity cap found by probe-and-drain: briefly size above the current level, keep the gain only if rejects, requotes, fill latency and markout do not worsen, then drain back. Counterparty pushback (dealer skew after repeated same-side fills, last-look rejections) is read as the ceiling arriving. The cap is a clamp under the record's max lot.
- **Levels:** unit, account.
- **Per class and style:** retail FX and CFD brokers with last look are the closest analogue; exchange futures and crypto books show capacity as impact instead, where the square-root law is only a sanity check. High-win-rate scalpers hit it first.
- **Ledger:** venue_capacity_cap (new); max_position_size_lots, max_lot, slippage_cost.
- **Performance:** size can grow to the true ceiling instead of a guessed one.
- **Survival:** the probe is bounded and drains; the cap arrives suddenly in the real case, so the probe watches rejections, not only P&L.
- **Evidence chain:** one real-money betting experiment (read), BBR (production networking), dealer skew (simulation). Weakest link: no trading test of probing a broker's tolerance; it may also get an account flagged.
- **Maturity:** wild.

### 2.2 Scalping (1-5 minutes and tick, where costs dominate)

What the template must hold for this style, and why: the risk unit is R **after costs** with the cut inside it, because at a 5-pip stop a 0.8-pip round trip is 16 percent of R before anything happens; the stop is a fast-invalidation cut with a wide disaster stop behind it, because a full stop is the expensive exit; brakes read money and R-points at the unit's own trade rate, because any fixed count fires on healthy days once trades pile up; costs reach the sizer as an hourly table per instrument and bind size through a denominator and an admission gate; the only accelerators with evidence are cushion-funded (house money on the day ledger) and cost-windowed; pressing after wins is worth about nothing on independent trades.

#### X0-13. The scalper's risk unit: R after costs, cut inside, two ledgers
- **Components:** A1-139, A3-006, A3-014, A1-142, A2-252, A5-145, A2-091, A2-270.
- **Need:** A9 and A28 (every number must include fast-invalidation cuts), A11 (costs feed Kelly), B9 (R fixed at entry not accepted).
- **What it does:** 1R is the planned full loss at the disaster stop in account currency, fixed at entry (the logic record needs a fixed unit). The expected loss per losing trade is not 1R: it is the cut size c (about 0.35R in the October proposal) on cut trades and 1R on the rest, and the round-trip cost C in R is charged on every trade. Break-even win rate is p* = (L+C)/(W+L) with L the realised mean loss, not the stop. Two ledgers: the money ledger (brakes read it; a cut costs its size, a scratch costs C) and the R ledger (the logic record; a cut is a -c result, so the edge is measured honestly). Costs are per class: spread and swap bind FX and CFDs; taker fees bind crypto; the per-contract commission binds micro futures.
- **Levels:** trade, unit.
- **Per class and style:** FX: 0.8 pips round trip on EURUSD against a 5-pip stop is 0.16R; at a 3-pip stop it is 0.27R, so timeframe moves cost in R faster than price does. Crypto: 10-20 bp taker round trip against a 1.3 bp gross 15-minute reversal is the whole edge (A3-014). Micro futures: 2 MNQ points fixed. Metals: micro gold 0.01 lot with a $3 stop is already 1 percent of $300. Energy: generally not scalpable at small size. Stocks: per-share fees and borrow.
- **Ledger:** round_trip_cost_r, fast_invalidation_cut_r, fast_invalidation_trigger, breakeven_win_rate, mean_loss_r, loss_points_total, original_risk_r, hourly_cost_profile (new).
- **Performance:** a 78 percent scalper at W 0.5R, L 1R, c 0.08R has EV about 0.09R; the same unit with cuts at 0.35R on half its losers has mean loss 0.675R and EV about 0.25R **[arithmetic]**. The cut is where a weak scalper's edge lives.
- **Survival:** the disaster stop bounds the worst case at 1R plus gap; the money ledger sees the real drawdown including cuts.
- **Evidence chain:** arithmetic; the October FI proposal (never in code); no paper on fractional early cuts after costs (R8). Weakest link: the cut size has no evidence outside the unit's own trades, and trade rows today cannot tell a cut from a time exit (G11).
- **Maturity:** solid for the two ledgers; plausible for the cut size.

#### X0-14. Admission gate: the edge's lower bound against stressed cost, in the instrument's own units
- **Components:** A3-003, A2-223, A1-138, A3-004, A2-206, A3-005, A3-240, A1-140.
- **Need:** cost is the master state for scalpers (R5 B); G7's finding that no cost reaches the sizer; D17 (cheap-looking markets may be off-limits).
- **What it does:** a scalper may trade a cell (instrument, hour, session) only when the lower confidence bound of its gross edge per trade is at least twice the stressed round-trip cost for that cell; three times for negative-skew logics or thin live evidence. Gross edge is measured decision-time mid to planned-exit mid on all signals, not only fills; cost from fills against contemporaneous mids plus fees, funding, rejects and requotes. The friction floor is in the instrument's own units (the MGC-as-MNQ error charged gold 4x). Recomputed live in rolling, session-aware windows. Before promotion, the five-gate falsification (net t at least 2, 30 trades per fold, positive net, same sign every year, permutation p under 0.05, plus a +1 bar delay re-run) and a re-rank under two execution assumptions.
- **Levels:** unit, methodology.
- **Per class and style:** FX: the gate closes at rollover and the Sunday open and in the 21:00-22:00 GMT spread peak; crypto: the gate is per venue and fee tier; micro futures: 11 of 14 retail 5-minute families on MNQ failed the friction floor; metals: gold's 8-hour half-life fails a 5-minute mean-reversion gate; energy: the EIA hour fails; stocks: fragmented quotes make the mid itself uncertain.
- **Ledger:** edge_to_cost_ratio_min (new); expectancy_r, round_trip_cost_r, cost_stress_multiple, edge_t_statistic, min_trades_for_verdict, unit_cost_target.
- **Performance:** every cell a scalper trades has room for costs to double; the hours it does not trade are the hours it would have lost.
- **Survival:** breadth never multiplies a negative net edge; a broker change re-opens the gate.
- **Evidence chain:** the MNQ falsification study (author walk-forward, strong null), the BTC cost hurdle (author backtest), the 2x figure (assistant's proposal). Weakest link: 2x and 3x are stated, not derived; a thin record leaves the bound undefined and the unit waits (collides with A14).
- **Maturity:** solid for the gate; plausible for the multiples.

#### X0-15. The scalper's stop: FI cut as the working exit, a wide disaster stop as the clamp, safest exit wins
- **Components:** A2-252, A2-257, A2-258, A2-085, A5-087, A2-139, A2-233, A5-086, A2-260.
- **Need:** A10 (stop vs fast invalidation needs its own thought), M15 (FI replaced dynamic SL/TP for scalpers), A28.
- **What it does:** the working exit is a fast-invalidation cut: a named condition (the setup's own invalidation, a time stop at the edge-versus-time curve's zero, or a half-life for mean reversion) that closes at about -c R. A wide disaster stop sits at the venue under it for connectivity and gaps. Of the safety exit and the strategy exit, the safest wins. The one-shot rule keeps the breaker's count clean: no stop widening, ever. Every trade row records the exit mechanism and outcome, so the cut can be told from a time exit. Before any cut rule ships, it must beat "no early cut" and "cut one bar later" in a two-arm test with entries held fixed, per instrument.
- **Levels:** trade, unit.
- **Per class and style:** FX and metals on a dealer feed: the disaster stop fills at the stressed spread, so it is placed wider than the cut by at least the p95 spread; crypto perps: the disaster stop must sit inside the liquidation price (refused otherwise, A2-262); micro futures: the cut is in ticks and the commission is paid twice on a cut-and-re-enter, so re-entry cooling applies (A2-117); stocks: a halt makes the cut impossible, so the disaster stop is the only exit and sizing carries a halt allowance (A2-264).
- **Ledger:** fast_invalidation_cut_r, fast_invalidation_trigger, disaster_stop_distance, stop_widening_allowed, exit_reason_code, max_hold_time, stop_policy_per_style.
- **Performance:** the edge-versus-time curve per unit shows where holding stops paying (MNQ survivors held 60-75 minutes); a time stop there is free edge.
- **Survival:** the disaster stop is a clamp the cut cannot remove; exits are never blocked by any brake (A2-101).
- **Evidence chain:** two-arm exit tests (author out-of-sample, four instruments), the edge-versus-time curve (author backtest), the FI proposal (never in code). Weakest link: no study tests fractional early cuts after costs; the cut size must come from the unit's own paths.
- **Maturity:** plausible.

#### X0-16. Scalper brakes that scale with frequency: the money quantile, loss points, a random control
- **Components:** A5-144, A2-078, A2-091, A5-145, A2-116, A2-135, A2-083, A2-126, A2-030.
- **Need:** C31/C33 (how frequency affects the brakes; a sweet spot per level, no single standard), A26 (the circuit breaker is the baseline, improve it), A6 (brake at about three).
- **What it does:** the circuit breaker keeps its name and its job (a trip that benches the unit and whose fire density is decay evidence) but changes what it reads. For a unit at r trades a day and win rate p, a fixed count fires on healthy days by chance: "2 full stops" on 61 percent of days at 4 trades, "3 in a row" on 41 percent at 10. So the trip reads the money ledger: today's loss in R-points (a full stop 1, a cut its size, a scratch its cost) against the unit's own k-th percentile day at its rate (R9: a 1 percent worst day fires 1-3 percent of days at any rate). A rolling-window count with a minimum bench rest across the day boundary survives only for low-frequency units. Every brake ships shadow-first and must beat a random brake that fires as often (the 23482 design); its precision is recorded, and a noisy brake is a defect.
- **Levels:** unit; the same shape at book and BMS with their own quantiles.
- **Per class and style:** a 1-minute FX scalper at 40 trades a day gets a -10R day as its 1st percentile; a 5-minute index scalper at 8 trades gets about -5R; a crypto scalper's "day" is the declared 24/7 day (X0-27); an ORB unit at 1-3 trades a day keeps a count brake, scaled to its own streak distribution (X0-25).
- **Ledger:** money_brake_percentile (new); loss_points_total, loss_points_bench_threshold, circuit_breaker_strikes, circuit_breaker_window, loss_counting_rule, brake_precision, breaker_fire_density, unit_daily_loss_limit.
- **Performance:** a healthy scalper is no longer benched on most of its days; the lead's sims show a count brake at scalper rates is a tax on frequency, which is the system's edge.
- **Survival:** the quantile is in money, so a bad day is caught whatever the count; the breaker's fire density still feeds decay detection (WF3).
- **Evidence chain:** R9 arithmetic (400 paths), the lead's sims, one controlled brake test (23482, few trades). Weakest link: the quantile before a record exists comes from the card by simulation, and no money brake has been simulated on QMX's own trade streams yet (STATE 10).
- **Maturity:** solid.

#### X0-17. Scalper size bound: Q at most R over (D x V + C + S), round down, skip below a step
- **Components:** A3-007, A1-142, A3-002, A1-157, A5-042, A1-153, A1-004, A1-154.
- **Need:** sizing in pips, points and ticks across classes (A17); D17; the silent-oversize trap (A1-154: a minimum-lot clamp that raises size).
- **What it does:** quantity is at most the risk share over (stop distance x value per unit plus round-trip cost plus stressed stop slippage per unit). Round down to the lot step; below one step, no trade and a reported reason; never round up to reach a budget; recompute book risk after rounding and accept unused risk; a no-trade band stops rounding churn. Currency conversion comes from the record, never from a pip table.
- **Levels:** trade, unit, account.
- **Per class and style:** FX micro lots fit a small share; micro index futures and crude often round to zero on $500 (R3's worked number: the same volatility target gives a tradable EURUSD micro lot and zero Micro E-mini); crypto spot and fractional shares fit; energy and full-size futures rarely do; gold 0.01 lot is coarse.
- **Ledger:** feasible_size_usd (new); min_lot, lot_step, max_lot, lot_size, rounding_residue_r, value_per_point, slippage_cost.
- **Performance:** the denominator charges the real cost of the trade, so a cell that cannot pay is skipped before it costs anything.
- **Survival:** rounding never adds risk; the silent oversize that the April system allowed is refused.
- **Evidence chain:** arithmetic and the unit build's own `lots` conversion (built). Weakest link: stressed slippage S has no measured value until fills exist.
- **Maturity:** solid.

#### X0-18. Execution-fit gate and markout: the scalper's microstructure brake
- **Components:** A2-062, A3-073, A3-011, A3-070, A3-071, A3-075, A3-074, A3-082, A3-079, A2-111.
- **Need:** his doubt that microstructure belongs in sizing (D6), resolved as a permission gate first and a cost input second, never a reason to add size.
- **What it does:** five execution-noise gates must pass before any scalper entry: spread expansion against the instrument's own two-window histogram, tick velocity, quote gaps, micro-volatility, slippage stability ("the EA does not predict direction; it predicts whether the market can fill an order"). The SQS stays as the spread gate with hysteresis. Post-fill markout at 1, 5 and 60 seconds is recorded per instrument, venue, session and regime; an execution-quality anomaly brake trips on fills, not on P&L. Noisy filters (order-flow toxicity, VPIN) run as shadow labels and report blocked-versus-permitted counts and net P&L before any live veto. Thresholds are refit per instrument and broker; the tester's gates must equal the live ones (22772's trap).
- **Levels:** trade, unit, node.
- **Per class and style:** FX and CFDs: markout measures dealer skew and last look, not queue toxicity; futures, crypto and stocks on central books: queue mechanics apply and back-of-queue maker fills almost always lose (A3-011); crypto adds funding minutes; indices add the cash open's first minutes.
- **Ledger:** sqs_score, sqs_hard_block_threshold, sqs_hysteresis_band, spread_cost_guard, slippage_cost, cost_drift_multiple, microstructure_multiplier.
- **Performance:** avoided fills are avoided losses at the tightest stops; the markout record is what turns a cost table from a guess into a measurement.
- **Survival:** a hard block on untradeable conditions (spread or minimum size makes the budget impossible) is cheap; the shadow-first rule stops a noisy filter from starving a unit.
- **Evidence chain:** the five gates (author backtest, 2 months), markout (live, one venue one week), SQS (built, off the path). Weakest link: no evidence a retail gate improves net returns; only that it avoids bad fills.
- **Maturity:** plausible.

#### X0-19. Scalper accelerators that can pay: cushion-funded, cost-windowed, dose-stepped; never pyramiding
- **Components:** A1-067, A5-118, A1-070, A3-033, A1-052, A5-122, A5-119, A1-069, A5-127.
- **Need:** keep house money (A21) and the accelerator idea, with "brakes first" (C19) and the sitting-duck warning (M33).
- **What it does:** three kinds have a mechanism for a scalper. (1) The day-ledger cushion (X0-05): extra risk funded only from today's realised profit above the day start, bounded by a share of that profit. (2) The window lift: a measured slice where the unit's net edge in R is higher out of sample gets a larger share of the day budget, because cost is lower there, not because edge is handed out. (3) Dose-escalation levels (BOIN, 3+3): a new or returning scalper climbs size levels on cohorts of trades, with the first warning switching to small steps. Half size until a profit cushion equal to the loss allowance exists (the prop rule) is the same shape at the bottom. Pressing after wins (anti-martingale) adds about k x rho R per trade, which is nothing when trades are independent, so it is off by default and on only after a block-persistence test passes. Pyramiding is never for scalpers.
- **Levels:** unit.
- **Per class and style:** FX: the London hours are the cheap window; gold: around the fixes is a caution, not a lift (X0-30); indices: after the auction settles; crypto: the Europe-US overlap by venue; micro futures: the window must clear the fixed commission; stocks: the first minutes after the open are in-play, not cheap.
- **Ledger:** house_money_winnings_share, house_money_scope, premium_window_flag, session_multiplier, size_levels, tier_dwell (new), hourly_cost_profile (new).
- **Performance:** R9's pair script: +37-42 percent growth per risk under regimes for the cushion rule; the window lift is a pure cost effect and so is free when the slice is real.
- **Survival:** every accelerator is funded from profit or proof, never from a point edge; any active brake outranks all of them (A5-138).
- **Evidence chain:** Grossman-Zhou (theory), Topstep and Apex rules (live, no effect measure), the window studies (cost and activity only, no window-sizing test), BOIN (simulation). Weakest link: no study of win persistence in intraday retail strategies after costs.
- **Maturity:** plausible.

#### X0-20. Negative-skew scalpers sized on tail loss, not variance
- **Components:** A3-008, A1-169, A1-024, A3-028, A2-012.
- **Need:** A20 (his scalper profile: low reward-to-risk, high win rate) read as what it is: negative skew.
- **What it does:** many small wins and rare large losses means the tail, not the variance, decides survival. Such units are sized on expected shortfall and the per-class worst one-step move table (gaps, stop slippage, correlated positions), with a 1.3x divisor until the unit's own tail record exists (Landolfi's mean-reversion worst cases at 1.30-1.34x Gaussian). A calibrated tail bound (conformal VaR) sits apart from the edge: a VaR breach cuts exposure without claiming the alpha is gone.
- **Levels:** unit, methodology.
- **Per class and style:** crypto and index CFDs have the fattest tails; FX mean-reversion scalpers carry the flash-crash and fix tail; metals carry the fix volume spike; stocks carry the halt.
- **Ledger:** tail_loss_sizing_factor (new); mean_loss_r, payoff_ratio, win_rate, excursion_mae_mfe_r, gap_loss_beyond_stop.
- **Performance:** a smaller size on a negative-skew unit is the size that lets it keep trading through its own tail; the cost is paid in growth on calm days.
- **Survival:** the worst one-step move is in the denominator, so one flash crash is inside the budget.
- **Evidence chain:** Landolfi (simulation), conformal VaR (author backtest, CRSP), robust Kelly (theory). Weakest link: a short record has no tail in it, so the 1.3x is stated, not measured.
- **Maturity:** plausible.

#### X0-21. Tick rate as the volume proxy; activity sessions; recalibrate on broker change
- **Components:** A3-074, A3-021, A3-040, A1-151, A3-083, A3-077.
- **Need:** RVOL is blocked until bars carry volume and time (D5), and FX and CFD feeds carry no real volume at all.
- **What it does:** on broker feeds the activity gauge is quote updates per minute against the usual at the same minute of the session (quietest half hour waits 47x the busiest on EURUSD). It stands in for relative volume in the in-play gate and in window finding, and is never called volume. For 24/7 instruments, sessions are cut from the activity profile (X0-54). The gauge, the spread histogram and the cost table are all recalibrated on any broker change and monthly; a broker reality check runs before a unit deploys on a symbol.
- **Levels:** unit, system.
- **Per class and style:** spot FX and CFDs: tick rate only; futures and stocks: real volume and depth, so RVOL proper; crypto: real tape per venue; metals: broker spot vs exchange futures differ.
- **Ledger:** tick_rate_relative, activity_session_windows (new); rvol_multiplier, premium_window_flag, sqs_baseline_conditioning.
- **Performance:** a scalper is placed where the market is active now, which is where its cost is lowest and its fills best.
- **Survival:** a quiet feed is read as "unknown, not calm" (A3-094) and blocks new risk.
- **Evidence chain:** the ACD duration model (author out-of-sample, six symbols), the in-play study (cited paper, not retested). Weakest link: tick rate is broker-specific; a signal built on it died on another broker's quotes (R5 15330).
- **Maturity:** plausible.

#### X0-22. Sub-minute maker scalper with a market-maker's-dilemma brake (wild)
- **Components:** A3-011, A3-012, A3-066, UB-07 (idea bank).
- **Need:** the template must accept a unit the operator may build later from the idea bank without rework, even one that needs co-location.
- **What it does:** a passive-entry scalper on a central book whose risk template includes: a markout brake (fills drifting against the maker trip it), no orders in the first seconds of bar boundaries, jittered order times, and a capacity cap from impact over depth. Default off. The template holds the slots; the unit is not recommended at retail latency (naive market making ran at Sharpe -109 annualised in the Binance study).
- **Levels:** trade, unit.
- **Per class and style:** crypto per venue, index and energy futures, liquid stocks; never FX or CFDs (no book).
- **Ledger:** slippage_cost, cost_drift_multiple, venue_capacity_cap (new).
- **Performance:** nil at retail speed; kept so the frame does not forbid a style.
- **Survival:** the markout brake is the whole survival story.
- **Evidence chain:** one venue, one week, minimum size. Weakest link: everything.
- **Maturity:** wild.

### 2.3 Intraday (session opens, opening ranges, mean reversion inside the day)

What the template must hold for this style, and why: the risk unit is a fixed money budget over (stop plus a cost reserve) with the time-of-day volatility forecast cutting size, because intraday volatility has a shape and the open is not the overlap; the stop is a per-logic choice made by a test (trailing or breakeven where the unit's returns show momentum, a time exit where they mean-revert), because the stop-loss literature says a stop helps only under momentum; brakes are daily loss ladders at three levels read as capital breakers, with the hours clause for opens that correlate; costs reach size through the same hourly tables plus flat-by-deadline and gap rules; the accelerators with evidence are tier ladders with a dwell and a persistence press after a block test.

#### X0-23. The intraday risk unit: budget over stop plus cost reserve, cut by the hold's volatility forecast
- **Components:** A3-016, A3-017, A1-012, A3-054, A1-009, A3-023, A1-011.
- **Need:** C15 (growth across 24 hours is not one fixed percentage), the per-class "open" question (R5 C).
- **What it does:** quantity is the fixed money share over (stop per unit plus a cost reserve per unit), then cut when the volatility forecast for the planned hold is elevated. The forecast is seasonal bucket x the day's level x short-term clustering, per instrument, with HAR-RV as the multi-horizon forecaster for longer holds. Sessions are gated on measured volatility, not on clock flags (session volatility columns carried 25.6 percent of importance against 2.5 percent for session flags). The stop is volatility-scaled (ATR) at fixed money risk, capped.
- **Levels:** trade, unit.
- **Per class and style:** FX majors: London-New York overlap 12:00-16:00 UTC, JPY and AUD pairs also Asian hours; US indices: after the opening auction settles, the cash open itself is a caution; metals: the overlap, with US inflation and jobs as cautions; energy: active US hours with an explicit EIA policy; crypto: no clock shape, activity sessions; futures: when the underlying's book is deepest; stocks: regular hours after the auction.
- **Ledger:** hourly_volatility_profile (new); volatility_target, context_size_modifier, session_windows, stop_distance.
- **Performance:** size follows where the move is; a flat percentage across 24 hours wastes budget in dead hours and overspends it at the open.
- **Survival:** an elevated forecast cuts before the move, which is the only direction a forecast can help.
- **Evidence chain:** Andersen-Bollerslev (strong, old), the multiplicative component model (author backtest), the session-volatility importance (one author's out-of-sample). Weakest link: few trades a day make fine buckets noisy; pooling across the class is assumed to help (unbacked).
- **Maturity:** solid.

#### X0-24. The intraday stop: dynamic SL/TP rebuilt as risk-state invalidation, breakeven only when the forecast changes
- **Components:** A2-255, A2-256, A2-234, A2-266, A2-245, A2-269, A2-249, A5-079, A2-235, A2-244.
- **Need:** M15 (the old dynamic SL/TP: stop to breakeven by how far the trade is winning, kept for intraday), A10, A28's "what mechanism are we using".
- **What it does:** the April rule (stop to breakeven once at +1R, take-profit extends while continuation looks likely) is rebuilt as three parts. First, a stopping-premium check per unit: do its own returns persist at its horizon (MAE and MFE paths)? Momentum allows a stop move; mean reversion gets a time exit and no stop move; unknown keeps only the disaster stop. Second, the breakeven move happens only when the trigger changes the forecast, not at a fixed +1R, and is spread-aware (the offset includes the p95 spread). Third, the trail type is chosen by why the position was opened (breakout: ATR trail; mean reversion: half-life time exit; news: fixed). Risk per trade stays fixed while the stop moves; stops only tighten. A2-245's own result (still about 60 percent losers) is the warning that moving stops is not an edge.
- **Levels:** trade, unit.
- **Per class and style:** ORB on indices and stocks (momentum after the open): trail allowed; FX mean reversion in the overlap: time exit at the half-life, no breakeven; gold: the 8-hour half-life means no intraday mean-reversion stop at all; crypto: the trail must respect funding minutes; energy: no stop move across the EIA print.
- **Ledger:** stop_premium_check (new); breakeven_trigger, breakeven_offset, trailing_stop_setting, take_profit_extension_threshold, stop_policy_per_style, stop_widening_allowed.
- **Performance:** a time exit where the edge-versus-time curve crosses zero keeps the part of the move the unit was built for and gives back the rest to cost.
- **Survival:** the disaster stop is unchanged by any of it; a stop never widens.
- **Evidence chain:** Kaminski-Lo (assistant summary, paper not read by R6), the stopping-premium studies (author backtests), breakeven modes (author backtest). Weakest link: no study tests breakeven moves after costs (R8); the April thresholds were never valued and the code is lost.
- **Maturity:** plausible.

#### X0-25. ORB as a family: breadth through opens, sized as one family, in-play gated, streak brake from its own distribution
- **Components:** A3-032, A3-020, A1-135, A3-021, A1-082, A3-212, A2-129, A1-081, A3-146.
- **Need:** D11 (ORB gets frequency through breadth: "brilliant"), D12 (ORB wins less often; find the ORB that wins), his phase-1 seed.
- **What it does:** one ORB logic trades the opening range of every open it is placed on (Tokyo, London, New York for FX and gold; each index cash open; stock opens). The logic is proven as one family pooled across opens while each open earns its own record. The family is sized as one sleeve (the three Concretum ORBs combined had max drawdown about 10 percent against 15 percent alone, monthly correlation about 0.3), with the effective-bet count of opens lower on risk-off days. The in-play gate (relative volume, or tick rate where no volume exists) says whether a market may be traded today. The streak brake is scaled to the family's own streak distribution (a sub-30 percent win rate expects long runs; a fixed "three" would fire constantly), and the hours clause makes a risk-off day one event across opens. The hand-over scenario (ORB out at 16:00 London, scalpers in, the fix in the same minutes) gets a caution window and no day-budget reset.
- **Levels:** unit, methodology, book.
- **Per class and style:** stocks in play: the strongest evidence (net Sharpe 2.81 for the top 20, one period); indices: cash open; FX and gold: London and New York opens; crypto: no open, so no ORB; energy: the pit open and the EIA hour are different windows; futures: the underlying's open.
- **Ledger:** trade_rate, effective_independent_bets, rvol_multiplier, session_windows, decay_watch_loss_streak, co_loss_breadth (new), session_handover_buffer_width.
- **Performance:** frequency from breadth without more trades on one market; the family's drawdown is lower than any one open's.
- **Survival:** the hours clause and the family sizing are the two defences against the day when every open loses together.
- **Evidence chain:** the Concretum papers rebuilt (author backtest, in sample), stocks-in-play (cited, not retested), the streak arithmetic (R9). Weakest link: backtest correlation between opens depends on the period, and the 29 percent to 1,637 percent figure is a cited claim.
- **Maturity:** plausible.

#### X0-26. Intraday mean reversion placed by persistence readings, exited by half-life, tapered by regime age
- **Components:** A2-233, A3-061, A2-173, A3-189, A3-187, A3-190, A1-133, A3-184.
- **Need:** his System 1 (a logic placed where the market suits it) and the MIS as router (D1-D3); A16 (sizing through the unit's measured edge in its context).
- **What it does:** the MIS's built persistence readings (efficiency ratio, variance ratio, Hurst, CUSUM change points) are the placement inputs for a mean-reversion unit: it widens its scope to the markets reading mean-reverting at its timeframe. The time exit is the fitted half-life; a trade that has not reverted by then is closed at whatever it is. New adds are tapered as a regime ages (hidden semi-Markov durations: the chance a regime ends rises with its age). Placement is ranked by n x EV squared over variance per cell, with costs normalised and the edge shrunk first (X0-46). The MIS today only narrows; placement needs a widen door (flagged for the MIS, not designed here).
- **Levels:** unit, system.
- **Per class and style:** crypto: a real 15-minute reversal in 90 percent of 183 pairs but fees bind (A3-029); US stocks: reversal largely absent at 15 minutes; gold: half-life about 8 hours, so an intraday unit, not a scalper; FX: pair-specific, strong shared USD factor; indices: cash session only.
- **Ledger:** max_hold_time, context_size_modifier, ranking_score, board_stale_after, regime_age (not in the ledger; A3-061 proposes it).
- **Performance:** the unit trades only where the physics say its logic fits, which is the whole System 1 bet.
- **Survival:** the half-life exit bounds the hold; the regime-age taper stops adds into a regime that is about to end; a stale board means the unit trades its own rules, not the router's.
- **Evidence chain:** the readings are built (never run on a venue); the duration gate (author backtest, 8 months XAUUSD); the crypto reversal panel (one exchange, 14 months). Weakest link: the router can be wrong and the record must be per unit and market (his own caution).
- **Maturity:** plausible.

#### X0-27. Flat by deadline, cash and overnight apart, the day boundary as a contract
- **Components:** A3-018, A3-024, A3-025, A2-064, A3-022, A3-040, A2-011, A2-263.
- **Need:** "ORB never holds overnight" (D7), the day-boundary hole in count brakes (A3-219), the rollover minute (A3-216), DST shifts (A3-218).
- **What it does:** a unit that must be flat by session end exits at a deadline set minutes before the real close, tested against the venue's auction, halt and holiday rules. Intraday and ORB carry no gap allowance because they are flat by rule; anything allowed to carry is sized with the gap (X0-31). Records and decay evidence split into cash session and overnight. The day boundary and the session clock are contracts: broker time zone, DST rule, market zone, reset hour; counters are confirmed and persisted so they survive restarts and date changes; crypto declares its day because nothing closes.
- **Levels:** trade, unit, system.
- **Per class and style:** stocks and cash indices close daily; futures have maintenance breaks (a mid-session deadline); FX closes for the weekend and has the 17:00 New York minute; crypto never closes; metals follow Comex hours and the fixes.
- **Ledger:** forced_flat_instant, window_forced_flat, max_hold_time, day_boundary, session_windows, state_carry_rule, activity_session_windows (new).
- **Performance:** none directly; it is what makes the daily budgets and the two records honest.
- **Survival:** a position never sits through a close it was not sized for; the two-strikes-at-23:50 exploit is closed.
- **Evidence chain:** MQL5 scenario tests of the mechanism (author demo), exchange rules (live). Weakest link: closing orders can slip or partially fill, and a break mid-session needs its own deadline.
- **Maturity:** solid.

#### X0-28. Intraday daily loss ladders at unit, book and BMS as capital breakers
- **Components:** A2-010, A2-004, A2-094, A2-134, A5-143, A2-075, A2-177, A2-053, A1-109.
- **Need:** C7 (10/5/3 made no sense at $500; 3-5-7 is the standard; several brakes, each saying what is breaking), B13 (the set is circumstantial).
- **What it does:** a daily loss ladder at each level (alert, stop new entries, flatten), measured on equity with open positions against a confirmed day baseline (static or trailing by declared choice), in money, with early warnings at 80 and 90 percent of the limit. The limits are derived, not stated: the unit's from its own daily distribution (the "bad day" quantile, X0-16); the book's from the summed unit limits less co-loss (X0-10); the BMS's from the buffer above the floor (X0-05). They are capital breakers, not a claim that trading after a loss is bad; the stop-loss literature does not show that "stop after today's loss" improves the signal. The old 10/5/3 bands and the 3-5-7 rule are kept in seen_values as what was once said, with no weight.
- **Levels:** unit, book, portfolio.
- **Per class and style:** FX and metals: the day resets at the declared boundary, with the rollover minute flagged; indices: the cash day; crypto: no daily reset unless declared, weekend baselines; energy: a limit move is "risk uncontained", no automatic restart; stocks: a halt blocks the ladder's flatten step.
- **Ledger:** unit_daily_loss_limit, period_loss_budget, bms_daily_loss_limit, daily_loss_warning_fraction, brake_equity_basis, day_start_equity, account_daily_loss_limit.
- **Performance:** the opportunity cost of a stop after a bad day is accepted on purpose and measured (X0-52).
- **Survival:** three levels with the nearest tripping first; each says what tripped it.
- **Evidence chain:** prop and pod rules (live, no effect measure), the "bad day" quantile (arithmetic). Weakest link: no number here has a derivation older than this session; the whole ladder is circumstantial by his own word.
- **Maturity:** plausible.

#### X0-29. Intraday accelerators: tier ladder with dwell and same-day step-down; persistence press after a block test
- **Components:** A5-123, A5-124, A5-121, A5-131, A1-065, A5-136, A5-133, A5-134.
- **Need:** "accelerators make it aggressive, brakes make sure it never loses stupidly" (C19).
- **What it does:** size levels in a ladder; up one tier after a dwell of active days (Topstep: 10), down the same day a tier's loss limit is hit; no skipping; no size rise mid-session. A dead band between the up and down thresholds stops chatter (heparin's 46-70 s band). A persistence press (equity-curve scaling) is switched on only after the unit's own block-sum autocorrelation test passes at its horizon (about 950 trades for a 500-trade regime); the brake half of that pair (ease after a bad block) carried most of the factor-level value. AIMD with memory (x0.7 after a bad day, +5 percent per good day, slower near the last trip level) is the restore shape.
- **Levels:** unit, book.
- **Per class and style:** index and stock ORB families: active days; FX intraday: days; crypto: a declared day; energy: no step across a roll.
- **Ledger:** tier_dwell (new); size_levels, grow_back_rule, size_ramp_to_full, house_money_combined_cap.
- **Performance:** regime persistence pays (factor momentum 52 bp against 1-2 bp a month); the tier ladder is the best tested pair in R9.
- **Survival:** down is same-day; up waits a dwell; the memory ceiling stops a regrow straight into the last trip.
- **Evidence chain:** Topstep (live rules, no effect measure), Ehsani-Linnainmaa (strong, monthly factors), R9 script (arithmetic). Weakest link: no study of persistence in intraday retail strategies after costs.
- **Maturity:** plausible.

#### X0-30. Session-open, hand-over and fix minutes as caution windows with derived widths
- **Components:** A3-036, A3-035, A3-019, A3-229, A2-117, A3-212, A2-100.
- **Need:** D9 (session opens need a caution window like news), the hand-over scenario, the fix evidence (extraordinary volatility and negative serial correlation at the London 16:00 fix; gold volume up 50 percent at the PM fix).
- **What it does:** per instrument, a caution window after each open, at each hand-over and around each fix (WM/Reuters 16:00 London, Tokyo fix, ECB rate, gold fixes, month end). Inside it scalper entries are blocked and ORB entries allowed by design; exits are never blocked. The width is derived in event time: the minutes until the instrument's spread and volatility return to the matched non-event baseline. The old 25-minute warm-up and the node's hand-over buffer kind (built with no width) are replaced by that number. Re-entry cooling applies after a fill through the stop inside a window.
- **Levels:** unit, methodology, node.
- **Per class and style:** FX: the 16:00 fix and the overlap open; gold: the London fixes; indices: the cash open's first minutes; energy: the pit open; crypto: funding minutes stand in; stocks: the auction.
- **Ledger:** caution_window_width (new); session_handover_buffer_width, daily_dead_zone_width, warm_up_window, dominant_family_window.
- **Performance:** the blocked minutes are reported as a share of the day, so a window that swallows the day is visible (A3-208).
- **Survival:** the fix tail is where a mean-reversion scalper's worst fills live.
- **Evidence chain:** the fix studies (strong, academic), the opens' spread effect (insignificant in the NBER study, volatility rises). Weakest link: the width was never derived in any generation; the derivation here is proposed, not run. Collides with a fix unit (UB-18).
- **Maturity:** plausible.

### 2.4 Swing (days to weeks)

What the template must hold for this style, and why: the risk unit is a capped volatility target plus a gap allowance, because the hold crosses closes and the worst one-step move is the risk, not the daily variance; the stop is the thesis's own invalidation with a disaster clamp, because a stop that cuts a trend early costs more than it saves; brakes read drawdown and decay over long windows, because a swing unit gives few trades and a count means nothing; costs are carry, swap, funding and roll, booked where they belong; the accelerators with evidence are pyramiding for trend units and calm-volatility scaling with a guard.

#### X0-31. The swing risk unit: capped volatility target plus a gap allowance; stress loss binds
- **Components:** A1-011, A3-047, A3-025, A3-028, A5-097, A5-083, A1-010, A3-049.
- **Need:** the multi-instrument lens on a style that holds through closes, weekends and rolls.
- **What it does:** each position carries a set amount of daily volatility in account money (inverse volatility, capped; not inverse variance, which levers quiet spells). Stop width and position size are two separate knobs: the stop is volatility times a horizon factor; the size is the budget over (stop plus the gap allowance at a percentile for the closes the hold will cross). Volatility dynamics are pooled across the class with each instrument's own level (Carver's 214 futures, Bollerslev's pooled models). Stress loss, not routine risk, is the binding number for anything held over a close; a stressed correlation floor is applied when summing the sleeve.
- **Levels:** trade, unit, portfolio.
- **Per class and style:** FX: Sunday gaps and the weekly swap; indices: overnight gaps modelled apart from the session; metals: thin periods and rolls; energy: limit moves and expiry (never hold to the end: April 2020); crypto: no gap but thin weekend books, funding every 8 hours; futures: the contract month, basis kept separate; stocks: earnings gaps and halts.
- **Ledger:** gap_allowance_r (new); volatility_target, gap_loss_beyond_stop, stop_distance, swap_financing_cost, funding_cost.
- **Performance:** volatility scaling raised Sharpe for risk assets (Moreira-Muir); capped inverse vol keeps the steady risk contribution without the quiet-spell leverage.
- **Survival:** the gap is in the denominator, so a Sunday 80-pip gap is inside the budget; the cap stops leverage building in a long calm (Danielsson: long calm precedes crises).
- **Evidence chain:** Moreira-Muir (strong, contested in real time), pooled volatility (author backtests across hundreds of instruments), gap percentiles (arithmetic on history). Weakest link: a black-swan gap beyond the percentile still breaks it; the percentile is a choice.
- **Maturity:** solid.

#### X0-32. The swing stop: the thesis's own reversal is the exit; the hard stop is a disaster clamp
- **Components:** A5-081, A2-253, A2-268, A5-079, A2-231, A2-257, A5-080, A2-241.
- **Need:** A10 and A28 again, for a style where the stop-loss literature is clearest.
- **What it does:** for a trend unit the trend's own reversal (its signal flipping) is the working exit; the hard stop sits far enough away to be a disaster clamp only. Thesis-based invalidation names a falsifying condition per trade at entry (the Steward form) and closes when it is met, whatever the P&L. The stopping-premium pre-check decides whether any tighter stop helps (momentum: yes; mean reversion: it counts missed rebounds). Signal persistence sets the exit and the turnover policy. The stop fill is modelled at the stressed spread with an execution-delay option. A survival-analysis hold-or-close model (competing risks) is an allowed exit block once it passes the two-arm test.
- **Levels:** trade, unit.
- **Per class and style:** futures trend units: the clearest case; FX carry: the carry-unwind tell is the invalidation; gold: real yields and USD as the thesis; energy: inventory surprises as falsifiers; crypto: on-chain and funding anomalies; stocks: filings and guidance.
- **Ledger:** stop_premium_check (new); disaster_stop_distance, exit_reason_code, trailing_stop_setting, stop_policy_per_style.
- **Performance:** a trend unit that is not stopped out by noise keeps the move it was built for.
- **Survival:** the disaster clamp bounds the thesis being wrong in a gap.
- **Evidence chain:** Kaminski-Lo (assistant summary), the trend-reversal exit (author backtest, S&P long only), Steward (paper account, 102 days), survival analysis (author out-of-sample). Weakest link: all author backtests; no live test of thesis invalidation.
- **Maturity:** plausible.

#### X0-33. Swing costs in the hold decision: carry, swap, funding, roll; the CFD roll booked apart
- **Components:** A1-148, A3-026, A5-095, A5-031, A5-094, A1-152.
- **Need:** A11 (costs per market, instrument, timeframe and time of day must be known to the unit), the energy gap in R6.
- **What it does:** the daily swap in account currency (long and short, triple-swap day) enters the hold-and-size decision for anything held overnight; perpetual funding (paid or received, at its timestamps) likewise; a roll calendar per contract and per broker CFD is data with its own refresh. The CFD roll adjustment is booked as its own P&L line so it never reads as a unit loss or a stop trigger, and any stop or pending order inside a roll gap is flagged. Replay is contract-level with explicit rolls; a back-adjusted series never prices a hold. "For scalpers, swap rates don't really matter" (R5 22175): the cost table's swap column is zero for flat-by-close styles.
- **Levels:** position, unit, account.
- **Per class and style:** FX and metals: swap; crypto perps: funding; energy and index futures-based CFDs: roll; cash index CFDs: financing; stocks: borrow and recalls.
- **Ledger:** swap_financing_cost, funding_cost, exit_reason_code, hourly_cost_profile (new), round_trip_cost_r.
- **Performance:** a carry-positive hold is sized larger than a carry-negative one with the same signal, which is free money the sizer otherwise ignores.
- **Survival:** a roll gap can no longer trip a stop or a brake by accounting.
- **Evidence chain:** exchange and broker schedules (facts), the carry article (simulation with a synthetic swap), the roll anecdotes (snippet). Weakest link: the broker's rolled price drifted from benchmarks for days in one report.
- **Maturity:** solid for the mechanism; plausible for the broker facts.

#### X0-34. Swing brakes: cut because the edge fell, not because equity fell; drawdown ladders over long windows; a regime brake per class
- **Components:** A5-012, A5-022, A5-023, A3-044, A2-014, A5-146, A3-027, A2-015.
- **Need:** A25 (size down slowly, never pull out on one bad day) in the style where "one bad day" is one trade.
- **What it does:** a swing unit's brakes read three things over long windows. Decay: an estimated-edge drop (e-value or CUSUM on its own R stream) is the only reason to cut size for the unit's sake; equity falling on a known-stress day is not. Drawdown: a staged R ladder from the unit's high-water mark at its assigned budget (watch, reduce, suspend), with re-entry after a cause review at half the pilot budget and a dwell. Regime: a sticky statistical jump model per class cuts gross exposure in a bad regime; it never re-weights strategies. Style-aware worry lines set the drawdown depth and duration at which a given style's Sharpe is implausible, so the line is not the same for a trend unit and a carry unit. A dual-timescale loop (daily decisions, a 5-minute deterministic guard with hysteresis and staged re-entry) is the shape.
- **Levels:** unit, cluster, portfolio.
- **Per class and style:** futures trend: the drawdown ladder; FX carry: the carry-unwind tell is a fast cut; indices: the regime brake (1990-2023, with costs and a one-day delay); crypto: the 5-minute guard did the most work in SwingGuard (removing it: Sharpe 2.79 to 1.87); energy: a limit move is uncontained risk, no auto-restart.
- **Ledger:** drift_state, cusum_limit, drift_size_down_step, equity_drawdown_halt, brake_state, losing_days_limit.
- **Performance:** a trend unit is not cut for a drawdown that is inside its own style's expected depth; drawdown rules beat total-return rules only when skill decays (Man Group).
- **Survival:** the account drawdown signal (X0-08) is independent of all of this and acts at once.
- **Evidence chain:** the jump-model regime brake (author backtest, long sample, costs), SwingGuard (6 months, two coins), worry lines (simulation validated against closed forms). Weakest link: no swing-specific brake window in trades exists anywhere; a swing unit may need a year to show decay.
- **Maturity:** plausible.

#### X0-35. Swing accelerators: falling-risk pyramiding for trend units; calm-volatility scaling with a calm-duration guard
- **Components:** A5-120, A1-071, A5-129, A1-010, A3-052, A5-119, A1-072.
- **Need:** accelerators that pay in the one style where persistence is documented.
- **What it does:** pyramiding: one add per half-N favourable move up to four, each add smaller, all behind one stop, the unit's open risk never above its cap; allowed only for units whose stopping-premium check says momentum; never for mean reversion or scalpers. Calm-volatility scaling: raise toward a cap when forecast volatility is below normal for the session, with a calm-duration guard that stops further levering after a long calm; the instant cut on a volatility spike is the brake half of the pair. Volatility level and term structure are separate states.
- **Levels:** unit.
- **Per class and style:** futures and FX trends, metals and indices: pyramiding; equity-index and credit-like risk: calm scaling pays (Harvey et al.: risk assets only); crypto: calm scaling capped hard (2:1 leverage cap under retail rules); energy: no adds across a roll.
- **Ledger:** pyramid_add_rule (new); volatility_target, open_risk_at_stop, max_position_size_lots.
- **Performance:** regime persistence is the one place R9 found an accelerator beating fixed size.
- **Survival:** the cap and the calm-duration guard are the defences against levering into a jump; adds never raise risk above the unit's cap.
- **Evidence chain:** Turtle practice (snippet), MQL5 pyramiding (author backtests), Harvey et al. and Danielsson et al. (abstracts). Weakest link: the Turtle rule's attribution is unverified, and calm scaling hurt in real time across 103 strategies (Cederburg).
- **Maturity:** plausible.

#### X0-36. Swing frequency through cross-asset breadth; limits by tick-size tier and signal horizon
- **Components:** A3-236, A1-093, A1-096, A1-100, UB-35, UB-36.
- **Need:** C1 (many markets) for the style that trades least.
- **What it does:** a swing unit gets frequency by breadth across classes, allocated by hierarchical risk parity on P&L clusters (so many similar units do not pass as diversification) with bounded confidence-weighted tilts. Limits and capacity are set by instrument microstructure tier (volatility-normalised tick size) and signal horizon rather than by banning a class: fast trend on small-tick futures deteriorated most after 2009; slow trend held. Regimes cut gross; they never re-weight the units.
- **Levels:** unit, methodology, portfolio.
- **Per class and style:** futures across sectors: the home of this evidence; FX: strong USD factor, so N_eff is low; metals: gold as the diversifier; crypto: BTC/ETH beta; stocks: sector caps; energy: products are not interchangeable.
- **Ledger:** effective_independent_bets, cluster_exposure_cap, style_capital_split, price_increment.
- **Performance:** breadth is where a slow unit's Sharpe comes from (IR = IC x sqrt(BR)); the tick-size tier keeps capacity where it still exists.
- **Survival:** HRP stops the sleeve from being one bet; regimes cutting gross is the only regime action with a backtest behind it.
- **Evidence chain:** the 100-futures study (author backtest, 30 years), HRP (strong, out of sample), the fundamental law (theory). Weakest link: the impact mechanism for the tick-size result is proposed, not proven.
- **Maturity:** plausible.

### 2.5 Market structure: microstructure (spread, depth, order flow, liquidity by hour, fixes, news)

#### X0-37. Two per-instrument-hour tables, volatility and cost, never one open multiplier
- **Components:** A3-017, A3-039, A1-147, A3-084, A1-146, A3-016, A1-012, A4-061.
- **Need:** A11 and G7's finding that costs never reach the sizer; "busy can mean deep, wide, fast, or all three".
- **What it does:** every instrument carries two tables by hour bucket and session: a volatility forecast for the planned hold (X0-23) and a round-trip cost in R (spread crossed, commission, slippage against the mid, rejects, requotes). They are measured from QMX's own quotes and fills, per venue and per world (demo never calibrates live), refreshed daily, pooled across the class when thin. A missing cost cell refuses sizing; it is never zero. The old session multiplier (0.5 to 1.2 per window and family) is replaced by what the two tables say. The tables are the structural object every style's sizer and every brake reads.
- **Levels:** unit, system.
- **Per class and style:** FX: spreads narrow in London hours, widest 21:00-22:00 GMT, spikes at the 17:00 New York rollover and the Sunday open; the quote currency may differ from the account's. Indices: the cash open is liquid and fast. Metals: fixes. Energy: the EIA hour. Crypto: no session, venue-specific deep hours, funding minutes. Futures: the underlying's deepest hours, maintenance breaks. Stocks: the auctions.
- **Ledger:** hourly_cost_profile, hourly_volatility_profile (new); spread_cost, commission_cost, slippage_cost, swap_financing_cost, funding_cost, session_windows.
- **Performance:** a scalper's size follows its net edge by hour instead of a clock story; an intraday unit's size follows the move.
- **Survival:** "refuse when missing" is the rule that stops a unit from sizing on a cost it has never measured.
- **Evidence chain:** the NBER spread-by-hour study (strong), MQL5 hourly spread profiles (author measurements), the QMB cost ports (built, rates deferred). Weakest link: no fills exist yet, so every cell starts as a synthetic calibration.
- **Maturity:** solid.

#### X0-38. The venue rule: never call a quote a book; route microstructure methods per class
- **Components:** A3-078, A3-080, A3-066, A3-011, A3-238, A3-015, A4-106, A3-081.
- **Need:** D6 (what is microstructure; agents could summarise it), the multi-instrument lens on a word that means different things per venue.
- **What it does:** a flag per instrument record says whether the feed is a book (orders you can execute against) or a quote (a dealer's price). Exchange futures, crypto per venue and stocks have books: order-flow imbalance, depth, queue position and markout as toxicity apply. Spot FX and CFDs are quotes: dealer skew after repeated same-side fills, last-look rejection rates read together with the quoted spread, and markout as a measure of the dealer, not of a queue. VPIN and bar-based toxicity are diagnostics only. The square-root impact law is a sanity check for parent orders, not retail size. Microstructure features are deterministic code; an agent summarises them at a slow cadence and may veto a unit on capacity.
- **Levels:** unit, position, node.
- **Per class and style:** as above; index CFDs are not index futures; a metal CFD is not Comex; crypto ETFs behave like crypto; a US single stock is fragmented across venues so one book omits the rest.
- **Ledger:** sqs_score, spread_cost_guard, microstructure_multiplier, slippage_cost, instrument_class.
- **Performance:** methods are applied only where they can work, so no scalper is placed on a CFD by a book signal.
- **Survival:** a broker-specific signal is labelled as such and never treated as the global FX book.
- **Evidence chain:** Cont-Kukanov-Stoikov and MLOFI (strong for explanation on exchange books), last look (simulation), dealer skew (simulation). Weakest link: evidence is weak that any retail microstructure gate improves net returns.
- **Maturity:** solid for the rule; plausible for the methods.

#### X0-39. News as measured impact per release and instrument, with driver tags beyond currency
- **Components:** A3-130, A3-131, A3-133, A3-124, A3-228, A3-067, A2-100, A3-129, A3-134, A3-135.
- **Need:** C28 (news is the kill switch's job; on news days look at which instruments are affected, then isolate), his sectoring by instrument, region and correlated pairs.
- **What it does:** the calendar's colour levels are replaced by measured impact per release and instrument in event time (move and spread multiple against matched non-event minutes). Each event carries driver tags: both FX legs, the home exchange, the region, the commodity, the sector; so a US CPI print blocks indices, gold and the USD pairs, not only "USD". The window policy is by event type: flat through, cool down, never widen a stop. Liquidity withdraws before scheduled news, so the before-window is an execution brake, not a direction call. A surprise backstop (a velocity tell) catches the release the calendar missed. A stale calendar fails entries closed. A versioned historical event file makes the rules testable, and a news-collision rate per unit says how much of its day the windows take.
- **Levels:** node, unit, portfolio.
- **Per class and style:** FX: central banks, pair-relative surprises; indices: macro releases, mega-cap earnings, rebalances; metals: real rates and USD; energy: EIA Wednesday 10:30 ET, gas Thursday, OPEC with a decision-type field; crypto: 24/7 news where authenticity is the risk, exchange notices, unlocks; futures: tied to the contract month; stocks: EDGAR acceptance timestamps, earnings, halts. Scalpers get the widest windows; swing units get a gap factor instead.
- **Ledger:** event_impact_measured, event_window_width (new); news_blackout_before, news_blackout_after, news_impact_level_map, news_calendar_max_staleness, window_forced_flat.
- **Performance:** windows sized by measured impact are narrower than colour-level windows, so fewer trading minutes are lost (A3-208 is the test).
- **Survival:** the window blocks entries only; exits are never blocked; the stale calendar fails closed.
- **Evidence chain:** the liquidity-withdrawal study (author backtest, futures), real-time price discovery (strong, old), the driver-tag idea (his and the assistant's). Weakest link: energy event-response sizes are snippet-level; the surprise backstop is an idea.
- **Maturity:** plausible.

#### X0-40. Liquidity by hour drives the day budget: scale it with open breadth
- **Components:** A3-114, A3-040, A3-214, A3-058, A1-082.
- **Need:** the 24-hour system where only some classes are open at a given hour (C1, D10).
- **What it does:** the day risk budget is scaled by the share of the usual effective breadth that is open now, floored. On an FX weekend only crypto is open, so the budget shrinks rather than crypto inheriting the whole book's day. In single-class hours (Asia for JPY pairs, US afternoon for energy) the budget is the share those classes usually carry.
- **Levels:** portfolio.
- **Per class and style:** crypto on weekends; FX in the Asian session; indices overnight (thin futures); energy outside US hours; stocks only in regular hours.
- **Ledger:** day_budget_breadth_scale (new); portfolio_daily_risk_budget, effective_independent_bets, activity_session_windows (new).
- **Performance:** none directly; it stops the book from spending a full day's swing on one thin class.
- **Survival:** the weekend-crypto scenario (A3-214) is the case it exists for.
- **Evidence chain:** idea; the weekend crypto volatility factor (author backtest) is the one measured piece. Weakest link: the floor's value.
- **Maturity:** plausible.

### 2.6 Market structure: macro regimes and cross-asset links

#### X0-41. Factor buckets with a residual, and two layers of caps
- **Components:** A4-051, A3-048, A1-097, A1-163, A3-050, A1-114, A5-027.
- **Need:** the multi-instrument lens at the BMS: shared exposures (USD, equity beta, duration, energy, crypto beta) and the "same bet" across wrappers.
- **What it does:** every instrument carries a short class code and a bucket (fx-major, fx-cross, metal, index-us, index-eu, index-asia, crude, products, gas, stock, crypto-perp-major, crypto-perp-alt, residual), SIMM-style, with a residual bucket at zero within-bucket correlation for anything unclassified. Caps are two-layered: strategic by factor exposure (an index future and an ETF on the same index draw on one factor budget) and tighter per instrument for leverage, margin, liquidity and gaps. FX exposure sums by currency leg; the rest through the factor covariance.
- **Levels:** position, unit, portfolio.
- **Per class and style:** FX: USD and carry factors; indices: regional beta; metals: gold on real yields vs industrial on growth; energy: crude, products and gas apart; crypto: BTC/ETH beta, USD liquidity, equity beta in the overlap; futures: the underlying's factor; stocks: market, sector, style.
- **Ledger:** class_risk_cap (new); cluster_exposure_cap, currency_exposure_limit, per_instrument_exposure_cap, instrument_class, portfolio_exposure.
- **Performance:** the BMS can see two sleeves that are one bet and stop funding the second.
- **Survival:** the factor cap catches the risk-off day where every class is one bet.
- **Evidence chain:** SIMM and ISO codes (live in their own field), asset and factor risk budgeting (paper), currency legs (MQL5 author checks). Weakest link: the bucket list is a draft; energy's split is from one chat.
- **Maturity:** solid.

#### X0-42. Regimes: filtered probabilities per class, cut gross, never re-weight, links re-tested on a schedule
- **Components:** A3-043, A3-044, A3-045, A3-059, A3-046, A3-049, A1-129, A1-100, A3-057.
- **Need:** the macro half of "micro and macro structure" (D6, M10), with the warning that macro data are revised and lagged.
- **What it does:** regime models are fitted per class on point-in-time data and hand the risk service filtered probabilities, never smoothed labels. Their only action is to cut gross exposure per class (A3-045's lesson: regimes that re-weight strategies lost). Conditional correlation is monitored (DCC or exponentially weighted) as a diagnostic that diversification is weakening, with a stressed correlation floor applied when sizing. Cross-class links are re-tested on a schedule because they appear and vanish (weekend crypto now leads Monday risk in stocks and bonds). Size is set on stressed correlation, not yesterday's.
- **Levels:** portfolio, account.
- **Per class and style:** indices: the jump model (1990-2023); FX: USD and risk-appetite regimes; metals: haven vs growth; energy: supply vs demand shock as a scenario selector; crypto: too little history for its own model; stocks: sector co-movement rises into sell-offs.
- **Ledger:** regime_probability_vector (new); cross_market_stress_reading, unit_result_correlation, portfolio_correlation_ceiling.
- **Performance:** the regime brake with costs and a one-day delay held up over 33 years on indices.
- **Survival:** cut-only, point in time, per class: three rules that stop a regime model from doing harm.
- **Evidence chain:** Hamilton, Engle DCC (strong), the jump-model brake (author backtest), the re-weighting null (author backtest). Weakest link: a model fitted to one era misclassifies the next.
- **Maturity:** solid for the rules; plausible for the models.

#### X0-43. Risk-off two-layer tell stack per bucket; no single master score
- **Components:** A3-092, A3-088, A3-089, A3-090, A3-097, A3-099, A3-100, A3-101, A2-080, A3-098.
- **Need:** C27's "sense this type of move" with evidence, sectored.
- **What it does:** per bucket, fast tells (velocity: too far too fast; a volatility jump inside about 12 one-minute bars; spreads widening together across the class; a safe-haven move; a carry unwind) and slow confirmations (financial turbulence as a Mahalanobis nowcast, correlation surprise over magnitude surprise, the absorption ratio). A bucket alert blocks entries and steps down that bucket's risk; a separate whole-book control covers broad shocks. Bad data means "risk state unknown", not calm. The stack feeds X0-07's two-tell rule and X0-06's fast layer.
- **Levels:** portfolio, cluster.
- **Per class and style:** FX: USD, rates, risk assets, a one-currency divergence as a local cut; indices: regional, vol, rates, credit; metals: precious vs industrial; energy: contract-specific, roll squeezes are local; crypto: BTC/ETH, venues, funding, liquidation flows (taker-flow variance compression as a cascade warning); stocks: sector, peers, own liquidity.
- **Ledger:** cross_market_stress_reading, market_isolation_trigger, effective_bets_drop_trip, sqs_score.
- **Performance:** a bucket-local cut keeps the rest trading.
- **Survival:** two layers so that a single noisy tell cannot isolate a calm market.
- **Evidence chain:** turbulence and correlation surprise (author backtests, long samples), absorption ratio (some 5-minute and 1-hour forecasting value), the tells (author backtests). Weakest link: no lead time is reported for the graph and spectral detectors; the stack has never been run as one.
- **Maturity:** plausible.

### 2.7 Cross-cutting: the matrix itself, placement, windows, multi-position, worlds, wild

#### X0-44. The style x class cell is the unit of defaults: the override chain and pooling policy
- **Components:** A4-050, A4-051, A4-185, A4-183, A4-195, A5-048, A5-099, A1-166, A1-063.
- **Need:** A5 (one template per unit type) and M26 (the multi-instrument lens on everything) as one thing; A23 (the chassis handles any angle without the baseline deviating).
- **What it does:** defaults attach to cells of the matrix and resolve through a fixed chain where the later level wins: preset, style, class, bucket, instrument, venue account, unit, market; plus timeframe and session as axes; plus an MIS reading word as a key once reads compile. Every resolved value carries its provenance path. Children may tighten caps, never loosen them; event overrides expire. Pooling policy per parameter type: pool normalised statistics (volatility dynamics, cost shapes) across the class with each instrument's own level; never pool contract facts (tick size, minimum lot). An instrument earns its own number only when its record shows it differs from the pool (empirical-Bayes shrinkage). A derivation ladder with fallbacks means no key setting is ever blank.
- **Levels:** unit, cluster, methodology, portfolio, account.
- **Per class and style:** the class and bucket levels carry lot granularity, cost shape, session and gap defaults; the style level carries the risk unit, the stop policy, the brake signal and the accelerator list (sections 2.2-2.4); the cell is where they meet.
- **Ledger:** instrument_class, numeraire, number_motion_mode, calibration_shrink_k, judge_market_shrink_k, holding_horizon (new).
- **Performance:** a new class or style is a new row or column, not a new template; defaults are shared where the evidence says they can be.
- **Survival:** "children only tighten" is what keeps a unit from loosening a book cap.
- **Evidence chain:** software inheritance schemes (VS Code, CSS, systemd, n8n, all checked), SIMM buckets (live in its own field), partial pooling (statistics; no multi-instrument trading comparison). Weakest link: no source shows partial pooling raised held-out returns.
- **Maturity:** solid for the chain; plausible for pooling.

#### X0-45. Per-class feasibility map as a start-up gate
- **Components:** A3-013, A1-157, A5-042, A3-002, A5-096, A1-158, A1-151.
- **Need:** D17 (the lead's "at $500, costs and minimum lot sizes choose the markets before the MIS does", never reacted to), A22 (demo units at boot).
- **What it does:** before a class may trade live, its feasible size (the smallest allowed position with costs and stressed slippage) is compared with the unit's day risk share, and the regulatory leverage cap is checked. The verdict (tradable, simulate only, wait) is shown per class and re-derived per broker and as the budget grows. A class the budget cannot risk keeps its units on paper, visibly, rather than raising the budget or rounding up. The broker reality check runs before any symbol is enabled.
- **Levels:** system, portfolio.
- **Per class and style:** on a $500 book: unlevered spot crypto, FX with true micro lots and liquid low-price stocks are testable; micro index futures and micro gold sometimes; energy and full-size futures generally not; crypto under a 2:1 retail cap binds at once. A contract that meets margin is not one that fits the risk budget. Not anchored to $500: the verdict is a function of the budget.
- **Ledger:** class_feasibility_verdict, feasible_size_usd (new); min_lot, value_per_point, leverage, instrument_class.
- **Performance:** the book does not pay to learn that a class cannot be traded at its size.
- **Survival:** no silent oversize; no class enters live by accident.
- **Evidence chain:** arithmetic and regulatory rules (snippet for the EU caps). Weakest link: broker product specs change, and the jurisdiction that binds his account is unknown to me.
- **Maturity:** solid.

#### X0-46. Placement score with costs normalised and the edge shrunk before ranking
- **Components:** A1-133, A3-187, A3-240, A1-027, A1-166, A1-134, A3-184.
- **Need:** D2 (placement is the shared job: put each unit where it has the best odds given its logic).
- **What it does:** for each unit x market x cell, a score n x EV squared over variance, with costs normalised to the cell first (X0-37) and the edge shrunk for the search (James-Stein) and toward the family prior. A filter or MIS condition is worth having only if it raises the score. Units are re-ranked under two execution assumptions and a cell whose rank flips is marked unstable. Group selection (which units run together) is a search and gets the deflated-Sharpe treatment. The MIS routes (narrows); placement ranks and needs a widen door, flagged for the MIS.
- **Levels:** unit, portfolio.
- **Per class and style:** rank within a class; cost normalisation matters most for scalpers and for crypto (fee tiers); the record per unit and market is the input (his own caution: the router can be wrong).
- **Ledger:** ranking_score, trade_rate, expectancy_r, result_spread_r, effective_tries, correlated_market_merge_threshold.
- **Performance:** breadth goes where the score says, which is the System 1 bet made measurable.
- **Survival:** the squared edge rewards lucky estimates, so shrinkage first is not optional.
- **Evidence chain:** the 15 Oct derivation (QMX), James-Stein (simulation), rank instability (synthetic runs). Weakest link: a thin cell's score is noise.
- **Maturity:** plausible.

#### X0-47. Sniping windows as counted out-of-sample slices; agents propose, QMB proves
- **Components:** A3-033, A1-070, A4-172, A2-184, A2-181, A3-035, A1-069.
- **Need:** D8 (how are sniping windows found, by agents or deterministically), M10's "first confirm what it is".
- **What it does:** "sniping window" has no professional meaning (retail sniper entries, ICT kill zones; to professionals it is latency arbitrage). The honest version: a time slice where one unit's net edge in R on one instrument is higher out of sample than in the rest of its day. Windows lower cost or raise activity; they do not hand out edge. Agents propose candidate slices from the two hourly tables (sessions, fixes, releases, deep hours); QMB proves each on later data with planned interim looks; every slice tested is a counted try; a proven window gets the lift in X0-19 and lands in the Library as an artifact. Picking hours from the unit's own backtest P&L is look-ahead and refused.
- **Levels:** unit, methodology.
- **Per class and style:** FX: the London hours and the fixes (the fix reversal is positive only at half spreads); gold: the fixes; indices: the cash open and the last half-hour (intraday momentum survives costs in the ETF study); crypto: venue-deep hours; energy: the EIA hour is a caution, not a window; stocks: in-play opens.
- **Ledger:** premium_window_flag, session_multiplier, effective_tries, verification_trades_needed, hourly_cost_profile (new).
- **Performance:** for a scalper a lower-cost slice can turn a gross edge net; that is the whole value, and it is real where the slice is.
- **Survival:** counting tries stops the many-slices problem from inflating false windows.
- **Evidence chain:** the NBER and Bank of Canada window studies (strong on cost and activity, nothing on window sizing), the prop-firm guide's "the time window does not produce any edge". Weakest link: no window-sizing test exists.
- **Maturity:** solid for the definition; plausible for the lift.

#### X0-48. Contexts, not sessions: overrides keyed by a reading word; overlaps related only by the same-bet key
- **Components:** A3-030, A4-183, A1-115, A3-213, A3-183, A2-110.
- **Need:** D10 (sessions and overlaps across FX, crypto and futures at once; "design for complexity, not a complex system"), accepted by him in M10.
- **What it does:** units do not switch by named session. Each reads context words (mean-reverting, stressed, trending) from the MIS board and its own windows; two positions in an overlap are not a contradiction because each is sized on its own and they are related only through the bet key (same underlying move counted once). Overrides may be keyed by a reading word rather than a session. Sessions remain as the fallback when the board is stale (which fails open today: the unit trades all its markets on its own rules), and the fail mode is declared per unit.
- **Levels:** unit, portfolio.
- **Per class and style:** the operator's own case: FX, crypto perps and futures across Tokyo, London and New York; crypto has no session at all, so context is the only key it ever had.
- **Ledger:** context_size_modifier, board_stale_after, session_windows, positions_per_instrument.
- **Performance:** a unit trades where the context fits, at any hour, instead of a clock story.
- **Survival:** the same-bet key is the one thing that stops two units from doubling a bet in an overlap.
- **Evidence chain:** his acceptance and the built board read (C-22, not fed). Weakest link: context words need an MIS that runs on a venue, and it never has.
- **Maturity:** plausible.

#### X0-49. Style as a dial: one template on a holding-horizon axis (wild)
- **Components:** A3-236, A2-268, A3-016, A1-012, A5-083, A4-185.
- **Need:** A23's "handle any amount of stress from new angles without the baseline deviating"; the observation that every style default in sections 2.2-2.4 reads the holding horizon.
- **What it does:** instead of three named types, the unit carries a holding horizon h (minutes to weeks). Cost in R, the brake window, the volatility forecast horizon, the gap allowance, the stop policy test, the accelerator list and the dwell clock all derive from h. "Scalper", "intraday" and "swing" become presets that set a range of h and a name. A unit that fails to exit and drifts across a style boundary is caught because its realised h moved, not because someone renamed it. Signal persistence at h sets the exit and turnover policy; limits are by h and microstructure tier, not by class.
- **Levels:** unit.
- **Per class and style:** the class still owns contract facts, sessions and gaps; the dial owns everything that scales with time in the trade.
- **Ledger:** holding_horizon (new); max_hold_time, stop_policy_per_style, hourly_volatility_profile (new).
- **Performance:** no default is ever wrong because a unit's name was wrong; a 15-minute mean-reversion unit on crypto and a 5-minute one on FX get defaults from where they sit, not from one label.
- **Survival:** the style-boundary drift (an intraday unit holding overnight by accident) is sized for because h is measured, not declared.
- **Evidence chain:** the 100-futures horizon study (author backtest), the multiplicative volatility model (author backtest), the rest is design. Weakest link: entry-logic families (breakout, mean reversion, trend) may need their own axis; one dial may not be enough. Collides with his "one template per type" (A5).
- **Maturity:** wild.

#### X0-50. The dry chassis per cell, nightly (wild)
- **Components:** A1-174, A3-175, A4-181, A2-135, A2-178, A3-173.
- **Need:** E16 (one agent's "it couldn't lose" was not enough), the brake trap (any brake looks good on a losing strategy because it trades less).
- **What it does:** random entries run through the full template in every style x class cell, nightly, on replayed data and beside live units as a control twin. The result is what the chassis itself costs or saves with no edge: its drag from costs, its brake precision, its blocked minutes, its floor odds. Any brake, gate or accelerator must beat the random control at the same activity. A no-edge agent-based market is the second null.
- **Levels:** unit, methodology, system.
- **Per class and style:** the drag differs by cell: crypto fees, FX spread at rollover, micro-futures commission, energy windows; the dry chassis is how the matrix proves its own defaults.
- **Ledger:** brake_precision, expectancy_floor_r, cost_stress_multiple, monte_carlo_p5_floor.
- **Performance:** a template that knows its own drag can be tuned to cut it.
- **Survival:** the random control is the one test that cannot be fooled by a losing unit trading less.
- **Evidence chain:** the 23482 random-control design (one controlled test), the dry-chassis idea (this session). Weakest link: nobody has run it; it needs the whole template to exist.
- **Maturity:** wild.

#### X0-51. Multi-position units: the bet key, per-position cuts, a unit open-risk cap, a bulkhead
- **Components:** A1-115, A3-105, A1-120, A5-091, A1-034, A2-068.
- **Need:** A8 (several positions per unit, "not every type can"), C18 (the correlation ledger is "internally external").
- **What it does:** a unit may hold several positions when its template allows it. Each position has its own stop or cut and its own size; positions on the same bet (same underlying move, keyed by the bet key from the exposure ledger) count once; the unit's total open risk is capped; a bulkhead compartments open risk per unit and per market so one unit's basket cannot drain another's budget; a basket loss cut deletes pending orders too. Budget-constrained and reserve sizing from concurrent positions (A1-034) is the arithmetic.
- **Levels:** position, unit, portfolio.
- **Per class and style:** a mean-reversion scalper rarely (his caveat); an ORB family across opens yes, each open its own position; a swing unit across classes yes; crypto perps: one position per instrument under netting; FX: two pairs sharing a leg are one bet.
- **Ledger:** positions_per_instrument, max_open_positions, open_risk_at_stop, per_instrument_exposure_cap, cluster_exposure_cap.
- **Performance:** breadth inside the unit, where the logic supports it.
- **Survival:** the bet key and the unit cap are the lead's three rules he accepted (A8), made into fields.
- **Evidence chain:** bulkheads (live in their own field), the bet key (idea), concurrent sizing (idea). Weakest link: the bet key needs the exposure ledger (X0-11) to exist first.
- **Maturity:** plausible.

#### X0-52. The cost-of-conservatism meter feeding the BMS re-slot (wild)
- **Components:** A5-073, A1-121, A4-174, A2-030, A4-202.
- **Need:** M33 (the sitting duck; survival is a constraint, not the goal), A14 ("too safe").
- **What it does:** per sleeve per day: budget allowed minus budget used, plus the R forgone during brake holds whose precision later showed no action was needed, plus the trip tax (units paused, time lost). The meter is a first-class RiskState row. The BMS re-slot reads it: a sleeve idle for long is a candidate to lose a slot; one always at its cap with good precision is a candidate to gain one. Shedding by declared priority class when the budget tightens is the other direction.
- **Levels:** unit, book, portfolio.
- **Per class and style:** scalper sleeves show it as blocked minutes and cost-gated hours; swing sleeves as idle budget; a class in isolation shows it as the trip tax.
- **Ledger:** cost_of_conservatism (new); brake_precision, slot_rebalance_rule, unit_day_risk_share (new).
- **Performance:** the only hybrid whose whole job is performance with intention.
- **Survival:** it moves slots, never limits; the parent limit is untouched.
- **Evidence chain:** the measure is an idea; alarm-burden evidence is from hospitals. Weakest link: nobody has measured a trip tax in trading.
- **Maturity:** wild.

#### X0-53. World switch resets: costs calibrated per world, never carried across
- **Components:** A2-124, A3-220, A4-036, A1-146, A4-168.
- **Need:** D13 (split demo and live so a unit trades the same way; can slippage be measured on demo), D14 ("paper trading is demo trading").
- **What it does:** one code path for demo and live; only the account differs. But the cost tables, the markout record, the spread histogram and the activity gauge are calibrated per world and never carried: demo fills are kinder, and a demo pass never stands in for live calibration (G7 4.3). A world switch (paper to live, PC to VPS, broker to broker) resets the counters it must and carries the ones it may, by a declared rule; the ramp (X0-09) restarts at the pilot tier on the new world.
- **Levels:** unit, node, system.
- **Per class and style:** FX and CFDs: the demo-to-live slippage gap is the whole question; crypto testnet: no real liquidity at all; futures: no route yet.
- **Ledger:** paper_to_live_carry_rule, state_carry_rule, hourly_cost_profile (new), slippage_cost, paper_starting_balance.
- **Performance:** a unit promoted on demo costs is not surprised by live costs at full size.
- **Survival:** the pilot tier on the new world is the defence.
- **Evidence chain:** AutoQuant's one-ledger practice (author, short real-money phase), the built one-code-path (stack). Weakest link: the live binding is not built.
- **Maturity:** solid.

#### X0-54. Crypto as the 24/7 spine (wild)
- **Components:** A3-040, A3-058, A3-214, A3-235, A5-096, A1-119, A3-068.
- **Need:** C1's "around the clock" taken literally: the one class that is always open.
- **What it does:** crypto gets activity sessions, not clock sessions; funding minutes are caution minutes; the weekend crypto volatility factor is a Monday-open risk input for indices, metals and bonds (it now leads them); a liquidation-cascade warning (taker-flow variance compression) is a bucket tell; a three-state liquidity label per instrument (calm, mixed, stressed) feeds the fast layer. The day budget on an FX weekend is scaled by breadth (X0-40), so crypto carries the book without inheriting its whole budget. Spot before perps on a small account (liquidation can beat the stop); the 2:1 retail cap binds at once where it applies.
- **Levels:** unit, portfolio, system.
- **Per class and style:** crypto scalpers and intraday; the Monday rule touches index and metal swing sleeves.
- **Ledger:** activity_session_windows, day_budget_breadth_scale (new); funding_cost, day_boundary, liquidation_stop_check.
- **Performance:** the weekend is traded, at a budget that fits it.
- **Survival:** spot first; the cascade tell; the breadth scale.
- **Evidence chain:** crypto periodicity (author backtest), the weekend factor (author backtest), the cascade warning (author backtest). Weakest link: one exchange per study; Hyperliquid's own cycles are unmeasured.
- **Maturity:** wild (as a spine); its parts are plausible.

#### X0-55. Energy and stocks as data overlays on the general machinery
- **Components:** A5-094, A3-143, A3-144, A2-264, A3-096, A3-141, A5-095, A5-031.
- **Need:** the two classes the research is thinnest on (R6: energy not covered; stocks thin), handled without special formulas.
- **What it does:** energy needs no special sizer: the volatility-scaled size plus three overlays as data with their own refresh: the event calendar (EIA petroleum Wednesday 10:30 ET, gas Thursday, holiday shifts, OPEC with decision type; inventory releases are jump events for crude and gas alike), the roll calendar per contract and per broker CFD (no stop sits inside a roll gap; never hold to expiry), and gas apart from crude. Stocks: an earnings, filings and halts calendar; a halt allowance in sizing (a stop cannot fill through a halt); exchange breakers as per-product pauses plus market-wide tiers; "exchange resumed" is not a re-enable signal (spreads, depth and fills inside collars must normalise first).
- **Levels:** unit, cluster, node.
- **Per class and style:** energy intraday and swing (scalping generally not feasible at small size); stocks intraday ORB in play and swing on news; both get the widest event windows.
- **Ledger:** news_blackout_before, news_blackout_after, window_forced_flat, gap_loss_beyond_stop, swap_financing_cost, event_impact_measured (new).
- **Performance:** two classes become tradable by the same template instead of waiting for their own.
- **Survival:** the April 2020 negative-price expiry and the halted stock are the two cases the overlays exist for.
- **Evidence chain:** exchange and EIA schedules (facts), the inventory-shock sizes (snippets), the mini-flash-crash and halt studies (author event studies). Weakest link: no energy scalping or energy sizing evidence at all.
- **Maturity:** plausible.

## 2.8 The matrix, filled: what the template must hold per style and class

Each cell: risk unit / stop and cut / brakes vs frequency / costs to size / accelerators that can pay. Where a cell says "general", the style row's answer applies unchanged. Everything here is a starter default with its hybrid as the reason; the numbers lens sets values.

| | Scalping (1-5 m, tick) | Intraday (opens, ORB, mean reversion) | Swing (days to weeks) |
|---|---|---|---|
| **FX** | R after costs with cut; spread and swap bind, 0.8 pips on EURUSD is 0.16R at a 5-pip stop (X0-13). FI cut plus disaster stop at p95 spread (X0-15). Money quantile brake at own rate; hours clause on USD releases (X0-16, X0-10). Cost table by hour: London cheap, 21:00-22:00 GMT dear, rollover and Sunday open refused (X0-37). Day-ledger cushion; London window lift (X0-19). | Budget over stop plus cost reserve; vol forecast by pair, JPY and AUD also Asia (X0-23). Momentum: trail; mean reversion: half-life exit, no breakeven (X0-24). Daily ladder from own distribution; opens correlate on risk-off days (X0-28, X0-25). Flat before the weekend; fixes as caution (X0-27, X0-30). Tier ladder with dwell (X0-29). | Capped vol target plus Sunday gap at a percentile (X0-31). Carry-unwind tell as invalidation; disaster clamp (X0-32). Drawdown ladder from HWM; USD factor cap (X0-34, X0-41). Swap long and short, triple-swap day (X0-33). Pyramiding for trend; calm scaling capped (X0-35). |
| **Indices** | Index CFD is a quote, not the future's book (X0-38). Cash open first minutes are caution (X0-30). Micro futures: 2-point commission binds, 11 of 14 retail 5-minute families failed the floor (X0-14). Generally not feasible at small size except micro (X0-45). | ORB family across cash opens, in-play gated, sized as one family (X0-25). After the auction settles; last half-hour momentum as a window (X0-47). Overnight gap apart from the session (X0-27). Regional beta cap (X0-41). | Vol target plus overnight gap; stock-bond hedge unreliable in rate shocks (X0-31, X0-42). Regime brake per class (X0-34). Calm scaling pays here (risk assets) with a guard (X0-35). Futures-based CFD roll booked apart (X0-33). |
| **Metals** | Micro gold 0.01 lot with a $3 stop is already 1 percent of $300; coarse (X0-17). Fix minutes caution (X0-30). Gold's 8-hour half-life fails a 5-minute mean-reversion gate (X0-14). | Gold intraday mean reversion possible at the half-life (X0-26). London and New York opens (X0-25). US inflation and jobs as measured events (X0-39). | Gold on real yields, USD and haven demand vs industrial on growth; the diversifier to equity (X0-41, X0-36). Rolls and thin periods (X0-33). Pyramiding on trend (X0-35). |
| **Energy** | Generally not feasible at small size; natural gas hardest (X0-45). EIA hour refused (X0-14). | Active US hours; EIA Wednesday 10:30 ET and gas Thursday as jump events for crude and gas alike; OPEC with decision type (X0-55, X0-39). Smallest feasible exposure, no step across a roll (X0-09). | Vol target plus limit-move stress; never hold to expiry (X0-31). Roll calendar as data; CFD roll apart (X0-33, X0-55). Supply vs demand shock as scenario selector (X0-42). No adds across a roll (X0-35). |
| **Crypto** | Taker fees bind: 10-20 bp round trip against a 1.3 bp gross reversal (X0-13, X0-14). Spot before perps; disaster stop inside the liquidation price (X0-15). Declared 24/7 day for the money brake (X0-16, X0-27). Activity sessions; funding minutes caution; markout on central books (X0-21, X0-18). 2:1 cap where it applies (X0-45). | Real 15-minute reversal in most pairs but fees bind (X0-26). Activity sessions not clock (X0-54). Weekend books thin; day budget scaled by breadth (X0-40). | Vol target plus weekend realised move; funding every 8 hours in the hold decision (X0-31, X0-33). 5-minute guard did most of the work (X0-34). Calm scaling capped hard (X0-35). Weekend vol as Monday input for other classes (X0-54). |
| **Futures** | Real book: OFI, depth, queue, markout apply (X0-38). Per-contract commission; one contract over budget means zero (X0-17). No route in the build yet (X0-45). | Underlying's deepest hours; maintenance break as a mid-session deadline (X0-27). Contract month in every record (X0-33). | Fast trend on small-tick futures deteriorated most; limits by tick-size tier and horizon (X0-36). Contract-level replay with rolls (X0-33). Pyramiding is the Turtle home (X0-35). |
| **Stocks** | Fragmented quotes; one venue's book omits the rest (X0-38). Per-share fees and borrow (X0-13). Liquid low-price names maybe (X0-45). | ORB on stocks in play: the strongest ORB evidence (X0-25). Auction, halts, earnings as measured events (X0-39, X0-55). Halt allowance in sizing; a stop cannot fill through a halt (X0-15). | Vol per share plus issuer and event stress; sector caps (X0-31, X0-41). Thesis invalidation from filings and guidance (X0-32). News-LLM signals work at a daily horizon after costs (idea bank). Borrow and recalls in the hold (X0-33). |

Rows that hold everywhere: the three sleeve numbers (X0-01); the day share by effective bets (X0-02); the cushion ledger with a declared anchor (X0-05); the three signals apart (X0-08); the hours clause (X0-10); the exposure ledger (X0-11); two hourly tables (X0-37); feasibility first (X0-45); contexts not sessions (X0-48).

## 3. Problems and solutions (the problem-solving pass)

Run as `bmad-cis-problem-solving` in headless form: refine the statement, name the root cause, give at least two options with trade-offs. No picks; the funnel decides.

### P1. "One unit gets $20 alone but ten units get $2 each" (C29, M11)
- **Refined:** two different rules were answered as one. Kelly for independent small bets gives each unit its solo size, so total risk grows with N. A fixed total daily swing gives each unit 1/sqrt(N(1+(N-1)rho)) of the budget. A plain 1/N split is a third rule that under-uses independent units.
- **Root cause:** the lead's answer mixed the growth-optimal rule with the budget rule without naming either.
- **Options:**
  - (a) Effective-bets split as the baseline (X0-02). Survives a wrong edge; growth about 3x a plain split with independent units. Trade-off: a wrong rho (0.3 taken as 0) doubles the swing; needs the exposure ledger to estimate rho fast.
  - (b) Kelly-independent full size for every unit. Fastest growth when the edge is as believed. Trade-off: at half the edge ten full-size units touch the floor in 11 percent of runs against 5.8 percent for one (STATE 10); no survival at no edge.
  - (c) Hybrid: (a) as baseline, (b) as a per-unit accelerator switched on only after that unit's block-persistence test passes, and only inside the BMS parent limit. Trade-off: two rules to explain; the switch needs about 950 trades of evidence.

### P2. Sizing that does not lean on the edge (A24)
- **Refined:** he wants the edge as a range and the system to carry a weak real edge; the lead's "twice the edge, twice the size" is the opposite.
- **Root cause:** point-estimate sizing; Chopra-Ziemba's result that mean errors do about 11x the damage of variance errors.
- **Options:**
  - (a) Edge as a gate, breadth as the amount (X0-04). The range decides in or out; the risk budget and effective bets decide how much. Trade-off: a thin record has an undefined lower bound, so a new unit waits (A14's "too safe").
  - (b) Shrunk Kelly with a floor share: Kelly x t-squared over one plus t-squared, never below a minimum share of the cell's budget. Trade-off: the floor share is a number without a derivation yet; it leans on the edge a little.
  - (c) The hierarchy decides who gets risk (HRP on P&L clusters) and a capped fractional Kelly sets only the total (A5-025). Trade-off: needs enough units for clustering to mean anything; on two units it collapses to (a).

### P3. How frequency shapes the brakes, per level (C31, C33, A28)
- **Refined:** a count brake fires on healthy days by chance as trades pile up; he wants a sweet spot per level and brakes that count fast-invalidation cuts.
- **Root cause:** the old breaker counted full stops in a UTC day with no scaling and no cut sizes.
- **Options:**
  - (a) A money quantile per level with its own k (X0-16): the unit at its 1st percentile day, the book at its own, the BMS at the buffer. Trade-off: before a record exists the quantile comes from the card by simulation; no money brake is yet simulated on QMX streams.
  - (b) Loss points (a full stop 1, a cut its size, a scratch its cost) in a rolling window scaled to trade count. Trade-off: trade rows must tell a cut from a time exit (they cannot today, G11); the window width needs a derivation.
  - (c) Keep count brakes only for units under about 3 trades a day (ORB families), money brakes above. Trade-off: two shapes at one level; the boundary is a choice.

### P4. Stop versus fast invalidation, per style (A10, A28, M15)
- **Refined:** which exit protects the trade, and whether the old dynamic SL/TP (breakeven at +1R, take-profit extends) returns for intraday.
- **Root cause:** stops help only under momentum and hurt under mean reversion (Kaminski-Lo); the old rule applied one shape to every logic.
- **Options:**
  - (a) By style name, as he remembers it: FI for scalpers, dynamic SL/TP for intraday, thesis stops for swing. Trade-off: a mean-reverting intraday unit gets a breakeven move that counts missed rebounds.
  - (b) By a stopping-premium test per unit on its own paths (X0-24, X0-32), with the breakeven move allowed only when the trigger changes the forecast. Trade-off: needs MAE and MFE paths per trade (built in the journal) and a two-arm test before any rule ships.
  - (c) Both: the style sets the default, the test may override after the two-arm test. Trade-off: a default that the test later flips is a counted try against the unit's record.

### P5. Finding sniping windows (D8)
- **Refined:** the term has no professional meaning; the honest form is a slice where a unit's net edge in R is higher out of sample.
- **Root cause:** retail windows are clock stories; the edge, if any, is a cost effect.
- **Options:**
  - (a) Deterministic: slices from the two hourly tables where cost is low and activity high, proven per unit on later data (X0-47). Trade-off: misses windows that are about flow (fixes, closes), not cost.
  - (b) Agent-proposed candidates (sessions, fixes, releases, deep hours) proven by QMB with planned interim looks, each a counted try, artifacts in the Library. Trade-off: many slices tested inflate false windows unless the count is honest.
  - (c) Both, with the deterministic slice as the prior and the agent's as the alternative hypothesis. Trade-off: two sources of tries to count.

### P6. Which classes may trade at a given budget (D17)
- **Options:**
  - (a) The feasibility verdict gates live (X0-45): simulate-only until feasible. Trade-off: he sees classes he cannot trade yet; "too safe" by appearance.
  - (b) Raise the class's share until its minimum position fits. Trade-off: concentrates the book in the class with the coarsest lots, which is the opposite of breadth.
  - (c) Simulate-only sleeves earn a record on paper so that, when the budget grows, the class enters with evidence. Trade-off: paper costs are kinder, so the record is optimistic (X0-53).

### P7. The day for a class that never closes (crypto)
- **Options:**
  - (a) UTC midnight as the declared day. Simple; the money brake and the cushion ledger reset at a known minute. Trade-off: arbitrary against the venue's own cycle.
  - (b) A rolling 24-hour window for the money brake and the day ledger. Trade-off: no clean reset; the day-boundary exploit (A3-219) is replaced by a sliding one.
  - (c) The funding cycle as the day (three 8-hour periods, or one 24-hour period anchored at a funding minute). Trade-off: venue-specific; Hyperliquid's cycle differs from Binance's.

### P8. A bad day or a broken edge (A25)
- **Refined:** live results drift from the backtest; he wants size down slowly, never pulling out on one day, and a workflow that tells the two apart.
- **Root cause:** proof costs trades (55 percent at 1:1 needs about 610); a day holds too few.
- **Options:**
  - (a) Three signals apart (X0-08): only the slow decay signal may say the edge is gone; a bad day is caught by the money signal and nothing else happens. Trade-off: a dead unit keeps a reduced size for weeks before suspension.
  - (b) Input-first drift checks before any edge verdict: costs, fills, trade rate, holding time, replay match against the frozen card; a unit whose inputs drifted is fixed, not demoted (A2-166, A2-174). Trade-off: needs the cost ledger and the paper twin to exist.
  - (c) A paper twin and a random-entry control twin beside every live unit (A2-178): the live-minus-paper gap is fills; the paper-minus-control gap is edge. Trade-off: three runs per unit; the twins' fills are kinder.

### P9. Costs reaching the sizer (G7 4.3)
- **Refined:** no planned socket input carries a cost to the sizer; commission has no record key.
- **Options:**
  - (a) The hourly cost table lives on the instrument record and the sizer slot's contract gains a cost input (X0-37; an X1 change). Trade-off: the slot contract changes, which is a new version of every unit.
  - (b) The sizer stays four-input; the node's guard applies the cost cell as a multiplier after the sizer. Trade-off: the cost is hidden from the receipt, which is exactly what G7 warns about.
  - (c) QMB's cost ports feed a per-world calibration that the compiled unit embeds at compile time. Trade-off: a compiled cost goes stale between compiles.

### P10. Streak brakes for low win-rate families (ORB)
- **Options:**
  - (a) The streak threshold at the family's own 1st percentile run length (a 30 percent unit expects runs of 8-10). Trade-off: a long run before the brake acts.
  - (b) A money brake per family (X0-16's shape at the methodology level). Trade-off: a family of five opens can lose five full stops in one day inside its quantile.
  - (c) The hours clause so correlated opens are one event (X0-10) plus (a). Trade-off: the window width needs a derivation.

### P11. Macro multipliers with no evidence (X0-06)
- **Options:**
  - (a) Shadow mode, then cut-only live. Trade-off: raises never pay until a walk-forward exists.
  - (b) Informational only, forever: the state is shown; nothing moves. Trade-off: the sitting duck on a known risk-off day.
  - (c) Live with his click per state change (an applier mode). Trade-off: he is in the loop at 02:00.

### P12. Caution-window widths never derived (X0-30)
- **Options:**
  - (a) Derive in event time against matched baselines per instrument. Trade-off: needs weeks of quotes per instrument before the first number.
  - (b) Fixed defaults per class from the research windows (A3-019) until measured. Trade-off: clock windows break at DST twice a year.
  - (c) No caution windows; the execution-fit gate (X0-18) decides per tick. Trade-off: the gate cannot see the fix coming; it only sees the spread after it widened.

## 4. Collisions (named, not resolved)

1. **X0-02 against C29 and the lead.** His words read as a plain 1/N split; the lead's table gave each unit its full size; X0-02 gives each about 0.32 of the budget with ten independent units.
2. **X0-04 against the 1 Nov answer.** "Twice the edge, twice the size" is the rule X0-04 refuses; he refused it too (A24), but the lead's "starting size comes from QMB's evidence" got no reaction.
3. **X0-16 against A6 and A26.** He wants a brake "at about three" for a mean-reverting scalper and the circuit breaker as baseline; X0-16 retires any count for high-frequency units.
4. **X0-49 against A5.** "One template per unit type" against style as a dial. The matrix (X0-44) can hold either; the dial is wild.
5. **X0-26 and X0-46 against A3-184.** Placement needs the MIS to widen a unit's scope; the plan only lets the MIS narrow, and widening is a new version plus his click (G7).
6. **X0-05 against C19.** "Brakes first, accelerators second" against one rule that is both, with the anchor deciding.
7. **X0-24 against M15.** His memory is a stop moved by how far the trade is winning; X0-24 moves it only when the forecast changes.
8. **X0-25 against X0-10.** ORB breadth counts opens; the hours clause counts a risk-off day as one event across them. Both are right; the budget split reads the first, the brakes the second.
9. **X0-13 against B9.** R fixed at entry is not accepted by him; X0-13 keeps 1R fixed and lets the realised loss vary through the cut.
10. **X0-30 against UB-18.** A fix caution window blocks a fix-reversal unit.
11. **X0-40 against X0-54.** Scaling the day budget by breadth shrinks crypto's weekend; crypto as the spine wants to carry the book.
12. **X0-14 against A14.** The admission gate's lower bound is undefined for a thin record, so a new scalper waits: "too safe" in another form.
13. **X0-41 against X1's class codes.** X1's bucket list and this one differ (energy split into crude, products, gas here).
14. **X0-28 against B13.** A three-level daily ladder is exactly the set he called circumstantial and would not agree to.
15. **X0-09 against C13.** A pilot tier at 10-25 percent is "one working unit cut to $20" in another form; the fast early climb is the answer, not a resolution.
16. **X0-37 against the shipped sizer.** Four inputs, no cost; the table needs a contract change (P9).

## 5. Restructure proposals

- **R1. The Book becomes a risk-share sleeve, not a dollar pot.** Replace "Book = a style's seed capital with a runway over periods" (A1-041) by "sleeve = a share of the day risk budget and of the stress-loss cap, carrying three numbers (X0-01)". The name stays. Why it performs better: budgets compare across classes, so risk moves to where it pays; the GitBook ladder's fixed-dollar accelerator (A1-042) survives as the cushion ledger with a declared anchor (X0-05). The BMS keeps the parent limit below the sum (X0-10). [judgment]
- **R2. Count breakers become money breakers.** Replace the April two-strike circuit breaker (A2-083) by the money quantile with loss points (X0-16); keep the name, the bench, and the fire density as decay evidence. Why: a count at scalper rates is a tax on the frequency that is the system's edge; the quantile fires 1-3 percent of days at any rate. The count survives as a derived default for units under about 3 trades a day.
- **R3. Session multipliers become two hourly tables.** Replace the old session multiplier and premium-window flag (A3-037, A3-034) by the per-instrument-hour volatility and cost tables (X0-37) with overrides keyed by a reading word (X0-48). Why: the open is not the overlap; busy can mean deep, wide, fast or all three; a clock multiplier charges gold for MNQ's hours.
- **R4. News becomes data.** Replace the colour-level calendar and the kill-switch's news job (A3-125, A2-100) by measured impact per release and instrument with driver tags (X0-39). The kill switch keeps the hard kill; the news window is a node schedule derived from measurement. Why: narrower windows, more trading minutes, and instruments the currency map never covered.
- **R5. The style x class cell is the unit of defaults.** Replace "one template per unit type" as the top-level shape by the override chain keyed on cells (X0-44), with types as presets. Why: a new class or style is a row or a column, not a template; pooling across the class gives thin instruments a number with a reason. The holding-horizon dial (X0-49) is the wild form.
- **R6. (Flagged for the MIS, not designed.)** Placement needs a widen door; activity sessions for crypto; persistence readings as placement inputs (X0-21, X0-26, X0-46). The MIS is being built by another session; these are inputs to it.

## 6. Gaps: what no component covers

1. No component or paper tests an energy scalper, or any energy sizing rule.
2. No paper on fast invalidation; the cut size comes only from a unit's own paths.
3. Pooling parameters across instruments is unbacked by any held-out trading result.
4. No study measures whether house money pays; only that professionals do it.
5. No generation derived a caution-window width; the derivation in X0-30 is proposed, not run.
6. No swing-specific brake window in trades; a swing unit may take a year to show decay.
7. Nothing covers a unit that crosses a style boundary by failing to exit (X0-49 is the only answer and it is wild).
8. Stock borrow, recalls and short-sale rules at a small account are thin.
9. The jurisdiction that binds his account's leverage caps is unknown here.
10. No money brake has been simulated on QMX's own trade streams; R9's figures are synthetic.
11. The hours-clause window width has no derivation.
12. Hyperliquid's own activity cycle is unmeasured; every crypto number is from Binance-style venues.

## 7. The roundtable (party mode, session mode, non-interactive)

Five voices. 🛡️ **Marguerite**, pod-shop risk manager. ⚡ **Dez**, retail scalper, FX and crypto, runs 30-60 trades a day. 🏗️ **Ada**, platform engineer. 🌾 **Tomas**, futures and swing trader, holds for weeks. 🎙️ **The operator's voice**, his own words only, from the seeds. Topic: the five strongest hybrids under stress. Three rounds, then a close.

**Round 1: the day split (X0-02).**

🎙️ **The operator's voice:** "if we get the total amount of capital to be spent in a day, yeah, and then, you know, we split it across the total number of units."

⚡ **Dez:** Split it how? If you give me a tenth of the day because there are ten of us, I'm trading micro lots on a pair where my cost is already a sixth of my stop. I'll make nothing and you'll call me a sitting duck.

🛡️ **Marguerite:** You get a third, not a tenth, if your trades are independent of the other nine. That is the whole point of the square root. But I decide what independent means, and I measure it from the exposure ledger, not from your word.

🌾 **Tomas:** And on the day the dollar moves, my four futures and her six FX pairs are one bet. Your square root says ten. The ledger says two.

🛡️ **Marguerite:** Which is why the parent limit sits below the sum. The square root sets the shares; the co-loss count sets the ceiling. They are not the same number and I will not let anyone merge them.

🏗️ **Ada:** Then rho is two numbers on the row: one from results, slow, one from exposure overlap, fast. The smaller wins. I can build that. I cannot build "independent" as a feeling.

**Round 2: the brake (X0-16).**

🎙️ **The operator's voice:** "at three losses, or if we can sort of figure out a pattern in between, we get it from six to around three or two."

⚡ **Dez:** Three losses in a row happens to me before lunch on a good day. If three benches me, you have built a machine that stops the thing that works.

🛡️ **Marguerite:** In my shop nobody counts trades. We count money from a line. Your line is your own first percentile day; cross it and you are flat. You get to lose ten R on a forty-trade day and nobody blinks, because that is your day.

🌾 **Tomas:** My first percentile day is one trade. A money line does nothing for me for a month. Count my losses, please; I have three a quarter.

🏗️ **Ada:** So the brake's signal is a field, and the field's value depends on the trade rate. Under three a day, a count. Over it, the quantile. The row says which and why.

🎙️ **The operator's voice:** "breaks, remember, also take into account, or I meant to take into account, first invalidation."

⚡ **Dez:** Then a cut costs a third of a point and a full stop costs one. Fine. But your trade rows can't tell my cut from my time exit today. Fix the row before you fix the brake.

🏗️ **Ada:** Noted. That is an X6 change and it is cheap.

**Round 3: the matrix (X0-44) and the dial (X0-49).**

🎙️ **The operator's voice:** "one template by any type. I want any type is the right way, but... I think things might change, yeah."

🏗️ **Ada:** Types are presets over cells. The cell is style by class. A new class is a column. If you make the style a number, a holding horizon, even the row is a value and nothing is ever renamed.

🌾 **Tomas:** A number cannot tell a breakout from a mean reversion at the same horizon. I hold both for a week. One wants a trailing stop. The other wants a time exit. Your dial gives them the same defaults.

🛡️ **Marguerite:** Which is why the stop policy comes from a test on the unit's own paths, not from the dial. The dial sets the window; the test sets the exit.

⚡ **Dez:** I don't care what you call it. I care that when I drift from five minutes to five hours because a trade went wrong, something notices. The dial notices. The type does not.

🏗️ **Ada:** That is the one thing the dial buys that the type cannot. It is also the one thing nobody has built.

**The fight: the admission gate (X0-14) against "too safe".**

🎙️ **The operator's voice:** "it seems like it's too safe... Then what is the point of designing a unit that self-configures?"

🛡️ **Marguerite:** The gate is not safety. It is arithmetic. If your edge's lower bound is below twice your cost, you are paying the broker to find out you were wrong. Breadth multiplies that.

⚡ **Dez:** And if my record is thin the bound is undefined, so I never start. You have made a gate that opens only for units that already proved themselves somewhere else.

🌾 **Tomas:** So start him at the pilot tier on paper with the real cost table, and count it. The gate reads the paper record. It opens in days for a real edge.

🛡️ **Marguerite:** With demo fills. Which are kinder.

🏗️ **Ada:** Per-world calibration. The demo record opens the demo gate. The live gate opens at the pilot tier on live fills. Nobody skips a world.

**Close.** The room did not agree. It produced: rho as two fields with the smaller winning (X0-02, X0-11); the brake signal as a field that depends on trade rate (X0-16, P3); trade rows that tell a cut from a time exit as a cheap X6 change; the stop policy from a test, not from the dial (X0-24, X0-32); the dial's one real gift, noticing style drift (X0-49); the gate opened per world at the pilot tier (X0-14, X0-53, X0-09). Two questions for him (Q1, Q2 below).

## 8. Questions only he can answer

1. **Q1.** Is "one template per unit type" the shape, or may types be presets over style x class cells (X0-44), with the holding-horizon dial (X0-49) as a later form?
2. **Q2.** Which entity and jurisdiction hold his cTrader account? The leverage caps (X0-45) and so the feasibility verdict per class depend on it.
3. **Q3.** Does "ORB never holds overnight" extend to every intraday unit as a hard clamp (flat by deadline, X0-27), or may an intraday unit be allowed to carry with a gap allowance?

## 9. Index of hybrids

| Id | Name | Group | Maturity |
|---|---|---|---|
| X0-01 | One loss currency, three numbers per sleeve | Portfolio | solid |
| X0-02 | Day risk budget split by effective bets | Portfolio | solid |
| X0-03 | Style sleeves as risk-budget shares | Portfolio | plausible |
| X0-04 | Edge as a gate, breadth as the amount | Portfolio | solid |
| X0-05 | One cushion ledger per level with a declared anchor | Portfolio | solid |
| X0-06 | Macro as a slow governor, fast layer decides usable now | Portfolio | plausible |
| X0-07 | Isolation by underlying process with two tells | Portfolio | plausible |
| X0-08 | Three signals kept apart | Portfolio | solid |
| X0-09 | Staged ramp, unit and book both qualify | Portfolio | plausible |
| X0-10 | Co-loss accounting: hours clause, parent limit on co-loss | Portfolio | plausible |
| X0-11 | The exposure ledger | Portfolio | solid |
| X0-12 | Venue capacity probe on every accelerator | Portfolio | wild |
| X0-13 | Scalper risk unit: R after costs, cut inside, two ledgers | Scalping | solid / plausible |
| X0-14 | Admission gate: edge lower bound against stressed cost | Scalping | solid / plausible |
| X0-15 | Scalper stop: FI cut, disaster clamp, safest exit wins | Scalping | plausible |
| X0-16 | Scalper brakes that scale with frequency | Scalping | solid |
| X0-17 | Scalper size bound with costs in the denominator | Scalping | solid |
| X0-18 | Execution-fit gate and markout | Scalping | plausible |
| X0-19 | Scalper accelerators: cushion, window, dose steps | Scalping | plausible |
| X0-20 | Negative-skew scalpers sized on tail loss | Scalping | plausible |
| X0-21 | Tick rate as the volume proxy; activity sessions | Scalping | plausible |
| X0-22 | Sub-minute maker scalper with a dilemma brake | Scalping | wild |
| X0-23 | Intraday risk unit with the hold's volatility forecast | Intraday | solid |
| X0-24 | Intraday stop: risk-state invalidation, breakeven on forecast change | Intraday | plausible |
| X0-25 | ORB as a family: breadth through opens | Intraday | plausible |
| X0-26 | Intraday mean reversion placed by persistence readings | Intraday | plausible |
| X0-27 | Flat by deadline, cash and overnight apart, day boundary | Intraday | solid |
| X0-28 | Daily loss ladders at three levels as capital breakers | Intraday | plausible |
| X0-29 | Intraday accelerators: tier ladder, persistence press | Intraday | plausible |
| X0-30 | Session-open, hand-over and fix caution windows | Intraday | plausible |
| X0-31 | Swing risk unit: capped vol target plus gap allowance | Swing | solid |
| X0-32 | Swing stop: thesis reversal, disaster clamp | Swing | plausible |
| X0-33 | Swing costs: carry, swap, funding, roll | Swing | solid / plausible |
| X0-34 | Swing brakes: edge fell not equity fell, drawdown ladders, regime | Swing | plausible |
| X0-35 | Swing accelerators: pyramiding, calm scaling with guard | Swing | plausible |
| X0-36 | Swing breadth across classes; limits by tick-size tier | Swing | plausible |
| X0-37 | Two per-instrument-hour tables | Microstructure | solid |
| X0-38 | The venue rule | Microstructure | solid / plausible |
| X0-39 | News as measured impact with driver tags | Microstructure | plausible |
| X0-40 | Day budget scaled by open breadth | Microstructure | plausible |
| X0-41 | Factor buckets with a residual, two-layer caps | Macro | solid |
| X0-42 | Regimes: filtered, per class, cut gross | Macro | solid / plausible |
| X0-43 | Risk-off two-layer tell stack | Macro | plausible |
| X0-44 | The style x class cell as the unit of defaults | Cross-cutting | solid / plausible |
| X0-45 | Per-class feasibility map | Cross-cutting | solid |
| X0-46 | Placement score, costs normalised, edge shrunk | Cross-cutting | plausible |
| X0-47 | Sniping windows as counted slices | Cross-cutting | solid / plausible |
| X0-48 | Contexts not sessions | Cross-cutting | plausible |
| X0-49 | Style as a dial | Cross-cutting | wild |
| X0-50 | The dry chassis per cell | Cross-cutting | wild |
| X0-51 | Multi-position units | Cross-cutting | plausible |
| X0-52 | Cost-of-conservatism meter | Cross-cutting | wild |
| X0-53 | World switch resets | Cross-cutting | solid |
| X0-54 | Crypto as the 24/7 spine | Cross-cutting | wild |
| X0-55 | Energy and stocks as data overlays | Cross-cutting | plausible |

Counts: solid 15, solid-leaning (split tags, solid for the mechanism and plausible for a part) 7, plausible 27, wild 6. Total 55.
