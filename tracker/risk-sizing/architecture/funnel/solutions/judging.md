# Judging: the judge, the count of tries, and the luckiest-market trap

**What this part is.** How a unit's results become a verdict: the judge's checks in order, the count of every try, the study rules fixed before results are read, the "picking the best-looking market" trap (weak spot 3), paper as the honest out-of-sample test, and the baseline card that later decay checks read. QMB computes results (`qmb.md`); this part decides what they mean.

**Verdict: core.** The judge is a shared block and a subworkflow, the try ledger is written by the core's landing function, and the study spec is a Library record. None of it lives inside a QMB version, so a new tester cannot change the score (insight I3). This is the part research 43 called the product: when strategies are nearly free to make, judging them is what matters (STATE correction 10).

## His words

- "Agents should judge best of results from performance." (T1:1574)
- "we don't want to be too strict" (T1:1574)
- "judging and improvement should come from historical and paper trading" (T1:1574)
- "it is run on every bot across multiple instruments" (T1:442)
- "nothing actually ever enters live without me" (T1:1574)

## 1. What exists today

| Piece | State | Where checked |
| --- | --- | --- |
| QMB ledgers every trial (`role = trial`) | BUILT; no correction applied | research 08 §1.5; G1 §4.4 |
| Deflated Sharpe in a template block `_shared/overfit-gates`; the gate scripts copied into `b` and `d3` | BUILT as template content | research 43 F5, "Subtract first" item 3 |
| The shipped `b-build-and-prove` defaults: 100 trades, walk-forward efficiency 0.5, Monte Carlo 5th percentile above 0, 1.5x costs, deflated Sharpe confidence 0.95 | BUILT | research 43 §5 (CHECKED in r44) |
| `b-build-and-prove` hard-codes a family holdout and a 60/20/20 split | BUILT, conflicts with "holdout is his choice per study" | G2 §4, trap 9 |
| PBO and CSCV | DESIGNED in `qmb/robustness/`, deferred | research 08 §1.2 |
| Cost calibration | MISSING (GAP-0048) | G1 §4.4 |
| Governed Library kinds land as drafts that wait for his yes | BUILT | G2 §12 |

## 2. Harvest: solutions already on disk

| Solution | Where | Fits now? |
| --- | --- | --- |
| Count every try at the door, hand runs included; the judge refuses results without a door-issued run id | research 43 F5, §4 L08-04 | Yes, and the door is now the core landing function (because QMB is swappable) |
| Count effective tries by clustering result streams (daily R), never by edit type; 51 simulated variants: clustering found the true 11, the shortcut formula 1.9 | research 26 §3; research 43 F5 | Yes |
| The default chain, cheapest first: claim card, signal check against random entries, cost stress, walk-forward, try-corrected verdict; everything else opt-in | research 26 §2.1; research 43 §3.4 | Yes |
| Paper on demo as the honest out-of-sample test with holdouts off; counts only for the frozen version that took it | research 26 §2.2-2.3; research 43 §3.4 | Yes |
| One rule for every market, fixed before results are read; every judged market a try; each result pulled toward the unit's overall result by n/(n+k); correlated markets count as one | research 24 §2; research 43 §3.1 | Yes; the ledger's "settled" list says to put it in the judge without asking him |
| The record needed is computed per unit, or replaced by a sequential score checked after every trade | research 24 §3 | Yes |
| Two presets: the shipped `b` values as default, old QMX's R numbers as a second preset, each with its origin | research 43 §4 L08-10; research 08 §1.1 | Yes |
| Show every result with the unit's sizer and with a fixed-size baseline | research 43 §3.4 (his "radioactive" (T1:1574) sizing point, STATE 27 Oct) | Yes |
| Entry edge ratio and exit capture beside every verdict, never as gates | research 26 §4 | Yes |
| One frozen baseline card per unit, read by the decay check | research 08 §1.6, §2.3 | Yes |
| The judging skill checks what an agent cannot edit: the try ledger, the study spec, his holdout choice, costs present, failed children present | research 43 §4 L08-11 | Yes |
| Agents cannot check themselves; models' errors correlate across providers, so several models are review lenses, never a vote | research 29 §3; research 43 §4 | Yes |
| Overfitting grows with refinement depth; gains decay after about 15 rounds | research 11 (STATE row) | Yes, as a stop number |

