# X2: sizing, allocation, accelerators and costs (Stage B, linking)

File id `X2-sizing-accelerators`. Written 2026-11-03 under `linking/STAGE-B-BRIEF.md`. Expansion, not a design: it widens and does not rank. The Fable funnel judge ranks (`linking/RANKING.md`). Ledger additions: `ledger/additions/X2-sizing-accelerators.yaml`.

**How to read.**
- Each hybrid has an id `X2-Hnn`, the components it links (short ids: `A1-036` means `A1-sizing-allocation-036`; A2 to A5 the same way), the need it serves, what it does and how, its levels, its behaviour per class and style, the ledger ids it touches (new ids in *italics*), a performance note, a survival note, its evidence chain with the weakest link named, and a maturity tag: **solid** (all parts exist or are specified and the evidence is live or controlled), **plausible** (parts exist, the combination is new), **wild** (kept for the funnel; may break a ruling or rest on an analogue only).
- **[judgment]** marks my opinion. **[arithmetic]** marks numbers from my own script, `linking/stage-b/X2-sizing-accelerators/sims/horizon_sizer.py` (outputs `out-1000.txt` and `out-1000-gaps.txt` beside it). Those are model numbers, not evidence about real strategies.
- Method trail in `linking/stage-b/X2-sizing-accelerators/`: `.memlog.md` (the headless brainstorm: Morphological Analysis, Concept Blending, Forced Relationships, Cross-Pollination, Trait Transfer, Evolutionary Pressure, Solution Matrix; 101 ideas), `problem-solving.md` (diagnosis for PS1-PS17), `roundtable.md` (party mode), `brainstorm-intent.md`.
- Brake, accelerator, restore and clamp follow R9 §0.2. Section 0.2 below adds two kinds.

**Counts.** 62 hybrids: 15 solid, 35 plausible, 12 wild. 17 problems with options. 25 collisions. 8 restructure proposals. 73 new ledger variables (five more ideas reuse ids X0 and X1 already defined).

---

## 0. Ground

### 0.1 Needs this layer serves

Every hybrid names one or more of these. Sources are SEEDS item ids and the ledger v0 holes (STATE item 23).

| Need | What the template must do | From |
|---|---|---|
| N01 | Give every trade a baseline amount with a derivation, never blank, changeable in *how* it derives | A2, A13, D29, D46; ledger hole "risk per trade has no derivation" |
| N02 | Not lean on a point edge; read the edge as a range; let a weak edge still pay | A24, A14, A16 |
| N03 | Express frequency and breadth: his day budget split across units against full size per unit | C29, C1, C13, A18, D11 |
| N04 | Feed costs per market, instrument, timeframe, hour and world into size | A11, D17, D13; ledger hole "costs never reach the sizer" |
| N05 | Split risk across many units with correlation; parent below the sum; one bet counted once | B1, C18, A8, C27 |
| N06 | Accelerators that perform: house money, reverse house money, tiers, restores, under R9's definitions | A21, C19, C5, M39 |
| N07 | Pair accelerators with brakes so a raise never drives into a trip | C19, R9 §3.4 |
| N08 | Declare realised against marked equity for every sizing and brake row | B15; ledger hole "no money brake says which equity" |
| N09 | Handle minimum lots, lot steps, margin and leverage caps at small equity | A17, D16, C2 |
| N10 | Normalise risk across FX, indices, metals, energy, crypto, futures, stocks | A17, D16, D51, M26 |
| N11 | Size demo and live identically; only the account differs | D13, D15, A22 |
| N12 | Self-configure each number with a learner, an applier and guards; let him swap the derivation | A3, D31, D46, R7 |
| N13 | Ramp new and returning units without the sitting duck | A14, A15, A1-055 |
| N14 | Grow across 24 hours: compounding, anchors, sweeps, next-day restart | C15, C12, B5, B10, C22 |
| N15 | Put fast-invalidation cut sizes into every size number | A9, A28 |
| N16 | Size down slowly on edge drift, fast on money loss | A25, C19 |
| N17 | Let a unit hold several positions without stacking one bet | A8, T5 |
| N18 | Let the Lab, MCP agents and the future agent department use the template outside the order path | M35, M36, D42 |
| N19 | Treat idle capital and too-safe sizing as costs (the sitting duck) | M33, C11, A14 |
| N20 | Bound gap, halt and tail losses per class | C10, C27 |

### 0.2 Definitions used, and two extensions

R9's definitions hold: a **brake** holds risk at or below a declared **baseline** on evidence of danger; an **accelerator** raises it above baseline on evidence of opportunity or proof; a **restore** is a brake's way back to baseline, never above it; a **clamp** is a fixed bound. Compounding on the current budget is part of the baseline.

Two extensions this layer needs **[judgment]**:
- **Probation brake.** A new or returning unit trades below its derived baseline until evidence releases it. Its release path is a restore. So the level ladders (BOIN, titration, staged ramps) are brakes with restores, not accelerators. Only steps *above* the derived baseline are accelerators (tiers, persistence press, pyramiding, calm-volatility boost, cushion leverage on a fixed anchor).
- **Borrowing.** A unit uses budget another unit leaves idle, under a priority class, and gives it back on demand (Kubernetes burstable resources). It is neither a brake nor an accelerator of the lender; for the borrower it is a capped accelerator funded by slack, and any brake recalls it.

### 0.3 The central finding, in one paragraph

[judgment, with arithmetic] A per-trade risk can be derived from survival alone, with no edge input: risk = cushion ÷ (s × z × √(H × book-swing factor)), where the cushion is equity above his floor, s is the spread of trade results in R (fast-invalidation cuts make it smaller), z comes from his allowed chance of touching the floor, H is the number of trades the guarantee must hold for, and the book-swing factor counts how many units trade and how much they move together. The edge then only *relaxes* this size as evidence grows. In my sim ($500, $300 floor, 60 days, 10 trades a day, FI cuts on half of losers), this sizer touched the floor in none of 1,000 paths in all twelve cases (one or ten units, correlation 0 or 0.3, believed, half or zero edge), with and without shared 3R gap days; fixed 1 % per unit touched 18.7 % (30.7 % with gaps) with ten correlated units at half the edge, and half Kelly up to 100 %. With ten correlated units at the believed edge it grew a median $2,213 against $796 for his literal 1/N split at the same zero touch rate. It is the GitBook ladder with a derived multiplier: the Book's $42.86 per R on a $200 runway priced one R at 1/7 of the cushion, which equals surviving about 7 to 10 trades at zero edge with 99 % confidence. Details in Appendix A.

---

## 1. Hybrids

### A. The baseline amount and the sizing bases

