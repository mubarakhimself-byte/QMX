# Sub-area 2: the unit template, its numbers and how they move, identity, lifecycle, the socket and the dummy unit

Part A, 31 Oct 2026; amended 1 Nov by fixer X1-0A after review R1 (the dummy's slow number, its landing, and its slow rule's shrink). Decisions: AD-102, AD-103, AD-115, AD-116, AD-118 in `ARCHITECTURE-SPINE.md`. Shapes: `CONTRACTS.md` §1, §2, §4.3, §7, §8.

His words: "Unit is literally a replacement of a trading bot. It's just a self-configuring trading bot. Simple as that." (T2:788), "how do we make sure that those if-else statements can self-tune?" (T2:788), "we need the unit in terms of a template" (T3:904), "placeholders, I think is the right word" (T3:1087), "the unit is going to own its own exit" (T2:1000).

**Verdict: core** (a Library kind, a schema, templates, a pure lifecycle machine). A unit is never a mini app: two mini apps run it, QMB on history and the node on practice and live, which keeps "only the node sends orders" true.

## 1. What exists (CHECKED)

| Piece | Where | State |
| --- | --- | --- |
| The governed `unit` kind: lands as a draft for his yes; card and page tabs Logic, Results, Family tree, Markets (`fields.markets`), Versions | `qmx-agents/packages/qmx-library/src/qmx_library/kinds/unit.schema.json` | built; `fields.properties` empty |
| A shipped test that saves a schema-minimal item of every live kind, unit included | `qmx-library/tests/test_view.py:45-63`, `:110-128` | built; constrains the unit kind's schema (AD-111) |
| Parameter space (type, bounds, step, default, unit kind, UI flag); QMB's optimiser reads it | `qml/src/qml/declaration/parameters.py:1-60`; `qmb/src/qmb/optimize/__init__.py:411-424` (G1 §1.5) | built; the compiler projects numbers into it |
| "A tuned set mints a new bot" for bots | `qml/src/qml/declaration/bot.py:618-628` | built; units do not use it |
| Version graph with human-signed `continues-performance` | `qml/src/qml/declaration/versioning.py` | built; the identity table complements it |
| The `trade` kind with `r`, `initial_risk`, `worst_swing`, `best_swing` | `qmx-library/src/qmx_library/kinds/trade.schema.json` (G1 §7) | built; Part B's |
| The Lab's identity table | Lab AD-16 (`tracker/qma-v2/architecture/lab-and-pods/ARCHITECTURE-SPINE.md`) | designed only; no `identity_rule` in code (R0-18) |

## 2. What a unit holds

The document's field list is `CONTRACTS.md` §1. In trader terms: an idea with its sources; the markets it may trade with any market's own settings; the bar sizes and sessions it reads; the sides; the named parts (context, trigger, confirmation, filter, veto and the rest) each filled by tested blocks and joined by a stated rule; the exit set, the sizer and the halts; the readings it may use and what it does without them; every number with its measure, range and motion; and the lock of every block version it pins.

## 3. How a unit tunes itself (U-06, Q-12)

The answer to his if-else question, shown in data. The numbers inside the rules move by themselves, each inside a range he approved, by a rule written down before any test. The rules themselves (which blocks, which branches, which exits, how they combine) change only as a new version he approves.

| Kind | Moves | Driven by | Trades needed | Example |
| --- | --- | --- | --- | --- |
| fixed | never | nothing | none | EMA period 100 |
| derived (fast) | every bar | the market: a price statistic, the indicator's own history, a state the unit computes | none | `rsi_low` = the 20th percentile of RSI over its last 500 bars |
| calibrated (slow) | at its cadence, only when flat | the unit's own closed trades | a minimum count, then more for bigger moves | `min_trend_strength`, nightly or every 20 closed trades |

Four rules make the slow speed safe with few trades: a minimum count before the first move (each number may declare its own `min_count`; one that declares none takes the setting `min_trades`, 60); shrinkage toward the default by n/(n+k) with k = 100; at most one step per update and never outside the range; a market with a thin record shrinks toward the unit's pooled value across its markets. The motion runs inside QMB's replay exactly as live, reading only trades closed before the instant, so the backtest already includes the self-tuning and live motion is not a new try. QMB also runs motion off on the same split and reports the difference beside the verdict. Every slow move is a calibration row: which number, old and new value, the rule, the trade range it read and the statistic.

## 4. Identity and lifecycle