## 3. The shapes

### Shape A. A core judge with a core try ledger and a study spec written first (recommended)

- **What.** A pure judge block (scripts) plus a `judge` subworkflow every finding, expansion and rewrite template calls. The core landing writes the try ledger. A study spec (a Library record) fixes the rules before any run: which markets, which windows, the record needed, the shrinkage rule, the preset, his holdout choice. A judging skill explains verdicts in plain words; it never decides.
- **Hard cases.** A QMB variant (the core counts); an agent rerunning with a changed rule (changing the spec after reading results is itself a counted try, S064); a script reading prices directly (no run id, no verdict, S062); many correlated markets (clustered into one record).
- **Maintain.** One judge instead of copied gate scripts in `b` and `d3` (subtract first).
- **Explain.** "QMX counts every test anyone runs. A unit is judged by rules written down before the results came in. The same rule applies to every market."

### Shape B. Each QMB version judges its own results

- **Why not.** A new version could judge differently; the score would follow the tester, not the unit. It breaks variants side by side.

### Shape C. Agents judge with a skill, scripts only for the numbers

- **Why not.** His "Favor determinism over non-determinism" (T3:903) and research 29: agents cannot check themselves. The skill explains; it never passes or fails anything.

**Pick: Shape A.**

## 4. The luckiest-market trap, solved (weak spot 3)

The trap (research 24 §2.1, simulated): twenty markets, a hundred trades each; the best-looking market looked like +0.23R a trade while its true edge was +0.06R. Path A (a market's own settings earned from the unit's own record there) removes "from thin air" but not this.

**The rule, one line in the judge:**
1. **Written first.** The study spec names the markets, the record needed and the rule before any run. Editing it after reading a result is a counted try (S064).
2. **Same rule for every market.** Every market whose record reaches the threshold is judged the same way; none is skipped because it looked bad.
3. **Every market counts.** Each judged market is a try in the family's ledger; so is every market an agent shortlists and every paper market chosen by reading backtests (research 24 §1, §2.8).
4. **Pulled toward the whole.** Each market's result is shrunk toward the unit's overall result by n/(n+k) before any ranking (S065). In the same simulation the pulled estimate matched the true edge.
5. **Correlated markets are one record.** Markets whose trade results move together above a threshold (EURUSD and GBPUSD on one dollar move) are judged as one (S063).
6. **Fresh trades.** A market that became a candidate needs some trades after it became one before it reaches his card (research 24 §2.2 options B and D).

The record needed is not typed: it is computed per unit from its own spread of results, or replaced by a sequential score checked after every trade (research 24 §3). A fixed 100 trades passes a real 0.1R edge about one time in four; 270 about half the time; about 620 four times in five.

The shrinkage weight k (party P7, open clash). Lead's call: the study spec fixes the estimator before the run (default: k estimated from the spread between the unit's markets, as research 24 §8 does), and an agent cannot change it after reading results without a counted try. Why: estimated k is more honest than a fixed number; fixing the estimator in the spec closes the "tune k" loophole. How to undo: set a fixed k in the preset.

## 5. The default chain and the presets

**Cheapest first; most units die in the first three steps, which take seconds** (research 26 §2.1):
1. The claim card exists (written before any run).
2. Signal check against random entries (rule significance; entry edge ratio above 1.0 at the claimed horizon).
3. Cost stress.
4. Walk-forward.
5. The try-corrected verdict with the family's effective try count.

**Opt-in on the judge card:** semantic checks, ablation, sensitivity and plateau, the three-market challenge, the robustness what-ifs, PBO per family, the dark-MIS, shuffled-readings and hindsight-premium runs (research 43 §3.3), the context check once trades carry stamped readings.

