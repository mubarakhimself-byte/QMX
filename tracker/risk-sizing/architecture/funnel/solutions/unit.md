# The unit, as a template

**What this part is.** The unit document: what a unit holds, how each of its numbers may move and how fast, what makes a change a new version, the states a unit moves through on each market, what it needs to trade alone, the risk socket it leaves for the risk session, and the dummy unit that shows all of it working. QML compiles and checks the document (`qml.md`); QMB and the trading node run it.

**Verdict: core.** The unit is a Library kind with a real schema and a template. It is never a mini app: units are Library items that two mini apps run, QMB on history and the node on practice and live (S147). That is what keeps "only the node sends orders" true.

**Labels.** CHECKED = read this session at the cited place, or run. INFERRED = reasoning. Grounding files are cited as G1 to G4b.

## His words

- "Unit is literally a replacement of a trading bot. It's just a self-configuring trading bot. Simple as that." (T2:788)
- "how do we make sure that those if-else statements can self-tune?" (T2:788)
- "we need the unit in terms of a template" (T3:904)
- "does a unit actually make sense?" (T3:1145) "A unit, it is self-optimizing, it's relying on very few things" (T3:1145)
- "you are smart enough to conjure up any strategy you want" (T3:1264) "All we want to make sure is that our unit template or our unit thing works." (T3:1264)
- "placeholders, I think is the right word" (T3:1087) "the unit is going to own its own exit" (T2:1000)

## 1. What exists today

| Piece | State | Where checked |
| --- | --- | --- |
| Library `unit` kind: governed (lands as a draft for his yes), identity by manifest, page tabs Logic, Results, Family tree, Markets, Versions | BUILT, `fields.properties` is empty | read this session: `qmx-library/src/qmx_library/kinds/unit.schema.json` |
| Pages are walks along Library links (`uses`, `produced-by`, `variant-of`) | BUILT | G4a §1.2 last row |
| Stage 0: dictionary cite, role binding, logic graph, exit slots with honesty labels | BUILT; compile and mint refused | G1 §8.1 |
| `trade` kind with `world`, `initial_risk`, `r`, `worst_swing`, `best_swing` | BUILT; imported fills carry no initial risk | G1 §7 |
| A bot that trades in a backtest | only in Python test fixtures | G1 §3.3 |
| The Book premise in four layers (QML intents, qmf-risk door, QMB run config, QMN seat door) | BUILT | G1 §0 item 4 |
| The ATC/PolicyPair non-Book seam | BUILT, no fills, costs or R | G1 §3.4 |

So the unit does not exist as a thing yet (research 52 §9.1 "The unit ... 0 lines"). Everything around it exists.

## 2. Harvest: solutions already on disk

| Solution | Where | Fits the newest rulings? | Carried as |
| --- | --- | --- | --- |
| The unit spec: identity and lineage, logic as named slots, coordinates, data needs, every number with kind, range, motion, authority and origin, context needs, risk socket slots, baseline pointer, claim card | research 43 F3 | Yes; "one JSON document" read as the declaration, not literally (ledger U-08) | §3 |
| Slots any trader knows, plus an open role list | research 43 §3.1; research 35 §6 item 1; funnel4 `qml-field.md` B022 | Yes | §3 |
| Identity by the type of edit (a lookup table) | research 43 §3.1 | Yes; risk numbers left to the risk session | §5 |
| Lifecycle as a state machine per unit with a state per market | research 43 §3.1 (review E10) | Yes; only he moves toward live; only a risk rule stops | §5 |
| Self-tuning as two speeds: price-driven fast, record-driven slow | research 53 §3.2 weakness 1; research 35 "safe to auto-tune"; research 24 trade counts | Yes, and nobody wrote the split down | §4 |
| A unit cannot show tuning through a placeholder that never moves; move one real number by a real rule | research 53 §3.2 weakness 2 | Yes | §8 (the dummy) |
| Three meanings of "self-configuring"; only the first two work without a human | research 20 (STATE row); research 53 §3.2 | Yes; rules change only by his click | §4 |
| A market's own settings (shrunk toward pooled) and a market's own version (a new unit in the family), both earned from the record there (Path A) | research 43 §3.1; ledger U-11, U-12, U-13 | Yes; the names are working words, he will think about them himself | §3 field `market_settings`; §5 |
| Timeframe is a coordinate; 1m and 5m of one logic on one pair is one correlated idea | research 43 §3.1; ledger U-09 | Yes | §3 coordinates |
| The steps before one trade, all on the trading machine | research 43 §8 "Prototype: the steps before one trade" | Yes | §6 |
| The risk socket as a male and female connector; options R-A to R-E | ledger C-06; `funnel4-qml/cis/seams-options.md` §6; `RISK-SIZING-PACK.md` §4 | Yes, as room only | §7 |
| The seven prototype pass marks | research 53 §3.3 | Yes, minus the throwaway: the proof is the dummy on real parts (CC-17) | §9 |
| Reference unit candidates (index cash-open breakout with a VWAP trail; FX Asian-range reversion) | explainer `pages2.mjs:364-366` via G1 §8.2 | Replaced: both need blocks that are not wrapped yet (VWAP, session range); his ruling 1 lets the lead pick | §8 |

