# X6: observability, telemetry and what the UI must show

Stage B layer X6, 3 Nov 2026. File id `X6-observability`. Brief: `linking/STAGE-B-BRIEF.md`.

His question (D49, M12): "how do we know that this is wrong, this is right, it's working, it's up, it's on ... Then, you know, it's trading." And C7: "We need to be able to know what is breaking."

**How to read this.**
- Component ids are short: `A4-152` means `linking/components/A4-template-agents-telemetry.yaml`, id `A4-template-agents-telemetry-152`.
- Hybrids are `X6-01` to `X6-47`. Maturity tags are hints for the funnel judge, not a ranking.
- **[judgment]** marks my own opinion. Everything else cites a component, a grounding file or his words.
- New ledger ids live in `ledger/additions/X6-observability.yaml`. Ids already in `ledger/variables.yaml` are reused and marked (v0).
- Method record: `linking/stage-b/X6-observability/` holds the memlog (163 entries, 140 ideas), `problem-solving.md`, `roundtable.md` and `brainstorm-intent.md`.

**Counts.** 47 hybrids: 21 solid, 21 plausible, 5 wild. 12 problems. 19 collisions. 7 restructure proposals. UI requests for 16 screens. 58 new ledger variables.

---

## 0. The ground, in ten lines

1. The node reports health, not risk: no equity, drawdown, exposure, open risk, budget used, brake state or drift (G11 §0.10).
2. The only on-path risk brake is the kill switch, raised and lowered by his hand. The risk-stop pipe is built and nothing feeds it (G9 §0.1-0.2).
3. A risk stop is filed as `kill_switch` because reason text is mapped to codes by first match (G9 §1.4).
4. A time exit, a signal exit and an FI cut all read `close` on the trade row (G11 §3.4). FI never existed in code.
5. The node journals a kill-level rise but not his lowering, so the watcher cannot show the level now; `paused` is always 0 (G11 §4.1).
6. Pushes (C-18) fire mostly while a market they concern is open. The risk-stop push can never fire (G11 §4.1).
7. Slippage is measurable from node order rows; no script reads it. Paper fills have zero slippage (G9 §3.1, §3.4).
8. Drift pieces (cone, decay check, replay) all inform; nothing acts (G9 §7.3).
9. Journals reach This PC every 60 s (open month) or 300 s (server nodes) (G11 §4.1).
10. Telemetry shipping is off by default; two monitoring stacks ship, unresolved (A4-169).

---

## 1. The words: precise meanings

These are predicates over the `RiskState` fold (X6-01), per scope (unit on a market, unit, book, account, node). Each has a freshness limit (`risk_fact_staleness_limit`). Past it the word is **UNKNOWN**, shown grey, never the last colour. This is X6-11 in full.

| Word | True when | Inputs | False shows as |
|---|---|---|---|
| **UP** | the node process is alive and This PC can see it: heartbeat age under its limit, link age under its limit | liveness ping (C-18), node link, `liveness_heartbeat_cadence` (v0) | "Unreachable since 03:12" |
| **ON** | the scope may open new risk now: kill level GREEN at every covering scope, not paused, no stand-down, trading state ACTIVE, REDUCING or RESTORE, market open, warm-up done | kill level per scope, stand-down table, trading state (X1-08), calendar | the ten-word reason ("Stopped by a risk rule", "Shut until Sunday 22:00") |
| **TRADING** | ON, and the unit evaluated its last bar within `decision_pulse_max_age`, and its trade count is inside what its card expects for the open hours | decision pulse (X6-12), card trade rate, calendar | "On but quiet" (no signal), "On but refused" (count by code), "On but deaf" (no evaluation) |
| **RIGHT** | two halves, both true. *Mechanically right*: positions reconcile, every stop is shown at the venue, costs inside their band, replay match above its floor. *Statistically right*: drift zone green and results inside the card's cone | reconcile rows, protection rows, cost ledger (X6-30), drift zone (X6-27) | the failing half, with its cause class |
| **WRONG** | any RIGHT half false. Severity yellow (gather evidence) or red (act) | as RIGHT | names the cause class: execution, cost, market, implementation, edge |
| **TRIPPED** | a brake is latched at this scope | brake meters (X6-07) | "Tripped: unit loss run, 2.1R of 2R, since 10:42, clears when he resumes" |
| **UNKNOWN** | any input of the word is older than its limit, or node and This PC folds disagree | fold ages, parity check (X6-40) | grey, with "cannot confirm since 14:02" |

