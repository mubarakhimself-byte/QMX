# X3 brainstorm, headless run (working record)

Topic: brakes, restores, exits and drift for the unit risk-and-sizing template.
Goal: hybrids of Stage A components, each serving a named template need. Brakes must not choke a healthy unit.
Context: `linking/STAGE-B-BRIEF.md`, R9 definitions, A1-A5 components, SEEDS (A6, A9, A10, A25-A28, C7, C10, C19, C21, C27, C28, C31-C33), G8, G9, G11, R8.
Run by one agent playing every role. No human in the loop. Ideas went to `.memlog.md` as they landed.

Arithmetic used in this run: `x3_brake_sim.py`, output `out-200.txt` (200 paths per scenario, 250 days, size 1 per trade, costs netted into outcomes). It is model arithmetic, not evidence about real strategies.

## What the simulation said (read before the techniques)

| Unit | Brake | Healthy R kept | Healthy fire days | Note |
|---|---|---|---|---|
| fs10 (55 %, 10/day) | 2 full stops a day | 43.8 % | 97.7 % | the old breaker chokes |
| fs10 | 3 losses in a row | 83.9 % | 40.6 % | |
| fi10 (FI cuts, 10/day) | 2 full stops | 65.3 % | 80.4 % | |
| fi10 | 3 in a row | 74.6 % | 59.7 % | cuts make it fire more |
| fi40 (40/day) | 2 full stops | 18.1 % | 100 % | |
| fi40 | 3 in a row | 27.8 % | 98.4 % | |
| all units | money at own p1 (window of 10+ trades) | 99.4-99.8 % | 1.0-1.2 % | frequency-fair |
| all units | loss points at own p99 | 99.9-100 % | 0.4-2.0 % | FI-fair |
| all units | ladder: halve at own p10, bench at own p1 | 97.3-98.8 % | 6.3-10.5 % | regime R up, drawdown down |
| all units | AIMD as a pure brake (x0.7 on own p10 day, +0.05 per green day, cap 1.0) | 32-84 % | 58-98 % | halves drawdown, chokes |

Timing test against a random brake with the same fire rate and the same action, in a world with bad spells (good ~100 trades, bad ~50):
- 3 in a row beats its matched random control by +20R (fs10) and +22R (fi10) over 250 days, but costs 40-63R on a healthy unit.
- Money at own p1 beats its control by about +1R at 10/day (noise) and +26R at 40/day.
- 2 full stops at 40/day loses to its random control (-33R): a brake that fires every day carries no information.

Slow lane, each detector tuned to 5 % false alarms per 250 healthy days:
- Trade CUSUM caught a dead edge (-0.05R after day 100) in 92-99.5 % of runs for 10-40/day units, median 10-66 days; 52-69 % for slow units (4/day, 2/day), median 66-99 days.
- Breaker fire density caught it in 25-58 % (99.5 % at 40/day), median 36-93 days. Slower, calmer.
- On a bad week at 40/day, CUSUM alarmed 54.5 % of the time, density 18 %.
- At 40/day, "demote for good at the alarm" kept 614R in the bad-week world; "graded and reversible" (half size at half the threshold, paper at the threshold, back as the statistic falls) kept 902R of 950R.

## Technique 1: Morphological Analysis (components are the parameters)

| Parameter | Options (component ids) |
|---|---|
| P1 What it reads | loss count (A2-083, A2-054, A2-056); loss points by size (A2-091, A1-050); money against own percentile (A5-144); drawdown from unit high-water mark in R (A5-022); budget burn (A2-028); breaker fire density (A2-086); trade CUSUM (A2-149); e-process (A2-155); input drift (A2-166); environment tells (A2-111, A3-088, A3-095); peers (A2-033) |
| P2 Anchor | day start (A2-064); rolling N trades (A2-116); session (A2-108); unit high-water mark (A5-022); the frozen card (A2-216); the expected fire band (A2-088) |
| P3 How the threshold derives | fixed number (old rules); own percentile from the card (A5-144, A2-227); false-alarm budget (A2-152, A2-158); peer-relative (A2-033); zones (A2-196) |
| P4 Lever | bench (HALTED for the day); halve (REDUCING); level down (A2-190); paper (A2-083); scope off (A2-128); flatten (A2-002) |
| P5 Restore | timer (A2-047, warned against); state-based clear (A2-007); half-open probe (A2-032); ladder per cohort (A2-190); e-value (A2-221); his click (A2-103); memory ceiling (A5-134) |
| P6 Scope | trade, position, unit, cluster, methodology, class or region, BMS, account, node |
| P7 Proof | none; matched random control (A2-135); placebo (A2-136); precision and recall (A2-142); trip tax (A4-202) |
| P8 FI and breakeven counting | full stops only (A2-083); non-wins (MQL5 1367 trap); at or worse than -q (A2-090); by size (A2-091) |