## 3. The document's shape (data first)

The unit document is `qmx.unit/1`, held in the Library `unit` kind's `fields` (S002). It is the unit's declaration; its blocks are code in the catalogue. Field groups:

| Group | Fields | Notes |
| --- | --- | --- |
| Identity | `unit_id`, `family_id`, `version`, `parents` (links), `claim_card` {idea, claimed context, source refs, written_at} | the claim card is required before any run (S016; research 43 F3, research 26 §2.1) |
| Coordinates | `markets` [instrument at venue], `bars` [bar specs per stream], `sessions` [calendar ref plus windows in the market's zone], `direction` (long, short, both) | timeframe is a coordinate |
| Logic | `slots`: context, setup or level, trigger, confirmations, entry order, plus open roles (veto, target, invalidation, regime detector, sizing modifier, arming, timeout); each slot binds `{block: id@version, params: {name: NumberSpec}, inputs: {port: ref}}`; `combiner` per group | combiner vocabulary in `qml.md` §6 |
| Exits, sizing, halts | `exit_set` [slot bindings], `sizer` (one binding), `halts` at position, unit and account scope | the risk socket (§7); placeholder blocks allowed and labelled |
| Data needs | computed by the compiler from the blocks' declared data levels (S014); stored for reading, never typed by an author | the checker's layer D reads it |
| Context needs | `{require, warn, block}` on dictionary words with reading versions (the old capability_spec form, S015) | the MIS's board can match on it; the unit computes the readings itself |
| Routes | `data_routes` per data kind, `execution_route` | a proxy (a futures tape for a CFD unit) is declared, never silent (S116) |
| Market settings | per-market overrides of record-driven numbers, each with its earning-record pointer and shrinkage weight | "a market's own settings" (§5) |
| Baseline | pointer to the frozen baseline card from the judge | decay is judged against what was tested |
| Code | for each Python block: source fingerprint; for a plain-Python unit: a manifest declaring the same slots, numbers and data needs (S019) | plain Python keeps journals, lineage and tries |

### The number: `NumberSpec`

| Field | Meaning | Example |
| --- | --- | --- |
| `kind` | distance, count, clock, ratio, probability, threshold | threshold |
| `unit_kind` | price distance, ticks, pips, ATR multiple, percent, bars, seconds, money | percent |
| `range` | min, max, step | 0.00 to 0.30, step 0.01 |
| `default` | starting value | 0.00 |
| `motion` | see §4 | `shrink_from_own_trades`, nightly, min 60 trades |
| `authority` | inside the range: the unit's motion rule; a new range: his click only (research 43 §4 Q05) | as stated |
| `origin` | source-stated, published-convention, STRATS-standardized, inferred, builder-chosen, placeholder | builder-chosen |
| `applies_to_open_positions` | whether a moved value may change an open trade | false (the risk session decides, §7) |

## 4. How a unit tunes itself: two speeds (weak spot 1)

**The answer to his if-else question.** The numbers inside the rules move by themselves, each inside a tested range, by a tested rule for moving. The rules themselves (which blocks, which branches, which exits, the combiner) change only as a new version that he approves (research 43 §3.1). That is what every shipped platform does (research 20; research 35 §4).

**Each number declares where its movement comes from, and so how fast it can move.**

| Motion mode | Source | Moves | Trades needed | Example |
| --- | --- | --- | --- | --- |
| `fixed` | none | never | none | EMA period 100 |
| `scaled` | a price statistic | every bar | none | a distance = k × recent range (k fixed, range moves) |
| `percentile_of_own_history` | the indicator's own recent values | every bar | none | an RSI trigger at the 20th percentile of its last 500 bars |
| `state_table` | a reading the unit computes itself | when the state changes | none | a filter strength per volatility state |
| `shrink_from_own_trades` | the unit's own closed trades | on a cadence (nightly or every N closed trades) | a minimum count, then more for bigger moves | a trend-strength filter |
| `learned` | a model block retrained inside declared bounds | on a cadence | the model's own minimum sample | a probability threshold |

**The fast speed** reads price, so it needs no trades and works on day one. Research 35 calls volatility-scaled distances and adaptive indicators the safe things to auto-tune.

**The slow speed** reads the unit's own record, so it must work with few trades. Four rules make that safe (S006):
1. A minimum count before the first move (`min_trades`, default 60).
2. Shrinkage: the estimate is pulled toward the default by n/(n+k), so five trades barely move it and five hundred can reach the estimate.
3. At most one step per update, and never outside the range.
4. For a market with a thin record, the number shrinks toward the unit's pooled value across its markets, not toward zero (research 24; research 43 §3.1).

**Why live motion is not a new try** (insight I1). The calibrator runs inside the backtest replay too, reading only trades closed before the instant (S007, S008). So what QMB tests is the unit with its motion switched on, and the walk-forward result already includes the self-tuning. Live, the same rule does the same thing; nothing new was searched. A new motion rule, a new range or a new cadence is a new version and a counted try (§5).

**What the record shows.** Every move writes a calibration row: which number, old value, new value, the rule, the rows it read (a range of trade ids), the statistic it computed. The unit page shows a dial per number that reads only those rows (S160).

**Measuring what tuning is worth.** QMB runs the unit twice on the same split, motion on and motion off, and keeps both results (party P4). The difference is reported beside the verdict, never used to pick.

## 5. Identity and lifecycle

**What makes a change a new version or a new unit** (harvested from research 43 §3.1, unchanged). Risk and exit numbers are left to the risk session.

| Edit | Result | Counted try | His click before live |
| --- | --- | --- | --- |
| A logic number moves inside its range by its declared motion | calibration row | no | no |
| A learned block is retrained inside its declared bounds | calibration row | no | no |
| A learned block is retrained outside them, or has no declared bounds | new version | yes | yes |
| A range, a motion rule, a settings profile, a bar construction, a session window or the markets list changes; a market adopts its own settings | new version | yes | yes |
| A shared block's code is fixed | new version of every unit that uses it, re-tests queued | yes, per unit | yes, per unit |
| A block is swapped, a role or branch added or removed, the combiner changed, a part transplanted, or the logic changed for one market | new unit in the same family, linked to its parent | yes | yes |
| The logic is rewritten with different behaviour | new unit marked "rewritten from" | yes | yes |
| An ambiguity in the source is resolved | corrected successor; the old version stays | yes | yes |

**Lifecycle: one state machine per unit, a state per market inside it.** Only he moves a unit or a market toward live. The only automatic move is the unit's own risk rule stopping it, logged (standing order 7).

| From | To | Who | Note |
| --- | --- | --- | --- |
| draft | tested | the judge's passing verdict | a label, not a promotion |
| draft or tested | parked | the judge's failing verdict | the fail branch reads it |
| tested | paper (demo money) | his click by default; or automatically once the claim card, signal check and cost check pass, if he turns that switch on (research 43 §8 paper sequence) | no real money |
| paper | live, per market | his click only | |
| live | stopped | the unit's own risk rule, automatic, logged | which rules count is the risk session's |
| stopped | paper or live | his click only | a stopped unit keeps writing would-have-done rows |
| live | parked | his click | |
| any | retired | his click | |

"Units go back to paper" (ledger R-11) is live to stopped (automatic) then stopped to paper (his click), per market. Whether the stop rule may land a unit on paper directly, since that moves toward safety, goes to the risk session.

## 6. Standing alone: what a unit needs to trade

On the trading machine, with the PC, the Library, the MIS and the router all down, a unit trades if it has (research 53 §3.2 "relies on very few things"):
1. A price feed (the node's feed keeper on that machine).
2. The instrument facts for its markets (a snapshot in the node's volume, refreshed on change).
3. Its compiled document, its calibrated values and its own journal tail (in the node's volume).
4. Its budget share (placeholder: read from the account's equity).
5. His admission (a deployment record in the node's volume).

**The steps before one trade, all on the trading machine** (research 43 §8): data fresh; the unit's own readings and conditions; signal; the market's state is live; local guards (spread against the unit's cost target, kill-switch level); sizer slot; exit set attached; the cross-unit hook (a placeholder for the risk session); journal; order with its protection at the broker; fill journalled. The compiler refuses a rule input that is not local to the trading machine (`qml.md` §3).

## 7. The risk socket (room only, placeholders now)

No exit or sizing maths here (ledger R-04, R-01). The socket is the connector the risk session plugs into.

- **Slots:** an exit set (any number of exit blocks, at position, unit and account scope), one sizer, halts at three scopes. Option R-A (two ports plus halts) from seams §6.2 fits the slot list without closing R-B to R-E.
- **Readable inputs** (pack §4 "assumes" item 4): entry and stop, instrument facts (tick value, lot step, margin), account facts (balance, equity, open risk), the unit's journal in R, market statistics, his limits.
- **Placeholders, clearly labelled** (U-04): on backtest and demo, the exit set is a protective stop plus a target in R plus a time-out, and the sizer is a fixed fraction rounded down to the lot step, skipping with a reason below the minimum lot (research 07-qmb-lineage "round, don't refuse"). Each placeholder block carries `origin: placeholder`, shows on the unit card, and appears in the rip-out list for the risk session.
- **Protection at the broker:** every placeholder exit set places its protective stop with the order, because cTrader has no cancel-on-disconnect (G3 trap 3). Whether every live order must carry a broker stop is the risk session's (pack §2.10 C7).

## 8. The dummy unit (weak spot 2)

Picked so it uses only blocks that already run (SMA, EMA, WMA, RSI, MOM, ROC and swing points; G1 §2.3), so the proof tests the unit and not new indicators.

**"Trend pullback (dummy)"**, family `trend-pullback`.

| Part | Content | Number and motion |
| --- | --- | --- |
| Markets | EURUSD and XAUUSD, IC Markets on cTrader (demo for practice); history from the Library's Dukascopy partitions, bid and ask | markets list |
| Bars | M15 | coordinate |
| Context | uptrend when close is above EMA(close, 100) and the trend strength (ROC of that EMA over 20 bars) is at least `min_trend_strength`; mirror for downtrend | EMA period 100, fixed, `published-convention`; ROC lookback 20, fixed; **`min_trend_strength`: slow speed**, range 0.00% to 0.30%, step 0.01%, default 0.00%, motion `shrink_from_own_trades` (below), origin `builder-chosen` |
| Trigger | long when RSI(14) crosses back above `rsi_low`; short when it crosses back below `rsi_high` | RSI period 14, `published-convention`; **`rsi_low`: fast speed**, motion `percentile_of_own_history` at percentile 20 of the last 500 bars (`rsi_high` at 80); the percentile and window are fixed numbers with ranges 5 to 35 and 200 to 2,000 |
| Entry | market order at the next bar's open | none |
| Exit set | protective stop beyond the last swing point plus a buffer; target at 2R; time-out after 48 bars | all `placeholder` |
| Sizer | 0.5% of equity at risk at the stop, rounded down to the lot step; skip with reason below the minimum lot | `placeholder` |
| Halts | none beyond the node's guards | `placeholder` (warning on the card) |

**The slow motion rule for `min_trend_strength`.** Nightly, or after every 20 closed trades: once at least 60 trades have closed, bucket them by the trend strength they had at entry (five buckets), compute each bucket's mean R after costs, shrink each toward zero by n/(n+k) with k = 100, find the lowest bucket edge above which every shrunk bucket mean is at least zero, and move the number one step toward it, inside its range. It is a logic number, not an exit or a size, so it shows self-tuning without touching the risk session's ground (party P5). It runs inside the backtest exactly as live.

Why this strategy: every trader knows it; on M15 it trades a few times a day per market, so two years give enough closed trades for the slow number to move visibly; it uses a structure stop, so R is defined; and it runs on bid and ask data QMB already replays.

**It has three more jobs** (insight I5): QMB's conformance golden (`qmb.md` §6), the node's self-test unit (`node.md` §6), and the newcomer's first unit, installed out of the box (S088).

## 9. What "the unit works" means: the proof list he said was owed

Each pass mark is shown by a command and its output, never by a report (principle-prove-it-works). It runs on the real parts in the first build slice, not a throwaway (CC-17).

| # | Pass mark | Shown by |
| --- | --- | --- |
| P1 | **It can be written down.** The dummy document saves into the Library `unit` kind and the checker returns zero errors; its warnings list the placeholders | `unit_check` output |
| P2 | **The checker catches mistakes.** Three broken documents (a stop in pips on gold with no pip defined; a depth block on a bars-only market with no fallback; a number outside its range) give three typed errors with pointers | `unit_check` output |
| P3 | **It compiles into the seam QMB and the node already run**, with no change to their loops | the compiled fingerprint loaded by both |
| P4 | **QMB trades it.** Two years of EURUSD and XAUUSD M15: trades with money and R, excursions in R, context receipts; a rerun gives the identical trade list | two `backtest-result` objects and a diff |
| P5 | **It tunes itself, honestly.** Motion on and motion off on the same walk-forward split; calibration rows show `min_trend_strength` moving inside its range from named trades by the named rule, and `rsi_low` moving every bar; the difference is reported | the calibration rows and both results |
| P6 | **It stands alone.** An import and read-surface scan of the compiled unit shows no MIS, router, Library or PC-link read in its rule inputs; it trades in the node with the Library and the PC link off | scan output; node journal |
| P7 | **Same judging rule for both markets.** The judge reports both markets shrunk toward the unit's overall result and counts two tries | the verdict card |
| P8 | **It trades on demo.** The node on his PC places the dummy's demo trades on cTrader with protection at the broker; the journal rows match QMB's replay of the same days within the replay-match number | node journal against a QMB replay |
| P9 | **A cheap model can write one.** A haiku agent, given the schema, the dummy and the checker, produces a passing variant within a handful of tries | the agent's tool log and the final `unit_check` |

If P1 to P6 pass, the unit idea holds in code. P9 needs his Claude Code sign-in for haiku (research 29 §2.4); it does not block the others.

## 10. Numbers (starting defaults, all editable)

| Number | Default | Why |
| --- | --- | --- |
| `min_trades` before a slow number first moves | 60 | a mean in R at 60 trades has a standard error near 0.13R (research 24 §5), so it only nudges; INFERRED as a floor |
| shrinkage k | 100 | half weight at 100 trades if nothing better is known (research 43 §5 "Shrinkage") |
| slow cadence | nightly, or every 20 closed trades | research 43 §5 "Slow recalibration clock" |
| max step per update | one declared step | never jumps |
| range-edge card | a number at its range edge 3 times in 10 sessions raises a card for him | research 43 §5 (`qml-field.md` B017) |
| paper before his card | the later of 30 trades or 4 weeks, with the sequential score not below its start | research 43 §5 |
| `applies_to_open_positions` | false | the risk session decides |

## 11. Connection points

| From | To | What crosses |
| --- | --- | --- |
| Author (agent, copilot, him) | Library `unit` kind | the unit document; refusal with every problem |
| Unit document | QML | compile to a factory; check |
| QMB app | unit | the compiled unit by id and version; the calibration read surface fed from the run's own closed trades |
| Trading node app | unit | the deployment: compiled unit, calibrated values, instrument snapshots, journal pointer |
| Unit | journals | trades, decisions, calibration rows, state changes (`journals.md`) |
| Unit | risk session | the socket's slots and inputs; the placeholder list |

## 12. Open for the architecture step

1. Market settings inside the document (picked here, one item) or as separate linked Library items per market. Inside is simpler; separate scales better for a unit trading a hundred markets. The identity table works either way.
2. Whether `state_table` motion may read a reading the unit does not compute itself (picked: no, to stand alone).

## 13. Parked

- Rules that rewrite themselves (research 20's third meaning): ruled out by his rule that only he promotes (CC-11).
- A perps twin of the dummy (funding as a cost, 24/7 calendar): the first slice after the dummy runs (party P5, lead's call).
- Units reading other units live (build-time composition only).