**Two presets, each with its origin, nothing overriding a shipped default silently:**

| Preset | Values | Origin |
| --- | --- | --- |
| Shipped (default) | 100 trades, walk-forward efficiency 0.5, Monte Carlo 5th percentile above 0, 1.5x costs, deflated Sharpe confidence 0.95 | the shipped `b` template |
| Old QMX | 200 trades, +0.15R after costs, 2x cost stress, PBO below 0.25 to pass and above 0.50 dead | research 08 §1.1 |

**Always shown, never gates:** every result with the unit's own sizer and with a fixed-size baseline; entry edge ratio and exit capture; "costs uncalibrated" while GAP-0048 is open; motion on against motion off (`unit.md` §4).

## 6. Paper: the honest test

With holdouts off by default (his choice per study), paper on a demo account is the out-of-sample test, because nobody could fit a unit to trades that had not happened (research 26 §2.2). Paper trades count only for the frozen version that took them; an edit made after reading a paper result is a counted try that restarts the paper record. Paper may start once the claim card, the signal check and the cost check pass, with the rest of the judge running beside it (research 43 §8, recommended answer; a switch he controls). Live is only his click.

## 7. The baseline card and decay

A unit that passes gets one frozen baseline card: its test record in R, its Monte Carlo cone, its cost and fill assumptions, its trade rate, the readings range seen when its settings were earned (research 08 §1.6; research 24 §4.1). The nightly decay check per unit journal compares live against that card: CUSUM on R, the cone, cost and fill drift, trade-rate drift, and readings drift. It informs (OK, Watch, Alarm) and never acts on its own; what happens after an alarm is the risk session's (research 24 §4.2: an automatic fallback would break standing order 7). The check runs as a workflow (`workflows.md`).

## 8. Who does what

- **Scripts decide** pass and fail, from the result, the ledger and the spec.
- **Agents propose** units, variants and markets, call the judge, and read its verdict through the judging skill, which explains in plain words.
- **He decides** what goes live, with one click on the proposal card, which shows the verdict, the try count, the presets used and the placeholders still in the unit.

## 9. Numbers (starting defaults, all editable; from research 43 §5 unless marked)

| Number | Default |
| --- | --- |
| Signal check | rule significance p below 0.05 against random entries; entry edge ratio above 1.0 |
| Gauges, warn and flag | free parameters above 10 and 20; backtests per idea above 30 and 70 |
| Remove-top-trades what-if | remove the top 5%, keep 80% of profit |
| Effective-try clustering | daily R correlation above 0.5 joins a cluster (ONC preferred) |
| Correlated markets counted as one record | trade-result correlation above 0.6 |
| Sequential score | pass at 20; bets 0.025, 0.05, 0.1, 0.2 on trade R after costs |
| Shrinkage k | estimated from the spread between the unit's markets; half weight at 100 trades if unknown |
| Fresh trades after a market becomes a candidate | the later of 30 trades or 2 weeks |
| Minimum calendar span to earn; "too thin to judge" after | 4 weeks; 6 months |
| Paper before his card | the later of 30 trades or 4 weeks, sequential score not below its start |
| Replay match on paper | about 80% of trades |
| Refinement rounds before a family stops spawning variants | 15 without a validated gain |
| Decay check | nightly per unit, inform only |

## 10. Connection points

| From | To | What crosses |
| --- | --- | --- |
| QMB app | core landing | finished results and daily R streams |
| Core landing | try ledger | run id, family, stream, tester id and version, principal |
| Judge | Library | verdicts and baseline cards (governed drafts) |
| Judge | proposal card | the verdict, try count, presets, placeholders, for his click |
| Decay workflow | judge baseline card and journals | the comparison and its state |

## 11. Open for the architecture step

1. The try ledger's home: a family record in the Library (picked, it travels with his content) or the engine ledger.
2. The study spec's schema.

## 12. Parked

- Portfolio optimisation as judging input (a template, `p1`, owned by the risk session).
- A meta-test of each judge step's lift on held-back data (research 08 §1.3 last row): after there are enough judged units.
