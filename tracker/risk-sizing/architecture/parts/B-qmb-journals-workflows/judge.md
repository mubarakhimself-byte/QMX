# The judge, the try ledger and the study spec

Part B, sub-area 2. Decisions: spine AD-202 (open and close), AD-206 (conformance), AD-207 (the judge). Shapes: `CONTRACTS.md` §3. Slices: `BUILD-SLICES.md` B3, B6, B13, B14. Amended after R1 (`architecture/review/R1-FIXES-X1-B.md`).

**In plain words.** QMX counts every test anyone runs. Before a unit is tested, the rules of the test are written down: which markets, which dates, what record counts as enough. Every market is judged by the same rule, and a market that looks best is pulled back toward how the unit did everywhere, so luck does not reach his card. Scripts give the verdict; an agent explains it; he decides.

His words: "we don't want to be too strict" (T1:1574); "nothing actually ever enters live without me" (T1:1574); "Favor determinism over non-determinism. That's the whole point of QML" (T3:903). "Every test try is counted." (T3:903); what he meant was answered in chat (ledger "settled", T3:940-942).

Ledger rows that bind: B-09, B-10 (seed), CC-10, CC-11, CC-20, A-03 (seed), "settled": the luckiest-market trap goes in the judge without asking him.

## 1. Verdict: core

The judge, the run records, the try rows, study specs, verdicts and baseline cards live in the new package `qmx-agents/packages/qmx-judge` (Level 0 LC-A0-07), outside every tester. Why: a tester that judged or counted could change the score. The package is pure functions plus the lander; its only side effects are Library landings through the host's landing port and materialise calls through the market-data door, both injected.

## 2. The run record and the try ledger