Rules:
- **Dark cockpit.** When all is normal nothing is lit. Only exceptions draw the eye (roundtable, Ruiz).
- **"Nothing needs you" is earned.** It shows only when every word is fresh and normal; otherwise "cannot confirm".
- Health words (Gen 3's seven states: safety, execution readiness, connection, reconciliation, data freshness, lifecycle, sync) sit under UP and ON for engineers. He sees the six words (OBS `/health`; A4-162).

---

## 2. Hybrids

### A. The fact spine: what is recorded

**X6-01. One fold, many readers: `RiskState`.** Solid.
- Links: A4-152, A4-171, A4-20, A2-115, A5-10, A4-31, A2-114, A4-184.
- Need: the node must emit risk, not only health (G11 §4.3 "Money", "Which brake tripped").
- What and how: a pure fold over the append-only journals computes, per scope: equity triple (realized, marked, venue) with their anchors; drawdown by kind (X6-02); open risk at stop; exposure per bet key; budget used and burn rate; each brake and accelerator meter (X6-07); trading state; kill level requested and enforced (X6-09); drift zone and verification state (X6-27); placeholders still live; profile version and generation stamp. The guard reads the fold to act; the same fold library runs on This PC, in the Lab and behind MCP reads. Emission: on change plus a heartbeat every `risk_state_emit_interval`; deltas go to the journal, the full fold lives in memory and on read (roundtable, Priya).
- Levels: trade, unit, book, account, node; BMS when it exists.
- Per class and style: one shape for all classes. Scalpers change state often, so on-change emission matters most there. Crypto and 24/7: the heartbeat never pauses for a session. Futures: equity marks at the exchange settle, not only last trade.
- Ledger: v0 `brake_state`, `budget_remaining`, `kill_line_distance`, `open_risk_at_stop`, `portfolio_exposure`, `account_equity`, `realized_pnl`, `unrealized_pnl`, `drift_state`, `kill_switch_level`; new `risk_state_emit_interval`, `risk_fact_staleness_limit`, `status_generation`.
- Performance: the sizer and the screen read one number, so accelerators can lean on marked equity and cushion with confidence. Survival: brakes act on the same facts the UI shows; no "screen said fine, guard said stop".
- Evidence chain: Gen 3 docs (fold over transitions) → Kubernetes status pattern (production) → unit-build journals (built). Weakest link: marked equity on cTrader is read once at sign-in (G9 §3.3); the fold is only as good as that read.

**X6-02. Equity triple and drawdown by kind.** Solid.
- Links: A2-115, A5-10, A2-14, A2-15, A5-11, A4-42.
- Need: "exposure, drawdowns, unrealized and realized profits" (M12, B15); "5 % drawdown" meant four things across generations (G11 §2.2).
- What and how: every drawdown is a triple (equity series × anchor × window): day (marked, day start), session (realized R, session start), trailing (marked, high-water mark), cushion (marked, fixed floor), unit working anchor (may restart) and account floor (never restarts). Each shows depth and duration, with style-aware worry lines (depth for mean-reversion scalpers, duration for breakout and trend). A unitised price series per unit keeps its drawdown honest when allocation changes. Triple-penance gives "expected time to recover" beside each.
- Levels: unit, book, account, BMS.
- Per class and style: FX day anchor at the 17:00 New York rollover; crypto day anchor at UTC midnight by default, with his zone as a display option; index CFDs at the cash close; futures at settlement. Swing units: duration lines matter more than depth.
- Ledger: v0 `brake_equity_basis`, `day_start_equity`, `high_water_mark_equity`, `account_equity`, `realized_pnl`, `unrealized_pnl`, `day_boundary`; new `drawdown_by_kind`, `time_under_water`.
- Performance: duration lines catch slow decay that depth misses, so size can be stepped earlier and regrown sooner. Survival: two anchors stop a restart from hiding a drawdown (Hsieh's 20.18 % against a 20 % cap, A5-10).
- Evidence: Gen 3 docs, MQL5 basis enums, author simulation (A2-14). Weakest link: duration worry lines rest on a closed-form model checked in simulation only.

**X6-03. Decision trail with three weights and a trace id.** Solid.
- Links: A5-75, A4-153, A1-122, A1-156, A4-86, A4-31, OpenTelemetry pattern (memlog).
- Need: "why so small?", "why didn't it trade at 14:02?" (UI-NOTES §6); "every size change needs a stated reason" (A13).
- What and how: each decision row carries the unit's wanted size, each multiplier, brake and accelerator step with its value and reason code, the binding clamp, the rounding residue, the risk-approved size and the executed fill (three weights side by side). One trace id runs from the reading through the decision, order and fill to the trade row. "Explain this size" renders the row in ten words first.
- Levels: trade, position.
- Per class and style: the clamp list differs by class (margin and leverage caps for CFDs and crypto, contract steps for futures, lot step for FX); the row shape does not.
- Ledger: v0 `rounding_residue_r`, `control_rank_table`; new `weight_gap_r`.
- Performance: shows which clamp binds most often, so the binding one can be revisited instead of guessing. Survival: an unexplained size is visible the first time.
- Evidence: April spec (`binding_clamp`), production practice (OpenFeature reasons, Nautilus), author backtest (A5-75). Weakest link: the sizer receipt is hard-coded today (A4-86).

**X6-04. Trade row v2: mechanism apart from outcome.** Solid.
- Links: A4-150, A2-260, A2-261, A2-240, A5-95, A4-166.
- Need: "fast-invalidation cuts told apart from other exits" (brief); brakes must count FI (A28).
- What and how: the trade row gets an exit mechanism code (stop, FI cut, breakeven, time, signal, target, trail, forced flat by kill or risk rule, liquidation, roll) separate from the outcome (R, money). It also carries session, streak, equity before (both series), costs split (spread, commission, swap or funding, slippage) in R and money, MAE and MFE, stage and world. Per stop: trigger price, order type, quote source, decision and send times, fill and spread. A CFD roll adjustment is its own row kind, never a loss.
- Levels: trade, position, unit.
- Per class and style: swap for FX and CFDs held overnight; funding at the venue stamp for perps; roll rows for futures-based CFDs and futures; stocks carry dividends and corporate actions as their own lines [judgment].
- Ledger: v0 `exit_reason_code`, `excursion_mae_mfe_r`, `round_trip_cost_r`, `loss_counting_rule`, `loss_streak`, `swap_financing_cost`, `funding_cost`; new `exit_mechanism`.
- Performance: per-mechanism results show which exits earn (for example time exits at the edge's peak, A5-86). Survival: count brakes can count FI cuts by size.
- Evidence: Library `trade` kind already has the fields (G9 §7.1); Gen 3 split mechanism and outcome (SCN-0011). Weakest link: FI has no exit role in code, so its code has no emitter yet (X3's).

**X6-05. Two ledgers: money for brakes, events for decay.** Plausible.
- Links: A5-145, A2-166, A2-174, A5-86, A2-91.
- Need: count brakes must not punish frequency or FI cuts (brief); detect decay "before money shows it".
- What and how: the money ledger counts a cut by its size and a scratch by its costs; brakes read it. The event ledger records rates: FI rate, scratch rate, full-stop share, time-exit share, stop slippage, hold time. A rising full-stop share or a falling FI rate opens a ticket before P&L moves. Shown on the unit card as small rate lines.
- Levels: unit, methodology.
- Per class and style: scalpers carry the most signal here (many exits a day). Swing units have too few events per week; their rates are read monthly.
- Ledger: v0 `loss_counting_rule`, `loss_points_total`, `breaker_fire_density`, `exit_reason_code`; new `event_ledger_rates`.
- Performance: earlier, cheaper decay signals let size step down a notch instead of a full stop. Survival: an FI unit no longer trips "3 in a row" on 60 % of days (A5-145).
- Evidence: simulation (A5-145), practitioner rules (A2-166). Weakest link: no live study shows event-rate shifts lead P&L decay; it is arithmetic plus intuition.

**X6-06. Closed reason codes at source.** Solid.
- Links: A4-154, A4-64, A4-31, A5-49, A2-113, A2-160, A4-159 (cause classes).
- Need: the risk stop filed as kill switch (G9 §1.4); "each brake says what tripped it" (C7).
- What and how: one closed list in `CATEGORY_CONDITION` form, emitted where the event happens, never matched from text. Families: `KILL_<level>_BY_OPERATOR`, `RISKSTOP_<rule>`, `BRAKE_<kind>_<name>`, `ACCEL_<kind>_<name>`, `CLAMP_<name>`, `GATE_<name>`, `ISOLATION_<scope>`, `HEALTH_<cause>`, `EXIT_<mechanism>`, `CALIB_<learner>`. Every red also carries a cause class (execution, cost, market, implementation, edge, bad luck), from the Basel practice (roundtable, Mei). A contract test fails any emitter without a code; QMB's text map is deleted.
- Levels: all.
- Per class and style: codes for class-specific events (rollover minute, funding stamp, limit move, auction) are added as data rows, not code.
- Ledger: v0 `exit_reason_code`; new `demotion_cause`.
- Performance: fire densities become trustworthy, so the old breaker's alpha-decay reading (A26) works. Survival: a risk stop is never counted as a kill.
- Evidence: Nautilus (production), OpenFeature reasons (spec), the G9 bug. Weakest link: none technical; the risk is someone adding free text later. The contract test guards it.

**X6-07. Every brake and accelerator as a live meter.** Solid.
- Links: A5-106 (nine attributes), A4-152, A4-158, A2-28, A5-134, A5-123, R9 §0.2 (compressor knobs).
- Need: "which brake tripped" and "how close" (C7, G11 §4.3); R9's registry row made visible.
- What and how: each brake and accelerator reports its nine attributes as live values: what it reads (signal now), anchor, lever, direction, shape, speed, hysteresis band, counter and memory, clear rule. Plus state (shadow, armed, picked up, tripped, releasing, restoring, disabled), distance to trip in its own measure and as a share, time in state, fires today, and its scorecard link (X6-21). Accelerators show tier, dwell done against dwell needed, and the memory ceiling after a trip. Drawn like a compressor's gain-reduction meter: how hard and how fast it presses.
- Levels: unit, book, class, account, BMS.
- Per class and style: thresholds differ, meters do not. Count brakes on scalpers show "fires expected per day on a healthy unit" beside the count.
- Ledger: v0 `brake_state`, `breaker_fire_density`, `breaker_expected_fire_rate`, `brake_precision`.
- Performance: shows accelerators pressing and the ceiling they press against. Survival: a near-trip is visible before it trips.
- Evidence: R9 definitions (research), prop-firm and bank warning bands (A4-158). Weakest link: the attributes are R9's proposal; no shipped brake has them yet.

**X6-08. Motion receipts: who changed which number, and why.** Solid.
- Links: A4-1, A4-2, A4-3, A4-6, A4-80, A4-19, A4-41, A4-55, A4-31, A4-57.
- Need: "which learner and applier changed which number, and why" (brief); A13 volleyball; D46 change the derivation.
- What and how: spec (his value, range, derivation, applier mode) is apart from status (learner target, low and high bound, confidence, value in force, last apply, guard trips, frozen or not). Every move writes a receipt: number, learner id and version, input window, old and new, bounds, applier and mode (off/shadow, at flat, at new position, live), reason code, and the shadow's would-have result. A derivation fallback step (own record, class, preset) writes its step in the receipt. Improved defaults arrive as offers, never silently.
- Levels: unit, book, account.
- Per class and style: "at flat" is cheap for scalpers and rare for swing units; the receipt shows how long a pending value has waited.
- Ledger: v0 `number_motion_mode`, `calibration_cadence_trades`, `calibration_min_trades`, `applies_to_open_positions`; new `number_move_receipt`.
- Performance: a better learned value earns its place visibly, so he can trust live mode for more numbers. Survival: a bad learn is traceable and reversible to the receipt.
- Evidence: Kubernetes VPA (production), HotSpot guards (production), shipped calibration rows (built). Weakest link: QMX has no applier; `authority` is parsed and never read (G8 §3.10).

**X6-09. Requested, enforced, observed.** Solid.
- Links: A4-20, A4-19, A4-171, OBS `/health` (requested apart from enforced), v17 kill-switch popover design.
- Need: "is it on?" must mean "is it on at the node", not "did I click".
- What and how: every control (kill level, pause, brake trip, isolation, number change, deploy) shows three stamps: requested (by whom, when, why), enforced (which node, since when), observed by This PC (received, age). His resume that lowers a kill level gets its own row. A gap over `control_apply_lag_limit` shows "not yet applied on London-1".
- Levels: node, account, unit.
- Per class and style: the same for all.
- Ledger: v0 `kill_switch_level`, `kill_switch_scope`; new `control_apply_lag_limit`.
- Performance: none direct. Survival: a click that never reached a dead node is visible.
- Evidence: Gen 3 docs, Kubernetes, the v17 design itself. Weakest link: needs an ack path from node to PC for every control.

**X6-10. Context tags on every fire.** Solid.
- Links: A2-125, A3-112, A3-179, A3-68, A3-128, A5-52, A5-95.
- Need: tell a bad market from a bad unit; isolation evidence (C27).
- What and how: every brake fire, risk stop, refusal and loss row carries session, class, region, MIS words at the time, news window flag, liquidity label, rollover or funding minute, and roll window. Fire density by context then separates "this unit is broken" from "London open on gold is broken today".
- Levels: trade, unit, class.
- Per class and style: class-aware tags (FX rollover, crypto funding, index cash open, metal fixes, energy inventory releases, futures roll and limit state).
- Ledger: v0 `breaker_fire_density`, `instrument_class`, `session_windows`, `isolation_scope`; new `fire_context_tags`.
- Performance: a market problem pauses one market, not the unit. Survival: feeds class isolation with real evidence.
- Evidence: April annotation (old rule), idea. Weakest link: MIS readings are mostly not computed on the node today (G9 §4).

### B. Meanings

**X6-11. Six words and UNKNOWN, dark cockpit.** Solid. Full table in section 1.
- Links: A4-162, A4-163, A4-164, A4-151, A3-179, A4-20, A5-52, A2-80.
- Need: his D49 words, made exact.
- Levels: unit on a market, unit, book, account, node.
- Per class and style: ON reads each market's own calendar (crypto always, FX 24/5, indices by exchange, futures with halts). TRADING reads the style's trade rate.
- Ledger: v0 `liveness_heartbeat_cadence`, `watchdog_cadence`, `feed_stale_after`, `board_stale_after`; new `risk_light_state`, `risk_fact_staleness_limit`.
- Performance: "on but quiet" is a growth leak he can now see. Survival: a stale green is impossible.
- Evidence: aviation dark cockpit and Gen 3 doctrine (practice), April 30-second glance (design). Weakest link: "statistically right" depends on the drift zone, which is X5's and noisy early in a unit's life.

**X6-12. Decision pulse and the silence test.** Plausible.
- Links: A2-166, A3-181, A2-159, A4-151, G9 §7.1 (signal rows only for blocks).
- Need: TRADING must mean trading; an on-but-deaf unit is a sitting duck.
- What and how: a sampled "evaluated, no signal" row per unit (one per N quiet bars) proves the unit is listening. A Poisson test on the card's trade rate per open calendar hour flags "quiet beyond expectation" when P(zero trades) falls under `silence_alarm_probability`. Refusals are counted by code, so "quiet" splits into shut, no signal, refused, deaf.
- Levels: unit.
- Per class and style: scalpers: minutes. Intraday ORB: one window a day, so the test runs per window. Swing: days; weak (roundtable, Sam). Crypto weekends: the baseline is the same weekend hour, not weekdays.
- Ledger: v0 `trade_rate`, `trade_rate_band`; new `decision_pulse_max_age`, `silence_alarm_probability`.
- Performance: catches a silent unit in hours instead of at the weekly review. Survival: a deaf unit with open positions is also not managing them; the pulse catches that.
- Evidence: practitioner bands (A2-166), MIS baselines (idea). Weakest link: card trade rates come from backtests, which often overstate live rates.

**X6-13. Safety parameter display.** Solid.
- Links: nuclear control-room practice (memlog), A4-163, prop-firm distance bars, Dana's one-pager (roundtable).
- Need: a fixed glance, the same everywhere.
- What and how: six numbers always visible on Home, the Portfolio header and the phone's morning card: room above the floor, heat (open risk at stop), today's budget burn, kill level now, units trading against units expected, count of UNKNOWN facts. Each with its age. Dark when normal.
- Levels: account, BMS.
- Per class and style: the same.
- Ledger: v0 `open_risk_at_stop`, `kill_line_distance`, `budget_remaining`, `kill_switch_level`, `live_unit_count`; new `loss_budget_burn_rate`.
- Performance: the room number is also the accelerator's cushion. Survival: floor distance always in sight.
- Evidence: control-room and prop-firm practice. Weakest link: room above the floor needs marked equity (X6-01's weak link).

### C. Alerts

**X6-14. Four tiers: silent act, digest, ticket, page.** Solid.
- Links: A5-28, A4-201, A4-157, A2-25, A5-139, A5-160.
- Need: page against ticket; one alert at a time; enforcement never waits for a human.
- What and how: enforcement and notification are separate systems. Clamps act silently and record (aviation envelope). Money-at-risk facts may page. Edge estimates open tickets and move size slowly. Learner moves and normal brake fires are digest lines. A page names an action and a deadline or it is not a page. One page at a time, by `alert_priority`.

| Tier | Examples | Channel |
|---|---|---|
| Silent act | clamp binds, spread gate refuses, a brake steps size inside its band | journal, meters |
| Digest | a number moved, a brake fired and cleared, a healthy bad day | morning card, weekly letter |
| Ticket | drift yellow, cost drift, silence test, brake precision under floor, slow budget burn | Needs you inbox |
| Page | stop not at venue with no fix, open positions and node unreachable, fast budget burn, exit capacity lost with open positions, floor buffer breached | phone, then second channel |

- Levels: all.
- Per class and style: the tiers are the same; the thresholds per style come from X6-15.
- Ledger: new `alert_tier`, `alert_priority`.
- Performance: fewer interruptions keep him trusting the system, so he leaves accelerators on. Survival: trips never wait.
- Evidence: SRE and aviation practice (live in their fields). Weakest link: none in the idea; the risk is tier drift as rules are added (X6-41 guards it).

**X6-15. Frequency-fair burn-rate tiers.** Plausible.
- Links: A2-28, A4-32, A5-144, A2-177, A5-141, A2-217.
- Need: count-based alerts fire on healthy units as trades pile up; one rule must fit 40 trades a day and 2 a week.
- What and how: each scope has a loss budget for its period. Burn rate = share of budget used ÷ share of the period's trading time elapsed. Long and short windows (short = `burn_short_window_ratio` of long) must both exceed the tier, so alerts reset fast. Windows are set in expected trades (`burn_window_trades`), not hours. The budget comes from the unit's own daily P&L distribution at its trade count (A5-144). Below `low_traffic_trade_rate`, burn is replaced by a per-trade rule: one loss beyond k times the card's p95 loss opens a ticket.
- Levels: unit, book, account, BMS.
- Per class and style: scalpers: windows of tens of trades, minutes long. Intraday: the session. Swing: per-trade rule. Crypto: trading time is all hours; FX weekends do not count as elapsed time.
- Ledger: v0 `period_loss_budget`, `budget_remaining`, `unit_daily_loss_limit`, `portfolio_daily_risk_budget`, `trade_rate`; new `loss_budget_burn_rate`, `burn_rate_page_threshold`, `burn_rate_ticket_threshold`, `burn_short_window_ratio`, `burn_window_trades`, `low_traffic_trade_rate`.
- Performance: no page on a normal bad hour, so no panic pause. Survival: a fast burn pages before the budget is gone.
- Evidence: Google SRE tiers (live in its field). Weakest link: no trading test of burn tiers; the mapping from error budgets to loss budgets is [judgment].

**X6-16. Incident funnel: one root cause, one page.** Solid.
- Links: A4-160, A2-20, A2-26, A5-53, A2-125, A3-112, A2-25.
- Need: one alert at a time; alarm fatigue; "losing together" is one event.
- What and how: each alert gets an `incident_root_cause_key` (broker, feed, node, class, unit). Alerts within `incident_group_window` with one key join one incident with contributors listed (insurers' hours clause). One page per incident; a repeat only if it worsens, after `page_escalation_after`. Trips are never deduplicated, only the pages. Each incident is written once to an append-only ledger.
- Levels: unit, class, account, node.
- Per class and style: a crypto exchange outage groups all crypto units; a broker outage groups everything routed there.
- Ledger: new `incident_root_cause_key`, `incident_group_window`, `page_escalation_after`.
- Performance: none direct. Survival: a correlated day reads as one big event, not five strikes, which is what it is.
- Evidence: SRE and insurance practice. Weakest link: the root-cause key for "class losing together" needs X6-34's detector.

**X6-17. The wake contract for one operator.** Solid.
- Links: A4-201, A4-151 (C-18 list), A4-203, A2-25, A5-28, roundtable (Lin, Dana).
- Need: "the phone wake" (brief); C-18 pages only while a market is open.
- What and how: the phone wakes him only when all three hold: money is at risk now (open positions or working orders), the system cannot fix it alone, and his action changes the outcome before a stated deadline. The system has already done the safe thing (stop entries, close where it can) before it pages. The wake list: stop not shown at the venue after escalation failed; open positions with node unreachable or broker link down; exit capacity lost with open positions (X6-20); floor buffer breached; twin node trading one account. The first 60 characters say what, where and whether to act. An unacknowledged money page goes to a second channel. Everything else waits for the morning card. Conditions use open positions, never market hours.
- Levels: account, node.
- Per class and style: crypto and weekend-held FX get pages at any hour; a flat scalper account never pages at night.
- Ledger: v0 `liveness_heartbeat_cadence`, `protection_retry_max`; new `phone_wake_conditions`, `page_escalation_after`, `false_page_budget`.
- Performance: he sleeps, and trusts the system enough to run around the clock (Hummingbird). Survival: the few true emergencies wake him with a clear action.
- Evidence: process-industry alarm practice, the shipped C-18 list. Weakest link: ntfy has no delivery ack; a second channel is not built.

**X6-18. Distance-to-trip bars with pickups.** Solid.
- Links: A4-158, A2-53, A4-159, A5-136, grid relay practice (memlog).
- Need: early warning without alerts.
- What and how: instead of alerts at 80 % and 90 %, each limit is a bar with its distance and a "picked up" mark when the threshold is crossed but the timer has not fired. Yellow and orange are colours on the bar, not pushes.
- Levels: unit, book, account.
- Per class and style: bars fill fastest for scalpers; for swing units the bar moves per trade, so "picked up" is rare and meaningful.
- Ledger: v0 `daily_loss_warning_fraction`, `brake_state`.
- Performance: he sees room to keep trading. Survival: he sees the trip coming.
- Evidence: bank and prop practice. Weakest link: none.

**X6-19. Opening-bell and news watch window.** Plausible.
- Links: A4-203, A3-36, A3-229, A3-128.
- Need: opens and news are where most incidents start, and where most false alarms come from.
- What and how: for `watch_window_at_open` minutes around session opens and high-impact releases, watch sensitivity rises (shorter delays) and notifications are grouped; a window summary lands after. Hard protection never loosens.
- Levels: unit, class.
- Per class and style: index cash opens and FX London and New York opens; crypto has no open, so only news windows; energy inventory releases; futures limit-up and limit-down.
- Ledger: v0 `news_blackout_before`, `news_blackout_after`, `session_windows`; new `watch_window_at_open`.
- Performance: grouped notifications keep him from pausing units at the open, which is when ORB and session-open units earn. Survival: faster detection where incidents cluster.
- Evidence: assistant guidance (A4-203), calibrated event windows (author backtest, A3-229). Weakest link: news is parked on the unit path (G9 §2).

**X6-20. Exit capacity and locked heat.** Plausible.
- Links: A4-203, A3-162, A2-264, A5-80, A3-73.
- Need: "risk is high" is not "risk can be exited"; a halted market cannot be flattened.
- What and how: per position an exit-capacity state (open and liquid, thin, halted or limit-locked, venue down, rejecting). Heat in non-exitable positions shows as locked heat. A page fires when locked heat exceeds a share of room above the floor.
- Levels: position, account.
- Per class and style: futures and stocks halt; crypto venues go down; CFDs follow the underlying's hours; FX weekends lock all heat.
- Ledger: v0 `open_risk_at_stop`, `gap_loss_beyond_stop`; new `exit_capacity_state`, `locked_heat`.
- Performance: none direct. Survival: weekend and halt risk is visible before it happens.
- Evidence: assistant guidance, practice. Weakest link: venue halt and reject states are only partly in node rows.

### D. Alarm economics: performance with intention

**X6-21. The brake scorecard.** Plausible.
- Links: A2-30, A4-156, A2-142, A2-143, A2-135, A4-155, A2-137.
- Need: "brake precision tracked" (brief); his frequency "sweet spot" as a number (C33).
- What and how: monthly per brake: fires, precision (share of fires after which the shadow twin, without the brake, lost more than the brake's threshold), recall on replayed known bad episodes, detection and reset time, and lift against a random brake firing as often (the null). Under `brake_precision_floor` the brake gets a ticket: retune or back to shadow. Fewer than N fires reads "too few fires to judge".
- Levels: unit, book, account.
- Per class and style: precision is per class and style; a brake can be good on scalpers and noisy on swing.
- Ledger: v0 `brake_precision`, `breaker_expected_fire_rate`; new `brake_recall`, `brake_lift_vs_random`, `brake_precision_floor`.
- Performance: noisy brakes stop eating trades. Survival: a brake that never catches anything is found before the day it was needed.
- Evidence: random-control brake test (MQL5 23482, R5), hospital alarm audits. Weakest link: "needed action" rests on the twin's simulated fills (A2-174 warns simulated execution is not evidence).

**X6-22. Trip tax and the sitting-duck meter.** Plausible.
- Links: A4-202, A5-73, A4-35, A2-178, A4-155.
- Need: "I don't want just safety ... the sitting duck thing" (M33).
- What and how: per trip, the tax: units paused, time lost, forgone net P&L (from the twin), exit costs, loss avoided. Per unit and book, the sitting-duck meter: share of open hours held below baseline size and the R the twin made in that time. "This week brakes cost 1.8R and saved 3.1R."
- Levels: unit, book, account.
- Per class and style: scalpers accumulate tax fast; swing units show it monthly.
- Ledger: new `trip_tax_r`, `under_baseline_share`, `missed_return_r`, `twin_gap_r`.
- Performance: the main growth lens in this layer. Survival: shows when loosening is safe, not just when tightening is needed.
- Evidence: idea; EvolveTrade's idle-cash finding (A5-73). Weakest link: forgone P&L is a counterfactual.

**X6-23. Accelerator earned-keep.** Plausible.
- Links: R9 §1.11, §2.3, A5-131, A5-119, A5-123, A5-11.
- Need: brakes first, accelerators second (C19), but an accelerator must prove it is more than "size in disguise" (R9).
- What and how: per accelerator: extra R risked, extra R won, the block-persistence test on the unit's own record, and the tier dwell. If no persistence is measured, the line reads "size in disguise: same growth per unit of risk as a fixed size".
- Levels: unit, book.
- Per class and style: persistence shows at different block sizes per style; the test scans block sizes (A5-131).
- Ledger: v0 `house_money_multiplier`, `size_levels`; new `accelerator_earned_r`.
- Performance: keeps the accelerators that pay. Survival: retires the ones that only add variance.
- Evidence: R9 arithmetic, Ehsani-Linnainmaa factor persistence. Weakest link: block persistence needs about 950 trades for a 50-trade regime (R9).

**X6-24. Growth waterfall.** Plausible.
- Links: A4-42, A5-11, A1-141, A5-75, A4-139.
- Need: "it's right" includes "it is growing for the right reason".
- What and how: daily money change split into edge at base size, accelerators, brakes held under baseline, costs, execution gap (twin), allocation. Logic in R across versions; money per profile version.
- Levels: unit, book, account.
- Per class and style: carry (swap, funding) is its own bar for swing FX and perps; scalpers show costs as the biggest bar.
- Ledger: v0 `expectancy_r`, `round_trip_cost_r`; new `growth_attribution`.
- Performance: shows which lever grows the account, so effort goes to it. Survival: a day that "made money" through an accelerator on a decaying edge reads as such.
- Evidence: idea built from shipped records. Weakest link: attribution order changes the bars [judgment].

**X6-25. Family alarm budget across many units.** Plausible.
- Links: A2-152, A2-159, A4-161, A2-160, A2-158.
- Need: Hummingbird means many units; per-unit thresholds multiply false demotions.
- What and how: drift detectors across units share a false-alarm budget over a horizon (alpha = q/H per stream; e-BH for the review list). The UI shows "expected false alarms this month across 20 units: 1", and each demotion records its cause.
- Levels: unit, methodology, BMS.
- Per class and style: the horizon H counts each stream's own trade rate, so a scalper stream and a swing stream share the budget fairly (A2-159).
- Ledger: v0 `drift_state`, `sequential_evidence_pass`; new `demotion_cause`.
- Performance: fewer false demotions keep good units trading as the unit count grows. Survival: the family error rate is stated, not hoped.
- Evidence: proofs and simulation (A2-152). Weakest link: assumes valid e-values per stream; overlapping trades break independence.

**X6-26. Operator attention telemetry.** Wild.
- Links: A5-53, A5-56, A2-25, roundtable (Helen).
- Need: alarm fatigue measured on the operator, not only on the rules.
- What and how: count cards and pushes he dismisses without action, time to acknowledge, and reversals. A class dismissed three times proposes demotion to digest, with his yes. Money pages can never be demoted.
- Levels: system.
- Per class and style: none; it measures him.
- Ledger: new `operator_dismiss_rate`.
- Performance: his attention goes to what matters. Survival: noise that hides a real alert is cut, with money pages exempt.
- Evidence: approval-queue telemetry (live, A5-56). Weakest link: his dismissals may mean "busy", not "useless".

### E. Drift, verification and costs

**X6-27. Passport strip on the unit card.** Solid.
- Links: A4-165, A2-198, A2-186, A2-165, A2-176, A4-159, A2-167.
- Need: "drift zone and verification state" (brief); "right" in the statistical sense.
- What and how: a strip on the unit card: zone (green, yellow, red, thin, unknown), trades toward proof ("212 of 610"), next planned look, cone position as a percentile, upside alarm, zone history. Computed in R, not money, so accelerators do not move it.
- Levels: unit.
- Per class and style: proof takes years for swing units at low trade rates; the strip says "too thin to prove at this rate" (A2-186).
- Ledger: v0 `drift_state`, `mc_cone_floor_percentile`, `verification_trades_needed`; new `trades_toward_proof`, `upside_alarm_percentile`.
- Performance: green with proof lets size and accelerators rise on evidence. Survival: red is visible on the card he already opens; the upside alarm catches leverage nobody meant.
- Evidence: bank model inventories, Basel zones, built B13 card. Weakest link: the cone is not read by any check today (G9 §7.3).

**X6-28. Drift decomposition: why is it wrong.** Plausible.
- Links: A2-174, A2-166, A4-35, A2-178, A3-123, A2-164.
- Need: "you can't simply say if they differ, you simply pull out" (A25): tell causes apart.
- What and how: a panel splitting wrongness into costs (spread, commission, swap), fills (twin gap), market (bucket stress, MIS words), implementation (replay mismatch, version change), and edge (the residual). Each with its own zone and a "change began around" window.
- Levels: unit.
- Per class and style: costs dominate scalpers; market stress dominates class-wide events (crypto, indices at opens); implementation faults show first after a version change.
- Ledger: v0 `cost_drift_multiple`, `replay_match_floor`, `trade_rate_band`; new `twin_gap_r`.
- Performance: a cost problem gets a cost fix, not a pause of a good edge. Survival: real edge decay is not hidden under "bad fills".
- Evidence: assistant guidance, practitioner bands. Weakest link: the residual "edge" gets whatever the other parts miss.

**X6-29. Bad-day sentence and evidence honesty.** Solid.
- Links: A2-177, A5-30, A2-171, A2-161.
- Need: "it can be a bad day" (A25); a number without its noise misleads.
- What and how: "Yesterday was a one-in-24 day for a healthy unit of this type." Every performance number shows n, effective n and a band.
- Levels: unit, book.
- Per class and style: the day is the calendar day for FX and crypto, the session for index units; swing units use weeks.
- Ledger: v0 `daily_r_digest`, `edge_t_statistic`; new `bad_day_percentile`, `effective_observations`.
- Performance: no panic cuts after a normal bad day. Survival: a one-in-500 day is named as such and opens a ticket.
- Evidence: arithmetic on the card. Weakest link: the card's daily distribution is from backtest.

**X6-30. Cost against assumption, per cell.** Solid.
- Links: A1-146, A3-9, A3-239, A4-167, A4-168, A1-141, A3-17, A3-39, A1-144, A3-238, A5-157.
- Need: "slippage, and costs against assumptions" (brief); costs must reach the sizer.
- What and how: a cost cell is (instrument, hour of week, broker, order type). Each fill writes assumed against realised: spread, commission, slippage (from node send and fill rows, entry and exit apart, p50 and p95), swap or funding, rejection. The ratio is the cell's `cost_assumption_ratio`; the unit's cushion and retention follow. The sizer reads the cell; the UI shows it.
- Levels: trade, unit, account.
- Per class and style: FX last look (quoted spread with rejection rate); crypto fees and funding; CFD spreads by hour; futures commission per contract; stocks fees and borrow [judgment].
- Ledger: v0 `slippage_cost`, `spread_cost`, `commission_cost`, `round_trip_cost_r`, `cost_drift_multiple`, `unit_cost_target`; new `cost_cell_key`, `cost_assumption_ratio`, `slippage_p95_by_hour`, `slippage_asymmetry`.
- Performance: real costs size real trades; the 40 % of profit lost to costs in A1-141's example becomes visible. Survival: a cost blow-out reads as a cost problem, not decay.
- Evidence: AutoQuant reconciliation, MQL5 probes (author backtests). Weakest link: demo fills stand in for live; paper has zero slippage.

**X6-31. Fill quality: markout and stop execution.** Plausible.
- Links: A3-11, A2-261, A3-83, A4-167, A3-82.
- Need: scalpers drift through fills before R shows it.
- What and how: mid at 1 s, 5 s and 60 s after each fill; stop trigger against fill against spread. Markout lines on the scalper's card.
- Per class and style: crypto books per exchange are real; FX and CFD quotes are broker quotes, so markout is a venue proxy and labelled so (A3-78).
- Levels: trade, unit, node.
- Ledger: new `fill_markout_bp`.
- Performance: scalpers learn which hours and venues fill well. Survival: toxic fills show before R decays.
- Evidence: 232,897 live Binance maker orders (A3-11). Weakest link: broker quotes are not a book.

**X6-32. Shadow first for brakes, numbers and profiles.** Plausible.
- Links: A2-145, A4-30, A4-23, A4-24, A4-35.
- Need: a new brake or number earns enforcement with evidence.
- What and how: a new brake runs in shadow and writes would_have rows; its scorecard (X6-21) decides promotion to enforcing, ramped. Same for a number's applier mode and a profile version. The UI shows shadow and live lines side by side.
- Levels: unit, book, account.
- Per class and style: scalpers fill a shadow sample in days; swing units need months, so their shadow periods are set in trades, not days.
- Ledger: v0 `number_motion_mode`; new `twin_gap_r`.
- Performance: better brakes and numbers go live on evidence, faster than a new unit version. Survival: a bad new brake never enforces untested.
- Evidence: resilience4j, Argo dry runs (production). Weakest link: would_have rows have no writer today.

### F. Exposure and losing together

**X6-33. Exposure board.** Plausible.
- Links: A1-114, A3-162, A3-163, A5-1, A3-120, A5-64, A1-115.
- Need: "preventing losing all at once" (M12).
- What and how: per account and BMS: heat, exposure per bet key (currency legs for FX; underlying or class for the rest), N_eff ("10 units = 2.7 bets now"), top-factor share, and unit agreement (how many units are on one side, which families dominate).
- Per class and style: FX splits exactly into legs; metals, indices and crypto need covariance; energy by contract month.
- Levels: book, account, BMS.
- Ledger: v0 `portfolio_exposure`, `effective_independent_bets`, `open_risk_at_stop`, `currency_exposure_limit`; new `unit_agreement_score`.
- Performance: shows real breadth, the Hummingbird thesis's engine. Survival: "ten units, one bet" is visible before the shared move.
- Evidence: fundamental law (theory), MASS (paper). Weakest link: instrument records lack base currency (G9 §2).

**X6-34. Chorus detector with the hours clause.** Plausible.
- Links: A3-111, A3-158, A2-26, A2-125, A3-112, A3-95.
- Need: losing together seen as it happens, as evidence for isolation (C27) and his BMS breaker.
- What and how: co-loss fraction in a window against its expected rate; one incident per class or group; feeds the isolation proposal.
- Levels: class, account, BMS.
- Per class and style: windows short for scalpers at opens, a day for swing units; crypto weekends and FX Monday gaps are their own windows.
- Ledger: v0 `chorus_expected_frequency`, `loss_event_window`; new `co_loss_fraction`.
- Performance: one class paused, not the account. Survival: losing together is caught in its first window.
- Evidence: July spec (old rule, never run). Weakest link: the expected rate needs a cohort history.

**X6-35. Live stress gauge.** Plausible.
- Links: A5-93, A3-28, A3-162, A5-89, Lab stress board (UI map G).
- Need: "how bad could it get right now", in money, beside room above the floor.
- What and how: the Lab's stress-board cell computed live: loss if the worst plausible move per class hits now, plus gap allowance, as a share of room. The stress engine logs predicted against realised nightly.
- Levels: account, BMS.
- Per class and style: gap allowance for held positions (FX weekends, index overnight, energy events); crypto uses its own worst hour; scalpers that go flat carry little.
- Ledger: v0 `gap_loss_beyond_stop`; new `stress_gauge_loss`.
- Performance: room left after stress is the honest cushion for accelerators. Survival: a book one gap from the floor is visible.
- Evidence: SPAN practice (live in futures clearing). Weakest link: scenario sizes per class are unset.

### G. Journals, evidence and how facts flow

**X6-36. Incident bundle, black box and narrator.** Plausible (narrator: QMA flag).
- Links: A5-49, A2-19, A4-135, A5-153, A5-53, A5-50.
- Need: journals and evidence agents and he can read.
- What and how: a deterministic service writes each incident once with evidence ids and attribution (slippage, fees, sizing, exposure, market move). On a trip the last `black_box_window` minutes of ticks, decisions and RiskState are frozen. A read-only narrator writes plain words with a bounded cause list; a script checks every number it quotes; the text is attached, never an input.
- Levels: unit, account, node, system.
- Per class and style: the black box holds ticks for scalpers and bars for swing units.
- Ledger: v0 `exit_reason_code`; new `black_box_window`.
- Performance: faster fixes after incidents. Survival: raw records survive summaries that omit them (A5-53).
- Evidence: controlled tests of LLM alert triage (A5-50: logistic beat the best LLM). Weakest link: narrator accuracy.

**X6-37. Fact flow and authority.** Solid.
- Links: A4-171, A4-102, A4-20, OBS `/health` provenance, B15, B16, A4-184.
- Need: "how facts flow from node to This PC to the UI, the Lab and MCP tools" (brief).
- What and how: see section 3. The node's journals are the source; the node fold is live-authoritative; This PC's fold over harvested journals is replicated; the Lab's is simulated. Every read carries authority, source time, receive time and watermark.
- Levels: node, system.
- Per class and style: none; the flow is the same for every class.
- Ledger: new `journal_harvest_cadence`, `records_home_cadence`, `risk_fact_staleness_limit`.
- Performance: one truth lets the Lab and agents propose against real state. Survival: a late copy is labelled late, never mistaken for live.
- Evidence: Gen 3 provenance rules, shipped harvest. Weakest link: two fold hosts must stay identical (X6-40).

**X6-38. Risk read tools for agents.** Plausible; QMA flag.
- Links: G8 §4.1 tool rows, A4-133, A4-49, A4-111, A4-104.
- Need: agents read risk state to propose (X7) without touching money.
- What and how: read-only rows: `risk_state(scope)`, `risk_explain(unit, number)`, `brake_scorecard(brake)`, `incidents(since)`, `number_history(unit, number)`, `cost_cells(instrument)`. Same folds as the UI. Each answer carries authority and age. Reads are journalled (who read what, when).
- Levels: unit, book, account, node.
- Per class and style: none.
- Ledger: v0 `brake_state`, `drift_state`; none new.
- Performance: agents propose feasible changes (A4-133). Survival: read-only, no row writes money; reads are audited.
- Evidence: shipped read rows pattern. Weakest link: QMA is flagged, not designed here.

**X6-39. Lab parity.** Solid.
- Links: UI map G and H (interventions, stress board), A4-184, A2-141, A4-186.
- Need: the Lab and MCP use the template without rework (M36).
- What and how: the simulator writes the same decision, trade and RiskState rows with world `sim`. The Lab's interventions list, brake scorecards and stress board come from the same folds as live.
- Levels: all the template's levels.
- Per class and style: the simulator must model class costs and calendars; paper zero slippage must not leak into sim (collision 8).
- Ledger: v0 `brake_precision`; reuses every X6 measure.
- Performance: a pod variant is compared on the numbers live will report. Survival: a brake judged in the Lab is judged the same way live.
- Evidence: one compiled unit on PC and node (built). Weakest link: the Lab is unbuilt.

**X6-40. Observability observes itself.** Plausible.
- Links: A5-50, A5-61, A4-34, OBS three surfaces, memlog failure modes.
- Need: a stale green or a dead watcher is the worst failure.
- What and how: heartbeats for every scheduled watcher and digest job; node and PC fold checksums compared at a watermark; chaos drills on paper and demo (stale feed, missing fill, duplicate order, stop dropped) every `chaos_drill_cadence`, with a report of which alerts fired and how fast.
- Levels: node, system.
- Per class and style: drills per venue type (cTrader, CCXT perps).
- Ledger: new `chaos_drill_cadence`.
- Performance: none direct. Survival: a silent watcher or a stale green is found in a drill, not in a loss.
- Evidence: controlled monitoring-agent evaluations (A5-50); Knight Capital (live failure). Weakest link: drills on demo cannot produce real venue faults.

**X6-41. The ledger generates alerts, words and bars.** Plausible.
- Links: A4-69, A4-98, OBS allow-list generated from FAILURES.md.
- Need: a new brake must not need a hand-built screen or alert.
- What and how: each brake row in the ledger generates its meter, its distance bar, its reason codes, its alert tier and its MCP field. A rule with no ledger row cannot alert.
- Levels: all.
- Per class and style: class meanings come from the row (G11 §1.4 gap).
- Ledger: new `alert_tier`, `alert_priority`.
- Performance: a new brake or accelerator ships with its observability, so agents and he can add them without a UI session. Survival: no silent rule.
- Evidence: settings-schema-to-form (production), Gen 3 generated allow-list. Weakest link: the ledger is a design file today, not a runtime schema.

**X6-42. Get-even flag and autonomy demotion.** Plausible.
- Links: A5-85, A5-78, A4-139.
- Need: raises after a loss are the classic human and agent error.
- What and how: any size raise within `get_even_window` after a loss, by him or an agent, is flagged on the card and in the journal. A drawdown moves appliers from live to shadow until he resets.
- Levels: unit, system.
- Per class and style: windows in minutes for scalpers, a session for intraday, a day for swing.
- Ledger: new `get_even_window`.
- Performance: none direct. Survival: the costliest human bias is flagged when it happens; an agent that asks hardest for size gets the slowest accelerator (R9).
- Evidence: 1.3 million prop trades (live). Weakest link: none for the flag.

**X6-43. Morning card and weekly letter.** Solid.
- Links: A4-163, A2-177, UI-NOTES §2, A4-166.
- Need: "30 seconds to confidence"; long text goes unread.
- What and how: three lines first ("All up. 4 units traded, +3.1R. One brake fired, healthy-unit odds 1 in 6."), then per live unit what it did, stops, costs against assumptions, the sitting-duck line. The weekly letter: what grew, what brakes cost and saved, which numbers moved and why, what needs his ruling.
- Levels: unit, account.
- Per class and style: one line per live unit; swing units say "held, no change" when nothing happened.
- Ledger: v0 `daily_r_digest`; new `bad_day_percentile`.
- Performance: he reads it, so he keeps trusting automation. Survival: overnight stops are seen at breakfast.
- Evidence: April design, built morning-digest template. Weakest link: needs This PC on to build (collision 13).

### H. Wild

**X6-44. Vital-signs strip per unit.** Wild.
- Links: A4-163, A2-166, X6-12. Need: "is it working" at a glance on a phone.
- What and how: a patient-monitor strip per unit: decision pulse, cost pressure, drift zone, budget burn, exposure. A flat line is visible at once.
- Levels: unit. Per class and style: the pulse rate follows the style's bar.
- Ledger: new `decision_pulse_max_age`, `loss_budget_burn_rate`.
- Performance: a stalled unit is seen in seconds. Survival: same.
- Evidence: ICU practice only. Weakest link: may be decoration.

**X6-45. A status page agents read before answering.** Wild; QMA flag.
- Links: A4-133, A5-49, A4-20. Need: agents must not explain results from stale or broken state.
- What and how: a system status (up, degraded, incident open) that the copilot and agents read before answering any question about results, and quote.
- Levels: system. Per class and style: none.
- Ledger: v0 `brake_state`.
- Performance: fewer wrong answers. Survival: agents do not propose on a broken state.
- Evidence: public status pages (practice). Weakest link: QMA is flagged here, not designed.

**X6-46. An observability budget per unit.** Wild.
- Links: A2-29, A4-33, A2-30. Need: a noisy unit or rule is a defect, like a noisy brake.
- What and how: a unit may raise at most N tickets a week; over budget, a ticket opens against its own rules (SRE: a spent budget freezes changes).
- Levels: unit. Per class and style: N scales with trade rate.
- Ledger: v0 `brake_precision`; new `false_page_budget`.
- Performance: noisy units get fixed. Survival: none direct.
- Evidence: SRE error-budget policy. Weakest link: punishes honest units in bad markets.

**X6-47. One-tone sound map.** Wild.
- Links: A2-25, A4-157. Need: one alert at a time, on the desktop.
- What and how: one tone per state family, silent when normal (aviation one-aural rule).
- Levels: system. Per class and style: none.
- Ledger: new `alert_priority`.
- Performance: none. Survival: the loudest thing is the most urgent thing.
- Evidence: aviation practice. Weakest link: Priya's "gimmick".

---

## 3. How facts flow

```
node (VPS or This PC)
  journals: order, reconcile, stand_down, kill_level (rise AND lower), protection,
            trade v2, decision, calibration receipt, risk_event, RiskState deltas
  fold (live-authoritative) -> guard acts; pushes; node link answers
        |  node link: compact RiskState + acks (seconds)
        |  journal harvest: open month every 60 s; server records home every 300 s
        v
This PC
  fold over harvested journals (replicated, with watermark + checksum vs node)
  slow analytics: brake scorecards, trip tax, N_eff, drift tests, cost cells
        |
        +--> UI (Home, Portfolio, unit page, node page): every field shows authority + age
        +--> MCP read rows (agents, copilot): same folds, reads journalled
        +--> workflows (decay check, watcher, morning card)
Lab simulator
  same rows with world = sim -> same folds -> stress board, interventions, scorecards
```

- Push decisions are made on the node, so a dead This PC never silences a page.
- Liveness is watched from outside (Healthchecks); a dead box cannot report itself (OBS).
- Telemetry may drop under back-pressure; RiskState deltas and receipts are evidence and may not (DEC-0322).

---

## 4. Problems and solutions

Full workings in `linking/stage-b/X6-observability/problem-solving.md`.

| # | Problem | Option 1 | Option 2 | Option 3 | Trade-off |
|---|---|---|---|---|---|
| P1 | Node reports health, not risk | Node-authoritative fold | This PC recomputes from journals | Split by speed: node money facts, PC slow analytics | 1 needs the guard and marked equity; 2 is late and unusable for brakes; 3 needs fold parity |
| P2 | Codes lie; exits merge | Closed codes at source plus contract test | Precedence table over text | Structured reason object | 2 is small and breaks again; 3 is richer rows |
| P3 | Six words undefined | Six predicates plus UNKNOWN | Gen 3's seven health states raw | One colour with drill-down | 2 is not his words; 3 hides causes |
| P4 | On but not trading invisible | Decision pulse rows | Poisson silence test | Both | 1 adds rows; 2 is slow for swing |
| P5 | Alerts multiply with frequency and units | Burn tiers in expected trades | Family alarm budget | Operator attention budget | 1 adds thresholds; 2 slows detection; 3 may mistake busy for useless |
| P6 | Paging one sleeping operator | Wake contract | Never page at night | Escalation chain | 2 leaves a missing stop for hours; 3 needs a second person |
| P7 | No learner and applier trail | Spec and status with receipts | Profile version history | Both | 2 misses in-range moves |
| P8 | Brake cost unknown | Shadow twins | Monthly trade-list replay | Random brake at matched frequency | 1 simulated fills; 2 backtest fills; 3 needs many fires |
| P9 | Costs unmeasured; paper zero slippage | Cost cells from node rows | Paper borrows live cells | Minimum-size probes | 1 demo is weak; 2 is a model; 3 costs money |
| P10 | Facts late or disagreeing | Live state over node link | PC fold with watermark | Both with authority labels | 1 adds a channel; 2 is late |
| P11 | Losing together unseen | Exposure board by bet keys | Outcome chorus | Factor share | 1 lacks base currency; 2 is after the fact; 3 needs history |
| P12 | Two stacks, telemetry off | Risk in journals, stacks read only | One sink (OpenObserve) | Prometheus gauges from the fold | 2 is against his August ruling; 3 duplicates numbers |

---

## 5. Collisions

Named, not resolved.

1. **The v17 kill-switch design against the shipped kill switch.** The design shows "Requested: YELLOW by the volatility guard at 11:42". On the unit path only he raises it (G9 §0.1). The brief only says it goes down by his hand. Who may raise a kill level, and whether a guard's action is a kill level or a trading state, is open (X1 P15).
2. **"No separate risk screens" (UI-NOTES §18) against this layer's surfaces.** That note left risk to this session; restructure R5 folds risk into existing screens.
3. **Silent clamps (aviation, A4-157) against "each brake says what is breaking" (C7).** Silent here means no alarm; the act is always recorded and visible.
4. **Fast burn pages against "size down, but not quickly" (A25).** A burn page is about money now; drift is about edge and moves slowly (A5-139). X3 owns the size response.
5. **C-18 pushes fire mostly while a market is open** against crypto 24/7, weekend-held FX and roll gaps (X6-17).
6. **"Watchers have no authority" (Gen 3) against a burn-rate brake (A2-28, A5-141).** One signal, two consumers: the alert path and a brake in X3. Who owns the thresholds?
7. **Prometheus and Grafana ruled mandatory for the soak (DEC-0212)** against host OpenObserve and against "risk lives in journals".
8. **Paper fills have zero slippage (G9 §3.1)** against cost telemetry and twin gaps on paper units.
9. **Telemetry dropped before evidence (DEC-0322)** against RiskState volume: if RiskState is evidence it competes for VPS disk with journals.
10. **Agents seeing distance to trip (A4-133, X7)** against pod-shop practice of hiding exact limits so nobody sizes just under them (roundtable, Dana).
11. **Upside alarm (A2-176) against accelerators (X2).** A working accelerator in a persistent regime pushes money results above the cone. X6-27 computes the cone in R to dodge it; money views still collide.
12. **Brake precision needs a counterfactual** against "no hindsight" (CFS:1133) and "simulated execution is not evidence" (A2-174).
13. **The morning card is built on This PC** against units on a server while This PC is off (ruling: PC is home, servers substitute).
14. **Decision pulse rows (X6-12) against on-change emission (X6-01)** on scalper nodes.
15. **Operator attention demotion (X6-26) against the wake contract (X6-17).** Money pages must be exempt.
16. **Ledger-generated alerts (X6-41) against the incident funnel (X6-16).** Generated per-rule alerts must still group by root cause.
17. **The unit working anchor may restart (A5-10)** against drawdown-by-kind display: a restart could hide a drawdown on screen unless both anchors show.
18. **Three drift vocabularies:** dc-decay OK/Watch/Alarm (built), X5's green/yellow/orange/red ladder (A2-167), Basel green/yellow/red (A4-159). And the watcher's Well/Watch/Alarm against the six words.
19. **UI state words against trading states.** UI-NOTES has "Stopped by a risk rule" but no word for X1's REDUCING or RESTORE. Also: ids `demotion_cause`, `trades_toward_proof`, `bad_day_percentile`, `effective_observations` and `upside_alarm_percentile` may also be added by X5; the funnel merges.

---

## 6. Restructure proposals

- **R1. Replace the node's health-only `status` and the watcher's single word with the `RiskState` fold and the six words.** Health becomes the seven sub-states under UP and ON. Better because the UI, phone and guard read one truth, and "right or wrong" becomes computable (X6-01, X6-11).
- **R2. Replace QMB's text-to-code reason map with codes emitted at source, and delete the map** (migrate callers, then delete). Better because counting is exact and the G9 bug cannot return (X6-06).
- **R3. Replace "pushes while the market is open" with "pushes while money is at risk".** Better for crypto, weekends, halts and rolls (X6-17).
- **R4. Replace per-surface computations (watcher scripts, morning digest, UI, future Lab) with one fold library** used on node, This PC, Lab and MCP. Better because numbers never disagree by construction (X6-37, X6-39).
- **R5. Replace "no separate risk screens" with risk surfaces folded into existing screens:** a Risk tab on the unit page, the node Overview, the Portfolio pod panel and header, Home's safety strip. No new top-level screen. Better because risk shows where he already looks.
- **R6. Make the ledger the generator of alert rules, state words, meters and MCP fields,** as Gen 3 generated its push allow-list from FAILURES.md. Better because adding a brake adds its observability for free (X6-41).
- **R7. One drift vocabulary:** green, yellow, red, plus "thin" (too thin to judge) and UNKNOWN, used by the decay check, X5's ladder, the watcher and the unit card. Better because one word means one thing on every screen (UI-NOTES §0 rule).

---

## 7. Gaps: what no component covers

1. A ground-truth label for "this brake fire needed action" without a simulated counterfactual.
2. A marked-equity source on cTrader (balance is read once at sign-in, G9 §3.3).
3. Base currency or underlying keys on instrument records for non-FX exposure (G9 §2).
4. An evaluation heartbeat row per unit per bar.
5. Operator attention modelling beyond approval queues.
6. An audit of the MCP read path (who read which risk fact, when).
7. Retention and disk budgets for risk rows on a VPS at scalper frequency.
8. A BMS object to hang portfolio telemetry on (G9 §6).
9. "Trading time elapsed" across 24/7 crypto, 24/5 FX and exchange calendars, for burn windows.
10. An FI exit role, so FI's exit code has an emitter (X3's).
11. A second notification channel and a delivery acknowledgement.
12. Security for acting from a push ("flatten this" from the lock screen).

---

## 8. Questions only he can answer

1. At night, should QMX wake you only when your action changes the outcome, or never (it acts and tells you in the morning)?
2. Is there a second person or service to call if you do not answer a money page?
3. On Home, do you want the performance lines (what brakes cost, what accelerators earned), or only safety?
4. Keep Prometheus and Grafana from your August ruling, or one place for everything?

---

## 9. UI requests per screen, for the UI session

Requests only. No UI code. The current design is outdated (D47); screen names follow `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\build\UI-NOTES-UNITS.md` and the Portfolio, Home and Lab mockups in `C:\Users\Mubarak\Desktop\QMX\workroom\ui-review-2026-10-01` (v15 to v23, day-one shots). His rules hold: "a preview and a detailed view, design for both", "the proposal should be rendered in the UI", both units of measure on screen (C9). Each request names the hybrid behind it.

### 9.1 Everywhere
- Every risk number shows its age and authority (live, from the PC copy, simulated). Past its limit it turns grey with "cannot confirm since …" (X6-11, X6-37).
- Dark cockpit: normal states draw nothing; only exceptions are coloured (X6-11).
- Money rows show USD and R together (C9; X6-03).
- Reason text comes from codes, ten words first, detail on tap (X6-06).
- One word, one meaning: the six words and UNKNOWN; one drift vocabulary (R7).

### 9.2 Home (Today)
- A safety strip, always visible: room above the floor, heat, today's budget burn, kill level now, units trading against expected, UNKNOWN count (X6-13).
- "Needs you" holds tickets and pages only, grouped by incident with contributors listed (X6-16).
- "Nothing needs you" only when every fact is fresh; otherwise "cannot confirm" (X6-11).
- The morning card: three lines first, then per live unit what it did, stops, costs against assumptions, the sitting-duck line (X6-43, X6-22).
- The nodes strip shows UP with heartbeat age, and "not yet applied" when a click has not reached a node (X6-09).

### 9.3 Bell and notifications panel
- Incidents, not alerts; each with tier, action, deadline, owner, and whether it clears by itself (X6-14, X6-16).
- Shelved items show who shelved them and until when; shelving never hides a trip (A4-201).

### 9.4 Portfolio: header and Overview
- The safety strip in the header (X6-13).
- Exposure panel: heat, exposure per bet key, N_eff ("10 units = 2.7 bets"), top-factor share, unit agreement (X6-33).
- Locked heat (positions that cannot be exited now) shown apart (X6-20).
- Live stress gauge beside room above the floor (X6-35).
- Pod panel: "Limits right now" as distance bars with pickups, not rings alone (X6-18); drawdown by kind with its anchor named (X6-02); "Room above the kill line" with both the account floor and the unit working anchor (collision 17).

### 9.5 Portfolio: Live
- The kill-switch control shows requested, enforced and observed stamps, and his lowering as a row (X6-09).
- Holdings rows: open risk in R and USD, exit capacity state, stop shown at the broker with its last-seen time (X6-20).
- Trading state per scope (ACTIVE, REDUCING, HALTED, RESTORE) with reason and distance to the next trip (X1-08, X6-07).

### 9.6 Portfolio: Risk (Books table) and Allocate
- Per unit or book row: equity triple, drawdown by kind, budget burn, brakes tripped, accelerators pressing (X6-01, X6-07).
- Growth waterfall per row (X6-24).
- Chorus line: co-loss fraction today against expected (X6-34).

### 9.7 Portfolio: Road to live and Promotions
- The promotion card shows the passport strip, the brake scorecards of the brakes it carries, cost cells calibrated or not, and placeholders left (X6-27, X6-21, X6-30).

### 9.8 Portfolio: MIS
- Each reading's health word and which units used a fallback (X6-11).

### 9.9 Library: unit card (preview)
- Passport strip: zone, trades toward proof, next look (X6-27).
- The six words for this unit on each market (X6-11).
- Event rates for scalpers: FI rate, full-stop share (X6-05).
- Sitting-duck meter and trip tax this week (X6-22).

### 9.10 Library: unit page (detail)
- A **Risk** tab: brake and accelerator meters with state, distance, time in state, fires, scorecard (X6-07, X6-21); trading state history; drawdown by kind; budget burn.
- **Numbers** tab: each number's spec against status, target band and bounds as a dial, applier mode, last receipt with learner and reason (X6-08).
- **Costs** section: cost cells, assumed against realised, p95 slippage by hour, markout for scalpers (X6-30, X6-31).
- **Drift** section: the decomposition panel and the "change began around" window (X6-28).
- "Explain this size" on any trade or decision, three weights and the binding clamp (X6-03).
- Shadow lines beside live for any shadowed brake, number or profile (X6-32).

### 9.11 Journal view
- Row marks for exit mechanism apart from outcome; FI cuts, time exits and signal exits distinct (X6-04).
- Brake fire rows with rule, values, reason code and context tags (session, class, MIS words, news, rollover) (X6-06, X6-10).
- Number moves with receipts; his kill lowering as a row (X6-08, X6-09).
- Tap a time: the trace from reading to fill (X6-03).
- Incident rows link to the black box (X6-36).

### 9.12 Trading node app
- Overview: the six words for the node, the seven health sub-states on tap, kill level requested and enforced (X6-11, X6-09).
- Units tab: TRADING with decision pulse age; "on but quiet", "on but refused" (with counts by code) or "on but deaf" (X6-12).
- Positions tab: open risk, exit capacity, locked heat (X6-20).
- A new Fills tab: slippage per order from send and fill rows, entry and exit apart (X6-30).
- Checks: fold parity with This PC, watcher heartbeats, last chaos drill (X6-40).

### 9.13 Stop cards, alarms and the phone
- Stop card: rule and values from the code, scope, what happened to open trades, the trip tax so far, what clears it, the incident it belongs to (X6-06, X6-22).
- Push format: first 60 characters say what, where and whether to act, with a deadline (X6-17).
- Phone morning card fits one screen (X6-43).

### 9.14 Lab: Pods Test and Paper
- Interventions list uses the same codes and rows as live (X6-39).
- Stress board cells use the live stress gauge's maths (X6-35).
- Brake scorecards and trip tax per pod, with the random-brake null (X6-21, X6-22).
- "Ready for live?" adds: cost cells calibrated, brake scorecards past the floor, zero UNKNOWN facts in the soak (X6-30, X6-21, X6-11).

### 9.15 Copilot panel and agents
- "Explain this size", "why did it not trade at 14:02", "what tripped" answered from the read rows, quoting evidence ids (X6-38, X6-36).
- The narrator's text marked as attached commentary, with a "numbers checked" tick (X6-36).

### 9.16 Settings
- Alarms: the wake conditions list with plain words, the second channel, a "send a test page" button, the false-page budget and this month's count (X6-17).
- Units: freshness limits, emission interval, watch windows at opens, burn tiers per style, all editable with their derivation shown (X6-01, X6-15, X6-19).
- Records: harvest cadences and the black-box window (X6-37, X6-36).
- Attention: classes demoted to digest, with his yes, and a way back (X6-26).

---

## Appendix A. Method record

- **Brainstorming (headless).** 140 ideas across Morphological Analysis, Concept Blending, Forced Relationships, Cross-Pollination, Trait Transfer, Evolutionary Pressure and Solution Matrix, then experiential, performance, failure-mode and wildcard shifts. Evolutionary Pressure's selection rule: at most one page a month per account and one ticket a week per unit on healthy replays; catches the five injected faults; fits 40-a-day and 2-a-week units unchanged; works with This PC off; fewest new variables. Killed by it: paging on drift red, one colour per node, fixed Google burn tiers, "no trade in 24 h" silence. Memlog: `linking/stage-b/X6-observability/.memlog.md`.
- **Problem solving.** 12 problems, each with Is/Is-Not, a root cause and 2-3 options: `problem-solving.md`.
- **Roundtable.** Pod-shop risk manager, retail scalper, platform engineer, his voice, ICU alarm engineer, aviation human-factors engineer, swing trader, crypto desk, bank model validator. It changed seven hybrids (dark cockpit, on-change emission, low-traffic rule, pages on open positions, cause class on every red, random-brake null, separate cost lines): `roundtable.md`.

## Appendix B. Not covered

- I did not run the node, the UI or any code. The UI mockups were read as images; UI-NOTES-UNITS was the text source.
- The Exa tools and the alphaXiv MCP were not used; every claim rests on components, grounding and research already on disk.
- QMA (agent system) pieces are flagged, not designed: X6-36's narrator, X6-38's read rows, X6-45.
- The numbers lens: no threshold here has a value. Each new variable has a derivation rule and a null default.
