---
ticket: research-mis-organisation
title: How market-state systems are organised, and the shared-indicator question
date: 2026-10-30
author: research agent 1 (MIS), Opus poteto-agent
method: the literature in research 37 (E-ids cited, not repeated), practitioner documentation on shared feature libraries (Qlib, Feast, Two Sigma, State Street), research 16, 18, 19, 34 and the funnel files, his verbatim transcripts. Exa only.
labels: CHECKED (URL or path:line) or INFERRED.
---

# 23: How market-state systems are organised, and the shared-indicator question

## How to read this

- Options and evidence, not a design. Nothing is chosen; the options table in §2 is the deliverable.
- Research 37 (the literature) and 22 (speed) are cited by id and section instead of repeated.
- His words below are verbatim from `operator/transcript-2026-10-20-to-28.md` (`T1:n`) and `operator/transcript-2026-10-29-to-30.md` (`T2:n`), `n` = the line holding his whole turn, each CHECKED by substring this session.

## Short answer

1. **No source organises market state by one axis.** What the evidence supports is two axes at once: the clock a reading runs on (set by style and timeframe) and the data level it needs (set by what a venue offers). Asset class then mostly decides the calendar and which data levels exist (research 37 §5; `mis-field.md` B001-B004, CHECKED).
2. **One shared vocabulary with per-class sensors is supported, with one test added.** Book features rank the same across crypto assets of very different size (E08); intraday momentum shows "everywhere" across 60+ futures in four classes (E11); activity patterns are alike across 38 crypto exchanges (E33). Against: fitted models do not transfer from one crypto asset to another, though they do transfer between the spot and futures market of the same asset (E07). So a shared word is safe; a shared fitted model is not. A same-meaning check per word per class (`mis-field.md` P5-c, CHECKED) is the guard.
3. **Grouping by underlying, not by venue, fits the price-discovery evidence.** Gold's price forms mostly in COMEX futures though London trades ten times the volume (E32); one asset's spot and futures share a model (E07). A gold CFD and GC are one underlying with two data ladders.
4. **A unit using the same indicator as the MIS is one primitive in two roles, not double counting.** It only becomes double counting in three places: a lift study that treats the two as independent evidence, a try count that counts one filter twice, and a herding count where many units bind the same reading. His "it means it is already specific" (`T2:219`, CHECKED) is right: such a unit carries its own context claim, and the MIS's job for it shrinks to "where else is this true now" (`mis-field.md` B023, CHECKED).
5. **Training is mostly baseline updating, not model fitting.** Most useful readings (seasonal ratios, percentiles, volatility) "train" by refreshing their own usual levels. Fitted regime models are refit adaptively in the literature (E19, E20), and every refit relabels the past (research 05 §1.5), which is why stamped history comes first. His line "training an HMM per market is not viable" (`T2:219`, CHECKED) agrees with the non-transfer finding only if models are pooled by class or underlying.
6. **Perps funding is three things at once:** a calendar event (settlement hours, with activity spikes, E33), a state reading (the rate and its extremes, E34) and a carry cost (it changes the terrain and the trade's result). Market physics (Hurst, variance ratio, entropy, Ising) is the persistence family on the same reading shelf as everything else (research 22 §6).
7. **Publishing labels can change behaviour, but at his scale mostly inside QMX.** Published stock predictors lose 58% of their returns after publication (E42). For his units, the risk is herding on one reading, not moving the market. The MIS can add noise; research 22 measured two ways it does (bounce-made false mean reversion, hindsight-labelled gates).

---

## 1. His seeds on organisation

| Seed | His words |
| --- | --- |
| By instrument type | "I think the MIS should be able to categorize by, of course, organization is important. I had not seen this, but categorizing by instrument type." (`T1:1999`) |
| Different per class | "I don't think future is going to use the same analysis system, market analysis or market intelligence as a currency." (`T1:1999`) |
| By data, not by instrument | "we are going to consider variables that each market has" and "a Forex one is different from a futures one, but the time frame or the time frames are the same" (`T2:219`) |
| Style first | "we are now realizing that we need a trading style, firstly" (`T2:219`) |
| Not one model per market | "this part of training an HMM per market is not viable in any way, shape or form" (`T2:219`) |
| Configuration from papers | "an HMM with a specific configuration can work best in BT" (`T2:219`) |
| Shared indicator | "what if a strategy is using an indicator that also the MIS is using? Is that repetition?" and "it means it is already specific" (`T2:219`) |
| The MIS grows | "it means that the MIS can be upgraded as the agent see fit, obviously with my approval" (`T1:1951`) |
| Retrain from what he and the copilot see | "we can retrain a version of the MIS that can also see such" (`T2:219`) |
| Quality in, quality out | "the quality of what's processing information inside the MIS is directly proportional to the quality of output" (`T2:219`) |

Contradictions this ticket covers (`research/funnel3/party-brainstorm/playing-field.md:410-411`, CHECKED): C18 "do instruments matter?" (his `T1:1999` against his `T2:219`), and C19 "one MIS, or one per scalper type?" (his 13 Oct "a specific version… of the MIS" per scalper type, against the lead's "don't build one MIS per scalper type", which he answered "that's your opinion").

**The C18 reading that fits both of his statements (INFERRED):** instruments matter through their data and their calendar, and not one by one. That is exactly his `T2:219` sentence, and it keeps his `T1:1999` "categorize by instrument type" as a view (a class tab), not a separate engine.

## 2. Options: how to group the MIS

| Grouping | What it means | Evidence for | Evidence against | What breaks if chosen alone | Fails the hard cases? |
| --- | --- | --- | --- | --- | --- |
| A. By trading style (a scalper MIS, an intraday MIS, a swing MIS) | one set of readings per style | his `T2:219`; research 22 shows style decides which readings are fast enough | the same reading (spread ratio) serves every style; styles blur (an intraday unit with a scalper's entry) | duplicated readings with drifting versions; a unit that spans styles needs two MISes | yes: hybrids and new styles (a custom ML unit, STATE Q8) |
| B. By clock tier (tick, bar, session, day, week) | each reading declares the clock it runs on; a style subscribes to tiers | research 22 §3; `mis-field.md` B002 | none found | nothing breaks; but it says nothing about data | no |
| C. By data level (price only, quotes, depth, tape, derivatives fields, outside data) | each reading declares the minimum level and a fallback | research 37 matrices; `mis-field.md` B004, B005; his `T2:219` | none found | nothing; but it says nothing about speed | no |
| D. By asset class (an FX MIS, a futures MIS, a perps MIS) | separate engines per class | his `T1:1999`; class-only readings exist (funding, fixes, roll; research 37 §5) | most families recur across classes (research 37 §5); intraday momentum is cross-class (E11) | cross-class readings (dispersion, lead-lag between GC and the gold CFD) have no home; shared readings copied per class | yes: cross-class markets (Hyperliquid perps on gold and FX) |
| E. By venue or broker | one MIS per broker feed | costs differ per venue (`mis-field.md` B116) | price discovery happens at one venue for many (E32) | the gold CFD cannot read GC; duplicates per broker | yes: borrowed rungs |
| F. By underlying (gold = XAUUSD CFD + GC + a gold perp) | readings keyed to the underlying, each venue a data ladder | E32 (COMEX leads gold); E07 (spot and futures of one asset share a model) | costs and hours still differ per venue | needs a mapping from each instrument to its underlying | no, if venue costs stay per venue |
| G. By reading family (persistence, volatility, liquidity, calendar, order flow, regime) | library code grouped by what it computes | research 37 §5; Qlib groups its features by operator family (CHECKED https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/loader.py) | a family is a code shelf, not a grouping a unit asks for | nothing; it is how the code is filed | no |
| H. Tier × data level as labels, class as a pack | B and C on every reading; an asset class is a pack (calendar, data ladder, class-only readings, words to check) | `mis-field.md` B001, B020; research 43 §3.3 provisional recommendation (`research/43-convergence.md:222`, CHECKED) | more labels per reading | if the class pack is thin, the class looks covered but is not; needs visible empty rows (`mis-field.md` B019) | not found |

**What the hard cases test (INFERRED):** a gold unit that trades the CFD but reads the futures tape (only F and H handle it); a Hyperliquid perp on EURUSD (style and class both fuzzy; only B, C, F, H handle it); a 1m and 5m version of one idea (B handles it with one source aggregated up, `mis-field.md` B006); a news unit (an event clock, B); a plain-Python ML unit with no declared needs (it can subscribe to nothing, any option).

## 3. One shared vocabulary, or a separate set per class?

| Option | For | Against |
| --- | --- | --- |
| One vocabulary, per-class sensors ("separate engines, one speedometer", `mis-field.md` P5-b) | book features rank the same across five crypto assets (E08); intraday momentum across all classes (E11); activity peaks at the same UTC hour across 38 exchanges (E33); practitioners use one factor set with per-region versions (Two Sigma's "U.S. version" of its factor lens, CHECKED https://www.twosigma.com/articles/a-machine-learning-approach-to-regime-modeling/) | one word can mean different things: "crowded" for perps (open interest, funding) is not "positioning" for FX (`mis-field.md` QF08) |
| A separate vocabulary per class | each class has unique fields (funding, fixes, roll; research 37 §5) | breaks cross-class matching, which System 1 needs (a mean-reverting unit across FX, gold and indices); multiplies dictionaries (the Stats README forbids forking per market, research 16 §3.2, CHECKED) |
| One vocabulary, shared fitted models | simplest | fitted models do not transfer across crypto assets (E07) |
| One vocabulary, per-class words added only by a pack | keeps class-only words out of the shared core | a word may later prove shared and need moving |

**The guard every option needs (INFERRED from E07 and `mis-field.md` P5-c):** before a unit may match on a shared word across classes, the word must be shown to mean the same thing in each class (same percentile definition, same horizon). Shared words, per-class or per-underlying fitting.

## 4. The shared-indicator question, with worked examples

**What "double counting" can mean.** A primitive bound twice is not a problem by itself. Research 16 says context is a role, so the MIS needs no catalogue of its own: one dictionary, two bindings (research 16 §7 point 7, CHECKED). The old STRATS rule says the same in other words: a strategy can declare `requires: mis.liquidity-regime.v3`, and the MIS holds only what is shared, expensive, market state, needed in test and live, and worth versioning (research 19 §2, CHECKED). Double counting only bites in three places:

1. **Lift studies.** "Did the MIS help this unit?" counts the unit's own filter and the MIS label as two pieces of evidence when they are one.
2. **Try counts.** Tuning the unit's filter and tuning the MIS label it uses is one search, not two.
3. **Herding.** Many units binding one reading on one market at one moment is one bet seen many times (`mis-field.md` B045, B046).

**Worked examples (INFERRED):**

| Case | Unit's rule | MIS reading | Same primitive? | What it means | What to record |
| --- | --- | --- | --- | --- | --- |
| 1. Different primitives | entry: RSI(14) on 5m below 30 | "reverting" from variance ratio (240) on 1m | no | the MIS adds information the unit does not have; a lift study is meaningful | nothing special |
| 2. Same primitive, different settings | filter: efficiency ratio (20) above 0.6 | "trending" from efficiency ratio (240) | yes, different horizon | related, not identical; a fast and a slow view of one quantity | the entanglement mark with both settings (`mis-field.md` B093), so lift studies condition on the unit's own value |
| 3. Same primitive, same settings | filter: ATR(14) ÷ its 20-day median above 1.2 | volatility ratio, same formula | yes, identical | one input in two roles; with the MIS down the unit computes the same value from its own feed (research 43 §3.3) | one input, marked once; the MIS's value to this unit is placement only |
| 4. The unit's rule is the context | "fade the poke only when the session has been ranging" (its own range test) | "ranging" for the same market | yes, as a claim | his "already specific": the unit carries its own context; the MIS answers "where else is this true now" (`mis-field.md` B023) | the claim in the MIS's words so matching is a lookup (`mis-field.md` B030) |
| 5. A meta-label on top | the unit proposes; a second model trained on its own trades and the readings at entry takes or skips | any readings | uses them as features | research 05: meta-labeling is routing per trade (`research/05-academic.md:24`, CHECKED); the readings are features once | its own try count; stamped readings only (research 22 §4) |

**His "already specific" point, expanded (INFERRED):** a unit whose rules already state its context is the easy case for System 1. It needs no MIS to trade. The MIS widens where it can look. A unit whose rules state no context is the case where the MIS's label adds most, and also where it must be tested hardest (the dark-MIS and shuffled-readings runs, `research/43-convergence.md:226`, CHECKED).

## 5. Who trains market-state models, how often, on whose data (L03-08)

**Evidence.**

- Most readings "train" by refreshing their own usual levels: seasonal baselines, percentiles, volatility curves (research 05 T1; `mis-field.md` B054). Overnight refresh is the practice the literature implies for intraday periodicity (E02, E33). INFERRED.
- Regime models in the literature are refit adaptively or recursively (E19), or fit each day on the day before (E20). Jump-penalised fits need fewer iterations and are less sensitive to starting values (E19).
- Every refit relabels the past unless labels are stored as computed (research 05 §1.5, CHECKED). Feature stores solve the same problem with point-in-time joins that only return values available at the event time, with an option to exclude later backfills (CHECKED https://docs.feast.dev/getting-started/concepts/point-in-time-joins). That is the as-of query in `mis-field.md` B090.
- Fitted microstructure models do not transfer across assets but do across venues of one asset (E07).
- Practitioners refit factor-based regime models on decades of monthly data and use them for allocation, not timing (E41).

**Options (none chosen):**

| Option | Who | How often | On whose data | Breaks |
| --- | --- | --- | --- | --- |
| Baselines only, no fitted models | a scheduled QMX workflow | nightly, plus at each session close | his own recorded data and the Library's partitions | the day tier has no regime model |
| Pooled per class, normalised features | a workflow, his yes to go live | monthly in shadow | all markets of the class | fails where assets differ (E07) |
| Per underlying (spot, futures and perps of one asset together) | a workflow | monthly in shadow | that underlying's venues | many models if the universe is large (`mis-field.md` P3-a model zoo) |
| Per instrument per timeframe | a workflow | monthly | one instrument | his "not viable" (`T2:219`); thin data |
| Settings from papers as priors, refit on own data | the sensor scout workflow (`mis-field.md` B037) | when a paper or MT5 article proposes one | his data, after the prior | a paper's setting may not hold on his broker (QR06) |
| Human labels as training targets | he and the copilot, dated | weekly | what they could see (`mis-field.md` B040) | hindsight (research 22 §4, centred row) |

Where training runs follows his local-first rule (STANDING-ORDERS 8): on his PC first. One live version per reading at a time, new versions in shadow, live only with his yes (his `T1:1951`; research 43 §3.3, CHECKED).

## 6. Where perps funding and market physics fit (L03-25, L03-19)

**Funding (INFERRED from the evidence):**

| Aspect | What it is | Evidence | Home |
| --- | --- | --- | --- |
| Settlement hours | a calendar event: activity and volatility spike at funding times | E33 (0h, 8h, 16h UTC on Binance) | calendar rung, every perps venue's own schedule (Hyperliquid hourly, research 02) |
| The rate and its extremes | a state reading: extreme negative funding preceded 24-hour rebounds in one study; level predicts ≤ 8 h too weakly to trade in another | E34 | derivatives-fields rung, day and session tiers |
| The carry paid or received | a cost that changes the result of a held trade | research 43 F6, review A04 (funding as a carry cost on replay, `research/43-convergence.md:105`, CHECKED) | the instrument record and the market journal (terrain), and QMB's replay |

**Market physics.** Hurst, variance ratio, efficiency ratio, autocorrelation and entropy are one persistence family (research 22 §6). Ising-type measures have no trading evidence found (E40). The old sentinel ran Chaos and Ising readings, with HMM as shadow, and its ensemble was never wired live (research 19 §2, CHECKED). On the evidence, physics readings are members of the reading shelf like any other, judged by the same lag, false-alarm and lift card; no separate home.

## 7. Entries each class needs before perps and futures work (L04-14)

Today's dictionary covers FX and crypto spot, with no entries for funding, open interest, roll, liquidations, index sessions, or the statistics family (research 19 §6, research 16 §3.2, both CHECKED). From the evidence in research 37, each class needs at least:

| Class | Entries needed (market-state side only) | Evidence |
| --- | --- | --- |
| Every class | seasonal baseline per minute of the week; volatility by range and by ticks; spread and cost against target; calendar of sessions and events; persistence family (ER, VR, AC, Hurst with sample-size rules); change-point flags; known-state returns (move since open, rest of day) | research 37 §5 |
| Spot FX | tick volume as an activity proxy; 5 p.m. New York roll; the London 4 p.m. fix as a window; broker depth (flagged untested) | E30; research 02 |
| Gold and metals | London AM and PM auctions; COMEX open; US macro release classes (employment, GDP, CPI, personal income); GC as the lead market for the CFD | E32, E48 |
| Index CFDs | cash open and close; the future as lead market; intraday momentum into the close; dividends; regular versus extended hours | E10, E11; research 02 |
| Real futures | roll and front month; continuous contract; settlement; regular versus extended hours; open interest; trade delta; volume clock | E11, E25; research 02 |
| US stocks | relative volume ("in play"); earnings calendar; opening auction; corporate actions; halts | E13, E35 |
| Crypto spot | hour-of-day periodicity (peak 16:00-17:00 UTC); weekend state; per-venue volume; listings and delistings | E33 |
| Crypto perps | funding rate, its percentile and settlement hours per venue; open interest and its change; liquidations; basis to spot; mark versus last; venue rate limits as terrain | E33, E34; research 02 |

Each entry also needs its data level and fallback, its clock tier, and a "transfer status" per class (native, adapted, not transferable), which research 43 already proposes (`research/43-convergence.md:201-202`, CHECKED).

## 8. Can publishing labels change behaviour? Can the MIS add noise? (L03-21, L03-11)

**Publishing.** Published stock predictors lose 26% of their returns out of sample and 58% after publication, and predictors built from price and volume alone decay more (E42). FX technical rules faded over about a decade after they became known (E17). At his account size the market will not notice his labels (INFERRED). What can change is his own units' behaviour: many units binding one reading herd onto the same markets, which is why the herding count and dispersion readings are described for the risk session (`mis-field.md` B044, B045; research 43 §3.3). A slow observer-effect study (does a reading's predictive power fall once units bind it, `mis-field.md` B094) is the measurement.

**Noise.** His question, "So how is the MIS not adding more noise to an already noisy market?" (`T1:264`, as cited in `mis-field.md` S-NOISE, CHECKED there). Four measured or documented ways it can:

| Way the MIS adds noise | Evidence | Measure |
| --- | --- | --- |
| Fake mean reversion from bid-ask bounce | research 22 §2 (10-130× false alarms at heavy bounce) | the bounce ratio per market before a price-only reverting reading goes live |
| A slow label gating fast trades | research 22 §4 (no total gain at 2-hour states) | the spell-to-window ratio; the at-entry replay |
| Spurious regime switches | E19 | switches per day against the expected spell length |
| Refits that rewrite history | research 05 §1.5 | stamped values and the as-of query; a backfill flag (Feast's created-timestamp filter does the same, CHECKED above) |

The defined-to-fail tests already proposed: the dark-MIS run and the shuffled-readings run (`research/43-convergence.md:226`, CHECKED).

## 9. Numbers named here (starting defaults, none settled)

| Number | Default | Reason |
| --- | --- | --- |
| Same-meaning check across classes | percentile definitions must agree within 10 points on a shared validation window | INFERRED; `mis-field.md` P5-c |
| Baseline refresh | nightly and at each session close | E02, E33 |
| Regime-model refit in shadow | monthly | E19 (adaptive refits); INFERRED cadence |
| Live versions per reading | one at a time | his August "constant" (research 19 §2); research 43 §3.3 |
| Herding count warning | 3 or more units from one idea on one market | INFERRED; for the risk session to use |
| Funding extreme tail | trailing 180-day deciles | E34 |

## 10. Not verified

- The practitioner pages (Qlib, Feast, Two Sigma, State Street) were read for how they organise and store features, not for performance.
- How real quant desks split shared and strategy-owned features internally is not public beyond these pages; claims here are about the documented tools.
- No dictionary file was opened this session; its coverage is taken from research 16 and 19 (CHECKED there).