Configurations no generation tried, worked out below:
- {money own p1, rolling 10+ trades, card percentile, bench, half-open probe, unit, random control, by size} → fast breaker (H01, H15, H13).
- {money own p10 then p1, same anchor, halve then bench} → graded ladder (H02).
- {fire density, expected band, Bernoulli CUSUM, level down, e-value restore, unit, precision} → slow breaker (H08, H09, H11).
- {peers, cluster, peer-relative, scope off, growing ejection, class, capped share} → peer ejection (H30).
- {input drift, card bands, zones, level down, new episode} → input-first drift (H51, H48, H53).
- {count, rolling own-p99 run length, halve, only when the unit's block-persistence test passes} → conditional streak attenuator (H05, H06).
- {loss points, cluster, hours clause} → event-level chorus (H20, H21).

## Technique 2: Concept Blending

- Circuit breaker + Basel traffic light: a money brake at own p1 is a one-day 99 % VaR exception. Basel counts exceptions over 250 days (0-4 green, 5-9 yellow, 10+ red). The breaker's own fire count is the slow lane, with a regulatory history behind the zone cuts (H08, H48).
- SQS + circuit breaker: spread quality as a class breaker (K of N blocked) (H29).
- Kill switch + Envoy outlier ejection: automatic scoped stand-downs with a cap on the share of a cluster ejected (H30, H62).
- Hours clause + chorus flag: one event, one count, across a cohort (H20, H21).
- Survival analysis + fast invalidation: the FI trigger as a hazard model (H42).
- VPA + brake threshold: a brake's percentile is a learned number with bounds and an applier mode (H61).
- Dose escalation + restore: restore one level per clean cohort; a bad cohort sends the level down (H15).
- Topstep tiers + demotion: down the same day, up only after a dwell of active days (H49, H53).
- Heparin nomogram + drift zones: a dead band, steps sized by distance from the band, recheck after a settling time (H48).
- Reinsurance reinstatement + restore: a restore is paid for with evidence (H18).

## Technique 3: Forced Relationships (distant pairs)

- Triple penance x restore ladder: recovery takes about three times as long as the fall, so the restore dwell must be short enough not to triple it again (H15 note).
- LULD bands that double near the open and close x fast invalidation: FI cut levels widen in the first and last minutes of a session (H39 note).
- Credit-card limits x agent proposals: the party that asks most for more size should get the slowest raise; any raise asked right after a loss is flagged (H69).
- BOIN dose elimination x memory ceiling: a size level that tripped twice is locked out for a period (H17).
- Envoy peer ejection x FI rate: if one unit's FI rate jumps while peers on the same instrument do not, it is the unit; if all jump, it is the market (H30, H50).
- Kill switch x survival analysis: a node-health hazard (disconnects, rejects, stale quotes) sets the soft-kill exit schedule (wild, H66 family).
- SQS x re-promotion: no restore or re-promotion while the scope's SQS is not green (H15, H53).
- Exchange price collars x re-entry: re-enter only when fills land inside collars (H33).
- Man Group "drawdown rule as decay detector" x worry lines: drawdown thresholds widen with time in service and differ by style (H56).
- Hsieh restart x two anchors: a unit's working anchor may restart; the floor and the book high-water mark never do (H25).

## Technique 4: Cross-Pollination (fields and what crossed)

| Field | What crossed into X3 |
|---|---|
| Power grids | nearest protection first, recloser then lockout, staged load shedding (H59, H15, H02) |
| SRE | two-window burn rate, budget freeze, alert precision, METRICS_ONLY, enforcing ramp (H22, H12, H14) |
| Clinical trials | BOIN levels, planned looks, alpha spending, futility, effective challenge, accelerated titration (H48, H49, H53) |
| Medicine (monitors) | alarm fatigue, precision of alarms (H12) |
| Insurance | hours clause, reinstatement priced (H20, H18) |
| Networking | AIMD, CUBIC memory, half-open, backoff, outlier ejection (H07, H17, H15, H30) |
| Kubernetes | VPA modes, HPA asymmetric windows, missing data cautious (H61) |
| JIT compilers | guarded guess, named deopt reason, freeze after N trips (H61) |
| Control | Simplex fallback with dwell, robust MPC reserve after shocks (H61, H32) |
| Aviation | envelope protection, one alert at a time (H75, H12) |
| Banking | Basel zones, limit hierarchy below the sum, warnings before hard limits (H48, H24) |
| Immunology | danger accumulation (H66) |
| Audio | attack and release vocabulary for every brake row (H58) |
| Betting | bookmaker limits as a capacity ceiling (collision with X2) |

## Technique 5: Trait Transfer

| Trait | From | Transferred to |
|---|---|---|
| Expected fire band | Basel exceptions, July `breaker_expectation` | every brake row (H09, H58) |
| Half-open probe judged as a group | resilience4j | every restore (H15) |
| Minimum events before a signal | Kulldorff-Silva | every count and density statistic (H08) |
| One event, one count | reinsurance hours clause | fire density, chorus, methodology CUSUM (H20) |
| Capped share | Envoy | isolation and BMS shedding (H30, H27) |
| Two windows | SRE burn, SQS percentile gate | drift detectors and isolation tells (H22, H28) |
| Dead band, step by distance | heparin | drift zones and restore (H48) |
| Settle before the next change | heparin, AWS warm-up | every restore and every size step (H15) |
| Level elimination | BOIN | memory ceiling (H17) |
| Random control | MQL5 23482 | every brake, gate, exit and detector (H13) |
| Competing risks | survival analysis | open-trade exits (H42) |
| Named falsifying condition | Steward | fast invalidation (H40) |

## Technique 6: Evolutionary Pressure

Selection rule, stated before breeding: a fast unit brake survives only if, in `x3_brake_sim.py`, it
1. keeps at least 97 % of the no-brake R on a healthy unit at every tested frequency (2 to 40 trades a day), and
2. beats a random brake of the same fire rate and action in the bad-spell world, or cuts the 95th-percentile drawdown there, and
3. derives its threshold from the unit's own record, not a fixed number.

- Generation 0: 2 full stops; 3 in a row; 3 non-wins; loss points fixed; money fixed; AIMD as a pure brake.
- Selection: 2 full stops, 3 in a row and 3 non-wins fail rule 1 (keep 18-84 %). AIMD fails rule 1 (32-84 %). The fixed versions fail rule 3.
- Survivors: loss points at own p99; money at own p1 over a window of 10+ trades.
- Generation 1 (crosses with REDUCING): money_h (halve, not bench); 3 in a row with halve. money_h passes rule 1 but adds almost nothing in bad spells. 3 in a row with halve keeps 87-92 % at 10/day and 64 % at 40/day: fails.
- Generation 2 (cross with staged shedding): ladder = halve at own p10, bench at own p1. Keeps 97.3-98.8 %; bad-spell R +3 to +43R over no brake; 95th-percentile drawdown down (fi40 178 → 143). Passes.
- Generation 3 (mutations, not simulated): ladder whose percentiles tighten when fire density sits above its band (adaptive ladder); streak attenuator switched on only when the unit's own block-persistence test passes (conditional streak brake); AIMD kept only as a red-zone survival mode, never default.

Slow lane, same pressure (5 % healthy false alarms per 250 days fixed for all):
- Generation 0: breaker density alone; trade CUSUM alone; permanent demotion at the alarm.
- Selection on "catches a dead edge" and "survives a bad week": CUSUM catches most but trips on bad weeks at 40/day; density is calm but slow; permanent demotion throws away a third of a fast unit's year after a bad week.
- Survivor: graded and reversible demotion driven by CUSUM, with density as the calm second key for any step to paper (H11, H49).

## Technique 7: Solution Matrix (problems against component families)

Legend: ● strong component exists; ○ partial; · nothing.

| Problem | Trading practice | SRE and software | Trials and Basel | Grids and insurance | Statistics papers | MQL5 corpus | Old QMX |
|---|---|---|---|---|---|---|---|
| Count brakes punish frequency | ○ prop rules in money | ● burn rates | ○ | · | ● R9 sims | ○ | ○ loss points idea |
| FI and breakeven counting | · | · | ○ graded toxicity | · | ○ | ○ trap noted | ● Gen 3 -q, October points |
| Breaker as decay sensor | ○ Topstep call-down | ○ | ● Basel zones | · | ● CUSUM, e-detectors | ○ | ● WF3 density |
| Brake proof | · | ● precision, scorecard | ○ | ○ alarm fatigue | ○ | ● random control | · |
| Restore without choking | ● Topstep dwell | ● half-open, backoff | ● BOIN | ● recloser | ○ | ○ restore window | ○ |
| Losing together | ○ pods | ○ | · | ● hours clause | ○ N_eff | ○ | ○ chorus (null) |
| Class isolation on evidence | ● exchange breakers | ● Envoy | · | ● selectivity | ○ turbulence, AR | ○ | ○ April region shift |
| News windows | ○ | · | · | · | ○ event studies | ○ trap list | ● April soft kill, Gen 3 window |
| Stop mechanism per style | ○ Carver | · | · | · | ● Kaminski-Lo, Clare | ○ | ○ April dynamic SL/TP |
| FI cut size | · | · | · | · | **· (gap)** | ○ MAE stops | ○ 0.35R guess |
| Breakeven move value | · | · | · | · | **· (gap)** | ○ modes | ○ ratchet built |
| Bad day vs broken edge | ○ Topstep | ○ HPA windows | ● zones, looks | · | ● e-processes | ○ | ○ nightly check |
| Re-promotion | ○ Topstep call-up | ○ | ● new episode | · | ● restart weights | · | ○ 10 wins |
| Kill switch and SQS fit | ● CME kill switch | ○ | · | · | · | ○ | ● kill switch, SQS |
| Units with no price stop | · | · | · | · | ○ tail budget | ○ | **· (gap)** |
| Low-frequency units | ○ | ● low-traffic SLOs | ● calendar looks | · | ○ | · | ○ paper windows |
| Energy and single stocks | ○ EIA, halts | · | · | · | ○ thin | · | **· (gap)** |

Empty cells worth naming: no paper measures a fixed fractional early cut after costs; nothing tests a breakeven move after costs; no source says how pods restore a cut allocation; no tested class isolation for intraday units; no money brake for a unit without a price stop; energy and single-stock brakes rest on contract facts only.

## Synthesis (insights)

1. The fair trigger for a unit's fast breaker is money or loss points at the unit's own percentile over a window of at least ten trades. It fires about 1 % of days at any frequency and keeps over 99 % of a healthy unit's edge. Count triggers keep 18-84 %.
2. Fast day brakes carry almost no timing information on independent trades. Their value is tail shaping and, above all, the record of fires. Count brakes do carry timing when losses cluster, but pay for it heavily on healthy days.
3. The old circuit breaker's decay role survives, but its fire density is a slower decay sensor than a CUSUM on trade R. Density is the calm second key; the trade stream is the fast key.
4. Graded, reversible demotion beats permanent demotion where it matters most, at high frequency after a bad week.
5. Every brake needs four numbers on its row: expected healthy fire rate, precision, trip tax, and its margin over a matched random control.
6. Restores decide performance as much as trips do: half-open probes, settling and memory ceilings stop both the sitting duck and the re-raise into the trip.
7. Exits are where evidence is thinnest. Fast invalidation and breakeven must be set from each unit's own excursions and proven against "no cut" and "one bar later".