**X2-H01. Horizon floor-odds sizer (safe at zero edge; the edge only relaxes it).**
- Links: A1-036 (floor-touch bound), A1-024 (risk-constrained Kelly), A1-087 (three answers for N units), A1-105 (N_eff), A1-032 (edge as a range), A5-118 (cushion rule), A1-038 (pathwise invariance), A3-028 (worst-step table), A1-129 (stressed correlation), A4-001 (learner publishes bounds).
- Need: N01, N02, N03, N15, N19.
- What and how: Per-trade risk r is the largest value for which a Brownian estimate of P(book touches the floor within H rounds) stays at or under ε. At zero drift this has a closed form: r = D ÷ (s × z × √H × B), with D the usable cushion (equity above the floor, minus the H07 reserve), s the unit's result spread in R (with FI cuts), z = Φ⁻¹(1 − ε/2), and B = √(N × (1 + (N − 1) × ρ)) the book-swing factor for N units at correlation ρ. So each of N units gets 1/√(N(1 + (N − 1)ρ)) of the one-unit size: about a third each for ten independent units, about a sixth at ρ = 0.3. Example: D $200, ε 1 % (z 2.58), H 200 rounds, s 0.87 gives $6.3 a trade for one unit (1.3 % of $500); ten units at ρ 0.3 get about $1.0 each. With drift (the edge point from H03) the touch formula with drift is solved by bisection. Computed at each anchor (H12), cached; a stale cache falls back to the zero-edge closed form, which needs no edge input (roundtable, Priya). The receipt names D, s, ε, H, ρ used, the edge point and the resulting r in dollars and as a share of equity.
- Levels: unit (its own r); book and BMS (they own D, ε, ρ and the unit count).
- Per class and style: class-neutral in money at the stop once value per point is right (H47). Gappy classes (crypto weekends, index CFDs over weekends, energy releases, single stocks) need the H07 reserve, because the formula ignores jumps. Scalpers (high H per day) get small per-trade risk and high counts; ORB and swing get larger per-trade risk at the same daily swing (H02).
- Ledger: `floor_touch_size_bound`, `floor_touch_tolerance`, `loss_runway`, `result_spread_r`, `effective_independent_bets`, `unit_result_correlation`, `portfolio_floor`, `risk_fraction`; new *survival_horizon_rounds*, *horizon_survival_risk_usd*, *planning_edge_point*, *stressed_unit_correlation*.
- Performance: trades from day one at a size that rises with the cushion (a fixed floor makes it cushion leverage, R9's accelerator by anchor); 2.8x the 1/N split's median at equal safety in the sim. Survival: zero floor touches in all twelve sim cases, including shared −3R gap days.
- Evidence chain: first-passage maths (textbook) → Grossman-Zhou and Hsieh cushion results (R9 §0.4, READ) → my sim [arithmetic]. Weakest link: the Brownian approximation with fat tails and serially correlated results; H and ρ are choices.
- Maturity: **plausible**.

**X2-H02. Day-sigma budget: per-trade risk falls with the square root of the trade rate.**
- Links: A1-105 (fundamental law), A1-088 (his day-capital split), A1-087, A5-144 (money brake at the unit's own day percentile), A3-114 (open breadth), A5-003 (breadth spreads a fixed total).
- Need: N03, N01, N15.
- What and how: The book's allowed daily swing is σ_book = D ÷ (z × √(days in H)). It is split across units by the same correlation formula as H01. A unit's per-trade risk is r = σ_unit ÷ (s × √n), n its trades per day. So a 40-trades-a-day scalper risks half per trade what a 10-trades-a-day one does, and a 2-trades-a-day ORB unit more than twice. Expected daily gain = edge × n × r = edge × √n × σ_unit ÷ s: it grows with the square root of frequency, which is his "risk less, but do it so many times" as a formula, with the square root as the honest price of it. The unit's day money brake reads the same σ_unit (A5-144), so sizer and brake share one number. Example: D $200, ε 1 %, 20 days → σ_book ≈ $17.4 a day; one unit at 10 trades, s 0.87 → $6.3 a trade; at 2 trades → $14.1; at 40 → $3.2.
- Levels: BMS sets σ_book; book splits; unit converts to per-trade risk.
- Per class and style: n is per unit, so a scalper and an ORB unit on the same class get different per-trade sizes at the same daily swing. Crypto (24/7) counts its own day; FX weekends shrink the open book (H36).
- Ledger: `portfolio_daily_risk_budget`, `trade_rate`, `result_spread_r`, `unit_daily_loss_limit`; new *book_day_sigma_budget_usd*, *unit_day_sigma_budget_usd*.
- Performance: frequency becomes growth at a fixed daily swing; nothing idles. Survival: the daily brake and the size cannot disagree, because both read σ_unit.
- Evidence chain: fundamental law (A1-105, idea level), R9 frequency-scaled brake sims [arithmetic, R9 §4.1] → H01 maths. Weakest link: trade rate is variable day to day; n must be the unit's measured rate, refreshed at anchors.
- Maturity: **plausible**.

**X2-H03. The edge dial on a deflated, shrunk range (gate plus drift).**
- Links: A1-032 (edge as a range), A1-031 (edge as gate), A2-187 (plan at deflated holdout), A1-028 (family prior), A5-098 (empirical-Bayes family shrink), A1-027 (post-selection shrink), A1-019 (t-shrink), A4-196.
- Need: N02, N13, N12.
- What and how: The unit's edge is a band (low, mid, high) built from the deflated QMB holdout, shrunk toward its family prior and corrected for the number of tries, then updated by live trades. The band does two jobs only. (1) Gate: the low end after costs must be above zero for the unit to trade live (paper below that). (2) Drift: H01 uses one declared point of the band as drift: `zero` (default for new units), `low`, or `mid`. Moving the point is a profile version or his click, never automatic. Kelly never sets the amount (H04 caps it).
- Levels: unit; family prior at methodology level.
- Per class and style: crypto and new stocks get wide bands (thin history); FX and index units pool with their family. Scalpers narrow their band fastest (many trades).
- Ledger: `edge_range`, `edge_t_statistic`, `effective_tries`, `judge_market_shrink_k`, `kelly_shrink_factor`; new *planning_edge_point*.
- Performance: zero → low lifted the sim median from $2,213 to $5,854 (ten units, believed edge) at zero touches. Survival: a wrong edge cannot raise size above the zero-edge number unless the dial was moved on evidence.
- Evidence chain: post-selection and family shrinkage simulations (A1-027, A1-028) → anomaly decay meta-studies (A2-187) → sim. Weakest link: the family prior's choice.
- Maturity: **plausible**.

**X2-H04. Cost-and-gap Kelly as a ceiling, with an evidence-relaxed shrink.**
- Links: A5-084 (Kelly at the stop with costs and gap factor), A1-019, A1-030 (Kelly as a ceiling), A1-017, A5-016 (ridge Kelly), A1-018.
- Need: N04, N02, N06 (evidence-relaxed shrinkage is an accelerator kind in R9).
- What and how: f* = [p(b − c) − (1 − p)(g + c)] ÷ [(b − c)(g + c)] in R at the stop, with c the round-trip cost in R for this hour and g the average stop fill as a multiple of 1R after gaps and slippage; for three-outcome units (wins, FI cuts, full stops) the general Kelly on the measured distribution. Multiply by t² ÷ (1 + t²) on the deflated edge. The result caps H01's r; it never raises it. So a thin, costly edge is cut, and as evidence grows the cap relaxes (0.43 at 300 trades, 0.88 at 3,000 for a +0.05R edge, R2 §4.4).
- Levels: unit.
- Per class and style: c in R grows as the stop shrinks, so tight-stop scalpers on wide-spread CFDs and taker-fee crypto hit the cap first; g is near 1 for FX majors in liquid hours, well above 1 for energy at inventory releases and index futures at the open.
- Ledger: `kelly_fraction_raw`, `kelly_shrink_factor`, `round_trip_cost_r`, `win_rate`, `average_win_r`, `mean_loss_r`, `gap_loss_beyond_stop`, `fast_invalidation_cut_r`; new *stop_fill_gap_factor*, *cost_gap_kelly_ceiling*.
- Performance: binds only where the edge is weak or costs eat it, so it costs little elsewhere. Survival: stops a measured thin edge from being over-bet; 12 % against 17.5 % at c = 0.1R for p 0.45, b 2.
- Evidence chain: Kelly theory → cost algebra (A5-084, idea) → shrinkage (A1-019, idea). Weakest link: p and b estimation from short records.
- Maturity: **solid** (formula, no new seam beyond costs reaching the sizer).

**X2-H05. Risk-constrained Kelly from his floor (α, β), instead of half by habit.**
- Links: A1-024 (wealth-floor probability constraint), A1-136 (his floor and buffer), A1-171 (survival-first parameter choice), A5-013 (drawdown-constrained optimum), A1-018.
- Need: N01, N12.
- What and how: Choose the Kelly fraction so that P(wealth ever falls below α × start) < β, with α from his floor and β from his tolerance: one convex problem over the unit's scenario returns (A1-024). The answer replaces "half Kelly" with "the fraction that spends exactly your floor tolerance". Used as an alternative derivation block to H01 (his D46: swap how it derives), and as a cross-check: if the two disagree by more than a factor of two, the receipt flags it.
- Levels: unit, book.
- Per class and style: fat-tailed classes need tail scenarios in the set (crypto, energy, single stocks); FX majors are closest to the model.
- Ledger: `kelly_multiplier`, `floor_touch_tolerance` (β), `portfolio_floor` (α), `kill_line_floor`; no new id.
- Performance: spends the full survival allowance, no more. Survival: guarantee holds only under the scenario model.
- Evidence chain: Busseti-Ryu-Boyd style simulations (A1-024) → his floor words. Weakest link: scenario completeness.
- Maturity: **plausible**.

**X2-H06. Smallest-wins binding stack with the binding clamp named.**
- Links: A1-122 (many caps, smallest wins, each with a reason), A4-014 (priority combiner), A5-104 (clamp), A5-096 (regulatory leverage cap), A1-158 (margin), A5-148 (venue capacity), A1-123 (April chain, as the failure to avoid).
- Need: N01, N12, his volleyball rule (A13).
- What and how: Final size = min of: H01 baseline × level (H13) × at most one context modifier slot (A4-014 priority); H04 Kelly ceiling; H07 cushion clip; H08 tail budget; H24 raise permission; margin headroom; regulatory leverage cap; venue capacity cap; max lots. Every candidate carries a reason. The receipt names the binding one and records, per profile version, how often each binds. A cap that binds over 90 % of trades is flagged as dead weight (April's lesson: one cap bound always and the nine multipliers were inert).
- Levels: trade (applied), unit (stats).
- Per class and style: which cap binds differs by class: margin and regulatory caps on crypto CFDs (2:1), venue capacity on thin crypto venues and off-hours metals, Kelly on tight-stop scalpers.
- Ledger: `control_rank_table`, `context_size_modifier`, `max_position_size_lots`, `leverage`, `margin_used`; new *binding_size_constraint*.
- Performance: shows which cap is costing growth, so it can be re-derived. Survival: the most cautious answer always wins.
- Evidence chain: dash.js and April binding-clamp audit (live software; old QMX spec). Weakest link: none of its own; it is plumbing.
- Maturity: **solid**.

**X2-H07. Pathwise cushion clip with an N-1 and probable-maximum-loss reserve per class.**
- Links: A1-038 and A2-012 (pathwise drawdown invariance), A3-028 (worst-step table), A3-025 (gap allowance), A2-264 (halt allowance), A1-115 (bet key), A3-148 (exposure zones), A1-168 (joint-scenario ES), grid N-1 security (cross-pollination), reinsurance PML (roundtable, Ruth).
- Need: N20, N05, N01.
- What and how: Before any sizing, D_usable = D − max(N-1 reserve, PML reserve). N-1 reserve: the loss if the largest open bet key gaps to its class's worst one-step move. PML reserve: per exposure zone (USD, equity beta, crypto weekend, energy release), the loss on the worst credible event in the scenario table, summed across zones that the scenarios link. Then each new trade obeys the Hsieh clip: its worst-step loss plus costs ≤ D_usable × share. The worst moves come from X4's scenario table, never from recent volatility.
- Levels: book and BMS (reserve), trade (clip).
- Per class and style: FX majors small worst steps except the Sunday open; index CFDs and single stocks large over weekends and halts; crypto wicks all week; energy limit moves. Scalpers that never hold over a weekend carry no weekend term (Friday-flat rule, A3-025).
- Ledger: `gap_loss_beyond_stop`, `high_water_mark_equity`, `portfolio_floor`, `open_risk_at_stop`, `cluster_exposure_cap`; new *worst_step_move_r*, *largest_bet_contingency_usd*.
- Performance: a tight, honest worst-step table for liquid classes leaves more cushion to use. Survival: CPPI-shaped sizing fails only through gaps; this is the term that covers them.
- Evidence chain: Hsieh robust invariance, author backtest with proofs (A1-038) → grid N-1 and insurance PML practice (live in their fields). Weakest link: the worst-step table itself (X4).
- Maturity: **plausible**.

**X2-H08. Tail-budget sizing for negative-skew styles.**
- Links: A3-008 (size negative skew on tail loss), A2-250 (min of stop budget and tail budget), A5-084 (gap factor), A1-169 (calibrated tail limit), A3-155.
- Need: N20, N15.
- What and how: For units whose record is many small wins and rare large losses (high win rate, low payoff), size = min(stop budget, tail budget), the tail budget being the unit's 97.5 % expected shortfall per trade from its own record plus stressed slippage, resampled with gaps. Recomputed when the exit set changes, since FI and breakeven moves reshape the tail.
- Levels: unit.
- Per class and style: mean-reverting FX and index scalpers (fix and flash-crash tails), crypto mean reversion (wicks). Trend units rarely bind.
- Ledger: `mean_loss_r`, `payoff_ratio`, `win_rate`, `excursion_mae_mfe_r`, `slippage_cost`; new *tail_loss_budget_usd*.
- Performance: symmetric styles keep full size; only cliff-shaped ones shrink. Survival: bounds the one loss that erases many wins.
- Evidence chain: Landolfi-type simulations (A3-008), assistant design (A2-250). Weakest link: a short record has no tail in it; fall back to the class tail.
- Maturity: **plausible**.

**X2-H09. Holding-period risk for swing and position units (two knobs: stop width, then size).**
- Links: A1-011 (volatility target in account money), A3-016 (time-of-day volatility for the hold), A3-025 (gap allowance), A5-083 (stop from volatility × horizon factor; tightening never buys size), A1-148 (carry).
- Need: N10, N20, N04.
- What and how: For units without a tight price stop, or holding over sessions, the risk unit is the money swing over the planned hold (forecast volatility × √hold) plus the weekend or overnight gap allowance at a percentile, plus carry. The stop width comes from volatility × a horizon factor; size comes from the budget. Rule: tightening a stop to fit more size is refused unless H04's cost-aware ceiling still approves it.
- Levels: unit, trade.
- Per class and style: swing FX, gold and index holds; energy needs release-day allowances; crypto has no weekend close but thin weekend books.
- Ledger: `volatility_target`, `stop_distance`, `max_hold_time`, `swap_financing_cost`, `gap_loss_beyond_stop`; new *carry_cost_r*.
- Performance: swing keeps its overnight edge at an honest size. Survival: a gap costs at most planned R plus the allowance.
- Evidence chain: AQR-style volatility scaling practice (A1-011, idea), time-of-day models (A3-016, author backtest). Weakest link: gap percentiles from short histories.
- Maturity: **plausible**.

### B. The cushion pair and its anchors

**X2-H10. One-ledger cushion pair: house money and reverse house money as one rule.**
- Links: A5-118 (one rule), A5-116 (house money proper), A5-117 (reverse house money proper), A1-043 (April taper), A1-044 and A2-052 (sigmoid taper), A1-067 (share of winnings), A2-091 (loss points), A5-145 (money ledger), A5-144 (day percentile), A5-141 (budget-burn permit).
- Need: N06, N07, N15, N16.
- What and how: On one scope's money ledger, from one declared anchor, P = realised P&L since the anchor (an FI cut counts its size, a breakeven its cost), O = open risk at the stops. Multiplier m = (L + P − k × O) ÷ L, clipped to [m_min, m_max], with L the scope's loss allowance for the anchor period = z_L × σ_scope (H02), so it scales with frequency. Below the anchor m < 1 (reverse house money, the brake half); above it m > 1 is allowed only on realised profit, and the extra risk on open trades never exceeds a share s of that profit (house money, the accelerator half). Shapes offered: linear, the April quadratic taper, or the sigmoid with a cost safety factor. Anchor type: fixed (day or session start, a dollar floor) makes it a pair; trailing (running peak) makes it a pure brake. The brake half is on from day one; the accelerator half stays off until H20's proof card passes (roundtable).
- Levels: unit, book or BMS, one declared scope for the accelerator half (H11).
- Per class and style: high-frequency scalpers move the ledger many times a day, so their L must be frequency-scaled (H02) or house money fires by noise; swing units with one trade a day barely move it, so it does little for them (R9 §1.4).
- Ledger: `house_money_multiplier`, `house_money_winnings_share`, `house_money_scope`, `drawdown_pressure_multiplier`, `day_start_equity`, `loss_points_total`, `open_risk_at_stop`, `budget_remaining`; new *cushion_anchor_type*, *anchor_pnl_usd*, *cushion_multiplier_min*, *cushion_multiplier_max*.
- Performance: R9 script: equal to a constant on independent trades; +37 % and +42 % growth per unit of risk under regimes. Survival: a losing run cannot compound, because size falls in proportion to the allowance left.
- Evidence chain: Grossman-Zhou and Hsieh lemma (READ in R9) → R9 script [arithmetic] → old QMX spec. Weakest link: persistence in QMX's own units is unmeasured, so the accelerator half may only move risk around.
- Maturity: **plausible** (brake half **solid**).

**X2-H11. Book-level house money with an event window (one event counts once).**
- Links: A1-068 (event-windowed, book-capped house money), A3-195 (winning together), A1-067, A1-086 (parent limit), A2-026 (insurers' hours clause), A3-191 (losing together), H02.
- Need: N06, N05, N07.
- What and how: The accelerator half of H10 lives on the book (or BMS) ledger, not the unit's. Realised profit inside one event window (one shared driver: a USD release, a risk-off hour, a crypto weekend move) counts as one event; the book may add at most s × that event's profit to tomorrow's (or the next anchor's) σ_book, distributed by the H28 or H29 rule. No accelerator during a driver caution or an isolation. Five units paid by one USD move fund one extra allowance, not five.
- Levels: book, BMS.
- Per class and style: FX, gold and US indices share USD events; crypto has its own event clock; energy releases are events.
- Ledger: `house_money_scope`, `house_money_threshold`, `house_money_combined_cap`, `loss_event_window`, `portfolio_daily_risk_budget`.
- Performance: keeps the accelerator on independent profits. Survival: a correlated reversal after a correlated win costs no more than without house money.
- Evidence chain: reinsurance hours clauses (live practice, snippet in A2), X4 scenario reasoning. Weakest link: the event window's width.
- Maturity: **plausible**.

**X2-H12. Per-scope anchor clocks for 24-hour trading.**
- Links: A2-064 and A4-061 (confirmed, persisted day baseline), A4-059 (declared basis), A1-074 (session capital), A5-124 (no size rise mid-session), A3-114 (open breadth), A2-011 (counters that survive restarts).
- Need: N14, N08.
- What and how: Every scope declares its anchor clock: rolling 24 hours or session for scalpers, per open for ORB, UTC 00:00 or 22:00 New York for FX books, a declared UTC reset for crypto. At each anchor: the cushion ledger P resets, H01's multiplier is recomputed and cached, σ budgets refresh, and any raise takes effect (never mid-session, after Topstep). The account floor and the true high-water mark are never reset by an anchor (Hsieh's caveat). Anchor baselines are confirmed and persisted, so a restart cannot move them.
- Levels: unit, book, BMS, account.
- Per class and style: FX books anchor at the 17:00 New York rollover; crypto needs a declared clock; index units anchor at their cash open.
- Ledger: `day_boundary`, `day_start_equity`, `session_windows`; new *cushion_anchor_clock*.
- Performance: answers his "per cycle per Book against 24 hours" (B5): each style compounds on its own clock. Survival: no day-boundary exploit (X4-29), no reset by restart.
- Evidence chain: MQL5 day-boundary tests (A2-064, demo scenario tests), prop practice (A5-124, live). Weakest link: several clocks are harder to show on screen.
- Maturity: **solid**.

### C. Below baseline: levels, ramps and restores (probation brakes)

**X2-H13. The level map: a level is a fraction of the derived baseline.**
- Links: A1-052 and A2-190 (BOIN size levels), A5-039 (six-tier ramp), A5-021 (pilot budget in tail units), A1-054 (starter budget 10-25 %), A1-053 (proof continues at the smallest live size), A4-027 (live evidence only), X5-16.
- Need: N13, N01; answers X5's collision C4 (level-to-dollars).
- What and how: Level L0 is paper. L1 is the smallest live size that is feasible (H45) and at least 10 % of the H01 baseline. Then 25 %, 50 %, 75 % and 100 % of the baseline. Because each level is a fraction of the derived baseline, its dollars grow and shrink with the cushion and the unit count; no dollar ladder is typed. Moves: one level at a time, on cohorts of trades (cohort size scaled to trade rate: about 25 for a scalper, 10 for ORB), up when the bad-cohort rate is at or below BOIN's λe, down at or above λd, a level that trips twice is locked with all above it for a period (BOIN dose elimination). A bad cohort is in money (cohort net R at or below a threshold), so FI cuts count by size. Only live or smallest-level evidence moves levels (Numerai).
- Levels: unit.
- Per class and style: coarse-lot classes have few feasible levels at $500 (H49 makes them integer contracts); fast units climb in days, swing units in months (the "too safe" cost, named in collision X2-C05).
- Ledger: `size_levels`, `size_ramp_to_full`, `grow_back_rule`, `paper_min_trades`, `sequential_evidence_pass`; new *size_level_fraction_table*, *cohort_trades*, *bad_cohort_r*.
- Performance: a healthy unit reaches its full derived size as fast as cohorts fill. Survival: a failed unit is caught at a small level.
- Evidence chain: BOIN regulatory practice and simulations (A2-190, live in its field) → X5's cohort arithmetic. Weakest link: the bad-cohort threshold for each style.
- Maturity: **plausible**.

**X2-H14. Titration slow start with a first-warning switch.**
- Links: A5-127 (accelerated titration), A1-061 and A4-013 (warm-up ramp), A2-124 (world-switch reset), A1-055 (his "Kelly over about a month"), A1-057 (TCP slow start).
- Need: N13, N19.
- What and how: A new or returning unit starts at L1 and doubles its level fraction per clean cohort (never more than +100 % per step) until the first warning. A warning is a graded money event (a cohort at or below the bad threshold, or a day at the unit's own 5th percentile), never "any loss". After it: +50 % steps at most and cohorts of the full size, as in H13. Returning after an idle spell longer than a set number of anchors restarts at L1 (TCP restart after idle). His month: the ramp is counted in cohorts; a month is the calendar check that it is moving.
- Levels: unit.
- Per class and style: cohorts in trades for scalpers, in days for swing; energy and single stocks start one level lower (slowest ramp, A5-039).
- Ledger: `size_ramp_to_full`, `warm_up_window`, `size_levels`; new *first_warning_event*, *level_step_cap*.
- Performance: reaches working size much faster than a calendar ramp when all is well. Survival: the first warning slows the climb at once.
- Evidence chain: FDA titration rule (READ in R9), TCP slow start (live standard). Weakest link: the warning definition per style.
- Maturity: **plausible**.

**X2-H15. Restore engine with trip memory, settling and priced refills.**
- Links: A5-134 (memory ceiling: ssthresh and CUBIC), A5-137 (settle before the next change), A1-056 (probe at minimum size), A1-064 (loosen only on proof), A5-103 (restore definition), A5-130 (priced reinstatement), A2-039 (severity-graded cut).
- Need: N07, N16.
- What and how: After a brake cuts size, the restore remembers the level at which the trip happened. It climbs fast to half of that level, then slowly near it; no change while the last one is settling (enough trades at the current size to measure it). A restore never crosses baseline: going above needs an accelerator's own permission (H24). The cut itself is graded by severity: an FI-heavy bad day is mild, a gap through stops is severe (TCP: timeout drops to one segment). Repeated trips at one level lock it (H13).
- Levels: unit, book.
- Per class and style: settling counted in trades for fast units, in sessions for slow ones.
- Ledger: `grow_back_rule`, `drift_size_down_step`, `circuit_breaker_reset`, `calibration_cadence_trades`; new *last_trip_size_level*, *size_change_settle_trades*.
- Performance: fast recovery from small cuts. Survival: slow approach to the level that failed.
- Evidence chain: TCP and CUBIC (production standards), heparin recheck intervals (RCT, READ in R9). Weakest link: the remembered level goes stale after a regime change.
- Maturity: **plausible**.

**X2-H16. Overdose-controlled level steps (EWOC on the unit's own resampled record).**
- Links: A5-128 (EWOC), A1-052, A1-170 (re-size a recorded trade list), A5-131.
- Need: N13, N07.
- What and how: Before stepping up, resample the unit's own trade list (with FI cuts, costs and its gap history) at the next level's size and estimate P(bad cohort at the next level). Step only while that probability is at or under α. This is the dose-finding rule that "put more patients in the optimal range than accelerated titration without compromising safety" (R9 §1.6), with the toxicity model replaced by the unit's own record.
- Levels: unit.
- Per class and style: needs a record long enough for the resample; thin classes fall back to H14.
- Ledger: `size_levels`; new *overdose_bound_alpha*.
- Performance: climbs as fast as the bound allows. Survival: bounded chance of overshooting.
- Evidence chain: EWOC simulations (READ in R9). Weakest link: execution changes at a bigger size (slippage), which a resample of small-size fills cannot see (H23 covers capacity).
- Maturity: **wild**.

**X2-H17. Conservative-UCB tier probe (exploration with a bounded cost).**
- Links: A5-037 (conservative UCB live gate), A5-038 (contrast certificate), A5-026 (ring-fenced exploration budget), A4-199.
- Need: N19, N13.
- What and how: Treat "stay at this level" as the incumbent and "next level" as the candidate. Play the candidate only while a lower confidence bound on cumulative result stays above (1 − α) × what the incumbent would have made. The contrast is judged directly (candidate minus incumbent on the same trades), which recovers most of the opportunity a separate-bounds gate throws away. This makes "too safe" a measured cost: a level probe may cost at most a set fraction of the incumbent's result.
- Levels: unit.
- Per class and style: sub-Gaussian assumption breaks on fat-tailed classes; use only with H07's reserve in place.
- Ledger: `size_levels`, `size_ramp_to_full`; new *baseline_floor_fraction*.
- Performance: explores bigger sizes early instead of waiting for full proof. Survival: cumulative result never falls far below the incumbent's.
- Evidence chain: bandit simulations (A5-037, A5-038). Weakest link: a relative floor can approve a step while both the unit and the book lose; needs absolute limits beside it.
- Maturity: **wild**.

### D. Above baseline: accelerators and their proof

**X2-H18. Tier ladder with dwell and same-day step-down (Topstep shape on the unit's own ledger).**
- Links: A5-123 (Topstep Dynamic Live Risk Expansion), A5-124 (no size rise mid-session), A1-079 (consistency rule), A1-065 (prop scaling), A5-125 (fixed ratio, faster down), A4-004 (direction-split motion).
- Need: N06, N07.
- What and how: Net profit since the unit's last anchor reset of its tier record sets the tier. Tier widths are multiples of the unit's own day allowance (H02), so they are wide next to its normal swing (Topstep's first step needed five times the starting limit). Up one tier only after a dwell of active days and cohorts at the tier; down the same day if profit falls below the tier; counter resets on drop-out; no skipping; each tier lifts the unit's σ budget by a declared step (Topstep's +17 %, +14 %, +12 %). No step if one day supplied more than a set share of the qualifying profit (FTMO consistency). Tiers sit above baseline, so this is a true accelerator under R9.
- Levels: unit, book (a book tier on its own ledger).
- Per class and style: suits lumpy futures and index contracts; for FX micro lots the steps can be smooth.
- Ledger: `equity_band`, `equity_band_thresholds`, `unit_daily_loss_limit`; new *tier_width_day_sigmas*, *tier_dwell_active_days*, *best_day_profit_share_max*.
- Performance: risk grows with proven profit, slowly. Survival: step-down is immediate; a lucky day cannot qualify.
- Evidence chain: Topstep live rules (READ in R9), FTMO consistency (live). Weakest link: no published effect measure; on independent trades tiers add risk, not growth per risk (R9).
- Maturity: **solid** (as a rule set); its growth benefit is unproven.

**X2-H19. Persistence-gated press-and-ease.**
- Links: A5-121 (block-persistence pair), A5-131 (block test), A5-119 (pressing worth k × ρ R), A5-014 (pre-registered walk-forward with time out and rebound missed), A1-073 (size up below the curve, as the warning).
- Need: N06, N16.
- What and how: Off by default. It switches on for a unit only after the unit's own block test passes: block-sum autocorrelation scanned over block sizes with tries counted (a 500-trade regime shows in about 950 trades with 50-trade blocks). Then size presses after a good block and eases after a bad one, with a dead band (±5R in R9's script), the block size found by the test as the window. Book-level kill: when the test fails for many units at once, every persistence press goes off (persistence "breaks down abruptly and together", Ehsani-Linnainmaa).
- Levels: unit; book-level kill switch for the accelerator family.
- Per class and style: evidence is equity factors at monthly horizons; intraday FX, index, crypto units must prove their own. Mean-reverting sleeves are where the ease half most risks cutting before the rebound.
- Ledger: `drift_size_down_step`, `effective_tries`; new *block_persistence_score*.
- Performance: R9 script: 1.156 against 0.604 growth per risk under slow regimes. Survival: the ease half drops losers early, which carried most of the factor evidence.
- Evidence chain: factor momentum (READ in R9) → R9 script. Weakest link: no study of intraday retail persistence after costs.
- Maturity: **plausible**.

**X2-H20. Accelerator proof card: resize replay against an equal-average constant.**
- Links: A1-170 and A4-186 (re-size a recorded trade list), A2-141, A1-173 (random control at matched activity), A5-024 (shadow allocator ablation), A1-174 (dry chassis), R9 §2.3 metric.
- Need: N06, N12, N18.
- What and how: An accelerator's switch-on condition, for every kind: replay the unit's recorded trade list with the accelerator on and with a constant size equal to the accelerator's average size; it passes only if its growth per unit of average risk beats the constant by a set margin and its deep-drawdown odds are no worse, on the unit's own trades and on a random-entry control (the dry chassis). Tries counted. The card is what an agent or the copilot reads before proposing the accelerator, and what he signs.
- Levels: unit, book.
- Per class and style: same rule; replay uses each class's real costs and gaps.
- Ledger: `effective_tries`, `brake_precision`; new *accelerator_growth_per_risk_ratio*.
- Performance: only accelerators that pay ship. Survival: an accelerator that is a disguised size increase is caught.
- Evidence chain: StrategyQuant QuantAnalyzer (live product), MQL5 random-control design (A1-173, controlled test). Weakest link: QMX has no resize replay yet; the judge is size-blind (G8 §5.3).
- Maturity: **solid** (design); needs a build.

**X2-H21. Falling-risk pyramiding for trend units, with a persistence proof.**
- Links: A1-071 (unified stop, falling risk, occupancy gate), A5-120 (Turtle adds), A1-048 (regime-age taper), A1-115 (bet key), A5-131.
- Need: N06, N17.
- What and how: A trend unit may add to a winner only if total risk on the bet key does not rise (lots fall per add, one unified stop advances, locked profit covers the new risk), the book is under its occupancy cap, the regime is young (taper new adds as it ages), and the unit's own record shows trend persistence at its holding horizon. Adds are re-sized from the current baseline, not from the opening size.
- Levels: position, unit.
- Per class and style: futures, FX trends, metals, indices: plausible. Mean-reverting scalpers: never. Crypto weekend gaps make "risk-free" adds false, so weekend adds are refused.
- Ledger: `positions_per_instrument`, `open_risk_at_stop`, `stop_widening_allowed`, `context_size_modifier`.
- Performance: size grows where the trade proves its own premise. Survival: total risk on the bet stays flat.
- Evidence chain: Turtle practice (snippet), MQL5 author backtests. Weakest link: gaps skip the unified stop.
- Maturity: **plausible**.

**X2-H22. Calm-volatility scaling for risk-asset units, with a calm-duration guard and an instant spike cut.**
- Links: A5-129, A1-010 and A3-047 (volatility-managed exposure), A5-097 (pooled volatility dynamics), A1-025 (slow estimate inside a sizing rule), A3-016.
- Need: N06, N20, N10.
- What and how: Exposure × (σ_target ÷ σ_forecast), capped, with a slow, pooled forecast (each instrument's own level, dynamics pooled across the class) on the session-normal clock. Raise side only for units on equity-index or credit-like risk; for FX, bonds, commodities only the cut side runs (tail control). Calm-duration guard: after a long spell below the low volatility percentile, raises freeze (long calm precedes crises, Danielsson). Spikes cut at once. Not applied to stop-sized scalpers whose R already normalises volatility (collision X2-C19).
- Levels: unit, book.
- Per class and style: equity indices: Sharpe gain plausible; others tail control only; crypto weekend volatility leads Monday risk elsewhere.
- Ledger: `volatility_target`, `context_size_modifier`; new *vol_scaler_cap*, *calm_duration_guard_days*.
- Performance: Sharpe gain for risk assets (Harvey et al., abstract). Survival: smaller positions when volatility is high cut tails in all classes.
- Evidence chain: Moreira-Muir and Harvey (author and abstract), Cederburg (real-time doubts). Weakest link: the gain did not hold in real time across 103 strategies.
- Maturity: **plausible**.

**X2-H23. Probe-and-drain capacity finder with a venue capacity cap.**
- Links: A5-135 (BBR probe cycle), A5-148 (venue capacity ceiling), A5-042 (impact at the new size), A3-066 (slippage budget k / depth), A1-144 (p95 slippage).
- Need: N06, N04.
- What and how: When a unit's derived size grows past sizes it has traded, it probes: one cohort at 1.25x the current size, then one at 0.75x, then back to 1.0x, keeping the higher capacity estimate only if fills held (p95 slippage, rejections and requotes within band). Every accelerator respects the resulting capacity cap per venue and broker; rising rejections or worse fills lower it (bookmakers cut a winning bettor to $1.25 a bet).
- Levels: unit, venue.
- Per class and style: thin crypto venues, off-hours metals and small contracts have the most unknown capacity; FX dealing desks with last look push back first.
- Ledger: `max_position_size_lots`, `slippage_cost`; new *venue_capacity_cap_lots*.
- Performance: finds the largest size the venue takes. Survival: no accelerator assumes unlimited capacity.
- Evidence chain: BBR (production, snippet), Kaunitz et al. (READ). Weakest link: probing on a losing day mixes capacity with edge.
- Maturity: **wild** at $500 (capacity rarely binds), **plausible** later.

### E. Pairing: so a raise never drives into a trip

**X2-H24. Raise permission gate: headroom to the nearest trip.**
- Links: A5-138 (any brake blocks every raise), A5-141 (budget-burn permit), A5-137 (settle), A5-134 (memory ceiling), A4-007 (Simplex safe region), A2-112 (trading states), `brake_state`.
- Need: N07, N06.
- What and how: Before any accelerator or restore raises size, four checks, all must pass: (1) no brake at the unit's scope or above is active or settling; (2) the loss budget's burn is healthy over two windows (an exhausted budget freezes every accelerator until positive); (3) headroom: after the raise, m full losses at the new size (with gap factor) still fit before the nearest trip of any brake in force, read from `brake_state`'s distance to trip; (4) the new size is below the remembered trip level or the slow regrow allows it. A raise that fails is clipped to the largest size that passes, with the reason on the receipt.
- Levels: trade (applied), unit, book.
- Per class and style: m scales with the unit's frequency (a 40-trades-a-day unit needs more losses of headroom than a 2-a-day one).
- Ledger: `brake_state`, `control_rank_table`, `budget_remaining`; new *raise_headroom_losses*, *accelerator_ceiling_multiple*.
- Performance: accelerators act whenever conditions are clean. Survival: no accelerator can carry size into the brake that will fire next.
- Evidence chain: AWS any/all policy (snippet), TCP memory (standard), Simplex (engineering). Weakest link: brake_state must exist and be correct (X1, X6).
- Maturity: **plausible**.

**X2-H25. Nomogram block: one signal, a dead band, steps sized by distance, asymmetric speed.**
- Links: A5-136 (heparin nomogram), A5-113 (coupled pair), A5-140 (three zones), A5-139 (speed by signal type), A4-004 (direction-split windows).
- Need: N07, N12, his volleyball rule (A13).
- What and how: A generic QML block: one signal (a cushion z-score, a cohort score, a cost reading, a block P&L), a table of bands, and a size step per band, larger the further from the dead band, with an attack speed and a release speed per direction. Each row of the table is a stated reason. The same block runs the cushion pair (H10), the cost taper (H42), the drift step (H27) and a three-zone level move (H13), so "every change in size has a reason" is the table row.
- Levels: any.
- Per class and style: bands per class or per unit; under-exposure is corrected as actively as over-exposure (heparin's lesson).
- Ledger: `sqs_hysteresis_band`; new *nomogram_dead_band*.
- Performance: no churn inside the band. Survival: big deviations get big cuts.
- Evidence chain: Raschke heparin RCT (READ in R9: 97 % against 77 % in range within 24 h). Weakest link: bands need calibration per unit.
- Maturity: **plausible**.

**X2-H26. AIMD day pair with memory, thresholds in the unit's own percentiles.**
- Links: A5-133 (AIMD day pair), A1-058 and A4-012 (grow only when used), A5-144 (frequency-scaled thresholds), A5-134.
- Need: N07, N16, N20.
- What and how: Multiply size by 0.7 after a day at or below the unit's own 5th percentile day; add 0.05 of baseline after a green day, only if the unit used at least half its size that day; regrowth slows near the last trip level; bounds 0.25x to 2.0x of baseline (above 1.0x it needs H24's permission).
- Levels: unit, book.
- Per class and style: thresholds in the unit's own day distribution, so they scale with frequency and class volatility.
- Ledger: `drawdown_pressure_multiplier`, `session_result_r`, `grow_back_rule`; new *aimd_cut_factor*, *aimd_add_step*.
- Performance: R9 script: same growth per risk as a constant on independent trades; 0.700 and 1.105 against 0.583 and 0.604 under regimes. Survival: deep-drawdown odds 0.5 % against 1.3 % for a constant at the same 0.8x average.
- Evidence chain: R9 script [arithmetic], AIMD convergence (abstract), Netflix library (live). Weakest link: fat tails, gaps and correlated units make every number worse.
- Maturity: **plausible**.

**X2-H27. Two-speed sizer: a fast money multiplier times a slow edge multiplier.**
- Links: A5-139 (speed by signal type), A5-012 (cut because the edge fell, not because equity fell), A4-004, A1-019, A2-133 (drift size-down).
- Need: N16, N07, his A25 and C19.
- What and how: Size = baseline × m_money × m_edge. m_money comes from the cushion ledger (H10) and reacts at once to money facts. m_edge comes from the shrunk live edge against the plan and moves slowly: a down window over cohorts, steps no bigger than one level, never on one day. So a bad day hits m_money (and the brakes), not the unit's standing; a decaying edge lowers m_edge gradually and hands off to X3's demotion rules. This is "size down, but not quickly" for drift and "don't lose stupidly" for money, in one formula.
- Levels: unit.
- Per class and style: mean-reverting units suffer most from equity-based cuts, so m_edge matters most there.
- Ledger: `drift_state`, `drift_size_down_step`, `kelly_shrink_factor`, `drawdown_pressure_multiplier`; new *edge_signal_multiplier*.
- Performance: keeps size through ordinary losing patches, where much recovery return sits. Survival: money brakes still act fast at book level.
- Evidence chain: Man Group drawdown study (READ in R9), A5-012 (idea). Weakest link: the edge estimate lags a real decay.
- Maturity: **plausible**.

### F. Splitting risk across many units

**X2-H28. Breadth-to-budget on residual, stressed N_eff (breadth spreads a fixed total, never raises it).**
- Links: A5-003 (breadth-to-budget), A5-004 (residualised breadth), A1-087, A1-105, A1-129 (stressed correlation), A3-049 (stressed floor), A5-001 (entropy ENB), A3-163.
- Need: N03, N05.
- What and how: The book's total swing is fixed by survival (H01 or H02). Breadth only decides how it is shared: each unit's share is 1/√(N(1 + (N − 1)ρ)) of the solo size, where ρ = max(measured, stressed) correlation of units' *residual* P&L after shared drivers (USD, equity beta, crypto beta, rates, volatility). Recomputed on two clocks: allocation weekly, a fast stressed override when a co-movement tell fires. Ten units that are really two bets get the sizes of two bets.
- Levels: book, BMS.
- Per class and style: FX majors share the USD leg (low residual breadth); crypto tokens are one market factor (ENB near 1-2); futures across classes give the most real directions.
- Ledger: `effective_independent_bets`, `unit_result_correlation`, `portfolio_daily_risk_budget`, `cluster_exposure_cap`; new *stressed_unit_correlation*.
- Performance: budget flows to units that add independent risk; in the sim, √-scaled shares grew 2.8x the 1/N split at equal safety. Survival: breadth can never be the reason total risk rises.
- Evidence chain: fundamental law and ENB (idea level), sim [arithmetic]. Weakest link: correlation estimates from short, on/off unit histories.
- Maturity: **plausible**.

**X2-H29. Own full size under a parent limit set on co-loss (with overbooking and a bump rule).**
- Links: A1-085 (own weight, scaled only when the total binds), A1-086 and A3-161 (parent below the sum), A2-027 (warning before hard limit), A1-121 (shed by priority), airline overbooking (cross-pollination).
- Need: N03, N05; the lead's 1 Nov "each unit keeps its full size".
- What and how: Each unit sizes as if alone (H01 at N = 1). The book holds a parent limit = factor × Σ children, the factor measured from how often the children lose together (joint-loss quantile ÷ sum of standalone quantiles, floored at a stressed value). Children keep full size until the parent binds; then they are scaled by priority (H30), not pro rata. "Overbooking": the sum of children may exceed the parent because they rarely all trade at once; the bump rule says who waits when they do.
- Levels: book, BMS.
- Per class and style: works best where units really trade at different hours (Tokyo FX, London metals, New York indices, weekend crypto).
- Ledger: `portfolio_daily_risk_budget`, `bms_daily_loss_limit`, `unit_daily_loss_limit`, `capital_sharing_rule`; `x1_aggregate_limit_factor` (defined in X1's additions).
- Performance: each unit keeps full size in normal times (most breadth). Survival: the parent binds on losing-together days; at half the edge, ten full-size units touched the floor 11 % against 5.8 % for one unit (lead's 11:07 sim), so the parent is not optional.
- Evidence chain: RiskMetrics limit hierarchy (live bank practice). Weakest link: the co-loss factor rises in stress, exactly when it matters.
- Maturity: **plausible**.

**X2-H30. Risk QoS classes: Guaranteed, Burstable, BestEffort (with cushion lending).**
- Links: A4-188 (bulkhead plus guaranteed shares), A1-120 (open-risk compartment), A1-121 and A4-189 (shed by priority class), A1-058 (grow only when used), A1-119 (reserve ratio), Kubernetes requests and limits (R7), crop rotation (cross-pollination).
- Need: N05, N19, N13.
- What and how: Every unit has a request (its guaranteed share of book risk) and a limit (the most it may burst to when the book has slack). Proven units are Guaranteed (request = limit); probation units are Burstable (small request, may borrow slack); paper and new units are BestEffort (only slack, shed first). When the book tightens, BestEffort is shed first, then Burstable down to request; Guaranteed is touched last. Cushion lending: an idle style pot (ORB after the New York close) lends its slack to scalpers overnight as BestEffort budget, recalled at its next open.
- Levels: book, BMS.
- Per class and style: 24/7 crypto is a natural borrower on FX weekends (capped by H36).
- Ledger: `unit_capital_share`, `slot_rebalance_rule`, `concurrent_unit_slots`, `open_risk_ceiling`; new *unit_risk_qos_class*, *unit_risk_request_share*, *unit_risk_burst_share*.
- Performance: idle budget works instead of sitting. Survival: proven units keep size under pressure; borrowers are evicted first.
- Evidence chain: Kubernetes QoS and Google criticality shedding (production practice). Weakest link: priority by status can protect a decaying proven unit (X3's demotion must feed the class).
- Maturity: **plausible**.

**X2-H31. AIMD budget shares that converge without a central optimiser.**
- Links: A5-147 (AIMD shares converge to fair splits), A1-058 and A4-012 (grow only when used), A2-040.
- Need: N05, N12.
- What and how: Each unit runs AIMD on its share of the book's σ budget against one shared congestion signal (the book near its parent limit): +δ per anchor when it used at least half its share and the book was not congested, ×β when the book was congested. Shares converge to a fair split from any start (Chiu-Jain), and units that do not trade do not grow.
- Levels: book.
- Per class and style: no class difference.
- Ledger: `capital_sharing_rule`, `portfolio_daily_risk_budget`; new *share_growth_use_fraction*.
- Performance: a self-organising split with no optimiser to estimate. Survival: everyone cuts together when the book is stressed.
- Evidence chain: AIMD convergence proof (abstract), Netflix library (live). Weakest link: fair is not optimal when edges differ; "grow when used" rewards trading more.
- Maturity: **wild**.

**X2-H32. Hierarchy decides who gets risk; a capped fractional Kelly sets only the total.**
- Links: A5-025, A1-107 (three-level budget), A5-018 (NCO), A1-093 (HRP), A1-095 (inverse volatility as the default), A1-094 (one shrinkage knob), A5-019, A5-020 (bounded learned tilts).
- Need: N05, N12, N18.
- What and how: Portfolio → style pot → cluster (by exposure and behaviour, A5-027) → unit. Within a level, a signal-blind allocator (inverse volatility by default; HRP or NCO when there are enough histories) decides shares. The total scale is a heavily fractional, capped growth rule on aggregate validated edge that shrinks when uncertainty grows, and never above the survival total (H01). Learned tilts, if any, are bounded and slow.
- Levels: BMS, book, cluster.
- Per class and style: clusters by shared driver, not label.
- Ledger: `cluster_exposure_cap`, `unit_capital_share`, `kelly_multiplier`, `kelly_cap`; reuses `capital_sharing_rule` as the allocator choice.
- Performance: steadier than a full optimiser, so budget is not wasted on estimation noise. Survival: survival total above any edge-led total.
- Evidence chain: NCO and HRP (author work, simulations), RL-BHRP backtest (A5-020). Weakest link: alphas do not form stable clusters (Kakushadze).
- Maturity: **plausible**.

**X2-H33. Marginal-stress budget across exposure zones and dependencies.**
- Links: A3-159 (stress as survival gates, marginal stress as growth control), A3-150 (scenario-loss matrix), A3-148 (CRESTA zones), A5-091 (dependency concentration), A1-168 (joint ES).
- Need: N05, N20.
- What and how: Every unit's budget is tilted by its marginal contribution to book stress loss over X4's scenario matrix: units that lower book stress earn more, units that add to the dominant zone earn less. Zones include operational dependencies (one broker, one feed, one host, one signal family). Survival gates: no book state may breach his floor on any credible scenario.
- Levels: book, BMS.
- Per class and style: a single broker carrying FX, metals and index CFDs is one dependency zone; crypto on Hyperliquid another.
- Ledger: `portfolio_exposure`, `cluster_exposure_cap`, `unit_capital_share`, `portfolio_floor`; new *marginal_stress_contribution_usd*.
- Performance: diversifying units get more budget. Survival: the losing-together case is priced in advance.
- Evidence chain: insurance accumulation practice (live), CVaR allocation backtests (A3-150). Weakest link: scenario completeness.
- Maturity: **plausible**.

**X2-H34. Same-bet key, a unit basket cap and a heat cap derived by Little's law.**
- Links: A1-115 (bet key), A1-114 and A3-050 (currency legs), A1-113 (three scopes), A1-108 and A3-162 (portfolio heat), A3-148, Little's law (cross-pollination).
- Need: N17, N05.
- What and how: Every position gets a bet key by a declared rule (currency legs for FX, underlying id for futures and CFDs, sector for stocks, the window for ORB families). Open risk is capped per key, per unit (the basket) and per account; a second position on the same key gets only what the key has left. The heat cap is derived, not typed: expected concurrent positions L = trade rate × average hold; the unit's open-risk cap = r × (L + z√L) rounded up to whole positions; the book's heat cap is the sum under the parent factor.
- Levels: position, unit, book, account.
- Per class and style: example: a scalper with 0.5 trades an hour and 30-minute holds has L = 0.25, cap 2 positions; an ORB unit across three opens with 3-hour holds has L ≈ 1.1, cap 4. FX keys split by leg; gold sits in both USD and metals keys.
- Ledger: `open_risk_at_stop`, `open_risk_ceiling`, `positions_per_instrument`, `currency_exposure_limit`, `max_open_positions`; `x1_bet_key_rule` (X1's); new *open_risk_cap_per_key_usd*, *expected_concurrent_positions*.
- Performance: units hold several positions where the logic allows. Survival: three positions on one dollar are one bet.
- Evidence chain: MQL5 risk managers (ideas), queueing theory (textbook). Weakest link: undeclared shared exposure escapes the key.
- Maturity: **solid** (key and caps), **plausible** (derived heat cap).

**X2-H35. Session-open family budget for ORB breadth.**
- Links: A1-135 and A3-020 (size the family of session-open units), A3-032 and A1-082 (breadth through opens, his "brilliant"), A3-021 (in-play gate).
- Need: N03, N05.
- What and how: One ORB logic across many opens (Tokyo, London, New York; each index cash open; metals) is one family. The family's σ budget is shared by the correlation formula with ρ measured across opens (about 0.3 monthly in the MQL5 test), so each open gets about √N_eff ÷ N of the solo size. Each open still earns its own record and level; an "in play" gate (relative volume or tick rate at the open) decides whether that open trades today.
- Levels: methodology, unit.
- Per class and style: FX and gold opens are London and New York; indices have cash opens; crypto has no open (excluded).
- Ledger: `family_daily_budget`, `trade_rate`, `effective_independent_bets`, `session_windows`.
- Performance: a once-a-day edge becomes several bets a day without raising size. Survival: opens correlate on risk-off days, which the stressed ρ prices.
- Evidence chain: MQL5 ORB family backtest (author), ORB in-play paper claims (cited, not retested). Weakest link: correlation across opens is period-dependent.
- Maturity: **plausible**.

**X2-H36. Open-breadth day budget scaling (weekends and single-class hours).**
- Links: A3-114, A1-167 (session-aware risk on common UTC intervals), H02.
- Need: N14, N05, N20.
- What and how: The usable σ budget in any hour scales with the breadth actually open: when only crypto trades (the FX weekend), crypto may spend at most its weekday share, not the whole day budget, because N_eff is near 1. Stale-feed rules read the calendar so a closed FX feed is not a fault.
- Levels: BMS, book.
- Per class and style: crypto weekend volatility can be 1.5x weekday.
- Ledger: `portfolio_daily_risk_budget`, `effective_independent_bets`, `feed_stale_after`; new *open_breadth_budget_scale*.
- Performance: crypto keeps trading at its normal share. Survival: no crypto-sized hole on Sunday night.
- Evidence chain: idea (A3-114). Weakest link: crypto may be the only good market at the weekend, and a fixed share ignores it.
- Maturity: **plausible**.

**X2-H37. Poker-band style pots for BMS slots ("if the capital allows").**
- Links: A5-126 (bankroll bands with shots), A1-090 and A4-174 (BMS opens or closes style slots), A1-089 ($300/$200 split), A1-110 (slots), A1-102 (slow, capped reweighting), A1-103 (performance-chasing warning).
- Need: N14, N19, his C26.
- What and how: Each style pot (scalpers, intraday, ORB) opens another slot when its cushion holds X of the next slot's day budgets, and closes one below Y of the current slot's; between them it stays (the dead band stops flapping). A "shot" at an extra slot is allowed with a pre-set stop. Rebalancing between pots is slow, capped per review and charged for costs; it follows pot cushions, never last week's winner.
- Levels: BMS.
- Per class and style: no class difference; pots per style.
- Ledger: `style_capital_split`, `slot_rebalance_rule`, `concurrent_unit_slots`; new *pot_slot_open_day_budgets*, *pot_slot_close_day_budgets*.
- Performance: his self-optimising BMS as a rule, not a hand edit. Survival: a pot cannot open slots on profit it has not banked.
- Evidence chain: poker bankroll practice (snippet), adaptive-allocation warnings (A1-103, simulation). Weakest link: thresholds unvalidated.
- Maturity: **plausible**.

**X2-H38. Swarm split: above capacity, growth buys breadth, not size.**
- Links: A5-148 (venue capacity), A5-135 (probe), A1-082 (breadth), A5-005 (admit by marginal book effect), A1-105, beekeeping (cross-pollination).
- Need: N03, N06, N19.
- What and how: When a unit's derived size reaches its venue capacity cap or its bet-key cap, new budget does not raise its size: the BMS proposes a new deployment of the same logic on an admitted market or session with low residual correlation to it (his card). Compounding continues through breadth.
- Levels: BMS, unit.
- Per class and style: most useful for crypto and thin metals; at $500 capacity rarely binds.
- Ledger: `live_unit_count`, `effective_independent_bets`; new *breadth_split_threshold*.
- Performance: growth without crowding one market. Survival: no single venue carries the growth.
- Evidence chain: analogue only. Weakest link: a new market is a new unproven record.
- Maturity: **wild**.

### G. Costs into size

**X2-H39. Cost triple: denominator, Kelly in R and an edge-to-cost gate, per hour and per world.**
- Links: A1-142 and A3-007 (size bound with cost and stop slippage), A5-084 (Kelly with costs), A1-138 and A2-223 (edge-to-cost gate), A1-147 and A3-084 (hourly cost profile), A1-144 and A4-167 (p95 slippage, entry and exit apart), A1-146 (one cost ledger), A1-152 (QMB ports), A1-004 (commission), EOQ (cross-pollination).
- Need: N04, N15.
- What and how: Costs enter in three places and only three. (1) Denominator: quantity = risk ÷ (stop × value per point + round-trip cost + stressed stop slippage), all for this instrument, hour, session and world. (2) Ceiling: H04's Kelly in R with c = cost ÷ stop. (3) Gate: the low end of gross edge must be at least k × stressed cost (2x, 3x for negative skew) for this hour, else skip or wait for a cheaper hour. Every "per timeframe" effect falls out of cost over stop: shorter timeframes mean smaller stops, so the same cost is a larger share of R. Uncalibrated costs use a stressed class default (twice the broker's posted typical spread) that decays toward measured fills; never zero, never a blanket refusal. A minimum worthwhile risk (EOQ): when a per-lot minimum commission makes the cost share of R too high, the trade is skipped.
- Levels: trade, unit.
- Per class and style: FX: spread binds, 21:00-22:00 GMT and the 17:00 New York rollover; crypto: taker fees (about 0.09 % on Hyperliquid) and funding; micro futures: fixed commission per contract; CFDs: markup and last look.
- Ledger: `round_trip_cost_r`, `spread_cost`, `commission_cost`, `slippage_cost`, `unit_cost_target`, `cost_stress_multiple`; `hourly_cost_profile` and `edge_to_cost_ratio_min` (X0's); new *stressed_stop_slippage_r*, *min_worthwhile_risk_usd*.
- Performance: size goes to cheap hours automatically; no gross-edge over-sizing. Survival: stops a negative net edge being multiplied by breadth.
- Evidence chain: BTC cost-aware filter (author backtest: −64 % to +65 % a year), MQL5 broker probes (author), QMB ports (built, rates deferred). Weakest link: no slippage is measured anywhere yet (G6 §5.4).
- Maturity: **solid** (specified pieces), blocked on facts.

**X2-H40. Measured-cost hour map replaces session multipliers and premium-window lifts.**
- Links: A1-070 (sniping window as a measured slice of net edge), A1-069 and A3-034/A3-037 (old session multiplier and premium flag), A3-016 and A3-017 (time-of-day volatility and cost apart), A3-023 (gate on measured volatility, not clock flags), A1-147.
- Need: N04, N10, his D8.
- What and how: Delete the free size multiplier per session. A unit's "window" is a time slice where its measured net edge after costs is higher out of sample; it gets more size only through the cost term (H39) and the edge band (H03), never through a separate lift. The hour map is per instrument, per world, written from the market journal, with session flags replaced by measured volatility and cost states.
- Levels: unit, instrument.
- Per class and style: FX fixes and sessions; gold London fixes; index cash opens; crypto venue-deep hours and funding times.
- Ledger: `session_multiplier`, `premium_window_flag`, `session_windows`, `spread_cost`, `hourly_cost_profile` (X0's).
- Performance: trades the cheap hours harder for a real reason. Survival: no double-paying for a window.
- Evidence chain: FX spread-by-hour research (G7 §4.3), fix-reversal arithmetic (A1-070). Weakest link: selecting hours from history is look-ahead unless out of sample.
- Maturity: **plausible**.

**X2-H41. Carry and funding in the hold-size decision.**
- Links: A1-148 and A3-026 (swap and funding, triple-swap day), A3-239 (funding at the venue timestamp), A5-084, A1-151 (broker reality check).
- Need: N04, N10.
- What and how: For units that hold past a rollover or a funding time, expected carry over the planned hold (in R, signed) joins the cost term; the triple-swap day and funding timestamps are known events. Positive carry may extend the planned hold; heavy or asymmetric swap is flagged at deploy.
- Levels: trade, unit.
- Per class and style: FX and metals rollover; index CFDs financing and dividend adjustments; perps every 8 hours; futures pay roll instead. Scalpers flat before rollover carry nothing.
- Ledger: `swap_financing_cost`, `funding_cost`, `max_hold_time`; reuses *carry_cost_r*.
- Performance: carry-positive holds stay. Survival: slow financing drag is seen.
- Evidence chain: MQL5 swap articles (simulation), venue rules. Weakest link: QMB books carry as separate cash events, not in trade R (G8 §5.1).
- Maturity: **solid**.

**X2-H42. Cost nomogram: size shrinks before the SQS blocks.**
- Links: A1-014 and A3-071 (spread-percentile size cut), A1-150 (spread against the unit's cost target), A3-069 (one execution-risk score), A1-127 and A3-076 (old microstructure multiplier), A5-136, `sqs_score`.
- Need: N04, N20.
- What and how: Live cost (spread, then the execution-risk score) against the unit's proven cost band drives an H25 nomogram: inside the band no change; above p75 a step down; above p90 a bigger step and a feed check; above the SQS hard block, no entry (SQS stays as is). Today the SQS and the spread guard only block (A1-150); this adds the graded shrink in front of the block. With H39's denominator fed by live spread, much of this happens by itself; the nomogram covers depth and noise that the spread alone misses.
- Levels: trade, instrument.
- Per class and style: thresholds refit per instrument and broker; FX CFDs lack real depth, so spread and tick-rate stand-ins.
- Ledger: `sqs_score`, `sqs_hard_block_threshold`, `spread_cost_guard`, `unit_cost_target`, `microstructure_multiplier`; reuses *nomogram_dead_band*.
- Performance: trades continue at smaller size in costly minutes. Survival: hard block unchanged.
- Evidence chain: NQ M1 percentile study (author backtest, 602 sessions). Weakest link: thresholds do not transfer; any cut looks good on a losing unit unless tested against a random cut (A1-173).
- Maturity: **plausible**.

**X2-H43. Combined-flow cost netting across units on one venue.**
- Links: A3-239 (cost on combined flow through one interface), A1-118 and A4-076 (virtual positions netted), A3-015 (dealer skew on repeat same-side trades).
- Need: N04, N05.
- What and how: Costs are charged on the combined flow reaching one venue: two units offsetting on one symbol are flagged (they pay spread for no exposure); several units hitting one pair the same way within minutes are charged the dealer-skew penalty in their cost term; netting accounts get one real position per symbol from virtual unit positions.
- Levels: account, venue.
- Per class and style: OTC FX and CFD brokers internalise and skew; exchange books differ.
- Ledger: `netting_mode`, `spread_cost`, `slippage_cost`; no new id.
- Performance: less spread paid when units offset. Survival: units cannot each assume the whole book's liquidity.
- Evidence chain: BTC perp cost decomposition (author), MQL5 netting backtest (in-sample). Weakest link: attribution of netted fills back to units.
- Maturity: **wild**.

### H. Which equity the sizer reads

**X2-H44. Asymmetric equity basis: committed cushion for size, marked equity for brakes, realised profit for accelerators.**
- Links: A2-115 and A4-059 (declared series and base for every limit), A2-096 (kill line on marked equity), A1-113 (committed risk re-read from broker stops), A1-108 (heat), A1-130 (budget share), accounting's lower-of-cost-or-market rule (cross-pollination).
- Need: N08, N17.
- What and how: Four rows, each declaring its series. (1) Sizer: committed cushion = min(balance, marked equity) − floor − open risk at the stops − pending orders' risk, on the unit's budget share; size follows marked equity down at once and realised equity up only when closed. (2) Brakes: marked equity (FTMO practice; the DOCS kill line). (3) Accelerators: realised profit only, never open profit. (4) Floor clip (H07): worst case at the stops with the gap factor. A fourth position sizes from what the first three left.
- Levels: unit, book, account.
- Per class and style: crypto perps mark to the venue's mark price (liquidation reads mark, not last); FX CFDs mark on bid or ask; futures on settlement for overnight.
- Ledger: `sizing_equity_basis`, `brake_equity_basis`, `account_equity`, `account_balance`, `realized_pnl`, `unrealized_pnl`, `open_risk_at_stop`; new *committed_cushion_usd*, *accelerator_equity_basis*.
- Performance: no pressing on open profit that may vanish. Survival: three open trades in loss shrink the fourth at once.
- Evidence chain: prop-firm and DOCS practice (live; docs), MQL5 basket managers (idea). Weakest link: the shipped stack reads cTrader equity once at sign-in (G9 §3.3), so marked equity is not yet a fact.
- Maturity: **solid**.

### I. Lots, margin and normalising across classes

**X2-H45. Feasibility-first admission at the derived size.**
- Links: A1-157 (minimum-size feasibility per class), A3-002 (round toward less risk), A3-013 (per-class scalping realism), A5-042 (tier feasibility with impact), A1-153 (round down, skip below minimum), A1-158 (margin), A5-096 (regulatory leverage cap), A1-162 (instrument risk record), A1-154 (silent oversize, the failure).
- Need: N09, N10, N13.
- What and how: For each (unit, instrument, broker), compute the money at the unit's typical stop for one minimum lot, with gap factor and costs, and compare it with the unit's current L1 and baseline. Admit live only if min-lot risk ≤ tolerance × the level's risk (tolerance declared, for example 1.25x). Otherwise the instrument stays paper for that unit until the budget grows. The MIS router may only place a unit where it is feasible; admission is ordered by feasibility, so at $500 the first units go to FX micro lots and crypto spot (roundtable). Sizes always round down; margin headroom and the regulatory cap are separate checks.
- Levels: unit × instrument, account.
- Per class and style [judgment, from standard contract specs, not checked against IC Markets]: EUR/USD 0.01 lot ≈ $0.10 a pip, so a 10-pip stop needs $1; gold 0.01 lot ≈ $1 per $1, so a $3 stop needs $3; a micro E-mini is $5 a point and a micro Nasdaq $2 a point, so typical stops need $20-40; micro crude about $1 per cent; crypto spot and fractional shares are fine; energy is the hardest.
- Ledger: `min_lot`, `lot_step`, `max_lot`, `value_per_point`, `leverage`, `margin_used`, `rounding_residue_r`, `instrument_class`; new *min_lot_risk_tolerance*, *instrument_feasible_at_size*.
- Performance: picks the tradable universe before the MIS does; no budget wasted on skips. Survival: no forced oversize.
- Evidence chain: R3 worked numbers and chat-29 (research), April's 4x gap (old system). Weakest link: broker product specs change; records refresh daily (G7 §4.2).
- Maturity: **solid**.

**X2-H46. Lot dither: carry the rounding residue so average risk meets target.**
- Links: A1-153, A1-156 (rounding residue on the receipt), error diffusion from image printing (cross-pollination).
- Need: N09, N19.
- What and how: When the target is 0.013 lots and the step is 0.01, trade 0.01 and carry 0.003 lots of residue; when the carried residue reaches a step, the next trade takes one more step. Average risk equals target; no single trade exceeds a hard multiple of target (1.5x), none inside a news window, and the residue resets at the anchor.
- Levels: trade, unit.
- Per class and style: helps coarse-step classes at small equity (gold, index CFDs); pointless for crypto spot.
- Ledger: `rounding_residue_r`, `lot_size`; new *lot_dither_max_multiple*.
- Performance: no systematic under-sizing on coarse lots. Survival: a dithered trade risks up to 1.5x plan, which is the cost (Dana's objection in the roundtable).
- Evidence chain: analogue only. Weakest link: variance per trade rises even though the mean is right.
- Maturity: **wild**.

**X2-H47. The three-number sleeve record as the cross-class currency, with pooled class defaults.**
- Links: A3-001 (routine risk, stress loss, feasible size), A1-137 (account-level loss units), A1-160 (money at the stop from broker tick value), A1-161 (risk unit and quirks per class), A1-163 (risk buckets with a residual), A5-048 (pooling policy per parameter type), A5-097 (pooled volatility dynamics), A4-196 (empirical-Bayes shrink), A1-165 (underlying identity), A5-084 (gap factor).
- Need: N10, N09, N12.
- What and how: Every unit × instrument carries three numbers on one account-currency loss scale: routine risk (money at the stop with costs, which is what R means), stress loss (at the class's worst step from X4), feasible minimum loss (one lot). Sizing uses the first, caps and allocation the second, admission the third. Class defaults (gap factor, worst step, cost model) live on the class and bucket rungs of the override chain; instrument values shrink toward their class by rule: pool volatility dynamics, keep costs local, never pool market mechanics (rolls, funding, lot steps).
- Levels: instrument, unit, book.
- Per class and style: FX aggregates by legs; indices by regional beta; metals split precious and industrial; energy by product and month; crypto majors versus small tokens; stocks by sector.
- Ledger: `value_per_point`, `price_increment`, `instrument_class`, `gap_loss_beyond_stop`, `calibration_shrink_k`; new *sleeve_stress_loss_usd*, *pooling_rule_per_parameter*.
- Performance: one template sizes every class without per-class code. Survival: stress and feasibility get their own limits.
- Evidence chain: SIMM buckets (live), pooled volatility out-of-sample result (A5-097, author). Weakest link: the class worst-step table.
- Maturity: **solid**.

**X2-H48. Tick-size tier limits by signal horizon.**
- Links: A3-236 (trend decay by tick size), A1-163.
- Need: N10.
- What and how: Caps for fast-trend units are set per instrument tier of volatility-normalised tick size and signal horizon, not per class: small-tick markets, where fast trend decayed most after 2009, get lower caps for fast-trend units.
- Levels: instrument, unit.
- Per class and style: futures first; applies to CFDs and crypto contracts by tick over volatility.
- Ledger: `price_increment`, `instrument_class`; new *tick_size_tier*.
- Performance: keeps trend units where they still pay. Survival: smaller exposure where the edge measurably decayed.
- Evidence chain: about 100 futures, 1995-2025 (author backtest). Weakest link: the mechanism is proposed, not proven.
- Maturity: **wild** (a seed).

**X2-H49. Contract-lumpy ladders: levels as whole contracts, faster down than up.**
- Links: A5-125 (fixed ratio, cutting faster on the way down), A5-123, A1-153, A5-042 (zero if the minimum is too big).
- Need: N09, N13.
- What and how: Where one lot is large next to the budget (futures, index CFDs at small equity), the level map (H13) becomes whole contracts: 0, 1, 2, 3. A level is zero when one contract breaches the level's risk. Steps up need more profit per added contract than the last (fixed ratio); steps down come faster.
- Levels: unit.
- Per class and style: futures, index CFDs, metals contracts.
- Ledger: `size_levels`, `min_lot`; reuses *size_level_fraction_table*.
- Performance: a working ladder where fractions do not exist. Survival: no rounding up to a contract.
- Evidence chain: Ryan Jones fixed ratio (snippet). Weakest link: formula disputes.
- Maturity: **plausible**.

### J. Demo and live alike

**X2-H50. The deployment carries share, costs and level; the demo balance is never read.**
- Links: A1-130 (budget share carried by the deployment), A4-036 (one code path), A2-124 (world-switch reset), A4-035 (paper twin with a per-trade gap row), A4-028 (three-stage gaps), A1-146 (one cost ledger), A4-167 (slippage from node order rows).
- Need: N11, N04, N13.
- What and how: Every deployment (paper, demo, live) carries: its budget share of the live allocator's equity, refreshed at each anchor; the cost model for its world; its level. The sizer reads share × allocator equity in every world, never the demo account's balance. On a world switch: house money is zero, the level drops to L1 (or keeps one level lower on his card), costs count as uncalibrated (stressed default) until N live fills. A paper twin keeps running beside each live unit on the same signals; the per-trade gap between twin and live is the source of the live slippage term until enough live fills exist.
- Levels: unit, deployment.
- Per class and style: cTrader demo fills come from the broker's demo server (a weak stand-in); Hyperliquid testnet differs from mainnet liquidity; crypto spot simulation fills at the recorded bid or ask.
- Ledger: `unit_capital_share`, `paper_starting_balance`, `paper_to_live_carry_rule`, `sizing_equity_basis`, `slippage_cost`; new *budget_share_refresh_interval*, *live_cost_gap_multiplier*, *world_switch_reset_rule*.
- Performance: paper results translate into live money. Survival: no demo-sized position goes live.
- Evidence chain: the unit build's one-path design (built), Algo-trading three-stage benchmark (live, 4 weeks). Weakest link: DOCS freezes a paper balance "for data-collection realism", which this overrides (collision X2-C09).
- Maturity: **solid**.

### K. Self-configuring machinery

**X2-H51. VPA for sizing inputs: learner with bounds, applier with modes, direction-split motion, guarded guesses.**
- Links: A4-001 (learner with low and high bounds), A4-002 (applier modes), A4-003 (applier limits), A4-004 (direction-split motion), A4-006 (guarded guess with freeze), A1-060, A1-062 and A4-080 (shipped motion engine), A4-054 (derivation block with receipts), A1-063 (fallback ladder), A4-197 (cadence by layer), A4-015 (borrowed priors), A2-036.
- Need: N12, N01, N16.
- What and how: The formula (H01 and friends) stays fixed per profile version; its inputs move. Each input (s, the edge band, costs per hour, ρ, trade rate, gap factor) has a learner that publishes target, low and high from the unit's decayed record (half-life in trades, not hours). An applier applies it in the mode he picks per input: Off (shadow rows only), Initial (at the next anchor or flat), Live. Motion is direction-split: inputs that make size smaller (higher cost, higher ρ, larger s) apply at once; inputs that make it larger wait a window and a rate cap. Each learned value has a guard (cost calibration fresh, record long enough, regime unchanged); a tripped guard reverts to the fallback ladder's value (own record → class default → preset default) with a named reason, and K trips freeze it.
- Levels: unit, instrument.
- Per class and style: half-lives in trades suit scalpers; swing units need calendar floors too.
- Ledger: `number_motion_mode`, `calibration_min_trades`, `calibration_shrink_k`, `calibration_cadence_trades`, `risk_fraction`; `x1_number_authority_mode` (X1's); new *tuned_input_guard_trip_limit*.
- Performance: numbers follow the unit's own record instead of placeholders. Survival: every guess has a way back and a freeze.
- Evidence chain: Kubernetes VPA and HPA, HotSpot (production software, checked in R7). Weakest link: the compiler refuses sizer-bound moving numbers today (G8 §3.10).
- Maturity: **solid** (pattern), needs compiler format 2 (X1-56).

**X2-H52. Simplex fallback sizer: an edge-relaxed sizer inside a safe region, the zero-edge sizer at its edge.**
- Links: A4-007 and A2-037 (Simplex with dwell), A2-038 (failed tune reverts), H01, H03.
- Need: N02, N07, N19.
- What and how: The performance sizer (H01 with drift at the low or mid edge, or H05) runs while the projected next state stays inside a safe region (committed cushion above a share of D, no brake within m losses). If the next trade could leave the region, the zero-edge closed form takes over for a dwell of trades before control returns.
- Levels: unit, book.
- Per class and style: the region's width uses the class worst step, so gappy classes switch earlier.
- Ledger: `number_motion_mode`, `kill_line_distance`; new *fallback_dwell_trades*.
- Performance: lets an aggressive sizer run most of the time ("performance with intention"). Survival: a verified fallback near the edge.
- Evidence chain: Simplex architecture (control engineering, secondary paper). Weakest link: gaps leave the region in one step.
- Maturity: **plausible**.

**X2-H53. Conservative bandit over a few approved sizing profiles.**
- Links: A4-199 (online choice among approved configurations), A5-037, A5-026 (ring-fenced exploration), A5-162 (workflow), A4-126 (fixed screening rules).
- Need: N12, N19.
- What and how: Three or four sizing profiles he has signed (zero-edge horizon, low-edge horizon, low-edge with AIMD, cushion pair on) are arms; the default is the baseline arm. A conservative bandit switches live only while cumulative result stays above a baseline-relative floor, inside a ring-fenced exploration budget; stale rewards are discounted (rotting bandits).
- Levels: unit.
- Ledger: `number_motion_mode`; new *exploration_risk_budget_usd*.
- Performance: a unit can move to a better profile without a new version per move. Survival: exploration cannot cost more than its fence.
- Evidence chain: bandit theory (no trading test). Weakest link: nonstationary markets break the guarantee.
- Maturity: **wild**.

**X2-H54. Agent-bred sizing genomes judged by resize replay, tries counted.**
- Links: A4-182 (profiles as a genome inside ranges), A1-170 (resize replay), A5-024 (allocator ablation), A1-027 (post-selection shrink), A4-126.
- Need: N18, N12.
- What and how: Agents mutate a sizing profile inside his ranges (H, ε dial, edge point, AIMD factors, house-money share, tier widths), evaluate each by resize replay plus the scenario battery and the dry chassis, count every variant, shrink the winner toward the pool, and propose the survivor on a card. Nothing reaches the order path without his signature.
- Levels: profile (unit or preset).
- Ledger: `effective_tries`, `number_motion_mode`.
- Performance: finds sizing shapes nobody would try. Survival: a risk search overfits like a signal search; tries and shrinkage are the guard.
- Evidence chain: WF1 and WF2 variant pipeline (old system, by analogy). Weakest link: overfitting to the replayed period.
- Maturity: **wild**.

**X2-H55. Book-volatility thermostat.**
- Links: A4-009 (self-tuning block with hard output limits), A1-011, A5-129, H02.
- Need: N14, N12.
- What and how: One controller holds the book's realised day-sigma at the σ_book target H02 derives, by moving a single global scale on every unit's size, with anti-windup, hard output limits and a chosen error reaction (hold the last scale on bad data, never raise).
- Levels: BMS.
- Ledger: `volatility_target`; reuses *book_day_sigma_budget_usd*.
- Performance: the book uses its whole allowed swing. Survival: never above target by more than the controller's error band.
- Evidence chain: industrial PID practice. Weakest link: realised day-sigma from few days is noisy, so the loop may chase noise.
- Maturity: **wild**.

### L. Sweeps, re-seeds and the 24-hour growth question

**X2-H56. Gain-lock ratchet with sweeps only at the BMS and a conservation buffer.**
- Links: A1-037 (cushion under a rising floor), A1-077 (raise the base, send the rest elsewhere), A1-076 (sweep above a high-water mark at book or BMS), A2-077 (a unit-level sweep removes the unit's cushion), A1-075 (2.5x cycle cap), A5-105 (sweep and re-seed defined), Basel capital conservation buffer (cross-pollination).
- Need: N14, N19, his C12 and B10.
- What and how: At each BMS anchor the floor rises by φ × (any gain above the last high-water mark); φ = 0 is pure compounding on a fixed floor (cushion leverage, an accelerator by anchor), φ = 1 is a trailing floor (pure brake), between is time-invariant portfolio protection. Sweeps out of the risk zone happen only at the BMS and only above the high-water mark; units are never swept, so their brakes keep their cushion. While equity sits inside the BMS buffer above the floor, no sweeps, no accelerators, and re-seeds only priced (H57). This answers "is the sweep cap coming back": a smooth ratchet instead of a 2.5x cliff.
- Levels: BMS, book.
- Ledger: `rising_floor_fraction`, `high_water_mark_equity`, `sweep_cap_equity`, `cap_multiplier`, `bms_buffer_before_floor`, `portfolio_floor`; new *gain_lock_fraction*.
- Performance: nothing idles; growth compounds on the cushion. Survival: part of every new high is locked.
- Evidence chain: TIPP and CPPI theory (Grossman-Zhou, READ in R9), fund high-water marks (live), Basel buffers (live). Weakest link: φ is his money choice (Q5).
- Maturity: **plausible**.

**X2-H57. Priced reinstatement and a premium-funded restore reserve.**
- Links: A5-130 (reinstatement for a charge), A1-078 (refund reserve), A5-105, A1-064 (loosen only on proof).
- Need: N14, N06.
- What and how: Every accelerator raise pays a premium (a share of its expected extra profit, booked from realised gains) into a restore reserve. A unit or book that spent its budget can be refilled only from that reserve, at a price proportional to the amount used and with a proof requirement (an e-value on post-cut trades) that grows with the refill. Free refills do not exist.
- Levels: book, BMS.
- Ledger: `refund_reserve_rho`, `refund_reserve_cycles_per_month`, `book_seed_capital`; new *reinstatement_price*.
- Performance: a good unit gets its budget back after a loss without waiting for him. Survival: a broken unit cannot be refilled for free.
- Evidence chain: reinsurance reinstatement practice (snippet). Weakest link: no QMX analogue; the premium share is a guess.
- Maturity: **wild**.

### M. Agents, the Lab and MCP

**X2-H58. Agent sizing proposals: de-risk applies, raise shadows (with credit-line pacing).**
- Links: A1-132 (de-risking-only agent scale aggregated by a service), A1-131 and A4-131 (code-built size, agents write intent), A1-122, R9 §3.1 credit-limit warning, A4-147 (propose, shadow, card, click).
- Need: N18, N12.
- What and how: Agents and the copilot reach sizing through two typed, expiring proposals. A risk scale in [0, 1] (de-risk) is aggregated by a deterministic service and applies at once, capped per unverified item. A raise proposal (new edge point, new tier, new profile) goes to shadow rows and a card for his click. A proposer that always asks for more gets the slowest line (credit-limit research: the party that most wants more limit is the one for whom it is least profitable). The Lab reads the same `decide`, `on_event` and `state` verbs in simulation; MCP tools read `RiskState` and write proposals; neither is in the order path.
- Levels: unit, book.
- Ledger: `context_size_modifier`, `decision_freshness_bound`; new *agent_risk_scale_proposal*.
- Performance: agent context can only cut size, so gains come from avoided losses. Survival: agents never add risk.
- Evidence chain: Steward paper-account run (controlled, 102 days). Weakest link: many agents reading one feed are one agent.
- Maturity: **solid** (de-risk), **plausible** (raise path). QMA changes flagged, not designed.

**X2-H59. The Lab pod as a template consumer: allocator slot, shadow ablation.**
- Links: A5-024 (shadow allocator and ablation), A5-020 (bounded learned tilts), LAB seven-slot pod (G8 §6.2), H28, H29, H31, H32.
- Need: N18, N05.
- What and how: The Lab's pod slots map onto the template: allocator = one of H28, H29, H31, H32 as a block; caps = clamps; guards = brakes; sizer = H01. The Lab runs the same units under rival allocators, ablating signal alone, signal plus static budget and signal plus adaptive allocator, and reports whether the adaptive layer earns its place after costs.
- Levels: BMS, book.
- Ledger: `capital_sharing_rule`, `slot_rebalance_rule`.
- Performance: allocators are compared on QMX's own units. Survival: nothing in the Lab touches money.
- Evidence chain: design only. Weakest link: the Lab is unbuilt.
- Maturity: **plausible**.

### N. Guards and seeds

**X2-H60. Martingale firewall and a hidden-ruin audit.**
- Links: A1-008 (martingale, grid, averaging-down), A1-172 (hidden risk-of-ruin audit), A5-115 (contrarian accelerator, flagged), A1-073.
- Need: N20, N06.
- What and how: Size may not rise after a loss unless a declared contrarian accelerator says so on a card. A nightly audit scans each unit's trade history for escalation after losses (next size ≥ 1.3x), stacking at worse prices, payoff asymmetry and classical ruin, and grades it A to F; a D or F stops accelerators for that unit.
- Levels: unit.
- Ledger: `payoff_ratio`, `win_rate`, `risk_fraction`; new *size_escalation_after_loss_forbidden*.
- Performance: none. Survival: catches martingale-like sizing before it ruins.
- Evidence chain: MQL5 failure-family backtests (author). Weakest link: none; it is a guard.
- Maturity: **solid**.

**X2-H61. Meta-label probability to size, inside the budget.**
- Links: A5-044, A5-074, A1-033 (active-bet averaging, discrete steps), A5-158.
- Need: N02 (a unit-side option), N15.
- What and how: For units with a calibrated probability: expected net value = p × G − (1 − p) × L − C, with G and L from comparable trades (FI cuts included); trade only above a hurdle; size = budget × a discrete step of how far p sits above break-even, averaged over active bets so concurrent signals do not stack. Never probability times maximum size.
- Levels: trade, unit.
- Ledger: `win_rate`, `average_win_r`, `mean_loss_r`, `round_trip_cost_r`, `breakeven_win_rate`.
- Performance: skips the trades where thin edges leak to costs. Survival: size is capped by the budget whatever the model says.
- Evidence chain: López de Prado-style meta-labelling, author backtests. Weakest link: calibration drifts.
- Maturity: **plausible** (a unit seed as much as a sizing rule).

**X2-H62. Macro-state class gross multiplier (regimes cut gross, never re-weight).**
- Links: A1-015 and A3-042 (class cap × macro state × volatility and liquidity), A2-045 (lower fast, raise slowly, stale falls back conservative), A1-100 (regimes cut gross), A3-041.
- Need: N05, N20.
- What and how: Each class's gross cap = approved cap × macro-state multiplier (slow layer, daily and at releases) × volatility and liquidity multiplier (fast layer), lowered fast, raised slowly with hysteresis; stale inputs fall back to a conservative state. Regimes cut gross per class; they never re-weight units inside a class.
- Levels: BMS, class.
- Ledger: `cluster_exposure_cap`, `cross_market_stress_reading`, `context_size_modifier`; new *class_state_multiplier*.
- Performance: calm states run at full approved size. Survival: a shock state cuts every class together.
- Evidence chain: NCO regime test (author: regime re-weighting lost), assistant starting tables (unvalidated). Weakest link: one noisy classifier switching the book.
- Maturity: **plausible**; overlaps X3's isolation, which owns switching a class off.

---

## 2. Problems and solutions

Diagnosis for each (refined statement, is/is not, five whys, forces) is in `linking/stage-b/X2-sizing-accelerators/problem-solving.md`. No pick here.

| # | Problem | Option | How | Trade-off |
|---|---|---|---|---|
| PS1 | Risk per trade has no derivation | A. Horizon floor-odds sizer (H01) | Survival over H trades at zero edge; edge relaxes it | Needs D, ε, H, s, ρ as facts; Brownian approximation |
| | | B. Risk-constrained Kelly from his (α, β) (H05) | Fraction that spends exactly his floor tolerance | Leans on a return model; edge-led |
| | | C. Day-sigma budget (H02) | Book's daily swing from the cushion, per-trade by √n | Needs a reliable trade rate per unit |
| | | D. Keep a typed fraction with a reason row | His value, receipt says "stated" | Carries no weight by his own rule (D29) |
| PS2 | Edge-led against frequency-led | A. H01 with the edge dial (H03) | Zero edge by default, low or mid after proof | Grows slower than full Kelly at the believed edge |
| | | B. Own full size under a parent (H29) | Lead's 1 Nov view, made safe by co-loss factor | Parent binds late in stress |
| | | C. His literal split (A1-088) | Day risk ÷ N | Sitting duck: 1/2.8 of H01's growth at equal safety in the sim |
| | | D. Breadth-to-budget (H28) | √-scaled shares on residual ρ | Correlation estimates from short histories |
| PS3 | Costs never reach the sizer | A. Cost triple (H39) | Denominator, Kelly in R, gate, per hour and world | Needs a cost input on the socket and a commission key |
| | | B. Cost only as a gate (A1-138) | Trade or not; size unchanged | Over-sizes in costly hours |
| | | C. Cost through the edge only | Size on net edge | Hides cost from the receipt; no per-hour effect |
| PS4 | Which equity the sizer reads | A. Asymmetric basis (H44) | Committed cushion for size, marked for brakes, realised for accelerators | Four rows to maintain; needs marked equity live |
| | | B. One series: marked equity | FTMO style | Presses on open profit |
| | | C. One series: realised balance | Stable | Ignores open losses; the fourth trade over-sizes |
| PS5 | Accelerators have no proof | A. Proof card (H20) | Resize replay against an equal-average constant | Needs resize replay; slow for thin units |
| | | B. Persistence gate (H19) | Block test before switch-on | About 950 trades for a 500-trade regime |
| | | C. Ship only cushion leverage and tiers | Theory and live practice back them | Gives up persistence presses |
| PS6 | Accelerators drive into trips | A. Raise permission gate (H24) | Headroom, any-brake-blocks, burn permit, memory | brake_state must exist |
| | | B. AIMD with memory (H26) | Pair built into one rule | Mostly a brake (0.79x average) |
| | | C. Nomogram (H25) | Dead band and asymmetric speeds | Calibration per unit |
| PS7 | House money scope and correlated wins | A. Book ledger with an event window (H11) | One event funds once | Less responsive per unit |
| | | B. Unit ledger with a book cap (A1-068) | Unit earns its own | Still fires on shared moves unless windowed |
| | | C. BMS only | One place, one cap | Slowest; far from the unit's own record |
| PS8 | Minimum lots at small equity | A. Feasibility-first admission (H45) | Instrument paper until feasible | Fewer classes at $500 |
| | | B. Lot dither (H46) | Average risk on target | Single trades up to 1.5x plan |
| | | C. Fewer, larger units at $500 | Breadth later | Less frequency, against his C1 |
| | | D. Pool cushion across units with QoS borrowing (H30) | Idle budget lifts a unit above min lot | Borrowers evicted under stress |
| PS9 | Demo sizes from the demo balance | A. Deployment carries share, costs, level (H50) | Demo sizes from live share | Overrides DOCS frozen paper balance |
| | | B. Demo account funded to the live share | Broker-side fix | Not possible on most demos; drifts |
| PS10 | New units too safe or too risky | A. Zero-edge start (H01) plus titration (H14) | Trades from day one at a size safe without edge | Probation still costs growth |
| | | B. Level map with BOIN cohorts (H13) | Evidence moves levels | Slow for swing units |
| | | C. Conservative-UCB probe (H17) | Bounded-cost exploration | Relative floor can pass a losing book |
| | | D. His calendar ramp (A1-055) | Kelly over about a month | Ignores evidence speed |
| PS11 | Normalising across classes | A. Three-number sleeve record (H47) | Routine, stress, feasibility | Needs X4's worst-step table |
| | | B. Volatility units (A1-011) | Equal money swing | Equalises routine risk, not tails |
| | | C. Money at the stop only (A1-160) | R in dollars | Misses gaps and margin |
| PS12 | 24-hour growth, sweeps, restarts | A. Anchor clocks (H12) plus gain-lock ratchet (H56) | Per-scope anchors, φ ratchet at BMS | φ is his choice |
| | | B. Return the 2.5x cycle cap at Book and BMS (A1-075) | Known shape | A cliff; per-cycle clash with 24 h (B5) |
| | | C. Pure compounding, no sweep | Simplest | Floor never rises; cushion leverage grows unchecked |
| PS13 | What a level is in dollars | A. Fraction of derived baseline (H13) | Levels move with the cushion | Two mechanisms (level and baseline) on one size |
| | | B. Fixed dollar ladder per level | Easy to read | Typed numbers, no derivation |
| | | C. Whole contracts for lumpy classes (H49) | Natural steps | Only for coarse classes |
| PS14 | Shipped sizer contract and compiler | A. Widen the sizer inputs and allow derivations to move sizer-bound numbers (restructure R3) | X1-56, X1-58 | Compiler format change |
| | | B. Keep the sizer narrow; precompute everything at anchors into one "size budget" number the sizer reads | Smallest change | Receipt loses per-input detail |
| PS15 | FI cut sizes in the maths | A. s and mean loss from the unit's own cut distribution (H01, H04, H10 count cuts by size) | Every formula reads R in money | Trade rows must carry exit mechanism (X1-59) |
| | | B. Class or style default cut distribution until measured | No blank | A guess with a reason |
| PS16 | Self-configuring without overfitting | A. VPA pattern (H51) | Learner, modes, guard, freeze | Compiler change |
| | | B. Conservative bandit over signed profiles (H53) | Few arms, fenced | Wild |
| | | C. Agent genomes with counted tries (H54) | Search with shrinkage | Overfits the replay period |
| PS17 | Multi-position units stacking | A. Bet key and basket cap (H34) | One bet once | Undeclared shared drivers escape |
| | | B. Residual correlation at position level | Measured, not declared | Needs history per position pair |

---

## 3. Collisions

Named, not resolved.

- **X2-C01. Zero-edge default against wasted edge.** H01 and H03 default to zero edge; Hal (roundtable) and A1-017/A1-030 say that wastes a measured edge; his A24 says don't lean on it. The dial is the collision.
- **X2-C02. Breadth against the minimum lot at $500.** H28 and H35 shrink per-unit size as units are added; at $500 many shares fall below one lot on gold, index CFDs and futures (H45). His C1 frequency thesis and his $500 seed pull against each other here.
- **X2-C03. Fixed anchor against trailing anchor at one scope.** H10 with a fixed anchor accelerates; H56 at φ = 1 or A1-037 trails and never accelerates. One scope cannot hold both.
- **X2-C04. House money at unit (H10) against book (H11) against BMS.** His C5 leaves it open; X3's brake scopes depend on it.
- **X2-C05. Probation levels against "too safe".** H13 and H14 keep new units below baseline; his A14 rejects low-end sizing; A1-055 wants a month to Kelly. A swing unit may take months to climb.
- **X2-C06. Unit sizing follows edge, not equity (A5-012, H27), against a unit-level money ledger (H10).** If equity cuts belong to the book, the unit's reverse house money is in the wrong place.
- **X2-C07. Measured-cost hour map against session multipliers and premium windows.** H40 deletes the free lift; April's 1.2x premium windows (A1-069) and his "sniping windows get more if there is proof" (D8) keep it.
- **X2-C08. Marked equity in H44 against the shipped stack.** cTrader equity is read once at sign-in (G9 §3.3); halt blocks assume marked equity no host supplies (G11).
- **X2-C09. Budget share in every world (H50) against DOCS's frozen paper balance "sized for data-collection realism" (G6 §5.5).**
- **X2-C10. VPA-moved sizing inputs (H51) against the compiler (G8 §3.10): a sizer-bound number cannot move.**
- **X2-C11. Smallest-wins stack (H06) against the April handbrake (his C25).** A min of many caps can choke size; it is only safe with the binding-clamp audit.
- **X2-C12. Any automatic raise above baseline (H18, H19, H22, H26 above 1.0x) against Dana's (and pod practice's) "no automatic restore, the firm resizes" and his Q4.** R9: no accelerator beats a constant on independent trades.
- **X2-C13. Full size under a parent (H29) against breadth-to-budget (H28).** Same units, different sizes; his C29 sits between, the lead's 1 Nov view on H29's side.
- **X2-C14. Agents de-risk only (H58) against the agent-department vision (M35) where agents propose sizes and strategies.** QMA flagged, not designed.
- **X2-C15. Per-scope anchor clocks (H12) against one running `day_boundary` and the kill switch's daily counters.**
- **X2-C16. Worst-step moves (H07, H47) come from X4's scenario table; this layer cannot set them.** Dana: model gaps are not real gaps.
- **X2-C17. Planning edge for sizing (H03: zero by default) against X5's planning edge for proof (deflated holdout, half as fallback, A2-187).** Two different "planning edges".
- **X2-C18. AIMD grow-when-used (H26, H31) rewards trading more, while X3's count brakes punish it.**
- **X2-C19. Calm-volatility scaling (H22) against stop-based R.** For stop-sized units R already normalises volatility; scaling again double-counts.
- **X2-C20. Proof cards need resize replay (H20, H16, H54); QMX's judge is size-blind (G8 §5.3).**
- **X2-C21. His expectation that house money and Kelly are reasons to raise size (A13) against R9's finding that house money adds no growth per risk without persistence.** He may expect more from accelerators than they give.
- **X2-C22. H01 replaces the Book ladder's divisor (n × B × b × L̄) against "the Book is the skeleton" (B3).** The skeleton stays; its number changes.
- **X2-C23. Lot dither (H46) against "never round up" (A1-153, A3-002).**
- **X2-C24. Demo-to-live level reset (H50, A2-124) against his A1-055 ramp and the unit build's "live starts from paper's last calibrated values" (paper_to_live_carry_rule).**
- **X2-C25. A missing cost cell: X0's `hourly_cost_profile` refuses sizing; H39 and the roundtable use a stressed class default that decays toward measured.** Refusing is honest but starts every new market as a sitting duck; the default trades but on a guess.

---

## 4. Restructure proposals

1. **Replace the Book ladder's price of R with the horizon multiplier.** What replaces: risk per trade = usable cushion ÷ (s × z × √H × B) (H01), cached at anchors; the Book stays as the scope of a cushion ledger, the kill line stays a clamp. Why it performs better: the ladder's 1/7 of cushion per R survives about 7 to 10 trades at zero edge, prices every seat at full size regardless of how many seats trade, and in the sim touched the floor on 17-97 % of paths with ten seats; the horizon multiplier is derived, scales with correlation and kept zero touches with 2.8x the 1/N split's growth.
2. **Replace April's nine-multiplier chain** with one baseline (H01), one cushion pair (H10), one cost triple (H39), one optional context modifier slot with priority (A4-014), and a smallest-wins clamp stack that names its binding clamp (H06). Why: the chain's multipliers did each other's jobs (his C25) and sat inert under one cap; fewer, derived pieces show which one costs growth.
3. **Widen the shipped sizer contract** (G8 §1.4; X1-58): inputs = budget share, committed cushion, open risk per bet key, the unit's record (s, edge band, cut distribution, trade rate), cost profile for this hour and world, gap factor, level, trading state; output = size plus a receipt naming the binding constraint. Plus compiler format 2 so sizer-bound inputs move through derivations with applier modes (X1-56). Why: every hybrid here needs at least one of these inputs; none can run on equity, entry and stop alone.
4. **House money to one declared scope, default the book ledger with an event window (H11); retire the count form of reverse house money** (streak tiers) into X3's event ledger, keeping the money form as the brake half of the cushion pair (H10). Why: R9 shows the old pair was not a pair, and count forms punish FI units.
5. **Delete session multipliers and premium-window lifts** in favour of the measured-cost hour map (H40). Why: windows lower cost; a separate lift pays twice.
6. **Replace frozen paper balances with the budget share carried by the deployment** (H50). Why: paper results then translate into live money.
7. **BMS: replace the fixed $300/$200 style split with poker-band pots and QoS classes** (H37, H30), with the allocator itself a pluggable block the Lab can swap (H59). Why: "if the capital allows" becomes a rule, idle pots lend, proven units keep size under pressure.
8. **Replace the 2.5x cycle cap and sweep with a gain-lock ratchet at the BMS** (H56), never sweeping units. Why: no cliff, no idle reserve, units keep the cushion their brakes read.

---

## 5. Gaps (no component covers)

- No measurement of win or regime persistence in intraday retail-style strategies after costs (R9 gap); H19 cannot switch on until QMX measures its own.
- No slippage measured anywhere; no commission key; no cost input to the sizer (G6 §5.4, G7 §4.3).
- No worst-step move table per class and hold for retail instruments (X4 must supply).
- No real-data test of the horizon sizer; only my model sim.
- No resize replay in QMX.
- No QMX analogue for pricing a re-seed; reinsurance only.
- Stock borrow and futures roll in the sizer: no component.
- Multi-leg baskets (pairs, spreads, hedged positions) sizing: none.
- Margin increases in stress (margin calls before a drawdown rule reacts): modelled nowhere.
- A fair control for agent-proposed sizes: none.
- Perps: how funding, liquidation price and the stop interact in one size: partial (A1-158 only).
- Live currency conversion inside the sizer: planned, not built.
- How the unit count N and correlation ρ are measured for units that are on and off at different hours: no component.
- Per-session and per-timeframe records do not exist (records split per market only, G7 §5.3), so every "per hour" sizing input needs a new record shape.

---

## 6. Questions only he can answer

1. **How rare is "almost never"?** The floor-touch tolerance ε, as a chance per year (money; it sets z in every size).
2. **The first floor level.** How much of the $500 sits below the floor for the first live run (his "levels"; it sets D).
3. **Where house money lives.** Unit, book or BMS (his C5).
4. **Raises above baseline.** May a rule raise size above the derived baseline by itself (tiers, persistence), or is every step above baseline his click? Restores up to baseline would stay automatic.
5. **The ratchet.** What share of each new high should lock into the floor (φ in H56; 0 is pure compounding, 1 is a trailing floor)?

---

## Appendix A. The simulation

Script: `linking/stage-b/X2-sizing-accelerators/sims/horizon_sizer.py`. Outputs: `out-1000.txt` (no gaps) and `out-1000-gaps.txt` (2 % of days, every unit's first trade gaps −3R at once). Model: $500 seed, $300 floor, 60 days, 10 trades a day per unit, wins +1R, half of losers cut at −0.35R and half at −1R, believed edge +0.08R (s ≈ 0.87), one or ten units, correlation of wins 0 or 0.3 through a common factor, size set each morning and held for the day, 1,000 paths. Horizon sizers use ε 1 %, H 200 rounds, planning ρ 0.3. These are model numbers **[arithmetic]**.

Floor touch rate and median final equity, ten units, ρ 0.3:

| Policy | Believed edge | Half edge | Zero edge | Half edge, gap days |
|---|---|---|---|---|
| Fixed 1 % per unit | 2.2 %, $28,719 | 18.7 %, $2,600 | 78.7 %, $298 | 30.7 %, $1,558 |
| 1 %/N split (his literal split) | 0 %, $796 | 0 %, $630 | 0 %, $494 | 0 %, $609 |
| Half Kelly on the point edge | 97.7 %, $300 | 100 %, $271 | 100 %, $218 | 100 %, $238 |
| GitBook ladder, D/7 per seat | 88.3 %, $299 | 92.0 %, $300 | 97.3 %, $300 | 97.4 %, $297 |
| Horizon sizer, zero edge (H01) | 0 %, $2,213 | 0 %, $882 | 0 %, $466 | 0 %, $782 |
| Horizon sizer, half edge (H01 + H03 low) | 0 %, $5,854 | 0 %, $1,202 | 0 %, $432 | 0 %, $979 |

One unit: both horizon sizers touched 0 % in every case; fixed 1 % touched 1.6-2.7 % at zero edge; half Kelly 18-84 %. The horizon sizers spend more time inside the buffer (below $400) than fixed 1 % with one unit, which is the price of their higher growth (zero edge: 41 % against 32 %).

What it does not show: fat tails beyond the injected gap days, serially correlated results, learning of the edge, costs beyond the win rate, minimum lots, intraday re-sizing. Recomputing size each morning from the cushion makes every cushion-proportional rule hard to drive through the floor except by one day's loss exceeding the cushion, so "0 % touch" is partly structural; the H07 reserve is what covers the one-day hole.

## Appendix B. Roundtable digest

Full transcript: `linking/stage-b/X2-sizing-accelerators/roundtable.md`. Personas: a pod-shop risk manager, a retail scalper, a platform engineer, a betting-syndicate quant, a reinsurance actuary, and his voice from his recorded words. What changed in the hybrids because of it: H01 caches its multiplier at anchors with the zero-edge form as fallback; H07's reserve widened from N-1 to probable maximum loss per exposure zone; H45 orders admission by feasibility; H46 gets a news-window exclusion and stays wild; H10's accelerator half ships off until H20 passes; H11 is house money's default home; H24 never lets a restore cross baseline; H26 thresholds are in the unit's own percentiles; H39 uses a stressed default for uncalibrated costs; H40 deletes the session multiplier; H44 adds the floor-clip row; H50 takes the live slippage term from the paper twin gap. Unresolved: X2-C01, X2-C02, X2-C12.

## Appendix C. Solution matrix (problems against component families)

✓ = a component in that family addresses the problem; blank = no component. Families: K Kelly (A1-016..030, A5-016, A5-084), C cushion and drawdown (A1-036..047, A2-012, A5-118), L levels and ramps (A1-052..061, A5-039, A5-127), Acc accelerators (A1-065..073, A5-119..135), P pairing (A5-133..141), Al allocation (A1-084..107, A5-001..027), Co costs (A1-138..152, A3-004..007, A3-084), Lo lots and margin (A1-153..159, A5-042, A5-096), N normalisation (A1-160..167, A3-001, A5-097), S self-config (A4-001..015, A4-195..199), D demo/live (A1-130, A4-035, A4-036, A2-124), Sw sweeps (A1-074..078, A5-105, A5-130).

| | K | C | L | Acc | P | Al | Co | Lo | N | S | D | Sw |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PS1 baseline | ✓ | ✓ | | | | | | | | ✓ | | |
| PS2 edge vs frequency | ✓ | ✓ | | | | ✓ | | | | | | |
| PS3 costs | ✓ | | | | | | ✓ | | ✓ | | ✓ | |
| PS4 equity basis | | ✓ | | | | | | | | | ✓ | |
| PS5 accelerator proof | | | | ✓ | | ✓ | | | | | | |
| PS6 pairing | | ✓ | ✓ | | ✓ | | | | | ✓ | | |
| PS7 house money scope | | ✓ | | ✓ | | ✓ | | | | | | |
| PS8 min lots | | | ✓ | | | | | ✓ | ✓ | | | |
| PS9 demo sizing | | | | | | | ✓ | | | | ✓ | |
| PS10 new units | ✓ | | ✓ | | | | | | | ✓ | ✓ | |
| PS11 classes | | ✓ | | | | ✓ | ✓ | ✓ | ✓ | | | |
| PS12 24 h growth | | ✓ | | | | | | | | | | ✓ |
| PS13 level dollars | | | | | | | | ✓ | | | | |
| PS14 sizer contract | | | | | | | | | ✓ | ✓ | | |
| PS15 FI cuts | ✓ | ✓ | | | | | | | | | | |
| PS16 self-config | | | | | ✓ | | | | | ✓ | | |
| PS17 multi-position | | ✓ | | ✓ | | ✓ | | | | | | |

Empty cells worth naming: no accelerator component addresses costs (accelerators ignore that boosts raise cost in money); no levels component handles demo (levels reset on world switch only in A2-124); no sweep component reads correlation (a sweep after a correlated win banks a correlated profit); PS13 has only lot mechanics, no level design.
