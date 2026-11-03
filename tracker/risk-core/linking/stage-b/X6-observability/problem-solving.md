# X6 problem solving (bmad-cis-problem-solving, run headless)

Method per problem: refined statement, Is/Is-Not bounds, root cause (Five Whys or Fishbone), at least two solutions, a decision-matrix note on trade-offs. No pick: the funnel judge picks. Sources in brackets.

---

## P1. The node reports health, not risk

- **Statement.** Nothing on the unit path emits equity, drawdown, exposure, open risk, budget used, brake state, drift zone or the kill level now. So the UI can say "up, on, trading" but not "right, wrong, tripped" (G11 §0.10, §4.3).
- **Is / is not.** Is: node `status`, `units`, `positions`; the B21 watcher; C-18 pushes. Is not: QMB backtests, which do compute drawdown (G11 §2.1).
- **Root cause (Five Whys).** No risk row → no guard computes risk → the unit build parked risk for this session (PH, B21 README) → the sizer sees realized money only (`unit_handler.py:344-346`) → cTrader equity is read once at sign-in (G9 §3.3).
- **S1. Node-authoritative fold.** The guard computes `RiskState` per scope on the node and emits it on change plus a heartbeat (X6-01). + One truth, usable by brakes. − Needs the guard (X1-57) and a marked-equity source.
- **S2. This PC recomputes.** This PC folds harvested journals plus a view-only broker read. + No node change. − 60-300 s late; useless for brakes; disagrees with what sized the trade.
- **S3. Split by speed.** The node computes the money facts it acts on (equity series, drawdown, budget, heat, brake distances). This PC computes slow analytics (N_eff, precision, trip tax, drift tests) and stamps them with a watermark. + Cheapest on the VPS, honest authority labels. − Two fold hosts to keep identical (X6-37 parity check).

## P2. Reason codes lie, and exits merge into "close"

- **Statement.** A risk stop is journalled as `kill_switch` (first text match), and time, signal and FI exits all read `close` (G9 §1.4; G11 §3.4).
- **Root cause (Fishbone).** Method: reasons are free text mapped later. Data: QMB fill kinds double as exit kinds. People: no owner of a code list. Machine: no contract test.
- **S1. Closed codes at source** in `CATEGORY_CONDITION` form, with a contract test that fails on any emitter without a code, and the text map deleted (X6-06). + Counting becomes exact. − Touches every emitter.
- **S2. Precedence table** over the existing text map, plus tests. + Small. − Still text; breaks again on the next wording change.
- **S3. Structured reason object** `{code, scope, rule_id, values, by}` on every row. + Also gives the stop card its "rule and values". − Bigger rows.

## P3. His six words have no definitions

- **Statement.** "Up, on, trading, right, wrong, tripped" are not computable today; the watcher folds everything into Well, Watch or Alarm (G11 §4.1).
- **S1. Six predicates plus UNKNOWN**, each a fold with inputs and a freshness limit (X6-11). + His words, exact meaning, no stale green. − Six lights per scope can still be many on a big book.
- **S2. Gen 3's seven independent health states** shown raw (OBS §/health). + Engineer-grade. − Not his words; says nothing about money.
- **S3. One overall colour with drill-down.** + Simplest glance. − Gen 3 doctrine rejects it: one colour hides which part failed.

## P4. "On but not trading" is invisible

- **Statement.** A unit can be permitted to trade and silently never evaluate (deaf) or never find a signal (quiet). Signal rows are written only for blocked decisions (G9 §7.1).
- **S1. Decision pulse.** A sampled "evaluated, no signal" row per unit per bar (one per N bars when nothing happens). + Detects deaf units in minutes. − Journal volume on scalpers.
- **S2. Silence test on trades.** P(zero trades in window | card trade rate, open calendar hours) below a threshold opens a ticket (X6-12). + No new rows. − Slow for swing units; cannot tell deaf from quiet.
- **S3. Both,** pulse for deaf, Poisson for quiet, refusal counts by code for "refused".

## P5. Alerts multiply with frequency and with units