The identity table and its default rows are `CONTRACTS.md` §7; the lifecycle states, transitions and event body are §8. Three points carry most of the weight:
- A logic number moving inside its range is a calibration row, not a new version. A range, rule, cadence, fixed value, bar, session or markets change is a new version. A block swap, a role added or removed, a combiner change or a logic change for one market is a new unit in the family.
- Only his click moves a unit toward live on any market; tested to paper is his click by default, with an automatic switch that ships off. Only the unit's own risk rule moves it to stopped, and only his click resumes it.
- One admitted version per unit per market. A position belongs to the version that opened it until flat.

### Fork: where lifecycle state lives (principle-exhaust-the-design-space)

| Option | What | Verdict |
| --- | --- | --- |
| **A. A fold over events (picked)** | his clicks (written by This PC's host) and risk stops (written by the node) are events in journals with one writer each; `qml.lifecycle.fold` gives the current state | Picked: two writers never touch one record (one writer per partition, L0 AD-8); the state is reproducible from evidence; a pure, table-driven machine |
| B. A mutable state field on the unit item | each click or stop edits the item | Rejected: two machines would write one governed item; every state change would mint a unit version |
| C. A new Library kind per transition | one record per move | Rejected: duplicates the journal Part B already owns and adds a kind for no new capability |

## 5. The risk socket (room only)

Slot contracts: `CONTRACTS.md` §4.3. Places and today's stand-ins: `RISK-SIZING-POINTS.md`. Nothing here designs exit or sizing maths (ledger R-01, R-04).

## 6. The dummy unit (U-05, CC-17)

"Trend pullback (dummy)", family `trend-pullback`, the first template, installed out of the box: on first start the host lands it in his Library as a `unit` draft, once per store, and his yes publishes it (`BUILD-SLICES.md` A7, R1-A-05). Built only from blocks that wrap code QMX already runs, so the proof tests the unit and not new indicators.

| Part | Content | Number and motion |
| --- | --- | --- |
| Markets | EURUSD and XAUUSD at IC Markets on cTrader; history from the Library's Dukascopy bid and ask partitions | markets list |
| Stream | M15 closed bars, bid and ask | coordinate |
| Context | long when close is above EMA(100) and the trend strength, ROC of that EMA over 20 bars, is at least `min_trend_strength`; short is stated explicitly as the mirror case with the same blocks, which declare mirroring | EMA period 100, fixed, `published_convention`; ROC lookback 20, fixed; `min_trend_strength`: calibrated, percent, range 0.00 to 0.30, step 0.01, default 0.00, `min_count` 20, origin `builder_chosen` |
| Trigger | long when RSI(14) crosses back above `rsi_low`; short when it crosses back below `rsi_high` | RSI period 14, fixed, `published_convention`; `rsi_low`: derived, `percentile_of_own_history`, percentile 20 (fixed, range 5 to 35) over 500 bars (fixed, range 200 to 2,000); `rsi_high` the 80th |
| Entry order | market at the next bar's open | none |
| Exit set | protective stop beyond the last swing point plus a buffer of 0.02% of price; target at 2R; time-out after 48 bars | all `placeholder`, owner the risk session |
| Sizer | 0.5% of equity at risk at the stop, rounded down to the lot step; skip with a reason below the minimum lot | `placeholder` |
| Halts | none beyond the node's guards | empty, a warning on the card |

**The slow rule for `min_trend_strength`** (a motion block, `trend-floor-from-record@1`). At the market's day close, or after every 20 closed trades, once at least 20 trades have closed (its declared `min_count`): bucket the closed trades by the trend strength stamped at their entry into five buckets; take each bucket's mean R after costs; find the lowest bucket edge above which every bucket that holds a trade has a mean of at least zero; shrink that edge toward the number's default by n/(n+k), with n the closed trades read and k = 100; move the number one step toward the shrunk edge, inside its range. It is a logic number, not an exit or a size, so it shows self-tuning without touching the risk session's ground.

Two corrections from the R1 fix round. The minimum count is 20, not 60, because a one-month M15 run on two markets may close fewer than 60 trades, and the slow number must be seen to move in a real run, not only with a hand-fed journal (R1-A-01); QMB's B9 asserts at least one calibration row from real trades. The shrink now acts on the edge, as AD-103 says, because the first rule shrank each bucket's mean toward zero and then tested its sign, and shrinking toward zero never changes a sign, so the shrink did nothing (A-NEW-6, `scratchpad\x1-0a\shrink_sign.py`: 0 of 10,000 random cases changed). With 20 trades and an edge of 0.12, the target is 0.02 and the number moves one step to 0.01; with 400 trades the same edge gives 0.096.

Why this strategy: every trader knows it; on M15 it trades a few times a day per market, so a month of both markets should close 20 trades or more and move the slow number at least once (INFERRED; B9 asserts it on real data), and two years move it visibly; its stop is structural, so R is defined; QMB already replays bid and ask quotes.

```json
{
  "schema": "qmx.unit/1",
  "unit_id": "dummy-trend-pullback",
  "family_id": "trend-pullback",
  "title": "Trend pullback (dummy)",
  "claim_card": {"idea": "buy pullbacks in an uptrend, sell rallies in a downtrend",
                 "sources": [{"source_ref": "qmx:template", "locator": "built-in", "dated": "2026-10-31"}],
                 "written_at": "2026-10-31T00:00:00Z"},
  "markets": [{"market_id": "fx.eurusd", "instrument_ref": {"venue": "icmarkets-ctrader", "symbol": "EURUSD"}},
              {"market_id": "metal.xauusd", "instrument_ref": {"venue": "icmarkets-ctrader", "symbol": "XAUUSD"}}],
  "streams": [{"name": "m15", "market": "*", "bar": {"kind": "time", "size": "900"}, "input": "closed_bars", "price": "bid_ask"}],
  "direction": "both",
  "logic": {
    "long": {"slots": {
      "context": {"role": "context", "combiner": {"kind": "all", "when_inputs_absent": "no_signal"}, "bindings": [
        {"name": "trend", "block": "ema@1", "params": {"period": {"number": "ema_period"}}, "inputs": {"series": "m15.close"}},
        {"name": "strength", "block": "roc-of-series@1", "params": {"lookback": {"number": "roc_lookback"}, "floor": {"number": "min_trend_strength"}}, "inputs": {"series": "trend"}}]},
      "trigger": {"role": "trigger", "combiner": {"kind": "all", "when_inputs_absent": "no_signal"}, "bindings": [
        {"name": "rsi_cross", "block": "rsi-cross-back@1", "params": {"period": {"number": "rsi_period"}, "level": {"number": "rsi_low"}}, "inputs": {"series": "m15.close"}}]},
      "entry_order": {"role": "entry_order", "combiner": {"kind": "all", "when_inputs_absent": "no_signal"}, "bindings": [
        {"name": "next_open", "block": "market-next-open@1", "params": {}, "inputs": {}}]}}},
    "short": {"mirror_of": "long"}},
  "exit_set": [
    {"name": "swing_stop", "scope": "position", "block": "swing-stop-buffer@1", "params": {"buffer": {"number": "stop_buffer"}}, "inputs": {"series": "m15"}},
    {"name": "target_2r", "scope": "position", "block": "target-r-multiple@1", "params": {"multiple": {"number": "target_r"}}, "inputs": {}},
    {"name": "time_out", "scope": "position", "block": "time-exit-bars@1", "params": {"bars": {"number": "time_out_bars"}}, "inputs": {}}],
  "sizer": {"name": "fixed_fraction", "block": "fixed-fraction-at-stop@1", "params": {"fraction": {"number": "risk_fraction"}}, "inputs": {}},
  "halts": {"position": [], "unit": [], "account": []},
  "reads": [],
  "numbers": {
    "ema_period": {"kind": "fixed", "measure": "bars", "range": {"min": "20", "max": "300", "step": "1"}, "default": "100", "motion": {"mode": "fixed"}, "authority": "motion_inside_range", "origin": "published_convention"},
    "roc_lookback": {"kind": "fixed", "measure": "bars", "range": {"min": "5", "max": "100", "step": "1"}, "default": "20", "motion": {"mode": "fixed"}, "authority": "motion_inside_range", "origin": "builder_chosen"},
    "min_trend_strength": {"kind": "calibrated", "measure": "percent", "range": {"min": "0.00", "max": "0.30", "step": "0.01"}, "default": "0.00",
      "motion": {"mode": "shrink_from_own_trades", "source": "own_record", "cadence": {"every_closed_trades": 20, "at": "market_day_close"}, "min_count": 20, "shrink_k": 100, "step_limit": 1, "rule": "trend-floor-from-record@1", "rule_params": {"buckets": "5"}},
      "authority": "motion_inside_range", "origin": "builder_chosen", "applies_to_open_positions": false},
    "rsi_period": {"kind": "fixed", "measure": "bars", "range": {"min": "2", "max": "50", "step": "1"}, "default": "14", "motion": {"mode": "fixed"}, "authority": "motion_inside_range", "origin": "published_convention"},
    "rsi_low": {"kind": "derived", "measure": "ratio", "range": {"min": "0", "max": "100", "step": "0.01"}, "default": "30",
      "motion": {"mode": "percentile_of_own_history", "source": "price", "rule_params": {"percentile": "20", "window_bars": "500"}}, "authority": "motion_inside_range", "origin": "builder_chosen"},
    "stop_buffer": {"kind": "fixed", "measure": "percent", "range": {"min": "0", "max": "1", "step": "0.01"}, "default": "0.02", "motion": {"mode": "fixed"}, "authority": "motion_inside_range", "origin": "placeholder"},
    "target_r": {"kind": "fixed", "measure": "r", "range": {"min": "0.5", "max": "10", "step": "0.1"}, "default": "2", "motion": {"mode": "fixed"}, "authority": "motion_inside_range", "origin": "placeholder"},
    "time_out_bars": {"kind": "fixed", "measure": "bars", "range": {"min": "1", "max": "1000", "step": "1"}, "default": "48", "motion": {"mode": "fixed"}, "authority": "motion_inside_range", "origin": "placeholder"},
    "risk_fraction": {"kind": "fixed", "measure": "percent", "range": {"min": "0.01", "max": "5", "step": "0.01"}, "default": "0.5", "motion": {"mode": "fixed"}, "authority": "motion_inside_range", "origin": "placeholder"}},
  "pins": []
}
```

The `pins` list is filled by `unit_new` with the fingerprints of the QML blocks named above. The short side's thresholds use `rsi_high`, declared beside `rsi_low` in the shipped template (omitted above for length).

### Fixtures that ship beside it

| Fixture | Expected result |
| --- | --- |
| Broken document 1: `stop_buffer` in pips on XAUUSD, whose record defines no pip | one layer C error at `/numbers/stop_buffer/measure` naming the record |
| Broken document 2: a depth-imbalance trigger on a bars-only market with no fallback | one layer D error at the binding, naming the data level the market lacks |
| Broken document 3: `ema_period` default 400, above its range | one layer C error at `/numbers/ema_period/default` |
| Twin 1: always long (the context block replaced by a constant true) | safety verdict passes; behaviour warns `one_side_only` |
| Twin 2: an exit that cannot fire (time-out of 10,000,000 bars and no stop) | safety verdict passes; behaviour warns `exits_unfired` |
| Twin 3: a constant signal (RSI level outside RSI's range) | safety verdict passes; behaviour warns `signal_constant` and zero trades |

## 7. What "the unit works" means: the proof list he was owed

Each mark is shown by a command and its output on the real parts, not a throwaway (ledger CC-17). Marks 4, 5 and 7 run in QMB (Part B), mark 8 on the practice node (Part C); this part ships everything they call.

| # | Mark | Shown by |
| --- | --- | --- |
| P1 | It can be written down: the dummy saves as a draft; `unit_check` returns zero errors and lists the placeholders as warnings | the `unit_check` output |
| P2 | The checker catches mistakes: the three broken documents give three typed errors with pointers | the `unit_check` output |
| P3 | It compiles and is hosted through the unit door in QMB and the node with no change to their loops | the compiled fingerprint loaded by both |
| P4 | QMB trades it: two years of EURUSD and XAUUSD M15 with money and R; a rerun gives the identical trade list | two results and a diff |
| P5 | It tunes itself honestly: motion on and off on the same split; calibration rows show `min_trend_strength` moving from named trades; `rsi_low` stamped on every decision row | the rows and both results |
| P6 | It stands alone: a scan of the compiled unit's read surfaces shows nothing beyond its own machine | the scan output |
| P7 | The same judging rule for both markets, each a counted try | the judge's card |
| P8 | It trades on demo with protection at the broker; the journal matches QMB's replay of the same days | node journal against replay |
| P9 | A cheap model can write one: a haiku agent with the schema, the dummy and the rows writes a passing variant | the agent's tool log |

If P1 to P6 pass, the unit idea holds in code. P9 needs his Claude Code sign-in for haiku; nothing waits on it.

## 8. Must not break

The shipped every-kind view test (`test_view.py:110-128`) keeps passing: the unit kind's generated schema holds shape only, so a schema-minimal unit saves (AD-111; BR-A1 run). The page's Markets tab keeps reading `fields.markets`. Bots keep their seat rule (`bot.py:618-628`).

## 9. Edge cases handled here

QML-17, UT-04 to UT-09, UT-15 to UT-19, UT-21, UT-23, OP-03, OP-05 (handling lines in the spine's case table).

## 10. Ledger rows that bind it

U-01 to U-09, U-11 to U-16, U-20, CC-11, CC-17, R-01, R-04, R-11, C-06.

## 11. Seam for growth

A new kind of unit is a template. Per-market settings live inside the document; a unit that trades very many markets moves them to linked items in a schema version step with an upgrader (L0 P2 growth seam). A new motion mode is a motion block plus one row in the kind-to-mode table. The risk session's blocks fill the four socket slots with no change to the document's shape.