**Open** (from the supervisor's job path, AD-202). The lander `qmb-run`:
1. parses the run request against `qmx.qmb.run-request/1`; a schema problem refuses with every problem (AD-11);
2. resolves the study spec (`study-spec` item, pinned version); a request with no study gets an implicit spec built from its fields and marked `origin = quick`;
3. resolves the unit version and its compiled fingerprint; looks up the recorded G verdict for that fingerprint (Part A's `test-report` with `check = "qml-g/1"`, A CONTRACTS §3.3); with none recorded, it first runs a `behaviour_check` job of the same unit on the same tester through the `run_job` callable the host injects into the lander, lands that `test-report` and a try of kind `check`, and goes on only on a passing safety verdict (a failing one refuses the run with the report linked); a `behaviour_check` request itself needs no G record;
4. copies the model that built the unit and its training cutoff from the unit's lineage into the request (QB-11);
5. resolves the data recipe through the market-data door with the study's holdout and materialises the partitions into `data/runs/<run_id>/in/` of the tester's volume (hard link where store and volume share a drive, else copy; INFERRED, checked in the slice); a missing month refuses, naming it and the template that downloads it (LD-06);
6. copies the unit document, its pinned block sources, the instrument snapshots and the cost profile into the same folder;
7. mints the run id `qmbr-<machine>-<ulid>` and lands a `try` item: `{kind: run, run_id, family, unit, study, tester, principal, place, at, state: opened}`;
8. returns the run id and the inputs the job receives.

**Close.** The lander verifies every file in the bundle against its fingerprint, lands the `backtest-result` (fields and blobs in `CONTRACTS.md` §2) with edges `consumed` to each dataset card version, `uses` to the unit version, `tests` to the study spec, and lands a second `try` item `{state: landed, result}` that links to the first. **Fail** lands the result with `status = failed | killed`, the reason (for a kill under a memory limit he set, the limit in megabytes, MA-08), no measures, and the `try` item `{state: failed}`.

**Why two `try` items and not one item edited.** Each item is written once by one writer, and nothing ever edits a shared record (Level 0 AD-25; poteto-mode's separate-before-serializing principle). Family counts are a query over `try` items.

**Every try, not only runs.**

| Try kind | Written by | When |
| --- | --- | --- |
| `run` | the lander | every run opened, whatever the door |
| `check` | the lander | a behaviour check run |
| `spec_edit` | the Library save of a `study-spec`, through the kind's registered checker (Level 0 AD-29) | a new spec version when any result exists against an earlier one |
| `shortlist` | the pre-session shortlist template's script | each market it shortlists |
| `paper_pick` | the tagging template's script | each market proposed for paper after reading backtests |
| `whatif_rerun` | the lander | a what-if filter that can improve a result (§4) |

**Family.** The root of the unit's `variant of` lineage at the time of the try, stored on the item. **Effective tries** are computed at read by clustering the daily R streams of the family's runs (correlation above a setting joins a cluster; ONC preferred; `[judge] cluster_correlation` default 0.5). A run with no daily R stream (failed, killed, zero trades) counts as one try by itself.

## 3. The study spec and the default chain

**The study spec is written first.** Fields (`CONTRACTS.md` §3): the claim card (what the unit claims: direction of edge, horizon, the sessions and conditions it trades), markets (a list, or "every market I admitted for this unit"), windows, the record needed (or the sequential score), the preset, the shrinkage estimator, the correlated-market threshold, his holdout choice (off by default, ruling 137), the cost profile rule, the fill model, `allow_gaps`, `motion`. It is also the UI-editable run config: editing it before any result is free; editing it after a result exists lands a `spec_edit` try.

**The default chain, cheapest first** (research 26 §2.1). Each step states what it can and cannot fail on (MIS-11):

| Step | Can fail on | Cannot fail on |
| --- | --- | --- |
| 1. Claim card present | a missing or empty claim | anything about results |
| 2. Signal against random entries (rule significance; entry edge ratio above 1.0 at the claimed horizon) | a signal no better than random entries | an edge that only shows after costs |
| 3. Cost stress (1.5x in the shipped preset) | an edge that costs erase | luck in the sample |
| 4. Walk-forward efficiency | settings that only fit the in-sample | an edge that decays after the last window |
| 5. Try-corrected verdict (deflated Sharpe with the family's effective tries) | luck from many tries | a real edge that has too few trades yet (it reads "too thin to judge") |
| opt-in: shuffled-readings proof | a unit that leans on a reading's timing | a unit that computes its own inputs: marked "cannot fail here" |

**One rule for every market** (the luckiest-market trap, QB-10). Every market whose record reaches the threshold is judged by the same rule; none is dropped for looking bad; each judged market is a try; each market's result is shrunk toward the unit's whole result by n/(n+k), where the spec fixes k's estimator before the run (default: estimated from the spread between the unit's markets); markets whose trade results correlate above a setting count as one record; a market that became a candidate needs fresh trades after it became one before it reaches his card.

**Presets, each with its origin** (nothing overrides a shipped default silently):

| Preset | Values | Origin |
| --- | --- | --- |
| `shipped` (default) | 100 trades, walk-forward efficiency 0.5, Monte Carlo 5th percentile above 0, 1.5x costs, deflated Sharpe confidence 0.95 | the shipped `b-build-and-prove` template |
| `old-qmx` | 200 trades, +0.15R after costs, 2x cost stress, PBO below 0.25 to pass and above 0.50 dead | research 08 §1.1 |

**Always shown, never gates:** each result with the unit's own sizer and with a fixed-size baseline; entry edge ratio and exit capture; `costs_uncalibrated`; motion on against motion off; placeholders in the unit.

**Zero trades** (QB-15). A result with `zero_trades = true` is never a pass; the verdict reads "placed no trades", and the behaviour report says whether the unit declared that it may not trade on that slice.

**Like with like** (QB-13). The judge pools a family's results only within one tester version, or across two versions linked by a passing parity report.

## 4. The what-if split (QB-22)

| What-if | Effect | Counted? |
| --- | --- | --- |
| remove the top 5% of trades; fixed size instead of the sizer; entry one bar late; cost shock; missed limit fills; stops on mark price; funding at each settlement | can only worsen a result: a robustness **view** computed by the tester on a landed result | no; it lands as part of a `robustness` result |
| a filter that removes trades by a rule (a session, a reading's state, a day of week) | can improve a result | yes: a `whatif_rerun` try and its own run |

The tester declares each scenario's direction in `capabilities`; the lander refuses a scenario declared "worsen only" whose result improves the base measure (a deterministic check, so a mislabelled filter cannot slip through uncounted).

## 5. Verdicts, baseline cards, proposals and forecasts

- **Verdict** (`verdict` kind): the chain's outcome per market and overall, the effective try count, the preset, the judge version, the checker version, the tester, the study version. A new judge version judges again beside the old verdict, never over it (WF-12).
- **Baseline card** (`baseline-card` kind): frozen when a unit passes: its record in R, its Monte Carlo cone, its cost and fill assumptions, its trade rate, the readings range seen when its settings were earned. The decay check compares live against it: CUSUM on R, the cone, cost and fill drift, trade-rate drift, readings drift; the answer is OK, Watch or Alarm, and it informs only (the action after an alarm is the risk session's).
- **Proposal card** (`proposal-card` kind): what waits for his click (paper, live, a new market), with the verdict, the try count, the preset, the placeholders still in the unit, and the evidence links. It never moves a unit; his click does (Part A's lifecycle machine, recorded by Part C's promote action through the host's lifecycle writer).
- **The judge's own lifecycle move.** When a verdict on a `draft` unit lands, This PC's host writes the move `draft` to `tested` (pass) or `draft` to `parked` (fail) through `qmx_host/lifecycle.py`, with `by.kind = judge` and the judge run's principal (R1-B-06). The judge never moves a unit toward paper or live.
- **Forecast** (`forecast` kind): a dated call written before a session (market, direction or state, horizon, confidence), scored after it by a script against the market's recorded data (WF-11). The forecaster never marks its own call.
- **Death certificate** (`death-certificate` kind): a typed cause of death from an appendable list, classified by a script first, then explained; it also writes a `dead_end` memory row (engine AD-18) so agents do not repeat it.

## 6. Numbers (starting defaults, all editable; research 43 §5 unless marked)

| Setting | Default |
| --- | --- |
| `[judge] preset` | `shipped` |
| `[judge] signal_p` | 0.05 against random entries |
| `[judge] entry_edge_ratio_min` | 1.0 |
| `[judge] cluster_correlation` | 0.5 (daily R) |
| `[judge] correlated_markets` | 0.6 (trade results) |
| `[judge] shrinkage_k` | estimated from the spread between the unit's markets; half weight at 100 trades if unknown |
| `[judge] fresh_trades` | the later of 30 trades or 2 weeks |
| `[judge] thin_span` | 4 weeks minimum to earn; "too thin to judge" after 6 months without the record |
| `[judge] paper_before_card` | the later of 30 trades or 4 weeks, sequential score not below its start |
| `[judge] sequential_pass` | 20, bets 0.025, 0.05, 0.1, 0.2 on trade R after costs |
| `[judge] refinement_rounds` | 15 without a validated gain stops a family spawning variants |
| `[judge] decay_cadence` | nightly per unit, inform only |
| `[judge] replay_match` | about 80% of paper trades |

## 7. What must not break

The shipped `b` template's defaults keep their values as the `shipped` preset. Governed Library kinds keep landing as drafts that wait for his yes (`qmx_library/landing.py:1-18`). The judge refuses nothing that is his to decide: it never blocks a promotion click; it only writes verdicts.

## 8. How it is checked

`pytest qmx-agents/packages/qmx-judge` with literal expected values: the luckiest-market simulation (20 markets, true edge +0.06R, best-looking +0.23R; the shrunk estimate within a setting of the true edge); a family of 51 simulated variants whose clustering finds 11 effective tries; a zero-trade result never passing; a spec edit after a result landing one `spec_edit` try; a "worsen only" scenario that improves refused; a judge version bump landing a second verdict beside the first.

## 9. Growth seams

A new check is an opt-in step on the judge card (data). A new preset is data. A new try kind is an addable enum value. Portfolio-level judging is the risk session's.