- **Statement.** Count-based alerts fire on healthy units as trades pile up (the same arithmetic as count brakes, STATE item 10), and ten units mean ten times the alerts.
- **S1. Burn-rate tiers** with windows in expected trades and a budget from the unit's own daily distribution (X6-15). + Fair across 40/day and 2/week. − New thresholds to derive.
- **S2. Family alarm budget** (error over patience; alpha = q/H per stream) for drift alarms across units (X6-25). + Provable false-alarm rate. − Slower detection per unit.
- **S3. Operator attention budget**: classes he dismisses get demoted to digest with his yes (X6-26). + Learns his tolerance. − Must never demote money pages.

## P6. Paging one operator who sleeps

- **Statement.** He is the only human. A page at 3 am is not protection unless the system already acted (A4-201).
- **S1. Wake contract**: wake only if money is at risk now, the system cannot fix it alone, and his action changes the outcome by a deadline; the system has already done the safe thing (X6-17). + Few, meaningful pages. − Needs exit-capacity facts.
- **S2. Never page at night**: the system acts and the morning card reports. + Sleep. − A missing stop at the venue on a held position waits hours.
- **S3. Escalation chain**: unacknowledged pages go to a second channel and then a second person or a service. + Robust. − Needs a second person (his call).

## P7. No trail of which learner and applier changed which number

- **Statement.** QMX has the learner and no applier; `authority` is parsed and never read (R7; G8 §3.10). A move shows old and new but not who decided under what mode.
- **S1. Spec and status split with a receipt per move** naming learner, version, inputs window, target, bounds, applier, mode, reason code (X6-08). + Exactly his "every move needs a stated reason". − Schema work in the calibration row.
- **S2. Version history of the profile document** with diffs. + Uses A9 identity table. − Misses in-range moves that are not versions.
- **S3. Both,** in-range moves as receipts, out-of-range changes as versions with the identity label.

## P8. Nobody knows what brakes cost or what accelerators earn

- **Statement.** No precision, trip tax or earned-keep number exists, so a "sitting duck" cannot be seen (M33).
- **S1. Shadow twins and would_have rows** per brake and per unit (X6-22, X6-32). + Live evidence. − Twin fills are simulated (A2-174 warning).
- **S2. Monthly replay** on trade lists with the re-sizer (A2-141) under each brake on and off. + Cheap. − Backtest fills.
- **S3. Random brake at matched frequency** as the null (A2-135). + The only fair test found. − Needs many fires.

## P9. Costs against assumptions are unmeasured; paper has zero slippage

- **Statement.** The data for slippage exists in node order rows but no script reads it; paper fills at the bar's bid or ask (G9 §3.1, §3.4).
- **S1. Cost ledger per cell** (instrument, hour, broker, order type) from node rows, entry and exit apart, p50 and p95 (X6-30). − Demo fills are a weak stand-in for live.
- **S2. Paper borrows the live cell ledger** for its fills, so paper telemetry stops lying. − A model, not a measurement.
- **S3. Minimum-size probe trades** to calibrate cells (A3-83). − Costs money and spread.

## P10. Facts reach screens late or disagree

- **Statement.** Journals reach This PC every 60 s (open month) or 300 s (server nodes); a node can be unreachable; two folds can disagree (G11 §4.1).
- **S1. Live state over the node link** (compact RiskState) plus journals for evidence. − Another channel.
- **S2. PC fold from harvested journals** with watermark and checksum. − Late.
- **S3. Both, with authority labels** (live-authoritative, replicated, simulated) and age on every field (X6-37).

## P11. Losing together cannot be seen

- **Statement.** No cross-unit exposure, no bet keys for non-FX, no BMS object (G9 §6).
- **S1. Exposure board** by currency legs for FX and class or underlying keys for the rest (X6-33). − Instrument records lack base currency.
- **S2. Outcome-based chorus**: co-loss fraction in a window against its expected rate (X6-34). + Needs no keys. − Sees it only after losses.
- **S3. Factor share** (top principal component of unit returns). − Needs history.

## P12. Two monitoring stacks, telemetry off by default

- **Statement.** OpenObserve shipping is off; a Prometheus, Grafana and Loki stack ships unwired; he ruled the latter mandatory for the soak in August (DEC-0212; A4-169).
- **S1. Risk lives in journals and folds; any stack is a zero-authority reader.** + Losing the stack loses nothing. − Two places to look.
- **S2. One sink (OpenObserve)** for logs and risk rows. − Against his August ruling.
- **S3. Prometheus gauges exported from the fold** (heat, burn, distances) for Grafana. − Duplicates numbers; must stamp the fold watermark.
